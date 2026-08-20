"""The seeded scenario generator.

What this layer is for is narrow and worth stating, because it is easy to write tests
here that assert the generator ran rather than that it works. A generator can be wrong in
three ways that a green suite would not notice:

- **A dead knob.** A parameter that moves nothing still produces plausible instances, and
  the study built on them reports "no effect" as a property of the generator.
- **A no-op event.** An injected disruption that misses everything yields a replan whose
  answer is "change nothing", which looks like a very good result.
- **A drifting seed.** Non-reproducible instances make every committed number unfalsifiable.

Each has a test below. The tightness assertions matter most: `D-060` makes coverage
tightness the knob that decides whether the D0-D4 study can see anything at all.
"""

from __future__ import annotations

import dataclasses

import pytest
from conftest import solved

from benchmarks.generator import (
    AVAILABILITY_WITHDRAWAL,
    DEMAND_SPIKE,
    EVENTS,
    MULTI_ABSENCE,
    SCARCE_SKILL,
    SICK_CALL,
    ScenarioParams,
    generate,
    measure,
)
from roster_replan.validation import validate_instance

# Kept small on purpose: every scenario costs a full solve, and a generator suite that
# doubles the runtime of the whole test run is one that gets marked slow and then skipped.
LOOSE = ScenarioParams(employees=8, demand_ratio=0.4)
TYPICAL = ScenarioParams(employees=12, demand_ratio=0.7)
TIGHT = ScenarioParams(employees=14, demand_ratio=0.9)


# --- Reproducibility ----------------------------------------------------------------


def test_same_seed_gives_the_same_scenario():
    """Without this every committed benchmark number is unfalsifiable."""
    first, second = generate(11, TYPICAL), generate(11, TYPICAL)

    assert first.instance == second.instance
    assert first.incumbent == second.incumbent
    assert first.tightness == second.tightness


def test_different_seeds_give_different_payloads():
    """The complement of the test above, and it has to compare the **base week**.

    Comparing the replan instance passes for the wrong reason: `generate` hands the seed
    to the solver as well, so a fixed generator rng still yields different incumbents and
    therefore different instances. Mutation testing found this -- pinning
    `random.Random(0)` left the weaker version of this test perfectly green.

    `base` is built entirely from the generator's rng, before any solve, so it isolates
    the thing actually under test.
    """
    # Compared pairwise rather than through a set: `Instance` carries `derogation_basis`
    # as a dict and is deliberately not hashable.
    weeks = [generate(seed, TYPICAL).base for seed in range(4)]

    assert all(a != b for i, a in enumerate(weeks) for b in weeks[i + 1 :])
    assert len({tuple(p.name for p in w.employees) for w in weeks}) > 1, (
        "employee ordering is identical across seeds; the shuffle is not seeded"
    )


# --- The payload is well-formed -----------------------------------------------------


@pytest.mark.parametrize("params", [LOOSE, TYPICAL, TIGHT])
def test_generated_scenarios_are_valid_payloads(params):
    """Input validation is the caller's contract, and here the generator *is* the caller.

    Both instances are checked: a replan carries `now` and the incumbent together, and a
    base week carries neither, so the two exercise different branches of `D-040`'s layer.
    """
    scenario = generate(3, params)

    assert validate_instance(scenario.base) == []
    assert validate_instance(scenario.instance) == []


@pytest.mark.parametrize("event", EVENTS)
def test_every_event_produces_a_solvable_replan(event):
    """The suite-wide invariant of `D-063`, applied to generated instances: zero hard
    checker violations, and `OPTIMAL` rather than a truncated search."""
    scenario = generate(5, dataclasses.replace(TYPICAL, event=event))

    solved(scenario.instance)


# --- Tightness is measured, not asserted --------------------------------------------


@pytest.mark.parametrize("requested", [0.4, 0.7, 0.9])
def test_measured_demand_ratio_tracks_the_requested_one(requested):
    """`D-060`'s knob has to actually turn.

    The tolerance is the rounding that turning hours into whole shift instances forces,
    and it is asserted rather than eyeballed so a change that floors the achievable range
    -- opening all 21 slots regardless of demand, say -- fails here instead of quietly
    capping how loose a scenario can be.
    """
    scenario = generate(7, dataclasses.replace(TYPICAL, demand_ratio=requested))

    assert scenario.tightness.demand_ratio == pytest.approx(requested, abs=0.05)


def test_a_loose_week_does_not_open_every_shift():
    """Low demand is expressed by closing slots, not by thinning a full grid. `O` is the
    set of pairs with `req > 0`, so a full grid at low demand is a different instance."""
    loose = generate(7, LOOSE)
    tight = generate(7, TIGHT)

    assert len(loose.instance.open_shifts) < len(tight.instance.open_shifts)


def test_tightness_counts_slots_no_roster_can_staff():
    """A shift requiring more people than are eligible for it is a guaranteed shortfall.

    Legitimate -- `D-018` makes the floor soft so it comes back priced rather than
    refused -- but the instance set has to know it is holding one.
    """
    starved = generate(2, dataclasses.replace(TIGHT, scarce_skill_share=0.1))

    assert starved.tightness.short_slots > 0
    assert starved.tightness.guarantees_shortfall
    assert starved.tightness.min_slot_slack < 0


def test_scarcity_is_inside_the_tightness_number():
    """Eligibility, not headcount.

    Two instances with identical demand and identical employee counts must not measure as
    equally tight when one of them cannot staff its evenings. This is what `measure()`
    reading the model's presolve buys, and a version counting bodies would pass every
    other test in this file.
    """
    plentiful = generate(4, dataclasses.replace(TYPICAL, scarce_skill_share=0.9))
    scarce = generate(4, dataclasses.replace(TYPICAL, scarce_skill_share=0.2))

    assert plentiful.tightness.demand_hours == scarce.tightness.demand_hours
    assert scarce.tightness.min_slot_slack < plentiful.tightness.min_slot_slack


# --- The events do something --------------------------------------------------------


@pytest.mark.parametrize("event", EVENTS)
def test_every_event_changes_the_published_week(event):
    """A disruption that misses everything produces a replan whose best answer is 'change
    nothing', which reads as an excellent result and measures nothing at all."""
    scenario = generate(9, dataclasses.replace(TYPICAL, event=event))

    assert scenario.instance != scenario.base
    if event == DEMAND_SPIKE:
        before = sum(o.required for o in scenario.base.open_shifts)
        assert sum(o.required for o in scenario.instance.open_shifts) > before
    else:
        blocked = sum(
            len(p.absences) + len(p.unavailability) for p in scenario.instance.employees
        )
        was = sum(len(p.absences) + len(p.unavailability) for p in scenario.base.employees)
        assert blocked > was


@pytest.mark.parametrize(
    ("event", "attribute"),
    [(SICK_CALL, "absences"), (AVAILABILITY_WITHDRAWAL, "unavailability")],
)
def test_absence_and_withdrawal_are_different_provenances(event, attribute):
    """`D-020`: one rule, two provenances. A sick call is a fact about the world; a
    withdrawal is something a person declared. A generator that injected both as absences
    would make the relaxable case untestable, and nothing else in the suite would notice.
    """
    scenario = generate(6, dataclasses.replace(TYPICAL, event=event))

    added = [
        person
        for person, before in zip(scenario.instance.employees, scenario.base.employees)
        if getattr(person, attribute) != getattr(before, attribute)
    ]
    other = "unavailability" if attribute == "absences" else "absences"
    assert added, f"{event} added nothing to {attribute}"
    assert all(
        getattr(p, other) == getattr(b, other)
        for p, b in zip(scenario.instance.employees, scenario.base.employees)
    )


def test_multi_absence_hits_more_people_than_a_sick_call():
    def struck(scenario):
        return sum(
            1
            for person, before in zip(scenario.instance.employees, scenario.base.employees)
            if person.absences != before.absences
        )

    assert struck(generate(8, dataclasses.replace(TYPICAL, event=MULTI_ABSENCE))) > struck(
        generate(8, dataclasses.replace(TYPICAL, event=SICK_CALL))
    )


def test_events_never_reach_a_shift_that_has_already_started():
    """An absence over a pinned shift is a real thing, but it is not a replan question:
    `R-PIN-PAST` makes it an illegal incumbent the model reports rather than repairs.
    Generating one would silently swap what the benchmark is measuring."""
    for event in (SICK_CALL, MULTI_ABSENCE, AVAILABILITY_WITHDRAWAL):
        scenario = generate(12, dataclasses.replace(TYPICAL, event=event))
        instance = scenario.instance

        for index, (person, before) in enumerate(
            zip(instance.employees, scenario.base.employees)
        ):
            new = set(person.absences + person.unavailability) - set(
                before.absences + before.unavailability
            )
            for day, shift in ((d, s) for e, d, s in scenario.incumbent if e == index):
                if instance.window(day, shift) in new:
                    assert not instance.is_past(day, shift), (
                        f"{event} struck a pinned shift for employee {index}"
                    )


# --- The incumbent ------------------------------------------------------------------


def test_the_whole_week_is_published_and_the_incumbent_is_pinned_where_past():
    """`D-051`: publication state is one cutoff. The replan case is a week that is out,
    which is also the hardest -- every change is priced at `published_weight`."""
    scenario = generate(13, TYPICAL)
    instance = scenario.instance

    assert instance.now is not None and instance.incumbent is not None
    assert all(
        instance.is_published(o.day, o.shift) for o in instance.open_shifts
    )
    assert any(instance.is_past(o.day, o.shift) for o in instance.open_shifts)


def test_the_replan_stays_near_the_incumbent():
    """The thesis, at the smallest scale that can express it: repairing a single sick call
    on a week with slack should move a couple of assignments, not re-cut the roster.

    Deliberately loose. This is a guard against the objective silently reverting to
    cost-from-scratch (`D-005`), not a benchmark -- the real number is `benchmarks.md`'s to report.
    """
    scenario = generate(14, dataclasses.replace(TYPICAL, event=SICK_CALL))
    result = solved(scenario.instance)

    changed = result.roster ^ scenario.incumbent
    assert 0 < len(changed) <= 6


def test_measure_reads_eligibility_rather_than_headcount():
    """Directly, without a solve: block everyone on one shift and the slack must fall."""
    scenario = generate(15, TYPICAL)
    target = scenario.base.open_shifts[0]
    window = scenario.base.window(target.day, target.shift)

    blocked = dataclasses.replace(
        scenario.base,
        employees=tuple(
            dataclasses.replace(p, unavailability=p.unavailability + (window,))
            for p in scenario.base.employees
        ),
    )

    assert measure(blocked).min_slot_slack < measure(scenario.base).min_slot_slack
    assert measure(blocked).short_slots > 0


def test_the_scarce_skill_is_required_somewhere():
    """A skill nothing asks for is a knob attached to nothing."""
    scenario = generate(16, TYPICAL)

    assert any(
        SCARCE_SKILL in o.required_skills for o in scenario.instance.open_shifts
    )
