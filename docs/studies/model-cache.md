# Caching the compiled model, and what profiling said instead

**Question.** [`service.md`](../specs/service.md) calls for a per-tenant compiled-model cache:
*"at these instance sizes, building the model can cost more than solving it."* The premise is right —
about 5 ms of build against 3 ms of search. Is the remedy?

**Answer.** Not for replanning. The cache is correct, nearly free, and **hits 0 of 144 replan
solves**, because a replan is triggered by a change to the model's own inputs. The 20% that *was*
available came from somewhere the spec never looked: one memoised method. Both are shipped, and only
one of them is the thing that was asked for.

    uv run python -m pytest tests/test_cache.py

## What profiling actually found

Before optimising anything, `build` was profiled. Sixty per cent of it was in `Instance.window` —
694,800 calls across 200 builds, about **3,474 calls per build to compute 21 distinct values**. A
one-week horizon with three shift types has `7 × 3` windows; the model was allocating each of them
roughly 165 times.

Memoising it is unconditional, needs no invalidation, and cannot go stale — `window` is a pure
function of `(day, shift)` and immutable shift types, and `Interval` is frozen, so a shared instance
is indistinguishable from a fresh one.

| | before | after |
| --- | --- | --- |
| `headline/0` build | 6.5 ms | **5.2 ms** |
| `large/0` build | 13.4 ms | **10.9 ms** |

About 20% off the largest single cost in the solve path, measured on a **cold** cache per build — the
saving comes from collapsing 3,474 calls to 21 *within* one build, not from reuse across requests, so
it is a production win rather than a benchmark artifact.

That is larger than presolve (`studies/presolve.md`), larger than the warm start, and larger than
every level-1 lever in the benchmark set. It was invisible to all of them because they compared *encodings*,
and this was never an encoding question.

## The cache itself: correct, cheap, and useless where it was aimed

Built anyway, because "useless here" is a measurement and not a guess.

**The key has to cover everything `build` reads**, which is nearly the whole payload: horizon, shift
types, rule parameters, every employee's availability, skills, contract, budgets and eligibility,
every open shift, and `now`. The objective is *not* in the key, because `model.solve` applies it per
solve.

One exception makes this subtle rather than obvious, and it is [`D-058`](../decisions.md#d-058): `build` creates a variable for
any pair the **incumbent** assigned even when presolve excluded it, so the incumbent changes the
variable set and belongs in the key after all. The tidy split — constraints in, objective out — is
wrong in exactly that one place, and wrong in the direction that returns a model missing the variables
a deviation is counted on.

### The economics

| | |
| --- | --- |
| fingerprint | 0.030 ms |
| build | 5.11 ms |
| **cost of a miss** | **0.6% of a build** |
| **value of a hit** | **170×** |

### The hit rate

| workload | hits |
| --- | --- |
| **replan traffic** — every committed case, week then post-event | **0 / 144 (0%)** |
| the same instance solved repeatedly | 24 / 36 (67%) |

Zero, and structurally so. **The event that triggers a replan is a change to the model's inputs**: an
absence changes which pairs survive presolve, which changes the variables. A replan of a week is never
the same model as the week. The one case where a cache pays — the same instance solved more than once
— is not the replan path; it is the `what_if` sweep, replay, and retries.

So it ships **enabled**, on the grounds that a miss costs 0.6% and a hit saves 170×, not on the
grounds that it helps replanning. `test_the_replan_path_does_not_hit` asserts the zero, so that if it
ever starts hitting, something has stopped telling two different models apart.

## Two bugs the mutation harness found in the tests above

Both survived a fully green suite, and both are the kind this cache exists to be dangerous with.

**The absence test was passing for the wrong reason.** It compared `scenario.base` against
`scenario.instance` — which also differ in their *incumbent*, so the fingerprints separated for that
reason alone. A fingerprint blind to absences passed it. The test now injects an absence into one
instance and compares against the same instance without it.

**`clear_objective()` was dead code.** Deleting it broke nothing, because `minimize` and `maximize`
replace the objective rather than adding to it — verified directly against CP-SAT — and `model.solve`
sets one on every call. Hints and assumptions do accumulate and are still cleared. The defensive line
went, on this repo's standing rule that code which cannot be shown to fail is not known to work.

## A third thing, caught by the benchmark manifest

Memoising `window` meant adding a field to `Instance`, and `benchmarks/suite.py` fingerprints
instances by walking `dataclasses.fields`. The cache immediately leaked into the committed manifest,
so every hash depended on which methods had been called before the digest was taken. The manifest test
failed on the next run — which is what [`D-074`](../decisions.md#d-074) built it for.

The fix is general rather than a patch: the walk now includes only fields with `compare=True`. A field
excluded from `__eq__` must be excluded from a fingerprint, or two objects that compare equal hash
differently. With it in place the manifest reproduces byte-for-byte, which is also the cleanest
evidence that memoisation changed no instance — only how fast one builds.
