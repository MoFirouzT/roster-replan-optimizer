# Structural legal rules

The fourteen rules that carry a named legal instrument and constrain the shape of a person's week: rest, hour ceilings, consecutive days, and the optional pattern rules. [`rules.md`](rules.md) is where they are registered and where each source is set out.

*Assumes: the registry and the legal sources in [`rules.md`](rules.md); the reference period it explains, which [`R-MAX-WEEKLY`](#rule-r-max-weekly) approximates; the symbols in [`model.md`](../internals/model.md).*


The rules encoded from labour law. Every one is **hard**: a roster that breaks one is not a
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

- `R-MIN-SHIFT` reads **`span`**: art. 21 governs the *work period*, and a "prestatie" may contain
  short meal or coffee breaks without becoming two periods.
- `R-MAX-WEEKLY` and `R-MAX-DAILY` read **`work_hours`**: they are working-time ceilings.

There is deliberately no single `hours(d, s)`. One symbol would make one of those rules wrong by about
a break per shift, in a direction no test would notice until a checker and a model disagreed over
fifteen minutes. Definitions live in [`model.md`](../internals/model.md#sets-and-data).

<a id="rule-r-min-shift"></a>
### `R-MIN-SHIFT`: minimum work period

> **Class correction.** The registry carried this as a hard constraint. **With fixed shift instances it
> cannot be one.** Shift types have durations defined by the tenant profile, and `x[e, d, s]` either
> assigns a whole instance or none of it; no roster the model can express contains a work period the
> catalogue does not already contain. A too-short shift is therefore a **defect in the profile, not in
> the roster**, and a constraint that no reachable solution can violate is not a constraint, it is
> validation wearing one.
>
> Reclassified: **input validation**, and [`api.md`](api.md#what-gets-rejected-before-any-solve) lists it. The roster checker does not
> implement it, which is the one intended exception to *every rule gets a checker encoding*.

- **Statement.** Every work period in the tenant's shift catalogue lasts at least the applicable
  minimum.
- **Predicate.** Over the profile rather than over a roster, for every shift type `s`:

  ```
  span(d, s)  ≥  min_period_hours   for every d with (d, s) ∈ O
  ```

  Gross span, not net: a work period interrupted by a coffee break is still one period. Checked once at
  profile load and on every profile change, not per solve.
- **Class.** Input validation. **Becomes structural if shift boundaries ever become decision
  variables rather than data**, at which point it needs a real encoding and a checker
  entry. Recorded here so that transition is a known cost rather than a discovery.
- **Parameters.** `min_period_hours`, default **3** (art. 21). Horeca derogation to **2**, available
  only under two cumulative conditions: a motivated notification to the chair of the joint committee
  (required since 1 January 2018), and a registered cash-register system (GKS) in the establishment.
  Several worker categories fall outside art. 21 entirely (domestic staff, commercial
  representatives, management and confidential posts, family businesses) plus the five categories of
  the Royal Decree of 18 June 1990.
- **Validation encoding.** Reject the profile with the offending shift type named. A derogated minimum
  requires a non-empty `derogation_basis`, as with `R-REST-GAP`.
- **Explainer text.** Not an explainer case: a profile is rejected at load, before any solve exists to
  explain. [`api.md`](api.md#what-gets-rejected-before-any-solve) owns the message.
- **Provenance.** Arbeidswet art. 21: the statute, *not* art. 19; the FPS Employment summary page
  misattributes this one. Exempt categories: Royal Decree of 18 June 1990. Horeca limb: **CAO nr. 7
  of 25 June 1997** in joint committee 302, art. 10 for the two-hour work period and art. 9 for the
  ten-hour weekly floor, made generally binding by the Royal Decree of 25 May 1999 and amended as
  recently as the Royal Decree of 19 January 2023. The notification and GKS conditions
  above are attached to that derogation, but the instrument that added them in 2018 was not found;
  they are stated here from agreeing secondary sources.

  **The unresolved claim is now resolved, and the answer is that the rule does not exist.** A
  secondary source asserted a change effective 1 June 2026 (minimum contracts of 3h48 per week with
  performances of at least 3 hours per day) which would contradict the two-hour horeca figure. **No
  primary instrument applies it to horeca.** What exists is the Wet van 18 mei 2026 (BS 1 June 2026),
  which lowered the *general* part-time weekly floor from a third to a tenth of a full-timer's week;
  a 38-hour week makes that 3h48. It does not reach PC 302, whose ten-hour floor is set by CAO rather
  than derived from that fraction, and it left art. 21 untouched: the consolidated text still carries
  `<W 1989-12-22/31>` as its last marker, so the three-hour half of the claim has no source either.

  **It is a live dispute rather than a dead rumour**, which is why it stays on the record. The claim
  is the employer-side position in the sector, contested by ACV, who report the Ministry of Employment
  agreeing with them. Nothing here changes until PC 302 or the FPS issues something concrete.

<a id="rule-r-rest-gap"></a>
### `R-REST-GAP`: daily rest

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
- **Class.** Hard. Art. 38ter §2 does permit derogations (force majeure, split shifts, team changes in
  shift work) so the *parameter* is tenant-configurable downward against a recorded derogation basis.
  The rule itself is never dropped.
- **Parameters.** `min_rest_hours`, default **11**. A tenant may lower it only with a non-empty
  `derogation_basis` string, validated at profile load. There is no upward cap: a stricter tenant is
  always lawful.
- **Model encoding.** Pairwise `≤ 1` over the conflicting-pair set, per employee. At these instance sizes
  the pair set is small and the encoding is transparently the same object the checker walks, which is
  worth more here than tightness.

  **Alternative, measured and rejected**: one optional interval variable per
  `(employee, shift instance)` inflated by `min_rest_hours`, under a single `add_no_overlap` per
  employee. It is 23% smaller and builds 14% faster, and searches 15% slower on 28 of 28 cases: a 4%
  better total on the committed set that reverses to 11% worse on larger cold instances. It also
  coarsens the gate to one literal per employee-week, losing the slot coordinate this encoding
  reports. The scaling argument for it is about the **horizon**, which is fixed at one week here, so
  it remains untested rather than disproved: see
  [`studies/rest-gap-encoding.md`](../studies/rest-gap-encoding.md).
- **Checker encoding.** Sort the employee's assigned instances by start time, walk consecutive pairs,
  compare each gap against the parameter. `last_shift_end_before_horizon[e]` is the predecessor of the
  first instance: **not a special case, just the zeroth element**, which is the framing that stops the
  boundary being forgotten.
- **Explainer text.** `Ana finishes Fri 23:00 and would start Sat 07:00: 8h rest, 11h required.`
- **Provenance.** Arbeidswet art. 38ter §1: a worker is entitled, per 24-hour period between the end
  and resumption of work, to at least eleven consecutive hours of rest. Transposes **WTD art. 3**,
  which sets the same eleven hours.

<a id="rule-r-max-weekly"></a>
### `R-MAX-WEEKLY`: the weekly budget

- **Statement.** An employee's assigned hours this week do not exceed the budget the caller supplied
  for them.
- **Predicate.** For every `e ∈ E` and every week `w ∈ W`:

  ```
  Σ_{(d, s) ∈ O, week(d) = w} work_hours(d, s) · x[e, d, s]  ≤  max_hours_this_week[e]
  ```

  Net working time, not span: breaks are not working time. Pinned past shifts are inside this sum, not
  exempt from it. At a one-week horizon `W` has one member and this is the sum over all of `O`, which
  is what it was before weeks were named here.
- **Class.** Hard.
- **Parameters.** `max_hours_this_week[e]`, hours, caller-supplied and mandatory. No default: a missing
  budget is a malformed payload, because the safe fallback (some fixed weekly ceiling) is precisely
  the wrong model this rule exists to avoid (see [the reference period](rules.md#the-reference-period-and-why-r-max-weekly-is-a-budget)).
- **What the caller is actually computing.** The section above says the caller resolves the reference
  period into one number. Naming its three components makes that auditable, because all three are
  legally distinct and only one of them is an average:

  1. **The residual average allowance**: art. 19 sets 8h/day and 40h/week in the statute, reduced to
     **38h/week** since 1 January 2003; art. 26bis §1 measures it as an average over a reference period
     that is the calendar quarter by default and extendable to at most one year by royal decree,
     sectoral or company CBA, or work-rules amendment.
  2. **The internal limit**, art. 26bis §1bis: at no moment in the reference period may cumulative
     hours worked exceed the permitted average, times the weeks elapsed, by more than **143 hours**.
     This is the provision that makes a single-week budget coherent at all: without a bound on
     cumulative excess, no week could be assessed locally.
  3. **The absolute weekly ceiling**: the derogation ladder caps any individual week regardless of the
     average: generally **50h**, and **45h** under art. 20bis flexible schedules.

  The budget is the minimum of the three. **WTD art. 6** independently caps average weekly working time
  at 48h over a reference period of up to four months (art. 16(b)); the Belgian computation is stricter
  in the ordinary case and the caller owns reconciling them.
- **Model encoding.** One linear inequality per employee over eligible pairs.
- **Checker encoding.** Sum `hours(d, s)` over the employee's assignments and compare to the supplied
  budget. **The checker never recomputes the budget**: restating the constraint from this registry,
  because this is the single place a well-meaning checker most reliably goes wrong. A checker that
  reaches for the reference period is testing the caller, and it will disagree with the model for
  reasons that are defects in neither.
- **Payload validation, distinct from roster checking**. That the supplied budget does not exceed the
  absolute weekly ceiling *is* locally verifiable, and it is worth verifying, but as **input
  validation**, not as a roster violation. A too-large budget is a bad payload; it is not a property of
  the roster, and reporting it as an `R-MAX-WEEKLY` violation would blame the solver for the caller's
  arithmetic. [`api.md`](api.md#what-gets-rejected-before-any-solve) lists it.
- **Explainer text.** `Hugo is budgeted 32h a week and this roster assigns him 40h in the week from day 0.`
- **Provenance.** Arbeidswet art. 19 and art. 26bis §1, §1bis. **WTD art. 6** and art. 16(b).

<a id="rule-r-max-period"></a>
### `R-MAX-PERIOD`: what is left of the reference period

- **Statement.** An employee's assigned hours across the whole horizon do not exceed the working time
  the caller says remains in their rolling reference period.
- **Predicate.** For every `e ∈ E` with a supplied remainder:

  ```
  Σ_{(d, s) ∈ O} work_hours(d, s) · x[e, d, s]  ≤  max_hours_this_period[e]
  ```

  The whole horizon, deliberately: this is the one rule here whose span is the payload rather than a
  week, because the quantity it bounds is a pool rather than a rate.
- **Class.** Hard, and **optional**: absent means the caller had nothing to add beyond the weekly
  ceiling. It is the only rule in this registry whose absence is ordinary rather than a defect.
- **Parameters.** `max_hours_this_period[e]`, hours, caller-supplied. No default and no derivation:
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
- **Provenance.** Arbeidswet art. 26bis §1: the average measured over the reference period, which is
  the calendar quarter by default and at most a year by royal decree or CBA. **WTD art. 16(b)** allows
  a reference period up to four months, and art. 19 caps its extension; the Belgian computation is the
  stricter one and the caller owns reconciling them.

<a id="rule-r-max-daily"></a>
### `R-MAX-DAILY`: daily maximum

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
  | 9 | art. 20 §1: schedule giving at least a half-day's rest beyond the weekly rest day |
  | 9 | art. 20bis: flexible schedules (paired with a 45h weekly ceiling) |
  | 10 | art. 20 §2: worker away from home more than 14h/day for distance reasons |
  | 11 | art. 22 1°: successive shift work |
  | 12 | art. 22 2°: continuous processes |

  Further derogations exist under art. 23–26 and by sectoral CBA; the profile schema stores the basis
  as an opaque string and does not attempt to model the ladder's own preconditions.
- **Honest note on redundancy.** At one shift per day with 8h shifts this rule is nearly implied by
  `R-REST-GAP`, which already forbids most same-day pairs. It is **not** redundant in general: split
  shifts are lawful and common in horeca: two short periods in one day, separated by enough rest to
  satisfy `R-REST-GAP` while their sum binds here. Encoding it costs one inequality per employee-day,
  and the checker needs it independently regardless of what the model happens to make unreachable.
- **Model encoding.** One linear inequality per `(employee, day)`.
- **Checker encoding.** Group the employee's assignments by start day, sum `work_hours` per group.
- **Explainer text.** `Emma is assigned 12h on Wed; her contract allows 8h.`
- **Provenance.** Arbeidswet art. 19; derogations art. 20 §1, art. 20 §2, art. 20bis, art. 22 1°–2°,
  art. 23–26.

<a id="rule-r-consec-days"></a>
### `R-CONSEC-DAYS`: consecutive working days

> **Provenance correction.** The registry originally carried this as `labour law [CITE]`. **That is
> wrong, and the citation search is what surfaced it.** Belgian law sets no general cap on consecutive
> working days for adult workers. The commonly quoted figure of six derives from art. 16, which
> requires compensatory rest for Sunday work *within the six days following that Sunday*: a rule about
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
- **Class.** Hard, in the sense that the model enforces it, but the provenance is contractual, so a
  tenant may disable it entirely rather than only loosen it. This is the one rule in this section that
  may legitimately be switched off.
- **Parameters.** `max_consecutive_days`, default **6**, tenant-configurable including *off*.
  `consecutive_days_worked_before_horizon[e]`, caller-supplied, mandatory when the rule is enabled.

  **Per employee where one is supplied**. `Employee.max_consecutive_days` overrides the
  tenant's number for that person and absence means the tenant's applies. This is not a second rule
  (same ID, same encodings, same explainer text); only the place the limit is read from changes, and
  it is what lets one workforce hold two limits, which is how the only real dataset here states it.
- **Model encoding.** Sliding-window sums: `|D| − L + p` inequalities per employee, each over `L + 1`
  booleans, plus one reification per `(employee, day)` for `w`.

  **Alternative, measured and rejected**: a `regular` automaton over the worked/not-worked
  sequence, whose states count the current streak. It is the textbook encoding for sequence rules,
  which is why the study had to confirm it rather than assume it, and it is **19% slower to search on
  28 of 28 cases**, because at a seven-day horizon with a six-day limit this encoding builds exactly
  **one** window per employee, so the automaton competes against a single inequality. It also gates
  only per employee-week, losing the day coordinate. It does not express `R-WEEKLY-REST` either: a
  continuous 35-hour free run is measured in hours, not days. See
  [`studies/regular-constraint.md`](../studies/regular-constraint.md).
- **Checker encoding.** Walk days in order tracking a streak counter initialised to
  `consecutive_days_worked_before_horizon[e]`, reset on any unworked day.
- **Explainer text.** `Finn already worked 4 days before Monday and this roster adds 3 more: 7 consecutive, 6 allowed.`
- **Provenance.** **Operational / sectoral CBA.** No general statutory basis for adult workers; see the
  correction above.

<a id="rule-r-weekly-rest"></a>
### `R-WEEKLY-REST`: weekly rest

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
  lies inside it, so a rest straddling a boundary counts for neither: a known conservatism, at
  every internal boundary rather than only at the end.
- **Model encoding.** Candidate windows plus at-least-one. Introduce `r[e, j]` for each candidate
  window `j`, require `Σ_j r[e, j] ≥ 1`, and for each shift instance overlapping window `j` add
  `r[e, j] ⟹ x[e, instance] = 0`: a reified implication CP-SAT handles natively.

  **Candidates are bounded, which is what makes this tractable**: it suffices to anchor windows at
  `end(d, s)` for each shift instance, plus the horizon start. Any feasible rest window can be slid
  later until its left edge meets the end of some shift without shrinking below the threshold, so an
  anchored candidate exists whenever any window does. The candidate count is therefore `|O| + 1`, not a
  function of time granularity, no discretisation, no chosen minute resolution.
- **Checker encoding.** Sort the employee's assigned intervals, prepend
  `last_shift_end_before_horizon[e]`, and take the maximum gap between consecutive intervals **within
  each week**, clipping the roster to that week's span. Compare to the parameter. Independent of the
  candidate-window construction, which is the point: the model searches, the checker measures.
- **Known conservatism, stated rather than hidden.** The rest window is
  required to lie **within the week it counts for**. A lawful roster whose 35-hour block straddles a
  boundary is therefore rejected, and it counts for neither of the two weeks it spans.

  At the horizon's own end this is nearly harmless on a seven-day horizon (one such block must exist
  inside any week) and it bites on shorter ones. At an *internal* boundary it bites on every horizon
  longer than a week, which is the price of measuring the rule per week rather than per rolling
  seven-day window; the rolling form has no week to name, and naming the week is the reporting
  day coordinate the explainer needs.

  The fix for both is the same caller-supplied forward-looking commitment, symmetric with
  `last_shift_end_before_horizon`, and it is **deferred**: it would oblige the caller to promise
  something about a week it has not planned yet, which is a heavier contract than the conservatism
  costs. Revisit if short horizons, or rosters built around a straddling rest, become a real use case.
- **Interaction with `R-SUNDAY`.** Art. 38ter §3 builds the 35 hours by adding art. 38ter §1's eleven
  hours to *either* Sunday rest (art. 11) or compensatory rest for Sunday work (art. 16); art. 17 gives
  shift workers a distinct form: 24 uninterrupted hours weekly with at least 18 of them falling on
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
### `R-MAX-WEEKENDS`: weekends worked

- **Statement.** An employee works at most a stated number of weekends across the horizon. A weekend
  counts once however many of its days are worked.
- **Predicate.** For every `e ∈ E` with a supplied limit, where `weekend(d) ⟺ d mod 7 ∈ weekend_days`:

  ```
  | { w : ∃ (d, s) ∈ O with week_of(d) = w ∧ weekend(d) ∧ x[e, d, s] = 1 } |  ≤  max_weekends[e]
  ```

- **Class.** Hard, and **optional** in `R-MAX-PERIOD`'s sense: absent means the caller is not asking
  for it, which is ordinary rather than a defect. Hard rather than priced because the only formulation
  measured against real data states it as a constraint, and because hard here does not mean
  unrelaxable: the gate names it in a core, so a planner who must breach one is told which one.
- **Parameters.** `max_weekends[e]`, per employee, caller-supplied. Per employee because the one
  workforce this project has measured varies it from 1 to 3 inside a single team.

  `weekend_days ⊆ {0…6}`, on `RuleParams`, positions within a week. **Caller-supplied and empty by
  default**, and the emptiness is the point: this domain has no calendar, so [`model.md`](../internals/model.md) fixes that a
  week is a position in the horizon and never a Monday. Which of its days are the weekend is a fact
  only the caller holds, and an empty set switches the rule off.
- **Why a count of weekends and not of weekend days.** Two Saturdays are two weekends and a
  Saturday-Sunday pair is one. The rule people actually hold is about how many of their weekends are
  taken, not how many days it cost, which is why this counts weeks and not assignments.
- **Model encoding.** One boolean per (employee, week), forced up by any weekend assignment, summed
  over weeks. The implication is needed in one direction only: the variable appears in a `≤`
  constraint and nowhere else.
- **Checker encoding.** Collect the distinct weeks holding a weekend assignment and compare the set's
  size. Deliberately different arithmetic from the model's: a set rather than a sum of forced booleans.
- **Explainer text.** `Ana works 3 weekends; 2 allowed.`
- **Provenance.** Operational, or a CBA. Not statutory: Belgian law governs Sunday work
  (`R-SUNDAY`) and weekly rest (`R-WEEKLY-REST`), neither of which is a budget of weekends.

<a id="rule-r-min-days-off"></a>
### `R-MIN-DAYS-OFF`: days off in blocks

- **Statement.** A stretch of days off inside the horizon is at least a stated number of days long.
- **Predicate.** For every `e ∈ E` with a supplied minimum, every gap length `L` from 1 to
  `min_consecutive_days_off − 1`, and every day `d` with `d + L + 1 < days`:

  ```
  worked[e, d] − Σ_{j=1..L} worked[e, d+j] + worked[e, d+L+1]  ≤  1
  ```

  where `worked[e, d] ⟺ ∃ s : x[e, d, s] = 1`. The left side is 2 exactly on the pattern being
  forbidden (worked, then `L` days off, then worked) and at most 1 on everything else.
- **Class.** Hard and **optional**, on the same footing as `R-MAX-WEEKENDS`.
- **Parameters.** `min_consecutive_days_off[e]`, per employee. A minimum of 1 forbids nothing, since
  every gap between two worked days is at least one day long, and is treated as absent.
- **Only interior stretches are judged, and that is a rule rather than a shortcut**. A
  stretch of days off reaching either end of the horizon may continue outside it, and a roster cannot
  be judged on days it does not contain. Applied without that latitude the rule failed **every one of
  the 26 published rosters** in the benchmark set that supplied it: 26 rosters being wrong is not the
  reading to prefer. `R-WEEKLY-REST` already takes the same view of its own edges.
- **Model encoding.** The forbidden pattern above, one gated inequality per (employee, gap length,
  start). The boundary latitude needs no special case: the pattern requires a worked day on both
  sides, so an edge stretch is never matched.
- **Checker encoding.** Walk the days off, measure each stretch, and skip those touching either end.
  Here the latitude has to be stated, which is the usual asymmetry between the two readings.
- **Explainer text.** `Bram gets 1 day off from day 4; 2 consecutive required.`
- **Provenance.** Operational, or a CBA.

<a id="rule-r-min-block"></a>
### `R-MIN-BLOCK`: blocks of working days

- **Statement.** A block of consecutive working days inside the horizon is at least a stated number
  of days long.
- **Predicate.** `R-MIN-DAYS-OFF`'s pattern with worked and off exchanged. For every gap length `L`
  from 1 to `min_consecutive_days_worked − 1` and every day `d` with `d + L + 1 < days`:

  ```
  −worked[e, d] + Σ_{j=1..L} worked[e, d+j] − worked[e, d+L+1]  ≤  L − 1
  ```

  The left side is `L` exactly on the pattern being forbidden (off, then `L` days worked, then off)
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
### `R-MAX-SHIFT-TYPE`: how many of one shift

- **Statement.** An employee works at most a stated number of assignments of a given shift type.
- **Predicate.** For every `e ∈ E` and every capped shift type `s`:

  ```
  Σ_{d : (d, s) ∈ O} x[e, d, s]  ≤  max_shifts_per_type[e][s]
  ```

- **Class.** Hard and **optional**, per employee and shift type.
- **Why not a total.** A cap on shifts in general is `R-MAX-WEEKLY` in another unit. This one says
  *four nights a month*, and a cap of **zero is a prohibition**: the shape a total cannot express.
- **A cap of zero is a rule, not an impossibility**, so it stays here rather than moving into the
  presolve's exclusions. Presolve removes pairs that cannot be worked; a cap the tenant chose should
  be reportable as a rule the roster broke.
- **Model encoding.** One gated sum per (employee, capped type).
- **Checker encoding.** Count the employee's assignments of that type and compare.
- **Explainer text.** `Ana works 5 N shifts; 4 allowed.`
- **Provenance.** Operational, or a CBA.

<a id="rule-r-min-hours"></a>
### `R-MIN-HOURS`: the floor

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
- **Provenance.** Operational, or a CBA: a guaranteed-hours clause is the usual source.

<a id="rule-r-succession"></a>
### `R-SUCCESSION`: a shift that may not follow another

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
  automaton, for the reason [`studies/regular-constraint.md`](../studies/regular-constraint.md) gives:
  the pairs are local, the expansion is small, and the day coordinate survives into the violation.
- **Checker encoding.** Group the roster by employee and day, then check every consecutive pair. An
  employee holding two shifts on one day makes several pairs and each is checked: the rule is about
  the pairing, not about a canonical shift for the day.
- **Reported on the second day**, the one the forbidden shift falls on, in both readings.
- **Explainer text.** `Ana works M on day 4, which may not follow N.`
- **Provenance.** Operational, or a CBA.

<a id="rule-r-day-off"></a>
### `R-DAY-OFF`: a day granted off

- **Statement.** An employee is not assigned any shift that *starts* on a day they have been granted
  off.
- **Predicate.** For every `e ∈ E`, `d ∈ days_off[e]` and `s` with `(d, s) ∈ O`:

  ```
  x[e, d, s] = 0
  ```

- **Class.** Hard and **optional**, on `R-MAX-WEEKENDS`'s terms: an empty set is a caller not asking.
- **Why this is not `R-AVAIL`**. `R-AVAIL` refuses an assignment overlapping an interval,
  and a day off is not an interval. A shift starting at 22:00 the evening *before* runs six hours into
  the granted day and overlaps any interval covering it, so an interval reading refuses a shift the
  grant never meant to touch, while the day-indexed reading is exact. **Start-day attribution is what
  makes the difference**, and it is the convention this registry fixes for exactly this class of
  question.

  This is not hypothetical. The nurse-rostering importer drops its source's days off rather than
  translate them, and states the reason: every night shift before a day off was reported as `R-AVAIL`.
  That was the collision above, met from outside.
- **A grant, not an absence.** `R-AVAIL` splits by provenance: an absence is never relaxable, a
  declared unavailability is. This is a third thing: something the employer gave, which a planner may
  need to take back with the employee's agreement. Hard, and gated like every hard rule, so a core
  names it rather than a planner discovering it as an unexplained shortfall.
- **Model encoding.** One gated `x = 0` per (employee, granted day, shift starting that day). Gated
  rather than removed in the presolve, for `R-MAX-SHIFT-TYPE`'s reason: presolve removes the
  impossible, and a day the tenant granted is a rule a roster can break and be told about.
- **Checker encoding.** Membership of the granted set, read against the day the shift starts on.
  Deliberately not interval intersection: that is the reading this rule exists because it cannot do.
- **Explainer text.** `Ana is assigned day 3 07:00-15:00 (M) on a granted day off.`
- **Provenance.** Operational, or a CBA.

---

*Where each rule's classification comes from, and why the model and the checker never share a threshold: [`design.md`](../internals/design.md). The legal research behind the provenance column, including the two searches that found no rule: [`decisions.md`](../decisions.md#by-theme), under* Rules, provenance and the reference period.
