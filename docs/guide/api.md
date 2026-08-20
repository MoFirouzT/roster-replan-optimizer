# API

```bash
uv run uvicorn roster_replan.service.app:app
```

Solves take real time, so replanning is an **async job**: enqueue, poll, cancel. Tool calls are synchronous, because a tool call is somebody asking a question and waiting.

| Route | Behaviour |
| --- | --- |
| `POST /v1/replans` | `202`, a job id, and a `Location`. `422` and the defects if the request is unlawful |
| `GET /v1/replans/{id}` | The job, and its answer once terminal. `404` if unknown |
| `DELETE /v1/replans/{id}` | Cancel. Terminal jobs come back unchanged |
| `GET /v1/tools` | The five tools, with their schemas |
| `POST /v1/tools/{name}` | Invoke one, synchronously |
| `GET /v1/health` | Solver health — see [Health](#health) |

**A rejected request still gets a job id.** A payload the schema accepts and validation refuses returns `422` *and* a readable job in state `rejected`, so your flow is the same either way — poll the id — and the defects sit at the URL a result would have occupied.

**Cancelling does not stop the CPU work.** The job is marked cancelled at once and its result discarded, so your contract holds, but the search runs to its budget. Interrupting a running solve is not built.

---

## The request

`scenarios/saturday_sick_call.json` is a complete worked example. The wire schema is versioned and separate from the internal one, so a model change never breaks you.

### Time is hours from the horizon start

Every time quantity — shift bounds, `now`, `published_through`, interval endpoints — is a float counting hours from the start of the horizon. Values before the horizon are negative.

Calendar timestamps belong in your system, not this one. **This domain has no calendar:** a week is a position in the horizon and never a Monday.

### What you send

| Field | Carries |
| --- | --- |
| `days`, `shift_types`, `open_shifts` | The week and the demand. An `open_shift` is a `(day, shift)` pair with `required`, `required_skills`, `skill_mix` |
| `employees` | Name, contract, skills, absences, unavailability, eligibility gates, `hourly_rate`, and the caller-computed quantities below |
| `params` | Every rule threshold, explicitly. Plus `derogation_basis` where a statutory parameter is relaxed |
| `now`, `incumbent`, `published_through` | The replan inputs. Omit all three for a cold solve |
| `disruption` | Objective parameters — see [`limits.md`](limits.md#choosing-a-disruption-metric) |

A slot counts as published iff `start(d, s) < published_through`. One number, matching the dominant real pattern — *the schedule is out through Sunday the 14th*. A **wave-published** roster, with some shifts in the same week announced and others held back, is not representable.

A `shift_type` carries `span_hours` **and** `break_hours`; `work_hours` is derived. Both are needed because the rules disagree about which they mean — the minimum-shift rule reads gross span, the hour ceilings read net work.

An unbounded notice band is `null`, because `inf` is not valid JSON. A roster is a list of triples, normalised in sort order, so two identical rosters serialise identically.

### Four quantities you compute, and this service never recomputes

A one-week payload cannot see the history that constrains its own first day. Someone who worked the six days before Monday, or who finished a night shift at 07:00 on Monday, is constrained on Monday by a past the horizon does not contain.

| Field | Unit | Consumed by |
| --- | --- | --- |
| `max_hours_this_week[e]` | hours | `R-MAX-WEEKLY` |
| `consecutive_days_worked_before_horizon[e]` | days | `R-CONSEC-DAYS` |
| `last_shift_end_before_horizon[e]` | hours, negative | `R-REST-GAP`, `R-WEEKLY-REST` |
| `unpopular_shifts_before_horizon[e]` | count | the fairness term |

`max_hours_this_week[e]` is the one that matters most: it is the rolling reference period — a quarter, or a year — resolved by you into a single number, which is what lets the solve horizon stay at one week. See [`rules.md`](rules.md#the-reference-period-and-why-r-max-weekly-is-a-budget).

**The checker verifies against the values you supplied and never derives its own.** A checker that invents a budget from a reference period it cannot see is testing you, not the roster.

### Omitted is never defaulted

`max_hours_this_week`, `max_daily_hours`, `last_shift_end_before_horizon`, `flexi_eligible` and `dimona_ok` are optional in the container and **mandatory in practice**. Leave one out where a rule needs it and the request is rejected — nothing is substituted.

The failure this avoids is specific: an empty `flexi_eligible` would *deny* eligibility where you merely forgot to say, which is a different answer wearing the same shape. Neither it nor a defaulted weekly budget is detectable downstream, because both produce a perfectly plausible roster.

### Four fields that switch a rule on

Absent here means you are not asking for the rule, which is ordinary rather than a defect.

| Field | Consumed by | Absent means |
| --- | --- | --- |
| `max_hours_this_period[e]` | `R-MAX-PERIOD` | nothing beyond the weekly ceiling |
| `max_weekends[e]` | `R-MAX-WEEKENDS` | no weekend budget |
| `min_consecutive_days_off[e]` | `R-MIN-DAYS-OFF` | no minimum; `1` is the same as absent |
| `params.weekend_days` | `R-MAX-WEEKENDS` | no weekend is defined, so the rule is off |

---

## What gets rejected before any solve

`validation.validate_instance` runs at profile load and at the head of every solve. A non-empty result rejects the request outright — it never degrades into a best-effort solve, because a malformed request has no meaningful optimum.

The dividing question is **whether a different roster could fix it**. If no roster could, it is a request defect:

| Check | Why it is your problem, not the solver's |
| --- | --- |
| Every shift type meets the minimum work period (`R-MIN-SHIFT`) | No reachable roster can violate it; your shift catalogue either does or does not |
| `max_hours_this_week[e]` within the absolute weekly ceiling | A too-large budget is a bad payload. Reporting it as a rule violation blames the solver for your arithmetic |
| `max_daily_hours[e]` within the lawful derogation ladder | The ceiling is a property of the contract, not of the assignment |
| The horizon is a week or less, or a whole number of weeks | A horizon ending part-way through a week leaves a stub that weekly rest cannot fit inside |
| A derogated parameter carries a non-empty `derogation_basis` | A legality claim with no source is exactly what the registry exists to prevent |
| A legal `skill_mix` entry carries a provenance string | As above, per entry |
| `now` and `incumbent` both present, or both absent | A replan missing either is malformed, not defaulted |
| `flexi_eligible` / `dimona_ok` present for every flexi employee | Absence must never default to `true` — that invents an eligibility the NSSO did not grant |
| Every rule parameter supplied explicitly | No rule threshold is ever defaulted in shared code |
| Horizon begins at or after `now` on a cold solve | Otherwise there are past shifts and no incumbent to pin them to |
| `shortfall_weight` dominates what one unstaffed shift can save | A weight scale letting the optimiser buy stability by understaffing is an ordering error, not a preference |

`InputDefect` carries the offending field path, the observed value, and the constraint it broke. It is a **distinct type** from `Violation` and the two are never mixed in one list: you fix a defect, a planner reads a violation.

---

## The answer

**Nothing comes back unchecked.** Every roster this service returns has been re-verified against every rule by a plain function that imports no solver. That matters most on the two rungs no solver stands behind.

### The fallback ladder

exact → time-boxed with the gap **reported, not hidden** → greedy repair → last known good. The service never returns nothing.

| Rung | Promise | Reached when |
| --- | --- | --- |
| `exact` | proven optimal, gap 0 | the solve finished inside its budget |
| `time-boxed` | feasible, **gap reported** | the budget ran out with a solution in hand |
| `greedy` | legal, not optimal | the model had no solution to give |
| `incumbent` | what was published, violations named | greedy had nothing to repair from |

Three things to know about it:

- **The lower two rungs are replan-only.** Greedy repairs an incumbent and last-known-good returns one, so *never return nothing* is a promise about replanning. A cold solve cannot keep it.
- **A cold solve is never infeasible.** The empty roster satisfies every hard constraint, because the coverage floor is priced rather than required. Impossible demand comes back short, not refused. The only way a cold solve fails is exhaustion.
- **The `incumbent` rung can return an illegal roster, deliberately.** After a disruption the published roster is usually already broken. It comes back with its violations named, marked as the floor rather than as a repair.

**A timeout and an infeasibility are different answers, and the response says which.**

### When a shift comes back short

Coverage has a **priced floor**, not a hard requirement, so a shortfall is a common and honest outcome rather than an error. The response names every person who could have filled the shift and the rule that blocked each one.

`whatif.recommend()` answers the next question — *which single override would actually fill it, and what would that cost*.

**What comes back.** A tuple of `Recommendation`, each carrying the employee, the action in planner language, the `disruption_delta` it was measured at, the `rule` it would relax and that rule's `provenance`.

**Who gets tested.** Only people blocked by **exactly one** rule, and only where that rule has an override kind: `R-SKILL`, `R-MAX-DAILY` and `R-MAX-WEEKLY` today. At most `MAX_CANDIDATES` people, five by default — uncapped, the sweep is a solve per blocked person for a list nobody reads far into.

**The hint is checked, not trusted.** One blocker is a hint about who is cheapest to ask, not a guarantee that overriding it works — so each candidate is re-solved on a disposable copy of the instance and kept only if the shift actually closes.

**Ranked within a provenance, never across one.** Operational asks first, then statutory, cheapest-first inside each group. Disruption cannot order two asks of different kinds: ignoring a skill requirement is a judgement you already own, while asking somebody to work further into a budget a statute caps is a different question at any price. A single flat list would say otherwise by its shape, because the top line reads as the recommendation.

Nothing unlawful reaches the list — a cap above the absolute ceiling is refused before the candidate can be printed. **Lawful is not the same as equivalent**, which is what the grouping carries.

**Nothing is applied.** Every candidate is a fresh, disposable instance. Your incumbent and every employee's real record are exactly as they were. *Ignoring* a rule for one solve is not the same as changing somebody's record, and publishing an override is your later act.

This is a library function rather than a sixth tool, on purpose. A ranked list of ways to override labour rules, handed to a model, reads as an instruction however it is grouped.

---

## Tools

`solve`, `replan`, `explain_infeasibility`, `what_if`, `validate_profile` — enumerable at `GET /v1/tools`, invoked at `POST /v1/tools/{name}`.

Three properties hold across all five:

- **Structured fields *and* prose, together.** If you distrust the sentence, read the numbers; if you cannot parse the numbers, read the sentence. Prose alone would make a model's phrasing load-bearing.
- **Nothing decides anything.** `what_if` reports that a skilled hire fills a position and an unskilled one does not. Whether to hire is not a question this service has standing to answer.
- **All five are read-only.** `validate_profile` checks and reports; the save is yours. A tool a model can call should not be able to persist your policy.

**An unlawful hypothetical is refused, not answered.** Relaxing a statutory parameter with no recorded derogation basis is rejected before any solve, so `what_if` cannot reply *just shorten the rest gap* — the most dangerous output available from a tool a planner might trust.

**No language model is reachable from this service.** That is an import-linter contract, not a convention: `roster_replan.service` may not import `roster_replan.nl` or `anthropic`. Everything the service answers is derived.

---

<a id="health"></a>
## Health

`GET /v1/health` reports solver health, which is not the same as HTTP health. **A `200` from this API means a roster came back, not that it was a good one** — the ladder guarantees an answer, so a service falling to its greedy rung on every request looks perfect to any HTTP monitor.

Reported: solve-time distribution, terminating status, objective value, optimality gap, `violations_returned`, `rungs`, `fallback_rate`.

`rungs` and `fallback_rate` are what would show the failure above. `violations_returned` counts the worst case — a roster breaking a hard rule returned with a `200` — and it is counted by the independent checker rather than by the solver marking its own work.

Distributions are p50/p95/max rather than means: a mean hides the tail, and the tail is what you set a budget against.

## Running it

Solver workloads are not web workloads — CPU-bound, memory-hungry, bursty, long-running. **Autoscale on queue depth, not CPU.**

Concurrency is chosen first and each solve gets an equal share of what remains, so their product fits the box. CP-SAT with 8 workers in a 1-vCPU container is *slower*, and over-subscription is not merely wasteful: the portfolio search assumes the threads it was promised.

Per-tenant queues rotate rather than sharing one FIFO, so a tenant with 500 queued jobs gets one slot per rotation, exactly like a tenant with one.

## Not built

- **The queue is in-process.** State lives in a dict, so replicas do not share a queue and a restart loses it. The solver itself is stateless, so swapping in Redis or SQS touches nothing below `service/`.
- **No metrics backend.** The signals above are all on `/v1/health`; pushing them somewhere is a deployment choice.
- **No interrupting a running solve.**

---

*Why async, why the wire schema is its own schema, and why the recommendation list is grouped rather than ranked: [`decisions.md`](../archive/decisions.md#by-theme), under* Service, runtime and the fallback ladder *and* Explaining an answer.
