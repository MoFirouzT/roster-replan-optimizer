"""The harness's own verdict, which nothing else checks.

`tests/mutation.py` is the claim behind the test count, and until now it was the one piece of
this repo with no test of its own — understandable, since running it takes about ten minutes,
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


def test_a_run_that_could_not_vouch_for_the_tree_is_not_clean():
    """The run that prompted `D-112`, reduced to its verdict.

    Every mutant was caught and the clean-tree check found nothing — because both files it
    would have checked were already modified, so it checked neither. The report said
    `clean` and `trustworthy: true` with a mutated `checker.py` in the tree, and named the
    reason three fields lower in the same object. Absence of assurance now reads as absence
    of assurance.
    """
    report = mutation.summarise(
        [_result("a"), _result("b")],
        leaked=[],
        skipped=["roster_replan/checker.py", "roster_replan/model.py"],
        full=False,
    )

    assert report["verdict"] == "unverifiable"
    assert report["exit_code"] == 3
    assert not report["trustworthy"], "all caught is not the same as vouched for"
    assert report["caught"] == report["selected"], "and the catches are still reported"


def test_a_late_write_denies_the_run_its_guarantee_too():
    """`_late_restore` puts the file back and the run continues, so nothing leaks. But a
    mutant that ran inside that window was tested against source nobody chose, and the
    window is only bounded to one mutant, not closed."""
    report = mutation.summarise(
        [_result("a")], leaked=[], skipped=[], full=False, late=["roster_replan/disruption.py"]
    )

    assert report["verdict"] == "unverifiable"
    assert report["unvouched_for"] == ["roster_replan/disruption.py"]


def test_a_survivor_is_a_finding_and_outranks_an_unvouched_tree():
    """A mutant that survived, survived — that is true whatever the tree looked like, and
    burying it under `unverifiable` would hide the one thing worth acting on. The verdict
    names the finding; `trustworthy` still says the run could not vouch for itself."""
    report = mutation.summarise(
        [_result("a", caught=False)],
        leaked=[],
        skipped=["roster_replan/nl.py"],
        full=False,
    )

    assert report["verdict"] == "survivors"
    assert report["survivors"] == ["a"]
    assert not report["trustworthy"]


def test_the_report_round_trips_through_the_file(tmp_path):
    report = mutation.summarise([_result("a")], leaked=[], skipped=[], full=True)
    path = mutation.write_report(report, tmp_path / "report.json")

    assert json.loads(path.read_text()) == report
    assert report["catcher_only"] is False, "--full ran the whole suite per mutant"


def test_the_report_records_what_the_run_cost():
    """How long a run takes was folklore until this field existed: the docstrings said "tens
    of minutes", a session put it at ~100, and the measured answer for 103 mutants was 9.
    Nobody could check any of them, because the only durable record kept no clock."""
    report = mutation.summarise(
        [_result("a")],
        leaked=[],
        skipped=[],
        full=False,
        started_at="2026-08-17T06:36:31+00:00",
        duration_seconds=559.4,
    )

    assert report["started_at"] == "2026-08-17T06:36:31+00:00"
    assert report["duration_seconds"] == 559.4


def test_a_summary_taken_outside_a_run_admits_it_has_no_clock():
    """`None` rather than 0.0. A run that took no measurable time and a summary that was
    never timed are different things, and only one of them should read as fast."""
    report = mutation.summarise([_result("a")], leaked=[], skipped=[], full=False)

    assert report["started_at"] is None
    assert report["duration_seconds"] is None


# --- A defect that was gone before the tests ran (`D-139`) ---------------------------


def test_a_reverted_mutation_is_not_reported_as_a_survivor():
    """The fourth hardening, and the first where the harness reported a *finding* it did not
    have rather than withholding one it did.

    A full run came back `survivors: [model-days-off-judges-the-horizon-edge]`. Applying that
    mutation by hand raised `KeyError: -1` and failed twelve tests, and re-running the layer
    alone caught it. The defect had been reverted inside the test window, so pytest passed
    because there was nothing wrong — which scores as a survivor and reads as a hole in a
    test layer.
    """
    results = [
        {
            "name": "reverted", "layer": "model", "path": "roster_replan/model.py",
            "catcher": "tests/test_ground_truth.py", "caught": False, "failed": [],
            "note": mutation.REVERTED, "voided": True,
        }
    ]
    report = mutation.summarise(
        results, leaked=[], skipped=[], full=False, late=["roster_replan/model.py"]
    )

    assert report["survivors"] == []
    assert report["verdict"] == "unverifiable"
    assert report["trustworthy"] is False
    assert "roster_replan/model.py" in report["unvouched_for"]


def test_a_genuine_survivor_still_outranks_an_unvouched_tree():
    """The other direction, and the one that matters more: the fix must not turn a real hole
    into a shrug. A survivor with no `voided` flag is a survivor whatever else the run
    could not vouch for."""
    results = [
        {
            "name": "real", "layer": "model", "path": "roster_replan/model.py",
            "catcher": "tests/test_ground_truth.py", "caught": False, "failed": [],
            "note": "", "voided": False,
        }
    ]
    report = mutation.summarise(
        results, leaked=[], skipped=["roster_replan/model.py"], full=False
    )

    assert report["survivors"] == ["real"]
    assert report["verdict"] == "survivors"
