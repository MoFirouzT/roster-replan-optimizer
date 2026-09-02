"""Foreign instances: rosters this project did not produce.

    uv run python -m benchmarks.foreign --fetch     # download once, verified
    uv run python -m benchmarks.foreign             # report what was imported

`benchmarks.md` names the weak point of every number in this repo, and it has not moved: **the incumbent is
solved by the system under test.** A replan is measured against a roster this model would
produce, which cannot show that it repairs what real planners
publish. Capture and replay was written to close that with a captured corpus and is blocked on an
authorization this project does not control (`specs/README.md`).

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

**Days off are imported, and the collision that used to stop them is now a rule** (`D-142`).
Theirs forbids an assignment *on* a day; `R-AVAIL` is interval overlap, and a night shift
starting at 22:00 the evening before spills six hours into it — so translating a day off into
an interval reported every such night shift as `R-AVAIL`. They were dropped for that reason
from `D-125` until `R-DAY-OFF` gave the day-indexed reading a rule of its own. `Unencoded`
still carries them, because a record of what the mapping did outlives the reason it did it.

**`max_consecutive_days` is theirs, per employee.** It was the loosest limit in the workforce
until `R-CONSEC-DAYS` gained a per-employee override (`D-136`), which is an approximation this
importer no longer has to make.

**Their rest rule is stricter than the one imposed on them, and that is a check rather than a
coincidence** (`D-132`). The `.txt` form states no rest gap, which is why this importer applies
Belgian parameters; the `.ros` form does, and it is `MinRestTime` 840 minutes — 14 hours, on
every importable instance, against the 11 this project imposes. `R-REST-GAP` therefore cannot
fire on a published roster, and it never does. An importer that mistranslated the clock would
show up here immediately, so the empty column is evidence and not an absence of it.

## What is imported and not encoded

Everything their format states is now read (`D-132`), and what this model has no field for is
carried on `Unencoded` rather than discarded. That is a deliberate half-step: importing a
parameter is cheap and reversible, encoding one is a rule in two independent readings.

The split their format makes is worth stating, because it is not the split this project would
have guessed. **Their per-employee limits carry no weight and are hard** — `MaxShifts`,
`MinTotalMinutes`, `MaxConsecutiveShifts`, `MinConsecutiveShifts`, `MinConsecutiveDaysOff`,
`MaxWeekends`, and the "cannot follow" relation between shift types. Their *objective* is
narrow: shift-on and shift-off requests, each with a weight, plus per-slot under- and
over-cover weights. The `.ros` form settles it — a limit with no `weight` attribute is a
constraint, and only requests and cover carry one.

## What this still cannot support

**Solution quality.** Their objective is imported and not yet scored, so their published
objective values remain incomparable with anything here and no claim in this module depends on
them. The rosters are used as incumbents. Scoring their objective is the next step and is what
would make the comparison a two-way one.

**Their weekend.** `MaxWeekends` counts Saturday-Sunday pairs, and every instance starts on a
Monday, so days 5 and 6 of each week are the weekend. This project's domain has no calendar at
all — `domain.py` is explicit that a week is a position in the horizon and never a Monday — so
that mapping is a fact about their data recorded here, not a convention this model holds.
"""

from __future__ import annotations

import argparse
import dataclasses
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
# defaults rather than anything the source states: the `.txt` form states no rest rule and no
# weekly rest, which is the point of measuring. Their `.ros` form does state a daily one --
# `MinRestTime` 840 minutes, read back as `stated_rest_hours` below -- and it is *stricter*
# than this, so `R-REST-GAP` cannot fire on a published roster and never does (`D-132`).
PARAMS = dict(min_rest_hours=11.0, min_weekly_rest_hours=35.0, min_period_hours=3.0)

SKILL = "nurse"

# Their horizon starts on a Monday, stated in the instance files and confirmed by `StartDate`
# in every `.ros`. So these are the weekend days of each week, and this constant exists to
# read `MaxWeekends` -- it is a fact about their data, never a convention this model holds.
# `domain.py` is explicit that a week here is a position in the horizon and never a Monday.
WEEKEND_DAYS = (5, 6)

# Instances 1-13 are two to four weeks. Everything past 13 runs six weeks to a year, which
# is a different regime and outside anything this project claims; they are fetched with the
# rest and left for a study that wants them.
IMPORTABLE = tuple(range(1, 14))


@dataclasses.dataclass(frozen=True, slots=True)
class Limit:
    """One employee's limits, as their format states them.

    Every field here is **hard** in their formulation: the `.ros` form gives a weight to
    exactly the things in their objective, and none of these carries one.

    `max_shifts` is per shift type, keyed by label, because their `D=14` form is a cap on how
    many of *that* shift someone may work rather than on shifts in total.
    """

    max_shifts: dict[str, int]
    max_total_minutes: int
    min_total_minutes: int
    max_consecutive_shifts: int
    min_consecutive_shifts: int
    min_consecutive_days_off: int
    max_weekends: int


@dataclasses.dataclass(frozen=True, slots=True)
class Request:
    """A shift someone asked for or asked to avoid, with what their objective pays for it.

    `weight` is theirs and is on their scale, which is not this project's scale and is not
    converted here. Two of these plus the cover weights are their whole objective.
    """

    employee: int
    day: int
    shift: int
    weight: int


@dataclasses.dataclass(frozen=True, slots=True)
class Unencoded:
    """What their instance states that this model does not encode (`D-132`).

    Carried rather than discarded, and named for what it is: importing a parameter is cheap
    and reversible, and encoding one is a rule in two independent readings plus a mutant. The
    parse is the half that can be done without deciding anything.

    `days_off` is the one member that is **dropped rather than merely unencoded**, and for a
    stated reason rather than a missing field: theirs forbids an assignment *on* a day, ours is
    interval overlap, and a night shift starting at 22:00 the evening before spills into it. It
    keeps the shape it always had -- employee name to day numbers -- because callers read it.
    """

    limits: tuple[Limit, ...]
    on_requests: tuple[Request, ...]
    off_requests: tuple[Request, ...]

    # Per slot, keyed as `(day, shift)`: what their objective charges for one position short
    # and one position over. Under is 100 and over is 1 across this set, which is the same
    # ordering `D-057`'s domination bound produces here by a different route.
    under_weight: dict[tuple[int, int], int]
    over_weight: dict[tuple[int, int], int]

    # Shift types that may not follow a given one, keyed by the shift index they follow.
    # Their day-based answer to what this project spells as a rest gap in hours.
    cannot_follow: dict[int, frozenset[int]]

    # Their own daily rest rule, from the `.ros` form. Stated in hours so it compares directly
    # with `PARAMS["min_rest_hours"]`, and `None` if an instance ever omits it.
    stated_rest_hours: float | None

    days_off: dict[str, list[int]]


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


def _stated_rest_hours(name: str) -> float | None:
    """Their own daily rest rule, which only the `.ros` form carries.

    One number for the whole instance or none: it is stated on the `All` contract across this
    set. A set with two different values would be a per-contract rule this cannot represent,
    so it returns `None` rather than picking one.
    """
    root = ET.parse(_solution_dir() / f"{name}.ros").getroot()
    minutes = {int(node.text.strip()) for node in root.iter("MinRestTime")}
    if len(minutes) != 1:
        return None
    return minutes.pop() / 60.0


def _limits(rows: list[str]) -> tuple[Limit, ...]:
    """`SECTION_STAFF`, in full. Six of its seven columns had no reader until `D-132`.

    `MaxShifts` is `D=14|N=6` — per shift type, `|` separated — and not a total, which is why
    it is a mapping rather than an integer.
    """
    limits = []
    for row in rows:
        parts = row.split(",")
        caps = {}
        for entry in parts[1].split("|"):
            if entry:
                label, cap = entry.split("=")
                caps[label] = int(cap)
        limits.append(
            Limit(
                max_shifts=caps,
                max_total_minutes=int(parts[2]),
                min_total_minutes=int(parts[3]),
                max_consecutive_shifts=int(parts[4]),
                min_consecutive_shifts=int(parts[5]),
                min_consecutive_days_off=int(parts[6]),
                max_weekends=int(parts[7]),
            )
        )
    return tuple(limits)


def _requests(
    rows: list[str], order: dict[str, int], index: dict[str, int]
) -> tuple[Request, ...]:
    """`SECTION_SHIFT_ON_REQUESTS` and its off twin, which share a layout.

    Employees and shifts are translated to this project's integer coordinates here, so a
    caller never has to hold both naming schemes at once.
    """
    return tuple(
        Request(
            employee=order[parts[0]],
            day=int(parts[1]),
            shift=index[parts[2]],
            weight=int(parts[3]),
        )
        for parts in (row.split(",") for row in rows)
        if parts[2] in index
    )


@dataclasses.dataclass(frozen=True, slots=True)
class Solution:
    """One published roster, and the objective value its publisher claims for it.

    **The value is in the file name** — `Instance1.Solution.607.roster` — which is the only
    place the archives state it. That makes it an external number this project did not choose
    and cannot quietly adjust, which is what `score_their_objective` is checked against.
    """

    number: int
    objective: int
    path: pathlib.Path


def solutions(number: int) -> tuple[Solution, ...]:
    """Every published solution for an instance, best objective first.

    Eleven of the thirteen ship more than one, and `load` used to take whichever the glob
    yielded. For an incumbent that was harmless — any published roster is equally foreign. For
    a comparison it is not: a baseline has to be named, so this orders them and `load` takes
    the best (`D-133`).
    """
    found = []
    for path in (_solution_dir() / "Solutions" / "XML").glob(f"Instance{number}.Solution.*.roster"):
        found.append(Solution(number=number, objective=int(path.stem.split(".")[-1]), path=path))
    return tuple(sorted(found, key=lambda s: s.objective))


def _published_roster(path: pathlib.Path, order: dict[str, int], index: dict[str, int]):
    roster = set()
    for employee in ET.parse(path).getroot().findall("Employee"):
        position = order[employee.get("ID")]
        for assign in employee.findall("Assign"):
            sid = assign.find("Shift").text.strip()
            if sid in index:
                roster.add((position, int(assign.find("Day").text), index[sid]))
    return frozenset(roster)


def score_their_objective(roster, instance: Instance, unencoded: Unencoded) -> int:
    """Their objective, on any roster. The whole of it (`D-133`).

    ```
    Σ_slots under × max(0, required − assigned) + over × max(0, assigned − required)
      + Σ_on_requests  weight  where the shift was not assigned
      + Σ_off_requests weight  where it was
    ```

    That is the entire function, and the brevity is the finding rather than a simplification.
    `foreign.py` used to describe their objective as *"a weighted sum of soft preferences —
    shift-on and shift-off requests, weekend counts, minimum consecutive days off"*; the
    weekend and consecutive-day terms are **constraints** in their formulation, and this
    reproduces all 26 published values without them (`D-132`, `D-133`).

    Their weights, their scale, their arithmetic. Nothing here is converted into this
    project's disruption points, because a number that has been rescaled cannot be compared
    with the one on the tin.
    """
    assigned: dict[tuple[int, int], int] = {}
    for _, day, shift in roster:
        assigned[day, shift] = assigned.get((day, shift), 0) + 1

    penalty = 0
    for open_shift in instance.open_shifts:
        slot = (open_shift.day, open_shift.shift)
        have = assigned.get(slot, 0)
        penalty += unencoded.under_weight[slot] * max(0, open_shift.required - have)
        penalty += unencoded.over_weight[slot] * max(0, have - open_shift.required)

    for request in unencoded.on_requests:
        if (request.employee, request.day, request.shift) not in roster:
            penalty += request.weight
    for request in unencoded.off_requests:
        if (request.employee, request.day, request.shift) in roster:
            penalty += request.weight
    return penalty


def their_violations(roster, instance: Instance, unencoded: Unencoded) -> list[str]:
    """Their **constraints**, checked against a roster. One reading, and deliberately so.

    This is not a second `checker.py`. `guide/rules.md`'s independence rule governs rules this
    product enforces, and none of these is one — they are somebody else's operational limits,
    read here to answer a single question before any of them is encoded: **would they bind on
    a roster this project produces?** Encoding seven rules in two readings to discover they
    change nothing would be the expensive way to learn it.

    It carries the same external check the objective does. Their published rosters satisfy
    their own constraints, so a correct implementation reports **nothing** on all 26 of them,
    and a wrong one is caught by data it did not choose (`D-134`).

    Returned as rule-name strings rather than `Violation` objects, because these have no rule
    IDs — giving them one would put them in `guide/rules.md`'s registry, which is the decision this
    measurement exists to inform rather than to pre-empt.
    """
    by_employee: dict[int, dict[int, int]] = {}
    for employee, day, shift in roster:
        by_employee.setdefault(employee, {})[day] = shift

    found = []
    for employee, limit in enumerate(unencoded.limits):
        days = by_employee.get(employee, {})
        worked = sorted(days)

        counts: dict[int, int] = {}
        for shift in days.values():
            counts[shift] = counts.get(shift, 0) + 1
        for label, cap in limit.max_shifts.items():
            index = next(
                (i for i, s in enumerate(instance.shift_types) if s.label == label), None
            )
            if index is not None and counts.get(index, 0) > cap:
                found.append("MaxShifts")

        minutes = sum(instance.shift_types[shift].work_hours * 60 for shift in days.values())
        if minutes < limit.min_total_minutes:
            found.append("MinTotalMinutes")

        # A stretch touching either end of the horizon may be the tail of a longer one
        # outside it, so a *minimum* length is judged on interior stretches only. Their own
        # solvers are given that latitude and their published rosters need it: without it
        # every one of the 26 reports a short working block, which is this rule being read
        # too strictly rather than 26 rosters being wrong. A *maximum* needs no such care —
        # a run that is too long inside the horizon is too long whatever surrounds it.
        def interior(run: list[int]) -> bool:
            return run[0] > 0 and run[-1] < instance.days - 1

        for run in _runs(worked):
            if len(run) > limit.max_consecutive_shifts:
                found.append("MaxConsecutiveShifts")
            if interior(run) and len(run) < limit.min_consecutive_shifts:
                found.append("MinConsecutiveShifts")

        for run in _runs([day for day in range(instance.days) if day not in days]):
            if interior(run) and len(run) < limit.min_consecutive_days_off:
                found.append("MinConsecutiveDaysOff")

        weekends = {
            day // DAYS_PER_WEEK for day in days if day % DAYS_PER_WEEK in WEEKEND_DAYS
        }
        if len(weekends) > limit.max_weekends:
            found.append("MaxWeekends")

        for day, shift in days.items():
            following = days.get(day + 1)
            if following is not None and following in unencoded.cannot_follow.get(shift, ()):
                found.append("Succession")

    return found


def _runs(days: list[int]) -> list[list[int]]:
    """Consecutive stretches in a sorted list of day numbers."""
    runs: list[list[int]] = []
    for day in days:
        if runs and day == runs[-1][-1] + 1:
            runs[-1].append(day)
        else:
            runs.append([day])
    return runs


def as_rules(instance: Instance, unencoded: Unencoded) -> Instance:
    """Their per-employee constraints, expressed as this project's rules (`D-137`).

    Every one of them has a registry entry now (`D-135`, `D-136`), so this is a translation
    rather than an approximation — the first time anything in this module can say that.
    `MaxConsecutiveShifts` lands on `R-CONSEC-DAYS`'s per-employee limit rather than on a
    rule of its own, which is why there are seven constraints and six field names.
    """
    labels = {shift.label: index for index, shift in enumerate(instance.shift_types)}
    people = []
    for person, limit in zip(instance.employees, unencoded.limits):
        caps = {labels[label]: cap for label, cap in limit.max_shifts.items() if label in labels}
        people.append(
            dataclasses.replace(
                person,
                # `R-DAY-OFF`, which is why these stopped being dropped (`D-142`).
                days_off=frozenset(unencoded.days_off.get(person.name, ())),
                max_weekends=limit.max_weekends,
                min_consecutive_days_off=limit.min_consecutive_days_off,
                min_consecutive_days_worked=limit.min_consecutive_shifts,
                max_shifts_per_type=caps,
                min_hours_this_period=limit.min_total_minutes / 60.0,
                max_consecutive_days=limit.max_consecutive_shifts,
            )
        )

    return dataclasses.replace(
        instance,
        employees=tuple(people),
        params=dataclasses.replace(
            instance.params,
            weekend_days=frozenset(WEEKEND_DAYS),
            forbidden_successions=frozenset(
                (earlier, later)
                for earlier, blocked in unencoded.cannot_follow.items()
                for later in blocked
            ),
            # **Their rest rule, not this project's.** Everywhere else in this module the
            # Belgian parameters are imposed deliberately, because measuring what a stricter
            # jurisdiction does to a foreign roster is the point. Here the point is the
            # opposite: a comparison against their published optimum has to run on their
            # constraints, and 11 hours where they wrote 14 is a freedom their solver did not
            # have (`D-137`).
            min_rest_hours=unencoded.stated_rest_hours or instance.params.min_rest_hours,
        ),
    )


def _cover(rows: list[str], index: dict[str, int]) -> tuple[dict, dict, dict]:
    """`SECTION_COVER`: the requirement, and the two weights their objective charges.

    The weights are theirs and are left on their scale. Converting them to this project's
    would be answering `D-057`'s bound question with somebody else's number, which is a
    decision this half deliberately does not take.
    """
    required, under, over = {}, {}, {}
    for row in rows:
        day, sid, need, under_weight, over_weight = row.split(",")[:5]
        slot = (int(day), index[sid])
        required[slot] = int(need)
        under[slot] = int(under_weight)
        over[slot] = int(over_weight)
    return required, under, over


def _successions(
    ids: list[str], rows: list[str], index: dict[str, int]
) -> dict[int, frozenset]:
    """Which shift types may not follow which, `|` separated in the third column.

    Their day-based answer to what this project spells as a rest gap in hours. Empty for a
    single-shift instance and dense for an eighteen-shift one, which is why it is worth
    importing rather than assuming away.
    """
    blocked = {}
    for sid, row in zip(ids, rows):
        forbidden = frozenset(
            index[other] for other in row.split(",")[2].split("|") if other in index
        )
        if forbidden:
            blocked[index[sid]] = forbidden
    return blocked


def load(number: int) -> tuple[Instance, frozenset, Unencoded]:
    """One instance, its published roster, and everything their format states that this model
    does not encode.

    The third member used to be the dropped days off alone. It is now an `Unencoded` carrying
    those plus their per-employee limits, their two request lists, their per-slot cover weights
    and their stated rest rule (`D-132`) — a superset, so `instance, roster, _ = load(n)` reads
    exactly as it did.
    """
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
                # Theirs, per employee, now that `R-CONSEC-DAYS` reads one (`D-136`).
                max_consecutive_days=int(parts[4]),
            )
        )

    required, under, over = _cover(section["SECTION_COVER"], index)

    instance = Instance(
        days=days,
        shift_types=shift_types,
        employees=tuple(people),
        open_shifts=tuple(
            OpenShift(day=day, shift=shift, required=need)
            for (day, shift), need in sorted(required.items())
        ),
        # The tenant-level limit is the loosest in the workforce, so it can never bind
        # where an employee's own is stricter. Every employee carries theirs above.
        params=RuleParams(max_consecutive_days=max(consecutive), **PARAMS),
        disruption=shipped_d2(),
    )

    roster = _published_roster(solutions(number)[0].path, order, index)

    unencoded = Unencoded(
        limits=_limits(section["SECTION_STAFF"]),
        on_requests=_requests(section.get("SECTION_SHIFT_ON_REQUESTS", []), order, index),
        off_requests=_requests(section.get("SECTION_SHIFT_OFF_REQUESTS", []), order, index),
        under_weight=under,
        over_weight=over,
        cannot_follow=_successions(ids, section["SECTION_SHIFTS"], index),
        stated_rest_hours=_stated_rest_hours(name),
        days_off=days_off,
    )
    return instance, frozenset(roster), unencoded


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


def compare(*, budget: float = 300.0) -> None:
    """This project's solver on their problem, judged by their published optimum (`D-137`).

    The comparison every earlier step was building towards, and it needs all three of them:
    their constraints as rules (`D-135`, `D-136`), their objective as an expression, and a
    published value to be judged against. Scoring a roster this model produced for *its own*
    objective would have measured nothing — the number would say only that the two objectives
    differ, which nobody doubted.

    **Their formulation prices overstaffing and this project forbids it.** `D-018` makes the
    coverage ceiling hard, so solving their problem exactly means relaxing that one rule — and
    relaxing a named rule for a stated reason is precisely what the assumption literals exist
    for (`guide/rules.md`: *"relaxation is explicit, per-instance and reportable, never hidden
    inside a weight"*). The `R-COVER` gates are dropped from the assumption set and nothing
    else is, so the solve answers their question rather than a neighbouring one.
    """
    import time

    from ortools.sat.python import cp_model

    from roster_replan.model import build

    print(
        f"\n{'instance':>11} {'staff':>6} {'weeks':>6} {'published':>10} {'ours':>10} "
        f"{'gap to best':>12} {'status':>10} {'search s':>9}"
    )
    for number in (2, 4, 6):
        instance, published, unencoded = load(number)
        asked = as_rules(instance, unencoded)
        built = build(asked)

        model = built.model
        model.minimize(sum(_their_objective_terms(built, asked, unencoded)))

        # Every gate except the coverage ceiling, which their objective prices instead.
        assumptions = [
            literal
            for literal in built.literals
            if built.gates[literal.index].rule != "R-COVER"
        ]
        model.add_assumptions(assumptions)

        solver = cp_model.CpSolver()
        solver.parameters.max_time_in_seconds = budget
        solver.parameters.num_search_workers = 1
        solver.parameters.random_seed = 7
        started = time.perf_counter()
        status = solver.solve(model)
        elapsed = time.perf_counter() - started

        best = solutions(number)[0].objective
        if status not in (cp_model.OPTIMAL, cp_model.FEASIBLE):
            print(
                f"Instance{number:<3} {len(instance.employees):>6} {instance.days // 7:>6} "
                f"{best:>10} {'-':>10} {'-':>12} {solver.status_name(status):>10} {elapsed:>9.1f}"
            )
            continue

        roster = frozenset(key for key, var in built.x.items() if solver.value(var))
        ours = score_their_objective(roster, asked, unencoded)
        print(
            f"Instance{number:<3} {len(instance.employees):>6} {instance.days // 7:>6} "
            f"{best:>10} {ours:>10} {ours / best:>11.2f}x "
            f"{solver.status_name(status):>10} {elapsed:>9.1f}"
        )
        # The scorer and the model must agree about what was optimised, or the number above
        # is this project grading its own homework with a different pen.
        assert ours == round(solver.objective_value), (
            f"scorer says {ours}, model says {solver.objective_value}"
        )


def _their_objective_terms(built, instance: Instance, unencoded: Unencoded) -> list:
    """Their objective as CP-SAT expressions, over the model's own variables.

    The counterpart of `score_their_objective`, and deliberately not sharing code with it:
    the assertion in `compare` that the two agree is only worth making because they are two
    readings, which is `guide/rules.md`'s independence rule applied to somebody else's objective.
    """
    terms = []
    for slot, short in built.shortfall.items():
        terms.append(unencoded.under_weight[slot] * short)
    for slot, over in built.overage.items():
        terms.append(unencoded.over_weight[slot] * over)

    for request in unencoded.on_requests:
        var = built.x.get((request.employee, request.day, request.shift))
        # A request for a shift the presolve removed is unsatisfiable, and its weight is
        # then a constant this objective still owes.
        terms.append(request.weight * (1 - var) if var is not None else request.weight)
    for request in unencoded.off_requests:
        var = built.x.get((request.employee, request.day, request.shift))
        if var is not None:
            terms.append(request.weight * var)
    return terms


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


def report_unencoded() -> None:
    """What their format states and this model does not encode, per instance (`D-132`).

    Printed because a parse nobody looks at is a parse nobody checks. Each column is a rule
    or an objective term that exists in their data and has no counterpart here, and the point
    of the table is that none of it is zero.
    """
    print(
        f"\n{'instance':>11} {'staff':>6} {'on req':>7} {'off req':>8} {'max wknd':>9} "
        f"{'min off':>8} {'min seq':>8} {'rest h':>7} {'succ':>5}"
    )
    for number in IMPORTABLE:
        instance, _, unencoded = load(number)
        limits = unencoded.limits
        print(
            f"Instance{number:<3} {len(instance.employees):>6} "
            f"{len(unencoded.on_requests):>7} {len(unencoded.off_requests):>8} "
            f"{_spread(limit.max_weekends for limit in limits):>9} "
            f"{_spread(limit.min_consecutive_days_off for limit in limits):>8} "
            f"{_spread(limit.min_consecutive_shifts for limit in limits):>8} "
            f"{unencoded.stated_rest_hours or 0:>7.0f} "
            f"{len(unencoded.cannot_follow):>5}"
        )
    print(
        f"\nTheir daily rest rule is stricter than the {PARAMS['min_rest_hours']:g}h imposed on "
        f"them, so R-REST-GAP cannot fire on a published roster — the empty column in the table "
        f"above is a check on this importer rather than an absence of one."
    )


def _spread(values) -> str:
    """`n` when a column is uniform across a workforce, `lo-hi` when it is not."""
    distinct = sorted(set(values))
    return str(distinct[0]) if len(distinct) == 1 else f"{distinct[0]}-{distinct[-1]}"


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--fetch", action="store_true", help="download and verify the archives")
    parser.add_argument("--force", action="store_true", help="re-download even if present")
    parser.add_argument("--study", action="store_true", help="run the replan comparison")
    parser.add_argument("--scale", action="store_true", help="how far the model goes")
    parser.add_argument("--compare", action="store_true", help="this solver on their problem, against their published optimum")
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

    report_unencoded()

    if args.study:
        study()
    if args.compare:
        compare()
    if args.scale:
        scale()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
