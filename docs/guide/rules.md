# Rules

Every rule a roster is checked against: what it says, what parameters it takes, and where its authority comes from.

**One vocabulary end to end.** A rule's ID is the same string in this registry, in the CP-SAT model, in the independent checker, in the `Violation` objects you get back, and in the explainer's prose. When a shortfall says `R-SKILL`, that is the entry below.

Each rule is specified in eight bullets. Five are for anyone using the service — **Statement**, **Class**, **Parameters**, **Explainer text**, **Provenance** — and three are for anyone changing it: **Predicate**, **Model encoding**, **Checker encoding**. The last two are documented side by side deliberately, because the model and the checker are two independent readings of this page and keeping both visible is what makes the independence checkable.

Symbols come from [`model.md`](../internals/model.md).

## Registry

| ID | Rule | Class | Parameters | Provenance |
| --- | --- | --- | --- | --- |
| [`R-COVER`](#rule-r-cover) | Each open shift is staffed to its requirement | hard ceiling, soft floor | per shift | operational |
| [`R-AVAIL`](#rule-r-avail) | No assignment overlapping a declared absence or unavailability | hard | per employee, interval | operational |
| [`R-SKILL`](#rule-r-skill) | Assigned employee holds the shift's required skill | hard | per shift/employee | operational |
| [`R-SKILL-MIX`](#rule-r-skill-mix) | A shift's roster holds at least *m* people with a given skill | hard or soft, **per entry** | per shift/skill | operational, or legal per entry `[CITE]` |
| [`R-PIN-PAST`](#rule-r-pin-past) | Shifts starting before `now` are immutable | pinned | `now` | operational |
| [`R-MIN-SHIFT`](#rule-r-min-shift) | Minimum shift length — 2h horeca, 3h general | **input validation** — not roster-violable, see below | hours, per tenant | Arbeidswet art. 21; KB 18 June 1990; PC 302 CAO nr. 7 of 25 June 1997 art. 10 |
| [`R-REST-GAP`](#rule-r-rest-gap) | Minimum rest between consecutive shifts | hard | hours | Arbeidswet art. 38ter §1; WTD art. 3 |
| [`R-MAX-WEEKLY`](#rule-r-max-weekly) | Maximum hours this week, as a supplied per-employee budget | hard | hours, per employee | Arbeidswet art. 19, 26bis; WTD art. 6, 16(b) |
| [`R-MAX-PERIOD`](#rule-r-max-period) | Hours left in the rolling reference period, over the whole horizon | hard, **optional** | hours, per employee | Arbeidswet art. 26bis §1; WTD art. 16(b), 19 |
| [`R-MAX-DAILY`](#rule-r-max-daily) | Maximum hours per day | hard | hours, per contract | Arbeidswet art. 19, 20, 20bis, 22 |
| [`R-CONSEC-DAYS`](#rule-r-consec-days) | Maximum consecutive working days | hard | days | **not statutory** — operational/CBA, see below |
| [`R-MAX-WEEKENDS`](#rule-r-max-weekends) | Maximum weekends worked across the horizon | hard, **optional** | weekends, per employee | **not statutory** — operational/CBA |
| [`R-MIN-DAYS-OFF`](#rule-r-min-days-off) | Minimum length of a stretch of days off | hard, **optional** | days, per employee | **not statutory** — operational/CBA |
| [`R-MIN-BLOCK`](#rule-r-min-block) | Minimum length of a block of working days | hard, **optional** | days, per employee | **not statutory** — operational/CBA |
| [`R-MAX-SHIFT-TYPE`](#rule-r-max-shift-type) | Maximum assignments of one shift type | hard, **optional** | count, per employee and shift type | **not statutory** — operational/CBA |
| [`R-MIN-HOURS`](#rule-r-min-hours) | Minimum assigned hours over the horizon | hard, **optional** | hours, per employee | **not statutory** — operational/CBA |
| [`R-SUCCESSION`](#rule-r-succession) | A shift type that may not follow another | hard, **optional** | pairs of shift types | **not statutory** — operational/CBA |
| [`R-DAY-OFF`](#rule-r-day-off) | A day granted off, by day rather than by interval | hard, **optional** | day set, per employee | **not statutory** — operational/CBA |
| [`R-WEEKLY-REST`](#rule-r-weekly-rest) | Minimum uninterrupted weekly rest | hard | hours | Arbeidswet art. 38ter §3; WTD art. 5 |
| [`R-FLEXI-ELIG`](#rule-r-flexi-elig) | Flexi-job eligibility conditions | hard, **resolved upstream** | per employee, per day | Wet 16 Nov 2015 art. 4 §1, as amended by Wet 28 June 2026 |
| [`R-DIMONA-FLX`](#rule-r-dimona-flx) | `FLX` Dimona filing as an eligibility gate | hard, **resolved upstream** | filing state, per employee/day | NSSO Dimona instructions; Wet 16 Nov 2015 |
| `R-STUDENT-QUOTA` | Student-worker hour quota | hard, optional | hours/year | KB 28 November 1969 art. 17bis |
| `R-SUNDAY` | Sunday and public-holiday work restriction | hard, optional | derogation set | Arbeidswet art. 11, 16, 66; Feestdagenwet art. 4, 6, 11 |
| `R-BREAK` | In-shift break entitlement | hard, optional | minutes per hours worked | Arbeidswet art. 38quater; art. 34 under 18 |
| `R-PT-MIN` | Part-time minimum shift length and weekly hours | hard, optional | hours | Arbeidswet art. 21; Wet 3 July 1978 art. 11bis |
| `R-PUB-NOTICE` | Variable-schedule publication notice | soft, optional | days | Wet 8 April 1965 art. 6 §1, 1°, third para., d) |

An ID that links to a section below is specified there. The five that do not — `R-STUDENT-QUOTA`,
`R-SUNDAY`, `R-BREAK`, `R-PT-MIN`, `R-PUB-NOTICE` — are declared and sourced but not yet specified;
each still needs an exact predicate, its parameters and their per-tenant configurability, a
hard/soft classification, and the failure message the explainer renders.
Every rule marked *optional* is profile-gated: a tenant that does not enable it never pays for it.

`[CITE]` — every legal rule needs a named source. A legality claim without
provenance is a guess, and the checker is the component whose whole value is that it is not one.

**Every rule that names a statute names one.** The five unspecified rules are sourced above, and so
are the three items that were once open inside the specified ones. Two of those searches came back
negative, and the negative is the finding: there is **no 24-hour Dimona deadline** and **no horeca
3h48 minimum**. Both are recorded where the rule that would have carried them lives.

`R-SKILL-MIX` keeps its `[CITE]` and always will. Its provenance is declared **per entry** by the
tenant, so there is no one instrument to name — a first-aider requirement and a food-hygiene
requirement come from different places, and which applies is a fact about the tenant. That marker is
a property of the rule's shape rather than work left undone.

A citation is not the same as an encoded rule. Those five stay outlines until each has a predicate,
parameters, a hard/soft classification and a failure message, and `tests/test_specs.py` holds them to
*optional* until then.

### What the sources say, for rules not yet encoded

Recorded here so the search does not have to be repeated when one of these is built. **None of these
numbers is enforced by anything**, and none has been through the two independent readings that a
shipped rule gets.

| Rule | What the instrument sets |
| --- | --- |
| `R-STUDENT-QUOTA` | 650 hours a calendar year, permanent since 1 January 2025 — 475 before, 600 through 2023–24. Counted in hours, filed under Dimona worker type `STU`; ordinary contributions from the 651st hour |
| `R-SUNDAY` | Sunday work permitted for horeca under Arbeidswet art. 66 for workers 18 or over. Compensatory rest under art. 16: a full day where Sunday work passed four hours, half a day otherwise, inside the six days following. Public holidays are the Feestdagenwet's own entitlement and the two must not be made to coincide |
| `R-BREAK` | Two limbs. No more than six hours worked without interruption; and where working time passes six hours a break is owed, its length and timing set by CAO or the work rules. Only where no CAO applies does the statute's own floor bite — fifteen minutes, at the latest on reaching six hours. Under-18 workers take art. 34 instead. The statute does not say whether the break is paid |
| `R-PT-MIN` | Three hours per work period (Arbeidswet art. 21, general — **not** part-time-specific). Weekly floor one tenth of a comparable full-timer's week since 1 June 2026, a third before. PC 302 sets its own: ten hours a week, two hours a period |
| `R-PUB-NOTICE` | Seven working days, which a generally binding CAO may shorten to no fewer than three. **PC 302 sits at three** — it registered no CAO of its own by 31 December 2022, so the amending law's own floor took effect for it on 1 January 2023 |

Two of these carry a question that would have to be answered before encoding. `R-BREAK`'s second limb
is conditional on the tenant having no CAO, which is a profile fact this registry has no field for.
And `R-PUB-NOTICE` may not be alone: art. 159 of the Programmawet van 22 december 1989 states an
overlapping publication duty, and whether it is a second obligation or the same one seen twice was
not settled.

**Two provenance lines are weaker than the rest and say so.** `R-SUNDAY`'s art. 66 could not be read
off the consolidated statute — every ejustice endpoint truncates before Chapter VI — so its sector
list rests on agreeing secondary renderings. And the flexi income ceiling is carried by three
different figures in circulation. It is resolved upstream, so the number below is documentation
rather than a model input.

## Legal sources

Cited in short form throughout. Every instrument below is consolidated and publicly available.

| Short form | Instrument |
| --- | --- |
| **Arbeidswet** | Arbeidswet van 16 maart 1971 / Loi du 16 mars 1971 sur le travail (BS 30 March 1971), as amended |
| **WTD** | Directive 2003/88/EC of 4 November 2003 concerning certain aspects of the organisation of working time |
| **Feestdagenwet** | Wet van 4 januari 1974 betreffende de feestdagen — the public-holiday regime, separate from the Arbeidswet's Sunday regime |
| **Arbeidsreglementenwet** | Wet van 8 april 1965 tot instelling van de arbeidsreglementen, as amended by the Wet van 3 oktober 2022 (BS 10 November 2022) |
| **Arbeidsovereenkomstenwet** | Wet van 3 juli 1978 betreffende de arbeidsovereenkomsten, as amended by the Wet van 18 mei 2026 (BS 1 June 2026) |
| **RSZ-uitvoeringsbesluit** | KB van 28 november 1969 uitvoering wet 27 juni 1969 — art. 17bis carries the student quota |
| **PC 302 CAO nr. 7** | CAO nr. 7 van 25 juni 1997, Paritair Comité voor het Hotelbedrijf, generally binding by KB of 25 May 1999 |

Belgium transposes the WTD, and in several places transposes it *more strictly*. **Where the two
differ, this project implements the Belgian rule** — it is the binding one for the target tenants, and
the stricter of the two cannot produce a WTD violation. Each rule below records where that happens.

The relevant provisions are widely restated by third parties and often restated incorrectly; article
numbers here were checked against the consolidated statute rather than against summaries. One
concrete instance: the FPS Employment summary page attributes the three-hour minimum work period to
art. 19, and the statute puts it in art. 21.

## The reference period, and why `R-MAX-WEEKLY` is a budget

Average weekly hours in Belgian labour law are measured over a **rolling reference period** — a quarter or a year — not per calendar week. A per-week ceiling is not the rule; it is an approximation of it, and one that is wrong in both directions. It forbids a legal heavy week that a light week would compensate, and it permits thirteen consecutive weeks at the ceiling.

**So the reference period is resolved upstream and enters the solve as data.** You compute, per employee, the hours already worked in the period and the working time left in it, and supply a single `max_hours_this_week` budget. The solver and the checker see only that number. The horizon stays one week, the rule stays local, and the semantics stay correct.

The alternative — extending the solve horizon to cover the whole reference period — was built and measured, and it buys nothing: four weeks solved at once and four weeks solved one at a time reach identical coverage on every case tried, and under pressure the single solve is two to six times slower for it. See [`horizon.md`](../archive/studies/horizon.md).

**The budget is a week's hours, and it binds in every week of the horizon.** At a one-week horizon that is the same sum either way. What a single number cannot express is a *different* ceiling in week two from week one; supplying that is a payload change and it is not built.

A horizon of **whole weeks** is a precondition of the request. A week or less is answered; two, three or four whole weeks are answered; ten days is refused, because it ends in a stub week no roster can fit a weekly rest inside.

The cost is stated rather than hidden: **correctness depends on a computation this service does not perform.** The checker verifies assignments against the budget you supplied and never recomputes it — a checker that invents its own budget from a period it cannot see is testing you, not the roster.

## Operational rules

These rules carry no legal provenance, which is why they were specified first: nothing in them waited
on a `[CITE]`. The one exception is a `R-SKILL-MIX` entry that declares itself legal, which carries its
own. Symbols are defined in [`model.md`](../internals/model.md#sets-and-data).

<a id="rule-r-cover"></a>
### `R-COVER` — coverage

- **Statement.** Each open shift is staffed to its required headcount. Falling short is permitted and
  priced; exceeding it is not permitted.
- **Predicate.** For every `(d, s) ∈ O`, with shortfall `u[d, s] ≥ 0`:

  ```
  Σ_{e ∈ E} x[e, d, s] + u[d, s] = req[d, s]
  ```

  Feasibility requires `Σ_e x[e, d, s] ≤ req[d, s]`. Each unit of `u[d, s]` is priced in the
  objective.
- **Class.** Split — **hard ceiling, soft floor**. The split was ratified by measurement: forcing every non-historical shortfall to zero leaves **16 of
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
  linear relaxation, and `u` is directly the coordinate the explainer reports — no reconstruction
  from a headcount difference.
- **Checker encoding.** Recount assignees per shift instance from the returned roster. Emit a
  violation for any instance over `req`, and a shortfall record carrying `(observed, required)` for
  any instance under it. **The checker must not read `u` from the solver** — a checker that trusts the
  solver's own slack is verifying arithmetic, not coverage.
- **Explainer text.** `Sat 15:00–23:00 (Evening) is 1 short of its 3 required staff.`
- **Provenance.** Operational.

> **Consequence: this rule collapses the infeasibility surface**. Once the floor is soft, the empty
> roster satisfies every hard rule, so a **cold solve is essentially never infeasible** — a shift nobody
> can staff comes back as a priced shortfall rather than as a refusal. What remains able to produce
> infeasibility is narrow: an incumbent whose past already breaks a rule (`R-PIN-PAST`), and a parameter
> that cannot be satisfied by any roster at all, such as a weekly rest window wider than the horizon.
>
> This is the intended product behaviour, and it is what the explainer is scoped around. Its ordinary job is
> explaining **shortfalls and their cost**, not explaining infeasibility; infeasibility is the rare case
> and both of its causes are structural rather than combinatorial. An explainer built for the rare case
> first would be built for the wrong one.

<a id="rule-r-avail"></a>
### `R-AVAIL` — availability

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
  - `absences[e]` — hard, **never relaxable**. Sickness is a fact about the world.
  - `unavailability[e]` — hard. Specified as tenant-configurable to soft, since some operations do
    assign over a stated preference; the profile schema does not carry that switch today.

  The distinction is invisible to the solved model and visible in what a human is shown, which is the
  point: a report that blames a declared preference is actionable, one that blames an illness is
  noise. The checker carries it in the violation's `observed` field, as `absent` or `unavailable`.

  **Both provenances are gated identically in the model** — every eligibility fixing
  carries an assumption literal, so an ineligible assignment can be *reported* rather than merely
  making the model infeasible. The gate is reachable only where a variable exists anyway: an
  incumbent pair under `R-PIN-PAST`. A core naming an absence therefore means *the past itself is
  illegal*, which is worth saying. The consequence is that the model's gate descriptor does not yet
  distinguish the two provenances; carrying it there is an **explainer obligation**, recorded in

- **Parameters.** `absences[e]` and `unavailability[e]`, sets of half-open intervals, both
  caller-supplied. No defaults — an absent key means the empty set, and never means "unknown".
- **Model encoding.** Domain presolve, not a constraint: an ineligible `(e, d, s)` variable is never
  created. Removing variables is strictly cheaper than adding rows, and this rule plus `R-SKILL`
  eliminate most of the grid. Where the variable must exist anyway — any pair the **incumbent**
  assigned, so that a pinned past is representable and a deviation is countable — the
  exclusion becomes a *gated* `x = 0` rather than an outright fixing, so a roster that
  assigns an ineligible pair is reported instead of merely rejected.
- **Checker encoding.** Intersect the raw interval lists against shift bounds recomputed from
  timestamps. **Must not consume an eligibility mask from the model** — the mask is the thing under
  test.
- **Explainer text.** `Ana declared unavailable Sat 09:00–18:00, which overlaps Sat Evening (15:00–23:00).`
- **Provenance.** Operational. Sick leave has legal dimensions, but none that this rule encodes.

<a id="rule-r-skill"></a>
### `R-SKILL` — skill match

- **Statement.** Every assigned employee holds every skill the shift requires.
- **Predicate.** For every `e ∈ E` and `(d, s) ∈ O`:

  ```
  x[e, d, s] = 1   ⟹   req_skills[d, s] ⊆ skills[e]
  ```

  Set containment, not a single skill — a shift may require several, and each assignee needs all of
  them.
- **Class.** Hard, non-relaxable. A skill an employee does not hold is not a preference, and a core
  containing "Bram lacks forklift" is not actionable in the way a relaxable rule's core is. No
  assumption literal.
- **Parameters.** `skills[e] ⊆ K` per employee and `req_skills[d, s] ⊆ K` per shift instance, both
  caller-supplied. No tenant override.
- **Model encoding.** Domain presolve, the same mechanism as `R-AVAIL`. Both feed one joint
  eligibility filter — `eligible ⊆ E × O` in [`model.md`](../internals/model.md) — evaluated once at build time.
- **Checker encoding.** Independent set containment against the raw skill lists.
- **Explainer text.** `Wed 23:00–07:00 (Night) requires forklift; Bram does not hold it.`

  In practice `R-SKILL` surfaces through `R-COVER`: scarcity shows up as a priced shortfall, so the
  useful line is usually `only 1 of the 3 staff required for Wed Night hold forklift`. The explainer
  reports the skill scarcity alongside the shortfall rather than as a separate finding.
- **Provenance.** Operational.

<a id="rule-r-skill-mix"></a>
### `R-SKILL-MIX` — qualified coverage

- **Statement.** A shift may require that a minimum number of the people on it hold a given skill —
  "at least one first-aider among the three".
- **Predicate.** For every `(d, s) ∈ O` and every entry `(k, m) ∈ skill_mix[d, s]`, with shortfall
  `v[d, s, k] ≥ 0`:

  ```
  Σ_{e ∈ E : k ∈ skills[e]} x[e, d, s] + v[d, s, k] ≥ min(m, req[d, s] − u[d, s])
  ```

  The right-hand side is clamped to the headcount actually rostered. Demanding two first-aiders on a
  shift that only got one body is not a violation of this rule — the missing person is already
  reported once by `R-COVER`, and reporting it twice makes shortfalls incomparable across instances.
- **Class.** **Per entry**. Each `skill_mix` entry declares its own class, because the two cases are
  genuinely different rules wearing one shape:
  - *"at least one first-aider"* — operational, **soft**. A covered shift where nobody can do first
    aid is a real, priced operational state, and a planner must be shown it rather than handed an
    infeasibility.
  - *"at least one licensed nurse"* — legal, **hard**, non-relaxable. Running the ward without one is
    not an expensive option, it is a prohibited one.

  Applying the classification test rule-by-rule would force one answer for both; applying it
  entry-by-entry is the only way it comes out right. Legal entries carry a provenance string,
  validated as non-empty at profile load.
- **Why not fold this into `R-SKILL`**. `R-SKILL` is per-assignee and is enforced by *deleting*
  variables in presolve. `R-SKILL-MIX` constrains a shift's composition and needs a counting
  constraint over surviving variables — it cannot presolve away. `R-SKILL` is formally the special
  case `m = req[d, s]`, and unifying them anyway would trade the cheapest constraint in the model for
  the more expensive encoding. Two IDs, two encodings, one vocabulary.
- **Parameters.** `skill_mix[d, s]`, a set of `(skill, minimum, class, provenance)` entries per shift
  instance, caller-supplied, default empty. Weight for soft entries lives in [`model.md`](../internals/model.md) and must sit
  at or above the `R-COVER` shortfall weight — an unqualified shift is at least as bad as a short one.
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
### `R-PIN-PAST` — the immutable past

- **Statement.** A shift that has already started cannot be changed. The replan may not add to it,
  remove from it, or move it.
- **Predicate.** For every `e ∈ E` and `(d, s) ∈ O` with `start(d, s) < now`:

  ```
  x[e, d, s] = x̄[e, d, s]
  ```

  The boundary is `start(d, s) < now`, strictly — **a shift in progress is past.** Three hours of a
  night shift already worked cannot be un-worked, so pinning on `end(d, s) ≤ now` would be wrong.
- **Class.** Pinned — fixes variables rather than constraining them.
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
  equalities well, so the cost is expected to be small — **measured, not assumed, in the [presolve
  study](../archive/studies/presolve.md).**
- **Why that matters.** Because pins are equalities, an incumbent that already violates a rule makes
  the entire solve infeasible with no repair available. This is a real production scenario: rules
  changed, or the roster was hand-edited. The assumption literals let the service distinguish **"the
  past itself is illegal"** from **"no legal future exists"** — two different messages, two different
  operator responses, and the first is invisible without them.
- **Checker encoding.** Verify equality against the supplied `x̄` for every shift instance starting
  before the supplied `now`.
- **Explainer text.** `Thu 23:00–07:00 (Night) has already started; Driss cannot be removed from it.`
- **Provenance.** Operational.

---

## Structural legal rules

The rules encoded from labour law. Every one is **hard** — a roster that breaks one is not a
worse roster, it is an unlawful one, and "cheaply illegal" is not a state this service may return.
Each carries an assumption literal anyway, so a failed solve names the conflicting rule instances
instead of returning a bare `INFEASIBLE`; the literal is a diagnostic channel, not permission to relax.

### Two conventions these rules share

**Hours attribution**. A shift instance's hours are attributed **entirely to its start day**,
never split at midnight. A `23:00–07:00` night shift is eight hours on `d`, zero on `d + 1`. This follows
from shift instances being indexed by start day, and it must be stated because a checker that split at
midnight would disagree with the model on every night shift while both looked correct in isolation.

The same convention makes `d` a *worked day* for `R-CONSEC-DAYS` and leaves `d + 1` unworked, which is
the intended reading: the night worker's Tuesday is mostly rest, and it is `R-REST-GAP` that protects
it, not a fractional day count.

**Gross span and net working time are different symbols, and the rules disagree on which they want**.
Art. 38quater entitles a worker exceeding six hours to a break, and a break is not working time, so a
shift's `span` and its `work_hours` differ:

- `R-MIN-SHIFT` reads **`span`** — art. 21 governs the *work period*, and a "prestatie" may contain
  short meal or coffee breaks without becoming two periods.
- `R-MAX-WEEKLY` and `R-MAX-DAILY` read **`work_hours`** — they are working-time ceilings.

There is deliberately no single `hours(d, s)`. One symbol would make one of those rules wrong by about
a break per shift, in a direction no test would notice until a checker and a model disagreed over
fifteen minutes. Definitions live in [`model.md`](../internals/model.md#sets-and-data).

<a id="rule-r-min-shift"></a>
### `R-MIN-SHIFT` — minimum work period

> **Class correction.** The registry carried this as a hard constraint. **With fixed shift instances it
> cannot be one.** Shift types have durations defined by the tenant profile, and `x[e, d, s]` either
> assigns a whole instance or none of it; no roster the model can express contains a work period the
> catalogue does not already contain. A too-short shift is therefore a **defect in the profile, not in
> the roster** — and a constraint that no reachable solution can violate is not a constraint, it is
> validation wearing one.
>
> Reclassified: **input validation**, and [`api.md`](api.md#what-gets-rejected-before-any-solve) lists it. The roster checker does not
> implement it, which is the one intended exception to *every rule gets a checker encoding*.

- **Statement.** Every work period in the tenant's shift catalogue lasts at least the applicable
  minimum.
- **Predicate.** Over the profile rather than over a roster — for every shift type `s`:

  ```
  span(d, s)  ≥  min_period_hours   for every d with (d, s) ∈ O
  ```

  Gross span, not net — a work period interrupted by a coffee break is still one period. Checked once at
  profile load and on every profile change, not per solve.
- **Class.** Input validation. **Becomes structural if shift boundaries ever become decision
  variables rather than data** — at which point it needs a real encoding and a checker
  entry. Recorded here so that transition is a known cost rather than a discovery.
- **Parameters.** `min_period_hours`, default **3** (art. 21). Horeca derogation to **2**, available
  only under two cumulative conditions: a motivated notification to the chair of the joint committee
  (required since 1 January 2018), and a registered cash-register system (GKS) in the establishment.
  Several worker categories fall outside art. 21 entirely — domestic staff, commercial
  representatives, management and confidential posts, family businesses — plus the five categories of
  the Royal Decree of 18 June 1990.
- **Validation encoding.** Reject the profile with the offending shift type named. A derogated minimum
  requires a non-empty `derogation_basis`, as with `R-REST-GAP`.
- **Explainer text.** Not an explainer case — a profile is rejected at load, before any solve exists to
  explain. [`api.md`](api.md#what-gets-rejected-before-any-solve) owns the message.
- **Provenance.** Arbeidswet art. 21 — the statute, *not* art. 19; the FPS Employment summary page
  misattributes this one. Exempt categories: Royal Decree of 18 June 1990. Horeca limb: **CAO nr. 7
  of 25 June 1997** in joint committee 302, art. 10 for the two-hour work period and art. 9 for the
  ten-hour weekly floor, made generally binding by the Royal Decree of 25 May 1999 and amended as
  recently as the Royal Decree of 19 January 2023. The notification and GKS conditions
  above are attached to that derogation, but the instrument that added them in 2018 was not found;
  they are stated here from agreeing secondary sources.

  **The unresolved claim is now resolved, and the answer is that the rule does not exist.** A
  secondary source asserted a change effective 1 June 2026 — minimum contracts of 3h48 per week with
  performances of at least 3 hours per day — which would contradict the two-hour horeca figure. **No
  primary instrument applies it to horeca.** What exists is the Wet van 18 mei 2026 (BS 1 June 2026),
  which lowered the *general* part-time weekly floor from a third to a tenth of a full-timer's week;
  a 38-hour week makes that 3h48. It does not reach PC 302, whose ten-hour floor is set by CAO rather
  than derived from that fraction, and it left art. 21 untouched — the consolidated text still carries
  `<W 1989-12-22/31>` as its last marker, so the three-hour half of the claim has no source either.

  **It is a live dispute rather than a dead rumour**, which is why it stays on the record. The claim
  is the employer-side position in the sector, contested by ACV, who report the Ministry of Employment
  agreeing with them. Nothing here changes until PC 302 or the FPS issues something concrete.

<a id="rule-r-rest-gap"></a>
### `R-REST-GAP` — daily rest

- **Statement.** At least eleven consecutive hours of rest between the end of one shift and the start
  of the next.
- **Predicate.** For every `e ∈ E` and every ordered pair of distinct shift instances `a, b ∈ O` with
  `start(b) ≥ end(a)`:

  ```
  start(b) − end(a) < min_rest_hours   ⟹   x[e, a] + x[e, b] ≤ 1
  ```

  And across the horizon boundary, for every `(d, s) ∈ O`:

  ```
  start(d, s) − last_shift_end_before_horizon[e] < min_rest_hours   ⟹   x[e, d, s] = 0
  ```

  Overlap is the degenerate case rather than a separate rule: two overlapping instances have a negative
  gap and are excluded by the same inequality.
- **Class.** Hard. Art. 38ter §2 does permit derogations — force majeure, split shifts, team changes in
  shift work — so the *parameter* is tenant-configurable downward against a recorded derogation basis.
  The rule itself is never dropped.
- **Parameters.** `min_rest_hours`, default **11**. A tenant may lower it only with a non-empty
  `derogation_basis` string, validated at profile load. There is no upward cap — a stricter tenant is
  always lawful.
- **Model encoding.** Pairwise `≤ 1` over the conflicting-pair set, per employee. At these instance sizes
  the pair set is small and the encoding is transparently the same object the checker walks, which is
  worth more here than tightness.

  **Alternative, measured and rejected**: one optional interval variable per
  `(employee, shift instance)` inflated by `min_rest_hours`, under a single `add_no_overlap` per
  employee. It is 23% smaller and builds 14% faster, and searches 15% slower on 28 of 28 cases — a 4%
  better total on the committed set that reverses to 11% worse on larger cold instances. It also
  coarsens the gate to one literal per employee-week, losing the slot coordinate this encoding
  reports. The scaling argument for it is about the **horizon**, which is fixed at one week here, so
  it remains untested rather than disproved — see
  [`studies/rest-gap-encoding.md`](../archive/studies/rest-gap-encoding.md).
- **Checker encoding.** Sort the employee's assigned instances by start time, walk consecutive pairs,
  compare each gap against the parameter. `last_shift_end_before_horizon[e]` is the predecessor of the
  first instance — **not a special case, just the zeroth element**, which is the framing that stops the
  boundary being forgotten.
- **Explainer text.** `Ana finishes Fri 23:00 and would start Sat 07:00 — 8h rest, 11h required.`
- **Provenance.** Arbeidswet art. 38ter §1: a worker is entitled, per 24-hour period between the end
  and resumption of work, to at least eleven consecutive hours of rest. Transposes **WTD art. 3**,
  which sets the same eleven hours.

<a id="rule-r-max-weekly"></a>
### `R-MAX-WEEKLY` — the weekly budget

- **Statement.** An employee's assigned hours this week do not exceed the budget the caller supplied
  for them.
- **Predicate.** For every `e ∈ E` and every week `w ∈ W`:

  ```
  Σ_{(d, s) ∈ O, week(d) = w} work_hours(d, s) · x[e, d, s]  ≤  max_hours_this_week[e]
  ```

  Net working time, not span — breaks are not working time. Pinned past shifts are inside this sum, not
  exempt from it. At a one-week horizon `W` has one member and this is the sum over all of `O`, which
  is what it was before weeks were named here.
- **Class.** Hard.
- **Parameters.** `max_hours_this_week[e]`, hours, caller-supplied and mandatory. No default: a missing
  budget is a malformed payload, because the safe fallback — some fixed weekly ceiling — is precisely
  the wrong model this rule exists to avoid (see [the reference period](#the-reference-period-and-why-r-max-weekly-is-a-budget)).
- **What the caller is actually computing.** The section above says the caller resolves the reference
  period into one number. Naming its three components makes that auditable, because all three are
  legally distinct and only one of them is an average:

  1. **The residual average allowance** — art. 19 sets 8h/day and 40h/week in the statute, reduced to
     **38h/week** since 1 January 2003; art. 26bis §1 measures it as an average over a reference period
     that is the calendar quarter by default and extendable to at most one year by royal decree,
     sectoral or company CBA, or work-rules amendment.
  2. **The internal limit** — art. 26bis §1bis: at no moment in the reference period may cumulative
     hours worked exceed the permitted average, times the weeks elapsed, by more than **143 hours**.
     This is the provision that makes a single-week budget coherent at all: without a bound on
     cumulative excess, no week could be assessed locally.
  3. **The absolute weekly ceiling** — the derogation ladder caps any individual week regardless of the
     average: generally **50h**, and **45h** under art. 20bis flexible schedules.

  The budget is the minimum of the three. **WTD art. 6** independently caps average weekly working time
  at 48h over a reference period of up to four months (art. 16(b)); the Belgian computation is stricter
  in the ordinary case and the caller owns reconciling them.
- **Model encoding.** One linear inequality per employee over eligible pairs.
- **Checker encoding.** Sum `hours(d, s)` over the employee's assignments and compare to the supplied
  budget. **The checker never recomputes the budget** — restating the constraint from this registry,
  because this is the single place a well-meaning checker most reliably goes wrong. A checker that
  reaches for the reference period is testing the caller, and it will disagree with the model for
  reasons that are defects in neither.
- **Payload validation, distinct from roster checking**. That the supplied budget does not exceed the
  absolute weekly ceiling *is* locally verifiable, and it is worth verifying — but as **input
  validation**, not as a roster violation. A too-large budget is a bad payload; it is not a property of
  the roster, and reporting it as an `R-MAX-WEEKLY` violation would blame the solver for the caller's
  arithmetic. [`api.md`](api.md#what-gets-rejected-before-any-solve) lists it.
- **Explainer text.** `Hugo is budgeted 32h a week and this roster assigns him 40h in the week from day 0.`
- **Provenance.** Arbeidswet art. 19 and art. 26bis §1, §1bis. **WTD art. 6** and art. 16(b).

<a id="rule-r-max-period"></a>
### `R-MAX-PERIOD` — what is left of the reference period

- **Statement.** An employee's assigned hours across the whole horizon do not exceed the working time
  the caller says remains in their rolling reference period.
- **Predicate.** For every `e ∈ E` with a supplied remainder:

  ```
  Σ_{(d, s) ∈ O} work_hours(d, s) · x[e, d, s]  ≤  max_hours_this_period[e]
  ```

  The whole horizon, deliberately — this is the one rule here whose span is the payload rather than a
  week, because the quantity it bounds is a pool rather than a rate.
- **Class.** Hard, and **optional**: absent means the caller had nothing to add beyond the weekly
  ceiling. It is the only rule in this registry whose absence is ordinary rather than a defect.
- **Parameters.** `max_hours_this_period[e]`, hours, caller-supplied. No default and no derivation —
  the same prohibition as `R-MAX-WEEKLY`, for the same reason.
- **Why both, when `R-MAX-WEEKLY` already exists**. The section above concedes that one
  weekly number cannot express a *different* ceiling in week two from week one. This is the part of
  that gap worth closing: component 1 of the weekly budget's derivation is an **average over a
  reference period**, and an average is a pool. A caller with 140 hours left in the quarter and a 38h
  weekly ceiling is stating two different facts, and collapsing them into one number forbids the
  lawful 45-and-31 split in favour of 38-and-38.

  Both bind. The weekly ceiling is a rate limit and this is a budget, and neither implies the other:
  the ceiling alone permits thirteen consecutive weeks at the maximum, and the pool alone permits the
  whole quarter's hours in one week.
- **Model encoding.** One linear inequality per employee with a remainder supplied, over the whole
  horizon. Gated like every other hard constraint, so an infeasibility names it.
- **Checker encoding.** Sum the employee's assigned work hours and compare to the supplied remainder.
  **Never rederived from a period the payload does not contain**, which is `R-MAX-WEEKLY`'s
  prohibition applied to the quantity it was originally written about.
- **Explainer text.** `Hugo has 140h left in the reference period and this roster assigns him 152h.`
- **Provenance.** Arbeidswet art. 26bis §1 — the average measured over the reference period, which is
  the calendar quarter by default and at most a year by royal decree or CBA. **WTD art. 16(b)** allows
  a reference period up to four months, and art. 19 caps its extension; the Belgian computation is the
  stricter one and the caller owns reconciling them.

<a id="rule-r-max-daily"></a>
### `R-MAX-DAILY` — daily maximum

- **Statement.** An employee's hours on any single day do not exceed the daily maximum for their
  contract.
- **Predicate.** For every `e ∈ E` and `d ∈ D`:

  ```
  Σ_{s : (d, s) ∈ O} work_hours(d, s) · x[e, d, s]  ≤  max_daily_hours[e]
  ```

  Net working time, under the start-day attribution convention above.
- **Class.** Hard. The derogation ladder is a parameter change, not a relaxation of the rule.
- **Parameters.** `max_daily_hours[e]`, default **8** (art. 19). The lawful ladder, each step requiring
  its own recorded basis:

  | Hours | Basis |
  |---|---|
  | 9 | art. 20 §1 — schedule giving at least a half-day's rest beyond the weekly rest day |
  | 9 | art. 20bis — flexible schedules (paired with a 45h weekly ceiling) |
  | 10 | art. 20 §2 — worker away from home more than 14h/day for distance reasons |
  | 11 | art. 22 1° — successive shift work |
  | 12 | art. 22 2° — continuous processes |

  Further derogations exist under art. 23–26 and by sectoral CBA; the profile schema stores the basis
  as an opaque string and does not attempt to model the ladder's own preconditions.
- **Honest note on redundancy.** At one shift per day with 8h shifts this rule is nearly implied by
  `R-REST-GAP`, which already forbids most same-day pairs. It is **not** redundant in general: split
  shifts are lawful and common in horeca — two short periods in one day, separated by enough rest to
  satisfy `R-REST-GAP` while their sum binds here. Encoding it costs one inequality per employee-day,
  and the checker needs it independently regardless of what the model happens to make unreachable.
- **Model encoding.** One linear inequality per `(employee, day)`.
- **Checker encoding.** Group the employee's assignments by start day, sum `work_hours` per group.
- **Explainer text.** `Emma is assigned 12h on Wed; her contract allows 8h.`
- **Provenance.** Arbeidswet art. 19; derogations art. 20 §1, art. 20 §2, art. 20bis, art. 22 1°–2°,
  art. 23–26.

<a id="rule-r-consec-days"></a>
### `R-CONSEC-DAYS` — consecutive working days

> **Provenance correction.** The registry originally carried this as `labour law [CITE]`. **That is
> wrong, and the citation search is what surfaced it.** Belgian law sets no general cap on consecutive
> working days for adult workers. The commonly quoted figure of six derives from art. 16, which
> requires compensatory rest for Sunday work *within the six days following that Sunday* — a rule about
> where compensatory rest lands, not a ceiling on consecutive days. The binding legal guarantee is
> `R-WEEKLY-REST` (art. 38ter §3), and it belongs there.
>
> The rule stays in the registry, reclassified: **operational and CBA-derived**, not statutory.
> Planners want it, sectoral agreements impose it, and it is cheap. But the legality claim moves out.
> Youth workers under 18 do have explicit statutory limits; they are out of scope here and are not
> this rule.

- **Statement.** An employee does not work more than `max_consecutive_days` days in a row.
- **Predicate.** With the worked-day indicator `w[e, d] = ⋁_{s} x[e, d, s]` and `L =
  max_consecutive_days`, for every window of `L + 1` consecutive days starting at `d₀ ∈
  {−p, …, |D| − L − 1}`, where `p = consecutive_days_worked_before_horizon[e]`:

  ```
  Σ_{d = d₀}^{d₀ + L} w[e, d]  ≤  L
  ```

  Days with `d < 0` are pre-horizon and are **constants**, set to worked for the `p` days immediately
  preceding the horizon. Starting windows at `−p` rather than `0` is the whole boundary treatment: an
  employee who worked the six days before Monday is out of days on Monday, and a model whose windows
  begin at `0` silently grants them a fresh streak.
- **Class.** Hard, in the sense that the model enforces it — but the provenance is contractual, so a
  tenant may disable it entirely rather than only loosen it. This is the one rule in this section that
  may legitimately be switched off.
- **Parameters.** `max_consecutive_days`, default **6**, tenant-configurable including *off*.
  `consecutive_days_worked_before_horizon[e]`, caller-supplied, mandatory when the rule is enabled.

  **Per employee where one is supplied**. `Employee.max_consecutive_days` overrides the
  tenant's number for that person and absence means the tenant's applies. This is not a second rule —
  same ID, same encodings, same explainer text — only the place the limit is read from changes, and
  it is what lets one workforce hold two limits, which is how the only real dataset here states it.
- **Model encoding.** Sliding-window sums — `|D| − L + p` inequalities per employee, each over `L + 1`
  booleans, plus one reification per `(employee, day)` for `w`.

  **Alternative, measured and rejected**: a `regular` automaton over the worked/not-worked
  sequence, whose states count the current streak. It is the textbook encoding for sequence rules,
  which is why the study had to confirm it rather than assume it — and it is **19% slower to search on
  28 of 28 cases**, because at a seven-day horizon with a six-day limit this encoding builds exactly
  **one** window per employee, so the automaton competes against a single inequality. It also gates
  only per employee-week, losing the day coordinate. It does not express `R-WEEKLY-REST` either: a
  continuous 35-hour free run is measured in hours, not days. See
  [`studies/regular-constraint.md`](../archive/studies/regular-constraint.md).
- **Checker encoding.** Walk days in order tracking a streak counter initialised to
  `consecutive_days_worked_before_horizon[e]`, reset on any unworked day.
- **Explainer text.** `Finn already worked 4 days before Monday and this roster adds 3 more — 7 consecutive, 6 allowed.`
- **Provenance.** **Operational / sectoral CBA.** No general statutory basis for adult workers; see the
  correction above.

<a id="rule-r-weekly-rest"></a>
### `R-WEEKLY-REST` — weekly rest

- **Statement.** Every employee gets at least one uninterrupted block of 35 hours' rest in the week.
- **Predicate.** Let `A(e)` be the intervals of the shifts assigned to `e`. The rule requires some
  window `[t, t + min_weekly_rest_hours)` inside the horizon that no assigned shift intersects:

  ```
  ∃ t :  [t, t + min_weekly_rest_hours) ∩ ⋃ A(e)  =  ∅
  ```

  Existential, which is why this is the only rule here that is not a sum over assignments.
- **Class.** Hard. Art. 38ter §2's derogations reach §1, and this project does not relax §3.
- **Parameters.** `min_weekly_rest_hours`, default **35**. Window: **each week of the horizon**,
  seven days from its start, clipped to the horizon. At a one-week horizon that is the
  horizon, which is what it was before weeks were named here. A window counts for a week only if it
  lies inside it, so a rest straddling a boundary counts for neither — a known conservatism, at
  every internal boundary rather than only at the end.
- **Model encoding.** Candidate windows plus at-least-one. Introduce `r[e, j]` for each candidate
  window `j`, require `Σ_j r[e, j] ≥ 1`, and for each shift instance overlapping window `j` add
  `r[e, j] ⟹ x[e, instance] = 0` — a reified implication CP-SAT handles natively.

  **Candidates are bounded, which is what makes this tractable**: it suffices to anchor windows at
  `end(d, s)` for each shift instance, plus the horizon start. Any feasible rest window can be slid
  later until its left edge meets the end of some shift without shrinking below the threshold, so an
  anchored candidate exists whenever any window does. The candidate count is therefore `|O| + 1`, not a
  function of time granularity — no discretisation, no chosen minute resolution.
- **Checker encoding.** Sort the employee's assigned intervals, prepend
  `last_shift_end_before_horizon[e]`, and take the maximum gap between consecutive intervals **within
  each week**, clipping the roster to that week's span. Compare to the parameter. Independent of the
  candidate-window construction, which is the point — the model searches, the checker measures.
- **Known conservatism, stated rather than hidden.** The rest window is
  required to lie **within the week it counts for**. A lawful roster whose 35-hour block straddles a
  boundary is therefore rejected, and it counts for neither of the two weeks it spans.

  At the horizon's own end this is nearly harmless on a seven-day horizon — one such block must exist
  inside any week — and it bites on shorter ones. At an *internal* boundary it bites on every horizon
  longer than a week, which is the price of measuring the rule per week rather than per rolling
  seven-day window; the rolling form has no week to name, and naming the week is the reporting
  day coordinate the explainer needs.

  The fix for both is the same caller-supplied forward-looking commitment, symmetric with
  `last_shift_end_before_horizon`, and it is **deferred**: it would oblige the caller to promise
  something about a week it has not planned yet, which is a heavier contract than the conservatism
  costs. Revisit if short horizons, or rosters built around a straddling rest, become a real use case.
- **Interaction with `R-SUNDAY`.** Art. 38ter §3 builds the 35 hours by adding art. 38ter §1's eleven
  hours to *either* Sunday rest (art. 11) or compensatory rest for Sunday work (art. 16); art. 17 gives
  shift workers a distinct form — 24 uninterrupted hours weekly with at least 18 of them falling on
  Sunday. This rule encodes only the 35-hour block, which is the part that binds regardless of which
  limb applies. Sunday placement is `R-SUNDAY`, profile-gated and not yet specified.
- **Explainer text.** `Gita's longest rest this week is 27h; 35h uninterrupted is required.`
- **Provenance.** Arbeidswet art. 38ter §3, reading with art. 11, art. 16 and art. 17.

  **Stricter than the WTD, deliberately.** WTD art. 5 requires 24 uninterrupted hours plus the eleven
  of art. 3, and art. 16(a) permits averaging that over a 14-day reference period. Belgium requires 35
  *consecutive* hours and does not average. Implementing the Belgian rule satisfies both; implementing
  the WTD rule would not.

---

<a id="rule-r-max-weekends"></a>
### `R-MAX-WEEKENDS` — weekends worked

- **Statement.** An employee works at most a stated number of weekends across the horizon. A weekend
  counts once however many of its days are worked.
- **Predicate.** For every `e ∈ E` with a supplied limit, where `weekend(d) ⟺ d mod 7 ∈ weekend_days`:

  ```
  | { w : ∃ (d, s) ∈ O with week_of(d) = w ∧ weekend(d) ∧ x[e, d, s] = 1 } |  ≤  max_weekends[e]
  ```

- **Class.** Hard, and **optional** in `R-MAX-PERIOD`'s sense: absent means the caller is not asking
  for it, which is ordinary rather than a defect. Hard rather than priced because the only formulation
  measured against real data states it as a constraint, and because hard here does not mean
  unrelaxable — the gate names it in a core, so a planner who must breach one is told which one.
- **Parameters.** `max_weekends[e]`, per employee, caller-supplied. Per employee because the one
  workforce this project has measured varies it from 1 to 3 inside a single team.

  `weekend_days ⊆ {0…6}`, on `RuleParams`, positions within a week. **Caller-supplied and empty by
  default**, and the emptiness is the point: this domain has no calendar, so [`model.md`](../internals/model.md) fixes that a
  week is a position in the horizon and never a Monday. Which of its days are the weekend is a fact
  only the caller holds, and an empty set switches the rule off.
- **Why a count of weekends and not of weekend days.** Two Saturdays are two weekends and a
  Saturday-Sunday pair is one. The rule people actually hold is about how many of their weekends are
  taken, not how many days it cost — which is why this counts weeks and not assignments.
- **Model encoding.** One boolean per (employee, week), forced up by any weekend assignment, summed
  over weeks. The implication is needed in one direction only: the variable appears in a `≤`
  constraint and nowhere else.
- **Checker encoding.** Collect the distinct weeks holding a weekend assignment and compare the set's
  size. Deliberately different arithmetic from the model's — a set rather than a sum of forced booleans.
- **Explainer text.** `Ana works 3 weekends; 2 allowed.`
- **Provenance.** Operational, or a CBA. Not statutory: Belgian law governs Sunday work
  (`R-SUNDAY`) and weekly rest (`R-WEEKLY-REST`), neither of which is a budget of weekends.

<a id="rule-r-min-days-off"></a>
### `R-MIN-DAYS-OFF` — days off in blocks

- **Statement.** A stretch of days off inside the horizon is at least a stated number of days long.
- **Predicate.** For every `e ∈ E` with a supplied minimum, every gap length `L` from 1 to
  `min_consecutive_days_off − 1`, and every day `d` with `d + L + 1 < days`:

  ```
  worked[e, d] − Σ_{j=1..L} worked[e, d+j] + worked[e, d+L+1]  ≤  1
  ```

  where `worked[e, d] ⟺ ∃ s : x[e, d, s] = 1`. The left side is 2 exactly on the pattern being
  forbidden — worked, then `L` days off, then worked — and at most 1 on everything else.
- **Class.** Hard and **optional**, on the same footing as `R-MAX-WEEKENDS`.
- **Parameters.** `min_consecutive_days_off[e]`, per employee. A minimum of 1 forbids nothing, since
  every gap between two worked days is at least one day long, and is treated as absent.
- **Only interior stretches are judged, and that is a rule rather than a shortcut**. A
  stretch of days off reaching either end of the horizon may continue outside it, and a roster cannot
  be judged on days it does not contain. Applied without that latitude the rule failed **every one of
  the 26 published rosters** in the benchmark set that supplied it — 26 rosters being wrong is not the
  reading to prefer. `R-WEEKLY-REST` already takes the same view of its own edges.
- **Model encoding.** The forbidden pattern above, one gated inequality per (employee, gap length,
  start). The boundary latitude needs no special case: the pattern requires a worked day on both
  sides, so an edge stretch is never matched.
- **Checker encoding.** Walk the days off, measure each stretch, and skip those touching either end.
  Here the latitude has to be stated, which is the usual asymmetry between the two readings.
- **Explainer text.** `Bram gets 1 day off from day 4; 2 consecutive required.`
- **Provenance.** Operational, or a CBA.

<a id="rule-r-min-block"></a>
### `R-MIN-BLOCK` — blocks of working days

- **Statement.** A block of consecutive working days inside the horizon is at least a stated number
  of days long.
- **Predicate.** `R-MIN-DAYS-OFF`'s pattern with worked and off exchanged. For every gap length `L`
  from 1 to `min_consecutive_days_worked − 1` and every day `d` with `d + L + 1 < days`:

  ```
  −worked[e, d] + Σ_{j=1..L} worked[e, d+j] − worked[e, d+L+1]  ≤  L − 1
  ```

  The left side is `L` exactly on the pattern being forbidden — off, then `L` days worked, then off —
  and at most `L − 1` on everything else.
- **Class.** Hard and **optional**. A minimum of 1 forbids nothing and is treated as absent.
- **Why a tenant wants it.** A single day between two stretches off is a day somebody travels in for
  one shift. The rule is about the journey and the disruption to a week, not about the hours.
- **Interior blocks only**, for the reason `R-MIN-DAYS-OFF` gives about its own edges.
- **Model encoding.** The forbidden pattern above, one gated inequality per (employee, block length,
  start). The boundary latitude needs no special case.
- **Checker encoding.** Walk the worked days, measure each block, skip those touching either end.
  Written as its own walk rather than as `R-MIN-DAYS-OFF`'s with a flag: one predicate serving two
  rules is a defect that would break both readings of both at once.
- **Explainer text.** `Ana works a block of 1 day(s) from day 3; 2 consecutive required.`
- **Provenance.** Operational, or a CBA.

<a id="rule-r-max-shift-type"></a>
### `R-MAX-SHIFT-TYPE` — how many of one shift

- **Statement.** An employee works at most a stated number of assignments of a given shift type.
- **Predicate.** For every `e ∈ E` and every capped shift type `s`:

  ```
  Σ_{d : (d, s) ∈ O} x[e, d, s]  ≤  max_shifts_per_type[e][s]
  ```

- **Class.** Hard and **optional**, per employee and shift type.
- **Why not a total.** A cap on shifts in general is `R-MAX-WEEKLY` in another unit. This one says
  *four nights a month*, and a cap of **zero is a prohibition** — the shape a total cannot express.
- **A cap of zero is a rule, not an impossibility**, so it stays here rather than moving into the
  presolve's exclusions. Presolve removes pairs that cannot be worked; a cap the tenant chose should
  be reportable as a rule the roster broke.
- **Model encoding.** One gated sum per (employee, capped type).
- **Checker encoding.** Count the employee's assignments of that type and compare.
- **Explainer text.** `Ana works 5 N shifts; 4 allowed.`
- **Provenance.** Operational, or a CBA.

<a id="rule-r-min-hours"></a>
### `R-MIN-HOURS` — the floor

- **Statement.** An employee is assigned at least a stated number of working hours across the horizon.
- **Predicate.** For every `e ∈ E` with a supplied floor:

  ```
  Σ_{(d, s) ∈ O} work_hours(d, s) · x[e, d, s]  ≥  min_hours_this_period[e]
  ```

  `R-MAX-PERIOD`'s arithmetic with the comparison reversed, over the same span.
- **Class.** Hard and **optional**.
- **The only hard rule here a roster breaks by doing too little**, and that makes it the only one that can
  conflict with `R-COVER`'s soft floor: a week with too few shifts to go round cannot meet everybody's
  minimum, and no legal roster exists. **That is a legitimate infeasibility rather than a defect**, and
  it is gated like every other hard constraint, so the core names this rule instead of leaving a
  planner to infer it from a shortfall.
- **Model encoding.** One gated inequality per employee with a floor supplied.
- **Checker encoding.** Sum the employee's assigned work hours and compare. Net time, under the same
  convention every hours rule here uses.
- **Explainer text.** `Ana is assigned 15h; 24h is the minimum for the period.`
- **Provenance.** Operational, or a CBA — a guaranteed-hours clause is the usual source.

<a id="rule-r-succession"></a>
### `R-SUCCESSION` — a shift that may not follow another

- **Statement.** Where a tenant forbids a pairing, an employee working the earlier shift type does not
  work the later one the next day.
- **Predicate.** For every `e ∈ E`, `d ∈ D` and `(a, b) ∈ forbidden_successions`:

  ```
  x[e, d, a] + x[e, d+1, b]  ≤  1
  ```

- **Class.** Hard and **optional**. The pairs are on `RuleParams`, because they are a property of the
  shift catalogue rather than of a person.
- **Not subsumed by `R-REST-GAP`, though they overlap.** A rest gap is hours between two shifts and is
  satisfied by enough of them; this forbids a pairing outright however long the gap. A tenant who does
  not want anyone on an early shift the day after a late one is stating a rule about the *pattern*,
  and stating it as hours would forbid other pairs they are content with.
- **Model encoding.** One gated inequality per (employee, day, pair). Pairwise rather than an
  automaton, for the reason [`studies/regular-constraint.md`](../archive/studies/regular-constraint.md) gives:
  the pairs are local, the expansion is small, and the day coordinate survives into the violation.
- **Checker encoding.** Group the roster by employee and day, then check every consecutive pair. An
  employee holding two shifts on one day makes several pairs and each is checked — the rule is about
  the pairing, not about a canonical shift for the day.
- **Reported on the second day**, the one the forbidden shift falls on, in both readings.
- **Explainer text.** `Ana works M on day 4, which may not follow N.`
- **Provenance.** Operational, or a CBA.

<a id="rule-r-day-off"></a>
### `R-DAY-OFF` — a day granted off

- **Statement.** An employee is not assigned any shift that *starts* on a day they have been granted
  off.
- **Predicate.** For every `e ∈ E`, `d ∈ days_off[e]` and `s` with `(d, s) ∈ O`:

  ```
  x[e, d, s] = 0
  ```

- **Class.** Hard and **optional**, on `R-MAX-WEEKENDS`'s terms: an empty set is a caller not asking.
- **Why this is not `R-AVAIL`**. `R-AVAIL` refuses an assignment overlapping an interval,
  and a day off is not an interval. A shift starting at 22:00 the evening *before* runs six hours into
  the granted day and overlaps any interval covering it — so an interval reading refuses a shift the
  grant never meant to touch, while the day-indexed reading is exact. **Start-day attribution is what
  makes the difference**, and it is the convention this registry fixes for exactly this class of
  question.

  This is not hypothetical. The nurse-rostering importer drops its source's days off rather than
  translate them, and states the reason: every night shift before a day off was reported as `R-AVAIL`.
  That was the collision above, met from outside.
- **A grant, not an absence.** `R-AVAIL` splits by provenance — an absence is never relaxable, a
  declared unavailability is. This is a third thing: something the employer gave, which a planner may
  need to take back with the employee's agreement. Hard, and gated like every hard rule, so a core
  names it rather than a planner discovering it as an unexplained shortfall.
- **Model encoding.** One gated `x = 0` per (employee, granted day, shift starting that day). Gated
  rather than removed in the presolve, for `R-MAX-SHIFT-TYPE`'s reason: presolve removes the
  impossible, and a day the tenant granted is a rule a roster can break and be told about.
- **Checker encoding.** Membership of the granted set, read against the day the shift starts on.
  Deliberately not interval intersection — that is the reading this rule exists because it cannot do.
- **Explainer text.** `Ana is assigned day 3 07:00-15:00 (M) on a granted day off.`
- **Provenance.** Operational, or a CBA.

## Eligibility gates

`R-FLEXI-ELIG` and `R-DIMONA-FLX` share an architecture, and it is the one already established for
`R-MAX-WEEKLY`: **the condition is resolved upstream and enters the solve as data**.

Not by preference — by necessity. Between them these two rules depend on employment at *other*
employers, on quarters that ended before the horizon began, on year-to-date earnings, on sectoral
opt-outs, and on a response the NSSO returns from its own records. A one-week payload contains none of
it, and no amount of solver cleverness recovers it. What reaches the model is a per-employee, per-day
boolean, and the checker verifies against that boolean rather than re-deriving it.

The cost is the same one the reference period carries and is stated the same way: **correctness depends
on a computation this service does not perform.**

<a id="rule-r-flexi-elig"></a>
### `R-FLEXI-ELIG` — flexi-job eligibility

- **Statement.** Only an employee the caller has certified as flexi-eligible for the quarter containing
  a shift may be assigned that shift under a flexi contract.
- **Predicate.** For every `e` with `contract(e) = flexi` and every `(d, s) ∈ O`:

  ```
  x[e, d, s] = 1   ⟹   flexi_eligible[e, d] = true
  ```

  **Indexed by day, not by employee.** A horizon may straddle a quarter boundary — the week containing
  30 June and 1 July — and eligibility is retested per quarter, so one employee can be eligible on
  Tuesday and ineligible on Wednesday inside a single solve. An employee-level flag would silently get
  that week wrong, and it is exactly the week nobody tests.
- **Class.** Hard, non-relaxable, resolved upstream.
- **What the caller is resolving.** None of these are visible to a weekly roster solve, which is the
  argument for the whole approach:

  | Condition | Why the solver cannot see it |
  |---|---|
  | ≥ 4/5 employment with *other* employers in quarter T-3, against the sector's full-time reference person | Another employer's payroll, a quarter before the horizon |
  | Reduction from 100% in T-4 to 80% in T-3 bars flexi in T and T+1 | Two quarters of history |
  | Pensioners exempt from the 4/5 test | Personal status |
  | No concurrent regular contract with the same employer | Contract state, not roster state |
  | Annual flexi income ceiling | Year-to-date earnings across employers |
  | Sector scope and opt-outs | Tenant-level static fact |

  As of **1 July 2026** flexi-jobs are open in principle to the whole private *and* public sector,
  except sectors that opted out — a scope inversion from the previous enumerated-sectors regime. The
  annual ceiling rose from €12,000 to €18,000 at the same date, with the employee-side fiscal
  exemption at €18,440 for 2026 income and no ceiling for pensioners. Horeca additionally caps the
  flexi hourly wage at €21.00 (€22.61 including flexi holiday pay) — a **wage** rule, outside this
  model's scope, recorded so nobody mistakes it for a rostering constraint.
- **Parameters.** `flexi_eligible[e, d]`, boolean, caller-supplied, mandatory for any employee with a
  flexi contract. Absence is a malformed payload, never a default of `true`.
- **Treatment of the income ceiling**. Fold it into `max_hours_this_week[e]` as a fourth
  term in that budget's `min()`, rather than adding a parallel euro-denominated budget. The caller
  already converts a reference period into weekly hours; converting a remaining income allowance into
  remaining hours is the same kind of arithmetic against a known wage, and it keeps one budget concept
  in the model instead of two.
- **Model encoding.** Presolve elimination, alongside `R-AVAIL` and `R-SKILL` — an ineligible
  `(e, d, s)` variable is never created.
- **Checker encoding.** Verify each flexi assignment against the supplied flag for that day. **Never
  recompute eligibility** — a checker that reaches for quarter T-3 is testing the caller.
- **Explainer text.** `Bram is not flexi-eligible on Wed 1 July (new quarter); he is eligible through Tue 30 June.`
- **Provenance.** Law of 16 November 2015 on various social-affairs provisions, art. 4 §1 — note this is
  a *wet houdende diverse bepalingen inzake sociale zaken*, not a programmawet, and it has been amended
  repeatedly since. The amending instrument behind the 1 July 2026 expansion is the **Wet van 28 juni
  2026 houdende diverse bepalingen inzake flexi-jobs**, BS 2 July 2026, in force 1 July 2026.

  **The T-3 test this rule encodes is unchanged**, which is the part that matters here. What the 2026
  law moved is the pensioner route: pension status is now read in quarter T rather than T-2, so
  somebody newly retired can start at once. The eighty-percent employment test in T-3 for everybody
  else is untouched. A pensioner branch is therefore missing from the predicate above rather than
  wrong in it.

  Two exclusions survive in every sector: artistic, artistically-technical and artistically-supporting
  functions, and sex workers in PC 302 — the second lands inside this project's target sector.

  **The income ceiling is carried by three different figures** — €18,000, €18,440 and €18,880 — and
  which is the social-security ceiling and which the indexed fiscal exemption was not settled. It is
  documentation rather than a model input, because the ceiling is folded into
  `max_hours_this_week` upstream, so no predicate here reads a euro amount.

<a id="rule-r-dimona-flx"></a>
### `R-DIMONA-FLX` — Dimona filing gate

- **Statement.** A flexi shift may only be assigned if a Dimona declaration of type `FLX` covering it
  has been filed and the NSSO returned `OK`.
- **Predicate.** For every `e` with `contract(e) = flexi` and every `(d, s) ∈ O`:

  ```
  x[e, d, s] = 1   ⟹   dimona_ok[e, d] = true
  ```

  The NSSO returns `OK` or `NOK` at filing; only `OK` permits declaring the worker as flexi in the
  quarterly DmfA. `NOK` means the worker may not start, so this is a gate on the roster, not a
  post-hoc formality.
- **Class.** Hard, non-relaxable, external. The filing state is data the service reads and never sets.
- **Two filing regimes, and why the model cares.** The obligation differs by contract form:
  - **Verbal flexi contract** — one Dimona **per working day**, naming the start and end times of that
    day's work.
  - **Written flexi framework contract** — one Dimona IN and one OUT **per quarter**, plus a mandatory
    daily electronic time registration of hours actually worked.

  A Dimona **may never cross a quarter boundary** in either regime, because the conditions are retested
  each quarter. This is the mechanism behind `R-FLEXI-ELIG`'s per-day indexing.
- **The replanning consequence, which is the interesting one.** Under the verbal regime the filing names
  the day's start and end times, so **moving or dropping a flexi worker's shift requires re-filing,
  while moving a salaried worker's shift requires nothing.** Administrative disruption is therefore
  *asymmetric by contract type*, and a disruption metric that counts both changes as one unit is
  understating the real cost of the flexi change.

  This is a substantive input to [`model.md`](../internals/model.md): it is a defensible, externally-grounded reason for a
  contract-weighted disruption metric, which is D3/D4 territory rather than the D2 that ships. **Not a
  reason to change the shipped metric** — a reason the alternatives are not arbitrary.

  The D0–D4 study is done and deliberately left this out, and its result raised the value of
  the idea rather than lowering it. D0, D1 and D2 never diverge on the committed set, because their
  weights multiply every candidate repair by the same constant and a constant factor reorders nothing.
  A per-contract weight would not behave that way: it varies with **which employee** is chosen, and
  candidates differ precisely in that. It is the one weight in this family that would change the answer
  on this distribution — and its size is a fact about a tenant's back office, so it waits for the
  captured corpus rather than for a number someone invents.
- **The short-notice substitution gate.** Replacing an absent flexi worker with another flexi worker
  requires a fresh `OK` before the substitute starts. For this project's headline scenario — a Saturday
  sick call — that materially narrows which substitutes are reachable in time, and it narrows it in a
  way that has nothing to do with availability or skill. A replan that ignores it proposes repairs that
  cannot legally be executed that morning.

  Consequence: `dimona_ok[e, d]` is not static within a solve horizon. For a same-day replan the caller
  must distinguish *already filed* from *fileable in time*, and the second is a judgement about NSSO
  turnaround the service cannot make. **The conservative reading is taken — only `OK` counts** — and the
  optimistic reading is deferred with the [capture work](../archive/capture.md), specified and not built, where replay against real incumbent decisions
  can show whether it costs real repairs.

  **The filing deadline is settled, and the twenty-four-hour figure is not a rule**. The NSSO
  instruction defines a timely filing as *"vóór de aanvang van de prestaties"* — before the work
  starts. Vendor guidance stating twenty-four hours before start is tooling lead time with no
  instrument behind it. The earliest a `FLX` filing may be made is one month before the quarter opens;
  a verbal agreement needs one per day carrying the start and end times, a written one needs a single
  filing per quarter.

  This narrows what the conservative reading is *about*. The question for a same-day replan is not whether
  a day of notice exists but whether a filing returns `OK` before the shift starts, which is a much
  shorter bar than the deadline this rule was written against. **The NSSO instruction is guidance
  rather than law** and names no instrument itself; the statutory hook behind the Dimona obligation is
  not cited here because it was not confirmed.
- **Parameters.** `dimona_ok[e, d]`, boolean, caller-supplied, mandatory for flexi contracts.
  `filing_regime[e] ∈ {verbal, written}`, informational — it does not change the predicate, only
  the disruption weighting above.
- **Model encoding.** Presolve elimination, folded into the same eligibility filter as `R-FLEXI-ELIG`.
  The two rules are separate IDs because they fail for different reasons and produce different operator
  actions — *this person cannot hold a flexi job* versus *the paperwork is not in* — and the explainer
  must not conflate them.
- **Checker encoding.** Verify each flexi assignment against the supplied flag.
- **Explainer text.** `No Dimona FLX on file for Gita on Sat; she cannot be rostered to the Evening shift.`
- **Provenance.** NSSO administrative instructions on Dimona for flexi-job workers (type `FLX`); the
  underlying obligation from the law of 16 November 2015. Administrative instructions are **not**
  statute and are revised quarterly — cite the instruction version in force, and expect this section to
  need rereading more often than the Arbeidswet ones do.


---

*Where each rule's classification comes from, and why the model and the checker never share a threshold: [`design.md`](../internals/design.md). The legal research behind the provenance column, including two searches that came back negative: [`decisions.md`](../archive/decisions.md#by-theme), under* Rules, legal encoding and provenance.
