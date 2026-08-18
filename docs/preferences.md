# Preferences that reach past one week

> **This is a survey, not a spec.** It catalogues what the two sides of a roster actually want, sorts
> each item by the machinery it would need here, and names the conflicts between them.
>
> **Four of its items are no longer proposals.** [`D-135`](decisions.md#d-135) and [`D-136`](decisions.md#d-136) encoded E4, E7, E8's quick-return
> half and E1's block half as rules — `R-MAX-WEEKENDS`, `R-MIN-DAYS-OFF`, `R-SUCCESSION`,
> `R-MIN-BLOCK` — because the nurse-rostering benchmark set states them as *constraints* rather than
> preferences ([`D-132`](decisions.md#d-132)), and this document had assumed the opposite. `rules.md` owns them now; the
> entries below are kept as the survey that led there, and each says what shipped.
>
> It exists because the objective is defined inside one horizon. `replan.md` prices deviation from the
> incumbent, and the incumbent is a roster for *this* week. Ask what a person's fourth week in a row
> looks like and this project has almost nothing to say.

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
the gap. This project can carry a *count* across a horizon boundary and cannot carry a *shape*. Every
preference below that is about a pattern rather than a total runs into that one wall.

**And the horizon is not the limit people assume.** [`D-113`](decisions.md#d-113) allows any whole number of weeks, and
four is measured. The machinery to reason across weeks is already in the request path; what is missing
is anything in the objective that would spend it.

## The employee side

Ordered roughly by how often it decides whether someone stays in a job.
**What it wants** is the preference; **needs** is the machinery missing here; the class is the one defined below.

| | Preference | What it wants | Needs | Class |
| --- | --- | --- | --- | --- |
| **E1** | Shift-type consistency | the same shift type week after week, not a legal-but-arbitrary mixture — the single most common thing people mean by a good schedule | a **shape** carried across the boundary | B |
| **E2** | Day-pattern consistency | the same days each week, which is what childcare and second jobs are actually built around | a shape, or the promotion of a pattern into `unavailability` | B |
| **E3** | Hours consistency | a predictable pay packet, not 12 hours one week and 34 the next | a per-employee hours target and a convex penalty on distance from it, over multiple weeks in one solve | C |
| **E4** | Weekend load | not to work every weekend | **shipped as `R-MAX-WEEKENDS`** ([`D-135`](decisions.md#d-135)) | A |
| **E5** | Whole weekends | both weekend days off together, rather than one of each — a split weekend is worth much less than two days | a per-employee, per-weekend pair of indicators and a penalty on the split | C, cheaply |
| **E6** | Predictable weekend rotation | to know which weekends are theirs, months ahead | a horizon holding at least two weekends, plus one carried scalar | C |
| **E7** | Days off in blocks | two days off together rather than scattered singles | **shipped as `R-MIN-DAYS-OFF`** ([`D-135`](decisions.md#d-135)) | A |
| **E8** | Rotation direction, and quick returns | forward rotation, and never a close followed by an open | quick returns **shipped as `R-SUCCESSION`** ([`D-136`](decisions.md#d-136)); direction needs a carried last shift type | A / B |
| **E9** | Night load and recovery | a ceiling on nights and real recovery after a run of them | as E4 and E7 | A / C |
| **E10** | Requests | the specific Tuesday they asked for | a request list in the payload and a linear term — **the cheapest thing here** | D |
| **E11** | Notice and stability of the published plan | not to be the person edited every week | for the cumulative form, a count of prior edits carried per employee | A |
| **E12** | Clustering against spreading | fifteen hours over two days, or over five — **no consensus direction**, so a parameter rather than an objective | a per-employee direction and a penalty on days worked for given hours | C / D |
| **E13** | Who they work with | to work alongside someone, or not; not to be alone on a shift. Cheap to encode and politically expensive to hold — a preference naming a colleague is a record *about that colleague*, and `capture.md`'s privacy reasoning applies sharply | pairwise data and a term over pairs | D |
| **E14** | A fair share of the good shifts | the mirror of the fairness term: [`D-108`](decisions.md#d-108) spreads what nobody wants, and nobody spreads what everybody wants. The asymmetry is not a design decision anyone recorded — it follows from `Fairness.unpopular_shifts` being a single set | a second declared set and a term on it | A |

## The employer side

| | Preference | What it wants | Needs | Class |
| --- | --- | --- | --- | --- |
| **Em1** | Rotation for capability | nobody to be the only person who can run Saturday night. Invisible to every number this service returns, because the roster is legal and fully covered right up to the day that person is gone. **This is the employer's own reason to want the thing E1 dislikes** | a per-`(employee, slot)` count carried across horizons, and a penalty on concentration | A / B |
| **Em2** | Anti-entrenchment on a slot | the sharper version of Em1, and often not negotiable: whoever always closes and counts the till is who a control failure hides behind | Em1's counts, plus the classification question `rules.md` asks | A / B |
| **Em3** | Team mixing, or stable teams | either, depending on the tenant — and the two are opposite | pairwise co-assignment counts and a signed weight | B / D |
| **Em4** | Development and exposure | junior staff on the shifts that teach them something | a target count per employee per slot class, over a window | A / B |
| **Em5** | Continuity for the customer | the same faces on the same shifts. **Exactly Em1's counts with the weight's sign reversed** — that the same data serves both is the useful part | as Em1 | A / B |
| **Em6** | Overtime and premium distribution | premium hours spread or concentrated deliberately rather than by accident | wage data first | A, after that |
| **Em7** | Keeping the roster repairable | a roster with slack left in it, so next week's sick call is cheap to absorb | no payload change to *measure* it; a term to *optimise* it is a two-stage problem and a real research question, not a weight | — |
| **Em8** | Plan churn as administrative cost | fewer edits to process, independently of who they land on | a per-contract count ([`D-036`](decisions.md#d-036)) | A |
| **Em9** | Contract-mix economics | the cheapest lawful mix of flexi, student and permanent hours | wage data, and quota state carried per employee | A, after that |

## The four classes, and what each would cost

Sorting the whole catalogue by machinery rather than by whose preference it is:

**Class A — a count carried as a scalar.** E4, E9, E11-cumulative, E14, Em1, Em4, Em5, Em6, Em9.
The mechanism already exists and shipped once: `unpopular_shifts_before_horizon` plus a convex
penalty ([`D-108`](decisions.md#d-108), encoded per [`D-055`](decisions.md#d-055)). Additive, no horizon change, no new solve shape. The cost is
one field per counted thing and a caller who has to compute it — the same bargain `max_hours_this_week`
already strikes, with the same consequence `rules.md` states plainly: correctness comes to depend on a
computation this service does not perform.

**Class B — a shape carried as data.** E1, E2, E8-direction, Em1, Em2, Em3, Em5.
These need to know what the previous roster *looked like*, per employee and slot, not how much of it
there was. That is a second roster in the payload, and it is not the incumbent — see below.

**Class C — a trade between weeks, needing them in one solve.** E3, E5, E6, E7, E12.
The horizon already allows this ([`D-113`](decisions.md#d-113), up to four weeks measured). What these cost is search time,
and the horizon study measures the bill: search grows 13.5× over 7 to 28 days against build's 5.5×.
They are also the only class for which a longer horizon buys something — see the scoping note below.

**Class D — new data about people, not about time.** E10, E13, Em3.
No time reasoning at all. E10 is the cheapest item in this whole document and probably the first one a
real tenant would ask for.

### How badly each is ignored today, measured

This document argued from first principles that the objective is silent about structure across weeks.
That silence is now measured ([`D-134`](decisions.md#d-134)). Cold generation under this project's objective, checked
against the nurse-rostering benchmark's own constraints on three real instances, breaks **every one
of the seven** — and the two items ranked highest here are the two broken most:

| survey item | their constraint | breaches |
| --- | --- | --- |
| E7 — days off in blocks | `MinConsecutiveDaysOff` | 154 |
| E1 — block length | `MinConsecutiveShifts` | 67 |
| E8 — quick returns | `Succession` | 38 |
| E4 — weekend load | `MaxWeekends` | 34 |
| E3 — hours floor | `MinTotalMinutes` | 0 |

The ranking is worth more than the totals. It was produced by somebody else's constraint set rather
than by the judgement that wrote this catalogue, and it puts E7 and E1 — neither of which this
document nominated as the place to start — ahead of E4, which it did.

### The word *preference* is this document's assumption, and it is contradicted from outside

Everything above is sorted as something to be **priced**. That is a choice, and importing the
nurse-rostering instances in full shows it is not the only defensible one ([`D-132`](decisions.md#d-132)). In their
formulation, `MaxWeekends` (E4), `MinConsecutiveDaysOff` (E7), `MinConsecutiveShifts` (E1's
block-length half) and the forbidden shift successions (E8) are **hard constraints carrying no
weight**. Their objective is two request lists (E10) and per-slot cover deviation, and nothing else.

So four items this survey calls preferences are rules where those rosters come from. `rules.md`
already owns the test that decides which they are here — *when the only otherwise-legal roster
violates this, should the service return nothing and an explanation, or the best compromise, priced?*
— and the answer is per tenant rather than per item. What changes is that the question now has two
real answers in evidence instead of one assumption, and any of these built as a soft term should say
why it is soft rather than inheriting this document's framing.

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

**A template collapses most of Class B into arithmetic that already exists.** If a tenant publishes a
rotating master schedule — *lines of work*, in the literature's term — then E1, E2, E6, Em1, Em2 and
Em5 are all deviation from the template, which is D0–D2's encoding with `x̄` swapped for a second
roster and a separate weight. No new term shape, no per-pair variables, one new payload object. That is
the highest-leverage single move in this document, and it is worth pricing before any of the bespoke
terms above.

The catch is that a template is a thing the tenant must have. Many small horeca operators do not, and
for them the reference has to be last week's roster, which drifts: penalising deviation from a drifting
reference locks in whatever the first week happened to be, including its unfairness.

## The three-way conflict

Consistency, balance and rotation cannot all be had.

```
consistency (E1, E2, Em5)   — the same person on the same slot every week
balance     (E4, E14, D-108) — the unpopular and popular slots spread evenly
rotation    (Em1, Em2, Em4)  — deliberately moving people between slots
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

## A scoping note on the horizon study

[`studies/horizon.md`](studies/horizon.md) upholds the rejection of a reference-period horizon on the
finding that a longer one **buys nothing**: four weeks solved at once and four solved one at a time
reach identical coverage on every case, at both ends of the tightness axis.

That is measured on **coverage**, under an objective with no term that spans weeks. The study says as
much about the mechanism — *"the weeks are barely coupled"*, because `R-MAX-WEEKLY` binds inside a week
and `R-WEEKLY-REST` is measured inside one — and every Class C preference above is precisely a coupling
the objective does not currently have. Even the fairness term could not have shown up: [`D-108`](decisions.md#d-108) records
that the committed set cannot exercise it, because its evenings need a scarce skill.

So the narrower true statement is that a longer horizon buys no coverage **under the shipped
objective**, and the honest way to reopen it is not to re-time the same solve but to add a term that
needs two weeks and re-measure. [`D-116`](decisions.md#d-116)'s conclusion is not wrong; it is scoped, in the same way
[`D-081`](decisions.md#d-081)'s build-dominates premise turned out to be scoped to one week.

## One thing to measure before adding anything

This repo's rhythm is to find out whether a lever exists before pulling it, and five of eight studies
came back null. The equivalent question here:

**Does week-to-week consistency emerge for free?** Chain four one-week solves with the boundary state
carried, exactly as the horizon study's second arm already does, and measure what happens to each
employee's pattern: how often their shift-type mix changes, how many keep their days, how the weekend
load lands. The optimiser has reasons to be accidentally consistent — skills, availability, the same
demand shape every week — and if it already is, most of Class B is a null and the effort belongs in
Class A and D.

If it is not consistent, the same run produces the baseline that any consistency term would have to
beat. Either way the answer is worth more than the terms are, and the harness for it exists:
`benchmarks/studies.py` already chains four weekly solves and stitches them into one month for the
independent checker.

## A reachability defect found while writing this, since fixed

Not a preference question, but it belongs on the record because it was the difference between one of
these terms being shipped and being reachable.

`replan.md` and [`D-108`](decisions.md#d-108) both say unpopular shifts are **declared by the profile**. They were not:
`Profile` had no `fairness` field, and neither `Fairness` nor
`Employee.unpopular_shifts_before_horizon` appeared in `service/contracts.py`, whose `Strict` base
forbids unknown fields — so a caller who sent either was rejected with a schema error.
`Employee.max_hours_this_period` ([`D-123`](decisions.md#d-123), `R-MAX-PERIOD`) was missing from the same contract. The
project's one cross-week objective term and its one cross-week hard rule were both callable only from
Python.

**Closed under [`D-131`](decisions.md#d-131)**, along with a second divergence in the same paragraph of `replan.md`: the
warning it said `validation.py` gave when the supplied priors already exceed the tiers did not exist,
and belonged in `profile.remarks` rather than in a module whose every finding rejects a request.

The reason it survived is worth keeping in view while reading the rest of this document. The wire
round-trip test asserts an identity over the committed cases, and no case in the set sets fairness or
a period budget — so it held over the fields the set happens to use. **Every term proposed above will
arrive with the same blind spot**: a field the instance distribution does not contain is a field the
boundary is not tested to carry.
