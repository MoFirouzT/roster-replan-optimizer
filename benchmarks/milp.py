"""The MILP formulation, built so `D-001` can be written from a comparison.

    uv run python -m benchmarks.milp

`D-001` — *CP-SAT over MILP* — has been the one T1 record owed since T1, and `decisions.md`
says why it stayed owed: no spec argues it, so it could not be written without inventing a
rationale nobody had. The alternative to inventing one is to run the comparison, which is
what every other *this encoding against that one* question in this project got.

This is the same problem stated for a branch-and-cut solver. SCIP and CBC both ship inside
`ortools`, so the comparison needs no new dependency and no commercial licence — which also
means it is a comparison against **open-source** MILP, not against Gurobi. That limit is
stated in the study rather than glossed: a Gurobi licence would likely change the timings
and would not change the two structural findings below.

## What ports cleanly, and what does not

Most of the model is linear already and moves across with no cleverness: coverage with an
explicit slack, pairwise rest-gap exclusions, weekly and daily hour ceilings, the pinned
past, and D0–D2's objective — deviation is linear because the incumbent is a constant, so
`|x - x̄|` is `1 - x` or `x` depending on which.

Two things do not, and they are the interesting half of the answer.

**`R-CONSEC-DAYS` needs a linking constraint CP-SAT does not.** CP-SAT states
`y = max(shifts that day)` directly. MILP has no `max`, so the indicator is linked with one
inequality per shift, and the model grows by the number of (employee, day, shift) triples.
It is exact here only because the objective never rewards setting `y` high.

**D3 and D4 cannot be expressed at all without new binaries.** They pair a drop with an add
via `min(drops, adds)`, and `min` is not linear: MILP needs auxiliary binaries and big-M
per (employee, day). CP-SAT writes `add_min_equality` and stops. This module therefore
refuses D3 and D4 rather than silently comparing a different model, and that refusal is a
finding rather than a limitation of the effort spent.

**The gates do not port either.** Every hard constraint in `model.py` carries an assumption
literal so a failed solve can name the rule instances in conflict (`D-002`). MILP solvers
have no assumption mechanism; an IIS is the nearest equivalent and is a different object
with different guarantees. The comparison below is therefore between the CP-SAT model's
*feasible set* and this one's — the reporting machinery has no counterpart to compare.
"""

from __future__ import annotations

import argparse
import time
from collections import defaultdict

from ortools.linear_solver import pywraplp

from benchmarks import suite
from roster_replan.domain import Instance, Roster
from roster_replan.model import exclusions

BACKENDS = ("SCIP", "CBC")


def _minutes(hours: float) -> int:
    return int(round(hours * 60))


def build(instance: Instance, backend: str = "SCIP"):
    """The same feasible set as `model.build`, stated for a MILP solver."""
    if instance.disruption is None or instance.disruption.metric not in ("D0", "D1", "D2"):
        raise ValueError(
            "D3 and D4 pair changes with min(drops, adds), which is not linear; a MILP "
            "needs auxiliary binaries and big-M per (employee, day). Refused rather than "
            "silently compared against a different model -- see the module docstring"
        )
    if any(o.skill_mix for o in instance.open_shifts):
        raise ValueError(
            "R-SKILL-MIX clamps to min(minimum, headcount) and is not ported; no committed "
            "case carries a skill_mix entry, so the comparison does not need it"
        )

    solver = pywraplp.Solver.CreateSolver(backend)
    if solver is None:
        raise RuntimeError(f"MILP backend {backend!r} is not available")

    excluded = exclusions(instance)
    incumbent = instance.incumbent or frozenset()

    # The same variable set as `model.build`, including `D-058`'s rule: a pair the
    # incumbent assigned gets a variable even when presolve excluded it, or the deviation
    # it represents cannot be counted.
    keys = [
        (e, o.day, o.shift)
        for e in range(len(instance.employees))
        for o in instance.open_shifts
        if (e, o.day, o.shift) not in excluded or (e, o.day, o.shift) in incumbent
    ]
    x = {k: solver.BoolVar(f"x_{k[0]}_{k[1]}_{k[2]}") for k in keys}

    for key in keys:
        if key in excluded:
            solver.Add(x[key] == 0)

    shortfall = _cover(solver, instance, x)
    _pin_past(solver, instance, x, incumbent)
    _rest_gap(solver, instance, x)
    _weekly_rest(solver, instance, x)
    _hour_ceilings(solver, instance, x)
    _consec_days(solver, instance, x)

    _objective(solver, instance, x, shortfall)
    return solver, x, shortfall


def _cover(solver, instance: Instance, x):
    shortfall = {}
    for open_shift in instance.open_shifts:
        day, shift, required = open_shift.day, open_shift.shift, open_shift.required
        assigned = [
            x[e, day, shift] for e in range(len(instance.employees)) if (e, day, shift) in x
        ]
        short = solver.IntVar(0, max(required, 0), f"u_{day}_{shift}")
        shortfall[day, shift] = short
        # The ceiling is hard, so there is no overage variable: the equality states it.
        solver.Add(sum(assigned) + short == required)
    return shortfall


def _pin_past(solver, instance: Instance, x, incumbent: Roster):
    if instance.now is None or instance.incumbent is None:
        return
    for open_shift in instance.open_shifts:
        day, shift = open_shift.day, open_shift.shift
        if not instance.is_past(day, shift):
            continue
        for employee in range(len(instance.employees)):
            key = (employee, day, shift)
            if key in x:
                solver.Add(x[key] == int(key in incumbent))


def _rest_gap(solver, instance: Instance, x):
    minimum = instance.params.min_rest_hours
    slots = sorted(
        ((o.day, o.shift) for o in instance.open_shifts),
        key=lambda ds: instance.window(*ds).start,
    )
    for index, first in enumerate(slots):
        end = instance.window(*first).end
        for second in slots[index + 1 :]:
            if instance.window(*second).start - end >= minimum:
                continue
            for employee in range(len(instance.employees)):
                a, b = (employee, *first), (employee, *second)
                if a in x and b in x:
                    solver.Add(x[a] + x[b] <= 1)

    for employee, person in enumerate(instance.employees):
        previous_end = person.last_shift_end_before_horizon
        if previous_end is None:
            continue
        for open_shift in instance.open_shifts:
            key = (employee, open_shift.day, open_shift.shift)
            if key in x and (
                instance.window(open_shift.day, open_shift.shift).start - previous_end
                < minimum
            ):
                solver.Add(x[key] == 0)


def _weekly_rest(solver, instance: Instance, x):
    """Candidate windows and at-least-one, exactly as CP-SAT states it.

    The one place the two encodings look alike, because the CP-SAT version is already a
    disjunction over booleans rather than a global propagator. `selected -> x = 0` becomes
    `x + selected <= 1`, which is the standard indicator-free rewrite and needs no big-M.
    """
    width = instance.params.min_weekly_rest_hours
    horizon = instance.horizon()
    anchors = sorted(
        {horizon.start} | {instance.window(o.day, o.shift).end for o in instance.open_shifts}
    )

    for employee, person in enumerate(instance.employees):
        floor = horizon.start
        if person.last_shift_end_before_horizon is not None:
            floor = max(floor, person.last_shift_end_before_horizon)

        chosen = []
        for index, start in enumerate(anchors):
            if start < floor or start + width > horizon.end:
                continue
            selected = solver.BoolVar(f"r_{employee}_{index}")
            chosen.append(selected)
            for open_shift in instance.open_shifts:
                key = (employee, open_shift.day, open_shift.shift)
                if key not in x:
                    continue
                window = instance.window(open_shift.day, open_shift.shift)
                if window.start < start + width and start < window.end:
                    solver.Add(x[key] + selected <= 1)

        if chosen:
            solver.Add(sum(chosen) >= 1)
        else:
            solver.Add(solver.IntVar(0, 0, f"infeasible_{employee}") == 1)


def _hour_ceilings(solver, instance: Instance, x):
    for employee, person in enumerate(instance.employees):
        own = [(e, d, s) for (e, d, s) in x if e == employee]

        if person.max_hours_this_week is not None:
            solver.Add(
                sum(
                    _minutes(instance.shift_types[s].work_hours) * x[e, d, s]
                    for (e, d, s) in own
                )
                <= _minutes(person.max_hours_this_week)
            )

        if person.max_daily_hours is None:
            continue
        per_day = defaultdict(list)
        for e, d, s in own:
            per_day[d].append(_minutes(instance.shift_types[s].work_hours) * x[e, d, s])
        for day in sorted(per_day):
            solver.Add(sum(per_day[day]) <= _minutes(person.max_daily_hours))


def _consec_days(solver, instance: Instance, x):
    """The rule that costs MILP something CP-SAT gets free.

    CP-SAT states `worked = max(shifts that day)`. There is no `max` in a linear program,
    so the indicator is linked with `worked >= x` once per shift. It is exact only because
    nothing rewards raising `worked`: the objective never mentions it and every constraint
    on it is an upper bound, so an optimal solution leaves it as low as the links allow.
    """
    limit = instance.params.max_consecutive_days
    if limit is None:
        return

    for employee, person in enumerate(instance.employees):
        worked = {}
        for day in range(instance.days):
            indicator = solver.BoolVar(f"w_{employee}_{day}")
            same_day = [x[e, d, s] for (e, d, s) in x if e == employee and d == day]
            for var in same_day:
                solver.Add(indicator >= var)
            if not same_day:
                solver.Add(indicator == 0)
            worked[day] = indicator

        prior = person.consecutive_days_worked_before_horizon
        for start in range(-prior, instance.days - limit):
            before = max(0, min(-start, limit + 1))
            inside = [
                worked[d]
                for d in range(max(0, start), min(start + limit + 1, instance.days))
            ]
            if not inside:
                continue
            solver.Add(sum(inside) <= max(0, limit - min(before, limit)))


def _objective(solver, instance: Instance, x, shortfall):
    """D0-D2, linear because the incumbent is a constant.

    `|x - x̄|` needs no absolute value: where the incumbent assigned the slot the deviation
    is `1 - x`, and where it did not it is `x`. That is the property that makes these three
    metrics portable and D3/D4 not.
    """
    params = instance.disruption
    incumbent = instance.incumbent or frozenset()
    terms = []

    for (day, shift), slack in shortfall.items():
        if not instance.is_past(day, shift):
            terms.append(params.shortfall_weight * slack)

    for (e, day, shift), var in x.items():
        if params.metric == "D0":
            weight = 1
        else:
            publication = (
                params.published_weight
                if instance.is_published(day, shift)
                else params.draft_weight
            )
            weight = (
                publication
                if params.metric == "D1"
                else publication * params.notice_multiplier(instance.notice_hours(day, shift))
            )
        if (e, day, shift) in incumbent:
            terms.append(weight * (1 - var))
        else:
            terms.append(weight * var)

    solver.Minimize(sum(terms))


# --- Solving ------------------------------------------------------------------------


def solve(instance: Instance, *, backend: str = "SCIP", time_limit: float = 30.0):
    """Returns `(roster, objective, timings)`. `objective` is -1 when not proven optimal."""
    started = time.perf_counter()
    solver, x, _ = build(instance, backend)
    build_seconds = time.perf_counter() - started

    solver.SetTimeLimit(int(time_limit * 1000))

    # **The relative MIP gap must be forced to zero, and this is a finding rather than a
    # setting.** pywraplp defaults it to 1e-4, which is a *relative* tolerance -- and this
    # objective is not on a scale where that is small. `shortfall_weight` is 100,000 so that
    # coverage dominates disruption (`D-057`), so any roster with one unstaffed shift scores
    # in the hundreds of thousands, and 1e-4 of that is an absolute slack of about 30
    # disruption points. Ten changed shifts.
    #
    # At the default, SCIP returned a roster scoring 300003 and **reported it OPTIMAL** while
    # 300001 was feasible. CP-SAT is exact by default and has no equivalent knob, so the two
    # were not being asked the same question: the comparison was timing an approximation
    # against a proof. Caught by a cross-formulation equivalence test, not by review.
    params = pywraplp.MPSolverParameters()
    params.SetDoubleParam(pywraplp.MPSolverParameters.RELATIVE_MIP_GAP, 0.0)

    started = time.perf_counter()
    status = solver.Solve(params)
    search_seconds = time.perf_counter() - started

    optimal = status == pywraplp.Solver.OPTIMAL
    roster = (
        frozenset(k for k, v in x.items() if v.solution_value() > 0.5)
        if status in (pywraplp.Solver.OPTIMAL, pywraplp.Solver.FEASIBLE)
        else frozenset()
    )
    return (
        roster,
        round(solver.Objective().Value()) if optimal else -1,
        {
            "build_seconds": build_seconds,
            "search_seconds": search_seconds,
            "variables": solver.NumVariables(),
            "constraints": solver.NumConstraints(),
            "status": "OPTIMAL" if optimal else str(status),
        },
    )


if __name__ == "__main__":
    from roster_replan.model import build as cp_build, solve as cp_solve

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--backends", nargs="+", default=["SCIP", "CBC"])
    parser.add_argument("--cases", nargs="*", default=None)
    args = parser.parse_args()

    cases = args.cases or [f"{name}/0" for name in suite.CLASSES]

    print(
        f"{'case':20}{'solver':8}{'vars':>7}{'cons':>7}"
        f"{'build ms':>10}{'search ms':>11}{'objective':>11}  agree"
    )
    for case in cases:
        instance = suite.build(case).instance

        started = time.perf_counter()
        built = cp_build(instance)
        cp_build_seconds = time.perf_counter() - started
        reference = cp_solve(instance, time_limit=30.0)
        print(
            f"{case:20}{'CP-SAT':8}{len(built.model.proto.variables):>7}"
            f"{len(built.model.proto.constraints):>7}{1000 * cp_build_seconds:>10.1f}"
            f"{1000 * reference.search_seconds:>11.1f}{reference.objective:>11}  --"
        )

        for backend in args.backends:
            roster, objective, timing = solve(instance, backend=backend)
            agree = "same" if objective == reference.objective else f"DIFFERS ({objective})"
            print(
                f"{'':20}{backend:8}{timing['variables']:>7}{timing['constraints']:>7}"
                f"{1000 * timing['build_seconds']:>10.1f}"
                f"{1000 * timing['search_seconds']:>11.1f}{objective:>11}  {agree}"
            )
