"""The repository's social preview card: 1280x640, for the link and not for the reader.

    uv run python -m benchmarks.social            # report what it would write
    uv run python -m benchmarks.social --write    # and write build/social-preview.svg

GitHub shows this image wherever the repository is linked, in a feed or a chat, at a few
hundred pixels wide and before anybody has decided to click. `docs/saturday-sick-call.svg`
cannot do that job: it is 504 by 486 against this card's 2:1, and its labels are 9.5px, so a
straight rasterisation is a grey smear. The grids are here as evidence that the thing is
real, at a size where their shape reads and their text does not, and the argument is carried
by two numbers instead.

## Nothing on it is typed

The two means and the segment they are means over are registered figures owned by
`benchmarks.md`, read through the same registry `scripts/lint_docs.py` checks copies against
(`D-158`). A reworded table stops this command rather than producing a stale card. The
grids are drawn from the same solve as the committed figure, through `benchmarks.figure`.

The output is gitignored. It is uploaded once in the repository's settings and referenced by
nothing here, so committing it would be committing a build artifact for no reader's benefit.
"""

from __future__ import annotations

import argparse
import importlib.util
import pathlib
import re
import tomllib
import xml.etree.ElementTree as ET

from benchmarks import figure

ROOT = pathlib.Path(__file__).resolve().parents[1]
FIGURES_FILE = ROOT / "scripts" / "figures.toml"
OUT = ROOT / "build" / "social-preview.svg"

W, H = 1280, 640
INK = figure.INK
DEEP = "#1f2933"
ADDED = figure.ADDED
DROPPED = figure.DROPPED


def _lint():
    spec = importlib.util.spec_from_file_location("lint_docs", ROOT / "scripts" / "lint_docs.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def headline(fid: str) -> str:
    """A registered figure's live value, read from the line its owner marked.

    The rule `check_figures` runs, from the other side: the linter asserts every copy agrees
    with the owner, and this refuses to make a copy at all. A pattern that has stopped
    matching raises, so the card is not built rather than built stale.
    """
    lint = _lint()
    entries = tomllib.loads(FIGURES_FILE.read_text(encoding="utf-8"))["figure"]
    entry = next(e for e in entries if e["id"] == fid)

    owner = ROOT / entry["owner"]
    pattern = re.compile(entry["pattern"])
    context = re.compile(entry["context"]) if entry.get("context") else None
    marker = lint.FIGURE_MARKER.format(id=fid)

    owned = [
        value
        for _, value, line in lint.figure_hits(pattern, owner.read_text(encoding="utf-8"), context)
        if marker in line
    ]
    if not owned:
        raise SystemExit(
            f"figure {fid!r}: {entry['owner']} has no `{marker}` line its pattern matches. "
            "The table was reworded; fix the registry before the card is rebuilt."
        )
    return owned[0].strip()


# Each panel of the committed drawing is captioned with that one week's change count, 6
# against 2. The card leads with the means over 72 weeks, 12.36 against 2.40, and two
# different pairs of numbers for one idea is a reader stopping to work out which is wrong.
# The captions come off; the panel titles stay, because they say which grid is which.
PANEL_CAPTION = re.compile(r"^\d+ assignments? moved")


def _grids() -> tuple[str, float, float]:
    """The committed drawing's body, and the size it was drawn at.

    Taken from `benchmarks.figure` rather than redrawn, so the card cannot show a week the
    documentation does not. Its own `<style>` travels with it, scoped by the wrapping group.
    """
    svg = ET.fromstring(figure.render())
    _, _, width, height = (float(v) for v in svg.get("viewBox").split())
    kept = [
        child
        for child in svg
        if not (child.tag.endswith("text") and PANEL_CAPTION.match((child.text or "").strip()))
    ]
    if len(kept) == len(list(svg)):
        raise SystemExit(
            "the panel captions are gone from `benchmarks.figure`, or they are worded "
            "differently. Check PANEL_CAPTION before the card is rebuilt."
        )
    inner = "".join(ET.tostring(child, encoding="unicode") for child in kept)
    return inner, width, height


def render() -> str:
    cold = headline("headline-changes-cold")
    replan = headline("headline-changes-replan")
    weeks = headline("headline-fully-staffed-weeks")

    inner, gw, gh = _grids()
    # The grids fill the right third, upright, with the card's own padding around them.
    scale = (H - 96) / gh
    art_x = W - gw * scale - 56

    return "\n".join(
        [
            f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" '
            f'width="{W}" height="{H}" font-family="ui-sans-serif,system-ui,sans-serif">',
            "<style>",
            f".slug{{font-size:20px;font-weight:600;fill:{INK};letter-spacing:.02em}}",
            f".lede{{font-size:46px;font-weight:700;fill:{DEEP}}}",
            f".sub{{font-size:22px;fill:{INK}}}",
            f".claim{{font-size:20px;font-weight:600;fill:{DEEP}}}",
            f".label{{font-size:21px;font-weight:600;fill:{DEEP}}}",
            f".num{{font-size:84px;font-weight:700}}",
            f".cap{{font-size:19px;font-weight:600}}",
            f".foot{{font-size:15px;fill:{INK}}}",
            f".cold{{fill:{DROPPED}}}",
            f".warm{{fill:{ADDED}}}",
            "</style>",
            f'<rect width="{W}" height="{H}" fill="#ffffff"/>',
            f'<g class="art" transform="translate({art_x:.1f},48) scale({scale:.4f})">',
            inner,
            "</g>",
            # After the group, and by descendant selector, so these beat the drawing's own
            # rules and its dark-mode block alike. The drawing is tuned for a documentation
            # page at full size; on a card read at half this width its greys wash out.
            "<style>",
            ".art .off{fill:#b8c1cb;fill-opacity:.7}",
            ".art .held{fill:#737d87}",
            ".art .h,.art .n,.art .d,.art .e{fill:#3d4751}",
            "</style>",
            '<text x="56" y="60" class="slug">roster-replan-optimizer</text>',
            '<text x="56" y="142" class="lede">Someone calls in sick</text>',
            '<text x="56" y="194" class="lede">on Saturday.</text>',
            '<text x="56" y="242" class="sub">Minimum-disruption shift-roster replanning,</text>',
            '<text x="56" y="270" class="sub">under Belgian labour law.</text>',
            '<text x="56" y="328" class="label">Assignments moved by:*</text>',
            f'<text x="56" y="424" class="num cold">{cold}</text>',
            '<text x="56" y="456" class="cap cold">Cold re-solve</text>',
            f'<text x="304" y="424" class="num warm">{replan}</text>',
            '<text x="304" y="456" class="cap warm">Replan</text>',
            f'<text x="56" y="502" class="foot">* Means over the {weeks} committed weeks that '
            "could be fully staffed.</text>",
            '<text x="56" y="524" class="foot">Both rosters are legal, and both staff every '
            "shift the other does.</text>",
            '<text x="56" y="578" class="claim">Every roster is re-verified against every '
            "rule by a</text>",
            '<text x="56" y="604" class="claim">second implementation that imports no '
            "solver.</text>",
            "</svg>",
            "",
        ]
    )


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--write", action="store_true", help=f"write {OUT.name}")
    args = parser.parse_args(argv)

    svg = render()
    if not args.write:
        print(f"{len(svg):,} bytes, not written. Pass --write.")
        return 0

    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(svg, encoding="utf-8")
    print(f"wrote {OUT.relative_to(ROOT)} ({W}x{H})")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
