# Documentation

Four ways in, depending on how much time you have and what you came for.
Every document below is one of four kinds: a **spec** (present tense, what the system is), a **study** (a question and what measuring it answered), the **decision records** (what was chosen and why), or a **status** page.

## Five minutes

1. [`quickstart.md`](quickstart.md) — one scenario end to end, and what it prints.
2. [`benchmarks.md`](benchmarks.md#results) — the results table, four methods on one yardstick.

## The model, forty-five minutes

1. [`formulation.md`](formulation.md) — sets, variables, objective, constraint families, on one page.
2. [`specs/replan.md`](specs/replan.md) — what disruption is, the five definitions, and what they trade against coverage and cost.
3. [`specs/rules.md`](specs/rules.md) — the rule registry; the ID column links to each rule.
4. [`benchmarks.md`](benchmarks.md) — the instance distribution, the baselines, and what the set does *not* show.
5. Two studies worth the detour: [`studies/horizon.md`](studies/horizon.md), where a rejection was upheld on evidence that contradicted both reasons the spec gave for it, and [`studies/penalty-search.md`](studies/penalty-search.md), where the easy instance distribution would have produced the wrong answer.

## Reading the code

Module docstrings carry the argument for each module's shape; each names the spec it implements.

| Module | Spec | What it is |
| --- | --- | --- |
| [`model.py`](../roster_replan/model.py) | [`specs/model.md`](specs/model.md), [`specs/rules.md`](specs/rules.md) | the CP-SAT formulation — one reading of the registry |
| [`checker.py`](../roster_replan/checker.py) | [`specs/validation.md`](specs/validation.md) | the independent second reading; imports no solver |
| [`disruption.py`](../roster_replan/disruption.py) · [`scoring.py`](../roster_replan/scoring.py) | [`specs/replan.md`](specs/replan.md) | the objective, and its independent evaluation |
| [`repair.py`](../roster_replan/repair.py) | [`benchmarks.md`](benchmarks.md#methods-compared) | the greedy baseline, solver-free under an import contract |
| [`ladder.py`](../roster_replan/ladder.py) | [`specs/service.md`](specs/service.md) | exact → time-boxed → greedy → last known good |
| [`explain.py`](../roster_replan/explain.py) · [`core.py`](../roster_replan/core.py) · [`prose.py`](../roster_replan/prose.py) | [`specs/rules.md`](specs/rules.md) | why a shift is short, minimal cores, planner language |
| [`profile.py`](../roster_replan/profile.py) · [`nl.py`](../roster_replan/nl.py) | [`specs/config.md`](specs/config.md) | the tenant profile, and the only stage that needs a model |
| [`service/`](../roster_replan/service) | [`specs/service.md`](specs/service.md) | async job API, contracts, tool surface |

Then [`development.md`](development.md) for the suite, the import contracts, and the one script that costs money.

## Archaeology

- [`decisions.md`](decisions.md) — 143 records. Enter through its [lookup table](decisions.md#lookup), or through [by theme](decisions.md#by-theme) if you want the records that make one argument together.
- [`studies/README.md`](studies/README.md) — every analysis, **including the ones that found no effect**.
- [`finish.md`](finish.md) — what shipped, what did not, and what was got wrong.

## How it fits together

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
  That is a repaired claim rather than an assumed one: the optimal value is pinned and a canonical criterion picks one point on the optimal face ([`D-119`](decisions.md#d-119)), and CI proves it on a different ortools build from the one every committed artifact was recorded with ([`D-121`](decisions.md#d-121)).
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
  opposite story ([`foreign-incumbent.md`](studies/foreign-incumbent.md), ~8M variables, 527 s
  to build).
- **Fallback ladder**:
  exact → time-boxed with reported gap → greedy repair → last known good.
  The service never returns nothing.

---

## Repository map

The modules are in [Reading the code](#reading-the-code) above; this is everything else.

```text
roster_replan/service/   async job API, contracts, and the tool surface
benchmarks/
  generator.py           seeded instance generator
  manifest.json          the committed set, as seeds and fingerprints
  milp.py                the MILP formulation, for D-001
  anneal.py              the penalty-search rival, solver-free by contract
  nl_eval.py             the parse against free-form text — needs a key, so not in the suite
tests/
  test_ground_truth.py   exhaustive ground truth on micro-instances
  test_differential.py   model ⟺ checker
  test_properties.py     invariants
  test_golden.py         committed scenarios and objective values
  test_specs.py          the checkable half of "all specs true"
  mutation.py            deliberate defects, each naming the layer that must catch it
scenarios/               demo data — domain specificity lives here, not in the code
```

---

## Every document

**Specs** — present tense, and reconciled against the code rather than describing intent.

| Document | Status | What it owns |
| --- | --- | --- |
| [`specs/rules.md`](specs/rules.md) | shipped, 5 rules outline only | the rule registry: predicate, parameters, provenance, failure message |
| [`specs/model.md`](specs/model.md) | shipped | index sets, the input contract, presolve, symmetry |
| [`specs/replan.md`](specs/replan.md) | D2 shipped, D0–D4 defined | the objective, and what it trades against |
| [`specs/validation.md`](specs/validation.md) | shipped | input validation, the independent checker, the test layers |
| [`specs/service.md`](specs/service.md) | shipped | the async pattern, contracts, fallback ladder, telemetry |
| [`specs/config.md`](specs/config.md) | shipped | the profile document and the four stages of building one |
| [`specs/capture.md`](specs/capture.md) | **specified, not built** | capture and replay, and the bar fixed before the first replay |

**Everything else.**

| Document | Status | What it is |
| --- | --- | --- |
| [`formulation.md`](formulation.md) | derived reading | the model on one page |
| [`quickstart.md`](quickstart.md) | — | the demo run, and what it prints |
| [`benchmarks.md`](benchmarks.md) | measured | the committed set, the four methods, the results and their caveats |
| [`studies/`](studies/README.md) | measured | sixteen analyses, five of them nulls or rejections |
| [`decisions.md`](decisions.md) | — | what was chosen, what was rejected, why |
| [`finish.md`](finish.md) | status | the finish declaration, and everything since |
| [`preferences.md`](preferences.md) | **survey — nothing implemented** | what employees and employers want past one week |
| [`development.md`](development.md) | — | running the suite, and contributing |
| [`archive/PLAN.md`](archive/PLAN.md) | **archived, not maintained** | the original tiers and sequencing |
