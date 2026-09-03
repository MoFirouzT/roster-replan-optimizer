# Caching the compiled model, and what profiling said instead

**Question.** [`api.md`](../guide/api.md) called for a per-tenant compiled-model cache: *"at these
instance sizes, building the model can cost more than solving it."* The premise is right, about
5 ms of build against 3 ms of search. Is the remedy?

**Answer.** Not for replanning. The cache is correct, nearly free, and **hits 0 of 144 replan
solves**, because a replan is triggered by a change to the model's own inputs. The 20% that *was*
available came from somewhere the spec never looked: one memoised method.

**The cache has since been deleted** ([`D-149`](../decisions.md#d-149),
[`D-093`](../decisions.md#d-093) retired). This study is kept because the measurement is durable and
still governs: it is the evidence that the replan path cannot reuse a model, and the reason
[`model.py`](../../roster_replan/model.py) memoises nothing across calls.

## The numbers

| | |
| --- | --- |
| hit rate, replan traffic (every committed case, week then post-event) | **0 of 144** |
| hit rate, the same instance solved repeatedly | 24 of 36 |
| cost of a miss | 0.030 ms against a 5.11 ms build, so 0.6% |
| value of a hit | 170× |

Zero, and structurally so. **The event that triggers a replan is a change to the model's inputs**:
an absence changes which pairs survive presolve, which changes the variable set. A replan of a week
is never the same model as the week. The one workload where a cache pays, the same instance solved
more than once, is the `what_if` sweep and retries rather than the replan path.

## What profiling found instead

`build` was profiled before anything was optimised. Sixty per cent of it was in `Instance.window`:
694,800 calls across 200 builds, about **3,474 calls per build to compute 21 distinct values**.

| | before | after memoising |
| --- | --- | --- |
| `headline/0` build | 6.5 ms | **5.2 ms** |
| `large/0` build | 13.4 ms | **10.9 ms** |

About 20% off the largest single cost in the solve path, measured on a cold cache per build, so the
saving comes from collapsing 3,474 calls to 21 *within* one build rather than from reuse across
requests. That is larger than presolve, larger than the warm start, and larger than every encoding
lever in [`encoding-levers.md`](encoding-levers.md). It was invisible to all of them because they
compared **encodings**, and this was never an encoding question.

## Two things the harness caught in the tests above

Both survived a fully green suite.

**The absence test was passing for the wrong reason.** It compared `scenario.base` against
`scenario.instance`, which also differ in their incumbent, so the fingerprints separated for that
reason alone. A fingerprint blind to absences passed it.

**Memoising `window` leaked into the committed manifest.** `benchmarks/suite.py` fingerprints
instances by walking `dataclasses.fields`, so every hash depended on which methods had been called
before the digest was taken. The manifest test failed on the next run, which is what
[`D-074`](../decisions.md#d-074) built it for. The fix is general: the walk now includes only fields
with `compare=True`, because a field excluded from `__eq__` must be excluded from a fingerprint.

---

*Behind this: [`D-092`](../decisions.md#d-092) for the memoisation,
[`D-149`](../decisions.md#d-149) for deleting the cache. The index: [`README.md`](README.md).*
