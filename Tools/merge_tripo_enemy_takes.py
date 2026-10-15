"""Merge single-preset Tripo enemy exports into one game FBX with "Rig|<Take>" takes; no new animation authoring.

Usage: blender --background --factory-startup --python-exit-code 1 --python Tools/merge_tripo_enemy_takes.py --
           <enemy_id> <out_dir> Idle=idle.fbx Attack=box.fbx@0:53 Cast=cast.fbx ...

Each Name=path argument is one Tripo Studio export holding exactly one preset (FBX, skeleton on). An optional
@first:last keeps only those Blender-imported frames (inclusive); without it the whole take is kept. The first
argument also supplies the mesh, skin and material. Every source must carry the same bone set as the first one.

Writes, without touching the raw sources:
  <out_dir>/<id>.fbx              armature "Rig", mesh "Body", material "<id>", one take per argument
  <out_dir>/<id>_tex/<id>.png     the first source's basecolor (Unity's TexturedMaterials contract)
  <out_dir>/<id>_merge_report.json  source hashes, frame ranges, and the re-imported take list
The importer turns "Rig|Idle" into clip "Idle" (AbyssArtImporter); Idle and Run loop there, the rest play once.
Installing into Assets (keeping the existing .meta, adding the TRIPO marker) is a separate, reviewed step.
Exit: 0 = written and re-import verified, 1 = rejected/error, 2 = invalid arguments.
"""

import hashlib
import json
import os
import re
import shutil
import sys

import bpy

TAKE = re.compile(r"^([A-Z][A-Za-z]*)=(.+?)(?:@(\d+):(\d+))?$")


def fail(code, message):
    print("merge_tripo_enemy_takes: " + message, file=sys.stderr)
    sys.exit(code)


def parse(argv):
    args = argv[argv.index("--") + 1:] if "--" in argv else []
    if len(args) < 3:
        fail(2, __doc__)
    enemy_id, out_dir, takes = args[0], args[1], []
    for raw in args[2:]:
        m = TAKE.match(raw)
        if not m:
            fail(2, "bad take argument: " + raw)
        name, path = m.group(1), m.group(2)
        frames = (int(m.group(3)), int(m.group(4))) if m.group(3) else None
        if frames and frames[1] <= frames[0]:
            fail(2, "empty frame range: " + raw)
        if not os.path.isfile(path):
            fail(2, "missing file: " + path)
        if any(t["name"] == name for t in takes):
            fail(2, "duplicate take: " + name)
        takes.append({"name": name, "path": os.path.abspath(path), "frames": frames})
    if not any(t["name"] == "Idle" for t in takes):
        print("merge_tripo_enemy_takes: warning: no Idle take; the game refuses a model without one", file=sys.stderr)
    return enemy_id, os.path.abspath(out_dir), takes


def sha256(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for block in iter(lambda: f.read(1 << 20), b""):
            h.update(block)
    return h.hexdigest()


def import_fbx(path):
    before = set(bpy.data.objects)
    actions_before = set(bpy.data.actions)
    bpy.ops.import_scene.fbx(filepath=path, use_anim=True, ignore_leaf_bones=False)
    objects = [o for o in bpy.data.objects if o not in before]
    actions = [a for a in bpy.data.actions if a not in actions_before]
    armatures = [o for o in objects if o.type == "ARMATURE"]
    if len(armatures) != 1:
        fail(1, f"{path}: expected one armature, found {len(armatures)}")
    if len(actions) != 1:
        fail(1, f"{path}: expected one preset take, found {[a.name for a in actions]}")
    return objects, armatures[0], actions[0]


def basecolor(material):
    if not material or not material.use_nodes:
        return None
    for node in material.node_tree.nodes:
        if node.type == "BSDF_PRINCIPLED":
            for link in node.inputs["Base Color"].links:
                if link.from_node.type == "TEX_IMAGE" and link.from_node.image:
                    return link.from_node.image
    return None


def main():
    enemy_id, out_dir, takes = parse(sys.argv)
    bpy.ops.wm.read_factory_settings(use_empty=True)
    report = {"id": enemy_id, "takes": []}
    rig = body = None
    bones = None
    for i, take in enumerate(takes):
        objects, armature, action = import_fbx(take["path"])
        names = sorted(b.name for b in armature.data.bones)
        if i == 0:
            rig = armature
            meshes = [o for o in objects if o.type == "MESH"]
            if len(meshes) != 1:
                fail(1, f"{take['path']}: expected one mesh, found {len(meshes)}")
            body, bones = meshes[0], names
            rig.name, rig.data.name, body.name = "Rig", "Rig", "Body"
            if len(body.material_slots) != 1 or not body.material_slots[0].material:
                fail(1, "expected one material on the mesh")
            material = body.material_slots[0].material
            image = basecolor(material)
            if image is None:
                fail(1, "no basecolor texture on the material")
            material.name = enemy_id
        elif names != bones:
            fail(1, f"{take['path']}: bone set differs from {takes[0]['path']}")
        source_range, source_action = tuple(action.frame_range), action.name
        action.name = take["name"]
        action.use_fake_user = True
        if take["frames"]:
            first, last = take["frames"]
            if first < round(source_range[0]) or last > round(source_range[1]):
                fail(1, f"{take['name']}: range {first}:{last} outside source {source_range}")
            action.use_frame_range = True
            action.frame_start, action.frame_end = first, last
        report["takes"].append({"name": take["name"], "source": take["path"], "sha256": sha256(take["path"]),
                                "source_action": source_action,
                                "source_frames": source_range, "kept_frames": tuple(action.frame_range)})
        if i:
            for o in objects:
                bpy.data.objects.remove(o, do_unlink=True)
    # All takes drive the one kept rig; the exporter writes each as "Rig|<action>".
    rig.animation_data_create()
    first_action = bpy.data.actions[takes[0]["name"]]
    rig.animation_data.action = first_action
    if hasattr(rig.animation_data, "action_suitable_slots") and rig.animation_data.action_suitable_slots:
        rig.animation_data.action_slot = rig.animation_data.action_suitable_slots[0]
    bpy.context.scene.render.fps = 24
    for a in list(bpy.data.actions):
        if a.name not in {t["name"] for t in takes}:
            bpy.data.actions.remove(a)

    os.makedirs(out_dir, exist_ok=True)
    fbx = os.path.join(out_dir, enemy_id + ".fbx")
    bpy.ops.object.select_all(action="DESELECT")
    rig.select_set(True)
    body.select_set(True)
    bpy.ops.export_scene.fbx(
        filepath=fbx, use_selection=True, object_types={"MESH", "ARMATURE"},
        apply_unit_scale=True, apply_scale_options="FBX_SCALE_ALL", axis_forward="-Z", axis_up="Y",
        use_mesh_modifiers=True, mesh_smooth_type="FACE", add_leaf_bones=False,
        primary_bone_axis="Y", secondary_bone_axis="X", use_armature_deform_only=True,
        bake_space_transform=False, bake_anim=True, bake_anim_use_all_bones=True,
        bake_anim_use_nla_strips=False, bake_anim_use_all_actions=True, bake_anim_force_startend_keying=True,
        bake_anim_simplify_factor=0.0, use_custom_props=False, path_mode="STRIP", embed_textures=False)
    tex_dir = os.path.join(out_dir, enemy_id + "_tex")
    os.makedirs(tex_dir, exist_ok=True)
    tex = os.path.join(tex_dir, enemy_id + ".png")
    source_png = bpy.path.abspath(image.filepath)
    if image.packed_file or not os.path.isfile(source_png):
        image.filepath_raw, image.file_format = tex, "PNG"
        image.save()
    else:
        shutil.copyfile(source_png, tex)

    # Re-import the result and check every take landed with its frame count.
    bpy.ops.wm.read_factory_settings(use_empty=True)
    bpy.ops.import_scene.fbx(filepath=fbx, use_anim=True)
    found = {a.name.split("|")[-1]: tuple(a.frame_range) for a in bpy.data.actions}
    report["reimport"] = {"objects": sorted(f"{o.type}:{o.name}" for o in bpy.data.objects),
                          "materials": sorted(m.name for m in bpy.data.materials), "takes": found,
                          "fbx_sha256": sha256(fbx), "texture_sha256": sha256(tex)}
    problems = []
    for t in report["takes"]:
        got = found.get(t["name"])
        want = t["kept_frames"][1] - t["kept_frames"][0]
        if got is None:
            problems.append(f"take {t['name']} missing after re-import")
        elif abs((got[1] - got[0]) - want) > 1.01:
            problems.append(f"take {t['name']} spans {got}, expected {want} frames")
    if sorted(found) != sorted(t["name"] for t in takes):
        problems.append(f"re-imported takes {sorted(found)} differ from requested")
    if "MESH:Body" not in report["reimport"]["objects"] or "ARMATURE:Rig" not in report["reimport"]["objects"]:
        problems.append("Rig/Body objects missing after re-import")
    report["problems"] = problems
    with open(os.path.join(out_dir, enemy_id + "_merge_report.json"), "w", encoding="utf-8") as f:
        json.dump(report, f, indent=1)
    if problems:
        fail(1, "; ".join(problems))
    print(f"merge_tripo_enemy_takes: wrote {fbx} with takes {sorted(found)}")


if __name__ == "__main__":
    main()
