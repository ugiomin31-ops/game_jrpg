"""Recompile the running Unity editor and print compile errors/warnings compactly.

Usage: python Tools/unity_check.py [--no-recompile] [--warnings]
Requires the `unity` CLI (Unity Pipeline package) and the editor open on this project.
Exit code 1 when compile errors exist.
"""
import json
import subprocess
import sys
import time

PROJECT = r"C:\Users\User\Desktop\game"


def cmd(*args, timeout=60):
    r = subprocess.run(["unity", "command", *args, "--result-only", "--project-path", PROJECT],
                       capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=timeout + 15, shell=True)
    out = r.stdout.strip()
    try:
        return json.loads(out)
    except Exception:
        return {"raw": out, "err": r.stderr.strip()}


def main():
    warnings = "--warnings" in sys.argv
    if "--no-recompile" not in sys.argv:
        cmd("clear_console")
        cmd("recompile")
        t0 = time.time()
        while time.time() - t0 < 240:
            time.sleep(3)
            st = cmd("recompile_status")
            s = json.dumps(st)
            if "completed" in s or "up_to_date" in s or "idle" in s:
                break
        time.sleep(2)
    res = cmd("console", "--tail", "200")
    entries = res.get("entries", []) if isinstance(res, dict) else []
    gt = res.get("groundTruth", {}) if isinstance(res, dict) else {}
    errs = [e for e in entries if e.get("level") == "error" and "/api/exec" not in e.get("message", "")]
    warns = [e for e in entries if e.get("level") == "warning"]
    seen = set()
    for e in errs + (warns if warnings else []):
        m = e.get("message", "").strip()
        if m in seen:
            continue
        seen.add(m)
        print(f"[{e.get('level')}] {m[:600]}")
    print(f"compilationFailed={gt.get('compilationFailed')} errors={len(errs)} warnings={len(warns)}")
    sys.exit(1 if gt.get("compilationFailed") or errs else 0)


if __name__ == "__main__":
    main()
