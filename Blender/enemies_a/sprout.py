"""풀뿌리 (sprout): walking tree stump with a sapling on top, glowing eyes in a dark hollow,
root claws and root legs. Height ~1.1 m to the sapling tip.
Run: blender -b --factory-startup -P sprout.py
"""
import math
import os
import sys

sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from _common import *  # noqa: F401,F403
from _common import A, Act, Vector, S, C

EID = variant("sprout")
A.reset_scene()

BARK_L, BARK_M, BARK_D = "#d6a86c", "#a8784a", "#6a4426"
WOOD_IN = "#e8cc94"
MOSS_L, MOSS_D = "#b2dc45", "#62a02c"
LEAF_L, LEAF_D = "#a8e25c", "#4f9e2e"
HOLLOW = "#1e120a"

Z0 = 0.26          # trunk bottom
ZT = 0.80          # trunk top rim
NS = 40            # trunk segments around
HZ, HW, HH, HD = 0.55, 0.125, 0.115, 0.075   # hollow centre z, half width, half height, depth

# ---------------------------------------------------------------- trunk
prof = []
for i in range(19):
    z = Z0 - 0.02 + (ZT - Z0 + 0.02) * i / 18
    t = (z - Z0) / (ZT - Z0)
    r = 0.232 + 0.05 * max(0.0, 1 - t / 0.25) ** 2 - 0.012 * math.sin(math.pi * t) + 0.012 * t
    prof.append((r, z))
prof += [(0.205, ZT - 0.005), (0.1, ZT - 0.03), (0.0, ZT - 0.035)]
trunk = A.lathe("trunk", prof, color=BARK_M, seg=NS)


def jag(a):
    # jagged broken top: a few big teeth + small ones
    return 0.065 * max(0.0, math.sin(3 * a + 0.4)) + 0.022 * math.sin(7 * a + 1.3)


def hollow_e(a, z):
    da = (a + math.pi / 2 + math.pi) % (2 * math.pi) - math.pi
    return (da * 0.24 / HW) ** 2 + ((z - HZ) / HH) ** 2


def groove(a, z):
    return math.cos(11 * a + 2.2 * math.sin(z * 9 + a * 2))


def trunk_shape(co):
    a = math.atan2(co.y, co.x)
    r = math.hypot(co.x, co.y)
    if r > 0.15:
        k = 1.0 + 0.035 * groove(a, co.z)
        k *= 1.0 + 0.04 * math.sin(2 * a + 1.0) * math.sin(math.pi * max(0.0, (co.z - Z0)) / (ZT - Z0))
        e = hollow_e(a, co.z)
        if e < 1.0:
            k = (r - HD * math.sqrt(1 - e)) / r
        elif e < 1.9:
            k *= 1.0 + 0.09 * math.sin(math.pi * (e - 1.0) / 0.9)
        co.x *= k
        co.y *= k * 0.95
    if co.z > ZT - 0.012 and r > 0.19:
        co.z += jag(a)
    return co


A.deform(trunk, trunk_shape)
A.apply_transform(trunk)


def bark_col(co):
    a = math.atan2(co.y, co.x)
    r = math.hypot(co.x, co.y)
    if co.z > ZT - 0.045 and r < 0.2:
        return mix(WOOD_IN, "#c9a066", 0.5 + 0.5 * math.sin(r * 90))
    e = hollow_e(a, co.z)
    if r > 0.12 and e < 1.0:
        return mix(HOLLOW, "#3a2414", e ** 2)
    if r > 0.12 and e < 1.9:
        return mix(BARK_L, BARK_M, (e - 1.0) / 0.9)
    g = groove(a, co.z)
    base = mix(BARK_M, BARK_L, max(0.0, g) * 0.8) if g > 0 else mix(BARK_M, BARK_D, -g)
    t = max(0.0, min(1.0, (co.z - Z0) / 0.12))
    return mix(BARK_D, base, 0.55 + 0.45 * t)


paint_vert_fn(trunk, bark_col)

# inner wood rings on the top
rings = A.torus("ring", R=0.12, r=0.007, loc=(0, 0, ZT - 0.033), color="#bf945c", seg=24, minor=6)
ring2 = A.torus("ring2", R=0.06, r=0.006, loc=(0, 0, ZT - 0.034), color="#bf945c", seg=16, minor=6)
A.apply_transform(rings)
A.apply_transform(ring2)
rings = A.join([rings, ring2], "rings")

# ---------------------------------------------------------------- hollow face: glowing eyes inside the recess
eyes = []
for s in (-1, 1):
    p, n = surf(trunk, (0, 0, HZ + 0.012), dir_from(s * 11, 0))
    eyes.append(glow_eye(f"eye{s}", p + Vector((0, -0.006, 0)), (0, -1, 0), w=0.03, h=0.045, color="#ffd84a", depth=0.02))
face = []

# ---------------------------------------------------------------- moss + rim leaves
moss = []
for i, (yaw, pitch, sc) in enumerate([(70, 25, 0.8), (-120, 12, 0.9), (-60, -32, 0.6), (45, -40, 0.65),
                                      (150, -20, 0.8), (-160, 30, 0.7)]):
    p, n = surf(trunk, (0, 0, 0.55), dir_from(yaw, pitch))
    m = ellipsoid(f"moss{i}", (0.085 * sc, 0.025, 0.06 * sc), color=MOSS_L, seg=10, rings=6)
    A.deform(m, lambda co: co * (1.0 + 0.2 * math.sin(co.x * 110) * math.cos(co.z * 95)))
    orient(m, p, n, offset=0.004)
    paint_vert_fn(m, lambda co: mix(MOSS_D, MOSS_L, 0.5 + 0.5 * math.sin(co.x * 70 + co.z * 50)))
    moss.append(m)
# moss cushion around the top rim
for i in range(10):
    a = 2 * math.pi * i / 10 + 0.2
    r = 0.2 + 0.01 * math.sin(i * 2.3)
    loc = Vector((math.cos(a) * r, math.sin(a) * r * 0.95, ZT + jag(a) * 0.5 - 0.005))
    m = ellipsoid(f"rimmoss{i}", (0.07, 0.055, 0.035), color=MOSS_L, seg=10, rings=6)
    A.deform(m, lambda co: co * (1.0 + 0.15 * math.sin(co.x * 120 + i)))
    m.location = loc
    m.rotation_euler = (0, 0, a)
    A.apply_transform(m)
    paint_vert_fn(m, lambda co: mix(MOSS_D, MOSS_L, max(0.0, min(1.0, (co.z - ZT + 0.03) / 0.07))))
    moss.append(m)

rim_leaves = []
for i in range(14):
    yaw = -180 + i * 360 / 14 + (7 if i % 2 else 0)
    if abs(yaw) < 20:
        continue
    a = math.radians(yaw - 90)
    lift = 0.15 + 0.35 * (i % 2)
    base = Vector((math.cos(a) * 0.19, math.sin(a) * 0.18, ZT + 0.02 + 0.02 * (i % 2)))
    d = Vector((math.cos(a), math.sin(a), lift))
    L = 0.17 + 0.03 * ((i * 7) % 3)
    lf = leaf(f"rimleaf{i}", length=L, width=L * 0.62, fold=0.18, curl=0.8, light=LEAF_L, dark=LEAF_D)
    place_leaf(lf, base, d, roll=((i * 5) % 3 - 1) * 15)
    rim_leaves.append(lf)
# a few leaves on the bark sides
for i, (yaw, pitch, spin) in enumerate([(78, 18, 30), (-82, 5, -20), (125, -10, 40), (-140, 25, 10), (100, -35, -30)]):
    rim_leaves.append(skin_leaf(f"sideleaf{i}", trunk, (0, 0, 0.5), yaw, pitch, length=0.1, width=0.07, curl=0.3,
                                lift=0.6, back=0.0, light=LEAF_L, dark=LEAF_D, spin=spin))

# ---------------------------------------------------------------- sapling (sprout bone)
sap = []
stem_pts = [(0, 0.01, ZT - 0.04), (0.0, 0.0, ZT + 0.08), (0.018, -0.005, ZT + 0.18), (0.0, 0.0, ZT + 0.27)]
sap.append(A.tube("stem", stem_pts, radius=0.02, color="#5aa833", taper_end=0.55))
tip = Vector(stem_pts[-1])
for i, (d, L, W) in enumerate([((0.9, -0.15, 0.5), 0.22, 0.14), ((-0.9, 0.1, 0.6), 0.21, 0.135),
                               ((0.1, -0.35, 1.0), 0.11, 0.07)]):
    lf = leaf(f"sapleaf{i}", length=L, width=W, fold=0.25, curl=0.5, light=LEAF_L, dark=LEAF_D)
    place_leaf(lf, tip - Vector((0, 0, 0.01)), d)
    sap.append(lf)
for i, (d, z) in enumerate([((0.8, 0.3, 0.6), ZT + 0.13), ((-0.7, -0.3, 0.5), ZT + 0.07)]):
    lf = leaf(f"stemleaf{i}", length=0.09, width=0.06, fold=0.25, curl=0.3, light=LEAF_L, dark=LEAF_D)
    place_leaf(lf, Vector((0.006, 0, z)), d)
    sap.append(lf)

# ---------------------------------------------------------------- arms (root claws)
def make_arm(s):
    sh = Vector((s * 0.2, -0.02, 0.62))
    el = Vector((s * 0.42, -0.07, 0.56))
    wr = Vector((s * 0.52, -0.14, 0.4))
    upper = A.tube(f"arm{s}", [tuple(sh), tuple(sh.lerp(el, 0.5) + Vector((0, 0, 0.035))), tuple(el), tuple(wr)],
                   radius=0.058, color=BARK_M, taper_end=0.72)
    paint_fn(upper, lambda c, n, i: BARK_L if (n.z > 0.35) else BARK_M)
    knot = ellipsoid(f"knot{s}", (0.062, 0.058, 0.055), loc=tuple(el), color=BARK_D, seg=14, rings=8)
    leafy = leaf(f"armleaf{s}", length=0.11, width=0.07, fold=0.2, curl=0.4, light=LEAF_L, dark=LEAF_D)
    place_leaf(leafy, el + Vector((0, 0, 0.03)), (s * 0.3, 0.2, 1.0))
    hand = []
    palm = ellipsoid(f"palm{s}", (0.07, 0.065, 0.06), loc=tuple(wr), color=BARK_M, seg=12, rings=8)
    hand.append(palm)
    for k, (dx, dy) in enumerate([(0.6, -0.3), (0.2, -0.75), (-0.3, -0.65), (0.9, 0.2)]):
        d = Vector((s * dx, dy, -0.6)).normalized()
        L = 0.17 if k < 3 else 0.12
        f_pts = []
        for j in range(5):
            t = j / 4
            q = wr + d * L * t + Vector((0, -0.05, 0)) * t * t * 2 + Vector((0, 0, 0.06)) * math.sin(math.pi * t)
            f_pts.append(tuple(q))
        finger = A.tube(f"finger{s}_{k}", f_pts, radius=0.036, color=BARK_M, taper_end=0.45, seg=8)
        paint_fn(finger, lambda c, n, i: BARK_L if n.z > 0.4 else BARK_M)
        hand.append(finger)
        tipc = claw(f"claw{s}_{k}", f_pts[-2], d + Vector((0, -0.5, -0.4)), length=0.1, r=0.02, color="#e8c99a")
        hand.append(tipc)
    return [upper, knot, leafy], hand, sh, wr


armL, handL, shL, wrL = make_arm(1)
armR, handR, shR, wrR = make_arm(-1)


# ---------------------------------------------------------------- legs (root legs)
def make_leg(s):
    hip = Vector((s * 0.12, 0.0, Z0 + 0.06))
    knee = Vector((s * 0.25, -0.03, 0.19))
    foot = Vector((s * 0.3, -0.06, 0.05))
    parts = [A.tube(f"leg{s}", [tuple(hip), tuple(knee), tuple(foot)], radius=0.085, color=BARK_M, taper_end=0.75)]
    paint_fn(parts[0], lambda c, n, i: BARK_L if n.z > 0.3 else (BARK_D if n.y > 0.5 else BARK_M))
    for k, (dx, dy) in enumerate([(0.2, -1.0), (0.9, -0.3), (-0.5, -0.8), (0.4, 0.9)]):
        d = Vector((s * dx, dy, 0)).normalized()
        toe_pts = [tuple(foot), tuple(foot + d * 0.08 + Vector((0, 0, -0.015))), tuple(foot + d * 0.16 + Vector((0, 0, -0.035)))]
        parts.append(A.tube(f"toe{s}_{k}", toe_pts, radius=0.038, color=BARK_M, taper_end=0.35))
        parts.append(claw(f"toeclaw{s}_{k}", Vector(toe_pts[-1]), d + Vector((0, 0, -0.4)), length=0.06, r=0.013,
                          color="#5a3a20"))
    mossk = ellipsoid(f"legmoss{s}", (0.05, 0.04, 0.035), loc=tuple(knee + Vector((0, -0.03, 0.03))), color=MOSS_L,
                      seg=10, rings=6)
    parts.append(mossk)
    return parts, hip


legL, hipL = make_leg(1)
legR, hipR = make_leg(-1)

# ---------------------------------------------------------------- rig
rig = make_rig([
    ("root", (0, 0, 0), None),
    ("body", (0, 0, Z0), "root"),
    ("eyes", (0, -0.26, 0.565), "body"),
    ("sapling", (0, 0, ZT - 0.02), "body"),
    ("arm.L", tuple(shL), "body"),
    ("hand.L", tuple(wrL), "arm.L"),
    ("arm.R", tuple(shR), "body"),
    ("hand.R", tuple(wrR), "arm.R"),
    ("leg.L", tuple(hipL), "root"),
    ("leg.R", tuple(hipR), "root"),
])
body_obj = A.skin({
    "body": [trunk, rings] + face + moss + rim_leaves,
    "eyes": eyes,
    "sapling": sap,
    "arm.L": armL, "hand.L": handL,
    "arm.R": armR, "hand.R": handR,
    "leg.L": legL, "leg.R": legR,
}, rig)

# ---------------------------------------------------------------- animation
with Act(rig, "Idle", 48) as a:
    a.loop_r("body", 4, lambda t: (2 * S(t), 2.5 * S(t, 0.25), 0))
    a.loop_l("body", 8, lambda t: (0, 0, 0.012 * S(t * 2)))
    a.loop_r("sapling", 8, lambda t: (-6 * S(t, -0.12), -7 * S(t, 0.13), 4 * S(t, 0.3)))
    for side, sg in (("L", 1), ("R", -1)):
        a.loop_r(f"arm.{side}", 4, lambda t, sg=sg: (4 * S(t, -0.1 + 0.2 * (sg > 0)), sg * 3 * S(t, -0.1), 0))
        a.loop_r(f"hand.{side}", 4, lambda t, sg=sg: (8 * S(t, -0.25 + 0.2 * (sg > 0)), 0, sg * 5 * S(t, -0.2)))
    for f, k in ((0, 1), (20, 1), (22, 0.1), (24, 1), (40, 1), (41, 0.1), (43, 1), (48, 1)):
        a.s("eyes", f, 1, 1, k)

# Run: heavy lumbering stride (legs alternate, body rocks, arms swing opposite)
with Act(rig, "Run", 20) as a:
    a.loop_r("leg.L", 4, lambda t: (-28 * S(t, 0.25), 0, 0))
    a.loop_r("leg.R", 4, lambda t: (28 * S(t, 0.25), 0, 0))
    a.loop_l("leg.L", 4, lambda t: (0, 0, 0.06 * max(0.0, S(t))))
    a.loop_l("leg.R", 4, lambda t: (0, 0, 0.06 * max(0.0, -S(t))))
    a.loop_l("body", 8, lambda t: (0, 0, 0.03 + 0.03 * C(2 * t)))
    a.loop_r("body", 8, lambda t: (10 + 2 * C(2 * t), 6 * S(t), 5 * S(t, 0.25)))
    a.loop_r("arm.L", 4, lambda t: (35 * S(t, 0.25), 6, 0))
    a.loop_r("arm.R", 4, lambda t: (-35 * S(t, 0.25), -6, 0))
    a.loop_r("hand.L", 4, lambda t: (20 * S(t, 0.1), 0, 0))
    a.loop_r("hand.R", 4, lambda t: (-20 * S(t, 0.1), 0, 0))
    a.loop_r("sapling", 8, lambda t: (-12 + 6 * C(2 * t, -0.1), 8 * S(t, -0.1), 0))

# Attack (26f, impact f10): arms rear up/back -> lunge, double claw rake down -> follow through
with Act(rig, "Attack", 26) as a:
    a.keys_r("body", [(0, (0, 0, 0)), (6, (-14, 0, 0)), (10, (24, 0, 0)), (14, (28, 0, 0)), (20, (6, 0, 0)), (26, (0, 0, 0))])
    a.keys_l("body", [(0, (0, 0, 0)), (6, (0, 0.04, 0.03)), (10, (0, -0.18, -0.03)), (14, (0, -0.2, -0.04)),
                      (20, (0, -0.05, 0)), (26, (0, 0, 0))])
    for side, sg in (("L", 1), ("R", -1)):
        a.keys_r(f"arm.{side}", [(0, (0, 0, 0)), (6, (-140, sg * 10, -sg * 10)), (10, (-50, -sg * 10, sg * 10)),
                                (14, (-20, -sg * 12, sg * 12)), (20, (-6, 0, 0)), (26, (0, 0, 0))])
        a.keys_r(f"hand.{side}", [(0, (0, 0, 0)), (6, (-30, 0, 0)), (10, (25, 0, 0)), (14, (35, 0, 0)), (20, (5, 0, 0)),
                                 (26, (0, 0, 0))])
    a.keys_r("leg.L", [(0, (0, 0, 0)), (6, (10, 0, 0)), (10, (-25, 0, 0)), (20, (-10, 0, 0)), (26, (0, 0, 0))])
    a.keys_r("leg.R", [(0, (0, 0, 0)), (6, (-5, 0, 0)), (10, (15, 0, 0)), (20, (5, 0, 0)), (26, (0, 0, 0))])
    a.keys_r("sapling", [(0, (0, 0, 0)), (6, (18, 0, 0)), (10, (-25, 0, 0)), (14, (14, 0, 0)), (19, (-6, 0, 0)), (26, (0, 0, 0))])
    a.keys_s("eyes", [(0, 1), (6, (1.2, 1, 0.6)), (10, (1.3, 1, 1.25)), (18, 1), (26, 1)])

# Cast (36f, release f22): roots brace, arms spread up, sapling flares
with Act(rig, "Cast", 36) as a:
    a.keys_l("body", [(0, (0, 0, 0)), (10, (0, 0, -0.04)), (18, (0, 0, -0.05)), (22, (0, 0, 0.06)), (28, (0, 0, 0.01)),
                      (36, (0, 0, 0))])
    a.keys_r("body", [(0, (0, 0, 0)), (10, (8, 0, 0)), (18, (6, 0, 0)), (22, (-12, 0, 0)), (28, (-4, 0, 0)), (36, (0, 0, 0))])
    for f in range(10, 19, 2):
        a.r("body", f, 7, 2.5 * (1 if (f // 2) % 2 else -1), 0)
    for side, sg in (("L", 1), ("R", -1)):
        a.keys_r(f"arm.{side}", [(0, (0, 0, 0)), (10, (10, sg * 10, -sg * 10)), (18, (5, sg * 15, -sg * 15)),
                                (22, (-30, -sg * 50, sg * 10)), (28, (-25, -sg * 45, sg * 8)), (36, (0, 0, 0))])
        a.keys_r(f"hand.{side}", [(0, (0, 0, 0)), (12, (30, 0, 0)), (22, (-30, 0, 0)), (30, (-10, 0, 0)), (36, (0, 0, 0))])
    a.keys_s("sapling", [(0, 1), (12, 0.9), (18, 0.9), (22, 1.45), (27, 1.2), (36, 1)])
    a.keys_r("sapling", [(0, (0, 0, 0)), (18, (0, 0, 30)), (22, (-10, 0, 90)), (28, (5, 0, 60)), (36, (0, 0, 0))])
    a.keys_s("eyes", [(0, 1), (10, (1, 1, 0.3)), (19, (1, 1, 0.3)), (22, (1.4, 1, 1.4)), (30, 1.1), (36, 1)])

# Hit (12f)
with Act(rig, "Hit", 12) as a:
    a.keys_r("body", [(0, (0, 0, 0)), (2, (-18, -6, 0)), (6, (6, 2, 0)), (9, (-2, 0, 0)), (12, (0, 0, 0))])
    a.keys_l("body", [(0, (0, 0, 0)), (2, (0, 0.08, 0)), (7, (0, 0.04, 0)), (12, (0, 0, 0))])
    a.keys_r("sapling", [(0, (0, 0, 0)), (2, (26, 0, 0)), (5, (-18, 0, 0)), (8, (8, 0, 0)), (12, (0, 0, 0))])
    for side, sg in (("L", 1), ("R", -1)):
        a.keys_r(f"arm.{side}", [(0, (0, 0, 0)), (2, (-35, -sg * 15, 0)), (6, (8, 0, 0)), (12, (0, 0, 0))])
    a.keys_s("eyes", [(0, 1), (1, (1.2, 1, 0.15)), (8, (1.2, 1, 0.2)), (12, 1)])

# Die (32f): stagger, topple backwards onto its back, sapling droops, eyes go out
with Act(rig, "Die", 32) as a:
    a.keys_r("body", [(0, (0, 0, 0)), (5, (12, 4, 0)), (10, (-10, -4, 0)), (20, (-70, -6, 0)), (24, (-94, -4, 0)),
                      (27, (-86, -4, 0)), (32, (-90, -4, 0))])
    a.keys_l("body", [(0, (0, 0, 0)), (10, (0, 0.03, 0)), (24, (0, 0.12, -0.02)), (32, (0, 0.12, -0.02))])
    a.keys_r("leg.L", [(0, (0, 0, 0)), (10, (-10, 0, 0)), (24, (-60, 10, 0)), (32, (-55, 12, 0))])
    a.keys_r("leg.R", [(0, (0, 0, 0)), (10, (5, 0, 0)), (24, (-70, -10, 0)), (32, (-65, -12, 0))])
    a.keys_l("leg.L", [(0, (0, 0, 0)), (24, (0, 0.1, 0.0)), (32, (0, 0.1, 0.0))])
    a.keys_l("leg.R", [(0, (0, 0, 0)), (24, (0, 0.1, 0.0)), (32, (0, 0.1, 0.0))])
    for side, sg in (("L", 1), ("R", -1)):
        a.keys_r(f"arm.{side}", [(0, (0, 0, 0)), (5, (-30, sg * 20, 0)), (20, (-20, -sg * 40, 0)), (26, (10, -sg * 50, 0)),
                                (32, (5, -sg * 48, 0))])
        a.keys_r(f"hand.{side}", [(0, (0, 0, 0)), (24, (30, 0, 0)), (32, (35, 0, 0))])
    a.keys_r("sapling", [(0, (0, 0, 0)), (12, (20, 0, 0)), (22, (-30, 15, 0)), (26, (-55, 22, 0)), (32, (-50, 25, 0))])
    a.keys_s("sapling", [(0, 1), (32, (1, 1, 0.8))])
    a.keys_s("eyes", [(0, 1), (8, (1.2, 1, 0.3)), (14, 1), (22, (0.4, 1, 0.05)), (32, (0.05, 1, 0.05))])

# Victory (44f): arms raised, happy stomp-hop, sapling flutters
with Act(rig, "Victory", 44) as a:
    a.keys_l("body", [(0, (0, 0, 0)), (6, (0, 0, -0.04)), (12, (0, 0, 0.12)), (18, (0, 0, 0)), (24, (0, 0, -0.03)),
                      (30, (0, 0, 0.1)), (36, (0, 0, 0)), (44, (0, 0, 0))])
    a.keys_r("body", [(0, (0, 0, 0)), (12, (-8, 0, 0)), (24, (4, 0, 0)), (30, (-8, 0, 0)), (44, (0, 0, 0))])
    for side, sg in (("L", 1), ("R", -1)):
        a.keys_r(f"arm.{side}", [(0, (0, 0, 0)), (8, (-80, -sg * 30, 0)), (14, (-110, -sg * 40, 0)), (22, (-90, -sg * 30, 0)),
                                (30, (-115, -sg * 40, 0)), (38, (-80, -sg * 30, 0)), (44, (0, 0, 0))])
        a.keys_r(f"hand.{side}", [(0, (0, 0, 0)), (14, (-30, 0, 0)), (22, (10, 0, 0)), (30, (-30, 0, 0)), (44, (0, 0, 0))])
    for f, k in ((0, 0), (12, 1), (30, 1), (44, 0)):
        pass
    a.keys_r("leg.L", [(0, (0, 0, 0)), (12, (-15, 0, 0)), (18, (0, 0, 0)), (30, (-15, 0, 0)), (36, (0, 0, 0)), (44, (0, 0, 0))])
    a.keys_r("leg.R", [(0, (0, 0, 0)), (12, (15, 0, 0)), (18, (0, 0, 0)), (30, (15, 0, 0)), (36, (0, 0, 0)), (44, (0, 0, 0))])
    a.loop_r("sapling", 8, lambda t: (10 * S(2 * t), 8 * S(2 * t, 0.25), 0))
    a.keys_s("eyes", [(0, 1), (8, (1.2, 1, 0.35)), (38, (1.2, 1, 0.35)), (44, 1)])

finish(EID, rig, body_obj, extra=[("cast", "Cast", 0.6, (75, 0, 30)), ("die", "Die", 1.0, (60, 0, 50))])
