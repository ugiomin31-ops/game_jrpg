"""Shared helpers for the enemies_b group (ember + undead families).

Builds on Blender/lib/abyss_bpy.py (read-only shared lib). Adds:
- shape helpers (rock, flame, leaf, plates, orient-on-normal),
- a procedural action builder (`act`) whose rotations/locations are given in ARMATURE-space axes
  (X = character's left, -Y = forward, Z = up) and converted to bone-local channels,
- `finish()` = skin -> action check -> FBX export -> .blend -> previews -> contact sheet -> FBX re-import check.
"""
import math
import os
import random
import sys

sys.path.append(os.path.join(os.path.dirname(os.path.abspath(__file__)), '../lib'))
import abyss_bpy as A  # noqa: E402

import bmesh  # noqa: E402
import bpy  # noqa: E402
from mathutils import Euler, Matrix, Vector, noise  # noqa: E402

ACTIONS = ("Idle", "Run", "Attack", "Cast", "Hit", "Die", "Victory")
TAU = math.tau


# ---------------------------------------------------------------- colour

def rgb(c):
    return A._as_rgba(c)


def mix(a, b, t):
    a, b = rgb(a), rgb(b)
    return tuple(a[i] * (1 - t) + b[i] * t for i in range(4))


def shade(c, k):
    """k < 1 darkens, k > 1 lightens towards white."""
    c = rgb(c)
    if k <= 1:
        return (c[0] * k, c[1] * k, c[2] * k, c[3])
    t = min(k - 1, 1)
    return mix(c, (1, 1, 1, 1), t)


def vgrad(obj, stops, axis=2):
    """Multi-stop gradient along a local axis. stops: [(t, colour), ...] with t in 0..1."""
    stops = [(t, rgb(c)) for t, c in stops]
    me = obj.data
    if "Col" not in me.color_attributes:
        me.color_attributes.new("Col", "BYTE_COLOR", "CORNER")
    attr = me.color_attributes["Col"]
    vs = [v.co[axis] for v in me.vertices]
    lo, hi = min(vs), max(vs)
    span = max(hi - lo, 1e-6)
    for loop in me.loops:
        t = (me.vertices[loop.vertex_index].co[axis] - lo) / span
        c = stops[-1][1]
        for (t0, c0), (t1, c1) in zip(stops, stops[1:]):
            if t <= t1:
                k = (t - t0) / max(t1 - t0, 1e-6)
                k = min(max(k, 0), 1)
                c = tuple(c0[i] * (1 - k) + c1[i] * k for i in range(4))
                break
        if t <= stops[0][0]:
            c = stops[0][1]
        attr.data[loop.index].color_srgb = c
    return obj


def paint_where(obj, fn, color):
    """Recolour face corners whose face centre (local) satisfies fn(center, normal)."""
    me = obj.data
    attr = me.color_attributes["Col"]
    col = rgb(color)
    for p in me.polygons:
        if fn(p.center, p.normal):
            for li in p.loop_indices:
                attr.data[li].color_srgb = col
    return obj


# ---------------------------------------------------------------- shapes

def orient_z(obj, direction, roll=0.0):
    """Rotate obj so its local +Z points along direction (world)."""
    d = Vector(direction).normalized()
    q = Vector((0, 0, 1)).rotation_difference(d)
    if roll:
        q = q @ Euler((0, 0, math.radians(roll))).to_quaternion()
    obj.rotation_mode = "XYZ"
    obj.rotation_euler = q.to_euler()
    return obj


def rock(name, size, loc=(0, 0, 0), rot=(0, 0, 0), color="#888888", seed=0, amp=0.18, bevel=0.3, mat="M_Toon", freq=2.2):
    """Chunky bevelled stone with noise; size = (x, y, z)."""
    m = min(size)
    o = A.box(name, size=size, loc=(0, 0, 0), color=color, mat=mat, bevel=m * bevel, seg=2)
    off = Vector((seed * 3.17, seed * 1.91, seed * 2.53))
    s = Vector(size)

    def f(v):
        n = noise.noise_vector(Vector((v.x / s.x, v.y / s.y, v.z / s.z)) * freq + off)
        return v + Vector((n.x * s.x, n.y * s.y, n.z * s.z)) * amp
    A.deform(o, f)
    A._place(o, loc, rot, 1)
    A.shade_smooth(o, angle=40)
    return o


def flame(name, h=0.4, r=0.1, loc=(0, 0, 0), rot=(0, 0, 0), curl=(0.0, 0.0), stops=None, mat="M_Emit", seg=12, wave=0.0, scale=(1, 1, 1)):
    """Teardrop flame tongue along +Z, tip bent by curl=(dx, dy) * h (quadratic)."""
    prof = [(0.0, -0.02 * h), (r * 0.55, 0.0), (r * 0.95, 0.12 * h), (r, 0.28 * h), (r * 0.8, 0.5 * h),
            (r * 0.45, 0.74 * h), (r * 0.16, 0.92 * h), (0.0, h)]
    o = A.lathe(name, prof, loc=(0, 0, 0), color="#ffffff", mat=mat, seg=seg)

    def f(v):
        t = max(v.z / h, 0)
        return Vector((v.x + curl[0] * h * t * t + wave * h * math.sin(t * 5) * t, v.y + curl[1] * h * t * t, v.z))
    A.deform(o, f)
    vgrad(o, stops or [(0, "#ffe060"), (0.5, "#ff9020"), (1, "#e03010")])
    A._place(o, loc, rot, scale)
    return o


def leaf(name, length=0.3, width=0.1, depth=0.02, loc=(0, 0, 0), rot=(0, 0, 0), color="#888888", mat="M_Toon", n=8, tip=1.0, base=0.15, jag=0.0, scale=(1, 1, 1), stops=None):
    """Leaf / feather / blade outline along +Z in the XZ plane (extruded on Y)."""
    pts_r, pts_l = [], []
    for i in range(n + 1):
        t = i / n
        w = width * math.sin(math.pi * (base + (1 - base) * t) ** tip) * (1 - 0.0 * t)
        j = jag * width * (1 if i % 2 else -0.3) if 0 < i < n else 0
        pts_r.append((w / 2 + j, t * length))
        pts_l.append((-w / 2 - j, t * length))
    pts = pts_r + list(reversed(pts_l))[1:-1]
    # dedupe tip
    clean = []
    for p in pts:
        if not clean or (abs(clean[-1][0] - p[0]) + abs(clean[-1][1] - p[1])) > 1e-5:
            clean.append(p)
    o = A.extrude_shape(name, clean, depth=depth, loc=(0, 0, 0), color=color, mat=mat)
    if stops:
        vgrad(o, stops)
    A._place(o, loc, rot, scale)
    return o


def spike(name, r=0.05, h=0.2, loc=(0, 0, 0), direction=(0, 0, 1), color="#222222", mat="M_Toon", seg=8, bend=0.0, bend_dir=(0, -1, 0)):
    o = A.cone(name, r=r, depth=h, loc=(0, 0, 0), color=color, mat=mat, seg=seg)
    A.deform(o, lambda v: Vector((v.x, v.y, v.z + h / 2)))
    if bend:
        bd = Vector(bend_dir)
        A.deform(o, lambda v: v + bd * bend * h * (v.z / h) ** 2)
    o.location = loc
    orient_z(o, direction)
    return o


def claw(name, r=0.03, length=0.12, loc=(0, 0, 0), direction=(0, -1, 0), curl=0.5, color="#1a1414"):
    """Curved talon: cone bent downward along its length."""
    o = A.cone(name, r=r, depth=length, loc=(0, 0, 0), color=color, seg=8)
    A.deform(o, lambda v: Vector((v.x, v.y, v.z + length / 2)))
    A.deform(o, lambda v: Vector((v.x, v.y + curl * length * (v.z / length) ** 2, v.z)))
    o.location = loc
    orient_z(o, direction)
    return o


def ring_band(name, r_bot, r_top, z0, z1, loc=(0, 0, 0), color="#888888", mat="M_Toon", seg=24, scale=(1, 1, 1), rot=(0, 0, 0)):
    """Open-ended band (short truncated cone shell) for trims and bracelets."""
    return A.lathe(name, [(r_bot, z0), (r_top, z1)], loc=loc, rot=rot, color=color, mat=mat, seg=seg, scale=scale)


def plate(name, radius=0.1, thick=0.03, loc=(0, 0, 0), normal=(0, 0, 1), color="#888888", seed=0, sides=7, jitter=0.25,
          dome=0.0, bevel=0.35, mat="M_Toon", stretch=(1, 1), roll=0.0, top_color=None):
    """Irregular polygon slab (crust plate / armour stone / scale). Built in XY, thickness along +Z, then its +Z is
    aimed along `normal` and placed at loc (the slab's underside sits on loc). dome bends it to hug a curved surface
    of radius 1/dome."""
    rnd = random.Random(seed)
    bm = bmesh.new()
    vs = []
    for i in range(sides):
        a = TAU * (i + rnd.uniform(-0.2, 0.2)) / sides
        r = radius * (1 + rnd.uniform(-jitter, jitter))
        vs.append(bm.verts.new((math.cos(a) * r * stretch[0], math.sin(a) * r * stretch[1], 0)))
    f = bm.faces.new(vs)
    ext = bmesh.ops.extrude_face_region(bm, geom=[f])
    top = [e for e in ext["geom"] if isinstance(e, bmesh.types.BMVert)]
    bmesh.ops.translate(bm, verts=top, vec=(0, 0, thick))
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    o = A._from_bmesh(name, bm)
    md = o.modifiers.new("bevel", "BEVEL")
    md.width = min(thick * bevel * 1.6, radius * 0.3)
    md.segments = 2
    md.limit_method = "ANGLE"
    A.apply_modifiers(o)
    md = o.modifiers.new("sub", "SUBSURF")
    md.levels = 1
    A.apply_modifiers(o)
    if dome:
        A.deform(o, lambda v: Vector((v.x, v.y, v.z - dome * 0.5 * (v.x * v.x + v.y * v.y))))
    A.paint(o, color, mat)
    if top_color:
        paint_where(o, lambda c, n: n.z > 0.75, top_color)
    o.location = loc
    orient_z(o, normal, roll)
    A.shade_smooth(o, angle=40)
    return o


def tris(o):
    return sum(len(p.vertices) - 2 for p in o.data.polygons)


# ---------------------------------------------------------------- animation

def _ease(k, mode):
    if mode == "l":
        return k
    if mode == "i":
        return k * k
    if mode == "o":
        return 1 - (1 - k) * (1 - k)
    if mode == "o3":
        return 1 - (1 - k) ** 3
    if mode == "s":  # step-ish hold then snap
        return 0 if k < 1 else 1
    return k * k * (3 - 2 * k)


def kf(f, keys):
    """Evaluate keyposes at frame f. keys: [(frame, (x,y,z)) or (frame, (x,y,z), ease)], ease applies to the
    segment ENDING at that key ('io' default, 'o' ease-out/snappy, 'i' accelerate, 'l' linear). Scalars allowed."""
    def V(x):
        return Vector(x) if hasattr(x, "__len__") else Vector((x, x, x))
    if f <= keys[0][0]:
        return V(keys[0][1])
    for a, b in zip(keys, keys[1:]):
        if f <= b[0]:
            k = (f - a[0]) / max(b[0] - a[0], 1e-6)
            k = _ease(k, b[2] if len(b) > 2 else "io")
            return V(a[1]).lerp(V(b[1]), k)
    return V(keys[-1][1])


def sw(f, period, phase=0.0):
    """Sine wave at frame f with a period in frames; phase in cycles (0..1)."""
    return math.sin(TAU * (f / period + phase))


def _bone_axes(rig):
    return {b.name: b.matrix_local.to_3x3() for b in rig.data.bones}


def act(rig, name, length, tracks, step=1):
    """Create an action. tracks = {bone: {"rot": spec, "loc": spec, "scl": spec}} where spec is a keylist
    for kf() or a callable f -> (x, y, z). Rotation in degrees about armature axes (XYZ order), location in
    armature-space metres, scale in armature axes. Bones without tracks get rest keys."""
    B = _bone_axes(rig)
    with A.Anim(rig, name, length) as a:
        for bone, ch in tracks.items():
            M = B[bone]
            Mi = M.inverted()
            perm = [max(range(3), key=lambda j: abs(M.col[i][j])) for i in range(3)]
            last = Euler()
            frames = list(range(0, length + 1, step))
            if frames[-1] != length:
                frames.append(length)
            for f in frames:
                pb = rig.pose.bones[bone]
                if "rot" in ch:
                    spec = ch["rot"]
                    d = spec(f) if callable(spec) else kf(f, spec)
                    Rw = Euler([math.radians(x) for x in d], "XYZ").to_matrix()
                    e = (Mi @ Rw @ M).to_euler("XYZ", last)
                    last = e
                    pb.rotation_euler = e
                    pb.keyframe_insert("rotation_euler", frame=f)
                if "loc" in ch:
                    spec = ch["loc"]
                    d = Vector(spec(f) if callable(spec) else kf(f, spec))
                    pb.location = Mi @ d
                    pb.keyframe_insert("location", frame=f)
                if "scl" in ch:
                    spec = ch["scl"]
                    d = spec(f) if callable(spec) else kf(f, spec)
                    if not hasattr(d, "__len__"):
                        d = (d, d, d)
                    pb.scale = [d[perm[i]] for i in range(3)]
                    pb.keyframe_insert("scale", frame=f)
    return bpy.data.actions[name]


def add(*vs):
    out = Vector((0, 0, 0))
    for v in vs:
        out += Vector(v)
    return out


# ---------------------------------------------------------------- output

def _sheet(paths, out, cols=4):
    imgs = [bpy.data.images.load(p, check_existing=False) for p in paths if os.path.exists(p)]
    if not imgs:
        return
    import numpy as np
    w, h = imgs[0].size
    rows = (len(imgs) + cols - 1) // cols
    canvas = np.full((rows * h, cols * w, 4), 0.05, dtype=np.float32)
    canvas[..., 3] = 1.0
    for i, im in enumerate(imgs):
        px = np.empty(w * h * 4, dtype=np.float32)
        im.pixels.foreach_get(px)
        px = px.reshape(h, w, 4)
        r, c = divmod(i, cols)
        y0 = (rows - 1 - r) * h
        canvas[y0:y0 + h, c * w:(c + 1) * w] = px
    sh = bpy.data.images.new("sheet", cols * w, rows * h, alpha=True)
    sh.pixels.foreach_set(canvas.ravel())
    sh.filepath_raw = out
    sh.file_format = "PNG"
    sh.save()
    for im in imgs:
        bpy.data.images.remove(im)
    bpy.data.images.remove(sh)


def finish(eid, rig, parts_by_bone, size=420, extra=(), zoom=2.7):
    """Skin, verify actions, export FBX, save .blend, render previews + contact sheet, re-import check."""
    body = A.skin(parts_by_bone, rig)
    A.volume_shade(body)  # same grounded, solid read as the heroes
    missing = [n for n in ACTIONS if n not in bpy.data.actions]
    if missing:
        raise RuntimeError(f"{eid}: missing actions {missing}")
    mats = [m.name for m in body.data.materials]
    bad = [m for m in mats if m not in A.MATERIALS]
    if bad:
        raise RuntimeError(f"{eid}: bad materials {bad}")
    lo = [min((body.matrix_world @ v.co)[i] for v in body.data.vertices) for i in range(3)]
    hi = [max((body.matrix_world @ v.co)[i] for v in body.data.vertices) for i in range(3)]
    print(f"[{eid}] tris={tris(body)} mats={mats} bbox lo={[round(x, 2) for x in lo]} hi={[round(x, 2) for x in hi]}")
    dist = (Vector(hi) - Vector(lo)).length / 2 * zoom
    path = A.export_fbx(f"Enemies/{eid}/{eid}.fbx", objects=[rig, body], animated=True)
    A.save_blend(f"enemy_{eid}")
    shots = [(f"enemy_{eid}", (72, 0, 32), None, None),
             (f"enemy_{eid}_side", (80, 0, 90), None, None),
             (f"enemy_{eid}_back", (68, 0, 160), None, None)]
    L = lambda n: int(bpy.data.actions[n].frame_range[1])  # noqa: E731
    shots += [(f"enemy_{eid}_attack", (75, 0, 40), "Attack", round(L("Attack") * 0.4)),
              (f"enemy_{eid}_attack0", (75, 0, 40), "Attack", round(L("Attack") * 0.2)),
              (f"enemy_{eid}_cast", (72, 0, 32), "Cast", round(L("Cast") * 0.6)),
              (f"enemy_{eid}_run", (75, 0, 60), "Run", round(L("Run") * 0.25)),
              (f"enemy_{eid}_hit", (72, 0, 32), "Hit", round(L("Hit") * 0.35)),
              (f"enemy_{eid}_die", (60, 0, 40), "Die", L("Die")),
              (f"enemy_{eid}_victory", (72, 0, 32), "Victory", round(L("Victory") * 0.5))]
    shots += list(extra)
    paths = []
    for nm, ang, action, frame in shots:
        paths.append(A.render_preview(nm, objects=[body], angle=ang, size=size, action=action, frame=frame, dist=dist))
    bpy.context.scene.frame_set(0)
    _sheet(paths, os.path.join(A.PREVIEW_DIR, f"enemy_{eid}_sheet.png"), cols=4)
    # re-import check
    bpy.ops.wm.read_factory_settings(use_empty=True)
    bpy.ops.import_scene.fbx(filepath=path)
    takes = sorted(a.name for a in bpy.data.actions)
    names = sorted(o.name for o in bpy.context.scene.objects)
    print(f"[{eid}] FBX OK {os.path.getsize(path)} bytes objects={names} takes={takes}")
    return path


def new_rig(bones):
    """bones: list of (name, head, tail, parent). Wrapper so scripts read uniformly."""
    return A.armature(bones)
