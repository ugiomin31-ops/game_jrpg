"""숲 슬라임 (slime): blue translucent jelly with a leaf crown, an ice-blue crystal and a cute face.
Height ~0.7 m incl. crystal. Run: blender -b --factory-startup -P slime.py
"""
import math
import os
import sys

sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from _common import *  # noqa: F401,F403
from _common import A, Act, Vector, S, C

EID = variant("slime")
A.reset_scene()

BLUE_LO, BLUE_MID, BLUE_HI = "#1d6ee0", "#3aa0ff", "#8fe0ff"
LEAF_L, LEAF_D = "#9be35a", "#4c9e2e"

# ---------------------------------------------------------------- body
prof = [(0.0, 0.0), (0.27, 0.0), (0.345, 0.022), (0.372, 0.07), (0.368, 0.14), (0.34, 0.22),
        (0.29, 0.30), (0.225, 0.375), (0.155, 0.44), (0.09, 0.49), (0.04, 0.52), (0.0, 0.53)]
body = A.lathe("slime_body", prof, color=BLUE_MID, mat="M_Clear", seg=32)


def shape(co):
    t = max(0.0, co.z / 0.53)
    co.y *= 0.9
    co.x += -0.03 * t * t      # tip leans to its right (-X) a touch, like the sheet
    co.y += 0.02 * t * t
    # soft belly bulge at the front-bottom
    if co.y < 0:
        co.y -= 0.02 * math.sin(math.pi * min(1.0, co.z / 0.3))
    return co


A.deform(body, shape)
A.apply_transform(body)


def body_col(co):
    t = max(0.0, min(1.0, co.z / 0.53))
    if t < 0.45:
        return mix(BLUE_LO, BLUE_MID, t / 0.45)
    return mix(BLUE_MID, BLUE_HI, (t - 0.45) / 0.55)


paint_vert_fn(body, body_col)

# glossy highlights (upper left of the jelly, as in the sheet)
gl1 = ellipsoid("gloss1", (0.035, 0.01, 0.07), color="#c9f1ff", seg=16, rings=8)
p, n = surf(body, (0, 0, 0.25), dir_from(-58, 44))
orient(gl1, p, n, up=(0.5, 0, 1), offset=0.003)
gl2 = ellipsoid("gloss2", (0.016, 0.008, 0.02), color="#ffffff", seg=10, rings=6)
p, n = surf(body, (0, 0, 0.25), dir_from(-30, 50))
orient(gl2, p, n, offset=0.003)
gl3 = ellipsoid("gloss3", (0.07, 0.008, 0.016), color="#a6e2ff", seg=14, rings=6)
p, n = surf(body, (0, 0, 0.1), dir_from(50, -16))
orient(gl3, p, n, up=(-0.3, 0, 1), offset=0.002)

# inner bubbles (show through M_Clear)
bubbles = []
for i, (x, y, z, r) in enumerate([(0.12, 0.02, 0.12, 0.035), (-0.15, 0.05, 0.08, 0.025), (0.05, 0.1, 0.28, 0.03)]):
    bubbles.append(A.sphere(f"bub{i}", r=r, loc=(x, y, z), color="#a8e4ff", mat="M_Clear", seg=12, rings=8))

# ---------------------------------------------------------------- face
face = []
for s in (-1, 1):
    p, n = surf(body, (0, 0, 0.25), dir_from(s * 17, 8))
    face += cute_eye(f"eye{s}", p, n, w=0.052, h=0.078, iris="#24358a", pupil="#0d1024", depth=0.02, surface=body)
    p, n = surf(body, (0, 0, 0.17), dir_from(s * 33, -6))
    face.append(orient(ellipsoid(f"blush{s}", (0.045, 0.008, 0.024), color="#ff9fc0", seg=12, rings=6), p, n, offset=0.002))
eyes = face[:]
p, n = surf(body, (0, 0, 0.17), dir_from(0, -4))
mouth = smile_mouth("mouth", p, n, w=0.05, h=0.05, inner="#6b1430", tongue="#ff7f9a")

# ---------------------------------------------------------------- leaf crown
crown = []
C0 = (0, 0, 0.2)
for i, (yaw, pitch, L, W, spin) in enumerate([(-160, 70, 0.21, 0.15, 0), (-100, 68, 0.2, 0.145, 10), (-40, 72, 0.2, 0.15, -5),
                                              (25, 70, 0.22, 0.15, 0), (85, 68, 0.2, 0.145, -10), (140, 70, 0.2, 0.14, 5),
                                              (-12, 56, 0.17, 0.13, 25), (52, 55, 0.16, 0.12, -20)]):
    crown.append(skin_leaf(f"leaf{i}", body, C0, yaw, pitch, length=L, width=W, curl=0.7, lift=0.18, back=0.15,
                           light=LEAF_L, dark=LEAF_D, spin=spin, fold=0.12))
stem = A.tube("sprig", [(-0.01, 0.02, 0.5), (0.0, 0.015, 0.58), (0.025, -0.005, 0.63)], radius=0.013, color="#4e9a2c",
              taper_end=0.7)
crown.append(stem)
for i, (d, L) in enumerate([((0.8, -0.3, 0.55), 0.13), ((-0.75, 0.15, 0.65), 0.11)]):
    lf = leaf(f"sprigleaf{i}", length=L, width=0.075, fold=0.3, curl=0.7, light=LEAF_L, dark=LEAF_D)
    place_leaf(lf, Vector((0.025, -0.005, 0.625)), d)
    crown.append(lf)

# vine trailing down its left side with little leaves (hugging the jelly)
vine_pts = []
for i in range(8):
    t = i / 7
    p, n = surf(body, (0, 0, 0.25), dir_from(48 + 22 * t, 48 - 62 * t))
    vine_pts.append(tuple(p + n * 0.01))
vine = A.tube("vine", vine_pts, radius=0.011, color="#3f8a26", taper_end=0.5)
crown_side = [vine]
for i, (yaw, pitch, spin) in enumerate([(56, 22, 50), (66, -2, -40), (72, -10, 60)]):
    crown_side.append(skin_leaf(f"vleaf{i}", body, (0, 0, 0.25), yaw, pitch, length=0.085, width=0.055, curl=0.4,
                                lift=0.5, back=0.0, light=LEAF_L, dark=LEAF_D, spin=spin))

# ---------------------------------------------------------------- crystal (its right, back)
cr_base = Vector((-0.12, 0.07, 0.40))
cr = crystal("crystal", r=0.075, h=0.36, light="#e2f8ff", dark="#2f86ea")
aim(cr, cr_base, (-0.38, 0.12, 1.0), roll=10)
cr2 = crystal("crystal2", r=0.042, h=0.2, light="#e2f8ff", dark="#2f86ea")
aim(cr2, cr_base + Vector((0.06, 0.06, -0.02)), (0.15, 0.45, 1.0), roll=25)
cr3 = crystal("crystal3", r=0.035, h=0.15, light="#e2f8ff", dark="#2f86ea")
aim(cr3, cr_base + Vector((-0.07, -0.05, -0.04)), (-0.8, -0.45, 0.7), roll=5)
crystals = [cr, cr2, cr3]

# ---------------------------------------------------------------- puddle droplets
drops = []
for i, (ang, dist, r) in enumerate([(-120, 0.42, 0.04), (-60, 0.44, 0.03), (-150, 0.47, 0.022), (30, 0.43, 0.035),
                                    (70, 0.46, 0.022), (-95, 0.5, 0.018)]):
    a = math.radians(ang)
    o = A.sphere(f"drop{i}", r=r, loc=(math.cos(a) * dist, math.sin(a) * dist, r * 0.55), scale=(1, 1, 0.75),
                 color="#3a9cf2", mat="M_Clear", seg=14, rings=8)
    A.apply_transform(o)
    paint_vert_fn(o, lambda co, r=r: mix("#1f6fd6", "#9ae0ff", max(0.0, min(1.0, co.z / (r * 1.1)))))
    drops.append(o)

# ---------------------------------------------------------------- rig
rig = make_rig([
    ("root", (0, 0, 0), None),
    ("body", (0, 0, 0), "root"),
    ("eyes", (0, -0.33, 0.24), "body"),
    ("mouth", (0, -0.35, 0.165), "body"),
    ("crown", (-0.03, 0.03, 0.45), "body"),
    ("crystal", (-0.12, 0.08, 0.40), "body"),
    ("drops", (0, 0, 0), "root"),
])
body_obj = A.skin({
    "body": [body, gl1, gl2, gl3] + bubbles + crown_side,
    "eyes": eyes,
    "mouth": mouth,
    "crown": crown,
    "crystal": crystals,
    "drops": drops,
}, rig)

# ---------------------------------------------------------------- animation
# Idle: breathing squash with lagging crown jiggle + blink
with Act(rig, "Idle", 48) as a:
    a.loop_s("body", 8, lambda t: (1 + 0.035 * S(t), 1 + 0.035 * S(t), 1 - 0.06 * S(t)))
    a.loop_r("crown", 8, lambda t: (4 * S(t, -0.15), -3 * C(t, -0.15), 0))
    a.loop_r("crystal", 8, lambda t: (0, 3 * S(t, -0.2), 0))
    for f, k in ((0, 1), (30, 1), (32, 0.1), (34, 1), (48, 1)):
        a.s("eyes", f, 1, 1, k)
    a.loop_s("mouth", 4, lambda t: (1, 1, 1 + 0.12 * S(t)))

# Run: in-place hop with stretch on take-off and squash on landing
with Act(rig, "Run", 20) as a:
    a.keys_s("body", [(0, (1.18, 1.18, 0.78)), (4, (0.88, 0.88, 1.2)), (10, (0.96, 0.96, 1.06)),
                      (15, (1.06, 1.06, 0.94)), (17, (1.2, 1.2, 0.76)), (20, (1.18, 1.18, 0.78))])
    a.keys_l("body", [(0, (0, 0, 0)), (4, (0, -0.02, 0.08)), (10, (0, -0.03, 0.17)), (15, (0, -0.01, 0.05)),
                      (17, (0, 0, 0)), (20, (0, 0, 0))])
    a.keys_r("body", [(0, (0, 0, 0)), (4, (8, 0, 0)), (10, (2, 0, 0)), (16, (-6, 0, 0)), (20, (0, 0, 0))])
    a.keys_r("crown", [(0, (-12, 0, 0)), (5, (14, 0, 0)), (11, (-6, 0, 0)), (17, (-14, 0, 0)), (20, (-12, 0, 0))])
    a.keys_r("crystal", [(0, (-6, 4, 0)), (6, (8, -3, 0)), (12, (-3, 2, 0)), (20, (-6, 4, 0))])
    a.keys_s("drops", [(0, 1), (20, 1)])

# Attack (26f, impact at f10): squash windup -> lunge stretch -> splat on target -> recover
with Act(rig, "Attack", 26) as a:
    a.keys_s("body", [(0, 1), (5, (1.25, 1.25, 0.68)), (8, (0.84, 0.84, 1.3)), (10, (1.32, 1.1, 0.72)),
                      (13, (0.94, 0.94, 1.1)), (17, (1.05, 1.05, 0.95)), (21, (0.99, 0.99, 1.01)), (26, 1)])
    a.keys_l("body", [(0, (0, 0, 0)), (5, (0, 0.06, 0)), (8, (0, -0.25, 0.18)), (10, (0, -0.42, 0.02)),
                      (14, (0, -0.3, 0.06)), (19, (0, -0.08, 0)), (26, (0, 0, 0))])
    a.keys_r("body", [(0, (0, 0, 0)), (5, (-12, 0, 0)), (8, (22, 0, 0)), (10, (14, 0, 0)), (14, (-6, 0, 0)),
                      (19, (2, 0, 0)), (26, (0, 0, 0))])
    a.keys_r("crown", [(0, (0, 0, 0)), (5, (12, 0, 0)), (8, (-22, 0, 0)), (11, (26, 0, 0)), (15, (-10, 0, 0)),
                       (20, (4, 0, 0)), (26, (0, 0, 0))])
    a.keys_r("crystal", [(0, (0, 0, 0)), (6, (10, 6, 0)), (9, (-18, -6, 0)), (12, (16, 4, 0)), (18, (-5, 0, 0)),
                         (26, (0, 0, 0))])
    a.keys_s("mouth", [(0, 1), (5, (0.8, 1, 0.6)), (8, (1.25, 1, 1.6)), (12, (1.2, 1, 1.4)), (18, 1), (26, 1)])
    a.keys_s("eyes", [(0, 1), (5, (1.1, 1, 0.45)), (8, (1, 1, 1.1)), (14, 1), (26, 1)])

# Cast (36f, release at f22): gathers itself, crystal flares, rises and bursts
with Act(rig, "Cast", 36) as a:
    a.keys_s("body", [(0, 1), (8, (1.12, 1.12, 0.84)), (14, (1.16, 1.16, 0.8)), (18, (1.18, 1.18, 0.78)),
                      (22, (0.86, 0.86, 1.3)), (26, (1.08, 1.08, 0.92)), (31, (0.98, 0.98, 1.03)), (36, 1)])
    a.keys_l("body", [(0, (0, 0, 0)), (18, (0, 0, 0)), (22, (0, 0, 0.08)), (27, (0, 0, 0)), (36, (0, 0, 0))])
    for f in range(8, 19, 2):
        a.r("body", f, 0, 2.5 * (1 if (f // 2) % 2 else -1), 0)
    a.r("body", 0, 0, 0, 0)
    a.r("body", 22, -6, 0, 0)
    a.r("body", 28, 3, 0, 0)
    a.r("body", 36, 0, 0, 0)
    a.keys_s("crystal", [(0, 1), (10, 1.1), (18, 1.2), (22, 1.45), (26, 1.1), (36, 1)])
    a.keys_r("crystal", [(0, (0, 0, 0)), (18, (0, 0, 20)), (22, (-8, 6, 60)), (30, (0, 0, 0)), (36, (0, 0, 0))])
    a.keys_r("crown", [(0, (0, 0, 0)), (14, (-6, 4, 0)), (22, (-16, 0, 0)), (26, (12, 0, 0)), (32, (-3, 0, 0)),
                       (36, (0, 0, 0))])
    a.keys_s("eyes", [(0, 1), (8, (1, 1, 0.35)), (19, (1, 1, 0.35)), (22, (1.15, 1, 1.15)), (30, 1), (36, 1)])
    a.keys_s("mouth", [(0, 1), (8, (0.7, 1, 0.4)), (19, (0.7, 1, 0.4)), (22, (1.3, 1, 1.6)), (30, 1), (36, 1)])

# Hit (12f): knocked back, flattened sideways, wobble
with Act(rig, "Hit", 12) as a:
    a.keys_s("body", [(0, 1), (2, (1.25, 0.8, 0.78)), (5, (0.88, 1.05, 1.15)), (8, (1.06, 1, 0.95)), (12, 1)])
    a.keys_l("body", [(0, (0, 0, 0)), (2, (0, 0.12, 0.02)), (6, (0, 0.08, 0)), (12, (0, 0, 0))])
    a.keys_r("body", [(0, (0, 0, 0)), (2, (-16, 0, 0)), (5, (8, 0, 0)), (8, (-3, 0, 0)), (12, (0, 0, 0))])
    a.keys_r("crown", [(0, (0, 0, 0)), (2, (20, 0, 0)), (5, (-16, 0, 0)), (8, (6, 0, 0)), (12, (0, 0, 0))])
    a.keys_s("eyes", [(0, 1), (1, (1.2, 1, 0.2)), (8, (1.2, 1, 0.25)), (12, 1)])
    a.keys_s("mouth", [(0, 1), (2, (0.6, 1, 1.3)), (12, 1)])

# Die (32f): shudder, melt into a puddle; crown and crystal topple onto it
with Act(rig, "Die", 32) as a:
    a.keys_s("body", [(0, 1), (4, (0.9, 0.9, 1.12)), (8, (1.08, 1.08, 0.9)), (14, (1.3, 1.3, 0.62)),
                      (22, (1.55, 1.5, 0.28)), (32, (1.62, 1.58, 0.2))])
    a.keys_r("body", [(0, (0, 0, 0)), (4, (-8, 0, 0)), (8, (4, 0, 0)), (32, (0, 0, 0))])
    a.keys_r("crown", [(0, (0, 0, 0)), (8, (10, -6, 0)), (16, (-10, 8, 0)), (24, (6, -20, 10)), (32, (4, -24, 12))])
    a.keys_r("crystal", [(0, (0, 0, 0)), (12, (0, 10, 0)), (22, (10, 60, 0)), (26, (8, 52, 0)), (32, (8, 56, 0))])
    a.keys_s("crystal", [(0, 1), (22, 1), (32, (1, 0.7, 0.7))])
    a.keys_s("eyes", [(0, 1), (4, (1.1, 1, 0.15)), (32, (1.3, 1, 0.1))])
    a.keys_s("mouth", [(0, 1), (6, (0.5, 1, 0.5)), (32, (0.4, 1, 0.3))])
    a.keys_s("drops", [(0, 1), (22, 1.2), (32, 1.25)])

# Victory (44f): two happy bounces with a spin
with Act(rig, "Victory", 44) as a:
    a.keys_s("body", [(0, 1), (4, (1.2, 1.2, 0.78)), (8, (0.86, 0.86, 1.25)), (14, (1, 1, 1)),
                      (19, (1.22, 1.22, 0.76)), (23, (0.86, 0.86, 1.25)), (30, (1, 1, 1)), (35, (1.15, 1.15, 0.82)),
                      (40, (0.98, 0.98, 1.02)), (44, 1)])
    a.keys_l("body", [(0, (0, 0, 0)), (4, (0, 0, 0)), (10, (0, 0, 0.2)), (16, (0, 0, 0.02)), (19, (0, 0, 0)),
                      (26, (0, 0, 0.26)), (33, (0, 0, 0)), (44, (0, 0, 0))])
    a.keys_r("body", [(0, (0, 0, 0)), (19, (0, 0, 0)), (33, (0, 0, 360)), (44, (0, 0, 360))])
    a.keys_r("crown", [(0, (0, 0, 0)), (9, (-14, 0, 0)), (16, (12, 0, 0)), (24, (-14, 0, 0)), (34, (14, 0, 0)),
                       (40, (-4, 0, 0)), (44, (0, 0, 0))])
    a.keys_s("eyes", [(0, 1), (8, (1.1, 1, 0.3)), (36, (1.1, 1, 0.3)), (40, 1), (44, 1)])
    a.keys_s("mouth", [(0, 1), (8, (1.3, 1, 1.5)), (36, (1.3, 1, 1.5)), (44, 1)])

finish(EID, rig, body_obj, extra=[("cast", "Cast", 0.6, (75, 0, 30)), ("die", "Die", 1.0, (70, 0, 35))])
