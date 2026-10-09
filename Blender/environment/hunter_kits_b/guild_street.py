"""guild_street tileset: downtown street around the hunter guild at night, overrun by monsters (hunter theme, zone 11).

Outdoors, no ceiling. Road tiles (KayKit City Builder) with lane marks, manholes, kerbs and a crosswalk; walls are
2-storey shop facades built from KayKit City buildings with shopfronts, awnings, lit signs (M_Emit), warm windows,
AC units and balconies; crashed cars, streetlights, bins, barricades, cones, debris and violet gate cracks.
Floor pieces are flush (the grid normaliser clamps them to z <= 0).
"""
import math

from common_b import (R, blk, bx, cy, cone, ball, lathe, pz, ring, tube, fin, panel, sign, glyphs, garland,
                      door_frame, make_door, make_lid, publish, rect_pts, arena_scene, FACE_Y, kfit, kstand,
                      ao_paint)
import _kit_common_b as K  # noqa: E402

TS = "guild_street"
WORLD = "#1b2230"
B = FACE_Y + 0.01

ASPHALT = ["#4a4f58", "#505660", "#43484f"]; ASPH_GROUT = "#2f343c"; LANE = "#f3f3ee"; LANE_Y = "#f2c230"
SIDEWALK = ["#cfc9bc", "#c4bdaf", "#d8d2c5"]; SIDE_GROUT = "#8c877c"; CURB = "#9aa0a8"
CONCRETE = "#d8d2c4"; CONCRETE_DK = "#b9b2a2"; BRICK = "#b86a4e"; BRICK_DK = "#8e4f3a"
SIGN_COLS = ["#ff7a59", "#3fb8a8", "#ffd24a", "#7ec8ff", "#ff6fa0"]
GUILD_BLUE = "#2f6db8"; GUILD_BLUE_DK = "#1f4a86"; GUILD_GOLD = "#ffd24a"; DAWN = "#5aa7e0"
GLASS = "#c9efff"; DARK = "#2a3440"; METAL = "#8c97a2"; METAL_DK = "#4a5562"
CONE = "#ff7a1a"; WHITE = "#fff8e8"; STRIPE_R = "#ff8a2a"; LAMP_EM = "#ffe3a0"; VIOLET = "#9d6bff"
VIOLET_EM = "#c7a8ff"; WOOD = "#a77a4c"; WOOD_DK = "#6e4d2e"; GREEN = "#4fa35a"; GREEN_DK = "#2f7a40"
YELLOW_RAIL = "#f2c230"; CAR = ["#e8e9ee", "#d24a4a", "#3d7fd1"]; PAPER = ["#fffbe9", "#ffe6a8", "#e6f7ff"]
WARM = "#ffc878"; AC = "#b9c3cc"; BALC = "#6b5a4a"; SHOP_FRAME = "#2a3440"
CONE_GRID = [(-1.05 + 0.7 * i, -1.05 + 0.7 * j) for i in range(3) for j in range(3)]
SLAB_FACE = -1.93                     # face plane of the building walls (KayKit building, 3.8 m footprint)


# ---------------------------------------------------------------- floors (flush; road tiles dropped so their top is z = 0)

def asphalt_base(prefix):
    return [bx(prefix + "g", (4.0, 4.0, 0.2), (0, 0, -0.13), ASPH_GROUT)]


def asphalt_slab(prefix, rng, x0, y0, x1, y1, col=None):
    return K.poly_slab(prefix, rect_pts(x0, y0, x1, y1, 0.0), top=-0.012, thick=0.2,
                       color=col or K.pick(rng, ASPHALT, 0.05), bevel=0.0, seed=rng.randint(0, 999))


def road_quad(prefix, spec):
    """Four KayKit City road tiles (2 x 2 m each) making one 4 m road cell. spec = [(name, rot_z), ...] by quadrant."""
    out = []
    for (cx, cy_), (name, rot) in zip(((-1, -1), (1, -1), (-1, 1), (1, 1)), spec):
        out.append(kstand("kc", name, center=(cx, cy_), z0=-0.10, scale=1.0, rot_z=rot))
    return out


def floor_a():
    """Asphalt road (KayKit road tiles) with violet gate cracks and a glowing rift; a manhole and cracks."""
    rng = R(51)
    objs = road_quad("fa", [("road_straight", 0), ("road_corner", 0), ("road_straight", 90), ("road_junction", 0)])
    for i in range(7):
        x, y = rng.uniform(-1.6, 1.6), rng.uniform(-1.6, 1.6)
        objs.append(bx(f"fa_cr{i}", (rng.uniform(0.5, 1.1), 0.05, 0.01), (x, y, 0.004), "#2c3138",
                       rot=(0, 0, rng.uniform(-70, 70))))
    objs.append(bx("fa_rift0", (1.5, 0.07, 0.012), (0.4, -0.2, 0.006), VIOLET, "M_Emit", rot=(0, 0, 28)))
    objs.append(bx("fa_rift1", (0.9, 0.06, 0.012), (-0.6, 0.8, 0.006), VIOLET, "M_Emit", rot=(0, 0, -40)))
    objs.append(bx("fa_rift2", (0.6, 0.05, 0.012), (0.9, 1.2, 0.006), VIOLET_EM, "M_Emit", rot=(0, 0, 70)))
    objs.append(K.ngon_disc("fa_mh", 0.36, z=0.008, n=16, loc=(-0.95, 0.9, 0), color="#3a3f47"))
    objs.append(K.ring_strip("fa_mhr", 0.27, 0.31, z=0.012, n=16, color="#5a616b"))
    for i in range(5):
        x, y = rng.uniform(-1.5, 1.5), rng.uniform(-1.5, 1.5)
        pts = [(x + 0.12 * math.cos(math.tau * j / 6), y + 0.1 * math.sin(math.tau * j / 6)) for j in range(6)]
        objs.append(K.poly_slab(f"fa_pt{i}", pts, top=0.0, thick=0.01, color="#3a3f47", bevel=0.0))
    return [fin("floor_a", objs)]


def floor_b():
    """Road with a dashed centre line, yellow edge lines, a T-junction and skid marks; sewer grate."""
    rng = R(52)
    objs = road_quad("fb", [("road_tsplit", 0), ("road_straight", 90), ("road_straight", 0), ("road_straight", 0)])
    for i in range(3):
        y = -1.6 + i * 1.6
        objs.append(bx(f"fb_dash{i}", (0.14, 0.9, 0.012), (0, y, 0.006), LANE))
    for sx in (-1, 1):
        objs.append(bx(f"fb_edge{sx}", (0.1, 4.0, 0.012), (sx * 1.85, 0, 0.006), LANE_Y))
    for i, (x, y) in enumerate(((-0.2, -0.3), (0.7, 0.4), (-1.0, 0.1))):  # skid marks
        objs.append(bx(f"fb_skid{i}", (0.6, 0.04, 0.008), (x, y, 0.006), "#23272d", rot=(0, 0, 70 + 20 * i)))
    for i, (x, y, w) in enumerate(((-0.9, 1.2, 0.8), (0.2, -1.5, 0.6), (-1.4, -0.4, 0.5))):
        objs.append(bx(f"fb_patch{i}", (w, 0.7, 0.01), (x, y, 0.005), "#3c4149", rot=(0, 0, 12 * i)))
    return [fin("floor_b", objs)]


def floor_c():
    """Sidewalk tiles with kerbs on the road side, a zebra crosswalk, a drain grate and cracks."""
    rng = R(53)
    objs = asphalt_base("fc") + [K.poly_slab(f"fc_t{i}{j}", rect_pts(-2 + 2 * i, -2 + 2 * j, -2 + 2 * i + 2, -2 + 2 * j + 2, 0.04),
                                             top=-0.012, thick=0.2, color=K.pick(rng, SIDEWALK, 0.03), bevel=0.01)
                                 for i in range(2) for j in range(2)]
    for sx in (-1, 1):   # kerb stones along the road edge
        objs.append(bx(f"fc_kerb{sx}", (0.18, 4.0, 0.12), (sx * 1.91, 0, 0.06), CURB))
    for k in range(-1, 2):   # zebra
        objs.append(bx(f"fc_zb{k}", (0.22, 0.9, 0.01), (-1.2 + k * 1.2, 0.0, 0.0), LANE))
    for k in range(4):
        objs.append(bx(f"fc_gr{k}", (0.5, 0.05, 0.01), (1.45, -1.55 + k * 0.14, 0.0), "#5d646e"))
    objs.append(bx("fc_crk", (0.9, 0.03, 0.006), (-0.6, 1.1, 0.0), SIDE_GROUT, rot=(0, 0, 18)))
    objs.append(bx("fc_crk2", (0.5, 0.03, 0.006), (0.9, 0.35, 0.0), SIDE_GROUT, rot=(0, 0, -35)))
    objs.append(K.ngon_disc("fc_gum", 0.07, z=0.004, n=10, loc=(0.4, -1.3, 0), color="#2d2f33"))
    objs.append(K.ngon_disc("fc_wet", 0.3, z=0.003, n=12, loc=(-1.2, -1.2, 0), color="#7d8790"))
    return [fin("floor_c", objs)]


# ---------------------------------------------------------------- walls: KayKit building core + shopfront decals

def building(prefix, pack_name, color_tint=None):
    """KayKit City building fitted to the 3.8 x 3.8 x 4.47 m envelope (2-storey shop block) as the wall core."""
    return kfit("kc", pack_name, (3.8, 3.8, 4.47), center=(0, 0), z0=0.0)


def shopfront(k, bg, cols=(2, 3)):
    """Ground-floor shop on the -Y face: warm-lit window with a frame, glowing lit sign, striped awning, door,
    and an upper floor with a balcony, a row of warm windows and an AC unit."""
    r = R(600 + k)
    out = []
    # ground floor: frame + warm-lit window (M_Emit behind a glass pane), door
    out.append(bx(f"sf{k}fr", (2.5, 0.06, 1.95), (-0.35, B - 0.03, 1.1), SHOP_FRAME))
    out.append(bx(f"sf{k}warm", (2.3, 0.02, 1.7), (-0.35, B - 0.06, 1.1), WARM, "M_Emit"))
    out.append(bx(f"sf{k}gl", (2.3, 0.02, 1.7), (-0.35, B - 0.075, 1.1), GLASS, "M_Clear"))
    for i in range(3):   # window mullions
        out.append(bx(f"sf{k}mu{i}", (0.04, 0.03, 1.7), (-0.35 - 0.77 + 0.77 * i, B - 0.085, 1.1), SHOP_FRAME))
    out.append(bx(f"sf{k}dr", (0.6, 0.06, 1.5), (1.25, B - 0.03, 0.85), DARK))
    out.append(bx(f"sf{k}drw", (0.36, 0.02, 0.5), (1.25, B - 0.07, 1.35), WARM, "M_Emit"))
    # awning: striped canopy over the shop window
    for i in range(4):
        col = "#ffffff" if i % 2 else bg
        out.append(bx(f"sf{k}aw{i}", (0.7, 0.1, 0.12), (-1.5 + i * 0.75, B - 0.05, 2.3), col))
    # lit sign: glowing board with glyph strokes
    out.append(bx(f"sf{k}sb", (3.4, 0.04, 0.5), (0, B - 0.02, 3.2), bg, "M_Emit"))
    out += glyphs(f"sf{k}g", r, -1.5, 1.5, 3.02, 3.38, B - 0.05, "#ffffff", n=3, depth=0.02, mat="M_Emit")
    # upper floor: balcony with railing, warm windows, AC units
    out.append(bx(f"sf{k}bal", (3.2, 0.1, 0.06), (0, B - 0.05, 2.0), BALC))
    for i in range(5):
        out.append(bx(f"sf{k}rl{i}", (0.03, 0.04, 0.4), (-1.5 + i * 0.75, B - 0.06, 2.2), BALC))
    out.append(bx(f"sf{k}rt", (3.2, 0.04, 0.04), (0, B - 0.07, 2.4), BALC))
    for i, x in enumerate((-1.2, 0.0, 1.2)):
        out.append(bx(f"sf{k}uw{i}", (0.6, 0.02, 0.85), (x, B - 0.01, 2.75), WARM, "M_Emit"))
    out.append(bx(f"sf{k}ac", (0.6, 0.07, 0.42), (1.45, B - 0.035, 1.9), AC))
    out.append(bx(f"sf{k}acg", (0.5, 0.01, 0.3), (1.45, B - 0.075, 1.9), DARK))
    return out


def wall_a():
    """Shop block: a warm-lit shopfront under a striped awning, with a lit sign and balconies on each face."""
    def face(k):
        return shopfront(k, SIGN_COLS[k % len(SIGN_COLS)])
    objs = [building("wa", "building_E")] + K.four_sides(face)
    return [fin("wall_a", objs)]


def banner_face(k):
    """Guild block: blue dawn banner with a gold sun emblem, pilasters, tall lit windows and an AC unit."""
    out = []
    out.append(bx(f"gb{k}pl0", (0.4, 0.07, 4.1), (-1.6, B - 0.02, 2.05), CONCRETE_DK))
    out.append(bx(f"gb{k}pl1", (0.4, 0.07, 4.1), (1.6, B - 0.02, 2.05), CONCRETE_DK))
    out.append(pz(f"gb{k}ban", [(-0.55, 0.0), (0.55, 0.0), (0.55, -2.7), (0.0, -2.35), (-0.55, -2.7)], 0.04, axis="Y",
                  loc=(0, B - 0.03, 4.1), color=GUILD_BLUE))
    out.append(bx(f"gb{k}edge", (1.2, 0.02, 0.1), (0, B - 0.05, 4.0), GUILD_GOLD))
    out += K.sun_emblem(f"gb{k}sun", r=0.36, rays=12, loc=(0, B - 0.05, 2.9), ray_col=GUILD_GOLD, disc_col="#ffe9a3",
                        core_col="#ffb347", core_mat="M_Emit")
    for i, x in enumerate((-1.0, 1.0)):
        out.append(bx(f"gb{k}win{i}", (0.7, 0.02, 1.4), (x, B - 0.02, 0.9), WARM, "M_Emit"))
        out.append(bx(f"gb{k}wf{i}", (0.78, 0.04, 1.48), (x, B - 0.03, 0.9), SHOP_FRAME))
    out.append(bx(f"gb{k}ac", (0.6, 0.07, 0.42), (0.0, B - 0.035, 2.0), AC))
    return out


def wall_b():
    objs = [building("wb", "building_F")] + K.four_sides(banner_face)
    return [fin("wall_b", objs)]


def cracked_face(k):
    """Brick block with a violet gate rift glowing across the facade, a fire escape and a warm window row."""
    r = R(800 + k)
    out = []
    out.append(bx(f"cw{k}rift", (0.06, 0.02, 2.6), (0.0 + r.uniform(-0.2, 0.2), B - 0.02, 2.4), VIOLET, "M_Emit",
                  rot=(0, 0, r.uniform(-12, 12))))
    out.append(bx(f"cw{k}rift2", (1.1, 0.02, 0.05), (0.4, B - 0.02, 3.4), VIOLET, "M_Emit", rot=(0, 0, 38)))
    out.append(bx(f"cw{k}rift3", (0.8, 0.02, 0.05), (-0.8, B - 0.02, 1.1), VIOLET_EM, "M_Emit", rot=(0, 0, -30)))
    for i in range(3):   # fire escape
        out.append(bx(f"cw{k}fe{i}", (2.6, 0.07, 0.05), (0, B - 0.05, 0.9 + i * 0.9), METAL_DK))
        out.append(bx(f"cw{k}fv{i}", (0.05, 0.07, 0.9), (-1.3, B - 0.05, 0.45 + i * 0.9), METAL_DK))
        out.append(bx(f"cw{k}fw{i}", (0.05, 0.07, 0.9), (1.3, B - 0.05, 0.45 + i * 0.9), METAL_DK))
    out.append(bx(f"cw{k}ac", (0.8, 0.07, 0.6), (-0.9, B - 0.035, 3.2), AC))
    out.append(bx(f"cw{k}acg", (0.6, 0.01, 0.45), (-0.9, B - 0.075, 3.2), DARK))
    out.append(bx(f"cw{k}win", (0.9, 0.02, 0.9), (1.0, B - 0.02, 3.0), WARM, "M_Emit"))
    return out


def wall_c():
    objs = [building("wc", "building_G")] + K.four_sides(cracked_face)
    return [fin("wall_c", objs)]


# ---------------------------------------------------------------- overlays (awnings, cables and paper signs hang outside the wall)

def overlay_1():
    """Striped awning hanging from the top of a wall face, reaching out to -2.3."""
    out = []
    for i in range(9):
        x0 = -1.9 + i * 0.42
        out.append(pz(f"o1a{i}", [(0, 0), (0.42, 0), (0.42, -0.5), (0, -0.5)], 0.05, axis="Y",
                      loc=(x0, -2.22, 4.2), color="#ffffff" if i % 2 else STRIPE_R))
        out.append(bx(f"o1r{i}", (0.42, 0.44, 0.04), (x0 + 0.21, -2.12, 4.22), STRIPE_R if i % 2 else "#ffffff"))
    out.append(bx("o1rail", (3.8, 0.1, 0.06), (0, -2.2, 4.22), METAL_DK))
    return [fin("overlay_1", out)]


def overlay_2():
    """Hanging power cables and two small paper signs from the wall top."""
    r = R(10201)
    out = []
    for i in range(5):
        x = -1.6 + i * 0.8
        L = r.uniform(0.9, 1.8)
        pts = [(x, -2.05, 4.3), (x + 0.1, -2.12, 4.3 - L * 0.5), (x - 0.05, -2.18, 4.3 - L)]
        out.append(tube(f"o2c{i}", pts, 0.025, DARK, seg=3))
    for i, (x, col) in enumerate(((-0.5, "#ff6fa0"), (0.9, "#7ec8ff"))):
        out.append(bx(f"o2s{i}", (0.5, 0.03, 0.7), (x, -2.2, 3.2), col, rot=(0, 0, r.uniform(-8, 8))))
        out += glyphs(f"o2g{i}", r, x - 0.18, x + 0.18, 3.0, 3.4, -2.22, "#ffffff", n=2, depth=0.015)
    return [fin("overlay_2", out)]


# ---------------------------------------------------------------- torch = KayKit streetlight, lamp head at the top

def torch():
    """Street lamp: a KayKit City streetlight scaled to 3.4 m; LightAnchor under the lamp head."""
    lamp = kstand("kc", "streetlight", center=(0, 0), z0=0.0, scale=3.5)
    return [fin("torch", [lamp]), K.empty("LightAnchor", loc=(0.0, 0.0, 3.1))]


# ---------------------------------------------------------------- decor

def decor_3():
    """Crashed car from the KayKit City kit, scaled to a 2.4 m sedan, nosed into a barrier."""
    o = [kstand("kc", "car_sedan", center=(0, 0), z0=0.0, scale=2.6, rot_z=-12)]
    o.append(bx("d3_dent", (0.5, 0.04, 0.3), (0.2, -0.5, 0.45), "#3a3f47", rot=(0, 0, -12)))
    o.append(bx("d3_glow", (0.28, 0.06, 0.12), (-0.3, -0.5, 0.42), "#fff6c2", "M_Emit"))
    return [fin("decor_3", o)]


def decor_4():
    """Street bins: a KayKit dumpster and trash piles, with two wooden crates."""
    o = [kstand("kc", "dumpster", center=(-0.15, 0.1), z0=0.0, scale=2.6),
         kstand("kc", "trash_A", center=(0.6, -0.5), z0=0.0, scale=4.0),
         kstand("kc", "trash_B", center=(-0.7, -0.4), z0=0.0, scale=4.0),
         blk("d4_cr0", (0.6, 0.6, 0.5), (0.0, -0.6, 0.25), WOOD, bevel=0.03),
         blk("d4_cr1", (0.5, 0.5, 0.4), (0.05, -0.55, 0.7), WOOD_DK, bevel=0.03)]
    return [fin("decor_4", o)]


def decor_6():
    """Street planter with three KayKit bushes."""
    o = [blk("d6_pl", (0.9, 0.9, 0.6), (0, 0, 0.3), CONCRETE_DK, bevel=0.04),
         bx("d6_soil", (0.8, 0.8, 0.04), (0, 0, 0.6), "#4a3a2a")]
    for i, (x, y) in enumerate(((-0.2, -0.1), (0.2, 0.15), (0.25, -0.2))):
        o.append(kstand("kc", "bush", center=(x, y), z0=0.6, scale=2.4 + 0.2 * i))
    return [fin("decor_6", o)]


# ---------------------------------------------------------------- arena: crossroads in front of the guild, enclosed by facades

def arena_builder():
    """Night street: asphalt crossing with lane marks and a zebra, KayKit buildings, streetlights, parked cars."""
    rng = R(920)
    floor = [bx("ar_road", (19.2, 19.2, 0.04), (0, 0, -0.02), "#4a4f58")]
    for i in range(-4, 5):   # dashed centre line along the street
        floor.append(bx(f"ar_dash{i}", (0.9, 0.12, 0.01), (i * 2.0, 0.0, 0.005), LANE))
    for i in range(8):       # zebra in front of the guild
        floor.append(bx(f"ar_zb{i}", (0.6, 2.4, 0.01), (-7.0 + i * 2.0, -5.5, 0.005), LANE))
    back = [bx("ar_guild", (24, 3.0, 12), (0, 19, 6), CONCRETE),
            bx("ar_guild_base", (24, 3.2, 1.2), (0, 18.8, 0.6), CONCRETE_DK)]
    back.append(pz("ar_banner", [(-1.6, 0.0), (1.6, 0.0), (1.6, -5.0), (0.0, -4.2), (-1.6, -5.0)], 0.2, axis="Y",
                   loc=(0, 17.4, 9.5), color=GUILD_BLUE))
    for x in (-8.0, -4.0, 4.0, 8.0):
        for z in (3.5, 7.5):
            back.append(bx(f"ar_win{x}{z}", (2.0, 0.1, 1.6), (x, 17.4, z), WARM, "M_Emit"))
    # enclosing facades: KayKit buildings on both sides, behind the guild and behind the enemies
    back.append(kfit("kc", "building_H", (7.0, 8.0, 9.0), center=(-13.0, 8.0), z0=0.0))
    back.append(kfit("kc", "building_G", (7.0, 8.0, 8.5), center=(13.0, 8.0), z0=0.0))
    back.append(kfit("kc", "building_E", (4.0, 4.0, 4.5), center=(-11.0, -6.0), z0=0.0))
    back.append(kfit("kc", "building_F", (4.0, 4.0, 4.5), center=(11.0, -6.0), z0=0.0))
    for x in (-8.0, 0.0, 8.0):
        back.append(kfit("kc", "building_F", (4.0, 4.0, 4.5), center=(x, 22.0), z0=0.0))
    # pass 2: the zone behind the enemies (y 6..12) is filled up to about 6 m with tall KayKit blocks
    for x, y, nm in ((-9.0, 9.5, "building_A"), (-3.0, 11.0, "building_B"), (3.0, 11.0, "building_B"), (9.0, 9.5, "building_A")):
        back.append(kfit("kc", nm, (3.6, 3.6, 5.8), center=(x, y), z0=0.0))
    back.append(kfit("kc", "building_E", (3.6, 3.6, 6.0), center=(-6.0, 12.4), z0=0.0))
    back.append(kfit("kc", "building_G", (3.6, 3.6, 5.6), center=(6.0, 12.4), z0=0.0))
    for sx in (-1, 1):   # streetlights
        for y in (2.0, 6.0, 10.0):
            back.append(kstand("kc", "streetlight", center=(sx * 8.5, y), z0=0.0, scale=4.4))
    back.append(kstand("kc", "car_sedan", center=(-5.0, 6.8), z0=0.0, scale=2.6, rot_z=0))
    back.append(kstand("kc", "car_taxi", center=(5.2, 7.0), z0=0.0, scale=2.6, rot_z=180))
    back.append(kstand("kc", "car_police", center=(-1.5, 4.6), z0=0.0, scale=2.6, rot_z=-15))
    back.append(kstand("kc", "firehydrant", center=(3.0, 4.2), z0=0.0, scale=3.0))
    back.append(kstand("kc", "trash_A", center=(-6.5, 4.4), z0=0.0, scale=4.0))
    back.append(kstand("kc", "trash_B", center=(7.0, 4.0), z0=0.0, scale=4.0))
    back.append(kstand("kc", "trafficlight_A", center=(-8.0, -2.5), z0=0.0, scale=2.6))
    back.append(kstand("kc", "dumpster", center=(-1.0, 8.4), z0=0.0, scale=3.0, rot_z=20))
    back.append(kstand("kc", "bush", center=(-7.6, 8.6), z0=0.0, scale=2.4))
    back.append(kstand("kc", "bush", center=(7.6, 8.2), z0=0.0, scale=2.4))
    back.append(kstand("kc", "trash_B", center=(3.6, 8.9), z0=0.0, scale=3.2))
    for i, (x, y) in enumerate(((-6.0, -2.0), (6.0, -2.0))):   # barricades at the near corners
        back.append(bx(f"ar_bar{i}", (2.2, 0.1, 0.8), (x, y, 0.5), STRIPE_R))
    back += garland("ar_gl", -7.5, 7.5, (7.0, 7.0), 0.9, 12.5, 16, [CAR[1], GUILD_GOLD, GUILD_BLUE, WHITE], flag_w=0.35,
                    flag_h=0.45)
    return floor, back


def arena():
    return arena_scene(TS, arena_builder, ("#3c5b86", "#141d2e"), WORLD)


def shutter_leaf(w=2.3, h=3.25, locked=False):
    x0, x1 = -w / 2 + 0.02, w / 2 - 0.02
    t = 0.1
    out = []
    n = 12
    for i in range(n):
        z = 0.05 + i * (h - 0.1) / n
        out.append(bx(f"sh_s{i}", (x1 - x0, t, (h - 0.1) / n - 0.04), ((x0 + x1) / 2, 0, z + (h - 0.1) / n / 2),
                      "#3d5570" if i % 2 else "#4a6584"))
    out.append(bx("sh_frame", (x1 - x0 + 0.04, t + 0.02, 0.08), ((x0 + x1) / 2, 0, h - 0.04), GUILD_BLUE_DK))
    out.append(bx("sh_bot", (x1 - x0 + 0.04, t + 0.02, 0.08), ((x0 + x1) / 2, 0, 0.04), GUILD_BLUE_DK))
    out.append(cy("sh_emb", 0.36, 0.02, (0, -t / 2 - 0.01, 2.2), GUILD_GOLD, rot=(90, 0, 0), seg=16))
    out += K.sun_emblem("sh_sun", r=0.3, rays=10, loc=(0, -t / 2 - 0.02, 2.2), ray_col=GUILD_GOLD, disc_col="#ffe9a3",
                        core_col="#ffb347", core_mat="M_Emit")
    if locked:
        out.append(bx("sh_warn", (0.5, 0.03, 0.5), (-0.7, -t / 2 - 0.02, 1.0), YELLOW_RAIL))
    return out


def door():
    frame = door_frame("dd", CONCRETE, GUILD_BLUE, w=2.3, h=3.25)
    return make_door("door", frame, shutter_leaf(), 2.3)


def door_locked():
    frame = door_frame("ddl", CONCRETE, GUILD_BLUE, w=2.3, h=3.25)
    chain = [tube("lk_ch0", [(-0.9, -0.18, 2.8), (-0.6, -0.2, 2.2), (-0.7, -0.2, 1.6)], 0.025, METAL_DK, seg=3),
             tube("lk_ch1", [(0.9, -0.18, 2.8), (0.6, -0.2, 2.2), (0.7, -0.2, 1.6)], 0.025, METAL_DK, seg=3),
             blk("lk_pad", (0.3, 0.14, 0.32), (0.0, -0.2, 1.5), GUILD_GOLD, bevel=0.02),
             ring("lk_sh", 0.09, 0.022, (0.0, -0.2, 1.75), METAL, rot=(90, 0, 0), seg=16, minor=4)]
    return make_door("door_locked", frame, shutter_leaf(locked=True), 2.3, lock_objs=chain)


def stairs(down):
    rng = R(3051 if down else 3151)
    o = []
    n, y0, y1 = 10, -1.4, 1.8
    run, rise = (y1 - y0) / n, 0.24
    if down:
        regions = [(-2, -2, -1.3, 2), (1.3, -2, 2, 2), (-1.3, -2, 1.3, -1.4), (-1.3, 1.8, 1.3, 2)]
        for i, (x0, yy0, x1, yy1) in enumerate(regions):
            o.append(bx(f"sd_g{i}", (x1 - x0, yy1 - yy0, 0.2), ((x0 + x1) / 2, (yy0 + yy1) / 2, -0.13), ASPH_GROUT))
            o.append(K.poly_slab(f"sd_t{i}", rect_pts(x0, yy0, x1, yy1, 0.035), top=-0.012, thick=0.2,
                                 color=K.pick(rng, SIDEWALK, 0.03), bevel=0.01))
        for i in range(n):
            top = -rise * (i + 1)
            o.append(blk(f"sd_st{i}", (2.6, run + 0.01, 0.2), (0, y0 + run * (i + 0.5), top - 0.1), CONCRETE, bevel=0.02))
            o.append(bx(f"sd_nz{i}", (2.6, 0.05, 0.03), (0, y0 + run * i + 0.03, top + 0.005), YELLOW_RAIL))
        for sx in (-1, 1):
            o.append(bx(f"sd_w{sx}", (0.14, y1 - y0, 2.6), (sx * 1.33, (y0 + y1) / 2, -1.3), DARK))
            pts = [(sx * 1.22, y0 + run * j, -rise * j + 0.95) for j in range(n + 1)]
            o.append(tube(f"sd_rl{sx}", pts, 0.03, YELLOW_RAIL))
            o.append(cy(f"sd_rp{sx}", 0.035, 0.95, (sx * 1.22, y0, 0.47), METAL_DK, seg=6))
        o.append(bx("sd_bk", (2.6, 0.14, 2.6), (0, y1 + 0.07, -1.3), DARK))
        o.append(bx("sd_glow", (2.2, 0.04, 0.12), (0, y1 - 0.05, -2.2), VIOLET_EM, "M_Emit"))
        return [fin("stairs_down", o)]
    ztop = 2.25
    run, rise = (y1 - y0) / 9, ztop / 9
    for i in range(9):
        top = rise * (i + 1)
        o.append(blk(f"su_st{i}", (2.36, run + 0.03, 0.18), (0, y0 + run * (i + 0.5), top - 0.09), CONCRETE, bevel=0.02))
        o.append(bx(f"su_sr{i}", (2.3, run, top - 0.17), (0, y0 + run * (i + 0.5), (top - 0.17) / 2), CONCRETE_DK))
        o.append(bx(f"su_nz{i}", (2.36, 0.05, 0.03), (0, y0 + run * i + 0.03, top + 0.005), YELLOW_RAIL))
    o.append(blk("su_land", (2.4, 0.9, ztop), (0, 1.85, ztop / 2), CONCRETE, bevel=0.03))
    for sx in (-1, 1):
        o.append(K.prism(f"su_sg{sx}", [(y0 - 0.05, 0), (y1, 0), (y1, ztop)], 0.14, axis="X",
                         loc=(sx * 1.22, 0, 0), color=CONCRETE_DK))
        pts = [(sx * 1.15, y0, rise * j + 0.95) for j in range(10)] + [(sx * 1.15, 2.3, ztop + 0.95)]
        o.append(tube(f"su_rl{sx}", pts, 0.03, YELLOW_RAIL))
        o.append(cy(f"su_np{sx}", 0.035, 0.95, (sx * 1.15, y0, 0.47), METAL_DK, seg=6))
    return [fin("stairs_up", o)]


def stairs_down():
    return stairs(True)


def stairs_up():
    return stairs(False)


def chest():
    W, D, H = 1.1, 0.72, 0.55
    body = [blk("cb_box", (W, D, H), (0, 0, H / 2), WOOD, bevel=0.03)]
    for z in (0.14, 0.4):
        body.append(bx(f"cb_pl{z}", (W + 0.02, D + 0.02, 0.05), (0, 0, z), WOOD_DK))
    body.append(bx("cb_rope", (0.1, D + 0.03, H + 0.005), (0, 0, H / 2), "#d8c08a"))
    body.append(blk("cb_emb", (0.3, 0.04, 0.3), (0, -D / 2 - 0.02, H * 0.6), GUILD_BLUE, bevel=0.01))
    for sx in (-1, 1):  # steel corner bands
        for sy in (-1, 1):
            body.append(bx(f"cb_cn{sx}{sy}", (0.06, 0.06, H + 0.01), (sx * W / 2, sy * D / 2, H / 2), METAL_DK))
    lid = [blk("cl_lid", (W + 0.03, D + 0.03, 0.1), (0, 0, H + 0.05), WOOD_DK, bevel=0.02),
           bx("cl_rope", (0.1, D + 0.05, 0.11), (0, 0, H + 0.05), "#d8c08a"),
           bx("cl_hasp", (0.14, 0.05, 0.12), (0, -D / 2 - 0.03, H + 0.02), METAL)]
    return [fin("chest", body), make_lid(lid, D, H)]


def lore_stone():
    """Wanted-poster board on a steel post, with violet rune scratches."""
    r = R(5101)
    o = [cy("ls_p", 0.05, 1.8, (0, 0, 0.9), METAL_DK, seg=8), blk("ls_base", (0.6, 0.5, 0.1), (0, 0, 0.05), METAL_DK, bevel=0.02),
         blk("ls_fr", (1.5, 0.1, 1.3), (0, 0, 1.7), METAL_DK, bevel=0.03),
         bx("ls_bd", (1.36, 0.06, 1.16), (0, -0.06, 1.7), "#8c6a4a")]
    for i, (x, z) in enumerate(((-0.35, 2.05), (0.3, 1.95), (-0.3, 1.3), (0.33, 1.35))):
        o.append(bx(f"ls_pp{i}", (0.34, 0.01, 0.38), (x, -0.11, z), PAPER[i % 3], rot=(0, r.uniform(-12, 12), 0)))
    o.append(ball("ls_pin0", 0.02, (-0.35, -0.12, 2.2), "#ff5a4a", seg=5, rings=3))
    o += glyphs("ls_g", r, -0.5, 0.5, 2.25, 2.5, -0.11, VIOLET_EM, n=4, depth=0.02, mat="M_Emit")
    return [fin("lore_stone", o)]


def trap():
    """Road spike strip: a dark plate with steel spikes (retracted 0.5 m below the asphalt)."""
    plate = [blk("tr_fr", (3.5, 3.5, 0.06), (0, 0, 0.0), LANE_Y, bevel=0.02),
             bx("tr_pl", (3.2, 3.2, 0.06), (0, 0, 0.01), "#3b4048")]
    for i, (x, y) in enumerate(CONE_GRID):
        plate.append(K.ngon_disc(f"tr_h{i}", 0.1, z=0.042, n=8, loc=(x, y, 0), color="#2a2e35"))
    for i in range(8):  # hazard stripes on the rim
        a = math.tau * i / 8
        plate.append(bx(f"tr_hz{i}", (0.5, 0.12, 0.01), (1.62 * math.cos(a), 1.62 * math.sin(a), 0.035),
                        LANE_Y if i % 2 else "#2b2f36", rot=(0, 0, math.degrees(a))))
    plate = fin("trap", plate)
    sp = [bx("sp_base", (3.2, 3.2, 0.04), (0, 0, -0.03), METAL_DK)]
    for i, (x, y) in enumerate(CONE_GRID):
        sp.append(cone(f"sp_c{i}", 0.05, 0.4, (x, y, 0.2), METAL, seg=5))
    spikes = fin("Spikes", sp)
    spikes.location = (0, 0, -0.5)
    return [plate, spikes]


def spring():
    """Health vending machine with a green glow, a bench and a healing ring on the pavement."""
    o = [K.ring_strip("sp_ring", 1.25, 1.36, z=0.012, n=36, color="#7fffb0", mat="M_Emit")]
    o.append(blk("sp_vm", (0.9, 0.7, 1.9), (0.0, 0.8, 0.95), "#ffffff", bevel=0.03))
    o.append(bx("sp_vmscr", (0.6, 0.02, 0.9), (0.0, 0.42, 1.35), "#7fffb0", "M_Emit"))
    for i in range(3):
        o.append(bx(f"sp_vmb{i}", (0.16, 0.02, 0.2), (-0.2 + 0.2 * i, 0.4, 0.7), GUILD_BLUE, rot=(0, 0, 0)))
    o.append(bx("sp_vmg", (0.7, 0.02, 0.2), (0.0, 0.41, 0.4), "#7fffb0", "M_Emit"))
    o.append(blk("sp_bn", (1.5, 0.45, 0.1), (-0.9, -0.6, 0.45), WOOD, bevel=0.02))
    for sx in (-1, 1):
        o.append(bx(f"sp_bl{sx}", (0.08, 0.4, 0.45), (-0.9 + sx * 0.6, -0.6, 0.22), METAL_DK))
    return [fin("spring", o)]


def warp():
    """Violet gate portal: a cracked round plate with a rift arch standing in the middle."""
    o = [cy("wp_d0", 1.6, 0.12, (0, 0, 0.06), "#3b4048", seg=20), K.ring_strip("wp_r1", 1.1, 1.2, z=0.13, n=36, color=VIOLET_EM, mat="M_Emit")]
    arch = [(-0.9, -0.05, 0.0), (-0.9, -0.05, 1.5), (-0.5, -0.05, 2.3), (0.0, -0.05, 2.5), (0.5, -0.05, 2.3),
            (0.9, -0.05, 1.5), (0.9, -0.05, 0.0)]
    o.append(tube("wp_arch", arch, 0.08, VIOLET, mat="M_Emit", seg=4))
    o.append(cy("wp_pl", 0.02, 1.0, (0, -0.05, 0.6), VIOLET_EM, mat="M_Clear", seg=6))
    for i in range(4):
        a = 2 * math.pi * i / 4
        o.append(K.shard(f"wp_sh{i}", r=0.12, h=0.6, loc=(math.cos(a) * 1.3, math.sin(a) * 1.3, 0), rot=(0, 0, math.degrees(a)),
                         color="#3b3550", seed=i))
    return [fin("warp", o)]


def boss_gate():
    o = [blk("bg_pl0", (0.3, 0.6, 3.7), (-1.85, 0, 1.85), CONCRETE, bevel=0.03),
         blk("bg_pl1", (0.3, 0.6, 3.7), (1.85, 0, 1.85), CONCRETE, bevel=0.03),
         blk("bg_hd", (4.0, 0.6, 0.5), (0, 0, 3.4), CONCRETE, bevel=0.03),
         blk("bg_th", (3.7, 0.7, 0.06), (0, 0, 0.03), METAL_DK, bevel=0.01)]
    o += sign("bg_sg", R(2201), -0.9, 0.9, 3.5, 3.85, -0.3, GUILD_BLUE, WHITE, n=3, depth=0.05)
    for sx in (-1, 1):
        xc = sx * 0.9
        o.append(blk(f"bg_sh{sx}", (1.72, 0.16, 3.1), (xc, 0, 1.55), "#3d5570", bevel=0.02))
        for k in range(6):
            o.append(bx(f"bg_sl{sx}{k}", (1.6, 0.04, 0.05), (xc, -0.1, 0.4 + k * 0.45), GUILD_BLUE_DK))
        pts = [(xc - 0.6 + 0.2 * k, -0.11, min(0.3 + 0.5 * (k % 2) + 0.2 * k, 3.0)) for k in range(7)]
        o.append(tube(f"bg_crk{sx}", pts, 0.03, VIOLET_EM, mat="M_Emit"))
    o.append(bx("bg_glow", (2.8, 0.7, 0.02), (0, -0.4, 0.01), VIOLET_EM, "M_Emit"))
    return [fin("boss_gate", o)]


def decor_1():
    """Striped road barricade with a plank and two legs."""
    o = []
    for i in range(4):
        o.append(bx(f"d1_pl{i}", (1.4, 0.04, 0.3), (0, -0.05, 0.6 - 0.15 * i + 0.05), STRIPE_R if i % 2 else WHITE))
    for sx in (-1, 1):
        o.append(bx(f"d1_lg{sx}", (0.07, 0.6, 0.9), (sx * 0.62, 0.0, 0.45), METAL_DK, rot=(20, 0, 0)))
        o.append(cy(f"d1_ft{sx}", 0.04, 0.8, (sx * 0.62, 0.0, 0.0), DARK, rot=(90, 0, 0), seg=6))
        o.append(bx(f"d1_rf{sx}", (0.1, 0.06, 0.08), (sx * 0.62, -0.04, 0.8), "#ffb020", "M_Emit"))
        o.append(cy(f"d1_cap{sx}", 0.035, 0.05, (sx * 0.62, 0.0, 0.92), DARK, seg=8))
    o.append(bx("d1_top", (1.5, 0.12, 0.05), (0, 0.0, 0.94), STRIPE_R))
    o.append(bx("d1_top2", (1.5, 0.12, 0.05), (0, 0.0, 0.9), WHITE))
    return [fin("decor_1", o)]


def decor_2():
    """Three traffic cones."""
    o = []
    for i, (x, y) in enumerate(((-0.3, 0.0), (0.3, 0.1), (0.0, -0.4))):
        o.append(cone(f"d2_c{i}", 0.22, 0.7, (x, y, 0.35), CONE, seg=10))
        o.append(cy(f"d2_base{i}", 0.26, 0.05, (x, y, 0.025), "#2b2f36", seg=10))
        o.append(cy(f"d2_st{i}", 0.12, 0.08, (x, y, 0.36), WHITE, seg=10))
    return [fin("decor_2", o)]


def decor_5():
    """A-frame shop standee with a signboard and a small guild sun emblem."""
    o = []
    for sy, nm in ((-1, "f"), (1, "b")):
        o.append(blk(f"d5_{nm}", (0.7, 0.05, 1.1), (0, sy * 0.1, 0.6), "#fff7e6", bevel=0.01, rot=(sy * 18, 0, 0)))
    o += sign("d5_sg", R(9601), -0.3, 0.3, 0.8, 1.2, -0.26, SIGN_COLS[1], WHITE, n=2, depth=0.03)
    return [fin("decor_5", o)]


def foe_marker():
    """Floor marker for a foe: violet ring, six crystal shards and a floating gate crystal."""
    o = [K.ring_strip("fm_r0", 1.0, 1.12, z=0.02, n=32, color=VIOLET),
         K.ring_strip("fm_r1", 0.7, 0.76, z=0.02, n=32, color=VIOLET_EM)]
    o.append(K.prism("fm_st", K.star_pts(6, 0.66, 0.3), 0.012, axis="Z", loc=(0, 0, 0.02), color=VIOLET_EM, mat="M_Emit"))
    for i in range(6):
        a = 2 * math.pi * i / 6
        o.append(K.shard(f"fm_sp{i}", r=0.1, h=0.55, loc=(math.cos(a) * 1.2, math.sin(a) * 1.2, 0),
                         rot=(0, -25, math.degrees(a)), color="#3b3550", seed=i))
    o.append(K.gem("fm_c", 0.3, loc=(0, 0, 2.0), color=VIOLET, mat="M_Emit", h=2.0, sides=6))
    return [fin("foe_marker", o)]


def corridor():
    """Street canyon: DungeonWorld rules (lamp 1.7 m, decor 1.45 m + 1 m, crate 1.3 m off the wall)."""
    plan = []
    for y in range(-1, 5):
        plan.append(("floor_b" if y % 2 else "floor_c", (0, y), 0, (0, 0, 0)))
    for y in range(-1, 6):
        for x in (-1, 1):
            plan.append((("wall_a", "wall_b", "wall_c")[(x * 7 + y * 3) % 3], (x, y), 0, (0, 0, 0)))
    plan.append(("wall_b", (0, 5), 0, (0, 0, 0)))
    plan += [
        ("torch", (0, 1), 90, (-1.7, 0, 0)), ("torch", (0, 3), -90, (1.7, 0, 0)),
        ("overlay_1", (-1, 1), 90, (0, 0, 0)), ("overlay_2", (1, 2), -90, (0, 0, 0)),
        ("overlay_1", (0, 5), 0, (0, 0, 0)),
        ("decor_3", (0, 2), 90, (-1.45, 1.0, 0)), ("decor_2", (0, 4), -90, (1.45, -1.0, 0)),
        ("chest", (0, 0), -90, (1.3, 0.2, 0)),
    ]
    return plan



# ---------------------------------------------------------------- pieces, layouts

PIECES = [
    ("floor_a", floor_a), ("floor_b", floor_b), ("floor_c", floor_c),
    ("wall_a", wall_a), ("wall_b", wall_b), ("wall_c", wall_c),
    ("door", door), ("door_locked", door_locked),
    ("stairs_down", stairs_down), ("stairs_up", stairs_up), ("chest", chest), ("lore_stone", lore_stone),
    ("trap", trap), ("spring", spring), ("warp", warp), ("torch", torch),
    ("decor_1", decor_1), ("decor_2", decor_2), ("decor_3", decor_3), ("decor_4", decor_4), ("decor_5", decor_5),
    ("decor_6", decor_6), ("overlay_1", overlay_1), ("overlay_2", overlay_2), ("boss_gate", boss_gate),
    ("foe_marker", lambda: foe_marker()),
]

LAYOUT = [
    "W W boss_gate W W".split(),
    "W lore_stone . torch W".split(),
    "W . chest warp W".split(),
    "W trap spring stairs_down W".split(),
    "W W door W W".split(),
]
EXTRAS = [
    ("decor_3", (1.3, 2.25), 0), ("decor_1", (3.3, 2.6), 0), ("decor_2", (1.3, 1.7), 40), ("decor_4", (2.6, 3.3), 0),
    ("decor_6", (3.25, 1.35), 0), ("decor_5", (2.0, 3.35), 0), ("foe_marker", (1.0, 3.0), 0),
    ("overlay_1", (1, 4), 0), ("overlay_2", (3, 4), 0), ("overlay_1", (0, 2), 90), ("overlay_2", (4, 3), -90),
]


def main():
    publish(TS, PIECES, LAYOUT, EXTRAS, WORLD, corridor, arena)


if __name__ == "__main__":
    main()
