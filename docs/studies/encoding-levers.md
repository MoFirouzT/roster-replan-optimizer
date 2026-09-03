# Five encodings measured against the shipped model

**Question.** The model states each rule one way and there is a textbook alternative for most of
them. [`model.md`](../internals/model.md) named four of these as studies rather than assumptions,
and [`rules-statutory.md`](../guide/rules-statutory.md#rule-r-rest-gap) deferred the fifth with the
words *"measured there, not assumed here"*. Does any alternative beat what ships?

**Answer. One ships, four are rejected, and three of the four fail for the same reason.** Presolve
is a consistent win. Symmetry breaking has nothing to break. The `regular` automaton, the interval
rest gap and pattern variables all lose, and the automaton, the intervals and the patterns lose
partly because **a global constraint aggregates, and this model's gates are per rule instance**: an
encoding that replaces many local constraints with one global one coarsens what a failure can be
blamed on, in a project whose headline deliverable is an explainer.

    uv run python -m benchmarks.studies --only presolve symmetry automaton rest-gap patterns

*Assumes: the formulation in [`model.md`](../internals/model.md); the committed distribution in
[`benchmarks.md`](../benchmarks.md).*

## Method

All five run through [`lab.py`](../../benchmarks/lab.py) and share its discipline: **paired on the
instance**, so what is reported is the distribution of per-case ratios; **best of five repeats**,
because wall-clock noise is one-sided; and **the sign test reported beside the ratio**, because at
3 ms a mean is a statement about the machine. Every variant is checked to reach the **same optimum**
before any timing is read, since a broken encoding is usually the fast one.

Ratios below are *variant against shipped*, so under 1.0 favours the variant.

| lever | build | search | total | verdict |
| --- | --- | --- | --- | --- |
| Presolve, on against off | 0.724 | 0.863 | ships | **shipped** |
| Symmetry breaking | 1.020 | 1.010 | 1.015 | rejected: nothing to break |
| `regular` automaton | 0.997 | **1.196** | 1.065 | rejected |
| Rest gap as intervals | 0.859 | **1.149** | 0.961 | rejected: sign flips by instance |
| Pattern variables | n/a | no proof in 30 s | n/a | rejected |

## Presolve

**A win, consistently, and not the largest one.** `model.md` called it *"often the largest single
win, and free"*. Free is right, since the exclusion table is computed either way to retain the
reasons for reporting ([`D-045`](../decisions.md#d-045)). Largest is not.

| quantity | ratio, on against off | helped | hurt |
| --- | --- | --- | --- |
| variables | 0.716 | 28/28 | 0 |
| constraints | 0.692 | 28/28 | 0 |
| build time | 0.724 | 28/28 | 0 |
| search time | 0.863 | 28/28 | 0 |

It removes about a quarter of the model, keeping 57% to 76% of the unpresolved variables across the
28 cases. **The 28 of 28 is what makes it a result at these sizes**: a 27% median on a 5.2 ms build
would not survive scrutiny alone; the same direction on every paired case does. The search figure is
the weakest of the four, since 14% of 3 ms is near the resolution of the clock, and the sign test is
what carries it.

**The largest single win was somewhere else entirely.** An earlier version of this named the
compiled-model cache; measured, that hits 0 of 144 replan solves. What actually paid was memoising
`Instance.window`, worth about 20% of build, found by profiling rather than by reasoning about
encodings ([`model-cache.md`](model-cache.md), [`D-092`](../decisions.md#d-092)).

**The measured 28% is the smaller half of the argument.** `R-AVAIL`, `R-SKILL`, `R-FLEXI-ELIG` and
`R-DIMONA-FLX` are enforced *entirely* by removing variables, so turning presolve off does not
merely slow the model down: it changes which mechanism enforces four rules.

## Symmetry breaking

**There is essentially no symmetry left to break**, and the reason is not the one the spec gave.

Interchangeable means swapping two employees maps every legal roster to a legal roster *and leaves
the objective unchanged*. The second half is what the incumbent destroys, since disruption is
measured against each person's own published row. `model._orbits` therefore groups employees only
when every attribute the model reads matches **and** their incumbent rows match.

| | interchangeable employees |
| --- | --- |
| committed replan cases (28) | **3**, in 1 case |
| the same weeks solved cold (6) | **7** |

Two things suppress symmetry and only one was predicted. The **incumbent** roughly halves what
remains, which is what `model.md` expected. The **generator** is the larger effect and was not:
every employee draws an independent weekly budget and independent unavailability, so two are rarely
identical before any incumbent exists.

On the committed set the lever is a null and slightly negative, every quantity worse by under 2%,
which is what "no symmetry to exploit" looks like. On `identical_workforce`, built to contain the
structure, it is worth **20% of total time**: 27% off search, paid for with a 79% larger model and a
38% slower build.

So the null is about the distribution rather than about the lever, and it does not travel: a real
tenant with eight part-timers on identical contracts would have genuine orbits.
[`D-087`](../decisions.md#d-087) records the condition for revisiting.

## The regular automaton

**It loses, and the reason is that there is only one window.** `max_consecutive_days` is 6 over a
7-day horizon, so the sliding-window encoding builds a single window per employee. The naive
encoding the automaton was going to replace is *one linear inequality over seven booleans*.

| quantity | ratio, automaton against windows | helped | hurt |
| --- | --- | --- | --- |
| variables, constraints | 1.000 | 0 | 0 |
| build time | 0.997 | 16 | 8 |
| search time | **1.196** | 0 | **24** |

**The counts being identical is the tell.** Both need the same seven `worked` indicators and then
one constraint each. At this size, summing seven booleans is simply cheaper than propagating a state
machine, and there is no structure for the automaton to exploit. The same holds on the larger cold
instances: 19% slower to search.

The reporting cost is the more durable objection. An automaton **can** be gated, verified in
`tests/test_studies.py` rather than assumed, but one automaton covers a whole week, so its literal
can say only *this employee's week is wrong somewhere*. The window encoding names the **day**, which
is the coordinate `checker.py` reports and `violations()` matches on.

**Where it would flip** is a longer horizon, where the window count grows and the automaton stays
one constraint. That is not hypothetical for this domain ([`D-014`](../decisions.md#d-014)), but it
is not the model this project ships. Rejected at this horizon, revisit past about two weeks
([`D-088`](../decisions.md#d-088)).

## Rest gaps as intervals

**A wash at this horizon, and rejected because which side wins depends on the workload.**

| quantity | committed set (28) | larger cold instances |
| --- | --- | --- |
| variables | 0.766 | 0.795 |
| build time | 0.859 | 0.911 |
| search time | **1.149** | 1.167 |
| **total time** | 0.961 | **1.115** |

**The interval form trades search time for build time.** One `no_overlap` replaces many pairwise
rows, so there is less model to construct, but a global propagator costs more to run than the
inequalities it replaced, on 28 of 28 cases. The two percentages sit on different bases: 14% of a
5.2 ms build is about 0.7 ms saved, 15% of a 3.3 ms search is about 0.5 ms lost. On the cold family,
where search is a larger share, the same two percentages land the other way and the total flips.

A lever that helps or hurts depending on the workload cannot be reasoned about at the call site,
which is the strongest reason not to adopt it. The margin narrowed further when
[`D-092`](../decisions.md#d-092) took 20% off build, shrinking the side this encoding trades for.

**The scaling claim behind it is now tested, and the verdict holds.** `rules.md` justified the
alternative by the pairwise set growing quadratically in slots, which a one-week horizon cannot
test. Measured out to eight weeks and on the foreign instances, the size win is real and large,
7.1× fewer variables on one import, and **search is still slower at every point**
([`scaling-levers.md`](scaling-levers.md)).

Rejected ([`D-089`](../decisions.md#d-089)), and the reporting cost is the automaton's, identically.

## Pattern variables

**Competitive on a replan, catastrophic on a cold week.** One boolean per (employee, legal weekly
pattern), exactly one true per employee. Every per-employee rule disappears from the model, because
a pattern breaking one is never enumerated; what is left is coverage, skill mix and the objective.
The objective survives intact, which is the formulation's most attractive property: a pattern's
disruption is a constant computed at enumeration time.

On a replan it ties, and for a reason that is not about the formulation. `now` sits at day 5, so
five of seven days are pinned and the enumeration ranges over two days: **36 to 122 patterns for a
whole tenant**. The pattern space of a replan is small because a replan is mostly not a choice. It
already loses at 25 employees, where enumeration alone costs more than the entire assignment solve.

Cold, with the whole horizon open, it does not finish:

| case | patterns | enumerate | search | assignment | outcome |
| --- | --- | --- | --- | --- | --- |
| `headline/0` | 9,740 | 1,200 ms | 30,001 ms | 29 ms | no proof |
| `loose/0` | 4,694 | 445 | 30,001 | 24 | no proof |
| `tight/0` | 9,740 | 1,233 | 30,001 | 19 | no proof |
| `large/0` | 19,495 | 6,674 | 7,905 | 87 | same optimum |

Enumeration alone is 20 to 60 times the assignment model's entire solve, and that part could be
cached. **The pattern model cannot prove optimality**, and caching does not remove that. With no
incumbent the objective is close to indifferent, and thousands of near-identical columns give CP-SAT
an enormous symmetric search space with nothing to guide it: the pattern encoding **creates** the
symmetry the section above found the assignment model does not have.

**What this does not say.** It does not say column-based formulations are wrong for rostering. It
says **explicit enumeration** is wrong at this horizon and these sizes. The standard technique is
column generation, generating columns from dual prices, which is a different project, needs an LP
relaxation CP-SAT does not expose, and would be measured against an assignment model that already
answers in 20 ms. Nor does it travel to longer horizons in the direction people expect: at a
four-week period the enumeration is `4^28` rather than `4^7`.

[`D-009`](../decisions.md#d-009) closes in favour of assignment booleans, and not narrowly.

## What the four rejections have in common

Three of them, the automaton, the intervals and the patterns, replace many local constraints with
one global one. That is the textbook move and it costs the same thing every time: **an aggregated
constraint carries one assumption literal, so a failure can no longer be attributed to a rule
instance.** This model's explainer, its differential harness and `violations()` all key on
`(rule, employee, day, shift)`, so coarsening the gate is not a presentational loss but a structural
one.

The fourth, symmetry breaking, fails differently and more cheaply: the structure it exploits is
absent from this distribution, and the study says so rather than claiming the lever is bad.

**None of the four was rejected on a small margin of speed.** That is worth stating, because a
20% timing difference at 3 ms would not have been worth acting on either way.

---

*Behind these: [`D-009`](../decisions.md#d-009), [`D-087`](../decisions.md#d-087),
[`D-088`](../decisions.md#d-088), [`D-089`](../decisions.md#d-089). Merged from five separate
studies on 2026-09-03; see [`README.md`](README.md). The scale re-measurement:
[`scaling-levers.md`](scaling-levers.md).*
