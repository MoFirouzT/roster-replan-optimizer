"""Input validation: defects the checker must never report as roster violations.

The dividing question throughout is whether a different roster could fix the fault. If
none could, it belongs here, and asserting that the checker stays quiet about it is as
much the point as catching it.
"""

from __future__ import annotations

import dataclasses

from conftest import MORNING

from roster_replan.checker import check
from roster_replan.domain import OpenShift, ShiftType, SkillMixEntry, shipped_d2
from roster_replan.validation import validate_instance


def fields(defects) -> list[str]:
    return [d.field for d in defects]


def test_a_well_formed_instance_has_no_defects(make_instance, person, one_shift):
    assert validate_instance(make_instance([person], [one_shift])) == []


# --- R-MIN-SHIFT ------------------------------------------------------------------


def test_min_shift_rejects_a_short_shift_type(make_instance, person, one_shift):
    instance = make_instance([person], [one_shift])
    stumpy = dataclasses.replace(
        instance,
        shift_types=(ShiftType(label="X", start_hour=7.0, span_hours=2.0, break_hours=0.0),)
        + instance.shift_types[1:],
    )
    (defect,) = validate_instance(stumpy)
    assert defect.field == "shift_types[0].span_hours"
    assert (defect.observed, defect.required) == (2.0, 3.0)


def test_min_shift_is_not_a_roster_violation(make_instance, person, one_shift):
    """No reachable roster can violate it, so the checker must be silent -- the reason
    the rule was reclassified out of the checker entirely."""
    instance = make_instance([person], [one_shift])
    stumpy = dataclasses.replace(
        instance,
        shift_types=(ShiftType(label="X", start_hour=7.0, span_hours=2.0, break_hours=0.0),)
        + instance.shift_types[1:],
    )
    assert "R-MIN-SHIFT" not in [v.rule for v in check(frozenset({(0, 0, MORNING)}), stumpy)]


def test_min_shift_reads_span_not_net(make_instance, person, one_shift):
    """A 3h period containing a 30-minute break is still a 3h work period: art. 21
    governs the period, and a prestatie may contain short breaks."""
    instance = make_instance([person], [one_shift])
    exact = dataclasses.replace(
        instance,
        shift_types=(ShiftType(label="X", start_hour=7.0, span_hours=3.0, break_hours=0.5),)
        + instance.shift_types[1:],
    )
    assert validate_instance(exact) == []


# --- Derogations ------------------------------------------------------------------


def test_derogation_below_statute_needs_a_basis(make_instance, person, one_shift, params):
    instance = make_instance([person], [one_shift])
    lax = dataclasses.replace(instance, params=dataclasses.replace(params, min_rest_hours=9.0))
    assert fields(validate_instance(lax)) == ["params.derogation_basis['min_rest_hours']"]


def test_derogation_with_a_basis_is_accepted(make_instance, person, one_shift, params):
    instance = make_instance([person], [one_shift])
    documented = dataclasses.replace(
        instance,
        params=dataclasses.replace(
            params,
            min_rest_hours=9.0,
            derogation_basis={"min_rest_hours": "art. 38ter §2, shift-change derogation"},
        ),
    )
    assert validate_instance(documented) == []


def test_stricter_than_statute_needs_nothing(make_instance, person, one_shift, params):
    instance = make_instance([person], [one_shift])
    strict = dataclasses.replace(instance, params=dataclasses.replace(params, min_rest_hours=12.0))
    assert validate_instance(strict) == []


# --- Budgets ----------------------------------------------------------------------


def test_missing_budget_is_a_defect(make_instance, person, one_shift):
    unbudgeted = dataclasses.replace(person, max_hours_this_week=None)
    instance = make_instance([unbudgeted], [one_shift])
    assert "employees[0].max_hours_this_week" in fields(validate_instance(instance))


def test_budget_over_the_absolute_ceiling_is_a_defect(make_instance, person, one_shift):
    """Locally verifiable, unlike the reference-period average -- and a payload defect
    rather than an R-MAX-WEEKLY violation, since no roster could repair it."""
    generous = dataclasses.replace(person, max_hours_this_week=60.0)
    instance = make_instance([generous], [one_shift])
    (defect,) = validate_instance(instance)
    assert defect.field == "employees[0].max_hours_this_week"
    assert defect.required == 50.0


def test_daily_maximum_over_the_ladder_is_a_defect(make_instance, person, one_shift):
    generous = dataclasses.replace(person, max_daily_hours=14.0)
    instance = make_instance([generous], [one_shift])
    assert "employees[0].max_daily_hours" in fields(validate_instance(instance))


# --- Replan pairing ---------------------------------------------------------------


def test_now_without_incumbent_is_a_defect(make_instance, person, one_shift):
    instance = make_instance([person], [one_shift], now=9.0)
    assert fields(validate_instance(instance)) == ["incumbent"]


def test_incumbent_without_now_is_a_defect(make_instance, person, one_shift):
    instance = make_instance([person], [one_shift], incumbent=frozenset())
    assert fields(validate_instance(instance)) == ["now"]


def test_cold_solve_needs_neither(make_instance, person, one_shift):
    assert validate_instance(make_instance([person], [one_shift])) == []


# --- Eligibility gates ------------------------------------------------------------


def test_flexi_without_gates_is_a_defect(make_instance, person, one_shift):
    """Absence must never default to eligible -- that would invent an eligibility the
    NSSO did not grant."""
    flexi = dataclasses.replace(person, contract="flexi")
    instance = make_instance([flexi], [one_shift])
    assert fields(validate_instance(instance)) == [
        "employees[0].flexi_eligible",
        "employees[0].dimona_ok",
    ]


def test_flexi_with_empty_gates_is_accepted(make_instance, person, one_shift):
    """An explicit empty set is a caller saying "eligible on no day", which is a
    meaningful and lawful answer -- distinct from having said nothing."""
    flexi = dataclasses.replace(
        person, contract="flexi", flexi_eligible=frozenset(), dimona_ok=frozenset()
    )
    assert validate_instance(make_instance([flexi], [one_shift])) == []


# --- Skill-mix provenance ---------------------------------------------------------


def test_hard_skill_mix_entry_needs_provenance(make_instance, person):
    shift = OpenShift(
        day=0,
        shift=MORNING,
        required=1,
        skill_mix=(SkillMixEntry(skill="nurse", minimum=1, hard=True),),
    )
    instance = make_instance([person], [shift])
    assert fields(validate_instance(instance)) == [
        "open_shifts[0].skill_mix[0].provenance"
    ]


def test_soft_skill_mix_entry_needs_none(make_instance, person):
    shift = OpenShift(
        day=0,
        shift=MORNING,
        required=1,
        skill_mix=(SkillMixEntry(skill="first-aid", minimum=1, hard=False),),
    )
    assert validate_instance(make_instance([person], [shift])) == []


# --- Catalogue integrity ----------------------------------------------------------


def test_open_shift_outside_the_horizon_is_a_defect(make_instance, person):
    instance = make_instance([person], [OpenShift(day=9, shift=MORNING, required=1)])
    assert "open_shifts[0].day" in fields(validate_instance(instance))


def test_duplicate_open_shift_is_a_defect(make_instance, person, one_shift):
    instance = make_instance([person], [one_shift, one_shift])
    assert "open_shifts[1]" in fields(validate_instance(instance))


def test_unknown_shift_type_is_a_defect(make_instance, person):
    instance = make_instance([person], [OpenShift(day=0, shift=99, required=1)])
    assert "open_shifts[0].shift" in fields(validate_instance(instance))


# --- The horizon a week's rules can be stated over ---------------------------------


def test_a_horizon_of_one_week_is_accepted(make_instance, person, one_shift):
    assert validate_instance(make_instance([person], [one_shift], days=7)) == []


def test_a_horizon_of_whole_weeks_is_accepted(make_instance, person, one_shift):
    """What `D-110` refused and `D-113` allows, once the rules were scoped to the week."""
    assert validate_instance(make_instance([person], [one_shift], days=14)) == []
    assert validate_instance(make_instance([person], [one_shift], days=28)) == []


def test_a_horizon_ending_part_way_through_a_week_is_a_defect(make_instance, person, one_shift):
    """Ten days is a week plus a three-day stub, and no roster can put 35 hours of rest
    inside three days. The model would report that as an infeasibility naming
    `R-WEEKLY-REST`, which is true and useless: the week it is about is mostly not in the
    payload. No roster fixes it, so it is the request that is wrong."""
    (defect,) = validate_instance(make_instance([person], [one_shift], days=10))
    assert defect.field == "days"
    assert (defect.observed, defect.required) == (10, "7 or fewer, or a multiple of 7")
    assert "3-day stub" in defect.message


def test_a_shorter_horizon_is_still_answered(make_instance, person, one_shift):
    """`D-029` prices the short horizon as conservatism -- there `R-WEEKLY-REST` is too
    strict, never too weak -- so it is answered rather than refused."""
    assert validate_instance(make_instance([person], [one_shift], days=3)) == []


def test_the_request_is_accepted_and_the_roster_is_judged_on_its_merits(make_instance, person):
    """The whole arc, in one assertion pair.

    `D-110` refused this payload because both readings would have called the roster legal.
    `D-111` scoped the rules to the week, so the checker reports the second week's 33 hours
    of rest. `D-113` therefore has no reason left to refuse the payload — and the two halves
    are now doing the jobs they are for: validation passes the request, and the checker
    judges the roster.
    """
    ana = dataclasses.replace(person, max_hours_this_week=45.0)
    shifts = [OpenShift(day=day, shift=MORNING, required=1) for day in range(7, 13)]
    instance = make_instance([ana], shifts, days=14)
    roster = frozenset({(0, day, MORNING) for day in range(7, 13)})

    assert validate_instance(instance) == []
    assert [(v.rule, v.day) for v in check(roster, instance)] == [("R-WEEKLY-REST", 7)]


# --- The domination bound ----------------------------------------------------------
# `D-057` derives the bound rather than choosing it, and says it is validated rather than
# trusted. Nothing asserted that until mutation testing found the check could be disabled
# without a single test objecting.


def test_a_shortfall_weight_that_does_not_dominate_is_a_defect(
    make_instance, person, one_shift
):
    """Understaffing *reduces* disruption, so a shortfall weight below the bound lets the
    optimiser buy stability by leaving shifts empty -- an ordering error that looks like a
    tuning problem. A weight scale that violates it is a malformed request."""
    weak = make_instance(
        [person], [one_shift], disruption=shipped_d2(shortfall_weight=1)
    )
    (defect,) = validate_instance(weak)

    assert defect.field == "disruption.shortfall_weight"
    assert defect.observed == 1


def test_the_bound_scales_with_demand(make_instance, person):
    """`max req x max_change_weight`: doubling the headcount a single shift needs doubles
    the disruption that leaving it empty can avoid, so a weight that passed can stop
    passing without the profile changing at all."""
    weight = shipped_d2(shortfall_weight=200)

    small = make_instance([person], [OpenShift(day=0, shift=MORNING, required=1)],
                          disruption=weight)
    large = make_instance([person], [OpenShift(day=0, shift=MORNING, required=8)],
                          disruption=weight)

    assert fields(validate_instance(small)) == []
    assert "disruption.shortfall_weight" in fields(validate_instance(large))
