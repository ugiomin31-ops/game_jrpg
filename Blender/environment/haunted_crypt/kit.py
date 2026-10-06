"""haunted_crypt dungeon kit — 망자의 묘소: the great sage's tomb.

Dark purple slate masonry, gothic pointed arches, skull niches with violet candles, coffins,
bone piles, ghostly purple / teal glows (M_Emit) and spectral wisps (M_Clear); overlays = cobwebs, torn banners.
Builds every kit piece into Assets/_Game/Resources/Art/Environment/haunted_crypt/<piece>.fbx,
plus contact sheets and a 5x5 mock layout. Arena lives in arena.py.
Run: blender -b --factory-startup -P Blender/environment/haunted_crypt/kit.py
"""
import math
import os
import random
import sys

sys.path.append(os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
import _kit_common_b as K  # noqa: E402

A = K.A
import bmesh  # noqa: E402
import bpy  # noqa: E402
from mathutils import Vector  # noqa: E402

TS = "haunted_crypt"

# ---------------------------------------------------------------- palette (sRGB)
SLATE = ["#4b4064", "#55486f", "#433a5b", "#5c4e76"]
SLATE_LT = "#71628c"
SLATE_DK = "#30283f"
TRIM = "#8c6a58"          # ochre-rust edge wear seen on the reference stones
GROUT = "#1b1524"
BONE = "#ddd1b8"
BONE_DK = "#a8987c"
PURP = "#b45cff"
PURP_HOT = "#e2a8ff"
PURP_DK = "#6a2aa0"
TEAL = "#3fe0d0"
TEAL_HOT = "#b8fff6"
GHOST = "#9ff3ff"
IRON = "#4a4658"
IRON_LT = "#77728c"
WOOD = "#4a3042"
WOOD_DK = "#33202e"
CLOTH = "#6a2e7a"
CLOTH_LT = "#9a4eaa"
CLOTH_DK = "#45204f"
WAX = "#efe6d0"
PUMPKIN = "#f08a2a"
PUMPKIN_DK = "#b8561a"
VOID = "#0c0812"
WEB = "#d9cdf0"

PURPLE_FLAME = (PURP, PURP_HOT, "#ffffff")
TEAL_FLAME = (TEAL, TEAL_HOT, "#ffffff")


def R(seed):
    return random.Random(seed)


def pflame(p, loc, s=1.0, seed=0, teal=False, **kw):
    o, m, i = TEAL_FLAME if teal else PURPLE_FLAME
    return K.flame(p, loc=loc, s=s, outer=o, mid=m, inner=i, seed=seed, **kw)


# ---------------------------------------------------------------- gothic helpers

def arch_curve(w, hs, R_=None, n=6):
    """Pointed-arch intrados points (x,z) from left springing (-w/2,hs) over the apex to (w/2,hs)."""
    R_ = R_ or w * 0.85
    cx = -w / 2 + R_
    th1 = math.acos(max(-1.0, min(1.0, -cx / R_)))
    left = [(cx + R_ * math.cos(math.pi - (math.pi - th1) * i / n), hs + R_ * math.sin(math.pi - (math.pi - th1) * i / n))
            for i in range(n + 1)]
    right = [(-x, z) for (x, z) in reversed(left[:-1])]
    return left + right


def arch_opening(w, hs, R_=None, n=6):
    """Closed outline of a pointed-arch opening, bottom at z=0."""
    return [(-w / 2, 0.0)] + arch_curve(w, hs, R_, n) + [(w / 2, 0.0)]


def voussoirs(p, w, hs, depth, thick=0.32, R_=None, n=7, cols=None, y=0.0, key_col=None, rng=None):
    """Ring of wedge stones following a pointed arch (in the XZ plane at y)."""
    rng = rng or R(5)
    cols = cols or SLATE
    pts = arch_curve(w, hs, R_, n)
    out = []
    m = len(pts) - 1
    for i in range(m):
        (x0, z0), (x1, z1) = pts[i], pts[i + 1]
        # outward normals at both ends (away from arch centre-line)
        def nrm(a, b):
            dx, dz = b[0] - a[0], b[1] - a[1]
            L = math.hypot(dx, dz) or 1
            return (-dz / L, dx / L)
        n0 = nrm(pts[max(i - 1, 0)], pts[i + 1])
        n1 = nrm(pts[i], pts[min(i + 2, m)])
        g = 0.025
        a0 = (x0 + (x1 - x0) * g, z0 + (z1 - z0) * g)
        a1 = (x1 - (x1 - x0) * g, z1 - (z1 - z0) * g)
        quad = [a0, a1, (a1[0] - n1[0] * -thick, a1[1] - n1[1] * -thick), (a0[0] - n0[0] * -thick, a0[1] - n0[1] * -thick)]
        # normals computed point inward-left; flip so the ring grows outward
        quad = [a0, a1, (a1[0] - n1[0] * thick, a1[1] - n1[1] * thick), (a0[0] - n0[0] * thick, a0[1] - n0[1] * thick)]
        col = key_col if (key_col and i in (m // 2 - 1, m // 2)) else K.pick(rng, cols, 0.06)
        out.append(K.prism(f"{p}{i}", quad, depth, axis="Y", loc=(0, y, 0), color=col, bevel=0.02))
    return out


def quatrefoil(p, r, loc=(0, 0, 0), rot=(0, 0, 0), col=SLATE_LT, inner=SLATE_DK, inner_mat="M_Toon", depth=0.08,
               axis="Y"):
    """Gothic quatrefoil boss: square-ish rosette with a 4-lobed recess."""
    pts = []
    for i in range(32):
        a = 2 * math.pi * i / 32
        rr = r * 0.42 * (1 + 0.35 * abs(math.cos(2 * a)) ** 0.5)
        pts.append((math.cos(a) * rr, math.sin(a) * rr))
    lobes = []
    for i in range(24):
        a = 2 * math.pi * i / 24
        rr = r * 0.32 * (0.55 + 0.45 * abs(math.cos(2 * a)))
        lobes.append((math.cos(a) * rr, math.sin(a) * rr))
    out = [K.prism(p + "o", K.circle_pts(8, r, math.pi / 8), depth, axis=axis, color=col, bevel=0.015),
           K.prism(p + "q", lobes, depth, axis=axis, color=inner, mat=inner_mat)]
    if axis == "Y":
        out[1].location.y = -depth * 0.3
    else:
        out[1].location.z = depth * 0.3
    K.grp_place(out, loc, rot)
    return out


def gothic_diamond(p, cx, cz, s=1.0, y=-2.0, col=SLATE_DK, rim=SLATE_LT, glow=None):
    """Elongated cross-diamond carving (ref pilasters) on a -Y face."""
    out = [K.prism(p + "r", [(0, 0.5 * s), (0.16 * s, 0.12 * s), (0.24 * s, 0), (0.16 * s, -0.12 * s), (0, -0.5 * s),
                             (-0.16 * s, -0.12 * s), (-0.24 * s, 0), (-0.16 * s, 0.12 * s)], 0.04, axis="Y",
                   loc=(cx, y - 0.005, cz), color=rim),
           K.prism(p + "c", [(0, 0.38 * s), (0.09 * s, 0.08 * s), (0.16 * s, 0), (0.09 * s, -0.08 * s), (0, -0.38 * s),
                             (-0.09 * s, -0.08 * s), (-0.16 * s, 0), (-0.09 * s, 0.08 * s)], 0.04, axis="Y",
                   loc=(cx, y - 0.02, cz), color=glow or col, mat="M_Emit" if glow else "M_Toon")]
    return out


def niche(p, rng, cx, cz, y=-2.0, w=0.8, hs=0.55, depth=0.35, skulls=1, candles=2, glow=PURP):
    """Pointed-arch wall niche with skulls and violet candles (ref wall)."""
    out = []
    # dark recess back panel + glow
    hole = K.prism(p + "bk", arch_opening(w, hs, w * 0.7, 5), 0.04, axis="Y", loc=(cx, y + depth, cz), color=VOID)
    out.append(hole)
    out.append(K.prism(p + "gl", arch_opening(w * 0.55, hs * 0.8, w * 0.4, 4), 0.02, axis="Y",
                       loc=(cx, y + depth - 0.03, cz + 0.08), color=PURP_DK, mat="M_Emit"))
    # side walls + floor of the recess
    for sx in (-1, 1):
        out.append(A.box(p + f"sw{sx}", (0.04, depth, hs + w * 0.3), loc=(cx + sx * w / 2, y + depth / 2, cz + (hs + w * 0.3) / 2),
                         color=SLATE_DK))
    out.append(A.box(p + "fl", (w, depth, 0.04), loc=(cx, y + depth / 2, cz), color=SLATE_DK))
    # stone frame (voussoirs + sill)
    vs = voussoirs(p + "v", w, hs, 0.12, thick=0.14, R_=w * 0.7, n=4, y=y - 0.02, rng=rng)
    K.grp_place(vs, loc=(cx, 0, cz))
    out += vs
    for sx in (-1, 1):
        out.append(K.stone(p + f"jb{sx}", (0.14, 0.12, hs), loc=(cx + sx * (w / 2 + 0.07), y - 0.02, cz + hs / 2),
                           color=K.pick(rng, SLATE), bevel=0.02, cull="+Y"))
    out.append(K.stone(p + "sl", (w + 0.42, 0.24, 0.1), loc=(cx, y - 0.06, cz - 0.04), color=SLATE_LT, bevel=0.02))
    # contents
    xs = [cx - w * 0.22, cx + w * 0.18]
    for i in range(skulls):
        out += K.skull(p + f"sk{i}", s=0.85 + 0.1 * i, loc=(xs[i % 2], y + depth * 0.45, cz + 0.02), low=True,
                       rot=(0, 0, rng.uniform(-20, 20)), color=BONE)
    for i in range(candles):
        x = xs[(i + 1) % 2] + 0.07 * i
        out += K.candle(p + f"cd{i}", h=0.16 + 0.07 * (1 - i), r=0.035, loc=(x, y + depth * 0.35, cz + 0.02), seed=i + len(p),
                        flame_col=(glow, PURP_HOT, "#ffffff"))
    return out


def cobweb(p, rng, r=0.9, spokes=6, rings=4, a0=0.0, a1=90.0, w=0.012, sag=0.12):
    """Flat corner cobweb in the XZ plane (fan from origin) — thin quads, M_Clear."""
    bm = bmesh.new()

    def quad(pa, pb, ww):
        d = Vector((pb[0] - pa[0], pb[1] - pa[1]))
        if d.length < 1e-5:
            return
        nrm = Vector((-d.y, d.x)).normalized() * ww / 2
        vs = [bm.verts.new((pa[0] - nrm.x, 0, pa[1] - nrm.y)), bm.verts.new((pb[0] - nrm.x, 0, pb[1] - nrm.y)),
              bm.verts.new((pb[0] + nrm.x, 0, pb[1] + nrm.y)), bm.verts.new((pa[0] + nrm.x, 0, pa[1] + nrm.y))]
        f = bm.faces.new(vs)
        bm.faces.new(list(reversed([bm.verts.new(v.co) for v in vs])))  # back side so it shows from both directions

    angs = [math.radians(a0 + (a1 - a0) * i / (spokes - 1)) for i in range(spokes)]
    lens = [r * rng.uniform(0.85, 1.05) for _ in angs]
    for a, L in zip(angs, lens):
        quad((0, 0), (math.cos(a) * L, math.sin(a) * L), w * 1.3)
    for k in range(1, rings + 1):
        t = k / (rings + 0.6)
        for i in range(spokes - 1):
            pa = (math.cos(angs[i]) * lens[i] * t, math.sin(angs[i]) * lens[i] * t)
            pb = (math.cos(angs[i + 1]) * lens[i + 1] * t, math.sin(angs[i + 1]) * lens[i + 1] * t)
            mid = ((pa[0] + pb[0]) / 2, (pa[1] + pb[1]) / 2)
            # sag toward the corner
            mid = (mid[0] * (1 - sag * t), mid[1] * (1 - sag * t))
            quad(pa, mid, w)
            quad(mid, pb, w)
    return K._obj_from_bm(p, bm, WEB, "M_Clear", recalc=False)


# ---------------------------------------------------------------- floors

def floor_grout(p, col=GROUT):
    return [A.box(p + "grout", (4.0, 4.0, 0.2), loc=(0, 0, -0.17), color=col)]


def bones_scatter(p, rng, n, rect, z=0.0):
    out = []
    x0, y0, x1, y1 = rect
    for i in range(n):
        x, y = rng.uniform(x0, x1), rng.uniform(y0, y1)
        a = rng.uniform(0, 360)
        ln = rng.uniform(0.18, 0.3)
        b = [A.cyl(f"{p}{i}s", r=0.022, depth=ln, rot=(0, 90, 0), color=BONE, seg=5, smooth=False)]
        for sx in (-1, 1):
            b.append(A.sphere(f"{p}{i}k{sx}", 0.035, loc=(sx * ln / 2, 0, 0), scale=(1, 1.4, 1), color=BONE, seg=6, rings=4))
        K.grp_place(b, loc=(x, y, z + 0.03), rot=(0, 0, a))
        out += b
    return out


def rune_inlay(p, x, y, s=0.12, col=TEAL, rot=0):
    return [K.prism(p, [(0, s), (s * 0.55, 0), (0, -s), (-s * 0.55, 0)], 0.01, axis="Z", loc=(x, y, 0.004),
                    rot=(0, 0, rot), color=col, mat="M_Emit"),
            K.prism(p + "i", [(0, s * 0.45), (s * 0.25, 0), (0, -s * 0.45), (-s * 0.25, 0)], 0.01, axis="Z",
                    loc=(x, y, 0.008), rot=(0, 0, rot), color=SLATE_DK)]


def floor_a():
    rng = R(1101)
    objs = floor_grout("fa")
    objs += K.flagstones("fa_s", rng, (-2, -2, 2, 2), SLATE, gap=0.08, min_size=0.7, max_size=1.4, chamfer=0.24,
                         col_fn=lambda r, x, y: K.pick(r, [TRIM], 0.05) if r.random() < 0.05 else K.pick(r, SLATE, 0.07))
    objs += K.scatter_pebbles("fa_p", rng, 18, (-1.95, -1.95, 1.95, 1.95), -0.07, [SLATE_DK, SLATE[2]], r=(0.04, 0.07))
    objs += bones_scatter("fa_b", rng, 2, (-1.5, -1.5, 1.5, 1.5))
    objs += rune_inlay("fa_r0", 0.62, -0.7, rot=10)
    objs += rune_inlay("fa_r1", -0.9, 0.85, rot=-15)
    return [K.finish("floor_a", objs)]


def floor_b():
    """Paving with an engraved tomb slab of a crypt knight in the centre (purple rune glow)."""
    rng = R(1202)
    objs = floor_grout("fb")
    cx0, cy0, cx1, cy1 = -0.7, -1.25, 0.7, 1.25

    for (x0, y0, x1, y1) in [(-2, -2, 2, cy0), (-2, cy1, 2, 2), (-2, cy0, cx0, cy1), (cx1, cy0, 2, cy1)]:
        objs += K.flagstones("fb_s", rng, (x0, y0, x1, y1), SLATE, gap=0.08, min_size=0.55, max_size=1.3, chamfer=0.22)
    objs.append(K.poly_slab("fb_t", [(cx0 + 0.04, cy0 + 0.04), (cx1 - 0.04, cy0 + 0.04), (cx1 - 0.04, cy1 - 0.04),
                                     (cx0 + 0.04, cy1 - 0.04)], top=0.0, thick=0.22, color=SLATE_LT, bevel=0.04))
    objs.append(K.poly_slab("fb_tr", [(-0.55, -1.1), (0.55, -1.1), (0.55, 1.1), (-0.55, 1.1)], top=0.006, thick=0.02,
                            color=TRIM, bevel=0.0))
    objs.append(K.poly_slab("fb_ti", [(-0.5, -1.05), (0.5, -1.05), (0.5, 1.05), (-0.5, 1.05)], top=0.008, thick=0.02,
                            color=SLATE[1], bevel=0.0))
    # engraved cross-sword (glowing purple) + quatrefoil
    objs.append(K.prism("fb_sw", [(-0.04, -0.75), (0.04, -0.75), (0.04, 0.45), (0, 0.58), (-0.04, 0.45)], 0.01, axis="Z",
                        loc=(0, 0, 0.012), color=PURP, mat="M_Emit"))
    objs.append(K.prism("fb_gd", [(-0.26, 0.0), (0.26, 0.0), (0.26, 0.06), (-0.26, 0.06)], 0.01, axis="Z",
                        loc=(0, -0.42, 0.012), color=PURP, mat="M_Emit"))
    objs += quatrefoil("fb_q", 0.26, loc=(0, 0.78, 0.012), axis="Z", col=SLATE_LT, inner=PURP_DK, inner_mat="M_Emit",
                       depth=0.012)
    for sx in (-1, 1):
        for sy in (-1, 1):
            objs.append(K.gem(f"fb_g{sx}{sy}", 0.05, loc=(sx * 0.42, sy * 0.98, 0.02), rot=(0, 90, 0), color=PURP, h=1.0))
    objs += K.scatter_pebbles("fb_p", rng, 12, (-1.95, -1.95, 1.95, 1.95), -0.07, [SLATE_DK], r=(0.04, 0.07),
                              avoid=lambda x, y: abs(x) < 0.8 and abs(y) < 1.35)
    return [K.finish("floor_b", objs)]


def floor_c():
    """Broken slate with violet soul-light seeping through the cracks, bone fragments."""
    rng = R(1303)
    objs = floor_grout("fc", VOID)
    objs.append(A.box("fc_glow", (3.0, 2.6, 0.02), loc=(0.3, -0.2, -0.07), rot=(0, 0, 20), color=PURP_DK, mat="M_Emit"))
    objs.append(A.box("fc_hot", (1.6, 0.35, 0.02), loc=(0.2, -0.1, -0.06), rot=(0, 0, -30), color=PURP, mat="M_Emit"))
    objs += K.flagstones("fc_s", rng, (-2, -2, 2, 2), SLATE, gap=0.12, min_size=0.5, max_size=1.5, chamfer=0.34,
                         tilt=0.025, rotj=0.14, col_fn=lambda r, x, y: K.pick(r, SLATE, 0.1))
    objs += bones_scatter("fc_b", rng, 3, (-1.6, -1.6, 1.6, 1.6))
    objs += K.skull("fc_sk", s=0.9, loc=(-1.2, 1.1, 0.0), rot=(8, 0, 35), low=True)
    return [K.finish("floor_c", objs)]


# ---------------------------------------------------------------- walls

def wall_core(p, col=SLATE_DK, mat="M_Toon", s=3.86):
    return [A.box(p + "core", (s, s, 4.42), loc=(0, 0, 2.21), color=col, mat=mat)]


def wall_top(p, rng, z=4.5, boss=True):
    objs = [A.box(p + "topg", (3.98, 3.98, 0.12), loc=(0, 0, z - 0.1), color=GROUT)]
    objs += K.flagstones(p + "top", rng, (-2, -2, 2, 2), SLATE, gap=0.08, min_size=1.2, max_size=2.1, top=z, thick=0.25,
                         chamfer=0.22, skip=(lambda cx, cy, r: abs(cx) < 0.6 and abs(cy) < 0.6) if boss else None)
    if boss:
        objs += quatrefoil(p + "qb", 0.62, loc=(0, 0, z + 0.04), axis="Z", depth=0.14)
    return objs


def pilaster(p, rng, x, y, h=4.1):
    o = [K.stone(p + "b", (0.62, 0.62, 0.42), loc=(x, y, 0.21), color=SLATE_LT, bevel=0.04),
         A.box(p + "s", (0.5, 0.5, h - 0.8), loc=(x, y, 0.42 + (h - 0.8) / 2), color=K.pick(rng, SLATE, 0.04)),
         K.stone(p + "c", (0.64, 0.64, 0.38), loc=(x, y, h - 0.2), color=SLATE_LT, bevel=0.04),
         K.stone(p + "t", (0.42, 0.42, 0.22), loc=(x, y, h + 0.1), color=TRIM, bevel=0.03)]
    o.append(K.gem(p + "f", 0.2, loc=(x, y, h + 0.3), rot=(0, 0, 45), color=SLATE_LT, mat="M_Toon", h=1.6))
    return o


def wall_a():
    """Ashlar with corner pilasters and a skull-and-candle niche on every face (the reference wall)."""
    rng = R(2101)
    objs = wall_core("wa")

    def side(k):
        r = R(2110 + k)
        o = [K.stone(f"wa{k}pl", (3.0, 0.4, 0.4), loc=(0, -1.8, 0.2), color=SLATE_LT, bevel=0.04, cull="+Y"),
             K.stone(f"wa{k}co", (3.0, 0.42, 0.3), loc=(0, -1.79, 4.15), color=SLATE_LT, bevel=0.04, cull="+Y")]
        # ashlar around the niche (left / right columns + top band + lower band)
        o += K.ashlar_face(f"wa{k}l", r, -1.4, -0.62, 0.4, 4.0, SLATE, y_face=-1.96, course=(0.6, 0.9), length=(0.78, 0.8),
                           gap=0.05, bevel=0.05)
        o += K.ashlar_face(f"wa{k}r", r, 0.62, 1.4, 0.4, 4.0, SLATE, y_face=-1.96, course=(0.6, 0.9), length=(0.78, 0.8),
                           gap=0.05, bevel=0.05)
        o += K.ashlar_face(f"wa{k}d", r, -0.62, 0.62, 0.4, 1.45, SLATE, y_face=-1.96, course=(0.5, 0.6), length=(0.6, 1.24),
                           gap=0.05, bevel=0.05)
        o += K.ashlar_face(f"wa{k}u", r, -0.62, 0.62, 3.0, 4.0, SLATE, y_face=-1.96, course=(0.45, 0.6), length=(0.6, 1.24),
                           gap=0.05, bevel=0.05)
        o.append(A.box(f"wa{k}nb", (1.24, 0.2, 1.55), loc=(0, -1.88, 2.22), color=GROUT))
        o += niche(f"wa{k}n", r, 0, 1.55, y=-1.98, w=0.8, hs=0.6, skulls=1 + (k % 2), candles=2 - (k % 2))
        o += pilaster(f"wa{k}p", r, 1.69, -1.69)
        for cx in (-1.69, 1.69):
            o += gothic_diamond(f"wa{k}gd{cx}", cx, 2.3, s=0.9, y=-1.95)
        return o

    objs += K.four_sides(side)
    objs += wall_top("wa", rng)
    return [K.finish("wall_a", objs)]


def wall_b():
    """Ossuary: pointed arcade framing shelves stacked with skulls, purple soul-glow behind."""
    rng = R(2201)
    objs = wall_core("wb")

    def side(k):
        r = R(2210 + k)
        o = [K.stone(f"wb{k}pl", (4.0, 0.44, 0.45), loc=(0, -1.78, 0.22), color=SLATE_LT, bevel=0.05, cull="+Y")]
        # recess with glow
        o.append(A.box(f"wb{k}bk", (2.6, 0.05, 2.9), loc=(0, -1.6, 2.05), color=PURP_DK, mat="M_Emit"))
        # surrounding ashlar
        o += K.ashlar_face(f"wb{k}s", r, -2.0, -1.32, 0.45, 4.2, SLATE, y_face=-2.0, course=(0.7, 1.0), length=(0.68, 0.7),
                           gap=0.05, bevel=0.05)
        o += K.ashlar_face(f"wb{k}t", r, 1.32, 2.0, 0.45, 4.2, SLATE, y_face=-2.0, course=(0.7, 1.0), length=(0.68, 0.7),
                           gap=0.05, bevel=0.05)
        o.append(A.box(f"wb{k}sp", (2.64, 0.4, 0.8), loc=(0, -1.8, 4.1), color=K.pick(r, SLATE)))
        vs = voussoirs(f"wb{k}v", 2.64, 2.3, 0.4, thick=0.3, R_=2.2, n=6, y=-1.82, rng=r, key_col=SLATE_LT)
        o += vs
        # fill spandrels above the arch
        for sx in (-1, 1):
            o.append(K.prism(f"wb{k}fill{sx}", [(sx * 1.32, 2.3), (sx * 1.32, 3.7), (sx * 0.15, 3.7)], 0.38, axis="Y",
                             loc=(0, -1.8, 0), color=SLATE_DK))
        # shelves + skulls
        for si, z in enumerate((0.55, 1.35, 2.15)):
            o.append(K.stone(f"wb{k}sh{si}", (2.62, 0.4, 0.1), loc=(0, -1.75, z), color=SLATE_LT, bevel=0.02))
            nsk = 4 if si < 2 else 3
            for j in range(nsk):
                x = -1.0 + 2.0 * (j + 0.5) / nsk + r.uniform(-0.06, 0.06)
                o += K.skull(f"wb{k}k{si}{j}", s=1.1, loc=(x, -1.7, z + 0.05), rot=(0, 0, r.uniform(-25, 25)), low=True,
                             color=K.jit(r, BONE, 0.05))
            # long bones stacked behind skulls
            o.append(A.box(f"wb{k}lb{si}", (2.5, 0.2, 0.2), loc=(0, -1.55, z + 0.15), color=BONE_DK))
        o += K.candle(f"wb{k}cd", h=0.25, r=0.05, loc=(0.85, -1.85, 2.2), seed=k)
        o += quatrefoil(f"wb{k}q", 0.38, loc=(0, -2.02, 3.75))
        return o

    objs += K.four_sides(side)
    objs += wall_top("wb", rng, boss=False)
    return [K.finish("wall_b", objs)]


def wall_c():
    """Collapsed crypt rubble: big cracked slate blocks, violet cracks, roots and webs."""
    rng = R(2301)
    objs = wall_core("wc", col=PURP_DK, mat="M_Emit", s=3.72)
    for li, (z0, z1) in enumerate([(0.0, 1.4), (1.4, 2.95), (2.95, 4.5)]):
        for ix in range(2):
            for iy in range(2):
                cx, cy = -1.0 + 2.0 * ix, -1.0 + 2.0 * iy
                h = z1 - z0
                objs.append(K.stone(f"wc{li}{ix}{iy}", (1.92, 1.92, h - 0.08), loc=(cx, cy, z0 + h / 2),
                                    color=K.pick(rng, SLATE, 0.1), bevel=0.14, rough=0.08, seed=rng.randint(0, 9999), freq=1.2))

    def side(k):
        r = R(2310 + k)
        o = []
        # dangling roots
        for j in range(2):
            x = r.uniform(-1.4, 1.4)
            pts = [(x, -2.02, 4.4)]
            for t in range(1, 5):
                pts.append((x + r.uniform(-0.12, 0.12), -2.04 - 0.02 * t, 4.4 - t * r.uniform(0.3, 0.45)))
            o.append(A.tube(f"wc{k}rt{j}", pts, radius=0.035, color="#8a6448", seg=4, taper_end=0.3))
        # embedded tomb plaque
        if k % 2 == 0:
            o.append(K.stone(f"wc{k}pq", (0.9, 0.12, 0.6), loc=(r.uniform(-0.6, 0.6), -2.0, r.uniform(1.0, 2.5)),
                             color=SLATE_LT, bevel=0.03, cull="+Y"))
            o += gothic_diamond(f"wc{k}gd", o[-1].location.x, o[-1].location.z, s=0.45, y=-2.06, glow=PURP)
        return o

    objs += K.four_sides(side)
    w = cobweb("wc_web", rng, r=0.9)
    K.grp_place([w], loc=(-1.95, -2.03, 4.45), rot=(0, 180, 0))
    objs.append(w)
    objs += bones_scatter("wc_b", rng, 2, (-1.2, -1.2, 1.2, 1.2), z=4.5)
    mesh = K.finish("wall_c", objs)
    for v in mesh.data.vertices:
        v.co.x = min(max(v.co.x, -2.0), 2.0)
        v.co.y = min(max(v.co.y, -2.05), 2.0)
        v.co.z = max(v.co.z, 0.0)
    return [mesh]


# ---------------------------------------------------------------- door / gates

OPEN_W, OPEN_HS = 2.2, 2.25


def door_frame(p, rng, depth=1.0):
    objs = []
    for sx in (-1, 1):
        cx = sx * (OPEN_W / 2 + (2.0 - OPEN_W / 2) / 2)
        w = 2.0 - OPEN_W / 2
        objs.append(K.stone(f"{p}pl{sx}", (w, depth + 0.12, 0.42), loc=(cx, 0, 0.21), color=SLATE_LT, bevel=0.04))
        z, i = 0.42, 0
        while z < 4.1:
            hh = min(rng.uniform(0.7, 0.95), 4.1 - z)
            objs.append(K.stone(f"{p}j{sx}{i}", (w - 0.06, depth, hh - 0.04), loc=(cx, 0, z + hh / 2),
                                color=K.pick(rng, SLATE), bevel=0.04, cull=("+X" if sx < 0 else "-X") if z > 99 else None))
            z += hh
            i += 1
        for side in (-1, 1):
            objs += K.grp_place(gothic_diamond(f"{p}gd{sx}{side}", 0, 0, s=0.8, y=0, glow=PURP),
                                loc=(cx, side * (depth / 2 + 0.005), 1.6), rot=(0, 0, 0 if side < 0 else 180))
    # arch ring (front + back faces share one deep voussoir ring) + infill above
    objs += voussoirs(p + "v", OPEN_W, OPEN_HS, depth + 0.1, thick=0.36, R_=OPEN_W * 0.8, n=7, rng=rng, key_col=SLATE_LT)
    apex = arch_curve(OPEN_W, OPEN_HS, OPEN_W * 0.8, 7)
    top_z = max(z for _, z in apex)
    for sx in (-1, 1):
        objs.append(K.prism(f"{p}fill{sx}", [(sx * OPEN_W / 2, OPEN_HS), (sx * 1.98, OPEN_HS), (sx * 1.98, 4.5), (0, 4.5),
                                              (0, top_z + 0.3)], depth - 0.1, axis="Y", color=SLATE_DK))
    objs.append(K.stone(p + "co", (4.0, depth + 0.16, 0.3), loc=(0, 0, 4.35), color=SLATE_LT, bevel=0.04))
    for side in (-1, 1):
        objs += quatrefoil(f"{p}q{side}", 0.32, loc=(0, side * (depth / 2 + 0.02), top_z + 0.62),
                           rot=(0, 0, 0 if side < 0 else 180), inner=PURP_DK, inner_mat="M_Emit")
    objs.append(A.box(p + "th", (OPEN_W, depth, 0.05), loc=(0, 0, 0.025), color=SLATE_LT))
    return objs


def door_leaf(p, rng):
    w = OPEN_W - 0.08
    outline = arch_opening(w, OPEN_HS, w * 0.8, 7)
    objs = [K.prism(p + "body", outline, 0.12, axis="Y", color=WOOD)]
    # plank grooves
    for i in range(1, 5):
        x = -w / 2 + w * i / 5
        # height of the arch at x
        hz = max((z for (xx, z) in arch_curve(w, OPEN_HS, w * 0.8, 24) if abs(xx - x) < 0.08), default=OPEN_HS)
        for sy in (-1, 1):
            objs.append(A.box(f"{p}gr{i}{sy}", (0.025, 0.012, hz - 0.1), loc=(x, sy * 0.061, (hz - 0.1) / 2 + 0.04),
                              color=WOOD_DK))
    # iron straps with studs
    for zi, z in enumerate((0.45, 1.5)):
        for sy in (-1, 1):
            objs.append(A.box(f"{p}st{zi}{sy}", (w - 0.02, 0.03, 0.14), loc=(0, sy * 0.07, z), color=IRON))
            for xi in range(5):
                objs.append(K.gem(f"{p}sd{zi}{xi}{sy}", 0.035, loc=(-w / 2 + 0.15 + (w - 0.3) * xi / 4, sy * 0.09, z),
                                  rot=(90, 0, 45), color=IRON_LT, mat="M_Toon", h=0.8))
    # iron arch rim
    rim = arch_curve(w - 0.08, OPEN_HS, (w - 0.08) * 0.8, 7)
    for sy in (-1, 1):
        objs.append(A.tube(f"{p}rim{sy}", [(x, sy * 0.075, z) for (x, z) in rim], radius=0.035, color=IRON, seg=4))
        # skull door knocker with ring
        objs += K.skull(f"{p}kn{sy}", s=0.75, loc=(0.55, sy * 0.1, 1.05), rot=(0, 0, 0 if sy < 0 else 180), low=True,
                        color=BONE)
        objs.append(A.torus(f"{p}rg{sy}", R=0.1, r=0.02, loc=(0.55, sy * 0.16, 0.95), rot=(90, 0, 0), color=IRON_LT, seg=10,
                            minor=4))
        objs.append(K.gem(f"{p}gm{sy}", 0.09, loc=(0, sy * 0.08, 2.55), rot=(90, 0, 45), color=PURP, h=1.4))
    return objs


def build_door(locked):
    rng = R(3001 if not locked else 3002)
    name = "door_locked" if locked else "door"
    frame = K.finish(name, door_frame("df", rng))
    leaf = K.finish("Door", door_leaf("dl", rng), origin=(-(OPEN_W - 0.08) / 2, 0, 0))
    out = [frame, leaf]
    if locked:
        lo = [K.stone("lk_b", (0.5, 0.18, 0.56), loc=(0, -0.16, 1.5), color=IRON, bevel=0.06)]
        lo += K.skull("lk_sk", s=1.0, loc=(0, -0.2, 1.43), low=True)
        lo.append(A.torus("lk_sh", R=0.18, r=0.045, loc=(0, -0.16, 1.82), rot=(90, 0, 0), color=IRON_LT, seg=12, minor=4))
        lo.append(K.gem("lk_g", 0.09, loc=(0, -0.27, 1.7), rot=(90, 0, 45), color=PURP, h=1.4))
        lo += K.chain("lk_c1", (-1.0, -0.12, 2.25), (-0.22, -0.24, 1.6), link_r=0.13, wire=0.032, color=IRON, n=5)
        lo += K.chain("lk_c2", (1.0, -0.12, 2.25), (0.22, -0.24, 1.6), link_r=0.13, wire=0.032, color=IRON, n=5)
        lock = K.finish("Lock", lo, origin=(0, -0.16, 1.5))
        lock.parent = leaf
        lock.matrix_parent_inverse = leaf.matrix_world.inverted()
        out.append(lock)
    return out


def hooded_statue(p, rng, s=1.0, flame=True):
    """Robed hooded guardian holding a violet flame (boss gate / arena)."""
    out = [K.stone(p + "pd", (0.9, 0.9, 0.5), loc=(0, 0, 0.25), color=SLATE_LT, bevel=0.05),
           A.lathe(p + "rb", [(0.42, 0.5), (0.4, 0.8), (0.33, 1.6), (0.27, 2.2), (0.0, 2.25)], color=SLATE[1], seg=10),
           A.lathe(p + "hd", [(0.0, 2.0), (0.26, 2.08), (0.3, 2.3), (0.24, 2.6), (0.08, 2.78), (0.0, 2.8)],
                   color=SLATE[0], seg=10),
           A.sphere(p + "fc", 0.17, loc=(0, -0.12, 2.32), scale=(1, 0.6, 1.1), color=VOID, seg=8, rings=6)]
    for sx in (-1, 1):
        out.append(K.gem(p + f"ey{sx}", 0.03, loc=(sx * 0.06, -0.22, 2.36), rot=(90, 0, 45), color=TEAL, h=1.0))
    # folded arms / sleeves holding a bowl
    out.append(A.cyl(p + "sl", r=0.13, depth=0.6, loc=(0, -0.3, 1.55), rot=(0, 90, 0), color=SLATE[2], seg=8))
    out.append(A.lathe(p + "bw", [(0.05, 0), (0.1, 0.05), (0.22, 0.14), (0.24, 0.18), (0, 0.15)],
                       loc=(0, -0.42, 1.6), color=IRON_LT, seg=10))
    for i in range(3):
        out.append(K.prism(p + f"fold{i}", [(-0.05, 0.5), (0.05, 0.5), (0.02, 1.7), (-0.02, 1.7)], 0.05, axis="Y",
                           loc=(-0.2 + 0.2 * i, -0.38 + abs(i - 1) * 0.04, 0), color=SLATE_DK))
    if flame:
        out += pflame(p + "fl", loc=(0, -0.42, 1.72), s=1.0, seed=len(p))
    K.grp_place(out, (0, 0, 0), scale=s)
    return out


def boss_gate():
    rng = R(3101)
    objs = []
    depth = 1.4
    for sx in (-1, 1):
        cx = sx * 1.55
        objs.append(K.stone(f"bg_pl{sx}", (0.9, depth + 0.2, 0.5), loc=(cx, 0, 0.25), color=SLATE_LT, bevel=0.05))
        objs.append(K.stone(f"bg_sh{sx}", (0.8, depth, 4.2), loc=(cx, 0, 2.6), color=K.pick(rng, SLATE), bevel=0.05))
        objs.append(K.stone(f"bg_cp{sx}", (0.95, depth + 0.15, 0.35), loc=(cx, 0, 4.85), color=SLATE_LT, bevel=0.05))
        objs.append(K.gem(f"bg_fn{sx}", 0.3, loc=(cx, 0, 5.3), rot=(0, 0, 45), color=SLATE_LT, mat="M_Toon", h=2.0))
        for side in (-1, 1):
            objs += K.grp_place(gothic_diamond(f"bg_gd{sx}{side}", 0, 0, s=1.3, y=0, glow=PURP),
                                loc=(cx, side * (depth / 2 + 0.005), 2.4), rot=(0, 0, 0 if side < 0 else 180))
    objs += voussoirs("bg_v", 2.3, 3.2, depth, thick=0.42, R_=2.0, n=8, rng=rng, key_col=SLATE_LT)
    apex = max(z for _, z in arch_curve(2.3, 3.2, 2.0, 8))
    objs.append(K.gem("bg_key", 0.32, loc=(0, -depth / 2 - 0.05, apex + 0.25), rot=(90, 0, 45), color=PURP, h=1.5))
    # glowing sealed rune veil inside the arch
    veil = K.prism("bg_veil", arch_opening(2.3, 3.2, 2.0, 8), 0.04, axis="Y", color=PURP_DK, mat="M_Clear")
    objs.append(veil)
    objs.append(K.ring_strip("bg_sig", 0.55, 0.64, z=0, n=24, color=PURP, loc=(0, 0, 0)))
    K.grp_place([objs[-1]], loc=(0, -0.03, 1.9), rot=(90, 0, 0))
    objs.append(K.prism("bg_sigx", [(0, 0.9), (0.12, 0.12), (0.9, 0), (0.12, -0.12), (0, -0.9), (-0.12, -0.12),
                                    (-0.9, 0), (-0.12, 0.12)], 0.02, axis="Y", loc=(0, -0.04, 1.9), color=PURP_HOT, mat="M_Emit"))
    # hooded guardians flanking on the -Y side
    for sx in (-1, 1):
        objs += K.grp_place(hooded_statue(f"bg_st{sx}", rng, s=0.8), loc=(sx * 1.55, -depth / 2 - 0.55, 0))
    objs += K.candle("bg_c1", h=0.3, loc=(-0.85, -0.9, 0), seed=1)
    objs += K.candle("bg_c2", h=0.2, loc=(0.9, -0.95, 0), seed=2)
    return [K.finish("boss_gate", objs)]


# ---------------------------------------------------------------- stairs

def stairs_down():
    rng = R(4001)
    objs = []
    hx1, hy0, hy1 = 1.1, -1.4, 1.6
    for i, (x0, y0, x1, y1) in enumerate([(-2, -2, -1.3, 2), (1.3, -2, 2, 2), (-1.3, -2, 1.3, -1.4), (-1.3, 1.8, 1.3, 2)]):
        objs.append(A.box(f"sd_g{i}", (x1 - x0, y1 - y0, 0.2), loc=((x0 + x1) / 2, (y0 + y1) / 2, -0.17), color=GROUT))
        objs += K.flagstones(f"sd_f{i}", rng, (x0, y0, x1, y1), SLATE, gap=0.08, min_size=0.6, max_size=1.3, chamfer=0.22)
    for sx in (-1, 1):
        objs.append(K.stone(f"sd_pp{sx}", (0.22, 3.4, 0.6), loc=(sx * 1.2, 0.15, 0.3), color=K.pick(rng, SLATE), bevel=0.04))
        objs.append(K.stone(f"sd_pc{sx}", (0.3, 3.45, 0.1), loc=(sx * 1.2, 0.15, 0.64), color=SLATE_LT, bevel=0.03))
        objs += pilaster(f"sd_po{sx}", rng, sx * 1.25, -1.55, h=1.3)
        objs += K.candle(f"sd_cd{sx}", h=0.22, r=0.05, loc=(sx * 1.2, 0.6, 0.69), seed=sx + 4)
    objs.append(K.stone("sd_bp", (2.62, 0.22, 0.6), loc=(0, 1.7, 0.3), color=K.pick(rng, SLATE), bevel=0.04))
    objs.append(K.stone("sd_bc", (2.7, 0.3, 0.1), loc=(0, 1.7, 0.64), color=SLATE_LT, bevel=0.03))
    depth = 2.6
    for sx in (-1, 1):
        w = A.box(f"sd_w{sx}", (0.2, hy1 - hy0, depth), loc=(sx * (hx1 + 0.1), (hy0 + hy1) / 2, -depth / 2), color=SLATE_DK)
        A.gradient(w, VOID, SLATE[2])
        objs.append(w)
    bw = A.box("sd_wb", (2.4, 0.2, depth), loc=(0, hy1 + 0.1, -depth / 2), color=SLATE_DK)
    A.gradient(bw, VOID, SLATE[2])
    objs.append(bw)
    n, run, rise = 10, (hy1 - hy0) / 10, 0.24
    for i in range(n):
        top = -rise * (i + 1)
        y0 = hy0 + run * i
        t = i / (n - 1)
        objs.append(K.stone(f"sd_st{i}", (2.2, run + 0.02, 0.2), loc=(0, y0 + run / 2, top - 0.1),
                            color=K.mix(SLATE[1], VOID, t * 0.85), bevel=0.03))
        objs.append(A.box(f"sd_sr{i}", (2.18, run, depth + top - 0.18), loc=(0, y0 + run / 2, (top - 0.18 - depth) / 2),
                          color=K.mix(SLATE_DK, VOID, 0.4 + t * 0.6)))
    objs.append(A.box("sd_bot", (2.2, 0.6, 0.05), loc=(0, hy1 - 0.3, -depth + 0.03), color=VOID))
    objs.append(A.box("sd_glow", (2.0, 0.04, 0.5), loc=(0, hy1 - 0.02, -depth + 0.45), color=TEAL, mat="M_Emit"))
    A.gradient(objs[-1], TEAL, VOID)
    return [K.finish("stairs_down", objs)]


def stairs_up():
    rng = R(4101)
    objs = []
    n, y0, y1, ztop = 9, -1.6, 1.4, 2.25
    run, rise = (y1 - y0) / n, ztop / n
    for i in range(n):
        top = rise * (i + 1)
        objs.append(K.stone(f"su_st{i}", (2.36, run + 0.03, 0.18), loc=(0, y0 + run * (i + 0.5), top - 0.09),
                            color=K.pick(rng, SLATE, 0.05), bevel=0.03))
        objs.append(A.box(f"su_sr{i}", (2.3, run, top - 0.17), loc=(0, y0 + run * (i + 0.5), (top - 0.17) / 2), color=SLATE_DK))
    objs.append(K.stone("su_land", (2.4, 0.6, ztop), loc=(0, 1.7, ztop / 2), color=K.pick(rng, SLATE), bevel=0.03))
    for sx in (-1, 1):
        pts = [(y0 - 0.1, 0), (2.0, 0), (2.0, ztop + 0.7), (y1, ztop + 0.7), (y0 - 0.1, 0.7)]
        objs.append(K.prism(f"su_bw{sx}", pts, 0.34, axis="X", loc=(sx * 1.35, 0, 0), color=K.pick(rng, SLATE)))
        cap = [(y0 - 0.15, 0.62), (y1, ztop + 0.62), (2.02, ztop + 0.62), (2.02, ztop + 0.8), (y1, ztop + 0.8), (y0 - 0.15, 0.8)]
        objs.append(K.prism(f"su_bc{sx}", cap, 0.42, axis="X", loc=(sx * 1.35, 0, 0), color=SLATE_LT))
        objs += pilaster(f"su_np{sx}", rng, sx * 1.35, y0 - 0.1, h=1.1)
        objs += K.skull(f"su_sk{sx}", s=0.9, loc=(sx * 1.35, y0 - 0.1, 1.42), low=True)
    # gothic portal at the top landing
    portal = voussoirs("su_v", 2.3, ztop + 1.4, 0.5, thick=0.3, R_=1.9, n=6, rng=rng, key_col=SLATE_LT)
    K.grp_place(portal, loc=(0, 1.75, 0))
    objs += portal
    for sx in (-1, 1):
        objs.append(K.stone(f"su_pj{sx}", (0.3, 0.5, 1.4), loc=(sx * 1.3, 1.75, ztop + 0.7), color=K.pick(rng, SLATE), bevel=0.03))
    objs.append(K.prism("su_void", arch_opening(2.3, 1.4, 1.9, 6), 0.05, axis="Y", loc=(0, 1.98, ztop), color=VOID))
    objs.append(K.prism("su_glow", arch_opening(1.6, 0.9, 1.3, 5), 0.02, axis="Y", loc=(0, 1.94, ztop), color=TEAL_HOT,
                        mat="M_Emit"))
    A.gradient(objs[-1], TEAL, VOID)
    return [K.finish("stairs_up", objs)]


# ---------------------------------------------------------------- chest

def chest():
    W, D, H, LR = 1.1, 0.72, 0.55, 0.36
    body = [K.stone("cb_box", (W, D, H), loc=(0, 0, H / 2), color=WOOD, bevel=0.03)]
    for i in range(3):
        body.append(A.box(f"cb_gr{i}", (W - 0.06, D + 0.005, 0.015), loc=(0, 0, 0.14 + i * 0.14), color=WOOD_DK))
    for sx in (-1, 1):
        body.append(K.stone(f"cb_vb{sx}", (0.13, D + 0.05, H + 0.02), loc=(sx * 0.32, 0, H / 2), color=IRON, bevel=0.02))
        for sy in (-1, 1):
            body.append(K.stone(f"cb_cc{sx}{sy}", (0.17, 0.17, 0.17), loc=(sx * (W / 2 - 0.05), sy * (D / 2 - 0.05), 0.085),
                                color=IRON_LT, bevel=0.03))
            body.append(K.gem(f"cb_cg{sx}{sy}", 0.035, loc=(sx * (W / 2 - 0.05), sy * (D / 2 + 0.04), 0.085), rot=(90, 0, 45),
                              color=PURP, h=1.0))
    body.append(K.stone("cb_rim", (W + 0.04, D + 0.04, 0.08), loc=(0, 0, 0.04), color=IRON, bevel=0.02))
    body.append(K.stone("cb_rimt", (W + 0.04, D + 0.04, 0.07), loc=(0, 0, H - 0.035), color=IRON_LT, bevel=0.02))
    body.append(K.prism("cb_lp", [(-0.13, 0.16), (0.13, 0.16), (0.15, -0.05), (0, -0.2), (-0.15, -0.05)], 0.05, axis="Y",
                        loc=(0, -D / 2 - 0.025, H - 0.12), color=IRON_LT, bevel=0.01))
    body += K.skull("cb_sk", s=0.55, loc=(0, -D / 2 - 0.06, H - 0.22), low=True)
    body.append(K.prism("cb_kh", [(-0.02, 0.0), (0.02, 0.0), (0.012, -0.06), (-0.012, -0.06)], 0.02, axis="Y",
                        loc=(0, -D / 2 - 0.06, H - 0.24), color=VOID))
    box = K.finish("chest", body)
    n = 12
    arc = [(math.cos(math.pi * i / n) * LR, math.sin(math.pi * i / n) * LR * 0.85) for i in range(n + 1)]
    arc_o = [(math.cos(math.pi * i / n) * (LR + 0.03), math.sin(math.pi * i / n) * (LR * 0.85 + 0.03)) for i in range(n + 1)]
    band = arc_o + list(reversed(arc))
    lid = [K.prism("cl_body", arc, W - 0.02, axis="X", loc=(0, 0, H), color=WOOD)]
    for sx in (-1, 1):
        lid.append(K.prism(f"cl_b{sx}", band, 0.13, axis="X", loc=(sx * 0.32, 0, H), color=IRON))
        lid.append(K.prism(f"cl_e{sx}", band, 0.06, axis="X", loc=(sx * (W / 2 - 0.02), 0, H), color=IRON_LT))
        lid.append(K.gem(f"cl_g{sx}", 0.05, loc=(sx * 0.32, 0, H + LR * 0.85 + 0.05), color=PURP))
    lid.append(K.gem("cl_top", 0.07, loc=(0, -0.1, H + LR * 0.85 + 0.02), rot=(60, 0, 45), color=PURP, h=1.2))
    lidobj = K.finish("Lid", lid, origin=(0, LR, H))
    return [box, lidobj]


# ---------------------------------------------------------------- lore stone

def lore_stone():
    rng = R(5001)
    outline = [(-0.5, 0.0), (0.5, 0.0), (0.5, 1.45)] + \
              [(math.cos(a) * 0.5, 1.45 + math.sin(a) * 0.42) for a in [math.pi * i / 10 for i in range(1, 10)]] + \
              [(-0.5, 1.45)]
    objs = [K.stone("ls_b0", (1.4, 1.0, 0.22), loc=(0, 0, 0.11), color=SLATE_DK, bevel=0.05),
            K.stone("ls_b1", (1.15, 0.6, 0.18), loc=(0, 0, 0.31), color=SLATE_LT, bevel=0.04),
            K.prism("ls_t", outline, 0.3, axis="Y", loc=(0, 0, 0.4), color=SLATE[3], bevel=0.04)]
    rim = [(x * 0.84, z * 0.9 + 0.08) for (x, z) in outline]
    for sy in (-1, 1):
        objs.append(K.prism(f"ls_in{sy}", rim, 0.02, axis="Y", loc=(0, sy * 0.155, 0.4), color=SLATE_DK))
        # glowing cross-diamond + rune lines (teal soul light)
        objs += K.grp_place(gothic_diamond(f"ls_gd{sy}", 0, 0, s=0.55, y=0, glow=TEAL, rim=SLATE_LT),
                            loc=(0, sy * 0.17, 1.6), rot=(0, 0, 0 if sy < 0 else 180))
        for row in range(4):
            z = 0.62 + row * 0.17
            for ci in range(3):
                wv = rng.uniform(0.08, 0.17)
                objs.append(K.prism(f"ls_r{sy}{row}{ci}", [(-wv / 2, -0.02), (wv / 2, -0.02), (wv / 2, 0.02), (-wv / 2, 0.02)],
                                    0.02, axis="Y", loc=(-0.22 + 0.22 * ci, sy * 0.172, z), color=TEAL, mat="M_Emit"))
    objs += K.candle("ls_c1", h=0.28, loc=(-0.48, -0.35, 0.22), seed=3)
    objs += K.candle("ls_c2", h=0.18, loc=(0.5, -0.32, 0.22), seed=5)
    w = cobweb("ls_web", rng, r=0.4, spokes=5, rings=3)
    K.grp_place([w], loc=(0.5, -0.16, 1.5), rot=(0, 90, 0))
    objs.append(w)
    return [K.finish("lore_stone", objs)]


# ---------------------------------------------------------------- trap

TRAP_GRID = [(-0.84 + 0.56 * i, -0.84 + 0.56 * j) for i in range(4) for j in range(4)]


def trap():
    objs = [K.stone("tr_fr", (2.7, 2.7, 0.06), loc=(0, 0, 0.0), color=IRON, bevel=0.03),
            A.box("tr_pl", (2.4, 2.4, 0.06), loc=(0, 0, 0.01), color=SLATE_DK)]
    for i in range(5):
        for axis in (0, 1):
            off = -1.0 + 0.5 * i
            sz = (0.05, 2.36, 0.02) if axis == 0 else (2.36, 0.05, 0.02)
            loc = (off + 0.25 * 0, 0, 0.045) if axis == 0 else (0, off, 0.045)
            if i < 4:
                objs.append(A.box(f"tr_bar{i}{axis}", sz, loc=(loc[0] + 0.12 if axis == 0 else 0, loc[1] + 0.12 if axis else 0,
                                                               0.045), color=IRON_LT))
    for i, (x, y) in enumerate(TRAP_GRID):
        objs.append(K.ngon_disc(f"tr_h{i}", 0.08, z=0.042, n=6, loc=(x, y, 0), color=VOID))
    for k in range(4):
        sk = K.skull(f"tr_sk{k}", s=0.6, loc=(0, -1.27, 0.02), low=True)
        K.rotz(sk, 90 * k)
        objs += sk
    plate = K.finish("trap", objs)
    sp = [A.box("sp_base", (2.3, 2.3, 0.04), loc=(0, 0, -0.03), color=IRON)]
    for i, (x, y) in enumerate(TRAP_GRID):
        sp.append(A.cone(f"sp_c{i}", r=0.075, depth=0.5, loc=(x, y, 0.25), color=IRON_LT, seg=5, smooth=False))
        sp.append(A.cone(f"sp_t{i}", r=0.028, depth=0.1, loc=(x, y, 0.45), color=BONE, seg=5, smooth=False))
    spikes = K.finish("Spikes", sp)
    spikes.location = (0, 0, -0.5)
    return [plate, spikes]


# ---------------------------------------------------------------- spring

def spring():
    rng = R(6001)
    objs = [K.stone("sp_b0", (2.6, 2.6, 0.3), loc=(0, 0, 0.15), color=SLATE_DK, bevel=0.06),
            A.lathe("sp_basin", [(1.15, 0.3), (1.2, 0.4), (1.1, 0.5), (1.15, 0.85), (1.25, 0.92), (1.25, 1.0),
                                 (1.05, 1.0), (1.0, 0.6), (0.0, 0.6)], color=SLATE[3], seg=8),
            K.ring_strip("sp_trim", 1.06, 1.26, z=1.002, n=8, color=SLATE_LT, mat="M_Toon")]
    K.rotz(objs[1:], 22.5)
    objs.append(K.ngon_disc("sp_glow", 1.0, z=0.65, n=16, color=TEAL, mat="M_Emit"))
    objs.append(K.ngon_disc("sp_water", 1.03, z=0.9, n=16, color=GHOST, mat="M_Clear"))
    for i in range(8):
        a = i * math.pi / 4 + math.pi / 8
        objs += K.grp_place(gothic_diamond(f"sp_gd{i}", 0, 0, s=0.32, y=0, glow=TEAL), loc=(math.cos(a) * 1.17,
                            math.sin(a) * 1.17, 0.72), rot=(0, 0, math.degrees(a) + 90))
    # central angel-less obelisk with quatrefoil and floating soul wisps
    objs.append(K.stone("sp_ob", (0.36, 0.36, 1.4), loc=(0, 0, 1.3), color=SLATE_LT, bevel=0.04, taper=0.3))
    objs.append(K.gem("sp_cr", 0.22, loc=(0, 0, 2.25), color=TEAL_HOT, h=1.6, sides=6))
    objs.append(K.ring_strip("sp_halo", 0.32, 0.38, z=0, n=16, color=TEAL, thick=0.03, loc=(0, 0, 2.22)))
    for i in range(5):
        a = rng.uniform(0, 6.28)
        d = rng.uniform(0.4, 0.95)
        wisp = A.sphere(f"sp_w{i}", rng.uniform(0.07, 0.11), loc=(math.cos(a) * d, math.sin(a) * d, rng.uniform(1.1, 1.8)),
                        scale=(1, 1, 1.6), color=TEAL_HOT, mat="M_Emit", seg=8, rings=5)
        objs.append(wisp)
    return [K.finish("spring", objs)]


# ---------------------------------------------------------------- warp

def warp():
    rng = R(7001)
    objs = [A.lathe("wp_d0", [(1.7, 0), (1.7, 0.14), (1.45, 0.16), (1.42, 0.25), (0, 0.25)], color=SLATE_DK, seg=8),
            K.ring_strip("wp_trim", 1.38, 1.46, z=0.252, n=8, color=IRON_LT, mat="M_Toon")]
    K.rotz(objs, 22.5)
    objs.append(K.ngon_disc("wp_top", 1.36, z=0.253, n=32, color=SLATE[0]))
    objs.append(K.ring_strip("wp_r1", 1.1, 1.18, z=0.26, n=32, color=PURP))
    objs.append(K.ring_strip("wp_r2", 0.6, 0.65, z=0.26, n=24, color=PURP))
    tri = [(math.cos(math.pi / 2 + 2 * math.pi * i / 3) * 1.08, math.sin(math.pi / 2 + 2 * math.pi * i / 3) * 1.08) for i in range(3)]
    for k, rot in enumerate((0, 180)):
        for i in range(3):
            a, b = tri[i], tri[(i + 1) % 3]
            mx, my = (a[0] + b[0]) / 2, (a[1] + b[1]) / 2
            L = math.hypot(b[0] - a[0], b[1] - a[1])
            bar = A.box(f"wp_t{k}{i}", (L, 0.045, 0.01), loc=(mx, my, 0.262), rot=(0, 0, math.degrees(math.atan2(b[1] - a[1], b[0] - a[0]))),
                        color=PURP_HOT, mat="M_Emit")
            K.rotz([bar], rot)
            objs.append(bar)
    for i in range(12):
        a = i * math.pi / 6
        objs.append(K.prism(f"wp_g{i}", [(0, 0.1), (0.04, 0), (0, -0.1), (-0.04, 0)], 0.012, axis="Z",
                            loc=(math.cos(a) * 0.88, math.sin(a) * 0.88, 0.262), rot=(0, 0, math.degrees(a)), color=PURP,
                            mat="M_Emit"))
    for i in range(4):
        a = math.pi / 4 + i * math.pi / 2
        x, y = math.cos(a) * 1.5, math.sin(a) * 1.5
        objs.append(A.cyl(f"wp_cs{i}", r=0.06, depth=0.9, loc=(x, y, 0.55), color=IRON, seg=6))
        objs.append(A.lathe(f"wp_cb{i}", [(0.03, 0), (0.1, 0.03), (0.12, 0.06), (0, 0.05)], loc=(x, y, 1.0), color=IRON_LT, seg=8))
        objs += K.candle(f"wp_cd{i}", h=0.2, r=0.05, loc=(x, y, 1.05), seed=i)
    objs.append(K.ring_strip("wp_fl", 1.2, 1.26, z=0.0, n=32, color=PURP, thick=0.03, loc=(0, 0, 0.9)))
    for i in range(3):
        a = 2 * math.pi * i / 3
        objs.append(K.gem(f"wp_sh{i}", 0.08, loc=(math.cos(a) * 0.5, math.sin(a) * 0.5, 1.2 + 0.15 * i), color=PURP_HOT))
    return [K.finish("warp", objs)]


# ---------------------------------------------------------------- torch

def torch():
    """Skull-faced stone post with an iron brazier of violet soul-fire (ref sconce)."""
    objs = [K.stone("to_b", (0.75, 0.75, 0.2), loc=(0, 0, 0.1), color=SLATE_DK, bevel=0.05),
            K.stone("to_s", (0.42, 0.42, 1.2), loc=(0, 0, 0.8), color=SLATE[1], bevel=0.04, taper=0.12)]
    for k in range(4):
        part = gothic_diamond(f"to_gd{k}", 0, 0.6, s=0.45, y=-0.215, glow=PURP)
        objs += K.rotz(part, 90 * k)
    objs += K.skull("to_sk", s=1.25, loc=(0, -0.2, 1.08), low=True)
    objs.append(K.stone("to_c", (0.56, 0.56, 0.12), loc=(0, 0, 1.46), color=SLATE_LT, bevel=0.03))
    objs.append(A.lathe("to_bowl", [(0.1, 0), (0.12, 0.08), (0.4, 0.28), (0.46, 0.4), (0.42, 0.42), (0.33, 0.34),
                                   (0.0, 0.3)], loc=(0, 0, 1.52), color=IRON, seg=10))
    for k in range(4):
        a = math.pi / 4 + k * math.pi / 2
        objs.append(K.gem(f"to_sp{k}", 0.08, loc=(math.cos(a) * 0.44, math.sin(a) * 0.44, 1.94), color=IRON_LT, mat="M_Toon",
                          h=2.0))
        objs.append(K.gem(f"to_pg{k}", 0.05, loc=(math.cos(a) * 0.36, math.sin(a) * 0.36, 1.72), rot=(0, 90, math.degrees(a)),
                          color=PURP, h=1.2))
    objs += pflame("to_fl", loc=(0, 0, 1.84), s=1.8, seed=3)
    mesh = K.finish("torch", objs)
    anchor = K.empty("LightAnchor", loc=(0, 0, 2.35))
    return [mesh, anchor]


# ---------------------------------------------------------------- decor

def coffin_outline(L=1.9, wh=0.62, wf=0.42):
    """Classic hexagonal coffin outline in XY (head toward +Y)."""
    return [(0, -L / 2), (wf / 2, -L / 2), (wh / 2, L * 0.18), (wf * 0.42, L / 2), (-wf * 0.42, L / 2), (-wh / 2, L * 0.18),
            (-wf / 2, -L / 2)][1:] + [(-wf / 2, -L / 2)]


def decor_1():
    """Coffin with its lid shoved aside, purple glow leaking out."""
    rng = R(9101)
    pts = [(0.21, -0.95), (0.31, 0.34), (0.18, 0.95), (-0.18, 0.95), (-0.31, 0.34), (-0.21, -0.95)]
    objs = [K.prism("cf_body", pts, 0.5, axis="Z", loc=(0, 0, 0.25), color=WOOD, bevel=0.02)]
    inner = [(x * 0.82, y * 0.92) for (x, y) in pts]
    objs.append(K.prism("cf_in", inner, 0.04, axis="Z", loc=(0, 0, 0.49), color=PURP_DK, mat="M_Emit"))
    for zz in (0.1, 0.4):
        objs.append(K.prism(f"cf_band{zz}", [(x * 1.03, y * 1.01) for (x, y) in pts], 0.05, axis="Z", loc=(0, 0, zz),
                            color=IRON))
    lid = [K.prism("cf_lid", [(x * 1.05, y * 1.03) for (x, y) in pts], 0.08, axis="Z", color=WOOD_DK, bevel=0.02),
           K.prism("cf_cx", [(-0.04, -0.5), (0.04, -0.5), (0.04, 0.5), (-0.04, 0.5)], 0.03, axis="Z", loc=(0, 0.1, 0.05),
                   color=IRON_LT),
           K.prism("cf_cy", [(-0.22, -0.04), (0.22, -0.04), (0.22, 0.04), (-0.22, 0.04)], 0.03, axis="Z", loc=(0, 0.35, 0.05),
                   color=IRON_LT)]
    K.grp_place(lid, loc=(0.3, -0.12, 0.6), rot=(0, -14, 18))
    objs += lid
    objs += K.skull("cf_sk", s=0.7, loc=(0, 0.6, 0.47), rot=(-20, 0, 0), low=True)
    objs += K.candle("cf_c1", h=0.32, loc=(-0.55, 0.6, 0), seed=1)
    objs += K.candle("cf_c2", h=0.2, loc=(-0.48, 0.38, 0), seed=2)
    return [K.finish("decor_1", objs)]


def decor_2():
    """Bone pile with skulls."""
    rng = R(9201)
    objs = [K.boulder("bp_m", 0.5, loc=(0, 0, 0.0), scale=(1.1, 0.9, 0.38), color=BONE_DK, seed=3, flat_bottom=0.0)]
    for i in range(14):
        a = rng.uniform(0, 360)
        ln = rng.uniform(0.35, 0.55)
        b = [A.cyl(f"bp_s{i}", r=0.03, depth=ln, rot=(0, 90, 0), color=K.jit(rng, BONE, 0.05), seg=6, smooth=False)]
        for sx in (-1, 1):
            b.append(A.sphere(f"bp_k{i}{sx}", 0.05, loc=(sx * ln / 2, 0, 0), scale=(1, 1.4, 1), color=BONE, seg=6, rings=4))
        d = rng.uniform(0, 0.45)
        aa = rng.uniform(0, 6.28)
        K.grp_place(b, loc=(math.cos(aa) * d, math.sin(aa) * d * 0.8, 0.08 + (0.45 - d) * 0.35), rot=(rng.uniform(-25, 25), 0, a))
        objs += b
    for i, (x, y, z, s, rz) in enumerate(((0.0, -0.15, 0.22, 1.4, 0), (-0.35, 0.1, 0.12, 1.1, 30), (0.38, 0.05, 0.1, 1.15, -35),
                                          (0.1, 0.3, 0.3, 1.0, 160))):
        objs += K.skull(f"bp_sk{i}", s=s, loc=(x, y, z), rot=(rng.uniform(-10, 10), 0, rz), low=i > 0)
    return [K.finish("decor_2", objs)]


def decor_3():
    """Candle cluster on a puddle of wax, on a little stone step."""
    rng = R(9301)
    objs = [K.stone("cc_st", (0.9, 0.6, 0.2), loc=(0, 0.1, 0.1), color=SLATE_LT, bevel=0.04),
            K.poly_slab("cc_wax", [(math.cos(a) * 0.55 * rng.uniform(0.8, 1.1), math.sin(a) * 0.4 * rng.uniform(0.8, 1.1))
                                   for a in [2 * math.pi * i / 10 for i in range(10)]], top=0.02, thick=0.02, color=WAX,
                        bevel=0.0, loc=(0, -0.25, 0))]
    specs = [(-0.2, 0.1, 0.2, 0.5, 0.07), (0.05, 0.15, 0.2, 0.36, 0.06), (0.25, 0.05, 0.2, 0.28, 0.055),
             (-0.3, -0.3, 0.0, 0.3, 0.06), (0.1, -0.35, 0.0, 0.2, 0.05), (0.35, -0.25, 0.0, 0.14, 0.045)]
    for i, (x, y, z, h, r) in enumerate(specs):
        objs += K.candle(f"cc{i}", h=h, r=r, loc=(x, y, z), seed=i + 10,
                         flame_col=(PURP, PURP_HOT, "#ffffff") if i % 3 else (TEAL, TEAL_HOT, "#ffffff"))
    return [K.finish("decor_3", objs)]


def decor_4():
    """Leaning gravestones (rounded + cross)."""
    rng = R(9401)
    objs = [K.boulder("gs_m", 0.6, loc=(0, 0, 0), scale=(1.4, 0.8, 0.22), color="#3a3046", seed=4, flat_bottom=0.0)]
    head = [(-0.28, 0), (0.28, 0), (0.28, 0.6)] + [(math.cos(a) * 0.28, 0.6 + math.sin(a) * 0.26)
                                                   for a in [math.pi * i / 8 for i in range(1, 8)]] + [(-0.28, 0.6)]
    g1 = [K.prism("gs_1", head, 0.14, axis="Y", color=SLATE[3], bevel=0.02),
          K.prism("gs_1c", [(-0.03, 0.3), (0.03, 0.3), (0.03, 0.48), (0.1, 0.48), (0.1, 0.54), (0.03, 0.54), (0.03, 0.66),
                            (-0.03, 0.66), (-0.03, 0.54), (-0.1, 0.54), (-0.1, 0.48), (-0.03, 0.48)], 0.02, axis="Y",
                  loc=(0, -0.075, 0), color=SLATE_DK)]
    K.grp_place(g1, loc=(-0.35, 0.05, 0.02), rot=(-8, 6, 10))
    cross = [(-0.05, 0), (0.05, 0), (0.05, 0.62), (0.2, 0.62), (0.2, 0.72), (0.05, 0.72), (0.05, 0.9), (-0.05, 0.9),
             (-0.05, 0.72), (-0.2, 0.72), (-0.2, 0.62), (-0.05, 0.62)]
    g2 = [K.prism("gs_2", cross, 0.1, axis="Y", color=SLATE_LT, bevel=0.015)]
    K.grp_place(g2, loc=(0.4, 0.15, 0.02), rot=(6, -12, -15))
    objs += g1 + g2
    w = cobweb("gs_web", rng, r=0.3, spokes=5, rings=3)
    K.grp_place([w], loc=(0.45, 0.06, 0.66), rot=(0, 0, -15))
    objs.append(w)
    objs += K.candle("gs_c", h=0.18, loc=(0.0, -0.3, 0.05), seed=7)
    return [K.finish("decor_4", objs)]


def decor_5():
    """Jack-o'-lanterns (from the battle background) with ghostly candle glow."""
    rng = R(9501)
    objs = []
    for i, (x, y, s, rz) in enumerate(((0, 0, 1.0, 0), (0.48, 0.22, 0.7, -25))):
        body = A.sphere(f"pk{i}", 0.3 * s, loc=(x, y, 0.25 * s), scale=(1.15, 1.15, 0.85), color=PUMPKIN, seg=16, rings=10)
        K.A.deform(body, lambda v: v * (1 + 0.08 * abs(math.sin(4 * math.atan2(v.y, v.x)))))
        K.A.gradient(body, PUMPKIN_DK, PUMPKIN)
        objs.append(body)
        objs.append(A.cyl(f"pk{i}st", r=0.04 * s, r2=0.025 * s, depth=0.14 * s, loc=(x, y, 0.5 * s), rot=(12, 0, 0),
                          color="#5a7a2a", seg=6))
        face = [K.prism(f"pk{i}e{sx}", [(-0.06, 0), (0.06, 0), (0, 0.08)], 0.04, axis="Y", loc=(sx * 0.1, 0, 0.3),
                        color="#ffd060", mat="M_Emit") for sx in (-1, 1)]
        face.append(K.prism(f"pk{i}m", [(-0.15, 0.02), (-0.08, -0.03), (-0.04, 0.0), (0.0, -0.04), (0.04, 0.0), (0.08, -0.03),
                                        (0.15, 0.02), (0.08, -0.09), (-0.08, -0.09)], 0.04, axis="Y", loc=(0, 0, 0.18),
                            color="#ffb030", mat="M_Emit"))
        K.grp_place(face, loc=(0, -0.33, 0), scale=1.0)
        K.grp_place(face, scale=s)
        K.grp_place(face, loc=(x, y, 0), rot=(0, 0, rz))
        objs += face
    objs += K.candle("pk_c", h=0.15, loc=(-0.38, -0.2, 0), seed=4)
    return [K.finish("decor_5", objs)]


def decor_6():
    """Soul urn: stone urn on a plinth with a teal ghost-flame and orbiting wisp."""
    objs = [K.stone("su_pl", (0.6, 0.6, 0.35), loc=(0, 0, 0.175), color=SLATE_LT, bevel=0.04),
            A.lathe("su_urn", [(0.12, 0.35), (0.2, 0.42), (0.3, 0.62), (0.28, 0.82), (0.16, 0.95), (0.2, 1.0), (0.0, 0.98)],
                    color=SLATE[3], seg=12),
            A.torus("su_rg", R=0.29, r=0.03, loc=(0, 0, 0.68), color=IRON_LT, seg=16, minor=4)]
    for k in range(4):
        objs += K.rotz(gothic_diamond(f"su_gd{k}", 0, 0.18, s=0.22, y=-0.305, glow=TEAL), 90 * k)
    objs += pflame("su_fl", loc=(0, 0, 0.97), s=1.1, seed=8, teal=True)
    objs.append(A.sphere("su_w", 0.08, loc=(0.32, -0.1, 1.25), scale=(1, 1, 1.5), color=GHOST, mat="M_Clear", seg=8, rings=5))
    return [K.finish("decor_6", objs)]


# ---------------------------------------------------------------- overlays

def overlay_1():
    """Big cobwebs spanning the top corners of a wall's -Y face + a hanging strand with a small spider."""
    rng = R(10101)
    objs = []
    w1 = cobweb("o1_w1", rng, r=1.3, spokes=7, rings=5)
    K.grp_place([w1], loc=(-1.98, -2.05, 4.45), rot=(0, 180, 0))   # opens toward +x / -z
    w2 = cobweb("o1_w2", rng, r=0.9, spokes=6, rings=4)
    K.grp_place([w2], loc=(1.98, -2.05, 4.45), rot=(0, 90, 0))
    objs += [w1, w2]
    # diagonal sagging web sheet strands across the face top
    for i in range(4):
        x0 = -1.2 + i * 0.7
        objs.append(A.tube(f"o1_s{i}", [(x0, -2.06, 4.45), (x0 + 0.35, -2.1, 4.1 - 0.1 * (i % 2)), (x0 + 0.7, -2.06, 4.45)],
                           radius=0.008, color=WEB, mat="M_Clear", seg=4))
    objs.append(A.tube("o1_drop", [(0.6, -2.12, 4.45), (0.6, -2.12, 3.3)], radius=0.006, color=WEB, mat="M_Clear", seg=4))
    sp = [A.sphere("o1_spb", 0.07, loc=(0.6, -2.12, 3.22), scale=(1, 1, 1.3), color="#2a2030", seg=8, rings=5),
          A.sphere("o1_sph", 0.045, loc=(0.6, -2.12, 3.32), color="#2a2030", seg=6, rings=4)]
    for k in range(4):
        for sx in (-1, 1):
            sp.append(A.tube(f"o1_l{k}{sx}", [(0.6, -2.12, 3.25 - 0.03 * k), (0.6 + sx * 0.1, -2.12, 3.3 - 0.03 * k),
                                              (0.6 + sx * 0.15, -2.12, 3.18 - 0.03 * k)], radius=0.008, color="#2a2030", seg=4))
    sp.append(K.gem("o1_eye", 0.015, loc=(0.6, -2.17, 3.33), rot=(90, 0, 0), color=PURP, h=1.0))
    objs += sp
    return [K.finish("overlay_1", objs)]


def banner(p, rng, w, h, col, col2, loc, emblem=True):
    """Tattered hanging cloth banner (in XZ plane, top edge at z=0)."""
    pts = [(-w / 2, 0), (w / 2, 0)]
    n = 7
    for i in range(n + 1):
        x = w / 2 - w * i / n
        z = -h + (rng.uniform(0, 0.28) * h if i % 2 else rng.uniform(-0.05, 0.08) * h)
        pts.append((x, z))
    cloth = K.prism(p + "c", pts, 0.03, axis="Y", color=col)
    K.grad3(cloth, K.mix(col, "#2a1830", 0.4), col, K.mix(col, "#ffffff", 0.1), mid=0.6)
    out = [cloth]
    out.append(K.prism(p + "s", [(-w * 0.15, -0.1), (w * 0.15, -0.1), (w * 0.15, -h * 0.75), (0, -h * 0.85), (-w * 0.15, -h * 0.75)],
                       0.035, axis="Y", color=col2))
    if emblem:
        out.append(K.prism(p + "e", [(0, -h * 0.25), (w * 0.2, -h * 0.4), (0, -h * 0.58), (-w * 0.2, -h * 0.4)], 0.04, axis="Y",
                           color="#c89a6a"))
        out.append(K.prism(p + "ei", [(0, -h * 0.32), (w * 0.09, -h * 0.4), (0, -h * 0.5), (-w * 0.09, -h * 0.4)], 0.045,
                           axis="Y", color=col2))
    K.grp_place(out, loc)
    return out


def overlay_2():
    """Iron rod with three tattered violet banners and cobwebs (ref props sheet)."""
    rng = R(10201)
    objs = [A.cyl("o2_rod", r=0.05, depth=3.6, loc=(0, -2.2, 4.0), rot=(0, 90, 0), color=IRON, seg=8)]
    for sx in (-1, 1):
        objs.append(K.gem(f"o2_f{sx}", 0.13, loc=(sx * 1.85, -2.2, 4.0), rot=(0, 90, 45), color=IRON_LT, mat="M_Toon", h=1.4))
        objs.append(A.box(f"o2_br{sx}", (0.08, 0.25, 0.08), loc=(sx * 1.5, -2.08, 4.0), color=IRON))
    objs += banner("o2_b0", rng, 1.0, 2.4, CLOTH, CLOTH_DK, (0, -2.2, 3.95))
    objs += banner("o2_b1", rng, 0.75, 1.8, CLOTH_LT, CLOTH, (-1.05, -2.18, 3.95), emblem=False)
    objs += banner("o2_b2", rng, 0.75, 1.6, CLOTH_LT, CLOTH, (1.05, -2.18, 3.95), emblem=False)
    for i, (x, rz) in enumerate(((-0.6, 0), (0.55, 90))):
        w = cobweb(f"o2_w{i}", rng, r=0.55, spokes=5, rings=3)
        K.grp_place([w], loc=(x, -2.26, 3.95), rot=(0, 180 + rz, 0))
        objs.append(w)
    return [K.finish("overlay_2", objs)]


# ---------------------------------------------------------------- foe marker

def foe_marker():
    rng = R(11001)
    objs = [K.ring_strip("fm_r0", 1.0, 1.1, z=0.02, n=32, color=PURP_DK),
            K.ring_strip("fm_r1", 0.72, 0.77, z=0.02, n=32, color=PURP)]
    tri = [(math.cos(math.pi / 2 + 2 * math.pi * i / 3) * 0.72, math.sin(math.pi / 2 + 2 * math.pi * i / 3) * 0.72) for i in range(3)]
    for k in (0, 60):
        for i in range(3):
            a, b = tri[i], tri[(i + 1) % 3]
            L = math.hypot(b[0] - a[0], b[1] - a[1])
            bar = A.box(f"fm_t{k}{i}", (L, 0.04, 0.01), loc=((a[0] + b[0]) / 2, (a[1] + b[1]) / 2, 0.025),
                        rot=(0, 0, math.degrees(math.atan2(b[1] - a[1], b[0] - a[0]))), color=PURP_HOT, mat="M_Emit")
            K.rotz([bar], k)
            objs.append(bar)
    sk = K.skull("fm_sk", s=2.2, loc=(0, 0, 1.55), low=False)
    objs += sk
    for sx in (-1, 1):
        objs.append(K.gem(f"fm_ey{sx}", 0.05, loc=(sx * 0.13, -0.33, 1.88), rot=(90, 0, 45), color=PURP_HOT, h=1.0))
    for i in range(3):
        a = 2 * math.pi * i / 3 + 0.4
        objs += pflame(f"fm_wf{i}", loc=(math.cos(a) * 0.85, math.sin(a) * 0.85, 1.2 + 0.25 * i), s=0.6, seed=i, teal=True,
                       tongues=1, sparks=0)
    for i in range(5):
        a = 2 * math.pi * i / 5
        objs += K.candle(f"fm_c{i}", h=0.18 + 0.05 * (i % 2), loc=(math.cos(a) * 1.25, math.sin(a) * 1.25, 0), seed=i)
    return [K.finish("foe_marker", objs)]


# ---------------------------------------------------------------- build

PIECES = [
    ("floor_a", floor_a), ("floor_b", floor_b), ("floor_c", floor_c),
    ("wall_a", wall_a), ("wall_b", wall_b), ("wall_c", wall_c),
    ("door", lambda: build_door(False)), ("door_locked", lambda: build_door(True)),
    ("stairs_down", stairs_down), ("stairs_up", stairs_up), ("chest", chest), ("lore_stone", lore_stone),
    ("trap", trap), ("spring", spring), ("warp", warp), ("torch", torch),
    ("decor_1", decor_1), ("decor_2", decor_2), ("decor_3", decor_3), ("decor_4", decor_4), ("decor_5", decor_5),
    ("decor_6", decor_6), ("overlay_1", overlay_1), ("overlay_2", overlay_2), ("boss_gate", boss_gate),
    ("foe_marker", foe_marker),
]

LAYOUT = [
    "W W boss_gate W W".split(),
    "W lore_stone . torch W".split(),
    "W . chest warp W".split(),
    "W trap spring stairs_down W".split(),
    "W W door_locked W W".split(),
]
EXTRAS = [
    ("decor_1", (1.25, 2.3), 90), ("decor_2", (3.3, 2.6), 0), ("decor_3", (2.65, 3.3), 0), ("decor_4", (1.3, 1.65), 20),
    ("decor_5", (3.3, 1.35), 0), ("decor_6", (1.6, 3.35), 0), ("foe_marker", (2.0, 3.0), 0),
    ("overlay_1", (1, 4), 0), ("overlay_2", (3, 4), 0), ("overlay_2", (0, 2), 90), ("overlay_1", (4, 2), -90),
]

def main():
    from _pipeline import run
    return run(TS, PIECES, layout=LAYOUT, extras=EXTRAS, world="#16121e")


if __name__ == "__main__":
    main()
