"""Limestone cave under the city ('cave' tileset).

Look: layered limestone walls (grey strata with ochre bands, grime at the foot and in the corners) with blue and violet
crystal veins and clusters (M_Emit), a rock ceiling with stalactites and glowing crystal clusters hanging from it
(`Ceiling` root object on every floor piece), uneven floors with rail tracks, an underground stream and puddles.
Props: mine cart, timber supports, a miner's lantern, giant mushrooms, boulder piles (KayKit Space Base rocks) and crystal
clusters; the arena is a cave hall with a rock roof, stalactites and crystal clusters around the edge.
"""
import math
import random

from mathutils import Vector

import common_a as C
import arch_geo as G
from common_a import HunterKit, MB, KA, T, box, cyl, quad, plate, flat_bar, chain, pick, jit, grime, cc, join, \
    kit_pal, place_mb, CEIL, ARENA_CEIL, WALL_H

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
RAIL = "#8f9499"

PAL = kit_pal("#2c2620", "#b9a88f")   # CC0 rock props: luminance mapped to limestone shades


def _rgb(h):
    return G.rgb(h)


def _base(z):
    """Shared bulge of every cave wall face (tiles across cells because it depends on z only)."""
    return 0.10 + 0.04 * math.sin(z * 1.3)


def _amp(z):
    return 0.18


def _wall_colour(seed):
    """Relief colouring: grey limestone layers with ochre strata; darker foot and corners (grime)."""
    def colour(cu, cz, normal, rng):
        band = int((cz + 0.3 * math.sin(cu * 1.7 + seed)) / 0.42) % 6
        base = STRATA[band % len(STRATA)] if band == 5 else ROCK[(band // 2) % len(ROCK)]
        k = 1.0 + rng.uniform(-0.05, 0.05)
        f = 0.62 if cz < 0.4 else (0.62 + 0.38 * min(1.0, (cz - 0.4) / 0.6))
        if abs(cu) > 1.7:
            f *= 0.86
        c = _rgb(base) * k * f
        return c, "M_Toon"
    return colour


def _ceil_colour(seed):
    def colour(cx, cy, normal, rng):
        c = _rgb(rng.choice([ROCK_D, ROCK_DD, "#4a4238"])) * (1 + rng.uniform(-0.05, 0.05))
        return c, "M_Toon"
    return colour


def _floor_colour(rng, edge=True):
    def colour(x, y, rng2):
        f = 1.0
        if edge:
            m = max(abs(x), abs(y))
            f = 0.78 + 0.22 * G.smooth(1.5, 2.0, m)
        base = FLOOR_ROCK[rng2.randrange(len(FLOOR_ROCK))]
        return _rgb(base) * f * (1 + rng2.uniform(-0.04, 0.04)), "M_Toon"
    return colour

class CaveKit(HunterKit):
    TS = "cave"
    WORLD = "#101418"
    SKY = ("#1d2350", "#05060f")

    # ------------------------------------------------------------ ceilings (Ceiling root, normals down)
    def _ceiling(self, piece):
        seed = sum(map(ord, self.TS + piece))
        objs = [G.cave_ceiling("rock_roof", seed, 0.4, _ceil_colour(seed), n=6)]
        n_st = {"floor_a": 5, "floor_b": 7, "floor_c": 4}.get(piece, 5)
        objs += G.stalactites(seed + 1, n_st, (ROCK_D, "#5a4a3c", ROCK_DD), length=(0.5, 1.3), radius=(0.14, 0.3))
        mb = MB()
        rng = random.Random(seed + 9)
        for k in range(3 if piece != "floor_b" else 2):   # glowing crystal clusters hanging from the rock
            x, y = rng.uniform(-1.4, 1.4), rng.uniform(-1.4, 1.4)
            KA.crystal_cluster(mb, rng, (x, y, CEIL - 0.02), [CRY_B, CRY_BL, CRY_V], n=4, size=0.55,
                               mat="M_Emit", spread=0.18, up=(0, 0, -1), tilt=0.35)
        objs.append(mb.build("crystals_roof"))
        return join("Ceiling", objs)

    # ------------------------------------------------------------ floors (flush detail at z = 0) + Ceiling
    def floor(self, v):
        rng = self.rng(f"floor_{v}")
        seed = sum(map(ord, f"floor{v}"))
        objs = []
        mb = MB()
        if v == "a":
            # uneven limestone with a few pits and dark puddles
            objs.append(G.faceted_plane("ground", seed, 7, _floor_colour(rng)))
            for _ in range(3):
                x, y = rng.uniform(-1.3, 1.3), rng.uniform(-1.3, 1.3)
                mb.add(KA.disc(rng.uniform(0.25, 0.45), n=12, z=0.003), WATER, "M_Clear", M=T((x, y, 0)))
            for _ in range(4):
                x, y = rng.uniform(-1.6, 1.6), rng.uniform(-1.6, 1.6)
                mb.add(KA.disc(0.09, n=8, z=0.002), CRY_B, "M_Emit", M=T((x, y, 0)))
        elif v == "b":
            # mine track: two rails and timber sleepers, flush on the rock
            objs.append(G.faceted_plane("ground", seed, 7, _floor_colour(rng)))
            for x in (-0.45, 0.45):
                flat_bar(mb, RAIL, (x, -2.0), (x, 2.0), 0.07, 0.003)
                flat_bar(mb, "#c9ced3", (x + 0.02, -2.0), (x + 0.02, 2.0), 0.02, 0.005)
            for k in range(9):
                y = -1.9 + k * 0.42
                quad(mb, WOOD_D, -0.7, y, 0.7, y + 0.16, 0.001)
        else:
            # cave stream: a glowing channel with stepping stones and a shallow pool
            objs.append(G.faceted_plane("ground", seed, 7, _floor_colour(rng)))
            flat_bar(mb, STREAM, (-0.3, -2.0), (0.6, 2.0), 0.42, 0.0, mat="M_Emit")
            flat_bar(mb, WATER, (-0.3, -2.0), (0.6, 2.0), 0.3, 0.004, mat="M_Clear")
            mb.add(KA.disc(0.75, n=14, z=0.003), WATER, "M_Clear", M=T((-1.3, 1.1, 0)))
            for k, (x, y) in enumerate(((-0.1, -1.4), (0.2, -0.7), (0.5, 0.1), (0.2, 0.9))):
                mb.add(KA.disc(0.22, n=10, z=0.006), ROCK_L, M=T((x, y, 0)))
        objs.append(mb.build("details"))
        return [join(f"floor_{v}", objs), self._ceiling(f"floor_{v}")]

    # ------------------------------------------------------------ walls
    def wall(self, v):
        seed = {"wall_a": 101, "wall_b": 211, "wall_c": 317}[f"wall_{v}"]
        objs = []
        core = MB()
        core.add(KA.cbox(3.7, 3.7, WALL_H, ch=0.1, loc=(0, 0, WALL_H / 2)), grime(ROCK_DD, low=0.5, k=0.55, corner=0.5),
                 "M_Toon")
        objs.append(core.build(f"core_{v}"))
        veins = {"a": 1, "b": 2, "c": 3}[v]
        for k, sd in enumerate("NESW"):
            f = G.relief_face(f"rock_{sd}", seed * 7 + k, _base, _amp, _wall_colour(seed + k), nu=12, nz=12,
                              jitter=0.3, cracks=G.crack_paths(seed * 3 + k, veins, steps=(3, 6)), crack_w=0.07,
                              crack_col=_rgb(CRY_B))
            f.data.transform(G.side(sd))
            objs.append(f)
            rng = random.Random(seed * 5 + k)
            if v != "a" or k % 2 == 0:   # crystal clusters pushing out of the face
                sub = MB()
                for _ in range(2 if v != "c" else 3):
                    u = rng.uniform(-1.4, 1.4)
                    z = rng.uniform(0.5, 3.2)
                    p = (u, -2.0 - _base(z) - 0.05, z)
                    KA.crystal_cluster(sub, rng, p, [CRY_B, CRY_BL, CRY_V], n=5, size=0.9 + 0.4 * rng.random(),
                                       mat="M_Emit", spread=0.2, up=(0, -1, 0.35), tilt=0.4)
                objs.append(C.place_mb(sub, G.side(sd)).build(f"crystals_{v}_{sd}"))
        return [join(f"wall_{v}", objs)]
    # ------------------------------------------------------------ decor (stand on the floor, front = -Y)
    def _mine_cart(self, mb):
        """Ore cart on a short stub of track: timber rim, iron body, copper ore heaped inside, four wheels."""
        box(mb, IRON, -0.55, 0.55, -0.36, 0.36, 0.28, 0.72, ch=0.03)
        for x in (-0.58, 0.58):
            box(mb, WOOD, x - 0.03, x + 0.03, -0.4, 0.4, 0.18, 0.78, ch=0.02)
        box(mb, WOOD, -0.6, 0.6, -0.4, -0.34, 0.72, 0.8, ch=0.02)
        box(mb, WOOD, -0.6, 0.6, 0.34, 0.4, 0.72, 0.8, ch=0.02)
        rng = random.Random(42)
        for _ in range(9):
            x, y = rng.uniform(-0.4, 0.4), rng.uniform(-0.25, 0.25)
            s = rng.uniform(0.12, 0.22)
            mb.add(KA.rock(rng, s, s, s * 0.7, n=9, flat=0.2), pick(rng, [ORE, COPPER]), M=T((x, y, 0.72)))
        for x in (-0.42, 0.42):
            for y in (-0.36, 0.36):
                cyl(mb, IRON_D, (x, y, 0.0), 0.11, 0.07, seg=10, rot=(0, 90, 0), center=True)

    def _timber(self, mb, x0=-0.9, x1=0.9):
        """Timber mine support: two posts, a cap beam and diagonal braces, all in the -Y plane."""
        for x in (x0 + 0.1, x1 - 0.1):
            box(mb, WOOD, x - 0.12, x + 0.12, -0.2, 0.2, 0.0, 2.7, ch=0.04)
        box(mb, WOOD_D, x0, x1, -0.22, 0.22, 2.6, 2.84, ch=0.05)
        for x, sgn in ((x0 + 0.1, 1), (x1 - 0.1, -1)):
            box(mb, WOOD_D, min(x, x + sgn * 0.45), max(x, x + sgn * 0.45), -0.22, 0.22, 2.1, 2.22, ch=0.02)

    def _lantern(self, mb):
        """Miner's lantern on a post: a warm glowing glass box under a cap."""
        cyl(mb, WOOD_D, (0, 0, 0), 0.07, 1.6, seg=8)
        box(mb, IRON_D, -0.14, 0.14, -0.14, 0.14, 1.6, 1.68, ch=0.03)
        box(mb, LANTERN, -0.1, 0.1, -0.1, 0.1, 1.35, 1.6, ch=0.0, mat="M_Emit")
        box(mb, IRON, -0.12, 0.12, -0.12, 0.12, 1.3, 1.35, ch=0.02)
        mb.add(KA.bipyramid(0.16, 0.2, seg=6), IRON_D, M=T((0, 0, 1.68)))

    def _mushrooms(self, mb, rng, cluster=True):
        """Giant cave mushrooms: pale stalks with coloured caps, two of them glowing."""
        spots = [(0.0, 0.0, 0.5, MUSH_CAP), (0.38, -0.2, 0.34, MUSH_V), (-0.3, 0.25, 0.42, MUSH_G)]
        for x, y, h, cap in spots:
            cyl(mb, MUSH, (x, y, 0.0), 0.05 + h * 0.06, h, seg=8)
            vs, fs = KA.lathe([(0.0, h), (h * 0.6, h + 0.04), (h * 0.8, h - 0.02), (h * 0.5, h - 0.07)], seg=10)
            mb.add((vs, fs), cap, M=T((x, y, 0.0)))
            mb.add(KA.disc(h * 0.07, n=7, z=h + 0.035), MUSH_G if cap != MUSH_G else CRY_BL, "M_Emit",
                   M=T((x + 0.03, y, 0.0)))

    def decor(self, i):
        mb = MB()
        rng = self.rng(f"decor_{i}")
        if i == 1:
            self._mine_cart(mb)
            return [mb.build("decor_1")]
        if i == 2:
            self._timber(mb)
            return [mb.build("decor_2")]
        if i == 3:
            self._lantern(mb)
            return [mb.build("decor_3")]
        if i == 4:
            self._mushrooms(mb, rng)
            return [mb.build("decor_4")]
        if i == 5:
            # boulder pile from the KayKit Space Base rock set, recoloured to limestone
            return [join("decor_5", [cc("ks", "rocks_A", PAL, loc=(0.0, 0.0, 0.0), scale=1.1, rz=30.0),
                                     cc("ks", "rock_B", PAL, loc=(0.45, -0.2, 0.0), scale=1.0, rz=80.0),
                                     cc("ks", "rock_A", PAL, loc=(-0.5, 0.2, 0.0), scale=1.2, rz=-40.0)])]
        KA.crystal_cluster(mb, rng, (0.0, 0.0, 0.0), [CRY_B, CRY_V, CRY_BL, CRY_VL], n=5, size=1.25, mat="M_Emit",
                           spread=0.25)
        return [mb.build("decor_6")]

    # ------------------------------------------------------------ overlays (hug the -Y face of a wall block: y -2..-2.35)
    def overlay(self, i):
        rng = self.rng(f"overlay_{i}")
        mb = MB()
        M = KA.face_matrix("S", 2.0)
        if i == 1:
            # crystal cluster growing out of the wall, with a vein of violet light
            KA.crystal_cluster(mb, rng, (0.2, -2.0, 0.0), [CRY_B, CRY_BL, CRY_V], n=6, size=1.1, mat="M_Emit",
                               spread=0.3, up=(0, -1, 0.3), tilt=0.45)
            flat_bar(mb, CRY_VL, (-0.9, 0.9), (-0.4, 2.3), 0.07, 0.0, M=M, mat="M_Emit")
            flat_bar(mb, CRY_VL, (-0.4, 2.3), (-0.6, 3.4), 0.06, 0.0, M=M, mat="M_Emit")
        else:
            # a row of stalactites hanging from the top of the wall, with a drip of water
            for k in range(6):
                u = -1.5 + 0.6 * k + rng.uniform(-0.1, 0.1)
                L = rng.uniform(0.35, 0.8)
                mb.add(KA.icicle(0.11, L, seg=6), ROCK_D, M=T((u, -2.15, CEIL - 0.02)))
            mb.add(KA.disc(0.07, n=8, z=0.0), WATER_L, "M_Clear", M=T((0.4, -2.15, 0.02)))
        return [mb.build(f"overlay_{i}")]
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

    # ------------------------------------------------------------ arena: a cave hall with a rock floor, a mine rail
    # behind the enemies, a limestone ring with crystal veins and a low rock roof (ARENA_CEIL)
    RING_R = 17.2

    def _ring_r(self, a, z):
        return self.RING_R + 0.38 * math.sin(7 * a + 0.9 * z) + 0.22 * math.sin(13 * a - 1.7 * z + 2.0)

    def _ring_p(self, a, z, inset=0.0):
        r = self._ring_r(a, z) - inset
        return (r * math.cos(a), r * math.sin(a), z)

    def _rock_floor(self, mb, rng, R, n):
        """Irregular limestone floor: a jittered lattice of triangles, each in a rock shade (darker toward the ring)."""
        step = 2 * R / n
        P = {}
        for j in range(n + 1):
            for i in range(n + 1):
                x, y = -R + i * step, -R + j * step
                if 0 < i < n:
                    x += rng.uniform(-0.3, 0.3) * step
                if 0 < j < n:
                    y += rng.uniform(-0.3, 0.3) * step
                P[i, j] = (x, y, 0.0)
        for j in range(n):
            for i in range(n):
                q = [P[i, j], P[i + 1, j], P[i + 1, j + 1], P[i, j + 1]]
                cx = sum(v[0] for v in q) / 4
                cy = sum(v[1] for v in q) / 4
                if math.hypot(cx, cy) > R - 0.2:
                    continue
                edge = math.hypot(cx, cy) > 13.5
                for tri in ((0, 1, 2), (0, 2, 3)):
                    col = rng.choice(["#5f574b", "#6d6456", "#7b725f", "#534c42"] if edge else FLOOR_ROCK)
                    mb.add(([q[k] for k in tri], [(0, 1, 2)]), col)

    def arena_floor(self, rng):
        """Rock floor across the hall: worn limestone tiles, opaque wet pools, cracks, crystal flecks, and a mine
        rail (two rails and timber sleepers along X) behind the enemy side at y = 11.6."""
        mb = MB()
        R = self.RING_R
        mb.add(KA.disc(R + 0.3, n=72, z=-0.01), ROCK_DD)
        self._rock_floor(mb, rng, R, n=24)
        for x, y in ((-7.5, 11.2), (7.0, 11.6), (1.5, 12.4)):   # wet pools beyond the rail (opaque, reads as water)
            mb.add(KA.disc(rng.uniform(0.7, 1.2), n=16, z=0.003), "#2f5a68", M=T((x, y, 0)))
        for _ in range(16):                                  # cracks
            x, y = rng.uniform(-14, 14), rng.uniform(-14, 14)
            if math.hypot(x, y) < 15.5:
                flat_bar(mb, "#5d5649", (x, y), (x + rng.uniform(-1.4, 1.4), y + rng.uniform(-1.4, 1.4)), 0.05, 0.004)
        for _ in range(12):                                  # crystal flecks in the rock
            x, y = rng.uniform(-13, 13), rng.uniform(-6, 14)
            if math.hypot(x, y) < 15.5:
                KA.crystal_cluster(mb, rng, (x, y, 0.0), [CRY_B, CRY_BL], n=3, size=0.32, mat="M_Emit",
                                   spread=0.2, tilt=0.3)
        for _ in range(9):                                   # floor variation: light and dark rock patches, pebbles
            x, y = rng.uniform(-15, 15), rng.uniform(-15, 15)
            if 9.6 < math.hypot(x, y) < 16.0:       # outside the battle disc
                mb.add(KA.disc(rng.uniform(0.9, 2.0), n=12, z=0.003), pick(rng, ["#a08c74", "#9a8468", "#7c6b56"]),
                       M=T((x, y, 0)))
        for _ in range(6):
            x, y = rng.uniform(-14, 14), rng.uniform(-14, 14)
            if math.hypot(x, y) < 15.5:
                mb.add(KA.disc(rng.uniform(0.6, 1.1), n=12, z=0.003), "#3f3930", M=T((x, y, 0)))   # wet dark patches
        for _ in range(22):
            x, y = rng.uniform(-14, 14), rng.uniform(-14, 14)
            if math.hypot(x, y) < 15.5:
                mb.add(KA.rock(rng, 0.09, 0.08, 0.05, n=7, flat=0.3), pick(rng, ROCK + [ROCK_L]),
                       M=T((x, y, 0)))
        RAIL_Y = 8.0
        for yy in (RAIL_Y - 0.45, RAIL_Y + 0.45):
            flat_bar(mb, RAIL, (-12.0, yy), (12.0, yy), 0.07, 0.004)
            flat_bar(mb, "#c9ced3", (-12.0, yy + 0.02), (12.0, yy + 0.02), 0.02, 0.005)
        for k in range(-12, 13):
            quad(mb, WOOD_D, k - 0.11, RAIL_Y - 0.72, k + 0.11, RAIL_Y + 0.72, 0.002)
        return mb

    def arena_backdrop(self, rng):
        """Limestone ring from the floor to the roof: layered strata with ochre bands, grime at the foot, crystal veins
        and clusters pushing out of the wall (dense on the enemy side, y 4..12)."""
        mb = MB()
        n_a, n_z, H = 72, 9, ARENA_CEIL
        zs = [H * k / n_z for k in range(n_z + 1)]
        for i in range(n_a):
            a0, a1 = 2 * math.pi * i / n_a, 2 * math.pi * (i + 1) / n_a
            for j in range(n_z):
                z0, z1 = zs[j], zs[j + 1]
                band = int(z0 / 1.2) % 6
                base = STRATA[(i + band) % len(STRATA)] if band == 5 else ROCK[((i // 3) + band // 2) % len(ROCK)]
                quad_v = [self._ring_p(a0, z0), self._ring_p(a1, z0), self._ring_p(a1, z1), self._ring_p(a0, z1)]
                # inward-facing quad, four corners in ring order
                mb.add((quad_v, [(0, 3, 2, 1)]), grime(base, low=1.1, k=0.6, corner=0.0))
        # crystal veins: thin glowing lines across the ring
        for k in range(14):
            a = rng.uniform(-0.2, math.pi + 0.2)
            z = rng.uniform(1.5, 6.0)
            for s in range(5):   # a zig-zag vein: a thin emissive strip per step, same winding as the wall quads
                a0, a1 = a + 0.05 * s, a + 0.05 * (s + 1)
                z0, z1 = z + 0.12 * s, z + 0.12 * (s + 1)
                q = [self._ring_p(a0, z0, inset=0.03), self._ring_p(a1, z0, inset=0.03),
                     self._ring_p(a1, z1, inset=0.03), self._ring_p(a0, z1, inset=0.03)]
                mb.add((q, [(0, 3, 2, 1)]), CRY_B if k % 3 else CRY_V, "M_Emit")
        # crystal clusters pushing out of the ring, enemy side (sin a > 0) dense, party side sparse
        for k in range(22):
            a = rng.uniform(0.15, math.pi - 0.15) if k < 16 else rng.uniform(math.pi, 2 * math.pi)
            z = rng.uniform(0.6, 4.5)
            r_in = self._ring_r(a, z) - 0.05
            p = (r_in * math.cos(a), r_in * math.sin(a), z)
            sub = MB()
            KA.crystal_cluster(sub, rng, (0, 0, 0), [CRY_B, CRY_BL, CRY_V], n=5, size=1.6 + 0.8 * rng.random(),
                               mat="M_Emit", spread=0.22, up=(-math.cos(a), -math.sin(a), 0.4), tilt=0.4)
            mb.extend(C.place_mb(sub, T(p)))
        return mb

    def _roof_z(self, x, y):
        """Roof height over the hall: a flat rim at ARENA_CEIL, lumps hanging down toward the middle."""
        r = math.hypot(x, y)
        taper = G.smooth(12.0, 16.0, r)
        lump = 0.5 + 0.5 * math.sin(0.9 * x + 0.4) * math.sin(1.1 * y - 0.7) + 0.25 * math.sin(2.3 * x - 1.7 * y)
        return ARENA_CEIL - 0.05 - 1.1 * (1.0 - taper) * max(0.0, lump)

    def arena_ceiling(self, rng):
        """Low rock roof over the hall (normals down): a lattice of rock plates with lumps, icicles and crystal
        clusters (enemy side first). No radial pattern."""
        mb = MB()
        R, n = 16.6, 34
        step = 2 * R / n
        P = {}
        for j in range(n + 1):
            for i in range(n + 1):
                x, y = -R + i * step, -R + j * step
                if 0 < i < n:
                    x += rng.uniform(-0.25, 0.25) * step
                if 0 < j < n:
                    y += rng.uniform(-0.25, 0.25) * step
                P[i, j] = (x, y, self._roof_z(x, y))
        for j in range(n):
            for i in range(n):
                q = [P[i, j], P[i + 1, j], P[i + 1, j + 1], P[i, j + 1]]
                cx = sum(v[0] for v in q) / 4
                cy = sum(v[1] for v in q) / 4
                if math.hypot(cx, cy) > R - 0.3:
                    continue
                col = rng.choice(["#7a6650", "#6b5a48", "#8a7459", "#5e4f3f"])
                # normals down: reversed winding relative to the floor lattice
                for tri in ((0, 3, 2), (0, 2, 1)):
                    mb.add(([q[k] for k in tri], [(0, 1, 2)]), col)
        for k in range(40):   # icicles hanging from the roof (tips well above the fighters' heads)
            x, y = rng.uniform(-14.0, 14.0), rng.uniform(-14.0, 14.0)
            if math.hypot(x, y) > R - 1.0:
                continue
            mb.add(KA.icicle(rng.uniform(0.12, 0.22), rng.uniform(0.6, 1.8), seg=6), ROCK_D,
                   M=T((x, y, self._roof_z(x, y) - 0.02)))
        for k in range(26):   # glowing clusters on the roof, enemy side first
            x, y = (rng.uniform(-12, 12), rng.uniform(3, 14)) if k < 17 else (rng.uniform(-13, 13), rng.uniform(-12, 3))
            if math.hypot(x, y) > R - 1.0:
                continue
            KA.crystal_cluster(mb, rng, (x, y, self._roof_z(x, y) - 0.02), [CRY_B, CRY_BL, CRY_V], n=4, size=0.6,
                               mat="M_Emit", spread=0.18, up=(0, 0, -1), tilt=0.35)
        return mb

    def arena_props(self, rng):
        """Mine carts on the rail, timber supports, lanterns, mushrooms and rock piles. Enemy side (y > 0) is dense,
        the party side is sparse and keeps clear of the camera (camera at (0, -12, 4))."""
        out = []
        mb = MB()
        for x, y, rz in ((-4.2, 8.0, 0.0), (7.6, 8.0, 0.0)):
            sub = MB()
            self._mine_cart(sub)
            mb.extend(C.place_mb(sub, T((x, y, 0), (0, 0, rz))))
        for x in (-9.0, -3.0, 3.0, 9.0):
            sub = MB()
            self._timber(sub, x0=-0.9, x1=0.9)
            mb.extend(C.place_mb(sub, T((x, 9.6, 0), (0, 0, 0))))
        for x, y in ((-6.5, 11.0), (6.5, 11.0), (-11.5, 8.4)):
            sub = MB()
            self._lantern(sub)
            mb.extend(C.place_mb(sub, T((x, y, 0), (0, 0, 0))))
        for x, y in ((-10.0, 7.0), (11.0, 7.4), (-1.5, 12.0)):
            sub = MB()
            self._mushrooms(sub, rng)
            mb.extend(C.place_mb(sub, T((x, y, 0), (0, 0, 0))))
        # crystal clusters against the flanks (x +-7..9, y 2..10), scaled up for the battle frame
        flank = MB()
        for x, y, sz in ((-8.4, 2.6, 2.1), (-7.4, 6.0, 2.5), (-8.8, 9.4, 2.2), (8.2, 2.8, 2.3), (7.4, 6.4, 2.6),
                         (8.6, 9.6, 2.0)):
            KA.crystal_cluster(flank, rng, (x, y, 0.0), [CRY_B, CRY_BL, CRY_V], n=6, size=sz, mat="M_Emit",
                               spread=0.3, tilt=0.35)
        out.append(flank.build("arena_crystals_flank"))
        out.append(mb.build("arena_props"))
        for x, y, rz, s in ((-8.0, 8.6, 30.0, 1.4), (9.2, 9.8, -20.0, 1.6), (-11.5, 12.8, 80.0, 1.8),
                            (2.4, 14.0, 10.0, 1.8)):
            out.append(cc("ks", "rocks_A", PAL, loc=(x, y, 0), rz=rz, scale=s))
        for x, y, rz in ((-6.0, 6.0, 40.0), (12.5, 4.8, 0.0)):
            out.append(cc("ks", "rock_B", PAL, loc=(x, y, 0), rz=rz, scale=1.5))
        for x, y, rz in ((-13.5, -8.0, 0.0), (13.0, -7.0, 0.0)):
            out.append(cc("ks", "rock_A", PAL, loc=(x, y, 0), rz=rz, scale=1.4))
        return out
