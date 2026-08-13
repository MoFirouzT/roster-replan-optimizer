"""The golden layer: committed values must not move silently.

Deliberately the cheapest layer in the suite -- it solves and compares against a committed
file, with no enumeration. Its value is not detection power, which stage (b) already has,
but *reviewability*: a behavioural change arrives as a diff a human reads.
"""

from __future__ import annotations

import pytest
from golden import GOLDEN_PATH, METRICS, load, record, variant
from micro_instances import MICRO_INSTANCES

NAMES = sorted(MICRO_INSTANCES)

REGENERATE = (
    "Objective values moved. If the change is intended, regenerate with\n"
    "    uv run python -m tests.golden --write\n"
    "and justify the diff with a decisions.md entry -- that entry is the point of this "
    "layer, not the file."
)


def test_the_golden_file_exists_and_covers_the_set():
    assert GOLDEN_PATH.exists(), f"missing {GOLDEN_PATH}; run `python -m tests.golden --write`"
    committed = load()
    assert sorted(committed) == NAMES, "the golden file and the instance set have diverged"
    for name in NAMES:
        assert sorted(committed[name]) == sorted(METRICS), name


@pytest.mark.parametrize("name", NAMES)
def test_objective_values_match_the_record(name):
    committed, current = load()[name], record()[name]
    for metric in METRICS:
        assert current[metric] == committed[metric], f"{name}/{metric}\n{REGENERATE}"


def test_recorded_rosters_are_reproduced():
    """Where a roster was recorded the optimum was unique at generation time, so the solver
    must return exactly it -- no tie to hide behind."""
    committed = load()
    for name in NAMES:
        for metric in METRICS:
            expected = committed[name][metric].get("roster")
            if expected is None:
                continue
            from conftest import solved

            result = solved(variant(name, metric))
            assert sorted(list(k) for k in result.roster) == expected, f"{name}/{metric}"


def test_the_record_distinguishes_unique_from_tied_optima():
    """A record in which nothing is unique, or everything is, would mean the uniqueness
    check silently stopped working -- and the roster assertions would go vacuous."""
    committed = load()
    with_roster = sum(
        1 for name in NAMES for metric in METRICS if "roster" in committed[name][metric]
    )
    total = len(NAMES) * len(METRICS)
    assert 0 < with_roster < total, f"{with_roster} of {total} entries recorded a roster"


def test_the_infeasible_instance_is_recorded_as_a_core():
    committed = load()["pinned_past_already_illegal"]
    for metric in METRICS:
        assert "R-PIN-PAST" in committed[metric]["core_rules"], metric
        assert "objective" not in committed[metric]
