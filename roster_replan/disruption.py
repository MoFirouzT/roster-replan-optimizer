"""The objective, as a CP-SAT expression.

The model's reading of `replan.md`, and the counterpart to `scoring.py`. Neither imports
the other: brute-force stage (b) compares the optimum this module produces against the
minimum that module measures, and a shared helper would make that comparison an identity.

Everything here is linear. D4's convex concentration penalty in particular needs no
piecewise machinery, because a convex function being minimised is the maximum of its
segments' lines -- lower-bound one variable by each and let the objective settle it.
"""

from __future__ import annotations

from collections import defaultdict

from ortools.sat.python import cp_model

from .domain import Disruption, Instance


def objective_terms(
    model: cp_model.CpModel,
    instance: Instance,
    x: dict[tuple[int, int, int], cp_model.IntVar],
    shortfall: dict[tuple[int, int], cp_model.IntVar],
    mix_shortfall: dict[tuple[int, int, str], cp_model.IntVar],
) -> list:
    """Every objective term, ready to be summed and minimised."""
    params = instance.disruption
    if params is None:
        raise ValueError("the objective needs Instance.disruption")

    terms: list = []

    # Historical shortfall is excluded -- no replan repairs a started shift, and keeping
    # it adds a constant that makes two runs with different `now` incomparable.
    for (day, shift), slack in shortfall.items():
        if not instance.is_past(day, shift):
            terms.append(params.shortfall_weight * slack)
    for (day, shift, _), slack in mix_shortfall.items():
        if not instance.is_past(day, shift):
            terms.append(params.mix_shortfall_weight * slack)

    terms += _cost(instance, x, params)

    if instance.incumbent is None:
        # Generation: disruption is constant across rosters of equal coverage, so the
        # objective reduces to cost. A peak term breaks ties, because cost is indifferent
        # to *who* works. Explicitly a tie-breaker, not a fairness model.
        terms.append(params.peak_weight * _peak(model, instance, x))
        return terms

    if params.metric in ("D0", "D1", "D2"):
        terms += _per_assignment(instance, x, params)
    elif params.metric in ("D3", "D4"):
        terms += _per_event(model, instance, x, params)
    else:
        raise ValueError(f"unknown metric {params.metric!r}")

    return terms


def _slot_weight(instance: Instance, day: int, shift: int, params: Disruption) -> int:
    """P x N for one slot. D0 flattens both factors; D1 omits the notice multiplier."""
    if params.metric == "D0":
        return 1
    publication = (
        params.published_weight if instance.is_published(day, shift) else params.draft_weight
    )
    if params.metric == "D1":
        return publication
    return publication * params.notice_multiplier(instance.notice_hours(day, shift))


def _deviation(key, var, instance: Instance):
    """`1 - var` where the incumbent assigned this slot, `var` where it did not: either
    way, an expression that is 1 exactly when the roster deviates."""
    return 1 - var if key in (instance.incumbent or frozenset()) else var


# --- D0, D1, D2 ---------------------------------------------------------------------


def _per_assignment(instance: Instance, x, params: Disruption) -> list:
    return [
        _slot_weight(instance, day, shift, params) * _deviation((e, day, shift), var, instance)
        for (e, day, shift), var in x.items()
    ]


# --- D3 and D4 ----------------------------------------------------------------------
# Drops and adds are paired per (employee, day) so a moved shift is one event rather than
# two. `min` is what does the pairing, and CP-SAT expresses it directly.


def _per_event(model: cp_model.CpModel, instance: Instance, x, params: Disruption) -> list:
    incumbent = instance.incumbent or frozenset()
    dropped: dict[tuple[int, int], list] = defaultdict(list)
    added: dict[tuple[int, int], list] = defaultdict(list)

    for (employee, day, shift), var in x.items():
        bucket = dropped if (employee, day, shift) in incumbent else added
        bucket[employee, day].append(1 - var if (employee, day, shift) in incumbent else var)

    terms: list = []
    events: dict[int, list] = defaultdict(list)

    for key in set(dropped) | set(added):
        employee, day = key
        drops_here, adds_here = dropped[key], added[key]
        limit = max(len(drops_here), len(adds_here))

        drops = model.new_int_var(0, len(drops_here), f"drops_{employee}_{day}")
        adds = model.new_int_var(0, len(adds_here), f"adds_{employee}_{day}")
        model.add(drops == sum(drops_here))
        model.add(adds == sum(adds_here))

        moves = model.new_int_var(0, limit, f"moves_{employee}_{day}")
        model.add_min_equality(moves, [drops, adds])

        weight = _slot_weight(instance, day, instance.day_anchor(day), params)
        terms.append(
            weight
            * (
                params.move_weight * moves
                + params.cancel_weight * (drops - moves)
                + params.call_in_weight * (adds - moves)
            )
        )
        # Event count for D4: moves + residual drops + residual adds == drops + adds - moves.
        events[employee].append(drops + adds - moves)

    if params.metric == "D4":
        terms += _concentration(model, events, params, bound=len(instance.open_shifts))
    return terms


def _concentration(
    model: cp_model.CpModel, events: dict[int, list], params: Disruption, *, bound: int
) -> list:
    """The convex penalty, as lower bounds rather than a piecewise construction.

    `f(n) = max_k (k*n - k(k-1)/2)` is convex and is being minimised, so bounding one
    variable below by every segment's line leaves it at exactly `f(n)`. No products, no
    auxiliary booleans, no discretisation.

    `bound` is the number of open shifts: an employee cannot change more slots than exist.
    """
    terms = []
    tiers = params.concentration_tiers
    for employee, counts in events.items():
        total = model.new_int_var(0, bound, f"events_{employee}")
        model.add(total == sum(counts))

        penalty = model.new_int_var(0, tiers * bound, f"conc_{employee}")
        for k in range(1, tiers + 1):
            model.add(penalty >= k * total - k * (k - 1) // 2)
        terms.append(params.concentration_weight * penalty)
    return terms


def fairness_terms(
    model: cp_model.CpModel,
    instance: Instance,
    x: dict[tuple[int, int, int], cp_model.IntVar],
) -> list:
    """Rolling balance of unpopular shifts (`replan.md`, `D-108`).

    The same convex trick as `_concentration`, on a different quantity: an employee's
    unpopular count is what they worked before the horizon plus what this roster gives
    them, and `g` escalates so the cheapest way to spend a fixed number of unpopular
    shifts is to spread them.

    Kept out of `objective_terms` rather than folded into it because fairness is not a
    disruption metric — it is orthogonal to D0–D4 and a tenant can want either alone. The
    caller adds both lists.
    """
    params = instance.fairness
    if params is None or not params.active:
        return []

    terms = []
    horizon_max = len(instance.open_shifts)
    for employee, person in enumerate(instance.employees):
        prior = person.unpopular_shifts_before_horizon
        assigned = [
            var
            for (candidate, _, shift), var in x.items()
            if candidate == employee and shift in params.unpopular_shifts
        ]
        if not assigned and not prior:
            # Nothing to balance and nothing carried: `g(0) = 0`, so the variable would be
            # pinned at zero and contribute nothing but build time.
            continue

        ceiling = prior + horizon_max
        total = model.new_int_var(0, ceiling, f"unpopular_{employee}")
        model.add(total == prior + sum(assigned))

        penalty = model.new_int_var(0, params.tiers * ceiling, f"fair_{employee}")
        for k in range(1, params.tiers + 1):
            model.add(penalty >= k * total - k * (k - 1) // 2)
        terms.append(params.weight * penalty)
    return terms


# --- Cost and the tie-breaker -------------------------------------------------------


def _cost(instance: Instance, x, params: Disruption) -> list:
    """Placeholder: paid minutes at a flat rate. See `replan.md` -- overtime premiums,
    flexi rates and shift differentials are all T2, with the wage data that would make
    them mean something."""
    terms = []
    for (employee, _, shift), var in x.items():
        rate = instance.employees[employee].hourly_rate
        minutes = round(instance.shift_types[shift].work_hours * 60)
        terms.append(params.cost_weight * round(minutes * (1.0 if rate is None else rate)) * var)
    return terms


def _peak(model: cp_model.CpModel, instance: Instance, x) -> cp_model.IntVar:
    peak = model.new_int_var(0, len(instance.open_shifts), "peak")
    for employee in range(len(instance.employees)):
        model.add(peak >= sum(var for key, var in x.items() if key[0] == employee))
    return peak
