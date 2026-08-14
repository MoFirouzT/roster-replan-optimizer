"""Differential and brute-force layers: the two readings, compared.

This is the file that makes the independence rule pay. Neither `checker.py` nor
`model.py` imports the other, so agreement here is evidence about `rules.md` rather than
about a shared helper.

Brute force runs in stage **(a)** only -- feasible sets, not objectives. Stage (b)
compares the solver's optimum against the enumerated one and needs a disruption metric
`replan.md` has not shipped; see `PLAN.md`.
"""

from __future__ import annotations

import dataclasses
import itertools
import random

import pytest
from conftest import EVENING, MORNING, NIGHT

from roster_replan.checker import check, is_feasible
from roster_replan.domain import (
    Employee,
    Instance,
    OpenShift,
    RuleParams,
    ShiftType,
    shipped_d2,
)
from roster_replan.model import exclusions, solve, violations

# R-CONSEC-DAYS is compared at (rule, employee) rather than including the day. The two
# readings legitimately differ in granularity: the checker names the first breaching day
# of a run, where the model gates every sliding window that breaches. The substance --
# whether the rule is broken for this person -- is compared; a day-coordinate error in
# this one rule is not caught here, which is the stated cost.
COARSE_RULES = {"R-CONSEC-DAYS"}

# The second stated comparison rule, and the more interesting one. Presolve *removes*
# ineligible (employee, shift) pairs, so an assignment to one is not representable in the
# model at all -- and the consequence is broader than it first looks. The model cannot
# count that body toward coverage, toward the employee's weekly or daily hours, toward a
# consecutive-day streak, or toward a rest gap. Every aggregating rule is affected, not
# just R-COVER.
#
# So on such a roster the only thing the model has an opinion about is *why the pair was
# excluded*. Comparison is split accordingly: representable rosters are compared in full,
# and the rest are compared on the eligibility findings alone. The eligibility
# derivations are then compared exhaustively, pair by pair, in
# `test_presolve_agrees_with_the_checker` -- which is a stronger test than any headcount
# comparison would have been, and is what makes the narrowing safe rather than convenient.
ELIGIBILITY_RULES = {"R-AVAIL", "R-SKILL", "R-FLEXI-ELIG", "R-DIMONA-FLX"}


def representable(roster, instance) -> bool:
    excluded = exclusions(instance)
    return not any(key in excluded for key in roster)


def checker_keys(roster, instance, *, strict: bool = True) -> set[tuple]:
    return _filter(
        {_coarsen(v.key()) for v in check(roster, instance) if not v.soft}, strict
    )


def model_keys(roster, instance, *, strict: bool = True) -> set[tuple]:
    return _filter({_coarsen(g.key()) for g in violations(roster, instance)}, strict)


def _filter(keys: set[tuple], strict: bool) -> set[tuple]:
    if strict:
        return keys
    return {k for k in keys if k[0] in ELIGIBILITY_RULES}


def _coarsen(key: tuple) -> tuple:
    rule, employee = key[0], key[1]
    return (rule, employee) if rule in COARSE_RULES else key


def agree(roster, instance) -> bool:
    strict = representable(roster, instance)
    return checker_keys(roster, instance, strict=strict) == model_keys(
        roster, instance, strict=strict
    )


# --- Fixtures for enumeration ------------------------------------------------------
# Deliberately tiny: brute force is 2**(employees * shift instances).


def micro(**overrides) -> Instance:
    shift_types = (
        ShiftType("M", 7.0, 8.0, 0.5),
        ShiftType("E", 15.0, 8.0, 0.5),
    )
    params = RuleParams(
        min_rest_hours=11.0,
        min_weekly_rest_hours=35.0,
        min_period_hours=3.0,
        max_consecutive_days=2,
    )
    people = tuple(
        Employee(
            name=name,
            contract="salaried",
            skills=frozenset({"bar"}),
            max_hours_this_week=16.0,
            max_daily_hours=8.0,
        )
        for name in ("Ana", "Bram", "Chloe")
    )
    shifts = tuple(
        OpenShift(day=day, shift=shift, required=1) for day in range(3) for shift in (MORNING,)
    )
    base = dict(
        days=3,
        shift_types=shift_types,
        employees=people,
        open_shifts=shifts,
        params=params,
        disruption=shipped_d2(),
    )
    return Instance(**(base | overrides))


def all_rosters(instance: Instance):
    keys = [
        (e, o.day, o.shift)
        for e in range(len(instance.employees))
        for o in instance.open_shifts
    ]
    for mask in itertools.product((0, 1), repeat=len(keys)):
        yield frozenset(k for k, bit in zip(keys, mask) if bit)


# --- Brute force, stage (a) --------------------------------------------------------


def test_brute_force_feasible_sets_agree():
    """Every roster of a micro-instance, both readings, feasibility must coincide."""
    instance = micro()
    rosters = list(all_rosters(instance))
    assert len(rosters) == 2 ** 9

    disagreements = [
        r for r in rosters if is_feasible(r, instance) != (violations(r, instance) == [])
    ]
    assert disagreements == [], f"{len(disagreements)} rosters disagree, e.g. {disagreements[:1]}"


def test_brute_force_violation_sets_agree():
    """Stronger than feasibility: the same rules, at the same coordinates."""
    instance = micro()
    mismatches = [
        (r, checker_keys(r, instance), model_keys(r, instance))
        for r in all_rosters(instance)
        if not agree(r, instance)
    ]
    assert mismatches == [], f"{len(mismatches)} mismatches, first: {mismatches[:1]}"


def bracketing() -> Instance:
    """A variant whose rest gaps straddle `min_rest_hours` rather than clearing it.

    `micro()` opens mornings only, so every gap between consecutive shifts is 24h and no
    roster it can express distinguishes an 11-hour rest threshold from a 9-hour one. The
    differential layer was therefore blind to a wrong threshold in either reading --
    `D-066`'s blind spot, found here by mutation testing after the same lesson had already
    been learned once in the ground-truth set.

    A late shift ending at 21:00 followed by the next morning at 07:00 leaves a 10-hour
    gap: illegal at 11, legal at 9, so the two thresholds now disagree about a roster the
    harness actually enumerates.
    """
    late = ShiftType("L", 13.0, 8.0, 0.5)
    return dataclasses.replace(
        micro(),
        shift_types=(ShiftType("M", 7.0, 8.0, 0.5), late),
        open_shifts=(
            OpenShift(day=0, shift=1, required=1),
            OpenShift(day=1, shift=0, required=1),
            OpenShift(day=1, shift=1, required=1),
            OpenShift(day=2, shift=0, required=1),
        ),
    )


def test_violation_sets_agree_on_gaps_that_straddle_the_threshold():
    """The comparison above, over rosters where the rest threshold actually binds."""
    instance = bracketing()
    gaps = {
        instance.window(1, 0).start - instance.window(0, 1).end,
        instance.window(2, 0).start - instance.window(1, 1).end,
    }
    assert gaps == {10.0}, f"the instance no longer brackets the threshold: {gaps}"

    mismatches = [
        (r, checker_keys(r, instance), model_keys(r, instance))
        for r in all_rosters(instance)
        if not agree(r, instance)
    ]
    assert mismatches == [], f"{len(mismatches)} mismatches, first: {mismatches[:1]}"


def test_presolve_agrees_with_the_checker():
    """The two eligibility derivations, compared pair by pair over every instance
    variant. This is what makes dropping R-COVER on unrepresentable rosters safe: the
    rules presolve enforces are checked directly rather than through a headcount.
    """
    from roster_replan.domain import Interval

    eligibility = {"R-AVAIL", "R-SKILL", "R-FLEXI-ELIG", "R-DIMONA-FLX"}
    base = micro()
    variants = [
        base,
        _with_first(base, absences=(Interval(6.0, 12.0),)),
        _with_first(base, unavailability=(Interval(30.0, 40.0),)),
        _with_first(base, skills=frozenset()),
        _with_first(
            base, contract="flexi", flexi_eligible=frozenset({0}), dimona_ok=frozenset({0, 1})
        ),
    ]

    for instance in variants:
        removed = exclusions(instance)
        for employee in range(len(instance.employees)):
            for open_shift in instance.open_shifts:
                key = (employee, open_shift.day, open_shift.shift)
                from_checker = {
                    v.rule
                    for v in check(frozenset({key}), instance)
                    if v.rule in eligibility and (v.employee, v.day, v.shift) == key
                }
                assert set(removed.get(key, ())) == from_checker, key


def _with_first(instance: Instance, **changes) -> Instance:
    return dataclasses.replace(
        instance,
        employees=(dataclasses.replace(instance.employees[0], **changes),)
        + instance.employees[1:],
    )


def test_brute_force_with_history_agrees():
    """The horizon boundary is where the two readings are most likely to diverge."""
    instance = micro()
    with_history = _with_first(
        instance,
        consecutive_days_worked_before_horizon=2,
        last_shift_end_before_horizon=2.0,
    )
    assert [r for r in all_rosters(with_history) if not agree(r, with_history)] == []


def test_brute_force_with_absences_agrees():
    from roster_replan.domain import Interval

    with_absence = _with_first(micro(), absences=(Interval(6.0, 12.0),))
    assert [r for r in all_rosters(with_absence) if not agree(r, with_absence)] == []


# --- The week rules, over more than one week ---------------------------------------
# `D-111`. Both readings scoped these to the horizon, which is the week only while the
# horizon is one. These are the assertions that the scope is now the week in both, and
# that the two still agree about it -- agreement being the thing that was never in doubt
# and never worth anything while they were wrong together.


def fortnight(**overrides) -> Instance:
    """Two weeks, one employee, one shift a day. Small enough to reason about by hand:
    a morning shift is 07:00-15:00 with a 30-minute break, so 7.5h net."""
    people = (
        Employee(
            name="Ana",
            contract="salaried",
            skills=frozenset({"bar"}),
            max_hours_this_week=38.0,
            max_daily_hours=8.0,
        ),
    )
    base = dict(
        days=14,
        shift_types=(ShiftType("M", 7.0, 8.0, 0.5),),
        employees=people,
        open_shifts=tuple(OpenShift(day=d, shift=0, required=1) for d in range(14)),
        params=RuleParams(
            min_rest_hours=11.0,
            min_weekly_rest_hours=35.0,
            min_period_hours=3.0,
            max_consecutive_days=6,
        ),
        disruption=shipped_d2(),
    )
    return Instance(**(base | overrides))


def test_a_second_week_is_measured_on_its_own():
    """Ana works the six days that close the fortnight. Her longest rest inside that
    second week is 33h -- day 12's shift ends at 15:00 and the horizon ends 33 hours
    later -- against the 35h the rule requires. The first week is untouched and offers a
    rest seven days long, which is what used to satisfy both readings for the whole
    horizon.
    """
    instance = fortnight()
    roster = frozenset({(0, day, 0) for day in range(7, 13)})

    assert ("R-WEEKLY-REST", 0, 7, None) in checker_keys(roster, instance)
    assert ("R-WEEKLY-REST", 0, 0, None) not in checker_keys(roster, instance)
    assert agree(roster, instance)


def test_a_budget_is_a_week_of_hours_in_every_week():
    """Six shifts is 45h against a 38h budget. Spread across the fortnight it is lawful
    in both weeks; concentrated in one it is not, and the horizon-wide sum could not tell
    those two rosters apart.
    """
    instance = fortnight()
    concentrated = frozenset({(0, day, 0) for day in range(0, 6)})
    spread = frozenset({(0, day, 0) for day in (0, 2, 4, 7, 9, 11)})

    assert ("R-MAX-WEEKLY", 0, 0, None) in checker_keys(concentrated, instance)
    assert "R-MAX-WEEKLY" not in {key[0] for key in checker_keys(spread, instance)}
    assert agree(concentrated, instance)
    assert agree(spread, instance)


def test_the_rest_window_is_not_borrowed_across_the_boundary():
    """`D-029`'s conservatism, now at every internal boundary rather than only at the
    horizon's end.

    Ana works every day except day 7, so her one long rest runs from 15:00 on day 6 to
    07:00 on day 8 -- 40 uninterrupted hours, more than the rule asks for. It is split 9h
    either side of the boundary, and both weeks are reported short. A reading that let a
    straddling block count for the week it began in would accept this roster; requiring
    it to lie inside the week refuses it. That is the conservative direction, and the
    same one `D-029` already takes at the horizon's own edge.
    """
    relaxed = RuleParams(
        min_rest_hours=11.0,
        min_weekly_rest_hours=35.0,
        min_period_hours=3.0,
        max_consecutive_days=None,
    )
    instance = _with_first(fortnight(params=relaxed), max_hours_this_week=60.0)
    roster = frozenset({(0, day, 0) for day in range(14) if day != 7})

    short = {key[2] for key in checker_keys(roster, instance) if key[0] == "R-WEEKLY-REST"}
    assert short == {0, 7}
    assert agree(roster, instance)


# --- Differential on a realistic instance ------------------------------------------


def week(**overrides) -> Instance:
    shift_types = (
        ShiftType("M", 7.0, 8.0, 0.5),
        ShiftType("E", 15.0, 8.0, 0.5),
        ShiftType("N", 23.0, 8.0, 0.5),
    )
    params = RuleParams(
        min_rest_hours=11.0,
        min_weekly_rest_hours=35.0,
        min_period_hours=3.0,
        max_consecutive_days=6,
    )
    people = tuple(
        Employee(
            name=name,
            contract="salaried",
            skills=frozenset({"bar"}),
            max_hours_this_week=38.0,
            max_daily_hours=8.0,
        )
        for name in ("Ana", "Bram", "Chloe", "Driss", "Emma", "Finn", "Gita", "Hugo")
    )
    demand = {MORNING: [2] * 7, EVENING: [2, 2, 2, 2, 2, 3, 3], NIGHT: [1] * 7}
    shifts = tuple(
        OpenShift(day=day, shift=shift, required=demand[shift][day])
        for day in range(7)
        for shift in (MORNING, EVENING, NIGHT)
    )
    base = dict(
        days=7,
        shift_types=shift_types,
        employees=people,
        open_shifts=shifts,
        params=params,
        disruption=shipped_d2(),
    )
    return Instance(**(base | overrides))


def perturb(roster: frozenset, instance: Instance, rng: random.Random) -> frozenset:
    """Nearly-feasible rosters. Uniformly random assignments breach coverage instantly
    and never exercise the interesting rules, so perturb a solved one instead."""
    mutable = set(roster)
    for _ in range(rng.randint(1, 4)):
        action = rng.choice(("drop", "add", "move"))
        if action == "drop" and mutable:
            mutable.discard(rng.choice(sorted(mutable)))
        elif action == "add":
            open_shift = rng.choice(instance.open_shifts)
            mutable.add((rng.randrange(len(instance.employees)), open_shift.day, open_shift.shift))
        elif mutable:
            employee, day, shift = rng.choice(sorted(mutable))
            mutable.discard((employee, day, shift))
            mutable.add((rng.randrange(len(instance.employees)), day, shift))
    return frozenset(mutable)


def test_model_solution_has_no_hard_checker_violations():
    """The suite-wide invariant, on a real instance rather than a micro one."""
    instance = week()
    solution = solve(instance)
    assert not isinstance(solution, list), f"expected a solution, got core {solution}"
    assert [v for v in check(solution.roster, instance) if not v.soft] == []


def test_differential_over_perturbed_rosters():
    instance = week()
    solution = solve(instance)
    rng = random.Random(11)

    mismatches = []
    for _ in range(300):
        roster = perturb(solution.roster, instance, rng)
        if checker_keys(roster, instance) != model_keys(roster, instance):
            mismatches.append(
                (
                    sorted(roster),
                    checker_keys(roster, instance) ^ model_keys(roster, instance),
                )
            )
    assert mismatches == [], f"{len(mismatches)} mismatches, first symmetric difference: {mismatches[0][1]}"


def test_differential_is_actually_exercising_rules():
    """A harness that only ever sees feasible rosters proves nothing. Assert the
    perturbations reach a spread of rules."""
    instance = week()
    solution = solve(instance)
    rng = random.Random(11)

    seen = set()
    for _ in range(300):
        roster = perturb(solution.roster, instance, rng)
        seen |= {key[0] for key in checker_keys(roster, instance)}
    assert {"R-COVER", "R-REST-GAP"} <= seen, seen


# --- Infeasibility reporting -------------------------------------------------------


def test_impossible_coverage_returns_a_shortfall_not_an_infeasibility():
    """The soft floor's whole point, and it changes where infeasibility can come from.

    One employee cannot hold both a morning and an evening on the same day under the
    rest gap. With coverage hard that is `INFEASIBLE`; with the floor soft the service
    answers "one short on the evening, here is what it costs", which is the answer a
    planner can act on.
    """
    instance = micro(
        employees=(
            Employee(
                name="Solo",
                contract="salaried",
                skills=frozenset({"bar"}),
                max_hours_this_week=40.0,
                max_daily_hours=8.0,
            ),
        ),
        open_shifts=(
            OpenShift(day=0, shift=MORNING, required=1),
            OpenShift(day=0, shift=EVENING, required=1),
        ),
    )
    solution = solve(instance)
    assert not isinstance(solution, list), "a coverage shortfall must not be infeasible"
    assert sum(solution.shortfall.values()) == 1
    assert [v for v in check(solution.roster, instance) if not v.soft] == []


def test_structurally_impossible_parameter_returns_a_core():
    """A rest window wider than the horizon cannot be placed at all. Reported through
    the gate rather than as a bare INFEASIBLE, which is what the literals buy."""
    instance = micro()
    impossible = dataclasses.replace(
        instance,
        params=dataclasses.replace(instance.params, min_weekly_rest_hours=200.0),
    )
    core = solve(impossible)
    assert isinstance(core, list) and core, "expected an infeasibility core"
    # `in`, not `==`: CP-SAT returns a *sufficient* set of assumptions, not a guaranteed
    # minimal one. Genuine minimality needs iterative deletion, which is T4's job.
    assert "R-WEEKLY-REST" in {gate.rule for gate in core}


def test_pinned_illegal_past_is_reported_as_such():
    """An incumbent that already breaks a rule makes the solve infeasible with the pin
    in the core -- "the past itself is illegal", distinct from "no legal future exists".
    """
    instance = week()
    person = dataclasses.replace(instance.employees[0], max_daily_hours=8.0)
    instance = dataclasses.replace(instance, employees=(person,) + instance.employees[1:])

    # Ana holds both a morning and an evening on day 0, which breaches her daily maximum
    # and the rest gap, and day 0 is already past.
    illegal = frozenset({(0, 0, MORNING), (0, 0, EVENING)})
    replan = dataclasses.replace(instance, now=30.0, incumbent=illegal)
    core = solve(replan)
    assert isinstance(core, list) and core
    assert "R-PIN-PAST" in {gate.rule for gate in core}


def test_replan_absorbs_an_absence():
    """The headline scenario end to end: publish, injure, repair, verify."""
    from roster_replan.domain import Interval

    instance = week()
    published = solve(instance)
    assert not isinstance(published, list)

    sick = next(e for (e, d, s) in published.roster if d == 5)
    injured = dataclasses.replace(
        instance.employees[sick], absences=(Interval(5 * 24.0, 6 * 24.0),)
    )
    employees = list(instance.employees)
    employees[sick] = injured
    replan = dataclasses.replace(
        instance, employees=tuple(employees), now=0.0, incumbent=published.roster
    )

    repaired = solve(replan)
    assert not isinstance(repaired, list), f"replan infeasible: {repaired}"
    assert [v for v in check(repaired.roster, replan) if not v.soft] == []
    changed = published.roster ^ repaired.roster
    assert changed, "a replan around an absence must change something"


# --- Determinism -------------------------------------------------------------------


@pytest.mark.parametrize("seed", [1, 7])
def test_same_seed_gives_the_same_roster(seed):
    instance = week()
    first = solve(instance, seed=seed)
    second = solve(instance, seed=seed)
    assert first.roster == second.roster
    assert first.objective == second.objective
