# Working in this repo

## Prose

This repo is mostly prose (specs, decision records, docstrings) and it is read by people who did
not write it, including non-native English readers. Write it accordingly.

**Use the most common word that is exactly as precise.** A less common word must earn its place by
carrying meaning the common one lacks. If it only sounds more considered, it is costing the reader
and buying nothing.

These are the substitutions already made across this repo, kept as a worked example of the rule:

| Instead of | Write |
| --- | --- |
| residue, remainder | what is left |
| erode | weaken, decay |
| vindication | confirmation |
| artefact (of a process) | side effect |
| discharge (an obligation) | meet, satisfy |
| commensuration | weighted sum, trade-off, one scale |
| smeared into | hidden inside |
| licence to | permission to |
| nicety | nice-to-have |
| seductive | tempting |
| churned | reshuffled |
| explicable | easy to explain |
| conceals | hides |
| retrievability | being able to find one again |
| incurring | taking on |
| seam (metaphorical) | boundary, interface |
| fortnight | two weeks |
| unimplementable | cannot be implemented | <!-- lint-ok: the table quotes the words it bans -->
| unmatchable | impossible to match |
| widenable | cannot be widened | <!-- lint-ok: the table quotes the words it bans -->
| scoreable | scored | <!-- lint-ok: the table quotes the words it bans -->
| gameable | can be gamed | <!-- lint-ok: the table quotes the words it bans -->
| uncomparable | incomparable (the first is not a word) |

Coined `-able` and `-ability` words are the most common failure: if the adjective does not already
exist, write the verb phrase instead.

The table is a record, not a checklist. The rule is the test.

**Exempt: terms of art.** A word that names a code identifier, a spec symbol or a rule ID is used
verbatim, every time, and is never softened into a synonym. The glossary below is the sanctioned
list; anything outside it is fair game for simplification.

### Glossary: the terms of art, used verbatim

| Term | Means here |
| --- | --- |
| **incumbent** | The published roster a replan starts from: `x̄`, `instance.incumbent`. Not "current": current is ambiguous once a solve is running, and this one is specifically the roster being deviated *from* |
| **horizon** | The solve window, one week. Days are indexed from its start |
| **presolve** | Removing impossible `(employee, shift)` pairs before the solver sees them |
| **core** | The set of assumption literals CP-SAT returns to explain an infeasibility |
| **slack** | An explicit variable absorbing a shortfall so it can be priced instead of refused |
| **gate** | The boolean a hard constraint is conditioned on, so it can be reported or relaxed. CP-SAT's own name for it is an *assumption literal* |
| **disruption** | The objective: deviation from the incumbent, as defined in `docs/internals/model.md` |
| **predicate** | The exact conditions a rule imposes: the fenced block in the rule's own file, which [`rules.md`](docs/guide/rules.md) names in its registry. Not the rule, which also has an ID, a provenance and parameters, and not its encoding in the model or the checker. The model/checker independence claim is stated in this word, so it is grep-able on purpose |
| **provenance** | Where a rule's authority comes from: a statute, a CBA, or nothing (operational) |
| **derogation** | A lawful relaxation of a statutory parameter, requiring a recorded basis |

## Documentation

**The unit of work is the component**: one capability, specified before it is built and reconciled
against its code afterwards. It carries two documents. [`docs/specs/`](docs/specs) holds its **work
order**, from [`_TEMPLATE.md`](docs/specs/_TEMPLATE.md): the scope, the interfaces, the test
contract, the acceptance gate and the decision trail. A live document in `guide/` or `internals/`
says what the thing does now. [`docs/specs/README.md`](docs/specs/README.md) is the ledger, one row
per component, and a component is not finished until it has a row saying what it found, including
where the answer was no.

**A spec cites the canonical documents and never restates them.** A predicate, a formulation section
or a rule parameter has one owner, and two documents owning one claim is how the unread one goes
stale ([`D-151`](docs/decisions.md#d-151), [`D-152`](docs/decisions.md#d-152)). The twelve specs for
components built before 2026-09-02 are reconstructions and say so on their Status line. A spec
holds one component, and where several ran as one piece of work they may share a file, one
section each, with a ledger row apiece ([`D-157`](docs/decisions.md#d-157)).

Documents come in five kinds and they do not mix.

**Work orders**: [`docs/specs/`](docs/specs), one per component.
Scope, interfaces, the test contract, the gate and the decision trail.
Frozen at approval and then reconciled: a spec marked `Implemented` may carry no unrecorded box, and
the linter enforces that, because *we meant to tick it* and *it passed* are indistinguishable six
weeks later.

**Live documents**: [`docs/guide/`](docs/guide) for people using the service, [`docs/internals/`](docs/internals) for people changing it, and [`docs/STATE.md`](docs/STATE.md) for where the project stands.
Present tense, short, and reconciled against the code.
They say what is so now, and carry only as much reasoning as a reader needs to not think a choice was arbitrary.

**Decision records**: [`docs/decisions.md`](docs/decisions.md).
What was chosen, what was rejected, and why.
**They are curated rather than append-only.** A record whose wording has gone stale is corrected in
place, and a record that no longer earns a reader's attention is retired. What a record may not do is
quietly change what it decided: reversing a decision takes a new record, and the old one says which
record superseded it.

**Measurements**: [`docs/studies/`](docs/studies), including the nulls and the rejected alternatives, and [`docs/benchmarks.md`](docs/benchmarks.md).
**A measurement is durable.** It states the conditions it was taken under, and it is kept even when
the thing it measured has been deleted, because the number is still evidence about how this project
behaves. A measured null is a stronger signal than an unmeasured win.

**Tier 0**: `planning/`, gitignored. Working notes, spent plans, and specifications for work nobody
built. Nothing in the repository links to it.

Three rules follow:

- **A component is not done until its documentation matches its code.** When they diverge, decide which is wrong and fix that one: do not leave a live document describing intent.
- **Reasoning goes in a record, not in a live document.** The exception is [`docs/internals/design.md`](docs/internals/design.md), which exists to be the bridge: it states the current design as one argument and links the record behind each claim. It is the only live document that cites records heavily.
- **A canonical document says what it assumes.** It carries an `*Assumes:*` line naming what a reader needs first, with links. `CANONICAL` in the linter is the list, and the linter fails without the line.

Every live document also ends with a footer naming where its reasoning lives. The two answer
different questions, where to start and where to go next, and a document may carry both.

The enforceable half of the charter above is a script rather than a habit:

```bash
uv run python scripts/lint_docs.py
```

It gates em dashes, coined `-able` words, the 600-line cap, the `*Assumes:*` lines, every
cross-document anchor, and **every documentation citation in a source file**: a backticked
`<name>.md` in `roster_replan/`, `tests/`, `benchmarks/` or `scripts/` resolves against the
repository root first and then `docs/`, so write `guide/rules.md` or `specs/rules.md` and never the
bare name ([`D-152`](docs/decisions.md#d-152)). Everything else in this file is review judgment. A line may opt out of the
per-line checks with a trailing `<!-- lint-ok -->`, which is for quoting a banned word, not for
keeping one.

## Overrides

Where this project departs from the shared discipline contract, with the reason. Nothing else in
that contract is turned off.

**Decision records keep numeric IDs.** The contract names records by subject and drops numbering, so
that one can be merged or retired without leaving a gap. Here they are `D-nnn` with an explicit
`<a id="d-nnn">` anchor each, because the numbering is load-bearing: **547 links from the
documentation into the records, 518 more inside `decisions.md` itself, 340 backticked citations in
code and tests**, and five checks built on the anchors. Those are counts of Markdown links to a
`#d-nnn` anchor, from outside `decisions.md` and from inside it, and of `` `D-nnn` `` under
`roster_replan/`, `tests/`, `benchmarks/` and `scripts/`, so they are re-measurable rather than
folklore. They were 324 and 328 on 2026-09-02
before the specs were written; the specs cite records heavily, which is most of the difference.
The gap the contract worries about is answered directly instead: a merged or retired ID keeps its
anchor in [Merged and retired](docs/decisions.md#merged-and-retired), on a row saying where its
reasoning went, so a reference to it lands somewhere that answers the reader.

## Notation

Predicate blocks are **plain fenced code blocks**, not ```` ```math ````. The identifiers in them are
payload field names and code identifiers (`max_hours_this_week`, `last_shift_end_before_horizon`),
and `grep`ping one across the documentation and the code is how the shared-parameter review obligation
in [`D-039`](docs/decisions.md#d-039) actually gets done. LaTeX escaping breaks that, and KaTeX renders multi-letter
identifiers as products of italic letters. Unicode operators (`Σ ∈ ⟹ ⊆ ∩ ≠ ≥`) carry the notation;
monospace preserves the alignment.

## Tests

**Break the code to prove a test layer works before calling it done.** A layer that has never been
shown to fail is not known to work.

The check is a script rather than a habit:

```bash
uv run python -m tests.mutation
```

Every mutant names the layer expected to object, and one caught only by some other layer is reported
as a miss. It is not part of the normal suite (it rewrites source files) so run it when a test
layer is added, or when one is about to be trusted. Adding a layer means adding a mutant for it.

**A full run is about 14 minutes**: 14m12s for all 136 mutants on 2026-08-21, up from 9m27s for 103
before [`D-141`](docs/decisions.md#d-141) made the harness delete cached bytecode after every write. Recompiling is most of the
difference, and it is what a size-neutral mutant costs to test at all. Every run records `started_at` and `duration_seconds` in its report ([`D-130`](docs/decisions.md#d-130)),
so the figure is checkable rather than folklore: quote the report, not this sentence, once they
differ. What the last run actually returned is in [`STATE.md`](docs/STATE.md). A single layer (`-k service`) is seconds, and is the cheap way to settle one doubtful result.

**Read the verdict from `tests/mutation-report.json`, not from the terminal.** Reading a run's result
through a pipe has twice destroyed it: `tail` truncates the per-mutant lines *and* reports its own
exit status, so a run that leaked a mutated file into the working tree read as a clean pass.
`jq .verdict tests/mutation-report.json` is the first question, and there are four answers: `clean`,
`unverifiable`, `survivors`, `leaked`.

**A `survivors` verdict is now worth one check before believing it** ([`D-139`](docs/decisions.md#d-139)). A mutant whose defect
an editor wrote away inside the test window used to score as a survivor (pytest found nothing wrong
because nothing was wrong) which reads as a hole in a test layer and is a hole in the harness. The
run now voids such a mutant instead. If a survivor still appears, apply it by hand and confirm it
fails before writing a test for ground that may already be covered.

`leaked` means the run is void, not passing-with-a-caveat, because every mutant after the leak may
have been caught by the leftover defect. If it does leak, `git checkout --` the named paths:
format-on-save is the usual culprit and is worth turning off for the duration.

`unverifiable` means every mutant was caught and **the run could not vouch for the tree it ran in**
([`D-112`](docs/decisions.md#d-112)): a file it mutated was already modified, so the clean-tree check skipped it, or an editor
wrote the mutated text back after the restore verified. `unvouched_for` names the paths. Diff them by
hand, or re-run, before believing the catches. Running on a dirty tree is allowed (it is when a new
layer is being proved) but it buys a weaker result, and now says so.

A late write does not cost a whole re-run ([`D-130`](docs/decisions.md#d-130)). Only the mutants touching the named paths are in
doubt, so re-run that layer alone: **and send it somewhere else with `--report`**, or a 5-mutant
report replaces the full one it was meant to repair:

```bash
uv run python -m tests.mutation -k service --report /tmp/service-rerun.json
```

That is how the run of 2026-08-17 was settled: 103/103 caught but `unverifiable` for a late write to
`roster_replan/service/jobs.py`, closed by re-running `service` alone for a `clean` five.

This has found four blind spots so far, each behind a fully green suite: [`D-066`](docs/decisions.md#d-066), [`D-058`](docs/decisions.md#d-058), a rest
threshold the differential harness could not see, and a validation rule with no test at all.
