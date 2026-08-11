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
