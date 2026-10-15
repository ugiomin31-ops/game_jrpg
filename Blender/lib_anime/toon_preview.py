"""Toon preview renders approximating the in-game Abyss/Toon shader (cel bands, rim, inverted-hull outline)."""
import math
import os

import bpy
from mathutils import Euler, Vector


def _toon_material():
    m = bpy.data.materials.get("PreviewToon")
    if m:
        return m
    m = bpy.data.materials.new("PreviewToon")
    m.use_nodes = True
    nt = m.node_tree
    nt.nodes.clear()
    out = nt.nodes.new("ShaderNodeOutputMaterial")
    col = nt.nodes.new("ShaderNodeVertexColor")
    col.layer_name = "Col"
    diff = nt.nodes.new("ShaderNodeBsdfDiffuse")
    s2r = nt.nodes.new("ShaderNodeShaderToRGB")
    ramp = nt.nodes.new("ShaderNodeValToRGB")
    ramp.color_ramp.interpolation = "CONSTANT"
    e = ramp.color_ramp.elements
    e[0].position, e[0].color = 0.0, (0.52, 0.50, 0.70, 1)
    e[1].position, e[1].color = 0.18, (1.0, 1.0, 1.0, 1)
    mul = nt.nodes.new("ShaderNodeMix")
    mul.data_type = "RGBA"
    mul.blend_type = "MULTIPLY"
    mul.inputs[0].default_value = 1.0
    lw = nt.nodes.new("ShaderNodeLayerWeight")
    lw.inputs[0].default_value = 0.12
    rim = nt.nodes.new("ShaderNodeMath")
    rim.operation = "GREATER_THAN"
    rim.inputs[1].default_value = 0.72
    add = nt.nodes.new("ShaderNodeMix")
    add.data_type = "RGBA"
    add.blend_type = "ADD"
    add.inputs[7].default_value = (0.22, 0.20, 0.17, 1)
    emit = nt.nodes.new("ShaderNodeEmission")
    L = nt.links.new
    L(diff.outputs[0], s2r.inputs[0])
    L(s2r.outputs[0], ramp.inputs[0])
    L(ramp.outputs[0], mul.inputs[6])
    L(col.outputs[0], mul.inputs[7])
    L(lw.outputs[1], rim.inputs[0])
    L(rim.outputs[0], add.inputs[0])
    L(mul.outputs[2], add.inputs[6])
    L(add.outputs[2], emit.inputs[0])
    L(emit.outputs[0], out.inputs[0])
    return m


def _outline_material():
    m = bpy.data.materials.get("PreviewOutline")
    if m:
        return m
    m = bpy.data.materials.new("PreviewOutline")
    m.use_nodes = True
    m.use_backface_culling = True
    nt = m.node_tree
    nt.nodes.clear()
    out = nt.nodes.new("ShaderNodeOutputMaterial")
    emit = nt.nodes.new("ShaderNodeEmission")
    emit.inputs[0].default_value = (0.08, 0.05, 0.09, 1)
    nt.links.new(emit.outputs[0], out.inputs[0])
    return m


def render(path, objects, views=((90, 0, 0), (90, 0, 35)), size=768, outline=0.0035, bg=(0.17, 0.17, 0.2), focus=None, span=None, aspect=0.62):
    """Renders each view side by side into one PNG at path."""
    sc = bpy.context.scene
    sc.render.engine = "BLENDER_EEVEE" if "BLENDER_EEVEE" in {e.identifier for e in bpy.types.RenderSettings.bl_rna.properties["engine"].enum_items} else "BLENDER_EEVEE_NEXT"
    toon, line = _toon_material(), _outline_material()
    saved = {}
    for o in objects:
        saved[o.name] = [s.material for s in o.material_slots]
        o.data.materials.clear()
        o.data.materials.append(toon)
        o.data.materials.append(line)
        md = o.modifiers.new("PreviewOutline", "SOLIDIFY")
        md.thickness = outline
        md.offset = 1.0
        md.use_flip_normals = True
        md.material_offset = 1
    sun = bpy.data.objects.new("PreviewSun", bpy.data.lights.new("PreviewSun", "SUN"))
    sun.data.energy = 3.0
    sun.rotation_euler = Euler((math.radians(50), 0, math.radians(-35)))
    sc.collection.objects.link(sun)
    world = sc.world or bpy.data.worlds.new("W")
    sc.world = world
    world.use_nodes = True
    world.node_tree.nodes["Background"].inputs[0].default_value = (*bg, 1)
    lo = Vector((1e9,) * 3)
    hi = Vector((-1e9,) * 3)
    dg = bpy.context.evaluated_depsgraph_get()
    for o in objects:
        oe = o.evaluated_get(dg)
        for c in oe.bound_box:
            w = oe.matrix_world @ Vector(c)
            lo = Vector(map(min, lo, w))
            hi = Vector(map(max, hi, w))
    center = Vector(focus) if focus else (lo + hi) / 2
    height = span or (hi.z - lo.z)
    cam = bpy.data.objects.new("PreviewCam", bpy.data.cameras.new("PreviewCam"))
    cam.data.type = "ORTHO"
    cam.data.ortho_scale = height * 1.12
    sc.collection.objects.link(cam)
    sc.camera = cam
    sc.render.resolution_x = int(size * aspect)
    sc.render.resolution_y = size
    sc.render.film_transparent = False
    sc.view_settings.view_transform = "Standard"
    tiles = []
    for i, ang in enumerate(views):
        rx, ry, rz = [math.radians(a) for a in ang]
        d = Euler((rx, ry, rz)).to_matrix() @ Vector((0, 0, 1))
        cam.location = center + d * 6
        cam.rotation_euler = Euler((rx, ry, rz))
        tile = f"{path}.{i}.png"
        sc.render.filepath = tile
        bpy.ops.render.render(write_still=True)
        tiles.append(tile)
    for o in objects:
        o.modifiers.remove(o.modifiers["PreviewOutline"])
        o.data.materials.clear()
        for m in saved[o.name]:
            o.data.materials.append(m)
    bpy.data.objects.remove(cam)
    bpy.data.objects.remove(sun)
    from PIL import Image
    ims = [Image.open(t) for t in tiles]
    sheet = Image.new("RGB", (sum(i.width for i in ims), ims[0].height))
    x = 0
    for im in ims:
        sheet.paste(im, (x, 0))
        x += im.width
    sheet.save(path)
    for t in tiles:
        os.remove(t)
    return path


# ---------------------------------------------------------------- textured toon preview (VRoid-based heroes)

NO_OUTLINE = ("_EYE", "_FACE")  # VRoid eye/brow/lash/mouth layers: no outline, alpha from the texture


def _toon_textured(src):
    """Toon version of a material: texture (if any) x vertex colour 'Col', two-band cel ramp, rim,
    alpha from the texture for the VRoid face layers and hair cards."""
    name = "PT_" + src.name
    m = bpy.data.materials.get(name)
    if m:
        return m
    img = None
    if src.node_tree:
        img = next((n.image for n in src.node_tree.nodes if n.type == "TEX_IMAGE" and n.image), None)
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    nt = m.node_tree
    nt.nodes.clear()
    out = nt.nodes.new("ShaderNodeOutputMaterial")
    col = nt.nodes.new("ShaderNodeVertexColor")
    col.layer_name = "Col"
    base = nt.nodes.new("ShaderNodeMix")
    base.data_type = "RGBA"
    base.blend_type = "MULTIPLY"
    base.inputs[0].default_value = 1.0
    nt.links.new(col.outputs["Color"], base.inputs[6])
    alpha = None
    if img is not None:
        tex = nt.nodes.new("ShaderNodeTexImage")
        tex.image = img
        nt.links.new(tex.outputs["Color"], base.inputs[7])
        alpha = tex.outputs["Alpha"]
    else:
        base.inputs[7].default_value = (1, 1, 1, 1)
    diff = nt.nodes.new("ShaderNodeBsdfDiffuse")
    diff.inputs["Color"].default_value = (1, 1, 1, 1)
    s2r = nt.nodes.new("ShaderNodeShaderToRGB")
    nt.links.new(diff.outputs[0], s2r.inputs[0])
    ramp = nt.nodes.new("ShaderNodeValToRGB")
    ramp.color_ramp.interpolation = "CONSTANT"
    e = ramp.color_ramp.elements
    e[0].position, e[0].color = 0.0, (0.68, 0.64, 0.80, 1)
    e[1].position, e[1].color = 0.10, (1, 1, 1, 1)
    nt.links.new(s2r.outputs["Color"], ramp.inputs[0])
    lit = nt.nodes.new("ShaderNodeMix")
    lit.data_type = "RGBA"
    lit.blend_type = "MULTIPLY"
    lit.inputs[0].default_value = 1.0
    nt.links.new(base.outputs[2], lit.inputs[6])
    nt.links.new(ramp.outputs["Color"], lit.inputs[7])
    emit = nt.nodes.new("ShaderNodeEmission")
    nt.links.new(lit.outputs[2], emit.inputs["Color"])
    face = any(k in src.name for k in NO_OUTLINE)
    if alpha is not None and (face or "HAIR" in src.name):
        tr = nt.nodes.new("ShaderNodeBsdfTransparent")
        mix = nt.nodes.new("ShaderNodeMixShader")
        nt.links.new(alpha, mix.inputs[0])
        nt.links.new(tr.outputs[0], mix.inputs[1])
        nt.links.new(emit.outputs[0], mix.inputs[2])
        nt.links.new(mix.outputs[0], out.inputs["Surface"])
        m.surface_render_method = "DITHERED"  # depth-correct inside one joined mesh
        m.use_backface_culling = False
    else:
        nt.links.new(emit.outputs[0], out.inputs["Surface"])
    return m


def render_textured(path, objects, views=((90, 0, 0), (90, 0, 35)), size=768, outline=0.0028, bg=(0.78, 0.78, 0.82),
                    focus=None, span=None, aspect=0.62):
    """Like render(), but keeps each material's texture (VRoid heroes); face layers get no outline."""
    sc = bpy.context.scene
    sc.render.engine = "BLENDER_EEVEE"
    line = _outline_material()
    saved = {}
    for o in objects:
        saved[o.name] = [s.material for s in o.material_slots]
        mats = [_toon_textured(m) if m else _toon_material() for m in saved[o.name]] or [_toon_material()]
        # Swap slots in place: clearing the list drops the faces' material indices.
        for i, m in enumerate(mats):
            if i < len(o.data.materials):
                o.data.materials[i] = m
            else:
                o.data.materials.append(m)
        o.data.materials.append(line)
        vg = o.vertex_groups.get("_outline") or o.vertex_groups.new(name="_outline")
        keep = [i for i, m in enumerate(saved[o.name]) if not (m and any(k in m.name for k in NO_OUTLINE))] \
            or [0]
        keep = set(keep)
        idx = {v for p in o.data.polygons if p.material_index in keep for v in p.vertices}
        vg.add(list(idx), 1.0, "REPLACE")
        md = o.modifiers.new("PreviewOutline", "SOLIDIFY")
        md.thickness = outline
        md.offset = 1.0
        md.use_flip_normals = True
        md.material_offset = len(mats)
        md.vertex_group = "_outline"
        md.thickness_vertex_group = 0.0
    world = sc.world or bpy.data.worlds.new("W")
    sc.world = world
    world.use_nodes = True
    world.node_tree.nodes["Background"].inputs[0].default_value = (*bg, 1)
    sun = bpy.data.objects.new("PreviewSun", bpy.data.lights.new("PreviewSun", "SUN"))
    sun.data.energy = 3.0
    sun.rotation_euler = Euler((math.radians(50), 0, math.radians(-35)))
    sc.collection.objects.link(sun)
    lo = Vector((1e9,) * 3)
    hi = Vector((-1e9,) * 3)
    dg = bpy.context.evaluated_depsgraph_get()
    for o in objects:
        oe = o.evaluated_get(dg)
        for c in oe.bound_box:
            w = oe.matrix_world @ Vector(c)
            lo = Vector(map(min, lo, w))
            hi = Vector(map(max, hi, w))
    center = Vector(focus) if focus else (lo + hi) / 2
    height = span or (hi.z - lo.z)
    cam = bpy.data.objects.new("PreviewCam", bpy.data.cameras.new("PreviewCam"))
    cam.data.type = "ORTHO"
    cam.data.ortho_scale = height * 1.08
    sc.collection.objects.link(cam)
    sc.camera = cam
    sc.render.resolution_x = int(size * aspect)
    sc.render.resolution_y = size
    sc.render.film_transparent = False
    sc.view_settings.view_transform = "Standard"
    tiles = []
    for i, ang in enumerate(views):
        rx, ry, rz = [math.radians(a) for a in ang]
        d = Euler((rx, ry, rz)).to_matrix() @ Vector((0, 0, 1))
        cam.location = center + d * 6
        cam.rotation_euler = Euler((rx, ry, rz))
        tile = f"{path}.{i}.png"
        sc.render.filepath = tile
        bpy.ops.render.render(write_still=True)
        tiles.append(tile)
    for o in objects:
        o.modifiers.remove(o.modifiers["PreviewOutline"])
        o.data.materials.pop()
        for i, m in enumerate(saved[o.name]):
            o.data.materials[i] = m
    bpy.data.objects.remove(cam)
    bpy.data.objects.remove(sun)
    from PIL import Image
    ims = [Image.open(t) for t in tiles]
    sheet = Image.new("RGB", (sum(i.width for i in ims), ims[0].height))
    x = 0
    for im in ims:
        sheet.paste(im, (x, 0))
        x += im.width
    sheet.save(path)
    for t in tiles:
        os.remove(t)
    return path
