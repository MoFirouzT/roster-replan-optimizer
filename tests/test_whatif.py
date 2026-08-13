"""`what_if`, and the two properties that decide whether its answer can be trusted.

**It must refuse an unlawful hypothetical rather than answer it.** A tool that replies *yes,
hire nobody, just shorten the rest gap* is the most dangerous output in this repo: it is
specific, actionable, and illegal. `validation.py` already knows that a statutory parameter
needs a recorded derogation basis, so the variant is validated before it is solved and a
rejection is returned as the answer.

**The comparison must be paired.** Baseline and variant are solved from the same incumbent
with the same seed, so a difference in disruption is the change's doing rather than the
search's — the discipline `lab.py` applies to timings, applied to outcomes.

The headline test is `test_hiring_the_scarce_skill_helps_and_headcount_alone_does_not`,
because it is the answer a planner would act on and the one a naive tool gets wrong: on a
tenant short of a skill, adding a body changes nothing at all.
"""

from __future__ import annotations

import pytest

from benchmarks import suite
from roster_replan import whatif
from roster_replan.model import solve
from roster_replan.scoring import disruption_of

SCARCE = "kitchen"


@pytest.fixture(scope="module")
def scarce_tenant():
    return suite.build("scarce-skill/0").instance


@pytest.fixture(scope="module")
def headline():
    return suite.build("headline/0").instance


# --- The answer a planner would act on ----------------------------------------------


def test_hiring_the_scarce_skill_helps_and_headcount_alone_does_not(scarce_tenant):
    """The distinction the explainer already reports, confirmed by solving.

    `explain` says 9 of 12 lack the required skill on the short slot. So a body without it
    is not a solution, and a tool that answered "hire someone" without qualifying it would be
    giving expensive, useless advice.
    """
    skilled = whatif.compare(
        scarce_tenant,
        (
            whatif.Change(
                kind=whatif.ADD_EMPLOYEE,
                skills=(SCARCE,),
                contract="flexi",
                weekly_hours=24.0,
                daily_hours=8.0,
            ),
        ),
    )
    unskilled = whatif.compare(
        scarce_tenant,
        (
            whatif.Change(
                kind=whatif.ADD_EMPLOYEE,
                skills=(),
                contract="salaried",
                weekly_hours=38.0,
                daily_hours=8.0,
            ),
        ),
    )

    assert skilled.shortfall_delta < 0, "a skilled hire should fill at least one position"
    assert unskilled.shortfall_delta == 0, (
        "an unskilled hire cannot fill a slot that needs the skill, and the tool must not "
        "suggest otherwise"
    )


def test_raising_hours_is_reported_without_being_recommended(scarce_tenant):
    """A change that helps is reported as helping; the tool takes no position on whether it
    is a good idea. Whether staff want more hours is not something a solver knows."""
    comparison = whatif.compare(
        scarce_tenant,
        (whatif.Change(kind=whatif.SET_WEEKLY_HOURS, weekly_hours=48.0),),
    )
    assert not comparison.refused
    assert comparison.shortfall_delta <= 0


# --- Refusal ------------------------------------------------------------------------


def test_an_unlawful_relaxation_is_refused_not_answered(scarce_tenant):
    comparison = whatif.compare(
        scarce_tenant,
        (whatif.Change(kind=whatif.RELAX_RULE, min_rest_hours=8.0),),
    )

    assert comparison.refused
    assert comparison.variant is None
    assert any("derogation" in d.message for d in comparison.defects)
    assert "Refused" in comparison.summary()


def test_the_same_relaxation_is_answered_when_a_basis_is_recorded(scarce_tenant):
    """The rule is *recorded basis*, not *never*. A derogation is lawful and the tool must
    let a planner explore one — refusing outright would make it useless for the case it
    exists to serve."""
    comparison = whatif.compare(
        scarce_tenant,
        (
            whatif.Change(
                kind=whatif.RELAX_RULE,
                min_rest_hours=8.0,
                derogation_basis=(("min_rest_hours", "PC 302 CBA art. 4"),),
            ),
        ),
    )

    assert not comparison.refused, [d.message for d in comparison.defects]
    assert comparison.variant is not None


def test_an_unknown_change_is_rejected(scarce_tenant):
    """A closed set of kinds is the point: a tool an LLM can call will be called with
    something unexpected, and a free-form patch endpoint is an arbitrary-edit hole."""
    with pytest.raises(ValueError, match="unknown change kind"):
        whatif.apply(scarce_tenant, whatif.Change(kind="drop_all_rules"))


# --- The comparison itself ----------------------------------------------------------


@pytest.mark.parametrize("seed", [7, 8, 9, 11, 13])
def test_the_baseline_is_the_instance_as_it_stands(seed):
    """Paired: the baseline must be the solve a caller would get without asking a
    hypothetical, at the seed they asked for.

    Asserted on `changes_from_incumbent` and swept across seeds, because **disruption is the
    wrong quantity to check this with**: the optimum is unique on this distribution, so a
    baseline computed at the wrong seed scores identically and the mutation harness proved
    the obvious test toothless. The *roster* does move with the seed where ties exist —
    `large/0` yields two distinct optima across five seeds (`D-080`) — so a roster-level
    property is what can see the difference.
    """
    instance = suite.build("large/0").instance
    comparison = whatif.compare(
        instance,
        (whatif.Change(kind=whatif.SET_WEEKLY_HOURS, weekly_hours=40.0),),
        seed=seed,
    )
    direct = solve(instance, seed=seed, time_limit=30.0)

    assert comparison.baseline.disruption == disruption_of(direct.roster, instance)
    assert comparison.baseline.changes_from_incumbent == len(
        direct.roster ^ (instance.incumbent or frozenset())
    )
    # The roster is the only field that can see a wrong seed: seeds 7 and 8 reach two
    # different optima here with identical objectives and identical change counts.
    assert comparison.baseline.roster == direct.roster


def test_the_incumbent_is_held_across_both_sides(headline):
    """Disruption is measured against the published roster, so a variant solved from a
    different incumbent would produce a delta that means nothing."""
    change = whatif.Change(
        kind=whatif.ADD_EMPLOYEE, skills=(SCARCE,), weekly_hours=24.0, daily_hours=8.0
    )
    variant = whatif.apply(headline, change)

    assert variant.incumbent == headline.incumbent
    assert variant.now == headline.now
    assert variant.published_through == headline.published_through


def test_a_change_that_does_nothing_says_so(headline):
    comparison = whatif.compare(
        headline,
        (
            whatif.Change(
                kind=whatif.SET_REQUIRED,
                day=headline.open_shifts[0].day,
                shift=headline.open_shifts[0].shift,
                required=headline.open_shifts[0].required,
            ),
        ),
    )
    assert comparison.shortfall_delta == 0
    assert "changes nothing" in comparison.summary()


def test_the_comparison_is_reproducible(scarce_tenant):
    change = whatif.Change(
        kind=whatif.ADD_EMPLOYEE, skills=(SCARCE,), weekly_hours=24.0, daily_hours=8.0
    )
    first = whatif.compare(scarce_tenant, (change,), seed=11)
    second = whatif.compare(scarce_tenant, (change,), seed=11)

    assert first.shortfall_delta == second.shortfall_delta
    assert first.disruption_delta == second.disruption_delta


def test_changes_compose_in_order(scarce_tenant):
    """Two hires are two hires, not one applied twice."""
    hire = whatif.Change(
        kind=whatif.ADD_EMPLOYEE, skills=(SCARCE,), weekly_hours=24.0, daily_hours=8.0
    )
    twice = whatif.apply(whatif.apply(scarce_tenant, hire), hire)

    assert len(twice.employees) == len(scarce_tenant.employees) + 2
    assert len({p.name for p in twice.employees}) == len(twice.employees)
