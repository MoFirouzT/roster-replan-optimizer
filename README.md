# roster-replan-optimizer

**Minimum-disruption shift-roster replanning under labour constraints.**

Someone calls in sick at 09:00 on Saturday.
The conventional answer is to re-solve the week from scratch, which returns a roster that is optimal, legal, and unrecognisable;
people whose shifts were never in question are moved so the solver can shave a marginal cost.

This service answers it differently:
**reproduce the roster with minimum disruption to everyone else.**
Past shifts are pinned, published shifts are penalised for changing, and the solve is warm-started from the roster it is repairing.
The penalty is what carries the result; the warm start is a small speedup, and the benchmarks say so in those terms.

> Generation is not a separate feature.
> It is the cold-start case of replanning — a replan from an empty roster.

---

## What it does

- **Replan:**
  repair a roster around absences, demand changes and late availability withdrawals, minimising weighted deviation from what people were already told.
- **Assign:**
  fill planner-created open shifts from an eligible workforce.
- **Verify independently:**
  every returned solution is re-checked against every rule by a plain function with no solver involved.
  Solutions that fail the checker are never returned.
- **Explain a short shift:**
  name the rule that blocked every person who could have filled it, in planner language —
  *9 of the 12 staff do not hold a skill the shift requires; 5 would not get the minimum rest*.
  This is the common case: with a soft coverage floor a shift comes back **priced** rather than refused.
- **Explain infeasibility:**
  in the rare case where no legal roster exists, return the *minimal* set of blocking rules with the day, shift and employee involved.
- **Answer a hypothetical:**
  *what if I hire one more flexi-jobber?* — re-solve under the change and report the difference.
  Unlawful hypotheticals are refused rather than answered.
- **Validate a profile before it is saved:**
  structural checks, contradictions between a tenant's own rules, rules that cannot bind, and a feasibility probe.
  Fully deterministic.
- **Configure in natural language:**
  describe a tenant's policy in plain English; the parse emits a typed profile, and the deterministic layers above decide whether it may be saved.
  The model is confined by a **narrow schema rather than by instruction** — it has nowhere to write an objective weight or to switch on a rule the solver does not enforce.
  It is the one stage that needs a language model, behind an optional dependency and an injected client: everything downstream works with no model available, and that is an import contract, not a promise.

Belgian labour law is encoded as **data, not code**:
rest gaps, weekly hour ceilings, flexi-job eligibility, same-day Dimona filing, student quotas, horeca minimum shift length.
Rules carry stable IDs used identically in the specs, the model, the checker, the violation objects and the explainer.
Full registry: [`docs/specs/rules.md`](docs/specs/rules.md).

Per-tenant policy lives in a profile document from day one, because across thousands of small tenants the configuration work, not the solve time, is the thing that does not scale.

---

## Headline results

Measured on the committed set in `benchmarks/manifest.json` (seeded generator, 84 cases across
14 scenario classes, 8–25 employees, one-week horizon), 3 solver seeds each, single-threaded.
Full method, segmentation and caveats in [`docs/benchmarks.md`](docs/benchmarks.md).

Weeks that were fully staffable before the disruption — 72 of the 84 cases, at the 5 s budget. Every method is scored on
the same D2 yardstick whatever it optimised; `changes` is assignments differing from the published
roster, `short` is positions left unstaffed.

| Method | p50 search | p95 search | Disruption (D2) | Changes | Short |
| --- | --- | --- | --- | --- | --- |
| Cold re-solve, cost objective | 3.61 ms | 10.5 ms | 307.3 | 12.36 | 0.15 |
| Greedy nearest-eligible repair | — | — | 53.6 | 1.94 | 0.31 |
| Cold solve, disruption objective | 3.58 ms | 10.7 ms | 65.3 | 2.40 | 0.15 |
| **Warm-started replan (this)** | 3.31 ms | 8.6 ms | 65.3 | 2.40 | 0.15 |

**The objective is what does the work**, not the warm start. Against a cold cost re-solve on identical
instances with identical coverage, the disruption objective cuts the score from 307 to 65 and the
number of people moved from 12.4 to 2.4. The warm start is worth about 9% of a 3 ms search — real,
paired on 662 of 756 runs, and small enough that the honest framing is the one above.

**Greedy is not the weak baseline it looks like.** It ties the optimal replan exactly on 71 of the 84
cases. Its lower average disruption is bought by leaving more shifts unstaffed, which is the trade
the shortfall weight exists to refuse. The optimiser earns its place on the 13 cases where the repair
needs a chain — move an uninvolved person so somebody else comes free — and on never being the one to
leave a shift uncovered.

That tie rate is a property of where the set samples, not of greedy: on a slack week greedy ties every
seed, and on a stretched one it loses half of them. The set now samples the middle of the coverage
axis as well as its ends (`D-105`).

The frontier is coverage, not cost: with a flat rate and a hard coverage ceiling, every fully staffed
roster costs the same paid hours, so the cost axis collapses. See
[`docs/benchmarks.md`](docs/benchmarks.md) for the per-class table and for what this set does *not*
show — nothing here ever came close to a time budget, and median damage is one assignment.

---

## Architecture

```text
                     NL config request
                            │
                   ┌────────▼─────────┐
                   │  profile builder │  LLM parse → schema validation →
                   │   (out of path)  │  contradiction check → feasibility probe
                   └────────┬─────────┘
                            │ typed profile (rejected if any stage fails)
   POST /solve ──► queue ──►│
   GET  /solve/{id}         ▼
   DELETE /solve/{id}   ┌───────────────┐     ┌──────────────┐
                        │ solver service│────►│   checker    │
                        │   (CP-SAT)    │     │ (no solver)  │
                        │   stateless   │◄────│  independent │
                        └───────┬───────┘     └──────────────┘
                                │ solution + status + gap + telemetry
                                ▼
                        explainer (minimal core → rule IDs → prose)
```

- **The solver service is stateless**:
  payload in, payload out, no database reads.
  Every solve's input, profile version and seed are persisted by the caller, so any roster produced in production can be reproduced offline.
- **Async by construction.**
  Solves take real time;
  synchronous HTTP breaks on timeouts, retry storms and the absence of cancellation.
- **The LLM never sits in the solve path.**
  It produces only artifacts a deterministic layer can reject:
  candidate configs (validated, then feasibility-probed) and prose renderings of conflicts
  the solver already proved.
- **Fallback ladder**:
  exact → time-boxed with reported gap → greedy repair → last known good.
  The service never returns nothing.

## Correctness

The model and the checker are two independent implementations of the same specification.
They share no rule logic — no predicate, no threshold — enforced in CI, and the differential harness is how we know which one is wrong.
Solver objectives are held against exhaustively enumerated optima on committed micro-instances, so the correctness claim rests on ground truth rather than on the solver agreeing with itself.

Test layers, invariants and the harness design: [`docs/specs/validation.md`](docs/specs/validation.md).

## Performance

The scaling problem here is **many small instances** and **interactive latency**, not one large instance.
Benchmarks are built accordingly; throughput and p95 across tenants, not a single 5000-employee monolith.

Levers, measured, including the three that did not pay off:

| Lever | Result |
| --- | --- |
| Domain presolve | **28% off build, 16% off search**, 24/24 cases — a quarter of the model removed |
| Memoising the shift-window lookup | **The largest one**: 20% off build, found by profiling — building costs more than solving here |
| Per-tenant compiled-model caching | **Null for replanning** — 0 hits in 144 solves; a replan changes the model's own inputs |
| Warm starts from the previous solution | **9% of search time**, paired on 216 runs; invisible end to end |
| Symmetry breaking | **Null** — 3 interchangeable employees across 24 cases. Worth 20% where symmetry exists, so the null is about the distribution |
| `regular` automaton for shift sequences | **Rejected, 20% slower** — a one-week horizon leaves exactly one window to replace |
| `no_overlap` intervals for rest gaps | **Rejected** — trades search time for build time, and the sign of the total flips by instance |
| Pattern/column variables | **Rejected** — no proof of optimality in 30 s on a cold week, against ~20 ms |

Five of the eight textbook levers lost, and the one that mattered most was the least interesting:
at these sizes the model is built more slowly than it is solved, and the biggest single win was one
memoised lookup that no encoding study could have found. Three of the four failures share a
cause worth naming — a global constraint aggregates, and this model gates every rule *instance*, so
replacing many local constraints with one global one coarsens what a failure can be blamed on. That
is a real cost when the T4 deliverable is an explainer. Each study, including every null:
[`docs/studies/README.md`](docs/studies/README.md).

## Deliberately out of scope

Authentication, persistence, a user interface, and demand forecasting.
All data committed to this repository is synthetic.
The forecast → optimise interface is documented in [`docs/specs/model.md`](docs/specs/model.md), not implemented.

## Quickstart

```bash
uv sync
uv run python -m roster_replan.demo scenarios/horeca/saturday_sick_call.json --weekday-of-day-zero 0
```

```text
tenant horeca-demo, profile horeca-2026.1
12 staff, 21 open shifts, 37 assignments published
replanning at hour 129 of the horizon

answer: exact — proven optimal
disruption 100040, gap 0.0%
solved in 12 ms

1 changed assignment(s):
  dropped    E03  Sat 15:00-23:00 (E)

Sat 15:00-23:00 (E) is 1 short of its 3 required staff.
  6 of the 12 staff do not hold a skill the shift requires (R-SKILL).
  5 of the 12 staff would not get the minimum rest between shifts (R-REST-GAP).
  E03, E05 and E07 are absent or unavailable then (R-AVAIL).
  E06, E10 and E11 would exceed their hours for the day (R-MAX-DAILY).
  E00 and E01 would exceed their hours for the week (R-MAX-WEEKLY).
```

The scenario file is the real wire format, so it doubles as the worked example of what a caller
sends. The shortfall is the honest outcome: E03 called in sick and **nobody could legally replace
them** — the explanation says why, person by person, and every line is derived rather than phrased
by a model.

Everything above — and the whole test suite — runs with no API key. One script does not:

```bash
cp .env.example .env          # paste a key into it; .env is gitignored
uv sync --extra nl
uv run python -m benchmarks.nl_eval --free-form -k rest-plain   # one call, a few cents
uv run python -m benchmarks.nl_eval                             # 18 calls, well under a dollar
```

That is the natural-language parse measured against text its author did not render
([`D-102`](docs/decisions.md)). It is a script rather than a test because it costs money and
because a result that depends on a model does not belong in a suite that must be reproducible.

## Repository map

```text
README.md                  this file — final-state
docs/finish.md             the finish declaration — what shipped, what did not
docs/archive/PLAN.md       tiers and sequencing (archived, not maintained)
roster_replan/
  model.py                 CP-SAT formulation
  checker.py               independent legality verification — imports no solver
  repair.py                greedy repair — solver-free, by contract
  ladder.py                exact → time-boxed → greedy → last known good
  explain.py               why a shift is short — answers from the checker, not the model
  prose.py                 findings in planner language, and the bound on what may be claimed
  core.py                  minimal infeasibility cores
  whatif.py                re-solve under a hypothetical change
  profile.py               profile document, contradictions, feasibility probe
  nl.py                    English → candidate profile — the only stage that needs a model
  compiled.py              per-tenant model cache
  service/                 async job API, contracts, and the tool surface
tests/
  test_ground_truth.py     exhaustive ground truth on micro-instances
  test_differential.py     model ⟺ checker
  test_properties.py       invariants
  test_golden.py           committed scenarios and objective values
  test_specs.py            the checkable half of "all specs true"
  mutation.py              deliberate defects, each naming the layer that must catch it
benchmarks/
  generator.py             seeded instance generator
  manifest.json            the committed set, as seeds and fingerprints
  milp.py                  the MILP formulation, for D-001
  nl_eval.py               the parse against free-form text — needs a key, so not in the suite
docs/
  specs/                   rules.md · model.md · replan.md · validation.md · config.md · service.md · capture.md
  decisions.md             what was chosen, what was rejected, why
  studies/                 analyses, nulls, rejected alternatives + index
  benchmarks.md            results and method
scenarios/horeca/          demo data — domain specificity lives here, not in the code
```
