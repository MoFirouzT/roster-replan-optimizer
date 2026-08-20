# Finish declaration

> **Two documents in one file, current state first.** [*Where the project stands*](#where-the-project-stands) is
> what is true now: what shipped, what it cost, what it got wrong, and what is still not done.
>
> [*The declaration*](#the-declaration-as-written-on-2026-08-13) below it is as it was written on 2026-08-13, when T3 was the
> finish — **including the sentences later work made false**, because a record that gets edited
> whenever the world moves is not a record. That is the rule `decisions.md` already runs on:
> supersede, never rewrite. The bracketed notes inside it are the only additions and they point
> forward — that, and the heading levels, which were demoted one step so the two parts nest. No words
> inside it were changed, and it was moved below the current state rather than rewritten ([`D-146`](decisions.md#d-146)).
> One of its claims (*"T4 and T5 were always upside and remain unbuilt"*) stopped being true on
> 2026-08-14.

## Where the project stands

Date: 2026-08-17. The declaration that follows is left as written.
This section is the same exercise applied to everything since, and there is more of it than *postscript* implied: **T4 and T5 both closed**.
`PLAN.md` is built out in full.

Each line below is a status, not a retelling.
The analysis is in the studies and the reasoning is in the records, both one click away.

### T4, built in full

| Piece | Where | The decision it turned on |
| --- | --- | --- |
| Shortfall and infeasibility explainer | [`explain.py`](../../roster_replan/explain.py), [`prose.py`](../../roster_replan/prose.py) | [`D-097`](decisions.md#d-097) — explain shortfalls first, and answer from the checker |
| Minimal cores | [`core.py`](../../roster_replan/core.py) | [`D-100`](decisions.md#d-100) — the objective inflates the core; deletion is a null on top |
| Tool surface and hypotheticals | [`service/tools.py`](../../roster_replan/service/tools.py), [`whatif.py`](../../roster_replan/whatif.py) | [`D-098`](decisions.md#d-098) — unlawful hypotheticals are refused, not answered |
| Profile review | [`profile.py`](../../roster_replan/profile.py) | [`D-099`](decisions.md#d-099) — deterministic, and enabling an unencoded rule is a defect |
| NL → profile | [`nl.py`](../../roster_replan/nl.py) | [`D-101`](decisions.md#d-101) — the schema is the confinement, and an open mapping is not a schema |
| Parse eval | [`nl_eval.py`](../../benchmarks/nl_eval.py) | [`D-102`](decisions.md#d-102) — score what was invented, not only what was found |

The Open table is empty: [`D-012`](decisions.md#d-012) and [`D-013`](decisions.md#d-013) were its last entries and both became writable once the boundary they describe existed.

### T5, closed: two built, two retired on measurement

| Item | Outcome |
| --- | --- |
| LNS | **Retired** ([`D-104`](decisions.md#d-104), [`D-105`](decisions.md#d-105)) — it improves a solution the solver cannot prove optimal in time, and neither half is true here |
| Learned warm starts | **Retired** ([`D-104`](decisions.md#d-104)) — they would chase the 9% of search time [`warm-start.md`](studies/warm-start.md) measured |
| Fairness objectives | **Shipped** ([`D-108`](decisions.md#d-108)) — rolling balance of unpopular shifts, and a third meaning of the word in this repo |
| Generation mode | **Shipped** ([`D-109`](decisions.md#d-109)) — the cold-start case, made testable rather than argued |

### What it got wrong

Six findings, each one a place a claim in this repository was false.
They are listed rather than told, because each has a study that tells it properly.

| Finding | Where it is told |
| --- | --- |
| **The optimum was degenerate**, so `README.md`'s reproducibility promise was false — and no test could see it, because none looked at *which* optimum | [`reproducibility.md`](studies/reproducibility.md) |
| Fixing that **blinded two test layers**: reproducibility and observability were trading against each other, and only one side was priced | [`mutation-harness.md`](studies/mutation-harness.md) |
| The harness reported `clean` with a mutated file in the tree, a survivor it did not have, and **fourteen mutants it had never tested** | [`mutation-harness.md`](studies/mutation-harness.md) |
| Two rules were **named for a week and measured over a horizon**, and the differential harness could not have caught it — both readings were wrong in the same direction | [`horizon.md`](studies/horizon.md), [`D-110`](decisions.md#d-110), [`D-111`](decisions.md#d-111) |
| The last unmeasured rejection in the repo was measured, and **both reasons it gave were wrong** — size grows linearly, and a longer horizon buys nothing | [`horizon.md`](studies/horizon.md) |
| `D-100` deferred core minimisation for a cause that was not the one that mattered, and `D-101`'s derogation field **compiled to an object that could hold nothing** | [`D-100`](decisions.md#d-100), [`D-101`](decisions.md#d-101) |

Two premises were scoped rather than falsified.
[`D-081`](decisions.md#d-081)'s *build dominates search* holds at one week and not beyond, so **every performance conclusion here is a statement about a one-week horizon**.
And [`D-104`](decisions.md#d-104)'s retirement of LNS narrowed from *this never happens* to *this does not happen in the regime we serve*, once foreign data produced a 7.71-second search ([`D-127`](decisions.md#d-127)).

### What a roster from outside this project did to it

`benchmarks.md` has said since T2 that the incumbent is solved by the system under test, and this declaration called it the largest single gap in the evidence.
**Half of it is now closed**: published solutions from the nurse-rostering set reproduce the headline claim by **4.6× to 37×**, where the committed set shows about 5×.

It also found what a synthetic set could not — ten of thirteen published rosters have a past this model calls illegal, a defect in a fix made the same day, and **where the model stops**: about 40 employees over four weeks, against 527 seconds of model construction at 8M variables.

Full account: [`foreign-incumbent.md`](studies/foreign-incumbent.md).

### What is still not done

Three of these are blocked on something outside this repository, which is the honest reason they are not done.
The fourth is not blocked at all — it is deployment work with no findings in it.

| Gap | Blocked on |
| --- | --- |
| **Capture and replay** — was the largest gap, now half of one ([`D-125`](decisions.md#d-125)) | External authorization and real vendor payloads. A Belgian horeca corpus is still what this owns |
| The cost axis (`cost_weight` ships at 0, [`D-050`](decisions.md#d-050)) | Wage data |
| `R-STUDENT-QUOTA`, `R-SUNDAY`, `R-BREAK`, `R-PT-MIN`, `R-PUB-NOTICE` | A named legal source each — `rules.md` refuses a legality claim without provenance |
| Service `[TODO]`s: external queue store, metrics backend, interrupting a running solve | Nothing — these are deployment choices |
| No committed benchmark case runs at **more than one week**, though the service now answers them ([`D-113`](decisions.md#d-113)) | Nothing. The generator hard-codes seven days |

The capture gap outranks the rest and the reason is unchanged: **the incumbent is solved by the system under test.**
Every benchmark number here shows a replan beats a re-solve *given a roster this model would produce*.

### The state of the repo

| | At the declaration | Now |
| --- | --- | --- |
| Tests | 567 | 949, of which 45 skip without fetched benchmark data |
| Mutants, each naming the layer that must catch it | 59 | 132 |
| Import-linter contracts | 8 | 11 |
| Decision records | 94, 2 open | 143, none open |
| Studies, including nulls | 8 | 16 |
| Python | ~12,000 lines | ~24,500 lines |

The mutation harness has been run in full eight times since the declaration, and **only the last one means what a verdict is supposed to mean**: 132 of 132 caught, `clean` and `trustworthy`, on a verified tree.
The seven before it were each spoiled, and the five hardenings they produced are told in [`mutation-harness.md`](studies/mutation-harness.md).

## The declaration, as written on 2026-08-13

**T3 is complete. The project is finished in the sense `PLAN.md` defined**: T0 through T3 shipped,
every tier gate passed on evidence rather than on prose, and every spec reconciled with its code.
T4 and T5 were always upside and remain unbuilt.

This document is the declaration `PLAN.md` required, and its job is to be **checkable rather than
celebratory**. What is not done is listed with the same care as what is, because a finish declaration
that only lists achievements is the failure mode this project was built to avoid.

Date: 2026-08-13. Nineteen commits.

### The gates, and what passed them

| Tier | Gate | Passed by |
| --- | --- | --- |
| T0 | something solves, inspectable by eye | the walking skeleton |
| T1 | the repo is trustworthy — a reviewer can see why the model is what the spec says | two independent readings, five test layers, brute-force ground truth |
| T2 | the headline claim is proven against baselines, on a stated instance distribution | four methods over 72 committed cases, both axes, seven studies |
| T3 | production surface | async job service, fallback ladder, telemetry, fairness, model cache |

*(The set is 84 cases since [`D-105`](decisions.md#d-105). The greedy comparison is re-measured over all of them; the other
T2 analyses are not, and the two added classes sit outside their basis.)*

**None of these could be passed by writing.** T1 needed a checker that disagrees with the model when
one of them is wrong. T2 needed numbers that could have come out the other way, and several did. T3
needed a service that runs.

### What the project measured, including what it got wrong

The headline claim held: **the disruption objective cuts mean disruption from 323 to 66** against a
cold cost re-solve. The rest of the results are more interesting than that, because a majority of the
levers this project expected to matter did not.

| Claim | Outcome |
| --- | --- |
| Disruption objective beats a cold re-solve | **Held** — 323 → 66 |
| Warm starting is a major speedup | **9% of search time**, invisible end to end |
| Greedy repair is a weak baseline | **Ties the optimum on 64 of 72 cases** — 71 of 84 once the coverage axis was sampled in the middle ([`D-105`](decisions.md#d-105)) |
| Presolve is "often the largest single win" | 28% off build — real, not the largest |
| Symmetry breaking helps | **Null** — 3 interchangeable employees in 24 cases |
| The `regular` automaton wins | **Rejected** — 20% slower; one window to replace |
| Pattern/column variables are "dramatically stronger" | **Rejected** — no proof of optimality in 30 s |
| Caching the compiled model is the big latency win | **0 hits in 144 replan solves** |
| — | The real win was memoising one method: **20% off build** |
| CP-SAT is the right solver for this | **Not for speed** — SCIP proves the same optimum faster on 24/24 |

Six of those contradict something a spec or an outline asserted before it was measured, and each is
recorded as a correction with the original reasoning left intact ([`D-082`](decisions.md#d-082), [`D-087`](decisions.md#d-087), [`D-088`](decisions.md#d-088), [`D-009`](decisions.md#d-009),
[`D-093`](decisions.md#d-093), [`D-001`](decisions.md#d-001)). That was the point of the rhythm.

**[`D-001`](decisions.md#d-001) was the last one written**, and it is the sharpest: the project's founding solver choice
turns out not to be justified by speed. CP-SAT ships because assumption literals, `violations()` and
non-linear expressiveness are load-bearing for three other commitments — at a measured cost of about
1.3 ms per solve, against a model build costing four times that.

**The D0–D4 study delivered what `replan.md` promised**: the five metrics genuinely disagree, on
23 of 72 cases, at roughly 100% relative regret in both directions — and the divergence found in the
wild reproduces the Ana/Bram example the spec invented to argue it was possible. *(Re-run over the
widened set: 26 of 84, same structure, and [`D-060`](decisions.md#d-060) confirmed on a curve — [`D-106`](decisions.md#d-106). Then 10 of 84
once [`D-119`](decisions.md#d-119) moved the instances underneath it, which is what that rate turned out to measure; the
structure held and the curve did not — [`D-120`](decisions.md#d-120).)*

### What is not done

#### Scheduled and not delivered

**Capture and replay** ([`specs/capture.md`](capture.md)) is the one component `PLAN.md`
scheduled inside a completed tier that does not exist. It never gated T2, by design: corpus
population depends on an external authorization this project does not control, and a vendor adapter
built before the payload shape is known yields a round-trip test proving only that the adapter
matches a guess.

It matters more than its status suggests, and the reason is in [`benchmarks.md`](benchmarks.md):
**the incumbent is solved by the system under test**. Every benchmark number here shows that a replan
beats a re-solve *given a roster this model would produce*, not that the model resembles what real
planners publish. Only a captured corpus can carry the second claim. That is the largest single gap
in the evidence, and it is stated here rather than in a footnote.

#### Deferred with reasons, in the specs that own them

- **The cost model is a flat rate** and `cost_weight` ships at `0` ([`D-050`](decisions.md#d-050)). The disruption/cost
  frontier therefore has no cost axis to trace. Needs wage data.
- **Two open decisions** remain in `decisions.md`, both T4 ([`D-012`](decisions.md#d-012), [`D-013`](decisions.md#d-013)) and both about the LLM
  boundary. Every decision for T1, T2, T3 and capture is written — capture's three were writable
  without the corpus, because the reasoning never depended on it, only the execution does.
  *(Both were written when T4 was built; the Open table is now empty. See the postscript.)*
- **Service `[TODO]`s**: external queue store, metrics backend, interrupting a running solve.
- **`R-STUDENT-QUOTA`, `R-SUNDAY`, `R-BREAK`, `R-PT-MIN`, `R-PUB-NOTICE`** are registry entries
  marked optional and not encoded — asserted as such by `tests/test_specs.py` so they cannot quietly
  pass as implemented.

#### Never started, by design

T4 (infeasibility explainer, tool surface, NL → profile) and T5 (LNS, generation mode, learned warm
starts, fairness objectives). `PLAN.md`: *T3 is a legitimate finish. T4 and T5 are upside, each
independently shippable.*

*(T4 was built after this declaration and is described in the postscript below. T5 is closed too:
LNS and learned warm starts retired on measurement — [`D-104`](decisions.md#d-104), [`D-105`](decisions.md#d-105) — with fairness objectives and
generation mode built, [`D-108`](decisions.md#d-108) and [`D-109`](decisions.md#d-109).)*

### "All specs true", and how far that is checkable

Every spec has been reconciled with its code. Two were corrected during this declaration:
`model.md` still carried a `[TODO]` for a wire format that shipped with T3, and `capture.md` still
claimed its adapter would land in T2.

Prose-level truth is a reading task and was done by reading. What can be mechanised now is, in
`tests/test_specs.py`:

- every rule the registry marks encoded appears in **both** readings, and neither reading invents one;
- every unencoded registry entry is marked optional;
- every decision ID referenced in any document or source file exists;
- **no decision ID is used twice** — [`D-089`](decisions.md#d-089) was assigned twice during T3 and only a human noticed;
- every relative link between documents resolves — which failed on its first run.

### The state of the repo

| | |
| --- | --- |
| Tests | 567 |
| Mutants, each naming the layer that must catch it | 59 |
| Import-linter contracts | 8 |
| Decision records | 94, with 2 still open |
| Studies, including nulls | 8 |
| Python | ~12,000 lines |

The mutation harness is the claim behind the test count: every layer has been shown to fail. It
found four blind spots behind a fully green suite during T1 and T2, and during T3 it found four more
— a ladder rung that reported a timeout as a proof, an absence test passing for the wrong reason, a
dead defensive call, and a fairness property no single response could show.

### Ratifications

`PLAN.md` listed two items to settle here. Both are settled ([`D-095`](decisions.md#d-095)).

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

`PLAN.md` is archived to [`archive/PLAN.md`](PLAN.md) and is not maintained. Anything in it
that is still true has moved into a spec; anything that has not is sequencing, which has been spent.
