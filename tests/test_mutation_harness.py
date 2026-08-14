"""The harness's own verdict, which nothing else checks.

`tests/mutation.py` is the claim behind the test count, and until now it was the one piece of
this repo with no test of its own — understandable, since running it takes tens of minutes,
and unfortunate, because its *verdict* is a few lines of pure logic that decide whether a
long run is believed.

The logic is separated from the run for that reason. What is tested here is what the report
says, not what the mutants do.

**A leak outranks survivors.** A run that left a mutation in the working tree cannot be
trusted about anything that ran after it: the next mutant's catcher tests may have failed on
the leftover defect rather than on their own, and been scored caught for the wrong reason.
That has happened — twice — which is why `trustworthy` is a field rather than an inference a
reader is left to make.
"""

from __future__ import annotations

import json

from tests import mutation


def _result(name: str, *, caught: bool = True) -> dict:
    return {
        "name": name,
        "layer": "checker",
        "path": "roster_replan/checker.py",
        "catcher": "tests/test_ground_truth.py",
        "caught": caught,
        "failed": ["test_something"] if caught else [],
        "note": "",
    }


def test_a_run_where_every_mutant_was_caught_is_clean():
    report = mutation.summarise(
        [_result("a"), _result("b")], leaked=[], skipped=[], full=False
    )

    assert report["verdict"] == "clean"
    assert report["exit_code"] == 0
    assert report["trustworthy"]
    assert (report["caught"], report["selected"]) == (2, 2)


def test_a_survivor_is_a_failure_and_is_named():
    report = mutation.summarise(
        [_result("a"), _result("b", caught=False)], leaked=[], skipped=[], full=False
    )

    assert report["verdict"] == "survivors"
    assert report["exit_code"] == 1
    assert report["survivors"] == ["b"]


def test_a_leak_outranks_survivors_and_voids_the_run():
    """The case that cost two runs. Everything was caught and a file was left modified — so
    the mutants that ran after the leak were tested against a defect nobody chose."""
    report = mutation.summarise(
        [_result("a"), _result("b", caught=False)],
        leaked=["roster_replan/disruption.py"],
        skipped=[],
        full=False,
    )

    assert report["verdict"] == "leaked"
    assert report["exit_code"] == 2
    assert not report["trustworthy"], "a leaked run must not read as a result"
    assert report["survivors"] == ["b"], "and it still says what else it found"


def test_a_clean_looking_run_is_still_void_if_a_file_leaked():
    report = mutation.summarise(
        [_result("a")], leaked=["roster_replan/disruption.py"], skipped=[], full=False
    )

    assert report["caught"] == report["selected"]
    assert report["verdict"] == "leaked", "all caught is not the same as trustworthy"


def test_files_the_run_could_not_vouch_for_are_named():
    """A file already modified when the run starts is skipped by the clean-tree check, so a
    mutation left in one of those is invisible. The report says which, rather than leaving a
    reader to reconstruct it from a note printed thirty minutes earlier."""
    report = mutation.summarise(
        [_result("a")], leaked=[], skipped=["roster_replan/nl.py"], full=False
    )

    assert report["unchecked_because_already_modified"] == ["roster_replan/nl.py"]


def test_the_report_round_trips_through_the_file(tmp_path):
    report = mutation.summarise([_result("a")], leaked=[], skipped=[], full=True)
    path = mutation.write_report(report, tmp_path / "report.json")

    assert json.loads(path.read_text()) == report
    assert report["catcher_only"] is False, "--full ran the whole suite per mutant"
