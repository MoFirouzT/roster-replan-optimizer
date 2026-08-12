# Model

> **Status: outline.** Spec-first component — fill before implementing (T1).

The CP-SAT formulation. Rule semantics live in [`rules.md`](rules.md); this file defines the index
sets, variables and encodings those rules are expressed over.

## Index sets and notation

Every symbol used by a rule predicate in [`rules.md`](rules.md) is defined here. Contract types and
the full payload schema are still `[TODO]`; the symbols below are settled and in use.

| Symbol | Type | Meaning |
|---|---|---|
| `E`, `e` | index set | Employees in the tenant |
| `D`, `d` | index set | Days in the horizon, `0`-indexed from its start |
| `T`, `s` | index set | Shift types (a start time and a length, per tenant) |
| `O ⊆ D × T` | index set | **Open shift instances** — the `(d, s)` pairs with `req[d, s] > 0` |
| `K`, `k` | index set | Skills |
| `x[e, d, s]` | bool | `1` iff employee `e` is assigned shift instance `(d, s)` |
| `x̄[e, d, s]` | bool, data | The **incumbent** published roster. Absent on a cold solve |
| `req[d, s]` | int ≥ 0, data | Required headcount for a shift instance |
| `start(d, s)`, `end(d, s)` | timestamp | Absolute bounds of a shift instance, `[start, end)` |
| `now` | timestamp, data | The replan instant. Required for a replan, absent on a cold solve |
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

`[TODO]` Full payload schema. The fields below are settled and are recorded here because another
spec depends on them.

### Caller-computed quantities

Some rule parameters cannot be derived from a one-week payload. The caller computes them and the
solve consumes them as opaque data.

| Field | Type | Owner | Consumed by |
|---|---|---|---|
| `max_hours_this_week[e]` | hours, per employee | caller | `R-MAX-WEEKLY` |
| `consecutive_days_worked_before_horizon[e]` | days, per employee | caller | `R-CONSEC-DAYS` |
| `last_shift_end_before_horizon[e]` | timestamp, per employee | caller | `R-REST-GAP`, `R-WEEKLY-REST` |

`max_hours_this_week[e]` is the reference-period budget described in
[`rules.md`](rules.md#the-reference-period-and-why-r-max-weekly-is-a-budget): the caller resolves
the rolling quarter or year into a single number so the solve horizon can stay at one week.

The other two exist for the same structural reason. A week boundary is an artifact of the payload,
not of the employee's working life — someone who worked the six days before Monday, or who finished
a night shift at 07:00 on Monday, is constrained on Monday by history the horizon cannot see.
Without these fields every horizon boundary silently resets the rules that span it.

**The checker verifies against the supplied values and never recomputes them.** A checker that
derives its own budget from data it cannot see is testing the caller rather than the roster, and
would disagree with the model for reasons that are not defects in either.

## Decision variables

`[TODO]` Assignment booleans (employee × day × shift), and their alternatives.

- **Rejected/deferred:** pattern/column variables — dramatically stronger formulations, evaluated
  as a T2 study at these instance sizes. Record the outcome even if null.

## Constraints

One subsection per rule ID from the registry. Each states the encoding and why it was chosen over
the alternatives — in particular the `regular`/automaton constraint for legal shift sequences
versus its linear expansion.

## Objective

Defined in [`replan.md`](replan.md). This file owns feasibility; that file owns preference.

## Presolve

Most (employee, shift) pairs are impossible: unavailable, wrong skill, wrong contract, Dimona gate.
Eliminate them before the solver sees them. Often the largest single win, and free.

## Symmetry

Interchangeable employees create exponentially many equivalent solutions. Lexicographic ordering
constraints, and the interaction with the disruption objective (which partially breaks symmetry on
its own — quantify this rather than assuming it).

## The forecast seam `[interface only, not implemented]`

Upstream of the optimiser sits demand forecasting — availability, absences, peak moments, weather,
revenue, skills. Structurally identical to a dispatch problem: forecast → optimise → commit under
constraints. This section defines the input contract that layer would satisfy. It is not built.
