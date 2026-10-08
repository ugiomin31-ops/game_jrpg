"""Seoul metro station after a gate break ('subway' tileset).

Look: cream subway tiles with a line-2 green band, safety-yellow tactile edge, grey platform tiles, rails and
sleepers in the tunnel variant, steel service furniture (turnstile, bench, bin, vending machine, first-aid cabinet,
info kiosk), violet gate cracks and a portal ring. Saturated but not neon; chunky shapes like verdant_ruins.
"""
import math

import common_a as C
from common_a import HunterKit, MB, KA, T, box, cyl, quad, plate, flat_bar, tile_quads, tile_face, wall_shell
from common_a import SHELL, WALL_H

TILE = ["#f7f5ee", "#efede5", "#fbfaf6"]          # cream-white glossy wall tiles
GROUT = "#c9cbcb"                                  # thin light-grey wall grout
FLOOR_GROUT = "#b4b2aa"
TILE_GAP = 0.0045                                  # joint = 2 x gap = 0.009 m (1/8 of the old 0.07 m)
LINE2 = "#1aa35a"
YELLOW = "#ffc91a"
YELLOW_D = "#d99a00"
PLAT = ["#ddd7c8", "#d2ccbd", "#e6e0d2"]   # light grey-beige floor tiles
STEEL = "#a2aab2"
STEEL_D = "#5b646c"
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


def _front(d):
    """Face matrix of the -Y (S) face pushed out by d: a point (u, v, e) lies at y = -(d + e)."""
    return KA.face_matrix("S", d)


def _front_side(side):
    """Wall-shell face matrix (details sit on the SHELL plane and reach +-2.0)."""
    return KA.face_matrix(side, SHELL)


class SubwayKit(HunterKit):
    TS = "subway"
    WORLD = "#1b2226"
    SKY = ("#2b1f4a", "#0c0a17")

    # ------------------------------------------------------------ floors (flush detail at z = 0)
    def floor(self, v):
        rng = self.rng(f"floor_{v}")
        mb = MB()
        if v == "a":
            # platform tiles with the yellow tactile safety line (band v in [1.0, 1.5] is one grid row)
            plate(mb, FLOOR_GROUT, -2, -2, 2, 2, -0.3, -0.03)
            tile_quads(mb, rng, PLAT, -2, -2, 2, 2, 0.4, 0.4, d=-0.01, gap=0.004,
                       skip=lambda cx, cy: 0.8 < cy < 1.2)
            quad(mb, YELLOW, -2, 0.8, 2, 1.2, 0.0)
            for i in range(20):
                u = -1.9 + i * 0.2
                quad(mb, YELLOW_D, u + 0.04, 0.9, u + 0.14, 1.1, 0.002)
        elif v == "b":
            # plain platform slabs with a faint violet gate crack
            plate(mb, FLOOR_GROUT, -2, -2, 2, 2, -0.3, -0.03)
            tile_quads(mb, rng, PLAT, -2, -2, 2, 2, 0.4, 0.4, d=-0.01, gap=0.004, amt=0.05)
            zig = [(-1.8, -1.6), (-1.2, -1.1), (-0.8, -0.45), (-0.3, -0.5), (0.2, 0.2), (0.7, 0.35), (1.3, 1.1),
                   (1.8, 1.4)]
            for p, q in zip(zig, zig[1:]):
                flat_bar(mb, VIOLET_E, p, q, 0.07, 0.0, mat="M_Emit")
            quad(mb, "#7f7b70", 0.1, -1.4, 1.2, -0.8, -0.005)
        else:
            # tunnel: gravel bed, sleepers across, two rails along the corridor (Y)
            plate(mb, "#3b3a37", -2, -2, 2, 2, -0.3, -0.03)
            tile_quads(mb, rng, GRAVEL, -2, -2, 2, 2, 0.25, 0.25, d=-0.01, gap=0.02, amt=0.1)
            for i in range(7):
                v0 = -1.9 + i * 0.6
                quad(mb, WOOD, -1.95, v0, 1.95, v0 + 0.26, -0.005)
            for u in (-0.72, 0.72):
                quad(mb, STEEL, u - 0.06, -2.0, u + 0.06, 2.0, 0.0)
                quad(mb, "#d6dde4", u - 0.02, -2.0, u + 0.01, 2.0, 0.003)
        return [mb.build(f"floor_{v}")]

    # ------------------------------------------------------------ walls (core at SHELL, details to +-2.0)
    def _tiles_and_skirt(self, mb, rng, s, skip):
        tile_face(mb, rng, s, TILE, GROUT, 0.5, 0.25, skip=skip, gap=TILE_GAP, amt=0.03)
        quad(mb, SKIRT, -2, 0.0, 2, 0.25, 0.02, M=_front_side(s))

    def _ceiling_band(self, mb, s):
        """Top edge of every wall: a navy station signboard band with glyph blocks, and a steel-housed fluorescent tube."""
        M = _front_side(s)
        plate(mb, STEEL_D, -1.9, 3.6, 1.9, 4.04, 0.02, 0.035, M=M)            # signboard frame
        plate(mb, NAVY, -1.82, 3.66, 1.82, 3.98, 0.035, 0.05, M=M)             # navy board
        for k, (u0, u1) in enumerate(((-1.6, -0.9), (-0.7, 0.2), (0.4, 1.3), (1.45, 1.75))):
            quad(mb, "#ffffff" if k % 2 == 0 else LINE2, u0, 3.74, u1, 3.92, 0.055, M=M)   # glyph blocks
        plate(mb, STEEL, -1.6, 4.12, 1.6, 4.26, 0.02, 0.03, M=M)              # light housing
        quad(mb, "#fff9e8", -1.55, 4.15, 1.55, 4.22, 0.04, M=M, mat="M_Emit")  # fluorescent tube

    def wall(self, v):
        rng = self.rng(f"wall_{v}")
        mb = wall_shell(MB(), CAP, ch=0.05)
        for s in C.SIDES:
            M = _front_side(s)
            self._ceiling_band(mb, s)
            if v == "a":
                # tiles, one line-2 green band (v 1.0-1.25), dark skirting
                self._tiles_and_skirt(mb, rng, s, lambda cx, cy: 1.0 < cy < 1.25 or cy < 0.25)
                quad(mb, LINE2, -2, 1.0, 2, 1.25, 0.02, M=M)
                zig = [(-1.85, 0.45), (-1.4, 0.7), (-1.1, 0.5), (-0.7, 0.85)]
                for p, q in zip(zig, zig[1:]):
                    flat_bar(mb, VIOLET_E, p, q, 0.05, 0.03, M=M, mat="M_Emit")   # violet gate crack
            elif v == "b":
                # tiles with a route-map board (navy) and a yellow header
                self._tiles_and_skirt(mb, rng, s, lambda cx, cy: cy < 0.25 or (-1.5 < cx < 1.5 and 1.25 < cy < 3.6))
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
                # tiles with a backlit ad panel (emissive poster blocks)
                self._tiles_and_skirt(mb, rng, s, lambda cx, cy: cy < 0.25 or (-1.5 < cx < 1.5 and 1.25 < cy < 3.6))
                plate(mb, STEEL_D, -1.55, 1.3, 1.55, 3.6, 0.02, 0.04, M=M)
                plate(mb, "#2d5d8c", -1.45, 1.4, 1.45, 3.5, 0.04, 0.05, M=M, mat="M_Emit")
                quad(mb, "#ff7fb0", -1.25, 2.6, 0.0, 3.3, 0.06, M=M, mat="M_Emit")
                quad(mb, "#58e0d0", 0.1, 1.6, 1.25, 2.9, 0.06, M=M, mat="M_Emit")
                quad(mb, "#ffd45a", -1.25, 1.6, -0.1, 2.4, 0.06, M=M, mat="M_Emit")
                mb.add(KA.disc(0.22, n=20, z=0.065), "#fff6e6", M=M @ T((0.55, 2.95, 0.0)), mat="M_Emit")
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

    # ------------------------------------------------------------ decor (stand on the floor, front = -Y)
    def decor(self, i):
        rng = self.rng(f"decor_{i}")
        mb = MB()
        if i == 1:
            # turnstile: two cabinets, central post, three arms turning at waist height
            box(mb, STEEL, -0.6, -0.35, -0.28, 0.28, 0.0, 1.0, ch=0.03)
            box(mb, STEEL, 0.35, 0.6, -0.28, 0.28, 0.0, 1.0, ch=0.03)
            box(mb, YELLOW, -0.6, 0.6, -0.3, 0.3, 1.0, 1.05, ch=0.01)
            cyl(mb, STEEL_D, (0, 0, 0.9), 0.12, 0.2, seg=10)
            for th in (0.0, 60.0, 120.0):
                cyl(mb, "#e4e6e8", (0, 0, 0.95), 0.035, 0.9, seg=8, rot=(0, 90, th), center=True)
        elif i == 2:
            # bench: green slats on a steel frame, backrest on the wall side (+Y)
            for x in (-0.6, 0.6):
                box(mb, STEEL_D, x - 0.05, x + 0.05, -0.2, 0.2, 0.0, 0.42, ch=0.0)
            for k in range(4):
                y0 = -0.2 + k * 0.1
                box(mb, LINE2 if k % 2 == 0 else "#23b56a", -0.75, 0.75, y0, y0 + 0.09, 0.42, 0.5, ch=0.01)
            box(mb, STEEL_D, -0.75, 0.75, 0.22, 0.3, 0.5, 0.95, ch=0.02)
        elif i == 3:
            # trash bin: grey drum with a green band and a lid
            cyl(mb, "#4a565f", (0, 0, 0), 0.28, 0.85, seg=14)
            cyl(mb, LINE2, (0, 0, 0.5), 0.295, 0.08, seg=14)
            cyl(mb, STEEL, (0, 0, 0.85), 0.3, 0.06, seg=14)
            cyl(mb, DARK, (0, 0, 0.91), 0.12, 0.04, seg=10)
        elif i == 4:
            # vending machine: red cabinet, lit product window and buttons on the front
            box(mb, RED, -0.45, 0.45, -0.36, 0.36, 0.0, 1.85, ch=0.03)
            box(mb, WHITE, -0.46, 0.46, -0.37, -0.3, 1.8, 1.9, ch=0.02)
            M = _front(0.36)
            quad(mb, "#ffe6a8", -0.33, 0.85, 0.2, 1.6, 0.02, M=M, mat="M_Emit")
            for k in range(3):
                for j in range(2):
                    quad(mb, "#ffffff", 0.27 + 0.06 * j, 0.95 + 0.14 * k, 0.32 + 0.06 * j, 1.02 + 0.14 * k, 0.03, M=M)
            quad(mb, STEEL, 0.25, 0.25, 0.4, 0.55, 0.03, M=M)
        elif i == 5:
            # rubble from the gate break, with violet glow shards
            for _ in range(7):
                x, y = rng.uniform(-0.45, 0.45), rng.uniform(-0.4, 0.3)
                s = rng.uniform(0.42, 0.72)
                mb.add(KA.rock(rng, s, s * 0.8, s * 0.6, n=10, flat=0.3), C.pick(rng, RUBBLE), M=T((x, y, 0)))
            for _ in range(3):
                x, y = rng.uniform(-0.3, 0.3), rng.uniform(-0.3, 0.2)
                mb.add(KA.crystal(0.06, 0.32, seg=5), VIOLET, "M_Emit",
                       M=KA.z_axis_matrix((0.3, 0.2, 1.0), (x, y, 0.05)))
        else:
            # station number pillar: white column, green band, sign disc on top
            cyl(mb, WHITE, (0, 0, 0), 0.22, 2.1, seg=14)
            cyl(mb, LINE2, (0, 0, 1.5), 0.225, 0.18, seg=14)
            cyl(mb, LINE2, (0, 0, 2.1), 0.3, 0.06, seg=18)
            mb.add(KA.disc(0.2, n=18, z=2.16), WHITE)
        return [mb.build(f"decor_{i}")]

    # ------------------------------------------------------------ overlays (hug the -Y face of a wall block: y -2..-2.35)
    def overlay(self, i):
        rng = self.rng(f"overlay_{i}")
        mb = MB()
        M = _front(2.0)
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
            # fire hose cabinet on the wall, two conduits rising to the top
            plate(mb, RED, -0.45, 1.0, 0.45, 1.8, 0.0, 0.26, M=M)
            plate(mb, WHITE, -0.33, 1.15, 0.33, 1.65, 0.26, 0.28, M=M)
            for x in (-1.1, 1.1):
                cyl(mb, "#7b838b", (x, -2.12, 0.0), 0.07, 4.2, seg=8)
            plate(mb, STEEL_D, -1.2, 2.6, 1.2, 2.66, 0.0, 0.06, M=M)
        return [mb.build(f"overlay_{i}")]

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

    # ------------------------------------------------------------ arena: platform battle stage
    def arena_floor(self, rng):
        mb = MB()
        n = 48
        for i in range(n):
            a0, a1 = 2 * math.pi * i / n, 2 * math.pi * (i + 1) / n
            col = PLAT[0] if i % 2 == 0 else PLAT[1]
            mb.add(([(0, 0, 0), (9.2 * math.cos(a0), 9.2 * math.sin(a0), 0),
                     (9.2 * math.cos(a1), 9.2 * math.sin(a1), 0)], [(0, 1, 2)]), col)
        mb.add(KA.disc(9.2, n=72, z=0.004, r_in=8.6), YELLOW)
        mb.add(KA.disc(1.9, n=48, z=0.004, r_in=1.6), VIOLET_E, "M_Emit")
        return mb

    def arena_backdrop(self, rng):
        """Tunnel ring around the platform: tiled wall with a green band; side tunnels are gaps; lamps overhead."""
        mb = MB()
        R, H, n = 17.0, 9.0, 56
        p = lambda a, z: (R * math.cos(a), R * math.sin(a), z)
        for i in range(n):
            a0, a1 = 2 * math.pi * i / n, 2 * math.pi * (i + 1) / n
            mid = 0.5 * (a0 + a1)
            if 0.5 < mid < 1.1 or 2.1 < mid < 2.7:
                continue  # side tunnel mouths
            col = TILE[i % 3]
            mb.add(([p(a0, 0), p(a1, 0), p(a1, H), p(a0, H)], [(0, 3, 2, 1)]), col)
            mb.add(([p(a0, 2.6), p(a1, 2.6), p(a1, 2.95), p(a0, 2.95)], [(0, 3, 2, 1)]), LINE2)
        for k in range(10):
            a = 2 * math.pi * k / 10 + 0.3
            x, y = (R - 0.6) * math.cos(a), (R - 0.6) * math.sin(a)
            box(mb, "#f7fff7", x - 0.8, x + 0.8, y - 0.12, y + 0.12, 6.6, 6.8, ch=0.0)
            box(mb, "#cdd3d8", x - 0.85, x + 0.85, y - 0.15, y + 0.15, 6.8, 6.85, ch=0.0)
        mb.add(([(-4.0, 16.8, 0.8), (4.0, 16.8, 0.8), (4.0, 16.8, 5.5), (-4.0, 16.8, 5.5)], [(0, 1, 2, 3)]),
               VIOLET, "M_Emit")
        return mb
