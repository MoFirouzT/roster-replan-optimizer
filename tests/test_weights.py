"""Weight identifiability: the probe has to be able to see a weight before a null means one.

`benchmarks/weights.py` reports that **no D2 weight moves the roster on any committed case**.
A measurement like that is worthless unless the thing doing the measuring can detect the
effect when it is present, so the load-bearing test here is not the null — it is
`forced_choice`, an instance built to present the choice, where the roster *must* follow the
weights. That is the same structure `test_studies.py` uses for symmetry
(`test_the_symmetric_family_actually_contains_symmetry`), and for the same reason: it
separates "this lever does nothing" from "this distribution never offers the lever a choice".

The second group asserts what recovery can and cannot return. Scale-equivalent weight
vectors produce identical rosters by construction, so an estimator that ever reported a
point estimate of a weight would be reporting its prior.
"""

from __future__ import annotations

import dataclasses

import pytest

from benchmarks import suite, weights
from roster_replan.checker import check
from roster_replan.model import solve

MULTIPLIERS = (1, 2, 3, 4, 5, 6, 8, 10, 12, 16, 20, 30, 50)


def test_the_forced_choice_instance_actually_forces_a_choice():
    """The probe's validity. Without this, the committed-set null proves nothing.

    Two holes, one filler, so the shortfall term cancels and the disruption weights are the
    only thing left to decide which hole stays open. If moving `published_weight` against
    `draft_weight` stops moving the roster here, `weights.py` has lost the ability to detect
    an identifiable weight and every null it reports is vacuous.
    """
    cheap_drafts = weights.forced_choice(published_weight=10, draft_weight=1)
    cheap_published = weights.forced_choice(published_weight=1, draft_weight=10)

    first = solve(cheap_drafts, seed=7, time_limit=30.0)
    second = solve(cheap_published, seed=7, time_limit=30.0)

    assert first.roster != second.roster, (
        "the instance built to make the weights decide no longer does -- weights.py can no "
        "longer tell an unidentifiable weight from an undetectable one"
    )
    assert sorted(d for _, d, _ in first.roster) == [5]
    assert sorted(d for _, d, _ in second.roster) == [2]


def test_both_answers_to_the_forced_choice_are_legal_and_equally_short():
    """The choice must be between two lawful rosters, or the weights are not what decided it.

    If one branch were illegal or shorter-staffed, the hard rules or the shortfall term would
    be doing the choosing and the instance would measure those instead.
    """
    for published, draft in [(10, 1), (1, 10)]:
        instance = weights.forced_choice(published_weight=published, draft_weight=draft)
        roster = solve(instance, seed=7, time_limit=30.0).roster

        assert not [v for v in check(roster, instance) if not v.soft]
        assert len(roster) == 1, "exactly one of the two holes must stay open"


@pytest.mark.parametrize("weight", sorted(weights.D2_SWEEPS))
def test_no_d2_weight_moves_the_roster_on_the_committed_set(weight):
    """The finding, guarded. `D-129` rests on this being reproducible rather than a run.

    Asserted on one case rather than all fourteen so the suite stays fast; the study carries
    the full grid. A failure here does not mean the study is wrong -- it means the
    distribution moved and the study needs rerunning before it is quoted again.
    """
    scenario = suite.build("headline/0")
    row = weights.sweep_one(scenario, weight, weights.D2_SWEEPS[weight])

    assert not weights.identifiable(row), (
        f"{weight} now moves the roster on headline/0, across {row['values']}. That "
        "contradicts docs/studies/weight-recovery.md, which reports 0/14 for every D2 "
        f"weight -- rerun benchmarks.weights before citing it. Bands: {row['bands']}"
    )


def test_scale_equivalent_weights_are_indistinguishable_from_rosters():
    """Doubling every weight changes no roster, so no estimator can recover a magnitude.

    This is why `recover_ratio` returns an interval on a ratio and why the study reports no
    point estimate anywhere. It is a property of the objective, not a limit of the effort.
    """
    seen = {
        (published, draft): weights.observe(
            8, published_weight=published, draft_weight=draft
        )
        for published, draft in [(1, 10), (2, 20), (5, 50), (10, 100)]
    }

    assert len(set(seen.values())) == 1, (
        f"scale-equivalent weight vectors produced different rosters: {seen}. Either the "
        "objective acquired a term that is not homogeneous in the weights, or the solve is "
        "not returning the canonical optimum D-119 guarantees."
    )


@pytest.mark.parametrize(
    "published,draft", [(1, 10), (2, 20), (1, 1), (10, 1), (3, 30)]
)
def test_recovery_brackets_the_true_ratio(published, draft):
    """The estimator may return a wide answer; it may never return a wrong one."""
    recovered = weights.recover_ratio(
        published_weight=published, draft_weight=draft, multipliers=MULTIPLIERS
    )

    assert recovered["contains_truth"], (
        f"recovered {recovered['recovered']} excludes the true ratio "
        f"{recovered['true_ratio']}, from observations {recovered['observations']}"
    )


def test_recovery_never_sees_the_weights_it_is_recovering():
    """The estimator reads rosters. If it could read the profile the exercise is circular.

    Asserted by construction rather than by inspection: two runs whose true weights differ
    but whose *observations* are identical must return the same interval, which cannot
    happen if anything downstream of `observe` is consulting the profile.
    """
    first = weights.recover_ratio(
        published_weight=1, draft_weight=10, multipliers=MULTIPLIERS
    )
    second = weights.recover_ratio(
        published_weight=5, draft_weight=50, multipliers=MULTIPLIERS
    )

    assert first["observations"] == second["observations"]
    assert first["recovered"] == second["recovered"]
    assert first["true_ratio"] == second["true_ratio"] == 10.0


def test_the_event_weights_are_inert_under_the_shipped_metric():
    """D2 never reads `move_weight`; a tenant on D2 cannot have it learned at any sample size.

    Not a distribution fact like the rest of this file -- it follows from
    `scoring.disruption_of` routing D0-D2 through `_per_assignment`, which prices a slot and
    never looks at an event. Asserted so the study's claim about *why* stays true.
    """
    scenario = suite.build("headline/0")
    instance = scenario.instance
    base = instance.disruption

    rosters = set()
    for value in (1, 100):
        moved = dataclasses.replace(base, metric="D2", move_weight=value)
        solution = solve(
            dataclasses.replace(instance, disruption=moved), seed=7, time_limit=30.0
        )
        rosters.add(solution.roster)

    assert len(rosters) == 1, "move_weight changed a D2 roster, which D2 cannot read"
