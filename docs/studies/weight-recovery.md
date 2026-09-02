# Can a tenant's soft weights be read back off their rosters?

**Question.** Configuring a tenant's objective profile is the manual bottleneck in this domain,
and every planner edit is a labelled preference. So: recover a tenant's soft weights from
(what the model would have produced, what they published) pairs.

**Answer. No, and not because the estimator is weak: there is no signal to estimate from.**
On the committed set **not one of the five D2-active weights moves the roster on any of the
fourteen classes**, swept across three orders of magnitude. Forty profiles spanning all five
metrics and wide weight ranges produce **one or two distinct rosters per case**. The objective
is *priced but not pivotal*: it scores the answer, it does not choose it.

Where signal does exist, what comes back is **an interval on a ratio, never a weight**. Four
weight vectors (1/10, 2/20, 5/50, 10/100) produce byte-identical rosters and recover the
identical interval, because scaling every weight leaves every argmin unchanged.

    uv run python -m benchmarks.weights

## The null, and it is total

| weight | metric | cases whose roster responds |
| --- | --- | --- |
| `published_weight` | D2 | **0/14** |
| `draft_weight` | D2 | **0/14** |
| `notice_multiplier` | D2 | **0/14** |
| `peak_weight` | D2 | **0/14** |
| `mix_shortfall_weight` | D2 | **0/14** |
| `move_weight` | D3 | 6/14 |
| `cancel_weight` | D3 | 0/14 |
| `call_in_weight` | D3 | 5/14 |

The D3 weights are swept under a D3 profile on purpose. Under D2 they are inert *by
construction*: `scoring.disruption_of` routes D0–D2 through `_per_assignment`, which prices a
slot at `publication x notice` and never looks at an event, so sweeping them under D2 would
measure the metric rather than the distribution. **A tenant on the shipped D2 profile cannot
have `move_weight` learned at any sample size.**

## Priced but not pivotal

The weights are not being ignored. On `headline/0`, moving the near-band multiplier moves the
objective exactly as the specification says it should:

| `notice_multiplier` | objective | roster |
| --- | --- | --- |
| 1 | 20 | unchanged |
| 4 | 80 | unchanged |
| 16 | 320 | unchanged |
| 64 | 1,280 | unchanged |

A 64× swing in what the answer *costs*, and no change in what the answer *is*. The weight
enters the objective and cannot reach the argmin, because there is almost nothing to choose
between: **five of twenty-one slots are changeable** on a committed replan, the rest being
pinned past, and coverage must be met.

## It reproduces two findings this repo already had

**`disruption-metrics.md` from the other side.** Across 40 profiles per case, the only split
that ever appears is D0/D1/D2 against D3/D4: never within a side:

| case | roster 0 | roster 1 |
| --- | --- | --- |
| `headline/0` | D0, D1, D2, D3, D4 (32 profiles) | D3, D4 (8 profiles) |
| `busy/0` | D0, D1, D2, D3, D4 (36 profiles) | D3, D4 (4 profiles) |

That is exactly what [`D-085`](../decisions.md#d-085), [`D-106`](../decisions.md#d-106) and [`D-120`](../decisions.md#d-120) report: *"only D0/D1/D2 against D3/D4;
within each side nothing separates them"*: arrived at from the weights rather than from the
metrics, and it says why: the factors distinguishing D1 and D2 from D0 cannot reach the argmin.

**[`D-083`](../decisions.md#d-083) said it first and nobody read it this way.** Solver-free greedy repair, which has no
objective at all, ties the optimum on **71 of 84** committed cases ([`D-105`](../decisions.md#d-105)). A method that
cannot read a weight reaching the optimum 85% of the time *is* the statement that weights do
not pick the roster here. The premise of this study was already falsified by a measurement in
this repo, and connecting them took running the sweep.

## The null is about the distribution, and here is the proof

[`weights.forced_choice`](../../benchmarks/weights.py) is built to present the choice the
committed set never does: the same move `studies.identical_workforce` makes for symmetry.
Two holes, one employee with budget for one, so exactly one hole stays open either way and
**the shortfall term cancels**. The two slots differ on precisely what D2 prices: day 2 is
published and one hour away (inside the near band), day 5 is draft and 73 hours away.

| `published_weight` | `draft_weight` | hole filled |
| --- | --- | --- |
| 10 | 1 | day 5 |
| 1 | 10 | day 2 |
| 100 | 1 | day 5 |
| 1 | 100 | day 2 |

The roster follows the weights. So `weights.py` can detect an identifiable weight, and the
0/14 above is a fact about what the generator produces rather than about the model or the probe.

## What recovery actually returns

Given only the rosters (the estimator never reads the profile) the flip point brackets the
ratio:

| true weights | true ratio | recovered | brackets the truth |
| --- | --- | --- | --- |
| 10 / 1 | 0.10 | (: , 1) | yes |
| 1 / 1 | 1.00 | (1, 2) | yes |
| 1 / 10 | 10.00 | **(10, 12)** | yes |
| 2 / 20 | 10.00 | **(10, 12)** | yes |
| 5 / 50 | 10.00 | **(10, 12)** | yes |
| 10 / 100 | 10.00 | **(10, 12)** | yes |

**Four different weight vectors, one recovered answer.** A roster is an argmin, so it reports
one inequality between weighted terms; every vector satisfying it explains the observation
equally well, and more data narrows the interval without ever collapsing it to a point. That
is not a limit of the effort spent: it is what inverse optimization returns, and any
estimator reporting a point estimate of a weight would be reporting its prior.

Two further non-identifiabilities are structural rather than distributional and were not worth
measuring separately: `shortfall_weight` must clear the domination bound ([`D-057`](../decisions.md#d-057)), above which
every value behaves identically, so only *that it clears the bound* is observable; and
`cost_weight` ships at 0 ([`D-050`](../decisions.md#d-050)), so the cost term is absent rather than unlearnable.

## What this does not establish

**Marginal identifiability only.** Each weight was swept alone, holding the rest fixed. Weights
could in principle be jointly identifiable while none is marginally so, though a roster
identical across a 1000× range of `published_weight` makes that implausible for that weight.

**One seed per class.** Fourteen cases, named rather than sliced ([`D-107`](../decisions.md#d-107)). The greedy result
this leans on is measured over all 84.

**Nothing about real planners.** The premise this study set out to test is that *published*
rosters encode preferences. What it shows is that on rosters **this model produces**, the
weights leave no trace. A published roster made by a human is a different object, and
[`benchmarks.md`](../benchmarks.md)'s standing gap: the incumbent is solved by the system
under test: is exactly the gap that would have to close before the original question could be
asked properly. [`D-125`](../decisions.md#d-125)'s foreign rosters are the nearest thing available and were not swept
here.

## Notes

[`D-129`](../decisions.md#d-129) records the decision. No committed artifact: the whole grid regenerates in about
eleven seconds, so a JSON file would be a copy of these tables that nothing reads and nothing
keeps honest. `tests/test_weights.py` guards the finding, and its load-bearing test is
`forced_choice` rather than the null: a probe that cannot see a weight makes every zero above
meaningless, and two mutants flatten the instance to prove the test notices.
