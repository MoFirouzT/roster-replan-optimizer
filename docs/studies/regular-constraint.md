# The `regular` automaton against sliding windows

**Question.** [`model.md`](../specs/model.md#the-regular-automaton) makes this a study rather than
an assumption on purpose: the automaton is the textbook encoding for a sequence rule, and the spec
wanted it to confirm the win rather than take it on faith.

**Answer.** It loses. `R-CONSEC-DAYS` as an automaton is **19% slower to search on 28 of 28 cases**,
with an identical variable and constraint count, and it costs the day coordinate in violation
reporting. The spec's own suspicion — "at a seven-day horizon the window count is trivially small" —
turns out to understate it: at this horizon the window count is **one**.

    uv run python -m benchmarks.studies --only automaton

## Why there is only one window

`max_consecutive_days` is 6 and the horizon is 7 days, so the sliding-window encoding builds
`range(-prior, days - limit)` = a single window per employee. The naive encoding it was going to
replace is therefore *one linear inequality over seven booleans*, and an automaton over the same
seven booleans has to beat that. It does not.

| quantity | ratio, automaton against windows | helped | hurt |
| --- | --- | --- | --- |
| variables | 1.000 | 0 | 0 |
| constraints | 1.000 | 0 | 0 |
| build time | 0.997 | 16 | 8 |
| search time | **1.196** | 0 | **24** |
| total time | 1.065 | 0 | 24 |

The same holds on the larger cold instances: search 1.195, 19% slower, and a 17% worse total.

The counts being *identical* is the tell. Both encodings need the same seven `worked` indicators per
employee — that is where the model's size is — and then one constraint each. The automaton is one
constraint that propagates a state machine; the window is one constraint that sums seven booleans and
compares. At this size the second is simply cheaper, and there is no structure for the first to
exploit.

## The reporting cost, which is the more durable objection

An automaton **can** be gated — `only_enforce_if` on `add_automaton` is accepted and properly
enforced, verified in `tests/test_studies.py` rather than assumed, since an API accepting a call is
not evidence that it means anything. But one automaton covers the whole week, so its assumption
literal can only say *this employee's week is wrong somewhere*.

The window encoding carries one literal per (employee, window) and names the **day** the streak
breached the limit — the same coordinate `checker.py` reports. That matters beyond neatness:

- `violations()` compares model gates against checker violations on the `(rule, employee, day, shift)`
  key. An automaton gate with no day would not match its counterpart, so the differential harness
  would need an exception carved into it — and an exception in the harness that proves the two
  readings agree is a bad thing to trade for 20% of 3 ms in the wrong direction.
- The explainer turns cores into rule IDs *and coordinates*. "Employee 7's week violates
  R-CONSEC-DAYS" is a worse explanation than "employee 7 would work a seventh consecutive day on
  Saturday".

## Where this would flip

The automaton's case is a longer horizon. At a four-week reference period the window count per
employee grows with the horizon while the automaton stays one constraint with a slightly larger state
space, and the comparison should reverse. That is not hypothetical for this domain — Belgian
reference-period arithmetic is exactly a multi-week rule ([`D-014`](../decisions.md#d-014), [`D-033`](../decisions.md#d-033)) — but it is not the model
this project ships, which is a one-week horizon.

**Rejected at this horizon, and the condition for revisiting is a horizon longer than about two
weeks** ([`D-088`](../decisions.md#d-088)). `R-WEEKLY-REST` is not a candidate either way: it is a rule about a continuous
35-hour free run measured in hours, and a day-level automaton cannot express it.
