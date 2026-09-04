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
| Tests | 567 | 958, of which 47 skip without fetched benchmark data |
| Mutants, each naming the layer that must catch it | 59 | 140 | <!-- fig:mutant-count -->
| Import-linter contracts | 8 | 11 |
| Decision records | 94, 2 open | 144, one open ([`D-154`](decisions.md#d-154)), 14 merged or retired |
| Studies, including nulls | 8 | 16 |
| Python | ~12,000 lines | ~24,600 lines |

**The last full mutation run vouches for the tree it ran in.** 2026-09-04, 863 s:
140 of 140 caught, verdict `clean`, `unvouched_for` empty. It supersedes the `unverifiable`
run of 2026-08-21 ([`D-112`](decisions.md#d-112)), whose 136 catches were probably real and
were never vouched for.

It is also the first full run to cover the four mutants added on 2026-09-02 and 2026-09-03:
`citation-rule-accepts-anything`, `model-ungated-still-gates`,
`figure-check-accepts-a-copy-that-disagrees-with-its-owner` and
`figure-check-never-recounts-a-derived-figure`. Each had only been proved against its named
catcher in a targeted run, and every one of those runs returned `unverifiable` rather than
`clean`, because each proved a layer mid-change, which [`CLAUDE.md`](../CLAUDE.md) allows and
prices. Nothing is owed here now.

## What is still not done

Three of these are blocked on something outside this repository, which is the honest reason
they are not done. The rest are not blocked at all: they are deployment work with no findings
in them.

| Gap | Blocked on |
| --- | --- |
| **Capture and replay**: was the largest gap, now half of one ([`D-125`](decisions.md#d-125)) | External authorization and real vendor payloads. A Belgian horeca corpus is still what this owns |
| The cost axis (`cost_weight` ships at 0, [`D-050`](decisions.md#d-050)) | The same corpus as the row above, for a different reason. What is missing is not wage rates, which are published per sector, but **the exchange rate between disruption and cost**, which [`D-050`](decisions.md#d-050) calls a tenant's business judgement rather than a fact about rostering. Real planners choosing between paying overtime and moving someone reveal their own |
| `R-STUDENT-QUOTA`, `R-SUNDAY`, `R-BREAK`, `R-PT-MIN`, `R-PUB-NOTICE` | A named legal source each: [`rules.md`](guide/rules.md) refuses a legality claim without provenance |
| Service `[TODO]`s: external queue store, metrics backend, interrupting a running solve | Nothing: these are deployment choices |
| No committed benchmark case runs at **more than one week**, though the service now answers them ([`D-113`](decisions.md#d-113)) and the generator takes a horizon ([`D-115`](decisions.md#d-115)) | Nothing. No committed case asks for one |
| **The canonical optimum is not canonical** ([`D-154`](decisions.md#d-154)): sums of squared ordinals collide, so two rosters can tie and the search picks between them | Nothing, and it is a design question rather than a patch. Weights no two subsets can share overflow int64 long before 60,000 variables |
| **The foreign importer reads their coverage band as our ceiling** ([`D-155`](decisions.md#d-155)): their format prices over-coverage and this project prohibits it, so published rosters that overstaff legally import as illegal | Nothing. The fix is specified in [`scale-evidence.md`](specs/scale-evidence.md) and changes a shipped predicate, both readings of it, and [`D-057`](decisions.md#d-057)'s domination bound, for a benchmark's benefit |

The capture gap outranks the rest and the reason is unchanged: **the incumbent is solved by the
system under test.** Every benchmark number in this repository shows a replan beats a re-solve
*given a roster this model would produce*. [`foreign-incumbent.md`](studies/foreign-incumbent.md)
closed the half of that which was not blocked.

## Performance

**Closed on five nulls** ([`D-156`](decisions.md#d-156),
[`scaling-levers.md`](studies/scaling-levers.md)). A hand-written model builder is slower than
the wrapper, dropping the gate literals loses the proof of optimality, the interval rest-gap
encoding cuts variables by 7.1× and searches more slowly, parallel workers change a replan not
at all, and the generator cannot reach the sizes where any of it would matter. Nothing shipped
and nothing is scheduled: a committed case answers in about 3 ms, so there is no latency to
recover. Read that study before starting any performance work here.

## The documentation

Six rearrangements, and they are done. What came after is publication rather than movement.

**2026-08-20**: the specs were rewritten as two doors ([`D-151`](decisions.md#d-151)): a
[guide](guide) for people using the service and [internals](internals) for people changing it.
A spec that has been reconciled with its code describes the system, so it belongs where people
read about the system. The [ledger](specs/README.md) records where each original spec went.

**2026-09-02** : the documentation moved onto the shared discipline contract: no archive tier,
this file, the [ledger](specs/README.md), curated records, durable measurements, and
[`scripts/lint_docs.py`](../scripts/lint_docs.py) as a CI job. The spec, with every box recorded
against its evidence, is
[`documentation.md`](specs/documentation.md#the-restructure). No claim, number or rule ID
moved with the restructure itself; the stale figures it found were corrected, and they are the
numbers in the table above.

**2026-09-02**: the 150 decision records were curated to **137**, five retired and nine merged
into the records that carry their argument, with one written for a decision that never got one.
Every removed ID keeps its anchor in [Merged and retired](decisions.md#merged-and-retired), so no
link or docstring citing one had to move. The spec is
[`documentation.md`](specs/documentation.md#curating-the-decision-records) and what it found is its
[ledger row](specs/README.md).

**2026-09-02**: every built component now has a **work order** in [`specs/`](specs), holding what a
live document does not: the scope, the interfaces, the test contract, the gate it passed and the
decision trail ([`D-152`](decisions.md#d-152)). Twelve were written on that date and **they are
reconstructions**, from the code, the live documents, the records, the studies and the commits, and
each says so on its Status line. Nothing moved out of [guide](guide) or [internals](internals).

The sweep found **88 citations in `roster_replan/`, `tests/` and `benchmarks/` naming a spec file
deleted on 2026-08-20**. They sat behind a green suite and a green linter for two weeks, because
the anchor check reads only Markdown links inside the doc set.

**2026-09-02**: those citations are repointed, and the real count was **153**, because a bare
`rules.md` is not a path either and is ambiguous now that a spec has that name. <!-- lint-ok: it names the form that was repointed --> A citation now
resolves against the repository root and then `docs/`, and `scripts/lint_docs.py` checks it. The
spec is [`documentation.md`](specs/documentation.md#citations-in-source), and it found **four claims stale in content
rather than only in citation**, which is what its [ledger row](specs/README.md) records.

**2026-09-03**: the four documentation components above are held in one file,
[`documentation.md`](specs/documentation.md), one section each
([`D-157`](decisions.md#d-157)). The ledger keeps four rows, each pointing at its section, and
a [Merged](specs/README.md#merged) table maps the removed filenames. The read that merged them
found **seven stale figures**, each a number copied away from the document that owns it: the
illegal-past count in four places against the study's corrected 8 of 13, two study counts left
over from the encoding merge, and a record count four behind.

**2026-09-03**: those seven figures are now the linter's job rather than a reader's
([`D-158`](decisions.md#d-158)). [`scripts/figures.toml`](../scripts/figures.toml) names each
load-bearing number and the one document that owns it; `scripts/lint_docs.py` recounts the
`derived` ones from the repository and checks every statement of a `pinned` one against its
owner. Replayed against the commits that carried them, all three known incidents fire
([`figures_history.py`](../scripts/figures_history.py)), and **three live ones were found**:
this file's companion `CLAUDE.md` had its own link counts at 547/518/340 against 620/540/344,
[`documentation.md`](specs/documentation.md) claimed 16 of 16 ledger rows against 21, and the
study that owns the illegal-past figure still headed it *Ten of thirteen*. <!-- lint-ok: it names the figure it corrected -->

What no check that reads documents can catch is [`D-155`](decisions.md#d-155)'s scale table,
where every document agreed and the disagreement was with reality.

**2026-09-04**: the same files are published as a MkDocs site at
[mofirouzt.github.io/roster-replan-optimizer](https://mofirouzt.github.io/roster-replan-optimizer/),
built by [`docs.yml`](../.github/workflows/docs.yml) on every push to `main`. Nothing built is
committed, no document moved and no claim changed. GitHub stays the primary rendering, so a link
into `roster_replan/` or `scripts/` is still relative and
[`lint_docs.py`](../scripts/lint_docs.py) still checks it there;
[`mkdocs_hooks.py`](../scripts/mkdocs_hooks.py) turns the 85 that leave `docs/` into repository
URLs at build time. That is what lets the build run `--strict`, which buys a check this repository
did not have: **a document in neither `nav` nor `not_in_nav` fails the build** instead of going
live with no way to reach it.

Two corrections went with it. [`limits.md`](guide/limits.md) stated the scale envelope as a
headcount and stopped there, which reads as a low ceiling and an unfinished investigation; it now
says what binds (model construction, not search), what was tried against it (five levers, five
nulls, [`D-156`](decisions.md#d-156)) and what is still unknown (search above about a million
variables). The number itself is unchanged and still [`D-127`](decisions.md#d-127)'s. And the
transcript in [`quickstart.md`](guide/quickstart.md) is now asserted against what the demo prints,
every line but the wall-clock one: it had drifted once already, because a block of program output
sitting in a document is prose to every check here. Proved by hand, by editing the transcript and
watching `tests/test_demo.py` fail. It has no mutant, so it is not a layer this repository can yet
say it has broken on purpose.

## Known blockers

None that stop work. The three gaps above marked *blocked* need something this project cannot
obtain for itself.

---

*What each component found: [`specs/README.md`](specs/README.md). Every record: [`decisions.md`](decisions.md), by [ID](decisions.md#lookup) or [by theme](decisions.md#by-theme). Every measurement, including the nulls: [`studies/`](studies/README.md).*
