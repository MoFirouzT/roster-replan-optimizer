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
**linearly**, not by an order of magnitude, and four weeks answers in about 112 ms end to end.
What actually justifies the rejection is the half the sentence never mentions: a longer horizon
**buys nothing**. Four weeks solved at once and four weeks solved one at a time reach *identical
coverage* on every case tried, at both ends of the tightness axis — and under pressure the single
solve is up to six times slower for it.

    uv run python -m benchmarks.studies --only horizon

## The cost

Generated replan scenarios at `demand_ratio` 0.70, 12 employees, median of three seeds:

| days | slots | variables | constraints | build ms | search ms |
| --- | --- | --- | --- | --- | --- |
| 7 | 21 | 1,035 | 1,334 | 5.4 | 3.5 |
| 14 | 42 | 2,056 | 2,720 | 12.2 | 19.2 |
| 28 | 84 | 4,058 | 5,376 | 29.5 | 82.9 |

**Size is linear in the horizon.** Four times the days gives 3.9× the variables and 4.0× the
constraints. The rest-gap pairs stay local — a gap is eleven hours, so no shift conflicts with one a
week away — and nothing else aggregates across the horizon either. "An order of magnitude" describes
a growth this model does not have.

**Search is not linear.** It grows 23× over the same range, against build's 5.5×. That is the real
cost of a longer horizon, and it is in the term the rejection did not name.

**`D-081` inverts between one week and two.** At seven days build costs more than search (5.4 against
3.5), which is the premise several records reason from: it is why the two clocks are reported
separately, why the compiled-model cache was worth trying (`D-093`), and why memoising
`Instance.window` was the largest single win (`D-092`). At fourteen days search already costs more
than build (19.2 against 12.2), and at twenty-eight it costs nearly three times as much. Every
performance conclusion in this repo is scoped to a one-week horizon, and this is where that scoping
stops being a formality.

## What it buys

The comparison the rejection is really about: **one four-week solve, against four one-week solves
with the boundary state carried between them**, which is what the service does today. Cold
generation, three seeds, at both ends of the coverage axis. `short` is unstaffed positions across the
whole month.

| demand ratio | seed | one solve: short | search ms | four chained: short | search ms |
| --- | --- | --- | --- | --- | --- |
| 0.70 | 0 | 0 | 120.6 | 0 | 162.3 |
| 0.70 | 1 | 0 | 129.0 | 0 | 135.6 |
| 0.70 | 2 | 0 | 121.3 | 0 | 118.8 |
| 0.90 | 0 | **5** | 239.4 | **5** | 123.3 |
| 0.90 | 1 | **5** | 432.5 | **5** | 165.5 |
| 0.90 | 2 | **5** | 555.5 | **5** | 94.3 |

**Coverage is identical on every case.** Not close — identical, including at 0.90 where five
positions go unstaffed either way. The four-week solve sees the whole month and finds nothing the
weekly sequence misses.

The reason is that **the weeks are barely coupled**. `R-MAX-WEEKLY` binds inside a week and
`R-WEEKLY-REST` is measured inside a week, so neither reaches across a boundary at all. What does
reach across is `R-REST-GAP` and `R-CONSEC-DAYS`, and both reach exactly as far as a caller can
already tell them to: `last_shift_end_before_horizon` and
`consecutive_days_worked_before_horizon` are the boundary, and they carry it faithfully. A model with
almost no coupling between its blocks does not need to see them together.

**Under pressure the longer horizon is the slower one.** At 0.90 the single solve takes 239 to 555 ms
of search where the chained sequence takes 94 to 166 ms in total — the four small searches are
together two to six times cheaper than the one large one, for the same answer. The tight setting is
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

## What this does not measure

**The reference-period budget, which is the thing `rules.md` is actually about.** Both arms here
carry the same per-week ceiling, so this compares horizon *lengths*. The approximation the spec
describes is different: a caller resolves a rolling quarter into one number, and what is lost is the
freedom to spend it unevenly — 45 hours this week against 31 next, inside the same quarterly total.
A single four-week solve with a pooled budget could do that; four chained solves with a weekly
ceiling cannot, and neither can the four-week solve measured here, because the field does not exist.
`D-111` deferred it, and this study is the reason to reconsider: it is the one place a longer horizon
has a mechanism to win, and it is exactly the place the measurement cannot reach.

**Anything but cold generation.** These are generated months solved from empty. A replan over four
weeks would pin the past and prices deviation, which changes the search but not the coupling
argument.

**Three seeds, one scenario class, one tenant size.** Enough to show identical coverage six times
over; not a distribution.
