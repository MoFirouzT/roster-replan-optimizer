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

from .disruption import objective_terms
from .domain import FLEXI, Instance, Roster

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


def build(
    instance: Instance,
    *,
    presolve: bool = True,
    symmetry: bool = False,
    sequence: str = "windows",
) -> Built:
    """The model, with every hard constraint instance gated.

    The three keyword arguments are **study switches, not supported modes**. Each selects an
    alternative encoding of the same problem so that `docs/studies/` can measure one against
    the other with everything else held. The shipped configuration is the default of each,
    and `studies/*.md` records why.

    `presolve=False` keeps a variable for every pair, including the impossible ones, and
    leaves them to the gated `x = 0` below. This costs only one branch because of `D-058`:
    a variable already has to exist for any pair the incumbent assigned, eligible or not,
    so the machinery for carrying an ineligible variable under a gate is already here.

    `symmetry=True` adds lexicographic ordering within groups of genuinely interchangeable
    employees. `sequence="automaton"` encodes `R-CONSEC-DAYS` as a `regular` automaton
    instead of sliding-window sums.

    Every variant must reach the same optimum. That is checked by `lab.agree` before any
    timing is reported, because a broken encoding is usually the fast one.
    """
    model = cp_model.CpModel()
    excluded = exclusions(instance)
    incumbent = instance.incumbent or frozenset()

    # A variable exists for every eligible pair, and additionally for any pair the
    # **incumbent** assigned, eligible or not. Two things need the second case:
    #
    #  - An already-illegal past must be representable, or "the past itself is illegal"
    #    is indistinguishable from a clean solve.
    #  - A deviation from the incumbent must be *countable*. An employee who became
    #    unavailable has to be dropped, and that drop is disruption. Without a variable
    #    the objective never sees it, and the model silently understates the cost of
    #    exactly the change the replan exists to make.
    keys = [
        (e, o.day, o.shift)
        for e in range(len(instance.employees))
        for o in instance.open_shifts
        if not presolve
        or (e, o.day, o.shift) not in excluded
        or (e, o.day, o.shift) in incumbent
    ]

    built = Built(
        model=model,
        x={k: model.new_bool_var(f"x_{k[0]}_{k[1]}_{k[2]}") for k in keys},
        shortfall={},
        overage={},
        mix_shortfall={},
        excluded=excluded,
    )

    # An ineligible pair that exists only to carry a pin or a deviation is still
    # ineligible. Gated rather than fixed outright, so that a roster which assigns one can
    # be *reported* by `violations()` instead of making the model infeasible.
    for key in keys:
        for rule in excluded.get(key, ()):
            literal = built.gate(model, Gate(rule, key[0], key[1], key[2]))
            model.add(built.x[key] == 0).only_enforce_if(literal)

    _cover(built, instance)
    _skill_mix(built, instance)
    _pin_past(built, instance, incumbent)
    _rest_gap(built, instance)
    _weekly_rest(built, instance)
    _max_weekly(built, instance)
    _max_daily(built, instance)
    if sequence == "automaton":
        _consec_days_automaton(built, instance)
    else:
        _consec_days(built, instance)
    if symmetry:
        _break_symmetry(built, instance)
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


# --- R-CONSEC-DAYS, as a `regular` automaton `[study only]` -------------------------
# The textbook encoding of a sequence rule, and `model.md` calls it a T2 study rather than
# a T1 assumption precisely so it has to earn the swap. See `studies/regular-constraint.md`.


def _worked_indicators(built: Built, instance: Instance, employee: int) -> dict[int, object]:
    """One boolean per day: did this employee work at all. Shared by both encodings, so
    the comparison is between the sequence constraints and nothing else."""
    model = built.model
    worked = {}
    for day in range(instance.days):
        same_day = [built.x[e, d, s] for (e, d, s) in built.x if e == employee and d == day]
        indicator = model.new_bool_var(f"w_{employee}_{day}")
        if same_day:
            model.add_max_equality(indicator, same_day)
        else:
            model.add(indicator == 0)
        worked[day] = indicator
    return worked


def _consec_days_automaton(built: Built, instance: Instance) -> None:
    """The same rule as a state machine over the week: state = current streak length.

    **It can be gated, but only per employee, and that is the trade.** An automaton does
    accept `only_enforce_if` and CP-SAT enforces it properly -- checked, not assumed, in
    `tests/test_studies.py`, because the API accepting a call is not evidence that it means
    anything. What changes is granularity. The sliding-window encoding carries one literal
    per (employee, window), so a violation is reported against the **day** the streak
    breached the limit -- the same coordinate the checker names. One automaton covers the
    whole week, so its literal can only say *this employee's week is wrong somewhere*.

    That is not a rounding error in reporting quality. `violations()` compares model gates
    against checker violations on the `(rule, employee, day, shift)` key, so an automaton
    gate with no day would not match its counterpart and the differential harness would
    have to be told about the exception. See `studies/regular-constraint.md`.
    """
    limit = instance.params.max_consecutive_days
    if limit is None:
        return

    model = built.model
    # State `s` means "s consecutive days worked, ending here". Working from the last
    # allowed state is what the rule forbids, so that transition simply does not exist.
    transitions = []
    for state in range(limit + 1):
        transitions.append((state, 0, 0))
        if state < limit:
            transitions.append((state, 1, state + 1))

    for employee, person in enumerate(instance.employees):
        worked = _worked_indicators(built, instance, employee)
        # A streak already past the limit before the horizon cannot be repaired by any
        # roster, so it is clamped rather than made infeasible -- the same clamp the
        # sliding-window encoding applies, and the two disagree without it.
        start = min(person.consecutive_days_worked_before_horizon, limit)
        # No day coordinate: one automaton covers the week, so this is the finest gate the
        # encoding admits. The window encoding names the breaching day.
        literal = built.gate(model, Gate("R-CONSEC-DAYS", employee, None))
        model.add_automaton(
            [worked[day] for day in range(instance.days)],
            start,
            list(range(limit + 1)),
            transitions,
        ).only_enforce_if(literal)


# --- Symmetry breaking `[study only]` -----------------------------------------------


def _orbits(instance: Instance) -> list[list[int]]:
    """Groups of employees that are genuinely interchangeable.

    Interchangeable means swapping them maps every legal roster to a legal roster **and
    leaves the objective unchanged**. The second half is what the incumbent destroys:
    disruption is measured against each person's own published row, so two otherwise
    identical people with different published shifts are not interchangeable at all, and a
    lexicographic constraint over them would cut off optima.

    Two employees therefore join an orbit only when every attribute the model reads matches
    *and* their incumbent rows match. `studies/symmetry-breaking.md` reports how often that
    happens, which is the number `model.md` asks for rather than assumes.
    """
    incumbent = instance.incumbent or frozenset()
    groups: dict[tuple, list[int]] = defaultdict(list)

    for index, person in enumerate(instance.employees):
        signature = (
            person.contract,
            tuple(sorted(person.skills)),
            tuple(sorted((i.start, i.end) for i in person.absences)),
            tuple(sorted((i.start, i.end) for i in person.unavailability)),
            person.max_hours_this_week,
            person.max_daily_hours,
            person.consecutive_days_worked_before_horizon,
            person.last_shift_end_before_horizon,
            tuple(sorted(person.flexi_eligible or ())),
            tuple(sorted(person.dimona_ok or ())),
            person.hourly_rate,
            tuple(sorted((d, s) for (e, d, s) in incumbent if e == index)),
        )
        groups[signature].append(index)

    return [sorted(members) for members in groups.values() if len(members) > 1]


def _break_symmetry(built: Built, instance: Instance) -> None:
    """Lexicographic ordering inside each orbit, on the assignment vector.

    Ungated on purpose: this is not a rule, it is a statement that one of several equally
    good rosters has been chosen arbitrarily, so there is nothing for an explainer to
    report and nothing a relaxation should restore.
    """
    slots = sorted({(o.day, o.shift) for o in instance.open_shifts})
    for orbit in _orbits(instance):
        for earlier, later in zip(orbit, orbit[1:]):
            _lexicographic(built, slots, earlier, later)


def _lexicographic(built: Built, slots, earlier: int, later: int) -> None:
    """`row(earlier) >= row(later)` read as a binary number, position by position.

    CP-SAT has no lexicographic primitive, so this is the standard prefix-equality chain:
    at each position the earlier row may only fall below the later one once some earlier
    position has already broken the tie.
    """
    model = built.model
    tied = model.new_bool_var(f"lex_{earlier}_{later}_0")
    model.add(tied == 1)

    for position, (day, shift) in enumerate(slots):
        a = built.x.get((earlier, day, shift))
        b = built.x.get((later, day, shift))
        if a is None or b is None:
            # Presolve removed one side, so the two rows already differ structurally and
            # the pair is not interchangeable in this model. Ordering them would cut optima.
            return

        model.add(a >= b).only_enforce_if(tied)
        following = model.new_bool_var(f"lex_{earlier}_{later}_{position + 1}")
        model.add_bool_and(following.negated()).only_enforce_if(tied.negated())
        model.add(a == b).only_enforce_if(following)
        model.add(a != b).only_enforce_if([tied, following.negated()])
        tied = following


# --- Solving ------------------------------------------------------------------------


@dataclass(frozen=True, slots=True)
class Solution:
    """`search_seconds` is CP-SAT's own wall time, and it is reported separately from
    whatever the caller measured around this function on purpose.

    At T2 sizes a solve is milliseconds and building the model in Python is a comparable
    number, so an end-to-end stopwatch is mostly measuring model construction -- which is
    identical for every method and would make four methods look equally fast for a reason
    that has nothing to do with any of them. End-to-end latency is the number T3's service
    owes a caller; this is the number that separates a search from another search.
    """

    roster: Roster
    objective: int
    status: str
    shortfall: dict[tuple[int, int], int]
    search_seconds: float = 0.0


def solve(
    instance: Instance,
    *,
    seed: int = 7,
    time_limit: float = 30.0,
    workers: int = 1,
    hint: Roster | None = None,
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

    `hint` is the warm start of `replan.md`, and it is a **separate argument from
    `instance.incumbent` on purpose**. The two are the same roster in the shipped replan,
    and keeping them one parameter would have made the T2 measurement impossible to
    state: the disruption objective and the hint are two independent reasons a replan
    beats a cold solve, and a benchmark that cannot solve with the objective and without
    the hint is measuring their sum.
    """
    built = build(instance)
    model = built.model
    _objective(built, instance)

    if hint is not None:
        # Every variable, not only the ones the hint sets. A partial hint states the adds
        # and leaves CP-SAT to guess the drops, which is the half of a repair that carries
        # the disruption.
        for key, var in built.x.items():
            model.add_hint(var, int(key in hint))

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
        search_seconds=solver.wall_time,
    )


def _objective(built: Built, instance: Instance) -> None:
    """Delegated to `disruption.py`, which owns the model's reading of `replan.md`."""
    built.model.minimize(
        sum(
            objective_terms(
                built.model, instance, built.x, built.shortfall, built.mix_shortfall
            )
        )
    )


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
