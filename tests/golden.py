"""The golden record: committed objective values, and how to regenerate them.

`internals/testing.md`: *committed scenarios with committed objective values; a diff fails CI until
a `decisions.md` entry justifies it.* This module owns the record's shape and its
regeneration, so the workflow is a command rather than folklore:

    uv run python -m tests.golden --write

The point is friction in the right place. Any change to the model, the metric or the rules
that moves a number shows up as a **reviewable diff in a committed JSON file**, and the only
way to make CI green again is to regenerate deliberately and say why.

**Rosters are recorded only where the optimum is unique.** Interchangeable employees create
ties, so a tied optimum's *roster* is a function of solver version and search order rather
than of the specification -- committing one would produce failures that are not defects and
would train everyone to regenerate without reading. Uniqueness is settled by enumeration at
generation time, so the distinction is measured rather than guessed.
"""

from __future__ import annotations

import argparse
import dataclasses
import json
import pathlib
import sys

# This module is both a pytest import and a command-line entry point, and the two see
# different paths: pytest puts `tests/` on `sys.path`, while running the file directly puts
# only `tests/` there and `python -m tests.golden` puts only the repo root. Setting both
# makes every invocation work, which matters because a regeneration command nobody can run
# is the same as no regeneration command.
_HERE = pathlib.Path(__file__).resolve().parent
for _path in (_HERE, _HERE.parent):
    if str(_path) not in sys.path:
        sys.path.insert(0, str(_path))

from micro_instances import EXPECTED_INFEASIBLE, MICRO_INSTANCES  # noqa: E402

from roster_replan.domain import shipped_d2  # noqa: E402
from roster_replan.model import solve  # noqa: E402
from roster_replan.scoring import score  # noqa: E402

GOLDEN_PATH = pathlib.Path(__file__).with_name("golden.json")
METRICS = ["D0", "D1", "D2", "D3", "D4"]


def variant(name: str, metric: str):
    return dataclasses.replace(MICRO_INSTANCES[name], disruption=shipped_d2(metric=metric))


def _unique_optimum(instance) -> tuple[bool, int]:
    """Whether exactly one feasible roster attains the optimum, by enumeration."""
    from test_ground_truth import enumerate_optimum

    optimum, winners = enumerate_optimum(instance)
    return len(winners) == 1, optimum


def record() -> dict:
    """The record as it should be, computed from the current code."""
    out: dict = {}
    for name in sorted(MICRO_INSTANCES):
        out[name] = {}
        for metric in METRICS:
            instance = variant(name, metric)
            result = solve(instance)

            if isinstance(result, list):
                out[name][metric] = {"core_rules": sorted({g.rule for g in result})}
                continue

            terms = score(result.roster, instance)
            entry = {
                "objective": result.objective,
                "disruption": terms.disruption,
                "shortfall": terms.shortfall,
                "mix_shortfall": terms.mix_shortfall,
                "cost": terms.cost,
                "peak": terms.peak,
            }
            if name not in EXPECTED_INFEASIBLE:
                unique, _ = _unique_optimum(instance)
                if unique:
                    entry["roster"] = sorted(list(k) for k in result.roster)
            out[name][metric] = entry
    return out


def load() -> dict:
    return json.loads(GOLDEN_PATH.read_text())


def write() -> None:
    GOLDEN_PATH.write_text(json.dumps(record(), indent=2, sort_keys=True) + "\n")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--write",
        action="store_true",
        help="overwrite golden.json. The resulting diff needs a decisions.md entry.",
    )
    args = parser.parse_args()
    if args.write:
        write()
        print(f"wrote {GOLDEN_PATH}")
    else:
        print(json.dumps(record(), indent=2, sort_keys=True))
