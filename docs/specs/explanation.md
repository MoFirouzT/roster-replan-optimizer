# Explanation, prose, and minimal cores

**Status:** Implemented 2026-08-18
**Reconstructed 2026-09-02** from [`explain.py`](../../roster_replan/explain.py),
[`prose.py`](../../roster_replan/prose.py), [`core.py`](../../roster_replan/core.py),
[`guide/api.md`](../guide/api.md), [`internals/design.md`](../internals/design.md) §7, the
mutant catalogue, and the commits of 2026-08-13 to 2026-08-18, and **it is not the work
order this component was built from**: this project had none
([`documentation.md`](documentation.md#specs-for-the-built-components)).
**Depends on:** [`validation.md`](validation.md), whose checker it answers from.

## Objective

Tell a planner why a shift came back short, in numbers and in a sentence, where the
numbers are proved by the independent checker and the sentence is a rendering of them
that cannot introduce a fact.

## Motivation

An optimiser that returns a short roster and no reason is worse than useless: the planner
has to reconstruct the search by hand. The obvious first feature is explaining an
infeasible solve, and that is the wrong one. With a priced coverage floor a cold solve is
essentially never infeasible ([`D-047`](../decisions.md#d-047)), so an explainer built for
infeasibility first is built for a case that does not occur.

What does occur is a shift coming back short, on 16 of 72 committed cases.

## Canonical reference

[`guide/api.md`](../guide/api.md) owns what comes back when a shift is short.
[`internals/design.md`](../internals/design.md) §7 owns the argument for where a model may
speak.

## Governing reference

None. What bounds the language model here is a local validator, not a published method.

## Parameters and configuration

The prose layer is the only place in this project that calls a language model, and it is
unreachable from the service by contract.

## Interfaces

```text
explain.explain(...)          why each person could not fill the shift
core.minimal_core(...)        a minimal core by deletion, asked with no objective set
prose.render(...)             the sentence, validated before it is returned
```

Structured fields **and** prose, together. If a reader distrusts the sentence they read
the numbers; if they cannot parse the numbers they read the sentence. Prose alone would
make a model's phrasing load-bearing.

## Layering

*The explainer answers from the checker, never from the model.* `explain.py` may not
import `model`, `disruption` or `ortools`.

That is the whole design in one contract. An explanation derived from the model's own
exclusion table is the solver's account of itself: a wrong exclusion produces a wrong
explanation that agrees with it and nothing shows. Asking the independent reading makes a
wrong exclusion **contradict** the roster, which is a finding rather than a consistent lie
([`D-097`](../decisions.md#d-097)).

## Build tasks

- [x] Explain a shortfall first, not an infeasibility.
- [x] Answer from the checker, and forbid the model by contract.
- [x] Reduce a core by deletion, asking the feasibility question with no objective set.
- [x] Report the minimal core **and** how large the sufficient one was.
- [x] Confine the language model to phrasing a finding it cannot alter, behind a
      validator.

## Test contract

| Claim | Layer |
| --- | --- |
| Nobody is reported as unexplained | `test_explain.py::explain-never-reports-unexplained` |
| A rule already broken before the replan is still accounted for | `explain-ignores-rules-already-broken` |
| Every blocking rule is reported, not only the first | `explain-reports-only-the-first-rule` |
| The prose validator rejects an invented name | `test_prose.py::prose-validator-ignores-invented-names` |
| The prose layer never invents a weekday | `prose-invents-a-weekday-without-a-calendar` |
| An unexplained case is warned about rather than smoothed over | `prose-drops-the-unexplained-warning` |
| The core is minimal, and the necessary gates are kept | `test_core.py`, two mutants |

`prose-invents-a-weekday-without-a-calendar` is the one worth naming: **this domain has
no calendar.** A week is a position in the horizon and never a Monday, so a sentence
naming a weekday is a fact the model made up.

## Acceptance gate

*Blocks:* nothing downstream.

- [x] The explainer imports no solver, enforced by contract.
- [x] Every person off a short shift is blocked by a rule the checker names.
- [x] The core is reported with the size of the sufficient one beside it, so a reader can
      see how much was removed.
- [!] **The deferral was right and its diagnosis was wrong**
      ([`D-100`](../decisions.md#d-100), which retires
      [`D-048`](../decisions.md#d-048)). The earlier record deferred core minimisation
      because a sufficient core "can name rule instances that are not actually
      necessary". Measured, that understates it badly: `solve` returns **159 to 219 gates
      naming eight rules** where the real conflict is two.
- [!] **Deletion is not the lever, and is currently a null.** Asking the same question as
      pure feasibility, with no objective set, returns **2 to 3 gates**: an 80-fold
      reduction from one line rather than from a loop of solves. Running deletion
      afterwards then drops **zero** gates on all five constructed instances.

## Measured results

**The deletion loop is kept even though it is a null**, and the reason is worth separating
from its measured effect: it **guarantees** minimality where dropping the objective merely
achieves it. The two changes compose in one order only. Minimising a 160-gate core would
be 160 solves; on a 2-gate core it is three. **Dropping the objective is what makes the
guarantee affordable.**

**Minimal is not smallest.** A different deletion order reaches a different minimal core,
so the order is fixed to keep the result reproducible.

**The design yields an invariant worth more than the feature.** Because the shortfall
weight dominates, an optimal solver adds anyone it legally can, so every person off a
short shift is blocked by something, and an unexplained person is a defect in one of the
two readings rather than a gap in the prose.

## Out of scope

- **An infeasibility explainer as the first feature.** Re-scoped before the work opened,
  and the measurement confirmed it: none of the committed cases is infeasible
  ([`D-097`](../decisions.md#d-097)).
- **Deriving reasons from `model.exclusions()`.** It retains them and would need no
  recomputation, and it is the solver's account of itself.
- **Letting the language model identify a finding.** It phrases a proven one and never
  identifies one ([`D-012`](../decisions.md#d-012),
  [`D-013`](../decisions.md#d-013)).
- **Reaching a language model from the service.** Forbidden by import contract.
- **Guessing at what could not be established.** `unclear` is for what could not be said,
  never for what was assumed ([`D-103`](../decisions.md#d-103)).

## Decisions

Reconstructed. Each was decided while the component was built, and the record is the
citation.

1. **Shortfall or infeasibility first?** Shortfall
   ([`D-097`](../decisions.md#d-097)), because with a priced coverage floor the
   infeasible case does not arise.

2. **Where does the explanation come from?** The checker, never the model or presolve
   ([`D-097`](../decisions.md#d-097)).

3. **What may the language model do?** Render a finding it cannot alter, inside a
   validator that bounds what it may say
   ([`D-012`](../decisions.md#d-012)). The core comes from the solver and the prose from
   the model, **never the reverse**
   ([`D-013`](../decisions.md#d-013)).

4. **Is CP-SAT's core reported as it comes?** No
   ([`D-100`](../decisions.md#d-100)). It is sufficient rather than smallest, and the
   objective inflates it by roughly 80-fold.

5. **Is the deletion loop removed now that it measures as a null?** No. A guarantee and a
   measurement are different things, and the loop is the guarantee.

---

*The ledger: [`README.md`](README.md). Where a model may speak:
[`internals/design.md`](../internals/design.md). The reasoning:
[`decisions.md`](../decisions.md).*
