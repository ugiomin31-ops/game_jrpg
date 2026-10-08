"""Abandoned factory ('factory' tileset).

Look: stained concrete with yellow/black hazard stripes, steel grating, corrugated blue-grey metal walls, rust-red
brick, concrete with mustard/teal pipes and valves, hanging cage lamps (warm orange), conveyor, crates, oil drums,
valves, chain hoists and gas cylinders, a steel roller door, and a machine-floor arena.
"""
import math

import common_a as C
from common_a import HunterKit, MB, KA, T, box, cyl, quad, plate, flat_bar, tile_quads, diag_stripes, chain, pick

CONC = ["#8f8b82", "#9a968c", "#86827a"]
CONC_STAIN = "#6e6a62"
CONC_D = "#5d5a53"
HAZ_Y = "#f2b705"
HAZ_K = "#2b2b2b"
RUST = "#b8612e"
RUST_D = "#7d3f22"
CORR_D = "#4c6474"
CORR_L = "#7f97a5"
BRICK = ["#a4543c", "#94493a", "#b26049", "#9b4c38"]
MORTAR = "#cfc6b4"
PIPE_T = "#d4a03a"
PIPE_G = "#4f9a8c"
PIPE_R = "#c8483a"
STEEL = "#8c969d"
STEEL_D = "#4f585f"
GRATE_D = "#3a4046"
GRATE_L = "#9aa3aa"
LAMP = "#ffc07a"
LAMP_E = "#ffd9a0"
DRUM_B = "#2f5f8f"
DRUM_O = "#e07a2a"
CRATE = "#a47a4d"
CRATE_D = "#7d5a36"
BELT = "#2b2e31"
GAS_G = "#3f7f5f"
GAS_Y = "#c9b04a"
VALVE_R = "#c23b2e"
BLACK = "#222427"


def _face(side, d):
    return KA.face_matrix(side, d)


class FactoryKit(HunterKit):
    TS = "factory"
    WORLD = "#2a1d17"
    SKY = ("#4a2f22", "#14100d")

    # ------------------------------------------------------------ floors
    def floor(self, v):
        rng = self.rng(f"floor_{v}")
        mb = MB()
        if v == "a":
            # stained concrete slabs with a diagonal yellow/black hazard band across the middle of the cell
            plate(mb, CONC_D, -2, -2, 2, 2, -0.3, -0.03)
            tile_quads(mb, rng, CONC, -2, -2, 2, 2, 0.4, 0.4, d=-0.01, gap=0.04, amt=0.06)
            for _ in range(7):
                x, y = rng.uniform(-1.6, 1.6), rng.uniform(-1.6, 1.6)
                r = rng.uniform(0.25, 0.5)
                quad(mb, CONC_STAIN, x - r, y - r * 0.6, x + r, y + r * 0.6, 0.0)
            diag_stripes(mb, [HAZ_Y, HAZ_K], -2, 0.9, 2, 1.5, 0.3, 0.0, mat="M_Toon")
        elif v == "b":
            # steel grating: light bars over a dark recess (reads as holes)
            plate(mb, GRATE_D, -2, -2, 2, 2, -0.3, -0.03)
            for i in range(11):
                u = -2 + 0.4 * i
                quad(mb, GRATE_L, u - 0.06, -2, u + 0.06, 2, 0.0)
            for j in range(11):
                w = -2 + 0.4 * j
                quad(mb, GRATE_L, -2, w - 0.06, 2, w + 0.06, 0.002)
            for i in range(10):
                for j in range(10):
                    quad(mb, "#1f2327", -2 + 0.4 * i + 0.08, -2 + 0.4 * j + 0.08,
                         -2 + 0.4 * i + 0.32, -2 + 0.4 * j + 0.32, -0.005)
        else:
            # cracked stained concrete with oil puddles (glossy M_Clear sheen)
            plate(mb, CONC_D, -2, -2, 2, 2, -0.3, -0.03)
            tile_quads(mb, rng, CONC, -2, -2, 2, 2, 0.5, 0.5, d=-0.01, gap=0.03, amt=0.07)
            for _ in range(4):
                x, y = rng.uniform(-1.2, 1.2), rng.uniform(-1.2, 1.2)
                mb.add(KA.disc(rng.uniform(0.35, 0.6), n=14, z=0.002), "#2b2a2f", "M_Clear",
                       M=T((x, y, 0)))
            zig = [(-1.9, -0.6), (-1.2, -0.3), (-0.8, -0.9), (-0.3, -0.5), (0.3, -0.7), (1.0, -0.2), (1.9, -0.5)]
            for p, q in zip(zig, zig[1:]):
                flat_bar(mb, "#5a5650", p, q, 0.04, -0.004)
        return [mb.build(f"floor_{v}")]

    # ------------------------------------------------------------ walls
    def _core(self, mb, col, inset):
        mb.add(KA.cbox(2 * (2.0 - inset), 2 * (2.0 - inset), C.WALL_H, ch=0.05, loc=(0, 0, C.WALL_H / 2)), col)

    def wall(self, v):
        rng = self.rng(f"wall_{v}")
        mb = MB()
        if v == "a":
            # corrugated metal: raised ribs over a recessed core, rust streaks, concrete plinth
            self._core(mb, CORR_D, 0.1)
            n = 18
            w = 4.0 / n
            for s in C.SIDES:
                M = _face(s, 1.9)
                for i in range(n):
                    u0 = -2.0 + i * w
                    col = CORR_L if i % 2 == 0 else "#6f8796"
                    plate(mb, col, u0 + 0.01, 0.6, u0 + w - 0.01, 4.5, 0.0, 0.1, M=M)
                for _ in range(3):
                    u = rng.uniform(-1.8, 1.4)
                    vv = rng.uniform(0.8, 2.6)
                    quad(mb, RUST, u, vv, u + 0.22, vv + rng.uniform(0.8, 1.6), 0.102, M=M)
                plate(mb, CONC[0], -2, 0.0, 2, 0.6, 0.0, 0.1, M=M)
        elif v == "b":
            # rust-red brick, staggered courses, a few missing bricks
            self._core(mb, MORTAR, 0.02)
            for s in C.SIDES:
                M = _face(s, 1.98)
                plate(mb, MORTAR, -2, 0, 2, 4.5, 0, 0.012, M=M)
                rows = 20
                bh = 4.5 / rows
                bw = 0.6
                for j in range(rows):
                    v0 = j * bh
                    u = -2.0 - (bw / 2 if j % 2 else 0.0)
                    while u < 2.0:
                        a, b = max(-2.0, u + 0.03), min(2.0, u + bw - 0.03)
                        if b - a > 0.08 and rng.random() > 0.06:
                            quad(mb, pick(rng, BRICK, 0.07), a, v0 + 0.03, b, v0 + bh - 0.03, 0.02, M=M)
                        u += bw
        else:
            # concrete with three pipe runs per face (teal, mustard, red), flanges and valve wheels
            self._core(mb, CONC[1], 0.15)
            for s in C.SIDES:
                M = _face(s, 1.85)
                for k, u in enumerate((-1.2, 0.0, 1.2)):
                    col = (PIPE_T, PIPE_G, PIPE_R)[(k + C.SIDES.index(s)) % 3]
                    cyl(mb, col, (u, 2.25, 0.0), 0.12, 4.5, seg=12, rot=(-90, 0, 0), center=True, M=M)
                    for vv in (0.8, 2.6, 3.9):
                        cyl(mb, STEEL, (u, vv, 0.0), 0.15, 0.08, seg=12, rot=(-90, 0, 0), center=True, M=M)
                cyl(mb, STEEL_D, (0.0, 3.1, 0.0), 0.12, 4.0, seg=12, rot=(0, 90, 0), center=True, M=M)
                cyl(mb, VALVE_R, (-0.6, 3.1, 0.15), 0.1, 0.04, seg=12, rot=(0, 0, 0), M=M)
                cyl(mb, STEEL, (0.6, 3.1, 0.15), 0.1, 0.05, seg=12, rot=(0, 0, 0), M=M)
        return [mb.build(f"wall_{v}")]

    # ------------------------------------------------------------ doors (cell block with a 2 m opening)
    def door(self, locked):
        name = "door_locked" if locked else "door"
        frame = MB()
        conc = CONC[0]
        box(frame, conc, -2.0, -1.0, -1.0, 1.0, 0.0, C.WALL_H, ch=0.04)
        box(frame, conc, 1.0, 2.0, -1.0, 1.0, 0.0, C.WALL_H, ch=0.04)
        box(frame, conc, -1.0, 1.0, -1.0, 1.0, 3.12, C.WALL_H, ch=0.04)
        for s in (-1.0, 1.0):
            # steel roller housing on the lintel, hazard edge on the jambs
            box(frame, STEEL_D, -1.1, 1.1, s - 0.04, s + 0.04, 3.12, 3.55, ch=0.02)
            box(frame, HAZ_Y, -2.0, -1.8, s - 0.03, s + 0.03, 0.0, 2.5, ch=0.0)
            box(frame, HAZ_Y, 1.8, 2.0, s - 0.03, s + 0.03, 0.0, 2.5, ch=0.0)
        objs = [frame.build(name)]
        leaf = MB()
        slats = 16
        h = 3.1 / slats
        for k in range(slats):
            z0 = k * h
            box(leaf, STEEL if k % 2 == 0 else "#7b858c", -1.0, 1.0, -0.035, 0.035, z0 + 0.01, z0 + h - 0.01, ch=0.0)
        box(leaf, HAZ_Y, -1.0, 1.0, -0.04, 0.04, 0.0, 0.18, ch=0.0)
        leaf_obj = leaf.build("Door", origin=(-1.0, 0.0, 0.0))
        objs.append(leaf_obj)
        if locked:
            lock = MB()
            cyl(lock, STEEL_D, (0.62, -0.1, 1.6), 0.15, 0.1, seg=12, rot=(90, 0, 0), center=True)
            box(lock, BLACK, 0.5, 0.75, -0.2, -0.06, 1.1, 1.45, ch=0.02)
            quad(lock, "#ff6a3a", 0.56, 1.25, 0.69, 1.33, -0.205, mat="M_Emit")
            lock_obj = lock.build("Lock")
            KA.parent_keep(lock_obj, leaf_obj)
            objs.append(lock_obj)
        return objs

    # ------------------------------------------------------------ stairs (steel grating treads, rails)
    def stairs(self, up):
        mb = MB()
        if up:
            # steel catwalk stair rising north to a 2.5 m platform
            for k in range(5):
                y1, y0 = 2.0 - 0.4 * k, 2.0 - 0.4 * (k + 1)
                box(mb, GRATE_L, -1.9, 1.9, y0 + 0.02, y1 - 0.02, 0.0, 0.5 * (k + 1), ch=0.0)
                box(mb, GRATE_D, -2.0, 2.0, y0, y1, 0.0, 0.5 * (k + 1) - 0.1, ch=0.0)
            box(mb, GRATE_D, -2.0, 2.0, -2.0, 0.0, 0.0, 2.5, ch=0.02)
            for x in (-1.9, 1.9):
                cyl(mb, STEEL, (x, 0.9, 0.0), 0.04, 1.1, seg=8)
                cyl(mb, STEEL, (x, -0.8, 0.0), 0.04, 1.1, seg=8)
            return [mb.build("stairs_up")]
        # descent into the basement: concrete treads stepping down north, south half keeps the floor
        plate(mb, CONC[0], -2.0, 0.0, 2.0, 2.0, -0.3, -0.01)
        tile_quads(mb, self.rng("stairs_down"), CONC, -2, 0.0, 2, 2, 0.5, 0.5, d=0.0, gap=0.04)
        for k in range(5):
            y1, y0 = -0.4 * k, -0.4 * (k + 1)
            box(mb, CONC_D, -2.0, 2.0, y0, y1, -3.0, -0.5 * (k + 1), ch=0.02)
            quad(mb, HAZ_Y, -2.0, y1 - 0.08, 2.0, y1, -0.5 * (k + 1) + 0.002)
        return [mb.build("stairs_down")]

    # ------------------------------------------------------------ cell props
    def chest(self):
        body = MB()
        box(body, CRATE, -0.75, 0.75, -0.42, 0.42, 0.0, 0.8, ch=0.03)
        for x in (-0.55, 0.55):
            box(body, STEEL_D, x - 0.05, x + 0.05, -0.44, 0.44, 0.0, 0.84, ch=0.0)
        M = _face("S", 0.42)
        quad(body, HAZ_Y, -0.75, 0.2, 0.75, 0.32, 0.005, M=M)
        quad(body, HAZ_K, -0.75, 0.34, 0.75, 0.38, 0.005, M=M)
        lid = MB()
        box(lid, CRATE_D, -0.77, 0.77, -0.42, 0.42, 0.8, 0.92, ch=0.03)
        return [body.build("chest"), lid.build("Lid", origin=(0.0, 0.42, 0.8))]

    def lore_stone(self):
        """Safety notice board on a steel post: a yellow hazard header and a notice panel."""
        mb = MB()
        box(mb, STEEL_D, -0.5, 0.5, -0.4, 0.4, 0.0, 0.2, ch=0.03)
        cyl(mb, STEEL, (0, 0.0, 0.2), 0.08, 1.0, seg=10)
        box(mb, "#e9e4d2", -0.6, 0.6, -0.12, 0.12, 1.2, 2.2, ch=0.03)
        M = KA.face_matrix("S", 0.12)
        quad(mb, HAZ_Y, -0.6, 1.95, 0.6, 2.2, 0.01, M=M)
        for i in range(3):
            quad(mb, "#3a6f8f", -0.42, 1.5 + 0.2 * i, 0.42 - 0.2 * (i % 2), 1.6 + 0.2 * i, 0.012, M=M)
        return [mb.build("lore_stone")]

    def spring(self):
        """Coolant tap station: a blue water tank on a steel stand, pipe and tap, glowing gauge."""
        mb = MB()
        box(mb, STEEL_D, -0.7, 0.7, -0.5, 0.5, 0.0, 0.25, ch=0.03)
        cyl(mb, "#4f8fb8", (0, 0.0, 0.25), 0.55, 1.35, seg=18)
        cyl(mb, STEEL, (0, 0.0, 1.6), 0.58, 0.08, seg=18)
        cyl(mb, STEEL, (0, -0.55, 0.9), 0.06, 0.1, seg=10, rot=(90, 0, 0), center=True)
        cyl(mb, VALVE_R, (0, -0.7, 0.9), 0.14, 0.05, seg=12, rot=(90, 0, 0), center=True)
        mb.add(KA.disc(0.1, n=12, z=0.0), "#9fe7ff", "M_Emit", M=T((0.0, -0.6, 1.2)))
        return [mb.build("spring")]

    def trap(self):
        """Spiked floor plate with a hazard border, rusted spikes."""
        mb = MB()
        box(mb, CONC_D, -1.4, 1.4, -1.4, 1.4, -0.02, 0.04, ch=0.01)
        for x0, x1, y0, y1 in ((-1.4, -1.15, -1.4, 1.4), (1.15, 1.4, -1.4, 1.4),
                               (-1.4, 1.4, -1.4, -1.15), (-1.4, 1.4, 1.15, 1.4)):
            box(mb, HAZ_Y, x0, x1, y0, y1, 0.04, 0.07, ch=0.0)
        spikes = MB()
        for i in range(9):
            a = 2 * math.pi * i / 9
            r = 0.55 if i % 2 else 0.95
            spikes.add(KA.cone(0.1, 0.5, seg=6), RUST_D, M=T((math.cos(a) * r, math.sin(a) * r, 0.04)))
        return [mb.build("trap"), spikes.build("Spikes")]

    def warp(self):
        """Gear pad: a steel gear ring with teeth and an orange glowing core."""
        mb = MB()
        cyl(mb, STEEL_D, (0, 0, 0), 1.5, 0.06, seg=24)
        for i in range(16):
            a = 2 * math.pi * i / 16
            mb.add(KA.disc(0.14, n=6, z=0.12), STEEL, M=T((math.cos(a) * 1.4, math.sin(a) * 1.4, 0.0)))
        mb.add(KA.disc(1.15, n=28, z=0.07, r_in=0.85), "#ff8a3d", "M_Emit")
        mb.add(KA.disc(0.85, n=28, z=0.075), "#ff9a4d", "M_Emit")
        return [mb.build("warp"), KA.empty("LightAnchor_warp", (0, 0, 0.8))]

    def torch(self):
        """Hanging industrial cage lamp: a wall arm carries a chain and a dome, bulb below (M_Emit)."""
        mb = MB()
        box(mb, STEEL_D, -0.07, 0.07, -0.9, 0.3, 3.3, 3.37, ch=0.0)
        box(mb, STEEL_D, -0.25, 0.25, 0.0, 0.3, 2.9, 3.4, ch=0.02)
        chain(mb, STEEL_D, (0.0, -0.7, 3.3), (0.0, -0.7, 2.75), link_r=0.05, wire=0.014)
        mb.add(KA.lathe([(0.0, 2.84), (0.14, 2.8), (0.42, 2.58), (0.44, 2.52)], seg=14), "#e8862e")
        mb.add(KA.disc(0.44, n=14, z=2.52), "#c46a22")
        sph = KA.uvsphere(0.16, seg=10, rings=6, loc=(0.0, -0.7, 2.44))
        mb.add(sph, LAMP_E, "M_Emit")
        return [mb.build("torch"), KA.empty("LightAnchor", (0, -0.7, 2.3))]

    def decor(self, i):
        rng = self.rng(f"decor_{i}")
        mb = MB()
        if i == 1:
            # conveyor: steel frame, black belt with yellow side rails and rollers, long axis along X
            for x in (-0.55, 0.55):
                for y in (-0.3, 0.3):
                    box(mb, STEEL_D, x - 0.04, x + 0.04, y - 0.04, y + 0.04, 0.0, 0.8, ch=0.0)
            box(mb, BELT, -0.65, 0.65, -0.32, 0.32, 0.78, 0.86, ch=0.01)
            for s in (-0.32, 0.32):
                box(mb, HAZ_Y, -0.66, 0.66, s - 0.03, s + 0.03, 0.86, 0.92, ch=0.0)
            for x in (-0.5, -0.17, 0.17, 0.5):
                cyl(mb, STEEL, (x, 0.0, 0.76), 0.05, 0.6, seg=8, rot=(90, 0, 0), center=True)
        elif i == 2:
            # stacked crates (wood with metal bands)
            box(mb, CRATE, -0.45, 0.45, -0.4, 0.4, 0.0, 0.6, ch=0.02)
            box(mb, CRATE_D, -0.38, 0.38, -0.33, 0.33, 0.6, 1.1, ch=0.02)
            box(mb, CRATE, -0.3, 0.3, -0.28, 0.28, 1.1, 1.5, ch=0.02)
            M = KA.face_matrix("S", 0.4)
            quad(mb, HAZ_Y, -0.3, 0.3, 0.3, 0.45, 0.01, M=M)
        elif i == 3:
            # oil drums: two upright blue, one orange, one lying on its side
            for x, y, col in ((-0.35, -0.05, DRUM_B), (0.35, -0.05, DRUM_O), (0.0, 0.35, DRUM_B)):
                cyl(mb, col, (x, y, 0.0), 0.3, 0.9, seg=14)
                cyl(mb, STEEL_D, (x, y, 0.88), 0.31, 0.04, seg=14)
                cyl(mb, STEEL, (x, y, 0.3), 0.31, 0.04, seg=14)
            cyl(mb, DRUM_O, (-0.15, -0.5, 0.3), 0.3, 0.6, seg=14, rot=(0, 90, 20), center=True)
        elif i == 4:
            # valve station: floor flange, vertical pipe, horizontal branch, red wheel facing -Y
            cyl(mb, STEEL_D, (0, 0, 0), 0.26, 0.12, seg=14)
            cyl(mb, PIPE_T, (0, 0, 0.6), 0.1, 1.2, seg=12)
            cyl(mb, PIPE_T, (0, 0.0, 1.05), 0.09, 0.9, seg=12, rot=(0, 90, 0), center=True)
            cyl(mb, PIPE_G, (0.0, 0.0, 0.8), 0.12, 0.08, seg=12)
            cyl(mb, VALVE_R, (0.0, -0.25, 1.4), 0.2, 0.05, seg=16, rot=(90, 0, 0), center=True)
            cyl(mb, STEEL, (0.0, -0.3, 1.4), 0.05, 0.06, seg=10, rot=(90, 0, 0), center=True)
        elif i == 5:
            # chain hoist: gantry bar on two posts, three chains with hooks hanging to the floor
            for x in (-0.45, 0.45):
                box(mb, STEEL_D, x - 0.05, x + 0.05, -0.1, 0.1, 0.0, 2.6, ch=0.0)
            box(mb, STEEL_D, -0.55, 0.55, -0.12, 0.12, 2.55, 2.65, ch=0.02)
            for x in (-0.25, 0.0, 0.25):
                chain(mb, "#6b7278", (x, 0.0, 2.5), (x, 0.0, 0.5), link_r=0.05, wire=0.014)
                mb.add(KA.disc(0.02, n=4, z=0.0), STEEL, M=T((x, 0.0, 0.42)))
            for x, y in ((0.5, 0.25), (0.62, -0.2)):
                chain(mb, "#6b7278", (x, y, 0.0), (x + 0.3, y + 0.2, 0.0), link_r=0.05, wire=0.014)
        else:
            # gas cylinder rack: steel frame with green and yellow cylinders
            for x in (-0.45, 0.45):
                box(mb, STEEL_D, x - 0.04, x + 0.04, -0.3, 0.3, 0.0, 1.5, ch=0.0)
            box(mb, STEEL_D, -0.5, 0.5, -0.32, -0.26, 1.2, 1.26, ch=0.0)
            for x, col in ((-0.3, GAS_G), (0.0, GAS_Y), (0.3, GAS_G)):
                cyl(mb, col, (x, 0.0, 0.1), 0.14, 1.1, seg=12)
                cyl(mb, STEEL_D, (x, 0.0, 1.2), 0.1, 0.1, seg=10)
        return [mb.build(f"decor_{i}")]

    # ------------------------------------------------------------ overlays (-Y face of a wall block, y -2 .. -2.35)
    def overlay(self, i):
        rng = self.rng(f"overlay_{i}")
        mb = MB()
        M = _face("S", 2.0)
        if i == 1:
            # pipe run with brackets and rust streaks
            for z, col in ((2.4, PIPE_T), (2.7, PIPE_G), (3.0, PIPE_R)):
                cyl(mb, col, (0.0, -2.14, z), 0.09, 3.0, seg=10, rot=(0, 90, 0), center=True)
            for u in (-1.0, 0.0, 1.0):
                box(mb, STEEL_D, u - 0.05, u + 0.05, -2.2, -2.04, 1.9, 3.4, ch=0.0)
            for _ in range(4):
                u = rng.uniform(-1.6, 1.6)
                quad(mb, RUST_D, u, 0.4, u + 0.12, rng.uniform(1.8, 2.6), -0.0, M=M)
        else:
            # cable tray and a hazard sign
            plate(mb, STEEL_D, -1.3, 2.4, 1.3, 2.52, 0.0, 0.24, M=M)
            plate(mb, HAZ_Y, -0.45, 0.9, 0.45, 1.6, 0.0, 0.03, M=M)
            diag_stripes(mb, [HAZ_Y, HAZ_K], -0.45, 0.9, 0.45, 1.6, 0.14, 0.035, M=M)
        return [mb.build(f"overlay_{i}")]

    # ------------------------------------------------------------ boss gate and marker
    def boss_gate(self):
        """Heavy steel press shutter with yellow edges and rivets."""
        mb = MB()
        box(mb, STEEL_D, -2.0, -1.75, -0.3, 0.3, 0.0, 4.5, ch=0.03)
        box(mb, STEEL_D, 1.75, 2.0, -0.3, 0.3, 0.0, 4.5, ch=0.03)
        box(mb, HAZ_Y, -2.0, 2.0, -0.3, 0.3, 4.2, 4.5, ch=0.03)
        for k in range(14):
            z0 = k * 0.3
            box(mb, STEEL if k % 2 == 0 else "#7b858c", -1.75, 1.75, -0.24, 0.24, z0 + 0.02, z0 + 0.28, ch=0.0)
        M = KA.face_matrix("S", 0.24)
        for u in (-1.5, -0.5, 0.5, 1.5):
            for vv in (0.5, 2.4, 3.9):
                mb.add(KA.disc(0.05, n=6, z=0.005), STEEL_D, M=M @ T((u, vv, 0.0)))
        flat_bar(mb, RUST, (-1.4, 3.9), (1.4, 3.9), 0.1, 0.01, M=M)
        return [mb.build("boss_gate"), KA.empty("LightAnchor_gate_L", (-1.65, -0.85, 0.9)),
                KA.empty("LightAnchor_gate_R", (1.65, -0.85, 0.9))]

    def foe_marker(self):
        mb = MB()
        mb.add(KA.disc(1.1, n=28, z=0.0, r_in=0.85), HAZ_Y, "M_Emit")
        mb.add(KA.disc(0.55, n=20, z=0.005), HAZ_K)
        return [mb.build("foe_marker"), KA.empty("Spot_foe", (0, 0, 0))]

    # ------------------------------------------------------------ arena: factory floor with machines
    def arena_floor(self, rng):
        mb = MB()
        n = 48
        for i in range(n):
            a0, a1 = 2 * math.pi * i / n, 2 * math.pi * (i + 1) / n
            col = CONC[0] if i % 2 == 0 else CONC[1]
            mb.add(([(0, 0, 0), (9.2 * math.cos(a0), 9.2 * math.sin(a0), 0),
                     (9.2 * math.cos(a1), 9.2 * math.sin(a1), 0)], [(0, 1, 2)]), col)
        for k in range(16):
            a0 = 2 * math.pi * k / 16
            a1 = a0 + math.pi / 16
            ring = [(8.6 * math.cos(a0), 8.6 * math.sin(a0), 0.004), (9.2 * math.cos(a0), 9.2 * math.sin(a0), 0.004),
                    (9.2 * math.cos(a1), 9.2 * math.sin(a1), 0.004), (8.6 * math.cos(a1), 8.6 * math.sin(a1), 0.004)]
            mb.add((ring, [(0, 1, 2, 3)]), HAZ_Y if k % 2 == 0 else HAZ_K)
        mb.add(KA.disc(1.6, n=40, z=0.004), "#5d5a53")
        mb.add(KA.disc(1.1, n=40, z=0.005), "#ff8a3d", "M_Emit")
        return mb

    def arena_backdrop(self, rng):
        """Machine hall: a corrugated ring wall, press machines and tanks silhouetted, lit windows and stacks."""
        mb = MB()
        R, H, n = 17.0, 9.0, 60
        p = lambda a, z: (R * math.cos(a), R * math.sin(a), z)
        for i in range(n):
            a0, a1 = 2 * math.pi * i / n, 2 * math.pi * (i + 1) / n
            col = CORR_L if i % 2 == 0 else CORR_D
            mb.add(([p(a0, 0), p(a1, 0), p(a1, H), p(a0, H)], [(0, 3, 2, 1)]), col)
        for k in range(12):
            a = 2 * math.pi * k / 12 + 0.15
            x, y = 15.2 * math.cos(a), 15.2 * math.sin(a)
            box(mb, STEEL_D, x - 1.4, x + 1.4, y - 1.4, y + 1.4, 0.0, 3.0 + 1.2 * (k % 3), ch=0.1)
            box(mb, "#e0a22e", x - 1.5, x + 1.5, y - 1.5, y + 1.5, 2.6, 2.9, ch=0.0)
            cyl(mb, RUST_D, (x, y, 0.0), 0.6, 9.0, seg=12)
        mb.add(([(-6.0, 15.0, 1.0), (6.0, 15.0, 1.0), (6.0, 15.0, 5.0), (-6.0, 15.0, 5.0)], [(0, 1, 2, 3)]),
               "#ffb35c", "M_Emit")
        return mb
