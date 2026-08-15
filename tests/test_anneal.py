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

import json
import pathlib

import pytest

from benchmarks import anneal, suite
from benchmarks.anneal_study import summarise
from roster_replan.checker import check
from roster_replan.scoring import score

CASES = ["headline/0", "tight/0", "multi-absence/0"]

BENCHMARKS = pathlib.Path(__file__).parent.parent / "benchmarks"
ARTIFACTS = {
    "committed": BENCHMARKS / "anneal-results.json",
    "foreign8": BENCHMARKS / "anneal-results-foreign8.json",
}


@pytest.fixture(scope="module")
def artifacts():
    return {name: json.loads(path.read_text()) for name, path in ARTIFACTS.items()}


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


# --- The committed artifacts -----------------------------------------------------------
# `anneal-results.json` and its foreign twin are *evidence*, not machinery: nothing in the
# package reads them, so unlike `manifest.json` and `timings.json` no existing layer notices
# when they go stale. That is a real gap -- `results.json` and `metrics.json` have it too --
# and these tests close it for this study at the cost of no solver time.
#
# What they cannot do is re-solve. A model change that moved the underlying numbers is only
# caught by rerunning `benchmarks.anneal_study`, and these tests are deliberately not a
# substitute for that. What they catch is the cheaper and likelier drift: a summariser whose
# meaning changed under a file nobody regenerated, a renamed field, and a study document
# whose headline no longer describes the data it cites.


@pytest.mark.parametrize("name", sorted(ARTIFACTS))
def test_the_stored_summary_regenerates_from_its_own_cases(name, artifacts):
    """The summary must still be what `summarise` derives from the rows beneath it.

    This is the exact defect this study shipped and caught by hand: `summarise` first led
    with violations the search *introduced* rather than violations the roster *carries*, so a
    run that returned the damaged incumbent untouched scored as clean. Both readings compute,
    both look plausible in a table, and the file cannot say which one produced it.
    """
    stored = artifacts[name]
    assert stored["summary"] == summarise(stored["cases"]), (
        f"{ARTIFACTS[name].name} carries a summary its own case rows no longer produce. "
        "`summarise` changed meaning without the artifact being regenerated -- rerun "
        "`python -m benchmarks.anneal_study` and reread docs/studies/penalty-search.md, "
        "because the numbers quoted there came from the stored version."
    )


@pytest.mark.parametrize("name", sorted(ARTIFACTS))
def test_every_run_carries_the_fields_the_study_reads(name, artifacts):
    """A renamed field would make `summarise` silently miscount rather than fail."""
    required = {
        "hard_weight",
        "evaluations",
        "seed",
        "hard",
        "introduced",
        "total",
        "shortfall",
        "disruption",
        "beats_optimum",
        "accepted_illegal",
    }
    for case in artifacts[name]["cases"]:
        for run in case["runs"]:
            missing = required - set(run)
            assert not missing, f"{case['case']} run is missing {sorted(missing)}"


def test_the_committed_set_still_says_what_the_study_says_it_says(artifacts):
    """The three claims `penalty-search.md` leads with, asserted against the data.

    Tied together rather than split, because they are one argument: cheap weights are unsafe
    *and* score well, and a dear weight is safe here. If a rerun moves any of them the study
    is out of date, which is the thing worth being told.
    """
    rows = {(r["hard_weight"], r["evaluations"]): r for r in artifacts["committed"]["summary"]}

    cheap = rows[(1, 100_000)]
    assert cheap["illegal"] == cheap["runs"] == 14, "study: every case illegal at weight 1"
    assert cheap["left_unrepaired"] == 10, (
        "study: ten of the fourteen introduced no new violation -- they returned the damaged "
        "incumbent untouched, which is the quiet failure the study leads on"
    )
    assert cheap["illegal_and_better_scoring"] == 13, (
        "study: 13 of 14 illegal rosters outscore the proven optimum on the shared yardstick"
    )

    tuned = rows[(1_000_000, 100_000)]
    assert tuned["illegal"] == 0 and tuned["matched_optimum"] == 11, (
        "study: at weight 1e6 and 100k evaluations the search is 0/14 illegal and matches "
        "the optimum on 11 of 14 -- the result that would falsify D-002's strong form if the "
        "committed set were the only evidence"
    )


def test_no_setting_on_instance_8_is_both_legal_and_fully_staffed(artifacts):
    """The study's central claim, and the one the whole item was built to test.

    Stated as the absence of a counter-example rather than as a table of numbers, so it stays
    true under a rerun that shifts the figures without changing the shape -- and fails loudly
    if some weight ever does find a legal, fully staffed roster.
    """
    case = artifacts["foreign8"]["cases"][0]

    assert case["exact"]["hard"] == 0 and case["exact"]["shortfall"] == 0, (
        "the exact reference on instance 8 must itself be legal and fully staffed, or there "
        "is nothing to compare against"
    )

    workable = [
        run for run in case["runs"] if run["hard"] == 0 and run["shortfall"] == 0
    ]
    assert not workable, (
        "a penalty weight produced a legal, fully staffed roster on instance 8. That is the "
        "counter-example docs/studies/penalty-search.md says does not exist, and D-128 rests "
        f"on it: {[(r['hard_weight'], r['evaluations']) for r in workable]}"
    )

    # The mechanism, not just the outcome: cheap weights break rules, dear ones leave holes.
    cheap = [r for r in case["runs"] if r["hard_weight"] <= 10_000]
    dear = [r for r in case["runs"] if r["hard_weight"] >= 1_000_000]
    assert all(r["hard"] > 0 for r in cheap), "study: every cheap weight breaks a rule"
    assert all(r["shortfall"] > 0 for r in dear), (
        "study: dear weights buy legality by refusing to staff, through R-COVER's soft floor"
    )
