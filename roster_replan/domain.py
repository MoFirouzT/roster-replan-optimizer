"""Payload schema and stated conventions, shared by the model and the checker.

This module is the *only* thing those two readings may share, and what it may contain
is fixed by `docs/specs/rules.md#independence-rule`:

- data containers, so the differential harness can feed both readings one instance;
- the conventions `rules.md` fixes by definition -- half-open overlap, start-day
  attribution, ``work_hours = span - break_hours``.

It contains **no rule predicate and no rule threshold**. There is deliberately no
default for ``min_rest_hours``, ``min_weekly_rest_hours``, ``max_consecutive_days`` or
``min_period_hours``: a shared threshold is invisible to both the brute-force and the
differential layer, because both readings would be wrong in the same direction. Every
rule parameter arrives explicitly in the payload.

Time is hours as a float, measured from the start of the horizon. Timestamps belong at
the API boundary (T3), not here -- the rules are arithmetic and stay testable without a
calendar. Values before the horizon are negative.
"""

from __future__ import annotations

from dataclasses import dataclass, field

# (employee, day, shift type). The roster is the set of assignments that are 1.
Assignment = tuple[int, int, int]
Roster = frozenset[Assignment]

# Schema vocabulary, not a rule parameter: both readings name the same contract type.
FLEXI = "flexi"


@dataclass(frozen=True, slots=True)
class Interval:
    """A half-open interval of hours from the horizon start.

    Half-open is a `rules.md` convention rather than a rule: two shifts where one ends
    exactly as the other begins do not overlap.
    """

    start: float
    end: float

    def overlaps(self, other: Interval) -> bool:
        return self.start < other.end and other.start < self.end


@dataclass(frozen=True, slots=True)
class ShiftType:
    """A shift's shape. `start_hour` is within its day; a span may cross midnight."""

    label: str
    start_hour: float
    span_hours: float
    break_hours: float

    @property
    def work_hours(self) -> float:
        """Net working time. Breaks are not working time -- see `rules.md`."""
        return self.span_hours - self.break_hours


@dataclass(frozen=True, slots=True)
class SkillMixEntry:
    """One composition requirement on a shift: `minimum` assignees holding `skill`.

    `hard` is per entry, not per rule: "at least one licensed nurse" is prohibitive
    where "at least one first-aider" is priced. `provenance` is required when hard.
    """

    skill: str
    minimum: int
    hard: bool
    provenance: str = ""


@dataclass(frozen=True, slots=True)
class OpenShift:
    """An open shift instance -- a (day, shift type) pair with positive demand."""

    day: int
    shift: int
    required: int
    required_skills: frozenset[str] = frozenset()
    skill_mix: tuple[SkillMixEntry, ...] = ()


@dataclass(frozen=True, slots=True)
class Employee:
    name: str
    contract: str
    skills: frozenset[str]

    # R-AVAIL, split by provenance: absences are never relaxable, declared
    # unavailability is relaxable-by-literal and tenant-configurable to soft in T2.
    absences: tuple[Interval, ...] = ()
    unavailability: tuple[Interval, ...] = ()

    # Caller-computed, per `model.md`. None means "not supplied", which input
    # validation rejects rather than defaulting -- never a silent zero.
    max_hours_this_week: float | None = None
    max_daily_hours: float | None = None
    consecutive_days_worked_before_horizon: int = 0
    last_shift_end_before_horizon: float | None = None

    # Eligibility gates, indexed by day: a Dimona may not cross a quarter boundary, so
    # one employee can be eligible on 30 June and not on 1 July inside one horizon.
    # None means "not supplied", which input validation rejects for a flexi contract --
    # an empty set would silently deny where the caller merely forgot to say.
    flexi_eligible: frozenset[int] | None = None
    dimona_ok: frozenset[int] | None = None


@dataclass(frozen=True, slots=True)
class RuleParams:
    """Every rule threshold, supplied explicitly. No defaults live here -- see module docstring."""

    min_rest_hours: float
    min_weekly_rest_hours: float
    min_period_hours: float
    max_consecutive_days: int | None
    derogation_basis: dict[str, str] = field(default_factory=dict)


@dataclass(frozen=True, slots=True)
class Instance:
    days: int
    shift_types: tuple[ShiftType, ...]
    employees: tuple[Employee, ...]
    open_shifts: tuple[OpenShift, ...]
    params: RuleParams

    # Replan inputs. Both present or both absent -- input validation enforces it.
    now: float | None = None
    incumbent: Roster | None = None

    def window(self, day: int, shift: int) -> Interval:
        """Absolute hours from the horizon start. Start-day attribution: a span may
        run past midnight into `day + 1`, and it still belongs to `day`."""
        begin = day * 24.0 + self.shift_types[shift].start_hour
        return Interval(begin, begin + self.shift_types[shift].span_hours)

    def horizon(self) -> Interval:
        return Interval(0.0, self.days * 24.0)

    def is_past(self, day: int, shift: int) -> bool:
        """A shift in progress is past: the boundary is `start < now`, strictly."""
        return self.now is not None and self.window(day, shift).start < self.now
