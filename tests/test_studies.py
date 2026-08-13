"""The level-1 study layer: the encodings must mean the same thing before timing them.

A study that compares two encodings is only evidence if they encode the same problem. Every
way this fails produces a *faster* variant, which is the direction that gets written up:

- an alternative encoding that quietly drops a constraint is fast and wrong;
- a symmetry-breaking constraint that is not a symmetry is fast and cuts off optima;
- an `only_enforce_if` the API accepts but does not honour would silently harden a rule
  that is supposed to be relaxable, and nothing in a timing would show it.

So this file asserts equivalence, not performance. Timings belong in `docs/studies/` where
they can be read with their caveats; a test that asserts a speed is a test that fails on a
busy machine.
"""

from __future__ import annotations

import dataclasses

import pytest
from ortools.sat.python import cp_model

from benchmarks import patterns, studies, suite
from roster_replan.checker import check
from roster_replan.model import _orbits, build, solve

CASES = ["headline/0", "tight/0", "small/0", "thin-availability/0", "multi-absence/0"]

VARIANTS = {
    "presolve-off": dict(presolve=False),
    "symmetry": dict(symmetry=True),
    "automaton": dict(sequence="automaton"),
}


@pytest.fixture(scope="module")
def scenarios():
    return {case: suite.build(case) for case in CASES}


@pytest.mark.parametrize("case", CASES)
@pytest.mark.parametrize("variant", sorted(VARIANTS))
def test_every_encoding_reaches_the_same_optimum(case, variant, scenarios):
    """The one thing that makes a timing meaningful."""
    instance = scenarios[case].instance
    reference = solve(instance)
    other = _solve_with(instance, **VARIANTS[variant])
    assert other == reference.objective, (
        f"{variant} on {case} reached {other}, not {reference.objective} -- that is a "
        f"broken encoding, and the broken one is usually the fast one"
    )


@pytest.mark.parametrize("case", CASES)
def test_presolve_off_is_larger_and_still_correct(case, scenarios):
    """Turning presolve off must add variables and change nothing else."""
    instance = scenarios[case].instance
    on = build(instance, presolve=True)
    off = build(instance, presolve=False)
    assert len(off.x) > len(on.x), "presolve removed nothing at all on this case"
    assert set(on.x) <= set(off.x), "presolve kept a pair the unpresolved model lacks"


def test_an_automaton_honours_its_enforcement_literal():
    """The API accepting `only_enforce_if` is not evidence that CP-SAT honours it.

    Gating `R-CONSEC-DAYS` as an automaton depends entirely on this, and a silently ignored
    enforcement literal would make the rule unconditional -- which no timing and no
    objective comparison would reveal, because the rule would simply always hold.
    """
    for gate_value, expected in ((1, "INFEASIBLE"), (0, "OPTIMAL")):
        model = cp_model.CpModel()
        days = [model.new_bool_var(f"d{i}") for i in range(2)]
        literal = model.new_bool_var("gate")
        # At most one consecutive working day.
        model.add_automaton(days, 0, [0, 1], [(0, 0, 0), (0, 1, 1), (1, 0, 0)]).only_enforce_if(
            literal
        )
        for day in days:
            model.add(day == 1)
        model.add(literal == gate_value)

        solver = cp_model.CpSolver()
        solver.parameters.num_workers = 1
        assert solver.status_name(solver.solve(model)) == expected


@pytest.mark.parametrize("case", CASES)
def test_orbits_never_group_employees_the_incumbent_separates(case, scenarios):
    """Two employees are interchangeable only if their published rows match too.

    Grouping on contract and skills alone is the natural mistake, and it would make the
    lexicographic constraint cut off optima rather than duplicates -- a wrong answer that
    arrives faster.
    """
    scenario = scenarios[case]
    incumbent = scenario.instance.incumbent or frozenset()
    for orbit in _orbits(scenario.instance):
        rows = {
            frozenset((d, s) for (e, d, s) in incumbent if e == member) for member in orbit
        }
        assert len(rows) == 1, f"{case}: orbit {orbit} groups different published rows"


def test_both_sequence_encodings_agree_about_a_streak_from_before_the_horizon():
    """The generator sets `consecutive_days_worked_before_horizon` to 0 on every case, so
    nothing in the committed set exercises the clamp -- and the mutation harness found that
    by surviving a mutant that deleted it.

    The two encodings carry the prior streak differently: the window encoding folds it into
    an allowance, the automaton into a start state. They have to agree, and they can only be
    shown to agree on an instance that has one.
    """
    base = studies.identical_workforce(4, required=1)
    limit = base.params.max_consecutive_days

    for prior in range(limit + 2):
        instance = dataclasses.replace(
            base,
            employees=tuple(
                dataclasses.replace(person, consecutive_days_worked_before_horizon=prior)
                for person in base.employees
            ),
        )
        windows = _solve_with(instance)
        automaton = _solve_with(instance, sequence="automaton")
        assert windows == automaton, (
            f"a prior streak of {prior} is priced differently by the two encodings: "
            f"{windows} against {automaton}"
        )


def test_orbits_separate_employees_who_differ_only_in_their_published_row():
    """Identical people, different published shifts, therefore not interchangeable.

    The committed set almost never contains two employees identical in everything else, so
    a version of `_orbits` that ignored the incumbent entirely would pass every test over
    it while being wrong. This constructs the case that tells them apart.
    """
    base = studies.identical_workforce(4, required=1)
    assert len(_orbits(base)) == 1, "the control instance should be one orbit of four"

    # Same four identical people, but two of them are published on different days.
    published = dataclasses.replace(
        base,
        now=0.0,
        published_through=7 * 24.0,
        incumbent=frozenset({(0, 0, 0), (1, 1, 0)}),
    )
    for orbit in _orbits(published):
        assert 0 not in orbit or 1 not in orbit, (
            "employees 0 and 1 hold different published shifts and are not interchangeable"
        )
    grouped = {member for orbit in _orbits(published) for member in orbit}
    assert grouped == {2, 3}, (
        f"only the two employees with empty published rows are interchangeable, got {grouped}"
    )


def test_the_symmetric_family_actually_contains_symmetry():
    """The control for the symmetry study. If this instance had no orbits, the study's
    second half would be measuring the same null as its first and would say so wrongly."""
    for size in (8, 12, 16):
        instance = studies.identical_workforce(size)
        assert sum(len(o) for o in _orbits(instance)) == size


# --- The pattern formulation --------------------------------------------------------


@pytest.mark.parametrize("case", ["small/0", "headline/0"])
def test_patterns_reach_the_assignment_optimum(case, scenarios):
    instance = scenarios[case].instance
    roster, objective, _ = patterns.solve_patterns(instance)
    reference = solve(instance)

    assert objective == reference.objective
    assert not [v for v in check(roster, instance) if not v.soft]


@pytest.mark.parametrize("case", ["small/0", "headline/0"])
def test_every_enumerated_pattern_is_legal_and_the_legal_ones_are_enumerated(case, scenarios):
    """Both directions. Enumerating an illegal pattern lets the model choose it; missing a
    legal one silently removes an option and can only make the answer worse -- which looks
    like a correct solve of a slightly different problem."""
    scenario = scenarios[case]
    instance = scenario.instance

    for employee in range(len(instance.employees)):
        catalogue = patterns.enumerate_patterns(instance, employee)
        assert catalogue, f"employee {employee} has no pattern at all on {case}"

        for pattern in catalogue:
            roster = frozenset((employee, day, shift) for day, shift in pattern)
            hard = [v for v in check(roster, instance) if not v.soft and v.employee == employee]
            assert hard == [], f"{case}: enumerated an illegal pattern for {employee}: {hard}"

    # The incumbent's own rows are legal patterns wherever the event did not break them,
    # so they must appear. This is the "missing a legal one" direction, on the one family
    # of patterns we know independently must be there.
    for employee in range(len(instance.employees)):
        row = frozenset((d, s) for (e, d, s) in scenario.incumbent if e == employee)
        roster = frozenset((employee, day, shift) for day, shift in row)
        if [v for v in check(roster, instance) if not v.soft and v.employee == employee]:
            continue  # the event made this row illegal, so it is correctly absent
        assert row in patterns.enumerate_patterns(instance, employee), (
            f"{case}: employee {employee}'s published row is legal but was not enumerated"
        )


def _solve_with(instance, **flags) -> int:
    from roster_replan.disruption import objective_terms

    built = build(instance, **flags)
    built.model.minimize(
        sum(
            objective_terms(
                built.model, instance, built.x, built.shortfall, built.mix_shortfall
            )
        )
    )
    built.model.clear_assumptions()
    built.model.add_assumptions(built.literals)

    solver = cp_model.CpSolver()
    solver.parameters.num_workers = 1
    solver.parameters.random_seed = 7
    status = solver.solve(built.model)
    assert status == cp_model.OPTIMAL, solver.status_name(status)
    return round(solver.objective_value)
