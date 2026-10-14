"""Shared helpers for the Tripo hunter pipeline (Blender/hunters_tripo).

The Tripo hunters are Unity Humanoid models (Mixamo bone names). They carry no takes of their own: Unity retargets
the hunter's existing Blender clips onto them through a Humanoid "animation source" FBX (see anim_source.py).

Both avatars are exported with the SAME rest pose convention -- a T-pose (arms horizontal along +-X, legs straight
down, hands rigid with the forearm, feet keep their world orientation) -- so Unity builds matching muscle-space
references for the source and the target whether or not it enforces a T-pose itself on import.

Unit/axis contract (Blender/README.md): 1 unit = 1 m, feet on z=0, character faces -Y, its left (.L / Left*) is +X.
"""
import json
import math
import os
import sys

import bpy
from mathutils import Matrix, Vector

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.abspath(os.path.join(HERE, "..", ".."))
sys.path.insert(0, os.path.join(REPO, "Blender", "lib"))
import tripo_guard  # noqa: E402  (refuses to overwrite Tripo-installed FBXs)
ART = os.path.join(REPO, "Assets", "_Game", "Resources", "Art")

MIX = "mixamorig:"

# Game 20-bone rig (Blender/lib_humanoid) -> Mixamo names. Unity's Humanoid auto-mapper is most reliable on Mixamo
# names, and using the same names on the source and the target keeps both avatars mapped identically.
GAME_TO_MIXAMO = {
    "hips": MIX + "Hips", "spine": MIX + "Spine", "chest": MIX + "Spine1", "neck": MIX + "Neck", "head": MIX + "Head",
    "shoulder.L": MIX + "LeftShoulder", "upper_arm.L": MIX + "LeftArm", "forearm.L": MIX + "LeftForeArm",
    "hand.L": MIX + "LeftHand",
    "shoulder.R": MIX + "RightShoulder", "upper_arm.R": MIX + "RightArm", "forearm.R": MIX + "RightForeArm",
    "hand.R": MIX + "RightHand",
    "thigh.L": MIX + "LeftUpLeg", "shin.L": MIX + "LeftLeg", "foot.L": MIX + "LeftFoot",
    "thigh.R": MIX + "RightUpLeg", "shin.R": MIX + "RightLeg", "foot.R": MIX + "RightFoot",
}

# Unity HumanBodyBones that must map for a valid Humanoid avatar (Mixamo names), plus the optional ones we expect.
REQUIRED_HUMAN = {
    "Hips": "Hips", "Spine": "Spine", "Head": "Head",
    "LeftUpperLeg": "LeftUpLeg", "LeftLowerLeg": "LeftLeg", "LeftFoot": "LeftFoot",
    "RightUpperLeg": "RightUpLeg", "RightLowerLeg": "RightLeg", "RightFoot": "RightFoot",
    "LeftUpperArm": "LeftArm", "LeftLowerArm": "LeftForeArm", "LeftHand": "LeftHand",
    "RightUpperArm": "RightArm", "RightLowerArm": "RightForeArm", "RightHand": "RightHand",
}
OPTIONAL_HUMAN = {"Chest": "Spine1", "UpperChest": "Spine2", "Neck": "Neck",
                  "LeftShoulder": "LeftShoulder", "RightShoulder": "RightShoulder",
                  "LeftToes": "LeftToeBase", "RightToes": "RightToeBase"}

CLIPS_REQUIRED = ["Idle", "Run", "Walk", "Attack", "Cast", "Hit", "Die", "Victory"]

# Old-rig weapon sockets in its arms-down rest (Blender/lib_humanoid): head = grip, +Y (tail) = weapon direction,
# +Z = blade-edge side. Measured from Characters/h_dohyun/h_dohyun.fbx; reused for the Tripo rig.
WEAPON_Y = Vector((0.0, -0.94, 0.33)).normalized()
WEAPON_Z = Vector((0.0, -0.33, -0.94)).normalized()


def args_after_dashes(argv):
    return argv[argv.index("--") + 1:] if "--" in argv else []


def reset():
    bpy.ops.wm.read_factory_settings(use_empty=True)
    sc = bpy.context.scene
    sc.render.fps = 30
    sc.render.fps_base = 1.0
    sc.unit_settings.system = "METRIC"
    sc.unit_settings.scale_length = 1.0


def import_fbx(path):
    before = set(bpy.data.objects)
    bpy.ops.import_scene.fbx(filepath=path, automatic_bone_orientation=False, ignore_leaf_bones=False)
    return [o for o in bpy.data.objects if o not in before]


def only(objs, kind):
    found = [o for o in objs if o.type == kind]
    if len(found) != 1:
        raise RuntimeError(f"expected exactly one {kind}, got {[o.name for o in found]}")
    return found[0]


def select(objs, active=None):
    if bpy.context.object is not None and bpy.context.object.mode != "OBJECT":
        bpy.ops.object.mode_set(mode="OBJECT")
    bpy.ops.object.select_all(action="DESELECT")
    for o in objs:
        o.select_set(True)
    bpy.context.view_layer.objects.active = active or objs[0]


def update():
    bpy.context.view_layer.update()


def clear_pose(rig):
    for pb in rig.pose.bones:
        pb.rotation_mode = "QUATERNION"
        pb.matrix_basis = Matrix.Identity(4)
    update()


# ---------------------------------------------------------------- T-pose

def _rotate_about_head(pb, q):
    """Rotate a pose bone (and with it its children) by world/armature-space quaternion q about its head."""
    m = pb.matrix.copy()
    head = m.translation.copy()
    pb.matrix = Matrix.Translation(head) @ q.to_matrix().to_4x4() @ Matrix.Translation(-head) @ m
    update()


def _swing(rig, bone, child, target):
    pb, cb = rig.pose.bones[bone], rig.pose.bones[child]
    d = cb.head - pb.head
    if d.length < 1e-6:
        return 0.0
    q = d.normalized().rotation_difference(target.normalized())
    _rotate_about_head(pb, q)
    return math.degrees(q.angle)


def pose_tpose(rig, names):
    """Pose `rig` into the shared T-pose. `names` maps canonical Mixamo short names to this rig's bone names.
    Upper arm and forearm swing onto +-X (hand rides along rigidly), thigh and shin swing straight down,
    feet keep their world orientation. Returns the swing angles (degrees) for the report."""
    report = {}
    n = names.get
    for side, sx in (("Left", 1.0), ("Right", -1.0)):
        out = Vector((sx, 0.0, 0.0))
        report[side + "Arm"] = _swing(rig, n(side + "Arm"), n(side + "ForeArm"), out)
        report[side + "ForeArm"] = _swing(rig, n(side + "ForeArm"), n(side + "Hand"), out)
        foot = rig.pose.bones[n(side + "Foot")]
        foot_rot = foot.matrix.to_quaternion()
        report[side + "UpLeg"] = _swing(rig, n(side + "UpLeg"), n(side + "Leg"), Vector((0, 0, -1)))
        report[side + "Leg"] = _swing(rig, n(side + "Leg"), n(side + "Foot"), Vector((0, 0, -1)))
        now = foot.matrix.to_quaternion()
        _rotate_about_head(foot, foot_rot @ now.inverted())
    return {k: round(v, 2) for k, v in report.items()}


def apply_pose_as_rest(rig, meshes=()):
    """Bake the current pose into the meshes (armature modifier applied) and make it the armature's rest pose."""
    for me in meshes:
        mods = [m for m in me.modifiers if m.type == "ARMATURE"]
        if len(mods) != 1:
            raise RuntimeError(f"{me.name}: expected one armature modifier, got {[m.name for m in me.modifiers]}")
        name = mods[0].name
        select([me])
        bpy.ops.object.modifier_apply(modifier=name)
    select([rig])
    bpy.ops.object.mode_set(mode="POSE")
    bpy.ops.pose.select_all(action="SELECT")
    bpy.ops.pose.armature_apply(selected=False)
    bpy.ops.object.mode_set(mode="OBJECT")
    for me in meshes:
        mod = me.modifiers.new("Armature", "ARMATURE")
        mod.object = rig
        mod.use_vertex_groups = True
    update()


# ---------------------------------------------------------------- export / checks

def export_fbx(path, objects, animated, path_mode="STRIP", force=False):
    """Same settings as Blender/lib/abyss_bpy.export_fbx for animated characters (bake_space_transform off), so the
    Tripo hunters land in Unity with the same axis/scale conventions as the Blender heroes.
    A Tripo-marked target is skipped unless force=True or ABYSS_OVERWRITE_TRIPO=1 (Blender/lib/tripo_guard.py)."""
    if tripo_guard.should_skip(path, force):
        return path
    os.makedirs(os.path.dirname(path), exist_ok=True)
    select(objects)
    bpy.ops.export_scene.fbx(
        filepath=path, use_selection=True, object_types={"MESH", "ARMATURE"},
        apply_unit_scale=True, apply_scale_options="FBX_SCALE_ALL", axis_forward="-Z", axis_up="Y",
        use_mesh_modifiers=False, mesh_smooth_type="FACE", add_leaf_bones=False,
        primary_bone_axis="Y", secondary_bone_axis="X", use_armature_deform_only=True,
        bake_space_transform=False, bake_anim=animated, bake_anim_use_all_bones=True,
        bake_anim_use_nla_strips=False, bake_anim_use_all_actions=animated,
        bake_anim_force_startend_keying=True, bake_anim_simplify_factor=0.0,
        use_custom_props=False, path_mode=path_mode, embed_textures=False)
    return path


def world_bounds(objs):
    dg = bpy.context.evaluated_depsgraph_get()
    lo = Vector((1e9, 1e9, 1e9))
    hi = Vector((-1e9, -1e9, -1e9))
    for o in objs:
        oe = o.evaluated_get(dg)
        me = oe.to_mesh()
        for v in me.vertices:
            w = oe.matrix_world @ v.co
            lo = Vector(map(min, lo, w))
            hi = Vector(map(max, hi, w))
        oe.to_mesh_clear()
    return lo, hi


def humanoid_check(rig):
    """Unity Humanoid needs these bones and a proper parent chain (Hips above everything human)."""
    bones = rig.data.bones
    missing = [u for u, m in REQUIRED_HUMAN.items() if MIX + m not in bones]
    optional = {u: (MIX + m in bones) for u, m in OPTIONAL_HUMAN.items()}
    chain_ok = True
    hips = bones.get(MIX + "Hips")
    for m in REQUIRED_HUMAN.values():
        b = bones.get(MIX + m)
        if b is None or hips is None:
            chain_ok = False
            continue
        if b != hips and hips not in b.parent_recursive:
            chain_ok = False
    fingers = sorted(b.name for b in bones if "Hand" in b.name and b.name[-1].isdigit())
    return {"missing_required": missing, "optional_present": optional, "hips_is_ancestor": chain_ok,
            "finger_bones": len(fingers)}


def write_json(path, data):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)


# ---------------------------------------------------------------- preview renders

def render(path, objs, yaw_deg, size=720, color_type="TEXTURE", pad=1.15, bounds=None):
    """Workbench render looking at `objs` from the front (yaw 0 = camera on -Y looking at the face)."""
    sc = bpy.context.scene
    lo, hi = bounds or world_bounds(objs)
    center = (lo + hi) / 2
    h = hi.z - lo.z
    cam_data = bpy.data.cameras.new("PreviewCam")
    cam_data.type = "ORTHO"
    cam_data.ortho_scale = max(h, hi.x - lo.x, hi.y - lo.y) * pad
    cam = bpy.data.objects.new("PreviewCam", cam_data)
    sc.collection.objects.link(cam)
    yaw = math.radians(yaw_deg)
    dirv = Vector((math.sin(yaw), -math.cos(yaw), 0.08)).normalized()
    cam.location = center + dirv * (h * 4 + 2)
    cam.rotation_euler = (-dirv).to_track_quat("-Z", "Y").to_euler()
    sc.camera = cam
    sc.render.engine = "BLENDER_WORKBENCH"
    sh = sc.display.shading
    sh.light = "STUDIO"
    sh.color_type = color_type
    sh.show_cavity = False
    sh.show_object_outline = True
    sh.show_shadows = False
    sc.render.resolution_x = size
    sc.render.resolution_y = size
    sc.render.film_transparent = False
    sc.world = sc.world or bpy.data.worlds.new("W")
    sc.world.color = (0.55, 0.57, 0.6)
    hidden = [o for o in sc.objects if o.type == "MESH" and o not in objs and not o.hide_render]
    for o in hidden:
        o.hide_render = True
    os.makedirs(os.path.dirname(path), exist_ok=True)
    sc.render.filepath = path
    bpy.ops.render.render(write_still=True)
    for o in hidden:
        o.hide_render = False
    bpy.data.objects.remove(cam)
    bpy.data.cameras.remove(cam_data)
    return path


def stitch(paths, out, cols):
    """Grid of same-size PNGs (numpy ships with Blender)."""
    import numpy as np
    imgs = []
    for p in paths:
        im = bpy.data.images.load(p)
        w, h = im.size
        a = np.array(im.pixels[:], dtype=np.float32).reshape(h, w, 4)
        imgs.append(a)
        bpy.data.images.remove(im)
    h, w = imgs[0].shape[:2]
    rows = (len(imgs) + cols - 1) // cols
    sheet = np.ones((rows * h, cols * w, 4), dtype=np.float32)
    for i, a in enumerate(imgs):
        r, c = divmod(i, cols)
        y0 = (rows - 1 - r) * h  # Blender pixel rows start at the bottom
        sheet[y0:y0 + h, c * w:(c + 1) * w] = a
    img = bpy.data.images.new("sheet", cols * w, rows * h, alpha=True)
    img.pixels = sheet.ravel()
    img.filepath_raw = out
    img.file_format = "PNG"
    img.save()
    bpy.data.images.remove(img)
    return out
