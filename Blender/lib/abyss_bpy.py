"""Shared Blender helpers for 심연의 미궁 (Abyss Labyrinth) asset generators.

Contract (Unity side relies on all of this — see Blender/README.md):
- 1 Blender unit = 1 m. Characters stand on z=0, face -Y (Blender front view).
- Colour lives in the "Col" colour attribute (sRGB, per face corner). Textures are not used, except by the
  textured anime heroes (lib_humanoid/textured.py: <id>_tex/<material>.png next to the FBX).
- Material slots are ONLY: M_Toon (opaque toon), M_Emit (glowing), M_Clear (translucent toon).
  Unity remaps them by name to shared materials.
- Animated assets: one armature object named "Rig", one skinned mesh named "Body" (rigid weights,
  one bone per part). Actions are named exactly Idle/Run/Attack/Cast/Hit/Die/Victory (+ extras)
  and exported as FBX takes "Rig|<Action>"; Unity strips the "Rig|" prefix.
- Static assets: one FBX may contain several root objects; each becomes a child in Unity.

Run generators with:  blender -b --factory-startup -P <script.py>
Generators import this module via sys.path.append(<repo>/Blender/lib).
"""
import math
import os

import bmesh
import bpy
from mathutils import Euler, Matrix, Vector

REPO = os.path.normpath(os.path.join(os.path.dirname(__file__), "..", ".."))
ASSETS = os.path.join(REPO, "Assets", "_Game", "Resources", "Art")
BLEND_DIR = os.path.join(REPO, "Blender", "blend")
PREVIEW_DIR = os.path.join(REPO, "Blender", "preview")
FPS = 30
MATERIALS = ("M_Toon", "M_Emit", "M_Clear")

# ---------------------------------------------------------------- scene

def reset_scene():
    bpy.ops.wm.read_factory_settings(use_empty=True)
    sc = bpy.context.scene
    sc.render.fps = FPS
    sc.unit_settings.system = "METRIC"
    sc.unit_settings.scale_length = 1.0
    for name in MATERIALS:
        _material(name)
    return sc


def _material(name):
    m = bpy.data.materials.get(name)
    if m:
        return m
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    nt = m.node_tree
    bsdf = nt.nodes.get("Principled BSDF")
    attr = nt.nodes.new("ShaderNodeVertexColor")
    attr.layer_name = "Col"
    nt.links.new(attr.outputs["Color"], bsdf.inputs["Base Color"])
    bsdf.inputs["Roughness"].default_value = 0.8
    if name == "M_Emit":
        nt.links.new(attr.outputs["Color"], bsdf.inputs["Emission Color"])
        bsdf.inputs["Emission Strength"].default_value = 2.0
    if name == "M_Clear":
        bsdf.inputs["Alpha"].default_value = 0.7
    return m


def hexcol(h, a=1.0):
    """'#rrggbb' (sRGB) -> RGBA tuple in sRGB space (what the Col attribute stores)."""
    h = h.lstrip("#")
    return (int(h[0:2], 16) / 255, int(h[2:4], 16) / 255, int(h[4:6], 16) / 255, a)


def _as_rgba(c):
    if isinstance(c, str):
        return hexcol(c)
    return tuple(c) if len(c) == 4 else (c[0], c[1], c[2], 1.0)


# ---------------------------------------------------------------- mesh building

def _new_obj(name, mesh):
    obj = bpy.data.objects.new(name, mesh)
    bpy.context.scene.collection.objects.link(obj)
    return obj


def _from_bmesh(name, bm):
    me = bpy.data.meshes.new(name)
    bm.to_mesh(me)
    bm.free()
    return _new_obj(name, me)


def paint(obj, color, mat="M_Toon"):
    """Fill the whole object with one colour and one material slot."""
    color = _as_rgba(color)
    me = obj.data
    if "Col" not in me.color_attributes:
        me.color_attributes.new("Col", "BYTE_COLOR", "CORNER")
    attr = me.color_attributes["Col"]
    for d in attr.data:
        d.color_srgb = color
    me.materials.clear()
    me.materials.append(_material(mat))
    for p in me.polygons:
        p.material_index = 0
    return obj


def gradient(obj, bottom, top, axis=2):
    """Vertical (default z) colour gradient over the object's local bounds."""
    bottom, top = _as_rgba(bottom), _as_rgba(top)
    me = obj.data
    if "Col" not in me.color_attributes:
        me.color_attributes.new("Col", "BYTE_COLOR", "CORNER")
    attr = me.color_attributes["Col"]
    vs = [v.co[axis] for v in me.vertices]
    lo, hi = min(vs), max(vs)
    span = max(hi - lo, 1e-6)
    for loop in me.loops:
        t = (me.vertices[loop.vertex_index].co[axis] - lo) / span
        attr.data[loop.index].color_srgb = tuple(bottom[i] * (1 - t) + top[i] * t for i in range(4))
    return obj


def volume_shade(obj, floor=0.8, rise=0.55, under=0.16, skip=("M_Emit",)):
    """Bake soft form shading into Col so a creature reads as a solid, grounded figure like the heroes:
    the lower `rise` share of its height fades toward `floor` brightness, and surfaces facing down lose up
    to `under`. Uses smooth vertex normals (no faceting); glowing parts (M_Emit) are left untouched."""
    me = obj.data
    attr = me.color_attributes.get("Col")
    if attr is None or len(me.vertices) == 0:
        return obj
    mw = obj.matrix_world
    nm = mw.to_3x3().inverted_safe().transposed()
    wz = [(mw @ v.co).z for v in me.vertices]
    wn = [(nm @ v.normal).normalized().z for v in me.vertices]
    lo, hi = min(wz), max(wz)
    span = max(hi - lo, 1e-6)
    names = [m.name.split(".")[0] if m else "" for m in me.materials]
    for p in me.polygons:
        if names and names[p.material_index] in skip:
            continue
        for li in p.loop_indices:
            vi = me.loops[li].vertex_index
            t = min(1.0, (wz[vi] - lo) / span / rise)
            t = t * t * (3 - 2 * t)
            k = (floor + (1 - floor) * t) * (1 - under * max(0.0, -wn[vi]))
            c = attr.data[li].color_srgb
            attr.data[li].color_srgb = (c[0] * k, c[1] * k, c[2] * k, c[3])
    return obj


def _place(obj, loc, rot, scale):
    obj.location = loc
    obj.rotation_euler = Euler([math.radians(a) for a in rot])
    obj.scale = scale if hasattr(scale, "__len__") else (scale, scale, scale)
    return obj


def box(name, size=(1, 1, 1), loc=(0, 0, 0), rot=(0, 0, 0), color="#888888", mat="M_Toon", bevel=0.0, seg=2):
    bm = bmesh.new()
    bmesh.ops.create_cube(bm, size=1.0)
    for v in bm.verts:
        v.co = Vector((v.co.x * size[0], v.co.y * size[1], v.co.z * size[2]))
    o = _from_bmesh(name, bm)
    if bevel > 0:
        md = o.modifiers.new("bevel", "BEVEL")
        md.width = bevel
        md.segments = seg
        md.limit_method = "ANGLE"
        apply_modifiers(o)
    _place(o, loc, rot, 1)
    return paint(o, color, mat)


def sphere(name, r=0.5, loc=(0, 0, 0), rot=(0, 0, 0), scale=(1, 1, 1), color="#888888", mat="M_Toon", seg=24, rings=14):
    bm = bmesh.new()
    bmesh.ops.create_uvsphere(bm, u_segments=seg, v_segments=rings, radius=r)
    o = _from_bmesh(name, bm)
    _place(o, loc, rot, scale)
    shade_smooth(o)
    return paint(o, color, mat)


def cyl(name, r=0.5, depth=1.0, loc=(0, 0, 0), rot=(0, 0, 0), scale=(1, 1, 1), color="#888888", mat="M_Toon", seg=20, r2=None, cap=True, smooth=True):
    """Cylinder / truncated cone along local Z, centred at loc. r2 = top radius."""
    bm = bmesh.new()
    bmesh.ops.create_cone(bm, cap_ends=cap, cap_tris=False, segments=seg, radius1=r, radius2=r if r2 is None else r2, depth=depth)
    o = _from_bmesh(name, bm)
    _place(o, loc, rot, scale)
    if smooth:
        shade_smooth(o, angle=50)
    return paint(o, color, mat)


def cone(name, r=0.5, depth=1.0, **kw):
    return cyl(name, r=r, depth=depth, r2=0.0, **kw)


def torus(name, R=0.5, r=0.1, loc=(0, 0, 0), rot=(0, 0, 0), scale=(1, 1, 1), color="#888888", mat="M_Toon", seg=32, minor=12):
    bpy.ops.mesh.primitive_torus_add(major_radius=R, minor_radius=r, major_segments=seg, minor_segments=minor)
    o = bpy.context.active_object
    o.name = name
    _place(o, loc, rot, scale)
    shade_smooth(o)
    return paint(o, color, mat)


def lathe(name, profile, loc=(0, 0, 0), rot=(0, 0, 0), scale=(1, 1, 1), color="#888888", mat="M_Toon", seg=24):
    """Revolve a list of (radius, z) points around local Z. Great for bodies, potions, hats."""
    bm = bmesh.new()
    rings = []
    for (rad, z) in profile:
        ring = []
        for i in range(seg):
            a = 2 * math.pi * i / seg
            ring.append(bm.verts.new((math.cos(a) * rad, math.sin(a) * rad, z)))
        rings.append(ring)
    for a, b in zip(rings, rings[1:]):
        for i in range(seg):
            j = (i + 1) % seg
            bm.faces.new((a[i], a[j], b[j], b[i]))
    if profile[0][0] > 1e-4:
        bm.faces.new(list(reversed(rings[0])))
    if profile[-1][0] > 1e-4:
        bm.faces.new(rings[-1])
    bmesh.ops.remove_doubles(bm, verts=bm.verts, dist=1e-5)
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    o = _from_bmesh(name, bm)
    _place(o, loc, rot, scale)
    shade_smooth(o)
    return paint(o, color, mat)


def extrude_shape(name, pts2d, depth=0.05, loc=(0, 0, 0), rot=(0, 0, 0), scale=(1, 1, 1), color="#888888", mat="M_Toon", bevel=0.0):
    """Flat polygon (x, z) in the XZ plane extruded along Y by depth. For blades, wings, leaves, ears."""
    bm = bmesh.new()
    vs = [bm.verts.new((x, -depth / 2, z)) for (x, z) in pts2d]
    f = bm.faces.new(vs)
    r = bmesh.ops.extrude_face_region(bm, geom=[f])
    moved = [e for e in r["geom"] if isinstance(e, bmesh.types.BMVert)]
    bmesh.ops.translate(bm, verts=moved, vec=(0, depth, 0))
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    o = _from_bmesh(name, bm)
    if bevel > 0:
        md = o.modifiers.new("bevel", "BEVEL")
        md.width = bevel
        md.segments = 2
        apply_modifiers(o)
    _place(o, loc, rot, scale)
    return paint(o, color, mat)


def tube(name, points, radius=0.05, color="#888888", mat="M_Toon", seg=10, taper_end=1.0):
    """Tube through 3D points (polyline with smooth bevel). For horns, tails, tentacles, vines, bows."""
    cu = bpy.data.curves.new(name, "CURVE")
    cu.dimensions = "3D"
    sp = cu.splines.new("POLY")
    sp.points.add(len(points) - 1)
    for i, p in enumerate(points):
        t = i / max(len(points) - 1, 1)
        sp.points[i].co = (p[0], p[1], p[2], 1)
        sp.points[i].radius = 1.0 + (taper_end - 1.0) * t
    cu.bevel_depth = radius
    cu.bevel_resolution = max(1, seg // 4)
    cu.use_fill_caps = True
    o = bpy.data.objects.new(name, cu)
    bpy.context.scene.collection.objects.link(o)
    o = to_mesh(o)
    shade_smooth(o)
    return paint(o, color, mat)


def to_mesh(o):
    bpy.ops.object.select_all(action="DESELECT")
    bpy.context.view_layer.objects.active = o
    o.select_set(True)
    bpy.ops.object.convert(target="MESH")
    return bpy.context.active_object


def shade_smooth(o, angle=None):
    for p in o.data.polygons:
        p.use_smooth = True
    if angle is not None:
        bpy.context.view_layer.objects.active = o
        try:
            bpy.ops.object.select_all(action="DESELECT")
            o.select_set(True)
            bpy.ops.object.shade_auto_smooth(angle=math.radians(angle))
            apply_modifiers(o)
        except Exception:
            pass
    return o


def subdivide(o, levels=1):
    md = o.modifiers.new("subd", "SUBSURF")
    md.levels = levels
    md.render_levels = levels
    apply_modifiers(o)
    shade_smooth(o)
    return o


def deform(o, fn):
    """Apply fn(Vector local co) -> Vector to every vertex. For organic shaping (noise, bends)."""
    for v in o.data.vertices:
        v.co = fn(v.co.copy())
    o.data.update()
    return o


def apply_modifiers(o):
    bpy.ops.object.select_all(action="DESELECT")
    bpy.context.view_layer.objects.active = o
    o.select_set(True)
    for md in list(o.modifiers):
        bpy.ops.object.modifier_apply(modifier=md.name)
    return o


def apply_transform(o):
    bpy.ops.object.select_all(action="DESELECT")
    bpy.context.view_layer.objects.active = o
    o.select_set(True)
    bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)
    return o


def mirror_x(o, name=None):
    """Duplicate an object mirrored across X (for symmetric parts)."""
    c = o.copy()
    c.data = o.data.copy()
    c.name = name or o.name.replace(".L", ".R").replace("_L", "_R")
    bpy.context.scene.collection.objects.link(c)
    c.location.x = -o.location.x
    c.rotation_euler = Euler((o.rotation_euler.x, -o.rotation_euler.y, -o.rotation_euler.z))
    c.scale = (-o.scale.x, o.scale.y, o.scale.z)
    apply_transform(c)
    bpy.ops.object.select_all(action="DESELECT")
    c.select_set(True)
    bpy.context.view_layer.objects.active = c
    bpy.ops.object.mode_set(mode="EDIT")
    bpy.ops.mesh.select_all(action="SELECT")
    bpy.ops.mesh.normals_make_consistent(inside=False)
    bpy.ops.object.mode_set(mode="OBJECT")
    return c


def join(objs, name):
    objs = [o for o in objs if o is not None]
    for o in objs:
        apply_transform(o)
    bpy.ops.object.select_all(action="DESELECT")
    for o in objs:
        o.select_set(True)
    bpy.context.view_layer.objects.active = objs[0]
    bpy.ops.object.join()
    o = bpy.context.active_object
    o.name = name
    o.data.name = name
    return o


# ---------------------------------------------------------------- rigging

def armature(bones):
    """bones: list of (name, head, tail, parent_or_None). Returns the armature object "Rig"."""
    arm = bpy.data.armatures.new("Rig")
    rig = bpy.data.objects.new("Rig", arm)
    bpy.context.scene.collection.objects.link(rig)
    bpy.context.view_layer.objects.active = rig
    bpy.ops.object.select_all(action="DESELECT")
    rig.select_set(True)
    bpy.ops.object.mode_set(mode="EDIT")
    for name, head, tail, parent in bones:
        eb = arm.edit_bones.new(name)
        eb.head = head
        eb.tail = tail
        if parent:
            eb.parent = arm.edit_bones[parent]
    bpy.ops.object.mode_set(mode="OBJECT")
    for pb in rig.pose.bones:
        pb.rotation_mode = "XYZ"
    return rig


def bind(part, bone):
    """Mark every vertex of part as 100 % owned by bone (rigid skinning)."""
    vg = part.vertex_groups.get(bone) or part.vertex_groups.new(name=bone)
    vg.add(list(range(len(part.data.vertices))), 1.0, "REPLACE")
    return part


def skin(parts_by_bone, rig, name="Body"):
    """parts_by_bone: {bone: [objects]}. Joins everything into one mesh bound to rig."""
    objs = []
    for bone, parts in parts_by_bone.items():
        for p in parts:
            bind(p, bone)
            objs.append(p)
    body = join(objs, name)
    md = body.modifiers.new("Armature", "ARMATURE")
    md.object = rig
    body.parent = rig
    return body


# ---------------------------------------------------------------- animation

class Anim:
    """Keyframe helper. Usage:
        with Anim(rig, "Idle", length=48) as a:
            a.rot("spine", 0, (0, 0, 0)); a.rot("spine", 24, (5, 0, 0)); a.rot("spine", 48, (0, 0, 0))
    Rotations in degrees (bone-local XYZ euler), locations in bone-local metres.
    """

    def __init__(self, rig, name, length):
        self.rig, self.name, self.length = rig, name, length

    def __enter__(self):
        rig = self.rig
        if rig.animation_data is None:
            rig.animation_data_create()
        act = bpy.data.actions.new(self.name)
        act.use_fake_user = True
        rig.animation_data.action = act
        self.action = act
        for pb in rig.pose.bones:
            pb.location = (0, 0, 0)
            pb.rotation_euler = (0, 0, 0)
            pb.scale = (1, 1, 1)
        return self

    def rot(self, bone, frame, deg):
        pb = self.rig.pose.bones[bone]
        pb.rotation_euler = [math.radians(d) for d in deg]
        pb.keyframe_insert("rotation_euler", frame=frame)

    def loc(self, bone, frame, xyz):
        pb = self.rig.pose.bones[bone]
        pb.location = xyz
        pb.keyframe_insert("location", frame=frame)

    def scl(self, bone, frame, xyz):
        pb = self.rig.pose.bones[bone]
        pb.scale = xyz if hasattr(xyz, "__len__") else (xyz, xyz, xyz)
        pb.keyframe_insert("scale", frame=frame)

    def __exit__(self, *a):
        act = self.action
        act.frame_range = (0, self.length)
        act.use_frame_range = True
        # Keep a full key set on every bone at frame 0 and end so takes never inherit stray poses.
        for pb in self.rig.pose.bones:
            for f in (0, self.length):
                for path in ("location", "rotation_euler", "scale"):
                    fc = _fcurve(act, pb.name, path)
                    if not fc:
                        pb.keyframe_insert(path, frame=f)
        self.rig.animation_data.action = None
        return False


def _fcurve(act, bone, path):
    dp = f'pose.bones["{bone}"].{path}'
    try:
        for fc in act.fcurves:
            if fc.data_path == dp:
                return fc
    except AttributeError:  # Blender 5 layered actions
        for layer in act.layers:
            for strip in layer.strips:
                for bag in strip.channelbags:
                    for fc in bag.fcurves:
                        if fc.data_path == dp:
                            return fc
    return None


# ---------------------------------------------------------------- output

def export_fbx(rel_path, objects=None, animated=False, path_mode="STRIP"):
    """rel_path is relative to Assets/_Game/Art (e.g. 'Characters/warrior/warrior.fbx').
    path_mode="RELATIVE" keeps texture references relative to the FBX (textured heroes)."""
    path = os.path.join(ASSETS, rel_path)
    os.makedirs(os.path.dirname(path), exist_ok=True)
    bpy.ops.object.select_all(action="DESELECT")
    objs = objects or [o for o in bpy.context.scene.objects if o.type in ("MESH", "ARMATURE", "EMPTY")]
    for o in objs:
        o.select_set(True)
    kw = dict(
        filepath=path,
        use_selection=True,
        object_types={"MESH", "ARMATURE", "EMPTY"},
        apply_unit_scale=True,
        apply_scale_options="FBX_SCALE_ALL",
        axis_forward="-Z",
        axis_up="Y",
        use_mesh_modifiers=True,
        mesh_smooth_type="FACE",
        colors_type="SRGB",
        prioritize_active_color=True,
        add_leaf_bones=False,
        primary_bone_axis="Y",
        secondary_bone_axis="X",
        use_armature_deform_only=True,
        bake_space_transform=not animated,
        bake_anim=animated,
        bake_anim_use_all_bones=True,
        bake_anim_use_nla_strips=False,
        bake_anim_use_all_actions=animated,
        bake_anim_force_startend_keying=True,
        bake_anim_simplify_factor=0.0,
        use_custom_props=False,
        path_mode=path_mode,
    )
    bpy.ops.export_scene.fbx(**kw)
    return path


def save_blend(name):
    os.makedirs(BLEND_DIR, exist_ok=True)
    bpy.ops.wm.save_as_mainfile(filepath=os.path.join(BLEND_DIR, name + ".blend"), compress=True)


def render_preview(name, objects=None, angle=(65, 0, 35), size=640, frame=None, action=None, dist=None,
                   color_type="VERTEX"):
    """Workbench render (vertex colours, cavity, outline) to Blender/preview/<name>.png for visual QA.
    color_type="TEXTURE" shows image textures instead (textured heroes)."""
    sc = bpy.context.scene
    os.makedirs(PREVIEW_DIR, exist_ok=True)
    objs = objects or [o for o in sc.objects if o.type == "MESH" and not o.hide_render]
    rig = sc.objects.get("Rig")
    if rig and action:
        rig.animation_data_create()
        rig.animation_data.action = bpy.data.actions[action]
        sc.frame_set(frame or 0)
    lo = Vector((1e9, 1e9, 1e9))
    hi = Vector((-1e9, -1e9, -1e9))
    dg = bpy.context.evaluated_depsgraph_get()
    for o in objs:
        oe = o.evaluated_get(dg)
        for c in oe.bound_box:
            w = oe.matrix_world @ Vector(c)
            lo = Vector(map(min, lo, w))
            hi = Vector(map(max, hi, w))
    center = (lo + hi) / 2
    radius = max((hi - lo).length / 2, 0.1)
    cam_data = bpy.data.cameras.new("PreviewCam")
    cam_data.lens = 50
    cam = bpy.data.objects.new("PreviewCam", cam_data)
    sc.collection.objects.link(cam)
    rx, ry, rz = [math.radians(a) for a in angle]
    d = dist or radius * 3.2
    direction = Euler((rx, ry, rz)).to_matrix() @ Vector((0, 0, 1))
    cam.location = center + direction * d
    cam.rotation_euler = Euler((rx, ry, rz))
    sc.camera = cam
    sc.render.engine = "BLENDER_WORKBENCH"
    sh = sc.display.shading
    sh.light = "STUDIO"
    sh.color_type = color_type
    sh.show_cavity = True
    sh.show_object_outline = True
    sh.show_shadows = True
    sc.render.resolution_x = size
    sc.render.resolution_y = size
    sc.render.film_transparent = False
    sc.world = sc.world or bpy.data.worlds.new("W")
    sc.render.filepath = os.path.join(PREVIEW_DIR, name + ".png")
    bpy.ops.render.render(write_still=True)
    bpy.data.objects.remove(cam)
    if rig and action:
        rig.animation_data.action = None
    return sc.render.filepath
