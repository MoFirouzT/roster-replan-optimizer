"""The D0-D4 study: do five defensible definitions of disruption disagree, and where?

    uv run python -m benchmarks.metrics            # summary to stdout
    uv run python -m benchmarks.metrics --write    # and metrics.json

`internals/model.md` defines five metrics and ships D2, and says the fact that they produce
different rosters is the deliverable rather than a problem to settle. This module is that
claim, measured. `D-060` adds the constraint that makes the measurement possible at all:
they can only diverge where there is slack, because a tightly covered week has one legal
repair and every metric returns it.

## Comparing rosters is the wrong measurement, and the tempting one

The obvious method is to solve under each metric and ask whether the rosters differ. It
does not work, and the reason is the same one that made the cost baseline in `methods.py`
report noise: **a metric usually has many optimal rosters**, and which one comes back is
the solver's search order. Two rosters differing tells you nothing about whether the two
metrics wanted different things -- D0 has a huge tie set, so it will "disagree" with
everything, including with itself at another seed.

## What is measured instead: regret, by lexicographic solve

For an ordered pair of metrics `(a, b)`, the question worth asking is *what does committing
to a cost you in b, at best*. That is answered exactly, and without any tie ambiguity:

1. Solve under `a`. Call its optimal objective `V_a`.
2. Solve again minimising `b`, subject to the constraint that `a`'s objective equals `V_a`.
   This picks the **best `b`-roster among all of `a`'s optima** -- the most charitable
   reading of `a` available.
3. `regret(a → b)` is that roster's `b` score minus `b`'s own optimum.

`regret(a → b) > 0` is therefore a genuine conflict: *no* roster that is optimal under `a`
is optimal under `b`, so the two metrics cannot be satisfied together and the choice
between them changes who works. Zero regret means `a` and `b` can agree, whichever roster
the solver happened to return. Ties cannot manufacture a finding, and cannot hide one.

The relation need not be symmetric, so both directions are computed. Raw regrets across
directions are **not comparable**, because the metrics live on different scales -- D3
multiplies by change-type weights of 6 to 14 where D2 does not. Normalise against the
paying metric's own optimum before reading an asymmetry into them; measured that way the
disagreement here turns out to be about even in both directions.

Scoring is done by `scoring.py`, the independent reading, on the returned roster -- never
by reading an objective value back out of the solver.
"""

from __future__ import annotations

import argparse
import dataclasses
import json
import pathlib
import statistics
from collections import defaultdict

from ortools.sat.python import cp_model

from benchmarks import suite
from benchmarks.generator import Scenario
from roster_replan.checker import check
from roster_replan.disruption import objective_terms
from roster_replan.domain import Instance, Roster
from roster_replan.model import build, exclusions
from roster_replan.scoring import disruption_of

METRICS_PATH = pathlib.Path(__file__).with_name("metrics.json")

METRICS = ("D0", "D1", "D2", "D3", "D4")


def as_metric(instance: Instance, metric: str) -> Instance:
    """The same instance read under a different metric, and **nothing else changed**.

    Every weight, band and threshold is held: `internals/model.md` makes each metric nest the one
    before it, so D1 with equal weights is D0 and D2 with a flat multiplier is D1. Varying
    a weight alongside the metric would measure the weight.
    """
    params = instance.disruption
    if params is None:
        raise ValueError("the metric study needs the scenario's disruption profile")
    if metric not in METRICS:
        raise KeyError(f"unknown metric {metric!r}; expected one of {METRICS}")
    return dataclasses.replace(instance, disruption=dataclasses.replace(params, metric=metric))


def _terms(built, instance: Instance, metric: str):
    return objective_terms(
        built.model, as_metric(instance, metric), built.x, built.shortfall, built.mix_shortfall
    )


def _extract(solver: cp_model.CpSolver, built) -> Roster:
    return frozenset(key for key, var in built.x.items() if solver.value(var))


def _configure(built, seed: int, time_limit: float) -> cp_model.CpSolver:
    """A solver over a built model, with every gate held true.

    The assumptions are not optional and skipping them is silent: each hard constraint is
    conditioned on an assumption literal so that a failed solve can name it (`model.py`),
    which means an unasserted literal is a free boolean the optimiser will happily set
    false to switch its constraint off. The first version of this module omitted this line
    and scored rosters that broke hard rules.
    """
    built.model.clear_assumptions()
    built.model.add_assumptions(built.literals)

    solver = cp_model.CpSolver()
    solver.parameters.num_workers = 1
    solver.parameters.random_seed = seed
    solver.parameters.max_time_in_seconds = time_limit
    return solver


def optimum(instance: Instance, metric: str, *, seed: int = 7, time_limit: float = 30.0):
    """Solve under one metric. Returns `(roster, objective)`."""
    built = build(instance)
    built.model.minimize(sum(_terms(built, instance, metric)))

    solver = _configure(built, seed, time_limit)
    status = solver.solve(built.model)
    if status != cp_model.OPTIMAL:
        raise RuntimeError(
            f"metric {metric} did not solve to optimality ({solver.status_name(status)}); "
            f"a regret computed from a non-optimal bound is not a regret"
        )
    return _extract(solver, built), round(solver.objective_value)


def best_under(
    instance: Instance, hold: str, held_at: int, minimise: str, *, seed: int = 7, time_limit: float = 30.0
) -> Roster:
    """The best `minimise`-roster among the optima of `hold`.

    One model carrying both objectives: `hold` as an equality at its known optimum, and
    `minimise` as the thing being optimised. Both are built over the same assignment
    variables, which is what makes the comparison exact rather than a re-solve that might
    land somewhere else.
    """
    built = build(instance)
    built.model.add(sum(_terms(built, instance, hold)) == held_at)
    built.model.minimize(sum(_terms(built, instance, minimise)))

    solver = _configure(built, seed, time_limit)
    status = solver.solve(built.model)
    if status != cp_model.OPTIMAL:
        raise RuntimeError(
            f"holding {hold} at {held_at} while minimising {minimise} did not solve to "
            f"optimality ({solver.status_name(status)})"
        )
    return _extract(solver, built)


# --- The study ----------------------------------------------------------------------


def regrets(scenario: Scenario, *, seed: int = 7, time_limit: float = 30.0) -> dict:
    """Every ordered pair's regret on one case, plus the per-metric optima behind them."""
    instance = scenario.instance
    solved = {m: optimum(instance, m, seed=seed, time_limit=time_limit) for m in METRICS}

    # Scored by the independent reading, on the roster -- never read back off the solver.
    own = {m: score_under(solved[m][0], instance, m) for m in METRICS}

    pairs: dict[str, int] = {}
    for a in METRICS:
        for b in METRICS:
            if a == b:
                continue
            charitable = best_under(
                instance, a, solved[a][1], b, seed=seed, time_limit=time_limit
            )
            regret = score_under(charitable, instance, b) - own[b]
            if regret < 0:
                raise AssertionError(
                    f"{scenario.name}: holding {a} at its optimum reached a {b} score below "
                    f"{b}'s own optimum, which is impossible -- one of the two solves is wrong"
                )
            pairs[f"{a}->{b}"] = regret

    return {
        "own": own,
        "regret": pairs,
        "rosters_differ": len({solved[m][0] for m in METRICS}) > 1,
        "changes": {m: len(solved[m][0] ^ (instance.incumbent or frozenset())) for m in METRICS},
    }


def score_under(roster: Roster, instance: Instance, metric: str) -> int:
    """Disruption only, under `metric`. Coverage is identical across these rosters by
    construction -- the shortfall weight dominates every metric equally -- so the
    disruption component is the whole of the difference."""
    read = as_metric(instance, metric)
    assert not [v for v in check(roster, read) if not v.soft], "an illegal roster was scored"
    return disruption_of(roster, read)


def repair_slack(scenario: Scenario) -> int | None:
    """Spare eligible people at the slot the event actually damaged, not over the week.

    `D-060` says divergence needs slack, and the instance set records
    `Tightness.min_slot_slack` -- a minimum over all 21 slots. That is the wrong
    instrument for this question and the study says so: a week can hold one impossible
    slot and abundant room everywhere else, and the repair happens where the damage is.
    This is the local quantity, so the claim can be tested against something that could
    falsify it.

    `None` when the event damaged nothing, which the instance set already forbids.
    """
    instance = scenario.instance
    excluded = exclusions(instance)
    hit = {(k[1], k[2]) for k in scenario.incumbent if k in excluded}
    base = {(o.day, o.shift): o.required for o in scenario.base.open_shifts}
    grown = {
        (o.day, o.shift)
        for o in instance.open_shifts
        if o.required > base.get((o.day, o.shift), o.required)
    }
    slots = hit | grown
    if not slots:
        return None

    slacks = []
    for day, shift in slots:
        required = next(
            o.required for o in instance.open_shifts if (o.day, o.shift) == (day, shift)
        )
        eligible = sum(
            1
            for e in range(len(instance.employees))
            if (e, day, shift) not in excluded
        )
        slacks.append(eligible - required)
    return min(slacks)


def study(cases: list[str], *, seed: int = 7) -> dict:
    rows = {}
    for case in cases:
        scenario = suite.build(case)
        result = regrets(scenario, seed=seed)
        result["class"] = case.partition("/")[0]
        result["min_slot_slack"] = scenario.tightness.min_slot_slack
        result["repair_slack"] = repair_slack(scenario)
        result["tight_slots"] = scenario.tightness.tight_slots
        result["base_shortfall"] = scenario.base_shortfall
        result["damage"] = suite.entry(scenario)["damage"]
        rows[case] = result
    return {"generator_version": suite.GENERATOR_VERSION, "seed": seed, "cases": rows}


# --- Summary ------------------------------------------------------------------------


def _print(results: dict) -> None:
    rows = results["cases"]
    total = len(rows)

    print(f"\n=== regret matrix over {total} cases: rows commit to a, columns pay in b ===")
    print("cell = cases where committing to a costs something in b (mean regret)")
    print(f"\n{'a \\ b':10}" + "".join(f"{b:>14}" for b in METRICS))
    for a in METRICS:
        cells = []
        for b in METRICS:
            if a == b:
                cells.append(f"{'--':>14}")
                continue
            values = [r["regret"][f"{a}->{b}"] for r in rows.values()]
            hits = sum(1 for v in values if v > 0)
            mean = statistics.mean(v for v in values if v > 0) if hits else 0.0
            cells.append(f"{hits:>4}/{total} {mean:>6.1f}")
        print(f"{a:10}" + "".join(cells))

    for field, label in (("min_slot_slack", "week minimum"), ("repair_slack", "at the repair")):
        print(f"\n=== D2/D3 conflict against slack, {label} ===")
        buckets: dict[int, list[int]] = defaultdict(list)
        for r in rows.values():
            if r[field] is None:
                continue
            buckets[min(r[field], 6)].append(1 if r["regret"]["D2->D3"] > 0 else 0)
        print(f"{'slack':10}{'cases':>7}{'conflict':>10}")
        for slack in sorted(buckets):
            hits = sum(buckets[slack])
            name = f"{slack}" if slack < 6 else "6+"
            print(f"{name:10}{len(buckets[slack]):>7}{hits:>7}/{len(buckets[slack])}")

    print()
    by_class: dict[str, list[int]] = defaultdict(list)
    for r in rows.values():
        by_class[r["class"]].append(1 if r["regret"]["D2->D3"] > 0 else 0)
    print("=== D2/D3 conflict by class ===")
    for name in sorted(by_class, key=lambda k: -sum(by_class[k]) / len(by_class[k])):
        print(f"  {name:20}{sum(by_class[name])}/{len(by_class[name])}")

    agree = sum(1 for r in rows.values() if not any(v > 0 for v in r["regret"].values()))
    print(f"\ncases where all five metrics can agree: {agree}/{total}")
    differ = sum(1 for r in rows.values() if r["rosters_differ"])
    print(f"cases where the returned rosters merely differ: {differ}/{total} (see the docstring)")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--write", action="store_true", help="write metrics.json")
    parser.add_argument("--cases", nargs="*", default=None, help="case names, default all")
    args = parser.parse_args()

    results = study(args.cases or suite.case_names())
    _print(results)
    if args.write:
        METRICS_PATH.write_text(json.dumps(results, indent=2, sort_keys=True) + "\n")
        print(f"\nwrote {METRICS_PATH}")
