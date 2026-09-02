# The checker, input validation, and the correctness harnesses

**Status:** Implemented 2026-08-20
**Reconstructed 2026-09-02** from [`checker.py`](../../roster_replan/checker.py),
[`validation.py`](../../roster_replan/validation.py),
[`internals/testing.md`](../internals/testing.md), the mutant catalogue, the records
cited below, and the commits of 2026-08-12 to 2026-08-20. **It is not the work order this
component was built from**; no such document existed
([`spec-reconstruction.md`](spec-reconstruction.md)).
**Depends on:** [`rules.md`](rules.md), which it is the second reading of.

## Objective

A checker that decides whether a roster is legal without ever consulting the model, a
separate layer that rejects malformed requests before either runs, and the harnesses that
hold the two readings against each other.

## Motivation

A solver that checks its own answers proves only that it agrees with itself. The whole
correctness argument of this project is that the rules are read twice, by two pieces of
code that share a schema and never a threshold, and that a disagreement between them is
reported rather than reconciled.

That argument is worth exactly as much as the independence is real, which is why the
independence is a contract rather than a convention, and why the harnesses that compare
the two readings are specified here alongside them.

## Canonical reference

[`internals/testing.md`](../internals/testing.md) owns the checker's three prohibitions,
the seven test layers and what each asserts, the two stated comparison rules, and the
mutation harness. [`guide/rules.md`](../guide/rules.md) owns one *Checker encoding*
bullet per rule. [`internals/design.md`](../internals/design.md) §4 owns the argument for
two readings.

## Governing reference

None. Differential testing between independent implementations is standard technique.

## Parameters and configuration

None of its own. The checker reads every threshold off the payload and **never
recomputes a caller-supplied quantity**: not `max_hours_this_week`, not
`consecutive_days_worked_before_horizon`, not `flexi_eligible`.

## Interfaces

```text
checker.check(roster, instance) -> list[Violation]      plain Python, imports no solver
validation.validate_instance(instance) -> list[InputDefect]  with field paths
```

`Violation` carries the rule ID, employee, day, shift, and the observed value against the
required one. Input validation returns a **different result type** from roster checking,
because a malformed request and an illegal roster are different answers to different
questions ([`D-040`](../decisions.md#d-040)).

## Layering

Three contracts, and they are the component's whole claim:

- *The checker is an independent reading: it never reaches the model or a solver.*
- *The model never reaches the checker.*
- *Input validation is independent of both readings.*

## Build tasks

- [x] Write the checker from [`rules.md`](../guide/rules.md), never from the model.
- [x] Enforce the three prohibitions: never recompute a caller-supplied quantity, never
      read the solver's own slack, never consume the model's eligibility mask.
- [x] Report soft violations as violations, flagged rather than treated as failures.
- [x] Build the seven layers: input validation, brute force in two stages, differential,
      property, metamorphic, golden.
- [x] State the two places the two readings do not compare at identical granularity, and
      make widening either one need a record.

## Test contract

| Claim | Layer |
| --- | --- |
| Malformed payloads are rejected with the right field path | input validation, `test_validation.py` |
| Checker hard-feasible set **equals** model feasible set | brute force **(a)** |
| Solver objective **equals** enumerated optimum, all five metrics | brute force **(b)**, scored by `scoring.py` |
| The two readings name the same violations as sets | the differential harness |
| Replan is idempotent; a fixed seed gives one optimum; relaxation is monotone; the past is never modified | the property layer |
| Relabelling employees leaves the objective invariant; permuting days does too, on a day-decoupled cold instance | the metamorphic layer |
| Committed objective values do not move without a record | the golden layer |

Twelve mutants name a layer here: eight `checker` over `test_differential.py` and
`test_ground_truth.py` (thresholds, slack, a period budget that never binds, weekly rest
and weekly budget spanning the horizon, a consecutive-days off-by-one), three
`validation`, and one `objective`.

**The `objective` mutant is the point of the golden layer.** Changing `published_weight`
from 10 to 12 leaves both readings agreeing perfectly about a different optimum, so
stage (b) sees nothing and only a committed number catches it
([`D-067`](../decisions.md#d-067)).

## Acceptance gate

*Blocks:* every claim in this repository that a roster is legal.

- [x] The checker imports no solver, enforced by contract rather than by review.
- [x] Brute force agrees on the feasible set and on the optimum, 39 micro-instances.
- [x] The differential harness compares violation **sets**, not feasibility bits
      ([`D-041`](../decisions.md#d-041)). Comparing bits is vacuous once a shortfall is
      representable, because the empty roster satisfies every hard rule.
- [x] Every test producing a solution asserts zero hard violations and an `OPTIMAL`
      status ([`D-063`](../decisions.md#d-063)).
- [!] **The harness has a measured limit, and it is not small.** Two week rules were
      named for a week and measured over a horizon, and the differential harness could
      not have caught it, because **both readings were wrong in the same direction**
      ([`D-111`](../decisions.md#d-111)). Two independent readings do not protect against
      a shared premise.
- [!] **Stage (b) passed while a bug was live.** It needs an instance whose incumbent
      contains a presolved-away pair and had none: every micro-instance happened to have
      a clean incumbent, so the drop the replan exists to perform was invisible to the
      objective ([`D-058`](../decisions.md#d-058)). **A ground-truth layer only covers the
      structures its instances contain.**
- [!] **The instance set was blind at every threshold it tested.** The three main shift
      types sit on an eight-hour grid, so a rest threshold of 9 hours was indistinguishable
      from 11, and lowering it in the model passed every ground-truth test. Probing each
      threshold found the same blindness in the weekly budget, the daily maximum, and the
      gross-against-net distinction ([`D-066`](../decisions.md#d-066)). Five instances now
      bracket their thresholds from both sides.
- [!] **A later rule repeated it.** `R-MIN-HOURS`'s micro-instance set a floor of 15
      hours against exactly 15 hours of shifts, so a floor could not be told from a
      ceiling ([`D-140`](../decisions.md#d-140)).

## Measured results

**A fixture set proves a rule exists; only a fixture at the boundary proves it is
enforced at the right number.** That is the durable finding of this component, it was
found by mutation rather than by review, and it then happened again in a rule written
after it was recorded.

Two narrowings are stated rather than hidden, and neither may be widened without a record
([`internals/testing.md`](../internals/testing.md#two-stated-comparison-rules)):

- `R-CONSEC-DAYS` is compared at `(rule, employee)`, dropping the day, because the
  checker names the first breaching day and the model gates every breaching window. A
  day-coordinate error in this one rule is not caught.
- A roster assigning a presolved-away pair is compared on eligibility findings only. Such
  an assignment is not representable, so the model cannot count that body toward
  headcount, hours, a streak or a rest gap. Bought back by comparing the two eligibility
  derivations pair by pair, which localises a disagreement better than a headcount
  comparison three rules away ([`D-045`](../decisions.md#d-045)).

## Out of scope

- **Recomputing anything the caller supplied.** A checker that derives its own budget
  from a reference period it cannot see is testing the caller.
- **A serialised format for the micro-instances.** They are Python constructors; a schema
  and a loader belong with the benchmark set ([`D-064`](../decisions.md#d-064)).
- **Derogating weekly rest to shorten the micro horizon.** Every instance runs seven days
  instead, because inventing a legal citation to quiet the validator is the dishonesty
  the registry exists to prevent ([`D-065`](../decisions.md#d-065)).
- **Committing a roster where the optimum is not unique.** Ties are a function of solver
  version and search order, and committing one trains everyone to regenerate without
  reading the diff.
- **Unconditional day-permutation invariance.** It is false, for three separate couplings
  ([`D-061`](../decisions.md#d-061)).

## Decisions

Reconstructed. Each was decided while the component was built, and the record is the
citation.

1. **How independent is independent?** Independent in rule logic, sharing the payload
   schema and the stated conventions ([`D-003`](../decisions.md#d-003),
   [`D-038`](../decisions.md#d-038)). A shared threshold would defeat the whole
   comparison; a shared dataclass does not.

2. **May shared code default a threshold?** No ([`D-039`](../decisions.md#d-039)). A
   default is a threshold both readings would inherit from one place.

3. **Is input validation part of the checker?** No, a separate layer with a separate
   result type ([`D-040`](../decisions.md#d-040)).

4. **Does the harness compare feasibility or violations?** Violations, as sets
   ([`D-041`](../decisions.md#d-041)).

5. **Does relaxation monotonicity cover coverage?** No
   ([`D-062`](../decisions.md#d-062)). Relaxing a rule expands the feasible set; relaxing
   coverage changes the objective through the shortfall term, so comparing optima across
   it is meaningless. One test asserts at least one relaxation actually moves the
   objective, so the suite cannot pass vacuously.

6. **Is the suite-wide invariant enforced automatically?** No, a shared `solved()` helper
   ([`D-063`](../decisions.md#d-063)), so a test calling the solver directly opts out and
   should have a reason to.

---

*The ledger: [`README.md`](README.md). The layers:
[`internals/testing.md`](../internals/testing.md). The harness over the layers:
[`mutation.md`](mutation.md).*
