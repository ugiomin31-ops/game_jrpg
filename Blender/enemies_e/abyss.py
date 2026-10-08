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
def mirror_post(crack_scale=2.6, tint='#b8b0d8'):
    """post-paint for living mirror-glass: a sky-bright top and dark lower reflection split by a soft horizon,
    a violet tint, and a web of dark cracks with pale chipped edges."""
    def f(p, n, col):
        h = n.z
        sky = lerp_col('#e8ecff', '#9fb2e8', 1 - h) if h > -0.05 else lerp_col('#3a3456', '#16122a', -h)
        base = lerp_col(sky, tint, 0.35)
        q = abs(noise.noise(p * crack_scale + Vector((1.7, 0.3, 2.2))))
        r = abs(noise.noise(p * crack_scale * 1.7 + Vector((4.1, 2.0, 0.6))))
        if q < 0.045 or r < 0.02:
            return rgba('#120c1e')
        if q < 0.075 or r < 0.032:
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
