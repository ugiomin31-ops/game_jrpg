"""Hero-style painted faces for monsters, so enemies share the look of the party.

The heroes (lib_humanoid/body.py `head`) paint their eyes as thin decals projected onto the head:
white -> iris with a vertical gradient (light below, dark above) -> pupil -> soft glint band ->
two small highlights -> upper lash line. Nothing bulges out of the head and only the two tiny highlights
glow. Monster eyes used to be stacked discs with a thick ink ring and a glowing iris, which read as
staring "sticker" eyes in Unity's toon shader. Everything here reuses the hero decal helpers instead.

All functions return lists of mesh objects in world space (identity transform), ready for skinning.
"""
import math
import os
import sys

sys.path.append(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'lib_humanoid'))
from humanoid import arc_band, decal, ellipse, mix, shade, zgrad  # noqa: E402
from mathutils import Vector  # noqa: E402
from mathutils.bvhtree import BVHTree  # noqa: E402

LASH = '#2a1d24'


def ellipsoid_bvh(center, radii, seg=48, rings=24):
    """Analytic ellipsoid surface to project decals onto (matches an `orb` of the same centre/radii)."""
    c, r = Vector(center), Vector(radii)
    verts, polys = [], []
    for i in range(rings + 1):
        th = math.pi * i / rings
        for j in range(seg):
            ph = math.tau * j / seg
            verts.append(Vector((c.x + r.x * math.sin(th) * math.cos(ph), c.y + r.y * math.sin(th) * math.sin(ph),
                                 c.z + r.z * math.cos(th))))
    for i in range(rings):
        for j in range(seg):
            a, b = i * seg + j, i * seg + (j + 1) % seg
            polys.append([a, b, b + seg, a + seg])
    return BVHTree.FromPolygons(verts, polys)


def object_bvh(obj):
    mw = obj.matrix_world
    return BVHTree.FromPolygons([mw @ v.co for v in obj.data.vertices], [list(p.vertices) for p in obj.data.polygons])


def cap_bvh(center, normal, size):
    """Fallback surface: a gently curved cap behind `center` (for eyes placed without a known surface)."""
    R = size * 2.6
    return ellipsoid_bvh(Vector(center) - Vector(normal).normalized() * R, (R, R, R))


def eye(name, bvh, center, normal, W, H, iris, iris_lo=None, side=1, k=1.0, pupil=None, sclera='#fdfaf7',
        lash=LASH, lash_weight=1.0, slit=False, angry=0.0, brow=None, lid=None, up=(0, 0, 1)):
    """One hero-style eye. W, H are the full width/height of the white; side=+1 creature's left (+X)."""
    n = Vector(normal).normalized()
    c = Vector(center)
    parts = [decal(name + '_w', ellipse(W, H, 24), bvh, c, n, sclera, up=up, offset=0.0012 * k)]
    ir = decal(name + '_i', ellipse(W * 0.80, H * 0.88, 22, cy=-H * 0.04), bvh, c, n, iris, up=up, offset=0.0021 * k)
    zgrad(ir, c.z - H * 0.45, iris_lo or mix(iris, '#ffffff', 0.35), c.z + H * 0.25, shade(iris, 0.42))
    parts.append(ir)
    pw, ph = (W * 0.16, H * 0.58) if slit else (W * 0.36, H * 0.46)
    parts.append(decal(name + '_p', ellipse(pw, ph, 16, cy=-H * 0.02), bvh, c, n, pupil or shade(iris, 0.25), up=up,
                       offset=0.0028 * k))
    parts.append(decal(name + '_g', arc_band(W * 0.62, H * 0.70, H * 0.10, 205, 335, n=12, cy=-H * 0.05, taper=0.8),
                       bvh, c, n, mix(iris, '#ffffff', 0.55), up=up, offset=0.0031 * k))
    parts.append(decal(name + '_h1', ellipse(W * 0.28, H * 0.28, 14, cx=-side * W * 0.17, cy=H * 0.18), bvh, c, n,
                       '#ffffff', up=up, offset=0.0037 * k, mat='M_Emit'))
    parts.append(decal(name + '_h2', ellipse(W * 0.12, H * 0.10, 10, cx=side * W * 0.16, cy=-H * 0.22), bvh, c, n,
                       '#ffffff', up=up, offset=0.0037 * k, mat='M_Emit'))
    a0, a1 = (8, 160) if side > 0 else (20, 172)
    parts.append(decal(name + '_lash', arc_band(W * 1.12, H * 1.05, 0.014 * k * lash_weight, a0, a1, n=16, cy=H * 0.01,
                                                taper=0.55), bvh, c, n, lash, up=up, offset=0.0040 * k))
    if lid:
        parts.append(decal(name + '_lid', ellipse(W * 1.04, H * 0.46, 18, cy=H * 0.34), bvh, c, n, lid, up=up,
                           offset=0.0043 * k))
    if brow or angry:
        rot = -side * 22.0 * angry
        parts.append(decal(name + '_brow', arc_band(W * 1.0, H * 0.42, 0.011 * k, 35, 145, n=10, cy=H * 0.66, taper=0.7),
                           bvh, c, n, brow or lash, up=up, offset=0.0030 * k, rot=rot))
    return parts


def socket_eye(name, bvh, center, normal, W, H, pupil='#f1e2b4', side=1, k=1.0, angry=0.0, up=(0, 0, 1)):
    """Skull eye: a dark painted socket with a small pale (non-glowing) pupil and an optional brow ridge."""
    c, n = Vector(center), Vector(normal)
    parts = [decal(name + '_socket', ellipse(W, H, 22), bvh, c, n, '#2b2230', up=up, offset=0.0015 * k),
             decal(name + '_pupil', ellipse(W * 0.3, H * 0.3, 14, cy=H * 0.04), bvh, c, n, pupil, up=up,
                   offset=0.0028 * k),
             decal(name + '_hl', ellipse(W * 0.1, H * 0.09, 8, cx=-side * W * 0.06, cy=H * 0.1), bvh, c, n, '#ffffff',
                   up=up, offset=0.0034 * k)]
    if angry:
        parts.append(decal(name + '_brow', arc_band(W * 1.1, H * 0.5, 0.014 * k, 35, 145, n=10, cy=H * 0.62, taper=0.6),
                           bvh, c, n, '#3a2c34', up=up, offset=0.0030 * k, rot=-side * 22.0 * angry))
    return parts


def glow_eye(name, bvh, center, normal, W, H, color, slant=0.0, k=1.0, up=(0, 0, 1)):
    """Flat glowing slit (helmets, skulls, elementals) — the only place a whole eye may glow."""
    return [decal(name, ellipse(W, H, 18), bvh, Vector(center), Vector(normal), color, up=up, offset=0.0025 * k,
                  mat='M_Emit', rot=slant)]


def blush(name, bvh, center, normal, W, color='#f29aa4', k=1.0, up=(0, 0, 1)):
    return [decal(name, ellipse(W, W * 0.36, 14), bvh, Vector(center), Vector(normal), color, up=up, offset=0.0010 * k)]


def mouth_line(name, bvh, center, normal, W, color=LASH, k=1.0, up=(0, 0, 1), smile=0.5):
    """Small closed mouth: a thin arc (smile > 0 curves up at the corners)."""
    a0, a1 = (200, 340) if smile >= 0 else (20, 160)
    return [decal(name, arc_band(W, W * (0.35 + 0.4 * abs(smile)), 0.007 * k, a0, a1, n=12, taper=0.6), bvh,
                  Vector(center), Vector(normal), color, up=up, offset=0.0030 * k)]


def mouth_open(name, bvh, center, normal, W, H, inner='#5a1a24', tongue='#e0707e', k=1.0, up=(0, 0, 1)):
    c, n = Vector(center), Vector(normal)
    return [decal(name, ellipse(W, H, 18), bvh, c, n, inner, up=up, offset=0.0026 * k),
            decal(name + '_tongue', ellipse(W * 0.6, H * 0.4, 14, cy=-H * 0.22), bvh, c, n, tongue, up=up,
                  offset=0.0032 * k)]
