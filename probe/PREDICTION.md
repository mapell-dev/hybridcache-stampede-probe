# Prediction, written before any run

Written 2026-11-24, before the probe was built or run. Copied from BRIEF.md v2, Experiment plan
(Marcin, 2026-11-23: "Tak, A~1000, B=1, C=2").

Scenario: 1,000 concurrent requests for one cold key, released together on one shared
`TaskCompletionSource` gate; the repository is a fake that counts calls with `Interlocked` and
waits 100 ms. Metric: repository calls per burst. 5 bursts per condition, each a fresh process.

| condition | what it is | predicted calls per burst |
|---|---|---|
| A | `IMemoryCache.GetOrCreateAsync` | about 1,000 |
| B | one `HybridCache` instance, in-memory only | exactly 1 |
| C | two `HybridCache` instances (two `ServiceProvider`s), burst split evenly | exactly 2 |

The prediction is wrong if, in any burst: B is above 1, C is above 2, or A is under 900.

Confirmatory: the A, B, C counts only. The extra A burst with a 1 ms delay, and anything
noticed after the runs, are exploratory observations.

Run order: the 15 confirmatory bursts shuffled with a fixed seed, recorded in `runs/`.
