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
from roster_replan import explain as explain_module
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


def test_ignoring_one_blocked_employees_missing_skill_fills_the_slot(scarce_tenant):
    """The per-employee counterpart to hiring: `explain().by_employee()` can point at the
    person blocked by fewest rules, and this is how a planner tests overriding just them
    instead of the whole roster. Picking someone blocked by R-SKILL *alone* means ignoring
    that one requirement must clear every blocker they have, so the shortfall must strictly
    fall — a weaker `<=` would also pass if `IGNORE_SKILL` silently did nothing. Nothing
    about the employee's real record changes: `apply` returns a throwaway instance."""
    solved = solve(scarce_tenant, seed=7, time_limit=30.0)
    shortfall = next(s for s in explain_module.explain(solved.roster, scarce_tenant) if s.short)
    # `by_employee()` ranks by count alone, so a tie can land on someone blocked solely by an
    # unrelated rule (e.g. R-MAX-WEEKLY). Narrow to R-SKILL specifically: that is the one
    # blocker `IGNORE_SKILL` can actually clear.
    solo_skill_blocked = [
        b.employee for b in shortfall.blocked if b.rules == ("R-SKILL",)
    ]
    assert solo_skill_blocked, shortfall.blocked
    employee = solo_skill_blocked[0]

    comparison = whatif.compare(
        scarce_tenant,
        (whatif.Change(kind=whatif.IGNORE_SKILL, employee=employee, skills=(SCARCE,)),),
    )

    assert not comparison.refused
    assert comparison.shortfall_delta < 0


def test_raising_one_employees_daily_hours_is_reported_without_being_recommended(scarce_tenant):
    comparison = whatif.compare(
        scarce_tenant,
        (whatif.Change(kind=whatif.SET_DAILY_HOURS, employee=0, daily_hours=12.0),),
    )
    assert not comparison.refused
    assert comparison.shortfall_delta <= 0


def test_ignore_skill_without_an_employee_is_rejected(scarce_tenant):
    with pytest.raises(ValueError, match="ignore_skill requires an employee"):
        whatif.apply(scarce_tenant, whatif.Change(kind=whatif.IGNORE_SKILL, skills=(SCARCE,)))


# --- Recommending, without touching anything -----------------------------------------


def test_recommend_does_not_touch_the_real_instance(scarce_tenant):
    """`recommend` only ever solves throwaway copies (`apply` returns a new instance via
    `dataclasses.replace`), so the real employees and their real record must be exactly what
    they were before it ran."""
    solved = solve(scarce_tenant, seed=7, time_limit=30.0)
    before = scarce_tenant.employees
    shortfall = next(s for s in explain_module.explain(solved.roster, scarce_tenant) if s.short)

    recommendations = whatif.recommend(scarce_tenant, shortfall, seed=7, time_limit=30.0)

    assert recommendations
    assert scarce_tenant.employees == before


def test_recommend_only_names_candidates_confirmed_to_close_the_shortfall(scarce_tenant):
    """A candidate whose single override does not actually clear the shift — because the
    solver has something else to say about it once re-optimized — must not be reported, so
    each recommendation is re-applied and re-solved here as the independent check."""
    solved = solve(scarce_tenant, seed=7, time_limit=30.0)
    shortfall = next(s for s in explain_module.explain(solved.roster, scarce_tenant) if s.short)
    by_employee = {b.employee: b.rules[0] for b in shortfall.blocked if len(b.rules) == 1}
    shift_type = scarce_tenant.shift_types[shortfall.shift]

    recommendations = whatif.recommend(scarce_tenant, shortfall, seed=7, time_limit=30.0)
    assert recommendations

    for rec in recommendations:
        rule = by_employee[rec.employee]
        employee = scarce_tenant.employees[rec.employee]
        if rule == "R-SKILL":
            change = whatif.Change(
                kind=whatif.IGNORE_SKILL, employee=rec.employee, skills=(SCARCE,)
            )
        elif rule == "R-MAX-WEEKLY":
            change = whatif.Change(
                kind=whatif.SET_WEEKLY_HOURS,
                employee=rec.employee,
                weekly_hours=(employee.max_hours_this_week or 0.0) + shift_type.span_hours,
            )
        else:
            change = whatif.Change(
                kind=whatif.SET_DAILY_HOURS,
                employee=rec.employee,
                daily_hours=(employee.max_daily_hours or 0.0) + shift_type.span_hours,
            )
        comparison = whatif.compare(scarce_tenant, (change,), seed=7, time_limit=30.0)
        assert comparison.shortfall_delta < 0, rec


def test_recommend_is_sorted_cheapest_first_within_a_provenance(scarce_tenant):
    """Cheapest-first inside each group, operational before statutory, and never
    interleaved: a statutory relaxation must not outrank an operational one because it
    scored a few points lower. Disruption cannot order two asks of different kinds."""
    solved = solve(scarce_tenant, seed=7, time_limit=30.0)
    shortfall = next(s for s in explain_module.explain(solved.roster, scarce_tenant) if s.short)

    recommendations = whatif.recommend(scarce_tenant, shortfall, seed=7, time_limit=30.0)

    groups = [r.provenance for r in recommendations]
    assert groups == sorted(groups, key=lambda p: p != "operational")
    for provenance in set(groups):
        deltas = [r.disruption_delta for r in recommendations if r.provenance == provenance]
        assert deltas == sorted(deltas)


def test_recommend_solves_the_unchanged_instance_once(scarce_tenant, monkeypatch):
    """The baseline does not depend on which override is being tested, so N candidates cost
    N+1 solves, not 2N. Guards the reuse against a later edit quietly restoring the pairing
    per candidate."""
    solved = solve(scarce_tenant, seed=7, time_limit=30.0)
    shortfall = next(s for s in explain_module.explain(solved.roster, scarce_tenant) if s.short)
    candidates = sum(1 for b in shortfall.blocked if len(b.rules) == 1)

    solves, tested = 0, 0
    real_solve, real_compare = whatif.solve, whatif.compare

    def counted_solve(*args, **kwargs):
        nonlocal solves
        solves += 1
        return real_solve(*args, **kwargs)

    def counted_compare(*args, **kwargs):
        nonlocal tested
        tested += 1
        return real_compare(*args, **kwargs)

    monkeypatch.setattr(whatif, "solve", counted_solve)
    monkeypatch.setattr(whatif, "compare", counted_compare)
    whatif.recommend(scarce_tenant, shortfall, seed=7, time_limit=30.0)

    # One baseline plus one variant each, not a baseline and a variant each. `tested` is at
    # most `candidates` — a single-blocker person whose rule has no `Change` kind is skipped
    # before any solving — so the second assertion is what pins the reuse.
    assert 0 < tested <= candidates
    assert solves == tested + 1


def test_recommend_tests_no_more_than_max_candidates(scarce_tenant, monkeypatch):
    """An uncapped sweep is a solve per blocked person; the cap bounds the work by a number
    the caller sets rather than by the tenant's headcount."""
    solved = solve(scarce_tenant, seed=7, time_limit=30.0)
    shortfall = next(s for s in explain_module.explain(solved.roster, scarce_tenant) if s.short)

    tested = 0
    real = whatif.compare

    def counted(*args, **kwargs):
        nonlocal tested
        tested += 1
        return real(*args, **kwargs)

    monkeypatch.setattr(whatif, "compare", counted)
    whatif.recommend(scarce_tenant, shortfall, seed=7, time_limit=30.0, max_candidates=1)

    assert tested == 1


def test_recommend_reports_the_rule_and_its_provenance(scarce_tenant):
    """The number alone does not say what kind of ask it prices, so every recommendation
    carries the rule it would relax and where that rule's authority comes from."""
    solved = solve(scarce_tenant, seed=7, time_limit=30.0)
    shortfall = next(s for s in explain_module.explain(solved.roster, scarce_tenant) if s.short)

    recommendations = whatif.recommend(scarce_tenant, shortfall, seed=7, time_limit=30.0)

    assert recommendations
    for rec in recommendations:
        assert rec.provenance == whatif._PROVENANCE[rec.rule]
        assert rec.provenance in {"operational", "statutory"}


def test_recommend_drops_a_candidate_that_does_not_actually_close_the_shortfall(
    scarce_tenant, monkeypatch
):
    """A rule count of one is only a hint (`explain.py`'s own caveat); the solver might still
    leave the shift short once re-optimized around the rest of the roster. `recommend` must
    not report that candidate just because it was the cheapest-looking one."""
    from roster_replan.explain import Blocked, Shortfall

    shortfall = Shortfall(
        day=0,
        shift=0,
        required=1,
        assigned=0,
        blocked=(Blocked(employee=0, rules=("R-SKILL",)),),
        unexplained=(),
    )

    def fake_compare(instance, changes, *, seed=7, time_limit=30.0, baseline=None):
        return whatif.Comparison(
            described=("stub",),
            baseline=whatif.Outcome(0, 0, 0, (), frozenset()),
            variant=whatif.Outcome(0, 0, 0, (), frozenset()),
        )

    monkeypatch.setattr(whatif, "compare", fake_compare)
    assert whatif.recommend(scarce_tenant, shortfall) == ()


def test_recommend_skips_a_person_blocked_by_more_than_one_rule():
    from roster_replan.explain import Blocked, Shortfall

    shortfall = Shortfall(
        day=0,
        shift=0,
        required=1,
        assigned=0,
        blocked=(Blocked(employee=0, rules=("R-SKILL", "R-MAX-WEEKLY")),),
        unexplained=(),
    )
    instance = suite.build("scarce-skill/0").instance

    assert whatif.recommend(instance, shortfall) == ()


def test_recommend_never_tests_a_multiply_blocked_person(scarce_tenant, monkeypatch):
    """Relaxing one of two blockers cannot free them (`explain.py`'s own reasoning), so a
    multiply-blocked person must not even be tested — testing them anyway would be reporting
    a rule count of one for someone actually blocked by two."""
    from roster_replan.explain import Blocked, Shortfall

    shortfall = Shortfall(
        day=0,
        shift=0,
        required=1,
        assigned=0,
        blocked=(Blocked(employee=0, rules=("R-SKILL", "R-MAX-WEEKLY")),),
        unexplained=(),
    )

    def fail_if_called(*args, **kwargs):
        raise AssertionError("recommend must not test a multiply-blocked candidate")

    monkeypatch.setattr(whatif, "compare", fail_if_called)
    assert whatif.recommend(scarce_tenant, shortfall) == ()


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

    **This test has now been strengthened twice, by the same harness, for the same reason.**
    It first checked `disruption`, and the mutation harness proved that toothless because a
    baseline at the wrong seed scores identically. It moved to `changes_from_incumbent`,
    which worked only because the roster moved with the seed where ties existed —
    `large/0` yielded two distinct optima across five seeds (`D-080`). `D-119` then removed
    every tie on purpose, and with it the last observable difference a wrong seed makes.

    So it stops inferring the seed from the answer and asserts it where it is used
    (`D-124`). A roster is the same at every seed now, by design; what must still be true is
    that the baseline is measured at the seed the caller asked for.
    """
    instance = suite.build("large/0").instance

    seen: list[int] = []
    original = whatif._measure

    def spy(measured, *, seed, time_limit):
        seen.append(seed)
        return original(measured, seed=seed, time_limit=time_limit)

    whatif._measure = spy
    try:
        comparison = whatif.compare(
            instance,
            (whatif.Change(kind=whatif.SET_WEEKLY_HOURS, weekly_hours=40.0),),
            seed=seed,
        )
    finally:
        whatif._measure = original

    assert seen, "no measurement was taken at all"
    assert set(seen) == {seed}, (
        f"a hypothetical asked at seed {seed} measured at {sorted(set(seen))}; baseline and "
        f"variant must be solved under the same conditions or the comparison is not paired"
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
