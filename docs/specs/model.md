# Model

> **Status: outline.** Spec-first component — fill before implementing (T1).

The CP-SAT formulation. Rule semantics live in [`rules.md`](rules.md); this file defines the index
sets, variables and encodings those rules are expressed over.

## Index sets and notation

Notation table first, every symbol defined before use, dimensions annotated. `[TODO]`

- employees, days, shift types, skills, contract types
- the eligible (employee, shift) pairs surviving domain presolve

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
