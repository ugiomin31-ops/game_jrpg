"""school tileset: Korean high school on festival night after a gate break (hunter theme, zone 7).

Linoleum and classroom wood floors, lockers / classroom-door / notice-board walls with paper garlands and
festival banners, desks, chalkboard, festival booth, nurse corner, gym double doors, gym arena.
"""
import math

from common_b import (R, blk, bx, cy, cone, ball, lathe, pz, ring, tube, fin, face_y, panel, sign, glyphs,
                      garland, door_frame, make_door, make_lid, publish, rect_pts, arena_scene, FACE_Y)
import _kit_common_b as K  # noqa: E402

TS = "school"
WORLD = "#1d2430"
B = FACE_Y + 0.01            # back plane of wall details (they stand out toward -Y)

CREAM = "#efe4cc"; CREAM_DK = "#d8c9a6"
LINO = ["#dfe9ec", "#d3e1e6", "#cad9de"]; GROUT = "#7f98a0"
BLUE = "#4f8fd6"; BLUE_DK = "#2d64a3"; SKY = "#7fb8d8"; BLUE_B = "#5fa8e6"
TEAL = "#3fb8a8"; RED = "#e5534b"; RED_DK = "#a93a35"
YELLOW = "#ffd24a"; YELLOW_DK = "#d9a52b"; ORANGE = "#ff9a3c"
PINK = "#ff8fb1"; MINT = "#7fe0c4"; VIOLET = "#9d6bff"; VIOLET_EM = "#c7a8ff"
METAL = "#a3afba"; METAL_DK = "#5d6a76"; WOOD = "#c58a52"; WOOD_LT = "#e2aa70"; WOOD_DK = "#8a5632"
CHALK = "#2f5f4f"; CORK = "#c99a62"; WHITE = "#fbfbf6"; GLASS = "#c9efff"; DARK = "#2a3440"
LANTERN = "#ff6a4a"; LANTERN_EM = "#ffc27a"; CLAY = "#c8733e"; GREEN = "#4fa35a"; GREEN_DK = "#2f7a40"
SOIL = "#4a3426"; GREY = "#b8c0c7"; STEP = "#c9d6dc"; CONFETTI = [PINK, YELLOW, "#6fd3ff", MINT, WHITE, ORANGE]


# ---------------------------------------------------------------- floors (flush; floor top z = 0)

def grout_base(prefix, color=GROUT):
    return [bx(prefix + "g", (4.0, 4.0, 0.2), (0, 0, -0.13), color)]


def tiles2(prefix, rng, cols, gap=0.07, top=-0.012, n=2):
    out = []
    s = 4.0 / n
    for i in range(n):
        for j in range(n):
            x0, y0 = -2 + i * s, -2 + j * s
            out.append(K.poly_slab(f"{prefix}{i}{j}", rect_pts(x0, y0, x0 + s, y0 + s, gap / 2), top=top, thick=0.2,
                                   color=K.pick(rng, cols, 0.03), bevel=0.01, seed=rng.randint(0, 999)))
    return out


def floor_a():
    """Linoleum corridor tiles with blue safety stripes on both sides, a floor drain and scuff marks."""
    rng = R(11)
    objs = grout_base("fa") + tiles2("fa_t", rng, LINO)
    for sx in (-1, 1):
        objs.append(bx(f"fa_s{sx}", (0.14, 4.0, 0.02), (sx * 1.7, 0, -0.01), BLUE))
    for i in range(5):
        x, y = rng.uniform(-1.3, 1.3), rng.uniform(-1.5, 1.5)
        k = rng.uniform(0.25, 0.45)
        pts = [(x + k * math.cos(math.tau * j / 7) * rng.uniform(0.7, 1.2), y + k * 0.6 * math.sin(math.tau * j / 7))
               for j in range(7)]
        objs.append(K.poly_slab(f"fa_sc{i}", pts, top=-0.008, thick=0.012, color="#c3d2d8", bevel=0.0))
    objs.append(bx("fa_drain", (0.5, 0.5, 0.02), (0.0, -1.0, -0.005), METAL_DK))
    for j in range(4):
        objs.append(bx(f"fa_dg{j}", (0.44, 0.04, 0.03), (0.0, -1.0 - 0.2 + 0.13 * j, 0.0), DARK))
    return [fin("floor_a", objs)]


def floor_b():
    """Classroom wood floor: five planks running along the corridor, each cut in two."""
    rng = R(22)
    objs = grout_base("fb", "#5a3d28")
    cols = ["#c98a52", "#b97840", "#d39a5f", "#c2864d"]
    for i in range(5):
        x0 = -2 + 0.8 * i
        cut = rng.uniform(-1.3, 1.3)
        for j, (y0, y1) in enumerate(((-2.0, cut), (cut, 2.0))):
            objs.append(K.poly_slab(f"fb_p{i}{j}", rect_pts(x0, y0, x0 + 0.8, y1, 0.012), top=-0.012, thick=0.2,
                                    color=K.pick(rng, cols, 0.05), bevel=0.008, seed=rng.randint(0, 999)))
    return [fin("floor_b", objs)]


def floor_c():
    """Linoleum with festival confetti and torn paper scattered flush on the tiles."""
    rng = R(33)
    objs = grout_base("fc") + tiles2("fc_t", rng, LINO)
    for i in range(26):
        x, y = rng.uniform(-1.85, 1.85), rng.uniform(-1.85, 1.85)
        a, w = rng.uniform(0, math.tau), rng.uniform(0.1, 0.2)
        c, s = math.cos(a), math.sin(a)
        pts = [(x + u * c - v * s, y + u * s + v * c) for (u, v) in
               ((-w / 2, -w / 4), (w / 2, -w / 3), (w / 2, w / 4), (-w / 2, w / 3))]
        objs.append(K.poly_slab(f"fc_c{i}", pts, top=0.004, thick=0.02, color=rng.choice(CONFETTI), bevel=0.0))
    return [fin("floor_c", objs)]


# ---------------------------------------------------------------- walls (4 faces decorated, top trim)

def shell(prefix, col, s=3.86, h=4.42):
    return [blk(prefix + "core", (s, s, h), (0, 0, h / 2), col, bevel=0.02),
            blk(prefix + "cap", (3.96, 3.96, 0.08), (0, 0, 4.46), CREAM_DK, bevel=0.012)]


def wainscot(prefix, col, rail, h=1.0):
    return [blk(prefix + "w", (3.9, 0.08, h), (0, B - 0.04, h / 2), col, bevel=0.01),
            blk(prefix + "r", (3.92, 0.12, 0.1), (0, B - 0.06, h + 0.05), rail, bevel=0.01)]


def lockers_face(k):
    r = R(100 + k)
    d = 0.1
    front = B - d
    out = wainscot(f"la{k}", SKY, BLUE_DK)
    out.append(blk(f"la{k}top", (3.9, 0.1, 0.2), (0, B - 0.05, 4.1), BLUE_DK, bevel=0.01))
    cols = [BLUE, BLUE_B, TEAL, BLUE]
    for i, xc in enumerate((-1.56, -0.52, 0.52, 1.56)):
        col = cols[(i + k) % len(cols)]
        out.append(blk(f"la{k}{i}", (0.84, d, 2.75), (xc, B - d / 2, 2.575), col, bevel=0.015))
        for j in range(3):
            out.append(bx(f"la{k}{i}v{j}", (0.46, 0.02, 0.05), (xc - 0.05, front + 0.004, 3.5 - j * 0.12), DARK))
        out.append(bx(f"la{k}{i}h", (0.05, 0.03, 0.32), (xc + 0.3, front - 0.01, 2.35), METAL))
        out.append(bx(f"la{k}{i}n", (0.24, 0.02, 0.14), (xc, front - 0.01, 3.2 + r.uniform(-0.02, 0.02)), WHITE))
    return out


def wall_a():
    objs = shell("wa", CREAM)
    objs += K.four_sides(lockers_face)
    objs.append(bx("wa_light", (1.2, 0.25, 0.04), (0, 0, 4.52), "#fff6d6", "M_Emit"))
    return [fin("wall_a", objs)]


def classroom_face(k):
    out = wainscot(f"cb{k}", CREAM_DK, TEAL, h=0.9)
    d = 0.1
    fy = B - d / 2
    out.append(blk(f"cb{k}hd", (2.24, d, 0.14), (0, fy, 3.35), BLUE_DK, bevel=0.012))
    out.append(blk(f"cb{k}sl", (2.24, d, 0.12), (0, fy, 1.0), BLUE_DK, bevel=0.012))
    for x in (-1.05, 1.05):
        out.append(blk(f"cb{k}st{x}", (0.14, d, 2.35), (x, fy, 2.2), BLUE_DK, bevel=0.012))
    out.append(bx(f"cb{k}gl", (1.0, 0.03, 2.15), (-0.5, B - 0.02, 2.17), GLASS, "M_Clear"))
    out.append(bx(f"cb{k}gr", (1.0, 0.03, 2.15), (0.5, B - 0.02, 2.17), GLASS, "M_Clear"))
    for x in (-0.12, 0.12):
        out.append(bx(f"cb{k}hn{x}", (0.04, 0.06, 0.7), (x, B - 0.08, 1.9), METAL))
    for sx in (-1, 1):   # side windows with mullion frames
        xc = sx * 1.52
        out.append(blk(f"cb{k}wf{sx}", (0.66, d, 1.9), (xc, fy, 2.2), BLUE_DK, bevel=0.012))
        out.append(bx(f"cb{k}wg{sx}", (0.5, 0.03, 1.74), (xc, B - 0.02, 2.2), GLASS, "M_Clear"))
    out += sign(f"cb{k}sg", R(200 + k), -1.85, -1.2, 3.5, 3.9, B, WHITE, BLUE_DK, n=2, depth=0.05)
    return out


def wall_b():
    objs = shell("wb", CREAM)
    objs += K.four_sides(classroom_face)
    objs.append(bx("wb_light", (1.2, 0.25, 0.04), (0, 0, 4.52), "#fff6d6", "M_Emit"))
    return [fin("wall_b", objs)]


def notice_face(k):
    r = R(300 + k)
    out = wainscot(f"nb{k}", CREAM_DK, TEAL, h=1.0)
    out.append(panel(f"nb{k}cf", -1.75, 0.05, 1.35, 3.15, B, CORK, depth=0.06))
    for nm, (a, b_, c, d_) in (("l", (-1.79, -1.71, 1.3, 3.2)), ("r", (0.01, 0.09, 1.3, 3.2)),
                               ("b", (-1.79, 0.09, 1.3, 1.38)), ("t", (-1.79, 0.09, 3.12, 3.2))):
        out.append(panel(f"nb{k}f{nm}", a, b_, c, d_, B - 0.055, WOOD_DK, depth=0.02))
    for i in range(6):
        x, z = r.uniform(-1.6, -0.1), r.uniform(1.5, 3.0)
        out.append(bx(f"nb{k}p{i}", (0.3, 0.01, 0.34), (x, B - 0.07, z), r.choice([WHITE, "#fff0a8", "#c8f0e0", PINK]),
                      rot=(0, r.uniform(-14, 14), 0)))
        if i < 3:
            out.append(ball(f"nb{k}pin{i}", 0.022, (x, B - 0.08, z + 0.15), RED, seg=5, rings=3))
    out += sign(f"nb{k}p1", r, 0.3, 1.0, 1.9, 2.9, B, PINK, WHITE, n=2, depth=0.04)
    out += sign(f"nb{k}p2", r, 1.12, 1.8, 1.9, 2.7, B, MINT, BLUE_DK, n=2, depth=0.04)
    out += garland(f"nb{k}g", -1.85, 1.85, (3.95, 3.95), 0.25, B - 0.02, 7, [RED, YELLOW, BLUE, MINT, PINK],
                   flag_w=0.2, flag_h=0.26, seg=10)
    return out


def wall_c():
    objs = shell("wc", CREAM)
    objs += K.four_sides(notice_face)
    objs.append(bx("wc_light", (1.2, 0.25, 0.04), (0, 0, 4.52), "#fff6d6", "M_Emit"))
    return [fin("wall_c", objs)]


# ---------------------------------------------------------------- overlays (hang on a wall face, reach to -2.3)

def overlay_1():
    """Festival garland with paper lanterns draped along a wall face."""
    r = R(10101)
    y = -2.04
    out = garland("o1g", -1.9, 1.9, (4.3, 4.3), 0.4, y, 9, [RED, YELLOW, MINT, PINK, BLUE], flag_w=0.16, flag_h=0.22)
    for i, x in enumerate((-1.2, 0.0, 1.2)):
        zs = 4.3 - 0.4 * 4 * ((x + 1.9) / 3.8) * (1 - (x + 1.9) / 3.8)
        out.append(cy(f"o1c{i}", 0.006, 0.2, (x, y - 0.1, zs - 0.12), DARK))
        out.append(ball(f"o1l{i}", 0.17, (x, y - 0.14, zs - 0.42), LANTERN, scale=(1, 0.9, 1.2), seg=10, rings=6))
        out.append(ball(f"o1i{i}", 0.13, (x, y - 0.17, zs - 0.42), LANTERN_EM, mat="M_Emit", scale=(1, 0.9, 1.15),
                        seg=8, rings=5))
        out.append(cy(f"o1k{i}", 0.05, 0.05, (x, y - 0.14, zs - 0.12), YELLOW_DK, seg=8))
    return [fin("overlay_1", out)]


def overlay_2():
    """Two hanging festival banners from a bamboo pole, with hangul-like calligraphy."""
    r = R(10201)
    out = []
    for i, (x, col) in enumerate(((-0.75, RED), (0.75, BLUE_DK))):
        y = -2.12
        out.append(tube(f"o2p{i}", [(x - 0.45, y + 0.06, 4.28), (x + 0.45, y + 0.06, 4.28)], 0.03, WOOD_DK))
        out.append(pz(f"o2b{i}", [(-0.36, 0.0), (0.36, 0.0), (0.36, -1.9), (0.0, -1.66), (-0.36, -1.9)], 0.04,
                      axis="Y", loc=(x, y, 4.28), color=col))
        out.append(bx(f"o2s{i}", (0.6, 0.04, 0.1), (x, y - 0.03, 4.1), YELLOW))
        out += glyphs(f"o2g{i}", r, x - 0.22, x + 0.22, 2.9, 3.85, y - 0.04, WHITE, n=2, depth=0.02)
    return [fin("overlay_2", out)]


# ---------------------------------------------------------------- doors

def sliding_leaf(w=2.3, h=3.25):
    """Classroom sliding door: wood rails, two glass panes, handle and room sign."""
    r = R(2001)
    x0, x1 = -w / 2 + 0.02, w / 2 - 0.02
    t = 0.08
    out = [blk("dl_sl", (0.1, t, h - 0.04), (x0 + 0.05, 0, h / 2), WOOD_LT, bevel=0.015),
           blk("dl_sr", (0.1, t, h - 0.04), (x1 - 0.05, 0, h / 2), WOOD_LT, bevel=0.015),
           blk("dl_tr", (x1 - x0, t, 0.1), (0, 0, h - 0.07), WOOD_LT, bevel=0.015),
           blk("dl_br", (x1 - x0, t, 0.14), (0, 0, 0.07), WOOD_LT, bevel=0.015),
           blk("dl_mid", (0.08, t, h - 0.3), (0, 0, h / 2), WOOD, bevel=0.01)]
    for nm, xc in (("a", -0.55), ("b", 0.55)):
        out.append(bx(f"dl_g{nm}", (0.9, 0.03, h - 0.45), (xc, 0.0, h / 2 - 0.02), GLASS, "M_Clear"))
    out.append(bx("dl_hd", (0.05, 0.08, 0.6), (0.7, -t / 2 - 0.02, 1.45), METAL))
    out += sign("dl_sg", r, -0.55, 0.55, h - 0.5, h - 0.14, -t / 2, WHITE, BLUE_DK, n=2, depth=0.02)
    return out


def hinged_door_leaf(w=2.3, h=3.25):
    """Teachers' office door: solid wood, small window, sign plate."""
    r = R(2002)
    x0, x1 = -w / 2 + 0.02, w / 2 - 0.02
    t = 0.1
    out = [blk("dh_pn", (x1 - x0, t, h - 0.04), ((x0 + x1) / 2, 0, h / 2), WOOD, bevel=0.015),
           blk("dh_tr", (x1 - x0 - 0.1, t + 0.03, 0.08), ((x0 + x1) / 2, 0, h - 0.1), WOOD_DK, bevel=0.01),
           bx("dh_win", (0.7, 0.03, 0.5), (-0.1, -t / 2, 2.55), GLASS, "M_Clear")]
    out += sign("dh_sg", r, -0.6, 0.6, 1.95, 2.35, -t / 2, WHITE, BLUE_DK, n=3, depth=0.03)
    out.append(ball("dh_kn", 0.05, (0.8, -t / 2 - 0.04, 1.15), METAL, seg=8, rings=4))
    return out


def door():
    frame = door_frame("dd", CREAM, BLUE_DK, w=2.3, h=3.25)
    return make_door("door", frame, sliding_leaf(), 2.3)


def door_locked():
    frame = door_frame("ddl", CREAM, BLUE_DK, w=2.3, h=3.25)
    lock = [bx("lk_hasp", (0.22, 0.04, 0.26), (0.8, -0.13, 1.5), METAL_DK),
            blk("lk_pad", (0.3, 0.14, 0.32), (0.8, -0.19, 1.2), YELLOW_DK, bevel=0.02),
            ring("lk_sh", 0.09, 0.022, (0.8, -0.19, 1.45), METAL, rot=(90, 0, 0), seg=16, minor=4)]
    return make_door("door_locked", frame, hinged_door_leaf(), 2.3, lock_objs=lock)


# ---------------------------------------------------------------- stairs

def stairs_down():
    rng = R(3001)
    o = []
    regions = [(-2, -2, -1.3, 2), (1.3, -2, 2, 2), (-1.3, -2, 1.3, -1.4), (-1.3, 1.8, 1.3, 2)]
    for i, (x0, y0, x1, y1) in enumerate(regions):
        o.append(bx(f"sd_g{i}", (x1 - x0, y1 - y0, 0.2), ((x0 + x1) / 2, (y0 + y1) / 2, -0.13), GROUT))
        o.append(K.poly_slab(f"sd_t{i}", rect_pts(x0, y0, x1, y1, 0.035), top=-0.012, thick=0.2,
                             color=K.pick(rng, LINO, 0.02), bevel=0.01))
    # handrail posts flank the opening
    y0, y1, n, depth = -1.4, 1.8, 10, 2.6
    run, rise = (y1 - y0) / n, 0.24
    for i in range(n):
        top = -rise * (i + 1)
        yc = y0 + run * (i + 0.5)
        o.append(blk(f"sd_st{i}", (2.6, run + 0.01, 0.2), (0, yc, top - 0.1), STEP, bevel=0.02))
        o.append(bx(f"sd_nz{i}", (2.6, 0.05, 0.03), (0, y0 + run * i + 0.03, top + 0.005), YELLOW))
    for sx in (-1, 1):
        o.append(bx(f"sd_w{sx}", (0.14, y1 - y0, depth), (sx * 1.33, (y0 + y1) / 2, -depth / 2), DARK))
        pts = [(sx * 1.22, y0 + run * j, -rise * j + 0.95) for j in range(n + 1)]
        o.append(tube(f"sd_rl{sx}", pts, 0.03, BLUE_DK))
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
        yc = y0 + run * (i + 0.5)
        o.append(blk(f"su_st{i}", (2.36, run + 0.03, 0.18), (0, yc, top - 0.09), STEP, bevel=0.02))
        o.append(bx(f"su_sr{i}", (2.3, run, top - 0.17), (0, yc, (top - 0.17) / 2), CREAM_DK))
        o.append(bx(f"su_nz{i}", (2.36, 0.05, 0.03), (0, y0 + run * i + 0.03, top + 0.005), YELLOW))
    o.append(blk("su_land", (2.4, 0.9, ztop), (0, 1.85, ztop / 2), STEP, bevel=0.03))
    for sx in (-1, 1):
        o.append(K.prism(f"su_sg{sx}", [(y0 - 0.05, 0), (y1, 0), (y1, ztop)], 0.14, axis="X",
                         loc=(sx * 1.22, 0, 0), color=CREAM_DK))
        pts = [(sx * 1.15, y0, rise * j + 0.95) for j in range(n + 1)] + [(sx * 1.15, 1.4, ztop + 0.95),
                                                                         (sx * 1.15, 2.3, ztop + 0.95)]
        o.append(tube(f"su_rl{sx}", pts, 0.03, BLUE))
        o.append(cy(f"su_np{sx}", 0.035, 0.95, (sx * 1.15, y0, 0.47), METAL_DK, seg=6))
        o.append(cy(f"su_nq{sx}", 0.035, 0.95, (sx * 1.15, 2.3, ztop + 0.47), METAL_DK, seg=6))
    return [fin("stairs_up", o)]


# ---------------------------------------------------------------- chest / lore / trap / spring / warp / torch

def chest():
    W, D, H = 1.1, 0.72, 0.55
    body = [blk("cb_box", (W, D, H), (0, 0, H / 2), RED, bevel=0.03)]
    body.append(bx("cb_rv", (0.16, D + 0.01, H + 0.005), (0, 0, H / 2), YELLOW))
    body.append(bx("cb_belt", (W + 0.01, D + 0.01, 0.12), (0, 0, H * 0.7), YELLOW_DK))
    for sx in (-1, 1):
        for sy in (-1, 1):
            body.append(blk(f"cb_c{sx}{sy}", (0.14, 0.14, 0.14), (sx * (W / 2 - 0.02), sy * (D / 2 - 0.02), H / 2),
                            YELLOW_DK, bevel=0.02))
    lid = [blk("cl_lid", (W + 0.04, D + 0.04, 0.12), (0, 0, H + 0.06), RED, bevel=0.03),
           bx("cl_rv", (0.16, D + 0.05, 0.13), (0, 0, H + 0.06), YELLOW),
           ball("cl_knot", 0.05, (0, 0, H + 0.16), YELLOW, seg=8, rings=5)]
    for sx in (-1, 1):
        lid.append(ring(f"cl_bow{sx}", 0.1, 0.03, (sx * 0.1, 0, H + 0.2), YELLOW, rot=(90, 0, 0), seg=16, minor=5))
    return [fin("chest", body), make_lid(lid, D, H)]


def lore_stone():
    """Campus notice board: wooden frame, cork face, pinned notices and violet runes across the top."""
    r = R(5001)
    o = [cy("ls_p1", 0.05, 1.7, (-0.55, 0, 0.85), METAL_DK, seg=8), cy("ls_p2", 0.05, 1.7, (0.55, 0, 0.85), METAL_DK, seg=8),
         blk("ls_base", (1.2, 0.5, 0.1), (0, 0, 0.05), METAL_DK, bevel=0.02),
         blk("ls_fr", (1.5, 0.12, 1.3), (0, 0, 1.7), WOOD_DK, bevel=0.03),
         bx("ls_cork", (1.3, 0.06, 1.1), (0, -0.07, 1.7), CORK)]
    for i, (x, z, col) in enumerate(((-0.35, 1.9, WHITE), (0.3, 1.85, PINK), (-0.3, 1.25, YELLOW), (0.32, 1.3, MINT))):
        o.append(bx(f"ls_n{i}", (0.3, 0.01, 0.34), (x, -0.105, z), col, rot=(0, r.uniform(-12, 12), 0)))
    o += glyphs("ls_g", r, -0.5, 0.5, 2.25, 2.5, -0.1, VIOLET_EM, n=4, depth=0.02, mat="M_Emit")
    return [fin("lore_stone", o)]


SPIKE_GRID = [(-1.05 + 0.7 * i, -1.05 + 0.7 * j) for i in range(3) for j in range(3)]


def trap():
    plate = [blk("tr_fr", (3.5, 3.5, 0.06), (0, 0, 0.0), YELLOW, bevel=0.02),
             bx("tr_pl", (3.2, 3.2, 0.06), (0, 0, 0.01), "#f3f0e6")]
    for i, (x, y) in enumerate(SPIKE_GRID):
        plate.append(K.ngon_disc(f"tr_h{i}", 0.1, z=0.042, n=8, loc=(x, y, 0), color=GREY))
    plate = fin("trap", plate)
    sp = [bx("sp_base", (3.2, 3.2, 0.04), (0, 0, -0.03), METAL_DK)]
    for i, (x, y) in enumerate(SPIKE_GRID):
        sp.append(cone(f"sp_c{i}", 0.05, 0.36, (x, y, 0.18), METAL, seg=6))
        sp.append(ball(f"sp_h{i}", 0.09, (x, y, 0.4), RED, seg=6, rings=4))
    spikes = fin("Spikes", sp)
    spikes.location = (0, 0, -0.5)
    return [plate, spikes]


def spring():
    """Nurse corner: cot, first-aid cabinet, water cooler and a mint healing ring on the floor."""
    o = [K.ring_strip("sp_ring", 1.25, 1.36, z=0.012, n=36, color=MINT, mat="M_Emit")]
    o.append(blk("sp_cf", (1.9, 0.8, 0.12), (0, -0.7, 0.42), WHITE, bevel=0.02))
    for sx in (-1, 1):
        for sy in (-1, 1):
            o.append(cy(f"sp_leg{sx}{sy}", 0.03, 0.4, (sx * 0.85, -0.7 + sy * 0.32, 0.2), METAL_DK, seg=6))
    o.append(blk("sp_mt", (1.82, 0.74, 0.14), (0, -0.7, 0.55), "#bfe3ff", bevel=0.02))
    o.append(blk("sp_bl", (1.0, 0.76, 0.1), (0.35, -0.7, 0.66), MINT, bevel=0.02))
    o.append(blk("sp_pl", (0.42, 0.56, 0.12), (-0.6, -0.7, 0.68), WHITE, bevel=0.03))
    o.append(blk("sp_cab", (0.7, 0.36, 1.05), (0.9, 0.9, 0.525), WHITE, bevel=0.02))
    o.append(bx("sp_crh", (0.36, 0.02, 0.1), (0.9, 0.7, 0.9), RED))
    o.append(bx("sp_crv", (0.1, 0.02, 0.36), (0.9, 0.7, 0.9), RED))
    o.append(cy("sp_cool", 0.2, 0.7, (-1.1, 0.9, 0.35), WHITE, seg=10))
    o.append(cy("sp_bot", 0.17, 0.42, (-1.1, 0.9, 1.12), "#9ee6ff", mat="M_Clear", seg=10))
    o.append(bx("sp_tap", (0.08, 0.06, 0.04), (-1.1, 0.68, 0.7), METAL))
    return [fin("spring", o)]


def warp():
    """Violet gate portal: stone dais, rune ring and a standing oval gate."""
    o = [cy("wp_d0", 1.7, 0.14, (0, 0, 0.07), "#d6c7a8", seg=24), cy("wp_d1", 1.45, 0.14, (0, 0, 0.21), GREY, seg=24),
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
    """Festival paper lantern on a school pole; LightAnchor sits inside the lantern."""
    o = [blk("to_b", (0.5, 0.5, 0.1), (0, 0, 0.05), METAL_DK, bevel=0.02), cy("to_p", 0.035, 1.9, (0, 0, 1.0), METAL, seg=8),
         ball("to_l", 0.3, (0, 0, 2.25), LANTERN, scale=(1, 1, 1.2), seg=12, rings=8),
         ball("to_c", 0.24, (0, 0, 2.25), LANTERN_EM, mat="M_Emit", scale=(1, 1, 1.15), seg=10, rings=6),
         cy("to_cap", 0.1, 0.08, (0, 0, 2.58), RED_DK, seg=10)]
    for z in (2.0, 2.25, 2.5):
        o.append(ring(f"to_rb{z}", 0.3, 0.018, (0, 0, z), RED_DK, seg=20, minor=4))
    lamp = fin("torch", o)
    anchor = K.empty("LightAnchor", loc=(0, 0, 2.25))
    return [lamp, anchor]


# ---------------------------------------------------------------- boss gate: gymnasium double doors with violet crack

def boss_gate():
    o = [blk("bg_pl0", (0.3, 0.6, 3.7), (-1.85, 0, 1.85), CREAM, bevel=0.03),
         blk("bg_pl1", (0.3, 0.6, 3.7), (1.85, 0, 1.85), CREAM, bevel=0.03),
         blk("bg_hd", (4.0, 0.6, 0.5), (0, 0, 3.4), CREAM, bevel=0.03),
         blk("bg_th", (3.7, 0.7, 0.06), (0, 0, 0.03), METAL_DK, bevel=0.01)]
    o += sign("bg_sg", R(2101), -0.9, 0.9, 3.5, 3.85, -0.3, GREEN, WHITE, n=3, depth=0.05)
    for sx in (-1, 1):
        xc = sx * 0.9
        o.append(blk(f"bg_lf{sx}", (1.72, 0.16, 3.1), (xc, 0, 1.55), BLUE_DK, bevel=0.02))
        o.append(bx(f"bg_bar{sx}", (1.2, 0.07, 0.09), (xc, -0.12, 1.1), METAL))
        o.append(bx(f"bg_win{sx}", (0.5, 0.02, 0.8), (xc, -0.09, 2.3), GLASS, "M_Clear"))
        pts = [(xc - 0.6 + 0.2 * k, -0.11, 0.25 + 0.5 * (k % 2) + 0.2 * k) for k in range(7)]
        o.append(tube(f"bg_crk{sx}", [(p[0], p[1], min(p[2], 3.0)) for p in pts], 0.03, VIOLET_EM, mat="M_Emit"))
    o.append(bx("bg_glow", (2.8, 0.7, 0.02), (0, -0.4, 0.01), VIOLET_EM, "M_Emit"))
    return [fin("boss_gate", o)]


# ---------------------------------------------------------------- decor (footprint ~ +-0.9 m, front = -Y)

def decor_1():
    """Classroom desk with a textbook and a chair pulled out in front."""
    o = [blk("d1_top", (0.9, 0.6, 0.05), (0, 0, 0.75), WOOD_LT, bevel=0.015),
         bx("d1_dr", (0.8, 0.5, 0.2), (0, 0, 0.56), WOOD),
         blk("d1_book", (0.22, 0.16, 0.03), (-0.2, 0.05, 0.79), RED, bevel=0.005)]
    for sx in (-1, 1):
        for sy in (-1, 1):
            o.append(cy(f"d1_leg{sx}{sy}", 0.022, 0.72, (sx * 0.4, sy * 0.25, 0.36), METAL_DK, seg=6))
    cx, cyy = 0.0, -0.6
    o.append(blk("d1_seat", (0.44, 0.42, 0.05), (cx, cyy, 0.45), BLUE_DK, bevel=0.01))
    o.append(blk("d1_back", (0.44, 0.05, 0.5), (cx, cyy + 0.19, 0.72), BLUE_DK, bevel=0.01))
    for sx in (-1, 1):
        for sy in (-1, 1):
            o.append(cy(f"d1_cl{sx}{sy}", 0.02, 0.44, (cx + sx * 0.18, cyy + sy * 0.17, 0.22), METAL_DK, seg=6))
    return [fin("decor_1", o)]


def decor_2():
    """Chalkboard on an easel with chalk tray and a few drawings."""
    r = R(9201)
    o = [cy("d2_p0", 0.03, 2.0, (-0.75, 0.15, 1.0), METAL_DK, seg=6), cy("d2_p1", 0.03, 2.0, (0.75, 0.15, 1.0), METAL_DK, seg=6),
         bx("d2_fb", (1.7, 0.05, 0.06), (0, -0.25, 0.08), METAL_DK),
         bx("d2_bar", (1.7, 0.06, 0.06), (0, 0.15, 0.2), METAL_DK),
         blk("d2_board", (1.5, 0.06, 1.1), (0, 0, 1.45), CHALK, bevel=0.01),
         bx("d2_frt", (1.6, 0.08, 0.06), (0, -0.02, 2.04), WOOD),
         bx("d2_frb", (1.6, 0.08, 0.06), (0, -0.02, 0.86), WOOD),
         bx("d2_frl", (0.06, 0.08, 1.2), (-0.77, -0.02, 1.45), WOOD),
         bx("d2_frr", (0.06, 0.08, 1.2), (0.77, -0.02, 1.45), WOOD),
         bx("d2_tray", (1.5, 0.12, 0.05), (0, -0.07, 0.8), WOOD_DK)]
    o += glyphs("d2_g", r, -0.6, 0.45, 1.2, 1.75, -0.035, "#f4f7f2", n=3, depth=0.015)
    o.append(K.prism("d2_st", K.star_pts(5, 0.13, 0.055), 0.015, axis="Y", loc=(0.55, -0.04, 1.6), color=YELLOW))
    for i, col in enumerate((WHITE, PINK, YELLOW)):
        o.append(cy(f"d2_ch{i}", 0.014, 0.1, (-0.4 + 0.2 * i, -0.09, 0.85), col, rot=(0, 90, 0), seg=6))
    return [fin("decor_2", o)]


def decor_3():
    """Three potted tulip-like plants."""
    o = []
    for i, (x, y, s, col) in enumerate(((0.0, 0.0, 1.0, PINK), (0.5, -0.35, 0.7, YELLOW), (-0.45, 0.3, 0.8, WHITE))):
        prof = [(0.0, 0.0), (0.18 * s, 0.0), (0.26 * s, 0.22 * s), (0.3 * s, 0.38 * s), (0.32 * s, 0.42 * s),
                (0.27 * s, 0.44 * s), (0.0, 0.44 * s)]
        o.append(lathe(f"d3_pot{i}", prof, loc=(x, y, 0), color=CLAY, seg=10))
        for k in range(3):
            a = 2 * math.pi * k / 3 + i
            lx, ly = x + math.cos(a) * 0.12 * s, y + math.sin(a) * 0.12 * s
            o.append(tube(f"d3_st{i}{k}", [(x, y, 0.44 * s), (lx, ly, 0.8 * s)], 0.018, GREEN_DK, seg=4))
            o.append(ball(f"d3_lf{i}{k}", 0.13 * s, (lx, ly, 0.7 * s), GREEN, scale=(1, 1, 1.4), seg=8, rings=4))
            o.append(ball(f"d3_fl{i}{k}", 0.09 * s, (lx, ly, 0.92 * s), col, seg=8, rings=4))
    return [fin("decor_3", o)]


def decor_4():
    """Sports bags and a basketball."""
    o = [ball("d4_b1", 0.3, (0.0, 0.0, 0.22), RED, scale=(1.5, 0.9, 0.85), seg=10, rings=6),
         bx("d4_z1", (0.5, 0.92, 0.04), (0, 0, 0.42), DARK),
         ball("d4_b2", 0.27, (0.55, -0.4, 0.2), BLUE_DK, scale=(1.4, 0.9, 0.85), seg=10, rings=6),
         ball("d4_bb", 0.14, (-0.45, 0.25, 0.14), ORANGE, seg=10, rings=6)]
    for k, c in enumerate(((0, 0, 1), (0, 1, 0), (1, 0, 0))):
        o.append(ring(f"d4_seam{k}", 0.14, 0.008, (-0.45, 0.25, 0.14), DARK, rot=(90 * c[0], 90 * c[1], 0),
                      seg=24, minor=3))
    return [fin("decor_4", o)]


def decor_5():
    """Festival booth: striped canopy, counter, sign board and two lanterns."""
    o = [blk("d5_ct", (1.5, 0.6, 0.8), (0, 0.0, 0.4), WHITE, bevel=0.02),
         bx("d5_ctst", (1.52, 0.62, 0.12), (0, 0.0, 0.7), RED),
         cy("d5_p0", 0.04, 2.1, (-0.85, 0.35, 1.05), WOOD_DK, seg=6), cy("d5_p1", 0.04, 2.1, (0.85, 0.35, 1.05), WOOD_DK, seg=6)]
    for i in range(6):
        x = -0.9 + 0.3 * i + 0.15
        o.append(bx(f"d5_cn{i}", (0.3, 1.2, 0.05), (x, 0.0, 2.1), RED if i % 2 == 0 else WHITE))
    o += sign("d5_sg", R(9501), -0.7, 0.7, 1.3, 1.7, -0.3, YELLOW, BLUE_DK, n=3, depth=0.05)
    for sx in (-1, 1):
        o.append(ball(f"d5_lt{sx}", 0.08, (sx * 0.6, -0.55, 1.95), LANTERN_EM, mat="M_Emit", seg=8, rings=5))
    return [fin("decor_5", o)]


def decor_6():
    """Stacked classroom chairs beside a mop bucket."""
    o = []
    for i in range(3):
        z = 0.3 + i * 0.25
        o.append(blk(f"d6_s{i}", (0.44, 0.42, 0.05), (0.3, 0.2, z), BLUE_DK, bevel=0.01))
        o.append(blk(f"d6_b{i}", (0.44, 0.05, 0.4), (0.3, 0.39, z + 0.22), BLUE_DK, bevel=0.01))
    o.append(lathe("d6_bk", [(0.0, 0.0), (0.2, 0.0), (0.24, 0.3), (0.22, 0.32), (0.0, 0.32)], loc=(-0.5, -0.3, 0),
                   color=BLUE, seg=10))
    o.append(cy("d6_mp", 0.02, 1.0, (-0.5, -0.3, 0.5), WOOD_DK, rot=(8, 0, 0), seg=6))
    o.append(ball("d6_mh", 0.16, (-0.5, -0.3, 0.07), WHITE, scale=(1, 1, 0.5), seg=8, rings=4))
    return [fin("decor_6", o)]


# ---------------------------------------------------------------- arena: gymnasium stage with festival decorations

def arena_builder():
    rng = R(900)
    floor = []
    floor.append(lathe("ar_rim", [(9.55, -0.5), (9.55, -0.12), (9.4, -0.03), (0.0, -0.03)], color=WOOD_DK, seg=64))
    for i in range(24):
        a0, a1 = math.tau * i / 24, math.tau * (i + 1) / 24
        pts = [(0.0, 0.0), (9.4 * math.cos(a0), 9.4 * math.sin(a0)), (9.4 * math.cos(a1), 9.4 * math.sin(a1))]
        floor.append(K.poly_slab(f"ar_w{i}", pts, top=0.0, thick=0.03, color=WOOD if i % 2 else WOOD_LT, bevel=0.0))
    floor.append(K.ring_strip("ar_c1", 1.55, 1.65, z=0.004, n=48, color=RED, mat="M_Toon"))
    floor.append(K.ring_strip("ar_c2", 8.9, 9.0, z=0.004, n=64, color=WHITE, mat="M_Toon"))
    floor.append(K.ring_strip("ar_c3", 0.0, 0.12, z=0.004, n=24, color=WHITE, mat="M_Toon"))
    back = []
    back.append(blk("ar_wall", (60, 2.0, 14), (0, 19, 7), CREAM, bevel=0.1))
    back.append(blk("ar_stage", (26, 6, 1.2), (0, 14, 0.6), WOOD_LT, bevel=0.03))
    back.append(blk("ar_stg2", (26, 0.3, 0.3), (0, 11.2, 1.25), WOOD_DK, bevel=0.02))
    for sx in (-1, 1):
        back.append(blk(f"ar_cur{sx}", (2.8, 0.5, 7.5), (sx * 10.5, 11.3, 4.0), RED, bevel=0.05))
        back.append(blk(f"ar_cp{sx}", (3.0, 0.6, 0.4), (sx * 10.5, 11.2, 7.9), YELLOW_DK, bevel=0.03))
    back.append(blk("ar_banner", (7.5, 0.2, 4.4), (0, 17.9, 7.0), BLUE_DK, bevel=0.03))
    back.append(K.prism("ar_star", K.star_pts(5, 1.5, 0.65), 0.1, axis="Y", loc=(0, 17.7, 7.2), color=YELLOW))
    back.append(bx("ar_board", (4.0, 0.3, 1.2), (0, 17.6, 11.0), DARK))
    back.append(bx("ar_score", (3.6, 0.1, 0.9), (0, 17.4, 11.0), "#ffd96b", "M_Emit"))
    for sx in (-1, 1):
        for r_ in range(5):
            back.append(blk(f"ar_bl{sx}{r_}", (2.0, 14, 0.5), (sx * (11.6 + r_ * 1.0), 4, 0.25 + r_ * 0.5),
                            BLUE if r_ % 2 else CREAM, bevel=0.02))
    back += garland("ar_gl", -12, 12, (8.2, 8.2), 1.2, 9.0, 26, [RED, YELLOW, BLUE_B, MINT, PINK, ORANGE],
                    flag_w=0.42, flag_h=0.5)
    for i in range(9):
        x = -12 + i * 3.0
        t = (x + 12) / 24
        back.append(ball(f"ar_lt{i}", 0.22, (x, 9.0, 8.2 - 1.2 * 4 * t * (1 - t) - 0.55), LANTERN_EM,
                         mat="M_Emit", seg=8, rings=5))
    return floor, back


def arena():
    return arena_scene(TS, arena_builder, ("#3a3f7a", "#141a3a"), WORLD)


# ---------------------------------------------------------------- pieces, layouts, publish

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
    """First-person corridor: DungeonWorld rules (torch 1.7 m, decor 1.45 m + 1 m, chest 1.3 m off the wall)."""
    plan = []
    for y in range(-1, 5):
        plan.append(("floor_a" if y % 2 else "floor_c", (0, y), 0, (0, 0, 0)))
    for y in range(-1, 6):
        for x in (-1, 1):
            plan.append((("wall_a", "wall_b", "wall_c")[(x * 7 + y * 3) % 3], (x, y), 0, (0, 0, 0)))
    plan.append(("wall_b", (0, 5), 0, (0, 0, 0)))
    plan += [
        ("torch", (0, 1), 90, (-1.7, 0, 0)), ("torch", (0, 3), -90, (1.7, 0, 0)),
        ("overlay_1", (-1, 1), 90, (0, 0, 0)), ("overlay_2", (1, 2), -90, (0, 0, 0)),
        ("overlay_1", (0, 5), 0, (0, 0, 0)),
        ("decor_1", (0, 2), 90, (-1.45, 1.0, 0)), ("decor_3", (0, 4), -90, (1.45, -1.0, 0)),
        ("chest", (0, 0), -90, (1.3, 0.2, 0)),
    ]
    return plan


def main():
    publish(TS, PIECES, LAYOUT, EXTRAS, WORLD, corridor, arena)


if __name__ == "__main__":
    main()
