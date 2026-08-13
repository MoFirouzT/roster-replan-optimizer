"""The D0-D4 study layer: what has to hold before a regret number means anything.

The study's whole method is one lexicographic construction, and it fails silently in three
ways that all still print a plausible matrix.

- **A regret could be negative**, which is arithmetically impossible and means one of the
  two solves is wrong. The study asserts it inline; here it is asserted independently.
- **The held metric could not actually be held.** If the equality constraint were dropped,
  every regret would collapse to zero and the study would report perfect agreement — the
  most flattering possible result, reached by removing the measurement.
- **A gate literal could be left unasserted.** Every hard constraint in the model is
  conditioned on an assumption literal, so a solve that does not assert them lets the
  optimiser switch constraints off. The first version of this module did exactly that and
  scored rosters that broke hard rules.

The known-answer case is `early-notice/1`, whose arithmetic is checkable by hand and is
worked through in `docs/studies/disruption-metrics.md`. A study with no case whose numbers
can be derived without running it is a study that cannot be reviewed.
"""

from __future__ import annotations

import pytest

from benchmarks import metrics, suite
from roster_replan.checker import check

CASES = ["headline/0", "early-notice/1", "tight/0", "multi-absence/2", "scarce-skill/0"]


@pytest.fixture(scope="module")
def worked():
    """The case whose divergence is derived by hand in the study."""
    return suite.build("early-notice/1")


@pytest.mark.parametrize("case", CASES)
def test_regret_is_never_negative(case):
    """Holding `a` at its optimum cannot reach a `b` score below `b`'s own optimum: the
    lexicographic solve searches a subset of what the plain solve searched."""
    result = metrics.regrets(suite.build(case))
    for pair, regret in result["regret"].items():
        assert regret >= 0, f"{case} {pair} produced a negative regret of {regret}"


@pytest.mark.parametrize("case", CASES)
def test_every_metric_returns_a_legal_roster(case):
    """The gates are assumptions, and a solve that forgets to assert them returns rosters
    that break hard rules while reporting a lower objective."""
    instance = suite.build(case).instance
    for metric in metrics.METRICS:
        roster, _ = metrics.optimum(metrics.as_metric(instance, metric), metric)
        hard = [v for v in check(roster, instance) if not v.soft]
        assert hard == [], f"{metric} on {case} returned an illegal roster: {hard}"


@pytest.mark.parametrize("case", CASES)
def test_holding_a_metric_actually_holds_it(case):
    """The lexicographic solve must not improve the held metric's own objective away.

    Without this, the constraint could be silently ineffective and every regret would read
    zero — a study reporting that all five metrics agree, because it stopped measuring.
    """
    instance = suite.build(case).instance
    for hold in metrics.METRICS:
        roster, value = metrics.optimum(metrics.as_metric(instance, hold), hold)
        held_score = metrics.score_under(roster, instance, hold)
        for minimise in metrics.METRICS:
            if minimise == hold:
                continue
            other = metrics.best_under(instance, hold, value, minimise)
            assert metrics.score_under(other, instance, hold) == held_score, (
                f"{case}: minimising {minimise} moved {hold} off its optimum"
            )


def test_the_metric_swap_changes_only_the_metric():
    """Each metric nests the one before it, so the study is a clean comparison only if
    every weight, band and threshold is held while the metric name moves."""
    instance = suite.build("headline/0").instance
    for metric in metrics.METRICS:
        swapped = metrics.as_metric(instance, metric).disruption
        original = instance.disruption
        assert swapped.metric == metric
        for field in (
            "published_weight",
            "draft_weight",
            "notice_bands",
            "move_weight",
            "cancel_weight",
            "call_in_weight",
            "concentration_weight",
            "concentration_tiers",
            "shortfall_weight",
            "cost_weight",
        ):
            assert getattr(swapped, field) == getattr(original, field), field


def test_the_worked_divergence(worked):
    """`early-notice/1`, derived by hand in the study and asserted here.

    D2 answers with a call-in: two changed slots, scoring 2 x 10 = 20 to itself and
    10x10 + 10x14 = 240 to D3 as one cancellation plus one call-in. D3 answers with two
    moves: four changed slots, scoring 10 x 6 x 2 = 120 to itself and 4 x 10 = 40 to D2.
    Notice exceeds 24 hours so the multiplier is 1, and the whole week is published.
    """
    instance = worked.instance
    d2, _ = metrics.optimum(metrics.as_metric(instance, "D2"), "D2")
    d3, _ = metrics.optimum(metrics.as_metric(instance, "D3"), "D3")

    assert len(d2 ^ worked.incumbent) == 2
    assert len(d3 ^ worked.incumbent) == 4

    assert metrics.score_under(d2, instance, "D2") == 20
    assert metrics.score_under(d3, instance, "D3") == 120
    assert metrics.score_under(d2, instance, "D3") == 240
    assert metrics.score_under(d3, instance, "D2") == 40

    # D3's answer is two moves: the same employee dropped and added on the same day.
    changed = d3 ^ worked.incumbent
    days = {(employee, day) for employee, day, _ in changed}
    assert len(days) == 2, "the divergence is two paired moves, one per employee-day"


def test_the_study_reports_a_conflict_where_one_exists(worked):
    """End to end: the matrix must actually record the divergence above."""
    result = metrics.regrets(worked)
    assert result["regret"]["D2->D3"] == 120
    assert result["regret"]["D3->D2"] == 20
    assert result["regret"]["D0->D1"] == 0
