# The warm start, isolated from the objective effect

**Question.** A replan is hinted with the roster it is repairing.
"Warm-started replan" is the headline phrase, so the obvious risk is that the speedup being claimed for the hint is really the **objective** doing the work.
[`replan.md`](../../internals/model.md) asked for this filed either way.

**Answer.** **Not a null, and not the headline either: 9% of search time.**
The hint reduces search time on 201 of 216 paired runs, median paired ratio **0.907** — reproduced at **0.906 on 662 of 756 runs** over the widened set ([`D-105`](../decisions.md#d-105)).
It is invisible end to end, and it never changes the answer.

## What was compared

The confound is separated by the **cold disruption baseline**: same objective, same instance, same solver seed, hint or no hint.
The only difference left is the hint.
A cold *cost* baseline would have conflated the two, which is exactly the claim `replan.md` warned against.

| | median paired ratio | faster | runs |
| --- | --- | --- | --- |
| 72-case set ([`D-082`](../decisions.md#d-082)) | 0.907 | 201/216 | 216 |
| 84-case set ([`D-105`](../decisions.md#d-105)) | 0.906 | 662/756 | 756 |

Reproducing to within a thousandth over a set widened along the coverage axis is the useful part: it says the figure is a property of the hint rather than of where the original set sampled.

## Reading it honestly

**9% of a 3 ms search is a rounding error, and [`benchmarks.md`](../benchmarks.md) says so in those words.**
The effect that carries the results is the **objective**: the disruption profile cuts mean disruption from 323 to 66 against the cost baseline.
Beside that, the hint does not show up end to end at all.

This is why the README's framing is *the objective is what does the work*, not *warm-started replan*.
The honest sentence was available only because the two effects were measured separately.

**It has a consequence for work not done.** Learned warm starts — a candidate that was never built — are chasing 9% of the smaller half of the latency budget, at these sizes.
That is worth knowing before building them, and it is part of why that item was retired on measurements already taken ([`D-104`](../decisions.md#d-104)).

**What is unanswered.** Whether the hint matters where search dominates construction.
It does not here: build is ~5 ms against ~3 ms of search, and after canonicalising the optimum the balance moved to roughly 1:1 ([`D-119`](../decisions.md#d-119)).
Answering it needs instances this set does not contain — and the one foreign instance hard enough to search for 7.71 s arrived too late to be swept ([`foreign-incumbent.md`](foreign-incumbent.md)).
