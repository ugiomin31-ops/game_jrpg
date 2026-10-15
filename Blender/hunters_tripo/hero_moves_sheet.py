"""Contact sheet of a Blender-rig hero's moves (Characters/<id>/<id>_moves.fbx) on its own model.

    blender -b --factory-startup --python-exit-code 1 -P Blender/hunters_tripo/hero_moves_sheet.py -- <hero_id> OUT.png
        [--frames 5] [--size 180] [--yaw 35] [--takes Slash,Smash]

The weapon socket (weapon.R / weapon.L bone) is drawn as a stick along the bone, where Unity attaches the weapon.
"""
import os
import sys

import bpy
from mathutils import Matrix, Vector

sys.path.append(os.path.dirname(os.path.abspath(__file__)))
import common as C  # noqa: E402


def main():
    a = C.args_after_dashes(sys.argv)
    hid, out = a[0], os.path.abspath(a[1])
    o = {"frames": 5, "size": 180, "yaw": 35.0, "takes": None}
    i = 2
    while i < len(a):
        key = a[i].lstrip("-")
        o[key] = a[i + 1] if key == "takes" else type(o[key])(a[i + 1]); i += 2
    C.reset()
    folder = os.path.join(C.ART, "Characters", hid)
    objs = C.import_fbx(os.path.join(folder, hid + ".fbx"))
    rig = C.only(objs, "ARMATURE")
    meshes = [ob for ob in objs if ob.type == "MESH"]
    for act in list(bpy.data.actions):
        bpy.data.actions.remove(act)
    moves = C.import_fbx(os.path.join(folder, hid + "_moves.fbx"))
    for ob in moves:
        bpy.data.objects.remove(ob, do_unlink=True)
    acts = {act.name.split("|")[-1]: act for act in bpy.data.actions}
    names = o["takes"].split(",") if o["takes"] else sorted(acts)
    bpy.ops.mesh.primitive_cylinder_add(vertices=8, radius=1, depth=2)
    stick = bpy.context.active_object
    mat = bpy.data.materials.new("Stick")
    mat.diffuse_color = (0.85, 0.75, 0.3, 1)
    stick.data.materials.append(mat)
    side = "L" if "weapon.L" in rig.pose.bones and hid and False else "R"
    cells = []
    tmp = os.path.splitext(out)[0] + "_cells"
    lo, hi = C.world_bounds(meshes)
    h = hi.z - lo.z
    bounds = (Vector((-h * .55, -h * .55, -0.05)), Vector((h * .55, h * .55, h * 1.05)))
    for name in names:
        act = acts[name]
        rig.animation_data_create()
        rig.animation_data.action = act
        if getattr(act, "slots", None) and len(act.slots):
            rig.animation_data.action_slot = act.slots[0]
        s, e = act.frame_range
        if act.use_frame_range:
            s, e = act.frame_start, act.frame_end
        for k in range(o["frames"]):
            t = k / max(1, o["frames"] - 1)
            bpy.context.scene.frame_set(int(round(s + (e - s) * t)))
            C.update()
            pb = rig.pose.bones["weapon." + side]
            head, tail = rig.matrix_world @ pb.head, rig.matrix_world @ pb.tail
            d = (tail - head).normalized()
            L = h * .32
            stick.matrix_world = Matrix.Translation(head + d * L * .5) @ d.to_track_quat("Z", "Y").to_matrix().to_4x4() @ Matrix.Diagonal((0.01 * h, 0.01 * h, L * .5, 1))
            cells.append(C.render(os.path.join(tmp, f"{len(cells):03d}_{name}_{k}.png"), meshes + [stick], o["yaw"], size=o["size"], bounds=bounds, pad=1.0))
    C.stitch(cells, out, o["frames"])
    print("SHEET", out, names)


if __name__ == "__main__":
    main()
