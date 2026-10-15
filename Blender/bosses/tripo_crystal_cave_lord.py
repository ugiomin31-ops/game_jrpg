"""crystal_cave_lord (수정 동굴의 주인) — zone-5 cave boss from a Tripo Studio mesh, rigged here instead of by Tripo.

Why this script exists: Tripo's "Other" auto rig failed twice on this quadruped (30 bones but only 7 vertex groups,
2794/5150 vertices weighted, legs and tail unweighted; see ArtSource/hunter-bosses/crystal_cave_lord/candidates/
prompts.md). The skeleton detection was fine, the skinning was not, and a retry repeated the same result, so the
failure follows the mesh (short legs buried under a wide shell skirt) and a third paid rig would not fix it.
This script keeps only Tripo's mesh and texture and builds everything else:

- the Tripo armature and all its vertex groups are discarded,
- a quadruped `Rig` (root, body, chest, head, leg.{F,B}{L,R} upper/lower, tail1-3) is fitted to the mesh bounds:
  paws from the floor-contact vertex clusters, hips/shoulders at HIP_H of the height, head and tail at the ends,
- skin weights are geometric, not heat diffusion: each vertex takes inverse-distance weights to the bone segments it
  is allowed to follow (legs only below the hip line in their own quadrant, head only in front of the neck, tail only
  behind the rump), then a few rounds of edge smoothing. This needs no closed/manifold surface, which is exactly what
  the shell skirt breaks, and cannot leave a vertex unweighted,
- seven baked actions Idle/Run/Attack/Cast/Hit/Die/Victory (README lengths, Attack head-slam at 40 %, Cast crystal
  flare at 60 %, Die ends on its belly), paws pinned to the floor with an analytic two-bone IK,
- export via lib_humanoid/textured.py (one material `crystal_cave_lord`, base-colour PNG, white `Col`), then a fresh
  Blender re-imports the FBX and checks the contract, every vertex weighted, each leg/tail/head bone actually
  deforming its region, floor contact per clip and loop seams, and renders preview sheets.

Source (not generated here): ArtSource/hunter-bosses/crystal_cave_lord/tripo_export/*.fbx (+ .fbm textures), Tripo
task e207ee73 (H3.1, Smart Mesh retopo 10,316 tris). Either of the two failed-rig exports works; its rig is ignored.
Output goes to ArtSource/hunter-bosses/crystal_cave_lord/staging/ (mirrors Assets/...) unless `--assets` is given.
The data still points the boss at `crystal_horror` (enemies.json `model`); switch it only after reviewing previews.

Run (repo root):
  C:/Users/User/Tools/Blender/blender.exe -b --factory-startup --python-exit-code 1 -P Blender/bosses/tripo_crystal_cave_lord.py
  ... -- --assets        write straight into Assets/_Game/Resources/Art instead of staging/
  ... -- --src X.fbx     use another source FBX (default: the single FBX in tripo_export/)
  ... -- --yaw 180       turn the source about Z first if its head does not face -Y (check preview/side.png)
  ... -- --verify        only re-import the exported FBX, check the contract and render previews
After a build the script re-runs itself with --verify in a fresh Blender process.
"""
import glob
import json
import math
import os
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.join(HERE, "..", "lib"))
sys.path.insert(0, os.path.join(HERE, "..", "lib_humanoid"))
import bpy  # noqa: E402  (first: outside Blender, the bpy module is what makes bmesh importable)
import abyss_bpy as A  # noqa: E402
import numpy as np  # noqa: E402
from mathutils import Euler, Matrix, Quaternion, Vector  # noqa: E402

ID = "crystal_cave_lord"
SRC_DIR = os.path.join(A.REPO, "ArtSource", "hunter-bosses", ID)
PREVIEW_DIR = os.path.join(SRC_DIR, "preview")
STAGING = os.path.join(SRC_DIR, "staging")
ARGV = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
if "--assets" not in ARGV:
    A.ASSETS = os.path.join(STAGING, "Assets", "_Game", "Resources", "Art")
REL_FBX = f"Enemies/{ID}/{ID}.fbx"
FBX = os.path.join(A.ASSETS, REL_FBX)
TEX_SIZE = 1024            # Unity caps _tex PNGs at 1024 (AbyssArtImporter.OnPreprocessTexture)


def arg(name, default=None):
    return ARGV[ARGV.index(name) + 1] if name in ARGV else default


# crystal_horror (the model the boss borrows today) is 0.65 x 1.51 x 1.18 m; the boss stands a little taller.
TARGET_H = 1.35
HIP_H = 0.42               # hip / shoulder joints at this fraction of the height
FOOT_H = 0.12              # vertices below this fraction of the height are paw-contact candidates
HEAD_K = 0.30              # front fraction of the length that follows the head
TAIL_K = 0.24              # rear fraction of the length that may follow the tail

LENGTHS = {"Idle": 48, "Run": 20, "Attack": 25, "Cast": 35, "Hit": 12, "Die": 30, "Victory": 44}
RANGES = {"Idle": (40, 60), "Run": (16, 24), "Attack": (18, 30), "Cast": (30, 40), "Hit": (10, 14),
          "Die": (24, 36), "Victory": (36, 48)}
ATTACK_HIT = 10            # 40 % of 25
CAST_HIT = 21              # 60 % of 35
LEGS = ("FL", "FR", "BL", "BR")
# Paws that must stay on the floor through a clip (Run swings them, Attack/Victory raise the front pair).
PLANTED = {"Idle": LEGS, "Cast": LEGS, "Hit": LEGS, "Attack": ("BL", "BR"), "Victory": ("BL", "BR")}
TAU = math.tau


def source_fbx():
    src = arg("--src")
    if src:
        return os.path.abspath(src)
    hits = sorted(glob.glob(os.path.join(SRC_DIR, "tripo_export", "*.fbx")))
    if len(hits) != 1:
        raise RuntimeError(f"expected one Tripo FBX in {os.path.join(SRC_DIR, 'tripo_export')}, found {hits}")
    return hits[0]


def K(f, *pairs):
    """Smooth-step key interpolation over (frame, value) pairs; values may be numbers or tuples."""
    if f <= pairs[0][0]:
        return pairs[0][1]
    for (f0, v0), (f1, v1) in zip(pairs, pairs[1:]):
        if f <= f1:
            u = (f - f0) / (f1 - f0)
            u = u * u * (3 - 2 * u)
            if isinstance(v0, tuple):
                return tuple(a + (b - a) * u for a, b in zip(v0, v1))
            return v0 + (v1 - v0) * u
    return pairs[-1][1]


# ---------------------------------------------------------------- import: keep the mesh, drop Tripo's rig

def import_mesh():
    A.reset_scene()
    for name in A.MATERIALS:          # textured model: no shared slots
        bpy.data.materials.remove(bpy.data.materials[name])
    bpy.ops.import_scene.fbx(filepath=source_fbx())
    objs = list(bpy.context.scene.objects)
    meshes = [o for o in objs if o.type == "MESH"]
    if not meshes:
        raise RuntimeError("no mesh in the source FBX")
    for o in meshes:
        o.matrix_world = o.matrix_world.copy()          # keep world placement through un-parenting
        mw = o.matrix_world.copy()
        o.parent = None
        o.matrix_world = mw
        o.modifiers.clear()
        o.vertex_groups.clear()
        A.apply_transform(o)
    for o in objs:
        if o.type != "MESH":
            bpy.data.objects.remove(o, do_unlink=True)
    body = A.join(meshes, "Body") if len(meshes) > 1 else meshes[0]
    body.name = body.data.name = "Body"
    for key in list(body.data.shape_keys.key_blocks) if body.data.shape_keys else []:
        body.shape_key_remove(key)

    # Normalise: optional yaw, centred in X/Y, standing on z=0, scaled to TARGET_H.
    yaw = float(arg("--yaw", 0.0))
    if yaw:
        body.rotation_euler = (0, 0, math.radians(yaw))
        A.apply_transform(body)
    pts = verts(body)
    lo, hi = pts.min(0), pts.max(0)
    k = TARGET_H / float(hi[2] - lo[2])
    body.location = (-(lo[0] + hi[0]) / 2 * k, -(lo[1] + hi[1]) / 2 * k, -lo[2] * k)
    body.scale = (k, k, k)
    A.apply_transform(body)

    # One material named after the enemy, carrying only the base colour (Abyss/Toon shades from _BaseMap and Col).
    imgs = [n.image for m in body.data.materials if m and m.use_nodes for n in m.node_tree.nodes
            if n.type == "TEX_IMAGE" and n.image]
    if not imgs:
        raise RuntimeError("source material has no image texture")
    base = next((i for i in imgs if "basecolor" in i.name.lower() or "base_color" in i.name.lower()), imgs[0])
    base.colorspace_settings.name = "sRGB"
    olds = list(body.data.materials)
    mat = bpy.data.materials.new(ID)
    mat.use_nodes = True
    nt = mat.node_tree
    bsdf = next(n for n in nt.nodes if n.type == "BSDF_PRINCIPLED")
    tex = nt.nodes.new("ShaderNodeTexImage")
    tex.image = base
    nt.links.new(tex.outputs["Color"], bsdf.inputs["Base Color"])
    bsdf.inputs["Roughness"].default_value = 0.8
    body.data.materials.clear()
    body.data.materials.append(mat)
    for p in body.data.polygons:
        p.material_index = 0
    for m in olds:
        if m and m.users == 0:
            bpy.data.materials.remove(m)
    for img in list(bpy.data.images):
        if img != base and img.users == 0:
            bpy.data.images.remove(img)

    col = body.data.color_attributes.new("Col", "BYTE_COLOR", "CORNER")
    col.data.foreach_set("color", [1.0] * (4 * len(col.data)))
    body.data.color_attributes.active_color = col
    for p in body.data.polygons:
        p.use_smooth = True
    return body


def verts(o):
    pts = np.empty(len(o.data.vertices) * 3, np.float64)
    o.data.vertices.foreach_get("co", pts)
    pts = pts.reshape(-1, 3)
    m = np.array(o.matrix_world)
    return pts @ m[:3, :3].T + m[:3, 3]


# ---------------------------------------------------------------- skeleton fitted to the mesh

def fit_skeleton(pts):
    """Joint positions (armature space) from the normalised mesh; facing -Y, left = +X."""
    lo, hi = pts.min(0), pts.max(0)
    W, L, H = hi - lo
    hz = HIP_H * H
    # Paws: floor-contact vertices split into quadrants; a quadrant with nothing on the floor gets a default spot.
    low = pts[pts[:, 2] < FOOT_H * H]
    paws = {}
    for leg in LEGS:
        sx = 1.0 if leg[1] == "L" else -1.0
        sy = -1.0 if leg[0] == "F" else 1.0
        q = low[(np.sign(low[:, 0]) == sx) & (np.sign(low[:, 1]) == sy) & (np.abs(low[:, 0]) > 0.08 * W)]
        if len(q) >= 12:
            c = q.mean(0)
            paws[leg] = Vector((float(c[0]), float(c[1]), 0.0))
        else:
            paws[leg] = Vector((sx * 0.3 * W, sy * 0.28 * L, 0.0))
    front_y = (paws["FL"].y + paws["FR"].y) / 2
    back_y = (paws["BL"].y + paws["BR"].y) / 2
    j = {"paws": paws, "W": W, "L": L, "H": H, "hz": hz, "lo": lo, "hi": hi}
    j["hips"] = {leg: Vector((paws[leg].x * 0.8, paws[leg].y, hz)) for leg in LEGS}
    j["body"] = (Vector((0, back_y, hz)), Vector((0, (front_y + back_y) / 2, hz)))
    j["chest"] = (j["body"][1].copy(), Vector((0, front_y, hz * 1.08)))
    # Head: centroid of the front slab above the paws; neck joint just behind it.
    front = pts[pts[:, 1] < lo[1] + HEAD_K * L]
    hc = front.mean(0) if len(front) else np.array([0, lo[1] + 0.15 * L, 0.6 * H])
    neck = Vector((0, min(front_y, float(lo[1] + HEAD_K * L)), max(hz * 1.08, float(hc[2]) - 0.1 * H)))
    j["head"] = (neck, Vector((0, float(lo[1]), float(hc[2]) + 0.05 * H)))
    j["neck_y"] = neck.y
    # Tail: from the rump to the rear-most low point.
    rear = pts[(pts[:, 1] > hi[1] - 0.1 * L) & (pts[:, 2] < 0.6 * H)]
    tip = rear.mean(0) if len(rear) else np.array([0, hi[1], 0.25 * H])
    t0 = Vector((0, max(back_y, float(hi[1] - TAIL_K * L)), hz * 0.9))
    t3 = Vector((0, float(hi[1]), float(tip[2])))
    j["tail"] = [t0.lerp(t3, k / 3) for k in range(4)]
    j["tail_y"] = t0.y
    return j


def build_rig(j):
    arm = bpy.data.armatures.new("Rig")
    rig = bpy.data.objects.new("Rig", arm)
    bpy.context.scene.collection.objects.link(rig)
    bpy.context.view_layer.objects.active = rig
    rig.select_set(True)
    bpy.ops.object.mode_set(mode="EDIT")
    eb = arm.edit_bones

    def bone(name, head, tail, parent=None, deform=True):
        b = eb.new(name)
        b.head, b.tail = head, tail
        b.roll = 0.0
        b.use_deform = deform
        if parent:
            b.parent = eb[parent]
        return b

    H = j["H"]
    bone("root", (0, 0, 0), (0, 0, 0.2 * H), deform=False)
    bone("body", *j["body"], parent="root")
    bone("chest", *j["chest"], parent="body")
    bone("head", *j["head"], parent="chest")
    for leg in LEGS:
        hip, paw = j["hips"][leg], j["paws"][leg]
        # The knee sits a little off the hip-paw line so the IK always bends the same way:
        # front elbows back (+Y), hind knees forward (-Y).
        bend = 0.1 * j["L"] * (1.0 if leg[0] == "F" else -1.0)
        knee = hip.lerp(paw, 0.5) + Vector((0, bend, 0))
        foot = paw + Vector((0, 0, 0.04 * H))
        bone(f"leg.{leg}", hip, knee, parent="chest" if leg[0] == "F" else "body")
        bone(f"shin.{leg}", knee, foot, parent=f"leg.{leg}").use_connect = True
        # The paw stays level while the shin tilts (a rotating shin would dig the toes into the floor).
        bone(f"paw.{leg}", foot, foot + Vector((0, -0.08 * j["L"], 0)), parent=f"shin.{leg}")
    t = j["tail"]
    for k in range(3):
        bone(f"tail{k + 1}", t[k], t[k + 1], parent="body" if k == 0 else f"tail{k}")
    bpy.ops.object.mode_set(mode="OBJECT")
    for pb in rig.pose.bones:
        pb.rotation_mode = "XYZ"
    return rig


# ---------------------------------------------------------------- geometric skin weights

def seg_dist(p, a, b):
    ab = b - a
    t = np.clip(((p - a) @ ab) / max(float(ab @ ab), 1e-12), 0.0, 1.0)
    return np.linalg.norm(p - (a + t[:, None] * ab), axis=1)


def skin_weights(body, rig, j):
    pts = verts(body)
    W, L, H, hz = j["W"], j["L"], j["H"], j["hz"]
    bones = [b for b in rig.data.bones if b.use_deform]
    names = [b.name for b in bones]
    n = len(pts)
    D = np.stack([seg_dist(pts, np.array(b.head_local), np.array(b.tail_local)) for b in bones], 1)
    allow = np.ones((n, len(bones)), bool)
    blend_z = 0.06 * H
    for i, name in enumerate(names):
        if name.startswith(("leg.", "shin.", "paw.")):
            leg = name.split(".")[1]
            sx = 1.0 if leg[1] == "L" else -1.0
            front = leg[0] == "F"
            mid = (j["body"][0].y + j["chest"][1].y) / 2
            # Floor-contact vertices follow only the level paw bone; any shin share there would dip below z=0.
            band = ((pts[:, 2] < 0.14 * H) if name.startswith("paw.") else
                    (pts[:, 2] > 0.05 * H) & (pts[:, 2] < hz + blend_z))
            allow[:, i] = band & (pts[:, 0] * sx > 0.02 * W) & ((pts[:, 1] < mid) if front else (pts[:, 1] >= mid))
        elif name == "head":
            allow[:, i] = pts[:, 1] < j["neck_y"] + 0.06 * L
        elif name.startswith("tail"):
            allow[:, i] = (pts[:, 1] > j["tail_y"] - 0.04 * L) & (pts[:, 2] < 0.7 * H)
    w = np.where(allow, 1.0 / (D + 0.02 * H) ** 4, 0.0)
    w /= w.sum(1, keepdims=True)

    # Edge smoothing so the seams between bones bend instead of creasing.
    me = body.data
    e = np.empty(len(me.edges) * 2, np.int64)
    me.edges.foreach_get("vertices", e)
    e = e.reshape(-1, 2)
    deg = np.bincount(e.ravel(), minlength=n).astype(np.float64)[:, None]
    for _ in range(8):
        acc = np.zeros_like(w)
        np.add.at(acc, e[:, 0], w[e[:, 1]])
        np.add.at(acc, e[:, 1], w[e[:, 0]])
        nb = np.where(deg > 0, acc / np.maximum(deg, 1), w)
        w = np.where(allow, 0.5 * w + 0.5 * nb, 0.0)
        w /= np.maximum(w.sum(1, keepdims=True), 1e-12)

    # Keep the four strongest influences per vertex (Unity's default skin quality).
    order = np.argsort(-w, axis=1)
    keep = np.zeros_like(w, bool)
    np.put_along_axis(keep, order[:, :4], True, axis=1)
    w = np.where(keep & (w > 0.01), w, 0.0)
    w /= w.sum(1, keepdims=True)
    groups = [body.vertex_groups.new(name=nm) for nm in names]
    for i, g in enumerate(groups):
        idx = np.nonzero(w[:, i])[0]
        for v in idx:
            g.add([int(v)], float(w[v, i]), "REPLACE")
    md = body.modifiers.new("Armature", "ARMATURE")
    md.object = rig
    body.parent = rig
    body.matrix_parent_inverse.identity()
    return {nm: int((w[:, i] > 0.5).sum()) for i, nm in enumerate(names)}


# ---------------------------------------------------------------- pose model: rigid deltas per bone, leg IK

REST = {}


def learn_rest(rig, j):
    REST["mat"] = {b.name: b.matrix_local.copy() for b in rig.data.bones}
    REST["parent"] = {b.name: b.parent.name if b.parent else None for b in rig.data.bones}
    REST["order"] = [b.name for b in rig.data.bones]          # parents come before children
    REST["j"] = j
    REST["clear"] = 0.1 * j["H"]
    for leg in LEGS:
        up, lo = rig.data.bones[f"leg.{leg}"], rig.data.bones[f"shin.{leg}"]
        REST[leg] = dict(hip=up.head_local.copy(), knee=up.tail_local.copy(), foot=lo.tail_local.copy(),
                         L1=up.length, L2=lo.length)


def about(pivot, deg, order="XYZ"):
    """Rotation by armature-axis degrees about a pivot point, as a 4x4."""
    R = Euler([math.radians(a) for a in deg], order).to_matrix().to_4x4()
    return Matrix.Translation(pivot) @ R @ Matrix.Translation(-pivot)


def two_bone(hip, target, L1, L2, pole):
    d = target - hip
    a = min(max(d.length, abs(L1 - L2) + 1e-4), (L1 + L2) * 0.9999)
    u = d.normalized()
    side = pole - u * pole.dot(u)
    side = side.normalized() if side.length > 1e-6 else Vector((0, 1, 0))
    c = (L1 * L1 + a * a - L2 * L2) / (2 * L1 * a)
    s = math.sqrt(max(0.0, 1 - c * c))
    knee = hip + u * (L1 * c) + side * (L1 * s)
    return knee, hip + u * a


def aim(D_parent, a_rest, b_rest, a_new, b_new):
    """Rigid delta that carries the rest segment a->b onto a_new->b_new, keeping the parent's twist."""
    Rp = D_parent.to_3x3()
    q = (Rp @ (b_rest - a_rest)).rotation_difference(b_new - a_new)
    R = (q.to_matrix() @ Rp).to_4x4()
    return Matrix.Translation(a_new) @ R @ Matrix.Translation(-a_rest)


class Pose:
    """body: loc (m) + rot (pitch, roll, yaw deg) about the hind hips; chest/head/tail: local deg about their joints.
    feet: per leg (dx, dy, dz) offset of the paw target from rest, in armature space."""

    def __init__(self):
        self.loc = Vector((0, 0, 0))
        self.rot = [0.0, 0.0, 0.0]
        self.rear = False                     # True: body pitches about the hind hips (rearing), else mid-body
        self.chest = [0.0, 0.0, 0.0]
        self.head = [0.0, 0.0, 0.0]
        self.tail = [0.0, 0.0, 0.0]          # pitch, roll, yaw per tail bone (yaw = side sway)
        self.feet = {leg: (0.0, 0.0, 0.0) for leg in LEGS}


def deltas(P):
    j = REST["j"]
    D = {"root": Matrix.Identity(4)}
    piv = j["body"][0] if P.rear else j["body"][1]
    D["body"] = Matrix.Translation(P.loc) @ about(piv, P.rot)
    D["chest"] = D["body"] @ about(j["chest"][0], P.chest)
    D["head"] = D["chest"] @ about(j["head"][0], P.head)
    prev = D["body"]
    for k in range(3):
        name = f"tail{k + 1}"
        D[name] = prev @ about(j["tail"][k], P.tail, "XYZ")
        prev = D[name]
    for leg in LEGS:
        r = REST[leg]
        Dp = D["chest"] if leg[0] == "F" else D["body"]
        hip = Dp @ r["hip"]
        target = r["foot"] + Vector(P.feet[leg])
        pole = Dp.to_3x3() @ (r["knee"] - r["hip"].lerp(r["foot"], 0.5))
        knee, foot = two_bone(hip, target, r["L1"], r["L2"], pole)
        D[f"leg.{leg}"] = aim(Dp, r["hip"], r["knee"], hip, knee)
        D[f"shin.{leg}"] = aim(D[f"leg.{leg}"], r["knee"], r["foot"], knee, foot)
        D[f"paw.{leg}"] = Matrix.Translation(foot - r["foot"])
    return D


def apply_pose(rig, P, last=None):
    D = deltas(P)
    eul = {}
    for name in REST["order"]:
        pb = rig.pose.bones[name]
        rest = REST["mat"][name]
        par = REST["parent"][name]
        rel = D[par].inverted() @ D[name] if par else D[name]
        basis = rest.inverted() @ rel @ rest
        loc, rot, _ = basis.decompose()
        e = rot.to_euler("XYZ", last[name]) if last and name in last else rot.to_euler("XYZ")
        pb.location, pb.rotation_euler, pb.scale = loc, e, (1, 1, 1)
        eul[name] = e
    return eul


LIFT = {}               # clip -> {frame: body lift in m}, set by fit_floor() so nothing passes through the floor
TAIL_UP = {}            # clip -> {frame: extra tail pitch in deg}, set by fit_floor() so the tail clears the floor


def bake(rig, name, length, fn, clip=None):
    lift = LIFT.get(clip or name, {})
    tail_up = TAIL_UP.get(clip or name, {})
    with A.Anim(rig, name, length) as a:
        last = None
        for f in range(length + 1):
            P = Pose()
            fn(P, f, f / length)
            P.loc = P.loc + Vector((0, 0, lift.get(f, 0.0)))
            P.tail = [P.tail[0] + tail_up.get(f, 0.0)] + list(P.tail[1:])
            last = apply_pose(rig, P, last)
            for pb in rig.pose.bones:
                pb.keyframe_insert("location", frame=f)
                pb.keyframe_insert("rotation_euler", frame=f)
                pb.keyframe_insert("scale", frame=f)
    return a.action


# ---------------------------------------------------------------- clips (H-relative so they survive any rescale)

def Hh(k):
    return k * REST["j"]["H"]


def Ll(k):
    return k * REST["j"]["L"]


def dip(k):
    """A downward body move of k*H, capped at half the belly clearance (the shell skirt may hang close to the floor)."""
    return min(Hh(k), 0.5 * REST["clear"])


def sway_tail(P, side, lift=0.0):
    P.tail = [lift, 0.0, side]


def idle(P, f, t):
    # One slow breath per loop: the shell rises, the head bobs under its hard hat, the tail sways.
    br = 0.5 - 0.5 * math.cos(TAU * t)
    P.loc = Vector((0, 0, -dip(0.012) * (1 - br)))
    P.rot = [-1.5 * br, 1.2 * math.sin(TAU * t), 0]
    P.chest = [1.0 - 2.0 * br, 0, 0]
    P.head = [2.0 * math.sin(TAU * t - 0.6), 0, 3.0 * math.sin(TAU * t)]
    sway_tail(P, 8 * math.sin(TAU * t - 0.9), lift=-2 * br)


def trot_foot(phase):
    """(dy, dz) of one paw over a stubby trot cycle; stance 0..0.55 slides back, swing lifts it forward."""
    s, lift = Ll(0.06), Hh(0.07)
    p = phase % 1.0
    if p < 0.55:
        return -s + 2 * s * p / 0.55, 0.0
    u = (p - 0.55) / 0.45
    return s - 2 * s * (0.5 - 0.5 * math.cos(math.pi * u)), lift * math.sin(math.pi * u)


def run(P, f, t):
    # Trot in place: diagonal pairs (FL+BR, FR+BL), the shell bobs twice per loop and rolls over the stance pair.
    ph = {"FL": 0.0, "BR": 0.0, "FR": 0.5, "BL": 0.5}
    for leg in LEGS:
        dy, dz = trot_foot(t + ph[leg])
        P.feet[leg] = (0, dy, dz)
    bob = math.cos(TAU * 2 * (t - 0.1))
    P.loc = Vector((0, 0, -dip(0.03) - dip(0.015) * bob))
    P.rot = [2.0, 3.0 * math.sin(TAU * t), 0]
    P.chest = [0, 0, 4 * math.sin(TAU * t)]
    P.head = [-3 + 2 * bob, 0, -4 * math.sin(TAU * t)]
    sway_tail(P, 12 * math.sin(TAU * t + 1.2), lift=3 * bob)


ATTACK_HEAD = [24.0]    # head pitch at impact, solved by fit_attack_to_floor() so the hard hat just meets the floor


def attack(P, f, t):
    # Rear back on the hind legs (0-6), front paws up; slam the hard hat and both front paws down in front at frame 10
    # (40 %); shudder (10-14); push back to stand (14-25).
    fr = (0, 6, 10, 14, 25)
    k = lambda *v: K(f, *zip(fr, v))  # noqa: E731
    P.rear = True
    shake = math.sin(f * 3.0) * (1.0 if ATTACK_HIT <= f <= 14 else 0.0) * (1 - (f - ATTACK_HIT) / 5.0)
    P.rot = [k(0, -16, 6, 5, 0), 0, 0]
    P.loc = Vector((0, k(0, Ll(0.03), -Ll(0.03), -Ll(0.03), 0), k(0, 0, -dip(0.06), -dip(0.05), 0) + Hh(0.008) * shake))
    P.chest = [k(0, -6, 5, 4, 0), 0, 0]
    slam = ATTACK_HEAD[0]
    P.head = [k(0, -14, slam, slam - 4, 0) + 2 * shake, 0, 0]
    for leg in ("FL", "FR"):
        P.feet[leg] = (0, k(0, -Ll(0.02), -Ll(0.09), -Ll(0.09), 0), k(0, Hh(0.22), 0, 0, 0))
    for leg in ("BL", "BR"):
        P.feet[leg] = (0, 0, 0)
    sway_tail(P, 0, lift=k(0, -12, 10, 8, 0))


def cast(P, f, t):
    # Hunker down and curl (0-12); draw in (12-18); at frame 21 (60 %) arch the back so the crystal row flares up,
    # head thrown up in a roar; tremble to 28; settle by 35.
    fr = (0, 12, 18, 21, 28, 35)
    k = lambda *v: K(f, *zip(fr, v))  # noqa: E731
    shake = math.sin(f * 2.6) * (1.0 if CAST_HIT <= f <= 28 else 0.0) * (1 - (f - CAST_HIT) / 8.0)
    P.loc = Vector((0, 0, k(0, -dip(0.08), -dip(0.06), Hh(0.01), Hh(0.008), 0)))
    P.rot = [k(0, 3, 2, -5, -4, 0) + 1.2 * shake, 1.5 * shake, 0]
    P.chest = [k(0, 8, 5, -7, -6, 0), 0, 0]
    P.head = [k(0, 16, 8, -26, -22, 0), 0, 0]
    sway_tail(P, 3 * shake, lift=k(0, 8, 4, -16, -14, 0))


def hit(P, f, t):
    # Knocked back at frame 3, head snapped up, recovers by 12; the paws stay planted.
    fr = (0, 3, 7, 12)
    k = lambda *v: K(f, *zip(fr, v))  # noqa: E731
    P.loc = Vector((0, k(0, Ll(0.03), Ll(0.01), 0), k(0, -dip(0.03), -dip(0.01), 0)))
    P.rot = [k(0, -6, -2, 0), k(0, 4, 1, 0), k(0, 5, 2, 0)]
    P.chest = [k(0, -4, -1, 0), 0, 0]
    P.head = [k(0, -16, -5, 0), 0, k(0, -8, -3, 0)]
    sway_tail(P, k(0, 10, 4, 0), lift=k(0, 8, 2, 0))


DIE_DROP = [0.0]        # final body drop, set by fit_die_to_floor()


def die(P, f, t):
    # Staggers (0-5), legs buckle outward (5-16), belly flops onto the floor (16-20), bounce (23), lies still from 26.
    fr = (0, 5, 16, 20, 23, 26, 30)
    k = lambda *v: K(f, *zip(fr, v))  # noqa: E731
    drop = DIE_DROP[0]
    P.loc = Vector((0, k(0, Ll(0.03), Ll(0.01), 0, 0, 0, 0), k(0, Hh(0.01), -drop * 0.6, -drop, -drop + Hh(0.02), -drop, -drop)))
    P.rot = [k(0, -5, 4, 3, 2, 3, 3), k(0, 3, 6, 4, 4, 4, 4), 0]
    P.chest = [k(0, -4, 6, 8, 6, 8, 8), 0, 0]
    P.head = [k(0, -10, 14, 26, 22, 26, 26), 0, k(0, 0, 8, 12, 12, 12, 12)]
    spread = k(0, 0, 0.16, 0.22, 0.22, 0.22, 0.22)
    for leg in LEGS:
        sx = 1.0 if leg[1] == "L" else -1.0
        sy = -1.0 if leg[0] == "F" else 1.0
        P.feet[leg] = (sx * Ll(spread * 0.5), sy * Ll(spread * 0.35), 0)
    sway_tail(P, k(0, 6, 10, 14, 12, 14, 14), lift=k(0, -4, 6, 12, 10, 12, 12))


def victory(P, f, t):
    # Rear up (0-8), stomp the front paws (14), rear again (20), stomp (26), then a proud head-up pose (32-44).
    fr = (0, 8, 14, 20, 26, 32, 44)
    k = lambda *v: K(f, *zip(fr, v))  # noqa: E731
    P.rear = True
    P.rot = [k(0, -14, 0, -12, 0, -3, -3), 0, 0]
    P.loc = Vector((0, 0, k(0, 0, -dip(0.03), 0, -dip(0.03), 0, 0)))
    P.chest = [k(0, -4, 2, -4, 2, -2, -2), 0, 0]
    P.head = [k(0, -12, 6, -12, 6, -14, -14), 0, k(0, 0, 0, 0, 0, 6, 6)]
    for leg in ("FL", "FR"):
        P.feet[leg] = (0, 0, k(0, Hh(0.18), 0, Hh(0.16), 0, 0, 0))
    sway_tail(P, 10 * math.sin(TAU * t * 3), lift=k(0, -8, 4, -8, 4, -10, -10))


CLIPS = {"Idle": idle, "Run": run, "Attack": attack, "Cast": cast, "Hit": hit, "Die": die, "Victory": victory}


# ---------------------------------------------------------------- floor fit / checks

def mesh_points(body):
    dg = bpy.context.evaluated_depsgraph_get()
    ev = body.evaluated_get(dg)
    me = ev.to_mesh()
    pts = np.empty(len(me.vertices) * 3, np.float32)
    me.vertices.foreach_get("co", pts)
    ev.to_mesh_clear()
    pts = pts.reshape(-1, 3)
    m = np.array(body.matrix_world)
    return pts @ m[:3, :3].T + m[:3, 3]


def pose_points(rig, body, action, frame):
    rig.animation_data.action = action
    bpy.context.scene.frame_set(frame)
    return mesh_points(body)


def dominant(body, prefixes):
    names = [g.name for g in body.vertex_groups]
    mask = np.zeros(len(body.data.vertices), bool)
    for v in body.data.vertices:
        if v.groups:
            mask[v.index] = names[max(v.groups, key=lambda g: g.weight).group].startswith(prefixes)
    return mask


def fit_attack_to_floor(rig, body):
    """Head pitch at impact such that the lowest vertex just meets the floor (+1 cm), searched over -20..45 deg."""
    lo, hi = -20.0, 45.0
    z = 0.0
    head = dominant(body, ("head",))
    for _ in range(12):
        ATTACK_HEAD[0] = 0.5 * (lo + hi)
        act = bake(rig, "_Probe", LENGTHS["Attack"], attack, clip="none")
        z = float(pose_points(rig, body, act, ATTACK_HIT)[head, 2].min())
        rig.animation_data.action = None
        bpy.data.actions.remove(act)
        if abs(z - 0.01) < 0.003:
            break
        if z > 0.01:
            lo = ATTACK_HEAD[0]
        else:
            hi = ATTACK_HEAD[0]
    print(f"[{ID}] Attack head slam {ATTACK_HEAD[0]:.1f} deg (lowest head vertex at impact {z:.3f})")


def fit_floor(rig, body, name):
    """Fix any frame whose lowest vertex would pass through the floor: a tail vertex raises the tail, anything else
    lifts the body (the paws stay pinned by IK, so the legs take up the lift). Looping clips get the same fix on their
    first and last frame (same pose)."""
    LIFT[name] = {}
    TAIL_UP[name] = {}
    tail_len = (REST["j"]["tail"][3] - REST["j"]["tail"][0]).length
    worst = 0.0
    culprit = None
    for _ in range(12):
        act = bake(rig, "_Probe", LENGTHS[name], CLIPS[name], clip=name)
        frames = [pose_points(rig, body, act, f) for f in range(LENGTHS[name] + 1)]
        lows = [float(p[:, 2].min()) for p in frames]
        if culprit is None and min(lows) < -0.004:
            f = int(np.argmin(lows))
            v = body.data.vertices[int(np.argmin(frames[f][:, 2]))]
            g = max(v.groups, key=lambda g: g.weight)
            culprit = f"frame {f}, {min(lows):.3f} m, vertex on {body.vertex_groups[g.group].name}"
        rig.animation_data.action = None
        bpy.data.actions.remove(act)
        worst = min(lows)
        if worst > -0.004:
            break
        for f, z in enumerate(lows):
            if z < -0.002:
                v = body.data.vertices[int(np.argmin(frames[f][:, 2]))]
                g = body.vertex_groups[max(v.groups, key=lambda g: g.weight).group].name
                if g.startswith("tail"):
                    TAIL_UP[name][f] = TAIL_UP[name].get(f, 0.0) + math.degrees((0.006 - z) / tail_len)
                else:
                    LIFT[name][f] = LIFT[name].get(f, 0.0) + 0.004 - z
    if LIFT[name] or TAIL_UP[name]:
        print(f"[{ID}] {name} floor fix: body lift max {max(LIFT[name].values(), default=0):.3f} m, tail raise max "
              f"{max(TAIL_UP[name].values(), default=0):.1f} deg (deepest before: {culprit}; lowest after {worst:.3f})")


def fit_die_to_floor(rig, body):
    """Solve the Die drop so the collapsed body rests on z=0 (lowest vertex at +1 cm)."""
    DIE_DROP[0] = Hh(0.2)
    low = 0.0
    for _ in range(12):
        act = bake(rig, "_Probe", LENGTHS["Die"], die)
        low = float(pose_points(rig, body, act, LENGTHS["Die"])[:, 2].min())
        rig.animation_data.action = None
        bpy.data.actions.remove(act)
        DIE_DROP[0] += low - 0.01
        DIE_DROP[0] = max(DIE_DROP[0], 0.0)
        if abs(low - 0.01) < 0.004:
            break
    print(f"[{ID}] Die drop {DIE_DROP[0]:.3f} m (last pose lowest vertex {low:.3f})")


def build():
    body = import_mesh()
    j = fit_skeleton(verts(body))
    rig = build_rig(j)
    counts = skin_weights(body, rig, j)
    print(f"[{ID}] mesh {len(body.data.vertices)} verts; joints paws "
          f"{ {k: tuple(round(c, 3) for c in v) for k, v in j['paws'].items()} } hip z {j['hz']:.3f}")
    print(f"[{ID}] vertices mostly on each bone: {json.dumps(counts)}")
    learn_rest(rig, j)
    rest = verts(body)
    REST["clear"] = float(rest[~dominant(body, ("leg.", "shin.", "paw."))][:, 2].min())
    print(f"[{ID}] belly clearance {REST['clear']:.3f} m")
    rig.animation_data_create()
    fit_attack_to_floor(rig, body)
    fit_die_to_floor(rig, body)
    for name in CLIPS:
        fit_floor(rig, body, name)
    for name, fn in CLIPS.items():
        bake(rig, name, LENGTHS[name], fn)
    for act in list(bpy.data.actions):
        if act.name not in CLIPS:
            bpy.data.actions.remove(act)
    lows = {}
    for name in CLIPS:
        act = bpy.data.actions[name]
        lows[name] = round(min(float(pose_points(rig, body, act, f)[:, 2].min()) for f in range(LENGTHS[name] + 1)), 3)
    print(f"[{ID}] lowest vertex per clip: {lows}")
    rig.animation_data.action = None
    for pb in rig.pose.bones:
        pb.location = (0, 0, 0)
        pb.rotation_euler = (0, 0, 0)
        pb.scale = (1, 1, 1)
    bpy.context.scene.frame_set(0)
    import textured as T
    path, tex_dir, textures = T.export_textured_fbx(REL_FBX, body, rig, max_size=TEX_SIZE)
    print(f"[{ID}] exported {path} ({os.path.getsize(path)} bytes); textures {json.dumps(textures)}")
    A.BLEND_DIR = os.path.join(SRC_DIR, "staging") if "--assets" not in ARGV else A.BLEND_DIR
    A.save_blend(f"boss_{ID}")
    return path


# ---------------------------------------------------------------- verification (fresh Blender)

def region_masks(pts):
    lo, hi = pts.min(0), pts.max(0)
    W, L, H = hi - lo
    m = {}
    for leg in LEGS:
        sx = 1.0 if leg[1] == "L" else -1.0
        sy = -1.0 if leg[0] == "F" else 1.0
        m[f"shin.{leg}"] = (pts[:, 2] < 0.15 * H) & (pts[:, 0] * sx > 0.1 * W) & (pts[:, 1] * sy > 0.1 * L)
    m["head"] = pts[:, 1] < lo[1] + 0.15 * L
    m["tail3"] = pts[:, 1] > hi[1] - 0.05 * L
    return m


def verify():
    bpy.ops.wm.read_factory_settings(use_empty=True)
    sc = bpy.context.scene
    sc.render.fps = A.FPS
    bpy.ops.import_scene.fbx(filepath=FBX)
    objs = list(sc.objects)
    problems = []
    rigs = [o for o in objs if o.type == "ARMATURE"]
    meshes = [o for o in objs if o.type == "MESH"]
    if [o.name for o in rigs] != ["Rig"]:
        problems.append(f"armatures {[o.name for o in rigs]}")
    if [o.name for o in meshes] != ["Body"]:
        problems.append(f"meshes {[o.name for o in meshes]}")
    rig, body = rigs[0], meshes[0]
    me = body.data
    rep = {"fbx": os.path.relpath(FBX, A.REPO).replace("\\", "/"),
           "triangles": sum(len(p.vertices) - 2 for p in me.polygons), "vertices": len(me.vertices),
           "bones": len(rig.data.bones), "materials": [m.name for m in me.materials],
           "color_attributes": [c.name for c in me.color_attributes]}
    if rep["materials"] != [ID]:
        problems.append(f"materials {rep['materials']}")
    png = os.path.join(os.path.dirname(FBX), f"{ID}_tex", f"{ID}.png")
    if not os.path.isfile(png):
        problems.append(f"missing {png}")
    if "Col" not in me.color_attributes:
        problems.append("no Col")
    unweighted = sum(not any(g.weight > 0 for g in v.groups) for v in me.vertices)
    rep["unweighted_vertices"] = unweighted
    if unweighted:
        problems.append(f"{unweighted} unweighted vertices")
    names = [g.name for g in body.vertex_groups]
    rep["vertex_groups"] = len(names)
    deform = [b.name for b in rig.data.bones if b.use_deform and b.name != "root"]
    missing = [b for b in deform if b not in names]
    if missing:
        problems.append(f"bones without a vertex group: {missing}")
    if not any(m.type == "ARMATURE" and m.object == rig for m in body.modifiers):
        problems.append("Body not skinned to Rig")

    paws = {leg: dominant(body, (f"paw.{leg}",)) for leg in LEGS}
    takes = {a.name.split("|")[-1]: a for a in bpy.data.actions}
    rep["takes"] = sorted(a.name for a in bpy.data.actions)
    if sorted(takes) != sorted(RANGES):
        problems.append(f"takes {sorted(takes)}")
    rep["clips"] = {}
    rig.animation_data_create()
    for name, (lo, hi) in RANGES.items():
        a = takes.get(name)
        if a is None:
            problems.append(f"missing take {name}")
            continue
        f0, f1 = (int(round(x)) for x in a.frame_range)
        info = {"frames": [f0, f1], "length": f1 - f0}
        if not lo <= f1 - f0 <= hi:
            problems.append(f"{name} length {f1 - f0} outside {lo}-{hi}")
        lows = []
        for f in range(f0, f1 + 1):
            p = pose_points(rig, body, a, f)
            lows.append(float(p[:, 2].min()))
            if f == f0:
                first = p
        if name in PLANTED:
            paw_lows = {leg: [] for leg in PLANTED[name]}
            for f in range(f0, f1 + 1):
                p = pose_points(rig, body, a, f)
                for leg in PLANTED[name]:
                    paw_lows[leg].append(float(p[paws[leg], 2].min()))
            lift = max(max(v) for v in paw_lows.values())
            info["planted_paw_max_lift"] = round(lift, 3)
            if lift > 0.03:
                problems.append(f"{name}: a planted paw lifts {lift:.3f} m off the floor")
        info["lowest_z"] = round(min(lows), 3)
        info["last_lowest_z"] = round(lows[-1], 3)
        if min(lows) < -0.025:
            problems.append(f"{name} sinks below the floor ({min(lows):.3f})")
        if name in ("Idle", "Run"):
            seam = float(np.abs(p - first).max())
            info["loop_seam_max_offset"] = round(seam, 4)
            if seam > 0.002:
                problems.append(f"{name} loop seam off by {seam:.4f} m")
        rep["clips"][name] = info
    if "Die" in takes and abs(rep["clips"]["Die"]["last_lowest_z"]) > 0.05:
        problems.append(f"Die does not end on the floor ({rep['clips']['Die']['last_lowest_z']})")

    # "Posing a bone moves its own region": each paw, the head tip and the tail tip must follow their bone.
    rig.animation_data.action = None
    modes = {pb.name: pb.rotation_mode for pb in rig.pose.bones}
    for pb in rig.pose.bones:
        pb.rotation_mode = "XYZ"
        pb.location = (0, 0, 0)
        pb.rotation_euler = (0, 0, 0)
    sc.frame_set(0)
    rest = mesh_points(body)
    rep["rest_bounds"] = [rest.min(0).round(3).tolist(), rest.max(0).round(3).tolist()]
    masks = region_masks(rest)
    probes = {f"leg.{leg}": f"shin.{leg}" for leg in LEGS}
    probes.update({"head": "head", "tail1": "tail3"})
    for bone, region in probes.items():
        pb = rig.pose.bones[bone]
        pb.rotation_euler = (math.radians(30), 0, 0)
        bpy.context.view_layer.update()
        moved = np.linalg.norm(mesh_points(body) - rest, axis=1)
        mask = masks[region]
        share = float((moved[mask] > 0.01).mean()) if mask.any() else 0.0
        rep[f"pose_{bone}_30deg"] = {"region_vertices": int(mask.sum()), "region_moved_share": round(share, 3),
                                    "verts_moved_1cm": int((moved > 0.01).sum())}
        if mask.sum() < 10:
            problems.append(f"region for {bone} is empty; check the mesh orientation (--yaw)")
        elif share < 0.8:
            problems.append(f"posing {bone} moves only {share:.0%} of its region")
        pb.rotation_euler = (0, 0, 0)
    for pb in rig.pose.bones:
        pb.rotation_mode = modes[pb.name]
    bpy.context.view_layer.update()
    rep["problems"] = problems
    os.makedirs(PREVIEW_DIR, exist_ok=True)
    with open(os.path.join(PREVIEW_DIR, "verify.json"), "w", encoding="utf-8") as fh:
        json.dump(rep, fh, ensure_ascii=False, indent=2)
    print(f"[{ID}] VERIFY " + json.dumps(rep, ensure_ascii=False), flush=True)
    render_previews(rig, body, takes)
    if problems:
        raise RuntimeError(problems)


MARKS = {"Attack": [0, 3, 6, 10, 14, 25], "Cast": [0, 12, 18, 21, 28, 35], "Die": [0, 5, 10, 16, 20, 30],
         "Victory": [0, 8, 14, 20, 26, 44], "Hit": [0, 2, 3, 5, 8, 12]}


def render_previews(rig, body, takes):
    sc = bpy.context.scene
    bpy.ops.mesh.primitive_plane_add(size=6.0, location=(0, 0, 0))
    floor = bpy.context.active_object
    floor.name = "PreviewFloor"
    fm = bpy.data.materials.new("PreviewFloor")
    fm.diffuse_color = (0.42, 0.44, 0.48, 1)
    floor.data.materials.append(fm)
    cam = bpy.data.objects.new("Cam", bpy.data.cameras.new("Cam"))
    sc.collection.objects.link(cam)
    sc.camera = cam
    cam.data.type = "ORTHO"
    sc.render.engine = "BLENDER_WORKBENCH"
    sh = sc.display.shading
    sh.light = "STUDIO"
    sh.color_type = "TEXTURE"
    sh.show_cavity = True
    sh.show_object_outline = True
    sc.view_settings.view_transform = "Standard"
    size = max(TARGET_H, *(np.ptp(mesh_points(body), 0)[:2])) * 1.35

    def shot(path, rot, res):
        cam.rotation_euler = Euler([math.radians(a) for a in rot])
        d = cam.rotation_euler.to_matrix() @ Vector((0, 0, 1))
        cam.location = Vector((0, 0, TARGET_H * 0.45)) + d * 8
        cam.data.ortho_scale = size
        sc.render.resolution_x = sc.render.resolution_y = res
        sc.render.filepath = path
        bpy.ops.render.render(write_still=True)

    def pixels(path):
        im = bpy.data.images.load(path, check_existing=False)
        a = np.empty(len(im.pixels), np.float32)
        im.pixels.foreach_get(a)
        a = a.reshape(im.size[1], im.size[0], 4)
        bpy.data.images.remove(im)
        os.remove(path)
        return a

    rig.animation_data.action = None
    sc.frame_set(0)
    shot(os.path.join(PREVIEW_DIR, "front.png"), (90, 0, 0), 800)
    shot(os.path.join(PREVIEW_DIR, "three_quarter.png"), (72, 0, 35), 800)
    shot(os.path.join(PREVIEW_DIR, "side.png"), (90, 0, 90), 800)
    cell, cols = 260, 6
    for view, rot in (("three_quarter", (75, 0, 35)), ("side", (88, 0, 90))):
        rows = []
        for name in RANGES:
            a = takes[name]
            f0, f1 = (int(round(x)) for x in a.frame_range)
            n = f1 - f0
            row = []
            for m in MARKS.get(name, [round(n * k / (cols - 1)) for k in range(cols)]):
                rig.animation_data.action = a
                sc.frame_set(f0 + m)
                tmp = os.path.join(PREVIEW_DIR, "_cell.png")
                shot(tmp, rot, cell)
                img = pixels(tmp)
                if (name == "Attack" and m == ATTACK_HIT) or (name == "Cast" and m == CAST_HIT):
                    img[:6, :, :3] = (1.0, 0.35, 0.2)
                row.append(img)
            rows.append(np.concatenate(row, axis=1))
        sheet = np.concatenate(rows[::-1], axis=0)
        out = bpy.data.images.new("sheet", sheet.shape[1], sheet.shape[0], alpha=True)
        out.pixels.foreach_set(sheet.ravel())
        out.filepath_raw = os.path.join(PREVIEW_DIR, f"clips_{view}.png")
        out.file_format = "PNG"
        out.save()
        bpy.data.images.remove(out)
    rig.animation_data.action = None
    print(f"[{ID}] previews in {PREVIEW_DIR}", flush=True)


def main():
    if "--verify" in ARGV:
        verify()
        return
    build()
    exe = arg("--blender", bpy.app.binary_path)
    cmd = [exe, "-b", "--factory-startup", "--python-exit-code", "1", "-P", os.path.abspath(__file__),
           "--", "--verify"] + (["--assets"] if "--assets" in ARGV else [])
    if not exe or not os.path.isfile(exe):          # bpy-as-a-module: verify in a fresh interpreter instead
        cmd = [sys.executable, os.path.abspath(__file__), "--", "--verify"] + (["--assets"] if "--assets" in ARGV else [])
    r = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8", errors="replace")
    for line in r.stdout.splitlines():
        if line.startswith(f"[{ID}]") or "Error" in line or "Traceback" in line:
            print(line)
    if r.returncode != 0:
        print(r.stderr[-4000:])
        raise RuntimeError("verification failed")


if __name__ == "__main__":
    main()
