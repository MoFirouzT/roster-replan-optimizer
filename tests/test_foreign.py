"""The foreign importer's parse (`D-125`, `D-132`).

**Two layers, and the split is a licence decision rather than a preference.** The benchmark
data is fetched and never redistributed (`D-125`), so a test that needs a fetched copy cannot
run in CI. Everything that can be checked without one therefore is: the sample below is
written here in their documented format, so the column-by-column parse is exercised on every
push, and a mutant in it is caught on any machine.

What genuinely needs their data — that all thirteen instances parse, that no row is dropped,
that their stated rest rule is what this importer says it is — is marked to skip when no copy
has been fetched. Those assertions are worth having and are worth nobody mistaking for CI
coverage, which is why they say so rather than being silently absent.

**The sample is synthetic**, like everything else committed here. It is written to a temporary
file rather than a fixture directory so that nothing in the repository looks like a copy of
somebody else's instance.
"""

from __future__ import annotations

import pathlib

import pytest

from benchmarks import foreign
from roster_replan.domain import Employee, Instance, OpenShift, RuleParams, ShiftType

# Their format, exercising every column this importer reads: two shift types with a
# succession rule, per-shift-type caps including a zero, requests on both sides with
# different weights, and cover weights that differ per slot.
SAMPLE = """\
# a comment, which the parser drops
SECTION_HORIZON
14

SECTION_SHIFTS
# ShiftID, Length in mins, Shifts which cannot follow this shift | separated
D,480,
N,600,D

SECTION_STAFF
# ID, MaxShifts, MaxTotalMinutes, MinTotalMinutes, MaxConsecutiveShifts, MinConsecutiveShifts, MinConsecutiveDaysOff, MaxWeekends
A,D=14|N=0,4320,3360,5,2,2,1
B,D=10|N=4,4800,3000,6,1,3,2

SECTION_DAYS_OFF
A,3,7
B,

SECTION_SHIFT_ON_REQUESTS
# EmployeeID, Day, ShiftID, Weight
A,2,D,2

SECTION_SHIFT_OFF_REQUESTS
B,12,N,3
B,13,N,1

SECTION_COVER
# Day, ShiftID, Requirement, Weight for under, Weight for over
0,D,5,100,1
0,N,2,50,7
"""


@pytest.fixture
def sections(tmp_path):
    path = tmp_path / "Sample.txt"
    path.write_text(SAMPLE)
    return foreign._sections(path)


@pytest.fixture
def index():
    return {"D": 0, "N": 1}


# --- The parse, checked without their data --------------------------------------------


def test_every_stated_limit_is_read(sections):
    """Six of `SECTION_STAFF`'s seven columns had no reader before `D-132`, and a limit
    nobody parses is a constraint nobody can encode later."""
    first, second = foreign._limits(sections["SECTION_STAFF"])

    assert first.max_total_minutes == 4320
    assert first.min_total_minutes == 3360
    assert first.max_consecutive_shifts == 5
    assert first.min_consecutive_shifts == 2
    assert first.min_consecutive_days_off == 2
    assert first.max_weekends == 1

    assert second.max_consecutive_shifts == 6
    assert second.min_consecutive_days_off == 3
    assert second.max_weekends == 2


def test_max_shifts_is_per_shift_type_and_a_zero_is_a_prohibition(sections):
    """`D=14|N=0` caps each shift type separately. Read as a total it would be a number with
    no meaning, and the zero — which forbids a shift outright — would vanish entirely."""
    first, second = foreign._limits(sections["SECTION_STAFF"])

    assert first.max_shifts == {"D": 14, "N": 0}
    assert second.max_shifts == {"D": 10, "N": 4}


def test_requests_arrive_in_this_projects_coordinates(sections, index):
    """Their employee and shift ids are strings. A caller holding both naming schemes at once
    is a caller who will eventually mix them up."""
    order = {"A": 0, "B": 1}

    on = foreign._requests(sections["SECTION_SHIFT_ON_REQUESTS"], order, index)
    off = foreign._requests(sections["SECTION_SHIFT_OFF_REQUESTS"], order, index)

    assert on == (foreign.Request(employee=0, day=2, shift=0, weight=2),)
    assert off == (
        foreign.Request(employee=1, day=12, shift=1, weight=3),
        foreign.Request(employee=1, day=13, shift=1, weight=1),
    )


def test_the_cover_weights_are_read_per_slot_and_left_on_their_scale(sections, index):
    """Both halves matter. Per slot, because their format allows a shift to be priced
    differently on different days; unconverted, because turning their weights into this
    project's would answer `D-057`'s question with somebody else's number."""
    required, under, over = foreign._cover(sections["SECTION_COVER"], index)

    assert required == {(0, 0): 5, (0, 1): 2}
    assert under == {(0, 0): 100, (0, 1): 50}
    assert over == {(0, 0): 1, (0, 1): 7}


def test_a_succession_rule_is_read_and_an_empty_one_is_not_invented(sections, index):
    """Both directions. Their `cannot follow` is the day-based counterpart of a rest gap, and
    a shift with no restriction must not acquire an empty entry that later reads as one."""
    blocked = foreign._successions(["D", "N"], sections["SECTION_SHIFTS"], index)

    assert blocked == {1: frozenset({0})}


def test_a_uniform_column_reads_as_one_number_and_a_varied_one_as_a_range():
    """The report's only piece of arithmetic. A workforce whose limits differ is the
    interesting case and must not be flattened into a single figure."""
    assert foreign._spread([2, 2, 2]) == "2"
    assert foreign._spread([1, 3, 2]) == "1-3"


# --- Their objective, checked without their data ---------------------------------------


@pytest.fixture
def scored():
    """A two-slot week with one request of each kind, built by hand.

    Small enough that every term of their objective can be read off it, which is what makes
    the four tests below able to attribute a wrong total to the term that produced it.
    """
    instance = Instance(
        days=1,
        shift_types=(
            ShiftType(label="D", start_hour=8.0, span_hours=8.0, break_hours=0.0),
            ShiftType(label="N", start_hour=20.0, span_hours=10.0, break_hours=0.0),
        ),
        employees=tuple(
            Employee(name=name, contract="salaried", skills=frozenset(), max_hours_this_week=40.0)
            for name in ("A", "B")
        ),
        open_shifts=(
            OpenShift(day=0, shift=0, required=2),
            OpenShift(day=0, shift=1, required=1),
        ),
        params=RuleParams(
            min_rest_hours=11.0,
            min_weekly_rest_hours=35.0,
            min_period_hours=3.0,
            max_consecutive_days=6,
        ),
    )
    unencoded = foreign.Unencoded(
        limits=(),
        on_requests=(foreign.Request(employee=0, day=0, shift=0, weight=5),),
        off_requests=(foreign.Request(employee=1, day=0, shift=1, weight=7),),
        under_weight={(0, 0): 100, (0, 1): 50},
        over_weight={(0, 0): 1, (0, 1): 3},
        cannot_follow={},
        stated_rest_hours=14.0,
        days_off={},
    )
    return instance, unencoded


def test_a_roster_meeting_every_slot_and_request_scores_zero(scored):
    """Their objective's floor. A scorer that cannot return zero is measuring something
    other than what it claims to."""
    instance, unencoded = scored
    perfect = frozenset({(0, 0, 0), (1, 0, 0), (0, 0, 1)})

    assert foreign.score_their_objective(perfect, instance, unencoded) == 0


def test_under_and_over_cover_are_priced_separately(scored):
    """Their two cover weights differ by two orders of magnitude, so a scorer that used one
    for both would still look plausible on a roster that is only ever short."""
    instance, unencoded = scored

    short_one_day = frozenset({(0, 0, 0), (0, 0, 1)})
    assert foreign.score_their_objective(short_one_day, instance, unencoded) == 100

    over_on_nights = frozenset({(0, 0, 0), (1, 0, 0), (0, 0, 1), (1, 0, 1)})
    assert foreign.score_their_objective(over_on_nights, instance, unencoded) == 3 + 7


def test_an_unmet_on_request_and_an_ignored_off_request_both_cost(scored):
    """The two request lists are penalised in opposite directions, which is the easiest thing
    in their format to implement backwards."""
    instance, unencoded = scored

    # A works nights instead of the day shift they asked for: the on-request goes unmet, and
    # the day shift is one short.
    swapped = frozenset({(1, 0, 0), (0, 0, 1)})
    assert foreign.score_their_objective(swapped, instance, unencoded) == 100 + 5

    # B works the night they asked to avoid.
    unwanted = frozenset({(0, 0, 0), (1, 0, 0), (1, 0, 1)})
    assert foreign.score_their_objective(unwanted, instance, unencoded) == 7


def test_nothing_outside_their_objective_is_charged(scored):
    """The finding `D-132` and `D-133` rest on: weekend counts, consecutive days and rest are
    constraints in their formulation, not objective terms. A scorer that priced any of them
    would still reproduce a roster with none of those features and fail on the archives."""
    instance, unencoded = scored
    perfect = frozenset({(0, 0, 0), (1, 0, 0), (0, 0, 1)})

    # One person working both shifts in a day breaks a sequence rule and costs nothing here.
    assert foreign.score_their_objective(perfect, instance, unencoded) == 0


# --- Their constraints, checked without their data -------------------------------------


def _fortnight(limit: foreign.Limit, **overrides) -> tuple[Instance, foreign.Unencoded]:
    """Two weeks, one person, two shift types. Long enough to have an interior."""
    instance = Instance(
        days=14,
        shift_types=(
            ShiftType(label="D", start_hour=8.0, span_hours=8.0, break_hours=0.0),
            ShiftType(label="N", start_hour=20.0, span_hours=10.0, break_hours=0.0),
        ),
        employees=(
            Employee(name="A", contract="salaried", skills=frozenset(), max_hours_this_week=60.0),
        ),
        open_shifts=(OpenShift(day=0, shift=0, required=1),),
        params=RuleParams(
            min_rest_hours=11.0,
            min_weekly_rest_hours=35.0,
            min_period_hours=3.0,
            max_consecutive_days=14,
        ),
    )
    unencoded = foreign.Unencoded(
        limits=(limit,),
        on_requests=(),
        off_requests=(),
        under_weight={},
        over_weight={},
        cannot_follow=overrides.get("cannot_follow", {}),
        stated_rest_hours=14.0,
        days_off={},
    )
    return instance, unencoded


def _limit(**overrides) -> foreign.Limit:
    """A limit that forbids nothing, so a test switches on only what it is about."""
    base = dict(
        max_shifts={"D": 99, "N": 99},
        max_total_minutes=100_000,
        min_total_minutes=0,
        max_consecutive_shifts=99,
        min_consecutive_shifts=1,
        min_consecutive_days_off=1,
        max_weekends=99,
    )
    return foreign.Limit(**(base | overrides))


def test_working_both_weekends_breaks_a_one_weekend_limit():
    """`MaxWeekends` counts Saturday-Sunday pairs, and their horizons start on a Monday, so
    days 5 and 6 of each week are the weekend (E4 in the preference survey)."""
    instance, unencoded = _fortnight(_limit(max_weekends=1))

    one = frozenset({(0, 5, 0), (0, 6, 0)})
    assert foreign.their_violations(one, instance, unencoded) == []

    both = frozenset({(0, 5, 0), (0, 6, 0), (0, 12, 0), (0, 13, 0)})
    assert foreign.their_violations(both, instance, unencoded) == ["MaxWeekends"]


def test_a_single_day_off_between_two_blocks_breaks_a_two_day_minimum():
    """E7: two days off together beat two days off apart, which is a constraint here."""
    instance, unencoded = _fortnight(_limit(min_consecutive_days_off=2))

    split = frozenset({(0, day, 0) for day in (2, 3, 5, 6)})
    assert foreign.their_violations(split, instance, unencoded) == ["MinConsecutiveDaysOff"]

    together = frozenset({(0, day, 0) for day in (2, 3, 6, 7)})
    assert foreign.their_violations(together, instance, unencoded) == []


def test_a_stretch_touching_the_horizon_edge_is_not_judged_against_a_minimum():
    """The latitude their own rosters need (`D-134`). A block at either end may be the tail of
    a longer one outside the horizon, and without this every one of the 26 published rosters
    reports a short working block — which is the rule read too strictly, not 26 wrong rosters.

    A *maximum* gets no such latitude: a run too long inside the horizon is too long whatever
    surrounds it.
    """
    instance, unencoded = _fortnight(_limit(min_consecutive_shifts=3, max_consecutive_shifts=4))

    assert foreign.their_violations(frozenset({(0, 0, 0)}), instance, unencoded) == []
    assert foreign.their_violations(frozenset({(0, 13, 0)}), instance, unencoded) == []

    interior = frozenset({(0, 5, 0)})
    assert foreign.their_violations(interior, instance, unencoded) == ["MinConsecutiveShifts"]

    at_the_edge = frozenset({(0, day, 0) for day in range(0, 5)})
    assert foreign.their_violations(at_the_edge, instance, unencoded) == ["MaxConsecutiveShifts"]


def test_a_forbidden_succession_is_reported_only_in_that_order():
    """Their day-based counterpart of a rest gap: N may not be followed by D."""
    instance, unencoded = _fortnight(_limit(), cannot_follow={1: frozenset({0})})

    night_then_day = frozenset({(0, 5, 1), (0, 6, 0)})
    assert foreign.their_violations(night_then_day, instance, unencoded) == ["Succession"]

    day_then_night = frozenset({(0, 5, 0), (0, 6, 1)})
    assert foreign.their_violations(day_then_night, instance, unencoded) == []


def test_a_per_shift_type_cap_and_an_hours_floor_are_both_checked():
    """`MaxShifts` is per shift type and `MinTotalMinutes` is a floor — the only limit in
    their format that a roster breaks by doing too little."""
    instance, unencoded = _fortnight(_limit(max_shifts={"D": 1, "N": 99}))
    two_days = frozenset({(0, 5, 0), (0, 6, 0)})
    assert foreign.their_violations(two_days, instance, unencoded) == ["MaxShifts"]

    instance, unencoded = _fortnight(_limit(min_total_minutes=10_000))
    assert foreign.their_violations(two_days, instance, unencoded) == ["MinTotalMinutes"]


def test_published_solutions_are_ordered_by_objective_not_by_directory(tmp_path, monkeypatch):
    """`load` used to take whatever `glob` yielded, which is directory order and therefore a
    property of the machine (`D-133`) — the same defect `D-118` found in the solver's choice
    of optimum, in a second place.

    Written against empty files with the right names rather than against the archives, so the
    ordering claim is checked on every machine. The objective is in the file name, so the name
    is all this needs.
    """
    xml = tmp_path / "Solutions" / "XML"
    xml.mkdir(parents=True)
    names = [f"Instance99.Solution.{value}.roster" for value in (1002, 837, 828)]
    for name in names:
        (xml / name).touch()

    # Discovery order is fixed here rather than left to the filesystem, which is the whole
    # point: written against `touch` order alone this test passed even with the sort removed,
    # because APFS happened to return the names in the order the assertion wanted. A test
    # whose subject is "do not trust directory order" must not itself trust directory order.
    monkeypatch.setattr(foreign, "_solution_dir", lambda: tmp_path)
    monkeypatch.setattr(
        pathlib.Path, "glob", lambda self, pattern: iter([xml / name for name in names])
    )

    found = foreign.solutions(99)

    assert [s.objective for s in found] == [828, 837, 1002]
    assert found[0].path.name == "Instance99.Solution.828.roster"
    assert all(s.number == 99 for s in found)


# --- The whole import, which needs a fetched copy --------------------------------------

needs_data = pytest.mark.skipif(
    not foreign.available(),
    reason="benchmark data is fetched, never redistributed (`D-125`) — "
    "run `uv run python -m benchmarks.foreign --fetch`",
)


@needs_data
@pytest.mark.parametrize("number", foreign.IMPORTABLE)
def test_every_importable_instance_parses_into_matching_coordinates(number):
    instance, _, unencoded = foreign.load(number)

    assert len(unencoded.limits) == len(instance.employees)
    assert set(unencoded.under_weight) == {(o.day, o.shift) for o in instance.open_shifts}
    assert set(unencoded.over_weight) == set(unencoded.under_weight)

    for request in unencoded.on_requests + unencoded.off_requests:
        assert 0 <= request.employee < len(instance.employees)
        assert 0 <= request.day < instance.days
        assert 0 <= request.shift < len(instance.shift_types)


@needs_data
@pytest.mark.parametrize("number", foreign.IMPORTABLE)
def test_no_request_row_is_silently_dropped(number):
    """The failure this guards is quiet: a request whose shift id did not resolve would be
    skipped, and their objective would be imported one term short with nothing to show it."""
    section = foreign._sections(foreign._instance_dir() / f"Instance{number}.txt")
    _, _, unencoded = foreign.load(number)

    assert len(unencoded.on_requests) == len(section.get("SECTION_SHIFT_ON_REQUESTS", []))
    assert len(unencoded.off_requests) == len(section.get("SECTION_SHIFT_OFF_REQUESTS", []))


@needs_data
def test_their_rest_rule_is_stricter_than_the_one_imposed_on_them():
    """Why `R-REST-GAP` never fires on a published roster (`D-132`).

    Read as an absence it says nothing. Read against their own stated 14 hours it is a check
    on this importer's clock: a mistranslated start time would put shifts closer together
    than either rule allows, and the column would stop being empty.
    """
    imposed = foreign.PARAMS["min_rest_hours"]
    for number in foreign.IMPORTABLE:
        _, _, unencoded = foreign.load(number)
        assert unencoded.stated_rest_hours is not None, number
        assert unencoded.stated_rest_hours > imposed, number


@needs_data
def test_their_objective_reproduces_every_published_value():
    """The external check (`D-133`), and the strongest one in this repo.

    Every other correctness claim here rests on two readings this project wrote agreeing with
    each other. This one rests on 26 numbers somebody else published, stated in the solution
    file names before this project existed. An implementation that invents a term, drops one,
    or mistranslates a coordinate cannot pass it by coincidence.
    """
    checked = 0
    for number in foreign.IMPORTABLE:
        instance, _, unencoded = foreign.load(number)
        order = {person.name: i for i, person in enumerate(instance.employees)}
        index = {shift.label: i for i, shift in enumerate(instance.shift_types)}

        for published in foreign.solutions(number):
            roster = foreign._published_roster(published.path, order, index)
            assert foreign.score_their_objective(roster, instance, unencoded) == (
                published.objective
            ), f"Instance{number} solution {published.objective}"
            checked += 1

    assert checked == 26, f"expected 26 published solutions, scored {checked}"


@needs_data
@pytest.mark.parametrize("number", foreign.IMPORTABLE)
def test_the_incumbent_is_the_best_published_solution_and_not_whichever_was_found(number):
    """`load` used to take whatever `glob` yielded, which is directory order and therefore a
    property of the machine (`D-133`). A baseline nobody named is a baseline nobody can
    reproduce — the same defect `D-118` found in the solver's choice of optimum."""
    published = foreign.solutions(number)

    assert published, f"Instance{number} has no published solution"
    assert [s.objective for s in published] == sorted(s.objective for s in published)

    instance, incumbent, unencoded = foreign.load(number)
    assert foreign.score_their_objective(incumbent, instance, unencoded) == (
        published[0].objective
    )


@needs_data
def test_their_constraints_are_satisfied_by_every_published_roster():
    """The second external check (`D-134`), and the reason this reading can be trusted before
    anything is encoded from it.

    Their published rosters are legal under their own constraints, so a correct reading
    reports nothing on all 26. This caught a real misreading on its first run: a minimum block
    length applied at the horizon's edge failed every roster in the set, because a stretch
    touching either end may continue outside the window.
    """
    for number in foreign.IMPORTABLE:
        instance, _, unencoded = foreign.load(number)
        order = {person.name: i for i, person in enumerate(instance.employees)}
        index = {shift.label: i for i, shift in enumerate(instance.shift_types)}

        for published in foreign.solutions(number):
            roster = foreign._published_roster(published.path, order, index)
            assert foreign.their_violations(roster, instance, unencoded) == [], (
                f"Instance{number} solution {published.objective}"
            )


@needs_data
def test_the_dropped_days_off_survive_the_new_carrier():
    """`load`'s third member grew from a dict into an object, and callers read the dict."""
    _, _, unencoded = foreign.load(1)

    assert unencoded.days_off
    assert all(isinstance(days, list) for days in unencoded.days_off.values())
