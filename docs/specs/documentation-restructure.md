# Documentation restructure

**Status:** Implemented 2026-09-02
**Unit:** component (structural, no code change)  **Depends on:** none

## Objective

Bring this project's documentation onto the shared `project-discipline` contract:
no archive tier, a component ledger, curated records, durable studies, and a doc
linter in CI. Change no claim, no number and no code.

## Motivation

Two projects grew the same discipline separately and disagree on where documents
live. The disagreements were settled in the plugin's own decision records, and this
is the second project catching up. The concrete costs today: eight links pointing at
a `docs/specs/` directory that no longer exists, a count that says 149 records where
there are 150, a status document four days behind the repo, and nothing that could
have caught any of them.

## The sorting

Every file in `docs/archive/` goes to exactly one destination. The test is whether a
live document cites it and whether it is still true, never how old it is.

| File | Cited by | Destination |
| --- | --- | --- |
| `decisions.md` | 8 live documents, 302 links | `docs/decisions.md`, a canonical reference |
| `studies/` (17 files + index) | the index is cited from 4 live documents | `docs/studies/`, canonical, durable |
| `benchmarks.md` | `limits.md` footer | `docs/benchmarks.md`, canonical |
| `finish.md` | `limits.md`, `design.md` | splits: see decision 3 |
| `preferences.md` | `design.md` | splits: see decision 2 |
| `capture.md` | `rules.md` | Tier 0: see decision 1 |
| `PLAN.md` | nothing | Tier 0, gitignored |
| `README.md` (archive index) | 4 live documents | deleted; `docs/README.md` absorbs it |

`docs/archive/` does not exist when this is done.

## Build tasks

Ordered. Each step leaves the repository consistent, so the work can stop between
any two.

- [x] 1. Move `decisions.md`, `studies/`, `benchmarks.md` up into `docs/`. Retarget
      every link mechanically. No sentence changes.
- [x] 2. Move `PLAN.md` to `planning/`, gitignored. This removes all eight dead
      `docs/specs/` references at once, since every one of them is in that file.
- [x] 3. Resolve `capture.md`, `preferences.md` and `finish.md` per the decisions
      below, once they are settled.
- [x] 4. Delete `docs/archive/README.md` and fold what a reader still needs into
      `docs/README.md`.
- [x] 5. Write `docs/specs/README.md`: the component ledger, one row per component,
      reconstructed from `finish.md`'s T4 and T5 tables, `PLAN.md`'s tier scoping, and
      the studies. Twelve to fourteen rows expected. **14 rows.** Ran before task 3, so
      the declaration's six findings had rows to move into.
- [x] 6. Write `docs/STATE.md`. The project is closed, so it records that, names the
      documentation split of 2026-08-20 that `finish.md` predates, and lists what is
      still not done. **Folded into task 3**, which had to write it as the destination for
      `finish.md`'s live half. Verified against all three requirements afterwards.
- [x] 7. Add `scripts/lint_docs.py` from the plugin, configured for this project:
      `PACKAGE = "roster_replan"`, `SRC_DIR = ROOT`, `LINE_CAP_EXEMPT` holding
      `docs/decisions.md`, `CANONICAL` naming the canonical documents, and `FORBIDDEN`
      allowing the staffing sense of the word it currently flags in `decisions.md`.
- [x] 8. Add `*Assumes:*` lines to the canonical documents. Keep the existing
      reasoning footers: they answer a different question.
- [x] 9. Remove the em dashes. About 1000 across the repo, `decisions.md` holding 561.
      Punctuation only; no claim, number or decision moves. **1,235 removed.** Verified
      word-for-word against the prior tree with punctuation stripped. One test regex
      (`test_specs.py:285`) parsed the em dash in a record heading and had to follow.
- [x] 10. Fix the 16 coined words the linter flags. Replacements in decision 5.
- [x] 11. Correct "149 decision records" to 150 in `docs/README.md` and wherever else
      the count appears. **Already correct** by tasks 4 and 8; swept the other nine
      structural counts in the live documents and all hold.
- [x] 12. Split `docs/guide/rules.md` (1072 lines). Proposed split in decision 4.
      **Four files, not three**: decision 4 left *Eligibility gates* unassigned, and folding
      its 161 lines into `rules-statutory.md` makes 729, over the cap the split exists for.
      134 / 224 / 576 / 170 lines. Rule IDs unchanged.
- [x] 13. Update `CLAUDE.md`: the unit is the component, records are curated,
      measurements are durable, supersede-never-rewrite is gone, no archive tier.
      Keep the plain-word charter and the glossary, which the plugin adopted from here.
- [x] 14. Wire the linter into CI as its own step. A `docs` job, which installs a system
      word list first: without one the coined-word check skips silently and the job would
      pass having checked nothing.

## Acceptance gate

*Blocks:* nothing. This is a structural unit and the project is closed.

- [x] `uv run python scripts/lint_docs.py` exits zero. **`Doc lint: OK (39 files)`.**
- [x] `docs/archive/` does not exist.
- [x] No link in the repository resolves to a missing file or anchor, verified by the
      linter's own check, which now counts the `<a id="d-nnn">` anchors this project
      uses. The linter checks `file.md#anchor` links; `test_specs.py` checks bare `#anchor`
      fragments and file existence. **Both were needed**: the rules split left a bare
      fragment the linter does not look at, and only the suite caught it.
- [x] Every ledger row names a component, where it lives, and what it found. 14 of 14.
- [x] `git diff` over the move commits contains no change to any number, claim,
      rule ID, or code identifier. Verified by diffing the two sides with links and
      punctuation normalised: 177 lines in task 1, 318 in task 9, zero differences.
      Numbers **were** corrected outside the move commits, deliberately and as this spec's
      motivation required: the record count, the study count, and the six stale figures in
      `STATE.md`'s repo table.
- [x] The full test suite passes unchanged: `uv run pytest`. **933 passed.**
- [!] `uv run python -m tests.mutation` is **not** re-run. It was not, but the premise is
      not exactly met: one docstring line in `roster_replan/model.py` changed, a stale
      `docs/archive/studies/` path. No executable line moved. The standing verdict is in any
      case `unverifiable` (136/136 caught, 2026-08-21) and already names `model.py` among
      its unvouched-for paths, so it vouched for nothing there before this unit either.

Record a box only against evidence. `- [x]` passed, `- [!]` ran and did not, with the
result on the line, `- [ ]` no record.

## Out of scope

- **Curating the 150 records.** They become editable under this change; deciding which
  to merge or retire is judgment over content and is a separate unit. Until then the
  set stays as it is, and `docs/decisions.md` is exempt from the line cap.
- Any change to `roster_replan/` or `tests/`.
- Re-running benchmarks or studies. Every number is carried across untouched.
- Badges and README presentation. Separate, small, and independent of this.

## Decisions

Each was posed with a proposal and resolved at review on 2026-09-02. The proposals are
kept, so this section is the decision trail rather than a list of answers given
elsewhere.

1. **`capture.md` is cited by a live document but describes work that was specified
   and never built.** The two sorting tests disagree.
   *Proposed:* Tier 0. It is a plan for unbuilt work, which is what Tier 0 is for, and
   the one citation in `rules.md:1040` becomes prose without a link: the sentence
   already says "specified and not built" and loses nothing.
   **Resolved: as proposed** (2026-09-02). A citation to a plan is not the same as a
   citation to a claim, so the sorting test reads "is anything relying on it", and
   nothing is.

2. **`preferences.md` is two documents.** The first half measures what the objective
   can express across weeks, with a table tied to `disruption.objective_terms`. The
   second is what remains of a catalogue of 23 proposals, four of which shipped.
   *Proposed:* the measured half becomes `docs/studies/cross-week-reach.md`, a durable
   measurement with its conditions stated. The proposal remainder goes to Tier 0.
   `design.md:87` retargets to the study.
   **Resolved: as proposed** (2026-09-02). The study must carry the conditions it was
   measured under, which the current text leaves implicit: the objective terms as
   shipped, and the three scalars of employee memory the payload carries.

3. **`finish.md` carries a declaration preserved verbatim including sentences later
   work made false**, justified by supersede-never-rewrite, which this change removes.
   *Proposed:* "Where the project stands" becomes `docs/status.md`, live and correct.
   The declaration goes to Tier 0. What it got wrong is not lost: those six items are
   findings and belong in ledger rows, which is where a reader will look for them.
   **Resolved: as proposed** (2026-09-02), with one condition: the six items move to
   ledger rows **before** the declaration leaves, not after, so there is no commit in
   which they exist nowhere.

4. **`docs/guide/rules.md` is 1072 lines** and is a live document, so the cap applies.
   Its sections are Registry, Legal sources, The reference period, Operational rules
   (216 lines), Structural legal rules (568), Eligibility gates.
   *Proposed:* three files. `rules.md` keeps the registry, the legal sources and the
   reference period and becomes the door. `rules-operational.md` and
   `rules-statutory.md` take the two large sections. Rule IDs are unchanged, so every
   `R-REST-GAP` reference in code, tests and prose still resolves.
   **Resolved: as proposed** (2026-09-02). The registry table stays whole in `rules.md`
   and gains a column pointing at the file holding each rule's predicate, so a reader
   still meets every rule in one place.

5. **Sixteen coined words.** *Proposed:* <!-- lint-ok: quotes the words being fixed -->
   `staffable` becomes *can be fully staffed*, `fileable` *can be filed the same day*, <!-- lint-ok -->
   `coverable` *can be covered*, `diffable` *produces a readable diff*, <!-- lint-ok -->
   `enableable` *can be switched on*, `reconstructable` *can be reconstructed*, <!-- lint-ok -->
   `explicably` *in a way that can be explained*. Each is checked in context rather <!-- lint-ok -->
   than substituted blindly, since three sit inside rule prose where the subject
   matters.
   **Resolved: as proposed** (2026-09-02). Where a replacement will not fit the
   sentence, rewrite the sentence rather than keeping the word.

6. **Does `docs/decisions.md` stay one file?** It is 3778 lines, against a preference
   for smaller documents.
   *Proposed:* one file for now, exempt from the cap. Splitting 150 records into 150
   files is the opposite of curating them, and the lookup and by-theme indexes already
   work. Revisit after the curation unit, when the count is known.
   **Resolved: as proposed** (2026-09-02).
