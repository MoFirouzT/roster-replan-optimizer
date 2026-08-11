"""T0 walking skeleton: solve a week, injure it with one absence, replan around it.

Deliberately one file and deliberately undocumented elsewhere (see PLAN.md T0).
Three hard rules only: R-COVER, R-AVAIL, R-REST-GAP. Disruption is a raw count of
changed assignments -- the D0 that replan.md rejects. That is fine here; T0 exists
to prove something solves and that the output is readable by eye.

    uv run python -m roster_replan.t0
"""

from __future__ import annotations

import random

from ortools.sat.python import cp_model

DAYS = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]
EMPLOYEES = ["Ana", "Bram", "Chloe", "Driss", "Emma", "Finn", "Gita", "Hugo"]

# (label, start hour within its day, length in hours). N crosses midnight.
SHIFTS = [("M", 7, 8), ("E", 15, 8), ("N", 23, 8)]

MIN_REST_HOURS = 11

DEMAND = {
    "M": [2, 2, 2, 2, 2, 2, 2],
    "E": [2, 2, 2, 2, 2, 3, 3],
    "N": [1, 1, 1, 1, 1, 1, 1],
}

ABSENCE_RATE = 0.10
SEED = 7

# The headline scenario, hardcoded: someone calls in sick on Saturday morning.
SICK_DAY = DAYS.index("Sat")


def shift_window(day: int, shift: int) -> tuple[int, int]:
    """Absolute (start, end) hours from the start of the week."""
    _, start, length = SHIFTS[shift]
    begin = day * 24 + start
    return begin, begin + length


def slots() -> list[tuple[int, int]]:
    return [(d, s) for d in range(len(DAYS)) for s in range(len(SHIFTS))]


def declared_unavailability() -> set[tuple[int, int]]:
    """Seeded (employee, day) unavailability -- R-AVAIL input."""
    rng = random.Random(SEED)
    return {
        (e, d)
        for e in range(len(EMPLOYEES))
        for d in range(len(DAYS))
        if rng.random() < ABSENCE_RATE
    }


def conflicting_slot_pairs() -> list[tuple[tuple[int, int], tuple[int, int]]]:
    """Slot pairs one employee cannot hold together under R-REST-GAP.

    Covers overlap as the degenerate case: an overlapping pair has negative rest.
    """
    pairs = []
    ordered = sorted(slots(), key=lambda slot: shift_window(*slot))
    for i, a in enumerate(ordered):
        _, end_a = shift_window(*a)
        for b in ordered[i + 1 :]:
            start_b, _ = shift_window(*b)
            if start_b - end_a < MIN_REST_HOURS:
                pairs.append((a, b))
    return pairs


def solve(
    unavailable: set[tuple[int, int]],
    baseline: dict[tuple[int, int, int], int] | None = None,
) -> tuple[dict[tuple[int, int, int], int], int] | None:
    """Cold solve when `baseline` is None, otherwise a minimum-disruption replan."""
    model = cp_model.CpModel()
    x = {
        (e, d, s): model.new_bool_var(f"x_{e}_{d}_{s}")
        for e in range(len(EMPLOYEES))
        for d, s in slots()
    }

    # R-COVER -- every shift staffed to its requirement, exactly.
    for d, s in slots():
        label = SHIFTS[s][0]
        model.add(sum(x[e, d, s] for e in range(len(EMPLOYEES))) == DEMAND[label][d])

    # R-AVAIL -- no assignment against declared unavailability.
    for e, d in unavailable:
        for s in range(len(SHIFTS)):
            model.add(x[e, d, s] == 0)

    # R-REST-GAP -- minimum rest between any two shifts one person holds.
    for (d1, s1), (d2, s2) in conflicting_slot_pairs():
        for e in range(len(EMPLOYEES)):
            model.add(x[e, d1, s1] + x[e, d2, s2] <= 1)

    if baseline is None:
        # Cold start has no preference to express; pick the flattest workload so the
        # roster being repaired later is a plausible one rather than an artefact.
        peak = model.new_int_var(0, len(DAYS), "peak")
        for e in range(len(EMPLOYEES)):
            model.add(peak >= sum(x[e, d, s] for d, s in slots()))
        model.minimize(peak)
    else:
        # Disruption: every assignment that differs from what people were told.
        model.minimize(
            sum(
                x[key] if was == 0 else 1 - x[key]
                for key, was in baseline.items()
            )
        )

    solver = cp_model.CpSolver()
    solver.parameters.num_workers = 1
    solver.parameters.random_seed = SEED
    solver.parameters.max_time_in_seconds = 30.0
    status = solver.solve(model)
    if status not in (cp_model.OPTIMAL, cp_model.FEASIBLE):
        return None
    return {k: solver.value(v) for k, v in x.items()}, round(solver.objective_value)


def render(roster: dict[tuple[int, int, int], int]) -> str:
    lines = ["      " + "".join(f"{d:>6}" for d in DAYS)]
    for e, name in enumerate(EMPLOYEES):
        cells = []
        for d in range(len(DAYS)):
            worked = [SHIFTS[s][0] for s in range(len(SHIFTS)) if roster[e, d, s]]
            cells.append("".join(worked) or ".")
        lines.append(f"{name:<6}" + "".join(f"{c:>6}" for c in cells))
    return "\n".join(lines)


def diff(before: dict, after: dict) -> list[str]:
    changes = []
    for (e, d, s), was in before.items():
        now = after[e, d, s]
        if was == now:
            continue
        verb = "dropped" if was else "added  "
        changes.append(f"  {verb} {EMPLOYEES[e]:<6} {DAYS[d]} {SHIFTS[s][0]}")
    return sorted(changes)


def main() -> None:
    unavailable = declared_unavailability()

    cold = solve(unavailable)
    if cold is None:
        raise SystemExit("cold solve infeasible -- the instance, not the model, is wrong")
    baseline, peak = cold
    print("Published roster (cold solve, flattest workload)")
    print(render(baseline))
    print(f"\nBusiest employee works {peak} shifts.\n")

    # Injure it: the first person holding a Saturday shift calls in sick.
    sick = next(
        e
        for e in range(len(EMPLOYEES))
        for s in range(len(SHIFTS))
        if baseline[e, SICK_DAY, s]
    )
    print(f"{EMPLOYEES[sick]} calls in sick for {DAYS[SICK_DAY]}.\n")

    repaired = solve(unavailable | {(sick, SICK_DAY)}, baseline=baseline)
    if repaired is None:
        raise SystemExit("replan infeasible -- no legal roster absorbs this absence")
    after, disruption = repaired

    print("Replanned roster")
    print(render(after))
    print(f"\nDisruption (changed assignments): {disruption}")
    for line in diff(baseline, after):
        print(line)


if __name__ == "__main__":
    main()
