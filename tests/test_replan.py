"""The objective: D0-D4, the weighted trade-off, and brute-force stage (b).

Two things are being tested, and they are different. That each metric is *encoded*
correctly is checked by comparing `disruption.py` against `scoring.py` -- the same
independence discipline the rules get. That the five metrics are *distinct* is checked by
showing they choose different rosters, which is the claim `replan.md` makes and the T2
study will quantify.
"""

from __future__ import annotations

import dataclasses
import itertools

import pytest
from conftest import EVENING, MORNING, NIGHT
from test_differential import micro, week

from roster_replan.checker import is_feasible
from roster_replan.domain import NoticeBand, shipped_d2
from roster_replan.model import solve
from roster_replan.scoring import disruption_of, max_change_weight, score
from roster_replan.validation import validate_instance

METRICS = ["D0", "D1", "D2", "D3", "D4"]


def replan_of(instance, incumbent, **overrides):
    overrides.setdefault("published_through", 7 * 24.0)
    overrides.setdefault("now", 0.0)
    return dataclasses.replace(instance, incumbent=incumbent, **overrides)


# --- The nesting property ----------------------------------------------------------
# Each metric contains the one before it, which is what makes the T2 study a comparison
# rather than five unrelated numbers.


def test_d1_with_equal_weights_is_d0():
    instance = week()
    published = solve(instance)
    replan = replan_of(instance, published.roster)
    moved = frozenset(list(published.roster)[:-2])

    flat = dataclasses.replace(
        replan, disruption=shipped_d2(metric="D1", published_weight=1, draft_weight=1)
    )
    as_d0 = dataclasses.replace(replan, disruption=shipped_d2(metric="D0"))
    assert disruption_of(moved, flat) == disruption_of(moved, as_d0)


def test_d2_with_a_flat_band_is_d1():
    instance = week()
    published = solve(instance)
    replan = replan_of(instance, published.roster)
    moved = frozenset(list(published.roster)[:-2])

    flat = dataclasses.replace(
        replan,
        disruption=shipped_d2(metric="D2", notice_bands=(NoticeBand(float("inf"), 1),)),
    )
    as_d1 = dataclasses.replace(replan, disruption=shipped_d2(metric="D1"))
    assert disruption_of(moved, flat) == disruption_of(moved, as_d1)


# --- What each metric is sensitive to ----------------------------------------------


def test_d0_cannot_tell_a_published_change_from_a_draft_one():
    """The reason D0 is rejected, as a test rather than an assertion in prose."""
    instance = week()
    published = solve(instance)
    early = next(k for k in sorted(published.roster) if k[1] == 0)
    late = next(k for k in sorted(published.roster) if k[1] == 6)

    # Published only through day 1, so the day-0 change is published and day-6 is draft.
    base = replan_of(instance, published.roster, published_through=24.0)
    as_d0 = dataclasses.replace(base, disruption=shipped_d2(metric="D0"))
    assert disruption_of(published.roster - {early}, as_d0) == disruption_of(
        published.roster - {late}, as_d0
    )

    as_d1 = dataclasses.replace(base, disruption=shipped_d2(metric="D1"))
    assert disruption_of(published.roster - {early}, as_d1) > disruption_of(
        published.roster - {late}, as_d1
    )


def test_d2_prices_short_notice_higher():
    """The step at 24h: the same change, two distances from `now`."""
    instance = week()
    published = solve(instance)
    imminent = next(k for k in sorted(published.roster) if k[1] == 0)
    distant = next(k for k in sorted(published.roster) if k[1] == 5)

    base = replan_of(instance, published.roster)
    tonight = disruption_of(published.roster - {imminent}, base)
    next_week = disruption_of(published.roster - {distant}, base)
    assert tonight == 4 * next_week


def test_d3_counts_a_move_once():
    """A shift moved within a day is one event, not a drop plus an add."""
    instance = week()
    published = solve(instance)
    base = replan_of(instance, published.roster)

    victim = next(k for k in sorted(published.roster) if k[1] == 3 and k[2] == MORNING)
    employee, day, _ = victim
    moved = (published.roster - {victim}) | {(employee, day, EVENING)}

    as_d2 = dataclasses.replace(base, disruption=shipped_d2(metric="D2"))
    as_d3 = dataclasses.replace(base, disruption=shipped_d2(metric="D3"))

    # D2 charges two changed slots; D3 recognises one move.
    params = as_d3.disruption
    assert disruption_of(moved, as_d3) < 2 * params.cancel_weight * (
        disruption_of(moved, as_d2) // 2
    )
    # And a move is cheaper than an unpaired cancellation of the same slot.
    assert disruption_of(moved, as_d3) < disruption_of(published.roster - {victim}, as_d3)


def flat_instance():
    """Five people, one shift type, seven days, one body per day.

    Built by hand rather than derived from a solve so that publication state and notice
    band are identical for every slot compared -- otherwise a concentration test is
    really measuring the notice multiplier.
    """
    from roster_replan.domain import (
        Employee,
        Instance,
        OpenShift,
        RuleParams,
        ShiftType,
    )

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
            min_weekly_rest_hours=35.0,
            min_period_hours=3.0,
            max_consecutive_days=6,
        ),
        disruption=shipped_d2(),
        now=0.0,
        published_through=7 * 24.0,
    )


def test_d4_prefers_spreading_changes():
    """Three changes to one person against one change to three, priced.

    Days 2, 3 and 4 all carry the same publication state and the same notice band, so
    the only difference between the two rosters is *who bears the changes*.
    """
    incumbent = frozenset({(day % 5, day, 0) for day in range(7)})
    instance = dataclasses.replace(flat_instance(), incumbent=incumbent)

    concentrated = frozenset(
        {k for k in incumbent if k[1] not in (2, 3, 4)} | {(0, 2, 0), (0, 3, 0), (0, 4, 0)}
    )
    spread = frozenset(
        {k for k in incumbent if k[1] not in (2, 3, 4)}
        | {(0, 2, 0), (1, 3, 0), (2, 4, 0)}
    )

    as_d3 = dataclasses.replace(instance, disruption=shipped_d2(metric="D3"))
    as_d4 = dataclasses.replace(instance, disruption=shipped_d2(metric="D4"))

    # Same number of changes, same slots: D3 sums and is blind to who bears them.
    assert disruption_of(concentrated, as_d3) == disruption_of(spread, as_d3)
    # D4 is not. Three changes on one person cost f(3)=6 against 3 x f(1)=3.
    assert disruption_of(concentrated, as_d4) > disruption_of(spread, as_d4)


def test_convex_penalty_is_triangular():
    from roster_replan.scoring import _convex

    assert [_convex(n, 4) for n in range(5)] == [0, 1, 3, 6, 10]


# --- The five metrics choose different rosters -------------------------------------


def move_or_call_in():
    """A replan with exactly two sensible repairs, which the metrics rank differently.

    Ana holds day 0 morning and Bram day 0 evening. Ana becomes unavailable in the
    morning but not the evening, so either:

      A. Ana moves to the evening and Bram moves to the morning -- four changed slots,
         but two *moves* when changes are paired per person.
      B. Chloe is called in for the morning and Ana is dropped -- two changed slots, but
         an unpaired cancellation plus a call-in.

    D2 counts slots and prefers B. D3 pairs and prices by type, and prefers A. The
    divergence is the point: both answers are defensible, which is exactly `replan.md`'s
    claim about the five definitions.
    """
    from roster_replan.domain import (
        Employee,
        Instance,
        Interval,
        OpenShift,
        RuleParams,
        ShiftType,
    )

    def person(name, **extra):
        return Employee(
            name=name,
            contract="salaried",
            skills=frozenset(),
            max_hours_this_week=38.0,
            max_daily_hours=8.0,
            **extra,
        )

    return Instance(
        days=3,
        shift_types=(ShiftType("M", 7.0, 8.0, 0.5), ShiftType("E", 15.0, 8.0, 0.5)),
        employees=(
            person("Ana", absences=(Interval(7.0, 15.0),)),
            person("Bram"),
            person("Chloe"),
        ),
        open_shifts=(
            OpenShift(day=0, shift=MORNING, required=1),
            OpenShift(day=0, shift=EVENING, required=1),
        ),
        params=RuleParams(
            min_rest_hours=11.0,
            min_weekly_rest_hours=35.0,
            min_period_hours=3.0,
            max_consecutive_days=6,
        ),
        disruption=shipped_d2(),
        now=0.0,
        published_through=24.0,
        incumbent=frozenset({(0, 0, MORNING), (1, 0, EVENING)}),
    )


def test_d2_and_d3_choose_different_rosters():
    """`replan.md`'s central claim, demonstrated rather than asserted."""
    from roster_replan.checker import check

    instance = move_or_call_in()
    chosen = {}
    for metric in ("D2", "D3"):
        variant = dataclasses.replace(instance, disruption=shipped_d2(metric=metric))
        result = solve(variant)
        assert not isinstance(result, list), f"{metric} infeasible: {result}"
        assert [v for v in check(result.roster, variant) if not v.soft] == []
        chosen[metric] = result.roster

    assert chosen["D2"] != chosen["D3"], chosen

    # D2 keeps Bram where he is and calls Chloe in; D3 moves both and calls nobody.
    assert (2, 0, MORNING) in chosen["D2"], "D2 should call in the third person"
    assert (2, 0, MORNING) not in chosen["D3"], "D3 should prefer two moves"
    assert (0, 0, EVENING) in chosen["D3"], "D3 should move Ana rather than drop her"


def test_metrics_only_diverge_when_there_is_slack():
    """The finding that made the previous version of this test fail, kept as a test.

    A tightly-covered instance has one legal repair, so every metric returns it and the
    choice of metric is invisible. This matters for T2: an instance generator that does
    not vary coverage tightness would report "the metrics agree" as a finding, when it is
    a side effect of the instances.
    """
    from roster_replan.domain import Interval

    instance = week()
    published = solve(instance)
    sick = next(e for (e, d, s) in published.roster if d == 5)
    employees = list(instance.employees)
    employees[sick] = dataclasses.replace(
        employees[sick], absences=(Interval(5 * 24.0, 6 * 24.0),)
    )
    tight = dataclasses.replace(instance, employees=tuple(employees))

    rosters = {
        metric: solve(
            replan_of(tight, published.roster, disruption=shipped_d2(metric=metric))
        ).roster
        for metric in METRICS
    }
    assert len({frozenset(r) for r in rosters.values()}) == 1, (
        "this instance was chosen because it is tight enough to force one repair; if it "
        "now admits several, the test has lost its point rather than found a bug"
    )


# --- Brute force, stage (b) --------------------------------------------------------
# The half of the gate that needed a disruption metric to exist. The solver's optimum
# must equal the true optimum, enumerated and scored by the independent reading.


def enumerate_optimum(instance):
    """The true optimum: every hard-feasible roster, scored by `scoring.py`."""
    keys = [
        (e, o.day, o.shift)
        for e in range(len(instance.employees))
        for o in instance.open_shifts
    ]
    best = None
    for mask in itertools.product((0, 1), repeat=len(keys)):
        roster = frozenset(k for k, bit in zip(keys, mask) if bit)
        if not is_feasible(roster, instance):
            continue
        total = score(roster, instance).total
        if best is None or total < best:
            best = total
    return best


@pytest.mark.parametrize("metric", METRICS)
def test_brute_force_optimum_matches_the_solver(metric):
    """Stage (b), for every metric. A single objective mismatch here would mean the
    encoding and the specification have diverged."""
    instance = micro(disruption=shipped_d2(metric=metric))
    solution = solve(instance)
    assert not isinstance(solution, list)
    assert solution.objective == enumerate_optimum(instance)


@pytest.mark.parametrize("metric", METRICS)
def test_brute_force_optimum_matches_on_a_replan(metric):
    """The cold case exercises coverage and cost; only a replan exercises disruption."""
    instance = micro()
    published = solve(instance)
    assert not isinstance(published, list)

    replan = dataclasses.replace(
        instance,
        now=0.0,
        incumbent=published.roster,
        published_through=3 * 24.0,
        disruption=shipped_d2(metric=metric),
    )
    solution = solve(replan)
    assert not isinstance(solution, list)
    assert solution.objective == enumerate_optimum(replan)


@pytest.mark.parametrize("metric", METRICS)
def test_brute_force_optimum_matches_when_the_incumbent_became_ineligible(metric):
    """Regression: an incumbent assignment that presolve would remove.

    The model eliminates ineligible pairs, so without a variable for this one the drop of
    an employee who became unavailable is invisible to the objective -- the model
    understates the cost of exactly the change a replan exists to make. Stage (b) missed
    it until this case existed, because no other instance put an excluded pair in the
    incumbent.
    """
    from roster_replan.domain import Interval

    instance = micro()
    published = solve(instance)
    assert not isinstance(published, list)

    holder = next(e for (e, d, s) in published.roster if d == 0)
    employees = list(instance.employees)
    employees[holder] = dataclasses.replace(
        employees[holder], absences=(Interval(6.0, 16.0),)
    )

    replan = dataclasses.replace(
        instance,
        employees=tuple(employees),
        now=0.0,
        incumbent=published.roster,
        published_through=3 * 24.0,
        disruption=shipped_d2(metric=metric),
    )
    solution = solve(replan)
    assert not isinstance(solution, list)
    assert solution.objective == enumerate_optimum(replan)


@pytest.mark.parametrize("metric", METRICS)
def test_scorer_agrees_with_the_model_on_the_chosen_roster(metric):
    """Weaker than stage (b) but on a realistic instance, where enumeration cannot run."""
    instance = week()
    published = solve(instance)
    replan = replan_of(instance, published.roster, disruption=shipped_d2(metric=metric))
    solution = solve(replan)
    assert not isinstance(solution, list)
    assert score(solution.roster, replan).total == solution.objective


# --- Generation as cold start ------------------------------------------------------


def test_generation_makes_disruption_constant():
    """With an empty incumbent every change is an unpublished add, and coverage pins how
    many there are -- so disruption is the same for every roster meeting coverage, and
    the objective reduces to cost. That is why generation needs no separate formulation.
    """
    instance = micro()
    empty = dataclasses.replace(
        instance, now=0.0, incumbent=frozenset(), published_through=None
    )
    solution = solve(empty)
    assert not isinstance(solution, list)

    scores = set()
    for mask in itertools.product((0, 1), repeat=3):
        # Three rosters that each cover all three days with different people.
        roster = frozenset((employee, day, MORNING) for day, employee in enumerate(mask))
        if len(roster) == 3:
            scores.add(disruption_of(roster, empty))
    assert len(scores) == 1, scores


def test_cold_solve_has_no_disruption_term():
    instance = micro()
    assert disruption_of(frozenset({(0, 0, MORNING)}), instance) == 0


# --- The domination bound ----------------------------------------------------------


def test_domination_bound_is_validated():
    """Understaffing reduces disruption, so a shortfall weight that does not dominate
    lets the optimiser buy stability by leaving shifts empty."""
    instance = micro(disruption=shipped_d2(shortfall_weight=1))
    defects = validate_instance(instance)
    assert [d.field for d in defects] == ["disruption.shortfall_weight"]


def test_shipped_default_satisfies_the_bound():
    assert validate_instance(micro()) == []
    assert validate_instance(week()) == []


def test_bound_scales_with_the_metric():
    """D4 can charge more per change than D2, so it needs a larger shortfall weight."""
    assert max_change_weight(micro(disruption=shipped_d2(metric="D4"))) > max_change_weight(
        micro(disruption=shipped_d2(metric="D2"))
    )
    assert max_change_weight(micro(disruption=shipped_d2(metric="D0"))) == 1


def test_understaffing_is_never_bought():
    """The bound, end to end: a replan under every metric fully covers a satisfiable
    instance rather than trading coverage for stability."""
    instance = week()
    published = solve(instance)
    for metric in METRICS:
        replan = replan_of(instance, published.roster, disruption=shipped_d2(metric=metric))
        solution = solve(replan)
        assert sum(solution.shortfall.values()) == 0, metric
