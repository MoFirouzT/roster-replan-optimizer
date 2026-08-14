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

# A week is seven days from the horizon's start, and it is the span the week rules are
# measured over. This is calendar arithmetic of the same kind as the `day * 24.0` in
# `window` below, not a rule threshold: no rule can be relaxed by changing it, and a
# tenant cannot configure it. The domain still has no calendar -- a week here is a
# position in the horizon, never a Monday -- so a caller who needs the two to coincide
# starts the horizon on one.
DAYS_PER_WEEK = 7


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

    # History the horizon does not contain, for the fairness term. One week cannot be fair
    # on its own -- somebody has to work Saturday -- so the balance is struck over a window
    # the caller states and counts here (`D-108`). Parallel to the two fields above, which
    # carry history for `R-CONSEC-DAYS` and `R-REST-GAP` for the same reason.
    unpopular_shifts_before_horizon: int = 0

    # Eligibility gates, indexed by day: a Dimona may not cross a quarter boundary, so
    # one employee can be eligible on 30 June and not on 1 July inside one horizon.
    # None means "not supplied", which input validation rejects for a flexi contract --
    # an empty set would silently deny where the caller merely forgot to say.
    flexi_eligible: frozenset[int] | None = None
    dimona_ok: frozenset[int] | None = None

    # Cost, in currency units per hour. None means a uniform rate: the cost model is a
    # placeholder until T2 supplies wage data -- see replan.md.
    hourly_rate: float | None = None


@dataclass(frozen=True, slots=True)
class NoticeBand:
    """`multiplier` applies when notice is strictly less than `within_hours`.

    Bands are tested in order, so the last should be unbounded (`inf`).
    """

    within_hours: float
    multiplier: int


@dataclass(frozen=True, slots=True)
class Disruption:
    """Objective parameters. `replan.md` owns the semantics; nothing here is a rule.

    Weights are integers in "disruption points" -- CP-SAT is integral, and rounding a
    float weight at build time is a silent way for the model and an independent scorer
    to disagree about the optimum.
    """

    metric: str  # "D0" | "D1" | "D2" | "D3" | "D4"

    # D1: publication state. `draft_weight` is small but never zero -- see replan.md.
    published_weight: int
    draft_weight: int

    # D2: notice horizon.
    notice_bands: tuple[NoticeBand, ...]

    # D3: change type, applied per (employee, day).
    move_weight: int
    cancel_weight: int
    call_in_weight: int

    # D4: convex concentration. `tiers` is K in `t >= k*n - k(k-1)/2`.
    concentration_weight: int
    concentration_tiers: int

    # Commensuration. `shortfall_weight` must satisfy the domination bound in
    # replan.md, which `validation.py` checks rather than trusts.
    shortfall_weight: int
    mix_shortfall_weight: int
    cost_weight: int
    peak_weight: int

    def notice_multiplier(self, notice_hours: float) -> int:
        for band in self.notice_bands:
            if notice_hours < band.within_hours:
                return band.multiplier
        return self.notice_bands[-1].multiplier if self.notice_bands else 1


def shipped_d2(**overrides) -> Disruption:
    """The shipped default profile, as specified in `replan.md`.

    This is **data**, not a rule threshold: both readings receive it through the payload
    and neither derives anything from it, so a shared default cannot hide an encoding
    disagreement the way a shared `min_rest_hours` could. `req[d, s]` is shared for the
    same reason.

    The exchange rate embedded here -- one published change at short notice against two
    hours of overtime premium -- is a stated hypothesis awaiting T2 calibration, not a
    measurement.
    """
    defaults = dict(
        metric="D2",
        published_weight=10,
        draft_weight=1,
        notice_bands=(NoticeBand(24.0, 4), NoticeBand(float("inf"), 1)),
        move_weight=6,
        cancel_weight=10,
        call_in_weight=14,
        concentration_weight=2,
        concentration_tiers=4,
        shortfall_weight=100_000,
        mix_shortfall_weight=100_000,
        cost_weight=0,
        peak_weight=1,
    )
    return Disruption(**(defaults | overrides))


@dataclass(frozen=True, slots=True)
class Fairness:
    """Rolling balance of unpopular shifts. Separate from `Disruption` on purpose.

    `replan.md` scopes this as fairness *beyond* disruption concentration, and the two answer
    different questions: D4 spreads the **changes** a replan makes, this spreads the
    **shifts nobody wants** across weeks. A tenant can want either without the other, and
    folding them into one dataclass would make that impossible to express (`D-108`).

    `unpopular_shifts` holds indices into `Instance.shift_types`. Which shifts those are is a
    social fact about a tenant, not something this system can derive -- a late shift is a
    burden in one restaurant and the shift people compete for in another.
    """

    weight: int
    unpopular_shifts: frozenset[int]
    tiers: int

    @property
    def active(self) -> bool:
        """Off unless it is switched on, priced, and pointed at some shift.

        Three ways to be inert and all of them mean the same thing to the objective, so the
        term is skipped rather than encoded at zero: an unused variable per employee is not
        free at build time, and build time is most of the solve here (`D-081`).
        """
        return bool(self.weight and self.tiers and self.unpopular_shifts)


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

    # A slot is published iff its start is before this. Parallel to `now`, and the
    # special case of a general `published ⊆ O` -- see replan.md.
    published_through: float | None = None
    disruption: Disruption | None = None
    fairness: Fairness | None = None

    # Memoised `window` results, filled on first use. Not a field a caller supplies:
    # excluded from `init`, from equality and from `repr`, so two instances differing only
    # in what they have been asked are still equal and `dataclasses.replace` still works.
    #
    # This is a cache, not a convention, and it is the one thing in this module that is
    # neither a data container nor a rule -- see `window` for why it is here rather than in
    # a caller.
    _windows: dict = field(default_factory=dict, init=False, compare=False, repr=False)

    def is_published(self, day: int, shift: int) -> bool:
        published = self.published_through
        return published is not None and self.window(day, shift).start < published

    def notice_hours(self, day: int, shift: int) -> float:
        """Hours between `now` and the slot's start. Infinite on a cold solve, where
        there is no `now` and therefore no notice to give."""
        if self.now is None:
            return float("inf")
        return self.window(day, shift).start - self.now

    def window(self, day: int, shift: int) -> Interval:
        """Absolute hours from the horizon start. Start-day attribution: a span may
        run past midnight into `day + 1`, and it still belongs to `day`.

        **Memoised, and that is a performance fix rather than a design flourish.** Building
        the model calls this about 3,500 times and there are only `days x shift_types`
        distinct answers -- 21 for a one-week horizon with three shift types. Profiling
        `build` put 60% of its time in this one method, which made it the largest single
        cost in the whole solve path: at T2 sizes the model is built more slowly than it is
        searched, so the dominant cost of a replan was allocating the same 21 intervals
        thousands of times.

        Returning a shared `Interval` is safe because it is frozen -- no caller can mutate
        one, and equality is by value, so a cached result is indistinguishable from a fresh
        one. The cache is unbounded but its size is `days x shift_types`, fixed per instance
        and freed with it.
        """
        cached = self._windows.get((day, shift))
        if cached is None:
            shift_type = self.shift_types[shift]
            begin = day * 24.0 + shift_type.start_hour
            cached = Interval(begin, begin + shift_type.span_hours)
            self._windows[day, shift] = cached
        return cached

    def horizon(self) -> Interval:
        return Interval(0.0, self.days * 24.0)

    @property
    def weeks(self) -> int:
        """Whole and part weeks in the horizon. A trailing part-week counts as a week:
        hours worked in it are hours worked in a week, and the rule is measured over the
        part that lies inside the horizon."""
        return -(-self.days // DAYS_PER_WEEK)

    def week_of(self, day: int) -> int:
        return day // DAYS_PER_WEEK

    def week_span(self, week: int) -> Interval:
        """The week's hours, clipped to the horizon.

        Clipping is what makes a one-week horizon behave exactly as it did before weeks
        existed here: there is one week, its span is the horizon, and both readings
        measure what they always measured.
        """
        start = week * DAYS_PER_WEEK * 24.0
        return Interval(start, min(start + DAYS_PER_WEEK * 24.0, self.horizon().end))

    def week_start_day(self, week: int) -> int:
        """The day coordinate a week rule reports itself at, so a violation and a gate
        name *which* week — the coordinate the automaton was rejected for losing."""
        return week * DAYS_PER_WEEK

    def day_anchor(self, day: int) -> int:
        """The shift type anchoring publication state and notice for a whole day.

        A `replan.md` convention, shared for the same reason half-open overlap is: D3
        prices changes per (employee, day), so it needs one slot per day to read `P` and
        `N` from. It must be **solution-independent** -- anchoring on the earliest
        *affected* slot would make the weight depend on which slots changed, which is
        both non-linear and impossible to match between the two readings.
        """
        candidates = [o.shift for o in self.open_shifts if o.day == day]
        return min(candidates, key=lambda s: self.window(day, s).start)

    def is_past(self, day: int, shift: int) -> bool:
        """A shift in progress is past: the boundary is `start < now`, strictly."""
        return self.now is not None and self.window(day, shift).start < self.now
