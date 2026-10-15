"""Visual check: the hero's old clips on the Tripo model, next to the old model playing the same frame.

    blender -b --factory-startup --python-exit-code 1 -P Blender/hunters_tripo/retarget_preview.py -- <hero_id>
        [--dir DIR]        staging dir holding <id>.fbx and <id>_anim.fbx (default ArtSource/hunters/<id>/staging)
        [--old FBX]        old game model (default Assets/_Game/Resources/Art/Characters/<id>/<id>.fbx)
        [--weapon FBX]     weapon held on weapon.R (default Weapons/sword_iron.fbx)

Approximates Unity Humanoid retargeting: both rigs share the T-pose rest, so each mapped bone gets the source bone's
world-space rotation delta from rest; hips translation is scaled by the hips-height ratio. Unmapped target bones
(Spine2, fingers, toes) keep their rest relative to the parent. Weapons sit on weapon.R with the Unity attach
convention (weapon +Z along the bone tail). Writes DIR/preview/<id>_retarget.png: pairs of [old | Tripo] per clip.
"""
import math
import os
import sys

import bpy
from mathutils import Matrix

sys.path.append(os.path.dirname(os.path.abspath(__file__)))
import common as C  # noqa: E402

SHOTS = [("Idle", 0.25), ("Walk", 0.25), ("Run", 0.25), ("Attack", 0.4), ("Cast", 0.6), ("Skill", 0.5),
         ("Ultimate", 0.42), ("Guard", 0.5), ("Hit", 0.5), ("Victory", 0.6), ("Revive", 0.0), ("Die", 1.0)]
WEAPON_FIX = Matrix.Rotation(math.radians(-90), 4, "X")


def parse(argv):
    a = C.args_after_dashes(argv)
    if not a:
        raise SystemExit(__doc__)
    o = {"id": a[0], "dir": None, "old": None, "weapon": os.path.join(C.ART, "Weapons", "sword_iron.fbx")}
    i = 1
    while i < len(a):
        key = a[i].lstrip("-")
        o[key] = os.path.abspath(a[i + 1]); i += 2
    o["dir"] = o["dir"] or os.path.join(C.REPO, "ArtSource", "hunters", o["id"], "staging")
    o["old"] = o["old"] or os.path.join(C.ART, "Characters", o["id"], o["id"] + ".fbx")
    return o


def load(path, tag):
    objs = C.import_fbx(path)
    rig = C.only(objs, "ARMATURE")
    rig.name = tag + "_Rig"
    return rig, [ob for ob in objs if ob.type == "MESH"]


def ordered(rig):
    res = []

    def visit(b):
        res.append(rig.pose.bones[b.name])
        for c in b.children:
            visit(c)
    for b in rig.data.bones:
        if b.parent is None:
            visit(b)
    return res


def action_for(clip, rig_actions):
    for a in rig_actions:
        if a.name.split("|")[-1].split(".")[0] == clip:
            return a
    raise KeyError(clip)


def set_frame(rig, act, t):
    rig.animation_data_create()
    rig.animation_data.action = act
    if getattr(act, "slots", None) and len(act.slots):
        rig.animation_data.action_slot = act.slots[0]
    s, e = act.frame_range
    bpy.context.scene.frame_set(int(round(s + (e - s) * t)))


def retarget(src, dst, mapped, ratio):
    C.update()
    for pb in ordered(dst):
        pb.matrix_basis = Matrix.Identity(4)
    C.update()
    for pb in ordered(dst):
        if pb.name not in mapped:
            continue
        sp = src.pose.bones[pb.name]
        delta = sp.matrix.to_quaternion() @ sp.bone.matrix_local.to_quaternion().inverted()
        rot = delta @ pb.bone.matrix_local.to_quaternion()
        if pb.name == C.MIX + "Hips":
            head = pb.bone.head_local + (sp.matrix.translation - sp.bone.head_local) * ratio
        else:
            head = pb.matrix.translation.copy()
        pb.matrix = Matrix.Translation(head) @ rot.to_matrix().to_4x4()
        C.update()


def hold(weapon, rig):
    weapon.matrix_world = rig.matrix_world @ rig.pose.bones["weapon.R"].matrix @ WEAPON_FIX


def main(o):
    hid, d = o["id"], o["dir"]
    prev = os.path.join(d, "preview")
    C.reset()
    old_rig, old_meshes = load(o["old"], "Old")
    old_actions = list(bpy.data.actions)
    src_rig, _ = load(os.path.join(d, hid + "_anim.fbx"), "Src")
    src_actions = [a for a in bpy.data.actions if a not in old_actions]
    dst_rig, dst_meshes = load(os.path.join(d, hid + ".fbx"), "Dst")
    for a in bpy.data.actions:
        if a not in old_actions and a not in src_actions:
            bpy.data.actions.remove(a)
    weapons = []
    for _ in range(2):
        objs = C.import_fbx(o["weapon"])
        for ob in objs:
            if ob.type == "MESH" and ob.parent is None:
                weapons.append(ob)
                break
    w_old, w_new = weapons[0], weapons[1]
    mapped = {b.name for b in src_rig.data.bones if b.name.startswith(C.MIX)} & set(dst_rig.data.bones.keys())
    ratio = dst_rig.data.bones[C.MIX + "Hips"].head_local.z / src_rig.data.bones[C.MIX + "Hips"].head_local.z
    src_rig.hide_render = True

    bounds = (C.Vector((-1.0, -1.0, -0.05)), C.Vector((1.0, 1.0, 1.95)))
    cells = []
    for clip, t in SHOTS:
        set_frame(old_rig, action_for(clip, old_actions), t)
        set_frame(src_rig, action_for(clip, src_actions), t)
        retarget(src_rig, dst_rig, mapped, ratio)
        hold(w_old, old_rig)
        hold(w_new, dst_rig)
        C.update()
        cells.append(C.render(os.path.join(prev, "cells", f"{clip}_old.png"), old_meshes + [w_old], 30, size=360,
                              bounds=bounds, pad=1.0))
        cells.append(C.render(os.path.join(prev, "cells", f"{clip}_tripo.png"), dst_meshes + [w_new], 30, size=360,
                              bounds=bounds, pad=1.0))
    out = C.stitch(cells, os.path.join(prev, hid + "_retarget.png"), 6)
    print("RETARGET SHEET", out, "mapped", len(mapped), "hips ratio", round(ratio, 4))


if __name__ == "__main__":
    main(parse(sys.argv))
