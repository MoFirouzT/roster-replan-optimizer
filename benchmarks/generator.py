"""The seeded scenario generator.

`docs/benchmarks.md` states the instance distribution, and states why: *an undefined
distribution makes a p95 unfalsifiable*. This module is that distribution, executable.

Three things about its shape are decisions rather than mechanics, and each is recorded
in `docs/decisions.md`:

**A benchmark case is a scenario, not an instance.** A replan is a function of a
published roster and a disruption to it, so the generator runs in two phases: build and
solve a base week, then injure it. An instance alone cannot pose the question this
project answers.

**The incumbent is solved, not invented.** The base week is solved cold and the result
becomes `x̄`. A hand-built incumbent would be one the solver finds easy or impossible for
reasons nobody chose. The cost is stated rather than hidden: the incumbent comes from the
same solver under test, which is a weaker baseline than a real published roster, and
replacing it with real ones is exactly what `capture.md` exists to do.

**Tightness is measured, not asserted.** The parameter below is a *target*: demand as a
share of workforce capacity. What lands on a scenario is the realised eligibility slack,
computed after availability and skills have had their say, using the model's own presolve.
`D-060` makes tightness the knob that decides whether the D0-D4 study can see anything at
all, so a nominal figure would quietly decide the study's answer.

Rule thresholds appear here as they do in `tests/micro_instances.py`: this is an instance
source, and every payload has to carry every parameter explicitly (`D-039`). Nothing here
is reachable from either reading of the rules.
"""

from __future__ import annotations

import dataclasses
import random
from dataclasses import dataclass

from roster_replan.domain import (
    FLEXI,
    Employee,
    Instance,
    Interval,
    OpenShift,
    Roster,
    RuleParams,
    ShiftType,
    shipped_d2,
)
from roster_replan.model import Unproven, exclusions, solve

# --- The tenant's fixed furniture ---------------------------------------------------
# Three 8h spans on an eight-hour grid with a 30-minute break, so `span` and `work_hours`
# differ and a rule reading the wrong one is visible rather than coincidentally right.

MORNING, EVENING, NIGHT = 0, 1, 2

SHIFT_TYPES: tuple[ShiftType, ...] = (
    ShiftType(label="M", start_hour=7.0, span_hours=8.0, break_hours=0.5),
    ShiftType(label="E", start_hour=15.0, span_hours=8.0, break_hours=0.5),
    ShiftType(label="N", start_hour=23.0, span_hours=8.0, break_hours=0.5),
)

RULE_PARAMS = RuleParams(
    min_rest_hours=11.0,
    min_weekly_rest_hours=35.0,
    min_period_hours=3.0,
    max_consecutive_days=6,
)

SCARCE_SKILL = "kitchen"
BASE_SKILL = "bar"

DAYS = 7
WORK_HOURS = SHIFT_TYPES[0].work_hours

# --- Disruption events --------------------------------------------------------------

SICK_CALL = "sick_call"
MULTI_ABSENCE = "multi_absence"
DEMAND_SPIKE = "demand_spike"
AVAILABILITY_WITHDRAWAL = "availability_withdrawal"

EVENTS = (SICK_CALL, MULTI_ABSENCE, DEMAND_SPIKE, AVAILABILITY_WITHDRAWAL)


@dataclass(frozen=True, slots=True)
class ScenarioParams:
    """The generator's knobs, one per axis named in `docs/benchmarks.md`.

    `demand_ratio` is the tightness *target*: required shift-hours as a share of the
    workforce's total weekly budget. It drives generation; it is not what gets reported.
    See `Tightness` for what does.

    `scarce_skill_share` is benchmarks.md's "skill scarcity", expressed as the share of
    employees who **hold** the scarce skill, so a larger number means a less scarce
    skill. A knob whose direction has to be remembered is a knob that gets set wrongly.

    Student contracts are absent on purpose. `R-STUDENT-QUOTA` is a profile-gated T2 rule
    and is not yet encoded, so a student share would move no constraint -- a knob that
    does nothing makes the instance distribution look richer than it is.
    """

    employees: int = 12
    demand_ratio: float = 0.70
    scarce_skill_share: float = 0.5
    flexi_share: float = 0.25
    availability_density: float = 0.85
    event: str = SICK_CALL
    event_day: int = 5
    event_hour: float = 9.0


@dataclass(frozen=True, slots=True)
class Tightness:
    """What the instance turned out to be, as against what was asked for.

    `demand_ratio` here is recomputed from the generated payload, so it differs from the
    requested one by the rounding that turning hours into whole shift instances forces.

    The slot figures are the ones that bind. They are computed over the *eligible* pairs
    that survive `model.exclusions()`, so availability and skill scarcity are inside the
    number rather than beside it.
    """

    demand_hours: float
    capacity_hours: float
    demand_ratio: float
    min_slot_slack: int
    tight_slots: int
    short_slots: int

    @property
    def guarantees_shortfall(self) -> bool:
        """Some shift has fewer eligible people than it requires, so no roster covers it.

        A legitimate scenario -- `D-018` makes the coverage floor soft precisely so this
        comes back priced rather than refused -- but one the instance set should know it
        is holding.
        """
        return self.short_slots > 0


@dataclass(frozen=True, slots=True)
class Scenario:
    """A replan question: a published week, and something that went wrong with it."""

    name: str
    seed: int
    params: ScenarioParams
    base: Instance
    incumbent: Roster
    base_shortfall: int
    instance: Instance
    tightness: Tightness


# --- Employees ----------------------------------------------------------------------


def _employees(rng: random.Random, params: ScenarioParams) -> tuple[Employee, ...]:
    count = params.employees
    flexi_count = round(count * params.flexi_share)
    skilled_count = round(count * params.scarce_skill_share)

    people = []
    for index in range(count):
        flexi = index < flexi_count
        skills = {BASE_SKILL}
        if index < skilled_count:
            skills.add(SCARCE_SKILL)

        # Flexi budgets are smaller: the reference-period arithmetic and the income
        # ceiling both land in this one number (`D-014`, `D-033`).
        budget = rng.choice((16.0, 20.0, 24.0)) if flexi else rng.choice((32.0, 38.0, 38.0))

        people.append(
            Employee(
                name=f"E{index:02d}",
                contract=FLEXI if flexi else "salaried",
                skills=frozenset(skills),
                unavailability=_unavailability(rng, params),
                max_hours_this_week=budget,
                max_daily_hours=8.0,
                consecutive_days_worked_before_horizon=0,
                # Eligibility is resolved upstream and enters as data (`D-032`). The
                # generator plays the caller: eligible on every day of the horizon.
                flexi_eligible=frozenset(range(DAYS)) if flexi else None,
                dimona_ok=frozenset(range(DAYS)) if flexi else None,
            )
        )
    # Shuffle so flexi contracts and the scarce skill are not correlated with the index,
    # which would otherwise make employee 0 systematically special across every seed.
    rng.shuffle(people)
    return tuple(people)


def _unavailability(rng: random.Random, params: ScenarioParams) -> tuple[Interval, ...]:
    """Declared unavailability, not absence.

    The distinction is `D-020`'s: what a person said in advance, as against what befell
    them. The event injected later is the second kind, so the base week must only carry
    the first or the replan has nothing to distinguish.
    """
    blocks = []
    for day in range(DAYS):
        if rng.random() < params.availability_density:
            continue
        start = day * 24.0 + rng.choice((0.0, 7.0, 15.0))
        blocks.append(Interval(start, start + rng.choice((8.0, 12.0, 24.0))))
    return tuple(blocks)


# --- Demand -------------------------------------------------------------------------


def _demand(rng: random.Random, params: ScenarioParams, people) -> tuple[OpenShift, ...]:
    """Size total demand to hit `demand_ratio` against the workforce's weekly budgets.

    Capacity is the sum of the supplied budgets rather than a headcount times a nominal
    week: the budget *is* the constraint (`R-MAX-WEEKLY`), and a flexi worker on 16h is
    not half a salaried one for any other purpose.
    """
    capacity = sum(p.max_hours_this_week for p in people)
    slots = max(1, round(capacity * params.demand_ratio / WORK_HOURS))
    grid = _grid()
    weights = [_load(day, shift) for day, shift in grid]

    if slots < len(grid):
        # A loose week is not a full grid with thin demand -- it is a week that does not
        # open every shift. `O` is the set of pairs with `req > 0` (`model.md`), so
        # closing a slot is how low demand is actually expressed. Forcing all 21 open
        # would floor the achievable ratio and quietly cap how loose a scenario can be.
        opened = _sample(rng, grid, weights, slots)
        required = {key: 1 for key in opened}
    else:
        required = {key: 1 for key in grid}
        for _ in range(slots - len(grid)):
            # Weight the extra bodies toward the shifts a hospitality week actually
            # loads: evenings, and the back half of the week.
            required[rng.choices(grid, weights=weights)[0]] += 1

    holders = round(len(people) * params.scarce_skill_share)
    return tuple(
        OpenShift(
            day=day,
            shift=shift,
            required=required[day, shift],
            # The scarce skill is required on evenings, which is also where the demand
            # weighting puts the bodies. No guard against demanding more holders than
            # exist: that case is the whole point of the knob, and `Tightness` reports
            # it as `short_slots` rather than the generator quietly preventing it.
            required_skills=frozenset({SCARCE_SKILL})
            if shift == EVENING and holders
            else frozenset(),
        )
        for day, shift in sorted(required)
    )


def _sample(rng: random.Random, grid, weights, count: int) -> list[tuple[int, int]]:
    """Weighted sample without replacement. `rng.choices` samples *with*, and a repeat
    would silently become one slot rather than two."""
    pool = list(zip(grid, weights))
    picked = []
    for _ in range(count):
        key = rng.choices([k for k, _ in pool], weights=[w for _, w in pool])[0]
        picked.append(key)
        pool = [(k, w) for k, w in pool if k != key]
    return picked


def _grid() -> list[tuple[int, int]]:
    return [(day, shift) for day in range(DAYS) for shift in (MORNING, EVENING, NIGHT)]


def _load(day: int, shift: int) -> float:
    weekend = 1.6 if day >= 4 else 1.0
    return weekend * {MORNING: 1.0, EVENING: 1.5, NIGHT: 0.6}[shift]


# --- Measured tightness -------------------------------------------------------------


def measure(instance: Instance) -> Tightness:
    """Realised slack, computed against the eligibility the solver will actually see.

    Uses `model.exclusions()` rather than a second reading of the eligibility rules. That
    is deliberate and is not an independence breach: tightness is a *description* of an
    instance, not a claim about what is legal, and the description that matters is the one
    the solver is working from.
    """
    excluded = exclusions(instance)
    capacity = sum(p.max_hours_this_week or 0.0 for p in instance.employees)
    demand_hours = sum(o.required * WORK_HOURS for o in instance.open_shifts)

    slacks = []
    for open_shift in instance.open_shifts:
        eligible = sum(
            1
            for employee in range(len(instance.employees))
            if (employee, open_shift.day, open_shift.shift) not in excluded
        )
        slacks.append(eligible - open_shift.required)

    return Tightness(
        demand_hours=demand_hours,
        capacity_hours=capacity,
        demand_ratio=demand_hours / capacity if capacity else 0.0,
        min_slot_slack=min(slacks, default=0),
        tight_slots=sum(1 for s in slacks if s == 0),
        short_slots=sum(1 for s in slacks if s < 0),
    )


# --- Events -------------------------------------------------------------------------
# Each returns the instance as it looks *after* the disruption. `now` and the incumbent
# are already set by then, so a shift that has started is pinned (`R-PIN-PAST`) and the
# event can only reach the part of the week still in front of the planner.


def _apply_event(
    rng: random.Random, instance: Instance, incumbent: Roster, params: ScenarioParams
) -> Instance:
    if params.event == SICK_CALL:
        return _absences(rng, instance, incumbent, count=1, declared=False)
    if params.event == MULTI_ABSENCE:
        return _absences(rng, instance, incumbent, count=3, declared=False)
    if params.event == AVAILABILITY_WITHDRAWAL:
        return _absences(rng, instance, incumbent, count=1, declared=True)
    if params.event == DEMAND_SPIKE:
        return _spike(rng, instance)
    raise ValueError(f"unknown event {params.event!r}; expected one of {EVENTS}")


def _absences(
    rng: random.Random,
    instance: Instance,
    incumbent: Roster,
    *,
    count: int,
    declared: bool,
) -> Instance:
    """Take people out of shifts they were already published as working.

    Targets *future* assignments only. An absence over a shift that has already started
    is a real thing, but it is not a replan question -- the past is pinned and the model
    would report it as an illegal incumbent rather than repair it.
    """
    future = sorted(
        key for key in incumbent if not instance.is_past(key[1], key[2])
    )
    if not future:
        return instance

    rng.shuffle(future)
    chosen: dict[int, list[tuple[int, int, int]]] = {}
    for employee, day, shift in future:
        if len(chosen) >= count:
            break
        chosen.setdefault(employee, []).append((employee, day, shift))

    people = list(instance.employees)
    for employee, keys in chosen.items():
        person = people[employee]
        blocks = tuple(instance.window(day, shift) for _, day, shift in keys)
        people[employee] = dataclasses.replace(
            person,
            unavailability=person.unavailability + blocks
            if declared
            else person.unavailability,
            absences=person.absences if declared else person.absences + blocks,
        )
    return dataclasses.replace(instance, employees=tuple(people))


def _spike(rng: random.Random, instance: Instance) -> Instance:
    """Demand goes up on a shift nobody has staffed yet."""
    future = [o for o in instance.open_shifts if not instance.is_past(o.day, o.shift)]
    if not future:
        return instance

    target = rng.choice(future)
    return dataclasses.replace(
        instance,
        open_shifts=tuple(
            dataclasses.replace(o, required=o.required + 1) if o is target else o
            for o in instance.open_shifts
        ),
    )


# --- The generator ------------------------------------------------------------------


def generate(seed: int, params: ScenarioParams | None = None) -> Scenario:
    """One seed, one scenario. The same seed gives the same scenario, always."""
    params = params or ScenarioParams()
    if params.event not in EVENTS:
        raise ValueError(f"unknown event {params.event!r}; expected one of {EVENTS}")
    rng = random.Random(seed)

    people = _employees(rng, params)
    base = Instance(
        days=DAYS,
        shift_types=SHIFT_TYPES,
        employees=people,
        open_shifts=_demand(rng, params, people),
        params=RULE_PARAMS,
        disruption=shipped_d2(),
    )

    solution = solve(base, seed=seed)
    if isinstance(solution, list):
        raise RuntimeError(
            f"seed {seed} produced a base week with no legal roster at all, which "
            f"`D-047` says should be nearly unreachable: {solution}"
        )
    if isinstance(solution, Unproven):
        raise RuntimeError(
            f"seed {seed}'s base week did not solve within the budget ({solution.status}); "
            f"the committed set's fingerprints depend on this being deterministic, so a "
            f"timeout here would silently move instances rather than fail"
        )

    # The whole week is published. That is the case a replan is actually asked about, and
    # it is the hardest one -- every change is priced at `published_weight` (`D-051`).
    published = dataclasses.replace(
        base,
        now=params.event_day * 24.0 + params.event_hour,
        incumbent=solution.roster,
        published_through=DAYS * 24.0,
    )
    instance = _apply_event(rng, published, solution.roster, params)

    return Scenario(
        name=f"{params.event}-n{params.employees}-d{params.demand_ratio:g}-s{seed}",
        seed=seed,
        params=params,
        base=base,
        incumbent=solution.roster,
        base_shortfall=sum(solution.shortfall.values()),
        instance=instance,
        tightness=measure(instance),
    )
