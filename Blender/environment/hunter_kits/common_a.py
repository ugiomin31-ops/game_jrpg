"""Shared builders for the hunter-theme dungeon kits (subway, factory, cave).

Same contract as verdant_ruins / frost_grotto (Blender/README.md, _kit_common_a.py, _pipeline.py):
- 1 cell = 4 m. Blender cell (gx, gy) sits at world (4 gx, 4 gy, 0), which is DungeonWorld.Position(cell)
  after the Unity axis mapping (Unity X = Blender X, Unity Z = -Blender Y). North = -Y, East = +X.
- Floor tops at z = 0. _pipeline.grid_piece clamps floor_* vertices to z <= 0 and |x|,|y| <= 2, and rescales
  wall_* so their bounding box is exactly [-2,2]^2 x [0,4.5]. So a floor's raised detail must be flush,
  and wall details must stay inside |x|,|y| <= 2 (the core is set back by SHELL and details reach 2.0).
- Door-like pieces: passage along Y through the y=0 plane, `Door` leaf hinged at x = -1 (the -X jamb side),
  opens by yaw +95 (DungeonWorld.RefreshProgress). Chests face -Y with a back-hinged `Lid`.
- Props placed by DungeonWorld.AgainstWall / Dress stand on a floor and face -Y (their front faces the cell
  centre). Their back (+Y) must stay within the offset they are placed at (see the constants below).
- Torches: back (+Y) on the wall face, `LightAnchor` Empty in front. Overlays: -Y face on a wall block.

Geometry goes through MB (per-corner `Col` colours, slots M_Toon / M_Emit / M_Clear only).
Face decoration uses face_matrix(side, dist): local u = along the face, local v = +Z up, local d = outward.
"""
import math
import os
import random
import sys

ENV_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
LIB_DIR = os.path.normpath(os.path.join(ENV_DIR, "..", "lib"))
for _p in (ENV_DIR, LIB_DIR):
    if _p not in sys.path:
        sys.path.insert(0, _p)

import bpy  # noqa: E402
import abyss_bpy as A  # noqa: E402
import _kit_common_a as KA  # noqa: E402
import _kit_common_b as B  # noqa: E402
from _kit_common_a import MB, T, Vector  # noqa: E402
from _pipeline import run  # noqa: E402
from mathutils import Matrix  # noqa: E402

CELL = 4.0
HALF = 2.0
WALL_H = 4.5
SHELL = 1.98          # wall core face; wall details add up to 0.02 m so the cell bbox is exactly +-2.0
SIDES = ("S", "E", "N", "W")  # S = -Y, E = +X, N = +Y, W = -X (outward face normals)

# DungeonWorld.Dress / Facing: N, E, S, W as Blender XY unit offsets (north = -Y).
DIRS = {0: (0.0, -1.0), 1: (1.0, 0.0), 2: (0.0, 1.0), 3: (-1.0, 0.0)}
# Eye height and placement offsets from DungeonWorld.
EYE = 1.35
TORCH_OFF = 1.7       # torch origin 1.7 m from the cell centre toward the wall (back touches the face at 2.0)
DECOR_OFF = 1.45      # decor: 1.45 m toward the wall and 1 m to one side
OVERLAY_CHANCE, DECOR_CHANCE = 18, 26
CHEST_OFF, LORE_OFF, SPRING_OFF = 1.3, 1.35, 1.1


# ---------------------------------------------------------------- DungeonWorld ports

def cell_hash(x, y, salt):
    """Port of DungeonWorld.CellHash (unchecked uint arithmetic)."""
    M = 0xFFFFFFFF
    h = (x * 374761393 + y * 668265263 + salt * 2246822519) & M
    h = ((h ^ (h >> 13)) * 1274126177) & M
    return (h ^ (h >> 16)) & 0x7FFFFFFF


def yaw_of(fx, fy):
    """Degrees of Z rotation that turns a piece's local -Y (its front) onto the Blender direction (fx, fy).
    Equivalent to Quaternion.LookRotation(v) for pieces authored front = -Y."""
    return math.degrees(math.atan2(fx, -fy))


def face_front_dirs(facing):
    return DIRS[facing]


# ---------------------------------------------------------------- colour

def jit(rng, col, amt=0.05):
    r, g, b, a = KA.C(col)
    k = 1 + rng.uniform(-amt, amt)
    return (min(1.0, r * k), min(1.0, g * k), min(1.0, b * k), a)


def pick(rng, cols, amt=0.05):
    return jit(rng, rng.choice(cols), amt)


def shade(col, k):
    r, g, b, a = KA.C(col)
    return (min(1.0, r * k), min(1.0, g * k), min(1.0, b * k), a)


def mix(a, b, t):
    return KA.mix(a, b, t)


def ccw(poly):
    return list(poly) if KA.poly_area(poly) >= 0 else list(reversed(poly))


def face_mats(dist=SHELL):
    return {s: KA.face_matrix(s, dist) for s in SIDES}


# ---------------------------------------------------------------- primitives (accept M = object/face matrix)

def quad(mb, col, u0, v0, u1, v1, d=0.0, M=None, mat="M_Toon"):
    """One flat rectangle in local XY at z = d, normal +Z (2 tris)."""
    mb.add(([(u0, v0, d), (u1, v0, d), (u1, v1, d), (u0, v1, d)], [(0, 1, 2, 3)]), col, mat, M=M)


def plate(mb, col, u0, v0, u1, v1, d0, d1, M=None, mat="M_Toon"):
    """Rectangular slab in local (u, v), extruded along local d in [d0, d1]."""
    mb.add(KA.prism(KA.rect_poly(u0, v0, u1, v1), d0, d1), col, mat, M=M)


def box(mb, col, x0, x1, y0, y1, z0, z1, ch=0.02, M=None, mat="M_Toon", bottom=True):
    """Chamfered box spanning the given extents (bottom face included)."""
    c = min(ch, (x1 - x0) / 2.5, (y1 - y0) / 2.5, (z1 - z0) / 2.5)
    poly = KA.rect_poly(x0, y0, x1, y1)
    mb.add(KA.slab(poly, z0, z1, ch=c, bottom=bottom) if c > 1e-4 else KA.prism(poly, z0, z1, bottom=bottom),
           col, mat, M=M)


def cyl(mb, col, loc, r, h, seg=12, rot=(0, 0, 0), mat="M_Toon", M=None, r2=None, center=False):
    """Cylinder along local Z from loc (or centred on loc when center=True), then rotated by rot (degrees)."""
    base = T(loc, rot)
    geo = KA.cyl(r, h, seg=seg, r2=r2, z0=-h / 2 if center else 0.0)
    mb.add(geo, col, mat, M=(M @ base) if M is not None else base)


def flat_bar(mb, col, p0, p1, w, d=0.0, M=None, mat="M_Toon"):
    """Flat convex strip from p0 to p1 (width w) lying at local z = d (normal +Z)."""
    p0, p1 = Vector(p0), Vector(p1)
    dv = p1 - p0
    if dv.length < 1e-9:
        return
    n = Vector((-dv.y, dv.x)).normalized() * (w / 2)
    poly = [tuple(p0 + n), tuple(p1 + n), tuple(p1 - n), tuple(p0 - n)]
    poly = ccw(poly)
    mb.add(([(x, y, d) for x, y in poly], [tuple(range(4))]), col, mat, M=M)


def sphere(mb, col, loc, r, seg=10, rings=6, scale=(1, 1, 1), mat="M_Toon", M=None):
    v, f = KA.uvsphere(r, seg=seg, rings=rings, scale=scale)
    geo = ([(x, y, z) for x, y, z in v], f)
    base = T(loc)
    mb.add(geo, col, mat, M=(M @ base) if M is not None else base)


def bar(mb, col, p0, p1, w, d0, d1, M=None, mat="M_Toon"):
    """Flat bar from p0 to p1 in local XY (width w) extruded along z from d0 to d1."""
    p0, p1 = Vector(p0), Vector(p1)
    n = Vector((-(p1 - p0).y, (p1 - p0).x)).normalized() * (w / 2)
    poly = ccw([tuple(p0 + n), tuple(p1 + n), tuple(p1 - n), tuple(p0 - n)])
    mb.add(KA.prism(poly, d0, d1), col, mat, M=M)


def tile_quads(mb, rng, cols, u0, v0, u1, v1, cu, cv, d=0.0, M=None, gap=0.03, mat="M_Toon", amt=0.06,
               skip=None):
    """Grid of flat tiles (one quad each) with jittered colours; skip(cx, cy) hides a tile."""
    nu = max(1, round((u1 - u0) / cu))
    nv = max(1, round((v1 - v0) / cv))
    du, dv = (u1 - u0) / nu, (v1 - v0) / nv
    for i in range(nu):
        for j in range(nv):
            cx, cy = u0 + (i + 0.5) * du, v0 + (j + 0.5) * dv
            if skip and skip(cx, cy):
                continue
            a, b = u0 + i * du + gap, u0 + (i + 1) * du - gap
            c, e = v0 + j * dv + gap, v0 + (j + 1) * dv - gap
            quad(mb, jit(rng, rng.choice(cols), amt), a, c, b, e, d, M=M, mat=mat)


def stripes_quads(mb, cols, u0, v0, u1, v1, count, d, M=None, vertical=False, mat="M_Toon"):
    """Alternating hazard-style stripes across a rectangle (flat quads)."""
    if vertical:
        w = (u1 - u0) / count
        for i in range(count):
            quad(mb, cols[i % 2], u0 + i * w, v0, u0 + (i + 1) * w, v1, d, M=M, mat=mat)
    else:
        h = (v1 - v0) / count
        for i in range(count):
            quad(mb, cols[i % 2], u0, v0 + i * h, u1, v0 + (i + 1) * h, d, M=M, mat=mat)


def diag_stripes(mb, cols, u0, v0, u1, v1, width, d, M=None, mat="M_Toon"):
    """Diagonal hazard stripes clipped to a rectangle (convex polygons, 45 degrees)."""
    rect = KA.rect_poly(u0, v0, u1, v1)
    k = 0
    start = u0 - (v1 - v0)
    x = start
    while x < u1 + (v1 - v0):
        a = (x, v0)
        b = (x + width, v0)
        c = (x + width + (v1 - v0), v1)
        e = (x + (v1 - v0), v1)
        poly = [a, b, c, e]
        from_clip = _clip_convex(poly, rect)
        if len(from_clip) >= 3:
            vs = [(px, py, d) for px, py in ccw(from_clip)]
            mb.add((vs, [tuple(range(len(vs)))]), cols[k % 2], mat, M=M)
        k += 1
        x += width
    return mb


def _clip_convex(subject, clip):
    """Sutherland-Hodgman clip of a convex polygon by a convex CCW clip polygon."""
    out = list(subject)
    for i in range(len(clip)):
        a = clip[i]
        b = clip[(i + 1) % len(clip)]
        inp = out
        out = []
        if not inp:
            break
        for j in range(len(inp)):
            p = inp[j]
            q = inp[(j + 1) % len(inp)]
            side_p = (b[0] - a[0]) * (p[1] - a[1]) - (b[1] - a[1]) * (p[0] - a[0])
            side_q = (b[0] - a[0]) * (q[1] - a[1]) - (b[1] - a[1]) * (q[0] - a[0])
            if side_p >= 0:
                out.append(p)
            if (side_p >= 0) != (side_q >= 0):
                t = side_p / (side_p - side_q)
                out.append((p[0] + (q[0] - p[0]) * t, p[1] + (q[1] - p[1]) * t))
    return out


def tile_face(mb, rng, side, cols, grout, cu, cv, skip=None, mat="M_Toon", gap=0.035, amt=0.06):
    """Tiled face of the wall shell: grout plate + tile quads. skip(u, v) hides tiles (for stripes/signs)."""
    M = KA.face_matrix(side, SHELL)
    plate(mb, grout, -HALF, 0.0, HALF, WALL_H, 0.0, 0.012, M=M)
    tile_quads(mb, rng, cols, -HALF, 0.0, HALF, WALL_H, cu, cv, d=0.02, M=M, gap=gap, mat=mat, amt=amt,
               skip=skip)


def wall_shell(mb, core_col, ch=0.06, mat="M_Toon"):
    """The wall core: chamfered block at +-SHELL (bbox is restored by the face details to +-2.0)."""
    mb.add(KA.cbox(2 * SHELL, 2 * SHELL, WALL_H, ch=ch, loc=(0, 0, WALL_H / 2)), core_col, mat)
    return mb


# ---------------------------------------------------------------- tube / rope / chain helpers

def chain(mb, col, p0, p1, link_r=0.05, wire=0.014, M=None, mat="M_Toon"):
    """Hanging chain from p0 down to p1 as alternating torus-ish link rings (cheap: thin cylinders)."""
    p0, p1 = Vector(p0), Vector(p1)
    n = max(2, int((p0 - p1).length / (link_r * 2.2)))
    for i in range(n):
        t = (i + 0.5) / n
        p = p0.lerp(p1, t)
        h = link_r * 1.5
        ring = KA.cyl(wire, h, seg=6)
        rot = (90, 0, 0) if i % 2 == 0 else (0, 90, 0)
        mb.add(ring, col, mat, M=(M @ T(p, rot)) if M is not None else T(p, rot))


# ---------------------------------------------------------------- base kit

class HunterKit:
    """One tileset. Subclasses set TS/WORLD/SKY and implement the piece builders (each returns a list of objects).
    The pieces() list is the contract names used by _pipeline.PIECE_NAMES."""
    TS = "kit"
    WORLD = "#202020"
    SKY = ("#202020", "#101010")

    def rng(self, name):
        return random.Random(KA.seed_of(self.TS, name))

    def out(self, mb, name, origin=(0, 0, 0)):
        """Wrap one MB as a single exported object list."""
        return [mb.build(name, origin=origin)]

    # -- piece list (names must match _pipeline.PIECE_NAMES)
    def pieces(self):
        out = [(f"floor_{v}", lambda v=v: self.floor(v)) for v in "abc"]
        out += [(f"wall_{v}", lambda v=v: self.wall(v)) for v in "abc"]
        out += [("door", lambda: self.door(False)), ("door_locked", lambda: self.door(True)),
                ("stairs_down", lambda: self.stairs(False)), ("stairs_up", lambda: self.stairs(True))]
        out += [(n, getattr(self, n)) for n in ("chest", "lore_stone", "trap", "spring", "warp", "torch")]
        out += [(f"decor_{i}", lambda i=i: self.decor(i)) for i in range(1, 7)]
        out += [(f"overlay_{i}", lambda i=i: self.overlay(i)) for i in (1, 2)]
        out += [("boss_gate", self.boss_gate), ("foe_marker", self.foe_marker)]
        return out

    # -- arena (shared stage scaffolding; tilesets provide floor + backdrop as MB)
    def arena_floor(self, rng):
        raise NotImplementedError

    def arena_backdrop(self, rng):
        raise NotImplementedError

    def arena(self):
        A.reset_scene()
        rng = self.rng("arena")
        floor = self.arena_floor(rng).build("arena")
        backdrop = self.arena_backdrop(rng).build("arena_backdrop")
        sky = MB()
        sky.add(KA.uvsphere(95, seg=32, rings=16, loc=(0, 10, 8)), KA.vgrad(self.SKY[0], self.SKY[1], -20, 90),
                "M_Emit")
        skyobj = sky.build("arena_sky")
        collision = MB()
        collision.add(KA.disc(9.4, n=64, z=0), "#888888")
        collider = collision.build("Col_Ground")
        roots = [floor, backdrop, skyobj, collider]
        roots += [KA.empty("Spot_party", (0, -4, 0)), KA.empty("Spot_enemies", (0, 4, 0)),
                  KA.empty("Spot_camera", (0, -12, 4)), KA.empty("LightAnchor_stage", (0, 0, 5))]
        for i, (x, y) in enumerate(((-10.5, 4), (10.5, 4), (-10.5, 14), (10.5, 14))):
            roots.append(KA.empty(f"LightAnchor_edge_{i}", (x, y, 2.2)))
        B.export_piece(self.TS, "arena", roots)
        collider.hide_render = True
        B.render_cam(f"env_{self.TS}_arena_battlecam", loc=(0, -12, 4), target=(0, 3, 1), fov_deg=70,
                     res=(1600, 900), world=self.WORLD)
        B.render_cam(f"env_{self.TS}_arena_wide", loc=(0, -13, 8.5), target=(0, 8, 1.5), fov_deg=60,
                     res=(1600, 900), world=self.WORLD)
        B.render_cam(f"env_{self.TS}_arena_top", loc=(0.01, -0.01, 34), target=(0, 0, 0), fov_deg=50,
                     res=(1200, 1200), world=self.WORLD, hide=[skyobj])
        print(f"[arena] {self.TS}: {sum(B.tris(o) for o in roots)} tris", flush=True)
        return roots

    # -- first-person corridor, placed by the same rules as DungeonWorld.Initialize / Dress / AgainstWall
    CORRIDOR = [
        "###",
        "#.#", "#.#", "#.#", "#T#", "#.#", "#.#", "#L#", "#.#", "#.#", "#H#", "#.#", "#.#", "#N#", "#.#", "#.#",
        "###",
    ]

    def corridor(self, sheet, base=(400.0, 0.0, 0.0)):
        grid = self.CORRIDOR
        H, W = len(grid), len(grid[0])

        def cell(x, y):
            if 0 <= y < H and 0 <= x < W:
                return grid[y][x]
            return "#"

        def pos(x, y):
            return Vector((base[0] + x * CELL, base[1] + y * CELL, 0.0))

        mock = []

        def place(piece, x, y, rot=0.0, off=(0.0, 0.0)):
            objs = sheet.instance(piece, (x, y), rot=rot, base=base)
            for o in objs:
                o.location = o.location + Vector((off[0], off[1], 0.0))
            mock.extend(objs)

        def on_wall(x, y):
            return cell(x, y) == "#"

        # walls: every '#' touching an open cell (DungeonWorld.Initialize)
        for y in range(H):
            for x in range(W):
                if cell(x, y) != "#":
                    continue
                touches = any(cell(x + dx, y + dy) != "#" for dy in (-1, 0, 1) for dx in (-1, 0, 1))
                if touches:
                    place(f"wall_{'abc'[(x * 17 + y * 31) % 3]}", x, y)
        for y in range(H):
            for x in range(W):
                m = cell(x, y)
                if m == "#":
                    continue
                if m != ">":
                    place(f"floor_{'abc'[(x * 17 + y * 31) % 3]}", x, y)
                if m == "T":
                    start = cell_hash(x, y, 7) % 4
                    for i in range(4):
                        f = (start + i) % 4
                        if on_wall(x + int(DIRS[f][0]), y + int(DIRS[f][1])):
                            tx, ty = DIRS[f]
                            place("chest", x, y, rot=yaw_of(-tx, -ty), off=(tx * CHEST_OFF, ty * CHEST_OFF))
                            break
                elif m == "L":
                    place("door_locked", x, y)
                elif m == "H":
                    start = cell_hash(x, y, 7) % 4
                    for i in range(4):
                        f = (start + i) % 4
                        if on_wall(x + int(DIRS[f][0]), y + int(DIRS[f][1])):
                            tx, ty = DIRS[f]
                            place("spring", x, y, rot=yaw_of(-tx, -ty), off=(tx * SPRING_OFF, ty * SPRING_OFF))
                            break
                elif m == "N":
                    start = cell_hash(x, y, 7) % 4
                    for i in range(4):
                        f = (start + i) % 4
                        if on_wall(x + int(DIRS[f][0]), y + int(DIRS[f][1])):
                            tx, ty = DIRS[f]
                            place("lore_stone", x, y, rot=yaw_of(-tx, -ty), off=(tx * LORE_OFF, ty * LORE_OFF))
                            break
                # sparse torch and wall dressing (DungeonWorld.Initialize / Dress)
                torch_facing = -1
                if (x * 13 + y * 7) % 9 == 0:
                    for f in range(4):
                        if torch_facing >= 0:
                            break
                        if not on_wall(x + int(DIRS[f][0]), y + int(DIRS[f][1])):
                            continue
                        torch_facing = f
                        tx, ty = DIRS[f]
                        place("torch", x, y, rot=yaw_of(-tx, -ty), off=(tx * TORCH_OFF, ty * TORCH_OFF))
                if m in "LB<>":
                    continue
                decor_allowed = m in ".SE"
                for f in range(4):
                    if f == torch_facing:
                        continue
                    wx, wy = x + int(DIRS[f][0]), y + int(DIRS[f][1])
                    if not on_wall(wx, wy):
                        continue
                    tx, ty = DIRS[f]
                    h = cell_hash(x, y, f)
                    if h % 100 < OVERLAY_CHANCE:
                        piece = "overlay_1" if h % 2 == 0 else "overlay_2"
                        place(piece, wx, wy, rot=yaw_of(-tx, -ty))
                    if decor_allowed and (h // 100) % 100 < DECOR_CHANCE:
                        piece = f"decor_{1 + (h // 10000) % 6}"
                        side_sign = -1.0 if ((h >> 20) & 1) == 0 else 1.0
                        sx, sy = -ty * side_sign, tx * side_sign
                        off = (tx * DECOR_OFF + sx * 1.0, ty * DECOR_OFF + sy * 1.0)
                        jitter = ((h >> 21) % 5 - 2) * 12.0
                        place(piece, x, y, rot=yaw_of(-tx, -ty) + jitter, off=off)
                        decor_allowed = False
        # camera: stand at the south end (1, H-2) facing north (-Y), eye height 1.35 m as DungeonWorld.SnapCamera
        cam_p = pos(1, H - 2) + Vector((0, 0, EYE))
        keep = set(mock)
        hide = [o for o in bpy.context.scene.objects if o not in keep]
        return B.render_cam(f"env_{self.TS}_corridor", loc=tuple(cam_p),
                            target=tuple(cam_p + Vector((0.0, -22.0, -0.25))),
                            fov_deg=65, res=(1600, 900), world=self.WORLD, hide=hide)

    def run_all(self):
        sheet = run(self.TS, self.pieces(), world=self.WORLD)
        self.corridor(sheet)
        self.arena()
        return sheet

    # piece builders are provided by the tileset modules
    def floor(self, v):
        raise NotImplementedError

    def wall(self, v):
        raise NotImplementedError

    def door(self, locked):
        raise NotImplementedError

    def stairs(self, up):
        raise NotImplementedError

    def chest(self):
        raise NotImplementedError

    def lore_stone(self):
        raise NotImplementedError

    def trap(self):
        raise NotImplementedError

    def spring(self):
        raise NotImplementedError

    def warp(self):
        raise NotImplementedError

    def torch(self):
        raise NotImplementedError

    def decor(self, i):
        raise NotImplementedError

    def overlay(self, i):
        raise NotImplementedError

    def boss_gate(self):
        raise NotImplementedError

    def foe_marker(self):
        raise NotImplementedError
