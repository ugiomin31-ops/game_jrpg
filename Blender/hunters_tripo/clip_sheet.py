"""Contact sheet of Humanoid takes on a Tripo hunter (visual review of motions, no Unity needed).

    blender -b --factory-startup --python-exit-code 1 -P Blender/hunters_tripo/clip_sheet.py -- <hero_id> OUT.png
        CLIP.fbx [CLIP.fbx ...] [--frames 6] [--yaw 30] [--size 220] [--weapon FBX]

Each CLIP.fbx is a skeleton-only Humanoid take (Art/HumanoidAnimations*/.../<Take>.fbx, Mixamo names, T-pose rest).
It is applied to the hero's Tripo FBX with the same world-space rotation-delta retarget as retarget_preview.py (an
approximation of Unity's muscle retarget). One row per take, `--frames` evenly spaced frames from first to last.
"""
import math
import os
import sys

import bpy
from mathutils import Matrix

sys.path.append(os.path.dirname(os.path.abspath(__file__)))
import common as C  # noqa: E402
import retarget_preview as R  # noqa: E402


def parse(argv):
    a = C.args_after_dashes(argv)
    o = {"id": a[0], "out": os.path.abspath(a[1]), "clips": [], "frames": 6, "yaw": 30.0, "size": 220,
         "weapon": os.path.join(C.ART, "Weapons", "sword_iron.fbx")}
    i = 2
    while i < len(a):
        if a[i] == "--frames": o["frames"] = int(a[i + 1]); i += 2
        elif a[i] == "--yaw": o["yaw"] = float(a[i + 1]); i += 2
        elif a[i] == "--size": o["size"] = int(a[i + 1]); i += 2
        elif a[i] == "--weapon": o["weapon"] = os.path.abspath(a[i + 1]); i += 2
        else: o["clips"].append(os.path.abspath(a[i])); i += 1
    return o


def grip_stick(rig, stick, length=0.42):
    """Place a stick where CharacterModel.TryHumanoidGrip puts a weapon (shaft along the knuckle line, -35 deg toward the fingers)."""
    pb = rig.pose.bones
    hand = pb[C.MIX + "RightHand"].head
    index, middle, outer = (pb[C.MIX + "RightHand" + n + "1"].head for n in ("Index", "Middle", "Pinky"))
    fingers = middle - hand
    hl = fingers.length
    fingers.normalize()
    knuckle = index - outer
    knuckle = (knuckle - fingers * knuckle.dot(fingers)).normalized()
    palm = fingers.cross(knuckle)
    p = math.radians(-35)
    shaft = (knuckle * math.cos(p) + fingers * math.sin(p)).normalized()
    center = hand + ((index + middle + outer) / 3 - hand) * 0.6 + palm.normalized() * hl * 0.22
    rot = shaft.to_track_quat("Z", "Y")
    stick.matrix_world = Matrix.Translation(center + shaft * (length * 0.5 - 0.04)) @ rot.to_matrix().to_4x4() @ Matrix.Diagonal((0.012, 0.012, length * 0.5, 1))


def main(o):
    C.reset()
    dst_rig, dst_meshes = R.load(os.path.join(C.ART, "Characters", o["id"], o["id"] + ".fbx"), "Dst")
    for a in list(bpy.data.actions):
        bpy.data.actions.remove(a)
    bpy.ops.mesh.primitive_cylinder_add(vertices=8, radius=1, depth=2)
    weapon = bpy.context.active_object
    mat = bpy.data.materials.new("Stick")
    mat.diffuse_color = (0.85, 0.75, 0.3, 1)
    weapon.data.materials.append(mat)
    cells = []
    tmp = os.path.splitext(o["out"])[0] + "_cells"
    for path in o["clips"]:
        before = set(bpy.data.actions)
        src_rig, src_meshes = R.load(path, "Src")
        for m in src_meshes:
            m.hide_render = True
        acts = [a for a in bpy.data.actions if a not in before]
        act = acts[0]
        mapped = {b.name for b in src_rig.data.bones if b.name.startswith(C.MIX)} & set(dst_rig.data.bones.keys())
        ratio = dst_rig.data.bones[C.MIX + "Hips"].head_local.z / src_rig.data.bones[C.MIX + "Hips"].head_local.z
        name = os.path.splitext(os.path.basename(path))[0]
        s, e = act.frame_range
        print("CLIP", path, "frames", s, e, "mapped", len(mapped))
        bounds = (C.Vector((-1.1, -1.1, -0.05)), C.Vector((1.1, 1.1, 2.0)))
        for k in range(o["frames"]):
            t = k / max(1, o["frames"] - 1)
            R.set_frame(src_rig, act, t)
            R.retarget(src_rig, dst_rig, mapped, ratio)
            objs = list(dst_meshes)
            if weapon is not None:
                C.update()
                grip_stick(dst_rig, weapon)
                objs.append(weapon)
            C.update()
            cells.append(C.render(os.path.join(tmp, f"{len(cells):03d}_{name}_{k}.png"), objs, o["yaw"], size=o["size"],
                                  bounds=bounds, pad=1.0))
        for ob in [src_rig] + src_meshes:
            bpy.data.objects.remove(ob, do_unlink=True)
    C.stitch(cells, o["out"], o["frames"])
    print("SHEET", o["out"])


if __name__ == "__main__":
    main(parse(sys.argv))
