"""The penalty search: a rival formulation, and the premise its study rests on.

`benchmarks/anneal.py` exists so `D-002` can be read as a number rather than as a sentence.
That makes one of these tests different in kind from the rest: **the search must be shown to
return an illegal roster** when a hard rule is priced cheaply. If a later change quietly
repaired its way back to feasibility, every number in the study would still compute and would
mean nothing, so the premise is asserted here rather than assumed by the runner.

The others are the ordinary obligations of a benchmark rival: the objective it reports is the
one it claims to report, a seed reproduces a run, and the one structural restriction on its
move generator actually holds. That last one carries weight beyond tidiness — the generator
refuses slots that have already started, so if it leaked the study's headline illegality rate
would be inflated by `R-PIN-PAST` violations that no engine would ever commit.
"""

from __future__ import annotations

import pytest

from benchmarks import anneal, suite
from roster_replan.checker import check
from roster_replan.scoring import score

CASES = ["headline/0", "tight/0", "multi-absence/0"]


@pytest.fixture(scope="module")
def scenarios():
    return {case: suite.build(case) for case in CASES}


@pytest.mark.parametrize("case", CASES)
def test_the_penalty_is_the_yardstick_plus_the_price_of_the_rules(case, scenarios):
    """`penalty` must be `score().total + weight x hard`, because the study reads it as that.

    The objective term is the same `scoring.score` every other method in `methods.py` is
    scored on. If this drifts, the search is optimising something the comparison does not
    measure and every gap in the study is against the wrong reference.
    """
    scenario = scenarios[case]
    instance = scenario.instance
    weight = 1_000

    total, objective, hard = anneal.penalty(scenario.incumbent, instance, weight)

    expected_objective = score(scenario.incumbent, instance).total
    expected_hard = sum(1 for v in check(scenario.incumbent, instance) if not v.soft)

    assert objective == expected_objective
    assert hard == expected_hard
    assert total == expected_objective + weight * expected_hard


@pytest.mark.parametrize("case", CASES)
def test_a_seed_reproduces_the_run(case, scenarios):
    """A rival whose number moves between runs cannot be compared with anything."""
    scenario = scenarios[case]
    kwargs = dict(hard_weight=10_000, evaluations=2_000, seed=11)

    first = anneal.anneal(scenario.instance, scenario.incumbent, **kwargs)
    second = anneal.anneal(scenario.instance, scenario.incumbent, **kwargs)

    assert first.roster == second.roster
    assert (first.objective, first.hard, first.accepted) == (
        second.objective,
        second.hard,
        second.accepted,
    )


@pytest.mark.parametrize("case", CASES)
def test_the_returned_roster_is_the_best_one_seen(case, scenarios):
    """Metropolis ends wherever it happens to be; the answer is the best, not the last."""
    scenario = scenarios[case]
    result = anneal.anneal(
        scenario.instance, scenario.incumbent, hard_weight=10_000, evaluations=2_000, seed=3
    )

    recomputed, objective, hard = anneal.penalty(
        result.roster, scenario.instance, result.hard_weight
    )

    assert (objective, hard) == (result.objective, result.hard)
    assert recomputed == min(sample.penalty for sample in result.trace)


@pytest.mark.parametrize("case", CASES)
def test_the_search_never_touches_a_shift_that_has_already_started(case, scenarios):
    """The one structural restriction, and the study's honesty depends on it holding.

    Priced rules are meant to show a search buying its way out of a *rule*. A generator that
    could also rewrite the past would report `R-PIN-PAST` violations no real engine would
    commit, and the headline rate would be inflated by the harness rather than earned.
    """
    scenario = scenarios[case]
    instance = scenario.instance

    result = anneal.anneal(
        instance, scenario.incumbent, hard_weight=1, evaluations=3_000, seed=5
    )

    past_before = {key for key in scenario.incumbent if instance.is_past(key[1], key[2])}
    past_after = {key for key in result.roster if instance.is_past(key[1], key[2])}

    assert past_after == past_before
    assert not any(
        v.rule == "R-PIN-PAST" for v in check(result.roster, instance) if not v.soft
    )


def test_a_cheaply_priced_rule_is_bought_rather_than_respected(scenarios):
    """The study's premise, mechanised: priced rules produce an illegal roster.

    This is the sentence `D-002` decides on and `D-003` leans on -- *a penalised legal rule
    produces a roster that is cheaply illegal* -- and it had never been measured anywhere in
    this project. If a future change makes the search repair into feasibility, the study is
    stale and this test is how anyone finds out.

    Asserted at weight 1 across the sampled classes rather than on one case, so a single
    instance that happens to have no cheap violation available cannot make it pass hollowly.
    """
    illegal = {}
    for case, scenario in scenarios.items():
        result = anneal.anneal(
            scenario.instance, scenario.incumbent, hard_weight=1, evaluations=3_000, seed=7
        )
        hard = [v for v in check(result.roster, scenario.instance) if not v.soft]
        illegal[case] = [v.rule for v in hard]

    assert any(illegal.values()), (
        "no priced rule was broken anywhere at weight 1 -- either the search has acquired a "
        f"feasibility gate or the penalty is not being applied: {illegal}"
    )


@pytest.mark.parametrize("case", CASES)
def test_the_search_walks_through_illegal_rosters_rather_than_around_them(case, scenarios):
    """No feasibility gate, asserted on the trajectory instead of on the answer.

    The version of this file without this test **passed with a feasibility gate installed**.
    A gate refusing any move that raises the violation count still returns an illegal roster,
    because the incumbent arrives carrying the damage the event did and the gate forbids
    repairing through a worse state -- so `hard > 0` at the end, and every assertion about the
    answer agrees with an unpenalised search.

    What separates them is the path, so the path is what is asserted: a priced rule has to be
    one the search is willing to *break*, not merely one it declines to fix.
    """
    scenario = scenarios[case]
    result = anneal.anneal(
        scenario.instance, scenario.incumbent, hard_weight=1, evaluations=3_000, seed=5
    )

    assert result.accepted_illegal > 0, (
        "the search never accepted a move that raised the hard-violation count, which means "
        "hard rules are effectively prohibited rather than priced -- the study's whole "
        "premise. Check for a feasibility gate on acceptance."
    )


def test_raising_the_price_of_a_rule_buys_legality_back(scenarios):
    """The other end of the sweep: the weight axis has to actually move the outcome.

    Without this, a study reporting an illegality *rate by weight* could be reporting one
    number five times. It asserts direction rather than a threshold -- where the crossover
    sits is a finding and belongs in the study, not in an assertion.
    """
    scenario = scenarios["headline/0"]
    kwargs = dict(evaluations=5_000, seed=7)

    cheap = anneal.anneal(
        scenario.instance, scenario.incumbent, hard_weight=1, **kwargs
    )
    dear = anneal.anneal(
        scenario.instance, scenario.incumbent, hard_weight=10_000_000, **kwargs
    )

    assert cheap.hard > 0
    assert dear.hard < cheap.hard
