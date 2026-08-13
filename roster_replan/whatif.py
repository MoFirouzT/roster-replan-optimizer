"""`what if I hire one more flexi-jobber?` — a sweep over machinery that already exists.

`service.md` names this as the question owners actually ask, and it is the one tool in T4's
surface that is not a wrapper: the others expose a solve, a validation or an explanation that
already has a caller. This one composes them into an answer to a hypothetical.

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
SET_REQUIRED = "set_required"
RELAX_RULE = "relax_rule"

KINDS = (ADD_EMPLOYEE, SET_WEEKLY_HOURS, SET_REQUIRED, RELAX_RULE)


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
) -> Comparison:
    """Solve the instance as it is and as it would be, and report the difference.

    Both solves use the same seed and the same incumbent, so a difference in disruption is
    the change's doing rather than the search's.
    """
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
