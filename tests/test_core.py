"""Minimal infeasibility cores, closing the debt `D-048` opened at T1.

Infeasibility has to be constructed here. `D-047` collapsed the surface — with a soft
coverage floor the empty roster satisfies every hard rule — so none of the 72 committed cases
is infeasible and every fixture below is built on the one shape that remains: **an incumbent
whose past already breaks a rule**, which `R-PIN-PAST` then forces the solver to keep.

Two properties are asserted, and they are different claims:

**Still a core.** The reduced set must genuinely explain the infeasibility — enforcing only
those gates must still be unsatisfiable. A "minimisation" that reduced to something
satisfiable would be smaller and meaningless.

**Every element necessary.** Dropping any one gate must make the model satisfiable. This is
verified here independently of the loop that produced it, because a minimisation checking its
own work is checking its own bug.

Minimal is not *smallest*: another deletion order can reach a different minimal core, and
finding the smallest is a harder problem than an explanation needs.
"""

from __future__ import annotations

import dataclasses

import pytest
from ortools.sat.python import cp_model

from benchmarks import studies, suite
from roster_replan.core import minimal_core
from roster_replan.domain import Interval
from roster_replan.model import build, solve


def _pin(instance, incumbent, now=72.0):
    return dataclasses.replace(
        instance, now=now, published_through=7 * 24.0, incumbent=frozenset(incumbent)
    )


def _swap(base, index, **changes):
    people = list(base.employees)
    people[index] = dataclasses.replace(people[index], **changes)
    return dataclasses.replace(base, employees=tuple(people))


@pytest.fixture(scope="module")
def base():
    return studies.identical_workforce(5, required=1)


@pytest.fixture(scope="module")
def infeasible(base):
    """The narrow surface `D-047` leaves: a past that is already illegal."""
    window = base.window(0, 0)
    return {
        "absent-but-pinned": _pin(
            _swap(base, 0, absences=(Interval(window.start, window.end),)), {(0, 0, 0)}
        ),
        "over-weekly-hours": _pin(_swap(base, 0, max_hours_this_week=7.0), {(0, 0, 0)}),
        "over-daily-hours": _pin(_swap(base, 0, max_daily_hours=4.0), {(0, 0, 0)}),
        "breaks-rest-gap": _pin(
            dataclasses.replace(
                base, params=dataclasses.replace(base.params, min_rest_hours=20.0)
            ),
            {(0, 0, 0), (0, 1, 0)},
        ),
    }


# --- The fixtures have to be infeasible ---------------------------------------------


@pytest.mark.parametrize("name", ["absent-but-pinned", "over-weekly-hours", "breaks-rest-gap"])
def test_the_fixture_is_actually_infeasible(name, infeasible):
    """Otherwise every test below passes by describing nothing."""
    assert isinstance(solve(infeasible[name], time_limit=30.0), list)


def test_a_satisfiable_instance_returns_none():
    """`None`, not an empty core: *there is no conflict* and *the conflict is empty* are
    different answers, and conflating them is the ambiguity `D-094` had to remove elsewhere."""
    assert minimal_core(suite.build("headline/0").instance) is None


# --- The two properties -------------------------------------------------------------


@pytest.mark.parametrize(
    "name", ["absent-but-pinned", "over-weekly-hours", "over-daily-hours", "breaks-rest-gap"]
)
def test_the_minimal_core_is_still_a_core(name, infeasible):
    instance = infeasible[name]
    reduction = minimal_core(instance)

    assert reduction is not None
    assert not _satisfiable(instance, reduction.minimal), (
        "the reduced set no longer explains the infeasibility, so it is not a core"
    )


@pytest.mark.parametrize(
    "name", ["absent-but-pinned", "over-weekly-hours", "over-daily-hours", "breaks-rest-gap"]
)
def test_every_gate_in_the_minimal_core_is_necessary(name, infeasible):
    """Verified independently of the loop that produced it."""
    instance = infeasible[name]
    reduction = minimal_core(instance)
    assert reduction is not None

    for gate in reduction.minimal:
        without = tuple(g for g in reduction.minimal if g != gate)
        assert _satisfiable(instance, without), (
            f"{gate} can be dropped and the model stays infeasible, so the core is not "
            f"minimal"
        )


@pytest.mark.parametrize("name", ["absent-but-pinned", "breaks-rest-gap"])
def test_the_minimal_core_names_the_rules_a_planner_needs(name, infeasible):
    """`R-PIN-PAST` plus whatever the past breaks. Anything else is noise in an
    explanation."""
    reduction = minimal_core(infeasible[name])
    assert "R-PIN-PAST" in reduction.rules
    assert len(reduction.rules) == 2, reduction.rules


@pytest.mark.parametrize("name", ["absent-but-pinned", "over-weekly-hours"])
def test_the_reduction_is_reproducible(name, infeasible):
    """Deletion order is fixed, so the same instance yields the same core — which a
    planner-facing explanation needs as much as a test does."""
    first = minimal_core(infeasible[name])
    second = minimal_core(infeasible[name])
    assert first.minimal == second.minimal


# --- The measured finding behind `D-100` --------------------------------------------


@pytest.mark.parametrize(
    "name", ["absent-but-pinned", "over-weekly-hours", "over-daily-hours", "breaks-rest-gap"]
)
def test_the_objective_is_what_inflates_the_core(name, infeasible):
    """The finding that reframed `D-048`.

    `solve` sets the disruption objective before asking, and the core it gets back is two
    orders of magnitude larger than the same question asked as pure feasibility. The
    deferred work was aimed at the loop; the lever was the objective.
    """
    instance = infeasible[name]

    with_objective = solve(instance, time_limit=30.0)
    assert isinstance(with_objective, list)

    reduction = minimal_core(instance)
    assert len(reduction.sufficient) * 10 < len(with_objective), (
        f"{name}: feasibility core {len(reduction.sufficient)} against objective core "
        f"{len(with_objective)} — the gap this test documents has closed"
    )


@pytest.mark.parametrize(
    "name", ["absent-but-pinned", "over-weekly-hours", "over-daily-hours", "breaks-rest-gap"]
)
def test_deletion_finds_little_left_to_delete(name, infeasible):
    """The null half of `D-100`, asserted so it cannot quietly stop being true.

    Once the objective is gone the core is already minimal on every constructed case, so the
    deletion loop drops nothing. It is kept because it *guarantees* minimality rather than
    observing it — and it costs 3 to 4 solves only because the core it works on is small.
    """
    reduction = minimal_core(infeasible[name])
    assert reduction.dropped == 0
    assert reduction.solves <= len(reduction.sufficient) + 2


def _satisfiable(instance, gates) -> bool:
    """Solve enforcing only these gates, by rebuilding and matching on gate descriptors."""
    built = build(instance)
    wanted = set(gates)
    assumptions = [
        literal for literal in built.literals if built.gates[literal.index] in wanted
    ]

    built.model.clear_assumptions()
    built.model.add_assumptions(assumptions)

    solver = cp_model.CpSolver()
    solver.parameters.num_workers = 1
    solver.parameters.max_time_in_seconds = 30.0
    return solver.solve(built.model) in (cp_model.OPTIMAL, cp_model.FEASIBLE)
