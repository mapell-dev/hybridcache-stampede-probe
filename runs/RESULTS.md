# Probe results, 2026-11-24

Every burst is a file in this folder (`NN-<condition>-<delay>ms.json`); `manifest.json` holds
the environment, the seed and the order. All figures below are copied from those files.

## Setup, as recorded

- Run 2026-11-24, 08:10:22 to the end of burst 16 (UTC); Apple M2 Pro, 10 cores, macOS 27.2.1,
  Arm64.
- .NET SDK 10.0.302, runtime .NET 10.0.10, Release build, workstation GC (`serverGc: false`,
  latency mode Interactive), `ThreadPool` minimum 10 worker / 1 IO threads (defaults).
- Packages restored (`obj/project.assets.json`): `Microsoft.Extensions.Caching.Hybrid` 11.0.1,
  `Microsoft.Extensions.Caching.Memory` 11.0.0, `Microsoft.Extensions.DependencyInjection` 11.0.0.
- Seed 20261209 (fixed in `probe/run_all.py` before the first run); confirmatory order
  `AAAABBCCBBBCCCA`, then the exploratory burst.
- `probe/PREDICTION.md` sha256 `be3d1e9f…ef20`, written 2026-11-24T08:09Z; the manifest
  records the same hash, so the file was unchanged when the runs started.

## Confirmatory: repository calls per burst (1,000 callers, 100 ms fake query)

| condition | predicted | burst results | prediction |
|---|---|---|---|
| A, `IMemoryCache.GetOrCreateAsync` | about 1,000 (wrong if under 900) | 1000, 1000, 1000, 1000, 1000 (bursts 1, 2, 3, 4, 15) | held |
| B, one `HybridCache` | exactly 1 | 1, 1, 1, 1, 1 (bursts 5, 6, 9, 10, 11) | held |
| C, two `HybridCache` instances | exactly 2 | 2, 2, 2, 2, 2 (bursts 7, 8, 12, 13, 14) | held |

All 16 processes exited 0, and in every burst all 1,000 callers received the same value
(`distinctValues: 1`).

## Manipulation check: did the callers overlap?

Caller start spread (first to last caller past the gate): 4.45 to 5.95 ms across the 15
bursts; first caller 0.97 to 1.37 ms after release. In A, the 1,000 factory entries spread
over 2.82 to 3.13 ms, all inside the 100 ms fake query, so every A caller missed while the
first query was still in flight. A's count is not a harness artifact of callers arriving one
after another.

## Exploratory (labeled observation, not confirmatory)

- Burst 16, A with a 1 ms fake query: 966 repository calls. The competing explanation "the
  100 ms delay, not the cache API, decides A's count" is not supported: with a query about one
  hundredth as long, 96.6% of callers still reached the database. Callers started over 5.31 ms
  and factory entries spread over 3.44 ms. Why so few hits: not tested. A guess, not a
  finding: the entry is stored only after the factory's continuation runs, and that queues
  behind the other callers on a 10-thread pool.
- Caller latency (recorded, not a finding per the plan): A max 105.1 to 107.2 ms; B and C max
  111.2 to 113.4 ms.

## Outside the plan, excluded

- `runs/smoke/`: one harness check before the confirmatory runs, the same 16-burst plan with
  10 callers instead of 1,000, to confirm the program and the records work. Results: A 10,
  B 1, C 2, the exploratory A 10. Excluded from every reader-facing figure. It ran the same
  conditions at 1% of the size, so it previewed the shape of the result
  before the confirmatory runs; the prediction file was already written and hashed.
- Build change, not a protocol change: `Microsoft.Extensions.DependencyInjection` 11.0.0 was
  added to the csproj because `BuildServiceProvider` lives there (first build failed without
  it). `probe/global.json` pins SDK 10.0.302.

## Source edit after the runs (2026-11-24, at the draft)

`probe/Program.cs` line 24 changed from `var memory = new MemoryCache(...)` to
`IMemoryCache memory = new MemoryCache(...)`, so the post's listing names the interface the prose
talks about (the article check flagged `IMemoryCache` in prose against `MemoryCache` in the code).
Same object; `GetOrCreateAsync` is an extension method on `IMemoryCache` either way, so the call
resolves to the same method. Hashes: before `6823ffd8…8244`, after `9b65664e…4479`. The
confirmatory runs above used the "before" source. Release build after the edit: 0 warnings,
0 errors. One harness check after the edit, outside the plan and excluded:
`runs/after-edit/A-100ms-10callers.json`, A with 10 callers, 10 repository calls.

## v4 addition: condition D, single-flight (2026-11-24)

Added after an outside senior .NET review of draft 1 named single-flight as the exact .NET
equivalent of Discord's in-flight coalescing; Marcin chose "Prose plus single-flight".

- `probe/PREDICTION-v4.md` written and hashed (sha256 `6e532b67…9545`) at 2026-11-24T13:26Z,
  before D was coded; the prediction is Claude's, not Marcin's (recorded deviation): D exactly 1.
- `probe/Program.cs` gained case "D" and the `SingleFlight<T>` class (a `ConcurrentDictionary`
  of `Lazy<Task<T>>`, entry removed when the query completes). Conditions A, B and C unchanged.
  Hashes: before `9b65664e…4479`, after `42ae6161…3943`. Release build 0 warnings, 0 errors.
- Harness check first, excluded: `runs/v4/smoke/`, 10 callers, D 1 in each of 5 bursts, B 1.
- Runs (`probe/run_v4.py`, records in `runs/v4/`), 1,000 callers, 100 ms, each a fresh process:

| burst | condition | repository calls | distinct values | caller start spread | first caller after release |
|---|---|---|---|---|---|
| 1 to 5 | D, single-flight | 1, 1, 1, 1, 1 | 1 | 3.25 to 3.68 ms | 1.32 to 1.51 ms |
| 6 | B, one `HybridCache` (control on the edited build) | 1 | 1 | 22.88 ms | 7.15 ms |

Prediction held. The B control reproduced B's v3 result on the edited build; its caller start
spread (22.88 ms) is wider than any v3 burst (at most 5.95 ms) but still well inside the 100 ms
query, so the callers overlapped. Not investigated; a single control burst, not a finding.
Caller latency max (recorded, not a finding): D 103.9 to 104.5 ms.

## v5: all four conditions in one seeded, shuffled run (2026-11-24)

Run after the retrospective plan review of D (blocker: D had run as a separate, unshuffled block
on an edited build; Marcin: "Rerun all four"). This run is the source of the post's results
table from now on; v3 and v4 above stay as records.

- `probe/PREDICTION-v5.md` (sha256 `caa8c18d…8831`, written 2026-11-24T15:23Z, before the run):
  the existing predictions restated, A about 1,000 (wrong under 900), B 1, C 2, D 1; seed
  20261124 fixed there. No smoke run, no exploratory burst.
- Build: `Program.cs` sha256 `42ae6161…3943` (unchanged since v4), Release, 0 warnings, 0
  errors, built just before the run. Manifest records SDK 10.0.302, packages
  `Microsoft.Extensions.Caching.Hybrid` 11.0.1, `Microsoft.Extensions.Caching.Memory` 11.0.0,
  `Microsoft.Extensions.DependencyInjection` 11.0.0, Apple M2 Pro, macOS 27.2.1; runtime .NET
  10.0.10 in every burst.
- Run 15:24:03 to 15:24:07 UTC, `probe/run_v5.py`, records in `runs/v5/`; order
  `CCBDDDCDABBDCABCAAAB`. All 20 processes exited 0; every burst returned one distinct value.

| condition | bursts | repository calls | caller start spread | first caller after release | prediction |
|---|---|---|---|---|---|
| A, `IMemoryCache.GetOrCreateAsync` | 9, 14, 17, 18, 19 | 1000 each | 4.38 to 4.68 ms | 1.16 to 1.55 ms | held |
| B, one `HybridCache` | 3, 10, 11, 15, 20 | 1 each | 5.84 to 6.04 ms | 0.94 to 1.18 ms | held |
| C, two `HybridCache` instances | 1, 2, 7, 13, 16 | 2 each | 5.34 to 6.17 ms | 0.98 to 1.16 ms | held |
| D, single-flight | 4, 5, 6, 8, 12 | 1 each | 3.38 to 3.65 ms | 1.32 to 1.52 ms | held |

Manipulation check: every caller started within 6.17 ms of the first, inside the 100 ms query;
in A the 1,000 factory entries spread over 2.79 to 3.02 ms, so every A caller missed while the
first query was in flight. Same counts as v3 and v4, so no reading changes. The v4 B control's
wide start spread (22.88 ms) did not recur (B 5.84 to 6.04 ms here). Caller latency max
(recorded, not a finding): A 105.0 to 107.1 ms, B 111.5 to 113.5, C 112.7 to 113.5, D 103.3 to
104.7. The exploratory 1 ms A burst (966 calls) remains from v3 and was not repeated.
