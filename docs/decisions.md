# Decisions

What was chosen, what was rejected, and why.

**Each entry is readable standalone.** A decisions file backed by studies decays into a table of
links; a reviewer will read this file and never open a study. Summarise the finding here, link for
the analysis.

A decision record is permanently true — it is not history, and it does not belong in a spec, where
present tense squeezes rationale out.

Where a later decision overrides an earlier one, the earlier record is **amended in place with the
supersession named**, never rewritten and never deleted. A decisions file that silently corrects its
own past is a spec.

---

## Template

### D-000 — Title

- **Decision.** What was chosen.
- **Alternatives.** What was considered and rejected.
- **Reason.** Why, in terms that survive without context.
- **Consequences.** What this forces elsewhere.
- **Study.** `docs/studies/...` if one exists.
- **Date.**

---

## Open — to be written as they are made

Records leave this table as they are written. What remains here is what is still owed.

| ID | Decision | Tier |
| --- | --- | --- |

---

# Records

Written in batches, one batch per spec, and ordered here by ID so a reader can look one up directly.

**Every T1 decision is now written.** Three batches: the rule registry
([`specs/rules.md`](specs/rules.md)), the model and validation layers
([`specs/model.md`](specs/model.md), [`specs/validation.md`](specs/validation.md)), and the objective
([`specs/replan.md`](specs/replan.md)). What the Open table still lists is T2 and later, plus
`D-001`, which is T1 and is called out there for what it needs.

## D-001 — CP-SAT over MILP: measured, and not for speed

- **Decision.** CP-SAT. The MILP alternative is fully built in `benchmarks/milp.py` and reaches the
  same optimum on every committed case, so this record rests on a comparison rather than on a
  preference.
- **Alternatives.** Branch-and-cut MILP. Both SCIP 10 and CBC ship inside `ortools`, so the
  comparison needed no new dependency — and is therefore against **open-source** MILP, not Gurobi.
- **Reason.** **Not speed. Measured, CP-SAT loses**: SCIP proves the same optimum faster on 24 of 24
  cases, 38% faster than the shipped configuration and 25% faster than an ungated one. CBC is a coin
  flip at 11 of 24. What CP-SAT provides instead is three capabilities this project already depends
  on and MILP cannot supply:

  1. **Assumption literals, and therefore infeasibility cores** (`D-002`, `D-048`) — the object T4's
     explainer consumes and that `D-013` requires come from the solver rather than an LLM. MILP has no
     assumption mechanism; an IIS is a different guarantee and `pywraplp` does not expose one.
  2. **`violations()`** (`D-044`) — fixing every assignment and maximising true gate literals leaves
     exactly the violated constraints false, so one solve enumerates them all. That trick *is* the
     assumption mechanism. Without it the model can only refuse a roster, and comparing a refusal
     against the checker's violation set is the vacuous comparison `D-065` rejects.
  3. **Non-linear expressiveness** — D3 and D4 pair changes through `min(drops, adds)`, which
     `add_min_equality` states directly and MILP needs auxiliary binaries and big-M for. `milp.py`
     refuses D3 and D4 rather than comparing a linearised approximation.

  The price is quantified rather than waved away: about 1.3 ms per solve, against a model build
  costing ~5 ms regardless of backend (`D-092`). The solver choice moves roughly 15% of a request and
  Python model construction moves more.
- **Consequences.** The gating that buys capability 1 and 2 costs **21% of CP-SAT's search time** and
  half of its variables — 534 gate literals against 183 assignment variables on `headline/0`. That is
  the real price of the explainer, and it is now a number rather than an intuition.

  One finding travels beyond this record. **MILP's default relative MIP gap is unsafe at this
  objective's scale and fails silently.** `pywraplp` defaults it to `1e-4`, and `shortfall_weight` is
  100,000 so that coverage dominates (`D-057`) — so a roster one shift short scores in the hundreds of
  thousands and `1e-4` of that is ~30 disruption points, about ten changed shifts. At the default,
  SCIP returned 300003 and **reported it `OPTIMAL`** while 300001 was feasible. The first version of
  this study was therefore timing an approximation against a proof, and only the cross-formulation
  equivalence test exposed it. Generalised: **the weight that makes coverage dominate also makes any
  relative termination criterion coarse**, and any future solver with a gap tolerance inherits it.
- **Study.** `docs/studies/cp-sat-vs-milp.md`.
- **Date.** 2026-08-13.

## D-002 — Hard constraints structural rather than penalised

- **Decision.** Hard rules are encoded as constraints, not as large penalties in the objective.
  Infeasibility is a legitimate return value.
- **Alternatives.** Penalise every rule with a weight big enough that the solver avoids it — the
  formulation that never has to answer "no".
- **Reason.** A penalised legal rule produces a roster that is *cheaply illegal*, and cheaply illegal
  is not a state this service may return. It also destroys the differential harness: if nothing is
  hard, `checker_feasible` is universally true and the comparison is vacuous. And it moves every
  semantic claim into a weight nobody can falsify — a rule you can buy your way out of is a price,
  not a rule.
- **Consequences.** The service must be able to answer "nothing, and an explanation", which forces
  the assumption-literal machinery (`D-044`, `D-048`) and the T4 explainer. It also forces the
  classification test to be applied honestly rule by rule, because "make it soft" is no longer a free
  escape from a hard modelling question. The one deliberate exception is `R-COVER`'s floor (`D-018`),
  and what that costs is recorded in `D-047`.
- **Date.** 2026-08-12.

## D-003 — Model and checker as independent implementations sharing no rule logic

- **Decision.** The rules are implemented twice — once as a CP-SAT encoding, once as plain Python
  over a returned roster — and the two are compared automatically on every run.
- **Alternatives.** One implementation, tested directly against expected outputs. A checker that
  reuses the model's predicates so the two cannot drift.
- **Reason.** Structurally required, not a nice-to-have. Under any formulation without
  hard-constraint guarantees — penalties inside a local search, or a time-boxed solve accepting a gap
  — feasibility is not guaranteed by construction, and independent verification is the only thing
  that makes a legality claim true rather than assumed. A checker that reuses the model's predicates
  verifies that the model agrees with itself, which is the one thing never in doubt.
- **Consequences.** The duplication is deliberate and has to be defended against well-meaning
  refactoring, so an import-linter contract enforces it in CI. Exactly where the line falls is
  `D-038`; what may never be shared is `D-039`. The checker is also what every other test layer
  asserts against (`D-063`), so its independence is load-bearing for the whole suite rather than for
  the differential layer alone.
- **Date.** 2026-08-12.

## D-004 — Brute-force enumeration as ground truth rather than trusting the solver

- **Decision.** On instances small enough to enumerate exhaustively, every roster is generated and
  scored by the independent readings, and the solver is required to agree.
- **Alternatives.** Trust CP-SAT's `OPTIMAL` status. Test the model against hand-computed expected
  answers.
- **Reason.** `OPTIMAL` means optimal *for the model as encoded*, which is precisely the thing under
  test — it certifies the search, not the formulation. A wrong threshold, an inverted inequality or a
  forgotten horizon boundary all produce a confidently optimal answer to the wrong question.
  Hand-computed expectations do not scale past a handful, and they encode the author's reading of the
  spec, which is the same reading that produced the bug.
- **Consequences.** Enumeration costs `2 ** (employees × open_shifts)`, so instances stay tiny and
  the bound is asserted by a test rather than left to review — an oversized instance would not fail,
  it would only make the suite slow, which is how enumeration layers quietly get deleted instead of
  fixed. The layer lands in two stages (`D-042`). It is blind to anything both readings take as data,
  which is what the golden layer exists for (`D-067`). And it only covers the structures its
  instances contain, which is how a live objective bug survived it (`D-058`).
- **Date.** 2026-08-13.

## D-005 — Deviation-from-published as the objective, not cost-from-scratch

- **Decision.** The objective minimises how far the new roster departs from the published one. Cost
  is a second term traded against it, not the thing being minimised.
- **Alternatives.** Re-solve the week from scratch on a cost objective, which is what a scheduler
  normally does after a disruption.
- **Reason.** After a sick call the planner does not want the cheapest week, they want the cheapest
  *change*. A cost-optimal re-solve is free to rearrange people who were never affected, because cost
  cannot see that they had already been told. The product claim of this whole project is that the
  second-best roster nobody has to be re-told about beats the best roster everybody does.
- **Consequences.** The objective needs three inputs a cost objective does not: the incumbent, the
  publication state (`D-051`) and `now`. It gives cold solves a degenerate case rather than a separate
  formulation — with an empty incumbent every change weighs the same and the objective falls back to
  cost. And it fixes the T2 comparison, since "cold re-solve on cost" is precisely the baseline this
  is measured against.
- **Date.** 2026-08-12.

## D-006 — D2 as the shipped disruption metric; D3 and D4 configurable

- **Decision.** Five metrics D0–D4 are defined and encoded. **D2** — changed slots weighted by
  publication state and by notice — is the shipped default. D3 and D4 are configurable.
- **Alternatives.** Ship one metric and define no others. Ship the most detailed one, D4.
- **Reason.** All five are defensible, and the fact that they produce different rosters is the
  deliverable rather than a problem to settle — the T2 study exists to show it. D2 is the shipped
  choice because it is the simplest metric that prices the two things a planner actually reacts to:
  whether people were told, and how much warning they get. D3 and D4 add claims about human
  preference that are hypotheses rather than measurements, and a hypothesis is better shipped as an
  option than baked into the default.
- **Consequences.** Each metric contains the one before it — D1 with equal weights *is* D0, D2 with a
  flat multiplier *is* D1 — which is what makes the study a clean comparison rather than five
  unrelated ideas. Every metric has to be scored independently, so `scoring.py` implements all
  five and not only the shipped one (`D-042`). D2 reads `now`, so a golden test must pin `now` and
  not only the instance. And the metrics only diverge where there is slack, which is what makes
  coverage tightness T2's decisive generator knob (`D-060`).
- **Date.** 2026-08-12.

## D-007 — Answered under `D-049`

- **Decision.** The question this ID reserved — lexicographic ordering against a weighted sum for
  trading disruption against cost — was decided in [`D-049`](#d-049--weighted-sum-not-lexicographic-ordering),
  written with the objective batch at T1 rather than waiting for T2. Weighted sum.
- **Reason this record exists at all.** The ID was listed as owed, and deleting the row would leave a
  reader who finds `D-007` referenced anywhere with nothing to look up. `decisions.md` amends in place
  and does not erase, and the same courtesy applies to a question that turned out to be answered
  early.
- **Consequences.** None beyond `D-049`'s. The T2 half of what this row anticipated — sweeping the
  exchange rate rather than asserting it — is `D-050`, and its measurement is in
  [`benchmarks.md`](benchmarks.md): with a flat cost model the cost axis collapses, so the sweep has
  nothing to trace yet and says so.
- **Date.** 2026-08-13.

## D-008 — `R-COVER`'s soft floor ratified, and now measured rather than argued

- **Decision.** `R-COVER` keeps the hard ceiling and soft floor that `D-018` introduced provisionally
  at T1. The provisional marking comes off `rules.md`.
- **Alternatives.** A hard floor, which is what the walking skeleton did. Both directions soft.
- **Reason.** `D-018` argued this from the classification test — *what should the service return when
  the only otherwise-legal roster breaks the rule* — and concluded that "nothing, and an explanation"
  is the wrong answer for a coverage shortfall. Sound, and never measured. It is now: forcing every
  non-historical shortfall to zero over the committed set, **a hard floor cannot answer 16 of the 72
  cases at all**.

  The composition of those 16 is what settles it. Eight are weeks that were **already fully
  staffable before the event** — ordinary disruptions on healthy tenants, where a hard floor turns
  "one short on Saturday, here is what it costs" into "infeasible". The other eight are the
  chronically short tenants a hard floor was never going to serve. `scarce-skill` fails on all six
  seeds, `flexi-heavy` on three, `tight` and `multi-absence` on two each, and even `headline` — the
  Saturday sick call on a mid-sized tenant with slack — fails on one.
- **Consequences.** A fifth of this distribution would receive no answer from a hard floor, which is a
  product failure rather than a correct solve. The soft floor is what makes the fallback ladder in T3
  meaningful too: the exact rung returns a priced shortfall instead of dropping through to the greedy
  rung, and `benchmarks.md` shows the optimal replan leaving 0.16 positions short per clean case, so
  this path is exercised routinely rather than in extremis. The obligations `D-018` created stand
  unchanged — the shortfall weight must dominate by the derived bound (`D-057`), and `validation.py`
  checks it rather than trusting it.
- **Amends.** `D-018`, whose "provisional for T1 — folds into `D-008` in T2" is now discharged.
- **Date.** 2026-08-13.

## D-009 — Assignment booleans over pattern/column variables, measured

- **Decision.** Assignment booleans `x[e, d, s]`. The pattern formulation is fully built in
  `benchmarks/patterns.py` so the comparison is against a real second formulation rather than an
  estimate, and it is not shipped.
- **Alternatives.** One boolean per (employee, legal weekly pattern), with coverage summing the
  chosen patterns — which makes every per-employee rule vanish from the model, because a pattern
  breaking one is never enumerated.
- **Reason.** It is competitive on a replan and **fails on a cold week**. On replans the two are within
  noise, and the reason is not the formulation: `now` sits on day 5, so five of seven days are pinned
  and there are only 36 to 122 legal patterns for a whole tenant. Solved cold, with the horizon open,
  the catalogue grows to 5,000–19,500 patterns, enumeration alone costs 0.4–6.7 seconds against a 20 ms
  assignment solve, and the pattern model **fails to prove optimality within 30 seconds on 5 of 6
  cases**. The second failure is the one that matters, because caching removes the first and not the
  second.
- **Consequences.** The mechanism is worth naming, because it ties two of these studies together: with
  no incumbent the objective is nearly indifferent, and thousands of near-identical columns give
  CP-SAT an enormous symmetric search space. **The pattern encoding creates the symmetry that `D-087`
  found the assignment model does not have.** This is a result about *explicit enumeration*, not about
  column-based formulations in general — the standard answer is column generation, which needs an LP
  relaxation CP-SAT does not expose and would be a separate project. It also does not improve with a
  longer horizon: at a four-week reference period the enumeration is `4^28` rather than `4^7`.
- **Study.** `docs/studies/pattern-encoding.md`.
- **Date.** 2026-08-13.

## D-010 — Async job queue over synchronous HTTP

- **Decision.** `POST /v1/replans` enqueues and returns `202` with a job id; `GET` polls; `DELETE`
  cancels. No endpoint solves inside the request.
- **Alternatives.** Synchronous HTTP, which is simpler and needs no job state. An event-driven design
  reacting continuously to roster changes.
- **Reason.** Synchronous works only for sub-second solves. At 30 s it produces timeouts, retries that
  re-trigger an expensive solve, request pile-up, no progress feedback and no way to cancel — and the
  retry storm is the dangerous one, because it multiplies exactly the load that caused it.
  Event-driven suits continuous replanning but makes *"why did my roster change?"* hard to answer,
  which is the question this project exists to answer well.
- **Consequences.** Measured, the premise is weaker than it looked: **nothing in the committed set
  takes more than 12.4 ms**, so at present sizes a synchronous endpoint would have been adequate and
  this is insurance against instance sizes the project does not yet serve. The insurance is cheap and
  the shape is hard to retrofit — a caller written against a synchronous API cannot be moved to
  polling without a version bump — so it stays. It is also what makes the fallback ladder's budget
  meaningful: a request that may take 30 s needs somewhere to put a partial answer.

  Cancelling a *running* solve marks the job and discards its result but does not stop the CPU work,
  which needs a solution callback wired through `model.solve`. Stated in `service.md` rather than left
  to be discovered under load.
- **Date.** 2026-08-13.

## D-011 — Stateless solver, and an in-process queue that is not

- **Decision.** `run_job` takes a payload and returns a payload. No database reads anywhere in the
  solve path. The job store holds requests in memory, keyed by tenant.
- **Alternatives.** Let the solver read tenant profiles and rosters from a database directly, which
  removes a serialisation layer and a class of contract bugs.
- **Reason.** A solve that reads from a database cannot be replayed, and optimisation is close to
  undebuggable without replay: the input is large, the output is sensitive to every field, and "it
  returned something odd last Tuesday" is unanswerable unless last Tuesday's exact input is
  reconstructible. Every job therefore keeps its request, seed and profile version after completion —
  a job that has discarded its input cannot be replayed however good its telemetry is.
- **Consequences.** The distinction that matters is between the *solver* and the *queue*. The solver
  is stateless as specified. The queue is in-process, so replicas do not share it and a restart loses
  it — the honest limit of this tier, and a contained change: swapping the store for Redis or SQS
  touches nothing below `service/`, precisely because the solver reads nothing.

  Statelessness is also what makes the T2 benchmark machinery and the production path the same code.
  `benchmarks/methods.py` and `run_job` call the same solver with the same payloads, so a benchmark
  number is a claim about the deployed system rather than about a laboratory copy of it.
- **Date.** 2026-08-13.

## D-012 — The LLM renders a finding it cannot alter, and a validator bounds what it may say

- **Decision.** The deterministic layer computes the finding (`explain.py`) *and* renders it
  (`prose.py`). An LLM is optional and may only rephrase. `prose.unsupported_terms` bounds what any
  rendering may contain: every employee name, rule ID and number must appear in the finding it came
  from, and the deterministic renderer is held to the same bound it would judge a model by.
- **Alternatives.** Hand the LLM the structured finding and let it write the sentence, checking the
  result by reading. Let it choose which blocked employees are worth mentioning.
- **Reason.** `PLAN.md` requires the LLM be confined to artifacts a deterministic layer can reject,
  and "can reject" is the load-bearing half — a rejection rule that cannot be executed is a review
  policy. Meaning is what a deterministic layer cannot judge; **vocabulary is what it can**. So the
  check is not whether the sentence is true but whether it mentions anything the finding does not
  support, which is decidable and catches the failures that matter: an invented employee, an invented
  rule, an invented count.

  Building the renderer first is what makes the LLM optional rather than load-bearing. A phrasing
  step that already exists and is already correct leaves a model nothing to do but vary wording, so
  the feature degrades to "slightly better English" when the model is unavailable rather than to "no
  explanation".
- **Consequences.** The validator's first version flagged a token only if it was already a **real**
  employee name, which let a wholly invented `E99` through — the worse failure, since a fabricated
  person is less checkable than a real one named wrongly. It now treats anything identifier-shaped as
  a claim about the instance: rule-ID prefixed, or carrying a digit. Ordinary English words are not
  claims, which is what leaves a rephrasing model room to work.

  Three things the renderer refuses to invent are `D-013`'s rule applied to itself. **Weekdays**:
  `domain.py` has no calendar by design, so `day 5` becomes `Sat` only when the caller supplies
  `weekday_of_day_zero`, and says `day 5` otherwise. **Shift names**: `ShiftType.label` is printed
  verbatim, because expanding `E` to `Evening` is right for this generator and wrong for a tenant
  whose `E` means something else. **Employee identity**: names come from the payload, so under
  `D-016` a captured corpus renders surrogate keys — the text is exactly as readable as the caller's
  own identifiers, which is the correct dependency rather than a limitation.
- **Date.** 2026-08-13.

## D-013 — Minimal core from the solver, prose from the LLM — never the reverse

- **Decision.** The conflict is always identified by deterministic code. The LLM never decides *what*
  is wrong, only how to say it. Enforced by `D-012`'s validator rather than by instruction.
- **Alternatives.** Let the model read the instance and diagnose the shortfall directly, which is
  what a general-purpose assistant would do and needs no explainer at all.
- **Reason.** A diagnosis is a claim about the world that a planner will act on — moving someone's
  Saturday, calling somebody in. A model that produces one is producing a claim nothing checked, and
  the failure mode is not obvious nonsense but a plausible, specific, wrong reason: *Ana is
  unavailable* when Ana is merely over hours. That is worse than no explanation, because it is
  actionable and wrong.

  The inversion this record forbids is the tempting one, because it is less work: the model is good
  at reading a payload and producing a fluent account of it, and the account is usually right. Usually
  right is the problem.
- **Consequences.** The rule now has machinery behind it rather than a paragraph. `explain.py`
  answers from the checker (`D-097`), so the finding is independently derived; `prose.py` renders it;
  `unsupported_terms` rejects any rendering that adds a name, a rule or a number. A model that
  hallucinates fails the check rather than reaching a planner.

  It also constrains the tool surface T4 builds next: `explain_infeasibility` returns the structured
  finding alongside the prose, so a caller that does not trust the sentence can read the fields. The
  minimal-core reduction `D-048` defers is still owed and belongs to the *rare* case (`D-047`); this
  record's machinery is what it will render through when it lands.
- **Date.** 2026-08-13.

## D-014 — Horizon-boundary state supplied by the caller, not solved over a longer horizon

- **Decision.** Every rule whose true legal scope exceeds the one-week horizon takes its
  cross-boundary state as caller-supplied data: `max_hours_this_week[e]`,
  `last_shift_end_before_horizon[e]`, `consecutive_days_worked_before_horizon[e]`,
  `flexi_eligible[e, d]`, `dimona_ok[e, d]`. The solver and the checker see only those numbers.
- **Alternatives.** Extend the solve horizon to the legal reference period — a quarter, or a year.
  Reconstruct the history inside the service from its own store.
- **Reason.** Average weekly hours in Belgian law are measured over a rolling reference period
  (Arbeidswet art. 26bis §1), not per calendar week. A per-week ceiling is therefore not the rule but
  an approximation of it, and one that is wrong in both directions: it forbids a legal heavy week that
  a light week would compensate, and it permits thirteen consecutive weeks at the ceiling. Extending
  the horizon fixes that and multiplies instance size by an order of magnitude, destroying the
  interactive latency the whole service is built around.
- **Consequences.** Correctness now depends on a computation this service does not perform, and that
  cost is stated rather than hidden. The checker verifies assignments against the *supplied* budget
  and must never recompute it — a checker that reaches for the reference period is testing the caller,
  not the roster. Missing boundary state is a malformed payload and never a defaulted one, because the
  safe-looking fallback is precisely the wrong model this decision exists to avoid. `model.md` owns the
  input contract and names the caller as its owner. The same architecture is reused, there by necessity
  rather than by preference, in `D-032`.
- **Date.** 2026-08-12.

## D-015 — Incumbent comparison on observables only, never on objective values

- **Decision.** A replayed record compares only externally observable outcomes: coverage shortfall,
  violations by rule ID, cost, disruption, solve time. The two systems' objective values are never
  compared. Both solutions are scored by **this project's** checker and metrics.
- **Alternatives.** Compare objective values directly. Fit a mapping from the incumbent's objective
  onto this one so the two become comparable.
- **Reason.** The incumbent's objective is unknown, differently scaled and differently weighted, so a
  table comparing the two numbers is measuring nothing while looking rigorous. Fitting a mapping is
  worse: it invents the very thing under test, and any conclusion then depends on a translation
  nobody can check.

  This is the same rule `methods.py` already applies inside the repo — every method scored on the
  shipped D2 yardstick whatever it optimised, because scoring each method under its own objective
  makes every comparison a tautology. `D-015` is that discipline applied across an organisational
  boundary instead of within one, where it matters more because the other side's objective is not
  merely different but unavailable.
- **Consequences.** Scoring the incumbent with this project's checker means **the incumbent can fail
  it**. That is a finding to report, not a bug in the harness, and it is the most valuable thing an
  independent legality layer can produce — so the harness must not be built in a way that suppresses
  it or treats a violating incumbent as bad input.

  Results are paired per-instance deltas with win/loss/tie counts, never aggregate means. A mean
  hides the distribution that decides this: a substitute tying on ninety instances and losing badly
  on ten is not a substitute, and an average will not say so.

  Solve time is the one confounded metric and is marked as such rather than quietly compared: this
  service is measured locally while the vendor's figure may include queueing and network time. Where
  the vendor reports solver time separately that is the number used, and each record states which of
  the two was available.
- **Date.** 2026-08-13.

## D-016 — Pseudonymisation at capture, and absence reasons never written

- **Decision.** Employee identifiers become stable per-tenant surrogate keys at the moment of
  capture. Names, contact details and national registry numbers are never written. **Absence reasons
  are discarded**, retaining only the availability bit.
- **Alternatives.** Capture verbatim and pseudonymise at analysis or export time. Retain absence
  reasons under access control, on the grounds that they might inform a future model.
- **Reason.** Data that is never written cannot leak, and the timing is the whole decision: a
  pseudonymisation step at analysis time protects nothing about the window between capture and
  analysis, which is when a roster store is most exposed. And a roster store is an unusually rich
  target — it locates named individuals at specific places and times.

  Dropping absence reasons is the load-bearing half. A sick call is health data under GDPR Article 9,
  which carries obligations a benchmark corpus has no business taking on. The optimiser never needed
  the reason: `R-AVAIL` reads an interval, not a cause. So discarding it costs the model nothing and
  removes an entire category of data from scope — the cheapest privacy decision available, and only
  cheap because the domain model was already built without it (`D-020` separates *what befell
  someone* from *what they declared*, and neither carries a reason).
- **Consequences.** **The "raw" layer is not verbatim, and `capture.md` said it was.** The two-layer
  scheme exists so the normalization can be shown faithful, and it describes the raw layer as "the
  vendor request and response, verbatim and immutable" — which cannot hold once identifiers are
  replaced before anything is written. Writing this record surfaced the contradiction and the spec is
  corrected: raw means *as received, after pseudonymisation and with nothing else altered*, and the
  adapter's round-trip test compares against that, with pseudonymisation named as the first of the
  documented losses rather than discovered as a mismatch.

  A stable per-tenant surrogate key is deliberately stable: an employee must be recognisable across
  records or a replay cannot measure disruption against them, which is the whole point of the corpus.
  That is a real residual exposure — a stable key plus a shift pattern is re-identifying in a small
  tenant — and it is accepted rather than hidden, because the alternative removes the corpus's
  ability to measure the thing it exists to measure.
- **Date.** 2026-08-13.

## D-017 — The acceptance bar is fixed before the first replay

- **Decision.** The bar in [`specs/capture.md`](specs/capture.md#the-bar-stated-before-measuring) is
  fixed in advance of the first replay: two absolute gates, then bars on the paired distribution. It
  changes only through a `decisions.md` entry, and never in response to a result.
- **Alternatives.** Set the bar once the distribution is known, which is what usually happens.
- **Reason.** A success criterion written after the numbers arrive is not a criterion — it is a
  description of the numbers. This project spends its credibility on measurements that could have
  come out the other way, and a movable bar retracts that at the one moment it matters most, on the
  only corpus that can test the headline claim against reality rather than against instances this
  project invented for itself.
- **Consequences.** Each clause exists to close a specific route, and the structure is the decision
  rather than the numbers:

  - **Two absolute gates** — zero checker violations, and no instance with worse coverage. Both are
    outcomes no distributional argument can compensate for: one violation breaks the legality claim
    the product is built on, and understaffing is what a planner notices within the hour.
  - **Parity and thesis are separate numbers** — no worse on ≥ 90%, strictly better on ≥ 50%. One
    figure cannot carry both, and T2 already produced the method that proves it: greedy repair ties
    the optimum on 64 of 72 cases, so it would clear a 90% parity bar while demonstrating nothing.
    The ≥ 50% clause is what that finding argues for.
  - **A cap on the losses** — worse by no more than 25% on the instances where it is worse. Without
    it the 10% allowance is unbounded and ten catastrophic losses pass a bar designed to exclude
    exactly that.
  - **Two time bounds** — p95 ≤ 1.5x the incumbent *and* ≤ 5 s. The relative bound alone is gamed by
    a slow incumbent; the absolute one is what the planner waiting for the answer experiences.
- **Date.** 2026-08-13.

## D-018 — `R-COVER` split into a hard ceiling and a soft floor

- **Decision.** Coverage is one equality per shift instance, `Σ_e x[e, d, s] + u[d, s] = req[d, s]`
  with `u ∈ [0, req]` priced in the objective. Overstaffing is rejected outright; understaffing is
  permitted and priced. ~~Provisional for T1 — folds into `D-008` in T2.~~ **Ratified by `D-008`**,
  which measured what this record argued: a hard floor cannot answer 16 of the 72 committed cases,
  and eight of those weeks were fully staffable before the disruption.
- **Alternatives.** A hard equality, which is what the walking skeleton did. Both directions soft. Two
  inequalities rather than one equality with an explicit slack.
- **Reason.** The classification test asks what the service should return when the only
  otherwise-legal roster breaks the rule. For a coverage shortfall, "nothing, and an explanation" is
  the wrong answer — a disruption often has no legal repair, and *one short on Saturday, here is what
  it costs* is what a planner can act on. The ceiling can be hard for free: the all-zero roster
  satisfies it, so a hard upper bound can never be the sole cause of infeasibility. Both degenerate
  alternatives are worse than the split. **Everything soft** makes `checker_feasible` universally true,
  so the differential harness asserts `true ⟺ true` and every semantic claim retreats into a weight
  nobody can falsify. **Everything hard** leaves no shortfall representable, so there is no cost axis to
  trade disruption against and no Pareto frontier — and the service answers only "infeasible" to a
  planner who is one person short, which is a product failure rather than a correct solve.
- **Consequences.** The equality with an explicit slack gives CP-SAT a tighter linear relaxation than
  two inequalities, and `u` is directly the coordinate the explainer reports rather than something
  reconstructed from a headcount difference. The shortfall weight must dominate every other soft term —
  the bound is derived in `D-057`. In the unconstrained case the optimum still lands exactly on
  `req[d, s]`, so the walking skeleton's behaviour is preserved rather than abandoned. Leads directly to
  `D-047`.
- **Date.** 2026-08-12.

## D-019 — Availability as interval intersection rather than whole-day blocking

- **Decision.** `R-AVAIL` blocks `(e, d, s)` when the shift's half-open interval intersects a blocked
  interval — not when the absence falls on the same calendar day.
- **Alternatives.** Day-granular blocking, which is what `t0.py` does.
- **Reason.** Day equality is wrong in both directions. An unavailability of `Sat 09:00–12:00` must
  not block `Sat Evening`, and a `23:00–07:00` shift belongs partly to the next day.
- **Consequences.** Shift windows are computed from timestamps on both sides, and the checker
  recomputes them from the raw interval lists rather than consuming an eligibility mask from the model
  — the mask is the thing under test. Half-open overlap is a shared convention under `D-038`, so an
  unavailability ending exactly at a shift's start is not a conflict. This is the substantive
  correction to `t0.py`, which the rules spec supersedes rather than extends.
- **Date.** 2026-08-12.

## D-020 — Absences non-relaxable, declared unavailability relaxable — one rule, two provenances

- **Decision.** `R-AVAIL` takes two caller-supplied interval sets, `absences[e]` and
  `unavailability[e]`. One rule ID, one predicate, two provenances carried through to what a human is
  shown: the checker's `Violation` records `absent` or `unavailable` in its `observed` field.
  `unavailability` becomes tenant-configurable to soft in T2; `absences` never does.
- **Alternatives.** Two rule IDs. A single `blocked` set that discards the provenance at parse time.
- **Reason.** The distinction is invisible to the solved model and matters only to what a human is
  told. A report blaming a declared preference is actionable — that person can be asked. One blaming an
  illness is noise. Two IDs would duplicate an identical predicate to buy a reporting difference.
- **Consequences.** Provenance has to survive into the reporting surface, so the two sets cannot be
  merged when the payload is parsed. An absent key means the empty set, and never means "unknown".
- **Superseded in part by `D-059`, 2026-08-13.** This record originally held that `absences` carry no
  assumption literal, "because there is no meaningful core containing *Ana is ill*". `D-059` gates every
  eligibility fixing uniformly, absences included, so a pair that exists only to carry an incumbent
  assignment is gated either way. The original clause was written when both provenances presolved away
  and neither had a literal at all; it describes a distinction that only bites for pairs where a
  variable exists anyway. That case is reachable exactly when the incumbent's already-started past
  assigns an absent person — *the past itself is illegal*, which is a diagnostic worth having rather
  than permission to relax, and which is the framing the structural legal rules already use for their
  own literals. What is left in practice: the model's `Gate` descriptor does not distinguish the two
  provenances; only the checker's `Violation` does. Carrying provenance into the gate is a **T4
  explainer obligation**, recorded here so it is a known cost rather than a discovery.
- **Date.** 2026-08-12, amended 2026-08-13.

## D-021 — Pins as assumption-literal equalities rather than build-time constant substitution

- **Decision.** `R-PIN-PAST` fixes `x[e, d, s] = x̄[e, d, s]` as a gated equality for every shift
  instance with `start(d, s) < now`, rather than substituting constants when the model is built.
- **Alternatives.** Substitute the constant at build time and never create the variable.
- **Reason.** Substitution is cheaper and makes *pinning is not exemption* automatic, but it destroys
  the ability to name the past as the source of a conflict. Because pins are equalities, an incumbent
  that already violates a rule makes the entire solve infeasible with no repair available — a real
  production scenario, reached whenever rules changed or a roster was hand-edited. The literals let the
  service distinguish **"the past itself is illegal"** from **"no legal future exists"**: two different
  messages, two different operator responses, and the first is invisible without them.
- **Consequences.** Pinned assignments are ordinary variables, so they stay inside every other rule's
  sums by construction — pinned hours consume the `R-MAX-WEEKLY` budget, pinned days count toward
  `R-CONSEC-DAYS`, and a pinned night shift ending at 07:00 constrains the following morning through
  `R-REST-GAP`. Treating the past as though it did not happen is the classic bug in this rule, and it
  produces rosters that are illegal precisely at the boundary nobody inspects. The cut-off is
  `start(d, s) < now` strictly — a shift in progress is past, because three hours of a night shift
  already worked cannot be un-worked. `now` and `x̄` are both caller-supplied and neither is derived; a
  replan carrying one without the other is a malformed payload. The encoding cost is expected to be
  small because CP-SAT presolve folds equalities well — **measured in the T2 presolve study, not
  assumed here.**
- **Date.** 2026-08-12.

## D-022 — Historical coverage shortfall excluded from the objective, reported separately

- **Decision.** Shortfall on shift instances that started before `now` is excluded from the objective
  and reported separately as historical. The same applies to `R-SKILL-MIX` shortfall.
- **Alternatives.** Include it in the objective. Forbid it, by requiring the incumbent's past to be
  fully staffed.
- **Reason.** A past shift that was understaffed stays understaffed, and nothing in the horizon can
  fix it. Leaving it in the objective adds a constant that cannot be optimised away, and it makes two
  runs with different `now` values incomparable — which is exactly the comparison a replan study needs
  to make.
- **Consequences.** Both the objective encoding and the independent scorer need the `now` boundary,
  and each implements the exclusion separately. The shortfall is still reported, so it does not vanish
  from a planner's view along with its cost.
- **Date.** 2026-08-12.

## D-023 — `R-CONSEC-DAYS` reclassified operational/CBA — no statutory basis for adult workers

- **Decision.** The rule stays in the registry; its legality claim does not. Provenance is operational
  and sectoral-CBA, and a tenant may switch the rule off entirely rather than only loosen it — the one
  rule among the structural legal set that may legitimately be disabled.
- **Alternatives.** Keep it as statutory with a citation attached. Drop the rule.
- **Reason.** The citation search surfaced that Belgian law sets **no general cap on consecutive
  working days for adult workers**. The commonly quoted figure of six derives from Arbeidswet art. 16,
  which requires compensatory rest for Sunday work *within the six days following that Sunday* — a rule
  about where compensatory rest lands, not a ceiling on consecutive days. The binding legal guarantee
  is `R-WEEKLY-REST` (art. 38ter §3), and it belongs there. Planners want the cap and sectoral
  agreements impose it, so the rule is worth encoding; the legality claim is not.
- **Consequences.** Tenant-configurable including *off*, unlike everything else in that section. Youth
  workers under 18 do have explicit statutory limits — out of scope for T1, and not this rule. This is
  the clearest case for requiring provenance before T1 closes: the rule was carried as
  `labour law [CITE]`, and only the search for the citation found that there wasn't one. A legality
  claim without provenance is a guess, and the checker is the component whose whole value is that it is
  not one.
- **Date.** 2026-08-12.

## D-024 — Belgian rule implemented wherever it is stricter than the WTD

- **Decision.** Where the Arbeidswet and Directive 2003/88/EC differ, this project implements the
  Belgian rule. Each affected rule records where the divergence falls.
- **Alternatives.** Implement the WTD as a portable European baseline. Implement both and check the
  pair against each other.
- **Reason.** The Belgian rule is the binding one for the target tenants, and the stricter of the two
  cannot produce a WTD violation — so one implementation satisfies both, and the converse does not
  hold. The clearest instance is `R-WEEKLY-REST`: WTD art. 5 requires 24 uninterrupted hours plus
  art. 3's eleven, and art. 16(a) permits averaging that over a 14-day reference period; Belgium
  requires 35 *consecutive* hours and does not average. Implementing the WTD rule would leave rosters
  that are unlawful in Belgium.
- **Consequences.** Each rule records which of its parameters are national rather than European, so a
  future non-Belgian tenant knows exactly what has to move. Article numbers were checked against the
  consolidated statute rather than third-party restatements, which are frequently wrong: the FPS
  Employment summary attributes the three-hour minimum work period to art. 19 where the statute puts it
  in art. 21.
- **Date.** 2026-08-12.

## D-025 — `R-SKILL-MIX` class declared per entry, not per rule

- **Decision.** Each `skill_mix` entry declares its own class, and a hard entry carries its own legal
  provenance string, validated non-empty at profile load.
- **Alternatives.** One class for the whole rule, as every other rule has.
- **Reason.** The classification test gives *different answers* for two entries of identical shape.
  "At least one first-aider" is operational and soft — a covered shift where nobody can do first aid is
  a real, priced operational state, and a planner must be shown it rather than handed an infeasibility.
  "At least one licensed nurse" is legal and hard — running the ward without one is not an expensive
  option, it is a prohibited one. Applying the test rule-by-rule forces one answer for both; applying
  it entry-by-entry is the only way it comes out right.
- **Consequences.** Soft entries get a slack variable and hard entries none, so the encoding branches
  on payload data rather than on the rule ID. Weights for soft entries sit at or above the `R-COVER`
  shortfall weight — an unqualified shift is at least as bad as a short one. Validation owns checking
  that a hard entry names its source, since the class travels in the payload rather than in the code.
- **Date.** 2026-08-12.

## D-026 — `R-SKILL-MIX` kept separate from `R-SKILL` to preserve presolve elimination

- **Decision.** Two rule IDs and two encodings, even though `R-SKILL` is formally the special case
  `m = req[d, s]` of `R-SKILL-MIX`.
- **Alternatives.** Unify them under one counting constraint, since one is a special case of the other.
- **Reason.** `R-SKILL` is per-assignee and is enforced by *deleting* variables in presolve — the
  cheapest constraint in the model, and together with `R-AVAIL` it eliminates most of the grid.
  `R-SKILL-MIX` constrains a shift's *composition*, needs a counting constraint over the surviving
  variables, and cannot presolve away. Unifying them would trade the cheapest encoding in the model for
  the more expensive one and buy nothing but a shorter registry.
- **Consequences.** Two IDs, two encodings, one vocabulary. The checker implements the two counts
  independently even though both read `skills[e]`. In practice `R-SKILL` reaches a planner through
  `R-COVER` — scarcity surfaces as a priced shortfall — so the explainer reports skill scarcity
  alongside the shortfall rather than as a separate finding.
- **Date.** 2026-08-12.

## D-027 — Shift hours attributed wholly to the start day, never split at midnight

- **Decision.** A shift instance's hours belong entirely to its start day. A `23:00–07:00` night shift
  is eight hours on `d` and zero on `d + 1`, for `R-MAX-DAILY`, `R-MAX-WEEKLY` and `R-CONSEC-DAYS`
  alike.
- **Alternatives.** Split the hours at midnight, in proportion to the time falling either side.
- **Reason.** It follows from shift instances being indexed by start day, and it has to be *stated*
  because a checker that split at midnight would disagree with the model on every night shift while
  both looked entirely correct in isolation.
- **Consequences.** `d` is a worked day for `R-CONSEC-DAYS` and `d + 1` is not, which is the intended
  reading: the night worker's Tuesday is mostly rest, and it is `R-REST-GAP` that protects it, not a
  fractional day count. The convention is shared between model and checker under `D-038` — it is a
  definition this project fixes, not a reading of the law, so two independent implementations of it
  would add no signal.
- **Date.** 2026-08-12.

## D-028 — Weekly rest as anchored candidate windows rather than time discretisation

- **Decision.** Introduce `r[e, j]` for each candidate window `j`, require `Σ_j r[e, j] ≥ 1`, and for
  each shift instance overlapping window `j` add `r[e, j] ⟹ x[e, instance] = 0`. Candidates are
  anchored at `end(d, s)` for each shift instance, plus the horizon start.
- **Alternatives.** Discretise time and test a window at every tick. A `regular` automaton over the
  worked/not-worked sequence.
- **Reason.** Anchoring is sufficient, not merely convenient: any feasible rest window can be slid
  later until its left edge meets the end of some shift without shrinking below the threshold, so an
  anchored candidate exists whenever any window does. The candidate count is therefore `|O| + 1` and
  **not a function of time granularity** — no minute resolution has to be chosen, and no correctness
  claim depends on one.
- **Consequences.** `R-WEEKLY-REST` is the only T1 rule that is existential rather than a sum over
  assignments. The checker *measures* where the model *searches* — sort the assigned intervals, prepend
  `last_shift_end_before_horizon[e]`, take the maximum gap — which is what keeps the two readings
  independent for the one rule where sharing the construction would be most tempting. The automaton
  alternative expresses this rule and `R-CONSEC-DAYS` in a single propagator and is deferred to the T2
  encoding study, which should confirm that it beats the naive form at seven-day horizons rather than
  assume it.
- **Date.** 2026-08-12.

## D-029 — Weekly rest required inside the horizon — conservatism accepted over a heavier caller contract

- **Decision.** The 35-hour rest block must lie **within** the horizon. A lawful roster whose block
  straddles the horizon's end is therefore rejected.
- **Alternatives.** A caller-supplied forward-looking commitment, symmetric with
  `last_shift_end_before_horizon`.
- **Reason.** On a seven-day horizon the conservatism is nearly harmless, since one such block must
  exist inside any week. The alternative obliges the caller to promise something about a week it has
  not planned yet — a heavier contract than the conservatism costs, and one that could not be honestly
  honoured at the moment a replan is requested.
- **Consequences.** It bites on shorter horizons, so short horizons are not a supported use case until
  that commitment lands. Recorded as known conservatism rather than left to be rediscovered as a bug
  report. The committed micro-instance set keeps a seven-day horizon throughout for this reason, rather
  than derogating the rule — see `D-065`.
- **Date.** 2026-08-12.

## D-030 — Budget sanity bounds as input validation, not as roster violations

- **Decision.** That the supplied `max_hours_this_week[e]` does not exceed the absolute weekly ceiling
  is checked in the input-validation layer. It is never reported as an `R-MAX-WEEKLY` violation.
- **Alternatives.** Report it as a rule violation, since it is locally verifiable. Do not check it at
  all, since the budget is the caller's contract.
- **Reason.** It *is* worth verifying — a 60-hour weekly budget is a bad payload whatever the roster
  says. But it is a property of the payload, not of the roster, and reporting it as a rule violation
  would blame the solver for the caller's arithmetic while describing a roster that is perfectly legal
  against the budget it was given.
- **Consequences.** Two layers with two result types — see `D-040`. The checker verifies assignments
  against the *supplied* budget and never recomputes it. This is the single place a well-meaning
  checker most reliably goes wrong: one that reaches for the reference period is testing the caller,
  and it will disagree with the model for reasons that are defects in neither.
- **Date.** 2026-08-12.

## D-031 — `R-MIN-SHIFT` reclassified input validation — not roster-violable under fixed shift instances

- **Decision.** The minimum work period is checked over the tenant's shift catalogue at profile load
  and on every profile change, not over rosters. The roster checker does not implement it — the one
  intended exception to *every rule gets a checker encoding*.
- **Alternatives.** Keep it as the hard constraint the registry originally carried.
- **Reason.** With fixed shift instances it cannot be one. Shift types have durations defined by the
  tenant profile, and `x[e, d, s]` assigns a whole instance or none of it, so no roster the model can
  express contains a work period the catalogue does not already contain. A too-short shift is a
  **defect in the profile, not in the roster** — and a constraint that no reachable solution can violate
  is not a constraint, it is validation wearing one.
- **Consequences.** It becomes structural again in **T5 generation mode**, where shift boundaries turn
  into decision variables rather than data, at which point it needs a real encoding and a checker entry.
  Recorded so that transition is a known cost rather than a discovery. It reads gross `span` rather than
  net working time — see `D-037` — because art. 21 governs the work period, and a "prestatie" containing
  a coffee break is still one period. There is no explainer case: a profile is rejected at load, before
  any solve exists to explain.
- **Date.** 2026-08-12.

## D-032 — Flexi eligibility and Dimona state resolved upstream, indexed per employee **per day**

- **Decision.** `flexi_eligible[e, d]` and `dimona_ok[e, d]` are caller-supplied booleans indexed by
  day, mandatory for any employee on a flexi contract. Model and checker read the boolean and never
  derive it.
- **Alternatives.** Derive eligibility inside the service. Index the flag per employee rather than per
  day.
- **Reason.** Two separate arguments, and both are forcing. **Upstream, by necessity** — between them
  these rules depend on employment with *other* employers in quarter T-3 against a sectoral full-time
  reference, on a reduction from 100% in T-4 to 80% in T-3, on year-to-date earnings across employers,
  on sectoral opt-outs, and on a response the NSSO returns from its own records. A one-week payload
  contains none of it, and no amount of solver cleverness recovers it. **Per day, because quarters cut
  through horizons** — eligibility is retested each quarter and a Dimona may never cross a quarter
  boundary, so in the week containing 30 June and 1 July one employee can be eligible on Tuesday and
  ineligible on Wednesday inside a single solve. An employee-level flag gets exactly that week wrong,
  and it is the week nobody tests.
- **Consequences.** Correctness depends on a computation this service does not perform, stated the same
  way as the reference period in `D-014`. A missing flag for a flexi employee is a malformed payload,
  never a default of `true`. Both rules are enforced by presolve elimination into the same eligibility
  filter, which is what makes `D-034`'s separation a deliberate choice rather than a side effect.
- **Date.** 2026-08-12.

## D-033 — Flexi income ceiling folded into `max_hours_this_week`, not a parallel euro budget

- **Decision.** The annual flexi income ceiling enters as a fourth term in the `min()` the caller
  already computes for `max_hours_this_week[e]`.
- **Alternatives.** A parallel euro-denominated budget, with its own constraint in the model.
- **Reason.** The caller already converts a reference period into weekly hours; converting a remaining
  income allowance into remaining hours is the same kind of arithmetic against a known wage. It keeps
  one budget concept in the model instead of two, and the second would be another thing to keep
  consistent for no modelling gain.
- **Consequences.** The model never sees money, which keeps wage rules cleanly outside it — the horeca
  flexi hourly cap is recorded in the spec precisely so nobody mistakes it for a rostering constraint.
  The conversion's correctness sits with the caller, alongside everything else `D-014` moved there.
- **Date.** 2026-08-12.

## D-034 — `R-FLEXI-ELIG` and `R-DIMONA-FLX` kept as separate IDs — different operator actions

- **Decision.** Two rule IDs, even though both are presolve eliminations folded into a single
  eligibility filter and both consume a caller-supplied per-day boolean.
- **Alternatives.** One combined flexi-eligibility gate, since the encodings are identical.
- **Reason.** They fail for different reasons and produce different operator actions — *this person
  cannot hold a flexi job* versus *the paperwork is not in*. The second is fixable this morning; the
  first is not fixable at all. An explainer that conflates them sends the planner somewhere useless.
- **Consequences.** The presolve exclusion table records both reasons when a pair is excluded by both,
  so neither is lost behind the other. Identical encoding is not an argument for identical identity:
  the ID exists for the vocabulary, not for the constraint.
- **Date.** 2026-08-12.

## D-035 — Conservative Dimona reading for same-day replan — only filed `OK` counts

- **Decision.** `dimona_ok[e, d]` is true only where a type-`FLX` declaration is filed and the NSSO
  returned `OK`. "Fileable in time" does not count in T1.
- **Alternatives.** An optimistic reading, admitting substitutes whose filing could plausibly complete
  before the shift starts.
- **Reason.** The optimistic reading requires a judgement about NSSO turnaround that this service
  cannot make. The gate is real and it binds precisely where this project's headline scenario lives:
  under the verbal regime the filing names the day's start and end times, so replacing an absent flexi
  worker with another flexi worker requires a fresh `OK` before the substitute starts. For a Saturday
  sick call that materially narrows which substitutes are reachable, in a way that has nothing to do
  with availability or skill. A replan that ignores it proposes repairs that cannot legally be executed
  that morning.
- **Consequences.** `dimona_ok[e, d]` is not static within a horizon, and for a same-day replan the
  caller must distinguish *already filed* from *fileable in time*. The conservative reading may
  therefore reject repairs a human would make; whether that costs real repairs is answerable only
  against real incumbent decisions, and is deferred to the T2 capture and replay work. The filing
  deadline itself is unresolved — vendor guidance states 24 hours before start, the general statutory
  obligation is filing before work begins, and the two are not the same claim.
- **Related.** The asymmetry this creates — moving a flexi worker's shift requires re-filing, moving a
  salaried worker's requires nothing — is the externally grounded argument that a contract-weighted
  disruption metric is not arbitrary. That is `D-036` and D3/D4 territory, and it is deliberately *not*
  a reason to change the shipped D2.
- **Date.** 2026-08-12.

## D-036 — Per-contract administrative disruption deferred, and the D0–D4 study raised its value

- **Decision.** Not added to the metric. Changing a flexi worker's shift carries administrative cost a
  salaried change does not — same-day Dimona filing (`R-DIMONA-FLX`) is the clearest case — and this
  ID reserved the question of pricing that asymmetry. It stays out of D0–D4 and out of the shipped
  profile.
- **Alternatives.** Add a per-contract multiplier to the slot weight and include it in the D0–D4
  comparison as a sixth variant.
- **Reason.** It is not one of D0–D4 and adding it would have changed what that study measured. D0–D4
  nest — D1 with equal weights is D0, D2 with a flat multiplier is D1 — which is what makes their
  comparison clean (`D-085`). A contract multiplier is orthogonal to that ladder rather than another
  rung on it, so it belongs in its own study. More importantly the weight itself is unknown: how much
  administrative cost a same-day Dimona actually imposes is a fact about a tenant's back office, and
  inventing a number would make it look measured.
- **Consequences.** The D0–D4 study makes this **more** interesting rather than less, and the reason is
  worth recording because it is not obvious. D0, D1 and D2 turn out never to diverge on the committed
  set, because a disruption damages a *given* slot, so the publication and notice weights multiply
  every candidate repair by the same constant and a constant factor reorders nothing. A per-contract
  weight would not behave that way: it varies with **which employee** is chosen, and candidates differ
  precisely in that. So it is the one weight in this family that would genuinely change the answer on
  this distribution — unlike the two that ship.

  It needs the same evidence D3's `W_callin > W_cancel > W_move` ordering needs, which is
  capture-and-replay. Revisit with that corpus, not before.
- **Date.** 2026-08-13.

## D-037 — `span` and `work_hours` as separate symbols — no single `hours(d, s)`

- **Decision.** A shift instance carries gross `span` and net `work_hours` as distinct symbols.
  `R-MIN-SHIFT` reads `span`; `R-MAX-WEEKLY` and `R-MAX-DAILY` read `work_hours`.
- **Alternatives.** One `hours(d, s)` symbol, as most rostering models have.
- **Reason.** Art. 38quater entitles a worker exceeding six hours to a break, and a break is not
  working time — so the two quantities genuinely differ, and the rules disagree about which one they
  want. Art. 21 governs the *work period*, and a "prestatie" may contain short meal or coffee breaks
  without becoming two periods, so the minimum-length rule wants gross span. The other two are
  working-time ceilings and want net.
- **Consequences.** One symbol would make one of those rules wrong by about a break per shift — some
  fifteen minutes, in a direction no test would notice until a checker and a model disagreed over it.
  `work_hours = span − break_hours` is a stated convention shared between the two readings under
  `D-038`.
- **Date.** 2026-08-12.

## D-038 — Independence scoped to rule logic; payload schema and stated conventions shared

- **Decision.** The model and the checker share the payload schema and the stated conventions —
  half-open interval overlap, start-day attribution, `work_hours = span − break_hours`. They share no
  rule predicate and no rule parameter. Enforced by import-linter contracts in CI.
- **Alternatives.** The original phrasing, "they share no code".
- **Reason.** The original cannot be implemented as written: the differential harness must feed *the
  identical instance* to both readings, so both must be able to parse an instance, so something is
  shared. The line is drawn by what a shared item could hide. A **schema** bug corrupts both readings
  identically and the harness cannot see it — but neither can a schema hide a *rule* bug, which is what
  the harness exists to catch, and sharing is the only way the two readings are comparable at all. A
  **convention** is a definition this project fixes rather than a reading of the law; two independent
  implementations of the same convention add no signal, and a disagreement between them would be a bug
  in neither model nor checker.
- **Consequences.** Six import-linter contracts covering the checker, the model, input validation and
  the objective scorer, each asserting a direction of non-dependence. The parameter half of the rule is
  **not** linted — see `D-039` — because no linter can tell a shared constant from a coincidentally
  equal one.
- **Date.** 2026-08-12.

## D-039 — Rule thresholds never defaulted in shared code — payload carries every parameter

- **Decision.** Every numeric rule parameter — 11 hours, 35 hours, 3 hours, 6 days — travels in the
  payload. No default for any of them lives in code that either reading can reach.
- **Alternatives.** A shared constants module holding the statutory defaults, which is where they would
  naturally go.
- **Reason.** A shared threshold is precisely the bug the brute-force and differential layers **cannot**
  detect, because both readings would be wrong in the same direction and agree perfectly while doing it.
  Every other class of rule bug shows up as a disagreement; this one shows up as silence.
- **Consequences.** Payloads are more verbose, and a missing parameter is a malformed payload rather
  than a silent statutory default. Because no linter can distinguish a shared constant from a
  coincidentally equal one, this is a standing **review obligation** — the one part of `D-038` that CI
  does not enforce, and therefore the one most likely to decay.
- **Date.** 2026-08-12.

## D-040 — Input validation and roster checking as separate layers with separate result types

- **Decision.** `validate_instance()` returns `InputDefect`; `check()` returns `Violation`. The two
  are never mixed in one list.
- **Alternatives.** One validation pass returning one list of problems, which is what most systems
  do.
- **Reason.** The dividing question is whether a different roster could fix the fault. If none could,
  it is input validation. Conflating the two is how a caller's arithmetic error gets reported as a
  solver defect. They also have different audiences — a caller fixes a defect, a planner reads a
  violation — and a single list forces both to filter it.
- **Consequences.** A non-empty defect list rejects the request outright and never degrades into a
  best-effort solve, because a request that is not well-formed has no meaningful optimum. Several
  rules land wholly or partly in the validation layer as a result — `R-MIN-SHIFT` entirely (`D-031`),
  `R-MAX-WEEKLY`'s budget bound (`D-030`) — and the registry has to say so explicitly, or a reader
  looking for a checker encoding finds nothing and reads it as an omission.
- **Date.** 2026-08-12.

## D-041 — Differential harness compares violation sets, not feasibility bits

- **Decision.** The harness asserts `checker_violations(r)` equals `model_violations(r)` as sets of
  `(rule, coordinates)`, and prints the rule ID on mismatch.
- **Alternatives.** Assert `model_feasible(r) ⟺ checker_feasible(r)`, which is what `PLAN.md`
  originally specified.
- **Reason.** Once a coverage shortfall is representable the feasibility comparison is vacuous — the
  empty roster satisfies every hard rule, so `checker_feasible` is nearly always true and the
  assertion collapses to `true ⟺ true`. Comparing violation sets also localises a disagreement to the
  rule that caused it, instead of reporting that two systems disagree about a whole roster and
  leaving someone to find out where.
- **Consequences.** The model must be able to *report* violations rather than merely refuse rosters,
  which is `D-044`, and which is the second independent reason the assumption literals are not
  optional. Two places where the readings genuinely differ in granularity had to be stated rather
  than papered over — `D-046` and `D-045` — and neither narrowing may be widened without a record
  here.
- **Date.** 2026-08-12.

## D-042 — Brute-force layer split into feasible-set and objective stages

- **Decision.** Stage **(a)** asserts the enumerated hard-feasible set equals the model's feasible
  set; stage **(b)** asserts the solver's objective equals the enumerated optimum. (a) shipped with
  the checker, (b) with the disruption metric.
- **Alternatives.** Hold the whole layer until the objective exists, as the tier gate implied. Pull
  the metric forward to unblock it.
- **Reason.** The gate as written in `PLAN.md` read *solver objective equals enumerated optimum* —
  which needs an objective, and the disruption metric is specified late in T1. The gate depended on
  an artifact the same tier scheduled after it. Splitting resolves that without reordering the tier:
  (a) needs only the checker, and it catches the large majority of encoding errors — a wrong
  threshold, an inverted inequality, a forgotten horizon boundary.
- **Consequences.** Stage (a) is not a weaker version of the gate, it is the half that does not need
  preference to be defined, and saying so is what stops it being treated as a placeholder. Stage (b)
  needs a second independent reading of the *objective* for exactly the reason (a) needs one of the
  rules — an enumeration that asks the model what a roster is worth proves only that the model agrees
  with itself — so `scoring.py` evaluates `replan.md` directly and is forbidden by contract from
  importing the model's encoding.
- **Date.** 2026-08-13.

## D-043 — `R-COVER` ceiling gated as `o == 0` so overstaffing is reportable, not merely rejected

- **Decision.** Overage gets its own variable `o[d, s]` under a gated `o == 0`, rather than being
  excluded by bounding the assignment sum inside the slack's domain.
- **Alternatives.** Fold the ceiling into `u`'s domain, which makes an overstaffed roster
  unrepresentable and costs nothing.
- **Reason.** An unrepresentable roster cannot be reported. The differential harness fixes a roster
  and asks the model what is wrong with it, so an overstaffed roster has to produce a *finding with
  coordinates* rather than an infeasibility with none. Same argument as `D-059`, one layer up.
- **Consequences.** One extra variable and one extra gate per shift instance. The checker
  independently recounts assignees and emits a violation for any instance over `req`, and must not
  read `u` from the solver — a checker that trusts the solver's own slack is verifying arithmetic,
  not coverage.
- **Date.** 2026-08-12.

## D-044 — Model violations enumerated by maximising gate literals, not by iterating cores

- **Decision.** `violations(roster, instance)` fixes every assignment variable to the roster, then
  maximises the number of true gate literals. The literals left false are exactly the violated
  constraints.
- **Alternatives.** Read the infeasibility core. Iterate cores — drop each and re-solve — to
  enumerate all conflicts.
- **Reason.** With every assignment fixed, each gate can be true exactly when its own constraint
  holds, so one maximisation enumerates every violation at once. A core explains one conflict and
  hides the rest, which is precisely wrong for a harness whose job is comparing *complete* violation
  sets.
- **Consequences.** One solve per comparison instead of a loop of them. The function asserts that a
  fully fixed roster leaves the model feasible, which is a live check that every hard constraint
  carries a literal — an ungated constraint makes the model infeasible there, and the assertion says
  why. Presolved-away pairs never become variables and so can only be reported from the exclusion
  table, which is `D-045` and is why that table is retained.
- **Date.** 2026-08-12.

## D-045 — Presolve retains exclusion reasons; unrepresentable rosters compared on eligibility only

- **Decision.** Presolve keeps a map from each excluded pair to the rule IDs that excluded it.
  Rosters that assign such a pair are compared between the readings on **eligibility findings only**.
- **Alternatives.** Discard the reasons, since the variable is gone anyway. Compare those rosters in
  full and make the model account for the assignment somehow.
- **Reason.** A removed pair can never be reported by a constraint that does not exist, so without
  the map an assignment to an ineligible person is invisible rather than rejected. The comparison
  narrowing is larger than it first looks, and it took a failing test to state correctly: because the
  pair is not representable, the model cannot count that body toward **anything** — headcount, weekly
  or daily hours, a consecutive-day streak, a rest gap. Every aggregating rule is affected, not just
  coverage. The only thing the model has an opinion about is *why the pair was excluded*.
- **Consequences.** Nothing aggregate is compared on those rosters. The loss is bought back by
  comparing the two eligibility derivations directly — pair by pair, over every instance variant, for
  `R-AVAIL`, `R-SKILL`, `R-FLEXI-ELIG` and `R-DIMONA-FLX`. That is a stronger test than the headcount
  comparison would have been, because it localises a disagreement to the eligibility rule that caused
  it rather than surfacing it as a coverage mismatch three rules away. The narrowing may not be
  widened without a new record.
- **Date.** 2026-08-12.

## D-046 — `R-CONSEC-DAYS` compared at `(rule, employee)` granularity in the harness

- **Decision.** For this rule alone, the harness drops the day coordinate and compares at
  `(rule, employee)`.
- **Alternatives.** Compare at full coordinates, and change one reading until it matches the other.
- **Reason.** The two readings genuinely report different things and both are right. The checker
  walks days and names the first breaching day of a run; the model gates every sliding window that
  breaches, so a long run yields one finding on one side and several on the other. Forcing agreement
  would mean rewriting one reading to imitate the other, which is the one thing independence forbids.
- **Consequences.** Stated cost: a day-coordinate error in this one rule is not caught by the
  harness. Recorded rather than silently narrowed, and it cannot be widened without a record here. This is
  the smaller of the two comparison narrowings — `D-045` is the larger.
- **Date.** 2026-08-12.

## D-047 — Soft coverage floor collapses the infeasibility surface to pins and impossible parameters

- **Decision.** Recorded as a consequence of `D-018` rather than as a separate choice: with the
  coverage floor soft, a cold solve is essentially never infeasible.
- **Alternatives.** None. This is a finding, and the alternative was not noticing it until T4.
- **Reason.** Once the floor is soft, the empty roster satisfies every hard rule, so a shift nobody can
  staff comes back as a priced shortfall rather than as a refusal. What remains able to produce
  infeasibility is narrow, and both causes are structural rather than combinatorial: an incumbent whose
  past already breaks a rule (`R-PIN-PAST`), and a parameter that no roster can satisfy at all, such as
  a weekly rest window wider than the horizon.
- **Consequences.** **This re-scopes T4.** The explainer's ordinary job is explaining *shortfalls and
  their cost*, not explaining infeasibility; infeasibility is the rare case, and an explainer built for
  the rare case first would be built for the wrong one. It also constrains the ground-truth layer: a
  micro-instance intended to be infeasible has to reach infeasibility through one of those two doors,
  because nothing else leads there.
- **Date.** 2026-08-12.

## D-048 — Infeasibility core is sufficient, not minimal; minimisation deferred to T4

- **Decision.** T1 reports CP-SAT's `sufficient_assumptions_for_infeasibility` as it comes. No
  minimisation.
- **Alternatives.** Iterative deletion — solve, drop a gate, re-solve, keep what stays necessary —
  to reduce the core to a minimal one.
- **Reason.** CP-SAT returns a set of assumptions that explains the infeasibility with no guarantee
  it is the smallest. T4's explainer is specified against a *minimal* core, and the reduction is a
  loop of solves layered on top rather than a change to the model, so it belongs with the explainer
  that needs it.
- **Consequences.** A sufficient core can name rule instances that are not actually necessary to the
  conflict — acceptable for T1's diagnostic use, not acceptable for a planner-facing explanation. The
  gap is recorded in `model.md` so it is a known cost at the start of T4 rather than a discovery in
  the middle of it.
- **Amended by `D-100`.** The deferral was right and the diagnosis was wrong. Measured at T4, the
  sufficient core is 150-plus gates — far worse than anticipated — but iterative deletion is not what
  fixes that. Setting the objective before asking is what inflates it.
- **Date.** 2026-08-12.

## D-049 — Weighted sum, not lexicographic ordering

- **Decision.** Hard rules are constraints; shortfall, disruption and cost are summed with weights.
  Not a lexicographic ordering.
- **Alternatives.** Lexicographic — feasibility, then disruption, then cost — which guarantees
  disruption is never traded away.
- **Reason.** That guarantee is the problem. Under a lexicographic ordering no cost saving, however
  large, buys a single unit of disruption. This collapses the disruption/cost Pareto frontier to one
  point, and that frontier is the headline chart in [`benchmarks.md`](benchmarks.md). An objective
  that makes the money chart trivial is the wrong objective.
- **Consequences.** The weights have to sit on one scale, which forces the shortfall term to dominate
  by a derived bound rather than by a number that merely looks large (`D-057`). The exchange rate
  becomes a parameter to sweep rather than a constant to defend (`D-050`). Four levels result, and
  only two of them trade: hard rules are not in the objective at all, shortfall is priced and must
  dominate, and disruption and cost trade against each other.
- **Date.** 2026-08-12.

## D-050 — Exchange rate swept to trace the frontier rather than fixed by assertion

- **Decision.** `cost_weight` is swept across a range to trace the frontier. The shipped default is
  stated as a hypothesis with its reasoning attached, not presented as correct.
- **Alternatives.** Pick one exchange rate and defend it. Tune it until the output looks reasonable.
- **Reason.** The rate is a tenant's business judgement, not a fact about rostering. The honest claim
  is not "here is the correct exchange rate" but *"we cannot know yours; here is the frontier, and
  here is our default and why"*. Tuning until the output looks reasonable is the same act with the
  reasoning taken out, and it produces a number nobody can argue with because nobody knows where it
  came from.
- **Consequences.** The default — one published change at short notice is worth about two hours of
  overtime premium — is written down so it can be argued with. Calibrating it needs the T2 corpus:
  real planners choosing between paying overtime and moving someone reveal their own rate. Until
  then `cost_weight` ships at **0**, so the shipped objective is pure disruption and the cost axis
  only comes alive when a tenant sets it.
- **Date.** 2026-08-12.

## D-051 — Publication state as a single `published_through` cutoff, not a per-slot set

- **Decision.** The caller supplies one number, `published_through`. A slot is published iff its start
  falls before it. Exactly parallel to `now`.
- **Alternatives.** A general set `published ⊆ O`, naming exactly which slots are out.
- **Reason.** One number is easy for a caller to get right, and it matches the pattern that actually
  dominates: *"the schedule is out through Sunday the 14th."* A per-slot set is more expressive and
  correspondingly easier to supply wrongly, and a wrong publication state silently misprices every
  change in the horizon.
- **Consequences.** Stated limit: a wave-published roster — some shifts in a horizon announced,
  others held back — cannot be represented. `published_through` is a special case of the general set,
  so the generalisation is additive when a tenant needs it. Publication state attaches to **slots
  rather than to assignments**, which is what makes an add cost anything at all: a published roster
  communicates rest as well as work, and being called in on a day off is among the most disruptive
  things a replan can do.
- **Date.** 2026-08-12.

## D-052 — `draft_weight` non-zero, for stable output and warm starts that resemble their hint

- **Decision.** Changes to unpublished slots carry a small weight rather than zero.
- **Alternatives.** Zero, which is what "an unpublished draft can be reshuffled freely" literally
  implies.
- **Reason.** Zero leaves the optimiser indifferent among draft rosters, and indifference costs two
  things worth keeping: stable output across runs, and a warm start that resembles its hint. A small
  weight buys both and distorts nothing, because the number of assignments is pinned by coverage
  rather than chosen freely.
- **Consequences.** A cold solve is not indifferent either, which is what makes *generation is a
  replan from an empty incumbent* produce a stable roster rather than an arbitrary one. Ships at 1
  against a `published_weight` of 10.
- **Date.** 2026-08-12.

## D-053 — D3 pairs drops with adds per (employee, day) so a move is one event

- **Decision.** Within an `(employee, day)`, `moves = min(drops, adds)`, and what is left over is
  priced as cancellations and call-ins.
- **Alternatives.** Count every changed slot on its own, as D0–D2 do.
- **Reason.** D0–D2 count a moved shift twice, once as a drop and once as an add. To the person it
  happened to it is one event — *"your Saturday moved from the morning to the evening."* D3 is the
  definition that notices.
- **Consequences.** Pairing needs a common granularity for the drop and the add, which is what forces
  the per-day weight in `D-054`. It also produces the worked divergence that makes the D0–D4 study
  real: where D2 calls a third person in for a morning (two changes), D3 prefers to move two people
  who were already working (four slots, but two *moves*). Both are defensible answers to the same
  disruption. The default ordering `W_callin > W_cancel > W_move` is a hypothesis about human
  preference, not a measurement, and it is the most falsifiable claim in the objective spec — T2's
  replay work tests it directly against what real planners chose.
- **Date.** 2026-08-12.

## D-054 — D3 weights read from the day's anchor slot — solution-independent by necessity

- **Decision.** In D3, `P` and `N` are evaluated per day, read from the day's earliest **open** shift.
- **Alternatives.** The day's earliest **affected** shift, which is the more intuitive reading.
- **Reason.** The intuitive choice is wrong twice over. The weight would depend on which slots the
  solution changed, which makes the objective non-linear. And it would be impossible to match between the
  model and an independent scorer, because one iterates variables and the other iterates changes.
  Solution-independence is not a nice-to-have here — it is what makes the two readings comparable, and
  without it stage (b) of ground truth cannot exist at all (`D-042`).
- **Consequences.** Stated cost: a move from an early shift to a late one inside a long day is priced
  by the day's earliest notice rather than by the affected shift's. The anchor lives in `domain.py`
  as a shared convention for the same reason half-open overlap does — it is a definition this project
  fixes, not a reading of the rules (`D-038`).
- **Date.** 2026-08-12.

## D-055 — D4 as convex lower bounds rather than a max-term or a piecewise construction

- **Decision.** Introduce `t_e` and lower-bound it by every segment's line —
  `t_e ≥ k·events_e − k(k−1)/2` for `k = 1 … concentration_tiers` — then minimise `Σ_e t_e`.
- **Alternatives.** A max-term over the tiers. A general piecewise-linear construction with auxiliary
  booleans.
- **Reason.** A convex function of an integer variable needs no piecewise machinery when it is being
  minimised. Because `f` is convex and the objective pushes `t_e` down, `t_e` settles at exactly
  `f(events_e)`. Linear, no products, no auxiliary booleans. The max-term is the
  `concentration_tiers = 1` special case, and it is insensitive to everything below the maximum —
  which is the opposite of what a concentration penalty is for.
- **Consequences.** `f` is the triangular numbers, so the *n*-th change to one person costs *n*. The
  tier count is a parameter, so how far the escalation runs is configurable without touching the
  encoding. This is the answer to *five changes to one person is worse than one change to five*,
  which any plain sum over changes is blind to.
- **Date.** 2026-08-12.

## D-056 — `extend` dropped from D3 — not representable with fixed shift instances

- **Decision.** Extending a shift is not a D3 change type.
- **Alternatives.** Keep it, as the outline listed.
- **Reason.** With fixed shift instances a shift's boundaries are data, so there is no roster the
  model can express in which one is extended. A change type that no solution can exhibit is not a
  change type.
- **Consequences.** It becomes representable in T5's generation mode, where boundaries turn into
  decision variables, and it is a change type only there. This is the same shape as `D-031`, which
  reclassified `R-MIN-SHIFT` for exactly the same reason: fixed shift instances remove a whole class
  of things the model is able to talk about, and both the rules and the objective have to notice.
- **Date.** 2026-08-12.

## D-057 — Shortfall-weight domination bound derived and validated, not chosen

- **Decision.** `shortfall_weight > max_{(d,s)} req[d, s] × max_change_weight`, computed from the
  instance and checked at profile load.
- **Alternatives.** Pick a large round number and assume it is large enough.
- **Reason.** Understaffing *reduces* disruption — an unstaffed shift is a shift nobody was moved
  onto. So a shortfall weight that is too low lets the optimiser buy stability by leaving shifts
  empty: a failure that looks like a tuning problem and is really an ordering error. The bound is
  computable, which is why it does not have to be guessed. Leaving one shift instance unstaffed
  avoids at most `req[d, s]` changed assignments, each worth at most the largest per-change weight
  the metric can produce.
- **Consequences.** Because it is derived it is checkable, so it is checked: a weight scale that
  violates it is a malformed request rather than a preference, and it lands in the input-validation
  layer (`D-040`). `max_change_weight` is computed by the scorer and read by validation, which is why
  validation depends on `scoring.py` and not on the model. The same bound is what makes
  generation-as-cold-start safe — disruption is constant across rosters with equal coverage, and a
  shortfall is the only thing that could break that constancy.
- **Date.** 2026-08-12.

## D-058 — Variables exist for every incumbent pair, so deviations are always countable

- **Decision.** A variable is created for every eligible pair, and additionally for any pair the
  incumbent assigned, eligible or not.
- **Alternatives.** Create variables only for eligible pairs, which is what presolve would otherwise
  dictate.
- **Reason.** Two separate things need the second case. An already-illegal past must be
  representable, or *the past itself is illegal* is indistinguishable from a clean solve. And a
  deviation from the incumbent must be **countable**: an employee who became unavailable has to be
  dropped, and that drop is disruption — without a variable the objective never sees it, and the
  model silently understates the cost of exactly the change the replan exists to make.
- **Consequences.** This was a live bug behind a green suite. Every micro-instance happened to have a
  clean incumbent, so the ground-truth layer passed while the objective was wrong; the regression
  instance is now committed. The general lesson is `D-004`'s standing limit — a ground-truth layer
  only covers the structures its instances contain. A pair that exists only to carry a pin or a
  deviation is still ineligible, which is `D-059`.
- **Date.** 2026-08-12.

## D-059 — Eligibility fixings gated, so an ineligible assignment is reportable

- **Decision.** Where a variable exists for an ineligible pair (`D-058`), the exclusion is a gated
  `x == 0` rather than an outright fixing.
- **Alternatives.** Fix the variable to zero unconditionally, which is what "ineligible" plainly
  means.
- **Reason.** An outright fixing makes a roster that assigns the pair *infeasible* rather than
  *reported*, and the differential harness needs a finding with coordinates. Same argument as
  `D-043`.
- **Consequences.** The gate is reachable only through an incumbent pin, so a core naming an absence
  means *the past itself is illegal* — a diagnostic worth having. It partially supersedes `D-020`'s
  claim that absences carry no assumption literal, and the amendment is recorded there. The model's
  gate descriptor still does not carry the absence-versus-unavailability provenance, which is a T4
  explainer obligation.
- **Date.** 2026-08-12.

## D-060 — Metric divergence requires slack: the mechanism holds, the stated instrument does not

- **Decision.** Divergence needs room to choose, and coverage tightness is a real generator knob for
  it. But the quantity this record originally proposed to test it against — the instance set's
  week-level `min_slot_slack` — does not predict divergence and is not used for the claim.
- **Alternatives.** Report the week-level correlation as the confirmation. Drop the claim.
- **Reason.** The mechanism is confirmed where it is cleanest: `tight` diverges on 0 of 6 cases,
  because a fully constrained week has one legal repair and every metric returns it. But the
  week-level minimum is a minimum over 21 slots, and the repair happens at the one the event damaged
  — a week can hold one impossible slot and abundant room everywhere else. Measured that way the
  relationship is non-monotone and the most constrained bucket has the highest conflict rate, which
  is an artifact of the instrument. Measured at the damaged slot (`metrics.repair_slack`) it improves
  to 16/40 at high slack against near-zero below, and still is not a law.
- **Consequences.** **Slack is necessary and nowhere near sufficient.** The missing condition is
  structural: D3 diverges from D2 only when a *move* is available — another open shift on the same
  day that a rostered person could be shifted to — which is a property of the damaged day rather than
  of the week or the slot. The committed set does not vary it, so the study reports a correlation and
  not a law, and a generator axis over same-day shift availability is the honest way to close it.
  `demand-spike` diverging on 0 of 6 is the same point from the other side: an added headcount is a
  pure call-in with nothing to pair against, so no move exists to be preferred.
- **Supersedes.** The forward-declared version of this record, which assumed the week-level measure
  would serve.
- **Date.** 2026-08-13.

## D-061 — Day-permutation invariance holds only on a day-decoupled cold instance

- **Decision.** The metamorphic day-permutation test asserts objective invariance only under stated
  preconditions: one shift type per day separated by more than `min_rest_hours`, no consecutive-day
  limit, weekly rest loose enough not to bind, and a **cold** solve.
- **Alternatives.** The original unqualified claim that day permutation "stays structure-consistent".
- **Reason.** The unqualified claim is false, and three separate couplings make it so. `R-REST-GAP`
  and `R-WEEKLY-REST` constrain adjacent and consecutive days. `R-CONSEC-DAYS` counts runs, and
  `{0,1,2}` is one run of three where `{0,2,4}` is three runs of one. D1 and D2 read publication state
  and notice from absolute start times, so permuting days reprices every change.
- **Consequences.** The preconditions are load-bearing and look like boilerplate, so the negative
  case is committed alongside: one employee and two *adjacent* days with `max_consecutive_days = 1`
  must leave a shift unstaffed, while the same two shifts moved apart are both coverable. That test
  exists so the preconditions cannot later be dropped as decoration. Employee relabelling, by
  contrast, is invariant unconditionally, and the difference between the two is the point of having
  both.
- **Date.** 2026-08-12.

## D-062 — Relaxation monotonicity excludes coverage, which changes the objective rather than the feasible set

- **Decision.** The *monotone objective under relaxation* property test relaxes rules but never
  coverage.
- **Alternatives.** Include coverage among the relaxable rules, since it is one.
- **Reason.** Relaxing a rule expands the feasible set without touching the objective function, so
  the optimum can only improve or hold. Relaxing coverage changes the objective itself, through the
  shortfall term — it is not a relaxation in this sense, and comparing optima across it is
  meaningless rather than merely noisy.
- **Consequences.** A monotonicity suite in which every relaxation happened to be inert would pass
  vacuously, so one test asserts that at least one relaxation actually moves the objective. The
  property depends on relaxation being expressible at all, which is what the assumption literals buy
  under `D-002`.
- **Date.** 2026-08-12.

## D-063 — Suite-wide invariant realised as a shared helper, opt-out by construction

- **Decision.** Every test that produces a solution goes through a `solved()` helper asserting zero
  **hard** checker violations and an `OPTIMAL` status. Soft violations are recorded, not asserted
  away.
- **Alternatives.** A pytest fixture or hook applying the assertion automatically to every test.
- **Reason.** Automatic enforcement cannot be opted out of, and some tests legitimately call the
  solver directly. A helper puts the opt-out in the test body, so bypassing the invariant is a choice
  someone can see in review rather than an absence nobody notices.
- **Consequences.** The `OPTIMAL` half matters more than it looks: a test comparing objectives across
  relaxations or against enumeration is meaningless on a time-limited `FEASIBLE`, and the failure
  would read as a wrong objective rather than as a truncated search. The invariant is why the
  checker's independence (`D-003`) is load-bearing for the whole suite and not only for the
  differential layer.
- **Date.** 2026-08-12.

## D-064 — Committed instances as Python constructors, not serialised — a schema is T2's problem

- **Decision.** The micro-instance set lives in `tests/micro_instances.py` as Python constructors.
  No JSON, no loader.
- **Alternatives.** Serialise the set, which is what "committed and versioned" usually implies.
- **Reason.** "Committed" here means fixed and diffable, which a module already is. A schema and a
  loader are T2's problem, and they arrive there anyway alongside the versioned *benchmark* set that
  actually needs them. Building them now would be building a T2 artifact early and filing it under
  T1.
- **Consequences.** Instances are constructed with the domain types, so a schema change breaks them
  at import rather than at parse — the better failure, and an earlier one. The golden *record* is
  serialised, because it is data rather than construction, so the two choices are not in tension.
- **The prediction was wrong, 2026-08-13.** The benchmark set did not need a schema or a loader
  either. Generation is deterministic, so `D-073` defines the set by its seeds and commits
  fingerprints rather than payloads, for the same readability reason this record gives. Serialisation
  is now owed to T3's API boundary, which needs it for its own reasons, and no earlier. The decision
  recorded above stands; only its guess about when the bill would arrive was wrong, and it is left in
  place because a prediction that failed is worth more visible than deleted.
- **Date.** 2026-08-13.

## D-065 — Seven-day horizon throughout the micro set, rather than derogating weekly rest

- **Decision.** Every micro-instance runs a seven-day horizon, including those with only two open
  shifts.
- **Alternatives.** Use a three-day horizon matching the instance's real content, and lower
  `min_weekly_rest_hours` to suit.
- **Reason.** `R-WEEKLY-REST` requires its 35-hour window inside the horizon (`D-029`), so on a
  three-day instance the rule binds everywhere for a reason belonging to the horizon rather than to
  the roster — the instance would be testing its own scaffolding. Lowering the parameter instead
  would demand a `derogation_basis`, and inventing a legal citation to quiet the validator is
  precisely the dishonesty the rule registry exists to prevent.
- **Consequences.** Free, because enumeration cost is `2 ** (employees × open_shifts)` and does not
  depend on the number of days. A convention that costs nothing and removes a whole class of
  misleading failure is worth stating rather than leaving to per-instance judgement.
- **Date.** 2026-08-13.

## D-066 — Threshold-bracketing instances for every rule limit, after mutation testing found the set blind

- **Decision.** Five instances bracket their rule thresholds from both sides, added after
  deliberately breaking the model to see what the suite caught.
- **Alternatives.** Trust that an instance exercising a rule proves the rule is enforced.
- **Reason.** It does not. The three main shift types sit on an eight-hour grid, so every gap they
  can produce is 0, 8 or 16 hours — and a rest threshold of 9 hours is indistinguishable from 11.
  Lowering `min_rest_hours` in the model passed all 82 ground-truth tests. Probing each threshold in
  turn found the same blindness in the weekly budget and the daily maximum, whose limits sat far from
  any shift-count boundary, and in the gross-versus-net distinction, which only shows up for a budget
  in `[15.0, 16.0)`.
- **Consequences.** The generalisable lesson, and the reason this is a record rather than a commit
  message: **a fixture set proves a rule exists; only a fixture at the boundary proves it is enforced
  at the right number.** It also establishes the practice — a test layer is not done until it has
  been shown to fail on a deliberate break.
- **Date.** 2026-08-13.

## D-067 — Golden rosters recorded only where enumeration proves the optimum unique

- **Decision.** The golden record commits objective values for every scenario, and the roster itself
  only where enumeration shows the optimum is unique.
- **Alternatives.** Commit every roster, which is what a golden layer normally means.
- **Reason.** Interchangeable employees create ties, and a tied optimum's *roster* is a function of
  solver version and search order rather than of the specification. Committing one would produce
  failures that are not defects — and would train everyone to regenerate without reading the diff,
  which destroys the only value the layer has.
- **Consequences.** Uniqueness is settled by enumeration at generation time, so the distinction is
  measured rather than guessed. The layer exists because stage (b) of ground truth is blind to
  anything *both* readings take as data: changing `published_weight` from 10 to 12 leaves both
  readings agreeing perfectly about a different optimum, and all 82 ground-truth tests pass. That is
  the class the golden record catches, verified by mutation rather than assumed — the weight change
  fails the golden layer and nothing else. Regeneration is a documented command rather than folklore,
  so the friction sits where it belongs.
- **Date.** 2026-08-13.

## D-068 — A benchmark case is a scenario: a published week and a disruption to it

- **Decision.** The generator emits a `Scenario` — a base week, the incumbent solved from
  it, and the instance carrying a disruption event — rather than a bare `Instance`.
- **Alternatives.** Generate instances, and let the benchmark runner inject the events.
- **Reason.** A replan is a function of a published roster and something that went wrong with it
  (`D-005`). An instance on its own cannot pose the question this project answers. Injecting events
  in the runner would also let the disruption vary independently of the week it lands on, so two
  methods could be compared on differently damaged weeks with nothing to show it had happened.
- **Consequences.** Generation runs in two phases and costs a solve per scenario, which puts a floor
  under how large the committed set can be. The scenario carries the base week as well as the replan
  instance, so the cold baselines have something to solve that never saw the incumbent — which is
  what makes "cold re-solve" a fair comparison rather than a straw man.
- **Date.** 2026-08-13.

## D-069 — The incumbent is solved cold, not hand-built

- **Decision.** The base week is solved with the shipped profile and the resulting roster becomes
  `x̄`.
- **Alternatives.** Hand-construct incumbents. Build them with a greedy heuristic.
- **Reason.** A hand-built incumbent is easy or hard for reasons nobody chose, and it encodes the
  author's idea of what a published roster looks like — the same idea that produced the model.
  Solving it makes the incumbent legal and coverage-satisfying by construction, which is what a real
  published week is.
- **Consequences.** Stated cost, because it is the weak point of the whole benchmark: **the
  incumbent comes from the system under test.** It cannot be evidence that this model matches
  practice, only that a replan beats a re-solve *given* a roster this model would produce. Replacing
  it with captured rosters is exactly what [`capture.md`](specs/capture.md) exists to do, and this is
  the strongest argument for that work being scheduled rather than optional. The base solve can leave
  shortfall at high demand, so `base_shortfall` is recorded on the scenario rather than assumed zero.
- **Date.** 2026-08-13.

## D-070 — Tightness measured against presolved eligibility, not asserted by the parameter

- **Decision.** `demand_ratio` is a generation *target*. What a scenario reports is measured after
  the fact — realised demand ratio, minimum slot slack, tight slots, and slots no roster can staff —
  computed over the pairs that survive `model.exclusions()`.
- **Alternatives.** Report the requested parameter. Measure slack against headcount.
- **Reason.** `D-060` makes coverage tightness the knob that decides whether the D0–D4 study can see
  anything at all, so a nominal figure would quietly decide the study's answer. Availability density
  and skill scarcity both change how tight a week actually is, and neither is visible in the demand
  parameter. Headcount has the same fault one level down: two weeks with identical demand and
  identical staff are not equally tight if one of them cannot staff its evenings.
- **Consequences.** The measure imports the model's presolve. That is deliberate and is not an
  independence breach — tightness *describes* an instance rather than claiming what is legal, and the
  description that matters is the one the solver is working from. Requested and measured ratios
  differ by the rounding that turning hours into whole shift instances forces, so `benchmarks.md`
  reports the measured figure and the instance set records both.
- **Date.** 2026-08-13.

## D-071 — Low demand expressed by closing slots, not by thinning a full grid

- **Decision.** When target demand falls below one person per shift instance, the generator opens
  fewer shift instances rather than keeping the whole grid open.
- **Alternatives.** Always open every `(day, shift)` pair and vary the required headcount.
- **Reason.** `O` is the set of pairs with `req > 0` ([`model.md`](specs/model.md)), so closing a
  slot is how low demand is actually expressed — and a small tenant genuinely does not run a night
  shift every day. The full grid also puts a floor under the achievable demand ratio: with 21
  instances at one body each, no scenario can be looser than that floor, which silently caps how
  loose the study is able to look.
- **Consequences.** Instance size now varies with tightness, so a solve-time comparison across
  tightness is partly a comparison across instance size, and the benchmark has to report both rather
  than attribute the difference to tightness alone. Guarded by a test asserting that measured
  tightness tracks the requested value across the range, which is what fails if the grid is forced
  open again.
- **Date.** 2026-08-13.

## D-072 — Student contracts omitted from the generator until `R-STUDENT-QUOTA` is encoded

- **Decision.** The generated contract mix is flexi and salaried. No student share.
- **Alternatives.** Generate students now, as `benchmarks.md`'s parameter list implies.
- **Reason.** `R-STUDENT-QUOTA` is a profile-gated T2 rule and is not yet encoded, so a student share
  would move no constraint. A knob that does nothing makes the instance distribution look richer than
  it is, and a study run over it would report a null that is a property of the generator rather than
  of the problem.
- **Consequences.** The contract-mix axis is narrower than `benchmarks.md` originally described until
  the rule lands, and the spec now says so rather than leaving the gap to be found in the results.
  Adding students is additive once the rule is encoded: the flexi path already proves the per-employee,
  per-day eligibility shape the quota will need.
- **Date.** 2026-08-13.

## D-073 — The benchmark set is defined by its seeds, not by serialised instances

- **Decision.** What is committed is a manifest of class names, seeds and fingerprints.
  Instances are regenerated on demand from `benchmarks/suite.py`.
- **Alternatives.** Serialise all 72 instances, which is what "committed and versioned" normally
  means.
- **Reason.** Generation is deterministic, so a class name plus a seed names an instance exactly.
  What that buys is a readable diff, and readability decides whether anyone looks — the same
  argument `D-067` makes about golden rosters. Seventy-two serialised payloads produce a diff nobody
  reads, and a diff nobody reads is not review, it is a checkbox.
- **Consequences.** The set's stability now rests on the generator staying put, which is what the
  fingerprints and `GENERATOR_VERSION` are for (`D-074`). No schema and no loader are needed, which
  contradicts the expectation recorded in `D-064`; that record is amended rather than rewritten.
- **Date.** 2026-08-13.

## D-074 — Two fingerprints per case, so a stale manifest says which layer moved

- **Decision.** Each case records a `week` digest over the generated payload and an `incumbent`
  digest over the solved base roster.
- **Alternatives.** One combined digest per case.
- **Reason.** The two move for different reasons. `week` moves when the generator moves. `incumbent`
  moves when the generator moves *or* when the solver does — a CP-SAT upgrade, or a change to the
  objective encoding. A single digest says "something changed" and leaves the reader to work out
  what, which `D-067` already names as the failure that trains everyone to regenerate without
  reading.
- **Consequences.** A `week` hash holding while incumbents move is a solver change, and the
  instances stay comparable across it. Both moving is a generator change, and they do not.
  `GENERATOR_VERSION` carries the second case explicitly, and the manifest test fails when it is not
  bumped. The independence of the two is verified by moving each input on its own: counting distinct
  hashes across the set cannot show it, because the incumbent is a deterministic function of the week
  and the seed, so the two counts match whether or not one field is a copy of the other.
- **Date.** 2026-08-13.

## D-075 — Nothing filtered out of the committed set

- **Decision.** Scenarios that guarantee a coverage shortfall, or whose base week is already short,
  stay in the set with that fact recorded per case.
- **Alternatives.** Drop them at generation time so that every committed case is a clean repair
  question.
- **Reason.** Filtering at generation prunes the distribution to the cases that flatter the thesis,
  and it does it invisibly — the resulting p95 is a p95 over a set somebody curated, and the stated
  distribution no longer describes what was measured. Which cases to exclude is an analysis
  decision, and it belongs in `benchmarks.md` where it can be argued with, not in the generator where
  it cannot be seen.
- **Consequences.** `base_shortfall`, `short_slots` and `damage` are recorded per case so the
  analysis can segment rather than pool. One class, `scarce-skill`, is chronically short by design,
  and results over it are reported separately: pooling a capacity question with a repair question
  averages two different things into a number that answers neither. The one property that *is*
  asserted is that every case poses a question at all — a scenario whose event damaged nothing scores
  as a flawless repair for all four methods and measures none of them.
- **Date.** 2026-08-13.

## D-076 — Classes differing only in the event share a base week

- **Decision.** Classes that vary only the disruption event generate the identical published week at
  a given seed, and the set asserts it rather than relying on it.
- **Alternatives.** Let every class generate its own week.
- **Reason.** The property falls out of the event parameters not being read until the base week
  already exists, and leaving it accidental is the whole risk: if the base week ever came to depend
  on the event, a difference in results across events would be a difference in *instances* and
  nothing in the benchmark would say so. The event axis measures the event only if the week is held.
- **Consequences.** The same holds one axis over — `early-notice` is the headline week at a
  different hour, so the notice axis varies notice and nothing else. Both are asserted by test, and
  a mutant that seeds generation from the event name is caught by them.
- **Date.** 2026-08-13.

## D-077 — Mutation testing as a committed harness, each mutant naming the layer that should catch it

- **Decision.** `tests/mutation.py` holds every deliberate defect this project has used to check a
  test layer. Each mutant names the layer expected to object, and one caught only by some *other*
  layer is reported as a miss rather than a pass.
- **Alternatives.** Keep it a habit, applied by hand whenever a layer is written. Point an
  off-the-shelf mutation tool at the whole codebase.
- **Reason.** A habit is not evidence. This repo already claimed every layer had been checked this
  way, and until now the claim was the only thing committed — the checks themselves were thrown
  away after each use, so nothing could be re-run and nothing could be reviewed. Naming the expected
  catcher is what makes a result mean anything: run the *whole* suite against any mutant and
  something fails, which says nothing about whether the ground-truth layer can see a wrong threshold
  or whether the golden record can see a reweighted objective. Those are separate claims and they
  need separate answers. A general mutation tool generates thousands of mutants, most of them
  meaningless, and buries the handful that encode a real hypothesis about a layer.
- **Consequences.** Adding a test layer now means adding a mutant for it — the harness is where a
  layer earns being trusted. It is deliberately outside the normal suite: it rewrites source files
  and takes minutes, so it runs when a layer is added or is about to be relied on.

  Its first full run found two holes, both behind a fully green suite. The differential harness could
  not see a wrong `min_rest_hours` in the model at all, because its only instance opened mornings and
  every gap it could express was 24 hours — `D-066`'s blind spot, in the one layer that had not been
  checked for it. And the `D-057` domination bound, which that record says is *validated rather than
  trusted*, had no test asserting it fires. Both were closed rather than filed.
- **The restore has to be verified, not assumed.** An editor's format-on-save watcher reads a file
  when it changes and writes its result later, so during a run it sees the mutated text and its
  delayed write can land *after* the restore. That happened, and it left a swapped publication weight
  in a working tree that looked clean at a glance. The harness now retries the restore until it holds
  and checks every touched path against git before exiting, reporting a leak as its own failure mode.
- **Date.** 2026-08-13.

## D-078 — The greedy baseline is solver-free by contract, and its tie-break is stated

- **Decision.** `benchmarks/greedy.py` is its own module, forbidden by an import-linter contract from
  reaching `model`, `disruption`, `scoring` or `ortools`. Its legality oracle is the checker. Its
  candidate order is written down: hours already rostered this week, then employee index.
- **Alternatives.** A function inside `methods.py`. Eligibility read from `model.exclusions()`.
  Whatever candidate order iteration happens to produce.
- **Reason.** The baseline's whole claim is that it is not the thing it is a baseline for. A baseline
  that consults the model inherits the model's bugs and stops being independent evidence, and a
  docstring saying "solver-free" is not a check. It cannot live in `methods.py`, which runs the three
  solver methods, so the contract needs a module boundary to attach to. The tie-break is stated for a
  different reason: "nearest-eligible" names an ordering that does not exist until somebody writes it
  down, and an undefined choice among equally eligible people makes the baseline's number
  irreproducible — a change to it would be indistinguishable from a change to the method.
- **Consequences.** `_legal` asks the checker only about the candidate's own assignments. Adding one
  person to one shift can break a rule about that person or overstaff the slot, and the slot is never
  filled past `required`, so the narrow question is the whole question — at a fraction of the cost of
  re-checking the full roster, which matters because this method's time is one of the reported
  numbers. The greedy loop's `is_past` skip turned out **not** to be a defence: `_legal` refuses a
  past slot anyway, because adding one is a `R-PIN-PAST` violation the checker names. The mutation
  harness established that by surviving, and the comment now says so, so that nobody later reads the
  skip as the thing protecting the past.
- **Date.** 2026-08-13.

## D-079 — Every method is scored on one yardstick, whatever it optimised

- **Decision.** All four methods are scored with `scoring.score` under the scenario's own shipped D2
  profile. A method's own objective decides what it searches for and never how it is measured.
- **Alternatives.** Score each method under the objective it optimised.
- **Reason.** Scoring under its own objective makes the comparison a tautology: each method wins the
  axis it was pointed at, the cold cost solve reports zero disruption because its profile prices none,
  and the table says nothing. There is one comparison worth making and it requires one scale.
- **Consequences.** `cold-cost` optimises a profile with every change weight zeroed and is then
  measured on a profile that prices them at full weight, which is exactly the point — that is what
  "the status quo is disruptive" means. The invariant that makes the whole table checkable follows
  from the shared scale: the disruption solve is optimal, so no method may score below it on
  `Score.total`, and `test_optimum_dominates` asserts it per case. Comparing on total rather than on
  disruption alone is deliberate: greedy reaches a lower disruption on eight cases by leaving a shift
  unstaffed, and that is a different point on the frontier rather than a better answer.
- **Date.** 2026-08-13.

## D-080 — The cost baseline keeps the incumbent attached and zeroes the change weights

- **Decision.** `cold-cost` solves the same instance, with `now` and the incumbent still attached,
  under a profile whose publication, move, cancel, call-in and concentration weights are all zero and
  whose `cost_weight` is 1.
- **Alternatives.** Solve with `incumbent=None` and `now=None`, which is the literal reading of "cold".
- **Reason.** Dropping the incumbent unpins the past. A baseline free to reassign shifts that have
  already started is not a legal roster and is not a baseline for anything — and dropping `now` also
  changes which shortfall counts as historical, so the two scores would no longer be on one scale.
  Zeroing the weights reaches the same place legitimately: the model, the coverage priority and the
  pinned past are identical, and exactly one thing differs, which is that deviation is free.
- **Consequences.** The baseline is **indifferent**, and that is the finding rather than a defect.
  The cost model is a flat rate (`D-050`), coverage is an equality with a hard ceiling, so every fully
  staffed roster costs the same and CP-SAT returns whichever it reaches first. Measured across three
  solver seeds, its disruption moves by a median of 80 points and by as much as 260 on the same case,
  on 45 of the 72 — so a single seed's number would have been an accident reported as a result. The
  disruption methods move by zero across the same seeds. Both figures are in `benchmarks.md`, and the
  seed sweep exists because of this record.
- **Date.** 2026-08-13.

## D-081 — Search time is reported separately from end-to-end time

- **Decision.** `Solution` carries CP-SAT's own wall time, and every benchmark row reports it
  alongside the end-to-end measurement taken around the whole call.
- **Alternatives.** One stopwatch around `solve`.
- **Reason.** At T2 sizes a search is about 3 ms and building the model in Python is about 7 ms
  (**since reduced to about 5 ms by `D-092`; the figure is left as measured, and the conclusion is
  unaffected because build still dominates**), so
  an end-to-end number is mostly measuring model construction — which is identical for all four
  methods. The first version of this harness reported exactly that, and the four methods came out
  equally fast for a reason that has nothing to do with any of them. The warm start's effect is
  invisible on that clock and clear on the other.
- **Consequences.** Two columns, and they answer different questions. End-to-end is the latency T3's
  service owes a caller, and it is the number that says model construction is the bottleneck at this
  size — which is what the per-tenant compiled-model cache in T3 is for. Search time is the only one
  that compares one search against another.
- **Date.** 2026-08-13.

## D-082 — The warm start helps, and only where the right clock can see it

- **Decision.** `replan.md` asked for this result to be filed either way. It is not a null: the hint
  reduces search time on 201 of 216 paired runs, with a median paired ratio of 0.907. It is
  invisible end to end, and it never changes the answer.
- **Alternatives.** Report the end-to-end number, which shows nothing, or drop the hint as not worth
  its complexity.
- **Reason.** The claim `replan.md` warned against is a warm-start speedup that is really an objective
  effect. The cold *disruption* baseline separates them, and it is the comparison used here: same
  objective, same instance, same solver seed, hint or no hint. What is left is the hint, and it is
  worth about 9% of a 3 ms search.
- **Consequences.** A 9% saving on 3 ms is not the headline the phrase "warm-started replan" suggests,
  and `benchmarks.md` says so in those words. The effect that carries the results is the **objective**:
  the disruption profile cuts mean disruption from 323 to 66 against the cost baseline, and the hint
  is a rounding error beside it. The finding also has a T5 consequence — learned warm starts are
  chasing 9% of the smaller half of the latency budget, and that is worth knowing before building
  them. Whether the hint matters at sizes where search dominates construction is unanswered here and
  needs instances this set does not contain.
- **Date.** 2026-08-13.

## D-083 — The committed set is not widened to manufacture a gap against greedy

- **Decision.** Greedy ties the optimal replan exactly on 64 of the 72 committed cases. That is
  reported as the result, and no harder scenario class is added in response to it.
- **Alternatives.** Extend the distribution with a high-damage class until the optimiser's advantage
  is visible in the headline average.
- **Reason.** The cases were committed before these numbers existed (`D-073`, `D-075`), and adding a
  class *because* the existing ones do not flatter the thesis is the same act `D-075` refuses at
  generation time, moved one step later where it is even harder to see. The honest statement is
  available and is more useful: on a one-week horizon where a disruption damages one to three
  assignments, calling the nearest eligible person is usually optimal, and the optimiser earns its
  place on the eight cases where the repair needs a chain the planner would not find — all of them in
  the tight, thin-availability, flexi-heavy or multi-absence classes, where greedy leaves a shift
  unstaffed that a chain would have covered.
- **Consequences.** The damage axis is now named as the one the distribution does not vary: median
  damage is 1 assignment and the maximum over all 72 cases is 3. A class that varies it is a
  legitimate future addition, and if it is added it is added as an axis with a stated range like every
  other, not as a repair to a disappointing table. The result also sharpens what the optimiser is
  *for* at this scale: not beating the planner on the common case, but never being the one to leave a
  shift uncovered, and being right on the case the planner cannot see.
- **Date.** 2026-08-13.

## D-084 — Benchmark results are not committed; the analysis is

- **Decision.** `benchmarks/results.json` is generated and gitignored. What the repository carries is
  the analysis in `benchmarks.md`, the hardware and versions it was measured on, and the command that
  regenerates it.
- **Alternatives.** Commit the raw rows the way `benchmarks/manifest.json` is committed. Commit the
  summary table instead of the rows.
- **Reason.** The manifest is committed because a fingerprint is exact: it changes only when the
  instances change, so a diff to it is a signal. A results row carries wall-clock milliseconds, so it
  changes on every run and on every machine. A 750 KB file that always shows a diff is a file whose
  diff nobody reads, and `D-067` is this repo's standing record of what that trains people to do.
  Committing the summary instead has the opposite fault: the summary embeds the segmentation choices
  `benchmarks.md` argues for, and a reader has to be able to redo them differently.
- **Consequences.** The numbers in `benchmarks.md` are backed by a stated command, a stated seed set
  and stated hardware rather than by a checked-in artifact, which is the honest position given they
  are timings. The comparisons meant to survive a change of machine are the paired ones — warm against
  cold, seed against seed — and they are reported as ratios for that reason. Anything that must be
  exact and diffable belongs in the manifest, which is where `D-073` and `D-074` put it.
- **Date.** 2026-08-13.

## D-085 — Metric divergence is measured as regret by lexicographic solve, not by comparing rosters

- **Decision.** Two metrics are said to disagree on a case when holding one at its optimum makes the
  other strictly worse than its own optimum. The second solve minimises `b` subject to `a`'s
  objective equalling `V_a`, which selects the best `b`-roster among **all** of `a`'s optima.
- **Alternatives.** Solve under each metric and compare the returned rosters. Compare objective
  values.
- **Reason.** A metric usually has many optimal rosters, and which one is returned is the solver's
  search order. Comparing returned rosters reports 47 of 72 cases as divergent where only 23 are —
  D0's tie set is large enough that it would "disagree" with itself at another seed. The
  lexicographic form removes the ambiguity entirely: a positive regret means *no* optimum of `a` is
  an optimum of `b`, which is a fact about the metrics rather than about the search. This is the same
  failure `D-080` records for the cost baseline, and it is worth having been caught twice.
- **Consequences.** Raw regrets are **not comparable across directions**, because D3 multiplies by
  change-type weights of 6 to 14 and D2 does not — the apparent 420-against-50 asymmetry in the matrix
  is units, and normalised against the paying metric's own optimum the disagreement is about even
  both ways. The study reports the normalised figure and says so. Every regret must be non-negative,
  which is asserted inline and independently in the test layer: a negative one means a solve is wrong,
  not that a metric is surprising.
- **Date.** 2026-08-13.

## D-086 — D4 is unexercised by the committed set, and this is recorded rather than inferred

- **Decision.** D3 and D4 never conflict on any of the 72 cases, in either direction. The
  concentration penalty is reported as **unexercised** rather than as validated or as equivalent.
- **Alternatives.** Report the zero as evidence that D4 adds nothing. Drop D4.
- **Reason.** The penalty only becomes non-linear when two events land on the same person
  (`f(1)=1, f(2)=3`), and median damage across this set is one assignment. Even `multi-absence`, which
  removes three people, gives each of them one event. A zero here is therefore a fact about the
  distribution and says nothing about the metric — reading it as "D4 adds nothing" would be inferring
  a null from an experiment that could not have produced anything else.
- **Consequences.** Any claim that D4 behaves correctly rests on the micro-instances and the golden
  record, not on the benchmark set. The same damage axis `D-083` names as missing is what would
  exercise it, which is the second independent reason to add one. Until then the study says so in
  those words.
- **Date.** 2026-08-13.

## D-087 — Symmetry breaking measured and not shipped, because the distribution has no symmetry

- **Decision.** No symmetry breaking in the model. `model.md` said this was deliberate pending
  measurement; the measurement is now in [`studies/symmetry-breaking.md`](studies/symmetry-breaking.md).
- **Alternatives.** Ship lexicographic ordering over interchangeable employees.
- **Reason.** There is almost nothing to break. Across 24 committed cases there are **3**
  interchangeable employees in total, in one case. Lexicographic ordering therefore costs about 4% of
  build time and returns a coin flip on search. But the null had to be separated from "the lever does
  not work", so it was also run on a workforce built to be interchangeable, where it is worth **20% of
  total time** — 27% off the search, paid for with a 79% larger model. The lever works; this
  distribution does not present the structure it needs.
- **Consequences.** The spec's stated reason was **partly wrong and is corrected**. It attributes the
  suppression to the disruption objective, and the objective is the smaller half: the incumbent
  roughly halves what symmetry remains (7 interchangeable employees across six cold weeks, 3 across
  24 replans), but the larger effect is the generator giving every employee an independently sampled
  budget and availability, so two employees are rarely identical before any incumbent exists. That
  also bounds how far this null travels — a real tenant with eight part-timers on identical contracts
  and open availability would have genuine orbits, and this distribution does not model that tenant.
  Revisit when a tenant profile shows a substantial group identical in contract, skills, budget and
  availability.
- **Study.** `docs/studies/symmetry-breaking.md`.
- **Date.** 2026-08-13.

## D-088 — The `regular` automaton rejected at a one-week horizon, on speed and on reporting

- **Decision.** `R-CONSEC-DAYS` keeps the sliding-window encoding. The automaton is implemented behind
  `build(sequence="automaton")` for the study and is not the shipped path.
- **Alternatives.** Adopt the automaton, which is the textbook encoding for a sequence rule.
- **Reason.** It loses on both axes. **Speed:** 20% slower to search on 24 of 24 cases, with an
  identical variable and constraint count — because at a seven-day horizon with a six-day limit the
  sliding-window encoding builds exactly **one** window per employee, so the automaton is competing
  against a single linear inequality over seven booleans. `model.md` suspected the window count would
  be small; it is one. **Reporting:** an automaton can carry an assumption literal — checked rather
  than assumed, since the API accepts calls it might not honour — but only one per employee for the
  whole week, where the window encoding names the *day* the streak breached. `violations()` compares
  gates to checker violations on the `(rule, employee, day, shift)` key, so adopting it would mean
  carving an exception into the harness that proves the two readings agree.
- **Consequences.** Revisit at a horizon longer than about two weeks, where the window count grows
  with the horizon and the automaton stays one constraint. That is not hypothetical for this domain —
  reference-period arithmetic is a multi-week rule (`D-014`, `D-033`) — but it is not the model that
  ships. `R-WEEKLY-REST` is not a candidate in either direction: it governs a continuous 35-hour free
  run measured in hours, which a day-level automaton cannot express.
- **Study.** `docs/studies/regular-constraint.md`.
- **Date.** 2026-08-13.

## D-089 — `R-REST-GAP` keeps pairwise inequalities at a one-week horizon

- **Decision.** The pairwise encoding stays. The `no_overlap` alternative is implemented behind
  `build(rest="intervals")` for the study and is not the shipped path.
- **Alternatives.** One optional interval per (employee, shift instance), inflated by
  `min_rest_hours`, under a single `add_no_overlap` per employee — the alternative `rules.md` named
  and deferred to a T2 study.
- **Reason.** It trades search time for build time and the trade does not come out ahead. The interval
  form is 23% smaller and builds 12% faster, and searches 16% slower on 24 of 24 cases; the total is
  2% better on the committed set — the threshold the measurement harness itself calls not worth the
  complexity — and **11% worse** on the larger cold instances. A lever whose sign
  depends on which half of the latency dominates is not a lever. It also coarsens the gate: a
  `no_overlap` covers an employee's whole week, where the pairwise encoding names the second slot of
  the offending pair — the coordinate the checker reports and `violations()` matches on.
- **Consequences.** **The claim behind the alternative is untested, and the study says so rather than
  claiming a null.** `rules.md` justifies it by the pair set growing quadratically *as the horizon
  grows*, and this project's horizon is fixed at one week. The larger family varies employees, and
  employees are the wrong axis — conflicting pairs are computed over slots, so adding people
  multiplies both encodings equally. Revisit with a longer horizon, not with tenant size.

  Worth recording once across three studies: `D-088`, `D-009` and this one all failed partly because
  **global constraints aggregate, and this model's gates are per rule instance**. Any encoding that
  replaces many local constraints with one global one coarsens what a failure can be attributed to,
  and that is a standing cost in a project whose T4 deliverable is an explainer.
- **Study.** `docs/studies/rest-gap-encoding.md`.
- **Date.** 2026-08-13.

## D-090 — The wire schema is its own schema, not a serialisation of the domain

- **Decision.** `service/contracts.py` defines a parallel set of Pydantic models with explicit
  conversion in both directions. The domain dataclasses are never exposed at the boundary. A request
  Pydantic accepts but `validation.py` refuses becomes a job in state `rejected`, returned with `422`
  and readable at the same URL a result would have occupied.
- **Alternatives.** Serialise `domain.Instance` directly, or make the domain types Pydantic models.
- **Reason.** `service.md` asks for versioned contracts "so a model change never breaks a caller",
  and reusing the dataclasses defeats that in one step: every internal field becomes public API, and
  renaming an attribute becomes a breaking change for every caller. The cost is a parallel file and
  two conversion functions; the benefit is that `domain.py` stays free to change and the thing that
  must not change lives in a file whose only job is to not change.
- **Consequences.** Two things JSON cannot carry had to be decided rather than discovered. An
  unbounded notice band is `null`, because `NoticeBand.within_hours` is `inf` on the last band and
  `Infinity` is not valid JSON — a strict parser at a caller would have rejected our own output. A
  `Roster` is a list of triples in sort order, so two identical rosters serialise identically and a
  response body does not depend on set iteration order.

  **The round trip is the identity, and is tested as one over four committed instances and through
  the real serialiser.** This is not tidiness: `PLAN.md` requires every solve's input, seed and
  profile version to be persisted for replay, and a wire format that cannot express something the
  solver can breaks that guarantee *silently* — the payload still parses, it just describes a
  slightly different problem. A mutant that drops `unavailability` from the round trip is caught by
  that test and by nothing else.
- **Date.** 2026-08-13.

## D-091 — Round-robin fairness across tenants, not weighted

- **Decision.** One queue per tenant and a rotation between them. Each scheduling turn takes one job
  from the next tenant that has one, so a tenant with 500 queued jobs gets one slot per rotation,
  exactly like a tenant with one.
- **Alternatives.** A single FIFO. Weighted scheduling by plan tier, contract value or queue age.
- **Reason.** `service.md` requires that "one large customer cannot starve two thousand small ones",
  and a FIFO fails it precisely when it matters: a tenant submitting 500 replans at 09:00 takes the
  next 500 slots. Weighting was rejected for now because a per-tenant weight needs a priority nothing
  in this project can justify — plan tier, contract value and queue age are all defensible and none
  is derivable from a payload. Equal shares is the honest default, and inventing a weighting to look
  sophisticated would encode a business decision nobody made.
- **Consequences.** `next_batch` is where a weight goes when there is a reason for one, and the
  rotation is the only thing that would change. Fairness is a claim about *scheduling* and cannot be
  observed in any single response, so it is asserted directly against the rotation rather than
  through the API — a FIFO passes every other test in `test_service.py` and fails only that one. The
  mutation harness carries a mutant that turns the rotation back into a FIFO.
- **Date.** 2026-08-13.

## D-092 — `Instance.window` memoised: the largest single win in the solve path

- **Decision.** `Instance.window` caches its results per `(day, shift)` in a field excluded from
  `init`, equality and `repr`.
- **Alternatives.** Leave it pure and pursue the compiled-model cache `service.md` asks for. Hoist the
  computation into each caller.
- **Reason.** Profiling `build` put **60% of its time in this one method** — about 3,474 calls per
  build to compute the 21 distinct values a one-week horizon with three shift types has. Since build
  (~5 ms) costs more than search (~3 ms) at these sizes (`D-081`), that made it the largest single
  cost in the whole solve path. It takes about **20% off build time**, measured on a cold cache per
  build: the saving is collapsing 3,474 calls to 21 *within* one build, not reuse across requests, so
  it is a production win rather than a benchmark artifact. That is larger than presolve, larger than
  the warm start, and larger than every level-1 lever in T2 — all of which compared *encodings*, which
  is why none of them could see it.
- **Consequences.** Safe without invalidation: `window` is a pure function of `(day, shift)` and
  immutable shift types, and `Interval` is frozen, so a shared instance is indistinguishable from a
  fresh one. This is the only thing in `domain.py` that is neither a data container nor a stated
  convention, and it earns the exception by being the largest measured cost in the project.

  **It broke the benchmark manifest immediately, and that is the guard working.** `suite.py`
  fingerprints instances by walking `dataclasses.fields`, so the cache leaked into every committed
  hash and made it depend on which methods had been called first. `_canonical` now walks only fields
  with `compare=True` — a field excluded from `__eq__` must be excluded from a fingerprint, or two
  equal objects hash differently. The manifest then reproduced byte-for-byte, which is also the
  cleanest evidence that memoisation changed no instance.
- **Study.** `docs/studies/model-cache.md`.
- **Date.** 2026-08-13.

## D-093 — The compiled-model cache ships enabled, and does not help replanning

- **Decision.** `compiled.ModelCache` is built, wired into the service, and enabled. It is keyed on a
  fingerprint of everything `build` reads, bounded, and **thread-local rather than shared**.
- **Alternatives.** Skip it, given the measured hit rate. Share one cache per process.
- **Reason.** `service.md` asks for it on a correct premise — building costs more than solving — but
  the remedy does not follow for the replan path, and the measurement says so plainly: **0 hits in 144
  replan solves**. A replan is triggered by a change to the model's own inputs; an absence changes
  which pairs survive presolve, which changes the variables, so a replan of a week is never the same
  model as the week. It ships anyway because the economics are one-sided — a miss costs 0.6% of a
  build, a hit saves 170× — and because the workloads that *do* repeat an instance are real: T4's
  `what_if` sweep, replay, and retries. It is enabled on those grounds, not on the grounds that it
  helps replanning, and `test_the_replan_path_does_not_hit` asserts the zero so a future hit means
  something has stopped distinguishing two models.
- **Consequences.** **Thread-local, because `CpModel` is not thread-safe.** A shared cache would hand
  the same model object to two concurrent solves whenever their fingerprints matched, and both would
  set an objective and assumptions on it at once — a data race whose output is a plausible roster.
  Thread-local storage removes the sharing instead of guarding it, so there is no lock to get right
  and concurrency stays real; the cost is one cache per worker thread.

  The key includes the incumbent, which looks like an objective input and is not: `D-058` makes
  `build` create a variable for any pair the incumbent assigned even when presolve excluded it. The
  tidy constraints-in-objective-out split is wrong in exactly that place, and wrong in the direction
  that drops the variables a deviation is counted on.

  Two test defects surfaced from the mutation harness rather than from review: an absence test that
  passed because the two instances it compared also differed in their incumbent, and a
  `clear_objective()` call that was dead because `minimize` replaces rather than accumulates. Both are
  in the study.
- **Study.** `docs/studies/model-cache.md`.
- **Date.** 2026-08-13.

## D-094 — A timeout and an infeasibility are different answers, and `solve` now says which

- **Decision.** `solve` returns three things, not two: a `Solution`, a `list[Gate]` meaning **proved
  infeasible**, or an `Unproven` meaning the search stopped with no solution and no proof. Previously
  the last two shared a type.
- **Alternatives.** Keep the two-way split and let callers infer exhaustion from an empty core. Raise
  on a timeout.
- **Reason.** An empty `list[Gate]` is type-identical to "proved infeasible, with an empty core", so
  no caller could tell a proof from a stopwatch. Three consumers turn that into a real failure. The
  fallback ladder reported *no legal roster exists* when the truth was *we did not look for long
  enough*. `methods.py` recorded a timeout as `INFEASIBLE`, which would have put a stopwatch reading
  into a benchmark as a proof. And T4's explainer is specified to consume a core and phrase it, so it
  would have narrated a conflict nobody demonstrated — the exact failure `D-013` exists to prevent,
  arriving through the data rather than through the LLM.
- **Consequences.** The ladder's cold branch reads `Unproven` and never a core, which is not merely
  defensive: **a cold solve cannot be infeasible at all**, because the coverage floor is soft and the
  empty roster satisfies every hard constraint (`D-018`). So exhaustion is the only cold failure, and
  the branch that would report a cold core is unreachable by construction. That reasoning is asserted
  by test rather than left in a comment, because it silently stops holding if the floor ever hardens.
- **How it was found.** Not by review. The ladder was given a 1 ms budget to force its lower rungs,
  and it answered "no legal roster exists" for an instance that solves in 10 ms. Nothing in the
  committed set takes more than 12.4 ms, so no benchmark, test or production payload would have
  reached this path — it needed a deliberately absurd budget, which is the same technique the whole
  rung-forcing exercise rests on.
- **Date.** 2026-08-13.

## D-095 — Finish declaration: name ratified, publication deferred

- **Decision.** T3 is declared finished. The repo keeps the name `roster-replan-optimizer`. The
  public/private fork is **deferred rather than executed**: the project stays private for now.
  `PLAN.md` is archived to `docs/archive/` and is no longer maintained.
- **Alternatives.** Rename to something shorter, such as `roster-replan`. Publish now, which was
  `PLAN.md`'s own recommended default for completion.
- **Reason.** The name is accurate and is load-bearing in three places — the package, the remote and
  every cross-reference in the docs — so renaming costs a sweep and buys a shorter URL. On
  publication, the project passes the IP-hygiene test it set itself: it is synthetic throughout, with
  no tenant data, no vendor payloads and no wage data, so "would I be fine if this went public
  tomorrow?" is already yes. The reason to wait is asymmetry rather than doubt. Publishing is
  irreversible in practice — what is published is cached and indexed regardless of a later revert —
  and staying private is not. Between two acceptable options where one can be undone, the reversible
  one is the cheaper order to take them in.
- **Consequences.** Finishing is recorded as a state of the repo rather than as an announcement, which
  is the correct separation: the work is done whether or not anyone is shown it. The declaration in
  [`finish.md`](finish.md) is complete, and it lists what did **not** ship with the same care as what
  did — capture and replay, `D-001`, the flat cost model, and T4/T5 as designed upside.

  One thing the declaration adds that `PLAN.md` did not ask for: `tests/test_specs.py`, which
  mechanises the checkable half of "all specs true". It found a broken documentation link on its
  first run, and it encodes the duplicate-ID check that would have caught `D-089` being assigned
  twice.
- **Date.** 2026-08-13.

## D-096 — The timing balance is committed and asserted; absolute milliseconds are not

- **Decision.** `tests/timings.json` records build p50, search p50 and their ratio. The test asserts
  the **ratio** within 20%, and the milliseconds only within a loose sanity band.
- **Alternatives.** Assert a band around the absolute figures, which is the obvious guard. Assert
  nothing and re-read the documents by hand after a performance change.
- **Reason.** `D-092` cut build time from about 7 ms to about 5 ms and **six documents went on quoting
  7 ms** — two specs, two studies, `benchmarks.md` and a decision record. Nothing caught it: the suite
  was green, the mutation harness was green, and `test_specs.py` checks rule IDs, decision IDs and
  links but has no opinion about numbers.

  The incident taught something narrower than *measurements rot*, and it is what shapes this guard.
  **Paired ratios did not rot.** Re-running every level-1 study after `D-092` moved the ratios by
  about a point and changed no verdict, because a ratio divides out whatever the shared baseline does.
  **The absolute figure did**, because it is a statement about the baseline itself.

  The first version of this file asserted a 40% band on the milliseconds, and it would **not** have
  caught `D-092`, whose shift was 26%. A band loose enough to survive a slower laptop is too loose to
  detect what it exists for, which makes the absolute figure the wrong quantity to assert on.
  `build / search` is the right one: it is what the prose reasons from (`D-081`, `D-093`), and a
  faster machine shrinks both sides of it. `D-092` moved it from about 2.2 to about 1.5 — a 44% drift
  against a 20% band.
- **Consequences.** The studies are left alone, which is the point: they were already robust and
  adding provenance stamps to all eight would have been friction against a failure mode they do not
  have. One quantity is guarded, and it is the one that broke.

  `test_build_still_dominates_search` asserts the *ordering* separately, because two records reason
  from it rather than merely quote it — `D-081` separates the two clocks because build costs more, and
  `D-093` rejects the compiled-model cache partly on that balance. If it ever reversed, both would
  need rereading, and a silent reversal is exactly what happened last time.
- **Date.** 2026-08-13.

## D-097 — The explainer starts with shortfalls, and answers from the checker

- **Decision.** T4's first component explains **why a shift is short**, not why a solve was infeasible.
  `roster_replan/explain.py` imports the checker and nothing else; an import-linter contract forbids
  it `model`, `disruption` and `ortools`.
- **Alternatives.** Start with the infeasibility explainer `PLAN.md` names first — assumption literals
  to minimal core to prose. Derive the reasons from `model.exclusions()`, which already retains them
  (`D-045`) and would need no recomputation.
- **Reason.** `D-047` re-scoped this before T4 opened and the measurement confirms it: with a soft
  coverage floor the empty roster satisfies every hard rule, so **a cold solve is essentially never
  infeasible**. Across the committed set, **16 of 72 cases return an optimal roster that still leaves a
  shift short — 24 unstaffed positions — and none is infeasible.** An explainer built for infeasibility
  first would be built for a case that does not occur. The minimal-core reduction `D-048` defers is
  still owed, and is now correctly ordered behind this.

  Answering from the checker rather than from presolve is the other half. An explanation derived from
  the model's own exclusion table is the solver's account of itself: a wrong exclusion produces a
  wrong explanation that agrees with it, and nothing shows. Asking the independent reading means a
  wrong exclusion makes the explanation **contradict** the roster, which is a finding rather than a
  consistent lie. The cost is recomputing what presolve knew — microseconds against a solve.
- **Consequences.** The design yields an invariant worth more than the feature. Because
  `shortfall_weight` dominates (`D-057`), an optimal solver adds anyone it legally can, so every
  person off an under-staffed slot must be blocked by something. An employee the checker says could
  have been added is not a gap in the explanation but a **defect report** — the roster is suboptimal,
  or the two readings disagree about eligibility. `Shortfall.unexplained` carries them and is asserted
  empty across all 72 cases, which makes this a fifth reading of the rules rather than a presentation
  layer: it can fail on a roster the model, the checker, the differential harness and the golden
  record all accept, because it asks a question none of them asks.

  A person blocked by two rules is counted under both. Naming one "primary" reason would imply that
  relaxing it frees them, and it does not — the report is meant to answer *what would have to change*.

  One test defect surfaced from the mutation harness: every committed roster is legal, so no
  employee's own row is ever already broken and the subtraction of pre-existing violations was a
  no-op everywhere. It matters on the one shape that does occur — an incumbent whose past is illegal
  and `R-PIN-PAST` forces the solver to keep — where without it that person's existing breach is
  reported as the reason they cannot work an unrelated shift later in the week.
- **Date.** 2026-08-13.

## D-098 — `what_if` refuses unlawful hypotheticals rather than answering them

- **Decision.** A `what_if` variant is validated before it is solved. If the change makes the instance
  unlawful — most importantly, relaxing a statutory parameter with no recorded derogation basis — the
  tool returns the refusal and its defects as the answer, and no roster.
- **Alternatives.** Solve it anyway and let the caller notice. Refuse rule relaxations outright.
- **Reason.** *Yes, hire nobody, just shorten the rest gap* is the most dangerous sentence this
  project could emit: specific, actionable, and illegal. A hypothetical tool is exactly where that
  answer would be produced innocently, because the machinery is perfectly capable of solving an
  instance whose parameters break the law — `validation.py` is what knows better, and it was already
  written.

  Refusing relaxations outright was rejected for the opposite reason: a derogation is lawful, and a
  planner exploring one is the case this tool exists to serve. The rule is *recorded basis*, not
  *never*, so the same relaxation is answered when a basis is supplied.
- **Consequences.** The change set is closed and typed rather than a free-form patch. A tool an LLM
  can call will be called with something unexpected, and a patch endpoint over `Instance` is an
  arbitrary-edit hole wearing a schema — each `Change` kind is one whose interaction with the rule
  registry was understood before it was allowed.

  A hypothetical hire is eligible on every day, which is the optimistic reading and is stated rather
  than hidden: the answer is an **upper bound** on what hiring would buy.

  `Outcome` carries the resulting roster, not only the summary numbers. That began as a testability
  fix and is the better design anyway: two tied optima under D2 share an objective *and* a change
  count, so a baseline accidentally solved at the wrong seed is invisible in every scalar and visible
  only in the roster — the mutation harness caught exactly that, twice, before the field existed.
- **Date.** 2026-08-13.

## D-099 — Profile review is deterministic, and enabling an unencoded rule is a defect

- **Decision.** Stages 2 to 4 of `config.md` — structural lawfulness, contradiction and subsumption,
  feasibility probe — are built in `roster_replan/profile.py` and run with no model available. A
  profile that enables one of the five registry-declared, unencoded optional rules is **rejected**.
- **Alternatives.** Build the natural-language parse first, since it is the visible feature. Accept
  enabled optional rules as a forward declaration of intent.
- **Reason.** `config.md` states the constraint and it decides the order: *"deterministic profile
  editing works fully with no LLM; the NL layer is an accelerator, never a dependency."* An
  accelerator built before the thing it accelerates has nothing to fall back to, and the same
  argument ordered `prose.py` before any model call — a deterministic layer that already works makes
  the model optional rather than load-bearing.

  Accepting an enabled-but-unencoded rule would be worse than ignoring it. The tenant would hold a
  profile stating that Sunday work is restricted, the solver would restrict nothing, and no test
  anywhere would fail. That is the registry describing intent rather than code — the specific failure
  `rules.md` was written to prevent — reaching production through configuration instead of through
  documentation.
- **Consequences.** Two categories, deliberately not merged. A **contradiction** is a property of the
  profile alone and is rejected: `min_period_hours` above every shift's length means no shift is legal
  whatever week arrives, which needs no solver to see. **Subsumption** is reported and not rejected:
  `max_consecutive_days` of 9 over seven days forbids nothing, the profile is valid, and the tenant
  may have meant it — but nothing else in the system would ever tell them the protection is inert.

  The probe is skipped when a contradiction was found, because solving parameters that cannot all
  hold yields an infeasibility whose cause is the profile and whose explanation would be about the
  week. It uses the **caller's** sample rather than a generated one, which also keeps `benchmarks`
  out of the runtime.

  The round-trip eval stays outstanding, and what it would prove is now stated: a round trip over
  canonical English tests a renderer against its own parser and is close to a tautology. The eval
  worth running takes free-form descriptions, and that needs stage 1.
- **Date.** 2026-08-13.

## D-100 — The objective inflates the infeasibility core; minimisation is a null on top

- **Decision.** `roster_replan/core.py` reduces a core by deletion, and asks the feasibility question
  **with no objective set**. `explain_infeasibility` reports the minimal core and how large the
  sufficient one was.
- **Alternatives.** Report CP-SAT's core as it comes, which is what T1 did (`D-048`). Minimise the
  core produced by `solve`, which is what `D-048` specified.
- **Reason.** `D-048` deferred minimisation on the grounds that a sufficient core "can name rule
  instances that are not actually necessary". Measured, that understates it badly: on five constructed
  infeasible instances `solve` returns **159 to 219 gates naming eight rules**, where the real conflict
  is two — the past is illegal, and `R-PIN-PAST` forces it to be kept. A planner handed that has no
  way to tell which two.

  But **deletion is not the lever**. Asking the same question as pure feasibility, with no objective,
  returns **2 to 3 gates** — an ~80x reduction from one line rather than from a loop of solves. Running
  deletion afterwards then drops **zero** gates on all five cases. The deferred work was aimed at the
  wrong cause.
- **Consequences.** The deletion loop is kept even though it is currently a null, for a reason worth
  separating from its measured effect: it **guarantees** minimality where dropping the objective merely
  achieves it. Every gate is shown necessary rather than observed to be few, and the guarantee is what
  the explainer is specified against.

  The two changes compose, and only in one order. Deletion costs one solve per candidate gate, so
  minimising a 160-gate core would be 160 solves; on a 2-gate core it is three, about 13 ms. **Dropping
  the objective is what makes the guarantee affordable.**

  Minimal is not smallest. A different deletion order reaches a different minimal core, so the order is
  fixed to keep the result reproducible — a planner-facing explanation needs that as much as a test
  does.

  One mutant was removed rather than left failing: "solves with the objective set" is not expressible
  as a source swap, because `_satisfiable` has no instance to build an objective from. The property is
  asserted directly instead, against `solve` itself. A mutant that cannot fail is a false pass waiting
  to happen.
- **Date.** 2026-08-13.

## D-101 — The parse is confined by the schema, and an open mapping is not a schema

- **Decision.** Stage 1 of `config.md` ships as `roster_replan/nl.py`: a narrow `StatedPolicy`
  schema, structured outputs, an injected client, and a `Proposal` that ends in a verdict rather
  than a save. Every field is designed against the schema the API **compiles**, not against the
  Python type that looks right. Derogations are therefore a list of `(parameter, basis)` pairs with
  the parameter an enum, not the `dict[str, str]` the domain uses.
- **Alternatives.** Mirror `RuleParams.derogation_basis` as a mapping, which is what the first
  version did. Take the parameter name as free text. Confine the model by instruction — *do not
  propose weights* — rather than by leaving it nowhere to write one.
- **Reason.** Measured, not reasoned: a `dict[str, str]` field compiles to
  `{"type": "object", "properties": {}, "additionalProperties": false}` — **an object that can hold
  nothing**. The field is described in the prompt and unreachable in the response. A tenant citing a
  CBA article for a nine-hour rest gap would have the citation dropped, and their lawful policy
  reported back as unlawful, with nothing anywhere saying why.

  What makes this worth a record is that no test of the surrounding logic could see it. The tests
  drive a stub client, and a stub returns whatever the test hands it — including a value the API
  would have refused to produce. So the layer reads the **compiled** schema instead, and the first
  schema mutant restores this bug.

  The enum on the parameter name is the same argument one level down. `validation.py` looks a basis
  up by parameter name, so `"rest between shifts"` validates as no basis at all: the mapping is
  populated, the check still fails, and the failure names a field that looks correct.

  The confinement this buys is structural rather than instructed. There is no field for
  `shortfall_weight`, whose scale is bound by `D-057`'s domination proof, and none for
  `enabled_optional_rules`, which `D-099` makes a defect. **A rule the model cannot state is a rule
  it cannot break**, and that holds against a bad parse, a bad prompt and a prompt injection alike.
- **Consequences.** `to_profile` translates the pairs into the mapping the domain carries; the
  domain type does not change to suit the parse.

  Unset is not a default. Every rule field is optional and a silence carries the base profile's
  value forward, which is what a tenant editing one rule means by not mentioning the others.
  `to_profile` is tested against a base that deliberately disagrees with the shipped defaults —
  against one that agrees, inheriting and falling back are indistinguishable, and the mutant that
  replaces the base with defaults survives. It did.

  `config.md`'s *the NL layer is an accelerator, never a dependency* is now an import-linter
  contract: no deterministic module may reach `roster_replan.nl` **or** `anthropic`. The SDK is an
  optional extra, so a deterministic layer importing it would need `uv sync --extra nl` to run at
  all — which is the dependency the sentence denies.

  The round-trip eval `config.md` describes is now possible and still not run. `D-099` states what
  it would be worth: over canonical English it is close to a tautology, and the version that means
  something needs free-form descriptions.
- **Date.** 2026-08-14.

## D-102 — The parse eval scores what was invented, not only what was found

- **Decision.** `benchmarks/nl_eval.py` scores every case against a **complete** expected payload:
  a field the text did not mention must come back unset, and a parse that fills one is reported as
  `invented` rather than as a near miss. The round trip `config.md` asked for is built as well, kept
  despite being close to a tautology, and reported separately rather than folded into one number.
- **Alternatives.** Score recall on the fields each case mentions, which is what an extraction eval
  usually does. Ship only the round trip, which was the promise. Ship only the free-form half, since
  the round trip proves little.
- **Reason.** Recall measures the wrong failure. A parse that misses a stated rule produces a
  profile the tenant can see is incomplete; a parse that supplies eleven hours nobody mentioned
  produces one that looks exactly like a policy they wrote, and the rule is enforced against real
  people until somebody reads the document closely. The prompt already forbids supplying defaults
  and `to_profile` treats unset as inheritance — this is the measurement that would catch either of
  them being wrong, so it has to be able to fail in that direction.

  Keeping the round trip is a smaller point with the same shape. It cannot prove comprehension —
  same author both sides — but it does prove **coverage**: a field `describe` forgets, or one the
  schema cannot hold, does not come home. Its profiles disagree with the shipped figures for the
  reason `D-101` gives, and the same claim is asserted with no API in `tests/test_nl.py`, so the
  live run adds exactly one thing: whether a model can read the rendering back.

  Four cases state no policy at all. They ask for a weight `D-057` bounds, for a rule `D-099` leaves
  unencoded, and once as an instruction rather than a description. Those are the cases that test the
  claim worth testing — that confinement is structural — and the only correct answer to each is to
  report it as something the schema cannot say.
- **Consequences.** The eval needs a key and is not part of the suite, so its scoring is what breaks
  silently. `tests/test_nl.py` therefore tests the scorer: invented and missed are distinguished,
  `unclear` is scored present-or-absent because its wording is the model's, and the round trip is
  shown failing. **An eval that cannot fail measures nothing**, and this one is only ever read when
  it disagrees with a model.

  Two things it does not prove, stated here rather than discovered later. It does not measure Dutch
  beyond two cases, which is a smoke test and not a claim about the language. And every expected
  payload is one reading of an ambiguous sentence — a disagreement is a finding to argue with, not
  automatically a defect in the parse.

  Not run at the time of writing: this machine has no key. The result belongs in
  `docs/studies/nl-parse.md` and in the studies index when it is.
- **Date.** 2026-08-14.

## D-103 — `unclear` is for what could not be said, not for what was assumed

- **Decision.** `StatedPolicy.unclear` carries only what the schema cannot express or what the text
  leaves unresolved. An assumption the parse **resolved** belongs in the field it resolved to, and a
  silence is not unclear — an unset field already reports that the text did not mention it. The
  field description and `SYSTEM` say so, and `PROMPT_VERSION` moved to `nl-2026.2`.
- **Alternatives.** Leave the description as it was and relax the eval, since both failing cases had
  extracted every figure correctly. Score `unclear` only on the cases that ask for something
  unsayable, and ignore it elsewhere.
- **Reason.** Measured (`studies/nl-parse.md`). The first run scored 16 of 18, and **both failures
  were this field** — the figures were right in every case. *"Less than a day's warning ... four
  times as bad"* parsed to 24 hours and a multiplier of 4, and then filed a note saying a day had
  been interpreted as 24 hours. A shift catalogue parsed correctly and then filed the text's
  silences: no weekly rest stated, no minimum shift length stated, and so on.

  The old wording invited it — *"anything the text asks for that this schema cannot express, or that
  is genuinely ambiguous"* reads perfectly well as *log every assumption you made*. So this is a
  defect in the schema rather than in the model, which is the reason it is fixed there.

  It matters because of what the field is **for**. A planner reads `unclear` to find the one thing
  the system could not take on. A profile that parsed cleanly and comes back with five caveats about
  what the text did not say trains them to skim the field, and the note that mattered — in the same
  run, that a Late shift ending at 23:00 before an Early at 07:00 leaves eight hours of rest — is the
  one they skim past.
- **Consequences.** The eval scores `unclear` as present-or-absent on every case, including the ones
  that should report nothing. That strictness is deliberate: it is what turned a pair of passes into
  a finding. Both cases passed on re-run with the extraction unchanged, so the correction cost
  nothing in what the parse reads.

  One failure in that run was **the eval's fault and is recorded as such**: shift labels came back
  `early` and `late` where the eval expected `Early` and `Late`, from a text reading *"an early one
  ... and a late one"*. The schema calls that field the tenant's own name for the shift, so the
  model's casing is at least as faithful as the author's. Labels are now compared without case.
  `D-102` said in advance that a disagreement is a finding to argue with rather than a defect; this
  is that clause being used, and it went both ways in the same run.

  `PROMPT_VERSION` exists for exactly this and has now been exercised once: a proposal made before
  today carries `nl-2026.1` and is not comparable with one made after it.
- **Date.** 2026-08-14.

## D-104 — Two of T5's four items are retired on measurements already taken

- **Decision.** **LNS and learned warm starts are retired**, not deferred: this project will not
  build them, and the reason is measurement rather than scope. **Generation mode and fairness
  objectives stay open** — nothing here has measured them, and they are product capabilities rather
  than solver improvements. `PLAN.md` is archived and is not edited; this record is where T5 now
  stands, alongside the postscript in `finish.md`.
- **Alternatives.** Retire T5 whole, which is the tidier story. Leave all four open, on the grounds
  that upside costs nothing to keep listed.
- **Reason.** **Large-neighbourhood search improves a solution the solver cannot prove optimal in
  the time available. Neither half of that sentence is true here.** The time-budget study ran 2,160
  solves at 1s, 5s and 30s and **every one returned `OPTIMAL`**, longest search 12.4 ms. There is no
  quality gap for a neighbourhood search to close and no time pressure creating one. Greedy repair —
  solver-free, by contract — already **ties the optimum on 64 of 72 committed cases** (`D-083`),
  which says the same thing from the other end: this instance distribution is not hard.

  **Learned warm starts are the weaker of the two.** `D-082` measured warm starting at **9% of
  search time**, invisible end to end, on a search that runs in milliseconds. Learning a better one
  optimises nine per cent of twelve milliseconds. The machinery to train it would exceed the thing
  it optimises by orders of magnitude, and the project has already rejected three levers on smaller
  margins than that (`D-087`, `D-088`, `D-089`).

  Keeping the other two is not hedging. **Generation mode** — building a roster with no incumbent —
  is a mode this system can already solve for, since the cold cost baseline in `benchmarks.md` does
  exactly that; what is missing is the product surface, not the capability. **Fairness objectives**
  are untouched by anything measured here: `D-091`'s round-robin fairness is across *tenants in the
  queue*, and says nothing about how unsocial shifts fall across *people*, which is the fairness a
  planner and a works council actually argue about.
- **Consequences.** What would reopen LNS is stated, so the retirement is falsifiable rather than
  final: **a distribution where the solver stops proving optimality.** Longer horizons than one
  week, tenants past the 8–25 employee range, or a cost axis with real wage data — any of those
  could produce instances where a neighbourhood search has something to do. The measurements above
  are about *this* distribution, and `D-086` and `D-089` already record the same limitation for
  other levers.

  This also removes the last reason to treat the benchmark set as fixed. It was built to compare
  methods; a distribution that never produces a hard instance is now a finding about the generator
  rather than a property of the problem.

  **Amended by `D-105`.** That thread was pulled the same day. The generator's whole range was
  swept, and no setting it can express makes the search hard — so the "64 of 72" cited above is
  superseded by "71 of 84", and the retirement rests on a swept range rather than on one sample of
  it. The conclusion is firmer; only the citation moved.
- **Date.** 2026-08-14.

## D-105 — The coverage axis is sampled where the answer changes, not only at its ends

- **Decision.** Two classes added — `busy` at 0.80 and `overloaded` at 0.95 — taking the committed
  set from 72 cases to 84. Existing instances are untouched and `GENERATOR_VERSION` stays at 1: the
  generator did not move, the sampling did. The greedy comparison is re-measured over all 84. The
  other T2 analyses are not, and this record says so rather than letting a widened set be read as a
  wider basis for them.
- **Alternatives.** Leave the set alone, since it was built for attribution and does that well. Add
  **conjunction** classes — high demand together with scarce skills and thin availability — which
  was the obvious way to make instances harder and was the plan when this work started.
- **Reason.** The set held 60 of its 72 cases at a demand ratio of ~0.70, with nothing between 0.73
  and 0.89: one tightness level and two deliberate outliers. That follows from the one-axis-at-a-time
  design, which is right for attribution and blind to the region where methods separate. Measured
  along the axis, greedy ties the optimum on **6 of 6 seeds at 0.70 and 3 of 6 at 0.95**, so
  **"greedy ties 64 of 72" was substantially a statement about where the set looks.** Over 84 it is
  71, and the 13 losses are the original 8 reproduced exactly plus 5 in the new band.

  **The conjunction idea was measured and rejected, which is the more useful half of this record.**
  Piling demand, skill scarcity and thin availability together produces weeks that are
  *structurally* short — slots no roster can fill — and there greedy ties **6 of 6 at every setting
  tried**, because both methods leave the same unavoidable holes. Hardening in that direction makes
  the benchmark blind rather than sharper, and it would have been easy to read the resulting ties as
  a finding about greedy.

  It does not make the **search** harder either, which was the original motivation and is now swept
  rather than assumed: demand at 105% of capacity, minimum slot slack of −7, 40 employees, all three
  pressures at once — every configuration returns `OPTIMAL` in 3 to 11 ms, and the crunch cases run
  *faster* than the baseline because the shortfall variables absorb what search would otherwise
  explore. Solve time tracks instance size, weakly, and tightness not at all.
- **Consequences.** `D-104` retired LNS on the grounds that nothing here stops the solver proving
  optimality, citing the old 64 of 72. That citation is superseded by the 71 of 84 above, and the
  conclusion is **firmer** rather than weaker: it now rests on a swept parameter range instead of an
  inference from one sample of it. What would reopen it is unchanged and still unfound — a longer
  horizon, or a tenant an order of magnitude past the 8–25 this product targets.

  The other T2 analyses — D0–D4 divergence, the warm start, presolve, the time-budget curve — were
  measured over the 72 and are not re-run here. They are not wrong, and their basis is stated
  wherever they appear; the two new classes simply sit outside it. Re-running them is cheap and is
  the obvious next thing.

  The frontier table in `benchmarks.md` is regenerated over 84. The twelve original classes
  reproduce their committed numbers exactly, which is worth more than the two new rows: it says the
  set is stable and that the new rows are a widening rather than a different measurement.
- **Date.** 2026-08-14.

## D-106 — `D-060` confirmed on a curve, and divergence is not monotone in slack

- **Decision.** The D0–D4 study is re-run over the 84 cases `D-105` produced, and
  `studies/disruption-metrics.md` is updated from that run. `D-060`'s mechanism — metrics can only
  diverge where there is slack — is recorded as **confirmed** rather than merely supported. The
  study's headline is unchanged in substance: divergence is real, severe, and entirely between
  D0/D1/D2 and D3/D4.
- **Alternatives.** Leave the study on its 72-case basis and note that the new classes sit outside
  it, which is what `D-105` said would be acceptable in the interim.
- **Reason.** The old set held exactly **one** class at the tight end of the coverage axis, and a
  single zero cannot separate *tightness* from something peculiar to `tight`. With `busy` at 0.80 and
  `overloaded` at 0.95 the axis has five points, and they make a shape: 3/6 at 0.35, **4/6** at 0.70,
  3/6 at 0.80, then **0/6** at both 0.90 and 0.95. `overloaded` reaching zero independently of
  `tight` is the observation that upgrades `D-060` from a mechanism the data was consistent with to
  one the data demonstrates.

  **The unpredicted half is the loose end.** `loose` at 0.35 — the slackest weeks in the set —
  conflicts *less* than `headline` at 0.70. Slack alone was never the claim, but more room reading as
  less disagreement wants an explanation, and `D-071` supplies it: low demand is expressed by opening
  **fewer shift instances** rather than by thinning a full grid, so a loose week offers fewer shifts
  on the damaged day for D3 to move anybody into. Divergence needs slack *and* somewhere to put
  people; the loose end gains the first and runs out of the second.

  That is the same missing condition this study already named — whether a **move** exists on the
  damaged day — reached from the opposite direction. Both ends of the coverage axis suppress
  divergence, for opposite reasons, and the middle is where the metrics have something to argue
  about.
- **Consequences.** The rate barely moved: 26 of 84 against 23 of 72, 31% either way. The
  structure reproduced exactly — zero conflict inside D0/D1/D2, zero inside D3/D4, ~100% relative
  regret in both directions across the divide. **`D-086` stands unchanged: D4 is still unexercised**,
  0 of 84 against D3, because concentration needs two events on one person and median damage here is
  one assignment. A wider set did not fix that and was never going to; only a damage axis would.

  What this does **not** do is turn the correlation into a law, and the study still says so. The
  condition that predicts divergence is a property of the damaged *day*, the generator does not vary
  it, and `D-085` already names the same-day shift-availability axis as the honest way to close it.
  This record adds evidence for where that axis matters and does not substitute for it.
- **Date.** 2026-08-14.

## D-107 — The rest of T2 re-run over 84: everything reproduces, and the sampling bug did not

- **Decision.** The analyses `D-105` left on a 72-case basis are re-run over the widened set:
  presolve, symmetry, the automaton, patterns, the rest-gap encoding, the coverage floor and the
  time-budget curve. **All reproduce.** One code change came out of it: `studies.py` now names its
  cold sample instead of slicing `CASES[:6]`, and `specs/service.md` carries 15.4 ms where it carried
  12.4. The re-measurement debt `D-105` recorded is closed.
- **Alternatives.** Trust the reproduction. Every one of these studies is a lever comparison on the
  same model, the widening added two classes at one end of one axis, and today's sweep had already
  shown the solver insensitive to everything the generator can express.
- **Reason.** That expectation was right about the levers and would have missed the thing worth
  finding. `studies.py` selected its cold instances **positionally** — `CASES[:6]` over a dict — so
  inserting `busy` and `overloaded` after `tight` pushed `large/0` and `scarce-skill/0` out of the
  sample without touching a line of study code. Two results moved as a consequence, and **both read
  as findings**: the symmetry study's cold count fell from 7 interchangeable employees to 0, and the
  pattern study went from failing on 5 of 6 cold cases to 6 of 6. The first would have been reported
  as the generator suppressing symmetry even harder than `D-087` found; the second as a stronger
  rejection of pattern encoding. Neither is true. With the sample named, the cold count is 7 again
  and patterns fails on 5 of 6 again, both exactly as committed.

  **A sample that changes membership when an unrelated class is added cannot be compared with its own
  previous run**, and nothing in the harness said so — the studies kept reporting confidently against
  a set that had quietly moved underneath them. That is the same shape as `D-074`'s fingerprint
  argument, arriving in the one place fingerprints do not reach.
- **Consequences.** The reproductions, for the record: presolve 28% off build and 14% off search on
  28 of 28 (was 28% and 16% on 24 of 24); symmetry unchanged at 3 interchangeable employees and 20%
  on a workforce built to be symmetric; the automaton 19% slower on 28 of 28; the rest-gap total
  still flipping sign by instance family. Nothing here changes a shipping decision.

  Two figures moved enough to matter, both **upward and explicably**. The longest search went 12.4 ms
  → **15.4 ms**, because `busy` and `overloaded` open more shift instances than the 0.70 baseline
  (`D-071`) — a latency claim measured on a distribution missing its own busy end was mildly
  optimistic. And a hard coverage floor could not answer **18 of 84** cases where it could not answer
  16 of 72, holding at about a fifth. Both supersede the figures cited in `D-018`, `D-024` and
  `D-094`, which stay as written; `specs/service.md` is a spec rather than a record and is updated in
  place.

  The time-budget result came back stronger rather than merely intact: all **2,268** solver runs
  `OPTIMAL`, and **no answer changed with the budget on any of 756 (case, method, seed) triples**.
  The three budgets are indistinguishable case by case, not just uniformly optimal.
- **Date.** 2026-08-14.

## D-108 — Fairness is a third thing, and it pays for understaffing like everything else

- **Decision.** T5's fairness objective ships: a rolling balance of unpopular shifts, carried in its
  own `Fairness` dataclass on the instance rather than inside `Disruption`, encoded by
  `disruption.fairness_terms` and read back independently by `scoring.fairness_of`. Which shifts are
  unpopular is **declared by the profile**, and each employee carries
  `unpopular_shifts_before_horizon` so the balance is struck over a window wider than the horizon.
  `D-057`'s domination bound grows a term to cover it.
- **Alternatives.** Add the weights to `Disruption`, which already holds every other objective
  parameter. Derive unpopularity from the shift times — evenings and weekends — instead of asking.
  Balance with a `max − min` range term instead of a convex penalty.
- **Reason.** **This repo already had two things called fairness and this is neither**, which is why
  it gets its own type rather than three more fields on `Disruption`. `D-091`'s round-robin is
  fairness between *tenants in the queue*; D4's concentration spreads *the changes a replan makes*.
  Both are about the replan. This one is about the roster — who works the shifts nobody wants, across
  weeks. A tenant can want any one of the three without the others, and folding them together would
  make that impossible to say.

  **Unpopularity cannot be derived.** A late shift is a burden in one restaurant and the shift people
  compete for in another; a Sunday is unpopular in a bakery and normal in a hotel. Computing it from
  the clock would encode one tenant's culture as arithmetic, in the one part of this system that is
  supposed to be policy-as-data.

  **Convex, not a range.** `replan.md` already rejects the max-term for D4 — it is the `tiers = 1`
  case and is blind to everything between the extremes — and the same argument applies here: a range
  term equalises the two ends and ignores everyone in the middle. The convex escalation is reused
  wholesale, including `D-055`'s lower-bound encoding.
- **Consequences.** **Fairness gives the optimiser a second reason to leave a shift empty**: an
  unstaffed unpopular shift is one nobody's rolling count went up for. That is `D-057`'s failure mode
  arriving through a new door, so the bound now reads
  `req × (max_change_weight + fairness_weight × fairness_tiers)` and a weight scale that breaks it is
  a malformed request, not an aggressive preference. `fairness-escapes-the-domination-bound` is the
  mutant that holds it.

  **The escalation flattens past `fairness_tiers`**, and the limit is stated in `replan.md` and
  asserted by test rather than left to be discovered: everyone whose rolling total already exceeds the
  tier count sits in the linear region where the term cannot distinguish them, so a window long enough
  to push the whole workforce past it switches fairness off while still looking configured.

  **Every `week` fingerprint moved and no `incumbent` did.** Adding a field to `Employee` changes the
  serialised payload for all 84 cases while the solved rosters and every measured field — demand
  ratio, slack, shortfall, damage — are identical. `D-074` named two patterns, a solver change and a
  generator change; this is a third, a **schema** change, and the split diagnosed it exactly. Results
  taken before it remain comparable, so `GENERATOR_VERSION` stays at 1 and the manifest is regenerated
  with this record as its justification.

  The committed set cannot exercise this term, and that is recorded rather than worked around: its
  evenings require a scarce skill, so the employees with no late shifts are the ones who *cannot work
  them*, and a balanced roster there is indistinguishable from an unbalanced one that ran out of
  eligible staff. The behavioural tests therefore run over `identical_workforce`, on the same argument
  `D-087` used for symmetry breaking — a lever needs an instance that contains the structure it
  exploits before a null over the committed set means anything.
- **Date.** 2026-08-14.

## D-109 — Generation ships as the cold-start case, and the spec's derivation of it was wrong

- **Decision.** Generation mode is T5's last item and needs no formulation, no mode flag and no second
  route: a caller omits `incumbent` and `now`, and validation already accepts that as a cold solve.
  What ships is the claim made **testable** — `tests/test_generation.py` holds it at the solver, the
  ladder and the service — plus a correction to the derivation `replan.md` had been carrying.
- **Alternatives.** Add a `/v1/rosters` endpoint, or a `mode: "generate"` field, so the capability is
  visible in the API rather than implied by two omitted fields.
- **Reason.** A second route over the same solve would contradict the thing this design is *for*.
  `replan.md`'s argument is that generation is not a special case, and the honest way to ship that is
  to prove the existing surface carries it, not to add a surface that implies otherwise. The service
  test is the load-bearing one: "no second formulation" would be true of `solve` and false of the
  product if a cold payload could not get through the queue, and nothing had ever checked.

  **Testing it found the spec wrong about why it works.** The derivation said cold disruption is a
  positive constant — every assignment an add at `draft_weight`, the count pinned by coverage — and
  that a shortfall would reduce it, with `D-057`'s domination bound stopping that from mattering.
  Measured, `scoring.disruption_of` short-circuits to **0** when there is no incumbent, so the
  disruption axis is flat at every coverage level. Both readings rank equal-coverage rosters the same
  way, which is why nobody noticed, but they are different claims and only one of them is the code's.

  The consequence is that the caveat was describing a risk the implementation cannot have: **a cold
  shortfall buys nothing on the disruption axis**, because there is nothing there to buy. The
  shortfall term still prices the missing coverage. The true statement is narrower than the one the
  spec made, and narrower is the point.
- **Consequences.** With disruption flat and `cost_weight` at `0` (`D-050`), the objective a cold
  solve minimises is **entirely the peak-workload tie-breaker** — measurably so: on a cold week the
  tie-breaker's value *is* the objective value. `replan.md` said generation "reduces to cost", which
  is true only once wage data exists; today it reduces to the term beneath cost. That is a second
  place where a spec sentence was accurate in principle and vacuous in practice, and `D-050` is
  already the record for why.

  Generation reaches the `exact` rung, and keeps the ladder's "never return nothing" promise for a
  reason worth restating: a cold solve cannot be infeasible, because the empty roster satisfies every
  hard rule once the coverage floor is soft (`D-018`). The lower rungs remain replan-only — greedy
  repairs an incumbent and last-known-good returns one — so generation does not gain a fallback, it
  simply never needs one.

  **T5 is now closed.** LNS and learned warm starts retired on measurement (`D-104`, `D-105`),
  fairness objectives shipped (`D-108`), generation shipped here. Nothing in `PLAN.md` remains
  unbuilt except the items `finish.md` lists as externally blocked.
- **Date.** 2026-08-14.

## D-110 — A horizon longer than a week is refused, because both readings would agree it is legal

- **Decision.** `validate_instance` rejects `days > 7`. Shorter horizons stay legal and are answered.
- **Alternatives.** *Leave it unguarded*, on the grounds that every caller in this repo supplies seven
  days and the generator hard-codes it. *Assert it in the model*, where the encoding actually makes the
  assumption. *Fix the two rules instead*, scoping them to a week so any horizon is answerable.
- **Reason.** `R-MAX-WEEKLY` and `R-WEEKLY-REST` are week rules, and both readings scope them to the
  **horizon**. The model sums an employee's whole instance against one `max_hours_this_week` and asks
  for one 35-hour window anywhere in the horizon; the checker sums the same roster and measures the
  longest free run in the same span. At seven days those two scopes are the same span and the
  encodings are right. Past seven they separate, in the weak direction: 35 hours of rest inside four
  weeks satisfies a rule that means 35 hours inside each of them, and no supplied value can make one
  budget mean "this much per week" when the sum runs over four.

  What makes this worth refusing rather than documenting is that **nothing in the suite could catch
  it**. The differential harness compares two readings that are wrong in the same direction, so it
  reports agreement. Brute-force ground truth enumerates against the same predicates. This is the
  shared-*assumption* form of the failure `domain.py` forbids for shared thresholds — where the
  discipline is written down, seven days was never named as a threshold at all, because it does not
  appear as a number in either reading.

  Asserting it in the model was rejected for where it puts the answer: an assertion is a crash, and
  this is a caller supplying a payload the service cannot price. That is the definition `D-040` gives
  for input validation — no different roster fixes it — so it is an `InputDefect` with a field path
  and a stated bound, reaching the caller through the same channel as every other malformed request.

  Fixing the rules is the right end state and is not this record. It changes the payload schema, both
  readings, the generator and four specs, and it should be measured rather than assumed — the claim in
  `rules.md` that a longer horizon "multiplies instance size by an order of magnitude and destroys the
  interactive latency" is the one major rejection in this project written without a measurement behind
  it. The guard is what makes deferring that honest instead of silent.
- **Consequences.** `rules.md` records the horizon scope of both rules as enforced rather than assumed,
  and `D-029`'s conservatism note now has its opposite number: short horizons are too strict and
  answered, long ones are too weak and refused. A test asserts that the checker certifies a two-week
  roster whose second week has 33 hours of rest, which is the blind spot stated as a fact rather than
  as a worry, and a mutant asserts the guard cannot quietly stop firing.

  Generation mode (`D-109`) inherits the bound: a cold solve over a month is refused for the same
  reason a replan is. That is a real restriction on the feature and is stated here rather than
  discovered.
- **Superseded in part by `D-111`.** The two rules are now scoped to the week in both readings, so
  the blind spot this record was written about is closed: the test that documented it asserts the
  opposite finding, and four mutants restore the defect one reading at a time. The guard itself
  stays, for the narrower reasons `D-111` gives — this record's reasoning about *why* it went in is
  left as written.
- **Retired by `D-113`.** The flat refusal is gone; what is left of it refuses a horizon that ends
  part-way through a week. This record stands as written, and it was worth writing: it was in force
  for the two changes that made it unnecessary, which is the whole job of a guard.
- **Date.** 2026-08-14.

## D-111 — The week rules are measured over a week, and the guard stays for narrower reasons

- **Decision.** `R-MAX-WEEKLY` and `R-WEEKLY-REST` are enforced **per week** in both readings, over
  weeks of seven days counted from the horizon's start. A rest window counts for a week only if it
  lies inside that week. `domain.py` gains the week as a shared convention — `weeks`, `week_of`,
  `week_span`, `week_start_day` — alongside half-open overlap and start-day attribution, and both
  rules now report the week they are about in the day coordinate. `D-110`'s `days > 7` guard stays.
- **Alternatives.** *A per-week budget field*, so week two can carry a different ceiling from week
  one. *A rolling reading* — 35 free hours in every seven-day window, not in every aligned week.
  *Lifting the guard here*, since the defect it stood for is fixed. *Leaving it alone* and treating
  one week as a permanent restriction of the product.
- **Reason.** At a one-week horizon the horizon and the week are the same span, which is why the
  original encoding was right and why nothing could see that it was right for the wrong reason. The
  generalisation costs nothing at that size and is verifiable as such: the model built for the
  headline instance has **895 variables and 1,205 constraints before and after this change**. It is
  the same model. At two weeks and beyond it is a different one, and the difference is the rule.

  The **per-week budget field** is the right end state and is deliberately not here. It is a payload
  change across 28 files, and it is the field the reference-period question actually turns on — a
  caller resolving a rolling quarter supplies what is left of it, which is a horizon total, not a
  weekly ceiling repeated. Both belong in the same record as the measurement that needs them, which
  is the study `rules.md` still owes.

  The **rolling reading** is stricter and was rejected on reporting rather than on strictness: it has
  no week to name, so a violation could say a person is short of rest without saying when, which is
  the coordinate `D-088` refused to give up for a 20% search win. Aligned weeks keep the day
  coordinate. What that costs is real and is asserted rather than hidden: a 40-hour rest straddling
  a week boundary counts for neither week, so a roster with one long break in the right place and
  nothing else is refused. That is `D-029`'s conservatism at every internal boundary rather than only
  at the horizon's end, and it is the same direction — too strict, never too weak.

  **Lifting the guard was rejected on evidence rather than on caution.** Two rules are correct at any
  horizon now; the stack around them is not known to be. `profile.py` probes feasibility over a
  hard-coded `7 * 24.0`, the generator hard-codes seven days, and a horizon that is not a whole
  number of weeks ends in a stub week that cannot contain a 35-hour rest — which this encoding
  reports as an infeasibility naming `R-WEEKLY-REST`, correct and baffling. Each is a small piece of
  work and none is done, so the request gate stays shut and `D-110` is amended rather than retired.
- **Consequences.** Both rules report a day coordinate where they reported none, naming the week by
  its first day, so the differential harness now compares *which week* rather than only *whether*.
  The checker's `_longest_free_run` clips to the span it is given rather than assuming the horizon,
  because an employee's roster reaches outside any one week.

  Four mutants restore the old scoping one reading at a time, and all four are caught by
  `test_differential.py`. That is the pointed part: the layer that was structurally unable to catch
  this defect an hour ago catches it four ways now, because the two readings can finally disagree
  about it.

  What `D-110` still guards is now a list rather than a principle, and it is the work that lifts it:
  the profile probe, the generator, and a whole-weeks rule for horizons past one week.
- **Amended by `D-113`.** That list was worked through and only one item on it was a defect. The
  profile probe was already right and only misnamed; the whole-weeks rule is what the guard became;
  the generator is unfixed and turned out not to gate the request path at all, only the evidence.
- **Date.** 2026-08-14.

## D-112 — The mutation harness says `unverifiable` where it used to say `clean`

- **Decision.** A run that cannot vouch for the tree it ran in reports `verdict: unverifiable`,
  exit code 3, `trustworthy: false`. Two conditions trigger it: a target file already modified when
  the run started, and a late write an editor reinstated after the per-mutant restore verified. A
  survivor still outranks both, because a mutant that survived, survived.
- **Alternatives.** *Refuse to start on a dirty tree*, which is the strongest fix and forbids the
  workflow that found this — running a new mutant against uncommitted work is exactly when a new
  layer is being proved. *Leave it*, since the report already named the skipped files. *Check the
  tree by content instead of by `git status`*, which is what `_late_restore` already does.
- **Reason.** The harness knew and said nothing that mattered. The report from the run that prompted
  this record read `verdict: clean`, `trustworthy: true`, `leaked: []` — with a mutated `checker.py`
  sitting in the working tree — and named the reason three fields lower, in
  `unchecked_because_already_modified`. The clean-tree check subtracts files that were already
  modified, so it was blind to precisely the two files the run was mutating, and `trustworthy` was
  computed as `verdict != "leaked"`, which is a tautology when the leak check cannot see.

  `CLAUDE.md` tells a reader to ask `jq .verdict` first and treat `leaked` as void. That instruction
  is only as good as the verdict, and here the verdict contradicted two other fields in its own
  object. **A field a reader is told to trust must not be the one field that cannot see the failure.**

  Refusing to start was rejected because of when the harness is used. `CLAUDE.md` says to run it when
  a layer is added or is about to be trusted, which is mid-change by definition — a rule that forbids
  dirty trees forbids the case the harness exists for. Labelling the run honestly costs nothing and
  keeps it available.

  Checking by content rather than by git was rejected as insufficient rather than wrong.
  `_late_restore` already does it, and it is why nothing leaked *during* the run. It cannot reach the
  failure that actually happened, which is a format-on-save watcher writing the mutated text back
  **after the process exited**, into an idle tree. No in-process check can. What the harness can do
  is decline to certify a tree it will not be around to watch.
- **Consequences.** `summarise` takes `late` and computes `unvouched_for` from it, so the field the
  verdict is derived from is in the report rather than reconstructable from two others. Four tests
  pin the ordering — leak, survivor, unverifiable, clean — and one of them is the run that prompted
  this record, reduced to its verdict.

  The pre-flight anchor check remains the thing that catches the post-exit write, on the *next* run:
  a mutant whose `old` text is missing means either a stale mutant or a leaked payload, and it
  refuses to start. That is why this defect was survivable — the harness would have refused the next
  run rather than testing against the leftover. It is a second line, not the first.

  `CLAUDE.md` and the module docstring carry the new verdict, because the instruction to read
  `.verdict` first is now worth following.
- **Date.** 2026-08-14.

## D-113 — The guard comes off for whole weeks, and stays on for part of one

- **Decision.** A horizon longer than a week is accepted when it is a **whole number of weeks**. One
  that ends part-way through a week is refused as a request. `D-110`'s flat refusal is retired;
  `_horizon_span` keeps the name and changes the rule.
- **Alternatives.** *Keep the guard* until the committed set contains multi-week instances. *Accept a
  part-week horizon* and let the model report what it finds. *Require whole weeks always*, which
  would refuse the three-day horizons the service answers today.
- **Reason.** `D-111` gave three reasons for keeping the guard, and they did not survive contact in
  the same way.

  The **profile probe** was not a defect. `contradictions()` compared `min_weekly_rest_hours` against
  a hard-coded `7 * 24.0` called `horizon_hours`, and the value was right for a reason the name
  denied: after `D-111` the rest window must fit inside a *week*, so the constant is the rule's own
  span and no longer stands in for the payload's. It is `week_hours` now. A profile is configuration
  with no horizon attached, and this check was always about the week — it was correct by the same
  coincidence `D-110` was written about, and is correct on purpose now.

  The **stub week** is real and is what the guard becomes. `R-WEEKLY-REST` needs its window inside
  the week it counts for, so a ten-day horizon ends in a three-day week that cannot hold 35 hours
  under any roster. The model reports that honestly — the gate goes false, the solve is infeasible,
  and the core names `R-WEEKLY-REST` — and it is a useless truth: the week it is about is mostly not
  in the payload, and the planner can do nothing with it. No roster fixes it, which is `D-040`'s
  dividing question answered, so it is an `InputDefect` naming the stub.

  The **generator** is the one that is unfixed, and it does not gate this. It is evidence tooling,
  not the request path: a caller sending fourteen days never touches it. What its seven-day
  hard-coding actually costs is that **no committed benchmark case runs at more than a week**, so
  this ships a supported configuration with no measurement behind it. That is stated here rather than
  discovered later, and it is the study's job rather than the guard's.

  What replaces the guard as evidence is an end-to-end test at two weeks, and it is built to separate
  the two readings rather than to pass: one week's demand twice is 277.5 hours of work against 304
  hours of budget *per week* and fits, while the same instance measured across the fortnight against
  one week's budget is 555 hours into 304 and has no roster at all. It distinguishes the encodings by
  feasibility, not by a violation count.
- **Consequences.** Generation mode (`D-109`) inherits the lift: a cold solve over four weeks is now
  answerable, where `D-110` refused it. The horizon-scaling numbers in `D-111`'s probe were taken on
  a tiled instance with a loosened budget, and now that the configuration is supported they can be
  measured on real ones — which is the study `rules.md` still owes.

  Two things the generator needs before it can supply them, both found while scoping this and neither
  fixed here: `DAYS = 7` has to become a scenario parameter, and `_load` treats `day >= 4` as the
  weekend, which past day six makes every remaining day of a fortnight a Saturday.
- **Date.** 2026-08-14.

## D-114 — The timing guards are calibrated, so CI deselects them rather than widening them

- **Decision.** `test_the_build_to_search_balance_still_holds` and
  `test_the_absolute_timings_are_the_right_order_of_magnitude` are marked `machine` and deselected in
  CI with `-m "not machine"`. They still run by default everywhere else.
  `test_build_still_dominates_search` is not marked and runs in CI.
- **Alternatives.** *Widen the bands* until a shared runner passes. *Regenerate `timings.json` on the
  runner*, making CI the calibration machine. *Delete the guards*, since CI cannot check them.
- **Reason.** `timings.json` holds 4.87 ms of build against 3.21 ms of search, measured on the machine
  in `benchmarks.md`'s hardware line. The absolute band admits a factor of three, and a shared
  two-core runner is routinely two to four times slower at single-threaded Python — so the guard fails
  on build somewhere above 14.6 ms, which is an ordinary figure there. It is not detecting a
  regression; it is detecting the runner.

  **Widening is the option `D-096` already refused**, one level up. That record rejected a 40% band on
  the milliseconds because it would not have caught `D-092`'s 26% shift: a band loose enough to
  survive a slower laptop is too loose to detect what it exists for. A band loose enough to survive a
  CI runner is looser still, so taking that option now would spend the guard to keep a green tick.

  **Regenerating on the runner** moves the calibration to hardware nobody reads the documents on. The
  figures exist to keep `benchmarks.md`, `replan.md` and the studies honest, and those quote the
  laptop. A `timings.json` measured on a runner would guard a number no document claims.

  The ratio is the subtler half. `D-096` chose `build / search` because a faster machine shrinks both
  sides, and that holds between comparable machines. It does not hold between a laptop and a shared
  runner, where the Python half and the C++ half slow by different factors — the ratio is portable
  against *speed*, not against a change in the mix.

  `test_build_still_dominates_search` stays in CI because it asserts an ordering rather than a
  calibration, and slower hardware makes it more true rather than less: Python is what a slow machine
  punishes hardest, so build pulls further ahead of search.
- **Consequences.** CI checks 761 of 764 tests, and the three it does not check are the three it
  cannot. That is a real hole and it is the honest shape of one: the guard `D-096` exists for is a
  guard against *this* repo's documents drifting from *this* machine, and it can only be run here.
  `README.md` says which command CI runs and why it differs.

  This is also the first thing CI found, and it found it by failing on a green repo — the tests pass
  on every machine that has ever run them and fail on the one machine that had never run them.
- **Date.** 2026-08-14.

## D-115 — The generator takes a horizon, and its weekly pattern was a weekly pattern only by accident

- **Decision.** `ScenarioParams` gains `days`, defaulting to seven, and the generator refuses a
  horizon `validation.py` would refuse (`D-113`). `_load`'s demand weighting keys on
  `day % DAYS_PER_WEEK` rather than on `day`.
- **Alternatives.** Generate multi-week instances by tiling a week, which is what the scoping probe
  for `D-111` did. Leave the generator at one week and study horizons with hand-built instances.
- **Reason.** The tiled probe was fine for measuring model *size* and knowingly wrong about
  everything else: it repeated one week's demand exactly, scaled the budget by the number of weeks to
  keep the model feasible, and therefore could not be used for any claim about coverage. A study of
  what a longer horizon buys needs instances whose demand was drawn for that horizon.

  **`_load` is the defect this turned up.** It weights demand toward the back of the week with
  `1.6 if day >= 4`, which is a weekly pattern for exactly as long as the horizon is a week. At
  fourteen days it makes every day from the first Thursday onward a Saturday, so a fortnight would
  have been generated with ten weekend days out of fourteen and the tightness reported against it
  would have been describing a week that does not exist. Nothing would have failed; the study would
  simply have measured a different world.

  It is the same shape as `D-110` one layer out — a constant that is right only because two things
  coincide, and stops being right the moment they separate. The generator had three of them
  (`DAYS` for eligibility, for unavailability, and for the grid) and they were mechanical; this one
  was arithmetic, and it is the one that would have been believed.
- **Consequences.** Capacity is now the weekly budget times the number of weeks, in both `_demand`
  and `measure`, because `max_hours_this_week` binds per week (`D-111`) while demand is stated over
  the horizon. Without that, a fortnight at `demand_ratio` 0.70 would open one week's shifts across
  two weeks and report twice the tightness it had.

  **Nothing moved at seven days.** The committed manifest's fingerprints are unchanged, which is the
  guard `D-074` exists to be: every one of these edits is inert at the default, and the fingerprints
  are what says so rather than a reading of the diff.
- **Date.** 2026-08-14.

## D-116 — A longer horizon is rejected because it buys nothing, not because it costs too much

- **Decision.** The one-week horizon stands. `rules.md`'s rejection of a reference-period horizon is
  kept and **its stated reasons are replaced with the measured ones**
  ([`studies/horizon.md`](studies/horizon.md)).
- **Alternatives.** Ship a multi-week horizon now that validation accepts one. Keep the rejection and
  leave its reasoning as written.
- **Reason.** The sentence being tested claimed a longer horizon *"multiplies instance size by an
  order of magnitude and destroys the interactive latency the whole service is built around."*
  Measured over 7, 14 and 28 days: four times the days gives **3.9× the variables and 4.0× the
  constraints**, and four weeks answers in about **112 ms end to end**. Size is linear because
  nothing in this model aggregates across the horizon — a rest gap is eleven hours, so no shift
  conflicts with one a week away. Both halves of the claim are wrong.

  What justifies the rejection is the half the sentence never mentions. Four weeks solved at once and
  four weeks solved one at a time with the boundary state carried between them reach **identical
  coverage on every case tried**, at `demand_ratio` 0.70 and 0.90, three seeds each — including the
  tight setting where five positions go unstaffed either way. And under that pressure the single
  solve costs 239 to 555 ms of search where the four small ones cost 94 to 166 ms in total. **The
  longer horizon is slower and finds nothing.**

  That follows from the structure once `D-111` is in place, which is why it is worth stating as a
  property rather than as a number: `R-MAX-WEEKLY` binds inside a week and `R-WEEKLY-REST` is
  measured inside a week, so neither couples one week to the next. What couples them is
  `R-REST-GAP` and `R-CONSEC-DAYS`, and both reach exactly as far as `last_shift_end_before_horizon`
  and `consecutive_days_worked_before_horizon` already carry. A model whose blocks are joined only at
  the seam does not need to see them together.
- **Consequences.** `D-081`'s premise is now **scoped rather than general**. Build costs more than
  search at seven days; at fourteen search already costs more, and at twenty-eight nearly three times
  as much. Every performance conclusion in this repo — the two clocks, the compiled-model cache
  (`D-093`), memoising `Instance.window` (`D-092`) — is a statement about a one-week horizon, and the
  crossover sits between one week and two.

  **The measurement cannot reach the question `rules.md` is actually about**, and this is the reason
  to reopen `D-111`'s deferral rather than close it. Both arms carry the same per-week ceiling, so
  what was compared is horizon *length*. The approximation the spec makes is a caller collapsing a
  rolling quarter into one weekly number, and what that loses is the freedom to spend it unevenly —
  45 hours this week against 31 next, inside one quarterly total. That is the single place a longer
  horizon has a mechanism to win, and no arm of this study can express it, because the field does not
  exist. Whether the approximation is lossy remains unmeasured, and it is now the only part of the
  original sentence still standing on assertion.
- **Study.** [`docs/studies/horizon.md`](studies/horizon.md)
- **Date.** 2026-08-14.

## D-117 — The solved half of the manifest is an artifact of one solver build, and CI checks the other half

- **Decision.** `test_manifest_matches_regeneration` is split. The **generated** half — the
  `week` digest, the event and the headcount — is asserted everywhere, including CI. The **solved**
  half, which is everything downstream of the incumbent, is marked `machine` and runs only where the
  artifact was recorded. `suite.portable()` names the split in code rather than in a test.
- **Alternatives.** *A lexicographic tie-break* in the objective, making the optimum unique so the
  roster is determined by the model rather than by the search. *Regenerate the manifest on the
  runner.* *Deselect the manifest test in CI entirely.*
- **Reason.** **The optimum is degenerate, and by a lot.** Four solver seeds on `headline/0` return
  the same objective — 4, every time — and **four different rosters**. Nothing in the model prefers
  one; the objective is flat across a large set of assignments, so which roster comes back is a
  property of the search path. A search path is fixed by the seed, the ortools version *and the
  binary*: CP-SAT is deterministic for a given build, and does not promise the same answer from a
  different one. The committed `incumbent` digests were written by a macOS arm64 build, and asserting
  them on a linux x86-64 runner tests the wheel rather than the generator.

  It is the same category as `D-114` one week later, and finding a second one is the point worth
  recording: **this repo commits artifacts, and an artifact carries the machine that made it.**
  `timings.json` carries the hardware; `manifest.json`'s solved half carries the solver build. Both
  were invisible while everything ran on one machine.

  The **tie-break** was rejected on the same ground this project refuses every other test-driven model
  change: it would alter what the solver optimises in order to make a fingerprint reproducible, and a
  model that is shaped by its test is no longer independent evidence about the spec. It would also be
  a real constraint added to every solve in production to serve a benchmark.

  **Regenerating on the runner** calibrates to a build nobody reads results from, which is `D-114`'s
  argument verbatim.

  **Deselecting the whole test** throws away the half that does travel, and it is the more important
  half: `week` digests the base instance before anything is solved, from `random.Random(seed)` and
  exact floats, so it answers *did the instances move* — which is the question the manifest exists
  for. `D-074` split the two fingerprints so a failure would say which moved; this makes that split
  load-bearing rather than diagnostic, and CI now checks the one that can be checked anywhere.
- **Consequences.** `D-074`'s guarantee is narrower than it read. "The set is its seeds" holds for
  the seeds; the solved incumbents are reproducible on the machine that recorded them and are
  *assumed* reproducible elsewhere. Anyone re-running the benchmarks on another platform should
  expect the solved half to move and the generated half to hold, and that is now what the tests say
  rather than something they would discover.

  **This was inferred, not read.** No CI log was available — `gh` is not installed here — so the
  diagnosis rests on the degeneracy measured locally plus the elimination of every failure a fresh
  clone could reproduce. If the runner is failing on something else, this change is still right and
  will not fix it.
- **Date.** 2026-08-14.

## D-118 — CI runs the platform the committed artifacts were recorded on, and the reproducibility claim is scoped

- **Decision.** CI runs on `macos-latest`, matching the arm64 macOS wheel the committed scenarios,
  goldens and manifest were produced with. `README.md`'s reproducibility claim gains the qualifier it
  always needed: a roster reproduces **on the same solver build**, and the objective value reproduces
  anywhere.
- **Alternatives.** *A dominated lexicographic tie-break* making the optimum unique, so the same input
  gives the same roster on any machine. *Mark the six failing tests `machine`*, as `D-114` and `D-117`
  did for two others. *Rewrite them to assert the objective and legality* rather than which optimum
  came back.
- **Reason.** `D-117` had the cause right and the blast radius wrong. It treated the solved half of
  `manifest.json` as the artifact carrying the solver build; the truth is that **every committed case
  does**. The incumbent is solved, the disruption event picks whom to injure *out of that roster*, and
  the whole scenario diverges from there — so a linux x86-64 runner fails six tests that have nothing
  to do with the manifest: the demo scenario, two metric-divergence results, MILP agreement on
  `tight/0`, the sample week's shortfall, and the profile probe's blocking rules.

  That was established by reproduction rather than by inference, after two inferences had already been
  wrong. Changing the seed the *generator* passes to its solve is exactly what a different binary does,
  and it reproduces the runner's six failures on this machine.

  Underneath is a **product defect rather than a test problem**, and it is stated here because a green
  tick that hides it would be worth less than the red one: the README promised that a roster could be
  reproduced from its input, seed and profile version, and that promise does not survive a change of
  binary. The objective value does. Which of the equally optimal rosters comes back does not, and
  nothing in the specification says which one should.

  **The tie-break is the real fix and is deliberately not here.** It would make the promise true, and
  an earlier draft of this reasoning rejected it as "changing the model to serve a test" — which was
  wrong, because it serves a documented product claim. It is invasive: keeping the tie-break dominated
  means growing the objective scale, which regenerates every golden and every committed objective
  value. That deserves its own record and its own review, not a paragraph inside a CI fix.

  **Marking the six** was rejected for what it would cost: the metrics, MILP, parse and profile layers
  would stop running in CI, which is most of the evidence, to avoid an artifact problem.
- **Consequences.** CI is a workaround wearing its reason on its sleeve, and the workflow says so.
  What it now checks is that the code works on the platform the artifacts came from — which is worth
  having and is less than it looks like: **CI can no longer tell you the project is portable**, because
  it is only run where it is known to work. That is a real loss and it is the price of A over B.

  macOS runners bill at a multiplier on private repositories and are free on public ones, so this is
  cheap exactly when `D-095`'s deferred publication happens and dearer until then.

  `D-117`'s split stands and is still right — the generated half of the manifest travels and the solved
  half does not — but its framing of the problem as *the manifest's* was too narrow, and this record is
  the correction.
- **Date.** 2026-08-14.

## D-119 — The optimum is canonical, because the model should decide the roster and the search should not

- **Decision.** `model.solve` runs a second phase on every proved optimum: the optimal objective value
  is pinned as a constraint and a canonical criterion is minimised over the optimal face. The roster
  returned is therefore a function of the model, not of the search. Nothing about *what is optimal*
  changes, so every committed objective value is untouched by construction.
- **Alternatives.** *Canonicalise cold solves only*, since that is where the degeneracy was first
  measured. *A dominated tie-break folded into the primary objective*, which would need the objective
  scale to grow. *Leave it*, and keep `D-118`'s scoped claim.
- **Reason.** The claim being repaired is `README.md`'s: a roster can be reproduced offline from its
  input, seed and profile version. `D-118` had to qualify it with *on the same solver build*, because
  a linux runner and a macOS laptop return different rosters for the same input, which broke six tests
  and sent CI to macOS to avoid the question.

  **The degeneracy is not marginal.** Across the 84 committed cases at four solver seeds, the
  objective value is identical every single time, and the roster differs on **24 of the 84 replans and
  on all 84 cold weeks**. The value is fully determined by the model; the choice among equal optima was
  determined by nothing anybody wrote down.

  Canonicalising cold solves only was the recommendation until that measurement, on the reasoning that
  a replan is pinned by its own objective. Two instances agreed and the set did not: 24 of 84 is not
  the rare edge the argument assumed. It is `D-105`'s lesson landing again — the property was a
  statement about where the sample was taken.

  **The criterion is `Σ ordinal² · x`, and the exponent was measured rather than chosen.** A linear
  criterion left a cold week with four rosters across four seeds; squaring collapsed it to one *and*
  ran three times faster, because a steeper gradient prunes harder. No preference about rosters is
  encoded by it — any total order would serve, and this one is cheap.

  Folding a dominated tie-break into the primary objective was rejected on blast radius: keeping it
  dominated means scaling every other weight, which moves every committed objective value and every
  golden for a change that is supposed to be invisible to them.
- **Consequences.** **Search time rises 61%, and `D-081`'s premise dies at one week.** The committed
  balance moves from `build/search` 1.52 to 0.985 — build 4.87 ms against search 3.21 ms becomes 5.08
  against 5.16. Building the model no longer costs more than searching it, which is the premise
  `D-081` separates the two clocks for and `D-093` partly rejects the compiled-model cache on. Neither
  decision flips: the cache was rejected on 0 hits in 144 solves, and `D-092`'s memoisation still cut
  build time. What is retired is the *present-tense* claim, and with it
  `test_build_still_dominates_search`, because a test pinning a claim the code no longer makes is
  worse than no test. `D-116` had already located that crossover between one week and two;
  this brought it forward to one.

  Every committed artifact derived from a solve is regenerated: the manifest, and the demo scenario.
  **The demo scenario moved from `headline/0` to `headline/3`**, and that is worth stating plainly
  rather than burying in a diff. Under the canonical incumbent the sick call in `headline/0` lands on
  somebody who *can* be covered, so the demo stopped showing a shortfall at all — and the shortfall
  explanation is the whole point of that file, quoted at length in `README.md`. `headline/3` is the
  same scenario class, the same Saturday sick call, from a week that was fully staffable, and it still
  poses the question. Choosing it is a presentation decision and is recorded as one.

  What remains unproven is the thing that started this: whether the canonical roster is stable across
  *builds*, rather than merely across seeds on one machine. The test is putting CI back on
  `ubuntu-latest` and watching, which `D-118` gave up on.
- **Date.** 2026-08-14.

## D-120 — The D0–D4 divergence rate is 10 of 84, and the number it replaces was never robust

- **Decision.** [`studies/disruption-metrics.md`](studies/disruption-metrics.md) is re-measured on the
  set as `D-119` leaves it. Divergence falls from **26 of 84 to 10 of 84**, the worked example moves
  from `early-notice/1` to `early-notice/0`, and the coverage-axis curve the study drew is withdrawn.
  `D-085`, `D-086` and `D-106` keep their figures as recorded; this supersedes them.
- **Alternatives.** Keep the old numbers with a note. Re-run and report the new rate without
  revisiting the conclusions drawn from the old one.
- **Reason.** **The method did not change and could not have.** `metrics.py` builds its own models and
  calls the solver directly, so the canonical optimum in `model.solve` never touches it, and the
  regret measurement was tie-proof before and after: it holds `a` at its optimum and minimises `b`
  over *all* of `a`'s optima, which is the most charitable reading of `a` available.

  **The instances changed.** A canonical incumbent is a different published roster, so the disruption
  event lands on a different person and every replan in the committed set is a new instance. The
  divergence rate is a property of the instances, and this is the measurement of how little that
  property travels: same generator, same classes, same seeds, and a rate that fell by a factor of
  two and a half.

  What held is the part worth having. The split is still **entirely** D0/D1/D2 against D3/D4, with
  zero inside each side. The regret is still symmetric at about 100% of the paying metric's own
  optimum. And the hand-derived worked example reproduces **to the point** on a different seed of the
  same class — two changed slots against four, 20 against 240, 40 against 120. A structure that
  survives its instances being replaced is a finding; a rate that does not is a measurement.

  Two conclusions drawn from the old rate are withdrawn rather than restated. **The coverage-axis
  curve is gone**: divergence used to rise to 4/6 at 0.70 and fall to zero by 0.90, and it is now flat
  at one case across the middle and zero at both ends. Six cases per point and ten conflicts in total
  cannot resolve a shape, and the previous run drew one anyway. **`tight` diverges once**, where
  `D-060`'s cleanest confirmation was that it never did.
- **Consequences.** `D-060`'s mechanism comes out of this *stronger*, from the instrument the study
  already argued was the right one. Measured at the slot the event damaged, **all ten divergences sit
  in the top slack bucket and every other bucket is a clean zero** — no case with fewer than six spare
  eligible people at the damaged slot diverges at all, where the previous set scattered conflicts
  across six of eight buckets. As a necessary condition that is now exact on this set; as a sufficient
  one it remains nowhere close, at 10 of 40.

  The rate is quoted in `README.md` and `finish.md` and both are corrected. What should not be
  corrected is the impression the old number gave, so it is worth stating: **26 of 84 was never a
  robust figure**, and nothing in the study said so, because nothing had moved the instances
  underneath it before.
- **Study.** [`docs/studies/disruption-metrics.md`](studies/disruption-metrics.md)
- **Date.** 2026-08-14.
