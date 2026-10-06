"""ember_caverns battle arena — sun-temple courtyard on a basalt shelf above a lava sea.

Origin-centred walkable disc (flat z=0 for r<=9), edge dressing, cave-mouth framing,
and a +Y backdrop: sunken sun-temple facade with lavafalls, rock arches and a smoking volcano
under a dusk sky dome. Battle camera ~(0,-12,4) -> (0,3,1), 70 deg vFOV never sees void.
Output: Assets/_Game/Resources/Art/Environment/ember_caverns/arena.fbx
"""
import math
import os
import random
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.append(os.path.join(HERE, ".."))
sys.path.append(HERE)
import _kit_common_b as K  # noqa: E402
import importlib.util
_spec = importlib.util.spec_from_file_location("ember_arena_kit", os.path.join(HERE, "kit.py"))
E = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(E)

A = K.A
import bpy  # noqa: E402
from mathutils import Vector  # noqa: E402

TS = "ember_caverns"
R = random.Random


def sector_pts(r0, r1, a0, a1, n=3):
    """Annular sector outline (CCW) with n arc points per side."""
    pts = [(math.cos(a0 + (a1 - a0) * i / n) * r1, math.sin(a0 + (a1 - a0) * i / n) * r1) for i in range(n + 1)]
    pts += [(math.cos(a1 - (a1 - a0) * i / n) * r0, math.sin(a1 - (a1 - a0) * i / n) * r0) for i in range(n + 1)]
    return pts


def floor_disc(rng):
    """Concentric temple paving out to r=9.6 with a gold sun mosaic in the middle."""
    objs = [K.ngon_disc("ar_grout", 9.75, z=-0.05, n=64, color=E.GROUT)]
    rings = [(1.7, 3.0), (3.0, 4.3), (4.3, 5.6), (5.6, 6.9), (6.9, 8.2), (8.2, 9.3)]
    g = 0.045
    for ri, (r0, r1) in enumerate(rings):
        n = max(8, int(2 * math.pi * (r0 + r1) / 2 / rng.uniform(1.5, 1.8)))
        off = rng.uniform(0, 1)
        for i in range(n):
            a0 = 2 * math.pi * (i + off) / n + g / r1
            a1 = 2 * math.pi * (i + 1 + off) / n - g / r1
            # every few slabs split radially for variety
            if rng.random() < 0.35:
                rm = (r0 + r1) / 2
                parts = [(r0 + g, rm - g / 2), (rm + g / 2, r1 - g)]
            else:
                parts = [(r0 + g, r1 - g)]
            for pj, (q0, q1) in enumerate(parts):
                basalt = rng.random() < (0.06 if ri < 4 else 0.14)
                col = K.pick(rng, E.BAS if basalt else E.SAND, 0.07)
                objs.append(K.poly_slab(f"ar_s{ri}_{i}_{pj}", sector_pts(q0, q1, a0, a1, 2), top=-rng.uniform(0, 0.015),
                                        thick=0.2, color=col, bevel=0.04))
    # central sun mosaic
    objs.append(K.poly_slab("ar_c0", K.circle_pts(24, 1.65), top=0.0, thick=0.2, color=E.SAND_LT, bevel=0.05))
    objs.append(K.ring_strip("ar_c1", 1.35, 1.5, z=0.004, n=24, color=E.GOLD, mat="M_Toon"))
    objs += K.sun_emblem("ar_sun", r=1.15, rays=12, loc=(0, 0, 0.0), ray_col=E.GOLD, disc_col=E.GOLD_LT,
                         core_col=E.LAVA_HOT, axis="Z", depth=0.02)
    # glowing ray lines radiating from the mosaic (inlaid, flush)
    for i in range(8):
        a = i * math.pi / 4 + math.pi / 8
        objs.append(K.prism(f"ar_ray{i}", [(1.75, -0.05), (3.0, -0.025), (3.0, 0.025), (1.75, 0.05)], 0.01, axis="Z",
                            loc=(0, 0, 0.005), rot=(0, 0, math.degrees(a)), color=E.LAVA_HOT, mat="M_Emit"))
    # curb ring at the rim
    n = 40
    for i in range(n):
        a0 = 2 * math.pi * i / n + 0.006
        a1 = 2 * math.pi * (i + 1) / n - 0.006
        objs.append(K.poly_slab(f"ar_cb{i}", sector_pts(9.32, 9.95, a0, a1, 2), top=0.14, thick=0.5,
                                color=K.pick(rng, [E.SAND_DK, E.SAND[1]], 0.05), bevel=0.05))
        if i % 5 == 0:
            objs += K.grp_place(E.zigzag(f"ar_cz{i}", -0.35, 0.35, 0, h=0.18, y=0, n=3, col=E.SAND_CARVE),
                                loc=(math.cos((a0 + a1) / 2) * 9.96, math.sin((a0 + a1) / 2) * 9.96, -0.03),
                                rot=(0, 0, math.degrees((a0 + a1) / 2) + 90))
    return objs


def shelf(rng):
    """Basalt shelf under/around the disc that drops into the lava sea."""
    objs = []
    objs.append(A.cyl("sh_body", r=11.5, r2=10.0, depth=3.0, loc=(0, 0, -1.6), color=E.BAS[0], seg=32, smooth=False))
    K.A.gradient(objs[-1], E.LAVA_DEEP, E.BAS_DK)
    # broken rock rim (r 10..13)
    for i in range(46):
        a = 2 * math.pi * i / 46 + rng.uniform(-0.04, 0.04)
        d = rng.uniform(10.2, 12.4)
        r = rng.uniform(0.6, 1.3)
        objs.append(K.boulder(f"sh_r{i}", r, loc=(math.cos(a) * d, math.sin(a) * d, rng.uniform(-0.6, 0.05)),
                              scale=(1.3, 1.1, 0.7), rot=(0, 0, math.degrees(a)), color=K.pick(rng, E.BAS, 0.1),
                              seed=200 + i, subdiv=1, flat_bottom=-1.2))
    return objs


def edge_dressing(rng):
    objs = []
    lights = []
    # four broken temple pillars + four braziers around the ring (keep -Y wedge open for the camera)
    for i, deg in enumerate((25, 60, 120, 155, 205, 335)):
        a = math.radians(deg)
        x, y = math.cos(a) * 10.6, math.sin(a) * 10.6
        h = rng.uniform(2.4, 4.6) if deg not in (205, 335) else rng.uniform(1.2, 1.8)
        objs.append(K.stone(f"ed_pb{i}", (1.3, 1.3, 0.5), loc=(x, y, 0.25), rot=(0, 0, deg), color=E.SAND_DK, bevel=0.06))
        objs.append(K.stone(f"ed_ps{i}", (0.95, 0.95, h), loc=(x, y, 0.5 + h / 2), rot=(0, 0, deg), color=K.pick(rng, E.SAND),
                            bevel=0.06, rough=0.03, seed=i))
        objs.append(K.stone(f"ed_pt{i}", (0.9, 0.9, 0.5), loc=(x + 0.05, y, 0.5 + h + 0.2), rot=(6, -8, deg + 12),
                            color=K.pick(rng, E.SAND), bevel=0.06, rough=0.08, seed=i + 50))
        for k in range(4):
            part = E.diamond_carving(f"ed_d{i}{k}", 0, 0, s=0.75, y=-0.48)
            K.grp_place(part, loc=(0, 0, 0), rot=(0, 0, 90 * k))
            K.grp_place(part, loc=(x, y, 0.5 + min(h, 2.6) / 2), rot=(0, 0, deg))
            objs += part
    for i, deg in enumerate((20, 160, 200, 340)):
        a = math.radians(deg)
        x, y = math.cos(a) * 9.6, math.sin(a) * 9.6
        objs.append(K.stone(f"ed_bb{i}", (0.8, 0.8, 0.3), loc=(x, y, 0.29), color=E.SAND_DK, bevel=0.05))
        objs.append(A.cyl(f"ed_bs{i}", r=0.16, r2=0.12, depth=1.1, loc=(x, y, 0.95), color=E.GOLD_DK, seg=8))
        objs.append(A.lathe(f"ed_bw{i}", [(0.1, 0), (0.15, 0.08), (0.48, 0.3), (0.52, 0.38), (0.38, 0.34), (0, 0.3)],
                            loc=(x, y, 1.5), color=E.GOLD, seg=12))
        objs += K.flame(f"ed_fl{i}", loc=(x, y, 1.78), s=1.7, seed=i + 3)
        lights.append(K.empty(f"LightAnchor_brazier{i}", loc=(x, y, 2.4)))
    # urns, rubble, obsidian, agave tufts scattered on the rim
    for i in range(16):
        a = rng.uniform(0, 2 * math.pi)
        if -2.0 < a - 1.5 * math.pi < 2.0 and rng.random() < 0.6:
            continue
        d = rng.uniform(10.2, 11.6)
        x, y = math.cos(a) * d, math.sin(a) * d
        kind = i % 4
        if kind == 0:
            s = rng.uniform(0.7, 1.1)
            prof = [(0.0, 0), (0.22, 0.0), (0.33, 0.12), (0.4, 0.35), (0.36, 0.6), (0.2, 0.75), (0.24, 0.85), (0.0, 0.8)]
            objs.append(A.lathe(f"ed_u{i}", [(r * s, z * s) for r, z in prof], loc=(x, y, 0.1), color=K.jit(rng, E.CLAY),
                                seg=12))
            objs.append(A.cyl(f"ed_ub{i}", r=0.405 * s, depth=0.1 * s, loc=(x, y, 0.1 + 0.42 * s), color=E.SAND_CARVE, seg=12))
        elif kind == 1:
            for j in range(3):
                objs.append(K.shard(f"ed_o{i}{j}", r=rng.uniform(0.15, 0.3), h=rng.uniform(0.7, 1.6),
                                    loc=(x + rng.uniform(-0.4, 0.4), y + rng.uniform(-0.4, 0.4), 0),
                                    rot=(rng.uniform(-20, 20), rng.uniform(-20, 20), 0),
                                    color=E.OBS if j % 2 else E.OBS_HI, seed=i * 3 + j))
        elif kind == 2:
            objs.append(K.stone(f"ed_rb{i}", (rng.uniform(0.8, 1.4), rng.uniform(0.6, 1.0), rng.uniform(0.4, 0.7)),
                                loc=(x, y, 0.2), rot=(rng.uniform(-8, 8), rng.uniform(-8, 8), rng.uniform(0, 90)),
                                color=K.pick(rng, E.SAND), bevel=0.06, rough=0.05, seed=i))
        else:
            for j in range(9):
                aa = 2 * math.pi * j / 9
                leaf = K.prism(f"ed_ag{i}{j}", [(-0.06, 0), (0.06, 0), (0, rng.uniform(0.5, 0.8))], 0.03, axis="Y",
                               color=K.jit(rng, E.GREEN if j % 2 else E.GREEN_DK, 0.06))
                K.grp_place([leaf], loc=(x, y, 0.15), rot=(rng.uniform(25, 55), 0, math.degrees(aa)))
                objs.append(leaf)
    # glowing lava cracks running out from the curb into the rocks
    for i in range(10):
        a = 2 * math.pi * i / 10 + 0.2
        pts = []
        d = 9.9
        for k in range(4):
            aa = a + rng.uniform(-0.05, 0.05)
            pts.append((math.cos(aa) * d, math.sin(aa) * d, 0.12 - k * 0.06))
            d += rng.uniform(0.5, 0.8)
        objs += E.lava_vein(f"ed_lv{i}", pts, w=0.07)
    return objs, lights


def lava_sea(rng):
    objs = []
    sea = K.ngon_disc("ls_sea", 260, z=-1.4, n=48, color=E.LAVA, mat="M_Emit")
    objs.append(sea)
    # concentric hot glow near the shelf + crust floes scattered across the sea
    objs.append(K.ring_strip("ls_hot", 11.0, 16.0, z=-1.38, n=40, color=E.LAVA_HOT))
    for i in range(70):
        a = rng.uniform(0, 2 * math.pi)
        d = rng.uniform(15, 120)
        r = rng.uniform(0.8, 2.6) * (1 + d / 80)
        objs.append(K.poly_slab(f"ls_fl{i}", [(math.cos(t) * r * rng.uniform(0.7, 1.1), math.sin(t) * r * rng.uniform(0.6, 1.0))
                                               for t in [2 * math.pi * j / 6 for j in range(6)]],
                                top=-1.3, thick=0.15, color=K.pick(rng, [E.BAS_DK, E.BAS[2]]), bevel=0.0,
                                loc=(math.cos(a) * d, math.sin(a) * d, 0)))
    return objs


def cliff(prefix, rng, x0, x1, y0, y1, h0, h1, n, col_set, seed):
    """Rock mass made of stacked faceted boulders between two x/y spans, heights h0..h1."""
    objs = []
    for i in range(n):
        t = rng.random()
        x = x0 + (x1 - x0) * t + rng.uniform(-2, 2)
        y = y0 + (y1 - y0) * t + rng.uniform(-2, 2)
        h = h0 + (h1 - h0) * t * rng.uniform(0.7, 1.2)
        r = rng.uniform(2.5, 4.5)
        b = K.boulder(f"{prefix}{i}", r, loc=(x, y, h * 0.5 - 1.5), scale=(1.0, 1.0, max(1.0, h / (2 * r))),
                      rot=(0, 0, rng.uniform(0, 360)), color=K.pick(rng, col_set, 0.1), seed=seed + i, subdiv=1,
                      rough=0.22)
        top_c = K.pick(rng, ["#9a4e3c", "#b0603f", "#8a4438"], 0.06)
        K.A.gradient(b, E.BAS_DK, top_c)
        objs.append(b)
    return objs


def side_ruins(rng):
    """Canyon walls left & right with sandstone temple ruins and lavafalls (frames the battle view)."""
    objs = []
    for sx in (-1, 1):
        objs += cliff(f"cl{sx}", rng, sx * 17, sx * 24, -18, 30, 6, 16, 26, E.BAS, 400 + (sx > 0) * 50)
        # stepped ruin terrace blocks on the inner face
        for j in range(5):
            y = -6 + j * 7 + rng.uniform(-1, 1)
            x = sx * (14.5 + rng.uniform(0, 1.5))
            h = rng.uniform(3, 7)
            objs.append(K.stone(f"rt{sx}{j}", (rng.uniform(3, 4.5), rng.uniform(3, 5), h), loc=(x, y, h / 2 - 0.8),
                                rot=(0, 0, rng.uniform(-8, 8)), color=K.pick(rng, E.SAND), bevel=0.12, rough=0.12, seed=j))
            objs.append(K.stone(f"rtc{sx}{j}", (rng.uniform(3.2, 4.8), rng.uniform(3.2, 5.2), 0.5),
                                loc=(x, y, h - 0.55), color=E.SAND_LT, bevel=0.08, rough=0.04, seed=j + 9))
            objs += K.grp_place(E.zigzag(f"rtz{sx}{j}", -1.4, 1.4, 0, h=0.42, y=0, n=6, col=E.SAND_CARVE, col2=E.GOLD_DK),
                                loc=(x - sx * 1.7, y, h - 1.2), rot=(0, 0, -90 * sx))
            # lavafall pouring from between ruin blocks
            if j in (1, 3):
                lf = K.ribbon(f"lf{sx}{j}", -1.4, h + 1.0, 10, lambda t: 1.0 + 0.6 * t, x_fn=lambda t: math.sin(t * 6) * 0.15,
                              y_fn=lambda t: -0.3 - 0.8 * t ** 2, thick=0.2, color=E.LAVA)
                K.grad3(lf, E.LAVA_DEEP, E.LAVA, E.LAVA_CORE, mid=0.55)
                K.grp_place([lf], loc=(x - sx * 1.6, y + 3.4, 0), rot=(0, 0, -90 * sx))
                objs.append(lf)
        # tall sun-temple pylon on each side
        px, py = sx * 13.5, 17
        objs.append(K.stone(f"py_b{sx}", (3.2, 3.2, 1.2), loc=(px, py, 0.6), color=E.SAND_DK, bevel=0.1))
        objs.append(K.stone(f"py_s{sx}", (2.5, 2.5, 10), loc=(px, py, 6.2), color=K.pick(rng, E.SAND), bevel=0.1, taper=0.12))
        objs.append(K.stone(f"py_c{sx}", (2.9, 2.9, 0.9), loc=(px, py, 11.6), color=E.SAND_LT, bevel=0.1))
        for k in range(4):
            part = E.diamond_carving(f"py_d{sx}{k}", 0, 0, s=2.2, y=-1.27)
            K.grp_place(part, loc=(0, 0, 0), rot=(0, 0, 90 * k))
            K.grp_place(part, loc=(px, py, 4.5))
            objs += part
            part = E.zigzag(f"py_z{sx}{k}", -1.2, 1.2, 0, h=0.5, y=-1.2, n=5, col=E.SAND_CARVE)
            K.grp_place(part, loc=(0, 0, 0), rot=(0, 0, 90 * k))
            K.grp_place(part, loc=(px, py, 9.2))
            objs += part
        objs.append(A.lathe(f"py_bw{sx}", [(0.4, 0), (0.6, 0.3), (1.4, 0.9), (1.5, 1.2), (1.1, 1.1), (0, 1.0)],
                            loc=(px, py, 12.05), color=E.GOLD, seg=14))
        objs += K.flame(f"py_fl{sx}", loc=(px, py, 13.0), s=4.5, seed=sx + 20)
    return objs


def cave_mouth(rng):
    """Overhanging rock lip with stalactites at the top of the frame (like the reference)."""
    objs = []
    for i in range(22):
        t = i / 21
        a = math.pi * (0.04 + 0.92 * t)
        x = -math.cos(a) * 32
        z = 11.5 + math.sin(a) * 6.5
        y = 12 + rng.uniform(-2, 2)
        objs.append(K.boulder(f"cm{i}", rng.uniform(3.2, 4.6), loc=(x, y, z), scale=(1.2, 1.0, 0.8),
                              color=K.pick(rng, E.BAS, 0.1), seed=600 + i, subdiv=1, rough=0.25))
        for j in range(2):
            ln = rng.uniform(2.0, 4.5)
            sx = x + rng.uniform(-2, 2)
            st = A.cone(f"cms{i}{j}", r=rng.uniform(0.5, 0.9), depth=ln, loc=(sx, y - rng.uniform(0, 2), z - 2.6 - ln / 2),
                        rot=(180, 0, 0), color=K.pick(rng, E.BAS, 0.1), seg=6, smooth=False)
            objs.append(st)
            if rng.random() < 0.4:
                objs.append(A.cone(f"cmd{i}{j}", r=0.18, depth=ln * 0.8, loc=(sx, st.location.y - 0.45, z - 2.6 - ln * 0.45),
                                   rot=(180, 0, 0), color=E.LAVA_HOT, mat="M_Emit", seg=5, smooth=False))
    return objs


def temple_backdrop(rng):
    """Sunken sun-temple facade rising from the lava at y~44, sun disc, lavafalls; arches/mesas + volcano beyond."""
    objs = []
    Y = 46
    # stepped pyramid base (sinking into lava)
    for k, (w, d, h) in enumerate(((44, 12, 4), (36, 10, 4), (28, 8, 4))):
        objs.append(K.stone(f"tb_st{k}", (w, d, h), loc=(0, Y + k * 1.5, -1.5 + 4 * k + h / 2), color=K.pick(rng, E.SAND),
                            bevel=0.25, rough=0.25, seed=k, freq=0.15))
        objs += K.grp_place(E.zigzag(f"tb_z{k}", -w / 2 + 1, w / 2 - 1, 0, h=1.1, y=0, n=int(w / 1.3), col=E.SAND_CARVE,
                                     col2=E.GOLD_DK), loc=(0, Y + k * 1.5 - d / 2 - 0.02, -1.5 + 4 * k + h - 0.9))
    # colonnade on the top terrace
    top = -1.5 + 12
    for i in range(8):
        x = -10.5 + 3 * i
        if i in (3, 4):
            continue
        objs.append(K.stone(f"tc_b{i}", (2.0, 2.0, 0.8), loc=(x, Y + 2, top + 0.4), color=E.SAND_DK, bevel=0.1))
        objs.append(A.cyl(f"tc_c{i}", r=0.8, r2=0.7, depth=8, loc=(x, Y + 2, top + 4.8), color=K.pick(rng, E.SAND), seg=10,
                          smooth=False))
        objs.append(K.stone(f"tc_t{i}", (2.1, 2.1, 0.8), loc=(x, Y + 2, top + 9.2), color=E.SAND_LT, bevel=0.1))
    objs.append(K.stone("tc_ent", (30, 4, 2.2), loc=(0, Y + 2, top + 10.7), color=K.pick(rng, E.SAND), bevel=0.15))
    objs += K.grp_place(E.zigzag("tc_ez", -14.5, 14.5, 0, h=1.4, y=0, n=20, col=E.SAND_CARVE, col2=E.GOLD_DK),
                        loc=(0, Y - 0.02, top + 10.7))
    # broken pediment pieces + central portal with a giant sun
    objs.append(K.prism("tc_ped", [(-13, 0), (13, 0), (2, 6), (-2, 6)], 3.5, axis="Y", loc=(0, Y + 2, top + 11.8),
                        color=E.SAND_DK, bevel=0.1))
    objs.append(K.stone("tc_portal", (5.4, 2.0, 8.5), loc=(0, Y + 1.4, top + 4.25), color=E.VOID, bevel=0.1))
    objs.append(K.ngon_disc("tc_glow", 2.4, z=0, n=12, loc=(0, Y + 0.35, top + 3.2), rot=(90, 0, 0), color=E.LAVA_DEEP,
                            mat="M_Emit"))
    objs += K.sun_emblem("tc_sun", r=4.6, rays=16, loc=(0, Y + 0.0, top + 13.8), ray_col=E.GOLD, disc_col=E.GOLD_LT,
                         core_col=E.LAVA_HOT, depth=0.6)
    # lavafalls cascading down the pyramid steps
    for sx in (-1, 1):
        for j, xx in enumerate((7.5, 15.0)):
            lf = K.ribbon(f"tf{sx}{j}", -1.4, top - 0.5 - j * 4, 12, lambda t: 2.2 + 1.5 * t,
                          y_fn=lambda t: -6 * t ** 1.2, thick=0.3, color=E.LAVA)
            K.grad3(lf, E.LAVA_DEEP, E.LAVA, E.LAVA_CORE, mid=0.6)
            K.grp_place([lf], loc=(sx * xx, Y - 1, 0))
            objs.append(lf)
    # distant rock arches and mesas
    for i, (x, y, s) in enumerate(((-38, 80, 1.0), (40, 90, 1.2), (-70, 120, 1.5), (75, 130, 1.4), (-20, 140, 1.1),
                                   (25, 115, 0.9))):
        h = 22 * s
        for sx in (-1, 1):
            objs.append(K.boulder(f"am_l{i}{sx}", 3.0 * s, loc=(x + sx * 5 * s, y, h / 2 - 2), scale=(1, 1, h / (6 * s)),
                                  color=K.pick(rng, ["#b65b3a", "#9c4a34", "#c86f45"], 0.05), seed=700 + i * 3 + sx,
                                  subdiv=1, rough=0.25))
        if i % 2 == 0:
            objs.append(K.boulder(f"am_t{i}", 4.0 * s, loc=(x, y, h - 1), scale=(2.1, 0.9, 0.55),
                                  color="#a85238", seed=800 + i, subdiv=1, rough=0.25))
    # volcano
    vol = A.lathe("vol", [(70, 0), (52, 14), (30, 34), (14, 52), (9, 56), (7, 54), (0, 53)], loc=(10, 190, -3), seg=20,
                  color="#5a2d3e")
    K.A.deform(vol, lambda v: v + Vector((0, 0, math.sin(math.atan2(v.y, v.x) * 5) * 1.5 * (v.z / 56))))
    K.grad3(vol, "#7a3a40", "#5a2d3e", "#3e2034", mid=0.5)
    objs.append(vol)
    objs.append(K.ngon_disc("vol_crater", 7.2, z=55.0, n=12, loc=(10, 190, -3), color=E.LAVA_HOT, mat="M_Emit"))
    for i in range(5):
        a = math.radians(-120 + 15 * i + rng.uniform(-5, 5))
        pts = []
        for k in range(6):
            t = k / 5
            r = 8 + t * 48
            z = 54 - t * 50
            pts.append((10 + math.cos(a + t * 0.2) * r, 190 + math.sin(a + t * 0.2) * r - 1.0, z - 3))
        objs += E.lava_vein(f"vol_lv{i}", pts, w=1.0)
    # smoke plume
    for i in range(7):
        objs.append(K.boulder(f"smk{i}", 7 + i * 1.6, loc=(10 + i * 4 + rng.uniform(-2, 2), 192 + i * 2, 62 + i * 9),
                              scale=(1.3, 1, 0.8), color=K.mix("#4a2c48", "#7a5068", i / 7), seed=900 + i, subdiv=1,
                              rough=0.2, smooth=True))
    return objs


def sky():
    """Dusk sky dome (emissive gradient) so the backdrop never shows void."""
    dome = A.sphere("sky", 420, loc=(0, 0, -30), seg=32, rings=16, color="#ff9a4a", mat="M_Emit")
    me = dome.data
    # flip normals inward
    import bmesh
    bm = bmesh.new()
    bm.from_mesh(me)
    bmesh.ops.reverse_faces(bm, faces=bm.faces)
    bm.to_mesh(me)
    bm.free()
    K.paint_fn(dome, lambda co: K.ramp([(-0.2, "#5a1810"), (0.0, "#ff7a2a"), (0.06, "#ffb860"), (0.2, "#f07a6a"),
                                        (0.45, "#8a4a8a"), (0.8, "#3a2860")], (co.z - 30) / 420))
    return [dome]


def build():
    rng = R(4242)
    A.reset_scene()
    floor = floor_disc(rng)
    objs = floor + shelf(rng)
    edge, lights = edge_dressing(rng)
    objs += edge
    stage = K.finish("arena", objs)
    back = K.finish("arena_backdrop", lava_sea(rng) + side_ruins(rng) + cave_mouth(rng) + temple_backdrop(rng))
    sky_o = K.finish("arena_sky", sky())
    col = K.ngon_disc("Col_Ground", 10.0, z=0.0, n=32, color="#808080")
    lights.append(K.empty("LightAnchor_lava", loc=(0, 30, 6)))
    lights.append(K.empty("LightAnchor_center", loc=(0, 0, 5)))
    roots = [stage, back, sky_o, col] + lights
    tris = {o.name: K.tris(o) for o in roots if o.type == "MESH"}
    print("[arena] tris", tris, "total", sum(tris.values()))
    path = K.export_piece(TS, "arena", roots)
    print("[arena] exported", path)
    A.save_blend("env_ember_caverns_arena")
    col.hide_render = True
    K.render_cam("env_ember_caverns_arena_battlecam", loc=(0, -12, 4), target=(0, 3, 1), fov_deg=70, res=(1600, 900),
                 world="#000000")
    K.render_cam("env_ember_caverns_arena_wide", loc=(0, -24, 14), target=(0, 10, 2), fov_deg=60, res=(1600, 900),
                 world="#000000")
    K.render_cam("env_ember_caverns_arena_top", loc=(0.01, -0.01, 34), target=(0, 0, 0), fov_deg=50, res=(1200, 1200),
                 world="#000000", hide=[sky_o])
    return roots


if __name__ == "__main__":
    build()
