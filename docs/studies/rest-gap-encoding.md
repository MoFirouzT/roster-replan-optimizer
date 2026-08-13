# `R-REST-GAP`: pairwise inequalities against `no_overlap`

**Question.** [`rules.md`](../specs/rules.md#r-rest-gap--minimum-rest-between-shifts) encodes the rest
gap as one inequality per conflicting pair, and defers the alternative — one optional interval per
(employee, shift instance) inflated by `min_rest_hours`, under a single `add_no_overlap` per employee
— to a T2 study, with the words *"measured there, not assumed here"*.

This study exists because that promise was outstanding. It is not one of the four level-1 studies
`PLAN.md` names; it surfaced during the T2 close-out reconcile, which is what that beat is for.

**Answer.** A wash at this horizon, and rejected. The interval form is smaller and builds faster, and
searches slower by more than it saves — a 2% total win on the committed set, which is exactly the
threshold `lab.py` calls "not worth the complexity", and it reverses to an **11% total loss** on the
larger cold instances. It also costs the same reporting coordinate the `regular`
automaton costs. And the claim it was set up to test cannot be tested here at all.

    uv run python -m benchmarks.studies --only rest-gap

## The measurement

**On the committed set** (24 cases):

| quantity | ratio, intervals against pairwise | helped | hurt |
| --- | --- | --- | --- |
| variables | 0.766 | 24 | 0 |
| constraints | 0.958 | 24 | 0 |
| build time | 0.878 | 24 | 0 |
| search time | **1.156** | 0 | **24** |
| total time | 0.975 | 20 | 4 |

**On the larger cold instances** (8–16 employees, whole horizon open):

| quantity | ratio | helped | hurt |
| --- | --- | --- | --- |
| variables | 0.795 | 5 | 0 |
| build time | 0.911 | 5 | 0 |
| search time | 1.167 | 1 | 4 |
| **total time** | **1.115** | 1 | 4 |

The pattern is consistent and the sign flips on the total: **the interval form trades search time for
build time.** It is 23% smaller because one `no_overlap` replaces many pairwise rows, so there is less
model to construct — but a global propagator over intervals costs more to run than the inequalities it
replaced, on 24 of 24 cases.

**The two percentages are on different bases, and that is what decides the total.** 12% of a ~5.2 ms
build is about 0.6 ms saved; 16% of a ~3.3 ms search is about 0.5 ms lost. The saving is the larger
number on the committed set, which is why the total comes out marginally ahead — and on the cold
family, where search is a larger share of the work, the same two percentages land the other way and
the total flips. Which side wins is therefore a property of the instance rather than of the encoding,
which is the strongest reason not to adopt it: a lever that helps or hurts depending on the workload
cannot be reasoned about at the call site.

**That margin narrowed after this study was run.** Memoising `Instance.window` (`D-092`) took about
20% off build time, so the build-side saving this encoding trades for shrank from ~0.8 ms to ~0.6 ms
against an unchanged ~0.5 ms of search lost. The conclusion is unchanged and the reason for it is
stronger: the two sides are now closer still, so which one wins depends even more on the workload.

## The study cannot test the claim it was set up to test

`rules.md` justifies the alternative by **scaling**: "it scales as the horizon grows where the
pairwise set grows quadratically". That is a claim about the horizon, and this project's horizon is
fixed at one week.

The "larger" family above varies **employees**, not days — and employees are the wrong axis for this
hypothesis. The conflicting-pair set is computed over *slots*, not people, so adding employees
multiplies both encodings equally and tests nothing about the quadratic growth. There are 21 slots at
a one-week horizon, so the pair set is small, and there is no instance in this repo where it is not.

The honest position: **the hypothesis is untested and remains plausible.** What is tested is that at a
one-week horizon the alternative is not worth taking, which is the decision this project actually
needs.

## The reporting cost, which decides it

Identical to the automaton's (`D-088`). A `no_overlap` covers an employee's whole week, so its
assumption literal can say only *this employee's week has a rest violation somewhere*. The pairwise
encoding names the **second slot of the offending pair** — the coordinate `checker.py` reports and
`violations()` matches on.

Two of the four level-1 alternatives and this one all failed for the same structural reason, which is
worth stating once: **global constraints aggregate, and this model's gates are per rule instance.** An
encoding that replaces many local constraints with one global one necessarily coarsens what a failure
can be attributed to. That is a real cost in a project whose T4 deliverable is an explainer.

**Rejected at a one-week horizon** (`D-089`). Revisit with the horizon, not with tenant size.
