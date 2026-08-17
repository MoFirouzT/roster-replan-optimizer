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

import pytest

from benchmarks import foreign

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
def test_the_dropped_days_off_survive_the_new_carrier():
    """`load`'s third member grew from a dict into an object, and callers read the dict."""
    _, _, unencoded = foreign.load(1)

    assert unencoded.days_off
    assert all(isinstance(days, list) for days in unencoded.days_off.values())
