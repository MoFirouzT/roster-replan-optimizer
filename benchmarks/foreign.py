"""Foreign instances: rosters this project did not produce.

    uv run python -m benchmarks.foreign --fetch     # download once, verified
    uv run python -m benchmarks.foreign             # report what was imported

`benchmarks.md` names the weak point of every number in this repo, and it has not moved
since T2: **the incumbent is solved by the system under test.** A replan is measured against
a roster this model would produce, which cannot show that it repairs what real planners
publish. `capture.md` was written to close that with a captured corpus, and is blocked on an
authorization this project does not control.

This is the half that is not blocked. The nurse-rostering benchmark instances at
schedulingbenchmarks.org ship with **published solutions** — rosters produced by other
people's solvers optimising an objective this project does not implement. As incumbents they
are exactly what the generator cannot make: foreign.

## Nothing here is committed, and that is a licence decision

The site states no licence, no copyright and no terms. "No licence" means default copyright
rather than public domain, so **the data is fetched and never redistributed**. What is
committed is `foreign.json`: the URLs and their SHA-256. That is `D-073`'s pattern — the
benchmark manifest already commits fingerprints instead of payloads — so a fetched copy is
verified rather than trusted, and `README.md`'s "all data committed here is synthetic" stays
true (`D-125`).

## The mapping, and the three places it is a decision

Their model is day-based with a "cannot follow" relation between shifts; this one is
clock-based. The clock exists in the `.ros` form of each instance, so rest gaps are computed
from their own start times rather than from invented ones.

**Their `MaxTotalMinutes` is `max_hours_this_period`** and nothing else. Deriving a weekly
rate from it was the first version of this importer and it was wrong in a way worth keeping
on the record: a flat weekly average forbids precisely the uneven spending a pool permits, so
it reported 60-80% of every published roster as illegal. That is `D-123`'s finding arriving
from the outside. `max_hours_this_week` is set to the statutory ceiling instead, where it
cannot bind and their own limit does.

**Days off are dropped, not translated.** Theirs forbids an assignment *on* a day; ours is
interval overlap, and a night shift starting at 22:00 the evening before spills six hours
into it. Translating a day off into an interval therefore reports every such night shift as
`R-AVAIL` — the start-day attribution convention `rules.md` fixes, colliding with a naive
translation. They are omitted rather than approximated, and `_days_off` records them so a
caller can see what was dropped.

**`max_consecutive_days` is theirs at its most permissive.** Ours is per instance and theirs
is per employee, so the loosest is used and a violation means someone exceeded even that.

## What this cannot support

Their objective is a weighted sum of soft preferences — shift-on and shift-off requests,
weekend counts, minimum consecutive days off — and **none of it is imported**. Their rosters
are optimal for a goal this project never scores, so no claim about solution quality can be
made from them, and their published objective values are not comparable with anything here.
They are incumbents. That is the whole of the claim.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import pathlib
import urllib.request
import xml.etree.ElementTree as ET
import zipfile

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
from roster_replan.validation import ABSOLUTE_DAILY_CEILING_HOURS, ABSOLUTE_WEEKLY_CEILING_HOURS

HERE = pathlib.Path(__file__).resolve().parent
CACHE = HERE / ".foreign"
SOURCES_PATH = HERE / "foreign.json"

# The Belgian parameters these rosters are being judged against. They are this project's
# defaults rather than anything the source states -- the source has no rest rule at all,
# which is the point of measuring.
PARAMS = dict(min_rest_hours=11.0, min_weekly_rest_hours=35.0, min_period_hours=3.0)

SKILL = "nurse"

# Instances 1-13 are two to four weeks. Everything past 13 runs six weeks to a year, which
# is a different regime and outside anything this project claims; they are fetched with the
# rest and left for a study that wants them.
IMPORTABLE = tuple(range(1, 14))


def sources() -> dict:
    return json.loads(SOURCES_PATH.read_text())


def fetch(*, force: bool = False) -> None:
    """Download each archive and verify it against the committed digest."""
    CACHE.mkdir(exist_ok=True)
    for name, entry in sources()["archives"].items():
        target = CACHE / name
        if target.exists() and not force:
            print(f"{name}: already present")
        else:
            print(f"{name}: fetching {entry['url']}")
            with urllib.request.urlopen(entry["url"]) as response:  # noqa: S310
                target.write_bytes(response.read())

        digest = hashlib.sha256(target.read_bytes()).hexdigest()
        if digest != entry["sha256"]:
            target.unlink()
            raise SystemExit(
                f"{name} does not match the committed digest and has been deleted.\n"
                f"  expected {entry['sha256']}\n  got      {digest}\n"
                f"The upstream file changed, or the download was corrupted. Either way this "
                f"is not the data the study was run against."
            )
        print(f"{name}: verified {digest[:16]}...")

        with zipfile.ZipFile(target) as archive:
            archive.extractall(CACHE / target.stem)


def available() -> bool:
    return (CACHE / "instances").exists() and (CACHE / "solutions").exists()


def _instance_dir() -> pathlib.Path:
    return CACHE / "instances" / "instances1_24"


def _solution_dir() -> pathlib.Path:
    return CACHE / "solutions" / "instances1_24solutions"


def _sections(path: pathlib.Path) -> dict[str, list[str]]:
    out: dict[str, list[str]] = {}
    current = None
    for raw in path.read_text().splitlines():
        line = raw.strip()
        if not line or line.startswith("#"):
            continue
        if line.startswith("SECTION_"):
            current = line
            out[current] = []
        elif current:
            out[current].append(line)
    return out


def _start_hours(name: str) -> dict[str, float]:
    """Shift start times, which the plain-text form does not carry."""
    root = ET.parse(_solution_dir() / f"{name}.ros").getroot()
    hours = {}
    for shift in root.find("ShiftTypes"):
        hour, minute = (int(part) for part in shift.find("StartTime").text.strip().split(":"))
        hours[shift.get("ID")] = hour + minute / 60.0
    return hours


def load(number: int) -> tuple[Instance, frozenset, dict[str, list[int]]]:
    """One instance, its published roster, and the days off that were dropped."""
    name = f"Instance{number}"
    section = _sections(_instance_dir() / f"{name}.txt")
    days = int(section["SECTION_HORIZON"][0])
    starts = _start_hours(name)

    ids = [row.split(",")[0] for row in section["SECTION_SHIFTS"]]
    index = {sid: position for position, sid in enumerate(ids)}
    shift_types = tuple(
        ShiftType(
            label=sid,
            start_hour=starts[sid],
            span_hours=int(row.split(",")[1]) / 60.0,
            break_hours=0.0,
        )
        for sid, row in zip(ids, section["SECTION_SHIFTS"])
    )

    days_off: dict[str, list[int]] = {}
    for row in section.get("SECTION_DAYS_OFF", []):
        parts = row.split(",")
        days_off[parts[0]] = [int(day) for day in parts[1:] if day]

    people, order, consecutive = [], {}, []
    for row in section["SECTION_STAFF"]:
        parts = row.split(",")
        consecutive.append(int(parts[4]))
        order[parts[0]] = len(people)
        people.append(
            Employee(
                name=parts[0],
                contract="salaried",
                skills=frozenset({SKILL}),
                # The statutory ceilings, so only limits the source actually states can bind.
                max_hours_this_week=ABSOLUTE_WEEKLY_CEILING_HOURS,
                max_daily_hours=ABSOLUTE_DAILY_CEILING_HOURS,
                max_hours_this_period=int(parts[2]) / 60.0,
            )
        )

    required: dict[tuple[int, int], int] = {}
    for row in section["SECTION_COVER"]:
        day, sid, need = row.split(",")[:3]
        required[int(day), index[sid]] = int(need)

    instance = Instance(
        days=days,
        shift_types=shift_types,
        employees=tuple(people),
        open_shifts=tuple(
            OpenShift(day=day, shift=shift, required=need)
            for (day, shift), need in sorted(required.items())
        ),
        params=RuleParams(max_consecutive_days=max(consecutive), **PARAMS),
        disruption=shipped_d2(),
    )

    roster = set()
    solution = next((_solution_dir() / "Solutions" / "XML").glob(f"{name}.Solution.*.roster"))
    for employee in ET.parse(solution).getroot().findall("Employee"):
        position = order[employee.get("ID")]
        for assign in employee.findall("Assign"):
            sid = assign.find("Shift").text.strip()
            if sid in index:
                roster.add((position, int(assign.find("Day").text), index[sid]))

    return instance, frozenset(roster), days_off


def scenario(number: int, *, seed: int = 7):
    """A replan question whose incumbent nobody here produced.

    Built as a `generator.Scenario` on purpose, so a foreign incumbent flows through the
    same `methods.run` as every committed case and the comparison is the same comparison.
    What differs is one thing: `incumbent` is a published roster rather than one this
    solver returned.

    The event is the headline class — a single absence — placed on the employee with the
    most assignments on the chosen day, so it damages a roster that is actually being
    relied on rather than an idle one.
    """
    import dataclasses
    import random

    from benchmarks.generator import Scenario, ScenarioParams, measure

    instance, published, _ = load(number)
    rng = random.Random(seed)

    # Mid-horizon, so there is a pinned past and a repairable future on either side.
    day = instance.days // 2
    on_that_day = [key for key in published if key[1] == day]
    if not on_that_day:
        raise ValueError(f"Instance{number} has nobody rostered on day {day}")
    employee = rng.choice(sorted({key[0] for key in on_that_day}))

    injured = dataclasses.replace(
        instance.employees[employee],
        absences=(Interval(day * 24.0, (day + 1) * 24.0),),
    )
    employees = list(instance.employees)
    employees[employee] = injured

    disrupted = dataclasses.replace(
        instance,
        employees=tuple(employees),
        now=day * 24.0,
        incumbent=published,
        published_through=instance.days * 24.0,
    )

    required = sum(shift.required for shift in instance.open_shifts)
    return Scenario(
        name=f"foreign-{number}",
        seed=seed,
        params=ScenarioParams(days=instance.days, employees=len(instance.employees)),
        base=instance,
        incumbent=published,
        base_shortfall=max(0, required - len(published)),
        instance=disrupted,
        tightness=measure(disrupted),
    )


def study() -> None:
    """The headline claim, on incumbents this project did not produce.

    Two questions, and the second only arises where the first is answered. **Is the
    published past legal** under Belgian rules? `R-PIN-PAST` fixes everything before `now`,
    so a hard violation in that region makes the replan infeasible by construction — the
    documented "the past itself is illegal" case, which until now had no natural instance
    anywhere in this project. Where the past is clean, **does the disruption objective still
    beat a cold cost re-solve** when the roster it is preserving came from somebody else?
    """
    from benchmarks import methods
    from roster_replan.checker import check

    print(f"\n{'instance':>11} {'staff':>6} {'weeks':>6} {'past':>10} "
          f"{'cold-cost':>20} {'warm-replan':>20}")
    print(f"{'':>11} {'':>6} {'':>6} {'':>10} {'disruption':>10} {'changes':>9} "
          f"{'disruption':>10} {'changes':>9}")

    for number in IMPORTABLE:
        case = scenario(number)
        instance = case.instance
        in_past = [
            v
            for v in check(case.incumbent, instance)
            if not v.soft and v.day is not None and instance.is_past(v.day, v.shift or 0)
        ]
        weeks = instance.days // DAYS_PER_WEEK
        staff = len(instance.employees)

        if in_past:
            print(
                f"Instance{number:<3} {staff:>6} {weeks:>6} {'ILLEGAL':>10} "
                f"  {len(in_past)} hard violation(s) before `now`; a replan cannot repair a "
                f"pinned past"
            )
            continue

        outcomes = {m: methods.run(m, case, time_limit=30.0) for m in ("cold-cost", "warm-replan")}
        cost, replan = outcomes["cold-cost"], outcomes["warm-replan"]
        print(
            f"Instance{number:<3} {staff:>6} {weeks:>6} {'clean':>10} "
            f"{cost.disruption:>10} {cost.changes:>9} {replan.disruption:>10} "
            f"{replan.changes:>9}"
        )


def scale(*, budget: float = 30.0) -> None:
    """How far does this model go, on instances nobody sized for it?

    Every performance claim in this repo is measured on 8-25 employees over one week, and
    `D-104` retired LNS on the grounds that nothing ever fails to prove optimality. Both are
    statements about a distribution this project generated for itself. These instances run
    to 150 employees over 52 weeks and were built by other people for other purposes, which
    is the only way to find out where the model stops.

    The **replan** case is measured rather than the cold one, because that is what the
    service does: the published roster pins the past and prices the future, which is the
    regime the whole project is about. A cold solve of a year for 150 people is a different
    question and not this one.
    """
    import time

    from roster_replan.model import build, solve

    print(f"\n{'instance':>11} {'staff':>6} {'weeks':>6} {'shifts':>7} {'vars':>9} "
          f"{'cons':>9} {'build s':>9} {'search s':>9} {'status':>11} {'canon':>6}",
          flush=True)

    for number in range(1, 25):
        try:
            case = scenario(number)
        except Exception as error:  # noqa: BLE001
            print(f"Instance{number:<3} could not build a scenario: {type(error).__name__}")
            continue

        instance = case.instance
        started = time.perf_counter()
        try:
            built = build(instance)
        except MemoryError:
            print(f"Instance{number:<3} {len(instance.employees):>6} "
                  f"{instance.days // DAYS_PER_WEEK:>6}  ran out of memory building the model",
                  flush=True)
            continue
        build_seconds = time.perf_counter() - started

        answer = solve(instance, built=built, time_limit=budget)
        status = getattr(answer, "status", "INFEASIBLE" if isinstance(answer, list) else "?")
        canonical = getattr(answer, "canonical", False)
        search = getattr(answer, "search_seconds", 0.0)

        print(
            f"Instance{number:<3} {len(instance.employees):>6} "
            f"{instance.days // DAYS_PER_WEEK:>6} {len(instance.shift_types):>7} "
            f"{len(built.model.proto.variables):>9} {len(built.model.proto.constraints):>9} "
            f"{build_seconds:>9.2f} {search:>9.2f} {status:>11} "
            f"{'yes' if canonical else 'no':>6}",
            flush=True,
        )


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--fetch", action="store_true", help="download and verify the archives")
    parser.add_argument("--force", action="store_true", help="re-download even if present")
    parser.add_argument("--study", action="store_true", help="run the replan comparison")
    parser.add_argument("--scale", action="store_true", help="how far the model goes")
    args = parser.parse_args()

    if args.fetch:
        fetch(force=args.force)
        return 0

    if not available():
        print("no data: run `uv run python -m benchmarks.foreign --fetch` first")
        return 1

    from roster_replan.checker import check

    print(f"{'instance':>11} {'staff':>6} {'weeks':>6} {'assigned':>9} {'hard':>5}  rules")
    for number in IMPORTABLE:
        instance, roster, _ = load(number)
        hard = [v for v in check(roster, instance) if not v.soft]
        rules = sorted({v.rule for v in hard})
        print(
            f"Instance{number:<3} {len(instance.employees):>6} "
            f"{instance.days // DAYS_PER_WEEK:>6} {len(roster):>9} {len(hard):>5}  "
            f"{', '.join(rules) if rules else 'none'}"
        )

    if args.study:
        study()
    if args.scale:
        scale()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
