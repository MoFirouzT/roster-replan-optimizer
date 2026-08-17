"""The independent checker: a second reading of `docs/specs/rules.md`.

Imports no solver. Imports only `domain`, which carries the payload schema and the
conventions `rules.md` fixes by definition. Every rule predicate here is written from
the spec, not from the model -- that duplication is what makes the differential harness
meaningful, so resist any urge to factor a helper out of this module and into a place
the model could reach.

Three prohibitions from `validation.md`, restated because each is a way a checker
quietly stops testing the roster:

1. Never recompute a caller-supplied quantity (budgets, streak history, eligibility).
2. Never read the solver's own slack -- shortfalls are recounted from the roster.
3. Never consume the model's eligibility mask -- the mask is the thing under test.

`R-MIN-SHIFT` is absent by design: no reachable roster can violate it, so it is input
validation. See `validation.py`.
"""

from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass

from .domain import DAYS_PER_WEEK, FLEXI, Employee, Instance, Interval, Roster


@dataclass(frozen=True, slots=True)
class Violation:
    """A rule broken by a roster, with the coordinates a planner needs to act.

    `soft` marks a violation that is priced rather than prohibited: a returned roster
    can be optimal and still carry these. `historical` marks one on a shift that has
    already started, which no replan can repair.
    """

    rule: str
    message: str
    employee: int | None = None
    day: int | None = None
    shift: int | None = None
    observed: float | int | str | None = None
    required: float | int | str | None = None
    soft: bool = False
    historical: bool = False

    def key(self) -> tuple:
        """Identity for set comparison in the differential harness -- coordinates and
        rule only. Messages are prose and must not affect equivalence."""
        return (self.rule, self.employee, self.day, self.shift)


def check(roster: Roster, instance: Instance) -> list[Violation]:
    """Every rule violated by `roster`, hard and soft, in a deterministic order."""
    violations: list[Violation] = []
    violations += _cover(roster, instance)
    violations += _skill_mix(roster, instance)
    violations += _avail(roster, instance)
    violations += _skill(roster, instance)
    violations += _flexi_elig(roster, instance)
    violations += _dimona(roster, instance)
    violations += _pin_past(roster, instance)
    violations += _rest_gap(roster, instance)
    violations += _weekly_rest(roster, instance)
    violations += _max_weekly(roster, instance)
    violations += _max_period(roster, instance)
    violations += _max_daily(roster, instance)
    violations += _consec_days(roster, instance)
    violations += _max_weekends(roster, instance)
    violations += _min_days_off(roster, instance)
    violations += _min_block(roster, instance)
    violations += _max_shifts_per_type(roster, instance)
    violations += _min_hours(roster, instance)
    violations += _succession(roster, instance)
    return sorted(violations, key=lambda v: (v.rule, _nk(v.employee), _nk(v.day), _nk(v.shift)))


def is_feasible(roster: Roster, instance: Instance) -> bool:
    """Hard feasibility. Soft violations are priced, not disqualifying."""
    return not any(not v.soft for v in check(roster, instance))


def _nk(value: int | None) -> int:
    """Sort key placing `None` before any index."""
    return -1 if value is None else value


def _by_employee(roster: Roster, count: int) -> list[list[tuple[int, int]]]:
    grouped: list[list[tuple[int, int]]] = [[] for _ in range(count)]
    for employee, day, shift in roster:
        grouped[employee].append((day, shift))
    return grouped


def _label(instance: Instance, day: int, shift: int) -> str:
    window = instance.window(day, shift)
    return (
        f"day {day} {instance.shift_types[shift].label} "
        f"({window.start % 24:g}:00-{window.end % 24:g}:00)"
    )


# --- R-COVER ------------------------------------------------------------------------
# Hard ceiling, soft floor. The ceiling can never be the sole cause of infeasibility
# (the empty roster satisfies it), so the split adds no infeasibility surface.


def _cover(roster: Roster, instance: Instance) -> list[Violation]:
    headcount: dict[tuple[int, int], int] = defaultdict(int)
    for _, day, shift in roster:
        headcount[day, shift] += 1

    out = []
    for open_shift in instance.open_shifts:
        seen = headcount[open_shift.day, open_shift.shift]
        past = instance.is_past(open_shift.day, open_shift.shift)
        if seen > open_shift.required:
            out.append(
                Violation(
                    rule="R-COVER",
                    message=f"{_label(instance, open_shift.day, open_shift.shift)} is "
                    f"overstaffed: {seen} assigned, {open_shift.required} required",
                    day=open_shift.day,
                    shift=open_shift.shift,
                    observed=seen,
                    required=open_shift.required,
                    historical=past,
                )
            )
        elif seen < open_shift.required:
            out.append(
                Violation(
                    rule="R-COVER",
                    message=f"{_label(instance, open_shift.day, open_shift.shift)} is "
                    f"{open_shift.required - seen} short of its "
                    f"{open_shift.required} required staff",
                    day=open_shift.day,
                    shift=open_shift.shift,
                    observed=seen,
                    required=open_shift.required,
                    soft=True,
                    historical=past,
                )
            )
    return out


# --- R-SKILL-MIX --------------------------------------------------------------------
# Clamped to the headcount actually rostered: a missing body is R-COVER's finding, and
# reporting it twice makes shortfalls incomparable across instances.


def _skill_mix(roster: Roster, instance: Instance) -> list[Violation]:
    assigned: dict[tuple[int, int], list[int]] = defaultdict(list)
    for employee, day, shift in roster:
        assigned[day, shift].append(employee)

    out = []
    for open_shift in instance.open_shifts:
        on_shift = assigned[open_shift.day, open_shift.shift]
        for entry in open_shift.skill_mix:
            holders = sum(1 for e in on_shift if entry.skill in instance.employees[e].skills)
            needed = min(entry.minimum, len(on_shift))
            if holders < needed:
                out.append(
                    Violation(
                        rule="R-SKILL-MIX",
                        message=f"{_label(instance, open_shift.day, open_shift.shift)} has "
                        f"{len(on_shift)} staff but {holders} with {entry.skill!r}; "
                        f"{needed} required",
                        day=open_shift.day,
                        shift=open_shift.shift,
                        observed=holders,
                        required=needed,
                        soft=not entry.hard,
                        historical=instance.is_past(open_shift.day, open_shift.shift),
                    )
                )
    return out


# --- R-AVAIL ----------------------------------------------------------------------
# Interval intersection, not day equality: an unavailability of 09:00-12:00 must not
# block an evening shift, and a span crossing midnight belongs partly to the next day.


def _avail(roster: Roster, instance: Instance) -> list[Violation]:
    out = []
    for employee, day, shift in sorted(roster):
        person = instance.employees[employee]
        window = instance.window(day, shift)
        for blocked, kind in ((person.absences, "absent"), (person.unavailability, "unavailable")):
            hit = next((b for b in blocked if window.overlaps(b)), None)
            if hit is not None:
                out.append(
                    Violation(
                        rule="R-AVAIL",
                        message=f"{person.name} declared {kind} "
                        f"{hit.start:g}-{hit.end:g}h, which overlaps "
                        f"{_label(instance, day, shift)}",
                        employee=employee,
                        day=day,
                        shift=shift,
                        observed=kind,
                        required="no overlap",
                    )
                )
                break
    return out


# --- R-SKILL ----------------------------------------------------------------------


def _skill(roster: Roster, instance: Instance) -> list[Violation]:
    out = []
    for employee, day, shift in sorted(roster):
        person = instance.employees[employee]
        required = _required_skills(instance, day, shift)
        missing = required - person.skills
        if missing:
            out.append(
                Violation(
                    rule="R-SKILL",
                    message=f"{_label(instance, day, shift)} requires "
                    f"{', '.join(sorted(missing))}; {person.name} does not hold it",
                    employee=employee,
                    day=day,
                    shift=shift,
                    observed=", ".join(sorted(person.skills)) or "none",
                    required=", ".join(sorted(required)),
                )
            )
    return out


def _required_skills(instance: Instance, day: int, shift: int) -> frozenset[str]:
    for open_shift in instance.open_shifts:
        if (open_shift.day, open_shift.shift) == (day, shift):
            return open_shift.required_skills
    return frozenset()


# --- R-FLEXI-ELIG and R-DIMONA-FLX ------------------------------------------------
# Both verified against the supplied per-day flag and never recomputed: the conditions
# behind them live in other employers' payrolls and in NSSO records. Separate rules
# because they fail for different reasons -- "cannot hold a flexi job" versus "the
# paperwork is not in" -- and produce different operator actions.


def _flexi_elig(roster: Roster, instance: Instance) -> list[Violation]:
    out = []
    for employee, day, shift in sorted(roster):
        person = instance.employees[employee]
        if person.contract == FLEXI and day not in (person.flexi_eligible or frozenset()):
            out.append(
                Violation(
                    rule="R-FLEXI-ELIG",
                    message=f"{person.name} is not flexi-eligible on day {day}",
                    employee=employee,
                    day=day,
                    shift=shift,
                    observed="ineligible",
                    required="eligible",
                )
            )
    return out


def _dimona(roster: Roster, instance: Instance) -> list[Violation]:
    out = []
    for employee, day, shift in sorted(roster):
        person = instance.employees[employee]
        if person.contract == FLEXI and day not in (person.dimona_ok or frozenset()):
            out.append(
                Violation(
                    rule="R-DIMONA-FLX",
                    message=f"no Dimona FLX on file for {person.name} on day {day}; "
                    f"she or he cannot be rostered to "
                    f"{instance.shift_types[shift].label}",
                    employee=employee,
                    day=day,
                    shift=shift,
                    observed="not filed",
                    required="filed and OK",
                )
            )
    return out


# --- R-PIN-PAST -------------------------------------------------------------------
# Pinning is not exemption: past assignments stay inside every other rule's sums. This
# function only verifies immutability; the other rules see past shifts like any other.


def _pin_past(roster: Roster, instance: Instance) -> list[Violation]:
    if instance.now is None or instance.incumbent is None:
        return []

    out = []
    for open_shift in instance.open_shifts:
        if not instance.is_past(open_shift.day, open_shift.shift):
            continue
        for employee in range(len(instance.employees)):
            key = (employee, open_shift.day, open_shift.shift)
            was, now = key in instance.incumbent, key in roster
            if was == now:
                continue
            verb = "removed from" if was else "added to"
            out.append(
                Violation(
                    rule="R-PIN-PAST",
                    message=f"{_label(instance, open_shift.day, open_shift.shift)} has "
                    f"already started; {instance.employees[employee].name} "
                    f"cannot be {verb} it",
                    employee=employee,
                    day=open_shift.day,
                    shift=open_shift.shift,
                    observed="assigned" if now else "unassigned",
                    required="assigned" if was else "unassigned",
                    historical=True,
                )
            )
    return out


# --- R-REST-GAP -------------------------------------------------------------------
# `last_shift_end_before_horizon` is the zeroth element of the sequence, not a special
# case -- the framing that stops the horizon boundary being forgotten. Overlap is the
# degenerate case: an overlapping pair has a negative gap.


def _rest_gap(roster: Roster, instance: Instance) -> list[Violation]:
    minimum = instance.params.min_rest_hours
    out = []
    for employee, shifts in enumerate(_by_employee(roster, len(instance.employees))):
        person = instance.employees[employee]
        previous_end = person.last_shift_end_before_horizon
        for day, shift in sorted(shifts, key=lambda ds: instance.window(*ds).start):
            window = instance.window(day, shift)
            if previous_end is not None:
                gap = window.start - previous_end
                if gap < minimum:
                    out.append(
                        Violation(
                            rule="R-REST-GAP",
                            message=f"{person.name} finishes at {previous_end:g}h and would "
                            f"start {_label(instance, day, shift)} at "
                            f"{window.start:g}h -- {gap:g}h rest, {minimum:g}h required",
                            employee=employee,
                            day=day,
                            shift=shift,
                            observed=gap,
                            required=minimum,
                        )
                    )
            previous_end = window.end if previous_end is None else max(previous_end, window.end)
    return out


# --- R-WEEKLY-REST ----------------------------------------------------------------
# The model searches for a rest window; the checker measures the largest one. Two
# independent readings of the same requirement, which is the point.


def _weekly_rest(roster: Roster, instance: Instance) -> list[Violation]:
    minimum = instance.params.min_weekly_rest_hours
    out = []
    for employee, shifts in enumerate(_by_employee(roster, len(instance.employees))):
        person = instance.employees[employee]
        occupied = _merge([instance.window(d, s) for d, s in shifts])
        for week in range(instance.weeks):
            span = instance.week_span(week)
            longest = _longest_free_run(occupied, span, person)
            if longest < minimum:
                out.append(
                    Violation(
                        rule="R-WEEKLY-REST",
                        message=f"{person.name}'s longest rest in the week from day "
                        f"{instance.week_start_day(week)} is {longest:g}h; "
                        f"{minimum:g}h uninterrupted is required",
                        employee=employee,
                        day=instance.week_start_day(week),
                        observed=longest,
                        required=minimum,
                    )
                )
    return out


def _merge(intervals: list[Interval]) -> list[Interval]:
    """Union of possibly-overlapping intervals. An invalid roster may well overlap."""
    merged: list[Interval] = []
    for interval in sorted(intervals, key=lambda i: i.start):
        if merged and interval.start <= merged[-1].end:
            merged[-1] = Interval(merged[-1].start, max(merged[-1].end, interval.end))
        else:
            merged.append(interval)
    return merged


def _longest_free_run(occupied: list[Interval], span: Interval, person: Employee) -> float:
    """Longest stretch inside `span` touched by no assigned shift.

    A shift that ran into the span from before it shortens the first stretch; one that
    ended before the span began cannot, which is why the floor is a max.

    `occupied` is the employee's whole roster and may reach outside `span` in either
    direction -- a shift in a neighbouring week, or one that ran into the horizon from
    before it. Both are clipped rather than dropped: time a shift occupies inside this
    span is occupied, and time outside it is not rest this span can offer.
    """
    floor = span.start
    if person.last_shift_end_before_horizon is not None:
        floor = max(floor, person.last_shift_end_before_horizon)

    longest, cursor = 0.0, floor
    for interval in occupied:
        start = min(max(interval.start, span.start), span.end)
        end = min(max(interval.end, span.start), span.end)
        if start > cursor:
            longest = max(longest, start - cursor)
        cursor = max(cursor, end)
    return max(longest, span.end - cursor)


# --- R-MAX-WEEKLY and R-MAX-DAILY -------------------------------------------------
# Net working time, not span: breaks are not working time. The budget is verified as
# supplied and never rederived -- a checker that reaches for the reference period is
# testing the caller. A missing budget is an input defect, not a violation, so these
# stay silent rather than inventing a ceiling.


def _max_weekly(roster: Roster, instance: Instance) -> list[Violation]:
    out = []
    for employee, shifts in enumerate(_by_employee(roster, len(instance.employees))):
        person = instance.employees[employee]
        if person.max_hours_this_week is None:
            continue
        for week in range(instance.weeks):
            worked = sum(
                instance.shift_types[s].work_hours
                for d, s in shifts
                if instance.week_of(d) == week
            )
            if worked > person.max_hours_this_week:
                out.append(
                    Violation(
                        rule="R-MAX-WEEKLY",
                        message=f"{person.name} is budgeted "
                        f"{person.max_hours_this_week:g}h a week and this roster assigns "
                        f"{worked:g}h in the week from day {instance.week_start_day(week)}",
                        employee=employee,
                        day=instance.week_start_day(week),
                        observed=worked,
                        required=person.max_hours_this_week,
                    )
                )
    return out


# --- R-MAX-PERIOD ---------------------------------------------------------------------
# The horizon's whole sum against the reference period's remainder. Verified as supplied,
# never rederived: the caller owns the arithmetic that produced it and a checker that
# recomputes a reference period is testing the caller rather than the roster.


def _max_period(roster: Roster, instance: Instance) -> list[Violation]:
    out = []
    for employee, shifts in enumerate(_by_employee(roster, len(instance.employees))):
        person = instance.employees[employee]
        if person.max_hours_this_period is None:
            continue
        worked = sum(instance.shift_types[s].work_hours for _, s in shifts)
        if worked > person.max_hours_this_period:
            out.append(
                Violation(
                    rule="R-MAX-PERIOD",
                    message=f"{person.name} has {person.max_hours_this_period:g}h left in "
                    f"the reference period and this roster assigns {worked:g}h",
                    employee=employee,
                    observed=worked,
                    required=person.max_hours_this_period,
                )
            )
    return out


def _max_daily(roster: Roster, instance: Instance) -> list[Violation]:
    out = []
    for employee, shifts in enumerate(_by_employee(roster, len(instance.employees))):
        person = instance.employees[employee]
        if person.max_daily_hours is None:
            continue
        per_day: dict[int, float] = defaultdict(float)
        for day, shift in shifts:
            per_day[day] += instance.shift_types[shift].work_hours
        for day in sorted(per_day):
            if per_day[day] > person.max_daily_hours:
                out.append(
                    Violation(
                        rule="R-MAX-DAILY",
                        message=f"{person.name} is assigned {per_day[day]:g}h on day {day}; "
                        f"{person.max_daily_hours:g}h allowed",
                        employee=employee,
                        day=day,
                        observed=per_day[day],
                        required=person.max_daily_hours,
                    )
                )
    return out


# --- R-CONSEC-DAYS ----------------------------------------------------------------
# Operational/CBA, not statutory -- see the provenance correction in `rules.md`. The
# streak is initialised from history, because a week boundary is an artifact of the
# payload rather than of the employee's working life. Reported once per breaching run.


def _consec_days(roster: Roster, instance: Instance) -> list[Violation]:
    out = []
    for employee, shifts in enumerate(_by_employee(roster, len(instance.employees))):
        person = instance.employees[employee]
        # The employee's own limit where they have one, the tenant's otherwise (`D-136`).
        # Read here rather than shared with the model, like every other threshold.
        limit = person.max_consecutive_days
        if limit is None:
            limit = instance.params.max_consecutive_days
        if limit is None:
            continue

        worked = {day for day, _ in shifts}
        streak = person.consecutive_days_worked_before_horizon
        reported = False
        for day in range(instance.days):
            if day not in worked:
                streak, reported = 0, False
                continue
            streak += 1
            # The first breaching day of a run, not `streak == limit + 1`: a prior
            # streak already past the limit jumps the equality and would go unreported.
            if streak > limit and not reported:
                reported = True
                before = person.consecutive_days_worked_before_horizon
                prior = f" already worked {before} days before the horizon and" if before else ""
                out.append(
                    Violation(
                        rule="R-CONSEC-DAYS",
                        message=f"{person.name}{prior} reaches {streak} consecutive days "
                        f"at day {day}; {limit} allowed",
                        employee=employee,
                        day=day,
                        observed=streak,
                        required=limit,
                    )
                )
    return out


# --- R-MAX-WEEKENDS -----------------------------------------------------------------
# Count the distinct weeks in which the employee worked at least one weekend day, and
# compare. Deliberately *not* the model's formulation: that one forces a boolean up per
# week and sums it, this one collects the weeks into a set. Same rule, different arithmetic
# -- which is the whole purpose of two readings.


def _max_weekends(roster: Roster, instance: Instance) -> list[Violation]:
    weekend = instance.params.weekend_days
    if not weekend:
        return []

    out = []
    for employee, shifts in enumerate(_by_employee(roster, len(instance.employees))):
        limit = instance.employees[employee].max_weekends
        if limit is None:
            continue

        weeks = {
            instance.week_of(day) for day, _ in shifts if day % DAYS_PER_WEEK in weekend
        }
        if len(weeks) > limit:
            person = instance.employees[employee]
            out.append(
                Violation(
                    rule="R-MAX-WEEKENDS",
                    message=f"{person.name} works {len(weeks)} weekends; {limit} allowed",
                    employee=employee,
                    # The horizon's first day: the rule is a count over the whole payload,
                    # and no single week is the one that broke it.
                    day=0,
                    observed=len(weeks),
                    required=limit,
                )
            )
    return out


# --- R-MIN-DAYS-OFF -----------------------------------------------------------------
# Walk the days off and measure each stretch, against the model's forbidden-pattern
# encoding of the same rule.
#
# **Only interior stretches are judged** (`D-134`). A stretch reaching either end of the
# horizon may continue outside it, and a roster cannot be judged on days it does not
# contain. In the model this falls out of the pattern needing a worked day on both sides;
# here it has to be said, which is the usual asymmetry between the two readings.


def _min_days_off(roster: Roster, instance: Instance) -> list[Violation]:
    out = []
    for employee, shifts in enumerate(_by_employee(roster, len(instance.employees))):
        minimum = instance.employees[employee].min_consecutive_days_off
        if minimum is None or minimum < 2:
            continue

        worked = {day for day, _ in shifts}
        start = None
        for day in range(instance.days + 1):
            off = day < instance.days and day not in worked
            if off and start is None:
                start = day
            elif not off and start is not None:
                length = day - start
                if start > 0 and day < instance.days and length < minimum:
                    person = instance.employees[employee]
                    out.append(
                        Violation(
                            rule="R-MIN-DAYS-OFF",
                            message=f"{person.name} gets {length} day(s) off from day "
                            f"{start}; {minimum} consecutive required",
                            employee=employee,
                            day=start,
                            observed=length,
                            required=minimum,
                        )
                    )
                start = None
    return out


# --- R-MIN-BLOCK --------------------------------------------------------------------
# The mirror of `_min_days_off`, and written as its own walk rather than as that function
# with a flag: a shared helper parameterised by "worked or off" is one predicate serving
# two rules, and a defect in it would break both readings of both at once.
#
# Interior blocks only, for the reason `R-MIN-DAYS-OFF` gives about its own edges.


def _min_block(roster: Roster, instance: Instance) -> list[Violation]:
    out = []
    for employee, shifts in enumerate(_by_employee(roster, len(instance.employees))):
        minimum = instance.employees[employee].min_consecutive_days_worked
        if minimum is None or minimum < 2:
            continue

        worked = {day for day, _ in shifts}
        start = None
        for day in range(instance.days + 1):
            on = day < instance.days and day in worked
            if on and start is None:
                start = day
            elif not on and start is not None:
                length = day - start
                if start > 0 and day < instance.days and length < minimum:
                    person = instance.employees[employee]
                    out.append(
                        Violation(
                            rule="R-MIN-BLOCK",
                            message=f"{person.name} works a block of {length} day(s) from "
                            f"day {start}; {minimum} consecutive required",
                            employee=employee,
                            day=start,
                            observed=length,
                            required=minimum,
                        )
                    )
                start = None
    return out


# --- R-MAX-SHIFT-TYPE ---------------------------------------------------------------
# Count assignments of the capped type. A cap of zero is a prohibition and is reported the
# same way as any other breach -- the rule is the tenant's choice, not an impossibility,
# so it belongs in the violation list rather than in the presolve's exclusions.


def _max_shifts_per_type(roster: Roster, instance: Instance) -> list[Violation]:
    out = []
    for employee, shifts in enumerate(_by_employee(roster, len(instance.employees))):
        caps = instance.employees[employee].max_shifts_per_type
        if not caps:
            continue

        for shift, cap in sorted(caps.items()):
            worked = sum(1 for _, s in shifts if s == shift)
            if worked > cap:
                person = instance.employees[employee]
                label = instance.shift_types[shift].label
                out.append(
                    Violation(
                        rule="R-MAX-SHIFT-TYPE",
                        message=f"{person.name} works {worked} {label} shifts; {cap} allowed",
                        employee=employee,
                        day=0,
                        shift=shift,
                        observed=worked,
                        required=cap,
                    )
                )
    return out


# --- R-MIN-HOURS --------------------------------------------------------------------
# A floor, so the arithmetic is `R-MAX-PERIOD`'s with the comparison reversed. Net working
# time, under the same convention every hours rule here uses.


def _min_hours(roster: Roster, instance: Instance) -> list[Violation]:
    out = []
    for employee, shifts in enumerate(_by_employee(roster, len(instance.employees))):
        floor = instance.employees[employee].min_hours_this_period
        if floor is None:
            continue

        worked = sum(instance.shift_types[shift].work_hours for _, shift in shifts)
        if worked < floor:
            person = instance.employees[employee]
            out.append(
                Violation(
                    rule="R-MIN-HOURS",
                    message=f"{person.name} is assigned {worked:g}h; {floor:g}h is the "
                    f"minimum for the period",
                    employee=employee,
                    day=0,
                    observed=worked,
                    required=floor,
                )
            )
    return out


# --- R-SUCCESSION -------------------------------------------------------------------
# Which shift someone worked on each day, then every consecutive pair. An employee holding
# two shifts on one day makes several pairs, and each is checked: the rule is about the
# pairing, not about a canonical shift for the day.


def _succession(roster: Roster, instance: Instance) -> list[Violation]:
    pairs = instance.params.forbidden_successions
    if not pairs:
        return []

    by_day: dict[int, dict[int, list[int]]] = defaultdict(lambda: defaultdict(list))
    for employee, day, shift in roster:
        by_day[employee][day].append(shift)

    out = []
    for employee in sorted(by_day):
        days = by_day[employee]
        for day in sorted(days):
            for earlier in sorted(days[day]):
                for later in sorted(days.get(day + 1, [])):
                    if (earlier, later) not in pairs:
                        continue
                    person = instance.employees[employee]
                    out.append(
                        Violation(
                            rule="R-SUCCESSION",
                            message=f"{person.name} works "
                            f"{instance.shift_types[later].label} on day {day + 1}, which "
                            f"may not follow {instance.shift_types[earlier].label}",
                            employee=employee,
                            # The day the forbidden shift falls on, matching the model.
                            day=day + 1,
                            shift=later,
                            observed=instance.shift_types[earlier].label,
                            required=f"not after {instance.shift_types[earlier].label}",
                        )
                    )
    return out
