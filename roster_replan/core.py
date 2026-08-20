"""Reducing a sufficient infeasibility core to a minimal one.

`D-048` deferred this with a precise reason: CP-SAT's
`sufficient_assumptions_for_infeasibility` returns a set that *explains* the infeasibility
with no guarantee it is the smallest, and the reduction is a loop of solves layered on top
rather than a change to the model. This is that loop.

The gap it closes is not theoretical. On the one construction that reliably produces
infeasibility — an incumbent whose past already breaks a rule — CP-SAT returns **123 gates
naming eight different rules**, where the actual conflict is two: the person is absent, and
`R-PIN-PAST` forces the roster to keep them there anyway. A planner-facing explanation built
on the sufficient core would list eight rules, seven of them irrelevant, and the reader would
have no way to tell which.

## Deletion-based minimisation, and why it is exact

The model's hard constraints are conditioned on assumption literals (`D-002`), so a solve
takes a *set* of assumptions and constraints outside that set are simply not enforced. That
turns minimisation into a membership question with a decision procedure:

    for each gate g in the candidate core C:
        if the model is still infeasible under C \\ {g}:
            g was not necessary — drop it

What remains is minimal in the standard sense: **every element is necessary**, so removing
any one makes the model satisfiable. That is not the same as *smallest* — a different search
order can reach a different minimal core, and finding the smallest is a harder problem than
the explanation needs. `minimal_core` returns one minimal core and says so rather than
implying uniqueness.

Cost is one solve per candidate gate, which is why this belongs here and not in `solve`.
Every solve in the loop is on a model that is *usually* infeasible, and infeasibility under
assumptions is the cheap direction for CP-SAT.

## Infeasibility is rare, and that is the point of ordering this last

`D-047` collapsed the infeasibility surface: with a soft coverage floor the empty roster
satisfies every hard rule, so a cold solve is essentially never infeasible and **none of the
72 committed cases is**. This code runs on a case that has to be constructed. It is still
worth having, because when it does fire the alternative is handing a planner 123 rule
instances.
"""

from __future__ import annotations

from dataclasses import dataclass

from ortools.sat.python import cp_model

from .domain import Instance
from .model import Built, Gate, build


@dataclass(frozen=True, slots=True)
class Reduction:
    """A minimal core, and what it was reduced from."""

    minimal: tuple[Gate, ...]
    sufficient: tuple[Gate, ...]
    solves: int

    @property
    def dropped(self) -> int:
        return len(self.sufficient) - len(self.minimal)

    @property
    def rules(self) -> tuple[str, ...]:
        """The distinct rules the minimal core names, in registry-ID order."""
        return tuple(sorted({gate.rule for gate in self.minimal}))


def minimal_core(
    instance: Instance, *, seed: int = 7, time_limit: float = 30.0
) -> Reduction | None:
    """One minimal core, or `None` when the instance is satisfiable.

    `None` rather than an empty tuple: an empty core is a meaningful answer in some
    formulations, and conflating *there is no conflict* with *the conflict is empty* is the
    kind of ambiguity `D-094` had to be written to remove elsewhere.
    """
    built = build(instance)
    solver = _solver(seed, time_limit)

    if _satisfiable(built, built.literals, solver):
        return None

    sufficient = [
        built.literals[_index(built, literal)]
        for literal in _core_literals(built, solver)
    ]
    solves = 1

    # Deletion order is fixed rather than incidental. Any order yields *a* minimal core, but
    # a stable one makes the result reproducible, which a planner-facing explanation needs
    # as much as a test does.
    candidate = sorted(sufficient, key=lambda lit: lit.index)
    necessary: list = []

    while candidate:
        gate = candidate.pop()
        solves += 1
        if _satisfiable(built, necessary + candidate, solver):
            # Without this gate the model can be satisfied, so it is doing real work.
            necessary.append(gate)

    return Reduction(
        minimal=tuple(sorted(_describe(built, necessary), key=_order)),
        sufficient=tuple(sorted(_describe(built, sufficient), key=_order)),
        solves=solves,
    )


def _solver(seed: int, time_limit: float) -> cp_model.CpSolver:
    solver = cp_model.CpSolver()
    solver.parameters.num_workers = 1
    solver.parameters.random_seed = seed
    solver.parameters.max_time_in_seconds = time_limit
    return solver


def _satisfiable(built: Built, assumptions: list, solver: cp_model.CpSolver) -> bool:
    """Is the model satisfiable when only these gates are enforced?

    No objective is set. Minimisation asks a feasibility question, and leaving the objective
    on would spend the budget proving optimality of an answer nobody reads.
    """
    built.model.clear_assumptions()
    built.model.add_assumptions(assumptions)
    status = solver.solve(built.model)
    return status in (cp_model.OPTIMAL, cp_model.FEASIBLE)


def _core_literals(built: Built, solver: cp_model.CpSolver) -> list:
    return [
        index
        for index in solver.sufficient_assumptions_for_infeasibility()
        if index in built.gates
    ]


def _index(built: Built, literal_index: int) -> int:
    for position, literal in enumerate(built.literals):
        if literal.index == literal_index:
            return position
    raise KeyError(f"assumption {literal_index} is not one of the model's gates")


def _describe(built: Built, literals: list) -> list[Gate]:
    return [built.gates[literal.index] for literal in literals]


def _order(gate: Gate) -> tuple:
    return (
        gate.rule,
        -1 if gate.employee is None else gate.employee,
        -1 if gate.day is None else gate.day,
        -1 if gate.shift is None else gate.shift,
    )
