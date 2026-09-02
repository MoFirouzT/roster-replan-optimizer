# Fairness, generation, and two retirements

**Status:** Implemented 2026-08-15
**Reconstructed 2026-09-02** from [`disruption.py`](../../roster_replan/disruption.py),
[`scoring.py`](../../roster_replan/scoring.py),
[`benchmarks/weights.py`](../../benchmarks/weights.py),
[`internals/model.md`](../internals/model.md),
[`studies/weight-recovery.md`](../studies/weight-recovery.md), the mutant catalogue, and
the commits of 2026-08-14 to 2026-08-15. **It is not the work order this component was
built from**; no such document existed
([`spec-reconstruction.md`](spec-reconstruction.md)).
**Depends on:** [`disruption.md`](disruption.md) and
[`benchmark-set.md`](benchmark-set.md), whose measurements retire half of it.

## Objective

Four candidate capabilities examined together: a fairness objective, generation as a
product surface, large-neighbourhood search, and learned warm starts. Build the two that
were never measured, and retire the two that already had been.

## Motivation

A tier of "possible improvements" is where a project accumulates work it will never do,
because upside costs nothing to list. This component exists to sort the four by whether
anything has been measured about them, and to write the retirements down as retirements
rather than as deferrals.

**Retiring is the harder half and it is the one worth recording.** A deferral is a promise
nobody will keep; a retirement states what would reopen it.

## Canonical reference

[`internals/model.md`](../internals/model.md) owns the fairness term and generation as
cold start. [`guide/configuring.md`](../guide/configuring.md) owns the profile's fairness
declaration.

## Governing reference

None. Fairness here is a tenant's policy, not a legal entitlement: the statutory rules
that touch the same ground are in [`rules.md`](rules.md).

## Parameters and configuration

`Fairness` is its own dataclass rather than a field on `Disruption`. **Which shifts are
unpopular is declared by the profile**, and each employee carries
`unpopular_shifts_before_horizon` so the balance is struck over a window wider than the
horizon.

## Interfaces

```text
disruption.fairness_terms(model, instance, x, params)   the model's reading
scoring.fairness_of(roster, instance)                   the independent reading
```

Generation adds no interface at all: a caller generates by **omitting `incumbent` and
`now`**.

## Layering

The same two objective contracts as [`disruption.md`](disruption.md), which the fairness
term shares. *The penalty search is solver-free* covers the identifiability probe.

## Build tasks

- [x] Ship fairness as a rolling balance of unpopular shifts, in its own type, encoded and
      scored independently.
- [x] Grow the domination bound by a fairness term, and check it at profile load.
- [x] Make generation testable at the solver, the ladder and the service, rather than
      adding a route.
- [x] Measure whether the soft weights are identifiable at all, before building any
      estimator.
- [x] Retire LNS and learned warm starts, each with what would reopen it.

## Test contract

| Claim | Layer |
| --- | --- |
| Fairness counts history from before the horizon | `test_fairness.py::fairness-ignores-history-before-the-horizon` |
| Both readings count it | `fairness-scorer-ignores-history` |
| The escalation is not flat | `fairness-escalation-is-flat` |
| Fairness cannot escape the domination bound | `fairness-escapes-the-domination-bound` |
| Cold disruption is flat at zero | `test_generation.py::generation-cold-disruption-is-not-flat` |
| A cold solve keeps its tie-breaker | `generation-loses-its-only-tie-breaker` |

**The service test is load-bearing.** *No second formulation* would be true of `solve` and
false of the product if a cold payload could not get through the queue, and nothing had
ever checked.

## Acceptance gate

*Blocks:* nothing. This is the last tier.

- [x] Fairness is a third meaning of the word here, and gets its own type for that reason
      ([`D-108`](../decisions.md#d-108)). Round-robin is fairness between tenants in the
      queue; D4's concentration spreads the changes a replan makes; this one is about the
      roster, and a tenant can want any one without the others.
- [x] Generation ships with no formulation, no mode flag and no second route
      ([`D-109`](../decisions.md#d-109)).
- [!] **Testing generation found the design wrong about why it works.** The derivation
      said cold disruption is a positive constant that a shortfall would reduce. Measured,
      `scoring.disruption_of` short-circuits to **0** with no incumbent, so the disruption
      axis is flat at every coverage level. Both readings rank equal-coverage rosters the
      same way, which is why nobody noticed, and the caveat was describing a risk the
      implementation cannot have.
- [!] **LNS is retired on measurements already taken.** It improves a solution the solver
      cannot prove optimal in the time available, and **neither half of that sentence is
      true here**: every one of 2,160 solves at three budgets returned `OPTIMAL`, and
      solver-free greedy already ties the optimum on most committed cases
      ([`D-104`](../decisions.md#d-104)). What would reopen it is stated: a distribution
      where the solver stops proving optimality.
- [!] **Learned warm starts are retired twice over.** They would chase 9% of a search that
      runs in milliseconds, so the machinery to train one would exceed the thing it
      optimises by orders of magnitude. And then the stronger reason:
      **the rosters carry no signal to learn from at all**
      ([`weight-recovery.md`](../studies/weight-recovery.md),
      [`D-129`](../decisions.md#d-129)).

## Measured results

**Not one of the five D2-active weights moves the roster on any of the fourteen classes**,
swept across three orders of magnitude. Forty profiles spanning all five metrics and wide
weight ranges produce one or two distinct rosters per case. The objective is **priced but
not pivotal**: it scores the answer, it does not choose it.

Two existing records already said this from other directions, which is what makes the
finding solid rather than surprising: D0, D1 and D2 never disagree
([`D-120`](../decisions.md#d-120)), and a solver-free greedy with no objective at all ties
the optimum on 71 of 84 ([`D-105`](../decisions.md#d-105)).

**The null is about the distribution, and it is demonstrated rather than argued.** Where
`weights.forced_choice` builds a case the weights alone decide, the roster follows them.

**Where signal exists, recovery returns an interval on a ratio and never a weight.**
Scaling every weight leaves every argmin unchanged, so more data narrows the interval and
never collapses it. **Any estimator reporting a point estimate is reporting its prior**,
which is why identifiability was measured before anything was fitted.

**Fairness gives the optimiser a second reason to leave a shift empty**, because an
unstaffed unpopular shift is one nobody's count went up for. The domination bound grows a
term for it, and a weight scale that breaks the bound is a malformed request.

**The escalation flattens past `fairness_tiers`, and that is a real bound.** An employee
whose rolling total already exceeds the tier count sits where the term no longer
distinguishes them, so a window long enough to push everybody past it **switches fairness
off while appearing to be configured**. Profile review says so when the supplied priors
already reach the tiers, as a remark rather than a defect: the request is lawful and the
tenant may have meant the window.

## Out of scope

- **Building a weight estimator.** The measurement is the result
  ([`D-129`](../decisions.md#d-129)). An estimator scored against parameters the data
  cannot identify reports its own prior and looks like a result.
- **Deriving unpopularity from shift times.** A late shift is a burden in one restaurant
  and the shift people compete for in another. Computing it from the clock would encode one
  tenant's culture as arithmetic, in the part of this system that is meant to be
  policy-as-data.
- **A `max − min` range term.** It equalises the two ends and ignores everyone in the
  middle.
- **Adding fairness weights to `Disruption`.** Three different things are called fairness
  here and merging two of them would lose the distinction.
- **A `/v1/rosters` route or a `mode: "generate"` field.** A second route over the same
  solve would contradict what the design is for.

## Decisions

Reconstructed. Each was decided while the component was built, and the record is the
citation.

1. **Are all four items kept open?** No: two retired, two built
   ([`D-104`](../decisions.md#d-104)). Keeping the other two is not hedging, and each
   retirement states what would reopen it.

2. **Does fairness live inside `Disruption`?** No, its own type
   ([`D-108`](../decisions.md#d-108)).

3. **Is generation a mode?** No, the cold-start case
   ([`D-109`](../decisions.md#d-109)), and the honest way to ship that claim is to prove
   the existing surface carries it.

4. **Is identifiability measured before an estimator is built?** Yes
   ([`D-129`](../decisions.md#d-129)), and it is the reason no estimator exists.

5. **Could a caller reach any of this?** Not at first
   ([`D-131`](../decisions.md#d-131)). `Fairness`,
   `unpopular_shifts_before_horizon` and `max_hours_this_period` had no wire counterpart,
   so **the one cross-week term in the objective was callable only from Python**. A term
   the service cannot express is not shipped.

---

*The ledger: [`README.md`](README.md). The null:
[`studies/weight-recovery.md`](../studies/weight-recovery.md). The reasoning:
[`decisions.md`](../decisions.md).*
