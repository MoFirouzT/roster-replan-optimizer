# Preferences that reach past one week

> **This is a survey, not a spec, and no decision is taken in it.** It catalogues what the two sides
> of a roster actually want, sorts each item by the machinery it would need here, and names the
> conflicts between them. Nothing below is implemented; anything that becomes implemented moves into
> [`specs/replan.md`](specs/replan.md) with a record in [`decisions.md`](decisions.md).
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
| Cost | nothing — paid hours | the horizon, and `cost_weight` ships at `0` (`D-050`) |
| D0–D2 | the incumbent, per changed slot | the horizon |
| D3 | the incumbent, per `(employee, day)` | one day |
| D4 concentration | the incumbent, per employee | the horizon |
| Fairness `g(unpopular)` | a **carried count** plus this roster | the horizon **plus history** (`D-108`) |
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

**And the horizon is not the limit people assume.** `D-113` allows any whole number of weeks, and
four is measured. The machinery to reason across weeks is already in the request path; what is missing
is anything in the objective that would spend it.

## The employee side

Ordered roughly by how often it decides whether someone stays in a job.

### E1 — Shift-type consistency

*"I am a morning person, and I have been on mornings for two years."* An employee wants the same shift
type week after week, not a legal-but-arbitrary mixture. This is the single most common thing people
mean by a good schedule, and it is invisible to every term above: two rosters that give someone three
mornings and two rosters that give them a morning, an evening, a night and two mornings score
identically on disruption if neither deviated from its own incumbent.

Needs: a shape carried across the boundary. **Class B.**

### E2 — Day-pattern consistency

Same *days*, for reasons outside work — childcare on Wednesdays, a course on Thursday evenings, a
second job. Distinct from E1: someone can hold their shift type and lose their Wednesday. Often
stronger than E1, because the arrangements it protects have their own contracts.

Note the overlap with `R-AVAIL`: a hard-enough version of E2 is just declared unavailability, and a
tenant that treats it that way already has it. What E2 asks for is the *soft* version — a Wednesday
somebody would rather keep, not one they cannot work.

Needs: a shape, or the promotion of a pattern into `unavailability`. **Class B.**

### E3 — Hours consistency

Income predictability. For a part-timer on variable hours, 20 hours this week and 32 next is a worse
outcome than 26 twice, at identical total pay. `max_hours_this_week` is a ceiling, not a target, and
nothing in the objective prefers an even split. `max_hours_this_period` (`D-123`) makes the *pool*
expressible and deliberately permits the uneven spending this preference objects to — the freedom the
horizon study found is real and buys no coverage is, from the employee's side, the harm.

Needs: a per-employee hours target and a convex penalty on distance from it, over multiple weeks in
one solve. **Class C.**

### E4 — Weekend load

How many weekends worked in a rolling window. The most standardised employee preference in the
literature — the nurse-rostering benchmark set scores it directly, as
[`studies/foreign-incumbent.md`](studies/foreign-incumbent.md) notes when it says none of their
objective is imported.

This one is nearly free: it is the fairness term with a different set. Declare the weekend shifts
unpopular and `g` spreads them. What the current term cannot do is treat *a weekend* as the unit
rather than a shift, which matters for E5.

Needs: nothing new, if a weekend is counted as shifts. A weekend indicator, if it is counted as a
weekend. **Class A.**

### E5 — Whole weekends

Saturday off and Sunday on is not a weekend off. The preference is for the two days to move together —
work both or neither. This is a *structural* preference inside the horizon, not a count, and it is the
first item on this list that the current model could take on with no payload change at all: both days
are in the same week.

Needs: a per-employee, per-weekend pair of indicators and a penalty on the split. **Class C**, but
cheaply — the weeks are already in the horizon.

### E6 — Predictable weekend rotation

*Every other weekend off*, and knowing which. Stronger than E4: E4 is satisfied by two weekends in
four however they fall, and this asks for the alternation. It cannot be expressed in a one-week
horizon at all, and cannot be expressed in a four-week horizon without knowing which weekend the
previous horizon ended on — a count, so it is carryable.

Needs: a horizon holding at least two weekends, plus one carried scalar. **Class C.**

### E7 — Days off in blocks

Two consecutive days off is worth more than two scattered ones, and no rule in the registry says so:
`R-WEEKLY-REST` asks for one uninterrupted window per week and is silent about the rest. Note the
boundary case — a block spanning Sunday to Monday is invisible to a solve that ends on Sunday, so this
is a preference a chained weekly solve systematically undercounts.

Needs: consecutive-day-off indicators, and the boundary carried. **Class C.**

### E8 — Rotation direction, and quick returns

Where shift types do change, the direction matters physiologically: forward rotation
(morning → evening → night) is easier to adapt to than backward. And a *quick return* — an evening
followed by an early morning — can satisfy `R-REST-GAP` and still be the shift pair people complain
about most.

The quick-return half is within-day-pair and could be a soft term today, over the same conflicting
pairs `_conflicting_pairs` already computes for the rest gap. The direction half needs the whole
sequence, including where the previous horizon left the person.

Needs: a soft penalty on named shift-type pairs (cheap), plus a carried last shift type for direction.
**Class A / B.**

### E9 — Night load and recovery

Count of nights in a window, and days off after a night block. The count half is E4's mechanism again.
The recovery half is E7 conditioned on shift type.

Needs: as E4 and E7. **Class A / C.**

### E10 — Requests

*Please not this Saturday. Please this Friday.* Shift-on and shift-off requests, with a weight
reflecting how firmly they were asked. Distinct from `R-AVAIL` in exactly the way E2 is: a request is
priced, an absence is refused.

This is the one item on the list needing no notion of time at all — it is per `(employee, day, shift)`
data with a weight, and the objective is a sum over granted and denied requests. It is also the item
most likely to arrive first from a real tenant, because it is what the staff already send by text
message.

Needs: a request list in the payload and a linear term. **Class D**, and the cheapest thing here.

### E11 — Notice and stability of the published plan

Already the project's subject. `D2`'s notice bands price short notice and `R-PUB-NOTICE` is the
registry's placeholder for the statutory version. Listed for completeness, and to mark the one place
this project is already on the employee's side.

What it does *not* cover: churn measured across publications rather than within one. Somebody whose
week is edited four times, each edit small and each priced against a fresh incumbent, pays nothing
cumulative. That is E11's cross-horizon form and it is a genuine hole.

Needs: for the cumulative form, a count of prior edits carried per employee. **Class A.**

### E12 — Clustering against spreading

Fifteen hours over two days or over five is the same pay and a different life, and which one people
want depends on commute and on whether the job is their only one. It is a preference with no
consensus direction, which makes it a per-employee or per-tenant parameter rather than an objective
this project could pick.

Needs: a per-employee direction and a penalty on days worked for given hours. **Class C/D.**

### E13 — Who they work with

Working alongside a particular person, or not; not being alone on a shift. Cheap to encode and
politically expensive to hold — a preference naming a colleague is a record about that colleague.
`capture.md`'s privacy reasoning applies to it more sharply than to anything currently in the payload.

Needs: pairwise data and a term over pairs. **Class D.**

### E14 — A fair share of the good shifts

The mirror of the fairness term. `D-108` spreads what nobody wants; nobody currently spreads what
everybody wants — the well-tipped Friday evening, the quiet Sunday morning. The same convex encoding
works with the sign flipped: a concave reward, or equivalently a convex penalty on *not* getting them.

Worth naming because the asymmetry is not a design decision anyone recorded. It follows from
`Fairness.unpopular_shifts` being a single set.

Needs: a second declared set and a term on it. **Class A.**

## The employer side

### Em1 — Rotation for capability

Nobody should be the only person who can run Saturday night. If one employee always holds a slot, the
tenant's exposure when they leave, fall ill or take holiday is total — and it is invisible to every
number this service returns, because the roster it produces is legal and fully covered right up to the
day that person is gone.

This is the employer's own reason to want the thing E1 dislikes. It is not a fairness argument.

Needs: a per-`(employee, slot)` count carried across horizons, and a penalty on concentration.
**Class A/B.**

### Em2 — Anti-entrenchment on a slot

The sharper version of Em1, and the reason it is often not negotiable: whoever always closes, always
counts the till, always opens alone is the person a control failure hides behind. This is a
segregation-of-duties argument and it comes from finance rather than from operations. A tenant with an
auditor may have it as a requirement rather than a preference — which would make it a hard rule with
provenance, not an objective term.

Needs: the same counts as Em1, and possibly the classification question `rules.md` asks — when the
only otherwise-legal roster puts the same person on the till all month, is the answer *nothing, and an
explanation*?

### Em3 — Team mixing, or stable teams

Two opposite policies, both defensible, both common. Mixing spreads skill and reduces cliques; stable
pairs are faster and make fewer mistakes. There is no correct answer, which puts this exactly where
`D-108` put unpopularity: **declared, not derived.**

Needs: pairwise co-assignment counts and a signed weight. **Class B/D.**

### Em4 — Development and exposure

Junior staff need hours on the shifts that teach them something, which are usually the busy ones the
seniors hold. `R-SKILL-MIX` can require a senior present; nothing pushes a junior *onto* the peak
shift, and left alone the optimiser will staff every hard shift with the safest available person
forever.

Needs: a target count per employee per slot class, over a window. **Class A/B.**

### Em5 — Continuity for the customer

The same face on the same slot: the regulars' bartender, the ward's familiar nurse, the client's named
cleaner. This is the direct opposite of Em1 and Em2, and it is the employer *agreeing* with E1 against
its own resilience interest.

Needs: exactly Em1's counts, with the weight's sign reversed. That the same data serves both is the
useful part.

### Em6 — Overtime and premium distribution

Which employee absorbs the expensive hours, and how evenly. Blocked on the same thing `replan.md`
blocks the cost model on: with a flat rate every fully staffed roster costs the same, so there is
nothing to distribute. Listed here so that when wage data arrives, this is on the list of things it
unlocks and not only the frontier's cost axis.

Needs: wage data first. **Class A** after that.

### Em7 — Keeping the roster repairable

The one item here that is about *this service specifically*. A roster where every shift's only
eligible substitute is already working is legal, optimal, and one sick call away from an infeasible
replan. The whole project is built on repairing rosters cheaply, and nothing in it prefers a roster
that will be cheap to repair.

This is robustness, and it is the most interesting thing on either list, because it is measurable with
machinery this repo already has: generate a roster, fire every single-absence event at it, and score
the resulting replans. `benchmarks/` does most of that already for the headline claim.

Needs: no payload change to *measure*. A term to *optimise* it is a two-stage problem and is a real
research question, not a weight.

### Em8 — Plan churn as administrative cost

Every change is a message to send, a confirmation to chase and a payroll line to correct. This is the
employer's version of E11, and unlike E11 it is already the objective: the disruption metric prices
exactly this. Named to record that the interests coincide here, which is unusual on this list and is
part of why disruption was a good place to start.

### Em9 — Contract-mix economics

Flexi against contracted hours, students against staff, the horeca flexi wage cap. `rules.md` treats
these as eligibility gates — `R-FLEXI-ELIG`, `R-DIMONA-FLX`, `R-STUDENT-QUOTA` — which is the legality
half. The preference half, *which mix is cheapest across a quarter*, is a cross-horizon budgeting
question and is out of reach for the same reason Em6 is.

Needs: wage data, and quota state carried per employee. **Class A** after that.

## The four classes, and what each would cost

Sorting the whole catalogue by machinery rather than by whose preference it is:

**Class A — a count carried as a scalar.** E4, E9, E11-cumulative, E14, Em1, Em4, Em5, Em6, Em9.
The mechanism already exists and shipped once: `unpopular_shifts_before_horizon` plus a convex
penalty (`D-108`, encoded per `D-055`). Additive, no horizon change, no new solve shape. The cost is
one field per counted thing and a caller who has to compute it — the same bargain `max_hours_this_week`
already strikes, with the same consequence `rules.md` states plainly: correctness comes to depend on a
computation this service does not perform.

**Class B — a shape carried as data.** E1, E2, E8-direction, Em1, Em2, Em3, Em5.
These need to know what the previous roster *looked like*, per employee and slot, not how much of it
there was. That is a second roster in the payload, and it is not the incumbent — see below.

**Class C — a trade between weeks, needing them in one solve.** E3, E5, E6, E7, E12.
The horizon already allows this (`D-113`, up to four weeks measured). What these cost is search time,
and the horizon study measures the bill: search grows 13.5× over 7 to 28 days against build's 5.5×.
They are also the only class for which a longer horizon buys something — see the scoping note below.

**Class D — new data about people, not about time.** E10, E13, Em3.
No time reasoning at all. E10 is the cheapest item in this whole document and probably the first one a
real tenant would ask for.

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
a tenant in exactly the sense `D-108` established for unpopularity — a bakery whose staff have held
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
the objective does not currently have. Even the fairness term could not have shown up: `D-108` records
that the committed set cannot exercise it, because its evenings need a scarce skill.

So the narrower true statement is that a longer horizon buys no coverage **under the shipped
objective**, and the honest way to reopen it is not to re-time the same solve but to add a term that
needs two weeks and re-measure. `D-116`'s conclusion is not wrong; it is scoped, in the same way
`D-081`'s build-dominates premise turned out to be scoped to one week.

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

`replan.md` and `D-108` both say unpopular shifts are **declared by the profile**. They were not:
`Profile` had no `fairness` field, and neither `Fairness` nor
`Employee.unpopular_shifts_before_horizon` appeared in `service/contracts.py`, whose `Strict` base
forbids unknown fields — so a caller who sent either was rejected with a schema error.
`Employee.max_hours_this_period` (`D-123`, `R-MAX-PERIOD`) was missing from the same contract. The
project's one cross-week objective term and its one cross-week hard rule were both callable only from
Python.

**Closed under `D-131`**, along with a second divergence in the same paragraph of `replan.md`: the
warning it said `validation.py` gave when the supplied priors already exceed the tiers did not exist,
and belonged in `profile.remarks` rather than in a module whose every finding rejects a request.

The reason it survived is worth keeping in view while reading the rest of this document. The wire
round-trip test asserts an identity over the committed cases, and no case in the set sets fairness or
a period budget — so it held over the fields the set happens to use. **Every term proposed above will
arrive with the same blind spot**: a field the instance distribution does not contain is a field the
boundary is not tested to carry.
