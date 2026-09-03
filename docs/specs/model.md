# The model

**Status:** Implemented 2026-08-20
**Reconstructed 2026-09-02** from [`model.py`](../../roster_replan/model.py),
[`internals/model.md`](../internals/model.md), the nine studies cited below, the mutant
catalogue, and the commits of 2026-08-12 to 2026-08-20. **It is not the work order this
component was built from**; no such document existed
([`spec-reconstruction.md`](spec-reconstruction.md)).
**Depends on:** [`rules.md`](rules.md), whose predicates this encodes.

## Objective

A CP-SAT formulation that produces a legal roster for the rest of the horizon, reports
which rule instances conflict when it cannot, and does both fast enough for a planner to
wait for the answer.

## Motivation

The rules are written down; that does not settle how to encode them, and the encoding
choices are where a scheduling model is usually wrong in ways nobody measures. This
component exists to make each of those choices explicit and, wherever a textbook
alternative exists, to build the alternative and measure it rather than cite it.

Four alternatives were built in full for that purpose and none of them shipped.

## Canonical reference

[`internals/model.md`](../internals/model.md) owns the whole formulation: sets and data,
decision variables, the objective, the constraint families, gates, presolve, symmetry,
warm starting, generation as cold start, the canonical optimum, and where it stops.
[`guide/rules.md`](../guide/rules.md) owns the predicates and one *Model encoding* bullet
per rule. The disruption term is specified in [`disruption.md`](disruption.md).

Nothing in this file restates a formula from those documents.

## Governing reference

None for the formulation itself. Assignment booleans under a weighted sum are standard
technique, and saying so plainly beats inventing a citation.

## Parameters and configuration

The model reads `RuleParams` and `Disruption` off the `Instance` and defaults nothing.
Two build-time switches exist for the rejected alternatives rather than for callers:
`build(sequence="automaton")` keeps the `regular` encoding, and the presolve flag keeps
the comparison runnable.

**Durations are carried in minutes**, because CP-SAT is integral and `work_hours` is
not. That conversion is arithmetic rather than a rule threshold, which is why it sits in
the model rather than in the shared schema.

## Interfaces

```text
model.build(instance, ...)            -> the CP-SAT model and its gate map
model.solve(instance, hint=..., ...)  -> a roster, a status, and the gates that failed
model.violations(roster, instance)    -> the rule instances this roster breaks
```

`hint` is a **separate argument from `instance.incumbent`**, even though the shipped
replan passes the same roster to both. Fusing them would make the warm-start measurement
impossible, because solving with the objective and without the hint is exactly the
baseline that separates the two effects ([`D-082`](../decisions.md#d-082)).

## Layering

- *The model never reaches the checker.*
- *The solver core never reaches the service layer.*

[`domain.py`](../../roster_replan/domain.py) is the only module the model and the checker
may both import, and what it may hold is fixed: data containers and stated conventions,
no predicate and no threshold ([`D-038`](../decisions.md#d-038)).

## Build tasks

- [x] Assignment booleans, with a variable for every pair surviving presolve **and** for
      every pair the incumbent assigned, eligible or not
      ([`D-058`](../decisions.md#d-058)).
- [x] Gate every hard constraint instance on its own assumption literal, so a failed
      solve names the conflict ([`D-044`](../decisions.md#d-044)).
- [x] Enforce eligibility entirely by presolve, retaining the exclusion reasons
      ([`D-045`](../decisions.md#d-045)).
- [x] Encode the shape rules as optional, profile-gated families.
- [x] Warm-start from the incumbent, as a hint that cannot change the answer.
- [x] Build and measure the four alternatives: the `regular` automaton, pattern
      variables, `no_overlap` rest gaps, lexicographic symmetry breaking.
- [x] Pin the optimal value and minimise a canonical criterion over the optimal set
      ([`D-119`](../decisions.md#d-119)).

## Test contract

| Claim | Layer |
| --- | --- |
| The model's feasible set equals the checker's hard-feasible set | brute force **(a)**, 39 micro-instances |
| The encoded optimum is the enumerated optimum, for every metric | brute force **(b)** |
| The two readings agree on which rules a roster breaks | the differential harness |
| A relaxation can only improve or hold the optimum | the property layer, with one test asserting a relaxation actually moves it ([`D-062`](../decisions.md#d-062)) |
| Past shifts are never modified, including where changing them would help | the property layer |
| The rejected alternatives are still correct | `test_studies.py`, six mutants |
| The MILP comparison is like for like | `test_milp.py`, four mutants |

Five mutants name the `model` layer directly, over `test_differential.py`: the period
budget never binding, a wrong rest-gap threshold, a consecutive-days allowance off by
one, and weekly rest and weekly budget spanning the horizon instead of the week.

## Acceptance gate

*Blocks:* everything downstream. The service, the benchmark set and the explainer all
call `solve`.

- [x] Brute force agrees on the feasible set and on the optimum, on 39 committed
      micro-instances.
- [x] Presolve removes about a quarter of the model: **28% off build and 14% off search
      on 28 of 28 paired cases** ([`presolve.md`](../studies/presolve.md)). Free, because
      the exclusion table is computed either way.
- [x] Every committed benchmark run returns `OPTIMAL`. **2,268 of 2,268.**
- [x] Four alternatives measured and rejected: the automaton is 19% slower to search on
      28 of 28 ([`regular-constraint.md`](../studies/regular-constraint.md)); pattern
      variables tie on a replan and fail to prove optimality in 30 s on a cold week the
      assignment model answers in about 20 ms
      ([`pattern-encoding.md`](../studies/pattern-encoding.md)); `no_overlap` rest gaps
      build faster and search slower for a 2% wash
      ([`rest-gap-encoding.md`](../studies/rest-gap-encoding.md)); symmetry breaking
      costs about 4% of build and returns a coin flip
      ([`symmetry-breaking.md`](../studies/symmetry-breaking.md)).
- [!] **The reproducibility promise was false and no test could see it.** The optimum is
      degenerate: the objective value is identical every time and the roster differs on
      **24 of 84 replans and on all 84 cold weeks**. Which roster came back was decided by
      the ortools binary. Nothing caught it because no test looked at *which* optimum
      ([`reproducibility.md`](../studies/reproducibility.md),
      [`D-119`](../decisions.md#d-119)). Canonicalising costs **61% of search time**, and
      the phase can itself run out of budget, in which case it says so rather than
      raising ([`D-126`](../decisions.md#d-126)).
- [!] **CP-SAT is not the faster solver here.** SCIP proves the same optimum faster on
      **24 of 24** cases, 38% faster than the shipped configuration. CP-SAT ships for the
      assumption literals, at a measured cost of about 1.3 ms per solve
      ([`cp-sat-vs-milp.md`](../studies/cp-sat-vs-milp.md),
      [`D-001`](../decisions.md#d-001)).
- [!] **The last unmeasured rejection in the repository was measured and both its reasons
      were wrong.** A longer horizon does not multiply instance size by an order of
      magnitude: size grows linearly. The rejection holds anyway, because four weeks
      solved at once and four solved one at a time reach identical coverage on every case
      tried, and under pressure the single solve is two to six times slower
      ([`horizon.md`](../studies/horizon.md), [`D-116`](../decisions.md#d-116)).

## Measured results

**Where it stops is a number rather than a worry.** A committed case is 8 to 25
employees over one week: a few hundred variables, about 5 ms to build, about 3 ms to
search. The largest foreign instance reaches about **8M variables and 527 s of model
construction**, and returns no roster ([`D-127`](../decisions.md#d-127)): it is refused for
an illegal past rather than searched ([`D-155`](../decisions.md#d-155)). The first genuinely
hard searches came from the same import: 7.71 s to prove optimality, re-measured at 8.43 s,
against a committed-set maximum of 15.4 ms.

**That ceiling belongs to this implementation, not to the formulation.** The 527 s is a
Python loop emitting constraints one at a time, and whether batching moves it is now
measured: it does not ([`gate-cost.md`](../studies/gate-cost.md),
[`D-153`](../decisions.md#d-153)). Writing the proto by hand is slower than the wrapper,
so the ceiling moves only by emitting fewer objects or by leaving Python.

**Build dominates search at one week**, which is why the performance work went to model
construction. That is a statement about one week and not about the model: instance size
grows linearly in the horizon and search does not. The largest single win in the solve
path was memoising `Instance.window`, not presolve
([`D-092`](../decisions.md#d-092)).

**The symmetry null is about the distribution, not the lever.** Across 24 committed cases
there are three interchangeable employees in total, in one case. On a workforce built to
be interchangeable the lever is worth 20% of total time.

## Out of scope

- **The forecast interface.** Demand forecasting sits upstream and nothing of it exists.
- **A separate generation formulation.** Generation is the same solve with an empty
  incumbent: no mode flag and no second route
  ([`D-109`](../decisions.md#d-109), specified in
  [`fairness-generation.md`](fairness-generation.md)).
- **Minimising the infeasibility core.** CP-SAT's core is sufficient rather than
  smallest, and deletion on top belongs with the explainer
  ([`explanation.md`](explanation.md)).
- **Shipping any of the four measured alternatives.** They stay in the tree so the
  comparison can be re-run, not as options.
- **A per-week ceiling that differs between weeks.** The budget binds in every week of
  the horizon, and expressing a different one is a payload change.

## Decisions

Reconstructed. Each was decided while the component was built, and the record is the
citation.

1. **CP-SAT or MILP?** CP-SAT, and the honest form of the record is *chosen for the
   assumption literals at a measured cost*, not *chosen because it is better at
   scheduling* ([`D-001`](../decisions.md#d-001)). This was the last record in the project
   still owed a rationale, and it was written only once the comparison existed.

2. **Assignment booleans or patterns?** Booleans, with the pattern formulation built in
   full so the comparison is against a real second model
   ([`D-009`](../decisions.md#d-009)). Thousands of near-identical columns create exactly
   the symmetry this model turns out not to have.

3. **Are hard constraints penalised or structural?** Structural
   ([`D-002`](../decisions.md#d-002)), with gates so they can be reported and relaxed.

4. **Weighted sum or lexicographic ordering?** Weighted sum
   ([`D-049`](../decisions.md#d-049)), with the shortfall weight derived rather than
   tuned.

5. **Are pins constant substitution?** No, gated equalities
   ([`D-021`](../decisions.md#d-021)), so a roster that changes the past is reported
   rather than being unrepresentable.

6. **Does a variable exist for an ineligible pair the incumbent assigned?** Yes
   ([`D-058`](../decisions.md#d-058)). Without it an already-illegal past cannot be
   represented and the objective silently understates the change the replan exists to
   make. This was a real defect that a ground-truth layer passed over, because every
   micro-instance happened to have a clean incumbent.

7. **How are violations enumerated?** By maximising true gates in one solve, not by
   iterating cores ([`D-044`](../decisions.md#d-044)): a core explains one conflict and
   hides the rest.

---

*The ledger: [`README.md`](README.md). The formulation:
[`internals/model.md`](../internals/model.md). Every measurement:
[`studies/`](../studies/README.md).*
