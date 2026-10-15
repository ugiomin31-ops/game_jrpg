"""고목 수호자 forest_guardian (B3 boss) — ancient mossy tree guardian, ~4.3 m.

Reference: enemies/forest_guardian/forest_guardian.png, incoming/enemies/boss__master__v1.png + boss__parts__v1.png.
Hunched bark trunk body, carved bark face with amber glowing eyes and moss beard, bark spike crown,
huge canopy (green + autumn gold, pink blossoms, fireflies) on branches, log-end shoulders, carved
stone pauldrons/bracers/knee guards, green rune heart-stone (emissive), massive clawed hands,
splayed root feet, mushrooms and hanging vines (secondary-motion chains).
"""
import sys
sys.path.append(r"C:\Users\User\Desktop\game\Blender\bosses")
from _common import *  # noqa: F401,F403

ID = "forest_guardian"
random.seed(3)

BARK = "#9b6a3c"
BARK_L = "#c39159"
BARK_D = "#5c3a20"
MOSS = "#79b53a"
MOSS_L = "#b4dc48"
MOSS_D = "#3f7a2b"
STONE = "#cbc4ae"
STONE_D = "#8e887a"
CLAW = "#f1d9a8"
CLAW_D = "#c79f69"
RUNE = "#59e83a"
RUNE_L = "#d2ff8a"
EYE = "#ffbc3a"
CAP = "#d8452f"
LEAF_G = ["#2f6b33", "#3f8a37", "#5fae3d", "#8fd14f"]
LEAF_A = ["#c2541e", "#e8892a", "#f2b33a", "#f7d65a"]

A.reset_scene()
bark = bark_painter(BARK, BARK_D, MOSS, MOSS_L, seed=1.0)
bark_lite = bark_painter(BARK, BARK_D, MOSS, MOSS_L, moss_amount=0.15, seed=2.0)
bark_nomoss = bark_painter(BARK_L, BARK, None, seed=4.0, groove=9)


def stone_paint(seed=0.0):
    def fn(c, n, p):
        g = nz(c * 4.5, seed)
        col = mix(STONE, STONE_D, smooth((g - 0.15) * 3.0))
        if n.z + nz(c * 2.0, seed + 3) * 0.5 > 0.75:
            col = rgba(MOSS)
        return col
    return fn


def grooved(o, n=9, amp=0.05, seed=0.0, center=(0, 0)):
    cx, cy = center

    def f(c):
        a = math.atan2(c.y - cy, c.x - cx)
        k = 1.0 + amp * math.sin(n * a + c.z * 2.3) + 0.04 * nz(c * 2.2, seed)
        return Vector((cx + (c.x - cx) * k, cy + (c.y - cy) * k, c.z))
    return A.deform(o, f)


# ---------------------------------------------------------------- rig
L = []


def bone(name, h, t, parent=None, mirror=True):
    L.append((name, h, t, parent))
    if mirror and name.endswith(".L"):
        mh = (-h[0], h[1], h[2])
        mt = (-t[0], t[1], t[2])
        L.append((name[:-2] + ".R", mh, mt, parent[:-2] + ".R" if parent and parent.endswith(".L") else parent))


SH = Vector((1.02, 0.02, 2.5))
EL = Vector((1.55, -0.18, 1.72))
WR = Vector((1.76, -0.5, 1.02))
HN = Vector((1.8, -0.72, 0.62))
HIP = Vector((0.52, 0.02, 1.32))
KN = Vector((0.74, -0.08, 0.72))
AN = Vector((0.8, 0.0, 0.26))

bone("root", (0, 0, 0), (0, 0, 0.4))
bone("hips", (0, 0, 1.2), (0, -0.02, 1.62), "root")
bone("spine", (0, -0.02, 1.62), (0, -0.12, 2.25), "hips")
bone("chest", (0, -0.12, 2.25), (0, -0.2, 2.7), "spine")
bone("head", (0, -0.28, 2.72), (0, -0.33, 3.3), "chest")
bone("crown", (0, 0.22, 2.95), (0, 0.28, 3.45), "chest")
bone("canopy.L", (0.3, 0.3, 3.35), (1.45, 0.35, 3.7), "crown")
bone("canopy.B", (0.0, 0.35, 3.45), (0.0, 0.45, 4.2), "crown")
bone("upperarm.L", tuple(SH), tuple(EL), "chest")
bone("forearm.L", tuple(EL), tuple(WR), "upperarm.L")
bone("hand.L", tuple(WR), tuple(HN), "forearm.L")
bone("claws.L", (1.8, -0.78, 0.8), (1.86, -1.1, 0.5), "hand.L")
bone("thigh.L", tuple(HIP), tuple(KN), "hips")
bone("shin.L", tuple(KN), tuple(AN), "thigh.L")
bone("foot.L", tuple(AN), (0.8, -0.45, 0.08), "shin.L")
# secondary chains: canopy vines and arm vines
VINES_C = {
    "vineC1.L": ((1.55, 0.05, 3.42), (1.62, 0.0, 2.95), (1.6, -0.02, 2.45), "canopy.L"),
    "vineC2.L": ((0.95, -0.35, 3.45), (0.98, -0.4, 3.05), (1.0, -0.42, 2.7), "canopy.L"),
    "vineB.L": ((0.6, 0.85, 3.4), (0.62, 0.9, 2.95), (0.64, 0.9, 2.5), "canopy.B"),
}
for n, (h, m, t, par) in VINES_C.items():
    bone(n.replace(".L", "a.L"), h, m, par)
    bone(n.replace(".L", "b.L"), m, t, n.replace(".L", "a.L"))
VINE_ARM = ((1.42, -0.32, 1.55), (1.45, -0.35, 1.1), (1.47, -0.36, 0.7))
bone("vineArma.L", VINE_ARM[0], VINE_ARM[1], "forearm.L")
bone("vineArmb.L", VINE_ARM[1], VINE_ARM[2], "vineArma.L")
rig = A.armature(L)
BONES = {b[0]: (Vector(b[1]), Vector(b[2])) for b in L}

parts = {}
smooth_parts = []


def put(bn, *objs):
    parts.setdefault(bn, []).extend(objs)


def put_mirror(bn, *objs):
    """Put objs on bone bn (.L) and their mirrored copies on .R."""
    put(bn, *objs)
    put(bn[:-2] + ".R", *mirror(objs))


# ---------------------------------------------------------------- trunk / torso
def bend_fwd(c, z0=1.5, z1=2.9, amt=0.28):
    return Vector((c.x, c.y - amt * smooth((c.z - z0) / (z1 - z0)), c.z))


trunk = A.lathe("trunk", [(0.42, 1.12), (0.6, 1.3), (0.7, 1.6), (0.78, 1.95), (0.88, 2.25), (0.93, 2.48),
                          (0.84, 2.7), (0.62, 2.86), (0.32, 2.95), (0.0, 2.98)], seg=28)
A.deform(trunk, lambda c: Vector((c.x, c.y * 0.78, c.z)))
grooved(trunk, n=9, amp=0.06, seed=1)
A.deform(trunk, bend_fwd)
paint_faces(trunk, bark)
put("spine", trunk)

pelvis = A.lathe("pelvis", [(0.0, 0.95), (0.5, 1.0), (0.66, 1.2), (0.66, 1.4), (0.5, 1.58)], seg=22)
A.deform(pelvis, lambda c: Vector((c.x * 1.05, c.y * 0.8, c.z)))
grooved(pelvis, n=7, amp=0.05, seed=3)
paint_faces(pelvis, bark_lite)
put("hips", pelvis)

# moss fringe "skirt" (pointed moss leaves hanging at the waist, like the reference)
for i in range(13):
    a = math.radians(-160 + i * 26.0)
    x, y = math.cos(a) * 0.62, math.sin(a) * 0.52
    if y > 0.25:
        continue
    lf = leaf(f"fringe{i}", length=0.42 + 0.12 * random.random(), width=0.2, color=MOSS if i % 2 else MOSS_D,
              loc=(x, y - 0.03, 1.62), rot=(180 - 15, 0, math.degrees(a) + 90))
    put("hips", lf)
mossbelt = A.torus("mossbelt", R=0.68, r=0.1, loc=(0, -0.02, 1.6), scale=(1, 0.8, 1), color=MOSS, seg=24, minor=6)
A.deform(mossbelt, lambda c: c * (1 + 0.12 * nz(c * 4, 7)))
put("hips", mossbelt)

# chest heart-stone (carved stone diamond + glowing green rune)
CZ, CY = 2.12, -0.82
stone = plate("heartstone", ngon(4, 0.42, math.pi / 2, rz=0.5), 0.16, (0, CY + 0.03, CZ), (-8, 0, 0), STONE, bevel=0.03)
paint_faces(stone, stone_paint(1))
r1 = plate("rune1", ngon(4, 0.28, math.pi / 2, rz=0.33), 0.06, (0, CY - 0.06, CZ), (-8, 0, 0), RUNE, "M_Emit")
r2 = plate("rune2", ngon(4, 0.19, math.pi / 2, rz=0.22), 0.06, (0, CY - 0.085, CZ), (-8, 0, 0), "#1f6b25")
r3 = plate("rune3", ngon(4, 0.1, math.pi / 2, rz=0.12), 0.06, (0, CY - 0.11, CZ), (-8, 0, 0), RUNE_L, "M_Emit")
put("chest", stone, r1, r2, r3)
for i in range(4):
    a = math.pi / 2 * i
    nub = A.box(f"stonenub{i}", (0.16, 0.14, 0.12), loc=(math.cos(a) * 0.5, CY + 0.06, CZ + math.sin(a) * 0.58),
                rot=(0, math.degrees(a), 0), color=STONE_D, bevel=0.02)
    put("chest", nub)
# vines wrapping the chest
for s in (1, -1):
    pts = [(s * 0.55, -0.62, 2.75), (s * 0.45, -0.8, 2.45), (s * 0.15, -0.88, 2.0), (s * -0.25, -0.83, 1.75), (s * -0.6, -0.6, 1.62)]
    v, _ = sweep(f"chestvine{s}", catmull(pts, 4), 0.045, seg=6, color=MOSS_D)
    put("chest", v)

# moss mantle on the shoulders / neck
for i, (x, y, z, r) in enumerate([(0.0, -0.45, 2.78, 0.32), (0.45, -0.3, 2.72, 0.3), (-0.45, -0.3, 2.72, 0.3),
                                   (0.75, 0.0, 2.72, 0.28), (-0.75, 0.0, 2.72, 0.28), (0.3, 0.3, 2.85, 0.3),
                                   (-0.3, 0.3, 2.85, 0.3)]):
    m = blob(f"mantle{i}", r, (x, y, z), (1.2, 1.0, 0.55), color=MOSS, seed=i, amp=0.25, subdiv=2)
    paint_faces(m, lambda c, n, p: MOSS_L if n.z > 0.55 + 0.3 * nz(c * 5, 2) else (MOSS if n.z > -0.2 else MOSS_D))
    put("chest", m)

# ---------------------------------------------------------------- head (carved bark face)
head = A.lathe("head", [(0.0, 2.55), (0.4, 2.6), (0.48, 2.85), (0.45, 3.1), (0.33, 3.3), (0.0, 3.36)], seg=22,
               loc=(0, -0.32, 0))
A.deform(head, lambda c: Vector((c.x, c.y * 0.85, c.z)))
grooved(head, n=8, amp=0.04, seed=5)
A.apply_transform(head)
paint_faces(head, bark_nomoss)
brow, _ = sweep("brow", catmull([(-0.42, -0.6, 3.2), (-0.18, -0.72, 3.1), (0.0, -0.74, 3.02), (0.18, -0.72, 3.1),
                                 (0.42, -0.6, 3.2)], 4), lambda t: 0.06 + 0.05 * math.sin(math.pi * t), seg=8, color=BARK_L)
nose = A.cone("nose", r=0.09, depth=0.3, loc=(0, -0.76, 2.9), rot=(100, 0, 0), color=BARK_L, seg=8)
cheekL = A.sphere("cheek.L", 0.12, loc=(0.26, -0.68, 2.84), scale=(1.2, 0.6, 0.8), color=BARK, seg=10, rings=6)
cheekR = A.mirror_x(cheekL)
sockets, eyes = [], []
for s in (1, -1):
    so = A.sphere(f"socket{s}", 0.13, loc=(s * 0.19, -0.66, 3.0), rot=(0, s * -18, 0), scale=(1.0, 0.45, 0.62),
                  color="#2a1408", seg=14, rings=8)
    ey = A.sphere(f"eye{s}", 0.09, loc=(s * 0.19, -0.7, 3.0), rot=(0, s * -18, 0), scale=(1.0, 0.45, 0.55),
                  color=EYE, mat="M_Emit", seg=12, rings=8)
    pu = A.sphere(f"pupil{s}", 0.035, loc=(s * 0.2, -0.735, 3.0), scale=(1, 0.5, 1.2), color="#fff6c8", mat="M_Emit",
                  seg=8, rings=6)
    sockets.append(so)
    eyes += [ey, pu]
# moss beard: layered pointed moss leaves hanging from the chin
beard = []
for i in range(9):
    a = (i - 4) / 4.0
    lf = leaf(f"beard{i}", length=0.42 - abs(a) * 0.12, width=0.2, color=MOSS if i % 2 else MOSS_L,
              loc=(a * 0.28, -0.7 + abs(a) * 0.1, 2.83), rot=(180 + 10, 0, a * 25))
    beard.append(lf)
bb = blob("beardblob", 0.22, (0, -0.66, 2.74), (1.3, 0.7, 0.8), color=MOSS, seed=3, amp=0.2)
beard.append(bb)
# bark spike crown on the head
spikes = []
for i, (x, y, ang_y, ang_x, ln) in enumerate([(0.0, -0.45, 0, -18, 0.5), (0.2, -0.38, -28, -10, 0.45), (-0.2, -0.38, 28, -10, 0.45),
                                              (0.36, -0.25, -50, 0, 0.42), (-0.36, -0.25, 50, 0, 0.42),
                                              (0.2, -0.12, -20, 15, 0.38), (-0.2, -0.12, 20, 15, 0.38)]):
    sp = A.cone(f"spike{i}", r=0.085, depth=ln, loc=(0, 0, 0), color=BARK_L, seg=7)
    A.deform(sp, lambda c, ln=ln: Vector((c.x, c.y + 0.25 * (c.z / ln + 0.5) ** 2 * 0.0, c.z + ln / 2)))
    sp.location = (x, y, 3.2)
    sp.rotation_euler = Euler((math.radians(ang_x), math.radians(ang_y), 0))
    A.apply_transform(sp)
    A.gradient(sp, BARK, BARK_L)
    spikes.append(sp)
crest = leaf("crest", 0.45, 0.24, loc=(0, -0.42, 3.22), rot=(-10, 0, 0), color=MOSS_L)
put("head", head, brow, nose, cheekL, cheekR, crest, *sockets, *eyes, *beard, *spikes)

# ---------------------------------------------------------------- arms
def arm_parts():
    out = {"upperarm.L": [], "forearm.L": [], "hand.L": [], "claws.L": []}
    # log-end shoulder with tree rings
    log = A.cyl("shoulderlog", r=0.46, depth=0.55, loc=(SH.x + 0.02, SH.y, SH.z + 0.05), rot=(0, 90, 0), color=BARK, seg=18)
    A.apply_transform(log)
    paint_faces(log, bark)
    out["upperarm.L"].append(log)
    # tree-ring end cap (concentric discs, slightly proud of the log end)
    for k, (rr, col) in enumerate([(0.4, "#e3bb80"), (0.3, "#b9894f"), (0.2, "#e3bb80"), (0.1, "#b9894f")]):
        ring = A.cyl(f"logring{k}", r=rr, depth=0.02, loc=(SH.x + 0.3 + 0.012 * k, SH.y, SH.z + 0.05), rot=(0, 90, 0),
                     color=col, seg=18)
        out["upperarm.L"].append(ring)
    ua, _ = sweep("upperarm", catmull([SH + V(0.05, 0, -0.1), (SH + EL) / 2 + V(0.05, 0, 0), EL], 4),
                  lambda t: 0.36 - 0.06 * t, seg=14)
    grooved(ua, n=6, amp=0.05, seed=10, center=(1.3, -0.08))
    paint_faces(ua, bark)
    elbow = blob("elbow", 0.33, tuple(EL), (1, 1, 1), color=BARK, seed=4, amp=0.12, subdiv=2)
    paint_faces(elbow, bark)
    out["upperarm.L"] += [ua]
    fa, _ = sweep("forearm", catmull([EL, (EL + WR) / 2 + V(0.04, 0, 0), WR], 4), lambda t: 0.31 + 0.1 * t, seg=14)
    grooved(fa, n=7, amp=0.05, seed=11, center=(1.65, -0.33))
    paint_faces(fa, bark)
    out["forearm.L"] += [elbow, fa]
    # stone bracer
    d = (WR - EL).normalized()
    br = A.lathe("bracer", [(0.38, -0.13), (0.45, -0.1), (0.46, 0.1), (0.4, 0.14)], seg=16)
    br.matrix_world = Matrix.Translation(EL + (WR - EL) * 0.55) @ d.to_track_quat("Z", "Y").to_matrix().to_4x4()
    A.apply_transform(br)
    paint_faces(br, stone_paint(4))
    out["forearm.L"].append(br)
    for k in range(4):
        rune = A.box(f"bracerrune{k}", (0.1, 0.03, 0.12), color=STONE_D, bevel=0.01)
        a = k * math.pi / 2 + 0.4
        q = d.to_track_quat("Z", "Y").to_matrix()
        off = q @ V(math.cos(a) * 0.46, math.sin(a) * 0.46, 0)
        rune.location = EL + (WR - EL) * 0.55 + off
        rune.rotation_euler = (q @ Matrix.Rotation(a + math.pi / 2, 3, "Z")).to_euler()
        out["forearm.L"].append(rune)
    # pauldron (curved carved stone)
    pd = A.box("pauldron", (0.7, 0.75, 0.16), color=STONE, bevel=0.04)
    A.deform(pd, lambda c: Vector((c.x, c.y, c.z - 0.9 * c.x * c.x - 0.5 * c.y * c.y)))
    pd.location = SH + V(0.12, -0.02, 0.42)
    pd.rotation_euler = (0, math.radians(-28), 0)
    A.apply_transform(pd)
    paint_faces(pd, stone_paint(6))
    out["upperarm.L"].append(pd)
    for k in range(3):
        st = A.box(f"pstrip{k}", (0.08, 0.6, 0.05), loc=SH + V(-0.12 + k * 0.2, -0.02, 0.5 - abs(k - 1) * 0.07 + 0.05),
                   rot=(0, -28 + (k - 1) * 12, 0), color=STONE_D, bevel=0.015)
        out["upperarm.L"].append(st)
    # hand
    palm = blob("palm", 0.36, tuple(WR + V(0.03, -0.12, -0.18)), (1.0, 1.1, 0.9), color=BARK, seed=6, amp=0.12)
    paint_faces(palm, bark)
    out["hand.L"].append(palm)
    # claws: thick knuckles + long curved bone talons
    base = WR + V(0.03, -0.3, -0.25)
    for k, (dx, dz, ln) in enumerate([(-0.24, -0.06, 0.62), (-0.08, 0.02, 0.72), (0.08, 0.02, 0.7), (0.24, -0.05, 0.6)]):
        p0 = base + V(dx, 0.05, dz)
        ctrl = [p0, p0 + V(dx * 0.3, -0.22, 0.06), p0 + V(dx * 0.5, -0.42, -0.12), p0 + V(dx * 0.6, -0.5, -ln * 0.65),
                p0 + V(dx * 0.6, -0.4, -ln * 1.0)]
        cl, _ = sweep(f"claw{k}", catmull(ctrl, 4), lambda t: 0.11 * (1 - t) ** 0.8 + 0.008, seg=9)
        paint_faces(cl, lambda c, n, p, cl=cl: mix(CLAW_D, CLAW, face_attr(cl, p, "tpar") * 1.6))
        kn = blob(f"knuckle{k}", 0.13, tuple(p0 + V(0, 0.06, 0.02)), (1, 1.2, 1), color=BARK, seed=k + 20, amp=0.1, subdiv=1)
        paint_faces(kn, bark)
        out["claws.L"] += [cl, kn]
    th0 = WR + V(-0.25, -0.12, -0.15)
    th, _ = sweep("thumb", catmull([th0, th0 + V(-0.18, -0.15, 0.0), th0 + V(-0.26, -0.38, -0.12), th0 + V(-0.18, -0.48, -0.3)], 4),
                  lambda t: 0.1 * (1 - t) ** 0.8 + 0.008, seg=9)
    paint_faces(th, lambda c, n, p: mix(CLAW_D, CLAW, face_attr(th, p, "tpar") * 1.6))
    out["hand.L"].append(th)
    return out


for bn, objs in arm_parts().items():
    put_mirror(bn, *objs)

# ---------------------------------------------------------------- legs and roots
def leg_parts():
    out = {"thigh.L": [], "shin.L": [], "foot.L": []}
    th, _ = sweep("thigh", catmull([HIP + V(0, 0, 0.1), (HIP + KN) / 2, KN], 4), lambda t: 0.4 - 0.04 * t, seg=14)
    grooved(th, n=6, amp=0.05, seed=12, center=(0.63, -0.03))
    paint_faces(th, bark)
    knee = blob("knee", 0.36, tuple(KN), (1, 1, 1), color=BARK, seed=8, amp=0.1)
    paint_faces(knee, bark)
    guard = A.box("kneeguard", (0.5, 0.18, 0.5), color=STONE, bevel=0.04)
    A.deform(guard, lambda c: Vector((c.x, c.y + 0.9 * c.x * c.x, c.z)))
    guard.location = KN + V(0.02, -0.33, 0.04)
    guard.rotation_euler = (math.radians(-10), 0, math.radians(8))
    A.apply_transform(guard)
    paint_faces(guard, stone_paint(9))
    eye = plate("guardglyph", ngon(3, 0.12, math.pi / 2), 0.04, tuple(KN + V(0.02, -0.43, 0.05)), (-10, 0, 8), STONE_D)
    out["thigh.L"] += [th]
    out["shin.L"] += [knee, guard, eye]
    sh, _ = sweep("shin", catmull([KN, (KN + AN) / 2, AN + V(0, 0, -0.18)], 4), lambda t: 0.34 + 0.16 * t * t, seg=14)
    grooved(sh, n=7, amp=0.07, seed=13, center=(0.77, -0.04))
    paint_faces(sh, bark)
    out["shin.L"].append(sh)
    # splayed roots
    for k, ang in enumerate([-150, -115, -85, -55, -20, 25, 80]):
        a = math.radians(ang)
        dvec = V(math.cos(a), math.sin(a), 0)
        ln = 0.75 + 0.25 * random.random()
        p0 = AN + dvec * 0.28 + V(0, 0, 0.0)
        ctrl = [p0, p0 + dvec * 0.3 + V(0, 0, 0.0), p0 + dvec * ln * 0.7 + V(0, 0, -0.1), p0 + dvec * ln + V(0, 0, -0.22)]
        rt, _ = sweep(f"root{k}", catmull(ctrl, 4), lambda t: 0.17 * (1 - t) + 0.025, seg=9)
        A.deform(rt, lambda c: Vector((c.x, c.y, max(c.z, 0.0))))
        paint_faces(rt, bark_lite)
        out["foot.L"].append(rt)
    return out


for bn, objs in leg_parts().items():
    put_mirror(bn, *objs)

# ---------------------------------------------------------------- mushrooms
def mushroom(name, loc, s=1.0, tilt=(0, 0, 0)):
    stem = A.cyl(name + "stem", r=0.05 * s, r2=0.04 * s, depth=0.16 * s, loc=(0, 0, 0.08 * s), color="#f2e4c6", seg=8)
    cap = A.lathe(name + "cap", [(0.0, 0.13 * s), (0.08 * s, 0.125 * s), (0.15 * s, 0.09 * s), (0.17 * s, 0.05 * s),
                                 (0.05 * s, 0.07 * s)], seg=14, color=CAP)
    gill = A.cyl(name + "gill", r=0.16 * s, depth=0.01, loc=(0, 0, 0.055 * s), color="#f6e7cd", seg=14)
    spots = []
    for k in range(5):
        a = k * 1.3 + 0.4
        rr = 0.09 * s if k else 0.0
        sp = A.sphere(name + f"spot{k}", 0.028 * s, loc=(math.cos(a) * rr, math.sin(a) * rr, 0.128 * s - (0.02 * s if k else 0)),
                      scale=(1, 1, 0.4), color="#fff6e6", seg=8, rings=4)
        spots.append(sp)
    m = A.join([stem, cap, gill] + spots, name)
    m.location = loc
    m.rotation_euler = Euler([math.radians(x) for x in tilt])
    A.apply_transform(m)
    return m


put("upperarm.L", mushroom("mushL1", SH + V(0.05, -0.15, 0.55), 1.4, (0, -25, 0)),
    mushroom("mushL2", SH + V(0.32, 0.1, 0.42), 1.0, (10, -40, 0)))
put("chest", mushroom("mushC1", (-0.62, -0.42, 2.5), 1.2, (-10, 35, 0)), mushroom("mushC2", (-0.75, -0.25, 2.35), 0.8, (0, 50, 0)))
put("thigh.R", mushroom("mushT", (-0.72, -0.35, 1.2), 1.3, (-20, 30, 0)))

# ---------------------------------------------------------------- canopy
canopy_bones = {"canopy.L": Vector((1.0, 0.35, 3.6)), "canopy.R": Vector((-1.0, 0.35, 3.6)), "canopy.B": Vector((0, 0.45, 3.9))}


def canopy_bone_for(p):
    return min(canopy_bones, key=lambda k: (canopy_bones[k] - p).length)


# branches from the back of the trunk into the canopy
BR = [
    [(0.25, 0.25, 2.75), (0.45, 0.35, 3.15), (0.95, 0.35, 3.45), (1.5, 0.3, 3.6)],
    [(-0.25, 0.25, 2.75), (-0.45, 0.35, 3.15), (-0.95, 0.35, 3.45), (-1.5, 0.3, 3.6)],
    [(0.0, 0.32, 2.8), (0.05, 0.42, 3.3), (0.0, 0.5, 3.75), (0.1, 0.5, 4.05)],
    [(0.35, 0.3, 3.0), (0.6, 0.6, 3.5), (0.75, 0.75, 3.9)],
    [(-0.35, 0.3, 3.0), (-0.6, 0.6, 3.5), (-0.75, 0.75, 3.9)],
]
for i, ctrl in enumerate(BR):
    pts = catmull(ctrl, 4)
    b, _ = sweep(f"branch{i}", pts, lambda t: 0.2 * (1 - t) + 0.06, seg=10)
    paint_faces(b, bark_lite)
    tip = Vector(ctrl[-1])
    chain_weights(b, [("chest", ctrl[0], ctrl[1]), (canopy_bone_for(tip), ctrl[1], tip)])
    smooth_parts.append(b)
    if i < 2:  # twig forks
        for k, off in enumerate([(0.0, -0.4, 0.3), (0.2, 0.3, 0.35)]):
            s0 = Vector(ctrl[2])
            tw, _ = sweep(f"twig{i}{k}", [s0, s0 + V(*off) * 0.6, s0 + V(*off)], [0.07, 0.05, 0.03], seg=6)
            paint_faces(tw, bark_lite)
            put(canopy_bone_for(s0), tw)

clusters = [
    # (x, y, z, r, autumn)
    (1.55, 0.25, 3.62, 0.62, True), (1.0, -0.15, 3.85, 0.62, True), (0.55, 0.45, 4.15, 0.62, True),
    (-0.05, 0.05, 4.2, 0.6, False), (-0.6, 0.45, 4.1, 0.62, False), (-1.05, -0.12, 3.82, 0.6, False),
    (-1.6, 0.28, 3.58, 0.58, False), (0.0, 0.85, 3.85, 0.65, False), (1.15, 0.75, 3.6, 0.58, False),
    (-1.15, 0.78, 3.6, 0.58, True), (0.45, -0.35, 3.85, 0.45, False), (-0.45, -0.32, 3.92, 0.48, True),
    (1.95, 0.3, 3.4, 0.42, False), (-1.95, 0.35, 3.38, 0.4, False),
]
for i, (x, y, z, r, aut) in enumerate(clusters):
    pal = LEAF_A if aut else LEAF_G
    cl = blob(f"leaves{i}", r, (x, y, z), (1.15, 1.0, 0.78), color=pal[1], seed=i * 1.7, amp=0.28, freq=2.6, subdiv=1)
    cz = z

    def lp(c, n, p, cz=cz, pal=pal, i=i):
        h = n.z * 0.7 + (c.z - cz) * 1.2 + nz(c * 3.5, i) * 0.5
        idx = 0 if h < -0.45 else (1 if h < 0.05 else (2 if h < 0.5 else 3))
        return pal[idx]
    paint_faces(cl, lp)
    bn = canopy_bone_for(Vector((x, y, z)))
    put(bn, cl)
    # serrated leaf cards breaking the silhouette
    for k in range(5):
        a = random.uniform(0, TAU)
        el = random.uniform(-0.6, 0.5)
        d = V(math.cos(a) * math.cos(el), math.sin(a) * math.cos(el), math.sin(el))
        pos = V(x, y, z) + V(d.x * r * 1.1, d.y * r, d.z * r * 0.75)
        rot_q = d.to_track_quat("Z", "Y").to_euler()
        lf = leaf(f"lcard{i}_{k}", 0.34, 0.24, color=pal[2 + (k % 2)], thick=0.025)
        lf.location = pos - d * 0.12
        lf.rotation_euler = rot_q
        put(bn, lf)

# blossoms and fireflies
FLOWER = [(math.cos(a) * (0.09 if k % 2 == 0 else 0.04), math.sin(a) * (0.09 if k % 2 == 0 else 0.04))
          for k, a in enumerate([TAU * j / 10 for j in range(10)])]
for i, (x, y, z) in enumerate([(-0.55, -0.1, 4.45), (-1.25, -0.6, 3.95), (-1.85, -0.15, 3.75), (-0.2, -0.55, 4.25),
                               (-1.5, 0.75, 3.95), (0.0, 0.85, 4.38), (0.9, -0.55, 4.05)]):
    fl = plate(f"flower{i}", FLOWER, 0.03, (x, y, z), (-60, 0, i * 30), "#ffb3cf")
    fc = A.sphere(f"fcen{i}", 0.035, loc=(x, y - 0.03, z + 0.01), color="#ffe066", seg=8, rings=4)
    put(canopy_bone_for(Vector((x, y, z))), fl, fc)
for i, (x, y, z) in enumerate([(1.3, -0.65, 3.6), (-0.9, -0.55, 3.55), (0.3, -0.7, 3.65), (-1.8, -0.2, 3.25),
                               (1.9, -0.1, 3.25), (0.6, 0.2, 4.6)]):
    ff = A.sphere(f"firefly{i}", 0.045, loc=(x, y, z), color="#fff27a", mat="M_Emit", seg=8, rings=5)
    put(canopy_bone_for(Vector((x, y, z))), ff)


# ---------------------------------------------------------------- hanging vines (secondary chains)
def vine(name, top, mid, bot, chain):
    pts = [Vector(top), Vector(mid), Vector(bot)]
    ctrl = [pts[0], (pts[0] + pts[1]) / 2 + V(0.05, 0.0, 0), pts[1], (pts[1] + pts[2]) / 2 + V(-0.05, 0.02, 0), pts[2]]
    v, _ = sweep(name, catmull(ctrl, 4), lambda t: 0.035 * (1 - 0.5 * t), seg=6, color=MOSS_D)
    objs = [v]
    path = catmull(ctrl, 4)
    for k in range(2, len(path) - 1, 2):
        p = path[k]
        side = 1 if k % 4 == 0 else -1
        lf = leaf(f"{name}lf{k}", 0.16, 0.09, color=MOSS if k % 3 else MOSS_L, loc=tuple(p),
                  rot=(180 - 30 * side, 0, 90 * side + random.uniform(-30, 30)))
        objs.append(lf)
    tipl = leaf(f"{name}tip", 0.18, 0.11, color=MOSS_L, loc=tuple(pts[2]), rot=(180, 0, 0))
    objs.append(tipl)
    w = A.join(objs, name)
    chain_weights(w, chain)
    return w


for n, (h, m, t, par) in VINES_C.items():
    for side in (1, -1):
        bn = n.replace(".L", "a.L" if side == 1 else "a.R")
        bn2 = n.replace(".L", "b.L" if side == 1 else "b.R")
        hh, mm, tt = [V(p[0] * side, p[1], p[2]) for p in (h, m, t)]
        smooth_parts.append(vine(f"v{bn}", hh, mm, tt, [(bn, hh, mm), (bn2, mm, tt)]))
for side in (1, -1):
    hh, mm, tt = [V(p[0] * side, p[1], p[2]) for p in VINE_ARM]
    sfx = ".L" if side == 1 else ".R"
    smooth_parts.append(vine(f"varm{sfx}", hh, mm, tt, [("vineArma" + sfx, hh, mm), ("vineArmb" + sfx, mm, tt)]))

# ---------------------------------------------------------------- skin
body = skin2(parts, smooth_parts, rig)
print("TRIS", tris(body))


# ---------------------------------------------------------------- animation
VINE_BONES = [b[0] for b in L if b[0].startswith("vine")]


def secondary(P, t, cycles=1.0, amp=1.0, lag=0.0):
    """Canopy sway, vine swing, claw flex — layered on every action."""
    for k, side in (("L", 1), ("R", -1)):
        P.r(f"canopy.{k}", (2.0 * amp * wave(t, cycles, 0.1 + lag), 2.5 * amp * side * wave(t, cycles, 0.25 + lag), 0))
    P.r("canopy.B", (2.5 * amp * wave(t, cycles, 0.2 + lag), 1.5 * amp * wave(t, cycles, 0.45 + lag), 0))
    for i, b in enumerate(VINE_BONES):
        ph = 0.13 * i + (0.15 if b[-3] == "b" else 0.0)
        P.r(b, (7 * amp * wave(t, cycles, ph + lag), 6 * amp * wave(t, cycles, ph + 0.3 + lag), 0))


def legs_stand(P, crouch=0.0):
    """Counter-rotate legs so the feet stay planted while the hips drop by `crouch` metres."""
    a = math.degrees(math.asin(clamp(crouch / 1.0, -0.9, 0.9)))
    for s in ("L", "R"):
        P.r(f"thigh.{s}", (-a, 0, 0))
        P.r(f"shin.{s}", (a * 2, 0, 0))
        P.r(f"foot.{s}", (-a, 0, 0))


def idle(P, f, t):
    br = wave(t, 1)
    P.l("hips", (0, 0, -0.03 + 0.03 * br))
    legs_stand(P, 0.03 - 0.03 * br)
    P.r("spine", (1.5 * wave(t, 1, 0.1), 0, 1.0 * wave(t, 1, 0.3)))
    P.r("chest", (1.5 * wave(t, 1, 0.2), 0, 0))
    P.s("chest", (1 + 0.012 * wave(t, 1, 0.2), 1 + 0.012 * wave(t, 1, 0.2), 1))
    P.r("head", (-2 * wave(t, 1, 0.35), 3 * wave(t, 1, 0.6), 0))
    for s, sg in (("L", 1), ("R", -1)):
        P.r(f"upperarm.{s}", (-4 + 3 * wave(t, 1, 0.3), sg * 2 * wave(t, 1, 0.45), 0))
        P.r(f"forearm.{s}", (-10 + 4 * wave(t, 1, 0.4), 0, 0))
        P.r(f"claws.{s}", (8 * wave(t, 1, 0.5), 0, 0))
    secondary(P, t, 1, 1.0)
    P.r("crown", (1.5 * wave(t, 1, 0.3), 0, 0))


def run(P, f, t):
    # heavy stomping advance in place (24 f, two steps)
    for s, ph, sg in (("L", 0.0, 1), ("R", 0.5, -1)):
        lift = max(0.0, wave(t, 1, ph))
        P.r(f"thigh.{s}", (-28 * lift + 10 * wave(t, 1, ph + 0.25), 0, 0))
        P.r(f"shin.{s}", (38 * lift, 0, 0))
        P.r(f"foot.{s}", (-12 * lift, 0, 0))
        P.r(f"upperarm.{s}", (14 * wave(t, 1, ph + 0.5) - 8, sg * 4, 0))
        P.r(f"forearm.{s}", (-18 + 8 * wave(t, 1, ph + 0.6), 0, 0))
    bounce = abs(wave(t, 1, 0.0))
    P.l("hips", (0, 0, 0.06 * bounce - 0.06))
    P.r("hips", (0, 6 * wave(t, 1, 0.0), 4 * wave(t, 1, 0.0)))
    P.r("spine", (12, -4 * wave(t, 1, 0.0), -3 * wave(t, 1, 0.0)))
    P.r("chest", (4 + 2 * wave(t, 2, 0.1), 0, 0))
    P.r("head", (-10, 0, 3 * wave(t, 1, 0.1)))
    secondary(P, t, 2, 1.6, lag=0.1)


def attack(P, f, t):
    # right-claw overhead smash; impact at 40 %
    T0, T1, T2 = 0.0, 0.3, 0.4
    wind = K(t, (0, 0), (0.28, 1), (0.36, 1.05), (0.42, 0), (0.75, 0), (1, 0))
    hit = K(t, (0, 0), (0.33, 0), (0.4, 1), (0.62, 1), (1, 0))
    P.r("spine", (-14 * wind + 22 * hit, 0, 10 * wind - 6 * hit))
    P.r("chest", (-8 * wind + 10 * hit, 0, 8 * wind))
    P.r("head", (10 * wind - 12 * hit, 0, -6 * wind))
    P.r("upperarm.R", (-150 * wind - 75 * hit, -20 * wind, 0))
    P.r("forearm.R", (-40 * wind + 10 * hit, 0, 0))
    P.r("claws.R", (-25 * wind + 40 * hit, 0, 0))
    P.r("upperarm.L", (12 * wind - 20 * hit, -8 * wind, 0))
    P.r("forearm.L", (-15 * wind, 0, 0))
    crouch = 0.12 * hit - 0.04 * wind
    P.l("hips", (0, -0.1 * hit, -crouch))
    legs_stand(P, crouch)
    P.r("hips", (0, 0, 8 * wind - 6 * hit))
    shake = K(t, (0.38, 0), (0.42, 1), (0.7, 0))
    secondary(P, t, 1, 1.0 + 3 * shake)
    P.r("canopy.B", (-6 * wind + 8 * hit, 0, 0))


def cast(P, f, t):
    # arms rise, canopy flares, rune pulses; release (palms slam forward) at 60 %
    up = K(t, (0, 0), (0.45, 1), (0.56, 1.1), (0.62, 0), (1, 0))
    rel = K(t, (0, 0), (0.55, 0), (0.6, 1), (0.85, 1), (1, 0))
    P.r("spine", (-12 * up + 16 * rel, 0, 0))
    P.r("chest", (-8 * up + 6 * rel, 0, 0))
    P.r("head", (-14 * up + 6 * rel, 0, 0))
    for s, sg in (("L", 1), ("R", -1)):
        P.r(f"upperarm.{s}", (-60 * up - 80 * rel, -sg * 55 * up + sg * 10 * rel, 0))
        P.r(f"forearm.{s}", (-30 * up + 10 * rel, 0, 0))
        P.r(f"claws.{s}", (-35 * up + 30 * rel, 0, 0))
    P.s("chest", 1 + 0.05 * up)
    P.l("hips", (0, 0, 0.05 * up - 0.08 * rel))
    legs_stand(P, -0.05 * up + 0.08 * rel)
    P.s("crown", 1 + 0.08 * up)
    secondary(P, t, 2, 1.0 + 2.0 * up)


def hit(P, f, t):
    k = K(t, (0, 0), (0.18, 1), (1, 0))
    P.r("spine", (-14 * k, 0, 5 * k))
    P.r("chest", (-8 * k, 0, 0))
    P.r("head", (-15 * k, 6 * k, 0))
    P.l("hips", (0, 0.12 * k, -0.04 * k))
    legs_stand(P, 0.04 * k)
    for s, sg in (("L", 1), ("R", -1)):
        P.r(f"upperarm.{s}", (20 * k, -sg * 12 * k, 0))
        P.r(f"claws.{s}", (-20 * k, 0, 0))
    secondary(P, t, 2, 1 + 3 * k)


def die(P, f, t):
    # stagger back, knees buckle, then topple forward face-down; canopy droops
    stag = K(t, (0, 0), (0.15, 1), (0.3, 0.6), (1, 0.6))
    fall = K(t, (0.25, 0), (0.75, 1), (1, 1))
    bounce = K(t, (0.72, 0), (0.8, 1), (0.9, 0), (1, 0))
    P.r("root", (78 * fall - 4 * bounce, 0, 6 * fall))
    P.l("root", (0, -0.25 * fall, -0.1 * fall))
    P.r("spine", (-12 * stag + 10 * fall, 0, 6 * stag))
    P.r("head", (-20 * stag + 25 * fall, 10 * fall, 0))
    for s, sg in (("L", 1), ("R", -1)):
        P.r(f"thigh.{s}", (-35 * fall, 0, 0))
        P.r(f"shin.{s}", (55 * fall, 0, 0))
        P.r(f"foot.{s}", (-20 * fall, 0, 0))
        P.r(f"upperarm.{s}", (30 * stag - 120 * fall, -sg * 25 * stag - sg * 20 * fall, 0))
        P.r(f"forearm.{s}", (-10 * fall, 0, 0))
        P.r(f"claws.{s}", (25 * fall, 0, 0))
    P.r("crown", (12 * fall, 0, 0))
    P.r("canopy.L", (10 * fall, 10 * fall, 0))
    P.r("canopy.R", (10 * fall, -10 * fall, 0))
    P.r("canopy.B", (14 * fall, 0, 0))
    for b in VINE_BONES:
        P.r(b, (-60 * fall if "b" in b[-3] else -30 * fall, 0, 0))
    secondary(P, t, 2, 1.5 * (1 - fall))


def roar(P, f, t):
    # 60 f: crouch (anticipation), rear up with arms spread and head thrown back, shake, settle
    ant = K(t, (0, 0), (0.15, 1), (0.25, 0))
    up = K(t, (0.15, 0), (0.3, 1), (0.78, 1), (1, 0))
    shake = math.sin(t * TAU * 9) * K(t, (0.28, 0), (0.35, 1), (0.75, 1), (0.85, 0))
    P.r("spine", (14 * ant - 18 * up, 0, 2 * shake))
    P.r("chest", (8 * ant - 10 * up + 1.5 * shake, 0, 0))
    P.r("head", (10 * ant - 28 * up, 0, 3 * shake))
    for s, sg in (("L", 1), ("R", -1)):
        P.r(f"upperarm.{s}", (12 * ant - 40 * up, -sg * 70 * up + sg * 6 * ant, 0))
        P.r(f"forearm.{s}", (-45 * up, sg * 10 * up, 0))
        P.r(f"claws.{s}", (-40 * up + 4 * shake, 0, 0))
    crouch = 0.14 * ant - 0.06 * up
    P.l("hips", (0, 0.05 * up, -crouch))
    legs_stand(P, crouch)
    P.s("chest", 1 + 0.06 * up)
    P.r("crown", (-6 * up + 2 * shake, 0, 0))
    secondary(P, t, 3, 1 + 3.5 * up)


def victory(P, f, t):
    up = K(t, (0, 0), (0.3, 1), (0.8, 1), (1, 0))
    P.r("spine", (-8 * up, 0, 0))
    P.r("head", (-12 * up, 6 * up * wave(t, 2), 0))
    P.r("upperarm.R", (-130 * up, -25 * up, 0))
    P.r("forearm.R", (-20 * up, 0, 0))
    P.r("claws.R", (-30 * up, 0, 0))
    P.r("upperarm.L", (-10 * up, 0, 0))
    P.l("hips", (0, 0, 0.04 * up))
    legs_stand(P, -0.04 * up)
    secondary(P, t, 2, 1 + up)


bake(rig, "Idle", 60, idle, step=2)
bake(rig, "Run", 24, run)
bake(rig, "Attack", 30, attack)
bake(rig, "Cast", 36, cast)
bake(rig, "Hit", 12, hit)
bake(rig, "Die", 36, die)
bake(rig, "Victory", 44, victory, step=2)
bake(rig, "Roar", 60, roar, step=2)

finish(ID, rig, body, STD_PREVIEWS + [
    ("roar", (72, 0, 32), "Roar", 34),
    ("attack_wind", (72, 0, 32), "Attack", 9),
    ("attack_hit", (72, 0, 32), "Attack", 12),
    ("cast", (72, 0, 32), "Cast", 16),
    ("die", (72, 0, 60), "Die", 36),
])
