# STATE: where the project stands

Read this after [`CLAUDE.md`](../CLAUDE.md); update it at the end of every working session.
It holds the current state and nothing else.

**History is not here.** What each component found is one row per component in the
[ledger](specs/README.md); the reasoning behind each is in [`decisions.md`](decisions.md), and the
measurements are in [`studies/`](studies/README.md).

---

## Status: closed

The project is finished and is not under active development. T0 through T5 shipped, each tier
gate passed on evidence rather than on prose, and two of T5's four items were retired on
measurement rather than built. The declaration that closed it was written on 2026-08-13, when
T3 was the finish; T4 and T5 both closed afterwards, so that document is a dated record and is
no longer in the repository.

Work since then has been documentation and correction, not capability.

## The repo today

| | At the declaration, 2026-08-13 | Now |
| --- | --- | --- |
| Tests | 567 | 933, of which 47 skip without fetched benchmark data |
| Mutants, each naming the layer that must catch it | 59 | 136 |
| Import-linter contracts | 8 | 11 |
| Decision records | 94, 2 open | 137, none open, 14 merged or retired |
| Studies, including nulls | 8 | 18 |
| Python | ~12,000 lines | ~24,600 lines |

**The last full mutation run does not vouch for the tree it ran in.** 2026-08-21, 852 s:
136 of 136 caught, and the verdict is `unverifiable` rather than `clean`, because three files
it mutated were already modified or were written back after the restore:
`benchmarks/weights.py`, `roster_replan/disruption.py`, `roster_replan/model.py`
([`D-112`](decisions.md#d-112)). The catches are probably real and are not vouched for. Re-run
those layers before trusting them, per [`CLAUDE.md`](../CLAUDE.md).

## What is still not done

Three of these are blocked on something outside this repository, which is the honest reason
they are not done. The rest are not blocked at all: they are deployment work with no findings
in them.

| Gap | Blocked on |
| --- | --- |
| **Capture and replay**: was the largest gap, now half of one ([`D-125`](decisions.md#d-125)) | External authorization and real vendor payloads. A Belgian horeca corpus is still what this owns |
| The cost axis (`cost_weight` ships at 0, [`D-050`](decisions.md#d-050)) | Wage data |
| `R-STUDENT-QUOTA`, `R-SUNDAY`, `R-BREAK`, `R-PT-MIN`, `R-PUB-NOTICE` | A named legal source each: [`rules.md`](guide/rules.md) refuses a legality claim without provenance |
| Service `[TODO]`s: external queue store, metrics backend, interrupting a running solve | Nothing: these are deployment choices |
| No committed benchmark case runs at **more than one week**, though the service now answers them ([`D-113`](decisions.md#d-113)) and the generator takes a horizon ([`D-115`](decisions.md#d-115)) | Nothing. No committed case asks for one |
| The last mutation verdict is `unverifiable` | Nothing: re-run the three named layers on a clean tree |

The capture gap outranks the rest and the reason is unchanged: **the incumbent is solved by the
system under test.** Every benchmark number in this repository shows a replan beats a re-solve
*given a roster this model would produce*. [`foreign-incumbent.md`](studies/foreign-incumbent.md)
closed the half of that which was not blocked.

## The documentation

Three rearrangements, and they are done.

**2026-08-20**: the specs were rewritten as two doors ([`D-151`](decisions.md#d-151)): a
[guide](guide) for people using the service and [internals](internals) for people changing it.
A spec that has been reconciled with its code describes the system, so it belongs where people
read about the system. The [ledger](specs/README.md) records where each original spec went.

**2026-09-02** : the documentation moved onto the shared discipline contract: no archive tier,
this file, the [ledger](specs/README.md), curated records, durable measurements, and
[`scripts/lint_docs.py`](../scripts/lint_docs.py) as a CI job. The spec, with every box recorded
against its evidence, is
[`documentation-restructure.md`](specs/documentation-restructure.md). No claim, number or rule ID
moved with the restructure itself; the stale figures it found were corrected, and they are the
numbers in the table above.

**2026-09-02**: the 150 decision records were curated to **137**, five retired and nine merged
into the records that carry their argument, with one written for a decision that never got one.
Every removed ID keeps its anchor in [Merged and retired](decisions.md#merged-and-retired), so no
link or docstring citing one had to move. The spec is
[`decision-curation.md`](specs/decision-curation.md) and what it found is its
[ledger row](specs/README.md).

## Known blockers

None that stop work. The three gaps above marked *blocked* need something this project cannot
obtain for itself.

---

*What each component found: [`specs/README.md`](specs/README.md). Every record: [`decisions.md`](decisions.md), by [ID](decisions.md#lookup) or [by theme](decisions.md#by-theme). Every measurement, including the nulls: [`studies/`](studies/README.md).*
