# Configuration

> **Status: outline.** Spec-after component — the NL layer is exploratory (T4). The profile schema
> itself is spec-first and lands in T1, because rules-as-data is a day-one structural commitment.

## Profile as data

Per-tenant policy — what "optimal" means here, which rules apply, which parameters they take — is a
document, never code. Across thousands of small tenants, configuration work is the constraint that
does not scale; a code change per tenant is not a product.

`[TODO]` Schema, versioning, and how a profile version is recorded with every solve for replay.

## Natural-language profile building `[T4]`

Four stages. Each rejects into the previous. The LLM is confined to stage 1.

1. **Parse** — natural-language policy description → candidate profile JSON in the schema.
2. **Validate structurally** — schema, referential integrity, value ranges. Deterministic.
3. **Validate semantically** — contradiction and subsumption between rules. Deterministic; two
   rules bounding the same quantity in opposite directions is a solver-free check.
4. **Probe feasibility** — solve a sample week under the candidate profile. Infeasible → reject
   before save, returning the blocking rules through the same explainer machinery.

Config errors are caught at configuration time, not at 9am on a Saturday.

**Round-trip eval:** profile → rendered to English → re-parsed must equal the original profile.

**Guardrails.** The LLM sits outside the solver service; the stateless payload-in/payload-out
property is preserved. Model, prompt version and raw response are persisted with every config
change. Deterministic profile editing works fully with no LLM available — the NL layer is an
accelerator, never a dependency.
