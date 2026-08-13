"""The human default: drop what broke, call someone for each hole, touch nothing else.

Its own module rather than a function inside `methods.py`, because the claim that makes it
a baseline worth having is that it is **not the solver in disguise** -- and that claim is
mechanised here the same way the checker's independence is. An import-linter contract
forbids this module from reaching `model`, `disruption` or `ortools`, so "solver-free" is
checked rather than asserted in a docstring. `methods.py` cannot carry that contract: it
runs the three solver methods too.

The legality oracle is the **checker**, which is the reading that owes no allegiance to
the model. So a greedy repair that the model would have rejected cannot be scored as a
legal one, and the baseline cannot inherit a bug from the thing it is measuring.

## The tie-break is stated, not incidental (`D-078`)

"Nearest-eligible" names an ordering that does not exist until somebody writes it down.
Here it is: candidates are ordered by hours already rostered this week, then by index --
call the person with the most room, and break exact ties by a stable key. Two things make
this the right choice rather than an arbitrary one. It is what a planner scanning a
roster actually does, and it is deterministic, so the baseline is reproducible and a
change to its number is a change to the method.
"""

from __future__ import annotations

from collections import defaultdict

from roster_replan.checker import check
from roster_replan.domain import Instance, Roster


def repair(instance: Instance, incumbent: Roster) -> Roster:
    """Drop what the event broke, then call the nearest eligible person for each hole.

    Never fills past `required`, so it cannot overstaff, and never touches a shift that
    has already started, so it cannot break `R-PIN-PAST`. What it does *not* do is the
    whole point of it being a baseline: it will not move an uninvolved person to free
    someone up, because no planner working from a printed roster would find that chain.
    """
    roster = set(_drop_broken(instance, incumbent))
    by_employee: dict[int, set] = defaultdict(set)
    for key in roster:
        by_employee[key[0]].add(key)

    people = range(len(instance.employees))
    for open_shift in sorted(
        instance.open_shifts, key=lambda o: instance.window(o.day, o.shift).start
    ):
        day, shift = open_shift.day, open_shift.shift
        if instance.is_past(day, shift):
            # A hole in a shift that has already started is not repairable, and filling
            # it would be a `R-PIN-PAST` violation dressed up as a repair.
            #
            # **This is intent and a saving, not the defence.** `_legal` refuses a past
            # slot on its own, because adding one is a violation the checker names --
            # deleting this line changes no roster, which the mutation harness
            # established rather than assumed. The defence of the past is `_drop_broken`
            # leaving historical violations alone, and that is where the mutant is.
            continue

        while sum(1 for e in people if (e, day, shift) in roster) < open_shift.required:
            candidate = _nearest(instance, roster, by_employee, day, shift)
            if candidate is None:
                # Nobody legal is left. The hole stays, which is the baseline's
                # characteristic failure and the reason results are read with the
                # shortfall column beside the disruption one.
                break
            roster.add((candidate, day, shift))
            by_employee[candidate].add((candidate, day, shift))

    return frozenset(roster)


def _drop_broken(instance: Instance, incumbent: Roster) -> Roster:
    """Every incumbent assignment a hard rule now names, outside the pinned past.

    The event is expressed as an absence or a withdrawal, so what it broke is exactly what
    the checker reports against the incumbent. This method therefore never has to know
    which event happened, which is what makes it one baseline rather than four.

    **The past is excluded by asking the instance, not by reading `Violation.historical`.**
    That flag was the first version of this line and it was wrong: only `R-COVER`,
    `R-SKILL-MIX` and `R-PIN-PAST` set it, so a person taken ill during a shift they had
    already started produced an unflagged `R-AVAIL` violation, greedy dropped a pinned
    assignment, and the returned roster broke `R-PIN-PAST`. Whether a slot has started is a
    fact about the instance, and this module should read it there rather than depend on
    every rule in another module remembering to mark it.
    """
    broken = {
        (v.employee, v.day, v.shift)
        for v in check(incumbent, instance)
        if not v.soft
        and None not in (v.employee, v.day, v.shift)
        and not instance.is_past(v.day, v.shift)
    }
    return frozenset(key for key in incumbent if key not in broken)


def _nearest(
    instance: Instance, roster: set, by_employee: dict[int, set], day: int, shift: int
) -> int | None:
    """The first legal candidate under the stated order: least rostered, then by index."""
    for employee in sorted(
        range(len(instance.employees)),
        key=lambda e: (_rostered_hours(instance, by_employee[e]), e),
    ):
        key = (employee, day, shift)
        if key in roster:
            continue
        if _legal(instance, by_employee[employee], key):
            return employee
    return None


def _rostered_hours(instance: Instance, assignments: set) -> float:
    return sum(instance.shift_types[shift].work_hours for _, _, shift in assignments)


def _legal(instance: Instance, assignments: set, key) -> bool:
    """Does adding `key` break a hard rule about this employee that was not already broken?

    Asked about the candidate's *own* assignments only. Adding one person to one shift can
    break a rule about that person or overstaff the slot, and nothing else -- and the slot
    is never filled past `required`, so the narrow question is the whole question. Asking
    it over the full roster would give the same answer at tens of times the cost, and the
    time this method takes is one of the numbers being reported.

    Already-broken is the right comparison rather than "breaks nothing": an incumbent can
    arrive carrying a violation no replan can repair, and a candidate should not be
    refused for a rule that was already failing before anyone called them.
    """
    employee = key[0]
    before = _hard_keys(instance, frozenset(assignments), employee)
    after = _hard_keys(instance, frozenset(assignments | {key}), employee)
    return not (after - before)


def _hard_keys(instance: Instance, roster: Roster, employee: int) -> set:
    return {
        v.key() for v in check(roster, instance) if not v.soft and v.employee == employee
    }
