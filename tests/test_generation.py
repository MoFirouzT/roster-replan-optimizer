"""Generation mode: the cold-start case of replanning (`replan.md`, `D-109`).

Generation was planned as a separate mode, and `replan.md` answered it in advance — generation
is a replan from an empty incumbent, so there is no second formulation to build. That is a
strong claim and it was never tested. This file tests it, and the three consequences the spec
derives from it.

**Two of those three turned out to be true for a different reason than the spec gives**, which
is the whole reason to write the tests rather than trust the derivation. `disruption_of`
short-circuits to zero when there is no incumbent, so cold disruption is not the constant
`draft_weight × |roster|` the spec derives — it is identically nothing, and the shortfall
caveat the spec attaches to it cannot arise. See `D-109`; the spec now says what the code does.

What this file does *not* do is add an endpoint. `replan.md` argues there is one formulation,
so a `/v1/rosters` beside `/v1/replans` would be a second surface over the same solve — the
tests below pin generation through the surfaces that already exist instead.
"""

from __future__ import annotations

import dataclasses

import pytest

from benchmarks.studies import identical_workforce
from roster_replan import ladder
from roster_replan.checker import check
from roster_replan.model import solve
from roster_replan.scoring import disruption_of, score
from roster_replan.service import contracts
from roster_replan.validation import validate_instance


@pytest.fixture
def cold():
    """No incumbent and no `now`: the payload shape that means *generate*."""
    return identical_workforce(6, required=1)


# --- It is a replan with an empty incumbent, not a second formulation -----------------


def test_a_cold_instance_is_lawful_input(cold):
    """`now` and the incumbent are both absent, which validation accepts as a cold solve —
    the same check that rejects a replan missing only one of them."""
    assert cold.incumbent is None and cold.now is None
    assert validate_instance(cold) == []


def test_generation_solves_to_proven_optimality(cold):
    solution = solve(cold, seed=7, time_limit=30.0)

    assert solution.status == "OPTIMAL"
    assert len(solution.roster) == sum(o.required for o in cold.open_shifts)
    assert [v for v in check(solution.roster, cold) if not v.soft] == []


def test_generation_needs_no_second_code_path(cold):
    """The claim `replan.md` makes and this file exists to hold: the same `solve` produces
    a roster from nothing, with no mode flag and no separate builder."""
    generated = solve(cold, seed=7, time_limit=30.0)
    replanned = solve(
        dataclasses.replace(cold, incumbent=generated.roster, now=0.0, published_through=0.0),
        seed=7,
        time_limit=30.0,
    )
    assert generated.status == replanned.status == "OPTIMAL"


# --- The degeneracy the spec derives -------------------------------------------------


def test_disruption_is_constant_across_rosters_with_equal_coverage(cold):
    """The spec's conclusion, and it holds. Which of several equally-covering rosters is
    returned cannot be decided by disruption, so a cold solve needs its tie-breaker."""
    slots = sorted((o.day, o.shift) for o in cold.open_shifts)
    people = len(cold.employees)
    variants = [
        frozenset(
            ((index + offset) % people, day, shift)
            for index, (day, shift) in enumerate(slots)
        )
        for offset in range(3)
    ]

    assert len({disruption_of(roster, cold) for roster in variants}) == 1


def test_cold_disruption_is_zero_rather_than_a_positive_constant(cold):
    """`D-109`. The spec derived `draft_weight × |roster|`; the scorer returns 0 outright,
    because deviation from nothing is nothing.

    Both rank equal-coverage rosters identically, which is why this went unnoticed — but
    they are different claims, and the next one is why the difference matters.
    """
    solution = solve(cold, seed=7, time_limit=30.0)
    assert disruption_of(solution.roster, cold) == 0
    assert score(solution.roster, cold).disruption == 0


def test_a_cold_shortfall_cannot_buy_a_lower_disruption(cold):
    """The spec warns that a shortfall reduces disruption on a cold solve and that the
    domination bound is what stops it mattering. As implemented it cannot arise at all:
    disruption is zero at every coverage level, so there is nothing for a shortfall to buy.

    The shortfall term still does its own work — this says only that the *disruption* axis
    is flat, which is a narrower and more accurate statement than the spec made.
    """
    solution = solve(cold, seed=7, time_limit=30.0)
    short = frozenset(list(solution.roster)[:-3])

    assert disruption_of(short, cold) == disruption_of(solution.roster, cold) == 0
    assert score(short, cold).shortfall > 0, "the shortfall term still prices it"


def test_the_tie_breaker_is_what_ranks_a_cold_roster(cold):
    """With disruption flat and `cost_weight` at 0 (`D-050`), the objective a cold solve
    actually minimises is the peak-workload tie-breaker. `replan.md` said it reduces to
    cost; today cost is switched off, so it reduces to the thing beneath it."""
    solution = solve(cold, seed=7, time_limit=30.0)
    scored = score(solution.roster, cold)

    assert scored.disruption == 0
    assert scored.cost == 0
    assert scored.peak == solution.objective, "the tie-breaker is the whole objective"


# --- The ladder, which is replan-shaped ----------------------------------------------


def test_generation_reaches_the_exact_rung(cold):
    answer = ladder.answer(cold, seed=7, budget_seconds=30.0)

    assert answer.rung == "exact"
    assert answer.gap == 0.0
    assert len(answer.roster) == sum(o.required for o in cold.open_shifts)


def test_the_lower_rungs_are_replan_only_and_generation_lives_with_that(cold):
    """`service.md` states it: greedy repairs an incumbent and last-known-good returns one,
    so "never return nothing" is a promise about replanning. A cold solve keeps it only
    because a cold solve cannot be infeasible — the empty roster satisfies every hard rule,
    since the coverage floor is soft (`D-018`)."""
    assert [v for v in check(frozenset(), cold) if not v.soft] == []


# --- The wire format already carries it ----------------------------------------------


def test_the_wire_format_round_trips_a_cold_instance(cold):
    """No new contract: `incumbent` and `now` are already nullable, so a caller generates by
    omitting them. The round trip is the identity here as everywhere else."""
    payload = contracts.from_domain(cold)

    assert payload.incumbent is None and payload.now is None
    assert contracts.to_domain(payload) == cold
