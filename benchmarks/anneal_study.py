"""The comparison behind the penalty-search study: exact against priced rules.

    uv run python -m benchmarks.anneal_study --set committed
    uv run python -m benchmarks.anneal_study --set foreign --instance 8

Separate from [`anneal.py`](anneal.py) because that module carries an import contract
holding it solver-free, and a comparison needs both sides. Same split as `repair.py` against
`methods.py`, for the same reason.

## What is being measured

`D-002` refuses penalties for hard rules on the grounds that they produce a roster that is
*cheaply illegal*. Three questions follow from that sentence and this runner answers all
three:

1. **The illegal-roster rate**, by penalty weight and by budget. The deliverable.
2. **Whether an illegal roster scores better** than the proven optimum on the shared D2
   yardstick. If it does, the objective column of a benchmark table ranks the unsafe method
   first, and only the violations column says otherwise.
3. **What legality costs when the weight is raised until it is safe** — the D2 gap against
   the optimum, which is the other half of "no weight is both safe and effective".

## The sample is named, not sliced (`D-107`)

One seed per class, listed literally below. `studies.py` learned this the hard way: a
positional sample over a set people add classes to silently swapped two cases out, and two
results moved in a way that read exactly like a finding. Six seeds of one class measure the
same structure six times; fourteen classes are what vary it.
"""

from __future__ import annotations

import argparse
import dataclasses
import json
import pathlib
import time

from benchmarks import anneal, methods, suite
from roster_replan.checker import check
from roster_replan.domain import Instance, Roster
from roster_replan.scoring import disruption_of, score

# One per class, named. See the module docstring.
CASES = (
    "headline/0",
    "loose/0",
    "tight/0",
    "busy/0",
    "overloaded/0",
    "small/0",
    "large/0",
    "scarce-skill/0",
    "flexi-heavy/0",
    "thin-availability/0",
    "multi-absence/0",
    "demand-spike/0",
    "withdrawal/0",
    "early-notice/0",
)

RESULTS = pathlib.Path(__file__).parent / "anneal-results.json"


def _measure(roster: Roster, instance: Instance, inherited: frozenset = frozenset()) -> dict:
    """Both readings of quality, plus the legality verdict, from the independent checker.

    `introduced` is the count this study has to lead with, and separating it from `hard` is
    not bookkeeping. **An incumbent can arrive illegal**: `D-125` found that 7 of 13 published
    foreign rosters have a past this model calls illegal, and instance 8's incumbent carries
    five hard violations before any search touches it. A raw count would credit the method
    with those, and the claim under test is about what pricing a rule *causes*, not about what
    it was handed.

    On the committed set the two are nearly the same number, because a generated incumbent is
    legal apart from the damage the event did. On the foreign set they are not, which is
    exactly the kind of thing a synthetic distribution cannot show you.
    """
    measured = score(roster, instance)
    hard = [v.key() for v in check(roster, instance) if not v.soft]
    fresh = [key for key in hard if key not in inherited]
    return {
        "total": measured.total,
        "disruption": disruption_of(roster, instance),
        "shortfall": measured.shortfall,
        "hard": len(hard),
        "introduced": len(fresh),
        "rules": sorted({key[0] for key in hard}),
        "rules_introduced": sorted({key[0] for key in fresh}),
    }


def one_case(
    scenario,
    *,
    weights: tuple[int, ...],
    budgets: tuple[int, ...],
    seeds: tuple[int, ...],
    time_limit: float,
    trace: bool = False,
) -> dict:
    """The exact answer, then the priced-rules answers across the grid."""
    instance = scenario.instance

    # What the incumbent was already breaking, so the search is charged only for what it
    # broke itself. Taken before anything runs, from the same independent reading.
    inherited = frozenset(
        v.key() for v in check(scenario.incumbent, instance) if not v.soft
    )

    started = time.perf_counter()
    exact = methods.run("warm-replan", scenario, seed=7, time_limit=time_limit)
    exact_seconds = time.perf_counter() - started

    reference = None
    if exact.roster is not None:
        reference = _measure(exact.roster, instance, inherited)

    runs = []
    for weight in weights:
        for budget in budgets:
            for seed in seeds:
                result = anneal.anneal(
                    instance,
                    scenario.incumbent,
                    hard_weight=weight,
                    evaluations=budget,
                    seed=seed,
                )
                measured = _measure(result.roster, instance, inherited)
                runs.append(
                    {
                        "hard_weight": weight,
                        "evaluations": budget,
                        "seed": seed,
                        "seconds": round(result.seconds, 3),
                        "accepted": result.accepted,
                        "accepted_illegal": result.accepted_illegal,
                        **measured,
                        # The finding question 2 asks, recorded per run rather than derived
                        # later: did priced rules buy a better score than the optimum?
                        "beats_optimum": (
                            reference is not None and measured["total"] < reference["total"]
                        ),
                        # Kept only when asked. The three budgets are already an anytime
                        # curve, and a better one -- independent runs rather than one
                        # trajectory's best-so-far. A per-run trace is 100 samples that no
                        # finding reads, and at 210 runs it was 96% of a 3.2 MB file.
                        # `run.py` drops the roster from `results.json` on exactly this
                        # reasoning: the case name and the seed reproduce it.
                        **(
                            {"trace": [dataclasses.asdict(s) for s in result.trace]}
                            if trace
                            else {}
                        ),
                    }
                )

    return {
        "case": scenario.name,
        "status": exact.status,
        "exact_seconds": round(exact_seconds, 3),
        "exact_search_seconds": round(exact.search_seconds, 4),
        "exact": reference,
        "inherited": len(inherited),
        "incumbent": _measure(scenario.incumbent, instance),
        "runs": runs,
    }


def summarise(cases: list[dict]) -> list[dict]:
    """The headline table: illegal rate and D2 gap, by weight and budget."""
    grid: dict[tuple[int, int], list] = {}
    for case in cases:
        for run in case["runs"]:
            grid.setdefault((run["hard_weight"], run["evaluations"]), []).append(
                (run, case["exact"])
            )

    rows = []
    for (weight, budget), pairs in sorted(grid.items()):
        # **`hard > 0` is the deliverable, not `introduced > 0`.** A service returning a
        # roster that breaks a hard rule has returned an illegal roster, and it does not
        # matter to the person holding it whether the search created the violation or
        # declined to repair one it was handed. The first version of this function led with
        # `introduced` and scored a search that returned the incumbent untouched -- absence
        # and all -- as legal, which inverted the headline: leaving the damage in place is
        # the *cheapest* way to buy your way out of a priced rule, and it read as a clean run.
        #
        # `introduced` stays, one column over, because it separates two different failures:
        # a search that breaks new rules, and one that simply never fixes anything.
        illegal = [run for run, _ in pairs if run["hard"] > 0]
        fresh = [run for run, _ in pairs if run["introduced"] > 0]
        unrepaired = [
            run for run, _ in pairs if run["hard"] > 0 and run["introduced"] == 0
        ]
        cheated = [run for run, _ in pairs if run["beats_optimum"] and run["hard"] > 0]
        # The gap is only defined where the exact solve produced an optimum to gap against,
        # and only meaningful on the legal runs -- an illegal roster's score is not a
        # quality number, it is the price of the rule it broke.
        gaps = [
            run["total"] - exact["total"]
            for run, exact in pairs
            if exact is not None and run["hard"] == 0
        ]
        rows.append(
            {
                "hard_weight": weight,
                "evaluations": budget,
                "runs": len(pairs),
                "illegal": len(illegal),
                "illegal_rate": round(len(illegal) / len(pairs), 3),
                "introduced_new": len(fresh),
                "left_unrepaired": len(unrepaired),
                "worst_introduced": max((r["introduced"] for r, _ in pairs), default=0),
                "illegal_and_better_scoring": len(cheated),
                "legal_runs": len(gaps),
                "mean_gap": round(sum(gaps) / len(gaps), 1) if gaps else None,
                "matched_optimum": sum(1 for g in gaps if g <= 0),
            }
        )
    return rows


def main() -> int:
    parser = argparse.ArgumentParser(description="Penalty search against the exact model")
    parser.add_argument("--set", choices=("committed", "foreign"), default="committed")
    parser.add_argument("--instance", type=int, default=8, help="foreign instance number")
    parser.add_argument("--budgets", type=int, nargs="+", default=list(anneal.BUDGETS))
    parser.add_argument("--weights", type=int, nargs="+", default=list(anneal.WEIGHTS))
    parser.add_argument("--seeds", type=int, nargs="+", default=[7])
    parser.add_argument("--time-limit", type=float, default=30.0)
    parser.add_argument(
        "--trace",
        action="store_true",
        help="keep the per-run anytime samples; off by default because the budget axis "
        "already carries the curve and the samples dominate the file",
    )
    parser.add_argument("--out", type=pathlib.Path, default=RESULTS)
    args = parser.parse_args()

    if args.set == "foreign":
        from benchmarks import foreign

        scenarios = [foreign.scenario(args.instance)]
    else:
        scenarios = [suite.build(name) for name in CASES]

    cases = []
    for scenario in scenarios:
        started = time.perf_counter()
        case = one_case(
            scenario,
            weights=tuple(args.weights),
            budgets=tuple(args.budgets),
            seeds=tuple(args.seeds),
            time_limit=args.time_limit,
            trace=args.trace,
        )
        cases.append(case)
        worst = max(run["introduced"] for run in case["runs"])
        print(
            f"{scenario.name:<28} exact={case['status']:<9} "
            f"illegal={sum(1 for r in case['runs'] if r['introduced'] > 0)}/{len(case['runs'])} "
            f"worst_hard={worst:<3} {time.perf_counter() - started:6.1f}s",
            flush=True,
        )

    payload = {"cases": cases, "summary": summarise(cases)}
    args.out.write_text(json.dumps(payload, indent=2))

    print(f"\n{'weight':>10} {'evals':>8} {'illegal':>9} {'rate':>6} {'new':>4} "
          f"{'unrep':>6} {'illegal&better':>15} {'mean_gap':>10} {'matched':>8}")
    for row in payload["summary"]:
        gap = "-" if row["mean_gap"] is None else f"{row['mean_gap']:.1f}"
        print(
            f"{row['hard_weight']:>10} {row['evaluations']:>8} "
            f"{row['illegal']:>4}/{row['runs']:<4} {row['illegal_rate']:>6} "
            f"{row['introduced_new']:>4} {row['left_unrepaired']:>6} "
            f"{row['illegal_and_better_scoring']:>15} {gap:>10} "
            f"{row['matched_optimum']:>3}/{row['legal_runs']:<4}"
        )
    print(f"\nwritten to {args.out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
