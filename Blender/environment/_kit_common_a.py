"""Shared builders for the DungeonKitA tilesets (verdant_ruins, frost_grotto).

Geometry is accumulated in an `MB` (mesh builder) with per-face colour + material and turned
into one Blender object per logical part (main body, `Door`, `Lid`, `Spikes`, ...). This keeps
generation fast and deterministic and gives full control over winding (Unity culls back faces).

Kit conventions (see Blender/README.md "던전 키트 조각"):
- 1 cell = 4 m x 4 m, origin at the cell centre floor, floor top at z = 0.
- Wall blocks fill the cell (x, y in [-2, 2]), 4.5 m tall.
- Door-like pieces: frame plane at y = 0 spanning x in [-2, 2], passage along Y.
- Overlays hug the -Y face of a wall block placed in the same cell (y ~ -2 .. -2.35).
"""
import math
import os
import sys
import zlib

sys.path.append(r"C:\Users\User\Desktop\game\Blender\lib")
import abyss_bpy as A  # noqa: E402

import bmesh  # noqa: E402
import bpy  # noqa: E402
from mathutils import Euler, Matrix, Vector, noise  # noqa: E402

CELL = 4.0
HALF = 2.0
WALL_H = 4.5
_MATS = ("M_Toon", "M_Emit", "M_Clear")


# ---------------------------------------------------------------- colour

def C(h, a=1.0):
    if isinstance(h, str):
        return A.hexcol(h, a)
    return tuple(h) if len(h) == 4 else (h[0], h[1], h[2], 1.0)


def mix(a, b, t):
    a, b = C(a), C(b)
    t = max(0.0, min(1.0, t))
    return tuple(a[i] * (1 - t) + b[i] * t for i in range(4))


def shade(c, k):
    c = C(c)
    return (min(1.0, c[0] * k), min(1.0, c[1] * k), min(1.0, c[2] * k), c[3])


def vgrad(c0, c1, z0, z1):
    """Colour callable: vertical gradient in piece coordinates."""
    span = max(z1 - z0, 1e-6)
    return lambda co: mix(c0, c1, (co.z - z0) / span)


def rgrad(c0, c1, r0, r1, center=(0, 0)):
    """Colour callable: radial gradient around center (xy)."""
    span = max(r1 - r0, 1e-6)
    cx, cy = center
    return lambda co: mix(c0, c1, (math.hypot(co.x - cx, co.y - cy) - r0) / span)


def seed_of(*parts):
    return zlib.crc32("/".join(str(p) for p in parts).encode())


def nz(v, s=1.0):
    v = Vector(v)
    return noise.noise(v * s)


# ---------------------------------------------------------------- mesh builder

class MB:
    """Accumulates polygons with per-face colour (rgba / hex / callable(co)->rgba) and material."""

    def __init__(self):
        self.v = []
        self.f = []

    def add(self, geo, col, mat="M_Toon", smooth=False, M=None):
        verts, faces = geo
        base = len(self.v)
        if M is None:
            self.v.extend(Vector(p) for p in verts)
        else:
            if M.determinant() < 0:
                faces = [tuple(reversed(f)) for f in faces]
            self.v.extend(M @ Vector(p) for p in verts)
        if not callable(col):
            col = C(col)
        for f in faces:
            self.f.append((tuple(base + i for i in f), col, mat, smooth))
        return self

    def extend(self, other):
        base = len(self.v)
        self.v.extend(other.v)
        for idx, col, mat, sm in other.f:
            self.f.append((tuple(base + i for i in idx), col, mat, sm))
        return self

    def tris(self):
        return sum(len(f[0]) - 2 for f in self.f)

    def build(self, name, origin=(0, 0, 0)):
        o = Vector(origin)
        me = bpy.data.meshes.new(name)
        me.from_pydata([tuple(p - o) for p in self.v], [], [f[0] for f in self.f])
        used = [m for m in _MATS if any(f[2] == m for f in self.f)]
        for m in used:
            me.materials.append(A._material(m))
        mi = {m: i for i, m in enumerate(used)}
        me.polygons.foreach_set("material_index", [mi[f[2]] for f in self.f])
        me.polygons.foreach_set("use_smooth", [bool(f[3]) for f in self.f])
        attr = me.color_attributes.new("Col", "BYTE_COLOR", "CORNER")
        loops = me.loops
        for p in me.polygons:
            col = self.f[p.index][1]
            if callable(col):
                for li in p.loop_indices:
                    attr.data[li].color_srgb = C(col(self.v[loops[li].vertex_index]))
            else:
                for li in p.loop_indices:
                    attr.data[li].color_srgb = col
        me.color_attributes.active_color = attr
        me.update()
        obj = bpy.data.objects.new(name, me)
        bpy.context.scene.collection.objects.link(obj)
        obj.location = o
        return obj


def _bm_lists(bm):
    bm.verts.index_update()
    verts = [tuple(v.co) for v in bm.verts]
    faces = [[v.index for v in f.verts] for f in bm.faces]
    bm.free()
    return verts, faces


def T(loc=(0, 0, 0), rot=(0, 0, 0), scale=(1, 1, 1)):
    """Matrix from location, euler degrees, scale."""
    s = scale if hasattr(scale, "__len__") else (scale, scale, scale)
    return (Matrix.Translation(Vector(loc)) @ Euler([math.radians(a) for a in rot]).to_matrix().to_4x4()
            @ Matrix.Diagonal((s[0], s[1], s[2], 1.0)))


def basis(y_axis, z_hint, origin=(0, 0, 0), scale=1.0):
    """Matrix whose local +Y = y_axis and local +Z ~ z_hint (orthogonalised)."""
    y = Vector(y_axis).normalized()
    zh = Vector(z_hint)
    x = y.cross(zh)
    if x.length < 1e-6:
        x = y.cross(Vector((0.3, 0.1, 1.0)))
    x.normalize()
    z = x.cross(y).normalized()
    o = Vector(origin)
    s = scale
    return Matrix(((x.x * s, y.x * s, z.x * s, o.x),
                   (x.y * s, y.y * s, z.y * s, o.y),
                   (x.z * s, y.z * s, z.z * s, o.z),
                   (0, 0, 0, 1)))


def z_axis_matrix(d, origin, scale=1.0, roll_hint=(0.13, 0.71, 0.2)):
    """Matrix whose local +Z = d."""
    z = Vector(d).normalized()
    x = z.cross(Vector(roll_hint))
    if x.length < 1e-6:
        x = z.cross(Vector((1, 0, 0)))
    x.normalize()
    y = z.cross(x)
    o = Vector(origin)
    s = scale
    return Matrix(((x.x * s, y.x * s, z.x * s, o.x), (x.y * s, y.y * s, z.y * s, o.y),
                   (x.z * s, y.z * s, z.z * s, o.z), (0, 0, 0, 1)))


# ---------------------------------------------------------------- 2D polygons (CCW seen from +Z)

def rect_poly(x0, y0, x1, y1, cut=0.0, cuts=None):
    """Rectangle (CCW), optionally with chamfered corners (cuts = per-corner sizes: SW, SE, NE, NW)."""
    if cuts is None:
        cuts = (cut, cut, cut, cut)
    m = 0.45 * min(x1 - x0, y1 - y0)
    k = [min(c, m) for c in cuts]
    pts = []
    if k[0] > 1e-4:
        pts += [(x0, y0 + k[0]), (x0 + k[0], y0)]
    else:
        pts.append((x0, y0))
    if k[1] > 1e-4:
        pts += [(x1 - k[1], y0), (x1, y0 + k[1])]
    else:
        pts.append((x1, y0))
    if k[2] > 1e-4:
        pts += [(x1, y1 - k[2]), (x1 - k[2], y1)]
    else:
        pts.append((x1, y1))
    if k[3] > 1e-4:
        pts += [(x0 + k[3], y1), (x0, y1 - k[3])]
    else:
        pts.append((x0, y1))
    return pts


def circle_poly(r, n, cx=0.0, cy=0.0, rng=None, jitter=0.0, phase=0.0):
    pts = []
    for i in range(n):
        a = phase + 2 * math.pi * i / n
        rr = r * (1 + (rng.uniform(-jitter, jitter) if rng else 0))
        pts.append((cx + math.cos(a) * rr, cy + math.sin(a) * rr))
    return pts


def poly_area(poly):
    s = 0.0
    for i in range(len(poly)):
        x0, y0 = poly[i]
        x1, y1 = poly[(i + 1) % len(poly)]
        s += x0 * y1 - x1 * y0
    return s / 2


def poly_centroid(poly):
    return (sum(p[0] for p in poly) / len(poly), sum(p[1] for p in poly) / len(poly))


def inset_poly(poly, d):
    """Uniform inset of a convex CCW polygon."""
    n = len(poly)
    lines = []
    for i in range(n):
        a = Vector(poly[i])
        b = Vector(poly[(i + 1) % n])
        e = b - a
        if e.length < 1e-9:
            e = Vector((1e-6, 0))
        e.normalize()
        nrm = Vector((-e.y, e.x))
        lines.append((a + nrm * d, e))
    out = []
    for i in range(n):
        p1, d1 = lines[i - 1]
        p2, d2 = lines[i]
        den = d1.x * d2.y - d1.y * d2.x
        if abs(den) < 1e-9:
            out.append((p2.x, p2.y))
            continue
        t = ((p2.x - p1.x) * d2.y - (p2.y - p1.y) * d2.x) / den
        q = p1 + d1 * t
        out.append((q.x, q.y))
    return out


def clip_half(poly, p, nrm):
    """Keep the part of a convex polygon where (q - p) . nrm >= 0."""
    out = []
    n = len(poly)
    px, py = p
    nx, ny = nrm
    for i in range(n):
        a = poly[i]
        b = poly[(i + 1) % n]
        da = (a[0] - px) * nx + (a[1] - py) * ny
        db = (b[0] - px) * nx + (b[1] - py) * ny
        if da >= 0:
            out.append(a)
        if (da >= 0) != (db >= 0):
            t = da / (da - db)
            out.append((a[0] + (b[0] - a[0]) * t, a[1] + (b[1] - a[1]) * t))
    return out


def split_poly(poly, p, ang, gap=0.0):
    """Split a convex polygon along a line through p at angle ang; returns pieces (gap apart)."""
    nrm = (-math.sin(ang), math.cos(ang))
    g = gap / 2
    a = clip_half(poly, (p[0] + nrm[0] * g, p[1] + nrm[1] * g), nrm)
    b = clip_half(poly, (p[0] - nrm[0] * g, p[1] - nrm[1] * g), (-nrm[0], -nrm[1]))
    return [q for q in (a, b) if len(q) >= 3 and abs(poly_area(q)) > 1e-3]


def bsp_rects(rng, x0, y0, x1, y1, maxs=1.4, mins=0.55, keep=0.25):
    """Recursive random split of a rectangle into flagstone rectangles."""
    w, h = x1 - x0, y1 - y0
    big = max(w, h)
    if big <= mins * 2 or (big <= maxs and rng.random() < keep + (maxs - big)):
        return [(x0, y0, x1, y1)]
    if w >= h:
        s = x0 + w * rng.uniform(0.35, 0.65)
        return bsp_rects(rng, x0, y0, s, y1, maxs, mins, keep) + bsp_rects(rng, s, y0, x1, y1, maxs, mins, keep)
    s = y0 + h * rng.uniform(0.35, 0.65)
    return bsp_rects(rng, x0, y0, x1, s, maxs, mins, keep) + bsp_rects(rng, x0, s, x1, y1, maxs, mins, keep)


def jitter_grid_polys(rng, x0, y0, x1, y1, nx, ny, jit=0.3):
    """Irregular quads from a jittered grid; border vertices stay on the border (tileable)."""
    xs = [x0 + (x1 - x0) * i / nx for i in range(nx + 1)]
    ys = [y0 + (y1 - y0) * j / ny for j in range(ny + 1)]
    dx, dy = (x1 - x0) / nx, (y1 - y0) / ny
    Pt = {}
    for i in range(nx + 1):
        for j in range(ny + 1):
            x, y = xs[i], ys[j]
            if 0 < i < nx:
                x += rng.uniform(-jit, jit) * dx
            if 0 < j < ny:
                y += rng.uniform(-jit, jit) * dy
            Pt[i, j] = (x, y)
    return [[Pt[i, j], Pt[i + 1, j], Pt[i + 1, j + 1], Pt[i, j + 1]] for i in range(nx) for j in range(ny)]


# ---------------------------------------------------------------- 3D primitives -> (verts, faces)

def prism(poly, z0, z1, inset=0.0, ch=0.0, bottom=False, top=True):
    """Extrude a CCW polygon from z0 to z1; optional chamfer (top inset `inset` over height `ch`)."""
    n = len(poly)
    vs = [(x, y, z0) for x, y in poly]
    if inset > 0 and ch > 0:
        tp = inset_poly(poly, inset)
        vs += [(x, y, z1 - ch) for x, y in poly]
        vs += [(x, y, z1) for x, y in tp]
        rings = 3
    else:
        vs += [(x, y, z1) for x, y in poly]
        rings = 2
    fs = []
    for r in range(rings - 1):
        for i in range(n):
            j = (i + 1) % n
            fs.append((r * n + i, r * n + j, (r + 1) * n + j, (r + 1) * n + i))
    if top:
        fs.append(tuple((rings - 1) * n + i for i in range(n)))
    if bottom:
        fs.append(tuple(reversed(range(n))))
    return vs, fs


def slab(poly, z0, z1, ch=0.04, bottom=False):
    """Prism chamfered at both top and bottom edges."""
    n = len(poly)
    ip = inset_poly(poly, ch)
    rings = [(ip, z0), (poly, z0 + ch), (poly, z1 - ch), (ip, z1)]
    vs = []
    for pp, z in rings:
        vs += [(x, y, z) for x, y in pp]
    fs = []
    for r in range(3):
        for i in range(n):
            j = (i + 1) % n
            fs.append((r * n + i, r * n + j, (r + 1) * n + j, (r + 1) * n + i))
    fs.append(tuple(3 * n + i for i in range(n)))
    if bottom:
        fs.append(tuple(reversed(range(n))))
    return vs, fs


def lathe(profile, seg=12, phase=0.0):
    """Revolve [(r, z)] around Z (bottom->top). r=0 entries collapse to a pole."""
    vs, fs, rings = [], [], []
    for r, z in profile:
        if r <= 1e-5:
            rings.append([len(vs)])
            vs.append((0.0, 0.0, z))
        else:
            ring = []
            for i in range(seg):
                a = phase + 2 * math.pi * i / seg
                ring.append(len(vs))
                vs.append((math.cos(a) * r, math.sin(a) * r, z))
            rings.append(ring)
    for a, b in zip(rings, rings[1:]):
        if len(a) == 1 and len(b) == 1:
            continue
        if len(a) == 1:
            for i in range(seg):
                fs.append((a[0], b[(i + 1) % seg], b[i]) if False else (a[0], b[i], b[(i + 1) % seg])[::-1])
        elif len(b) == 1:
            for i in range(seg):
                fs.append((a[i], a[(i + 1) % seg], b[0]))
        else:
            for i in range(seg):
                j = (i + 1) % seg
                fs.append((a[i], a[j], b[j], b[i]))
    if len(rings[0]) > 1:
        fs.append(tuple(reversed(rings[0])))
    if len(rings[-1]) > 1:
        fs.append(tuple(rings[-1]))
    return vs, fs


def cyl(r, h, seg=12, z0=0.0, r2=None):
    return lathe([(r, z0), (r if r2 is None else r2, z0 + h)], seg)


def cone(r, h, seg=8, z0=0.0):
    return lathe([(r, z0), (0, z0 + h)], seg)


def box(sx, sy, sz, loc=(0, 0, 0)):
    x, y, z = loc
    poly = [(x - sx / 2, y - sy / 2), (x + sx / 2, y - sy / 2), (x + sx / 2, y + sy / 2), (x - sx / 2, y + sy / 2)]
    return prism(poly, z - sz / 2, z + sz / 2, bottom=True)


def cbox(sx, sy, sz, ch=0.05, loc=(0, 0, 0), bottom=True):
    """Chamfered box."""
    x, y, z = loc
    c = min(ch, sz / 2.2, sx / 2.2, sy / 2.2)
    poly = rect_poly(x - sx / 2, y - sy / 2, x + sx / 2, y + sy / 2)
    return slab(poly, z - sz / 2, z + sz / 2, ch=c, bottom=bottom)


def hull(points, dissolve=3.0):
    bm = bmesh.new()
    for p in points:
        bm.verts.new(p)
    res = bmesh.ops.convex_hull(bm, input=bm.verts, use_existing_faces=False)
    junk = [g for g in res["geom_interior"] + res["geom_unused"] if isinstance(g, bmesh.types.BMVert)]
    if junk:
        bmesh.ops.delete(bm, geom=junk, context="VERTS")
    if dissolve > 0:
        bmesh.ops.dissolve_limit(bm, angle_limit=math.radians(dissolve), verts=bm.verts, edges=bm.edges)
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    return _bm_lists(bm)


def rock(rng, sx, sy, sz, n=14, flat=0.0, loc=(0, 0, 0)):
    """Faceted stylised rock: hull of jittered ellipsoid points; flat>0 squashes the bottom."""
    pts = []
    ga = math.pi * (3 - math.sqrt(5))
    off = rng.uniform(0, 6.28)
    for i in range(n):
        y = 1 - 2 * (i + 0.5) / n
        r = math.sqrt(max(0.0, 1 - y * y))
        a = ga * i + off + rng.uniform(-0.3, 0.3)
        k = rng.uniform(0.85, 1.12)
        pts.append(Vector((math.cos(a) * r * k, math.sin(a) * r * k, y * k)))
    out = []
    lim = -1 + flat * 2
    for p in pts:
        z = max(p.z, lim) if flat > 0 else p.z
        out.append((loc[0] + p.x * sx / 2, loc[1] + p.y * sy / 2, loc[2] + z * sz / 2))
    return hull(out)


def ico(r, subdiv=1, loc=(0, 0, 0)):
    bm = bmesh.new()
    bmesh.ops.create_icosphere(bm, subdivisions=subdiv, radius=r)
    bmesh.ops.translate(bm, verts=bm.verts, vec=Vector(loc))
    return _bm_lists(bm)


def uvsphere(r, seg=12, rings=8, loc=(0, 0, 0), scale=(1, 1, 1)):
    prof = []
    for i in range(rings + 1):
        a = -math.pi / 2 + math.pi * i / rings
        prof.append((math.cos(a) * r if 0 < i < rings else 0.0, math.sin(a) * r))
    v, f = lathe(prof, seg)
    return [(x * scale[0] + loc[0], y * scale[1] + loc[1], z * scale[2] + loc[2]) for x, y, z in v], f


def lump_sphere(rng, r, seg=10, rings=6, loc=(0, 0, 0), scale=(1, 1, 1), lump=0.15, flat_bottom=None):
    """Organic blob (canopy puff, bush, snow pile)."""
    v, f = uvsphere(r, seg, rings)
    sd = Vector((rng.uniform(0, 50), rng.uniform(0, 50), rng.uniform(0, 50)))
    out = []
    for x, y, z in v:
        p = Vector((x, y, z))
        k = 1 + lump * noise.noise(p * (2.2 / max(r, 1e-3)) + sd)
        q = p * k
        q = Vector((q.x * scale[0], q.y * scale[1], q.z * scale[2]))
        if flat_bottom is not None:
            q.z = max(q.z, flat_bottom)
        out.append(tuple(q + Vector(loc)))
    return out, f


def tube(points, radii, sides=6, cap0=True, cap1=True):
    """Tube along a 3D polyline with per-point radius (parallel-transport frames)."""
    pts = [Vector(p) for p in points]
    n = len(pts)
    if not hasattr(radii, "__len__"):
        radii = [radii] * n
    tans = []
    for i in range(n):
        a = pts[max(i - 1, 0)]
        b = pts[min(i + 1, n - 1)]
        tans.append((b - a).normalized())
    up = Vector((0, 0, 1)) if abs(tans[0].z) < 0.9 else Vector((1, 0, 0))
    N = tans[0].cross(up).normalized()
    frames = []
    for i in range(n):
        if i > 0:
            q = tans[i - 1].rotation_difference(tans[i])
            N = q @ N
            N = (N - tans[i] * N.dot(tans[i])).normalized()
        B = tans[i].cross(N)
        frames.append((N, B))
    vs, fs, rings = [], [], []
    for i in range(n):
        N, B = frames[i]
        r = radii[i]
        if r <= 1e-5:
            rings.append([len(vs)])
            vs.append(tuple(pts[i]))
            continue
        ring = []
        for k in range(sides):
            a = 2 * math.pi * k / sides
            ring.append(len(vs))
            vs.append(tuple(pts[i] + (N * math.cos(a) + B * math.sin(a)) * r))
        rings.append(ring)
    # winding: ring order is CCW around +tangent when N x B = T -> quads (a_k, a_j, b_j, b_k) face outward
    for a, b in zip(rings, rings[1:]):
        if len(a) == 1 and len(b) == 1:
            continue
        if len(a) == 1:
            for k in range(sides):
                fs.append((a[0], b[(k + 1) % sides], b[k])[::-1][::-1] if False else (a[0], b[k], b[(k + 1) % sides])[::-1])
        elif len(b) == 1:
            for k in range(sides):
                fs.append((a[k], a[(k + 1) % sides], b[0]))
        else:
            for k in range(sides):
                j = (k + 1) % sides
                fs.append((a[k], a[j], b[j], b[k]))
    if cap0 and len(rings[0]) > 1:
        fs.append(tuple(reversed(rings[0])))
    if cap1 and len(rings[-1]) > 1:
        fs.append(tuple(rings[-1]))
    return vs, fs


def card_fan(poly2d, center, fold=None, thick=0.004):
    """Double-sided flat star/flower card in local XY (normal +Z), fanned from a centre point."""
    n = len(poly2d)
    f = fold or (lambda x, y: 0.0)
    vs = [(center[0], center[1], f(*center))] + [(x, y, f(x, y)) for x, y in poly2d]
    vs += [(x, y, z - thick) for x, y, z in vs]
    fs = []
    for i in range(n):
        j = i + 1
        k = (i + 1) % n + 1
        fs.append((0, j, k))
        fs.append((n + 1, n + 1 + k, n + 1 + j))
    return vs, fs


def leaf(L=0.25, W=0.11, fold=0.03, curl=0.03, ivy=False):
    """Leaf card along local +Y, normal +Z, base at origin. ivy=True gives a 3-lobed ivy leaf."""
    if ivy:
        pts = [(W * 0.5, 0.02 * L), (W * 1.0, 0.3 * L), (W * 0.42, 0.45 * L), (W * 0.55, 0.72 * L), (0, L),
               (-W * 0.55, 0.72 * L), (-W * 0.42, 0.45 * L), (-W * 1.0, 0.3 * L), (-W * 0.5, 0.02 * L), (0, 0)]
    else:
        pts = [(W * 0.6, 0.18 * L), (W * 0.95, 0.5 * L), (W * 0.45, 0.82 * L), (0, L),
               (-W * 0.45, 0.82 * L), (-W * 0.95, 0.5 * L), (-W * 0.6, 0.18 * L), (0, 0)]
    pts = list(reversed(pts))  # CW->CCW so the front faces +Z
    return card_fan(pts, (0, 0.45 * L), fold=lambda x, y: abs(x) / max(W, 1e-6) * fold - (y / L) ** 2 * curl)


def _double(vs, fs, off=0.006):
    m = len(vs)
    vs = vs + [(x, y, z - off) for x, y, z in vs]
    fs = fs + [tuple(reversed([i + m for i in f])) for f in fs]
    return vs, fs


def blade(L, W, bend=0.3, segs=3):
    """Curved grass blade along +Y bending down in -Z, double-sided (front +Z)."""
    vs, fs = [], []
    for i in range(segs + 1):
        t = i / segs
        w = W * (1 - t) ** 0.8
        z = -bend * L * t * t
        vs.append((-w / 2, L * t, z))
        vs.append((w / 2, L * t, z))
    for i in range(segs):
        a, b, c, d = 2 * i, 2 * i + 1, 2 * i + 3, 2 * i + 2
        fs.append((a, b, c, d))
    return _double(vs, fs)


def frond(L=1.0, W=0.28, n=7, droop=0.5):
    """Fern frond: serrated tapered leaf along +Y drooping down, double-sided (front +Z)."""
    vs = [(0, 0, 0)]
    center, left, right = [], [], []
    for i in range(1, n + 1):
        t = i / n
        y = L * t
        z = -droop * L * t * t
        w = W * math.sin(math.pi * min(1.0, t * 0.95 + 0.05)) * (1.0 if i % 2 else 0.6) + 0.01
        center.append(len(vs))
        vs.append((0, y, z + 0.015))
        left.append(len(vs))
        vs.append((-w, y - 0.07 * L, z))
        right.append(len(vs))
        vs.append((w, y - 0.07 * L, z))
    fs = []
    prev = 0
    for i in range(n):
        c = center[i]
        fs.append((prev, right[i], c))
        fs.append((prev, c, left[i]))
        prev = c
    return _double(vs, fs, 0.008)


def flower(r=0.08, petals=5):
    pts = []
    for i in range(petals * 2):
        a = math.pi * i / petals
        rr = r if i % 2 == 0 else r * 0.45
        pts.append((math.cos(a) * rr, math.sin(a) * rr))
    return card_fan(pts, (0, 0), fold=lambda x, y: (x * x + y * y) ** 0.5 * 0.4)


def crystal(r=0.12, h=0.6, seg=6, tip=0.35, base_r=None):
    """Hexagonal crystal along +Z, origin at base."""
    br = r * 0.8 if base_r is None else base_r
    return lathe([(br, -0.05), (r, h * (1 - tip)), (0, h)], seg, phase=0.3)


def bipyramid(r=0.3, h=0.9, seg=6):
    return lathe([(0, -h * 0.4), (r, 0), (r * 0.85, h * 0.18), (0, h * 0.6)], seg)


def icicle(r=0.08, L=0.6, seg=5):
    """Hanging icicle, origin at the top, pointing -Z."""
    return lathe([(0, -L), (r * 0.35, -L * 0.62), (r * 0.8, -L * 0.25), (r, 0.0)], seg)


def dome(rx, ry, h, rng, seg=10, rings=3, lump=0.12, z0=-0.02, loc=(0, 0, 0)):
    """Lumpy mound (moss / snow)."""
    prof = [(1.0, z0)]
    for i in range(1, rings):
        a = (i / rings) * math.pi / 2
        prof.append((math.cos(a), math.sin(a) * h))
    prof.append((0.0, h))
    v, f = lathe(prof, seg, phase=rng.uniform(0, 6.28))
    sd = rng.random() * 100
    out = []
    for x, y, z in v:
        k = 1 + lump * noise.noise(Vector((x * 2.1, y * 2.1, sd)))
        out.append((loc[0] + x * rx * k, loc[1] + y * ry * k, loc[2] + z * (1 + lump * 0.5 * noise.noise(Vector((x, y, sd + 3))))))
    return out, f


def disc(r, n=24, z=0.0, r_in=0.0):
    """Flat disc / annulus facing +Z."""
    if r_in <= 0:
        vs = [(0, 0, z)] + [(math.cos(2 * math.pi * i / n) * r, math.sin(2 * math.pi * i / n) * r, z) for i in range(n)]
        fs = [(0, i + 1, (i + 1) % n + 1) for i in range(n)]
        return vs, fs
    vs = []
    for i in range(n):
        a = 2 * math.pi * i / n
        vs.append((math.cos(a) * r_in, math.sin(a) * r_in, z))
        vs.append((math.cos(a) * r, math.sin(a) * r, z))
    fs = [(2 * i, 2 * i + 1, 2 * ((i + 1) % n) + 1, 2 * ((i + 1) % n)) for i in range(n)]
    return vs, fs


# ---------------------------------------------------------------- composite helpers

FACES = {
    "S": ((1, 0, 0), (0, -1, 0)),
    "N": ((-1, 0, 0), (0, 1, 0)),
    "E": ((0, 1, 0), (1, 0, 0)),
    "W": ((0, -1, 0), (-1, 0, 0)),
}


def face_matrix(side, dist=0.0):
    """Face-local frame: local X = along the face (U), local Y = +Z (up), local Z = outward normal."""
    u, n = (Vector(a) for a in FACES[side])
    t = n * dist
    return Matrix(((u.x, 0, n.x, t.x), (u.y, 0, n.y, t.y), (u.z, 1, n.z, t.z), (0, 0, 0, 1)))


def split_widths(rng, total, wmin, wmax):
    out = []
    left = total
    while left > wmax:
        w = rng.uniform(wmin, wmax)
        if left - w < wmin:
            w = left / 2
        out.append(w)
        left -= w
    out.append(left)
    rng.shuffle(out)
    return out


def leaf_spray(mb, rng, base, normal, count, size, cols, spread=0.35, droop=(0, 0, -1), ivy=True):
    """Leaves around a point, facing roughly `normal`, pointing roughly `droop`."""
    nrm = Vector(normal).normalized()
    for _ in range(count):
        d = Vector(droop) + Vector((rng.uniform(-1, 1), rng.uniform(-1, 1), rng.uniform(-0.6, 0.8))) * 0.9
        d = d - nrm * d.dot(nrm)
        if d.length < 1e-3:
            d = Vector((0, 0, -1)) if abs(nrm.z) < 0.9 else Vector((1, 0, 0))
        p = Vector(base) + Vector((rng.uniform(-1, 1), rng.uniform(-1, 1), rng.uniform(-1, 1))) * spread * size
        zn = nrm + Vector((rng.uniform(-0.4, 0.4), rng.uniform(-0.4, 0.4), rng.uniform(-0.2, 0.5)))
        s = size * rng.uniform(0.75, 1.2)
        mb.add(leaf(L=s, W=s * 0.5, ivy=ivy), rng.choice(cols), M=basis(d, zn, p))


def vine(mb, rng, pts, normal, stem_col, leaf_cols, r=0.025, leaf_size=0.22, leaf_step=0.28,
         flower_cols=None, flower_p=0.0, sides=4):
    """Stem tube along pts with ivy leaves facing `normal` (vector or callable(p))."""
    radii = [r * (1 - 0.6 * i / max(len(pts) - 1, 1)) for i in range(len(pts))]
    mb.add(tube(pts, radii, sides=sides), stem_col, smooth=True)
    Pv = [Vector(p) for p in pts]
    acc = leaf_step * 0.5
    for a, b in zip(Pv, Pv[1:]):
        seg = (b - a).length
        pos = 0.0
        while True:
            need = leaf_step - acc
            if pos + need > seg:
                acc += seg - pos
                break
            pos += need
            acc = 0.0
            p = a.lerp(b, pos / max(seg, 1e-6))
            nrm = Vector(normal(p) if callable(normal) else normal).normalized()
            side = (b - a).cross(nrm).normalized() * rng.choice((-1, 1))
            d = side * 0.8 + (b - a).normalized() * 0.5 + Vector((0, 0, -0.35))
            d = d - nrm * d.dot(nrm)
            s = leaf_size * rng.uniform(0.7, 1.2)
            zn = nrm + Vector((rng.uniform(-0.35, 0.35), rng.uniform(-0.35, 0.35), rng.uniform(0.0, 0.4)))
            mb.add(leaf(L=s, W=s * 0.55, ivy=True), rng.choice(leaf_cols), M=basis(d, zn, p + nrm * 0.02))
            if flower_cols and rng.random() < flower_p:
                fp = p + nrm * 0.05 - side * 0.09
                mb.add(flower(0.075), flower_cols[0], M=z_axis_matrix(nrm, fp))
                mb.add(cyl(0.025, 0.02, 6), flower_cols[1], M=z_axis_matrix(nrm, fp + nrm * 0.004))


def tuft(mb, rng, p, cols, n=5, L=0.25, W=0.05, bend=0.35):
    """Grass tuft: blades radiating up/out from p."""
    p = Vector(p)
    for i in range(n):
        a = 2 * math.pi * i / n + rng.uniform(-0.4, 0.4)
        out = Vector((math.cos(a), math.sin(a), 0))
        d = (out * 0.45 + Vector((0, 0, 1))).normalized()
        side = out.cross(Vector((0, 0, 1)))
        zn = side.cross(d)  # faces outward/up
        mb.add(blade(L * rng.uniform(0.7, 1.2), W, bend=bend), rng.choice(cols), M=basis(d, zn, p))


def fern(mb, rng, p, cols, n=7, L=0.9, W=0.22, droop=0.45, up=0.9):
    p = Vector(p)
    for i in range(n):
        a = 2 * math.pi * i / n + rng.uniform(-0.3, 0.3)
        out = Vector((math.cos(a), math.sin(a), 0))
        d = (out + Vector((0, 0, up * rng.uniform(0.7, 1.3)))).normalized()
        side = out.cross(Vector((0, 0, 1)))
        zn = side.cross(d) * -1
        if zn.z < 0:
            zn = -zn
        mb.add(frond(L * rng.uniform(0.75, 1.15), W, droop=droop), rng.choice(cols), M=basis(d, zn, p))


def crystal_cluster(mb, rng, p, cols, n=5, size=1.0, mat="M_Emit", spread=0.25, up=(0, 0, 1), tilt=0.45, r_scale=1.0):
    upv = Vector(up).normalized()
    p = Vector(p)
    for i in range(n):
        h = size * (1.0 if i == 0 else rng.uniform(0.35, 0.75))
        r = h * rng.uniform(0.16, 0.22) * r_scale
        off = Vector((rng.uniform(-1, 1), rng.uniform(-1, 1), 0)) * spread * size * (0 if i == 0 else 1)
        jitter = Vector((rng.uniform(-1, 1), rng.uniform(-1, 1), rng.uniform(-0.3, 0.3)))
        d = (upv + jitter * (tilt if i else tilt * 0.25) + off * 1.5).normalized()
        o = p + off
        c = cols[i % len(cols)]
        mb.add(crystal(r, h), c if callable(c) else vgrad(shade(c, 0.7), c, o.z, o.z + h * d.z), mat,
               M=z_axis_matrix(d, o))


# ---------------------------------------------------------------- scene / export / preview

def tri_count(obj):
    return sum(len(p.vertices) - 2 for p in obj.data.polygons)


def empty(name, loc, size=0.25):
    e = bpy.data.objects.new(name, None)
    e.empty_display_type = "SPHERE"
    e.empty_display_size = size
    e.location = loc
    bpy.context.scene.collection.objects.link(e)
    return e


def parent_keep(child, parent):
    bpy.context.view_layer.update()
    mw = child.matrix_world.copy()
    child.parent = parent
    child.matrix_parent_inverse = parent.matrix_world.inverted()
    child.matrix_world = mw


class Kit:
    """Builds, validates, exports pieces and lays them out for contact-sheet previews."""

    def __init__(self, tileset):
        self.ts = tileset
        self.pieces = {}
        self.order = []
        self.report = []

    def export(self, piece, objs, tri_range=(200, 3000)):
        bpy.context.view_layer.update()
        meshes = [o for o in objs if o.type == "MESH"]
        tris = sum(tri_count(o) for o in meshes)
        for o in meshes:
            assert "Col" in o.data.color_attributes, (piece, o.name)
            for m in o.data.materials:
                assert m.name in _MATS, (piece, o.name, m.name)
        lo, hi = tri_range
        status = "OK" if lo <= tris <= hi else "OUT_OF_BUDGET"
        path = A.export_fbx(f"Environment/{self.ts}/{piece}.fbx", objects=objs)
        assert os.path.exists(path), path
        names = ",".join(o.name for o in objs)
        self.report.append(f"{piece:12s} tris={tris:6d} {status} [{names}]")
        print(f"[kit] {self.ts}/{piece}: {tris} tris {status} objs={names}")
        # rename so following pieces can reuse the contract names (Door, Lid, LightAnchor, ...)
        for o in objs:
            o.name = f"{piece}__{o.name}"
        self.pieces[piece] = objs
        self.order.append(piece)
        return tris


def move_piece(objs, dx, dy, rotz=0.0):
    M = Matrix.Translation(Vector((dx, dy, 0))) @ Matrix.Rotation(math.radians(rotz), 4, "Z")
    bpy.context.view_layer.update()
    for o in objs:
        if o.parent is None:
            o.matrix_world = M @ o.matrix_world


def instance(objs, loc=(0, 0, 0), rotz=0.0, tag="inst"):
    """Copies (shared mesh data) of a piece placed in a layout (preview only)."""
    bpy.context.view_layer.update()
    M = Matrix.Translation(Vector(loc)) @ Matrix.Rotation(math.radians(rotz), 4, "Z")
    mapping = {}
    for o in objs:
        c = o.copy()
        c.name = f"{tag}_{o.name}"
        bpy.context.scene.collection.objects.link(c)
        mapping[o] = c
    for o, c in mapping.items():
        if o.parent in mapping:
            c.parent = mapping[o.parent]
    for o, c in mapping.items():
        if o.parent not in mapping:
            c.matrix_world = M @ o.matrix_world
    out = list(mapping.values())
    for c in out:
        c.hide_render = False
    return out


def only_render(visible):
    vis = set(visible)
    for o in bpy.context.scene.objects:
        if o.type in ("MESH", "EMPTY"):
            o.hide_render = o not in vis


def render_cam(name, loc, target, fov=70.0, res=(1280, 720), bg=(0.55, 0.6, 0.65), ortho=None, lens=None):
    sc = bpy.context.scene
    sc.render.engine = "BLENDER_WORKBENCH"
    sh = sc.display.shading
    sh.light = "STUDIO"
    sh.color_type = "VERTEX"
    sh.show_cavity = True
    sh.show_object_outline = True
    sh.show_shadows = True
    sh.shadow_intensity = 0.3
    sc.render.resolution_x, sc.render.resolution_y = res
    sc.render.resolution_percentage = 100
    sc.render.film_transparent = False
    sc.world = sc.world or bpy.data.worlds.new("W")
    sc.world.color = bg
    sh.background_type = "WORLD"
    cd = bpy.data.cameras.new(name + "_cam")
    if ortho:
        cd.type = "ORTHO"
        cd.ortho_scale = ortho
    elif lens:
        cd.lens = lens
    else:
        cd.sensor_fit = "VERTICAL"
        cd.angle_y = math.radians(fov)
    cd.clip_end = 1000
    cam = bpy.data.objects.new(name + "_cam", cd)
    sc.collection.objects.link(cam)
    cam.location = loc
    d = Vector(target) - Vector(loc)
    cam.rotation_euler = d.to_track_quat("-Z", "Y").to_euler()
    sc.camera = cam
    os.makedirs(A.PREVIEW_DIR, exist_ok=True)
    sc.render.filepath = os.path.join(A.PREVIEW_DIR, name + ".png")
    bpy.ops.render.render(write_still=True)
    bpy.data.objects.remove(cam)
    print(f"[preview] {sc.render.filepath}")
    return sc.render.filepath
