"""The pattern/column formulation, built so `D-009` can be closed with a measurement.

`internals/model.md` lists pattern variables as "dramatically stronger formulations, evaluated as a
study at these instance sizes", and `D-009` had been open since the model was first written.
This module is the second formulation, and it is a genuine one rather than a sketch: it enumerates every legal
weekly pattern per employee, selects one per employee, and reaches the same optimum as the
assignment model.

## The formulation

One boolean per (employee, legal weekly pattern), exactly one true per employee. Coverage
sums the chosen patterns' slots. **Every per-employee rule disappears from the model** --
rest gaps, daily and weekly hours, consecutive days, weekly rest, the pinned past -- because
a pattern that breaks one is never enumerated. What is left is coverage, skill mix, and the
objective.

The objective survives the change intact, and that is not a coincidence. D0-D2 price
disruption per changed slot, so a pattern's disruption is a **constant** computed once at
enumeration time. The model is then linear in the pattern booleans with no auxiliary
variables at all. D3 and D4 also decompose per employee-day and per employee, so they would
carry over the same way.

## Why enumeration is tractable here, and where it stops being

`max_daily_hours` of 8 against shifts of 7.5 net hours means at most one shift per day, so a
pattern is a choice of one shift or nothing on each of seven days. That is at most `4^7`
before any rule filters it, and the weekly budget cuts it to a few thousand. This is a
property of a one-week horizon with a daily cap, and the module says so rather than
implying pattern enumeration is generally cheap: at a four-week reference period the same
enumeration is `4^28`, and the technique that replaces it is column generation, which is a
different project.

The enumeration is validated by the **checker**, not by re-deriving the rules here. A
pattern is legal exactly when the independent reading says that employee's own row is
clean, which is the same oracle the greedy baseline uses and for the same reason.
"""

from __future__ import annotations

import argparse
import itertools
import time

from ortools.sat.python import cp_model

from benchmarks import suite
from roster_replan.checker import check
from roster_replan.domain import Instance, Roster
from roster_replan.model import exclusions
from roster_replan.scoring import disruption_of

Pattern = frozenset[tuple[int, int]]


def enumerate_patterns(instance: Instance, employee: int) -> list[Pattern]:
    """Every legal weekly pattern for one employee, as (day, shift) pairs.

    Built day by day so the branch dies early, then validated as a whole by the checker.
    The past is not enumerated over: `R-PIN-PAST` fixes it, so a pattern that differs there
    is not a candidate the replan may consider.
    """
    excluded = exclusions(instance)
    incumbent = instance.incumbent or frozenset()
    by_day: dict[int, list[tuple[int, int]]] = {}

    for day in range(instance.days):
        open_here = [
            (o.day, o.shift)
            for o in instance.open_shifts
            if o.day == day and (employee, o.day, o.shift) not in excluded
        ]
        past = [o for o in instance.open_shifts if o.day == day and instance.is_past(o.day, o.shift)]
        if past:
            # Pinned: the only choice on this day is what the incumbent already did.
            fixed = tuple(
                (o.day, o.shift) for o in past if (employee, o.day, o.shift) in incumbent
            )
            future_here = [
                slot for slot in open_here if not instance.is_past(slot[0], slot[1])
            ]
            by_day[day] = [
                fixed + extra
                for extra in _day_choices(instance, future_here)
                if _within_daily(instance, employee, fixed + extra)
            ]
        else:
            by_day[day] = [
                choice
                for choice in _day_choices(instance, open_here)
                if _within_daily(instance, employee, choice)
            ]

    budget = instance.employees[employee].max_hours_this_week or float("inf")
    per_shift = {s: instance.shift_types[s].work_hours for s in range(len(instance.shift_types))}

    patterns: list[Pattern] = []
    for combination in itertools.product(*(by_day[day] for day in range(instance.days))):
        slots = tuple(slot for day in combination for slot in day)
        if sum(per_shift[shift] for _, shift in slots) > budget:
            continue
        pattern = frozenset(slots)
        if _legal(instance, employee, pattern):
            patterns.append(pattern)
    return patterns


def _day_choices(instance: Instance, open_here) -> list[tuple]:
    """Every subset of one day's open shifts, smallest first. Not just "one or none": the
    daily cap is a parameter and a tenant whose shifts are short enough for two is a legal
    tenant, so the subset is filtered by hours rather than assumed away."""
    choices: list[tuple] = [()]
    for size in range(1, len(open_here) + 1):
        choices.extend(itertools.combinations(open_here, size))
    return choices


def _within_daily(instance: Instance, employee: int, slots) -> bool:
    """This employee's own daily cap. Reading employee 0's was the first version, and it
    is the kind of mistake enumeration hides: every employee in the generated set happens
    to carry the same cap, so the wrong answer and the right one agree here and would stop
    agreeing on the first tenant with a part-timer on a shorter day."""
    limit = instance.employees[employee].max_daily_hours
    if limit is None:
        return True
    return sum(instance.shift_types[shift].work_hours for _, shift in slots) <= limit


def _legal(instance: Instance, employee: int, pattern: Pattern) -> bool:
    roster = frozenset((employee, day, shift) for day, shift in pattern)
    return not [v for v in check(roster, instance) if not v.soft and v.employee == employee]


# --- The model ----------------------------------------------------------------------


def solve_patterns(instance: Instance, *, seed: int = 7, time_limit: float = 30.0):
    """Select one pattern per employee. Returns `(roster, objective, timings)`."""
    started = time.perf_counter()
    catalogue = [enumerate_patterns(instance, e) for e in range(len(instance.employees))]
    enumerate_seconds = time.perf_counter() - started

    started = time.perf_counter()
    model = cp_model.CpModel()
    chosen = [
        [model.new_bool_var(f"y_{e}_{p}") for p in range(len(patterns))]
        for e, patterns in enumerate(catalogue)
    ]
    for e, row in enumerate(chosen):
        if not row:
            raise RuntimeError(f"employee {e} has no legal pattern at all, not even an empty one")
        model.add_exactly_one(row)

    terms = []
    params = instance.disruption
    for open_shift in instance.open_shifts:
        key = (open_shift.day, open_shift.shift)
        assigned = [
            chosen[e][p]
            for e, patterns in enumerate(catalogue)
            for p, pattern in enumerate(patterns)
            if key in pattern
        ]
        short = model.new_int_var(0, open_shift.required, f"u_{key}")
        model.add(sum(assigned) + short == open_shift.required)
        if not instance.is_past(*key):
            terms.append(params.shortfall_weight * short)

    # Disruption is a constant per pattern: D0-D2 price it per changed slot, so it is
    # known before the solve and needs no variable.
    #
    # The coefficient is this employee's **own** contribution, obtained by scoring their
    # pattern against everyone else's incumbent row -- the other rows then match the
    # incumbent and contribute nothing, so what is left is exactly `cost_e(pattern)`. An
    # earlier version subtracted the cost of emptying the row as well, which is a constant
    # per employee: it left the chosen roster optimal and the reported objective wrong by a
    # fixed offset, which is the kind of bug that looks like a formulation disagreement.
    for e, patterns in enumerate(catalogue):
        others = _others(instance, e)
        for p, pattern in enumerate(patterns):
            cost = disruption_of(
                frozenset((e, day, shift) for day, shift in pattern) | others, instance
            )
            if cost:
                terms.append(cost * chosen[e][p])

    # The cold case needs the peak tie-breaker, for the same reason `disruption.py` adds
    # one: with no incumbent every roster of equal coverage has equal disruption, so
    # without it the two formulations would be minimising different things and any
    # comparison between them would be meaningless rather than merely close.
    #
    # It costs one constraint per employee here against one per employee there, because a
    # pattern's assignment count is known at enumeration time.
    if instance.incumbent is None:
        peak = model.new_int_var(0, len(instance.open_shifts), "peak")
        for e, employee_patterns in enumerate(catalogue):
            model.add(
                peak
                >= sum(
                    len(pattern) * chosen[e][p] for p, pattern in enumerate(employee_patterns)
                )
            )
        terms.append(params.peak_weight * peak)

        for e, employee_patterns in enumerate(catalogue):
            for p, pattern in enumerate(employee_patterns):
                paid = sum(
                    round(instance.shift_types[shift].work_hours * 60) for _, shift in pattern
                )
                if params.cost_weight and paid:
                    terms.append(params.cost_weight * paid * chosen[e][p])

    model.minimize(sum(terms))
    build_seconds = time.perf_counter() - started

    solver = cp_model.CpSolver()
    solver.parameters.num_workers = 1
    solver.parameters.random_seed = seed
    solver.parameters.max_time_in_seconds = time_limit
    status = solver.solve(model)

    roster: Roster = frozenset(
        (e, day, shift)
        for e, patterns in enumerate(catalogue)
        for p, pattern in enumerate(patterns)
        if solver.value(chosen[e][p])
        for day, shift in pattern
    )
    return (
        roster,
        round(solver.objective_value) if status == cp_model.OPTIMAL else -1,
        {
            "enumerate_seconds": enumerate_seconds,
            "build_seconds": build_seconds,
            "search_seconds": solver.wall_time,
            "patterns": sum(len(p) for p in catalogue),
            "status": solver.status_name(status),
        },
    )


def _others(instance: Instance, employee: int) -> Roster:
    """The incumbent's rows for everyone else, so one employee's disruption can be read
    off a whole roster the independent scorer will accept."""
    return frozenset(k for k in (instance.incumbent or frozenset()) if k[0] != employee)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--cases", nargs="*", default=["small/0", "headline/0", "large/0"])
    args = parser.parse_args()

    from roster_replan.model import solve as assignment_solve

    print(f"{'case':16}{'patterns':>10}{'enum ms':>10}{'build ms':>10}{'search ms':>11}"
          f"{'total ms':>10}{'vs assignment':>15}")
    for case in args.cases:
        scenario = suite.build(case)
        roster, objective, timing = solve_patterns(scenario.instance)
        reference = assignment_solve(scenario.instance)
        total = 1000 * (
            timing["enumerate_seconds"] + timing["build_seconds"] + timing["search_seconds"]
        )
        agree = "same optimum" if objective == reference.objective else "DISAGREES"
        print(
            f"{case:16}{timing['patterns']:>10,}{1000 * timing['enumerate_seconds']:>10.1f}"
            f"{1000 * timing['build_seconds']:>10.1f}{1000 * timing['search_seconds']:>11.2f}"
            f"{total:>10.1f}{agree:>15}"
        )
