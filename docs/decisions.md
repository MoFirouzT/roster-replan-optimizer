# Decisions

What was chosen, what was rejected, and why.

**Each entry is readable standalone.** A decisions file backed by studies decays into a table of
links; a reviewer will read this file and never open a study. Summarise the finding here, link for
the analysis.

A decision record is permanently true — it is not history, and it does not belong in a spec, where
present tense squeezes rationale out.

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

| ID | Decision | Tier |
|---|---|---|
| D-001 | CP-SAT over MILP | T1 |
| D-002 | Hard constraints structural rather than penalised | T1 |
| D-003 | Model and checker as independent implementations sharing no code | T1 |
| D-004 | Brute-force enumeration as ground truth rather than trusting the solver | T1 |
| D-005 | Deviation-from-published as the objective, not cost-from-scratch | T1 |
| D-006 | D2 as the shipped disruption metric; D3/D4 configurable | T1 |
| D-007 | Lexicographic vs. weighted commensuration of disruption and cost | T2 |
| D-008 | Coverage as hard or soft constraint | T2 |
| D-009 | Assignment booleans over pattern/column formulation at these sizes | T2 |
| D-010 | Async job queue over synchronous HTTP | T3 |
| D-011 | Stateless solver service, no DB reads | T3 |
| D-012 | LLM confined to artifacts a deterministic layer can reject | T4 |
| D-013 | Minimal core from the solver, prose from the LLM — never the reverse | T4 |
| D-014 | Horizon-boundary state supplied by the caller, not solved over a longer horizon | T1 |
| D-015 | Incumbent comparison on observables only, never on objective values | T2 |
| D-016 | Pseudonymisation at capture; absence reasons discarded rather than protected | T2 |
| D-017 | Acceptance bar for incumbent replacement fixed before the first replay | T2 |
| D-018 | `R-COVER` split into a hard ceiling and a soft floor — provisional, folds into `D-008` | T1 |
| D-019 | Availability as interval intersection rather than whole-day blocking | T1 |
| D-020 | Absences non-relaxable, declared unavailability relaxable — one rule, two provenances | T1 |
| D-021 | Pins as assumption-literal equalities rather than build-time constant substitution | T1 |
| D-022 | Historical coverage shortfall excluded from the objective, reported separately | T1 |
| D-023 | `R-CONSEC-DAYS` reclassified operational/CBA — no statutory basis for adult workers | T1 |
| D-024 | Belgian rule implemented wherever it is stricter than the WTD | T1 |
| D-025 | `R-SKILL-MIX` class declared per entry, not per rule | T1 |
| D-026 | `R-SKILL-MIX` kept separate from `R-SKILL` to preserve presolve elimination | T1 |
| D-027 | Shift hours attributed wholly to the start day, never split at midnight | T1 |
| D-028 | Weekly rest as anchored candidate windows rather than time discretisation | T1 |
| D-029 | Weekly rest required inside the horizon — conservatism accepted over a heavier caller contract | T1 |
| D-030 | Budget sanity bounds as input validation, not as roster violations | T1 |
| D-031 | `R-MIN-SHIFT` reclassified input validation — not roster-violable under fixed shift instances | T1 |
| D-032 | Flexi eligibility and Dimona state resolved upstream, indexed per employee **per day** | T1 |
| D-033 | Flexi income ceiling folded into `max_hours_this_week`, not a parallel euro budget | T1 |
| D-034 | `R-FLEXI-ELIG` and `R-DIMONA-FLX` kept as separate IDs — different operator actions | T1 |
| D-035 | Conservative Dimona reading for same-day replan — only filed `OK` counts | T1 |
| D-036 | Asymmetric administrative disruption by contract type as input to the D0–D4 study | T2 |
