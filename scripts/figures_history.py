#!/usr/bin/env python3
"""Run the figure check against the commits that carried each known incident.

`scripts/lint_docs.py`'s figure check exists because of three incidents, and a check
built from incidents is worth what it can be shown to catch. This replays each one:
the tree is exported at the commit that carried it, today's check is dropped in, and
the check runs against that tree with the registry named on the command line.

    uv run python scripts/figures_history.py

It is not part of the suite. It reads git history and writes nothing.

Two things it must be honest about, and both are printed rather than hidden:

  - A `pinned` figure needs the owner's `<!-- fig:<id> -->` marker, which did not exist
    at these commits. The harness inserts it on the owner's heading and says so. It
    inserts a marker, never a value.
  - The check reads documents. Where every document agreed with the others and the
    disagreement was with reality, it is silent, and the case below records that.
"""

from __future__ import annotations

import importlib.util
import shutil
import subprocess
import sys
import tarfile
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

# One case per incident. `extra` names a file of history-only entries appended to the
# shipped registry: an entry goes there when the claim it was written against has since
# been deleted, so the shipped registry would report it as covering nothing.
CASES = [
    (
        "2. The illegal-past figure, corrected to 8 of 13 with four copies left behind",
        "e6a18da",
        None,
        [("docs/studies/foreign-incumbent.md", "## Ten of thirteen have an illegal past")],
    ),
    (
        "3a. A ledger-row coverage claim of 16 of 16 against a ledger of 18 rows",
        "8de74e6",
        None,
        [],
    ),
    (
        "3b. The by-theme index claimed to cover 146 of 150",
        "5f511f4",
        "scripts/figures-history.toml",
        [],
    ),
    (
        "1. The scale table before it was known to be wrong: every document agreed",
        "195e507",
        None,
        [("docs/studies/foreign-incumbent.md", "## Ten of thirteen have an illegal past")],
    ),
]

MARKER = "<!-- fig:foreign-illegal-past -->"


def export(commit: str, dest: Path) -> None:
    archive = dest / "tree.tar"
    with open(archive, "wb") as fh:
        subprocess.run(["git", "archive", commit], cwd=ROOT, stdout=fh, check=True)
    with tarfile.open(archive) as tar:
        tar.extractall(dest, filter="data")
    archive.unlink()


def run_case(
    title: str, commit: str, extra: str | None, markers: list[tuple[str, str]]
) -> None:
    print(f"\n=== {title}\n    commit {commit}" + (f", plus {extra}" if extra else ""))
    with tempfile.TemporaryDirectory() as tmp:
        tree = Path(tmp)
        export(commit, tree)
        (tree / "scripts").mkdir(exist_ok=True)
        shutil.copy(ROOT / "scripts" / "lint_docs.py", tree / "scripts" / "lint_docs.py")
        registry = (ROOT / "scripts" / "figures.toml").read_text(encoding="utf-8")
        if extra:
            registry += "\n" + (ROOT / extra).read_text(encoding="utf-8")
        (tree / "scripts" / "figures.toml").write_text(registry, encoding="utf-8")

        for path, heading in markers:
            target = tree / path
            if not target.exists():
                continue
            text = target.read_text(encoding="utf-8")
            if heading in text and MARKER not in text:
                target.write_text(text.replace(heading, f"{heading} {MARKER}"), encoding="utf-8")
                print(f"    marker inserted on {path}: {heading!r}")

        spec = importlib.util.spec_from_file_location(
            f"lint_{commit}", tree / "scripts" / "lint_docs.py"
        )
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)

        errors: list[str] = []
        module.check_figures(errors)
        if not errors:
            print("    silent: no registered figure disagrees with its owner in this tree")
        for e in errors:
            print(f"    - {e}")


def main() -> int:
    for case in CASES:
        run_case(*case)
    print()
    return 0


if __name__ == "__main__":
    sys.exit(main())
