# roster-replan-optimizer

[![CI](https://github.com/MoFirouzT/roster-replan-optimizer/actions/workflows/ci.yml/badge.svg)](https://github.com/MoFirouzT/roster-replan-optimizer/actions/workflows/ci.yml)

**Minimum-disruption shift-roster replanning under labour constraints.**

Someone calls in sick at 09:00 on Saturday.
The conventional answer is to re-solve the week from scratch, which returns a roster that is optimal, legal, and heavily reshuffled;
people whose shifts were never in question are moved so the solver can shave a marginal cost.

This service answers it differently:
**reproduce the roster with minimum disruption to everyone else.**
Past shifts are pinned, and published shifts are penalised for changing; that penalty is what produces the low-disruption result.
The solve is also warm-started from the roster it is repairing, purely for speed.
The benchmarks measure the two effects separately and confirm the split.

> Generation is not a separate feature.
> It is the cold-start case of replanning; a replan from an empty roster.

---

## What it does

- **Replan:**
  repair a roster around absences, demand changes and late availability withdrawals, minimising weighted deviation from what people were already told.
  With no incumbent supplied, the same solve fills a planner's open shifts from scratch; this is generation, not a second feature.
- **Verify every roster against the rules:**
  every returned solution is re-checked against every rule by a plain function with no solver involved.
  Solutions that fail the checker are never returned.
- **Explain a short shift:**
  name the rule that blocked every person who could have filled it, in planner language:
  *6 of the 12 staff do not hold a skill the shift requires; 5 would not get the minimum rest*.
  This is the common case: with a soft coverage floor a shift comes back **priced** rather than refused.
- **Explain infeasibility:**
  in the rare case where no legal roster exists, return the *minimal* set of blocking rules with the day, shift and employee involved.
- **Answer a hypothetical:**
  *what if I hire one more flexi-jobber?* — re-solve under the change and report the difference.
  Unlawful hypotheticals are refused rather than answered.
- **Validate a policy before it can produce a roster:**
  structural checks, contradictions between a tenant's own rules, rules that cannot bind, and a feasibility probe.
- **Configure in natural language:**
  describe a tenant's policy in plain English;
  the parse emits a typed profile, which the validation bullet above then accepts or rejects.
  The model is confined by a **narrow schema rather than by instruction**:
  it has nowhere to write an objective weight or to switch on a rule the solver does not enforce.

> Belgian labour law is encoded as **data, not code**:
> rest gaps, weekly hour ceilings, flexi-job eligibility, same-day Dimona filing, student quotas, horeca minimum shift length.
> Rules carry stable IDs, for example `R-REST-GAP` for the minimum-rest rule, used identically in the specs, the model, the checker, the violation objects and the explainer.
> Full registry: [`docs/specs/rules.md`](docs/specs/rules.md).

---

## Reading guide

**Ten minutes, in reading order.** [`docs/quickstart.md`](docs/quickstart.md) for a demo run and what
it prints, then [`benchmarks.md`](docs/benchmarks.md) for what was measured and against what,
[`studies/README.md`](docs/studies/README.md) for the eight levers and the five that lost,
[`specs/validation.md`](docs/specs/validation.md) for how a legality claim is made true rather than
assumed, [`specs/rules.md`](docs/specs/rules.md) for the full rule registry, and
[`finish.md`](docs/finish.md) for what did not ship.

**If you only read one thing, make it a place the project was wrong.** The optimum was
[degenerate](docs/decisions.md) and nobody noticed until a CI runner disagreed with a laptop; the
[horizon rejection](docs/studies/horizon.md) in the spec was upheld on evidence that contradicted
both reasons it gave; and the [mutation harness](docs/decisions.md) reported `clean` three times
while a defect sat in the working tree.

---

## Results

**The disruption metric.** On the 72 of 84 cases where every shift could still be covered before the
disruption hit, swapping a cost objective for a disruption objective, against an otherwise identical
cold re-solve, cuts the disruption score (a weighted count of changed shifts) from 307 to 65. The
average number of people whose shifts moved falls from 12.4 to 2.4. Full definition of the score and
the method behind these numbers: [`docs/specs/replan.md`](docs/specs/replan.md) and
[`docs/benchmarks.md`](docs/benchmarks.md).

See it on one case (this is one scenario, not the 84-case set below; full reproduction is in
[`docs/quickstart.md`](docs/quickstart.md)):

```bash
uv sync
uv run python -m roster_replan.demo scenarios/saturday_sick_call.json --weekday-of-day-zero 0
```

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

The performance work behind these numbers, including the five levers that did not pay off, is indexed
in [`docs/studies/README.md`](docs/studies/README.md).

---

## Correctness

The model and the checker are two independent implementations of the same specification.
They share no rule logic — no predicate, no threshold — enforced in CI, and the differential harness is how we know which one is wrong.
Solver objectives are held against exhaustively enumerated optima on committed micro-instances, so the correctness claim rests on ground truth rather than on the solver agreeing with itself.

The reproducibility claim carried a silent bug of its own: the optimum was degenerate, and which
roster came back was decided by the solver binary rather than the specification, without any test
noticing. That finding and its fix are indexed as a study: [`docs/studies/README.md`](docs/studies/README.md) (`D-119`, `D-121`).

Test layers, invariants and the harness design: [`docs/specs/validation.md`](docs/specs/validation.md).

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
  Every solve's input, profile version and seed are persisted by the caller, so any roster produced in production can be reproduced offline — **on any machine, not just the one that produced it**.
  That is a repaired claim rather than an assumed one: the optimal value is pinned and a canonical criterion picks one point on the optimal face ([`D-119`](docs/decisions.md)), and CI proves it on a different ortools build from the one every committed artifact was recorded with ([`D-121`](docs/decisions.md)).
- **Async by construction.**
  Solves take real time;
  synchronous HTTP breaks on timeouts, retry storms and the absence of cancellation.
- **The LLM never sits in the solve path.**
  It produces only artifacts a deterministic layer can reject:
  candidate configs (validated, then feasibility-probed) and prose renderings of conflicts
  the solver already proved.
- **Policy is a document, not code.**
  A tenant's rules live in a profile from day one. Across thousands of small tenants the bottleneck
  is configuration work, not solve time; the one large instance this project tried tells the
  opposite story ([`foreign-incumbent.md`](docs/studies/foreign-incumbent.md), ~8M variables, 527 s
  to build).
- **Fallback ladder**:
  exact → time-boxed with reported gap → greedy repair → last known good.
  The service never returns nothing.

---

## Repository map

```text
README.md                   this file
docs/finish.md              the finish declaration — what shipped, what did not
docs/archive/PLAN.md        tiers and sequencing (archived, not maintained)
roster_replan/
  model.py                  CP-SAT formulation
  checker.py                independent legality verification — imports no solver
  repair.py                 greedy repair — solver-free, by contract
  ladder.py                 exact → time-boxed → greedy → last known good
  explain.py                why a shift is short — answers from the checker, not the model
  prose.py                  findings in planner language, and the bound on what may be claimed
  core.py                   minimal infeasibility cores
  whatif.py                 re-solve under a hypothetical change
  profile.py                profile document, contradictions, feasibility probe
  nl.py                     English → candidate profile — the only stage that needs a model
  compiled.py               per-tenant model cache
  service/                  async job API, contracts, and the tool surface
tests/
  test_ground_truth.py      exhaustive ground truth on micro-instances
  test_differential.py      model ⟺ checker
  test_properties.py        invariants
  test_golden.py            committed scenarios and objective values
  test_specs.py             the checkable half of "all specs true"
  mutation.py               deliberate defects, each naming the layer that must catch it
benchmarks/
  generator.py              seeded instance generator
  manifest.json             the committed set, as seeds and fingerprints
  milp.py                   the MILP formulation, for D-001
  nl_eval.py                the parse against free-form text — needs a key, so not in the suite
docs/
  specs/                    rules.md · model.md · replan.md · validation.md · config.md · service.md · capture.md
  decisions.md              what was chosen, what was rejected, why
  preferences.md            what employees and employers want past one week — a survey, nothing implemented
  studies/                  analyses, nulls, rejected alternatives + index
  benchmarks.md             results and method
  quickstart.md             demo run and what it prints
  development.md            suite commands, the one script that costs money
scenarios/                  demo data — domain specificity lives here, not in the code
```

---

## Deliberately out of scope

Authentication, persistence, a user interface, and demand forecasting.
All data committed to this repository is synthetic.
The forecast → optimise interface is documented in [`docs/specs/model.md`](docs/specs/model.md), not implemented.

---

MIT licensed. See [`LICENSE`](LICENSE).
