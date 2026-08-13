"""A cache for built models, and the fingerprint that makes reuse safe.

`service.md` asks to "cache the compiled model per tenant; at these instance sizes, building
the model can cost more than solving it". The premise is measured and correct -- building is
about 5 ms against about 3 ms of search. The remedy needs care, because **a replan changes
exactly the inputs the model is built from**: the event that triggers it is usually an
absence, and an absence changes which `(employee, shift)` pairs survive presolve, which
changes the variables.

So the cache is keyed on a fingerprint of everything `build` reads, and on nothing else.

## What the fingerprint covers, and what it deliberately omits

**Covered** -- the horizon, shift types, rule parameters, every employee's availability,
skills, contract, budgets and eligibility, every open shift, and `now` (which decides what
`R-PIN-PAST` pins). Any change to these is a different model.

**Omitted** -- `disruption` and `incumbent`. Neither is a constraint. The objective is applied
per solve by `model.solve`, and the incumbent enters the objective rather than the feasible
set... **except for one thing**, which is why this file is careful rather than obvious: `build`
creates a variable for any pair the *incumbent* assigned even when presolve excluded it
(`D-058`), so the incumbent does change the variable set. It is therefore in the fingerprint
after all, and only `disruption` is genuinely omitted.

That single exception is the reason this is a fingerprint of `build`'s inputs rather than a
tidy "constraints versus objective" split. The tidy version would be wrong, and wrong in the
direction that returns a model missing the variables a deviation is counted on.

## Reuse is not free, and the reset is the risky part

A `CpModel` is mutated by solving: `minimize` sets an objective, `add_hint` adds hints,
`add_assumptions` sets assumptions. Handing a used model to a second solve without clearing
all three silently carries the previous request's objective into this one. `reset` below does
it, and `tests/test_cache.py` asserts a reused model reaches the same answer as a fresh one
under a *different* objective -- which is the case a stale objective would fail.
"""

from __future__ import annotations

import hashlib
from collections import OrderedDict

from .domain import Instance
from .model import Built, build


def fingerprint(instance: Instance) -> str:
    """A stable digest of everything `build` reads.

    Cheap by construction: it walks the payload once and hashes a flat string. It has to be
    much cheaper than the build it might save, or a miss costs more than it protects.
    """
    parts: list[str] = [
        str(instance.days),
        repr(instance.params),
        "|".join(
            f"{s.label},{s.start_hour},{s.span_hours},{s.break_hours}"
            for s in instance.shift_types
        ),
        "" if instance.now is None else str(instance.now),
    ]

    for person in instance.employees:
        parts.append(
            f"{person.name};{person.contract};{sorted(person.skills)};"
            f"{[(i.start, i.end) for i in person.absences]};"
            f"{[(i.start, i.end) for i in person.unavailability]};"
            f"{person.max_hours_this_week};{person.max_daily_hours};"
            f"{person.consecutive_days_worked_before_horizon};"
            f"{person.last_shift_end_before_horizon};"
            f"{None if person.flexi_eligible is None else sorted(person.flexi_eligible)};"
            f"{None if person.dimona_ok is None else sorted(person.dimona_ok)}"
        )

    for shift in instance.open_shifts:
        parts.append(
            f"{shift.day},{shift.shift},{shift.required},"
            f"{sorted(shift.required_skills)},{shift.skill_mix}"
        )

    # `D-058`: the incumbent adds variables for pairs presolve excluded, so it changes the
    # model and belongs in the key even though it is otherwise an objective input.
    if instance.incumbent is not None:
        parts.append(";".join(map(str, sorted(instance.incumbent))))

    return hashlib.blake2b("\n".join(parts).encode(), digest_size=16).hexdigest()


def reset(built: Built) -> Built:
    """Clear what a previous solve left on the model and what the next one will not replace.

    Hints and assumptions accumulate: `add_hint` and `add_assumptions` append, so without
    this a cached model would carry every previous request's hints into the next solve.
    That does not change the optimum, but it changes the *search*, so a cached solve would
    stop being reproducible from its seed -- which `PLAN.md` requires end to end.

    **The objective is deliberately not cleared**, and that is a verified fact about CP-SAT
    rather than an oversight: `minimize` and `maximize` replace the objective rather than
    adding to it, so `model.solve` overwrites it on every call. A `clear_objective()` here
    was the obvious defensive move and the mutation harness proved it dead -- deleting the
    call broke no test, because no reachable path leaves the objective unset. Code that
    cannot be shown to fail is not known to work, so it is gone.
    """
    model = built.model
    model.clear_hints()
    model.clear_assumptions()
    return built


class ModelCache:
    """Bounded, per-fingerprint. Keyed by tenant so one tenant cannot evict another's.

    An LRU rather than an unbounded dict: this lives in a long-running service, and a cache
    that grows with distinct payloads is a memory leak with a friendly name.
    """

    def __init__(self, *, capacity: int = 64) -> None:
        self.capacity = capacity
        self._entries: OrderedDict[tuple[str, str], Built] = OrderedDict()
        self.hits = 0
        self.misses = 0

    def __len__(self) -> int:
        return len(self._entries)

    @property
    def hit_rate(self) -> float:
        total = self.hits + self.misses
        return 0.0 if total == 0 else self.hits / total

    def get(self, instance: Instance, *, tenant: str = "-") -> Built:
        key = (tenant, fingerprint(instance))
        cached = self._entries.get(key)

        if cached is not None:
            self._entries.move_to_end(key)
            self.hits += 1
            return reset(cached)

        self.misses += 1
        built = build(instance)
        self._entries[key] = built
        if len(self._entries) > self.capacity:
            self._entries.popitem(last=False)
        return built

    def clear(self) -> None:
        self._entries.clear()
        self.hits = self.misses = 0
