"""hospital tileset: abandoned hospital, kept cute and warm (hunter theme, zone 9). No blood, no bodies.

Pale mint tiles under a clean panel ceiling with round lamps, ventilation grilles and curtain rails. White ward walls
with mint wainscot and blue handrails, pastel ward curtains, a nurse hatch recessed into the wall, beds, IV stands,
wheelchairs, medicine carts, potted plants, red-cross signs. Door = ward double door with round windows;
door_locked = staff-only door with a card reader; arena = enclosed hospital lobby with waiting seats.
"""
import math

from common_b import (R, blk, bx, cy, cone, ball, lathe, pz, ring, tube, fin, face_y, panel, sign, glyphs,
                      garland, door_frame, make_door, make_lid, publish, rect_pts, arena_scene, FACE_Y, CEIL,
                      WALL_TOP, CORE_Y0, SLAB_D, ao_paint, slab_boxes, wall_core, recess_glass, frame_strips,
                      ceil_panel, fixture, round_lamp, hang_string, paper_lantern, kfit, kstand)
import _kit_common_b as K  # noqa: E402

TS = "hospital"
WORLD = "#22363a"
B = FACE_Y + 0.01

WHITE = "#f8fdfd"; WHITE_DK = "#e4eef0"; MINT = ["#d3f2e6", "#c6ebdc", "#dcf7ef"]; MINT_DK = "#9fd0c2"
MINT_WAIN = "#9fdcc9"; BLUE = "#3f8fd6"; BLUE_LT = "#8cc2ea"; BLUE_DK = "#2d64a3"; RED = "#e5534b"; RED_DK = "#b33b35"
PINK_CU = "#f3c6d8"; SKYC = "#c6e9f5"; LEMON = "#fbe7a1"; GREEN = "#4fa35a"; GREEN_DK = "#2f7a40"
METAL = "#b8c4cc"; METAL_DK = "#6b7b86"; DARK = "#2d3e52"; GLASS = "#c9efff"; YELLOW = "#ffd24a"; YELLOW_DK = "#d9a52b"
CLAY = "#f1f6f4"; VIOLET = "#9d6bff"; VIOLET_EM = "#7b3dff"; MINT_EM = "#7fffd4"; WARM_EM = "#ffe2b0"
CREAM = "#fbf7ef"; CHART = "#ffffff"; SOFT_BLUE = "#cfe8ff"; PLATE = "#f3f0e6"
CEIL_PANEL = "#f4f8f7"; CEIL_SEAM = "#c4d6d4"; GRILLE = "#e8f1f0"
HOLE_NURSE = (-0.9, 0.9, 1.2, 2.9)   # nurse hatch recess on a wall face: x0, x1, z0, z1
SYRINGE_GRID = [(-1.05 + 0.7 * i, -1.05 + 0.7 * j) for i in range(3) for j in range(3)]


# ---------------------------------------------------------------- ceilings (floor pieces carry a `Ceiling` root)

def ceiling_hospital(prefix, layout="panel", seed=0):
    """Clean panel ceiling (2 x 2 white panels), round lamps or a fluorescent bar, a ventilation grille and
    curtain rails with pastel curtains hanging at the edges. Everything hangs at or below CEIL."""
    r = R(seed)
    o = [bx(prefix + "seam", (4.0, 4.0, 0.04), (0, 0, CEIL - 0.02), CEIL_SEAM)]
    for i in range(2):
        for j in range(2):
            x0, y0 = -2 + 2 * i, -2 + 2 * j
            o.append(ceil_panel(f"{prefix}pn{i}{j}", x0 + 0.04, y0 + 0.04, x0 + 1.96, y0 + 1.96,
                                r.choice([CEIL_PANEL, WHITE_DK]), thick=0.1))
    if layout == "round":
        o += round_lamp(prefix + "rl", 0.0, 0.0, CEIL - 0.1, r=0.42)
    else:
        for y in (-0.9, 0.9):
            o += fixture(f"{prefix}fy{y}", 0.0, y, CEIL - 0.1, 1.8, 0.3, rot_z=90, housing=WHITE_DK)
    # ventilation grille on one ceiling edge: a frame with dark slats
    o.append(bx(prefix + "vg", (0.9, 0.6, 0.03), (1.35, 0.8, CEIL - 0.13), GRILLE))
    for j in range(5):
        o.append(bx(f"{prefix}vs{j}", (0.8, 0.04, 0.02), (1.35, 0.52 + 0.1 * j, CEIL - 0.15), DARK))
    # curtain rails along the corridor with a pastel curtain hanging from each
    for sx in (-1, 1):
        o.append(bx(f"{prefix}cr{sx}", (0.04, 4.0, 0.04), (sx * 1.55, 0.0, CEIL - 0.13), METAL))
        for k, yc in enumerate((-1.0, 1.0)):
            o.append(bx(f"{prefix}cu{sx}{k}", (0.02, 0.9, 1.1), (sx * 1.55, yc, CEIL - 0.7), (PINK_CU, SKYC)[k]))
    return o


# ---------------------------------------------------------------- floors (flush; floor top z = 0)

def floor_a():
    """Pale mint tiles in a 2 x 2 layout, with a few lighter inlays and scuffs set flush."""
    rng = R(41)
    objs = grout("ha") + tiles2("ha_t", rng, MINT)
    for i in range(4):
        x, y = -1.2 + 2.4 * (i % 2), -1.2 + 2.4 * (i // 2)
        objs.append(K.poly_slab(f"ha_in{i}", rect_pts(x - 0.35, y - 0.35, x + 0.35, y + 0.35), top=-0.008, thick=0.012,
                                color="#ffffff", bevel=0.0))
    for i in range(6):
        x, y = rng.uniform(-1.4, 1.4), rng.uniform(-1.4, 1.4)
        k = rng.uniform(0.2, 0.35)
        pts = [(x + k * math.cos(math.tau * j / 6), y + k * 0.6 * math.sin(math.tau * j / 6)) for j in range(6)]
        objs.append(K.poly_slab(f"ha_sc{i}", pts, top=-0.007, thick=0.011, color="#b7d9cc", bevel=0.0))
    return [fin("floor_a", objs), fin("Ceiling", ceiling_hospital("ha", "panel", seed=51))]


def floor_b():
    """Checker floor, 4 x 4 squares of mint and white with a blue entry line."""
    rng = R(42)
    objs = grout("hb", "#7fa9a2")
    for i in range(4):
        for j in range(4):
            x0, y0 = -2 + i, -2 + j
            col = WHITE if (i + j) % 2 else MINT[(i * 3 + j) % 3]
            objs.append(K.poly_slab(f"hb_t{i}{j}", rect_pts(x0, y0, x0 + 1, y0 + 1, 0.035), top=-0.012, thick=0.2,
                                    color=K.pick(rng, [col], 0.02), bevel=0.008))
    objs.append(bx("hb_line", (0.16, 4.0, 0.02), (0, 0, -0.01), BLUE_LT))
    return [fin("floor_b", objs), fin("Ceiling", ceiling_hospital("hb", "bars", seed=52))]


def floor_c():
    """Mint tiles with a blue rubber runner and little red crosses set flush."""
    rng = R(43)
    objs = grout("hc") + tiles2("hc_t", rng, MINT)
    objs.append(bx("hc_mat", (1.1, 4.0, 0.02), (0, 0, -0.01), "#5fa8e6"))
    for i, (x, y) in enumerate(((-1.4, -1.0), (1.4, 0.8), (-1.3, 1.3))):
        objs.append(bx(f"hc_c{i}h", (0.28, 0.07, 0.02), (x, y, 0.0), RED))
        objs.append(bx(f"hc_c{i}v", (0.07, 0.28, 0.02), (x, y, 0.0), RED))
    for sx in (-1, 1):
        objs.append(bx(f"hc_el{sx}", (0.08, 4.0, 0.012), (sx * 1.92, 0, 0.0), "#f4f7fa"))
    for sy in (-1, 1):
        objs.append(bx(f"hc_eb{sy}", (3.9, 0.08, 0.012), (0, sy * 1.92, 0.0), "#f4f7fa"))
    objs.append(bx("hc_pad", (0.5, 0.5, 0.012), (0.0, -1.2, 0.0), "#5fa8e6"))
    return [fin("floor_c", objs), fin("Ceiling", ceiling_hospital("hc", "round", seed=53))]


# ---------------------------------------------------------------- walls: core + four decorated face slabs

def base_trim(prefix, col=MINT_WAIN, rail=BLUE):
    return [bx(prefix + "wn", (3.86, 0.07, 1.0), (0, FACE_Y - 0.035, 0.5), col),
            bx(prefix + "wc", (3.86, 0.08, 0.06), (0, FACE_Y - 0.04, 1.0), BLUE_DK)]


def solid_slab(prefix, col, dark, hole=None):
    slab = slab_boxes(prefix, col, hole=hole)
    for o in slab:
        ao_paint(o, col, dark, band=0.42, corner=0.2)
    return slab


def handrail_line(prefix, x0, x1, z, depth=0.12):
    """Blue handrail along a wall face on brackets."""
    out = [blk(prefix + "hr", (x1 - x0, 0.1, 0.08), ((x0 + x1) / 2, B - 0.1, z), BLUE, bevel=0.02)]
    xs = [x0 + 0.1, (x0 + x1) / 2, x1 - 0.1]
    for i, x in enumerate(xs):
        out.append(bx(f"{prefix}br{i}", (0.05, 0.14, 0.06), (x, B - 0.05, z - 0.07), BLUE_DK))
    return out


def ward_face_a(k):
    """White ward wall face: mint wainscot, handrail, red-cross sign panel and a blue header band."""
    out = solid_slab(f"ha{k}s", WHITE, WHITE_DK)
    out += base_trim(f"ha{k}")
    out += handrail_line(f"ha{k}", -1.8, 1.8, 1.1)
    out.append(panel(f"ha{k}cp", -0.5, 0.5, 2.3, 3.1, B, WHITE, depth=0.06))
    out.append(bx(f"ha{k}cv", (0.14, 0.04, 0.5), (0, B - 0.07, 2.7), RED))
    out.append(bx(f"ha{k}ch", (0.5, 0.04, 0.14), (0, B - 0.07, 2.7), RED))
    out.append(bx(f"ha{k}top", (3.86, 0.08, 0.2), (0, B - 0.05, 4.12), BLUE_LT))
    return out


def wall_a():
    objs = wall_core("wa", WHITE, cap=WHITE_DK) + K.four_sides(ward_face_a)
    objs.append(bx("wa_light", (1.2, 0.25, 0.04), (0, 0, 4.52), "#fff9e0", "M_Emit"))
    return [fin("wall_a", objs)]


def ward_face(k):
    """Pastel ward curtains on a rail (kept from the first version, with a solid face slab underneath)."""
    out = solid_slab(f"wb{k}s", WHITE_DK, WHITE_DK)
    out.append(bx(f"wb{k}w", (3.86, 0.07, 1.0), (0, FACE_Y - 0.035, 0.5), WHITE_DK))
    out.append(bx(f"wb{k}rod", (3.86, 0.08, 0.08), (0, FACE_Y - 0.05, 3.3), METAL))
    cols = [PINK_CU, SKYC, LEMON, "#d8f5e9"]
    for i, (x0, x1) in enumerate(((-1.85, -0.6), (-0.6, 0.6), (0.6, 1.85))):
        out += curtain(f"wb{k}{i}", x0 + 0.02, x1 - 0.02, 1.05, 3.25, B, cols[(i + k) % 4])
    out.append(bx(f"wb{k}ph", (0.6, 0.02, 0.14), (0, B - 0.03, 2.2), BLUE_DK))
    return out


def curtain(prefix, x0, x1, z0, z1, y, col, folds=4, depth=0.08):
    """Pastel ward curtain: wavy-edged sheet hanging from a rail."""
    pts = [(x0, z1)]
    for k in range(folds * 2 + 1):
        x = x0 + (x1 - x0) * k / (folds * 2)
        pts.append((x, z0 + (0.12 if k % 2 else 0.0)))
    pts.append((x1, z1))
    return [pz(prefix + "c", pts, depth, axis="Y", loc=(0, y - depth / 2, 0), color=col)]


def wall_b():
    objs = wall_core("wbx", WHITE_DK, cap=WHITE_DK) + K.four_sides(ward_face)
    objs.append(bx("wbx_light", (1.2, 0.25, 0.04), (0, 0, 4.52), "#fff9e0", "M_Emit"))
    return [fin("wall_b", objs)]


def nurse_face(k):
    """Nurse hatch: a recess with a counter, a red-cross board on the back and a sign above."""
    out = solid_slab(f"nc{k}s", WHITE, WHITE_DK, hole=HOLE_NURSE)
    out += base_trim(f"nc{k}")
    out += frame_strips(f"nc{k}f", HOLE_NURSE, BLUE, w=0.09, depth=0.05)
    x0, x1, z0, z1 = HOLE_NURSE
    out.append(bx(f"nc{k}bk", (1.6, 0.03, 1.0), (0, CORE_Y0 - 0.02, 2.3), MINT_WAIN))
    out.append(bx(f"nc{k}rh", (0.36, 0.03, 0.1), (0, CORE_Y0 - 0.04, 2.6), RED))
    out.append(bx(f"nc{k}rv", (0.1, 0.03, 0.36), (0, CORE_Y0 - 0.04, 2.6), RED))
    out.append(bx(f"nc{k}ct", (1.7, 0.36, 0.78), (0, -1.66, 1.2 + 0.39), WHITE))
    out.append(bx(f"nc{k}cp", (1.8, 0.42, 0.05), (0, -1.66, 2.0), BLUE_LT))
    out.append(bx(f"nc{k}cd", (0.5, 0.02, 0.5), (0.4, -1.84, 1.6), BLUE_DK))
    out += sign(f"nc{k}sg", R(9000 + k), -0.9, 0.9, 3.2, 3.6, B, RED, WHITE, n=2, depth=0.05)
    return out


def wall_c():
    """Nurse station: a recessed hatch over a counter, with a red-cross sign above."""
    objs = wall_core("wcx", WHITE, cap=WHITE_DK) + K.four_sides(nurse_face)
    objs.append(bx("wcx_light", (1.2, 0.25, 0.04), (0, 0, 4.52), "#fff9e0", "M_Emit"))
    return [fin("wall_c", objs)]


# ---------------------------------------------------------------- overlays

def overlay_1():
    """Curtain rail and a pastel curtain hung from the top of a wall face."""
    out = [blk("o1rail", (3.6, 0.08, 0.08), (0, -2.1, 4.2), METAL, bevel=0.01)]
    out += curtain("o1c", -1.8, 1.8, 2.6, 4.12, -2.12, PINK_CU, folds=5, depth=0.06)
    out += [cy(f"o1h{i}", 0.02, 0.07, (x, -2.1, 4.25), METAL, seg=6) for i, x in enumerate((-1.6, -0.8, 0.0, 0.8, 1.6))]
    out += [ball(f"o1f{sx}", 0.05, (sx * 1.85, -2.12, 4.2), METAL, seg=6, rings=4) for sx in (-1, 1)]
    out += [bx(f"o1tie{i}", (0.1, 0.03, 0.5), (x, -2.14, 3.5), "#b9e7ff") for i, x in enumerate((-1.0, 1.0))]
    return [fin("overlay_1", out)]


def overlay_2():
    """Hanging ivy from the top of a wall face in mint and green."""
    r = R(10201)
    out = []
    for i in range(7):
        x = -1.75 + i * 0.58 + r.uniform(-0.05, 0.05)
        L = r.uniform(1.0, 2.0)
        pts = [(x, -2.08, 4.4), (x + r.uniform(-0.1, 0.1), -2.14, 4.4 - L * 0.5), (x + r.uniform(-0.15, 0.15), -2.2, 4.4 - L)]
        out.append(tube(f"o2v{i}", pts, 0.02, GREEN_DK, seg=3))
        for j in range(6):
            t = (j + 0.5) / 6
            lx = pts[0][0] + (pts[2][0] - pts[0][0]) * t
            lz = 4.4 - L * t
            side = 1 if j % 2 else -1
            out.append(ball(f"o2l{i}{j}", 0.1, (lx + side * 0.08, -2.17, lz), r.choice([GREEN, "#7bc96a", GREEN_DK]),
                            scale=(1.6, 0.35, 0.8), seg=6, rings=3))
    return [fin("overlay_2", out)]


# ---------------------------------------------------------------- decor

def decor_1():
    """Ward bed from the KayKit Furniture kit, made up with a mint blanket and a white pillow (0.9 x 1.9 m)."""
    o = [kfit("kf", "bed_single_A", (0.95, 1.9, 0.62), center=(0.0, 0.0), z0=0.0),
         bx("d1_bl", (0.9, 1.0, 0.08), (0.0, -0.35, 0.7), "#9fd8f0"),
         bx("d1_pl", (0.5, 0.3, 0.12), (0.0, 0.65, 0.72), WHITE)]
    return [fin("decor_1", o)]


# ---------------------------------------------------------------- arena: enclosed hospital lobby

def arena_builder():
    """Enclosed hospital lobby (pass 2): lobby pulled in to y -6..13.5 and x +-10 with a 5 m ceiling and recessed
    lights, tiled floor on a grout base (no glowing edges), reception counter with monitors and a cross sign,
    waiting chairs, two beds with privacy-curtain rails, IV stands, plants, a vending machine and a wheelchair."""
    floor = [bx("ar_fbase", (20.6, 19.2, 0.04), (0, 3.6, -0.05), "#8fbfb3")]   # grout base under the tiles
    for i in range(12):   # 1.6 m floor tiles, mint and white (top at z = 0), y -6..13.2
        for j in range(12):
            x0, y0 = -9.6 + i * 1.6, -6.0 + j * 1.6
            floor.append(bx(f"ar_t{i}_{j}", (1.56, 1.56, 0.04), (x0 + 0.8, y0 + 0.8, -0.02),
                            MINT[(i + j) % 3] if (i + j) % 2 else WHITE))
    floor.append(bx("ar_cr_h", (1.6, 0.25, 0.01), (0, 0, 0.005), RED))
    floor.append(bx("ar_cr_v", (0.25, 1.6, 0.01), (0, 0, 0.005), RED))
    back = []
    # closed walls: no bright window wall; side walls at x +-10.2, back wall front face at y 13.5, height 5 m
    back.append(bx("ar_wall", (20.8, 0.4, 5.0), (0, 13.7, 2.5), WHITE))
    back.append(bx("ar_base", (20.8, 0.44, 1.0), (0, 13.7, 0.5), MINT_WAIN))
    for sx in (-1, 1):
        back.append(bx(f"ar_sw{sx}", (0.4, 19.6, 5.0), (sx * 10.2, 3.6, 2.5), WHITE))
        back.append(bx(f"ar_sb{sx}", (0.44, 19.6, 1.0), (sx * 10.2, 3.6, 0.5), MINT_WAIN))
        for y in (-3.0, 4.0):
            back.append(bx(f"ar_wf{sx}{y}", (0.46, 0.5, 4.0), (sx * 10.22, y, 2.5), BLUE))
    back.append(bx("ar_ceil", (20.6, 19.6, 0.12), (0, 3.6, 5.0), CEIL_PANEL))
    for x in (-6.0, 0.0, 6.0):   # recessed lights in the 5 m ceiling
        for y in (-3.0, 2.0, 7.0, 11.0):
            back += round_lamp(f"ar_rl{x}{y}", x, y, 4.94, r=0.5)
    # reception counter (y 11.5..12.5) with two monitors and a cross sign on the back wall
    back.append(bx("ar_desk", (6.0, 1.0, 1.1), (0, 12.0, 0.55), WHITE))
    back.append(bx("ar_desk_t", (6.3, 1.2, 0.1), (0, 12.0, 1.15), BLUE_LT))
    for x in (-1.2, 1.2):
        back.append(bx(f"ar_mon_s{x}", (0.1, 0.1, 0.4), (x, 12.25, 1.35), METAL_DK))
        back.append(bx(f"ar_mon{x}", (0.9, 0.06, 0.55), (x, 12.25, 1.75), DARK))
        back.append(bx(f"ar_mon_e{x}", (0.8, 0.02, 0.45), (x, 12.2, 1.75), MINT_EM, "M_Emit"))
    back.append(bx("ar_sign", (1.6, 0.12, 1.6), (0, 13.35, 3.6), RED))
    back.append(bx("ar_sign_h", (1.1, 0.06, 0.35), (0, 13.27, 3.6), WHITE))
    back.append(bx("ar_sign_v", (0.35, 0.06, 1.1), (0, 13.27, 3.6), WHITE))
    # waiting chairs in rows at y 7.0 and 8.4, either side of the centre
    for y in (7.0, 8.4):
        for x in (-6.0, -4.5, -3.0, 3.0, 4.5, 6.0):
            back.append(kstand("kr", "chair_A", center=(x, y), z0=0.0, scale=1.0, rot_z=180))
    # two beds with a privacy-curtain rail (U-rail at z 2.9) and a curtain on the outer side
    for sx in (-1, 1):
        back.append(kfit("kf", "bed_single_A", (1.1, 2.3, 0.7), center=(sx * 7.2, 9.4), z0=0.0))
        back.append(bx(f"ar_blk{sx}", (1.0, 1.6, 0.12), (sx * 7.2, 9.2, 0.76), BLUE_LT))
        back.append(bx(f"ar_rh{sx}", (0.04, 2.6, 0.04), (sx * 8.2, 9.4, 2.9), METAL))
        back.append(bx(f"ar_rt{sx}", (1.9, 0.04, 0.04), (sx * 7.25, 8.1, 2.9), METAL))
        back.append(bx(f"ar_rb{sx}", (1.9, 0.04, 0.04), (sx * 7.25, 10.7, 2.9), METAL))
        back.append(bx(f"ar_cur{sx}", (0.04, 2.6, 2.4), (sx * 8.2, 9.4, 1.6), MINT_WAIN))
        # IV stand beside each bed
        back.append(cy(f"ar_ivp{sx}", 0.02, 1.9, (sx * 5.8, 9.4, 0.95), METAL, seg=6))
        back.append(cy(f"ar_ivb{sx}", 0.2, 0.04, (sx * 5.8, 9.4, 0.02), METAL_DK, seg=10))
        back.append(bx(f"ar_ivg{sx}", (0.2, 0.05, 0.34), (sx * 5.8, 9.4, 1.8), MINT_EM, "M_Clear"))
        back.append(kstand("kf", "cactus_medium_A", center=(sx * 9.2, 6.6), z0=0.0, scale=1.4))
    back.append(kfit("kf", "couch", (2.6, 1.2, 1.0), center=(0.0, 10.0), z0=0.0))
    # wheelchair beside the couch (built from boxes and discs)
    back.append(bx("ar_wc_s", (0.5, 0.5, 0.06), (2.6, 10.2, 0.5), BLUE_DK))
    back.append(bx("ar_wc_b", (0.5, 0.06, 0.6), (2.6, 10.45, 0.9), BLUE_DK))
    for x in (2.25, 2.95):
        back.append(cy(f"ar_wc_w{x}", 0.32, 0.05, (x, 10.2, 0.32), METAL_DK, rot=(0, 90, 0), seg=14))
    # vending machine and a plant in the back corners
    back.append(bx("ar_vend", (1.0, 0.8, 2.0), (8.8, 12.6, 1.0), RED))
    back.append(bx("ar_vend_w", (0.7, 0.03, 1.2), (8.8, 12.17, 1.3), MINT_EM, "M_Emit"))
    back.append(kstand("kf", "cactus_small_A", center=(-8.8, 12.3), z0=0.0, scale=1.6))
    for sx in (-1, 1):   # tall supply shelves either side of the counter (fill the upper frame)
        back.append(kstand("kf", "shelf_A_small", center=(sx * 4.6, 12.5), z0=0.0, scale=2.6, rot_z=0))
    return floor, back


def arena():
    return arena_scene(TS, arena_builder, ("#bfefff", "#6fb8d4"), WORLD)


def tiles2(prefix, rng, cols, gap=0.07, top=-0.012, n=2):
    out = []
    s = 4.0 / n
    for i in range(n):
        for j in range(n):
            x0, y0 = -2 + i * s, -2 + j * s
            out.append(K.poly_slab(f"{prefix}{i}{j}", rect_pts(x0, y0, x0 + s, y0 + s, gap / 2), top=top, thick=0.2,
                                   color=K.pick(rng, cols, 0.025), bevel=0.01, seed=rng.randint(0, 999)))
    return out


def grout(prefix, col="#8fbfb3"):
    return [bx(prefix + "g", (4.0, 4.0, 0.2), (0, 0, -0.13), col)]


def ward_leaf(w=2.3, h=3.25):
    x0, x1 = -w / 2 + 0.02, w / 2 - 0.02
    t = 0.09
    out = [blk("dw_p", (x1 - x0, t, h - 0.04), ((x0 + x1) / 2, 0, h / 2), WHITE, bevel=0.015),
           bx("dw_seam", (0.05, t + 0.02, h - 0.1), (0, 0, h / 2), WHITE_DK)]
    for xc in (-0.55, 0.55):
        out.append(ring(f"dw_rg{xc}", 0.2, 0.025, (xc, -t / 2 - 0.01, 2.3), BLUE, rot=(90, 0, 0), seg=18, minor=4))
        out.append(cy(f"dw_gl{xc}", 0.19, 0.02, (xc, -t / 2 - 0.005, 2.3), GLASS, rot=(90, 0, 0), mat="M_Clear", seg=18))
    out.append(bx("dw_push", (1.5, 0.05, 0.06), (0.0, -t / 2 - 0.03, 1.05), METAL))
    return out


def door():
    frame = door_frame("dd", WHITE, BLUE, w=2.3, h=3.25)
    return make_door("door", frame, ward_leaf(), 2.3)


def staff_leaf(w=2.3, h=3.25):
    x0, x1 = -w / 2 + 0.02, w / 2 - 0.02
    t = 0.1
    out = [blk("ds_p", (x1 - x0, t, h - 0.04), ((x0 + x1) / 2, 0, h / 2), "#7fa8c8", bevel=0.015),
           blk("ds_tr", (x1 - x0 - 0.1, t + 0.03, 0.08), ((x0 + x1) / 2, 0, h - 0.1), BLUE_DK, bevel=0.01)]
    out += sign("ds_sg", R(2003), -0.75, 0.75, 2.2, 2.6, -t / 2, DARK, WHITE, n=3, depth=0.03)
    out.append(ball("ds_kn", 0.05, (0.8, -t / 2 - 0.04, 1.15), METAL, seg=8, rings=4))
    return out


def door_locked():
    frame = door_frame("ddl", WHITE, BLUE, w=2.3, h=3.25)
    reader = [blk("lk_box", (0.22, 0.08, 0.32), (0.8, -0.14, 1.55), DARK, bevel=0.01),
              bx("lk_led", (0.05, 0.02, 0.05), (0.8, -0.19, 1.67), MINT_EM, "M_Emit")]
    return make_door("door_locked", frame, staff_leaf(), 2.3, lock_objs=reader)


def stairs_down():
    rng = R(3003)
    o = []
    regions = [(-2, -2, -1.3, 2), (1.3, -2, 2, 2), (-1.3, -2, 1.3, -1.4), (-1.3, 1.8, 1.3, 2)]
    for i, (x0, y0, x1, y1) in enumerate(regions):
        o.append(bx(f"sd_g{i}", (x1 - x0, y1 - y0, 0.2), ((x0 + x1) / 2, (y0 + y1) / 2, -0.13), "#8fbfb3"))
        o.append(K.poly_slab(f"sd_t{i}", rect_pts(x0, y0, x1, y1, 0.035), top=-0.012, thick=0.2,
                             color=K.pick(rng, MINT, 0.02), bevel=0.01))
    y0, y1, n, depth = -1.4, 1.8, 10, 2.6
    run, rise = (y1 - y0) / n, 0.24
    for i in range(n):
        top = -rise * (i + 1)
        o.append(blk(f"sd_st{i}", (2.6, run + 0.01, 0.2), (0, y0 + run * (i + 0.5), top - 0.1), "#e6edf0", bevel=0.02))
        o.append(bx(f"sd_nz{i}", (2.6, 0.05, 0.03), (0, y0 + run * i + 0.03, top + 0.005), MINT_DK))
    for sx in (-1, 1):
        o.append(bx(f"sd_w{sx}", (0.14, y1 - y0, depth), (sx * 1.33, (y0 + y1) / 2, -depth / 2), DARK))
        pts = [(sx * 1.22, y0 + run * j, -rise * j + 0.95) for j in range(n + 1)]
        o.append(tube(f"sd_rl{sx}", pts, 0.03, BLUE))
        o.append(cy(f"sd_rp{sx}", 0.035, 0.95, (sx * 1.22, y0, 0.47), METAL_DK, seg=6))
    o.append(bx("sd_bk", (2.6, 0.14, depth), (0, y1 + 0.07, -depth / 2), DARK))
    o.append(bx("sd_glow", (2.2, 0.04, 0.12), (0, y1 - 0.05, -depth + 0.4), "#c9fff0", "M_Emit"))
    return [fin("stairs_down", o)]


def stairs_up():
    o = []
    n, y0, y1, ztop = 9, -1.6, 1.4, 2.25
    run, rise = (y1 - y0) / n, ztop / n
    for i in range(n):
        top = rise * (i + 1)
        o.append(blk(f"su_st{i}", (2.36, run + 0.03, 0.18), (0, y0 + run * (i + 0.5), top - 0.09), "#e6edf0", bevel=0.02))
        o.append(bx(f"su_sr{i}", (2.3, run, top - 0.17), (0, y0 + run * (i + 0.5), (top - 0.17) / 2), WHITE_DK))
        o.append(bx(f"su_nz{i}", (2.36, 0.05, 0.03), (0, y0 + run * i + 0.03, top + 0.005), MINT_DK))
    o.append(blk("su_land", (2.4, 0.9, ztop), (0, 1.85, ztop / 2), "#e6edf0", bevel=0.03))
    for sx in (-1, 1):
        o.append(K.prism(f"su_sg{sx}", [(y0 - 0.05, 0), (y1, 0), (y1, ztop)], 0.14, axis="X",
                         loc=(sx * 1.22, 0, 0), color=WHITE_DK))
        pts = [(sx * 1.15, y0, rise * j + 0.95) for j in range(n + 1)] + [(sx * 1.15, 1.4, ztop + 0.95),
                                                                         (sx * 1.15, 2.3, ztop + 0.95)]
        o.append(tube(f"su_rl{sx}", pts, 0.03, BLUE))
        o.append(cy(f"su_np{sx}", 0.035, 0.95, (sx * 1.15, y0, 0.47), METAL_DK, seg=6))
    return [fin("stairs_up", o)]


def chest():
    W, D, H = 1.1, 0.72, 0.55
    body = [blk("cb_box", (W, D, H), (0, 0, H / 2), WHITE, bevel=0.03)]
    for sx in (-1, 1):
        body.append(bx(f"cb_bl{sx}", (0.1, D + 0.01, H + 0.01), (sx * 0.35, 0, H / 2), BLUE))
    body.append(bx("cb_cr", (0.26, 0.02, 0.26), (0, -D / 2 - 0.01, H * 0.55), RED))
    body.append(bx("cb_crv", (0.09, 0.03, 0.2), (0, -D / 2 - 0.02, H * 0.55), WHITE))
    for sx in (-1, 1):
        for sy in (-1, 1):
            body.append(blk(f"cb_cn{sx}{sy}", (0.14, 0.14, 0.14), (sx * (W / 2 - 0.02), sy * (D / 2 - 0.02), H / 2), METAL,
                            bevel=0.02))
    body.append(bx("cb_latch", (0.14, 0.05, 0.12), (0, -D / 2 - 0.03, H - 0.05), METAL))
    lid = [blk("cl_lid", (W + 0.04, D + 0.04, 0.12), (0, 0, H + 0.06), WHITE, bevel=0.03),
           bx("cl_bl0", (0.1, D + 0.05, 0.13), (-0.35, 0, H + 0.06), BLUE),
           bx("cl_bl1", (0.1, D + 0.05, 0.13), (0.35, 0, H + 0.06), BLUE),
           bx("cl_cr", (0.22, 0.02, 0.22), (0, -D / 2 - 0.03, H + 0.06), RED)]
    return [fin("chest", body), make_lid(lid, D, H)]


def lore_stone():
    """Patient information board: white chart with blue rules, red cross and mint runes."""
    r = R(5003)
    o = [cy("ls_p1", 0.05, 1.7, (-0.55, 0, 0.85), METAL_DK, seg=8), cy("ls_p2", 0.05, 1.7, (0.55, 0, 0.85), METAL_DK, seg=8),
         blk("ls_base", (1.2, 0.5, 0.1), (0, 0, 0.05), METAL_DK, bevel=0.02),
         blk("ls_fr", (1.5, 0.12, 1.3), (0, 0, 1.7), BLUE, bevel=0.03),
         bx("ls_ch", (1.3, 0.06, 1.1), (0, -0.07, 1.7), WHITE)]
    for i in range(4):
        o.append(bx(f"ls_ln{i}", (1.0 - 0.2 * (i % 2), 0.01, 0.04), (-0.05 - 0.05 * (i % 2), -0.11, 1.4 + i * 0.2), BLUE_LT))
    o.append(bx("ls_rh", (0.2, 0.02, 0.06), (0.45, -0.11, 1.95), RED))
    o.append(bx("ls_rv", (0.06, 0.02, 0.2), (0.45, -0.11, 1.95), RED))
    o += glyphs("ls_g", r, -0.5, 0.2, 2.25, 2.5, -0.1, MINT_EM, n=3, depth=0.02, mat="M_Emit")
    return [fin("lore_stone", o)]


def trap():
    """Floor plate with upright syringes (spikes): retracted 0.5 m below the tile."""
    plate = [blk("tr_fr", (3.5, 3.5, 0.06), (0, 0, 0.0), YELLOW, bevel=0.02),
             bx("tr_pl", (3.2, 3.2, 0.06), (0, 0, 0.01), PLATE)]
    for i, (x, y) in enumerate(SYRINGE_GRID):
        plate.append(K.ngon_disc(f"tr_h{i}", 0.1, z=0.042, n=8, loc=(x, y, 0), color="#c9d2d6"))
    plate = fin("trap", plate)
    sp = [bx("sp_base", (3.2, 3.2, 0.04), (0, 0, -0.03), METAL_DK)]
    for i, (x, y) in enumerate(SYRINGE_GRID):
        sp.append(cy(f"sp_b{i}", 0.05, 0.32, (x, y, 0.16), "#eafcff", mat="M_Clear", seg=6))
        sp.append(cy(f"sp_p{i}", 0.06, 0.08, (x, y, 0.36), RED, seg=6))
        sp.append(cone(f"sp_n{i}", 0.012, 0.16, (x, y, 0.4), METAL, seg=4))
    spikes = fin("Spikes", sp)
    spikes.location = (0, 0, -0.5)
    return [plate, spikes]


def spring():
    """Recovery corner: a made bed, an IV stand with a glowing drip bag and a mint healing ring."""
    o = [K.ring_strip("sp_ring", 1.25, 1.36, z=0.012, n=36, color=MINT_EM, mat="M_Emit")]
    o.append(blk("sp_bed", (1.8, 0.85, 0.14), (0, -0.5, 0.5), WHITE, bevel=0.03))
    o.append(blk("sp_mat", (1.7, 0.78, 0.12), (0, -0.5, 0.6), SOFT_BLUE, bevel=0.02))
    o.append(blk("sp_bl", (0.7, 0.8, 0.1), (0.4, -0.5, 0.68), "#8fd8c4", bevel=0.02))
    o.append(blk("sp_pl", (0.42, 0.5, 0.12), (-0.6, -0.5, 0.7), WHITE, bevel=0.03))
    for sx in (-1, 1):
        for sy in (-1, 1):
            o.append(cy(f"sp_lg{sx}{sy}", 0.03, 0.4, (sx * 0.8, -0.5 + sy * 0.3, 0.2), METAL_DK, seg=6))
    o.append(cy("sp_ivp", 0.02, 1.9, (-1.0, 0.8, 0.95), METAL, seg=6))
    o.append(cy("sp_ivb", 0.22, 0.04, (-1.0, 0.8, 0.02), METAL_DK, seg=10))
    o.append(blk("sp_ivg", (0.22, 0.06, 0.36), (-1.0, 0.8, 1.6), MINT_EM, mat="M_Emit", bevel=0.02))
    return [fin("spring", o)]


def warp():
    """Violet gate portal on a white dais."""
    o = [cy("wp_d0", 1.7, 0.14, (0, 0, 0.07), WHITE_DK, seg=24), cy("wp_d1", 1.45, 0.14, (0, 0, 0.21), SOFT_BLUE, seg=24),
         K.ring_strip("wp_r1", 1.15, 1.27, z=0.292, n=36, color=VIOLET_EM, mat="M_Emit")]
    for sx in (-1, 1):
        o.append(cy(f"wp_p{sx}", 0.1, 2.0, (sx * 0.95, 0, 1.0), "#4b3a7a", seg=8))
    o.append(ring("wp_gate", 1.02, 0.1, (0, 0, 2.0), VIOLET, rot=(90, 0, 0), mat="M_Emit", seg=32, minor=8))
    o.append(cy("wp_in", 0.9, 0.04, (0, 0, 2.0), VIOLET_EM, rot=(90, 0, 0), mat="M_Clear", seg=32))
    for i in range(3):
        a = 2 * math.pi * i / 3
        o.append(K.gem(f"wp_g{i}", 0.06, loc=(math.cos(a) * 1.4, math.sin(a) * 0.4, 1.3 + 0.3 * i), color=VIOLET_EM))
    return [fin("warp", o)]


def torch():
    """Warm reading lamp on a slim stand; LightAnchor at the bulb."""
    o = [blk("to_b", (0.42, 0.42, 0.08), (0, 0, 0.04), METAL_DK, bevel=0.02),
         cy("to_p", 0.03, 1.9, (0, 0, 1.0), METAL, seg=8),
         cy("to_sh", 0.18, 0.36, (0, 0, 2.15), CREAM, r2=0.3, seg=14),
         ball("to_bulb", 0.11, (0, 0, 2.0), WARM_EM, mat="M_Emit", seg=8, rings=5),
         cy("to_col", 0.06, 0.1, (0, 0, 0.5), METAL, seg=10),
         cy("to_knob", 0.05, 0.05, (0, 0, 1.6), METAL_DK, seg=8),
         cy("to_ring", 0.12, 0.03, (0, 0, 2.11), METAL_DK, seg=12)]
    lamp = fin("torch", o)
    return [lamp, K.empty("LightAnchor", loc=(0, 0, 2.0))]


def boss_gate():
    o = [blk("bg_pl0", (0.3, 0.6, 3.7), (-1.85, 0, 1.85), WHITE, bevel=0.03),
         blk("bg_pl1", (0.3, 0.6, 3.7), (1.85, 0, 1.85), WHITE, bevel=0.03),
         blk("bg_hd", (4.0, 0.6, 0.5), (0, 0, 3.4), WHITE, bevel=0.03),
         blk("bg_th", (3.7, 0.7, 0.06), (0, 0, 0.03), METAL_DK, bevel=0.01)]
    o += sign("bg_sg", R(2101), -0.9, 0.9, 3.5, 3.85, -0.3, RED, WHITE, n=2, depth=0.05)
    for sx in (-1, 1):
        xc = sx * 0.9
        o.append(blk(f"bg_lf{sx}", (1.72, 0.16, 3.1), (xc, 0, 1.55), "#bfe6f5", bevel=0.02))
        o.append(ring(f"bg_rg{sx}", 0.22, 0.03, (xc, -0.1, 2.2), BLUE, rot=(90, 0, 0), seg=18, minor=4))
        o.append(cy(f"bg_gl{sx}", 0.21, 0.02, (xc, -0.1, 2.2), GLASS, rot=(90, 0, 0), mat="M_Clear", seg=18))
        o.append(bx(f"bg_bar{sx}", (1.2, 0.07, 0.09), (xc, -0.12, 1.1), METAL))
        pts = [(xc - 0.6 + 0.2 * k, -0.11, min(0.25 + 0.5 * (k % 2) + 0.2 * k, 3.0)) for k in range(7)]
        o.append(tube(f"bg_crk{sx}", pts, 0.03, VIOLET_EM, mat="M_Emit"))
    o.append(bx("bg_glow", (2.8, 0.7, 0.02), (0, -0.4, 0.01), VIOLET_EM, "M_Emit"))
    return [fin("boss_gate", o)]


def decor_2():
    """IV stand with a drip bag, on a round base."""
    o = [cy("d2_b", 0.25, 0.04, (0, 0, 0.02), METAL_DK, seg=12), cy("d2_p", 0.02, 2.0, (0, 0, 1.02), METAL, seg=6),
         cy("d2_arm", 0.012, 0.3, (0, 0.12, 2.0), METAL, rot=(90, 0, 0), seg=4),
         blk("d2_bag", (0.22, 0.06, 0.36), (0, 0.22, 1.7), "#c9f5ec", mat="M_Clear", bevel=0.02),
         bx("d2_tub", (0.02, 0.02, 0.9), (0.0, 0.1, 1.0), "#e8fbff", mat="M_Clear"),
         blk("d2_bag2", (0.2, 0.05, 0.3), (0.0, -0.22, 1.45), "#f6fffd", mat="M_Clear", bevel=0.02),
         cy("d2_cl", 0.03, 0.04, (0, 0.12, 1.25), METAL, rot=(90, 0, 0), seg=8),
         cy("d2_hk", 0.09, 0.03, (0, 0.0, 2.02), METAL, seg=10)]
    return [fin("decor_2", o)]


def decor_3():
    """Wheelchair with big blue wheels and a footrest."""
    o = [blk("d3_seat", (0.5, 0.5, 0.06), (0, 0, 0.5), BLUE, bevel=0.02),
         blk("d3_back", (0.5, 0.06, 0.6), (0, 0.22, 0.8), BLUE, bevel=0.02),
         blk("d3_foot", (0.36, 0.3, 0.04), (0, -0.5, 0.2), METAL_DK, bevel=0.01),
         bx("d3_rim0", (0.04, 0.04, 0.8), (-0.3, 0.05, 0.6), METAL), bx("d3_rim1", (0.04, 0.04, 0.8), (0.3, 0.05, 0.6), METAL)]
    for sx in (-1, 1):
        o.append(ring(f"d3_w{sx}", 0.3, 0.035, (sx * 0.3, 0.05, 0.3), METAL_DK, rot=(0, 90, 0), seg=20, minor=4))
        o.append(cy(f"d3_cs{sx}", 0.02, 0.1, (sx * 0.3, -0.25, 0.1), METAL_DK, rot=(0, 0, 0), seg=4))
    return [fin("decor_3", o)]


def decor_4():
    """Medicine cart: three white shelves, bottles and a drawer."""
    o = [bx("d4_fr", (0.7, 0.45, 0.04), (0, 0, 0.1), METAL), bx("d4_post0", (0.04, 0.04, 0.9), (-0.33, 0.2, 0.55), METAL),
         bx("d4_post1", (0.04, 0.04, 0.9), (0.33, 0.2, 0.55), METAL)]
    for i, z in enumerate((0.28, 0.55, 0.82)):
        o.append(blk(f"d4_sh{i}", (0.7, 0.45, 0.04), (0, 0, z), WHITE, bevel=0.01))
    o.append(blk("d4_dr", (0.66, 0.44, 0.2), (0, -0.01, 0.42), BLUE_LT, bevel=0.02))
    for i, x in enumerate((-0.2, 0.0, 0.2)):
        o.append(cy(f"d4_bt{i}", 0.04, 0.14, (x, -0.08, 0.66), "#ffffff" if i else RED, seg=6))
    for sx in (-1, 1):
        for sy in (-1, 1):
            o.append(cy(f"d4_wh{sx}{sy}", 0.04, 0.04, (sx * 0.3, sy * 0.18, 0.04), DARK, rot=(90, 0, 0), seg=6))
    return [fin("decor_4", o)]


def decor_5():
    """Potted plant: white pot with a blue band and big mint-green leaves."""
    o = [cy("d5_pot", 0.22, 0.35, (0, 0, 0.175), WHITE, r2=0.18, seg=12), cy("d5_band", 0.23, 0.05, (0, 0, 0.3), BLUE_LT, seg=12)]
    for i, (x, y, s) in enumerate(((0, 0, 1.0), (0.18, -0.12, 0.7), (-0.2, 0.1, 0.8))):
        o.append(ball(f"d5_lf{i}", 0.3 * s, (x, y, 0.8 * s), GREEN, scale=(0.9, 0.9, 1.5), seg=8, rings=5))
        o.append(ball(f"d5_lm{i}", 0.2 * s, (x, y, 0.5 + 0.2 * s), "#7bc96a", scale=(1, 1, 1.4), seg=6, rings=4))
    return [fin("decor_5", o)]


def decor_6():
    """A-frame sign stand with a red cross and a 'wet floor' sign beside it."""
    o = []
    for sy, nm in ((-1, "f"), (1, "b")):
        o.append(blk(f"d6_{nm}", (0.6, 0.05, 0.9), (0, sy * 0.05, 0.5), WHITE, bevel=0.01, rot=(sy * 15, 0, 0)))
        o.append(bx(f"d6_{nm}ch", (0.22, 0.02, 0.06), (0, sy * 0.07 - 0.02, 0.5), RED, rot=(sy * 15, 0, 0)))
        o.append(bx(f"d6_{nm}cv", (0.06, 0.02, 0.22), (0, sy * 0.07 - 0.02, 0.5), RED, rot=(sy * 15, 0, 0)))
    o.append(bx("d6_wf", (0.35, 0.03, 0.5), (0.5, -0.25, 0.3), YELLOW, rot=(0, 0, 25)))
    o.append(bx("d6_wf2", (0.12, 0.04, 0.3), (0.5, -0.27, 0.3), DARK, rot=(0, 0, 25)))
    for sx in (-1, 1):  # splayed feet
        o.append(bx(f"d6_ft{sx}", (0.5, 0.06, 0.03), (0, sx * 0.1, 0.015), METAL_DK))
    o.append(cy("d6_pole", 0.02, 0.4, (0.5, -0.25, 0.1), METAL, seg=6))
    o.append(cy("d6_pb", 0.12, 0.02, (0.5, -0.25, 0.01), METAL_DK, seg=8))
    return [fin("decor_6", o)]


def foe_marker():
    """Floor marker for a foe: violet ring, six crystal shards and a floating gate crystal."""
    o = [K.ring_strip("fm_r0", 1.0, 1.12, z=0.02, n=32, color=VIOLET),
         K.ring_strip("fm_r1", 0.7, 0.76, z=0.02, n=32, color=VIOLET_EM)]
    o.append(K.prism("fm_st", K.star_pts(6, 0.66, 0.3), 0.012, axis="Z", loc=(0, 0, 0.02), color=VIOLET_EM, mat="M_Emit"))
    for i in range(6):
        a = 2 * math.pi * i / 6
        o.append(K.shard(f"fm_sp{i}", r=0.1, h=0.55, loc=(math.cos(a) * 1.2, math.sin(a) * 1.2, 0),
                         rot=(0, -25, math.degrees(a)), color=METAL_DK, seed=i))
    o.append(K.gem("fm_c", 0.3, loc=(0, 0, 2.0), color=VIOLET, mat="M_Emit", h=2.0, sides=6))
    return [fin("foe_marker", o)]


def corridor():
    """First-person ward corridor: DungeonWorld rules (torch 1.7 m, decor 1.45 m + 1 m, chest 1.3 m off the wall)."""
    plan = []
    for y in range(-1, 5):
        plan.append(("floor_a" if y % 2 else "floor_b", (0, y), 0, (0, 0, 0)))
    for y in range(-1, 6):
        for x in (-1, 1):
            plan.append((("wall_a", "wall_b", "wall_c")[(x * 7 + y * 3) % 3], (x, y), 0, (0, 0, 0)))
    plan.append(("wall_c", (0, 5), 0, (0, 0, 0)))
    plan += [
        ("torch", (0, 1), 90, (-1.7, 0, 0)), ("torch", (0, 3), -90, (1.7, 0, 0)),
        ("overlay_1", (-1, 1), 90, (0, 0, 0)), ("overlay_2", (1, 2), -90, (0, 0, 0)),
        ("overlay_1", (0, 5), 0, (0, 0, 0)),
        ("decor_1", (0, 2), 90, (-1.45, 1.0, 0)), ("decor_5", (0, 4), -90, (1.45, -1.0, 0)),
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
    ("decor_1", (1.3, 2.25), 0), ("decor_3", (3.3, 2.6), 0), ("decor_5", (1.3, 1.7), 40), ("decor_6", (2.6, 3.3), 0),
    ("decor_2", (3.25, 1.35), 0), ("decor_4", (2.0, 3.35), 0), ("foe_marker", (1.0, 3.0), 0),
    ("overlay_1", (1, 4), 0), ("overlay_2", (3, 4), 0), ("overlay_1", (0, 2), 90), ("overlay_2", (4, 3), -90),
]


def main():
    publish(TS, PIECES, LAYOUT, EXTRAS, WORLD, corridor, arena)


if __name__ == "__main__":
    main()
