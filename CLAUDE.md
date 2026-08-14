# Working in this repo

## Prose

This repo is mostly prose — specs, decision records, docstrings — and it is read by people who did
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
| unimplementable | cannot be implemented |
| unmatchable | impossible to match |
| widenable | cannot be widened |
| scoreable | scored |
| gameable | can be gamed |
| uncomparable | incomparable (the first is not a word) |

Coined `-able` and `-ability` words are the most common failure: if the adjective does not already
exist, write the verb phrase instead.

The table is a record, not a checklist. The rule is the test.

**Exempt: terms of art.** A word that names a code identifier, a spec symbol or a rule ID is used
verbatim, every time, and is never softened into a synonym. The glossary below is the sanctioned
list; anything outside it is fair game for simplification.

### Glossary — the terms of art, used verbatim

| Term | Means here |
| --- | --- |
| **incumbent** | The published roster a replan starts from — `x̄`, `instance.incumbent`. Not "current": current is ambiguous once a solve is running, and this one is specifically the roster being deviated *from* |
| **horizon** | The solve window, one week. Days are indexed from its start |
| **presolve** | Removing impossible `(employee, shift)` pairs before the solver sees them |
| **core** | The set of assumption literals CP-SAT returns to explain an infeasibility |
| **slack** | An explicit variable absorbing a shortfall so it can be priced instead of refused |
| **gate** | An assumption literal a hard constraint is conditioned on, so it can be reported or relaxed |
| **disruption** | The objective: deviation from the incumbent, as defined in `docs/specs/replan.md` |
| **provenance** | Where a rule's authority comes from — a statute, a CBA, or nothing (operational) |
| **derogation** | A lawful relaxation of a statutory parameter, requiring a recorded basis |

## Documentation

The rhythm is **spec → implement → reconcile**, and `PLAN.md` explains why the third beat is the one
that matters. Two things follow:

- **A component is not done until its spec matches its code.** When they diverge, decide which is
  wrong and fix that one — do not leave the spec describing intent.
- **Decisions go in `docs/decisions.md`**, not in specs. A spec is present tense and squeezes the
  rationale out. A later decision amends an earlier record in place with the supersession named; it
  never rewrites or deletes it.

Specs anchor decision IDs inline — `(`D-0NN`)` at the point the rationale applies — so a reader can
go either direction.

## Notation in specs

Predicate blocks are **plain fenced code blocks**, not ```` ```math ````. The identifiers in them are
payload field names and code identifiers (`max_hours_this_week`, `last_shift_end_before_horizon`),
and `grep`ping one across specs and code is how the shared-parameter review obligation in `D-039`
actually gets done. LaTeX escaping breaks that, and KaTeX renders multi-letter identifiers as
products of italic letters. Unicode operators (`Σ ∈ ⟹ ⊆ ∩ ≠ ≥`) carry the notation; monospace
preserves the alignment.

## Tests

**Break the code to prove a test layer works before calling it done.** A layer that has never been
shown to fail is not known to work.

The check is a script rather than a habit:

```bash
uv run python -m tests.mutation
```

Every mutant names the layer expected to object, and one caught only by some other layer is reported
as a miss. It is not part of the normal suite — it rewrites source files and takes minutes, so run it
when a test layer is added, or when one is about to be trusted. Adding a layer means adding a mutant
for it.

**Read the verdict from `tests/mutation-report.json`, not from the terminal.** A run takes tens of
minutes, and reading its result through a pipe has twice destroyed it: `tail` truncates the
per-mutant lines *and* reports its own exit status, so a run that leaked a mutated file into the
working tree read as a clean pass. `jq .verdict tests/mutation-report.json` is the first question,
and there are four answers: `clean`, `unverifiable`, `survivors`, `leaked`.

`leaked` means the run is void, not passing-with-a-caveat, because every mutant after the leak may
have been caught by the leftover defect. If it does leak, `git checkout --` the named paths —
format-on-save is the usual culprit and is worth turning off for the duration.

`unverifiable` means every mutant was caught and **the run could not vouch for the tree it ran in**
(`D-112`): a file it mutated was already modified, so the clean-tree check skipped it, or an editor
wrote the mutated text back after the restore verified. `unvouched_for` names the paths. Diff them by
hand, or commit and re-run, before believing the catches. Running on a dirty tree is allowed — it is
when a new layer is being proved — but it buys a weaker result, and now says so.

This has found four blind spots so far, each behind a fully green suite: `D-066`, `D-058`, a rest
threshold the differential harness could not see, and a validation rule with no test at all.
