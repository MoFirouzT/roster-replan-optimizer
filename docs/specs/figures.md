# Stale duplicated figures

**Status:** Implemented 2026-09-03
**Depends on:** [`documentation.md`](documentation.md) (the linter this extends)

## Objective

A number copied out of the document that owns it, and left behind when that document is
corrected, fails `scripts/lint_docs.py` instead of surviving until somebody reads both
places.

## Motivation

The linter gates paths, anchors, banned words, line caps and source citations. It checks
nothing about the numbers, and the numbers are what this repository is mostly made of.
Three separate incidents are on record, each found by hand:

1. The scale table in [`foreign-incumbent.md`](../studies/foreign-incumbent.md) recorded
   instances 8, 10 and 23 as `OPTIMAL`/`OPTIMAL`/`UNKNOWN`. All three return `INFEASIBLE`
   today, and four claims elsewhere rested on those rows ([`D-155`](../decisions.md#d-155)).
2. That study's illegal-past figure was corrected from *10 of 13* to **8 of 13**. Four <!-- lint-ok: the motivation quotes the figure it was written about -->
   copies elsewhere kept the old number through the commit that made the correction, and
   were fixed a session later ([`D-157`](../decisions.md#d-157)).
3. The same read found three more: [`D-083`](../decisions.md#d-083)'s *64 of 72* standing
   against [`D-105`](../decisions.md#d-105)'s *71 of 84*, a *146 of 150* index count, and a
   ledger row claiming *14 of 14* when it was 16.

Every one of them is the same shape: one document owns a measurement, another states it,
and only the owner gets corrected.

## Canonical reference

None. No new predicate and no new formulation. The rule this mechanises is `CLAUDE.md`'s,
under *Documentation*: a measurement is durable, and a claim has one owner.

## Parameters and configuration

`scripts/figures.toml`, read by the linter with `tomllib`. One `[[figure]]` table per
registered figure:

| Field | Means |
| --- | --- |
| `id` | The figure's name, used in the owner's marker and in error messages |
| `owner` | Path, relative to the repository root, of the document that owns the figure |
| `kind` | `derived` or `pinned`, below |
| `pattern` | A regex with one capture group: the figure's value, wherever it is stated |
| `compute` | `derived` only: the key in `lint_docs.COMPUTED` that recounts it |
| `tolerance` | `derived` only: the fraction a stated value may differ by. Default `0` |
| `reproducible` | `computed`, `command` or `no`, below. Documentation, not behaviour |
| `command` | `reproducible = "command"` only: what re-measures it |
| `note` | Why the figure is registered |

**`kind` is where the value comes from, and it is the distinction this check is built on.**

- **`derived`** figures the repository can recount from itself: how many decision records
  there are, how many links point into them. `compute` names the function, and every
  stated value must match what it returns, within `tolerance`.
- **`pinned`** figures nothing here can recount: a solver status on data that is fetched
  rather than committed, a wall-clock second. The value is whatever the **owner's marked
  line** says, and the check is that every other statement of it agrees. Nothing is
  re-measured, ever.

`reproducible` records the second half of that distinction without acting on it. A solver
status is deterministic and a command would settle it (`command`); a wall-clock figure is
not and no command would (`no`). The linter runs neither: see the decisions below.

## Interfaces

```python
COMPUTED: dict[str, Callable[[], int]]   # a derived figure's recount, keyed by `compute`
def figure_value(text: str, pattern: re.Pattern, marker: str) -> str | None
def normalise_figure(value: str) -> str  # "**Ten**" and "10" are one value
def check_figures(errors: list[str]) -> None
```

The owner marks the line holding the live value with an HTML comment, invisible when
rendered:

```markdown
**Eight of thirteen published rosters have a past this model calls illegal.** <!-- fig:foreign-illegal-past -->
```

A line already carrying `<!-- lint-ok -->` is skipped, which is how a document states a
superseded figure on purpose.

## Build tasks

- [x] `scripts/figures.toml`, with the registry and a header stating the rule. Seven
      figures: five `derived` and two `pinned`.
- [x] `check_figures` in `scripts/lint_docs.py`, plus `COMPUTED` and `figure_hits`.
- [x] Owner markers in the documents that own the registered figures. Two, both on
      `studies/foreign-incumbent.md`, one of them a heading that was itself the stale copy.
- [x] Correct whatever the check finds stale on the current tree. Three, below.
- [x] `tests/test_specs.py`: nine tests, six of them rejections.
- [x] Two mutants in `tests/mutation.py`, layer `specs`, one per branch.
- [x] The history gate below, as `scripts/figures_history.py`.

## Test contract

- **Unit**, `tests/test_specs.py`: `normalise_figure` and `figure_value` directly, then
  `check_figures` against a constructed tree holding a disagreeing copy. A rule that has
  never rejected anything is not known to reject anything, which is the defect
  [`D-152`](../decisions.md#d-152) records in another form.
- **Registry self-check**, same file: every entry's owner carries a marker, that marked
  line matches the entry's pattern, and every `compute` key exists. A registry that
  silently matches nothing is exactly the failure this component exists to prevent, and it
  would read as coverage.
- **Mutant**, layer `specs`: `check_figures` accepting any value, the state the whole
  documentation set was already in. `tests/test_specs.py` is named to catch it.
- **History**, `scripts/figures_history.py`: the check run against the commits that
  carried each incident. This is the acceptance gate.

## Acceptance gate

*Blocks:* nothing.

- [x] Incident 2 fires at `e6a18da`: three sites disagree with the owner about
      `foreign-illegal-past`. **It names the corrected sites as the wrong ones**, because the
      marker sits on the study's heading and that heading was one of the copies still saying
      *Ten*. The split is reported and located; which side is right is the reader's call.
- [x] Incident 3 fires. `ledger-rows` at `8de74e6`: *16 of 16* and *14 of 14* against a
      ledger of 18. `theme-index-coverage` at `5f511f4`: *146 of 150* against 137.
- [!] Incident 1 is **not** caught at `195e507`, and cannot be. Every document agreed with
      the scale table and the table disagreed with reality. What the check does report at
      that commit is four other figures that had already drifted, which is the finding
      underneath: drift was continuous and nothing was watching.
- [x] At most a handful of candidates, all real. **Three on the tree this shipped against**,
      two of which are lines quoting a superseded figure on purpose and are annotated once.
      Six annotated lines in all across seven figures. Steady state is zero.
- [x] `uv run python scripts/lint_docs.py` green, 53 files.
- [x] `uv run pytest -q` green, **957 passing** against 948 before.
- [x] `uv run lint-imports` green, 11 contracts.
- [!] `uv run python -m tests.mutation -k specs --report /tmp/figures-rerun.json` caught
      **5 of 5**, verdict `unverifiable`: `scripts/lint_docs.py` was already modified, so
      the clean-tree check skipped it ([`D-112`](../decisions.md#d-112)). That is the
      expected verdict for a layer proved before its own commit. Both figure mutants
      report `caught`, the file is byte-identical to the working copy afterwards and the
      linter is green on it; re-run after the commit for a `clean` five.

## Measured results

**The heuristic sweep does not survive its own numbers.** The documents hold 133 `N of M`
pairs and 141 percentages; reporting them all is 274 candidates a run. Its strongest form,
one denominator stated with two different numerators, reports **7 groups of which 2 are
real**, a precision of 29%. The five false ones are different claims about the same
population (*0 of 84*, *10 of 84*, *18 of 84*), which is normal writing rather than a
defect. That is why the registry is curated ([`D-158`](../decisions.md#d-158)).

**Three live figures were stale when this shipped.** `CLAUDE.md`'s own link counts, offered
there as re-measurable rather than folklore, were 547/518/340 against 620/540/344.
[`documentation.md`](documentation.md) claimed *16 of 16* ledger rows against 21. And
[`foreign-incumbent.md`](../studies/foreign-incumbent.md), which owns the illegal-past
figure, still headed the section *Ten of thirteen* while four other documents said eight. <!-- lint-ok: it names the figure it corrected -->

**Spelled-out numbers are the load-bearing half.** Every stale copy in incident 2 was
written *ten of thirteen*, never *10 of 13*. A check reading digits only would have caught
none of them.

**One figure costs an annotation in an unrelated study.** Instance 8's recorded 7.71 s is
stated in six documents, and no pattern separates it from
[`penalty-search.md`](../studies/penalty-search.md)'s 5.74 s, which is a different
measurement of a different set in nearly the same words. That line carries a `lint-ok`
saying so. The alternative was leaving a figure with six copies unregistered, which is the
worse trade: the annotation is one line and permanent, and the copies drift.

**The pattern is anchored forward on purpose.** `7.71 s to prove optimality, re-measured at
8.43 s` states two numbers; only the one immediately before the phrase is the figure. A
two-sided context window would have captured both and reported the re-measurement as a
disagreement, so this entry uses a lookahead where the illegal-past entry uses `context`.
One mention stays outside it, in [`warm-start.md`](../studies/warm-start.md), which says
*hard enough to search for 7.71 s* without naming the proof.

## Out of scope

- Re-running any measurement. The linter reads documents.
- **Growing the registry.** It shipped with seven figures and takes more without a change to
  this component: `mutant-count` was added the same day, for a number in
  [`STATE.md`](../STATE.md) that had drifted by two while this was being built. The build
  tasks and gate above record the seven this shipped against, and are not recounted as the
  registry grows.
- **A figure whose value depends on a run artifact.** *How many mutants have not been in a
  full run* was written as a derived figure and removed: the only record of what a run
  covered is the gitignored `tests/mutation-report.json`, so it passed on a machine holding a
  report and would have failed in CI, where that file does not exist. **A check that reads a
  gitignored file makes the verdict a property of the machine**, which is the defect
  [`D-118`](../decisions.md#d-118) and [`D-121`](../decisions.md#d-121) already record. Any
  future figure must derive from tracked, committed inputs alone.
- A heuristic sweep of every `N of M` in the documentation, unless the numbers below say
  it is quiet enough to survive.

## Decisions

1. **A curated registry, a heuristic sweep, or re-running the measurements?**
   **Resolved:** the registry. The sweep was measured first and is 29% right in its best
   form. Re-running is unavailable rather than merely expensive: the foreign instances are
   fetched rather than committed ([`D-125`](../decisions.md#d-125)) and instance 23 costs
   561 s to build. `reproducible` records which figures a re-run *would* settle, and the
   linter runs none of them ([`D-158`](../decisions.md#d-158), 2026-09-03).
2. **Where does a pinned figure's value come from?** **Resolved:** the owner's marked line.
   A registry holding values is a fourth copy of every number and would go stale the same
   way; reading from the owner also makes the same entry work against any commit, which is
   what let the history gate run at all (2026-09-03).
3. **What happens to a document that states a superseded figure on purpose?**
   **Resolved:** the existing `<!-- lint-ok -->` escape hatch, with the reason on the line.
   Five lines carry one. The risk is that it becomes the way to silence the check rather
   than to declare a number historical, and nothing mechanical can tell those apart: it is
   a review obligation, like the rest of the charter (2026-09-03).
4. **Is a `- [x]` gate box a measurement or a coverage claim?** **Resolved:** it can be
   either, and the linter cannot tell. *Every ledger row names its spec, 16 of 16* is a <!-- lint-ok: it quotes the box it moved -->
   claim that is supposed to still be true, so the live count moved to the
   [ledger](README.md) where it is recounted, and the gate box keeps its dated figure and
   says which day it was checked (2026-09-03).

---

*The ledger: [`README.md`](README.md). The reasoning behind the shape of this file:
[`documentation.md`](documentation.md#specs-for-the-built-components).*
