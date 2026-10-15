"""subway_bat_lord (지하철 박쥐 군주) — zone-1 hunter boss from a Tripo Studio model.

Source (not generated here): ArtSource/hunter-bosses/subway_bat_lord/tripo_export/tripo_convert_*.fbx + .fbm textures
(ChatGPT web concept -> Tripo Studio image-to-3D, Retopo 16k tris, Auto Rig "Other"; see candidates/prompts.md).

This script turns that export into the art contract (Blender/README.md):
- armature object `Rig` + one skinned mesh `Body`; Tripo's skin weights are kept as they are (no re-weighting),
- one material `subway_bat_lord` whose base colour is written to
  Enemies/subway_bat_lord/subway_bat_lord_tex/subway_bat_lord.png (lib_humanoid/textured.py -> Unity TexturedMaterials),
  plus a white `Col` attribute (Abyss/Toon multiplies vertex colour into the albedo),
- scaled so its battle height matches the elite_bat model it replaces (top ~1.41 m) and hovering above z=0 in the rest pose,
- seven baked actions Idle/Run/Attack/Cast/Hit/Die/Victory (30 fps, README lengths, Attack hit at 40 %, Cast release at
  60 %, Die holds a collapsed pose on the floor), keyed on Tripo's own bones via bosses/_common.bake.

Run (repo root):
  C:/Users/User/Tools/Blender/blender.exe -b --factory-startup --python-exit-code 1 -P Blender/bosses/tripo_subway_bat_lord.py
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
from mathutils import Euler, Vector  # noqa: E402

ID = "subway_bat_lord"
SRC_DIR = os.path.join(A.REPO, "ArtSource", "hunter-bosses", ID)
PREVIEW_DIR = os.path.join(SRC_DIR, "preview")
REL_FBX = f"Enemies/{ID}/{ID}.fbx"
FBX = os.path.join(A.ASSETS, REL_FBX)
TEX_SIZE = 1024            # Unity caps _tex PNGs at 1024 (AbyssArtImporter.OnPreprocessTexture)

# Scale / hover. elite_bat (the model this replaces) spans z 0.76..1.41 m, 1.64 m wingspan, in its rest pose.
# The Tripo bat is 0.98 x 0.50 x 0.89 m with its feet at z=0: x1.25 and lifted 0.35 m it tops out at ~1.46 m.
SCALE = 1.25
HOVER = 0.35

# README lengths (frames at 30 fps).
LENGTHS = {"Idle": 48, "Run": 20, "Attack": 25, "Cast": 35, "Hit": 12, "Die": 30, "Victory": 44}
RANGES = {"Idle": (40, 60), "Run": (16, 24), "Attack": (18, 30), "Cast": (30, 40), "Hit": (10, 14),
          "Die": (24, 36), "Victory": (36, 48)}
WING = ("Clavicle", "Upperarm", "Forearm")
WING_SHARE = (0.38, 0.34, 0.28)   # how a wing angle is spread over the chain (the chest is partly clavicle-weighted)
FINGERS = ("Index1", "Mid1", "Ring1", "Pinky1")


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

    # Bake scale + hover into the rest pose (mesh and bones), then re-parent without an inverse.
    body.parent = None
    for o in (rig, body):
        o.matrix_world = Euler((0, 0, 0)).to_matrix().to_4x4()
        o.scale = (SCALE, SCALE, SCALE)
        o.location = (0, 0, HOVER)
        A.apply_transform(o)
    body.parent = rig
    body.matrix_parent_inverse.identity()
    mods = [m for m in body.modifiers if m.type == "ARMATURE"]
    assert len(mods) == 1
    mods[0].object = rig
    for pb in rig.pose.bones:
        pb.rotation_mode = "XYZ"

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
    for img in list(bpy.data.images):
        if img != base and img.users == 0:
            bpy.data.images.remove(img)
    bpy.data.materials.remove(src)

    # White vertex colour: Abyss/Toon multiplies Col into the albedo; render_icons needs the attribute.
    col = body.data.color_attributes.new("Col", "BYTE_COLOR", "CORNER")
    col.data.foreach_set("color", [1.0] * (4 * len(col.data)))
    body.data.color_attributes.active_color = col
    return rig, body


# ---------------------------------------------------------------- pose vocabulary (armature axes, degrees, metres)
# Character faces -Y, its left is +X. +X rot = pitch forward; for the wings a positive "up" raises both tips.

def wings(P, up, sweep=0.0, left=1.0, right=1.0):
    """up > 0 raises both wing tips (rotation about the forward axis), sweep > 0 swings the tips forward."""
    for side, sgn, k in (("L", -1.0, left), ("R", 1.0, right)):
        for bone, share in zip(WING, WING_SHARE):
            P.r(f"{side}_{bone}", (0, sgn * up * share * k, sgn * sweep * share * k))


def claws(P, reach, curl=0.0):
    """reach > 0 swings both claw hands forward/up, curl > 0 closes the claws."""
    for side in ("L", "R"):
        P.r(f"{side}_Hand", (-reach, 0, 0))
        for f in FINGERS:
            if f"{side}_{f}" in RIG_BONES:
                P.r(f"{side}_{f}", (curl, 0, 0))


def legs(P, swing, spread=0.0):
    """swing > 0 trails the feet backward, spread > 0 opens them sideways."""
    P.r("L_Thigh", (swing, -spread, 0))
    P.r("R_Thigh", (swing, spread, 0))
    P.r("L_Calf", (swing * 0.5, 0, 0))
    P.r("R_Calf", (swing * 0.5, 0, 0))


def body(P, loc=(0, 0, 0), pitch=0.0, roll=0.0, yaw=0.0):
    P.l("BoneRoot", loc)
    P.r("BoneRoot", (pitch, roll, yaw))


def torso(P, bend=0.0, head=0.0, turn=0.0):
    """bend > 0 curls the spine forward, head > 0 nods the head down (kept small: Tripo weighted ~30 % of the wings to it)."""
    P.r("Waist", (bend * 0.3, 0, 0))
    P.r("Spine01", (bend * 0.35, 0, turn * 0.5))
    P.r("Spine02", (bend * 0.35, 0, turn * 0.5))
    P.r("Head", (head, 0, 0))


RIG_BONES = set()
W = C.wave
K = C.K


# ---------------------------------------------------------------- clips

def idle(P, f, t):
    # Two heavy wing beats per loop; the body rises just after each down-stroke.
    w = 2.0 * t
    up = -3 + 21 * math.cos(math.tau * w)
    wings(P, up, sweep=5 * math.sin(math.tau * w))
    body(P, loc=(0.02 * math.sin(math.tau * t), 0, -0.04 * math.cos(math.tau * w - 0.6)),
         pitch=2 * math.sin(math.tau * w - 0.9), roll=2.5 * math.sin(math.tau * t))
    torso(P, bend=3 * math.cos(math.tau * w - 0.9), head=3 * math.sin(math.tau * w + 1.2))
    claws(P, 6 * math.sin(math.tau * t), curl=8 + 6 * math.sin(math.tau * w + 2.0))
    legs(P, 7 * math.sin(math.tau * w - 1.4))


def run(P, f, t):
    # Lean into a fast forward flight: two strong beats per loop, feet trailing.
    w = 2.0 * t
    wings(P, 2 + 26 * math.cos(math.tau * w), sweep=-6 + 8 * math.sin(math.tau * w))
    body(P, loc=(0, 0, -0.05 * math.cos(math.tau * w - 0.6)), pitch=13 + 2 * math.sin(math.tau * w - 0.9))
    torso(P, bend=3, head=-6 + 2 * math.sin(math.tau * w + 1.0))
    claws(P, -12, curl=18)
    legs(P, 24 + 6 * math.sin(math.tau * w - 1.4))


def attack(P, f, t):
    # Rear up (0-6), swoop forward and rake with the claws: impact at frame 10 (40 %), recover by 25.
    keys = lambda *v: K(f, *zip((0, 6, 10, 14, 25), v))  # noqa: E731
    loc = keys((0, 0, 0), (0, 0.18, 0.12), (0, -0.42, -0.10), (0, -0.36, -0.10), (0, 0, 0))
    body(P, loc=loc, pitch=keys(0, -12, 26, 20, 0))
    wings(P, keys(0, 30, -30, -20, 0), sweep=keys(0, -12, 18, 10, 0))
    torso(P, bend=keys(0, -8, 10, 6, 0), head=keys(0, -8, 8, 5, 0))
    claws(P, keys(0, -22, 55, 40, 0), curl=keys(8, -10, 30, 25, 8))
    legs(P, keys(0, -10, 22, 16, 0))


def cast(P, f, t):
    # Gather (0-12), inhale (12-18), screech with wings flung wide at frame 21 (60 %), tremble to 28, settle by 35.
    keys = lambda *v: K(f, *zip((0, 12, 18, 21, 28, 35), v))  # noqa: E731
    shake = math.sin(f * 2.6) * (1.0 if 21 <= f <= 28 else 0.0) * (1 - (f - 21) / 8.0)
    body(P, loc=(0, keys(0, 0.04, 0.06, -0.02, -0.02, 0), keys(0, -0.04, 0.06, 0.12, 0.10, 0)),
         pitch=keys(0, 8, -8, -12, -10, 0))
    wings(P, keys(0, 18, -6, -30, -26, 0) + 3 * shake, sweep=keys(0, 22, -8, -20, -16, 0))
    torso(P, bend=keys(0, 12, -10, -14, -12, 0), head=keys(0, 10, -12, -18, -15, 0) + 3 * shake)
    claws(P, keys(0, -10, 10, 30, 26, 0), curl=keys(8, 35, 0, -15, -12, 8))
    legs(P, keys(0, 8, -6, -10, -8, 0), spread=keys(0, 0, 4, 8, 6, 0))


def hit(P, f, t):
    # Knocked back at frame 3, recovers by 12.
    keys = lambda *v: K(f, *zip((0, 3, 7, 12), v))  # noqa: E731
    body(P, loc=keys((0, 0, 0), (0, 0.18, 0.05), (0, 0.07, 0.01), (0, 0, 0)), pitch=keys(0, -20, -6, 0),
         roll=keys(0, 6, 1.5, 0))
    wings(P, keys(0, 26, 8, 0), sweep=keys(0, 14, 4, 0))
    torso(P, bend=keys(0, -10, -3, 0), head=keys(0, -14, -3, 0))
    claws(P, keys(0, -15, -4, 0), curl=keys(8, 30, 14, 8))
    legs(P, keys(0, -12, -4, 0))


DIE_DROP = [0.0]   # set by fit_die_to_floor()


def die(P, f, t):
    # Recoil (0-4), wings give out and it drops onto its back (4-19), bounces (22) and lies still (25-30).
    keys = lambda *v: K(f, *zip((0, 4, 13, 19, 22, 25, 30), v))  # noqa: E731
    drop = DIE_DROP[0]
    body(P, loc=keys((0, 0, 0), (0, 0.08, 0.08), (0, 0.20, -0.45 * drop), (0, 0.28, -drop),
                     (0, 0.28, -drop + 0.03), (0, 0.28, -drop), (0, 0.28, -drop)),
         pitch=keys(0, -12, -40, -72, -68, -72, -72), roll=keys(0, 3, 12, 18, 17, 18, 18))
    wings(P, keys(0, 25, -10, -38, -34, -38, -38), sweep=keys(0, -8, 6, 10, 9, 10, 10),
          left=1.0, right=keys(1.0, 1.0, 0.9, 0.85, 0.85, 0.85, 0.85))
    torso(P, bend=keys(0, -10, 8, 12, 10, 12, 12), head=keys(0, -14, 6, 12, 10, 12, 12))
    claws(P, keys(0, -10, 15, 25, 22, 25, 25), curl=keys(8, 30, 45, 50, 48, 50, 50))
    legs(P, keys(0, -8, -18, -30, -28, -30, -30), spread=keys(0, 2, 6, 8, 8, 8, 8))


def victory(P, f, t):
    # Rises (0-10), two triumphant beats (10-34), then holds a proud wide-wing pose (34-44).
    keys = lambda *v: K(f, *zip((0, 10, 16, 22, 28, 34, 44), v))  # noqa: E731
    body(P, loc=(0, 0, keys(0, 0.20, 0.28, 0.20, 0.28, 0.18, 0.18)), pitch=keys(0, -8, -12, -7, -12, -10, -10))
    wings(P, keys(0, 30, -36, 24, -38, -32, -32), sweep=keys(0, -6, -14, 4, -14, -16, -16))
    torso(P, bend=keys(0, -12, -16, -10, -16, -14, -14), head=keys(0, -12, -22, -14, -22, -18, -18))
    claws(P, keys(0, 10, 25, 15, 28, 22, 22), curl=keys(8, 0, -15, 0, -15, -10, -10))
    legs(P, keys(0, -6, -10, -6, -10, -8, -8), spread=keys(0, 4, 8, 6, 8, 7, 7))


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


def min_z(rig, body, action, frame):
    rig.animation_data.action = action
    bpy.context.scene.frame_set(frame)
    return float(mesh_points(body)[:, 2].min())


def fit_die_to_floor(rig, body):
    """Solve the Die drop so the collapsed body rests on z=0 (lowest vertex at +1 cm)."""
    rig.animation_data_create()
    DIE_DROP[0] = HOVER
    for _ in range(6):
        act = C.bake(rig, "_DieProbe", LENGTHS["Die"], die)
        low = min_z(rig, body, act, LENGTHS["Die"])
        rig.animation_data.action = None
        bpy.data.actions.remove(act)
        DIE_DROP[0] += low - 0.01
        if abs(low - 0.01) < 0.003:
            break
    print(f"[{ID}] Die drop {DIE_DROP[0]:.3f} m (last pose lowest vertex {low:.3f})")


def build():
    rig, body_obj = build_model()
    RIG_BONES.update(b.name for b in rig.data.bones)
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
        lows[name] = round(min(min_z(rig, body_obj, act, f) for f in range(LENGTHS[name] + 1)), 3)
    print(f"[{ID}] lowest vertex per clip: {lows}")
    rig.animation_data.action = None
    for pb in rig.pose.bones:
        pb.location = (0, 0, 0)
        pb.rotation_euler = (0, 0, 0)
        pb.scale = (1, 1, 1)
    bpy.context.scene.frame_set(0)
    sys.path.insert(0, os.path.join(HERE, "..", "lib_humanoid"))
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
    rep = {"triangles": sum(len(p.vertices) - 2 for p in me.polygons), "vertices": len(me.vertices),
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

    # Rest pose size + "posing a wing bone moves the mesh".
    rig.animation_data.action = None
    modes = {pb.name: pb.rotation_mode for pb in rig.pose.bones}   # imported takes key quaternions
    for pb in rig.pose.bones:
        pb.rotation_mode = "XYZ"
        pb.location = (0, 0, 0)
        pb.rotation_euler = (0, 0, 0)
    sc.frame_set(0)
    rest = mesh_points(body_obj)
    rep["rest_bounds"] = [rest.min(0).round(3).tolist(), rest.max(0).round(3).tolist()]
    for bone in ("L_Upperarm", "R_Forearm", "Head"):
        pb = rig.pose.bones[bone]
        pb.rotation_euler = (0, 0, math.radians(30))
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


def render_previews(rig, body_obj, takes):
    sc = bpy.context.scene
    os.makedirs(PREVIEW_DIR, exist_ok=True)
    bpy.ops.mesh.primitive_plane_add(size=3.2, location=(0, 0, 0))
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

    center = (0, 0, 0.85)
    rig.animation_data.action = None
    sc.frame_set(0)
    shot(os.path.join(PREVIEW_DIR, "front.png"), (90, 0, 0), center, 2.1, 900)
    shot(os.path.join(PREVIEW_DIR, "three_quarter.png"), (78, 0, 32), center, 2.2, 900)
    shot(os.path.join(PREVIEW_DIR, "side.png"), (90, 0, 90), center, 2.1, 900)

    cell = 300
    cols = 6
    for view, rot in (("front", (80, 0, 20)), ("side", (88, 0, 90))):
        rows = []
        for name in RANGES:
            a = takes[name]
            f0, f1 = (int(round(x)) for x in a.frame_range)
            n = f1 - f0
            marks = {"Attack": [0, 6, 10, 14, 19, 25], "Cast": [0, 12, 18, 21, 26, 35],
                     "Die": [0, 4, 13, 19, 25, 30]}.get(name, [round(n * k / (cols - 1)) for k in range(cols)])
            row = []
            for m in marks:
                rig.animation_data.action = a
                sc.frame_set(f0 + m)
                tmp = os.path.join(PREVIEW_DIR, "_cell.png")
                shot(tmp, rot, (0, 0, 0.72), 1.9, cell)
                img = pixels(tmp)
                # frame tick: darker strip at the bottom marks key moments (Attack 40 %, Cast 60 %)
                if (name == "Attack" and m == 10) or (name == "Cast" and m == 21):
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
    argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
    if "--verify" in argv:
        verify()
        return
    build()
    cmd = [bpy.app.binary_path, "-b", "--factory-startup", "--python-exit-code", "1", "-P", os.path.abspath(__file__),
           "--", "--verify"]
    r = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8", errors="replace")
    for line in r.stdout.splitlines():
        if line.startswith(f"[{ID}]") or "Error" in line or "Traceback" in line:
            print(line)
    if r.returncode != 0:
        print(r.stderr[-4000:])
        raise RuntimeError("verification failed")


if __name__ == "__main__":
    main()
