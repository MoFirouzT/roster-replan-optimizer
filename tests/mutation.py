"""Break the code on purpose, and check the right layer notices.

    uv run python -m tests.mutation
    uv run python -m tests.mutation --list
    uv run python -m tests.mutation -k rest-gap

Every run writes its verdict to `tests/mutation-report.json` as well as to stdout, and the
report is the copy to trust. A full run takes tens of minutes, and reading its result through
a pipe has twice destroyed it: `tail` truncates the per-mutant lines and reports *its own*
exit status, so a run that leaked a mutated file into the working tree read as a clean pass.
`jq .verdict tests/mutation-report.json` answers the only question that matters first.

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

**Not part of the normal suite.** It rewrites source files and takes minutes, so it is run
deliberately -- when a test layer is added, or when one is about to be trusted.
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
COMPILED = "roster_replan/compiled.py"
MILP = "benchmarks/milp.py"
EXPLAIN = "roster_replan/explain.py"
PROSE = "roster_replan/prose.py"
WHATIF = "roster_replan/whatif.py"
PROFILE = "roster_replan/profile.py"
CORE = "roster_replan/core.py"
CONTRACTS = "roster_replan/service/contracts.py"
DOMAIN = "roster_replan/domain.py"
NL = "roster_replan/nl.py"
NL_EVAL = "benchmarks/nl_eval.py"

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
    # --- The T3 boundary -------------------------------------------------------------
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
    # --- The compiled-model cache ----------------------------------------------------
    # Every defect here returns a legal, plausible roster that answers the wrong question:
    # a stale objective, or a model built from a payload before the disruption. Nothing in
    # a status code, a violation count or a gap would show it.
    Mutant(
        "cache-blind-to-unavailability",
        "cache",
        COMPILED,
        '            f"{[(i.start, i.end) for i in person.unavailability]};"',
        '            f"{[]};"',
        "tests/test_cache.py",
    ),
    Mutant(
        "cache-keeps-a-stale-hint",
        "cache",
        COMPILED,
        "    model.clear_hints()",
        "    pass",
        "tests/test_cache.py",
    ),
    Mutant(
        "cache-blind-to-absences",
        "cache",
        COMPILED,
        '            f"{[(i.start, i.end) for i in person.absences]};"',
        '            f"{[]};"',
        "tests/test_cache.py",
    ),
    Mutant(
        "cache-ignores-the-incumbent",
        "cache",
        COMPILED,
        '        parts.append(";".join(map(str, sorted(instance.incumbent))))',
        "        pass",
        "tests/test_cache.py",
    ),
    Mutant(
        "cache-is-unbounded",
        "cache",
        COMPILED,
        "        if len(self._entries) > self.capacity:",
        "        if False:",
        "tests/test_cache.py",
    ),
    Mutant(
        "cache-leaks-across-tenants",
        "cache",
        COMPILED,
        "        key = (tenant, fingerprint(instance))",
        "        key = (\"-\", fingerprint(instance))",
        "tests/test_cache.py",
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
        "    baseline = _measure(instance, seed=seed, time_limit=time_limit)",
        "    baseline = _measure(instance, seed=seed + 1, time_limit=time_limit)",
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
    # A `.env` that overrides an exported key bills the wrong account, and looks like
    # nothing at all -- the run succeeds, against credentials the caller did not choose.
    Mutant(
        "nl-eval-env-file-overrides-the-shell",
        "nl",
        NL_EVAL,
        "        if not key or not value or key in environ:",
        "        if not key or not value:",
        "tests/test_nl.py",
    ),
    Mutant(
        "studies-patterns-skip-the-legality-check",
        "studies",
        PATTERNS,
        "        if _legal(instance, employee, pattern):\n            patterns.append(pattern)",
        "        if True:\n            patterns.append(pattern)",
        "tests/test_studies.py",
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
        time.sleep(0.2 * (attempt + 1))
        if path.read_text() == original:
            return
    raise RuntimeError(
        f"could not restore {path}: something else is writing to it. Run "
        f"`git checkout -- {path}` and turn off format-on-save before retrying."
    )


REPORT = _HERE / "mutation-report.json"


def summarise(results: list[dict], *, leaked: list[str], skipped: list[str], full: bool) -> dict:
    """The run's verdict, as data. Pure, so the part that can be wrong is testable.

    **The verdict does not live in stdout.** A run takes tens of minutes and its result was
    twice read through a pipe that swallowed it: `tail` truncated the per-mutant lines *and*
    reported its own exit status, so a run that leaked a mutated file into the working tree
    read as a clean pass. The report is written before any of the return paths, so a
    truncated terminal, a killed pager or a lost scrollback costs nothing.

    **A leak outranks survivors**, matching what the exit codes have always said. A run that
    left a mutation behind cannot be trusted about anything that ran after it: the following
    mutants' catcher tests may have failed on the leftover defect rather than on their own,
    and would be scored as caught for the wrong reason. That is a void run, not a passing
    one with a caveat.
    """
    survivors = [r["name"] for r in results if not r["caught"]]
    if leaked:
        verdict, exit_code = "leaked", 2
    elif survivors:
        verdict, exit_code = "survivors", 1
    else:
        verdict, exit_code = "clean", 0

    return {
        "verdict": verdict,
        "exit_code": exit_code,
        "trustworthy": verdict != "leaked",
        "finished_at": datetime.datetime.now(datetime.timezone.utc).isoformat(timespec="seconds"),
        "selected": len(results),
        "caught": sum(1 for r in results if r["caught"]),
        "survivors": survivors,
        "leaked": sorted(leaked),
        # Files this run could not vouch for, because they were already modified when it
        # started. A mutation left in one of these is invisible to the clean-tree check.
        "unchecked_because_already_modified": sorted(skipped),
        "catcher_only": not full,
        "mutants": results,
    }


def write_report(report: dict, path: pathlib.Path = REPORT) -> pathlib.Path:
    path.write_text(json.dumps(report, indent=2) + "\n")
    return path


def _dirty(paths: list[str]) -> set[str]:
    """Which of these paths git already considers modified."""
    result = subprocess.run(
        ["git", "status", "--porcelain", "--", *paths],
        cwd=ROOT, capture_output=True, text=True,
    )
    return {line[3:].strip() for line in result.stdout.splitlines() if line.strip()}


def run(mutant: Mutant, *, full: bool) -> tuple[bool, list[str], str]:
    """Apply, test, restore. Returns (caught, failing tests, note)."""
    path = mutant.target()
    original = path.read_text()
    if original.count(mutant.old) != 1:
        return False, [], f"anchor matched {original.count(mutant.old)} times, so nothing was tested"

    path.write_text(original.replace(mutant.old, mutant.new, 1))
    try:
        target = "tests" if full else mutant.catcher
        result = subprocess.run(
            [sys.executable, "-m", "pytest", target, "-q", "--no-header", "--tb=no", "-p",
             "no:cacheprovider"],
            cwd=ROOT, capture_output=True, text=True, timeout=1800,
        )
    finally:
        _restore(path, original)

    failed = _failed_tests(result.stdout)
    note = ""
    if not failed and result.returncode != 0:
        note = "the target failed without a test failure -- a collection or import error"
    return bool(failed), failed, note


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

    print(f"{len(chosen)} mutants; each expects its own layer to object.\n")
    results = []
    for mutant in chosen:
        caught, failed, note = run(mutant, full=args.full)
        status = "CAUGHT" if caught else "SURVIVED"
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
            }
        )

    print()
    report = summarise(
        results,
        leaked=sorted(_dirty(touched) - already),
        skipped=sorted(already),
        full=args.full,
    )
    # Written before every return below, so the verdict survives a truncated terminal, a
    # closed pager, or a pipe that reports its own exit status instead of this one.
    write_report(report, args.report)
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
    return report["exit_code"]


if __name__ == "__main__":
    raise SystemExit(main())
