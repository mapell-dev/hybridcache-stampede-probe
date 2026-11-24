"""Run the plan: 15 confirmatory bursts (5 x A, B, C) in seeded random order, each a fresh
process, then one exploratory A burst with a 1 ms delay. Writes one JSON per burst and a
manifest to ../runs/. Build first: dotnet build -c Release. Usage: python3 run_all.py [--smoke]   (--smoke: 10 callers, harness check)"""
import hashlib, json, pathlib, platform, random, subprocess, sys, datetime

HERE = pathlib.Path(__file__).resolve().parent
SEED = 20261209  # publication date; fixed before the first run
smoke = "--smoke" in sys.argv
out = HERE.parent / "runs" / ("smoke" if smoke else "")
out.mkdir(parents=True, exist_ok=True)
dll = HERE / "bin/Release/net10.0/Probe.dll"

def sh(*cmd):
    return subprocess.run(cmd, capture_output=True, text=True, check=True, cwd=HERE).stdout.strip()

assets = json.loads((HERE / "obj/project.assets.json").read_text())["libraries"]
order = [c for c in "ABC" for _ in range(5)]
random.Random(SEED).shuffle(order)
plan = [(c, 100, "confirmatory") for c in order] + [("A", 1, "exploratory")]
callers = "10" if smoke else "1000"

manifest = {
    "started": datetime.datetime.now(datetime.timezone.utc).isoformat(timespec="seconds"),
    "seed": SEED, "order": "".join(order), "smoke": smoke,
    "sdk": sh("dotnet", "--version"),
    "packages": sorted(k for k in assets if k.startswith(("Microsoft.Extensions.Caching.Hybrid/",
                                                        "Microsoft.Extensions.Caching.Memory/",
                                                        "Microsoft.Extensions.DependencyInjection/"))),
    "machine": sh("sysctl", "-n", "machdep.cpu.brand_string"), "macos": platform.mac_ver()[0],
    "build": "Release", "prediction_sha256": hashlib.sha256((HERE / "PREDICTION.md").read_bytes()).hexdigest(),
    "bursts": [],
}
for n, (cond, delay, kind) in enumerate(plan, 1):
    r = subprocess.run(["dotnet", str(dll), cond, str(delay), callers], capture_output=True, text=True, cwd=HERE)
    rec = {"burst": n, "kind": kind, "exit": r.returncode, "stderr": r.stderr.strip()}
    try:
        rec |= json.loads(r.stdout)
    except json.JSONDecodeError:
        rec["stdout"] = r.stdout
    (out / f"{n:02d}-{cond}-{delay}ms.json").write_text(json.dumps(rec, indent=2) + "\n")
    manifest["bursts"].append({k: rec.get(k) for k in ("burst", "kind", "condition", "delayMs", "repositoryCalls", "exit")})
    print(n, cond, delay, kind, rec.get("repositoryCalls"), rec.get("callerStartSpreadMs"), flush=True)
manifest["finished"] = datetime.datetime.now(datetime.timezone.utc).isoformat(timespec="seconds")
(out / "manifest.json").write_text(json.dumps(manifest, indent=2) + "\n")
