"""Build every CC0-sourced enemy (specs.SPECS) in isolated Blender processes and verify each exported FBX.

Run from the repository root:
  blender -b --factory-startup --python-exit-code 1 -P Blender/enemies_cc0/generate_all.py -- [--only ID ...] [--jobs 2]
Child mode (one enemy, used by the parent):  ... -- --asset ID

Each child: cc0_monsters.build(ID) -> Assets/_Game/Resources/Art/Enemies/<ID>/<ID>.fbx (+ Blender/blend/enemy_cc0_<ID>.blend,
Blender/preview/enemy_cc0_<ID>.png), then re-imports the FBX and checks the contract (Rig + one skinned Body, Col,
M_Toon/M_Emit/M_Clear only, the seven takes with README lengths, every vertex weighted, size close to the target).
Evidence goes to Blender/blend/enemy_cc0_production_<ID>.json and enemy_cc0_production_all.json.
Enemies not in specs.SPECS (see specs.GAPS) keep the procedural model from Blender/enemies_a/generate_all.py.
"""
import argparse
import json
import os
import subprocess
import sys
import time

import bpy

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import cc0_monsters as C  # noqa: E402
import specs  # noqa: E402

A = C.A
ROOT = A.REPO
REPORTS = A.BLEND_DIR
# README frame ranges (inclusive) per take.
RANGES = {"Idle": (40, 60), "Run": (16, 24), "Attack": (18, 30), "Cast": (30, 40), "Hit": (10, 14),
          "Die": (24, 36), "Victory": (36, 48)}


def verify_fbx(eid, fbx):
    bpy.ops.wm.read_factory_settings(use_empty=True)
    bpy.context.scene.render.fps = A.FPS
    bpy.ops.import_scene.fbx(filepath=fbx)
    objs = list(bpy.context.scene.objects)
    rigs = [o for o in objs if o.type == "ARMATURE"]
    meshes = [o for o in objs if o.type == "MESH"]
    problems = []
    if [o.name for o in rigs] != ["Rig"]:
        problems.append(f"armatures {[o.name for o in rigs]}")
    if [o.name for o in meshes] != ["Body"]:
        problems.append(f"meshes {[o.name for o in meshes]}")
    other = [o.name for o in objs if o.type not in ("ARMATURE", "MESH")]
    if other:
        problems.append(f"unexpected objects {other}")
    rig, body = (rigs or [None])[0], (meshes or [None])[0]
    report = {"objects": sorted(o.name for o in objs)}
    if body is not None:
        me = body.data
        report["triangles"] = sum(len(p.vertices) - 2 for p in me.polygons)
        report["vertices"] = len(me.vertices)
        report["materials"] = [m.name for m in me.materials]
        if "Col" not in me.color_attributes:
            problems.append("no Col attribute")
        if any(m.name.split(".")[0] not in A.MATERIALS for m in me.materials):
            problems.append(f"materials {report['materials']}")
        unweighted = sum(not any(g.weight > 0 for g in v.groups) for v in me.vertices)
        report["unweighted_vertices"] = unweighted
        if unweighted:
            problems.append(f"{unweighted} unweighted vertices")
        if not any(m.type == "ARMATURE" and m.object == rig for m in body.modifiers):
            problems.append("Body not skinned to Rig")
    if rig is not None:
        report["bones"] = len(rig.data.bones)
    takes = {a.name.split("|")[-1]: a for a in bpy.data.actions}
    report["clips"] = {}
    for name, (lo, hi) in RANGES.items():
        a = takes.get(name)
        if a is None:
            problems.append(f"missing take {name}")
            continue
        f0, f1 = a.frame_range
        report["clips"][name] = [f0, f1]
        if not (lo <= f1 - f0 <= hi):
            problems.append(f"{name} length {f1 - f0} outside {lo}-{hi}")
    if rig is not None and body is not None and "Idle" in takes:
        lo, hi = C.mesh_bounds(body, rig, takes["Idle"], int(takes["Idle"].frame_range[0]))
        report["idle_bounds"] = [list(map(lambda x: round(x, 3), lo)), list(map(lambda x: round(x, 3), hi))]
        th, tz, tw = specs.TARGETS[eid]
        spec = specs.ALL[eid]
        fit_height = spec.get("fit", "height") == "height" and not spec.get("dress")   # dressing may add height
        if th and fit_height and abs((hi.z - lo.z) - th) > 0.05 * th + 0.02:
            problems.append(f"height {hi.z - lo.z:.2f} != target {th}")
        if tw and spec.get("fit") == "width" and abs((hi.x - lo.x) - tw) > 0.05 * tw + 0.02:
            problems.append(f"width {hi.x - lo.x:.2f} != target {tw}")
        if tz is not None and abs(lo.z - tz) > 0.03:
            problems.append(f"bottom {lo.z:.2f} != target {tz}")
    report["problems"] = problems
    return report


def produce_one(eid):
    started = time.time()
    built = C.build(eid)
    fbx = built["fbx"]
    if not os.path.isfile(fbx) or os.path.getmtime(fbx) < started - 2:
        raise RuntimeError(f"FBX not written: {fbx}")
    check = verify_fbx(eid, fbx)
    result = {"id": eid, "source": built["source"], "generator": "Blender/enemies_cc0/cc0_monsters.py",
              "blender_version": bpy.app.version_string,
              "produced_at_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
              "fbx": os.path.relpath(fbx, ROOT).replace("\\", "/"), "fbx_bytes": os.path.getsize(fbx),
              "scale_from_source": built["scale"], "built": {k: built[k] for k in ("triangles", "bones", "materials")},
              "reimported_fbx": check}
    os.makedirs(REPORTS, exist_ok=True)
    with open(os.path.join(REPORTS, f"enemy_cc0_production_{eid}.json"), "w", encoding="utf-8") as fh:
        json.dump(result, fh, ensure_ascii=False, indent=2)
    print("CC0_PRODUCTION " + json.dumps(result), flush=True)
    if check["problems"]:
        raise RuntimeError(f"{eid}: {check['problems']}")


def child_cmd(eid):
    script = os.path.abspath(__file__)
    exe = bpy.app.binary_path or ""
    if os.path.basename(exe).lower().startswith("blender"):
        return [exe, "-b", "--factory-startup", "--python-exit-code", "1", "-P", script, "--", "--asset", eid]
    return [sys.executable, script, "--", "--asset", eid]      # bpy installed as a Python module


def main():
    args = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--asset", choices=sorted(specs.ALL))
    ap.add_argument("--only", nargs="+", choices=sorted(specs.ALL))
    ap.add_argument("--jobs", type=int, default=1)
    opts = ap.parse_args(args)
    if opts.asset:
        produce_one(opts.asset)
        return
    ids = opts.only or list(specs.SPECS)
    os.makedirs(REPORTS, exist_ok=True)
    pending, running, failures = list(ids), [], []
    while pending or running:
        while pending and len(running) < max(1, opts.jobs):
            eid = pending.pop(0)
            log = open(os.path.join(REPORTS, f"enemy_cc0_production_{eid}.log"), "w", encoding="utf-8")
            print("PRODUCING", eid, flush=True)
            running.append((eid, log, subprocess.Popen(child_cmd(eid), cwd=ROOT, stdout=log, stderr=subprocess.STDOUT)))
        time.sleep(0.5)
        for item in list(running):
            eid, log, proc = item
            if proc.poll() is None:
                continue
            running.remove(item)
            log.close()
            if proc.returncode:
                failures.append({"id": eid, "exit_code": proc.returncode, "log": log.name})
                print(f"FAILED {eid} (see {log.name})", flush=True)
            else:
                print("PRODUCED", eid, flush=True)
    reports = []
    for eid in specs.ALL:
        path = os.path.join(REPORTS, f"enemy_cc0_production_{eid}.json")
        if os.path.isfile(path):
            with open(path, encoding="utf-8") as fh:
                reports.append(json.load(fh))
    summary = {"cc0_ids": list(specs.SPECS), "rebuilt_ids": ids, "procedural_ids_kept": specs.GAPS,
               "failures": failures, "reports": reports}
    with open(os.path.join(REPORTS, "enemy_cc0_production_all.json"), "w", encoding="utf-8") as fh:
        json.dump(summary, fh, ensure_ascii=False, indent=2)
    print("CC0_PRODUCTION_ALL " + json.dumps({k: v for k, v in summary.items() if k != "reports"}), flush=True)
    if failures:
        raise SystemExit(f"{len(failures)} CC0 enemy builds failed")


if __name__ == "__main__":
    main()
