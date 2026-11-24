# Prediction, v4 addition: condition D (single-flight)

Written 2026-11-24, before condition D was coded or run. Deviation from the workflow: written by
Claude, not decided by Marcin. Marcin chose to add single-flight ("Prose plus single-flight",
2026-11-24) after an outside review named it the exact .NET equivalent of Discord's coalescing;
he did not state a prediction. This file is fixed before any D run and is shown to him with the
results.

Scenario: unchanged from `PREDICTION.md` (1,000 concurrent requests for one cold key, one shared
gate, fake repository counting calls and waiting 100 ms; each burst a fresh process).

| condition | what it is | predicted calls per burst |
|---|---|---|
| D | single-flight: a `ConcurrentDictionary` of in-flight `Lazy<Task<T>>`, entry removed when the query completes; nothing is stored afterwards | exactly 1 |

Wrong if any D burst is above 1, or if any burst returns more than one distinct value.

Plan: 5 D bursts, then 1 B burst as a control that the edited build still gives B's result (1).
Each a fresh process, 1,000 callers, 100 ms. Records in `runs/v4/`. A 10-caller harness check
of D runs first, after this file is hashed, and is excluded from every reader-facing figure.
