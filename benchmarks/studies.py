"""The level-1 model studies: presolve, symmetry, the `regular` automaton, and patterns.

    uv run python -m benchmarks.studies                # all of them
    uv run python -m benchmarks.studies --only presolve

Each asks whether one change to how the model is *expressed* -- never to what it means --
makes it cheaper. `lab.py` owns the measurement discipline; this module owns the
configurations and the two instance families they run over.

**Every study checks agreement before it reports a timing.** A variant that reaches a
different optimum is a broken encoding, not a fast one, and the broken encoding is usually
the fast one. `lab.agree` is called first, every time.

## Two instance families, because the committed set cannot answer one of the questions

The committed set is the distribution the project claims to serve, so it is where a lever's
value is decided. But a null over it has two possible causes -- the lever does nothing, or
the instances never present the structure the lever exploits -- and those are different
findings that a single number cannot tell apart.

So symmetry breaking also runs over `identical_workforce`, an instance built to contain the
structure: N employees with identical skills, contracts, budgets and availability. If a
lever does nothing there, it does nothing. If it works there and not on the committed set,
the committed set is the reason, and that is a statement about the distribution rather than
about the lever.

The fourth study is different in kind. Presolve, symmetry and the automaton are switches
inside one model, so `lab.compare` can pair them directly. Pattern/column variables are a
**second formulation** -- it lives in `patterns.py` and is compared end to end, including
the enumeration it needs before a model exists at all. Leaving that enumeration out of its
total would be the way to make it look competitive, so it is inside every number reported.

That study also runs twice, on the replan case and on the cold week, because the replan
case flatters it for a reason that has nothing to do with the formulation: `now` sits on
day 5, so five of seven days are pinned and there is almost nothing left to enumerate.
"""

from __future__ import annotations

import argparse
import dataclasses
import statistics
import time

from benchmarks import generator, lab, suite
from roster_replan.checker import check
from roster_replan.disruption import objective_terms
from roster_replan.domain import (
    DAYS_PER_WEEK,
    Employee,
    Instance,
    Interval,
    OpenShift,
    RuleParams,
    ShiftType,
    shipped_d2,
)
from roster_replan.model import _orbits, build, solve

# A sample rather than all 72: each study builds and solves every case several times under
# several configurations, and the committed set's classes are what vary the structure, not
# the seeds. Six seeds of the same class measure the same thing six times.
CASES = [f"{name}/0" for name in suite.CLASSES] + [f"{name}/1" for name in suite.CLASSES]

# The cold sample is **named, not sliced**. It used to be `CASES[:6]`, which is positional
# over a dict that people add classes to: inserting `busy` and `overloaded` (`D-105`) pushed
# `large/0` and `scarce-skill/0` out of it, and the symmetry study's cold count moved from 7
# interchangeable employees to 0 for that reason and no other. A sample that silently changes
# membership cannot be compared against its own previous run, and the drift reads exactly
# like a finding (`D-107`). These are the six the committed results were measured on.
COLD_SAMPLE = ("headline/0", "loose/0", "tight/0", "small/0", "large/0", "scarce-skill/0")


def _objective(built, instance: Instance) -> None:
    built.model.minimize(
        sum(
            objective_terms(
                built.model, instance, built.x, built.shortfall, built.mix_shortfall
            )
        )
    )


def _run(instances: dict[str, Instance], builder, *, repeats: int = 5) -> dict:
    return {
        name: lab.measure(instance, builder, objective=_objective, repeats=repeats)
        for name, instance in instances.items()
    }


def committed() -> dict[str, Instance]:
    return {case: suite.build(case).instance for case in CASES}


# --- An instance built to contain the structure symmetry breaking exploits -----------


def identical_workforce(employees: int = 12, *, required: int = 2) -> Instance:
    """N employees who are genuinely interchangeable, and a cold week to place them in.

    Deliberately unlike anything the generator produces: no unavailability, one skill, one
    contract, one budget. That is the point -- it isolates the lever from the question of
    whether the committed distribution ever presents symmetry.

    Cold, with no incumbent, because an incumbent destroys symmetry by construction: each
    person's disruption is measured against their own published row, so two people with
    different published shifts are not interchangeable however identical their contracts.
    """
    shift_types = (
        ShiftType(label="M", start_hour=7.0, span_hours=8.0, break_hours=0.5),
        ShiftType(label="E", start_hour=15.0, span_hours=8.0, break_hours=0.5),
    )
    people = tuple(
        Employee(
            name=f"E{index:02d}",
            contract="salaried",
            skills=frozenset({"bar"}),
            unavailability=(),
            absences=(),
            max_hours_this_week=38.0,
            max_daily_hours=8.0,
            consecutive_days_worked_before_horizon=0,
            last_shift_end_before_horizon=None,
        )
        for index in range(employees)
    )
    return Instance(
        days=7,
        shift_types=shift_types,
        employees=people,
        open_shifts=tuple(
            OpenShift(day=day, shift=shift, required=required)
            for day in range(7)
            for shift in range(2)
        ),
        params=RuleParams(
            min_rest_hours=11.0,
            min_weekly_rest_hours=35.0,
            min_period_hours=3.0,
            max_consecutive_days=6,
        ),
        disruption=shipped_d2(),
    )


def symmetric_family() -> dict[str, Instance]:
    return {f"identical-{n}": identical_workforce(n) for n in (8, 10, 12, 14, 16)}


# --- The studies --------------------------------------------------------------------


def presolve_study() -> None:
    instances = committed()
    print("\n" + "=" * 78)
    print("PRESOLVE -- removing impossible (employee, shift) pairs before the solver")
    print("=" * 78)

    control = _run(instances, lambda i: build(i, presolve=False))
    treatment = _run(instances, lambda i: build(i, presolve=True))
    _guard(control, treatment)
    lab.report("presolve on, against presolve off", control, treatment)

    kept = [treatment[c].variables / control[c].variables for c in instances]
    print(
        f"\nvariables kept: {100 * min(kept):.0f}% to {100 * max(kept):.0f}% "
        f"of the unpresolved model across {len(kept)} cases"
    )


def symmetry_study() -> None:
    print("\n" + "=" * 78)
    print("SYMMETRY BREAKING -- lexicographic ordering over interchangeable employees")
    print("=" * 78)

    committed_instances = committed()
    orbits = {
        name: sum(len(o) for o in _orbits(instance))
        for name, instance in committed_instances.items()
    }
    covered = sum(1 for count in orbits.values() if count)
    print(
        f"\ninterchangeable employees on the committed set: "
        f"{sum(orbits.values())} across {len(orbits)} cases, "
        f"{covered} of which have any at all"
    )

    cold = {
        name: dataclasses.replace(
            suite.build(name).base, disruption=suite.build(name).instance.disruption
        )
        for name in COLD_SAMPLE
    }
    cold_orbits = {name: sum(len(o) for o in _orbits(i)) for name, i in cold.items()}
    print(f"the same weeks solved cold, with no incumbent: {sum(cold_orbits.values())}")

    print("\n-- on the committed set --")
    control = _run(committed_instances, lambda i: build(i))
    treatment = _run(committed_instances, lambda i: build(i, symmetry=True))
    _guard(control, treatment)
    lab.report("symmetry breaking on, against off", control, treatment)

    print("\n-- on a workforce built to be interchangeable --")
    family = symmetric_family()
    for name, instance in family.items():
        print(f"   {name}: {sum(len(o) for o in _orbits(instance))} interchangeable employees")
    control = _run(family, lambda i: build(i))
    treatment = _run(family, lambda i: build(i, symmetry=True))
    _guard(control, treatment)
    lab.report("symmetry breaking on, against off", control, treatment)


def automaton_study() -> None:
    instances = committed()
    print("\n" + "=" * 78)
    print("REGULAR AUTOMATON -- R-CONSEC-DAYS as a state machine, not sliding windows")
    print("=" * 78)

    control = _run(instances, lambda i: build(i))
    treatment = _run(instances, lambda i: build(i, sequence="automaton"))
    _guard(control, treatment)
    lab.report("automaton, against sliding windows", control, treatment)

    family = symmetric_family()
    control = _run(family, lambda i: build(i))
    treatment = _run(family, lambda i: build(i, sequence="automaton"))
    _guard(control, treatment)
    lab.report("automaton, on the larger cold instances", control, treatment)


def pattern_study() -> None:
    """Pattern/column variables against assignment booleans, closing `D-009`.

    Run twice, because the replan case flatters the pattern formulation for a reason that
    has nothing to do with the formulation: `now` sits on day 5, so five of the seven days
    are pinned and there is almost nothing left to enumerate. The cold week is the same
    tenant with the whole horizon open, and it is the honest test of whether enumeration
    scales.
    """
    from roster_replan.model import solve as assignment_solve

    from benchmarks import patterns

    print("\n" + "=" * 78)
    print("PATTERN ENCODING -- one boolean per legal weekly pattern, against assignments")
    print("=" * 78)

    for label, pick in (
        ("replan (most of the week pinned)", lambda s: s.instance),
        ("cold (whole horizon open)", lambda s: dataclasses.replace(
            s.base, disruption=s.instance.disruption
        )),
    ):
        print(f"\n-- {label} --")
        print(
            f"{'case':20}{'patterns':>10}{'enum ms':>9}{'build ms':>10}{'search ms':>11}"
            f"{'total ms':>10}{'assignment ms':>15}{'':>4}"
        )
        for case in COLD_SAMPLE:
            scenario = suite.build(case)
            instance = pick(scenario)

            started = time.perf_counter()
            roster, objective, timing = patterns.solve_patterns(instance)
            pattern_total = 1000 * (time.perf_counter() - started)

            started = time.perf_counter()
            reference = assignment_solve(instance)
            assignment_total = 1000 * (time.perf_counter() - started)

            # "did not finish" and "finished with the wrong answer" are different results
            # and only one of them is about the formulation being incorrect. Reporting
            # both as a disagreement would hide the more interesting of the two.
            if timing["status"] != "OPTIMAL":
                verdict = f"NO PROOF ({timing['status']})"
            elif objective == reference.objective:
                verdict = "same"
            else:
                verdict = f"DISAGREES {objective} vs {reference.objective}"
            print(
                f"{case:20}{timing['patterns']:>10,}"
                f"{1000 * timing['enumerate_seconds']:>9.1f}"
                f"{1000 * timing['build_seconds']:>10.1f}"
                f"{1000 * timing['search_seconds']:>11.2f}"
                f"{pattern_total:>10.1f}{assignment_total:>15.1f}  {verdict}"
            )


# --- The tight week the gate study needs --------------------------------------------
# The committed set cannot answer the gate question either, and for the reason `D-105`
# already named: it is loose enough that the bound is easy to close whatever the model
# looks like. This week is not. Eight interchangeable staff, 37 slots, 34.7 net hours
# each against a 38-hour cap, so the weekly ceiling binds nearly everywhere.
#
# It is the fixture `tests/test_differential.py` builds, restated here rather than
# imported: `benchmarks` does not import `tests`, and a study whose instance lives in a
# test file is a study nobody can re-run from the command in its own write-up.


def tight_week() -> Instance:
    people = tuple(
        Employee(
            name=name,
            contract="salaried",
            skills=frozenset({"bar"}),
            max_hours_this_week=38.0,
            max_daily_hours=8.0,
        )
        for name in ("Ana", "Bram", "Chloe", "Driss", "Emma", "Finn", "Gita", "Hugo")
    )
    demand = {0: [2] * 7, 1: [2, 2, 2, 2, 2, 3, 3], 2: [1] * 7}
    return Instance(
        days=7,
        shift_types=(
            ShiftType("M", 7.0, 8.0, 0.5),
            ShiftType("E", 15.0, 8.0, 0.5),
            ShiftType("N", 23.0, 8.0, 0.5),
        ),
        employees=people,
        open_shifts=tuple(
            OpenShift(day=day, shift=shift, required=demand[shift][day])
            for day in range(7)
            for shift in (0, 1, 2)
        ),
        params=RuleParams(
            min_rest_hours=11.0,
            min_weekly_rest_hours=35.0,
            min_period_hours=3.0,
            max_consecutive_days=6,
        ),
        disruption=shipped_d2(metric="D3"),
    )


def tight_family() -> dict[str, Instance]:
    """The tight week as a replan, plus the seven relaxations of its own rules.

    The relaxations are the ones `tests/test_properties.py` uses for monotonicity. They
    are here because each one is a legal week a tenant could ask for, and three of them
    are where removing the gates stops proving optimality.
    """
    base = tight_week()
    solution = solve(base, seed=7)
    published = solution.roster
    sick = next(e for (e, d, s) in sorted(published) if d == 5)
    employees = list(base.employees)
    employees[sick] = dataclasses.replace(
        employees[sick], absences=(Interval(5 * 24.0, 6 * 24.0),)
    )
    instance = dataclasses.replace(
        base,
        employees=tuple(employees),
        incumbent=published,
        published_through=7 * 24.0,
        now=0.0,
    )

    def with_params(**changes):
        return dataclasses.replace(
            instance, params=dataclasses.replace(instance.params, **changes)
        )

    def with_everyone(**changes):
        return dataclasses.replace(
            instance,
            employees=tuple(dataclasses.replace(p, **changes) for p in instance.employees),
        )

    return {
        "base": instance,
        "shorter rest gap": with_params(min_rest_hours=instance.params.min_rest_hours - 4),
        "less weekly rest": with_params(min_weekly_rest_hours=24.0),
        "consecutive days off": with_params(max_consecutive_days=None),
        "more consecutive days": with_params(max_consecutive_days=7),
        "bigger weekly budget": with_everyone(max_hours_this_week=48.0),
        "bigger daily maximum": with_everyone(max_daily_hours=12.0),
        "absences lifted": with_everyone(absences=(), unavailability=()),
    }


def gate_study() -> None:
    """What the per-instance assumption literals cost, and what they buy.

    Two halves, and only the second one has a finding. On the committed set the ungated
    build is cheaper on both clocks and proves optimality everywhere, which reads as an
    overhead worth removing. On the tight week it stops proving optimality at all, so the
    literals turn out to be carrying search rather than only reporting (`D-153`).

    Reported per instance rather than as a ratio: the failures are statuses, and a median
    over a set where three members time out is a number about the time limit.
    """
    print("\n" + "=" * 78)
    print("GATES -- what the per-instance assumption literals cost, and what they buy")
    print("=" * 78)

    instances = committed()
    control = _run(instances, lambda i: build(i))
    treatment = _run(instances, lambda i: build(i, gated=False))
    _guard(control, treatment)
    lab.report("ungated, against the shipped gated build", control, treatment)

    print("\n  the tight week, phase one only, single worker, 30 s limit")
    print(f"  {'instance':<24} {'gated':>22}   {'ungated':>22}")
    for name, instance in tight_family().items():
        row = []
        for gated in (True, False):
            started = time.perf_counter()
            outcome = solve(instance, seed=7, time_limit=30.0, built=build(instance, gated=gated))
            elapsed = time.perf_counter() - started
            status = outcome.status if hasattr(outcome, "status") else type(outcome).__name__
            row.append(f"{status:>9} {elapsed:8.3f}s")
        flag = "  <-- lost the proof" if "OPTIMAL" not in row[1] else ""
        print(f"  {name:<24} {row[0]:>22}   {row[1]:>22}{flag}")


def rest_gap_study() -> None:
    """Pairwise inequalities against one `add_no_overlap` per employee.

    `guide/rules.md` deferred this to a study and said "measured there, not assumed here",
    which is a promise the repo had not kept. The pairwise set grows quadratically in the
    slots, so the interval form should win as the horizon grows -- and the horizon here is
    one week, which is exactly the regime where the naive form is cheapest.
    """
    instances = committed()
    print("\n" + "=" * 78)
    print("REST GAP -- one no_overlap per employee, against pairwise inequalities")
    print("=" * 78)

    control = _run(instances, lambda i: build(i))
    treatment = _run(instances, lambda i: build(i, rest="intervals"))
    _guard(control, treatment)
    lab.report("intervals, against pairwise", control, treatment)

    family = symmetric_family()
    control = _run(family, lambda i: build(i))
    treatment = _run(family, lambda i: build(i, rest="intervals"))
    _guard(control, treatment)
    lab.report("intervals, on the larger cold instances", control, treatment)


def coverage_study() -> None:
    """How often a hard coverage floor would answer "infeasible" instead of answering.

    The evidence `D-008` needs. `R-COVER` ships as a hard ceiling and a soft floor, and
    `D-018` argued that from first principles -- a disruption often has no legal
    repair, and *one short on Saturday, here is what it costs* is what a planner can act
    on. That argument is sound and was never measured. This measures it: force every
    non-historical shortfall to zero and count how many of the committed cases stop having
    an answer at all.
    """
    from ortools.sat.python import cp_model

    print("\n" + "=" * 78)
    print("COVERAGE FLOOR -- what a hard floor would refuse to answer")
    print("=" * 78)

    refused = []
    already_short = []
    for case in suite.case_names():
        scenario = suite.build(case)
        instance = scenario.instance

        built = build(instance)
        _objective(built, instance)
        for (day, shift), slack in built.shortfall.items():
            if not instance.is_past(day, shift):
                built.model.add(slack == 0)

        built.model.clear_assumptions()
        built.model.add_assumptions(built.literals)
        solver = cp_model.CpSolver()
        solver.parameters.num_workers = 1
        solver.parameters.random_seed = 7
        solver.parameters.max_time_in_seconds = 30.0

        if solver.solve(built.model) not in (cp_model.OPTIMAL, cp_model.FEASIBLE):
            refused.append(case)
            if scenario.base_shortfall:
                already_short.append(case)

    total = len(suite.case_names())
    print(f"\ncases a hard floor could not answer: {len(refused)}/{total}")
    print(f"  of those, already short before the event: {len(already_short)}")
    print(f"  fully staffable before the event: {len(refused) - len(already_short)}")
    by_class: dict[str, int] = {}
    for case in refused:
        name = case.partition("/")[0]
        by_class[name] = by_class.get(name, 0) + 1
    for name in sorted(by_class, key=lambda k: -by_class[k]):
        print(f"    {name:20}{by_class[name]}/6")


# --- The horizon --------------------------------------------------------------------
# Different in kind from the four above. Those compare two encodings of one problem; this
# compares two *problems* -- a longer horizon against several short ones -- because that is
# the shape of the claim `guide/rules.md` makes without a measurement behind it (`D-116`).


def _week_slice(instance: Instance, week: int, carried: dict) -> Instance:
    """Week `week` of `instance` as a standalone seven-day instance.

    This is the study playing the caller `internals/model.md` describes: the boundary fields are
    exactly what a caller solving one week at a time would have to compute from the week
    before, and getting them wrong is how a chained solve would flatter itself.
    """
    offset = week * DAYS_PER_WEEK
    shifts = tuple(
        dataclasses.replace(o, day=o.day - offset)
        for o in instance.open_shifts
        if instance.week_of(o.day) == week
    )
    people = tuple(
        dataclasses.replace(
            person,
            consecutive_days_worked_before_horizon=carried.get(index, (0, None))[0],
            last_shift_end_before_horizon=carried.get(index, (0, None))[1],
            unavailability=tuple(
                Interval(i.start - offset * 24.0, i.end - offset * 24.0)
                for i in person.unavailability
            ),
            flexi_eligible=(
                None
                if person.flexi_eligible is None
                else frozenset(d - offset for d in person.flexi_eligible if d // DAYS_PER_WEEK == week)
            ),
            dimona_ok=(
                None
                if person.dimona_ok is None
                else frozenset(d - offset for d in person.dimona_ok if d // DAYS_PER_WEEK == week)
            ),
        )
        for index, person in enumerate(instance.employees)
    )
    return dataclasses.replace(
        instance, days=DAYS_PER_WEEK, open_shifts=shifts, employees=people
    )


def _carry(instance: Instance, roster, week: int) -> dict:
    """What each employee takes into the next week: the trailing run of worked days, and
    when their last shift ended, stated negatively as `internals/model.md` requires."""
    end_of_week = (week + 1) * DAYS_PER_WEEK
    carried = {}
    for index in range(len(instance.employees)):
        days = sorted({d for (e, d, _) in roster if e == index})
        streak = 0
        for day in range(end_of_week - 1, -1, -1):
            if day in days:
                streak += 1
            else:
                break
        ends = [
            instance.window(d, s).end for (e, d, s) in roster if e == index
        ]
        last = max(ends) - end_of_week * 24.0 if ends else None
        carried[index] = (streak, last)
    return carried


def horizon_study() -> None:
    """The two halves of a claim `guide/rules.md` makes by assertion.

    *"The obvious fix is to extend the solve horizon to the reference period. That is
    rejected: it multiplies instance size by an order of magnitude and destroys the
    interactive latency the whole service is built around."*

    **Cost** is the first table: model size and both clocks at one, two and four weeks.
    **Benefit** is the second: four weeks solved at once, against the same four weeks
    solved one at a time with the boundary state carried between them, which is what the
    service does today. A longer horizon is worth its cost only if it buys coverage the
    chained solve cannot reach.
    """
    print("\n" + "=" * 78)
    print("HORIZON -- what a longer one costs, and what it buys")
    print("=" * 78)

    seeds = (0, 1, 2)
    print(f"\n{'days':>5} {'slots':>6} {'vars':>7} {'cons':>7} {'build ms':>9} {'search ms':>10}")
    for days in (7, 14, 28):
        rows = []
        for seed in seeds:
            scenario = generator.generate(seed, generator.ScenarioParams(days=days))
            instance = scenario.instance
            started = time.perf_counter()
            built = build(instance)
            build_ms = 1000 * (time.perf_counter() - started)
            answer = solve(instance, built=built, time_limit=30.0)
            rows.append(
                (
                    len(instance.open_shifts),
                    len(built.model.proto.variables),
                    len(built.model.proto.constraints),
                    build_ms,
                    1000 * answer.search_seconds,
                )
            )
        median = [statistics.median(column) for column in zip(*rows)]
        print(
            f"{days:>5} {median[0]:>6.0f} {median[1]:>7.0f} {median[2]:>7.0f} "
            f"{median[3]:>9.1f} {median[4]:>10.1f}"
        )

    # Both ends of the coverage axis, for `D-105`'s reason: on a slack month both methods
    # staff everything and the comparison cannot say anything, so the tight setting is
    # where the answer is allowed to change.
    print(f"\n{'ratio':>6} {'seed':>5} {'one solve':>21} {'four chained':>21}")
    print(f"{'':>6} {'':>5} {'short':>9} {'search ms':>11} {'short':>9} {'search ms':>11}")
    for ratio in (0.70, 0.90):
        for seed in seeds:
            scenario = generator.generate(
                seed, generator.ScenarioParams(days=28, demand_ratio=ratio)
            )
            whole = scenario.base

            single = solve(whole, time_limit=30.0)
            chained_short, chained_ms = 0, 0.0
            stitched: set = set()
            carried: dict = {}
            for week in range(4):
                part = _week_slice(whole, week, carried)
                answer = solve(part, time_limit=30.0)
                chained_short += sum(answer.shortfall.values())
                chained_ms += 1000 * answer.search_seconds
                stitched |= {
                    (e, d + week * DAYS_PER_WEEK, s) for (e, d, s) in answer.roster
                }
                carried = _carry(part, answer.roster, 0)

            # The guard this study needs, and the analogue of `_guard` above. The chained
            # arm is only a fair comparison if its four weeks stitch back into a roster
            # that is legal over the whole month -- if the boundary state is carried
            # wrongly, the weekly solves are cheating across a seam nobody is checking.
            # Asked of the independent reading, so a mistake here contradicts the checker
            # rather than agreeing with the code that made it.
            illegal = [v for v in check(frozenset(stitched), whole) if not v.soft]
            if illegal:
                raise AssertionError(
                    f"the chained solve stitches into an illegal month at ratio {ratio}, "
                    f"seed {seed}: {illegal[:3]} -- the carried boundary state is wrong, "
                    f"so its coverage is not comparable with the single solve's"
                )
            print(
                f"{ratio:>6.2f} {seed:>5} {sum(single.shortfall.values()):>9} "
                f"{1000 * single.search_seconds:>11.1f} "
                f"{chained_short:>9} {chained_ms:>11.1f}"
            )

    # The third arm, and the question `guide/rules.md` is actually about (`D-123`). Both arms
    # above hold the same weekly ceiling, so what they compare is horizon *length*. A
    # caller resolving a rolling quarter supplies a pool as well as a rate, and the pool is
    # the thing a chained weekly solve cannot spend unevenly. Here the same total hours are
    # given two ways: as a pooled remainder the four-week solve may spend as it likes, and
    # as the flat weekly ceiling a chained solve is stuck with.
    print(f"\n{'ratio':>6} {'seed':>5} {'pooled: short':>14} {'uneven weeks':>13} "
          f"{'flat: short':>12}")
    for ratio in (0.70, 0.90):
        for seed in seeds:
            scenario = generator.generate(
                seed, generator.ScenarioParams(days=28, demand_ratio=ratio)
            )
            whole = scenario.base
            weeks = whole.weeks

            # The pool is exactly what the flat ceiling would have allowed in total, so the
            # two arms are given the same hours and differ only in how freely they spend.
            pooled = dataclasses.replace(
                whole,
                employees=tuple(
                    dataclasses.replace(
                        person,
                        max_hours_this_period=(person.max_hours_this_week or 0.0) * weeks,
                    )
                    for person in whole.employees
                ),
            )
            answer = solve(pooled, time_limit=30.0)
            flat = solve(whole, time_limit=30.0)

            worked: dict[tuple[int, int], float] = {}
            for employee, day, shift in answer.roster:
                key = (employee, pooled.week_of(day))
                worked[key] = worked.get(key, 0.0) + pooled.shift_types[shift].work_hours
            spread = {
                employee: {w for (e, w) in worked if e == employee}
                for employee in range(len(pooled.employees))
            }
            uneven = sum(
                1
                for employee, weeks_worked in spread.items()
                if len({round(worked[employee, w], 2) for w in weeks_worked}) > 1
            )
            print(
                f"{ratio:>6.2f} {seed:>5} {sum(answer.shortfall.values()):>14} "
                f"{uneven:>13} {sum(flat.shortfall.values()):>12}"
            )


def _guard(control: dict, treatment: dict) -> None:
    """No timing is reported until the two configurations agree about the answer."""
    disagreed = lab.agree(control, treatment)
    if disagreed:
        raise AssertionError(
            f"the two encodings reached different optima on {disagreed} -- that is a bug "
            f"in an encoding, not a result about one"
        )


STUDIES = {
    "presolve": presolve_study,
    "symmetry": symmetry_study,
    "automaton": automaton_study,
    "patterns": pattern_study,
    "coverage": coverage_study,
    "rest-gap": rest_gap_study,
    "gates": gate_study,
    "horizon": horizon_study,
}


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--only", choices=sorted(STUDIES), nargs="*", default=None)
    args = parser.parse_args()
    for name in args.only or STUDIES:
        STUDIES[name]()
