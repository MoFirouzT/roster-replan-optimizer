"""The committed benchmark set.

Two jobs, and they fail for different reasons.

**The manifest is a golden record** in the sense `D-067` established: committed numbers,
so a change to the generator or the solver arrives as a reviewable diff rather than as a
silently different benchmark. The split between the `week` and `incumbent` fingerprints is
what makes the diff say *which* moved.

**The set has to span the axes it claims to span.** A benchmark set that is really twelve
copies of one instance passes every consistency check ever written. The tests below assert
the distribution, not the mechanism: instance size varies, tightness reaches both ends,
every event type appears, and every case poses a question worth asking.
"""

from __future__ import annotations

import dataclasses

import pytest

from benchmarks.generator import EVENTS
from benchmarks.suite import (
    CLASSES,
    GENERATOR_VERSION,
    MANIFEST_PATH,
    SEEDS,
    build,
    case_names,
    entry,
    load,
    manifest,
    portable,
)
from roster_replan.model import exclusions
from roster_replan.validation import validate_instance


@pytest.fixture(scope="module")
def committed() -> dict:
    return load()


@pytest.fixture(scope="module")
def rebuilt() -> dict:
    """Every committed case, regenerated once and shared across the module.

    Seventy-two solves. Cheap enough at these sizes to run every time, and a set that is
    only checked on demand is one that drifts.
    """
    return {case: build(case) for case in case_names()}


# --- The manifest is a golden record ------------------------------------------------


def test_the_generated_half_of_the_manifest_matches_regeneration(committed):
    """The instances themselves, which are the same on any machine (`D-117`).

    `week` digests the base instance before anything is solved, and it is built from
    `random.Random(seed)` and exact floats, so a generator change moves it and nothing else
    does. This is the half of `D-074`'s split that travels, and it is the half that
    actually answers "did the instances move" — the question the manifest exists for.

    On failure, regenerate deliberately and justify the diff:

        uv run python -m benchmarks.suite --write
    """
    current = manifest()
    assert committed["generator_version"] == current["generator_version"]
    assert {case: portable(e) for case, e in committed["cases"].items()} == {
        case: portable(e) for case, e in current["cases"].items()
    }, (
        f"{MANIFEST_PATH.name} is stale: the generated instances moved. Regenerate it, "
        f"bump GENERATOR_VERSION, and write a decisions.md entry."
    )


def test_the_solved_half_of_the_manifest_matches_regeneration(committed):
    """The whole manifest, including everything downstream of a solve.

    `D-117` marked this `machine`, because the optimum was degenerate and the roster that
    came back was a property of the search path — four solver seeds on one instance gave
    the same objective and four different rosters, so the committed digests were an artifact
    of the ortools build that wrote them.

    **`D-119` removed the reason.** The roster is now a function of the model: the optimal
    value is pinned and a canonical criterion picks a single point on the optimal face, and
    degeneracy across this set measures zero on both cold weeks and replans. So the mark
    comes off, and this test is what says whether that holds on a *different binary* rather
    than merely a different seed (`D-121`). If it fails in CI, the canonical optimum does
    not travel and `D-119` bought reproducibility on one machine only.
    """
    assert committed == manifest(), (
        f"{MANIFEST_PATH.name} is stale. If the change was intended, regenerate it, bump "
        f"GENERATOR_VERSION when the generator moved, and write a decisions.md entry."
    )


def test_manifest_covers_exactly_the_declared_cases(committed):
    assert sorted(committed["cases"]) == sorted(case_names())
    assert len(case_names()) == len(CLASSES) * len(SEEDS)


def test_manifest_records_the_generator_version(committed):
    """A manifest whose version does not track the generator cannot say whether an old
    result is comparable with a new one."""
    assert committed["generator_version"] == GENERATOR_VERSION


def test_the_two_fingerprints_move_independently(rebuilt):
    """The split is what makes a stale manifest diagnostic rather than merely loud.

    Counting distinct hashes across the set cannot show this: the incumbent is a
    deterministic function of the week and the seed, so the two counts match exactly and
    would match just as well if one field were a copy of the other. The claim has to be
    tested by moving each input on its own.
    """
    scenario = rebuilt["headline/0"]
    base = entry(scenario)

    # A different solved roster: same generated week, different incumbent.
    resolved = dataclasses.replace(
        scenario, incumbent=frozenset(sorted(scenario.incumbent)[1:])
    )
    assert entry(resolved)["week"] == base["week"]
    assert entry(resolved)["incumbent"] != base["incumbent"]

    # A different generated week, incumbent untouched.
    regenerated = dataclasses.replace(
        scenario,
        base=dataclasses.replace(
            scenario.base, open_shifts=scenario.base.open_shifts[:-1]
        ),
    )
    assert entry(regenerated)["week"] != base["week"]
    assert entry(regenerated)["incumbent"] == base["incumbent"]


# --- The set is well-formed ---------------------------------------------------------


def test_every_committed_case_is_a_valid_payload(rebuilt):
    for case, scenario in rebuilt.items():
        assert validate_instance(scenario.instance) == [], case
        assert validate_instance(scenario.base) == [], case


def test_every_case_poses_a_question(rebuilt):
    """A scenario whose event damaged nothing scores as a flawless repair by every
    method, which flatters all four equally and measures none of them."""
    unharmed = [case for case, s in rebuilt.items() if entry(s)["damage"] == 0]

    assert unharmed == []


# --- The set spans what it claims to span -------------------------------------------


def test_instance_size_varies(rebuilt):
    """`D-071`: low demand closes shift instances. If every case runs the full grid, the
    only thing varying across the set is headcount, and a solve-time curve over tightness
    would be a curve over nothing."""
    sizes = {len(s.instance.open_shifts) for s in rebuilt.values()}

    assert len(sizes) > 1


def test_tightness_reaches_both_ends(rebuilt):
    """`D-060`: the metrics only diverge where there is slack. A set clustered at one
    tightness would report "the metrics agree" as a property of the set."""
    ratios = [s.tightness.demand_ratio for s in rebuilt.values()]

    assert min(ratios) < 0.45
    assert max(ratios) > 0.85


def test_every_event_type_appears(rebuilt):
    assert {s.params.event for s in rebuilt.values()} == set(EVENTS)


def test_both_notice_bands_are_exercised_on_the_damaged_shifts(rebuilt):
    """D2 is publication state times a notice multiplier with a step at 24h (`D-006`).

    Measured on the shifts the event actually broke, which is where the multiplier gets
    applied. An earlier version looked at every open shift in the horizon and passed
    vacuously: on any seven-day week some shift is more than a day away, so the assertion
    held whatever the events did.

    Even measured properly this is a floor, not a guarantee that the notice axis is well
    covered -- a single Saturday event reaches shifts on both sides of the 24h line, so
    the set spans both bands without `early-notice`. That class earns its place by making
    long notice *systematic* rather than incidental: without it every long-notice case is
    an accident of which shift the event happened to hit, and the D2 study would be
    reading a handful of stragglers.
    """
    bands = set()
    for scenario in rebuilt.values():
        instance = scenario.instance
        excluded = exclusions(instance)
        for employee, day, shift in scenario.incumbent:
            if (employee, day, shift) in excluded:
                bands.add(instance.notice_hours(day, shift) < 24.0)

    assert bands == {True, False}, (
        "every damaged shift falls in one notice band, so D2's multiplier is constant "
        "across the set and the shipped metric reduces to D1"
    )


def test_the_set_holds_both_staffable_and_chronically_short_weeks(rebuilt):
    """Both are real tenants. Pooling them would average a repair question together with
    a capacity question, so the set carries both and `base_shortfall` marks which."""
    shortfalls = [s.base_shortfall for s in rebuilt.values()]

    assert min(shortfalls) == 0
    assert max(shortfalls) > 0


def test_classes_differing_only_in_the_event_share_a_base_week(rebuilt):
    """The controlled comparison the event axis depends on.

    `headline`, `multi-absence`, `demand-spike` and `withdrawal` differ from each other in
    one field. At a given seed they must be the *same published week*, or a difference in
    results is a difference in instances and the event axis measures nothing.
    """
    for seed in SEEDS:
        weeks = {
            name: entry(rebuilt[f"{name}/{seed}"])["week"]
            for name in ("headline", "multi-absence", "demand-spike", "withdrawal")
        }
        assert len(set(weeks.values())) == 1, f"seed {seed} differs across events: {weeks}"


def test_early_notice_is_the_same_week_as_headline_at_a_different_hour(rebuilt):
    """The notice axis has to vary notice and nothing else."""
    for seed in SEEDS:
        headline = rebuilt[f"headline/{seed}"]
        early = rebuilt[f"early-notice/{seed}"]

        assert entry(headline)["week"] == entry(early)["week"]
        assert early.instance.now < headline.instance.now
