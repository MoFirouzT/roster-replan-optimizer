# roster-replan-optimizer

[![CI](https://github.com/MoFirouzT/roster-replan-optimizer/actions/workflows/ci.yml/badge.svg)](https://github.com/MoFirouzT/roster-replan-optimizer/actions/workflows/ci.yml)

**Minimum-disruption shift-roster replanning under labour constraints.**

Someone calls in sick at 09:00 on Saturday.
The conventional answer is to re-solve the week from scratch, which returns a roster that is optimal, legal, and heavily reshuffled;
people whose shifts were never in question are moved so the solver can shave a marginal cost.

This service answers it differently:
**reproduce the roster with minimum disruption to everyone else.**
Past shifts are pinned, and published shifts are penalised for changing.

Nothing comes back unexplained or unchecked.
Every roster is re-verified against every rule by a plain function with no solver involved, a short shift names the rule that blocked each person who could have filled it, and a policy written in plain English is accepted or rejected before it can produce a roster.

> Generation is not a separate feature.
> It is the cold-start case of replanning; a replan from an empty roster.

---

## The difference, on one week

![One week of a 12-person roster, drawn twice. A cold cost re-solve moves six assignments; the minimum-disruption replan moves two.](docs/saturday-sick-call.svg)

E05 calls in sick for Sunday evening. Both rosters are legal, both staff every shift, and both are optimal for the objective they were given.

The replan drops E05 and calls E04 in — the absence, and its replacement. The cold re-solve also moves **E01, E07 and E08**, three people whose shifts were never in question, because nothing in a cost objective prefers the roster they were already told about.

That is one case. Across 72 cases the means are **12.4 assignments moved against 2.4**.

```bash
uv sync
uv run python -m roster_replan.demo scenarios/saturday_sick_call.json
```

---

## Two doors

**[Using it](docs/guide/quickstart.md)** — run the demo, configure a tenant, call the API, read the rule registry, and find out what it guarantees and where it stops.

**[Working on it](docs/internals/design.md)** — why the system is shaped this way, then the formulation, the test layers, and the suite.

Both are indexed at [`docs/README.md`](docs/README.md).

---

## What it does

- **Replan** a roster around absences, demand changes and late availability withdrawals, minimising weighted deviation from what people were already told. With no incumbent, the same solve generates from scratch.
- **Verify** every returned roster against every rule, by a second independent implementation that imports no solver. That matters most on the two fallback rungs no solver stands behind.
- **Explain a short shift** — name the rule that blocked every person who could have filled it, in planner language, and say which single override would close it, confirmed by re-solving rather than assumed.
- **Explain infeasibility** — return the minimal set of blocking rules with the day, shift and employee involved.
- **Answer a hypothetical** — *what if I hire one more flexi-jobber?* Unlawful hypotheticals are refused rather than answered.
- **Validate a policy** before it can produce a roster, including contradictions between a tenant's own rules and rules that cannot bind.
- **Configure in natural language** — the model is confined by a narrow schema rather than by instruction: it has nowhere to write an objective weight or to switch on a rule the solver does not enforce.

> Belgian labour law is encoded as **data, not code**: rest gaps, weekly hour ceilings, flexi-job eligibility, same-day Dimona filing, student quotas, horeca minimum shift length.
> Every rule carries a stable ID — `R-REST-GAP` for minimum rest — used identically in the registry, the model, the checker, the violation objects and the explainer.
> Full registry: [`docs/guide/rules.md`](docs/guide/rules.md).

---

## Results

84 cases across 14 scenario classes, 8–25 employees, one-week horizon, 3 solver seeds, single-threaded. Weeks fully staffable before the disruption — 72 of the 84. Every method is scored on the same D2 yardstick whatever it optimised.

| Method | p50 search | p95 search | Disruption (D2) | Changes | Short |
| --- | --- | --- | --- | --- | --- |
| Cold re-solve, cost objective | 3.61 ms | 10.5 ms | 307.3 | 12.36 | 0.15 |
| Greedy nearest-eligible repair | — | — | 53.6 | 1.94 | 0.31 |
| Cold solve, disruption objective | 3.58 ms | 10.7 ms | 65.3 | 2.40 | 0.15 |
| **Warm-started replan (this)** | 3.31 ms | 8.6 ms | 65.3 | 2.40 | 0.15 |

**The objective is what does the work**, not the warm start — which is worth about 9% of a 3 ms search, paired on 662 of 756 runs, and small enough that this is the honest framing.

**Greedy is not the weak baseline it looks like.** It ties the optimal replan exactly on 71 of 84 cases, and its lower average disruption is bought by leaving more shifts unstaffed — the trade the shortfall weight exists to refuse. The optimiser earns its place on the 13 cases where the repair needs a chain, and on never being the one to leave a shift uncovered.

Caveats, segmentation and what this set does *not* show: [`docs/guide/limits.md`](docs/guide/limits.md).

---

## Correctness

The model and the checker are two independent implementations of the same registry. They share no rule logic — no predicate, no threshold — enforced in CI, and a differential harness is how we know which one is wrong. Solver objectives are held against exhaustively enumerated optima on committed micro-instances, so the correctness claim rests on ground truth rather than on the solver agreeing with itself.

Every one of those layers is itself checked by deliberately breaking the code and confirming the layer that should object does. That has found four blind spots behind fully green suites.

[`docs/internals/testing.md`](docs/internals/testing.md).

**If you only read one thing, make it a place the project was wrong.** The optimum was [degenerate](docs/archive/decisions.md#d-119) and nobody noticed until a CI runner disagreed with a laptop; the [horizon rejection](docs/archive/studies/horizon.md) was upheld on evidence that contradicted both reasons the spec gave for it; and the [mutation harness](docs/archive/decisions.md#d-139) reported `clean` three times while a defect sat in the working tree.

Every design choice that could have gone the other way is a [numbered decision](docs/archive/decisions.md), and the ones that turned on evidence are written up as [studies](docs/archive/studies/README.md) — including the nulls.

---

## Deliberately out of scope

Authentication, persistence, a user interface, and demand forecasting.
All data committed to this repository is synthetic.

---

MIT licensed. See [`LICENSE`](LICENSE).
