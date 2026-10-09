"""새벽 길드 거리 (Dawn Guild street): an outdoor dusk city block around the Dawn Guild HQ.

Writes Assets/_Game/Resources/Art/Town/town.fbx with the marker names of town.py (Spot_spawn, Spot_innkeeper,
Spot_shopkeeper, Spot_smith, Spot_guild_clerk, Spot_elder, Spot_gate, Spot_villager_1..3, Spot_camera_title),
Col_* collision boxes and LightAnchor* empties. Blender/town/markers.json and Blender/town/guild_atmosphere.json
are rewritten beside this script. Preview renders go to PREVIEW_DIR (GUILD_PREVIEW_DIR overrides it).

Run:  blender -b --factory-startup --python-exit-code 1 -P Blender/town/guild.py [-- --no-preview]

Layout (Blender metres, Z up, characters face -Y; Unity sees (x, z, -y)):
  Walkable plaza x -21..21, y -24..14 (same bounds as before). Paved plaza with a sunrise medallion and a fountain.
  Back (south, -Y): the Dawn Guild HQ, 4 storeys, front face y=-17.5 facing the plaza, entrance steps, canopy,
  guild master at the door (Spot_elder) and the reception kiosk under the canopy (Spot_guild_clerk).
  West (-X): the clinic pavilion (Spot_innkeeper) and the lower-left corner gate pocket (Spot_gate).
  East (+X): the hunter market (Spot_shopkeeper) and the workshop garage (Spot_smith), both with colliders kept
  under 2.2 m so the follow camera (10, 14, 12 m from the party, i.e. toward +X +Y) is never pulled in by them.
  Roads with crosswalks and lane lines ring the plaza; two rows of KayKit City buildings (building_A..H, some
  stretched 1.5-2.5x into high-rises) ring the whole block so no bare ground shows from any camera. Only Col_ meshes collide, so visual-only trim never blocks the camera.
  Kit parts: KayKit City Builder Bits (kc, scale 4.6 = metres: a car is 0.94 units long), Furniture (kf),
  Restaurant (kr), Space Base (ks) (all 1 unit = 1 m, see Blender/environment/cc0_kit.py) and the dungeon barrier (kd).
"""
import json
import math
import os
import random
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.normpath(os.path.join(HERE, "..", "lib")))  # abyss_bpy, imported by _common
sys.path.insert(0, os.path.normpath(os.path.join(HERE, "..", "environment")))  # cc0_kit, cc0_preview

from _common import MB, T, RX, RZ, A, COLS, ANCHORS, SPOTS, anchor, col_box, empty, look_matrix, spot  # noqa: E402
from mathutils import Matrix, Vector  # noqa: E402
import bpy  # noqa: E402
import cc0_kit as K  # noqa: E402

PREVIEW_DIR = os.environ.get("GUILD_PREVIEW_DIR", "/mnt/project-files/art-upgrade/hunter_v2/hub")
KC = 4.6  # KayKit City Builder units -> metres (car 0.94 u = 4.3 m, bench 0.4 u = 1.84 m, road tile 2 u = 9.2 m)

# palette (sRGB hex; the Col attribute stores these)
IVORY, IVORY_D = "#f6ebd9", "#e6d3b2"
MINT_W, TEAL, TEAL_D = "#eef8f4", "#3fb8a6", "#22786e"
BLUE, BLUE_D, BLUE_L = "#2f6fc4", "#21467e", "#6aa8ea"
NAVY, ROOF = "#243a57", "#3b4a6b"
GOLD, GOLD_L = "#e9b651", "#ffe08a"
RED, CREAM, WHITE = "#e2535e", "#fbf6ea", "#ffffff"
YELLOW, AMBER = "#ffc857", "#ffb84d"
STEEL, STEEL_D, STEEL_B = "#7f8ca3", "#4a5467", "#5b6f93"
STONE, STONE_D = "#d8cfc0", "#9d9485"
GLASS, SKY = "#c4ecf7", "#9ed8f4"
WARM_WIN = "#ffd58a"
VIOLET, VIOLET_L, VIOLET_D = "#9b6bff", "#e3d2ff", "#3d2a6b"
GREEN_E, GREEN_D = "#7dffb0", "#2fd27a"
SUN = "#ffb84d"
GRASS = "#8fc46d"
ASPHALT, LANE, CROSS = "#5a6274", "#f4e3a1", "#f6f1e6"
PAVE_A, PAVE_B, PAVE_C, GROUT = "#f2e5cf", "#e4d0b0", "#dcc4a0", "#b9a58a"
WOOD, WOOD_D, WOOD_L = "#a86f47", "#6b4530", "#cf9a66"
SOIL, POT = "#6b4a34", "#c8795a"
LEAF, LEAF_L = "#5fae6a", "#8ad08a"
TREE_A, TREE_B, TREE_C, TREE_D = "#7fc27a", "#94d088", "#6fb36e", "#a6dd92"
BLACK, DARK = "#1d1d1d", "#2a2f3a"
PAVEMENT = "#7a7f8e"
PETALS = ("#f78fb3", "#ffd45c", "#ff6b6b", "#fbf6ea", "#b68cff")
WATER = "#8fdcff"
H_UNITS = dict(building_A=1.65, building_B=1.65, building_C=2.98, building_D=2.97, building_E=2.35,
               building_F=2.35, building_G=2.98, building_H=3.05)   # KayKit City heights in units (x KC)

# ---------------------------------------------------------------- layout constants
HQ_X0, HQ_X1, HQ_YF, HQ_YB, HQ_H = -13.5, 13.5, -17.5, -29.0, 15.4   # HQ footprint; front face faces +Y
FLOORS = ((4.8, 8.6), (8.6, 12.4), (12.4, 15.4))
WIN_X = (-10.5, -7.5, -4.5, -1.5, 1.5, 4.5, 7.5, 10.5)
GATE_X, GATE_Y = -16.5, -22.4
FOUNTAIN = (-3.6, 6.6)                                         # dungeon gate pocket (south-west corner)
BARRIER_Y = -16.2
CLINIC = (-20.8, -15.6, -3.6, 6.6, 6.8)                              # x0, x1, y0, y1, height (west, facing +X)
MARKET = (15.6, 20.8, -5.6, 2.6, 5.6)                                # east, facing -X
WORKSHOP = (15.6, 20.8, 7.2, 14.0, 6.0)                              # east north, facing -X
COUNTER_H = 1.2   # storefront / booth colliders: keep under the follow camera's ray (0.8 m + 1.2 m per m of run)
BOUND_H = 1.2     # plaza boundary walls


def bb(m, x0, y0, z0, x1, y1, z1, col, mat="M_Toon"):
    return m.bbox((x0, y0, z0), (x1, y1, z1), col, mat)


def frame(x, y, z, yaw):
    """Plane whose local +Z normal points where a character with this yaw faces (front = -Y)."""
    return T(x, y, z) @ RZ(yaw) @ RX(90)


def emblem(m, fr, R):
    """Dawn Guild crest: gold ring, blue disc, rising sun over a cream horizon, radial gold rays. Local XY."""
    with m.at(fr):
        m.torus(R * 0.96, R * 0.07, (0, 0, 0.012), GOLD, seg=40, minor=6)
        m.cyl(R * 0.9, 0.010, (0, 0, 0.008), BLUE, seg=40)
        pts = [(R * 0.52 * math.cos(math.pi * k / 12), R * 0.52 * math.sin(math.pi * k / 12)) for k in range(13)]
        m.prism(pts, 0.012, 0.026, AMBER)
        m.box((R * 1.12, R * 0.07, 0.02), (0, 0, 0.02), CREAM)
        for k in range(7):
            a = math.radians(22 + k * 23.3)
            m.box((R * 0.18, R * 0.07, 0.012), (R * 0.74 * math.cos(a), R * 0.74 * math.sin(a), 0.014), GOLD,
                  r=(0, 0, math.degrees(a)))


def colb(name, x0, y0, z0, x1, y1, z1, rz=0.0):
    """Invisible collider (Unity: MeshCollider on a stripped renderer) from min/max corners."""
    col_box(name, (x1 - x0, y1 - y0, z1 - z0), ((x0 + x1) / 2, (y0 + y1) / 2, (z0 + z1) / 2), rz)


def text_mesh(name, body, loc, size, col, yaw=0.0, mat="M_Toon"):
    """Latin sign text (Blender's built-in font has no Hangul) converted to a flat mesh whose front is yaw-facing."""
    bpy.ops.object.text_add(location=(0, 0, 0))
    t = bpy.context.object
    t.data.body = body
    t.data.size = size
    t.data.align_x = "CENTER"
    bpy.ops.object.convert(target="MESH")
    o = bpy.context.object
    o.name = name
    o.rotation_euler = (math.radians(90), 0, math.radians(yaw))
    o.location = loc
    bpy.ops.object.select_all(action="DESELECT")
    o.select_set(True)
    bpy.context.view_layer.objects.active = o
    bpy.ops.object.transform_apply(location=False, rotation=True, scale=False)
    A.paint(o, col, mat)
    return o


# ---------------------------------------------------------------- KayKit parts (kit objects are joined at the end)

KIT = []


def kit_m(pack, name, M, default=("keep", None, "M_Toon")):
    o = K.inst(pack, name, K.Palette(None, default), M=M, oname="%s_%s_%03d" % (pack, name, len(KIT)))
    KIT.append(o)
    return o


def kit(pack, name, x, y, z=0.0, yaw=0.0, s=1.0, default=("keep", None, "M_Toon")):
    return kit_m(pack, name, T(x, y, z) @ RZ(yaw) @ Matrix.Diagonal((s, s, s, 1.0)), default)


def bench(x, y, yaw, tag):
    kit("kc", "bench", x, y, 0.0, yaw, KC)
    col_box("Bench_" + tag, (0.4 * KC, 0.15 * KC, 0.6), (x, y, 0.3), yaw)


def street_lamp(x, y):
    kit("kc", "streetlight", x, y, 0.0, 0.0, KC)
    anchor((x, y, 4.1), "street")


def car(x, y, yaw, variant):
    kit("kc", variant, x, y, 0.0, yaw, KC)


# ---------------------------------------------------------------- nature

def tree(m, x, y, s=1.0, tag=""):
    m.cyl(0.13 * s, 2.0 * s, (x, y, 1.0 * s), WOOD_D, seg=8)
    for dx, dy, dz, r, c in ((0, 0, 2.7, 1.05, TREE_A), (0.6, 0.3, 2.3, 0.75, TREE_B),
                             (-0.55, -0.2, 2.35, 0.7, TREE_C), (0.1, -0.45, 3.2, 0.7, TREE_D)):
        m.ico(r * s, (x + dx * s, y + dy * s, dz * s), c, sub=2, jitter=0.10, seed=dx + dz)
    colb("Tree_%s_%d_%d" % (tag, round(x * 10), round(y * 10)), x - 0.2 * s, y - 0.2 * s, 0.0,
         x + 0.2 * s, y + 0.2 * s, 1.2 * s)


def planter(m, x, y, tag, s=1.0):
    h = 0.5 * s
    bb(m, x - 0.8 * s, y - 0.8 * s, 0.0, x + 0.8 * s, y + 0.8 * s, h, STONE)
    bb(m, x - 0.66 * s, y - 0.66 * s, h - 0.02, x + 0.66 * s, y + 0.66 * s, h + 0.08, SOIL)
    colb("Planter_%s" % tag, x - 0.8 * s, y - 0.8 * s, 0.0, x + 0.8 * s, y + 0.8 * s, 0.9 * s)
    kit("kc", "bush", x, y, h, 0.0, 1.1 * s)


# ---------------------------------------------------------------- ground, roads, plaza

ROADS = ((-30.2, -21.0, -40.1, 24.3), (21.0, 30.2, -40.1, 24.3), (-30.2, 30.2, 15.0, 24.3),
         (-30.2, 30.2, -40.1, -30.9))


def dashes_y(m, x, y0, y1, skip=None):
    y = y0
    while y < y1 - 0.5:
        ye = min(y + 3.0, y1)
        if not (skip and skip[0] < y + 1.5 < skip[1]):
            bb(m, x - 0.12, y, 0.0, x + 0.12, ye, 0.012, LANE)
        y += 6.0


def dashes_x(m, y, x0, x1):
    x = x0
    while x < x1 - 0.5:
        xe = min(x + 3.0, x1)
        bb(m, x, y - 0.12, 0.0, xe, y + 0.12, 0.012, LANE)
        x += 6.0


def zebra_on_ns_road(m, x0, x1, yc):
    """Crossing over a north-south road: bars run along the traffic (Y), spaced across the road (X)."""
    for k in range(8):
        xc = x0 + 0.7 + k * 1.1
        bb(m, xc - 0.28, yc - 1.5, 0.0, xc + 0.28, yc + 1.5, 0.014, CROSS)


def zebra_on_ew_road(m, y0, y1, xc):
    for k in range(8):
        yc = y0 + 0.7 + k * 1.1
        bb(m, xc - 1.5, yc - 0.28, 0.0, xc + 1.5, yc + 0.28, 0.014, CROSS)


def pave_rect(m, x0, x1, y0, y1, s=3.0):
    nx = int(math.ceil((x1 - x0) / s - 1e-6))
    ny = int(math.ceil((y1 - y0) / s - 1e-6))
    for i in range(nx):
        for j in range(ny):
            ax, ay = x0 + i * s, y0 + j * s
            bx, by = min(ax + s, x1), min(ay + s, y1)
            tone = PAVE_A if (i + j) % 2 == 0 else PAVE_B
            if (i * 7 + j * 3) % 11 == 0:
                tone = PAVE_C
            bb(m, ax + 0.05, ay + 0.05, 0.0, bx - 0.05, by - 0.05, 0.03, tone)
    bb(m, x0, y0, -0.012, x1, y1, 0.0, GROUT)


def build_ground(m):
    bb(m, -120.0, -120.0, -0.12, 120.0, 120.0, -0.04, PAVEMENT)   # city pavement base (collider top -0.03)
    for x0, x1, y0, y1 in ROADS:
        bb(m, x0, y0, -0.02, x1, y1, 0.0, ASPHALT)
    dashes_y(m, -25.6, -40.1, 24.3, skip=(-4.0, 1.0))
    dashes_y(m, 25.6, -40.1, 24.3, skip=(-4.0, 1.0))
    dashes_x(m, 19.65, -30.2, 30.2)
    dashes_x(m, -35.5, -30.2, 30.2)
    zebra_on_ns_road(m, -30.2, -21.0, -2.0)
    zebra_on_ns_road(m, 21.0, 30.2, -2.0)
    zebra_on_ew_road(m, 15.0, 24.3, -3.5)
    # kerbs on the road edges that face the blocks (light stone)
    for x0, x1, y0, y1 in ((-30.5, -30.2, -40.1, 24.3), (30.2, 30.5, -40.1, 24.3)):
        bb(m, x0, y0, 0.0, x1, y1, 0.14, STONE)
    bb(m, -30.2, 24.3, 0.0, 30.2, 24.6, 0.14, STONE)
    # street trees on the north sidewalk, between the north road and the skyline
    for x in (-26.0, -12.0, 2.0, 16.0, 30.0):
        tree(m, x, 28.5, 1.0, tag="north")


def build_plaza(m):
    # paved plaza (x -21..21, y -17.5..14) and the two south side strips beside the HQ (y -24.5..-17.5)
    pave_rect(m, -21.0, 21.0, -17.5, 14.0)
    pave_rect(m, -21.0, -13.5, -24.5, -17.5)
    pave_rect(m, 13.5, 21.0, -24.5, -17.5)
    # kerbs along the plaza edge (inside the walkable area; the boundary walls sit just outside)
    bb(m, -20.8, -17.5, 0.0, -20.3, 14.0, 0.14, STONE)
    bb(m, 20.3, -17.5, 0.0, 20.8, 14.0, 0.14, STONE)
    bb(m, -20.8, 13.5, 0.0, 20.8, 14.0, 0.14, STONE)
    # sunrise medallion on the walkway
    emblem(m, T(0.0, -5.5, 0.03), 2.2)
    m.torus(2.55, 0.06, (0.0, -5.5, 0.04), GOLD, seg=48, minor=6)
    build_fountain(m)
    # trees and planters
    for i, (x, y) in enumerate(((-9.5, -12.5), (19.8, -15.6), (9.5, 4.0), (-9.0, 13.0), (-14.0, 1.0))):
        tree(m, x, y, 1.0 + 0.1 * (i % 3), tag="plaza")
    for x, y in ((-6.5, -7.5), (6.5, -7.5), (6.8, 12.4), (-13.0, 12.6)):
        planter(m, x, y, "%d_%d" % (round(x), round(y)))


def build_props_plaza():
    bench(FOUNTAIN[0], FOUNTAIN[1] - 3.9, 0.0, "fountain_s")
    bench(FOUNTAIN[0] + 3.9, FOUNTAIN[1], 90.0, "fountain_e")
    bench(-11.0, 11.6, 0.0, "north_w")
    bench(7.5, 11.6, 0.0, "north_e")
    for x, y in ((-11.0, 8.6), (10.5, 8.6), (-18.0, -9.5)):
        street_lamp(x, y)
    kit("kc", "trafficlight_B", -19.4, 12.6, 0.0, 0.0, KC)
    kit("kc", "trash_A", -12.2, -4.8, 0.0, 30.0, KC)
    kit("kc", "trash_B", 17.8, -6.9, 0.0, 0.0, KC)
    # parked cars on the flanking roads (visual only, outside the walkable bounds)
    car(-27.6, -4.0, 0.0, "car_sedan")
    car(-27.6, 6.5, 180.0, "car_taxi")
    car(27.6, -9.0, 180.0, "car_police")
    car(27.6, 3.0, 0.0, "car_hatchback")


# ---------------------------------------------------------------- fountain, street life, skyline (pass 2)

def build_fountain(m):
    """Three-tier stone fountain, about 4.7 m across. Recessed basins hold clear light-blue water."""
    fx, fy = FOUNTAIN
    # tier 1: wide basin, stone rim, water 0.06 m above its floor
    m.lathe([(0.0, 0.0), (2.35, 0.0), (2.35, 0.42), (2.12, 0.42), (2.12, 0.30), (0.0, 0.30)],
            (fx, fy, 0.0), STONE, seg=40)
    m.cyl(2.10, 0.02, (fx, fy, 0.34), WATER, mat="M_Clear", seg=40)
    # tier 2: smaller bowl standing in the basin
    m.lathe([(0.0, 0.0), (1.42, 0.0), (1.42, 0.42), (1.22, 0.42), (1.22, 0.32), (0.0, 0.32)],
            (fx, fy, 0.30), STONE_D, seg=36)
    m.cyl(1.22, 0.02, (fx, fy, 0.66), WATER, mat="M_Clear", seg=36)
    # tier 3: top cup with a spout column and a gold finial
    m.lathe([(0.0, 0.0), (0.60, 0.0), (0.60, 0.30), (0.50, 0.30), (0.50, 0.22), (0.0, 0.22)],
            (fx, fy, 0.72), STONE, seg=24)
    m.cyl(0.50, 0.02, (fx, fy, 0.94), WATER, mat="M_Clear", seg=24)
    m.cyl(0.09, 0.70, (fx, fy, 1.37), STONE_D, seg=10)
    m.cyl(0.05, 0.62, (fx, fy, 1.55), WATER, mat="M_Clear", seg=8)     # falling water
    m.ico(0.17, (fx, fy, 1.78), GOLD, sub=1)
    colb("Fountain", fx - 2.35, fy - 2.35, 0.0, fx + 2.35, fy + 2.35, 0.42)


def food_cart(m, x, y, awn_a, awn_b, body, tag):
    """Street food stall, 2.2 m wide, serving side toward -Y, striped awning on four posts."""
    with m.at(T(x, y, 0.0)):
        m.box((2.2, 1.1, 1.0), (0, 0, 0.5), body)
        m.box((2.36, 0.56, 0.08), (0, -0.78, 1.04), CREAM)
        m.box((1.9, 0.03, 0.5), (0, -0.56, 1.30), "#fff1c2", "M_Emit")    # lit menu panel
        for sx in (-1.0, 1.0):
            for sy in (-0.45, 0.45):
                m.cyl(0.04, 2.45, (sx, sy, 1.22), STEEL_D, seg=6)
        for k in range(6):
            m.box((0.44, 1.9, 0.06), (-1.1 + 0.44 * k + 0.22, -0.25, 2.55), awn_a if k % 2 == 0 else awn_b)
        m.box((1.6, 0.06, 0.34), (0, -1.0, 2.9), GOLD)                   # sign board
    colb("FoodCart_%s" % tag, x - 1.1, y - 0.55, 0.0, x + 1.1, y + 0.55, 1.1)


def vending(m, x, y, yaw, body, tag):
    """Drinks vending machine, 0.9 m wide, 1.9 m tall, glowing front panel."""
    with m.at(T(x, y, 0.0) @ RZ(yaw)):
        m.box((0.9, 0.8, 1.9), (0, 0, 0.95), body)
        m.box((0.66, 0.02, 1.05), (0, -0.41, 1.25), "#ffe9b0", "M_Emit")
        for i in range(3):
            for j in range(2):
                m.box((0.14, 0.03, 0.14), (-0.22 + 0.22 * i, -0.43, 1.02 + 0.22 * j), PETALS[(i + 2 * j) % len(PETALS)])
        m.box((0.7, 0.03, 0.1), (0, -0.43, 0.35), DARK)
    colb("Vending_%s" % tag, x - 0.45, y - 0.4, 0.0, x + 0.45, y + 0.4, COUNTER_H)   # low collider: keeps the follow camera clear


def cafe_set(m, x, y, canopy, tag):
    """Outdoor café table with two chairs and a parasol (canopy colour given)."""
    with m.at(T(x, y, 0.0)):
        m.cyl(0.035, 2.0, (0, 0, 1.0), STEEL_D, seg=6)
        m.cyl(1.25, 0.24, (0, 0, 2.18), canopy, seg=16, r2=0.15)
    kit_m("kr", "table_round_A_small", T(x, y, 0.0) @ Matrix.Diagonal((0.55, 0.55, 0.75, 1.0)))
    kit_m("kr", "chair_A", T(x - 0.85, y, 0.0) @ RZ(90.0) @ Matrix.Diagonal((0.6, 0.6, 0.6, 1.0)))
    kit_m("kr", "chair_A", T(x + 0.85, y, 0.0) @ RZ(-90.0) @ Matrix.Diagonal((0.6, 0.6, 0.6, 1.0)))
    colb("Cafe_Table_%s" % tag, x - 0.42, y - 0.42, 0.0, x + 0.42, y + 0.42, 0.75)


def flower_bed(m, x, y, tag):
    """Long stone planter (2.4 m) with a row of blossoms."""
    bb(m, x - 1.2, y - 0.45, 0.0, x + 1.2, y + 0.45, 0.42, STONE)
    bb(m, x - 1.1, y - 0.36, 0.40, x + 1.1, y + 0.36, 0.48, SOIL)
    for k in range(12):
        px = x - 0.95 + (k % 6) * 0.38
        py = y - 0.2 + (k // 6) * 0.4
        m.ico(0.13, (px, py, 0.62 + 0.05 * ((k * 7) % 3)), PETALS[k % len(PETALS)], sub=1)
        m.ico(0.09, (px + 0.12, py - 0.05, 0.56), LEAF, sub=1)
    colb("FlowerBed_%s" % tag, x - 1.2, y - 0.45, 0.0, x + 1.2, y + 0.45, 0.6)


def notice_board(m, x, y, tag):
    """Cork notice board on two posts, front facing -Y (the spawn side)."""
    with m.at(T(x, y, 0.0)):
        m.cyl(0.04, 1.3, (-0.85, 0, 0.65), WOOD_D, seg=6)
        m.cyl(0.04, 1.3, (0.85, 0, 0.65), WOOD_D, seg=6)
        m.box((1.9, 0.07, 1.05), (0, 0, 1.55), "#b98a5a")
        m.box((1.98, 0.05, 0.12), (0, 0, 2.12), WOOD)
        for k, c in enumerate((WHITE, "#ffe58a", "#ffb3c7", WHITE, "#bfe9ff", "#ffe58a")):
            m.box((0.36, 0.02, 0.28), (-0.66 + 0.33 * (k % 4), -0.06, 1.22 + 0.36 * (k // 4)), c)
    colb("Notice_%s_L" % tag, x - 0.9, y - 0.06, 0.0, x - 0.8, y + 0.06, 1.2)
    colb("Notice_%s_R" % tag, x + 0.8, y - 0.06, 0.0, x + 0.9, y + 0.06, 1.2)


def banner(m, x, y, col, tag):
    """Guild pennant on a steel pole, crest facing -Y."""
    m.cyl(0.05, 4.8, (x, y, 2.4), STEEL, seg=6)
    m.box((0.9, 0.05, 2.2), (x, y - 0.04, 3.0), col)
    m.box((0.9, 0.06, 0.12), (x, y - 0.05, 1.95), GOLD)
    emblem(m, frame(x, y - 0.075, 3.0, yaw=0.0), 0.32)


def scooter(m, x, y, yaw, col):
    """Parked scooter: two wheels, deck, seat and steering column (long axis along Y)."""
    with m.at(T(x, y, 0.0) @ RZ(yaw)):
        for yy in (-0.5, 0.5):
            m.torus(0.2, 0.05, (0, yy, 0.22), DARK, seg=16, minor=6, m=RX(90))
        m.box((0.22, 1.0, 0.1), (0, 0, 0.4), col)
        m.box((0.26, 0.36, 0.1), (0, -0.1, 0.7), DARK)
        m.cyl(0.03, 0.7, (0, 0.5, 0.75), STEEL_D, seg=6)
        m.box((0.56, 0.05, 0.05), (0, 0.5, 1.1), DARK)


def string_lights(m, x0, x1, y, z_end, sag, n, tag):
    """Festoon string between two poles at constant y: a chain of thin boxes with warm bulbs every second joint."""
    xs = [x0 + (x1 - x0) * i / n for i in range(n + 1)]
    zs = [z_end - sag * 4.0 * (i / n) * (1.0 - i / n) for i in range(n + 1)]
    for i in range(n):
        bb(m, xs[i], y - 0.012, min(zs[i], zs[i + 1]) - 0.012, xs[i + 1], y + 0.012, max(zs[i], zs[i + 1]) + 0.012, "#4a4f5c")
    for i in range(0, n + 1, 2):
        m.ico(0.09, (xs[i], y, zs[i] - 0.12), WARM_WIN, mat="M_Emit", sub=1)


def build_street_life(m):
    food_cart(m, -16.6, -6.6, RED, CREAM, WOOD, "west")
    food_cart(m, 10.6, -11.4, TEAL, CREAM, YELLOW, "east")
    # café tables with parasols beside the market front, south of the shop
    cafe_set(m, 16.8, -8.6, RED, "a")
    cafe_set(m, 16.8, -12.8, TEAL, "b")
    # vending machines: one in the south-east strip (facing the plaza), one beside the clinic (facing east)
    vending(m, 19.5, -20.2, 180.0, BLUE, "south_east")
    vending(m, -19.4, 9.0, 90.0, RED, "clinic")
    # flower beds and a notice board
    flower_bed(m, 8.0, 4.6, "east")
    flower_bed(m, -6.2, 12.2, "north")
    notice_board(m, -9.6, -1.5, "plaza")
    # guild pennants on poles
    banner(m, -2.6, 13.1, BLUE, "north_a")
    banner(m, -17.0, 13.2, RED, "north_b")
    banner(m, -20.0, -19.8, TEAL, "south_west")
    # parked scooters on the north road (visual only, outside the walkable area)
    scooter(m, -24.6, 21.6, 0.0, RED)
    scooter(m, -22.9, 21.6, 0.0, BLUE)
    # festoon strings across the plaza, hung from the lamp posts (poles at the ends)
    m.cyl(0.05, 4.1, (19.6, -9.5, 2.05), STEEL, seg=6)
    string_lights(m, -11.0, 10.5, 8.6, 4.0, 0.9, 16, "north")
    string_lights(m, -18.0, 19.6, -9.5, 4.0, 0.9, 24, "south")


# skyline: two rows of KayKit City buildings around the block (9.2 m footprints, 10 m pitch)
SKY_NAMES = ("building_A", "building_B", "building_C", "building_D", "building_E", "building_F", "building_G", "building_H")
SKY_LOW = ("building_A", "building_B", "building_E", "building_F")
SKY_INNER = (1.0, 1.0, 1.25, 1.6, 2.1)      # first row: mostly mid-rise, a few tall
SKY_OUTER = (1.0, 1.5, 1.9, 2.3, 2.5)       # second row: more high-rises


def skyline_building(name, x, y, zs):
    kit_m("kc", name, T(x, y, 0.0) @ Matrix.Diagonal((KC, KC, KC * zs, 1.0)))
    colb("Building_%d_%d" % (round(x), round(y)), x - KC, y - KC, 0.0, x + KC, y + KC, H_UNITS[name] * KC * zs)


def build_skyline():
    rng = random.Random(20260)
    slots = []
    for y in range(-56, 30, 10):
        slots.append((-37.0, y, SKY_INNER))
        slots.append((-48.0, y, SKY_OUTER))
        slots.append((37.0, y, SKY_INNER))
        slots.append((48.0, y, SKY_OUTER))
    for x in range(-26, 31, 10):
        slots.append((x, -46.0, SKY_INNER))
        slots.append((x, -56.0, SKY_OUTER))
    for x in range(-50, 51, 10):
        if abs(x + 4.0) <= 14.0:                      # north row directly ahead of the title camera: keep it low
            slots.append((x, 37.0, (1.0,)))
        else:
            slots.append((x, 37.0, SKY_INNER))
        slots.append((x, 49.0, SKY_OUTER))
    for x, y, pool in slots:
        names = SKY_LOW if pool == (1.0,) else SKY_NAMES
        skyline_building(rng.choice(names), x, y, rng.choice(pool))


# ---------------------------------------------------------------- Dawn Guild HQ (back of the plaza)

def build_hq(m):
    X0, X1, YF, YB, H = HQ_X0, HQ_X1, HQ_YF, HQ_YB, HQ_H
    bb(m, X0, YB, 0.0, X1, YF, H, IVORY)
    # roof: dark deck inside a blue parapet, a couple of plant boxes and the guild beacon
    bb(m, X0 + 0.5, YB + 0.5, H, X1 - 0.5, YF - 0.5, H + 0.06, ROOF)
    for box in ((X0, YB, X1, YB + 0.5), (X0, YF - 0.5, X1, YF), (X0, YB, X0 + 0.5, YF), (X1 - 0.5, YB, X1, YF)):
        bb(m, box[0], box[1], H, box[2], box[3], H + 0.7, BLUE)
    bb(m, -8.0, -24.0, H + 0.06, -5.2, -22.0, H + 1.3, "#c9d2dc")
    bb(m, 4.5, -27.0, H + 0.06, 7.4, -25.0, H + 1.1, "#c9d2dc")
    m.cyl(0.22, 2.4, (0.0, -25.0, H + 1.26), STEEL_D, seg=10)
    m.ico(0.36, (0.0, -25.0, H + 2.7), GOLD_L, sub=1, mat="M_Emit")
    # front facade: pilasters, floor bands, windows (lit for a third), the crest and the lit sign board
    for xc in (-13.0, -6.0, 6.0, 13.0):
        bb(m, xc - 0.4, YF, 0.9, xc + 0.4, YF + 0.35, H, BLUE)
    for z0, z1 in FLOORS:
        bb(m, X0, YF, z0, X1, YF + 0.2, z0 + 0.25, GOLD)
    for fi, (z0, z1) in enumerate(FLOORS):
        wz0, wz1 = (z0 + 0.8, z1 - 0.55) if fi < 2 else (z0 + 0.6, z1 - 0.5)
        for i, xc in enumerate(WIN_X):
            if fi == 1 and abs(xc) < 2.8:
                continue
            if fi == 2 and abs(xc) < 6.5:
                continue
            lit = (i + 2 * fi) % 3 == 0
            bb(m, xc - 1.05, YF, wz0 - 0.12, xc + 1.05, YF + 0.12, wz1 + 0.12, NAVY)
            bb(m, xc - 0.9, YF + 0.12, wz0, xc + 0.9, YF + 0.16, wz1, WARM_WIN if lit else SKY,
               "M_Emit" if lit else "M_Clear")
    # lobby: warm backdrop behind the glass, glass front, mullions, door centre post
    bb(m, X0 + 0.5, YF, 0.9, X1 - 0.5, YF + 0.03, 4.6, WARM_WIN, "M_Emit")
    bb(m, X0 + 0.5, YF + 0.06, 0.9, X1 - 0.5, YF + 0.10, 4.6, GLASS, "M_Clear")
    for xc in (-10.4, -7.8, -5.2, -2.6, 0.0, 2.6, 5.2, 7.8, 10.4):
        bb(m, xc - 0.07, YF, 0.9, xc + 0.07, YF + 0.16, 4.6, STEEL_D)
    # side walls: three windows per floor on the flanks
    for xs, wsign in ((X1, 1), (X0, -1)):
        for fi, (z0, z1) in enumerate(FLOORS):
            wz0, wz1 = (z0 + 0.8, z1 - 0.55) if fi < 2 else (z0 + 0.6, z1 - 0.5)
            for i, yc in enumerate((-20.0, -23.0, -26.0)):
                lit = (i + fi) % 3 == 1
                x0 = xs if wsign > 0 else xs - 0.12
                bb(m, x0, yc - 0.9, wz0, x0 + 0.12, yc + 0.9, wz1, WARM_WIN if lit else SKY,
                   "M_Emit" if lit else "M_Clear")
    # crest and lit "DAWN GUILD" board above the windows
    emblem(m, frame(0.0, YF, 10.45, 180.0), 2.2)
    bb(m, -6.6, YF, 12.9, 6.6, YF + 0.3, 14.9, BLUE)
    text_mesh("Sign_DawnGuild", "DAWN GUILD", (0.0, YF + 0.34, 13.25), 0.95, GOLD_L, yaw=180.0, mat="M_Emit")
    # canopy over the entrance and the kiosk, striped blue and cream, on two posts
    for k in range(8):
        x0 = -9.8 + k * 2.45
        bb(m, x0, YF, 4.6, x0 + 2.45, YF + 4.0, 4.85, BLUE if k % 2 == 0 else CREAM)
    for xc in (-9.5, 9.5):
        m.cyl(0.14, 3.7, (xc, -13.9, 2.75), STEEL_D, seg=8)
    # front plinth (walkable top at 0.9 m), the steps in the middle (0.225 m rises stay within stepOffset)
    bb(m, -9.5, YF, 0.0, 9.5, -14.4, 0.9, STONE)
    bb(m, -9.5, -14.4, 0.84, 9.5, -14.3, 0.9, GOLD)
    for y0, y1, top in ((-14.4, -14.05, 0.675), (-14.05, -13.7, 0.45), (-13.7, -13.35, 0.225)):
        bb(m, -3.0, y0, 0.0, 3.0, y1, top, STONE)
    colb("HQ_Body", X0, YB, 0.0, X1, YF, H)
    colb("HQ_Plinth_W", -9.5, YF, 0.0, -3.0, -14.4, 0.9)
    colb("HQ_Plinth_E", 3.0, YF, 0.0, 9.5, -14.4, 0.9)
    # reception kiosk under the canopy (east of the door)
    bb(m, 4.0, -15.9, 0.9, 8.4, -14.6, 1.9, NAVY)
    bb(m, 3.9, -16.0, 1.9, 8.5, -14.5, 2.0, CREAM)
    bb(m, 5.0, -14.6, 1.2, 7.4, -14.57, 1.7, SKY, "M_Emit")
    colb("Reception_Kiosk", 4.0, -15.9, 0.9, 8.4, -14.6, 2.0)
    # quest board on posts, posters on the plaza side, lit header
    for xc in (9.1, 11.6):
        m.cyl(0.07, 3.2, (xc, -15.75, 1.6), WOOD_D, seg=8)
    bb(m, 8.8, -15.9, 1.4, 11.9, -15.6, 3.2, WOOD)
    for i in range(3):
        for j in range(2):
            x0 = 8.95 + i * 1.0
            z0 = 1.5 + j * 0.85
            bb(m, x0, -15.62, z0, x0 + 0.75, -15.6, z0 + 0.7, (CREAM, "#ffd6e0", "#d6f0ff", "#d9f7d9", "#fff4c2", "#ffd6e0")[i * 2 + j])
    bb(m, 8.8, -15.9, 3.2, 11.9, -15.6, 3.45, BLUE)


def build_clinic(m):
    X0, X1, Y0, Y1, H = CLINIC
    bb(m, X0, Y0, 0.0, X1, Y1, H, MINT_W)
    bb(m, X0 - 0.15, Y0 - 0.15, H, X1 + 0.15, Y1 + 0.15, H + 0.3, TEAL_D)
    bb(m, X0, Y0, 3.3, X1 + 0.15, Y1, 3.5, TEAL)
    # facade on +X (plaza side): door, ground and upper windows, sign board with a green cross
    bb(m, X1, 0.5, 0.0, X1 + 0.12, 2.5, 2.9, GLASS, "M_Clear")
    bb(m, X1, -3.0, 0.7, X1 + 0.12, -0.6, 2.9, GLASS, "M_Clear")
    bb(m, X1, 3.4, 0.7, X1 + 0.12, 6.0, 2.9, GLASS, "M_Clear")
    bb(m, X1, -3.0, 3.9, X1 + 0.12, -0.6, 5.9, WARM_WIN, "M_Emit")
    bb(m, X1, 3.4, 3.9, X1 + 0.12, 6.0, 5.9, GLASS, "M_Clear")
    for k in range(10):
        y0 = Y0 + k * 1.02
        bb(m, X1, y0, 3.0, X1 + 1.8, y0 + 1.02, 3.2, TEAL if k % 2 == 0 else WHITE)
    bb(m, X1 + 0.02, -2.8, 6.05, X1 + 0.14, 5.2, 6.65, TEAL_D)
    bb(m, X1 + 0.14, 1.3, 6.15, X1 + 0.2, 1.7, 6.55, GREEN_E, "M_Emit")
    bb(m, X1 + 0.14, 0.9, 6.25, X1 + 0.2, 2.1, 6.45, GREEN_E, "M_Emit")
    colb("Clinic", X0, Y0, 0.0, X1, Y1, COUNTER_H)


def build_market(m):
    X0, X1, Y0, Y1, H = MARKET
    bb(m, X0, Y0, 0.0, X1, Y1, H, YELLOW)
    bb(m, X0 - 0.14, Y0 + 0.2, 4.2, X0, Y1 - 0.2, 5.1, "#fff1c2", "M_Emit")   # lit sign band
    bb(m, X0 - 0.2, Y0, 5.1, X0, Y1, 5.6, RED)
    text_mesh("Sign_Market", "MARKET", (X0 - 0.16, -1.5, 4.35), 0.6, RED, yaw=-90.0)
    bb(m, X0 - 0.12, Y0 + 0.3, 0.8, X0, Y1 - 0.3, 3.1, GLASS, "M_Clear")
    for yy in (-3.6, -1.0, 1.4):
        bb(m, X0 - 0.14, yy - 0.06, 0.8, X0, yy + 0.06, 3.1, RED)
    for k in range(9):
        y0 = Y0 + k * 0.91
        bb(m, X0 - 1.8, y0, 3.2, X0, y0 + 0.91, 3.45, RED if k % 2 == 0 else CREAM)
    colb("Market", X0, Y0, 0.0, X1, Y1, COUNTER_H)


def build_workshop(m):
    X0, X1, Y0, Y1, H = WORKSHOP
    bb(m, X0, Y0, 0.0, X1, Y1, H, STEEL_B)
    bb(m, X0 - 0.2, Y0 - 0.2, H, X1 + 0.2, Y1 + 0.2, H + 0.3, ROOF)
    # open garage bay on the plaza side: dark interior with a furnace glow
    bb(m, X0 - 0.12, 8.0, 0.0, X0, 12.6, 3.6, DARK)
    bb(m, X0 - 0.14, 8.4, 0.3, X0 - 0.12, 12.2, 2.9, AMBER, "M_Emit")
    bb(m, X0 - 0.14, 7.8, 0.0, X0 - 0.1, 7.95, 3.8, STEEL_D)
    bb(m, X0 - 0.14, 12.65, 0.0, X0 - 0.1, 12.8, 3.8, STEEL_D)
    bb(m, X0 - 0.14, 7.8, 3.8, X0 - 0.1, 12.8, 3.95, STEEL_D)
    bb(m, X0 - 0.14, Y0 + 0.2, 4.2, X0, Y1 - 0.2, 5.2, AMBER, "M_Emit")
    text_mesh("Sign_Workshop", "WORKSHOP", (X0 - 0.16, 10.6, 4.4), 0.55, "#3a2a14", yaw=-90.0)
    colb("Workshop", X0, Y0, 0.0, X1, Y1, COUNTER_H)


def build_plaza_props(m):
    # anvil and a barrel in front of the workshop
    bb(m, 13.4, 11.7, 0.0, 14.4, 12.5, 0.6, STEEL_D)
    bb(m, 13.2, 11.6, 0.6, 14.6, 12.6, 0.85, STEEL)
    m.cyl(0.38, 0.9, (14.1, 7.6, 0.45), WOOD_D, seg=12)
    # the clinic's green flag pole and the benches' stone planters are on the plaza side of the clinic
    m.cyl(0.05, 3.6, (-13.0, 5.2, 1.8), STEEL, seg=6)
    bb(m, -13.0, 5.18, 2.9, -12.4, 5.22, 3.5, GREEN_D)
    bb(m, -13.0, 0.4, 0.0, -12.6, 0.6, 0.6, WOOD)  # small sandwich board
    for x, y in ((-14.6, -2.6), (-14.6, 6.0)):
        planter(m, x, y, "clinic_%d" % round(y))


def build_gate(m):
    GX, GY = GATE_X, GATE_Y
    # stone pillars with gold caps and an arch
    for dx in (-2.15, 2.15):
        bb(m, GX + dx - 0.4, GY - 0.4, 0.0, GX + dx + 0.4, GY + 0.4, 3.4, STONE_D)
        bb(m, GX + dx - 0.5, GY - 0.5, 3.4, GX + dx + 0.5, GY + 0.5, 3.62, GOLD)
        bb(m, GX + dx - 0.5, GY - 0.5, 0.0, GX + dx + 0.5, GY + 0.5, 0.25, STONE)
        bb(m, GX + dx - 0.3, GY + 0.4, 1.7, GX + dx + 0.3, GY + 0.46, 2.4, YELLOW)
        bb(m, GX + dx - 0.3, GY + 0.46, 2.0, GX + dx + 0.3, GY + 0.5, 2.1, BLACK)
    m.torus(2.15, 0.18, (GX, GY, 3.4), GOLD, seg=40, minor=8, m=RX(90), arc=0.5)
    # the portal: a violet emissive ring and a glowing disc (the gate's visual hero)
    m.torus(1.5, 0.13, (GX, GY, 1.63), VIOLET_L, mat="M_Emit", seg=48, minor=8, m=RX(90))
    m.cyl(1.38, 0.06, (GX, GY + 0.02, 1.63), VIOLET, mat="M_Emit", seg=40, rr=(90, 0, 0))
    m.cyl(0.62, 0.07, (GX, GY + 0.03, 1.63), VIOLET_L, mat="M_Emit", seg=32, rr=(90, 0, 0))
    # violet rune circle on the pocket floor
    m.cyl(2.6, 0.01, (GX, GY, 0.04), VIOLET_D, seg=48)
    m.torus(2.25, 0.05, (GX, GY, 0.05), VIOLET_L, mat="M_Emit", seg=48, minor=6)
    # warning tape along the top of the barricades
    x = -20.9
    k = 0
    while x < -13.6:
        bb(m, x, BARRIER_Y - 0.36, 0.92, x + 0.42, BARRIER_Y - 0.28, 1.04, YELLOW if k % 2 == 0 else BLACK)
        x += 0.5
        k += 1
    # guard booths: left (west) and right (east) of the gate, windows facing the barricade
    for x0, x1, tag in ((-20.7, -18.9, "W"), (-14.6, -13.0, "E")):
        y0, y1, h = -15.1, -13.5, 2.0
        bb(m, x0, y0, 0.0, x1, y1, h, NAVY)
        bb(m, x0 - 0.15, y0 - 0.15, h, x1 + 0.15, y1 + 0.15, h + 0.2, BLUE)
        bb(m, x0 + 0.2, y0 - 0.02, 1.0, x1 - 0.2, y0, 1.7, SKY, "M_Emit")
        bb(m, x0 + 0.85, y0 - 0.02, 0.1, x0 + 0.95, y0, 0.9, DARK)
        colb("Booth_" + tag, x0, y0, 0.0, x1, y1, COUNTER_H)
    colb("Barricade_Corner", -13.85, -17.5, 0.0, -13.35, -16.2, 1.1)


def build_kit_gate():
    for x in (-19.75, -17.25, -14.75):
        kit_m("kd", "barrier", T(x, BARRIER_Y, 0.0) @ Matrix.Diagonal((0.625, 1.0, 1.0, 1.0)))
        colb("Barricade_%d" % round(x * 10), x - 1.25, BARRIER_Y - 0.25, 0.0, x + 1.25, BARRIER_Y + 0.25, 1.1)
    kit_m("kd", "barrier", T(-13.6, -16.85, 0.0) @ RZ(90.0) @ Matrix.Diagonal((0.325, 1.0, 1.0, 1.0)))


def build_storefront_kits():
    # clinic front
    kit("kr", "menu", -13.3, -0.8, 0.0, 90.0, 1.5)
    # market front: crates, a drinks fridge and an A-board
    kit("kr", "crate_tomatoes", 13.2, -3.6, 0.0, 0.0, 0.5)
    kit("kr", "crate_potatoes", 13.2, -2.4, 0.0, 0.0, 0.5)
    kit("kr", "crate_carrots", 13.7, -3.0, 0.5, 0.0, 0.5)
    kit_m("kr", "fridge_A", T(14.5, -6.6, 0.0) @ Matrix.Diagonal((0.45, 0.4, 0.7, 1.0)))
    kit("kr", "menu", 12.9, 0.9, 0.0, 0.0, 1.5)
    # workshop: stacked cargo, a steel bench
    kit("ks", "cargo_A", 14.6, 6.0, 0.0, 0.0, 2.0)
    kit("ks", "cargo_A", 14.6, 6.0, 1.0, 0.0, 2.0)
    kit("ks", "cargo_B", 13.5, 5.4, 0.0, 0.0, 2.0)
    kit("kf", "table_low", 13.6, 4.5, 0.0, 90.0, 0.8)


def build_lights():
    anchor((-16.5, -21.2, 3.0), "gate")
    anchor((0.0, -15.0, 3.6), "hq")
    anchor((-14.6, 1.5, 5.6), "clinic")
    anchor((14.6, -1.6, 4.0), "market")
    anchor((14.8, 10.0, 3.0), "workshop")


def build_boundaries():
    # invisible walls 1.2 m high: the character cannot step over them (stepOffset 0.24) and the follow camera's
    # ray passes above them, so it is not pulled in when the party walks along the edges
    col_box("BoundaryWest", (1.0, 38.0, BOUND_H), (-21.5, -5.0, BOUND_H / 2))
    col_box("BoundaryEast", (1.0, 38.0, BOUND_H), (21.5, -5.0, BOUND_H / 2))
    col_box("BoundarySouth", (44.0, 1.0, BOUND_H), (0.0, -24.5, BOUND_H / 2))
    col_box("BoundaryNorth", (44.0, 1.0, BOUND_H), (0.0, 14.5, BOUND_H / 2))


def build_scene():
    g = MB()
    build_ground(g)
    g.build("City_Ground")
    plaza = MB()
    build_plaza(plaza)
    plaza.build("Plaza")
    hq = MB()
    build_hq(hq)
    hq.build("Guild_HQ")
    shops = MB()
    build_clinic(shops)
    build_market(shops)
    build_workshop(shops)
    shops.build("Storefronts")
    gate = MB()
    build_gate(gate)
    gate.build("Dungeon_Gate")
    props = MB()
    build_plaza_props(props)
    props.build("Plaza_Props")
    build_skyline()
    street = MB()
    build_street_life(street)
    street.build("Street_Life")
    build_props_plaza()
    build_kit_gate()
    build_storefront_kits()
    K.finish("Kit_Props", KIT)
    col_box("Ground", (120.0, 120.0, 0.4), (0, 0, -0.23))
    build_boundaries()
    build_lights()


def markers():
    spots = [
        ("Spot_spawn", (0.0, -9.4, 0.0), 180.0),
        ("Spot_innkeeper", (-13.2, 1.8, 0.0), 90.0),
        ("Spot_shopkeeper", (13.4, -0.5, 0.0), -90.0),
        ("Spot_smith", (13.2, 9.8, 0.0), -90.0),
        ("Spot_guild_clerk", (6.2, -16.4, 0.9), 180.0),
        ("Spot_elder", (-3.6, -16.4, 0.9), 180.0),
        ("Spot_gate", (-16.5, -15.0, 0.0), 0.0),
        ("Spot_villager_1", (-8.5, 0.5, 0.0), 0.0),
        ("Spot_villager_2", (-4.2, -10.8, 0.0), 180.0),
        ("Spot_villager_3", (-10.8, -10.5, 0.0), 90.0),
    ]
    for name, loc, yaw in spots:
        spot(name, loc, yaw)
    staff = [Vector(SPOTS[n].location) for n in ("Spot_innkeeper", "Spot_smith", "Spot_elder")]
    target = sum(staff, Vector()) / 3 + Vector((0, 0, 1.5))
    cam_loc = Vector((-4.0, 42.0, 24.0))
    cam = empty("Spot_camera_title", tuple(cam_loc), kind="CUBE", size=1, matrix=look_matrix(cam_loc, target))
    SPOTS[cam.name] = cam
    return target


def write_manifest(target):
    manifest = {
        "asset": "Art/Town/town",
        "name": "새벽 길드 거리 (Dawn Guild street) hub",
        "units": "metres",
        "blender_axes": "Z-up; humanoid forward -Y",
        "unity_position_mapping": "(Blender x, Blender z, -Blender y)",
        "usage": "Use imported Spot_ transform positions for actors. Spot_gate is an interaction anchor, not an obstacle. "
                 "Title camera target = mean(innkeeper, smith, elder) + 1.5 m up, which TownWorld.cs computes itself.",
        "playable_bounds_blender": {"min": [-21.0, -24.0, 0.0], "max": [21.0, 14.0, 0.0]},
        "plaza_paving_blender": {"min": [-21.0, -24.5, 0.0], "max": [21.0, 14.0, 0.03]},
        "hq_footprint_blender": {"min": [HQ_X0, HQ_YB, 0.0], "max": [HQ_X1, HQ_YF, HQ_H]},
        "camera_title_target_blender": [round(v, 4) for v in target],
        "camera_title_target_unity": [round(target[0], 4), round(target[2], 4), round(-target[1], 4)],
        "camera_title_lens_mm": 30,
        "markers": {},
        "collision": "All Col_ meshes are hidden from Blender renders; Unity strips renderers and creates MeshColliders. "
                     "Col_Ground top=-0.03m. The HQ body and plinth, clinic, market, workshop and booths (1.2 m counters), the "
                     "kiosk, barricades, planters, benches, trunks and the fountain collide; the plaza boundary walls are 1.2 m "
                     "high. Roads, lamps, cars, bushes, signs and the skyline are visual only. Colliders north-east of the player "
                     "stay low so the follow camera (offset +10 x, +14 y, +12 z) is not pulled in.",
        "doors": "HQ entrance: plinth steps centre x -3..3 (rise 0.225 m each), walkable top 0.9 m. "
                 "Gate pocket: barricades at y -16.2 from x -21 to -13.5 close it; Spot_gate stands in front at y -15.",
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


# ---------------------------------------------------------------- previews (toon-ish Workbench + the dungeon post pass)

CITY_DUSK = dict(fog=(0.44, 0.42, 0.56), fog_range=(60, 190), bg=(0.46, 0.52, 0.78), sun=(1.0, 0.82, 0.62),
                 torch=(1.0, 0.72, 0.40), bloom=1.1, sat=1.18)
CITY_NIGHT = dict(fog=(0.17, 0.19, 0.36), fog_range=(50, 170), bg=(0.13, 0.16, 0.36), sun=(0.62, 0.70, 1.0),
                  torch=(1.0, 0.72, 0.42), bloom=1.45, sat=1.12, dim=0.9)


def shot(name, loc, target=None, lens=24.0, res=(1600, 900), at=CITY_DUSK, rot=None):
    import cc0_preview as CP  # noqa: E402  (environment/ is on sys.path)
    sc = bpy.context.scene
    cd = bpy.data.cameras.new("ShotCam")
    cd.sensor_fit = "VERTICAL"
    cd.sensor_height = 24.0
    cd.lens = lens
    cd.clip_start = 0.1
    cd.clip_end = 600
    cam = bpy.data.objects.new("ShotCam", cd)
    sc.collection.objects.link(cam)
    cam.matrix_world = look_matrix(Vector(loc), Vector(target)) if target is not None else rot
    sc.camera = cam
    os.makedirs(PREVIEW_DIR, exist_ok=True)
    CP.workbench(sc, res, tuple(CP.srgb_to_lin(at["bg"])))
    base = os.path.join(PREVIEW_DIR, name)
    rgb, z = CP.render_exr(sc, base + "_raw.exr")
    mask = CP.emissive_mask(sc, base + "_emit.exr")
    img = CP.post(rgb, z, mask, cam, cd, res, [tuple(a.location) for a in ANCHORS], at)
    CP.save_png(img, base + ".png")
    for p in (base + "_raw.exr", base + "_emit.exr"):
        if os.path.exists(p):
            os.remove(p)
    bpy.data.objects.remove(cam)
    bpy.data.cameras.remove(cd)
    return base + ".png"


def render_previews(target):
    spawn = Vector(SPOTS["Spot_spawn"].location)
    gate = Vector(SPOTS["Spot_gate"].location)
    shot("title_camera", tuple(SPOTS["Spot_camera_title"].location), tuple(target), lens=30, res=(1600, 1000), at=CITY_NIGHT)
    # follow camera: TownWorld offset (10, 12, -14) Unity = (10, 14, 12) Blender, aimed 0.8 m above the feet
    shot("play_spawn", tuple(spawn + Vector((10.0, 14.0, 12.0))), tuple(spawn + Vector((0, 0, 0.8))), lens=24.5)
    shot("close_gate", (-19.0, -9.0, 3.2), (GATE_X, GATE_Y + 0.6, 2.2), lens=30)
    shot("close_storefronts", (9.0, -13.5, 4.6), (14.0, 3.0, 1.6), lens=28)
    # plan: orthographic top view, Workbench only
    sc = bpy.context.scene
    cd = bpy.data.cameras.new("PlanCam")
    cd.type = "ORTHO"
    cd.ortho_scale = 70
    cam = bpy.data.objects.new("PlanCam", cd)
    cam.location = (0.0, -5.0, 120.0)
    sc.collection.objects.link(cam)
    sc.camera = cam
    import cc0_preview as CP  # noqa: E402
    CP.workbench(sc, (1400, 1400), tuple(CP.srgb_to_lin((0.46, 0.52, 0.78))))
    sc.render.filepath = os.path.join(PREVIEW_DIR, "plan_topdown.png")
    sc.render.image_settings.media_type = "IMAGE"
    sc.render.image_settings.file_format = "PNG"
    bpy.ops.render.render(write_still=True)
    bpy.data.objects.remove(cam)
    bpy.data.cameras.remove(cd)


def main():
    A.reset_scene()
    SPOTS.clear()
    ANCHORS.clear()
    COLS.clear()
    KIT.clear()
    build_scene()
    target = markers()
    write_manifest(tuple(target))
    objects = [o for o in bpy.context.scene.objects if o.type in ("MESH", "EMPTY")]
    A.export_fbx("Town/town.fbx", objects)
    A.save_blend("town_guild")
    if "--no-preview" not in sys.argv:
        render_previews(target)
        for name in os.listdir(PREVIEW_DIR):  # EXR passes are scratch files, never left in the shared folder
            if name.endswith(".exr"):
                os.remove(os.path.join(PREVIEW_DIR, name))
    print("GUILD_COMPLETE spots=%d colliders=%d light_anchors=%d" % (len(SPOTS), len(COLS), len(ANCHORS)), flush=True)


if __name__ == "__main__":
    main()
