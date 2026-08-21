# Archive

How the project got here.

Nothing in this directory is in the reading path.
The live documentation — [`guide/`](../guide) for using the service, [`internals/`](../internals) for changing it — states what is true now.
This is where it comes from: the choices, the measurements, and the several occasions the measurements overturned what a spec had claimed.

**The rule here is supersede, never rewrite.**
A later decision amends an earlier record in place with the supersession named.
A record that gets edited whenever the world moves is not a record.
That applies to the words; file paths are retargeted when documents move, which is not a rewrite.
Neither is renaming a term of art, provided it is renamed here, in the live documents and in the code at once, and nothing but the word changes.

| Document | What it is |
| --- | --- |
| [`decisions.md`](decisions.md) | 149 numbered records — what was chosen, what was rejected, why. Enter through its [lookup table](decisions.md#lookup), or [by theme](decisions.md#by-theme) for the records that make one argument together |
| [`studies/`](studies/README.md) | Seventeen analyses, **including the nulls and the rejected alternatives**. A measured null is a stronger signal than an unmeasured win |
| [`benchmarks.md`](benchmarks.md) | The committed instance set, the four methods compared, the results and their caveats |
| [`finish.md`](finish.md) | Where the project stands, what it got wrong, and the declaration that closed it — left as written |
| [`preferences.md`](preferences.md) | What the objective cannot say across weeks, and what that costs |
| [`capture.md`](capture.md) | Capture and replay: **specified, never built**. The acceptance bar was fixed before the first replay, and there has been no replay |
| [`PLAN.md`](PLAN.md) | The original tiers and sequencing. **Archived, not maintained** |

## Three worth the detour

- [`studies/horizon.md`](studies/horizon.md) — a rejection upheld on evidence that contradicted both reasons the spec gave for it.
- [`studies/penalty-search.md`](studies/penalty-search.md) — where the easy instance distribution would have produced the wrong answer.
- [`studies/mutation-harness.md`](studies/mutation-harness.md) — four blind spots found behind fully green suites, and five times the harness was confidently wrong about itself.
