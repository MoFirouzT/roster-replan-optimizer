"""Findings rendered in planner language, deterministically and with nothing added.

`rules.md` specifies the target text rule by rule — *"Sat 15:00–23:00 (Evening) is 1 short of
its 3 required staff."* — and `explain.py` computes the finding behind it. This module is the
step between, and it is **pure**: a function of the finding and the instance, with no model
call, no solver, and no source of fact other than what it was handed.

That is what makes an LLM layer optional rather than load-bearing later. `D-013` requires the
model to phrase a conflict it never identified, and a phrasing step that already exists and
is already correct leaves the LLM nothing to do but vary the wording — which a validator can
check, because every name, number, slot and rule in a legitimate rendering appears in the
finding it came from.

## Three things this refuses to invent

**Weekdays.** `domain.py` has no calendar on purpose: *"the rules are arithmetic and stay
testable without a calendar"*, and timestamps belong at the API boundary. So `day 5` cannot
become `Sat` from anything this module knows. The caller may supply
`weekday_of_day_zero`, exactly as it supplies `now` and `published_through`; without it the
text says `day 5`, which is honest rather than helpful. Guessing a Monday start would be a
fact this layer made up.

**Shift names.** `ShiftType.label` is the tenant's own label and is printed verbatim.
Expanding `E` to `Evening` is the same class of invention: it happens to be right for the
generated set and would be wrong for a tenant whose `E` means something else.

**Employee identity.** Names come from `Employee.name` and nothing else. Under `D-016` a
captured corpus carries surrogate keys, so this will correctly print `E07` rather than a
person's name — the renderer is exactly as readable as the caller's own identifiers, which
is the right dependency.

## The rule sentences live here, and a test holds them to the registry

`RULE_TEXT` is code, not prose duplicated from a spec — but its *keys* are a claim about
`rules.md`, so `tests/test_prose.py` asserts the two agree in both directions: every rule the
registry marks encoded has a sentence, and no sentence names a rule the registry does not
have.
"""

from __future__ import annotations

import re

from .domain import Instance
from .explain import Shortfall

WEEKDAYS = ("Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun")

# One clause per rule, phrased as *what stopped these people*, plural and count-led, because
# the shortfall case is an aggregate: `rules.md` notes that R-SKILL surfaces through R-COVER
# as scarcity rather than as a fact about one person.
RULE_TEXT: dict[str, str] = {
    "R-AVAIL": "are absent or unavailable then",
    "R-SKILL": "do not hold a skill the shift requires",
    "R-SKILL-MIX": "would not satisfy the shift's required skill mix",
    "R-REST-GAP": "would not get the minimum rest between shifts",
    "R-WEEKLY-REST": "would lose their minimum weekly rest",
    "R-MAX-WEEKLY": "would exceed their hours for the week",
    "R-MAX-DAILY": "would exceed their hours for the day",
    "R-CONSEC-DAYS": "would work too many consecutive days",
    "R-FLEXI-ELIG": "are not eligible for a flexi-job that day",
    "R-DIMONA-FLX": "have no Dimona filing for that day",
    "R-PIN-PAST": "are fixed by a shift that has already started",
    "R-COVER": "would overstaff the shift",
}


def slot(instance: Instance, day: int, shift: int, *, weekday_of_day_zero: int | None = None) -> str:
    """`Sat 15:00-23:00 (E)`, or `day 5 15:00-23:00 (E)` with no calendar supplied."""
    window = instance.window(day, shift)
    label = instance.shift_types[shift].label

    if weekday_of_day_zero is None:
        when = f"day {day}"
    else:
        when = WEEKDAYS[(weekday_of_day_zero + day) % 7]

    return f"{when} {_clock(window.start)}-{_clock(window.end)} ({label})"


def _clock(hours: float) -> str:
    """Hours from the horizon start, as a wall clock. The day rolls over past 24."""
    minutes = int(round(hours * 60)) % (24 * 60)
    return f"{minutes // 60:02d}:{minutes % 60:02d}"


def render(
    finding: Shortfall,
    instance: Instance,
    *,
    weekday_of_day_zero: int | None = None,
    name_limit: int = 3,
) -> str:
    """One shortfall, as a planner would read it.

    Names are given when few enough people are involved to be worth naming, and counted
    otherwise. The threshold is a presentation choice rather than a claim: *Ana and Bram are
    absent* is actionable, and a list of nine names is a wall.
    """
    where = slot(instance, finding.day, finding.shift, weekday_of_day_zero=weekday_of_day_zero)
    headline = (
        f"{where} is {finding.short} short of its {finding.required} required staff."
    )

    by_rule: dict[str, list[int]] = {}
    for entry in finding.blocked:
        for rule in entry.rules:
            by_rule.setdefault(rule, []).append(entry.employee)

    lines = [headline]
    for rule, employees in sorted(by_rule.items(), key=lambda kv: (-len(kv[1]), kv[0])):
        clause = RULE_TEXT.get(rule, f"are blocked by {rule}")
        if len(employees) <= name_limit:
            who = _names(instance, employees)
        else:
            who = f"{len(employees)} of the {len(instance.employees)} staff"
        lines.append(f"  {who} {clause} ({rule}).")

    if finding.unexplained:
        # Never expected on an optimal roster -- see `explain.py`. Rendered rather than
        # hidden, because a shortfall nobody is blocked from filling is the single most
        # useful thing this text could ever say.
        lines.append(
            f"  {_names(instance, list(finding.unexplained))} could have been assigned and "
            f"were not, which means the roster is not optimal."
        )

    return "\n".join(lines)


def render_all(
    findings: tuple[Shortfall, ...],
    instance: Instance,
    *,
    weekday_of_day_zero: int | None = None,
) -> str:
    if not findings:
        return "Every shift is fully staffed."
    return "\n\n".join(
        render(f, instance, weekday_of_day_zero=weekday_of_day_zero) for f in findings
    )


def _names(instance: Instance, employees: list[int]) -> str:
    # Sorted by name, not by index. The generator shuffles employees after naming them, so
    # index order and name order differ and sorting by index reads as unsorted.
    labels = sorted(instance.employees[e].name for e in employees)
    if len(labels) == 1:
        return labels[0]
    return ", ".join(labels[:-1]) + f" and {labels[-1]}"


# --- The boundary an LLM layer would have to pass -----------------------------------


def supported_terms(finding: Shortfall, instance: Instance) -> set[str]:
    """Every name, rule and number a faithful rendering of this finding may contain.

    This is `D-013` made checkable. The rule is that the model phrases a conflict it did not
    identify, and the way to enforce it is not to trust the phrasing but to bound the
    vocabulary: a rendering that mentions an employee, a rule or a count absent from the
    finding has added a fact, whoever wrote it.
    """
    terms = {rule for entry in finding.blocked for rule in entry.rules}
    terms |= {
        instance.employees[e].name
        for e in [entry.employee for entry in finding.blocked] + list(finding.unexplained)
    }
    terms |= {
        str(finding.short),
        str(finding.required),
        str(finding.assigned),
        str(finding.day),
        str(len(instance.employees)),
    }
    terms |= {str(len(employees)) for employees in _grouped(finding).values()}
    terms |= {instance.shift_types[finding.shift].label}
    return terms


def unsupported_terms(text: str, finding: Shortfall, instance: Instance) -> set[str]:
    """Names, rule IDs and numbers in `text` that the finding does not support.

    Deliberately crude: it checks the vocabulary rather than the meaning, because meaning is
    what a deterministic layer cannot judge and vocabulary is what it can. Empty for anything
    `render` produces, which is the point -- the validator and the renderer are held to the
    same bound, so a future LLM rendering is judged against a standard already met.
    """
    allowed = supported_terms(finding, instance)
    known_names = {person.name for person in instance.employees}
    found: set[str] = set()

    for token in re.findall(r"[A-Za-z][A-Za-z0-9-]*|\d+", text):
        if token in allowed:
            continue
        # Identifier-shaped, not merely known. The first version flagged a token only if it
        # was already a *real* employee name, which let a wholly invented `E99` through --
        # the worse failure, since a fabricated person is less checkable than a real one
        # named wrongly. Anything carrying a digit, or shaped like a rule ID, is treated as
        # a claim about the instance; ordinary English words are not.
        identifier = (
            token.startswith("R-")
            or any(character.isdigit() for character in token)
            or token in known_names
        )
        if identifier:
            found.add(token)

    # Clock times and the slot line are rendered from the instance, so their digits are
    # supported by construction rather than by the finding.
    return found - _clock_digits(finding, instance)


def _grouped(finding: Shortfall) -> dict[str, list[int]]:
    grouped: dict[str, list[int]] = {}
    for entry in finding.blocked:
        for rule in entry.rules:
            grouped.setdefault(rule, []).append(entry.employee)
    return grouped


def _clock_digits(finding: Shortfall, instance: Instance) -> set[str]:
    window = instance.window(finding.day, finding.shift)
    # Separated, because concatenating `15:00` and `23:00` tokenises as `15`, `0023`, `00`
    # rather than as the four fields, so the real `23` looked unsupported in the renderer's
    # own output.
    return set(re.findall(r"\d+", f"{_clock(window.start)} {_clock(window.end)}"))
