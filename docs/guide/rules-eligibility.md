# Eligibility gates

The two rules whose condition is resolved upstream and enters the solve as data. Both are statutory, and both depend on facts a one-week payload cannot hold, which is why they are specified apart from the rest. [`rules.md`](rules.md) registers them.

*Assumes: the registry and the legal sources in [`rules.md`](rules.md); the payload fields the resolved booleans arrive in, [`api.md`](api.md).*


`R-FLEXI-ELIG` and `R-DIMONA-FLX` share an architecture, and it is the one already established for
`R-MAX-WEEKLY`: **the condition is resolved upstream and enters the solve as data**.

Not by preference, by necessity. Between them these two rules depend on employment at *other*
employers, on quarters that ended before the horizon began, on year-to-date earnings, on sectoral
opt-outs, and on a response the NSSO returns from its own records. A one-week payload contains none of
it, and no amount of solver cleverness recovers it. What reaches the model is a per-employee, per-day
boolean, and the checker verifies against that boolean rather than re-deriving it.

The cost is the same one the reference period carries and is stated the same way: **correctness depends
on a computation this service does not perform.**

<a id="rule-r-flexi-elig"></a>
### `R-FLEXI-ELIG`: flexi-job eligibility

- **Statement.** Only an employee the caller has certified as flexi-eligible for the quarter containing
  a shift may be assigned that shift under a flexi contract.
- **Predicate.** For every `e` with `contract(e) = flexi` and every `(d, s) ∈ O`:

  ```
  x[e, d, s] = 1   ⟹   flexi_eligible[e, d] = true
  ```

  **Indexed by day, not by employee.** A horizon may straddle a quarter boundary (the week containing
  30 June and 1 July) and eligibility is retested per quarter, so one employee can be eligible on
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
  except sectors that opted out: a scope inversion from the previous enumerated-sectors regime. The
  annual ceiling rose from €12,000 to €18,000 at the same date, with the employee-side fiscal
  exemption at €18,440 for 2026 income and no ceiling for pensioners. Horeca additionally caps the
  flexi hourly wage at €21.00 (€22.61 including flexi holiday pay): a **wage** rule, outside this
  model's scope, recorded so nobody mistakes it for a rostering constraint.
- **Parameters.** `flexi_eligible[e, d]`, boolean, caller-supplied, mandatory for any employee with a
  flexi contract. Absence is a malformed payload, never a default of `true`.
- **Treatment of the income ceiling**. Fold it into `max_hours_this_week[e]` as a fourth
  term in that budget's `min()`, rather than adding a parallel euro-denominated budget. The caller
  already converts a reference period into weekly hours; converting a remaining income allowance into
  remaining hours is the same kind of arithmetic against a known wage, and it keeps one budget concept
  in the model instead of two.
- **Model encoding.** Presolve elimination, alongside `R-AVAIL` and `R-SKILL`: an ineligible
  `(e, d, s)` variable is never created.
- **Checker encoding.** Verify each flexi assignment against the supplied flag for that day. **Never
  recompute eligibility**: a checker that reaches for quarter T-3 is testing the caller.
- **Explainer text.** `Bram is not flexi-eligible on Wed 1 July (new quarter); he is eligible through Tue 30 June.`
- **Provenance.** Law of 16 November 2015 on various social-affairs provisions, art. 4 §1. Note this is
  a *wet houdende diverse bepalingen inzake sociale zaken*, not a programmawet, and it has been amended
  repeatedly since. The amending instrument behind the 1 July 2026 expansion is the **Wet van 28 juni
  2026 houdende diverse bepalingen inzake flexi-jobs**, BS 2 July 2026, in force 1 July 2026.

  **The T-3 test this rule encodes is unchanged**, which is the part that matters here. What the 2026
  law moved is the pensioner route: pension status is now read in quarter T rather than T-2, so
  somebody newly retired can start at once. The eighty-percent employment test in T-3 for everybody
  else is untouched. A pensioner branch is therefore missing from the predicate above rather than
  wrong in it.

  Two exclusions survive in every sector: artistic, artistically-technical and artistically-supporting
  functions, and sex workers in PC 302: the second lands inside this project's target sector.

  **The income ceiling is carried by three different figures** (€18,000, €18,440 and €18,880) and
  which is the social-security ceiling and which the indexed fiscal exemption was not settled. It is
  documentation rather than a model input, because the ceiling is folded into
  `max_hours_this_week` upstream, so no predicate here reads a euro amount.

<a id="rule-r-dimona-flx"></a>
### `R-DIMONA-FLX`: Dimona filing gate

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
  - **Verbal flexi contract**: one Dimona **per working day**, naming the start and end times of that
    day's work.
  - **Written flexi framework contract**: one Dimona IN and one OUT **per quarter**, plus a mandatory
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
  reason to change the shipped metric**: a reason the alternatives are not arbitrary.

  The D0–D4 study is done and deliberately left this out, and its result raised the value of
  the idea rather than lowering it. D0, D1 and D2 never diverge on the committed set, because their
  weights multiply every candidate repair by the same constant and a constant factor reorders nothing.
  A per-contract weight would not behave that way: it varies with **which employee** is chosen, and
  candidates differ precisely in that. It is the one weight in this family that would change the answer
  on this distribution, and its size is a fact about a tenant's back office, so it waits for the
  captured corpus rather than for a number someone invents.
- **The short-notice substitution gate.** Replacing an absent flexi worker with another flexi worker
  requires a fresh `OK` before the substitute starts. For this project's headline scenario, a Saturday
  sick call, that materially narrows which substitutes are reachable in time, and it narrows it in a
  way that has nothing to do with availability or skill. A replan that ignores it proposes repairs that
  cannot legally be executed that morning.

  Consequence: `dimona_ok[e, d]` is not static within a solve horizon. For a same-day replan the caller
  must distinguish *already filed* from *can still be filed in time*, and the second is a judgement about NSSO
  turnaround the service cannot make. **The conservative reading is taken, only `OK` counts**, and the
  optimistic reading is deferred with the capture work, specified and not built, where replay against real incumbent decisions
  can show whether it costs real repairs.

  **The filing deadline is settled, and the twenty-four-hour figure is not a rule**. The NSSO
  instruction defines a timely filing as *"vóór de aanvang van de prestaties"*: before the work
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
  `filing_regime[e] ∈ {verbal, written}`, informational: it does not change the predicate, only
  the disruption weighting above.
- **Model encoding.** Presolve elimination, folded into the same eligibility filter as `R-FLEXI-ELIG`.
  The two rules are separate IDs because they fail for different reasons and produce different operator
  actions (*this person cannot hold a flexi job* versus *the paperwork is not in*) and the explainer
  must not conflate them.
- **Checker encoding.** Verify each flexi assignment against the supplied flag.
- **Explainer text.** `No Dimona FLX on file for Gita on Sat; she cannot be rostered to the Evening shift.`
- **Provenance.** NSSO administrative instructions on Dimona for flexi-job workers (type `FLX`); the
  underlying obligation from the law of 16 November 2015. Administrative instructions are **not**
  statute and are revised quarterly: cite the instruction version in force, and expect this section to
  need rereading more often than the Arbeidswet ones do.


---

*Where each rule's classification comes from, and why the model and the checker never share a threshold: [`design.md`](../internals/design.md). The legal research behind the provenance column, including two searches that came back negative: [`decisions.md`](../decisions.md#by-theme), under* Rules, legal encoding and provenance.

---

*Where each rule's classification comes from, and why the model and the checker never share a threshold: [`design.md`](../internals/design.md). The legal research behind the provenance column, including the two searches that found no rule: [`decisions.md`](../decisions.md#by-theme), under* Rules, provenance and the reference period.
