# hybridcache-stampede-probe

The probe behind the mapell.dev article [Who fixed Discord's hot partitions: the new database or the layer in front?](https://mapell.dev/articles/discord-hot-partitions).

It sends 1,000 concurrent requests for one cold key, released together on one gate, to a fake database that counts its calls and waits 100 ms like a query. Each burst is a fresh process. The question is how many of those requests reach the database.

| Condition | Setup | Predicted database calls |
|---|---|---|
| A | `IMemoryCache.GetOrCreateAsync` | about 1,000 (wrong if under 900) |
| B | one `HybridCache` | 1 |
| C | two `HybridCache` instances, 500 requests each | 2 |
| D | single-flight (`SingleFlight<T>` in `Program.cs`) | 1 |

## Results

The article's table comes from `runs/v5/`: 20 bursts, 5 per condition, in one order shuffled with seed 20261124.

| Condition | Database calls, 5 bursts | Caller start spread, max |
|---|---|---|
| A | 1000, 1000, 1000, 1000, 1000 | 4.68 ms |
| B | 1, 1, 1, 1, 1 | 6.04 ms |
| C | 2, 2, 2, 2, 2 | 6.17 ms |
| D | 1, 1, 1, 1, 1 | 3.65 ms |

Every burst returned one distinct value. Every prediction held.

Earlier runs, kept as records:

- `runs/` (v3): A, B and C, 5 bursts each, seed 20261209. A 1,000, B 1, C 2 in every burst. One extra A burst with a 1 ms query, outside the prediction, sent 966 of 1,000 requests to the database.
- `runs/v4/`: D, 5 bursts, 1 in every burst, plus one B control burst (1).
- `runs/smoke/` and `runs/v4/smoke/`: 10-caller harness checks before the real runs. Not results.
- `runs/after-edit/`: one 10-caller check after a one-line source edit. Not a result.

`runs/RESULTS.md` is the full record, including every derived figure and how it was derived.

## Which source made which runs

Each `manifest.json` records the sha256 of the prediction file, and from v4 on the sha256 of `Program.cs`.

| Runs | Source | sha256 | Prediction file | sha256 |
|---|---|---|---|---|
| `runs/`, `runs/smoke/` | `history/Program-v3.cs` | `6823ffd8bcd93c88f2baa6399fc82d1504608f29993094b1c8b74a368f448244` | `probe/PREDICTION.md` | `be3d1e9f426e6bd4b1308e1a0a56d740789c1c7491211cc844cc657fd592ef20` |
| `runs/after-edit/` | `history/Program-v3-edited.cs` (`var memory` became `IMemoryCache memory`) | `9b65664e82f1dfd7941d20fb6df92b0bbed50178a57334b5adc04b1a263d4479` | none | |
| `runs/v4/`, `runs/v4/smoke/` | `probe/Program.cs` (adds condition D) | `42ae61619dbb1edb6be1a32359f7cebac8588b3318bb5b7030df6b799dd43939` | `probe/PREDICTION-v4.md` | `6e532b679f4b51a341952cbf5b19d0c67d93f1056d745673d86fab53d7b79545` |
| `runs/v5/` | `probe/Program.cs` | `42ae61619dbb1edb6be1a32359f7cebac8588b3318bb5b7030df6b799dd43939` | `probe/PREDICTION-v5.md` | `caa8c18d969660ca0f03e95ae3abd91ed0e1b4540fc8e49300eac4b036c28831` |

Check a file with `shasum -a 256 <file>`. The prediction files are published unchanged, so their hashes still match. The A, B and C predictions are Marcin's. The D prediction was written by Claude, his AI assistant, before D was coded; `PREDICTION-v4.md` says so.

## Run it yourself

You need the .NET 10 SDK (`probe/global.json` pins 10.0.302 and rolls forward to the latest patch) and Python 3.

```bash
cd probe
dotnet build -c Release
python3 run_v5.py
```

`run_v5.py` writes one JSON file per burst and a `manifest.json` to `runs/v5/`, replacing the records there. To run a single burst: `dotnet bin/Release/net10.0/Probe.dll <A|B|C|D> [delayMs=100] [callers=1000]`.

`run_all.py` and `run_v4.py` are the scripts for the earlier runs. To repeat v3 exactly, build from `history/Program-v3.cs`.

Tested on an Apple M2 Pro with macOS 27.2.1, .NET 10.0.10, `Microsoft.Extensions.Caching.Hybrid` 11.0.1, `Microsoft.Extensions.Caching.Memory` 11.0.0 and `Microsoft.Extensions.DependencyInjection` 11.0.0. The counts should not depend on the machine; the timings will.

It's a practitioner's check, not a study.

## License

MIT, see `LICENSE`.
