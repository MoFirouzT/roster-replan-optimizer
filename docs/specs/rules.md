# Rules

The canonical registry of scheduling rules.
Every rule has a stable ID used identically in this spec, the CP-SAT model, the independent checker, the `Violation` objects and the infeasibility explainer.
**One vocabulary end to end.**

`model.md` and `validation.md` reference IDs from this file and do not restate rule semantics.

> **Status: outline.** Each rule below needs: exact predicate, parameters and their per-tenant
> configurability, hard/soft classification, provenance for legal rules, and the failure message
> the explainer renders.

## Classification

- **Structural hard** — encoded as constraints. Infeasibility is a legitimate answer.
- **Soft** — penalised in the objective, with its weight on a stated scale (see `replan.md`).
- **Pinned** — fixes variables rather than constraining them.

## Registry

| ID | Rule | Class | Parameters | Provenance |
|---|---|---|---|---|
| `R-COVER` | Each open shift is staffed to its requirement | hard *(soft variant TBD — see `replan.md`)* | per shift | operational |
| `R-AVAIL` | No assignment against declared unavailability or absence | hard | per employee/day | operational |
| `R-SKILL` | Assigned employee holds the shift's required skill | hard | per shift/employee | operational |
| `R-PIN-PAST` | Shifts starting before `now` are immutable | pinned | `now` | operational |
| `R-MIN-SHIFT` | Minimum shift length — 2h horeca, 3h general | hard | hours, per tenant | labour law `[CITE]` |
| `R-REST-GAP` | Minimum rest between consecutive shifts | hard | hours | labour law `[CITE]` |
| `R-MAX-WEEKLY` | Maximum hours this week, as a supplied per-employee budget | hard | hours, per employee | labour law `[CITE]` |
| `R-MAX-DAILY` | Maximum hours per day | hard | hours, per contract | labour law `[CITE]` |
| `R-CONSEC-DAYS` | Maximum consecutive working days | hard | days | labour law `[CITE]` |
| `R-WEEKLY-REST` | Minimum uninterrupted weekly rest | hard | hours | labour law `[CITE]` |
| `R-FLEXI-ELIG` | Flexi-job eligibility conditions | hard | per employee | labour law `[CITE]` |
| `R-DIMONA-FLX` | Same-day `FLX` Dimona filing as an eligibility gate | hard | filing state | labour law `[CITE]` |
| `R-STUDENT-QUOTA` | Student-worker hour quota | hard, optional | hours/year | labour law `[CITE]` |
| `R-SUNDAY` | Sunday and public-holiday work restriction | hard, optional | derogation set | labour law `[CITE]` |
| `R-BREAK` | In-shift break entitlement | hard, optional | minutes per hours worked | labour law `[CITE]` |
| `R-PT-MIN` | Part-time minimum shift length and weekly hours | hard, optional | hours | labour law `[CITE]` |
| `R-PUB-NOTICE` | Variable-schedule publication notice | soft, optional | days | labour law `[CITE]` |

`R-MAX-DAILY`, `R-CONSEC-DAYS` and `R-WEEKLY-REST` land in T1 — they are structural, cheap, and
belong in the checker before it is written rather than bolted on after.
The four rules marked *optional* are profile-gated and land in T2;
a tenant that does not enable them never pays for them.

`[CITE]` — every legal rule needs a named source before T1 closes. A legality claim without
provenance is a guess, and the checker is the component whose whole value is that it is not one.

## The reference period, and why `R-MAX-WEEKLY` is a budget

Average weekly hours in Belgian labour law are measured over a **rolling reference period** — a
quarter or a year — not per calendar week. A per-week ceiling is therefore not the rule; it is an
approximation of it, and one that is wrong in both directions. It forbids a legal heavy week that
a light week would compensate, and it permits thirteen consecutive weeks at the ceiling.

The obvious fix is to extend the solve horizon to the reference period. That is rejected: it
multiplies instance size by an order of magnitude and destroys the interactive latency the whole
service is built around.

**Instead the reference period is resolved upstream and enters the solve as data.** The caller
computes, per employee, the hours already worked in the current period and the working time
remaining in it, and supplies a single `max_hours_this_week` budget. The solver and the checker see
only that number. The horizon stays one week, the rule stays local, and the semantics are correct.

The cost is stated rather than hidden: **correctness now depends on a computation this service does
not perform.** Two consequences follow, and both are binding.

- `model.md` owns the input contract for the budget and names the caller as its owner.
- The checker verifies assignments against the *supplied* budget. It must not recompute it from a
  period it cannot see — a checker that invents its own budget is testing the caller, not the roster.

## Per rule (template)

### `R-EXAMPLE` — short name

- **Statement.** One sentence, in the planner's language.
- **Predicate.** The exact condition, over the index sets defined in `model.md`.
- **Class.** Hard / soft / pinned.
- **Parameters.** Names, units, defaults, and whether a tenant profile can override them.
- **Model encoding.** How the constraint is expressed in CP-SAT, and why that encoding.
- **Checker encoding.** How it is verified independently. Must not reference the model encoding.
- **Explainer text.** What the planner sees when this rule blocks a solve.
- **Provenance.** Source for legal rules.

## Independence rule

The model and the checker are two readings of this document. **They share no code** — not a
constants module, not a helper. The duplication is deliberate: it is what makes the differential
harness meaningful. Enforced by an import-linter contract in CI.
