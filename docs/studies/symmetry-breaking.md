# Symmetry breaking, and how much the incumbent already does

**Question.** [`model.md`](../specs/model.md#symmetry) says no symmetry breaking is in the model
deliberately, because "the disruption objective already breaks symmetry partially — quantify this
rather than assuming it". So: quantify it.

**Answer.** There is essentially **no symmetry left to break**. Across 24 committed cases there are 3
interchangeable employees in total, in a single case. Lexicographic ordering therefore buys nothing
and costs about 4% of build time. But the null is not evidence that the lever is useless — on a
workforce built to be interchangeable it is worth **20% of total time** — so what this study
establishes is a fact about the distribution, and the decision follows from that.

    uv run python -m benchmarks.studies --only symmetry

## What "interchangeable" has to mean

Swapping two employees must map every legal roster to a legal roster **and leave the objective
unchanged**. The second half is what the incumbent destroys: disruption is measured against each
person's own published row, so two people with identical contracts, skills, budgets and availability
are *not* interchangeable if their published shifts differ. A lexicographic constraint over them
would cut off optima rather than duplicates.

`model._orbits` therefore groups employees only when every attribute the model reads matches *and*
their incumbent rows match.

## The count, which is the actual deliverable

| | interchangeable employees |
| --- | --- |
| committed replan cases (24) | **3**, in 1 case |
| the same weeks solved cold, no incumbent (6) | **7** |

Two separate things are suppressing symmetry, and only one of them is the objective:

1. **The incumbent**, which is what `model.md` predicted. It roughly halves what remains.
2. **The generator**, which is the larger effect and was not predicted. Each employee gets an
   independently sampled weekly budget from `{16, 20, 24}` or `{32, 38, 38}` and independently
   sampled unavailability, so two employees are rarely identical *before* any incumbent exists. Seven
   interchangeable employees across six cold weeks is already almost none.

That second point matters for how far this result travels. A real tenant with eight part-timers on
identical contracts and open availability would have genuine orbits, and this distribution does not
model that tenant. The null below is measured on the instances this project commits to, and it is not
a claim about rostering in general.

## The measurement

**On the committed set** — a null, and slightly negative:

| quantity | ratio, on against off | helped | hurt |
| --- | --- | --- | --- |
| variables | 1.000 | 0 | 1 |
| build time | 1.004 | 7 | 17 |
| search time | 0.999 | 13 | 11 |
| total time | 1.003 | 7 | 17 |

Search time is a coin flip, 13 against 11, which is exactly what "no symmetry to exploit" looks like.
Build time is consistently but trivially worse, because the orbit search runs and finds nothing.

**On a workforce built to be interchangeable** — `identical_workforce`, 8 to 16 employees with
identical skills, contracts, budgets and no unavailability, solved cold:

| quantity | ratio, on against off | helped | hurt |
| --- | --- | --- | --- |
| variables | 1.235 | 0 | 5 |
| constraints | 1.788 | 0 | 5 |
| build time | 1.330 | 0 | 5 |
| search time | **0.730** | 4 | 1 |
| **total time** | **0.801** | 4 | 1 |

The lever works where the structure exists: 27% off the search, paid for with a 79% larger model and
a 33% slower build, netting **20% off the total**. It is worth noting that it nets out positive at
all — the prefix-equality chain is not a cheap encoding, and at these sizes a lever that grows the
build usually loses.

## Decision

**Not implemented, and `model.md` stays as written.** The reasoning in the spec was right and is now
measured rather than assumed. What changes is the recorded reason: the spec attributes the
suppression to the disruption objective, and the larger share of it is the generator giving every
employee a different budget and a different availability pattern.

The condition under which this would be revisited is now stated rather than left to judgement: a
tenant profile with a substantial group of employees identical in contract, skills, budget and
availability. `D-087` records it.
