"""The specs, checked mechanically. The finish declaration's evidence rather than its claim.

`PLAN.md`: *a component is not done until its spec matches its code*, and the finish
declaration asserts that of every spec at once. An assertion like that is worth what it can
be checked against, so what can be checked is checked here rather than read once and
declared true.

Four things are mechanisable, and each corresponds to a way the documentation has drifted or
could drift:

1. **Every rule the registry says is encoded exists in both readings.** `rules.md` is the
   day-1 artifact and the one document every other file cites; a rule ID that no longer
   appears in `checker.py` and `model.py` is the registry describing a system that is gone.
2. **Every decision ID referenced anywhere has exactly one record.** A dangling `D-0NN` sends
   a reader to nothing.
3. **No duplicate decision IDs.** This is not hypothetical: `D-089` was assigned twice in
   this repo -- once to the rest-gap encoding study and once to a service record written in
   parallel -- and nothing noticed until a human read the index.
4. **Every relative link between documents resolves.** The specs cross-reference heavily and
   a renamed file breaks silently.

What is *not* mechanisable is whether a spec's prose describes what the code does. That is
the reconcile beat, done by reading, and these tests do not pretend to replace it.
"""

from __future__ import annotations

import pathlib
import re

import pytest

ROOT = pathlib.Path(__file__).resolve().parent.parent
DOCS = ROOT / "docs"
SPECS = DOCS / "specs"

MARKDOWN = sorted(
    p for p in DOCS.rglob("*.md") if ".venv" not in p.parts
) + [ROOT / "README.md", ROOT / "CLAUDE.md"]

# Rules the registry marks `optional` are profile-gated and deliberately not encoded, and
# `R-MIN-SHIFT` is input validation rather than a roster rule. `R-EXAMPLE` is the template
# the registry uses to show the shape of an entry.
UNENCODED = {
    "R-STUDENT-QUOTA",
    "R-SUNDAY",
    "R-BREAK",
    "R-PT-MIN",
    "R-PUB-NOTICE",
    "R-MIN-SHIFT",
    "R-EXAMPLE",
}


def _text(path: pathlib.Path) -> str:
    return path.read_text(encoding="utf-8")


@pytest.fixture(scope="module")
def registry() -> set[str]:
    """Rule IDs from the registry table in `rules.md`."""
    ids = set()
    for line in _text(SPECS / "rules.md").splitlines():
        match = re.match(r"\|\s*`(R-[A-Z-]+)`\s*\|", line)
        if match:
            ids.add(match.group(1))
    assert ids, "no rule IDs parsed from the registry -- the table shape changed"
    return ids


# --- The rule registry against both readings ----------------------------------------


def test_every_encoded_rule_appears_in_both_readings(registry):
    """The independence rule's whole point is two readings of the same registry.

    A rule present in one and missing from the other is not caught by the differential
    harness, which compares the violations they *report*: a rule neither of them encodes
    produces no disagreement at all.
    """
    checker = _text(ROOT / "roster_replan" / "checker.py")
    model = _text(ROOT / "roster_replan" / "model.py")

    for rule in sorted(registry - UNENCODED):
        assert rule in checker, f"{rule} is in the registry but not in checker.py"
        assert rule in model, f"{rule} is in the registry but not in model.py"


def test_no_reading_invents_a_rule_the_registry_does_not_have(registry):
    """A rule ID in the code with no registry entry is a rule nobody agreed to."""
    for path in ("checker.py", "model.py"):
        found = set(re.findall(r'"(R-[A-Z-]+)"', _text(ROOT / "roster_replan" / path)))
        unknown = found - registry
        assert not unknown, f"{path} uses rule IDs absent from the registry: {unknown}"


def test_unencoded_rules_are_still_declared_optional(registry):
    """The registry may carry rules the code does not implement, but it has to say so.

    Silently listing an unimplemented rule beside implemented ones is how a registry starts
    describing intent -- exactly the failure the documentation methodology exists to stop.
    """
    rules_md = _text(SPECS / "rules.md")
    for rule in sorted(UNENCODED - {"R-EXAMPLE"}):
        row = next((r for r in rules_md.splitlines() if f"`{rule}`" in r and r.startswith("|")), None)
        assert row is not None, f"{rule} is not in the registry table"
        assert "optional" in row or "input validation" in row, (
            f"{rule} is not encoded but the registry does not mark it optional: {row}"
        )


# --- Decision records ---------------------------------------------------------------


@pytest.fixture(scope="module")
def records() -> list[str]:
    return re.findall(r"^## (D-\d+)", _text(DOCS / "decisions.md"), re.MULTILINE)


def test_no_decision_id_is_used_twice(records):
    """`D-089` was assigned twice — to the rest-gap study and to a service record written in
    parallel — and only a human reading the index caught it."""
    duplicates = {ident for ident in records if records.count(ident) > 1}
    assert not duplicates, f"duplicate decision records: {sorted(duplicates)}"


def test_records_are_in_ascending_order(records):
    """`decisions.md` says a reader can look an ID up directly, which needs them ordered."""
    numbers = [int(ident.split("-")[1]) for ident in records]
    assert numbers == sorted(numbers), "decision records are out of order"


def test_every_referenced_decision_exists(records):
    known = set(records)
    # The Open table lists decisions deliberately not yet written.
    open_rows = set(
        re.findall(r"^\| (D-\d+) \|", _text(DOCS / "decisions.md"), re.MULTILINE)
    )

    dangling: dict[str, set[str]] = {}
    for path in MARKDOWN:
        referenced = set(re.findall(r"`(D-\d+)`", _text(path)))
        missing = referenced - known - open_rows
        if missing:
            dangling[str(path.relative_to(ROOT))] = missing

    assert not dangling, f"references to decisions that do not exist: {dangling}"


def test_code_only_cites_decisions_that_exist(records):
    known = set(records) | set(
        re.findall(r"^\| (D-\d+) \|", _text(DOCS / "decisions.md"), re.MULTILINE)
    )
    dangling: dict[str, set[str]] = {}

    for path in sorted((ROOT / "roster_replan").rglob("*.py")) + sorted(
        (ROOT / "benchmarks").rglob("*.py")
    ):
        missing = set(re.findall(r"`(D-\d+)`", _text(path))) - known
        if missing:
            dangling[str(path.relative_to(ROOT))] = missing

    assert not dangling, f"code cites decisions that do not exist: {dangling}"


# --- Links --------------------------------------------------------------------------


def test_every_relative_link_resolves():
    """The specs cross-reference heavily; a renamed file breaks them silently."""
    broken: dict[str, list[str]] = {}

    for path in MARKDOWN:
        if not path.exists():
            continue
        for target in re.findall(r"\]\(([^)#][^)]*)\)", _text(path)):
            if target.startswith(("http://", "https://", "mailto:")):
                continue
            resolved = (path.parent / target.split("#")[0]).resolve()
            if not resolved.exists():
                broken.setdefault(str(path.relative_to(ROOT)), []).append(target)

    assert not broken, f"broken relative links: {broken}"
