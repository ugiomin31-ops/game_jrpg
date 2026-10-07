"""Sculpted beasts (monster v3): canines (ice_wolf, hellhound + elites).
Run through the production runner: blender -b --factory-startup -P Blender/enemies_a/generate_all.py -- --asset ice_wolf
"""
import math
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from sculpt_kit import Sculpt, A, lerp_col  # noqa: E402,F401
from monster_kit import DIE_HOLD  # noqa: E402
from mathutils import Vector  # noqa: E402


def canine_head(c, hb, eb, jb, cx, k, pal, iris, ear=True, snarl=False):
    """Wolf/hound head on bones hb (skull), eb (eyes), jb (jaw), centred at x=cx, scaled by k.
    pal: back, side, pale, dark."""
    back, side_c, pale, dark = pal
    X = lambda x: cx + x * k  # noqa: E731
    c.blob(hb, (X(0), -0.43, 0.79), (0.1 * k, 0.11 * k, 0.085 * k), back)
    for s in (-1, 1):
        c.blob(hb, (X(s * 0.075), -0.45, 0.73), (0.055 * k, 0.07 * k, 0.06 * k), pale, weight=1.3)
        c.blob(hb, (X(s * 0.045), -0.43 - 0.1 * k, 0.79 + 0.025 * k), (0.035 * k, 0.035 * k, 0.018 * k), back)  # brow
    c.limb(hb, [(X(0), -0.43 - 0.07 * k, 0.765), (X(0), -0.43 - 0.15 * k, 0.75), (X(0), -0.43 - 0.215 * k, 0.74)],
           [0.06 * k, 0.047 * k, 0.034 * k], side_c)
    c.blob(hb, (X(0), -0.43 - 0.14 * k, 0.77), (0.04 * k, 0.06 * k, 0.03 * k), back)              # muzzle bridge
    c.blob(hb, (X(0), -0.43 - 0.245 * k, 0.745), (0.022 * k, 0.016 * k, 0.017 * k), dark)         # nose
    c.limb(jb, [(X(0), -0.43 - 0.07 * k, 0.7), (X(0), -0.43 - 0.17 * k, 0.705)], [0.04 * k, 0.026 * k], pale, weight=1.3)
    c.blob(jb, (X(0), -0.43 - 0.17 * k, 0.715), (0.022 * k, 0.02 * k, 0.008 * k), dark)           # lip line
    if snarl:
        for s in (-1, 1):
            c.spike(jb, f'fang{hb}{s}', (X(s * 0.02), -0.43 - 0.19 * k, 0.72), (X(s * 0.02), -0.43 - 0.2 * k, 0.69),
                    0.008 * k, '#f4ead6')
    for s in (-1, 1):
        c.eye(eb, (X(s * 0.052), -0.43 - 0.115 * k, 0.79), (s * 0.45, -1, 0.05), 0.023 * k, iris)
        c.tufts(hb, (X(s * 0.09), -0.45, 0.72), [(s * 0.8, 0.6, -0.4), (s * 0.9, 0.45, 0.0)], 0.08 * k, 0.032 * k, pale,
                weight=1.3)
    if ear:
        for s, side in ((-1, 'R'), (1, 'L')):
            b = 'ear.' + side
            if hb == 'head':
                c.bone(b, (X(s * 0.06), -0.41, 0.86), hb)
            else:
                b = hb  # extra heads keep their ears on the skull bone
            c.blob(b, (X(s * 0.065), -0.41, 0.885), (0.045 * k, 0.022 * k, 0.04 * k), back, rot=(0, s * 12, 0))
            c.blob(b, (X(s * 0.075), -0.405, 0.885 + 0.055 * k), (0.03 * k, 0.017 * k, 0.035 * k), back, rot=(0, s * 14, 0))
            c.blob(b, (X(s * 0.083), -0.4, 0.885 + 0.095 * k), (0.016 * k, 0.012 * k, 0.024 * k), dark, rot=(0, s * 16, 0))
            c.blob(b, (X(s * 0.066), -0.43, 0.9), (0.025 * k, 0.008 * k, 0.03 * k), '#c9a9b4')


def canine_body(c, pal, fur, bulk=1.0, tail_col=None):
    """Torso, four legs and tail of a wolf-like quadruped (bones body, leg.*, tail1-3)."""
    back, side_c, pale, dark = pal
    b = bulk
    c.blob('body', (0, -0.17, 0.53), (0.15 * b, 0.17, 0.18 * b), fur)
    c.blob('body', (0, 0.02, 0.56), (0.14 * b, 0.2, 0.14 * b), fur)
    c.blob('body', (0, 0.06, 0.48), (0.1 * b, 0.16, 0.07), pale)
    c.blob('body', (0, 0.25, 0.56), (0.13 * b, 0.14, 0.13 * b), fur)
    c.blob('body', (0, -0.04, 0.66), (0.1 * b, 0.32, 0.05), back)
    c.blob('body', (0, -0.29, 0.52), (0.11 * b, 0.08, 0.13), pale, weight=1.35)
    c.blob('body', (0, -0.31, 0.42), (0.07 * b, 0.06, 0.07), pale, weight=1.35)
    for s in (-1, 1):
        c.tuft('body', (s * 0.07, -0.34, 0.5), (s * 0.5, 0.9, -0.35), 0.12, 0.05, pale, weight=1.4)
    for s, side in ((-1, 'R'), (1, 'L')):
        x = s * 0.1 * b
        c.bone('leg.F' + side, (x, -0.2, 0.52), 'body')
        c.blob('leg.F' + side, (x, -0.21, 0.48), (0.07 * b, 0.09, 0.11), fur)
        c.limb('leg.F' + side, [(x, -0.22, 0.42), (x * 1.05, -0.25, 0.27), (x * 1.05, -0.22, 0.12), (x * 1.05, -0.24, 0.05)],
               [0.055 * b, 0.042 * b, 0.032 * b, 0.034 * b], side_c)
        c.blob('leg.F' + side, (x * 1.05, -0.27, 0.032), (0.04 * b, 0.058, 0.03), pale)
        c.tuft('leg.F' + side, (x, -0.19, 0.36), (s * 0.1, 1, -0.7), 0.07, 0.03, side_c)
        c.bone('leg.B' + side, (x, 0.28, 0.52), 'body')
        c.blob('leg.B' + side, (x * 1.1, 0.28, 0.46), (0.075 * b, 0.12, 0.13), fur)
        c.limb('leg.B' + side, [(x * 1.1, 0.24, 0.36), (x * 1.1, 0.3, 0.24), (x * 1.1, 0.38, 0.15), (x * 1.08, 0.33, 0.05)],
               [0.06 * b, 0.045 * b, 0.034 * b, 0.03 * b], side_c)
        c.blob('leg.B' + side, (x * 1.08, 0.3, 0.032), (0.04 * b, 0.058, 0.03), pale)
        c.tufts('leg.B' + side, (x * 1.1, 0.37, 0.42), [(s * 0.1, 1, -0.9), (s * 0.2, 1, -0.4)], 0.08, 0.035, side_c)
    for k, p in enumerate(((0, 0.37, 0.6), (0, 0.52, 0.58), (0, 0.65, 0.5))):
        c.bone(f'tail{k + 1}', p, 'body' if k == 0 else f'tail{k}')
    c.limb(['tail1', 'tail2', 'tail3'], [(0, 0.36, 0.6), (0, 0.5, 0.58), (0, 0.63, 0.5), (0, 0.72, 0.4)],
           [0.05, 0.075, 0.07, 0.04], tail_col or (lambda p: lerp_col(back, pale, (p.y - 0.6) / 0.1)))


def neck(c, bones, cx, fur, pale, k=1.0, mane=None, el=False):
    """Neck from the shoulders to a head at x=cx, with a ruff of sculpted tufts sweeping back."""
    c.limb(bones, [(cx * 0.4, -0.2, 0.62), (cx * 0.8, -0.31, 0.69), (cx, -0.39, 0.76)], [0.12 * k, 0.105 * k, 0.09 * k], fur)
    for s in (-1, 1):
        c.blob('body', (cx + s * 0.08 * k, -0.3, 0.6), (0.06 * k, 0.07, 0.09), pale, weight=1.3)
        for z, dz in ((0.7, 0.35), (0.63, 0.05), (0.56, -0.3)):
            c.tuft('body', (cx + s * 0.085 * k, -0.33, z), (s * 0.4, 1, dz), (0.2 if el else 0.16) * k, 0.05 * k,
                   mane or pale, curl=0.15, weight=1.2)
    c.tufts('body', (cx, -0.33, 0.73), [(0, 0.7, 0.8), (0.3, 0.7, 0.6), (-0.3, 0.7, 0.6)], 0.1 * k, 0.04 * k, mane or pale)


def ice_wolf(eid):
    """서리 늑대 / 설원의 우두머리 — lean frost wolf: deep chest, tucked waist, zig-zag hind legs, bushy tail,
    pale ruff and muzzle, ice-blue eyes set under brows; a few ice shards along the spine."""
    c = Sculpt(eid, tris=9000)
    el = c.elite
    pal = ('#3f5f93', '#7d9cc9', '#f4f8ff', '#2c2f3c') if el else ('#5f84b8', '#9db8dc', '#fbfdff', '#2c2f3c')
    back, side_c, pale, dark = pal
    fur = lambda p: lerp_col(pale, lerp_col(side_c, back, (p.z - 0.5) / 0.14), (p.z - 0.42) / 0.1)  # noqa: E731
    c.bone('body', (0, 0.04, 0.55))
    c.bone('head', (0, -0.33, 0.68), 'body')
    c.bone('eyes', (0, -0.55, 0.79), 'head')
    c.bone('jaw', (0, -0.47, 0.67), 'head')
    canine_body(c, pal, fur)
    neck(c, ['body', 'head'], 0, fur, pale, mane=side_c if not el else pale, el=el)
    canine_head(c, 'head', 'eyes', 'jaw', 0, 1.0, pal, '#8fd0ee' if not el else '#ffcf5a')
    shards = ((0, -0.18, 0.7, 0.07), (0, -0.06, 0.71, 0.09), (0, 0.07, 0.7, 0.07), (0, 0.18, 0.68, 0.05))
    if el:
        shards += ((0.05, -0.3, 0.78, 0.06), (-0.05, -0.3, 0.78, 0.06), (0, 0.29, 0.66, 0.05))
    for k, (x, y, z, h) in enumerate(shards):
        c.gem('body', f'ice_shard{k}', (x, y, z - 0.02), (x * 3, 0.15, 1), 0.024 + h * 0.15, h * (1.5 if el else 1.1),
              '#e4fbff', '#6fc6ee', mat='M_Clear')
    return c.finish('quad')


def hellhound(eid):
    """헬하운드 / 오르트로스 — heavy charcoal hound with glowing ember cracks, a flame mane and tail flame;
    the elite has two heads with curled horns."""
    c = Sculpt(eid, tris=10000)
    el = c.elite
    pal = ('#2a1f27', '#43333b', '#6b4f50', '#140e12') if not el else ('#3a1820', '#5a2a31', '#8a5047', '#160a0d')
    back, side_c, pale, dark = pal

    def fur(p):
        # charcoal with ember-orange cracks along the flanks
        crack = abs(math.sin(p.y * 31 + math.sin(p.z * 23) * 1.7)) < 0.07 and 0.42 < p.z < 0.62
        return lerp_col(side_c, back, (p.z - 0.48) / 0.14) if not crack else lerp_col('#ff6a1a', '#ffb347', 0.4)
    c.bone('body', (0, 0.04, 0.55))
    heads = [('head', 'eyes', 'jaw', 0.0)] if not el else [('head', 'eyes', 'jaw', -0.11), ('head2', 'eyes2', 'jaw2', 0.11)]
    for hb, eb, jb, cx in heads:
        c.bone(hb, (cx, -0.33, 0.68), 'body')
        c.bone(eb, (cx, -0.55, 0.79), hb)
        c.bone(jb, (cx, -0.47, 0.67), hb)
    canine_body(c, pal, fur, bulk=1.18, tail_col=side_c)
    k = 1.0 if not el else 0.82
    for hb, eb, jb, cx in heads:
        neck(c, ['body', hb], cx, fur, pale, k=k * 1.05, mane=side_c)
        canine_head(c, hb, eb, jb, cx, k, pal, '#ffb02e', ear=True, snarl=True)
        for j in range(4):  # flame mane
            ang = math.pi * (0.2 + 0.6 * j / 3)
            c.flame(hb, f'mane{hb}{j}', (cx + 0.1 * k * math.cos(ang), -0.36, 0.78 + 0.06 * math.sin(ang)), 0.2 * k,
                    0.045 * k, lean=(0.06 * math.cos(ang), 0.16, 0))
        if el:
            for s in (-1, 1):
                c.tube(hb, f'horn{hb}{s}', [(cx + s * 0.05 * k, -0.42, 0.86), (cx + s * 0.1 * k, -0.37, 0.95),
                                            (cx + s * 0.12 * k, -0.3, 0.98)], 0.022 * k, '#d8b46a', taper=0.25)
    c.bone('flame_tail', (0, 0.72, 0.42), 'tail3')
    c.flame('flame_tail', 'tail_flame', (0, 0.72, 0.42), 0.26, 0.06, lean=(0, 0.12, 0))
    for s in (-1, 1):
        c.tube('body', f'collar{s}', [(s * 0.14, -0.28, 0.56), (s * 0.08, -0.33, 0.66), (0, -0.34, 0.7)], 0.022,
               '#5a2420' if not el else '#c99a3e')
    if el:
        c.gem('body', 'brand_gem', (0, -0.36, 0.6), (0, -1, 0.3), 0.035, 0.07, '#ffd1a1', '#ff5a1a')

    def extra(a, clip, f, t, i, names):
        if 'head2' not in names:
            return
        # The second head is a lagging, mirrored twin of the first: it looks the other way in Idle, snaps a beat
        # after its brother in Attack and howls a beat later in Cast, so the pair reads as two minds.
        tt = min(t, DIE_HOLD) if clip == 'Die' else t
        q = a.anim.at(clip, tt - 0.04)
        a.r('head2', f, (q.hr[0] + (3 * math.sin(math.tau * t + 2) if clip == 'Idle' else 0), -q.hr[1], -q.hr[2]))
        a.r('jaw2', f, (q.jaw, 0, 0))
        a.s('eyes2', f, (1, 1, max(0.08, a.anim.at(clip, tt - 0.08).blink)))
    return c.finish('quad', extra)


BUILDERS = {'ice_wolf': ice_wolf, 'elite_ice_wolf': ice_wolf, 'hellhound': hellhound, 'elite_hellhound': hellhound}

if __name__ == '__main__':
    eid = sys.argv[sys.argv.index('--') + 1]
    BUILDERS[eid](eid)
