# roster-replan-optimizer

**Minimum-disruption shift-roster replanning under labour constraints.**

Someone calls in sick at 09:00 on Saturday.
The conventional answer is to re-solve the week from scratch, which returns a roster that is optimal, legal, and unrecognisable;
people whose shifts were never in question are moved so the solver can shave a marginal cost.

This service answers it differently:
**reproduce the roster with minimum disruption to everyone else.**
Past shifts are pinned, published shifts are penalised for changing, and the solve is warm-started from the roster it is repairing.

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

Measured on `benchmarks/instances/` (seeded generator, `[N-INSTANCES]` instances across
`[N-CLASSES]` scenario classes, 8–25 employees, one-week horizon).
Full method in [`docs/benchmarks.md`](docs/benchmarks.md).

| Method | p50 solve | p95 solve | Disruption (D2) | Cost delta |
| --- | --- | --- | --- | --- |
| Cold re-solve, cost objective | `[B-1]` | `[B-2]` | `[B-3]` | baseline |
| Greedy nearest-eligible repair | `[B-4]` | `[B-5]` | `[B-6]` | `[B-7]` |
| Cold solve, disruption objective | `[B-8]` | `[B-9]` | `[B-10]` | `[B-11]` |
| **Warm-started replan (this)** | `[B-12]` | `[B-13]` | `[B-14]` | `[B-15]` |

The trade-off is a choice, not a constant — see the disruption/cost frontier in
[`docs/benchmarks.md`](docs/benchmarks.md). Absorbing a Saturday sick call costs either a few more
euros or a few more disrupted people, and the planner picks the point.

`[PLACEHOLDER — every [B-n] is filled at T2. If any remain at the finish declaration, the project
is not finished.]`

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

Levers, in the order they paid off:

- domain presolve (eliminating impossible employee/shift pairs before the solver sees them)
- symmetry breaking over interchangeable employees
- the `regular` automaton constraint for legal shift sequences
- warm starts from the previous solution
- per-tenant compiled-model caching, because at these sizes model *building* can cost more than solving.

Details and the studies behind each, including the ones that produced no measurable effect: [`docs/studies/README.md`](docs/studies/README.md).

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
