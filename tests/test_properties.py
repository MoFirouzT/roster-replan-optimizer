"""Property and metamorphic layers.

These test relations that must hold across *many* inputs rather than facts about one, so
they catch a different class of bug from the differential harness: not "the two readings
disagree" but "the solver's answer depends on something it should not".

Every relation here is stated as an implication with its preconditions, because two of
them do not hold unconditionally and pretending otherwise would produce failures that are
not defects.
"""

from __future__ import annotations

import dataclasses

import pytest
from conftest import EVENING, MORNING, NIGHT, solved
from test_differential import micro, week

from roster_replan.domain import (
    Employee,
    Instance,
    Interval,
    OpenShift,
    RuleParams,
    ShiftType,
    shipped_d2,
)
from roster_replan.model import solve
from roster_replan.scoring import disruption_of, score

METRICS = ["D0", "D1", "D2", "D3", "D4"]


def replan_of(instance, incumbent, **overrides):
    overrides.setdefault("published_through", 7 * 24.0)
    overrides.setdefault("now", 0.0)
    return dataclasses.replace(instance, incumbent=incumbent, **overrides)


def injured(instance, day=5):
    """Make a replan that has real work to do: someone on `day` falls sick."""
    published = solved(instance)
    sick = next(e for (e, d, s) in sorted(published.roster) if d == day)
    employees = list(instance.employees)
    employees[sick] = dataclasses.replace(
        employees[sick], absences=(Interval(day * 24.0, (day + 1) * 24.0),)
    )
    hurt = dataclasses.replace(instance, employees=tuple(employees))
    return replan_of(hurt, published.roster), published.roster


# --- Idempotence --------------------------------------------------------------------


@pytest.mark.parametrize("metric", METRICS)
def test_replanning_an_unchanged_instance_changes_nothing(metric):
    """Nothing has gone wrong, so nothing should move.

    Zero disruption is the objective's floor and is reachable only by returning the
    incumbent exactly, so this pins the roster and not merely its cost.
    """
    instance = week()
    published = solved(instance)
    replan = replan_of(instance, published.roster, disruption=shipped_d2(metric=metric))

    again = solved(replan)
    assert again.roster == published.roster
    assert disruption_of(again.roster, replan) == 0


def test_idempotence_is_a_fixed_point_not_just_one_step():
    """Feeding a replan's output back in must also change nothing. A metric that
    rewarded churn would pass the single-step test and fail here."""
    instance = week()
    roster = solved(instance).roster
    for _ in range(3):
        replan = replan_of(instance, roster)
        result = solved(replan)
        assert result.roster == roster
        roster = result.roster


# --- Determinism --------------------------------------------------------------------


@pytest.mark.parametrize("seed", [1, 7, 4242])
def test_repeated_solves_are_identical(seed):
    instance = week()
    first, second = solve(instance, seed=seed), solve(instance, seed=seed)
    assert first.roster == second.roster
    assert first.objective == second.objective
    assert first.shortfall == second.shortfall


def test_different_seeds_reach_the_same_optimum():
    """Seeds may reorder search but must not change the optimal *value*. A difference
    here means the objective is being truncated, not explored."""
    instance = week()
    objectives = {solve(instance, seed=seed).objective for seed in (1, 7, 99, 4242)}
    assert len(objectives) == 1, objectives


def test_determinism_depends_on_single_threading():
    """Documenting a real limitation rather than asserting a false guarantee: CP-SAT is
    deterministic per seed at one worker, and parallel search is not reproducible. The
    solver defaults to one worker for exactly this reason."""
    import inspect

    signature = inspect.signature(solve)
    assert signature.parameters["workers"].default == 1


# --- Monotonicity under relaxation --------------------------------------------------
# Relaxing a *rule* expands the feasible set without touching the objective function, so
# the optimum can only improve or hold. Relaxing coverage is deliberately excluded: it
# changes the objective itself through the shortfall term, so it is not a relaxation in
# this sense and comparing across it would be meaningless.


def relaxations(instance: Instance):
    params = instance.params
    people = instance.employees

    def with_params(**changes):
        return dataclasses.replace(instance, params=dataclasses.replace(params, **changes))

    def with_everyone(**changes):
        return dataclasses.replace(
            instance,
            employees=tuple(dataclasses.replace(p, **changes) for p in people),
        )

    return {
        "shorter rest gap": with_params(min_rest_hours=params.min_rest_hours - 4),
        "less weekly rest": with_params(min_weekly_rest_hours=24.0),
        "consecutive days off": with_params(max_consecutive_days=None),
        "more consecutive days": with_params(max_consecutive_days=7),
        "bigger weekly budget": with_everyone(max_hours_this_week=48.0),
        "bigger daily maximum": with_everyone(max_daily_hours=12.0),
        "absences lifted": with_everyone(absences=(), unavailability=()),
    }


@pytest.mark.parametrize("metric", METRICS)
def test_relaxation_never_worsens_the_optimum(metric):
    base, _ = injured(week())
    base = dataclasses.replace(base, disruption=shipped_d2(metric=metric))
    baseline = solved(base).objective

    for name, relaxed in relaxations(base).items():
        assert solved(relaxed).objective <= baseline, f"{name} made the optimum worse"


def test_at_least_one_relaxation_actually_helps():
    """A monotonicity suite where every relaxation is inert passes vacuously. At least
    one must move the objective, or the test is measuring nothing."""
    base, _ = injured(week())
    baseline = solved(base).objective
    improved = [
        name for name, relaxed in relaxations(base).items() if solved(relaxed).objective < baseline
    ]
    assert improved, "no relaxation changed the optimum, so monotonicity is untested here"


# --- Past shifts are immutable ------------------------------------------------------


@pytest.mark.parametrize("now", [30.0, 80.0, 130.0])
def test_a_replan_never_touches_the_past(now):
    instance = week()
    published = solved(instance)
    replan = replan_of(instance, published.roster, now=now)
    result = solved(replan)

    past = [
        (e, o.day, o.shift)
        for e in range(len(instance.employees))
        for o in instance.open_shifts
        if replan.is_past(o.day, o.shift)
    ]
    assert past, "this `now` leaves nothing in the past, so the test proves nothing"
    for key in past:
        assert (key in result.roster) == (key in published.roster), key


def test_the_past_is_immutable_even_when_it_would_help():
    """The interesting case: an absence lands on a shift already under way. The rule must
    hold the assignment anyway -- three hours already worked cannot be un-worked."""
    instance = week()
    published = solved(instance)

    now = 30.0  # part-way through day 1
    victim = next(
        (e, d, s)
        for (e, d, s) in sorted(published.roster)
        if instance.window(d, s).start < now
    )
    employee, day, shift = victim
    employees = list(instance.employees)
    employees[employee] = dataclasses.replace(
        employees[employee], absences=(instance.window(day, shift),)
    )

    replan = replan_of(
        dataclasses.replace(instance, employees=tuple(employees)),
        published.roster,
        now=now,
    )
    result = solve(replan)
    # Pinned equality against an absence is a genuine conflict, and the gate names it.
    if isinstance(result, list):
        assert "R-PIN-PAST" in {gate.rule for gate in result}
    else:
        assert victim in result.roster, "a started shift was dropped"


# --- Metamorphic: employee relabelling ----------------------------------------------


def relabel(instance: Instance, permutation: dict[int, int]) -> Instance:
    """Move every employee to a new index, carrying their data and the incumbent with
    them. A pure renaming: nothing about the problem changes."""
    employees = list(instance.employees)
    for old, new in permutation.items():
        employees[new] = instance.employees[old]

    incumbent = instance.incumbent
    if incumbent is not None:
        incumbent = frozenset((permutation[e], d, s) for (e, d, s) in incumbent)

    return dataclasses.replace(
        instance, employees=tuple(employees), incumbent=incumbent
    )


PERMUTATIONS = [
    {0: 1, 1: 0, 2: 2, 3: 3, 4: 4, 5: 5, 6: 6, 7: 7},
    {0: 7, 1: 6, 2: 5, 3: 4, 4: 3, 5: 2, 6: 1, 7: 0},
    {0: 3, 1: 0, 2: 1, 3: 2, 4: 5, 5: 6, 6: 7, 7: 4},
]


@pytest.mark.parametrize("metric", METRICS)
@pytest.mark.parametrize("permutation", PERMUTATIONS, ids=["swap", "reverse", "rotate"])
def test_relabelling_employees_leaves_the_objective_invariant(metric, permutation):
    """The objective, not the roster: interchangeable employees create ties, so the
    solver may legitimately return a different-but-equal roster."""
    base, _ = injured(week())
    base = dataclasses.replace(base, disruption=shipped_d2(metric=metric))
    assert solved(relabel(base, permutation)).objective == solved(base).objective


SMALL_PERMUTATIONS = [{0: 1, 1: 0, 2: 2}, {0: 2, 1: 0, 2: 1}, {0: 1, 1: 2, 2: 0}]


@pytest.mark.parametrize("metric", ["D3", "D4"])
@pytest.mark.parametrize("permutation", SMALL_PERMUTATIONS, ids=["swap", "rotate", "cycle"])
def test_relabelling_is_invariant_where_moves_actually_occur(metric, permutation):
    """Found by mutation testing: every instance above resolves its disruption with
    cancellations and call-ins, so `moves` was always zero and D3's move term was never
    exercised. Making the move weight depend on the employee index passed the whole suite.

    This uses the instance built to produce a genuine move, and guards against the term
    going quiet again.
    """
    from test_replan import move_or_call_in

    base = dataclasses.replace(move_or_call_in(), disruption=shipped_d2(metric=metric))
    chosen = solved(base)

    paired = _moves_in(chosen.roster, base)
    assert paired > 0, "no move occurred, so the move term is still untested"

    relabelled = relabel(base, permutation)
    assert solved(relabelled).objective == chosen.objective


def _moves_in(roster, instance) -> int:
    """Drops paired with adds on the same (employee, day) -- what D3 calls a move."""
    incumbent = instance.incumbent or frozenset()
    drops: dict[tuple[int, int], int] = {}
    adds: dict[tuple[int, int], int] = {}
    for employee in range(len(instance.employees)):
        for open_shift in instance.open_shifts:
            key = (employee, open_shift.day, open_shift.shift)
            before, after = key in incumbent, key in roster
            if before and not after:
                drops[employee, open_shift.day] = drops.get((employee, open_shift.day), 0) + 1
            elif after and not before:
                adds[employee, open_shift.day] = adds.get((employee, open_shift.day), 0) + 1
    return sum(min(drops.get(k, 0), adds.get(k, 0)) for k in set(drops) | set(adds))


def test_relabelling_maps_the_score_of_a_specific_roster_exactly():
    """Stronger than the objective invariance and independent of the solver: the same
    roster, relabelled, must score identically under the independent scorer."""
    base, published = injured(week())
    for permutation in PERMUTATIONS:
        moved = frozenset((permutation[e], d, s) for (e, d, s) in published)
        assert score(moved, relabel(base, permutation)) == score(published, base)


# --- Metamorphic: day permutation ---------------------------------------------------


def decoupled_week() -> Instance:
    """A cold instance whose days do not interact, which day permutation needs.

    `validation.md` claimed day permutation "stays structure-consistent" without
    qualification, and that is too strong. Permuting days is **not** an invariance in
    general, because three things couple days together:

      - `R-REST-GAP` and `R-WEEKLY-REST` constrain adjacent and consecutive days;
      - `R-CONSEC-DAYS` counts runs, and {0,1,2} is a run of three where {0,2,4} is three
        runs of one;
      - D1 and D2 read publication state and notice from absolute start times.

    So the relation holds under stated preconditions: one shift type per day with more
    than `min_rest_hours` between consecutive days, no consecutive-day limit, weekly rest
    loose enough not to bind, and a **cold** solve, where the objective is cost plus the
    peak tie-breaker and neither reads the calendar.
    """
    return Instance(
        days=7,
        shift_types=(ShiftType("M", 7.0, 8.0, 0.5),),
        employees=tuple(
            Employee(
                name=name,
                contract="salaried",
                skills=frozenset(),
                max_hours_this_week=38.0,
                max_daily_hours=8.0,
            )
            for name in ("A", "B", "C", "D", "E")
        ),
        open_shifts=tuple(OpenShift(day=d, shift=0, required=1) for d in range(7)),
        params=RuleParams(
            min_rest_hours=11.0,
            min_weekly_rest_hours=24.0,
            min_period_hours=3.0,
            max_consecutive_days=None,
        ),
        disruption=shipped_d2(),
    )


def permute_days(instance: Instance, permutation: dict[int, int]) -> Instance:
    return dataclasses.replace(
        instance,
        open_shifts=tuple(
            dataclasses.replace(o, day=permutation[o.day]) for o in instance.open_shifts
        ),
    )


DAY_PERMUTATIONS = [
    {0: 6, 1: 5, 2: 4, 3: 3, 4: 2, 5: 1, 6: 0},
    {0: 1, 1: 2, 2: 3, 3: 4, 4: 5, 5: 6, 6: 0},
]


@pytest.mark.parametrize("permutation", DAY_PERMUTATIONS, ids=["reverse", "rotate"])
def test_day_permutation_leaves_a_decoupled_cold_solve_invariant(permutation):
    instance = decoupled_week()
    assert solved(permute_days(instance, permutation)).objective == solved(instance).objective


def test_day_permutation_is_not_invariant_once_days_couple():
    """The negative half, which is the honest one: with a consecutive-day limit the
    feasible sets differ under permutation, so the unconditional claim is false.

    Kept as a test so the precondition above cannot quietly be dropped as redundant.
    """
    instance = decoupled_week()
    # One person, two *adjacent* days, nobody may work two days running: one day must go
    # unstaffed. The same two shifts moved apart are both coverable by the same person.
    adjacent = dataclasses.replace(
        instance,
        params=dataclasses.replace(instance.params, max_consecutive_days=1),
        employees=instance.employees[:1],
        open_shifts=tuple(OpenShift(day=d, shift=0, required=1) for d in (0, 1)),
    )
    spread = dataclasses.replace(
        adjacent,
        open_shifts=tuple(OpenShift(day=d, shift=0, required=1) for d in (0, 2)),
    )
    assert sum(solved(adjacent).shortfall.values()) == 1
    assert sum(solved(spread).shortfall.values()) == 0
