# Prediction, v5: all four conditions in one seeded, shuffled run

Written 2026-11-24, before any v5 run, after the retrospective plan review of condition D found
that D had run as a separate, unshuffled block on an edited build (blocker, verified by Marcin:
"Rerun all four"). No new predictions: these are the existing ones, restated.

- A, B, C: Marcin's predictions from `PREDICTION.md` (2026-11-23: "Tak, A~1000, B=1, C=2").
- D: the prediction in `PREDICTION-v4.md`, written by Claude before D was first run.

Scenario: unchanged (1,000 concurrent requests for one cold key, one shared gate, a fake
repository that counts calls and waits 100 ms; each burst a fresh process). Source:
`Program.cs` sha256 `42ae6161…3943`, Release build, built just before the run.

| condition | what it is | predicted calls per burst |
|---|---|---|
| A | `IMemoryCache.GetOrCreateAsync` | about 1,000 |
| B | one `HybridCache` | exactly 1 |
| C | two `HybridCache` instances | exactly 2 |
| D | single-flight | exactly 1 |

Wrong if, in any burst: A is under 900, B above 1, C above 2, D above 1, or any burst returns
more than one distinct value.

Plan: 20 confirmatory bursts, 5 per condition, order shuffled with seed 20261124 (fixed here,
before the run). No smoke run (the harness ran 16 + 6 bursts earlier today). No exploratory
burst. Every burst is reported. Records in `runs/v5/`, with the SDK, package versions, machine
and OS in the manifest. This run replaces v3 and v4 as the source of the post's results table;
v3 and v4 stay in the records.
