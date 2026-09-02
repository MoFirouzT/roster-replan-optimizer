# The mutation harness

**Status:** Implemented 2026-08-21
**Reconstructed 2026-09-02** from [`tests/mutation.py`](../../tests/mutation.py),
[`studies/mutation-harness.md`](../studies/mutation-harness.md),
[`internals/testing.md`](../internals/testing.md), `tests/mutation-report.json`, the
records cited below, and the commits of 2026-08-13 to 2026-08-21. **It is not the work
order this component was built from**; no such document existed
([`spec-reconstruction.md`](spec-reconstruction.md)).
**Depends on:** [`validation.md`](validation.md), whose layers it tests.

## Objective

A committed catalogue of deliberate defects in which **each mutant names the layer that
must object**, so the harness answers *can this layer see this defect* rather than the
weaker *does anything fail*.

## Motivation

Every test layer in this repository claims to catch something. A layer that has never
been shown to fail is not known to work, and a fully green suite is evidence about the
code rather than about the suite.

Naming the catcher is what makes the answer worth having. Run the whole suite against any
mutant and something fails; that says nothing about whether the ground-truth layer can
see a wrong threshold or whether the golden record can see a reweighted objective. Those
are separate claims and they need separate answers, so a mutant caught only by some other
layer is reported as a **miss** ([`D-077`](../decisions.md#d-077)).

## Canonical reference

[`internals/testing.md`](../internals/testing.md) owns the verdict table and how to run
it. [`studies/mutation-harness.md`](../studies/mutation-harness.md) owns what it found
and the five times it was wrong about itself.

## Governing reference

None. Mutation testing is standard technique; what is unusual here is the catcher naming,
and that is a local choice rather than a published one.

## Parameters and configuration

```bash
uv run python -m tests.mutation
uv run python -m tests.mutation -k service --report /tmp/service-rerun.json
```

`-k` selects a layer. `--report` redirects the output file, and **a re-run without it
overwrites the full report with a five-mutant one** ([`D-130`](../decisions.md#d-130)).

## Interfaces

Each `Mutant` carries a name, the layer expected to catch it, the source file, the exact
text to replace, its replacement, and the test file that is its catcher. The verdict is
read from `tests/mutation-report.json`, never from the terminal: reading a result through
a pipe has twice destroyed it, because `tail` truncates the per-mutant lines *and*
reports its own exit status.

Four verdicts, in order of severity: `leaked`, `unverifiable`, `survivors`, `clean`.

## Layering

None. The harness is test infrastructure and imports nothing from the package under test.

## Build tasks

- [x] Write a mutant for every test layer, each naming its catcher.
- [x] Score a mutant caught by any other layer as a miss.
- [x] Verify the restore rather than assuming it, and check every touched path against
      git before exiting.
- [x] Record `started_at` and `duration_seconds` from `time.monotonic()`.
- [x] Delete cached bytecode after every write.
- [x] Check every distinct catcher passes before anything is mutated.

## Test contract

`tests/test_mutation_harness.py` tests the harness itself, and two `specs` mutants cover
the catalogue's own anchors. The harness is the one component here whose real test is its
own history: five of its hardenings came from it asserting something false, and each is
recorded rather than quietly patched.

## Acceptance gate

*Blocks:* trusting any test layer. A layer arrives with its mutant.

- [x] Every mutant is caught by the layer named for it. **136 of 136** on 2026-08-21.
- [!] **The verdict of that run is `unverifiable`, not `clean`.** Three files it mutated
      were already modified or were written back after the restore:
      `benchmarks/weights.py`, `roster_replan/disruption.py`, `roster_replan/model.py`.
      The catches are probably real and are not vouched for
      ([`D-112`](../decisions.md#d-112)). This is the honest standing state of the
      component and it is recorded in [`STATE.md`](../STATE.md) rather than rounded to a
      pass.
- [x] A run records what it cost. **852 s for 136 mutants**, against 9m27s for 103 before
      the bytecode fix ([`D-130`](../decisions.md#d-130),
      [`D-141`](../decisions.md#d-141)).

## Measured results

**Four blind spots, each behind a fully green suite:**

| Blind spot | |
| --- | --- |
| The differential harness could not see a wrong `min_rest_hours` at all: its only instance opened mornings, so every gap it could express was 24 hours | [`D-066`](../decisions.md#d-066) |
| [`D-057`](../decisions.md#d-057)'s domination bound, documented as *validated rather than trusted*, had no test asserting it fires | |
| Two search-path detectors blinded by canonicalising the optimum: 95 of 97, on a clean tree and 766 green tests | [`D-124`](../decisions.md#d-124) |
| `R-MIN-HOURS`'s micro-instance set a floor of 15 hours against exactly 15 hours of shifts, so a floor could not be told from a ceiling | [`D-140`](../decisions.md#d-140) |

**Five hardenings, and each one is the harness asserting something false rather than
failing to run.** That pattern is the more useful half of this component, because a
harness that reports confidently and falsely is worse than one that fails loudly.

1. **The restore has to be verified.** A format-on-save watcher's delayed write landed
   after the restore, leaving a swapped publication weight in a tree that looked clean
   ([`D-077`](../decisions.md#d-077)).
2. **`clean` became `unverifiable`.** A report read `verdict: clean, trustworthy: true`
   with a mutated `checker.py` in the tree. The clean-tree check subtracted files that
   were already modified, so it was blind to precisely the files being mutated, and
   `trustworthy` was computed as `verdict != "leaked"`, a tautology when the leak check
   cannot see ([`D-112`](../decisions.md#d-112)). **A field a reader is told to trust must
   not be the one field that cannot see the failure.**
3. **A survivor that was not one.** The first three hardenings were the harness
   withholding a failure; this one was it **inventing** one. The mutant's defect had been
   written away inside the test window, so pytest found nothing wrong because nothing was
   wrong. That reads as a hole in a test layer, which is the most expensive wrong answer
   available ([`D-139`](../decisions.md#d-139)).
4. **Fourteen mutants were never tested.** CPython validates a `.pyc` against the
   source's size and its mtime in whole seconds, so a size-neutral mutation is invisible
   to that check and the interpreter runs the original code. Proved rather than inferred,
   and **every survivor across four full runs was one of the fourteen**
   ([`D-141`](../decisions.md#d-141)).
5. **A catch against a red catcher is not a catch.** A run reported 132 of 132 caught,
   `clean`, `trustworthy: true`, with one mutant scored on a test that could not have
   passed whatever the code did. **CI found that one**
   ([`D-143`](../decisions.md#d-143)).

## Out of scope

- **An off-the-shelf mutation tool.** Thousands of generated mutants, most meaningless,
  burying the handful that encode a real hypothesis about a layer.
- **Refusing to start on a dirty tree.** The harness is used when a layer is added or is
  about to be trusted, which is mid-change by definition. Running dirty is allowed and
  buys a weaker result, and the verdict now says so.
- **Running it in the normal suite.** It rewrites source files.
- **Closing the window in hardening 3.** A write landing between the check and the tests'
  own reads is still possible. Turning format-on-save off is the actual fix, and the
  harness makes its absence detectable rather than misleading.
- **The general reachability test.** A test walking every `domain` field and asserting a
  wire counterpart is named rather than made
  ([`D-138`](../decisions.md#d-138)).

## Decisions

Reconstructed. Each was decided while the component was built, and the record is the
citation.

1. **Does a mutant name its catcher?** Yes, and a catch elsewhere is a miss
   ([`D-077`](../decisions.md#d-077)). Without it the harness answers a question nobody
   asked.

2. **Where is the verdict read from?** The report file
   ([`D-130`](../decisions.md#d-130)). A pipe has destroyed a run twice.

3. **Is `survivors` believed on sight?** No, not since hardening 3
   ([`D-139`](../decisions.md#d-139)). Apply the mutant by hand and confirm it fails
   before writing a test for ground that may already be covered.

4. **Does a late write cost a whole re-run?** No, one layer
   ([`D-130`](../decisions.md#d-130)), and the re-run must be sent somewhere else.

5. **Is a recorded lesson a control?** No, and this component is the proof
   ([`D-138`](../decisions.md#d-138)). [`D-131`](../decisions.md#d-131) recorded a
   reachability defect and it happened again seven rules later. What caught the repeat
   was the harness refusing to start on stale anchors: its self-protection found a
   product defect while protecting itself.

---

*The ledger: [`README.md`](README.md). What it found:
[`studies/mutation-harness.md`](../studies/mutation-harness.md). The layers it tests:
[`validation.md`](validation.md).*
