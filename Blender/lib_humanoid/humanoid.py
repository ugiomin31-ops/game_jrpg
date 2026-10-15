"""Parametric chibi humanoid builder for 심연의 미궁 heroes and NPCs.

Geometry helpers (sweep, hair locks, projected decals, wrapped bands, cloth shells), the base body
(head + anime face, torso, arms with mitten/fist hands, legs, boots), the fixed bone layout and
skinning. Animation lives in anims.py.

Coordinates are world space, character faces -Y, left (.L) is +X (see Blender/README.md).
"""
import math
import os
import sys

sys.path.append(os.path.join(os.path.dirname(os.path.abspath(__file__)), '../lib'))
import abyss_bpy as A  # noqa: E402

import bmesh  # noqa: E402
import bpy  # noqa: E402
from mathutils import Euler, Matrix, Vector  # noqa: E402
from mathutils.bvhtree import BVHTree  # noqa: E402

V = Vector
FRONT = V((0, -1, 0))


def rgb(c):
    return A._as_rgba(c)


def shade(c, k):
    """Multiply an sRGB colour by k (k<1 darker, >1 lighter, clamped)."""
    r = rgb(c)
    return tuple(min(1.0, max(0.0, r[i] * k)) for i in range(3)) + (1.0,)


def mix(a, b, t):
    a, b = rgb(a), rgb(b)
    return tuple(a[i] * (1 - t) + b[i] * t for i in range(4))


# =============================================================== mesh primitives

def _finish(o, color, mat, smooth):
    if smooth:
        for p in o.data.polygons:
            p.use_smooth = True
    return A.paint(o, color, mat)


def _bm_obj(name, bm, color, mat, smooth=True, recalc=True):
    bmesh.ops.remove_doubles(bm, verts=bm.verts, dist=1e-6)
    if recalc:
        bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    o = A._from_bmesh(name, bm)
    return _finish(o, color, mat, smooth)


def sweep(name, pts, radii, color="#888888", mat="M_Toon", seg=10, up=None, caps=True, smooth=True, phase=0.0):
    """Tube along pts with elliptical sections. radii: float or (width, thick) per point.
    width runs along B = T x N, thick along N (N starts as `up` projected off the tangent)."""
    pts = [V(p) for p in pts]
    n = len(pts)
    radii = [radii] * n if isinstance(radii, (int, float)) else radii
    rr = [(r, r) if isinstance(r, (int, float)) else tuple(r) for r in radii]
    T = []
    for i in range(n):
        a, b = pts[max(i - 1, 0)], pts[min(i + 1, n - 1)]
        T.append((b - a).normalized())
    up = V(up) if up is not None else (V((0, 0, 1)) if abs(T[0].z) < 0.9 else V((0, -1, 0)))
    N = up - up.dot(T[0]) * T[0]
    if N.length < 1e-6:
        N = V((1, 0, 0)) - V((1, 0, 0)).dot(T[0]) * T[0]
    N.normalize()
    bm = bmesh.new()
    rings = []
    for i in range(n):
        if i > 0:
            N = T[i - 1].rotation_difference(T[i]) @ N
            N = (N - N.dot(T[i]) * T[i]).normalized()
        B = T[i].cross(N)
        w, t = rr[i]
        if w < 1e-5 and t < 1e-5:
            rings.append([bm.verts.new(pts[i])])
            continue
        ring = []
        for k in range(seg):
            a = 2 * math.pi * k / seg + phase
            ring.append(bm.verts.new(pts[i] + B * (w * math.cos(a)) + N * (t * math.sin(a))))
        rings.append(ring)
    for a, b in zip(rings, rings[1:]):
        if len(a) == 1 and len(b) == 1:
            continue
        for k in range(seg):
            k2 = (k + 1) % seg
            if len(a) == 1:
                bm.faces.new((a[0], b[k], b[k2]))
            elif len(b) == 1:
                bm.faces.new((a[k], b[0], a[k2]))
            else:
                bm.faces.new((a[k], a[k2], b[k2], b[k]))
    if caps:
        for ring, p, sgn in ((rings[0], pts[0], -1), (rings[-1], pts[-1], 1)):
            if len(ring) > 1:
                c = bm.verts.new(p + (T[0] if sgn < 0 else T[-1]) * 0.0)
                for k in range(seg):
                    bm.faces.new((ring[k], ring[(k + 1) % seg], c))
    return _bm_obj(name, bm, color, mat, smooth)


def bez(ctrl, n):
    """Bezier (any degree) through control points, n+1 samples."""
    out = []
    for i in range(n + 1):
        t = i / n
        pts = [V(p) for p in ctrl]
        while len(pts) > 1:
            pts = [a.lerp(b, t) for a, b in zip(pts, pts[1:])]
        out.append(pts[0])
    return out


def lock(name, ctrl, width, thick, color, up, n=8, seg=6, mat="M_Toon", root=0.85, tip=0.0, belly=0.5, wave=None):
    """Tapered flattened hair lock / spike along a bezier. up = outward (thickness) direction."""
    pts = bez(ctrl, n)
    if wave:
        amp, freq, axis = wave
        axis = V(axis)
        pts = [p + axis * (amp * math.sin(freq * math.pi * i / n) * (i / n)) for i, p in enumerate(pts)]
    radii = []
    for i in range(n + 1):
        t = i / n
        f = (root + (1 - root) * min(1.0, t / max(belly, 1e-3))) if t < belly else 1.0
        f *= (1 - t ** 1.7) ** 0.85
        f = max(f, tip * (1 - t)) if t < 1 else tip
        radii.append((width * f, thick * f))
    return sweep(name, pts, radii, color, mat, seg=seg, up=up)


def ellipsoid(name, c, r, color, mat="M_Toon", seg=20, rings=12, rot=(0, 0, 0)):
    o = A.sphere(name, r=1.0, loc=c, rot=rot, scale=r, color=color, mat=mat, seg=seg, rings=rings)
    A.apply_transform(o)
    return o


def cyl(name, p0, p1, r0, r1=None, color="#888888", mat="M_Toon", seg=16, scale_xy=(1, 1)):
    """Cylinder/cone between two world points."""
    p0, p1 = V(p0), V(p1)
    d = p1 - p0
    o = A.cyl(name, r=r0, r2=r1, depth=d.length, color=color, mat=mat, seg=seg, scale=(scale_xy[0], scale_xy[1], 1))
    A.apply_transform(o)
    q = V((0, 0, 1)).rotation_difference(d.normalized())
    o.data.transform(Matrix.Translation((p0 + p1) / 2) @ q.to_matrix().to_4x4())
    return o


def lathe(name, profile, color, center=(0, 0, 0), sx=1.0, sy=1.0, seg=24, mat="M_Toon", a0=None, a1=None, thick=0.0,
          yshift=None, caps=True, xshift=None):
    """Revolve (r, z) around Z with elliptical scaling. a0/a1 (deg, 0 = front -Y, +90 = +X) = partial arc.
    thick > 0 solidifies (cloth). yshift(z)/xshift(z) offset rings. r may be a callable r(angle_rad)."""
    bm = bmesh.new()
    rings = []
    full = a0 is None
    cnt = seg if full else seg + 1
    for (rad, z) in profile:
        ring_ = []
        dy = yshift(z) if yshift else 0.0
        dx = xshift(z) if xshift else 0.0
        for i in range(cnt):
            if full:
                a = 2 * math.pi * i / seg
            else:
                a = math.radians(a0 + (a1 - a0) * i / seg)
            rr = rad(a) if callable(rad) else rad
            x = math.sin(a) * rr * sx + dx
            y = -math.cos(a) * rr * sy + dy
            ring_.append(bm.verts.new((center[0] + x, center[1] + y, center[2] + z)))
        rings.append(ring_)
    for ra, rb in zip(rings, rings[1:]):
        for i in range(cnt if full else cnt - 1):
            j = (i + 1) % cnt
            bm.faces.new((ra[i], ra[j], rb[j], rb[i]))
    if full and caps:
        r0 = profile[0][0](0.0) if callable(profile[0][0]) else profile[0][0]
        r1 = profile[-1][0](0.0) if callable(profile[-1][0]) else profile[-1][0]
        if r0 > 1e-4:
            bm.faces.new(list(reversed(rings[0])))
        if r1 > 1e-4:
            bm.faces.new(rings[-1])
    bmesh.ops.remove_doubles(bm, verts=bm.verts, dist=1e-6)
    if full and caps:
        bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    else:
        # outward = away from the (possibly shifted) axis
        for f in bm.faces:
            c = f.calc_center_median()
            zz = c.z - center[2]
            out = V((c.x - center[0] - (xshift(zz) if xshift else 0), c.y - center[1] - (yshift(zz) if yshift else 0), 0))
            if f.normal.dot(out) < 0:
                f.normal_flip()
    o = A._from_bmesh(name, bm)
    if thick > 0:
        solidify(o, thick)
    return _finish(o, color, mat, True)


def along(name, p0, p1, profile, color, seg=16, mat="M_Toon", thick=0.0, caps=True, sx=1.0, sy=1.0, spin=0.0):
    """Lathe profile [(r, t)] (t in 0..1 along p0->p1) revolved around the p0->p1 axis."""
    p0, p1 = V(p0), V(p1)
    d = p1 - p0
    L = d.length
    o = lathe(name, [(r, t * L) for r, t in profile], color, seg=seg, mat=mat, thick=thick, caps=caps, sx=sx, sy=sy)
    q = V((0, 0, 1)).rotation_difference(d.normalized())
    xform(o, Matrix.Translation(p0) @ q.to_matrix().to_4x4() @ Matrix.Rotation(math.radians(spin), 4, "Z"))
    return o


def capsule(name, p0, p1, r0, r1, color, seg=14, mat="M_Toon", n_cap=4, sx=1.0, sy=1.0):
    """Rounded limb: spheres of r0 at p0 and r1 at p1 joined by a cone (extends past both joints)."""
    p0, p1 = V(p0), V(p1)
    L = (p1 - p0).length
    prof = []
    for i in range(n_cap + 1):
        a = math.pi / 2 * i / n_cap
        prof.append((r0 * math.sin(a), -r0 * math.cos(a) / L))
    for i in range(n_cap + 1):
        a = math.pi / 2 * (n_cap - i) / n_cap
        prof.append((r1 * math.sin(a), 1 + r1 * math.cos(a) / L))
    return along(name, p0, p1, prof, color, seg=seg, mat=mat, sx=sx, sy=sy)


def ring(name, center, axis, R, r, color, seg=28, minor=8, mat="M_Toon", scale=(1, 1, 1)):
    bpy.ops.mesh.primitive_torus_add(major_radius=R, minor_radius=r, major_segments=seg, minor_segments=minor)
    o = bpy.context.active_object
    o.name = name
    o.data.transform(Matrix.Diagonal((scale[0], scale[1], scale[2], 1)))
    q = V((0, 0, 1)).rotation_difference(V(axis).normalized())
    xform(o, Matrix.Translation(V(center)) @ q.to_matrix().to_4x4())
    return _finish(o, color, mat, True)


def gem(name, center, normal, size, color, bezel=None):
    """Glowing cabochon with (width, height, depth) radii and an optional fitted bezel."""
    n = V(normal).normalized()
    sx, sy, depth = size
    out = []
    g = ellipsoid(name, (0, 0, 0), (sx, sy, depth), color, mat="M_Emit", seg=12, rings=8)
    q = V((0, 0, 1)).rotation_difference(n)
    xform(g, Matrix.Translation(V(center)) @ q.to_matrix().to_4x4())
    out.append(g)
    if bezel:
        radius = max(sx, sy)
        b = ring(name + "_bz", V(center) - n * depth * 0.1, n, radius * 1.08, radius * 0.20,
                 bezel, seg=16, minor=6, scale=(sx / radius, sy / radius, 1))
        out.append(b)
    return out


def zgrad(o, z0, c0, z1, c1, axis=2):
    """Colour gradient by absolute (mesh-space) coordinate between z0 (c0) and z1 (c1)."""
    c0, c1 = rgb(c0), rgb(c1)
    me = o.data
    attr = me.color_attributes["Col"]
    for loop in me.loops:
        t = (me.vertices[loop.vertex_index].co[axis] - z0) / (z1 - z0)
        t = min(1.0, max(0.0, t))
        attr.data[loop.index].color_srgb = tuple(c0[i] * (1 - t) + c1[i] * t for i in range(4))
    return o


def recolor(o, fn):
    """fn(world co) -> colour or None (keep). Per-vertex recolour."""
    me = o.data
    attr = me.color_attributes["Col"]
    for loop in me.loops:
        c = fn(o.matrix_world @ me.vertices[loop.vertex_index].co)
        if c is not None:
            attr.data[loop.index].color_srgb = rgb(c)
    return o


def solidify(o, thick, offset=-1.0):
    md = o.modifiers.new("solid", "SOLIDIFY")
    md.thickness = thick
    md.offset = offset
    md.use_even_offset = True
    A.apply_modifiers(o)
    return o


def shell(name, c, r, color, scale=(1, 1, 1), cut=None, thick=0.012, seg=32, rings=18, mat="M_Toon", keep=None):
    """Sphere shell (hood, hair cap). cut(local_dir)->True deletes that vertex region."""
    bm = bmesh.new()
    bmesh.ops.create_uvsphere(bm, u_segments=seg, v_segments=rings, radius=r)
    for v in bm.verts:
        v.co = V((v.co.x * scale[0], v.co.y * scale[1], v.co.z * scale[2]))
    if cut:
        dead = [v for v in bm.verts if cut(v.co.normalized())]
        bmesh.ops.delete(bm, geom=dead, context="VERTS")
    for v in bm.verts:
        v.co += V(c)
    o = A._from_bmesh(name, bm)
    if keep:
        A.deform(o, keep)
    if thick > 0:
        solidify(o, thick)
    return _finish(o, color, mat, True)


def xform(o, mat):
    o.data.transform(mat)
    o.data.update()
    return o


def mirror(o, name=None):
    """World-space X mirror copy with fixed normals."""
    c = o.copy()
    c.data = o.data.copy()
    c.name = name or o.name.replace(".L", ".R")
    bpy.context.scene.collection.objects.link(c)
    c.data.transform(Matrix.Scale(-1, 4, (1, 0, 0)))
    c.data.flip_normals()
    c.data.update()
    return c


# =============================================================== surface projection

def bvh_of(objs):
    verts, polys = [], []
    for o in objs:
        mw = o.matrix_world
        base = len(verts)
        verts += [mw @ v.co for v in o.data.vertices]
        polys += [[base + i for i in p.vertices] for p in o.data.polygons]
    return BVHTree.FromPolygons(verts, polys)


def _basis(normal, up):
    n = V(normal).normalized()
    r = V(up).cross(n)
    if r.length < 1e-6:
        r = V((1, 0, 0))
    r.normalize()
    u = n.cross(r).normalized()
    return n, r, u


def decal(name, shape, bvh, center, normal, color, up=(0, 0, 1), size=(1, 1), offset=0.0015, rings=2, mat="M_Toon",
          grad=None, rot=0.0):
    """Project a 2D shape (list of (u, v), u = viewer-right) onto the surface hit along -normal.
    Single-sided (no toon outline). grad=(bottom, top) for a vertical gradient."""
    n, r, u = _basis(normal, up)
    ca, sa = math.cos(math.radians(rot)), math.sin(math.radians(rot))
    pts = [(x * size[0] * ca - y * size[1] * sa, x * size[0] * sa + y * size[1] * ca) for x, y in shape]
    cx = sum(p[0] for p in pts) / len(pts)
    cy = sum(p[1] for p in pts) / len(pts)
    bm = bmesh.new()
    cv = bm.verts.new((cx, cy, 0))
    prev = None
    allr = []
    for k in range(1, rings + 1):
        s = k / rings
        ring = [bm.verts.new((cx + (x - cx) * s, cy + (y - cy) * s, 0)) for x, y in pts]
        m = len(ring)
        if prev is None:
            for i in range(m):
                bm.faces.new((cv, ring[i], ring[(i + 1) % m]))
        else:
            for i in range(m):
                bm.faces.new((prev[i], ring[i], ring[(i + 1) % m], prev[(i + 1) % m]))
        prev = ring
        allr.append(ring)
    C = V(center)
    for v in bm.verts:
        P = C + r * v.co.x + u * v.co.y
        hit = bvh.ray_cast(P + n * 0.5, -n, 1.0)
        if hit[0] is not None:
            nor = hit[1] if hit[1].dot(n) > 0 else -hit[1]
            v.co = hit[0] + nor * offset
        else:
            v.co = P
    for f in bm.faces:
        f.normal_update()
        if f.normal.dot(n) < 0:
            f.normal_flip()
    o = A._from_bmesh(name, bm)
    _finish(o, color, mat, True)
    if grad:
        A.gradient(o, grad[0], grad[1])
    return o


def ellipse(w=1.0, h=1.0, n=20, cx=0.0, cy=0.0, a0=0.0, a1=360.0):
    full = abs(a1 - a0) >= 359.9
    cnt = n if full else n + 1
    return [(cx + w * 0.5 * math.cos(math.radians(a0 + (a1 - a0) * i / (n if full else n))),
             cy + h * 0.5 * math.sin(math.radians(a0 + (a1 - a0) * i / (n if full else n)))) for i in range(cnt)]


def arc_band(w, h, t, a0, a1, n=14, cx=0.0, cy=0.0, taper=0.0):
    """Crescent band along an ellipse arc (eyelashes, brows, smiles). t = thickness (inward)."""
    outer = []
    inner = []
    for i in range(n + 1):
        f = i / n
        a = math.radians(a0 + (a1 - a0) * f)
        tt = t * (1 - taper * abs(2 * f - 1) ** 2)
        outer.append((cx + w * 0.5 * math.cos(a), cy + h * 0.5 * math.sin(a)))
        inner.append((cx + (w * 0.5 - tt) * math.cos(a), cy + (h * 0.5 - tt) * math.sin(a)))
    return outer + list(reversed(inner))


def fleur(s=1.0):
    """Fleur-de-lis-ish motif (star-shaped from its centroid)."""
    pts = [(0, 1.0), (0.18, 0.55), (0.55, 0.62), (0.42, 0.25), (0.62, 0.0), (0.25, 0.02), (0.2, -0.35),
           (0.42, -0.6), (0, -0.48), (-0.42, -0.6), (-0.2, -0.35), (-0.25, 0.02), (-0.62, 0.0), (-0.42, 0.25),
           (-0.55, 0.62), (-0.18, 0.55)]
    return [(x * s, y * s) for x, y in pts]


def cross_motif(s=1.0, arm=0.22, flare=0.1):
    a, f = arm, flare
    pts = [(-a, 1), (a, 1), (a, a), (1, a), (1, -a), (a, -a), (a + f, -1), (-a - f, -1), (-a, -a), (-1, -a),
           (-1, a), (-a, a)]
    return [(x * s, y * s) for x, y in pts]


def diamond(w=1.0, h=1.0):
    return [(0, h / 2), (w / 2, 0), (0, -h / 2), (-w / 2, 0)]


def leaf(w=1.0, h=1.0, n=10):
    pts = []
    for i in range(n + 1):
        t = i / n
        pts.append((w / 2 * math.sin(math.pi * t), h / 2 - h * t))
    for i in range(1, n):
        t = 1 - i / n
        pts.append((-w / 2 * math.sin(math.pi * t) * 0.9, h / 2 - h * t))
    return pts


def star(n=5, r0=1.0, r1=0.45):
    out = []
    for i in range(2 * n):
        a = math.pi / 2 + math.pi * i / n
        r = r0 if i % 2 == 0 else r1
        out.append((math.cos(a) * r, math.sin(a) * r))
    return out


def wrap_band(name, bvh, z0, z1, color, offset=0.004, thick=0.012, seg=36, center=(0, 0), mat="M_Toon",
              tilt=0.0, scale=(1, 1), a0=None, a1=None):
    """Belt / trim ring hugging the outermost surface of bvh between heights z0..z1 (tilt: z += tilt*y)."""
    cx, cy = center
    rows = []
    zs = (z0, z1)
    full = a0 is None
    cnt = seg if full else seg + 1
    for z in zs:
        row = []
        last = 0.1
        for i in range(cnt):
            a = 2 * math.pi * i / seg if full else math.radians(a0 + (a1 - a0) * i / seg)
            d = V((math.sin(a), -math.cos(a), 0))
            far = V((cx, cy, 0)) + d * 1.0
            zz = z + tilt * (-math.cos(a))
            hit = bvh.ray_cast(V((far.x, far.y, zz)), -d, 2.0)
            if hit[0] is not None:
                rr = (V((hit[0].x - cx, hit[0].y - cy, 0))).length
                last = rr
            else:
                rr = last
            row.append((d, zz, rr))
        rows.append(row)
    bm = bmesh.new()
    vin, vout = [], []
    for row in rows:
        ri, ro = [], []
        for d, zz, rr in row:
            p = V((cx, cy, zz))
            ri.append(bm.verts.new(p + d * (rr + offset) * 1.0))
            ro.append(bm.verts.new(p + d * (rr + offset + thick)))
        vin.append(ri)
        vout.append(ro)
    m = cnt
    rng = range(m) if full else range(m - 1)
    for i in rng:
        j = (i + 1) % m
        bm.faces.new((vout[0][i], vout[0][j], vout[1][j], vout[1][i]))
        bm.faces.new((vin[0][j], vin[0][i], vin[1][i], vin[1][j]))
        bm.faces.new((vin[0][i], vin[0][j], vout[0][j], vout[0][i]))
        bm.faces.new((vin[1][j], vin[1][i], vout[1][i], vout[1][j]))
    if not full:
        for k in (0, m - 1):
            bm.faces.new((vin[0][k], vout[0][k], vout[1][k], vin[1][k]))
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    o = A._from_bmesh(name, bm)
    if scale != (1, 1):
        xform(o, Matrix.Diagonal((scale[0], scale[1], 1, 1)))
    return _finish(o, color, mat, True)


def surface_point(bvh, origin, direction):
    """First hit going from origin+dir*1 back toward origin (outermost surface along dir)."""
    d = V(direction).normalized()
    hit = bvh.ray_cast(V(origin) + d * 1.0, -d, 2.0)
    if hit[0] is None:
        return V(origin), d
    nor = hit[1] if hit[1].dot(d) > 0 else -hit[1]
    return hit[0], nor


# =============================================================== skeleton layout

DEFAULT = dict(
    head_r=0.235, head_sx=1.06, leg=0.40, torso=0.30, neck=0.06, shoulder_w=0.125, hip_w=0.068,
    upper_arm=0.135, forearm=0.125, hand=0.072, ankle=0.075, foot_len=0.105, arm_angle=13.0,
    girth=1.0, belly=0.0, chest=1.0, hand_scale=1.0, foot_scale=1.0, limb=1.0,
)

MAIN_BONES = ["root", "hips", "spine", "chest", "neck", "head",
              "shoulder.L", "upper_arm.L", "forearm.L", "hand.L", "weapon.L",
              "shoulder.R", "upper_arm.R", "forearm.R", "hand.R", "weapon.R",
              "thigh.L", "shin.L", "foot.L", "thigh.R", "shin.R", "foot.R"]

GRIP_DIR = V((0, -1, 0.35)).normalized()


class Humanoid:
    def __init__(self, name, **params):
        self.name = name
        self.P = dict(DEFAULT)
        self.P.update(params)
        self.parts = []  # (obj, bone or weight_fn)
        self.extra_bones = []  # (name, head, tail, parent)
        self.secondary = []  # names of secondary (cloth/hair) bones
        self._layout()

    # ------------------------------------------------------------ layout
    def _layout(self):
        P = self.P
        j = {}
        hip_z = P["leg"]
        neck_z = hip_z + P["torso"]
        head_z = neck_z + P["neck"]
        hr = P["head_r"]
        j["hip"] = V((0, 0, hip_z))
        j["spine"] = V((0, 0, hip_z + P["torso"] * 0.27))
        j["chest"] = V((0, 0, hip_z + P["torso"] * 0.52))
        j["neck"] = V((0, 0, neck_z))
        j["head"] = V((0, 0, head_z))
        j["head_c"] = V((0, 0, head_z + hr * 0.80))
        sh_z = neck_z - 0.035 * P["torso"] / 0.30
        a = math.radians(P["arm_angle"])
        for s, sg in (("L", 1), ("R", -1)):
            sh = V((sg * P["shoulder_w"], 0, sh_z))
            el = sh + V((sg * math.sin(a), 0.004, -math.cos(a))) * P["upper_arm"]
            a2 = a * 0.55
            wr = el + V((sg * math.sin(a2), -0.012, -math.cos(a2))).normalized() * P["forearm"]
            hd = (wr - el).normalized()
            tip = wr + hd * P["hand"] * P["hand_scale"]
            grip = wr + hd * 0.038 * P["hand_scale"] + V((-sg * 0.004, -0.004, 0))
            j["shoulder_in." + s] = V((sg * 0.035, 0, sh_z))
            j["shoulder." + s] = sh
            j["elbow." + s] = el
            j["wrist." + s] = wr
            j["hand_tip." + s] = tip
            j["grip." + s] = grip
            hp = V((sg * P["hip_w"], 0, hip_z))
            an = V((sg * (P["hip_w"] + 0.006), 0.0, P["ankle"]))
            kn = hp.lerp(an, 0.5) + V((0, -0.006, 0))
            j["hipj." + s] = hp
            j["knee." + s] = kn
            j["ankle." + s] = an
            j["toe." + s] = an + V((0, -P["foot_len"] * P["foot_scale"], -P["ankle"] * 0.55))
        self.j = j
        self.height_est = j["head_c"].z + hr

    def bones(self):
        j = self.j
        b = [
            ("root", V((0, 0, 0)), V((0, 0, 0.1)), None),
            ("hips", j["hip"], j["spine"], "root"),
            ("spine", j["spine"], j["chest"], "hips"),
            ("chest", j["chest"], j["neck"], "spine"),
            ("neck", j["neck"], j["head"], "chest"),
            ("head", j["head"], j["head"] + V((0, 0, self.P["head_r"] * 1.9)), "neck"),
        ]
        for s in ("L", "R"):
            b += [
                ("shoulder." + s, j["shoulder_in." + s], j["shoulder." + s], "chest"),
                ("upper_arm." + s, j["shoulder." + s], j["elbow." + s], "shoulder." + s),
                ("forearm." + s, j["elbow." + s], j["wrist." + s], "upper_arm." + s),
                ("hand." + s, j["wrist." + s], j["hand_tip." + s], "forearm." + s),
                ("weapon." + s, j["grip." + s], j["grip." + s] + GRIP_DIR * 0.15, "hand." + s),
                ("thigh." + s, j["hipj." + s], j["knee." + s], "hips"),
                ("shin." + s, j["knee." + s], j["ankle." + s], "thigh." + s),
                ("foot." + s, j["ankle." + s], j["toe." + s], "shin." + s),
            ]
        return b + self.extra_bones

    def add_bone(self, name, head, tail, parent, secondary=True):
        self.extra_bones.append((name, V(head), V(tail), parent))
        if secondary:
            self.secondary.append(name)

    # ------------------------------------------------------------ parts
    def add(self, bone, *objs):
        for o in objs:
            if o is not None:
                self.parts.append((o, bone))
        return objs[0] if len(objs) == 1 else objs

    def add_blend(self, obj, fn):
        """fn(world_co) -> {bone: weight}"""
        self.parts.append((obj, fn))
        return obj

    def side(self, s):
        return 1 if s == "L" else -1

    def registered(self):
        return {obj for obj, _ in self.parts}

    # ------------------------------------------------------------ rig + skin
    def build_rig(self):
        arm = bpy.data.armatures.new("Rig")
        rig = bpy.data.objects.new("Rig", arm)
        bpy.context.scene.collection.objects.link(rig)
        bpy.context.view_layer.objects.active = rig
        bpy.ops.object.select_all(action="DESELECT")
        rig.select_set(True)
        bpy.ops.object.mode_set(mode="EDIT")
        for name, head, tail, parent in self.bones():
            eb = arm.edit_bones.new(name)
            eb.head = head
            eb.tail = tail
            if name.startswith("weapon."):
                d = (V(tail) - V(head)).normalized()
                z = V((1, 0, 0)).cross(d)
                eb.align_roll(z)
            else:
                eb.roll = 0.0
            if parent:
                eb.parent = arm.edit_bones[parent]
        bpy.ops.object.mode_set(mode="OBJECT")
        for pb in rig.pose.bones:
            pb.rotation_mode = "QUATERNION"
        arm.display_type = "STICK"
        self.rig = rig
        return rig

    def skin(self):
        objs = []
        for o, b in self.parts:
            A.apply_modifiers(o)
            A.apply_transform(o)
            for vg in list(o.vertex_groups):
                o.vertex_groups.remove(vg)
            if isinstance(b, str):
                vg = o.vertex_groups.new(name=b)
                vg.add(list(range(len(o.data.vertices))), 1.0, "REPLACE")
            else:
                groups = {}
                for v in o.data.vertices:
                    w = b(o.matrix_world @ v.co)
                    tot = sum(w.values()) or 1.0
                    for bn, ww in w.items():
                        if ww <= 1e-4:
                            continue
                        if bn not in groups:
                            groups[bn] = o.vertex_groups.new(name=bn)
                        groups[bn].add([v.index], ww / tot, "REPLACE")
            objs.append(o)
        body = A.join(objs, "Body")
        # merge vertex groups that ended duplicated by name on join is automatic in Blender.
        md = body.modifiers.new("Armature", "ARMATURE")
        md.object = self.rig
        body.parent = self.rig
        self.body = body
        return body

    def tris(self):
        me = self.body.data
        return sum(len(p.vertices) - 2 for p in me.polygons)


def blend2(b0, b1, z0, z1, axis=2, smooth=True):
    """Weight fn: b0 below z0, b1 above z1 (or the other way if z0 > z1), smooth in between."""
    def fn(co):
        t = (co[axis] - z0) / (z1 - z0)
        t = min(1.0, max(0.0, t))
        if smooth:
            t = t * t * (3 - 2 * t)
        return {b0: 1 - t, b1: t}
    return fn


def chain(bones_z, axis=2):
    """Weight fn along a bone chain: [(bone, coord), ...] ordered by coord; linear blend between neighbours."""
    def fn(co):
        c = co[axis]
        pts = bones_z
        if (pts[0][1] < pts[-1][1] and c <= pts[0][1]) or (pts[0][1] > pts[-1][1] and c >= pts[0][1]):
            return {pts[0][0]: 1.0}
        for (b0, z0), (b1, z1) in zip(pts, pts[1:]):
            lo, hi = min(z0, z1), max(z0, z1)
            if lo <= c <= hi:
                t = (c - z0) / (z1 - z0)
                t = t * t * (3 - 2 * t)
                return {b0: 1 - t, b1: t}
        return {pts[-1][0]: 1.0}
    return fn
