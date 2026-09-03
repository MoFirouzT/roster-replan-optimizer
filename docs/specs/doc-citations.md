# Documentation citations in source, and the check that holds them

**Status:** Implemented 2026-09-02
**Depends on:** [`spec-reconstruction.md`](spec-reconstruction.md), which decided what
these citations should point at.

## Objective

Make every documentation citation in a source file resolve to a document that exists, and
add the linter check that keeps it true.

## Motivation

This codebase cites its own documentation heavily, and the citations are load-bearing: a
docstring saying a module is written from a named document is how the independence claim
is stated at the point where somebody might break it. `scoring.py` opens by saying it
scores a roster from `replan.md` directly, and there is no `replan.md`.

[`D-152`](../decisions.md#d-152) found 88 citations naming a file deleted on 2026-08-20.
Written as a check, the number is larger: **153 citations do not resolve**, because a bare
`rules.md` is not a path either, and now that [`rules.md`](rules.md) exists beside
[`guide/rules.md`](../guide/rules.md) it is ambiguous as well as unqualified.

Nothing caught any of it. The linter's anchor check reads only Markdown links inside the
doc set, and `check_canonical_sections` is inert here because `CANONICAL_DOC_GLOB` is
empty. **This is a class of claim the repository makes constantly and had no way to
verify.**

## Canonical reference

None. This unit changes citations, not claims.

## The resolution rule

A backticked `<name>.md` in a `.py` file under `roster_replan/`, `tests/`, `benchmarks/`
or `scripts/` resolves as **`<root>/<name>` first, then `<root>/docs/<name>`**.

That gives one rule with no special cases:

| Written | Resolves to |
| --- | --- |
| `CLAUDE.md`, `README.md` | the repository root |
| `decisions.md`, `benchmarks.md`, `STATE.md` | `docs/` |
| `guide/rules.md`, `internals/model.md`, `specs/model.md` | the door that owns it |
| `studies/encoding-levers.md` | the measurement |

A bare `rules.md` resolves nowhere and is therefore an error, which is what forces the
`guide/` or `specs/` prefix exactly where the ambiguity is. Nothing needs a rule about
ambiguity, because an ambiguous name is not a path and simply fails.

## Where each dead name goes

| Written | Count | Now | Why |
| --- | --- | --- | --- |
| `replan.md` | 41 | `internals/model.md`, or `specs/` where the claim is about scope | [`D-151`](../decisions.md#d-151) moved its content there |
| `rules.md` | 36 | `guide/rules.md` | Qualified, not moved |
| `config.md` | 24 | `guide/configuring.md`, `specs/nl.md`, `studies/nl-parse.md` | Its content split three ways |
| `service.md` | 16 | `guide/api.md`, or `specs/service.md` for scope | As above |
| `model.md` | 9 | `internals/model.md` | Qualified |
| `PLAN.md` | 8 | the document that now carries the requirement | Tier 0 and gitignored: **a reader cannot open it** |
| `validation.md` | 5 | `internals/testing.md`, or `specs/validation.md` | As above |
| `configuring.md`, `quickstart.md`, `design.md`, `testing.md` | 8 | their door | Qualified |
| four bare study names | 4 | `studies/<name>.md` | Qualified |
| `capture.md` | 2 | `specs/README.md` | Tier 0: the ledger row is what a reader can read |

**`PLAN.md` is the one that is not a rename.** Eight citations name a gitignored working
document, so a reader following one finds nothing and cannot even tell that the file is
deliberately absent. Each is rewritten to cite what now carries the requirement, or to
state the requirement directly.

## Build tasks

- [x] Repoint all 153 citations. The check now reports **none**.
- [x] Fix the claims the sweep found stale in content rather than in citation. **Four**,
      listed under *Measured results*.
- [x] Add `check_source_citations` and `citation_resolves` to
      [`scripts/lint_docs.py`](../../scripts/lint_docs.py), and two tests over the rule in
      `tests/test_specs.py`.
- [x] Add `citation-rule-accepts-anything`, which makes `citation_resolves` return
      `True` unconditionally.

## Test contract

The check itself is the test. It is a linter check rather than a pytest one because it
belongs beside the other citation checks, and because `scripts/lint_docs.py` already runs
in CI.

A mutant in the `specs` layer breaks one citation and requires the linter to object.

## Acceptance gate

*Blocks:* nothing.

- [x] `uv run python scripts/lint_docs.py` exits zero with the new check on. **`Doc
      lint: OK (55 files)`.** The check found two more on its first run, both in the
      linter's own new text quoting the form it bans, and both now carry `lint-ok`.
- [x] The check reports **153** against the tree as it was before this unit: 41
      `replan.md`, 36 `rules.md`, 24 `config.md`, 16 `service.md`, 9 `model.md`, 8
      `PLAN.md`, 5 `validation.md`, 8 across four other bare door names, 4 bare study
      names, 2 `capture.md`. <!-- lint-ok: the list quotes the names it repointed -->
- [x] `uv run pytest` passes. **937**, two more than before: the two new tests.
- [x] No claim, number or rule ID changes, other than the four stale ones below.
- [x] `uv run python -m tests.mutation -k specs` catches **3 of 3**, the new mutant by
      `test_a_citation_resolves_against_the_root_then_docs`, which is the catcher named
      for it. Verdict `unverifiable` rather than `clean`, because the tree was dirty:
      running mid-change is allowed and buys a weaker result
      ([`D-112`](../decisions.md#d-112)).

Record a box only against evidence. `- [x]` passed, `- [!]` ran and did not, with the
result on the line, `- [ ]` no record.

## Measured results

**Four claims were stale in content, not only in citation**, and each was found by having
to decide what the citation should point at. That is the argument for doing this by hand
rather than by `sed`.

- **`tests/test_differential.py` said stage (b) needed "a disruption metric `replan.md`
  has not shipped".** D2 shipped on 2026-08-12 and stage (b) has run in
  `tests/test_replan.py` ever since, over all five metrics. The docstring described the
  state of the layer before the metric existed. <!-- lint-ok: it quotes the citation it replaced -->
- **`tests/test_properties.py` attributed a claim to `internals/testing.md` that the
  document does not make.** The unqualified "stays structure-consistent" belonged to the
  deleted spec; `testing.md` states the conditional version
  ([`D-061`](../decisions.md#d-061)). Repointing the citation would have made a true
  statement about the wrong document into a false one about the right one.
- **`roster_replan/service/contracts.py` said the per-tenant model cache keys on
  `tenant`.** The cache was deleted ([`D-149`](../decisions.md#d-149)) and there is no
  cache in `roster_replan/`. The docstring justified a required field by a behaviour that
  no longer exists.
- **`tests/test_generation.py` cited "the spec" five times and said "the spec now says
  what the code does".** That spec is gone, so the sentence was a promise about a document
  a reader cannot open.

**Eight citations named a gitignored file.** `PLAN.md` is Tier 0, so a reader following one
finds nothing and cannot tell that the absence is deliberate. That is worse than an
ordinary broken link, and it is the reason decision 2 went the way it did.

## Out of scope

- **Markdown-to-Markdown links.** The linter already checks those.
- **Citations in non-Python files.** There are none outside the doc set.
- **Making `docs/README.md` reachable by a bare name.** Nothing cites it, and root wins by
  the rule above.
- **Restoring `PLAN.md` or `capture.md` to the repository.** Tier 0 stays Tier 0; only the
  citations to it change.

## Decisions

Each was posed with a proposal and resolved in the course of the work on 2026-09-02.
The proposals are kept.

1. **Repo-root paths, or names relative to `docs/`?** *Proposed:* both, by precedence:
   root first, then `docs/`. Full repo-root paths (`docs/guide/rules.md`) would be
   unambiguous and are what a few citations already use, at the cost of four extra
   characters on every one of about 200. Names relative to `docs/` alone would strand
   `CLAUDE.md` and `README.md`. The precedence rule takes the short form of each.
   **Resolved as proposed.** It also turned out to need no rule about ambiguity, which
   was the part I expected to be awkward: an ambiguous bare name is not a path under
   either root, so it fails on its own.

2. **Does a citation to a Tier 0 document stay?** *Proposed:* No. A citation a reader
   cannot follow is worse than no citation, because it reads as a reference rather than
   as an absence. `PLAN.md` and `capture.md` citations are rewritten to name a document
   in the repository, or to state the thing directly. **Resolved as proposed.** Seven
   of the eight now name a document; the eighth was a stale claim and is rewritten.

3. **Is the check a linter check or a test?** *Proposed:* the linter, beside the other
   citation checks, and in CI already. **Resolved: both, and the split is the point.**
   The linter owns the sweep over the tree; `citation_resolves` is a pure function so a
   test can assert it **rejects** something. A check asserted only against the tree as it
   happens to be would pass just as well if the rule accepted everything, which is
   precisely the state the 88 dead citations were already in.
