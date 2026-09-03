# The rule registry

**Status:** Implemented 2026-08-20
**Reconstructed 2026-09-02** from [`guide/rules.md`](../guide/rules.md) and its three
companion files, [`checker.py`](../../roster_replan/checker.py), the mutant catalogue, the
records cited below, and the commits of 2026-08-12 to 2026-08-20, and **it is not the work
order this component was built from**: this project had none
([`documentation.md`](documentation.md#specs-for-the-built-components)).
**Depends on:** nothing. Everything else in this project reads this.

## Objective

One registry of every rule a roster is checked against, where each rule has a stable ID
used unchanged in the model, the checker, the `Violation` objects and the explainer's
prose, and where every rule that claims legal authority names the instrument it comes
from.

## Motivation

A rostering tool that says a roster is illegal is making a claim about the law, and the
value of that claim is exactly the quality of its source. Most tools in this space encode
thresholds that somebody remembered. This component exists so that every threshold can be
traced to a statute, a CBA article, or an explicit statement that there is no legal basis
and the rule is operational.

The second half is the vocabulary. A rule whose ID differs between the model, the checker
and the error message is three rules, and nobody can tell whether they agree.

## Canonical reference

[`guide/rules.md`](../guide/rules.md) owns the registry, the legal sources, and the
reference-period argument. The predicates live in the three files it points to:

- [`rules-operational.md`](../guide/rules-operational.md), the five imposed because a
  roster has to work
- [`rules-statutory.md`](../guide/rules-statutory.md), the fourteen carrying a named
  instrument
- [`rules-eligibility.md`](../guide/rules-eligibility.md), the two resolved upstream

Each rule is specified in eight bullets, of which **Predicate**, **Model encoding** and
**Checker encoding** are what make the two readings checkable against each other.
Nothing in this file restates a predicate.

## Governing reference

The instruments are tabled in [`guide/rules.md`](../guide/rules.md) under *Legal
sources*: Arbeidswet, WTD, Feestdagenwet, Arbeidsreglementenwet,
Arbeidsovereenkomstenwet, the RSZ implementing decree, and PC 302 CAO nr. 7.

Article numbers were read against the consolidated statute and not against summaries,
which is not pedantry: the FPS Employment summary attributes the three-hour minimum work
period to art. 19 and the statute puts it in art. 21.

## Parameters and configuration

Every threshold sits on `RuleParams` in [`domain.py`](../../roster_replan/domain.py),
**explicit and undefaulted**, plus `derogation_basis`. A default in shared code is a
threshold that two readings would inherit from one place, which is the one thing the
independence rule forbids ([`D-039`](../decisions.md#d-039)).

Every rule marked *optional* is profile-gated, so a tenant that does not enable it never
pays for it.

## Interfaces

A rule ID is the same string in five places: this registry, the model, the checker, the
`Violation` returned to a caller, and the explainer's prose. `Violation` carries the rule
ID, employee, day, shift, and the observed value against the required one.

## Layering

The registry itself imports nothing. What enforces its independence claim is the pair of
contracts on its two readings, which are specified in
[`validation.md`](validation.md).

## Build tasks

- [x] Give every rule a stable ID, a statement, a class, its parameters, an explainer
      string, and a provenance.
- [x] Write the predicate, the model encoding and the checker encoding side by side for
      every specified rule.
- [x] Search for a named instrument behind every rule claiming statutory authority
      ([`D-145`](../decisions.md#d-145)).
- [x] Reclassify the rules whose search came back without one.
- [x] Hold the unspecified rules to *optional* under test, so a citation cannot be
      mistaken for an encoded rule.

## Test contract

| Claim | Layer |
| --- | --- |
| Every encoded rule appears in both readings, and neither invents one | `test_specs.py`, three tests over the registry |
| An unencoded rule is still declared optional | `test_specs.py::test_unencoded_rules_are_still_declared_optional` |
| Each rule binds at the right number | brute force, on threshold-bracketing instances |
| The two readings agree rule by rule | the differential harness |

Eighteen mutants name a rule layer: ten `spanrules`
(`R-MIN-BLOCK`, `R-MAX-SHIFT-TYPE`, `R-MIN-HOURS`, `R-SUCCESSION`, and the personal
consecutive limit, each mutated in *both* readings), five `weekends`
(`R-MAX-WEEKENDS`, `R-MIN-DAYS-OFF`) and three `dayoff` (`R-DAY-OFF`). Each pair exists
because a defect written into one reading only would be caught by the differential
harness, and a defect written into both would not.

## Acceptance gate

*Blocks:* the model and the checker, which are two readings of this.

- [x] 26 rules, each with a stable ID and a provenance.
- [x] Every rule claiming statutory authority names an instrument and an article.
      [`D-145`](../decisions.md#d-145).
- [x] Twenty-one rules carry a written predicate. The other five are declared and
      sourced, and `test_specs.py` holds them to *optional*.
- [!] **Two searches found no rule at all.** There is no 24-hour Dimona deadline and no
      horeca 3h48 minimum. Both entries lost their legality claim rather than keeping an
      unsourced one, which is the gate returning a negative result rather than failing.
- [!] **Three rules were reclassified out of *statutory* on the same evidence.**
      `R-CONSEC-DAYS` has no statutory basis for adult workers
      ([`D-023`](../decisions.md#d-023)), and `R-MIN-SHIFT` is not roster-violable at all
      under fixed shift instances, so it became input validation
      ([`D-031`](../decisions.md#d-031)).
- [!] **Two provenance lines are weaker than the rest and say so.** `R-SUNDAY`'s art. 66
      could not be read off the consolidated statute, because every ejustice endpoint
      truncates before Chapter VI, so its sector list rests on agreeing secondary
      renderings. The flexi income ceiling is carried by three different figures in
      circulation, and is documentation rather than a model input.

## Measured results

**The registry grew by seven rules on foreign evidence, after this component was
declared finished.** Reading thirteen published rosters this project did not produce
found four items catalogued here as preferences that are hard constraints where those
rosters come from, and every one of the seven bound hard when measured
([`D-134`](../decisions.md#d-134), [`D-135`](../decisions.md#d-135),
[`D-136`](../decisions.md#d-136)). That work is specified in
[`cross-week-rules.md`](cross-week-rules.md).

**Two week rules were named for a week and measured over a horizon**, and the
differential harness could not have caught it, because both readings were wrong in the
same direction ([`D-111`](../decisions.md#d-111)).

## Out of scope

- **Encoding the five sourced-but-unspecified rules.** `R-STUDENT-QUOTA`, `R-SUNDAY`,
  `R-BREAK`, `R-PT-MIN` and `R-PUB-NOTICE` each need a predicate, parameters, a hard or
  soft classification and a failure message before anything may enforce them. What the
  instruments say is recorded so the search is not repeated.
- **A per-entry instrument for `R-SKILL-MIX`.** Its provenance is declared by the tenant
  per entry, so there is no one source to name and the `[CITE]` marker stays
  ([`D-025`](../decisions.md#d-025)).
- **A profile field for whether a tenant has a CAO.** `R-BREAK`'s second limb is
  conditional on it and the registry has nowhere to put it.
- **Computing the reference period.** It is resolved upstream and arrives as a single
  `max_hours_this_week` budget. Correctness depends on a computation this service does
  not perform, and that cost is stated rather than hidden.
- **Student contracts in the generator**, until `R-STUDENT-QUOTA` is encoded
  ([`D-072`](../decisions.md#d-072)).

## Decisions

Reconstructed. Each was decided while the component was built, and the record is the
citation.

1. **Where Belgian law and the WTD differ, which is implemented?** The Belgian rule,
   wherever it is stricter ([`D-024`](../decisions.md#d-024)). It binds for the target
   tenants, and the stricter of the two cannot produce a WTD violation.

2. **Is the weekly ceiling a per-week number?** No, a supplied budget
   ([`D-123`](../decisions.md#d-123)). Average weekly hours are measured over a rolling
   reference period, and a per-week ceiling is wrong in both directions: it forbids a
   legal heavy week and permits thirteen at the ceiling. Extending the horizon instead
   was built and measured and buys nothing ([`D-116`](../decisions.md#d-116),
   [`horizon.md`](../studies/horizon.md)).

3. **Is a granted day off an availability interval?** No, a rule
   ([`D-142`](../decisions.md#d-142)). Expressing it as an interval was the workaround,
   and it loses the reason the day is off.

4. **Are `span` and `work_hours` one symbol?** No
   ([`D-037`](../decisions.md#d-037)). The rules disagree about which they mean:
   `R-MIN-SHIFT` reads gross, the hour ceilings read net. Collapsing them would make one
   rule silently wrong by about a break per shift.

5. **Are flexi eligibility and Dimona state one rule?** No, two IDs
   ([`D-034`](../decisions.md#d-034)), because they call for different operator actions.
   Both are resolved upstream and indexed per employee per day
   ([`D-032`](../decisions.md#d-032)), and the same-day reading is deliberately
   conservative: only a filed `OK` counts ([`D-035`](../decisions.md#d-035)).

6. **Are absences and declared unavailability the same rule?** One rule, two
   provenances ([`D-020`](../decisions.md#d-020)): an absence is not relaxable and a
   declared preference is.

---

*The ledger: [`README.md`](README.md). The predicates:
[`guide/rules.md`](../guide/rules.md). The reasoning:
[`decisions.md`](../decisions.md).*
