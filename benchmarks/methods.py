"""The four methods compared, and the one yardstick all four are scored on.

They are: cold cost-objective re-solve, greedy nearest-eligible repair, cold
disruption-objective solve, warm-started replan. Each isolates one thing.

| Method | Objective it optimises | Hint |
| --- | --- | --- |
| `cold-cost` | cost, disruption weights zeroed | none |
| `greedy` | none -- it is not an optimiser | starts from the incumbent |
| `cold-disruption` | the shipped D2 profile | none |
| `warm-replan` | the shipped D2 profile | the incumbent |

**Every method is scored on the same yardstick**, which is the shipped D2 profile carried
by the scenario, whatever the method itself optimised. Scoring a method under its own
objective would make the comparison a tautology -- each method wins the axis it was
pointed at, and the table says nothing.

**The two baselines separate two effects.** `replan.md` is explicit that a warm-started
replan beats a cold cost solve for two independent reasons -- the objective has its
optimum near the incumbent, and the hint starts the search there. `cold-disruption` is
the only thing that tells them apart, and without it a warm-start speedup claim is
measuring the objective.

## What `cold-cost` actually is

The status quo, expressed inside this model rather than as a second formulation: the same
instance, with the incumbent still attached so the past stays pinned and the horizon
accounting matches, and with every change weight set to zero so nothing prices deviation.
Attaching the incumbent is what makes the comparison legal -- dropping it would unpin the
past, and a "baseline" free to reassign shifts that have already started is not a baseline
for anything.

**It is indifferent, and that is the finding rather than a defect.** The cost model is a
flat rate (`D-050`), coverage is an equality with a hard ceiling, so every fully staffed
roster costs the same and CP-SAT returns whichever it reaches first. A real cost objective
behaves the same way -- cost has no opinion about *who* works. So the disruption this
method scores is a property of the solver's search order, and reporting one seed's number
as "the cost baseline's disruption" would be reporting an accident. `run` takes a solver
seed for exactly this reason. Measured, it moves by a median of 80 disruption points across
three seeds on the same case, where the disruption methods move by zero (`D-080`).

## What `greedy` actually is

See `roster_replan/repair.py`, which is a separate module so that an import-linter contract can hold it
to being solver-free. That is the property that makes it a baseline rather than a second
opinion from the same source.
"""

from __future__ import annotations

import dataclasses
import time

from benchmarks.generator import Scenario
from roster_replan.checker import check
from roster_replan.domain import Disruption, Instance, Roster
from roster_replan.model import Unproven, solve
from roster_replan.repair import repair
from roster_replan.scoring import disruption_of, score

COLD_COST = "cold-cost"
GREEDY = "greedy"
COLD_DISRUPTION = "cold-disruption"
WARM_REPLAN = "warm-replan"

METHODS = (COLD_COST, GREEDY, COLD_DISRUPTION, WARM_REPLAN)


@dataclasses.dataclass(frozen=True, slots=True)
class Outcome:
    """One method on one case, on the common yardstick.

    `disruption` is the weighted D2 score; `changes` is the raw count of assignments that
    differ from the incumbent. Both are reported because they answer different questions:
    the weighted number is what the objective minimises, and the count is what a planner
    recognises. A method can improve one and worsen the other, and hiding that behind a
    single number is how a weighting gets to look like a result.

    `paid_hours` carries the cost axis. It is computed directly rather than read off
    `Score.cost`, which is zero throughout because `cost_weight` ships at 0 (`D-050`) --
    a column of zeros would report the weight, not the cost.

    `seconds` is end-to-end -- building the model in Python and then searching.
    `search_seconds` is CP-SAT's own wall time. Both are reported because they answer
    different questions and, at these instance sizes, they are the same order of magnitude: an
    end-to-end number alone would say the four methods are equally fast, which is true
    and is a fact about the model builder rather than about any method. Greedy has no
    search, so its `search_seconds` is zero and its end-to-end number is the whole story.
    """

    method: str
    case: str
    seed: int
    time_limit: float
    seconds: float
    search_seconds: float
    status: str
    disruption: int
    changes: int
    short_slots: int
    paid_hours: float
    violations: tuple[tuple, ...]

    # The roster itself, so a caller can re-score it independently rather than trust the
    # summary fields above. `run.py` drops it before writing results: 720 rosters is a
    # results file nobody opens, and the case name plus the seed reproduces any of them.
    roster: Roster | None = None

    @property
    def solved(self) -> bool:
        return self.status not in ("INFEASIBLE", "UNKNOWN")

    def roster_or_fail(self) -> Roster:
        if self.roster is None:
            raise AssertionError(f"{self.method} returned no roster on {self.case}")
        return self.roster


def run(
    method: str, scenario: Scenario, *, seed: int = 7, time_limit: float = 30.0
) -> Outcome:
    """One method on one scenario, timed and scored."""
    if method not in METHODS:
        raise KeyError(f"unknown method {method!r}; expected one of {METHODS}")

    started = time.perf_counter()
    roster, status, search_seconds = _dispatch(
        method, scenario, seed=seed, time_limit=time_limit
    )
    seconds = time.perf_counter() - started

    return _measure(
        method,
        scenario,
        roster,
        status,
        seed=seed,
        time_limit=time_limit,
        seconds=seconds,
        search_seconds=search_seconds,
    )


def _dispatch(
    method: str, scenario: Scenario, *, seed: int, time_limit: float
) -> tuple[Roster | None, str, float]:
    if method == GREEDY:
        return repair(scenario.instance, scenario.incumbent), "GREEDY", 0.0

    instance = scenario.instance
    hint = None
    if method == COLD_COST:
        instance = dataclasses.replace(instance, disruption=cost_profile(instance))
    elif method == WARM_REPLAN:
        hint = scenario.incumbent

    solution = solve(instance, seed=seed, time_limit=time_limit, hint=hint)
    if isinstance(solution, list):
        return None, "INFEASIBLE", 0.0
    if isinstance(solution, Unproven):
        # Not the same as infeasible, and recording it as such would put a timeout in the
        # benchmark as a proof. Never reached at these sizes; kept correct anyway.
        return None, solution.status, solution.search_seconds
    return solution.roster, solution.status, solution.search_seconds


def _measure(
    method: str,
    scenario: Scenario,
    roster: Roster | None,
    status: str,
    *,
    seed: int,
    time_limit: float,
    seconds: float,
    search_seconds: float,
) -> Outcome:
    """Score on the scenario's own profile, never on the one the method optimised."""
    instance = scenario.instance
    if roster is None:
        return Outcome(
            method=method,
            case=scenario.name,
            seed=seed,
            time_limit=time_limit,
            seconds=seconds,
            search_seconds=search_seconds,
            status=status,
            disruption=0,
            changes=0,
            short_slots=0,
            paid_hours=0.0,
            violations=(),
        )

    measured = score(roster, instance)
    hard = tuple(v.key() for v in check(roster, instance) if not v.soft)

    return Outcome(
        method=method,
        case=scenario.name,
        seed=seed,
        time_limit=time_limit,
        seconds=seconds,
        search_seconds=search_seconds,
        status=status,
        disruption=disruption_of(roster, instance),
        changes=len(roster ^ (instance.incumbent or frozenset())),
        short_slots=measured.shortfall // max(1, instance.disruption.shortfall_weight),
        paid_hours=paid_hours(roster, instance),
        violations=hard,
        roster=roster,
    )


def paid_hours(roster: Roster, instance: Instance) -> float:
    """The cost axis, as `replan.md` says to read it until wage data arrives: paid hours,
    rate-weighted where a rate is supplied, not euros."""
    total = 0.0
    for employee, _, shift in roster:
        rate = instance.employees[employee].hourly_rate
        total += instance.shift_types[shift].work_hours * (1.0 if rate is None else rate)
    return total


def cost_profile(instance: Instance) -> Disruption:
    """The shipped profile with every change weight zeroed and cost switched on.

    Zeroing rather than removing: the metric stays D2 and the shortfall weight stays
    dominant, so the baseline solves the same model under the same coverage priority and
    differs in exactly one thing -- that deviation from the incumbent is free.
    """
    params = instance.disruption
    if params is None:
        raise ValueError("a cost baseline needs the scenario's disruption profile")
    return dataclasses.replace(
        params,
        published_weight=0,
        draft_weight=0,
        move_weight=0,
        cancel_weight=0,
        call_in_weight=0,
        concentration_weight=0,
        cost_weight=1,
    )
