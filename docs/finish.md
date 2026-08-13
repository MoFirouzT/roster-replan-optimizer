# Finish declaration

**T3 is complete. The project is finished in the sense `PLAN.md` defined**: T0 through T3 shipped,
every tier gate passed on evidence rather than on prose, and every spec reconciled with its code.
T4 and T5 were always upside and remain unbuilt.

This document is the declaration `PLAN.md` required, and its job is to be **checkable rather than
celebratory**. What is not done is listed with the same care as what is, because a finish declaration
that only lists achievements is the failure mode this project was built to avoid.

Date: 2026-08-13. Nineteen commits.

## The gates, and what passed them

| Tier | Gate | Passed by |
| --- | --- | --- |
| T0 | something solves, inspectable by eye | the walking skeleton |
| T1 | the repo is trustworthy — a reviewer can see why the model is what the spec says | two independent readings, five test layers, brute-force ground truth |
| T2 | the headline claim is proven against baselines, on a stated instance distribution | four methods over 72 committed cases, both axes, seven studies |
| T3 | production surface | async job service, fallback ladder, telemetry, fairness, model cache |

**None of these could be passed by writing.** T1 needed a checker that disagrees with the model when
one of them is wrong. T2 needed numbers that could have come out the other way, and several did. T3
needed a service that runs.

## What the project measured, including what it got wrong

The headline claim held: **the disruption objective cuts mean disruption from 323 to 66** against a
cold cost re-solve. The rest of the results are more interesting than that, because a majority of the
levers this project expected to matter did not.

| Claim | Outcome |
| --- | --- |
| Disruption objective beats a cold re-solve | **Held** — 323 → 66 |
| Warm starting is a major speedup | **9% of search time**, invisible end to end |
| Greedy repair is a weak baseline | **Ties the optimum on 64 of 72 cases** |
| Presolve is "often the largest single win" | 28% off build — real, not the largest |
| Symmetry breaking helps | **Null** — 3 interchangeable employees in 24 cases |
| The `regular` automaton wins | **Rejected** — 20% slower; one window to replace |
| Pattern/column variables are "dramatically stronger" | **Rejected** — no proof of optimality in 30 s |
| Caching the compiled model is the big latency win | **0 hits in 144 replan solves** |
| — | The real win was memoising one method: **20% off build** |
| CP-SAT is the right solver for this | **Not for speed** — SCIP proves the same optimum faster on 24/24 |

Six of those contradict something a spec or an outline asserted before it was measured, and each is
recorded as a correction with the original reasoning left intact (`D-082`, `D-087`, `D-088`, `D-009`,
`D-093`, `D-001`). That was the point of the rhythm.

**`D-001` was the last one written**, and it is the sharpest: the project's founding solver choice
turns out not to be justified by speed. CP-SAT ships because assumption literals, `violations()` and
non-linear expressiveness are load-bearing for three other commitments — at a measured cost of about
1.3 ms per solve, against a model build costing four times that.

**The D0–D4 study delivered what `replan.md` promised**: the five metrics genuinely disagree, on
23 of 72 cases, at roughly 100% relative regret in both directions — and the divergence found in the
wild reproduces the Ana/Bram example the spec invented to argue it was possible.

## What is not done

### Scheduled and not delivered

**Capture and replay** ([`specs/capture.md`](specs/capture.md)) is the one component `PLAN.md`
scheduled inside a completed tier that does not exist. It never gated T2, by design: corpus
population depends on an external authorization this project does not control, and a vendor adapter
built before the payload shape is known yields a round-trip test proving only that the adapter
matches a guess.

It matters more than its status suggests, and the reason is in [`benchmarks.md`](benchmarks.md):
**the incumbent is solved by the system under test**. Every benchmark number here shows that a replan
beats a re-solve *given a roster this model would produce*, not that the model resembles what real
planners publish. Only a captured corpus can carry the second claim. That is the largest single gap
in the evidence, and it is stated here rather than in a footnote.

### Deferred with reasons, in the specs that own them

- **The cost model is a flat rate** and `cost_weight` ships at `0` (`D-050`). The disruption/cost
  frontier therefore has no cost axis to trace. Needs wage data.
- **Five open decisions** remain in `decisions.md`: three for capture (`D-015`–`D-017`) and two for
  T4. Every T1, T2 and T3 decision is written.
- **Service `[TODO]`s**: external queue store, metrics backend, interrupting a running solve.
- **`R-STUDENT-QUOTA`, `R-SUNDAY`, `R-BREAK`, `R-PT-MIN`, `R-PUB-NOTICE`** are registry entries
  marked optional and not encoded — asserted as such by `tests/test_specs.py` so they cannot quietly
  pass as implemented.

### Never started, by design

T4 (infeasibility explainer, tool surface, NL → profile) and T5 (LNS, generation mode, learned warm
starts, fairness objectives). `PLAN.md`: *T3 is a legitimate finish. T4 and T5 are upside, each
independently shippable.*

## "All specs true", and how far that is checkable

Every spec has been reconciled with its code. Two were corrected during this declaration:
`model.md` still carried a `[TODO]` for a wire format that shipped with T3, and `capture.md` still
claimed its adapter would land in T2.

Prose-level truth is a reading task and was done by reading. What can be mechanised now is, in
`tests/test_specs.py`:

- every rule the registry marks encoded appears in **both** readings, and neither reading invents one;
- every unencoded registry entry is marked optional;
- every decision ID referenced in any document or source file exists;
- **no decision ID is used twice** — `D-089` was assigned twice during T3 and only a human noticed;
- every relative link between documents resolves — which failed on its first run.

## The state of the repo

| | |
| --- | --- |
| Tests | 563 |
| Mutants, each naming the layer that must catch it | 59 |
| Import-linter contracts | 8 |
| Decision records | 90, with 5 still open |
| Studies, including nulls | 8 |
| Python | ~12,000 lines |

The mutation harness is the claim behind the test count: every layer has been shown to fail. It
found four blind spots behind a fully green suite during T1 and T2, and during T3 it found four more
— a ladder rung that reported a timeout as a proof, an absence test passing for the wrong reason, a
dead defensive call, and a fairness property no single response could show.

## Ratifications

`PLAN.md` listed two items to settle here. Both are settled (`D-095`).

1. **Repo name: `roster-replan-optimizer`, ratified unchanged.** Accurate, and it matches the package
   name, the remote and every link in the docs. Nothing the project learned contradicts it.
2. **Public/private fork: deliberately deferred, not executed.** `PLAN.md`'s recommended default was
   *public on completion*, and the IP-hygiene test it set itself is satisfied — the project is
   synthetic throughout, with no tenant data, no vendor payloads and no wage data, so it would pass
   "would I be fine if this went public tomorrow?" today. The owner has chosen to keep it private for
   now, which changes nothing about the code. Publication is irreversible in practice — whatever is
   published can be cached and indexed after any revert — so leaving a reversible decision reversible
   is the cheaper order to do these in.

**This declaration is therefore complete.**

## Archived

`PLAN.md` is archived to [`archive/PLAN.md`](archive/PLAN.md) and is not maintained. Anything in it
that is still true has moved into a spec; anything that has not is sequencing, which has been spent.
