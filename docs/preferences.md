# Preferences that reach past one week

> **What the objective cannot say across weeks, and what that silence costs.**
>
> The objective is defined inside one horizon. `replan.md` prices deviation from the incumbent, and
> the incumbent is a roster for *this* week. Ask what a person's fourth week in a row looks like and
> this project has almost nothing to say.
>
> **This was a catalogue of twenty-three proposals and is no longer** ([`D-146`](decisions.md#d-146)). Four of its items
> shipped as rules — `R-MAX-WEEKENDS`, `R-MIN-DAYS-OFF`, `R-SUCCESSION`, `R-MIN-BLOCK` ([`D-135`](decisions.md#d-135),
> [`D-136`](decisions.md#d-136)) — and `rules.md` owns them now. The rest was a roadmap, and a roadmap of unbuilt things is
> not evidence. What is kept is the part that was measured, and the item IDs the measurement uses.

## What the objective can express today

Every term in the objective, with the reference point it measures against and how far it reaches.
`disruption.objective_terms` and `disruption.fairness_terms` are the whole list.

| Term | Measures against | Reach |
| --- | --- | --- |
| Coverage shortfall, mix shortfall | the slot's requirement | one slot |
| Cost | nothing — paid hours | the horizon, and `cost_weight` ships at `0` ([`D-050`](decisions.md#d-050)) |
| D0–D2 | the incumbent, per changed slot | the horizon |
| D3 | the incumbent, per `(employee, day)` | one day |
| D4 concentration | the incumbent, per employee | the horizon |
| Fairness `g(unpopular)` | a **carried count** plus this roster | the horizon **plus history** ([`D-108`](decisions.md#d-108)) |
| Peak workload | nothing — a cold-solve tie-breaker | the horizon |

One term has memory. Everything else is a function of the payload alone, and the payload's memory is
three scalars on `Employee`:

```
last_shift_end_before_horizon           R-REST-GAP across the boundary
consecutive_days_worked_before_horizon  R-CONSEC-DAYS across the boundary
unpopular_shifts_before_horizon         the fairness term's rolling window
```

Plus one resolved upstream: `max_hours_this_week` is a rolling reference period collapsed into a
number by the caller, which `rules.md` states as an approximation and
[`studies/horizon.md`](studies/horizon.md) confirms costs no coverage.

**There is no field anywhere holding what last week's roster looked like.** That is the exact shape of
the gap. This project can carry a *count* across a horizon boundary and cannot carry a *shape*. Any
preference about a pattern rather than a total runs into that one wall.

**And the horizon is not the limit people assume.** [`D-113`](decisions.md#d-113) allows any whole number of weeks, and
four is measured. The machinery to reason across weeks is already in the request path; what is missing
is anything in the objective that would spend it.


## How badly each is ignored today, measured

This document argued from first principles that the objective is silent about structure across weeks.
That silence is now measured ([`D-134`](decisions.md#d-134)). Cold generation under this project's objective, checked
against the nurse-rostering benchmark's own constraints on three real instances, breaks **every one
of the seven**. The `survey item` column carries the IDs this document used, and is what
[`studies/foreign-incumbent.md`](studies/foreign-incumbent.md) cites:

| survey item | their constraint | breaches |
| --- | --- | --- |
| E7 — days off in blocks | `MinConsecutiveDaysOff` | 154 |
| E1 — block length | `MinConsecutiveShifts` | 67 |
| E8 — quick returns | `Succession` | 38 |
| E4 — weekend load | `MaxWeekends` | 34 |
| E3 — hours floor | `MinTotalMinutes` | 0 |

The ranking is worth more than the totals. It was produced by somebody else's constraint set rather
than by the judgement that wrote this document, and it put E7 and E1 — neither of which this
document nominated as the place to start — ahead of E4, which it did. That is the whole reason the
measurement outlived the catalogue it was made to rank.

## The word *preference* was an assumption, and it is contradicted from outside

This document sorted every item as something to be **priced**. That is a choice, and importing the
nurse-rostering instances in full shows it is not the only defensible one ([`D-132`](decisions.md#d-132)). In their
formulation, `MaxWeekends` (E4), `MinConsecutiveDaysOff` (E7), `MinConsecutiveShifts` (E1's
block-length half) and the forbidden shift successions (E8) are **hard constraints carrying no
weight**. Their objective is two lists of shift requests and per-slot cover deviation, and nothing else.

So four items this document called preferences are rules where those rosters come from. `rules.md`
already owns the test that decides which they are here — *when the only otherwise-legal roster
violates this, should the service return nothing and an explanation, or the best compromise, priced?*
— and the answer is per tenant rather than per item. What changes is that the question now has two
real answers in evidence instead of one assumption, and anything built as a soft term should say why
it is soft rather than inheriting this document's framing.


## Two reference rosters, not one

The distinction Class B turns on, and it is worth stating precisely because the arithmetic is
identical and the meaning is not.

- **The incumbent** — what people were *told about this horizon*. Deviation from it is disruption.
  Owned by `replan.md`. Already implemented.
- **A reference** — what this person's working life is *arranged around*: last week's actual roster, or
  a rotating master schedule, or a stated ideal week. Deviation from it is inconsistency.

They are the same sum over `x[e,d,s] ≠ reference[e,d,s]`, and they conflict. Honouring the promise
about Thursday can be exactly the thing that breaks the pattern the person arranged childcare around,
and a model with one reference roster cannot see the trade.

**A template collapses most of the cross-week wishes into arithmetic that already exists.** If a
tenant publishes a rotating master schedule — *lines of work*, in the literature's term — then
shift-type consistency, day-pattern consistency, weekend rotation and the employer's mirror of all
three are deviation from the template, which is D0–D2's encoding with `x̄` swapped for a second roster
and a separate weight. No new term shape, no per-pair variables, one new payload object. That is the
highest-leverage single move in this document, and it is worth pricing before any bespoke term.

The catch is that a template is a thing the tenant must have. Many small horeca operators do not, and
for them the reference has to be last week's roster, which drifts: penalising deviation from a drifting
reference locks in whatever the first week happened to be, including its unfairness.

## The three-way conflict

Consistency, balance and rotation cannot all be had.

```
consistency  — the same person on the same slot every week
balance      — the unpopular and popular slots spread evenly, as `D-108` does
rotation     — deliberately moving people between slots
```

Balance and rotation both require reshuffling who works what. Consistency forbids reshuffling. Any two
of the three are satisfiable and all three are not, and the choice between them is a social fact about
a tenant in exactly the sense [`D-108`](decisions.md#d-108) established for unpopularity — a bakery whose staff have held
their shifts for a decade and a hospital rotating night duty are not making the same trade badly, they
are making different trades.

So whatever lands from this document should be **declared rather than derived**, and the profile is
where it is declared.

**Where the project sits today, stated precisely.** Inside a horizon the objective is strongly sticky:
disruption pulls the roster toward the incumbent, which is consistency over the days of one week.
Across horizons it is indifferent — nothing prefers this week to resemble last week — with one
exception, the fairness term, which pulls the other way and rewards reshuffling who takes the
unpopular shifts. Nobody chose that asymmetry; it fell out of one term having history and the rest not.
