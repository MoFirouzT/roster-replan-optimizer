"""The sweep: every method, over every committed case, at a stated time budget.

    uv run python -m benchmarks.run                    # summary to stdout
    uv run python -m benchmarks.run --write            # and results.json

`results.json` holds raw per-run rows rather than the summary table, because the summary
embeds analysis decisions -- which cases to segment, which to exclude -- that
`benchmarks.md` argues for and that a reader has to be able to redo differently.

**It is not committed** (`D-084`), and that is the one place this file departs from how the
instance set is handled. The manifest is committed because a fingerprint is exact and a
change to it means something. A row here carries wall-clock milliseconds, so it changes on
every run and on every machine, and a 750 KB diff that always changes is a diff nobody
reads -- the failure `D-067` is the standing lesson about. What is committed is the
analysis in `benchmarks.md`, the hardware it was taken on, and the command above.

**Every solver method runs at several solver seeds.** For `cold-cost` that is essential
rather than tidy: it is indifferent among fully staffed rosters (see `methods.py`), so one
seed's disruption is an accident of search order and reporting it alone would be reporting
noise as a result. Running the disruption methods across the same seeds costs little and
answers the obvious objection, which is whether their advantage is also a seed.
"""

from __future__ import annotations

import argparse
import dataclasses
import json
import pathlib
import statistics

from benchmarks import methods, suite
from benchmarks.generator import Scenario

RESULTS_PATH = pathlib.Path(__file__).with_name("results.json")

# Solver seeds. Three, not one: enough to show a spread, cheap enough to run the whole
# set at every time budget.
SOLVER_SEEDS = (7, 11, 13)

# The budgets the quality curve is drawn at (`studies/time-budget.md`).
BUDGETS = (1.0, 5.0, 30.0)


def sweep(
    cases: list[str], *, time_limit: float, seeds: tuple[int, ...] = SOLVER_SEEDS
) -> list[methods.Outcome]:
    outcomes: list[methods.Outcome] = []
    for case in cases:
        scenario = suite.build(case)
        for method in methods.METHODS:
            # Greedy has no solver and therefore no solver seed. Running it three times
            # would report the same roster three times and quietly triple its weight in
            # any average taken over rows.
            for seed in (seeds if method != methods.GREEDY else seeds[:1]):
                outcome = methods.run(
                    method, scenario, seed=seed, time_limit=time_limit
                )
                outcomes.append(dataclasses.replace(outcome, case=case))
    return outcomes


def row(outcome: methods.Outcome) -> dict:
    """One run as a JSON-able row. The roster is dropped: 720 of them is a results file
    nobody opens, and a case name with a seed reproduces any one of them exactly."""
    fields = dataclasses.asdict(outcome)
    fields.pop("roster")
    fields["violations"] = [list(v) for v in outcome.violations]
    return fields


def facts(case: str, scenario: Scenario) -> dict:
    """The per-case facts the analysis segments on, carried alongside the runs so the
    results file can be read without regenerating all 72 instances."""
    return {
        "class": case.partition("/")[0],
        "event": scenario.params.event,
        "employees": scenario.params.employees,
        "open_shifts": len(scenario.instance.open_shifts),
        "incumbent_size": len(scenario.incumbent),
        "base_shortfall": scenario.base_shortfall,
        "damage": suite.entry(scenario)["damage"],
        "short_slots": scenario.tightness.short_slots,
    }


def collect(cases: list[str], budgets: tuple[float, ...]) -> dict:
    runs = []
    for budget in budgets:
        runs += [row(o) for o in sweep(cases, time_limit=budget)]
    return {
        "generator_version": suite.GENERATOR_VERSION,
        "solver_seeds": list(SOLVER_SEEDS),
        "budgets": list(budgets),
        "cases": {case: facts(case, suite.build(case)) for case in cases},
        "runs": runs,
    }


# --- Summary ------------------------------------------------------------------------
# Printed, never committed. See the module docstring.


def _percentile(values: list[float], fraction: float) -> float:
    ordered = sorted(values)
    if not ordered:
        return float("nan")
    index = min(len(ordered) - 1, int(fraction * len(ordered)))
    return ordered[index]


def summarise(results: dict, *, budget: float, segment: str = "all") -> list[dict]:
    """One row per method, over the cases the segment admits.

    Segments, per `benchmarks.md`: `clean` is the repair question -- a week that was fully
    staffable before the event. `short` is the capacity question. They are never pooled,
    because averaging them produces a number that answers neither.
    """
    cases = results["cases"]

    def admits(case: str) -> bool:
        if segment == "all":
            return True
        short = cases[case]["base_shortfall"] > 0
        return short if segment == "short" else not short

    rows = []
    for method in methods.METHODS:
        # Greedy is budget-independent -- it does not search, so a time limit means
        # nothing to it -- but its rows are still filtered by budget rather than pooled
        # across all three. Pooling would triple its weight against methods filtered to
        # one budget, and print a run count three times the number of cases.
        picked = [
            r
            for r in results["runs"]
            if r["method"] == method and admits(r["case"]) and r["time_limit"] == budget
        ]
        if not picked:
            continue
        times = [r["seconds"] for r in picked]
        searches = [r["search_seconds"] for r in picked]
        rows.append(
            {
                "method": method,
                "runs": len(picked),
                "p50_ms": 1000 * _percentile(times, 0.50),
                "p95_ms": 1000 * _percentile(times, 0.95),
                "search_p50_ms": 1000 * _percentile(searches, 0.50),
                "search_p95_ms": 1000 * _percentile(searches, 0.95),
                "disruption": statistics.mean(r["disruption"] for r in picked),
                "changes": statistics.mean(r["changes"] for r in picked),
                "short_slots": statistics.mean(r["short_slots"] for r in picked),
                "paid_hours": statistics.mean(r["paid_hours"] for r in picked),
                "optimal": sum(1 for r in picked if r["status"] == "OPTIMAL"),
            }
        )
    return rows


def _print(results: dict) -> None:
    for budget in results["budgets"]:
        for segment in ("clean", "short"):
            rows = summarise(results, budget=budget, segment=segment)
            print(f"\n=== budget {budget:g}s · segment {segment} ===")
            print(
                f"{'method':18}{'runs':>6}{'p50 ms':>9}{'p95 ms':>9}"
                f"{'srch p50':>10}{'srch p95':>10}"
                f"{'disruption':>12}{'changes':>9}{'short':>8}{'paid h':>9}"
            )
            for row in rows:
                print(
                    f"{row['method']:18}{row['runs']:>6}{row['p50_ms']:>9.1f}"
                    f"{row['p95_ms']:>9.1f}{row['search_p50_ms']:>10.2f}"
                    f"{row['search_p95_ms']:>10.2f}{row['disruption']:>12.1f}"
                    f"{row['changes']:>9.2f}{row['short_slots']:>8.2f}"
                    f"{row['paid_hours']:>9.1f}"
                )


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--write", action="store_true", help="write results.json")
    parser.add_argument(
        "--budgets",
        type=float,
        nargs="+",
        default=list(BUDGETS),
        help="time budgets in seconds",
    )
    parser.add_argument("--cases", nargs="*", default=None, help="case names, default all")
    args = parser.parse_args()

    cases = args.cases or suite.case_names()
    results = collect(cases, tuple(args.budgets))
    _print(results)
    if args.write:
        RESULTS_PATH.write_text(json.dumps(results, indent=2, sort_keys=True) + "\n")
        print(f"\nwrote {RESULTS_PATH} ({len(results['runs'])} runs)")
