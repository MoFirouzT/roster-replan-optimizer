"""Why a shift is short: the explainer's ordinary job.

The explainer was specified as an infeasibility explainer, and `rules.md` re-scoped it before a
line was written (`D-047`): once the coverage floor is soft, the empty roster satisfies every
hard rule, so **a cold solve is essentially never infeasible**. A shift nobody can staff
comes back as a priced shortfall, not a refusal. Measured on the committed set, 16 of 72
cases return an optimal roster that still leaves a shift short — 24 unstaffed positions —
and **none is infeasible**.

So the question a planner actually asks is not *why is there no roster* but *why is nobody
on Saturday night, and what would it take*. That is what this module answers.

## It is built on the checker, deliberately

`explain` imports the **checker** and nothing else — no model, no solver, no `exclusions()`.
An import-linter contract holds it there, the same one `repair.py` carries.

That is not tidiness. An explanation derived from the model's own presolve table is the
solver's account of itself: if the model wrongly believes somebody is ineligible, it also
wrongly explains why they were not used, and the two errors agree. Asking the independent
reading instead means a wrong exclusion produces an explanation that **contradicts** the
roster, which is a finding rather than a consistent lie.

The cost is that this recomputes what presolve already knew. At these sizes that is
microseconds against a solve, and it buys the one property the explanation needs: it is
checkable against something other than the thing being explained.

## Every unassigned person gets a reason, or the roster is wrong

For a slot that is short, every employee not on it must be blocked by something — because
`shortfall_weight` dominates every other term (`D-057`), so if anyone *could* legally be
added, an optimal solver would have added them.

An employee with no blocking rule is therefore not an explanation, it is a **defect
report**: either the roster is suboptimal or the two readings disagree about eligibility.
`Shortfall.unexplained` carries them, and it is expected to be empty on every optimal
roster. `tests/test_explain.py` asserts exactly that across the committed set, which makes
this module a fifth check on the solver rather than only a presentation layer.
"""

from __future__ import annotations

from collections import Counter
from dataclasses import dataclass

from .checker import check
from .domain import Instance, Roster


@dataclass(frozen=True, slots=True)
class Blocked:
    """One person who could not take the slot, and the rules that stopped them."""

    employee: int
    rules: tuple[str, ...]


@dataclass(frozen=True, slots=True)
class Shortfall:
    """One under-staffed slot, with a reason for every person not on it."""

    day: int
    shift: int
    required: int
    assigned: int
    blocked: tuple[Blocked, ...]

    # Employees the checker says could have been added legally. Always empty on an optimal
    # roster; non-empty means the roster is suboptimal or the two readings disagree.
    unexplained: tuple[int, ...]

    @property
    def short(self) -> int:
        return self.required - self.assigned

    def by_rule(self) -> dict[str, int]:
        """How many people each rule accounts for.

        A person blocked by two rules counts once for each: the question is *what would have
        to change*, and relaxing one of two blockers does not free them. Reporting a single
        "primary" reason would imply it does.
        """
        counts: Counter[str] = Counter()
        for entry in self.blocked:
            counts.update(set(entry.rules))
        return dict(counts.most_common())

    def by_employee(self) -> dict[int, int]:
        """How many rules block each excluded person, fewest first.

        The rule count, not the identity of the rules: someone blocked by one rule is the
        cheapest to relax, in the sense that overriding them needs one justification instead
        of several. It is not a promise that overriding them clears the shortfall — the
        solver would still have to re-optimize around whatever else the roster owes.
        """
        counts = {entry.employee: len(entry.rules) for entry in self.blocked}
        return dict(sorted(counts.items(), key=lambda item: item[1]))

    def summary(self) -> str:
        """One line, in the shape `rules.md` asks for.

        Deliberately plain: this is the string an LLM is handed to phrase, and `D-013` says
        the model never identifies the conflict, only renders one already proved. Everything
        here is derived, so there is nothing for it to invent.
        """
        parts = [f"{count} {rule}" for rule, count in self.by_rule().items()]
        reasons = ", ".join(parts) if parts else "no eligible staff at all"
        return (
            f"day {self.day} shift {self.shift}: {self.assigned} of {self.required} staffed, "
            f"{self.short} short — {reasons}"
        )


def explain(roster: Roster, instance: Instance) -> tuple[Shortfall, ...]:
    """Every under-staffed slot, with the reason each unassigned person could not fill it.

    Historical slots are skipped: a shift that has already started cannot be repaired, so
    naming who could not have worked it is noise. That is the same exclusion the objective
    makes (`replan.md`), applied for the same reason.
    """
    assigned_to: dict[tuple[int, int], set[int]] = {}
    for employee, day, shift in roster:
        assigned_to.setdefault((day, shift), set()).add(employee)

    by_employee: dict[int, set] = {}
    for key in roster:
        by_employee.setdefault(key[0], set()).add(key)

    findings = []
    for open_shift in sorted(instance.open_shifts, key=lambda o: (o.day, o.shift)):
        day, shift = open_shift.day, open_shift.shift
        if instance.is_past(day, shift):
            continue

        here = assigned_to.get((day, shift), set())
        if len(here) >= open_shift.required:
            continue

        blocked, unexplained = [], []
        for employee in range(len(instance.employees)):
            if employee in here:
                continue
            rules = _blocking_rules(instance, by_employee.get(employee, set()), employee, day, shift)
            if rules:
                blocked.append(Blocked(employee=employee, rules=rules))
            else:
                unexplained.append(employee)

        findings.append(
            Shortfall(
                day=day,
                shift=shift,
                required=open_shift.required,
                assigned=len(here),
                blocked=tuple(blocked),
                unexplained=tuple(unexplained),
            )
        )

    return tuple(findings)


def _blocking_rules(
    instance: Instance, own: set, employee: int, day: int, shift: int
) -> tuple[str, ...]:
    """Which hard rules adding this person to this slot would break.

    Asked of the employee's own row only, and against what they are *already* assigned. Two
    reasons for the narrow question, both borrowed from `repair.py`: adding one person to
    one shift can only break a rule about that person, and a rule already broken before the
    addition is not a reason to refuse them.
    """
    before = _hard_rules(instance, frozenset(own), employee)
    after = _hard_rules(instance, frozenset(own | {(employee, day, shift)}), employee)
    return tuple(sorted(after - before))


def _hard_rules(instance: Instance, roster: Roster, employee: int) -> set[str]:
    return {
        violation.rule
        for violation in check(roster, instance)
        if not violation.soft and violation.employee == employee
    }
