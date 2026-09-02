# How far the objective reaches across weeks

**Question.** The objective is defined inside one horizon: it prices deviation from the
incumbent, and the incumbent is a roster for *this* week. Ask what a person's fourth week in a
row looks like and this project has almost nothing to say. How much is *almost nothing*, and
how badly does it show?

**Answer.** One objective term reaches past the horizon and everything else is a function of
the payload alone. Measured against somebody else's constraint set on three real instances,
cold generation under this objective **breaks every one of the seven constraints they check**,
and the ranking of which it breaks worst was not the ranking this project would have guessed.

**Conditions.** The measurement is of the objective *as shipped*: `disruption.objective_terms`
and `disruption.fairness_terms` as tabulated below, D2 as the shipped disruption metric
([`D-006`](../decisions.md#d-006)), and the three scalars of employee memory the payload
carries: no more. Change any of those and the table below is the thing to re-measure. The
breach counts are cold generation, not replanning, on three of the thirteen imported
nurse-rostering instances ([`D-134`](../decisions.md#d-134)).

This began as a twenty-three item catalogue of proposals and is no longer
([`D-146`](../decisions.md#d-146)). Four of its items shipped as rules: `R-MAX-WEEKENDS`,
`R-MIN-DAYS-OFF`, `R-SUCCESSION`, `R-MIN-BLOCK` ([`D-135`](../decisions.md#d-135),
[`D-136`](../decisions.md#d-136)), and [`rules.md`](../guide/rules.md) owns them now. What is
kept here is what was measured, and the item IDs the measurement uses.

## What the objective can express today

Every term in the objective, with the reference point it measures against and how far it reaches.
`disruption.objective_terms` and `disruption.fairness_terms` are the whole list.

| Term | Measures against | Reach |
| --- | --- | --- |
| Coverage shortfall, mix shortfall | the slot's requirement | one slot |
| Cost | nothing: paid hours | the horizon, and `cost_weight` ships at `0` ([`D-050`](../decisions.md#d-050)) |
| D0–D2 | the incumbent, per changed slot | the horizon |
| D3 | the incumbent, per `(employee, day)` | one day |
| D4 concentration | the incumbent, per employee | the horizon |
| Fairness `g(unpopular)` | a **carried count** plus this roster | the horizon **plus history** ([`D-108`](../decisions.md#d-108)) |
| Peak workload | nothing: a cold-solve tie-breaker | the horizon |

One term has memory. Everything else is a function of the payload alone, and the payload's memory is
three scalars on `Employee`:

```
last_shift_end_before_horizon           R-REST-GAP across the boundary
consecutive_days_worked_before_horizon  R-CONSEC-DAYS across the boundary
unpopular_shifts_before_horizon         the fairness term's rolling window
```

Plus one resolved upstream: `max_hours_this_week` is a rolling reference period collapsed into a
number by the caller, which `rules.md` states as an approximation and
[`studies/horizon.md`](../studies/horizon.md) confirms costs no coverage.

**There is no field anywhere holding what last week's roster looked like.** That is the exact shape of
the gap. This project can carry a *count* across a horizon boundary and cannot carry a *shape*. Any
preference about a pattern rather than a total runs into that one wall.

**And the horizon is not the limit people assume.** [`D-113`](../decisions.md#d-113) allows any whole number of weeks, and
four is measured. The machinery to reason across weeks is already in the request path; what is missing
is anything in the objective that would spend it.


## How badly each is ignored today, measured

The survey argued from first principles that the objective is silent about structure across weeks.
That silence is now measured ([`D-134`](../decisions.md#d-134)). Cold generation under this project's objective, checked
against the nurse-rostering benchmark's own constraints on three real instances, breaks **every one
of the seven**. The `survey item` column carries the IDs the survey used, and is what
[`foreign-incumbent.md`](foreign-incumbent.md) cites:

| survey item | their constraint | breaches |
| --- | --- | --- |
| E7: days off in blocks | `MinConsecutiveDaysOff` | 154 |
| E1: block length | `MinConsecutiveShifts` | 67 |
| E8: quick returns | `Succession` | 38 |
| E4: weekend load | `MaxWeekends` | 34 |
| E3: hours floor | `MinTotalMinutes` | 0 |

The ranking is worth more than the totals. It was produced by somebody else's constraint set rather
than by the judgement that wrote the survey, and it put E7 and E1: neither of which the
survey nominated as the place to start: ahead of E4, which it did. That is the whole reason the
measurement outlived the catalogue it was made to rank.

## The word *preference* was an assumption, and it is contradicted from outside

The survey sorted every item as something to be **priced**. That is a choice, and importing the
nurse-rostering instances in full shows it is not the only defensible one ([`D-132`](../decisions.md#d-132)). In their
formulation, `MaxWeekends` (E4), `MinConsecutiveDaysOff` (E7), `MinConsecutiveShifts` (E1's
block-length half) and the forbidden shift successions (E8) are **hard constraints carrying no
weight**. Their objective is two lists of shift requests and per-slot cover deviation, and nothing else.

So four items the survey called preferences are rules where those rosters come from. `rules.md`
already owns the test that decides which they are here: *when the only otherwise-legal roster
violates this, should the service return nothing and an explanation, or the best compromise, priced?*,
and the answer is per tenant rather than per item. What changes is that the question now has two
real answers in evidence instead of one assumption, and anything built as a soft term should say why
it is soft rather than inheriting the survey's framing.


## Where the project sits today

Inside a horizon the objective is strongly sticky:
disruption pulls the roster toward the incumbent, which is consistency over the days of one week.
Across horizons it is indifferent (nothing prefers this week to resemble last week) with one
exception, the fairness term, which pulls the other way and rewards reshuffling who takes the
unpopular shifts. Nobody chose that asymmetry; it fell out of one term having history and the rest not.
