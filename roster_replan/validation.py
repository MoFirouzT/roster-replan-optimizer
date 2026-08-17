"""Input validation: is this payload well-formed and lawful *as a request*?

Distinct from the checker, and the dividing question is whether a different roster could
fix the fault. If none could, it belongs here. Conflating the two is how a caller's
arithmetic error gets reported as a solver defect -- and a caller fixes a defect where a
planner reads a violation, so the two never share a result list.

`R-MIN-SHIFT` lives here in full: with fixed shift instances no reachable roster can
contain a work period the catalogue does not already contain, so a too-short shift is a
profile defect. It becomes a real constraint in T5 generation mode, where shift
boundaries become decision variables.

This module may hold statutory baselines -- it is not one of the two independent
readings, so `rules.md`'s no-shared-thresholds discipline does not reach it. The model
and the checker still receive every parameter explicitly through the payload.
"""

from __future__ import annotations

from dataclasses import dataclass

from .domain import DAYS_PER_WEEK, FLEXI, Instance
from .scoring import max_change_weight

# Statutory baselines, used only to decide whether a supplied parameter is a derogation
# needing a recorded basis. Arbeidswet art. 19 and art. 21; art. 38ter §1 and §3.
STATUTORY_MIN_PERIOD_HOURS = 3.0
STATUTORY_MIN_REST_HOURS = 11.0
STATUTORY_MIN_WEEKLY_REST_HOURS = 35.0

# The derogation ladder caps any individual week regardless of the reference-period
# average: generally 50h, and 45h under art. 20bis flexible schedules.
ABSOLUTE_WEEKLY_CEILING_HOURS = 50.0

# art. 19 baseline, with the lawful ladder from art. 20 §1, art. 20bis, art. 20 §2 and
# art. 22 1°-2°. Further derogations exist by sectoral CBA, hence the ceiling not a set.
ABSOLUTE_DAILY_CEILING_HOURS = 12.0


@dataclass(frozen=True, slots=True)
class InputDefect:
    """A malformed or unlawful request. Addressed to the caller, not to a planner."""

    field: str
    message: str
    observed: object = None
    required: object = None


def validate_instance(instance: Instance) -> list[InputDefect]:
    """Every defect in `instance`. A non-empty result rejects the request outright --
    a payload that is not well-formed has no meaningful optimum to degrade towards."""
    defects: list[InputDefect] = []
    defects += _min_shift(instance)
    defects += _horizon_span(instance)
    defects += _derogations(instance)
    defects += _replan_pair(instance)
    defects += _shift_catalogue(instance)
    defects += _employees(instance)
    defects += _skill_mix_provenance(instance)
    defects += _weight_domination(instance)
    defects += _weekend_days(instance)
    return defects


# --- The domination bound -----------------------------------------------------------
# Understaffing reduces disruption: an unstaffed shift is a shift nobody was moved onto.
# So a shortfall weight that is too low lets the optimiser buy stability by leaving
# shifts empty -- a failure that looks like a tuning problem and is an ordering error.
#
# `replan.md` derives the bound rather than choosing it, which makes it checkable, so it
# is checked. A weight scale that violates it is a malformed request, not a preference.
#
# **Fairness pays for understaffing too** (`D-108`). An unstaffed unpopular shift is one
# nobody's rolling count went up for, so the fairness term gives the optimiser a second
# reason to leave one empty and the bound has to cover it. `tiers` is the escalation's
# steepest slope, so `weight x tiers` is the most one extra unpopular assignment can cost.


def _weight_domination(instance: Instance) -> list[InputDefect]:
    params = instance.disruption
    if params is None or not instance.open_shifts:
        return []

    largest_demand = max(o.required for o in instance.open_shifts)
    fair = instance.fairness
    per_assignment = max_change_weight(instance)
    if fair is not None and fair.active:
        per_assignment += fair.weight * fair.tiers
    bound = largest_demand * per_assignment
    if params.shortfall_weight > bound:
        return []
    return [
        InputDefect(
            field="disruption.shortfall_weight",
            message=f"shortfall_weight of {params.shortfall_weight} does not dominate the "
            f"{bound} of disruption and fairness that leaving one shift unstaffed can "
            f"avoid, so the optimiser could buy stability by understaffing",
            observed=params.shortfall_weight,
            required=f"> {bound}",
        )
    ]


# --- R-MIN-SHIFT --------------------------------------------------------------------
# Gross span, not net: art. 21 governs the work *period*, and a "prestatie" may contain
# short meal or coffee breaks without becoming two periods.


def _min_shift(instance: Instance) -> list[InputDefect]:
    minimum = instance.params.min_period_hours
    return [
        InputDefect(
            field=f"shift_types[{index}].span_hours",
            message=f"shift type {shift.label!r} spans {shift.span_hours:g}h, "
            f"below the {minimum:g}h minimum work period",
            observed=shift.span_hours,
            required=minimum,
        )
        for index, shift in enumerate(instance.shift_types)
        if shift.span_hours < minimum
    ]


# --- Derogations --------------------------------------------------------------------
# A legality claim with no named source is exactly what `rules.md` exists to prevent, so
# any parameter looser than its statutory baseline must carry one. Stricter than
# statute is always lawful and needs nothing.


def _derogations(instance: Instance) -> list[InputDefect]:
    params = instance.params
    looser = [
        ("min_period_hours", params.min_period_hours, STATUTORY_MIN_PERIOD_HOURS),
        ("min_rest_hours", params.min_rest_hours, STATUTORY_MIN_REST_HOURS),
        (
            "min_weekly_rest_hours",
            params.min_weekly_rest_hours,
            STATUTORY_MIN_WEEKLY_REST_HOURS,
        ),
    ]
    return [
        InputDefect(
            field=f"params.derogation_basis[{name!r}]",
            message=f"{name} of {value:g} is below the statutory {baseline:g} and needs a "
            f"recorded derogation basis",
            observed=value,
            required=baseline,
        )
        for name, value, baseline in looser
        if value < baseline and not params.derogation_basis.get(name, "").strip()
    ]


# --- Replan inputs ------------------------------------------------------------------


def _replan_pair(instance: Instance) -> list[InputDefect]:
    if (instance.now is None) == (instance.incumbent is None):
        return []
    missing = "incumbent" if instance.incumbent is None else "now"
    return [
        InputDefect(
            field=missing,
            message=f"a replan needs both `now` and `incumbent`; {missing} is missing. "
            f"R-PIN-PAST cannot pin a past it has no incumbent for",
            observed=None,
            required="present",
        )
    ]


# --- A horizon the week rules can be stated over --------------------------------------
# `D-110` refused any horizon past a week, because both readings then scoped the week
# rules to the horizon and would have agreed an unlawful roster was fine. `D-111` scoped
# them to the week, so a longer horizon is answerable and this is what is left of the
# guard (`D-113`): the horizon must not end **part-way through a week**.
#
# `R-WEEKLY-REST` requires its window to lie inside the week it counts for, so a horizon
# of ten days ends in a three-day stub that cannot hold 35 hours however the roster is
# arranged. The model reports that honestly -- the gate goes false and the solve is
# infeasible naming `R-WEEKLY-REST` -- and a planner reading "no legal roster exists"
# because of a week that is mostly not in the payload has been told the truth and given
# nothing to do with it.
#
# **A week or less stays legal, unchanged.** There the same requirement is too *strict*
# rather than unanswerable, which `D-029` records and prices as conservatism: one week is
# the case the service has always served, and a three-day horizon still gets a roster.


def _horizon_span(instance: Instance) -> list[InputDefect]:
    if instance.days <= DAYS_PER_WEEK or instance.days % DAYS_PER_WEEK == 0:
        return []
    weeks = instance.days // DAYS_PER_WEEK
    stub = instance.days % DAYS_PER_WEEK
    return [
        InputDefect(
            "days",
            f"horizon of {instance.days} days ends {stub} day(s) into week {weeks + 1}. "
            f"R-WEEKLY-REST needs its window inside the week it counts for, and no roster "
            f"can put {instance.params.min_weekly_rest_hours:g}h inside a {stub}-day stub",
            instance.days,
            f"{DAYS_PER_WEEK} or fewer, or a multiple of {DAYS_PER_WEEK}",
        )
    ]


def _shift_catalogue(instance: Instance) -> list[InputDefect]:
    defects = []
    if instance.days <= 0:
        defects.append(
            InputDefect("days", f"horizon of {instance.days} days", instance.days, "> 0")
        )

    seen: set[tuple[int, int]] = set()
    for index, open_shift in enumerate(instance.open_shifts):
        where = f"open_shifts[{index}]"
        if not 0 <= open_shift.day < instance.days:
            defects.append(
                InputDefect(
                    f"{where}.day",
                    f"day {open_shift.day} is outside a {instance.days}-day horizon",
                    open_shift.day,
                    f"0..{instance.days - 1}",
                )
            )
        if not 0 <= open_shift.shift < len(instance.shift_types):
            defects.append(
                InputDefect(
                    f"{where}.shift",
                    f"shift type {open_shift.shift} is not in the catalogue",
                    open_shift.shift,
                    f"0..{len(instance.shift_types) - 1}",
                )
            )
        if open_shift.required < 0:
            defects.append(
                InputDefect(
                    f"{where}.required",
                    f"required headcount {open_shift.required} is negative",
                    open_shift.required,
                    ">= 0",
                )
            )
        key = (open_shift.day, open_shift.shift)
        if key in seen:
            defects.append(
                InputDefect(
                    where,
                    f"duplicate open shift for day {open_shift.day}, "
                    f"shift type {open_shift.shift}",
                    key,
                    "unique",
                )
            )
        seen.add(key)
    return defects


# --- Employees ----------------------------------------------------------------------
# The budget checks are input validation and not R-MAX-WEEKLY violations: a too-large
# budget is the caller's arithmetic, and no roster could repair it.


def _employees(instance: Instance) -> list[InputDefect]:
    defects = []
    for index, person in enumerate(instance.employees):
        where = f"employees[{index}]"

        if person.max_hours_this_week is None:
            defects.append(
                InputDefect(
                    f"{where}.max_hours_this_week",
                    f"{person.name} has no weekly budget. It is caller-computed and "
                    f"mandatory -- a default weekly ceiling is the wrong model",
                    None,
                    "hours",
                )
            )
        elif person.max_hours_this_week > ABSOLUTE_WEEKLY_CEILING_HOURS:
            defects.append(
                InputDefect(
                    f"{where}.max_hours_this_week",
                    f"{person.name}'s budget of {person.max_hours_this_week:g}h exceeds the "
                    f"{ABSOLUTE_WEEKLY_CEILING_HOURS:g}h absolute weekly ceiling",
                    person.max_hours_this_week,
                    ABSOLUTE_WEEKLY_CEILING_HOURS,
                )
            )
        elif person.max_hours_this_week < 0:
            defects.append(
                InputDefect(
                    f"{where}.max_hours_this_week",
                    f"{person.name} has a negative budget",
                    person.max_hours_this_week,
                    ">= 0",
                )
            )

        if person.max_daily_hours is None:
            defects.append(
                InputDefect(
                    f"{where}.max_daily_hours",
                    f"{person.name} has no daily maximum",
                    None,
                    "hours",
                )
            )
        elif person.max_daily_hours > ABSOLUTE_DAILY_CEILING_HOURS:
            defects.append(
                InputDefect(
                    f"{where}.max_daily_hours",
                    f"{person.name}'s daily maximum of {person.max_daily_hours:g}h exceeds "
                    f"the {ABSOLUTE_DAILY_CEILING_HOURS:g}h lawful ceiling",
                    person.max_daily_hours,
                    ABSOLUTE_DAILY_CEILING_HOURS,
                )
            )

        # A reference period with negative time left is arithmetic that went wrong
        # upstream, and it makes every roster illegal including the empty one -- so it is
        # a malformed request rather than an infeasible instance (`D-123`).
        if person.max_hours_this_period is not None and person.max_hours_this_period < 0:
            defects.append(
                InputDefect(
                    f"{where}.max_hours_this_period",
                    f"{person.name} has {person.max_hours_this_period:g}h left in the "
                    f"reference period, which no roster can satisfy",
                    person.max_hours_this_period,
                    ">= 0",
                )
            )

        if person.consecutive_days_worked_before_horizon < 0:
            defects.append(
                InputDefect(
                    f"{where}.consecutive_days_worked_before_horizon",
                    f"{person.name} has a negative prior streak",
                    person.consecutive_days_worked_before_horizon,
                    ">= 0",
                )
            )

        if person.contract == FLEXI:
            for gate in ("flexi_eligible", "dimona_ok"):
                if getattr(person, gate) is None:
                    defects.append(
                        InputDefect(
                            f"{where}.{gate}",
                            f"{person.name} is on a flexi contract with no {gate}. It is "
                            f"resolved upstream and mandatory -- absence must never "
                            f"default to eligible",
                            None,
                            "set of days",
                        )
                    )
    return defects


def _skill_mix_provenance(instance: Instance) -> list[InputDefect]:
    return [
        InputDefect(
            field=f"open_shifts[{index}].skill_mix[{position}].provenance",
            message=f"hard skill-mix entry for {entry.skill!r} claims legal force with no "
            f"named source",
            observed="",
            required="non-empty",
        )
        for index, open_shift in enumerate(instance.open_shifts)
        for position, entry in enumerate(open_shift.skill_mix)
        if entry.hard and not entry.provenance.strip()
    ]


# --- R-MAX-WEEKENDS's calendar ------------------------------------------------------
# A day index outside a week is not a stricter weekend, it is a typo that switches the
# rule off for the days it names. `weekend_days` is the one parameter in this payload a
# caller states in a coordinate system they do not otherwise use, so it is checked rather
# than trusted (`D-135`).


def _weekend_days(instance: Instance) -> list[InputDefect]:
    out = []
    for day in sorted(instance.params.weekend_days):
        if not 0 <= day < DAYS_PER_WEEK:
            out.append(
                InputDefect(
                    field="params.weekend_days",
                    message=f"weekend day {day} is not a position in a week, so it names "
                    f"nothing and R-MAX-WEEKENDS would silently ignore it",
                    observed=day,
                    required=f"0 to {DAYS_PER_WEEK - 1}",
                )
            )
    return out
