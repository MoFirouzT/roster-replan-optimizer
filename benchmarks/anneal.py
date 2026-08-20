"""A penalty-based local search, built so `D-002` can be read as a number.

    uv run python -m benchmarks.anneal

`D-002` decides that hard rules are encoded as constraints rather than as large penalties
in the objective, and the sentence carrying the decision is this one: *a penalised legal
rule produces a roster that is **cheaply illegal**, and cheaply illegal is not a state this
service may return.* `D-003` leans on the same claim to justify the independent checker —
*under any formulation without hard-constraint guarantees (penalties inside a local search,
or a time-boxed solve accepting a gap), feasibility is not guaranteed by construction* — and
[`validation.md`](../docs/internals/testing.md) repeats it a third time.

Three records rest on it and none of them measured it. This module is the formulation those
sentences describe, so the claim can be checked rather than repeated.

## What it is

Metropolis acceptance over the assignment encoding, cooling geometrically, with **every hard
rule priced instead of prohibited**. There is no repair step and no feasibility gate: a move
into an illegal roster is accepted with the usual probability, which is the whole point. A
search that repaired its way back to feasibility would be a different method answering a
different question.

## Why it is allowed the checker as its oracle

The penalty counts hard violations reported by `checker.check`, which is the reading this
project trusts. That looks like a gift to the method and it is a deliberate one: it grants
the metaheuristic a **perfect legality oracle**, so whatever illegality comes back cannot be
blamed on an evaluator that was wrong about the rules. The claim under test is that pricing
a rule is unsafe *even when you know exactly which rules you broke*, and handing it a
weaker oracle would confound that with an implementation defect.

It also keeps the rules read twice rather than three times. An incremental evaluator fast
enough to be competitive would have to know which rules are per-employee and which are
per-slot — rule structure living outside `checker.py`, which is the shared-assumption
failure mode `D-111` and `D-123` were both written about. The cost of refusing that is
speed, and the next section says what is done about it.

## The budget is counted in evaluations, not seconds

Each move costs a full `check` and a full `score` — 0.13 ms on a committed case, 2.5 ms on
foreign instance 8. A production engine evaluates incrementally and would run orders of
magnitude more moves in the same wall time, so **a wall-clock comparison against CP-SAT
would measure this implementation rather than the method class**.

So `evaluations` is the budget axis and the anytime curve is drawn against it. Wall seconds
are recorded beside it and are honest about what they are: the cost of this Python, not the
cost of annealing. `D-081` already separates two clocks in this project for a related
reason, and this is the same discipline applied to a method whose natural unit is moves.

## What it may and may not touch

The move generator never proposes a slot that has already started, which is `instance.is_past`
— a fact about the instance, not a rule reading, and the same question `repair.py` asks for
the same reason. Everything else is fair game and every rule is priced, including the ones a
planner would call non-negotiable. Restricting the generator further would be repairing by
the back door.
"""

from __future__ import annotations

import dataclasses
import math
import random
import time

from roster_replan.checker import check
from roster_replan.domain import Instance, Roster
from roster_replan.scoring import score

# The weights the sweep walks. `D-002`'s claim is not that some weight is too small; it is
# that no weight is both safe and effective, so the sweep has to reach both failure modes.
# 1 prices a rule at about one changed assignment; 10_000_000 is two orders above the
# shortfall weight (`D-057`), where the penalty term swamps everything the objective is
# actually for.
WEIGHTS = (1, 100, 10_000, 1_000_000, 10_000_000)

# Budgets in moves. The top of the range is where a committed case takes ~13 s and foreign
# instance 8 takes ~4 minutes, which is the practical ceiling for a study that runs several
# seeds over both sets.
BUDGETS = (1_000, 10_000, 100_000)


@dataclasses.dataclass(frozen=True, slots=True)
class Sample:
    """One point on the anytime curve.

    `hard` is the count this study exists to report, and it is kept beside the objective
    rather than folded into it: a search can improve its penalty by trading a violation for
    disruption, and a single number hides exactly the trade being measured.
    """

    evaluations: int
    seconds: float
    penalty: int
    objective: int
    hard: int


@dataclasses.dataclass(frozen=True, slots=True)
class Result:
    """What one anneal returned, and what it cost to get there.

    `roster` is the best-penalty roster seen, not the last one visited — a Metropolis search
    ends wherever it happens to be, and reporting that would add noise nobody asked about.
    """

    roster: Roster
    hard_weight: int
    evaluations: int
    seconds: float
    seed: int
    accepted: int
    objective: int
    hard: int
    trace: tuple[Sample, ...]

    # Accepted moves that left the roster with *more* hard violations than before. This is
    # the no-feasibility-gate property made observable, and it is here because a test could
    # not see the difference without it: a gate that refuses to make things worse still
    # leaves the incumbent's own damage unrepaired, so the returned roster is illegal either
    # way and every other field agrees. A mutant installing exactly that gate survived the
    # first version of `tests/test_anneal.py`.
    #
    # It is also the mechanism the study is about rather than bookkeeping: traversing illegal
    # space is how a penalty search reaches a chain repair that greedy cannot, and it is the
    # same freedom that lets it stop somewhere illegal.
    accepted_illegal: int = 0

    @property
    def legal(self) -> bool:
        return self.hard == 0


def penalty(roster: Roster, instance: Instance, hard_weight: int) -> tuple[int, int, int]:
    """The penalised objective: the D2 yardstick plus a price on every hard violation.

    Returns `(penalty, objective, hard)`. The objective term is `scoring.score(...).total`,
    which is the same yardstick `methods.py` scores every other method on — so a roster this
    search returns is comparable with one the solver returned, whatever it optimised.
    """
    measured = score(roster, instance).total
    hard = sum(1 for v in check(roster, instance) if not v.soft)
    return measured + hard_weight * hard, measured, hard


def anneal(
    instance: Instance,
    incumbent: Roster,
    *,
    hard_weight: int,
    evaluations: int = 10_000,
    seed: int = 7,
    trace_every: int = 0,
) -> Result:
    """Anneal from the incumbent, pricing every hard rule at `hard_weight`.

    Starting from the incumbent rather than from empty is what a replan engine does, and it
    is also the harder test of the claim: the search begins at a roster that is legal except
    for the damage the event did, so any illegality in the answer was **introduced by the
    search** rather than inherited from where it started.
    """
    rng = random.Random(seed)
    slots = _slots(instance)
    if not slots:
        raise ValueError("no repairable slot in this instance; nothing to search over")
    people = tuple(range(len(instance.employees)))

    current = set(incumbent)
    current_penalty, objective, hard = penalty(frozenset(current), instance, hard_weight)

    best = frozenset(current)
    best_penalty, best_objective, best_hard = current_penalty, objective, hard

    hot, cold = _temperatures(instance, incumbent, hard_weight, slots, people, rng)
    decay = (cold / hot) ** (1.0 / max(1, evaluations)) if hot > 0 else 1.0
    temperature = hot

    every = trace_every or max(1, evaluations // 100)
    trace: list[Sample] = []
    started = time.perf_counter()
    accepted = 0
    accepted_illegal = 0

    for step in range(1, evaluations + 1):
        proposal = _propose(current, slots, people, rng)
        if proposal is None:
            continue

        candidate = frozenset(proposal)
        cand_penalty, cand_objective, cand_hard = penalty(
            candidate, instance, hard_weight
        )
        delta = cand_penalty - current_penalty

        if delta <= 0 or rng.random() < math.exp(-delta / max(temperature, 1e-9)):
            current = proposal
            accepted += 1
            if cand_hard > hard:
                accepted_illegal += 1
            current_penalty, objective, hard = cand_penalty, cand_objective, cand_hard
            if cand_penalty < best_penalty:
                best = candidate
                best_penalty = cand_penalty
                best_objective, best_hard = cand_objective, cand_hard

        temperature *= decay

        if step % every == 0 or step == evaluations:
            trace.append(
                Sample(
                    evaluations=step,
                    seconds=time.perf_counter() - started,
                    penalty=best_penalty,
                    objective=best_objective,
                    hard=best_hard,
                )
            )

    return Result(
        roster=best,
        hard_weight=hard_weight,
        evaluations=evaluations,
        seconds=time.perf_counter() - started,
        seed=seed,
        accepted=accepted,
        accepted_illegal=accepted_illegal,
        objective=best_objective,
        hard=best_hard,
        trace=tuple(trace),
    )


def _slots(instance: Instance) -> tuple[tuple[int, int], ...]:
    """Every (day, shift) the search may touch: the open shifts, minus the pinned past.

    Asked of the instance rather than of the rules. `R-PIN-PAST` is still priced like every
    other rule — this only stops the generator wasting its budget proposing moves into a
    week that has already happened, which is a structural property any engine has and not a
    repair step.
    """
    return tuple(
        (o.day, o.shift)
        for o in sorted(instance.open_shifts, key=lambda o: (o.day, o.shift))
        if not instance.is_past(o.day, o.shift)
    )


def _propose(
    roster: set, slots: tuple, people: tuple, rng: random.Random
) -> set | None:
    """One neighbour: add, drop, move a slot to somebody else, or swap two assignments.

    `move` is what makes a chain reachable at all — dropping and adding independently has to
    pass through a strictly worse roster, and at a low temperature it will not. `swap`
    exchanges two people's assignments in one step, which is the shape of the repair greedy
    cannot find: `D-083`'s 13 losses are chains where somebody uninvolved has to shift.
    """
    kind = rng.random()
    movable = [key for key in roster if (key[1], key[2]) in slots]

    if kind < 0.25 or not movable:
        day, shift = rng.choice(slots)
        employee = rng.choice(people)
        key = (employee, day, shift)
        if key in roster:
            return None
        return roster | {key}

    if kind < 0.45:
        return roster - {rng.choice(movable)}

    if kind < 0.75:
        employee, day, shift = rng.choice(movable)
        replacement = rng.choice(people)
        if replacement == employee or (replacement, day, shift) in roster:
            return None
        return (roster - {(employee, day, shift)}) | {(replacement, day, shift)}

    if len(movable) < 2:
        return None
    first, second = rng.sample(movable, 2)
    if first[0] == second[0]:
        return None
    swapped = {
        (second[0], first[1], first[2]),
        (first[0], second[1], second[2]),
    }
    if swapped & roster:
        return None
    return (roster - {first, second}) | swapped


def _temperatures(
    instance: Instance,
    incumbent: Roster,
    hard_weight: int,
    slots: tuple,
    people: tuple,
    rng: random.Random,
    *,
    probes: int = 60,
) -> tuple[float, float]:
    """Calibrate the schedule to the objective's own scale rather than to a constant.

    The penalty ranges over orders of magnitude — `shortfall_weight` is 100,000 (`D-057`)
    and `hard_weight` is swept across five decades — so a hard-coded starting temperature
    would anneal one configuration properly and freeze or boil every other. Sampling the
    mean uphill move makes the schedule a property of the instance, which is the only way
    the sweep compares like with like.
    """
    base = set(incumbent)
    reference, _, _ = penalty(frozenset(base), instance, hard_weight)
    uphill: list[float] = []
    for _ in range(probes):
        proposal = _propose(base, slots, people, rng)
        if proposal is None:
            continue
        moved, _, _ = penalty(frozenset(proposal), instance, hard_weight)
        if moved > reference:
            uphill.append(float(moved - reference))

    # Nothing uphill in sixty probes means a flat neighbourhood; any positive temperature
    # behaves the same there, so the constant is arbitrary and says so.
    hot = (sum(uphill) / len(uphill)) if uphill else 1.0
    return hot, max(hot / 1_000.0, 1e-6)


def sweep(
    instance: Instance,
    incumbent: Roster,
    *,
    weights: tuple[int, ...] = WEIGHTS,
    budgets: tuple[int, ...] = BUDGETS,
    seeds: tuple[int, ...] = (7,),
) -> list[Result]:
    """Every (weight, budget, seed), which is the grid the claim needs.

    One weight would only show that *that* weight was wrong. The claim is about the
    formulation, so the answer has to be a surface rather than a point.
    """
    results = []
    for weight in weights:
        for budget in budgets:
            for seed in seeds:
                results.append(
                    anneal(
                        instance,
                        incumbent,
                        hard_weight=weight,
                        evaluations=budget,
                        seed=seed,
                    )
                )
    return results


def row(result: Result, case: str) -> dict:
    """One result flattened for the results file, roster dropped.

    Same convention as `methods.Outcome`: the case name plus the seed reproduces the roster,
    and a file full of rosters is one nobody opens.
    """
    return {
        "case": case,
        "hard_weight": result.hard_weight,
        "evaluations": result.evaluations,
        "seed": result.seed,
        "seconds": round(result.seconds, 3),
        "accepted": result.accepted,
        "objective": result.objective,
        "hard": result.hard,
        "legal": result.legal,
        "trace": [dataclasses.asdict(s) for s in result.trace],
    }


# No `main` and no scenario loading here, and the import contract is why. `suite` and
# `foreign` both reach `roster_replan.model` to build the instances they hand out, so a CLI
# in this module would pull the solver in behind it — which the contract caught on its first
# run rather than on review. The runner is `benchmarks/anneal_study.py`.
