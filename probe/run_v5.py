"""v5: all four conditions, 5 bursts each, in one seeded shuffle; each burst a fresh process.
Build first: dotnet build -c Release. Usage: python3 run_v5.py"""
import hashlib, json, pathlib, platform, random, subprocess, datetime

HERE = pathlib.Path(__file__).resolve().parent
SEED = 20261124  # fixed in PREDICTION-v5.md before the run
out = HERE.parent / "runs" / "v5"
out.mkdir(parents=True, exist_ok=True)
dll = HERE / "bin/Release/net10.0/Probe.dll"

def sh(*cmd):
    return subprocess.run(cmd, capture_output=True, text=True, check=True, cwd=HERE).stdout.strip()

sha = lambda f: hashlib.sha256((HERE / f).read_bytes()).hexdigest()
assets = json.loads((HERE / "obj/project.assets.json").read_text())["libraries"]
order = [c for c in "ABCD" for _ in range(5)]
random.Random(SEED).shuffle(order)
manifest = {
    "started": datetime.datetime.now(datetime.timezone.utc).isoformat(timespec="seconds"),
    "seed": SEED, "order": "".join(order),
    "sdk": sh("dotnet", "--version"),
    "packages": sorted(k for k in assets if k.startswith(("Microsoft.Extensions.Caching.Hybrid/",
                                                        "Microsoft.Extensions.Caching.Memory/",
                                                        "Microsoft.Extensions.DependencyInjection/"))),
    "machine": sh("sysctl", "-n", "machdep.cpu.brand_string"), "macos": platform.mac_ver()[0],
    "build": "Release", "program_sha256": sha("Program.cs"),
    "dll_sha256": hashlib.sha256(dll.read_bytes()).hexdigest(),
    "prediction_sha256": sha("PREDICTION-v5.md"), "bursts": [],
}
for n, cond in enumerate(order, 1):
    r = subprocess.run(["dotnet", str(dll), cond, "100", "1000"], capture_output=True, text=True, cwd=HERE)
    rec = {"burst": n, "kind": "confirmatory", "exit": r.returncode, "stderr": r.stderr.strip()}
    try:
        rec |= json.loads(r.stdout)
    except json.JSONDecodeError:
        rec["stdout"] = r.stdout
    (out / f"{n:02d}-{cond}-100ms.json").write_text(json.dumps(rec, indent=2) + "\n")
    manifest["bursts"].append({k: rec.get(k) for k in ("burst", "condition", "repositoryCalls", "distinctValues", "callerStartSpreadMs", "exit")})
    print(n, cond, rec.get("exit"), rec.get("repositoryCalls"), rec.get("distinctValues"), rec.get("callerStartSpreadMs"), flush=True)
manifest["finished"] = datetime.datetime.now(datetime.timezone.utc).isoformat(timespec="seconds")
(out / "manifest.json").write_text(json.dumps(manifest, indent=2) + "\n")
