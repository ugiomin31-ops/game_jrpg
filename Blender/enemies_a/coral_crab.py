"""산호 소라게 (coral_crab): hermit crab in a big barnacled cream shell with red branching coral on top,
dark shell opening with two glowing eyes, big speckled red-orange claws and spindly spotted legs.
Elite (elite_coral_crab, 거대 산호 집게): one huge serrated claw, armour plates/spikes on the shell,
tall spiky orange coral spires, deeper orange-red palette, barnacle crust, glowing orange eyes.
"""
import math
import os
import sys

sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from _common import *  # noqa: F401,F403
from _common import A, Act, Vector, S, C

EID = variant("coral_crab")
ELITE = EID.startswith("elite_")
A.reset_scene()

if ELITE:
    SHELL_L, SHELL_M, SHELL_D = "#e8cf9f", "#cfae78", "#9c774c"
    SPECK = "#a8452c"
    RED_L, RED_M, RED_D = "#ef5a32", "#cf3a1f", "#8e2414"
    CREAM = "#f1d29c"
    CORAL_L, CORAL_D = "#ffa040", "#e8601c"
    EYE = "#ff8a1a"
    PLATE_L, PLATE_D = "#a4553a", "#6e3222"
else:
    SHELL_L, SHELL_M, SHELL_D = "#f3e7c6", "#e0cfa2", "#b9a274"
    SPECK = "#c87a58"
    RED_L, RED_M, RED_D = "#f58358", "#e45c3c", "#b23c28"
    CREAM = "#f6e2b8"
    CORAL_L, CORAL_D = "#f27a62", "#d9483a"
    EYE = "#ffd84a"
BARN_L, BARN_D, BARN_IN = "#b3ada2", "#8a857b", "#4e4a43"
HOLE = "#17100d"

SC = (0.0, 0.05, 0.45)         # shell centre
SR = (0.36, 0.37, 0.31)        # shell radii


def wob(x, y, z, k=1.0):
    return k * (math.sin(7.1 * x + 1.3) * math.sin(6.3 * y + 0.4) * math.sin(5.7 * z + 2.1))


def speck(co, base, dark, density=0.78, f=19.0):
    v = math.sin(co.x * f + 1.7) * math.sin(co.y * f * 1.13 + 0.3) * math.sin(co.z * f * 0.91 + 2.2)
    return dark if v > density * 0.9 else base


# ---------------------------------------------------------------- shell
shell = ellipsoid("shell", SR, loc=SC, color=SHELL_M, seg=32, rings=18)


def shell_shape(co):
    d = co - Vector(SC)
    k = 1.0 + 0.06 * wob(d.x * 3, d.y * 3, d.z * 3) + 0.03 * math.sin(6 * math.atan2(d.y, d.x))
    d = d * k
    p = Vector(SC) + d
    # flat-ish bottom
    if p.z < 0.24:
        p.z = 0.24 + (p.z - 0.24) * 0.35
    # slight conch peak leaning back
    t = max(0.0, d.z / SR[2])
    p.y += 0.06 * t * t
    p.z += 0.05 * t ** 3
    return p


A.deform(shell, shell_shape)


def shell_col(co):
    rel = (co.z - 0.24) / 0.55
    base = mix(SHELL_D, SHELL_L, min(1.0, max(0.0, rel * 1.4)))
    v = math.sin(co.x * 23 + 1.7) * math.sin(co.y * 21 + 0.3) * math.sin(co.z * 25 + 2.2)
    if v > 0.72:
        return mix(base, SPECK, 0.75)
    if v < -0.8:
        return mix(base, SHELL_D, 0.6)
    return base


paint_vert_fn(shell, shell_col)
body_parts = [shell]

# spiral whorl ridge on top-back
whorl = []
for i in range(26):
    t = i / 25
    ang = math.radians(90 + 520 * t)
    pitch = 88 - 52 * t
    d = Vector((math.cos(ang) * math.cos(math.radians(pitch)), 0.0, 0.0))
    dd = Vector((math.cos(ang) * math.cos(math.radians(pitch)) * 0.8,
                 abs(math.sin(ang)) * 0.4 + 0.35, math.sin(math.radians(pitch)))).normalized()
    p, n = surf(shell, SC, dd)
    whorl.append(tuple(p + n * 0.004))
ridge = A.tube("whorl", whorl, radius=0.022, color=SHELL_L, seg=8, taper_end=0.3)
body_parts.append(ridge)

# ---------------------------------------------------------------- opening + eyes
op, on = surf(shell, (0, 0.05, 0.38), dir_from(0, -8))
hole = ellipsoid("hole", (0.2, 0.07, 0.15), color=HOLE, seg=20, rings=10)
orient(hole, op - on * 0.025, on)
lip = A.torus("lip", R=0.2, r=0.04, scale=(1.0, 0.78, 1.0), color=SHELL_L, seg=28, minor=8)
A.apply_transform(lip)
paint_vert_fn(lip, lambda co: SHELL_L if co.y > 0 else SHELL_M)
aim(lip, op - on * 0.012, on)
body_parts += [hole, lip]
eyes = []
for s in (-1, 1):
    e = glow_eye(f"eye{s}", op + Vector((s * 0.065, 0, 0.0)) + on * 0.018, on, w=0.038, h=0.05, color=EYE)
    eyes.append(e)
EYE_POS = op + on * 0.01

# crab body peeking under the shell
belly = ellipsoid("belly", (0.2, 0.17, 0.09), loc=(0, -0.02, 0.22), color=RED_M, seg=16, rings=10)
paint_vert_fn(belly, lambda co: RED_L if co.z > 0.24 else RED_D)
body_parts.append(belly)

# ---------------------------------------------------------------- barnacles
barn_dirs = [(-35, 55), (40, 48), (120, 40), (-130, 35), (170, 60), (75, 20), (-80, 15), (20, 78), (-150, 70),
             (140, 12)]
if ELITE:
    barn_dirs += [(-60, 30), (95, 55), (-105, 50), (60, 70), (-170, 25), (155, 35), (-15, 35), (110, 5),
                  (-115, 5), (30, 25)]
barns = []
for i, (yaw, pitch) in enumerate(barn_dirs):
    p, n = surf(shell, SC, dir_from(yaw, pitch))
    sz = 0.75 + 0.35 * ((i * 37) % 7) / 6
    c = A.cyl(f"barn{i}", r=0.034 * sz, r2=0.02 * sz, depth=0.04 * sz, color=BARN_L, seg=10)
    A.apply_transform(c)
    paint_fn(c, lambda cc, nn, ii: BARN_L if nn.z > 0.5 else (BARN_D if nn.z < -0.5 else
                                                               (BARN_L if nn.x + nn.y > 0 else BARN_D)))
    c.location.z = 0.012 * sz
    A.apply_transform(c)
    aim(c, p - n * 0.006, n)
    hl = A.cyl(f"barnh{i}", r=0.013 * sz, depth=0.008, color=BARN_IN, seg=8)
    A.apply_transform(hl)
    hl.location.z = 0.032 * sz
    A.apply_transform(hl)
    aim(hl, p - n * 0.006, n)
    barns += [c, hl]
    if i % 3 == 0:  # tiny ring barnacle next to it
        side = n.cross(Vector((0, 0, 1)))
        if side.length < 1e-3:
            side = Vector((1, 0, 0))
        q, qn = surf(shell, SC, (p + side.normalized() * 0.05 - Vector(SC)))
        rg = A.torus(f"barnr{i}", R=0.016, r=0.007, color=BARN_D, seg=10, minor=5)
        A.apply_transform(rg)
        aim(rg, q, qn)
        barns.append(rg)
body_parts += barns

# ---------------------------------------------------------------- armour (elite)
if ELITE:
    for i, (yaw, pitch, sc) in enumerate([(-55, 35, 1.0), (55, 35, 1.0), (-110, 30, 0.9), (110, 30, 0.9),
                                          (180, 30, 1.0), (0, 62, 0.9), (-150, 55, 0.8), (150, 55, 0.8)]):
        p, n = surf(shell, SC, dir_from(yaw, pitch))
        pl = ellipsoid(f"plate{i}", (0.11 * sc, 0.03, 0.08 * sc), color=PLATE_D, seg=12, rings=8)
        paint_fn(pl, lambda c, nn, ii: PLATE_L if nn.y < -0.3 else PLATE_D)
        orient(pl, p, n)
        sp = A.cone(f"spike{i}", r=0.03 * sc, depth=0.12 * sc, color=CREAM, seg=8)
        A.apply_transform(sp)
        sp.location.z = 0.05 * sc
        A.apply_transform(sp)
        paint_fn(sp, lambda c, nn, ii: CREAM if c.z > 0.03 else PLATE_L)
        aim(sp, p + n * 0.02, n)
        body_parts += [pl, sp]
    # spiked lip crown over the opening
    for k in range(5):
        ang = math.radians(35 + 27.5 * k)
        p, n = surf(shell, SC, (op + Vector((math.cos(ang) * 0.24, 0, math.sin(ang) * 0.2)) - Vector(SC)))
        sp = A.cone(f"lipspike{k}", r=0.025, depth=0.09, color=CREAM, seg=8)
        A.apply_transform(sp)
        sp.location.z = 0.04
        A.apply_transform(sp)
        aim(sp, p, (n + Vector((0, -0.6, 0.3))).normalized())
        body_parts.append(sp)


# ---------------------------------------------------------------- corals
def coral_tree(name, base, direction, length, r, depth, parts, spread=34.0, seed=0):
    d = Vector(direction).normalized()
    end = Vector(base) + d * length
    mid = Vector(base).lerp(end, 0.5) + Vector((math.sin(seed) * 0.01, 0, 0))
    if ELITE:
        t = A.tube(f"{name}", [tuple(base), tuple(mid), tuple(end)], radius=r, color=CORAL_D, seg=8,
                   taper_end=0.15 if depth == 0 else 0.55)
    else:
        t = A.tube(f"{name}", [tuple(base), tuple(mid), tuple(end)], radius=r, color=CORAL_D, seg=8, taper_end=0.85)
    paint_vert_fn(t, lambda co: CORAL_L if (co - Vector(base)).length > length * 0.55 else CORAL_D)
    parts.append(t)
    if depth == 0:
        if not ELITE:
            tip = A.sphere(f"{name}_tip", r=r * 0.95, loc=tuple(end), color=CORAL_L, seg=10, rings=6)
            A.apply_transform(tip)
            parts.append(tip)
        return
    side = d.cross(Vector((0.3, 0.2, 1.0) if abs(d.z) < 0.95 else (1, 0, 0))).normalized()
    for k, (sgn, at) in enumerate([(1, 1.0), (-1, 0.62)]):
        a = math.radians(spread * sgn + 6 * math.sin(seed + k))
        nd = (d * math.cos(a) + side * math.sin(a)).normalized()
        nb = Vector(base).lerp(end, at)
        coral_tree(f"{name}_{k}", nb, nd, length * 0.66, r * 0.78, depth - 1, parts, spread, seed + 1.7 * k + 0.9)


def coral_cluster(name, yaw, pitch, lean, scale, parts):
    p, n = surf(shell, SC, dir_from(yaw, pitch))
    up = (n * 0.35 + Vector((0, 0, 1)) + Vector(lean)).normalized()
    base_blob = ellipsoid(f"{name}_base", (0.05 * scale, 0.05 * scale, 0.03 * scale), color=CORAL_D, seg=12, rings=6)
    orient(base_blob, p, n)
    parts.append(base_blob)
    if ELITE:
        for k, (dx, dy, h) in enumerate([(0, 0, 1.0), (0.4, 0.2, 0.7), (-0.35, 0.25, 0.75), (0.1, -0.4, 0.6)]):
            dd = (up + Vector((dx, dy, 0)) * 0.6).normalized()
            coral_tree(f"{name}_sp{k}", p - n * 0.01, dd, 0.2 * scale * h, 0.03 * scale, 1, parts, spread=28,
                       seed=k * 2.3)
    else:
        coral_tree(f"{name}_a", p - n * 0.01, up, 0.13 * scale, 0.026 * scale, 2, parts, seed=yaw * 0.1)
        side = up.cross(Vector((0, 1, 0))).normalized()
        coral_tree(f"{name}_b", p - n * 0.01, (up + side * 0.7).normalized(), 0.09 * scale, 0.022 * scale, 1, parts,
                   seed=pitch)
    return p


coralL, coralR = [], []
cpL = coral_cluster("coralL", 38, 50, (0.25, 0.05, 0), 1.25 if ELITE else 1.15, coralL)
cpR = coral_cluster("coralR", -45, 62, (-0.25, 0.1, 0), 1.45 if ELITE else 1.3, coralR)


# ---------------------------------------------------------------- claws
def make_claw(s, big):
    k = 1.9 if big else 1.0
    sh = Vector((s * 0.15, -0.16, 0.25))
    el = Vector((s * 0.27, -0.27, 0.22))
    wr = Vector((s * (0.27 + 0.03 * (k - 1)), -0.35 - 0.04 * (k - 1), 0.2 + 0.03 * (k - 1)))
    arm = [A.tube(f"arm{s}", [tuple(sh), tuple(el), tuple(wr)], radius=0.035 * (1 + 0.35 * (k - 1)),
                  color=RED_M, seg=8, taper_end=1.1)]
    paint_fn(arm[0], lambda c, n, i: RED_L if n.z > 0.3 else RED_D if n.z < -0.4 else RED_M)
    arm.append(ellipsoid(f"elbow{s}", (0.045 * (1 + 0.35 * (k - 1)),) * 3, loc=tuple(el), color=RED_M, seg=12, rings=8))
    hand = []
    pc = wr + Vector((s * 0.0, -0.06 * k, 0.0))
    palm = ellipsoid(f"palm{s}", (0.085 * k, 0.11 * k, 0.08 * k), loc=tuple(pc), color=RED_M, seg=18, rings=12)
    palm.rotation_euler = (0, 0, math.radians(-s * 15))
    A.apply_transform(palm)

    def palm_col(co, _pc=pc):
        rel = co - _pc
        base = RED_L if rel.z > 0.02 * k else (RED_D if rel.z < -0.045 * k else RED_M)
        v = math.sin(co.x * 41 / k + 1.1) * math.sin(co.y * 37 / k + 0.7) * math.sin(co.z * 43 / k + 0.2)
        return CREAM if v > 0.7 else base

    paint_vert_fn(palm, palm_col)
    hand.append(palm)
    # fixed (lower) finger: forward, curving inward, cream tip
    fb = pc + Vector((s * 0.01, -0.08 * k, -0.025 * k))
    fpts = []
    for j in range(5):
        t = j / 4
        fpts.append(tuple(fb + Vector((-s * 0.06 * k * t * t, -0.13 * k * t, -0.01 * k * math.sin(math.pi * t)))))
    fixed = A.tube(f"fixed{s}", fpts, radius=0.036 * k, color=RED_M, seg=10, taper_end=0.2)
    paint_vert_fn(fixed, lambda co, _fb=fb: CREAM if (co - _fb).length > 0.08 * k else RED_M)
    hand.append(fixed)
    hinge = pc + Vector((s * 0.03 * k, -0.07 * k, 0.035 * k))
    dpts = []
    for j in range(5):
        t = j / 4
        dpts.append(tuple(hinge + Vector((-s * 0.065 * k * t * t, -0.14 * k * t, 0.015 * k * math.sin(math.pi * t)
                                          - 0.03 * k * t))))
    dact = A.tube(f"dact{s}", dpts, radius=0.032 * k, color=RED_M, seg=10, taper_end=0.2)
    paint_vert_fn(dact, lambda co, _h=hinge: CREAM if (co - _h).length > 0.085 * k else RED_L)
    jaw = [dact]
    if big:
        for j in range(5):
            t = 0.25 + 0.15 * j
            q = Vector(fpts[0]).lerp(Vector(fpts[-1]), t)
            q = Vector(fpts[min(4, int(t * 4))]).lerp(Vector(fpts[min(4, int(t * 4) + 1)]), (t * 4) % 1)
            tooth = A.cone(f"ftooth{s}_{j}", r=0.016, depth=0.045, color=CREAM, seg=6)
            A.apply_transform(tooth)
            tooth.location.z = 0.02
            A.apply_transform(tooth)
            aim(tooth, q + Vector((0, 0, 0.035 * k * 0.6)), (0, 0, 1))
            hand.append(tooth)
            q2 = Vector(dpts[min(4, int(t * 4))]).lerp(Vector(dpts[min(4, int(t * 4) + 1)]), (t * 4) % 1)
            tooth2 = A.cone(f"dtooth{s}_{j}", r=0.014, depth=0.04, color=CREAM, seg=6)
            A.apply_transform(tooth2)
            tooth2.location.z = 0.018
            A.apply_transform(tooth2)
            aim(tooth2, q2 - Vector((0, 0, 0.032 * k * 0.6)), (0, 0, -1))
            jaw.append(tooth2)
        # armoured knuckle spikes on the giant claw
        for j, (dx, dz) in enumerate([(0.6, 0.6), (1.0, 0.0), (0.3, 0.95)]):
            dd = Vector((s * dx, 0.15, dz)).normalized()
            p, n = surf(palm, pc, dd)
            sp = A.cone(f"kspike{s}_{j}", r=0.03, depth=0.1, color=CREAM, seg=8)
            A.apply_transform(sp)
            sp.location.z = 0.04
            A.apply_transform(sp)
            aim(sp, p - n * 0.01, n)
            hand.append(sp)
    return arm, hand, jaw, sh, wr, hinge


big_side = 1  # elite giant claw on creature's left (+X)
armL, handL, jawL, shL, wrL, hgL = make_claw(1, ELITE and big_side == 1)
armR, handR, jawR, shR, wrR, hgR = make_claw(-1, False)


# ---------------------------------------------------------------- legs
def make_leg(s, i):
    y = -0.04 + 0.12 * i
    hip = Vector((s * 0.17, y, 0.24))
    spread = (i - 0.6) * 0.32
    out = Vector((s * math.cos(spread), math.sin(spread), 0))
    knee = hip + out * 0.2 + Vector((0, 0, 0.12))
    ank = hip + out * 0.33 + Vector((0, 0, 0.03))
    foot = hip + out * 0.37 + Vector((0, 0, -0.235))
    parts = []
    segs = [(hip, knee, 0.026), (knee, ank, 0.022), (ank, foot, 0.018)]
    for j, (a, b, r) in enumerate(segs):
        t = A.tube(f"leg{s}_{i}_{j}", [tuple(a), tuple(a.lerp(b, 0.5) + Vector((0, 0, 0.012))), tuple(b)], radius=r,
                   color=RED_M, seg=8, taper_end=0.75 if j < 2 else 0.35)
        paint_vert_fn(t, lambda co: CREAM if math.sin(co.x * 60 + co.z * 47) * math.sin(co.y * 53) > 0.75
                      else (RED_L if co.z > 0.2 else RED_M))
        parts.append(t)
    for j, (pt, r) in enumerate([(knee, 0.026), (ank, 0.022)]):
        parts.append(ellipsoid(f"joint{s}_{i}_{j}", (r, r, r), loc=tuple(pt), color=RED_D, seg=10, rings=6))
    parts.append(A.cone(f"foottip{s}_{i}", r=0.012, depth=0.03, loc=tuple(foot - Vector((0, 0, 0.0))),
                        color=CREAM, seg=6, rot=(180, 0, 0)))
    return parts, hip


legs = {}
for s, side in ((1, "L"), (-1, "R")):
    for i in range(3):
        parts, hip = make_leg(s, i)
        legs[f"leg{i + 1}.{side}"] = (parts, hip)

# ---------------------------------------------------------------- rig
bones = [
    ("root", (0, 0, 0), None),
    ("body", (0, 0.02, 0.24), "root"),
    ("eyes", tuple(EYE_POS), "body"),
    ("coral.L", tuple(cpL), "body"),
    ("coral.R", tuple(cpR), "body"),
    ("arm.L", tuple(shL), "body"),
    ("claw.L", tuple(wrL), "arm.L"),
    ("pincer.L", tuple(hgL), "claw.L"),
    ("arm.R", tuple(shR), "body"),
    ("claw.R", tuple(wrR), "arm.R"),
    ("pincer.R", tuple(hgR), "claw.R"),
]
for name, (parts, hip) in legs.items():
    bones.append((name, tuple(hip), "root"))
rig = make_rig(bones)
skin_map = {
    "body": body_parts,
    "eyes": eyes,
    "coral.L": coralL, "coral.R": coralR,
    "arm.L": armL, "claw.L": handL, "pincer.L": jawL,
    "arm.R": armR, "claw.R": handR, "pincer.R": jawR,
}
for name, (parts, hip) in legs.items():
    skin_map[name] = parts
body_obj = A.skin(skin_map, rig)

LEGS = [(f"leg{i}.{sd}", i, 1 if sd == "L" else -1) for sd in ("L", "R") for i in (1, 2, 3)]
GB = 2.0 if ELITE else 1.0   # big claw heavier: slower/greater swing reads via amplitude


def lift(s, deg):
    """Leg raise: (ax, ay, az) lifting the tip of a side-s leg by deg."""
    return (0, -s * deg, 0)


# ---------------------------------------------------------------- animation
# Idle (48f): shell bob, leg shuffle (wave), claws click, eye blink, coral sway
with Act(rig, "Idle", 48) as a:
    a.loop_l("body", 4, lambda t: (0, 0, 0.012 * S(t)))
    a.loop_r("body", 4, lambda t: (1.5 * S(t, 0.25), 1.5 * S(t), 0))
    for name, i, s in LEGS:
        ph = i * 0.17 + (0.5 if s < 0 else 0)
        a.loop_r(name, 8, lambda t, s=s, ph=ph: (0, -s * 4 * max(0, S(2 * t, ph)), 5 * S(t, ph)))
    for s, sd in ((1, "L"), (-1, "R")):
        a.loop_r(f"arm.{sd}", 4, lambda t, s=s: (-4 * S(t, 0.1 if s > 0 else 0.6), 0, 0))
        a.keys_r(f"pincer.{sd}", [(0, (0, 0, 0)), (14 + (s < 0) * 6, (0, 0, 0)), (17 + (s < 0) * 6, (-24, 0, 0)),
                                  (19 + (s < 0) * 6, (2, 0, 0)), (22 + (s < 0) * 6, (-18, 0, 0)),
                                  (24 + (s < 0) * 6, (0, 0, 0)), (48, (0, 0, 0))])
    a.loop_r("coral.L", 4, lambda t: (3 * S(t, -0.1), 4 * S(t, 0.15), 0))
    a.loop_r("coral.R", 4, lambda t: (3 * S(t, -0.2), -4 * S(t, 0.05), 0))
    for f, k in [(0, 1), (30, 1), (32, 0.1), (34, 1), (48, 1)]:
        a.s("eyes", f, 1, 1, k)

# Run (20f): sideways scuttle in place, rippling legs, body sways side to side
with Act(rig, "Run", 20) as a:
    a.loop_l("body", 8, lambda t: (0.03 * S(t), 0, 0.015 * abs(S(t, 0.25)) - 0.005))
    a.loop_r("body", 8, lambda t: (0, -6 * S(t), 3 * S(t, 0.25)))
    for name, i, s in LEGS:
        ph = i * 0.18 + (0.5 if s < 0 else 0)
        a.loop_r(name, 8, lambda t, s=s, ph=ph: (12 * C(t, ph), -s * 16 * max(0, S(t, ph)), 0))
    for s, sd in ((1, "L"), (-1, "R")):
        a.loop_r(f"arm.{sd}", 4, lambda t, s=s: (-10 + 5 * S(2 * t, 0.1), 0, s * 4 * S(t)))
        a.loop_r(f"pincer.{sd}", 4, lambda t, s=s: (-10 - 10 * S(2 * t, 0 if s > 0 else 0.5), 0, 0))
    a.loop_r("coral.L", 4, lambda t: (0, 8 * S(t, -0.15), 0))
    a.loop_r("coral.R", 4, lambda t: (0, 8 * S(t, -0.2), 0))

# Attack (25f, impact f10): raise claw back (jaw open) -> SNAP forward -> follow through, recover
A_SIDE = "L"
with Act(rig, "Attack", 25) as a:
    a.keys_r("body", [(0, (0, 0, 0)), (6, (-8, 4, 6)), (10, (12, -2, -6)), (14, (10, -2, -4)), (20, (2, 0, 0)),
                      (25, (0, 0, 0))])
    a.keys_l("body", [(0, (0, 0, 0)), (6, (0, 0.03, 0.02)), (10, (0, -0.06, -0.01)), (14, (0, -0.05, -0.01)),
                      (25, (0, 0, 0))])
    a.keys_r(f"arm.{A_SIDE}", [(0, (0, 0, 0)), (6, (-65, 15, 10)), (8, (-62, 15, 10)), (10, (18, 0, -12)),
                               (13, (24, 0, -14)), (19, (5, 0, -3)), (25, (0, 0, 0))])
    a.keys_l(f"arm.{A_SIDE}", [(0, (0, 0, 0)), (6, (0, 0.04, 0.02)), (10, (0, -0.1, 0)), (14, (0, -0.09, 0)),
                               (25, (0, 0, 0))])
    a.keys_r(f"claw.{A_SIDE}", [(0, (0, 0, 0)), (6, (-20, 0, 0)), (10, (10, 0, 0)), (14, (14, 0, 0)), (25, (0, 0, 0))])
    a.keys_r(f"pincer.{A_SIDE}", [(0, (0, 0, 0)), (5, (-45, 0, 0)), (9, (-48, 0, 0)), (10, (4, 0, 0)), (12, (0, 0, 0)),
                                  (16, (-10, 0, 0)), (19, (0, 0, 0)), (25, (0, 0, 0))])
    a.keys_r("arm.R", [(0, (0, 0, 0)), (6, (-15, 0, -8)), (10, (-5, 0, 6)), (25, (0, 0, 0))])
    a.keys_r("pincer.R", [(0, (0, 0, 0)), (6, (-20, 0, 0)), (10, (0, 0, 0)), (25, (0, 0, 0))])
    for name, i, s in LEGS:
        a.keys_r(name, [(0, (0, 0, 0)), (6, lift(s, -4)), (10, (0, -s * -6, -s * 6)), (16, lift(s, 3)), (25, (0, 0, 0))])
    a.keys_r("coral.L", [(0, (0, 0, 0)), (6, (-6, 0, 0)), (10, (8, 0, 0)), (14, (-6, 0, 0)), (19, (3, 0, 0)),
                         (25, (0, 0, 0))])
    a.keys_r("coral.R", [(0, (0, 0, 0)), (6, (-6, 0, 0)), (11, (9, 0, 0)), (15, (-6, 0, 0)), (20, (3, 0, 0)),
                         (25, (0, 0, 0))])
    a.keys_s("eyes", [(0, 1), (6, (1, 1, 0.5)), (10, (1.3, 1, 1.3)), (16, 1), (25, 1)])

# Cast (36f, release f22): retreat into shell (eyes dim) -> burst out, corals flare, claws raised
with Act(rig, "Cast", 36) as a:
    a.keys_l("body", [(0, (0, 0, 0)), (8, (0, 0, -0.04)), (18, (0, 0, -0.045)), (22, (0, 0, 0.07)), (27, (0, 0, 0.02)),
                      (36, (0, 0, 0))])
    a.keys_r("body", [(0, (0, 0, 0)), (8, (6, 0, 0)), (14, (5, 1.5, 0)), (16, (5, -1.5, 0)), (18, (6, 0, 0)),
                      (22, (-12, 0, 0)), (28, (-4, 0, 0)), (36, (0, 0, 0))])
    for s, sd in ((1, "L"), (-1, "R")):
        a.keys_r(f"arm.{sd}", [(0, (0, 0, 0)), (8, (20, 0, s * 35)), (18, (20, 0, s * 35)), (22, (-80, s * 25, -s * 10)),
                               (28, (-72, s * 20, -s * 8)), (36, (0, 0, 0))])
        a.keys_l(f"arm.{sd}", [(0, (0, 0, 0)), (8, (-s * 0.04, 0.08, 0.02)), (18, (-s * 0.04, 0.08, 0.02)),
                               (22, (0, 0, 0.03)), (30, (0, 0, 0)), (36, (0, 0, 0))])
        a.keys_r(f"pincer.{sd}", [(0, (0, 0, 0)), (8, (0, 0, 0)), (22, (-40, 0, 0)), (25, (0, 0, 0)), (27, (-35, 0, 0)),
                                  (30, (0, 0, 0)), (36, (0, 0, 0))])
    for name, i, s in LEGS:
        a.keys_r(name, [(0, (0, 0, 0)), (8, (0, -s * 35, 0)), (18, (0, -s * 35, 0)), (22, (0, s * 6, 0)),
                        (28, (0, 0, 0)), (36, (0, 0, 0))])
    for sd, sg in (("L", 1), ("R", -1)):
        a.keys_r(f"coral.{sd}", [(0, (0, 0, 0)), (8, (0, -sg * 4, 0)), (18, (0, -sg * 4, 0)), (22, (-6, sg * 18, 0)),
                                 (26, (4, -sg * 6, 0)), (30, (-2, sg * 6, 0)), (36, (0, 0, 0))])
        a.keys_s(f"coral.{sd}", [(0, 1), (18, (0.95, 0.95, 0.9)), (22, (1.15, 1.15, 1.25)), (28, 1.05), (36, 1)])
    a.keys_l("eyes", [(0, (0, 0, 0)), (8, (0, 0.07, 0)), (18, (0, 0.07, 0)), (22, (0, -0.01, 0)), (36, (0, 0, 0))])
    a.keys_s("eyes", [(0, 1), (8, (0.4, 1, 0.4)), (18, (0.4, 1, 0.4)), (22, (1.45, 1, 1.45)), (30, 1.1), (36, 1)])

# Hit (12f): shell rocks back, claws flail, eyes squeeze
with Act(rig, "Hit", 12) as a:
    a.keys_r("body", [(0, (0, 0, 0)), (2, (-16, 5, 0)), (5, (6, -2, 0)), (8, (-3, 1, 0)), (12, (0, 0, 0))])
    a.keys_l("body", [(0, (0, 0, 0)), (2, (0, 0.05, 0.01)), (6, (0, 0.01, 0)), (12, (0, 0, 0))])
    for s, sd in ((1, "L"), (-1, "R")):
        a.keys_r(f"arm.{sd}", [(0, (0, 0, 0)), (2, (-45, s * 15, s * 20)), (5, (-15, -s * 5, -s * 10)),
                               (8, (-25, s * 5, s * 5)), (12, (0, 0, 0))])
        a.keys_r(f"pincer.{sd}", [(0, (0, 0, 0)), (2, (-40, 0, 0)), (5, (0, 0, 0)), (7, (-25, 0, 0)), (12, (0, 0, 0))])
    for name, i, s in LEGS:
        a.keys_r(name, [(0, (0, 0, 0)), (2, (0, -s * (10 + 5 * i), 4 * i)), (6, (0, -s * 3, 0)), (12, (0, 0, 0))])
    for sd in ("L", "R"):
        a.keys_r(f"coral.{sd}", [(0, (0, 0, 0)), (3, (-14, 0, 0)), (6, (8, 0, 0)), (9, (-3, 0, 0)), (12, (0, 0, 0))])
    a.keys_s("eyes", [(0, 1), (1, (1.2, 1, 0.15)), (8, (1.2, 1, 0.2)), (12, 1)])

# Die (32f): stagger, flip onto its side/back, legs curl, claws go limp, eyes go out
with Act(rig, "Die", 32) as a:
    a.keys_r("root", [(0, (0, 0, 0)), (6, (0, 8, 0)), (12, (0, -10, 0)), (20, (0, 70, 0)), (24, (0, 112, 0)),
                      (27, (0, 104, 0)), (32, (0, 108, 0))])
    a.keys_l("root", [(0, (0, 0, 0)), (12, (0, 0, 0.04)), (20, (-0.1, 0, 0.3)), (24, (-0.28, 0, 0.36)),
                      (27, (-0.26, 0, 0.34)), (32, (-0.28, 0, 0.35))])
    a.keys_r("body", [(0, (0, 0, 0)), (6, (-10, 0, 0)), (12, (6, 0, 0)), (32, (0, 0, 0))])
    for s, sd in ((1, "L"), (-1, "R")):
        a.keys_r(f"arm.{sd}", [(0, (0, 0, 0)), (6, (-40, s * 10, 0)), (14, (-60, s * 15, 0)), (24, (15, -s * 20, 0)),
                               (28, (5, -s * 25, 0)), (32, (8, -s * 25, 0))])
        a.keys_r(f"pincer.{sd}", [(0, (0, 0, 0)), (6, (-35, 0, 0)), (24, (-20, 0, 0)), (32, (-28, 0, 0))])
    for name, i, s in LEGS:
        a.keys_r(name, [(0, (0, 0, 0)), (6, (0, -s * 10, 0)), (16, (0, -s * 25, 0)), (24, (0, -s * 60, 0)),
                        (27, (0, -s * 52, 0)), (32, (0, -s * 70, 3 * i))])
    for sd in ("L", "R"):
        a.keys_r(f"coral.{sd}", [(0, (0, 0, 0)), (24, (0, 0, 0)), (26, (8, 0, 0)), (29, (-3, 0, 0)), (32, (0, 0, 0))])
    a.keys_s("eyes", [(0, 1), (6, (1.2, 1, 0.3)), (12, 1), (22, (0.5, 1, 0.08)), (32, (0.05, 1, 0.05))])

# Victory (44f): both claws raised clacking, happy hops, corals sway
with Act(rig, "Victory", 44) as a:
    a.keys_l("body", [(0, (0, 0, 0)), (6, (0, 0, -0.03)), (11, (0, 0, 0.07)), (16, (0, 0, 0)), (22, (0, 0, -0.02)),
                      (27, (0, 0, 0.06)), (32, (0, 0, 0)), (44, (0, 0, 0))])
    a.keys_r("body", [(0, (0, 0, 0)), (11, (-6, 4, 0)), (27, (-6, -4, 0)), (44, (0, 0, 0))])
    for s, sd in ((1, "L"), (-1, "R")):
        keys = [(0, (0, 0, 0)), (6, (-20, 0, 0))]
        for j, f in enumerate(range(10, 38, 4)):
            keys.append((f, (-85 + 8 * (j % 2), s * (18 + 6 * ((j + (s < 0)) % 2)), -s * 10)))
        keys += [(44, (0, 0, 0))]
        a.keys_r(f"arm.{sd}", keys)
        pk = [(0, (0, 0, 0))]
        for f in range(10, 38, 4):
            pk += [(f + (0 if s > 0 else 2), (-35, 0, 0)), (f + (2 if s > 0 else 4), (0, 0, 0))]
        pk += [(44, (0, 0, 0))]
        a.keys_r(f"pincer.{sd}", pk)
    for name, i, s in LEGS:
        a.keys_r(name, [(0, (0, 0, 0)), (6, (0, s * 5, 0)), (11, (0, -s * 12, 0)), (16, (0, 0, 0)),
                        (22, (0, s * 5, 0)), (27, (0, -s * 12, 0)), (32, (0, 0, 0)), (44, (0, 0, 0))])
    for sd, sg in (("L", 1), ("R", -1)):
        a.keys_r(f"coral.{sd}", [(0, (0, 0, 0)), (13, (-5, sg * 8, 0)), (29, (-5, -sg * 6, 0)), (44, (0, 0, 0))])
    a.keys_s("eyes", [(0, 1), (8, (1.2, 1, 0.35)), (38, (1.2, 1, 0.35)), (44, 1)])

finish(EID, rig, body_obj, extra=[("cast", "Cast", 0.6, (75, 0, 30)), ("die", "Die", 1.0, (60, 0, 50)),
                                  ("victory", "Victory", 0.3, (75, 0, 30))])
