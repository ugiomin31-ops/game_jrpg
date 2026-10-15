"""Tripo Studio export (Mixamo-rigged FBX) -> game-contract Humanoid hunter FBX.

    blender -b --factory-startup --python-exit-code 1 -P Blender/hunters_tripo/convert.py -- <hero_id> <tripo.fbx>
        [--out-dir DIR]   default ArtSource/hunters/<hero_id>/staging
        [--height M]      standing height in metres (default 1.81 = the current Blender h_dohyun, so
                          ArtLibrary.HeroDisplayHeight scales it exactly like the model it replaces)
        [--apose]         keep Tripo's A-pose rest instead of the shared T-pose (see common.py; not recommended)
        [--tex PX]        base-colour texture size (default 1024)

Output (all under DIR):
    <id>.fbx                 armature `Rig`, skinned mesh `Body`, one material `<id>`, Mixamo bone names
                             (Unity Humanoid auto-maps them) + weapon.R / weapon.L sockets under the hands
    <id>_tex/<id>.png        base colour (PNG name = material name -> AbyssArtImporter.TexturedMaterials)
    <id>.blend               the converted scene, for inspection
    <id>_report.json         re-import verification (names, bones, weights, height, facing, humanoid bones)
    preview/<id>_*.png       Workbench renders of the source (A-pose) and the exported FBX (front + 3/4)

No takes are exported: Unity retargets the hunter's existing clips through <id>_anim.fbx (anim_source.py).
"""
import math
import os
import sys

import bpy
from mathutils import Vector

sys.path.append(os.path.dirname(os.path.abspath(__file__)))
import common as C  # noqa: E402


def parse(argv):
    a = C.args_after_dashes(argv)
    if len(a) < 2:
        raise SystemExit(__doc__)
    opts = {"id": a[0], "fbx": os.path.abspath(a[1]), "out": None, "height": 1.81, "apose": False, "tex": 1024}
    i = 2
    while i < len(a):
        k = a[i]
        if k == "--out-dir":
            opts["out"] = os.path.abspath(a[i + 1]); i += 2
        elif k == "--height":
            opts["height"] = float(a[i + 1]); i += 2
        elif k == "--tex":
            opts["tex"] = int(a[i + 1]); i += 2
        elif k == "--apose":
            opts["apose"] = True; i += 1
        else:
            raise SystemExit("unknown option " + k)
    opts["out"] = opts["out"] or os.path.join(C.REPO, "ArtSource", "hunters", opts["id"], "staging")
    return opts


def base_color_image(mesh):
    for mat in mesh.data.materials:
        if mat is None or mat.node_tree is None:
            continue
        for n in mat.node_tree.nodes:
            if n.type == "TEX_IMAGE" and n.image is not None:
                if any(l.to_socket.name == "Base Color" for l in n.outputs["Color"].links):
                    return n.image
    raise RuntimeError("no base colour texture on " + mesh.name)


def write_texture(src, path, size):
    """Downscale the Tripo base colour (sRGB JPEG) to a straight sRGB PNG."""
    os.makedirs(os.path.dirname(path), exist_ok=True)
    img = src.copy()
    img.name = os.path.splitext(os.path.basename(path))[0] + "_tmp"
    if tuple(img.size) != (size, size):
        img.scale(size, size)
    img.filepath_raw = path
    img.file_format = "PNG"
    img.save()
    bpy.data.images.remove(img)
    return path


def make_material(body, name, png):
    for m in list(body.data.materials):
        if m is not None:
            m.name = m.name + "_tripo_src"
    mat = bpy.data.materials.new(name)
    mat.use_nodes = True
    nt = mat.node_tree
    bsdf = next(n for n in nt.nodes if n.type == "BSDF_PRINCIPLED")
    bsdf.inputs["Roughness"].default_value = 0.8
    bsdf.inputs["Metallic"].default_value = 0.0
    tex = nt.nodes.new("ShaderNodeTexImage")
    tex.image = bpy.data.images.load(png)
    tex.image.name = name
    tex.image.colorspace_settings.name = "sRGB"
    nt.links.new(tex.outputs["Color"], bsdf.inputs["Base Color"])
    body.data.materials.clear()
    body.data.materials.append(mat)
    for poly in body.data.polygons:
        poly.material_index = 0
    for m in list(bpy.data.materials):
        if m.users == 0:
            bpy.data.materials.remove(m)
    for im in list(bpy.data.images):
        if im.users == 0:
            bpy.data.images.remove(im)
    return mat


def add_weapon_sockets(rig, scale_hint):
    """weapon.R / weapon.L like the Blender heroes: head = grip inside the closed hand, +Y = weapon direction,
    +Z = blade edge side (old-rig values, both measured in an arms-down rest). Added in the A-pose rest so the
    T-pose swing carries them with the hands."""
    C.select([rig])
    bpy.ops.object.mode_set(mode="EDIT")
    eb = rig.data.edit_bones
    made = {}
    for side, tag, sx in (("Left", "L", 1.0), ("Right", "R", -1.0)):
        hand = eb[C.MIX + side + "Hand"]
        mid = eb[C.MIX + side + "HandMiddle1"]
        wrist = hand.head.copy()
        span = mid.head - wrist
        # 3/4 of the way to the knuckles, nudged toward the palm (palms face the body in the A-pose).
        grip = wrist + span * 0.75 + Vector((-sx * 0.12 * span.length, 0.0, 0.0))
        b = eb.new("weapon." + tag)
        b.head = grip
        b.tail = grip + C.WEAPON_Y * 0.1 * scale_hint
        b.align_roll(C.WEAPON_Z)
        b.parent = hand
        b.use_connect = False
        b.use_deform = True  # kept by use_armature_deform_only; has no vertex group, so it never moves the mesh
        made["weapon." + tag] = [round(v, 4) for v in grip]
    bpy.ops.object.mode_set(mode="OBJECT")
    return made


def unweighted(body):
    n = 0
    for v in body.data.vertices:
        if not any(g.weight > 1e-4 for g in v.groups):
            n += 1
    return n


def tris(body):
    return sum(len(p.vertices) - 2 for p in body.data.polygons)


def convert(o):
    hid = o["id"]
    out = o["out"]
    prev = os.path.join(out, "preview")
    C.reset()
    objs = C.import_fbx(o["fbx"])
    rig = C.only(objs, "ARMATURE")
    body = C.only(objs, "MESH")
    for ob in objs:
        if ob not in (rig, body):
            bpy.data.objects.remove(ob)
    rig.animation_data_clear()
    body.animation_data_clear()
    for act in list(bpy.data.actions):
        bpy.data.actions.remove(act)
    C.clear_pose(rig)
    if body.parent != rig:
        raise RuntimeError("mesh is not parented to the armature")

    # 1. Flatten object transforms, scale to height, feet on z=0, hips over the origin.
    C.select([rig, body], rig)
    bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)
    lo, hi = C.world_bounds([body])
    src_height = hi.z - lo.z
    s = o["height"] / src_height
    hips = rig.data.bones[C.MIX + "Hips"].head_local
    rig.scale = (s, s, s)
    rig.location = (-hips.x * s, -hips.y * s, -lo.z * s)
    C.update()
    C.select([rig, body], rig)
    bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)
    C.update()
    rig.name = rig.data.name = "Rig"
    body.name = body.data.name = "Body"

    # 2. Contract checks: faces -Y, its left is +X.
    bones = rig.data.bones
    faces_minus_y = bones[C.MIX + "LeftToe_End"].head_local.y < bones[C.MIX + "LeftFoot"].head_local.y
    left_is_plus_x = bones[C.MIX + "LeftArm"].head_local.x > 0 > bones[C.MIX + "RightArm"].head_local.x
    if not (faces_minus_y and left_is_plus_x):
        raise RuntimeError(f"orientation: faces -Y {faces_minus_y}, left +X {left_is_plus_x}")

    # 3. Texture + single material named after the hero.
    png = os.path.join(out, hid + "_tex", hid + ".png")
    write_texture(base_color_image(body), png, o["tex"])
    make_material(body, hid, png)

    C.render(os.path.join(prev, hid + "_src_front.png"), [body], 0)
    C.render(os.path.join(prev, hid + "_src_34.png"), [body], 35)

    # 4. Weapon sockets, then the shared T-pose rest.
    sockets = add_weapon_sockets(rig, o["height"] / 1.81)
    swing = {}
    if not o["apose"]:
        names = {b.name[len(C.MIX):]: b.name for b in rig.data.bones if b.name.startswith(C.MIX)}
        swing = C.pose_tpose(rig, names)
        C.apply_pose_as_rest(rig, [body])
        # Straightened legs move the soles a few mm: put the feet back on z=0.
        lo2, _ = C.world_bounds([body])
        rig.location.z -= lo2.z
        C.update()
        C.select([rig, body], rig)
        bpy.ops.object.transform_apply(location=True, rotation=False, scale=False)
        C.update()

    os.makedirs(out, exist_ok=True)
    fbx = C.export_fbx(os.path.join(out, hid + ".fbx"), [rig, body], animated=False, path_mode="RELATIVE", force=True)
    bpy.ops.wm.save_as_mainfile(filepath=os.path.join(out, hid + ".blend"), compress=True)
    return fbx, {"source_height_m": round(src_height, 4), "scale": round(s, 5), "tpose_swing_deg": swing,
                 "weapon_sockets": sockets, "rest": "A-pose (Tripo)" if o["apose"] else "T-pose"}


def verify(o, fbx, info):
    hid = o["id"]
    out = o["out"]
    prev = os.path.join(out, "preview")
    C.reset()
    objs = C.import_fbx(fbx)
    rig = C.only(objs, "ARMATURE")
    body = C.only(objs, "MESH")
    C.clear_pose(rig)
    lo, hi = C.world_bounds([body])
    bones = rig.data.bones
    mats = [m.name for m in body.data.materials]
    images = sorted({n.image.filepath for m in body.data.materials if m and m.node_tree
                     for n in m.node_tree.nodes if n.type == "TEX_IMAGE" and n.image})
    arm = {}
    for side in ("Left", "Right"):
        d = bones[C.MIX + side + "ForeArm"].head_local - bones[C.MIX + side + "Arm"].head_local
        arm[side] = round(math.degrees(math.asin(max(-1, min(1, d.normalized().z)))), 2)
    groups = {g.name for g in body.vertex_groups}
    weighted_bones = sorted(b.name for b in bones if b.name in groups)
    report = dict(info)
    report.update({
        "id": hid, "fbx": os.path.relpath(fbx, C.REPO).replace("\\", "/"),
        "objects": sorted(ob.name for ob in objs), "armature": rig.name, "mesh": body.name,
        "materials": mats, "texture_refs": images,
        "triangles": tris(body), "vertices": len(body.data.vertices), "unweighted_vertices": unweighted(body),
        "bones": len(bones), "weighted_bones": len(weighted_bones),
        "bounds_min": [round(v, 4) for v in lo], "bounds_max": [round(v, 4) for v in hi],
        "height_m": round(hi.z - lo.z, 4),
        "faces_minus_y": bones[C.MIX + "LeftToe_End"].head_local.y < bones[C.MIX + "LeftFoot"].head_local.y,
        "left_is_plus_x": bones[C.MIX + "LeftArm"].head_local.x > 0,
        "upper_arm_elevation_deg": arm,
        "weapon_sockets_present": {t: (t in bones and bones[t].parent is not None and bones[t].parent.name)
                                   for t in ("weapon.R", "weapon.L")},
        "humanoid": C.humanoid_check(rig),
        "takes": [a.name for a in bpy.data.actions],
    })
    ok = (report["armature"] == "Rig" and report["mesh"] == "Body" and mats == [hid] and report["unweighted_vertices"] == 0
          and not report["humanoid"]["missing_required"] and report["humanoid"]["hips_is_ancestor"]
          and report["faces_minus_y"] and report["left_is_plus_x"] and abs(lo.z) < 0.01
          and abs(report["height_m"] - o["height"]) < 0.02 and not report["takes"]
          and all(report["weapon_sockets_present"].values()) and any(hid + ".png" in p for p in images))
    report["ok"] = ok
    shots = [C.render(os.path.join(prev, f"{hid}_front.png"), [body], 0),
             C.render(os.path.join(prev, f"{hid}_34.png"), [body], 35),
             C.render(os.path.join(prev, f"{hid}_back.png"), [body], 180)]
    C.stitch([os.path.join(prev, f"{hid}_src_front.png"), os.path.join(prev, f"{hid}_src_34.png")] + shots[:2],
             os.path.join(prev, f"{hid}_sheet.png"), 4)
    C.write_json(os.path.join(out, hid + "_report.json"), report)
    print("REPORT", report)
    if not ok:
        raise SystemExit("verification failed: see " + os.path.join(out, hid + "_report.json"))


if __name__ == "__main__":
    opts = parse(sys.argv)
    path, info = convert(opts)
    verify(opts, path, info)
