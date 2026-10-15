"""Shared helpers for the boss generators (forest_guardian, frost_kraken, flame_sphinx, boss).

Builds on Blender/lib/abyss_bpy.py (read-only shared lib). Adds:
- per-face procedural painting (moss on up-facing faces, lava cracks, two-tone tentacles) with
  optional per-face material (M_Toon / M_Emit / M_Clear),
- swept tubes with known frames (tentacles, roots, tails, branches),
- smooth chain skinning for secondary-motion chains (tentacles, tails, cloth strips, vines),
- a procedural pose/bake animation system: every action is a function frame -> pose, keys are
  written in armature-space axes (+X rot = pitch forward/down for up-pointing bones, +Z rot = turn
  toward the character's left (+X), +Y rot = roll toward +X),
- finish(): action check, FBX export, .blend save and preview renders.
"""
import math
import os
import random
import sys

sys.path.append(r"C:\Users\User\Desktop\game\Blender\lib")
import abyss_bpy as A  # noqa: E402

import bmesh  # noqa: E402
import bpy  # noqa: E402
from mathutils import Euler, Matrix, Vector, noise  # noqa: E402

TAU = math.pi * 2


def V(x, y=None, z=None):
    if y is None:
        return Vector(x)
    return Vector((x, y, z))


def rgba(c):
    return A._as_rgba(c)


def mix(c1, c2, t):
    a, b = rgba(c1), rgba(c2)
    t = max(0.0, min(1.0, t))
    return tuple(a[i] * (1 - t) + b[i] * t for i in range(4))


def clamp(x, lo=0.0, hi=1.0):
    return max(lo, min(hi, x))


def smooth(t):
    t = clamp(t)
    return t * t * (3 - 2 * t)


def nz(p, seed=0.0, freq=1.0):
    """Perlin noise in [-1, 1]."""
    return noise.noise(Vector(p) * freq + Vector((seed * 13.1, seed * 7.7, seed * 3.3)))


# ---------------------------------------------------------------- painting

def world_faces(obj):
    """Yield (poly, world_center, world_normal) for each polygon."""
    bpy.context.view_layer.update()
    mw = obj.matrix_world
    nm = mw.to_3x3().inverted().transposed()
    for p in obj.data.polygons:
        yield p, mw @ p.center, (nm @ p.normal).normalized()


def paint_faces(obj, fn):
    """fn(world_center, world_normal, poly) -> colour | (colour, material_name). One colour per face."""
    me = obj.data
    if "Col" not in me.color_attributes:
        me.color_attributes.new("Col", "BYTE_COLOR", "CORNER")
    attr = me.color_attributes["Col"]
    results = []
    for p, c, n in world_faces(obj):
        r = fn(c, n, p)
        if isinstance(r, tuple) and len(r) == 2 and isinstance(r[1], str):
            col, mat = r
        else:
            col, mat = r, "M_Toon"
        results.append((p.index, rgba(col), mat))
    me.materials.clear()
    slots = {}
    for _, _, mat in results:
        if mat not in slots:
            slots[mat] = len(slots)
            me.materials.append(A._material(mat))
    for idx, col, mat in results:
        p = me.polygons[idx]
        p.material_index = slots[mat]
        for li in p.loop_indices:
            attr.data[li].color_srgb = col
    return obj


def bark_painter(base, dark, moss=None, moss_hi=None, moss_amount=0.35, seed=0.0, groove=7.0, moss_up=0.45):
    """Bark with vertical-ish grooves (noise bands) and moss on up-facing faces."""
    def fn(c, n, p):
        g = nz((c.x * groove * 0.35, c.y * groove * 0.35, c.z * 1.2), seed)
        g2 = nz(c * 3.0, seed + 5)
        col = mix(base, dark, smooth((g * 0.5 + 0.5 - 0.55) * 4.0))
        if g2 > 0.45:
            col = mix(col, dark, 0.5)
        if moss is not None:
            m = n.z + nz(c * 1.7, seed + 11) * 0.55 + (moss_amount - 0.35)
            if m > moss_up:
                hi = nz(c * 4.0, seed + 17) > 0.1
                col = rgba(moss_hi if (hi and moss_hi) else moss)
        return col
    return fn


# ---------------------------------------------------------------- mesh builders

def obj_from_bm(name, bm, smooth_shade=True):
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    me = bpy.data.meshes.new(name)
    bm.to_mesh(me)
    bm.free()
    o = bpy.data.objects.new(name, me)
    bpy.context.scene.collection.objects.link(o)
    if smooth_shade:
        A.shade_smooth(o)
    return o


def catmull(pts, n=6):
    """Catmull-Rom resample of control points (n samples per span)."""
    pts = [Vector(p) for p in pts]
    if len(pts) < 3:
        return pts
    P = [pts[0] * 2 - pts[1]] + pts + [pts[-1] * 2 - pts[-2]]
    out = []
    for i in range(1, len(P) - 2):
        p0, p1, p2, p3 = P[i - 1], P[i], P[i + 1], P[i + 2]
        for k in range(n):
            t = k / n
            t2, t3 = t * t, t * t * t
            out.append(0.5 * ((2 * p1) + (-p0 + p2) * t + (2 * p0 - 5 * p1 + 4 * p2 - p3) * t2 + (-p0 + 3 * p1 - 3 * p2 + p3) * t3))
    out.append(P[-2])
    return out


def sweep(name, pts, radii, seg=12, n0=None, color="#888888", mat="M_Toon", cap_start=True, cap_end=True,
          shape=None, smooth_shade=True):
    """Tube through pts with per-point radius. radii: float list, or callable(t)->r. shape(t, ang)->radius mult.
    n0: initial frame normal (the 'side' reference). Returns obj; obj['side'] tag stored in attribute
    'side' (float, per vertex = cos(angle from frame normal)) and 'tpar' (0..1 along the tube)."""
    pts = [Vector(p) for p in pts]
    n = len(pts)
    if callable(radii):
        radii = [radii(i / (n - 1)) for i in range(n)]
    elif not hasattr(radii, "__len__"):
        radii = [float(radii)] * n
    elif len(radii) != n:  # control radii -> resample linearly along the points
        src = list(radii)
        radii = [KL(i / (n - 1), *[(j / (len(src) - 1), r) for j, r in enumerate(src)]) for i in range(n)]
    T = []
    for i in range(n):
        a, b = pts[max(i - 1, 0)], pts[min(i + 1, n - 1)]
        T.append((b - a).normalized())
    ref = Vector(n0) if n0 is not None else (Vector((0, 0, -1)) if abs(T[0].z) < 0.9 else Vector((0, -1, 0)))
    N = [(ref - T[0] * ref.dot(T[0])).normalized()]
    for i in range(1, n):
        prev = N[-1]
        nn = prev - T[i] * prev.dot(T[i])
        N.append(nn.normalized() if nn.length > 1e-6 else prev)
    bm = bmesh.new()
    rings = []
    side, tpar = [], []
    for i in range(n):
        B = T[i].cross(N[i])
        t = i / (n - 1)
        ring = []
        for k in range(seg):
            a = TAU * k / seg
            r = radii[i] * (shape(t, a) if shape else 1.0)
            ring.append(bm.verts.new(pts[i] + (N[i] * math.cos(a) + B * math.sin(a)) * r))
            side.append(math.cos(a))
            tpar.append(t)
        rings.append(ring)
    for a, b in zip(rings, rings[1:]):
        for k in range(seg):
            j = (k + 1) % seg
            bm.faces.new((a[k], a[j], b[j], b[k]))
    if cap_start and radii[0] > 1e-4:
        bm.faces.new(list(reversed(rings[0])))
    if cap_end and radii[-1] > 1e-4:
        bm.faces.new(rings[-1])
    o = obj_from_bm(name, bm, smooth_shade)
    me = o.data
    if len(me.vertices) == len(side):
        at = me.attributes.new("side", "FLOAT", "POINT")
        at2 = me.attributes.new("tpar", "FLOAT", "POINT")
        for i in range(len(side)):
            at.data[i].value = side[i]
            at2.data[i].value = tpar[i]
    A.paint(o, color, mat)
    return o, (pts, T, N)


def face_attr(obj, p, name):
    at = obj.data.attributes.get(name)
    if at is None:
        return 0.0
    return sum(at.data[v].value for v in p.vertices) / len(p.vertices)


def blob(name, r=0.5, loc=(0, 0, 0), scale=(1, 1, 1), rot=(0, 0, 0), color="#888888", mat="M_Toon", seed=0.0,
         amp=0.15, freq=2.0, subdiv=2, flat=False):
    """Noise-displaced icosphere: foliage lumps, rocks, smoke puffs."""
    bm = bmesh.new()
    bmesh.ops.create_icosphere(bm, subdivisions=subdiv, radius=r)
    for v in bm.verts:
        d = v.co.normalized()
        v.co = v.co * (1.0 + amp * nz(d * freq, seed))
    o = obj_from_bm(name, bm, not flat)
    A._place(o, loc, rot, scale)
    return A.paint(o, color, mat)


def crystal(name, r=0.1, h=0.5, loc=(0, 0, 0), rot=(0, 0, 0), color="#9fe4ff", mat="M_Clear", sides=6, waist=0.3,
            base=0.15, scale=(1, 1, 1)):
    """Faceted hexagonal crystal pointing +Z from loc (base slightly below)."""
    prof = [(0.0, -h * base), (r, h * waist * 0.3), (r * 0.92, h * waist + h * 0.25), (0.0, h)]
    o = A.lathe(name, prof, loc=loc, rot=rot, scale=scale, color=color, mat=mat, seg=sides)
    for p in o.data.polygons:
        p.use_smooth = False
    return o


def leaf(name, length=0.3, width=0.12, loc=(0, 0, 0), rot=(0, 0, 0), color="#5bbf3a", mat="M_Toon", thick=0.02):
    """Pointed leaf card along +Z (extruded, slight fold)."""
    pts = [(0, 0), (width * 0.5, length * 0.25), (width * 0.55, length * 0.55), (width * 0.25, length * 0.85), (0, length),
           (-width * 0.25, length * 0.85), (-width * 0.55, length * 0.55), (-width * 0.5, length * 0.25)]
    o = A.extrude_shape(name, pts, depth=thick, loc=loc, rot=rot, color=color, mat=mat)
    A.deform(o, lambda c: Vector((c.x, c.y + abs(c.x) * 0.6, c.z)))
    return o


def flame(name, h=0.6, r=0.15, loc=(0, 0, 0), rot=(0, 0, 0), bottom="#d2321a", top="#ffe36a", seed=0.0, curl=0.25,
          seg=10, mat="M_Emit", scale=(1, 1, 1)):
    """Licking flame tongue pointing +Z, tip curls sideways. Emissive gradient."""
    prof = [(0.0, -r * 0.6), (r * 0.8, -r * 0.3), (r, r * 0.4), (r * 0.8, h * 0.4), (r * 0.45, h * 0.7), (r * 0.15, h * 0.9), (0.0, h)]
    o = A.lathe(name, prof, seg=seg, color=bottom, mat=mat)

    def f(c):
        t = clamp(c.z / h)
        w = 1.0 + 0.25 * nz((c.x * 3, c.y * 3, c.z * 2), seed)
        return Vector((c.x * w + curl * h * t * t, c.y * w + 0.3 * curl * h * t * t * math.sin(seed * 3), c.z))
    A.deform(o, f)
    A.gradient(o, bottom, top)
    A._place(o, loc, rot, scale)
    return o


def plate(name, pts2d, depth, loc, rot, color, mat="M_Toon", bevel=0.0, scale=(1, 1, 1)):
    return A.extrude_shape(name, pts2d, depth=depth, loc=loc, rot=rot, color=color, mat=mat, bevel=bevel, scale=scale)


def ngon(n, r, start=0.0, rx=None, rz=None):
    rx = rx or r
    rz = rz or r
    return [(math.cos(start + TAU * i / n) * rx, math.sin(start + TAU * i / n) * rz) for i in range(n)]


def dup(o, name=None):
    c = o.copy()
    c.data = o.data.copy()
    c.name = name or (o.name + "_d")
    bpy.context.scene.collection.objects.link(c)
    return c


def mirror(objs):
    """Mirror each object across X; returns the mirrored copies."""
    out = []
    for o in objs:
        out.append(A.mirror_x(o, o.name + "_m"))
    return out


def tris(obj):
    return sum(len(p.vertices) - 2 for p in obj.data.polygons)


# ---------------------------------------------------------------- skinning

def chain_weights(obj, chain, falloff=1.0):
    """Smoothly weight obj's vertices along a bone chain. chain: [(bone, head, tail), ...] (armature space).
    Each bone gets a tent weight centred on its middle; ends clamp to first/last bone."""
    A.apply_transform(obj)
    joints = [Vector(chain[0][1])] + [Vector(b[2]) for b in chain]
    nb = len(chain)
    groups = [obj.vertex_groups.get(b[0]) or obj.vertex_groups.new(name=b[0]) for b in chain]
    for v in obj.data.vertices:
        best, bu = 1e9, 0.0
        for i in range(nb):
            a, b = joints[i], joints[i + 1]
            ab = b - a
            t = clamp((v.co - a).dot(ab) / max(ab.length_squared, 1e-9))
            d = (a + ab * t - v.co).length
            if d < best:
                best, bu = d, i + t
        ws = []
        for i in range(nb):
            c = i + 0.5
            if (i == 0 and bu <= c) or (i == nb - 1 and bu >= c):
                w = 1.0
            else:
                w = max(0.0, 1.0 - abs(bu - c) / falloff)
            ws.append(w)
        s = sum(ws) or 1.0
        for i, w in enumerate(ws):
            if w > 1e-3:
                groups[i].add([v.index], w / s, "REPLACE")
    obj["weighted"] = 1
    return obj


def skin2(rigid, smooth_parts, rig, name="Body"):
    """rigid: {bone: [objs]} (100 % weights); smooth_parts: objects already carrying vertex groups."""
    objs = []
    for bone, parts in rigid.items():
        for p in parts:
            if p is None:
                continue
            A.bind(p, bone)
            objs.append(p)
    objs += [p for p in smooth_parts if p is not None]
    body = A.join(objs, name)
    md = body.modifiers.new("Armature", "ARMATURE")
    md.object = rig
    body.parent = rig
    return body


# ---------------------------------------------------------------- animation

def K(t, *pairs):
    """Piecewise smoothstep interpolation through (time, value) pairs. value: float or tuple."""
    if t <= pairs[0][0]:
        return pairs[0][1]
    for (t0, v0), (t1, v1) in zip(pairs, pairs[1:]):
        if t <= t1:
            u = smooth((t - t0) / max(t1 - t0, 1e-9))
            if isinstance(v0, (tuple, list)):
                return tuple(a + (b - a) * u for a, b in zip(v0, v1))
            return v0 + (v1 - v0) * u
    return pairs[-1][1]


def KL(t, *pairs):
    """Piecewise linear version of K."""
    if t <= pairs[0][0]:
        return pairs[0][1]
    for (t0, v0), (t1, v1) in zip(pairs, pairs[1:]):
        if t <= t1:
            u = clamp((t - t0) / max(t1 - t0, 1e-9))
            if isinstance(v0, (tuple, list)):
                return tuple(a + (b - a) * u for a, b in zip(v0, v1))
            return v0 + (v1 - v0) * u
    return pairs[-1][1]


def sc(v, k):
    return tuple(x * k for x in v)


def add(*vs):
    return tuple(sum(c) for c in zip(*vs))


class Pose:
    """Additive pose accumulator. Rotations in degrees around armature axes, locations in metres (armature axes)."""

    def __init__(self):
        self.R, self.L, self.S = {}, {}, {}

    def r(self, bone, deg):
        self.R[bone] = add(self.R.get(bone, (0, 0, 0)), deg)

    def l(self, bone, xyz):
        self.L[bone] = add(self.L.get(bone, (0, 0, 0)), xyz)

    def s(self, bone, k):
        if not hasattr(k, "__len__"):
            k = (k, k, k)
        cur = self.S.get(bone, (1, 1, 1))
        self.S[bone] = tuple(a * b for a, b in zip(cur, k))


def bake(rig, name, length, fn, step=1):
    """fn(P: Pose, f: frame, t: 0..1) fills a pose; keys all bones on every sampled frame."""
    rest = {b.name: b.matrix_local.to_3x3() for b in rig.data.bones}
    inv = {k: m.inverted() for k, m in rest.items()}
    last = {}
    frames = list(range(0, length + 1, step))
    if frames[-1] != length:
        frames.append(length)
    with A.Anim(rig, name, length) as a:
        for f in frames:
            P = Pose()
            fn(P, f, f / length)
            for pb in rig.pose.bones:
                b = pb.name
                deg = P.R.get(b, (0, 0, 0))
                W = Euler([math.radians(d) for d in deg], "XYZ").to_matrix()
                Lm = inv[b] @ W @ rest[b]
                e = Lm.to_euler("XYZ", last[b]) if b in last else Lm.to_euler("XYZ")
                last[b] = e
                pb.rotation_euler = e
                pb.location = inv[b] @ Vector(P.L.get(b, (0, 0, 0)))
                pb.scale = P.S.get(b, (1, 1, 1))
                pb.keyframe_insert("rotation_euler", frame=f)
                pb.keyframe_insert("location", frame=f)
                pb.keyframe_insert("scale", frame=f)
    return a.action


def wave(t, cycles=1.0, phase=0.0):
    return math.sin(TAU * (t * cycles + phase))


# ---------------------------------------------------------------- output

ACTIONS = ("Idle", "Run", "Attack", "Cast", "Hit", "Die", "Victory", "Roar")


def finish(asset_id, rig, body, previews):
    """Validate actions, export FBX, save .blend, render previews.
    previews: list of (suffix, angle, action, frame)."""
    names = {a.name for a in bpy.data.actions}
    missing = [n for n in ACTIONS if n not in names]
    if missing:
        raise RuntimeError(f"{asset_id}: missing actions {missing}")
    for n in ACTIONS:
        act = bpy.data.actions[n]
        print(f"[{asset_id}] action {n}: frames {tuple(act.frame_range)}")
    print(f"[{asset_id}] tris: {tris(body)}  bones: {len(rig.data.bones)}  mats: {[m.name for m in body.data.materials]}")
    for m in body.data.materials:
        assert m.name in A.MATERIALS, m.name
    rig.animation_data.action = None
    for pb in rig.pose.bones:
        pb.location = (0, 0, 0)
        pb.rotation_euler = (0, 0, 0)
        pb.scale = (1, 1, 1)
    path = A.export_fbx(f"Enemies/{asset_id}/{asset_id}.fbx", objects=[rig, body], animated=True)
    assert os.path.exists(path), path
    print(f"[{asset_id}] exported {path} ({os.path.getsize(path)} bytes)")
    A.save_blend(f"boss_{asset_id}")
    for suffix, angle, action, frame in previews:
        A.render_preview(f"boss_{asset_id}_{suffix}", angle=angle, action=action, frame=frame, size=720)
    return path


STD_PREVIEWS = [
    ("front", (72, 0, 32), None, None),
    ("side", (80, 0, 90), None, None),
    ("back", (70, 0, 160), None, None),
]
