"""Break the code on purpose, and check the right layer notices.

    uv run python -m tests.mutation
    uv run python -m tests.mutation --list
    uv run python -m tests.mutation -k rest-gap

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
DOMAIN = "roster_replan/domain.py"

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
    survivors = []
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
        if not caught:
            survivors.append(mutant.name)

    print()
    leaked = _dirty(touched) - already
    if leaked:
        print(f"!! source left modified: {', '.join(sorted(leaked))}")
        print("!! run `git checkout --` on those paths before doing anything else.")
        return 2

    if survivors:
        print(f"{len(survivors)} survived: {', '.join(survivors)}")
        print("A surviving mutant is a hole in the layer that claims that ground.")
        return 1
    print(f"all {len(chosen)} caught by the layer expected to catch them")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
