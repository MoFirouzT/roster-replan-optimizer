"""The README's figure, held to the numbers it draws.

A committed artifact drifts from the code that made it, silently, and this one is on the
front page. `manifest.json` has the same exposure and answers it the same way (`D-073`):
commit the artifact, and assert it is what the generator still produces.

The second test is the one worth having. An image that reports *six changes* in its caption
while drawing five marks is worse than no image, because a reader counts the marks and
believes them. So the drawing is parsed back and its marks are counted against what
`methods.run` reports, rather than against a number written down beside it.
"""

from __future__ import annotations

import collections
import pathlib
import xml.etree.ElementTree as ET

import pytest

from benchmarks import figure
from benchmarks.methods import COLD_COST, WARM_REPLAN, run
from benchmarks.suite import build

SVG = "{http://www.w3.org/2000/svg}"


@pytest.fixture(scope="module")
def drawn() -> str:
    return figure.render()


def _classes(svg: str) -> collections.Counter:
    root = ET.fromstring(svg)
    return collections.Counter(
        node.get("class") for node in root.iter(f"{SVG}rect")
    )


def test_the_committed_figure_is_what_the_generator_still_produces(drawn):
    """Regenerating must be a no-op. If this fails the figure is stale, not wrong --
    run `python -m benchmarks.figure --write` and read the diff before committing it.
    """
    committed = pathlib.Path(figure.OUT)
    assert committed.exists(), "the README links this file; it has to be committed"
    assert committed.read_text() == drawn


def test_the_figure_draws_exactly_the_changes_the_methods_report(drawn):
    """The caption's counts are the drawing's counts.

    Both panels share one legend, which contributes one swatch per state, so the marks
    are the totals less that one. A miscount either way fails here.
    """
    scenario = build(figure.CASE)
    cold = run(COLD_COST, scenario, seed=7, time_limit=30.0)
    warm = run(WARM_REPLAN, scenario, seed=7, time_limit=30.0)

    counts = _classes(drawn)
    legend = 1  # one swatch each for held, added, dropped
    drawn_changes = (counts["add"] - legend) + (counts["drop"] - legend)

    assert drawn_changes == cold.changes + warm.changes
    assert f"{cold.changes} assignments moved" in drawn
    assert f"{warm.changes} assignments moved" in drawn


def test_every_slot_of_both_panels_is_drawn(drawn):
    """A cell missing from the grid is a shift the reader cannot see was never staffed.

    Two panels, one cell per (employee, day, shift), plus the three legend swatches.
    """
    instance = build(figure.CASE).instance
    slots = len(instance.employees) * instance.days * len(instance.shift_types)

    counts = _classes(drawn)
    assert sum(counts.values()) == 2 * slots + 3


def test_the_pinned_boundary_lands_where_now_does(drawn):
    """`R-PIN-PAST` is the reason the cold solve cannot reshuffle Monday, and the rule
    marks that boundary. Drawn in the wrong column it argues the opposite of the truth.
    """
    instance = build(figure.CASE).instance
    shifts = len(instance.shift_types)
    first_future = min(
        (day, shift)
        for day in range(instance.days)
        for shift in range(shifts)
        if day * 24 + instance.shift_types[shift].start_hour >= instance.now
    )
    expected = figure._x(*first_future, shifts) - figure.GAP / 2

    # The legend's swatch carries the same class and is ten pixels tall; a panel's rule
    # spans every employee row. Length is what separates them.
    root = ET.fromstring(drawn)
    rules = [
        node
        for node in root.iter(f"{SVG}line")
        if node.get("class") == "now"
        and float(node.get("y2")) - float(node.get("y1")) > 40
    ]
    assert len(rules) == 2, "one boundary per panel"
    assert all(float(node.get("x1")) == expected for node in rules)
