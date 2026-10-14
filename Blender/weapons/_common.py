"""Shared builders for the weapon generators (Blender/weapons/*.py).

Conventions (Blender/README.md §6): origin = grip point, weapon extends along +Z,
sharp edge / front faces -Y. One joined mesh object per weapon named after its id.
"""
import math
import os
import sys

import bmesh
import bpy
from mathutils import Euler, Matrix, Vector

sys.path.append(os.path.join(os.path.dirname(os.path.abspath(__file__)), '../lib'))
import abyss_bpy as A  # noqa: E402

# ------------------------------------------------------------------ palette
GOLD = "#e8b43a"
GOLD_HI = "#ffd866"
GOLD_DK = "#a8741c"
SILVER = "#d6dde6"
STEEL = "#a9b4c2"
STEEL_DK = "#6c7684"
IRON = "#7d858f"
IRON_DK = "#4a4f57"
BRONZE = "#c9853f"
BRONZE_HI = "#e8b070"
LEATHER = "#7a4a2a"
LEATHER_DK = "#4f2e1a"
WOOD = "#9a6436"
WOOD_DK = "#6b4022"
WOOD_LT = "#c08850"
WHITE = "#f4efe4"


# ------------------------------------------------------------------ low-level mesh helpers

def _finish_bm(name, bm, color, mat, smooth_angle=None, flat=False):
    bmesh.ops.remove_doubles(bm, verts=bm.verts, dist=1e-6)
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    o = A._from_bmesh(name, bm)
    if flat:
        for p in o.data.polygons:
            p.use_smooth = False
    elif smooth_angle is not None:
        A.shade_smooth(o, angle=smooth_angle)
    else:
        A.shade_smooth(o)
    return A.paint(o, color, mat)


def loft(name, sections, color="#888888", mat="M_Toon", closed=True, cap_start=True, cap_end=True,
         smooth_angle=35, flat=False):
    """Skin consecutive point rings (each a list of 3D points, equal count).
    A section with a single point becomes an apex (cone fan)."""
    bm = bmesh.new()
    rings = [[bm.verts.new(p) for p in s] for s in sections]
    for a, b in zip(rings, rings[1:]):
        if len(a) == 1 and len(b) == 1:
            continue
        if len(a) == 1:
            n = len(b)
            for i in range(n if closed else n - 1):
                bm.faces.new((a[0], b[i], b[(i + 1) % n]))
            continue
        if len(b) == 1:
            n = len(a)
            for i in range(n if closed else n - 1):
                bm.faces.new((a[i], a[(i + 1) % n], b[0]))
            continue
        n = len(a)
        for i in range(n if closed else n - 1):
            j = (i + 1) % n
            bm.faces.new((a[i], a[j], b[j], b[i]))
    if closed:
        if cap_start and len(rings[0]) > 2:
            bm.faces.new(list(reversed(rings[0])))
        if cap_end and len(rings[-1]) > 2:
            bm.faces.new(rings[-1])
    return _finish_bm(name, bm, color, mat, smooth_angle=smooth_angle, flat=flat)


def blade(name, profile, color=STEEL, mat="M_Toon", edge_frac=0.5, smooth_angle=20):
    """Double-edged blade with bevelled-edge hexagonal cross-section.
    profile: list of (z, half_width, half_thickness[, y_offset]); width runs along Y (edges face -Y/+Y),
    thickness along X. half_width 0 at the end makes a point."""
    secs = []
    for row in profile:
        z, hw, t = row[0], row[1], row[2]
        yo = row[3] if len(row) > 3 else 0.0
        if hw <= 1e-5:
            secs.append([(0.0, yo, z)])
            continue
        e = hw * edge_frac
        secs.append([(0.0, yo - hw, z), (t, yo - e, z), (t, yo + e, z),
                     (0.0, yo + hw, z), (-t, yo + e, z), (-t, yo - e, z)])
    return loft(name, secs, color=color, mat=mat, smooth_angle=smooth_angle)


def flat_plate(name, pts_yz, thickness, x=0.0, color="#888888", mat="M_Toon", bevel=0.0):
    """Polygon given in the (y, z) plane, extruded along X (centred on x). For inlays on blade flats,
    guards, wings seen from the side."""
    # extrude_shape builds in XZ extruded along Y; rotate 90deg about Z: x->y, y->-x
    o = A.extrude_shape(name, [(y, z) for (y, z) in pts_yz], depth=thickness, color=color, mat=mat, bevel=bevel)
    o.rotation_euler = Euler((0, 0, math.radians(90)))
    o.location = (x, 0, 0)
    A.apply_transform(o)
    return o


def flat_plate_xz(name, pts_xz, thickness, y=0.0, color="#888888", mat="M_Toon", bevel=0.0):
    """Polygon in the (x, z) plane extruded along Y (front-facing shapes)."""
    o = A.extrude_shape(name, pts_xz, depth=thickness, color=color, mat=mat, bevel=bevel)
    o.location = (0, y, 0)
    A.apply_transform(o)
    return o


def gem(name, r=0.03, h=None, loc=(0, 0, 0), rot=(0, 0, 0), scale=(1, 1, 1), color="#3aa0ff", mat="M_Emit", seg=8):
    """Faceted brilliant-cut gem; table faces +Z before rotation."""
    h = h or r * 1.2
    prof = [(0.0, -h * 0.75), (r * 0.55, -h * 0.35), (r, 0.0), (r * 0.82, h * 0.18), (r * 0.5, h * 0.3), (0.0, h * 0.3)]
    o = A.lathe(name, prof, loc=loc, rot=rot, scale=scale, color=color, mat=mat, seg=seg)
    for p in o.data.polygons:
        p.use_smooth = False
    return o


def crystal(name, r=0.04, h=0.16, loc=(0, 0, 0), rot=(0, 0, 0), scale=(1, 1, 1), color="#8fd8ff", mat="M_Emit", seg=6, base=0.25):
    """Elongated hexagonal crystal spike (bipyramid, longer on top)."""
    prof = [(0.0, -h * base), (r, 0.0), (r * 0.92, h * 0.55), (0.0, h)]
    o = A.lathe(name, prof, loc=loc, rot=rot, scale=scale, color=color, mat=mat, seg=seg)
    for p in o.data.polygons:
        p.use_smooth = False
    return o


def star(name, r_out=0.06, r_in=0.028, depth=0.02, points=5, loc=(0, 0, 0), rot=(0, 0, 0), color=GOLD, mat="M_Toon"):
    """Puffy star (front face -Y) with a raised centre for a bevelled look."""
    bm = bmesh.new()
    n = points * 2
    front, back = [], []
    for i in range(n):
        a = math.pi / 2 + i * math.pi / points
        rr = r_out if i % 2 == 0 else r_in
        front.append(bm.verts.new((math.cos(a) * rr, -depth * 0.25, math.sin(a) * rr)))
        back.append(bm.verts.new((math.cos(a) * rr, depth * 0.25, math.sin(a) * rr)))
    cf = bm.verts.new((0, -depth * 0.5 - r_in * 0.4, 0))
    cb = bm.verts.new((0, depth * 0.5 + r_in * 0.4, 0))
    for i in range(n):
        j = (i + 1) % n
        bm.faces.new((front[j], front[i], cf))
        bm.faces.new((back[i], back[j], cb))
        bm.faces.new((front[i], front[j], back[j], back[i]))
    o = _finish_bm(name, bm, color, mat, flat=True)
    A._place(o, loc, rot, 1)
    return o


def ring_pts(r, z, n=16, rx=None, ry=None, cx=0.0, cy=0.0, phase=0.0):
    rx = r if rx is None else rx
    ry = r if ry is None else ry
    return [(cx + math.cos(phase + 2 * math.pi * i / n) * rx, cy + math.sin(phase + 2 * math.pi * i / n) * ry, z)
            for i in range(n)]


def shaft(name, profile, color=WOOD, mat="M_Toon", seg=16, wobble=None, smooth_angle=None):
    """Lathe-like shaft from (r, z) rows with optional wobble(z)->(dx, dy) for gnarled wood."""
    secs = []
    for (r, z) in profile:
        dx, dy = wobble(z) if wobble else (0.0, 0.0)
        if r <= 1e-5:
            secs.append([(dx, dy, z)])
        else:
            secs.append(ring_pts(r, z, seg, cx=dx, cy=dy))
    o = loft(name, secs, color=color, mat=mat, smooth_angle=smooth_angle)
    if smooth_angle is None:
        for p in o.data.polygons:
            p.use_smooth = True
    return o


def wrap_grip(name, z0, z1, r, turns=6, color=LEATHER, band=LEATHER_DK, seg=12):
    """Leather-wrapped grip: core cylinder + spiral wrap ridge."""
    core = A.cyl(name + "_core", r=r, depth=z1 - z0, loc=(0, 0, (z0 + z1) / 2), color=color, seg=seg)
    pts = []
    steps = turns * 14
    for i in range(steps + 1):
        t = i / steps
        a = t * turns * 2 * math.pi
        pts.append((math.cos(a) * r, math.sin(a) * r, z0 + (z1 - z0) * t))
    wrap = A.tube(name + "_wrap", pts, radius=r * 0.22, color=band, seg=6)
    return [core, wrap]


def helix(name, z0, z1, r, turns, radius=0.004, color=GOLD, mat="M_Toon", phase=0.0, steps_per_turn=16, r_fn=None):
    pts = []
    steps = max(4, int(turns * steps_per_turn))
    for i in range(steps + 1):
        t = i / steps
        a = phase + t * turns * 2 * math.pi
        z = z0 + (z1 - z0) * t
        rr = r_fn(z) if r_fn else r
        pts.append((math.cos(a) * rr, math.sin(a) * rr, z))
    return A.tube(name, pts, radius=radius, color=color, mat=mat, seg=6)


def band(name, z, r, h=0.015, color=GOLD, seg=20, bevel=True):
    """Metal collar ring around a shaft."""
    prof = [(r * 0.96, z - h / 2), (r, z - h * 0.35), (r, z + h * 0.35), (r * 0.96, z + h / 2)]
    o = A.lathe(name, [(0.0, z - h / 2)] + prof + [(0.0, z + h / 2)], color=color, seg=seg)
    return o


def curve_pts(ctrl, n=24):
    """Catmull-Rom through control points -> smooth polyline."""
    P = [Vector(c) for c in ctrl]
    P = [P[0] + (P[0] - P[1])] + P + [P[-1] + (P[-1] - P[-2])]
    out = []
    segs = len(P) - 3
    per = max(2, n // segs)
    for s in range(segs):
        p0, p1, p2, p3 = P[s], P[s + 1], P[s + 2], P[s + 3]
        for k in range(per):
            t = k / per
            t2, t3 = t * t, t * t * t
            out.append(0.5 * ((2 * p1) + (-p0 + p2) * t + (2 * p0 - 5 * p1 + 4 * p2 - p3) * t2 + (-p0 + 3 * p1 - 3 * p2 + p3) * t3))
    out.append(P[-2])
    return [tuple(v) for v in out]


def sweep(name, path, width_fn, thick_fn, color="#888888", mat="M_Toon", up=(1, 0, 0), smooth_angle=40, n_side=6):
    """Sweep a flattened hexagon along a 3D path. width along the path's in-plane normal, thickness along `up`.
    width_fn/thick_fn take t in [0,1]. For bow limbs, curved blades, wings."""
    up = Vector(up).normalized()
    P = [Vector(p) for p in path]
    secs = []
    for i, p in enumerate(P):
        t = i / (len(P) - 1)
        tan = (P[min(i + 1, len(P) - 1)] - P[max(i - 1, 0)]).normalized()
        nrm = tan.cross(up).normalized()
        u = nrm.cross(tan).normalized()
        w, th = width_fn(t), thick_fn(t)
        if w <= 1e-5:
            secs.append([tuple(p)])
            continue
        secs.append([tuple(p + nrm * w), tuple(p + nrm * w * 0.5 + u * th), tuple(p - nrm * w * 0.5 + u * th),
                     tuple(p - nrm * w), tuple(p - nrm * w * 0.5 - u * th), tuple(p + nrm * w * 0.5 - u * th)])
    return loft(name, secs, color=color, mat=mat, smooth_angle=smooth_angle)


def rays(name, n, r0, r1, width, depth, arc=(0, 360), z=0.0, y=0.0, color=GOLD, mat="M_Toon", alt=None):
    """Radiant sun rays in the XZ plane (front -Y), centred at (0, y, z). alt = (r1_short) for alternating."""
    objs = []
    a0, a1 = arc
    full = abs(a1 - a0) >= 359.9
    for i in range(n):
        f = i / n if full else (i / (n - 1) if n > 1 else 0.5)
        a = math.radians(a0 + (a1 - a0) * f)
        rr1 = alt if (alt and i % 2 == 1) else r1
        c, s = math.cos(a), math.sin(a)
        px, pz = -s, c
        pts = [(c * r0 + px * width, s * r0 + pz * width), (c * rr1, s * rr1), (c * r0 - px * width, s * r0 - pz * width)]
        # pts are (x, z) using a measured from +X axis
        pts = [(x, z + 0.0) for (x, z) in pts]
        o = A.extrude_shape(f"{name}{i}", pts, depth=depth, color=color, mat=mat)
        o.location = (0, y, z)
        A.apply_transform(o)
        objs.append(o)
    return objs


# ------------------------------------------------------------------ assembly / output

def finalize(objs, name):
    """Join parts into one clean mesh named `name`, origin at world origin (grip)."""
    o = A.join(objs, name)
    bpy.ops.object.select_all(action="DESELECT")
    o.select_set(True)
    bpy.context.view_layer.objects.active = o
    # merge exact duplicates only inside the object, fix normals
    bm = bmesh.new()
    bm.from_mesh(o.data)
    bmesh.ops.remove_doubles(bm, verts=bm.verts, dist=1e-6)
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    bm.to_mesh(o.data)
    bm.free()
    o.data.update()
    bad = [m.name for m in o.data.materials if m is None or m.name not in A.MATERIALS]
    assert not bad, f"{name}: illegal material slots {bad}"
    assert "Col" in o.data.color_attributes, f"{name}: missing Col"
    return o


def tri_count(o):
    return sum(len(p.vertices) - 2 for p in o.data.polygons)


def export_items(items, folder):
    """items: list of (id, obj). Exports each object alone to <folder>/<id>.fbx."""
    paths = []
    for wid, o in items:
        o.location = (0, 0, 0)
        p = A.export_fbx(f"{folder}/{wid}.fbx", objects=[o])
        assert os.path.isfile(p), p
        paths.append(p)
        print(f"[export] {wid}: {tri_count(o)} tris, slots={[m.name for m in o.data.materials]} -> {p}")
    return paths


def _only_visible(objs_visible, all_objs):
    for o in all_objs:
        hide = o not in objs_visible
        o.hide_render = hide
        o.hide_viewport = hide


def preview_items(items, prefix, angles, size=640, zoom=0.9):
    """Per-item renders; zoom < 1 frames the object tighter than the lib default."""
    all_objs = [o for _, o in items]
    for wid, o in items:
        _only_visible([o], all_objs)
        bpy.context.view_layer.update()
        dims = o.dimensions
        radius = max(dims.length / 2, 0.1)
        for tag, ang in angles.items():
            A.render_preview(f"{prefix}{wid}{tag}", objects=[o], angle=ang, size=size, dist=radius * 3.2 * zoom)
    _only_visible(all_objs, all_objs)


def contact_sheet(items, name, spacing, axis=(0, 1, 0), angle=(90, 0, 90), size=1280, dist=None):
    """Lay items side by side along `axis`, render one preview, then move them back to the origin."""
    all_objs = [o for _, o in items]
    _only_visible(all_objs, all_objs)
    n = len(items)
    for i, (_, o) in enumerate(items):
        off = (i - (n - 1) / 2) * spacing
        o.location = (axis[0] * off, axis[1] * off, axis[2] * off)
    bpy.context.view_layer.update()
    A.render_preview(name, objects=all_objs, angle=angle, size=size, dist=dist)
    for _, o in items:
        o.location = (0, 0, 0)
    bpy.context.view_layer.update()


def paint_faces(o, pred, color, mat=None):
    """Recolour faces where pred(center, normal) is true (object-local). Optionally switch material slot."""
    color = A._as_rgba(color)
    me = o.data
    attr = me.color_attributes["Col"]
    idx = None
    if mat:
        names = [x.name for x in me.materials]
        if mat not in names:
            me.materials.append(A._material(mat))
            names.append(mat)
        idx = names.index(mat)
    for p in me.polygons:
        if pred(p.center, p.normal):
            for li in p.loop_indices:
                attr.data[li].color_srgb = color
            if idx is not None:
                p.material_index = idx
    return o
