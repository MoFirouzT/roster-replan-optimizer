# Curating the decision records

**Status:** Implemented 2026-09-02
**Unit:** component (documentation, no change to `roster_replan/`)  **Depends on:**
[`documentation-restructure.md`](documentation-restructure.md)

## Objective

Bring the 150 records in [`decisions.md`](../decisions.md) onto the curated contract:
every surviving record says what governs the code today, a record that only restates a
ledger row is merged into the record that carries the argument, nothing is kept in a
state known to be false, and not one inbound link or anchor breaks.

## Motivation

The restructure left this out of scope on purpose: it made the records editable, and
deciding which of them should exist is judgment over content rather than a move.

What is owed now is concrete. `decisions.md` still opens by stating the rule the
restructure removed: that a record is *permanently true*, that it is amended in place
and *never rewritten and never deleted*. `CLAUDE.md` says records are curated. The file
and the contract governing it disagree in writing, and the file is canonical, so this is
the first thing the unit fixes rather than something it works around.

Two measurements say what kind of file this is. The records total 38,577 words over 150
of them: mean 257, median 267, and **not one is over the 340-word cap**. Per record the
file is disciplined. The open question is how many records there should be, which the cap
cannot see. And the by-theme index already covers **146 of 150**: `D-146` through `D-149`
sit under no theme at all, which is what an index maintained by hand does over time.

The ledger made this possible. Fifteen rows now carry the project's history, so a record
that only restates one has somewhere to be merged into, and nothing is lost by merging it.

## What earns a record

The test, applied record by record, with three outcomes.

**A record earns its place when reversing what it decided would be expensive**: it would
invalidate a gate, force a re-derivation, or change a published number. That is the
contract's test and it is not weakened here.

**A record that a ledger row already carries, and that adds no reasoning beyond the row,
is a merge candidate.** A record carrying the reasoning the row compresses is not: the row
is one line and is meant to be, and the reasoning behind it has to live somewhere.

Three outcomes:

| Outcome | What happens | What the file shows afterwards |
| --- | --- | --- |
| **Keep** | The record stands, corrected in place where a figure or a reading has been superseded | The record, naming the correction and the record that made it |
| **Merge** | Its argument moves into the record that owns that argument | The survivor, naming what it absorbed and when; the merged ID as a tombstone row |
| **Retire** | It governs nothing: what it decided is gone, or a later record replaced it | The tombstone row, naming the replacement and **why the old reading was wrong** |

Four things are **not** reasons to merge or retire, and a classification resting on one of
them is wrong:

- age, or which tier the record was written in
- being cited by nothing outside `decisions.md`
- being short
- being about code that has since been deleted. A record saying why something is not there
  still governs: reversing it means building the thing again ([`D-149`](../decisions.md#d-149) is the worked case)

## The count: estimated 110 to 125, landed 137

The estimate is kept because being wrong is the finding.

**It predicted 110 to 125** from three measurements: 46 records link a study; 105 are
cited by at least one document outside `decisions.md` and 45 by none; 35 of those 45 sit
in runs of consecutive IDs, which was read as one batch about one subject and therefore
as where merge candidates collect.

**Reading all 150 gave 137**, and the estimate was wrong in a way worth recording:

- **The predicted pool is not a pool.** The consecutive run is mostly the T1 rule-encoding
  batch, `D-019` to `D-037`. Each fixes a distinct predicate, convention or registry
  identity that both readings implement, so reversing any one of them changes a rule.
  They are cited by no live document because the rules documents cite **rule IDs**, not
  record links. Consecutive IDs meant one working session, not one argument.
- **No record only restated a ledger row.** Zero candidates on the criterion this unit was
  framed around. The rows were reconstructed *from* the records, so a row compresses
  several and duplicates none.
- **What was removable sat at the other end of the file**: records a later record on the
  same subject had replaced. Four of the five retirements are `D-093` and above.

The band did what a tripwire is for: it stopped the work and sent the reading back for
review rather than being quietly satisfied. **The count is 137**: 150 less 5 retired and
9 merged, plus [`D-151`](../decisions.md#d-151) written for a decision that never had one.

## The two indexes

Both stay. They answer different questions and both are cheap to regenerate.

- **Lookup** is rebuilt from the surviving set, still in ascending ID order. IDs now have gaps, which the ordering test allows and which the tombstone table explains.
- **By theme** is re-derived from the surviving set rather than edited down. A theme left with one record is folded into its nearest neighbour, and every surviving record lands under at least one theme, including the four that are under none today.
- **Open: to be written as they are made** stays as it is. Its two rows are still owed and neither is a record.
- **Merged and retired** is new, and is where every ID that stops being a record goes.

## How the links survive

This is the part that can silently break, so it is stated before the tasks and it is what
the gate mostly checks.

What points at these records today:

| Source | Links | May it be edited? |
| --- | --- | --- |
| The 17 studies, the studies index, and `benchmarks.md` | **210** | **No.** Measurements are durable |
| `specs/README.md`, `design.md`, `STATE.md`, `model.md`, `README.md`, `CLAUDE.md` | **114** | Yes, these are live |
| Cross-references inside `decisions.md` itself | **558** | Yes |
| Backticked `D-nnn` in `roster_replan/` and `benchmarks/` | 162, over 60 distinct IDs | Out of scope here |
| Backticked `D-nnn` in `tests/` | 166, over 67 distinct IDs | Out of scope here |

**The rule is that no anchor is ever removed.** An ID that stops being a record keeps its
`<a id="d-nnn"></a>`, which moves into the *Merged and retired* table on a row naming where
its reasoning went and why. Every existing link then still lands somewhere that answers the
reader, one hop from the record it wanted.

That one rule satisfies five checks that already exist, with no test loosened:

- the linter's `check_anchors`, which resolves every cross-document `file.md#anchor` link
- `test_every_fragment_link_resolves`, which reads explicit `<a id>` anywhere in the file, not only at a heading
- `test_every_record_has_an_anchor`, which looks only at `## D-nnn` headings and so is unaffected by a tombstone
- `test_every_referenced_decision_exists` and `test_code_only_cites_decisions_that_exist`, whose known set is the `## D-nnn` headings **plus every bare `| D-nnn |` table row**. A tombstone row shaped `| D-034 | merged into ... |` matches that pattern, so a retired ID stays known to both tests without touching either. Their comment says the table it means is the Open table, and that comment is now wrong: it is a comment, and correcting it weakens nothing.

It also settles the durable half without an argument: a study never has to be edited
because a record elsewhere was merged.

## Build tasks

Ordered. Task 2 ends in a review, and nothing after it starts before that review.

- [x] 1. Rewrite the preamble of `decisions.md`: records are curated, a supersession names
      what it replaced and why the old reading was wrong, and nothing is kept in a state
      known to be false. Keep the 300-word budget, the 340-word cap, and the rule that a
      record states its decision rather than its analysis. Keep the `*Assumes:*` line.
- [x] 2. Read all 150 against the test above and classify each keep, merge or retire, with
      the reason on the row, in a working table in `planning/`. **Bring the classification
      to review before any record moves.** Done in
      `planning/decision-curation-classification.md`; **the review changed three things**:
      the expected count, one borderline merged (`D-046`), and a record written for the
      two-door split.
- [x] 3. Apply the merges. The survivor names what it absorbed and the date. **Nine**:
      `D-007`→`D-049`, `D-008`→`D-018`, `D-030`→`D-040`, `D-042`→`D-004`, `D-046`→`D-045`,
      `D-056`→`D-053`, `D-107`→`D-105`, `D-110`→`D-111`, `D-147`→`D-127`.
- [x] 4. Apply the retirements, and correct in place every record carrying a figure or a
      reading that has been superseded, naming the record that superseded it. **Five
      retired** (`D-048`, `D-093`, `D-106`, `D-117`, `D-118`) and **five corrected**:
      `D-081`'s dead premise, `D-083`'s superseded tie count, `D-095`'s and `D-146`'s
      references to documents that left the repository, and `D-120`'s citation of
      `finish.md`.
- [x] 5. Write the *Merged and retired* table, carrying every removed ID's anchor. 14 rows.
- [x] 6. Regenerate the lookup table; re-derive the by-theme index from the survivors.
      137 lookup rows, 14 themes, every record under at least one.
- [x] 7. Retarget the live-document links where a merge moved which record owns the claim.
      **Five**: three in the ledger, one in `design.md`, and the two-door citation in
      `STATE.md` and the ledger. The 210 links from studies and `benchmarks.md` are
      untouched by design.
- [x] 8. Update the record count where it is stated: `docs/README.md`, the `STATE.md` repo
      table, and the `LINE_CAP_EXEMPT` comment in `scripts/lint_docs.py`.
- [x] 9. Add the two index tests. Both were **proven by hand before being trusted**: removing
      two lookup rows and one theme entry fails them, and the restored file passes.
- [x] 10. Write the ledger row, and rewrite the documentation section of `STATE.md`.

## Acceptance gate

*Blocks:* nothing. The project is closed and this is a documentation unit. The unit is not
done until every box carries a record.

- [x] Every one of the 150 `<a id="d-nnn">` anchors is still present. **`comm -23` over the
      sorted anchor sets is empty**; 150 before, 151 after, the addition being `d-151`.
- [x] `uv run python scripts/lint_docs.py` exits zero. **`Doc lint: OK (40 files)`.**
- [x] `uv run pytest tests/test_specs.py` passes: no duplicate ID, ascending order, every
      referenced ID resolves, every record has an anchor, every fragment link resolves, and
      no record over the 340-word cap. **16 passed**, the 14 before plus this unit's two.
- [x] `uv run pytest` passes. **935 passed**: the 933 before, plus the two index tests.
- [x] **No record is over the cap.** This box said no first, as expected: after the merges
      **eight records were over**, `D-105` at 434 and `D-018` at 397. Each was compressed to
      its decision rather than split or concatenated. Every record is now inside 340, and
      `D-105` and `D-111` sit at 339.
- [x] Every removed ID appears exactly once in the *Merged and retired* table, with a
      destination and a reason. **14 rows, matching the 14 IDs that lost their heading.**
- [x] Every merge survivor names what it absorbed. Every retirement names what replaced it
      and why the old reading was wrong. **Nine `Absorbs` lines, and five retirements named by the four records that replaced them.**
- [x] No surviving record repeats a figure that a later record superseded without naming
      that record. **Two found and corrected**: `D-081`'s build-dominates premise, which
      [`D-119`](../decisions.md#d-119) reversed, and `D-083`'s 64 of 72 against
      [`D-105`](../decisions.md#d-105)'s 71 of 84.
- [x] The lookup table lists every surviving record exactly once and nothing else, and
      every surviving record appears under at least one theme. **Both are now tests**, not
      a one-off check.
- [x] `git diff --name-only` names nothing under `docs/studies/` and not `docs/benchmarks.md`.
- [x] `git diff --name-only` names nothing under `roster_replan/` or `benchmarks/`, and
      nothing under `tests/` beyond `test_specs.py`.
- [x] The count is the same in the ledger row, `STATE.md` and `docs/README.md`. **137.**
- [!] `uv run python -m tests.mutation` is **not** re-run: no line in `roster_replan/` or
      `benchmarks/` moved. The premise is not exactly met, because task 9 adds two tests.
      They are new checks in an existing layer rather than a new layer, and **no mutant can
      express them**: the harness mutates Python source, and these two assert a Markdown
      file against itself. They were proven by hand instead, which is what a mutant would
      have established.

Record a box only against evidence. `- [x]` passed, `- [!]` ran and did not, with the
result on the line, `- [ ]` no record.

## Out of scope

- **`README.md` still has no runnable command.** A reader arriving at the repository root
  cannot get from it to a solve without reading something else first. Separate, small, and
  independent of this. **Unchanged by this unit.**
- Splitting `decisions.md` into one file per record, and renaming the IDs to subjects. See
  decision 1.
- Any change to a study or to `benchmarks.md`. Measurements are durable, and the tombstone
  design exists so that this unit never needs to touch one.
- Any change to `roster_replan/` or `benchmarks/`, including the 162 `D-nnn` citations in
  their docstrings.
- Re-measuring anything. A record with a stale figure is corrected against the study that
  already holds the number, or it says the figure is unconfirmed. Nothing is re-run.
- The ledger rows themselves, beyond adding this unit's own.

## Decisions

Posed with a proposal, resolved at review on 2026-09-02. The proposals are kept, so this is
the decision trail.

1. **The IDs stay numeric, against the shared contract, which says records are named by
   subject and unnumbered so one can be merged without leaving a gap.**
   *Proposed:* keep `D-nnn`, and record it as an `## Overrides` entry in `CLAUDE.md`
   naming the rule and the reason. The reason is measured: 324 links in the doc set, 328
   backticked citations in code and tests, and an anchor scheme five checks are built on.
   The contract's own reason for dropping numbers is that a gap embarrasses a numbering,
   and the tombstone table answers that directly: a gap here is a row that says where the
   record went.
   **Resolved: as proposed.** The `## Overrides` section is written. This is the project
   winning on a rule that was never general, not the rule being dropped.

2. **Does `decisions.md` stay one file?**
   *Proposed:* yes, and it stays exempt from the 600-line cap. About 115 records is still
   roughly 2,900 lines, so curation does not bring the file under the cap and was never
   going to.
   **Resolved: as proposed.** 137 records and **3,565 lines**, against a 600-line cap: curation
   was never going to bring it under. The exemption's comment now says that, rather than
   reading as though it expires with this unit.

3. **Which inbound links are retargeted.**
   *Proposed:* the 114 from live documents, where a merge moved which record owns the
   claim. The 210 from studies and `benchmarks.md` are left, because editing a durable
   measurement to follow a change elsewhere is what durable is meant to prevent. The 162 in
   `roster_replan/` and `benchmarks/` are left, because a documentation unit should not
   appear in the solver's diff.
   **Resolved: as proposed**, and the code half proved itself immediately: `pyproject.toml`
   and `tests/test_suite.py` both cite `D-117`, which this unit retired. Both still resolve,
   to a row that says where it went.

4. **Two new tests over the indexes.**
   *Proposed:* add them. The lookup table lists every record exactly once, and every record
   sits under at least one theme. Both are claims the file makes about itself in prose, and
   the second is false today by four records.
   **Resolved: as proposed.** Both were broken deliberately before being trusted.

5. **Does a record about deleted code get retired?**
   *Proposed:* no. `D-149` deleted the model cache; reversing it means building the cache
   again, which is the expensive-to-reverse test passing rather than failing.
   **Resolved: as proposed.** `D-093`, which *shipped* the cache, is retired; `D-149`,
   which deleted it, is kept. The distinction is whether the decision still governs.

6. **May two study-backed records merge into one?**
   *Proposed:* no. A record that links a study is the decision that study fed, and merging
   two of them leaves one record answering to two measurements.
   **Resolved: as proposed**, with one crossing: `D-107` carried
   [`time-budget.md`](../studies/time-budget.md) and `D-105` carried no study, so the
   survivor inherits the link rather than holding two.

7. **The classification review in task 2.**
   *Proposed:* a hard stop, not a courtesy.
   **Resolved: as proposed**, and it earned its place: the review is what caught that the
   expected count was wrong, before 150 records had been edited to fit it.

8. **A decision with no record: the two-door split of 2026-08-20.** Reading all 150 found
   that [`STATE.md`](../STATE.md) and the [ledger](README.md) both cite
   [`D-146`](../decisions.md#d-146) for the guide/internals split. `D-146` is the trim of
   four documents, from a different commit, and decides something else. The split itself
   left no record.
   *Proposed at review:* write it now as [`D-151`](../decisions.md#d-151) and retarget both
   citations, rather than correcting the citations to point at nothing.
   **Resolved: as proposed.** The record says it was written late and why, because a
   record's date and the day it was written are different facts.

9. **Eight borderline classifications**, each argued both ways in the working table.
   *Proposed at review:* merge one and keep seven. `D-046` merges into `D-045`, because it
   calls itself the smaller of the two comparison narrowings and one record holds both
   rules. The other seven stay: `D-015` and `D-016` carry claims that bind the moment
   capture is built, and `D-013`, `D-031`, `D-033`, `D-103` and `D-138` each decide
   something their neighbour does not.
   **Resolved: as proposed.**

---

*Reasoning behind the contract this unit applies: [`CLAUDE.md`](../../CLAUDE.md). What each component found: [`README.md`](README.md).*
