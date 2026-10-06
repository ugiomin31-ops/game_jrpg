"""Anime-proportioned (about 6.3 heads) hero body for 심연의 미궁.

Replaces the chibi part-assembly look with one continuous, smoothly skinned body:
limbs and torso are swept tubes with authored cross-sections, fused by voxel remesh
and relaxed so armpits, hips and knees blend organically, then reduced to a game budget.
Weights come from Blender's automatic (heat) weights, so the mesh bends instead of
rotating as rigid pieces. Clothing is painted onto the body (fitted garments) or built
as shells cut from the body itself, which inherits the body's weights.

The skeleton, bone names and animation contract are the chibi Humanoid's (see
lib_humanoid/humanoid.py and Blender/README.md), only with adult proportions.
"""
import math
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path[:0] = [os.path.join(HERE, "..", "lib"), os.path.join(HERE, "..", "lib_humanoid")]

import abyss_bpy as A  # noqa: E402
import bmesh  # noqa: E402
import bpy  # noqa: E402
from humanoid import Humanoid, V, mix, rgb, shade, sweep  # noqa: E402

# Proportions: hip height 0.78 m, head radius 0.13 m -> ~1.53 m to the crown, ~5.9 heads.
ANIME = dict(
    head_r=0.130, head_sx=0.93, leg=0.78, torso=0.41, neck=0.075, shoulder_w=0.150, hip_w=0.060,
    upper_arm=0.265, forearm=0.235, hand=0.165, ankle=0.072, foot_len=0.17, arm_angle=9.0,
)

SKIN = "#ffe6d6"


class AnimeHumanoid(Humanoid):
    """Humanoid with adult layout; parts registered with bone=None keep their own vertex groups."""

    def __init__(self, name, **params):
        merged = dict(ANIME)
        merged.update(params)
        super().__init__(name, **merged)
        self.weighted = []  # objects that already carry vertex groups (body, cloth shells)

    def add_weighted(self, obj):
        self.weighted.append(obj)
        return obj

    def skin(self):
        """Rigid/blended parts get groups like the chibi pipeline; weighted parts keep theirs."""
        weighted = list(self.weighted)
        keep = set(weighted)
        self.parts = [(o, b) for o, b in self.parts if o not in keep]
        if not self.parts:
            body = A.join(sorted(weighted, key=lambda o: -len(o.data.uv_layers)), "Body")
        else:
            super().skin()
            # A textured body goes first: join keeps the active object's UV maps.
            objs = sorted([self.body] + weighted, key=lambda o: -len(o.data.uv_layers))
            body = A.join(objs, "Body")
        if body.data.uv_layers:
            uv = body.data.uv_layers[0]
            body.data.uv_layers.active = uv
            uv.active_render = True
        body.modifiers.clear()
        md = body.modifiers.new("Armature", "ARMATURE")
        md.object = self.rig
        body.parent = self.rig
        self.body = body
        return body


# =============================================================== body sculpt

def _limb(name, pts, radii, seg=18):
    return sweep(name, pts, radii, SKIN, seg=seg, caps=True)


def _lerp_pts(a, b, ts, bend=V((0, 0, 0))):
    return [a.lerp(b, t) + bend * math.sin(math.pi * t) for t in ts]


def body_tubes(H, female=False, muscle=1.0):
    """Swept tubes for torso, neck, arms, hands and legs (world space, faces -Y)."""
    j, P = H.j, H.P
    hz = j["hip"].z
    nz = j["neck"].z
    T = nz - hz
    chest = 1.06 if female else 1.0
    waist = 0.86 if female else 0.94
    hipw = 1.08 if female else 1.0
    m = muscle
    # Torso: (z, half-width, half-depth, y-offset). Front is -Y.
    prof = [
        (hz - 0.075, 0.040 * hipw, 0.045, 0.000),
        (hz - 0.045, 0.100 * hipw, 0.078, 0.004),
        (hz + 0.015, 0.122 * hipw, 0.086, 0.006),
        (hz + 0.09 * T / 0.42, 0.112 * waist, 0.076, 0.000),
        (hz + 0.18 * T / 0.42, 0.102 * waist * m, 0.072, -0.002),
        (hz + 0.26 * T / 0.42, 0.116 * m, 0.082 * chest, -0.008),
        (hz + 0.32 * T / 0.42, 0.126 * m, 0.086 * chest, -0.008),
        (hz + 0.375 * T / 0.42, 0.124 * m, 0.072, 0.002),
        (nz - 0.012, 0.075, 0.056, 0.006),
        (nz + 0.010, 0.042, 0.042, 0.008),
    ]
    pts = [V((0, y, z)) for z, _, _, y in prof]
    torso = sweep("torso", pts, [(w, d) for _, w, d, _ in prof], SKIN, seg=28, up=(0, -1, 0))
    parts = [torso]
    if female:
        for s in (1, -1):
            c = V((s * 0.062, -0.072, hz + 0.31 * T / 0.42))
            parts.append(A.sphere("bust", r=1, loc=c, scale=(0.062, 0.058, 0.056), color=SKIN, seg=20, rings=12))
    parts.append(_limb("neck", [j["neck"] + V((0, 0.010, -0.03)), j["head"] + V((0, 0.012, 0.045))],
                       [(0.040, 0.044), (0.036, 0.040)], seg=16))
    for S, s in (("L", 1), ("R", -1)):
        sh, el, wr = j["shoulder." + S], j["elbow." + S], j["wrist." + S]
        # Deltoid cap blending the arm into the shoulder line.
        # Shoulder slope: a tapered tube from the neck base out over the joint, then the arm.
        parts.append(_limb("trapezius", [V((s * 0.03, 0.008, j["neck"].z - 0.01)), sh + V((-s * 0.01, 0.004, 0.012)),
                                         sh + V((s * 0.012, 0.004, -0.02))], [(0.040, 0.038), (0.044, 0.046), (0.040, 0.044)]))
        up_pts = _lerp_pts(sh + V((0, 0.004, -0.005)), el, (0, 0.25, 0.55, 0.85, 1.0))
        parts.append(_limb("upper_arm", up_pts, [0.043 * m, 0.041 * m, 0.037 * m, 0.032, 0.029]))
        fo_pts = _lerp_pts(el, wr, (0, 0.2, 0.45, 0.8, 1.0))
        parts.append(_limb("forearm", fo_pts, [0.029, 0.034 * m, 0.031, 0.026, 0.024]))
        parts.extend(hand(H, S))
        hp, kn, an = j["hipj." + S], j["knee." + S], j["ankle." + S]
        th_pts = _lerp_pts(hp + V((s * 0.004, 0.004, 0.02)), kn, (0, 0.2, 0.5, 0.8, 1.0))
        parts.append(_limb("thigh", th_pts, [(0.064, 0.072), (0.064, 0.070), (0.058, 0.062),
                                             (0.047, 0.050), (0.041, 0.044)]))
        sh_pts = _lerp_pts(kn, an, (0, 0.12, 0.35, 0.7, 1.0), bend=V((0, 0.010, 0)))
        parts.append(_limb("shin", sh_pts, [(0.041, 0.044), (0.043, 0.047), (0.044, 0.050),
                                            (0.032, 0.035), (0.026, 0.028)]))
        toe = j["toe." + S]
        foot = [an + V((0, 0.03, -0.02)), an + V((0, -0.02, -0.045)), toe + V((0, 0.0, 0.025))]
        parts.append(_limb("foot", foot, [(0.028, 0.030), (0.035, 0.030), (0.030, 0.019)], seg=14))
    return parts


def hand(H, S):
    """Relaxed anime hand hanging at the side: palm faces the thigh, fingers loosely curled toward it."""
    from mathutils import Matrix
    j = H.j
    s = H.side(S)
    wr, tip = j["wrist." + S], j["hand_tip." + S]
    d = (tip - wr).normalized()
    across = V((0, -1, 0)) - V((0, -1, 0)).dot(d) * d  # knuckle line runs front (-Y) to back
    across.normalize()
    inward = d.cross(across)
    if inward.x * s > 0:
        inward = -inward  # palm side points toward the body
    L = (tip - wr).length
    out = [A.sphere("wrist", r=0.026, loc=wr + d * 0.006, color=SKIN, seg=12, rings=8)]
    palm_c = wr + d * L * 0.27
    palm = A.sphere("palm", r=1, loc=(0, 0, 0), color=SKIN, seg=14, rings=10)
    palm.data.transform(Matrix((inward, across, d)).transposed().to_4x4() @ Matrix.Diagonal((0.017, 0.032, 0.040, 1.0)))
    palm.location = palm_c
    out.append(palm)
    for k, off in enumerate((-0.022, -0.0075, 0.0075, 0.021)):
        base = wr + d * L * 0.48 + across * off
        ln = (0.30, 0.34, 0.33, 0.26)[k] * L
        pts = [base, base + d * ln * 0.75 + inward * 0.004, base + d * ln + inward * 0.020,
               base + d * ln * 0.75 + inward * 0.032]
        out.append(sweep("finger", pts, [0.0085, 0.0080, 0.0074, 0.0064], SKIN, seg=8))
    tb = wr + d * L * 0.14 - across * 0.022 + inward * 0.010
    out.append(sweep("thumb", [tb, tb + d * L * 0.20 - across * 0.012 + inward * 0.016,
                               tb + d * L * 0.34 - across * 0.008 + inward * 0.026], [0.012, 0.010, 0.0085], SKIN, seg=8))
    return out


def fuse(parts, name="body", voxel=0.0045, smooth=14, target_tris=12000):
    """Union overlapping parts into one clean, relaxed surface at a game polygon budget."""
    o = A.join(parts, name)
    md = o.modifiers.new("remesh", "REMESH")
    md.mode = "VOXEL"
    md.voxel_size = voxel
    md.adaptivity = 0.0
    md.use_smooth_shade = True
    A.apply_modifiers(o)
    sm = o.modifiers.new("relax", "CORRECTIVE_SMOOTH")
    sm.factor = 0.5
    sm.iterations = smooth
    sm.smooth_type = "LENGTH_WEIGHTED"
    sm.use_only_smooth = True
    A.apply_modifiers(o)
    tris = sum(len(p.vertices) - 2 for p in o.data.polygons)
    if tris > target_tris:
        dec = o.modifiers.new("budget", "DECIMATE")
        dec.ratio = target_tris / tris
        dec.use_collapse_triangulate = False
        A.apply_modifiers(o)
    for p in o.data.polygons:
        p.use_smooth = True
    A.paint(o, SKIN)
    return o


def auto_weights(H, obj):
    """Heat-diffusion weights from the rig (deform bones only; weapon sockets carry no skin)."""
    rig = H.rig
    for b in rig.data.bones:
        b.use_deform = not b.name.startswith("weapon.") and b.name != "root"
    bpy.ops.object.select_all(action="DESELECT")
    obj.select_set(True)
    rig.select_set(True)
    bpy.context.view_layer.objects.active = rig
    bpy.ops.object.parent_set(type="ARMATURE_AUTO")
    obj.modifiers.clear()
    obj.parent = None
    obj.matrix_parent_inverse.identity()
    for b in rig.data.bones:
        b.use_deform = True
    return obj


# =============================================================== painting helpers

def paint_faces(o, fn):
    """fn(world face centre, normal) -> colour or None per face: hard colour borders (trims, bands)."""
    me = o.data
    attr = me.color_attributes["Col"]
    for p in me.polygons:
        c = fn(o.matrix_world @ p.center, p.normal)
        if c is None:
            continue
        c = rgb(c)
        for li in p.loop_indices:
            attr.data[li].color_srgb = c
    return o


def paint_regions(o, fn):
    """fn(world co, normal) -> colour or None per vertex (fitted clothing, gradients)."""
    me = o.data
    attr = me.color_attributes["Col"]
    cache = {}
    for v in me.vertices:
        c = fn(o.matrix_world @ v.co, v.normal)
        if c is not None:
            cache[v.index] = rgb(c)
    for loop in me.loops:
        c = cache.get(loop.vertex_index)
        if c is not None:
            attr.data[loop.index].color_srgb = c
    return o


def cloth_shell(name, body, keep, color, offset=0.006, thick=0.008, bisect=()):
    """Garment cut from the weighted body: copy, cut along planes, keep a region, push out, thicken.
    keep(co) -> bool on world positions; bisect: [(point, normal)] planes to cut cleanly first."""
    o = body.copy()  # object copy keeps the vertex-group names the weights refer to
    o.data = me = body.data.copy()
    o.name = name
    o.modifiers.clear()
    bpy.context.scene.collection.objects.link(o)
    bm = bmesh.new()
    bm.from_mesh(me)
    for co, no in bisect:
        geom = bm.verts[:] + bm.edges[:] + bm.faces[:]
        bmesh.ops.bisect_plane(bm, geom=geom, plane_co=V(co), plane_no=V(no))
    if keep.__code__.co_argcount - len(keep.__defaults__ or ()) >= 2:
        dom = dominant_bones(body)
        drop = [v for v in bm.verts if not keep(v.co, dom.get(v.index))] if not bisect else None
        if drop is None:
            # Bisecting adds vertices; take their bone from the nearest original vertex.
            from mathutils.kdtree import KDTree
            kd = KDTree(len(body.data.vertices))
            for v in body.data.vertices:
                kd.insert(v.co, v.index)
            kd.balance()
            drop = [v for v in bm.verts if not keep(v.co, dom.get(kd.find(v.co)[1]))]
    else:
        drop = [v for v in bm.verts if not keep(v.co)]
    bmesh.ops.delete(bm, geom=drop, context="VERTS")
    bm.normal_update()
    for v in bm.verts:
        v.co += v.normal * offset
    bm.to_mesh(me)
    bm.free()
    A.paint(o, color)
    if thick > 0:
        md = o.modifiers.new("thick", "SOLIDIFY")
        md.thickness = thick
        md.offset = 1.0
        md.use_even_offset = True
        md.use_rim = True
        A.apply_modifiers(o)
    for p in o.data.polygons:
        p.use_smooth = True
    return o


# =============================================================== weights as region masks

def dominant_bones(o):
    """Vertex index -> name of its heaviest deform group."""
    names = {g.index: g.name for g in o.vertex_groups}
    out = {}
    for v in o.data.vertices:
        best, w = None, 0.0
        for g in v.groups:
            if g.weight > w:
                best, w = names.get(g.group), g.weight
        out[v.index] = best
    return out


def paint_by_bone(o, fn):
    """fn(bone, world co) -> colour or None, using each vertex's dominant bone."""
    dom = dominant_bones(o)
    me = o.data
    attr = me.color_attributes["Col"]
    for loop in me.loops:
        vi = loop.vertex_index
        c = fn(dom[vi], o.matrix_world @ me.vertices[vi].co)
        if c is not None:
            attr.data[loop.index].color_srgb = rgb(c)
    return o


def bone_side(bone):
    return None if bone is None else bone.split(".")[0]


# =============================================================== garments that follow the body

def conform(o, body, offset=0.008, keep_outside=False):
    """Snaps a garment onto the body surface + offset (keep_outside: only vertices inside the body move, so a
    shape that already clears the body keeps its own silhouette)."""
    md = o.modifiers.new("conform", "SHRINKWRAP")
    md.target = body
    md.wrap_method = "NEAREST_SURFACEPOINT"
    md.wrap_mode = "OUTSIDE" if keep_outside else "OUTSIDE_SURFACE"
    md.offset = offset
    A.apply_modifiers(o)
    return o


def transfer_weights(o, body):
    """Copies the body's skin weights onto a garment (nearest face, interpolated) so it bends with the body."""
    for g in body.vertex_groups:
        if g.name not in o.vertex_groups:
            o.vertex_groups.new(name=g.name)
    md = o.modifiers.new("weights", "DATA_TRANSFER")
    md.object = body
    md.use_vert_data = True
    md.data_types_verts = {"VGROUP_WEIGHTS"}
    md.vert_mapping = "POLYINTERP_NEAREST"
    md.layers_vgroup_select_src = "ALL"
    md.layers_vgroup_select_dst = "NAME"
    A.apply_modifiers(o)
    return o


def fitted(H, o, body, offset=0.008):
    """Conform + inherit weights, registered as an already-weighted part."""
    conform(o, body, offset)
    transfer_weights(o, body)
    for p in o.data.polygons:
        p.use_smooth = True
    return H.add_weighted(o)


def relax(o, iterations=8, factor=1.0):
    """Smooths a garment shell (drops body detail such as toes, collarbones, nipples)."""
    md = o.modifiers.new("relax", "LAPLACIANSMOOTH")  # open edges stay put (a plain smooth shrinks them)
    md.lambda_factor = 0.8 * factor
    md.lambda_border = 0.0
    md.iterations = iterations
    A.apply_modifiers(o)
    return o


def drop_faces(o, fn):
    """Deletes faces whose centre satisfies fn(world co) (skin hidden under boots or armour)."""
    bm = bmesh.new()
    bm.from_mesh(o.data)
    bmesh.ops.delete(bm, geom=[f for f in bm.faces if fn(o.matrix_world @ f.calc_center_median())], context="FACES")
    bmesh.ops.delete(bm, geom=[v for v in bm.verts if not v.link_faces], context="VERTS")
    bm.to_mesh(o.data)
    bm.free()
    return o


def section(o, z, band=0.012, exclude=("upper_arm", "forearm", "hand")):
    """Half width (x) and half depth (y) of the torso/hips at height z, arms excluded."""
    dom = dominant_bones(o)
    xs, ys = [0.0], [0.0]
    for v in o.data.vertices:
        co = o.matrix_world @ v.co
        if abs(co.z - z) < band and bone_side(dom[v.index]) not in exclude:
            xs.append(abs(co.x))
            ys.append(abs(co.y))
    return max(xs), max(ys)


def boot(H, body, S, top, color, cuff_color=None, cuff=0.045):
    """A boot as one clean shape: a shaft up the shin fused with a foot (heel to a rounded toe), remeshed,
    then pushed outside the leg and given the leg's weights."""
    j = H.j
    kn, an, toe = j["knee." + S], j["ankle." + S], j["toe." + S]
    sx = 1 if S == "L" else -1
    shin = (kn - an).normalized()
    t_top = (top - an.z) / (kn.z - an.z)
    pts = [an + (kn - an) * t for t in (-0.05, 0.25, 0.55, t_top)]
    shaft = sweep("boot_shaft", pts, [0.050, 0.046, 0.054, 0.060], color, seg=20)
    fwd = V((toe.x - an.x, toe.y - an.y, 0)).normalized()
    heel = V((an.x, an.y, 0.035)) - fwd * 0.045
    tip = V((toe.x, toe.y, 0.026)) + fwd * 0.040
    foot = sweep("boot_foot", [heel, heel.lerp(tip, 0.35) + V((0, 0, 0.012)), heel.lerp(tip, 0.75), tip],
                 [(0.040, 0.036), (0.046, 0.042), (0.048, 0.030), (0.020, 0.018)], color, seg=16,
                 up=V((0, 0, 1)))
    b = fuse([shaft, foot], name="boot", voxel=0.004, smooth=6, target_tris=1800)
    for v in b.data.vertices:
        if v.co.z < 0.0:
            v.co.z = 0.0
    # Cut the open top.
    bm = bmesh.new()
    bm.from_mesh(b.data)
    bmesh.ops.bisect_plane(bm, geom=bm.verts[:] + bm.edges[:] + bm.faces[:], plane_co=V((0, 0, top)),
                           plane_no=V((0, 0, 1)), clear_outer=True)
    bm.to_mesh(b.data)
    bm.free()
    A.paint(b, color)
    from humanoid import zgrad
    zgrad(b, 0.0, shade(color, 0.55), 0.03, color)
    conform(b, body, 0.006)
    transfer_weights(b, body)
    for p in b.data.polygons:
        p.use_smooth = True
    H.add_weighted(b)
    if cuff_color:
        # A painted turn-down band: a separate cuff shell spikes where the open top is thin.
        paint_faces(b, lambda co, n: cuff_color if co.z > top - cuff else None)
    return [b]
