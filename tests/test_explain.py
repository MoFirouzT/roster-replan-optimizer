"""The shortfall explainer, and the invariant that makes it more than presentation.

`D-047` re-scoped T4 before it started: with a soft coverage floor a cold solve is
essentially never infeasible, so the explainer's ordinary job is shortfalls, not
infeasibility. Measured on the committed set — 16 of 72 cases return an optimal roster that
still leaves a shift short, and none is infeasible.

The load-bearing test here is `test_no_unexplained_employee_on_an_optimal_roster`. Because
`shortfall_weight` dominates every other term (`D-057`), an optimal solver adds anyone it
legally can, so **every person off an under-staffed slot must be blocked by something**. An
employee the checker says could have been added is therefore not a gap in the explanation —
it is evidence that the roster is suboptimal, or that the model and the checker disagree
about eligibility.

Run across all 72 cases, that makes this module a fifth reading of the rules rather than a
report over the other four: it can fail on a roster the model, the checker, the differential
harness and the golden record all accept, because it asks a question none of them asks.
"""

from __future__ import annotations

import dataclasses

import pytest

from benchmarks import suite
from roster_replan.checker import check
from roster_replan.domain import Interval
from roster_replan.explain import explain
from roster_replan.model import solve

CASES = ["headline/0", "scarce-skill/0", "tight/0", "large/0", "thin-availability/0"]


@pytest.fixture(scope="module")
def solved():
    out = {}
    for case in CASES:
        scenario = suite.build(case)
        out[case] = (scenario, solve(scenario.instance, time_limit=30.0).roster)
    return out


# --- The invariant ------------------------------------------------------------------


def test_no_unexplained_employee_on_an_optimal_roster():
    """Across every committed case, not a sample.

    This is the one test worth the runtime: it asserts a property of *the solver* through
    the explainer, over the whole distribution, and the whole distribution is what makes it
    meaningful — a shortfall that could have been filled is rare by construction and would
    not show up in five hand-picked cases.
    """
    offenders = []
    for case in suite.case_names():
        scenario = suite.build(case)
        roster = solve(scenario.instance, time_limit=30.0).roster
        for finding in explain(roster, scenario.instance):
            if finding.unexplained:
                offenders.append((case, finding.day, finding.shift, finding.unexplained))

    assert not offenders, (
        f"an optimal roster left a shift short while somebody could legally have filled it: "
        f"{offenders[:5]}. Either the solver is suboptimal or the model and the checker "
        f"disagree about eligibility -- both are defects, not explanations"
    )


def test_the_invariant_has_teeth(solved):
    """Break a roster and the explainer must notice.

    A dropped assignment leaves the slot short with the dropped person able to return, which
    is exactly the shape the invariant above forbids. Without this, a version of `explain`
    that never populated `unexplained` would pass that test on all 72 cases.
    """
    scenario, roster = solved["headline/0"]
    instance = scenario.instance

    staffed = {
        (o.day, o.shift)
        for o in instance.open_shifts
        if not instance.is_past(o.day, o.shift)
        and sum(1 for _, d, s in roster if (d, s) == (o.day, o.shift)) >= o.required
    }
    victim = next(k for k in sorted(roster) if (k[1], k[2]) in staffed)

    findings = explain(roster - {victim}, instance)
    culprit = next(f for f in findings if (f.day, f.shift) == (victim[1], victim[2]))

    assert victim[0] in culprit.unexplained, (
        "the dropped employee can legally be put back, so the explainer must report them "
        "as unexplained rather than inventing a reason"
    )


# --- What it reports ----------------------------------------------------------------


@pytest.mark.parametrize("case", CASES)
def test_every_reported_shortfall_is_a_real_one(case, solved):
    """The explainer's slots must match the checker's, in both directions."""
    scenario, roster = solved[case]
    instance = scenario.instance

    reported = {(f.day, f.shift) for f in explain(roster, instance)}
    from_checker = {
        (v.day, v.shift)
        for v in check(roster, instance)
        if v.rule == "R-COVER" and v.soft and not instance.is_past(v.day, v.shift)
    }

    assert reported == from_checker, (
        f"{case}: explainer says {sorted(reported)}, checker says {sorted(from_checker)}"
    )


@pytest.mark.parametrize("case", CASES)
def test_every_blocked_employee_carries_at_least_one_rule(case, solved):
    scenario, roster = solved[case]
    for finding in explain(roster, scenario.instance):
        for entry in finding.blocked:
            assert entry.rules, f"{case}: employee {entry.employee} blocked by nothing"


def test_a_person_blocked_twice_is_counted_under_both_rules():
    """Relaxing one of two blockers does not free them, so naming one reason would mislead
    about what would have to change."""
    from roster_replan.explain import Blocked, Shortfall

    finding = Shortfall(
        day=0,
        shift=0,
        required=2,
        assigned=0,
        blocked=(
            Blocked(employee=0, rules=("R-AVAIL", "R-MAX-WEEKLY")),
            Blocked(employee=1, rules=("R-AVAIL",)),
        ),
        unexplained=(),
    )

    assert finding.by_rule() == {"R-AVAIL": 2, "R-MAX-WEEKLY": 1}
    assert finding.by_employee() == {1: 1, 0: 2}
    assert list(finding.by_employee()) == [1, 0]  # fewest blockers first
    assert finding.short == 2


def test_the_cause_is_named_when_there_is_exactly_one():
    """A slot nobody is available for, with availability the only thing wrong.

    Constructed rather than found: on a generated case several rules block at once, which is
    realistic and useless for checking that the right rule is named.
    """
    scenario = suite.build("headline/0")
    instance = scenario.instance
    target = next(o for o in instance.open_shifts if not instance.is_past(o.day, o.shift))
    window = instance.window(target.day, target.shift)

    # The slot's skill requirement is stripped as well. Leaving it in blocks six of the
    # twelve for `R-SKILL` *as well as* availability, which is realistic and useless here:
    # the point is to check the right rule is named when exactly one applies.
    everyone_absent = dataclasses.replace(
        instance,
        employees=tuple(
            dataclasses.replace(person, absences=person.absences + (Interval(window.start, window.end),))
            for person in instance.employees
        ),
        open_shifts=tuple(
            dataclasses.replace(o, required_skills=frozenset(), skill_mix=())
            if (o.day, o.shift) == (target.day, target.shift)
            else o
            for o in instance.open_shifts
        ),
        incumbent=frozenset(),
        now=None,
        published_through=None,
    )

    findings = explain(frozenset(), everyone_absent)
    culprit = next(f for f in findings if (f.day, f.shift) == (target.day, target.shift))

    assert culprit.unexplained == ()
    assert set(culprit.by_rule()) == {"R-AVAIL"}, culprit.by_rule()
    assert culprit.by_rule()["R-AVAIL"] == len(instance.employees)


def test_historical_slots_are_not_explained(solved):
    """A shift that has already started cannot be repaired, so naming who could not have
    worked it is noise — the same exclusion the objective makes."""
    scenario, roster = solved["headline/0"]
    instance = scenario.instance

    for finding in explain(roster, instance):
        assert not instance.is_past(finding.day, finding.shift)


def test_the_summary_names_the_slot_and_the_rules(solved):
    scenario, roster = solved["scarce-skill/0"]
    finding = explain(roster, scenario.instance)[0]

    summary = finding.summary()
    assert f"day {finding.day}" in summary
    assert "short" in summary
    assert any(rule in summary for rule in finding.by_rule())


def test_a_rule_already_broken_is_not_a_reason_to_refuse_someone():
    """The subtraction in `_blocking_rules`, which nothing in the committed set exercises.

    Every committed roster is legal, so no employee's own row is already broken and the
    "rules already broken before this addition" set is always empty. The mutation harness
    proved it: deleting the subtraction changed no result.

    It matters on the one roster shape that does occur — an incumbent whose *past* is already
    illegal, which `R-PIN-PAST` forces the solver to keep. Without the subtraction, that
    person's existing violation would be reported as the reason they cannot take an unrelated
    shift later in the week, which is both wrong and unactionable: relaxing it frees nobody.
    """
    scenario = suite.build("headline/0")
    cold = dataclasses.replace(
        scenario.base, incumbent=None, now=None, published_through=None
    )

    early = min(cold.open_shifts, key=lambda o: (o.day, o.shift))
    window = cold.window(early.day, early.shift)

    # Employee 0 is absent for `early`, and the roster puts them on it anyway.
    broken = dataclasses.replace(
        cold,
        employees=(
            dataclasses.replace(
                cold.employees[0],
                absences=cold.employees[0].absences + (Interval(window.start, window.end),),
            ),
        )
        + cold.employees[1:],
    )
    roster = frozenset({(0, early.day, early.shift)})

    assert any(
        v.rule == "R-AVAIL" and v.employee == 0
        for v in check(roster, broken)
        if not v.soft
    ), "the fixture does not actually put employee 0 in breach"

    # A slot late in the week, far enough from `early` that no rest gap links them.
    late = max(cold.open_shifts, key=lambda o: (o.day, o.shift))
    finding = next(f for f in explain(roster, broken) if (f.day, f.shift) == (late.day, late.shift))

    reasons = {rule for entry in finding.blocked if entry.employee == 0 for rule in entry.rules}
    assert "R-AVAIL" not in reasons, (
        f"employee 0's pre-existing R-AVAIL breach was reported as the reason they cannot "
        f"work an unrelated later shift: {reasons}"
    )
