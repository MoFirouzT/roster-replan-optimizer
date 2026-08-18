# Domain presolve: removing impossible pairs before the solver

**Question.** [`model.md`](../specs/model.md#presolve) calls presolve "often the largest single win,
and free". Is it?

**Answer.** A win, consistently, and not the largest one. It removes about a quarter of the model and
buys **28% off build time and 14% off search time**, on 28 of 28 paired cases in every quantity
measured. (Re-measured over the widened set — [`D-107`](../decisions.md#d-107); the original figures were 28% and 16% on
24 of 24.) "Free" is right — the exclusion table is computed either way, because the reasons have to
be retained for reporting ([`D-045`](../decisions.md#d-045)).

    uv run python -m benchmarks.studies --only presolve

Re-measured after [`D-092`](../decisions.md#d-092) memoised `Instance.window` and cut build time by 20%. The verdict is
unchanged and the ratios moved by about a point, which is what a lever independent of that one should
do.

## What was compared

`build(presolve=False)` against the default. The off variant keeps a variable for every
(employee, shift) pair including the impossible ones, and leaves them to the gated `x = 0` that
already exists for incumbent pairs ([`D-058`](../decisions.md#d-058)). Both models have the same feasible set and the same
optimum, which the study checks before reporting any timing — a broken encoding is usually the fast
one.

| quantity | ratio, on against off | helped | hurt |
| --- | --- | --- | --- |
| variables | 0.716 | 28/28 | 0 |
| constraints | 0.692 | 28/28 | 0 |
| build time | 0.724 | 28/28 | 0 |
| search time | 0.863 | 28/28 | 0 |

Presolve keeps 57% to 76% of the unpresolved model's variables across the 28 cases, so the model is
about a quarter smaller and the range across scenario classes is wide — `thin-availability`, where
declared unavailability removes the most pairs, is at the bottom of it.

## Reading it honestly

**The 28/28 is what makes this a result at these sizes.** A 27% median improvement on a 5.2 ms build
would not survive scrutiny on its own; the same direction on every paired case does. This is the
cleanest positive in the level-1 set, and it is the only one of the four that wins on every quantity
at once.

**It is not "the largest single win", and the spec is now corrected.** Build time dominates search
time at these sizes ([`D-081`](../decisions.md#d-081)), and presolve takes 28% off the larger half — real, but a factor of
1.4, not the order of magnitude the phrase suggests.

An earlier version of this paragraph named caching the compiled model as the largest available win.
That was a guess and it was wrong — measured, the cache hits **0 of 144** replan solves, because a
replan changes the model's own inputs. The largest single win turned out to be memoising
`Instance.window`, worth about 20% of build time and found by profiling rather than by reasoning about
encodings. See [`model-cache.md`](model-cache.md) and [`D-092`](../decisions.md#d-092).

**The search-time figure is the weakest of the four numbers** and is reported last for that reason.
Search is about 3 ms, 14% of it is under half a millisecond, and that is near the resolution
of the measurement. The sign test carries it: 28 of 28 is not a clock artifact.

## Why it is kept regardless of the number

Presolve is not only a speed lever, and this is the part a benchmark cannot show. `R-AVAIL`,
`R-SKILL`, `R-FLEXI-ELIG` and `R-DIMONA-FLX` are enforced *entirely* by removing variables rather than
by adding rows (`model.md`), so turning it off does not merely slow the model down — it changes which
mechanism enforces four rules, and it makes the model carry constraints whose only purpose is to
forbid what the presolve would have deleted. The measured 28% is the smaller half of the argument.
