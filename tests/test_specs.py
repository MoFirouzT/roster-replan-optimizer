"""The specs, checked mechanically. The finish declaration's evidence rather than its claim.

`CLAUDE.md`: *a component is not done until its documentation matches its code*, and the finish
declaration asserted that of every spec at once. An assertion like that is worth what it can
be checked against, so what can be checked is checked here rather than read once and
declared true.

Four things are mechanisable, and each corresponds to a way the documentation has drifted or
could drift:

1. **Every rule the registry says is encoded exists in both readings.** `guide/rules.md` is the
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

import contextlib
import importlib.util
import io
import pathlib
import re

import pytest

ROOT = pathlib.Path(__file__).resolve().parent.parent
DOCS = ROOT / "docs"
GUIDE = DOCS / "guide"
STUDIES = DOCS / "studies"

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
    """Rule IDs from the registry table in `guide/rules.md`."""
    ids = set()
    for line in _text(GUIDE / "rules.md").splitlines():
        # The ID cell links to the rule's own section where one exists, and is bare
        # where the rule is declared but not specified -- accept both shapes.
        match = re.match(r"\|\s*\[?`(R-[A-Z-]+)`\]?(?:\([^)]*\))?\s*\|", line)
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
    rules_md = _text(GUIDE / "rules.md")
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
    # Bare `| D-nnn |` table rows are known IDs that are not records: the Open table, for
    # decisions deliberately not yet written, and Merged and retired, for IDs whose record
    # was merged or retired. A citation to either resolves, which is why neither is dangling.
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


# --- Anchors and fragments ----------------------------------------------------------


def _slug(heading: str) -> str:
    """GitHub's heading slug, near enough for link checking.

    Lowercase, drop everything that is not a word character, a space or a hyphen, then
    hyphenate the spaces. Backticks, em-dashes and bracketed status markers all vanish,
    which is what makes a generated slug fragile enough to be worth pinning with an
    explicit `<a id>` wherever a link has to survive a title edit.
    """
    text = re.sub(r"[^\w\s-]", "", heading.strip().lower())
    return re.sub(r"\s", "-", text)


def _anchors(path: pathlib.Path) -> set[str]:
    text = _text(path)
    explicit = set(re.findall(r'<a id="([^"]+)"></a>', text))
    headings = {_slug(m) for m in re.findall(r"^#{1,6} (.+)$", text, re.MULTILINE)}
    return explicit | headings


def test_every_record_has_an_anchor():
    """`D-0NN` is cited over 800 times in the docs and every citation is a link.

    A generated slug moves when a title is edited, so each record carries an explicit
    anchor and the links point at that.
    """
    text = _text(DOCS / "decisions.md")
    missing = [
        ident
        for ident in re.findall(r"^## (D-(?:\d+))", text, re.MULTILINE)
        if f'<a id="{ident.lower()}"></a>' not in text
    ]
    assert not missing, f"records with no anchor: {missing}"


def test_the_lookup_lists_every_record_exactly_once():
    """`decisions.md` says the lookup is the whole set in ID order, and that is checkable.

    A record missing from it is unreachable by the route the file tells a reader to use, and a
    lookup row with no record is a link into nothing. Both are the kind of claim a file makes
    about itself that nothing notices going stale -- the by-theme index was four records behind
    when the curation pass found it.
    """
    text = _text(DOCS / "decisions.md")
    records = re.findall(r"^## (D-\d+)\.", text, re.MULTILINE)
    lookup = re.findall(r"^\| \[`(D-\d+)`\]\(#d-\d+\) \|", text, re.MULTILINE)

    assert lookup == sorted(set(lookup)), "the lookup is out of order or lists an ID twice"
    assert set(lookup) == set(records), (
        f"lookup rows with no record: {sorted(set(lookup) - set(records))}; "
        f"records missing from the lookup: {sorted(set(records) - set(lookup))}"
    )


def test_every_record_sits_under_at_least_one_theme():
    """The by-theme index is the second way in, and a record under no theme is missing from it.

    It is maintained by hand, so it falls behind silently: `D-146` to `D-149` were under no theme
    at all until this was written. A record may sit under more than one; the grouping is not a
    partition, so only the empty case is a defect.
    """
    text = _text(DOCS / "decisions.md")
    records = set(re.findall(r"^## (D-\d+)\.", text, re.MULTILINE))
    themes = text.split("## By theme", 1)[1].split("\n---", 1)[0]
    themed = set(re.findall(r"D-\d+", themes))

    assert not (records - themed), f"records under no theme: {sorted(records - themed)}"
    assert not (themed - records), f"themed IDs with no record: {sorted(themed - records)}"


def test_every_fragment_link_resolves():
    """`test_every_relative_link_resolves` drops the fragment; this is the other half.

    A link to `decisions.md#d-119` that lands at the top of a 4,000-line file is a
    reference the reader has to finish by hand, which is the failure this whole
    cross-reference scheme exists to remove.
    """
    broken: dict[str, list[str]] = {}
    cache: dict[pathlib.Path, set[str]] = {}

    for path in MARKDOWN:
        if not path.exists():
            continue
        for target in re.findall(r"\]\(([^)]+)\)", _text(path)):
            if target.startswith(("http://", "https://", "mailto:")) or "#" not in target:
                continue
            filename, fragment = target.split("#", 1)
            resolved = (path.parent / filename).resolve() if filename else path
            if not resolved.exists() or resolved.suffix != ".md":
                continue
            if resolved not in cache:
                cache[resolved] = _anchors(resolved)
            if fragment not in cache[resolved]:
                broken.setdefault(str(path.relative_to(ROOT)), []).append(target)

    assert not broken, f"links to anchors that do not exist: {broken}"


# --- The studies index against the studies -------------------------------------------


def test_the_studies_index_and_the_studies_agree():
    """A row with no file sends the reader nowhere; a file with no row cannot be found.

    Both existed: `studies/reproducibility.md`, `studies/warm-start.md` and
    `studies/time-budget.md` were indexed for months as plain text, and `README.md` named the
    first as the one thing to read.
    """
    index = _text(STUDIES / "README.md")
    linked = set(re.findall(r"\[`([a-z-]+\.md)`\]\(\1\)", index))
    present = {p.name for p in STUDIES.glob("*.md")} - {"README.md"}

    assert not (linked - present), f"indexed studies with no file: {sorted(linked - present)}"
    assert not (present - linked), f"studies missing from the index: {sorted(present - linked)}"


# --- The record budget ---------------------------------------------------------------

RECORD_CAP = 340


def test_no_record_exceeds_the_word_cap():
    """`decisions.md` states a 300-word budget and a 340-word cap; this is the cap.

    The file reached a 343-word mean without one, because a record that restates its own
    study reads like diligence while it is being written. The cap is set where editing the
    thirty longest records actually landed them -- between 259 and 332 words -- rather than
    at a round number that would force the argument out of a record and into nothing.
    """
    text = _text(DOCS / "decisions.md")
    records = re.findall(r"^## D-\d+\. .+?(?=^<a id=\"d-|\Z)", text, re.MULTILINE | re.DOTALL)
    assert records, "no records parsed -- the heading or anchor shape changed"

    over = {
        re.match(r"^## (D-\d+)", record).group(1): len(record.split())
        for record in records
        if len(record.split()) > RECORD_CAP
    }
    assert not over, (
        f"{len(over)} records over the {RECORD_CAP}-word cap "
        f"(move the analysis to the study): {dict(sorted(over.items(), key=lambda kv: -kv[1]))}"
    )


# --- The worked profile in configuring.md --------------------------------------------


def _demo_profile():
    """`horeca-2026.1`, assembled from the scenario the quickstart runs.

    Not a fixture built by hand: the point of the example in `guide/configuring.md` is that it
    is the profile a reader can run, so it is read from the same file `demo.py` reads.
    """
    import json

    from roster_replan import profile as P
    from roster_replan.service import contracts

    payload = json.loads((ROOT / "scenarios" / "saturday_sick_call.json").read_text())
    request = contracts.ReplanRequest.model_validate(payload)
    instance = contracts.to_domain(request.instance)
    return P.Profile(
        version=request.profile_version,
        shift_types=instance.shift_types,
        params=instance.params,
        disruption=instance.disruption,
        fairness=instance.fairness,
    ), instance


def test_the_worked_profile_matches_the_scenario():
    """Every value shown in `guide/configuring.md`'s profile is the one in the scenario file.

    A pasted example is a claim about code that nothing re-reads. This one is small enough
    to check field by field, and the failure it prevents is the quiet one: a weight changes
    in the scenario and the guide keeps teaching the old number.
    """
    profile, _ = _demo_profile()
    shown = re.search(
        r"```python\n(Profile\(.*?)\n```", _text(GUIDE / "configuring.md"), re.DOTALL
    )
    assert shown, "no worked profile in configuring.md -- has the fence moved?"
    block = shown.group(1)

    assert f'version="{profile.version}"' in block
    for shift in profile.shift_types:
        assert (
            f'ShiftType(label="{shift.label}", start_hour={shift.start_hour}, '
            f"span_hours={shift.span_hours}, break_hours={shift.break_hours})"
        ) in block, f"{shift.label} differs from the scenario"

    for field in ("min_rest_hours", "min_weekly_rest_hours", "min_period_hours", "max_consecutive_days"):
        assert f"{field}={getattr(profile.params, field)}," in block, field
    for field in ("metric", "published_weight", "draft_weight", "shortfall_weight", "cost_weight"):
        value = getattr(profile.disruption, field)
        rendered = f'"{value}"' if isinstance(value, str) else value
        assert f"{field}={rendered}," in block, field
    for band in profile.disruption.notice_bands:
        within = "inf" if band.within_hours == float("inf") else band.within_hours
        assert f"NoticeBand(within_hours={within}, multiplier={band.multiplier})" in block

    assert (profile.fairness is None) == ("fairness=None" in block)


def test_the_quoted_remarks_are_what_review_returns():
    """`guide/configuring.md` quotes the subsumption verdict; this re-derives it.

    The remark text is prose inside `profile.py` and reads like something safe to reword.
    It is quoted in the guide, so rewording it silently makes the guide describe output the
    service no longer produces.
    """
    import dataclasses

    from roster_replan import profile as P

    profile, instance = _demo_profile()
    loosened = dataclasses.replace(
        profile, params=dataclasses.replace(profile.params, max_consecutive_days=9)
    )
    produced = {remark.field: remark.message for remark in P.remarks(loosened, sample=instance)}

    quoted = re.search(r"```text\n(params\.max_consecutive_days.*?)\n```",
                       _text(GUIDE / "configuring.md"), re.DOTALL)
    assert quoted, "no remarks block in configuring.md"
    block = " ".join(quoted.group(1).split())

    for field, message in produced.items():
        assert f"{field} {message}" in block, f"{field}: guide and `remarks` disagree"
    assert len(produced) == block.count("params.") + block.count("disruption."), (
        "the guide shows a different number of remarks than `review` returns"
    )


# --- Documentation citations in source ------------------------------------------------


def _lint_module():
    """`scripts/lint_docs.py` is a script rather than a package, so it is loaded by path."""
    spec = importlib.util.spec_from_file_location("lint_docs", ROOT / "scripts" / "lint_docs.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_a_citation_resolves_against_the_root_then_docs():
    """The rule `D-152` fixed, asserted in both directions.

    Asserting only that the tree is clean would pass just as well if the rule accepted
    everything, which is exactly the failure the 88 dead citations were: a claim nothing
    could reject. So the negative cases are the point of this test, and the unqualified
    rules filename is the one that matters: it is a real file twice over, under `guide/`
    and under `specs/`, and it is a path to neither.
    """
    lint = _lint_module()

    assert lint.citation_resolves("CLAUDE.md")
    assert lint.citation_resolves("decisions.md")
    assert lint.citation_resolves("guide/rules.md")
    assert lint.citation_resolves("internals/model.md")
    assert lint.citation_resolves("studies/encoding-levers.md")

    assert not lint.citation_resolves("rules.md")
    assert not lint.citation_resolves("replan.md")
    assert not lint.citation_resolves("PLAN.md")


def test_no_source_citation_names_a_missing_document():
    """The regression guard over the tree, after `D-152`'s 153 were repointed."""
    lint = _lint_module()
    errors: list[str] = []
    lint.check_source_citations(errors)
    assert not errors, "dead documentation citations:\n  " + "\n  ".join(errors)


# --- Stale duplicated figures ---------------------------------------------------------


def test_a_figure_reads_the_same_spelled_out_as_in_digits():
    """The four stale copies were all "ten of thirteen", never "10 of 13".

    A check reading digits only would have caught none of them, so the word forms are
    the load-bearing half of `normalise_figure` rather than a nicety.
    """
    lint = _lint_module()

    assert lint.normalise_figure("ten") == "10"
    assert lint.normalise_figure("**Eight**") == "8"
    assert lint.normalise_figure(" Thirteen ") == "13"
    assert lint.normalise_figure("1,024") == "1024"
    assert lint.normalise_figure("8") == "8"
    assert lint.normalise_figure("OPTIMAL") == "optimal"


def test_a_figure_is_identified_by_context_on_either_side_of_the_number():
    """The words naming a figure sit wherever the sentence puts them.

    Looking only forward from the number missed every copy in the incident this check
    was built from: *the illegal-past figure falls from 10 of 13* names the figure
    before it, and *10 of 13 published rosters* after it. Both are the same claim.
    """
    lint = _lint_module()
    pattern = re.compile(r"\b(\d+) of 13\b")
    context = re.compile(r"(?i)illegal|published roster")

    after = lint.figure_hits(pattern, "**10 of 13 published rosters** overstaff", context)
    before = lint.figure_hits(pattern, "the illegal-past figure falls from 10 of 13", context)
    unrelated = lint.figure_hits(pattern, "a non-best solution on 8 of 13 instances", context)

    assert [h[1] for h in after] == ["10"]
    assert [h[1] for h in before] == ["10"]
    assert unrelated == []


def test_a_line_marked_lint_ok_states_a_superseded_figure_on_purpose():
    lint = _lint_module()
    pattern = re.compile(r"\b(\d+) of 13\b")
    text = "10 of 13 rosters <!-- lint-ok: as first published -->\n8 of 13 rosters\n"

    assert [h[1] for h in lint.figure_hits(pattern, text)] == ["8"]


def _figure_tree(tmp_path, registry: str, docs: dict[str, str]):
    """A whole tree the figure check can run against, so it can be shown to reject one."""
    lint = _lint_module()
    (tmp_path / "scripts").mkdir()
    (tmp_path / "scripts" / "figures.toml").write_text(registry, encoding="utf-8")
    written = []
    for name, body in docs.items():
        path = tmp_path / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(body, encoding="utf-8")
        written.append(path)
    lint.ROOT = tmp_path
    lint.DOC_PATHS = written
    lint.FIGURES_FILE = tmp_path / "scripts" / "figures.toml"
    return lint


PINNED_REGISTRY = r"""
[[figure]]
id = "illegal-past"
owner = "study.md"
kind = "pinned"
reproducible = "no"
pattern = '(?i)\b(\d+|[a-z]+) of (?:13|thirteen)\b'
context = '(?i)illegal'
"""


def test_the_figure_check_rejects_a_copy_that_disagrees_with_its_owner(tmp_path):
    """The rejection, not the clean tree.

    A rule that has never rejected anything is not known to reject anything, which is
    `D-152`'s defect in another form: 88 dead citations sat behind a check that could
    not fail. So the disagreeing copy is asserted directly, in the spelling the real
    incident used.
    """
    lint = _figure_tree(
        tmp_path,
        PINNED_REGISTRY,
        {
            "study.md": "**Eight of thirteen have an illegal past** <!-- fig:illegal-past -->\n",
            "guide.md": "ten of thirteen published rosters have an illegal past\n",
        },
    )
    errors: list[str] = []
    lint.check_figures(errors)

    assert len(errors) == 1
    assert "guide.md:1" in errors[0]
    assert "illegal-past" in errors[0]


def test_the_figure_check_accepts_a_copy_that_agrees(tmp_path):
    lint = _figure_tree(
        tmp_path,
        PINNED_REGISTRY,
        {
            "study.md": "**Eight of thirteen have an illegal past** <!-- fig:illegal-past -->\n",
            "guide.md": "8 of 13 published rosters have an illegal past\n",
        },
    )
    errors: list[str] = []
    lint.check_figures(errors)

    assert not errors, errors


def test_a_registry_entry_that_covers_nothing_is_reported(tmp_path):
    """A registry matching nothing reads exactly like a registry matching something.

    That is the failure this component exists to prevent, one level up, so the entry is
    checked as hard as the documents are.
    """
    lint = _figure_tree(
        tmp_path,
        PINNED_REGISTRY,
        {"study.md": "the past is illegal <!-- fig:illegal-past -->\n"},
    )
    errors: list[str] = []
    lint.check_figures(errors)

    assert len(errors) == 1
    assert "matches nothing" in errors[0]


def test_an_owner_that_lost_its_marker_is_reported(tmp_path):
    lint = _figure_tree(
        tmp_path,
        PINNED_REGISTRY,
        {
            "study.md": "**Eight of thirteen have an illegal past**\n",
            "guide.md": "8 of 13 published rosters have an illegal past\n",
        },
    )
    errors: list[str] = []
    lint.check_figures(errors)

    assert len(errors) == 1
    assert "no `<!-- fig:illegal-past -->` line" in errors[0]


def test_a_derived_figure_is_recounted_from_the_repository(tmp_path):
    """`derived` is the half nothing has to remember to update: it is recomputed."""
    lint = _figure_tree(
        tmp_path,
        r"""
[[figure]]
id = "rows"
owner = "ledger.md"
kind = "derived"
compute = "rows"
reproducible = "computed"
pattern = 'Every ledger row [^\n]{0,90}?(\d+) of \d+'
""",
        {"ledger.md": "Every ledger row names its spec. **16 of 16.**\n"},
    )
    lint.COMPUTED = {**lint.COMPUTED, "rows": lambda: 20}
    errors: list[str] = []
    lint.check_figures(errors)

    assert len(errors) == 1
    assert "stated as 16" in errors[0] and "counts 20" in errors[0]


def test_no_registered_figure_is_stated_two_ways_in_this_tree():
    """The regression guard over the tree, and the registry's own self-check."""
    lint = _lint_module()
    errors: list[str] = []
    lint.check_figures(errors)
    assert not errors, "figures that disagree with their owner:\n  " + "\n  ".join(errors)


def test_the_coined_word_check_does_not_depend_on_the_host_dictionary():
    """The lint verdict must not be a property of the machine that produced it.

    `/usr/share/dict/words` is a different file on every OS: macOS ships `web2`, a 1934
    Webster's of 236k entries, and CI's `wamerican` is a modern list about a third that
    size. A word only the larger one has lints clean on a laptop and red in CI, which is
    what `REPO_VOCABULARY` exists to prevent and what it silently stopped covering:
    `assertable` reached `main` and CI is where it was caught, one commit later.

    So the claim is asserted at its strongest. With no dictionary at all, only
    `REAL_ADJECTIVES` and `REPO_VOCABULARY` remain, and any real word list is a superset
    of that; a tree clean here is clean on every host. Regenerate by reading the failure:
    each word it names is either real English and belongs in `REPO_VOCABULARY`, or coined
    and the sentence is rewritten.
    """
    lint = _lint_module()
    lint.WORD_LIST = set()
    buf = io.StringIO()
    with contextlib.redirect_stdout(buf):
        code = lint.main()

    coined = re.findall(r"coined word '([^']+)'", buf.getvalue())
    assert not coined, (
        "these lint clean here and would fail on a smaller system dictionary: "
        f"{sorted(set(coined))}"
    )
    assert code == 0, buf.getvalue()
