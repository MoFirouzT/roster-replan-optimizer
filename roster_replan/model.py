"""The CP-SAT model: the other reading of `docs/specs/rules.md`.

Imports `domain` and `ortools`, and **never** `checker`. Every predicate here is written
from the spec rather than from the checker, which is what makes comparing the two
meaningful. If a helper in this module starts to look like one in `checker.py`, that is
the design working, not duplication to factor out.

Two things the spec asks of this module that are easy to skip:

- **Every hard constraint instance is gated on an assumption literal.** Not decoration:
  it is what lets a failed solve name the conflicting rule instances, and it is what
  makes `violations()` below able to report rather than merely refuse.
- **Pinning is not exemption.** Past assignments stay inside every other rule's sums.
  That falls out here by construction, because pinned shifts are ordinary variables
  carrying an equality rather than constants substituted at build time.

CP-SAT is integral, so durations are carried in **minutes** internally. The conversion
is arithmetic rather than a rule threshold, so it lives here rather than in `domain`.
"""

from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass, field

from ortools.sat.python import cp_model

from .domain import FLEXI, Instance, Roster

# --- Provisional objective weights --------------------------------------------------
# `replan.md` owns the objective and is still an outline: D2 is not shipped, so nothing
# here is decided. The soft-shortfall terms are forced by `rules.md` (a soft floor that
# is not priced is not a floor), but the scale and the disruption term are placeholders.
#
# DISRUPTION_WEIGHT prices a raw count of changed assignments -- the D0 that `replan.md`
# explicitly rejects. It is here so a replan has *an* objective, and it must be replaced
# when D2 lands. Grep D0_PLACEHOLDER before believing any objective value from this file.
D0_PLACEHOLDER = True
COVER_SHORTFALL_WEIGHT = 1000
MIX_SHORTFALL_WEIGHT = 1000
DISRUPTION_WEIGHT = 1
PEAK_WEIGHT = 1


def _minutes(hours: float) -> int:
    return int(round(hours * 60))


@dataclass(frozen=True, slots=True)
class Gate:
    """A gated hard-constraint instance, addressed the way a `Violation` is.

    The field order matches `checker.Violation.key()` so the differential harness can
    compare the two readings without either side knowing about the other.
    """

    rule: str
    employee: int | None = None
    day: int | None = None
    shift: int | None = None

    def key(self) -> tuple:
        return (self.rule, self.employee, self.day, self.shift)


@dataclass
class Built:
    """A built model and the handles needed to interrogate it."""

    model: cp_model.CpModel
    x: dict[tuple[int, int, int], cp_model.IntVar]
    shortfall: dict[tuple[int, int], cp_model.IntVar]
    overage: dict[tuple[int, int], cp_model.IntVar]
    mix_shortfall: dict[tuple[int, int, str], cp_model.IntVar]
    gates: dict[int, Gate] = field(default_factory=dict)
    literals: list[cp_model.IntVar] = field(default_factory=list)
    # Pairs the presolve removed, with the rules that removed them. These never become
    # variables, so they can only be reported from here.
    excluded: dict[tuple[int, int, int], tuple[str, ...]] = field(default_factory=dict)

    def gate(self, model: cp_model.CpModel, descriptor: Gate) -> cp_model.IntVar:
        literal = model.new_bool_var(f"gate_{len(self.literals)}")
        self.gates[literal.index] = descriptor
        self.literals.append(literal)
        return literal


# --- Presolve -----------------------------------------------------------------------
# R-AVAIL, R-SKILL, R-FLEXI-ELIG and R-DIMONA-FLX are all enforced by *removing*
# variables rather than constraining them. Most (employee, shift) pairs are impossible,
# and eliminating them is often the largest single win and free. The reasons are kept
# because a removed pair can otherwise never be reported.


def exclusions(instance: Instance) -> dict[tuple[int, int, int], tuple[str, ...]]:
    excluded: dict[tuple[int, int, int], tuple[str, ...]] = {}
    for employee, person in enumerate(instance.employees):
        for open_shift in instance.open_shifts:
            day, shift = open_shift.day, open_shift.shift
            window = instance.window(day, shift)
            reasons: list[str] = []

            if any(window.overlaps(b) for b in person.absences + person.unavailability):
                reasons.append("R-AVAIL")
            if not open_shift.required_skills <= person.skills:
                reasons.append("R-SKILL")
            if person.contract == FLEXI:
                if day not in (person.flexi_eligible or frozenset()):
                    reasons.append("R-FLEXI-ELIG")
                if day not in (person.dimona_ok or frozenset()):
                    reasons.append("R-DIMONA-FLX")

            if reasons:
                excluded[employee, day, shift] = tuple(reasons)
    return excluded


def build(instance: Instance) -> Built:
    """The model, with every hard constraint instance gated."""
    model = cp_model.CpModel()
    excluded = exclusions(instance)
    incumbent = instance.incumbent or frozenset()

    # A variable exists for every eligible pair, and additionally for an *ineligible*
    # pair the incumbent already assigned to a past shift. Without the second case an
    # already-illegal past could not be represented, and "the past itself is illegal"
    # would be indistinguishable from a clean solve.
    keys = [
        (e, o.day, o.shift)
        for e in range(len(instance.employees))
        for o in instance.open_shifts
        if (e, o.day, o.shift) not in excluded
        or (instance.is_past(o.day, o.shift) and (e, o.day, o.shift) in incumbent)
    ]

    built = Built(
        model=model,
        x={k: model.new_bool_var(f"x_{k[0]}_{k[1]}_{k[2]}") for k in keys},
        shortfall={},
        overage={},
        mix_shortfall={},
        excluded=excluded,
    )

    # An ineligible pair that only exists to carry a pin is still ineligible.
    for key in keys:
        if key in excluded:
            model.add(built.x[key] == 0)

    _cover(built, instance)
    _skill_mix(built, instance)
    _pin_past(built, instance, incumbent)
    _rest_gap(built, instance)
    _weekly_rest(built, instance)
    _max_weekly(built, instance)
    _max_daily(built, instance)
    _consec_days(built, instance)
    return built


# --- R-COVER ------------------------------------------------------------------------
# One equality per shift instance with an explicit slack, rather than two inequalities:
# the equality gives CP-SAT the tighter linear relaxation, and the slack is directly the
# coordinate the explainer reports.
#
# The ceiling is gated as `overage == 0` rather than folded into the slack's domain, so
# that a fixed overstaffed roster can be *reported* instead of merely rejected.


def _cover(built: Built, instance: Instance) -> None:
    model = built.model
    for open_shift in instance.open_shifts:
        day, shift, required = open_shift.day, open_shift.shift, open_shift.required
        assigned = [
            built.x[e, day, shift]
            for e in range(len(instance.employees))
            if (e, day, shift) in built.x
        ]
        short = model.new_int_var(0, max(required, 0), f"u_{day}_{shift}")
        over = model.new_int_var(0, max(len(assigned) - required, 0), f"o_{day}_{shift}")
        built.shortfall[day, shift] = short
        built.overage[day, shift] = over
        model.add(sum(assigned) + short - over == required)

        literal = built.gate(model, Gate("R-COVER", None, day, shift))
        model.add(over == 0).only_enforce_if(literal)


# --- R-SKILL-MIX --------------------------------------------------------------------
# Clamped to the headcount actually rostered, so a missing body is R-COVER's finding
# and is not billed twice.


def _skill_mix(built: Built, instance: Instance) -> None:
    model = built.model
    for open_shift in instance.open_shifts:
        day, shift = open_shift.day, open_shift.shift
        on_shift = [
            built.x[e, day, shift]
            for e in range(len(instance.employees))
            if (e, day, shift) in built.x
        ]
        for entry in open_shift.skill_mix:
            holders = [
                built.x[e, day, shift]
                for e in range(len(instance.employees))
                if (e, day, shift) in built.x and entry.skill in instance.employees[e].skills
            ]
            need = model.new_int_var(0, entry.minimum, f"need_{day}_{shift}_{entry.skill}")
            model.add_min_equality(need, [entry.minimum, sum(on_shift)])

            if entry.hard:
                literal = built.gate(model, Gate("R-SKILL-MIX", None, day, shift))
                model.add(sum(holders) >= need).only_enforce_if(literal)
            else:
                slack = model.new_int_var(0, entry.minimum, f"v_{day}_{shift}_{entry.skill}")
                built.mix_shortfall[day, shift, entry.skill] = slack
                model.add(sum(holders) + slack >= need)


# --- R-PIN-PAST -------------------------------------------------------------------
# Equalities carrying assumption literals, not constants substituted at build time.
# Substitution is cheaper and makes "pinning is not exemption" automatic, but it
# destroys the ability to name the past as the source of a conflict -- the distinction
# between "the past itself is illegal" and "no legal future exists".


def _pin_past(built: Built, instance: Instance, incumbent: Roster) -> None:
    if instance.now is None or instance.incumbent is None:
        return

    model = built.model
    for open_shift in instance.open_shifts:
        day, shift = open_shift.day, open_shift.shift
        if not instance.is_past(day, shift):
            continue
        for employee in range(len(instance.employees)):
            key = (employee, day, shift)
            if key not in built.x:
                continue
            literal = built.gate(model, Gate("R-PIN-PAST", employee, day, shift))
            model.add(built.x[key] == int(key in incumbent)).only_enforce_if(literal)


# --- R-REST-GAP -------------------------------------------------------------------
# Pairwise <= 1 over the conflicting-pair set. At T1 sizes the pair set is small, and
# the encoding is transparently the object the spec describes. The interval/no-overlap
# alternative is a T2 study, not a T1 decision.


def _conflicting_pairs(instance: Instance) -> list[tuple[tuple[int, int], tuple[int, int]]]:
    minimum = instance.params.min_rest_hours
    slots = sorted(
        ((o.day, o.shift) for o in instance.open_shifts),
        key=lambda ds: instance.window(*ds).start,
    )
    pairs = []
    for index, first in enumerate(slots):
        end = instance.window(*first).end
        for second in slots[index + 1 :]:
            if instance.window(*second).start - end < minimum:
                pairs.append((first, second))
    return pairs


def _rest_gap(built: Built, instance: Instance) -> None:
    model = built.model
    minimum = instance.params.min_rest_hours

    for first, second in _conflicting_pairs(instance):
        for employee in range(len(instance.employees)):
            a, b = (employee, *first), (employee, *second)
            if a in built.x and b in built.x:
                literal = built.gate(model, Gate("R-REST-GAP", employee, second[0], second[1]))
                model.add(built.x[a] + built.x[b] <= 1).only_enforce_if(literal)

    # The horizon boundary is the zeroth element of the sequence, not a special case.
    for employee, person in enumerate(instance.employees):
        previous_end = person.last_shift_end_before_horizon
        if previous_end is None:
            continue
        for open_shift in instance.open_shifts:
            key = (employee, open_shift.day, open_shift.shift)
            if key not in built.x:
                continue
            if instance.window(open_shift.day, open_shift.shift).start - previous_end < minimum:
                literal = built.gate(
                    model, Gate("R-REST-GAP", employee, open_shift.day, open_shift.shift)
                )
                model.add(built.x[key] == 0).only_enforce_if(literal)


# --- R-WEEKLY-REST ----------------------------------------------------------------
# Candidate windows plus at-least-one. Anchoring candidates at shift ends is what makes
# this tractable: any feasible rest window can be slid later until its left edge meets
# the end of some shift without shrinking, so an anchored candidate exists whenever any
# window does. The candidate count is |O| + 1 -- no time discretisation, no chosen
# minute resolution.


def _weekly_rest(built: Built, instance: Instance) -> None:
    model = built.model
    width = instance.params.min_weekly_rest_hours
    horizon = instance.horizon()
    anchors = sorted(
        {horizon.start} | {instance.window(o.day, o.shift).end for o in instance.open_shifts}
    )

    for employee, person in enumerate(instance.employees):
        floor = horizon.start
        if person.last_shift_end_before_horizon is not None:
            floor = max(floor, person.last_shift_end_before_horizon)

        chosen = []
        for index, start in enumerate(anchors):
            if start < floor or start + width > horizon.end:
                continue
            selected = model.new_bool_var(f"r_{employee}_{index}")
            chosen.append(selected)
            for open_shift in instance.open_shifts:
                key = (employee, open_shift.day, open_shift.shift)
                if key not in built.x:
                    continue
                window = instance.window(open_shift.day, open_shift.shift)
                if window.start < start + width and start < window.end:
                    model.add(built.x[key] == 0).only_enforce_if(selected)

        literal = built.gate(model, Gate("R-WEEKLY-REST", employee))
        if chosen:
            model.add_bool_or(chosen).only_enforce_if(literal)
        else:
            # No window of this width fits the horizon at all. Forcing the gate false
            # reports that through the same channel rather than as a bare infeasibility.
            model.add(literal == 0)


# --- R-MAX-WEEKLY and R-MAX-DAILY -------------------------------------------------
# Net working time, not span. A missing budget is an input defect, so the constraint is
# omitted rather than defaulted -- this module must not invent a ceiling either.


def _max_weekly(built: Built, instance: Instance) -> None:
    model = built.model
    for employee, person in enumerate(instance.employees):
        if person.max_hours_this_week is None:
            continue
        terms = [
            _minutes(instance.shift_types[shift].work_hours) * built.x[e, day, shift]
            for (e, day, shift) in built.x
            if e == employee
        ]
        literal = built.gate(model, Gate("R-MAX-WEEKLY", employee))
        model.add(sum(terms) <= _minutes(person.max_hours_this_week)).only_enforce_if(literal)


def _max_daily(built: Built, instance: Instance) -> None:
    model = built.model
    for employee, person in enumerate(instance.employees):
        if person.max_daily_hours is None:
            continue
        per_day: dict[int, list] = defaultdict(list)
        for (e, day, shift) in built.x:
            if e == employee:
                per_day[day].append(
                    _minutes(instance.shift_types[shift].work_hours) * built.x[e, day, shift]
                )
        for day in sorted(per_day):
            literal = built.gate(model, Gate("R-MAX-DAILY", employee, day))
            model.add(sum(per_day[day]) <= _minutes(person.max_daily_hours)).only_enforce_if(
                literal
            )


# --- R-CONSEC-DAYS ----------------------------------------------------------------
# Sliding-window sums over a reified worked-day indicator. Windows start at -p rather
# than 0: an employee who worked the six days before Monday is out of days on Monday,
# and windows beginning at 0 silently grant a fresh streak. The `regular` automaton is
# the T2 alternative.


def _consec_days(built: Built, instance: Instance) -> None:
    limit = instance.params.max_consecutive_days
    if limit is None:
        return

    model = built.model
    for employee, person in enumerate(instance.employees):
        worked = {}
        for day in range(instance.days):
            same_day = [
                built.x[e, d, s] for (e, d, s) in built.x if e == employee and d == day
            ]
            indicator = model.new_bool_var(f"w_{employee}_{day}")
            if same_day:
                model.add_max_equality(indicator, same_day)
            else:
                model.add(indicator == 0)
            worked[day] = indicator

        prior = person.consecutive_days_worked_before_horizon
        for start in range(-prior, instance.days - limit):
            before = max(0, min(-start, limit + 1))
            inside = [worked[d] for d in range(max(0, start), min(start + limit + 1, instance.days))]
            if not inside:
                continue
            # Clamped: a prior streak already past the limit cannot be repaired by any
            # roster, so the tightest window forces rest rather than infeasibility.
            allowance = max(0, limit - min(before, limit))
            # The window's last day is the first that can breach it, which is the day
            # the checker names too -- the two readings must be comparable.
            literal = built.gate(model, Gate("R-CONSEC-DAYS", employee, max(0, start + limit)))
            model.add(sum(inside) <= allowance).only_enforce_if(literal)


# --- Solving ------------------------------------------------------------------------


@dataclass(frozen=True, slots=True)
class Solution:
    roster: Roster
    objective: int
    status: str
    shortfall: dict[tuple[int, int], int]


def solve(
    instance: Instance,
    *,
    seed: int = 7,
    time_limit: float = 30.0,
    workers: int = 1,
) -> Solution | list[Gate]:
    """Solve, or return the rule instances that make it impossible.

    A list of `Gate`s means infeasible: those are the rule instances in conflict, which
    is the shape the T4 explainer consumes.

    **Sufficient, not minimal.** CP-SAT's `sufficient_assumptions_for_infeasibility`
    returns a set that explains the infeasibility, and does not guarantee it is the
    smallest such set. `PLAN.md` describes T4's explainer as consuming a *minimal* core,
    which needs iterative deletion on top of this -- solve, drop a gate, re-solve, keep
    what remains necessary. That reduction belongs with the explainer rather than here,
    but the gap is real and should not be discovered then.
    """
    built = build(instance)
    model = built.model
    _objective(built, instance)

    solver = cp_model.CpSolver()
    solver.parameters.num_workers = workers
    solver.parameters.random_seed = seed
    solver.parameters.max_time_in_seconds = time_limit
    model.clear_assumptions()
    model.add_assumptions(built.literals)

    status = solver.solve(model)
    if status not in (cp_model.OPTIMAL, cp_model.FEASIBLE):
        return [
            built.gates[index]
            for index in solver.sufficient_assumptions_for_infeasibility()
            if index in built.gates
        ]

    roster = frozenset(key for key, var in built.x.items() if solver.value(var))
    return Solution(
        roster=roster,
        objective=round(solver.objective_value),
        status=solver.status_name(status),
        shortfall={k: solver.value(v) for k, v in built.shortfall.items()},
    )


def _objective(built: Built, instance: Instance) -> None:
    """Provisional. `replan.md` owns this and has not shipped D2 -- see the weights."""
    model = built.model
    terms = []

    # Historical shortfall is excluded: no replan can repair a shift that has started,
    # and leaving it in makes two runs with different `now` values incomparable.
    for (day, shift), slack in built.shortfall.items():
        if not instance.is_past(day, shift):
            terms.append(COVER_SHORTFALL_WEIGHT * slack)
    for (day, shift, _), slack in built.mix_shortfall.items():
        if not instance.is_past(day, shift):
            terms.append(MIX_SHORTFALL_WEIGHT * slack)

    if instance.incumbent is not None:
        # D0_PLACEHOLDER: a raw count of changed assignments, which `replan.md` rejects.
        for key, var in built.x.items():
            terms.append(DISRUPTION_WEIGHT * (1 - var if key in instance.incumbent else var))
    else:
        peak = model.new_int_var(0, len(instance.open_shifts), "peak")
        for employee in range(len(instance.employees)):
            model.add(peak >= sum(v for k, v in built.x.items() if k[0] == employee))
        terms.append(PEAK_WEIGHT * peak)

    model.minimize(sum(terms))


# --- The differential reporting surface ---------------------------------------------


def violations(roster: Roster, instance: Instance) -> list[Gate]:
    """Every hard rule instance this roster breaks, as the *model* sees it.

    A model that answers only `INFEASIBLE` can be differentially tested against a
    checker's feasibility bit and nothing more, and that comparison is the vacuous one.

    With every assignment fixed, each gate literal can be true exactly when its
    constraint holds, so maximising the number of true literals leaves precisely the
    violated constraints false. One solve enumerates them all -- as against a single
    minimal core, which explains one conflict and hides the rest.
    """
    built = build(instance)
    model = built.model

    for key, var in built.x.items():
        model.add(var == int(key in roster))
    model.maximize(sum(built.literals))

    solver = cp_model.CpSolver()
    solver.parameters.num_workers = 1
    status = solver.solve(model)
    if status not in (cp_model.OPTIMAL, cp_model.FEASIBLE):
        raise AssertionError(
            "a fully fixed roster left the model infeasible, which means some hard "
            "constraint is ungated -- every one of them must carry a literal"
        )

    broken = [
        built.gates[literal.index] for literal in built.literals if not solver.value(literal)
    ]

    # Presolved pairs never became variables, so an assignment to one can only be
    # reported from the exclusion table.
    for key in sorted(roster):
        for rule in built.excluded.get(key, ()):
            broken.append(Gate(rule, key[0], key[1], key[2]))

    return sorted(broken, key=lambda g: (g.rule, _nk(g.employee), _nk(g.day), _nk(g.shift)))


def _nk(value: int | None) -> int:
    return -1 if value is None else value
