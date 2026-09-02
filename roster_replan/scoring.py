"""Independent evaluation of the objective on a concrete roster.

The same discipline `guide/rules.md` imposes on the checker, applied to the objective. Brute
force stage (b) compares the solver's optimum against the enumerated one, and that
comparison is worthless if the enumeration asks the model what a roster is worth. So this
module scores a roster from `internals/model.md` directly, imports no solver, and never touches
`disruption.py`.

Plain Python and integral throughout, matching the model's arithmetic exactly. Any
rounding difference between the two readings would surface as a false objective mismatch,
so both work in integer disruption points and integer minutes.
"""

from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass

from .domain import Disruption, Instance, Roster


@dataclass(frozen=True, slots=True)
class Score:
    """The objective, broken into the terms `internals/model.md` distinguishes.

    Reported separately rather than only as a total, because the coverage/disruption
    frontier needs both axes and a single number cannot be placed on a chart.
    """

    disruption: int
    shortfall: int
    mix_shortfall: int
    cost: int
    peak: int
    fairness: int = 0

    @property
    def total(self) -> int:
        return (
            self.disruption
            + self.shortfall
            + self.mix_shortfall
            + self.cost
            + self.peak
            + self.fairness
        )


def score(roster: Roster, instance: Instance) -> Score:
    params = instance.disruption
    if params is None:
        raise ValueError("scoring needs Instance.disruption")

    return Score(
        disruption=disruption_of(roster, instance),
        shortfall=_shortfall(roster, instance, params),
        mix_shortfall=_mix_shortfall(roster, instance, params),
        cost=_cost(roster, instance, params),
        peak=_peak(roster, instance, params),
        fairness=fairness_of(roster, instance),
    )


def fairness_of(roster: Roster, instance: Instance) -> int:
    """Rolling balance of unpopular shifts, read independently of the model (`D-108`).

    Deliberately written from `internals/model.md` rather than from `disruption.py`: this is the
    reading the differential harness compares the encoding against, so sharing a helper
    would make the comparison an identity. `_convex` is reused because it is *this*
    module's convex function, already used by D4.
    """
    params = instance.fairness
    if params is None or not params.active:
        return 0

    total = 0
    for employee, person in enumerate(instance.employees):
        worked = sum(
            1
            for (candidate, _, shift) in roster
            if candidate == employee and shift in params.unpopular_shifts
        )
        count = person.unpopular_shifts_before_horizon + worked
        total += _convex(count, params.tiers)
    return params.weight * total


# --- Disruption ---------------------------------------------------------------------


def disruption_of(roster: Roster, instance: Instance) -> int:
    """D0 through D4, per `internals/model.md`. Zero when there is no incumbent to deviate from."""
    params = instance.disruption
    if params is None:
        raise ValueError("scoring needs Instance.disruption")
    if instance.incumbent is None:
        return 0

    if params.metric in ("D0", "D1", "D2"):
        return _per_assignment(roster, instance, params)
    if params.metric == "D3":
        return _per_event(roster, instance, params)[0]
    if params.metric == "D4":
        total, events = _per_event(roster, instance, params)
        return total + params.concentration_weight * sum(
            _convex(count, params.concentration_tiers) for count in events.values()
        )
    raise ValueError(f"unknown metric {params.metric!r}")


def _changed(roster: Roster, instance: Instance) -> list[tuple[int, int, int, bool]]:
    """Changed slots as (employee, day, shift, was_dropped).

    Only slots that exist as open shifts are considered: a roster cannot deviate on a
    slot the instance does not have.
    """
    incumbent = instance.incumbent or frozenset()
    changes = []
    for employee in range(len(instance.employees)):
        for open_shift in instance.open_shifts:
            key = (employee, open_shift.day, open_shift.shift)
            before, after = key in incumbent, key in roster
            if before != after:
                changes.append((employee, open_shift.day, open_shift.shift, before))
    return changes


def _slot_weight(instance: Instance, day: int, shift: int, params: Disruption) -> int:
    """P x N for one slot. D0 flattens both factors to 1."""
    if params.metric == "D0":
        return 1
    publication = (
        params.published_weight if instance.is_published(day, shift) else params.draft_weight
    )
    if params.metric == "D1":
        return publication
    return publication * params.notice_multiplier(instance.notice_hours(day, shift))


def _per_assignment(roster: Roster, instance: Instance, params: Disruption) -> int:
    return sum(
        _slot_weight(instance, day, shift, params)
        for _, day, shift, _ in _changed(roster, instance)
    )


def _per_event(
    roster: Roster, instance: Instance, params: Disruption
) -> tuple[int, dict[int, int]]:
    """D3: drops and adds paired into moves, priced per (employee, day).

    `P` and `N` are read from the day's anchor slot -- solution-independent by
    construction, per the stated simplification in `internals/model.md`.
    """
    drops: dict[tuple[int, int], int] = defaultdict(int)
    adds: dict[tuple[int, int], int] = defaultdict(int)

    for employee, day, _, was_dropped in _changed(roster, instance):
        bucket = drops if was_dropped else adds
        bucket[employee, day] += 1

    total = 0
    events: dict[int, int] = defaultdict(int)
    for key in set(drops) | set(adds):
        employee, day = key
        dropped, added = drops[key], adds[key]
        moves = min(dropped, added)
        weight = _slot_weight(instance, day, instance.day_anchor(day), params)
        total += weight * (
            params.move_weight * moves
            + params.cancel_weight * (dropped - moves)
            + params.call_in_weight * (added - moves)
        )
        events[employee] += moves + (dropped - moves) + (added - moves)
    return total, dict(events)


def _convex(count: int, tiers: int) -> int:
    """f(n) = max_k (k*n - k(k-1)/2) for k = 1..tiers -- the triangular escalation."""
    if count <= 0 or tiers <= 0:
        return 0
    return max(k * count - k * (k - 1) // 2 for k in range(1, tiers + 1))


# --- The other terms ----------------------------------------------------------------


def _headcount(roster: Roster) -> dict[tuple[int, int], int]:
    counts: dict[tuple[int, int], int] = defaultdict(int)
    for _, day, shift in roster:
        counts[day, shift] += 1
    return counts


def _shortfall(roster: Roster, instance: Instance, params: Disruption) -> int:
    """Historical shortfall is excluded: no replan repairs a shift that has started, and
    including it makes two runs with different `now` incomparable."""
    counts = _headcount(roster)
    short = sum(
        max(0, o.required - counts[o.day, o.shift])
        for o in instance.open_shifts
        if not instance.is_past(o.day, o.shift)
    )
    return params.shortfall_weight * short


def _mix_shortfall(roster: Roster, instance: Instance, params: Disruption) -> int:
    assigned: dict[tuple[int, int], list[int]] = defaultdict(list)
    for employee, day, shift in roster:
        assigned[day, shift].append(employee)

    total = 0
    for open_shift in instance.open_shifts:
        if instance.is_past(open_shift.day, open_shift.shift):
            continue
        on_shift = assigned[open_shift.day, open_shift.shift]
        for entry in open_shift.skill_mix:
            if entry.hard:
                continue
            holders = sum(1 for e in on_shift if entry.skill in instance.employees[e].skills)
            total += max(0, min(entry.minimum, len(on_shift)) - holders)
    return params.mix_shortfall_weight * total


def _cost(roster: Roster, instance: Instance, params: Disruption) -> int:
    """Placeholder cost model -- paid minutes at a flat rate. See `internals/model.md`."""
    total = 0
    for employee, _, shift in roster:
        rate = instance.employees[employee].hourly_rate
        minutes = round(instance.shift_types[shift].work_hours * 60)
        total += round(minutes * (1.0 if rate is None else rate))
    return params.cost_weight * total


def _peak(roster: Roster, instance: Instance, params: Disruption) -> int:
    """Tie-breaker for cold solves, where cost is indifferent to *who* works. Not a
    fairness model -- that is `fairness_of` above."""
    if instance.incumbent is not None or not roster:
        return 0
    counts: dict[int, int] = defaultdict(int)
    for employee, _, _ in roster:
        counts[employee] += 1
    return params.peak_weight * max(counts.values())


# --- The domination bound -----------------------------------------------------------


def max_change_weight(instance: Instance) -> int:
    """The largest disruption a single changed assignment can carry.

    Used by `validation.py` to check the bound in `internals/model.md`. It lives here rather than
    there because it is a property of the metric, and the metric is this module's
    subject.
    """
    params = instance.disruption
    if params is None:
        return 0

    if params.metric == "D0":
        per_slot = 1
    else:
        bands = max((b.multiplier for b in params.notice_bands), default=1)
        per_slot = params.published_weight * (1 if params.metric == "D1" else bands)

    if params.metric in ("D0", "D1", "D2"):
        return per_slot

    by_type = max(params.move_weight, params.cancel_weight, params.call_in_weight)
    escalation = params.concentration_weight * params.concentration_tiers
    return per_slot * by_type + (escalation if params.metric == "D4" else 0)
