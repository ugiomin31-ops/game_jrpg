"""Sculpted bugs and sea creatures (monster v3): frost_spider, rhino_beetle / elite_rhino_beetle, sand_scorpion,
coral_crab / elite_coral_crab, jellyfish. Legs are chunky and few; only two natural eyes (no spider eye clusters).
Run through the production runner: blender -b --factory-startup -P Blender/enemies_a/generate_all.py -- --asset frost_spider
"""
import math
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from sculpt_kit import Sculpt, A, lerp_col, vgrad  # noqa: E402,F401
from mathutils import Vector  # noqa: E402


def walker_legs(c, ys, hip_x, hip_z, reach, lift, r, color, foot_col=None, splay=0.07, cuff=None, start=1):
    """Pairs of chunky arthropod legs on bones legN.L/R: hip -> raised knee -> planted foot."""
    for s, side in ((-1, 'R'), (1, 'L')):
        for k, y in enumerate(ys):
            b = f'leg{k + start}.{side}'
            sp = (k - (len(ys) - 1) / 2) * splay
            hip = (s * hip_x, y, hip_z)
            knee = (s * (hip_x + reach * 0.55), y + sp * 0.6, hip_z + lift)
            foot = (s * (hip_x + reach), y + sp, 0.04)
            c.bone(b, hip, 'body')
            c.limb(b, [hip, knee, foot], [r, r * 0.9, r * 0.8], color)
            c.blob(b, (foot[0], foot[1], 0.035), (r * 1.1, r * 1.3, r * 0.8), foot_col or color)
            if cuff:
                c.blob(b, knee, (r * 1.35, r * 1.35, r * 1.2), cuff, weight=1.2)


def frost_spider(eid):
    """서리 거미 — a stocky snow spider: frosted pale head, a round navy abdomen frosted with white fur and ice
    crystals, three pairs of thick legs with white fur cuffs and snow-boot feet, two calm ice-blue eyes."""
    c = Sculpt(eid, tris=8000)
    shell, navy, white = '#8fc8ee', '#2c4f8a', '#f2faff'
    c.bone('body', (0, 0.05, 0.3)); c.bone('head', (0, -0.12, 0.33), 'body'); c.bone('eyes', (0, -0.25, 0.38), 'head')
    c.bone('tail1', (0, 0.15, 0.38), 'body')
    c.blob('head', (0, -0.13, 0.33), (0.15, 0.14, 0.12), vgrad(0.25, '#5f93c8', 0.45, shell))
    c.blob('tail1', (0, 0.2, 0.42), (0.22, 0.24, 0.2), vgrad(0.3, navy, 0.62, '#4a74b8'))
    c.tufts('body', (0, 0.0, 0.42), [(0.6, 0.2, 0.6), (-0.6, 0.2, 0.6), (0, 0.4, 0.9), (0.9, 0.0, 0.0), (-0.9, 0.0, 0.0)], 0.08,
            0.045, white, weight=1.3)
    for k in range(6):
        a = math.tau * k / 6
        c.tuft('tail1', (0.12 * math.cos(a), 0.22 + 0.1 * math.sin(a), 0.58), (math.cos(a) * 0.6, math.sin(a) * 0.6, 0.6),
               0.07, 0.04, white)
    for k, (x, y, z, dx, dy) in enumerate(((-0.1, 0.16, 0.6, -0.4, -0.2), (0.1, 0.16, 0.6, 0.4, -0.2), (0, 0.3, 0.6, 0, 0.5))):
        c.gem('tail1', f'ice{k}', (x, y, z), (dx, dy, 1), 0.035, 0.12, '#d8fbff', '#3fb2ea', mat='M_Clear')
    for s in (-1, 1):
        c.blob('eyes', (s * 0.06, -0.225, 0.41), (0.045, 0.035, 0.018), '#5f93c8')
        c.eye('eyes', (s * 0.06, -0.235, 0.38), (s * 0.4, -1, 0.05), 0.03, '#2ab8f0')
    c.paint((0, -0.27, 0.3), (0.035, 0.015, 0.01), '#1d3a66')
    walker_legs(c, (-0.16, 0.0, 0.16), 0.13, 0.3, 0.32, 0.14, 0.048, navy, foot_col=white, cuff=white, splay=0.12)
    return c.finish('crawler')


def rhino_beetle(eid):
    """장수풍뎅이 / 강철 투구왕 — an armoured beetle: glossy domed wing cases with a seam, a broad pronotum,
    a long upcurved horn ending in a fork, three pairs of sturdy legs; the elite is steel-blue with gold edging."""
    c = Sculpt(eid, tris=9000)
    el = c.elite
    shell, dark = ('#2f6d4b', '#1c2b22') if not el else ('#3d6fa0', '#1a2230')

    def case(p):
        if abs(p.x) < 0.012 and p.y > -0.05:
            return dark
        gloss = max(0.0, 1 - ((p.x - 0.07 * (1 if p.x > 0 else -1)) ** 2 + (p.y + 0.02) ** 2) / 0.006)
        return lerp_col(shell, '#ffffff', 0.35 * gloss) if p.z > 0.45 else shell
    c.bone('body', (0, 0.05, 0.3)); c.bone('head', (0, -0.22, 0.32), 'body'); c.bone('eyes', (0, -0.34, 0.34), 'head')
    for s in (-1, 1):
        c.blob('body', (s * 0.1, 0.12, 0.36), (0.14, 0.27, 0.17), case)
    c.blob('body', (0, -0.12, 0.38), (0.19, 0.14, 0.15), shell)
    c.blob('body', (0, 0.05, 0.22), (0.17, 0.28, 0.09), dark)
    c.limb('body', [(0, -0.16, 0.48), (0, -0.25, 0.58)], [0.05, 0.02], dark)                     # thorax horn
    c.blob('head', (0, -0.28, 0.31), (0.12, 0.1, 0.1), dark)
    horn = [(0, -0.33, 0.36), (0, -0.42, 0.44), (0, -0.48, 0.58), (0, -0.47, 0.72)]
    c.limb('head', horn, [0.06, 0.05, 0.035, 0.022], '#3b2a22' if not el else '#2b3242')
    for s in (-1, 1):
        c.cone_to('head', f'fork{s}', horn[-1], (s * 0.07, -0.45, 0.8), 0.022, '#e3b64c' if el else '#3b2a22')
        c.eye('eyes', (s * 0.08, -0.33, 0.34), (s * 0.7, -0.7, 0.05), 0.026, '#ffcf2e')
        c.tube('head', f'antenna{s}', [(s * 0.06, -0.36, 0.38), (s * 0.13, -0.42, 0.44)], 0.01, dark)
        c.orb('head', f'antenna_club{s}', (s * 0.14, -0.43, 0.45), (0.024, 0.024, 0.02), '#d9a33a')
    walker_legs(c, (-0.16, 0.0, 0.16), 0.15, 0.25, 0.32, 0.12, 0.048, dark, foot_col=lerp_col(dark, shell, 0.4), splay=0.12)
    if el:
        for s in (-1, 1):
            c.tube('body', f'gold_edge{s}', [(s * 0.02, -0.07, 0.52), (s * 0.2, 0.05, 0.44), (s * 0.24, 0.22, 0.34),
                                             (s * 0.14, 0.38, 0.3)], 0.014, '#e3b64c')
        c.gem('body', 'shell_gem', (0, 0.14, 0.55), (0, 0.2, 1), 0.05, 0.1, '#9fffe9', '#2fb39a')
    return c.finish('crawler')


def sand_scorpion(eid):
    """모래 전갈 — a desert scorpion: banded sandy carapace, a segmented tail arching over its back to a purple
    venom bulb and stinger, heavy pincers with real claw fingers, three pairs of short legs."""
    c = Sculpt(eid, tris=10000)
    sand, plate = '#e0a04a', '#a5582a'

    def bands(p):
        return plate if math.sin(p.y * 32) > 0.55 else sand
    c.bone('body', (0, 0.05, 0.25)); c.bone('head', (0, -0.2, 0.27), 'body'); c.bone('eyes', (0, -0.3, 0.33), 'head')
    c.limb('body', [(0, -0.12, 0.26), (0, 0.06, 0.27), (0, 0.24, 0.26)], [0.17, 0.16, 0.12], bands)
    c.blob('body', (0, 0.05, 0.18), (0.14, 0.24, 0.06), '#f5d9a0')
    c.blob('head', (0, -0.23, 0.27), (0.13, 0.11, 0.09), sand)
    for s in (-1, 1):
        c.blob('eyes', (s * 0.05, -0.27, 0.355), (0.03, 0.025, 0.012), plate)
        c.eye('eyes', (s * 0.05, -0.28, 0.33), (s * 0.3, -0.8, 0.5), 0.022, '#1a1418', iris_edge=0.3)
    tail = [(0, 0.3, 0.28), (0, 0.42, 0.4), (0, 0.45, 0.56), (0, 0.4, 0.7), (0, 0.3, 0.78)]
    for k in range(4):
        b = f'tail{k + 1}'
        c.bone(b, tail[k], 'body' if k == 0 else f'tail{k}')
        c.limb(b, [tail[k], tail[k + 1]], [0.085 - k * 0.012, 0.075 - k * 0.012], sand if k % 2 == 0 else plate)
    c.blob('tail4', (0, 0.27, 0.79), (0.07, 0.07, 0.065), '#9b45d6')
    c.cone_to('tail4', 'stinger', (0, 0.22, 0.78), (0, 0.16, 0.71), 0.03, '#4a2a1c')
    for s, side in ((-1, 'R'), (1, 'L')):
        c.bone('arm.' + side, (s * 0.15, -0.22, 0.27), 'body')
        c.limb('arm.' + side, [(s * 0.15, -0.22, 0.27), (s * 0.27, -0.32, 0.3), (s * 0.31, -0.43, 0.3)], [0.05, 0.045, 0.045], plate)
        c.blob('arm.' + side, (s * 0.32, -0.5, 0.3), (0.075, 0.09, 0.06), sand)
        c.limb('arm.' + side, [(s * 0.35, -0.55, 0.31), (s * 0.35, -0.66, 0.32)], [0.04, 0.02], plate)
        c.limb('arm.' + side, [(s * 0.28, -0.56, 0.3), (s * 0.29, -0.64, 0.31)], [0.03, 0.016], plate)
    walker_legs(c, (-0.06, 0.07, 0.2), 0.14, 0.24, 0.3, 0.12, 0.036, plate, foot_col=sand, splay=0.1)

    def extra(a, clip, f, t, i, names):
        hit = max(0.0, 1 - abs(t - 0.4) / 0.16)
        wind = max(0.0, 1 - abs(t - 0.2) / 0.16)
        if clip == 'Attack':
            for k, w in ((1, 10), (2, 22), (3, 28), (4, 30)):
                a.r(f'tail{k}', f, (-8 * wind * k / 4 + w * hit, 0, 0))
    return c.finish('crawler', extra)


def coral_crab(eid):
    """산호 소라게 / 거대 산호 집게 — a hermit crab in a pale spiral conch grown over with red coral: orange crab body,
    eyes on stalks, two claws (the elite has one huge armoured claw), three pairs of sturdy legs."""
    c = Sculpt(eid, tris=10000)
    el = c.elite
    shell_c = vgrad(0.2, '#d9b48a', 0.8, '#fff1dc') if not el else vgrad(0.2, '#b98a5a', 0.8, '#f1d29c')
    red, light = ('#e45c3c', '#f58358') if not el else ('#cf3a1f', '#ef5a32')
    coral = '#e8503a' if not el else '#ff8a3a'
    c.bone('body', (0, 0.04, 0.3)); c.bone('eyes', (0, -0.3, 0.42), 'body')
    def whorl(p):  # pale conch with a darker spiral groove and banding
        a = math.atan2(p.y - 0.1, p.x)
        if math.sin(a + p.z * 22) > 0.88:
            return lerp_col(shell_c(p), '#7a5a40', 0.55)
        return shell_c(p)
    for k in range(14):  # spiral conch: body whorl plus a tightening spire
        t = k / 13
        a = t * math.tau * 1.8
        r = 0.28 * (1 - 0.82 * t)
        rr = 0.13 * (1 - t)
        c.blob('body', (rr * math.cos(a), 0.1 + rr * math.sin(a) + 0.05 * t, 0.34 + 0.5 * t ** 0.8), (r, r, r * 0.8), whorl)
    c.blob('body', (0, -0.16, 0.24), (0.17, 0.12, 0.11), light)                                   # crab body in the opening
    c.paint((0, -0.27, 0.22), (0.05, 0.02, 0.012), '#6a1a1a')
    for s in (-1, 1):
        c.limb('eyes', [(s * 0.06, -0.24, 0.3), (s * 0.08, -0.29, 0.42)], [0.022, 0.018], light)
        c.eye('eyes', (s * 0.085, -0.3, 0.44), (s * 0.3, -1, 0.15), 0.035, '#2a2030', iris_edge=0.45)
    for k, (yaw, h) in enumerate(((-30, 0.26), (40, 0.22), (160, 0.24))):
        a = math.radians(yaw)
        base = (0.14 * math.sin(a), 0.1 + 0.12 * math.cos(a), 0.56)
        tip = (base[0] * 1.6, base[1] + 0.04, base[2] + h)
        c.tube('body', f'coral{k}', [base, tip], 0.04, coral, taper=0.45)
        for j in range(3):
            mid = Vector(base).lerp(Vector(tip), 0.35 + 0.22 * j)
            c.tube('body', f'coral{k}_{j}', [tuple(mid), tuple(mid + Vector(((j - 1) * 0.1, 0.03, 0.1)))], 0.024, coral, taper=0.4)
    for s, side in ((-1, 'R'), (1, 'L')):
        big = el and s > 0
        k = 1.7 if big else 1.0
        c.bone('arm.' + side, (s * 0.14, -0.2, 0.22), 'body')
        c.limb('arm.' + side, [(s * 0.14, -0.2, 0.22), (s * 0.22, -0.28, 0.2), (s * 0.24, -0.34, 0.16)], [0.04 * k, 0.04 * k, 0.04 * k], red)
        c.blob('arm.' + side, (s * 0.25, -0.4, 0.15), (0.075 * k, 0.09 * k, 0.065 * k), light)
        c.limb('arm.' + side, [(s * (0.27 + 0.02 * k), -0.44 - 0.04 * k, 0.17), (s * (0.27 + 0.02 * k), -0.5 - 0.08 * k, 0.17)],
               [0.035 * k, 0.015 * k], light)
        c.limb('arm.' + side, [(s * 0.22, -0.44 - 0.03 * k, 0.12), (s * 0.23, -0.48 - 0.06 * k, 0.14)], [0.028 * k, 0.012 * k], red)
        if big:
            for j in range(3):
                c.cone_to('arm.' + side, f'claw_spike{j}', (s * 0.3, -0.38 + j * 0.05, 0.25), (s * 0.34, -0.38 + j * 0.05, 0.32), 0.02, '#f1d29c')
    walker_legs(c, (-0.08, 0.04, 0.16), 0.16, 0.2, 0.26, 0.1, 0.036, red, foot_col=light, splay=0.12)
    return c.finish('crawler')


def jellyfish(eid):
    """물방울 해파리 — a translucent drifting jellyfish: a soft bell with a frilled rim, a glowing core, flowing
    tentacles and four frilly oral arms, two small dark eyes."""
    c = Sculpt(eid, tris=8000, material='M_Clear', ao=0.35)
    bell = vgrad(0.95, '#5fb8f0', 1.25, '#c8f0ff')
    c.bone('body', (0, 0, 1.05)); c.bone('eyes', (0, -0.22, 1.05), 'body')
    c.blob('body', (0, 0, 1.06), (0.26, 0.26, 0.15), bell)
    c.blob('body', (0, 0, 1.14), (0.2, 0.2, 0.12), bell)
    for k in range(12):
        a = math.tau * k / 12
        c.blob('body', (0.25 * math.cos(a), 0.25 * math.sin(a), 0.97), (0.06, 0.06, 0.035), '#8fd8ff')
    c.add('body', A.sphere('core', r=0.09, loc=(0, 0, 1.06), color='#c8f6ff', mat='M_Emit', seg=16, rings=10))
    for s in (-1, 1):
        c.eye('eyes', (s * 0.08, -0.225, 1.05), (s * 0.3, -1, 0.0), 0.028, '#10203a', iris_edge=0.3, sclera='#14223e')
    for k in range(6):
        a = math.tau * (k + 0.5) / 6
        root = Vector((0.18 * math.cos(a), 0.18 * math.sin(a), 0.97))
        b = f'tentacle{k + 1}'
        c.bone(b, tuple(root), 'body')
        pts = [tuple(root + Vector((0.03 * math.sin(j * 1.7 + k) * math.cos(a), 0.03 * math.sin(j * 1.7 + k) * math.sin(a), -0.11 * j)))
               for j in range(6)]
        c.limb(b, pts, [0.03, 0.025, 0.02, 0.016, 0.012, 0.008], '#9fe0ff')
    for k in range(4):
        a = math.tau * k / 4 + 0.3
        root = Vector((0.05 * math.cos(a), 0.05 * math.sin(a), 0.95))
        pts = [tuple(root + Vector((0.04 * math.cos(a) * j, 0.04 * math.sin(a) * j, -0.08 * j))) for j in range(4)]
        c.limb('body', pts, [0.045, 0.04, 0.03, 0.015], '#d6a8ff')
    return c.finish('float')


BUILDERS = {'frost_spider': frost_spider, 'rhino_beetle': rhino_beetle, 'elite_rhino_beetle': rhino_beetle,
            'sand_scorpion': sand_scorpion, 'coral_crab': coral_crab, 'elite_coral_crab': coral_crab, 'jellyfish': jellyfish}

if __name__ == '__main__':
    eid = sys.argv[sys.argv.index('--') + 1]
    BUILDERS[eid](eid)
