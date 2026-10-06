"""서리 늑대 (ice_wolf) / 설원의 우두머리 (elite_ice_wolf): chibi quadruped frost wolf ~1.1 m tall.
Big head, fluffy white-grey fur with blue-grey patches and socks, huge layered neck ruff, big pointed
ears with pink inner, bright cyan eyes, open fanged grin, two-tone faceted ice crystals on head, back and
tail, crystal claws. Elite: icier palette, massive crystal mane, crystal pauldrons, horn, scarred eye.
Run: blender -b --factory-startup -P ice_wolf.py -- [ice_wolf|elite_ice_wolf]
"""
import math
import os
import sys

sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from _common import *  # noqa: F401,F403
from _common import A, Act, Vector, S, C

import bmesh  # noqa: E402
import bpy  # noqa: E402
from mathutils import Matrix  # noqa: E402

EID = variant("ice_wolf")
ELITE = EID.startswith("elite_")
TINT = (0.75, 0.9, 1.0)
A.reset_scene()

if ELITE:
    FUR_W, FUR_S = "#f2f8ff", "#c6dcf4"
    PATCH, PATCH_D = "#5c86cc", "#3a62ad"
    SOCK, SOCK_D = "#2e57a6", "#1f3f80"
    EAR_O, EAR_T = "#3a62ad", "#24468c"
    EAR_IN = "#d77d98"
    EYE_IRIS, EYE_PUP = "#c8f4ff", "#1c4f9a"
    CRY_L, CRY_D = "#f0fdff", "#3d8fe6"
    CRY2_L, CRY2_D = "#d4f2ff", "#2d6fd0"
else:
    FUR_W, FUR_S = "#eef1f8", "#cdd5e6"
    PATCH, PATCH_D = "#8ea6d2", "#6f8cc4"
    SOCK, SOCK_D = "#5b7cc0", "#4762a4"
    EAR_O, EAR_T = "#6f8fca", "#4d6aa8"
    EAR_IN = "#e8849a"
    EYE_IRIS, EYE_PUP = "#3fd8ff", "#14203a"
    CRY_L, CRY_D = "#dff8ff", "#4aa6e8"
    CRY2_L, CRY2_D = "#c8eeff", "#3a8fdc"
NOSE = "#1c2030"
MOUTH, TONGUE, FANG = "#7e1d34", "#ff8798", "#ffffff"
EYE_LINE = "#101626"


# ---------------------------------------------------------------- local helpers
def xform(o, m):
    """Bake o, then apply world matrix m on top and bake again."""
    A.apply_transform(o)
    o.matrix_world = m
    A.apply_transform(o)
    return o


def frame(base, d, n):
    """4x4 with local +Z along d, local +Y toward n (orthogonalised), origin at base."""
    z = Vector(d).normalized()
    y = Vector(n) - z * Vector(n).dot(z)
    if y.length < 1e-4:
        y = Vector((0, 0, 1)) - z * z.z
        if y.length < 1e-4:
            y = Vector((0, 1, 0))
    y.normalize()
    x = y.cross(z)
    m = Matrix((x, y, z)).transposed().to_4x4()
    m.translation = Vector(base)
    return m


def tuft(name, base, d, n, L=0.1, r=0.035, flat=0.45, bend=0.25, c0=None, c1=None, sides=6):
    """Flattened, curling fur spike: built along +Z, thin along Y; tip curls toward +Y (= n)."""
    c0 = c0 or FUR_W
    c1 = c1 or c0
    bm = bmesh.new()
    rings = []
    for t in (0.0, 0.35, 0.7):
        rad = r * (1.0 - t) ** 0.75 * (1.0 + 0.25 * math.sin(math.pi * t))
        ring = []
        for i in range(sides):
            a = 2 * math.pi * i / sides
            ring.append(bm.verts.new((math.cos(a) * rad, math.sin(a) * rad * flat + bend * L * t * t, L * t)))
        rings.append(ring)
    tip = bm.verts.new((0, bend * L, L))
    for a, b in zip(rings, rings[1:]):
        for i in range(sides):
            j = (i + 1) % sides
            bm.faces.new((a[i], a[j], b[j], b[i]))
    for i in range(sides):
        bm.faces.new((rings[-1][i], rings[-1][(i + 1) % sides], tip))
    bm.faces.new(list(reversed(rings[0])))
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    o = A._from_bmesh(name, bm)
    A.shade_smooth(o)
    A.paint(o, c0)
    paint_vert_fn(o, lambda co: mix(c0, c1, min(1.0, max(0.0, co.z / L)) ** 1.6))
    return xform(o, frame(base, d, n))


def skin_tuft(name, target, center, yaw, pitch, L=0.1, r=0.035, down=0.6, lift=0.35, sink=0.012, **kw):
    """Tuft rooted on target surface at dir_from(yaw, pitch), lying along the surface flowing
    toward 'down' (blend of gravity and outward normal)."""
    p, n = surf(target, center, dir_from(yaw, pitch))
    g = Vector((0, 0, -1))
    t = g - n * g.dot(n)
    if t.length < 1e-3:
        t = Vector((0, 1, 0)) - n * n.y
    t.normalize()
    d = (t * down + n * lift).normalized()
    return tuft(name, p - n * sink, d, n, L=L, r=r, **kw)


def ice(name, base, d, r=0.04, h=0.16, mat="M_Emit", roll=0.0, sink=0.02, light=None, dark=None, sides=6):
    o = crystal(name, r=r, h=h, light=light or CRY_L, dark=dark or CRY_D, mat=mat, sides=sides)
    dd = Vector(d).normalized()
    return aim(o, Vector(base) - dd * sink, dd, roll=roll)


def surf_on(target, center, yaw, pitch):
    return surf(target, center, dir_from(yaw, pitch))


def eye(name, loc, n, w, h, narrow=1.0):
    """Wolf eye: dark rim, bright cyan (emissive) iris, pupil, two highlights."""
    up = (0, 0, 1)
    parts = []
    hh = h * narrow
    rim = A.sphere(name, r=1.0, scale=(w, 0.022, hh), color=EYE_LINE, seg=16, rings=8)
    parts.append(orient(rim, loc, n, up))
    nn = Vector(n).normalized()
    b = basis(nn, up)
    upv, side = b.col[2], b.col[0]
    ir = A.sphere(name + "_iris", r=1.0, scale=(w * 0.8, 0.018, hh * 0.84), color=EYE_IRIS, mat="M_Emit", seg=16, rings=8)
    parts.append(orient(ir, Vector(loc) - upv * hh * 0.08, nn, up, offset=0.008))
    if not ELITE:
        pu = A.sphere(name + "_pup", r=1.0, scale=(w * 0.42, 0.014, hh * 0.5), color=EYE_PUP, seg=12, rings=6)
        parts.append(orient(pu, Vector(loc) - upv * hh * 0.05, nn, up, offset=0.015))
    else:
        pu = A.sphere(name + "_pup", r=1.0, scale=(w * 0.16, 0.014, hh * 0.62), color=EYE_PUP, seg=10, rings=6)
        parts.append(orient(pu, Vector(loc), nn, up, offset=0.015))
    if narrow > 0.7:
        h1 = A.sphere(name + "_hl1", r=1.0, scale=(w * 0.3, 0.01, hh * 0.24), color="#ffffff", seg=10, rings=6)
        parts.append(orient(h1, Vector(loc) + upv * hh * 0.42 - side * w * 0.3, nn, up, offset=0.02))
        h2 = A.sphere(name + "_hl2", r=1.0, scale=(w * 0.14, 0.01, hh * 0.12), color="#ffffff", seg=8, rings=4)
        parts.append(orient(h2, Vector(loc) - upv * hh * 0.38 + side * w * 0.32, nn, up, offset=0.02))
    return parts


def surface_tube(name, target, center, pts_yp, radius, color, lift=0.004, mat="M_Toon", taper=0.4):
    pts = []
    for (yaw, pitch) in pts_yp:
        p, n = surf(target, center, dir_from(yaw, pitch))
        pts.append(tuple(p + n * lift))
    return A.tube(name, pts, radius=radius, color=color, mat=mat, seg=8, taper_end=taper)


def patch_noise(c):
    return (math.sin(c.x * 17 + 1.3) * math.sin(c.y * 13 + 0.4) + 0.6 * math.sin(c.z * 19 + c.x * 7 + 2.1)
            + 0.4 * math.sin(c.y * 29 - c.z * 11))


# ---------------------------------------------------------------- torso
HIND_C = Vector((0, 0.2, 0.38))
CHEST_C = Vector((0, -0.05, 0.42))
hind = ellipsoid("hind", (0.17, 0.2, 0.17), loc=HIND_C, color=FUR_W)
chest = ellipsoid("chest", (0.19, 0.2, 0.19), loc=CHEST_C, color=FUR_W)


def body_col(c, n, i):
    k = patch_noise(c)
    if n.z > -0.15 and k > 0.55:
        return PATCH if k < 1.1 else PATCH_D
    if n.z < -0.5:
        return FUR_S
    return FUR_W


paint_fn(hind, body_col)
paint_fn(chest, lambda c, n, i: body_col(c, n, i) if c.y > -0.05 else (FUR_S if n.z < -0.6 else FUR_W))

RUFF_C = Vector((0, -0.18, 0.5))
ruff = ellipsoid("ruff", (0.23, 0.16, 0.21), loc=RUFF_C, color=FUR_W, seg=20, rings=12)

# ---------------------------------------------------------------- head
H = Vector((0, -0.3, 0.745))
head = ellipsoid("head", (0.25, 0.22, 0.215), loc=H, color=FUR_W, seg=24, rings=14)


def head_col(c, n, i):
    if n.z > 0.45 and n.y > -0.55:
        return FUR_S
    if n.y > 0.35:
        return FUR_S
    side = abs(n.x)
    if side > 0.7 and n.z > -0.1 and n.y > -0.3:
        return PATCH
    return FUR_W


paint_fn(head, head_col)

muzzle = ellipsoid("muzzle", (0.1, 0.085, 0.062), loc=(0, -0.5, 0.668), color=FUR_W, seg=18, rings=10)
paint_fn(muzzle, lambda c, n, i: FUR_W if n.z > -0.4 else FUR_S)
nose = ellipsoid("nose", (0.036, 0.024, 0.026), loc=(0, -0.58, 0.703), color=NOSE, seg=12, rings=8)
nose_hl = ellipsoid("nose_hl", (0.012, 0.006, 0.007), loc=(0.01, -0.596, 0.717), color="#8a93ad", seg=8, rings=4)
cavity = ellipsoid("cavity", (0.072, 0.066, 0.042), loc=(0, -0.48, 0.6), color=MOUTH, seg=14, rings=8)

face = [muzzle, nose, nose_hl, cavity]
for s in (-1, 1):
    p, _n = surf(muzzle, (s * 0.048, -0.548, 0.66), (0, 0, -1))
    fg = A.cone(f"fang{s}", r=0.013 if not ELITE else 0.016, depth=0.04 if not ELITE else 0.05,
                loc=(0, 0, 0), color=FANG, seg=8)
    xform(fg, Matrix.Translation(p + Vector((0, 0, -0.012))) @ Matrix.Rotation(math.pi, 4, "X"))
    face.append(fg)

# jaw: built closed, then opened to a grin for the rest pose
JAW_P = Vector((0, -0.4, 0.628))
jaw = ellipsoid("jaw", (0.076, 0.078, 0.032), loc=(0, -0.475, 0.578), color=FUR_W, seg=16, rings=8)
paint_fn(jaw, lambda c, n, i: FUR_W if n.z < 0.3 or abs(c.y + 0.475) > 0.065 else TONGUE)
tongue = ellipsoid("tongue", (0.05, 0.055, 0.016), loc=(0, -0.48, 0.602), color=TONGUE, seg=12, rings=6)
jaw_parts = [jaw, tongue]
for s in (-1, 1):
    lf = A.cone(f"lfang{s}", r=0.009, depth=0.024, loc=(s * 0.045, -0.53, 0.612), color=FANG, seg=6)
    jaw_parts.append(lf)
open_m = Matrix.Translation(JAW_P) @ Matrix.Rotation(math.radians(16), 4, "X") @ Matrix.Translation(-JAW_P)
for o in jaw_parts:
    xform(o, open_m)

# eyes
EYE_W, EYE_H = 0.062, 0.078
eyes = []
for s in (-1, 1):
    p, n = surf_on(head, H, s * 30, 6)
    narrow = 1.0
    if ELITE:
        narrow = 0.62 if s > 0 else 0.8
    eyes += eye(f"eye{s}", p, (n + Vector((0, -0.4, 0))).normalized(), EYE_W, EYE_H, narrow=narrow)
    if ELITE:
        # heavy angled brow (menacing)
        bp, bn = surf_on(head, H, s * 28, 22)
        br = A.sphere(f"brow{s}", r=1.0, scale=(0.07, 0.03, 0.02), color=PATCH_D, seg=12, rings=6)
        orient(br, bp, bn, up=(s * -0.45, 0, 1))
        eyes.append(br)
    else:
        # pale forehead marks above the eyes (reference)
        mp, mn = surf_on(head, H, s * 14, 34)
        mk = A.sphere(f"mark{s}", r=1.0, scale=(0.022, 0.01, 0.034), color="#ffffff", seg=10, rings=6)
        orient(mk, mp, mn, up=(s * 0.3, 0.3, 1))
        face.append(mk)

if ELITE:
    # scar across the creature's left eye (+X): dark red slash + lighter healed edge
    scar = surface_tube("scar", head, H, [(14, 40), (22, 26), (31, 10), (39, -6), (45, -20)], 0.011, "#7a1424",
                        lift=0.006, taper=0.5)
    scar2 = surface_tube("scar2", head, H, [(20, 36), (27, 22), (35, 6)], 0.006, "#c0505e", lift=0.012, taper=0.3)
    face += [scar, scar2]

# ears
ears = {}
EAR_PTS = [(-0.09, 0.0), (-0.083, 0.07), (-0.055, 0.15), (-0.02, 0.225), (0.0, 0.25), (0.018, 0.22),
           (0.05, 0.15), (0.078, 0.07), (0.09, 0.0)]
for s, side in ((1, "L"), (-1, "R")):
    base, bn = surf_on(head, H, s * 44, 50)
    outer = A.extrude_shape(f"ear{side}", EAR_PTS, depth=0.04, color=EAR_O)
    A.deform(outer, lambda co: Vector((co.x, co.y - 0.035 * (co.x / 0.09) ** 2, co.z)))
    paint_vert_fn(outer, lambda co: mix(EAR_O, EAR_T, min(1.0, max(0.0, (co.z - 0.12) / 0.1))))
    inner_pts = [(x * 0.62, 0.025 + z * 0.66) for x, z in EAR_PTS]
    inner = A.extrude_shape(f"earin{side}", inner_pts, depth=0.02, loc=(0, -0.018, 0), color=EAR_IN)
    A.deform(inner, lambda co: Vector((co.x, co.y - 0.035 * (co.x / 0.09) ** 2, co.z)))
    parts = [outer, inner]
    for k, (dx, L) in enumerate([(-0.025, 0.1), (0.02, 0.085), (0.0, 0.07)]):
        parts.append(tuft(f"eartuft{side}{k}", Vector((dx, -0.03, 0.01)), (dx * 4, -0.25, 1), (0, -1, 0), L=L,
                          r=0.02, flat=0.5, bend=0.3, c0=FUR_W, c1="#ffffff"))
    m = (Matrix.Translation(base - bn * 0.03) @ Matrix.Rotation(math.radians(s * 14), 4, "Z")
         @ Matrix.Rotation(math.radians(s * 20), 4, "Y") @ Matrix.Rotation(math.radians(-8), 4, "X"))
    for o in parts:
        xform(o, m)
    ears[side] = (parts, base)

# cheek + head fluff tufts (shaped spikes)
head_fluff = []
for s in (-1, 1):
    for k, (yaw, pitch, L) in enumerate([(78, -8, 0.13), (92, -22, 0.15), (74, -34, 0.12), (100, 6, 0.1), (62, -44, 0.09)]):
        p, n = surf_on(head, H, s * yaw, pitch)
        d = (n * 0.8 + Vector((0, 0.35, -0.45))).normalized()
        head_fluff.append(tuft(f"cheek{s}_{k}", p - n * 0.03, d, Vector((0, 0, 1)), L=L, r=0.045, flat=0.4,
                               bend=-0.15, c0=FUR_W, c1="#ffffff" if not ELITE else "#e8f4ff"))
    for k, (yaw, pitch) in enumerate([(14, 62), (30, 72)]):
        head_fluff.append(skin_tuft(f"crown{s}_{k}", head, H, s * yaw, pitch, L=0.08, r=0.03, down=-0.2, lift=0.8,
                                    c0=FUR_S, c1=FUR_W))
for k, (yaw, pitch) in enumerate([(0, 30), (0, 18)]):
    pass
head_fluff.append(skin_tuft("nape", head, H, 180, 30, L=0.12, r=0.05, down=0.8, lift=0.4, c0=FUR_S, c1=FUR_W))

# head crystals (crest bone)
crest = []
CREST_P, cn = surf_on(head, H, 0, 74)
CREST_P = CREST_P + Vector((0, 0.04, 0))
for k, (dx, dy, tilt_x, tilt_y, r, h, mat) in enumerate([
        (0.0, 0.0, 0.0, 0.25, 0.05, 0.3, "M_Emit"),
        (0.05, 0.03, 0.55, 0.35, 0.036, 0.19, "M_Clear"),
        (-0.05, 0.03, -0.55, 0.35, 0.036, 0.2, "M_Clear"),
        (0.035, -0.04, 0.4, -0.1, 0.028, 0.13, "M_Emit"),
        (-0.03, 0.08, -0.25, 0.75, 0.03, 0.15, "M_Emit")]):
    bp, bn = surf(head, H, Vector((dx, dy, 0.215)) + (CREST_P - H) * 0 + Vector((0, 0, 0)) - Vector((0, 0, 0)))
    base = Vector(surf(head, H, (Vector((dx, 0.04 + dy, 0.22)) ).normalized())[0])
    crest.append(ice(f"crest{k}", base, (tilt_x, tilt_y, 1.0), r=r, h=h, mat=mat, roll=k * 17,
                     light=CRY_L if mat == "M_Emit" else CRY2_L, dark=CRY_D if mat == "M_Emit" else CRY2_D))
if ELITE:
    hp, hn = surf_on(head, H, 0, 36)
    horn = ice("horn", hp, (0, -0.55, 1.0), r=0.034, h=0.22, mat="M_Emit", sink=0.02)
    crest.append(horn)

# ---------------------------------------------------------------- ruff (layered fur spikes) + ruff crystals
ruff_parts = [ruff]
k = 0
for (pitch, yaws, L, r, down) in [
        (-35, range(-150, 151, 30), 0.17, 0.06, 0.9),
        (-5, list(range(-165, -59, 26)) + list(range(60, 166, 26)), 0.16, 0.055, 0.7),
        (25, list(range(-150, -89, 30)) + list(range(90, 151, 30)), 0.13, 0.05, 0.5)]:
    for yaw in yaws:
        jit = (k * 37 % 11) / 11.0
        ruff_parts.append(skin_tuft(f"ruff{k}", ruff, RUFF_C, yaw + jit * 8 - 4, pitch, L=L * (0.9 + 0.2 * jit), r=r,
                                    down=down, lift=0.5, c0=FUR_W, c1="#ffffff" if jit > 0.5 else FUR_S))
        k += 1
# chest bib spikes pointing down
for j, (dx, L) in enumerate([(-0.09, 0.15), (-0.03, 0.18), (0.03, 0.18), (0.09, 0.15), (0.0, 0.14)]):
    p, n = surf(ruff, RUFF_C + Vector((dx, 0, -0.06)), (0, -1, -0.4))
    ruff_parts.append(tuft(f"bib{j}", p - n * 0.02, (dx * 1.5, -0.25, -1), n, L=L, r=0.05, flat=0.45, bend=0.2,
                           c0=FUR_W, c1="#ffffff"))

ruff_cry = []
cry_spots = [(-70, 30, 0.11), (-95, 10, 0.13), (-115, -15, 0.1), (-80, -30, 0.09), (-130, 20, 0.08)]
for s in (-1, 1):
    for j, (yaw, pitch, h) in enumerate(cry_spots):
        p, n = surf_on(ruff, RUFF_C, s * -yaw, pitch)
        d = (n + Vector((0, 0.25, 0.35))).normalized()
        mat = "M_Emit" if j % 2 == 0 else "M_Clear"
        ruff_cry.append(ice(f"rcry{s}_{j}", p, d, r=h * 0.26, h=h, mat=mat, roll=j * 23))

if ELITE:
    # massive ice-crystal mane ringing the neck and shoulders
    mi = 0
    for (pitch, step, h0, out) in [(15, 24, 0.28, 0.55), (-15, 30, 0.2, 0.8), (40, 40, 0.22, 0.4)]:
        for yaw in range(-168, 169, step):
            if abs(yaw) < 45 and pitch < 30:
                continue
            jit = (mi * 53 % 13) / 13.0
            p, n = surf_on(ruff, RUFF_C, yaw + jit * 10 - 5, pitch)
            d = (n * out + Vector((0, 0.45, 0.75))).normalized()
            mat = "M_Emit" if mi % 3 != 1 else "M_Clear"
            hh = h0 * (0.75 + 0.5 * jit)
            ruff_cry.append(ice(f"mane{mi}", p, d, r=hh * 0.22, h=hh, mat=mat, roll=mi * 19, sink=0.03,
                                light=CRY_L if mat == "M_Emit" else CRY2_L, dark=CRY_D if mat == "M_Emit" else CRY2_D))
            mi += 1

# dorsal crystals (shoulders/back) on 'dorsal' bone
dorsal = []
dors = [(0.0, -0.02, 0.18, 0.045), (0.06, 0.06, 0.12, 0.034), (-0.06, 0.08, 0.13, 0.034), (0.0, 0.16, 0.1, 0.03)]
if ELITE:
    dors = [(0.0, -0.04, 0.3, 0.06), (0.07, 0.03, 0.22, 0.048), (-0.07, 0.05, 0.22, 0.048), (0.0, 0.12, 0.24, 0.05),
            (0.05, 0.2, 0.17, 0.04), (-0.05, 0.22, 0.17, 0.04), (0.0, 0.3, 0.15, 0.036)]
for j, (dx, dy, h, r) in enumerate(dors):
    tgt = chest if dy < 0.1 else hind
    cc = CHEST_C if dy < 0.1 else HIND_C
    p, n = surf(tgt, Vector((dx, dy, cc.z)), (0, 0, 1))
    d = (Vector((dx * 3, 0.55, 1.0))).normalized()
    mat = "M_Emit" if j % 2 == 0 else "M_Clear"
    dorsal.append(ice(f"dors{j}", p, d, r=r, h=h, mat=mat, roll=j * 31, sink=0.03))

# body fluff along back / sides
body_fluff = []
for j, (yaw, pitch, L) in enumerate([(120, 40, 0.1), (-120, 40, 0.1), (150, 20, 0.11), (-150, 20, 0.11), (100, 0, 0.09),
                                     (-100, 0, 0.09), (180, -20, 0.09)]):
    body_fluff.append(skin_tuft(f"hfluff{j}", hind, HIND_C, yaw, pitch, L=L, r=0.04, down=0.6, lift=0.4,
                                c0=FUR_W, c1=FUR_S))
for j, (yaw, pitch) in enumerate([(-170, -50), (170, -50), (180, -55)]):
    body_fluff.append(skin_tuft(f"belly{j}", chest, CHEST_C + Vector((0, 0.08, 0)), yaw - 180, pitch, L=0.09, r=0.04,
                                down=0.9, lift=0.3, c0=FUR_W, c1=FUR_S))


# ---------------------------------------------------------------- legs
def sock_col(z_cut):
    return lambda c, n, i: (SOCK if c.z < z_cut else FUR_W) if n.z > -0.7 else SOCK_D


def paw(name, ctr, s, color=None):
    color = color or SOCK
    p = ellipsoid(name, (0.07, 0.085, 0.048), loc=ctr, color=color, seg=14, rings=8)
    A.deform(p, lambda co: Vector((co.x, co.y, max(co.z, ctr[2] - 0.042))))
    paint_fn(p, lambda c, n, i: SOCK_D if n.z < -0.6 else color)
    out = [p]
    for k, dx in enumerate((-0.04, 0.0, 0.04)):
        base = Vector((ctr[0] + dx, ctr[1] - 0.065, ctr[2] + 0.005))
        out.append(ice(f"{name}_claw{k}", base, (dx * 2.5, -1.0, -0.55), r=0.017, h=0.065, mat="M_Emit", roll=10, sink=0.0))
    return out


legs = {}
for s, side in ((1, "L"), (-1, "R")):
    # front
    sh = Vector((s * 0.13, -0.1, 0.4))
    wr = Vector((s * 0.145, -0.17, 0.15))
    upper = A.tube(f"fleg{side}", [tuple(sh + Vector((0, 0, 0.02))), tuple(sh.lerp(wr, 0.5) + Vector((0, 0.01, 0))),
                                   tuple(wr)], radius=0.062, color=FUR_W, taper_end=0.82)
    paint_fn(upper, lambda c, n, i: PATCH if (n.x * s > 0.5 and patch_noise(c) > 0.4) else FUR_W)
    elbow = tuft(f"elbow{side}", sh + Vector((s * 0.02, 0.05, -0.12)), (s * 0.2, 0.8, -0.6), (s * 0.5, 0.5, 0),
                 L=0.09, r=0.035, c0=FUR_W, c1=FUR_S)
    upper_parts = [upper, elbow]
    lower = A.tube(f"fsock{side}", [tuple(wr + Vector((0, 0.005, 0.025))), tuple(Vector((s * 0.15, -0.19, 0.05)))],
                   radius=0.054, color=SOCK, taper_end=1.05)
    paint_fn(lower, lambda c, n, i: SOCK)
    lower_parts = [lower] + paw(f"fpaw{side}", (s * 0.15, -0.215, 0.045), s)
    for k, a in enumerate((-60, 0, 60, 180)):
        d = Vector((math.sin(math.radians(a)) * s, -math.cos(math.radians(a)), 0))
        lower_parts.append(tuft(f"fcuff{side}{k}", wr + d * 0.045 + Vector((0, 0, 0.04)), (d.x * 0.35, d.y * 0.35, -1),
                                d, L=0.07, r=0.03, flat=0.5, bend=0.25, c0=FUR_W, c1="#ffffff"))
    if ELITE:
        # crystal pauldron: overlapping flat crystal plates on the shoulder
        for k, (yaw, pitch, h, r) in enumerate([(0, 30, 0.14, 0.07), (25, 5, 0.12, 0.06), (-25, 5, 0.12, 0.06),
                                                (0, -20, 0.1, 0.05)]):
            dvec = Vector((s, 0, 0))
            dvec = (Matrix.Rotation(math.radians(pitch), 3, Vector((0, -s, 0))) @
                    Matrix.Rotation(math.radians(yaw), 3, "Z") @ dvec)
            base = sh + Vector((s * 0.05, -0.02, -0.01)) + dvec * 0.03
            plate = ice(f"pauld{side}{k}", base, (dvec + Vector((0, 0.15, 0.55))).normalized(), r=r, h=h,
                        mat="M_Emit" if k % 2 == 0 else "M_Clear", sides=5, sink=0.0, roll=k * 20,
                        light=CRY_L, dark=CRY_D)
            A.deform(plate, lambda co: co)
            upper_parts.append(plate)
    legs[f"leg_f.{side}"] = (upper_parts, sh)
    legs[f"paw_f.{side}"] = (lower_parts, wr)

    # hind
    hp = Vector((s * 0.13, 0.24, 0.38))
    hk = Vector((s * 0.145, 0.31, 0.16))
    thigh = ellipsoid(f"thigh{side}", (0.08, 0.125, 0.125), loc=(s * 0.135, 0.25, 0.3), color=FUR_W, seg=16, rings=10)
    paint_fn(thigh, lambda c, n, i: (PATCH if patch_noise(c) > 0.3 and n.z > -0.2 else FUR_W)
             if c.z > 0.21 else SOCK)
    shank = A.tube(f"shank{side}", [(s * 0.14, 0.29, 0.25), tuple(hk + Vector((0, 0, 0.0)))], radius=0.052, color=SOCK,
                   taper_end=0.95)
    paint_fn(shank, lambda c, n, i: FUR_W if c.z > 0.21 else SOCK)
    hfl = tuft(f"hfur{side}", Vector((s * 0.14, 0.33, 0.33)), (s * 0.1, 1.0, -0.5), (0, 1, 0.3), L=0.1, r=0.04,
               c0=FUR_W, c1=FUR_S)
    hupper = [thigh, shank, hfl]
    hlow = A.tube(f"hsock{side}", [tuple(hk + Vector((0, 0, 0.02))), (s * 0.145, 0.29, 0.05)], radius=0.05,
                  color=SOCK, taper_end=1.05)
    hlower = [hlow] + paw(f"hpaw{side}", (s * 0.145, 0.255, 0.045), s)
    # ankle crystal tuft (reference: crystal cluster on the hind leg)
    for k, (dx, dy, dz, h) in enumerate([(s * 0.6, 0.6, 0.6, 0.09), (s * 0.9, 0.2, 0.5, 0.07), (s * 0.4, 0.9, 0.2, 0.06)]):
        hlower.append(ice(f"ankle{side}{k}", hk + Vector((s * 0.03, 0.03, -0.01)), (dx, dy, dz), r=h * 0.28, h=h,
                          mat="M_Emit" if k != 1 else "M_Clear", roll=k * 40, sink=0.0))
    legs[f"leg_h.{side}"] = (hupper, hp)
    legs[f"paw_h.{side}"] = (hlower, hk)

# ---------------------------------------------------------------- tail (3 bones)
T1 = Vector((0, 0.36, 0.46))
T2 = Vector((0, 0.47, 0.58))
T3 = Vector((0, 0.55, 0.72))
tail = {"tail1": [], "tail2": [], "tail3": []}
seg_c = [(Vector((0, 0.42, 0.52)), (0.07, 0.085, 0.075), "tail1"),
         (Vector((0, 0.52, 0.65)), (0.1, 0.1, 0.11), "tail2"),
         (Vector((0, 0.585, 0.8)), (0.1, 0.09, 0.12), "tail3")]
for j, (c, rad, bone) in enumerate(seg_c):
    e = ellipsoid(f"tailseg{j}", rad, loc=c, color=FUR_W, seg=16, rings=10)
    if j == 0:
        paint_fn(e, lambda cc, n, i: PATCH)
    elif j == 1:
        paint_fn(e, lambda cc, n, i: PATCH if n.y > 0.3 and n.z < 0.5 else FUR_W)
    tail[bone].append(e)
    nt = 6 if j else 4
    for k in range(nt):
        a = 2 * math.pi * (k + 0.5 * j) / nt
        out = Vector((math.cos(a), math.sin(a) * 0.6 + 0.6, math.sin(a) * 0.4 + 0.2)).normalized()
        base = c + Vector((out.x * rad[0], out.y * rad[1] * 0.6, out.z * rad[2] * 0.5))
        d = (out * 0.8 + Vector((0, 0.45, 0.6))).normalized()
        col1 = PATCH if j == 0 else ("#ffffff" if k % 2 else FUR_S)
        tail[bone].append(tuft(f"tailtuft{j}_{k}", base, d, out, L=0.12 + 0.03 * j, r=0.045, flat=0.45, bend=0.25,
                               c0=FUR_W if j else PATCH, c1=col1))
# tail tip fluff + crystals
tail["tail3"].append(tuft("tailtip", Vector((0, 0.6, 0.88)), (0, 0.35, 1), (0, 1, 0), L=0.16, r=0.06, bend=0.3,
                          c0=FUR_W, c1="#ffffff"))
for k, (dx, dy, h, r, mat) in enumerate([(0.0, 0.3, 0.3 if not ELITE else 0.4, 0.05, "M_Emit"),
                                          (0.6, 0.5, 0.18, 0.035, "M_Clear"),
                                          (-0.6, 0.5, 0.2, 0.035, "M_Clear"),
                                          (0.25, 0.9, 0.14, 0.03, "M_Emit")]):
    base = Vector((dx * 0.05, 0.6 + 0.03 * abs(dx), 0.82))
    tail["tail3"].append(ice(f"tailcry{k}", base, (dx, dy, 1.0), r=r, h=h, mat=mat, roll=k * 29, sink=0.0,
                             light=CRY_L if mat == "M_Emit" else CRY2_L, dark=CRY_D if mat == "M_Emit" else CRY2_D))
if ELITE:
    for k, (dx, dy, dz, h) in enumerate([(0.9, 0.4, 0.5, 0.14), (-0.9, 0.4, 0.5, 0.14), (0.0, 1.0, 0.2, 0.12)]):
        tail["tail2"].append(ice(f"tail2cry{k}", Vector((0, 0.53, 0.68)) + Vector((dx, dy * 0.5, 0)) * 0.07,
                                 (dx, dy, dz), r=h * 0.25, h=h, mat="M_Emit", roll=k * 33, sink=0.0))

# ---------------------------------------------------------------- rig
NECK_P = Vector((0, -0.16, 0.54))
HEAD_P = Vector((0, -0.27, 0.62))
rig = make_rig([
    ("root", (0, 0, 0), None),
    ("spine1", (0, 0.2, 0.38), "root"),
    ("spine2", (0, 0.02, 0.42), "spine1"),
    ("dorsal", (0, -0.04, 0.58), "spine2"),
    ("neck", tuple(NECK_P), "spine2"),
    ("head", tuple(HEAD_P), "neck"),
    ("jaw", tuple(JAW_P), "head"),
    ("eyes", (0, -0.48, 0.76), "head"),
    ("crest", tuple(CREST_P), "head"),
    ("ear.L", tuple(ears["L"][1]), "head"),
    ("ear.R", tuple(ears["R"][1]), "head"),
    ("leg_f.L", tuple(legs["leg_f.L"][1]), "spine2"),
    ("paw_f.L", tuple(legs["paw_f.L"][1]), "leg_f.L"),
    ("leg_f.R", tuple(legs["leg_f.R"][1]), "spine2"),
    ("paw_f.R", tuple(legs["paw_f.R"][1]), "leg_f.R"),
    ("leg_h.L", tuple(legs["leg_h.L"][1]), "spine1"),
    ("paw_h.L", tuple(legs["paw_h.L"][1]), "leg_h.L"),
    ("leg_h.R", tuple(legs["leg_h.R"][1]), "spine1"),
    ("paw_h.R", tuple(legs["paw_h.R"][1]), "leg_h.R"),
    ("tail1", tuple(T1), "spine1"),
    ("tail2", tuple(T2), "tail1"),
    ("tail3", tuple(T3), "tail2"),
])
parts = {
    "spine1": [hind] + body_fluff,
    "spine2": [chest] + ruff_parts + ruff_cry,
    "dorsal": dorsal,
    "head": [head] + face + head_fluff,
    "jaw": jaw_parts,
    "eyes": eyes,
    "crest": crest,
    "ear.L": ears["L"][0],
    "ear.R": ears["R"][0],
}
for b, (ps, _p) in legs.items():
    parts[b] = ps
parts.update(tail)
body_obj = A.skin(parts, rig)

LEGS_F = (("leg_f.L", "paw_f.L", 1), ("leg_f.R", "paw_f.R", -1))
LEGS_H = (("leg_h.L", "paw_h.L", 1), ("leg_h.R", "paw_h.R", -1))

# ---------------------------------------------------------------- animation
# Idle (48f): breathing, tail wag with phase lag, ear twitches, blink, panting grin
with Act(rig, "Idle", 48) as a:
    a.loop_r("spine2", 4, lambda t: (-1.5 * S(t), 0, 0))
    a.loop_r("spine1", 4, lambda t: (1.0 * S(t), 0, 0))
    a.loop_l("spine2", 4, lambda t: (0, 0, 0.006 * S(t)))
    a.loop_r("neck", 4, lambda t: (2 * S(t, -0.1), 0, 0))
    a.loop_r("head", 8, lambda t: (2.5 * S(t, -0.2), 3 * S(t, 0.1), 5 * S(t, 0.35)))
    a.loop_r("jaw", 8, lambda t: (3 + 3 * S(4 * t), 0, 0))
    a.loop_r("tail1", 8, lambda t: (3 * S(t), 0, 14 * S(2 * t)))
    a.loop_r("tail2", 8, lambda t: (4 * S(t, -0.1), 0, 16 * S(2 * t, -0.12)))
    a.loop_r("tail3", 8, lambda t: (5 * S(t, -0.2), 0, 20 * S(2 * t, -0.25)))
    a.keys_r("ear.L", [(0, (0, 0, 0)), (14, (0, 0, 0)), (16, (-14, 16, 10)), (18, (4, -4, -3)), (20, (-6, 8, 4)),
                       (23, (0, 0, 0)), (48, (0, 0, 0))])
    a.keys_r("ear.R", [(0, (0, 0, 0)), (33, (0, 0, 0)), (35, (-14, -16, -10)), (37, (4, 4, 3)), (40, (0, 0, 0)),
                       (48, (0, 0, 0))])
    a.keys_s("eyes", [(0, 1), (26, 1), (28, (1.05, 1, 0.1)), (30, 1), (48, 1)])
    a.loop_s("crest", 4, lambda t: (1 + 0.03 * S(t), 1 + 0.03 * S(t), 1 + 0.03 * S(t)))
    for leg, pw, sg in LEGS_F + LEGS_H:
        a.loop_r(leg, 4, lambda t: (0.8 * S(t), 0, 0))

# Run (20f): rotary gallop in place
with Act(rig, "Run", 20) as a:
    N = 10
    a.loop_l("root", N, lambda t: (0, 0, 0.035 * (1 + S(t, 0.05))))
    a.loop_r("root", N, lambda t: (-4 * S(t, -0.05), 0, 0))
    a.loop_r("spine1", N, lambda t: (-7 * S(t, 0.25), 0, 0))
    a.loop_r("spine2", N, lambda t: (9 * S(t, 0.25), 0, 0))
    a.loop_r("neck", N, lambda t: (-6 * S(t, 0.15) + 4, 0, 0))
    a.loop_r("head", N, lambda t: (5 * S(t, -0.05) + 6, 0, 0))
    a.loop_r("jaw", N, lambda t: (8 + 6 * S(t, 0.1), 0, 0))
    for leg, pw, sg in LEGS_F:
        ph = 0.0 if sg > 0 else 0.09
        a.loop_r(leg, N, lambda t, ph=ph: (-38 * S(t, ph), 0, 0))
        a.loop_r(pw, N, lambda t, ph=ph: (30 * (1 + C(t, ph + 0.1)) * 0.5 + 10 * max(0.0, C(t, ph + 0.1)), 0, 0))
    for leg, pw, sg in LEGS_H:
        ph = 0.5 if sg > 0 else 0.59
        a.loop_r(leg, N, lambda t, ph=ph: (-34 * S(t, ph), 0, 0))
        a.loop_r(pw, N, lambda t, ph=ph: (-30 * (1 + C(t, ph + 0.1)) * 0.5, 0, 0))
    a.loop_r("tail1", N, lambda t: (-38 + 6 * S(t, -0.1), 0, 5 * S(t)))
    a.loop_r("tail2", N, lambda t: (-18 + 9 * S(t, -0.2), 0, 7 * S(t, -0.1)))
    a.loop_r("tail3", N, lambda t: (-14 + 12 * S(t, -0.3), 0, 9 * S(t, -0.2)))
    a.loop_r("ear.L", N, lambda t: (-26 + 6 * S(t, -0.2), -8, 0))
    a.loop_r("ear.R", N, lambda t: (-26 + 6 * S(t, -0.2), 8, 0))

# Attack (26f, impact f10): crouch -> pounce lunge with jaw snap -> land/recover
with Act(rig, "Attack", 26) as a:
    a.keys_l("root", [(0, (0, 0, 0)), (5, (0, 0.06, -0.06)), (7, (0, 0.04, -0.07)), (9, (0, -0.32, 0.12)),
                      (10, (0, -0.4, 0.08)), (13, (0, -0.44, 0.0)), (16, (0, -0.42, -0.03)), (20, (0, -0.2, 0.0)),
                      (26, (0, 0, 0))])
    a.keys_r("root", [(0, (0, 0, 0)), (5, (4, 0, 0)), (7, (6, 0, 0)), (9, (-10, 0, 0)), (10, (6, 0, 0)), (13, (8, 0, 0)),
                      (16, (2, 0, 0)), (26, (0, 0, 0))])
    a.keys_r("spine2", [(0, (0, 0, 0)), (5, (8, 0, 0)), (9, (-10, 0, 0)), (10, (6, 0, 0)), (16, (2, 0, 0)), (26, (0, 0, 0))])
    a.keys_r("spine1", [(0, (0, 0, 0)), (5, (-6, 0, 0)), (9, (6, 0, 0)), (12, (-3, 0, 0)), (26, (0, 0, 0))])
    a.keys_r("neck", [(0, (0, 0, 0)), (5, (12, 0, 0)), (8, (-10, 0, 0)), (10, (8, 0, 0)), (14, (4, 0, 0)), (26, (0, 0, 0))])
    a.keys_r("head", [(0, (0, 0, 0)), (5, (10, 0, 0)), (8, (-22, 0, 0)), (10, (14, 0, 0)), (12, (18, 0, 6)),
                      (16, (4, 0, -4)), (26, (0, 0, 0))])
    a.keys_r("jaw", [(0, (0, 0, 0)), (5, (-6, 0, 0)), (8, (34, 0, 0)), (9, (36, 0, 0)), (10, (-14, 0, 0)),
                     (13, (-12, 0, 0)), (18, (4, 0, 0)), (26, (0, 0, 0))])
    for leg, pw, sg in LEGS_F:
        a.keys_r(leg, [(0, (0, 0, 0)), (5, (-18, 0, 0)), (7, (-12, 0, 0)), (9, (-70, 0, 0)), (10, (-62, 0, 0)),
                       (13, (-20, 0, 0)), (16, (-6, 0, 0)), (26, (0, 0, 0))])
        a.keys_r(pw, [(0, (0, 0, 0)), (5, (30, 0, 0)), (7, (24, 0, 0)), (9, (-10, 0, 0)), (10, (-20, 0, 0)),
                      (13, (10, 0, 0)), (16, (6, 0, 0)), (26, (0, 0, 0))])
    for leg, pw, sg in LEGS_H:
        a.keys_r(leg, [(0, (0, 0, 0)), (5, (-22, 0, 0)), (7, (-26, 0, 0)), (9, (48, 0, 0)), (10, (55, 0, 0)),
                       (13, (30, 0, 0)), (16, (8, 0, 0)), (26, (0, 0, 0))])
        a.keys_r(pw, [(0, (0, 0, 0)), (5, (-30, 0, 0)), (7, (-34, 0, 0)), (9, (20, 0, 0)), (10, (25, 0, 0)),
                      (13, (-10, 0, 0)), (26, (0, 0, 0))])
    a.keys_r("tail1", [(0, (0, 0, 0)), (5, (12, 0, 10)), (9, (-50, 0, 0)), (12, (-45, 0, -6)), (16, (-20, 0, 8)),
                       (26, (0, 0, 0))])
    a.keys_r("tail2", [(0, (0, 0, 0)), (6, (10, 0, 12)), (10, (-30, 0, 0)), (14, (-20, 0, -10)), (19, (-5, 0, 8)),
                       (26, (0, 0, 0))])
    a.keys_r("tail3", [(0, (0, 0, 0)), (7, (10, 0, 14)), (11, (-25, 0, 0)), (15, (-15, 0, -12)), (21, (0, 0, 8)),
                       (26, (0, 0, 0))])
    for ear, sg in (("ear.L", 1), ("ear.R", -1)):
        a.keys_r(ear, [(0, (0, 0, 0)), (5, (-30, -sg * 10, 0)), (10, (-40, -sg * 12, 0)), (14, (-10, 0, 0)),
                       (18, (6, sg * 4, 0)), (26, (0, 0, 0))])
    a.keys_s("eyes", [(0, 1), (5, (1.1, 1, 0.55)), (9, (1.15, 1, 1.15)), (12, 1), (26, 1)])
    a.keys_s("crest", [(0, 1), (8, 1.0), (10, 1.15), (14, 1.0), (26, 1)])

# Cast (36f, release f22): gather -> head thrown back in a howl, jaw open, crystals flare
with Act(rig, "Cast", 36) as a:
    a.keys_l("root", [(0, (0, 0, 0)), (8, (0, 0.02, -0.04)), (16, (0, 0.02, -0.03)), (22, (0, 0, 0.03)),
                      (30, (0, 0, 0.01)), (36, (0, 0, 0))])
    a.keys_r("spine2", [(0, (0, 0, 0)), (8, (8, 0, 0)), (16, (-6, 0, 0)), (22, (-14, 0, 0)), (30, (-10, 0, 0)),
                        (36, (0, 0, 0))])
    a.keys_r("spine1", [(0, (0, 0, 0)), (8, (-3, 0, 0)), (22, (4, 0, 0)), (30, (3, 0, 0)), (36, (0, 0, 0))])
    a.keys_r("neck", [(0, (0, 0, 0)), (8, (14, 0, 0)), (16, (-16, 0, 0)), (22, (-26, 0, 0)), (30, (-24, 0, 0)),
                      (36, (0, 0, 0))])
    a.keys_r("head", [(0, (0, 0, 0)), (8, (14, 0, 0)), (16, (-22, 0, 0)), (22, (-34, 0, 0)), (26, (-32, 0, 3)),
                      (30, (-30, 0, -3)), (36, (0, 0, 0))])
    a.keys_r("jaw", [(0, (0, 0, 0)), (8, (-10, 0, 0)), (16, (14, 0, 0)), (22, (36, 0, 0)), (24, (32, 0, 0)),
                     (26, (36, 0, 0)), (28, (32, 0, 0)), (30, (34, 0, 0)), (36, (0, 0, 0))])
    a.keys_s("crest", [(0, 1), (8, 0.9), (16, 1.05), (22, 1.45), (26, 1.3), (30, 1.32), (36, 1)])
    a.keys_s("dorsal", [(0, 1), (8, 0.92), (22, 1.3), (28, 1.18), (36, 1)])
    a.keys_s("tail3", [(0, 1), (8, 0.95), (22, 1.25), (28, 1.12), (36, 1)])
    a.keys_r("tail1", [(0, (0, 0, 0)), (8, (14, 0, 0)), (22, (-18, 0, 0)), (30, (-12, 0, 0)), (36, (0, 0, 0))])
    a.keys_r("tail2", [(0, (0, 0, 0)), (10, (10, 0, 0)), (24, (-14, 0, 0)), (32, (-8, 0, 0)), (36, (0, 0, 0))])
    a.keys_r("tail3", [(0, (0, 0, 0)), (12, (10, 0, 0)), (26, (-16, 0, 0)), (33, (-6, 0, 0)), (36, (0, 0, 0))])
    for ear, sg in (("ear.L", 1), ("ear.R", -1)):
        a.keys_r(ear, [(0, (0, 0, 0)), (8, (-18, -sg * 8, 0)), (22, (-28, sg * 6, 0)), (30, (-24, sg * 4, 0)),
                       (36, (0, 0, 0))])
    a.keys_s("eyes", [(0, 1), (8, (1.05, 1, 0.5)), (16, (1.05, 1, 0.25)), (22, (1.05, 1, 0.12)), (30, (1.05, 1, 0.15)),
                      (34, 1), (36, 1)])
    for leg, pw, sg in LEGS_F:
        a.keys_r(leg, [(0, (0, 0, 0)), (8, (-6, 0, 0)), (22, (-12, 0, 0)), (30, (-10, 0, 0)), (36, (0, 0, 0))])
        a.keys_r(pw, [(0, (0, 0, 0)), (8, (6, 0, 0)), (22, (10, 0, 0)), (36, (0, 0, 0))])
    for leg, pw, sg in LEGS_H:
        a.keys_r(leg, [(0, (0, 0, 0)), (8, (-8, 0, 0)), (22, (6, 0, 0)), (36, (0, 0, 0))])

# Hit (12f): flinch back, head jerks, ears pin, eyes squeeze
with Act(rig, "Hit", 12) as a:
    a.keys_l("root", [(0, (0, 0, 0)), (2, (0, 0.09, 0.0)), (6, (0, 0.05, 0)), (12, (0, 0, 0))])
    a.keys_r("root", [(0, (0, 0, 0)), (2, (-6, 0, 0)), (6, (2, 0, 0)), (12, (0, 0, 0))])
    a.keys_r("spine2", [(0, (0, 0, 0)), (2, (-10, 4, 0)), (6, (4, -1, 0)), (12, (0, 0, 0))])
    a.keys_r("neck", [(0, (0, 0, 0)), (2, (-14, 0, 0)), (6, (6, 0, 0)), (12, (0, 0, 0))])
    a.keys_r("head", [(0, (0, 0, 0)), (2, (-16, -8, 10)), (5, (8, 2, -3)), (8, (-3, 0, 0)), (12, (0, 0, 0))])
    a.keys_r("jaw", [(0, (0, 0, 0)), (2, (14, 0, 0)), (6, (-6, 0, 0)), (12, (0, 0, 0))])
    for ear, sg in (("ear.L", 1), ("ear.R", -1)):
        a.keys_r(ear, [(0, (0, 0, 0)), (2, (-38, -sg * 14, 0)), (7, (-15, 0, 0)), (12, (0, 0, 0))])
    a.keys_r("tail1", [(0, (0, 0, 0)), (2, (25, 0, 0)), (6, (-6, 0, 0)), (12, (0, 0, 0))])
    a.keys_r("tail2", [(0, (0, 0, 0)), (3, (20, 0, 0)), (8, (-5, 0, 0)), (12, (0, 0, 0))])
    a.keys_r("tail3", [(0, (0, 0, 0)), (4, (18, 0, 0)), (9, (-4, 0, 0)), (12, (0, 0, 0))])
    a.keys_s("eyes", [(0, 1), (1, (1.15, 1, 0.12)), (8, (1.1, 1, 0.2)), (12, 1)])
    for leg, pw, sg in LEGS_F:
        a.keys_r(leg, [(0, (0, 0, 0)), (2, (14, 0, 0)), (6, (-4, 0, 0)), (12, (0, 0, 0))])
    for leg, pw, sg in LEGS_H:
        a.keys_r(leg, [(0, (0, 0, 0)), (2, (-10, 0, 0)), (6, (3, 0, 0)), (12, (0, 0, 0))])

# Die (32f): stagger, buckle, collapse onto its right side, legs limp, eyes shut (last pose held)
with Act(rig, "Die", 32) as a:
    a.keys_r("root", [(0, (0, 0, 0)), (6, (6, 6, 0)), (12, (10, -12, 0)), (18, (8, -55, 0)), (22, (4, -92, 0)),
                      (25, (4, -84, 0)), (28, (4, -89, 0)), (32, (4, -88, 0))])
    a.keys_l("root", [(0, (0, 0, 0)), (6, (0, 0.03, -0.02)), (12, (0, 0.04, -0.08)), (18, (0.08, 0.04, -0.02)),
                      (22, (0.3, 0.04, 0.18)), (25, (0.3, 0.04, 0.2)), (28, (0.3, 0.04, 0.18)), (32, (0.3, 0.04, 0.185))])
    a.keys_r("spine2", [(0, (0, 0, 0)), (6, (-8, 0, 0)), (12, (10, 0, 0)), (22, (6, 0, 0)), (32, (6, 0, 0))])
    a.keys_r("neck", [(0, (0, 0, 0)), (6, (-14, 0, 0)), (12, (20, 0, 0)), (20, (6, -10, 0)), (24, (10, -18, 0)),
                      (27, (8, -14, 0)), (32, (8, -16, 0))])
    a.keys_r("head", [(0, (0, 0, 0)), (6, (-12, 0, 8)), (12, (18, 0, -6)), (22, (6, -14, 0)), (26, (8, -10, 0)),
                      (32, (8, -12, 0))])
    a.keys_r("jaw", [(0, (0, 0, 0)), (6, (20, 0, 0)), (14, (4, 0, 0)), (24, (14, 0, 0)), (32, (12, 0, 0))])
    for leg, pw, sg in LEGS_F + LEGS_H:
        front = leg.startswith("leg_f")
        top = sg > 0  # left legs end up on top after rolling onto the right side
        a.keys_r(leg, [(0, (0, 0, 0)), (12, (12 if front else -12, 0, 0)),
                       (22, ((-25 if front else 25), (24 if top else -8), 0)),
                       (25, ((-30 if front else 30), (30 if top else -4), 0)),
                       (32, ((-28 if front else 28), (28 if top else -5), 0))])
        a.keys_r(pw, [(0, (0, 0, 0)), (12, (25 if front else -25, 0, 0)), (24, (15 if front else -15, 10 if top else 0, 0)),
                      (32, (18 if front else -18, 12 if top else 0, 0))])
    a.keys_r("tail1", [(0, (0, 0, 0)), (12, (20, 0, 0)), (24, (-40, 10, 0)), (32, (-42, 12, 0))])
    a.keys_r("tail2", [(0, (0, 0, 0)), (14, (10, 0, 0)), (26, (-20, 8, 0)), (32, (-18, 10, 0))])
    a.keys_r("tail3", [(0, (0, 0, 0)), (16, (8, 0, 0)), (28, (-10, 4, 0)), (32, (-10, 6, 0))])
    for ear, sg in (("ear.L", 1), ("ear.R", -1)):
        a.keys_r(ear, [(0, (0, 0, 0)), (6, (-30, 0, 0)), (22, (-35, sg * 10, 0)), (32, (-40, sg * 12, 0))])
    a.keys_s("eyes", [(0, 1), (4, (1.15, 1, 0.15)), (10, (1.0, 1, 0.6)), (20, (1.05, 1, 0.1)), (32, (1.05, 1, 0.06))])
    a.keys_s("crest", [(0, 1), (18, 1), (32, 0.9)])

# Victory (44f): proud hop and a long howl with crystals glowing, tail wagging
with Act(rig, "Victory", 44) as a:
    a.keys_l("root", [(0, (0, 0, 0)), (5, (0, 0, -0.05)), (10, (0, 0, 0.14)), (14, (0, 0, 0.0)), (17, (0, 0, -0.02)),
                      (22, (0, 0, 0.02)), (38, (0, 0, 0.02)), (44, (0, 0, 0))])
    a.keys_r("root", [(0, (0, 0, 0)), (5, (4, 0, 0)), (10, (-8, 0, 0)), (14, (2, 0, 0)), (20, (-4, 0, 0)), (38, (-4, 0, 0)),
                      (44, (0, 0, 0))])
    a.keys_r("spine2", [(0, (0, 0, 0)), (5, (6, 0, 0)), (12, (-8, 0, 0)), (20, (-14, 0, 0)), (38, (-12, 0, 0)),
                        (44, (0, 0, 0))])
    a.keys_r("neck", [(0, (0, 0, 0)), (6, (10, 0, 0)), (14, (-10, 0, 0)), (20, (-28, 0, 0)), (38, (-26, 0, 0)),
                      (44, (0, 0, 0))])
    a.keys_r("head", [(0, (0, 0, 0)), (6, (8, 0, 0)), (14, (-12, 0, 0)), (20, (-36, 0, 0)), (26, (-34, 3, 4)),
                      (32, (-36, -3, -4)), (38, (-32, 0, 0)), (44, (0, 0, 0))])
    a.keys_r("jaw", [(0, (0, 0, 0)), (8, (6, 0, 0)), (18, (30, 0, 0)), (22, (38, 0, 0)), (26, (34, 0, 0)), (30, (38, 0, 0)),
                     (34, (33, 0, 0)), (38, (36, 0, 0)), (42, (4, 0, 0)), (44, (0, 0, 0))])
    for leg, pw, sg in LEGS_F:
        a.keys_r(leg, [(0, (0, 0, 0)), (5, (-10, 0, 0)), (10, (-30, 0, 0)), (14, (-8, 0, 0)), (20, (-12, 0, 0)),
                       (38, (-12, 0, 0)), (44, (0, 0, 0))])
        a.keys_r(pw, [(0, (0, 0, 0)), (5, (20, 0, 0)), (10, (40, 0, 0)), (14, (8, 0, 0)), (20, (10, 0, 0)), (44, (0, 0, 0))])
    for leg, pw, sg in LEGS_H:
        a.keys_r(leg, [(0, (0, 0, 0)), (5, (-14, 0, 0)), (10, (25, 0, 0)), (14, (0, 0, 0)), (20, (6, 0, 0)), (44, (0, 0, 0))])
        a.keys_r(pw, [(0, (0, 0, 0)), (5, (-20, 0, 0)), (10, (15, 0, 0)), (14, (0, 0, 0)), (44, (0, 0, 0))])
    a.loop_r("tail1", 11, lambda t: (-10 * math.sin(math.pi * t), 0, 22 * S(4 * t)))
    a.loop_r("tail2", 11, lambda t: (-6 * math.sin(math.pi * t), 0, 22 * S(4 * t, -0.12)))
    a.loop_r("tail3", 11, lambda t: (-4 * math.sin(math.pi * t), 0, 24 * S(4 * t, -0.25)))
    for ear, sg in (("ear.L", 1), ("ear.R", -1)):
        a.keys_r(ear, [(0, (0, 0, 0)), (10, (-12, 0, 0)), (20, (-22, sg * 6, 0)), (38, (-20, sg * 6, 0)), (44, (0, 0, 0))])
    a.keys_s("eyes", [(0, 1), (14, 1), (20, (1.05, 1, 0.12)), (38, (1.05, 1, 0.12)), (42, 1), (44, 1)])
    a.keys_s("crest", [(0, 1), (14, 1.05), (22, 1.35), (30, 1.25), (38, 1.35), (44, 1)])
    a.keys_s("dorsal", [(0, 1), (22, 1.2), (38, 1.2), (44, 1)])

finish(EID, rig, body_obj, extra=[("cast", "Cast", 0.6, (75, 0, 30)), ("die", "Die", 1.0, (55, 0, 35)),
                                  ("run", "Run", 0.25, (80, 0, 90)), ("victory", "Victory", 0.6, (75, 0, 40)),
                                  ("back", "Idle", 0.0, (65, 0, 160))])
