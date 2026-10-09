"""Seoul metro station after a gate break ('subway' tileset).

Look: cream subway tiles with a line-2 green band and a navy station-sign band, safety-yellow tactile edge, grey
platform tiles, rails and sleepers in the tunnel variant. Ceilings: grey acoustic panels with recessed fluorescent
strips, cable trays and hanging station signs (`Ceiling` root object on every floor piece). Walls: grime in the lower
40 cm and the corners, corner pilasters with line-colour bands, route-map and ad lightboxes, conduits. Props: ticket
gates, a vending machine, a broken escalator, a bench and litter (KayKit City Builder), a station number pillar.
"""
import math

import common_a as C
from common_a import HunterKit, MB, KA, T, box, cyl, quad, plate, flat_bar, tile_quads, grime, tiles_g, \
    ceil_tiles, ceil_rect, hang, cc, join, kit_pal, pick, CEIL, ARENA_CEIL, SHELL, WALL_H

TILE = ["#f7f5ee", "#efede5", "#fbfaf6"]          # cream-white glossy wall tiles
GROUT = "#c9cbcb"                                  # thin light-grey wall grout
FLOOR_GROUT = "#b4b2aa"
TILE_GAP = 0.0045                                  # joint = 2 x gap = 0.009 m
LINE2 = "#1aa35a"
YELLOW = "#ffc91a"
YELLOW_D = "#d99a00"
PLAT = ["#ddd7c8", "#d2ccbd", "#e6e0d2"]           # light grey-beige floor tiles
STEEL = "#a2aab2"
STEEL_D = "#5b646c"
STEEL_G = "#8d959c"
DARK = "#2e3338"
VIOLET = "#a25bff"
VIOLET_E = "#cf9bff"
WOOD = "#8a5e3a"
GRAVEL = ["#4f4d4a", "#5a5854", "#45433f"]
RUBBLE = ["#8a857a", "#9b968a", "#716d65"]
NAVY = "#1f3d6b"
ORANGE = "#f39a2c"
BLUE = "#2b74d0"
RED = "#d8453b"
WHITE = "#f5f4ef"
SKIRT = "#4d5257"
CAP = "#d3cdbd"
CAP_D = "#a9a392"
CEIL_TILE = ["#e3e6e9", "#d9dcdf", "#eceef0"]     # acoustic ceiling panels
PLENUM = "#3a3f46"
LIGHT = "#fff9e8"
CONC_T = "#6d7177"                                 # tunnel concrete (floor_c ceiling)
PAPER = "#f2efe4"
TRAIN_W = "#eef1f2"
TRAIN_R = "#c9ced3"
TRAIN_STEEL = "#9aa1a8"
BOGIE = "#3d434a"
RAIL_C = "#8e949b"
WOOD_TRACK = "#6b4a30"

# CC0 props (KayKit City Builder) recoloured to the station: luminance mapped between two greys
PAL = kit_pal("#2b3138", "#d9dde2")


def _front(d):
    """Face matrix of the -Y (S) face pushed out by d."""
    return KA.face_matrix("S", d)


def _front_side(side):
    """Wall-shell face matrix (details sit on the SHELL plane and reach +-2.0)."""
    return KA.face_matrix(side, SHELL)


class SubwayKit(HunterKit):
    TS = "subway"
    WORLD = "#1b2226"
    SKY = ("#2b1f4a", "#0c0a17")

    # ------------------------------------------------------------ ceilings (Ceiling root, normals down)
    def _ceiling(self, piece):
        rng = self.rng(f"ceiling_{piece}")
        mb = MB()
        tunnel = piece == "floor_c"
        base_tiles = CONC_T if tunnel else None
        ceil_rect(mb, PLENUM, -2, -2, 2, 2, CEIL)                  # dark plenum shows in the joints
        if tunnel:
            # bare tunnel concrete with two steel bolt bands across the corridor
            ceil_rect(mb, CONC_T, -2, -2, 2, 2, CEIL - 0.004)
            for y in (-1.0, 1.0):
                ceil_rect(mb, STEEL_D, -2, y - 0.05, 2, y + 0.05, CEIL - 0.006)
        else:
            ceil_tiles(mb, rng, CEIL_TILE, -2, -2, 2, 2, CEIL - 0.005, 0.6, gap=0.025,
                       grime_kw=dict(low=0.0, corner=0.4, wall_edge=0.35))
        # recessed fluorescent strips along the corridor (Y) with steel housings
        for x in (-0.9, 0.9):
            C.box(mb, STEEL_G, x - 0.27, x + 0.27, -2.0, 2.0, CEIL - 0.04, CEIL - 0.005, ch=0.0)
            ceil_rect(mb, LIGHT, x - 0.22, -2.0, x + 0.22, 2.0, CEIL - 0.045, mat="M_Emit")
        # cable tray (steel U with cables) hung on rods, runs along Y at x = +-1.55
        for x in (-1.55, 1.55):
            ceil_rect(mb, STEEL, x - 0.2, -2.0, x + 0.2, 2.0, CEIL - 0.2)
            for side in (-1, 1):
                C.box(mb, STEEL_G, x + side * 0.2 - 0.012, x + side * 0.2 + 0.012, -2.0, 2.0, CEIL - 0.2, CEIL - 0.13, ch=0.0)
            for k, cab in enumerate((DARK, RED, YELLOW)):   # three cables lying in the tray
                cyl(mb, cab, (x - 0.12 + 0.12 * k, -2.0, CEIL - 0.19), 0.018, 4.0, seg=6, rot=(-90, 0, 0))
            for y in (-1.5, 0.0, 1.5):
                hang(mb, STEEL_D, x - 0.18, y, CEIL - 0.2, CEIL - 0.005, r=0.011)
                hang(mb, STEEL_D, x + 0.18, y, CEIL - 0.2, CEIL - 0.005, r=0.011)
        if piece in ("floor_b", "stairs_down"):
            # hanging station sign: navy board on two rods, white glyph blocks, green line band
            for x in (-0.7, 0.7):
                hang(mb, DARK, x, 0.0, CEIL - 0.005, 3.75, r=0.01)
            box(mb, NAVY, -0.85, 0.85, -0.06, 0.06, 3.3, 3.75, ch=0.0)
            for k, (u0, u1) in enumerate(((-0.72, -0.25), (-0.15, 0.3), (0.4, 0.72))):
                mb.add(([(u0, -0.065, 3.55), (u1, -0.065, 3.55), (u1, -0.065, 3.66), (u0, -0.065, 3.66)],
                        [(0, 1, 2, 3)]), WHITE if k != 1 else LINE2)
            mb.add(([(-0.8, -0.065, 3.4), (0.8, -0.065, 3.4), (0.8, -0.065, 3.46), (-0.8, -0.065, 3.46)],
                    [(0, 1, 2, 3)]), LINE2)
        return mb.build("Ceiling")

    # ------------------------------------------------------------ floors (flush detail at z = 0) + Ceiling
    def floor(self, v):
        rng = self.rng(f"floor_{v}")
        mb = MB()
        if v == "a":
            # platform tiles with the yellow tactile safety line; grime strip along both walls
            plate(mb, FLOOR_GROUT, -2, -2, 2, 2, -0.3, -0.03)
            tiles_g(mb, rng, PLAT, -2, -2, 2, 2, 0.4, 0.4, d=-0.01, gap=0.004,
                    skip=lambda cx, cy: 0.8 < cy < 1.2, grime_kw=dict(low=0.0, corner=0.4, wall_edge=0.45))
            quad(mb, YELLOW, -2, 0.8, 2, 1.2, 0.0)
            for i in range(20):
                u = -1.9 + i * 0.2
                quad(mb, YELLOW_D, u + 0.04, 0.9, u + 0.14, 1.1, 0.002)
            for _ in range(3):   # dropped ticket and wrapper litter, flush
                x, y = rng.uniform(-1.5, 1.5), rng.uniform(-1.6, 1.6)
                if 0.7 < y < 1.3:
                    continue
                quad(mb, PAPER, x, y, x + 0.09, y + 0.05, 0.003)
        elif v == "b":
            # plain platform slabs with a violet gate crack and a dark drain grate
            plate(mb, FLOOR_GROUT, -2, -2, 2, 2, -0.3, -0.03)
            tiles_g(mb, rng, PLAT, -2, -2, 2, 2, 0.4, 0.4, d=-0.01, gap=0.004,
                    grime_kw=dict(low=0.0, corner=0.4, wall_edge=0.45))
            zig = [(-1.8, -1.6), (-1.2, -1.1), (-0.8, -0.45), (-0.3, -0.5), (0.2, 0.2), (0.7, 0.35), (1.3, 1.1),
                   (1.8, 1.4)]
            for p, q in zip(zig, zig[1:]):
                flat_bar(mb, VIOLET_E, p, q, 0.07, 0.0, mat="M_Emit")
            quad(mb, "#7f7b70", 0.1, -1.4, 1.2, -0.8, -0.005)
            for k in range(4):   # drain grate
                quad(mb, DARK, 1.2, -1.85 + 0.2 * k, 1.85, -1.73 + 0.2 * k, -0.004)
        else:
            # tunnel: gravel bed, sleepers across, two rails along the corridor (Y), a puddle
            plate(mb, "#3b3a37", -2, -2, 2, 2, -0.3, -0.03)
            tiles_g(mb, rng, GRAVEL, -2, -2, 2, 2, 0.25, 0.25, d=-0.01, gap=0.02, amt=0.1,
                    grime_kw=dict(low=0.0, corner=0.3, wall_edge=0.5))
            for i in range(7):
                v0 = -1.9 + i * 0.6
                quad(mb, WOOD, -1.95, v0, 1.95, v0 + 0.26, -0.005)
            for u in (-0.72, 0.72):
                quad(mb, STEEL, u - 0.06, -2.0, u + 0.06, 2.0, 0.0)
                quad(mb, "#d6dde4", u - 0.02, -2.0, u + 0.01, 2.0, 0.003)
            mb.add(KA.disc(0.7, n=16, z=0.001), "#1f2a30", "M_Clear", M=T((1.2, 1.2, 0)))
        return [mb.build(f"floor_{v}"), self._ceiling(f"floor_{v}")]

    # ------------------------------------------------------------ walls
    def _face(self, mb, rng, s, d0, v):
        """One wall face: tiles or wall variant details. d0 = core distance of the face (pilasters stand 0.15 m out)."""
        M = KA.face_matrix(s, d0)
        plate(mb, GROUT, -2, 0, 2, 4.5, 0, 0.012, M=M)
        band = (lambda cx, cy: 1.0 < cy < 1.25 or cy < 0.25) if v == "a" else \
               (lambda cx, cy: cy < 0.25 or (-1.5 < cx < 1.5 and 1.25 < cy < 3.6))
        tiles_g(mb, rng, TILE, -2, 0.0, 2, 4.5, 0.5, 0.25, d=0.02, M=M, gap=TILE_GAP, amt=0.03,
                skip=band, grime_kw=dict(low=0.4, k=0.6, corner=0.55))
        quad(mb, SKIRT, -2, 0.0, 2, 0.25, 0.02, M=M, mat="M_Toon")
        # cornice band where the wall meets the ceiling, and the station sign band with its light tube
        plate(mb, CAP_D, -2, 4.36, 2, 4.5, 0.0, 0.02, M=M)
        plate(mb, STEEL_D, -1.9, 3.6, 1.9, 4.04, 0.02, 0.035, M=M)
        plate(mb, NAVY, -1.82, 3.66, 1.82, 3.98, 0.035, 0.05, M=M)
        for k, (u0, u1) in enumerate(((-1.6, -0.9), (-0.7, 0.2), (0.4, 1.3), (1.45, 1.75))):
            quad(mb, "#ffffff" if k % 2 == 0 else LINE2, u0, 3.74, u1, 3.92, 0.055, M=M)
        plate(mb, STEEL, -1.6, 4.12, 1.6, 4.26, 0.02, 0.03, M=M)
        quad(mb, "#fff9e8", -1.55, 4.15, 1.55, 4.22, 0.04, M=M, mat="M_Emit")
        if v == "a":
            quad(mb, LINE2, -2, 1.0, 2, 1.25, 0.02, M=M)
            zig = [(-1.85, 0.45), (-1.4, 0.7), (-1.1, 0.5), (-0.7, 0.85)]
            for p, q in zip(zig, zig[1:]):
                flat_bar(mb, VIOLET_E, p, q, 0.05, 0.03, M=M, mat="M_Emit")
        elif v == "b":
            # route-map board (navy) with a yellow header and coloured lines
            plate(mb, STEEL_D, -1.55, 1.3, 1.55, 3.6, 0.02, 0.04, M=M)
            plate(mb, NAVY, -1.45, 1.4, 1.45, 3.5, 0.04, 0.05, M=M)
            quad(mb, YELLOW, -1.45, 3.1, 1.45, 3.5, 0.06, M=M)
            lines = (([(-1.1, 1.95), (0.0, 1.95), (0.0, 2.7), (1.1, 2.7)], LINE2),
                     ([(-1.1, 2.7), (-0.4, 2.7), (-0.4, 2.25), (0.8, 2.25)], ORANGE),
                     ([(-0.8, 1.65), (1.0, 1.65)], BLUE))
            for pts, col in lines:
                for p, q in zip(pts, pts[1:]):
                    flat_bar(mb, col, p, q, 0.1, 0.07, M=M)
                for p in pts:
                    mb.add(KA.disc(0.075, n=12, z=0.075), "#ffffff", M=M @ T((p[0], p[1], 0.0)))
        else:
            # backlit ad lightboxes (emissive poster blocks in steel frames)
            plate(mb, STEEL_D, -1.55, 1.3, 1.55, 3.6, 0.02, 0.04, M=M)
            plate(mb, "#2d5d8c", -1.45, 1.4, 1.45, 3.5, 0.04, 0.05, M=M, mat="M_Emit")
            quad(mb, "#ff7fb0", -1.25, 2.6, 0.0, 3.3, 0.06, M=M, mat="M_Emit")
            quad(mb, "#58e0d0", 0.1, 1.6, 1.25, 2.9, 0.06, M=M, mat="M_Emit")
            quad(mb, "#ffd45a", -1.25, 1.6, -0.1, 2.4, 0.06, M=M, mat="M_Emit")
            mb.add(KA.disc(0.22, n=20, z=0.065), "#fff6e6", M=M @ T((0.55, 2.95, 0.0)), mat="M_Emit")
        if v != "a":
            # corner pilasters with line-colour bands and a conduit down the middle of the face
            for u in (-1.82, 1.82):
                mb.add(KA.prism(KA.rect_poly(u - 0.16, 0.0, u + 0.16, 4.36), 0.0, 0.15), CAP, M=M)
                for zb, col in ((1.0, LINE2), (1.25, ORANGE), (2.45, BLUE)):
                    plate(mb, col, u - 0.165, zb, u + 0.165, zb + 0.12, 0.13, 0.15, M=M, mat="M_Toon")
                plate(mb, STEEL_D, u - 0.2, 0.0, u + 0.2, 0.18, 0.0, 0.15, M=M)
            cyl(mb, STEEL_G, (0.95, 0.25, 0.02), 0.045, 3.95, seg=8, rot=(-90, 0, 0), M=M)

    def wall(self, v):
        rng = self.rng(f"wall_{v}")
        d0 = SHELL if v == "a" else 1.85
        mb = MB()
        mb.add(KA.cbox(2 * d0, 2 * d0, WALL_H, ch=0.05, loc=(0, 0, WALL_H / 2)),
               grime(CAP, low=0.4, k=0.6, corner=0.6), "M_Toon")
        for s in C.SIDES:
            self._face(mb, rng, s, d0, v)
        return [mb.build(f"wall_{v}")]

    # ------------------------------------------------------------ doors (door block: 4 m wide, 2 m deep, 2 m arch)
    def door(self, locked):
        name = "door_locked" if locked else "door"
        frame = MB()
        cream = "#d8d3c4"
        box(frame, cream, -2.0, -1.0, -1.0, 1.0, 0.0, WALL_H, ch=0.05)
        box(frame, cream, 1.0, 2.0, -1.0, 1.0, 0.0, WALL_H, ch=0.05)
        box(frame, cream, -1.0, 1.0, -1.0, 1.0, 3.12, WALL_H, ch=0.05)
        for y in (-1.0, 1.0):
            for x0, x1 in ((-1.05, -0.95), (0.95, 1.05)):
                box(frame, STEEL, x0, x1, y - 0.03, y + 0.03, 0.0, 3.14, ch=0.0)
            box(frame, STEEL, -1.05, 1.05, y - 0.03, y + 0.03, 3.08, 3.14, ch=0.0)
        for s in ("S", "N"):
            M = KA.face_matrix(s, 1.0)
            quad(frame, "#27c46b", -0.6, 3.6, 0.6, 4.1, 0.01, M=M, mat="M_Emit")
            quad(frame, LINE2, -0.5, 1.0, 0.5, 1.12, 0.01, M=M)
        objs = [frame.build(name)]
        # screen door: glass panes in a steel frame, hinged on the -X jamb (leaf coordinates in world X)
        leaf = MB()
        for x0, x1, z0, z1 in ((-1.0, -0.94, 0.0, 3.1), (0.94, 1.0, 0.0, 3.1), (-1.0, 1.0, 3.0, 3.1),
                                (-1.0, 1.0, 0.0, 0.1), (-0.03, 0.03, 0.0, 3.1)):
            box(leaf, STEEL_D, x0, x1, -0.04, 0.04, z0, z1, ch=0.0)
        glass = "#a7e6ea"
        for x0, x1 in ((-0.94, -0.03), (0.03, 0.94)):
            quad_pts = [(x0, 0.0, 0.1), (x1, 0.0, 0.1), (x1, 0.0, 3.0), (x0, 0.0, 3.0)]
            leaf.add((quad_pts, [(0, 1, 2, 3)]), glass, "M_Clear")
            leaf.add((quad_pts, [(0, 3, 2, 1)]), glass, "M_Clear")
        leaf_obj = leaf.build("Door", origin=(-1.0, 0.0, 0.0))
        objs.append(leaf_obj)
        if locked:
            lock = MB()
            box(lock, DARK, 0.42, 0.68, -0.13, -0.04, 1.15, 1.75, ch=0.02)
            quad(lock, "#3cff8a", 0.48, 1.52, 0.62, 1.6, -0.135, mat="M_Emit")
            quad(lock, "#ff5a4a", 0.48, 1.36, 0.62, 1.42, -0.135, mat="M_Emit")
            lock_obj = lock.build("Lock")
            KA.parent_keep(lock_obj, leaf_obj)
            objs.append(lock_obj)
        return objs

    # ------------------------------------------------------------ stairs
    def stairs(self, up):
        mb = MB()
        if up:
            # station stairs rising north (-Y) from the floor onto a 2.5 m landing
            for k in range(5):
                y1, y0 = 2.0 - 0.4 * k, 2.0 - 0.4 * (k + 1)
                box(mb, "#cfcabb", -2.0, 2.0, y0, y1, 0.0, 0.5 * (k + 1), ch=0.03)
                quad(mb, YELLOW, -2.0, y1 - 0.08, 2.0, y1, 0.5 * (k + 1) + 0.002)
            box(mb, "#bdb8aa", -2.0, 2.0, -2.0, 0.0, 0.0, 2.5, ch=0.03)
            tile_quads(mb, self.rng("stairs_up"), PLAT, -2, -2, 2, 0.0, 0.5, 0.5, d=2.503, gap=0.035)
            quad(mb, LINE2, -1.9, -0.9, 1.9, -0.7, 2.502)
            return [mb.build("stairs_up")]
        # station stairs descending north into the cell; the south half keeps the platform floor
        plate(mb, PLAT[0], -2.0, 0.0, 2.0, 2.0, -0.3, -0.01)
        tile_quads(mb, self.rng("stairs_down"), PLAT, -2, 0.0, 2, 2, 0.5, 0.5, d=0.0, gap=0.035)
        for k in range(5):
            y1, y0 = -0.4 * k, -0.4 * (k + 1)
            box(mb, "#b7b2a4", -2.0, 2.0, y0, y1, -3.0, -0.5 * (k + 1), ch=0.02)
            quad(mb, YELLOW, -2.0, y1 - 0.08, 2.0, y1, -0.5 * (k + 1) + 0.002)
        return [mb.build("stairs_down")]

    # ------------------------------------------------------------ cell props (front = -Y, back = +Y toward a wall)
    def chest(self):
        body = MB()
        box(body, "#6f7f5b", -0.75, 0.75, -0.42, 0.42, 0.0, 0.8, ch=0.04)
        for x0, x1 in ((-0.76, -0.66), (0.66, 0.76)):
            box(body, STEEL_D, x0, x1, -0.44, 0.44, 0.0, 0.84, ch=0.0)
        M = _front(0.42)
        quad(body, YELLOW, -0.75, 0.18, 0.75, 0.3, 0.005, M=M)
        quad(body, WHITE, -0.4, 0.34, -0.12, 0.62, 0.005, M=M)
        quad(body, "#d64f3e", 0.12, 0.34, 0.4, 0.62, 0.005, M=M)
        lid = MB()
        box(lid, "#7c8c66", -0.77, 0.77, -0.42, 0.42, 0.8, 0.92, ch=0.03)
        quad(lid, YELLOW, -0.77, -0.42, 0.77, -0.3, 0.922)
        return [body.build("chest"), lid.build("Lid", origin=(0.0, 0.42, 0.8))]

    def lore_stone(self):
        mb = MB()
        box(mb, "#e6e3d8", -0.5, 0.5, -0.4, 0.4, 0.0, 1.1, ch=0.04)
        box(mb, LINE2, -0.52, 0.52, -0.42, 0.42, 0.38, 0.5, ch=0.0)
        box(mb, YELLOW, -0.56, 0.56, -0.44, 0.44, 1.9, 2.02, ch=0.02)
        M = _front(0.4)
        plate(mb, STEEL_D, -0.46, 1.1, 0.46, 1.9, -0.01, 0.03, M=M)
        quad(mb, "#7fd6ff", -0.4, 1.16, 0.4, 1.84, 0.035, M=M, mat="M_Emit")
        for i, col in enumerate((LINE2, ORANGE, BLUE)):
            flat_bar(mb, col, (-0.28, 1.5 + 0.12 * i), (0.25, 1.5 + 0.12 * i), 0.05, 0.045, M=M)
        return [mb.build("lore_stone")]

    def spring(self):
        mb = MB()
        box(mb, "#f4f4f0", -0.6, 0.6, -0.7, 0.45, 0.35, 2.0, ch=0.04)
        box(mb, STEEL, -0.6, 0.6, -0.7, 0.45, 0.0, 0.35, ch=0.02)
        M = _front(0.7)
        quad(mb, RED, -0.07, 1.3, 0.07, 1.7, 0.02, M=M)
        quad(mb, RED, -0.2, 1.45, 0.2, 1.55, 0.02, M=M)
        plate(mb, "#7fe0a5", -0.42, 0.45, 0.42, 0.95, -0.01, 0.02, M=M, mat="M_Emit")
        cyl(mb, BLUE, (0.0, 0.0, 2.0), 0.08, 0.1, seg=10)
        return [mb.build("spring")]

    def trap(self):
        mb = MB()
        box(mb, DARK, -1.4, 1.4, -1.4, 1.4, -0.02, 0.04, ch=0.01)
        for x0, x1, y0, y1 in ((-1.4, -1.15, -1.4, 1.4), (1.15, 1.4, -1.4, 1.4),
                               (-1.4, 1.4, -1.4, -1.15), (-1.4, 1.4, 1.15, 1.4)):
            box(mb, YELLOW, x0, x1, y0, y1, 0.04, 0.07, ch=0.0)
        for u in (-0.6, 0.0, 0.6):
            box(mb, VIOLET, u - 0.07, u + 0.07, -0.95, 0.95, 0.07, 0.11, ch=0.0)
        spikes = MB()
        for i in range(8):
            a = 2 * math.pi * i / 8
            spikes.add(KA.cone(0.09, 0.42, seg=6), STEEL_D, M=T((math.cos(a) * 0.95, math.sin(a) * 0.95, 0.04)))
        return [mb.build("trap"), spikes.build("Spikes")]

    def warp(self):
        mb = MB()
        cyl(mb, "#56606a", (0, 0, 0), 1.5, 0.05, seg=28)
        mb.add(KA.disc(1.45, n=28, z=0.06, r_in=1.2), VIOLET, "M_Emit")
        mb.add(KA.disc(1.15, n=28, z=0.065), VIOLET, "M_Clear")
        for i in range(6):
            a = 2 * math.pi * i / 6
            flat_bar(mb, VIOLET_E, (0.0, 0.0), (math.cos(a) * 0.9, math.sin(a) * 0.9), 0.08, 0.07, mat="M_Emit")
        return [mb.build("warp"), KA.empty("LightAnchor_warp", (0, 0, 0.8))]

    def torch(self):
        """Wall-mounted fluorescent lamp: bracket and housing touch the wall at y = +0.3 (cell offset 1.7 m)."""
        mb = MB()
        box(mb, STEEL_D, -0.5, 0.5, 0.0, 0.3, 2.45, 3.25, ch=0.02)
        box(mb, "#dfe3e4", -0.8, 0.8, -0.4, 0.3, 2.55, 3.15, ch=0.03)
        quad(mb, "#eafff4", -0.7, 2.62, 0.7, 3.08, 0.405, M=_front(0.0), mat="M_Emit")
        box(mb, STEEL, -0.82, -0.78, -0.4, 0.3, 2.55, 3.15, ch=0.0)
        box(mb, STEEL, 0.78, 0.82, -0.4, 0.3, 2.55, 3.15, ch=0.0)
        return [mb.build("torch"), KA.empty("LightAnchor", (0, -0.5, 2.85))]

    # ------------------------------------------------------------ boss gate and marker
    def boss_gate(self):
        mb = MB()
        box(mb, STEEL_D, -2.0, -1.75, -0.25, 0.25, 0.0, 4.5, ch=0.03)
        box(mb, STEEL_D, 1.75, 2.0, -0.25, 0.25, 0.0, 4.5, ch=0.03)
        box(mb, DARK, -2.0, 2.0, -0.25, 0.25, 4.2, 4.5, ch=0.03)
        slat = 4.2 / 22
        for k in range(22):
            z0 = k * slat
            box(mb, STEEL if k % 2 == 0 else "#8e979f", -1.75, 1.75, -0.22, 0.22, z0 + 0.02, z0 + slat - 0.02, ch=0.0)
        M = _front(0.22)
        zig = [(-1.4, 4.0), (-0.9, 3.4), (-0.6, 3.0), (-0.2, 2.2), (0.3, 1.8), (0.8, 1.1), (1.2, 0.5)]
        for p, q in zip(zig, zig[1:]):
            flat_bar(mb, VIOLET_E, p, q, 0.09, 0.01, M=M, mat="M_Emit")
        return [mb.build("boss_gate"), KA.empty("LightAnchor_gate_L", (-1.65, -0.85, 0.9)),
                KA.empty("LightAnchor_gate_R", (1.65, -0.85, 0.9))]

    def foe_marker(self):
        mb = MB()
        mb.add(KA.disc(1.1, n=28, z=0.0, r_in=0.85), ORANGE, "M_Emit")
        mb.add(KA.disc(0.55, n=20, z=0.005), "#7a2b1f")
        return [mb.build("foe_marker"), KA.empty("Spot_foe", (0, 0, 0))]

    # ------------------------------------------------------------ decor (stand on the floor, front = -Y)
    def _pillar_num(self, mb, x=0.0, y=0.0):
        """Station number pillar: white column with two line-colour bands and a round sign on top."""
        cyl(mb, WHITE, (x, y, 0), 0.22, 2.1, seg=14)
        cyl(mb, LINE2, (x, y, 1.5), 0.225, 0.18, seg=14)
        cyl(mb, BLUE, (x, y, 1.0), 0.225, 0.12, seg=14)
        cyl(mb, LINE2, (x, y, 2.1), 0.3, 0.06, seg=18)
        mb.add(KA.disc(0.2, n=18, z=2.16), WHITE, M=T((x, y, 0)))

    def _ticket_gate(self, mb):
        """Two steel reader cabinets with glowing readers, a turnstile post and three arms."""
        for x in (-0.6, 0.6):
            box(mb, STEEL, x - 0.25, x + 0.25, -0.28, 0.28, 0.0, 1.0, ch=0.03)
            box(mb, DARK, x - 0.27, x + 0.27, -0.3, 0.3, 1.0, 1.06, ch=0.01)
            quad(mb, "#5cf0a0", x - 0.1, 0.62, x + 0.1, 0.7, 0.0, M=KA.face_matrix("S", 0.28), mat="M_Emit")
            quad(mb, "#ffffff", x - 0.12, 0.8, x + 0.12, 0.86, 0.0, M=KA.face_matrix("S", 0.28))
        cyl(mb, STEEL_D, (0, 0, 0), 0.12, 1.0, seg=10)
        for th in (0.0, 60.0, 120.0):
            cyl(mb, WHITE, (0, 0, 0.9), 0.035, 0.9, seg=8, rot=(0, 90, th), center=True)
            cyl(mb, YELLOW, (0, 0, 0.9), 0.04, 0.2, seg=8, rot=(0, 90, th), center=True)

    def _vending(self, mb, x=0.0, y=0.0, rz=0.0):
        """Vending machine: red cabinet, lit product window, rows of products, coin panel."""
        M = T((x, y, 0), (0, 0, rz))
        box(mb, RED, -0.45, 0.45, -0.36, 0.36, 0.0, 1.85, ch=0.03, M=M)
        box(mb, WHITE, -0.46, 0.46, -0.37, -0.3, 1.8, 1.9, ch=0.02, M=M)
        F = KA.face_matrix("S", 0.36)
        quad(mb, "#ffe6a8", -0.33, 0.85, 0.2, 1.6, 0.0, M=M @ F, mat="M_Emit")
        for k in range(3):
            for j in range(4):
                col = ("#ffffff", "#7ad1ff", "#ffd45a", "#ff9e7a")[(k + j) % 4]
                quad(mb, col, -0.3 + 0.13 * j, 0.95 + 0.2 * k, -0.2 + 0.13 * j, 1.05 + 0.2 * k, 0.005, M=M @ F)
        quad(mb, STEEL, 0.25, 0.25, 0.4, 0.55, 0.0, M=M @ F)
        quad(mb, LINE2, -0.45, 1.9, 0.45, 2.0, 0.0, M=M @ F)

    def _escalator(self, mb):
        """Broken escalator: a stepped ramp rising 1.6 m towards -Y, top step missing, bent handrail."""
        L, H, W = 1.9, 1.6, 0.9
        s = H / L

        def zt(y):
            return (L / 2 - y) * s
        for k in range(8):
            y1 = L / 2 - k * 0.2375
            y0 = y1 - 0.2375
            if k == 7:
                continue                       # the top step is gone
            top = zt(y0)
            box(mb, STEEL_D, -W / 2 + 0.02, W / 2 - 0.02, y0 + 0.01, y1 - 0.01, 0.0, top, ch=0.0)
            quad(mb, YELLOW, -W / 2, y0, W / 2, y0 + 0.05, top + 0.002)
            quad(mb, "#40464e", -W / 2 + 0.05, y0 + 0.05, W / 2 - 0.05, y1 - 0.02, top + 0.002)
        for x in (-W / 2 - 0.05, W / 2 + 0.05):
            pts = [(x, y, zt(y) + 0.95) for y in [L / 2 - i * (L / 7) for i in range(8)]]
            pts[-1] = (x + 0.02, pts[-1][1], pts[-1][2] - 0.28)     # the rail is bent at the top
            vs, fs = KA.tube(pts, 0.026, sides=6)
            mb.add((vs, fs), DARK)
            for p in pts[::3]:                  # balusters
                cyl(mb, STEEL_D, (p[0], p[1], p[2] - 0.9), 0.02, 0.9, seg=6)
        # side skirts (sloped plates in the x = +-W/2 planes)
        for x in (-W / 2, W / 2):
            vs = [(x, L / 2, 0.0), (x, -L / 2, 0.0), (x, -L / 2, H), (x, L / 2, zt(L / 2) + 0.02)]
            mb.add((vs, [(0, 1, 2, 3), (0, 3, 2, 1)]), STEEL)

    def decor(self, i):
        mb = MB()
        if i == 1:
            self._ticket_gate(mb)
            return [mb.build("decor_1")]
        if i == 2:
            return [join("decor_2", [cc("kc", "bench", PAL, scale=4.0)])]
        if i == 3:
            cyl(mb, "#4a565f", (-0.3, 0.0, 0), 0.24, 0.8, seg=14)
            cyl(mb, LINE2, (-0.3, 0.0, 0.45), 0.245, 0.08, seg=14)
            cyl(mb, STEEL, (-0.3, 0.0, 0.8), 0.26, 0.05, seg=14)
            cyl(mb, DARK, (-0.3, 0.0, 0.85), 0.1, 0.04, seg=10)
            return [join("decor_3", [mb.build("decor_3_bin"), cc("kc", "trash_A", PAL, loc=(0.35, 0.1, 0), scale=4.0)])]
        if i == 4:
            self._vending(mb)
            return [mb.build("decor_4")]
        if i == 5:
            self._escalator(mb)
            return [mb.build("decor_5")]
        self._pillar_num(mb)
        return [mb.build("decor_6")]

    # ------------------------------------------------------------ overlays (hug the -Y face of a wall block: y -2..-2.35)
    def overlay(self, i):
        rng = self.rng(f"overlay_{i}")
        mb = MB()
        M = KA.face_matrix("S", 2.0)
        if i == 1:
            # violet gate crack running up the wall, rubble at the base
            zig = [(-0.9, 0.0), (-0.5, 0.8), (-0.7, 1.5), (-0.1, 2.2), (-0.35, 3.0), (0.3, 3.5), (0.1, 4.2)]
            for p, q in zip(zig, zig[1:]):
                flat_bar(mb, VIOLET_E, p, q, 0.07, 0.02, M=M, mat="M_Emit")
            plate(mb, "#3b3832", -1.2, 0.0, 1.2, 0.5, 0.0, 0.03, M=M)
            for _ in range(5):
                x = rng.uniform(-1.1, 1.1)
                s = rng.uniform(0.12, 0.26)
                mb.add(KA.rock(rng, s, s, s * 0.7, n=9, flat=0.3), C.pick(rng, RUBBLE), M=T((x, -2.2, 0.0)))
        else:
            # fire-hose cabinet with two conduits rising to the top, and a fuse box
            plate(mb, RED, -0.45, 1.0, 0.45, 1.8, 0.0, 0.26, M=M)
            plate(mb, WHITE, -0.33, 1.15, 0.33, 1.65, 0.26, 0.28, M=M)
            plate(mb, STEEL_D, -0.5, 2.05, -0.1, 2.6, 0.0, 0.12, M=M)
            quad(mb, "#ffb347", -0.4, 2.15, -0.25, 2.25, 0.13, M=M, mat="M_Emit")
            for x in (-1.1, 1.1):
                cyl(mb, "#7b838b", (x, -2.12, 0.0), 0.07, 4.2, seg=8)
            plate(mb, STEEL_D, -1.2, 2.6, 1.2, 2.66, 0.0, 0.06, M=M)
        return [mb.build(f"overlay_{i}")]

    # ------------------------------------------------------------ arena: island platform with a train on the track
    # Battle camera at (0,-12,4) looking at (0,3,1), fov 70: the enemy side (+Y) is the far half, behind it the track and
    # the train (y 11.4..14.2); the party side (-Y) stays sparse so it does not block the camera.
    def arena_floor(self, rng):
        """Near island platform (y < 8.2) with a yellow tactile strip and drop line at its edge, a track bed between the
        platform screens (y 8.2) and a raised far platform (y > 13, 0.9 m) with its own yellow edge. Two rails and
        sleepers run along X under the train (y 9.7 / 11.3). Lines, wet patches and cracks break up the tiles."""
        mb = MB()
        R = 17.5
        edge, far_edge = 8.2, 13.0
        tiles_g(mb, rng, GRAVEL, -R, -R, R, R, 1.2, 1.2, d=-0.01, gap=0.03, amt=0.1,
                grime_kw=dict(low=0.0, corner=0.0))
        tiles_g(mb, rng, PLAT, -R, -R, R, edge, 0.8, 0.8, d=0.0, gap=0.008, amt=0.05,
                grime_kw=dict(low=0.0, corner=0.0))
        flat_bar(mb, "#2a2d31", (-R, edge + 0.02), (R, edge + 0.02), 0.08, 0.0)       # drop line at the platform edge
        flat_bar(mb, YELLOW, (-R, 7.6), (R, 7.6), 0.55, 0.004)                        # tactile strip
        for k in range(-17, 18):
            quad(mb, YELLOW_D, k - 0.06, 7.48, k + 0.06, 7.72, 0.006)
        flat_bar(mb, "#f2f0e8", (-R, 6.4), (R, 6.4), 0.12, 0.004)                     # painted safety line
        # raised far platform (box from z 0 to 0.9) with tiles on top and a yellow edge
        box(mb, "#8d939a", -R, R, far_edge, R, 0.0, 0.9, ch=0.0)
        tiles_g(mb, rng, PLAT, -R, far_edge, R, R, 0.8, 0.8, d=0.9, gap=0.008, amt=0.05,
                grime_kw=dict(low=0.0, corner=0.0))
        flat_bar(mb, YELLOW, (-R, far_edge + 0.35), (R, far_edge + 0.35), 0.4, 0.904)
        for _ in range(9):                                                            # cracks on the platform
            x, y = rng.uniform(-14, 14), rng.uniform(-14, 4.0)
            flat_bar(mb, "#7b766b", (x, y), (x + rng.uniform(-1.0, 1.0), y + rng.uniform(-1.0, 1.0)), 0.035, 0.007)
        for _ in range(7):                                                            # wet patches and oil (opaque)
            x, y = rng.uniform(-13, 13), rng.uniform(-14, 4.5)
            mb.add(KA.disc(rng.uniform(0.3, 0.7), n=14, z=0.006),
                   pick(rng, ["#5a5650", "#7e8790", "#6a6f75"]), M=T((x, y, 0)))
        for x in range(-16, 17):                                                      # sleepers
            quad(mb, WOOD_TRACK, x - 0.14, 9.1, x + 0.14, 11.9, 0.0)
        for y in (9.7, 11.3):
            flat_bar(mb, RAIL_C, (-R, y), (R, y), 0.08, 0.012)
        return mb

    def arena_backdrop(self, rng):
        """Tunnel ring: tiled walls with grime at the base, a green band, a cornice and ad lightboxes on the far side.
        Side tunnel mouths are dark tunnels (no sky behind them)."""
        mb = MB()
        R, H, n = 17.0, ARENA_CEIL, 64
        p = lambda a, z: (R * math.cos(a), R * math.sin(a), z)
        for i in range(n):
            a0, a1 = 2 * math.pi * i / n, 2 * math.pi * (i + 1) / n
            mid = 0.5 * (a0 + a1)
            tunnel = 0.5 < mid < 1.1 or 2.1 < mid < 2.7
            col = "#16191d" if tunnel else grime(TILE[i % 3], low=0.9, k=0.6, corner=0.0)
            mb.add(([p(a0, 0), p(a1, 0), p(a1, H - 0.4), p(a0, H - 0.4)], [(0, 3, 2, 1)]), col)
            mb.add(([p(a0, 2.6), p(a1, 2.6), p(a1, 2.95), p(a0, 2.95)], [(0, 3, 2, 1)]),
                   "#0e1013" if tunnel else LINE2)
            mb.add(([p(a0, H - 0.4), p(a1, H - 0.4), p(a1, H), p(a0, H)], [(0, 3, 2, 1)]), CAP_D)
        for k in range(12):   # ad lightboxes on the enemy side of the ring (y > 0)
            a = math.radians(20 + 140 * k / 11)
            x, y = (R - 0.45) * math.cos(a), (R - 0.45) * math.sin(a)
            M = T((x, y, 0))
            box(mb, STEEL_D, -1.5, 1.5, -0.1, 0.1, 1.2, 3.2, ch=0.0, M=M)
            col = ("#ff7fb0", "#58e0d0", "#ffd45a", "#8fc7ff")[k % 4]
            mb.add(([(-1.35, -0.12, 1.3), (1.35, -0.12, 1.3), (1.35, -0.12, 3.1), (-1.35, -0.12, 3.1)], [(0, 1, 2, 3)]),
                   col, "M_Emit", M=M)
        return mb

    def arena_ceiling(self, rng):
        """Station ceiling over the whole hall: acoustic panels, fluorescent strips and a hanging station sign."""
        mb = MB()
        rr = 16.6
        ceil_tiles(mb, rng, CEIL_TILE, -17.5, -17.5, 17.5, 17.5, ARENA_CEIL, 1.5, gap=0.04,
                   grime_kw=dict(low=0.0, corner=0.0, wall_edge=0.0),
                   skip=lambda cx, cy: math.hypot(cx, cy) > rr)
        for x in (-8.0, -4.0, 0.0, 4.0, 8.0):
            half = math.sqrt(max(rr * rr - x * x, 1.0))
            ceil_rect(mb, STEEL_G, x - 0.27, -half, x + 0.27, half, ARENA_CEIL - 0.04)
            ceil_rect(mb, LIGHT, x - 0.22, -half, x + 0.22, half, ARENA_CEIL - 0.045, mat="M_Emit")
        for x in (-2.2, 2.2):   # hanging station sign over the stage
            hang(mb, DARK, x, 0.0, ARENA_CEIL - 0.005, 6.7, r=0.02)
        box(mb, NAVY, -2.6, 2.6, -0.1, 0.1, 6.0, 6.7, ch=0.0)
        for k, (u0, u1) in enumerate(((-2.4, -1.2), (-1.0, 0.4), (0.6, 2.2))):
            mb.add(([(u0, -0.12, 6.2), (u1, -0.12, 6.2), (u1, -0.12, 6.5), (u0, -0.12, 6.5)], [(0, 1, 2, 3)]),
                   WHITE if k != 1 else LINE2)
        return mb

    def _train(self, mb, xc=3.5, y=10.4):
        """One lit 18 m subway car along X on the near track: lit windows, three open doors, a green livery."""
        sub = MB()
        h = 9.0
        box(sub, TRAIN_W, -h, h, -1.4, 1.4, 0.55, 3.45, ch=0.06)
        box(sub, TRAIN_R, -h + 0.2, h - 0.2, -1.3, 1.3, 3.45, 3.6, ch=0.03)
        for x in (-6.0, 6.0):
            box(sub, BOGIE, x - 1.6, x + 1.6, -1.1, 1.1, 0.1, 0.55, ch=0.0)
        for x in (-4.0, 2.0, 6.0):
            box(sub, TRAIN_STEEL, x - 0.9, x + 0.9, -0.9, 0.9, 3.6, 3.85, ch=0.02)
        F = KA.face_matrix("S", 1.4)
        quad(sub, LINE2, -h + 0.05, 1.05, h - 0.05, 1.25, 0.004, M=F)
        doors = (-5.5, 0.0, 5.5)
        for x in range(-8, 8, 2):
            if any(abs(x + 0.5 - d) < 1.4 for d in doors):
                continue
            quad(sub, "#ffe7a6", x + 0.2, 1.6, x + 1.7, 2.6, 0.004, M=F, mat="M_Emit")
        for d in doors:
            quad(sub, "#ffd98a", d - 0.6, 0.5, d + 0.6, 2.9, 0.004, M=F, mat="M_Emit")      # lit interior
            box(sub, TRAIN_STEEL, d - 0.78, d - 0.7, -1.95, -1.4, 0.5, 2.95, ch=0.0)       # door leaves, open
            box(sub, TRAIN_STEEL, d + 0.7, d + 0.78, -1.95, -1.4, 0.5, 2.95, ch=0.0)
        quad(sub, "#fff6d0", -0.6, 1.9, 0.6, 2.2, 0.004, M=F, mat="M_Emit")
        mb.extend(C.place_mb(sub, T((xc, y, 0))))

    def _tiled_pillar(self, mb, x, y, band=LINE2, h=3.3):
        """Tiled pillar of height h with a line-colour band and a navy line-number sign on top."""
        sub = MB()
        sub.add(KA.cbox(0.7, 0.7, h, ch=0.05, loc=(0, 0, h / 2)), grime(TILE[0], low=0.4, k=0.6, corner=0.5), "M_Toon")
        box(sub, band, -0.36, 0.36, -0.36, 0.36, h * 0.68, h * 0.68 + 0.15, ch=0.0)
        box(sub, NAVY, -0.36, 0.36, -0.36, 0.36, h, h + 0.25, ch=0.02)
        quad(sub, WHITE, -0.22, h + 0.1, 0.22, h + 0.2, 0.0, M=KA.face_matrix("S", 0.37))
        mb.extend(C.place_mb(sub, T((x, y, 0))))

    def _signal_mast(self, mb, x, y, h=5.6):
        """Tall signal mast at the track edge: steel pole, a navy head with two lit lamps."""
        cyl(mb, STEEL_D, (x, y, 0.0), 0.09, h, seg=8)
        box(mb, NAVY, x - 0.35, x + 0.35, y - 0.12, y + 0.12, h - 0.9, h - 0.2, ch=0.03)
        for k, col in enumerate(("#ff5a4a", "#7dff8a")):
            box(mb, col, x - 0.22 + 0.22 * k, x - 0.1 + 0.22 * k, y - 0.14, y - 0.1, h - 0.7, h - 0.5, ch=0.0, mat="M_Emit")
        box(mb, STEEL, x - 0.7, x + 0.7, y - 0.05, y + 0.05, h - 0.05, h + 0.05, ch=0.0)

    def _screen_doors(self, mb, y=9.0, x0=-8.4, x1=8.4):
        """Glass platform screens along the platform edge facing the track (1.75 m: low enough that the lit car behind
        them shows above the glass from the battle camera): steel posts, glass panes, top rail."""
        H = 1.75
        n = int(round((x1 - x0) / 1.2))
        step = (x1 - x0) / n
        for k in range(n + 1):
            x = x0 + k * step
            box(mb, STEEL_D, x - 0.04, x + 0.04, y - 0.05, y + 0.05, 0.0, H, ch=0.0)
        box(mb, STEEL_D, x0, x1, y - 0.05, y + 0.05, H - 0.1, H, ch=0.0)
        for k in range(n):
            a, b = x0 + k * step + 0.04, x0 + (k + 1) * step - 0.04
            mb.add(([(a, y, 0.05), (b, y, 0.05), (b, y, H - 0.12), (a, y, H - 0.12)], [(0, 1, 2, 3), (0, 3, 2, 1)]),
                   "#b9e6ef", "M_Clear")

    def arena_props(self, rng):
        """Train and platform screens, tiled pillars with line-number signs on both platforms, life-size benches and
        bins on the near platform (enemy side), vending machines on the party side."""
        mb = MB()
        out = []
        self._train(mb)
        self._screen_doors(mb, y=8.2, x0=-9.0, x1=13.0)
        for x in (-11.0, 11.0):
            self._tiled_pillar(mb, x, 3.6, band=LINE2)
        for x in (-12.0, -6.0, 0.0, 6.0, 12.0):                                       # far platform, behind the train
            self._tiled_pillar(mb, x, 14.2, band=pick(rng, [LINE2, ORANGE, BLUE]), h=6.0)
        self._signal_mast(mb, -8.5, 9.2)
        self._signal_mast(mb, 14.6, 9.6)
        for x in (-9.2, 9.2):
            self._tiled_pillar(mb, x, -5.5, band=LINE2)
        for x, y in ((-8.6, -4.5), (8.6, -4.5)):
            self._vending(mb, x, y, 0.0)
        out.append(mb.build("arena_props"))
        for x, y in ((-6.6, 6.3), (6.6, 6.3)):
            out.append(cc("kc", "bench", PAL, loc=(x, y, 0), rz=0.0, scale=4.5))   # 1.8 m bench
        for x, y in ((-8.4, 6.8), (-4.2, 6.9), (9.6, 6.6)):
            out.append(cc("kc", "trash_A", PAL, loc=(x, y, 0), scale=4.0))         # ~0.5 m bin
        return out
