"""Rendering a finding in planner language, and the bound a future LLM must stay inside.

Two things are worth testing here and one thing is not. The wording is not: it is a
presentation choice and asserting it letter by letter makes every improvement a test edit.

What is worth testing:

**The rule sentences agree with the registry**, in both directions. `RULE_TEXT` is code, but
its keys are a claim about `rules.md` — that every rule the registry marks encoded can be
explained to a planner. A rule with no sentence renders as a bare ID, which is the
engineer-language failure this module exists to remove.

**Nothing is invented.** `unsupported_terms` bounds the vocabulary a faithful rendering may
use, and the renderer is held to it. That matters more than it looks: `D-013` says the LLM
phrases a conflict it never identified, and this is the check that makes the rule
enforceable rather than aspirational. The deterministic renderer passing its own validator is
what proves the bound is satisfiable — a standard nothing can meet is not a standard.
"""

from __future__ import annotations

import re

import pytest

from benchmarks import suite
from roster_replan.explain import Blocked, Shortfall, explain
from roster_replan.model import solve
from roster_replan.prose import (
    RULE_TEXT,
    render,
    render_all,
    slot,
    supported_terms,
    unsupported_terms,
)
from tests.test_specs import UNENCODED, _text, SPECS

CASES = ["scarce-skill/0", "tight/0", "headline/3", "thin-availability/0"]


@pytest.fixture(scope="module")
def findings():
    out = {}
    for case in CASES:
        scenario = suite.build(case)
        roster = solve(scenario.instance, time_limit=30.0).roster
        out[case] = (scenario.instance, explain(roster, scenario.instance))
    return out


# --- Against the registry -----------------------------------------------------------


def test_every_encoded_rule_can_be_explained_to_a_planner():
    registry = {
        match.group(1)
        for line in _text(SPECS / "rules.md").splitlines()
        if (match := re.match(r"\|\s*`(R-[A-Z-]+)`\s*\|", line))
    }
    missing = (registry - UNENCODED) - set(RULE_TEXT)
    assert not missing, f"encoded rules with no planner-facing sentence: {sorted(missing)}"


def test_no_sentence_names_a_rule_the_registry_does_not_have():
    registry = {
        match.group(1)
        for line in _text(SPECS / "rules.md").splitlines()
        if (match := re.match(r"\|\s*`(R-[A-Z-]+)`\s*\|", line))
    }
    unknown = set(RULE_TEXT) - registry
    assert not unknown, f"sentences for rules absent from the registry: {sorted(unknown)}"


# --- Nothing invented ---------------------------------------------------------------


@pytest.mark.parametrize("case", CASES)
def test_the_renderer_passes_its_own_validator(case, findings):
    """The bound has to be satisfiable, or it is not a standard."""
    instance, results = findings[case]
    for finding in results:
        text = render(finding, instance, weekday_of_day_zero=0)
        assert unsupported_terms(text, finding, instance) == set(), text


def test_the_validator_catches_an_invented_name(findings):
    instance, results = findings["scarce-skill/0"]
    finding = results[0]

    honest = render(finding, instance)
    invented = honest + "\n  E99 is also unavailable."

    assert "E99" in unsupported_terms(invented, finding, instance)


def test_the_validator_catches_an_invented_rule(findings):
    instance, results = findings["scarce-skill/0"]
    finding = results[0]

    invented = render(finding, instance) + "\n  Two would breach R-SUNDAY."
    assert "R-SUNDAY" in unsupported_terms(invented, finding, instance)


def test_the_validator_catches_an_invented_count(findings):
    """The subtle one. A wrong number reads as authoritative and is the likeliest thing a
    language model gets wrong while sounding right."""
    instance, results = findings["scarce-skill/0"]
    finding = results[0]

    invented = render(finding, instance) + "\n  47 staff are unavailable."
    assert "47" in unsupported_terms(invented, finding, instance)


def test_a_named_employee_must_be_one_the_finding_blocked(findings):
    """Naming a real employee who is *not* in this finding is still an invention, and the
    one a plausible-sounding rendering is most likely to commit.

    Scanned across the committed cases rather than pinned to one, because *which* case
    leaves somebody outside a finding is a property of the roster that came back, and
    `D-119` has just finished demonstrating how little that is worth relying on. A test
    that names a case for a property the case merely happens to have is a test that breaks
    for reasons unrelated to what it checks.
    """
    for instance, results in findings.values():
        for finding in results:
            involved = {entry.employee for entry in finding.blocked} | set(finding.unexplained)
            outsiders = [
                instance.employees[e].name
                for e in range(len(instance.employees))
                if e not in involved
            ]
            if not outsiders:
                continue
            text = render(finding, instance) + f"\n  {outsiders[0]} is unavailable."
            assert outsiders[0] in unsupported_terms(text, finding, instance)
            return

    pytest.fail("no committed case left an employee outside a finding, so nothing was tested")


# --- What it refuses to invent ------------------------------------------------------


def test_no_weekday_without_a_calendar(findings):
    """`domain.py` has no calendar by design, so a weekday cannot be derived from a day
    index. Saying `day 5` is honest; guessing `Sat` is a fabricated fact."""
    instance, _ = findings["headline/3"]

    without = slot(instance, 5, 1)
    assert "day 5" in without
    assert not any(name in without for name in ("Mon", "Sat", "Sun"))

    with_calendar = slot(instance, 5, 1, weekday_of_day_zero=0)
    assert "Sat" in with_calendar


def test_the_shift_label_is_printed_verbatim(findings):
    """`E` is the tenant's label. Expanding it to `Evening` is right for this generator and
    would be wrong for a tenant whose `E` means something else."""
    instance, _ = findings["headline/3"]
    assert f"({instance.shift_types[1].label})" in slot(instance, 5, 1)


def test_the_clock_rolls_over_midnight(findings):
    """A night shift starting at 23:00 runs to 07:00, not to 31:00."""
    instance, _ = findings["headline/3"]
    night = next(
        (o.day, o.shift)
        for o in instance.open_shifts
        if instance.window(o.day, o.shift).end % 24 < instance.window(o.day, o.shift).start % 24
    )
    text = slot(instance, *night)
    assert not re.search(r"\b(2[4-9]|3\d):", text), text


# --- Shape ---------------------------------------------------------------------------


def test_a_fully_staffed_roster_says_so(findings):
    instance, _ = findings["headline/3"]
    assert render_all((), instance) == "Every shift is fully staffed."


def test_an_unexplained_employee_is_reported_as_a_defect(findings):
    """The most useful sentence this module can produce, so it must not be silently dropped."""
    instance, _ = findings["headline/3"]
    finding = Shortfall(
        day=0,
        shift=0,
        required=2,
        assigned=1,
        blocked=(Blocked(employee=0, rules=("R-AVAIL",)),),
        unexplained=(1,),
    )

    text = render(finding, instance)
    assert "not optimal" in text
    assert instance.employees[1].name in text
    assert unsupported_terms(text, finding, instance) == set()


def test_small_groups_are_named_and_large_ones_counted(findings):
    instance, _ = findings["headline/3"]
    many = Shortfall(
        day=0,
        shift=0,
        required=9,
        assigned=0,
        blocked=tuple(Blocked(employee=e, rules=("R-AVAIL",)) for e in range(9)),
        unexplained=(),
    )
    assert "9 of the" in render(many, instance)

    few = Shortfall(
        day=0,
        shift=0,
        required=2,
        assigned=0,
        blocked=(Blocked(employee=0, rules=("R-AVAIL",)),),
        unexplained=(),
    )
    assert instance.employees[0].name in render(few, instance)


def test_supported_terms_covers_what_the_finding_holds(findings):
    instance, results = findings["tight/0"]
    finding = results[0]
    terms = supported_terms(finding, instance)

    for entry in finding.blocked:
        assert instance.employees[entry.employee].name in terms
        for rule in entry.rules:
            assert rule in terms
