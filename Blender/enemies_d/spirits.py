"""Sculpted spirits (monster v3): ghost, flame_elemental.
Run through the production runner: blender -b --factory-startup -P Blender/enemies_a/generate_all.py -- --asset ghost
"""
import math
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from sculpt_kit import Sculpt, A, lerp_col, vgrad  # noqa: E402,F401
from mathutils import Vector  # noqa: E402


def ghost(eid):
    """원령 — a drifting shroud spirit: a hooded head flowing into a long, twisting tail, draped sleeve-arms,
    hollow dark eyes with faint pale pupils and a small open mouth; it carries a soul lantern and a broken shackle."""
    c = Sculpt(eid, tris=7000, material='M_Clear', ao=0.4)
    sheet = vgrad(0.35, '#a99bdf', 1.1, '#efeaff')
    c.bone('body', (0, 0, 0.75)); c.bone('eyes', (0, -0.2, 0.93), 'body'); c.bone('tail1', (0, 0.02, 0.55), 'body')
    c.bone('tail2', (0, 0.1, 0.38), 'tail1')
    c.blob('body', (0, 0, 0.92), (0.2, 0.19, 0.2), sheet)                                           # head
    c.blob('body', (0, 0.01, 0.74), (0.24, 0.21, 0.2), sheet)                                       # shoulders
    c.limb(['tail1', 'tail1', 'tail2', 'tail2'], [(0, 0.02, 0.62), (0.02, 0.05, 0.5), (-0.03, 0.1, 0.4), (0.04, 0.16, 0.32),
                                                  (0.1, 0.24, 0.27)], [0.2, 0.16, 0.11, 0.07, 0.025], sheet)
    for k in range(5):  # loose ragged folds hanging from the shoulders
        a = math.radians(200 + k * 35)
        c.tuft('body', (0.2 * math.cos(a), 0.17 * math.sin(a) + 0.02, 0.66), (math.cos(a) * 0.4, math.sin(a) * 0.4, -1), 0.14,
               0.06, '#c9bff0', curl=0.0)
    for s in (-1, 1):  # hollow dark eyes with a faint pale pupil, set slightly into the hood
        c.eye('eyes', (s * 0.068, -0.172, 0.93), (s * 0.3, -1, 0.0), 0.036, '#d8d0ff', iris_edge=0.9, sclera='#2b1f45',
              pupil='#f4f0ff', glint=False)
    c.paint((0, -0.19, 0.84), (0.025, 0.02, 0.03), '#2b1f45', weight=1.2)                             # small mouth
    for s, side in ((-1, 'R'), (1, 'L')):
        c.bone('arm.' + side, (s * 0.2, -0.02, 0.8), 'body')
        c.limb('arm.' + side, [(s * 0.2, -0.02, 0.8), (s * 0.3, -0.08, 0.72), (s * 0.34, -0.14, 0.64)], [0.07, 0.06, 0.05], sheet)
        c.tuft('arm.' + side, (s * 0.33, -0.13, 0.65), (s * 0.2, -0.2, -1), 0.1, 0.05, '#c9bff0')
    c.ring('arm.R', 'shackle', (-0.33, -0.15, 0.62), 0.045, 0.014, '#6a6f7e', rot=(30, 0, 30))
    for k in range(3):
        c.ring('arm.R', f'chain{k}', (-0.35 - k * 0.025, -0.17 - k * 0.02, 0.55 - k * 0.06), 0.025, 0.008, '#6a6f7e',
               rot=(90 * (k % 2), 30, 0))
    c.bone('weapon.L', (0.34, -0.15, 0.62), 'arm.L')
    c.tube('weapon.L', 'lantern_chain', [(0.34, -0.15, 0.62), (0.35, -0.17, 0.5)], 0.006, '#3b3542')
    c.box('weapon.L', 'lantern_cap', (0.35, -0.17, 0.49), (0.08, 0.08, 0.025), '#2b2632', bevel=0.008)
    c.orb('weapon.L', 'soul_flame', (0.35, -0.17, 0.42), (0.04, 0.04, 0.055), '#7dff9a', 'M_Emit')
    c.add('weapon.L', A.lathe('lantern_glass', [(0.045, 0.36), (0.05, 0.42), (0.045, 0.48)], loc=(0.35, -0.17, 0), color='#bfffd0',
                              mat='M_Clear', seg=12))
    c.box('weapon.L', 'lantern_base', (0.35, -0.17, 0.355), (0.075, 0.075, 0.02), '#2b2632', bevel=0.006)

    def extra(a, clip, f, t, i, names):
        a.r('tail1', f, (4 * math.sin(math.tau * t * 2), 0, 12 * math.sin(math.tau * t)))
        a.r('tail2', f, (6 * math.sin(math.tau * t * 2 + 1), 0, 18 * math.sin(math.tau * t + 0.8)))
    return c.finish('float', extra)


def flame_elemental(eid):
    """불꽃 정령 — a fire spirit with a body of cooling magma: an obsidian-crusted torso split by glowing cracks,
    a mane of living flame, heavy rock fists, and a tapering flame tail instead of legs."""
    c = Sculpt(eid, tris=8000)
    obs, lava = '#2c1d22', '#ff8a2a'

    def magma(p):
        a = math.atan2(p.y, p.x)
        crack = min(abs(math.sin(a * 3 + p.z * 8)), abs(math.sin(p.z * 13 + a)))
        if crack < 0.14:
            return lerp_col('#ffe07a', lava, crack / 0.14)
        return lerp_col(obs, '#5a2e24', (p.z - 0.5) / 0.4)
    c.bone('body', (0, 0, 0.62)); c.bone('head', (0, -0.02, 0.86), 'body'); c.bone('eyes', (0, -0.16, 0.92), 'head')
    c.bone('flame_hair', (0, 0.02, 1.0), 'head'); c.bone('tail1', (0, 0, 0.48), 'body')
    c.blob('body', (0, 0, 0.7), (0.19, 0.15, 0.16), magma)
    c.blob('body', (0, 0, 0.56), (0.14, 0.12, 0.1), magma)
    for s in (-1, 1):
        c.blob('body', (s * 0.17, 0, 0.78), (0.09, 0.09, 0.08), magma)
    c.limb('tail1', [(0, 0.0, 0.5), (0.02, 0.04, 0.4), (-0.02, 0.08, 0.32)], [0.1, 0.07, 0.035], lambda p: lerp_col(lava, '#ffd23a', (0.5 - p.z) / 0.2))
    c.blob('head', (0, -0.03, 0.92), (0.12, 0.11, 0.11), magma)
    c.blob('head', (0, -0.12, 0.97), (0.09, 0.04, 0.025), obs)                                     # brow ridge
    for s in (-1, 1):
        c.eye('eyes', (s * 0.05, -0.115, 0.935), (s * 0.35, -1, 0.0), 0.024, '#ffd23a', iris_edge=0.35, sclera='#ffe9a0',
              pupil='#7a2a0a')
        c.cone_to('head', f'horn{s}', (s * 0.09, 0.0, 1.0), (s * 0.17, 0.05, 1.12), 0.03, obs)
    c.paint((0, -0.13, 0.86), (0.04, 0.02, 0.012), '#ffb347')
    for k in range(7):
        x = (k - 3) * 0.04
        c.flame('flame_hair', f'hair_flame{k}', (x, 0.03 + abs(k - 3) * 0.01, 0.99 - abs(k - 3) * 0.02), 0.32 - abs(k - 3) * 0.04, 0.055,
                lean=(x * 1.2, 0.2, 0))
    c.flame('tail1', 'tail_flame', (0, 0.06, 0.36), 0.28, 0.08, lean=(0, 0.1, 0))
    for s, side in ((-1, 'R'), (1, 'L')):
        c.bone('arm.' + side, (s * 0.18, -0.02, 0.76), 'body')
        c.limb('arm.' + side, [(s * 0.2, -0.02, 0.76), (s * 0.28, -0.06, 0.64), (s * 0.31, -0.1, 0.54)], [0.06, 0.05, 0.05], magma)
        c.blob('arm.' + side, (s * 0.32, -0.12, 0.48), (0.08, 0.08, 0.08), magma)
        for j in range(2):
            c.flame('arm.' + side, f'shoulder_flame{side}{j}', (s * (0.17 + 0.05 * j), 0.03, 0.84 - 0.05 * j), 0.18 - 0.04 * j, 0.045,
                    lean=(s * 0.1, 0.08, 0))
    return c.finish('float')


BUILDERS = {'ghost': ghost, 'flame_elemental': flame_elemental}

if __name__ == '__main__':
    eid = sys.argv[sys.argv.index('--') + 1]
    BUILDERS[eid](eid)
