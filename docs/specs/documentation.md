# The documentation: four components, one campaign

**Status:** Implemented 2026-09-02
**Depends on:** none. Each section depends on the one before it.

Four components ran over two days and are held here as one file, merged on 2026-09-03
([`D-157`](../decisions.md#d-157)). They are one campaign: the restructure made the records
editable, curating them made the ledger able to carry a component's history, the specs were
written against that ledger, and the citation sweep repointed what the specs decided the code
should name. Each keeps its own ledger row and its own section here.

None of them changed `roster_replan/`.

## Canonical reference

None. No component here adds a predicate, a formulation or a rule parameter. What each one
decided about the *shape* of the documentation is in [`CLAUDE.md`](../../CLAUDE.md), which is
the live document; this file is the build record behind it.

## Governing reference

None.

---

## The restructure

**Objective.** Bring the documentation onto the shared `project-discipline` contract: no
archive tier, a component ledger, curated records, durable studies, and a doc linter in CI.
Change no claim, no number and no code.

**Motivation.** Two projects grew the same discipline separately and disagree on where
documents live. The disagreements were settled in the plugin's own records, so nothing was
re-argued here. The concrete costs on the day: eight links pointing at a `docs/specs/`
directory that did not exist, a count saying 149 records where there were 150, a status
document four days behind the repository, and nothing that could have caught any of them.

### Where `docs/archive/` went

Every file went to exactly one destination. The test was whether a live document cites it and
whether it is still true, never how old it is. `docs/archive/` does not exist.

| File | Destination |
| --- | --- |
| `decisions.md` | [`docs/decisions.md`](../decisions.md), canonical |
| `studies/` (17 files + index) | [`docs/studies/`](../studies/README.md), canonical and durable |
| `benchmarks.md` | [`docs/benchmarks.md`](../benchmarks.md), canonical |
| `finish.md` | splits: the live half becomes [`STATE.md`](../STATE.md), the declaration goes to Tier 0, and its six findings became ledger rows **before** it left |
| `preferences.md` | splits: the measured half becomes [`cross-week-reach.md`](../studies/cross-week-reach.md) with its conditions stated, the proposal remainder to Tier 0 |
| `capture.md` | Tier 0. A citation to a plan is not a citation to a claim, and nothing relied on it |
| `PLAN.md` | Tier 0, gitignored. This removed all eight dead `docs/specs/` links at once |
| `README.md` (archive index) | deleted; [`docs/README.md`](../README.md) absorbs it |

### What it found

**Worse than what it was called for, and every one of them sat behind a green suite**: eight
dead `docs/specs/` links, a record count wrong by one, a status document four days stale,
`CLAUDE.md` quoting a mutation run that had been superseded, a registry claiming 31 rules
against 26, and a bare anchor the linter cannot see.

`docs/guide/rules.md` was 1072 lines, over the cap. It split into **four** files rather than the
three proposed, because folding *Eligibility gates* into `rules-statutory.md` would have made
729: 134 / 224 / 576 / 170. Rule IDs are unchanged, so every `R-REST-GAP` reference still
resolves, and the registry table stays whole in [`rules.md`](../guide/rules.md) with a column
naming the file that holds each predicate.

**1,235 em dashes removed**, verified word-for-word against the prior tree with punctuation
stripped. One test regex parsed the em dash in a record heading and had to follow.

### Gate

- [x] `uv run python scripts/lint_docs.py` exits zero. **`Doc lint: OK (39 files)`.**
- [x] `docs/archive/` does not exist, and no link resolves to a missing file or anchor.
      **Both checks were needed**: the rules split left a bare fragment the linter does not
      look at, and only `test_specs.py` caught it.
- [x] `git diff` over the move commits contains no change to any number, claim, rule ID or
      code identifier. Diffed with links and punctuation normalised: 177 lines in the move,
      318 in the em-dash pass, zero differences. Numbers **were** corrected outside those
      commits, which is what the motivation asked for.
- [x] `uv run pytest`. **933 passed.**
- [!] `uv run python -m tests.mutation` **not** re-run. One docstring line in
      `roster_replan/model.py` changed, a stale `docs/archive/studies/` path; no executable
      line moved. The standing verdict is `unverifiable` and already names `model.py` among
      its unvouched-for paths.

---

## Curating the decision records

**Objective.** Bring the 150 records onto the curated contract: every survivor says what
governs the code today, nothing is kept in a state known to be false, and not one inbound link
or anchor breaks.

**Motivation.** `decisions.md` still opened by stating the rule the restructure removed, that a
record is permanently true and *never rewritten and never deleted*, while `CLAUDE.md` said
records are curated. The file and the contract governing it disagreed in writing.

### The count: estimated 110 to 125, landed 137

The estimate is kept because being wrong is the finding.

It predicted 110 to 125 from three measurements: 46 records link a study; 105 are cited by at
least one document outside `decisions.md` and 45 by none; 35 of those 45 sit in runs of
consecutive IDs, read as one batch about one subject and therefore as where merge candidates
collect. Reading all 150 gave **137**, and the estimate was wrong in three ways worth recording:

- **The predicted pool is not a pool.** The consecutive run is mostly the T1 rule-encoding
  batch, `D-019` to `D-037`. Each fixes a distinct predicate, convention or registry identity
  that both readings implement, so reversing any one changes a rule. They are cited by no live
  document because the rules documents cite **rule IDs**, not record links. Consecutive IDs
  meant one working session, not one argument.
- **No record only restated a ledger row.** Zero candidates on the criterion the unit was
  framed around, because the rows were reconstructed *from* the records.
- **What was removable sat at the other end of the file**: records a later record on the same
  subject had replaced. Four of the five retirements are `D-093` and above.

The band did what a tripwire is for. It stopped the work and sent the reading back for review
rather than being quietly satisfied, and the review is what caught the wrong expected count
before 150 records had been edited to fit it.

**137 = 150 less 5 retired and 9 merged, plus one written.** Five records were also corrected in
place: `D-081`'s dead premise, `D-083`'s superseded tie count, `D-095`'s and `D-146`'s
references to documents that left the repository, and `D-120`'s citation of `finish.md`.

### No anchor is ever removed

An ID that stops being a record keeps its `<a id="d-nnn"></a>`, which moves into
[Merged and retired](../decisions.md#merged-and-retired) on a row naming where its reasoning
went and why. Every existing link then lands one hop from the record it wanted, which satisfies
all five existing anchor checks with no test loosened, and settles the durable half without an
argument: a study never has to be edited because a record elsewhere was merged. The code half
proved itself immediately, `pyproject.toml` and `tests/test_suite.py` both citing `D-117`,
which this retired.

**A decision with no record.** Reading all 150 found that [`STATE.md`](../STATE.md) and the
[ledger](README.md) both cited [`D-146`](../decisions.md#d-146) for the guide/internals split.
`D-146` is the trim of four documents, from a different commit, and decides something else. The
split itself left no record, and is now [`D-151`](../decisions.md#d-151), which says it was
written late and why: a record's date and the day it was written are different facts.

### Gate

- [x] Every one of the 150 anchors still present. **`comm -23` over the sorted sets is empty**;
      150 before, 151 after, the addition being `d-151`.
- [x] `Doc lint: OK (40 files)`. `uv run pytest`: **935 passed**, the 933 before plus two new
      index tests, both **proven by hand before being trusted**.
- [x] **No record is over the 340-word cap.** This said no first, as expected: after the merges
      eight were over, `D-105` at 434 and `D-018` at 397. Each was compressed to its decision
      rather than split.
- [x] 14 tombstone rows, matching the 14 IDs that lost their heading; nine `Absorbs` lines;
      five retirements named by the four records that replaced them.
- [x] `git diff --name-only` names nothing under `docs/studies/`, `docs/benchmarks.md`,
      `roster_replan/` or `benchmarks/`.
- [!] `uv run python -m tests.mutation` **not** re-run, and the premise is not exactly met: two
      tests were added. They are new checks in an existing layer, and **no mutant can express
      them**, because the harness mutates Python source and these assert a Markdown file against
      itself. Proven by hand instead.

---

## Specs for the built components

**Objective.** Give every built component a spec file holding what a live document does not:
the scope it was built to, its interfaces, the test contract, the gate it passed, what it ruled
out, and the decision trail.

### This project never had a build record

The obvious reading is that [`D-151`](../decisions.md#d-151) threw away seven work orders and
this restored them. That reading is wrong, and it was checked rather than assumed. The seven
files are in git, added whole on 2026-08-11 in `6d8646f` and deleted on 2026-08-20 in `48e86d3`,
and none of them is a work order:

| | `rules` | `model` | `replan` | `validation` | `service` | `config` | `capture` |
| --- | --- | --- | --- | --- | --- | --- | --- |
| Status line | no | no | no | no | no | no | no |
| Build tasks | no | no | no | no | no | no | no |
| Acceptance gate | no | no | no | no | no | no | no |
| Out of scope | no | no | no | no | no | no | no |
| Decisions | no | no | no | no | no | no | no |

What they carried instead was inline `[built]`, `[shipped]` and `[not implemented]` markers,
kept up to date across 7 to 16 commits each. They were **design statements maintained alongside
the code**, which is what `D-151` called them, and moving them into the two doors was right.
Restoring them would put a second owner on every predicate they hold.

So this did not restore a tier. **It created one this project has never had.** The build record
was in the gitignored `planning/`, in `decisions.md` and in the commits, which is defensible
while a project is being built and bad once it is closed, because two of those three cannot be
read by anyone who was not here.

### The honesty rules

A spec written after the code is a reconstruction. It was not reviewed before implementation,
its build tasks were not a plan, and its gate boxes are ticked from evidence found afterwards. A
document that looks like a frozen work order and is not one is worse than no document, and there
is no earlier version to fall back on. Three rules are what make these specs worth keeping:

- **Every reconstructed spec says so on its Status line**, and names what it was built from: the
  code, the live documents, the records, the studies and the commits.
- **A gate box is ticked only against evidence that exists now.** A condition the component
  clearly met but for which no record survives is written as prose in **Measured results**, not
  as a `- [x]`. A reconstruction may not manufacture a tick.
- **The Decisions section cites records rather than inventing a trail.** Where no record exists,
  the section says the reasoning was not written down, which is a true statement about this
  project and a useful one.

**Twelve were written.** Three take a name that differs from the obvious one, because
`docs/benchmarks.md`, `studies/mutation-harness.md` and `studies/foreign-incumbent.md` already
exist and a citation naming one of those would be ambiguous:
[`mutation.md`](mutation.md), [`benchmark-set.md`](benchmark-set.md) and
[`cross-week-rules.md`](cross-week-rules.md). The gap is `config.md`, whose content split across
[`tools.md`](tools.md) and [`nl.md`](nl.md), so its 24 citations named nothing until the sweep
below routed them by file.

Two ledger rows get no spec. The **walking skeleton**'s code was deleted
([`D-146`](../decisions.md#d-146)), and a spec for deleted code describes nothing.
**Capture and replay** is specified and never built, so its work order is the one document here
that was never a reconstruction; it is in Tier 0, at
`git show 48e86d3^:docs/specs/capture.md`, and whether a plan that is *blocked* rather than
merely unstarted belongs in Tier 0 or in **In flight** was left open deliberately.

### Gate

- [x] `Doc lint: OK (54 files)`. `uv run pytest`: **935 passed**, the same count as before:
      nothing here adds or removes a test. The suite caught two things in this unit's own
      writing, a `D-152` forward reference made before the record existed, and `D-151` going
      over the word cap once its superseded pointer was added.
- [x] Every one of the twelve says it is a reconstruction and names its sources. The two written
      earlier correctly carry no such line.
- [x] No spec restates a predicate, a formulation section or a rule parameter. Every one carries
      a **Canonical reference** section, and no fenced predicate block was copied here.
- [x] No claim, number or rule ID in `guide/`, `internals/` or `studies/` changed.
- [x] Every ledger row names its spec or says why it has none. **16 of 16** on 2026-09-02; the live count is in the [ledger](README.md). <!-- lint-ok: a gate outcome, not the live count -->
- [x] **106 ticked boxes and 30 `- [!]` ones** across the twelve, every `- [!]` saying what
      happened on the line. Close to one condition in five came back qualified rather than
      passed, and that ratio is worth reading on its own.
- [!] **The linter checks stay inert, deliberately.** `check_spec_status` and the module
      reference check now bind fourteen files rather than two and caught nothing new. The
      `Depends on:` graph check stays dead, because this project's unit is the component and not
      the delivery pass, so no spec owns a phase ID.

**What it left open.** Eighty-eight citations in `roster_replan/`, `tests/` and `benchmarks/`
named a spec file deleted on 2026-08-20, behind a green suite and a green linter for two weeks.
`scoring.py` opened by saying it scores a roster from `replan.md` directly, and there was no
`replan.md`. That is the next section.

---

## Citations in source

**Objective.** Make every documentation citation in a source file resolve to a document that
exists, and add the check that keeps it true.

**The count is larger than `D-152` found.** Written as a check, **153 citations do not resolve**,
because a bare `rules.md` is not a path either, and now that a spec has that name it is
ambiguous as well as unqualified. Nothing caught any of it: the linter's anchor check reads only
Markdown links inside the doc set. **This is a class of claim the repository makes constantly
and had no way to verify.**

A backticked `<name>.md` in a `.py` file under `roster_replan/`, `tests/`, `benchmarks/` or
`scripts/` now resolves as `<root>/<name>` first, then `<root>/docs/<name>`, which is the rule in
[`CLAUDE.md`](../../CLAUDE.md) and the check `check_source_citations` in
[`lint_docs.py`](../../scripts/lint_docs.py). It needs no rule about ambiguity, which was the
part expected to be awkward: an ambiguous bare name is not a path under either root, so it fails
on its own.

| Written | Count | Now |
| --- | --- | --- |
| `replan.md` | 41 | `internals/model.md`, or `specs/` where the claim is about scope |
| `rules.md` | 36 | `guide/rules.md` |
| `config.md` | 24 | `guide/configuring.md`, `specs/nl.md`, `studies/nl-parse.md` |
| `service.md` | 16 | `guide/api.md`, or `specs/service.md` for scope |
| `model.md` | 9 | `internals/model.md` |
| `PLAN.md` | 8 | the document that now carries the requirement |
| `validation.md` | 5 | `internals/testing.md`, or `specs/validation.md` |
| `configuring.md`, `quickstart.md`, `design.md`, `testing.md` | 8 | their door |
| four bare study names | 4 | `studies/<name>.md` |
| `capture.md` | 2 | `specs/README.md` |

**`PLAN.md` is the one that is not a rename.** Eight citations named a gitignored working
document, so a reader following one finds nothing and cannot even tell the absence is
deliberate. That is worse than an ordinary broken link.

### Four claims were stale in content, not only in citation

Each was found by having to decide what the citation should point at, which is the argument for
doing this by hand rather than by `sed`.

- **`tests/test_differential.py` said stage (b) needed a disruption metric that had not
  shipped.** D2 shipped on 2026-08-12 and stage (b) has run in `tests/test_replan.py` ever
  since, over all five metrics. The docstring described the layer before the metric existed.
- **`tests/test_properties.py` attributed a claim to `internals/testing.md` that the document
  does not make.** The unqualified "stays structure-consistent" belonged to the deleted spec;
  `testing.md` states the conditional version ([`D-061`](../decisions.md#d-061)). Repointing the
  citation would have turned a true statement about the wrong document into a false one about
  the right one.
- **`roster_replan/service/contracts.py` said the per-tenant model cache keys on `tenant`.** The
  cache was deleted ([`D-149`](../decisions.md#d-149)). The docstring justified a required field
  by a behaviour that no longer exists.
- **`tests/test_generation.py` cited "the spec" five times** and said the spec now says what the
  code does. That spec is gone, so the sentence was a promise about a document a reader cannot
  open.

### Gate

- [x] All 153 repointed; the check reports none. **`Doc lint: OK (55 files)`.** The check found
      two more on its first run, both in the linter's own new text quoting the form it bans.
- [x] `uv run pytest`. **937**, two more than before: the two new tests.
- [x] `uv run python -m tests.mutation -k specs` catches **3 of 3**, the new mutant by its named
      catcher. Verdict `unverifiable` rather than `clean`, because the tree was dirty: running
      mid-change is allowed and buys a weaker result ([`D-112`](../decisions.md#d-112)).

---

## Out of scope

Binding across all four.

- **Any change to `roster_replan/`, `benchmarks/` or `tests/`**, beyond the citation repointing
  and the four spec tests, and beyond the 162 `D-nnn` docstring citations, which were left
  because a documentation unit should not appear in the solver's diff.
- **Re-running a benchmark, a study or the mutation harness.** Every number is carried across
  untouched, and a document that wants a number cites the study that holds it.
- **Rewriting `guide/` or `internals/`.** They own the description of the system. Where a spec
  and a live document disagreed, the live document was right by construction, because it had
  been reconciled against the code and the spec was being written from it.
- **Editing a study or `benchmarks.md` to follow a change elsewhere.** Measurements are durable,
  and the tombstone design exists so that curation never needs to touch one.
- **Splitting `decisions.md` into one file per record, or renaming the IDs to subjects.**
  See decision 1.
- **Restoring the deleted walking skeleton, `PLAN.md` or `capture.md`.** Tier 0 stays Tier 0.
- **Phase IDs.** This project's unit is the component, not the delivery pass.

## Decisions

Each was posed with a proposal and resolved at review. The proposals are kept, so this is the
trail rather than a list of answers given somewhere else.

1. **The IDs stay numeric, against the shared contract**, which names records by subject and
   drops numbering so one can be merged without leaving a gap. *Proposed:* keep `D-nnn` and
   record it as an `## Overrides` entry naming the rule and the reason, which is measured: the
   links in the doc set, the backticked citations in code and tests, and an anchor scheme five
   checks are built on. The contract's own reason for dropping numbers is that a gap embarrasses
   a numbering, and the tombstone table answers that directly: a gap here is a row saying where
   the record went. **Resolved: as proposed** (2026-09-02). This is the project winning on a
   rule that was never general, not the rule being dropped.

2. **Does a spec own the predicates and the formulation, with the live documents becoming
   summaries?** *Proposed:* no. The spec cites; the canonical document owns. It is the only
   reading under which writing specs does not reverse [`D-151`](../decisions.md#d-151)
   wholesale: the failure that record names is real, and two documents owning one predicate is
   how it happens. **Resolved: cite, do not own** (2026-09-02), and the rule is now in
   [`CLAUDE.md`](../../CLAUDE.md) so it binds the next one too.

3. **May a reconstructed spec tick a gate box?** *Proposed:* yes, but only where the evidence
   exists now and is cited on the line. Everything else goes in **Measured results** as prose.
   Leaving every box `- [ ]` is blocked by the linter for any spec marked `Implemented`, and
   marking twelve finished components `Draft` to get around it would be a worse lie than the one
   it avoids. **Resolved: as proposed** (2026-09-02).

4. **Does a record about deleted code get retired?** *Proposed:* no.
   [`D-149`](../decisions.md#d-149) deleted the model cache; reversing it means building the
   cache again, which is the expensive-to-reverse test passing rather than failing. **Resolved:
   as proposed** (2026-09-02). `D-093`, which *shipped* the cache, is retired; `D-149`, which
   deleted it, is kept. The distinction is whether the decision still governs.

5. **May two study-backed records merge into one?** *Proposed:* no. A record that links a study
   is the decision that study fed, and merging two leaves one record answering to two
   measurements. **Resolved: as proposed** (2026-09-02), with one crossing: `D-107` carried
   [`time-budget.md`](../studies/time-budget.md) and `D-105` carried none, so the survivor
   inherits the link rather than holding two.

6. **Repo-root paths, or names relative to `docs/`?** *Proposed:* both, by precedence. Full
   repo-root paths would be unambiguous at the cost of four characters on every one of about
   200; names relative to `docs/` alone would strand `CLAUDE.md` and `README.md`. **Resolved: as
   proposed** (2026-09-02).

7. **Is the citation check a linter check or a test?** *Proposed:* the linter, beside the other
   citation checks and in CI already. **Resolved: both, and the split is the point**
   (2026-09-02). The linter owns the sweep over the tree; `citation_resolves` is a pure function
   so a test can assert it **rejects** something. A check asserted only against the tree as it
   happens to be would pass just as well if the rule accepted everything, which is precisely the
   state the dead citations were already in.

8. **Does a citation to a Tier 0 document stay?** *Proposed:* no. A citation a reader cannot
   follow is worse than none, because it reads as a reference rather than as an absence.
   **Resolved: as proposed** (2026-09-02). Seven of the eight `PLAN.md` citations now name a
   document; the eighth was a stale claim and was rewritten.

---

*The ledger: [`README.md`](README.md). The contract these four built:
[`CLAUDE.md`](../../CLAUDE.md). Every record: [`decisions.md`](../decisions.md).*
