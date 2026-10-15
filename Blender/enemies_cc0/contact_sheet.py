"""Render labelled review sheets straight from the exported enemy FBX files (what Unity will import).

  blender -b --factory-startup -P Blender/enemies_cc0/contact_sheet.py -- --out sheet.png [--ids ID ...] [--cols 7]
  blender -b --factory-startup -P Blender/enemies_cc0/contact_sheet.py -- --out actions.png --actions --ids skeleton fire_drake

Default: one front-3/4 Idle cell per enemy id in Resources/Data/enemies.json, labelled "<id> - <source>".
--actions: one row per id with Idle / Attack (40 % impact) / Cast (60 % release) / Hit / Die (last frame).
Workbench, vertex colours (Col), studio light + outline: a quick toon-ish look, not the Unity shader.
Composition uses only bpy + numpy (no PIL), so it runs in a stock Blender.
"""
import argparse
import json
import math
import os
import sys
import tempfile

import bpy
import numpy as np
from mathutils import Euler, Vector

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import cc0_monsters as C  # noqa: E402
import specs  # noqa: E402

A = C.A
ACTION_COLS = (("Idle", 0.0), ("Attack", 0.40), ("Cast", 0.60), ("Hit", 0.5), ("Die", 1.0))


def label_for(eid):
    if eid in specs.SPECS:
        src = os.path.splitext(specs.SPECS[eid]["source"])[0]
        pack = "Quaternius" if src.startswith("quaternius") else "KayKit"
        return f"{eid}  [{pack} {src.split('/')[-1]}]"
    return f"{eid}  [procedural]"


def load(eid, root=None):
    bpy.ops.wm.read_factory_settings(use_empty=True)
    sc = bpy.context.scene
    sc.render.fps = A.FPS
    bpy.ops.import_scene.fbx(filepath=os.path.join(root or os.path.join(A.ASSETS, "Enemies"), eid, f"{eid}.fbx"))
    rig = next(o for o in sc.objects if o.type == "ARMATURE")
    body = [o for o in sc.objects if o.type == "MESH"]
    takes = {a.name.split("|")[-1]: a for a in bpy.data.actions}
    return rig, body, takes


def pose(rig, act, frac):
    C.assign_action(rig, act)
    f0, f1 = act.frame_range
    bpy.context.scene.frame_set(int(round(f0 + (f1 - f0) * frac)))


def bounds(meshes):
    dg = bpy.context.evaluated_depsgraph_get()
    lo = Vector((1e9,) * 3)
    hi = Vector((-1e9,) * 3)
    for o in meshes:
        oe = o.evaluated_get(dg)
        me = oe.to_mesh()
        for v in me.vertices:
            w = oe.matrix_world @ v.co
            lo = Vector(map(min, lo, w))
            hi = Vector(map(max, hi, w))
        oe.to_mesh_clear()
    return lo, hi


def shoot(path, box, size, note, angle=(76, 0, 22)):
    sc = bpy.context.scene
    lo, hi = box
    center = (lo + hi) / 2
    radius = max((hi - lo).length / 2, 0.2)
    cam = bpy.data.objects.get("SheetCam")
    if cam is None:
        cam = bpy.data.objects.new("SheetCam", bpy.data.cameras.new("SheetCam"))
        sc.collection.objects.link(cam)
    cam.data.lens = 50
    e = Euler([math.radians(a) for a in angle])
    cam.location = center + (e.to_matrix() @ Vector((0, 0, 1))) * radius * 2.9
    cam.rotation_euler = e
    sc.camera = cam
    C.setup_look(sc)
    r = sc.render
    r.resolution_x = r.resolution_y = size
    r.resolution_percentage = 100
    for attr in dir(r):
        if attr.startswith("use_stamp_"):
            try:
                setattr(r, attr, False)
            except (AttributeError, TypeError):
                pass
    r.use_stamp = bool(note)
    r.use_stamp_note = True
    r.stamp_note_text = note
    r.stamp_font_size = max(12, size // 22)
    r.stamp_foreground = (1, 1, 1, 1)
    r.stamp_background = (0.05, 0.05, 0.08, 0.75)
    r.image_settings.file_format = "PNG"
    r.filepath = path
    bpy.ops.render.render(write_still=True)


def compose(cells, cols, size, out):
    rows = (len(cells) + cols - 1) // cols
    W, H = cols * size, rows * size
    sheet = np.zeros((H, W, 4), dtype=np.float32)
    sheet[..., :3] = 0.1
    sheet[..., 3] = 1
    for i, path in enumerate(cells):
        img = bpy.data.images.load(path)
        px = np.empty(size * size * 4, dtype=np.float32)
        img.pixels.foreach_get(px)
        px = px.reshape(size, size, 4)
        r, c = divmod(i, cols)
        y0 = H - (r + 1) * size            # Blender images start at the bottom row
        sheet[y0:y0 + size, c * size:(c + 1) * size] = px
        bpy.data.images.remove(img)
    im = bpy.data.images.new("sheet", W, H, alpha=False)
    im.pixels.foreach_set(sheet.ravel())
    im.filepath_raw = out
    im.file_format = "PNG"
    os.makedirs(os.path.dirname(os.path.abspath(out)), exist_ok=True)
    im.save()
    return out


def main():
    argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", required=True)
    ap.add_argument("--ids", nargs="+")
    ap.add_argument("--cols", type=int, default=7)
    ap.add_argument("--cell", type=int, default=320)
    ap.add_argument("--actions", action="store_true")
    ap.add_argument("--fbx-dir", help="folder holding <id>/<id>.fbx (default: Resources/Art/Enemies)")
    ap.add_argument("--no-source-label", action="store_true", help="label cells with the id only")
    o = ap.parse_args(argv)
    ids = o.ids
    if not ids:
        with open(os.path.join(A.REPO, "Assets/_Game/Resources/Data/enemies.json"), encoding="utf-8") as fh:
            ids = sorted(row["id"] for row in json.load(fh))
    tmp = tempfile.mkdtemp(prefix="abyss_sheet_")
    cells = []
    for eid in ids:
        rig, meshes, takes = load(eid, o.fbx_dir)
        if o.actions:
            boxes = []
            for name, frac in ACTION_COLS:
                pose(rig, takes[name], frac)
                boxes.append(bounds(meshes))
            lo = Vector(map(min, *[b[0] for b in boxes]))
            hi = Vector(map(max, *[b[1] for b in boxes]))
            for name, frac in ACTION_COLS:
                pose(rig, takes[name], frac)
                p = os.path.join(tmp, f"{eid}_{name}.png")
                f0, f1 = takes[name].frame_range
                shoot(p, (lo, hi), o.cell, f"{eid}  {name} f{int(round((f1 - f0) * frac))}/{int(f1 - f0)}")
                cells.append(p)
        else:
            pose(rig, takes["Idle"], 0.0)
            p = os.path.join(tmp, f"{eid}.png")
            shoot(p, bounds(meshes), o.cell, eid if o.no_source_label else label_for(eid))
            cells.append(p)
        print("SHOT", eid, flush=True)
    cols = len(ACTION_COLS) if o.actions else o.cols
    print("SHEET", compose(cells, cols, o.cell, o.out), flush=True)


if __name__ == "__main__":
    main()
