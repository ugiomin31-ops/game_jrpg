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
from mathutils import Euler, Vector, noise  # noqa: E402

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
def _ring_point(center, R, rot, a):
    """Point at angle a on a ring of radius R (a torus lying in XY, turned by the Euler rot in degrees)."""
    m = Euler([math.radians(v) for v in rot]).to_matrix()
    return Vector(center) + m @ Vector((R * math.cos(a), R * math.sin(a), 0.0))


def void_eye(eid):
    """공허의 눈 — a floating star-orb guardian: a smooth violet crystal shell with a crown of small crystal points,
    one calm gem-like eye set in a crystal bezel, two rune rings orbiting the shell with glowing motes, and a skirt of
    flat ribbon fins trailing beneath it instead of tentacles."""
    c = Sculpt(eid, tris=4800, ao=0.45)
    deep, violet, lilac, teal = '#3a2a86', '#6a4cc8', '#cdbcf6', '#6ff0e0'
    C = Vector((0, 0, 0.86))
    E = Vector((0, -0.215, 0.86))                       # eye centre = blink pivot
    c.bone('body', tuple(C)); c.bone('eyes', tuple(E), 'body')
    c.bone('orbit1', tuple(C), 'body'); c.bone('orbit2', tuple(C), 'body')
    fins = [math.radians(30 + 72 * i) for i in range(5)]
    for i, a in enumerate(fins):
        c.bone(f'tentacle{i + 1}', (math.cos(a) * 0.19, math.sin(a) * 0.19, C.z - 0.14), 'body')

    def shell(p):
        t = (p.z - C.z) / 0.25                          # -1 underside .. +1 crown
        return lerp_col(lerp_col(deep, violet, (t + 0.7) / 1.4), lilac, max(0.0, t - 0.3) * 1.3)
    c.blob('body', tuple(C), (0.25, 0.25, 0.245), shell)
    # crystal bezel: a fused rim round the eye, so the eye sits in a socket of the shell
    for k in range(14):
        a = TAU * k / 14
        c.blob('body', tuple(E + Vector((math.cos(a) * 0.115, -0.03, math.sin(a) * 0.115))), (0.03, 0.03, 0.03), lilac)
    # a 1.6x eye: teal iris with a gold limbal ring and a bright glint, so it reads at battle distance
    eye = c.eye('eyes', tuple(E), (0, -1, 0), 0.096, '#3fd6c8', pupil='#14102a', sclera='#f6f2ff', iris_edge=0.6)
    for loop in eye.data.loops:
        d = (eye.data.vertices[loop.vertex_index].co - E).normalized()
        if 0.54 < d.dot(Vector((0, -1, 0))) <= 0.6:
            eye.data.color_attributes['Col'].data[loop.index].color_srgb = rgba('#e8c050')
    c.blob('eyes', tuple(E + Vector((0, -0.03, 0.085))), (0.105, 0.035, 0.025), deep)      # heavy calm lid
    # crown of crystal points on the crown and back of the shell (the eye side stays clear)
    crown = [d for d in fibo(48) if d.z > 0.35 and d.y > -0.1][:7]
    for k, d in enumerate(crown):
        if k % 3 == 0:
            c.gem('body', f'crown{k}', tuple(C + d * 0.21), d, 0.044, 0.16, teal, '#2aa8a0', mat='M_Emit', sides=5)
        else:
            c.gem('body', f'crown{k}', tuple(C + d * 0.21), d, 0.044, 0.16, '#f0eaff', '#7050d8', mat='M_Toon', sides=5)
    # two rune rings tilted in different planes: the Idle clip spins the orbit bones about Z
    c.ring('orbit1', 'rune_ring1', tuple(C), 0.40, 0.011, teal, rot=(66, 0, 0), mat='M_Emit')
    c.ring('orbit2', 'rune_ring2', tuple(C), 0.47, 0.012, lilac, rot=(66, 0, 90), mat='M_Toon')
    for k in range(3):
        c.orb('orbit1', f'rune1_{k}', tuple(_ring_point(C, 0.40, (66, 0, 0), TAU * k / 3)), (0.02, 0.02, 0.02), teal, 'M_Emit')
        c.orb('orbit2', f'rune2_{k}', tuple(_ring_point(C, 0.47, (66, 0, 90), TAU * (k + 0.5) / 3)), (0.018, 0.018, 0.018), teal, 'M_Emit')
    # ribbon fins: flat bands that flow out and down, each on its own sway bone
    for i, a in enumerate(fins):
        # a thin flared fin (sail-like membrane) fanning down from the shell; its frilled edge is teal
        ca, sa = math.cos(a), math.sin(a)
        out, side = Vector((ca, sa, 0)), Vector((-sa, ca, 0))
        root = Vector((ca * 0.16, sa * 0.16, C.z - 0.12))
        edge = []
        for k in range(9):      # a rounded petal hem: widest in the middle, curling slightly out at the bottom
            th = math.pi * k / 8
            edge.append(root + side * (0.14 * math.cos(th)) + Vector((0, 0, -0.05 - 0.2 * math.sin(th))) + out * (0.1 * math.sin(th)))
        c.membrane(f'tentacle{i + 1}', f'fin{i + 1}', tuple(root), [tuple(p) for p in edge], violet, thick=0.008, edge_color=teal)
    return c.finish('float')


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
    """혼돈의 촉수 — a chubby jelly imp that bounces on stubby legs: a soft lilac-to-violet body with teal spots, a
    round head with two small calm eyes under heavy lids, a closed smile with one small fang (no mouth hole), blush
    dots, two crystal horns and a few sparkle motes."""
    c = Sculpt(eid, tris=6200, ao=0.5)
    lilac, violet, deep, teal, blush = '#c8b4f4', '#8a5ad6', '#5a3aa8', '#48d8c8', '#ff9ac4'

    def skin(p):
        return lerp_col(lilac, violet, (p.z - 0.1) / 0.45)
    c.bone('body', (0, 0, 0.3)); c.bone('head', (0, -0.02, 0.6), 'body'); c.bone('eyes', (0, -0.2, 0.62), 'head')
    c.blob('body', (0, 0, 0.3), (0.3, 0.27, 0.22), skin)                              # chubby body
    c.blob('body', (0, 0, 0.45), (0.22, 0.2, 0.14), skin)                             # neck
    c.blob('head', (0, -0.02, 0.6), (0.25, 0.22, 0.2), skin)                          # round head
    for s, side in ((1, 'L'), (-1, 'R')):                                              # +X is the creature's left
        c.bone('arm.' + side, (s * 0.25, -0.02, 0.36), 'body')
        c.limb('arm.' + side, [(s * 0.25, -0.02, 0.36), (s * 0.32, -0.08, 0.3), (s * 0.36, -0.11, 0.25)], [0.07, 0.066, 0.06], skin)
        c.blob('arm.' + side, (s * 0.38, -0.12, 0.23), (0.078, 0.078, 0.072), skin)   # mitten hand
        c.bone('leg.' + side, (s * 0.13, 0.0, 0.16), 'body')
        c.limb('leg.' + side, [(s * 0.13, 0.0, 0.16), (s * 0.15, -0.04, 0.08), (s * 0.15, -0.06, 0.05)], [0.085, 0.075, 0.075], skin)
        c.blob('leg.' + side, (s * 0.15, -0.09, 0.055), (0.095, 0.12, 0.06), deep)    # round foot
    for s in (1, -1):                                                                  # crystal horns
        c.gem('head', f'horn{s}', (s * 0.12, 0.0, 0.78), (s * 0.4, 0.25, 1), 0.06, 0.26, '#e6fbff', '#3ab8d8', mat='M_Toon', sides=5)
    for s in (1, -1):                                                                  # small calm eyes under light lids
        c.eye('eyes', (s * 0.085, -0.205, 0.62), (s * 0.12, -1, 0.05), 0.048, '#2fc7c0', pupil='#1a1030', sclera='#f8f4ff',
              iris_edge=0.6)
        c.blob('head', (s * 0.085, -0.2, 0.675), (0.05, 0.035, 0.015), violet)
    for k in range(7):                                                                 # closed smile, painted (no mouth hole)
        t = -1 + k / 3
        c.paint((0.07 * t, -0.244, 0.54 + 0.035 * t * t), (0.018, 0.024, 0.016), '#20082e', weight=3.0)
    spine(c, 'head', 'fang', (0.03, -0.245, 0.548), (0.0, -0.1, -1), 0.03, 0.011, '#fbf8ff', tip='#ffffff', seg=6)
    for s in (1, -1):                                                                  # blush dots
        c.paint((s * 0.14, -0.2, 0.57), (0.03, 0.035, 0.025), blush, weight=1.6)
    for n, p in enumerate(((0.3, -0.1, 0.84), (-0.32, -0.04, 0.72), (0.0, 0.26, 0.94))):   # sparkle motes
        c.orb('head', f'mote{n}', p, (0.016, 0.016, 0.016), '#8ffff0', 'M_Emit')
    return c.finish('hop')


# ---------------------------------------------------------------------------------------------- gargoyle
def _patina(up=0.6, seed=0.0):
    """post-paint for weathered stone: moss on up-facing ledges, verdigris-teal patina in patches."""
    def f(p, n, col):
        k = (n.z - up) / (1 - up)
        if k > 0:
            m = 0.5 + 0.5 * noise.noise(p * 7 + Vector((seed, 0.0, 1.0)))
            col = lerp_col(col, '#6f9a5a', min(0.7, 1.5 * k * m))
        if noise.noise(p * 5 + Vector((4.0, 2.0, seed))) > 0.5:
            col = lerp_col(col, '#4fb3a8', 0.4)
        return col
    return f


def gargoyle(eid):
    """가고일 — a friendly-tough stone-dragon gargoyle: a chunky carved body in lavender-grey stone with a bold chest
    plate and a ridge of stone spines, moss and teal patina in the creases, a glowing rune crack on the plate, a broad
    blunt head with small horns and round amber eyes, and big bat wings with a teal-lit membrane and bone fingers."""
    from flyers import bat_wing
    c = Sculpt(eid, tris=5000, ao=0.4)
    c.post = _patina(0.6)
    base_stone = stone_col('#c2bcdc', '#7a769e', None, 3.0)

    def stone(p):   # weathered stone with fine cracks
        if abs(noise.noise(p * 6 + Vector((0.3, 1.1, 2.0)))) < 0.03:
            return '#5c5880'
        return base_stone(p)
    plate, dark, claw, ridge, glow = '#cfcae4', '#5a5680', '#2e2c40', '#8c86ae', '#5ef2e0'
    c.bone('body', (0, 0, 0.98)); c.bone('head', (0, -0.1, 1.22), 'body'); c.bone('eyes', (0, -0.23, 1.27), 'head')
    c.bone('jaw', (0, -0.2, 1.14), 'head')
    # body: barrel chest, heavy belly, hips, shoulder balls
    c.blob('body', (0, -0.01, 1.02), (0.23, 0.18, 0.23), stone)
    c.blob('body', (0, 0.02, 0.84), (0.2, 0.17, 0.15), stone)
    c.blob('body', (0, 0.05, 0.72), (0.15, 0.13, 0.09), stone)
    c.blob('body', (0, -0.04, 1.15), (0.18, 0.14, 0.1), stone)
    for s in (-1, 1):
        c.blob('body', (s * 0.19, 0.0, 1.1), (0.11, 0.11, 0.11), stone)
    # a lighter stone chest plate with a glowing rune crack
    PC, PR = (0, -0.17, 1.03), (0.19, 0.085, 0.18)
    c.add('body', dome('chest_plate', PC, PR, cut=-0.25, color=plate))
    rune = [tuple(ellipsoid_point(PC, PR, Vector(d), out=0.012)[0])
            for d in ((-0.6, -1, 0.7), (-0.25, -1, 0.05), (0.2, -1, 0.6), (0.52, -1, -0.05))]
    c.tube('body', 'rune_chest', rune, 0.012, glow, mat='M_Emit')
    # a crest of stone spines down the back
    for k in range(5):
        spine(c, 'body', f'ridge{k}', (0, 0.12 + 0.01 * k, 1.2 - k * 0.1), (0, 0.6, 1), 0.075 - 0.008 * k, 0.03 - 0.002 * k,
              ridge, tip=plate)
    # head: broad skull, short snout, closed snarl with two little fangs
    c.blob('head', (0, -0.1, 1.24), (0.14, 0.13, 0.13), stone)
    c.limb('head', [(0, -0.12, 1.2), (0, -0.2, 1.18), (0, -0.25, 1.17)], [0.07, 0.06, 0.05], stone)
    c.blob('head', (0, -0.27, 1.16), (0.055, 0.045, 0.045), stone)
    c.limb('jaw', [(0, -0.14, 1.14), (0, -0.2, 1.13), (0, -0.25, 1.14)], [0.05, 0.042, 0.035], stone)
    c.paint((0, -0.27, 1.13), (0.04, 0.02, 0.008), '#2a2638', weight=1.6)
    for s in (-1, 1):
        side = 'L' if s > 0 else 'R'
        c.blob('eyes', (s * 0.065, -0.2, 1.27), (0.05, 0.035, 0.03), stone)                     # brow ridge
        c.paint((s * 0.035, -0.3, 1.18), (0.012, 0.012, 0.012), dark, weight=2)                  # nostrils
        spine(c, 'jaw', f'fang{s}', (s * 0.035, -0.25, 1.15), (s * 0.1, -0.1, 1), 0.035, 0.009, '#f2ecdc', tip='#ffffff', seg=6)
        c.eye('eyes', (s * 0.07, -0.225, 1.24), (s * 0.2, -1, 0.1), 0.032, '#ffb84a', sclera='#f4efe0')
        horn(c, 'head', f'horn{s}', (s * 0.08, -0.04, 1.32), (s * 0.13, 0.02, 1.42), (s * 0.12, 0.12, 1.44), 0.026, '#d8d2e6', '#8c86ae')
        c.bone('ear.' + side, (s * 0.1, -0.07, 1.27), 'head')
        c.blob('ear.' + side, (s * 0.13, -0.06, 1.28), (0.05, 0.012, 0.025), stone, rot=(0, -s * 25, s * 20))
    # arms with fists and claws, stubby legs with talons
    for s, side in ((-1, 'R'), (1, 'L')):
        c.bone('arm.' + side, (s * 0.18, -0.02, 1.1), 'body')
        c.limb('arm.' + side, [(s * 0.19, -0.02, 1.1), (s * 0.26, -0.06, 0.95), (s * 0.27, -0.12, 0.8)], [0.075, 0.065, 0.055], stone)
        c.blob('arm.' + side, (s * 0.27, -0.16, 0.75), (0.065, 0.065, 0.06), stone)
        for j in range(3):
            spine(c, 'arm.' + side, f'claw{side}{j}', (s * 0.27 + (j - 1) * 0.03, -0.2, 0.72), (0, -0.6, -1), 0.045, 0.011, claw, seg=6)
        c.bone('leg.' + side, (s * 0.12, 0.0, 0.85), 'body')
        c.blob('leg.' + side, (s * 0.13, 0.0, 0.8), (0.085, 0.1, 0.09), stone)
        c.limb('leg.' + side, [(s * 0.13, -0.02, 0.74), (s * 0.14, -0.06, 0.6), (s * 0.13, -0.08, 0.5)], [0.075, 0.06, 0.055], stone)
        c.blob('leg.' + side, (s * 0.13, -0.11, 0.46), (0.07, 0.11, 0.05), stone)
        for j in range(3):
            spine(c, 'leg.' + side, f'talon{side}{j}', (s * 0.13 + (j - 1) * 0.03, -0.17, 0.44), (0, -1, -0.4), 0.045, 0.011, claw, seg=6)
        # big bat wing: four-point membrane with teal-lit scalloped edge
        c.bone('wing.' + side, (s * 0.12, 0.07, 1.14), 'body')
        bat_wing(c, 'wing.' + side, s, (s * 0.14, 0.08, 1.14), (s * 0.6, 0.12, 1.3),
                 [(s * 0.98, 0.14, 1.32), (s * 1.06, 0.16, 1.02), (s * 0.82, 0.18, 0.74)], (s * 0.14, 0.14, 0.78),
                 (s * 0.36, 0.13, 1.0), '#a8a2c8', '#5a80a8', '#9ff5e6', r=0.045)
    # tail with a spade tip
    c.bone('tail1', (0, 0.14, 0.82), 'body'); c.bone('tail2', (0, 0.3, 0.66), 'tail1')
    c.limb(['tail1', 'tail1', 'tail2'], [(0, 0.12, 0.84), (0, 0.24, 0.74), (0.02, 0.34, 0.6), (0.04, 0.42, 0.5)],
           [0.07, 0.05, 0.035, 0.025], stone)
    sp = A.extrude_shape('tail_spade', [(0, 0), (0.07, 0.06), (0.04, 0.08), (0, 0.16), (-0.04, 0.08), (-0.07, 0.06)], depth=0.025,
                         color=ridge)
    sp.rotation_mode = 'QUATERNION'
    sp.rotation_quaternion = Vector((0.15, 0.5, -0.6)).to_track_quat('Z', 'Y')
    sp.location = (0.05, 0.44, 0.48)
    c.add('tail2', sp)
    return c.finish('fly')


# ---------------------------------------------------------------------------------------------- nightmare
def _tongue(c, bone, name, base, direction, length, r, outer, inner, seg=10):
    """Two-layer violet star-flame tongue aimed along direction (it can stream back or hang), emissive."""
    prof = [(0.0, -r * 0.4), (r * 0.8, 0.0), (r, length * 0.18), (r * 0.7, length * 0.5), (r * 0.25, length * 0.82), (0.0, length)]
    q = Vector(direction).normalized().to_track_quat('Z', 'Y')
    for nm, pr, col in ((name, prof, outer), (name + '_in', [(x * 0.55, z * 0.72) for x, z in prof], inner)):
        ob = A.lathe(nm, pr, color=col, mat='M_Emit', seg=seg)
        ob.rotation_mode = 'QUATERNION'
        ob.rotation_quaternion = q
        ob.location = tuple(base)
        c.add(bone, ob)


def _crescent_pts(R=0.05, n=8):
    """Crescent moon outline in the (x, z) plane: an outer arc on the left and a shallower inner arc back."""
    outer = [(R * math.cos(math.radians(a)), R * math.sin(math.radians(a))) for a in range(90, 271, 180 // n)]
    inner = [(0.45 * R + 0.75 * R * math.cos(math.radians(a)), 0.75 * R * math.sin(math.radians(a)))
             for a in range(270, 89, -180 // n)]
    return outer + inner


def nightmare(eid):
    """나이트메어 — a dream steed: a sturdy star-speckled violet horse with a lighter belly and muzzle, muscular legs
    ending in tapered hooves with flame-wisps at the fetlocks, a long crescent horn and a forelock of star-flame, a
    flowing mane of violet-to-pink flame ribbons along the crest, a long flowing flame tail, and a saddle blanket
    with gold crescent emblems on each flank."""
    c = Sculpt(eid, tris=3000, ao=0.4)
    coat, belly, muzzle_c, hoof, eyec = '#8478d8', '#c4bcf4', '#dcd4ff', '#5a4fa8', '#b8a8ff'
    blanket, gold = '#a0408e', '#e8b84c'
    fl_out, fl_in = '#b064ff', '#ffd6ff'

    def hide(p):   # lighter belly, a pale muzzle, violet elsewhere
        under = min(1.0, max(0.0, (0.66 - p.z) * 4.0))
        nose = min(1.0, max(0.0, (-0.6 - p.y) * 5.0)) if p.z < 1.12 else 0.0
        return lerp_col(lerp_col(coat, belly, under), muzzle_c, nose)

    def stars(p, n, col):   # soft, larger star speckles that still read at battle distance
        if noise.noise(p * 11 + Vector((1.3, 0.2, 2.5))) > 0.42 and n.z > -0.5:
            return lerp_col(col, '#f2ecff', 0.8)
        return col
    c.post = stars
    c.bone('body', (0, 0.05, 0.7))
    c.bone('head', (0, -0.36, 1.0), 'body'); c.bone('eyes', (0, -0.52, 1.2), 'head'); c.bone('jaw', (0, -0.6, 1.02), 'head')
    c.bone('flame_mane', (0, -0.3, 1.0), 'body'); c.bone('flame_tail', (0, 0.4, 0.8), 'body')
    # barrel, deep chest, round croup, withers and belly
    c.blob('body', (0, -0.22, 0.7), (0.16, 0.14, 0.2), hide)
    c.blob('body', (0, 0.0, 0.7), (0.165, 0.27, 0.19), hide)
    c.blob('body', (0, 0.3, 0.74), (0.15, 0.13, 0.17), hide)
    c.blob('body', (0, -0.15, 0.9), (0.13, 0.13, 0.1), hide)
    c.blob('body', (0, 0.02, 0.52), (0.14, 0.24, 0.07), hide)
    # arching neck and a long head with a pale muzzle
    c.limb(['body', 'body', 'head', 'head'], [(0, -0.22, 0.84), (0, -0.3, 0.98), (0, -0.37, 1.1), (0, -0.42, 1.2)],
           [0.15, 0.125, 0.105, 0.09], hide)
    c.blob('head', (0, -0.45, 1.2), (0.085, 0.095, 0.09), hide)
    c.limb('head', [(0, -0.5, 1.17), (0, -0.6, 1.1), (0, -0.72, 1.06)], [0.07, 0.058, 0.05], hide)
    c.blob('head', (0, -0.77, 1.04), (0.055, 0.06, 0.05), hide)
    c.limb('jaw', [(0, -0.6, 1.06), (0, -0.68, 1.03), (0, -0.73, 1.04)], [0.048, 0.042, 0.04], hide)
    c.blob('eyes', (0, -0.52, 1.25), (0.075, 0.04, 0.03), hide)                                    # brow
    for s in (-1, 1):
        c.paint((s * 0.025, -0.8, 1.04), (0.01, 0.012, 0.01), '#2a1a48', weight=2.0)             # nostril
        c.eye('eyes', (s * 0.055, -0.56, 1.205), (s * 0.4, -1, 0.1), 0.022, eyec, sclera='#f1edff', pupil='#1a1230')
        c.bone('ear.' + ('L' if s > 0 else 'R'), (s * 0.04, -0.44, 1.27), 'head')
        c.blob('ear.' + ('L' if s > 0 else 'R'), (s * 0.05, -0.44, 1.31), (0.022, 0.014, 0.055), hide, rot=(0, -s * 12, 0))
    # crescent horn arcing forward over the brow
    horn(c, 'head', 'horn', (0, -0.56, 1.28), (0, -0.64, 1.38), (0, -0.54, 1.45), 0.022, '#eee6ff', '#b898ff')
    # saddle blanket (colour over the back) with a gold crescent emblem on each flank
    c.paint((0, 0.0, 0.84), (0.2, 0.3, 0.05), blanket, weight=1.2)
    for s in (-1, 1):
        c.add('body', A.extrude_shape(f'crest{s:+d}', _crescent_pts(0.065), depth=0.014, loc=(s * 0.178, 0.0, 0.74),
                                      rot=(0, 0, 90), color=gold, mat='M_Toon'))
    # four legs: muscular forearms and gaskins, slim cannons, tapered hooves with flat soles, fetlock flame-wisps
    for s, side in ((-1, 'R'), (1, 'L')):
        x = s * 0.1
        c.bone('leg.F' + side, (x, -0.22, 0.66), 'body')
        c.blob('leg.F' + side, (x, -0.22, 0.6), (0.09, 0.1, 0.13), hide)
        c.limb('leg.F' + side, [(x, -0.23, 0.5), (x, -0.235, 0.36), (x, -0.24, 0.16)], [0.06, 0.042, 0.034], hide)
        c.blob('leg.F' + side, (x, -0.24, 0.13), (0.04, 0.044, 0.034), hide)                    # fetlock
        c.add('leg.F' + side, A.cyl('hoof_F' + side, r=0.046, depth=0.07, loc=(x, -0.25, 0.035), r2=0.035, color=hoof,
                                   mat='M_Toon', seg=12))
        _tongue(c, 'leg.F' + side, 'fetlock_F' + side, (x, -0.25, 0.1), (0, 0.5, -1), 0.11, 0.03, fl_out, fl_in, seg=8)
        c.bone('leg.B' + side, (x * 1.1, 0.3, 0.7), 'body')
        c.blob('leg.B' + side, (x * 1.1, 0.3, 0.62), (0.1, 0.13, 0.14), hide)
        c.limb('leg.B' + side, [(x, 0.33, 0.52), (x, 0.36, 0.34), (x, 0.335, 0.12)], [0.062, 0.046, 0.034], hide)
        c.blob('leg.B' + side, (x, 0.34, 0.31), (0.05, 0.055, 0.05), hide)                      # hock
        c.blob('leg.B' + side, (x, 0.335, 0.11), (0.04, 0.044, 0.034), hide)                    # fetlock
        c.add('leg.B' + side, A.cyl('hoof_B' + side, r=0.046, depth=0.07, loc=(x, 0.33, 0.035), r2=0.035, color=hoof,
                                   mat='M_Toon', seg=12))
        _tongue(c, 'leg.B' + side, 'fetlock_B' + side, (x, 0.33, 0.1), (0, 0.5, -1), 0.11, 0.03, fl_out, fl_in, seg=8)
    # mane: eight star-flame ribbons down the whole neck crest, violet at the poll fading to pink at the withers
    for j in range(10):
        t = j / 9
        base = Vector((0, -0.42, 1.2)).lerp(Vector((0, -0.2, 0.98)), t)
        outer, inner = lerp_col(fl_out, '#ff70e0', t), lerp_col('#e0c0ff', '#fff0ff', t)
        side = 1 if j % 2 else -1     # alternate sides so the ribbons separate into flowing tongues
        _tongue(c, 'flame_mane', f'mane{j}', tuple(base + Vector((side * 0.03, 0.0, 0.0))),
                (side * 0.45, 0.9, 0.35 - 0.2 * t), (0.5 if j % 3 else 0.36) - 0.1 * t,
                0.1 - 0.02 * t, outer, inner, seg=8)
    # forelock: two ribbons falling forward over the brow
    for s in (-1, 1):
        _tongue(c, 'flame_mane', f'forelock{s:+d}', (s * 0.02, -0.5, 1.3), (s * 0.25, -0.85, -0.35), 0.2, 0.035,
                fl_out, fl_in, seg=8)
    # long flame tail streaming back and down, fanned so it reads from the front three-quarter view
    for k, (dx, dz, L) in enumerate(((-0.14, -0.15, 0.8), (-0.07, -0.45, 0.9), (0.0, -0.7, 0.86),
                                     (0.07, -0.5, 0.92), (0.14, -0.2, 0.78))):
        _tongue(c, 'flame_tail', f'tail_flame{k}', (dx * 0.4, 0.4, 0.8), (dx * 1.8, 0.7, dz), L, 0.08, fl_out, fl_in, seg=8)
    for k, p in enumerate(((-0.22, -0.44, 1.36), (0.2, -0.5, 1.34), (0.0, -0.1, 1.42))):
        c.gem('flame_mane', f'star{k}', p, (0, 0, 1), 0.02, 0.075, '#f4e8ff', '#9a70ff', mat='M_Emit', sides=4)
    return c.finish('quad')


# ---------------------------------------------------------------------------------------------- doppelganger
def doppelganger(eid):
    """도플갱어 — a mirror-mask phantom duelist that copies the heroes: a heroic, slim-waisted figure in a long
    high-collared violet coat with gold trim, three flowing coat-tails sculpted into the body, a porcelain mirror mask
    with one glowing crescent crack and a violet hood with a plume, a gold belt set with the four heroes' gems, a
    gold pauldron, and a rapier with a cup guard; mirror-glass motes orbit it."""
    c = Sculpt(eid, tris=5600, ao=0.4)
    violet, lav_hi, gold, dark_v = '#8a64e0', '#d2c4f8', '#e0b04a', '#5a3fb0'
    legs, boot, glove, porcelain = '#5a4aa8', '#6a50b8', '#4a3a92', '#d8d0f4'
    glass, tail_c = '#e6e8ff', '#7a58d4'

    def hem(p):   # coat-tails: solid violet, with a lavender edge only at the very hem
        return lerp_col(tail_c, lav_hi, min(0.6, max(0.0, (0.2 - p.z) * 5.0)))

    def face(p):  # porcelain at the front of the head, violet hood at the back
        return lerp_col(porcelain, violet, min(1.0, max(0.0, (p.y + 0.02) / 0.05)))
    c.bone('body', (0, 0, 0.62)); c.bone('head', (0, -0.01, 1.1), 'body')
    c.bone('tail1', (0, 0.04, 0.62), 'body'); c.bone('tail2', (0.12, 0.02, 0.62), 'body'); c.bone('tail3', (-0.12, 0.02, 0.62), 'body')
    # heroic torso: broad shoulders, tapered waist, long coat skirt
    c.blob('body', (0, 0, 0.98), (0.15, 0.1, 0.12), violet)
    c.blob('body', (0, 0, 0.8), (0.11, 0.085, 0.09), violet)
    c.blob('body', (0, 0, 0.66), (0.135, 0.095, 0.08), violet)
    for s in (-1, 1):
        c.blob('body', (s * 0.18, 0, 1.0), (0.07, 0.07, 0.07), violet)
    c.blob('body', (0, 0, 0.74), (0.12, 0.09, 0.03), gold)                                   # gold belt band
    c.blob('body', (0, 0, 0.5), (0.125, 0.09, 0.08), violet)                                 # coat skirt
    for k in range(8):                                                                       # high gold collar ring
        a = TAU * k / 8
        c.blob('body', (math.cos(a) * 0.075, math.sin(a) * 0.065, 1.02), (0.03, 0.03, 0.04), gold)
    for z in (0.92, 0.84):                                                                   # gold buttons down the front
        c.blob('body', (0, -0.1, z), (0.013, 0.013, 0.013), gold)
    # three coat-tails sculpted into the body and weighted to the spine (centre) and hips (sides)
    for bone, x0, x1, y0, y1 in (('tail1', 0.0, 0.0, 0.06, 0.22), ('tail2', 0.1, 0.19, 0.04, 0.18),
                                 ('tail3', -0.1, -0.19, 0.04, 0.18)):
        for k in range(8):   # a dense run of flattened masses: one continuous cloth-like tail per bone
            t = k / 7
            p = (x0 + (x1 - x0) * t, y0 + (y1 - y0) * t, 0.58 - 0.3 * t)
            w = 0.055 + 0.02 * t
            c.blob(bone, p, (w, 0.03, 0.09), hem)
    # head: porcelain mask over the skull, a violet hood behind it and a plume rising from the crown
    c.blob('head', (0, -0.01, 1.2), (0.1, 0.095, 0.12), face)
    c.blob('head', (0, 0.035, 1.25), (0.1, 0.085, 0.09), violet)
    # one glowing crescent crack across the mask (emissive, a single line)
    crack = [tuple(ellipsoid_point((0, -0.01, 1.2), (0.1, 0.095, 0.12),
                                   Vector((0.07 * math.cos(math.radians(a)) / 0.1, -1.0,
                                           (1.2 + 0.07 * math.sin(math.radians(a)) - 1.2) / 0.12)), out=0.004)[0])
             for a in range(-40, 121, 10)]
    c.tube('head', 'mask_crack', crack, 0.009, '#f0e0ff', mat='M_Emit')
    c.add('head', A.torus('circlet', R=0.088, r=0.013, loc=(0, -0.01, 1.27), scale=(1.05, 1.0, 1.0), color=gold, seg=24, minor=8))
    # arms: sleeves, gold cuffs and dark gloves; legs in leggings with boots and gold cuffs
    for s, side in ((-1, 'R'), (1, 'L')):
        c.bone('arm.' + side, (s * 0.14, 0, 0.95), 'body')
        c.limb('arm.' + side, [(s * 0.18, 0, 0.98), (s * 0.23, -0.03, 0.83), (s * 0.26, -0.07, 0.7)], [0.055, 0.045, 0.04], violet)
        c.paint((s * 0.265, -0.09, 0.67), (0.035, 0.035, 0.035), gold, weight=1.6)
        c.blob('arm.' + side, (s * 0.27, -0.1, 0.64), (0.04, 0.04, 0.045), glove)
        c.bone('leg.' + side, (s * 0.085, 0, 0.6), 'body')
        c.limb('leg.' + side, [(s * 0.085, 0, 0.6), (s * 0.09, -0.01, 0.34), (s * 0.09, 0, 0.1)], [0.06, 0.045, 0.04], legs)
        c.blob('leg.' + side, (s * 0.09, -0.035, 0.06), (0.05, 0.085, 0.05), boot)
        c.paint((s * 0.09, -0.06, 0.13), (0.055, 0.035, 0.02), gold, weight=1.6)              # boot cuff
    # one gold pauldron on the left shoulder
    c.add('body', dome('pauldron', (0.2, 0.0, 1.07), (0.085, 0.085, 0.05), cut=-0.25, color=gold))
    # rapier in the right hand: grip, cup guard, a long thin silver blade pointing forward and up
    hand = Vector((-0.27, -0.09, 0.66))
    d = Vector((0.12, -0.9, 0.34)).normalized()
    c.bone('weapon.R', tuple(hand), 'arm.R')
    c.tube('weapon.R', 'grip', [tuple(hand - d * 0.1), tuple(hand)], 0.012, dark_v)
    c.disc('weapon.R', 'guard', tuple(hand), d, (0.06, 0.018, 0.06), gold)
    c.disc('weapon.R', 'cup', tuple(hand + d * 0.03), d, (0.04, 0.02, 0.04), gold)
    blade(c, 'weapon.R', 'rapier', tuple(hand), 0.72, 0.022, '#e8e4ff', edge='#c8a8ff', depth=0.008, axis=tuple(d), tip_len=0.3)
    # mirror-glass motes orbiting on a spinning bone, plus three small violet embers
    c.bone('orbit', (0, 0, 1.0), 'body')
    for k in range(6):
        a = TAU * k / 6 + 0.3
        p = (math.cos(a) * 0.34, math.sin(a) * 0.34, 1.02 + 0.22 * math.sin(a * 2.0))
        c.gem('orbit', f'mote{k}', p, (math.cos(a), math.sin(a), 0.35), 0.02, 0.085, glass, '#8e82d0', mat='M_Clear', sides=4)
    for k in range(3):
        a = TAU * k / 3 + 1.1
        c.gem('orbit', f'ember{k}', (math.cos(a) * 0.24, math.sin(a) * 0.24, 1.36 - 0.1 * k), (0, 0, 1), 0.012, 0.04,
              '#f4e8ff', '#8a50ff', mat='M_Emit', sides=4)
    # belt gems: one in each hero's colour (warrior, archer, mage, cleric)
    for k, (col, dark) in enumerate((('#c0622e', '#7a3a1c'), ('#4fae5a', '#2a6a34'), ('#358ed4', '#1f5a94'), ('#e88aa8', '#9a4a68'))):
        c.gem('body', f'belt_gem{k}', (-0.075 + 0.05 * k, -0.115, 0.745), (0, -1, 0.1), 0.014, 0.03, col, dark, mat='M_Toon', sides=5)
    c.arm_limit = (80, 30)
    return c.finish('biped')


# ---------------------------------------------------------------------------------------------- abyss_worm
def abyss_worm(eid):
    """심연 벌레 — a segmented armoured worm rearing out of a sand mound: rounded violet plates over a pale blue belly,
    dark grooves between them, crystal spines down its back, and a beetle-like helmeted head with a crystal crest,
    two small eyes under the brim and a pair of closed pincer mandibles."""
    c = Sculpt(eid, tris=6000, ao=0.55)
    plate, dark, belly, helm = '#7a5cc8', '#2a2468', '#9fb8e0', '#4a3a98'
    band = '#3a2e84'
    c.bone('body', (0, 0.0, 0.35)); c.bone('head', (0, -0.1, 0.85), 'body')
    c.bone('jaw', (0, -0.3, 0.98), 'head'); c.bone('eyes', (0, -0.37, 0.965), 'head')
    # the arching body: a row of rounded plates, each with a dark groove after it
    path = [Vector(p) for p in bezier((0, 0.14, -0.05), (0, 0.12, 1.1), (0, -0.3, 1.08), 26)]
    radii = [0.19 + 0.02 * math.sin(math.pi * i / 26) for i in range(27)]
    for i, (p, r) in enumerate(zip(path, radii)):
        if i > 21:      # the arch ends inside the helmet; past this point the plates would bury the face
            break
        b = 'root' if p.z < 0.25 else 'body' if p.z < 0.8 else 'head'
        t = (path[min(i + 1, 26)] - path[max(i - 1, 0)]).normalized()
        rot = [math.degrees(v) for v in t.to_track_quat('Z', 'Y').to_euler()]
        if i % 3 == 0:
            # the belly tint stays a minority so the plates keep their violet banding
            col = lambda q, p=p: lerp_col(plate, belly, min(0.4, max(0.0, -(q.y - p.y) / 0.13 - 0.15)))  # noqa: E731
            c.blob(b, tuple(p), (r * 1.2, r * 1.2, r * 0.62), col, rot=rot, stiff=3.0)
            if i in (3, 9, 15, 21):   # four larger crystal spines down the back (dorsal = +Y on the rising body, +Z over the top)
                dorsal = Vector((0, t.z, -t.y)).normalized()
                c.gem(b, f'spine{i}', tuple(p + dorsal * r * 0.7), dorsal, 0.06, 0.26, '#d8f8ff', '#3a8ec8', mat='M_Toon', sides=5)
        else:   # a deep indigo band between the plates
            c.blob(b, tuple(p), (r * 0.84, r * 0.84, r * 0.4), band, rot=rot)
    # helmeted head: a domed beetle shell, a brow lip, a crystal crest, and eyes tucked under the brim
    c.blob('head', (0, -0.14, 0.98), (0.23, 0.25, 0.19), helm)
    c.blob('head', (0, -0.31, 1.05), (0.19, 0.05, 0.035), dark)
    c.blob('head', (0, -0.05, 1.14), (0.05, 0.15, 0.03), dark)
    c.gem('head', 'crest_crystal', (0, -0.14, 1.13), (0, -0.3, 1), 0.05, 0.24, '#e6fbff', '#3a8ec8', mat='M_Toon', sides=5)
    for s in (-1, 1):   # beetle eyes just proud of the helmet, with a bright glint
        c.eye('eyes', (s * 0.1, -0.37, 0.965), (s * 0.25, -1, 0.1), 0.042, '#7ff0e0', pupil='#14102a', sclera='#f4f8ff',
              iris_edge=0.6)
    # two curved pincers at the sides of the jaw, pointing forward and inward, tips crossing slightly
    for s in (-1, 1):
        c.limb('jaw', [(s * 0.13, -0.24, 0.74), (s * 0.12, -0.4, 0.7), (s * 0.07, -0.5, 0.7), (-s * 0.01, -0.52, 0.74)],
               [0.036, 0.03, 0.024, 0.016], lambda q: lerp_col('#2e2470', '#3a2e80', (-q.y - 0.4) / 0.16))
    # a low sand mound round the hole
    for k in range(7):
        a = TAU * k / 7
        r = 0.3 + 0.04 * (k % 2)
        c.chunk('root', f'mound{k}', (r * math.cos(a), 0.14 + r * math.sin(a), 0.05), (0.09, 0.07, 0.06 + 0.02 * (k % 3)),
                '#6a5a98', seed=k + 3, jitter=0.15)

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
    violet-lit seams and gold trim, layered spiked pauldrons, a horned great helm whose T-visor burns with two amber eye-lights, a crown of horns (two great swept-back horns ringed by a circlet of smaller ones), a vast cape of
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
    c.ring('body', 'belt', (0, -0.01, 0.86), 0.205, 0.014, gold, scale=(1, 0.75, 1))
    for i in range(7):    # tassets
        a = math.radians(-90 + i * 30)
        c.chunk('body', f'tasset{i}', (0.21 * math.sin(a), -0.15 * math.cos(a), 0.74), (0.075, 0.025, 0.1), plate_hi, seed=i, jitter=0.03)
    c.membrane('body', 'loincloth', (0, -0.15, 0.86), [(-0.09, -0.15, 0.84), (-0.1, -0.17, 0.5), (-0.03, -0.18, 0.42), (0, -0.17, 0.46),
                                                        (0.03, -0.18, 0.42), (0.1, -0.17, 0.5), (0.09, -0.15, 0.84)], '#3a1a5a', thick=0.012,
               edge_color=gold)
    # head: a horned great helm with a T-visor; two amber eye-lights burn in the dark slit
    c.blob('head', (0, -0.01, 1.32), (0.065, 0.065, 0.07), skin)                                     # neck
    for s in (-1, 1):                                                                                # high collar
        c.blob('body', (s * 0.09, 0.0, 1.3), (0.07, 0.08, 0.07), armour)
    c.blob('body', (0, 0.06, 1.31), (0.11, 0.06, 0.07), armour)
    helm = lathe_helm(c, 'head', 'helm', (0, -0.03, 1.45), 0.105, 0.24, plate_hi,
                      profile=[(0.095, -0.12), (0.108, -0.07), (0.11, 0.0), (0.104, 0.05), (0.085, 0.09), (0.05, 0.115), (0.0, 0.122)],
                      scale=(1, 1.1, 1))
    for v in helm.data.vertices:   # pinch the face into a keel
        if v.co.y < -0.03:
            v.co.y -= 0.035 * max(0.0, 1 - abs(v.co.x) / 0.09)
    paint_fn(helm, lambda p: '#0a0610' if (p.y < -0.08 and ((abs(p.x) < 0.075 and abs(p.z - 1.46) < 0.014) or
                                                           (abs(p.x) < 0.014 and 1.36 < p.z < 1.46)))
             else gold if abs(p.z - 1.335) < 0.012 or (abs(p.x) < 0.01 and p.z > 1.5) else armour(p))
    for s in (-1, 1):
        c.add('head', A.sphere(f'eye_light{s}', r=0.014, loc=(s * 0.042, -0.152, 1.46), scale=(1.7, 0.5, 0.6), color='#ffb030',
                               mat='M_Emit', seg=10, rings=6))
        spine(c, 'head', f'cheek_spike{s}', (s * 0.09, -0.08, 1.37), (s * 0.6, -0.4, -0.5), 0.07, 0.016, plate_hi, tip='#c9a0ff', seg=6)
    # crown of horns
    for s in (-1, 1):
        horn(c, 'crest', f'great_horn{s}', (s * 0.085, -0.02, 1.52), (s * 0.26, 0.0, 1.66), (s * 0.24, 0.12, 1.86), 0.04, '#2a2232', '#e8d8ff', n=14)
    c.ring('crest', 'circlet', (0, -0.03, 1.54), 0.1, 0.012, gold, rot=(-8, 0, 0), scale=(1, 1.1, 1))
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
