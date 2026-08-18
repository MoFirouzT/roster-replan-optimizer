# The mutation harness, and the five times it was confidently wrong

**Question.** Every test layer in this repo claims to catch something.
How is that claim checked, and what happens when the checker itself is broken?

**Answer.** `tests/mutation.py` holds a committed catalogue of deliberate defects, **each naming the layer that must object**.
It has found **four blind spots behind fully green suites**.
It has also been wrong about its own verdict five times, and each of those cost a hardening — the more useful half of this study, because a harness that reports confidently and falsely is worse than one that fails loudly.

```bash
uv run python -m tests.mutation
uv run python -m tests.mutation -k service --report /tmp/service-rerun.json
```

## Why each mutant names its catcher

Run the whole suite against any mutant and *something* fails.
That says nothing about whether the ground-truth layer can see a wrong threshold, or whether the golden record can see a reweighted objective.
Those are separate claims and they need separate answers, so a mutant caught only by some *other* layer is reported as a **miss** rather than a pass ([`D-077`](../decisions.md#d-077)).

An off-the-shelf mutation tool was rejected for the opposite reason: thousands of generated mutants, most meaningless, burying the handful that encode a real hypothesis about a layer.

The rule that follows: **adding a test layer means adding a mutant for it.** The harness is where a layer earns being trusted.

## What it found

| Blind spot | Behind |
| --- | --- |
| The differential harness could not see a wrong `min_rest_hours` at all — its only instance opened mornings, so every gap it could express was 24 hours | a green suite |
| [`D-057`](../decisions.md#d-057)'s domination bound, documented as *validated rather than trusted*, had no test asserting it fires | a green suite |
| Two search-path detectors blinded by canonicalising the optimum — 95 of 97, on a clean tree and 766 green tests ([`reproducibility.md`](reproducibility.md)) | a green suite, on two platforms |
| `R-MIN-HOURS`'s micro-instance set a floor of 15 hours against exactly 15 hours of shifts, so a floor could not be told from a ceiling ([`D-140`](../decisions.md#d-140)) | a green suite |

The last one is [`D-066`](../decisions.md#d-066)'s lesson in a new rule: **a fixture set proves a rule exists; only a fixture at the boundary proves it is enforced at the right number.**

## The five hardenings

Each one is the harness asserting something false, not failing to run.
That is the pattern, and it is why the verdict is read from `tests/mutation-report.json` rather than from a terminal.

**1. The restore has to be verified, not assumed** ([`D-077`](../decisions.md#d-077)).
An editor's format-on-save watcher reads a file when it changes and writes its result later — so during a run it sees the mutated text and its delayed write lands *after* the restore.
That left a swapped publication weight in a tree that looked clean at a glance.
The harness now retries the restore until it holds and checks every touched path against git before exiting.

**2. `clean` became `unverifiable`** ([`D-112`](../decisions.md#d-112)).
A report read `verdict: clean, trustworthy: true, leaked: []` with a mutated `checker.py` in the working tree, and named the reason three fields lower.
The clean-tree check subtracted files that were already modified — so it was blind to precisely the two files the run was mutating — and `trustworthy` was computed as `verdict != "leaked"`, a tautology when the leak check cannot see.

> **A field a reader is told to trust must not be the one field that cannot see the failure.**

Refusing to start on a dirty tree was rejected: the harness is used *when a layer is added or is about to be trusted*, which is mid-change by definition.

**3. A survivor that was not one** ([`D-139`](../decisions.md#d-139)).
The first three hardenings were the harness withholding a failure; this one was the harness **inventing** one.
A mutant reported as a survivor is caught decisively by hand — it raises `KeyError: -1` and fails twelve tests — but its defect had been written away inside the test window, so pytest found nothing wrong because nothing was wrong.
That reads as a hole in a test layer, which is the most expensive wrong answer available: it points at the layer rather than at itself, and the natural response is to write a test for ground already covered.
Such a mutant is now `voided`, and the verdict is `unverifiable`.

**4. Fourteen mutants were never tested** ([`D-141`](../decisions.md#d-141)).
CPython validates a `.pyc` against the source's **size and its mtime in whole seconds**.
A mutation changing neither is invisible to that check, so the interpreter loads the cached bytecode and runs the *original* code — the mutant survives without ever having been tested.

Proved rather than inferred: with the mutation on disk and the mtime untouched, a probe runs clean; with identical bytes and the mtime bumped two seconds, it raises the `KeyError` the mutation causes.

Fourteen of the 132 mutants are size-neutral — swapping two identifiers, `>=` for `<=`, a range's bounds — and **every survivor across four full runs was one of them**.
This is worse than the three before it: those made the verdict untrustworthy in ways the report could state, while this made a `clean` verdict *partly hollow*, and nothing said which mutants it applied to.

**5. A catch against a red catcher is not a catch** ([`D-143`](../decisions.md#d-143)).
A mutant is scored caught when its catcher fails — so a catcher that was *already* failing scores every mutant it guards as caught without testing one of them.
A run reported **132 of 132 caught, `clean`, `trustworthy: true`** with one mutant scored on a test that could not have passed whatever the code did.
The harness now checks every distinct catcher passes before anything is mutated: 25 runs rather than 132, because the question is about the tree, not about a mutation.

**CI found that one**, which is the second time CI has caught what the local discipline could not.

## Reading a verdict

Four answers, in order of severity: `leaked`, `unverifiable`, `survivors`, `clean`.

- **`leaked`** — the run is void, not passing-with-a-caveat: every mutant after the leak may have been caught by the leftover defect.
- **`unverifiable`** — every mutant was caught and the run **could not vouch for the tree it ran in**. `unvouched_for` names the paths.
- **`survivors`** — worth one check before believing it, since hardening 3. Apply the mutant by hand and confirm it fails before writing a test.
- **`clean`** — and note that every `clean` recorded before hardening 4 should be read with its caveat.

**A late write costs one layer, not a whole run** ([`D-130`](../decisions.md#d-130)).
Only the mutants touching the named paths are in doubt, so re-run that layer alone — **and send it somewhere else with `--report`**, or a 5-mutant report overwrites the 132-mutant one it was meant to repair.

## What a run costs, and why the number is recorded

The runtime was folklore, and every copy of it was wrong: the module docstring and `CLAUDE.md` both said *tens of minutes*, a working session put it near a hundred, and **the one durable record kept no clock**.

Every run now writes `started_at` and `duration_seconds`.
A wrong cost estimate quietly discourages the exact use the harness exists for — an hour-long job gets scheduled around, a ten-minute one gets run.

| Run | Mutants | Duration |
| --- | --- | --- |
| default catcher-only mode | 103 | 9m27s |
| after hardening 4 made the harness delete cached bytecode | 132 | 13m50s |

Recompiling is most of that difference, and it is what a size-neutral mutant costs to test at all.
`duration_seconds` comes from `time.monotonic()` rather than from subtracting wall-clock stamps, which would measure a laptop that sleeps mid-run as much as the run.

## What is still open

**A recorded lesson is not a control** ([`D-138`](../decisions.md#d-138)).
[`D-131`](../decisions.md#d-131) recorded a defect where rule parameters were encoded, tested, specified and unreachable by any caller — and it happened again seven rules later.
What caught the repeat was the harness **refusing to start** on stale anchors: its self-protection found a product defect while protecting itself from a stale catalogue.

The general fix — a test walking every `domain` field and asserting a wire counterpart — is named rather than made.

The window in hardening 3 is bounded but not closed: a write landing *between* the check and the tests' own reads is still possible.
Turning format-on-save off remains the actual fix, and the harness now makes its absence detectable rather than misleading.
