"""새벽 길드 (Dawn Guild): the hunter-guild hub that replaces the Hearthvale square.

Writes Assets/_Game/Resources/Art/Town/town.fbx with the same marker names and semantics as town.py
(Spot_spawn, Spot_innkeeper, Spot_shopkeeper, Spot_smith, Spot_guild_clerk, Spot_elder, Spot_gate,
Spot_villager_1..3, Spot_camera_title), Col_* collision boxes and LightAnchor* empties. Blender/town/markers.json
is rewritten beside it. Preview renders go to PREVIEW_DIR (GUILD_PREVIEW_DIR overrides it).

Run:  blender -b --factory-startup --python-exit-code 1 -P Blender/town/guild.py [-- --no-preview]

Layout (Blender metres, Z up, characters face -Y, glass entrance on the -Y side):
  hall interior x -15.5..15.5, y -11.5..11.5, walls 6.6 m high, no roof. This is a cut-away hall: the follow
  camera sits 14 m behind and 12 m above the party, so a ceiling collider would pull it inside.
  Front-left lounge, front-right reception and quest board, mid-left medical bay, mid-right hunter market,
  back-left guild master's dais, back-right workshop behind glass, back-centre violet gate arch.
  A forecourt with paving, trees and a crest sign sits outside the glass front.
"""
import json
import math
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.normpath(os.path.join(HERE, "..", "lib")))  # abyss_bpy, imported by _common

from _common import MB, T, RX, RZ, A, COLS, ANCHORS, SPOTS, anchor, col_box, empty, look_matrix, spot  # noqa: E402
from mathutils import Matrix, Vector  # noqa: E402
import bpy  # noqa: E402

PREVIEW_DIR = os.environ.get("GUILD_PREVIEW_DIR", "/mnt/project-files/art-upgrade/hunter_v1/guild")

# palette (sRGB hex; the Col attribute stores these)
IVORY, IVORY2 = "#f7ecdb", "#ecdcc4"
PLASTER, PLASTER_OUT = "#fdf1de", "#fff4e6"
WOOD, WOOD_D, WOOD_L = "#a86f47", "#6b4530", "#cf9a66"
NAVY = "#243a57"
BLUE, BLUE_L, SKY = "#2f6fc4", "#6aa8ea", "#9ed8f4"
GOLD, SUN = "#e9b651", "#ffb84d"
STEEL, STEEL_D = "#7f8ca3", "#4a5467"
GLASS = "#c4ecf7"
VIOLET, VIOLET_L, VIOLET_D = "#9b6bff", "#e3d2ff", "#3d2a6b"
MINT, GREEN_EMIT, RED, CREAM = "#dff3ea", "#2fd27a", "#e2535e", "#fbf6ea"
LEAF, LEAF_L, POT = "#5fae6a", "#8ad08a", "#c8795a"
GRASS, PAVE = "#9ccf72", "#f2e6d3"
WALL_H = 6.6


def bb(m, x0, y0, z0, x1, y1, z1, col, mat="M_Toon"):
    return m.bbox((x0, y0, z0), (x1, y1, z1), col, mat)


def frame_front(x, y, z):
    """Local XY lies on a plane facing -Y (into the hall from the entrance side); local +Z is the normal."""
    return T(x, y, z) @ RX(90)


def emblem(m, frame, R):
    """Dawn Guild crest: gold ring, blue disc, rising sun over a cream horizon, radial gold rays. Local XY."""
    with m.at(frame):
        m.torus(R * 0.96, R * 0.07, (0, 0, 0.012), GOLD, seg=40, minor=6)
        m.cyl(R * 0.9, 0.010, (0, 0, 0.008), BLUE, seg=40)
        pts = [(R * 0.52 * math.cos(math.pi * k / 12), R * 0.52 * math.sin(math.pi * k / 12)) for k in range(13)]
        m.prism(pts, 0.012, 0.026, SUN)
        m.box((R * 1.12, R * 0.07, 0.02), (0, 0, 0.02), CREAM)
        for k in range(7):
            a = math.radians(22 + k * 23.3)
            m.box((R * 0.18, R * 0.07, 0.012), (R * 0.74 * math.cos(a), R * 0.74 * math.sin(a), 0.014), GOLD,
                  r=(0, 0, math.degrees(a)))


def arch_pts(r, base=0.05, top=3.3, steps=16):
    """Polygon (x, z) of a doorway arch: straight sides from `base` up to `top`, then a half circle of radius r."""
    pts = [(-r, base), (-r, top)]
    for k in range(1, steps + 1):
        a = math.pi - math.pi * k / steps
        pts.append((r * math.cos(a), top + r * math.sin(a)))
    pts.append((r, base))
    return pts


def sofa(m, x, y, yaw):
    """Two-seat sofa; its front (cushion side) faces the direction given by yaw, as in the characters' convention."""
    with m.at(T(x, y, 0) @ RZ(yaw)):
        bb(m, -1.1, -0.45, 0.10, 1.1, 0.45, 0.46, "#4f7fc0")
        bb(m, -1.1, 0.30, 0.46, 1.1, 0.47, 1.05, "#4f7fc0")
        bb(m, -1.25, -0.46, 0.10, -1.08, 0.46, 0.80, "#3b6bb0")
        bb(m, 1.08, -0.46, 0.10, 1.25, 0.46, 0.80, "#3b6bb0")
        bb(m, -1.0, -0.38, 0.46, 1.0, 0.34, 0.56, "#8fb6e8")
        for i, c in enumerate((GOLD, RED)):
            m.ico(0.12, (-0.5 + i, 0.30, 0.8), c, sub=1)
    width_along_x = abs(math.sin(math.radians(yaw))) < 0.5
    size = (2.5, 0.95, 0.95) if width_along_x else (0.95, 2.5, 0.95)
    col_box("Sofa_%d_%d" % (round(x * 10), round(y * 10)), size, (x, y, 0.45))


def plant(m, x, y, s=1.0):
    m.cyl(0.32 * s, 0.5 * s, (x, y, 0.25 * s), POT, seg=12)
    m.cyl(0.36 * s, 0.08 * s, (x, y, 0.52 * s), "#a85d44", seg=12)
    for dx, dy, dz, c in ((0, 0, 0.95, LEAF), (0.24, 0.10, 0.80, LEAF_L), (-0.22, 0.12, 0.84, "#4f9c64"),
                          (0.06, -0.22, 0.76, LEAF_L), (-0.10, -0.18, 1.12, LEAF)):
        m.ico(0.30 * s, (x + dx * s, y + dy * s, dz * s), c, sub=1, scale=(1, 1, 0.85), jitter=0.12, seed=dx + dy)
    m.ico(0.07 * s, (x + 0.1 * s, y - 0.05 * s, 1.35 * s), "#f29bb0", sub=1)
    col_box("Plant_%d_%d" % (round(x * 10), round(y * 10)), (0.7 * s, 0.7 * s, 1.4 * s), (x, y, 0.7 * s))


def tree(m, x, y, s=1.0):
    m.cyl(0.13 * s, 2.0 * s, (x, y, 1.0 * s), WOOD_D, seg=8)
    for dx, dy, dz, r, c in ((0, 0, 2.7, 1.05, "#7fc27a"), (0.6, 0.3, 2.3, 0.75, "#94d088"),
                             (-0.55, -0.2, 2.35, 0.7, "#6fb36e"), (0.1, -0.45, 3.2, 0.7, "#a6dd92")):
        m.ico(r * s, (x + dx * s, y + dy * s, dz * s), c, sub=2, jitter=0.10, seed=dx + dz)
    col_box("Tree_%d_%d" % (round(x * 10), round(y * 10)), (0.4 * s, 0.4 * s, 2.0 * s), (x, y, 1.0 * s))


def bench(m, x, y, yaw):
    with m.at(T(x, y, 0) @ RZ(yaw)):
        bb(m, -0.9, -0.25, 0.40, 0.9, 0.25, 0.52, WOOD)
        bb(m, -0.9, 0.22, 0.52, 0.9, 0.30, 1.0, WOOD)
        for xx in (-0.75, 0.75):
            bb(m, xx - 0.05, -0.2, 0, xx + 0.05, 0.2, 0.40, STEEL_D)


def lamp(m, x, y):
    m.cyl(0.06, 3.0, (x, y, 1.5), STEEL_D, seg=8)
    m.box((0.36, 0.36, 0.42), (x, y, 3.2), SUN, mat="M_Emit")
    m.cone(0.30, 0.22, (x, y, 3.6), BLUE, seg=4)
    anchor((x, y, 3.1), "street")


# ---------------------------------------------------------------- hall

def build_floor(m):
    bb(m, -15.5, -11.5, -0.13, 15.5, 11.5, -0.012, "#b9a893")  # grout base, top just under the tiles
    for ix in range(-15, 16):
        for iy in range(-11, 12):
            c = IVORY if (ix + iy) % 2 == 0 else IVORY2
            m.box((0.94, 0.94, 0.02), (ix, iy, -0.01), c)  # tile tops at z = 0
    bb(m, -14.9, -10.9, 0.0, -5.3, -6.1, 0.014, "#3f63a5")  # lounge rug
    bb(m, -14.5, -10.5, 0.014, -5.7, -6.5, 0.022, "#5b84c8")
    bb(m, -15.4, -5.0, 0.0, -7.3, 4.4, 0.012, MINT)  # medical bay
    bb(m, 5.2, 4.6, 0.0, 15.4, 11.4, 0.012, "#8a9099")  # workshop
    bb(m, 5.2, 6.8, 0.012, 5.5, 9.2, 0.02, GOLD)  # workshop threshold strip
    m.cyl(1.9, 0.012, (0, 9.6, 0.006), VIOLET_D, seg=40)  # gate pad
    m.torus(1.9, 0.08, (0, 9.6, 0.02), VIOLET, seg=40, minor=6)
    emblem(m, T(0, -1.0, 0.0), 2.6)  # sunrise crest on the walkway


def build_walls(m):
    # Outer shell, interior wainscot, blue stripe and plaster.
    bb(m, -16.0, -12.0, 0.0, -15.5, 12.0, WALL_H, PLASTER_OUT)
    bb(m, 15.5, -12.0, 0.0, 16.0, 12.0, WALL_H, PLASTER_OUT)
    bb(m, -16.0, 11.5, 0.0, 16.0, 12.0, WALL_H, PLASTER_OUT)
    bb(m, -16.0, -12.0, 5.6, 16.0, -11.5, WALL_H, PLASTER_OUT)  # header over the glass
    for x0, x1, y0, y1 in ((-15.5, -15.44, -11.5, 11.5), (15.44, 15.5, -11.5, 11.5), (-15.5, 15.5, 11.44, 11.5)):
        bb(m, x0, y0, 0.0, x1, y1, 1.1, WOOD)
        bb(m, x0, y0, 1.1, x1, y1, 1.24, BLUE)
        bb(m, x0, y0, 1.24, x1, y1, WALL_H - 0.02, PLASTER)
    for x in (-15.75, 15.75):
        bb(m, x - 0.27, -12.0, WALL_H, x + 0.27, 12.0, WALL_H + 0.12, BLUE)  # parapet caps
    bb(m, -16.0, -12.0, WALL_H, 16.0, -11.5, WALL_H + 0.12, BLUE)
    bb(m, -16.0, 11.5, WALL_H, 16.0, 12.0, WALL_H + 0.12, BLUE)
    # Front glass: sill, mullions every 2 m, a 4.4 m entrance gap at x -2.2..2.2.
    bb(m, -16.0, -12.0, 0.0, 16.0, -11.5, 0.35, STEEL_D)
    mull = [-15.5, -14, -12, -10, -8, -6, -4, -2.2, 2.2, 4, 6, 8, 10, 12, 14, 15.5]
    for x in mull:
        bb(m, x - 0.08, -12.0, 0.35, x + 0.08, -11.5, 5.6, STEEL_D)
    for a, b in zip(mull, mull[1:]):
        if a == -2.2 and b == 2.2:
            continue
        bb(m, a + 0.08, -11.95, 0.35, b - 0.08, -11.9, 5.5, GLASS, mat="M_Clear")
    emblem(m, frame_front(-7.8, -12.03, 6.0), 0.6)
    emblem(m, frame_front(7.8, -12.03, 6.0), 0.6)
    text_mesh("Sign_DawnGuild", "DAWN GUILD", (0.0, -12.05, 5.9), 0.75, BLUE)
    # Entrance canopy, striped blue and cream, on two posts outside the glass.
    for k in range(8):
        bb(m, -3.4 + k * 0.85, -14.2, 3.9, -2.55 + k * 0.85, -12.2, 4.05, BLUE if k % 2 == 0 else CREAM)
    for x in (-3.4, 3.4):
        m.cyl(0.07, 3.9, (x, -14.2, 1.95), STEEL_D, seg=8)
    # Back wall: a gate-status screen, hunter posters and a crest.
    bb(m, 4.4, 11.3, 1.4, 7.6, 11.44, 3.5, "#17324f")
    bb(m, 4.5, 11.2, 1.5, 7.5, 11.3, 3.4, "#0f2236")
    for k, (c, w) in enumerate(((RED, 2.4), ("#ffd166", 1.7), (GREEN_EMIT, 2.9), (SKY, 1.2))):
        bb(m, 4.7, 11.15, 1.7 + k * 0.4, 4.7 + w, 11.19, 1.82 + k * 0.4, c, mat="M_Emit")
    for px, pc in ((2.7, "#ffe9b8"), (3.8, "#cfe8ff")):
        bb(m, px, 11.39, 1.7, px + 0.9, 11.42, 3.5, pc)
        m.ico(0.32, (px + 0.45, 11.36, 2.5), VIOLET_D, sub=1, scale=(1, 0.25, 1.1))
        bb(m, px + 0.1, 11.36, 1.8, px + 0.8, 11.37, 1.95, RED)
    emblem(m, frame_front(-5.6, 11.36, 4.6), 0.45)
    # Two-storey lobby gallery on the side walls: visual only, nobody walks on it.
    for x0, x1 in ((-15.5, -11.4), (11.4, 15.5)):
        bb(m, x0, -11.5, 4.2, x1, 11.5, 4.42, WOOD_L)
        bb(m, x0, -11.5, 4.42, x1, -11.44, 5.4, WOOD)
    for x in (-11.45, 11.35):
        bb(m, x - 0.04, -11.5, 4.42, x + 0.04, 11.5, 5.4, WOOD)
        bb(m, x - 0.05, -11.5, 5.35, x + 0.05, 11.5, 5.45, WOOD)
        for y in range(-11, 12, 2):
            bb(m, x - 0.03, y - 0.03, 4.42, x + 0.03, y + 0.03, 5.35, WOOD_D)


def text_mesh(name, body, loc, size, col):
    """Latin sign text (Blender's built-in font has no Hangul): converted to a flat mesh facing -Y."""
    bpy.ops.object.text_add(location=(0, 0, 0))
    t = bpy.context.object
    t.data.body = body
    t.data.size = size
    t.data.align_x = "CENTER"
    bpy.ops.object.convert(target="MESH")
    o = bpy.context.object
    o.name = name
    o.rotation_euler = (math.radians(90), 0, 0)
    o.location = loc
    bpy.ops.object.select_all(action="DESELECT")
    o.select_set(True)
    bpy.context.view_layer.objects.active = o
    bpy.ops.object.transform_apply(location=False, rotation=True, scale=False)
    A.paint(o, col, "M_Toon")
    return o


def build_colliders_walls():
    col_box("WallWest", (0.5, 23.0, WALL_H), (-15.75, 0.5, WALL_H / 2))
    col_box("WallEast", (0.5, 23.0, WALL_H), (15.75, 0.5, WALL_H / 2))
    col_box("WallBack", (32.0, 0.5, WALL_H), (0.0, 11.75, WALL_H / 2))
    col_box("FrontWest", (13.3, 0.5, 5.6), (-8.85, -11.75, 2.8))  # glass from x -15.5 to -2.2
    col_box("FrontEast", (13.3, 0.5, 5.6), (8.85, -11.75, 2.8))  # glass from x 2.2 to 15.5


def build_lounge(m):
    # West wall screen (gate alerts): frame, glowing panel and bars.
    # Wall faces are at x=-15.44 (wainscot below); the screen hangs on the room side.
    bb(m, -15.44, -10.4, 2.5, -15.36, -6.0, 4.5, "#1d2433")
    bb(m, -15.36, -10.3, 2.6, -15.34, -6.1, 4.4, "#0d1826", mat="M_Emit")
    for k, (c, w) in enumerate(((RED, 2.6), (SUN, 1.8), (GREEN_EMIT, 3.2), (SKY, 2.2))):
        bb(m, -15.34, -10.0, 2.85 + k * 0.38, -15.33, -10.0 + w, 3.07 + k * 0.38, c, mat="M_Emit")
    sofa(m, -12.2, -8.2, 90)  # front faces +X, toward the table
    sofa(m, -6.2, -8.2, -90)  # front faces -X
    bb(m, -9.8, -8.8, 0.30, -8.6, -7.6, 0.42, "#f0e2c8")
    m.cyl(0.05, 0.3, (-9.2, -8.2, 0.15), STEEL_D, seg=8)
    col_box("LoungeTable", (1.2, 1.2, 0.5), (-9.2, -8.2, 0.25))
    plant(m, -14.6, -11.0)
    plant(m, -4.8, -10.4, 1.1)
    plant(m, -6.4, -10.9, 0.8)


def build_reception(m):
    bb(m, 4.6, -6.1, 0.0, 11.4, -4.9, 1.05, NAVY)
    bb(m, 4.5, -6.2, 1.05, 11.5, -4.8, 1.12, CREAM)
    bb(m, 4.6, -6.16, 0.45, 11.4, -6.1, 0.5, SKY, mat="M_Emit")
    emblem(m, frame_front(8.0, -6.18, 0.78), 0.34)
    col_box("Reception", (6.9, 1.2, 1.1), (8.0, -5.5, 0.55))
    bb(m, 7.5, -5.2, 1.12, 8.5, -5.05, 1.9, "#2b313b")
    bb(m, 7.6, -5.04, 1.26, 8.4, -5.02, 1.80, SKY, mat="M_Emit")
    m.cyl(0.12, 0.10, (5.6, -5.4, 1.17), GOLD, seg=10)
    m.ico(0.09, (10.2, -5.4, 1.25), BLUE_L, sub=1)
    # Quest board on the east wall with a gate-alert screen above it.
    bb(m, 15.2, -10.8, 0.9, 15.45, -6.2, 2.6, WOOD_D)
    bb(m, 15.12, -10.6, 1.05, 15.2, -6.4, 2.45, "#c99a6b")
    for i in range(14):
        y = -10.3 + (i % 7) * 0.6
        z = 1.25 + (i // 7) * 0.9 + 0.1 * (i % 3)
        bb(m, 15.06, y, z, 15.12, y + 0.42, z + 0.46, ("#fff4c2", "#ffd6e0", "#d6f0ff", "#d9f7d9")[i % 4])
    bb(m, 15.1, -10.7, 2.65, 15.45, -6.3, 2.85, BLUE)
    bb(m, 15.36, -10.4, 3.0, 15.44, -6.6, 4.5, "#1d2433")
    bb(m, 15.33, -10.3, 3.1, 15.36, -6.7, 4.4, "#0d1826", mat="M_Emit")
    for k, (c, w) in enumerate(((RED, 2.0), (GREEN_EMIT, 2.8), (SUN, 1.6))):
        bb(m, 15.31, -10.1, 3.35 + k * 0.4, 15.33, -10.1 + w * 0.5, 3.55 + k * 0.4, c, mat="M_Emit")
    plant(m, 14.3, -10.9, 1.0)


def build_market(m):
    bb(m, 9.4, -2.5, 0.0, 11.1, 2.8, 1.05, WOOD)  # counter body
    bb(m, 9.3, -2.7, 1.05, 11.2, 3.0, 1.12, WOOD_L)
    bb(m, 9.25, -2.8, 1.12, 11.2, 3.1, 1.3, GLASS, mat="M_Clear")  # display case
    for i, c in enumerate((RED, BLUE_L, GREEN_EMIT, SUN, "#c77ddd")):
        for j in range(3):
            m.ico(0.10, (9.6 + 0.3 * i, -2.2 + 0.9 * j, 1.25), c, sub=1, scale=(1, 1, 1.4),
                  mat="M_Emit" if j == 1 else "M_Toon")
    col_box("MarketCounter", (1.7, 5.3, 1.2), (10.25, 0.15, 0.6))
    for k in range(6):  # striped canopy
        bb(m, 9.3 + k * 0.33, -2.8, 2.5, 9.63 + k * 0.33, 3.2, 2.6, RED if k % 2 == 0 else CREAM)
    # Wall shelves on the east wall: potions with glowing vials, sword racks and an armour bench.
    bb(m, 15.2, -4.5, 0.2, 15.45, 3.9, 3.4, "#7a5a44")
    for z in (0.5, 1.4, 2.3, 3.2):
        bb(m, 14.5, -4.5, z, 15.45, 3.9, z + 0.06, WOOD_L)
        for i in range(8):
            y = -4.0 + i * 1.0
            c = (RED, BLUE_L, GREEN_EMIT, SUN, VIOLET, "#ff8fa3", SKY, GOLD)[(i + int(z * 3)) % 8]
            m.cyl(0.11, 0.34, (14.9, y, z + 0.23), c, seg=8, mat="M_Emit" if i % 4 == 0 else "M_Toon")
            m.cyl(0.05, 0.08, (14.9, y, z + 0.44), "#e8e0cc", seg=6)
    for i in range(3):
        bb(m, 14.94, -2.5 + i * 2.2, 2.1, 15.2, -2.2 + i * 2.2, 2.2, STEEL)
        bb(m, 14.98, -2.6 + i * 2.2, 2.0, 15.1, -2.1 + i * 2.2, 2.06, GOLD)
    for x in (12.2, 13.6):  # weapon rack: sword blades on a rail
        bb(m, x - 0.04, 3.5, 0.0, x + 0.04, 3.6, 1.6, STEEL_D)
    bb(m, 12.2, 3.5, 1.6, 13.6, 3.6, 1.66, WOOD_L)
    for i in range(6):
        x = 12.35 + i * 0.22
        bb(m, x, 3.45, 1.66, x + 0.05, 3.55, 2.5, STEEL)
        bb(m, x - 0.05, 3.45, 1.62, x + 0.1, 3.55, 1.72, GOLD)
    bb(m, 12.8, 2.0, 0.0, 13.9, 3.2, 0.9, WOOD_L)  # crates
    bb(m, 12.8, 2.0, 0.9, 13.4, 2.6, 1.6, WOOD)
    m.cyl(0.42, 0.9, (13.9, -0.2, 0.45), WOOD_D, seg=12)


def build_workshop(m):
    # Glass wall (x = 5) with a door gap at y 6.8..9.2, steel frame and a top rail.
    bb(m, 4.9, 4.6, 0.0, 5.1, 6.8, 4.0, GLASS, mat="M_Clear")
    bb(m, 4.9, 9.2, 0.0, 5.1, 11.4, 4.0, GLASS, mat="M_Clear")
    for y in (4.6, 6.8, 9.2, 11.4):
        bb(m, 4.85, y - 0.1, 0.0, 5.15, y + 0.1, 4.1, STEEL_D)
    bb(m, 4.85, 4.5, 4.0, 5.15, 11.5, 4.12, STEEL_D)
    col_box("WorkshopWallA", (0.25, 2.2, 4.0), (5.0, 5.7, 2.0))
    col_box("WorkshopWallB", (0.25, 2.2, 4.0), (5.0, 10.3, 2.0))
    # Anvil press, workbench, pegboard with tools, and the furnace with a glowing mouth.
    bb(m, 10.3, 8.4, 0.0, 11.9, 9.6, 0.9, STEEL_D)
    bb(m, 10.0, 8.2, 0.9, 12.2, 9.8, 1.25, STEEL)
    m.cone(0.22, 0.6, (12.6, 9.0, 1.05), STEEL, seg=8)
    col_box("Anvil", (2.2, 1.6, 1.25), (11.1, 9.0, 0.62))
    bb(m, 7.0, 10.4, 0.0, 14.2, 11.4, 0.95, "#8b6447")
    bb(m, 6.9, 10.3, 0.95, 14.3, 11.5, 1.02, WOOD_L)
    col_box("Bench", (7.3, 1.1, 1.0), (10.6, 10.9, 0.5))
    bb(m, 6.3, 11.42, 1.6, 14.6, 11.5, 4.0, "#c4a279")
    for i in range(10):
        x = 6.6 + i * 0.8
        bb(m, x, 11.36, 2.4 + (i % 3) * 0.4, x + 0.06, 11.40, 3.2 + (i % 3) * 0.4, STEEL)
    for i, (x, z) in enumerate(((7.2, 2.6), (8.0, 2.9), (10.6, 2.4), (12.0, 3.2))):
        bb(m, x, 11.33, z, x + 0.12, 11.37, z + 0.5, SUN if i % 2 else STEEL)
    bb(m, 12.6, 4.8, 0.0, 14.6, 6.6, 1.6, STEEL_D)
    bb(m, 12.9, 4.78, 0.6, 14.3, 4.82, 1.2, "#ff9d4a", mat="M_Emit")
    col_box("Furnace", (2.0, 1.8, 1.6), (13.6, 5.7, 0.8))
    for x, y, s in ((13.0, 9.9, 0.8), (14.3, 10.4, 0.6)):
        bb(m, x - s / 2, y - s / 2, 0.0, x + s / 2, y + s / 2, s, "#b08a5a")


def build_medical(m):
    def bed(x, y):
        bb(m, x - 1.0, y - 0.55, 0.22, x + 1.0, y + 0.55, 0.44, "#c9d6e2")
        bb(m, x - 1.0, y - 0.55, 0.44, x + 1.0, y + 0.55, 0.58, "#fbfdff")
        bb(m, x - 0.25, y - 0.56, 0.58, x + 1.0, y + 0.56, 0.66, "#7aa8d8")
        bb(m, x - 0.92, y - 0.38, 0.58, x - 0.5, y + 0.38, 0.72, "#ffffff")
        col_box("Bed_%d_%d" % (round(x * 10), round(y * 10)), (2.0, 1.1, 0.6), (x, y, 0.3))
    bed(-13.2, -2.0)
    bed(-13.2, 1.6)
    m.cyl(0.03, 2.0, (-11.4, -0.2, 1.0), STEEL, seg=6)  # IV stand and bag
    m.box((0.22, 0.12, 0.4), (-11.4, -0.2, 2.1), GLASS, mat="M_Clear")
    bb(m, -15.44, -1.6, 2.6, -15.38, 1.2, 3.9, "#ffffff")  # green cross board on the west wall
    bb(m, -15.38, -0.1, 3.0, -15.36, 0.1, 3.5, GREEN_EMIT, mat="M_Emit")
    bb(m, -15.38, -0.5, 3.1, -15.36, 0.5, 3.4, GREEN_EMIT, mat="M_Emit")
    bb(m, -15.5, -5.0, 0.0, -14.6, -3.6, 1.8, "#dfe8ef")
    for z in (0.5, 1.1):
        bb(m, -14.58, -4.9, z, -14.52, -3.7, z + 0.05, STEEL)
    col_box("MedCabinet", (0.9, 1.4, 1.8), (-15.05, -4.3, 0.9))
    bb(m, -7.9, -2.7, 0.0, -7.1, 3.4, 1.05, "#f3f6f9")  # nurse counter, mint top
    bb(m, -8.0, -2.8, 1.05, -7.0, 3.5, 1.12, "#7fd2b8")
    col_box("MedCounter", (0.9, 6.2, 1.1), (-7.5, 0.35, 0.55))


def build_office(m):
    # Raised dais (0.32 m) with two steps at the centre front, desk, bookcase and the banner.
    bb(m, -15.5, 6.3, 0.0, -6.4, 11.5, 0.32, "#8a6242")
    bb(m, -15.5, 6.3, 0.30, -6.4, 11.5, 0.34, "#b07d52")
    bb(m, -10.9, 5.6, 0.0, -9.4, 6.0, 0.16, "#b07d52")
    bb(m, -10.9, 6.0, 0.0, -9.4, 6.3, 0.32, "#b07d52")
    col_box("DaisBody", (9.1, 5.2, 0.32), (-10.95, 8.9, 0.16))
    col_box("DaisStep1", (1.5, 0.4, 0.16), (-10.15, 5.8, 0.08))
    col_box("DaisStep2", (1.5, 0.3, 0.32), (-10.15, 6.15, 0.16))
    bb(m, -11.7, 6.4, 0.32, -8.5, 7.4, 1.0, "#5b3e2c")  # desk
    bb(m, -11.8, 6.3, 1.0, -8.4, 7.5, 1.06, "#7a5538")
    bb(m, -10.6, 6.9, 1.06, -9.6, 7.1, 1.6, "#2b313b")
    bb(m, -10.5, 6.92, 1.14, -9.7, 6.95, 1.52, SKY, mat="M_Emit")
    col_box("Desk", (3.2, 1.0, 0.74), (-10.1, 6.9, 0.69))
    bb(m, -15.5, 10.3, 0.32, -12.0, 11.5, 2.8, "#6b4a34")  # bookcase with spines
    for r in range(3):
        for i in range(10):
            x = -15.3 + i * 0.33
            z0 = 0.34 + r * 0.7
            bb(m, x, 11.2, z0, x + 0.22, 11.38, z0 + 0.5, ("#e2535e", "#2f6fc4", "#2fd27a", "#ffb84d", "#9b6bff")[(i + r) % 5])
    col_box("Bookcase", (3.5, 1.2, 2.5), (-13.75, 10.9, 1.57))
    banner = [(x - 9.0, z) for x, z in ((-1.0, 6.0), (1.0, 6.0), (1.0, 3.2), (0.0, 2.5), (-1.0, 3.2))]
    m.slab(banner, 0.05, BLUE, y=11.39)
    emblem(m, frame_front(-9.0, 11.36, 4.6), 0.75)


def build_gate(m):
    # Stone pillars, a violet arch with an emissive portal, the arch crown in gold.
    for x in (-2.05, 2.05):
        bb(m, x - 0.27, 10.4, 0.0, x + 0.27, 10.8, 3.3, STEEL)
        bb(m, x - 0.33, 10.36, 0.0, x + 0.33, 10.84, 0.25, STEEL_D)
    m.torus(2.05, 0.2, (0, 10.6, 3.3), GOLD, seg=36, minor=8, m=RX(90), arc=0.5)
    m.slab(arch_pts(1.75), 0.08, VIOLET, mat="M_Emit", y=10.52)
    m.slab(arch_pts(1.45, base=0.08), 0.04, VIOLET_L, mat="M_Emit", y=10.46)
    col_box("GatePillarA", (0.6, 0.5, 3.3), (-2.05, 10.6, 1.65))
    col_box("GatePillarB", (0.6, 0.5, 3.3), (2.05, 10.6, 1.65))


def build_outside(m):
    """Forecourt paving, crest sign, flagpole, benches, lamps, trees and a skyline behind the hall."""
    bb(m, -21.0, -24.0, -0.02, 21.0, -12.0, 0.0, PAVE)
    for x in range(-20, 21, 3):
        bb(m, x - 0.04, -24.0, 0.0, x + 0.04, -12.0, 0.01, "#c8c0b1")
    for y in range(-23, -11, 3):
        bb(m, -21.0, y - 0.04, 0.0, 21.0, y + 0.04, 0.01, "#c8c0b1")
    bb(m, 3.5, -15.0, 1.9, 5.7, -14.8, 3.2, BLUE)
    bb(m, 3.4, -15.05, 1.8, 5.8, -14.95, 1.95, GOLD)
    emblem(m, frame_front(4.6, -15.02, 2.6), 0.42)
    m.cyl(0.08, 1.8, (4.6, -15.4, 0.9), STEEL_D, seg=8)
    m.cyl(0.06, 7.0, (-12.8, -17.0, 3.5), STEEL, seg=8)
    m.slab([(-12.7, 6.8), (-11.0, 6.5), (-11.0, 4.6), (-12.7, 4.9)], 0.05, BLUE, y=-17.05)
    emblem(m, frame_front(-11.9, -17.07, 5.7), 0.5)
    for x, y in ((-8.5, -13.5), (8.5, -13.5), (-19.0, -15.0), (19.0, -15.0)):
        lamp(m, x, y)
    bench(m, -6.0, -17.5, 0)
    bench(m, 7.0, -18.0, 0)
    for x, y in ((-18.5, -19.0), (18.5, -19.0), (-16.0, -22.5), (16.0, -22.5), (-7.0, 13.0), (7.0, 13.0),
                 (-19.0, 6.0), (19.0, 6.0), (-19.0, -4.0), (19.0, -4.0)):
        tree(m, x, y, 1.0 + 0.1 * ((x + y) % 3))
    # Soft pastel hills behind the hall (visual only, outside the boundary) to close the title shot.
    for i, x in enumerate(range(-50, 56, 9)):
        m.ico(7.0 + (i % 3) * 1.5, (x, 52 + (i % 4) * 3, 0.0), ("#a9d9a0", "#b9e2c2", "#9fcf9a")[i % 3],
              sub=2, scale=(1.3, 1.0, 0.55), jitter=0.10, seed=i)


def build_boundaries():
    col_box("BoundaryWest", (1.0, 38.0, 8.0), (-21.5, -5.0, 4.0))
    col_box("BoundaryEast", (1.0, 38.0, 8.0), (21.5, -5.0, 4.0))
    col_box("BoundarySouth", (44.0, 1.0, 8.0), (0.0, -24.5, 4.0))
    col_box("BoundaryNorth", (44.0, 1.0, 8.0), (0.0, 14.5, 4.0))


def build_lights():
    for loc, tag in (((-10.0, -8.5, 4.0), "lounge"), ((8.0, -6.5, 3.8), "reception"), ((12.6, -0.5, 3.8), "market"),
                     ((8.0, 8.0, 3.6), "workshop"), ((-11.0, 0.0, 3.8), "medical"), ((-10.5, 9.0, 3.8), "office"),
                     ((0.0, 8.6, 3.4), "gate"), ((0.0, -2.0, 4.2), "lobby")):
        anchor(loc, tag)


def build_scene():
    hall = MB()
    build_floor(hall)
    build_walls(hall)
    build_lounge(hall)
    build_reception(hall)
    build_market(hall)
    build_workshop(hall)
    build_medical(hall)
    build_office(hall)
    build_gate(hall)
    for x, y in ((-4.8, -10.4), (4.8, -10.4), (14.6, 4.6), (-14.6, 10.6), (3.8, 9.4), (-4.9, 9.4)):
        plant(hall, x, y, 1.0)
    hall.build("Hall_Interior")
    build_colliders_walls()
    outside = MB()
    build_outside(outside)
    outside.build("Forecourt_Decor")
    grass = MB()
    grass.box((120.0, 120.0, 0.4), (0, 0, -0.23), GRASS)
    grass.build("Ground_Grass")
    col_box("Ground", (120.0, 120.0, 0.4), (0, 0, -0.23))
    build_boundaries()
    build_lights()


def markers():
    spots = [
        ("Spot_spawn", (0.0, -9.4, 0.0), 180.0),
        ("Spot_innkeeper", (-8.8, 0.4, 0.0), 90.0),
        ("Spot_shopkeeper", (11.9, -0.5, 0.0), -90.0),
        ("Spot_smith", (8.4, 8.3, 0.0), -90.0),
        ("Spot_guild_clerk", (8.0, -3.9, 0.0), 0.0),
        ("Spot_elder", (-10.2, 7.9, 0.32), 0.0),
        ("Spot_gate", (0.0, 8.8, 0.0), 180.0),
        ("Spot_villager_1", (-9.5, -5.2, 0.0), 0.0),
        ("Spot_villager_2", (-5.0, -10.2, 0.0), -90.0),
        ("Spot_villager_3", (-13.6, -4.2, 0.0), 60.0),
    ]
    for name, loc, yaw in spots:
        spot(name, loc, yaw)
    staff = [Vector(SPOTS[n].location) for n in ("Spot_innkeeper", "Spot_smith", "Spot_elder")]
    target = sum(staff, Vector()) / 3 + Vector((0, 0, 1.5))
    cam_loc = Vector((-21.0, -31.0, 15.5))
    cam = empty("Spot_camera_title", tuple(cam_loc), kind="CUBE", size=1, matrix=look_matrix(cam_loc, target))
    SPOTS[cam.name] = cam
    return target


def write_manifest(target):
    manifest = {
        "asset": "Art/Town/town",
        "name": "새벽 길드 (Dawn Guild) hub",
        "units": "metres",
        "blender_axes": "Z-up; humanoid forward -Y",
        "unity_position_mapping": "(Blender x, Blender z, -Blender y)",
        "usage": "Use imported Spot_ transform positions for actors. Spot_gate is an interaction anchor, not an obstacle. "
                 "Title camera target = mean(innkeeper, smith, elder) + 1.5 m up, which TownWorld.cs computes itself.",
        "playable_bounds_blender": {"min": [-21.0, -24.0, 0.0], "max": [21.0, 14.0, 0.0]},
        "hall_interior_blender": {"min": [-15.5, -11.5, 0.0], "max": [15.5, 11.5, WALL_H]},
        "camera_title_target_blender": [round(v, 4) for v in target],
        "camera_title_target_unity": [round(target[0], 4), round(target[2], 4), round(-target[1], 4)],
        "camera_title_lens_mm": 30,
        "markers": {},
        "collision": "All Col_ meshes are hidden from Blender renders; Unity strips renderers and creates MeshColliders. "
                     "Col_Ground top=-0.03m. Hall walls and glass are colliders; the hall has no roof collider (cut-away). "
                     "Gallery, crests, banners and the skyline are visual only.",
        "doors": "Front entrance: open 4.4 m gap at x -2.2..2.2. Workshop: glass door gap at x=5, y 6.8..9.2.",
        "light_anchors": [{"name": e.name, "blender_position": list(e.location),
                           "unity_position": [e.location.x, e.location.z, -e.location.y]} for e in ANCHORS],
    }
    for name, e in SPOTS.items():
        q = e.matrix_world.to_quaternion()
        p = e.location
        manifest["markers"][name] = {
            "blender_position": list(p),
            "blender_euler_deg": [math.degrees(v) for v in e.rotation_euler],
            "blender_quaternion_xyzw": [q.x, q.y, q.z, q.w],
            "unity_position": [p.x, p.z, -p.y],
        }
    with open(os.path.join(HERE, "markers.json"), "w", encoding="utf-8") as f:
        json.dump(manifest, f, ensure_ascii=False, indent=2)


# ---------------------------------------------------------------- previews

ENGINE = os.environ.get("GUILD_ENGINE", "eevee").lower()  # "eevee" (lit, ~20 s/frame) or "workbench" (flat QA)


def setup_preview(world=(0.62, 0.78, 0.9)):
    sc = bpy.context.scene
    if ENGINE == "eevee":
        try:
            sc.render.engine = "BLENDER_EEVEE_NEXT"
        except TypeError:
            sc.render.engine = "BLENDER_EEVEE"
        sc.view_settings.view_transform = "Standard"
        sc.render.resolution_percentage = 100
        if sc.world is None:
            sc.world = bpy.data.worlds.new("W")
        sc.world.use_nodes = True
        bg = sc.world.node_tree.nodes.get("Background")
        if bg is not None:
            bg.inputs["Color"].default_value = (0.78, 0.88, 0.98, 1.0)
            bg.inputs["Strength"].default_value = 0.9
        if "PreviewSun" not in bpy.data.objects:
            lamp = bpy.data.lights.new("PreviewSun", "SUN")
            lamp.energy = 3.0
            lamp.color = (1.0, 0.95, 0.88)
            sun = bpy.data.objects.new("PreviewSun", lamp)
            sc.collection.objects.link(sun)
            sun.rotation_euler = (math.radians(52), 0.0, math.radians(35))
        return
    sc.render.engine = "BLENDER_WORKBENCH"
    sh = sc.display.shading
    sh.light = "STUDIO"
    sh.color_type = "VERTEX"
    sh.show_cavity = True
    sh.show_object_outline = True
    sh.show_shadows = True
    sc.world = sc.world or bpy.data.worlds.new("W")
    sc.world.color = world
    sc.render.film_transparent = False


def render_view(name, loc, target=None, lens=24.5, size=(1600, 900), ortho=None, rot=None):
    sc = bpy.context.scene
    setup_preview()
    os.makedirs(PREVIEW_DIR, exist_ok=True)
    cd = bpy.data.cameras.new("ShotCam")
    cd.lens = lens
    cd.clip_start = 0.05
    cd.clip_end = 900
    if ortho:
        cd.type = "ORTHO"
        cd.ortho_scale = ortho
    cam = bpy.data.objects.new("ShotCam", cd)
    sc.collection.objects.link(cam)
    if rot is not None:
        cam.matrix_world = Matrix.Translation(Vector(loc)) @ rot
    else:
        cam.matrix_world = look_matrix(Vector(loc), Vector(target))
    sc.camera = cam
    sc.render.resolution_x, sc.render.resolution_y = size
    sc.render.filepath = os.path.join(PREVIEW_DIR, name + ".png")
    bpy.ops.render.render(write_still=True)
    bpy.data.objects.remove(cam)
    bpy.data.cameras.remove(cd)
    return sc.render.filepath


def render_previews(target):
    render_view("guild_title_camera", (-21.0, -31.0, 15.5), target=target, lens=30, size=(1600, 1000))
    # Follow camera at spawn: TownWorld offset (10, 12, -14) Unity = (10, 14, 12) Blender, aimed 0.8 m above the feet.
    spawn = Vector(SPOTS["Spot_spawn"].location)
    render_view("guild_spawn_follow", spawn + Vector((10.0, 14.0, 12.0)), target=spawn + Vector((0, 0, 0.8)),
                lens=24.5, size=(1600, 900))
    # Eye height at spawn, looking toward the gate arch.
    gate = Vector(SPOTS["Spot_gate"].location)
    render_view("guild_spawn_eye", spawn + Vector((0, 0, 1.45)), target=gate + Vector((0, 1.0, 1.6)), lens=28,
                size=(1600, 900))
    render_view("guild_plan_topdown", (0, 0.001, 80), rot=Matrix.Identity(4), ortho=50, size=(1400, 1000))
    render_view("guild_reception_lounge", (-2.0, -9.5, 4.2), target=(4.0, 0.5, 1.2), lens=26, size=(1600, 900))
    render_view("guild_market_workshop", (2.0, -6.0, 4.6), target=(11.0, 5.5, 1.2), lens=26, size=(1600, 900))
    render_view("guild_medical_office", (-4.0, 1.0, 4.6), target=(-11.5, 6.5, 1.2), lens=26, size=(1600, 900))
    render_view("guild_gate", (0.0, -2.5, 3.0), target=(0.0, 10.6, 2.4), lens=30, size=(1600, 900))


def main():
    A.reset_scene()
    SPOTS.clear()
    ANCHORS.clear()
    COLS.clear()
    build_scene()
    target = markers()
    write_manifest(tuple(target))
    objects = [o for o in bpy.context.scene.objects if o.type in ("MESH", "EMPTY")]
    A.export_fbx("Town/town.fbx", objects)
    A.save_blend("town_guild")
    if "--no-preview" not in sys.argv:
        render_previews(target)
    print("GUILD_COMPLETE spots=%d colliders=%d light_anchors=%d" % (len(SPOTS), len(COLS), len(ANCHORS)), flush=True)


if __name__ == "__main__":
    main()
