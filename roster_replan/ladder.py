"""The fallback ladder: exact, time-boxed with the gap reported, greedy, last known good.

`service.md`'s rule is **never return nothing**. A planner whose Saturday just fell apart is
not served by `INFEASIBLE`, and a solver that answers only when it can answer perfectly is a
solver that answers rarely. So each rung is a weaker promise than the one above it, every
rung says which one it is, and the answer carries what it cost.

This module is deliberately importable **without the web layer**. `service.md` asks for the
boundary to stay boring and the intricate part to stay small and heavily tested, and the
ladder is the intricate part. It knows nothing about HTTP, jobs or queues.

## The rungs

| Rung | Promise | Reached when |
| --- | --- | --- |
| `exact` | proven optimal, gap 0 | the solve finished inside its budget |
| `time-boxed` | feasible, **gap reported** | the budget ran out with a solution in hand |
| `greedy` | legal, not optimal | the model had no solution to give |
| `incumbent` | what was already published, violations named | greedy had nothing to repair from |

**`exact` and `time-boxed` are one solve, not two.** CP-SAT already returns the best
solution found plus the best proven bound when a time limit stops it, so re-solving with a
smaller budget to "try the fast rung first" would spend the budget twice to learn the same
thing. Which rung a solve landed on is read from its outcome rather than chosen in advance.

## Two honest limits, stated rather than discovered later

**The lower rungs are replan-only.** Greedy repairs an incumbent and last-known-good returns
one, so neither exists for a cold generation solve. "Never return nothing" is a promise about
replanning, which is what the service is for, and it is not a promise the cold path can keep.

There is a second half to that, and it narrows what can go wrong rather than widening it:
**a cold solve is never infeasible.** The coverage floor is soft and the ceiling is satisfied
by assigning nobody, so the empty roster meets every hard constraint and impossible demand
comes back priced rather than refused. That is `D-018` arriving somewhere it was not aimed.
The only way a cold solve fails is by running out of budget, so the cold branch below reads
`Unproven` and never a core. Asserted in `tests/test_ladder.py` rather than assumed, because
if the coverage floor ever hardens this reasoning silently stops holding.

**The incumbent rung can return an illegal roster, on purpose.** After a disruption the
published roster is usually *already* broken -- that is what triggered the replan. Returning
it silently would be the worst outcome in this module, so that rung returns the violations
alongside it and marks the answer as the floor rather than a repair.

## Reaching the middle rungs at all

No instance in the committed benchmark set takes more than 12.4 ms to prove optimality, so
the `time-boxed` rung is never reached by a real payload and would ship untested on the
strength of a code review. Every rung is therefore reachable by construction through
`budget_seconds`, and `tests/test_ladder.py` forces each one.
"""

from __future__ import annotations

import time
from dataclasses import dataclass, field

from .checker import check
from .domain import Instance, Roster
from .model import Gate, Solution, Unproven, solve
from .repair import repair

EXACT = "exact"
TIME_BOXED = "time-boxed"
GREEDY = "greedy"
INCUMBENT = "incumbent"

# Descending strength. A rung's index is how far the answer fell, which is the number
# `service.md` wants aggregated as a fallback rate.
RUNGS = (EXACT, TIME_BOXED, GREEDY, INCUMBENT)


@dataclass(frozen=True, slots=True)
class Answer:
    """What the ladder returns, and everything needed to judge it.

    There is no `success` flag. Every field a caller would use to decide whether to trust
    this is present -- the rung, the gap, the violations -- and collapsing them into a
    boolean would be the service deciding on the caller's behalf what "good enough" means.
    """

    roster: Roster
    rung: str
    reason: str
    seconds: float

    objective: int | None = None
    gap: float | None = None
    shortfall: int = 0

    # Hard violations in the returned roster, from the independent checker. Normally
    # empty; non-empty only on the `incumbent` rung, where it is the point.
    violations: tuple[tuple, ...] = ()

    # The conflicting rule instances, when the exact rung proved infeasibility. This is
    # what T4's explainer consumes, and it is kept even when a lower rung then answered:
    # the fallback says what to do now, the core says what is actually wrong.
    core: tuple[Gate, ...] = ()

    attempts: tuple[str, ...] = field(default_factory=tuple)

    @property
    def degraded(self) -> bool:
        return self.rung != EXACT

    @property
    def trustworthy(self) -> bool:
        """A legal roster, whatever rung produced it. The `incumbent` rung is the only one
        that can fail this, and it fails it by design."""
        return not self.violations


def answer(
    instance: Instance,
    *,
    seed: int = 7,
    budget_seconds: float = 30.0,
    workers: int = 1,
    built=None,
) -> Answer:
    """Solve, and fall back rather than fail. Never raises for an unsolvable instance.

    `built` is an optional pre-built model from `compiled.ModelCache`. The ladder does not
    own the cache and does not create one: caching policy is a deployment concern, and a
    module that silently memoised across calls would make a solver that is supposed to be
    replayable depend on what it was asked before.
    """
    started = time.perf_counter()
    attempts: list[str] = []

    outcome = solve(
        instance, seed=seed, time_limit=budget_seconds, workers=workers, built=built
    )

    if isinstance(outcome, Solution):
        attempts.append(EXACT if outcome.status == "OPTIMAL" else TIME_BOXED)
        return _from_solve(instance, outcome, started, attempts)

    attempts.append(EXACT)

    # Two different failures, and the ladder falls the same way for both while saying
    # different things about why. `Unproven` carries no core because none was proved --
    # writing "the conflicting rules are" over an empty tuple is the specific lie this
    # distinction exists to prevent.
    exhausted = isinstance(outcome, Unproven)
    core = () if exhausted else tuple(outcome)
    blame = (
        f"the search ran out of its {budget_seconds:g}s budget without finding any roster"
        if exhausted
        else "no legal roster exists"
    )
    incumbent = instance.incumbent

    if incumbent is None:
        # Cold, and nothing to fall back to. The ladder does not invent a roster it has no
        # basis for, and an empty one would satisfy "never return nothing" by lying.
        attempts.append(GREEDY)
        return Answer(
            roster=frozenset(),
            rung=INCUMBENT,
            reason=(
                f"{blame}, and there is no incumbent to fall back to"
                + ("" if exhausted else "; the conflicting rules are in `core`")
            ),
            seconds=time.perf_counter() - started,
            violations=_violations(frozenset(), instance),
            core=core,
            attempts=tuple(attempts),
        )

    attempts.append(GREEDY)
    repaired = repair(instance, incumbent)
    violations = _violations(repaired, instance)

    if not violations:
        return Answer(
            roster=repaired,
            rung=GREEDY,
            reason=f"{blame}, so the published roster was repaired slot by slot instead",
            seconds=time.perf_counter() - started,
            shortfall=_shortfall(repaired, instance),
            violations=(),
            core=core,
            attempts=tuple(attempts),
        )

    # Greedy could not produce a legal roster either. Return what people were already
    # told, and name what is wrong with it.
    attempts.append(INCUMBENT)
    return Answer(
        roster=incumbent,
        rung=INCUMBENT,
        reason=(
            f"{blame}, and repair could not produce one either; this is the published "
            f"roster unchanged, and it is already broken"
        ),
        seconds=time.perf_counter() - started,
        shortfall=_shortfall(incumbent, instance),
        violations=_violations(incumbent, instance),
        core=core,
        attempts=tuple(attempts),
    )


def _from_solve(
    instance: Instance, outcome: Solution, started: float, attempts: list[str]
) -> Answer:
    optimal = outcome.status == "OPTIMAL"
    return Answer(
        roster=outcome.roster,
        rung=EXACT if optimal else TIME_BOXED,
        reason=(
            "proven optimal"
            if optimal
            else f"the {outcome.status.lower()} solution when the budget ran out, "
            f"within {100 * outcome.gap:.1f}% of the proven bound"
        ),
        seconds=time.perf_counter() - started,
        objective=outcome.objective,
        gap=outcome.gap,
        shortfall=sum(
            value
            for (day, shift), value in outcome.shortfall.items()
            if not instance.is_past(day, shift)
        ),
        violations=_violations(outcome.roster, instance),
        attempts=tuple(attempts),
    )


def _violations(roster: Roster, instance: Instance) -> tuple[tuple, ...]:
    """Hard violations only, from the independent checker.

    Every rung is checked, including the ones that came from the model. A solver that
    validates its own output is checking its encoding against itself, and the whole point
    of `checker.py` is that it does not.
    """
    return tuple(v.key() for v in check(roster, instance) if not v.soft)


def _shortfall(roster: Roster, instance: Instance) -> int:
    counts: dict[tuple[int, int], int] = {}
    for _, day, shift in roster:
        counts[day, shift] = counts.get((day, shift), 0) + 1
    return sum(
        max(0, o.required - counts.get((o.day, o.shift), 0))
        for o in instance.open_shifts
        if not instance.is_past(o.day, o.shift)
    )
