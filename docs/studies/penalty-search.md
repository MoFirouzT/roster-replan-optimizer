# Priced rules against structural ones

**Question.** [`D-002`](../decisions.md#d-002) encodes hard rules as constraints rather than as large
penalties, on the grounds that *a penalised legal rule produces a roster that is cheaply illegal*.
[`D-003`](../decisions.md#d-003) leans on the same sentence to justify the independent checker, and
[`validation.md`](../internals/testing.md) states it a third time. Three records rest on the claim and
none of them measured it. So: measure it.

**Answer.** **It depends entirely on the instance, and the easy distribution gives the wrong answer.**
On the committed set there *is* a setting that is both safe and near-optimal: 0 illegal rosters in 14
cases, within 38.6 of the optimum, which taken alone would read as a partial falsification of
[`D-002`](../decisions.md#d-002). On the one genuinely hard instance this project has ([`D-127`](../decisions.md#d-127)), **no setting works at all**:
every weight is either illegal or leaves shifts unstaffed, and the best legal answer is 500× worse
than the proven optimum while still failing to staff the week.

The mechanism is the finding. Raising the price of a rule does not buy legality plus quality: it buys
legality **by refusing to staff**, because `R-COVER`'s floor is soft ([`D-018`](../decisions.md#d-018)) and is therefore the
one exit a penalised search can always afford.

    uv run python -m benchmarks.anneal_study --set committed
    uv run python -m benchmarks.anneal_study --set foreign --instance 8

## What was built

[`benchmarks/anneal.py`](../../benchmarks/anneal.py): Metropolis acceptance over the assignment
encoding, geometric cooling, moves being add / drop / reassign / swap. Every hard rule is priced at
`hard_weight` instead of prohibited. There is no repair step and no feasibility gate.

It lives in `benchmarks/` and not on the product path, which is the `benchmarks/milp.py` precedent
([`D-001`](../decisions.md#d-001)), and an import-linter contract holds it solver-free the way `repair.py` is held: a rival
that can reach the model is not a rival, and a module whose whole point is having no hard-constraint
guarantee must not be able to borrow one.

**It is deliberately not registered in `methods.METHODS`.** That tuple defines the four-method
comparison and drives the committed `results.json`; adding a fifth member would re-base every number
in [`benchmarks.md`](../benchmarks.md) to answer a question that comparison was not asking.

### Three choices that decide what the numbers mean

**The checker is the search's own oracle.** The penalty counts hard violations reported by
`checker.check`. That hands the metaheuristic a *perfect* legality oracle, so nothing it returns can
be blamed on an evaluator that misread the rules. The claim under test is that pricing a rule is
unsafe **even when you know exactly which rules you broke**.

**The budget is counted in evaluations, not seconds.** Each move costs a full `check` and `score`:
0.13 ms on a committed case, 2.5 ms on instance 8. A production engine evaluates incrementally and
would run orders of magnitude more moves per second, so a wall-clock race against CP-SAT would measure
this Python rather than the method class. Seconds are recorded and are labelled as what they are.

The alternative was an incremental evaluator, and it was refused rather than skipped: one fast enough
to compete would have to encode which rules are per-employee and which are per-slot, which is rule
structure living outside `checker.py`: the shared-assumption failure mode [`D-111`](../decisions.md#d-111) and [`D-123`](../decisions.md#d-123) were
both written about.

**The weight is swept across five decades**, because [`D-002`](../decisions.md#d-002)'s claim is not that some particular
weight is too small. It is that no weight is both safe and effective, and only a surface can answer
that.

## The committed set: a penalty engine that works, if you tune it

Fourteen cases, one per class, named rather than sliced ([`D-107`](../decisions.md#d-107)). `illegal` counts rosters carrying
any hard violation; `new` counts those where the search *created* one; `unrepaired` counts those where
it simply left the damage it was handed.

| weight | evals | illegal | new | unrepaired | scores better than the optimum | mean gap | matched |
| --- | --- | --- | --- | --- | --- | --- | --- |
| 1 | 1k–100k | **14/14** | 4 | 10 | **13** | n/a | 0/0 |
| 100 | 1k | 14/14 | 4 | 10 | 13 | n/a | 0/0 |
| 100 | 100k | 13/14 | 4 | 9 | 12 | 0.0 | 1/1 |
| 10,000 | 1k | 5/14 | 3 | 2 | 5 | 135.6 | 2/9 |
| 10,000 | 100k | 3/14 | 3 | 0 | 3 | 40.0 | 8/11 |
| 1,000,000 | 1k | 0/14 | 0 | 0 | 0 | 107,332 | 1/14 |
| 1,000,000 | 100k | **0/14** | 0 | 0 | 0 | **38.6** | 11/14 |
| 10,000,000 | 100k | 0/14 | 0 | 0 | 0 | 35,836 | 2/14 |

**The characteristic failure is doing nothing.** At weight 1, ten of the fourteen illegal rosters
introduced no new violation at all: they returned the incumbent essentially untouched, absence and
all. The cheapest way out of a priced rule is to decline to repair it, which is a quieter failure than
the rule-breaking [`D-002`](../decisions.md#d-002) describes and a worse one to detect.

**Thirteen of fourteen illegal rosters score better than the proven optimum** on the shared D2
yardstick. A results table showing the objective column ranks the unsafe method first in 93% of cases,
and only the violations column dissents. This is why `methods.Outcome` carries `violations` beside
`disruption` rather than reporting a single number.

**Too dear fails like too cheap.** At 10,000,000 the penalty term swamps the objective, the search
freezes, and the gap is 35,836 at the largest budget with 2 of 14 matching.

**And there is a sweet spot**: weight 1,000,000 at 100,000 evaluations is 0/14 illegal and within 38.6
of the optimum, matching it outright on 11 of 14. On this distribution, [`D-002`](../decisions.md#d-002)'s claim does not hold
in its strong form.

## Instance 8: no setting works

Foreign instance 8: 30 employees over 4 weeks, the first genuinely hard search this project has seen
([`D-127`](../decisions.md#d-127)). The exact model proves optimality in **5.74 s** at disruption **210**, fully staffed. The
published incumbent arrives carrying 5 hard violations of its own, so `new` is reported separately.

| weight | evals | hard violations | new | slots left unstaffed | disruption |
| --- | --- | --- | --- | --- | --- |
| 1 | 100k | 278 | 276 | 0 | 5,370 |
| 100 | 100k | 78 | 76 | 0 | 4,820 |
| 10,000 | 1k | 32 | 32 | 0 | 3,340 |
| 10,000 | 100k | **3** | 3 | 0 | 4,410 |
| 1,000,000 | 1k | 5 | 0 | **5** | 0 |
| 1,000,000 | 100k | **0** | 0 | **1** | 4,540 |
| 10,000,000 | 100k | 0 | 0 | **19** | 4,580 |
| *exact* | n/a | **0** | 0 | **0** | **210** |

**Every configuration fails, and the two halves fail differently.** Below 1,000,000 the search staffs
the week and breaks rules: 3 violations at best, all of them `R-MAX-PERIOD`. At and above 1,000,000
it stops breaking rules and starts leaving holes: 1 unstaffed slot at the best setting, 19 at the
dearest.

**The exit is the soft floor.** `R-COVER`'s floor is the one deliberate soft exception in this model
([`D-018`](../decisions.md#d-018), priced in [`D-047`](../decisions.md#d-047)), so a shortfall is expensive but never prohibited. As the price of hard
rules rises, the search discovers that not staffing is the affordable way to be legal. Nothing told it
to do that; it is what pricing legality means.

The best legal answer costs **104,540 against an optimum of 210**: one unstaffed shift plus 4,540
disruption, about 500× worse: after 220 seconds of search against 5.74.

### What it has when the exact solver finishes

**It never matches, at any weight and any budget tested.** That is the implementation-independent
answer, and it is the one that counts: the best legal result at 100,000 evaluations still leaves a
shift unstaffed, and the best fully-staffed result still breaks three rules.

Read against the clock instead, at the 5.74 seconds CP-SAT needs to prove optimality, this <!-- lint-ok: this set's own figure, not the foreign instance's -->
implementation has managed 1,000–2,000 moves and holds:

| weight | hard violations | objective |
| --- | --- | --- |
| 1 | 278 | 5,370 |
| 100 | 200 | 3,420 |
| 10,000 | 5 | 500,000 |
| 1,000,000 | 5 | 500,000 |
| *exact, same instant* | **0** | **210** |

**That table is about this Python, not about annealing**, and it is here with that label rather than
left out. At 2.5 ms per move a production engine with an incremental evaluator would be somewhere
between two and four orders of magnitude further along. The row that survives that objection is the
one above it: no budget in the sweep reaches a legal, fully-staffed roster at all.

## What this changes

**[`D-002`](../decisions.md#d-002) and [`D-003`](../decisions.md#d-003) are confirmed, and narrowly.** Had this been run only on the committed set, the
honest report would have been *a tuned penalty engine is safe and near-optimal here*, which is true and
does not transfer. The distribution that produced that answer is the one [`D-105`](../decisions.md#d-105) swept without finding
anything hard and [`D-127`](../decisions.md#d-127) showed cannot produce a hard instance.

**The independent checker is load-bearing rather than a nice-to-have, and now there is a number for
it.** A penalty formulation returned an illegal roster in 100% of committed cases at low weight and in
9 of 15 configurations on instance 8, while *scoring better than the proven optimum* in 13 of 14
committed cases. Nothing inside such a search can report that; only a reading that owes it nothing can.

**The anytime argument for a metaheuristic is not made here.** Instance 8 is where an exact method is
slowest, and it is still 500× better at 1/40th the search time. Instance 23: the 8-million-variable
case where the exact model returns no roster: is **not** the counter-example it looks like: [`D-127`](../decisions.md#d-127)
records that its failure is 527 seconds of *model construction*, not search, so a comparison there
measures Python object building rather than either method.

## What this does not establish

**One hard instance.** Instance 8 is the only case in this project where an exact search is
genuinely slow, so the foreign half of this study is n=1 and is reported as such.

**One implementation of one metaheuristic.** Simulated annealing with four move types, no tabu list,
no restarts, no adaptive weighting. A commercial engine with an incremental evaluator and a tuned
neighbourhood would search far more of the space per second. What it could not do is change the
mechanism: the exit through the soft floor is a property of the objective, not of the search.

**The weights are a five-decade grid**, not an optimisation. A weight between 10,000 and 1,000,000
might narrow the gap on instance 8; that it would have to be tuned per instance is itself the point,
since the exact formulation needs no such number.

## Notes

[`D-128`](../decisions.md#d-128) records the decision. The runner writes
[`benchmarks/anneal-results.json`](../../benchmarks/anneal-results.json) and
`anneal-results-foreign8.json`.

**Per-run anytime samples are not committed**, and the reason is worth stating because the first
version of these files carried them. They were 96% of a 3.2 MB artifact, and the three budgets are
already an anytime curve: a better one, being independent runs rather than one trajectory's
best-so-far. The one question the samples did answer, the 5.74-second snapshot above, is five numbers
that now live in this document. `run.py` drops the roster from `results.json` on the same reasoning:
the case name and the seed reproduce it. Rerun with `--trace` to regenerate them.

Two defects were found in this study's own harness before it produced a number, and both are recorded
in [`D-128`](../decisions.md#d-128) because each would have produced a study whose every figure computed and meant nothing: a
feasibility gate that survived the first test suite, and a summary that counted an untouched damaged
incumbent as a clean run.
