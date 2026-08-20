# Service

> **Status: built.** `roster_replan/service/` — contracts, job queue, endpoints, telemetry, and the
> tool surface. Reconciled with the code; `[TODO]`s below are what is not built.

    uv run uvicorn roster_replan.service.app:app

## Pattern `[built]`

Async job queue. POST enqueue / GET poll / DELETE cancel.

| Route | Behaviour |
| --- | --- |
| `POST /v1/replans` | `202` and a job id, with `Location`. `422` and the defects if unlawful |
| `GET /v1/replans/{id}` | the job, and its answer once terminal. `404` if unknown |
| `DELETE /v1/replans/{id}` | cancel. Terminal jobs are returned unchanged |
| `GET /v1/health` | solver health, not HTTP health — see [Telemetry](#telemetry) |

**A rejected request still gets a job id** ([`D-090`](../decisions.md#d-090)). A payload Pydantic accepts and
`validation.py` refuses returns `422` *and* a readable job in state `rejected`, so the
caller's flow is the same either way — poll the id — and the defects sit at the URL a result
would have occupied.

Synchronous HTTP works only for sub-second solves; at 30s–5min it produces timeouts, retries that
re-trigger expensive solves, request pile-up, no progress feedback and no cancellation. Event-driven
suits continuous replanning but makes *"why did my roster change?"* hard to answer.

## Statelessness `[built]`

Payload in, payload out. **No database reads inside the solver service.** This is what makes solves
testable, replayable, and reproducible offline from a persisted input — debugging optimisation in
production is close to impossible without it.

`run_job` satisfies this literally: it takes a payload, returns a payload, and reads nothing.
Each job keeps its request, seed and profile version after completion, which is what
`PLAN.md`'s seeded-determinism-end-to-end requirement actually needs — a job that has
discarded its input cannot be replayed however good its telemetry is.

**The queue itself is in-process, and that is the tier's honest limit.** State lives in a
dict, so replicas do not share a queue and a restart loses it. The *solver* is stateless, so
swapping the store for Redis or SQS is a contained change and touches nothing below
`service/`. `[TODO]` an external store, when there is a second replica.

## Contracts `[built]`

Pydantic at the boundary. Versioned API contracts, so a model change never breaks a caller.

**The wire schema is a separate schema, not a serialisation of `domain.py`** ([`D-090`](../decisions.md#d-090)).
Reusing the domain dataclasses would be less code and would publish every internal field as
public API, making a rename a breaking change for every caller — precisely the coupling the
versioning exists to prevent.

Two validation layers, and they answer different questions. Pydantic answers *is this
well-formed*; `validation.validate_instance` answers *is this lawful* — a derogation with no
recorded basis, a shortfall weight that does not dominate. Folding the second into Pydantic
validators would hide domain knowledge inside a schema.

Two things JSON cannot carry are decided at this boundary. An unbounded notice band is
`null`, because `inf` is not valid JSON. A `Roster` is a list of triples, normalised in sort
order so two identical rosters serialise identically — a response body that depends on set
iteration order is not comparable between runs.

**The round trip is the identity, and is tested as one.** A wire format that cannot express
something the solver can would break the replay guarantee silently: the payload still
parses, it just describes a slightly different problem.

## Fallback ladder `[built — roster_replan/ladder.py]`

exact → time-boxed with the gap **reported, not hidden** → greedy repair → last known good.
Never return nothing.

| Rung | Promise | Reached when |
| --- | --- | --- |
| `exact` | proven optimal, gap 0 | the solve finished inside its budget |
| `time-boxed` | feasible, **gap reported** | the budget ran out with a solution in hand |
| `greedy` | legal, not optimal | the model had no solution to give |
| `incumbent` | what was published, violations named | greedy had nothing to repair from |

**`exact` and `time-boxed` are one solve, not two.** CP-SAT returns the best solution found
*and* the best proven bound when a time limit stops it, so re-solving with a smaller budget
to "try the fast rung first" would spend the budget twice to learn the same thing. Which rung
an answer came from is read off the outcome, not decided in advance.

**The ladder imports no web layer.** The intricate part stays small and testable; the
boundary stays boring. `ladder.py` knows nothing about HTTP, jobs or queues.

Three things about it are consequences rather than choices, and each is asserted by test:

- **The lower rungs are replan-only.** Greedy repairs an incumbent and last-known-good
  returns one, so "never return nothing" is a promise about *replanning*. The cold path
  cannot keep it.
- **A cold solve is never infeasible** — the empty roster satisfies every hard constraint,
  because the coverage floor is soft ([`D-018`](../decisions.md#d-018)). Impossible demand comes back priced, not
  refused, so the only way a cold solve fails is exhaustion.
- **The `incumbent` rung can return an illegal roster, deliberately.** After a disruption the
  published roster is usually already broken. It is returned with its violations named and
  marked as the floor rather than a repair.

**Every rung is reachable by construction**, because none of them is reachable by accident:
no instance in the committed set takes more than 15.4 ms, so `time-boxed`, `greedy` and
`incumbent` would otherwise ship untested. `tests/test_ladder.py` forces each one, and the
mutation harness carries a mutant per rung.

### A timeout is not an infeasibility ([`D-094`](../decisions.md#d-094))

The ladder's first version reported one as the other, because `solve` returned an empty
`list[Gate]` for both. See the record; the fix is a third return type, and the distinction
matters most to T4's explainer, which is specified to turn a core into prose.

<a id="telemetry"></a>
## Telemetry `[built — GET /v1/health]`

Web observability says nothing about solver health: latency and error rate stay green while the
optimiser quietly returns garbage. Required signals: solve-time distribution, terminating status
(optimal / feasible / infeasible / timeout), objective value, optimality gap, constraint-violation
count from the checker, fallback rate.

All of them are on `GET /v1/health`. A `200` from this API means a roster came back, not that
it was a good one — the fallback ladder guarantees an answer, so a service falling to its
greedy rung on every request looks perfect to any HTTP monitor. `rungs` and `fallback_rate`
are what would show it; `violations_returned` counts the worst case, a roster breaking a hard
rule returned with a `200`, and it is counted by the independent checker rather than by the
solver marking its own work.

Distributions are reported as p50/p95/max rather than means: a mean hides the tail, and the
tail is what a budget is set against. `[TODO]` pushing these to a metrics backend, which is a
deployment choice; the signals are what this project owes.

## Runtime

Solver workloads are not web workloads — CPU-bound, memory-hungry, bursty, long-running.
Autoscale on queue depth, not CPU.

**Threads against cores `[built]`.** Concurrency is chosen first and each solve gets an equal
share of what remains, so their product fits the box. CP-SAT with 8 workers in a 1-vCPU
container is *slower*, and over-subscription is not merely wasteful — the portfolio search
assumes the threads it was promised.

**Fairness `[built]`.** Per-tenant queues with a rotation, not one FIFO: a tenant with 500
queued jobs gets one slot per rotation, exactly like a tenant with one. Round-robin rather
than weighted ([`D-091`](../decisions.md#d-091)), because a per-tenant weight needs a priority nothing in this project
can currently justify.

**Solves run off the event loop `[built]`.** CP-SAT blocks, so a solve on the loop would
stall every other request in the process — including the polls asking how it is doing.

**Cancelling a running solve does not stop the CPU work.** The job is marked cancelled at
once and its result discarded, so the caller's contract holds, but the search runs to its
budget. Interrupting needs a solution callback wired through `model.solve`. `[TODO]`, and
stated because the misreading — that `DELETE` frees a core — only shows up under load.

**Per-tenant compiled-model cache `[built — and it does not help replanning]`.** The premise
here was right and the remedy was not ([`D-093`](../decisions.md#d-093)). Building does cost more than solving, but a
replan is triggered by a change to the model's own inputs — an absence changes which pairs
survive presolve, which changes the variables — so the cache **hits 0 of 144 replan solves**.
It ships enabled because a miss costs 0.6% of a build and a hit saves 170×, and because
`what_if`, replay and retries do repeat an instance. It is **thread-local**: `CpModel` is not
thread-safe, and a shared cache would hand one model to two concurrent solves.

The latency win that was actually available came from profiling rather than from caching:
memoising `Instance.window` removed 20% of build time ([`D-092`](../decisions.md#d-092)), which is larger than presolve
and larger than every level-1 lever in T2. See
[`studies/model-cache.md`](../studies/model-cache.md).

## Tool surface `[built — roster_replan/service/tools.py]`

`solve`, `replan`, `explain_infeasibility`, `what_if`, `validate_profile`, enumerable at
`GET /v1/tools` with schemas and invoked at `POST /v1/tools/{name}`.

Four are thin over machinery that already exists, and that is the design rather than a
shortcut: a tool surface whose tools each contain original logic is a second implementation
of the product, with its own bugs. `what_if` is the exception and the one `service.md`
singled out — a parameter sweep, and the question owners actually ask.

**Tool calls are synchronous, unlike `/replans`.** A tool call is exploratory: a planner or an
agent asking a question and waiting. An enqueued replan is production work with a budget and
a cancellation story. Both exist because they are different interactions.

Three properties hold across all five ([`D-012`](../decisions.md#d-012), [`D-013`](../decisions.md#d-013)):

- **Structured fields *and* prose, together.** A caller that distrusts the sentence reads the
  numbers; one that cannot parse the numbers reads the sentence. Prose alone would make a
  model's phrasing load-bearing.
- **Nothing decides anything.** `what_if` reports that a skilled hire fills a position and an
  unskilled one does not. Whether to hire is not a question this project has standing to
  answer, and a tool that answered it would launder a business decision through a solver.
- **All five are read-only.** `validate_profile` checks and reports; the save is the
  caller's. A tool an LLM can call should not be able to persist a tenant's policy.

**An unlawful hypothetical is refused, not answered** ([`D-098`](../decisions.md#d-098)). Relaxing a statutory
parameter without a recorded derogation basis is rejected by `validation.py` before any
solve, so `what_if` cannot reply *just shorten the rest gap* — the most dangerous output
available from a tool a planner might trust.

## Shortfall recommendations `[built — roster_replan/whatif.py:recommend]`

A shortfall says who was blocked and by which rule. `recommend()` answers the next question a
planner asks — *which single override would actually fill it, and what would that cost* — by
composing the explainer and `compare()`. It is a **library function, not a sixth tool**; the
reason is below.

**Input** is one `Shortfall` and the instance it came from. **Output** is a tuple of
`Recommendation`, each carrying the employee, the action in planner language, the
`disruption_delta` it was measured at, the `rule` it would relax and that rule's `provenance`.

### Which candidates are tested

Only people the explainer records as blocked by **exactly one** rule, and only where that rule
has a `Change` kind — `R-SKILL`, `R-MAX-DAILY`, `R-MAX-WEEKLY` today:

```
tested = { e ∈ shortfall.blocked : |rules(e)| = 1 ∧ rules(e) ⊆ _PROVENANCE }
```

One blocker is `by_employee()`'s own hint about who is cheapest to ask, and a person with two
blockers cannot be tested by relaxing one of them. **The hint is checked, not trusted**: each
candidate is re-solved and kept only if the shift actually closes. A rule count of one does not
mean the solver can use the person once the rest of the week is re-optimised around them.

At most `MAX_CANDIDATES` people are tested, five by default. Uncapped, the sweep is a solve per
blocked person for a list nobody reads far into ([`D-144`](../decisions.md#d-144)).

### Ranked within a provenance, never across one ([`D-144`](../decisions.md#d-144))

Operational asks first, then statutory, cheapest-first inside each group:

```
sort key = (provenance ≠ operational, disruption_delta, employee)
```

Disruption cannot order two asks of different kinds. Ignoring a skill requirement is a judgement
the planner already owns; asking somebody to work further into a budget a statute caps is a
different question at any price. A single flat list says otherwise by its shape — the top line
reads as the recommendation.

Nothing unlawful reaches the list: a cap above the absolute ceiling is refused by
`validate_instance` and `compare` returns that refusal, so the candidate is dropped before it can
be printed. **Lawful is not the same as equivalent**, which is what the grouping carries.

### Nothing is applied, and nothing is decided

Every candidate is a fresh, disposable instance. The incumbent and every employee's real record
are exactly as they were. *Ignoring* a rule for one solve is not the same as changing somebody's
record, and publishing an override is a caller's later act.

**Why this is not a tool.** The tool surface's standing rule is that nothing there ranks options
or decides. A ranked list of ways to override labour rules, handed to a model, is read as an
instruction however it is grouped — and the exclusions the list depends on are invisible to a
caller: a person blocked by `R-AVAIL` or `R-REST-GAP` never appears, and a rule with no `Change`
kind is silently untested. A planner reading the demo output has that context. If it is ever
exposed, the shape that survives the boundary is a **directed** query — the caller names the
employee and the rule, the tool prices that one override — not a ranking.

## Boundary discipline

Everything around the solver stays deliberately boring — endpoints, validation, queue handling,
error mapping — so a non-specialist can read and change it. The intricate part is small and heavily
tested.

**No language model is reachable from here.** `config.md` puts the parse outside the service, and
that is an import-linter contract rather than a convention ([`D-101`](../decisions.md#d-101)): `roster_replan.service` may
not import `roster_replan.nl` or `anthropic`. The SDK is an optional extra, so the service would
otherwise acquire a dependency that has to be installed before it can start — and the tool surface
would have a route whose availability depends on a key. Everything this service answers is derived,
and [`D-013`](../decisions.md#d-013) is what makes that worth stating twice.
