"""The demo, and the committed scenario it runs on.

The README promises exactly one runnable command, and before this existed it named a module
and a directory that were not there. A command in a README is a claim like any other, so it
is tested like one.

The second test is the more valuable of the two. `scenarios/saturday_sick_call.json`
is a payload frozen at a point in time, and the generator that produced it is still under
development — so it can drift into describing a week the project no longer generates, with
nothing to notice. That is the failure `D-074` built the benchmark manifest to catch, in a
file the manifest does not cover.
"""

from __future__ import annotations

import json
import pathlib

import pytest

from benchmarks import suite
from roster_replan.demo import main
from roster_replan.service.contracts import ReplanRequest, from_domain, to_domain

SCENARIO = pathlib.Path(__file__).resolve().parent.parent / "scenarios" / (
    "saturday_sick_call.json"
)


def test_the_readme_command_runs(capsys):
    assert main([str(SCENARIO)]) == 0

    printed = capsys.readouterr().out
    assert "proven optimal" in printed
    assert "Sat" in printed, "the demo defaults to a Monday day zero, so days should be named"
    assert "short of its" in printed, "the explanation should reach the output"


def test_a_missing_payload_fails_cleanly(capsys):
    assert main(["scenarios/does-not-exist.json"]) == 2
    assert "no such payload" in capsys.readouterr().err


def test_a_different_weekday_of_day_zero_overrides_the_default(capsys):
    """`prose.py` still refuses to invent a weekday on its own — see
    `test_no_weekday_without_a_calendar` in `test_prose.py` — but the demo's own default
    (`day 0 == Monday`) can be overridden by a caller who knows better."""
    main([str(SCENARIO), "--weekday-of-day-zero", "1"])
    printed = capsys.readouterr().out

    assert "Sun" in printed, "day 5 is a Sunday when day zero is a Tuesday"


def test_the_committed_scenario_still_matches_the_generator():
    """Otherwise the demo slowly starts describing a week the project no longer produces.

    Regenerate deliberately if the generator moved, the same way `manifest.json` is
    regenerated, and say why in `decisions.md`.
    """
    request = ReplanRequest.model_validate_json(SCENARIO.read_text())
    assert to_domain(request.instance) == suite.build("headline/3").instance


def test_the_scenario_is_the_real_wire_format():
    """The demo doubles as the worked example of what a caller sends, so the file has to be
    a payload the API would accept — not a convenient shape invented for the demo."""
    raw = json.loads(SCENARIO.read_text())
    request = ReplanRequest.model_validate(raw)

    assert request.tenant
    assert from_domain(to_domain(request.instance)).model_dump() == request.instance.model_dump()


@pytest.mark.parametrize("flag", ["--budget-seconds", "--weekday-of-day-zero"])
def test_the_documented_flags_exist(flag, capsys):
    with pytest.raises(SystemExit):
        main(["--help"])
    assert flag in capsys.readouterr().out
