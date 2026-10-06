"""Living-ruin, glacier and crypt battle stages, with a clear 9 m radius."""
import math
import random
import _kit_common_a as K
import _kit_common_b as B
from _kit_common_a import MB, T, Vector, vgrad
from _kit_interact_a import NorthernKit, xz_prism


def sector(r0, r1, a0, a1):
    return [(math.cos(a0) * r0, math.sin(a0) * r0),
            (math.cos(a0) * r1, math.sin(a0) * r1),
            (math.cos((a0 + a1) / 2) * r1, math.sin((a0 + a1) / 2) * r1),
            (math.cos(a1) * r1, math.sin(a1) * r1),
            (math.cos(a1) * r0, math.sin(a1) * r0)]


def stage(theme, rng):
    mb = MB()
    mb.add(K.lathe([(10.2, -0.6), (10.2, -0.14), (9.5, -0.05), (0, -0.05)], seg=64), theme.dark)
    mb.add(K.prism(K.circle_poly(1.25, 20), -0.25, 0), theme.trim)
    theme.motif(mb, (0, 0, -0.025), 0.9, upright=False)
    for j, (r0, r1) in enumerate(((1.25, 2.6), (2.6, 4), (4, 5.5), (5.5, 7), (7, 8.4), (8.4, 9.4))):
        n = int(r1 * 4) + 8
        for i in range(n):
            a0, a1 = (i + 0.01) * math.tau / n, (i + 0.99) * math.tau / n
            mb.add(K.prism(sector(r0 + 0.018, r1 - 0.018, a0, a1), -0.2, 0, inset=0.025, ch=0.03), rng.choice(theme.stone))
    for i in range(48):
        mb.add(K.prism(sector(9.45, 10.0, i * math.tau / 48 + 0.008, (i + 1) * math.tau / 48 - 0.008), -0.3, 0.18,
                       inset=0.03, ch=0.04), theme.trim)
    return mb


def tree(mb, rng, loc, height, theme):
    x, y, z = loc
    pts = [(x, y, z), (x - 0.15, y + 0.25, z + height * 0.4), (x + 0.4, y, z + height * 0.85)]
    mb.add(K.tube(pts, [height * 0.11, height * 0.08, height * 0.035], sides=8), vgrad("#49352c", "#926746", z, z + height))
    for i in range(5):
        a = i * math.tau / 5
        end = (x + math.cos(a) * height * 0.3, y + math.sin(a) * height * 0.27, z + height * rng.uniform(0.62, 0.86))
        mb.add(K.tube([pts[1], end], [height * 0.05, height * 0.018], sides=6), "#7a5a36")
        mb.add(K.lump_sphere(rng, height * 0.26, seg=10, rings=6, loc=end, scale=(1.2, 1, 0.7)), rng.choice(theme.plant))
    for i in range(4):
        a = i * math.pi / 2
        mb.add(K.tube([(x, y, z + 0.35), (x + math.cos(a) * 1.2, y + math.sin(a) * 1.2, z)], [0.25, 0.04], sides=6), "#6b4d32")


def forest(theme, rng):
    mb = MB()
    # A raised ruined sanctuary enclosed by a lush treeline; the southern view stays open.
    for x, y, h in ((-13, 0, 7), (13, 1, 8), (-15, 12, 10), (15, 13, 11), (-9, 25, 12), (10, 27, 13), (-19, 29, 12), (20, 31, 14)):
        tree(mb, rng, (x, y, -0.3), h, theme)
    for x in (-13, -8, 8, 13):
        sub = MB()
        sub.add(K.lathe([(0.95, 0), (0.95, 0.4), (0.7, 0.55), (0.62, 5.6), (0.95, 5.85), (0.95, 6.2)], seg=12), theme.trim)
        for i in range(8):
            a = i * math.pi / 4
            sub.add(K.tube([(math.cos(a) * 0.62, math.sin(a) * 0.62, 0.6), (math.cos(a) * 0.62, math.sin(a) * 0.62, 5.5)], 0.035, sides=4), theme.dark)
        theme.nature(sub, rng, (0, 0, 6.18), 1.5)
        mb.add((sub.v, [f[0] for f in sub.f]), theme.trim, M=T((x, 18, 0)))
    for x in (-10.5, 10.5):
        theme.block(mb, (5.8, 1.1, 0.7), (x, 18, 6.0), theme.stone[1], 0.12)
    arch = MB()
    theme.arch(arch, rng, width=5.6, spring=4.8, depth=1.4)
    # Preserve per-face material/colour while placing this composite.
    for verts, col, mat, smooth in arch.f:
        mb.add(([arch.v[v] for v in verts], [tuple(range(len(verts)))]), col, mat, smooth, M=T((0, 24, 0)))
    for i in range(16):
        x = -24 + i * 3.2
        tree(mb, rng, (x, 37 + rng.uniform(-2, 4), -0.4), rng.uniform(8, 14), theme)
    for x in (-10.5, 10.5):
        for y in (3, 9, 14):
            theme.nature(mb, rng, (x, y, 0), 1.5)
    return mb


def glacier(theme, rng):
    mb = MB()
    # Stratified cave sides and rear ice ribs; every mass starts outside the stage.
    for sx in (-1, 1):
        for j in range(7):
            x, y = sx * rng.uniform(12, 16), -1 + j * 5
            h = rng.uniform(7, 12)
            mb.add(K.rock(rng, 5.8, 7, h, n=18, loc=(x, y, h / 2 - 0.5)), rng.choice(theme.stone))
            mb.add(K.dome(3.2, 3.5, 0.5, rng, seg=10, rings=2, loc=(x, y, h - 0.6)), "#d8eff8")
            K.crystal_cluster(mb, rng, (x - sx, y, 0), theme.plant, n=5, size=3.5, mat="M_Clear")
            for i in range(4):
                mb.add(K.icicle(0.2 + i * 0.04, rng.uniform(1, 3)), theme.plant[i % 3], "M_Clear", M=T((x - sx * 2, y + i * 0.5, h - 0.8)))
    for i in range(9):
        x = -20 + i * 5
        h = 12 + 3 * math.cos(i)
        mb.add(K.rock(rng, 6, 6, h, n=18, loc=(x, 35, h / 2 - 1)), rng.choice(theme.stone))
        K.crystal_cluster(mb, rng, (x, 32, h * 0.35), theme.plant, n=3, size=5, mat="M_Clear")
    # Curving glacial portal in the far wall.
    for i in range(14):
        a = i * math.pi / 13
        mb.add(K.crystal(0.45, 3.2, seg=6), theme.plant[i % 3], "M_Clear",
               M=T((math.cos(a) * 6.5, 28, 3.3 + math.sin(a) * 7), rot=(0, math.degrees(a) - 90, 0)))
    mb.add(K.prism(K.circle_poly(24, 40, cy=24), -0.7, -0.2), "#4fa6c5", "M_Clear")
    # Aurora ribbons are a distant, continuous coloured backdrop, not particles over actors.
    for j in range(3):
        pts = [(x, 42 + j, 10 + j * 1.8 + math.sin(x * 0.14 + j) * 2) for x in range(-30, 31, 3)]
        mb.add(K.tube(pts, [0.4] * len(pts), sides=4), ("#64e9d9", "#8cb4f6", "#b7a1ec")[j], "M_Emit")
    return mb


def crypt(theme, rng, H):
    mb, objects = MB(), []
    theme.block(mb, (48, 35, 0.4), (0, 23, -0.5), theme.dark)
    # A vaulted ossuary nave with two receding colonnades.
    for sx in (-1, 1):
        for j in range(5):
            x, y = sx * 12, 8 + j * 6
            mb.add(K.lathe([(1.05, 0), (1.05, 0.5), (0.72, 0.65), (0.62, 7.5), (0.9, 7.7), (1.1, 8.1)], seg=12), theme.stone[1], M=T((x, y, 0)))
            for z in (1, 6.8):
                mb.add(K.cyl(0.74, 0.15, seg=12), theme.trim, M=T((x, y, z)))
            for i in range(9):
                a = i * math.pi / 8
                theme.block(mb, (0.75, 0.9, 0.65), (math.cos(a) * 12, y, 8 + math.sin(a) * 4.8), theme.stone[i % 4])
            objs = H.hooded_statue(f"guardian{sx}_{j}", rng, s=2, flame=True)
            B.grp_place(objs, loc=(sx * 10.3, y, 0))
            objects += objs
    # Rear apse with genuine pointed openings and carved tracery.
    for x in (-9, 0, 9):
        objs = H.voussoirs(f"apse{x}", w=5.2, hs=5, depth=1.2, thick=0.6, n=9, y=38, rng=rng)
        B.grp_place(objs, loc=(x, 0, 0))
        objects += objs
        theme.block(mb, (1.2, 1.4, 9), (x - 3.4, 38, 4.5), theme.stone[1])
        theme.block(mb, (1.2, 1.4, 9), (x + 3.4, 38, 4.5), theme.stone[1])
        objects += H.quatrefoil(f"rose{x}", 1.2, loc=(x, 37.25, 8), col=theme.trim, inner=theme.glow, inner_mat="M_Emit", depth=0.1)
    for sx in (-1, 1):
        for j in range(6):
            y = j * 5 + 8
            objs = H.decor_4()
            B.grp_place(objs, loc=(sx * 11.0, y, 0), rot=(0, 0, sx * 12), scale=1.4)
            objects += objs
    return mb, objects


def build(ts, haunted=None):
    K.A.reset_scene()
    theme = NorthernKit(ts == "frost_grotto")
    theme.ts = ts
    if ts == "haunted_crypt":
        theme.stone = ["#4b4064", "#55486f", "#433a5b", "#5c4e76"]
        theme.dark, theme.trim, theme.glow = "#1b1524", "#8c6a58", "#b45cff"
        theme.metal = "#77728c"
    rng = random.Random(K.seed_of(ts, "arena"))
    floor = stage(theme, rng).build("arena")
    if ts == "verdant_ruins":
        back, extra = forest(theme, rng), []
        skycols = ("#9aead0", "#77bcd2")
    elif ts == "frost_grotto":
        back, extra = glacier(theme, rng), []
        skycols = ("#314d76", "#152638")
    else:
        back, extra = crypt(theme, rng, haunted)
        skycols = ("#42365c", "#171421")
    backdrop = back.build("arena_backdrop")
    if extra:
        backdrop = B.finish("arena_backdrop", [backdrop] + extra)
    sky = MB()
    sky.add(K.uvsphere(95, seg=32, rings=16, loc=(0, 10, 8)), vgrad(skycols[0], skycols[1], -20, 90), "M_Emit")
    skyobj = sky.build("arena_sky")
    collision = MB()
    collision.add(K.disc(9.4, n=64, z=0), "#888888")
    collider = collision.build("Col_Ground")
    roots = [floor, backdrop, skyobj, collider]
    roots += [K.empty("Spot_party", (0, -4, 0)), K.empty("Spot_enemies", (0, 4, 0)),
              K.empty("Spot_camera", (0, -12, 4)), K.empty("LightAnchor_stage", (0, 0, 5))]
    for i, (x, y) in enumerate(((-10.5, 4), (10.5, 4), (-10.5, 14), (10.5, 14))):
        roots.append(K.empty(f"LightAnchor_edge_{i}", (x, y, 2.2)))
    B.export_piece(ts, "arena", roots)
    collider.hide_render = True
    K.A.save_blend(f"env_{ts}_arena")
    B.render_cam(f"env_{ts}_arena_battlecam", loc=(0, -12, 4), target=(0, 3, 1), fov_deg=70,
                 res=(1600, 900), world="#18202b")
    B.render_cam(f"env_{ts}_arena_wide", loc=(0, -24, 14), target=(0, 10, 2), fov_deg=60,
                 res=(1600, 900), world="#18202b")
    B.render_cam(f"env_{ts}_arena_top", loc=(0.01, -0.01, 34), target=(0, 0, 0), fov_deg=50,
                 res=(1200, 1200), world="#18202b", hide=[skyobj])
    print(f"[arena] {ts}: {sum(B.tris(o) for o in roots)} tris")
    return roots
