"""Sculpted slimes and plant creatures (monster v3): slime, magma_slime, mushroom (+elite), sprout, mandragora.
Run through the production runner: blender -b --factory-startup -P Blender/enemies_a/generate_all.py -- --asset slime
"""
import math
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from sculpt_kit import Sculpt, A, lerp_col, vgrad  # noqa: E402,F401
from mathutils import Vector  # noqa: E402


def _drip_skirt(c, bone, r, z, lobes, size, color, seed=0):
    """Uneven ring of drips/lobes around the base of a jelly body."""
    for k in range(lobes):
        a = math.tau * (k + 0.37 * math.sin(k * 2.3 + seed)) / lobes
        rr = r * (0.92 + 0.12 * math.sin(k * 1.7 + seed))
        c.blob(bone, (rr * math.cos(a), rr * math.sin(a), z), (size, size, size * 0.6), color)


def slime(eid):
    """숲 슬라임 — translucent teal jelly with a drooping teardrop top, a drip skirt, a darker core,
    glossy dark eyes, a leaf sprig and a small crystal grown into its crown."""
    c = Sculpt(eid, tris=6000, material='M_Clear', ao=0.45)
    c.bone('body', (0, 0, 0.2)); c.bone('eyes', (0, -0.27, 0.34), 'body'); c.bone('crest', (0, 0.06, 0.58), 'body')
    jelly = vgrad(0.0, '#2f8fd0', 0.6, '#9fe3ff')
    c.blob('body', (0, 0, 0.21), (0.36, 0.33, 0.21), jelly)
    c.blob('body', (0, 0.02, 0.36), (0.25, 0.24, 0.2), jelly)
    c.blob('body', (0, 0.05, 0.5), (0.13, 0.13, 0.12), jelly)
    c.limb('crest', [(0, 0.06, 0.56), (0.02, 0.1, 0.64), (0.06, 0.15, 0.66)], [0.07, 0.04, 0.018], jelly)
    _drip_skirt(c, 'body', 0.3, 0.06, 7, 0.1, '#2f7fc0')
    c.paint((0, -0.25, 0.2), (0.07, 0.04, 0.05), '#2a4d8a')                  # mouth shadow
    for s in (-1, 1):
        c.eye('eyes', (s * 0.1, -0.265, 0.34), (s * 0.25, -1, 0.1), 0.055, '#0f1a33', iris_edge=0.25,
              sclera='#16213d')
    core = A.sphere('core', r=0.11, loc=(0, 0.04, 0.23), color='#1f6aa8', seg=16, rings=10)
    c.add('body', core)
    for k, (d, L) in enumerate((((0.8, -0.2, 0.6), 0.16), ((-0.7, 0.2, 0.7), 0.14), ((0.1, 0.6, 1), 0.1))):
        c.petal('crest', f'leaf{k}', (0.06, 0.15, 0.66), d, L, L * 0.6, '#7fd65a', tip='#3c9a35')
    c.gem('body', 'crystal', (-0.16, 0.08, 0.42), (-0.5, 0.3, 1), 0.04, 0.16, '#d9f4ff', '#58aee0', mat='M_Clear')
    return c.finish('hop')


def magma_slime(eid):
    """용암 슬라임 — heavy molten blob: dark cooled crust plates over glowing lava, lava drips at the base,
    squinting ember eyes."""
    c = Sculpt(eid, tris=7000, ao=0.5)
    c.bone('body', (0, 0, 0.2)); c.bone('eyes', (0, -0.3, 0.36), 'body'); c.bone('crest', (0, 0, 0.6), 'body')

    def lava(p):
        # cooled crust plates split by thin glowing cracks; the base is still molten
        a = math.atan2(p.y, p.x)
        crack = min(abs(math.sin(a * 3 + p.z * 6)), abs(math.sin(p.z * 10 + math.sin(a * 2) * 1.2)))
        if p.z < 0.12:
            return lerp_col('#ff6a1a', '#ffb347', (0.12 - p.z) / 0.1)
        if crack < 0.16:
            return lerp_col('#ffd060', '#ff6a1a', crack / 0.16)
        return lerp_col('#2e1b19', '#4a2a24', (p.z - 0.2) / 0.4)
    c.blob('body', (0, 0, 0.22), (0.4, 0.37, 0.22), lava)
    c.blob('body', (0, 0.03, 0.38), (0.28, 0.26, 0.2), lava)
    c.blob('body', (0, 0.05, 0.52), (0.14, 0.14, 0.11), lava)
    _drip_skirt(c, 'body', 0.34, 0.05, 8, 0.11, '#ff7a1a', seed=1.3)
    c.paint((0, -0.3, 0.2), (0.09, 0.05, 0.05), '#2a0f0a')
    for s in (-1, 1):
        c.blob('eyes', (s * 0.11, -0.28, 0.395), (0.07, 0.04, 0.025), '#3a2220')         # heavy crust lids
        c.eye('eyes', (s * 0.11, -0.29, 0.35), (s * 0.25, -1, 0.05), 0.045, '#ffb02e', iris_edge=0.45,
              sclera='#ffe7a0')
    for k in range(6):
        a = math.tau * k / 6 + 0.4
        c.chunk('crest', f'crust{k}', (0.16 * math.cos(a), 0.16 * math.sin(a) + 0.04, 0.5 - 0.02 * (k % 2)),
                (0.07, 0.06, 0.04), '#2c1a18', seed=k + 3)
    for k in range(3):
        c.flame('crest', f'vent{k}', (0.06 * (k - 1), 0.08, 0.6), 0.14, 0.035, lean=(0.03 * (k - 1), 0.04, 0))
    return c.finish('hop')


def mushroom(eid):
    """독버섯 / 독왕 버섯 — stout mushroom folk: a broad spotted cap with gills underneath, a pot-bellied stalk,
    stubby arms and feet, small eyes under the cap's shadow; the elite is a purple toadstool king."""
    c = Sculpt(eid, tris=8000)
    el = c.elite
    cap_col, spot_col, stalk = ('#c8352c', '#fff3dc', '#f0e2c6') if not el else ('#6a3aa2', '#d9ff7a', '#e8dcc8')
    spots = [(0.0, -0.1), (0.22, 0.05), (-0.2, 0.12), (0.1, 0.25), (-0.12, -0.22), (0.26, -0.18), (-0.28, -0.08), (0.02, 0.1)]

    def cap(p):
        for sx, sy in spots:
            if (p.x - sx) ** 2 + (p.y - sy) ** 2 < 0.0055 and p.z > 0.7:
                return spot_col
        return lerp_col(lerp_col(cap_col, '#000000', 0.25), cap_col, (p.z - 0.62) / 0.12)
    c.bone('body', (0, 0, 0.25)); c.bone('head', (0, 0, 0.6), 'body'); c.bone('eyes', (0, -0.17, 0.48), 'head')
    c.blob('body', (0, 0, 0.3), (0.19, 0.17, 0.22), stalk)                         # pot belly
    c.blob('body', (0, 0, 0.5), (0.15, 0.14, 0.12), stalk)
    c.blob('body', (0, -0.06, 0.26), (0.14, 0.1, 0.14), lerp_col(stalk, '#ffffff', 0.4))
    c.blob('head', (0, 0, 0.66), (0.4, 0.38, 0.1), cap)                             # cap rim
    c.blob('head', (0, 0.01, 0.75), (0.33, 0.32, 0.16), cap)                        # cap dome
    c.blob('head', (0, 0.02, 0.85), (0.2, 0.2, 0.1), cap)                           # crown of the dome
    for k in range(10):                                                             # rim curls down
        a = math.tau * k / 10
        c.blob('head', (0.37 * math.cos(a), 0.35 * math.sin(a), 0.6), (0.09, 0.09, 0.06), cap)
    c.blob('head', (0, 0.0, 0.6), (0.33, 0.31, 0.05), lerp_col(stalk, '#8a6a52', 0.45))   # gills
    for s, side in ((-1, 'R'), (1, 'L')):
        c.bone('arm.' + side, (s * 0.17, -0.02, 0.4), 'body')
        c.limb('arm.' + side, [(s * 0.16, -0.02, 0.4), (s * 0.28, -0.06, 0.33), (s * 0.33, -0.1, 0.26)], [0.055, 0.045, 0.05], stalk)
        c.bone('leg.' + side, (s * 0.09, 0, 0.14), 'body')
        c.limb('leg.' + side, [(s * 0.09, 0, 0.16), (s * 0.11, -0.03, 0.06)], [0.07, 0.065], stalk)
        c.blob('leg.' + side, (s * 0.11, -0.06, 0.04), (0.08, 0.1, 0.045), lerp_col(stalk, '#a08060', 0.3))
        c.blob('eyes', (s * 0.065, -0.15, 0.5), (0.05, 0.04, 0.02), stalk)           # brow lids
        c.eye('eyes', (s * 0.065, -0.155, 0.47), (s * 0.3, -1, 0.05), 0.028, '#3a2a1e' if not el else '#9a2ab8')
    c.paint((0, -0.17, 0.4), (0.035, 0.02, 0.012), '#6a3a2a')                       # small mouth
    if el:
        for k in range(5):
            a = math.pi * (0.15 + 0.7 * k / 4)
            c.cone_to('head', f'crown{k}', (0.12 * math.cos(a), -0.02 + 0.06 * math.sin(a), 0.86),
                      (0.14 * math.cos(a), -0.02 + 0.07 * math.sin(a), 0.98), 0.025, '#e8b84a')
        c.gem('head', 'crown_gem', (0, -0.1, 0.88), (0, -0.4, 1), 0.03, 0.06, '#c8ff7a', '#5aa02a')
    return c.finish('biped')


def sprout(eid):
    """풀뿌리 — a walking tree stump: ridged bark trunk that splits into root legs and branch arms, a mossy rim,
    a sapling on top, and calm eyes set in a bark knot."""
    c = Sculpt(eid, tris=9000)

    def bark(p):
        a = math.atan2(p.y, p.x)
        ridge = 0.5 + 0.5 * math.sin(a * 11 + math.sin(p.z * 9) * 1.4)
        return lerp_col('#6e4527', '#b88454', ridge * 0.8 + 0.2 * (p.z - 0.2))
    c.bone('body', (0, 0, 0.3)); c.bone('eyes', (0, -0.22, 0.57), 'body'); c.bone('crest', (0, 0, 0.82), 'body')
    for k, z in enumerate((0.32, 0.45, 0.58, 0.7)):
        r = 0.22 - 0.012 * k
        c.blob('body', (0, 0, z), (r, r * 0.95, 0.1), bark)
    c.blob('body', (0, 0, 0.8), (0.2, 0.19, 0.05), '#d6b27a')                      # cut top rings
    for k in range(9):
        a = math.tau * k / 9
        c.blob('body', (0.2 * math.cos(a), 0.19 * math.sin(a), 0.79), (0.06, 0.06, 0.04), '#7cb342')  # moss rim
    for s in (-1, 1):
        c.blob('eyes', (s * 0.07, -0.19, 0.6), (0.05, 0.035, 0.022), '#5a3a20')     # knot brows
        c.eye('eyes', (s * 0.07, -0.2, 0.565), (s * 0.3, -1, 0.0), 0.03, '#5a8a2a')
    c.paint((0, -0.21, 0.5), (0.04, 0.02, 0.012), '#3a2414')
    for s, side in ((-1, 'R'), (1, 'L')):
        c.bone('arm.' + side, (s * 0.2, -0.02, 0.6), 'body')
        c.limb('arm.' + side, [(s * 0.18, -0.02, 0.6), (s * 0.33, -0.06, 0.55), (s * 0.42, -0.12, 0.42)], [0.06, 0.045, 0.04], bark)
        c.blob('arm.' + side, (s * 0.44, -0.14, 0.39), (0.06, 0.055, 0.055), '#8a5a34')
        c.limb('arm.' + side, [(s * 0.44, -0.14, 0.39), (s * 0.5, -0.2, 0.35)], [0.03, 0.02], '#8a5a34')   # twig thumb
        c.petal('arm.' + side, f'armleaf{side}', (s * 0.33, -0.06, 0.58), (s * 0.3, 0.2, 1), 0.1, 0.06, '#8ad25a', tip='#4c9a2c')
        c.bone('leg.' + side, (s * 0.12, 0, 0.26), 'body')
        c.limb('leg.' + side, [(s * 0.12, 0, 0.28), (s * 0.19, -0.02, 0.15), (s * 0.22, -0.05, 0.05)], [0.09, 0.075, 0.07], bark)
        for j, d in enumerate(((0.4, -1), (1, -0.3), (-0.3, -0.9))):
            c.limb('leg.' + side, [(s * 0.22, -0.05, 0.04), (s * 0.22 + s * d[0] * 0.09, -0.05 + d[1] * 0.09, 0.025)],
                   [0.045, 0.028], '#7a4c2a')
    c.tube('crest', 'stem', [(0, 0, 0.78), (0.01, 0, 0.9), (0, 0, 1.02)], 0.018, '#5aa833', taper=0.6)
    for k, (d, L) in enumerate((((0.9, -0.15, 0.5), 0.22), ((-0.9, 0.1, 0.6), 0.21), ((0.1, -0.35, 1.0), 0.12))):
        c.petal('crest', f'sapleaf{k}', (0, 0, 1.0), d, L, L * 0.6, '#9ae05a', tip='#4c9a2c')
    return c.finish('biped')


def mandragora(eid):
    """만드라고라 — a pale root creature: a plump tapered root body with fine root hairs, root-like arms and legs,
    a leafy crown with a magenta bloom, and an open, wailing mouth (its scream is its weapon)."""
    c = Sculpt(eid, tris=7000)
    skin = vgrad(0.1, '#b98a5e', 0.55, '#f0d6ae')
    c.bone('body', (0, 0, 0.3)); c.bone('eyes', (0, -0.21, 0.5), 'body'); c.bone('crest', (0, 0, 0.72), 'body')
    c.blob('body', (0, 0, 0.44), (0.23, 0.21, 0.26), skin)
    c.limb('body', [(0, 0.01, 0.24), (0, 0.02, 0.13), (0.01, 0.04, 0.06)], [0.15, 0.08, 0.03], skin)
    c.blob('body', (0, 0, 0.66), (0.1, 0.1, 0.06), '#c9a274')
    for z in (0.33, 0.5):
        c.paint((0, -0.2, z), (0.25, 0.02, 0.008), '#c79c70')                        # root rings
    c.blob('body', (0, -0.205, 0.38), (0.055, 0.03, 0.06), skin, negative=True)      # open mouth cavity
    c.paint((0, -0.19, 0.38), (0.06, 0.05, 0.07), '#4a1a22', weight=1.5)
    for s in (-1, 1):
        c.blob('eyes', (s * 0.08, -0.19, 0.535), (0.055, 0.035, 0.022), '#c9a274')    # brows
        c.eye('eyes', (s * 0.08, -0.2, 0.5), (s * 0.3, -1, 0.05), 0.032, '#6a3fa8')
    for s, side in ((-1, 'R'), (1, 'L')):
        c.bone('arm.' + side, (s * 0.2, -0.02, 0.45), 'body')
        c.limb('arm.' + side, [(s * 0.2, -0.02, 0.45), (s * 0.3, -0.06, 0.38), (s * 0.34, -0.1, 0.3), (s * 0.35, -0.12, 0.25)],
               [0.045, 0.035, 0.03, 0.03], skin)
        c.bone('leg.' + side, (s * 0.1, 0, 0.2), 'body')
        c.limb('leg.' + side, [(s * 0.1, 0, 0.22), (s * 0.14, -0.02, 0.12), (s * 0.15, -0.06, 0.04)], [0.055, 0.045, 0.045], skin)
    for k in range(6):
        a = math.tau * k / 6 + 0.25
        c.petal('crest', f'crown_leaf{k}', (0, 0, 0.68), (math.cos(a) * 0.9, math.sin(a) * 0.9, 1.0), 0.3 + 0.05 * (k % 2),
                0.14, '#5fbf4a', tip='#2f8a35', cup=0.35)
    c.tube('crest', 'flower_stalk', [(0, 0, 0.7), (0.02, -0.02, 0.86), (0, -0.05, 0.98)], 0.016, '#3e8f37')
    for k in range(6):
        a = math.tau * k / 6
        c.petal('crest', f'bloom{k}', (0, -0.05, 0.98), (math.cos(a), math.sin(a) - 0.3, 0.55), 0.11, 0.08, '#ff6fc6',
                tip='#c02d93', cup=0.3)
    c.orb('crest', 'bloom_heart', (0, -0.06, 1.0), (0.035, 0.035, 0.03), '#ffe45c')

    def extra(a, clip, f, t, i, names):
        if clip == 'Cast':  # the scream: crown leaves flare
            r = max(0.0, 1 - abs(t - 0.6) / 0.25)
            a.s('crest', f, (1 + 0.35 * r, 1 + 0.35 * r, 1 - 0.1 * r))
        else:
            a.r('crest', f, (4 * math.sin(math.tau * t), 6 * math.sin(math.tau * t + 1), 0))
    return c.finish('biped', extra)


BUILDERS = {'slime': slime, 'magma_slime': magma_slime, 'mushroom': mushroom, 'elite_mushroom': mushroom,
            'sprout': sprout, 'mandragora': mandragora}

if __name__ == '__main__':
    eid = sys.argv[sys.argv.index('--') + 1]
    BUILDERS[eid](eid)
