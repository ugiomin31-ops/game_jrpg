"""용암 슬라임 (magma_slime) — molten blob with rock-crust plates, glowing face, lava droplets, crown flames.

Height ~0.8 m (body 0.62 + flames). Run: blender -b --factory-startup -P magma_slime.py
"""
import math
import os
import random
import sys

sys.path.append(os.path.dirname(os.path.abspath(__file__)))
import _common as C  # noqa: E402
from _common import A, Vector, bmesh, bpy, kf, sw  # noqa: E402

PROFILE = [(0.0, 0.0), (0.26, 0.0), (0.36, 0.02), (0.42, 0.07), (0.445, 0.14), (0.44, 0.22), (0.42, 0.30),
           (0.385, 0.38), (0.33, 0.46), (0.26, 0.53), (0.17, 0.585), (0.08, 0.61), (0.0, 0.62)]
SY = 0.92  # front/back squash of the blob


def r_at(z, prof=PROFILE):
    for (r0, z0), (r1, z1) in zip(prof, prof[1:]):
        if z0 <= z <= z1:
            k = (z - z0) / max(z1 - z0, 1e-6)
            return r0 + (r1 - r0) * k
    return 0.0


def front_y(x, z, out=0.0):
    r = r_at(z) + out
    return -SY * math.sqrt(max(r * r - x * x, 0.0))


def smooth_profile(prof, n=3):
    """Catmull-Rom resample for a rounder lathe."""
    pts = [Vector((r, z)) for r, z in prof]
    out = []
    for i in range(len(pts) - 1):
        p0 = pts[max(i - 1, 0)]
        p1, p2 = pts[i], pts[i + 1]
        p3 = pts[min(i + 2, len(pts) - 1)]
        for k in range(n):
            t = k / n
            t2, t3 = t * t, t * t * t
            v = 0.5 * ((2 * p1) + (-p0 + p2) * t + (2 * p0 - 5 * p1 + 4 * p2 - p3) * t2 + (-p0 + 3 * p1 - 3 * p2 + p3) * t3)
            out.append((max(v.x, 0.0), v.y))
    out.append(prof[-1])
    return out


def crust(seed=7):
    """Rock plates on the upper shell, split along Voronoi-ish cracks so the molten core shows through."""
    rnd = random.Random(seed)
    prof = [(r * 1.0 + (0.018 if r > 0 else 0), z + 0.012) for r, z in smooth_profile(PROFILE, 3)]
    o = A.lathe("crust", prof, color="#3a2824", seg=56)
    o.scale = (1, SY, 1)
    A.apply_transform(o)
    c0 = Vector((0, 0, 0.26))
    n = 26
    seeds = []
    for i in range(n):  # fibonacci sphere + jitter
        z = 1 - 2 * (i + 0.5) / n
        rr = math.sqrt(1 - z * z)
        a = i * math.pi * (3 - math.sqrt(5)) + rnd.uniform(-0.25, 0.25)
        seeds.append(Vector((math.cos(a) * rr, math.sin(a) * rr, z + rnd.uniform(-0.08, 0.08))).normalized())

    def keep(s):
        if s.z < -0.15:
            return False
        if s.y < -0.35 and s.z < 0.62:  # molten face window
            return False
        if s.z < 0.15 and s.y < 0.2:
            return rnd.random() < 0.35
        return True
    keepers = [keep(s) for s in seeds]
    bm = bmesh.new()
    bm.from_mesh(o.data)
    lay = bm.faces.layers.int.new("cell")
    kill = []
    for f in bm.faces:
        d = (f.calc_center_median() - c0).normalized()
        ds = sorted(((d - s).length, i) for i, s in enumerate(seeds))
        if ds[1][0] - ds[0][0] < 0.075 or not keepers[ds[0][1]]:
            kill.append(f)
        else:
            f[lay] = ds[0][1]
    bmesh.ops.delete(bm, geom=kill, context="FACES")
    shades = ["#3b2a26", "#4a332c", "#2f2220", "#553a30", "#3f2c2a"]
    cell_col = {i: C.rgb(rnd.choice(shades)) for i in range(n)}
    bm.to_mesh(o.data)
    bm.free()
    me = o.data
    attr = me.color_attributes["Col"]
    cells = me.attributes["cell"].data
    for p in me.polygons:
        col = cell_col[cells[p.index].value]
        # lighter top faces for a toon highlight on each plate
        if p.normal.z > 0.6:
            col = C.shade(col, 1.18)
        for li in p.loop_indices:
            attr.data[li].color_srgb = col
    md = o.modifiers.new("solid", "SOLIDIFY")
    md.thickness = 0.045
    md.offset = 1.0
    md.use_rim = True
    A.apply_modifiers(o)
    me.attributes.remove(me.attributes["cell"])
    off = Vector((seed * 1.3, 2.1, 0.7))
    C.A.deform(o, lambda v: v + C.noise.noise_vector(v * 9 + off) * 0.008)
    A.shade_smooth(o, angle=35)
    return o


def build():
    A.reset_scene()
    rnd = random.Random(11)

    # ---------------- body (molten core)
    body = A.lathe("core", smooth_profile(PROFILE, 3), color="#ff7020", mat="M_Emit", seg=40)
    body.scale = (1, SY, 1)
    A.apply_transform(body)
    C.vgrad(body, [(0, "#ffd860"), (0.18, "#ffa030"), (0.45, "#f05a1c"), (0.8, "#b8261a"), (1, "#7a1712")])
    # brighter molten belly glow on the front
    C.paint_where(body, lambda c, n: n.y < -0.75 and 0.05 < c.z < 0.2, "#ffc048")
    plates = crust()

    # a few loose crust rocks sitting on the shoulders (chunky silhouette like the art)
    top_rocks = []
    for i, (x, z, s) in enumerate([(-0.28, 0.42, 0.11), (0.3, 0.38, 0.1), (0.05, 0.58, 0.12), (-0.12, 0.55, 0.09)]):
        y = 0.08 if i != 2 else 0.05
        rk = C.rock(f"trock{i}", (s * 1.3, s, s * 0.8), loc=(x, y, z), rot=(rnd.uniform(-20, 20), rnd.uniform(-20, 20), rnd.uniform(0, 90)),
                    color="#2e2220", seed=i + 3, amp=0.22)
        top_rocks.append(rk)

    # ---------------- face
    face = []
    for side in (1, -1):
        x, z = 0.115 * side, 0.33
        y = front_y(x, z)
        nrm = Vector((x * 0.9, y, 0.08)).normalized()
        rim = A.sphere(f"eyerim{side}", r=1, loc=(0, 0, 0), scale=(0.062, 0.03, 0.082), color="#2a0c08", seg=20, rings=12)
        rim.location = Vector((x, y, z)) + nrm * 0.004
        C.orient_z(rim, (0, 0, 1))
        rim.rotation_euler = Vector((0, 0, 1)).rotation_difference(Vector((0, -1, 0))).to_euler()
        rim.rotation_euler = (math.radians(0), 0, math.atan2(nrm.x, -nrm.y))
        iris = A.sphere(f"eye{side}", r=1, loc=Vector((x, y, z)) + nrm * 0.016, scale=(0.046, 0.025, 0.066),
                        rot=(0, 0, math.degrees(math.atan2(nrm.x, -nrm.y))), color="#ffd23a", mat="M_Emit", seg=20, rings=12)
        C.vgrad(iris, [(0, "#ffb020"), (0.6, "#ffe066"), (1, "#fff2b0")])
        hl = A.sphere(f"eyehl{side}", r=0.016, loc=Vector((x - 0.014 * side + 0.01, y, z + 0.03)) + nrm * 0.036, color="#ffffff", mat="M_Emit", seg=10, rings=6)
        face += [rim, iris, hl]
    # open smile: dark mouth with a red tongue
    mz = 0.215
    my = front_y(0, mz)
    mouth_pts = [(-0.06 + 0.12 * i / 10, -0.004 * math.sin(math.pi * i / 10)) for i in range(11)]
    mouth_pts += [(0.06 * math.cos(math.pi * i / 10), -0.055 * math.sin(math.pi * i / 10)) for i in range(1, 10)]
    mouth = A.extrude_shape("mouth", mouth_pts, depth=0.04, loc=(0, my + 0.006, mz), color="#3a0806")
    tongue = A.sphere("tongue", r=1, loc=(0, my - 0.004, mz - 0.038), scale=(0.035, 0.014, 0.016), color="#e04848")
    face_body = [mouth, tongue]

    # ---------------- crown flames
    flames = []
    flame_stops = [(0, "#ffe680"), (0.35, "#ffb030"), (0.7, "#ff6a1c"), (1, "#d8301a")]
    for i, (x, y, h, r, cx, cy, tilt) in enumerate([
            (0.0, 0.03, 0.30, 0.085, -0.25, 0.15, 0), (-0.09, 0.05, 0.2, 0.06, -0.35, 0.1, -18),
            (0.09, 0.0, 0.22, 0.06, 0.3, 0.1, 16), (0.02, 0.1, 0.17, 0.05, 0.1, 0.4, 0)]):
        fl = C.flame(f"flame{i}", h=h, r=r, loc=(x, y, 0.54), rot=(0, tilt, 0), curl=(cx, cy), stops=flame_stops, seg=14)
        flames.append(fl)

    # ---------------- floating lava droplets
    drops = []
    for i, (x, y, z, r) in enumerate([(-0.48, -0.05, 0.5, 0.045), (0.5, 0.0, 0.42, 0.04), (-0.4, 0.15, 0.72, 0.032), (0.38, 0.12, 0.7, 0.036)]):
        d = A.sphere(f"drop{i}", r=r, loc=(x, y, z), color="#ff5a1a", mat="M_Emit", seg=14, rings=8)
        C.vgrad(d, [(0, "#a8160e"), (0.6, "#ff5020"), (1, "#ffc060")])
        h = A.sphere(f"drophl{i}", r=r * 0.32, loc=(x - r * 0.35, y - r * 0.55, z + r * 0.4), color="#fff0c0", mat="M_Emit", seg=8, rings=5)
        drops.append([d, h])

    # ---------------- ground: lava puddle + rocks
    pud = A.cyl("puddle", r=0.52, depth=0.025, loc=(0, 0, 0.012), color="#ff8a24", mat="M_Emit", seg=40)
    A.deform(pud, lambda v: Vector((v.x * (1 + 0.12 * math.sin(math.atan2(v.y, v.x) * 5)), v.y * (1 + 0.12 * math.sin(math.atan2(v.y, v.x) * 5)), v.z)))
    C.vgrad(pud, [(0, "#d84a14"), (1, "#ffb43a")])
    ground = [pud]
    for i, (a, dist, s) in enumerate([(200, 0.47, 0.13), (235, 0.5, 0.09), (320, 0.48, 0.12), (-20, 0.52, 0.08), (90, 0.46, 0.14), (140, 0.5, 0.1), (40, 0.5, 0.09)]):
        ar = math.radians(a)
        ground.append(C.rock(f"brock{i}", (s * 1.2, s, s * 0.85), loc=(math.cos(ar) * dist, math.sin(ar) * dist, s * 0.3),
                             rot=(rnd.uniform(-15, 15), rnd.uniform(-15, 15), rnd.uniform(0, 180)), color=rnd.choice(["#2a1e1c", "#3a2a26", "#33241f"]), seed=i + 20, amp=0.25))
    # tiny glowing splashes
    for i, (a, dist) in enumerate([(250, 0.6), (300, 0.58), (20, 0.62), (160, 0.6)]):
        ar = math.radians(a)
        ground.append(A.sphere(f"splash{i}", r=0.03, loc=(math.cos(ar) * dist, math.sin(ar) * dist, 0.012), scale=(1.4, 1.1, 0.5), color="#ffb040", mat="M_Emit", seg=10, rings=6))

    # ---------------- rig
    bones = [("root", (0, 0, 0), (0, 0, 0.12), None),
             ("body", (0, 0, 0), (0, 0, 0.32), "root"),
             ("eyes", (0, -0.36, 0.33), (0, -0.46, 0.33), "body"),
             ("flame", (0, 0.03, 0.54), (0, 0.03, 0.78), "body")]
    for i, grp in enumerate(drops):
        p = grp[0].location
        bones.append((f"drop{i}", tuple(p), (p.x, p.y, p.z + 0.08), "root"))
    rig = C.new_rig(bones)
    parts = {"root": ground, "body": [body, plates] + top_rocks + face_body, "eyes": face, "flame": flames}
    for i, grp in enumerate(drops):
        parts[f"drop{i}"] = grp

    animate(rig)
    C.finish("magma_slime", rig, parts)


def animate(rig):
    D = ["drop0", "drop1", "drop2", "drop3"]

    def drops_idle(L, amp=0.05, speed=1):
        tr = {}
        for i, d in enumerate(D):
            ph = i * 0.27
            tr[d] = {"loc": (lambda f, ph=ph: (0.02 * sw(f, L / speed, ph + 0.25), 0.02 * sw(f, L / speed, ph), amp * sw(f, L / speed, ph))),
                     "scl": (lambda f, ph=ph: 1 + 0.08 * sw(f, L / (2 * speed), ph))}
        return tr

    # Idle 48: double breathing bubble, flame flicker, blink
    L = 48
    t = {"body": {"scl": lambda f: (1 + 0.035 * sw(f, 24, 0.25), 1 + 0.035 * sw(f, 24, 0.25), 1 - 0.05 * sw(f, 24, 0.25)),
                  "rot": lambda f: (1.5 * sw(f, 48), 2 * sw(f, 48, 0.25), 0)},
         "flame": {"rot": lambda f: (6 * sw(f, 16), 8 * sw(f, 24, 0.3), 0),
                   "scl": lambda f: (1 + 0.08 * sw(f, 12, 0.5), 1 + 0.08 * sw(f, 12, 0.5), 1 + 0.16 * sw(f, 8))},
         "eyes": {"scl": [(0, (1, 1, 1)), (30, (1, 1, 1)), (32, (1.05, 1, 0.1)), (35, (1, 1, 1)), (48, (1, 1, 1))]}}
    t.update(drops_idle(L))
    C.act(rig, "Idle", L, t)

    # Run 20: hop forward with squash & stretch
    L = 20
    t = {"body": {"loc": [(0, (0, 0, 0)), (4, (0, 0, 0.03)), (9, (0, 0, 0.16), "o"), (14, (0, 0, 0.0), "i"), (20, (0, 0, 0))],
                  "scl": [(0, (1.12, 1.12, 0.84)), (4, (0.9, 0.9, 1.16), "o"), (9, (0.98, 0.98, 1.04)), (14, (1.0, 1.0, 1.0)),
                          (16, (1.16, 1.16, 0.8), "o"), (20, (1.12, 1.12, 0.84))],
                  "rot": [(0, (6, 0, 0)), (5, (14, 0, 0)), (10, (4, 0, 0)), (14, (-2, 0, 0)), (17, (8, 0, 0)), (20, (6, 0, 0))]},
         "flame": {"rot": [(0, (-6, 0, 0)), (5, (-22, 0, 0)), (11, (8, 0, 0)), (16, (-14, 0, 0)), (20, (-6, 0, 0))]},
         "eyes": {"scl": [(0, (1, 1, 1)), (20, (1, 1, 1))]}}
    for i, d in enumerate(D):
        t[d] = {"loc": (lambda f, i=i: (0, 0.05 * sw(f, 20, i * 0.2), 0.06 * sw(f, 20, i * 0.25 + 0.1)))}
    C.act(rig, "Run", L, t)

    # Attack 24 (hit @ ~10): coil back, lunge-bite forward, splat, recover
    L = 24
    t = {"body": {"rot": [(0, (0, 0, 0)), (6, (-16, 0, 0)), (10, (26, 0, 0), "o"), (14, (12, 0, 0)), (24, (0, 0, 0))],
                  "loc": [(0, (0, 0, 0)), (6, (0, 0.07, 0)), (10, (0, -0.34, 0.08), "o"), (14, (0, -0.3, 0.0)), (24, (0, 0, 0))],
                  "scl": [(0, (1, 1, 1)), (6, (1.14, 1.14, 0.8)), (10, (0.84, 0.84, 1.24), "o"), (13, (1.18, 1.18, 0.82)),
                          (17, (0.96, 0.96, 1.05)), (24, (1, 1, 1))]},
         "flame": {"rot": [(0, (0, 0, 0)), (6, (14, 0, 0)), (10, (-34, 0, 0), "o"), (15, (12, 0, 0)), (24, (0, 0, 0))],
                   "scl": [(0, (1, 1, 1)), (10, (1.2, 1.2, 1.4)), (24, (1, 1, 1))]},
         "eyes": {"scl": [(0, (1, 1, 1)), (6, (1.1, 1, 0.45)), (10, (1, 1, 1.15)), (16, (1, 1, 1)), (24, (1, 1, 1))]}}
    t.update(drops_idle(L, 0.03))
    C.act(rig, "Attack", L, t)

    # Cast 36 (release @ ~22): swell + flame flare, compress, erupt
    L = 36
    t = {"body": {"scl": [(0, (1, 1, 1)), (12, (1.12, 1.12, 1.1)), (19, (1.22, 1.22, 0.78)), (22, (0.86, 0.86, 1.3), "o"),
                          (26, (1.08, 1.08, 0.92)), (30, (0.98, 0.98, 1.02)), (36, (1, 1, 1))],
                  "rot": [(0, (0, 0, 0)), (12, (-6, 0, 0)), (19, (-4, 0, 0)), (22, (6, 0, 0)), (36, (0, 0, 0))]},
         "flame": {"scl": [(0, (1, 1, 1)), (12, (1.4, 1.4, 1.6)), (19, (1.2, 1.2, 1.0)), (22, (1.7, 1.7, 2.4), "o"), (28, (1.3, 1.3, 1.5)), (36, (1, 1, 1))],
                   "rot": lambda f: (5 * sw(f, 6), 5 * sw(f, 9), 0)},
         "eyes": {"scl": [(0, (1, 1, 1)), (12, (1, 1, 0.5)), (19, (1, 1, 0.4)), (22, (1.15, 1, 1.25)), (30, (1, 1, 1)), (36, (1, 1, 1))]}}
    for i, d in enumerate(D):
        out = Vector((-1 if i % 2 == 0 else 1, -0.6, 0.4)).normalized() * 0.3
        t[d] = {"loc": [(0, (0, 0, 0)), (12, (0, 0, 0.22)), (19, (0, 0, 0.14)), (22, tuple(out), "o"), (30, tuple(out * 1.1)), (36, (0, 0, 0))],
                "scl": [(0, 1), (12, 1.4), (19, 1.2), (22, 1.6), (30, 0.6), (36, 1)]}
    C.act(rig, "Cast", L, t)

    # Hit 12: squash back, jiggle
    L = 12
    t = {"body": {"rot": [(0, (0, 0, 0)), (3, (-18, 0, 6), "o"), (7, (6, 0, -3)), (12, (0, 0, 0))],
                  "loc": [(0, (0, 0, 0)), (3, (0, 0.1, 0), "o"), (12, (0, 0.0, 0))],
                  "scl": [(0, (1, 1, 1)), (3, (1.22, 1.22, 0.74), "o"), (6, (0.9, 0.9, 1.12)), (9, (1.05, 1.05, 0.95)), (12, (1, 1, 1))]},
         "flame": {"rot": [(0, (0, 0, 0)), (3, (30, 0, -10), "o"), (7, (-14, 0, 6)), (12, (0, 0, 0))]},
         "eyes": {"scl": [(0, (1, 1, 1)), (2, (1.2, 1, 0.12)), (8, (1.1, 1, 0.15)), (12, (1, 1, 1))]}}
    t.update(drops_idle(L, 0.02))
    C.act(rig, "Hit", L, t)

    # Die 30: recoil, wobble, melt flat into a cooling puddle
    L = 30
    t = {"body": {"rot": [(0, (0, 0, 0)), (4, (-16, 0, 0), "o"), (10, (8, 0, 6)), (16, (-4, 0, -4)), (30, (0, 0, 0))],
                  "loc": [(0, (0, 0, 0)), (4, (0, 0.08, 0)), (30, (0, 0.06, 0))],
                  "scl": [(0, (1, 1, 1)), (4, (1.2, 1.2, 0.76), "o"), (9, (0.88, 0.88, 1.14)), (16, (1.3, 1.3, 0.55)),
                          (24, (1.55, 1.55, 0.26)), (30, (1.62, 1.62, 0.2))]},
         "flame": {"scl": [(0, (1, 1, 1)), (6, (1.2, 1.2, 1.3)), (16, (0.4, 0.4, 0.3)), (20, (0.01, 0.01, 0.01)), (30, (0.01, 0.01, 0.01))],
                   "rot": [(0, (0, 0, 0)), (4, (30, 0, 0)), (14, (-20, 0, 0)), (30, (0, 0, 0))]},
         "eyes": {"scl": [(0, (1, 1, 1)), (3, (1.2, 1, 0.1)), (10, (1.1, 1, 0.5)), (14, (1.2, 1, 0.08)), (30, (1.2, 1, 0.08))]}}
    for i, d in enumerate(D):
        h = [0.5, 0.42, 0.72, 0.7][i]
        t[d] = {"loc": [(0, (0, 0, 0)), (6 + i, (0, 0, 0.06)), (16 + 2 * i, (0, 0, -h + 0.03), "i"), (30, (0, 0, -h + 0.03))],
                "scl": [(0, 1), (16 + 2 * i, 0.9), (22 + i, (1.6, 1.6, 0.3)), (30, (1.6, 1.6, 0.3))]}
    C.act(rig, "Die", L, t)

    # Victory 40: two happy hops, the second with a full spin
    L = 40
    t = {"body": {"loc": [(0, (0, 0, 0)), (4, (0, 0, 0)), (10, (0, 0, 0.2), "o"), (16, (0, 0, 0), "i"), (22, (0, 0, 0)), (29, (0, 0, 0.28), "o"), (36, (0, 0, 0), "i"), (40, (0, 0, 0))],
                  "scl": [(0, (1, 1, 1)), (4, (1.16, 1.16, 0.8)), (8, (0.88, 0.88, 1.18), "o"), (12, (1, 1, 1)), (16, (1.18, 1.18, 0.8), "o"),
                          (20, (1.14, 1.14, 0.84)), (25, (0.86, 0.86, 1.2), "o"), (30, (1, 1, 1)), (36, (1.18, 1.18, 0.8), "o"), (40, (1, 1, 1))],
                  "rot": [(0, (0, 0, 0)), (22, (0, 0, 0)), (34, (0, 0, 360), "io"), (40, (0, 0, 360))]},
         "flame": {"scl": lambda f: (1.3 + 0.1 * sw(f, 8), 1.3 + 0.1 * sw(f, 8), 1.5 + 0.25 * sw(f, 6)),
                   "rot": lambda f: (8 * sw(f, 10), 8 * sw(f, 14), 0)},
         "eyes": {"scl": [(0, (1, 1, 1)), (8, (1.1, 1, 0.35)), (30, (1.1, 1, 0.35)), (40, (1, 1, 1))]}}
    t.update(drops_idle(L, 0.08, speed=2))
    C.act(rig, "Victory", L, t)


if __name__ == "__main__":
    build()
