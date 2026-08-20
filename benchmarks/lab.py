"""Paired measurement for the level-1 model studies.

Every study in `docs/archive/studies/` asks the same shape of question -- does changing one thing
about the model make it faster -- and at these instance sizes that question is hard to
answer honestly. A search takes about 3 ms. Process noise on a 3 ms measurement is a large
fraction of a 3 ms measurement, so an unpaired comparison of two means will find an effect
whenever the machine was busier during one half of the run.

Three rules, applied by every study through this module.

**Pair on the instance.** The comparison is always the same case solved both ways, and what
is reported is the distribution of per-case ratios. A ratio cancels everything about the
instance -- its size, its tightness, how hard it happens to be -- and leaves the change.

**Repeat, and take the minimum.** Each configuration is run `repeats` times on each case and
the *fastest* run is kept, not the mean. Wall-clock noise is one-sided: interference can
only make a run slower, never faster, so the minimum is the cleanest estimator of the
underlying cost. A mean over a noisy tail measures the machine.

**Report the sign test alongside the ratio.** How many cases got faster is a claim that
survives a noisy clock; a 4% mean improvement is not. With 72 paired cases, a lever that
helps on 60 of them is real and one that helps on 38 is not, whatever the means say.

The three quantities are kept apart, because at these sizes they do not move together and
one of them dominates:

- `build_seconds` -- constructing the CP-SAT model in Python. About 7 ms, and the largest.
- `search_seconds` -- CP-SAT's own wall time. About 3 ms.
- `variables` and `constraints` -- the model's size, which is noise-free and often the only
  thing a level-1 lever moves measurably at all.
"""

from __future__ import annotations

import dataclasses
import statistics
import time
from collections.abc import Callable

from ortools.sat.python import cp_model

from roster_replan.domain import Instance, Roster

# A configuration is a function that turns an instance into a built model, so a study can
# vary the encoding without this module knowing what it varied.
Builder = Callable[[Instance], object]


@dataclasses.dataclass(frozen=True, slots=True)
class Measured:
    """One configuration on one case: the best of `repeats` runs."""

    build_seconds: float
    search_seconds: float
    variables: int
    constraints: int
    objective: int
    status: str
    roster: Roster

    @property
    def total_seconds(self) -> float:
        return self.build_seconds + self.search_seconds


def measure(
    instance: Instance,
    builder: Builder,
    *,
    objective: Callable[[object, Instance], None],
    repeats: int = 5,
    seed: int = 7,
    time_limit: float = 30.0,
) -> Measured:
    """Build and solve `repeats` times, keeping the fastest of each phase.

    Build and search minima are taken independently. They are separate costs paid in
    sequence, and a run that was interrupted during the build tells us nothing about the
    search that followed it.
    """
    best_build = float("inf")
    best_search = float("inf")
    last = None

    for _ in range(repeats):
        started = time.perf_counter()
        built = builder(instance)
        objective(built, instance)
        best_build = min(best_build, time.perf_counter() - started)

        built.model.clear_assumptions()
        built.model.add_assumptions(built.literals)

        solver = cp_model.CpSolver()
        solver.parameters.num_workers = 1
        solver.parameters.random_seed = seed
        solver.parameters.max_time_in_seconds = time_limit

        status = solver.solve(built.model)
        best_search = min(best_search, solver.wall_time)
        last = (built, solver, status)

    built, solver, status = last
    proto = built.model.proto
    return Measured(
        build_seconds=best_build,
        search_seconds=best_search,
        variables=len(proto.variables),
        constraints=len(proto.constraints),
        objective=round(solver.objective_value) if status == cp_model.OPTIMAL else -1,
        status=solver.status_name(status),
        roster=frozenset(k for k, v in built.x.items() if solver.value(v)),
    )


# --- Comparing two configurations ---------------------------------------------------


@dataclasses.dataclass(frozen=True, slots=True)
class Comparison:
    """A paired A/B over a set of cases, on one quantity.

    `helped` and `hurt` are the sign test. `ratio_p50` is the median of the per-case
    ratios, treatment over control, so below 1 means the treatment is cheaper.
    """

    quantity: str
    cases: int
    ratio_p50: float
    ratio_p10: float
    ratio_p90: float
    helped: int
    hurt: int

    @property
    def verdict(self) -> str:
        """A plain reading, so a study cannot quietly round a null up into a win.

        The sign test is what decides. A lever helping on fewer than two thirds of paired
        cases is called a null however good its median ratio looks, because a median over
        a noisy clock is exactly what a lucky run produces.
        """
        decided = self.helped + self.hurt
        if decided == 0:
            return "no change at all"
        share = self.helped / decided
        if share < 2 / 3 and (self.hurt / decided) < 2 / 3:
            return "null -- no consistent direction"
        # Counts are not clocks. A model with fewer variables is smaller, not faster, and
        # saying "faster" about a variable count is how a size reduction gets quoted as a
        # speedup later.
        timed = self.quantity.endswith("seconds")
        better, worse = ("faster", "slower") if timed else ("smaller", "larger")
        direction = better if self.helped > self.hurt else worse
        size = abs(1 - self.ratio_p50)
        if size < 0.02:
            return f"consistently {direction}, but by under 2% -- not worth the complexity"
        return f"{direction} by {100 * size:.0f}% at the median"


def compare(
    control: dict[str, Measured], treatment: dict[str, Measured], quantity: str
) -> Comparison:
    """Pair two runs over the same case names and report the ratio distribution."""
    shared = sorted(set(control) & set(treatment))
    ratios = []
    helped = hurt = 0

    for case in shared:
        base = getattr(control[case], quantity)
        other = getattr(treatment[case], quantity)
        if base > 0:
            ratios.append(other / base)
        if other < base:
            helped += 1
        elif other > base:
            hurt += 1

    ordered = sorted(ratios)
    return Comparison(
        quantity=quantity,
        cases=len(shared),
        ratio_p50=statistics.median(ordered) if ordered else float("nan"),
        ratio_p10=ordered[int(0.1 * len(ordered))] if ordered else float("nan"),
        ratio_p90=ordered[int(0.9 * len(ordered))] if ordered else float("nan"),
        helped=helped,
        hurt=hurt,
    )


def report(name: str, control: dict, treatment: dict, quantities=None) -> list[Comparison]:
    # `total_seconds` is last and is the one that decides. A lever that shrinks the search
    # while growing the model has not obviously won, and at these sizes the build is the
    # larger of the two -- so a study reporting only `search_seconds` can show a 23%
    # improvement in the half that costs less and call it a result.
    quantities = quantities or (
        "variables",
        "constraints",
        "build_seconds",
        "search_seconds",
        "total_seconds",
    )
    print(f"\n=== {name} ===")
    print(f"{'quantity':18}{'cases':>7}{'ratio p50':>11}{'helped':>9}{'hurt':>7}  verdict")
    rows = []
    for quantity in quantities:
        row = compare(control, treatment, quantity)
        rows.append(row)
        print(
            f"{row.quantity:18}{row.cases:>7}{row.ratio_p50:>11.3f}"
            f"{row.helped:>9}{row.hurt:>7}  {row.verdict}"
        )
    return rows


def agree(control: dict[str, Measured], treatment: dict[str, Measured]) -> list[str]:
    """Cases where the two configurations disagreed about the optimal objective.

    **The first thing every study checks.** A level-1 lever is supposed to change how the
    model is expressed and not what it means, so a different optimum is a bug in the
    encoding rather than a result about it -- and a broken encoding is usually the fast
    one, which is how a wrong answer gets written up as a win.
    """
    return [
        case
        for case in sorted(set(control) & set(treatment))
        if control[case].objective != treatment[case].objective
    ]
