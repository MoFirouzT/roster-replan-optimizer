"""The committed benchmark set: twelve scenario classes, six seeds each.

    uv run python -m benchmarks.suite --write

**The set is defined by its seeds, not by serialised instances.** Generation is
deterministic, so a class name plus a seed names an instance exactly, and the only
thing committed is a manifest of fingerprints rather than 72 payloads. The diff stays readable,
which is the property that decides whether anyone looks at it.

That trade has one exposure, and the manifest is shaped around it: if the generator
changes, every instance changes silently. So each scenario carries **two** fingerprints.

- `week` covers the generated payload only, before any solve. It moves when the generator
  moves.
- `incumbent` covers the solved base roster. It moves when the generator moves *or* when
  the solver does -- a CP-SAT upgrade or a change to the objective encoding.

Splitting them makes a failure diagnostic rather than merely loud: one hash moving is a
solver change, both moving is a generator change. A single combined hash would have said
"something changed" and left the reader to find out which, and `D-067` is the standing
lesson about what happens then -- people regenerate without reading.

Nothing is filtered. A scenario that guarantees a shortfall, or whose event barely damages
the week, stays in the set with that fact recorded. Filtering at generation time would
prune the distribution to the cases that flatter the thesis, and which cases to exclude is
an analysis decision that belongs in `benchmarks.md` where it can be argued with.
"""

from __future__ import annotations

import argparse
import dataclasses
import hashlib
import json
import pathlib

from benchmarks.generator import (
    AVAILABILITY_WITHDRAWAL,
    DEMAND_SPIKE,
    MULTI_ABSENCE,
    SICK_CALL,
    Scenario,
    ScenarioParams,
    generate,
)
from roster_replan.model import exclusions

MANIFEST_PATH = pathlib.Path(__file__).with_name("manifest.json")

# Bump when a change to `generator.py` is meant to move the instances, and say why in
# `decisions.md`. The fingerprints below are what makes forgetting to bump it fail.
GENERATOR_VERSION = 1

SEEDS = tuple(range(6))

# The Saturday 09:00 sick call on a mid-sized tenant with slack. Every other class varies
# one axis from here, so a difference in results has one candidate explanation rather
# than several.
BASELINE = ScenarioParams(
    employees=12,
    demand_ratio=0.70,
    scarce_skill_share=0.5,
    flexi_share=0.25,
    availability_density=0.85,
    event=SICK_CALL,
    event_day=5,
    event_hour=9.0,
)


def _vary(**changes) -> ScenarioParams:
    return dataclasses.replace(BASELINE, **changes)


CLASSES: dict[str, ScenarioParams] = {
    "headline": BASELINE,
    # Coverage tightness: the axis `D-060` says decides whether the metrics can diverge
    # at all. Three points, because two would not show a curve.
    #
    # `loose` sits at 0.35 rather than a rounder 0.45 for a structural reason: at this
    # tenant size the full 21-slot grid needs about 0.40, so anything above that keeps
    # every shift open and the set never exercises a week that closes slots (`D-071`).
    # Instance size would then be constant everywhere except the employee axis.
    "loose": _vary(demand_ratio=0.35),
    "tight": _vary(demand_ratio=0.90),
    # Tenant size, at both ends of the range `benchmarks.md` claims.
    "small": _vary(employees=8),
    "large": _vary(employees=25),
    # Eligibility pressure that is not demand: scarcity, contract mix, availability.
    #
    # `scarce-skill` is deliberately hard enough that the base week cannot be fully
    # staffed. The chronically short tenant is a real case and the replan question there
    # is a real question, but it is the one class where the incumbent starts broken, so
    # results over it are segmented rather than pooled.
    "scarce-skill": _vary(scarce_skill_share=0.25),
    "flexi-heavy": _vary(flexi_share=0.60),
    "thin-availability": _vary(availability_density=0.60),
    # The other three disruption types, held at the baseline so the event is the only
    # thing that differs from `headline`.
    "multi-absence": _vary(event=MULTI_ABSENCE),
    "demand-spike": _vary(event=DEMAND_SPIKE),
    "withdrawal": _vary(event=AVAILABILITY_WITHDRAWAL),
    # The same disruption with days of notice instead of hours. Without this class the
    # notice multiplier that defines D2 is constant across the whole set.
    "early-notice": _vary(event_day=1),
}


def case_names() -> list[str]:
    return [f"{name}/{seed}" for name in CLASSES for seed in SEEDS]


def build(case: str) -> Scenario:
    """The scenario for one committed case name, e.g. `headline/3`."""
    name, _, seed = case.partition("/")
    if name not in CLASSES:
        raise KeyError(f"unknown class {name!r}; expected one of {sorted(CLASSES)}")
    return generate(int(seed), CLASSES[name])


# --- Fingerprints -------------------------------------------------------------------


def _canonical(value):
    """A stable, JSON-able rendering of the payload tree.

    Sets and frozensets are sorted rather than left in iteration order: a hash that
    depends on set ordering would change between interpreter runs and the manifest would
    be worthless.
    """
    if dataclasses.is_dataclass(value):
        # Only fields that participate in equality. A field excluded from `__eq__` must be
        # excluded from a fingerprint too, or two instances that compare equal hash
        # differently -- which is not a stylistic point here: `Instance._windows` is a
        # memoisation cache, so its contents depend on which methods happened to be called
        # before the digest was taken, and every hash in the committed manifest would move
        # when an unrelated caller looked up one more shift window.
        return {
            f.name: _canonical(getattr(value, f.name))
            for f in dataclasses.fields(value)
            if f.compare
        }
    if isinstance(value, (frozenset, set)):
        return sorted(_canonical(v) for v in value)
    if isinstance(value, (list, tuple)):
        return [_canonical(v) for v in value]
    if isinstance(value, dict):
        return {str(k): _canonical(v) for k, v in sorted(value.items())}
    return value


def _digest(value) -> str:
    blob = json.dumps(_canonical(value), sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(blob.encode()).hexdigest()[:16]


def _damage(scenario: Scenario) -> int:
    """How much of the published week the event actually invalidated.

    Counted without solving: incumbent assignments the event made ineligible, plus any
    headcount the event added. A scenario whose damage is zero poses no question, and the
    benchmark would score it as a flawless repair.
    """
    excluded = exclusions(scenario.instance)
    broken = sum(1 for key in scenario.incumbent if key in excluded)
    added = sum(o.required for o in scenario.instance.open_shifts) - sum(
        o.required for o in scenario.base.open_shifts
    )
    return broken + added


def entry(scenario: Scenario) -> dict:
    tightness = scenario.tightness
    return {
        "event": scenario.params.event,
        "employees": scenario.params.employees,
        "open_shifts": len(scenario.instance.open_shifts),
        "week": _digest(scenario.base),
        "incumbent": _digest(sorted(scenario.incumbent)),
        "demand_ratio": round(tightness.demand_ratio, 4),
        "min_slot_slack": tightness.min_slot_slack,
        "tight_slots": tightness.tight_slots,
        "short_slots": tightness.short_slots,
        "base_shortfall": scenario.base_shortfall,
        "damage": _damage(scenario),
    }


def manifest() -> dict:
    """The manifest as it should be, computed from the current code."""
    return {
        "generator_version": GENERATOR_VERSION,
        "cases": {case: entry(build(case)) for case in case_names()},
    }


def load() -> dict:
    return json.loads(MANIFEST_PATH.read_text())


def write() -> None:
    MANIFEST_PATH.write_text(json.dumps(manifest(), indent=2, sort_keys=True) + "\n")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--write",
        action="store_true",
        help="overwrite manifest.json. The diff needs a decisions.md entry, and a "
        "generator change that moves it needs GENERATOR_VERSION bumped too.",
    )
    args = parser.parse_args()
    if args.write:
        write()
        print(f"wrote {MANIFEST_PATH} ({len(case_names())} cases)")
    else:
        print(json.dumps(manifest(), indent=2, sort_keys=True))
