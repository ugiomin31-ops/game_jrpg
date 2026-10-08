"""Limestone cave under the city ('cave' tileset).

Look: uneven limestone floors with pits and puddles, rock walls whose faces are pocketed (edges fixed at the cell
boundary so neighbours join), blue/violet crystal clusters in the pockets (M_Emit), stalagmites and giant mushrooms,
a small underground stream, a miner's lantern, timber mine props, a rail cart and a crystal portal.
"""
import math

import random

from mathutils import Vector, noise

import common_a as C
from common_a import HunterKit, MB, KA, T, box, cyl, quad, plate, flat_bar, chain, pick, jit

ROCK = ["#86725e", "#9a8267", "#7a6957", "#8f7a62"]          # brown-grey limestone
STRATA = ["#b8893f", "#c49a52", "#a27a45"]                  # ochre bands between the grey layers
ROCK_L = "#c9b592"
ROCK_D = "#55493c"
ROCK_DD = "#3b3630"
FLOOR_ROCK = ["#8f8775", "#7f7868", "#a0977f", "#877f6d"]
BASE_DARK = "#3b352c"
WATER = "#3f8fb8"
WATER_L = "#7fd4f2"
STREAM = "#2fe9ff"              # bright cyan underground stream
CRY_B = "#49c8ff"
CRY_BL = "#7fe6ff"
CRY_V = "#9a6bff"
CRY_VL = "#c9a6ff"
MUSH = "#efe6d6"
MUSH_CAP = "#d98fd6"
MUSH_G = "#7ff0d0"
MUSH_V = "#b78bff"
WOOD = "#8a5a36"
WOOD_D = "#5e3d25"
IRON = "#5f666d"
IRON_D = "#3a3f45"
ORE = "#6c6a66"
COPPER = "#c9824a"
LANTERN = "#ffc56b"
MOSS = "#6f9a5b"


def _noise01(x, y, z):
    return 0.5 + 0.5 * noise.noise(Vector((x, y, z)))


def _depth(base, seed, amp, w):
    """Inward bulge of the rock face: ridged low-frequency crease plus a finer chunky bump, scaled by the
    edge-tapered window w (zero on the cell boundary so neighbouring walls join)."""
    k1 = _noise01(base.x * 1.1 + seed, base.y * 1.1 - seed, base.z * 0.9)
    k2 = _noise01(base.x * 3.3 + seed * 1.3, base.y * 3.3, base.z * 2.9)
    ridge = 1.0 - abs(2.0 * k1 - 1.0)
    return amp * w * (0.15 + 0.65 * ridge + 0.45 * k2)


def _strata_pal(seed):
    """Warm brown-grey rock in horizontal layers with ochre bands; the layer edges wobble with noise."""
    def pal(co):
        k = _noise01(co.x * 1.5 + seed, co.y * 1.5, co.z * 0.7)
        layer = int((co.z + 0.3 * (k - 0.5)) / 0.32)
        if layer % 4 == 2:
            col = STRATA[(layer // 4) % len(STRATA)]
        else:
            col = ROCK[(layer * 3 + int(k * 4)) % len(ROCK)]
        r, g, b, a = KA.C(col)
        m = 0.82 + 0.28 * k - 0.08 * min(1.0, co.z / C.WALL_H)
        return (min(1, r * m), min(1, g * m), min(1, b * m), a)
    return pal


def rock_block(mb, rng, amp, n, pal, seed):
    """Solid-looking 4 x 4 x 4.5 m rock wall built as four bumpy heightfields plus a flat cap. Edges stay on the
    cell boundary (+-2, z 0..4.5) so neighbours join; the faces bulge into the room by up to ~amp (creases and
    chunks). The cap is flat and no vertex leaves the cell."""
    H = C.WALL_H
    S = 2.0
    for (nx, ny), (tx, ty) in (((1, 0), (0, 1)), ((-1, 0), (0, -1)), ((0, 1), (-1, 0)), ((0, -1), (1, 0))):
        grid = {}
        for i in range(n + 1):
            for j in range(n + 1):
                s, t = i / n, j / n
                u = -S + 2 * S * s
                z = H * t
                w = math.sin(math.pi * s) * math.sin(math.pi * t)
                base = Vector((nx * S + tx * u, ny * S + ty * u, z))
                p = base - Vector((nx, ny, 0)) * _depth(base, seed, amp, w)
                grid[i, j] = (p.x, p.y, p.z)
        vs = []
        idx = {}
        for key, p in grid.items():
            idx[key] = len(vs)
            vs.append(p)
        fs = []
        for i in range(n):
            for j in range(n):
                a, b, c, d = idx[i, j], idx[i + 1, j], idx[i + 1, j + 1], idx[i, j + 1]
                fs.append((a, b, c, d))
        mb.add((vs, fs), lambda co, pal=pal: pal(co))
    cap = [(-S, -S, H), (S, -S, H), (S, S, H), (-S, S, H)]
    mb.add((cap, [(0, 1, 2, 3)]), ROCK_D)
    return mb


SIDE_N = [((1, 0), (0, 1)), ((-1, 0), (0, -1)), ((0, 1), (-1, 0)), ((0, -1), (1, 0))]


def surface_point(side, s, t, amp, seed):
    """Point on the rock face (u = s, v = t across the face) and the outward normal of that side."""
    (nx, ny), (tx, ty) = SIDE_N[side]
    S, H = 2.0, C.WALL_H
    u = -S + 2 * S * s
    z = H * t
    w = math.sin(math.pi * s) * math.sin(math.pi * t)
    base = Vector((nx * S + tx * u, ny * S + ty * u, z))
    return base - Vector((nx, ny, 0)) * _depth(base, seed, amp, w), Vector((nx, ny, 0))


def hang_from_cap(mb, side, s, seed_rng, col):
    """Stalactite hanging from the flat top edge, set a little into the room from the face."""
    (nx, ny), (tx, ty) = SIDE_N[side]
    S = 2.0
    u = -S + 2 * S * s
    base = Vector((nx * S + tx * u, ny * S + ty * u, C.WALL_H)) - Vector((nx, ny, 0)) * 0.3
    L = seed_rng.uniform(0.7, 1.25)
    mb.add(KA.icicle(seed_rng.uniform(0.1, 0.14), L, seg=6), col, M=T((base.x, base.y, base.z - 0.005)))


class CaveKit(HunterKit):
    TS = "cave"
    WORLD = "#101418"
    SKY = ("#1d2350", "#05060f")

    # ------------------------------------------------------------ floors (uneven rock, pits at z = -0.06)
    def floor(self, v):
        rng = self.rng(f"floor_{v}")
        mb = MB()
        plate(mb, BASE_DARK, -2, -2, 2, 2, -0.3, -0.1)
        polys = KA.jitter_grid_polys(rng, -2, -2, 2, 2, 10, 10, jit=0.32)
        for poly in polys:
            z = -0.06 if rng.random() < 0.18 else 0.0
            col = pick(rng, FLOOR_ROCK, 0.06)
            pts = C.ccw(poly)
            mb.add(([(x, y, z) for x, y in pts], [(0, 1, 2, 3)]), col)
        if v == "b":
            # shallow puddle with a glossy sheen
            mb.add(KA.disc(0.9, n=20, z=-0.02), WATER, "M_Clear", M=T((0.4, -0.3, 0)))
            mb.add(KA.disc(0.5, n=16, z=-0.01), WATER_L, "M_Clear", M=T((-0.9, 0.9, 0)))
        if v == "c":
            # copper-veined patch and a few moss spots
            for _ in range(3):
                x, y = rng.uniform(-1.4, 1.4), rng.uniform(-1.4, 1.4)
                flat_bar(mb, COPPER, (x, y), (x + rng.uniform(-0.6, 0.6), y + rng.uniform(-0.5, 0.5)), 0.08, 0.0)
            for _ in range(4):
                x, y = rng.uniform(-1.6, 1.6), rng.uniform(-1.6, 1.6)
                mb.add(KA.disc(0.22, n=10, z=0.0), MOSS, M=T((x, y, 0)))
        return [mb.build(f"floor_{v}")]

    # ------------------------------------------------------------ walls
    def wall(self, v):
        rng = self.rng(f"wall_{v}")
        seed = 11.0 + "abc".index(v) * 7.3
        amp = {"a": 0.5, "b": 0.56, "c": 0.46}[v]
        mb = MB()
        rock_block(mb, rng, amp, 12, _strata_pal(seed), seed)
        hang_cols = [ROCK_L, STRATA[1], ROCK[0]]
        if v == "a":
            # four clusters, one per face, of five blue/violet crystals each
            for side in range(4):
                p, nrm = surface_point(side, rng.uniform(0.35, 0.65), rng.uniform(0.3, 0.5), amp, seed)
                cols = [CRY_B, CRY_BL, CRY_V] if side % 2 else [CRY_V, CRY_VL, CRY_B]
                KA.crystal_cluster(mb, rng, p + nrm * 0.02, cols, n=6, size=1.25, mat="M_Emit", spread=0.25,
                                   up=(-nrm * 0.75 + Vector((0, 0, 0.66))).normalized(), tilt=0.5)
            stal = 3
        elif v == "b":
            # two large clusters on opposite faces, six crystals each, plus a violet ledge at the base
            for side in (0, 2):
                p, nrm = surface_point(side, 0.5, rng.uniform(0.25, 0.4), amp, seed)
                cols = [CRY_V, CRY_VL, CRY_B]
                KA.crystal_cluster(mb, rng, p + nrm * 0.02, cols, n=6, size=1.45, mat="M_Emit", spread=0.3,
                                   up=(-nrm * 0.7 + Vector((0, 0, 0.7))).normalized(), tilt=0.5)
            stal = 3
        else:
            # two small clusters on the other faces; a glowing vein on every face
            for side in (1, 3):
                p, nrm = surface_point(side, 0.5, rng.uniform(0.3, 0.45), amp, seed)
                KA.crystal_cluster(mb, rng, p + nrm * 0.02, [CRY_BL, CRY_V], n=4, size=0.95, mat="M_Emit",
                                   spread=0.22, up=(-nrm * 0.6 + Vector((0, 0, 0.8))).normalized(), tilt=0.45)
            stal = 2
            for side in range(4):
                s0 = rng.uniform(0.3, 0.7)
                pts = []
                for k in range(6):
                    t = 0.12 + k * 0.13
                    p, nrm = surface_point(side, s0 + 0.04 * math.sin(k), t, amp, seed)
                    pts.append(p - nrm * 0.01)
                for a, b in zip(pts, pts[1:]):
                    mid = (a + b) / 2
                    mb.add(KA.crystal(0.05, 0.3, seg=4), CRY_B if side % 2 else CRY_V, "M_Emit",
                           M=KA.z_axis_matrix((0.2, 0.0, 1.0), (mid.x, mid.y, mid.z)))
        # stalactites hanging from the top edge of every face
        for side in range(4):
            for k in range(stal):
                s0 = (k + 0.5) / stal * rng.uniform(0.85, 1.15)
                hang_from_cap(mb, side, min(0.96, max(0.04, s0)), rng, pick(rng, hang_cols, 0.05))
        return [mb.build(f"wall_{v}")]

    # ------------------------------------------------------------ doors (timber mine gate in a rock frame)
    def door(self, locked):
        name = "door_locked" if locked else "door"
        frame = MB()
        rock = ROCK[0]
        box(frame, rock, -2.0, -1.0, -1.0, 1.0, 0.0, C.WALL_H, ch=0.06)
        box(frame, rock, 1.0, 2.0, -1.0, 1.0, 0.0, C.WALL_H, ch=0.06)
        box(frame, rock, -1.0, 1.0, -1.0, 1.0, 3.12, C.WALL_H, ch=0.06)
        for y in (-1.02, 1.02):
            for x in (-1.0, 1.0):
                box(frame, WOOD, x - 0.12, x + 0.12, y - 0.05, y + 0.05, 0.0, 3.2, ch=0.0)
            box(frame, WOOD, -1.12, 1.12, y - 0.05, y + 0.05, 3.1, 3.3, ch=0.0)
        objs = [frame.build(name)]
        leaf = MB()
        for k in range(7):
            x0 = -1.0 + k * (2.0 / 7)
            box(leaf, WOOD if k % 2 == 0 else "#7a4f2f", x0 + 0.02, x0 + 2.0 / 7 - 0.02, -0.05, 0.05, 0.0, 3.08,
                ch=0.0)
        for z in (0.5, 1.6, 2.6):
            box(leaf, IRON_D, -1.0, 1.0, -0.06, 0.06, z - 0.05, z + 0.05, ch=0.0)
        leaf_obj = leaf.build("Door", origin=(-1.0, 0.0, 0.0))
        objs.append(leaf_obj)
        if locked:
            lock = MB()
            box(lock, IRON, 0.5, 0.72, -0.12, -0.05, 1.2, 1.5, ch=0.02)
            quad(lock, LANTERN, 0.56, 1.36, 0.66, 1.42, -0.125, mat="M_Emit")
            chain(lock, IRON_D, (0.61, -0.12, 1.2), (0.61, -0.14, 0.9), link_r=0.04, wire=0.012)
            lock_obj = lock.build("Lock")
            KA.parent_keep(lock_obj, leaf_obj)
            objs.append(lock_obj)
        return objs

    # ------------------------------------------------------------ stairs (rock steps)
    def stairs(self, up):
        mb = MB()
        if up:
            for k in range(5):
                y1, y0 = 2.0 - 0.4 * k, 2.0 - 0.4 * (k + 1)
                box(mb, ROCK[k % 2], -1.9, 1.9, y0, y1, 0.0, 0.5 * (k + 1), ch=0.08)
            box(mb, ROCK[2], -2.0, 2.0, -2.0, 0.0, 0.0, 2.5, ch=0.08)
            for k in range(6):
                flat_bar(mb, CRY_B, (-1.7, -1.5 + 0.3 * k), (1.7, -1.5 + 0.3 * k), 0.05, 2.505, mat="M_Emit")
            return [mb.build("stairs_up")]
        plate(mb, FLOOR_ROCK[0], -2.0, 0.0, 2.0, 2.0, -0.3, -0.01)
        for k in range(5):
            y1, y0 = -0.4 * k, -0.4 * (k + 1)
            box(mb, ROCK[k % 2], -2.0, 2.0, y0, y1, -3.0, -0.5 * (k + 1), ch=0.08)
        return [mb.build("stairs_down")]

    # ------------------------------------------------------------ cell props
    def chest(self):
        body = MB()
        box(body, WOOD, -0.7, 0.7, -0.42, 0.42, 0.0, 0.75, ch=0.04)
        for x in (-0.5, 0.5):
            box(body, IRON, x - 0.04, x + 0.04, -0.44, 0.44, 0.0, 0.79, ch=0.0)
        M = KA.face_matrix("S", 0.42)
        quad(body, IRON, -0.12, 0.25, 0.12, 0.48, 0.005, M=M)
        lid = MB()
        box(lid, WOOD_D, -0.72, 0.72, -0.42, 0.42, 0.75, 0.9, ch=0.05)
        for x in (-0.5, 0.5):
            box(lid, IRON, x - 0.04, x + 0.04, -0.44, 0.44, 0.9, 0.93, ch=0.0)
        return [body.build("chest"), lid.build("Lid", origin=(0.0, 0.42, 0.75))]

    def lore_stone(self):
        mb = MB()
        box(mb, ROCK_L, -0.5, 0.5, -0.3, 0.3, 0.0, 2.0, ch=0.1)
        M = KA.face_matrix("S", 0.3)
        for k, (u0, v0, u1, v1) in enumerate(((-0.35, 1.5, 0.35, 1.6), (-0.2, 1.1, 0.2, 1.2), (-0.3, 0.7, 0.1, 0.8),
                                                (-0.1, 0.3, 0.3, 0.4))):
            quad(mb, CRY_BL, u0, v0, u1, v1, 0.01, M=M, mat="M_Emit")
        for i in range(3):
            flat_bar(mb, CRY_V, (-0.3, 1.8 - 0.12 * i), (0.3, 1.8 - 0.12 * i), 0.03, 0.01, M=M, mat="M_Emit")
        return [mb.build("lore_stone")]

    def spring(self):
        """Underground spring: rock basin, still water, crystals at the rim."""
        mb = MB()
        basin = KA.lathe([(0.8, 0.0), (0.95, 0.1), (0.95, 0.3), (0.7, 0.36), (0.5, 0.3), (0.0, 0.25)], seg=14)
        mb.add(basin, ROCK[1])
        mb.add(KA.disc(0.72, n=18, z=0.26), WATER, "M_Clear")
        mb.add(KA.disc(0.3, n=12, z=0.27), WATER_L, "M_Clear")
        KA.crystal_cluster(mb, random.Random(3), (0.0, 0.0, 0.3), [CRY_B, CRY_BL], n=3, size=0.6,
                           mat="M_Emit", spread=0.4, tilt=0.2)
        return [mb.build("spring")]

    def trap(self):
        """Pit of stalagmite spikes with a dark floor, glowing crystal chips."""
        mb = MB()
        plate(mb, BASE_DARK, -1.4, -1.4, 1.4, 1.4, -0.02, 0.02)
        spikes = MB()
        for i in range(9):
            a = 2 * math.pi * i / 9
            r = 0.5 if i % 2 else 0.95
            spikes.add(KA.cone(0.13, 0.7 + 0.2 * (i % 3), seg=6), ROCK[i % 4], M=T((math.cos(a) * r, math.sin(a) * r, 0.01)))
        mb.add(KA.disc(0.4, n=12, z=0.03), CRY_V, "M_Emit")
        return [mb.build("trap"), spikes.build("Spikes")]

    def warp(self):
        """Crystal portal: a ring of standing crystals around a glowing violet pool."""
        mb = MB()
        mb.add(KA.disc(1.5, n=32, z=0.0), ROCK_D)
        mb.add(KA.disc(1.15, n=32, z=0.02), CRY_V, "M_Clear")
        mb.add(KA.disc(1.3, n=32, z=0.03, r_in=1.1), CRY_V, "M_Emit")
        rng = random.Random(9)
        for i in range(8):
            a = 2 * math.pi * i / 8
            KA.crystal_cluster(mb, rng, (math.cos(a) * 1.35, math.sin(a) * 1.35, 0.0), [CRY_B, CRY_BL, CRY_VL],
                               n=2, size=0.7, mat="M_Emit", spread=0.05, tilt=0.1)
        return [mb.build("warp"), KA.empty("LightAnchor_warp", (0, 0, 0.8))]

    def torch(self):
        """Miner's lantern on an iron bracket that touches the wall at y = +0.3."""
        mb = MB()
        box(mb, IRON_D, -0.07, 0.07, -0.9, 0.3, 1.75, 1.82, ch=0.0)
        box(mb, IRON_D, -0.25, 0.25, 0.0, 0.3, 1.45, 1.9, ch=0.02)
        chain(mb, IRON, (0.0, -0.75, 1.75), (0.0, -0.75, 1.5), link_r=0.04, wire=0.011)
        box(mb, IRON, -0.15, 0.15, -0.9, -0.6, 1.0, 1.4, ch=0.02)
        quad(mb, LANTERN, -0.12, 1.02, 0.12, 1.36, 0.01, M=KA.face_matrix("S", 0.9), mat="M_Emit")
        mb.add(KA.lathe([(0.0, 1.5), (0.18, 1.42), (0.22, 1.4)], seg=10), IRON)
        return [mb.build("torch"), KA.empty("LightAnchor", (0, -0.75, 1.25))]

    # ------------------------------------------------------------ decor (stand on the floor, front = -Y)
    def decor(self, i):
        rng = self.rng(f"decor_{i}")
        mb = MB()
        if i == 1:
            # stalagmite cluster
            for (x, y, h, r) in ((-0.25, 0.0, 2.5, 0.4), (0.3, -0.12, 1.6, 0.32), (0.02, 0.32, 0.95, 0.26),
                                 (0.42, 0.25, 0.6, 0.2)):
                mb.add(KA.lathe([(r, 0.0), (r * 0.8, h * 0.35), (r * 0.45, h * 0.75), (0.0, h)], seg=7),
                       pick(rng, ROCK, 0.05), M=T((x, y, 0)))
        elif i == 2:
            # giant glowing mushrooms: cream stalks, emissive violet / teal / pink caps with pale spots
            for (x, y, h, cap, glow) in ((-0.42, -0.1, 1.3, MUSH_V, True), (0.3, 0.1, 0.9, MUSH_CAP, True),
                                        (0.0, 0.42, 0.55, MUSH_G, True), (-0.05, -0.42, 0.7, MUSH_CAP, True)):
                cyl(mb, MUSH, (x, y, 0.0), 0.1, h, seg=8)
                cap_geo = KA.lathe([(0.0, h), (0.22, h - 0.05), (0.42, h - 0.14), (0.4, h - 0.2)], seg=12)
                mb.add(cap_geo, cap, "M_Emit" if glow else "M_Toon", M=T((x, y, 0.0)))
                for k in range(3):
                    sp = KA.disc(0.05, n=5, z=0.0)
                    mb.add(sp, "#ffffff", M=T((x + 0.2 * math.cos(k * 2.1), y + 0.2 * math.sin(k * 2.1), h - 0.1)))
        elif i == 3:
            # crystal cluster standing on the floor
            KA.crystal_cluster(mb, rng, (0.0, 0.0, 0.0), [CRY_B, CRY_V, CRY_BL, CRY_VL], n=5, size=1.2,
                               mat="M_Emit", spread=0.2, tilt=0.35)
        elif i == 4:
            # old mine cart on a short rail: wooden box, iron rim, copper ore, wheels
            for y in (-0.5, 0.5):
                plate(mb, IRON_D, -0.5, y - 0.02, 0.5, y + 0.02, 0.0, 0.02)
            box(mb, WOOD, -0.5, 0.5, -0.32, 0.32, 0.12, 0.6, ch=0.02)
            box(mb, IRON, -0.52, 0.52, -0.34, 0.34, 0.6, 0.66, ch=0.0)
            for k in range(6):
                x = -0.4 + 0.16 * k
                mb.add(KA.rock(rng, 0.2, 0.2, 0.16, n=8), COPPER if k % 2 else ORE,
                       M=T((x, 0.0, 0.6)))
            for x in (-0.38, 0.38):
                for y in (-0.36, 0.36):
                    cyl(mb, IRON_D, (x, y, 0.06), 0.09, 0.06, seg=10, rot=(90, 0, 0), center=True)
        elif i == 5:
            # timber props: two posts with a cross beam, a leaning pickaxe
            for x in (-0.4, 0.4):
                box(mb, WOOD, x - 0.09, x + 0.09, -0.1, 0.1, 0.0, 2.2, ch=0.02)
            box(mb, WOOD_D, -0.6, 0.6, -0.12, 0.12, 2.1, 2.3, ch=0.02)
            box(mb, WOOD, -0.25, 0.25, 0.1, 0.16, 0.0, 0.2, ch=0.01)
            box(mb, WOOD_D, 0.06, 0.1, -0.08, -0.04, 0.0, 1.1, ch=0.0)
            box(mb, IRON, -0.12, 0.2, -0.1, -0.02, 1.05, 1.15, ch=0.0)
        else:
            # barrels with bands and a small glowing lantern on top
            for x, y in ((-0.3, -0.1), (0.3, 0.05)):
                cyl(mb, WOOD, (x, y, 0.0), 0.28, 0.9, seg=12)
                cyl(mb, IRON, (x, y, 0.25), 0.29, 0.05, seg=12)
                cyl(mb, IRON, (x, y, 0.65), 0.29, 0.05, seg=12)
            cyl(mb, IRON_D, (0.0, 0.3, 0.0), 0.15, 0.25, seg=10)
            mb.add(KA.uvsphere(0.12, seg=8, rings=4, loc=(0.0, 0.3, 0.3)), LANTERN, "M_Emit")
        return [mb.build(f"decor_{i}")]

    # ------------------------------------------------------------ overlays (-Y face of a wall block, y -2 .. -2.35)
    def overlay(self, i):
        rng = self.rng(f"overlay_{i}")
        mb = MB()
        if i == 1:
            # underground stream: rock channel along the wall foot with still water and glowing pebbles
            plate(mb, ROCK[2], -2.0, -2.35, 2.0, -2.0, 0.0, 0.22, M=None)
            mb.add(([(-2.0, -2.3, 0.2), (2.0, -2.3, 0.2), (2.0, -2.06, 0.2), (-2.0, -2.06, 0.2)], [(0, 1, 2, 3)]),
                   STREAM, "M_Emit")
            for k in range(7):
                x = -1.8 + 0.6 * k
                mb.add(KA.uvsphere(0.07, seg=6, rings=3), ROCK_L, M=T((x, -2.2 - 0.05 * (k % 2), 0.22)))
                mb.add(KA.disc(0.06, n=6, z=0.22), CRY_BL, "M_Emit", M=T((x + 0.2, -2.14, 0.0)))
        else:
            # stalactites hanging from a rock lip at the top of the wall
            plate(mb, ROCK[1], -2.0, -2.4, 2.0, -2.0, 4.2, 4.5, M=None)
            for k in range(7):
                x = -1.6 + 0.5 * k + rng.uniform(-0.08, 0.08)
                L = rng.uniform(0.6, 1.2)
                mb.add(KA.lathe([(0.0, -L), (0.1, -L * 0.6), (0.18, -L * 0.2), (0.2, 0.0)], seg=6),
                       ROCK[k % 4], M=T((x, -2.2, 4.2)))
                mb.add(KA.disc(0.04, n=5, z=-L + 0.02), CRY_V, "M_Emit", M=T((x, -2.2, 4.2)))
        return [mb.build(f"overlay_{i}")]

    # ------------------------------------------------------------ boss gate and marker
    def boss_gate(self):
        """Rock barrier across the cell with a huge violet crystal seal."""
        mb = MB()
        rng = self.rng("boss_gate")
        for x, y, s in ((-1.5, 0.0, 2.2), (1.5, 0.0, 2.2), (0.0, 0.0, 2.8), (-0.7, -0.35, 1.8), (0.9, -0.3, 1.7)):
            mb.add(KA.rock(rng, 1.9, 0.9, s, n=14, flat=0.1, loc=(0.0, 0.0, 0.0)), ROCK[int(abs(x) * 3) % 4],
                   M=T((x, y, s * 0.5 - 0.1)))
        KA.crystal_cluster(mb, rng, (0.0, -0.35, 1.5), [CRY_V, CRY_VL, CRY_B], n=5, size=1.6, mat="M_Emit",
                           spread=0.35, tilt=0.15)
        return [mb.build("boss_gate"), KA.empty("LightAnchor_gate_L", (-1.65, -0.85, 0.9)),
                KA.empty("LightAnchor_gate_R", (1.65, -0.85, 0.9))]

    def foe_marker(self):
        mb = MB()
        mb.add(KA.disc(1.1, n=28, z=0.0, r_in=0.85), CRY_B, "M_Emit")
        mb.add(KA.disc(0.55, n=20, z=0.005), ROCK_D)
        return [mb.build("foe_marker"), KA.empty("Spot_foe", (0, 0, 0))]

    # ------------------------------------------------------------ arena: crystal cavern stage
    def arena_floor(self, rng):
        mb = MB()
        mb.add(KA.disc(9.6, n=48, z=-0.08), BASE_DARK)
        polys = KA.jitter_grid_polys(rng, -10.0, -10.0, 10.0, 10.0, 12, 12, jit=0.25)
        for poly in polys:
            cx, cy = KA.poly_centroid(poly)
            if math.hypot(cx, cy) > 9.6:
                continue
            col = pick(rng, FLOOR_ROCK, 0.06)
            z = -0.05 if rng.random() < 0.15 else 0.0
            pts = C.ccw(poly)
            mb.add(([(x, y, z) for x, y in pts], [tuple(range(len(pts)))]), col)
        mb.add(KA.disc(2.0, n=28, z=0.01), WATER, "M_Clear")
        mb.add(KA.disc(2.0, n=28, z=0.012, r_in=1.8), CRY_V, "M_Emit")
        return mb

    def arena_backdrop(self, rng):
        """Cavern ring: a pocketed rock wall around the stage with crystal clusters and a bright crystal gate."""
        mb = MB()
        R, H, n = 17.0, 12.0, 56
        seed = 5.0
        for i in range(n):
            a0, a1 = 2 * math.pi * i / n, 2 * math.pi * (i + 1) / n
            mid = 0.5 * (a0 + a1)
            rr = lambda a, z: (R * math.cos(a), R * math.sin(a), z)
            k = _noise01(math.cos(mid) * 3 + seed, math.sin(mid) * 3, 0.5)
            col = ROCK[int(k * 4) % 4]
            mb.add(([rr(a0, 0), rr(a1, 0), rr(a1, H), rr(a0, H)], [(0, 3, 2, 1)]), col)
        for k in range(16):
            a = 2 * math.pi * k / 16 + 0.1
            x, y = (R - 0.8) * math.cos(a), (R - 0.8) * math.sin(a)
            KA.crystal_cluster(mb, rng, (x, y, 0.0), [CRY_B, CRY_V, CRY_BL], n=4, size=2.5 + 0.5 * (k % 3),
                               mat="M_Emit", spread=0.3, tilt=0.2)
        mb.add(([(-3.0, 16.8, 0.6), (3.0, 16.8, 0.6), (3.0, 16.8, 5.0), (-3.0, 16.8, 5.0)], [(0, 1, 2, 3)]),
               CRY_V, "M_Emit")
        return mb
