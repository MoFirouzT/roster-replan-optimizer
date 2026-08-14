# Configuration

> **Status: all four stages built.** `roster_replan/profile.py` — the profile document,
> contradiction and subsumption checks, and the feasibility probe, exposed as `review`.
> `roster_replan/nl.py` — the natural-language parse, the only stage that needs a model, behind an
> optional dependency (`uv sync --extra nl`) and an injected client.

## Profile as data

Per-tenant policy — what "optimal" means here, which rules apply, which parameters they take — is a
document, never code. Across thousands of small tenants, configuration work is the constraint that
does not scale; a code change per tenant is not a product.

`profile.Profile` carries the shift catalogue, the rule parameters, the objective weights, and which
profile-gated rules are enabled. `version` travels with every solve, alongside the input and the seed,
which is what `PLAN.md`'s replay requirement actually needs.

**Enabling an optional rule is currently a defect, not a courtesy.** All five profile-gated rules are
declared in `rules.md` and none is encoded in the model. Accepting one would promise enforcement that
never happens — the failure the registry exists to prevent, arriving through configuration instead of
through documentation. They become enableable when they are encoded, and not before.

## Natural-language profile building

Four stages. Each rejects into the previous. The LLM is confined to stage 1.

1. **Parse** `[built]` — natural-language policy description → candidate profile in the schema.

   **The schema is the confinement, and it is the schema the API compiles** (`D-101`). `StatedPolicy`
   carries only what a tenant would say — a rest gap, a shortest shift, how much worse a change at
   short notice is. It has no field for `shortfall_weight`, whose scale `D-057` bounds, and none for
   `enabled_optional_rules`, which `D-099` makes a defect: a rule the model cannot state is a rule it
   cannot break. Fields are designed against the compiled schema rather than the Python type,
   because an open mapping compiles to an object that can hold nothing.

   **Unset means the text did not say**, which is not the same claim as a default. A silence carries
   the base profile's value forward — the amendment case — and never invents a rule.

   The client is injected, so the module imports and tests with no API key, and nothing is saved:
   `propose` returns a candidate and the deterministic verdict on it.
2. **Validate structurally** `[built]` — schema, referential integrity, value ranges. Deterministic;
   the schema is enforced by the API for a parse and by `validation.validate_instance` for a solve.
3. **Validate semantically** `[built]` — contradiction and subsumption between rules. Deterministic;
   two rules bounding the same quantity in opposite directions is a solver-free check.

   A **contradiction** is a property of the profile alone: `min_period_hours` above every shift's
   length means no shift is legal for anyone, whatever week arrives. Knowable with no solver, no
   workforce and no open shifts — and worth catching here, because it otherwise surfaces as an
   unexplained empty roster on a Saturday morning.

   **Subsumption is the quieter failure and is reported, not rejected.** `max_consecutive_days` of 9
   over a seven-day horizon forbids nothing. The profile is valid; the tenant merely believes a
   protection is in force that is not, and nothing else in the system will ever say so.
4. **Probe feasibility** `[built]` — solve a sample week under the candidate profile. The sample is
   the **caller's** week, not a generated one: a synthetic week probes a workforce the tenant does not
   have. Blocking rules are returned through the explainer, so a config error and a Saturday-morning
   shortfall are described by the same machinery and cannot drift apart.

   The probe is **skipped when stage 3 found a contradiction.** Solving parameters that cannot all
   hold produces an infeasibility whose real cause is the profile, reported as though it were about
   the week.

Config errors are caught at configuration time, not at 9am on a Saturday.

**Round-trip eval `[not built]`:** profile → rendered to English → re-parsed must equal the original
profile. Stage 1 exists now, so this is possible rather than blocked — and still not run. Worth
stating precisely what it will and will not prove: a round trip over *canonical* English tests a
renderer against its own parser, which is close to a tautology. The eval that means something takes
**free-form** descriptions and checks the parse, and that needs a model to produce them.

**Guardrails.** The LLM sits outside the solver service; the stateless payload-in/payload-out
property is preserved. Model, prompt version and raw response are persisted with every config
change: `propose` carries the model and prompt version on the proposal, and the parsed payload *is*
the response, since structured outputs leave no separate raw text that could disagree with it.
Storing them is the caller's, as accepting a candidate is. Deterministic profile editing works fully
with no LLM available — the NL
layer is an accelerator, never a dependency, and that is an import-linter contract rather than a
promise (`D-101`): no deterministic module may reach `roster_replan.nl` or `anthropic`.
