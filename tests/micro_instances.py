"""The committed ground-truth instance set.

Twenty-nine micro-instances, each small enough to enumerate exhaustively and each chosen to
exercise a *structure* rather than to look realistic. Committed and versioned so that a
change in the model which alters an optimum shows up as a diff on a stable input, which is
the whole point: random instances catch bugs, fixed ones catch regressions.

Several exist because they were the structure that hid a live bug behind a green suite --
`incumbent_became_ineligible` and `move_pairs_within_a_day` in particular. A ground-truth
layer only covers the structures its instances contain, so structures earn a permanent
place here once they have caught something.

**Enumeration budget.** Stage (a) and (b) enumerate `2 ** (employees x open_shifts)`, so
every instance here keeps that product at 10 or below. The cost is checked by a test rather
than trusted to review, since an accidentally large instance would not fail -- it would
just make the suite slow, which is how enumeration layers quietly get deleted.

Serialisation is deliberately absent. These are Python constructors, not JSON: a schema and
a loader are T2's problem, alongside the versioned *benchmark* set they are actually needed
for. "Committed" here means fixed and diffable, which a module already is.
"""

from __future__ import annotations

from roster_replan.domain import (
    Employee,
    Instance,
    Interval,
    NoticeBand,
    OpenShift,
    RuleParams,
    SkillMixEntry,
    ShiftType,
    shipped_d2,
)

MORNING, EVENING, NIGHT = 0, 1, 2

SHIFTS = (
    ShiftType("M", 7.0, 8.0, 0.5),
    ShiftType("E", 15.0, 8.0, 0.5),
    ShiftType("N", 23.0, 8.0, 0.5),  # crosses midnight
)

# Every instance runs on a **7-day horizon** even where only two or three shifts are open,
# and that is not incidental. `R-WEEKLY-REST` requires its 35-hour window to fall inside the
# horizon, so a 3-day instance cannot hold one alongside work on more than a single day --
# the rule would bind everywhere for a reason that belongs to the horizon rather than
# of the roster. Lowering the parameter instead would need a derogation basis, and inventing
# a legal one to quiet the validator is exactly the dishonesty `rules.md` exists to prevent.
#
# Enumeration cost is `2 ** (employees x open_shifts)` and does not depend on `days`, so a
# long horizon is free. Statutory parameters throughout, and the one real derogation carries
# a real citation.
HORIZON_DAYS = 7

BASE_PARAMS = RuleParams(
    min_rest_hours=11.0,
    min_weekly_rest_hours=35.0,
    min_period_hours=3.0,
    max_consecutive_days=6,
)


def person(name: str, **overrides) -> Employee:
    defaults = dict(
        contract="salaried",
        skills=frozenset({"bar"}),
        max_hours_this_week=38.0,
        max_daily_hours=8.0,
    )
    return Employee(name=name, **(defaults | overrides))


def instance(*, employees, open_shifts, days=HORIZON_DAYS, params=None, **overrides) -> Instance:
    return Instance(
        days=days,
        shift_types=SHIFTS,
        employees=tuple(employees),
        open_shifts=tuple(open_shifts),
        params=params or BASE_PARAMS,
        disruption=overrides.pop("disruption", shipped_d2()),
        **overrides,
    )


def mornings(count: int, required: int = 1) -> tuple[OpenShift, ...]:
    return tuple(OpenShift(day=d, shift=MORNING, required=required) for d in range(count))


ABC = [person(n) for n in ("Ana", "Bram", "Chloe")]


def _cold_clean() -> Instance:
    """Three people, three morning shifts, nothing in the way. The control."""
    return instance(employees=ABC, open_shifts=mornings(3))


def _coverage_shortfall_forced() -> Instance:
    """Demand exceeds the workforce, so the soft floor must absorb it rather than the
    solve failing. The behaviour that makes a cold solve essentially never infeasible."""
    return instance(
        employees=[person("Solo")],
        open_shifts=(OpenShift(day=0, shift=MORNING, required=3),),
    )


def _overstaffing_impossible() -> Instance:
    """More willing bodies than the requirement: the hard ceiling must bind."""
    return instance(employees=ABC, open_shifts=(OpenShift(day=0, shift=MORNING, required=1),))


def _absence_partial_day() -> Instance:
    """An absence covering the morning only. Day-granular availability would wrongly
    block the evening too -- the correction to the walking skeleton."""
    return instance(
        employees=[person("Ana", absences=(Interval(6.0, 12.0),)), *ABC[1:]],
        open_shifts=(
            OpenShift(day=0, shift=MORNING, required=1),
            OpenShift(day=0, shift=EVENING, required=1),
        ),
    )


def _absence_versus_unavailability() -> Instance:
    """Both block, and both must be reported under R-AVAIL, but only one is relaxable.
    The distinction is invisible to the solved model and visible to the explainer."""
    return instance(
        employees=[
            person("Ana", absences=(Interval(6.0, 16.0),)),
            person("Bram", unavailability=(Interval(6.0, 16.0),)),
            ABC[2],
        ],
        open_shifts=mornings(3),
    )


def _night_crosses_midnight() -> Instance:
    """A night shift starting at 23:00 ends on the following day. Start-day attribution
    and the rest gap into the next morning both depend on getting this right."""
    return instance(
        employees=ABC,
        open_shifts=(
            OpenShift(day=0, shift=NIGHT, required=1),
            OpenShift(day=1, shift=MORNING, required=1),
        ),
    )


def _rest_gap_binds() -> Instance:
    """Morning and evening the same day are 0 hours apart: nobody may hold both."""
    return instance(
        employees=[person("Ana"), person("Bram")],
        open_shifts=(
            OpenShift(day=0, shift=MORNING, required=1),
            OpenShift(day=0, shift=EVENING, required=1),
        ),
    )


def _rest_gap_across_the_horizon_start() -> Instance:
    """A shift that ended at 02:00 on day 0 constrains that morning. A week boundary is an
    side effect of the payload, not of the employee's working life."""
    return instance(
        employees=[
            person("Ana", last_shift_end_before_horizon=2.0),
            person("Bram"),
            ABC[2],
        ],
        open_shifts=mornings(3),
    )


# Found by mutation testing. The three main shift types sit on an 8-hour grid, so every
# inter-shift gap they can produce is 0, 8 or 16 hours -- and a rest threshold of 9 hours is
# therefore indistinguishable from 11. Lowering `min_rest_hours` in the model passed the
# entire ground-truth suite. Pinning a threshold needs instances *at* it, so these two
# bracket 11 hours from either side with a 6-hour shift grid.
THRESHOLD_SHIFTS = (
    ShiftType("early", 8.0, 6.0, 0.0),  # 08:00-14:00
    ShiftType("ten", 0.0, 6.0, 0.0),  # next day 00:00, a 10-hour gap
    ShiftType("eleven", 1.0, 6.0, 0.0),  # next day 01:00, an 11-hour gap
)


def _threshold_instance(second_shift: int, name: str) -> Instance:
    return Instance(
        days=HORIZON_DAYS,
        shift_types=THRESHOLD_SHIFTS,
        employees=(person(name),),
        open_shifts=(
            OpenShift(day=0, shift=0, required=1),
            OpenShift(day=1, shift=second_shift, required=1),
        ),
        params=BASE_PARAMS,
        disruption=shipped_d2(),
    )


def _rest_gap_ten_hours_conflicts() -> Instance:
    """A gap of exactly 10 hours: under the 11-hour rule, one person cannot hold both, so
    the soft floor absorbs one shift. Distinguishes a threshold of 11 from anything below."""
    return _threshold_instance(1, "Ten")


def _rest_gap_eleven_hours_is_legal() -> Instance:
    """A gap of exactly 11 hours: lawful, because the rule is `gap < minimum`. Distinguishes
    a threshold of 11 from anything above, and pins the comparison as strict."""
    return _threshold_instance(2, "Eleven")


def _consecutive_days_binds() -> Instance:
    """Two people, three consecutive days, a limit of two."""
    return instance(
        employees=[person("Ana"), person("Bram")],
        open_shifts=mornings(3),
        params=RuleParams(
            min_rest_hours=11.0,
            min_weekly_rest_hours=35.0,
            min_period_hours=3.0,
            max_consecutive_days=2,
        ),
    )


def _consecutive_days_with_history() -> Instance:
    """A prior streak the horizon cannot see. Windows that begin at day 0 silently grant a
    fresh streak, which is the bug this instance exists to keep caught."""
    return instance(
        employees=[
            person("Ana", consecutive_days_worked_before_horizon=2),
            person("Bram"),
            ABC[2],
        ],
        open_shifts=mornings(3),
        params=RuleParams(
            min_rest_hours=11.0,
            min_weekly_rest_hours=35.0,
            min_period_hours=3.0,
            max_consecutive_days=2,
        ),
    )


def _weekly_rest_binds() -> Instance:
    """A 2-day horizon where the statutory 35-hour window genuinely competes with the work.

    The only instance here on a short horizon, and the exception proves the rule above:
    working both mornings leaves a longest free run of 33 hours, so somebody must be free
    for a whole day. That is over-strict against the statute -- the window may legally
    straddle the horizon edge -- and `rules.md` records the conservatism. Kept because it
    is the only shape that exercises the candidate-window encoding at all.
    """
    return instance(
        days=2,
        employees=[person("Ana"), person("Bram")],
        open_shifts=(
            OpenShift(day=0, shift=MORNING, required=1),
            OpenShift(day=1, shift=MORNING, required=1),
        ),
    )


def _weekly_budget_binds() -> Instance:
    """A budget of 8 hours against 7.5-hour net shifts: one shift each, no more."""
    return instance(
        employees=[person(n, max_hours_this_week=8.0) for n in ("Ana", "Bram", "Chloe")],
        open_shifts=mornings(3),
    )


def _weekly_budget_on_the_threshold() -> Instance:
    """A budget of 14.5 hours against two 7.5-hour net shifts: 15 hours does not fit, and
    15.5 would. The second boundary instance mutation testing asked for.

    `weekly_budget_binds` above proves the rule *exists*; only this one proves it is
    enforced at the right number. A budget of 8 or 38 hours sits far from any shift-count
    boundary, so adding an hour to the ceiling changes no optimum and the mutation survives.
    """
    return instance(
        employees=[person("Budget", max_hours_this_week=14.5)],
        open_shifts=(
            OpenShift(day=0, shift=MORNING, required=1),
            OpenShift(day=2, shift=MORNING, required=1),
        ),
    )


def _weekly_budget_distinguishes_net_from_span() -> Instance:
    """A budget of exactly 15 hours against two shifts of 7.5 net hours and 8.0 gross.

    Net fits exactly; gross does not. So this is the instance that pins `R-MAX-WEEKLY` to
    `work_hours` rather than `span` -- the distinction `model.md` carries two symbols for,
    and the one a single `hours(d, s)` would have got wrong by a break per shift.

    Needs its own instance because the discrimination is narrow: any budget outside
    [15.0, 16.0) admits the same shift count either way, and the two nearby threshold
    instances both sit outside it.
    """
    return instance(
        employees=[person("NetOrSpan", max_hours_this_week=15.0)],
        open_shifts=(
            OpenShift(day=0, shift=MORNING, required=1),
            OpenShift(day=2, shift=MORNING, required=1),
        ),
    )


def _daily_maximum_on_the_threshold() -> Instance:
    """Two 4-hour periods in one day against a 7.5-hour daily maximum: 8 hours does not
    fit, and 8.5 would. The same boundary argument as the weekly budget, one axis down."""
    short = (
        ShiftType("a", 7.0, 4.0, 0.0),
        ShiftType("b", 12.0, 4.0, 0.0),
    )
    return Instance(
        days=HORIZON_DAYS,
        shift_types=short,
        employees=(person("Daily", max_daily_hours=7.5),),
        open_shifts=(
            OpenShift(day=0, shift=0, required=1),
            OpenShift(day=0, shift=1, required=1),
        ),
        params=RuleParams(
            min_rest_hours=1.0,
            min_weekly_rest_hours=35.0,
            min_period_hours=3.0,
            max_consecutive_days=6,
            derogation_basis={"min_rest_hours": "Arbeidswet art. 38ter §2 - split work periods"},
        ),
        disruption=shipped_d2(),
    )


def _daily_maximum_binds_on_split_shifts() -> Instance:
    """Where R-MAX-DAILY is not implied by the rest gap: two short periods in one day,
    which is lawful in horeca and is what makes the daily total bind independently."""
    short = (
        ShiftType("a", 7.0, 4.0, 0.0),
        ShiftType("b", 12.0, 4.0, 0.0),
        ShiftType("c", 23.0, 8.0, 0.5),
    )
    return Instance(
        days=HORIZON_DAYS,
        shift_types=short,
        employees=(person("Ana", max_daily_hours=6.0), person("Bram", max_daily_hours=6.0)),
        open_shifts=(
            OpenShift(day=0, shift=0, required=1),
            OpenShift(day=0, shift=1, required=1),
        ),
        params=RuleParams(
            min_rest_hours=1.0,
            min_weekly_rest_hours=35.0,
            min_period_hours=3.0,
            max_consecutive_days=6,
            # A genuine derogation with a genuine source: art. 38ter §2 permits departure
            # from the eleven-hour rest for split work periods, which is precisely this.
            derogation_basis={"min_rest_hours": "Arbeidswet art. 38ter §2 - split work periods"},
        ),
        disruption=shipped_d2(),
    )


def _skill_scarcity() -> Instance:
    """One qualified person, two shifts needing the skill. Scarcity surfaces as a priced
    shortfall rather than as an infeasibility."""
    return instance(
        employees=[
            person("Ana", skills=frozenset({"bar", "forklift"})),
            person("Bram", skills=frozenset({"bar"})),
        ],
        open_shifts=(
            OpenShift(day=0, shift=MORNING, required=1, required_skills=frozenset({"forklift"})),
            OpenShift(day=1, shift=MORNING, required=1, required_skills=frozenset({"forklift"})),
        ),
    )


def _soft_skill_mix() -> Instance:
    """A covered shift with nobody qualified: a real operational state, priced, not a
    refusal."""
    return instance(
        employees=[person("Ana"), person("Bram")],
        open_shifts=(
            OpenShift(
                day=0,
                shift=MORNING,
                required=2,
                skill_mix=(SkillMixEntry("first_aid", 1, hard=False),),
            ),
        ),
    )


def _hard_skill_mix() -> Instance:
    """The legally-gated variant: running without the qualified person is prohibited, not
    expensive. Same shape, opposite class."""
    return instance(
        employees=[
            person("Ana", skills=frozenset({"bar", "nurse"})),
            person("Bram"),
            ABC[2],
        ],
        open_shifts=(
            OpenShift(
                day=0,
                shift=MORNING,
                required=2,
                skill_mix=(
                    SkillMixEntry("nurse", 1, hard=True, provenance="sector CBA [CITE]"),
                ),
            ),
        ),
    )


def _flexi_eligible_some_days() -> Instance:
    """Per-day eligibility, not per-employee: a Dimona may not cross a quarter boundary,
    so one worker can be eligible on Tuesday and not on Wednesday inside one horizon."""
    return instance(
        employees=[
            person(
                "Ana",
                contract="flexi",
                flexi_eligible=frozenset({0, 1}),
                dimona_ok=frozenset({0, 1}),
            ),
            person("Bram"),
        ],
        open_shifts=mornings(3),
    )


def _flexi_without_dimona() -> Instance:
    """Eligible but unfiled. Two rules, two operator actions: "this person cannot hold a
    flexi job" is not "the paperwork is not in"."""
    return instance(
        employees=[
            person(
                "Ana",
                contract="flexi",
                flexi_eligible=frozenset({0, 1, 2}),
                dimona_ok=frozenset({0}),
            ),
            person("Bram"),
        ],
        open_shifts=mornings(3),
    )


def _pinned_past() -> Instance:
    """`now` part-way through the horizon. Pinned hours still consume the weekly budget
    and still constrain the next morning: pinning is not exemption."""
    return instance(
        employees=ABC,
        open_shifts=mornings(3),
        now=30.0,
        incumbent=frozenset({(0, 0, MORNING), (1, 1, MORNING), (2, 2, MORNING)}),
        published_through=HORIZON_DAYS * 24.0,
    )


def _pinned_past_already_illegal() -> Instance:
    """An incumbent that breaks a rule in the part of the horizon nothing can change.
    Reported as "the past itself is illegal", not as "no legal future exists"."""
    return instance(
        employees=[person("Ana", max_daily_hours=8.0), person("Bram")],
        open_shifts=(
            OpenShift(day=0, shift=MORNING, required=1),
            OpenShift(day=0, shift=EVENING, required=1),
        ),
        now=30.0,
        incumbent=frozenset({(0, 0, MORNING), (0, 0, EVENING)}),
        published_through=HORIZON_DAYS * 24.0,
    )


def _incumbent_became_ineligible() -> Instance:
    """The structure that hid a live bug behind a green stage (b): presolve removes the
    ineligible pair, so without a variable the drop of a newly-absent employee was
    invisible to the objective."""
    return instance(
        employees=[person("Ana", absences=(Interval(6.0, 16.0),)), person("Bram"), ABC[2]],
        open_shifts=mornings(3),
        now=0.0,
        incumbent=frozenset({(0, 0, MORNING), (1, 1, MORNING), (2, 2, MORNING)}),
        published_through=HORIZON_DAYS * 24.0,
    )


def _move_pairs_within_a_day() -> Instance:
    """A repair that D3 sees as one move and D2 as two changes. The structure that made an
    employee-index-dependent move weight pass the whole suite."""
    return instance(
        employees=[person("Ana", absences=(Interval(7.0, 15.0),)), person("Bram"), ABC[2]],
        open_shifts=(
            OpenShift(day=0, shift=MORNING, required=1),
            OpenShift(day=0, shift=EVENING, required=1),
        ),
        now=0.0,
        incumbent=frozenset({(0, 0, MORNING), (1, 0, EVENING)}),
        published_through=24.0,
    )


def _published_and_draft() -> Instance:
    """Half the horizon announced, half not. The publication step is what separates D1
    from D0, and a single `published_through` is what makes it one number."""
    return instance(
        employees=ABC,
        open_shifts=mornings(3),
        now=0.0,
        incumbent=frozenset({(0, 0, MORNING), (1, 1, MORNING), (2, 2, MORNING)}),
        published_through=24.0,
    )


def _notice_on_the_band_boundary() -> Instance:
    """`now` set so one shift falls exactly on the 24-hour threshold. Bands are
    half-open, and a boundary instance is how that stays true."""
    return instance(
        employees=ABC,
        open_shifts=mornings(3),
        now=7.0,  # day 1 morning starts at 31.0, exactly 24 hours out
        incumbent=frozenset({(0, 0, MORNING), (1, 1, MORNING), (2, 2, MORNING)}),
        published_through=HORIZON_DAYS * 24.0,
        disruption=shipped_d2(notice_bands=(NoticeBand(24.0, 4), NoticeBand(float("inf"), 1))),
    )


MICRO_INSTANCES: dict[str, Instance] = {
    "cold_clean": _cold_clean(),
    "coverage_shortfall_forced": _coverage_shortfall_forced(),
    "overstaffing_impossible": _overstaffing_impossible(),
    "absence_partial_day": _absence_partial_day(),
    "absence_versus_unavailability": _absence_versus_unavailability(),
    "night_crosses_midnight": _night_crosses_midnight(),
    "rest_gap_binds": _rest_gap_binds(),
    "rest_gap_across_the_horizon_start": _rest_gap_across_the_horizon_start(),
    "rest_gap_ten_hours_conflicts": _rest_gap_ten_hours_conflicts(),
    "rest_gap_eleven_hours_is_legal": _rest_gap_eleven_hours_is_legal(),
    "consecutive_days_binds": _consecutive_days_binds(),
    "consecutive_days_with_history": _consecutive_days_with_history(),
    "weekly_rest_binds": _weekly_rest_binds(),
    "weekly_budget_binds": _weekly_budget_binds(),
    "weekly_budget_on_the_threshold": _weekly_budget_on_the_threshold(),
    "weekly_budget_distinguishes_net_from_span": _weekly_budget_distinguishes_net_from_span(),
    "daily_maximum_on_the_threshold": _daily_maximum_on_the_threshold(),
    "daily_maximum_binds_on_split_shifts": _daily_maximum_binds_on_split_shifts(),
    "skill_scarcity": _skill_scarcity(),
    "soft_skill_mix": _soft_skill_mix(),
    "hard_skill_mix": _hard_skill_mix(),
    "flexi_eligible_some_days": _flexi_eligible_some_days(),
    "flexi_without_dimona": _flexi_without_dimona(),
    "pinned_past": _pinned_past(),
    "pinned_past_already_illegal": _pinned_past_already_illegal(),
    "incumbent_became_ineligible": _incumbent_became_ineligible(),
    "move_pairs_within_a_day": _move_pairs_within_a_day(),
    "published_and_draft": _published_and_draft(),
    "notice_on_the_band_boundary": _notice_on_the_band_boundary(),
}

# Instances whose incumbent already breaks a rule, so a solve legitimately returns a core
# rather than a roster. Enumeration has no optimum to compare against for these.
EXPECTED_INFEASIBLE = {"pinned_past_already_illegal"}


def enumeration_cost(instance: Instance) -> int:
    return len(instance.employees) * len(instance.open_shifts)
