"""v4 addition: 5 bursts of condition D (single-flight), then 1 B burst as a control on the
edited build. Each a fresh process. Build first: dotnet build -c Release.
Usage: python3 run_v4.py [--smoke]   (--smoke: 10 callers, harness check, excluded)"""
import hashlib, json, pathlib, subprocess, sys, datetime

HERE = pathlib.Path(__file__).resolve().parent
smoke = "--smoke" in sys.argv
out = HERE.parent / "runs" / "v4" / ("smoke" if smoke else "")
out.mkdir(parents=True, exist_ok=True)
dll = HERE / "bin/Release/net10.0/Probe.dll"
plan = [("D", 100, "confirmatory")] * 5 + [("B", 100, "control")]
callers = "10" if smoke else "1000"
sha = lambda f: hashlib.sha256((HERE / f).read_bytes()).hexdigest()
manifest = {"started": datetime.datetime.now(datetime.timezone.utc).isoformat(timespec="seconds"),
            "smoke": smoke, "prediction_sha256": sha("PREDICTION-v4.md"),
            "program_sha256": sha("Program.cs"), "bursts": []}
for n, (cond, delay, kind) in enumerate(plan, 1):
    r = subprocess.run(["dotnet", str(dll), cond, str(delay), callers], capture_output=True, text=True, cwd=HERE)
    rec = {"burst": n, "kind": kind, "exit": r.returncode, "stderr": r.stderr.strip()}
    try:
        rec |= json.loads(r.stdout)
    except json.JSONDecodeError:
        rec["stdout"] = r.stdout
    (out / f"{n:02d}-{cond}-{delay}ms.json").write_text(json.dumps(rec, indent=2) + "\n")
    manifest["bursts"].append({k: rec.get(k) for k in ("burst", "kind", "condition", "repositoryCalls", "distinctValues", "callerStartSpreadMs", "exit")})
    print(n, cond, kind, rec.get("exit"), rec.get("repositoryCalls"), rec.get("distinctValues"), rec.get("callerStartSpreadMs"), flush=True)
manifest["finished"] = datetime.datetime.now(datetime.timezone.utc).isoformat(timespec="seconds")
(out / "manifest.json").write_text(json.dumps(manifest, indent=2) + "\n")
