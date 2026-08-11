# Validation

> **Status: outline.** Spec-first component — fill before implementing (T1).

## The independent checker

`(roster, context) -> list[Violation]`. Plain Python. **Imports no solver.** Stateless.

A second reading of [`rules.md`](rules.md), written without reference to the model implementation.
Shares no code with it — enforced by an import-linter contract in CI.

Structurally required, not a nice-to-have: under any formulation without hard-constraint
guarantees (penalties inside a local search, or a time-boxed solve accepting a gap), feasibility is
not guaranteed by construction. Independent verification is the only thing that makes a legality
claim true rather than assumed.

`Violation` carries: rule ID, employee, day, shift, and the observed vs. required values.

## Test layers

| Layer | Asserts |
|---|---|
| Brute force | N≤6, 3 days, ≤2 shift types: exhaustive enumeration → solver objective **equals** true optimum, on ~20 committed micro-instances |
| Differential | Random rosters (mostly infeasible): `model_feasible(r) ⟺ checker_feasible(r)`; mismatch prints the rule ID |
| Property | Idempotent replan on a no-change input · byte-identical output under a fixed seed · monotone objective under constraint relaxation · past shifts never modified |
| Metamorphic | Employee relabelling leaves the objective invariant; day permutation stays structure-consistent |
| Golden | Committed scenarios with committed objective values; a diff fails CI until a `decisions.md` entry justifies it |

**Suite-wide invariant:** every test that produces a solution asserts zero checker violations on it.
Not a separate test — a property of the harness.

Feasibility-checking a fixed roster in CP-SAT is fixing all variables and solving, so the
differential harness is small. Build it early.
