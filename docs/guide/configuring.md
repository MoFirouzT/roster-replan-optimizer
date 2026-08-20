# Configuring a tenant

A tenant's policy — which rules apply, what parameters they take, what "optimal" means here — is a **document, not code**. There is no per-tenant code path, and adding a tenant never means a deploy.

## The profile

`profile.Profile` carries five things:

| Field group | What it holds |
| --- | --- |
| Shift catalogue | The shift types this tenant runs: label, start hour, span, break |
| Rule parameters | Every threshold each enabled rule reads, supplied explicitly — see [`rules.md`](rules.md) |
| Objective weights | What a change costs, and how much worse a change at short notice is |
| Fairness declaration | Which shifts nobody wants. This is policy and cannot be derived, so a tenant states it |
| Enabled optional rules | The profile-gated rules this tenant switches on |

The fairness declaration sits beside the shift catalogue because it is a set of indices into it. Separated, it would be a set of numbers whose meaning depends on whichever week it was applied to.

`version` travels with every solve, alongside the input and the seed. That is what makes a roster reproducible after the fact.

### Optional rules are not yet enableable

Five rules are declared in the registry and none is encoded in the model: `R-STUDENT-QUOTA`, `R-SUNDAY`, `R-BREAK`, `R-PT-MIN`, `R-PUB-NOTICE`. **Enabling one is rejected as a defect, not accepted as a courtesy.** Accepting it would promise enforcement that never happens. They become enableable when they are encoded, and not before.

## Describing a policy in English

`review` validates a profile. `propose` builds one from a policy written in plain English. Four stages, each rejecting into the previous, and the model is confined to the first:

**1. Parse** — English (or Dutch) policy description → a candidate profile.

The confinement is the schema, not the prompt. `StatedPolicy` carries only what a tenant would actually say: a rest gap, a shortest shift, how much worse a change at short notice is. It has **no field** for `shortfall_weight`, and none for `enabled_optional_rules`. A rule the model cannot state is a rule it cannot break.

*Unset* means the text did not say so — which is not the same claim as a default. A silence carries the base profile's value forward, which is the amendment case, and never invents a rule.

The client is injected: the module imports and tests with no API key. Nothing is saved — `propose` returns a candidate and the deterministic verdict on it.

**2. Validate structurally** — schema, referential integrity, value ranges. Deterministic.

**3. Validate semantically** — contradiction and subsumption between the tenant's own rules. Deterministic, and needs no solver.

A **contradiction** is a property of the profile alone. A `min_period_hours` above every shift's length means no shift is legal for anyone, whatever week arrives. Worth catching here, because it otherwise surfaces as an unexplained empty roster on a Saturday morning.

**Subsumption is the quieter failure, and it is reported rather than rejected.** A `max_consecutive_days` of 9 over a seven-day horizon forbids nothing. The profile is valid; the tenant merely believes a protection is in force that is not, and nothing else in the system will ever say so.

**4. Probe feasibility** — solve a sample week under the candidate profile.

The sample is the **caller's** week, not a generated one: a synthetic week probes a workforce the tenant does not have. Blocking rules come back through the same explainer a live shortfall uses, so a config error and a Saturday-morning shortfall cannot drift apart.

The probe is **skipped when stage 3 found a contradiction** — solving parameters that cannot all hold produces an infeasibility whose real cause is the profile, reported as though it were about the week.

## Running the parse

The natural-language stage is an optional dependency and needs a key:

```bash
uv sync --extra nl
```

Everything else works without it. **Deterministic profile editing never reaches the model**, and that is an import-linter contract rather than a promise: no deterministic module may import `roster_replan.nl` or `anthropic`.

Model, prompt version and the parsed payload are carried on every proposal so a config change can be audited. Storing them is the caller's job, as accepting a candidate is.

---

*Why the schema confines rather than the prompt, and why enabling an unencoded rule is a defect: [`decisions.md`](../archive/decisions.md#by-theme), under* The LLM boundary and profile configuration. *How the parse was measured:* [`nl-parse.md`](../archive/studies/nl-parse.md) *— 18/18 on three consecutive runs.*
