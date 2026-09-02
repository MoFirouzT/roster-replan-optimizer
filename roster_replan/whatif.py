"""`what if I hire one more flexi-jobber?` — a sweep over machinery that already exists.

`guide/api.md` names this as the question owners actually ask, and it is the one tool in the
service's surface that is not a wrapper: the others expose a solve, a validation or an
explanation that already has a caller. This one composes them into an answer to a hypothetical.

The shape is deliberately narrow. A change is a **named, typed edit to the instance**, not an
arbitrary patch, for the same reason `explain.py` answers from the checker: a tool an LLM can
call is a tool that will be called with something unexpected, and a free-form patch endpoint
is an arbitrary-code hole wearing a schema. Each `Change` below is a transformation whose
effect on the rules is understood before it is applied.

## Two properties that make the answer trustworthy

**The comparison is paired and the incumbent is held.** Baseline and variant are solved from
the same published roster with the same seed, so the disruption difference is attributable to
the change rather than to a different starting point — the discipline `lab.py` applies to
timings, applied to outcomes.

**An unlawful hypothetical is refused, not answered.** Relaxing a statutory parameter needs a
recorded derogation basis, and `validation.py` already enforces that. A `what_if` that
quietly lowered `min_rest_hours` would answer *yes, hire nobody, just break the law* — the
most dangerous possible output from a tool a planner might trust. Changes are validated
before they are solved, and a rejection is returned as the answer.
"""

from __future__ import annotations

import dataclasses
from dataclasses import dataclass

from .checker import check
from .domain import Employee, Instance, Roster, RuleParams
from .explain import Shortfall, explain
from .model import solve
from .scoring import disruption_of
from .validation import InputDefect, validate_instance


@dataclass(frozen=True, slots=True)
class Change:
    """One typed edit. `kind` decides which of the remaining fields is read.

    A closed set rather than a patch: every kind here is one whose interaction with the rule
    registry was thought about, and adding a kind is a deliberate act rather than a caller's
    improvisation.
    """

    kind: str
    employee: int | None = None
    skills: tuple[str, ...] = ()
    contract: str = "salaried"
    weekly_hours: float | None = None
    daily_hours: float | None = None
    day: int | None = None
    shift: int | None = None
    required: int | None = None
    min_rest_hours: float | None = None
    max_consecutive_days: int | None = None
    derogation_basis: tuple[tuple[str, str], ...] = ()

    def describe(self) -> str:
        if self.kind == ADD_EMPLOYEE:
            skills = ", ".join(self.skills) if self.skills else "no listed skills"
            return f"hire one {self.contract} with {skills} at {self.weekly_hours}h/week"
        if self.kind == SET_WEEKLY_HOURS:
            who = "everyone" if self.employee is None else f"employee {self.employee}"
            return f"set {who}'s weekly hours to {self.weekly_hours}"
        if self.kind == SET_DAILY_HOURS:
            who = "everyone" if self.employee is None else f"employee {self.employee}"
            return f"set {who}'s daily hours to {self.daily_hours}"
        if self.kind == IGNORE_SKILL:
            skills = ", ".join(self.skills)
            return f"ignore that employee {self.employee} lacks the skill(s) {skills}"
        if self.kind == SET_REQUIRED:
            return f"set day {self.day} shift {self.shift} to {self.required} staff"
        if self.kind == RELAX_RULE:
            parts = []
            if self.min_rest_hours is not None:
                parts.append(f"min rest {self.min_rest_hours}h")
            if self.max_consecutive_days is not None:
                parts.append(f"max consecutive days {self.max_consecutive_days}")
            return "relax " + ", ".join(parts)
        raise ValueError(f"unknown change kind {self.kind!r}")


ADD_EMPLOYEE = "add_employee"
SET_WEEKLY_HOURS = "set_weekly_hours"
SET_DAILY_HOURS = "set_daily_hours"
IGNORE_SKILL = "ignore_skill"
SET_REQUIRED = "set_required"
RELAX_RULE = "relax_rule"

KINDS = (
    ADD_EMPLOYEE,
    SET_WEEKLY_HOURS,
    SET_DAILY_HOURS,
    IGNORE_SKILL,
    SET_REQUIRED,
    RELAX_RULE,
)


@dataclass(frozen=True, slots=True)
class Outcome:
    """One side of the comparison.

    The roster is carried, not just the summary numbers. A planner asking *what if I hire
    one more* wants to see the week that results, and the scalars cannot answer that. It is
    also the only field that makes the pairing checkable: two tied optima under D2 share an
    objective **and** a change count, so a baseline accidentally solved at the wrong seed is
    invisible in every summary and visible only here.
    """

    shortfall: int
    disruption: int
    changes_from_incumbent: int
    shortfalls: tuple[Shortfall, ...]
    roster: Roster


@dataclass(frozen=True, slots=True)
class Comparison:
    """Baseline against variant, with the difference stated in the direction that helps.

    `defects` non-empty means the hypothetical was refused rather than answered — the
    variant was unlawful or malformed, and `variant` is `None`.
    """

    described: tuple[str, ...]
    baseline: Outcome
    variant: Outcome | None
    defects: tuple[InputDefect, ...] = ()

    @property
    def refused(self) -> bool:
        return self.variant is None

    @property
    def shortfall_delta(self) -> int:
        """Negative is an improvement: positions filled that were not before."""
        if self.variant is None:
            return 0
        return self.variant.shortfall - self.baseline.shortfall

    @property
    def disruption_delta(self) -> int:
        if self.variant is None:
            return 0
        return self.variant.disruption - self.baseline.disruption

    def summary(self) -> str:
        if self.refused:
            reasons = "; ".join(d.message for d in self.defects)
            return f"Refused: {reasons}"

        moves = []
        if self.shortfall_delta:
            direction = "fills" if self.shortfall_delta < 0 else "costs"
            moves.append(f"{direction} {abs(self.shortfall_delta)} position(s)")
        if self.disruption_delta:
            direction = "less" if self.disruption_delta < 0 else "more"
            moves.append(f"{abs(self.disruption_delta)} disruption points {direction}")

        effect = ", ".join(moves) if moves else "changes nothing"
        return f"{'; '.join(self.described)}: {effect}."


def apply(instance: Instance, change: Change) -> Instance:
    """The instance as it would be under one hypothetical."""
    if change.kind == ADD_EMPLOYEE:
        hired = Employee(
            name=f"hypothetical-{len(instance.employees)}",
            contract=change.contract,
            skills=frozenset(change.skills),
            max_hours_this_week=change.weekly_hours,
            max_daily_hours=change.daily_hours,
            # Eligibility is resolved upstream and enters as data (`D-032`). A hypothetical
            # hire is eligible on every day, which is the optimistic reading and is stated
            # rather than hidden: the answer is an upper bound on what hiring would buy.
            flexi_eligible=frozenset(range(instance.days)),
            dimona_ok=frozenset(range(instance.days)),
        )
        return dataclasses.replace(instance, employees=instance.employees + (hired,))

    if change.kind == SET_WEEKLY_HOURS:
        return dataclasses.replace(
            instance,
            employees=tuple(
                dataclasses.replace(person, max_hours_this_week=change.weekly_hours)
                if change.employee is None or index == change.employee
                else person
                for index, person in enumerate(instance.employees)
            ),
        )

    if change.kind == SET_DAILY_HOURS:
        return dataclasses.replace(
            instance,
            employees=tuple(
                dataclasses.replace(person, max_daily_hours=change.daily_hours)
                if change.employee is None or index == change.employee
                else person
                for index, person in enumerate(instance.employees)
            ),
        )

    if change.kind == IGNORE_SKILL:
        # This does not teach the employee anything, and nothing here reaches the real
        # `instance` passed in — `dataclasses.replace` returns a new, throwaway copy, solved
        # only inside this one hypothetical. It answers *would the shortfall close if this
        # requirement did not apply to this one person*, not *give them the skill*.
        if change.employee is None:
            raise ValueError("ignore_skill requires an employee")
        return dataclasses.replace(
            instance,
            employees=tuple(
                dataclasses.replace(person, skills=person.skills | frozenset(change.skills))
                if index == change.employee
                else person
                for index, person in enumerate(instance.employees)
            ),
        )

    if change.kind == SET_REQUIRED:
        return dataclasses.replace(
            instance,
            open_shifts=tuple(
                dataclasses.replace(o, required=change.required)
                if (o.day, o.shift) == (change.day, change.shift)
                else o
                for o in instance.open_shifts
            ),
        )

    if change.kind == RELAX_RULE:
        params: RuleParams = instance.params
        updates = {}
        if change.min_rest_hours is not None:
            updates["min_rest_hours"] = change.min_rest_hours
        if change.max_consecutive_days is not None:
            updates["max_consecutive_days"] = change.max_consecutive_days
        if change.derogation_basis:
            updates["derogation_basis"] = dict(params.derogation_basis) | dict(
                change.derogation_basis
            )
        return dataclasses.replace(instance, params=dataclasses.replace(params, **updates))

    raise ValueError(f"unknown change kind {change.kind!r}; expected one of {KINDS}")


def compare(
    instance: Instance,
    changes: tuple[Change, ...],
    *,
    seed: int = 7,
    time_limit: float = 30.0,
    baseline: Outcome | None = None,
) -> Comparison:
    """Solve the instance as it is and as it would be, and report the difference.

    Both solves use the same seed and the same incumbent, so a difference in disruption is
    the change's doing rather than the search's.

    `baseline` lets a caller comparing several changes against **the same instance** supply
    the unchanged solve it already has, instead of paying for an identical one per change.
    Passing a baseline measured from a different instance or a different seed would break
    the pairing the whole comparison rests on, so it is the caller's obligation that it came
    from this instance at this seed — `recommend` below is the caller this exists for.
    """
    if baseline is None:
        baseline = _measure(instance, seed=seed, time_limit=time_limit)

    variant_instance = instance
    for change in changes:
        variant_instance = apply(variant_instance, change)

    defects = validate_instance(variant_instance)
    if defects:
        return Comparison(
            described=tuple(c.describe() for c in changes),
            baseline=baseline,
            variant=None,
            defects=tuple(defects),
        )

    return Comparison(
        described=tuple(c.describe() for c in changes),
        baseline=baseline,
        variant=_measure(variant_instance, seed=seed, time_limit=time_limit),
    )


def _measure(instance: Instance, *, seed: int, time_limit: float) -> Outcome:
    solution = solve(instance, seed=seed, time_limit=time_limit)
    roster = getattr(solution, "roster", frozenset())

    return Outcome(
        shortfall=sum(
            1
            for v in check(roster, instance)
            if v.rule == "R-COVER" and v.soft and not instance.is_past(v.day, v.shift)
            for _ in range(_missing(roster, instance, v.day, v.shift))
        ),
        disruption=disruption_of(roster, instance),
        changes_from_incumbent=len(roster ^ (instance.incumbent or frozenset())),
        shortfalls=explain(roster, instance),
        roster=roster,
    )


def _missing(roster, instance: Instance, day: int, shift: int) -> int:
    required = next(
        o.required for o in instance.open_shifts if (o.day, o.shift) == (day, shift)
    )
    return max(0, required - sum(1 for _, d, s in roster if (d, s) == (day, shift)))


# The provenance of each rule `recommend` can build a `Change` for, from the registry table
# in `guide/rules.md`. It is carried on the recommendation because disruption alone cannot order
# these asks: ignoring a skill requirement is an operational judgement a planner owns, while
# raising someone's weekly budget moves a parameter a statute sets the ceiling for, and a
# cheaper number does not make the second the preferable ask. Nothing unlawful reaches this
# point — `validate_instance` refuses a cap above the absolute ceiling and `compare` returns
# the refusal, so the candidate is already gone — but lawful is not the same as equivalent.
_PROVENANCE = {
    "R-SKILL": "operational",
    "R-MAX-WEEKLY": "statutory",
    "R-MAX-DAILY": "statutory",
}


@dataclass(frozen=True, slots=True)
class Recommendation:
    """One candidate for closing a shortfall, and what it would cost.

    Nothing here has happened — `recommend` only ran `compare` against a throwaway instance
    for each candidate. Acting on a recommendation is a separate, later step: publishing it
    is a caller's decision, not this module's.

    `rule` and `provenance` are here so a caller can see *what kind of ask* a number prices.
    A list sorted on `disruption_delta` alone would put a statutory relaxation above an
    operational one for the sake of a few points, which is the trade-off the sort is not
    entitled to make on a planner's behalf.
    """

    employee: int
    action: str
    disruption_delta: int
    rule: str
    provenance: str


# A candidate costs a solve, so an uncapped sweep is a solve per blocked person and its
# worst case is the time limit multiplied by a tenant's headcount. The list is read as
# *the cheapest few* anyway — nobody acts on the eleventh-best override — so the default
# bounds the work rather than leaving it to the size of the payload.
MAX_CANDIDATES = 5


def recommend(
    instance: Instance,
    shortfall: Shortfall,
    *,
    seed: int = 7,
    time_limit: float = 30.0,
    max_candidates: int = MAX_CANDIDATES,
) -> tuple[Recommendation, ...]:
    """Rank the people closest to filling one shortfall by what ignoring their one blocker
    would actually cost, confirmed by solving rather than assumed from the rule count.

    Ranked **within a provenance, not across one**: operational asks first, then statutory
    ones, each group cheapest-first. See `Recommendation`.

    Restricted to people blocked by exactly one rule: `by_employee()` already says these are
    the cheapest to ask, in the sense of needing one override instead of several, and a
    person with two or more blockers cannot be tested by relaxing only one of them. Only
    rules with a `Change` kind can be tested at all — R-SKILL, R-MAX-DAILY and R-MAX-WEEKLY
    today; R-AVAIL and the rest are not offered until `whatif.py` can express them.

    Every candidate is a fresh, disposable instance solved independently — the incumbent
    roster and every employee's real record are exactly as they were before this ran.

    At most `max_candidates` people are tested, in employee order, and the unchanged
    instance is solved once for all of them rather than once per candidate.
    """
    shift_type = instance.shift_types[shortfall.shift]
    open_shift = next(
        o for o in instance.open_shifts if (o.day, o.shift) == (shortfall.day, shortfall.shift)
    )

    # The one solve every candidate is measured against. It does not depend on which
    # override is being tested, so paying for it per candidate bought nothing but time.
    baseline = _measure(instance, seed=seed, time_limit=time_limit)

    results = []
    tested = 0
    for blocked in shortfall.blocked:
        if len(blocked.rules) != 1:
            continue
        if tested >= max_candidates:
            break
        rule = blocked.rules[0]
        employee = instance.employees[blocked.employee]

        if rule == "R-SKILL":
            missing = open_shift.required_skills - employee.skills
            change = Change(kind=IGNORE_SKILL, employee=blocked.employee, skills=tuple(missing))
            action = f"ignore {', '.join(sorted(missing))} skill"
        elif rule == "R-MAX-WEEKLY":
            raised = (employee.max_hours_this_week or 0.0) + shift_type.span_hours
            change = Change(kind=SET_WEEKLY_HOURS, employee=blocked.employee, weekly_hours=raised)
            action = f"raise weekly-hours cap by {shift_type.span_hours:g}h"
        elif rule == "R-MAX-DAILY":
            raised = (employee.max_daily_hours or 0.0) + shift_type.span_hours
            change = Change(kind=SET_DAILY_HOURS, employee=blocked.employee, daily_hours=raised)
            action = f"raise daily-hours cap by {shift_type.span_hours:g}h"
        else:
            continue

        tested += 1
        comparison = compare(
            instance, (change,), seed=seed, time_limit=time_limit, baseline=baseline
        )
        if comparison.refused or comparison.shortfall_delta >= 0:
            continue

        results.append(
            Recommendation(
                employee=blocked.employee,
                action=action,
                disruption_delta=comparison.disruption_delta,
                rule=rule,
                provenance=_PROVENANCE[rule],
            )
        )

    # Operational asks first, then statutory ones, and cheapest-first *within* a provenance
    # rather than across the whole list. The two groups are not on one scale, so the sort
    # keeps them apart instead of interleaving them by a number that cannot decide between
    # them; a caller that wants a flat ranking can still sort the tuple itself.
    return tuple(
        sorted(
            results,
            key=lambda r: (r.provenance != "operational", r.disruption_delta, r.employee),
        )
    )
