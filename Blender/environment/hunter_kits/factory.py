"""Abandoned factory ('factory' tileset).

Look: stained concrete with yellow/black hazard stripes and steel grating, corrugated steel and rust-red brick walls,
mustard/teal/red pipe runs with valves, a steel truss roof with corrugated panels, skylight strips and caged industrial
lamps (M_Emit). Every floor piece carries a `Ceiling` root (roof, trusses, lamps). Props: conveyor, machine press,
oil drums, a pallet cart, crates and containers (KayKit Restaurant / Space Base), cabinets and a dumpster (KayKit
Furniture / City Builder).
"""
import math

import common_a as C
from common_a import HunterKit, MB, KA, T, box, cyl, quad, plate, flat_bar, tile_quads, diag_stripes, chain, pick, \
    grime, tiles_g, ceil_tiles, ceil_rect, hang, cc, join, kit_pal, CEIL, ARENA_CEIL, WALL_H

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
ROOF_D = "#3f4b54"
ROOF_L = "#66778a"
TRUSS = "#6a5a4c"
SKYLIGHT = "#ffe2b0"
LAMP_CAGE = "#2d3237"

PAL = kit_pal("#2a2e33", "#c9ccd0")  # CC0 props: luminance mapped between a dark and a light grey-steel


def _face(side, d):
    return KA.face_matrix(side, d)


def _truss(mb, y, z_bot=4.02, z_top=4.4, col=TRUSS):
    """Steel roof truss across the corridor (X) at y: top and bottom chords and a zig-zag web."""
    box(mb, col, -2.0, 2.0, y - 0.07, y + 0.07, z_top - 0.07, z_top)
    box(mb, col, -2.0, 2.0, y - 0.07, y + 0.07, z_bot, z_bot + 0.07)
    n = 4
    pts = [(-2.0 + 4.0 * k / n, y, z_bot + 0.03 if k % 2 == 0 else z_top - 0.03) for k in range(n + 1)]
    for p, q in zip(pts, pts[1:]):
        mb.add(KA.tube([p, q], 0.035, sides=4), col)


def _lamp(mb, x, y, top=CEIL):
    """Caged industrial lamp hung from the roof: a conical shade, a glowing bulb underneath and a rod."""
    hang(mb, STEEL_D, x, y, top - 0.005, top - 0.5, r=0.012)
    vs, fs = KA.lathe([(0.1, 0.0), (0.34, -0.24)], seg=12)
    mb.add((vs, fs), LAMP_CAGE, M=T((x, y, top - 0.3)))
    vs, fs = KA.disc(0.1, n=10, z=0.0)
    mb.add((vs, [tuple(reversed(f)) for f in fs]), LAMP_E, "M_Emit", M=T((x, y, top - 0.54)))

class FactoryKit(HunterKit):
    TS = "factory"
    WORLD = "#2a1d17"
    SKY = ("#4a2f22", "#14100d")

    # ------------------------------------------------------------ ceilings (Ceiling root, normals down)
    def _ceiling(self, piece):
        rng = self.rng(f"ceiling_{piece}")
        mb = MB()
        ceil_rect(mb, ROOF_D, -2, -2, 2, 2, CEIL)
        # corrugated roof sheets: ribs running along the hall (Y), alternate shades, grimy at the walls
        for k in range(10):
            x = -1.8 + k * 0.4
            col = grime(ROOF_L if k % 2 else "#58687a", low=0.0, corner=0.0, wall_edge=0.3)
            box(mb, col, x - 0.07, x + 0.07, -2.0, 2.0, CEIL - 0.12, CEIL - 0.005, ch=0.0)
        # skylight strip over the centre line: frosted warm glass lit from above (emissive) in steel frames
        box(mb, STEEL_D, -0.42, 0.42, -2.0, 2.0, CEIL - 0.14, CEIL - 0.1, ch=0.0)
        ceil_rect(mb, SKYLIGHT, -0.34, -2.0, 0.34, 2.0, CEIL - 0.16, mat="M_Emit")
        if piece != "floor_c":
            _truss(mb, -2.0)
            _truss(mb, 0.0)
        else:
            _truss(mb, 0.0)
        if piece in ("floor_a", "stairs_down"):
            _lamp(mb, -0.9, -0.9)
            _lamp(mb, 0.9, 0.9)
        elif piece == "floor_b":
            _lamp(mb, 0.0, 0.0)
        else:
            _lamp(mb, -0.9, 1.1)
        # a hanging chain hoist on the truss
        if piece == "floor_c":
            chain(mb, STEEL_D, (1.3, 0.0, 4.0), (1.3, 0.0, 3.3), link_r=0.05, wire=0.012)
            box(mb, RUST_D, 1.2, 1.4, -0.12, 0.12, 3.3, 3.42, ch=0.01)
        return mb.build("Ceiling")

    # ------------------------------------------------------------ floors (flush detail at z = 0) + Ceiling
    def floor(self, v):
        rng = self.rng(f"floor_{v}")
        mb = MB()
        if v == "a":
            # stained concrete slabs with a diagonal yellow/black hazard band across the cell
            plate(mb, CONC_D, -2, -2, 2, 2, -0.3, -0.03)
            tiles_g(mb, rng, CONC, -2, -2, 2, 2, 0.4, 0.4, d=-0.01, gap=0.04, amt=0.06,
                    grime_kw=dict(low=0.0, corner=0.3, wall_edge=0.4))
            for _ in range(7):
                x, y = rng.uniform(-1.6, 1.6), rng.uniform(-1.6, 1.6)
                r = rng.uniform(0.25, 0.5)
                quad(mb, grime(CONC_STAIN, low=0.0, corner=0.0), x - r, y - r * 0.6, x + r, y + r * 0.6, 0.0)
            diag_stripes(mb, [HAZ_Y, HAZ_K], -2, 0.9, 2, 1.5, 0.3, 0.0, mat="M_Toon")
            for k in range(3):   # oil drip marks flush to the slab
                x = rng.uniform(-1.5, 1.5)
                flat_bar(mb, "#2b2a2f", (x, -1.8), (x + 0.15, -1.2 - 0.3 * k), 0.08, 0.002, mat="M_Clear")
        elif v == "b":
            # steel grating: light bars over a dark recess (reads as holes), with a steel nosing frame
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
            for pos in (-2.0, 2.0):   # yellow nosing at the cell edges
                quad(mb, HAZ_Y, pos - 0.1 if pos > 0 else pos, -2, pos if pos > 0 else pos + 0.1, 2, 0.004)
        else:
            # cracked stained concrete with oil puddles (glossy M_Clear sheen) and a faint drain channel
            plate(mb, CONC_D, -2, -2, 2, 2, -0.3, -0.03)
            tiles_g(mb, rng, CONC, -2, -2, 2, 2, 0.5, 0.5, d=-0.01, gap=0.03, amt=0.07,
                    grime_kw=dict(low=0.0, corner=0.3, wall_edge=0.4))
            for _ in range(4):
                x, y = rng.uniform(-1.2, 1.2), rng.uniform(-1.2, 1.2)
                mb.add(KA.disc(rng.uniform(0.35, 0.6), n=14, z=0.002), "#2b2a2f", "M_Clear", M=T((x, y, 0)))
            zig = [(-1.9, -0.6), (-1.2, -0.3), (-0.8, -0.9), (-0.3, -0.5), (0.3, -0.7), (1.0, -0.2), (1.9, -0.5)]
            for p, q in zip(zig, zig[1:]):
                flat_bar(mb, "#5a5650", p, q, 0.04, -0.004)
        return [mb.build(f"floor_{v}"), self._ceiling(f"floor_{v}")]

    # ------------------------------------------------------------ walls
    def _core(self, mb, col, inset):
        mb.add(KA.cbox(2 * (2.0 - inset), 2 * (2.0 - inset), C.WALL_H, ch=0.05, loc=(0, 0, C.WALL_H / 2)),
               grime(col, low=0.4, k=0.6, corner=0.6), "M_Toon")

    def wall(self, v):
        rng = self.rng(f"wall_{v}")
        mb = MB()
        if v == "a":
            # corrugated steel: raised ribs over a recessed core, rust streaks, a concrete plinth
            self._core(mb, CORR_D, 0.1)
            n = 18
            w = 4.0 / n
            for s in C.SIDES:
                M = _face(s, 1.9)
                for i in range(n):
                    u0 = -2.0 + i * w
                    col = grime(CORR_L if i % 2 == 0 else "#6f8796", low=0.5, k=0.7, corner=0.5)
                    plate(mb, col, u0 + 0.01, 0.6, u0 + w - 0.01, 4.5, 0.0, 0.1, M=M)
                for _ in range(3):
                    u = rng.uniform(-1.8, 1.4)
                    vv = rng.uniform(0.8, 2.6)
                    quad(mb, RUST, u, vv, u + 0.22, vv + rng.uniform(0.8, 1.6), 0.102, M=M)
                plate(mb, CONC[0], -2, 0.0, 2, 0.6, 0.0, 0.1, M=M)
                quad(mb, HAZ_Y, -2, 0.6, 2, 0.72, 0.1, M=M)
                for u in (-1.8, 1.8):   # angle-iron corner bars
                    plate(mb, STEEL_D, u - 0.06, 0.6, u + 0.06, 4.5, 0.1, 0.13, M=M)
        elif v == "b":
            # rust-red brick, staggered courses, a few missing bricks, a steel lintel band and a pipe
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
                            quad(mb, grime(pick(rng, BRICK, 0.07), low=0.35, k=0.6, corner=0.4),
                                 a, v0 + 0.03, b, v0 + bh - 0.03, 0.02, M=M)
                        u += bw
                plate(mb, STEEL_D, -2, 3.85, 2, 4.0, 0.0, 0.05, M=M)
                cyl(mb, RUST_D, (-1.2, 0.5, 0.06), 0.06, 0.5, seg=8, rot=(0, 0, 0), M=M)
                cyl(mb, PIPE_G, (0.6, 0.35, 0.09), 0.09, 4.0, seg=10, rot=(-90, 0, 0), M=M)
                for vv in (1.3, 3.1):
                    plate(mb, STEEL_D, 0.5, vv, 0.7, vv + 0.06, 0.09, 0.14, M=M)
        else:
            # concrete with three pipe runs per face (teal, mustard, red), flanges, valve wheels and hazard base
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
                diag_stripes(mb, [HAZ_Y, HAZ_K], -2, 0.0, 2, 0.45, 0.22, 0.02, M=M)
                plate(mb, CONC[0], -2, 0.45, 2, 0.6, 0.0, 0.02, M=M)
        return [mb.build(f"wall_{v}")]
    # ------------------------------------------------------------ decor (stand on the floor, front = -Y)
    def _conveyor(self, mb):
        """Belt conveyor along Y: steel legs, rollers, a black belt between yellow side rails, a motor box."""
        L, W, H = 1.8, 0.7, 0.9
        for x in (-W / 2 + 0.05, W / 2 - 0.05):
            for y in (-L / 2 + 0.1, L / 2 - 0.1):
                box(mb, STEEL_D, x - 0.04, x + 0.04, y - 0.04, y + 0.04, 0.0, H - 0.1, ch=0.0)
            box(mb, HAZ_Y, x - 0.04, x + 0.04, -L / 2, L / 2, H - 0.22, H - 0.12, ch=0.01)
        for k in range(8):
            y = -L / 2 + 0.1 + k * (L - 0.2) / 7
            cyl(mb, GRATE_L, (-W / 2 + 0.05, y, H - 0.14), 0.05, W - 0.1, seg=8, rot=(0, 90, 0), center=True)
        box(mb, BELT, -W / 2 + 0.07, W / 2 - 0.07, -L / 2 + 0.05, L / 2 - 0.05, H - 0.15, H - 0.12, ch=0.0)
        box(mb, DRUM_B, -0.22, 0.22, -L / 2 - 0.02, -L / 2 + 0.35, 0.0, 0.35, ch=0.02)
        cyl(mb, BLACK, (0.0, -L / 2 + 0.19, 0.35), 0.1, 0.03, seg=10, rot=(90, 0, 0), center=True)

    def _press(self, mb):
        """Machine press: a steel base, a column frame, a hydraulic head with a piston and a gauge."""
        box(mb, STEEL_D, -0.5, 0.5, -0.45, 0.45, 0.0, 0.3, ch=0.03)
        box(mb, DRUM_B, -0.42, 0.42, -0.36, 0.36, 0.3, 1.0, ch=0.04)
        for x in (-0.42, 0.42):
            for y in (-0.36, 0.36):
                cyl(mb, STEEL, (x, y, 1.0), 0.05, 1.3, seg=8)
        box(mb, GRATE_L, -0.5, 0.5, -0.45, 0.45, 2.3, 2.55, ch=0.03)
        cyl(mb, STEEL, (0.0, 0.0, 1.5), 0.1, 0.8, seg=10)
        box(mb, RUST_D, -0.15, 0.15, -0.12, 0.12, 2.55, 2.7, ch=0.02)
        cyl(mb, "#cfd6dc", (0.0, -0.45, 0.6), 0.08, 0.04, seg=12, rot=(90, 0, 0), center=True)
        quad(mb, HAZ_Y, -0.3, -0.2, 0.3, -0.12, 0.0, M=KA.face_matrix("S", 0.46))
        quad(mb, "#ffcf7a", -0.12, 0.6, 0.12, 0.72, 0.0, M=KA.face_matrix("S", 0.46), mat="M_Emit")

    def _drums(self, mb, x=0.0, y=0.0, lay=False):
        """Three oil drums (two upright, one on its side) with rolled bands."""
        for k, (dx, dy, col) in enumerate(((-0.35, -0.2, DRUM_B), (0.25, -0.25, DRUM_O), (0.0, 0.3, DRUM_B))):
            cyl(mb, col, (x + dx, y + dy, 0.0), 0.3, 0.9, seg=14)
            for zb in (0.12, 0.78):
                cyl(mb, STEEL_D, (x + dx, y + dy, zb), 0.31, 0.04, seg=14)
            cyl(mb, STEEL, (x + dx, y + dy, 0.9), 0.1, 0.03, seg=8)

    def _cart(self, mb):
        """Pallet / forklift-like cart: a steel chassis, a mast with two forks, a seat and small wheels."""
        box(mb, VALVE_R, -0.6, 0.6, -0.5, 0.7, 0.25, 0.35, ch=0.02)
        box(mb, BLACK, -0.35, 0.35, -0.2, 0.2, 0.35, 0.8, ch=0.03)
        for x in (-0.5, 0.5):
            box(mb, STEEL_D, x - 0.05, x + 0.05, -0.6, -0.55, 0.0, 2.1, ch=0.0)
        box(mb, STEEL_D, -0.5, 0.5, -0.6, -0.55, 2.0, 2.1, ch=0.0)
        for x in (-0.4, 0.4):
            box(mb, HAZ_Y, x - 0.08, x + 0.08, -0.55, 0.95, 0.12, 0.16, ch=0.0)
        for x, y in ((-0.5, -0.45), (0.5, -0.45), (-0.5, 0.5), (0.5, 0.5)):
            cyl(mb, BLACK, (x, y, 0.0), 0.1, 0.08, seg=10, rot=(0, 90, 0), center=True)

    def decor(self, i):
        mb = MB()
        if i == 1:
            self._conveyor(mb)
            return [mb.build("decor_1")]
        if i == 2:
            self._press(mb)
            return [mb.build("decor_2")]
        if i == 3:
            self._drums(mb, -0.1, 0.0)
            return [mb.build("decor_3")]
        if i == 4:
            self._cart(mb)
            return [mb.build("decor_4")]
        if i == 5:
            # stacked crates with a loose lid, and a cargo box (KayKit Restaurant / Space Base)
            return [join("decor_5", [cc("kr", "crate", PAL, loc=(-0.2, 0.0, 0.0), scale=0.85),
                                     cc("kr", "crate_lid", PAL, loc=(-0.2, 0.0, 0.85), scale=0.85),
                                     cc("ks", "cargo_A", PAL, loc=(0.45, -0.2, 0.0), scale=1.6, rz=20.0)])]
        # storage: a dumpster and a tall steel cabinet (KayKit City Builder / Furniture), with a container on top
        return [join("decor_6", [cc("kc", "dumpster", PAL, loc=(-0.25, 0.0, 0.0), scale=2.6, rz=10.0),
                                 cc("kf", "cabinet_small", PAL, loc=(0.7, -0.2, 0.0), scale=1.3, rz=-10.0)])]

    # ------------------------------------------------------------ overlays (hug the -Y face of a wall block: y -2..-2.35)
    def overlay(self, i):
        rng = self.rng(f"overlay_{i}")
        mb = MB()
        M = _face("S", 2.0)
        if i == 1:
            # pipe bundle with flanges and a hazard plate at the foot of the wall
            for k, (u, col) in enumerate(((-0.4, PIPE_T), (-0.22, PIPE_G), (-0.04, PIPE_R))):
                cyl(mb, col, (u, 0.0, 0.2), 0.08, 3.6, seg=10, rot=(0, 0, 0), M=M)
                cyl(mb, STEEL, (u, 1.2, 0.2), 0.1, 0.05, seg=10, rot=(0, 0, 0), M=M)
            plate(mb, STEEL_D, -0.8, 0.0, 0.25, 0.05, 0.0, 0.2, M=M)
            plate(mb, HAZ_Y, 0.4, 0.0, 0.9, 0.5, 0.0, 0.03, M=M)
            for _ in range(4):
                x = rng.uniform(-1.0, 1.0)
                s = rng.uniform(0.1, 0.2)
                mb.add(KA.rock(rng, s, s, s * 0.7, n=9, flat=0.3), C.pick(rng, ["#6e6a62", "#7d7870"]),
                       M=T((x, -2.2, 0.0)))
        else:
            # electric box on the wall with a warning sticker, and a rusted gauge
            plate(mb, "#5d6b74", -0.5, 1.2, 0.5, 2.0, 0.0, 0.25, M=M)
            quad(mb, HAZ_Y, -0.35, 1.5, 0.35, 1.75, 0.26, M=M)
            cyl(mb, "#c9ccd0", (0.0, 2.3, 0.0), 0.2, 0.12, seg=14, rot=(0, 0, 0), M=M)
            quad(mb, "#ffcf7a", -0.1, 2.25, 0.1, 2.35, 0.13, M=M, mat="M_Emit")
            plate(mb, RUST_D, -1.6, 0.0, -1.2, 2.6, 0.0, 0.03, M=M)
        return [mb.build(f"overlay_{i}")]
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

    # ------------------------------------------------------------ arena: machine hall stage (battle camera framing as subway)
    def arena_floor(self, rng):
        """Factory floor: worn concrete slabs with cracks, oil stains and grating patches; no ring or radial marking."""
        mb = MB()
        R = 17.5
        tiles_g(mb, rng, CONC, -R, -R, R, R, 1.5, 1.5, d=0.0, gap=0.05, amt=0.07,
                grime_kw=dict(low=0.0, corner=0.0))
        for k in range(5):   # steel grating patches over a pit
            x0, y0 = -6.5 + 3.0 * k, 10.5
            for i in range(4):
                quad(mb, GRATE_L, x0 + 0.1 * i, y0, x0 + 0.1 * i + 0.06, y0 + 1.8, 0.004)
            quad(mb, GRATE_D, x0, y0 - 0.1, x0 + 2.2, y0 + 1.9, 0.002)
        mb.add(KA.disc(0.9, n=40, z=0.002, r_in=0.84), "#7a756c")   # faint centre mark only
        for _ in range(9):
            x, y = rng.uniform(-14, 14), rng.uniform(-14, 14)
            if math.hypot(x, y) < 9.6 or math.hypot(x, y) > 17:
                continue
            mb.add(KA.disc(rng.uniform(0.4, 0.9), n=12, z=0.003), "#3b3a3c", M=T((x, y, 0)))
        for _ in range(16):
            x, y = rng.uniform(-8, 8), rng.uniform(-8, 8)
            if 1.5 < math.hypot(x, y) < 8.5:
                flat_bar(mb, "#2e2d30", (x, y), (x + rng.uniform(-1.2, 1.2), y + rng.uniform(-1.2, 1.2)), 0.04, 0.004)
        for x0 in (-9.0, 0.0, 9.0):                                  # painted aisle lines, grey-white, worn
            flat_bar(mb, "#c9c7bf", (x0 - 0.05, 2.5), (x0 + 0.05, 14.0), 0.1, 0.004)
        for _ in range(8):                                           # dark oil puddles (opaque)
            x, y = rng.uniform(-12, 12), rng.uniform(-10, 14)
            if math.hypot(x, y) < 16.5:
                mb.add(KA.disc(rng.uniform(0.35, 0.8), n=14, z=0.004), "#2a2a2e", M=T((x, y, 0)))
        for _ in range(4):                                           # rust-brown patches on the concrete
            x, y = rng.uniform(-12, 12), rng.uniform(-6, 14)
            if math.hypot(x, y) < 16.5:
                mb.add(KA.disc(rng.uniform(0.5, 1.2), n=14, z=0.003), "#7d6a58", M=T((x, y, 0)))
        return mb

    def _catwalk(self, mb, y=10.6, z=3.3):
        """Steel catwalk along X behind the enemies: grating deck, handrails, columns down to the floor."""
        sub = MB()
        box(sub, GRATE_D, -13.0, 13.0, y - 0.7, y + 0.7, z - 0.1, z, ch=0.0)
        for i in range(27):
            x = -13.0 + i
            quad(sub, GRATE_L, x + 0.1, y - 0.66, x + 0.2, y + 0.66, z + 0.002)
        for yy in (y - 0.7, y + 0.7):
            box(sub, STEEL, -13.0, 13.0, yy - 0.03, yy + 0.03, z, z + 1.0, ch=0.0)
            for x in range(-13, 14, 2):
                cyl(sub, STEEL, (x, yy, z), 0.03, 1.0, seg=6)
        for x in (-12.5, -4.0, 4.0, 12.5):
            box(sub, STEEL_D, x - 0.12, x + 0.12, y - 0.12, y + 0.12, 0.0, z, ch=0.0)
            box(sub, STEEL_D, x - 0.3, x + 0.3, y - 0.2, y + 0.2, z - 0.1, z, ch=0.0)
        for x in (-6.0, 6.0):   # ladder rails from the floor up to the deck, with rungs
            for side in (-0.25, 0.25):
                cyl(sub, STEEL, (x + side, y + 0.7 + 0.1, 0.0), 0.03, z, seg=6)
            for k in range(int(z / 0.4)):
                box(sub, STEEL, x - 0.25, x + 0.25, y + 0.7 + 0.08, y + 0.7 + 0.12, 0.2 + 0.4 * k, 0.24 + 0.4 * k, ch=0.0)
        mb.extend(sub)

    def arena_backdrop(self, rng):
        """Hall ring: corrugated steel with grime, steel girts, lit high windows, I-beam columns."""
        mb = MB()
        R, H, n = 17.0, ARENA_CEIL, 56
        p = lambda a, z: (R * math.cos(a), R * math.sin(a), z)
        for i in range(n):
            a0, a1 = 2 * math.pi * i / n, 2 * math.pi * (i + 1) / n
            base = CORR_L if i % 2 == 0 else "#6f8796"
            mb.add(([p(a0, 0), p(a1, 0), p(a1, H - 0.5), p(a0, H - 0.5)], [(0, 3, 2, 1)]),
                   grime(base, low=0.9, k=0.6, corner=0.0))
            mb.add(([p(a0, H - 0.5), p(a1, H - 0.5), p(a1, H), p(a0, H)], [(0, 3, 2, 1)]), STEEL_D)
        for z in (3.0, 6.2):
            for i in range(n):
                a0, a1 = 2 * math.pi * i / n, 2 * math.pi * (i + 1) / n
                mb.add(([p(a0, z), p(a1, z), p(a1, z + 0.12), p(a0, z + 0.12)], [(0, 3, 2, 1)]), STEEL_D)
        for k in range(10):
            a = 2 * math.pi * k / 10 + 0.15
            r = R - 0.05
            mb.add(([(r * math.cos(a - 0.1), r * math.sin(a - 0.1), 6.6), (r * math.cos(a + 0.1), r * math.sin(a + 0.1), 6.6),
                     (r * math.cos(a + 0.1), r * math.sin(a + 0.1), 7.7), (r * math.cos(a - 0.1), r * math.sin(a - 0.1), 7.7)],
                    [(0, 3, 2, 1)]), SKYLIGHT, "M_Emit")
        for k in range(12):
            a = 2 * math.pi * k / 12 + 0.12
            x, y = (R - 0.6) * math.cos(a), (R - 0.6) * math.sin(a)
            box(mb, STEEL_D, x - 0.3, x + 0.3, y - 0.3, y + 0.3, 0.0, H - 0.1, ch=0.02)
        self._catwalk(mb, y=9.6)
        return mb

    def arena_ceiling(self, rng):
        """Machine-hall roof over the whole arena: corrugated ribs, steel trusses, skylights and caged lamps."""
        mb = MB()
        R = 16.6
        for k in range(30):
            x = -17.4 + k * 1.2
            half = math.sqrt(max(R * R - x * x, 1.0))
            col = grime(ROOF_L if k % 2 else "#58687a", low=0.0, corner=0.0)
            box(mb, col, x - 0.08, x + 0.08, -half, half, ARENA_CEIL - 0.3, ARENA_CEIL - 0.005, ch=0.0)
        for y in (-12.0, -6.0, 0.0, 6.0, 12.0):
            half = math.sqrt(max(R * R - y * y, 1.0))
            box(mb, TRUSS, -half, half, y - 0.1, y + 0.1, ARENA_CEIL - 0.25, ARENA_CEIL - 0.13, ch=0.0)
            box(mb, TRUSS, -half, half, y - 0.1, y + 0.1, ARENA_CEIL - 1.0, ARENA_CEIL - 0.9, ch=0.0)
            n = 12
            pts = [(-half + 2 * half * k / n, y, ARENA_CEIL - (0.95 if k % 2 == 0 else 0.25)) for k in range(n + 1)]
            for p, q in zip(pts, pts[1:]):
                mb.add(KA.tube([p, q], 0.07, sides=4), TRUSS)
        for x in (-6.0, 0.0, 6.0):
            half = math.sqrt(max(R * R - x * x, 1.0))
            box(mb, STEEL_D, x - 0.4, x + 0.4, -half, half, ARENA_CEIL - 0.34, ARENA_CEIL - 0.28, ch=0.0)
            ceil_rect(mb, SKYLIGHT, x - 0.3, -half, x + 0.3, half, ARENA_CEIL - 0.36, mat="M_Emit")
        for x, y in ((-7.0, 3.0), (7.0, 3.0), (-7.0, 9.0), (7.0, 9.0), (0.0, 6.0)):
            _lamp(mb, x, y, top=ARENA_CEIL)
        return mb

    def arena_props(self, rng):
        """Machines, conveyors, crates and containers. Enemy side (y > 0) is dense (press, conveyors, drums, stacks),
        the party side stays sparse."""
        mb = MB()
        out = []
        for x, y, rz, kind in ((-8.5, 8.4, 90.0, "conv"), (-2.5, 9.0, 90.0, "conv"), (4.0, 8.6, 90.0, "conv"),
                               (-11.0, 6.6, 0.0, "press"), (10.8, 6.4, 0.0, "press"), (-6.2, 6.0, 0.0, "press"),
                               (6.4, 6.2, 0.0, "press"), (-4.4, 7.4, 0.0, "drums"), (4.6, 6.8, 0.0, "drums"),
                               (-11.4, 2.6, 0.0, "drums"), (11.2, 2.4, 0.0, "cart"), (-9.6, -6.6, 0.0, "cart")):
            sub = MB()
            if kind == "conv":
                self._conveyor(sub)
            elif kind == "press":
                self._press(sub)
            elif kind == "drums":
                self._drums(sub, 0.0, 0.0)
            else:
                self._cart(sub)
            mb.extend(C.place_mb(sub, T((x, y, 0), (0, 0, rz))))
        for x, y, rz in ((-12.4, 9.8, 0.0), (12.2, 10.2, 20.0), (-5.2, 10.6, -10.0), (1.8, 6.6, 0.0)):
            out.append(cc("kr", "crate", PAL, loc=(x, y, 0), rz=rz, scale=1.6))
            out.append(cc("kr", "crate_lid", PAL, loc=(x, y, 1.6), rz=rz, scale=1.6))
        for x, y, rz in ((-13.0, 6.4, 90.0), (13.0, 7.0, 90.0), (-9.2, 9.9, 0.0)):
            out.append(cc("ks", "containers_A", PAL, loc=(x, y, 0), rz=rz, scale=3.0))
        out.append(cc("kc", "dumpster", PAL, loc=(-9.6, -8.4, 0), rz=10.0, scale=2.6))
        # two storage silos on the enemy side: the tall element of the backdrop (about 5.5 m)
        silo = MB()
        for x, y in ((-12.8, 10.0), (12.6, 10.4)):
            cyl(silo, STEEL, (x, y, 0.0), 1.1, 5.4, seg=16)
            for z in (1.2, 2.5, 3.8, 5.0):
                cyl(silo, STEEL_D, (x, y, z), 1.14, 0.1, seg=16)
            cyl(silo, STEEL_D, (x, y, 5.4), 1.1, 0.35, seg=16)
        out.append(silo.build("arena_silos"))
        out.append(mb.build("arena_props"))
        return out
