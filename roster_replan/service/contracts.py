"""The wire format: Pydantic at the boundary, and the translation to `domain.py`.

`guide/api.md` asks for versioned contracts "so a model change never breaks a caller", and
that sentence is the whole design of this module. **The wire schema is a separate schema
from the domain dataclasses, not a serialisation of them.** Reusing `domain.Instance`
directly would be less code and would silently publish every internal field as public API:
renaming an attribute would then be a breaking change to every caller, which is exactly the
coupling the versioning is supposed to prevent.

The cost is this file -- a parallel set of models and two conversion functions. The benefit
is that `domain.py` stays free to change, and a wire format that must not change is
expressed in a file whose only job is to not change.

## Two validation layers, and they are not the same question

1. **Pydantic** answers *is this well-formed* -- types, required fields, ranges. A failure
   is a 422 with the field path, and nothing reaches the solver.
2. **`validation.validate_instance`** answers *is this a meaningful, lawful request* -- a
   derogation without a recorded basis, a shortfall weight that does not dominate, a flexi
   contract with no eligibility supplied. A failure is also a 422, and it carries rule
   language rather than schema language.

Keeping them apart matters because the second is domain knowledge that a schema cannot
express, and folding it into Pydantic validators would hide it from the tests that
currently own it.

## Two things JSON cannot carry, decided here

**Unbounded notice bands.** `NoticeBand.within_hours` is `inf` on the last band, and JSON
has no infinity -- `json.dumps` emits `Infinity`, which is not valid JSON and which strict
parsers reject. `null` means unbounded on the wire.

**Sets and tuples.** A `Roster` is a `frozenset` of `(employee, day, shift)`. On the wire it
is a list of three-element lists, and the round-trip restores the frozenset. Order is not
significant and is normalised on the way out, so two identical rosters serialise identically
-- which is what makes a response body comparable between runs.
"""

from __future__ import annotations

import math

from pydantic import BaseModel, ConfigDict, Field

from ..domain import (
    Disruption,
    Employee,
    Fairness,
    Instance,
    Interval,
    NoticeBand,
    OpenShift,
    RuleParams,
    ShiftType,
    SkillMixEntry,
)
from ..prose import render

API_VERSION = "v1"


class Strict(BaseModel):
    """Unknown fields are rejected rather than ignored.

    A caller who misspells `max_hours_this_week` should be told, not silently given a
    default. `domain.py` is explicit that a missing budget is rejected rather than defaulted
    -- the same principle, applied one layer out.
    """

    model_config = ConfigDict(extra="forbid")


# --- The instance ------------------------------------------------------------------


class IntervalIn(Strict):
    start: float
    end: float


class ShiftTypeIn(Strict):
    label: str
    start_hour: float
    span_hours: float = Field(gt=0)
    break_hours: float = Field(ge=0)


class SkillMixEntryIn(Strict):
    skill: str
    minimum: int = Field(ge=0)
    hard: bool
    provenance: str = ""


class OpenShiftIn(Strict):
    day: int = Field(ge=0)
    shift: int = Field(ge=0)
    required: int = Field(ge=0)
    required_skills: list[str] = Field(default_factory=list)
    skill_mix: list[SkillMixEntryIn] = Field(default_factory=list)


class EmployeeIn(Strict):
    name: str
    contract: str
    skills: list[str] = Field(default_factory=list)
    absences: list[IntervalIn] = Field(default_factory=list)
    unavailability: list[IntervalIn] = Field(default_factory=list)

    # `None` means "not supplied", which input validation rejects rather than defaulting.
    # The wire format preserves that distinction instead of substituting a zero.
    max_hours_this_week: float | None = None
    max_daily_hours: float | None = None

    # `R-MAX-PERIOD`. Optional in a way the two above are not: a one-week horizon cannot
    # tell it apart from the weekly budget, so a caller with nothing to add says nothing.
    max_hours_this_period: float | None = None

    consecutive_days_worked_before_horizon: int = 0
    last_shift_end_before_horizon: float | None = None

    # History the horizon does not contain, for the fairness term. Zero is the right
    # default here where it is the wrong one for a budget: a caller who says nothing is
    # saying this person has worked no unpopular shift in the window, which is a claim a
    # caller can make. A budget nobody stated is not.
    unpopular_shifts_before_horizon: int = 0

    # `R-MAX-WEEKENDS` and `R-MIN-DAYS-OFF`, optional in `R-MAX-PERIOD`'s sense: absent
    # means the caller is not asking for the rule (`D-135`).
    max_weekends: int | None = None
    min_consecutive_days_off: int | None = None

    # The rest of the same family (`D-136`). Absent means the caller is not asking for the
    # rule -- `D-138` is the record of these arriving late, encoded in both readings and
    # reachable from neither the wire nor a profile until then.
    min_consecutive_days_worked: int | None = None
    max_shifts_per_type: dict[int, int] | None = None
    min_hours_this_period: float | None = None
    max_consecutive_days: int | None = None
    # `R-DAY-OFF`: day indices, not intervals -- see the rule for why the two differ.
    days_off: list[int] = Field(default_factory=list)

    flexi_eligible: list[int] | None = None
    dimona_ok: list[int] | None = None
    hourly_rate: float | None = None


class NoticeBandIn(Strict):
    # `null` is unbounded. See the module docstring: JSON has no infinity.
    within_hours: float | None
    multiplier: int


class RuleParamsIn(Strict):
    min_rest_hours: float
    min_weekly_rest_hours: float
    min_period_hours: float
    max_consecutive_days: int | None

    # Which positions in a week `R-MAX-WEEKENDS` counts. Empty switches it off, and it is
    # asked for rather than derived because this domain has no calendar (`D-135`).
    weekend_days: list[int] = Field(default_factory=list)
    # `R-SUCCESSION`'s pairs, as two-element lists: JSON has no tuples and no sets.
    forbidden_successions: list[list[int]] = Field(default_factory=list)

    derogation_basis: dict[str, str] = Field(default_factory=dict)


class DisruptionIn(Strict):
    metric: str = Field(pattern=r"^D[0-4]$")
    published_weight: int
    draft_weight: int
    notice_bands: list[NoticeBandIn]
    move_weight: int
    cancel_weight: int
    call_in_weight: int
    concentration_weight: int
    concentration_tiers: int
    shortfall_weight: int
    mix_shortfall_weight: int
    cost_weight: int
    peak_weight: int


class FairnessIn(Strict):
    """The rolling balance of unpopular shifts, on the wire (`D-108`).

    Separate from `DisruptionIn` for the reason `domain.Fairness` is separate from
    `Disruption`: a tenant can want either without the other, and one object holding both
    cannot express that.

    `unpopular_shifts` are indices into `shift_types`, so the two travel together or the
    indices mean nothing.
    """

    weight: int
    unpopular_shifts: list[int]
    tiers: int


class InstanceIn(Strict):
    days: int = Field(gt=0)
    shift_types: list[ShiftTypeIn]
    employees: list[EmployeeIn]
    open_shifts: list[OpenShiftIn]
    params: RuleParamsIn

    now: float | None = None
    incumbent: list[list[int]] | None = None
    published_through: float | None = None
    disruption: DisruptionIn | None = None
    fairness: FairnessIn | None = None


class ReplanRequest(Strict):
    """What a caller POSTs.

    `tenant` is required and is not derived from anything -- the round-robin queue keys on
    it, and inferring it would make an operational behaviour depend on a guess. The
    per-tenant model cache keyed on it too, until it was deleted (`D-149`).

    `seed` and `profile_version` are recorded with every job because replay requires
    seeded determinism end to end: an input, a profile version and a seed are what make a
    solve replayable, and a solve that cannot be replayed cannot be debugged.
    """

    tenant: str = Field(min_length=1)
    instance: InstanceIn
    seed: int = 7
    budget_seconds: float = Field(default=30.0, gt=0, le=300)
    profile_version: str = "unversioned"


# --- Conversion ---------------------------------------------------------------------


def to_domain(payload: InstanceIn) -> Instance:
    """Wire to domain. Structural only -- no rule is applied and no default invented."""
    return Instance(
        days=payload.days,
        shift_types=tuple(
            ShiftType(
                label=s.label,
                start_hour=s.start_hour,
                span_hours=s.span_hours,
                break_hours=s.break_hours,
            )
            for s in payload.shift_types
        ),
        employees=tuple(
            Employee(
                name=e.name,
                contract=e.contract,
                skills=frozenset(e.skills),
                absences=tuple(Interval(i.start, i.end) for i in e.absences),
                unavailability=tuple(Interval(i.start, i.end) for i in e.unavailability),
                max_hours_this_week=e.max_hours_this_week,
                max_daily_hours=e.max_daily_hours,
                max_hours_this_period=e.max_hours_this_period,
                consecutive_days_worked_before_horizon=(
                    e.consecutive_days_worked_before_horizon
                ),
                last_shift_end_before_horizon=e.last_shift_end_before_horizon,
                unpopular_shifts_before_horizon=e.unpopular_shifts_before_horizon,
                max_weekends=e.max_weekends,
                min_consecutive_days_off=e.min_consecutive_days_off,
                min_consecutive_days_worked=e.min_consecutive_days_worked,
                max_shifts_per_type=(
                    None if e.max_shifts_per_type is None else dict(e.max_shifts_per_type)
                ),
                min_hours_this_period=e.min_hours_this_period,
                max_consecutive_days=e.max_consecutive_days,
                days_off=frozenset(e.days_off),
                flexi_eligible=(
                    None if e.flexi_eligible is None else frozenset(e.flexi_eligible)
                ),
                dimona_ok=None if e.dimona_ok is None else frozenset(e.dimona_ok),
                hourly_rate=e.hourly_rate,
            )
            for e in payload.employees
        ),
        open_shifts=tuple(
            OpenShift(
                day=o.day,
                shift=o.shift,
                required=o.required,
                required_skills=frozenset(o.required_skills),
                skill_mix=tuple(
                    SkillMixEntry(
                        skill=m.skill,
                        minimum=m.minimum,
                        hard=m.hard,
                        provenance=m.provenance,
                    )
                    for m in o.skill_mix
                ),
            )
            for o in payload.open_shifts
        ),
        params=RuleParams(
            min_rest_hours=payload.params.min_rest_hours,
            min_weekly_rest_hours=payload.params.min_weekly_rest_hours,
            min_period_hours=payload.params.min_period_hours,
            max_consecutive_days=payload.params.max_consecutive_days,
            weekend_days=frozenset(payload.params.weekend_days),
            forbidden_successions=frozenset(
                (pair[0], pair[1]) for pair in payload.params.forbidden_successions
            ),
            derogation_basis=dict(payload.params.derogation_basis),
        ),
        now=payload.now,
        incumbent=(
            None
            if payload.incumbent is None
            else frozenset(tuple(k) for k in payload.incumbent)
        ),
        published_through=payload.published_through,
        disruption=None if payload.disruption is None else _disruption(payload.disruption),
        fairness=(
            None
            if payload.fairness is None
            else Fairness(
                weight=payload.fairness.weight,
                unpopular_shifts=frozenset(payload.fairness.unpopular_shifts),
                tiers=payload.fairness.tiers,
            )
        ),
    )


def _disruption(payload: DisruptionIn) -> Disruption:
    return Disruption(
        metric=payload.metric,
        published_weight=payload.published_weight,
        draft_weight=payload.draft_weight,
        notice_bands=tuple(
            NoticeBand(
                within_hours=(
                    math.inf if b.within_hours is None else b.within_hours
                ),
                multiplier=b.multiplier,
            )
            for b in payload.notice_bands
        ),
        move_weight=payload.move_weight,
        cancel_weight=payload.cancel_weight,
        call_in_weight=payload.call_in_weight,
        concentration_weight=payload.concentration_weight,
        concentration_tiers=payload.concentration_tiers,
        shortfall_weight=payload.shortfall_weight,
        mix_shortfall_weight=payload.mix_shortfall_weight,
        cost_weight=payload.cost_weight,
        peak_weight=payload.peak_weight,
    )


def from_domain(instance: Instance) -> InstanceIn:
    """Domain back to wire. The inverse of `to_domain`, and tested as one.

    A round-trip that is not the identity means the wire format cannot express something
    the solver can, and the replay guarantee quietly stops holding -- a persisted payload
    would no longer reconstruct the solve it recorded.
    """
    return InstanceIn(
        days=instance.days,
        shift_types=[
            ShiftTypeIn(
                label=s.label,
                start_hour=s.start_hour,
                span_hours=s.span_hours,
                break_hours=s.break_hours,
            )
            for s in instance.shift_types
        ],
        employees=[
            EmployeeIn(
                name=e.name,
                contract=e.contract,
                skills=sorted(e.skills),
                absences=[IntervalIn(start=i.start, end=i.end) for i in e.absences],
                unavailability=[
                    IntervalIn(start=i.start, end=i.end) for i in e.unavailability
                ],
                max_hours_this_week=e.max_hours_this_week,
                max_daily_hours=e.max_daily_hours,
                max_hours_this_period=e.max_hours_this_period,
                consecutive_days_worked_before_horizon=(
                    e.consecutive_days_worked_before_horizon
                ),
                last_shift_end_before_horizon=e.last_shift_end_before_horizon,
                unpopular_shifts_before_horizon=e.unpopular_shifts_before_horizon,
                max_weekends=e.max_weekends,
                min_consecutive_days_off=e.min_consecutive_days_off,
                min_consecutive_days_worked=e.min_consecutive_days_worked,
                max_shifts_per_type=(
                    None if e.max_shifts_per_type is None else dict(e.max_shifts_per_type)
                ),
                min_hours_this_period=e.min_hours_this_period,
                max_consecutive_days=e.max_consecutive_days,
                days_off=sorted(e.days_off),
                flexi_eligible=(
                    None if e.flexi_eligible is None else sorted(e.flexi_eligible)
                ),
                dimona_ok=None if e.dimona_ok is None else sorted(e.dimona_ok),
                hourly_rate=e.hourly_rate,
            )
            for e in instance.employees
        ],
        open_shifts=[
            OpenShiftIn(
                day=o.day,
                shift=o.shift,
                required=o.required,
                required_skills=sorted(o.required_skills),
                skill_mix=[
                    SkillMixEntryIn(
                        skill=m.skill,
                        minimum=m.minimum,
                        hard=m.hard,
                        provenance=m.provenance,
                    )
                    for m in o.skill_mix
                ],
            )
            for o in instance.open_shifts
        ],
        params=RuleParamsIn(
            min_rest_hours=instance.params.min_rest_hours,
            min_weekly_rest_hours=instance.params.min_weekly_rest_hours,
            min_period_hours=instance.params.min_period_hours,
            max_consecutive_days=instance.params.max_consecutive_days,
            weekend_days=sorted(instance.params.weekend_days),
            forbidden_successions=[
                list(pair) for pair in sorted(instance.params.forbidden_successions)
            ],
            derogation_basis=dict(instance.params.derogation_basis),
        ),
        now=instance.now,
        # Sorted so two identical rosters serialise identically. A response body that
        # depends on set iteration order is not comparable between runs.
        incumbent=(
            None
            if instance.incumbent is None
            else [list(k) for k in sorted(instance.incumbent)]
        ),
        published_through=instance.published_through,
        disruption=(
            None
            if instance.disruption is None
            else DisruptionIn(
                metric=instance.disruption.metric,
                published_weight=instance.disruption.published_weight,
                draft_weight=instance.disruption.draft_weight,
                notice_bands=[
                    NoticeBandIn(
                        within_hours=(
                            None if math.isinf(b.within_hours) else b.within_hours
                        ),
                        multiplier=b.multiplier,
                    )
                    for b in instance.disruption.notice_bands
                ],
                move_weight=instance.disruption.move_weight,
                cancel_weight=instance.disruption.cancel_weight,
                call_in_weight=instance.disruption.call_in_weight,
                concentration_weight=instance.disruption.concentration_weight,
                concentration_tiers=instance.disruption.concentration_tiers,
                shortfall_weight=instance.disruption.shortfall_weight,
                mix_shortfall_weight=instance.disruption.mix_shortfall_weight,
                cost_weight=instance.disruption.cost_weight,
                peak_weight=instance.disruption.peak_weight,
            )
        ),
        fairness=(
            None
            if instance.fairness is None
            else FairnessIn(
                weight=instance.fairness.weight,
                # Sorted for the reason `incumbent` is: a body that depends on set
                # iteration order is not comparable between runs.
                unpopular_shifts=sorted(instance.fairness.unpopular_shifts),
                tiers=instance.fairness.tiers,
            )
        ),
    )


# --- The response -------------------------------------------------------------------


class ViolationOut(Strict):
    rule: str
    employee: int | None = None
    day: int | None = None
    shift: int | None = None


class ShortfallOut(Strict):
    """One under-staffed slot and why, on the wire.

    `summary` is rendered here rather than left to the caller so that every consumer — the
    API, a log line, and the prose layer — reads the same sentence. `D-013` requires the
    LLM to phrase a finding it did not identify, and this is the finding.
    """

    day: int
    shift: int
    required: int
    assigned: int
    short: int
    by_rule: dict[str, int]
    summary: str
    prose: str


class AnswerOut(Strict):
    """The ladder's answer, on the wire.

    Deliberately without a `success` flag, matching `ladder.Answer`. The rung, the gap and
    the violations are what a caller needs to judge this, and a boolean would be the service
    deciding on the caller's behalf what "good enough" means.
    """

    roster: list[list[int]]
    rung: str
    reason: str
    objective: int | None = None
    gap: float | None = None
    shortfall: int = 0
    violations: list[ViolationOut] = Field(default_factory=list)
    core: list[ViolationOut] = Field(default_factory=list)
    attempts: list[str] = Field(default_factory=list)
    shortfalls: list[ShortfallOut] = Field(default_factory=list)
    seconds: float = 0.0


class JobOut(Strict):
    id: str
    state: str
    tenant: str
    api_version: str = API_VERSION
    seed: int = 7
    profile_version: str = "unversioned"
    answer: AnswerOut | None = None
    error: str | None = None
    defects: list[dict] = Field(default_factory=list)


def answer_out(answer, instance: Instance) -> AnswerOut:
    return AnswerOut(
        roster=[list(k) for k in sorted(answer.roster)],
        rung=answer.rung,
        reason=answer.reason,
        objective=answer.objective,
        gap=answer.gap,
        shortfall=answer.shortfall,
        violations=[_violation(v) for v in answer.violations],
        core=[
            ViolationOut(rule=g.rule, employee=g.employee, day=g.day, shift=g.shift)
            for g in answer.core
        ],
        attempts=list(answer.attempts),
        shortfalls=[
            ShortfallOut(
                day=f.day,
                shift=f.shift,
                required=f.required,
                assigned=f.assigned,
                short=f.short,
                by_rule=f.by_rule(),
                summary=f.summary(),
                prose=render(f, instance),
            )
            for f in answer.shortfalls
        ],
        seconds=answer.seconds,
    )


def _violation(key: tuple) -> ViolationOut:
    rule, employee, day, shift = key
    return ViolationOut(rule=rule, employee=employee, day=day, shift=shift)
