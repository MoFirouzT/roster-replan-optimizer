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

*(The set is 84 cases since `D-105`. The greedy comparison is re-measured over all of them; the other
T2 analyses are not, and the two added classes sit outside their basis.)*

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
| Greedy repair is a weak baseline | **Ties the optimum on 64 of 72 cases** — 71 of 84 once the coverage axis was sampled in the middle (`D-105`) |
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
- **Two open decisions** remain in `decisions.md`, both T4 (`D-012`, `D-013`) and both about the LLM
  boundary. Every decision for T1, T2, T3 and capture is written — capture's three were writable
  without the corpus, because the reasoning never depended on it, only the execution does.
  *(Both were written when T4 was built; the Open table is now empty. See the postscript.)*
- **Service `[TODO]`s**: external queue store, metrics backend, interrupting a running solve.
- **`R-STUDENT-QUOTA`, `R-SUNDAY`, `R-BREAK`, `R-PT-MIN`, `R-PUB-NOTICE`** are registry entries
  marked optional and not encoded — asserted as such by `tests/test_specs.py` so they cannot quietly
  pass as implemented.

### Never started, by design

T4 (infeasibility explainer, tool surface, NL → profile) and T5 (LNS, generation mode, learned warm
starts, fairness objectives). `PLAN.md`: *T3 is a legitimate finish. T4 and T5 are upside, each
independently shippable.*

*(T4 was built after this declaration and is described in the postscript below. Half of T5 was
retired on measurements this project had already taken — `D-104`.)*

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

## Postscript: T4, built after the declaration

Date: 2026-08-14. The declaration above is left as it was written; this section says what changed
rather than rewriting a record of what was true on 2026-08-13.

**T4 is built.** `PLAN.md` listed it as upside, and it shipped as five pieces:

| Piece | Where | The decision it turned on |
| --- | --- | --- |
| Shortfall and infeasibility explainer | [`explain.py`](../roster_replan/explain.py), [`prose.py`](../roster_replan/prose.py) | `D-097` — explain shortfalls first, and answer from the checker |
| Minimal cores | [`core.py`](../roster_replan/core.py) | `D-100` — the objective inflates the core; deletion is a null on top |
| Tool surface and hypotheticals | [`service/tools.py`](../roster_replan/service/tools.py), [`whatif.py`](../roster_replan/whatif.py) | `D-098` — unlawful hypotheticals are refused, not answered |
| Profile review | [`profile.py`](../roster_replan/profile.py) | `D-099` — deterministic, and enabling an unencoded rule is a defect |
| NL → profile | [`nl.py`](../roster_replan/nl.py) | `D-101` — the schema is the confinement, and an open mapping is not a schema |
| Parse eval | [`nl_eval.py`](../benchmarks/nl_eval.py) | `D-102` — score what was invented, not only what was found |

**The two open decisions are written.** `D-012` and `D-013` were the only entries left in the Open
table, and both were writable once the boundary they describe existed. The table is now empty.

**What T4 measured, and got wrong.** The pattern held. `D-100` deferred core minimisation on the
grounds that a sufficient core names unnecessary rules; measured, the cause was not the one deferred
work was aimed at — dropping the objective cuts a 160-gate core to two, and the deletion loop that
was supposed to do the work removes nothing on top. `D-101` is the sharper one, because it is a
defect rather than a null: the derogation field the prompt asked the model to fill compiled to an
object that **could hold nothing**, and every behavioural test passed over it, because a stub returns
what the test hands it. The layer now reads the compiled schema.

**The parse has been measured.** `benchmarks/nl_eval.py` scores **18/18 on three consecutive runs**,
after 16/18 on the first ([`studies/nl-parse.md`](studies/nl-parse.md)). It found one real defect and one of its own:
`unclear` had been specified in a way that invited an assumptions log, so a profile that parsed
perfectly came back with caveats about what the text did not say (`D-103`); and the eval had scored
its author's capitalisation of a shift label as the correct one. The extraction itself was right in
every case on the first run, Dutch and adversarial cases included.

What that does **not** establish is stated in the study and belongs here too: fifteen cases written
by the same person who wrote the parser and the prompt. It is the incumbent problem from
[`benchmarks.md`](benchmarks.md) one layer up — **the text is text this system imagined**, not what
a Belgian horeca operator would send. Two Dutch cases are a smoke test, and a single run says
nothing about whether the same text parses the same way twice.

**What is still not done.** Everything in *What is not done* above stands: capture and replay, the
cost axis, the service `[TODO]`s, and the five unencoded optional rules.

**Half of T5 is retired rather than pending** (`D-104`, `D-105`). LNS improves a solution the solver
cannot prove optimal in the time available, and neither half of that is true here — 2,160 solves
returned `OPTIMAL`, longest search 12.4 ms, and solver-free greedy already ties the optimum on 71 of
84 cases. Learned warm starts would optimise the 9% of search time `D-082` measured, on a search that
takes milliseconds. Both are struck from the plan.

`D-105` then swept the generator's whole range rather than inferring from one sample of it: demand at
105% of capacity, minimum slot slack of −7, 40 employees, every pressure at once — all `OPTIMAL` in 3
to 11 ms, with the structurally short cases running *faster* than the baseline. What would reopen
these is a longer horizon or a tenant an order of magnitude larger, and neither exists here.

Generation mode and fairness objectives stay open, because nothing measured here touches them. The
fairness T3 shipped is round-robin across *tenants in the queue* (`D-091`) and says nothing about
how unsocial shifts fall across *people*, which is the fairness a works council argues about.

**The mutation harness was run in full**, for the first time since T4's layers landed: 80 mutants,
all caught by the layer named to catch them. Four of those are the parse layer's, and the first
restores `D-101`.

| | At the declaration | Now |
| --- | --- | --- |
| Tests | 567 | 729 |
| Mutants | 59 | 83 |
| Import-linter contracts | 8 | 10 |
| Decision records | 94, 2 open | 105, none open |
| Studies, including nulls | 8 | 11 |
| Python | ~12,000 lines | ~17,100 lines |

## Archived

`PLAN.md` is archived to [`archive/PLAN.md`](archive/PLAN.md) and is not maintained. Anything in it
that is still true has moved into a spec; anything that has not is sequencing, which has been spent.
