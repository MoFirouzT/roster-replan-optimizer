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
| D-001 | CP-SAT over MILP — **the one T1 record still owed.** No spec argues it, so it cannot be written from the repo without inventing a rationale nobody made. It needs the actual comparison: what MILP was weighed against, and on what | T1 |
| D-010 | Async job queue over synchronous HTTP | T3 |
| D-011 | Stateless solver service, no DB reads | T3 |
| D-012 | LLM confined to artifacts a deterministic layer can reject | T4 |
| D-013 | Minimal core from the solver, prose from the LLM — never the reverse | T4 |
| D-015 | Incumbent comparison on observables only, never on objective values | T2 |
| D-016 | Pseudonymisation at capture; absence reasons discarded rather than protected | T2 |
| D-017 | Acceptance bar for incumbent replacement fixed before the first replay | T2 |

---

# Records

Written in batches, one batch per spec, and ordered here by ID so a reader can look one up directly.

**Every T1 decision is now written.** Three batches: the rule registry
([`specs/rules.md`](specs/rules.md)), the model and validation layers
([`specs/model.md`](specs/model.md), [`specs/validation.md`](specs/validation.md)), and the objective
([`specs/replan.md`](specs/replan.md)). What the Open table still lists is T2 and later, plus
`D-001`, which is T1 and is called out there for what it needs.

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
- **Date.** 2026-08-12.

## D-049 — Weighted sum, not lexicographic ordering

- **Decision.** Hard rules are constraints; shortfall, disruption and cost are summed with weights.
  Not a lexicographic ordering.
- **Alternatives.** Lexicographic — feasibility, then disruption, then cost — which guarantees
  disruption is never traded away.
- **Reason.** That guarantee is the problem. Under a lexicographic ordering no cost saving, however
  large, buys a single unit of disruption. This collapses the disruption/cost Pareto frontier to one
  point, and that frontier is the headline chart in [`benchmarks.md`](../benchmarks.md). An objective
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
- **Reason.** At T2 sizes a search is about 3 ms and building the model in Python is about 7 ms, so
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
