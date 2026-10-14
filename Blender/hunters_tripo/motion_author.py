"""Keyframe authoring for the shared Humanoid hunter takes (Art/HumanoidAnimations/<Take>.fbx), without Tripo.

    blender -b --factory-startup --python-exit-code 1 -P Blender/hunters_tripo/motion_author.py -- [--only Cast,Hit] [--out DIR]

The skeleton is the shared library's own (Art/HumanoidAnimations/Cast.fbx: 65 Mixamo bones, its rest pose, 24 fps), so every
authored take lands on exactly the avatar the existing takes use. A take is a list of key poses in a character frame
(x = the character's right, y = forward, z = up, metres from the feet; angles in degrees). Every frame is solved, not just
the keys: pose parameters are eased per segment, arms and legs are two-bone IK (hands reach targets with an elbow hint, feet
stay planted where the pose puts them), the spine / neck / head bend in the body frame, and the result is keyed on every
frame. Export writes the REST pose into the bone nodes (a rest key at frame 0, outside the take's manual frame range), then
re-imports the file and checks that the rest matches the source skeleton and that the solved hand / foot targets are met.

Contact / release frames are part of each take's definition (CONTACT) and mirrored in BattleView.DefaultContact.
Takes (motion_takes.py) are shared by every hunter. Spell / Brace / Flinch stand in for the Tripo library's martial-arts
Cast / Guard / Hit (kept unchanged; BattleView prefers a class or hero take of the original name, then these), and the
variety takes the battle stages per skill:
Slash (horizontal sweep), Thrust (lunging stab), Smash (two-handed overhead slam), Spin (extended spinning cut),
Channel (both hands raised), Throw (underhand toss), Rally (war cry), Kneel (ally revive / big heal).
No .meta is written: Unity creates it and AbyssArtImporter names the clip after the file (as for the Tripo library).
"""
import json
import math
import os
import sys

import bpy
from mathutils import Matrix, Quaternion, Vector

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.append(HERE)
import common as C  # noqa: E402
import motion_takes as T  # noqa: E402

SOURCE = os.path.join(C.ART, "HumanoidAnimations", "Cast.fbx")
FPS = 24
M = C.MIX

# Character frame -> Blender world: the character faces -Y and its right is -X.
def W(v):
    return Vector((-v[0], -v[1], v[2]))


def body_rot(pitch=0.0, yaw=0.0, roll=0.0):
    """World rotation from body-frame angles: pitch > 0 bends forward, yaw > 0 turns to the character's left,
    roll > 0 tilts toward the character's right."""
    q_pitch = Quaternion(Vector((1, 0, 0)), math.radians(pitch))     # about the character's left axis (+X): head goes forward (-Y)
    q_yaw = Quaternion(Vector((0, 0, 1)), math.radians(yaw))
    q_roll = Quaternion(Vector((0, -1, 0)), math.radians(roll))      # about the forward axis
    return q_yaw @ q_pitch @ q_roll


EASE = {
    "linear": lambda t: t,
    "inout": lambda t: t * t * (3 - 2 * t),
    "in": lambda t: t * t * t,                # slow start, fast end (wind-up into a strike)
    "out": lambda t: 1 - (1 - t) ** 3,        # fast start, slow end (strike settling)
    "snap": lambda t: 1 - (1 - t) ** 5,
}


def lerp(a, b, t):
    if isinstance(a, (tuple, list)):
        return tuple(x + (y - x) * t for x, y in zip(a, b))
    return a + (b - a) * t


def resolve(keys):
    """Every key inherits the previous key's values for anything it does not set."""
    full, cur = [], {}
    for frame, pose in keys:
        cur = dict(cur)
        cur.update({k: v for k, v in pose.items() if k != "ease"})
        full.append((frame, cur, pose.get("ease", "inout")))
    return full


def sample(full, frame):
    if frame <= full[0][0]:
        return full[0][1]
    for (f0, p0, _), (f1, p1, ease) in zip(full, full[1:]):
        if f0 <= frame <= f1:
            t = EASE[ease]((frame - f0) / max(1e-6, f1 - f0))
            out = {}
            for k in set(p0) | set(p1):
                a, b = p0.get(k, p1.get(k)), p1.get(k, p0.get(k))
                out[k] = lerp(a, b, t) if not isinstance(a, str) else b
            return out
    return full[-1][1]


class Rig:
    def __init__(self, rig):
        self.rig = rig
        self.pb = rig.pose.bones
        self.rest_q = {b.name: b.matrix_local.to_quaternion() for b in rig.data.bones}
        self.rest_head = {b.name: b.head_local.copy() for b in rig.data.bones}
        self.order = []

        def visit(b):
            self.order.append(b.name)
            for c in b.children:
                visit(c)
        for b in rig.data.bones:
            if b.parent is None:
                visit(b)
        self.len = {n: (self.rest_head[c] - self.rest_head[n]).length for n, c in
                    [(M + "RightArm", M + "RightForeArm"), (M + "RightForeArm", M + "RightHand"),
                     (M + "LeftArm", M + "LeftForeArm"), (M + "LeftForeArm", M + "LeftHand"),
                     (M + "RightUpLeg", M + "RightLeg"), (M + "RightLeg", M + "RightFoot"),
                     (M + "LeftUpLeg", M + "LeftLeg"), (M + "LeftLeg", M + "LeftFoot")]}

    def clear(self):
        for p in self.pb:
            p.matrix_basis = Matrix.Identity(4)

    def world_q(self, name):
        return self.pb[name].matrix.to_quaternion()

    def set_world_q(self, name, q):
        """Set a bone's world rotation (armature space; the rig object is identity) keeping its head where the parent puts it."""
        pb = self.pb[name]
        bone = pb.bone
        if bone.parent is None:
            parent_q = Quaternion()
            rel = self.rest_q[name]
        else:
            parent_q = self.pb[bone.parent.name].matrix.to_quaternion()
            rel = self.rest_q[bone.parent.name].inverted() @ self.rest_q[name]
        basis = (parent_q @ rel).inverted() @ q
        pb.rotation_mode = "QUATERNION"
        pb.rotation_quaternion = basis.normalized()
        C.update()

    def rotate_body(self, name, q_world_delta):
        """Bend a bone by a body-frame rotation applied on top of what its parent already does (rest-relative)."""
        pb = self.pb[name]
        bone = pb.bone
        parent_q = self.pb[bone.parent.name].matrix.to_quaternion() if bone.parent else Quaternion()
        parent_rest = self.rest_q[bone.parent.name] if bone.parent else Quaternion()
        inherited = parent_q @ parent_rest.inverted()          # the parent's world delta from rest
        self.set_world_q(name, inherited @ q_world_delta @ self.rest_q[name])

    def aim(self, name, direction):
        """Swing a bone (its +Y) toward a world direction from where its parent carries it (minimal twist)."""
        pb = self.pb[name]
        bone = pb.bone
        parent_q = self.pb[bone.parent.name].matrix.to_quaternion() if bone.parent else Quaternion()
        rel = self.rest_q[bone.parent.name].inverted() @ self.rest_q[name] if bone.parent else self.rest_q[name]
        carried = parent_q @ rel
        y = carried @ Vector((0, 1, 0))
        swing = y.rotation_difference(direction.normalized())
        self.set_world_q(name, swing @ carried)

    def shaft_local(self, full):
        """Weapon shaft in the hand bone's rest frame, as CharacterModel.TryHumanoidGrip derives it from the knuckles."""
        hand = self.rest_head[M + full + "Hand"]
        index, middle, outer = (self.rest_head[M + full + "Hand" + n + "1"] for n in ("Index", "Middle", "Pinky"))
        fingers = (middle - hand).normalized()
        knuckle = index - outer
        knuckle = (knuckle - fingers * knuckle.dot(fingers)).normalized()
        p = math.radians(-35)
        shaft = (knuckle * math.cos(p) + fingers * math.sin(p)).normalized()
        return self.rest_q[M + full + "Hand"].inverted() @ shaft

    def aim_weapon(self, full, direction):
        """Turn the hand so the held weapon's shaft points along a world direction (minimal swing from the forearm-carried hand)."""
        name = M + full + "Hand"
        q = self.world_q(name)
        shaft = q @ self.shaft_local(full)
        self.set_world_q(name, shaft.rotation_difference(direction.normalized()) @ q)

    def head(self, name):
        return self.pb[name].head.copy()

    def two_bone(self, upper, lower, end, target, pole):
        s = self.head(upper)
        l1, l2 = self.len[upper], self.len[lower]
        d = target - s
        dist = max(1e-4, min(d.length, (l1 + l2) * 0.999))
        u = d.normalized()
        a = (l1 * l1 - l2 * l2 + dist * dist) / (2 * dist)
        h = math.sqrt(max(0.0, l1 * l1 - a * a))
        p = pole - u * pole.dot(u)
        if p.length < 1e-5:
            p = Vector((0, -1, 0)) - u * Vector((0, -1, 0)).dot(u)
        p.normalize()
        elbow = s + u * a + p * h
        self.aim(upper, elbow - s)
        self.aim(lower, (s + u * dist) - self.head(lower))
        return s + u * dist


def solve(r, pose, rest_feet):
    r.clear()
    C.update()
    hips = M + "Hips"
    # Hips: offset (character frame) and body rotation.
    off = W(pose.get("hips", (0, 0, 0)))
    q = body_rot(*pose.get("hips_rot", (0, 0, 0)))
    pb = r.pb[hips]
    rest_q = r.rest_q[hips]
    pb.rotation_mode = "QUATERNION"
    pb.rotation_quaternion = (rest_q.inverted() @ q @ rest_q).normalized()
    pb.location = rest_q.inverted() @ off
    C.update()
    # Spine chain, neck, head: body-frame bends relative to the parent.
    for key, bone in (("spine", "Spine"), ("chest", "Spine1"), ("chest2", "Spine2"), ("neck", "Neck"), ("head", "Head")):
        if key in pose:
            r.rotate_body(M + bone, body_rot(*pose[key]))
    # Clavicles: shrug / reach (body-frame rotation).
    for side in ("R", "L"):
        full = "Right" if side == "R" else "Left"
        if "shoulder" + side in pose:
            r.rotate_body(M + full + "Shoulder", body_rot(*pose["shoulder" + side]))
    # Arms: two-bone IK in the character frame, then the wrist.
    reached = {}
    for side in ("R", "L"):
        full = "Right" if side == "R" else "Left"
        if "hand" + side not in pose:
            continue
        target = W(pose["hand" + side])
        pole = W(pose.get("pole" + side, (0.6 if side == "R" else -0.6, -0.5, -0.4)))
        reached[side] = r.two_bone(M + full + "Arm", M + full + "ForeArm", M + full + "Hand", target, pole)
        wrist = pose.get("wrist" + side)
        if wrist and any(wrist):
            r.rotate_body(M + full + "Hand", body_rot(*wrist))
        weapon = pose.get("weapon" + side)
        if weapon:
            r.aim_weapon(full, W(weapon))
    # Legs: feet stay where the pose puts them (rest by default), knees toward the hint.
    for side in ("R", "L"):
        full = "Right" if side == "R" else "Left"
        ankle = W(pose["foot" + side]) if "foot" + side in pose else rest_feet[side]
        pole = W(pose.get("knee" + side, (0.08 if side == "R" else -0.08, 1, 0)))
        r.two_bone(M + full + "UpLeg", M + full + "Leg", M + full + "Foot", ankle, pole)
        # The foot keeps its rest orientation, turned by the pose's foot yaw (planted, flat on the floor).
        yaw = pose.get("footYaw" + side, 0.0)
        r.set_world_q(M + full + "Foot", body_rot(0, yaw, 0) @ r.rest_q[M + full + "Foot"])
        if "toe" + side in pose:
            r.rotate_body(M + full + "ToeBase", body_rot(*pose["toe" + side]))
    # Fingers: a grip curl (0 open .. 1 fist) on every finger joint.
    for side in ("R", "L"):
        full = "Right" if side == "R" else "Left"
        curl = pose.get("grip" + side, 0.0)
        if curl <= 0:
            continue
        for name in r.order:
            if not name.startswith(M + full + "Hand") or name == M + full + "Hand" or name.endswith("4"):
                continue
            thumb = "Thumb" in name
            ang = math.radians((35 if thumb else 75) * curl)
            pb = r.pb[name]
            pb.rotation_mode = "QUATERNION"
            # Mixamo finger joints bend about their local X (toward the palm).
            pb.rotation_quaternion = Quaternion(Vector((1, 0, 0)), ang if side == "L" else ang)
        C.update()
    return reached


def build_take(r, name, keys, rest_feet):
    full = resolve(keys)
    last = full[-1][0]
    act = bpy.data.actions.new(name)   # exported take: "Armature|<name>" like the library
    r.rig.animation_data_create()
    r.rig.animation_data.action = act
    # Frame 0: the REST pose (bone nodes are written from the current frame on export).
    r.clear()
    C.update()
    for pb in r.pb:
        pb.rotation_mode = "QUATERNION"
        pb.keyframe_insert("rotation_quaternion", frame=0, group=pb.name)
        pb.keyframe_insert("location", frame=0, group=pb.name)
    misses = []
    for f in range(1, last + 1):
        pose = sample(full, f)
        reached = solve(r, pose, rest_feet)
        for side, point in reached.items():
            hand = r.head(M + ("Right" if side == "R" else "Left") + "Hand")
            misses.append((hand - point).length)
        for pb in r.pb:
            pb.keyframe_insert("rotation_quaternion", frame=f, group=pb.name)
            if pb.bone.parent is None:
                pb.keyframe_insert("location", frame=f, group=pb.name)
    act.use_frame_range = True
    act.frame_start, act.frame_end = 1, last
    for fc in act.fcurves if hasattr(act, "fcurves") else []:
        for kp in fc.keyframe_points:
            kp.interpolation = "LINEAR"
    return act, max(misses) if misses else 0.0


def export_take(r, act, path):
    bpy.context.scene.render.fps = FPS
    bpy.context.scene.frame_set(0)        # rest pose in the bone nodes
    for a in list(bpy.data.actions):
        if a != act:
            bpy.data.actions.remove(a)
    r.rig.animation_data.action = act
    if getattr(act, "slots", None) and len(act.slots):
        r.rig.animation_data.action_slot = act.slots[0]
    bpy.context.scene.frame_set(0)
    os.makedirs(os.path.dirname(path), exist_ok=True)
    C.select([r.rig])
    bpy.ops.export_scene.fbx(
        filepath=path, use_selection=True, object_types={"ARMATURE"},
        apply_unit_scale=True, apply_scale_options="FBX_SCALE_ALL", axis_forward="-Z", axis_up="Y",
        add_leaf_bones=False, primary_bone_axis="Y", secondary_bone_axis="X", use_armature_deform_only=False,
        bake_space_transform=False, bake_anim=True, bake_anim_use_all_bones=True, bake_anim_use_nla_strips=False,
        bake_anim_use_all_actions=True, bake_anim_force_startend_keying=True, bake_anim_simplify_factor=0.0,
        use_custom_props=False, path_mode="STRIP", embed_textures=False)


def verify(path, rest_head):
    """Re-import: rest bone heads equal the source skeleton; returns (max rest error, frame count)."""
    before = set(bpy.data.objects)
    acts_before = set(bpy.data.actions)
    bpy.ops.import_scene.fbx(filepath=path)
    new = [o for o in bpy.data.objects if o not in before]
    rig = [o for o in new if o.type == "ARMATURE"][0]
    err = max((rig.matrix_world @ b.head_local - rest_head[b.name]).length for b in rig.data.bones)
    acts = [a for a in bpy.data.actions if a not in acts_before]
    s, e = acts[0].frame_range
    nbones = len(rig.data.bones)
    for o in new:
        bpy.data.objects.remove(o, do_unlink=True)
    for a in acts:
        bpy.data.actions.remove(a)
    return err, int(round(e - s)) + 1, nbones


def main():
    a = C.args_after_dashes(sys.argv)
    only, out = None, os.path.join(C.ART, "HumanoidAnimations")
    i = 0
    while i < len(a):
        if a[i] == "--only": only = set(a[i + 1].split(",")); i += 2
        elif a[i] == "--out": out = os.path.abspath(a[i + 1]); i += 2
        else: raise SystemExit("unknown option " + a[i])
    report = {}
    for name, keys in T.TAKES.items():
        if only and name not in only:
            continue
        C.reset()
        bpy.ops.import_scene.fbx(filepath=SOURCE)
        rig = [o for o in bpy.data.objects if o.type == "ARMATURE"][0]
        for act in list(bpy.data.actions):
            bpy.data.actions.remove(act)
        r = Rig(rig)
        rest_feet = {"R": r.rest_head[M + "RightFoot"].copy(), "L": r.rest_head[M + "LeftFoot"].copy()}
        act, miss = build_take(r, name, keys, rest_feet)
        path = os.path.join(out, name + ".fbx")
        export_take(r, act, path)
        rest_err, frames, bones = verify(path, r.rest_head)
        report[name] = {"frames": frames, "seconds": round((frames - 1) / FPS, 3), "contact": T.CONTACT.get(name),
                        "rest_error_m": round(rest_err, 7), "max_hand_ik_miss_m": round(miss, 5), "bones": bones}
        print("TAKE", name, json.dumps(report[name]))
        if rest_err > 1e-4 or bones != 65:
            raise SystemExit(f"{name}: rest/bone check failed ({rest_err}, {bones})")
    C.write_json(os.path.join(C.REPO, "docs", "verification", "authored_takes_report.json"), report)


if __name__ == "__main__":
    main()
