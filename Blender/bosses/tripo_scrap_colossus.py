"""scrap_colossus (고철 거상) — zone-3 hunter boss from a Tripo Studio model.

Source (not generated here): ArtSource/hunter-bosses/scrap_colossus/tripo_export/tripo_convert_*.fbx + .fbm textures
(ChatGPT web concept -> Tripo Studio image-to-3D, Retopo 11.4k tris, Auto Rig Humanoid/Mixamo; see candidates/prompts.md).

Same approach as tripo_subway_bat_lord.py, turned into the art contract (Blender/README.md):
- armature object `Rig` + one skinned mesh `Body`; Tripo's skin weights and Mixamo bone names (mixamorig:*) are kept,
- one material `scrap_colossus` whose base colour is written to
  Enemies/scrap_colossus/scrap_colossus_tex/scrap_colossus.png (lib_humanoid/textured.py -> Unity TexturedMaterials),
  plus a white `Col` attribute (Abyss/Toon multiplies vertex colour into the albedo),
- scaled so its height matches the elite_sand_golem model it replaces (top ~1.54 m), standing on z=0, facing -Y,
- seven baked actions Idle/Run/Attack/Cast/Hit/Die/Victory (30 fps, README lengths, Attack slam at 40 %, Cast flare
  at 60 %, Die holds a collapsed heap on the floor). It is a heavy biped: the feet are pinned to the floor with an
  analytic two-bone leg IK (hip drop / lean bend the knees instead of pushing the soles through the floor).

Output goes to ArtSource/hunter-bosses/scrap_colossus/staging/ (mirrors Assets/...) unless `--assets` is given,
because the Unity project may be open; copy the staged files into Assets/ afterwards.

Run (repo root):
  C:/Users/User/Tools/Blender/blender.exe -b --factory-startup --python-exit-code 1 -P Blender/bosses/tripo_scrap_colossus.py
  ... -- --assets        write straight into Assets/_Game/Resources/Art instead of staging/
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
import _common as C  # noqa: E402
import abyss_bpy as A  # noqa: E402

import bpy  # noqa: E402
import numpy as np  # noqa: E402
from mathutils import Euler, Matrix, Vector  # noqa: E402

ID = "scrap_colossus"
SRC_DIR = os.path.join(A.REPO, "ArtSource", "hunter-bosses", ID)
PREVIEW_DIR = os.path.join(SRC_DIR, "preview")
STAGING = os.path.join(SRC_DIR, "staging")
ARGV = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
if "--assets" not in ARGV:
    # textured.export_textured_fbx / A.export_fbx resolve paths against A.ASSETS at call time.
    A.ASSETS = os.path.join(STAGING, "Assets", "_Game", "Resources", "Art")
REL_FBX = f"Enemies/{ID}/{ID}.fbx"
FBX = os.path.join(A.ASSETS, REL_FBX)
TEX_SIZE = 1024            # Unity caps _tex PNGs at 1024 (AbyssArtImporter.OnPreprocessTexture)

# Scale. elite_sand_golem (the model this replaces) spans 1.20 x 0.59 x z 0.005..1.54 m in its rest pose.
# The Tripo colossus is 0.98 x 0.46 x 0.973 m with its feet at z=0: x1.583 tops out at 1.54 m (1.55 m wide).
SCALE = 1.583

# README lengths (frames at 30 fps).
LENGTHS = {"Idle": 48, "Run": 20, "Attack": 30, "Cast": 35, "Hit": 12, "Die": 34, "Victory": 44}
RANGES = {"Idle": (40, 60), "Run": (16, 24), "Attack": (18, 30), "Cast": (30, 40), "Hit": (10, 14),
          "Die": (24, 36), "Victory": (36, 48)}
ATTACK_HIT = 12            # 40 % of 30
CAST_HIT = 21              # 60 % of 35
PFX = "mixamorig:"
SIDES = (("Left", 1.0), ("Right", -1.0))   # character's left is +X
ARM_BONES = ("ForeArm", "Hand")            # the fists are weighted to the forearm, hand and finger bones


def B(name):
    return PFX + name


def source_fbx():
    hits = sorted(glob.glob(os.path.join(SRC_DIR, "tripo_export", "*.fbx")))
    if len(hits) != 1:
        raise RuntimeError(f"expected one Tripo FBX in tripo_export/, found {hits}")
    return hits[0]


# ---------------------------------------------------------------- import + contract

def build_model():
    A.reset_scene()
    for name in A.MATERIALS:          # textured model: no shared slots
        bpy.data.materials.remove(bpy.data.materials[name])
    bpy.ops.import_scene.fbx(filepath=source_fbx())
    objs = list(bpy.context.scene.objects)
    rig = next(o for o in objs if o.type == "ARMATURE")
    body = next(o for o in objs if o.type == "MESH")
    assert len(objs) == 2, [o.name for o in objs]
    rig.name = rig.data.name = "Rig"
    body.name = body.data.name = "Body"

    # Bake the scale into the rest pose (mesh and bones), then re-parent without an inverse.
    body.parent = None
    for o in (rig, body):
        o.matrix_world = Matrix.Identity(4)
        o.scale = (SCALE, SCALE, SCALE)
        A.apply_transform(o)
    body.parent = rig
    body.matrix_parent_inverse.identity()
    mods = [m for m in body.modifiers if m.type == "ARMATURE"]
    assert len(mods) == 1
    mods[0].object = rig
    for pb in rig.pose.bones:
        pb.rotation_mode = "XYZ"
    low = min(v.co.z for v in body.data.vertices)
    assert abs(low) < 0.005, f"feet not on the floor ({low:.4f})"

    # One material named after the enemy, carrying only the base colour (normal/roughness/metal maps are dropped:
    # Abyss/Toon shades from _BaseMap and vertex colour only).
    src = body.data.materials[0]
    base = next(n.image for n in src.node_tree.nodes if n.type == "TEX_IMAGE" and "basecolor" in n.image.name.lower())
    base.colorspace_settings.name = "sRGB"
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
    bpy.data.materials.remove(src)
    for img in list(bpy.data.images):
        if img != base and img.users == 0:
            bpy.data.images.remove(img)

    # White vertex colour: Abyss/Toon multiplies Col into the albedo; render_icons needs the attribute.
    col = body.data.color_attributes.new("Col", "BYTE_COLOR", "CORNER")
    col.data.foreach_set("color", [1.0] * (4 * len(col.data)))
    body.data.color_attributes.active_color = col
    return rig, body


# ---------------------------------------------------------------- pose vocabulary (armature axes, degrees, metres)
# Character faces -Y, its left is +X. For an up-pointing bone +X rot pitches it forward; for a hanging limb +X swings
# its tip backward. C.bake composes child rotations in the parent's posed frame (plain FK).

REST = {}      # filled by learn_rest(): joint heads (armature space) and leg chain angles


def psi(v):
    """Angle of a vector in the side (Y/Z) plane, degrees; straight down = -90, forward (-Y) = +-180."""
    return math.degrees(math.atan2(v.z, v.y))


def learn_rest(rig):
    bones = rig.data.bones
    REST["hips"] = bones[B("Hips")].head_local.copy()
    for side, _ in SIDES:
        hip, knee, ankle = (bones[B(side + n)].head_local.copy() for n in ("UpLeg", "Leg", "Foot"))
        t, c = knee - hip, ankle - knee
        REST[side] = dict(hip=hip, ankle=ankle, L1=Vector((0, t.y, t.z)).length, L2=Vector((0, c.y, c.z)).length,
                          psi1=psi(t), psi2=psi(c))
    REST["bones"] = {b.name for b in bones}


def hip_joint(side, loc, pitch):
    h = REST["hips"]
    return h + Vector(loc) + Matrix.Rotation(math.radians(pitch), 3, "X") @ (REST[side]["hip"] - h)


def leg_ik(side, hip, ankle):
    """World side-plane angle deltas (thigh, calf) that put the ankle at `ankle`, knee bending forward."""
    r = REST[side]
    L1, L2 = r["L1"], r["L2"]
    d = Vector((0, ankle.y - hip.y, ankle.z - hip.z))
    dist = min(d.length, (L1 + L2) * 0.9999)
    cos_a = (L1 * L1 + dist * dist - L2 * L2) / (2 * L1 * dist)
    alpha = math.degrees(math.acos(max(-1.0, min(1.0, cos_a))))
    th = psi(d) - alpha
    knee = hip + Vector((0, math.cos(math.radians(th)), math.sin(math.radians(th)))) * L1
    ca = psi(ankle - knee)
    return th - r["psi1"], ca - r["psi2"]


def leg_world(P, side, th, ca, ft, pitch, spread=0.0):
    """Leg from world side-plane deltas (degrees from rest): thigh, calf, foot; pitch = hips pitch."""
    sgn = 1.0 if side == "Left" else -1.0
    P.r(B(side + "UpLeg"), (th - pitch, -sgn * spread, 0))
    P.r(B(side + "Leg"), (ca - th, 0, 0))
    P.r(B(side + "Foot"), (ft - ca, sgn * spread, 0))


FOOT_K = [0.4]   # toe lift per degree of shin tilt: the toes carry some calf weight and would dip into the floor


def stance(P, loc=(0, 0, 0), pitch=0.0, feet=None):
    """Hips location/pitch with both feet pinned by IK. feet: {side: (dy, dz, foot pitch)} ankle offsets from rest."""
    feet = feet or {}
    P.l(B("Hips"), loc)
    P.r(B("Hips"), (pitch, 0, 0))
    angles = {}
    for side, _ in SIDES:
        dy, dz, fp = feet.get(side, (0.0, 0.0, 0.0))
        ankle = REST[side]["ankle"] + Vector((0, dy, dz))
        th, ca = leg_ik(side, hip_joint(side, loc, pitch), ankle)
        leg_world(P, side, th, ca, fp - FOOT_K[0] * ca, pitch)
        angles[side] = (th, ca, fp)
    return angles


def torso(P, bend=0.0, side=0.0, twist=0.0, head=0.0):
    """bend > 0 curls the boiler body forward, side > 0 leans toward its left (+X), twist > 0 turns it left,
    head > 0 nods the dome down (kept moderate: the Head bone carries the whole dome)."""
    P.r(B("Spine"), (bend * 0.55, side * 0.6, twist * 0.5))
    P.r(B("Spine1"), (bend * 0.25, side * 0.2, twist * 0.25))
    P.r(B("Spine2"), (bend * 0.20, side * 0.2, twist * 0.25))
    P.r(B("Neck"), (head * 0.4, 0, 0))
    P.r(B("Head"), (head * 0.6, 0, 0))


def arm(P, side, fwd=0.0, out=0.0, elbow=0.0, shrug=0.0, twist=0.0):
    """fwd > 0 swings the arm forward/up (180 = straight up), out > 0 opens it sideways (applied first, in the rest
    frame), elbow > 0 bends the forearm forward, shrug > 0 lifts the shoulder pad."""
    sgn = 1.0 if side == "Left" else -1.0
    P.r(B(side + "Shoulder"), (0, -sgn * shrug, 0))
    R = Matrix.Rotation(math.radians(-fwd), 3, "X") @ Matrix.Rotation(math.radians(-sgn * out), 3, "Y")
    R = R @ Matrix.Rotation(math.radians(sgn * twist), 3, "Z")
    P.r(B(side + "Arm"), tuple(math.degrees(a) for a in R.to_euler("XYZ")))
    P.r(B(side + "ForeArm"), (-elbow, 0, 0))


def arms(P, fwd=0.0, out=0.0, elbow=0.0, shrug=0.0, twist=0.0):
    for side, _ in SIDES:
        arm(P, side, fwd, out, elbow, shrug, twist)


K = C.K
TAU = math.tau


# ---------------------------------------------------------------- clips

def idle(P, f, t):
    # One slow breath per loop: the boiler body swells back and the shoulder pads rise; a slight side-to-side sway.
    br = 0.5 - 0.5 * math.cos(TAU * t)                 # 0 -> 1 -> 0
    sway = math.sin(TAU * t)
    stance(P, loc=(0.0, 0.0, -0.012 - 0.018 * br))
    torso(P, bend=2.0 - 4.0 * br, side=2.0 * sway, twist=1.5 * math.sin(TAU * t - 0.8), head=1.5 - 3.5 * br)
    for side, sgn in SIDES:
        arm(P, side, fwd=4 + 3 * math.sin(TAU * t + 0.6 * sgn), out=3 + 3 * br, elbow=8 + 4 * br, shrug=5 * br)


RUN_STRIDE = 0.15
RUN_LIFT = 0.13


def run_foot(phase):
    """(dy, dz, foot pitch) of one ankle over a lumbering step cycle; stance 0..0.55 slides back flat."""
    p = phase % 1.0
    if p < 0.55:
        u = p / 0.55
        return (-RUN_STRIDE + 2 * RUN_STRIDE * u, 0.0, 0.0)
    u = (p - 0.55) / 0.45
    s = 0.5 - 0.5 * math.cos(math.pi * u)
    return (RUN_STRIDE - 2 * RUN_STRIDE * s, RUN_LIFT * math.sin(math.pi * u), 12 * math.sin(math.pi * u))


def run(P, f, t):
    # Heavy jog: two stomps per loop, the hips drop after each foot lands, the body rolls over the stance leg.
    feet = {"Left": run_foot(t), "Right": run_foot(t + 0.5)}
    bob = math.cos(TAU * 2 * (t - 0.08))
    stance(P, loc=(0.0, 0.0, -0.07 - 0.03 * bob), pitch=5.0, feet=feet)
    torso(P, bend=9 + 2 * bob, side=-4 * math.sin(TAU * t), twist=7 * math.sin(TAU * t), head=-6)
    for side, sgn in SIDES:
        dy = feet[side][0]
        arm(P, side, fwd=12 + 24 * dy / RUN_STRIDE, out=7, elbow=28 + 8 * dy / RUN_STRIDE, shrug=3 * bob)


ATTACK_REACH = [55.0]   # arm swing at impact, solved by fit_attack_to_floor()


def attack(P, f, t):
    # Wind-up (0-9) both fists high behind the dome, leaning back; slam down (9-12): double-fist impact on the floor
    # in front at frame 12 (40 %), shudder (12-16), heave back up (16-30).
    fr = (0, 9, 12, 16, 30)
    keys = lambda *v: K(f, *zip(fr, v))  # noqa: E731
    shake = math.sin(f * 3.1) * (1.0 if ATTACK_HIT <= f <= 16 else 0.0) * (1 - (f - ATTACK_HIT) / 5.0)
    reach = ATTACK_REACH[0]
    stance(P, loc=(0, keys(0, 0.05, -0.06, -0.06, 0), keys(0, -0.03, -0.17, -0.16, 0) + 0.01 * shake),
           pitch=keys(0, -5, 12, 11, 0))
    torso(P, bend=keys(0, -16, 30, 27, 0), head=keys(0, -10, 10, 8, 0) + 2 * shake)
    arms(P, fwd=keys(0, 168, reach, reach - 2, 0), out=keys(0, -14, 4, 4, 0), elbow=keys(0, 35, 4, 8, 0),
         shrug=keys(0, 14, -4, -3, 0))


def cast(P, f, t):
    # Gather (0-12): hunch over the chest core, arms drawn down and back; draw in (12-18); flare at frame 21 (60 %):
    # chest thrust out, arms flung wide, dome up; tremble to 28, settle by 35.
    fr = (0, 12, 18, 21, 28, 35)
    keys = lambda *v: K(f, *zip(fr, v))  # noqa: E731
    shake = math.sin(f * 2.7) * (1.0 if CAST_HIT <= f <= 28 else 0.0) * (1 - (f - CAST_HIT) / 8.0)
    stance(P, loc=(0, keys(0, 0.02, 0.01, 0.03, 0.03, 0), keys(0, -0.08, -0.05, -0.04, -0.04, 0)),
           pitch=keys(0, 6, 0, -4, -3, 0))
    torso(P, bend=keys(0, 18, 4, -14, -12, 0) + 1.5 * shake, head=keys(0, 12, 0, -14, -12, 0))
    arms(P, fwd=keys(0, -20, -8, 12, 10, 0), out=keys(0, 14, 30, 72, 68, 0) + 3 * shake,
         elbow=keys(0, 22, 18, 8, 10, 0), shrug=keys(0, -4, 6, 14, 12, 0))


def hit(P, f, t):
    # Rocked back at frame 3 (body staggers, arms flung out), recovers by 12; the feet stay planted.
    fr = (0, 3, 7, 12)
    keys = lambda *v: K(f, *zip(fr, v))  # noqa: E731
    stance(P, loc=(0, keys(0, 0.07, 0.03, 0), keys(0, -0.04, -0.02, 0)), pitch=keys(0, -5, -2, 0))
    torso(P, bend=keys(0, -15, -5, 0), side=keys(0, 5, 2, 0), twist=keys(0, 7, 2, 0), head=keys(0, -12, -4, 0))
    for side, sgn in SIDES:
        arm(P, side, fwd=keys(0, -14, -4, 0), out=keys(0, 20 + 4 * sgn, 7, 0), elbow=keys(0, 16, 6, 0),
            shrug=keys(0, 8, 3, 0))


DIE_DROP = [0.0]        # final hips drop, set by fit_die_to_floor()
# Final heap (world side-plane degrees from rest): hips pitch, spine bend, leg chain, arm pose.
DIE = dict(pitch=80, bend=12, head=12, thigh=75, calf=85, foot=140, spread=12, y=-0.25,
           fwd=10, out=80, elbow=45, shrug=10)
DIE_LIFT = {}           # per-frame hips lift that keeps the falling body above the floor, set by fit_die_to_floor()


def die(P, f, t):
    # Rocked (0-4), the knees buckle (4-12), it pitches forward over its knees and slams down onto its belly
    # (12-22), bounces (25) and lies as a heap of scrap from frame 28.
    fr = (0, 4, 12, 22, 25, 28, 34)
    keys = lambda *v: K(f, *zip(fr, v))  # noqa: E731
    d, drop = DIE, DIE_DROP[0]
    loc = keys((0, 0, 0), (0, 0.06, -0.02), (0, 0.02, -0.20), (0, d["y"], -drop), (0, d["y"], -drop + 0.03),
               (0, d["y"], -drop), (0, d["y"], -drop))
    loc = (loc[0], loc[1], loc[2] + DIE_LIFT.get(f, 0.0))
    pitch = keys(0, -6, 6, d["pitch"], d["pitch"] - 2, d["pitch"], d["pitch"])
    if f <= 12:
        stance(P, loc=loc, pitch=pitch)
    else:
        P.l(B("Hips"), loc)
        P.r(B("Hips"), (pitch, 0, 0))
        u = C.smooth((f - 12) / 10.0)
        fold = 45 * math.sin(math.pi * u)        # shins fold up while the legs swing back, so the feet clear the floor
        for side, _ in SIDES:
            th0, ca0 = leg_ik(side, hip_joint(side, (0, 0.02, -0.20), 6), REST[side]["ankle"])
            ft0 = -FOOT_K[0] * ca0
            leg_world(P, side, th0 + (d["thigh"] - th0) * u, ca0 + (d["calf"] - ca0) * u + fold, ft0 + (d["foot"] - ft0) * u,
                      pitch, spread=d["spread"] * u)
    torso(P, bend=keys(0, -12, 10, d["bend"], d["bend"] - 4, d["bend"], d["bend"]), side=keys(0, 3, 4, 6, 6, 6, 6),
          twist=keys(0, 4, 2, -5, -5, -5, -5), head=keys(0, -10, 8, d["head"], d["head"] - 4, d["head"], d["head"]))
    for side, sgn in SIDES:
        arm(P, side, fwd=keys(0, -12, 20, d["fwd"], d["fwd"] - 4, d["fwd"], d["fwd"]),
            out=keys(0, 16, 10, d["out"] + 4 * sgn, d["out"] + 2, d["out"], d["out"]),
            elbow=keys(0, 14, 10, d["elbow"], d["elbow"] - 4, d["elbow"], d["elbow"]),
            shrug=keys(0, 6, -4, d["shrug"], d["shrug"] - 2, d["shrug"], d["shrug"]))


def victory(P, f, t):
    # Crouch (0-8), both fists thrust up (14), pumped twice (20/26), then a proud raised-fists pose (32-44).
    fr = (0, 8, 14, 20, 26, 32, 44)
    keys = lambda *v: K(f, *zip(fr, v))  # noqa: E731
    stance(P, loc=(0, keys(0, 0.02, 0, 0.01, 0, 0, 0), keys(0, -0.08, -0.01, -0.05, -0.01, -0.02, -0.02)),
           pitch=keys(0, 6, -4, 1, -4, -3, -3))
    torso(P, bend=keys(0, 12, -12, -4, -14, -10, -10), head=keys(0, 8, -14, -6, -16, -12, -12))
    arms(P, fwd=keys(0, 18, 162, 140, 165, 156, 156), out=keys(0, 10, 12, 16, 12, 14, 14),
         elbow=keys(0, 30, 28, 72, 24, 34, 34), shrug=keys(0, 0, 12, 6, 14, 12, 12))


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


def fist_mask(body):
    """Vertices whose strongest bone is a forearm / hand / finger bone (the big fists)."""
    names = [g.name for g in body.vertex_groups]
    arm_groups = {i for i, n in enumerate(names) if any(k in n for k in ARM_BONES)}
    mask = np.zeros(len(body.data.vertices), bool)
    for v in body.data.vertices:
        if v.groups:
            g = max(v.groups, key=lambda g: g.weight)
            mask[v.index] = g.group in arm_groups
    return mask


def pose_points(rig, body, action, frame):
    rig.animation_data.action = action
    bpy.context.scene.frame_set(frame)
    return mesh_points(body)


def probe(rig, body, name, frame, fn=None):
    act = C.bake(rig, "_Probe", LENGTHS[name], fn or CLIPS[name])
    pts = pose_points(rig, body, act, frame)
    rig.animation_data.action = None
    bpy.data.actions.remove(act)
    return pts


def fit_attack_to_floor(rig, body):
    """Solve the arm swing at impact so the lowest fist vertex touches the floor (+1 cm) at frame 12."""
    mask = fist_mask(body)
    lo, hi = 0.0, 100.0            # fist height rises with the swing angle on this range (hanging -> level)
    for _ in range(14):
        ATTACK_REACH[0] = 0.5 * (lo + hi)
        z = float(probe(rig, body, "Attack", ATTACK_HIT)[mask, 2].min())
        if abs(z - 0.01) < 0.003:
            break
        if z > 0.01:
            hi = ATTACK_REACH[0]
        else:
            lo = ATTACK_REACH[0]
    print(f"[{ID}] Attack impact swing {ATTACK_REACH[0]:.1f} deg (lowest fist vertex {z:.3f})")


def fit_die_to_floor(rig, body):
    """Solve the Die drop so the collapsed heap rests on z=0 (lowest vertex at +1 cm)."""
    DIE_DROP[0] = 0.25
    DIE_LIFT.clear()
    for _ in range(12):
        low = float(probe(rig, body, "Die", LENGTHS["Die"])[:, 2].min())
        DIE_DROP[0] += low - 0.01
        if abs(low - 0.01) < 0.003:
            break
    print(f"[{ID}] Die drop {DIE_DROP[0]:.3f} m (last pose lowest vertex {low:.3f})")
    # Then lift the hips on any falling frame whose lowest vertex would pass through the floor.
    for _ in range(4):
        act = C.bake(rig, "_DieProbe", LENGTHS["Die"], die)
        lows = [float(pose_points(rig, body, act, f)[:, 2].min()) for f in range(LENGTHS["Die"] + 1)]
        rig.animation_data.action = None
        bpy.data.actions.remove(act)
        worst = min(lows)
        if worst > -0.004:
            break
        for f, z in enumerate(lows):
            if z < -0.002:
                DIE_LIFT[f] = DIE_LIFT.get(f, 0.0) + 0.004 - z
    print(f"[{ID}] Die lift per frame {{{', '.join(f'{f}: {v:.3f}' for f, v in sorted(DIE_LIFT.items()))}}} "
          f"(lowest vertex over the clip {worst:.3f})")


def build():
    rig, body_obj = build_model()
    learn_rest(rig)
    rig.animation_data_create()
    fit_attack_to_floor(rig, body_obj)
    fit_die_to_floor(rig, body_obj)
    for name, fn in CLIPS.items():
        C.bake(rig, name, LENGTHS[name], fn)
    for act in list(bpy.data.actions):
        if act.name not in CLIPS:
            bpy.data.actions.remove(act)
    assert sorted(a.name for a in bpy.data.actions) == sorted(CLIPS), [a.name for a in bpy.data.actions]
    lows = {}
    for name in CLIPS:
        act = bpy.data.actions[name]
        lows[name] = round(min(float(pose_points(rig, body_obj, act, f)[:, 2].min())
                               for f in range(LENGTHS[name] + 1)), 3)
    print(f"[{ID}] lowest vertex per clip: {lows}")
    rig.animation_data.action = None
    for pb in rig.pose.bones:
        pb.location = (0, 0, 0)
        pb.rotation_euler = (0, 0, 0)
        pb.scale = (1, 1, 1)
    bpy.context.scene.frame_set(0)
    import textured as T
    path, tex_dir, textures = T.export_textured_fbx(REL_FBX, body_obj, rig, max_size=TEX_SIZE)
    print(f"[{ID}] exported {path} ({os.path.getsize(path)} bytes); textures {json.dumps(textures)}")
    A.save_blend(f"boss_{ID}")
    return path


# ---------------------------------------------------------------- verification (fresh Blender)

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
    rig, body_obj = rigs[0], meshes[0]
    me = body_obj.data
    rep = {"fbx": os.path.relpath(FBX, A.REPO).replace("\\", "/"),
           "triangles": sum(len(p.vertices) - 2 for p in me.polygons), "vertices": len(me.vertices),
           "bones": len(rig.data.bones), "materials": [m.name for m in me.materials],
           "color_attributes": [c.name for c in me.color_attributes]}
    if rep["materials"] != [ID]:
        problems.append(f"materials {rep['materials']}")
    imgs = [n.image for n in me.materials[0].node_tree.nodes if n.type == "TEX_IMAGE" and n.image]
    rep["texture"] = [bpy.path.abspath(i.filepath) for i in imgs]
    png = os.path.join(os.path.dirname(FBX), f"{ID}_tex", f"{ID}.png")
    if not os.path.isfile(png):
        problems.append(f"missing {png}")
    else:
        im = bpy.data.images.load(png)
        rep["texture_png"] = {"path": os.path.relpath(png, A.REPO).replace("\\", "/"), "size": list(im.size)}
        if not any(os.path.normcase(os.path.abspath(p)) == os.path.normcase(png) for p in rep["texture"]):
            problems.append(f"FBX texture reference {rep['texture']} is not {png}")
    if "Col" not in me.color_attributes:
        problems.append("no Col")
    unweighted = sum(not any(g.weight > 0 for g in v.groups) for v in me.vertices)
    rep["unweighted_vertices"] = unweighted
    if unweighted:
        problems.append(f"{unweighted} unweighted vertices")
    if not any(m.type == "ARMATURE" and m.object == rig for m in body_obj.modifiers):
        problems.append("Body not skinned to Rig")

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
        lows, tops = [], []
        for f in range(f0, f1 + 1):
            rig.animation_data.action = a
            sc.frame_set(f)
            p = mesh_points(body_obj)
            lows.append(float(p[:, 2].min()))
            tops.append(float(p[:, 2].max()))
            if f == f0:
                first = p
        info["lowest_z"] = round(min(lows), 3)
        info["highest_z"] = round(max(tops), 3)
        info["last_lowest_z"] = round(lows[-1], 3)
        if min(lows) < -0.02:
            problems.append(f"{name} sinks below the floor ({min(lows):.3f})")
        if name in ("Idle", "Run"):
            seam = float(np.abs(p - first).max())
            info["loop_seam_max_offset"] = round(seam, 4)
            if seam > 0.002:
                problems.append(f"{name} loop seam off by {seam:.4f} m")
        rep["clips"][name] = info
    if "Die" in takes and abs(rep["clips"]["Die"]["last_lowest_z"]) > 0.05:
        problems.append(f"Die does not end on the floor ({rep['clips']['Die']['last_lowest_z']})")
    if "Attack" in takes:
        a = takes["Attack"]
        rig.animation_data.action = a
        sc.frame_set(int(round(a.frame_range[0])) + ATTACK_HIT)
        z = float(mesh_points(body_obj)[fist_mask(body_obj), 2].min())
        rep["clips"]["Attack"]["fist_lowest_z_at_impact"] = round(z, 3)
        if not -0.02 <= z <= 0.06:
            problems.append(f"Attack fists do not reach the floor at impact ({z:.3f})")

    # Rest pose size + "posing a bone moves the mesh".
    rig.animation_data.action = None
    modes = {pb.name: pb.rotation_mode for pb in rig.pose.bones}   # imported takes key quaternions
    for pb in rig.pose.bones:
        pb.rotation_mode = "XYZ"
        pb.location = (0, 0, 0)
        pb.rotation_euler = (0, 0, 0)
    sc.frame_set(0)
    rest = mesh_points(body_obj)
    rep["rest_bounds"] = [rest.min(0).round(3).tolist(), rest.max(0).round(3).tolist()]
    for bone in ("LeftArm", "RightForeArm", "Head", "Spine", "LeftUpLeg", "RightLeg"):
        pb = rig.pose.bones[B(bone)]
        pb.rotation_euler = (math.radians(30), 0, 0)
        bpy.context.view_layer.update()
        moved = np.linalg.norm(mesh_points(body_obj) - rest, axis=1)
        rep[f"pose_{bone}_30deg"] = {"verts_moved_1cm": int((moved > 0.01).sum()), "max_move_m": round(float(moved.max()), 3)}
        if (moved > 0.01).sum() < 100:
            problems.append(f"posing {bone} barely moves the mesh")
        pb.rotation_euler = (0, 0, 0)
    for pb in rig.pose.bones:
        pb.rotation_mode = modes[pb.name]
    bpy.context.view_layer.update()
    rep["problems"] = problems
    print(f"[{ID}] VERIFY " + json.dumps(rep, ensure_ascii=False), flush=True)
    render_previews(rig, body_obj, takes)
    if problems:
        raise RuntimeError(problems)


MARKS = {"Attack": [0, 5, 9, 12, 16, 30], "Cast": [0, 12, 18, 21, 28, 35], "Die": [0, 4, 12, 17, 22, 34],
         "Victory": [0, 8, 14, 20, 26, 44], "Hit": [0, 2, 3, 5, 8, 12]}


def render_previews(rig, body_obj, takes):
    sc = bpy.context.scene
    os.makedirs(PREVIEW_DIR, exist_ok=True)
    bpy.ops.mesh.primitive_plane_add(size=4.0, location=(0, 0, 0))
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
    sh.show_shadows = False
    sc.view_settings.view_transform = "Standard"
    sc.render.film_transparent = False

    def shot(path, rot, center, ortho, size):
        cam.rotation_euler = Euler([math.radians(a) for a in rot])
        d = cam.rotation_euler.to_matrix() @ Vector((0, 0, 1))
        cam.location = Vector(center) + d * 8
        cam.data.ortho_scale = ortho
        sc.render.resolution_x = sc.render.resolution_y = size
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

    center = (0, 0, 0.8)
    rig.animation_data.action = None
    sc.frame_set(0)
    shot(os.path.join(PREVIEW_DIR, "front.png"), (90, 0, 0), center, 1.9, 900)
    shot(os.path.join(PREVIEW_DIR, "three_quarter.png"), (78, 0, 32), center, 2.0, 900)
    shot(os.path.join(PREVIEW_DIR, "side.png"), (90, 0, 90), center, 1.9, 900)

    cell = 300
    cols = 6
    for view, rot in (("front", (80, 0, 20)), ("side", (88, 0, 90))):
        rows = []
        for name in RANGES:
            a = takes[name]
            f0, f1 = (int(round(x)) for x in a.frame_range)
            n = f1 - f0
            marks = MARKS.get(name, [round(n * k / (cols - 1)) for k in range(cols)])
            row = []
            for m in marks:
                rig.animation_data.action = a
                sc.frame_set(f0 + m)
                tmp = os.path.join(PREVIEW_DIR, "_cell.png")
                shot(tmp, rot, (0, 0, 0.95), 2.5, cell)
                img = pixels(tmp)
                # key-moment tick: orange strip at the bottom marks Attack 40 % / Cast 60 %
                if (name == "Attack" and m == ATTACK_HIT) or (name == "Cast" and m == CAST_HIT):
                    img[:6, :, :3] = (1.0, 0.35, 0.2)
                row.append(img)
            rows.append(np.concatenate(row, axis=1))
        sheet = np.concatenate(rows[::-1], axis=0)   # Blender pixel rows go bottom-up: first clip on top
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
    cmd = [bpy.app.binary_path, "-b", "--factory-startup", "--python-exit-code", "1", "-P", os.path.abspath(__file__),
           "--", "--verify"] + (["--assets"] if "--assets" in ARGV else [])
    r = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8", errors="replace")
    for line in r.stdout.splitlines():
        if line.startswith(f"[{ID}]") or "Error" in line or "Traceback" in line:
            print(line)
    if r.returncode != 0:
        print(r.stderr[-4000:])
        raise RuntimeError("verification failed")


if __name__ == "__main__":
    main()
