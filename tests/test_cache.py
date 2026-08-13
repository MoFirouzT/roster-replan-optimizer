"""The compiled-model cache: reuse must be indistinguishable from a fresh build.

This cache has a failure mode worse than being slow. A model carries its objective, its
hints and its assumptions, and all three survive a solve. Reusing one without clearing them
returns **a legal roster optimised for the previous request** — a correct-looking answer to
somebody else's question, with no error, no violation and no gap to give it away.

So the tests are about equivalence, not speed:

- a cached solve equals a fresh solve, on the same instance;
- a cached solve under a *different metric* equals a fresh one, which is the case a stale
  objective fails and an identical-objective test would miss;
- a hint left by one solve does not follow the model into the next;
- the fingerprint separates any two instances that build different models, and in
  particular separates a week from the same week after an absence.

The fingerprint is the whole safety argument, so it is tested in both directions: it must
not collide across different models, and it must be stable across payloads that differ only
in things `build` never reads.
"""

from __future__ import annotations

import dataclasses

import pytest

from benchmarks import metrics, suite
from roster_replan.checker import check
from roster_replan.compiled import ModelCache, fingerprint
from roster_replan.domain import Interval
from roster_replan.model import solve

CASES = ["headline/0", "tight/0", "small/0", "scarce-skill/0"]


@pytest.fixture(scope="module")
def scenarios():
    return {case: suite.build(case) for case in CASES}


# --- The fingerprint ----------------------------------------------------------------


@pytest.mark.parametrize("case", CASES)
def test_an_absence_changes_the_fingerprint(case, scenarios):
    """The replan case, and the one that matters most.

    An event is usually an absence, an absence changes which pairs survive presolve, and
    that changes the variables. A fingerprint blind to it would hand a replan the model of
    the week before the disruption.

    **The absence is injected here rather than taken from the scenario**, because comparing
    `scenario.base` with `scenario.instance` proves nothing: those two also differ in their
    incumbent, so the fingerprints separate for that reason alone and a fingerprint blind to
    absences passes. The mutation harness found exactly that — this test used to be the
    weaker comparison, and deleting absences from the key did not break it.
    """
    instance = scenarios[case].instance
    person = instance.employees[0]
    absent = dataclasses.replace(
        person, absences=person.absences + (Interval(0.0, 24.0),)
    )
    changed = dataclasses.replace(
        instance, employees=(absent,) + instance.employees[1:]
    )

    assert fingerprint(changed) != fingerprint(instance)


@pytest.mark.parametrize("case", CASES)
def test_declared_unavailability_also_changes_the_fingerprint(case, scenarios):
    """`R-AVAIL` reads both, and presolve excludes on both, so both are model inputs.
    Split from absences (`D-020`) because they are different things and a key that covers
    one is not evidence it covers the other."""
    instance = scenarios[case].instance
    person = instance.employees[0]
    withdrawn = dataclasses.replace(
        person, unavailability=person.unavailability + (Interval(0.0, 24.0),)
    )
    changed = dataclasses.replace(
        instance, employees=(withdrawn,) + instance.employees[1:]
    )

    assert fingerprint(changed) != fingerprint(instance)


def test_the_fingerprint_is_stable_across_repeated_calls(scenarios):
    instance = scenarios["headline/0"].instance
    assert fingerprint(instance) == fingerprint(dataclasses.replace(instance))


def test_the_fingerprint_ignores_the_objective_but_not_the_incumbent(scenarios):
    """`disruption` is applied per solve, so it is not part of the model.

    The incumbent *is*, and only because of `D-058`: `build` creates a variable for any pair
    the incumbent assigned even when presolve excluded it. The tidy split — constraints in
    the key, objective out — would be wrong in exactly this one place, and wrong in the
    direction that drops the variables a deviation is counted on.
    """
    instance = scenarios["headline/0"].instance

    other_metric = metrics.as_metric(instance, "D3")
    assert fingerprint(other_metric) == fingerprint(instance)

    incumbent = set(instance.incumbent)
    incumbent.pop()
    moved = dataclasses.replace(instance, incumbent=frozenset(incumbent))
    assert fingerprint(moved) != fingerprint(instance)


@pytest.mark.parametrize("case", CASES)
def test_different_instances_get_different_fingerprints(case, scenarios):
    others = {fingerprint(s.instance) for name, s in scenarios.items() if name != case}
    assert fingerprint(scenarios[case].instance) not in others


# --- Equivalence --------------------------------------------------------------------


@pytest.mark.parametrize("case", CASES)
def test_a_cached_solve_equals_a_fresh_one(case, scenarios):
    instance = scenarios[case].instance
    cache = ModelCache()

    first = solve(instance, built=cache.get(instance))
    second = solve(instance, built=cache.get(instance))
    fresh = solve(instance)

    assert cache.hits == 1
    assert first.objective == fresh.objective
    assert second.objective == fresh.objective
    assert second.roster == fresh.roster
    assert not [v for v in check(second.roster, instance) if not v.soft]


@pytest.mark.parametrize("case", CASES)
def test_a_reused_model_does_not_carry_the_previous_objective(case, scenarios):
    """The bug this cache could introduce, and the only test that would catch it.

    Solve once under D2, then reuse the same model under D0. If the objective were not
    cleared, the second answer would be D2's — still legal, still optimal for *something*,
    and wrong. Comparing two solves under the same objective would pass either way.
    """
    instance = scenarios[case].instance
    cache = ModelCache()

    solve(instance, built=cache.get(instance))

    flat = metrics.as_metric(instance, "D0")
    reused = solve(flat, built=cache.get(flat))
    fresh = solve(flat)

    # The hit is the premise, not an accident: D0 and D2 differ only in the objective, so
    # they share a model by design. That is what puts a D2 objective in front of a D0
    # solve, which is the situation being tested.
    assert cache.hits == 1

    assert reused.objective == fresh.objective
    assert reused.roster == fresh.roster
    assert reused.objective != solve(instance).objective, (
        "D0 and D2 score this case identically, so a stale objective would be invisible "
        "here and this case proves nothing"
    )


@pytest.mark.parametrize("case", CASES)
def test_a_hint_does_not_survive_into_the_next_solve(case, scenarios):
    """A stale hint does not change the optimum, but it does change the search — so a
    cached solve would stop being reproducible from its seed, which `PLAN.md` requires end
    to end."""
    scenario = scenarios[case]
    instance = scenario.instance
    cache = ModelCache()

    solve(instance, built=cache.get(instance), hint=scenario.incumbent)
    reused = solve(instance, built=cache.get(instance))
    fresh = solve(instance)

    assert reused.objective == fresh.objective
    assert reused.roster == fresh.roster


# --- The cache itself ---------------------------------------------------------------


def test_the_cache_is_bounded(scenarios):
    """An unbounded cache in a long-running service is a memory leak with a friendly name."""
    cache = ModelCache(capacity=2)
    for case in CASES:
        cache.get(scenarios[case].instance)
    assert len(cache) == 2


def test_tenants_do_not_evict_or_read_each_other(scenarios):
    instance = scenarios["headline/0"].instance
    cache = ModelCache()

    cache.get(instance, tenant="a")
    cache.get(instance, tenant="b")
    assert cache.hits == 0, "an identical payload from another tenant is not a hit"

    cache.get(instance, tenant="a")
    assert cache.hits == 1


def test_the_replan_path_does_not_hit(scenarios):
    """The measured verdict, asserted so it cannot quietly stop being true.

    A replan is triggered by a change to the model's own inputs, so the base week and the
    post-event instance never share a fingerprint. The cache is kept because a miss costs
    0.6% of a build, not because it helps here — and if this ever starts hitting, something
    has stopped distinguishing two different models.
    """
    cache = ModelCache()
    for scenario in scenarios.values():
        cache.get(scenario.base, tenant=scenario.name)
        cache.get(scenario.instance, tenant=scenario.name)

    assert cache.hits == 0
    assert cache.misses == 2 * len(scenarios)
