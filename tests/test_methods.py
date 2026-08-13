"""The method-comparison layer: what has to hold before any benchmark number means anything.

A results table is only evidence if the machinery producing it cannot flatter one method.
Three things would let it, and each has a test here.

- **A method could win by cheating.** The disruption solve is optimal by construction, so
  no other method can score better on the same yardstick. If one does, either the yardstick
  differs per method or a "roster" is not legal. `test_optimum_dominates` is the check, and
  it is the single most load-bearing test in this file.
- **The warm start could change the answer.** A hint is a search suggestion, not a
  constraint. Implemented as one -- variables fixed to their hinted value -- it would still
  return rosters, still look fast, and quietly report a suboptimal number as the optimum.
- **A method could return something illegal.** Every returned roster is checked, which is
  the suite-wide invariant applied here rather than a separate claim.

One case per class at seed 0. Every class, because a method's weakness is a property of the
instance shape -- greedy fails where a repair needs a chain, and only the tight and thin
classes produce those.
"""

from __future__ import annotations

import dataclasses

import pytest

from benchmarks import greedy, methods, suite
from roster_replan.checker import check
from roster_replan.scoring import disruption_of, score

CASES = [f"{name}/0" for name in suite.CLASSES]


@pytest.fixture(scope="module")
def scenarios():
    return {case: suite.build(case) for case in CASES}


@pytest.fixture(scope="module")
def outcomes(scenarios):
    """Every method on every sampled case, run once and shared.

    Module-scoped because these are solves: re-running them per assertion would multiply
    the suite's runtime by the number of properties being asserted, for identical results.
    """
    return {
        case: {m: methods.run(m, scenario, time_limit=10.0) for m in methods.METHODS}
        for case, scenario in scenarios.items()
    }


@pytest.mark.parametrize("case", CASES)
def test_every_method_returns_a_legal_roster(case, outcomes):
    for method, outcome in outcomes[case].items():
        assert outcome.violations == (), f"{method} on {case} broke {outcome.violations}"


@pytest.mark.parametrize("case", CASES)
def test_optimum_dominates(case, scenarios, outcomes):
    """No method scores below the disruption solve, which is optimal by construction.

    Compared on `Score.total` rather than on disruption alone: greedy reaches a lower
    disruption on some cases by leaving a shift unstaffed, and that is not a better answer
    -- it is a different point that the shortfall weight is there to price. Comparing the
    parts separately would make the coverage-for-stability trade look like a win.
    """
    instance = scenarios[case].instance
    best = score(outcomes[case][methods.WARM_REPLAN].roster_or_fail(), instance).total

    for method in (methods.GREEDY, methods.COLD_COST, methods.COLD_DISRUPTION):
        other = score(outcomes[case][method].roster_or_fail(), instance).total
        assert best <= other, (
            f"{method} scored {other} on {case}, below the {best} of an optimal solve -- "
            f"either the yardstick is not shared or that roster is not legal"
        )


@pytest.mark.parametrize("case", CASES)
def test_the_hint_does_not_change_the_optimum(case, outcomes):
    """A warm start is a suggestion. One implemented as a constraint would fix variables
    to the incumbent's values and return the best roster *containing the damage*."""
    cold = outcomes[case][methods.COLD_DISRUPTION]
    warm = outcomes[case][methods.WARM_REPLAN]
    assert warm.disruption == cold.disruption
    assert warm.short_slots == cold.short_slots


@pytest.mark.parametrize("case", CASES)
def test_methods_are_deterministic(case, scenarios):
    """Same case, same seed, same roster. Without this every benchmark number is a
    sample of one from an undocumented distribution."""
    scenario = scenarios[case]
    for method in methods.METHODS:
        first = methods.run(method, scenario, seed=7, time_limit=10.0)
        again = methods.run(method, scenario, seed=7, time_limit=10.0)
        assert first.disruption == again.disruption
        assert first.changes == again.changes


# --- The greedy baseline ------------------------------------------------------------


@pytest.mark.parametrize("case", CASES)
def test_greedy_never_overstaffs_or_touches_the_past(case, scenarios):
    scenario = scenarios[case]
    instance = scenario.instance
    roster = greedy.repair(instance, scenario.incumbent)

    for open_shift in instance.open_shifts:
        assigned = sum(
            1 for _, day, shift in roster if (day, shift) == (open_shift.day, open_shift.shift)
        )
        assert assigned <= open_shift.required, f"greedy overstaffed {open_shift} on {case}"

    past_before = {k for k in scenario.incumbent if instance.is_past(k[1], k[2])}
    past_after = {k for k in roster if instance.is_past(k[1], k[2])}
    assert past_after == past_before, f"greedy moved a pinned shift on {case}"


@pytest.mark.parametrize("case", CASES)
def test_greedy_only_ever_drops_what_broke(case, scenarios):
    """It repairs; it does not reshuffle. Every incumbent assignment it dropped must be
    one the checker names, or the baseline is quietly doing optimisation."""
    scenario = scenarios[case]
    instance = scenario.instance
    roster = greedy.repair(instance, scenario.incumbent)

    named = {
        (v.employee, v.day, v.shift)
        for v in check(scenario.incumbent, instance)
        if not v.soft and None not in (v.employee, v.day, v.shift)
    }
    for key in scenario.incumbent - roster:
        assert key in named, f"greedy dropped {key} on {case}, which no rule objected to"


def test_greedy_keeps_the_past_when_the_past_is_what_broke(scenarios):
    """A person taken ill during a shift they had already started.

    The committed set never produces this: the generator injects events into the future
    only, because a damaged past is not a replan question. That makes it exactly the case
    an unreached branch hides in, and the first version of `_drop_broken` was wrong here
    -- it excluded the past by reading `Violation.historical`, which only three rules set,
    so an unflagged `R-AVAIL` on a started shift got the pinned assignment dropped.

    Built by hand from a committed scenario rather than added as a generator event, so the
    instance set and its fingerprints do not move for a case that exists to test one
    branch.
    """
    scenario = scenarios["headline/0"]
    instance = scenario.instance
    past = sorted(k for k in scenario.incumbent if instance.is_past(k[1], k[2]))
    assert past, "the headline scenario has no past assignment to damage"

    employee, day, shift = past[0]
    person = instance.employees[employee]
    people = list(instance.employees)
    people[employee] = dataclasses.replace(
        person, absences=person.absences + (instance.window(day, shift),)
    )
    damaged = dataclasses.replace(instance, employees=tuple(people))

    roster = greedy.repair(damaged, scenario.incumbent)

    assert (employee, day, shift) in roster, "greedy unpinned a shift that had started"
    assert not [v for v in check(roster, damaged) if v.rule == "R-PIN-PAST"]


# --- The cost baseline --------------------------------------------------------------


@pytest.mark.parametrize("case", CASES)
def test_the_cost_profile_prices_no_deviation(case, scenarios):
    """The one thing that makes `cold-cost` a cost baseline: under its profile, changing
    the roster is free. A weight left un-zeroed would make it a disruption solve with a
    smaller weight, and its number would look like evidence about cost."""
    scenario = scenarios[case]
    instance = scenario.instance
    profile = methods.cost_profile(instance)
    priced = dataclasses.replace(instance, disruption=profile)
    assert disruption_of(scenario.incumbent, priced) == 0
    assert disruption_of(frozenset(), priced) == 0


def test_the_cost_baseline_is_measured_on_the_shipped_yardstick(scenarios, outcomes):
    """It optimises the cost profile and is scored on the scenario's own. Scoring it under
    the profile it optimised would report zero disruption for every cold solve, which is
    true of that profile and says nothing about the roster."""
    disruptions = [
        outcomes[case][methods.COLD_COST].disruption
        for case in CASES
        if outcomes[case][methods.COLD_COST].changes > 0
    ]
    assert disruptions, "no cold-cost run changed anything; the comparison is vacuous"
    assert all(d > 0 for d in disruptions)
