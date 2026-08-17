"""The registry's **hard, optional** family (`D-135`, `D-136`).

Seven rules a caller opts into by supplying a parameter, all of them constraints
`D-134` measured this model breaking on every case it was given, all of them now encoded:
`R-MAX-WEEKENDS`, `R-MIN-DAYS-OFF`, `R-MIN-BLOCK`, `R-MAX-SHIFT-TYPE`, `R-MIN-HOURS`,
`R-SUCCESSION`, and `R-CONSEC-DAYS`'s per-employee limit.

`tests/micro_instances.py` carries nine instances for them, so brute-force ground truth and
the differential harness already hold the two readings against each other. What is here is
what those cannot say:

**The rules are off unless asked for.** Both parameters are optional in `R-MAX-PERIOD`'s
sense, and `weekend_days` is empty by default. A rule that quietly switched itself on would
change every existing caller's roster, and the committed set would be the last place to
notice — its instances supply none of these parameters.

**Weekends are counted, not weekend days.** The distinction is invisible on any instance with
one shift per weekend, which is most of them.

**A stretch of days off at the horizon's edge is not judged.** Read without that latitude the
rule failed all 26 published rosters in the benchmark set it came from, so it is the boundary
worth a test in both directions rather than a comment.
"""

from __future__ import annotations

import dataclasses

import pytest

from roster_replan.checker import check
from roster_replan.domain import OpenShift, RuleParams
from roster_replan.model import solve
from roster_replan.validation import validate_instance
from tests.micro_instances import EVENING, MICRO_INSTANCES, MORNING, instance, person

WEEKEND = frozenset({5, 6})


def _two_weeks(**employee) -> object:
    """A fortnight with a shift on every day of both weekends."""
    return instance(
        days=14,
        employees=[person("Ana", **employee)],
        open_shifts=tuple(
            OpenShift(day=day, shift=MORNING, required=1) for day in (5, 6, 12, 13)
        ),
        params=RuleParams(
            min_rest_hours=11.0,
            min_weekly_rest_hours=35.0,
            min_period_hours=3.0,
            max_consecutive_days=6,
            weekend_days=WEEKEND,
        ),
    )


# --- Off unless asked for -------------------------------------------------------------


def test_no_weekend_limit_means_no_rule():
    """Absent is ordinary, not a defect: the caller is not asking for the rule."""
    unlimited = _two_weeks()
    every_weekend_day = frozenset({(0, day, MORNING) for day in (5, 6, 12, 13)})

    assert [v for v in check(every_weekend_day, unlimited) if v.rule == "R-MAX-WEEKENDS"] == []


def test_a_limit_without_a_stated_weekend_forbids_nothing():
    """`weekend_days` empty switches the rule off, and that is the shipped default.

    This domain has no calendar — a week is a position in the horizon, never a Monday — so
    which days are the weekend is a fact only the caller holds. A model that guessed would
    put a calendar back into the one module built without one.
    """
    no_calendar = dataclasses.replace(
        _two_weeks(max_weekends=1),
        params=dataclasses.replace(_two_weeks().params, weekend_days=frozenset()),
    )
    every_weekend_day = frozenset({(0, day, MORNING) for day in (5, 6, 12, 13)})

    assert [v for v in check(every_weekend_day, no_calendar) if v.rule == "R-MAX-WEEKENDS"] == []


def test_a_minimum_of_one_day_off_forbids_nothing():
    """Every gap between two worked days is at least a day long, so a minimum of 1 is
    satisfied by construction and is treated as absent rather than encoded."""
    trivial = instance(
        employees=[person("Ana", min_consecutive_days_off=1)],
        open_shifts=tuple(OpenShift(day=d, shift=MORNING, required=1) for d in (0, 2, 4)),
    )
    alternating = frozenset({(0, day, MORNING) for day in (0, 2, 4)})

    assert [v for v in check(alternating, trivial) if v.rule == "R-MIN-DAYS-OFF"] == []


# --- Weekends, not weekend days -------------------------------------------------------


def test_both_days_of_one_weekend_are_one_weekend():
    """The distinction the threshold micro-instance exists for, asserted directly.

    A reading that counted weekend *days* would call this two and refuse it. The rule people
    actually hold is about how many of their weekends are taken, not how many days it cost.
    """
    limited = _two_weeks(max_weekends=1)
    one_whole_weekend = frozenset({(0, 5, MORNING), (0, 6, MORNING)})

    assert [v for v in check(one_whole_weekend, limited) if v.rule == "R-MAX-WEEKENDS"] == []

    split_across_two = frozenset({(0, 5, MORNING), (0, 12, MORNING)})
    breach = [v for v in check(split_across_two, limited) if v.rule == "R-MAX-WEEKENDS"]
    assert len(breach) == 1
    assert breach[0].observed == 2 and breach[0].required == 1


def test_the_solver_will_not_take_a_second_weekend():
    """The model's half of the same claim. Both weekends are staffable and only one may be
    taken, so the optimum leaves a shift short rather than breaching the limit."""
    limited = _two_weeks(max_weekends=1)
    outcome = solve(limited, seed=7, time_limit=30.0)

    weeks = {day // 7 for (_, day, _) in outcome.roster}
    assert len(weeks) == 1, f"took weekends in {weeks}"
    assert [v for v in check(outcome.roster, limited) if not v.soft] == []


# --- The horizon's edge ---------------------------------------------------------------


@pytest.mark.parametrize(
    ("worked", "expected"),
    [
        # A single day off at the start, at the end, and in the middle of the horizon.
        # Only the middle one is a stretch this roster can be judged on.
        (frozenset({1, 2, 3, 4, 5, 6}), []),
        (frozenset({0, 1, 2, 3, 4, 5}), []),
        (frozenset({0, 1, 2, 4, 5, 6}), [3]),
    ],
    ids=["off-at-day-zero", "off-at-the-last-day", "off-in-the-middle"],
)
def test_only_interior_stretches_of_days_off_are_judged(worked, expected):
    """`D-134`'s boundary latitude, in both directions.

    A stretch reaching either end may continue outside the payload, and a roster cannot be
    judged on days it does not contain. Applied without it, this rule failed every one of
    the 26 published rosters in the set it came from — which is one rule read too strictly
    rather than 26 wrong rosters.
    """
    week = instance(
        days=7,
        employees=[person("Ana", min_consecutive_days_off=2, max_hours_this_week=60.0)],
        open_shifts=tuple(OpenShift(day=d, shift=MORNING, required=1) for d in range(7)),
    )
    roster = frozenset({(0, day, MORNING) for day in worked})

    assert [v.day for v in check(roster, week) if v.rule == "R-MIN-DAYS-OFF"] == expected


def test_the_model_and_the_checker_agree_about_the_edge():
    """The two readings reach the latitude differently and must land in the same place.

    In the model it falls out of the forbidden pattern needing a worked day on both sides;
    in the checker it is an explicit skip. That asymmetry is exactly the kind the differential
    harness exists to catch, so it gets an instance of its own.
    """
    edge = MICRO_INSTANCES["days_off_at_the_horizon_edge_are_not_judged"]
    outcome = solve(edge, seed=7, time_limit=30.0)

    # Both shifts are taken: the single day off after the last one is at the edge.
    assert len(outcome.roster) == 2
    assert check(outcome.roster, edge) == []


# --- The parameter a caller states in a coordinate system they do not otherwise use ---


def test_a_weekend_day_outside_a_week_is_rejected():
    """A day index of 7 is not a stricter weekend, it is a typo that would silently switch
    the rule off for the day it names."""
    broken = dataclasses.replace(
        _two_weeks(max_weekends=1),
        params=dataclasses.replace(_two_weeks().params, weekend_days=frozenset({5, 7})),
    )

    defects = [d for d in validate_instance(broken) if d.field == "params.weekend_days"]
    assert len(defects) == 1
    assert defects[0].observed == 7


# --- The rest of the family (`D-136`) -------------------------------------------------


def _week(**employee):
    """One person, a shift open every day of a week."""
    return instance(
        days=7,
        employees=[person("Ana", max_hours_this_week=60.0, **employee)],
        open_shifts=tuple(OpenShift(day=d, shift=MORNING, required=1) for d in range(7)),
    )


@pytest.mark.parametrize(
    ("worked", "expected"),
    [
        (frozenset({1, 2, 3}), []),
        (frozenset({0, 2, 3, 4}), []),          # the day-zero block touches the edge
        (frozenset({1, 2, 3, 4, 5, 6}), []),    # and so does the day-six one
        (frozenset({1, 4, 5}), [1]),            # a lone interior day is the breach
    ],
    ids=["a-legal-block", "block-at-day-zero", "block-at-the-last-day", "a-lone-day"],
)
def test_only_interior_blocks_of_work_are_judged(worked, expected):
    """`R-MIN-BLOCK` mirrors `R-MIN-DAYS-OFF`, including its boundary latitude: a block
    running to either end of the horizon may continue outside it."""
    week = _week(min_consecutive_days_worked=2)
    roster = frozenset({(0, day, MORNING) for day in worked})

    assert [v.day for v in check(roster, week) if v.rule == "R-MIN-BLOCK"] == expected


def test_a_shift_type_cap_is_not_a_cap_on_shifts():
    """`R-MAX-SHIFT-TYPE` counts one type. A reading that counted every shift would refuse a
    roster this one must allow, and a cap of zero — a prohibition — would become a cap on
    working at all."""
    capped = instance(
        days=7,
        employees=[person("Ana", max_hours_this_week=60.0, max_shifts_per_type={EVENING: 1})],
        open_shifts=(
            OpenShift(day=0, shift=MORNING, required=1),
            OpenShift(day=2, shift=MORNING, required=1),
            OpenShift(day=4, shift=EVENING, required=1),
        ),
    )
    two_mornings_and_an_evening = frozenset({(0, 0, MORNING), (0, 2, MORNING), (0, 4, EVENING)})

    assert [v for v in check(two_mornings_and_an_evening, capped) if v.rule == "R-MAX-SHIFT-TYPE"] == []


def test_a_cap_of_zero_is_a_prohibition_and_is_reported_as_a_rule():
    """Not folded into the presolve's exclusions: presolve removes pairs that *cannot* be
    worked, and a cap the tenant chose should come back as a rule the roster broke."""
    forbidden = instance(
        days=7,
        employees=[person("Ana", max_shifts_per_type={EVENING: 0})],
        open_shifts=(OpenShift(day=0, shift=EVENING, required=1),),
    )
    breach = [v for v in check(frozenset({(0, 0, EVENING)}), forbidden) if v.rule == "R-MAX-SHIFT-TYPE"]

    assert len(breach) == 1
    assert breach[0].observed == 1 and breach[0].required == 0


def test_the_hours_floor_is_the_one_rule_an_empty_roster_breaks():
    """Every other hard rule in the registry is satisfied by assigning nobody. This one is
    what makes `R-MIN-HOURS` able to conflict with `R-COVER`'s soft floor."""
    floored = _week(min_hours_this_period=15.0)

    empty = [v for v in check(frozenset(), floored) if not v.soft]
    assert [v.rule for v in empty] == ["R-MIN-HOURS"]

    enough = frozenset({(0, 0, MORNING), (0, 3, MORNING)})
    assert [v for v in check(enough, floored) if v.rule == "R-MIN-HOURS"] == []


def test_an_unmeetable_floor_is_an_infeasibility_that_names_itself():
    """The conflict `rules.md` warns about, end to end. There is one shift and a floor two
    shifts high, so no legal roster exists — and because the rule is gated, the answer is a
    core naming `R-MIN-HOURS` rather than a shortfall a planner has to interpret.
    """
    impossible = instance(
        days=7,
        employees=[person("Ana", min_hours_this_period=15.0)],
        open_shifts=(OpenShift(day=0, shift=MORNING, required=1),),
    )
    core = solve(impossible, seed=7, time_limit=30.0)

    assert isinstance(core, list) and core, "expected an infeasibility core"
    # `in` rather than `==`: CP-SAT returns a sufficient set of assumptions, not a minimal
    # one, which is the same caveat `tests/test_differential.py` records.
    assert "R-MIN-HOURS" in {gate.rule for gate in core}


def test_a_forbidden_succession_is_not_a_rest_gap():
    """The claim `rules.md` makes about the two overlapping without either subsuming the
    other, asserted on the pair that separates them.

    Evening-then-morning is refused by `R-REST-GAP` anyway — eight hours — so it proves
    nothing. Morning-then-evening leaves 24 hours, which the gap rule permits.
    """
    paired = instance(
        days=7,
        employees=[person("Ana", max_hours_this_week=60.0)],
        open_shifts=(
            OpenShift(day=0, shift=MORNING, required=1),
            OpenShift(day=1, shift=EVENING, required=1),
        ),
        params=dataclasses.replace(
            _week().params, forbidden_successions=frozenset({(MORNING, EVENING)})
        ),
    )
    roster = frozenset({(0, 0, MORNING), (0, 1, EVENING)})
    found = [v.rule for v in check(roster, paired)]

    assert "R-SUCCESSION" in found
    assert "R-REST-GAP" not in found, "the pair must be legal on rest, or the rule proves nothing"

    # And the reverse pairing is untouched: the rule is directional.
    reversed_pairs = dataclasses.replace(
        paired,
        params=dataclasses.replace(
            paired.params, forbidden_successions=frozenset({(EVENING, MORNING)})
        ),
    )
    assert [v for v in check(roster, reversed_pairs) if v.rule == "R-SUCCESSION"] == []


def test_a_personal_consecutive_limit_overrides_the_tenants():
    """`R-CONSEC-DAYS` per employee (`D-136`) — one rule, two limits, not two rules."""
    mixed = instance(
        days=7,
        employees=[
            person("Ana", max_hours_this_week=60.0, max_consecutive_days=2),
            person("Bram", max_hours_this_week=60.0),
        ],
        open_shifts=tuple(OpenShift(day=d, shift=MORNING, required=1) for d in range(4)),
    )

    ana = frozenset({(0, day, MORNING) for day in range(3)})
    assert [v.rule for v in check(ana, mixed) if v.rule == "R-CONSEC-DAYS"] == ["R-CONSEC-DAYS"]

    # The same three days for Bram, whose limit is the tenant's six.
    bram = frozenset({(1, day, MORNING) for day in range(3)})
    assert [v for v in check(bram, mixed) if v.rule == "R-CONSEC-DAYS"] == []
