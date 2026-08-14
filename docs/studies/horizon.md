# The horizon: what a longer one costs, and what it buys

**Question.** [`rules.md`](../specs/rules.md#the-reference-period-and-why-r-max-weekly-is-a-budget)
rejects extending the solve horizon to the reference period in one sentence:

> The obvious fix is to extend the solve horizon to the reference period. That is rejected: it
> multiplies instance size by an order of magnitude and destroys the interactive latency the whole
> service is built around.

Nothing measured that. It was the last major rejection in this project standing on an assertion, and
it could not be measured until `D-111` scoped the week rules to the week and `D-113` let a longer
horizon through validation at all.

**Answer. The rejection holds, and both reasons given for it are wrong.** Instance size grows
**linearly**, not by an order of magnitude, and four weeks answers in about a tenth of a second.
What actually justifies the rejection is the half the sentence never mentions: a longer horizon
**buys nothing**. Four weeks solved at once and four weeks solved one at a time reach *identical
coverage* on every case tried, at both ends of the tightness axis. Nor does the pooled
reference-period budget the spec is really about, once it is expressible at all (`D-123`): the
freedom to spend a quarter unevenly is used by four to nine employees per case and converts into no
staffed shift anywhere.

    uv run python -m benchmarks.studies --only horizon

## The cost

Generated replan scenarios at `demand_ratio` 0.70, 12 employees, median of three seeds:

| days | slots | variables | constraints | build ms | search ms |
| --- | --- | --- | --- | --- | --- |
| 7 | 21 | 1,035 | 1,334 | 5.4 | 5.7 |
| 14 | 42 | 2,056 | 2,720 | 12.3 | 23.6 |
| 28 | 84 | 4,058 | 5,376 | 29.5 | 77.0 |

*(Re-measured after `D-119`. Search now includes the canonicalising second phase, which is
why one week reads 5.7 ms where this table first reported 3.5 — and why the crossover it
identifies has moved from between one week and two to **at** one week.)*

**Size is linear in the horizon.** Four times the days gives 3.9× the variables and 4.0× the
constraints. The rest-gap pairs stay local — a gap is eleven hours, so no shift conflicts with one a
week away — and nothing else aggregates across the horizon either. "An order of magnitude" describes
a growth this model does not have.

**Search is not linear.** It grows 13.5× over the same range against build's 5.5×, and grew 23× on
the pre-`D-119` measurement of the same table. That is the real cost of a longer horizon, and it is
in the term the rejection did not name.

**`D-081`'s premise is gone at every horizon here.** When this study first ran, build cost more than
search at seven days (5.4 against 3.5) and the two crossed over somewhere between one week and two.
Canonicalising the optimum (`D-119`) added a second search phase and moved the crossover to **one
week**: build 5.4 against search 5.7, and by four weeks search costs more than twice what build does.
That premise is why the two clocks are reported separately, why the compiled-model cache was worth
trying (`D-093`), and why memoising `Instance.window` was the largest single win (`D-092`). None of
those decisions reverses, and none of them can now be *argued* the way it originally was.

## What it buys

The comparison the rejection is really about: **one four-week solve, against four one-week solves
with the boundary state carried between them**, which is what the service does today. Cold
generation, three seeds, at both ends of the coverage axis. `short` is unstaffed positions across the
whole month.

| demand ratio | seed | one solve: short | search ms | four chained: short | search ms |
| --- | --- | --- | --- | --- | --- |
| 0.70 | 0 | 0 | 281.2 | 0 | 253.7 |
| 0.70 | 1 | 0 | 243.8 | 0 | 350.1 |
| 0.70 | 2 | 0 | 220.7 | 0 | 222.1 |
| 0.90 | 0 | **5** | 631.1 | **5** | 1563.2 |
| 0.90 | 1 | **5** | 593.1 | **5** | 1254.6 |
| 0.90 | 2 | **5** | 1603.6 | **5** | 168.9 |

**Coverage is identical on every case.** Not close — identical, including at 0.90 where five
positions go unstaffed either way. The four-week solve sees the whole month and finds nothing the
weekly sequence misses.

The reason is that **the weeks are barely coupled**. `R-MAX-WEEKLY` binds inside a week and
`R-WEEKLY-REST` is measured inside a week, so neither reaches across a boundary at all. What does
reach across is `R-REST-GAP` and `R-CONSEC-DAYS`, and both reach exactly as far as a caller can
already tell them to: `last_shift_end_before_horizon` and
`consecutive_days_worked_before_horizon` are the boundary, and they carry it faithfully. A model with
almost no coupling between its blocks does not need to see them together.

**The timing comparison did not survive canonicalisation, and the coverage one did.** Before
`D-119` the single solve was uniformly the slower arm under pressure — 239 to 555 ms against 94 to
166 ms. With a canonical second phase on every proved optimum the two arms swap places case by case
(1563 ms chained against 631 ms single on one seed, 169 ms against 1604 ms on another), because the
chained arm pays that phase four times and the single arm once. **No timing claim survives that**, and
the honest position is that this study no longer measures which arm is faster. What it still measures,
unchanged and on every case, is that neither finds coverage the other misses. The tight setting is
sampled for `D-105`'s reason: on a slack month both methods staff everything and the comparison
cannot say anything.

## Why the chained arm is a fair comparison, and how that is checked

A chained solve is easy to flatter by accident. If the boundary state is carried wrongly, each week
starts from a person with no history — free of the rest gap and the consecutive-day streak the
previous week imposed — and the chained arm returns a cheaper roster it was never entitled to.

So the study **stitches the four weekly rosters back into one month and hands it to the independent
checker**, and refuses to report a timing if it comes back with a hard violation. That is the same
discipline as `_guard` in the encoding studies: no number is printed until the two things being
compared are known to be answering the same question. `test_the_chained_solve_stitches_into_a_legal_month`
asserts it in the suite as well, and a mutant that drops the carried shift-end is caught by it.

## The pooled budget: the approximation `rules.md` actually makes

The two arms above hold the same weekly ceiling, so what they compare is horizon *length*. The
approximation the spec describes is a different thing, and it took a payload change to ask about it
(`D-123`): a caller resolves a rolling quarter into one weekly number, and what that destroys is the
freedom to spend it **unevenly** — 45 hours this week against 31 next, inside one quarterly total.

`R-MAX-PERIOD` makes the pool expressible alongside the rate. Both arms below are given the same
total hours over four weeks; they differ only in whether those hours may be distributed freely.
`uneven weeks` counts employees whose weekly hours are not all equal — the freedom being used.

| demand ratio | seed | pooled: short | uneven weeks | flat ceiling: short |
| --- | --- | --- | --- | --- |
| 0.70 | 0 | 0 | 9 | 0 |
| 0.70 | 1 | 0 | 9 | 0 |
| 0.70 | 2 | 0 | 9 | 0 |
| 0.90 | 0 | 5 | 6 | 5 |
| 0.90 | 1 | 5 | 4 | 5 |
| 0.90 | 2 | 5 | 5 | 5 |

**The freedom is real and it buys nothing.** Four to nine employees per case work unequal weeks when
allowed to — so the pooled budget is not inert, and the solver does spend it the way a flat ceiling
forbids. Coverage is identical on every case at both ends of the tightness axis.

So the approximation `rules.md` has made since T1 is **confirmed on evidence rather than assumed**,
which is the last thing in that section standing on an assertion. Collapsing a reference period into
a weekly rate loses a freedom the optimiser will use and cannot convert into a staffed shift.

What that does not say is that the pool never matters. It is given here as exactly the flat ceiling's
total, so the two arms are equally generous and differ only in distribution. A pool that is *tighter*
than the weeks it spans — a quarter nearly spent — binds where no weekly ceiling would, and this set
has no such case in it because the generator does not produce one.

## What this does not measure

**Anything but cold generation.** These are generated months solved from empty. A replan over four
weeks would pin the past and price deviation, which changes the search but not the coupling argument.

**Anything but cold generation.** These are generated months solved from empty. A replan over four
weeks would pin the past and prices deviation, which changes the search but not the coupling
argument.

**Three seeds, one scenario class, one tenant size.** Enough to show identical coverage six times
over; not a distribution.
