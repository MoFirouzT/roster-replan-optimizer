# Documentation

**Minimum-disruption shift-roster replanning under labour constraints.** Someone calls in
sick and the week is already published. This service reproduces that roster with the least
deviation from what people were told, rather than re-solving the week for the cheapest legal
answer. The case for that, with the picture and the measured results, is on the
[repository front page](https://github.com/MoFirouzT/roster-replan-optimizer).

What follows is the written record: what the service does, how it is built, what it was
measured at, and why each choice went the way it did.

**Using the service**: [`guide/`](guide)

| | |
| --- | --- |
| [`quickstart.md`](guide/quickstart.md) | one scenario end to end, and what it prints |
| [`configuring.md`](guide/configuring.md) | the tenant profile, and describing one in English |
| [`api.md`](guide/api.md) | jobs, statuses, the payload, the fallback ladder, the tools |
| [`rules.md`](guide/rules.md) | every rule a roster is checked against |
| [`limits.md`](guide/limits.md) | what it guarantees, what it was measured at, what it does not do |

Reaching further: the objective these pages configure is stated in full in [`internals/model.md`](internals/model.md). It is the other door (how the service works now, not what it promises) and worth the click if you want to see what *minimum disruption* means as a formulation.

**Working on it**: [`internals/`](internals)

| | |
| --- | --- |
| [`design.md`](internals/design.md) | why the system is shaped this way: **start here** |
| [`model.md`](internals/model.md) | sets, variables, objective, constraints, presolve |
| [`testing.md`](internals/testing.md) | the two readings, the seven layers, the mutation harness |
| [`development.md`](internals/development.md) | running the suite, the import contracts, the repository map |

**Why it is the way it is**

| | |
| --- | --- |
| [`STATE.md`](STATE.md) | where the project stands, what is closed, and what is still not done |
| [`specs/`](specs/README.md) | one work order per component (scope, the test contract, the gate it passed, the decision trail) and the [ledger](specs/README.md) indexing them: one row per component, where it lives, and what it found |
| [`decisions.md`](decisions.md) | 144 curated records: what was chosen, what was rejected, why. Enter by [ID](decisions.md#lookup), or [by theme](decisions.md#by-theme) for the records that make one argument together. An ID that is no longer a record is in [Merged and retired](decisions.md#merged-and-retired), which says where it went |
| [`studies/`](studies/README.md) | sixteen analyses, **including the nulls and the rejected alternatives**. A measured null is a stronger signal than an unmeasured win |
| [`benchmarks.md`](benchmarks.md) | the committed instance set, the four methods compared, the results and their caveats |

Three worth the detour:

- [`studies/horizon.md`](studies/horizon.md): a rejection upheld on evidence that contradicted both reasons the spec gave for it.
- [`studies/penalty-search.md`](studies/penalty-search.md): where the easy instance distribution would have produced the wrong answer.
- [`studies/mutation-harness.md`](studies/mutation-harness.md): four blind spots found behind fully green suites, and five times the harness was confidently wrong about itself.

## About this site

These are the same Markdown files the repository serves on GitHub, which is the primary
rendering. They are written for its heading anchors and for its relative links into
`roster_replan/` and `scripts/`, and [`lint_docs.py`](../scripts/lint_docs.py) checks them
there. The site adds an ordered nav and a search box over them, and a citation of a source
file opens that file in the repository.

Nothing here is generated from source, and there is no API reference built from docstrings:
the documentation is the argument, and a listing of every module would bury it.
