"""One firing test and one silence test per rule.

The silence half matters as much as the firing half: a checker that reports a violation
on every roster passes every firing test and is worthless. Several tests below therefore
assert on the *whole* violation set rather than on the presence of one rule ID.
"""

from __future__ import annotations

import dataclasses
import pathlib

from conftest import EVENING, MORNING, NIGHT, hours, unavailable

from roster_replan.checker import check, is_feasible
from roster_replan.domain import Employee, Interval, OpenShift, SkillMixEntry


def rules(violations) -> list[str]:
    return [v.rule for v in violations]


# --- R-COVER ------------------------------------------------------------------------


def test_cover_exact_is_silent(make_instance, person, one_shift):
    instance = make_instance([person], [one_shift])
    assert check(frozenset({(0, 0, MORNING)}), instance) == []


def test_cover_shortfall_is_soft(make_instance, person, one_shift):
    instance = make_instance([person], [one_shift])
    (violation,) = check(frozenset(), instance)
    assert violation.rule == "R-COVER"
    assert violation.soft is True
    assert (violation.observed, violation.required) == (0, 1)


def test_cover_overstaffing_is_hard(make_instance, person, one_shift):
    other = dataclasses.replace(person, name="Bram")
    instance = make_instance([person, other], [one_shift])
    roster = frozenset({(0, 0, MORNING), (1, 0, MORNING)})
    (violation,) = check(roster, instance)
    assert (violation.rule, violation.soft) == ("R-COVER", False)
    assert not is_feasible(roster, instance)


def test_shortfall_alone_stays_feasible(make_instance, person, one_shift):
    """Hard feasibility ignores soft violations -- otherwise there is no cost axis."""
    instance = make_instance([person], [one_shift])
    assert is_feasible(frozenset(), instance)


# --- R-AVAIL ----------------------------------------------------------------------


def test_avail_overlapping_absence_fires(make_instance, person, one_shift):
    absent = dataclasses.replace(person, absences=(unavailable(0, 6.0, 12.0),))
    instance = make_instance([absent], [one_shift])
    assert "R-AVAIL" in rules(check(frozenset({(0, 0, MORNING)}), instance))


def test_avail_is_interval_not_day(make_instance, person):
    """A morning unavailability must not block an evening shift on the same day.

    This is the behaviour the spec deliberately corrected: the walking skeleton blocked whole days.
    """
    morning_only = dataclasses.replace(person, unavailability=(unavailable(0, 6.0, 12.0),))
    instance = make_instance([morning_only], [OpenShift(day=0, shift=EVENING, required=1)])
    assert check(frozenset({(0, 0, EVENING)}), instance) == []


def test_avail_touching_intervals_do_not_overlap(make_instance, person, one_shift):
    """Half-open: unavailability ending exactly at the shift start is not a conflict."""
    until_seven = dataclasses.replace(person, unavailability=(unavailable(0, 0.0, 7.0),))
    instance = make_instance([until_seven], [one_shift])
    assert check(frozenset({(0, 0, MORNING)}), instance) == []


# --- R-SKILL and R-SKILL-MIX ------------------------------------------------------


def test_skill_missing_fires(make_instance, person):
    shift = OpenShift(day=0, shift=MORNING, required=1, required_skills=frozenset({"forklift"}))
    instance = make_instance([person], [shift])
    assert "R-SKILL" in rules(check(frozenset({(0, 0, MORNING)}), instance))


def test_skill_mix_soft_entry_fires_soft(make_instance, person):
    other = dataclasses.replace(person, name="Bram")
    shift = OpenShift(
        day=0,
        shift=MORNING,
        required=2,
        skill_mix=(SkillMixEntry(skill="first-aid", minimum=1, hard=False),),
    )
    instance = make_instance([person, other], [shift])
    (violation,) = check(frozenset({(0, 0, MORNING), (1, 0, MORNING)}), instance)
    assert (violation.rule, violation.soft) == ("R-SKILL-MIX", True)


def test_skill_mix_clamps_to_rostered_headcount(make_instance, person):
    """Two first-aiders cannot be required of a shift that only got one body -- the
    missing person is already R-COVER's finding, and double-counting it makes
    shortfalls incomparable across instances."""
    medic = dataclasses.replace(person, skills=frozenset({"bar", "first-aid"}))
    shift = OpenShift(
        day=0,
        shift=MORNING,
        required=2,
        skill_mix=(SkillMixEntry(skill="first-aid", minimum=2, hard=False),),
    )
    instance = make_instance([medic], [shift])
    assert rules(check(frozenset({(0, 0, MORNING)}), instance)) == ["R-COVER"]


# --- R-PIN-PAST -------------------------------------------------------------------


def test_pin_past_removal_fires(make_instance, person, one_shift):
    incumbent = frozenset({(0, 0, MORNING)})
    instance = make_instance([person], [one_shift], now=hours(0, 9.0), incumbent=incumbent)
    violations = check(frozenset(), instance)
    assert "R-PIN-PAST" in rules(violations)
    assert all(v.historical for v in violations if v.rule == "R-PIN-PAST")


def test_shift_in_progress_counts_as_past(make_instance, person, one_shift):
    """The boundary is `start < now`, strictly: three hours already worked cannot be
    un-worked, so a shift running at `now` is pinned."""
    instance = make_instance(
        [person], [one_shift], now=hours(0, 9.0), incumbent=frozenset({(0, 0, MORNING)})
    )
    assert instance.is_past(0, MORNING)


def test_future_shift_is_not_pinned(make_instance, person):
    shift = OpenShift(day=3, shift=MORNING, required=1)
    instance = make_instance(
        [person], [shift], now=hours(0, 9.0), incumbent=frozenset({(0, 3, MORNING)})
    )
    assert "R-PIN-PAST" not in rules(check(frozenset({(0, 3, MORNING)}), instance))


# --- R-REST-GAP -------------------------------------------------------------------


def test_rest_gap_fires_between_night_and_morning(make_instance, person):
    """Night ends 07:00 on day 1, morning starts 07:00 -- 0h rest against 11h."""
    shifts = [OpenShift(day=0, shift=NIGHT, required=1), OpenShift(day=1, shift=MORNING, required=1)]
    generous = dataclasses.replace(person, max_hours_this_week=40.0)
    instance = make_instance([generous], shifts)
    violations = check(frozenset({(0, 0, NIGHT), (0, 1, MORNING)}), instance)
    gap = next(v for v in violations if v.rule == "R-REST-GAP")
    assert (gap.observed, gap.required) == (0.0, 11.0)


def test_rest_gap_respects_horizon_boundary(make_instance, person, one_shift):
    """A shift that ended at 02:00 on the first horizon day constrains that morning --
    history the horizon cannot see, supplied by the caller."""
    arriving = dataclasses.replace(person, last_shift_end_before_horizon=hours(0, 2.0))
    instance = make_instance([arriving], [one_shift])
    assert "R-REST-GAP" in rules(check(frozenset({(0, 0, MORNING)}), instance))


def test_rest_gap_silent_when_history_is_old(make_instance, person, one_shift):
    rested = dataclasses.replace(person, last_shift_end_before_horizon=hours(-1, 20.0))
    instance = make_instance([rested], [one_shift])
    assert check(frozenset({(0, 0, MORNING)}), instance) == []


# --- R-WEEKLY-REST ----------------------------------------------------------------


def test_weekly_rest_fires_when_every_day_worked(make_instance, person):
    shifts = [OpenShift(day=d, shift=MORNING, required=1) for d in range(7)]
    unlimited = dataclasses.replace(person, max_hours_this_week=60.0)
    instance = make_instance([unlimited], shifts)
    roster = frozenset({(0, d, MORNING) for d in range(7)})
    weekly = next(v for v in check(roster, instance) if v.rule == "R-WEEKLY-REST")
    assert weekly.observed < 35.0


def test_weekly_rest_silent_with_a_free_weekend(make_instance, person):
    shifts = [OpenShift(day=d, shift=MORNING, required=1) for d in range(5)]
    instance = make_instance([person], shifts)
    roster = frozenset({(0, d, MORNING) for d in range(5)})
    assert "R-WEEKLY-REST" not in rules(check(roster, instance))


# --- R-MAX-WEEKLY and R-MAX-DAILY -------------------------------------------------


def test_max_weekly_reads_net_hours_not_span(make_instance, person):
    """Five 8h spans with 30-minute breaks are 40h gross and 37.5h net. A budget of 38h
    is therefore satisfied -- and would be breached by a checker reading spans."""
    shifts = [OpenShift(day=d, shift=MORNING, required=1) for d in range(5)]
    instance = make_instance([person], shifts)
    roster = frozenset({(0, d, MORNING) for d in range(5)})
    assert "R-MAX-WEEKLY" not in rules(check(roster, instance))


def test_max_weekly_fires_over_budget(make_instance, person):
    shifts = [OpenShift(day=d, shift=MORNING, required=1) for d in range(6)]
    tight = dataclasses.replace(person, max_hours_this_week=20.0)
    instance = make_instance([tight], shifts)
    roster = frozenset({(0, d, MORNING) for d in range(6)})
    assert "R-MAX-WEEKLY" in rules(check(roster, instance))


def test_max_weekly_silent_when_budget_absent(make_instance, person, one_shift):
    """A missing budget is an input defect, not a violation: the checker must not
    invent a ceiling."""
    unbudgeted = dataclasses.replace(person, max_hours_this_week=None)
    instance = make_instance([unbudgeted], [one_shift])
    assert "R-MAX-WEEKLY" not in rules(check(frozenset({(0, 0, MORNING)}), instance))


def test_max_daily_fires_on_split_shifts(make_instance, person):
    """Two 7.5h-net periods on one day exceed an 8h daily maximum while satisfying the
    rest gap -- the case that stops R-MAX-DAILY being redundant."""
    shifts = [OpenShift(day=0, shift=MORNING, required=1), OpenShift(day=0, shift=EVENING, required=1)]
    instance = make_instance([person], shifts)
    roster = frozenset({(0, 0, MORNING), (0, 0, EVENING)})
    assert "R-MAX-DAILY" in rules(check(roster, instance))


# --- R-CONSEC-DAYS ----------------------------------------------------------------


def test_consec_days_fires_on_seven(make_instance, person):
    shifts = [OpenShift(day=d, shift=MORNING, required=1) for d in range(7)]
    unlimited = dataclasses.replace(person, max_hours_this_week=60.0)
    instance = make_instance([unlimited], shifts)
    roster = frozenset({(0, d, MORNING) for d in range(7)})
    streak = next(v for v in check(roster, instance) if v.rule == "R-CONSEC-DAYS")
    assert (streak.observed, streak.required, streak.day) == (7, 6, 6)


def test_consec_days_counts_history(make_instance, person):
    """Someone who worked four days before Monday is out of days on Wednesday. A model
    whose windows begin at day 0 silently grants a fresh streak."""
    shifts = [OpenShift(day=d, shift=MORNING, required=1) for d in range(3)]
    tired = dataclasses.replace(person, consecutive_days_worked_before_horizon=4)
    instance = make_instance([tired], shifts)
    roster = frozenset({(0, d, MORNING) for d in range(3)})
    streak = next(v for v in check(roster, instance) if v.rule == "R-CONSEC-DAYS")
    assert (streak.observed, streak.day) == (7, 2)


def test_consec_days_reports_once_per_run(make_instance, person):
    shifts = [OpenShift(day=d, shift=MORNING, required=1) for d in range(7)]
    unlimited = dataclasses.replace(person, max_hours_this_week=60.0)
    instance = make_instance([unlimited], shifts)
    roster = frozenset({(0, d, MORNING) for d in range(7)})
    assert rules(check(roster, instance)).count("R-CONSEC-DAYS") == 1


def test_consec_days_disabled_is_silent(make_instance, person, params):
    shifts = [OpenShift(day=d, shift=MORNING, required=1) for d in range(7)]
    unlimited = dataclasses.replace(person, max_hours_this_week=60.0)
    instance = make_instance([unlimited], shifts)
    off = dataclasses.replace(instance, params=dataclasses.replace(params, max_consecutive_days=None))
    roster = frozenset({(0, d, MORNING) for d in range(7)})
    assert "R-CONSEC-DAYS" not in rules(check(roster, off))


# --- Eligibility gates ------------------------------------------------------------


def test_flexi_gates_fire_for_uncertified_day(make_instance, person, one_shift):
    flexi = dataclasses.replace(
        person, contract="flexi", flexi_eligible=frozenset({1}), dimona_ok=frozenset({1})
    )
    instance = make_instance([flexi], [one_shift])
    fired = rules(check(frozenset({(0, 0, MORNING)}), instance))
    assert "R-FLEXI-ELIG" in fired and "R-DIMONA-FLX" in fired


def test_flexi_gates_are_per_day(make_instance, person):
    """A Dimona may not cross a quarter boundary, so eligibility can end mid-horizon.
    Day 0 is certified, day 1 is not.
    """
    flexi = dataclasses.replace(
        person, contract="flexi", flexi_eligible=frozenset({0}), dimona_ok=frozenset({0})
    )
    shifts = [OpenShift(day=0, shift=MORNING, required=1), OpenShift(day=1, shift=MORNING, required=1)]
    instance = make_instance([flexi], shifts)
    violations = check(frozenset({(0, 0, MORNING), (0, 1, MORNING)}), instance)
    assert {v.day for v in violations if v.rule == "R-FLEXI-ELIG"} == {1}


def test_salaried_contract_ignores_flexi_gates(make_instance, person, one_shift):
    instance = make_instance([person], [one_shift])
    fired = rules(check(frozenset({(0, 0, MORNING)}), instance))
    assert "R-FLEXI-ELIG" not in fired and "R-DIMONA-FLX" not in fired


# --- Determinism ------------------------------------------------------------------


def test_violation_order_is_stable(make_instance, person):
    shifts = [OpenShift(day=d, shift=MORNING, required=1) for d in range(7)]
    unlimited = dataclasses.replace(person, max_hours_this_week=60.0)
    instance = make_instance([unlimited], shifts)
    roster = frozenset({(0, d, MORNING) for d in range(7)})
    assert [v.key() for v in check(roster, instance)] == [
        v.key() for v in check(roster, instance)
    ]


def test_empty_instance_has_no_violations(make_instance):
    assert check(frozenset(), make_instance([], [])) == []


def test_independence_contracts_hold():
    """The independence rule, mechanised. Runs the import-linter contracts from
    pyproject.toml so a boundary violation fails the suite and not only CI.

    Only the module boundary is enforceable this way. The no-shared-thresholds half
    stays a review obligation, because no linter distinguishes a shared constant from a
    coincidentally equal one.
    """
    import subprocess
    import sys

    result = subprocess.run(
        [sys.executable, "-m", "importlinter.cli", "lint-imports"],
        capture_output=True,
        text=True,
        cwd=pathlib.Path(__file__).parent.parent,
    )
    assert result.returncode == 0, result.stdout + result.stderr


def test_interval_overlap_is_half_open():
    assert not Interval(0.0, 5.0).overlaps(Interval(5.0, 9.0))
    assert Interval(0.0, 5.0).overlaps(Interval(4.9, 9.0))


def test_employee_defaults_supply_no_rule_thresholds():
    """No rule parameter may have a default near the schema -- a shared threshold is
    invisible to both the brute-force and the differential layer.
    """
    blank = Employee(name="X", contract="salaried", skills=frozenset())
    assert blank.max_hours_this_week is None
    assert blank.max_daily_hours is None
    assert blank.flexi_eligible is None and blank.dimona_ok is None
