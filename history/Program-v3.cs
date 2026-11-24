// One burst per process: 1,000 concurrent requests for one cold key, counted at a fake database.
// Usage: dotnet Probe.dll <A|B|C> [delayMs=100] [callers=1000]
//   A = IMemoryCache.GetOrCreateAsync, B = one HybridCache, C = two HybridCache instances.
using System.Diagnostics;
using System.Runtime;
using System.Runtime.InteropServices;
using System.Text.Json;
using Microsoft.Extensions.Caching.Hybrid;
using Microsoft.Extensions.Caching.Memory;
using Microsoft.Extensions.DependencyInjection;

var condition = args.Length > 0 ? args[0] : "B";
var delayMs = args.Length > 1 ? int.Parse(args[1]) : 100;
var callers = args.Length > 2 ? int.Parse(args[2]) : 1000;
const string Key = "channel:42:messages";

var db = new FakeDatabase(delayMs);

// Condition setup: each "instance" is its own ServiceProvider, as two app instances would be.
Func<int, ValueTask<string>> read;
switch (condition)
{
    case "A":
        var memory = new MemoryCache(new MemoryCacheOptions());
        read = async _ => (await memory.GetOrCreateAsync(Key, _ => db.LoadAsync(Key)))!;
        break;
    case "B":
    case "C":
        var instances = Enumerable.Range(0, condition == "B" ? 1 : 2)
            .Select(_ => new ServiceCollection().AddHybridCache().Services
                .BuildServiceProvider().GetRequiredService<HybridCache>())
            .ToArray();
        read = i => instances[i % instances.Length]
            .GetOrCreateAsync(Key, async ct => await db.LoadAsync(Key));
        break;
    default:
        throw new ArgumentException($"unknown condition {condition}");
}

// The gate: every caller awaits it, then all are released at once.
var gate = new TaskCompletionSource(TaskCreationOptions.RunContinuationsAsynchronously);
var clock = Stopwatch.StartNew();
var starts = new long[callers];
var latencies = new long[callers];

async Task<string> Caller(int i)
{
    await gate.Task;
    starts[i] = clock.ElapsedTicks;
    var value = await read(i);
    latencies[i] = clock.ElapsedTicks - starts[i];
    return value;
}

var tasks = Enumerable.Range(0, callers).Select(Caller).ToArray();
var released = clock.ElapsedTicks;
gate.SetResult();
var values = await Task.WhenAll(tasks);

double Ms(long ticks) => ticks * 1000.0 / Stopwatch.Frequency;
ThreadPool.GetMinThreads(out var minWorker, out var minIo);
var entries = db.Entries.ToArray();

Console.WriteLine(JsonSerializer.Serialize(new
{
    condition,
    delayMs,
    callers,
    repositoryCalls = db.Calls,
    distinctValues = values.Distinct().Count(),
    callerStartSpreadMs = Ms(starts.Max() - starts.Min()),
    firstCallerAfterReleaseMs = Ms(starts.Min() - released),
    factoryEntrySpreadMs = entries.Length > 0 ? Ms(entries.Max() - entries.Min()) : 0,
    latencyMsMin = Ms(latencies.Min()),
    latencyMsMax = Ms(latencies.Max()),
    runtime = RuntimeInformation.FrameworkDescription,
    os = RuntimeInformation.OSDescription,
    arch = RuntimeInformation.ProcessArchitecture.ToString(),
    processors = Environment.ProcessorCount,
    serverGc = GCSettings.IsServerGC,
    gcLatencyMode = GCSettings.LatencyMode.ToString(),
    threadPoolMinWorker = minWorker,
    threadPoolMinIo = minIo,
}));

// Stands in for a query: counts every call, records when it was entered, waits delayMs.
sealed class FakeDatabase(int delayMs)
{
    private int _calls;
    public int Calls => _calls;
    public System.Collections.Concurrent.ConcurrentBag<long> Entries { get; } = new();

    public async Task<string> LoadAsync(string key)
    {
        Interlocked.Increment(ref _calls);
        Entries.Add(Stopwatch.GetTimestamp());
        await Task.Delay(delayMs);
        return $"messages for {key}";
    }
}
