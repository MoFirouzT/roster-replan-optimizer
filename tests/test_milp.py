"""The MILP formulation: a third reading, and the evidence behind `D-001`.

`D-001` was owed from T1 until the comparison existed, because the alternative was to
invent a rationale nobody had. This module is the comparison's correctness half — a timing
against a formulation that means something *else* is not a comparison, it is a coincidence.

So what is asserted here is equivalence, and the equivalence is strong: the MILP must reach
the **same optimal objective** as CP-SAT on every case it is run against, and its roster must
pass the same independent checker. That makes it a third reading of `rules.md` alongside the
model and the checker, and a disagreement between any two of the three is a real finding
about one of them.

Two refusals are asserted rather than worked around, because they are the substance of
`D-001` rather than gaps in the effort spent:

- **D3 and D4 cannot be stated.** They pair a drop with an add through `min(drops, adds)`,
  which is not linear. CP-SAT writes `add_min_equality`; MILP needs auxiliary binaries and
  big-M per (employee, day). The module raises rather than quietly comparing a different
  model.
- **The gates have no counterpart.** Every hard constraint in `model.py` carries an
  assumption literal so a failed solve can name the rule instances in conflict. MILP has no
  assumption mechanism, so `violations()` and the infeasibility core have nothing to compare
  against — which is most of why the slower solver is the one that ships.
"""

from __future__ import annotations

import dataclasses

import pytest

from benchmarks import metrics, milp, suite
from roster_replan.checker import check
from roster_replan.domain import SkillMixEntry
from roster_replan.model import exclusions, solve as cp_solve

CASES = ["headline/0", "tight/0", "small/0", "large/0", "scarce-skill/0", "multi-absence/0"]
BACKENDS = ["SCIP", "CBC"]


@pytest.fixture(scope="module")
def scenarios():
    return {case: suite.build(case) for case in CASES}


@pytest.mark.parametrize("case", CASES)
@pytest.mark.parametrize("backend", BACKENDS)
def test_the_milp_reaches_the_cp_sat_optimum(case, backend, scenarios):
    """The precondition for any timing in `studies/cp-sat-vs-milp.md` to mean anything."""
    instance = scenarios[case].instance
    reference = cp_solve(instance, time_limit=30.0)

    roster, objective, timing = milp.solve(instance, backend=backend, time_limit=30.0)

    assert timing["status"] == "OPTIMAL", f"{backend} did not prove optimality on {case}"
    assert objective == reference.objective, (
        f"{backend} on {case}: {objective} against CP-SAT's {reference.objective} -- "
        f"two formulations of one problem disagreeing about its optimum"
    )


@pytest.mark.parametrize("case", CASES)
def test_the_milp_roster_passes_the_independent_checker(case, scenarios):
    """A third reading of the rules, held to the same oracle as the other two."""
    instance = scenarios[case].instance
    roster, _, _ = milp.solve(instance, backend="SCIP", time_limit=30.0)

    hard = [v for v in check(roster, instance) if not v.soft]
    assert hard == [], f"the MILP returned an illegal roster on {case}: {hard}"


@pytest.mark.parametrize("case", CASES[:3])
def test_the_two_formulations_agree_across_the_portable_metrics(case, scenarios):
    """D0, D1 and D2 are portable because the incumbent is a constant, so `|x - x̄|` is
    linear. Checked on all three rather than only the shipped one: a metric that agreed by
    coincidence on D2 would be caught by D0, where the weights are flat."""
    instance = scenarios[case].instance

    for metric in ("D0", "D1", "D2"):
        variant = metrics.as_metric(instance, metric)
        reference = cp_solve(variant, time_limit=30.0)
        _, objective, _ = milp.solve(variant, backend="SCIP", time_limit=30.0)
        assert objective == reference.objective, f"{case} disagrees under {metric}"


@pytest.mark.parametrize("case", ["early-notice/0", "early-notice/1", "tight/0"])
def test_the_two_agree_when_the_consecutive_day_limit_binds(case):
    """No committed case exercises `R-CONSEC-DAYS`: the limit is 6 over a 7-day horizon and
    nobody works enough shifts to reach it, so the constraint is slack everywhere and the
    mutation harness proved it — deleting the MILP's `worked >= x` link broke no test.

    Tightening the limit makes it bind. Without the link the indicator floats free, the
    constraint goes vacuous, and the MILP finds a cheaper roster CP-SAT will not accept.

    Sweeping the limit rather than picking one, because the useful setting is not knowable in
    advance: too tight and the *pinned past* already breaks it, so both formulations correctly
    answer infeasible and nothing about the constraint is tested. The sweep asserts they agree
    at every limit — including agreeing that a case is impossible — and then asserts that at
    least one of them actually bound, so the test cannot pass by never engaging the rule.

    Cases chosen for an early `now`: with the whole week pinned there is no room for a
    tightened limit to bind without the pinned past itself breaking it, and `headline/0` is
    exactly that — every limit it admits is either slack or impossible.
    """
    instance = suite.build(case).instance
    baseline = cp_solve(instance, time_limit=30.0).objective
    bound_somewhere = False

    for limit in range(2, 7):
        tightened = dataclasses.replace(
            instance,
            params=dataclasses.replace(instance.params, max_consecutive_days=limit),
        )
        reference = cp_solve(tightened, time_limit=30.0)
        _, objective, timing = milp.solve(tightened, backend="SCIP", time_limit=30.0)

        if isinstance(reference, list):
            assert timing["status"] != "OPTIMAL", (
                f"{case} at limit {limit}: CP-SAT proved it impossible, the MILP solved it"
            )
            continue

        assert objective == reference.objective, (
            f"{case} at limit {limit}: MILP {objective}, CP-SAT {reference.objective}"
        )
        if reference.objective != baseline:
            bound_somewhere = True

    assert bound_somewhere, (
        f"{case}: no limit in 2..6 changed the answer, so this test never exercised "
        f"R-CONSEC-DAYS and proves nothing about it"
    )


def test_the_two_agree_when_the_incumbent_overstaffs_a_shift(scenarios):
    """`R-COVER`'s ceiling is hard, and nothing in the committed set tests it.

    Every committed incumbent was produced by this model, so none of them overstaffs — which
    left the ceiling unexercised, and a MILP stating coverage as `>=` rather than `==` passed
    every test. An overstaffed incumbent is the case that separates them: the equality forces
    somebody to be dropped and prices it, the inequality lets them stay for free.
    """
    scenario = scenarios["headline/0"]
    instance = scenario.instance

    # Finding the slot is most of the test, and two earlier versions of it proved nothing.
    #
    # The extra person must be **eligible** for the slot, or presolve forces them to zero in
    # both formulations and neither can keep them. And the slot must be one the solution
    # actually fills to `required`: on a slot that is already short — which the headline sick
    # call produces — no formulation would exceed the requirement anyway, so the ceiling is
    # never the binding constraint and `>=` behaves exactly like `==`.
    excluded = exclusions(instance)
    staffed = _fully_staffed_slots(instance)

    target, spare = next(
        (o, e)
        for o in instance.open_shifts
        if not instance.is_past(o.day, o.shift) and (o.day, o.shift) in staffed
        for e in range(len(instance.employees))
        if (e, o.day, o.shift) not in scenario.incumbent
        and (e, o.day, o.shift) not in excluded
    )
    overstaffed = dataclasses.replace(
        instance,
        incumbent=scenario.incumbent | {(spare, target.day, target.shift)},
    )

    reference = cp_solve(overstaffed, time_limit=30.0)
    _, objective, _ = milp.solve(overstaffed, backend="SCIP", time_limit=30.0)

    assert objective == reference.objective, (
        f"an overstaffed incumbent: MILP {objective}, CP-SAT {reference.objective} -- "
        f"the coverage ceiling is stated differently by the two formulations"
    )


@pytest.mark.parametrize("metric", ["D3", "D4"])
def test_the_milp_refuses_the_metrics_it_cannot_state(metric, scenarios):
    """The refusal is the finding. Silently solving a linearised approximation and calling
    it the same problem is how a formulation comparison stops being one."""
    instance = metrics.as_metric(scenarios["headline/0"].instance, metric)

    with pytest.raises(ValueError, match="not linear"):
        milp.build(instance)


def test_the_milp_refuses_skill_mix_rather_than_ignoring_it(scenarios):
    """`R-SKILL-MIX` clamps to `min(minimum, headcount)` and is not ported. No committed
    case carries an entry, so the comparison does not need it — but a formulation that
    silently dropped a constraint would be faster and wrong."""
    instance = scenarios["headline/0"].instance
    first = instance.open_shifts[0]
    with_mix = dataclasses.replace(
        instance,
        open_shifts=(
            dataclasses.replace(
                first,
                skill_mix=(SkillMixEntry(skill="bar", minimum=1, hard=True, provenance="x"),),
            ),
        )
        + instance.open_shifts[1:],
    )

    with pytest.raises(ValueError, match="R-SKILL-MIX"):
        milp.build(with_mix)


@pytest.mark.parametrize("case", CASES[:3])
def test_the_milp_carries_no_gate_literals(case, scenarios):
    """Half of CP-SAT's variables are the reporting apparatus, and the MILP has none of it.

    Asserted because it is the fairness caveat on every timing in the study: the two solvers
    are not given the same model. CP-SAT carries an assumption literal per hard constraint
    instance so a failed solve can name it, and that costs about 22% of its search time.
    """
    from roster_replan.model import build as cp_build

    instance = scenarios[case].instance
    built = cp_build(instance)
    solver, _, _ = milp.build(instance)

    assert built.literals, "the CP-SAT model should be gated"
    assert solver.NumVariables() < len(built.model.proto.variables), (
        "the MILP should be the smaller model, having no gates"
    )


def _fully_staffed_slots(instance) -> set[tuple[int, int]]:
    """Slots the optimal roster fills to `required`.

    The ceiling can only bind where the requirement is actually reachable. On a slot the
    disruption already leaves short, `>=` and `==` describe the same feasible set at the
    optimum, so a test built on one measures nothing.
    """
    solution = cp_solve(instance, time_limit=30.0)
    counts: dict[tuple[int, int], int] = {}
    for _, day, shift in solution.roster:
        counts[day, shift] = counts.get((day, shift), 0) + 1
    return {
        (o.day, o.shift)
        for o in instance.open_shifts
        if counts.get((o.day, o.shift), 0) >= o.required
    }
