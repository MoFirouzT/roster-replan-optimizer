"""The fallback ladder, with every rung forced.

The ladder's failure mode is that it never runs. No instance in the committed set takes
more than 12.4 ms to prove optimality, so in normal operation every answer comes off the
top rung and the other three ship on the strength of a code review. That is the same
position `CLAUDE.md` describes for a test layer that has never been shown to fail.

So each test here **constructs the condition** rather than hoping for it:

- `exact` — an ordinary case.
- `time-boxed` — a solve stubbed to return what a budget-exhausted search returns, because
  the budget window that produces one for real is narrower than the machines CI runs on
  (`D-122`).
- `greedy` — a budget too small to find anything at all.
- `incumbent` — an incumbent whose *past* is already illegal, which greedy cannot repair
  because the past is pinned.

The last one is worth stating plainly: it is the only rung that returns a roster known to
break hard rules, and the test asserts that it says so.
"""

from __future__ import annotations

import dataclasses

import pytest

from benchmarks import studies, suite
from roster_replan import ladder
from roster_replan.checker import check
from roster_replan.domain import Employee, Instance, Interval, OpenShift
from roster_replan.model import solve


@pytest.fixture(scope="module")
def scenario():
    return suite.build("headline/0")


def test_exact_rung_on_an_ordinary_case(scenario):
    answer = ladder.answer(scenario.instance, budget_seconds=30.0)

    assert answer.rung == ladder.EXACT
    assert answer.gap == 0.0
    assert not answer.degraded
    assert answer.trustworthy
    assert answer.attempts == (ladder.EXACT,)


def test_time_boxed_rung_reports_a_gap_rather_than_hiding_it(monkeypatch, scenario):
    """A feasible roster the budget could not prove optimal, handed to the ladder directly.

    **Stubbing the solve here is a correction, not a shortcut** (`D-122`). The previous
    version asked for a budget that finds a roster and cannot prove it optimal, which is a
    window between first-feasible and proven-optimal — about 50 ms wide on the machine it
    was written on. CI fell below its lower edge and the ladder reported `incumbent`, on one
    of two jobs of the same commit on the same hardware. Widening it is not available
    either: this instance family proves optimal in about 90 ms at every size, and a
    four-week instance only stretches the window to 0.1-0.6 s, which a slower runner still
    loses.

    None of that window is the ladder's behaviour. What is asserted lives entirely in
    `_from_solve`: given a solution the solver could not prove optimal, the rung is
    `TIME_BOXED`, the gap is positive, and the caller is told in words. Handing it exactly
    that solution tests exactly that, on any machine, every time.
    """
    instance = scenario.instance
    proven = solve(instance)
    assert not isinstance(proven, list) and proven.status == "OPTIMAL"

    # The same legal roster, presented as the solver presents a time-boxed one: a real
    # answer with a bound it never closed.
    unproven = dataclasses.replace(proven, status="FEASIBLE", bound=proven.objective - 40)
    monkeypatch.setattr(ladder, "solve", lambda *args, **kwargs: unproven)

    answer = ladder.answer(instance, budget_seconds=0.05)

    assert answer.rung == ladder.TIME_BOXED
    assert answer.gap is not None and answer.gap > 0, "a time-boxed answer with no gap"
    assert answer.degraded
    assert answer.trustworthy, "a time-boxed roster is still a legal roster"
    assert "%" in answer.reason, "the gap must appear in what the caller is told"


def test_greedy_rung_when_the_search_finds_nothing(scenario):
    answer = ladder.answer(scenario.instance, budget_seconds=0.001)

    assert answer.rung == ladder.GREEDY
    assert answer.attempts == (ladder.EXACT, ladder.GREEDY)
    assert answer.trustworthy, "greedy must return a legal roster or fall further"
    assert answer.core == (), "nothing was proved, so there is no core to report"
    assert "budget" in answer.reason


def test_a_timeout_is_never_reported_as_an_infeasibility(scenario):
    """The bug this distinction exists for.

    `solve` used to return an empty `list[Gate]` on a timeout, which is type-identical to
    "proved infeasible with an empty core". A caller could not tell a proof from a
    stopwatch, and the explainer is specified to turn a core into prose.
    """
    from roster_replan.model import Unproven, solve

    outcome = solve(scenario.instance, time_limit=0.001)
    assert isinstance(outcome, Unproven)
    assert not isinstance(outcome, list)
    assert outcome.status != "INFEASIBLE"


def test_incumbent_rung_returns_the_published_roster_and_names_what_is_wrong():
    """The floor: an incumbent whose past is already illegal.

    Greedy cannot repair this, because `R-PIN-PAST` fixes the past and the violation is
    inside it. The ladder must return the published roster rather than nothing, and must
    not pretend it is clean.
    """
    instance, incumbent = _illegal_past()

    # The premise: the incumbent really is illegal, and the illegality is historical.
    violations = [v for v in check(incumbent, instance) if not v.soft]
    assert violations, "the fixture does not actually present an illegal past"

    answer = ladder.answer(instance, budget_seconds=30.0)

    assert answer.rung == ladder.INCUMBENT
    assert answer.roster == incumbent
    assert not answer.trustworthy, "this rung must not claim a broken roster is clean"
    assert answer.violations, "the violations are the point of this rung"
    assert "already broken" in answer.reason


def test_the_cold_path_cannot_promise_an_answer_and_says_so():
    """`never return nothing` is a promise about replanning, and the cold path cannot keep it.

    The failure it *can* hit is exhaustion, not infeasibility — see
    `test_a_cold_solve_is_never_infeasible` for why the other branch cannot be reached.
    With no incumbent there is nothing to repair and nothing to fall back to, and returning
    an empty roster as though it were an answer would satisfy the promise by lying.
    """
    instance = studies.identical_workforce(20, required=3)
    assert instance.incumbent is None

    answer = ladder.answer(instance, budget_seconds=0.0001)

    assert answer.rung == ladder.INCUMBENT
    assert answer.roster == frozenset()
    assert answer.core == (), "nothing was proved, so there is no core"
    assert "no incumbent" in answer.reason


def test_a_cold_solve_is_never_infeasible():
    """The empty roster satisfies every hard constraint, so a cold model always has an answer.

    This is `D-018`'s argument arriving somewhere it was not aimed: the coverage floor is
    soft and the ceiling is satisfied by assigning nobody, so understaffing is priced rather
    than refused and there is no way to make a cold instance infeasible by demanding too
    much. Asserted rather than assumed, because the ladder's cold branch is shaped by it —
    the only cold failure is running out of budget.
    """
    from roster_replan.model import solve

    # Demand no workforce could meet: one person, absent all week, and a shift to staff.
    outcome = solve(_impossible_cold(), time_limit=30.0)

    assert not isinstance(outcome, list), (
        "a cold instance was infeasible, which contradicts the soft coverage floor; "
        "if this fails, D-018's reasoning or the model has changed"
    )
    assert outcome.roster == frozenset()
    assert outcome.shortfall[0, 0] == 1, "the unstaffable shift is priced, not refused"


@pytest.mark.parametrize("budget", [0.001, 0.05, 30.0])
def test_the_ladder_never_raises_and_always_names_its_rung(scenario, budget):
    answer = ladder.answer(scenario.instance, budget_seconds=budget)
    assert answer.rung in ladder.RUNGS
    assert answer.reason
    assert answer.seconds >= 0


# --- Fixtures that construct the lower rungs ----------------------------------------


def _illegal_past() -> tuple[Instance, frozenset]:
    """A published roster with someone working a shift they were absent for, in the past."""
    base = studies.identical_workforce(4, required=1)
    absent = dataclasses.replace(
        base.employees[0],
        # Day 0 morning starts at hour 7 and runs 8 hours.
        absences=(Interval(0.0, 24.0),),
    )
    instance = dataclasses.replace(
        base,
        employees=(absent,) + base.employees[1:],
        now=48.0,
        published_through=7 * 24.0,
        incumbent=frozenset({(0, 0, 0)}),
    )
    return instance, instance.incumbent


def _impossible_cold() -> Instance:
    """Demand no roster can meet, and no incumbent: one shift needing two people, with a
    single employee who is the only one eligible."""
    base = studies.identical_workforce(1, required=1)
    return dataclasses.replace(
        base,
        employees=(
            Employee(
                name="solo",
                contract="salaried",
                skills=frozenset({"bar"}),
                absences=(Interval(0.0, 7 * 24.0),),
                max_hours_this_week=38.0,
                max_daily_hours=8.0,
            ),
        ),
        open_shifts=(OpenShift(day=0, shift=0, required=1),),
    )
