"""Profile review: contradictions, inert rules, and the probe.

`guide/configuring.md` puts the LLM in stage 1 only and says the rest must work without it.
These are stages 3 and 4, so every test here runs with no model available — which is the
property being asserted as much as the logic.

Three things are worth holding to:

**A contradiction is about the profile, not about a week.** `min_period_hours` above every
shift's length means no shift is legal for anyone, whatever workforce arrives. Catching that
needs no solver and no employees, and catching it at configuration time is the difference
between a clear message and an unexplained empty roster at 09:00 on a Saturday.

**An inert rule is reported and not rejected.** `max_consecutive_days` of 9 over seven days
forbids nothing. The profile is valid; the tenant merely believes a protection is in force
that is not, and nothing else in the system will ever tell them.

**Enabling an unencoded rule is a defect, not a courtesy.** The five profile-gated rules are
declared in the registry and none is encoded. Accepting one silently would promise
enforcement that never happens — the failure `guide/rules.md` exists to prevent, arriving through
configuration instead of through documentation.
"""

from __future__ import annotations

import dataclasses

import pytest

from benchmarks import suite
from roster_replan import profile as P
from roster_replan.domain import Fairness, ShiftType


@pytest.fixture(scope="module")
def sample():
    return suite.build("headline/3").instance


@pytest.fixture
def shipped(sample):
    return P.Profile(
        version="horeca-2026.1",
        shift_types=sample.shift_types,
        params=sample.params,
        disruption=sample.disruption,
    )


def _with_params(profile: P.Profile, **changes) -> P.Profile:
    return dataclasses.replace(
        profile, params=dataclasses.replace(profile.params, **changes)
    )


# --- The shipped profile ------------------------------------------------------------


def test_the_shipped_profile_has_no_contradictions(shipped):
    assert P.contradictions(shipped) == []


def test_the_shipped_profile_probes_clean_enough_to_save(shipped, sample):
    """Clean means solvable, not fully staffed. The headline case is a sick call, so a
    shortfall is the correct outcome and must not be read as a configuration fault."""
    result = P.probe(shipped, sample)
    assert result.solved
    assert result.defects == ()


# --- Contradictions -----------------------------------------------------------------


def test_a_minimum_shift_longer_than_every_shift_is_a_contradiction(shipped):
    broken = _with_params(shipped, min_period_hours=12.0)
    defects = P.contradictions(broken)

    assert defects, "no shift in an 8h catalogue can satisfy a 12h minimum"
    assert any("no shift is legal" in d.message for d in defects)


def test_that_contradiction_is_reported_once(shipped):
    """Both the longest and the shortest shift breach a 12h minimum, but that is one fault.
    Two messages read as two problems and send the reader looking for a second fix."""
    defects = P.contradictions(_with_params(shipped, min_period_hours=12.0))
    assert len(defects) == 1, [d.message for d in defects]


def test_a_shift_shorter_than_the_minimum_is_reported_when_others_are_legal(shipped):
    """The other side of the same check: some shifts legal, one not."""
    mixed = dataclasses.replace(
        shipped,
        shift_types=shipped.shift_types
        + (ShiftType(label="X", start_hour=9.0, span_hours=2.0, break_hours=0.0),),
    )
    defects = P.contradictions(_with_params(mixed, min_period_hours=3.0))

    assert any("never be staffed" in d.message for d in defects)


def test_weekly_rest_wider_than_the_horizon_is_a_contradiction(shipped):
    defects = P.contradictions(_with_params(shipped, min_weekly_rest_hours=7 * 24.0))
    assert any("nobody can ever work" in d.message for d in defects)


def test_a_daily_rest_gap_contradicts_allowing_consecutive_days(shipped):
    defects = P.contradictions(
        _with_params(shipped, min_rest_hours=26.0, max_consecutive_days=5)
    )
    assert any("two days running" in d.message for d in defects)


def test_a_zero_consecutive_day_limit_forbids_working(shipped):
    defects = P.contradictions(_with_params(shipped, max_consecutive_days=0))
    assert any("forbids working at all" in d.message for d in defects)


@pytest.mark.parametrize("rule", P.OPTIONAL_RULES)
def test_enabling_an_unencoded_optional_rule_is_refused(shipped, rule):
    profile = dataclasses.replace(shipped, enabled_optional_rules=frozenset({rule}))
    defects = P.contradictions(profile)

    assert any("not encoded" in d.message for d in defects), (
        f"{rule} is in the registry and not in the model; enabling it promises enforcement "
        f"that does not happen"
    )


def test_an_unknown_optional_rule_is_refused(shipped):
    profile = dataclasses.replace(shipped, enabled_optional_rules=frozenset({"R-INVENTED"}))
    assert any("unknown optional rules" in d.message for d in P.contradictions(profile))


# --- Inert rules --------------------------------------------------------------------


def test_a_consecutive_day_limit_beyond_the_horizon_is_reported_as_inert(shipped):
    notes = P.remarks(_with_params(shipped, max_consecutive_days=9))
    assert any("forbids nothing" in note.message for note in notes)


def test_an_inert_rule_is_not_a_defect(shipped):
    """The profile is valid. The tenant may have meant it, and rejecting would be wrong."""
    inert = _with_params(shipped, max_consecutive_days=9)
    assert P.contradictions(inert) == []
    assert P.remarks(inert)


def test_a_declared_but_inert_fairness_term_is_reported(shipped):
    """Three ways to switch fairness off while the object looks configured (`D-108`), and a
    tenant who set two of the three should be told which one is missing."""
    for fairness, missing in (
        (Fairness(weight=0, unpopular_shifts=frozenset({1}), tiers=4), "weight"),
        (Fairness(weight=20, unpopular_shifts=frozenset(), tiers=4), "unpopular_shifts"),
        (Fairness(weight=20, unpopular_shifts=frozenset({1}), tiers=0), "tiers"),
    ):
        notes = P.remarks(dataclasses.replace(shipped, fairness=fairness))
        assert any(n.field == "fairness" and missing in n.message for n in notes), missing


def test_a_declared_fairness_term_that_works_draws_no_remark(shipped):
    """The other direction, so the remark above is not merely always true."""
    working = Fairness(weight=20, unpopular_shifts=frozenset({1}), tiers=4)
    notes = P.remarks(dataclasses.replace(shipped, fairness=working))
    assert not any(n.field == "fairness" for n in notes)


def test_priors_past_the_tiers_are_reported_as_flat(shipped, sample):
    """`internals/model.md`'s stated limit, now checked rather than asserted (`D-131`).

    `g` is convex only up to `tiers`; past that its marginal cost is constant, so a window
    long enough to push the workforce past it switches fairness off while appearing to be
    configured. This needs a workforce and not just a profile, which is why `remarks` takes
    an optional sample.
    """
    profile = dataclasses.replace(
        shipped, fairness=Fairness(weight=20, unpopular_shifts=frozenset({1}), tiers=3)
    )
    loaded = dataclasses.replace(
        sample,
        employees=tuple(
            dataclasses.replace(person, unpopular_shifts_before_horizon=5)
            for person in sample.employees
        ),
    )

    notes = P.remarks(profile, sample=loaded)
    assert any(n.field == "fairness.tiers" and "every employee" in n.message for n in notes)

    # A workforce that has not spent its window past the tiers draws nothing, and neither
    # does the same profile with no sample to judge it against.
    assert not any(n.field == "fairness.tiers" for n in P.remarks(profile, sample=sample))
    assert not any(n.field == "fairness.tiers" for n in P.remarks(profile))


def test_a_switched_off_cost_weight_is_reported(shipped):
    """`cost_weight` ships at 0 (`D-050`), which is deliberate and worth saying out loud:
    a tenant reading their profile should know cost is not being traded at all."""
    assert any(n.field == "disruption.cost_weight" for n in P.remarks(shipped))


# --- The probe ----------------------------------------------------------------------


def test_the_probe_is_skipped_when_the_profile_contradicts_itself(shipped, sample):
    """Solving parameters that cannot all hold produces an infeasibility whose real cause is
    the profile, reported as though it were about the week."""
    broken = _with_params(shipped, min_period_hours=12.0)
    defects, _, result = P.review(broken, sample)

    assert defects
    assert result is None


def test_the_probe_reports_the_rules_that_blocked_staffing(shipped, sample):
    """Rejection returns through the explainer, as `guide/configuring.md` asks, so a config
    error and a Saturday-morning shortfall are described by the same machinery."""
    result = P.probe(shipped, sample)
    assert result.blocking
    assert all(rule.startswith("R-") for rule in result.blocking)


def test_an_unlawful_profile_is_caught_by_the_probe_not_the_solver(shipped, sample):
    """Stage 2 runs inside the probe: a derogation with no recorded basis is rejected before
    anything is solved."""
    unlawful = _with_params(shipped, min_rest_hours=8.0)
    result = P.probe(unlawful, sample)

    assert not result.solved
    assert any("derogation" in d.message for d in result.defects)


def test_a_profile_applied_to_a_week_replaces_only_policy(shipped, sample):
    """The profile owns policy, not the week: employees, demand and the incumbent are the
    caller's and must survive untouched."""
    applied = shipped.applied_to(sample)

    assert applied.employees == sample.employees
    assert applied.open_shifts == sample.open_shifts
    assert applied.incumbent == sample.incumbent
    assert applied.params == shipped.params
    assert applied.disruption == shipped.disruption


def test_a_profile_carries_its_fairness_declaration_onto_the_week(shipped, sample):
    """`internals/model.md` has said since `D-108` that the profile names the unpopular shifts. It
    could not: `Profile` had no field for them, so the term was reachable only by building an
    `Instance` by hand (`D-131`).

    The set is indices into `shift_types`, which is why it belongs beside the catalogue and
    not on the request.
    """
    fairness = Fairness(weight=20, unpopular_shifts=frozenset({1}), tiers=4)
    applied = dataclasses.replace(shipped, fairness=fairness).applied_to(sample)

    assert applied.fairness == fairness
    # And a profile declaring none says so, on the same footing as `disruption`: policy is
    # the profile's, so an instance cannot smuggle a term past it.
    assert shipped.applied_to(dataclasses.replace(sample, fairness=fairness)).fairness is None


def test_review_runs_without_a_sample(shipped):
    """Deterministic editing has to work with nothing but the profile — no week, no solver,
    no model."""
    defects, notes, result = P.review(shipped)
    assert defects == []
    assert notes
    assert result is None
