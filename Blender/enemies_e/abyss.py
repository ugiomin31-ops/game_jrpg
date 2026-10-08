"""Chapter 6 — 심연의 핵 (abyss core) monsters, sculpted kit (monster v4).
Run through the production runner: python Blender/enemies_a/generate_all.py -- --only void_eye
"""
import math
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
sys.path.insert(1, os.path.join(HERE, '..', 'enemies_d'))
from kit_v4 import (Sculpt, BossSculpt, A, lerp_col, vgrad, rgba, hexmix, fibo, spine, ellipsoid_point, teeth, blade,  # noqa: E402,F401
                    lathe_helm, paint_where, paint_fn, dome, scale_region,
                    attack_env, cast_env, die_env, window, bump, ramp, soft, DIE_HOLD)
from sea import bezier, anime_head, hair_fall, stone_col, serpent_die, fish_fin  # noqa: E402,F401
from mathutils import Vector, noise  # noqa: E402

TAU = math.tau
VOID, VIOLET, MAGENTA, PALE_V = '#1a1226', '#6a3fb0', '#d04ad8', '#d9c8ff'


def horn(c, bone, name, base, mid, tip, r, color, tip_col=None, n=10):
    """Curved tapering horn along a quadratic bezier; the colour fades to `tip_col` toward the point."""
    o = c.tube(bone, name, bezier(base, mid, tip, n), r, color, taper=0.08)
    if tip_col:
        b, t = Vector(base), Vector(tip)
        L = (t - b).length
        paint_fn(o, lambda p: lerp_col(color, tip_col, ((p - b).length / L - 0.45) / 0.5))
    return o


def smoke(c, bone, root, direction, length, r, dark, light, curl=0.0):
    """A rising wisp of smoke: a tuft whose colour lightens toward its tip."""
    root, d = Vector(root), Vector(direction).normalized()
    col = lambda p: lerp_col(dark, light, ((p - root).dot(d) / length - 0.2) / 0.8)  # noqa: E731
    c.tuft(bone, tuple(root), tuple(d), length, r, col, curl=curl)


def smoke_tongue(c, bone, name, base, height, r, lean=(0, 0), dark='#2a1e3a', light='#9a88c8'):
    """A lick of dark smoke: a translucent teardrop (like the kit's flame) shading from soot to pale violet."""
    prof = [(0.0, -r * 0.4), (r * 0.8, 0.0), (r, height * 0.18), (r * 0.75, height * 0.5), (r * 0.3, height * 0.82), (0.0, height)]
    o = A.lathe(name, prof, color=dark, mat='M_Clear', seg=10)
    for v in o.data.vertices:
        t = max(0.0, v.co.z / height)
        v.co.x += lean[0] * t * t
        v.co.y += lean[1] * t * t
    paint_fn(o, lambda p: lerp_col(dark, light, (p.z / height - 0.3) / 0.7))
    o.location = base
    return c.add(bone, o)


# ---------------------------------------------------------------------------------------------- void_eye
def void_eye(eid):
    """공허의 눈 — a great bloodshot eyeball hanging in the dark. The eyeball IS the body: its back half is wrapped in
    a fleshy violet hood whose ragged rim forms heavy lids round the iris; a crown of six small slit-pupilled
    eyes on stalks rings the hood, and a skirt of curling tentacles trails beneath."""
    c = Sculpt(eid, tris=7500, ao=0.5)
    flesh, dark, rim = '#6a3590', '#2a1538', '#9a62c0'
    C = Vector((0, 0, 0.85))
    R = 0.25
    c.bone('body', tuple(C)); c.bone('eyes', (0, -0.2, 0.86), 'body')

    def skin(p):
        n = noise.noise(p * 12)
        vein = abs(noise.noise(p * 6 + Vector((2, 0, 1)))) < 0.035
        col = lerp_col(dark, flesh, 0.6 + (p.z - C.z) * 2.0 - (p.y - C.y) * 1.0 + 0.2 * n)
        return lerp_col(col, MAGENTA, 0.6) if vein else col
    # the great eyeball (a rigid sphere, like the kit's eyes but body sized), looking forward
    big = c.eye('eyes', tuple(C), (0, -1, 0.05), R, '#e0a020', pupil='#120810', sclera='#f4ece6', iris_edge=0.8)
    bloodshot(big, C, (0, -1, 0.05), 0.8)
    # crisp iris and pupil laid over the eyeball as a domed cornea (a body-sized eye needs clean edges)
    iris = A.sphere('iris', r=1, loc=tuple(C + Vector((0, -0.8 * R, 0))), scale=(0.6 * R, 0.22 * R, 0.6 * R), color='#e0a020',
                    seg=40, rings=16)
    A.apply_transform(iris)
    ic = C + Vector((0, -R, 0))
    paint_fn(iris, lambda p: '#3a1a10' if (Vector((p.x, 0, p.z)) - Vector((ic.x, 0, ic.z))).length > 0.56 * R else
             lerp_col('#ffd060', '#b05a10', (Vector((p.x, 0, p.z)) - Vector((ic.x, 0, ic.z))).length / (0.5 * R) + (p.z - ic.z) / R))
    c.add('eyes', iris)
    pupil = A.sphere('pupil', r=1, loc=tuple(C + Vector((0, -1.005 * R, 0))), scale=(0.11 * R, 0.06 * R, 0.36 * R), color='#120810',
                     seg=24, rings=10)
    c.add('eyes', pupil)
    c.add('eyes', A.sphere('glint', r=0.018, loc=tuple(C + Vector((-0.2 * R, -1.0 * R, 0.25 * R))), color='#ffffff', seg=10, rings=6))
    # fleshy hood over the back half; its front rim makes thick lids that leave the iris and some sclera bare
    c.blob('body', tuple(C + Vector((0, 0.1, 0.0))), (R * 1.04, R * 0.92, R * 1.02), skin)
    c.blob('body', tuple(C + Vector((0, 0.2, 0.0))), (R * 0.8, R * 0.6, R * 0.8), skin)
    for k in range(14):
        a = TAU * k / 14
        d = Vector((math.cos(a), 0, math.sin(a)))
        lid = 0.9 if abs(math.sin(a)) > 0.7 else 0.97          # lids come further over the eye top and bottom
        p = C + d * R * lid + Vector((0, -R * (0.45 if abs(math.sin(a)) > 0.7 else 0.3), 0))
        c.blob('eyes', tuple(p), (0.07, 0.07, 0.07), rim)
    # crown of small eyes on stalks around the hood
    for i in range(6):
        a = math.radians(90 + 360 * i / 6 + 30)
        d = Vector((math.cos(a), 0.15, math.sin(a))).normalized()
        base = C + Vector((math.cos(a) * R * 0.92, 0.1, math.sin(a) * R * 0.92))
        tip = base + d * 0.13 + Vector((0, -0.04, 0))
        c.limb('body', [tuple(base), tuple(base.lerp(tip, 0.5) + Vector((0, 0, 0.0))), tuple(tip)], [0.045, 0.032, 0.03], skin)
        look = Vector((math.cos(a) * 0.35, -1, math.sin(a) * 0.35)).normalized()
        c.eye('eyes', tuple(tip + look * 0.012), look, 0.032, '#f0b030', slit=True, sclera='#f6e8c8')
        c.blob('eyes', tuple(tip + Vector((0, 0.0, 0.026))), (0.036, 0.03, 0.014), rim)
    # tentacles beneath and behind
    for i in range(6):
        a = math.radians(360 * i / 6 + 15)
        name = f'tentacle{i + 1}'
        r0 = Vector((math.cos(a) * 0.13, 0.12 + math.sin(a) * 0.1, C.z - 0.17))
        c.bone(name, tuple(r0), 'body')
        out = Vector((math.cos(a), math.sin(a) * 0.8 + 0.3, 0)).normalized()
        pts = [r0, r0 + out * 0.05 + Vector((0, 0, -0.14)), r0 + out * 0.12 + Vector((0, 0, -0.3)),
               r0 + out * 0.22 + Vector((0, 0, -0.4)), r0 + out * 0.3 + Vector((0, 0, -0.36))]
        c.limb(name, [tuple(p) for p in pts], [0.05, 0.04, 0.03, 0.02, 0.01],
               lambda p: lerp_col(flesh, MAGENTA, (C.z - 0.25 - p.z) / 0.3))
    return c.finish('float')


def bloodshot(o, center, look, edge=0.75):
    """Thin red veins on the sclera of a big eyeball (corners whose direction from `center` is outside the iris)."""
    attr = o.data.color_attributes['Col']
    look = Vector(look).normalized()
    for loop in o.data.loops:
        p = o.data.vertices[loop.vertex_index].co
        d = (p - Vector(center)).normalized()
        front = d.dot(look)
        if front > edge:
            continue
        a = math.atan2(d.z, d.x)
        vein = abs(math.sin(a * 9 + noise.noise(p * 30) * 2.5)) < 0.12 and front > 0.05
        attr.data[loop.index].color_srgb = rgba('#c8304a') if vein else lerp_col('#f2e6e0', '#d8a8b8', max(0.0, 0.6 - front))


# ---------------------------------------------------------------------------------------------- shadow_beast
def shadow_beast(eid):
    """그림자 짐승 — a hulking wolf-beast made of smoke: a sooty black-violet body with a heavy hunched neck,
    wisps of smoke rising off its back, shoulders and tail and trailing from its legs, pale-violet eyes under
    heavy brows and a jaw hanging open on a violet-white glowing maw lined with fangs."""
    from beasts import canine_head, canine_body, neck
    c = Sculpt(eid, tris=10000, ao=0.55)
    pal = ('#1c1424', '#2e2238', '#4a3a5c', '#0c0810')
    back, side_c, pale, dark = pal
    fur = lambda p: lerp_col(pale, lerp_col(side_c, back, (p.z - 0.5) / 0.14), (p.z - 0.42) / 0.1)  # noqa: E731
    c.bone('body', (0, 0.04, 0.55))
    c.bone('head', (0, -0.33, 0.68), 'body'); c.bone('eyes', (0, -0.55, 0.79), 'head'); c.bone('jaw', (0, -0.47, 0.67), 'head')
    canine_body(c, pal, fur, bulk=1.25, tail_col=side_c)
    neck(c, ['body', 'head'], 0, fur, pale, k=1.15, mane=side_c, el=True)
    canine_head(c, 'head', 'eyes', 'jaw', 0, 1.12, pal, '#c9a8ff', ear=True, snarl=True)
    # glowing maw: a violet-white light deep in the open mouth
    c.add('jaw', A.sphere('maw_glow', r=0.035, loc=(0, -0.62, 0.712), scale=(1.1, 1.5, 0.45), color='#f0d8ff', mat='M_Emit', seg=14, rings=8))
    c.add('jaw', A.sphere('maw_glow_outer', r=0.06, loc=(0, -0.58, 0.715), scale=(0.95, 1.2, 0.5), color='#b070ff', mat='M_Clear',
                          seg=14, rings=8))
    # hunched shoulders
    c.blob('body', (0, -0.18, 0.7), (0.17, 0.15, 0.12), back)
    # smoke: dark translucent tongues streaming back and up off the spine, shoulders, legs and tail
    for k, (x, y, z, h) in enumerate(((0.0, -0.22, 0.78, 0.24), (0.0, -0.04, 0.76, 0.26), (0.0, 0.14, 0.73, 0.24),
                                      (0.0, 0.3, 0.7, 0.2), (0.11, -0.16, 0.7, 0.18), (-0.11, -0.16, 0.7, 0.18))):
        smoke_tongue(c, 'body', f'smoke{k}', (x, y, z), h, 0.085, lean=(x * 1.2, 0.3))
    for s_, side in ((-1, 'R'), (1, 'L')):
        x = s_ * 0.125
        smoke_tongue(c, 'leg.F' + side, f'smoke_f{side}', (x * 1.05, -0.19, 0.2), 0.16, 0.035, lean=(s_ * 0.04, 0.12))
        smoke_tongue(c, 'leg.B' + side, f'smoke_b{side}', (x * 1.1, 0.38, 0.22), 0.16, 0.035, lean=(s_ * 0.04, 0.12))
    for k in range(3):
        smoke_tongue(c, 'tail3', f'smoke_t{k}', (0.03 * (k - 1), 0.68, 0.46), 0.28 - 0.04 * abs(k - 1), 0.05, lean=(0.06 * (k - 1), 0.2))
    return c.finish('quad')


# ---------------------------------------------------------------------------------------------- chaos_spawn
def chaos_spawn(eid):
    """혼돈의 촉수 — a heaving mound of flesh with a gaping toothed maw for a face: a lumpy magenta-violet body,
    a ring of hooked fangs round a dark throat, three mismatched eyes clustered above it, and six suckered
    tentacles writhing up and out of the mass."""
    c = Sculpt(eid, tris=9500, ao=0.6)
    flesh, deep, sucker = '#8a3a8e', '#3e1a4a', '#f0b8d8'

    def hide(p):
        n = noise.noise(p * 8)
        col = lerp_col(deep, flesh, 0.4 + p.z * 1.0 + 0.35 * n)
        if noise.noise(p * 14 + Vector((5, 1, 0))) > 0.45:
            col = lerp_col(col, '#3fb8a0', 0.55)   # sickly teal mottling
        return col
    c.bone('body', (0, 0, 0.32)); c.bone('eyes', (0, -0.22, 0.6), 'body'); c.bone('jaw', (0, -0.18, 0.24), 'body')
    for co, r in (((0, 0.02, 0.28), (0.34, 0.3, 0.26)), ((0.16, 0.12, 0.2), (0.2, 0.2, 0.18)), ((-0.18, 0.08, 0.18), (0.19, 0.2, 0.16)),
                  ((0, -0.08, 0.46), (0.22, 0.2, 0.18)), ((0.08, 0.18, 0.44), (0.16, 0.14, 0.16))):
        c.blob('body', co, r, hide)
    # gaping maw on the front: a dark throat sunk into the mass, lips round it, fangs pointing inward
    M = Vector((0, -0.27, 0.33))
    c.blob('body', tuple(M + Vector((0, 0.02, 0))), (0.13, 0.12, 0.11), '#000000', negative=True)
    c.paint(tuple(M + Vector((0, 0.06, 0))), (0.13, 0.13, 0.12), '#1a0510', weight=2.0)
    for i in range(12):
        a = TAU * i / 12
        p = M + Vector((math.cos(a) * 0.14, 0.0, math.sin(a) * 0.125))
        c.blob('jaw' if math.sin(a) < 0 else 'body', tuple(p), (0.045, 0.04, 0.045), '#c25a98')
    ring = [M + Vector((math.cos(TAU * i / 14) * 0.115, -0.01, math.sin(TAU * i / 14) * 0.1)) for i in range(14)]
    for k, p in enumerate(ring):
        d = (M + Vector((0, 0.1, 0)) - p).normalized()
        spine(c, 'jaw' if p.z < M.z else 'body', f'fang{k}', tuple(p), d, 0.06 + 0.015 * (k % 2), 0.014, '#f2e8d0', tip='#ffffff', seg=6)
    c.paint(tuple(M + Vector((0, 0.03, -0.09))), (0.07, 0.06, 0.03), '#d04a7a', weight=2.2)        # tongue
    # three mismatched eyes clustered above the maw
    for k, (x, z, r, look) in enumerate(((-0.1, 0.57, 0.04, (-0.3, -1, 0.1)), (0.07, 0.6, 0.05, (0.2, -1, 0.15)),
                                          (0.17, 0.5, 0.03, (0.6, -1, 0.0)))):
        y = -0.2 + abs(x) * 0.3
        c.blob('eyes', (x, y + 0.01, z + r * 0.8), (r * 1.3, r * 0.9, r * 0.5), deep)
        c.eye('eyes', (x, y - 0.01, z), look, r, '#f0e040', slit=True, sclera='#f4e8d8')
    # tentacles
    for i in range(6):
        a = math.radians(40 + 360 * i / 6)
        n = f'tentacle{i + 1}'
        r0 = Vector((math.cos(a) * 0.2, 0.08 + math.sin(a) * 0.18, 0.42))
        c.bone(n, tuple(r0), 'body')
        out = Vector((math.cos(a), math.sin(a), 0))
        side = Vector((-out.y, out.x, 0))
        pts = [r0, r0 + out * 0.08 + Vector((0, 0, 0.15)), r0 + out * 0.18 + Vector((0, 0, 0.3)) + side * 0.05,
               r0 + out * 0.3 + Vector((0, 0, 0.36)) + side * 0.1, r0 + out * 0.38 + Vector((0, 0, 0.28)) + side * 0.06]
        c.limb(n, [tuple(p) for p in pts], [0.075, 0.06, 0.045, 0.03, 0.012], hide)
        for k in range(4):   # suckers along the underside of the curl
            q = Vector(pts[1]).lerp(Vector(pts[3]), k / 3) - out * 0.04
            c.paint(tuple(q), (0.018, 0.018, 0.018), sucker, weight=2.0)
    return c.finish('hop')


# ---------------------------------------------------------------------------------------------- gargoyle
def gargoyle(eid):
    """가고일 — a crouching cathedral gargoyle come to life: weathered grey-violet stone with moss in the creases,
    a muscular hunched torso, a snarling horned head with a beaked brow, stone bat wings on finger ribs, clawed
    feet and a spade-tipped tail."""
    from flyers import bat_wing
    c = Sculpt(eid, tris=10000, ao=0.65)
    base_stone = stone_col('#a6a2b2', '#6e6a80', None, 3.0)

    def stone(p):   # weathered stone with fine dark cracks
        if abs(noise.noise(p * 7 + Vector((0.3, 1.1, 2.0)))) < 0.025:
            return '#3a3646'
        return base_stone(p)
    dark, claw = '#3e3c4c', '#2a2832'
    c.bone('body', (0, 0, 0.95)); c.bone('head', (0, -0.08, 1.16), 'body'); c.bone('eyes', (0, -0.2, 1.23), 'head')
    c.bone('jaw', (0, -0.17, 1.13), 'head')
    c.blob('body', (0, 0.0, 1.02), (0.17, 0.13, 0.14), stone)
    c.blob('body', (0, -0.04, 0.9), (0.13, 0.11, 0.1), stone)
    c.blob('body', (0, 0.02, 0.8), (0.12, 0.1, 0.07), stone)
    c.blob('body', (0, -0.1, 1.0), (0.13, 0.05, 0.08), stone)                                      # pecs
    for s in (-1, 1):
        c.blob('body', (s * 0.15, 0, 1.08), (0.08, 0.08, 0.07), stone)
    c.paint((0, -0.15, 0.9), (0.06, 0.02, 0.008), dark, weight=1.3)
    # head: heavy brow, short muzzle, snarling jaw, horns sweeping back, pointed ears
    c.blob('head', (0, -0.1, 1.22), (0.1, 0.1, 0.085), stone)
    c.limb('head', [(0, -0.17, 1.2), (0, -0.24, 1.18)], [0.06, 0.045], stone)
    c.blob('eyes', (0, -0.19, 1.27), (0.09, 0.04, 0.025), stone)                                   # brow ridge
    for s in (-1, 1):
        c.eye('eyes', (s * 0.045, -0.19, 1.24), (s * 0.35, -1, 0.0), 0.022, '#ff8a3a', slit=True, sclera='#e8dcc0')
        horn(c, 'head', f'horn{s}', (s * 0.06, -0.08, 1.3), (s * 0.15, 0.0, 1.42), (s * 0.12, 0.12, 1.46), 0.03, '#4a4658', '#cfc6d8')
        c.bone('ear.' + ('L' if s > 0 else 'R'), (s * 0.09, -0.06, 1.25), 'head')
        c.blob('ear.' + ('L' if s > 0 else 'R'), (s * 0.13, -0.05, 1.27), (0.05, 0.012, 0.025), stone, rot=(0, -s * 25, s * 20))
    c.limb('jaw', [(0, -0.12, 1.13), (0, -0.2, 1.12), (0, -0.25, 1.13)], [0.05, 0.04, 0.03], stone)
    c.paint((0, -0.24, 1.15), (0.04, 0.03, 0.006), '#1a1420', weight=1.6)
    for s in (-1, 1):
        spine(c, 'jaw', f'tusk{s}', (s * 0.03, -0.24, 1.135), (s * 0.15, -0.3, 1), 0.05, 0.011, '#e8e0d0', tip='#ffffff', seg=6)
        spine(c, 'head', f'fang{s}', (s * 0.02, -0.25, 1.165), (0, -0.2, -1), 0.03, 0.007, '#e8e0d0', seg=6)
    # arms and legs
    for s, side in ((-1, 'R'), (1, 'L')):
        c.bone('arm.' + side, (s * 0.17, -0.02, 1.08), 'body')
        c.limb('arm.' + side, [(s * 0.18, -0.02, 1.08), (s * 0.24, -0.06, 0.95), (s * 0.24, -0.13, 0.85)], [0.06, 0.05, 0.045], stone)
        c.blob('arm.' + side, (s * 0.24, -0.16, 0.82), (0.05, 0.05, 0.045), stone)
        for j in range(3):
            spine(c, 'arm.' + side, f'claw{side}{j}', (s * 0.24 + (j - 1) * 0.025, -0.19, 0.8), (0, -0.6, -1), 0.05, 0.01, claw, seg=6)
        c.bone('leg.' + side, (s * 0.09, 0.02, 0.8), 'body')
        c.blob('leg.' + side, (s * 0.11, -0.02, 0.72), (0.075, 0.1, 0.08), stone)                  # haunch
        c.limb('leg.' + side, [(s * 0.11, -0.04, 0.66), (s * 0.12, -0.1, 0.56), (s * 0.12, 0.0, 0.48), (s * 0.12, -0.02, 0.4)],
               [0.055, 0.045, 0.035, 0.035], stone)
        c.blob('leg.' + side, (s * 0.12, -0.06, 0.39), (0.045, 0.07, 0.025), stone)
        for j in range(3):
            spine(c, 'leg.' + side, f'talon{side}{j}', (s * 0.12 + (j - 1) * 0.025, -0.11, 0.39), (0, -1, -0.5), 0.04, 0.01, claw, seg=6)
        c.bone('wing.' + side, (s * 0.1, 0.08, 1.1), 'body')
        tips = [(s * 0.68, 0.12, 1.42), (s * 0.78, 0.14, 1.1), (s * 0.6, 0.16, 0.84)]
        bat_wing(c, 'wing.' + side, s, (s * 0.1, 0.09, 1.1), (s * 0.42, 0.11, 1.3), tips, (s * 0.1, 0.12, 0.86),
                 (s * 0.3, 0.12, 1.08), '#8a8698', '#7a7490', '#4a4458', r=0.04)
    # tail with a spade tip
    c.bone('tail1', (0, 0.1, 0.82), 'body'); c.bone('tail2', (0, 0.26, 0.66), 'tail1')
    c.limb(['tail1', 'tail1', 'tail2'], [(0, 0.08, 0.84), (0, 0.22, 0.72), (0.04, 0.32, 0.56), (0.06, 0.4, 0.46)], [0.05, 0.04, 0.03, 0.02], stone)
    sp = A.extrude_shape('tail_spade', [(0, 0), (0.05, 0.05), (0.03, 0.06), (0, 0.13), (-0.03, 0.06), (-0.05, 0.05)], depth=0.02,
                         color='#5c5a6c')
    sp.rotation_mode = 'QUATERNION'
    sp.rotation_quaternion = Vector((0.15, 0.5, -0.6)).to_track_quat('Z', 'Y')
    sp.location = (0.06, 0.4, 0.46)
    c.add('tail2', sp)
    c.post = _moss(0.7)
    return c.finish('fly')


def _moss(up):
    def f(p, n, col):
        k = (n.z - up) / (1 - up)
        if k <= 0 or noise.noise(p * 9) < 0.35:
            return col
        return lerp_col(col, '#6f8a5a', min(0.6, 1.2 * k))
    return f


# ---------------------------------------------------------------------------------------------- nightmare
def nightmare(eid):
    """나이트메어 — a black war-horse of bad dreams: a deep-chested ink-black body with a violet sheen, slender
    legs on dark hooves wreathed in violet fire, a long head with a flaring nostril and a cold red eye, and a
    mane and tail of tall violet flame."""
    c = Sculpt(eid, tris=10000, ao=0.55)
    coat, sheen, hoof = '#16121e', '#3a2c52', '#0a080c'

    def hide(p):
        return lerp_col(sheen, coat, 0.5 + (0.75 - p.z) * 3.0 + 0.3 * noise.noise(p * 6))
    c.bone('body', (0, 0.05, 0.66))
    c.bone('head', (0, -0.36, 0.98), 'body'); c.bone('eyes', (0, -0.5, 1.16), 'head'); c.bone('jaw', (0, -0.6, 1.0), 'head')
    # barrel, deep chest and round haunches
    c.blob('body', (0, -0.2, 0.68), (0.165, 0.18, 0.2), hide)
    c.blob('body', (0, 0.02, 0.68), (0.155, 0.25, 0.17), hide)
    c.blob('body', (0, 0.26, 0.7), (0.17, 0.16, 0.175), hide)
    c.blob('body', (0, 0.33, 0.78), (0.12, 0.1, 0.09), hide)
    c.blob('body', (0, -0.3, 0.6), (0.1, 0.06, 0.1), hide)                                          # breast
    # neck arching up to the head
    c.limb(['body', 'body', 'head', 'head'], [(0, -0.24, 0.78), (0, -0.32, 0.92), (0, -0.37, 1.04), (0, -0.41, 1.12)],
           [0.135, 0.115, 0.095, 0.08], hide)
    c.blob('head', (0, -0.43, 1.150), (0.07, 0.08, 0.07), hide)
    c.limb('head', [(0, -0.47, 1.130), (0, -0.56, 1.060), (0, -0.62, 1.000)], [0.06, 0.05, 0.045], hide)
    c.blob('head', (0, -0.645, 0.985), (0.045, 0.035, 0.04), '#2a2232')                            # muzzle
    for s in (-1, 1):
        c.paint((s * 0.022, -0.675, 0.990), (0.01, 0.012, 0.012), '#5a1a2a', weight=2.0)          # flared nostrils
        c.blob('eyes', (s * 0.05, -0.47, 1.200), (0.03, 0.04, 0.015), coat, rot=(0, s * 20, 0))
        c.eye('eyes', (s * 0.058, -0.48, 1.175), (s * 0.85, -0.5, 0.05), 0.022, '#e0303a', sclera='#2a1a22', pupil='#1a0a0a')
        c.bone('ear.' + ('L' if s > 0 else 'R'), (s * 0.04, -0.4, 1.210), 'head')
        c.blob('ear.' + ('L' if s > 0 else 'R'), (s * 0.045, -0.4, 1.250), (0.02, 0.015, 0.05), hide, rot=(0, -s * 10, 0))
        horn(c, 'head', f'horn{s}', (s * 0.03, -0.45, 1.210), (s * 0.06, -0.42, 1.320), (s * 0.04, -0.33, 1.380), 0.016, '#2a2236', '#a070e0')
    c.paint((0, -0.62, 0.965), (0.04, 0.03, 0.006), '#08060a', weight=1.5)                         # mouth line
    # legs
    for s, side in ((-1, 'R'), (1, 'L')):
        x = s * 0.09
        c.bone('leg.F' + side, (x, -0.22, 0.62), 'body')
        c.blob('leg.F' + side, (x, -0.22, 0.56), (0.07, 0.09, 0.11), hide)
        c.limb('leg.F' + side, [(x, -0.23, 0.48), (x, -0.25, 0.33), (x, -0.23, 0.17), (x, -0.235, 0.08)], [0.055, 0.04, 0.032, 0.036], hide)
        c.blob('leg.F' + side, (x, -0.245, 0.035), (0.045, 0.05, 0.04), hoof)
        c.bone('leg.B' + side, (x, 0.28, 0.66), 'body')
        c.blob('leg.B' + side, (x * 1.15, 0.28, 0.58), (0.075, 0.12, 0.14), hide)
        c.limb('leg.B' + side, [(x * 1.1, 0.3, 0.46), (x, 0.36, 0.3), (x, 0.3, 0.17), (x, 0.305, 0.08)], [0.06, 0.04, 0.032, 0.036], hide)
        c.blob('leg.B' + side, (x, 0.305, 0.035), (0.045, 0.05, 0.04), hoof)
        for k, (b, y) in enumerate((('leg.F' + side, -0.25), ('leg.B' + side, 0.3))):
            c.flame(b, f'hoof_fire{side}{k}', (x, y + 0.02, 0.05), 0.16, 0.045, outer='#8a3aff', inner='#ff9af0', lean=(0, 0.06))
    # flame mane (on the head, so it rides the neck) and tail
    for j in range(7):
        t = j / 6
        p = Vector((0, -0.42, 1.22)).lerp(Vector((0, -0.22, 0.84)), t)
        b = 'head' if t < 0.5 else 'body'
        for side_x in (-0.022, 0.022):
            c.flame(b, f'flame_mane{j}{side_x}', tuple(p + Vector((side_x * (1 + j % 2), 0.04, 0))), 0.3 - 0.08 * t, 0.055,
                    outer='#8a3aff', inner='#ffb0f8', lean=(side_x * 3, 0.2, 0))
    c.bone('flame_tail', (0, 0.38, 0.76), 'body')
    c.flame('flame_tail', 'tail_flame', (0, 0.38, 0.76), 0.46, 0.085, outer='#8a3aff', inner='#ffb0f8', lean=(0, 0.25))
    c.flame('flame_tail', 'tail_flame2', (0.03, 0.37, 0.74), 0.34, 0.06, outer='#6a2ae0', inner='#ff9af0', lean=(0.06, 0.2))
    return c.finish('quad')


# ---------------------------------------------------------------------------------------------- doppelganger
def mirror_post(crack_scale=3.2, tint='#b8b0d8'):
    """post-paint for living mirror-glass: a sky-bright top and dark lower reflection split by a soft horizon,
    a violet tint, and a web of dark cracks with pale chipped edges."""
    def f(p, n, col):
        h = n.z
        sky = lerp_col('#e8ecff', '#9fb2e8', 1 - h) if h > -0.05 else lerp_col('#3a3456', '#16122a', -h)
        base = lerp_col(sky, tint, 0.35)
        q = abs(noise.noise(p * crack_scale + Vector((1.7, 0.3, 2.2))))
        r = abs(noise.noise(p * crack_scale * 1.7 + Vector((4.1, 2.0, 0.6))))
        if q < 0.05 or r < 0.035:
            return rgba('#120c1e')
        if q < 0.08 or r < 0.055:
            return rgba('#ffffff')
        return lerp_col(base, col, 0.25)
    return f


def doppelganger(eid):
    """도플갱어 — a faceless humanoid of living mirror-glass: a slender, elegant body whose surface reflects a bright
    sky above and darkness below, split by a web of cracks; a smooth blank egg of a face with one shard broken
    out of it showing the violet void inside, splinters of glass drifting round its shoulders and a long glass
    blade grown from its right forearm."""
    c = Sculpt(eid, tris=9000, ao=0.45)
    c.post = mirror_post()
    glass = '#c8c4e0'
    c.bone('body', (0, 0, 0.62)); c.bone('head', (0, -0.01, 1.04), 'body')
    c.blob('body', (0, 0, 0.9), (0.16, 0.1, 0.11), glass)
    c.blob('body', (0, -0.02, 0.92), (0.12, 0.07, 0.07), glass)                                  # chest
    c.blob('body', (0, 0.0, 0.76), (0.1, 0.075, 0.09), glass)
    c.blob('body', (0, 0.0, 0.62), (0.13, 0.09, 0.08), glass)
    for s in (-1, 1):
        c.blob('body', (s * 0.15, 0, 0.95), (0.06, 0.06, 0.055), glass)
    c.limb('head', [(0, 0, 0.98), (0, -0.01, 1.05)], [0.035, 0.035], glass)
    c.blob('head', (0, -0.015, 1.15), (0.09, 0.095, 0.115), glass)                                  # blank egg face
    c.blob('head', (0, -0.015, 1.15), (0.03, 0.04, 0.035), '#000000', negative=True)
    c.add('head', A.sphere('void_hole', r=0.034, loc=(0.03, -0.085, 1.17), scale=(1, 0.5, 1.2), color='#5a2a9a', mat='M_Emit', seg=12, rings=7))
    for s, side in ((-1, 'R'), (1, 'L')):
        c.bone('arm.' + side, (s * 0.14, 0, 0.94), 'body')
        c.limb('arm.' + side, [(s * 0.16, 0, 0.94), (s * 0.22, -0.02, 0.8), (s * 0.25, -0.06, 0.66)], [0.048, 0.04, 0.034], glass)
        c.blob('arm.' + side, (s * 0.26, -0.08, 0.62), (0.034, 0.03, 0.045), glass)
        c.bone('leg.' + side, (s * 0.075, 0, 0.58), 'body')
        c.limb('leg.' + side, [(s * 0.075, 0, 0.58), (s * 0.085, -0.01, 0.34), (s * 0.085, 0.01, 0.08)], [0.068, 0.05, 0.04], glass)
        c.blob('leg.' + side, (s * 0.085, -0.04, 0.035), (0.045, 0.08, 0.03), glass)
        for j in range(3):   # shards jutting from the shoulder and forearm
            c.gem('arm.' + side, f'shoulder_shard{side}{j}', (s * (0.15 + 0.03 * j), 0.02, 1.0 - 0.02 * j), (s * 0.5, 0.3 + 0.2 * j, 1),
                  0.025, 0.14 - 0.03 * j, '#f4f6ff', '#9a90d0', mat='M_Clear', sides=4)
        c.gem('arm.' + side, f'forearm_shard{side}', (s * 0.24, 0.0, 0.74), (s * 0.6, 0.8, 0.2), 0.02, 0.1, '#f4f6ff', '#9a90d0',
              mat='M_Clear', sides=4)
    # glass blade grown from the right forearm
    c.bone('weapon.R', (-0.25, -0.08, 0.63), 'arm.R')
    c.gem('weapon.R', 'arm_blade', (-0.25, -0.09, 0.62), (0, -0.25, -1), 0.03, 0.42, '#f0f4ff', '#8a80c0', mat='M_Clear', sides=4)
    # glass splinters drifting round the shoulders and head
    for k, (p, d, h) in enumerate((((0.22, 0.06, 1.08), (0.4, 0.3, 1), 0.09), ((-0.2, 0.08, 1.12), (-0.5, 0.2, 1), 0.08),
                                   ((0.14, 0.1, 1.28), (0.2, 0.2, 1), 0.07), ((-0.12, 0.12, 1.3), (-0.3, 0.1, 1), 0.06),
                                   ((0.0, 0.16, 1.2), (0, 0.6, 1), 0.07))):
        c.gem('head' if p[2] > 1.15 else 'body', f'splinter{k}', p, d, 0.02, h, '#f4f6ff', '#9a90d0', mat='M_Clear', sides=4)
    c.arm_limit = (80, 30)
    return c.finish('biped')


# ---------------------------------------------------------------------------------------------- abyss_worm
def abyss_worm(eid):
    """심연 벌레 — a huge segmented worm bursting up through the floor: thick ringed segments of pale bruise-violet
    flesh with darker bands, rubble heaved up around the hole, and a round head that is all mouth — a lipped
    ring with three rows of hooked teeth spiralling into a dark throat, ringed by short twitching feelers."""
    c = Sculpt(eid, tris=9500, ao=0.6)
    flesh, band, deep = '#b89ac8', '#6a4a86', '#3a2450'
    c.bone('body', (0, 0.0, 0.35)); c.bone('head', (0, -0.1, 0.85), 'body'); c.bone('jaw', (0, -0.3, 1.0), 'head')
    # the arching body: segment rings alternate fat and thin along the spine curve
    path = [Vector(p) for p in bezier((0, 0.14, -0.05), (0, 0.12, 1.1), (0, -0.3, 1.08), 26)]
    radii = [0.19 + 0.02 * math.sin(math.pi * i / 26) for i in range(27)]
    for i, (p, r) in enumerate(zip(path, radii)):
        b = 'root' if p.z < 0.25 else 'body' if p.z < 0.8 else 'head'
        nxt = path[min(i + 1, 26)] - path[max(i - 1, 0)]
        rot = [math.degrees(v) for v in nxt.normalized().to_track_quat('Z', 'Y').to_euler()]
        if i % 2 == 0:   # a fat ring: an oblate disc across the body, pale on the belly side
            col = lambda q, p=p: lerp_col(flesh, '#ecdcec', max(0.0, -(q.y - p.y) / 0.14 - 0.1))  # noqa: E731
            c.blob(b, tuple(p), (r * 1.1, r * 1.1, r * 0.5), col, rot=rot, stiff=3.0)
        else:            # the dark groove between rings
            c.blob(b, tuple(p), (r * 0.9, r * 0.9, r * 0.5), band, rot=rot)
    # the mouth: a fleshy lip ring facing forward and down, throat cut deep into the head
    M = path[-1] + Vector((0, -0.1, -0.02))
    look = Vector((0, -1, -0.35)).normalized()
    side = Vector((1, 0, 0))
    up = side.cross(look).normalized() * -1
    for k in range(14):
        a = TAU * k / 14
        p = M + (side * math.cos(a) + up * math.sin(a)) * 0.16
        c.blob('jaw' if math.sin(a) < -0.2 else 'head', tuple(p), (0.06, 0.06, 0.06), '#d06a8a')
    c.blob('head', tuple(M + look * 0.05), (0.14, 0.14, 0.13), '#000000', negative=True)
    c.paint(tuple(M - look * 0.05), (0.12, 0.12, 0.12), '#2a0a18', weight=2.2)
    for row, (rad, L, depth) in enumerate(((0.14, 0.075, 0.0), (0.11, 0.06, 0.045), (0.08, 0.05, 0.09))):
        n = 14 - row * 3
        for k in range(n):
            a = TAU * (k + row * 0.5) / n
            p = M + (side * math.cos(a) + up * math.sin(a)) * rad - look * depth
            d = (M - look * (depth + 0.1) - p).normalized()
            spine(c, 'jaw' if math.sin(a) < -0.2 else 'head', f'tooth{row}_{k}', tuple(p), d, L, 0.012, '#f2e8d4', tip='#ffffff', seg=6)
    for k in range(8):   # feelers round the rim
        a = TAU * (k + 0.5) / 8
        root = M + (side * math.cos(a) + up * math.sin(a)) * 0.21 + look * 0.0
        out = (side * math.cos(a) + up * math.sin(a)) * 0.8 + look * 0.6
        c.tuft('jaw' if math.sin(a) < -0.2 else 'head', tuple(root), tuple(out), 0.12, 0.022, '#e08aa8', curl=-0.3)
    # heaved-up rubble round the hole
    for k in range(9):
        a = TAU * k / 9
        r = 0.29 + 0.04 * (k % 2)
        c.chunk('root', f'rubble{k}', (r * math.cos(a), 0.14 + r * math.sin(a), 0.05), (0.09, 0.07, 0.06 + 0.02 * (k % 3)), '#5a5068',
                seed=k + 3, jitter=0.15)

    def extra(a, clip, f, t, i, names):
        if clip == 'Die':
            serpent_die(a, f, t, slump=75.0)
        else:
            a.r('root', f, (0, 0, 0))
            a.l('root', f, (0, 0, 0))
    return c.finish('biped', extra)


# ---------------------------------------------------------------------------------------------- fallen_angel
def broken_halo(c, bone, center, R, tilt, gap=(70, 120), color='#ffe9a8'):
    """A halo ring with a broken-out arc (degrees `gap`) and the snapped piece drifting nearby."""
    pts = []
    for d in range(gap[1], gap[0] + 360 + 1, 10):
        a = math.radians(d)
        pts.append(Vector((math.cos(a) * R, math.sin(a) * R, 0)))
    from mathutils import Matrix
    M = Matrix.Rotation(math.radians(tilt), 3, 'X')
    pts = [tuple(Vector(center) + M @ p) for p in pts]
    c.tube(bone, 'halo', pts, R * 0.07, color, mat='M_Emit')
    frag = []
    for d in range(gap[0] + 12, gap[1] - 12, 8):
        a = math.radians(d)
        frag.append(tuple(Vector(center) + M @ Vector((math.cos(a) * R * 1.18, math.sin(a) * R * 1.18, -R * 0.25))))
    c.tube(bone, 'halo_shard', frag, R * 0.06, color, mat='M_Emit')


def fallen_angel(eid):
    """타락 천사 — a fallen angel: a tall pale warrior with long silver hair and red eyes, black-and-violet armour
    over a torn white robe, huge ragged black wings shading to violet at the tips, a cracked, tilted halo with a
    piece broken out of it, and a long greatsword with a violet-lit edge."""
    sys.path.insert(0, os.path.join(HERE, '..', 'enemies_d'))
    from flyers import feather_wing
    c = Sculpt(eid, tris=10000, ao=0.5)
    skin, hair, armor, trim, robe = '#f2e4e4', '#d8d4e8', '#2a2034', '#8a5ad0', '#e8e4f0'
    c.bone('body', (0, 0, 0.98)); c.bone('head', (0, -0.01, 1.3), 'body'); c.bone('eyes', (0, -0.1, 1.4), 'head')
    c.bone('crest', (0, 0.06, 1.5), 'head')
    c.blob('body', (0, 0, 1.17), (0.13, 0.08, 0.09), armor)
    c.blob('body', (0, 0, 1.05), (0.09, 0.07, 0.08), armor)
    c.blob('body', (0, 0, 0.95), (0.11, 0.08, 0.07), robe)
    for s in (-1, 1):
        c.blob('body', (s * 0.12, 0, 1.2), (0.05, 0.05, 0.045), armor)
    c.paint((0, -0.075, 1.17), (0.12, 0.03, 0.012), trim, weight=1.6)
    c.paint((0, -0.08, 1.1), (0.012, 0.03, 0.07), trim, weight=1.6)
    c.blob('head', (0, -0.005, 1.27), (0.035, 0.035, 0.05), skin)
    anime_head(c, 'head', 'eyes', (0, -0.01, 1.4), 0.95, skin, '#e0303a', '#5a5470', lips='#9a5a6a')
    hair_fall(c, 'head', (0, -0.01, 1.41), 0.95, hair, locks=9, length=0.55, back=0.18)
    broken_halo(c, 'crest', (0, 0.08, 1.58), 0.11, -25)
    # torn robe skirt: ragged strips
    for k in range(9):
        a = math.radians(-140 + 280 * k / 8)
        root = (0.1 * math.sin(a), -0.075 * math.cos(a), 0.92)
        L = 0.32 + 0.12 * ((k * 7) % 3) / 2
        c.tuft('body', root, (math.sin(a) * 0.25, -0.25 * math.cos(a) + 0.05, -1), L, 0.045, robe if k % 2 else '#c8c0d8')
    for s, side in ((-1, 'R'), (1, 'L')):
        c.bone('wing.' + side, (s * 0.07, 0.07, 1.2), 'body')
        feather_wing(c, 'wing.' + side, s, (s * 0.07, 0.08, 1.2), 0.85, 0.3, '#1a1422', '#7a3ac8', '#2e2440', '#1a1422', feathers=7,
                     r=0.03)
        c.bone('arm.' + side, (s * 0.13, 0, 1.2), 'body')
        c.limb('arm.' + side, [(s * 0.14, 0, 1.2), (s * 0.19, -0.03, 1.06), (s * 0.22, -0.08, 0.94)], [0.035, 0.03, 0.026], skin)
        c.blob('arm.' + side, (s * 0.2, -0.04, 1.03), (0.035, 0.035, 0.05), armor)                    # vambrace
        c.blob('arm.' + side, (s * 0.225, -0.1, 0.91), (0.025, 0.025, 0.032), skin)
        c.add('arm.' + side, dome(f'pauldron{side}', (s * 0.15, 0.0, 1.24), (0.07, 0.07, 0.045), color=armor))
        c.bone('leg.' + side, (s * 0.06, 0, 0.9), 'body')
        c.limb('leg.' + side, [(s * 0.06, 0, 0.9), (s * 0.07, -0.01, 0.68), (s * 0.07, 0.01, 0.48)], [0.042, 0.034, 0.026], armor)
        c.blob('leg.' + side, (s * 0.07, -0.03, 0.44), (0.028, 0.06, 0.022), armor)
    # greatsword in the right hand, held point-down and forward
    c.bone('weapon.R', (-0.225, -0.1, 0.91), 'arm.R')
    x, y = -0.225, -0.11
    c.tube('weapon.R', 'grip', [(x, y, 0.84), (x, y, 1.0)], 0.014, '#3a2a40')
    c.tube('weapon.R', 'guard', [(x - 0.1, y, 0.84), (x, y, 0.83), (x + 0.1, y, 0.84)], 0.016, '#8a5ad0')
    c.orb('weapon.R', 'pommel', (x, y, 1.01), (0.02, 0.02, 0.02), '#c9a0ff')
    blade(c, 'weapon.R', 'greatsword', (x, y, 0.83), 0.72, 0.075, '#3a3448', edge='#b070ff', depth=0.018, axis=(0, 0, -1))
    c.arm_limit = (80, 30)
    return c.finish('fly')


# ---------------------------------------------------------------------------------------------- void_reaper
def void_reaper(eid):
    """공허의 사신 — a hooded reaper drifting over the floor: a deep cowl with only two pale eyes in its shadow, a
    tattered black-violet robe streaming into ragged strips, bony grey hands, a bone clasp with a void gem, and a
    long scythe whose crescent blade burns violet along its edge."""
    c = Sculpt(eid, tris=10000, ao=0.5)
    cloth, inner, bone_c = '#231a30', '#0a0610', '#cfc6b8'
    robe = lambda p: lerp_col('#3a2a52', cloth, (p.z - 0.6) / 0.6)  # noqa: E731
    c.bone('body', (0, 0, 1.0)); c.bone('head', (0, 0, 1.32), 'body'); c.bone('eyes', (0, -0.12, 1.4), 'head')
    c.bone('cape', (0, 0.1, 1.3), 'body')
    c.blob('body', (0, 0, 1.2), (0.17, 0.12, 0.12), robe)
    c.blob('body', (0, 0.01, 1.0), (0.15, 0.12, 0.16), robe)
    c.blob('body', (0, 0.02, 0.78), (0.17, 0.14, 0.14), robe)
    for k in range(11):   # ragged strips trailing beneath
        a = math.radians(360 * k / 11)
        root = (0.14 * math.cos(a), 0.02 + 0.12 * math.sin(a), 0.68)
        c.tuft('body', root, (math.cos(a) * 0.3, math.sin(a) * 0.3 + 0.15, -1), 0.28 + 0.1 * (k % 3) / 2, 0.055, robe)
    # cowl: a deep hood with a dark hollow
    c.blob('head', (0, 0.0, 1.4), (0.13, 0.14, 0.14), robe)
    c.blob('head', (0, 0.06, 1.48), (0.08, 0.1, 0.08), robe)
    c.blob('head', (0, -0.12, 1.38), (0.085, 0.09, 0.1), '#000000', negative=True)
    c.paint((0, -0.11, 1.38), (0.1, 0.07, 0.11), inner, weight=2.2)
    for s in (-1, 1):
        c.eye('eyes', (s * 0.035, -0.07, 1.39), (s * 0.15, -1, -0.05), 0.019, '#c8b8ff', sclera='#100818', pupil='#f4f0ff',
              iris_edge=0.88, glint=False)
    c.orb('body', 'clasp', (0, -0.115, 1.24), (0.03, 0.015, 0.03), '#b08a3a')
    c.gem('body', 'clasp_gem', (0, -0.13, 1.24), (0, -1, 0), 0.02, 0.03, '#d8b8ff', '#5a2aa0')
    c.membrane('cape', 'cape', (0, 0.12, 1.3), [(-0.17, 0.08, 1.3), (-0.24, 0.2, 0.9), (-0.18, 0.26, 0.6), (-0.08, 0.24, 0.72),
                                                 (0, 0.28, 0.52), (0.08, 0.24, 0.7), (0.18, 0.26, 0.58), (0.24, 0.2, 0.9),
                                                 (0.17, 0.08, 1.3)], '#2a1e3a', thick=0.012, edge_color='#4a2a7a')
    for s, side in ((-1, 'R'), (1, 'L')):
        c.bone('arm.' + side, (s * 0.16, 0, 1.22), 'body')
        c.limb('arm.' + side, [(s * 0.17, 0, 1.22), (s * 0.25, -0.05, 1.08), (s * 0.27, -0.12, 0.98)], [0.06, 0.06, 0.075], robe)
        c.limb('arm.' + side, [(s * 0.27, -0.14, 0.97), (s * 0.28, -0.17, 0.93)], [0.025, 0.022], bone_c)
        for j in range(3):
            c.tube('arm.' + side, f'finger{side}{j}', [(s * 0.28 + (j - 1) * 0.012, -0.18, 0.93), (s * 0.285 + (j - 1) * 0.014, -0.21, 0.88),
                                                      (s * 0.28 + (j - 1) * 0.014, -0.2, 0.84)], 0.0075, bone_c, taper=0.5)
    # scythe
    c.bone('weapon.R', (-0.28, -0.17, 0.93), 'arm.R')
    x, y = -0.28, -0.18
    c.tube('weapon.R', 'snath', [(x, y, 0.3), (x + 0.01, y, 0.9), (x - 0.01, y, 1.6)], 0.016, '#2a2030')
    for z in (0.5, 0.93, 1.3):
        c.ring('weapon.R', f'snath_band{z}', (x, y, z), 0.02, 0.006, bone_c)
    crescent = [(0, 0), (0.08, 0.06), (0.22, 0.08), (0.38, 0.03), (0.52, -0.09), (0.6, -0.22), (0.46, -0.12), (0.3, -0.06),
                (0.14, -0.04), (0, -0.04)]
    bl = A.extrude_shape('scythe_blade', [(-u, v) for u, v in crescent], depth=0.014, color='#2c2838')
    paint_where(bl, lambda v: (v.z < -0.06 and v.x < -0.25) or (v.z < -0.02 and v.x < -0.1 and v.z < 0.03 - 0.0 * v.x) and False, '#b070ff')
    attr = bl.data.color_attributes['Col']
    for loop in bl.data.loops:   # violet glow along the inner (cutting) edge
        v = bl.data.vertices[loop.vertex_index].co
        u = -v.x
        inner_edge = -0.04 - 0.18 * max(0.0, (u - 0.14) / 0.46) ** 1.6
        if v.z < inner_edge + 0.035:
            attr.data[loop.index].color_srgb = rgba('#c890ff')
    bl.location = (x - 0.01, y, 1.58)
    c.add('weapon.R', bl)
    c.gem('weapon.R', 'snath_gem', (x - 0.01, y - 0.01, 1.6), (0, 0, 1), 0.02, 0.06, '#d8b8ff', '#5a2aa0')
    c.arm_limit = (70, 28)
    return c.finish('float')


# ---------------------------------------------------------------------------------------------- crystal_horror
def crystal_horror(eid):
    """수정 괴수 — a hulking beast grown through with violet abyss crystals: a heavy, low-slung body of dark
    violet rock-hide, massive forelimbs, a blunt head with a crystal horn, small cold eyes and a jaw of crystal
    teeth, and clusters of faceted crystals erupting from its back, shoulders and tail."""
    c = Sculpt(eid, tris=10500, ao=0.6)
    hide_base = stone_col('#4a3a62', '#2a2038', None, 5.0)

    def hide(p):
        if abs(noise.noise(p * 3.5 + Vector((2.0, 0.4, 1.0)))) < 0.045:
            return lerp_col('#b070ff', '#e0c8ff', 0.4)     # crystal veins glinting through the hide
        return hide_base(p)
    belly_c = '#6a5a7a'
    c.bone('body', (0, 0.05, 0.6))
    c.bone('head', (0, -0.42, 0.6), 'body'); c.bone('eyes', (0, -0.6, 0.66), 'head'); c.bone('jaw', (0, -0.55, 0.52), 'head')
    c.blob('body', (0, -0.18, 0.66), (0.26, 0.24, 0.24), hide)                                      # hunched shoulders
    c.blob('body', (0, 0.12, 0.58), (0.21, 0.24, 0.19), hide)
    c.blob('body', (0, 0.32, 0.54), (0.19, 0.14, 0.17), hide)
    c.blob('body', (0, -0.06, 0.45), (0.17, 0.26, 0.1), belly_c)
    # head: low, blunt, heavy brow and jaw
    c.blob('head', (0, -0.48, 0.62), (0.14, 0.15, 0.12), hide)
    c.blob('head', (0, -0.6, 0.6), (0.11, 0.08, 0.08), hide)
    c.blob('eyes', (0, -0.6, 0.69), (0.12, 0.05, 0.035), hide)                                     # brow
    for s in (-1, 1):
        c.eye('eyes', (s * 0.065, -0.635, 0.655), (s * 0.4, -1, 0.0), 0.02, '#b880ff', slit=True, sclera='#e8dcf0')
    c.limb('jaw', [(0, -0.46, 0.52), (0, -0.58, 0.5), (0, -0.66, 0.52)], [0.1, 0.085, 0.06], belly_c)
    c.paint((0, -0.66, 0.555), (0.08, 0.04, 0.008), '#1a0e24', weight=1.6)
    for k in range(5):
        x = (k - 2) * 0.035
        c.gem('jaw', f'jaw_crystal{k}', (x, -0.66, 0.55), (x * 2, -0.4, 1), 0.012, 0.045 + 0.01 * (k % 2), '#f0e0ff', '#8a50d0', mat='M_Clear', sides=4)
    c.gem('head', 'horn_crystal', (0, -0.62, 0.68), (0, -0.5, 1), 0.04, 0.2, '#f0e0ff', '#7a3ad0', mat='M_Clear', sides=5)
    for s in (-1, 1):
        c.gem('head', f'cheek_crystal{s}', (s * 0.12, -0.48, 0.66), (s, 0.4, 0.6), 0.025, 0.1, '#f0e0ff', '#7a3ad0', mat='M_Clear', sides=5)
    # legs: massive forelimbs, shorter hind legs
    for s, side in ((-1, 'R'), (1, 'L')):
        x = s * 0.2
        c.bone('leg.F' + side, (x, -0.22, 0.6), 'body')
        c.blob('leg.F' + side, (x * 1.05, -0.24, 0.52), (0.11, 0.13, 0.15), hide)
        c.limb('leg.F' + side, [(x * 1.05, -0.26, 0.4), (x * 1.05, -0.28, 0.22), (x * 1.05, -0.3, 0.08)], [0.09, 0.075, 0.08], hide)
        c.blob('leg.F' + side, (x * 1.05, -0.33, 0.04), (0.09, 0.1, 0.045), '#2a2038')
        for j in range(3):
            c.gem('leg.F' + side, f'claw{side}{j}', (x * 1.05 + (j - 1) * 0.04, -0.41, 0.03), (0, -1, 0.15), 0.014, 0.06, '#f0e0ff',
                  '#7a3ad0', mat='M_Clear', sides=4)
        c.bone('leg.B' + side, (x * 0.9, 0.32, 0.55), 'body')
        c.blob('leg.B' + side, (x * 0.95, 0.33, 0.44), (0.09, 0.13, 0.14), hide)
        c.limb('leg.B' + side, [(x * 0.95, 0.36, 0.3), (x * 0.95, 0.4, 0.16), (x * 0.95, 0.36, 0.07)], [0.07, 0.06, 0.065], hide)
        c.blob('leg.B' + side, (x * 0.95, 0.33, 0.035), (0.075, 0.09, 0.035), '#2a2038')
    c.bone('tail1', (0, 0.44, 0.55), 'body'); c.bone('tail2', (0, 0.6, 0.45), 'tail1')
    c.limb(['tail1', 'tail2'], [(0, 0.42, 0.55), (0, 0.58, 0.46), (0, 0.72, 0.36)], [0.1, 0.07, 0.04], hide)
    # crystal clusters: back ridge, shoulders, tail tip
    k = 0
    for (cx, cy, cz, n, h, b) in ((0, -0.2, 0.86, 5, 0.34, 'body'), (0.0, 0.05, 0.76, 4, 0.28, 'body'), (0.0, 0.26, 0.7, 3, 0.2, 'body'),
                                  (0.2, -0.2, 0.8, 3, 0.18, 'body'), (-0.2, -0.2, 0.8, 3, 0.18, 'body'), (0, 0.72, 0.38, 3, 0.16, 'tail2')):
        for j in range(n):
            a = TAU * j / n + k
            d = Vector((math.cos(a) * 0.45 + cx * 2.5, math.sin(a) * 0.35 + 0.15, 1)).normalized()
            hh = h * (1.0 if j == 0 else 0.62 + 0.15 * (j % 2))
            base = (cx + math.cos(a) * 0.03 * (j > 0), cy + math.sin(a) * 0.03 * (j > 0), cz - 0.02)
            c.gem(b, f'crystal{k}_{j}', base, d if j else Vector((cx * 1.5, 0.15, 1)), hh * 0.2, hh, '#f4e8ff', '#6a2ac0',
                  mat='M_Clear' if j % 2 == 0 else 'M_Emit', sides=6)
        k += 1
    return c.finish('quad')


# ---------------------------------------------------------------------------------------------- abyss_lord (final boss)
def abyss_lord(eid):
    """심연의 군주 — the final boss: a towering armoured demon king. Charcoal-violet skin, black plate armour with
    violet-lit seams and gold trim, layered spiked pauldrons, a demonic face with amber eyes under a heavy brow and
    fanged jaw, a crown of horns (two great swept-back horns ringed by a circlet of smaller ones), a vast cape of
    void — black shading to deep violet and flecked with stars — and a two-handed greatsword with a glowing fuller."""
    k = 2.35                                     # modelled at ~1.6 m, enlarged to ~3.8 m with the horns
    c = BossSculpt(eid, scale=k, tris=20000, ao=0.6)
    skin, plate, plate_hi, seam, gold = '#6a5478', '#2c2638', '#5a5070', '#b070ff', '#d8aa48'

    def armour(p):
        n = noise.noise(p * 10)
        return lerp_col(plate, plate_hi, 0.45 + 0.4 * n + (p.z - 0.9) * 0.4)
    c.bone('body', (0, 0, 0.82)); c.bone('head', (0, -0.02, 1.34), 'body'); c.bone('eyes', (0, -0.13, 1.44), 'head')
    c.bone('jaw', (0, -0.1, 1.37), 'head'); c.bone('crest', (0, 0, 1.52), 'head'); c.bone('cape', (0, 0.14, 1.28), 'body')
    # torso: broad chest and shoulders, narrower waist, heavy hips
    c.blob('body', (0, 0, 1.16), (0.25, 0.15, 0.15), armour)
    c.blob('body', (0, -0.01, 0.98), (0.17, 0.12, 0.12), armour)
    c.blob('body', (0, 0, 0.84), (0.2, 0.13, 0.09), armour)
    for s in (-1, 1):
        c.blob('body', (s * 0.2, 0, 1.2), (0.09, 0.09, 0.08), armour)
    cu = c.orb('body', 'cuirass', (0, -0.06, 1.12), (0.235, 0.135, 0.16), plate, seg=28, rings=14)
    A.apply_transform(cu)
    paint_fn(cu, lambda p: seam if abs(p.x) < 0.008 or abs(p.z - 1.05) < 0.006 else (gold if abs(p.z - 1.24) < 0.01 else armour(p)))
    c.add('body', A.sphere('core_gem', r=0.04, loc=(0, -0.19, 1.13), scale=(1, 0.5, 1.2), color='#d8a8ff', mat='M_Emit', seg=14, rings=8))
    c.ring('body', 'belt', (0, -0.01, 0.86), 0.205, 0.022, gold, scale=(1, 0.75, 1))
    for i in range(7):    # tassets
        a = math.radians(-90 + i * 30)
        c.chunk('body', f'tasset{i}', (0.21 * math.sin(a), -0.15 * math.cos(a), 0.74), (0.075, 0.025, 0.1), plate_hi, seed=i, jitter=0.03)
    c.membrane('body', 'loincloth', (0, -0.15, 0.86), [(-0.09, -0.15, 0.84), (-0.1, -0.17, 0.5), (-0.03, -0.18, 0.42), (0, -0.17, 0.46),
                                                        (0.03, -0.18, 0.42), (0.1, -0.17, 0.5), (0.09, -0.15, 0.84)], '#3a1a5a', thick=0.012,
               edge_color=gold)
    # head: demonic face, heavy brow, fanged jaw
    c.blob('head', (0, -0.01, 1.32), (0.06, 0.06, 0.07), skin)
    c.blob('head', (0, -0.04, 1.45), (0.095, 0.1, 0.1), skin)
    c.blob('head', (0, -0.1, 1.39), (0.07, 0.06, 0.055), skin)                                       # cheekbones/muzzle
    c.blob('eyes', (0, -0.115, 1.475), (0.09, 0.04, 0.028), skin)                                    # heavy brow
    for s in (-1, 1):
        c.eye('eyes', (s * 0.042, -0.112, 1.447), (s * 0.3, -1, 0.0), 0.021, '#ffb020', slit=True, sclera='#f0e0b0', pupil='#2a0a00')
        c.paint((s * 0.045, -0.135, 1.43), (0.02, 0.01, 0.03), '#2a1a30', weight=1.6)
    c.limb('jaw', [(0, -0.06, 1.36), (0, -0.12, 1.355), (0, -0.15, 1.36)], [0.06, 0.05, 0.035], skin)
    c.paint((0, -0.15, 1.38), (0.045, 0.02, 0.007), '#14081c', weight=1.8)
    for s in (-1, 1):
        spine(c, 'jaw', f'tusk{s}', (s * 0.03, -0.15, 1.37), (s * 0.2, -0.3, 1), 0.04, 0.009, '#efe6d0', tip='#ffffff', seg=6)
    # gorget and helm back
    c.ring('head', 'gorget', (0, -0.01, 1.31), 0.085, 0.022, plate_hi, scale=(1, 0.9, 1))
    c.blob('head', (0, 0.03, 1.49), (0.1, 0.09, 0.09), armour)
    # crown of horns
    for s in (-1, 1):
        horn(c, 'crest', f'great_horn{s}', (s * 0.08, -0.02, 1.53), (s * 0.26, 0.0, 1.66), (s * 0.24, 0.12, 1.86), 0.04, '#2a2232', '#e8d8ff', n=14)
    c.ring('crest', 'circlet', (0, -0.02, 1.53), 0.1, 0.014, gold, rot=(-8, 0, 0))
    for i in range(7):
        a = math.radians(-75 + 150 * i / 6)
        p = Vector((0.1 * math.sin(a), -0.02 - 0.1 * math.cos(a), 1.53))
        h = 0.13 if i == 3 else 0.09 - 0.012 * abs(i - 3)
        spine(c, 'crest', f'crown_horn{i}', tuple(p), (math.sin(a) * 0.3, -0.1 * math.cos(a), 1), h, 0.016, '#2a2232', tip='#c9a0ff', seg=6)
    c.add('crest', A.sphere('crown_gem', r=0.022, loc=(0, -0.125, 1.545), color='#d8a8ff', mat='M_Emit', seg=12, rings=7))
    # arms with spiked, layered pauldrons and clawed gauntlets
    for s, side in ((-1, 'R'), (1, 'L')):
        c.bone('arm.' + side, (s * 0.25, 0, 1.2), 'body')
        c.limb('arm.' + side, [(s * 0.26, 0, 1.2), (s * 0.33, -0.03, 1.02), (s * 0.35, -0.09, 0.88)], [0.08, 0.07, 0.066], skin)
        c.blob('arm.' + side, (s * 0.34, -0.07, 0.94), (0.075, 0.075, 0.09), armour)                 # gauntlet
        c.ring('arm.' + side, f'cuff{side}', (s * 0.34, -0.06, 0.99), 0.075, 0.014, gold, rot=(0, s * 15, 0))
        c.blob('arm.' + side, (s * 0.31, -0.02, 1.08), (0.075, 0.075, 0.06), plate_hi)               # couter
        c.blob('arm.' + side, (s * 0.355, -0.12, 0.83), (0.065, 0.065, 0.065), armour)
        for j in range(3):
            o = c.add('arm.' + side, dome(f'pauldron{side}{j}', (s * (0.29 + 0.025 * j), 0.0, 1.29 - 0.05 * j),
                                          (0.15 - 0.012 * j, 0.14 - 0.008 * j, 0.09), color=plate_hi if j == 0 else plate))
            paint_fn(o, lambda p, j=j, s=s: gold if p.z < 1.29 - 0.05 * j - 0.015 else (plate_hi if j == 0 else plate))
        for j in range(3):
            base = Vector((s * (0.3 + 0.04 * j), -0.03 + 0.04 * j, 1.37 - 0.02 * j))
            spine(c, 'arm.' + side, f'pauldron_spike{side}{j}', tuple(base), (s * 0.5, 0.1, 1), 0.14 - 0.03 * j, 0.025, '#2a2232',
                  tip='#c9a0ff', seg=6)
        c.bone('leg.' + side, (s * 0.11, 0, 0.78), 'body')
        c.limb('leg.' + side, [(s * 0.11, 0, 0.78), (s * 0.13, -0.02, 0.45), (s * 0.13, 0, 0.12)], [0.1, 0.085, 0.075], armour)
        c.blob('leg.' + side, (s * 0.13, -0.06, 0.45), (0.07, 0.05, 0.06), plate_hi)                # knee cop
        c.blob('leg.' + side, (s * 0.13, -0.07, 0.05), (0.085, 0.14, 0.055), plate)
        spine(c, 'leg.' + side, f'knee_spike{side}', (s * 0.13, -0.1, 0.46), (0, -1, 0.4), 0.07, 0.02, '#2a2232', tip='#c9a0ff', seg=6)
    # the void cape

    def void(p):
        col = lerp_col('#0c0814', '#4a1a7a', (1.3 - p.z) / 1.2)
        if p.z < 0.2:   # the hem burns violet
            col = lerp_col(col, '#9a50e0', (0.2 - p.z) / 0.15)
        return col
    cape_edge = [(-0.26, 0.08, 1.28), (-0.4, 0.2, 0.9), (-0.44, 0.3, 0.4), (-0.36, 0.36, 0.06), (-0.22, 0.34, 0.16), (-0.12, 0.38, 0.03),
                 (0.0, 0.36, 0.12), (0.12, 0.38, 0.03), (0.22, 0.34, 0.16), (0.36, 0.36, 0.06), (0.44, 0.3, 0.4), (0.4, 0.2, 0.9),
                 (0.26, 0.08, 1.28)]
    cp = c.membrane('cape', 'cape', (0, 0.14, 1.26), cape_edge, '#120c1e', thick=0.014)
    paint_fn(cp, void)
    c.ring('cape', 'cape_chain', (0, -0.02, 1.27), 0.2, 0.012, gold, rot=(-10, 0, 0), scale=(1, 0.7, 1))
    # two-handed greatsword, point down before him
    c.bone('weapon.R', (-0.355, -0.12, 0.83), 'arm.R')
    x, y = -0.355, -0.14
    c.tube('weapon.R', 'grip', [(x, y, 0.72), (x, y, 0.98)], 0.02, '#2a1a30')
    c.tube('weapon.R', 'guard', [(x - 0.16, y, 0.76), (x - 0.06, y, 0.72), (x, y, 0.71), (x + 0.06, y, 0.72), (x + 0.16, y, 0.76)], 0.024, gold)
    for s in (-1, 1):
        spine(c, 'weapon.R', f'guard_spike{s}', (x + s * 0.16, y, 0.76), (s, 0, 0.6), 0.08, 0.018, gold, tip='#fff0c0', seg=6)
    c.add('weapon.R', A.sphere('pommel_gem', r=0.03, loc=(x, y, 1.0), color='#d8a8ff', mat='M_Emit', seg=12, rings=7))
    blade(c, 'weapon.R', 'greatsword', (x, y, 0.71), 0.98, 0.14, '#2a2634', edge='#8a84a0', depth=0.026, axis=(0, 0, -1), tip_len=0.14)
    fuller = blade(c, 'weapon.R', 'fuller', (x, y - 0.0002, 0.69), 0.78, 0.04, '#c890ff', depth=0.03, axis=(0, 0, -1), mat='M_Emit', tip_len=0.1)
    c.follow['crest'] = 0.3
    c.arm_limit = (70, 26)
    return c.finish('heavy')


BUILDERS = {'void_eye': void_eye, 'shadow_beast': shadow_beast, 'chaos_spawn': chaos_spawn, 'gargoyle': gargoyle,
            'nightmare': nightmare, 'doppelganger': doppelganger, 'abyss_worm': abyss_worm, 'fallen_angel': fallen_angel,
            'void_reaper': void_reaper, 'crystal_horror': crystal_horror, 'abyss_lord': abyss_lord}

if __name__ == '__main__':
    eid = sys.argv[sys.argv.index('--') + 1]
    BUILDERS[eid](eid)
