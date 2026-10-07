"""신록의 유적 (verdant_ruins) dungeon kit generator.

Run: blender -b --factory-startup -P Blender/environment/verdant_ruins/build_verdant_ruins.py
Outputs Assets/_Game/Resources/Art/Environment/verdant_ruins/<piece>.fbx, blend + previews.
Pass `-- --only floor_a,wall_a` to rebuild a subset (no sheet/mock previews then).
"""
import math
import os
import random
import sys

sys.path.append(os.path.join(os.path.dirname(os.path.abspath(__file__)), '../../lib'))
sys.path.append(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..'))
import abyss_bpy as A  # noqa: E402
import _kit_common_a as K  # noqa: E402
from _kit_common_a import MB, T, Vector, basis, mix, shade, vgrad  # noqa: E402
from _kit_interact_a import NorthernKit
from _pipeline import run, grid_piece

TS = "verdant_ruins"

P = dict(
    stone=["#e8d6a2", "#dcc58c", "#e2cd96", "#d3bb80", "#eadcae"],
    stone_dark="#a58c5c",
    stone_deep="#7c6844",
    grey=["#c9c2a8", "#bdb59a", "#d2cbb2"],
    moss="#93c83a",
    moss_dark="#5c9a2a",
    moss_deep="#3f7424",
    soil="#5a4a2a",
    leaf=["#3e9a3c", "#57b445", "#2f7d35", "#7cc548"],
    leaf_hi="#a6d84e",
    stem="#6b5a2e",
    bark="#7a5a36",
    bark_dark="#5a3f24",
    wood="#8a5a2b",
    wood_dark="#6a4220",
    gold="#e2b443",
    gold_dark="#a97c22",
    bronze="#a8713a",
    flower="#fff4dc",
    flower_mid="#f2c230",
    crystal=["#7af5d0", "#58e0c8", "#a8ffe4"],
    rune="#8dffcf",
    flame=["#ffb030", "#ffe27a"],
    water="#6ff2d8",
    foe="#ff8a1e",
)


def rng_for(*k):
    return random.Random(K.seed_of(TS, *k))


# ================================================================ floors

def stone_col(rng):
    c = rng.choice(P["stone"])
    if rng.random() < 0.18:
        c = rng.choice(P["grey"])
    return c


def add_flagstone(mb, rng, poly, top=None, crack=0.3, z_bottom=-0.3, col=None):
    top = rng.uniform(-0.025, 0.012) if top is None else top
    c = col or stone_col(rng)
    polys = [poly]
    if rng.random() < crack and abs(K.poly_area(poly)) > 0.35:
        cx, cy = K.poly_centroid(poly)
        polys = K.split_poly(poly, (cx + rng.uniform(-0.15, 0.15), cy + rng.uniform(-0.15, 0.15)),
                             rng.uniform(0, math.pi), gap=0.03)
    for pp in polys:
        t = top + rng.uniform(-0.012, 0.004)
        mb.add(K.prism(pp, z_bottom, t, inset=0.05, ch=0.06), vgrad(shade(c, 0.62), c, t - 0.1, t))
    return top


def moss_base(mb, z=-0.07, x0=-2, y0=-2, x1=2, y1=2):
    poly = [(x0, y0), (x1, y0), (x1, y1), (x0, y1)]
    mb.add(K.prism(poly, -0.4, z), vgrad(P["moss_deep"], P["moss"], -0.4, z))


def moss_patch(mb, rng, x, y, z, rx, ry, h=0.035):
    mb.add(K.dome(rx, ry, h, rng, seg=8, rings=2, lump=0.18, loc=(x, y, z)), mix(P["moss"], "#b7dc5a", rng.random() * 0.5),
           smooth=True)


def seam_greens(mb, rng, rects, n, gap_z=-0.07, clover=True):
    """Tufts / clover at random seam points between flagstone rects."""
    pts = []
    for (x0, y0, x1, y1) in rects:
        for _ in range(2):
            if rng.random() < 0.5:
                pts.append((x0 if rng.random() < 0.5 else x1, rng.uniform(y0, y1)))
            else:
                pts.append((rng.uniform(x0, x1), y0 if rng.random() < 0.5 else y1))
    rng.shuffle(pts)
    pts = [p for p in pts if max(abs(p[0]), abs(p[1])) < 1.88][:n]
    for x, y in pts:
        if clover and rng.random() < 0.5:
            for k in range(3):
                a = 2 * math.pi * k / 3 + rng.uniform(-0.3, 0.3)
                d = Vector((math.cos(a), math.sin(a), 0.5))
                mb.add(K.leaf(L=0.12, W=0.08, fold=0.01, curl=-0.01), rng.choice(P["leaf"][1:]),
                       M=basis(d, (0, 0, 1), (x, y, gap_z + 0.02)))
        else:
            K.tuft(mb, rng, Vector((x, y, gap_z)), [P["moss"], P["leaf"][3], P["leaf_hi"]], n=4, L=0.18, W=0.045, bend=0.4)


def floor_a():
    rng = rng_for("floor_a")
    mb = MB()
    moss_base(mb)
    rects = K.bsp_rects(rng, -2, -2, 2, 2, maxs=1.45, mins=0.5, keep=0.3)
    for (x0, y0, x1, y1) in rects:
        g = 0.04
        poly = K.rect_poly(x0 + g, y0 + g, x1 - g, y1 - g, cuts=[rng.uniform(0, 0.12) for _ in range(4)])
        top = add_flagstone(mb, rng, poly, crack=0.25)
        if rng.random() < 0.3:
            ex = rng.choice((x0 + 0.12, x1 - 0.12))
            moss_patch(mb, rng, ex, rng.uniform(y0 + 0.2, y1 - 0.2), top - 0.02, 0.14, rng.uniform(0.18, 0.32))
    seam_greens(mb, rng, rects, 10)
    return [mb.build("floor_a")]


def floor_b():
    """Regular large square paving, cracked, moss creeping over corners."""
    rng = rng_for("floor_b")
    mb = MB()
    moss_base(mb)
    rects = []
    for i in range(3):
        for j in range(3):
            x0, y0 = -2 + i * 4 / 3, -2 + j * 4 / 3
            rects.append((x0, y0, x0 + 4 / 3, y0 + 4 / 3))
    # merge two cells into a long slab for rhythm
    rects.remove((-2 + 4 / 3, -2, -2 + 8 / 3, -2 + 4 / 3))
    rects.remove((-2 + 4 / 3, -2 + 4 / 3, -2 + 8 / 3, -2 + 8 / 3))
    rects.append((-2 + 4 / 3, -2, -2 + 8 / 3, -2 + 8 / 3))
    for (x0, y0, x1, y1) in rects:
        g = 0.045
        poly = K.rect_poly(x0 + g, y0 + g, x1 - g, y1 - g, cuts=[rng.uniform(0.02, 0.1) for _ in range(4)])
        top = add_flagstone(mb, rng, poly, crack=0.55)
        for _ in range(rng.randint(0, 2)):
            cx = rng.choice((x0 + 0.15, x1 - 0.15))
            cy = rng.choice((y0 + 0.15, y1 - 0.15))
            moss_patch(mb, rng, cx, cy, top - 0.02, rng.uniform(0.15, 0.3), rng.uniform(0.15, 0.3))
    # small inset carved disc on the long slab
    mb.add(K.lathe([(0.42, -0.05), (0.42, 0.006), (0.34, 0.006), (0.34, 0.0), (0.0, 0.0)], 16),
           shade(P["stone"][1], 0.88), M=T((0, 2 / 3 - 2 / 3, 0)))
    seam_greens(mb, rng, rects, 12)
    return [mb.build("floor_b")]


def floor_c():
    """Broken paving: a few stones missing, grass and a root crossing, scattered pebbles."""
    rng = rng_for("floor_c")
    mb = MB()
    moss_base(mb, z=-0.09)
    rects = K.bsp_rects(rng, -2, -2, 2, 2, maxs=1.3, mins=0.5, keep=0.3)
    inner = [r for r in rects if max(abs(r[0]), abs(r[2]), abs(r[1]), abs(r[3])) < 1.99]
    missing = set()
    order = sorted(range(len(rects)), key=lambda i: (rects[i][0] + rects[i][2]) ** 2 + (rects[i][1] + rects[i][3]) ** 2)
    for i in order[:2]:
        missing.add(i)
    for i, (x0, y0, x1, y1) in enumerate(rects):
        g = 0.045
        if i in missing:
            cx, cy = (x0 + x1) / 2, (y0 + y1) / 2
            mb.add(K.dome((x1 - x0) / 2, (y1 - y0) / 2, 0.06, rng, seg=10, rings=2, lump=0.1, loc=(cx, cy, -0.09)),
                   P["moss_dark"], smooth=True)
            K.tuft(mb, rng, Vector((cx, cy, -0.06)), [P["moss"], P["leaf"][3], P["leaf_hi"]], n=7, L=0.32, W=0.06)
            for _ in range(2):
                px, py = rng.uniform(x0 + 0.1, x1 - 0.1), rng.uniform(y0 + 0.1, y1 - 0.1)
                mb.add(K.rock(rng, 0.2, 0.16, 0.12, n=10, loc=(px, py, -0.04)), stone_col(rng))
            continue
        poly = K.rect_poly(x0 + g, y0 + g, x1 - g, y1 - g, cuts=[rng.uniform(0, 0.15) for _ in range(4)])
        tilt = rng.uniform(-0.04, 0.0)
        add_flagstone(mb, rng, poly, top=tilt, crack=0.45)
    # tree root snaking across the tile (stays inside the cell)
    pts = []
    for k in range(9):
        t = k / 8
        pts.append((-1.7 + 3.2 * t, -1.3 + 0.9 * math.sin(t * 3.3) + 0.6 * t, 0.03 + 0.05 * math.sin(t * 9)))
    mb.add(K.tube(pts, [0.11 * (1 - 0.65 * k / 8) for k in range(9)], sides=6), vgrad(P["bark_dark"], P["bark"], -0.05, 0.12),
           smooth=True)
    K.leaf_spray(mb, rng, (-1.6, -1.3, 0.12), (0, 0, 1), 4, 0.22, P["leaf"], spread=0.6, droop=(1, 0, 0))
    seam_greens(mb, rng, rects, 10)
    flowers(mb, rng, [(1.2, 1.1), (1.35, 1.25), (-1.1, 0.9)])
    return [mb.build("floor_c")]


def flowers(mb, rng, pts, z=0.0):
    for x, y in pts:
        zz = z + rng.uniform(0.04, 0.12)
        mb.add(K.tube([(x, y, z - 0.05), (x, y, zz)], 0.01, sides=3), P["leaf"][0])
        mb.add(K.flower(0.075), P["flower"], M=T((x, y, zz), (rng.uniform(-15, 15), rng.uniform(-15, 15), rng.uniform(0, 70))))
        mb.add(K.cyl(0.025, 0.02, 6), P["flower_mid"], M=T((x, y, zz - 0.003)))


# ================================================================ walls

WALL_OUT = 2.0


def brick_face(mb, rng, side, z0, z1, full, out=1.96, depth=0.3, wmin=0.9, wmax=1.7, carve=False):
    """One masonry course on one face. full=True spans the corners (alternating bond)."""
    span = 2.0 if full else 2.0 - depth
    widths = K.split_widths(rng, 2 * span, wmin, wmax)
    u = -span
    M = K.face_matrix(side, 0.0)
    g = 0.035
    for w in widths:
        c = stone_col(rng)
        o = min(WALL_OUT, out + rng.uniform(-0.035, 0.02))
        u0, u1 = u + g, u + w - g
        if full:
            u0 = max(u0, -2.0)
            u1 = min(u1, 2.0)
        poly = K.rect_poly(u0, z0 + g, u1, z1 - g, cuts=[rng.uniform(0.0, 0.1) for _ in range(4)])
        polys = [poly]
        if rng.random() < 0.18 and (u1 - u0) > 0.9:
            polys = K.split_poly(poly, ((u0 + u1) / 2 + rng.uniform(-0.2, 0.2), (z0 + z1) / 2), rng.uniform(1.0, 2.1), gap=0.03)
        for pp in polys:
            mb.add(K.prism(pp, 2.0 - depth - 0.25, o, inset=0.05, ch=0.07), vgrad(shade(c, 0.86), c, z0, z1), M=M)
        u += w


def wall_core(mb):
    poly = [(-1.72, -1.72), (1.72, -1.72), (1.72, 1.72), (-1.72, 1.72)]
    mb.add(K.prism(poly, 0.0, 4.44), vgrad(P["moss_deep"], P["moss_dark"], 0, 4.5))


def wall_masonry(mb, rng, carve_course=None):
    courses = [(0.0, 0.55)]
    z = 0.55
    hs = [0.85, 0.75, 0.9, 0.8, 0.65]
    rng.shuffle(hs)
    while z < 4.05:
        h = hs[len(courses) % len(hs)]
        h = min(h, 4.05 - z)
        if 4.05 - (z + h) < 0.3:
            h = 4.05 - z
        courses.append((z, z + h))
        z += h
    courses.append((4.05, 4.5))
    for ci, (z0, z1) in enumerate(courses):
        plinth = ci == 0
        cornice = ci == len(courses) - 1
        for si, side in enumerate(("S", "E", "N", "W")):
            full = (ci + si) % 2 == 0
            out = 2.0 if (plinth or cornice) else 1.95
            if ci == carve_course:
                frieze_face(mb, rng, side, z0, z1, full)
            else:
                brick_face(mb, rng, side, z0, z1, full, out=out,
                           wmin=1.2 if (plinth or cornice) else 0.85, wmax=2.2 if (plinth or cornice) else 1.6)
    return courses


def frieze_face(mb, rng, side, z0, z1, full):
    """Carved band: one long block with a row of semicircle relief arches (as in the wall reference)."""
    M = K.face_matrix(side, 0.0)
    span = 2.0 if full else 1.7
    c = P["stone"][4]
    poly = K.rect_poly(-span + 0.03, z0 + 0.035, span - 0.03, z1 - 0.035, cut=0.05)
    mb.add(K.prism(poly, 1.45, 1.97, inset=0.05, ch=0.07), vgrad(shade(c, 0.86), c, z0, z1), M=M)
    # horizontal fillet + arches
    mb.add(K.prism(K.rect_poly(-span + 0.1, z0 + 0.1, span - 0.1, z0 + 0.17), 1.96, 2.0), shade(c, 0.92), M=M)
    n = 4
    r = (z1 - z0) * 0.32
    for k in range(n):
        cx = -span + (k + 0.5) * 2 * span / n
        pts = [(cx + math.cos(a) * r, z0 + 0.2 + math.sin(a) * r, 1.985)
               for a in [math.pi * i / 6 for i in range(7)]]
        mb.add(K.tube(pts, 0.028, sides=4), shade(c, 0.95), M=M, smooth=True)
        mb.add(K.tube([(cx + math.cos(a) * r * 0.55, z0 + 0.2 + math.sin(a) * r * 0.55, 1.975)
                       for a in [math.pi * i / 4 for i in range(5)]], 0.02, sides=4), shade(c, 0.9), M=M, smooth=True)


def wall_top(mb, rng, lush=1.0):
    """Top of the wall block: worn capstones, moss mounds, ferns and grass."""
    rects = K.bsp_rects(rng, -1.98, -1.98, 1.98, 1.98, maxs=1.6, mins=0.7, keep=0.35)
    for (x0, y0, x1, y1) in rects:
        g = 0.04
        poly = K.rect_poly(x0 + g, y0 + g, x1 - g, y1 - g, cuts=[rng.uniform(0.0, 0.12) for _ in range(4)])
        c = stone_col(rng)
        t = 4.5 + rng.uniform(-0.03, 0.03)
        mb.add(K.prism(poly, 4.3, t, inset=0.05, ch=0.06), vgrad(shade(c, 0.7), c, 4.4, t))
    for _ in range(int(3 * lush)):
        x, y = rng.uniform(-1.3, 1.3), rng.uniform(-1.3, 1.3)
        mb.add(K.dome(rng.uniform(0.5, 0.9), rng.uniform(0.4, 0.8), rng.uniform(0.12, 0.22), rng, seg=10, rings=3, lump=0.15,
                      loc=(x, y, 4.47)), vgrad(P["moss_dark"], P["moss"], 4.45, 4.7), smooth=True)
    for _ in range(int(2 * lush)):
        K.fern(mb, rng, Vector((rng.uniform(-1.2, 1.2), rng.uniform(-1.2, 1.2), 4.5)), P["leaf"], n=6, L=0.75, W=0.18, droop=0.45)
    for _ in range(int(3 * lush)):
        K.tuft(mb, rng, Vector((rng.uniform(-1.6, 1.6), rng.uniform(-1.6, 1.6), 4.5)), [P["moss"], P["leaf"][3], P["leaf_hi"]],
               n=5, L=0.3, W=0.06)


def face_vine(mb, rng, side, u, length, flower_p=0.25, z_top=4.55):
    """Ivy hanging from the wall top down one face."""
    M = K.face_matrix(side, 0.0)
    nrm = M.to_3x3() @ Vector((0, 0, 1))
    pts = []
    n = max(3, int(length / 0.35))
    sw = rng.uniform(0, 6)
    for k in range(n + 1):
        t = k / n
        pts.append(M @ Vector((u + 0.25 * math.sin(sw + t * 4.5) * t, z_top - length * t, 2.02 + 0.015 * math.sin(t * 7))))
    # over the lip onto the top
    top = M @ Vector((u + rng.uniform(-0.2, 0.2), z_top + 0.03, 1.7))
    pts.insert(0, top)
    K.vine(mb, rng, pts, nrm, P["stem"], P["leaf"], r=0.025, leaf_size=0.24, leaf_step=0.2,
           flower_cols=(P["flower"], P["flower_mid"]), flower_p=flower_p)


def root_over(mb, rng, side, u, length, r=0.12):
    """Thick tree root climbing over the top lip and down a face."""
    M = K.face_matrix(side, 0.0)
    pts = [M @ Vector((u * 0.4, 4.55, 0.6)), M @ Vector((u * 0.8, 4.62, 1.6)), M @ Vector((u, 4.5, 2.05))]
    n = 5
    for k in range(1, n + 1):
        t = k / n
        pts.append(M @ Vector((u + 0.3 * math.sin(t * 3 + u), 4.5 - length * t, 2.04 + 0.03 * math.sin(t * 5))))
    radii = [r * 1.2, r * 1.15, r] + [r * (1 - 0.8 * k / n) for k in range(1, n + 1)]
    mb.add(K.tube(pts, radii, sides=6), vgrad(P["bark_dark"], P["bark"], 4.5 - length, 4.7), smooth=True)


def crystal_sprout(mb, rng, side, u, z, size=0.6):
    M = K.face_matrix(side, 0.0)
    nrm = M.to_3x3() @ Vector((0, 0, 1))
    base = M @ Vector((u, z, 1.98))
    mb.add(K.rock(rng, 0.45 * size * 2, 0.35 * size * 2, 0.3 * size * 2, n=10, loc=tuple(base)), shade(P["stone"][3], 0.8))
    K.crystal_cluster(mb, rng, base + nrm * 0.05, P["crystal"], n=4, size=size, up=(nrm * 0.8 + Vector((0, 0, 0.6))), tilt=0.35)


def wall_a():
    rng = rng_for("wall_a")
    mb = MB()
    wall_core(mb)
    wall_masonry(mb, rng)
    wall_top(mb, rng, lush=0.8)
    face_vine(mb, rng, "S", -0.9, 2.6)
    face_vine(mb, rng, "E", 0.6, 1.8)
    face_vine(mb, rng, "N", 1.1, 3.0)
    face_vine(mb, rng, "W", -0.4, 1.4, flower_p=0.0)
    return [mb.build("wall_a")]


def wall_b():
    rng = rng_for("wall_b")
    mb = MB()
    wall_core(mb)
    courses = wall_masonry(mb, rng, carve_course=3)
    wall_top(mb, rng, lush=0.7)
    crystal_sprout(mb, rng, "S", 1.2, 0.55, 0.55)
    crystal_sprout(mb, rng, "N", -1.0, 0.55, 0.5)
    face_vine(mb, rng, "E", -1.0, 2.2)
    face_vine(mb, rng, "W", 0.9, 2.8)
    face_vine(mb, rng, "S", -1.3, 1.2, flower_p=0.0)
    return [mb.build("wall_b")]


def wall_c():
    rng = rng_for("wall_c")
    mb = MB()
    wall_core(mb)
    wall_masonry(mb, rng)
    wall_top(mb, rng, lush=1.2)
    root_over(mb, rng, "S", 0.5, 3.3)
    root_over(mb, rng, "E", -0.7, 2.5, r=0.1)
    root_over(mb, rng, "N", 0.2, 3.8, r=0.13)
    root_over(mb, rng, "W", 0.8, 2.0, r=0.09)
    face_vine(mb, rng, "S", -1.1, 3.4)
    face_vine(mb, rng, "N", -1.2, 2.0)
    face_vine(mb, rng, "W", -0.8, 3.0)
    face_vine(mb, rng, "E", 1.2, 1.6)
    return [mb.build("wall_c")]


# ================================================================ main

PIECES = [
    ("floor_a", floor_a), ("floor_b", floor_b), ("floor_c", floor_c),
    ("wall_a", wall_a), ("wall_b", wall_b), ("wall_c", wall_c),
]
PIECES += NorthernKit(frozen=False).extras()


def main():
    argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
    only = None
    if "--only" in argv:
        only = set(argv[argv.index("--only") + 1].split(","))
    if not only:
        run(TS, PIECES, world="#597448")
        return
    A.reset_scene()
    kit = K.Kit(TS)
    for name, fn in PIECES:
        if name not in only:
            continue
        objs = grid_piece(name, fn)()
        kit.export(name, objs)
        if only:
            A.render_preview(f"env_{TS}_{name}", objects=[o for o in objs if o.type == "MESH"], angle=(58, 0, 30), size=720)
            for o in objs:
                o.hide_render = True
    print("\n".join(kit.report))


if __name__ == "__main__":
    main()
