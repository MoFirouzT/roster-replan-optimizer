"""Break the code on purpose, and check the right layer notices.

    uv run python -m tests.mutation
    uv run python -m tests.mutation --list
    uv run python -m tests.mutation -k rest-gap

Every run writes its verdict to `tests/mutation-report.json` as well as to stdout, and the
report is the copy to trust. Reading its result through a pipe has twice destroyed it: `tail`
truncates the per-mutant lines and reports *its own* exit status, so a run that leaked a
mutated file into the working tree read as a clean pass.
`jq .verdict tests/mutation-report.json` answers the only question that matters first.

**A full run is about 14 minutes** -- 13m50s for all 132 mutants on 2026-08-17, in the default
catcher-only mode. It was 9m27s for 103 before `D-141` added bytecode invalidation; recompiling each
mutated file is the price of a size-neutral mutation being visible to the interpreter at all. `--full` is a different and much longer question. That number is in the
report as `duration_seconds`, because until it was there every estimate in circulation was a
guess: this file said "tens of minutes", and a guess of 100 went unchallenged for want of a
single recorded figure.

Four verdicts, in the order they outrank each other (`D-112`):

    leaked        a mutation was left in the tree. The run is void, not caveated
    survivors     a mutant nothing objected to. A hole in the layer that claims that ground
    unverifiable  every mutant caught, and the run cannot vouch for the tree it ran in --
                  a target file was already modified, or an editor wrote back late
    clean         every mutant caught by the layer named to catch it, tree verified

`unverifiable` exists because the alternative was a lie the harness had already told: `clean`,
`trustworthy: true`, and a mutated `checker.py` in the tree, with the reason named three fields
lower in the same object.

`CLAUDE.md`: *a layer that has never been shown to fail is not known to work.* This module
is that claim, executable. It edits a source file in place, runs the tests that ought to
object, restores the file, and reports.

**Each mutant names the layer expected to catch it**, and a mutant caught only by some
other layer is reported as a miss rather than a pass. That distinction is the point. Every
mutant here would be "caught" by running the whole suite, which would say nothing about
whether the ground-truth layer can see a wrong threshold or whether the golden record can
see a reweighted objective. Those are different claims and they are tested separately.

The pair around the notice multiplier is the clearest illustration and is kept for that
reason. Dropping it from *one* reading is a disagreement between two readings, so
brute-force stage (b) catches it. Dropping it from *both* leaves the readings agreeing
perfectly about a different answer -- invisible to stage (b), by construction, and caught
only by the committed numbers in the golden record. That is `D-067` stated as a test rather
than as prose.

**Not part of the normal suite.** It rewrites source files, so it is run deliberately -- when
a test layer is added, or when one is about to be trusted.
"""

from __future__ import annotations

import argparse
import dataclasses
import datetime
import json
import pathlib
import subprocess
import sys
import time

_HERE = pathlib.Path(__file__).resolve().parent
for _path in (_HERE, _HERE.parent):
    if str(_path) not in sys.path:
        sys.path.insert(0, str(_path))

ROOT = _HERE.parent


@dataclasses.dataclass(frozen=True, slots=True)
class Mutant:
    """One deliberate defect, and the layer whose job it is to object.

    `catcher` is a pytest target. Running only that target is what makes the harness
    affordable, and it is also what makes the result mean something: the question is not
    whether *anything* fails, it is whether the layer that claims this ground can see it.
    """

    name: str
    layer: str
    path: str
    old: str
    new: str
    catcher: str

    def target(self) -> pathlib.Path:
        return ROOT / self.path


CHECKER = "roster_replan/checker.py"
MODEL = "roster_replan/model.py"
DISRUPTION = "roster_replan/disruption.py"
SCORING = "roster_replan/scoring.py"
VALIDATION = "roster_replan/validation.py"
GENERATOR = "benchmarks/generator.py"
SUITE = "benchmarks/suite.py"
METHODS = "benchmarks/methods.py"
GREEDY = "roster_replan/repair.py"
METRIC_STUDY = "benchmarks/metrics.py"
PATTERNS = "benchmarks/patterns.py"
LADDER = "roster_replan/ladder.py"
JOBS = "roster_replan/service/jobs.py"
MILP = "benchmarks/milp.py"
ANNEAL = "benchmarks/anneal.py"
ANNEAL_STUDY = "benchmarks/anneal_study.py"
WEIGHTS = "benchmarks/weights.py"
EXPLAIN = "roster_replan/explain.py"
PROSE = "roster_replan/prose.py"
WHATIF = "roster_replan/whatif.py"
PROFILE = "roster_replan/profile.py"
CORE = "roster_replan/core.py"
CONTRACTS = "roster_replan/service/contracts.py"
DOMAIN = "roster_replan/domain.py"
NL = "roster_replan/nl.py"
NL_EVAL = "benchmarks/nl_eval.py"
FOREIGN = "benchmarks/foreign.py"
FIGURE = "benchmarks/figure.py"

# A mutant whose defect was gone by the time the tests ran. Not a survivor and not a
# catch: nothing was tested, and the run cannot vouch for the file (`D-139`).
REVERTED = "the mutation was reverted before the tests ran, so nothing was tested"

MUTANTS: tuple[Mutant, ...] = (
    # --- Rule thresholds ------------------------------------------------------------
    # `D-066`: a fixture set proves a rule exists; only a fixture at the boundary proves
    # it is enforced at the right number. These are the mutants that were live once.
    Mutant(
        "checker-rest-gap-threshold",
        "checker",
        CHECKER,
        "    minimum = instance.params.min_rest_hours",
        "    minimum = instance.params.min_rest_hours - 2.0",
        "tests/test_ground_truth.py",
    ),
    Mutant(
        "checker-weekly-rest-threshold",
        "checker",
        CHECKER,
        "    minimum = instance.params.min_weekly_rest_hours",
        "    minimum = instance.params.min_weekly_rest_hours - 2.0",
        "tests/test_ground_truth.py",
    ),
    Mutant(
        "checker-weekly-budget-slack",
        "checker",
        CHECKER,
        "        if worked > person.max_hours_this_week:",
        "        if worked > person.max_hours_this_week + 1.0:",
        "tests/test_ground_truth.py",
    ),
    Mutant(
        "checker-daily-maximum-slack",
        "checker",
        CHECKER,
        "            if per_day[day] > person.max_daily_hours:",
        "            if per_day[day] > person.max_daily_hours + 1.0:",
        "tests/test_ground_truth.py",
    ),
    Mutant(
        "checker-period-budget-never-binds",
        "checker",
        CHECKER,
        "        if person.max_hours_this_period is None:",
        "        if True:",
        "tests/test_differential.py",
    ),
    Mutant(
        "model-period-budget-never-binds",
        "model",
        MODEL,
        "        if person.max_hours_this_period is None:",
        "        if True:",
        "tests/test_differential.py",
    ),
    Mutant(
        "checker-weekly-rest-spans-the-horizon",
        "checker",
        CHECKER,
        "            span = instance.week_span(week)",
        "            span = instance.horizon()",
        "tests/test_differential.py",
    ),
    Mutant(
        "checker-weekly-budget-spans-the-horizon",
        "checker",
        CHECKER,
        "                if instance.week_of(d) == week",
        "                if True",
        "tests/test_differential.py",
    ),
    Mutant(
        "checker-consecutive-days-off-by-one",
        "checker",
        CHECKER,
        "            if streak > limit and not reported:",
        "            if streak > limit + 1 and not reported:",
        "tests/test_ground_truth.py",
    ),
    # This one survived the differential layer on its first run, and the fix was a
    # missing fixture rather than a wrong expectation: `micro()` opened mornings only,
    # so every gap it could produce was 24h and no roster distinguished an 11-hour
    # threshold from a 9-hour one. `bracketing()` now puts a 10-hour gap in reach.
    Mutant(
        "model-rest-gap-threshold",
        "model",
        MODEL,
        "def _conflicting_pairs(instance: Instance) -> list[tuple[tuple[int, int], tuple[int, int]]]:\n    minimum = instance.params.min_rest_hours",
        "def _conflicting_pairs(instance: Instance) -> list[tuple[tuple[int, int], tuple[int, int]]]:\n    minimum = instance.params.min_rest_hours - 2.0",
        "tests/test_differential.py",
    ),
    Mutant(
        "model-consecutive-days-allowance",
        "model",
        MODEL,
        "            allowance = max(0, limit - min(before, limit))",
        "            allowance = max(0, limit + 1 - min(before, limit))",
        "tests/test_differential.py",
    ),
    # `D-111`. Both readings scoped the week rules to the horizon, and neither the
    # differential harness nor brute force could see it, because they were wrong in the
    # same direction. These two mutants are that defect restored, one reading at a time,
    # so the layer that could not catch it before is shown catching it now.
    Mutant(
        "model-weekly-rest-spans-the-horizon",
        "model",
        MODEL,
        "            span = instance.week_span(week)",
        "            span = instance.horizon()",
        "tests/test_differential.py",
    ),
    Mutant(
        "model-weekly-budget-spans-the-horizon",
        "model",
        MODEL,
        "                if e == employee and instance.week_of(day) == week",
        "                if e == employee",
        "tests/test_differential.py",
    ),
    # --- The objective --------------------------------------------------------------
    Mutant(
        "model-publication-weights-swapped",
        "disruption",
        DISRUPTION,
        "        params.published_weight if instance.is_published(day, shift) else params.draft_weight",
        "        params.draft_weight if instance.is_published(day, shift) else params.published_weight",
        "tests/test_ground_truth.py",
    ),
    Mutant(
        "model-notice-multiplier-dropped",
        "disruption",
        DISRUPTION,
        "    return publication * params.notice_multiplier(instance.notice_hours(day, shift))",
        "    return publication",
        "tests/test_ground_truth.py",
    ),
    Mutant(
        "scorer-notice-multiplier-dropped",
        "scoring",
        SCORING,
        "    return publication * params.notice_multiplier(instance.notice_hours(day, shift))",
        "    return publication",
        "tests/test_ground_truth.py",
    ),
    # --- The blind spot the golden layer exists for ---------------------------------
    # Both readings reweighted the same way. Stage (b) compares them against each other,
    # so it sees nothing; only committed numbers can (`D-067`).
    Mutant(
        "both-readings-reweighted",
        "objective",
        DOMAIN,
        "        published_weight=10,",
        "        published_weight=12,",
        "tests/test_golden.py",
    ),
    # --- Input validation -----------------------------------------------------------
    Mutant(
        "validation-domination-bound-never-fires",
        "validation",
        VALIDATION,
        "    if params.shortfall_weight > bound:",
        "    if True:",
        "tests/test_validation.py",
    ),
    Mutant(
        "validation-missing-budget-accepted",
        "validation",
        VALIDATION,
        "        if person.max_hours_this_week is None:",
        "        if False:",
        "tests/test_validation.py",
    ),
    Mutant(
        "validation-part-week-horizon-accepted",
        "validation",
        VALIDATION,
        "    if instance.days <= DAYS_PER_WEEK or instance.days % DAYS_PER_WEEK == 0:",
        "    if True:",
        "tests/test_validation.py",
    ),
    # --- The generator --------------------------------------------------------------
    Mutant(
        "generator-seed-not-threaded",
        "generator",
        GENERATOR,
        "    rng = random.Random(seed)",
        "    rng = random.Random(0)",
        "tests/test_generator.py",
    ),
    Mutant(
        "generator-loose-week-forced-full-grid",
        "generator",
        GENERATOR,
        "    slots = max(1, round(capacity * params.demand_ratio / WORK_HOURS))",
        "    slots = max(len(_grid()), round(capacity * params.demand_ratio / WORK_HOURS))",
        "tests/test_generator.py",
    ),
    Mutant(
        "generator-tightness-counts-bodies",
        "generator",
        GENERATOR,
        "            if (employee, open_shift.day, open_shift.shift) not in excluded",
        "            if True",
        "tests/test_generator.py",
    ),
    Mutant(
        "generator-sick-call-as-preference",
        "generator",
        GENERATOR,
        "        return _absences(rng, instance, incumbent, count=1, declared=False)\n    if params.event == MULTI_ABSENCE:",
        "        return _absences(rng, instance, incumbent, count=1, declared=True)\n    if params.event == MULTI_ABSENCE:",
        "tests/test_generator.py",
    ),
    Mutant(
        "generator-event-strikes-the-pinned-past",
        "generator",
        GENERATOR,
        "        key for key in incumbent if not instance.is_past(key[1], key[2])",
        "        key for key in incumbent",
        "tests/test_generator.py",
    ),
    Mutant(
        "generator-demand-spike-does-nothing",
        "generator",
        GENERATOR,
        "            dataclasses.replace(o, required=o.required + 1) if o is target else o",
        "            o if o is target else o",
        "tests/test_generator.py",
    ),
    Mutant(
        "generator-scarce-skill-never-required",
        "generator",
        GENERATOR,
        "            if shift == EVENING and holders",
        "            if False",
        "tests/test_generator.py",
    ),
    # --- The committed set ----------------------------------------------------------
    Mutant(
        "suite-loose-class-closes-no-slots",
        "suite",
        SUITE,
        '"loose": _vary(demand_ratio=0.35),',
        '"loose": _vary(demand_ratio=0.70),',
        "tests/test_suite.py",
    ),
    Mutant(
        "suite-tightness-axis-collapsed",
        "suite",
        SUITE,
        '"tight": _vary(demand_ratio=0.90),',
        '"tight": _vary(demand_ratio=0.70),',
        "tests/test_suite.py",
    ),
    Mutant(
        "suite-incumbent-fingerprint-copied",
        "suite",
        SUITE,
        '"incumbent": _digest(sorted(scenario.incumbent)),',
        '"incumbent": _digest(scenario.base),',
        "tests/test_suite.py",
    ),
    Mutant(
        "suite-version-bumped-without-regenerating",
        "suite",
        SUITE,
        "GENERATOR_VERSION = 1",
        "GENERATOR_VERSION = 2",
        "tests/test_suite.py",
    ),
    Mutant(
        "suite-class-dropped",
        "suite",
        SUITE,
        '"withdrawal": _vary(event=AVAILABILITY_WITHDRAWAL),',
        "",
        "tests/test_suite.py",
    ),
    Mutant(
        "suite-damage-always-zero",
        "suite",
        SUITE,
        "    return broken + added",
        "    return 0",
        "tests/test_suite.py",
    ),
    Mutant(
        "suite-base-week-depends-on-event",
        "suite",
        GENERATOR,
        "    rng = random.Random(seed)",
        "    rng = random.Random(seed + len(params.event))",
        "tests/test_suite.py",
    ),
    # --- The method comparison ------------------------------------------------------
    # A benchmark harness fails silently by construction: a wrong method still returns a
    # roster, still finishes in milliseconds, and still fills a table. These four are the
    # ways it could produce a flattering number without producing an error.
    #
    # The first is the one worth naming. A hint is a search suggestion, and the natural
    # mistake is to implement it as a constraint -- which would make every warm-started
    # replan return the best roster that *keeps the damage*, report it as the optimum, and
    # look fast doing it.
    Mutant(
        "methods-hint-implemented-as-a-constraint",
        "methods",
        MODEL,
        "            model.add_hint(var, int(key in hint))",
        "            model.add(var == int(key in hint))",
        "tests/test_methods.py",
    ),
    # Greedy's two defences of the pinned past are not equal, and the harness is what
    # found that out. Deleting the `is_past` skip in `repair` survives -- `_legal` refuses
    # a past slot anyway, because adding one is a `R-PIN-PAST` violation the checker
    # names. So that skip is a statement of intent and a saving, not a defence, and the
    # mutant that matters is the one on the other side: dropping an assignment the past
    # pins.
    Mutant(
        "methods-greedy-drops-a-pinned-past-assignment",
        "methods",
        GREEDY,
        "        and not instance.is_past(v.day, v.shift)",
        "        and not v.historical",
        "tests/test_methods.py",
    ),
    Mutant(
        "methods-greedy-calls-anyone",
        "methods",
        GREEDY,
        "    return not (after - before)",
        "    return True",
        "tests/test_methods.py",
    ),
    Mutant(
        "methods-cost-baseline-still-prices-deviation",
        "methods",
        METHODS,
        "        published_weight=0,",
        "        published_weight=params.published_weight,",
        "tests/test_methods.py",
    ),
    # --- The D0-D4 study ------------------------------------------------------------
    # This study fails towards a flattering answer. Every defect below makes the five
    # metrics look like they agree, which is the conclusion that requires no evidence --
    # so a green run of the study proves nothing until these are shown to be caught.
    Mutant(
        "metrics-lexicographic-hold-dropped",
        "metrics",
        METRIC_STUDY,
        "    built.model.add(sum(_terms(built, instance, hold)) == held_at)",
        "    built.model.add(sum(_terms(built, instance, hold)) >= 0)",
        "tests/test_metrics.py",
    ),
    Mutant(
        "metrics-gates-left-unasserted",
        "metrics",
        METRIC_STUDY,
        "    built.model.add_assumptions(built.literals)",
        "    built.model.clear_assumptions()",
        "tests/test_metrics.py",
    ),
    Mutant(
        "metrics-swap-does-not-swap",
        "metrics",
        METRIC_STUDY,
        "    return dataclasses.replace(instance, disruption=dataclasses.replace(params, metric=metric))",
        "    return instance",
        "tests/test_metrics.py",
    ),
    # --- The level-1 model studies --------------------------------------------------
    # Every defect here produces a *faster* variant, which is the direction that gets
    # written up. An encoding that drops a constraint, a symmetry that is not one, a
    # pattern catalogue missing an option: all three solve quicker and answer a different
    # question, and no timing would show it.
    Mutant(
        "studies-automaton-drops-the-prior-streak",
        "studies",
        MODEL,
        "        start = min(person.consecutive_days_worked_before_horizon, limit)",
        "        start = 0",
        "tests/test_studies.py",
    ),
    Mutant(
        "studies-orbits-ignore-the-incumbent",
        "studies",
        MODEL,
        "            tuple(sorted((d, s) for (e, d, s) in incumbent if e == index)),",
        "            (),",
        "tests/test_studies.py",
    ),
    Mutant(
        "studies-presolve-flag-does-nothing",
        "studies",
        MODEL,
        "        if not presolve\n        or (e, o.day, o.shift) not in excluded",
        "        if (e, o.day, o.shift) not in excluded",
        "tests/test_studies.py",
    ),
    Mutant(
        "studies-patterns-miss-a-legal-option",
        "studies",
        PATTERNS,
        "    choices: list[tuple] = [()]",
        "    choices: list[tuple] = []",
        "tests/test_studies.py",
    ),
    Mutant(
        "studies-rest-intervals-not-inflated",
        "studies",
        MODEL,
        "                    _minutes(window.end - window.start) + minutes,",
        "                    _minutes(window.end - window.start),",
        "tests/test_studies.py",
    ),
    # --- The fallback ladder ---------------------------------------------------------
    # Every rung here is unreachable in normal operation -- nothing in the committed set
    # takes more than 12.4 ms -- so these mutants are the only thing standing between the
    # lower rungs and shipping on the strength of a code review.
    Mutant(
        "ladder-timeout-reported-as-infeasible",
        "ladder",
        MODEL,
        "        if status != cp_model.INFEASIBLE:\n            return Unproven(",
        "        if False:\n            return Unproven(",
        "tests/test_ladder.py",
    ),
    Mutant(
        "ladder-gap-always-zero",
        "ladder",
        MODEL,
        "        return abs(self.objective - self.bound) / abs(self.objective)",
        "        return 0.0",
        "tests/test_ladder.py",
    ),
    Mutant(
        "ladder-skips-the-checker-on-its-own-output",
        "ladder",
        LADDER,
        "    return tuple(v.key() for v in check(roster, instance) if not v.soft)",
        "    return ()",
        "tests/test_ladder.py",
    ),
    Mutant(
        "ladder-invents-a-roster-when-there-is-no-incumbent",
        "ladder",
        LADDER,
        "        attempts.append(GREEDY)\n        return Answer(\n            roster=frozenset(),\n            rung=INCUMBENT,",
        "        attempts.append(GREEDY)\n        return Answer(\n            roster=frozenset(),\n            rung=EXACT,",
        "tests/test_ladder.py",
    ),
    # --- The service boundary -------------------------------------------------------------
    # Fairness and the replay round trip are both claims no single response can show, so
    # both would ship on a code review without these.
    Mutant(
        "service-queue-is-a-plain-fifo",
        "service",
        JOBS,
        "            if queue:\n                self._rotation.append(tenant)",
        "            if queue:\n                self._rotation.appendleft(tenant)",
        "tests/test_service.py",
    ),
    Mutant(
        "service-round-trip-drops-unavailability",
        "service",
        CONTRACTS,
        "                unavailability=[\n                    IntervalIn(start=i.start, end=i.end) for i in e.unavailability\n                ],",
        "                unavailability=[],",
        "tests/test_service.py",
    ),
    # A wire format that cannot carry a field is the shape `D-131` closed: the objective's
    # only memory, silently absent, on a payload that still parses and still solves.
    Mutant(
        "service-round-trip-drops-fairness",
        "service",
        CONTRACTS,
        "        fairness=(\n            None\n            if payload.fairness is None",
        "        fairness=(\n            None\n            if True",
        "tests/test_service.py",
    ),
    Mutant(
        "service-round-trip-drops-the-unpopular-prior",
        "service",
        CONTRACTS,
        "                unpopular_shifts_before_horizon=e.unpopular_shifts_before_horizon,\n                max_weekends=e.max_weekends,\n                min_consecutive_days_off=e.min_consecutive_days_off,\n                min_consecutive_days_worked=e.min_consecutive_days_worked,\n                max_shifts_per_type=(\n                    None if e.max_shifts_per_type is None else dict(e.max_shifts_per_type)\n                ),\n                min_hours_this_period=e.min_hours_this_period,\n                max_consecutive_days=e.max_consecutive_days,\n                flexi_eligible=(\n                    None if e.flexi_eligible is None else frozenset(e.flexi_eligible)\n                ),",
        "                max_weekends=e.max_weekends,\n                min_consecutive_days_off=e.min_consecutive_days_off,\n                min_consecutive_days_worked=e.min_consecutive_days_worked,\n                max_shifts_per_type=(\n                    None if e.max_shifts_per_type is None else dict(e.max_shifts_per_type)\n                ),\n                min_hours_this_period=e.min_hours_this_period,\n                max_consecutive_days=e.max_consecutive_days,\n                flexi_eligible=(\n                    None if e.flexi_eligible is None else frozenset(e.flexi_eligible)\n                ),",
        "tests/test_service.py",
    ),
    Mutant(
        "service-infinite-band-becomes-a-number",
        "service",
        CONTRACTS,
        "                            None if math.isinf(b.within_hours) else b.within_hours",
        "                            b.within_hours",
        "tests/test_service.py",
    ),
    Mutant(
        "service-skips-lawfulness-validation",
        "service",
        JOBS,
        "        defects = validate_instance(instance)",
        "        defects = []",
        "tests/test_service.py",
    ),
    Mutant(
        "service-solver-threads-ignore-concurrency",
        "service",
        JOBS,
        "    return max(1, (os.cpu_count() or 1) // max(1, concurrency))",
        "    return max(1, os.cpu_count() or 1)",
        "tests/test_service.py",
    ),
    # --- The MILP formulation, D-001's evidence ---------------------------------------
    # A second formulation is only evidence while it means the same thing. Each of these
    # produces a fast, plausible, wrong comparison.
    Mutant(
        "milp-accepts-the-default-mip-gap",
        "milp",
        MILP,
        "    params.SetDoubleParam(pywraplp.MPSolverParameters.RELATIVE_MIP_GAP, 0.0)",
        "    pass",
        "tests/test_milp.py",
    ),
    Mutant(
        "milp-drops-the-consecutive-day-link",
        "milp",
        MILP,
        "            for var in same_day:\n                solver.Add(indicator >= var)",
        "            for var in same_day:\n                pass",
        "tests/test_milp.py",
    ),
    Mutant(
        "milp-forgets-the-coverage-ceiling",
        "milp",
        MILP,
        "        solver.Add(sum(assigned) + short == required)",
        "        solver.Add(sum(assigned) + short >= required)",
        "tests/test_milp.py",
    ),
    Mutant(
        "milp-silently-accepts-d3",
        "milp",
        MILP,
        '    if instance.disruption is None or instance.disruption.metric not in ("D0", "D1", "D2"):',
        "    if False:",
        "tests/test_milp.py",
    ),
    # --- The penalty search, D-002's evidence -----------------------------------------
    # This rival exists to show what pricing a hard rule does, so the defects worth carrying
    # are the ones that quietly turn it back into a method that cannot. Both of these
    # produce a study whose every number still computes and means nothing.
    #
    # The first one **survived the first version of `tests/test_anneal.py`**, and that is why
    # `Result.accepted_illegal` exists: a gate refusing to make things worse still returns an
    # illegal roster, because the incumbent arrives already damaged. Only the trajectory
    # separates a priced rule from a prohibited one.
    Mutant(
        "anneal-gates-acceptance-on-feasibility",
        "anneal",
        ANNEAL,
        "        if delta <= 0 or rng.random() < math.exp(-delta / max(temperature, 1e-9)):",
        "        if cand_hard <= hard and (delta <= 0 or rng.random() < math.exp(-delta / max(temperature, 1e-9))):",
        "tests/test_anneal.py",
    ),
    Mutant(
        "anneal-lets-the-generator-rewrite-the-past",
        "anneal",
        ANNEAL,
        "        if not instance.is_past(o.day, o.shift)\n    )",
        "    )",
        "tests/test_anneal.py",
    ),
    Mutant(
        "anneal-drops-the-price-of-a-broken-rule",
        "anneal",
        ANNEAL,
        "    return measured + hard_weight * hard, measured, hard",
        "    return measured, measured, hard",
        "tests/test_anneal.py",
    ),
    # The summariser, which is a different kind of target: it cannot make the search wrong,
    # only the write-up. This is the defect this study actually shipped -- leading with
    # violations the search *introduced* rather than violations the roster *carries*, so a run
    # that returned the damaged incumbent untouched scored as a clean one. It inverts the
    # headline while every figure still computes, and the committed artifact cannot say which
    # reading produced it.
    Mutant(
        "anneal-summary-counts-only-fresh-violations",
        "anneal",
        ANNEAL_STUDY,
        '        illegal = [run for run, _ in pairs if run["hard"] > 0]',
        '        illegal = [run for run, _ in pairs if run["introduced"] > 0]',
        "tests/test_anneal.py",
    ),
    # --- Weight identifiability, D-129's evidence -------------------------------------
    # The finding is a null -- no D2 weight moves a committed roster -- so the thing that has
    # to be defended is the probe's ability to see a weight at all. Both mutants flatten
    # `forced_choice` so it no longer presents a choice, which turns a real null into a
    # vacuous one while every sweep still runs and still reports zero.
    Mutant(
        "weights-publish-the-whole-week-so-the-factor-is-uniform",
        "weights",
        WEIGHTS,
        "        published_through=96.0,",
        "        published_through=999.0,",
        "tests/test_weights.py",
    ),
    Mutant(
        "weights-give-the-spare-employee-budget-for-both-holes",
        "weights",
        WEIGHTS,
        'name="B", absences=(), max_hours_this_week=8.0',
        'name="B", absences=(), max_hours_this_week=38.0',
        "tests/test_weights.py",
    ),
    # --- The shortfall explainer ------------------------------------------------------
    # The invariant is the asset here: an unexplained employee means the roster is wrong,
    # not the explanation. A version that never reports one passes 72 cases silently.
    Mutant(
        "explain-never-reports-unexplained",
        "explain",
        EXPLAIN,
        "            else:\n                unexplained.append(employee)",
        "            else:\n                pass",
        "tests/test_explain.py",
    ),
    Mutant(
        "explain-ignores-rules-already-broken",
        "explain",
        EXPLAIN,
        "    before = _hard_rules(instance, frozenset(own), employee)",
        "    before = set()",
        "tests/test_explain.py",
    ),
    Mutant(
        "explain-explains-the-pinned-past-too",
        "explain",
        EXPLAIN,
        "        if instance.is_past(day, shift):\n            continue",
        "        if False:\n            continue",
        "tests/test_explain.py",
    ),
    Mutant(
        "explain-reports-only-the-first-rule",
        "explain",
        EXPLAIN,
        "            counts.update(set(entry.rules))",
        "            counts.update(set(entry.rules[:1]))",
        "tests/test_explain.py",
    ),
    # --- The prose layer --------------------------------------------------------------
    # The validator is the D-013 boundary made enforceable. Every defect here widens what a
    # rendering may claim, and a wider bound is invisible in output that happens to be true.
    Mutant(
        "prose-validator-ignores-invented-names",
        "prose",
        PROSE,
        "            or any(character.isdigit() for character in token)",
        "            or False",
        "tests/test_prose.py",
    ),
    Mutant(
        "prose-invents-a-weekday-without-a-calendar",
        "prose",
        PROSE,
        '        when = f"day {day}"',
        '        when = WEEKDAYS[day % 7]',
        "tests/test_prose.py",
    ),
    Mutant(
        "prose-drops-the-unexplained-warning",
        "prose",
        PROSE,
        "    if finding.unexplained:",
        "    if False:",
        "tests/test_prose.py",
    ),
    Mutant(
        "prose-clock-does-not-roll-over",
        "prose",
        PROSE,
        "    minutes = int(round(hours * 60)) % (24 * 60)",
        "    minutes = int(round(hours * 60))",
        "tests/test_prose.py",
    ),
    # --- what_if -----------------------------------------------------------------------
    # The dangerous output here is not a wrong number, it is a confident yes to an unlawful
    # hypothetical. Both mutants below produce one.
    Mutant(
        "whatif-answers-unlawful-hypotheticals",
        "whatif",
        WHATIF,
        "    defects = validate_instance(variant_instance)",
        "    defects = []",
        "tests/test_whatif.py",
    ),
    Mutant(
        "whatif-baseline-uses-a-different-seed",
        "whatif",
        WHATIF,
        "        baseline = _measure(instance, seed=seed, time_limit=time_limit)",
        "        baseline = _measure(instance, seed=seed + 1, time_limit=time_limit)",
        "tests/test_whatif.py",
    ),
    # --- recommend (`D-144`) -------------------------------------------------------------
    # The first two are the same species as the unlawful hypothetical above: an output a
    # planner would act on, wrong in a way the numbers do not show. The third is a cost
    # guard rather than a correctness one, and is here because an uncapped sweep is a solve
    # per blocked person.
    Mutant(
        "recommend-ranks-statutory-against-operational",
        "whatif",
        WHATIF,
        '            key=lambda r: (r.provenance != "operational", r.disruption_delta, r.employee),',
        "            key=lambda r: (r.disruption_delta, r.employee),",
        "tests/test_whatif.py",
    ),
    Mutant(
        "recommend-resolves-the-baseline-per-candidate",
        "whatif",
        WHATIF,
        "            instance, (change,), seed=seed, time_limit=time_limit, baseline=baseline",
        "            instance, (change,), seed=seed, time_limit=time_limit",
        "tests/test_whatif.py",
    ),
    Mutant(
        "recommend-ignores-the-candidate-cap",
        "whatif",
        WHATIF,
        "        if tested >= max_candidates:",
        "        if False:",
        "tests/test_whatif.py",
    ),
    Mutant(
        "whatif-hire-lands-without-the-skill",
        "whatif",
        WHATIF,
        "            skills=frozenset(change.skills),",
        "            skills=frozenset(),",
        "tests/test_whatif.py",
    ),
    # --- Profile review -----------------------------------------------------------------
    # A config check that silently passes is worse than none: the tenant believes their
    # policy was validated. Each of these makes a bad profile look acceptable.
    Mutant(
        "profile-accepts-unencoded-optional-rules",
        "profile",
        PROFILE,
        "    unenforced = profile.enabled_optional_rules & set(OPTIONAL_RULES)",
        "    unenforced = set()",
        "tests/test_profile.py",
    ),
    Mutant(
        "profile-probes-a-contradictory-profile-anyway",
        "profile",
        PROFILE,
        "    if defects or sample is None:",
        "    if sample is None:",
        "tests/test_profile.py",
    ),
    Mutant(
        "profile-skips-lawfulness-before-probing",
        "profile",
        PROFILE,
        "    defects = validate_instance(instance)\n    if defects:",
        "    defects = []\n    if defects:",
        "tests/test_profile.py",
    ),
    Mutant(
        "profile-inert-rule-reported-as-a-defect",
        "profile",
        PROFILE,
        "    if params.max_consecutive_days is not None and params.max_consecutive_days >= days:",
        "    if False:",
        "tests/test_profile.py",
    ),
    # The failure `D-131` was: policy the spec says the profile declares, which the profile
    # silently dropped on its way to the week. Nothing failed, and fairness was simply off.
    Mutant(
        "profile-drops-the-fairness-declaration",
        "profile",
        PROFILE,
        "            disruption=self.disruption,\n            fairness=self.fairness,",
        "            disruption=self.disruption,",
        "tests/test_profile.py",
    ),
    Mutant(
        "profile-misses-priors-past-the-tiers",
        "profile",
        PROFILE,
        "        if person.unpopular_shifts_before_horizon >= fair.tiers",
        "        if False",
        "tests/test_profile.py",
    ),
    # --- Minimal cores ------------------------------------------------------------------
    # A core that is smaller but no longer explains anything is the failure here, and it
    # looks like success: fewer rules, cleaner output, wrong.
    Mutant(
        "core-drops-necessary-gates",
        "core",
        CORE,
        "        if _satisfiable(built, necessary + candidate, solver):\n            # Without this gate the model can be satisfied, so it is doing real work.\n            necessary.append(gate)",
        "        if False:\n            necessary.append(gate)",
        "tests/test_core.py",
    ),
    Mutant(
        "core-keeps-everything",
        "core",
        CORE,
        "    while candidate:\n        gate = candidate.pop()",
        "    while False:\n        gate = candidate.pop()",
        "tests/test_core.py",
    ),
    # No mutant for "solves with the objective set": it is not expressible as a swap here,
    # because `_satisfiable` has no `instance` to build an objective from. The property is
    # asserted directly instead, by `test_the_objective_is_what_inflates_the_core`, which
    # compares against `solve()` itself.
    # --- The natural-language parse -----------------------------------------------------
    # The schema is the confinement, so the first two mutants are defects *in the schema*
    # rather than in any statement of logic. Both leave every behavioural test passing --
    # a stub returns whatever the test asks it to, whatever the API would have allowed --
    # which is why the layer reads the compiled schema instead. The first is `D-101` itself.
    Mutant(
        "nl-derogations-as-an-open-mapping",
        "nl",
        NL,
        "    derogations: list[DerogationIn] = Field(",
        "    derogations: dict[str, str] = Field(",
        "tests/test_nl.py",
    ),
    Mutant(
        "nl-derogation-parameter-is-free-text",
        "nl",
        NL,
        'DEROGABLE = Literal["min_rest_hours", "min_weekly_rest_hours", "min_period_hours"]',
        "DEROGABLE = str",
        "tests/test_nl.py",
    ),
    Mutant(
        "nl-silence-overwrites-the-base-profile",
        "nl",
        NL,
        "    fallback_params = base.params if base else RuleParams(",
        "    fallback_params = None or RuleParams(",
        "tests/test_nl.py",
    ),
    Mutant(
        "nl-accepts-a-candidate-with-defects",
        "nl",
        NL,
        "        if self.defects:\n            return False",
        "        if False:\n            return False",
        "tests/test_nl.py",
    ),
    # The renderer is half of `config.md`'s round trip, and a field it drops is invisible in
    # output that reads perfectly well -- the trip still passes whenever the dropped value
    # happens to equal the fallback. This is that failure, made to happen on purpose.
    Mutant(
        "nl-rendering-drops-a-rule",
        "nl",
        NL,
        '    lines.append(\n        f"Everyone must get at least {params.min_weekly_rest_hours:g} hours of unbroken "\n        f"rest each week."\n    )',
        "    pass  # the weekly rest never reaches the page",
        "tests/test_nl.py",
    ),
    # `D-102`: an eval that cannot fail measures nothing. This one is not in the suite -- it
    # needs a key -- so its scoring is exactly the code that can rot unnoticed.
    Mutant(
        "nl-eval-passes-an-invented-rule",
        "nl",
        NL_EVAL,
        '        if unset_want and not unset_have:\n            lines.append(f"invented {name}: {have!r}")',
        "        if unset_want and not unset_have:\n            pass",
        "tests/test_nl.py",
    ),
    # --- Generation (the cold-start case) ------------------------------------------------
    # The first mutant is the interesting one: it makes the code do what `replan.md` used to
    # *derive* -- cold disruption as a positive constant rather than flat zero. `D-109` found
    # that gap by measuring, and this is it turned into a defect the layer has to see.
    Mutant(
        "generation-cold-disruption-is-not-flat",
        "generation",
        SCORING,
        "    if instance.incumbent is None:\n        return 0",
        "    if False:\n        return 0",
        "tests/test_generation.py",
    ),
    Mutant(
        "generation-loses-its-only-tie-breaker",
        "generation",
        DISRUPTION,
        "        terms.append(params.peak_weight * _peak(model, instance, x))",
        "        terms.append(0 * _peak(model, instance, x))",
        "tests/test_generation.py",
    ),
    # --- Fairness ----------------------------------------------------------------------
    # The dangerous defect is not a wrong score, it is a term that prices correctly and
    # steers nothing, or one that outbids coverage. Both look like a working feature.
    Mutant(
        "fairness-ignores-history-before-the-horizon",
        "fairness",
        DISRUPTION,
        "        model.add(total == prior + sum(assigned))",
        "        model.add(total == sum(assigned))",
        "tests/test_fairness.py",
    ),
    Mutant(
        "fairness-scorer-ignores-history",
        "fairness",
        SCORING,
        "        count = person.unpopular_shifts_before_horizon + worked",
        "        count = worked",
        "tests/test_fairness.py",
    ),
    Mutant(
        "fairness-escalation-is-flat",
        "fairness",
        DISRUPTION,
        "        for k in range(1, params.tiers + 1):\n            model.add(penalty >= k * total - k * (k - 1) // 2)",
        "        for k in range(1, 2):\n            model.add(penalty >= k * total - k * (k - 1) // 2)",
        "tests/test_fairness.py",
    ),
    Mutant(
        "fairness-escapes-the-domination-bound",
        "fairness",
        VALIDATION,
        "        per_assignment += fair.weight * fair.tiers",
        "        per_assignment += 0",
        "tests/test_fairness.py",
    ),
    # A `.env` that overrides an exported key bills the wrong account, and looks like
    # nothing at all -- the run succeeds, against credentials the caller did not choose.
    Mutant(
        "nl-silence-deletes-the-fairness-declaration",
        "nl",
        NL,
        "        fairness=base.fairness if base else None,",
        "        fairness=None,",
        "tests/test_nl.py",
    ),
    Mutant(
        "nl-eval-env-file-overrides-the-shell",
        "nl",
        NL_EVAL,
        "        if not key or not value or key in environ:",
        "        if not key or not value:",
        "tests/test_nl.py",
    ),
    Mutant(
        "studies-horizon-forgets-the-boundary",
        "studies",
        "benchmarks/studies.py",
        "        last = max(ends) - end_of_week * 24.0 if ends else None",
        "        last = None",
        "tests/test_studies.py",
    ),
    # --- R-MAX-WEEKENDS and R-MIN-DAYS-OFF ------------------------------------------------
    # Both rules are new and both are optional, which is the dangerous combination: a rule
    # nobody's payload switches on is a rule no existing test can see fail (`D-135`). Each
    # of these breaks one reading and must be caught by the layer holding the two together.
    Mutant(
        "model-weekends-counted-per-day-not-per-week",
        "weekends",
        MODEL,
        "            model.add(worked_weekend[instance.week_of(day)] >= var)",
        "            model.add(worked_weekend[day % instance.weeks] >= var)",
        "tests/test_ground_truth.py",
    ),
    Mutant(
        "checker-weekends-counts-days-not-weekends",
        "weekends",
        CHECKER,
        "        weeks = {\n            instance.week_of(day) for day, _ in shifts if day % DAYS_PER_WEEK in weekend\n        }",
        "        weeks = {\n            day for day, _ in shifts if day % DAYS_PER_WEEK in weekend\n        }",
        "tests/test_optional_rules.py",
    ),
    Mutant(
        "model-days-off-judges-the-horizon-edge",
        "weekends",
        MODEL,
        "            for start in range(instance.days - gap - 1):",
        "            for start in range(-1, instance.days - gap):",
        "tests/test_ground_truth.py",
    ),
    Mutant(
        "checker-days-off-judges-the-horizon-edge",
        "weekends",
        CHECKER,
        "                if start > 0 and day < instance.days and length < minimum:\n                    person = instance.employees[employee]\n                    out.append(\n                        Violation(\n                            rule=\"R-MIN-DAYS-OFF\",",
        "                if length < minimum:\n                    person = instance.employees[employee]\n                    out.append(\n                        Violation(\n                            rule=\"R-MIN-DAYS-OFF\",",
        "tests/test_optional_rules.py",
    ),
    Mutant(
        "checker-days-off-rule-is-inert",
        "weekends",
        CHECKER,
        "        minimum = instance.employees[employee].min_consecutive_days_off\n        if minimum is None or minimum < 2:",
        "        minimum = instance.employees[employee].min_consecutive_days_off\n        if minimum is None or minimum < 3:",
        "tests/test_optional_rules.py",
    ),
    # --- The rest of D-134's constraint set (`D-136`) --------------------------------------
    # Each breaks one reading of one rule. The two `min-block` mutants are the pair worth
    # keeping: a shared predicate between it and R-MIN-DAYS-OFF would have made a single
    # defect break both rules in both readings, which is what the independence rule forbids.
    Mutant(
        "model-min-block-judges-the-horizon-edge",
        "spanrules",
        MODEL,
        "            for start in range(instance.days - block - 1):",
        "            for start in range(-1, instance.days - block):",
        "tests/test_ground_truth.py",
    ),
    Mutant(
        "checker-min-block-judges-the-horizon-edge",
        "spanrules",
        CHECKER,
        "                if start > 0 and day < instance.days and length < minimum:\n                    person = instance.employees[employee]\n                    out.append(\n                        Violation(\n                            rule=\"R-MIN-BLOCK\",",
        "                if length < minimum:\n                    person = instance.employees[employee]\n                    out.append(\n                        Violation(\n                            rule=\"R-MIN-BLOCK\",",
        "tests/test_optional_rules.py",
    ),
    Mutant(
        "model-shift-type-cap-is-a-total",
        "spanrules",
        MODEL,
        "                var for (e, _, s), var in built.x.items() if e == employee and s == shift",
        "                var for (e, _, s), var in built.x.items() if e == employee",
        "tests/test_ground_truth.py",
    ),
    Mutant(
        "checker-shift-type-cap-is-a-total",
        "spanrules",
        CHECKER,
        "            worked = sum(1 for _, s in shifts if s == shift)",
        "            worked = len(shifts)",
        "tests/test_optional_rules.py",
    ),
    Mutant(
        "model-hours-floor-is-a-ceiling",
        "spanrules",
        MODEL,
        "        model.add(sum(minutes) >= _minutes(floor)).only_enforce_if(literal)",
        "        model.add(sum(minutes) <= _minutes(floor)).only_enforce_if(literal)",
        "tests/test_ground_truth.py",
    ),
    Mutant(
        "checker-hours-floor-never-binds",
        "spanrules",
        CHECKER,
        "        if worked < floor:",
        "        if False:",
        "tests/test_optional_rules.py",
    ),
    Mutant(
        "model-succession-ignores-direction",
        "spanrules",
        MODEL,
        "                first = built.x.get((employee, day, earlier))\n                second = built.x.get((employee, day + 1, later))",
        "                first = built.x.get((employee, day, later))\n                second = built.x.get((employee, day + 1, earlier))",
        "tests/test_ground_truth.py",
    ),
    Mutant(
        "checker-succession-ignores-direction",
        "spanrules",
        CHECKER,
        "                    if (earlier, later) not in pairs:",
        "                    if (later, earlier) not in pairs:",
        "tests/test_optional_rules.py",
    ),
    Mutant(
        "model-personal-consecutive-limit-ignored",
        "spanrules",
        MODEL,
        "    if person.max_consecutive_days is not None:\n        return person.max_consecutive_days",
        "    if False:\n        return person.max_consecutive_days",
        "tests/test_ground_truth.py",
    ),
    Mutant(
        "checker-personal-consecutive-limit-ignored",
        "spanrules",
        CHECKER,
        "        limit = person.max_consecutive_days\n        if limit is None:",
        "        limit = None\n        if limit is None:",
        "tests/test_optional_rules.py",
    ),
    # --- R-DAY-OFF ----------------------------------------------------------------------
    # The rule exists because an interval reading is wrong at the day boundary, so the mutant
    # that matters is the one that reinstates the interval reading. Both are size-changing,
    # which `D-141` is the reason for caring about.
    Mutant(
        "model-day-off-catches-the-night-before",
        "dayoff",
        MODEL,
        "                if e != employee or d != day:",
        "                if e != employee or d not in (day, day - 1):",
        "tests/test_ground_truth.py",
    ),
    Mutant(
        "checker-day-off-catches-the-night-before",
        "dayoff",
        CHECKER,
        "        if day in person.days_off:",
        "        if day in person.days_off or day + 1 in person.days_off:",
        "tests/test_ground_truth.py",
    ),
    # Named for `test_ground_truth.py` and *not* the differential harness, which cannot see
    # this: the generator grants nobody a day off, so both readings agree perfectly about an
    # instance where the rule never applies. That is `D-108`'s note about fairness in another
    # place -- a layer needs an instance containing the structure before a null means anything.
    Mutant(
        "model-day-off-never-binds",
        "dayoff",
        MODEL,
        "        for day in sorted(person.days_off):",
        "        for day in sorted(()):",
        "tests/test_ground_truth.py",
    ),
    # --- The foreign importer -----------------------------------------------------------
    # Every one of these is a silent misreading of somebody else's data: the parse succeeds,
    # the numbers look plausible, and what they mean is wrong. These three are mutated in the
    # half of the parse that needs no fetched copy (`D-132`), so they are caught on any
    # machine — the benchmark data is never redistributed, and a mutant nobody can run is a
    # mutant that reports a survivor on every clean checkout.
    Mutant(
        "foreign-cover-weights-are-swapped",
        "foreign",
        FOREIGN,
        "        under[slot] = int(under_weight)\n        over[slot] = int(over_weight)",
        "        under[slot] = int(over_weight)\n        over[slot] = int(under_weight)",
        "tests/test_foreign.py",
    ),
    Mutant(
        "foreign-max-shifts-read-as-a-total",
        "foreign",
        FOREIGN,
        "        for entry in parts[1].split(\"|\"):",
        "        for entry in parts[1].split(\"|\")[:1]:",
        "tests/test_foreign.py",
    ),
    # Their objective, which is checked against 26 numbers this project did not choose. Each
    # of these is a term implemented backwards or omitted, and each would still produce a
    # plausible total on some roster (`D-133`).
    Mutant(
        "foreign-objective-ignores-overstaffing",
        "foreign",
        FOREIGN,
        "        penalty += unencoded.over_weight[slot] * max(0, have - open_shift.required)",
        "        penalty += 0",
        "tests/test_foreign.py",
    ),
    Mutant(
        "foreign-objective-reverses-the-request-lists",
        "foreign",
        FOREIGN,
        "    for request in unencoded.on_requests:\n        if (request.employee, request.day, request.shift) not in roster:",
        "    for request in unencoded.on_requests:\n        if (request.employee, request.day, request.shift) in roster:",
        "tests/test_foreign.py",
    ),
    Mutant(
        "foreign-incumbent-is-whichever-solution-was-found",
        "foreign",
        FOREIGN,
        "    return tuple(sorted(found, key=lambda s: s.objective))",
        "    return tuple(found)",
        "tests/test_foreign.py",
    ),
    # Their constraints, checked before any of them is encoded (`D-134`). The boundary one is
    # the mutant that matters: the latitude a minimum needs at the horizon edge is exactly what
    # a maximum must not get, and applying it to both is the plausible mistake.
    Mutant(
        "foreign-max-run-gets-the-boundary-latitude-too",
        "foreign",
        FOREIGN,
        "            if len(run) > limit.max_consecutive_shifts:",
        "            if interior(run) and len(run) > limit.max_consecutive_shifts:",
        "tests/test_foreign.py",
    ),
    Mutant(
        "foreign-weekends-counted-per-day-not-per-week",
        "foreign",
        FOREIGN,
        "            day // DAYS_PER_WEEK for day in days if day % DAYS_PER_WEEK in WEEKEND_DAYS",
        "            day for day in days if day % DAYS_PER_WEEK in WEEKEND_DAYS",
        "tests/test_foreign.py",
    ),
    Mutant(
        "foreign-succession-ignores-direction",
        "foreign",
        FOREIGN,
        "            if following is not None and following in unencoded.cannot_follow.get(shift, ()):",
        "            if following is not None and shift in unencoded.cannot_follow.get(following, ()):",
        "tests/test_foreign.py",
    ),
    Mutant(
        "foreign-invents-an-empty-succession-rule",
        "foreign",
        FOREIGN,
        "        if forbidden:\n            blocked[index[sid]] = forbidden",
        "        blocked[index[sid]] = forbidden",
        "tests/test_foreign.py",
    ),
    Mutant(
        "studies-patterns-skip-the-legality-check",
        "studies",
        PATTERNS,
        "        if _legal(instance, employee, pattern):\n            patterns.append(pattern)",
        "        if True:\n            patterns.append(pattern)",
        "tests/test_studies.py",
    ),
    # --- The README's figure --------------------------------------------------------
    # `D-147`: the drawing is committed, so it can go stale, and it carries counts in its
    # own caption, so it can lie. One mutant per failure -- a mark drawn in the wrong
    # state, and a boundary drawn in the wrong column.
    Mutant(
        "figure-drops-and-adds-swapped",
        "figure",
        FIGURE,
        '        elif key in roster:\n            states[key] = "added"',
        '        elif key in roster:\n            states[key] = "dropped"',
        "tests/test_figure.py",
    ),
    Mutant(
        "figure-pinned-boundary-off-by-a-day",
        "figure",
        FIGURE,
        "            if start >= instance.now:",
        "            if start >= instance.now - 24:",
        "tests/test_figure.py",
    ),

)


# --- Running ------------------------------------------------------------------------


def _failed_tests(stdout: str) -> list[str]:
    return [
        line.split("::", 1)[-1].split()[0]
        for line in stdout.splitlines()
        if line.startswith("FAILED")
    ]


def _restore(path: pathlib.Path, original: str, *, attempts: int = 5) -> None:
    """Put the file back, and keep putting it back until it stays put.

    An editor's format-on-save watcher reads the file when it changes and writes its
    result some time later. During a run it therefore sees the *mutated* text, and its
    debounced write can land after the restore and reinstate the mutation. That happened,
    and it left a swapped weight in `disruption.py` in a working tree that looked clean at
    a glance.

    Retrying with a pause is what makes the restore win the race. The final check is not
    optional -- a harness that edits source and cannot prove it undid the edit is worse
    than no harness.
    """
    for attempt in range(attempts):
        path.write_text(original)
        # The restore is a size-neutral write too, and the next mutant reads this file
        # through the same cache (`D-141`).
        _invalidate(path)
        time.sleep(0.2 * (attempt + 1))
        if path.read_text() == original:
            return
    raise RuntimeError(
        f"could not restore {path}: something else is writing to it. Run "
        f"`git checkout -- {path}` and turn off format-on-save before retrying."
    )


REPORT = _HERE / "mutation-report.json"


def summarise(
    results: list[dict],
    *,
    leaked: list[str],
    skipped: list[str],
    full: bool,
    late: list[str] = (),
    started_at: str | None = None,
    duration_seconds: float | None = None,
) -> dict:
    """The run's verdict, as data. Pure, so the part that can be wrong is testable.

    **The verdict does not live in stdout.** A run's result was twice read through a pipe
    that swallowed it: `tail` truncated the per-mutant lines *and* reported its own exit
    status, so a run that leaked a mutated file into the working tree read as a clean pass.
    The report is written before any of the return paths, so a truncated terminal, a killed
    pager or a lost scrollback costs nothing.

    **A leak outranks survivors**, matching what the exit codes have always said. A run that
    left a mutation behind cannot be trusted about anything that ran after it: the following
    mutants' catcher tests may have failed on the leftover defect rather than on their own,
    and would be scored as caught for the wrong reason. That is a void run, not a passing
    one with a caveat.

    **And absence of assurance is not assurance** (`D-112`). Two conditions leave this run
    unable to vouch for the tree it ran in, and both were reported in fields beside a
    `clean` verdict that contradicted them:

    - a target file **already modified** when the run started, which the clean-tree check
      subtracts, so a mutation left in that file is invisible to it;
    - a **late write**, where an editor reinstated the mutated text after its own restore
      verified, so some mutant ran against source nobody chose.

    **A third condition was added after that sentence was falsified** (`D-139`). "A mutant
    that survived, survived" is not true if the defect was gone before the tests ran: an
    editor that reinstates the original inside the test window leaves pytest with nothing to
    find, and the mutant is scored a survivor. `run` now checks the mutation is still in the
    file when the tests finish, and a `voided` result is neither caught nor survived -- it
    denies the run its guarantee for that path, exactly as a late write does.

    Neither of the first two is a finding, so neither outranks a survivor.
    Both deny the run its guarantee, so the verdict is `unverifiable` where it would have
    been `clean`, and `trustworthy` is false either way. This is written from the run that
    prompted it: `clean`, `trustworthy: true`, `leaked: []`, and a mutated `checker.py` in
    the tree, with the reason stated three fields lower in the same object.
    """
    survivors = [r["name"] for r in results if not r["caught"] and not r.get("voided")]
    unvouched = sorted(set(skipped) | set(late))
    if leaked:
        verdict, exit_code = "leaked", 2
    elif survivors:
        verdict, exit_code = "survivors", 1
    elif unvouched:
        verdict, exit_code = "unverifiable", 3
    else:
        verdict, exit_code = "clean", 0

    return {
        "verdict": verdict,
        "exit_code": exit_code,
        "trustworthy": not leaked and not unvouched,
        # How long the run took, so the cost of one is a measurement rather than folklore.
        # Both are `None` when `summarise` is called outside a run, as its own tests do.
        # `duration_seconds` comes from a monotonic clock: the wall-clock stamps bracket the
        # same interval, but subtracting them measures the system clock as much as the run.
        "started_at": started_at,
        "finished_at": datetime.datetime.now(datetime.timezone.utc).isoformat(timespec="seconds"),
        "duration_seconds": duration_seconds,
        "selected": len(results),
        "caught": sum(1 for r in results if r["caught"]),
        "survivors": survivors,
        "leaked": sorted(leaked),
        # Files this run could not vouch for, because they were already modified when it
        # started. A mutation left in one of these is invisible to the clean-tree check.
        "unchecked_because_already_modified": sorted(skipped),
        "restored_after_a_late_write": sorted(late),
        # The union of the two, which is what the verdict is computed from. Named rather
        # than left to be reconstructed, because it is the reason a run is not `clean`.
        "unvouched_for": unvouched,
        "catcher_only": not full,
        "mutants": results,
    }


def write_report(report: dict, path: pathlib.Path = REPORT) -> pathlib.Path:
    path.write_text(json.dumps(report, indent=2) + "\n")
    return path


def _late_restore(originals: dict) -> list[str]:
    """Put back anything that drifted after its own restore verified. Returns what drifted.

    A format-on-save watcher reads the file when the mutation lands and writes its result
    some time later, which can be after `_restore` has already checked and returned. That
    has now happened twice, to `disruption.py` and to `benchmarks/suite.py`, and each time
    it voided a run that was otherwise complete.

    Restoring here is safe in a way `git checkout --` is not: the text being written back
    is what this process read before it touched the file, so uncommitted work is preserved
    rather than discarded. The drift is still **reported** -- self-healing quietly would
    hide a real harness bug behind a plausible excuse.
    """
    drifted = []
    for relative, text in sorted(originals.items()):
        path = ROOT / relative
        if path.read_text() != text:
            path.write_text(text)
            drifted.append(relative)
    return drifted


def _dirty(paths: list[str]) -> set[str]:
    """Which of these paths git already considers modified."""
    result = subprocess.run(
        ["git", "status", "--porcelain", "--", *paths],
        cwd=ROOT, capture_output=True, text=True,
    )
    return {line[3:].strip() for line in result.stdout.splitlines() if line.strip()}


def _invalidate(path: pathlib.Path) -> None:
    """Drop the cached bytecode for a file this harness just rewrote (`D-141`).

    CPython validates a `.pyc` against the source's **size and mtime in whole seconds**. A
    mutation that changes neither -- swapping two identifiers, `>=` for `<=`, a range's
    bounds -- written inside the same second as the cached copy is invisible to that check,
    so the interpreter runs the *original* code and the mutant survives having never been
    tested.

    Fourteen of this catalogue's mutants are size-neutral, and the three that surfaced as
    intermittent survivors were all of them. Deleting the `.pyc` is the only fix that does
    not depend on timing: touching the mtime forward would work until two writes land in one
    second again, which is exactly the condition that produced this.
    """
    cache = path.parent / "__pycache__"
    if not cache.is_dir():
        return
    for stale in cache.glob(f"{path.stem}.*.pyc"):
        stale.unlink(missing_ok=True)


def run(
    mutant: Mutant, *, full: bool, originals: dict | None = None
) -> tuple[bool, list[str], str, str]:
    """Apply, test, restore. Returns (caught, failing tests, note, evidence).

    `originals` collects each touched file's pre-run text so `main` can sweep at the end.
    `_restore` verifies, and has still been beaten twice by an editor writing back the
    mutated text *after* that check returned -- see `_late_restore`.
    """
    path = mutant.target()
    original = path.read_text()
    if originals is not None:
        originals.setdefault(mutant.path, original)
    if original.count(mutant.old) != 1:
        return (
            False,
            [],
            f"anchor matched {original.count(mutant.old)} times, so nothing was tested",
            "",
        )

    path.write_text(original.replace(mutant.old, mutant.new, 1))
    _invalidate(path)
    try:
        target = "tests" if full else mutant.catcher
        result = subprocess.run(
            [sys.executable, "-m", "pytest", target, "-q", "--no-header", "--tb=no", "-p",
             "no:cacheprovider"],
            cwd=ROOT, capture_output=True, text=True, timeout=1800,
        )
        # **Was the defect still there when the tests ran?** (`D-139`) A late write lands in
        # this window as easily as in the one after the restore, and there it is worse: the
        # editor reinstates the *original*, pytest passes because there is nothing wrong,
        # and the mutant is scored a survivor. That reads as a hole in a test layer and is
        # a hole in this harness, which is the one failure mode it exists to not have.
        reverted = mutant.new not in path.read_text()
    finally:
        _restore(path, original)

    if reverted:
        return False, [], REVERTED, ""

    failed = _failed_tests(result.stdout)
    note = ""
    if not failed and result.returncode != 0:
        note = "the target failed without a test failure -- a collection or import error"

    # **A survivor keeps its evidence** (`D-140`). Two mutants have survived one run and been
    # caught in the next, deterministic in isolation and intermittent inside a full run, and
    # each investigation had to reconstruct what the catcher saw. The output is only kept for
    # a survivor, because that is the only case where anybody needs it and keeping all 132
    # would make the report unreadable.
    evidence = "" if failed else f"exit {result.returncode}\n{result.stdout[-2000:]}"
    return bool(failed), failed, note, evidence


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("-k", dest="pattern", help="only mutants whose name or layer matches")
    parser.add_argument("--list", action="store_true", help="list mutants and exit")
    parser.add_argument(
        "--full",
        action="store_true",
        help="run the whole suite per mutant instead of the layer that should catch it. "
        "Slower, and it answers a weaker question.",
    )
    parser.add_argument(
        "--report",
        type=pathlib.Path,
        default=REPORT,
        help=f"where to write the machine-readable verdict (default {REPORT.name})",
    )
    args = parser.parse_args()

    chosen = [
        m
        for m in MUTANTS
        if not args.pattern or args.pattern in m.name or args.pattern in m.layer
    ]
    if not chosen:
        print(f"no mutant matches {args.pattern!r}")
        return 1

    if args.list:
        width = max(len(m.name) for m in chosen)
        for m in chosen:
            print(f"{m.name:{width}}  {m.layer:11s}  expects {m.catcher}")
        return 0

    # Anything already modified cannot be checked for accidental damage afterwards, so
    # say so up front rather than reporting a false alarm at the end.
    touched = sorted({m.path for m in chosen})
    already = _dirty(touched)
    if already:
        print(f"note: already modified, so the final clean-tree check skips them: "
              f"{', '.join(sorted(already))}\n")

    # Pre-flight. A mutant whose anchor is missing means one of two things and both are
    # worth stopping a forty-minute run for: a payload leaked from an earlier run and is
    # sitting in the tree, or the source moved and the mutant is stale. The first has now
    # happened three times -- an editor's format-on-save watcher writing the mutated text
    # back *minutes* after the run that produced it had finished, into an idle tree, where
    # no end-of-run sweep can reach it.
    stale = []
    for mutant in chosen:
        text = mutant.target().read_text()
        if text.count(mutant.old) != 1:
            stale.append(f"{mutant.name} ({mutant.path})")
    if stale:
        print("!! refusing to start: these mutants cannot find their anchor —")
        for line in stale:
            print(f"!!   {line}")
        print("!! either a payload leaked into the tree, or the source moved and the mutant")
        print("!! is stale. `git diff` the named files; format-on-save is the usual culprit.")
        return 2

    # **Is every catcher green before anything is mutated?** (`D-143`) A mutant is scored
    # caught when its catcher fails, so a catcher that was *already* failing scores every
    # mutant it guards as caught without testing one. That happened: a micro-instance was
    # rewritten and the golden record not regenerated, and the run that followed reported
    # `clean` with `tests/test_golden.py` red the whole time.
    #
    # Checked once per distinct catcher rather than once per mutant -- 25 runs instead of
    # 132, and the question is about the tree rather than about any mutation.
    print(f"checking {len(set(m.catcher for m in chosen))} catchers are green first...")
    red = []
    for catcher in sorted({m.catcher for m in chosen}):
        result = subprocess.run(
            [sys.executable, "-m", "pytest", catcher, "-q", "--no-header", "--tb=no", "-p",
             "no:cacheprovider"],
            cwd=ROOT, capture_output=True, text=True, timeout=1800,
        )
        if result.returncode != 0:
            red.append(f"{catcher} ({', '.join(_failed_tests(result.stdout)[:3]) or 'no test failure -- a collection error'})")
    if red:
        print("!! refusing to start: these catchers already fail —")
        for line in red:
            print(f"!!   {line}")
        print("!! every mutant they guard would be scored caught without being tested.")
        print("!! fix the tree first; a green catcher is what makes a catch mean anything.")
        return 2

    print(f"\n{len(chosen)} mutants; each expects its own layer to object.\n")
    started_at = datetime.datetime.now(datetime.timezone.utc).isoformat(timespec="seconds")
    started = time.monotonic()
    results = []
    originals: dict[str, str] = {}
    late: list[str] = []
    for mutant in chosen:
        # Before each mutant, not only at the end. A late write lands *after* its own
        # restore verified, so the file stays wrong until something notices -- and every
        # mutant that runs meanwhile is tested against source nobody chose. Sweeping here
        # bounds that window to a single mutant instead of to the rest of the run.
        drifted = _late_restore(originals)
        if drifted:
            late.extend(d for d in drifted if d not in late)
            print(f"          ! late write to {', '.join(drifted)}, restored before this mutant")
        caught, failed, note, evidence = run(mutant, full=args.full, originals=originals)
        if note == REVERTED and mutant.path not in late:
            late.append(mutant.path)
        status = "CAUGHT" if caught else "VOID" if note == REVERTED else "SURVIVED"
        print(f"{status:9s} {mutant.name}")
        if note:
            print(f"          ! {note}")
        for name in failed[:3]:
            print(f"            {name}")
        if len(failed) > 3:
            print(f"            ... and {len(failed) - 3} more")
        results.append(
            {
                "name": mutant.name,
                "layer": mutant.layer,
                "path": mutant.path,
                "catcher": mutant.catcher,
                "caught": caught,
                "failed": failed,
                "note": note,
                "voided": note == REVERTED,
                # Only a survivor carries this; see `run`.
                "evidence": evidence,
            }
        )

    print()
    for path in _late_restore(originals):
        if path not in late:
            late.append(path)
    if late:
        print(f"note: restored after a late write to {', '.join(sorted(late))} — an editor "
              f"wrote back after the per-mutant check passed. The window is bounded to one "
              f"mutant, but turning format-on-save off is the actual fix.\n")

    report = summarise(
        results,
        leaked=sorted(_dirty(touched) - already),
        skipped=sorted(already),
        full=args.full,
        late=late,
        started_at=started_at,
        duration_seconds=round(time.monotonic() - started, 1),
    )
    # Written before every return below, so the verdict survives a truncated terminal, a
    # closed pager, or a pipe that reports its own exit status instead of this one.
    write_report(report, args.report)
    print(f"{len(chosen)} mutants in {report['duration_seconds']:.0f}s")
    print(f"verdict `{report['verdict']}` written to {args.report}\n")

    if report["leaked"]:
        print(f"!! source left modified: {', '.join(report['leaked'])}")
        print("!! run `git checkout --` on those paths before doing anything else.")
        print("!! this run is void: later mutants may have been caught by the leftover defect.")
        return report["exit_code"]

    if report["survivors"]:
        print(f"{len(report['survivors'])} survived: {', '.join(report['survivors'])}")
        print("A surviving mutant is a hole in the layer that claims that ground.")
        return report["exit_code"]

    print(f"all {len(chosen)} caught by the layer expected to catch them")
    if report["unvouched_for"]:
        print()
        print(f"!! but this run cannot vouch for: {', '.join(report['unvouched_for'])}")
        print("!! the clean-tree check is blind to a file that was already modified, and a")
        print("!! late write means some mutant ran against source nobody chose. Diff those")
        print("!! paths by hand, or commit and re-run, before believing the catches above.")
    return report["exit_code"]


if __name__ == "__main__":
    raise SystemExit(main())
