# Development plan

> **End of life.**
> This file is disposable.
> It is archived to `docs/archive/` at the finish declaration (end of T3) and is not maintained afterwards.
> If a sentence here would still be true after the project ships, it belongs in a spec, not in this file.

**Owns:** sequencing, per-tier scope, gates.
**Does not own:** what anything *is* — that lives in `docs/specs/`.

---

## Rhythm

Three beats per component, not two:
**spec → implement → reconcile.**

Reconcile is the beat that gets skipped, because the code works and moving on feels fine.
Skip it enough times and the specs describe intent rather than code, which is the failure the whole approach exists to avoid.

**Definition of done: a component is not done until its spec matches its code.**
The reconcile beat is also where `decisions.md` entries get written.
Sometimes the implementation contradicts the spec.
More often the spec was simply written by someone who knew less about the domain than you do by the time you reach it — expect to modify, add and remove as that expertise arrives.
Either way something was learned, and a week later the why is gone.

Spec-first where the design is certain (the model, the checker, the job API).
Spec-after where it is exploratory (does warm-starting help, and by how much).
Documentation methodology applies from **T1 onward**; T0 is deliberately undocumented.

## Stopping rules

This project's characteristic failure mode is 90% documented and 30% built.
The tier gates are the defence, and they are built so that none of them can be passed by writing prose.

- **T0 has a hard one-week cap.**
  If nothing solves after a week, the model is wrong, not incomplete.
  Go back to `docs/specs/rules.md` before writing more code.
- **No tier starts before the previous tier's gate passes.**
  T5 in particular is forbidden until T4 items ship;
  LNS is the single most seductive way to lose three months here.
- **T3 is a legitimate finish.**
  T4 and T5 are upside, each independently shippable.

---

## T0 — walking skeleton `[1 week, hard cap]`

No API, no specs, no documentation. One file if it wants to be.

- 8 employees, one week, three shift types
- Three hard rules only: `R-COVER`, `R-AVAIL`, `R-REST-GAP`
- One absence injected → replan → print objective and the changed assignments

**Gate:** something solves, and the output is inspectable by eye.

## T1 — correctness spine

The credibility layer. Everything downstream is worthless without it.

- `docs/specs/rules.md` — the rule registry with stable IDs. **This is the real day-1 artifact.**
- `docs/specs/model.md`, `docs/specs/validation.md`
- Full rule set from the registry encoded in the model
- Independent checker, no solver import — enforced by an import-linter rule in CI
- Brute-force ground truth: ~20 committed micro-instances (N≤6, 3 days), in two stages —
  **(a)** enumerated hard-feasible set **equals** model feasible set, available as soon as the checker
  exists; **(b)** solver objective **equals** enumerated optimum, which needs the disruption metric and
  therefore lands with it. The gate as originally written depended on an artifact this tier scheduled
  after it.
- Differential harness: random rosters, **violation sets equal** — not `model_feasible ⟺
  checker_feasible`, which is vacuous once a coverage shortfall is representable — mismatch prints the
  rule ID
- Property tests: idempotence, seed determinism, monotonicity under relaxation, past shifts immutable
- Metamorphic tests: employee relabelling leaves the objective invariant
- Every test in the suite asserts zero checker violations on the returned solution — an invariant,
  not a separate test
- **Late T1: the disruption metric spec** (`docs/specs/replan.md`, D0–D4 defined, D2 shipped). T2
  cannot open without it, because golden objective values come from it.

**Gate:** the repo is trustworthy — a reviewer can see why the model is what the spec says it is.

## T2 — the thesis, measured

Where the project earns its headline.

- Seeded instance generator: tenant size, coverage tightness, skill scarcity, flexi/student mix,
  availability density, disruption event type, event day and time
- Committed, versioned benchmark instance set
- Four methods run over it: cold cost-objective re-solve · greedy nearest-eligible repair · cold
  disruption-objective solve · warm-started replan
- Both axes reported for all four: solve time (p50/p95) **and** disruption **and** cost
- **Disruption/cost Pareto frontier** — the money chart, goes in the README
- Disruption vs. time-budget curve (quality at 1s / 5s / 30s)
- Study: D0–D4 produce different rosters — five defensible definitions, one shipped, here is why
- Level-1 model studies with honest nulls: presolve, symmetry breaking, `regular` automaton,
  assignment vs. pattern encoding
- `docs/benchmarks.md` filled; every `[B-n]` placeholder in the README resolved
- Capture and replay (`docs/specs/capture.md`): vendor adapter with round-trip test, replay harness,
  incumbent comparison scored on observables.
  Built here because it reuses T2's scoring machinery.
  **Does not gate T2** — corpus population depends on an external authorization, and that
  conversation starts now because it is the long pole.

**Gate:** the headline claim is proven against baselines, on a stated instance distribution.

## T3 — production surface `[finish declaration lands here]`

- Async FastAPI job service: POST enqueue / GET poll / DELETE cancel
- Pydantic contracts at the boundary; versioned API
- Stateless solver — no database reads inside the service
- Seeded determinism end to end; every solve's input, profile version and seed persisted for replay
- Solver telemetry: solve-time distribution, terminating status, objective, gap, violation counts,
  fallback rate
- Fallback ladder: exact → time-boxed with reported gap → greedy → last known good
- Solver threads right-sized to container cores; per-tenant compiled-model cache
- Multi-tenant fairness: one large tenant cannot starve the small ones
- **Finish declaration**: all specs true, `PLAN.md` archived, repo name ratified, public/private
  fork executed

## T4 — differentiation `[each item independently shippable]`

Build in this order — ascending cost, descending certainty.

1. **Infeasibility explainer** — assumption literals → minimal core → rule IDs and coordinates →
   LLM prose. The LLM never identifies the conflict, only phrases a proven one.
2. **Tool surface** — `solve`, `replan`, `explain_infeasibility`, `what_if`, `validate_profile`
   exposed as callable tools over the async API.
3. **NL → tenant profile** — parse → structural validation → contradiction and subsumption check →
   feasibility probe on a sample week → save or reject. Round-trip eval: profile → English →
   profile must be identity. Deterministic config editing works fully without any LLM.

Each gets its own mini finish declaration: spec true, tests green, README section written.

## T5 — stretch, not before T4 ships

- LNS: destroy-and-repair with an exact CP repair over small neighbourhoods
- Generation mode from demand (the cold-start case, formally)
- Learned warm starts — and file the null if it does not beat the previous solution as a hint
- Fairness objectives beyond disruption concentration (rolling balance of unpopular shifts)

---

## Open items to ratify before T0

1. Repo name — revisit at the finish declaration, not now.
2. Public/private fork. Recommended default: **public on completion in both branches**, private
   during development. The project is general and synthetic by construction, so "would I be fine if
   this went public tomorrow?" is also the cleanest IP-hygiene rule available.
3. Initial spec file list (the outline hypothesis) — see `docs/specs/`.
