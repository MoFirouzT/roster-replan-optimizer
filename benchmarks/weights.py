"""Which soft weights a roster can actually tell you about.

    uv run python -m benchmarks.weights

Recovering a tenant's objective weights from what their planner changed is only possible
for weights the roster **responds to**. This module measures that set before anything tries
to learn it, because an estimator scored against unidentifiable parameters reports its own
prior and looks like a result.

## Three reasons a weight may not be recoverable, all of them already in this repo

**Scale invariance.** The argmin of a linear objective is unchanged when every weight is
multiplied by the same positive constant. So weights are recoverable at best *up to scale*,
which makes rank correlation the honest comparison and absolute error meaningless.

**Domination.** `shortfall_weight` must satisfy the bound in `replan.md` so that coverage
outranks every disruption term (`D-057`), and `validation.py` checks it rather than trusting
it. Above that bound every value behaves identically, so its magnitude carries no information
at all — only the fact that it clears the bound.

**A flat optimum.** `D-118` measured this model's objective as degenerate: many rosters shared
one objective value, and which came back was decided by the search. `D-119` fixed that by
minimising a canonical criterion over the optimal face, so the roster is now a function of the
model. That is what makes this measurement meaningful — without it, a roster changing between
two weights could be the solver rather than the weight — and it is also why a *band* of
weights can map to one roster rather than a point.

## What D2 leaves inert

The shipped metric is D2, and `scoring.disruption_of` sends D0-D2 through `_per_assignment`,
which prices a changed slot at `publication x notice`. So under D2 the objective never reads
`move_weight`, `cancel_weight`, `call_in_weight` or `concentration_weight` — those exist for
D3 and D4. A tenant on D2 cannot have those weights learned from their rosters at any sample
size, and that is a fact about the metric rather than about the estimator.
"""

from __future__ import annotations

import dataclasses

from benchmarks.generator import Scenario
from roster_replan.domain import (
    Disruption,
    Employee,
    Instance,
    Interval,
    OpenShift,
    RuleParams,
    ShiftType,
    shipped_d2,
)
from roster_replan.model import Unproven, solve

# The weights that enter a D2 objective, plus the two that price coverage and peak. Each is
# swept across a range wide enough to cross any plausible trade-off, not tweaked around the
# shipped value -- the question is whether the roster ever moves, not whether it moves a
# little.
D2_SWEEPS: dict[str, tuple[int, ...]] = {
    "published_weight": (1, 2, 5, 10, 20, 50, 100, 1_000),
    "draft_weight": (1, 2, 5, 10, 20, 50),
    "notice_multiplier": (1, 2, 4, 8, 16, 64),
    "peak_weight": (0, 1, 2, 5, 20, 100),
    "mix_shortfall_weight": (1_000, 10_000, 100_000, 1_000_000),
}

# The D3/D4 weights. Swept under a D3 profile on purpose: under D2 they are inert by
# construction, and a sweep showing "no effect" there would be reporting the metric rather
# than measuring identifiability.
EVENT_SWEEPS: dict[str, tuple[int, ...]] = {
    "move_weight": (1, 3, 6, 12, 30, 100),
    "cancel_weight": (1, 5, 10, 25, 60, 200),
    "call_in_weight": (1, 7, 14, 35, 80, 250),
}


def with_weight(params: Disruption, weight: str, value: int) -> Disruption:
    """The profile with one weight moved. `notice_multiplier` is the near band's factor.

    Handled by name rather than by `dataclasses.replace` alone because the notice schedule is
    a tuple of bands rather than a scalar, and the near band is the one a planner would
    argue about -- the far band is the `1` everything else is measured against.
    """
    if weight == "notice_multiplier":
        bands = params.notice_bands
        if not bands:
            raise ValueError("no notice bands to vary")
        near = dataclasses.replace(bands[0], multiplier=value)
        return dataclasses.replace(params, notice_bands=(near,) + tuple(bands[1:]))
    return dataclasses.replace(params, **{weight: value})


def _solve(instance: Instance, seed: int, time_limit: float):
    solution = solve(instance, seed=seed, time_limit=time_limit)
    if isinstance(solution, list) or isinstance(solution, Unproven):
        return None
    return solution.roster


def sweep_one(
    scenario: Scenario,
    weight: str,
    values: tuple[int, ...],
    *,
    metric: str | None = None,
    seed: int = 7,
    time_limit: float = 30.0,
) -> dict:
    """Distinct canonical rosters produced by moving one weight, holding the rest fixed.

    Marginal identifiability, which is the right first question: a weight that cannot move
    the roster on its own cannot be recovered from a roster on its own either.
    """
    instance = scenario.instance
    params = instance.disruption
    if params is None:
        raise ValueError("weight identifiability needs a disruption profile")
    if metric is not None:
        params = dataclasses.replace(params, metric=metric)

    rosters: dict[frozenset, list[int]] = {}
    unsolved = []
    for value in values:
        moved = with_weight(params, weight, value)
        roster = _solve(
            dataclasses.replace(instance, disruption=moved), seed, time_limit
        )
        if roster is None:
            unsolved.append(value)
            continue
        rosters.setdefault(roster, []).append(value)

    return {
        "case": scenario.name,
        "weight": weight,
        "metric": metric or params.metric,
        "values": list(values),
        "unsolved": unsolved,
        "distinct": len(rosters),
        # The bands themselves, so a reader can see whether the roster flips once at a
        # threshold or wanders -- a single flip is a boundary, and it is the only thing an
        # estimator could ever locate.
        "bands": sorted((sorted(v) for v in rosters.values()), key=lambda b: b[0]),
    }


def identifiable(row: dict) -> bool:
    """A weight is identifiable on a case when the roster answers to it at all."""
    return row["distinct"] > 1


# --- An instance built to contain the structure a weight could be read from -------------
# The same move `studies.identical_workforce` makes for symmetry, and for the same reason: a
# null measured only on the committed set cannot tell "this lever does nothing" apart from
# "this distribution never presents the lever with a choice". One of those is about the
# model and the other is about the generator, and only a purpose-built instance separates
# them.


def forced_choice(*, published_weight: int = 10, draft_weight: int = 1) -> Instance:
    """Two holes, one person free to fill exactly one of them.

    Deliberately unlike anything the generator produces. The absent employee held two
    shifts; the only other employee has budget for one. So exactly one hole stays open
    whatever happens, both candidate answers are one slot short, and **the shortfall term
    cancels** — which hands the choice to the disruption weights and nothing else.

    The two slots are built to differ on precisely the two factors D2 prices:

    | slot | published | notice | cost of filling it |
    | --- | --- | --- | --- |
    | day 2 | yes | 1 h, inside the near band | `published_weight x 4` |
    | day 5 | no | 73 h, outside it | `draft_weight x 1` |

    So the optimum fills whichever is cheaper to touch, and moving the weights across that
    boundary must move the roster. If it does not, the probe is broken rather than the
    distribution being flat.
    """
    shift = ShiftType(label="M", start_hour=7.0, span_hours=8.0, break_hours=0.5)
    absent = Employee(
        name="A",
        contract="salaried",
        skills=frozenset({"bar"}),
        unavailability=(),
        # Away for the whole week, so both of their shifts must be dropped.
        absences=(Interval(0.0, 7 * 24.0),),
        max_hours_this_week=38.0,
        max_daily_hours=8.0,
        consecutive_days_worked_before_horizon=0,
        last_shift_end_before_horizon=None,
    )
    # One shift's worth of budget, which is what makes the choice exclusive.
    spare = dataclasses.replace(absent, name="B", absences=(), max_hours_this_week=8.0)

    return Instance(
        days=7,
        shift_types=(shift,),
        employees=(absent, spare),
        open_shifts=(
            OpenShift(day=2, shift=0, required=1),
            OpenShift(day=5, shift=0, required=1),
        ),
        params=RuleParams(
            min_rest_hours=11.0,
            min_weekly_rest_hours=35.0,
            min_period_hours=3.0,
            max_consecutive_days=6,
        ),
        # Day 2 starts at hour 55 and day 5 at 127.
        now=54.0,  # one hour before day 2's shift, so it sits inside the 24 h band
        published_through=96.0,  # day 2 is published, day 5 is not
        incumbent=frozenset({(0, 2, 0), (0, 5, 0)}),
        disruption=shipped_d2(
            published_weight=published_weight, draft_weight=draft_weight
        ),
    )


# --- Recovery, on the one family where there is anything to recover ---------------------


def observe(near_multiplier: int, *, published_weight: int, draft_weight: int) -> int:
    """Which hole the planner left open, at a given near-band multiplier.

    This is the only thing an observer ever gets: a roster, not a weight. Filling day 2
    costs `published_weight x near_multiplier` and filling day 5 costs `draft_weight`, so
    the answer encodes one inequality between them and nothing more.
    """
    instance = forced_choice(published_weight=published_weight, draft_weight=draft_weight)
    params = with_weight(instance.disruption, "notice_multiplier", near_multiplier)
    roster = _solve(dataclasses.replace(instance, disruption=params), 7, 30.0)
    if roster is None:
        raise ValueError(f"no roster at multiplier {near_multiplier}")
    return sorted(day for _, day, _ in roster)[0]


def recover_ratio(
    *, published_weight: int, draft_weight: int, multipliers: tuple[int, ...]
) -> dict:
    """Recover `draft_weight / published_weight` from rosters alone, by where the answer flips.

    **What comes back is an interval, not a number, and that is the lesson rather than a
    shortcoming.** A roster is an argmin, so it reports one inequality between weighted
    terms. Every weight vector satisfying that inequality explains the observation equally
    well, and no amount of data collapses the interval to a point -- scaling every weight
    by a constant leaves every roster in the sample unchanged.

    The planner is only ever asked which hole they left open. The true weights are passed
    in to *generate* the observations and are never read by the estimator.
    """
    filled = {m: observe(m, published_weight=published_weight, draft_weight=draft_weight)
              for m in multipliers}

    # Day 2 is filled while published x m < draft, so the flip brackets the true ratio.
    prefers_published = sorted(m for m, day in filled.items() if day == 2)
    prefers_draft = sorted(m for m, day in filled.items() if day == 5)

    lower = max(prefers_published) if prefers_published else None
    upper = min(prefers_draft) if prefers_draft else None
    return {
        "true_ratio": draft_weight / published_weight,
        "observations": filled,
        "lower": lower,
        "upper": upper,
        "recovered": (lower, upper),
        "contains_truth": (
            (lower is None or lower <= draft_weight / published_weight)
            and (upper is None or draft_weight / published_weight <= upper)
        ),
    }


# --- The study ---------------------------------------------------------------------------
# No committed artifact, deliberately. The whole grid regenerates in about eleven seconds,
# so a JSON file would be a copy of this table that nothing reads and nothing keeps honest.
# `anneal-results.json` earns its place because rerunning it costs eighteen minutes and its
# foreign half cannot be regenerated at all (`D-125`); neither is true here.


def main() -> int:
    import collections

    from benchmarks import suite
    from benchmarks.anneal_study import CASES

    rows = []
    for name in CASES:
        scenario = suite.build(name)
        for weight, values in D2_SWEEPS.items():
            rows.append(sweep_one(scenario, weight, values))
        for weight, values in EVENT_SWEEPS.items():
            rows.append(sweep_one(scenario, weight, values, metric="D3"))

    counts = collections.defaultdict(lambda: [0, 0])
    for row in rows:
        bucket = counts[row["weight"], row["metric"]]
        bucket[0] += 1
        bucket[1] += int(identifiable(row))

    print(f"{'weight':>22} {'metric':>7} {'cases whose roster responds':>29}")
    for (weight, metric), (total, moved) in counts.items():
        print(f"{weight:>22} {metric:>7} {moved:>13}/{total:<15}")

    print("\nRecovering draft/published from rosters alone, on the forced-choice family:")
    print(f"{'true weights':>16} {'true ratio':>11} {'recovered':>14} {'brackets it':>12}")
    multipliers = (1, 2, 3, 4, 5, 6, 8, 10, 12, 16, 20, 30, 50)
    for published, draft in [(10, 1), (1, 1), (1, 10), (2, 20), (5, 50), (10, 100)]:
        found = recover_ratio(
            published_weight=published, draft_weight=draft, multipliers=multipliers
        )
        print(
            f"{f'{published}/{draft}':>16} {found['true_ratio']:>11.2f} "
            f"{str(found['recovered']):>14} {found['contains_truth']!s:>12}"
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
