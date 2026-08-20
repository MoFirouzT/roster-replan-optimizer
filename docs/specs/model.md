# Model

> **Status: reconciled with `model.py` and `domain.py`.** Index sets, decision variables, the gate
> mechanism, presolve, symmetry and the payload schema describe what is built, and the four encoding
> questions this file deferred to a study are now measured rather than assumed — presolve ([`D-045`](../decisions.md#d-045)),
> symmetry ([`D-087`](../decisions.md#d-087)), the `regular` automaton ([`D-088`](../decisions.md#d-088)) and pattern variables ([`D-009`](../decisions.md#d-009)), each with a
> study in [`docs/studies/`](../studies/README.md). Presolve was confirmed; the other three
> alternatives lost, two of them to this file's own stated suspicions.
>
> Still outline: the wire format (JSON, versioning, the Pydantic boundary — all owned by the service),
> and the forecast interface, which is interface-only by design.

The CP-SAT formulation. Rule semantics live in [`rules.md`](rules.md); this file defines the index
sets, variables and encodings those rules are expressed over.

## Index sets and notation

Every symbol used by a rule predicate in [`rules.md`](rules.md) is defined here. The symbols below
and the payload schema are settled and in use.

| Symbol | Type | Meaning |
|---|---|---|
| `E`, `e` | index set | Employees in the tenant |
| `D`, `d` | index set | Days in the horizon, `0`-indexed from its start |
| `W`, `w` | index set | **Weeks in the horizon** — seven days from its start, the last clipped to it. `week(d) = d // 7` ([`D-111`](../decisions.md#d-111)) |
| `T`, `s` | index set | Shift types (a start time and a length, per tenant) |
| `O ⊆ D × T` | index set | **Open shift instances** — the `(d, s)` pairs with `req[d, s] > 0` |
| `K`, `k` | index set | Skills |
| `x[e, d, s]` | bool | `1` iff employee `e` is assigned shift instance `(d, s)` |
| `x̄[e, d, s]` | bool, data | The **incumbent** published roster. Absent on a cold solve |
| `req[d, s]` | int ≥ 0, data | Required headcount for a shift instance |
| `start(d, s)`, `end(d, s)` | hours | Bounds of a shift instance from the horizon start, `[start, end)` |
| `now` | hours, data | The replan instant. Required for a replan, absent on a cold solve |
| `absences[e]` | interval set, data | Periods `e` cannot work as a matter of fact |
| `unavailability[e]` | interval set, data | Periods `e` declared they will not work |
| `skills[e] ⊆ K` | set, data | Skills `e` holds |
| `req_skills[d, s] ⊆ K` | set, data | Skills a shift instance requires of **each** assignee |
| `skill_mix[d, s]` | entry set, data | `(skill, minimum, class, provenance)` composition requirements |
| `eligible ⊆ E × O` | derived | Pairs surviving domain presolve — see [Presolve](#presolve) |
| `span(d, s)` | hours | `end(d, s) − start(d, s)` — the **gross** span, breaks included |
| `break_hours(s)` | hours, data | Statutory break falling inside the span |
| `work_hours(d, s)` | hours | `span(d, s) − break_hours(s)` — **net** working time |
| `u[d, s]` | int ≥ 0 | Coverage shortfall — `R-COVER`'s slack |
| `v[d, s, k]` | int ≥ 0 | Qualified-coverage shortfall — `R-SKILL-MIX`'s slack, soft entries only |
| `w[e, d]` | bool | `1` iff `e` works at all on day `d`. Reified from `x` for `R-CONSEC-DAYS` |

Three further caller-supplied quantities — `max_hours_this_week[e]`,
`consecutive_days_worked_before_horizon[e]` and `last_shift_end_before_horizon[e]` — are defined under
[Caller-computed quantities](#caller-computed-quantities) below.

**Gross and net are both carried, because different rules need different ones.** Statutory rest breaks
are not working time, so a shift's span and its working time differ — and the rules do not agree on
which they mean:

- `R-MIN-SHIFT` tests art. 21's *work period*, and a "prestatie" is a continuous period that may
  contain short meal or coffee breaks. It reads **`span`**.
- `R-MAX-WEEKLY` and `R-MAX-DAILY` are working-time ceilings, and breaks are not working time. They
  read **`work_hours`**.

Collapsing the two into one symbol would therefore make one of those rules wrong, silently, by roughly
a break per shift. The payload carries `span` and `break_hours` and derives `work_hours`; there is no
single `hours(d, s)`.

Shift instances are `(day, shift type)` pairs, not calendar dates: `end(d, s)` may fall on `d + 1`
when a shift crosses midnight. Rule predicates are written over timestamps rather than day indices
wherever that distinction can change an answer.

Intervals are half-open throughout, in both this spec and the checker. Two shifts where one ends
exactly as the other begins do not overlap.

## Input contract

[`roster_replan/domain.py`](../../roster_replan/domain.py) is the normative schema; this section
describes it. It is the **only** module the model and the checker may both import, and what it may
hold is fixed by the [independence rule](rules.md#independence-rule): data containers and the stated
conventions, no rule predicate and no rule threshold ([`D-038`](../decisions.md#d-038), [`D-039`](../decisions.md#d-039)).

The wire format landed with the service:
[`service.md#contracts`](service.md#contracts-built) and `roster_replan/service/contracts.py`. It is
a **separate schema** rather than a serialisation of this one ([`D-090`](../decisions.md#d-090)), so what follows stays the
in-process schema and is free to change without breaking a caller. The two are held together by a
round-trip identity test rather than by convention.

### Time is hours from the horizon start, not a calendar timestamp

Every time quantity — shift bounds, `now`, `published_through`, interval endpoints — is a float
counting hours from the start of the horizon. Values before the horizon are negative, which is what
makes `last_shift_end_before_horizon[e]` an ordinary number rather than a special case.

Calendar timestamps belong at the API boundary. The rules are arithmetic, and keeping them off
the calendar keeps them testable without one: no timezone, no DST discontinuity, and a micro-instance
that reads as `Interval(6.0, 12.0)` rather than as a date.

### The containers

| Container | Carries |
| --- | --- |
| `Instance` | `days`, `shift_types`, `employees`, `open_shifts`, `params`, and the replan inputs `now`, `incumbent`, `published_through`, `disruption` |
| `ShiftType` | `label`, `start_hour` (within its day), `span_hours`, `break_hours`; `work_hours` derived ([`D-037`](../decisions.md#d-037)) |
| `OpenShift` | `day`, `shift`, `required`, `required_skills`, `skill_mix` — the `(d, s)` pairs that make up `O` |
| `Employee` | `name`, `contract`, `skills`, `absences`, `unavailability` ([`D-020`](../decisions.md#d-020)), the caller-computed quantities below, the per-day eligibility gates ([`D-032`](../decisions.md#d-032)), and `hourly_rate` |
| `SkillMixEntry` | `skill`, `minimum`, `hard`, `provenance` — class declared per entry ([`D-025`](../decisions.md#d-025)) |
| `RuleParams` | Every rule threshold, supplied explicitly with no defaults ([`D-039`](../decisions.md#d-039)), plus `derogation_basis` |
| `Disruption` | Objective parameters; [`replan.md`](replan.md) owns their semantics |
| `NoticeBand` | `within_hours`, `multiplier` — tested in order, last one unbounded |

The roster itself is a `frozenset` of `(employee, day, shift)` triples: the assignments that are `1`.

### `None` means "not supplied", never a default

`max_hours_this_week`, `max_daily_hours`, `last_shift_end_before_horizon`, `flexi_eligible` and
`dimona_ok` are all optional in the container and **mandatory in practice** — input validation rejects
a payload that omits one where a rule needs it, rather than substituting anything.

The failure mode this avoids is specific. A defaulted `max_hours_this_week` is the per-week ceiling
[`D-014`](../decisions.md#d-014) exists to reject. An empty `flexi_eligible` would *deny* eligibility where the caller merely
forgot to say, which is a different answer wearing the same shape. Neither is detectable downstream,
because both produce a perfectly plausible roster.

### Caller-computed quantities

Some rule parameters cannot be derived from a one-week payload. The caller computes them and the
solve consumes them as opaque data.

| Field | Type | Owner | Consumed by |
|---|---|---|---|
| `max_hours_this_week[e]` | hours, per employee | caller | `R-MAX-WEEKLY` |
| `consecutive_days_worked_before_horizon[e]` | days, per employee | caller | `R-CONSEC-DAYS` |
| `last_shift_end_before_horizon[e]` | hours (negative), per employee | caller | `R-REST-GAP`, `R-WEEKLY-REST` |
| `unpopular_shifts_before_horizon[e]` | count, per employee | caller | the fairness term ([`D-108`](../decisions.md#d-108)) |

`max_hours_this_week[e]` is the reference-period budget described in
[`rules.md`](rules.md#the-reference-period-and-why-r-max-weekly-is-a-budget): the caller resolves
the rolling quarter or year into a single number so the solve horizon can stay at one week. It is a
week's hours and binds in **every** week of the horizon ([`D-111`](../decisions.md#d-111)), which is the same constraint while
the horizon is one week and a different one after that. A per-week ceiling that varies by week is not
expressible in one number and is the payload change [`D-111`](../decisions.md#d-111) defers.

The other two exist for the same structural reason. A week boundary is an artifact of the payload,
not of the employee's working life — someone who worked the six days before Monday, or who finished
a night shift at 07:00 on Monday, is constrained on Monday by history the horizon cannot see.
Without these fields every horizon boundary silently resets the rules that span it.

### Rule parameters a caller opts into

Three fields switch a rule on rather than parameterising one that is always present. Absent means the
caller is not asking for the rule, which is ordinary rather than a defect — `R-MAX-PERIOD` established
the pattern ([`D-123`](../decisions.md#d-123)) and [`D-135`](../decisions.md#d-135) follows it.

| Field | Type | Consumed by | Absent means |
|---|---|---|---|
| `max_hours_this_period[e]` | hours, per employee | `R-MAX-PERIOD` | nothing to add beyond the weekly ceiling |
| `max_weekends[e]` | weekends, per employee | `R-MAX-WEEKENDS` | no weekend budget |
| `min_consecutive_days_off[e]` | days, per employee | `R-MIN-DAYS-OFF` | no minimum; 1 is the same as absent |
| `params.weekend_days` | day positions in a week | `R-MAX-WEEKENDS` | no weekend is defined, so the rule is off |

`weekend_days` is the only parameter here stated in a coordinate system the caller does not otherwise
use, and it is asked for rather than derived because **this domain has no calendar**: a week is a
position in the horizon and never a Monday. Validation rejects a day outside `0…6` rather than
silently ignoring it.

**The checker verifies against the supplied values and never recomputes them.** A checker that
derives its own budget from data it cannot see is testing the caller rather than the roster, and
would disagree with the model for reasons that are not defects in either.

## Decision variables

Assignment booleans `x[e, d, s]`, one per pair that survives presolve — plus the slacks and indicators
the rules need:

| Variable | Domain | Owner |
|---|---|---|
| `x[e, d, s]` | bool | assignment |
| `u[d, s]` | `0..req[d, s]` | `R-COVER` shortfall, priced |
| `o[d, s]` | `0..` | `R-COVER` overage, gated to zero |
| `v[d, s, k]` | `0..m` | `R-SKILL-MIX` shortfall, soft entries only |
| `w[e, d]` | bool | worked-day indicator, reified for `R-CONSEC-DAYS` |
| `r[e, w, j]` | bool | `R-WEEKLY-REST` candidate-window selector, per week ([`D-111`](../decisions.md#d-111)) |

**A variable exists** for every eligible pair, and additionally for any pair the incumbent assigned,
eligible or not ([`D-058`](../decisions.md#d-058)). Without that second case an already-illegal past cannot be represented and
"the past itself is illegal" becomes indistinguishable from a clean solve — and, just as important, a
deviation from the incumbent becomes uncountable, so the objective silently understates the cost of
exactly the change the replan exists to make. Such a pair is still ineligible: the exclusion becomes a
*gated* `x = 0` rather than an outright fixing ([`D-059`](../decisions.md#d-059)), so a roster assigning it is reported rather
than merely rejected.

**Durations are carried in minutes.** CP-SAT is integral and `work_hours` is not. The conversion is
arithmetic rather than a rule threshold, so it lives in the model rather than in the shared schema.

- **Rejected, measured** ([`D-009`](../decisions.md#d-009)): pattern/column variables. Built in full and compared, not
  estimated — see [`studies/pattern-encoding.md`](../studies/pattern-encoding.md). They tie on a
  replan, where the pinned past leaves only 36–122 legal patterns for a whole tenant, and fail to
  prove optimality within 30 seconds on a cold week where the assignment model takes 20 milliseconds.
  "Dramatically stronger" was the wrong expectation at this horizon, and the mechanism is the one
  symmetry breaking exists for: thousands of near-identical columns create exactly the symmetry the
  assignment model turns out not to have.

## Constraints

Per-rule encodings and their rationale live in [`rules.md`](rules.md), one *Model encoding* bullet per
rule, and are deliberately not restated here. This section owns only what cuts across them.

### Assumption literals

**Every hard constraint instance is gated on an assumption literal** ([`D-002`](../decisions.md#d-002)). Not decoration — three
separate things depend on it:

1. A failed solve returns the conflicting rule instances rather than a bare `INFEASIBLE`.
2. The differential harness needs the model to *report* violations, not merely refuse rosters. With all
   assignments fixed, each gate can be true exactly when its constraint holds, so **maximising the
   number of true gates leaves precisely the violated constraints false** ([`D-044`](../decisions.md#d-044)) — one solve
   enumerates them all, where a core would explain one conflict and hide the rest.
3. The *monotone objective under relaxation* property test needs relaxation to be expressible.

`R-COVER`'s ceiling is gated as `o[d, s] == 0` rather than folded into the slack's domain, so that an
overstaffed roster can be reported instead of silently rejected ([`D-043`](../decisions.md#d-043)).

**Sufficient, not minimal** ([`D-048`](../decisions.md#d-048)). CP-SAT returns a set of assumptions that explains the infeasibility, with
no guarantee it is the smallest. The explainer is specified against a *minimal* core, which needs
iterative deletion on top — solve, drop a gate, re-solve, keep what stays necessary. That reduction
belongs with the explainer; the gap is recorded here so it is not discovered there.

### The `regular` automaton

`R-CONSEC-DAYS` and `R-WEEKLY-REST` are both sequence rules, and both currently use the naive encoding —
sliding-window sums and candidate windows respectively. The automaton expresses both in one propagator
and is the textbook choice, which is exactly why it is a **study rather than an assumption**: at a
seven-day horizon the window count is trivially small, and the study should confirm the automaton wins
rather than take it on faith.

**It does not win** ([`D-088`](../decisions.md#d-088)). At this horizon the window count is not merely small, it is **one**, so
the automaton competes against a single linear inequality over seven booleans and is 19% slower to
search on 28 of 28 cases. It also gates only per employee, where the window encoding names the day the
streak breached — the coordinate the checker reports and `violations()` matches on. Kept behind
`build(sequence="automaton")` for the study, and revisited at a horizon beyond about two weeks.
`R-WEEKLY-REST` is not a candidate either way: a continuous 35-hour free run measured in hours is not
expressible by a day-level automaton. See
[`studies/regular-constraint.md`](../studies/regular-constraint.md).

## Objective

Defined in [`replan.md`](replan.md). This file owns feasibility; that file owns preference.

## Presolve

Most (employee, shift) pairs are impossible: unavailable, wrong skill, wrong contract, Dimona gate.
Eliminate them before the solver sees them.

**Measured: a quarter of the model, 28% off build time and 14% off search, on 28 of 28 paired cases**
([`studies/presolve.md`](../studies/presolve.md)). Free, as claimed — the exclusion table is computed
either way because the reasons have to be retained ([`D-045`](../decisions.md#d-045)). Not "the largest single win", which was
the earlier wording: build time dominates search at these sizes ([`D-081`](../decisions.md#d-081)), and this takes a quarter
off the larger half. The largest single win is memoising `Instance.window` ([`D-092`](../decisions.md#d-092)) — *not* caching
the compiled model, which was the obvious candidate and hits 0 of 144 replan solves ([`D-093`](../decisions.md#d-093)).

`R-AVAIL`, `R-SKILL`, `R-FLEXI-ELIG` and `R-DIMONA-FLX` are enforced *entirely* this way — by removing
variables, not by adding rows.

**The exclusion reasons must be retained** ([`D-045`](../decisions.md#d-045)). A removed pair can never be reported by a constraint that
does not exist, so presolve keeps a map from excluded pair to the rules that excluded it. Without it an
assignment to an ineligible person would be invisible rather than rejected.

This has a consequence for the differential harness that is easy to get wrong: an assignment to an
excluded pair is not representable, so the model cannot count that body toward *anything* — headcount,
weekly or daily hours, a consecutive-day streak, a rest gap. See the stated comparison rules in
[`validation.md`](validation.md#two-stated-comparison-rules).

## Symmetry

Interchangeable employees create exponentially many equivalent solutions. Lexicographic ordering
constraints, and the interaction with the disruption objective (which partially breaks symmetry on
its own — quantify this rather than assuming it).

**Not implemented, and now measured rather than assumed** ([`D-087`](../decisions.md#d-087)). Across 24 committed cases there
are **3** interchangeable employees in total, in one case — so lexicographic ordering costs about 4% of
build time and returns a coin flip on search.

The stated reason above was partly wrong. The incumbent does suppress symmetry, roughly halving it, but
the larger effect is the generator giving every employee an independently sampled budget and
availability, so two employees are rarely identical *before* any incumbent exists. That also bounds the
null: run on a workforce built to be interchangeable, the lever is worth 20% of total time, so it works
and this distribution does not present what it needs. Revisit for a tenant with a substantial group
identical in contract, skills, budget and availability. See
[`studies/symmetry-breaking.md`](../studies/symmetry-breaking.md).

## The forecast interface `[not implemented]`

Upstream of the optimiser sits demand forecasting — availability, absences, peak moments, weather,
revenue, skills. Structurally identical to a dispatch problem: forecast → optimise → commit under
constraints. This section defines the input contract that layer would satisfy. It is not built.
