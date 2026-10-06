"""ember_caverns dungeon kit — 홍염의 사막: sun-temple ruins sunk in lava.

Builds every kit piece (README "던전 키트 조각") into
Assets/_Game/Resources/Art/Environment/ember_caverns/<piece>.fbx, then a labelled contact sheet
and a 5x5 mock layout preview. Arena lives in arena.py.
Run: blender -b --factory-startup -P Blender/environment/ember_caverns/kit.py
"""
import math
import os
import random
import sys

sys.path.append(os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
import _kit_common_b as K  # noqa: E402

A = K.A
import bpy  # noqa: E402
from mathutils import Vector  # noqa: E402

TS = "ember_caverns"

# ---------------------------------------------------------------- palette (sRGB)
SAND = ["#e8954f", "#d9813f", "#f0a862", "#cf7638"]
SAND_LT = "#f6bd7a"
SAND_DK = "#a8582a"
SAND_CARVE = "#9a4b22"
BAS = ["#4e3142", "#5c3b47", "#432a3a", "#583646"]
BAS_DK = "#2e1c28"
GROUT = "#4a2218"
LAVA = "#ff5a0a"
LAVA_HOT = "#ffa21a"
LAVA_CORE = "#ffe27a"
LAVA_DEEP = "#d8300a"
GOLD = "#f5c445"
GOLD_DK = "#c98a22"
GOLD_LT = "#ffe08a"
OBS = "#2b1934"
OBS_HI = "#6a3f86"
WOOD = "#7a4224"
WOOD_DK = "#55291a"
CLAY = "#c8703c"
GREEN = "#7c9a3c"
GREEN_DK = "#55702a"
VOID = "#120708"


def R(seed):
    return random.Random(seed)


# ---------------------------------------------------------------- motif helpers

def diamond_carving(p, cx, cz, s=1.0, y=-2.0, outer=SAND_CARVE, inner=None, core=GOLD):
    """Nested diamond + chevron carving on a -Y facing surface at plane y (ref wall pilasters)."""
    inner = inner or SAND_LT
    out = [K.prism(p + "d0", [(0, 0.42 * s), (0.24 * s, 0), (0, -0.42 * s), (-0.24 * s, 0)], 0.05, axis="Y",
                   loc=(cx, y - 0.005, cz + 0.08 * s), color=outer),
           K.prism(p + "d1", [(0, 0.28 * s), (0.15 * s, 0), (0, -0.28 * s), (-0.15 * s, 0)], 0.05, axis="Y",
                   loc=(cx, y - 0.02, cz + 0.08 * s), color=inner),
           K.prism(p + "d2", [(0, 0.12 * s), (0.07 * s, 0), (0, -0.12 * s), (-0.07 * s, 0)], 0.05, axis="Y",
                   loc=(cx, y - 0.04, cz + 0.08 * s), color=core),
           K.prism(p + "v", [(-0.24 * s, 0), (0, -0.22 * s), (0.24 * s, 0), (0.24 * s, -0.08 * s), (0, -0.3 * s),
                             (-0.24 * s, -0.08 * s)], 0.05, axis="Y", loc=(cx, y - 0.005, cz - 0.38 * s), color=outer)]
    return out


def zigzag(p, x0, x1, cz, h=0.22, y=-2.0, col=SAND_CARVE, n=None, col2=None):
    """Row of alternating triangles (the ref frieze pattern) on a -Y surface."""
    n = n or max(2, int((x1 - x0) / (h * 1.1)))
    w = (x1 - x0) / n
    out = []
    for i in range(n):
        x = x0 + w * (i + 0.5)
        out.append(K.prism(f"{p}u{i}", [(-w * 0.46, -h / 2), (w * 0.46, -h / 2), (0, h / 2)], 0.05, axis="Y",
                           loc=(x, y - 0.01, cz), color=col))
        if col2 and i < n - 1:
            out.append(K.prism(f"{p}d{i}", [(-w * 0.3, h / 2), (w * 0.3, h / 2), (0, -h * 0.2)], 0.05, axis="Y",
                               loc=(x + w / 2, y - 0.01, cz), color=col2))
    return out


def sun(p, r, loc, rot=(0, 0, 0), rays=10, emit=True, axis="Y"):
    return K.sun_emblem(p, r=r, rays=rays, loc=loc, rot=rot, ray_col=GOLD, disc_col=GOLD_LT if not emit else GOLD,
                        core_col=LAVA_HOT if emit else GOLD_DK, core_mat="M_Emit" if emit else "M_Toon", axis=axis)


def lava_vein(p, pts, w=0.06, col=LAVA_HOT):
    """Glowing crack polyline (flattened tube)."""
    o = A.tube(p, pts, radius=w, color=col, mat="M_Emit", seg=4)
    return [o]


def ember_coals(p, rng, n, r, z, loc=(0, 0, 0)):
    out = []
    for i in range(n):
        a = rng.uniform(0, 6.28)
        d = rng.uniform(0, r)
        hot = rng.random() < 0.45
        out.append(K.boulder(f"{p}{i}", rng.uniform(0.05, 0.09), loc=(loc[0] + math.cos(a) * d, loc[1] + math.sin(a) * d,
                                                                         loc[2] + z), scale=(1, 1, 0.7),
                             color=LAVA if hot else BAS_DK, mat="M_Emit" if hot else "M_Toon", seed=rng.randint(0, 999),
                             subdiv=0))
    return out


# ---------------------------------------------------------------- floors

def floor_grout(p, col=GROUT):
    return [A.box(p + "grout", (4.0, 4.0, 0.2), loc=(0, 0, -0.17), color=col)]


def floor_a():
    rng = R(101)
    objs = floor_grout("fa")
    objs += K.flagstones("fa_s", rng, (-2, -2, 2, 2), SAND, gap=0.08, min_size=0.75, max_size=1.45, chamfer=0.26,
                         col_fn=lambda r, x, y: K.pick(r, BAS) if r.random() < 0.12 else K.pick(r, SAND, 0.07))
    objs += K.scatter_pebbles("fa_p", rng, 22, (-1.95, -1.95, 1.95, 1.95), -0.07, SAND + BAS[:2], r=(0.04, 0.08))
    return [K.finish("floor_a", objs)]


def floor_b():
    """Temple paving with a gold sun inlay in the centre slab and a glowing seam patch."""
    rng = R(202)
    objs = floor_grout("fb")
    centre = (-0.8, -0.8, 0.8, 0.8)

    def skip(cx, cy, rect):
        x0, y0, x1, y1 = rect
        return not (x1 <= centre[0] or x0 >= centre[2] or y1 <= centre[1] or y0 >= centre[3])

    for (x0, y0, x1, y1) in [(-2, -2, 2, -0.8), (-2, 0.8, 2, 2), (-2, -0.8, -0.8, 0.8), (0.8, -0.8, 2, 0.8)]:
        objs += K.flagstones("fb_s", rng, (x0, y0, x1, y1), SAND, gap=0.08, min_size=0.6, max_size=1.3, chamfer=0.22)
    # centre slab + inlay
    objs.append(K.poly_slab("fb_c", K.circle_pts(8, 0.82, math.pi / 8, 0.92, 0.92), top=0.0, thick=0.22, color=SAND_LT,
                            bevel=0.04))
    objs.append(K.ngon_disc("fb_ci", 0.62, z=0.004, n=8, rot=(0, 0, 22.5), color=SAND_CARVE))
    objs += sun("fb_sun", 0.5, loc=(0, 0, 0.0), rays=8, emit=False, axis="Z")
    # glowing seams in one quadrant (lava plate below stone level, above grout)
    objs.append(A.box("fb_lava", (1.3, 1.1, 0.02), loc=(1.15, 1.2, -0.06), color=LAVA, mat="M_Emit"))
    objs += K.scatter_pebbles("fb_p", rng, 14, (-1.95, -1.95, 1.95, 1.95), -0.07, BAS, r=(0.04, 0.07))
    return [K.finish("floor_b", objs)]


def floor_c():
    """Cracked basalt crust with lava glowing in the seams + a few sandstone ruin slabs."""
    rng = R(303)
    objs = floor_grout("fc", BAS_DK)
    objs.append(A.box("fc_lava", (3.7, 3.7, 0.02), loc=(0, 0, -0.06), color=LAVA, mat="M_Emit"))
    objs.append(A.box("fc_hot", (2.0, 0.5, 0.02), loc=(-0.3, 0.2, -0.05), rot=(0, 0, 35), color=LAVA_HOT, mat="M_Emit"))
    objs += K.flagstones("fc_s", rng, (-2, -2, 2, 2), BAS, gap=0.13, min_size=0.5, max_size=1.6, chamfer=0.38,
                         tilt=0.02, rotj=0.16,
                         col_fn=lambda r, x, y: K.pick(r, SAND, 0.06) if r.random() < 0.18 else K.pick(r, BAS, 0.08))
    return [K.finish("floor_c", objs)]


# ---------------------------------------------------------------- walls

def wall_core(p, col="#2c1a1e", mat="M_Toon", s=3.86):
    return [A.box(p + "core", (s, s, 4.42), loc=(0, 0, 2.21), color=col, mat=mat)]


def wall_top(p, rng, cols, z=4.5, gap=0.08):
    objs = [A.box(p + "topg", (3.98, 3.98, 0.12), loc=(0, 0, z - 0.1), color=GROUT)]
    objs += K.flagstones(p + "top", rng, (-2, -2, 2, 2), cols, gap=gap, min_size=1.2, max_size=2.1, top=z,
                         thick=0.25, chamfer=0.22)
    return objs


def wall_a():
    """Sandstone ashlar with carved corner pilasters and zigzag frieze."""
    rng = R(1101)
    objs = wall_core("wa")

    def side(k):
        r = R(1110 + k)
        o = []
        # plinth + cornice
        o.append(K.stone(f"wa{k}pl", (2.7, 0.4, 0.42), loc=(0, -1.8, 0.21), color=SAND_DK, bevel=0.05, cull="+Y"))
        o.append(K.stone(f"wa{k}co", (2.7, 0.4, 0.34), loc=(0, -1.8, 4.08), color=K.jit(r, SAND[0]), bevel=0.05,
                         cull="+Y"))
        o += K.ashlar_face(f"wa{k}a", r, -1.32, 1.32, 0.42, 3.22, SAND, y_face=-1.96, course=(0.85, 1.4),
                           length=(1.2, 2.0), gap=0.06, bevel=0.06)
        # frieze band with zigzag
        o.append(K.stone(f"wa{k}fr", (2.64, 0.3, 0.6), loc=(0, -1.8, 3.55), color=SAND_LT, bevel=0.04, cull="+Y"))
        o += zigzag(f"wa{k}z", -1.25, 1.25, 3.55, h=0.32, y=-1.95, col=SAND_CARVE, n=7)
        # corner pilaster at (+x,-y) + carvings on both -Y pilasters of this face
        o.append(K.stone(f"wa{k}pb", (0.72, 0.72, 0.5), loc=(1.64, -1.64, 0.25), color=SAND_DK, bevel=0.05))
        o.append(A.box(f"wa{k}ps", (0.6, 0.6, 3.5), loc=(1.64, -1.64, 2.25), color=K.jit(r, SAND[2])))
        o.append(K.stone(f"wa{k}pc", (0.72, 0.72, 0.36), loc=(1.64, -1.64, 4.18), color=SAND_LT, bevel=0.05))
        o.append(K.stone(f"wa{k}pk", (0.52, 0.52, 0.16), loc=(1.64, -1.64, 4.44), color=GOLD_DK, bevel=0.03))
        o.append(K.gem(f"wa{k}pg", 0.3, loc=(1.64, -1.64, 4.52), rot=(0, 0, 45), color=GOLD, mat="M_Toon", h=1.0))
        for cx in (-1.64, 1.64):
            o += diamond_carving(f"wa{k}dc{cx}", cx, 2.3, s=1.0, y=-1.94)
        return o

    objs += K.four_sides(side)
    objs += wall_top("wa", rng, SAND)
    return [K.finish("wall_a", objs)]


def wall_b():
    """Basalt rubble lower half glowing with lava seams, sandstone upper half with a gold sun medallion."""
    rng = R(1201)
    objs = wall_core("wb", col=LAVA_DEEP, mat="M_Emit", s=3.8)

    def side(k):
        r = R(1210 + k)
        o = []
        # basalt rubble courses (big rough blocks) z 0..2.2
        o += K.ashlar_face(f"wb{k}b", r, -1.98, 1.98, 0.0, 2.2, BAS, y_face=-2.0, depth=0.5, course=(0.7, 1.1),
                           length=(1.0, 1.6), gap=0.09, relief=0.07, bevel=0.1, rough=0.06)
        # sandstone upper
        o.append(A.box(f"wb{k}ub", (3.9, 0.3, 2.3), loc=(0, -1.8, 3.35), color=GROUT))
        o += K.ashlar_face(f"wb{k}s", r, -1.98, 1.98, 2.2, 4.12, SAND, y_face=-1.98, course=(0.9, 1.0),
                           length=(1.5, 2.4), gap=0.06, bevel=0.06, rough=0.015)
        o.append(K.stone(f"wb{k}co", (3.96, 0.42, 0.38), loc=(0, -1.79, 4.31), color=SAND_DK, bevel=0.06, cull="+Y"))
        # recessed medallion panel
        o.append(K.stone(f"wb{k}mp", (1.5, 0.1, 1.5), loc=(0, -2.0 + 0.05 - 0.04, 3.15), rot=(0, 45, 0),
                         color=SAND_CARVE, bevel=0.04, cull="+Y"))
        o += sun(f"wb{k}sun", 0.62, loc=(0, -2.02, 3.15), rays=8)
        return o

    objs += K.four_sides(side)
    objs += wall_top("wb", rng, SAND)
    # broken-off block lying on top
    objs.append(K.stone("wb_tb", (0.9, 0.7, 0.45), loc=(0.8, -0.6, 4.62), rot=(0, 6, 20), color=SAND_DK, bevel=0.0,
                        rough=0.03))
    return [K.finish("wall_b", objs)]


def wall_c():
    """Raw basalt cave rock in big strata, lava glowing through the fissures, obsidian on top."""
    rng = R(1301)
    objs = wall_core("wc", col=LAVA_DEEP, mat="M_Emit", s=3.7)
    layers = [(0.0, 1.5), (1.5, 3.05), (3.05, 4.5)]
    for li, (z0, z1) in enumerate(layers):
        for ix in range(2):
            for iy in range(2):
                cx, cy = -1.0 + 2.0 * ix, -1.0 + 2.0 * iy
                h = z1 - z0
                o = K.stone(f"wc{li}{ix}{iy}", (1.9, 1.9, h - 0.08), loc=(cx, cy, z0 + h / 2), color=K.pick(rng, BAS, 0.1),
                            bevel=0.18, rough=0.1, seed=rng.randint(0, 9999), freq=1.1)
                objs.append(o)
    # sandstone ruin block embedded in one corner of each face (temple remains)
    def side(k):
        r = R(1310 + k)
        x = r.choice((-1, 1)) * 1.1
        z = r.uniform(0.9, 2.6)
        o = [K.stone(f"wc{k}rb", (1.0, 0.4, 0.62), loc=(x, -1.82, z), color=K.pick(r, SAND), bevel=0.06, rough=0.02)]
        o += zigzag(f"wc{k}rz", x - 0.4, x + 0.4, z, h=0.22, y=-2.0, n=4)
        # hot lava vein trickling down the seam
        vx = -x * 0.05
        o += lava_vein(f"wc{k}lv", [(vx, -2.0, 3.0), (vx + 0.12, -2.0, 2.4), (vx - 0.05, -2.0, 1.9), (vx + 0.08, -2.0, 1.2)],
                       w=0.05)
        return o

    objs += K.four_sides(side)
    # obsidian shards + lava pocket on top
    for i in range(5):
        a = rng.uniform(0, 6.28)
        d = rng.uniform(0.2, 1.2)
        objs.append(K.shard(f"wc_sh{i}", r=rng.uniform(0.12, 0.22), h=rng.uniform(0.4, 0.9),
                            loc=(math.cos(a) * d, math.sin(a) * d, 4.4), rot=(rng.uniform(-15, 15), rng.uniform(-15, 15), 0),
                            color=OBS if i % 2 else OBS_HI, seed=i))
    objs.append(K.ngon_disc("wc_pool", 0.42, z=4.52, n=10, loc=(-0.9, 0.8, 0), color=LAVA_HOT, mat="M_Emit"))
    mesh = K.finish("wall_c", objs)
    clamp_bounds(mesh)
    return [mesh]


def clamp_bounds(o, lo=(-2, -2, 0), hi=(2, 2, 5.2)):
    for v in o.data.vertices:
        v.co.x = min(max(v.co.x, lo[0]), hi[0])
        v.co.y = min(max(v.co.y, lo[1]), hi[1])
        v.co.z = min(max(v.co.z, lo[2]), hi[2])
    o.data.update()


# ---------------------------------------------------------------- door / gates

def door_frame(p, rng, open_w=1.15, h_open=3.35, depth=1.0, top=4.5):
    objs = []
    for sx in (-1, 1):
        cx = sx * (open_w + (2.0 - open_w) / 2)
        w = 2.0 - open_w
        objs.append(K.stone(f"{p}pl{sx}", (w, depth + 0.1, 0.42), loc=(cx, 0, 0.21), color=SAND_DK, bevel=0.05))
        z = 0.42
        i = 0
        while z < h_open - 0.05:
            hh = min(rng.uniform(1.25, 1.6), h_open - z)
            objs.append(K.stone(f"{p}j{sx}{i}", (w - 0.08, depth, hh - 0.04), loc=(cx, 0, z + hh / 2),
                                color=K.pick(rng, SAND), bevel=0.05, rough=0.01))
            z += hh
            i += 1
        for side in (-1, 1):
            objs += K.grp_place(diamond_carving(f"{p}dc{sx}{side}", 0, 0, s=0.9, y=0),
                                loc=(cx, side * depth / 2, 1.9), rot=(0, 0, 0 if side < 0 else 180))
    # lintel
    objs.append(K.stone(p + "li", (4.0, depth + 0.06, 0.62), loc=(0, 0, h_open + 0.31), color=SAND_LT, bevel=0.06))
    objs.append(K.stone(p + "co", (3.96, depth + 0.2, 0.22), loc=(0, 0, h_open + 0.73), color=SAND_DK, bevel=0.05))
    objs.append(K.stone(p + "cr", (2.6, depth - 0.1, top - (h_open + 0.84)), loc=(0, 0, (top + h_open + 0.84) / 2),
                        color=K.pick(rng, SAND), bevel=0.05))
    for side in (-1, 1):
        objs += K.grp_place(zigzag(f"{p}z{side}", -1.9, 1.9, 0, h=0.3, y=0, n=9, col=SAND_CARVE),
                            loc=(0, side * (depth / 2 + 0.03), h_open + 0.31), rot=(0, 0, 0 if side < 0 else 180))
    for side in (-1, 1):
        objs += K.grp_place(sun(f"{p}sun{side}", 0.42, loc=(0, 0, 0), rays=10), loc=(0, side * (depth / 2 - 0.03), top - 0.12),
                            rot=(0, 0, 0 if side < 0 else 180))
    objs.append(A.box(p + "th", (open_w * 2, depth, 0.05), loc=(0, 0, 0.025), color=SAND_DK))
    return objs


def door_leaf(p, rng, open_w=1.15, h=3.3):
    w = open_w * 2 - 0.06
    x0 = -open_w + 0.03
    objs = []
    n = 5
    pw = w / n
    for i in range(n):
        hh = h - (0.0 if i in (0, n - 1) else 0.0)
        objs.append(K.stone(f"{p}pk{i}", (pw - 0.025, 0.14, hh), loc=(x0 + pw * (i + 0.5), 0, 0.04 + hh / 2),
                            color=K.jit(rng, WOOD if i % 2 else WOOD_DK, 0.06), bevel=0.02))
    for zi, z in enumerate((0.45, 1.65, 2.85)):
        objs.append(K.stone(f"{p}bd{zi}", (w + 0.02, 0.2, 0.2), loc=(0, 0, z), color=GOLD_DK, bevel=0.025))
        for xi in range(4):
            x = x0 + 0.15 + (w - 0.3) * xi / 3
            for sy in (-1, 1):
                objs.append(K.gem(f"{p}rv{zi}{xi}{sy}", 0.045, loc=(x, sy * 0.105, z), rot=(90, 0, 45), color=GOLD_LT,
                                  mat="M_Toon", h=0.8))
    for sy in (-1, 1):
        objs += K.grp_place(sun(f"{p}sun{sy}", 0.36, loc=(0, 0, 0), rays=10, emit=False), loc=(0.0, sy * 0.1, 2.25),
                            rot=(0, 0, 0 if sy < 0 else 180))
        objs.append(A.torus(f"{p}rg{sy}", R=0.12, r=0.025, loc=(0.75, sy * 0.13, 1.3), rot=(90, 0, 0), color=GOLD, seg=10,
                            minor=4))
        objs.append(K.gem(f"{p}rgb{sy}", 0.06, loc=(0.75, sy * 0.1, 1.42), rot=(90, 0, 45), color=GOLD_DK, mat="M_Toon"))
    return objs


def build_door(locked):
    rng = R(2001 if not locked else 2002)
    name = "door_locked" if locked else "door"
    frame = K.finish(name, door_frame("df", rng))
    leaf = K.finish("Door", door_leaf("dl", rng), origin=(-1.12, 0, 0))
    out = [frame, leaf]
    if locked:
        lo = []
        lo.append(K.stone("lk_b", (0.46, 0.2, 0.5), loc=(0, -0.19, 1.5), color=GOLD, bevel=0.06))
        lo.append(A.torus("lk_sh", R=0.17, r=0.045, loc=(0, -0.19, 1.78), rot=(90, 0, 0), color=GOLD_DK, seg=12, minor=4))
        lo.append(K.prism("lk_kh", [(-0.05, 0.05), (0.05, 0.05), (0.03, -0.12), (-0.03, -0.12)], 0.04, axis="Y",
                          loc=(0, -0.30, 1.45), color=VOID))
        lo.append(K.gem("lk_g", 0.08, loc=(0, -0.30, 1.63), rot=(90, 0, 45), color=LAVA_HOT))
        lo += K.chain("lk_c1", (-1.0, -0.12, 2.7), (-0.2, -0.27, 1.62), link_r=0.13, wire=0.032, color=BAS[1], n=5)
        lo += K.chain("lk_c2", (1.0, -0.12, 2.7), (0.2, -0.27, 1.62), link_r=0.13, wire=0.032, color=BAS[1], n=5)
        lock = K.finish("Lock", lo, origin=(0, -0.19, 1.5))
        lock.parent = leaf
        lock.matrix_parent_inverse = leaf.matrix_world.inverted()
        out.append(lock)
    return out


def boss_gate():
    rng = R(2101)
    objs = []
    ow, depth, h_open = 1.2, 1.5, 3.9
    for sx in (-1, 1):
        cx = sx * 1.6
        objs.append(K.stone(f"bg_pl{sx}", (0.8, depth + 0.2, 0.5), loc=(cx, 0, 0.25), color=SAND_DK, bevel=0.06))
        objs.append(K.stone(f"bg_sh{sx}", (0.72, depth, h_open - 0.5), loc=(cx, 0, 0.5 + (h_open - 0.5) / 2), color=SAND[0],
                            bevel=0.06, taper=0.05))
        for side in (-1, 1):
            objs += K.grp_place(diamond_carving(f"bg_dc{sx}{side}", 0, 0, s=1.1, y=0), loc=(cx, side * depth / 2, 1.5),
                                rot=(0, 0, 0 if side < 0 else 180))
            objs += K.grp_place(diamond_carving(f"bg_dd{sx}{side}", 0, 0, s=0.8, y=0), loc=(cx, side * depth / 2, 3.0),
                                rot=(0, 0, 0 if side < 0 else 180))
        # flame bowls on top of the pylons
        objs.append(A.lathe(f"bg_bw{sx}", [(0.12, 0), (0.18, 0.1), (0.38, 0.28), (0.42, 0.36), (0.3, 0.33), (0, 0.3)],
                            loc=(sx * 1.7, 0, 5.5), color=GOLD, seg=12))
        objs += K.flame(f"bg_fl{sx}", loc=(sx * 1.7, 0, 5.78), s=1.5, seed=sx + 5)
    # stepped lintels (temple pyramid crown)
    objs.append(K.stone("bg_l0", (4.0, depth + 0.1, 0.7), loc=(0, 0, h_open + 0.35), color=SAND_LT, bevel=0.07))
    objs.append(K.stone("bg_l1", (3.7, depth - 0.1, 0.5), loc=(0, 0, h_open + 0.95), color=K.pick(rng, SAND), bevel=0.06))
    objs.append(K.stone("bg_l2", (2.9, depth - 0.3, 0.5), loc=(0, 0, h_open + 1.45), color=SAND_DK, bevel=0.06))
    objs.append(K.stone("bg_pc", (0.8, 0.8, 0.4), loc=(1.7, 0, 5.3), color=SAND_DK, bevel=0.05))
    objs.append(K.stone("bg_pc2", (0.8, 0.8, 0.4), loc=(-1.7, 0, 5.3), color=SAND_DK, bevel=0.05))
    for side in (-1, 1):
        objs += K.grp_place(zigzag(f"bg_z{side}", -1.9, 1.9, 0, h=0.38, y=0, n=11, col=SAND_CARVE, col2=GOLD_DK),
                            loc=(0, side * (depth / 2 + 0.05), h_open + 0.35), rot=(0, 0, 0 if side < 0 else 180))
        objs.append(K.stone(f"bg_mb{side}", (1.25, 0.3, 1.25), loc=(0, side * (depth / 2 - 0.05), 5.3), rot=(0, 45, 0),
                            color=SAND_CARVE, bevel=0.05))
        objs += K.grp_place(sun(f"bg_sun{side}", 0.85, loc=(0, 0, 0), rays=12), loc=(0, side * (depth / 2 + 0.1), 5.3),
                            rot=(0, 0, 0 if side < 0 else 180))
    # glowing sun-seal rune across the threshold
    objs.append(K.ring_strip("bg_seal", 0.7, 0.8, z=0.012, n=24, color=LAVA_HOT))
    objs.append(K.prism("bg_sealst", K.star_pts(8, 0.6, 0.25), 0.01, axis="Z", loc=(0, 0, 0.01), color=LAVA, mat="M_Emit"))
    objs.append(A.box("bg_th", (2.4, depth, 0.06), loc=(0, 0, 0.0), color=SAND_DK))
    return [K.finish("boss_gate", objs)]


# ---------------------------------------------------------------- stairs

def stairs_down():
    rng = R(3001)
    objs = []
    hx0, hx1, hy0, hy1 = -1.1, 1.1, -1.4, 1.6
    regions = [(-2, -2, -1.3, 2), (1.3, -2, 2, 2), (-1.3, -2, 1.3, -1.4), (-1.3, 1.8, 1.3, 2)]
    for i, (x0, y0, x1, y1) in enumerate(regions):
        objs.append(A.box(f"sd_g{i}", (x1 - x0, y1 - y0, 0.2), loc=((x0 + x1) / 2, (y0 + y1) / 2, -0.17), color=GROUT))
        objs += K.flagstones(f"sd_f{i}", rng, (x0, y0, x1, y1), SAND, gap=0.08, min_size=0.6, max_size=1.3, chamfer=0.22)
    # parapet around the shaft (open toward -Y)
    for sx in (-1, 1):
        objs.append(K.stone(f"sd_pp{sx}", (0.22, 3.4, 0.55), loc=(sx * 1.2, 0.15, 0.27), color=K.pick(rng, SAND), bevel=0.05))
        objs.append(K.stone(f"sd_pc{sx}", (0.3, 3.45, 0.1), loc=(sx * 1.2, 0.15, 0.58), color=SAND_LT, bevel=0.03))
        objs.append(K.stone(f"sd_po{sx}", (0.42, 0.42, 1.05), loc=(sx * 1.25, -1.55, 0.52), color=SAND_DK, bevel=0.05))
        objs.append(K.stone(f"sd_pk{sx}", (0.5, 0.5, 0.14), loc=(sx * 1.25, -1.55, 1.1), color=SAND_LT, bevel=0.04))
        objs.append(K.gem(f"sd_gm{sx}", 0.13, loc=(sx * 1.25, -1.55, 1.36), color=GOLD, mat="M_Toon", h=1.4))
        objs += diamond_carving(f"sd_dc{sx}", sx * 1.25, 0.55, s=0.55, y=-1.77)
    objs.append(K.stone("sd_bp", (2.62, 0.22, 0.55), loc=(0, 1.7, 0.27), color=K.pick(rng, SAND), bevel=0.05))
    objs.append(K.stone("sd_bc", (2.7, 0.3, 0.1), loc=(0, 1.7, 0.58), color=SAND_LT, bevel=0.03))
    objs += zigzag("sd_z", -1.1, 1.1, 0.3, h=0.25, y=1.59, n=7)
    for o in objs[-7:]:
        o.rotation_euler.z = math.pi
        o.location.y = 1.58
    # shaft walls
    depth = 2.6
    for sx in (-1, 1):
        w = A.box(f"sd_w{sx}", (0.2, hy1 - hy0, depth), loc=(sx * (hx1 + 0.1), (hy0 + hy1) / 2, -depth / 2), color=SAND_DK)
        A.gradient(w, VOID, SAND_DK)
        objs.append(w)
    bw = A.box("sd_wb", (2.4, 0.2, depth), loc=(0, hy1 + 0.1, -depth / 2), color=SAND_DK)
    A.gradient(bw, VOID, SAND_DK)
    objs.append(bw)
    # steps going down toward +Y
    n = 10
    run = (hy1 - hy0) / n
    rise = 0.24
    for i in range(n):
        top = -rise * (i + 1)
        y0 = hy0 + run * i
        t = i / (n - 1)
        col = K.mix(SAND[1], VOID, t * 0.85)
        objs.append(K.stone(f"sd_st{i}", (2.2, run + 0.02, 0.2), loc=(0, y0 + run / 2, top - 0.1), color=col, bevel=0.03))
        objs.append(A.box(f"sd_sr{i}", (2.18, run, depth + top - 0.18), loc=(0, y0 + run / 2, (top - 0.18 - depth) / 2),
                          color=K.mix(SAND_DK, VOID, 0.4 + t * 0.6)))
    objs.append(A.box("sd_bot", (2.2, 0.6, 0.05), loc=(0, hy1 - 0.3, -depth + 0.03), color=VOID))
    objs.append(A.box("sd_glow", (2.0, 0.04, 0.12), loc=(0, hy1 - 0.02, -depth + 0.4), color=LAVA_DEEP, mat="M_Emit"))
    return [K.finish("stairs_down", objs)]


def stairs_up():
    rng = R(3101)
    objs = []
    n = 9
    y0, y1, ztop = -1.6, 1.4, 2.25
    run = (y1 - y0) / n
    rise = ztop / n
    for i in range(n):
        top = rise * (i + 1)
        objs.append(K.stone(f"su_st{i}", (2.36, run + 0.03, 0.18), loc=(0, y0 + run * (i + 0.5), top - 0.09),
                            color=K.pick(rng, SAND, 0.05), bevel=0.03))
        objs.append(A.box(f"su_sr{i}", (2.3, run, top - 0.17), loc=(0, y0 + run * (i + 0.5), (top - 0.17) / 2),
                          color=SAND_DK))
    objs.append(K.stone("su_land", (2.4, 0.6, ztop), loc=(0, 1.7, ztop / 2), color=K.pick(rng, SAND), bevel=0.03))
    # side balustrade walls (sloped)
    for sx in (-1, 1):
        pts = [(y0 - 0.1, 0), (2.0, 0), (2.0, ztop + 0.7), (y1, ztop + 0.7), (y0 - 0.1, 0.7)]
        objs.append(K.prism(f"su_bw{sx}", pts, 0.34, axis="X", loc=(sx * 1.35, 0, 0), color=K.pick(rng, SAND)))
        cap = [(y0 - 0.15, 0.62), (y1, ztop + 0.62), (2.02, ztop + 0.62), (2.02, ztop + 0.8), (y1, ztop + 0.8),
               (y0 - 0.15, 0.8)]
        objs.append(K.prism(f"su_bc{sx}", cap, 0.42, axis="X", loc=(sx * 1.35, 0, 0), color=SAND_LT))
        objs.append(K.stone(f"su_np{sx}", (0.5, 0.5, 1.0), loc=(sx * 1.35, y0 - 0.1, 0.5), color=SAND_DK, bevel=0.05))
        objs += sun(f"su_ns{sx}", 0.2, loc=(sx * 1.35, y0 - 0.36, 0.62), rays=8)
        # portal pillars at the top
        objs.append(K.stone(f"su_pp{sx}", (0.45, 0.45, 2.1), loc=(sx * 1.35, 1.75, ztop + 1.05), color=K.pick(rng, SAND),
                            bevel=0.05))
        objs += diamond_carving(f"su_dc{sx}", sx * 1.35, ztop + 1.05, s=0.6, y=1.52)
    objs.append(K.stone("su_li", (3.2, 0.6, 0.45), loc=(0, 1.75, ztop + 2.3), color=SAND_LT, bevel=0.05))
    objs += sun("su_ls", 0.38, loc=(0, 1.43, ztop + 2.3), rays=10)
    objs.append(A.box("su_void", (2.3, 0.05, 2.1), loc=(0, 1.98, ztop + 1.05), color=VOID))
    # warm light spilling from above
    objs.append(A.box("su_glow", (2.2, 0.03, 0.08), loc=(0, 1.95, ztop + 2.02), color=LAVA_HOT, mat="M_Emit"))
    return [K.finish("stairs_up", objs)]


# ---------------------------------------------------------------- chest

def chest():
    rng = R(4001)
    W, D, H, LR = 1.1, 0.72, 0.55, 0.36
    body = [K.stone("cb_box", (W, D, H), loc=(0, 0, H / 2), color=WOOD, bevel=0.03)]
    for i in range(3):
        body.append(A.box(f"cb_gr{i}", (W - 0.06, D + 0.005, 0.015), loc=(0, 0, 0.14 + i * 0.14), color=WOOD_DK))
    for sx in (-1, 1):
        body.append(K.stone(f"cb_vb{sx}", (0.16, D + 0.05, H + 0.02), loc=(sx * 0.3, 0, H / 2), color=CLAY, bevel=0.02))
        body += zigzag(f"cb_vz{sx}", sx * 0.3 - 0.07, sx * 0.3 + 0.07, 0.3, h=0.08, y=-D / 2 - 0.02, n=1, col=SAND_CARVE)
        for sy in (-1, 1):
            body.append(K.stone(f"cb_cc{sx}{sy}", (0.16, 0.16, 0.16), loc=(sx * (W / 2 - 0.05), sy * (D / 2 - 0.05), 0.08),
                                color=GOLD, bevel=0.03))
    body.append(K.stone("cb_rim", (W + 0.04, D + 0.04, 0.09), loc=(0, 0, 0.045), color=CLAY, bevel=0.02))
    body.append(K.stone("cb_rimt", (W + 0.04, D + 0.04, 0.07), loc=(0, 0, H - 0.035), color=GOLD_DK, bevel=0.02))
    # diamond lock plate
    body.append(K.prism("cb_lp", [(0, 0.2), (0.16, 0), (0, -0.2), (-0.16, 0)], 0.06, axis="Y", loc=(0, -D / 2 - 0.03, H - 0.08),
                        color=GOLD, bevel=0.01))
    body.append(K.gem("cb_lg", 0.06, loc=(0, -D / 2 - 0.07, H - 0.08), rot=(90, 0, 45), color=LAVA_HOT))
    box = K.finish("chest", body)
    # lid: half cylinder along X, hinge at back top edge
    n = 12
    arc = [(math.cos(math.pi * i / n) * LR, math.sin(math.pi * i / n) * LR * 0.85) for i in range(n + 1)]
    lid = [K.prism("cl_body", arc, W - 0.02, axis="X", loc=(0, 0, H), color=WOOD, smooth=False)]
    arc_o = [(math.cos(math.pi * i / n) * (LR + 0.03), math.sin(math.pi * i / n) * (LR * 0.85 + 0.03)) for i in range(n + 1)]
    band = arc_o + list(reversed(arc))
    for sx in (-1, 1):
        lid.append(K.prism(f"cl_b{sx}", band, 0.16, axis="X", loc=(sx * 0.3, 0, H), color=CLAY))
        lid.append(K.prism(f"cl_e{sx}", band, 0.06, axis="X", loc=(sx * (W / 2 - 0.02), 0, H), color=GOLD_DK))
        lid.append(K.gem(f"cl_st{sx}", 0.05, loc=(sx * 0.3, 0, H + LR * 0.85 + 0.05), color=GOLD, mat="M_Toon"))
    lid.append(K.prism("cl_hasp", [(-0.06, 0.0), (0.06, 0.0), (0.05, -0.14), (-0.05, -0.14)], 0.04, axis="Y",
                       loc=(0, -LR - 0.02, H + 0.12), color=GOLD))
    lidobj = K.finish("Lid", lid, origin=(0, LR, H))
    return [box, lidobj]


# ---------------------------------------------------------------- lore stone

def lore_stone():
    rng = R(5001)
    objs = [K.stone("ls_b0", (1.5, 1.1, 0.22), loc=(0, 0, 0.11), color=SAND_DK, bevel=0.05),
            K.stone("ls_b1", (1.15, 0.8, 0.2), loc=(0, 0, 0.32), color=K.pick(rng, SAND), bevel=0.05),
            K.stone("ls_t", (0.9, 0.36, 1.9), loc=(0, 0, 1.37), color=SAND[0], bevel=0.06, taper=0.12),
            K.prism("ls_pd", [(-0.5, 0), (0.5, 0), (0, 0.35)], 0.42, axis="Y", loc=(0, 0, 2.3), color=SAND_LT, bevel=0.03)]
    objs += sun("ls_sun", 0.2, loc=(0, -0.22, 2.42), rays=8)
    objs += K.grp_place(sun("ls_sunb", 0.2, loc=(0, 0, 0), rays=8), loc=(0, 0.22, 2.42), rot=(0, 0, 180))
    # glowing runes, front and back
    for side in (-1, 1):
        for row in range(5):
            z = 0.75 + row * 0.27
            xs = [-0.22, 0.0, 0.22]
            for ci, x in enumerate(xs):
                kind = (row * 3 + ci + (side > 0)) % 4
                y = side * (0.185 - 0.012 * (z - 0.4))
                if kind == 0:
                    shape = [(-0.07, -0.02), (0.07, -0.02), (0.07, 0.02), (-0.07, 0.02)]
                elif kind == 1:
                    shape = [(0, 0.08), (0.05, 0), (0, -0.08), (-0.05, 0)]
                elif kind == 2:
                    shape = [(-0.06, -0.07), (0.06, 0.07), (0.035, 0.08), (-0.075, -0.05)]
                else:
                    shape = [(-0.02, -0.08), (0.02, -0.08), (0.02, 0.08), (-0.02, 0.08)]
                g = K.prism(f"ls_r{side}{row}{ci}", shape, 0.03, axis="Y", loc=(x * (1 - 0.06 * row), y, z),
                            color=LAVA_HOT, mat="M_Emit")
                objs.append(g)
    for i in range(6):
        a = i * 1.05 + rng.uniform(-0.3, 0.3)
        objs.append(K.boulder(f"ls_r{i}", rng.uniform(0.1, 0.18), loc=(math.cos(a) * 0.85, math.sin(a) * 0.65, 0.05),
                              color=K.pick(rng, BAS), seed=i, subdiv=0, flat_bottom=-0.05))
    return [K.finish("lore_stone", objs)]


# ---------------------------------------------------------------- trap

TRAP_GRID = [(-0.84 + 0.56 * i, -0.84 + 0.56 * j) for i in range(4) for j in range(4)]


def trap():
    objs = [K.stone("tr_fr", (2.7, 2.7, 0.06), loc=(0, 0, 0.0), color=GOLD_DK, bevel=0.03),
            A.box("tr_pl", (2.4, 2.4, 0.06), loc=(0, 0, 0.01), color="#6e3a1e")]
    for i, (x, y) in enumerate(TRAP_GRID):
        objs.append(K.ngon_disc(f"tr_h{i}", 0.09, z=0.042, n=6, loc=(x, y, 0), color=VOID))
    for k in range(4):
        tri = K.prism(f"tr_w{k}", [(-0.16, 0), (0.16, 0), (0, 0.22)], 0.012, axis="Z", loc=(0, 0, 0.045), color=LAVA,
                      mat="M_Emit")
        K.grp_place([tri], loc=(0, -1.25, 0), rot=(0, 0, 0))
        K.rotz([tri], 90 * k)
        objs.append(tri)
    plate = K.finish("trap", objs)
    sp = [A.box("sp_base", (2.3, 2.3, 0.04), loc=(0, 0, -0.03), color=BAS_DK)]
    for i, (x, y) in enumerate(TRAP_GRID):
        sp.append(A.cone(f"sp_c{i}", r=0.085, depth=0.46, loc=(x, y, 0.23), color="#3a2a2e", seg=6, smooth=False))
        sp.append(A.cone(f"sp_t{i}", r=0.03, depth=0.12, loc=(x, y, 0.42), color=LAVA_HOT, mat="M_Emit", seg=6, smooth=False))
    spikes = K.finish("Spikes", sp)
    spikes.location = (0, 0, -0.5)
    return [plate, spikes]


# ---------------------------------------------------------------- spring

def spring():
    rng = R(6001)
    prof = [(1.45, 0.0), (1.52, 0.12), (1.42, 0.2), (1.36, 0.5), (1.5, 0.58), (1.52, 0.7), (1.3, 0.72), (1.24, 0.42),
            (0.0, 0.42)]
    objs = [A.lathe("sp_basin", prof, color=SAND[0], seg=24)]
    objs.append(K.ring_strip("sp_trim", 1.33, 1.53, z=0.721, n=24, color=GOLD, mat="M_Toon"))
    objs.append(K.ngon_disc("sp_glow", 1.25, z=0.47, n=24, color="#36e6c0", mat="M_Emit"))
    objs.append(K.ngon_disc("sp_water", 1.27, z=0.62, n=24, color="#6ff0e4", mat="M_Clear"))
    # sun inlays around the rim
    for i in range(6):
        a = i * math.pi / 3 + math.pi / 6
        objs += K.grp_place(sun(f"sp_s{i}", 0.16, loc=(0, 0, 0), rays=8, emit=False),
                            loc=(math.cos(a) * 1.48, math.sin(a) * 1.48, 0.38), rot=(0, 0, math.degrees(a) + 90))
    # central pillar with gold sun bowl spilling water
    objs.append(A.cyl("sp_col", r=0.17, depth=1.0, loc=(0, 0, 0.9), color=SAND_LT, seg=10))
    objs.append(A.lathe("sp_bowl", [(0.1, 0), (0.18, 0.05), (0.45, 0.2), (0.5, 0.26), (0.42, 0.25), (0.0, 0.2)],
                        loc=(0, 0, 1.38), color=GOLD, seg=16))
    for i in range(4):
        a = i * math.pi / 2 + math.pi / 4
        ca, sa = math.cos(a), math.sin(a)
        st = K.ribbon(f"sp_fall{i}", -0.95, 0.22, 6, lambda t: 0.22 - 0.06 * t,
                      y_fn=lambda t: -(0.5 + 0.5 * t ** 0.6), thick=0.05, color="#8ff5ea", mat="M_Clear")
        K.grp_place([st], loc=(0, 0, 1.38), rot=(0, 0, math.degrees(a) + 90))
        objs.append(st)
        objs.append(K.ring_strip(f"sp_spl{i}", 0.1, 0.2, z=0.625, n=10, color="#e8fffb", loc=(ca * 1.0, sa * 1.0, 0)))
    objs.append(K.ngon_disc("sp_bw", 0.43, z=0.235, n=16, loc=(0, 0, 1.38), color="#b6fff6", mat="M_Emit"))
    for i in range(7):
        a = rng.uniform(0, 6.28)
        d = rng.uniform(0.4, 1.1)
        objs.append(K.gem(f"sp_sp{i}", rng.uniform(0.04, 0.07), loc=(math.cos(a) * d, math.sin(a) * d, rng.uniform(0.9, 1.9)),
                          rot=(0, 0, rng.uniform(0, 90)), color="#d8fff4"))
    return [K.finish("spring", objs)]


# ---------------------------------------------------------------- warp

def warp():
    rng = R(7001)
    objs = [A.lathe("wp_d0", [(1.7, 0), (1.7, 0.14), (1.45, 0.16), (1.42, 0.3), (0, 0.3)], color=SAND_DK, seg=8),
            K.ring_strip("wp_gold", 1.38, 1.46, z=0.302, n=8, color=GOLD, mat="M_Toon")]
    K.rotz(objs, 22.5)
    objs.append(K.ngon_disc("wp_top", 1.36, z=0.303, n=32, color=SAND_LT))
    objs.append(K.ring_strip("wp_r1", 1.08, 1.18, z=0.31, n=32, color=LAVA_HOT))
    objs.append(K.ring_strip("wp_r2", 0.56, 0.62, z=0.31, n=24, color=LAVA_HOT))
    objs.append(K.prism("wp_st", K.star_pts(8, 0.5, 0.2, math.pi / 8), 0.012, axis="Z", loc=(0, 0, 0.312), color=LAVA_CORE,
                        mat="M_Emit"))
    for i in range(12):
        a = i * math.pi / 6
        glyph = K.prism(f"wp_g{i}", [(0, 0.12), (0.05, 0), (0, -0.12), (-0.05, 0)], 0.012, axis="Z",
                        loc=(math.cos(a) * 0.86, math.sin(a) * 0.86, 0.312), rot=(0, 0, math.degrees(a)), color=LAVA,
                        mat="M_Emit")
        objs.append(glyph)
    # four obelisks with glowing tips
    for i in range(4):
        a = math.pi / 4 + i * math.pi / 2
        x, y = math.cos(a) * 1.55, math.sin(a) * 1.55
        objs.append(K.stone(f"wp_ob{i}", (0.3, 0.3, 1.1), loc=(x, y, 0.55), color=K.pick(rng, SAND), bevel=0.04, taper=0.25))
        objs.append(K.prism(f"wp_ot{i}", [(-0.12, 0), (0.12, 0), (0, 0.22)], 0.24, axis="Y", loc=(x, y, 1.1),
                            rot=(0, 0, math.degrees(a)), color=GOLD))
        objs.append(K.gem(f"wp_og{i}", 0.09, loc=(x, y, 1.55), color=LAVA_CORE))
    # floating rune ring
    objs.append(K.ring_strip("wp_fl", 1.18, 1.24, z=0.0, n=32, color=LAVA_HOT, thick=0.03, loc=(0, 0, 0.75)))
    return [K.finish("warp", objs)]


# ---------------------------------------------------------------- torch

def torch():
    rng = R(8001)
    objs = [K.stone("to_b", (0.75, 0.75, 0.22), loc=(0, 0, 0.11), color=SAND_DK, bevel=0.05),
            K.stone("to_s", (0.48, 0.48, 1.05), loc=(0, 0, 0.74), color=SAND[0], bevel=0.04, taper=0.08),
            K.stone("to_c", (0.62, 0.62, 0.14), loc=(0, 0, 1.3), color=SAND_LT, bevel=0.04)]
    for k in range(4):
        part = diamond_carving(f"to_d{k}", 0, 0.78, s=0.45, y=-0.235)
        objs += K.rotz(part, 90 * k)
    objs.append(A.lathe("to_bowl", [(0.12, 0), (0.14, 0.1), (0.42, 0.3), (0.5, 0.42), (0.46, 0.46), (0.36, 0.38),
                                   (0.0, 0.34)], loc=(0, 0, 1.36), color=GOLD, seg=14))
    objs.append(K.ring_strip("to_bz", 0.4, 0.5, z=0.0, n=14, color=GOLD_DK, mat="M_Toon", thick=0.06, loc=(0, 0, 1.68)))
    objs += ember_coals("to_co", rng, 9, 0.28, 0.0, loc=(0, 0, 1.74))
    objs += K.flame("to_fl", loc=(0, 0, 1.72), s=1.8, seed=3)
    mesh = K.finish("torch", objs)
    anchor = K.empty("LightAnchor", loc=(0, 0, 2.15))
    return [mesh, anchor]


# ---------------------------------------------------------------- decor

def decor_1():
    """Clay urns with zigzag bands (ref pots)."""
    rng = R(9101)
    objs = []
    for i, (x, y, s, tilt) in enumerate(((0.0, 0.0, 1.0, 0), (0.55, -0.25, 0.62, 0), (-0.5, 0.25, 0.7, 75))):
        prof = [(0.0, 0), (0.22, 0.0), (0.33, 0.12), (0.4, 0.35), (0.36, 0.6), (0.2, 0.75), (0.18, 0.85), (0.24, 0.9),
                (0.16, 0.92), (0.14, 0.82), (0.0, 0.8)]
        parts = [A.lathe(f"u{i}b", [(r * s, z * s) for r, z in prof], color=K.jit(rng, CLAY, 0.05), seg=14)]
        parts.append(K.ring_strip(f"u{i}band", 0.0, 1.0, z=0, n=1, color=CLAY) if False else
                     A.cyl(f"u{i}bd", r=0.405 * s, depth=0.12 * s, loc=(0, 0, 0.42 * s), color=SAND_CARVE, seg=14))
        for k in range(10):
            a = 2 * math.pi * k / 10
            t = K.prism(f"u{i}z{k}", [(-0.07 * s, -0.05 * s), (0.07 * s, -0.05 * s), (0, 0.05 * s)], 0.03, axis="Y",
                        loc=(0, -0.405 * s, 0.42 * s), color=SAND_LT if k % 2 else GOLD)
            K.rotz([t], math.degrees(a))
            parts.append(t)
        if tilt:
            K.grp_place(parts, loc=(0, 0, 0.33 * s), rot=(tilt, 0, 30))
        K.grp_place(parts, loc=(x, y, 0))
        objs += parts
    objs += [K.boulder("u_sh0", 0.12, loc=(-0.2, -0.45, 0.03), scale=(1.4, 1, 0.3), color=CLAY, seed=3, subdiv=0),
             K.boulder("u_sh1", 0.09, loc=(-0.75, -0.2, 0.03), scale=(1.4, 1, 0.3), color=SAND_CARVE, seed=4, subdiv=0)]
    return [K.finish("decor_1", objs)]


def decor_2():
    """Broken temple pillar with carvings and a fallen drum."""
    rng = R(9201)
    objs = [K.stone("bp_b", (0.95, 0.95, 0.3), loc=(0, 0, 0.15), color=SAND_DK, bevel=0.05),
            K.stone("bp_s", (0.7, 0.7, 1.3), loc=(0, 0, 0.95), color=SAND[0], bevel=0.05),
            K.stone("bp_s2", (0.66, 0.66, 0.5), loc=(0.02, 0.0, 1.82), rot=(4, -6, 8), color=SAND[2], bevel=0.05, rough=0.07,
                    seed=5)]
    for k in range(4):
        objs += K.rotz(diamond_carving(f"bp_d{k}", 0, 1.0, s=0.7, y=-0.35), 90 * k)
    objs.append(K.stone("bp_f", (0.66, 0.66, 0.85), loc=(0.85, 0.55, 0.33), rot=(0, 90, 25), color=SAND[1], bevel=0.05,
                        rough=0.05, seed=9))
    objs += K.grp_place(zigzag("bp_fz", -0.3, 0.3, 0, h=0.2, y=-0.33, n=4), loc=(0.85, 0.55, 0.33), rot=(0, 90, 25))
    for i in range(5):
        objs.append(K.boulder(f"bp_r{i}", rng.uniform(0.08, 0.16), loc=(rng.uniform(-0.6, 0.9), rng.uniform(-0.7, -0.3), 0.04),
                              color=K.pick(rng, SAND + BAS), seed=i, subdiv=0, flat_bottom=-0.04))
    return [K.finish("decor_2", objs)]


def decor_3():
    """Small lava pool ringed by basalt with crust floes."""
    rng = R(9301)
    pts = [(math.cos(a) * r, math.sin(a) * r * 0.8) for a, r in
           [(2 * math.pi * i / 14, 0.85 + rng.uniform(-0.12, 0.12)) for i in range(14)]]
    objs = [K.poly_slab("lp_lava", pts, top=0.03, thick=0.06, color=LAVA, mat="M_Emit", bevel=0.0),
            K.poly_slab("lp_hot", [(x * 0.55, y * 0.55) for x, y in pts], top=0.035, thick=0.02, color=LAVA_HOT,
                        mat="M_Emit", bevel=0.0)]
    for i in range(13):
        a = 2 * math.pi * i / 13 + rng.uniform(-0.1, 0.1)
        objs.append(K.boulder(f"lp_r{i}", rng.uniform(0.18, 0.28), loc=(math.cos(a) * 0.98, math.sin(a) * 0.8, 0.06),
                              scale=(1.2, 1, 0.65), color=K.pick(rng, BAS), seed=i + 30, subdiv=1, flat_bottom=-0.08))
    for i in range(3):
        objs.append(K.poly_slab(f"lp_fl{i}", K.circle_pts(6, rng.uniform(0.1, 0.16)), top=0.045, thick=0.04, color=BAS_DK,
                                bevel=0.01, loc=(rng.uniform(-0.4, 0.4), rng.uniform(-0.3, 0.3), 0)))
    return [K.finish("decor_3", objs)]


def decor_4():
    """Obsidian crystal cluster growing from basalt, glowing at the roots."""
    rng = R(9401)
    objs = [K.boulder("ob_base", 0.55, loc=(0, 0, 0.05), scale=(1.2, 1.0, 0.45), color=BAS[0], seed=8, flat_bottom=-0.1)]
    specs = [(0, 0, 0.26, 1.6, 0, 0), (0.32, 0.1, 0.18, 1.0, 22, 30), (-0.3, 0.15, 0.17, 1.1, -24, 10),
             (0.1, -0.3, 0.15, 0.8, 18, -40), (-0.2, -0.25, 0.12, 0.6, -20, 60), (0.42, -0.25, 0.1, 0.5, 30, -20)]
    for i, (x, y, r, h, tx, tz) in enumerate(specs):
        objs.append(K.shard(f"ob_s{i}", r=r, h=h, loc=(x, y, 0.1), rot=(tx * 0.6, tx, tz), color=OBS if i % 2 == 0 else OBS_HI,
                            seed=i + 4))
        objs.append(K.gem(f"ob_g{i}", r * 0.5, loc=(x * 1.15, y * 1.15 - 0.05, 0.16), color=LAVA_HOT, h=1.0, sides=5))
    return [K.finish("decor_4", objs)]


def decor_5():
    """Desert agave on a sand mound (ref plant)."""
    rng = R(9501)
    objs = [K.boulder("ag_m", 0.6, loc=(0, 0, 0.0), scale=(1, 1, 0.3), color=SAND[1], seed=2, flat_bottom=0.0, subdiv=1)]
    for i in range(14):
        a = 2 * math.pi * i / 14 + rng.uniform(-0.15, 0.15)
        ln = rng.uniform(0.6, 0.95) * (1.0 if i % 2 else 0.8)
        leaf = K.prism(f"ag_l{i}", [(-0.07, 0), (0.07, 0), (0.025, ln * 0.7), (0, ln)], 0.03, axis="Y",
                       color=K.jit(rng, GREEN if i % 2 else GREEN_DK, 0.08))
        K.grp_place([leaf], loc=(0, 0, 0.12), rot=(rng.uniform(25, 60), 0, math.degrees(a) + 90))
        objs.append(leaf)
    for i in range(6):
        a = 2 * math.pi * i / 6 + 0.3
        leaf = K.prism(f"ag_c{i}", [(-0.06, 0), (0.06, 0), (0, 0.6)], 0.03, axis="Y", color=GREEN)
        K.grp_place([leaf], loc=(0, 0, 0.15), rot=(10, 0, math.degrees(a)))
        objs.append(leaf)
    for i in range(3):
        objs.append(K.boulder(f"ag_r{i}", rng.uniform(0.08, 0.13), loc=(rng.uniform(-0.6, 0.6), rng.uniform(-0.6, -0.3), 0.04),
                              color=K.pick(rng, BAS), seed=i, subdiv=0, flat_bottom=-0.03))
    return [K.finish("decor_5", objs)]


def decor_6():
    """Sun idol: stepped altar with an upright gold sun and offering flames."""
    rng = R(9601)
    objs = [K.stone("si_0", (1.1, 0.8, 0.25), loc=(0, 0, 0.125), color=SAND_DK, bevel=0.05),
            K.stone("si_1", (0.8, 0.6, 0.25), loc=(0, 0, 0.375), color=SAND[0], bevel=0.05),
            K.stone("si_2", (0.24, 0.24, 0.5), loc=(0, 0, 0.75), color=SAND_LT, bevel=0.04)]
    objs += zigzag("si_z", -0.5, 0.5, 0.125, h=0.16, y=-0.4, n=6)
    objs += sun("si_sun", 0.52, loc=(0, -0.02, 1.42), rays=12)
    objs += K.grp_place(sun("si_sunb", 0.52, loc=(0, 0, 0), rays=12), loc=(0, 0.02, 1.42), rot=(0, 0, 180))
    for sx in (-1, 1):
        objs.append(A.lathe(f"si_b{sx}", [(0.05, 0), (0.12, 0.05), (0.13, 0.1), (0, 0.08)], loc=(sx * 0.42, -0.1, 0.5),
                            color=GOLD, seg=10))
        objs += K.flame(f"si_f{sx}", loc=(sx * 0.42, -0.1, 0.58), s=0.55, seed=sx + 9)
    return [K.finish("decor_6", objs)]


# ---------------------------------------------------------------- overlays

def overlay_1():
    """Stalactite ledge dripping lava, hugging the top of a wall's -Y face."""
    rng = R(10101)
    objs = []
    x = -1.95
    i = 0
    while x < 1.95:
        w = rng.uniform(0.45, 0.75)
        cx = min(x + w / 2, 1.95 - w / 2)
        objs.append(K.boulder(f"o1_l{i}", 0.32, loc=(cx, -2.12, 4.28), scale=(w / 0.62, 0.55, 0.6), color=K.pick(rng, BAS, 0.1),
                              seed=i + 40, subdiv=1))
        x += w * 0.8
        i += 1
    for j in range(11):
        cx = -1.75 + 3.5 * j / 10 + rng.uniform(-0.08, 0.08)
        ln = rng.uniform(0.45, 1.3) * (1.3 if j % 3 == 1 else 1.0)
        r = rng.uniform(0.12, 0.2)
        st = A.cone(f"o1_s{j}", r=r, depth=ln, loc=(cx, -2.14 - rng.uniform(0, 0.06), 4.1 - ln / 2), rot=(180, 0, 0),
                    color=K.pick(rng, BAS, 0.1), seg=6, smooth=False)
        K.A.deform(st, lambda v, s=rng.random(): Vector((v.x + math.sin(v.z * 4 + s * 6) * 0.025, v.y, v.z)))
        objs.append(st)
        if j % 2 == 0:
            # glowing lava drip running down the stalactite + falling drop
            objs.append(A.cone(f"o1_d{j}", r=r * 0.45, depth=ln * 0.9, loc=(cx, -2.14 - r * 0.62, 4.1 - ln * 0.45),
                               rot=(180, 0, 0), color=LAVA_HOT, mat="M_Emit", seg=6, smooth=False))
            objs.append(A.sphere(f"o1_dr{j}", 0.045, loc=(cx, -2.16 - r * 0.5, 4.1 - ln - 0.14), scale=(1, 1, 1.5),
                                 color=LAVA_CORE, mat="M_Emit", seg=8, rings=5))
    objs += lava_vein("o1_v", [(-1.6, -2.3, 4.15), (-0.6, -2.31, 4.1), (0.3, -2.3, 4.16), (1.5, -2.3, 4.12)], w=0.035)
    return [K.finish("overlay_1", objs)]


def overlay_2():
    """Lavafall pouring from a fissure down the wall face into a small pool."""
    rng = R(10201)
    objs = []
    # fissure lip
    for i in range(5):
        objs.append(K.boulder(f"o2_lip{i}", rng.uniform(0.18, 0.28), loc=(-0.6 + 0.3 * i, -2.08, 3.85 + rng.uniform(-0.05, 0.1)),
                              scale=(1.2, 0.6, 0.8), color=K.pick(rng, BAS), seed=i + 70, subdiv=1))
    # lava stream: layered ribbons (wide molten orange, mid hot, pale core) hugging the face
    wob = lambda t: math.sin(t * 7.0) * 0.06
    objs.append(K.ribbon("o2_st0", 0.02, 3.8, 14, lambda t: 0.62 + 0.18 * t + 0.06 * math.sin(t * 9),
                         x_fn=wob, y_fn=lambda t: -2.05 - 0.04 * t, thick=0.08, color=LAVA))
    K.grad3(objs[-1], LAVA_DEEP, LAVA, LAVA_HOT, mid=0.5)
    objs.append(K.ribbon("o2_st1", 0.02, 3.75, 14, lambda t: 0.36 + 0.1 * t + 0.05 * math.sin(t * 11 + 1),
                         x_fn=wob, y_fn=lambda t: -2.1 - 0.04 * t, thick=0.06, color=LAVA_HOT))
    K.grad3(objs[-1], LAVA, LAVA_HOT, LAVA_CORE, mid=0.5)
    objs.append(K.ribbon("o2_st2", 0.1, 3.7, 10, lambda t: 0.12 + 0.04 * math.sin(t * 13), x_fn=lambda t: wob(t) + 0.05,
                         y_fn=lambda t: -2.14 - 0.04 * t, thick=0.04, color=LAVA_CORE))
    # side cracks on the face
    objs += lava_vein("o2_c1", [(-0.25, -2.02, 3.6), (-0.7, -2.02, 3.2), (-0.9, -2.02, 2.6), (-1.3, -2.02, 2.3)], w=0.035)
    objs += lava_vein("o2_c2", [(0.25, -2.02, 3.0), (0.6, -2.02, 2.7), (1.1, -2.02, 2.75)], w=0.03)
    # splash pool at the base
    pts = [(math.cos(a) * 0.9, -2.0 + abs(math.sin(a)) * -0.6) for a in [math.pi * i / 10 for i in range(11)]]
    pts = [(math.cos(math.pi * i / 10) * 0.95, -2.0 - math.sin(math.pi * i / 10) * 0.62) for i in range(11)]
    objs.append(K.poly_slab("o2_pool", list(reversed(pts)), top=0.04, thick=0.06, color=LAVA, mat="M_Emit", bevel=0.0))
    for i in range(9):
        a = math.pi * (i + 0.5) / 9
        objs.append(K.boulder(f"o2_r{i}", rng.uniform(0.14, 0.22), loc=(math.cos(a) * 1.02, -2.0 - math.sin(a) * 0.72, 0.06),
                              scale=(1.2, 1, 0.7), color=K.pick(rng, BAS), seed=i + 90, subdiv=1, flat_bottom=-0.06))
    objs += K.flame("o2_sp", loc=(0, -2.25, 0.04), s=0.9, outer=LAVA, mid=LAVA_HOT, inner=LAVA_CORE, seed=4)
    return [K.finish("overlay_2", objs)]


# ---------------------------------------------------------------- foe marker

def foe_marker():
    rng = R(11001)
    objs = [K.ring_strip("fm_r0", 1.0, 1.12, z=0.02, n=32, color=LAVA_DEEP),
            K.ring_strip("fm_r1", 0.7, 0.76, z=0.02, n=32, color=LAVA)]
    objs.append(K.prism("fm_st", K.star_pts(6, 0.66, 0.3), 0.012, axis="Z", loc=(0, 0, 0.02), color=LAVA_HOT, mat="M_Emit"))
    for i in range(6):
        a = 2 * math.pi * i / 6
        objs.append(K.shard(f"fm_sp{i}", r=0.1, h=0.55, loc=(math.cos(a) * 1.2, math.sin(a) * 1.2, 0),
                            rot=(0, -25, math.degrees(a)), color=OBS, seed=i))
    # floating obsidian eye-crystal
    objs.append(K.gem("fm_c", 0.32, loc=(0, 0, 2.0), color=OBS, mat="M_Toon", h=2.0, sides=6))
    objs.append(K.ring_strip("fm_h", 0.36, 0.44, z=0.0, n=16, color=GOLD, mat="M_Toon", thick=0.06, loc=(0, 0, 1.97)))
    objs.append(K.gem("fm_e", 0.15, loc=(0, -0.24, 2.0), rot=(90, 0, 0), color=LAVA_CORE, h=1.6, sides=6))
    for i in range(3):
        a = 2 * math.pi * i / 3
        objs.append(K.gem(f"fm_o{i}", 0.09, loc=(math.cos(a) * 0.7, math.sin(a) * 0.7, 1.6 + 0.2 * i), color=LAVA_HOT))
    return [K.finish("foe_marker", objs)]


# ---------------------------------------------------------------- build all

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

LAYOUT = [  # row 0 = north (y=4); W wall, . floor, other tokens = piece on a floor
    "W W boss_gate W W".split(),
    "W lore_stone . torch W".split(),
    "W . chest warp W".split(),
    "W trap spring stairs_down W".split(),
    "W W door W W".split(),
]
EXTRAS = [  # (piece, (cell x, cell y), rot)
    ("decor_1", (1.3, 2.25), 0), ("decor_4", (3.3, 2.6), 0), ("decor_5", (1.3, 1.7), 40), ("decor_3", (2.6, 3.3), 0),
    ("decor_2", (3.25, 1.35), 0), ("decor_6", (2.0, 3.35), 0), ("foe_marker", (1.0, 3.0), 0),
    ("overlay_1", (1, 4), 0), ("overlay_2", (3, 4), 0), ("overlay_2", (0, 2), 90), ("overlay_1", (4, 3), -90),
]


def main():
    from _pipeline import run
    return run(TS, PIECES, layout=LAYOUT, extras=EXTRAS, world="#2b1a1e")


if __name__ == "__main__":
    main()
