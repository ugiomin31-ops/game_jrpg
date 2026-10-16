"""Install Tripo Studio exports of the verdant_ruins briefed pieces (see ArtSource/_briefs/environment.md).

    blender -b --factory-startup -P Blender/environment/verdant_ruins/install_tripo.py -- --src DIR --out DIR [--only a,b]

--src holds one Tripo FBX export per piece at <src>/<piece>/tripo/**/*.fbx (with its .fbm textures), as dropped on the
tripo-glb-drop branch. Each piece is uniformly scaled to its target size, re-based (base centre at the origin, front
-Y), given one material M_Verdant<Piece>_Tripo with <piece>_tex/<material>.png (base colour, 1024), and written to
<out>/<piece>.fbx plus a <piece>.tripo marker. Special parts follow the old procedural pieces: chest Lid on its back
hinge, trap Spikes retracted below the plate, and the LightAnchor*/Spot_* empties. --out may be the installed
Art/Environment/verdant_ruins folder: existing .fbx.meta files are left alone.
"""
import argparse
import glob
import math
import os
import sys

import bmesh
import bpy
from mathutils import Matrix, Vector

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "..", "lib"))
import abyss_bpy as A  # noqa: E402

TEX_SIZE = 1024

# fit: ("xy", m) largest horizontal side, ("x", m) width, ("h", m) height.
PIECES = {
    "decor_1": dict(fit=("xy", 1.4)),
    "decor_2": dict(fit=("xy", 1.6)),
    "decor_3": dict(fit=("xy", 1.6)),
    "decor_4": dict(fit=("h", 1.3)),
    "decor_5": dict(fit=("xy", 1.8)),
    "decor_6": dict(fit=("h", 1.2)),
    "chest": dict(fit=("x", 1.3), lid_seam=0.40),
    "lore_stone": dict(fit=("h", 2.0)),
    "spring": dict(fit=("xy", 2.2), empties={"LightAnchor_spring": (0, 0, 1.2)}),
    # spawned 1.7 m from the cell centre toward a wall (0.3 m from its face), +Y toward the wall
    "torch": dict(fit=("h", 1.8), back_y=0.28, empties={"LightAnchor": "flame"}),
    "trap": dict(fit=("xy", 2.4), spikes=True, slab_top=0.14),
    # walked through at eye height 1.35 m: stones kept under 1 m so the camera passes over them
    "warp": dict(fit=("xy", 3.0), max_h=1.0, empties={"Spot_warp": (0, 0, 0), "LightAnchor_warp": (0, 0, 0.8)}),
    "foe_marker": dict(fit=("xy", 2.0), empties={"Spot_foe": (0, 0, 0)}),
    # wall decals: flat back on y = -2.0, hugging the -Y face of a wall block, up to 4.4 m tall
    # Tripo modelled whole mossy wall panels (stone face + ivy or roots), so both stand on the floor as facades
    "overlay_1": dict(overlay=True, width=3.9, anchor="floor"),
    "overlay_2": dict(overlay=True, width=3.9, anchor="floor"),
}


def camel(piece):
    return "".join(p.capitalize() for p in piece.split("_"))


def find_export(src, piece):
    hits = sorted(glob.glob(os.path.join(src, piece, "tripo", "**", "*.fbx"), recursive=True))
    if not hits:
        raise SystemExit(f"{piece}: no FBX under {src}/{piece}/tripo")
    return hits[0]


def base_color(path):
    hits = glob.glob(os.path.join(os.path.dirname(path), "**", "*basecolor*"), recursive=True)
    hits += glob.glob(os.path.join(os.path.dirname(path), "**", "*_BaseColor*"), recursive=True)
    if not hits:
        raise SystemExit(f"no base colour texture next to {path}")
    return hits[0]


def import_mesh(path):
    bpy.ops.wm.read_factory_settings(use_empty=True)
    bpy.ops.import_scene.fbx(filepath=path)
    meshes = [o for o in bpy.context.scene.objects if o.type == "MESH"]
    bpy.context.view_layer.update()
    bm = bmesh.new()
    for o in meshes:
        tmp = bmesh.new()
        tmp.from_mesh(o.data)
        tmp.transform(o.matrix_world)
        m = bpy.data.meshes.new("tmp")
        tmp.to_mesh(m)
        tmp.free()
        bm.from_mesh(m)
    for o in list(bpy.context.scene.objects):
        bpy.data.objects.remove(o, do_unlink=True)
    bmesh.ops.remove_doubles(bm, verts=bm.verts, dist=1e-5)
    bmesh.ops.triangulate(bm, faces=[f for f in bm.faces if len(f.verts) > 3])
    return bm


def bounds(verts):
    lo = Vector([min(v.co[i] for v in verts) for i in range(3)])
    hi = Vector([max(v.co[i] for v in verts) for i in range(3)])
    return lo, hi


def fit_scale(bm, fit):
    lo, hi = bounds(bm.verts)
    size = hi - lo
    axis, target = fit
    cur = {"xy": max(size.x, size.y), "x": size.x, "h": size.z}[axis]
    s = target / cur
    bmesh.ops.scale(bm, vec=(s, s, s), verts=bm.verts)
    lo, hi = bounds(bm.verts)
    bmesh.ops.translate(bm, vec=(-(lo.x + hi.x) / 2, -(lo.y + hi.y) / 2, -lo.z), verts=bm.verts)
    return s


def material(piece, out_dir, src_png):
    name = f"M_Verdant{camel(piece)}_Tripo"
    tdir = os.path.join(out_dir, piece + "_tex")
    os.makedirs(tdir, exist_ok=True)
    png = os.path.join(tdir, name + ".png")
    img = bpy.data.images.load(src_png)
    if max(img.size) != TEX_SIZE:
        img.scale(TEX_SIZE, TEX_SIZE)
    img.filepath_raw = png
    img.file_format = "PNG"
    img.save()
    img = bpy.data.images.load(png, check_existing=False)
    mat = bpy.data.materials.new(name)
    mat.use_nodes = True
    nt = mat.node_tree
    tex = nt.nodes.new("ShaderNodeTexImage")
    tex.image = img
    bsdf = nt.nodes.get("Principled BSDF")
    nt.links.new(tex.outputs["Color"], bsdf.inputs["Base Color"])
    bsdf.inputs["Roughness"].default_value = 0.9
    return mat


def to_object(name, bm, mat, origin=(0, 0, 0)):
    bmesh.ops.translate(bm, vec=-Vector(origin), verts=bm.verts)
    me = bpy.data.meshes.new(name)
    bm.to_mesh(me)
    for f in me.polygons:
        f.use_smooth = True
    me.materials.append(mat)
    o = bpy.data.objects.new(name, me)
    o.location = origin
    bpy.context.scene.collection.objects.link(o)
    return o


def split(bm, pred):
    """Return (rest, part): two bmeshes, `part` holding the faces whose centroid satisfies pred."""
    part = bm.copy()
    bmesh.ops.delete(part, geom=[f for f in part.faces if not pred(f.calc_center_median())], context="FACES")
    bmesh.ops.delete(bm, geom=[f for f in bm.faces if pred(f.calc_center_median())], context="FACES")
    for b in (bm, part):
        bmesh.ops.delete(b, geom=[v for v in b.verts if not v.link_faces], context="VERTS")
    return bm, part


def empty(name, loc):
    e = bpy.data.objects.new(name, None)
    e.location = loc
    bpy.context.scene.collection.objects.link(e)
    return e


def install(piece, src, out_dir, log):
    cfg = PIECES[piece]
    path = find_export(src, piece)
    bm = import_mesh(path)
    raw_tris = len(bm.faces)
    mat = material(piece, out_dir, base_color(path))
    objs, note = [], []
    if cfg.get("overlay"):
        s = overlay(bm, note, cfg)
    else:
        s = fit_scale(bm, cfg["fit"])
    lo, hi = bounds(bm.verts)
    if "max_h" in cfg and hi.z > cfg["max_h"]:
        k = cfg["max_h"] / hi.z
        bmesh.ops.scale(bm, vec=(1, 1, k), verts=bm.verts)
        note.append(f"height squashed x{k:.2f} to {cfg['max_h']} m")
        lo, hi = bounds(bm.verts)
    if "back_y" in cfg:
        bmesh.ops.translate(bm, vec=(0, cfg["back_y"] - hi.y, 0), verts=bm.verts)
        lo, hi = bounds(bm.verts)
    if "lid_seam" in cfg:
        seam = cfg["lid_seam"] * s
        body, lid = split(bm, lambda c: c.z > seam)
        blo, bhi = bounds(body.verts)
        hinge = (0.0, bhi.y, seam)
        objs.append(to_object(piece, body, mat))
        objs.append(to_object("Lid", lid, mat, origin=hinge))
        note.append(f"Lid split at z {seam:.3f}, hinge {tuple(round(v, 3) for v in hinge)}")
    elif cfg.get("spikes"):
        objs += trap(bm, mat, piece, note, s, cfg)
    else:
        objs.append(to_object(piece, bm, mat))
    for name, loc in cfg.get("empties", {}).items():
        if loc == "flame":
            loc = flame_anchor(objs[0])
        objs.append(empty(name, loc))
        note.append(f"{name} at {tuple(round(v, 2) for v in loc)}")
    bpy.context.view_layer.update()
    tris = sum(len(o.data.polygons) for o in objs if o.type == "MESH")
    fbx = os.path.join(out_dir, piece + ".fbx")
    A.export_fbx(fbx, objects=objs, path_mode="RELATIVE", force=True)
    with open(os.path.join(out_dir, piece + ".tripo"), "w", encoding="utf-8") as fh:
        fh.write("Tripo Studio export, cleaned in Blender by Blender/environment/verdant_ruins/install_tripo.py on "
                 f"2026-10-16. Source: ArtSource/terrain/verdant_ruins/{piece}/candidates/prompts.md\n")
    size = hi - lo
    line = (f"{piece}.fbx: uniform x{s:.3f}, {size.x:.2f} x {size.y:.2f} x {size.z:.2f} m, {tris} tris (Tripo {raw_tris}), "
            f"material {mat.name}" + ("; " + "; ".join(note) if note else ""))
    log.append(line)
    print("[install]", line, flush=True)


def flame_anchor(obj):
    vs = [obj.matrix_world @ v.co for v in obj.data.vertices]
    top = max(v.z for v in vs)
    crown = [v for v in vs if v.z > top - 0.25]
    c = sum(crown, Vector()) / len(crown)
    return (round(c.x, 3), round(c.y, 3), round(top - 0.2, 3))


def trap(bm, mat, piece, note, scale, cfg):
    """Floor slab sunk so its top sits at +0.04 m (old plate height); the thorn cluster above it becomes Spikes,
    squashed to 60 % height and retracted 0.5 m below its rest position like the old moving spike part."""
    seam = cfg["slab_top"] * scale
    bmesh.ops.translate(bm, vec=(0, 0, 0.04 - seam), verts=bm.verts)
    plate, spikes = split(bm, lambda c: c.z > 0.04)
    bmesh.ops.scale(spikes, vec=(1, 1, 0.6), space=Matrix.Translation((0, 0, -0.04)), verts=spikes.verts)
    objs = [to_object(piece, plate, mat)]
    sp = to_object("Spikes", spikes, mat)
    sp.location.z -= 0.5
    objs.append(sp)
    note.append(f"slab top at +0.04 m (sunk {seam - 0.04:.2f} m); Spikes = faces above it, height x0.6, retracted 0.5 m")
    return objs


def overlay(bm, note, cfg):
    """Flat-backed wall decal: fit to cfg width (<= 4.3 m tall), back plane on y = -2.0, relief <= 0.3 m.
    anchor "floor" stands it on z = 0, "top" hangs it from the wall top at z = 4.4."""
    lo, hi = bounds(bm.verts)
    size = hi - lo
    # Tripo stands the panel upright facing -Y; its thinnest horizontal side is the relief depth.
    s = min(cfg["width"] / size.x, 4.3 / size.z)
    bmesh.ops.scale(bm, vec=(s, s, s), verts=bm.verts)
    lo, hi = bounds(bm.verts)
    depth = hi.y - lo.y
    if depth > 0.3:
        k = 0.3 / depth
        bmesh.ops.scale(bm, vec=(1, k, 1), verts=bm.verts)
        note.append(f"relief squashed x{k:.2f}")
        lo, hi = bounds(bm.verts)
    dz = -lo.z if cfg["anchor"] == "floor" else 4.4 - hi.z
    bmesh.ops.translate(bm, vec=(-(lo.x + hi.x) / 2, -2.0 - hi.y, dz), verts=bm.verts)
    note.append(f"wall decal, back on y -2.0, anchored at the {cfg['anchor']}")
    return s


def main():
    argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
    ap = argparse.ArgumentParser()
    ap.add_argument("--src", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--only")
    opt = ap.parse_args(argv)
    os.makedirs(opt.out, exist_ok=True)
    pieces = opt.only.split(",") if opt.only else [p for p in PIECES if os.path.isdir(os.path.join(opt.src, p))]
    log = []
    for p in pieces:
        install(p, os.path.abspath(opt.src), os.path.abspath(opt.out), log)
    with open(os.path.join(opt.out, "install_log.txt"), "a", encoding="utf-8") as fh:
        fh.write("\n".join(log) + "\n")


if __name__ == "__main__":
    main()
