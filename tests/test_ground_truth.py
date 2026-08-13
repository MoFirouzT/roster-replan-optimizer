"""Brute-force ground truth over the committed instance set.

`PLAN.md`'s T1 gate: "~20 committed micro-instances (N<=6, 3 days), solver objective equals
enumerated optimum". This is that gate, in both stages -- (a) feasible and violation sets,
(b) objectives.

The instances live in `micro_instances.py` and are fixed rather than generated. Random
instances catch bugs; fixed ones catch regressions, and this layer is for the second job.
"""

from __future__ import annotations

import itertools

import pytest
from conftest import solved
from micro_instances import (
    EXPECTED_INFEASIBLE,
    MICRO_INSTANCES,
    enumeration_cost,
)
from test_differential import agree

from roster_replan.checker import check, is_feasible
from roster_replan.domain import Instance, shipped_d2
from roster_replan.model import solve, violations
from roster_replan.scoring import score
from roster_replan.validation import validate_instance

import dataclasses

NAMES = sorted(MICRO_INSTANCES)
SOLVABLE = [n for n in NAMES if n not in EXPECTED_INFEASIBLE]
METRICS = ["D0", "D1", "D2", "D3", "D4"]

# Enumerating 2**10 rosters per instance per metric is the budget. Above that the layer
# gets slow, and a slow enumeration layer is one that eventually gets deleted rather than
# fixed -- so the bound is asserted, not left to review.
MAX_ENUMERATION_EXPONENT = 10


def all_rosters(instance: Instance):
    keys = [
        (e, o.day, o.shift)
        for e in range(len(instance.employees))
        for o in instance.open_shifts
    ]
    for mask in itertools.product((0, 1), repeat=len(keys)):
        yield frozenset(k for k, bit in zip(keys, mask) if bit)


def enumerate_optimum(instance: Instance) -> tuple[int, list]:
    """The true optimum and every roster achieving it, scored independently of the model."""
    best, winners = None, []
    for roster in all_rosters(instance):
        if not is_feasible(roster, instance):
            continue
        total = score(roster, instance).total
        if best is None or total < best:
            best, winners = total, [roster]
        elif total == best:
            winners.append(roster)
    return best, winners


# --- The set itself -----------------------------------------------------------------


def test_the_set_is_large_enough():
    assert len(MICRO_INSTANCES) >= 20, "PLAN.md asks for ~20 committed instances"


def test_every_instance_is_a_well_formed_request():
    """A ground-truth instance that fails input validation is testing a malformed payload,
    and its "optimum" means nothing. Defects are exercised in `test_validation.py`."""
    for name in NAMES:
        assert validate_instance(MICRO_INSTANCES[name]) == [], name


def test_enumeration_stays_within_budget():
    over = {
        name: enumeration_cost(MICRO_INSTANCES[name])
        for name in NAMES
        if enumeration_cost(MICRO_INSTANCES[name]) > MAX_ENUMERATION_EXPONENT
    }
    assert over == {}, f"instances too large to enumerate: {over}"


def test_instances_are_structurally_distinct():
    """Two identical instances under different names look like coverage and are not."""
    seen: dict[str, str] = {}
    for name in NAMES:
        instance = MICRO_INSTANCES[name]
        # `repr` rather than the objects themselves: `RuleParams` carries a
        # `derogation_basis` dict and so is unhashable despite being frozen.
        fingerprint = repr(
            (
                instance.days,
                instance.shift_types,
                instance.employees,
                instance.open_shifts,
                instance.params,
                instance.now,
                sorted(instance.incumbent or ()),
                instance.published_through,
            )
        )
        assert fingerprint not in seen, f"{name} duplicates {seen.get(fingerprint)}"
        seen[fingerprint] = name


# --- Stage (a): feasible and violation sets ----------------------------------------


@pytest.mark.parametrize("name", NAMES)
def test_stage_a_feasible_sets_agree(name):
    instance = MICRO_INSTANCES[name]
    for roster in all_rosters(instance):
        assert is_feasible(roster, instance) == (violations(roster, instance) == []), (
            name,
            sorted(roster),
        )


@pytest.mark.parametrize("name", NAMES)
def test_stage_a_violation_sets_agree(name):
    instance = MICRO_INSTANCES[name]
    disagreements = [r for r in all_rosters(instance) if not agree(r, instance)]
    assert disagreements == [], (name, sorted(disagreements[0]))


# --- Stage (b): objectives ----------------------------------------------------------


@pytest.mark.parametrize("name", SOLVABLE)
def test_stage_b_optimum_matches_the_solver(name):
    instance = MICRO_INSTANCES[name]
    optimum, _ = enumerate_optimum(instance)
    assert solved(instance).objective == optimum, name


@pytest.mark.parametrize("metric", METRICS)
def test_stage_b_holds_for_every_metric(metric):
    """The metric changes the objective, so each needs its own ground truth. Run across the
    whole set rather than per-instance to keep the parametrisation from exploding."""
    for name in SOLVABLE:
        instance = dataclasses.replace(
            MICRO_INSTANCES[name], disruption=shipped_d2(metric=metric)
        )
        optimum, _ = enumerate_optimum(instance)
        assert solved(instance).objective == optimum, (name, metric)


# --- The deliberately unsatisfiable one --------------------------------------------


def test_an_illegal_past_returns_a_core_naming_the_pin():
    core = solve(MICRO_INSTANCES["pinned_past_already_illegal"])
    assert isinstance(core, list) and core
    assert "R-PIN-PAST" in {gate.rule for gate in core}


def test_solvable_instances_really_do_solve():
    """Guards the partition: an instance quietly becoming infeasible would otherwise just
    vanish from stage (b) rather than fail."""
    for name in SOLVABLE:
        result = solve(MICRO_INSTANCES[name])
        assert not isinstance(result, list), f"{name} became infeasible: {result}"
        assert [v for v in check(result.roster, MICRO_INSTANCES[name]) if not v.soft] == []
