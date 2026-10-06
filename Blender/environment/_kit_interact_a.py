"""Interactive architecture for the living ruins and glacier grotto.

All meshes are authored in metres at the cell origin. Hinged components retain
independent transforms; decorative detail is geometry with Col corner colours.
"""
import math
import random
import _kit_common_a as K
from _kit_common_a import MB, T, Vector, vgrad


def xz_prism(poly, depth):
    n = len(poly)
    vs = [(x, y, z) for y in (-depth / 2, depth / 2) for x, z in poly]
    fs = [tuple(reversed(range(n))), tuple(range(n, 2 * n))]
    fs += [(i, (i + 1) % n, (i + 1) % n + n, i + n) for i in range(n)]
    return vs, fs


class NorthernKit:
    def __init__(self, frozen=False):
        self.frozen = frozen
        self.ts = "frost_grotto" if frozen else "verdant_ruins"
        if frozen:
            self.stone = ["#506782", "#607f99", "#7898aa", "#455775"]
            self.dark, self.trim = "#263d59", "#c2e7ef"
            self.glow, self.wood, self.metal = "#8af5ff", "#455674", "#abd3e1"
            self.plant = ["#63a5d5", "#a3daee", "#c9f5ff"]
        else:
            self.stone = ["#e8d6a2", "#dcc58c", "#d3bb80", "#eadcae"]
            self.dark, self.trim = "#7c6844", "#f1dfac"
            self.glow, self.wood, self.metal = "#8dffcf", "#8a5a2b", "#e2b443"
            self.plant = ["#3e9a3c", "#57b445", "#7cc548"]

    def rng(self, name):
        return random.Random(K.seed_of(self.ts, name))

    def block(self, mb, size, loc, col=None, ch=0.045):
        mb.add(K.cbox(*size, ch=ch, loc=loc), col or self.stone[0])

    def ring(self, mb, r, width, z, col=None, mat="M_Toon", n=24):
        mb.add(K.disc(r, n=n, z=z, r_in=r - width), col or self.metal, mat)

    def motif(self, mb, loc, radius=0.35, upright=True, col=None):
        """Six-armed snowflake or leaf-wheel relief, never a flat texture."""
        M = T(loc, rot=(90, 0, 0) if upright else (0, 0, 0))
        c = col or self.glow
        n = 6 if self.frozen else 8
        for i in range(n):
            a = i * 2 * math.pi / n
            if self.frozen:
                pts = [(0, 0, 0), (math.cos(a) * radius, math.sin(a) * radius, 0)]
                mb.add(K.tube(pts, 0.018, sides=4), c, "M_Emit", M=M)
                for side in (-1, 1):
                    root = Vector(pts[1]) * 0.62
                    d = Vector((math.cos(a + side * 0.75), math.sin(a + side * 0.75), 0))
                    mb.add(K.tube([root, root + d * radius * 0.3], 0.012, sides=4), c, "M_Emit", M=M)
            else:
                mb.add(K.leaf(radius, radius * 0.4, fold=0.02), c, "M_Emit",
                       M=M @ T(rot=(0, 0, math.degrees(a))))
        mb.add(K.cyl(radius * 0.14, 0.035, seg=8), self.metal, M=M)

    def nature(self, mb, rng, loc, size=1.0):
        if self.frozen:
            mb.add(K.dome(0.45 * size, 0.35 * size, 0.12 * size, rng, seg=8, rings=2, loc=loc), "#e2f8ff")
            K.crystal_cluster(mb, rng, Vector(loc), self.plant, n=4, size=size, mat="M_Clear")
        else:
            mb.add(K.dome(0.45 * size, 0.35 * size, 0.08 * size, rng, seg=8, rings=2, loc=loc), "#93c83a")
            K.fern(mb, rng, Vector(loc), self.plant, n=5, L=0.6 * size, W=0.15 * size)

    def arch(self, mb, rng, width=2.3, spring=2.6, depth=0.8):
        """True open arch of individual voussoirs, plus bonded side piers."""
        for side in (-1, 1):
            for j in range(5):
                self.block(mb, (0.72, depth, spring / 5 - 0.025),
                           (side * (width / 2 + 0.36), 0, (j + 0.5) * spring / 5), rng.choice(self.stone))
            self.block(mb, (0.85, depth + 0.12, 0.2), (side * (width / 2 + 0.36), 0, 0.1), self.trim)
        n = 9
        for i in range(n):
            a0, a1 = i * math.pi / n + 0.012, (i + 1) * math.pi / n - 0.012
            inner, outer = width / 2, width / 2 + 0.38
            poly = [(math.cos(a0) * inner, spring + math.sin(a0) * inner),
                    (math.cos(a0) * outer, spring + math.sin(a0) * outer),
                    (math.cos(a1) * outer, spring + math.sin(a1) * outer),
                    (math.cos(a1) * inner, spring + math.sin(a1) * inner)]
            mb.add(xz_prism(poly, depth), self.trim if i == n // 2 else rng.choice(self.stone))
        self.motif(mb, (0, -depth / 2 - 0.025, spring + width / 2 + 0.04), 0.22)

    def door(self, locked=False):
        name = "door_locked" if locked else "door"
        rng, frame, leaf = self.rng(name), MB(), MB()
        self.arch(frame, rng)
        if self.frozen:
            for x in (-1.5, 1.5):
                for i in range(3):
                    frame.add(K.icicle(0.08, 0.35 + i * 0.12), self.plant[i], "M_Clear", M=T((x + i * 0.1, -0.48, 3.3)))
        else:
            for sx in (-1, 1):
                K.vine(frame, rng, [(sx * 1.7, -0.5, 3.7), (sx * 1.55, -0.5, 2.5), (sx * 1.75, -0.5, 1.4)],
                       (0, -1, 0), self.wood, self.plant, leaf_size=0.18)
        # Individual boards follow the round head instead of filling the opening.
        for i in range(8):
            x = -1.1 + (i + 0.5) * 2.2 / 8
            h = 2.55 + math.sqrt(max(0, 1.1 ** 2 - x ** 2))
            self.block(leaf, (0.26, 0.14, h - 0.06), (x, 0, h / 2 + 0.03), self.wood, 0.015)
        for z in (0.5, 1.8, 2.5):
            self.block(leaf, (2.17, 0.19, 0.12), (0, 0, z), self.metal, 0.02)
            for x in (-0.98, 0.98):
                leaf.add(K.uvsphere(0.037, seg=8, rings=4, loc=(x, -0.11, z)), self.trim)
        self.motif(leaf, (0, -0.1, 2.2), 0.36)
        leaf.add(K.tube([(0.8, -0.12, 1.1), (0.8, -0.22, 1.1), (0.8, -0.22, 1.45), (0.8, -0.12, 1.45)], 0.045, sides=6), self.metal)
        door = leaf.build("Door", origin=(-1.1, 0, 0))
        out = [frame.build(name), door]
        if locked:
            lock = MB()
            self.block(lock, (0.42, 0.22, 0.45), (0.35, -0.25, 1.45), self.metal)
            lock.add(K.tube([(0.22, -0.25, 1.65), (0.22, -0.25, 1.87), (0.48, -0.25, 1.87), (0.48, -0.25, 1.65)], 0.035, sides=6), self.trim)
            self.motif(lock, (0.35, -0.37, 1.45), 0.13)
            obj = lock.build("Lock")
            K.parent_keep(obj, door)
            out.append(obj)
        return out

    def stairs(self, up):
        name = "stairs_up" if up else "stairs_down"
        rng, mb = self.rng(name), MB()
        # Cell-contained flight: treads travel +Y, exposed sides have a plinth.
        for i in range(8):
            z = (i + 1) * 0.28 if up else -i * 0.28
            y = -1.8 + (i + 0.5) * 0.45
            mb.add(K.prism(K.rect_poly(-1.15, y - 0.225, 1.15, y + 0.225, cut=0.035), z - 0.28, z), rng.choice(self.stone))
            self.block(mb, (2.25, 0.06, 0.035), (0, y - 0.19, z - 0.035), self.trim, 0.01)
        for side in (-1, 1):
            for i in range(8):
                z = (i + 1) * 0.28 if up else -i * 0.28
                self.block(mb, (0.48, 0.43, 0.6), (side * 1.47, -1.8 + (i + 0.5) * 0.45, z + 0.12), rng.choice(self.stone))
            self.nature(mb, rng, (side * 1.5, 1.5, 2.55 if up else 0.0), 0.65)
        self.motif(mb, (0, -1.75, 0.012), 0.25, upright=False)
        return [mb.build(name)]

    def chest(self):
        body, lid = MB(), MB()
        # Hollow chest has four independent walls and an internal dark well.
        self.block(body, (1.3, 0.85, 0.1), (0, 0, 0.05), self.wood)
        for x in (-0.59, 0.59):
            self.block(body, (0.12, 0.85, 0.54), (x, 0, 0.36), self.wood)
        for y in (-0.365, 0.365):
            self.block(body, (1.1, 0.12, 0.54), (0, y, 0.36), self.wood)
            for z in (0.2, 0.4):
                self.block(body, (1.16, 0.015, 0.02), (0, y * 1.18, z), self.dark, 0.005)
        for x in (-0.45, 0.45):
            self.block(body, (0.12, 0.88, 0.63), (x, 0, 0.315), self.metal, 0.02)
        self.motif(body, (0, -0.44, 0.42), 0.17)
        arc = [(math.cos(math.pi * i / 12) * 0.425, 0.63 + math.sin(math.pi * i / 12) * 0.32) for i in range(13)]
        # Extrude Y/Z section along X, keeping rear hinge at +Y.
        geo = xz_prism(arc, 1.3)
        vs, fs = geo
        lid.add(([(y, x, z) for x, y, z in vs], [tuple(reversed(f)) for f in fs]), self.wood)
        for x in (-0.45, 0.45):
            pts = [(x, math.cos(math.pi * i / 12) * 0.44, 0.64 + math.sin(math.pi * i / 12) * 0.33) for i in range(13)]
            lid.add(K.tube(pts, 0.045, sides=5), self.metal)
        lid.add(K.bipyramid(0.12, 0.3), self.glow, "M_Emit", M=T((0, 0, 0.95)))
        return [body.build("chest"), lid.build("Lid", origin=(0, 0.425, 0.63))]

    def lore_stone(self):
        rng, mb = self.rng("lore_stone"), MB()
        self.block(mb, (1.45, 1.15, 0.22), (0, 0, 0.11), self.dark)
        poly = [(-0.6, 0.2), (0.6, 0.2), (0.6, 1.85), (0.4, 2.2), (-0.3, 2.28), (-0.58, 2.0)]
        mb.add(xz_prism(poly, 0.3), vgrad(self.dark, self.trim, 0, 2.3))
        for j in range(5):
            z = 0.6 + 0.25 * j
            for i in range(3):
                x = (i - 1) * 0.27
                mb.add(K.tube([(x - 0.07, -0.16, z - 0.05), (x, -0.16, z + 0.07), (x + 0.07, -0.16, z)], 0.014, sides=4), self.glow, "M_Emit")
        self.motif(mb, (0, -0.165, 1.98), 0.18)
        self.nature(mb, rng, (-0.6, 0.2, 0.22), 0.75)
        return [mb.build("lore_stone")]

    def trap(self):
        plate, spikes = MB(), MB()
        self.block(plate, (2.7, 2.7, 0.1), (0, 0, -0.05), self.metal)
        self.block(plate, (2.5, 2.5, 0.06), (0, 0, -0.025), self.dark)
        for i in range(4):
            for j in range(4):
                x, y = -0.84 + i * 0.56, -0.84 + j * 0.56
                plate.add(K.disc(0.13, n=8, z=0.012), "#152c37", M=T((x, y, 0)))
                spikes.add(K.cone(0.095, 0.55, seg=6), self.trim, M=T((x, y, 0)))
        self.block(spikes, (2.3, 2.3, 0.08), (0, 0, -0.06), self.metal)
        for z in (0,):
            self.motif(plate, (0, -1.19, 0.02), 0.13, upright=False)
        moving = spikes.build("Spikes")
        moving.location.z = -0.58
        return [plate.build("trap"), moving]

    def spring(self):
        rng, mb = self.rng("spring"), MB()
        profile = [(1.35, 0), (1.35, 0.2), (1.23, 0.34), (1.05, 0.34), (0.95, 0.12)]
        mb.add(K.lathe(profile, seg=20), self.trim)
        mb.add(K.disc(1.02, n=32, z=0.13), self.glow, "M_Clear")
        for r in (0.3, 0.65, 0.9):
            self.ring(mb, r, 0.016, 0.136, "#d1ffff", "M_Emit")
        self.block(mb, (0.5, 0.5, 0.3), (0, 0.8, 0.45), self.stone[1])
        mb.add(K.tube([(0, 0.75, 0.55), (0, 0.62, 0.7), (0, 0.25, 0.58), (0, 0.08, 0.14)], [0.05, 0.045, 0.04, 0.02], sides=6), self.glow, "M_Clear")
        self.nature(mb, rng, (0.95, 0.7, 0.1), 0.85)
        for i in range(6):
            a = i * math.pi / 3
            self.motif(mb, (math.cos(a) * 1.22, math.sin(a) * 1.22, 0.345), 0.09, upright=False)
        return [mb.build("spring"), K.empty("LightAnchor_spring", (0, 0, 1.0))]

    def warp(self):
        mb = MB()
        mb.add(K.lathe([(1.6, -0.06), (1.6, 0.04), (1.45, 0.12), (0, 0.12)], seg=24), self.dark)
        for r in (1.4, 1.18, 0.6):
            self.ring(mb, r, 0.035, 0.125, self.glow, "M_Emit")
        self.motif(mb, (0, 0, 0.13), 0.75, upright=False)
        for i in range(8):
            a = i * math.pi / 4
            self.motif(mb, (math.cos(a) * 1.28, math.sin(a) * 1.28, 0.13), 0.10, upright=False)
        return [mb.build("warp"), K.empty("Spot_warp", (0, 0, 0)), K.empty("LightAnchor_warp", (0, 0, 0.8))]

    def torch(self):
        mb = MB()
        mb.add(K.lathe([(0.35, 0), (0.4, 0.15), (0.22, 0.3), (0.19, 1.2), (0.36, 1.4), (0.4, 1.6), (0.3, 1.64)], seg=10), self.stone[1])
        for z in (0.28, 1.2):
            mb.add(K.cyl(0.24, 0.07, seg=10), self.metal, M=T((0, 0, z)))
        if self.frozen:
            K.crystal_cluster(mb, self.rng("torch"), (0, 0, 1.55), self.plant, n=5, size=0.75, mat="M_Emit")
        else:
            for i in range(3):
                mb.add(K.tube([(0, 0, 1.55), (0.1 * (i - 1), 0.04, 1.8), (0.03 * (i - 1), 0, 2.15 - 0.08 * i)], [0.17, 0.12, 0.002], sides=7),
                       vgrad("#ff8731", "#fff5bb", 1.55, 2.15), "M_Emit")
        self.motif(mb, (0, -0.2, 0.8), 0.16)
        return [mb.build("torch"), K.empty("LightAnchor", (0, 0, 1.85))]

    def decor(self, index):
        rng, mb = self.rng(f"decor_{index}"), MB()
        if index == 1:  # organic plant / crystal garden
            self.nature(mb, rng, (0, 0, 0.05), 1.7)
            for i in range(5):
                a = i * 1.3
                mb.add(K.rock(rng, 0.45, 0.4, 0.25, loc=(math.cos(a) * 0.6, math.sin(a) * 0.6, 0.1)), rng.choice(self.stone))
        elif index == 2:  # broken column with real fluted drums
            mb.add(K.lathe([(0.6, 0), (0.6, 0.16), (0.48, 0.22), (0.42, 1.55), (0.33, 1.65)], seg=12), self.stone[0])
            for i in range(8):
                a = i * math.pi / 4
                mb.add(K.tube([(0.4 * math.cos(a), 0.4 * math.sin(a), 0.25), (0.38 * math.cos(a), 0.38 * math.sin(a), 1.48)], 0.035, sides=4), self.trim)
            mb.add(K.cyl(0.45, 0.65, seg=12), self.stone[1], M=T((0.8, 0.1, 0.4), rot=(0, 65, 20)))
            self.nature(mb, rng, (-0.3, 0.3, 0.1), 0.7)
        elif index == 3:  # shallow natural pool
            for i in range(12):
                a = i * math.pi / 6
                mb.add(K.rock(rng, 0.4, 0.3, 0.25, loc=(math.cos(a) * 0.85, math.sin(a) * 0.65, 0.08)), rng.choice(self.stone))
            mb.add(K.disc(0.8, n=24, z=0.045), self.glow, "M_Clear", M=T(scale=(1, 0.75, 1)))
            if not self.frozen:
                for i in range(3):
                    mb.add(K.leaf(0.25, 0.2), self.plant[i], M=T((-0.3 + i * 0.3, 0.1, 0.052), rot=(0, 0, i * 80)))
        elif index == 4:  # shrine urn
            mb.add(K.lathe([(0.26, 0), (0.3, 0.08), (0.27, 0.2), (0.48, 0.55), (0.42, 0.9), (0.22, 1.08), (0.28, 1.13), (0.2, 1.15)], seg=16), self.stone[2])
            for z, r in ((0.18, 0.29), (0.9, 0.4), (1.1, 0.28)):
                mb.add(K.cyl(r, 0.045, seg=16), self.metal, M=T((0, 0, z)))
            self.motif(mb, (0, -0.45, 0.6), 0.22)
        elif index == 5:  # fallen carved lintel and rubble
            self.block(mb, (1.65, 0.7, 0.5), (0, 0, 0.3), self.stone[1], 0.1)
            for x in (-0.5, 0, 0.5):
                self.motif(mb, (x, -0.36, 0.3), 0.15)
            for i in range(6):
                mb.add(K.rock(rng, 0.4, 0.3, 0.3, loc=(rng.uniform(-0.9, 0.9), rng.uniform(-0.6, 0.6), 0.12)), rng.choice(self.stone))
        else:  # wayfinder idol
            mb.add(K.lathe([(0.65, 0), (0.65, 0.15), (0.42, 0.22), (0.32, 1.25), (0.4, 1.4), (0.3, 1.55)], seg=8), self.trim)
            if self.frozen:
                mb.add(K.bipyramid(0.36, 1.1), self.glow, "M_Clear", M=T((0, 0, 1.8)))
            else:
                for i in range(8):
                    mb.add(K.leaf(0.6, 0.22), self.plant[i % 3], M=T((0, 0, 1.48), rot=(35, 0, i * 45)))
                mb.add(K.uvsphere(0.22, seg=12, rings=6, loc=(0, 0, 1.65)), self.glow, "M_Emit")
        return [mb.build(f"decor_{index}")]

    def overlay(self, index):
        rng, mb = self.rng(f"overlay_{index}"), MB()
        if self.frozen:
            for i in range(12 if index == 1 else 5):
                x = -1.8 + 3.6 * i / (11 if index == 1 else 4)
                if index == 1:
                    mb.add(K.icicle(rng.uniform(0.07, 0.15), rng.uniform(0.5, 1.35)), rng.choice(self.plant), "M_Clear", M=T((x, -2.1, 4.4)))
                else:
                    mb.add(K.crystal(0.17, 0.75, seg=6), rng.choice(self.plant), "M_Clear", M=T((x, -2.13, 0.3 + rng.uniform(0, 1.6)), rot=(25, 0, 20)))
                    self.motif(mb, (x, -2.03, 2.8 + rng.uniform(-0.5, 0.5)), 0.2)
        else:
            for i in range(4):
                x = -1.5 + i
                length = rng.uniform(1.8, 3.5)
                pts = [(x + math.sin(j * 0.8 + i) * 0.14, -2.08, 4.4 - length * j / 6) for j in range(7)]
                if index == 1:
                    K.vine(mb, rng, pts, (0, -1, 0), self.wood, self.plant, leaf_size=0.26, leaf_step=0.3,
                           flower_cols=("#fff4dc", "#f2c230"), flower_p=0.18)
                else:
                    mb.add(K.tube(pts, [0.1 * (1 - j / 9) for j in range(7)], sides=6), self.wood)
                    K.leaf_spray(mb, rng, pts[-1], (0, -1, 0), 5, 0.32, self.plant)
        return [mb.build(f"overlay_{index}")]

    def boss_gate(self):
        rng, mb = self.rng("boss_gate"), MB()
        self.arch(mb, rng, width=2.1, spring=2.85, depth=0.85)
        for sx in (-1, 1):
            self.block(mb, (0.6, 0.6, 0.25), (sx * 1.65, -0.65, 0.125), self.dark)
            mb.add(K.lathe([(0.22, 0.25), (0.22, 1.4), (0.36, 1.6), (0.3, 1.75)], seg=8), self.trim, M=T((sx * 1.65, -0.65, 0)))
            mb.add(K.bipyramid(0.24, 0.85), self.glow, "M_Emit", M=T((sx * 1.65, -0.65, 2.1)))
            self.nature(mb, rng, (sx * 1.6, 0.5, 0.05), 0.7)
        return [mb.build("boss_gate"), K.empty("Spot_boss", (0, 0, 0)),
                K.empty("LightAnchor_gate_L", (-1.65, -0.65, 2.1)), K.empty("LightAnchor_gate_R", (1.65, -0.65, 2.1))]

    def foe_marker(self):
        mb = MB()
        mb.add(K.lathe([(0.65, 0), (0.65, 0.13), (0.4, 0.21), (0.3, 0.3)], seg=8), self.dark)
        mb.add(K.bipyramid(0.3, 1.0), "#ff7955", "M_Emit", M=T((0, 0, 0.85)))
        for sx in (-1, 1):
            mb.add(K.tube([(sx * 0.3, 0, 0.4), (sx * 0.5, 0, 0.9), (sx * 0.3, 0, 1.3)], 0.04, sides=5), self.metal)
        return [mb.build("foe_marker"), K.empty("Spot_foe", (0, 0, 0))]

    def extras(self):
        out = [("door", lambda: self.door(False)), ("door_locked", lambda: self.door(True)),
               ("stairs_down", lambda: self.stairs(False)), ("stairs_up", lambda: self.stairs(True))]
        out += [(name, getattr(self, name)) for name in ("chest", "lore_stone", "trap", "spring", "warp", "torch")]
        out += [(f"decor_{i}", lambda i=i: self.decor(i)) for i in range(1, 7)]
        out += [(f"overlay_{i}", lambda i=i: self.overlay(i)) for i in (1, 2)]
        return out + [("boss_gate", self.boss_gate), ("foe_marker", self.foe_marker)]

    def floor(self, variant):
        rng, mb = self.rng(f"floor_{variant}"), MB()
        mb.add(K.prism(K.rect_poly(-2, -2, 2, 2), -0.35, -0.06), self.dark)
        if variant == "c":
            mb.add(K.prism(K.rect_poly(-1.98, -1.98, 1.98, 1.98), -0.1, -0.02), "#54bfdc", "M_Clear")
        polys = K.jitter_grid_polys(rng, -2, -2, 2, 2, 4 if variant == "a" else 3, 4, jit=0.22)
        for i, p in enumerate(polys):
            p = K.inset_poly(p, 0.035 if variant != "c" else 0.07)
            if variant == "c":
                p = K.split_poly(p, K.poly_centroid(p), rng.random() * math.pi, gap=0.04)[0]
            col = "#cdeaf2" if variant == "b" and i % 3 == 0 else rng.choice(self.stone)
            mb.add(K.prism(p, -0.28, 0, inset=0.035, ch=0.035), vgrad(self.dark, col, -0.2, 0))
        if variant == "b":
            self.motif(mb, (0, 0, 0), 0.85, upright=False)
        return [mb.build(f"floor_{variant}")]

    def wall(self, variant):
        rng, mb = self.rng(f"wall_{variant}"), MB()
        self.block(mb, (3.7, 3.7, 4.4), (0, 0, 2.2), self.dark, 0.02)
        for side in ("S", "E", "N", "W"):
            M = K.face_matrix(side, 1.92)
            for j in range(6):
                z = (j + 0.5) * 0.7
                for i in range(3):
                    x = (i - 1) * 1.3
                    col = rng.choice(self.stone)
                    mb.add(K.cbox(1.28, 0.67, 0.26, ch=0.045, loc=(x, z, -0.12)), col, M=M)
            if variant in ("a", "b"):
                for x in (-1.55, 1.55):
                    mb.add(K.cbox(0.25, 4.15, 0.14, ch=0.04, loc=(x, 2.1, -0.02)), self.trim, M=M)
            # Face-local snowflake / crystal ribs on all four faces.
            relief = MB()
            self.motif(relief, (0, 0, 0), 0.42, upright=False)
            mb.add((relief.v, [f[0] for f in relief.f]), self.glow, "M_Emit", M=M @ T((0, 2.5, 0.005)))
            if variant == "c":
                for i in range(4):
                    x = -1.5 + i
                    mb.add(K.icicle(0.12, 0.9 + i * 0.15), self.plant[i % 3], "M_Clear",
                           M=T(M @ Vector((x, 4.15, 0.07))))
            if variant == "b":
                for x in (-1, 1):
                    mb.add(K.crystal(0.16, 0.7), self.plant[1], "M_Clear", M=M @ T((x, 0.4, 0), rot=(0, 25, 0)))
        mb.add(K.prism(K.rect_poly(-2, -2, 2, 2, cut=0.04), 4.2, 4.5, inset=0.035, ch=0.05), self.trim)
        for i in range(4):
            mb.add(K.dome(0.65, 0.55, 0.12, rng, seg=8, rings=2, loc=((-1) ** i, (-1) ** (i // 2), 4.38)), "#e2f8ff")
        return [mb.build(f"wall_{variant}")]

    def frost_pieces(self):
        return [(f"floor_{v}", lambda v=v: self.floor(v)) for v in "abc"] + \
               [(f"wall_{v}", lambda v=v: self.wall(v)) for v in "abc"] + self.extras()
