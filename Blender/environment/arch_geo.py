"""Procedural architecture for the dungeon kits (used by dungeon_cc0.py): rock / ice wall faces, cave and vault
ceilings, basalt hex floors, faceted ice floors, low-poly trees.

Everything is authored on the S face of a wall block (face plane y = -2, outward -Y) or on a floor cell
([-2, 2]^2, top z = 0), and colours are written straight into the `Col` attribute (sRGB face colour, one
material slot per face: M_Toon / M_Emit / M_Clear) so the meshes join with cc0_kit parts and pass `cc0_kit.finish`.

Tiling rules (cells are never rotated in Unity, so these keep neighbours seamless):
  * wall faces: displacement = base(z) + w(u) * amp(z) * noise, w = 0 at u = +-2 -> the edge columns of every
    variant are identical; noise >= 0 so faces only bulge into the corridor, and the corner chamfer (built from
    base(z) alone) closes convex corners exactly.
  * ceilings: flat at CEIL (just under the 4.5 m wall top, so wall tops pierce it -- no slit) at the cell edges,
    everything else hangs below.
"""
import math
import random

import bpy
import numpy as np
from mathutils import Matrix, Vector

import cc0_kit as C
from cc0_kit import T

H = 4.5
CEIL = 4.48


def rgb(h):
    return C.hexrgb(h)


def mix(a, b, t):
    return a * (1 - t) + b * t


def smooth(e0, e1, x):
    t = min(max((x - e0) / (e1 - e0), 0.0), 1.0)
    return t * t * (3 - 2 * t)


def colored_mesh(name, verts, faces, fcols, fmats):
    """Mesh object with one sRGB colour + material per face. Carries `src`/`key` like cc0_kit meshes."""
    me = bpy.data.meshes.new(name)
    me.from_pydata([tuple(map(float, v)) for v in verts], [], [tuple(f) for f in faces])
    me.update()
    nf, nl = len(me.polygons), len(me.loops)
    assert nf == len(faces), (name, nf, len(faces))
    lt = np.empty(nf, np.int32)
    me.polygons.foreach_get("loop_total", lt)
    out = np.ones((nl, 4), np.float32)
    out[:, :3] = np.repeat(np.clip(np.asarray(fcols, np.float32), 0, 1), lt, axis=0)
    a = me.color_attributes.new("Col", "BYTE_COLOR", "CORNER")
    a.data.foreach_set("color_srgb", out.ravel())
    me.color_attributes.active_color = a
    s = me.attributes.new("src", "FLOAT_COLOR", "CORNER")
    s.data.foreach_set("color", out.ravel())
    k = me.attributes.new("key", "INT", "FACE")
    kid = C._key_id("proc:arch")
    C._SWATCH_MEAN.setdefault("proc:arch", np.array([0.5, 0.5, 0.5], np.float32))
    k.data.foreach_set("value", np.full(nf, kid, np.int32))
    used = list(dict.fromkeys(fmats))
    for m in used:
        me.materials.append(C.material(m))
    me.polygons.foreach_set("material_index", np.array([used.index(m) for m in fmats], np.int32))
    o = bpy.data.objects.new(name, me)
    bpy.context.scene.collection.objects.link(o)
    return o


def transform(objs, M):
    for o in objs:
        o.data.transform(M)
        if M.determinant() < 0:
            o.data.flip_normals()
    return objs


def side(sd):
    """Matrix mapping the S face (outward -Y) onto side N/E/S/W of the block."""
    return Matrix.Rotation(math.radians({"N": 180, "E": 90, "S": 0, "W": -90}[sd]), 4, "Z")


class Noise:
    """Smooth 2D value in [0, 1]: a handful of seeded sine waves (cheap, deterministic)."""

    def __init__(self, seed, n=5, f=(0.7, 2.4)):
        r = random.Random(seed)
        self.t = [(r.uniform(*f) * r.choice((-1, 1)), r.uniform(*f), r.uniform(0, 6.283), r.uniform(0.5, 1.0)) for _ in range(n)]
        self.s = sum(t[3] for t in self.t)

    def __call__(self, u, v):
        x = sum(a * math.sin(fu * u + fv * v + ph) for fu, fv, ph, a in self.t) / self.s
        return 0.5 + 0.5 * max(-1.0, min(1.0, x * 1.6))


def _face_normal(p0, p1, p2):
    n = np.cross(p1 - p0, p2 - p0)
    ln = np.linalg.norm(n)
    return n / ln if ln > 1e-9 else np.array([0, -1, 0.0])


# ---------------------------------------------------------------- wall faces

def relief_face(name, seed, base, amp, colorize, nu=10, nz=10, jitter=0.3, cracks=(), crack_w=0.16,
                crack_col=None, chamfer=True):
    """Irregular natural wall face on the S side of a block.

    base(z) -> shared bulge (tiling-safe), amp(z) -> extra bulge scaled by noise inside the face.
    colorize(cu, cz, normal, rng) -> (sRGB colour, material) per triangle.
    cracks: polylines in (u, z) whose nearby triangles become crack_col / M_Emit (embedded glowing veins).
    """
    rng = random.Random(seed)
    nse = Noise(seed)
    us = np.linspace(-2, 2, nu + 1)
    zs = np.linspace(0, H, nz + 1)
    du, dz = 4.0 / nu, H / nz
    V = np.zeros((nz + 1, nu + 1, 3))
    for j, z0 in enumerate(zs):
        for i, u0 in enumerate(us):
            u, z = u0, z0
            if 0 < i < nu:
                u += rng.uniform(-jitter, jitter) * du
            if 0 < j < nz and 0 < i < nu:
                z += rng.uniform(-jitter, jitter) * dz
            w = smooth(0.0, 0.75, 2.0 - abs(u))
            d = base(z) + w * amp(z) * nse(u * 0.9, z * 0.75)
            V[j, i] = (u, -2.0 - d, z)
    verts = V.reshape(-1, 3)
    idx = lambda i, j: j * (nu + 1) + i
    faces, cols, mats = [], [], []
    segs = []
    for pl in cracks:
        for a, b2 in zip(pl[:-1], pl[1:]):
            segs.append((np.array(a, float), np.array(b2, float)))

    def near_crack(cu, cz):
        p = np.array((cu, cz))
        for a, b2 in segs:
            ab = b2 - a
            t = np.clip(np.dot(p - a, ab) / max(np.dot(ab, ab), 1e-9), 0, 1)
            if np.linalg.norm(p - (a + t * ab)) < crack_w:
                return True
        return False

    for j in range(nz):
        for i in range(nu):
            a, b_, c, d_ = idx(i, j), idx(i + 1, j), idx(i + 1, j + 1), idx(i, j + 1)
            tris = [(a, b_, c), (a, c, d_)] if rng.random() < 0.5 else [(a, b_, d_), (b_, c, d_)]
            for t in tris:
                p = verts[list(t)]
                cen = p.mean(0)
                n = _face_normal(*p)
                if segs and near_crack(cen[0], cen[2]):
                    col, mat = crack_col, "M_Emit"
                else:
                    col, mat = colorize(cen[0], cen[2], n, rng)
                faces.append(t)
                cols.append(col)
                mats.append(mat)
    if chamfer:   # +u corner: S-face edge column -> E-face edge column (both depend on base(z) only)
        off = len(verts)
        extra = []
        for z in zs:
            bz = base(z)
            extra += [(2.0, -2.0 - bz, z), (2.0 + bz, -2.0, z)]
        verts = np.vstack([verts, np.array(extra)])
        for j in range(nz):
            a, b_, c, d_ = off + 2 * j, off + 2 * j + 1, off + 2 * j + 3, off + 2 * j + 2
            p = verts[[a, b_, c]]
            col, mat = colorize(2.0, (zs[j] + zs[j + 1]) / 2, _face_normal(*p), rng)
            faces.append((a, b_, c, d_))
            cols.append(col)
            mats.append(mat)
    return colored_mesh(name, verts, faces, cols, mats)


def block_faces(name, seed, base, amp, colorize, sides="NESW", **kw):
    """All four faces of a natural wall block (one relief_face per side, different seeds)."""
    out = []
    for k, sd in enumerate("NESW"):
        if sd not in sides:
            continue
        f = relief_face(f"{name}_{sd}", seed * 7 + k, base, amp, colorize, **kw.get("per_side", {}).get(sd, {}),
                        **{a: b for a, b in kw.items() if a != "per_side"})
        f.data.transform(side(sd))
        out.append(f)
    return out


def face_point(base, u, z, out=0.0):
    """A point on the shared base surface of a natural face (S side), pushed `out` metres into the corridor."""
    return (u, -2.0 - base(z) - out, z)


def crack_paths(seed, n, z0=(0.0, 0.6), steps=(4, 7), umax=1.6):
    """Random zig-zag polylines climbing a face, in (u, z)."""
    r = random.Random(seed)
    out = []
    for _ in range(n):
        u = r.uniform(-umax, umax)
        z = r.uniform(*z0)
        pl = [(u, z)]
        for _ in range(r.randint(*steps)):
            u = max(-1.85, min(1.85, u + r.uniform(-0.45, 0.45)))
            z = min(z + r.uniform(0.35, 0.75), H - 0.2)
            pl.append((u, z))
        out.append(pl)
    return out


# ---------------------------------------------------------------- ceilings

def cave_ceiling(name, seed, amp, colorize, n=6):
    """Rough rock ceiling over a floor cell: z = CEIL at the cell edges, lumps hang below inside (normals down)."""
    rng = random.Random(seed)
    nse = Noise(seed + 5)
    xs = np.linspace(-2, 2, n + 1)
    V = []
    for j, y0 in enumerate(xs):
        for i, x0 in enumerate(xs):
            x, y = x0, y0
            if 0 < i < n and 0 < j < n:
                x += rng.uniform(-0.3, 0.3) * 4 / n
                y += rng.uniform(-0.3, 0.3) * 4 / n
            w = smooth(0, 0.7, 2 - abs(x)) * smooth(0, 0.7, 2 - abs(y))
            V.append((x, y, CEIL - w * amp * nse(x, y)))
    V = np.array(V)
    faces, cols, mats = [], [], []
    for j in range(n):
        for i in range(n):
            a, b_, c, d_ = j * (n + 1) + i, j * (n + 1) + i + 1, (j + 1) * (n + 1) + i + 1, (j + 1) * (n + 1) + i
            for t in ((a, c, b_), (a, d_, c)) if (i + j) % 2 else ((a, d_, b_), (b_, d_, c)):
                p = V[list(t)]
                col, mat = colorize(*p.mean(0)[:2], _face_normal(*p), rng)
                faces.append(t)
                cols.append(col)
                mats.append(mat)
    return colored_mesh(name, V, faces, cols, mats)


def stalactites(seed, n, colors, mat="M_Toon", length=(0.5, 1.4), radius=(0.12, 0.28), keep_out=0.0, sides=6):
    """Cones hanging from the ceiling (tips stay above 2.9 m, well over the 1.35 m eye line)."""
    r = random.Random(seed)
    out = []
    tries = 0
    while len(out) < n and tries < 200:
        tries += 1
        x, y = r.uniform(-1.8, 1.8), r.uniform(-1.8, 1.8)
        if keep_out and abs(x) < keep_out and abs(y) < keep_out:
            continue
        L = r.uniform(*length)
        rad = r.uniform(*radius)
        col = r.choice(colors)
        out.append(C.prism(f"stl{len(out)}", rad, L, sides, col, mat, M=T((x, y, CEIL + 0.04), (180, r.uniform(-6, 6), r.uniform(0, 60))), r_top=0.0))
        if r.random() < 0.5:   # a smaller twin beside it
            out.append(C.prism(f"stl{len(out)}b", rad * 0.55, L * 0.5, 5, col, mat,
                               M=T((x + r.uniform(-0.25, 0.25), y + r.uniform(-0.25, 0.25), CEIL + 0.04), (180, 0, r.uniform(0, 60))), r_top=0.0))
    return out


def vault_ceiling(name, stone, rib, boss_col, boss_mat="M_Emit"):
    """Gothic rib vault for one cell: flat dark web, transverse arch bands on the 4 edges (half width each, so
    neighbouring cells complete them), diagonal ribs to a central boss."""
    objs = [C.slab(name + "_web", -2.0, -2.0, 2.0, 2.0, CEIL - 0.04, CEIL, stone)]
    # edge bands: a pointed-arch soffit, lowest (3.85) at the corners, 4.2 in the middle
    for sd in "NESW":
        verts, faces = [], []
        n = 8
        for k in range(n + 1):
            u = -2 + 4 * k / n
            zb = CEIL - 0.3 - 0.55 * (abs(u) / 2) ** 2.2
            verts += [(u, -2.0, zb), (u, -1.82, zb), (u, -1.82, CEIL), (u, -2.0, CEIL)]
        for k in range(n):
            a = 4 * k
            b_ = a + 4
            faces += [(a, b_, b_ + 1, a + 1), (a + 1, b_ + 1, b_ + 2, a + 2)]   # soffit, inner side
        cols = [rgb(rib)] * len(faces)
        o = colored_mesh(name + "_band" + sd, verts, faces, cols, ["M_Toon"] * len(faces))
        o.data.transform(side(sd))
        objs.append(o)
    # diagonal ribs (square section 0.16), from just above the corner springing to the boss
    for k in range(4):
        a = math.radians(45 + 90 * k)
        p0 = Vector((math.cos(a) * 2.6, math.sin(a) * 2.6, 3.95))
        p1 = Vector((0, 0, CEIL - 0.12))
        d = p1 - p0
        L = d.length
        rot = d.to_track_quat("Z", "Y").to_matrix().to_4x4()
        objs.append(C.prism(f"rib{k}", 0.1, L, 4, rib, "M_Toon", M=Matrix.Translation(p0) @ rot))
    objs.append(C.prism("boss", 0.24, 0.14, 8, rib, "M_Toon", M=T((0, 0, CEIL - 0.2))))
    objs.append(C.crystal("boss_gem", 0.1, 0.1, boss_col, boss_mat, loc=(0, 0, CEIL - 0.2), rot=(180, 0, 0)))
    return objs


# ---------------------------------------------------------------- floors

def faceted_plane(name, seed, n, colorize, jitter=0.35, z=0.0, size=2.0):
    """Flat triangulated plane over the cell with per-triangle colour (frozen lake, flagstone noise)."""
    rng = random.Random(seed)
    xs = np.linspace(-size, size, n + 1)
    V = []
    for j, y0 in enumerate(xs):
        for i, x0 in enumerate(xs):
            x, y = x0, y0
            if 0 < i < n and 0 < j < n:
                x += rng.uniform(-jitter, jitter) * 2 * size / n
                y += rng.uniform(-jitter, jitter) * 2 * size / n
            V.append((x, y, z))
    V = np.array(V)
    faces, cols, mats = [], [], []
    for j in range(n):
        for i in range(n):
            a, b_, c, d_ = j * (n + 1) + i, j * (n + 1) + i + 1, (j + 1) * (n + 1) + i + 1, (j + 1) * (n + 1) + i
            for t in ((a, b_, c), (a, c, d_)) if rng.random() < 0.5 else ((a, b_, d_), (b_, c, d_)):
                col, mat = colorize(*V[list(t)].mean(0)[:2], rng)
                faces.append(t)
                cols.append(col)
                mats.append(mat)
    return colored_mesh(name, V, faces, cols, mats)


def hex_columns(name, seed, r=0.42, gap=0.9, top=(-0.07, 0.0), colors=("#2a2024",), rim=None):
    """Basalt column tops (Giant's-causeway hexes) tiling the cell; seams between them show what lies below."""
    rng = random.Random(seed)
    verts, faces, cols, mats = [], [], [], []
    w = math.sqrt(3) * r
    row = 0
    y = -2.0 - r
    while y < 2.0 + r:
        x = -2.0 - w + (w / 2 if row % 2 else 0)
        while x < 2.0 + w:
            zt = rng.uniform(*top)
            base = len(verts)
            rr = r * gap * rng.uniform(0.92, 1.0)
            for k in range(6):
                a = math.radians(30 + 60 * k)
                verts.append((x + math.cos(a) * rr, y + math.sin(a) * rr, zt))
            for k in range(6):
                a = math.radians(30 + 60 * k)
                verts.append((x + math.cos(a) * rr, y + math.sin(a) * rr, -0.3))
            c0 = rgb(rng.choice(colors)) * rng.uniform(0.9, 1.08)
            faces.append(tuple(range(base, base + 6)))
            cols.append(c0)
            mats.append("M_Toon")
            for k in range(6):
                k2 = (k + 1) % 6
                faces.append((base + k, base + 6 + k, base + 6 + k2, base + k2))
                cols.append(c0 * 0.7 if rim is None else rgb(rim))
                mats.append("M_Toon")
            x += w
        y += 1.5 * r
        row += 1
    return colored_mesh(name, verts, faces, cols, mats)


def mound(name, x0, x1, depth, height, seed, color_top, color_side, n=8, y_face=-2.0, z0=0.0):
    """Snowdrift / earth ridge along the foot of the S face: from y_face out to y_face - depth, tapering to a
    fixed profile at the block edges so neighbours line up."""
    r = random.Random(seed)
    nse = Noise(seed)
    verts, faces, cols, mats = [], [], [], []
    prof = [(0.0, 1.0), (0.35, 0.85), (0.75, 0.4), (1.0, 0.0)]   # (fraction of depth, fraction of height)
    for k in range(n + 1):
        u = x0 + (x1 - x0) * k / n
        hh = height * (0.55 + 0.9 * nse(u, 0.0) * smooth(0, 0.6, 2 - abs(u)))
        dd = depth * (0.7 + 0.6 * nse(u, 3.0) * smooth(0, 0.6, 2 - abs(u)))
        for t, s in prof:
            verts.append((u, y_face - dd * t, z0 + hh * s))
    m = len(prof)
    for k in range(n):
        for q in range(m - 1):
            a = k * m + q
            faces.append((a, a + 1, a + m + 1, a + m))
            cols.append(rgb(color_top) if q < 2 else rgb(color_side))
            mats.append("M_Toon")
    return colored_mesh(name, verts, faces, cols, mats)


# ---------------------------------------------------------------- vegetation

def blob(name, center, radius, color, seed, squash=0.85, sub=1, mat="M_Toon", shade=0.18):
    """Low-poly faceted foliage blob (icosphere, jittered), darker underneath."""
    import bmesh
    rng = random.Random(seed)
    bm = bmesh.new()
    bmesh.ops.create_icosphere(bm, subdivisions=sub, radius=1.0)
    verts = [Vector(v.co) for v in bm.verts]
    faces = [[v.index for v in f.verts] for f in bm.faces]
    bm.free()
    out = []
    for v in verts:
        k = 1 + rng.uniform(-0.12, 0.12)
        out.append((center[0] + v.x * radius * k, center[1] + v.y * radius * k, center[2] + v.z * radius * squash * k))
    out = np.array(out)
    base = rgb(color)
    cols = []
    for f in faces:
        nz = _face_normal(*out[f[:3]])[2]
        cols.append(np.clip(base * (1 - shade + shade * (nz + 1) / 2 * 1.4) * rng.uniform(0.94, 1.06), 0, 1))
    return colored_mesh(name, out, faces, cols, [mat] * len(faces))


def round_tree(seed, at=(0, 0, 0), height=5.0, crown=1.6, trunk="#6a4a32", leaves=("#3f8a34", "#57a63e", "#2f7a2e")):
    """Stylised broadleaf tree: tapered trunk + 4 faceted crown blobs (~400 tris)."""
    r = random.Random(seed)
    x, y, z = at
    objs = [C.prism("trunk", 0.26, height * 0.62, 6, trunk, r_top=0.15, M=T((x, y, z), (r.uniform(-4, 4), r.uniform(-4, 4), 0)))]
    for k, (dx, dy, dz, s) in enumerate([(0, 0, 0.78, 1.0), (0.55, 0.2, 0.62, 0.72), (-0.5, -0.3, 0.64, 0.7), (0.1, -0.55, 0.9, 0.6)]):
        objs.append(blob(f"crown{k}", (x + dx * crown, y + dy * crown, z + dz * height), crown * s, leaves[k % len(leaves)], seed + k))
    return objs


def roots(seed, at, n=4, color="#5a3e2a", length=(0.8, 1.4)):
    """Gnarled roots spreading over the ground from `at` (low flat prisms)."""
    r = random.Random(seed)
    out = []
    for k in range(n):
        a = r.uniform(0, 360)
        L = r.uniform(*length)
        out.append(C.prism(f"root{k}", 0.09, L, 4, color, r_top=0.03,
                           M=T(at, (0, 0, a)) @ T((0, 0, 0.08), (0, 82, 0))))
    return out
