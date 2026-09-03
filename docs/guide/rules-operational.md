# Operational rules

The five rules this product imposes because a roster has to work, not because a statute says so. Their authority is the tenant's own operation, and [`rules.md`](rules.md) is where they are registered and classified.

*Assumes: the registry and the classification in [`rules.md`](rules.md); the symbols in [`model.md`](../internals/model.md); the payload each rule reads its parameters from, [`api.md`](api.md).*


These rules carry no legal provenance, which is why they were specified first: nothing in them waited
on a `[CITE]`. The one exception is a `R-SKILL-MIX` entry that declares itself legal, which carries its
own. Symbols are defined in [`model.md`](../internals/model.md#sets-and-data).

<a id="rule-r-cover"></a>
### `R-COVER`: coverage

- **Statement.** Each open shift is staffed to its required headcount. Falling short is permitted and
  priced; exceeding it is not permitted.
- **Predicate.** For every `(d, s) ∈ O`, with shortfall `u[d, s] ≥ 0`:

  ```
  Σ_{e ∈ E} x[e, d, s] + u[d, s] = req[d, s]
  ```

  Feasibility requires `Σ_e x[e, d, s] ≤ req[d, s]`. Each unit of `u[d, s]` is priced in the
  objective.
- **Class.** Split: **hard ceiling, soft floor**. The split was ratified by measurement: forcing every non-historical shortfall to zero leaves **16 of
  the 72 committed cases with no answer at all**, and eight of those were weeks that could have been
  fully staffed before the disruption arrived.

  The ceiling is free: the all-zero roster satisfies it, so a hard upper bound can never be the sole
  cause of infeasibility. The floor must be soft because a disruption often has no legal repair, and
  "one short on Saturday, here is what it costs" is the answer a planner can act on. In the
  unconstrained case the optimum still lands exactly on `req[d, s]`, so the equality behaviour of the
  walking skeleton is preserved rather than abandoned.
- **Parameters.** `req[d, s]`, integer ≥ 0, per shift instance, caller-supplied. The shortfall weight
  lives in [`model.md`](../internals/model.md) and must dominate every other soft term. Overstaffing is rejected outright; an
  `allow_overstaffing` tenant flag is not in the profile schema.
- **Model encoding.** One equality per shift instance with an explicit slack variable
  `u[d, s] ∈ [0, req[d, s]]`, rather than two inequalities. The equality gives CP-SAT the tighter
  linear relaxation, and `u` is directly the coordinate the explainer reports, no reconstruction
  from a headcount difference.
- **Checker encoding.** Recount assignees per shift instance from the returned roster. Emit a
  violation for any instance over `req`, and a shortfall record carrying `(observed, required)` for
  any instance under it. **The checker must not read `u` from the solver**: a checker that trusts the
  solver's own slack is verifying arithmetic, not coverage.
- **Explainer text.** `Sat 15:00–23:00 (Evening) is 1 short of its 3 required staff.`
- **Provenance.** Operational.

> **Consequence: this rule collapses the infeasibility surface**. Once the floor is soft, the empty
> roster satisfies every hard rule, so a **cold solve is essentially never infeasible**: a shift nobody
> can staff comes back as a priced shortfall rather than as a refusal. What remains able to produce
> infeasibility is narrow: an incumbent whose past already breaks a rule (`R-PIN-PAST`), and a parameter
> that cannot be satisfied by any roster at all, such as a weekly rest window wider than the horizon.
>
> This is the intended product behaviour, and it is what the explainer is scoped around. Its ordinary job is
> explaining **shortfalls and their cost**, not explaining infeasibility; infeasibility is the rare case
> and both of its causes are structural rather than combinatorial. An explainer built for the rare case
> first would be built for the wrong one.

<a id="rule-r-avail"></a>
### `R-AVAIL`: availability

- **Statement.** Nobody is assigned to a shift that overlaps a declared absence or a period they
  declared unavailable.
- **Predicate.** For every `e ∈ E` and `(d, s) ∈ O`, writing
  `blocked[e] = absences[e] ∪ unavailability[e]`:

  ```
  [start(d, s), end(d, s)) ∩ blocked[e] ≠ ∅   ⟹   x[e, d, s] = 0
  ```

  **Interval intersection, not day equality.** This is the substantive correction to the walking
  skeleton, which blocked an employee for a whole day. A shift crossing midnight belongs partly to the
  next day, and an unavailability of `Sat 09:00–12:00` must not block `Sat Evening`.
- **Class.** Hard, and split by provenance:
  - `absences[e]`: hard, **never relaxable**. Sickness is a fact about the world.
  - `unavailability[e]`: hard. Specified as tenant-configurable to soft, since some operations do
    assign over a stated preference; the profile schema does not carry that switch today.

  The distinction is invisible to the solved model and visible in what a human is shown, which is the
  point: a report that blames a declared preference is actionable, one that blames an illness is
  noise. The checker carries it in the violation's `observed` field, as `absent` or `unavailable`.

  **Both provenances are gated identically in the model**: every eligibility fixing
  carries an assumption literal, so an ineligible assignment can be *reported* rather than merely
  making the model infeasible. The gate is reachable only where a variable exists anyway: an
  incumbent pair under `R-PIN-PAST`. A core naming an absence therefore means *the past itself is
  illegal*, which is worth saying. The consequence is that the model's gate descriptor does not yet
  distinguish the two provenances; carrying it there is an **explainer obligation**, recorded in

- **Parameters.** `absences[e]` and `unavailability[e]`, sets of half-open intervals, both
  caller-supplied. No defaults: an absent key means the empty set, and never means "unknown".
- **Model encoding.** Domain presolve, not a constraint: an ineligible `(e, d, s)` variable is never
  created. Removing variables is strictly cheaper than adding rows, and this rule plus `R-SKILL`
  eliminate most of the grid. Where the variable must exist anyway (any pair the **incumbent**
  assigned, so that a pinned past is representable and a deviation is countable) the
  exclusion becomes a *gated* `x = 0` rather than an outright fixing, so a roster that
  assigns an ineligible pair is reported instead of merely rejected.
- **Checker encoding.** Intersect the raw interval lists against shift bounds recomputed from
  timestamps. **Must not consume an eligibility mask from the model**: the mask is the thing under
  test.
- **Explainer text.** `Ana declared unavailable Sat 09:00–18:00, which overlaps Sat Evening (15:00–23:00).`
- **Provenance.** Operational. Sick leave has legal dimensions, but none that this rule encodes.

<a id="rule-r-skill"></a>
### `R-SKILL`: skill match

- **Statement.** Every assigned employee holds every skill the shift requires.
- **Predicate.** For every `e ∈ E` and `(d, s) ∈ O`:

  ```
  x[e, d, s] = 1   ⟹   req_skills[d, s] ⊆ skills[e]
  ```

  Set containment, not a single skill: a shift may require several, and each assignee needs all of
  them.
- **Class.** Hard, non-relaxable. A skill an employee does not hold is not a preference, and a core
  containing "Bram lacks forklift" is not actionable in the way a relaxable rule's core is. No
  assumption literal.
- **Parameters.** `skills[e] ⊆ K` per employee and `req_skills[d, s] ⊆ K` per shift instance, both
  caller-supplied. No tenant override.
- **Model encoding.** Domain presolve, the same mechanism as `R-AVAIL`. Both feed one joint
  eligibility filter (`eligible ⊆ E × O` in [`model.md`](../internals/model.md)) evaluated once at build time.
- **Checker encoding.** Independent set containment against the raw skill lists.
- **Explainer text.** `Wed 23:00–07:00 (Night) requires forklift; Bram does not hold it.`

  In practice `R-SKILL` surfaces through `R-COVER`: scarcity shows up as a priced shortfall, so the
  useful line is usually `only 1 of the 3 staff required for Wed Night hold forklift`. The explainer
  reports the skill scarcity alongside the shortfall rather than as a separate finding.
- **Provenance.** Operational.

<a id="rule-r-skill-mix"></a>
### `R-SKILL-MIX`: qualified coverage

- **Statement.** A shift may require that a minimum number of the people on it hold a given skill:
  "at least one first-aider among the three".
- **Predicate.** For every `(d, s) ∈ O` and every entry `(k, m) ∈ skill_mix[d, s]`, with shortfall
  `v[d, s, k] ≥ 0`:

  ```
  Σ_{e ∈ E : k ∈ skills[e]} x[e, d, s] + v[d, s, k] ≥ min(m, req[d, s] − u[d, s])
  ```

  The right-hand side is clamped to the headcount actually rostered. Demanding two first-aiders on a
  shift that only got one body is not a violation of this rule: the missing person is already
  reported once by `R-COVER`, and reporting it twice makes shortfalls incomparable across instances.
- **Class.** **Per entry**. Each `skill_mix` entry declares its own class, because the two cases are
  genuinely different rules wearing one shape:
  - *"at least one first-aider"*: operational, **soft**. A covered shift where nobody can do first
    aid is a real, priced operational state, and a planner must be shown it rather than handed an
    infeasibility.
  - *"at least one licensed nurse"*: legal, **hard**, non-relaxable. Running the ward without one is
    not an expensive option, it is a prohibited one.

  Applying the classification test rule-by-rule would force one answer for both; applying it
  entry-by-entry is the only way it comes out right. Legal entries carry a provenance string,
  validated as non-empty at profile load.
- **Why not fold this into `R-SKILL`**. `R-SKILL` is per-assignee and is enforced by *deleting*
  variables in presolve. `R-SKILL-MIX` constrains a shift's composition and needs a counting
  constraint over surviving variables: it cannot presolve away. `R-SKILL` is formally the special
  case `m = req[d, s]`, and unifying them anyway would trade the cheapest constraint in the model for
  the more expensive encoding. Two IDs, two encodings, one vocabulary.
- **Parameters.** `skill_mix[d, s]`, a set of `(skill, minimum, class, provenance)` entries per shift
  instance, caller-supplied, default empty. Weight for soft entries lives in [`model.md`](../internals/model.md) and must sit
  at or above the `R-COVER` shortfall weight: an unqualified shift is at least as bad as a short one.
- **Model encoding.** One linear inequality per `(shift instance, skill)` entry over the eligible
  employees holding that skill, with a slack variable for soft entries and none for hard ones.
- **Checker encoding.** Recount holders per shift instance from the raw skill lists and the returned
  roster. Independent of `R-SKILL`'s check, even though both read `skills[e]`.
- **Interaction with `R-PIN-PAST`.** Mix shortfalls on shift instances that have already started are
  historical: excluded from the objective, reported separately, for the same reason as coverage
  shortfall.
- **Explainer text.** `Sat 15:00–23:00 (Evening) has 3 of 3 staff but no first-aider; 1 required.`
- **Provenance.** Operational by default; per-entry legal provenance where an entry is declared hard.
  Sector-specific minimum-qualification rules are `[CITE]` and land with the profile schema.

<a id="rule-r-pin-past"></a>
### `R-PIN-PAST`: the immutable past

- **Statement.** A shift that has already started cannot be changed. The replan may not add to it,
  remove from it, or move it.
- **Predicate.** For every `e ∈ E` and `(d, s) ∈ O` with `start(d, s) < now`:

  ```
  x[e, d, s] = x̄[e, d, s]
  ```

  The boundary is `start(d, s) < now`, strictly: **a shift in progress is past.** Three hours of a
  night shift already worked cannot be un-worked, so pinning on `end(d, s) ≤ now` would be wrong.
- **Class.** Pinned: fixes variables rather than constraining them.
- **Parameters.** `now`, timestamp, caller-supplied. `x̄`, the incumbent roster. Neither is derived:
  the checker receives both and **must not infer `now`** from the data, or it will disagree with the
  model whenever a horizon happens to start late.
- **Preconditions.** A cold solve supplies no `x̄`; the pin set is then empty and the horizon must
  begin at or after `now`. A replan with `x̄` but no `now`, or the reverse, is a malformed payload
  rather than a defaulted one.
- **Pinning is not exemption.** Pinned assignments count toward **every** other rule. A pinned night
  shift ending at 07:00 constrains the following morning through `R-REST-GAP`; pinned hours consume
  the `R-MAX-WEEKLY` budget; pinned days count toward `R-CONSEC-DAYS`. Treating the past as though it
  did not happen is the classic bug in this rule, and it produces rosters that are illegal precisely
  at the boundary nobody inspects.
- **Interaction with `R-COVER`.** A past shift that was understaffed stays understaffed, and nothing
  in the horizon can fix it. Its shortfall is therefore **excluded from the objective** and reported
  separately as historical. Leaving it in adds a constant that cannot be optimised away and makes two
  runs with different `now` values incomparable.
- **Model encoding.** Equalities carrying assumption literals, not constant substitution. Substituting
  constants at build time is cheaper and makes *pinning is not exemption* automatic, but it destroys
  the explainer's ability to name the past as the source of a conflict. CP-SAT's presolve folds these
  equalities well, so the cost is expected to be small: **measured, not assumed, in the [presolve
  study](../studies/encoding-levers.md#presolve).**
- **Why that matters.** Because pins are equalities, an incumbent that already violates a rule makes
  the entire solve infeasible with no repair available. This is a real production scenario: rules
  changed, or the roster was hand-edited. The assumption literals let the service distinguish **"the
  past itself is illegal"** from **"no legal future exists"**: two different messages, two different
  operator responses, and the first is invisible without them.
- **Checker encoding.** Verify equality against the supplied `x̄` for every shift instance starting
  before the supplied `now`.
- **Explainer text.** `Thu 23:00–07:00 (Night) has already started; Driss cannot be removed from it.`
- **Provenance.** Operational.

---

---

*Where each rule's classification comes from, and why the model and the checker never share a threshold: [`design.md`](../internals/design.md). The legal research behind the provenance column, including the two searches that found no rule: [`decisions.md`](../decisions.md#by-theme), under* Rules, provenance and the reference period.
