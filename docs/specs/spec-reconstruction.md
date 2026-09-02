# Specs for the built components

**Status:** Implemented 2026-09-02
**Depends on:** [`documentation-restructure.md`](documentation-restructure.md), which
built the ledger this adds documents to.

## Objective

Give every built component a spec file in this directory, holding what a live document
does not hold: the scope it was built to, its interfaces, the test contract, the
acceptance gate it passed, what it ruled out, and the decision trail behind it.

## Motivation

### This project never had a build record, and the deleted files are not one

The obvious reading is that [`D-151`](../decisions.md#d-151) threw away seven work
orders and this unit restores them. That reading is wrong, and it was checked rather
than assumed. The seven files are in git, added whole on 2026-08-11 in `6d8646f` and
deleted on 2026-08-20 in `48e86d3`, and none of them is a work order:

| | `rules` | `model` | `replan` | `validation` | `service` | `config` | `capture` |
| --- | --- | --- | --- | --- | --- | --- | --- |
| Status line | no | no | no | no | no | no | no |
| Build tasks | no | no | no | no | no | no | no |
| Acceptance gate | no | no | no | no | no | no | no |
| Out of scope | no | no | no | no | no | no | no |
| Decisions | no | no | no | no | no | no | no |

What they carried instead was inline `[built]`, `[shipped]` and `[not implemented]`
markers, kept up to date across 7 to 16 commits each. They were **design statements
maintained alongside the code**, which is exactly what [`D-151`](../decisions.md#d-151)
called them, and moving them into the two doors was right. Restoring them would put a
second owner on every predicate they hold, which is the failure that record names.

So this unit does not restore a tier. **It creates one this project has never had.**
The build record was never in `docs/specs/`: it was in the gitignored `planning/`, in
`decisions.md`, and in the commits. That is a defensible place for it while a project is
being built and a bad one for a project that is closed, because two of those three are
not readable by anyone who was not here.

### The code still cites documents that no longer exist

Eighty-eight citations in `roster_replan/`, `tests/` and `benchmarks/` name a spec file
that was deleted on 2026-08-20: `replan.md` 41 times, `config.md` 24, `service.md` 16,
`validation.md` 5, `capture.md` 2. `scoring.py` opens by saying it scores a roster from
`replan.md` directly, and there is no `replan.md`.

Nothing catches this. The linter's anchor check only reads Markdown links inside the doc
set, and `check_canonical_sections` is inert here because `CANONICAL_DOC_GLOB` is empty.
Eighty-eight dead references sat behind a green suite and a green linter for two weeks,
which is the fifth time in this repository that a documentation claim survived only
because nothing looked at it.

They are evidence for this unit rather than a task in it: the code was written against
work orders that it still expects to be able to name.

### What a spec holds that a live document does not

The predicates stay in [`guide/rules.md`](../guide/rules.md) and its companions, the
formulation in [`internals/model.md`](../internals/model.md), the contract in
[`guide/api.md`](../guide/api.md). None of that moves. What a live document does not
carry, and should not, is what a component was scoped to, what it was allowed not to do,
which gate it had to pass and with what number, and which questions were open and how
they resolved. A live document says what is so now, for a reader who was not there.

Two documents here already work this way and are the model:
[`documentation-restructure.md`](documentation-restructure.md) and
[`decision-curation.md`](decision-curation.md).

## Canonical reference

None. This unit adds no predicate and no formulation, and every spec it writes cites the
canonical documents rather than restating them.

## The honesty problem, and how these documents answer it

A spec written after the code is a reconstruction. It was not reviewed before
implementation, its build tasks were not a plan, and its gate boxes are being ticked
from evidence found afterwards rather than recorded at the time. A document that looks
like a frozen work order and is not one is worse than no document, and the section above
is why that risk is real here: there is no earlier version of these documents to fall
back on, so nothing but the rules below stops a reconstruction from reading as a plan.

Three rules follow, and they are what makes these specs worth keeping:

- **Every reconstructed spec says so on its Status line**, and names what it was built
  from: the code, the live documents, the records, the studies, and the commits.
- **A gate box is ticked only against evidence that exists now.** A condition the
  component clearly met but for which no record survives is written as prose in
  **Measured results**, not as a `- [x]`. The tick means a check was run and its result
  is on the line, and a reconstruction may not manufacture one.
- **The Decisions section cites records rather than inventing a trail.** Where a
  question was genuinely open at review, `decisions.md` says so and the record is the
  citation. Where no record exists, the section says the reasoning was not written down,
  which is a true statement about this project and a useful one.

## Scope: which components get a spec

Fourteen ledger rows have no spec. Twelve get one.

Three take a name that differs from the obvious one, because `docs/benchmarks.md`,
`studies/mutation-harness.md` and `studies/foreign-incumbent.md` already exist and a
citation naming one of those would be ambiguous.

| Component | Spec file | Notes |
| --- | --- | --- |
| Rule registry | [`rules.md`](rules.md) | 26 rules, provenance, the two searches that found nothing |
| The model | [`model.md`](model.md) | The formulation stays in `internals/model.md` and is cited |
| Checker, validation, harnesses | [`validation.md`](validation.md) | Two readings, the import contracts, the differential harness limit |
| Disruption metric | [`disruption.md`](disruption.md) | The exemplar, written first: D0 to D4 defined, D2 shipped |
| Mutation harness | [`mutation.md`](mutation.md) | Four blind spots, five hardenings |
| Benchmark set and four methods | [`benchmark-set.md`](benchmark-set.md) | Seeds and fingerprints, never payloads |
| Job service | [`service.md`](service.md) | Queue, fairness, fallback ladder, the deleted cache |
| Explanation and minimal cores | [`explanation.md`](explanation.md) | The explainer answers from the checker |
| Tool surface and profile review | [`tools.md`](tools.md) | `what_if`, profile review, the two overrides |
| NL to profile | [`nl.md`](nl.md) | The schema is the confinement |
| T5: fairness and generation | [`fairness-generation.md`](fairness-generation.md) | Two built, two retired on measurement |
| Foreign incumbents, cross-week rules | [`cross-week-rules.md`](cross-week-rules.md) | Seven rules of this product |

Two rows get none:

- **Walking skeleton.** The code was deleted ([`D-146`](../decisions.md#d-146)). A spec
  for deleted code describes nothing, and the ledger row already says what it found and
  why it went.
- **Capture and replay.** Specified and never built, so its work order is the one
  document here that was never a reconstruction. It is in Tier 0. See decision 3 below.

## Build tasks

- [x] Write `_TEMPLATE.md` for this project, cutting the phase IDs and the golden-oracle
      table and adding the test contract this project uses.
- [x] Write one exemplar first, so the shape is reviewed before eleven more are written
      to it. [`disruption.md`](disruption.md), 231 lines.
- [x] Write the remaining eleven, each from the code, the live documents, the records,
      the studies and the implementing commits.
- [x] Record the reversal as [`D-152`](../decisions.md#d-152), with a pointer on
      [`D-151`](../decisions.md#d-151) naming it. The ID could not be written here until
      the record existed: `test_every_referenced_decision_exists` rejects a forward
      reference, and it rejected the first draft of this line.
- [x] Rewrite this directory's [`README.md`](README.md), replacing "The ledger is
      reconstructed, and the specs are still here" with a section on what each of the two
      documents owns, and adding **Adding a component**.
- [x] Add the spec column to the ledger table. 16 of 16 rows name a spec or say why not.
- [x] Update [`CLAUDE.md`](../../CLAUDE.md): work orders are a fifth kind of document,
      and a spec cites the canonical documents rather than restating them.
- [x] Update [`STATE.md`](../STATE.md), including the open citation gap this found.
- [!] **The linter checks stay inert, deliberately.** `check_spec_status` and the module
      reference check now bind fourteen files rather than two and caught nothing new. The
      `Depends on:` graph check stays dead, because this project's unit is the component
      and not the delivery pass, so no spec owns a phase ID. `CANONICAL_DOC_GLOB` stays
      empty: turning it on is the follow-on unit's job, not this one's.

## Test contract

This unit writes no code, so the layers that apply are the documentation ones:

- `scripts/lint_docs.py`: the `Implemented` box rule and the `## Decisions` requirement
  now bind twelve new files, as does every per-line check.
- `tests/test_specs.py`: link and anchor resolution across the new files.

## Acceptance gate

*Blocks:* nothing. The project is closed and this is a documentation unit.

- [x] `uv run python scripts/lint_docs.py` exits zero. **`Doc lint: OK (54 files)`.**
- [x] `uv run pytest` passes. **935 passed**, the same count as before this unit: nothing here adds or removes a test. The suite caught two things on the way, both in this unit's own writing: a `D-152` forward reference made before the record existed, and `D-151` going over the 340-word cap once its superseded pointer was added.
- [x] Every one of the twelve says it is a reconstruction and names its sources. The two written before 2026-09-02 correctly carry no such line.
- [x] No spec restates a predicate, a formulation section or a rule parameter. Every one
      carries a **Canonical reference** section naming what it cites instead, and no
      fenced predicate block was copied into this directory.
- [x] No claim, number or rule ID in `guide/`, `internals/` or `studies/` changed. The
      only edits outside this directory are the new record, its two index rows, a
      superseded pointer and a 14-word trim on [`D-151`](../decisions.md#d-151), and two
      additions to [`STATE.md`](../STATE.md) and [`CLAUDE.md`](../../CLAUDE.md).
- [x] Every ledger row names its spec, or says why it has none. **16 of 16**: twelve new, two already written, and two that get none (the walking skeleton was deleted; capture and replay is in Tier 0).

Record a box only against evidence. `- [x]` passed, `- [!]` ran and did not, with the
result on the line, `- [ ]` no record.

## Out of scope

- **Any change to `roster_replan/` or `tests/`.**
- **Re-running a benchmark, a study or the mutation harness.** Every number is carried
  across untouched, and a spec that wants a number cites the study that holds it.
- **Rewriting `guide/` or `internals/`.** They own the description of the system and
  keep owning it. If a spec and a live document disagree, the live document is right by
  construction here, because it was reconciled against the code and the spec is being
  written from it.
- **Restoring the deleted walking skeleton, or building capture and replay.**
- **Repointing the eighty-eight dead citations**, and adding the linter check that would
  have caught them. Both are edits to `roster_replan/` and `tests/`, and the check needs
  a decision about whether a backticked `<name>.md` in a docstring must resolve to a file.
  A separate unit, and it should not start until the specs exist, because what those
  citations should point *at* is what this unit decides.
- **Phase IDs.** This project's unit is the component, not the delivery pass, so specs
  stay named by subject and the linter's `Depends on:` graph check stays inert.

## Decisions

Each was posed with a proposal and resolved on 2026-09-02, in the order the work reached
it. The proposals are kept, so this is the trail rather than a list of answers given
somewhere else.

1. **Does a spec own the predicates and the formulation, with the live documents
   becoming summaries?** *Proposed:* No. The spec cites; the canonical document owns.
   This is what the bess project does, where the math lives in `formulation.md` at Tier 2
   and each work order names the sections it implements. It is also the only reading
   under which this unit does not reverse [`D-151`](../decisions.md#d-151) wholesale: the
   failure D-151 named is real, and two documents owning one predicate is how it happens.
   **Resolved: cite, do not own.** Every spec carries a **Canonical reference** section
   naming what it defers to, no fenced predicate block was copied here, and the rule is
   now in [`CLAUDE.md`](../../CLAUDE.md) so it binds the next one too.

2. **May a reconstructed spec tick a gate box?** *Proposed:* Yes, but only where the
   evidence exists now and is cited on the line, which in practice means a study, a
   named test, a committed benchmark result or a record. Everything else goes in
   **Measured results** as prose. The alternative, leaving every box `- [ ]`, is blocked
   by the linter for any spec marked `Implemented`, and marking twelve finished
   components `Draft` to get around it would be a worse lie than the one it avoids.
   **Resolved as proposed.** The twelve carry **106 ticked boxes and 30 `- [!]` ones**,
   and every `- [!]` says what happened on the line. That ratio is worth reading on its
   own: close to one condition in five came back qualified rather than passed.

3. **Does capture and replay come back from Tier 0?** *Proposed:* Yes, into **In
   flight**. It is the one work order here that was written before the code and never
   reconciled, which makes it the only genuine artifact of the original arrangement, and
   [`D-151`](../decisions.md#d-151) sent it to Tier 0 on the reasoning that Tier 0 is for
   plans for unbuilt work. That reasoning held when this directory had no place for an
   unbuilt component. It now has one, and the In flight table currently says *(none)*
   while the ledger says the component is the largest gap in the evidence.
   **Left open, deliberately.** This unit's scope was the built components, and whether a
   plan that is *blocked* rather than merely unstarted belongs in Tier 0 or in **In
   flight** is a separate judgement. The file is at
   `git show 48e86d3^:docs/specs/capture.md` if the answer turns out to be yes.

4. **Do the specs take the deleted files' names?** *Proposed:* Where a component maps
   to one, yes: `rules.md`, `model.md`, `validation.md`, `service.md`, `config.md`. The
   eighty-eight citations then name a document that exists again, and the follow-on unit
   becomes a path-qualification pass rather than a rewrite. The cost is that `rules.md`
   is ambiguous between this directory and `guide/`, and `model.md` between this
   directory and `internals/`, which is an argument for qualifying every citation with
   its directory and is the follow-on unit's job either way. `replan.md` is the awkward
   one: its content split across the model and the disruption metric, which are two
   ledger rows, so one of them takes the name and the other does not.
   **Resolved as proposed, with three exceptions and one gap.** `mutation.md`,
   `benchmark-set.md` and `cross-week-rules.md` avoid collisions with
   `studies/mutation-harness.md`, `benchmarks.md` and `studies/foreign-incumbent.md`.
   The gap is `config.md`: its content split across `tools.md` and `nl.md`, so its 24
   citations still name nothing and the follow-on unit has to route them by file.

5. **What happens to the ledger's finding column?** *Proposed:* Nothing. It stays one
   line per component and stays the index. The spec is where the detail goes, which is
   what "Where the detail lives" already promises and could not deliver.
   **Resolved as proposed**, with a **Spec** column added so each row names its own.

---

*The ledger: [`README.md`](README.md). Every record: [`decisions.md`](../decisions.md).*
