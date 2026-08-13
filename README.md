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
- **Explain infeasibility:**
  when no legal roster exists, return the *minimal* set of blocking rules with the day, shift and employee involved, in planner language.
- **Configure in natural language:**
  describe a tenant's scheduling policy in plain Dutch or English;
  the system emits a typed profile, validates it structurally and semantically, and probes it for feasibility **before** it is saved.

Belgian labour law is encoded as **data, not code**:
rest gaps, weekly hour ceilings, flexi-job eligibility, same-day Dimona filing, student quotas, horeca minimum shift length.
Rules carry stable IDs used identically in the specs, the model, the checker, the violation objects and the explainer.
Full registry: [`docs/specs/rules.md`](docs/specs/rules.md).

Per-tenant policy lives in a profile document from day one, because across thousands of small tenants the configuration work, not the solve time, is the thing that does not scale.

---

## Headline results

Measured on the committed set in `benchmarks/manifest.json` (seeded generator, 72 cases across
12 scenario classes, 8–25 employees, one-week horizon), 3 solver seeds each, single-threaded.
Full method, segmentation and caveats in [`docs/benchmarks.md`](docs/benchmarks.md).

Weeks that were fully staffable before the disruption — 62 of the 72 cases. Every method is scored on
the same D2 yardstick whatever it optimised; `changes` is assignments differing from the published
roster, `short` is positions left unstaffed.

| Method | p50 search | p95 search | Disruption (D2) | Changes | Short |
| --- | --- | --- | --- | --- | --- |
| Cold re-solve, cost objective | 3.35 ms | 10.4 ms | 322.8 | 13.09 | 0.16 |
| Greedy nearest-eligible repair | — | — | 56.5 | 2.02 | 0.27 |
| Cold solve, disruption objective | 3.30 ms | 10.8 ms | 66.1 | 2.35 | 0.16 |
| **Warm-started replan (this)** | 3.02 ms | 8.6 ms | 66.1 | 2.35 | 0.16 |

**The objective is what does the work**, not the warm start. Against a cold cost re-solve on identical
instances with identical coverage, the disruption objective cuts the score from 323 to 66 and the
number of people moved from 13.1 to 2.4. The warm start is worth about 9% of a 3 ms search — real,
paired on 201 of 216 runs, and small enough that the honest framing is the one above.

**Greedy is not the weak baseline it looks like.** It ties the optimal replan exactly on 64 of the 72
cases. Its lower average disruption is bought by leaving more shifts unstaffed, which is the trade
the shortfall weight exists to refuse. The optimiser earns its place on the 8 cases where the repair
needs a chain — move an uninvolved person so somebody else comes free — and on never being the one to
leave a shift uncovered.

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
| Per-tenant compiled-model caching | **The largest one**: building costs ~7 ms against ~3 ms of search |
| Warm starts from the previous solution | **9% of search time**, paired on 216 runs; invisible end to end |
| Symmetry breaking | **Null** — 3 interchangeable employees across 24 cases. Worth 20% where symmetry exists, so the null is about the distribution |
| `regular` automaton for shift sequences | **Rejected, 20% slower** — a one-week horizon leaves exactly one window to replace |
| `no_overlap` intervals for rest gaps | **Rejected** — trades search time for build time, and the sign of the total flips by instance |
| Pattern/column variables | **Rejected** — no proof of optimality in 30 s on a cold week, against ~20 ms |

Four of the seven textbook levers lost, and the one that mattered most was the least interesting:
at these sizes the model is built more slowly than it is solved. Three of the four failures share a
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
uv run python -m roster_replan.demo scenarios/horeca/saturday_sick_call.json
```

## Repository map

```text
README.md                  this file — final-state
PLAN.md                    tiers and sequencing (archived at the finish declaration)
roster_replan/
  model/                   CP-SAT formulation
  checker/                 independent legality verification — imports no solver
  explain/                 minimal-core extraction and rendering
  config/                  profile schema, validation, feasibility probe
  service/                 async job API
tests/
  brute_force/             exhaustive ground truth on micro-instances
  differential/            model ⟺ checker
  properties/              invariants
  golden/                  committed scenarios and objective values
benchmarks/
  generator/               seeded instance generator
  instances/               committed benchmark set
docs/
  specs/                   rules.md · model.md · replan.md · validation.md · config.md · service.md · capture.md
  decisions.md             what was chosen, what was rejected, why
  studies/                 analyses, nulls, rejected alternatives + index
  benchmarks.md            results and method
scenarios/horeca/          demo data — domain specificity lives here, not in the code
```
