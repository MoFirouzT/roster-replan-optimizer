"""Rolling balance of unpopular shifts — the T5 objective (`replan.md`, `D-108`).

Three things are being tested and only one of them is arithmetic.

**The two readings agree.** `disruption.fairness_terms` encodes the term for CP-SAT and
`scoring.fairness_of` reads it back independently, and neither may import the other. The
differential question here is the usual one: the solver's objective value must equal what
the independent scorer measures on the roster it returned.

**It actually balances.** A term that scores correctly and changes no roster is a term that
does nothing, and the arithmetic alone cannot tell those apart. So the behavioural tests run
over an interchangeable workforce, where balance is achievable and any imbalance is a choice.

**It cannot outbid coverage.** Fairness gives the optimiser a *second* reason to leave a
shift empty — an unstaffed unpopular shift is one nobody's count went up for — so `D-057`'s
domination bound had to grow a term. That is the failure worth guarding: it looks like a
tuning preference and is an ordering error.
"""

from __future__ import annotations

import dataclasses

import pytest

from benchmarks import suite
from benchmarks.studies import identical_workforce
from roster_replan.domain import Fairness
from roster_replan.model import solve
from roster_replan.scoring import fairness_of, score
from roster_replan.validation import validate_instance

LATE = 1  # index into the shift catalogue used by both fixtures


def _counts(roster, employees: int) -> list[int]:
    per = {}
    for employee, _, shift in roster:
        if shift == LATE:
            per[employee] = per.get(employee, 0) + 1
    return [per.get(index, 0) for index in range(employees)]


@pytest.fixture
def cold():
    """Eight interchangeable people and a week of late shifts to share.

    The committed set cannot answer this question: its evenings require a scarce skill, so
    the people with no late shifts are the people who *cannot work them*, and a perfectly
    balanced roster there is indistinguishable from an unbalanced one that ran out of
    eligible staff.
    """
    return identical_workforce(8, required=1)


@pytest.fixture
def fair():
    return Fairness(weight=20, unpopular_shifts=frozenset({LATE}), tiers=8)


# --- The two readings ----------------------------------------------------------------


def test_the_encoding_and_the_scorer_agree(cold, fair):
    """The differential question, on the objective rather than on legality."""
    instance = dataclasses.replace(cold, fairness=fair)
    solution = solve(instance, seed=7, time_limit=30.0)

    assert solution.status == "OPTIMAL"
    assert solution.objective == score(solution.roster, instance).total


def test_the_scorer_counts_history_and_horizon_together(cold, fair):
    people = list(cold.employees)
    people[0] = dataclasses.replace(people[0], unpopular_shifts_before_horizon=3)
    instance = dataclasses.replace(cold, employees=tuple(people), fairness=fair)

    roster = frozenset({(0, 0, LATE)})
    # E00 carried 3 and works 1 more: g(4) = 4+3+2+1 = 10, at weight 20.
    assert fairness_of(roster, instance) == 20 * 10


# --- It balances ---------------------------------------------------------------------


def test_a_fixed_number_of_unpopular_shifts_is_spread(cold, fair):
    """Coverage fixes how many late shifts exist, so the only question the term decides is
    who works them. The cheapest way to spend a fixed total under a convex penalty is to
    spread it, and that is the whole mechanism."""
    without = solve(cold, seed=7, time_limit=30.0)
    with_fairness = solve(dataclasses.replace(cold, fairness=fair), seed=7, time_limit=30.0)

    assert max(_counts(with_fairness.roster, 8)) <= max(_counts(without.roster, 8))
    assert max(_counts(with_fairness.roster, 8)) - min(_counts(with_fairness.roster, 8)) <= 1


def test_history_before_the_horizon_moves_the_load_off_the_loaded(cold, fair):
    """The rolling half. One week cannot be fair on its own — somebody works Saturday — so
    the balance is struck over the window the caller supplies."""
    people = list(cold.employees)
    people[0] = dataclasses.replace(people[0], unpopular_shifts_before_horizon=5)
    people[1] = dataclasses.replace(people[1], unpopular_shifts_before_horizon=4)
    instance = dataclasses.replace(cold, employees=tuple(people), fairness=fair)

    counts = _counts(solve(instance, seed=7, time_limit=30.0).roster, 8)
    assert counts[0] == 0, "the person carrying 5 should get none"
    assert counts[1] == 0, "nor the person carrying 4"
    assert sum(counts[2:]) == sum(counts), "the load goes to everyone else"


def test_the_escalation_flattens_past_the_tiers(cold):
    """A stated limit, asserted so it cannot be forgotten (`replan.md`).

    `g` is convex only up to `tiers`; past that the marginal cost is constant and the term
    stops distinguishing people. A rolling window long enough to push everyone beyond the
    tier count therefore switches fairness off while still looking configured.
    """
    flat = Fairness(weight=20, unpopular_shifts=frozenset({LATE}), tiers=2)
    people = [
        dataclasses.replace(person, unpopular_shifts_before_horizon=9)
        for person in cold.employees
    ]
    instance = dataclasses.replace(cold, employees=tuple(people), fairness=flat)

    # Everyone is deep in the linear region, so one more shift costs `tiers` wherever it
    # lands and the term cannot prefer any distribution over another.
    loaded = fairness_of(frozenset({(0, 0, LATE), (0, 1, LATE)}), instance)
    spread = fairness_of(frozenset({(0, 0, LATE), (1, 1, LATE)}), instance)
    assert loaded == spread


# --- Off unless switched on ----------------------------------------------------------


@pytest.mark.parametrize(
    "params",
    [
        None,
        Fairness(weight=0, unpopular_shifts=frozenset({LATE}), tiers=8),
        Fairness(weight=20, unpopular_shifts=frozenset(), tiers=8),
        Fairness(weight=20, unpopular_shifts=frozenset({LATE}), tiers=0),
    ],
    ids=["absent", "no-weight", "no-unpopular-shift", "no-tiers"],
)
def test_fairness_is_inert_unless_fully_configured(cold, params):
    instance = dataclasses.replace(cold, fairness=params)
    assert fairness_of(frozenset({(0, 0, LATE)}), instance) == 0
    assert score(frozenset({(0, 0, LATE)}), instance).fairness == 0


def test_a_shift_nobody_calls_unpopular_is_not_priced(cold):
    """Unpopularity is declared, not derived. A tenant whose late shift is the sought-after
    one names no shift, and the term must then price nothing."""
    instance = dataclasses.replace(
        cold, fairness=Fairness(weight=20, unpopular_shifts=frozenset({0}), tiers=8)
    )
    assert fairness_of(frozenset({(0, 0, LATE)}), instance) == 0


# --- It cannot outbid coverage -------------------------------------------------------


def test_fairness_cannot_buy_stability_by_understaffing():
    """`D-057` extended (`D-108`). An unstaffed unpopular shift is one nobody's count went
    up for, so a fairness weight large enough to outbid the shortfall weight is a malformed
    request rather than an aggressive preference."""
    instance = suite.build("headline/0").instance

    ok = dataclasses.replace(instance, fairness=Fairness(20, frozenset({LATE}), 8))
    assert validate_instance(ok) == []

    outbids = dataclasses.replace(instance, fairness=Fairness(20_000, frozenset({LATE}), 8))
    defects = validate_instance(outbids)
    assert any(d.field == "disruption.shortfall_weight" for d in defects)
    assert any("understaffing" in d.message for d in defects)


def test_the_bound_ignores_a_fairness_term_that_is_switched_off():
    """An inert term cannot pay for a shortfall, so it must not tighten the bound either —
    otherwise switching fairness on at weight zero would reject a valid weight scale."""
    instance = suite.build("headline/0").instance
    inert = dataclasses.replace(instance, fairness=Fairness(0, frozenset({LATE}), 8))
    assert validate_instance(inert) == []
