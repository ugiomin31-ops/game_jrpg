"""Convert Tripo GLB results into this project's static-asset contract (Blender/README.md).

Input : Blender/tripo/source/<id>/model.glb  (from Tools/tripo/tripo_run.py model ...)
Output: Assets/_Game/Resources/Art/<out from Tools/tripo/assets.json>
        Blender/preview/tripo_<id>.png, Blender/blend/tripo_<id>.blend, conversion report in state.json

What it does, per asset:
- joins the imported meshes into one object named <id>, drops armatures/empties/cameras
- decimates to the manifest tri_budget (collapse), keeping UVs for the colour bake
- bakes the base-colour texture into the "Col" corner attribute, one flat colour per face
  (toon look; Unity adds outline/shading), then removes UVs, images and the glTF materials
- material slots M_Toon / M_Emit / M_Clear only: the whole mesh uses the manifest emit_material
  (default M_Toon); assets with emit_hint also move bright, saturated faces to M_Emit
- scales so the height is height_m, origin at bottom centre (z=0), front stays -Y
  (glTF +Z forward imports as Blender -Y); rot_z_deg in the manifest turns it if Tripo faced it elsewhere

Run (all assets that have a model.glb, or the ids given after --):
  blender -b --factory-startup -P Blender/tripo/convert.py
  blender -b --factory-startup -P Blender/tripo/convert.py -- town_fountain town_forge
"""
import colorsys
import json
import math
import os
import sys

import bmesh
import bpy
import numpy as np

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "lib"))
import abyss_bpy as A  # noqa: E402

HERE = os.path.dirname(os.path.abspath(__file__))
SOURCE = os.path.join(HERE, "source")
MANIFEST = os.path.join(A.REPO, "Tools", "tripo", "assets.json")

# Faces brighter/more saturated than this go to M_Emit when the asset has an emit_hint.
EMIT_MIN_VALUE = 0.82
EMIT_MIN_SAT = 0.45


def import_glb(path):
    before = set(bpy.data.objects)
    bpy.ops.import_scene.gltf(filepath=path)
    new = [o for o in bpy.data.objects if o not in before]
    meshes = [o for o in new if o.type == "MESH"]
    if not meshes:
        raise RuntimeError("no mesh in " + path)
    # Bake parent transforms (glTF root nodes) into the meshes, then drop everything else.
    for o in meshes:
        mw = o.matrix_world.copy()
        o.parent = None
        o.matrix_world = mw
    for o in new:
        if o.type != "MESH":
            bpy.data.objects.remove(o, do_unlink=True)
    return meshes


def join(meshes, name):
    bpy.ops.object.select_all(action="DESELECT")
    for o in meshes:
        o.select_set(True)
    bpy.context.view_layer.objects.active = meshes[0]
    if len(meshes) > 1:
        bpy.ops.object.join()
    o = bpy.context.view_layer.objects.active
    o.name = o.data.name = name
    bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)
    return o


def tri_count(o):
    return sum(len(p.vertices) - 2 for p in o.data.polygons)


def weld(o):
    """glTF splits vertices along UV seams; collapse decimation tears such meshes apart unless welded.
    UVs live on loops, so welding keeps them for the colour bake."""
    bm = bmesh.new()
    bm.from_mesh(o.data)
    bmesh.ops.remove_doubles(bm, verts=bm.verts, dist=1e-5)
    bm.to_mesh(o.data)
    bm.free()
    if o.data.has_custom_normals:  # glTF normals; shading is redone by shade_smooth below
        bpy.context.view_layer.objects.active = o
        bpy.ops.mesh.customdata_custom_splitnormals_clear()


def decimate(o, budget):
    weld(o)
    tris = tri_count(o)
    if tris <= budget:
        return tris
    mod = o.modifiers.new("Decimate", "DECIMATE")
    mod.decimate_type = "COLLAPSE"
    mod.ratio = budget / tris * 0.98
    mod.use_collapse_triangulate = True
    A.apply_modifiers(o)
    return tri_count(o)


def _base_color_image(mat):
    """The image feeding Principled Base Color (glTF importer layout), or None."""
    if not mat or not mat.use_nodes:
        return None
    for node in mat.node_tree.nodes:
        if node.type == "BSDF_PRINCIPLED":
            stack = list(node.inputs["Base Color"].links)
            while stack:
                n = stack.pop().from_node
                if n.type == "TEX_IMAGE" and n.image:
                    return n.image
                for inp in n.inputs:
                    stack.extend(inp.links)
    for node in mat.node_tree.nodes:
        if node.type == "TEX_IMAGE" and node.image:
            return node.image
    return None


def _material_flat_color(mat):
    if mat and mat.use_nodes:
        for node in mat.node_tree.nodes:
            if node.type == "BSDF_PRINCIPLED":
                c = node.inputs["Base Color"].default_value
                return [_lin_to_srgb(c[0]), _lin_to_srgb(c[1]), _lin_to_srgb(c[2])]
    return [0.6, 0.6, 0.6]


def _lin_to_srgb(c):
    return 12.92 * c if c <= 0.0031308 else 1.055 * c ** (1 / 2.4) - 0.055


def _image_array(img):
    """Image pixels as (h, w, 4) float in sRGB-encoded space (what Col stores)."""
    w, h = img.size
    px = np.empty(w * h * 4, dtype=np.float32)
    img.pixels.foreach_get(px)
    px = px.reshape(h, w, 4)
    if img.is_float or img.colorspace_settings.name not in ("sRGB",):
        # float buffers are linear; encode so the Col attribute holds sRGB like the rest of the project
        rgb = px[..., :3]
        px[..., :3] = np.where(rgb <= 0.0031308, rgb * 12.92, 1.055 * np.power(np.clip(rgb, 0, None), 1 / 2.4) - 0.055)
    return px


def bake_face_colors(o):
    """Return (n_faces, 3) sRGB colours: texture sampled at each corner + face centre, averaged."""
    me = o.data
    n_faces = len(me.polygons)
    n_loops = len(me.loops)
    mat_idx = np.empty(n_faces, dtype=np.int32)
    me.polygons.foreach_get("material_index", mat_idx)
    loop_start = np.empty(n_faces, dtype=np.int32)
    loop_total = np.empty(n_faces, dtype=np.int32)
    me.polygons.foreach_get("loop_start", loop_start)
    me.polygons.foreach_get("loop_total", loop_total)
    face_of_loop = np.repeat(np.arange(n_faces), loop_total)

    uv = None
    if me.uv_layers.active:
        uv = np.empty(n_loops * 2, dtype=np.float32)
        me.uv_layers.active.data.foreach_get("uv", uv)
        uv = uv.reshape(n_loops, 2)

    out = np.zeros((n_faces, 3), dtype=np.float32)
    for slot, mat in enumerate(me.materials):
        faces = mat_idx == slot
        if not faces.any():
            continue
        img = _base_color_image(mat)
        if img is None or uv is None or img.size[0] == 0:
            out[faces] = _material_flat_color(mat)
            continue
        px = _image_array(img)
        h, w = px.shape[:2]
        loops = faces[face_of_loop]
        luv = uv[loops] % 1.0
        xs = np.clip((luv[:, 0] * w).astype(np.int64), 0, w - 1)
        ys = np.clip((luv[:, 1] * h).astype(np.int64), 0, h - 1)
        corner = px[ys, xs, :3]
        fidx = face_of_loop[loops]
        sums = np.zeros((n_faces, 3), dtype=np.float64)
        np.add.at(sums, fidx, corner)
        # face-centre sample weighs as much as all corners together (avoids seam bleed at corners)
        cuv = np.zeros((n_faces, 2), dtype=np.float64)
        np.add.at(cuv, fidx, luv)
        cuv[faces] /= loop_total[faces, None]
        cx = np.clip((cuv[faces, 0] * w).astype(np.int64), 0, w - 1)
        cy = np.clip((cuv[faces, 1] * h).astype(np.int64), 0, h - 1)
        centre = px[cy, cx, :3]
        out[faces] = (sums[faces] / loop_total[faces, None] + centre) / 2
    return np.clip(out, 0, 1)


def write_col(o, face_rgb):
    me = o.data
    for name in [a.name for a in me.color_attributes]:
        me.color_attributes.remove(me.color_attributes[name])
    attr = me.color_attributes.new("Col", "BYTE_COLOR", "CORNER")
    me.color_attributes.active_color = attr
    totals = np.empty(len(me.polygons), dtype=np.int32)
    me.polygons.foreach_get("loop_total", totals)
    rgba = np.ones((len(me.loops), 4), dtype=np.float32)
    rgba[:, :3] = np.repeat(face_rgb, totals, axis=0)
    attr.data.foreach_set("color_srgb", rgba.ravel())


def assign_materials(o, face_rgb, asset):
    me = o.data
    base = asset.get("emit_material", "M_Toon")
    me.materials.clear()
    for name in A.MATERIALS:
        me.materials.append(A._material(name))
    slot = {n: i for i, n in enumerate(A.MATERIALS)}
    idx = np.full(len(me.polygons), slot[base], dtype=np.int32)
    emit_faces = 0
    if asset.get("emit_hint") and base == "M_Toon":
        hsv = np.array([colorsys.rgb_to_hsv(*c) for c in face_rgb])
        glow = (hsv[:, 2] >= EMIT_MIN_VALUE) & (hsv[:, 1] >= EMIT_MIN_SAT)
        idx[glow] = slot["M_Emit"]
        emit_faces = int(glow.sum())
    me.polygons.foreach_set("material_index", idx)
    # drop unused slots so Unity does not get empty submeshes
    used = sorted(set(idx.tolist()))
    remap = {old: new for new, old in enumerate(used)}
    keep = [me.materials[i] for i in used]
    me.materials.clear()
    for m in keep:
        me.materials.append(m)
    me.polygons.foreach_set("material_index", np.array([remap[i] for i in idx], dtype=np.int32))
    return {A.MATERIALS[i]: int((idx == i).sum()) for i in used}, emit_faces


def normalize(o, height, rot_z_deg):
    if rot_z_deg:
        o.rotation_euler.z = math.radians(rot_z_deg)
        bpy.context.view_layer.objects.active = o
        bpy.ops.object.transform_apply(rotation=True)
    co = np.empty(len(o.data.vertices) * 3, dtype=np.float64)
    o.data.vertices.foreach_get("co", co)
    co = co.reshape(-1, 3)
    lo, hi = co.min(0), co.max(0)
    s = height / max(hi[2] - lo[2], 1e-6)
    centre = np.array([(lo[0] + hi[0]) / 2, (lo[1] + hi[1]) / 2, lo[2]])
    co = (co - centre) * s
    o.data.vertices.foreach_set("co", co.ravel())
    o.data.update()
    o.location = (0, 0, 0)
    size = co.max(0) - co.min(0)
    return [round(float(v), 3) for v in size]


def cleanup(o):
    me = o.data
    while me.uv_layers:
        me.uv_layers.remove(me.uv_layers[0])
    for img in list(bpy.data.images):
        bpy.data.images.remove(img)
    for m in list(bpy.data.materials):
        if m.name not in A.MATERIALS and m.users == 0:
            bpy.data.materials.remove(m)


def convert(asset):
    aid = asset["id"]
    glb = os.path.join(SOURCE, aid, "model.glb")
    A.reset_scene()
    o = join(import_glb(glb), aid)
    raw_tris = tri_count(o)
    tris = decimate(o, asset["tri_budget"])
    face_rgb = bake_face_colors(o)
    write_col(o, face_rgb)
    slots, emit_faces = assign_materials(o, face_rgb, asset)
    size = normalize(o, asset["height_m"], asset.get("rot_z_deg", 0))
    cleanup(o)
    A.shade_smooth(o, 40)
    path = A.export_fbx(asset["out"], [o])
    preview = A.render_preview("tripo_" + aid, [o])
    A.save_blend("tripo_" + aid)
    report = {"source_tris": raw_tris, "tris": tris, "size_m": size, "slots": slots,
              "emit_faces": emit_faces, "fbx": os.path.relpath(path, A.REPO).replace(os.sep, "/"),
              "preview": os.path.relpath(preview, A.REPO).replace(os.sep, "/")}
    state_path = os.path.join(SOURCE, aid, "state.json")
    state = {"id": aid}
    if os.path.exists(state_path):
        with open(state_path, encoding="utf-8") as f:
            state = json.load(f)
    state["convert"] = report
    with open(state_path, "w", encoding="utf-8") as f:
        json.dump(state, f, ensure_ascii=False, indent=2)
        f.write("\n")
    print("[tripo] %s: %d -> %d tris, size %s, slots %s" % (aid, raw_tris, tris, size, slots))
    return report


def main():
    with open(MANIFEST, encoding="utf-8") as f:
        assets = json.load(f)["assets"]
    argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
    chosen = [a for a in assets if not argv or a["id"] in argv]
    failed = []
    for a in chosen:
        if not os.path.exists(os.path.join(SOURCE, a["id"], "model.glb")):
            if argv:
                print("[tripo] %s: no model.glb, skipped" % a["id"])
            continue
        try:
            convert(a)
        except Exception as e:  # keep going so one bad mesh does not block the batch
            failed.append(a["id"])
            print("[tripo] %s FAILED: %s" % (a["id"], e))
    if failed:
        sys.exit(1)


if __name__ == "__main__":
    main()
