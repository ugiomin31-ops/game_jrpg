"""Sculpted flyers (monster v3): bat / elite_bat / grave_bat, phoenix, fire_drake / elite_fire_drake,
killer_bee, harpy.
Run through the production runner: blender -b --factory-startup -P Blender/enemies_a/generate_all.py -- --asset bat
"""
import math
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from sculpt_kit import Sculpt, A, lerp_col, vgrad  # noqa: E402,F401
from monster_kit import attack_env, cast_env, window  # noqa: E402
from mathutils import Vector  # noqa: E402


def _scallop(a, b, root, k=0.28):
    """Point between finger tips a and b pulled toward the wing root (the membrane's scalloped edge)."""
    a, b, root = Vector(a), Vector(b), Vector(root)
    m = (a + b) / 2
    return tuple(m + (root - m) * k)


def bat_wing(c, bone, s, shoulder, wrist, tips, hip, root, arm_col, mem_col, mem_edge, r=0.035):
    """Bat-style wing on `bone`: an organic arm to the wrist, rigid finger bones, scalloped membrane."""
    elbow = Vector(shoulder).lerp(Vector(wrist), 0.5) + Vector((0, 0.03, 0.08))
    c.limb(bone, [shoulder, tuple(elbow), wrist], [r, r * 0.8, r * 0.6], arm_col)
    for k, t in enumerate(tips):
        c.tube(bone, f'finger{s:+d}{k}', [wrist, t], r * 0.28, arm_col, taper=0.4)
    edge = [shoulder, wrist, tips[0]]
    for a, b in zip(tips, tips[1:]):
        edge += [_scallop(a, b, root), b]
    edge += [_scallop(tips[-1], hip, root, 0.2), hip]
    c.membrane(bone, f'membrane{s:+d}', root, edge, mem_col, edge_color=mem_edge)
    c.gem(bone, f'thumb{s:+d}', wrist, (s * 0.2, -0.6, 0.8), r * 0.35, r * 1.4, '#e8dcc8', '#b8a890', mat='M_Toon')


def feather_wing(c, bone, s, shoulder, span, droop, base_col, tip_col, covert_col, arm_col, feathers=7, r=0.03):
    """Bird wing on `bone`: a slim organic arm along the leading edge, a fan of primary feathers (scalloped
    membrane) and a shorter covert layer in another colour on top."""
    sh = Vector(shoulder)
    wrist = sh + Vector((s * span * 0.55, 0.03, span * 0.08))
    tip = sh + Vector((s * span, 0.06, span * 0.05 - droop * 0.2))
    c.limb(bone, [tuple(sh), tuple(sh.lerp(wrist, 0.5) + Vector((0, 0, 0.02))), tuple(wrist)], [r, r * 0.8, r * 0.6], arm_col)
    root = sh + Vector((s * span * 0.35, 0.05, -droop * 0.45))
    edge = [tuple(sh), tuple(wrist), tuple(tip)]
    for k in range(1, feathers + 1):
        t = k / feathers
        a = math.radians(-8 - 95 * t)
        L = span * (0.95 - 0.45 * t)
        p = sh + Vector((s * L * math.cos(a) * 0.9 + s * span * 0.1 * (1 - t), 0.06, L * math.sin(a) * 0.55 - droop * t))
        notch = (Vector(edge[-1]) + p) / 2 + (root - (Vector(edge[-1]) + p) / 2) * 0.12
        edge += [tuple(notch), tuple(p)]
    edge.append(tuple(sh + Vector((s * 0.03, 0.04, -droop * 0.9))))
    c.membrane(bone, f'feathers{s:+d}', tuple(root), edge, base_col, thick=0.008, edge_color=tip_col)
    cov = [tuple(sh + Vector((0, -0.01, 0.0))), tuple(wrist + Vector((0, -0.01, 0)))]
    for k in range(1, 5):
        t = k / 4
        cov.append(tuple(wrist.lerp(sh, t) + Vector((0, -0.012, -span * 0.22 * (1 - abs(2 * t - 1) * 0.5)))))
    c.membrane(bone, f'coverts{s:+d}', tuple(sh.lerp(wrist, 0.5) + Vector((0, -0.012, -span * 0.08))), cov, covert_col,
               thick=0.008)


def fan_tail(c, bone, base, length, spread, base_col, tip_col, n=6, droop=0.6):
    """Fanned tail feathers as one scalloped membrane."""
    b = Vector(base)
    edge = []
    for k in range(n + 1):
        a = math.radians(-spread / 2 + spread * k / n)
        p = b + Vector((math.sin(a) * length, math.cos(a) * length, -droop * length * math.cos(a) * 0.6))
        if edge:
            m = (Vector(edge[-1]) + p) / 2
            edge.append(tuple(m + (b - m) * 0.1))
        edge.append(tuple(p))
    c.membrane(bone, 'tail_fan', tuple(b), edge, base_col, thick=0.008, edge_color=tip_col)


def bat(eid):
    """동굴 박쥐 / 밤의 박쥐 군주 / 무덤 박쥐 — a furry bat: big pointed ears, pug snout with a nose leaf,
    small fangs, membrane wings on finger bones; the lord wears a crown, the grave bat is pale and ghostly."""
    c = Sculpt(eid, tris=7000)
    el, grave = eid == 'elite_bat', eid == 'grave_bat'
    fur, chest, skin = ('#4b3b6b', '#7b6890', '#8a6078') if not grave else ('#4e6466', '#8aa4a0', '#7a8a86')
    if el:
        fur, chest = '#3c2450', '#7a4a6a'
    mem, mem_edge = ('#6b4a7d', '#3a2549') if not grave else ('#7a9a94', '#3e5654')
    if el:
        mem, mem_edge = '#8a2a3a', '#3a1020'
    c.bone('body', (0, 0, 1.0)); c.bone('head', (0, -0.03, 1.12), 'body')
    c.bone('eyes', (0, -0.16, 1.18), 'head'); c.bone('jaw', (0, -0.13, 1.08), 'head')
    c.blob('body', (0, 0.02, 0.98), (0.13, 0.12, 0.16), fur)
    c.blob('body', (0, -0.07, 1.0), (0.1, 0.05, 0.12), chest)
    c.blob('body', (0, 0.0, 0.86), (0.09, 0.08, 0.07), fur)
    c.tufts('body', (0, -0.04, 1.08), [(0.6, -0.4, -0.3), (-0.6, -0.4, -0.3), (0, -0.6, -0.6)], 0.07, 0.035, chest)
    c.blob('head', (0, -0.05, 1.16), (0.12, 0.11, 0.1), fur)
    c.limb('head', [(0, -0.12, 1.13), (0, -0.18, 1.12)], [0.055, 0.04], skin)
    c.blob('head', (0, -0.215, 1.14), (0.024, 0.01, 0.03), lerp_col(skin, '#3a2030', 0.4))        # nose leaf
    c.paint((0, -0.205, 1.125), (0.02, 0.01, 0.008), '#2a1520')                                   # nostrils
    c.limb('jaw', [(0, -0.11, 1.09), (0, -0.16, 1.09)], [0.04, 0.028], skin)
    for s in (-1, 1):
        c.spike('jaw', f'fang{s}', (s * 0.016, -0.18, 1.1), (s * 0.016, -0.185, 1.075), 0.007, '#f6efe0')
        c.blob('eyes', (s * 0.05, -0.14, 1.2), (0.035, 0.03, 0.016), fur)                         # brow
        c.eye('eyes', (s * 0.05, -0.145, 1.18), (s * 0.4, -1, 0.05), 0.02, '#f0c040' if not grave else '#9fe8d8')
    for s, side in ((-1, 'R'), (1, 'L')):
        c.bone('ear.' + side, (s * 0.07, -0.04, 1.23), 'head')
        for k, (x, z, w, h) in enumerate(((0.08, 1.26, 0.06, 0.06), (0.105, 1.32, 0.045, 0.05), (0.125, 1.38, 0.025, 0.035))):
            c.blob('ear.' + side, (s * x, -0.03, z), (w, 0.02, h), fur, rot=(0, s * 18, 0))
        c.paint((s * 0.1, -0.055, 1.3), (0.035, 0.02, 0.05), lerp_col(skin, '#d08aa8', 0.4))
        c.bone('wing.' + side, (s * 0.1, 0.02, 1.06), 'body')
        tips = [(s * 0.76, 0.0, 1.26), (s * 0.82, 0.02, 0.98), (s * 0.6, 0.04, 0.8)]
        bat_wing(c, 'wing.' + side, s, (s * 0.1, 0.02, 1.08), (s * 0.48, 0.03, 1.13), tips, (s * 0.1, 0.05, 0.88),
                 (s * 0.32, 0.04, 1.02), skin, mem, mem_edge)
        c.bone('leg.' + side, (s * 0.05, 0.02, 0.86), 'body')
        c.limb('leg.' + side, [(s * 0.05, 0.02, 0.86), (s * 0.06, 0.03, 0.78)], [0.025, 0.02], skin)
        for j in range(3):
            c.spike('leg.' + side, f'toe{side}{j}', (s * 0.06 + (j - 1) * 0.012, 0.03, 0.775), (s * 0.06 + (j - 1) * 0.014, 0.0, 0.76),
                    0.006, '#2a1a24')
    if el:
        for k in range(5):
            a = math.pi * (0.15 + 0.7 * k / 4)
            c.cone_to('head', f'crown{k}', (0.07 * math.cos(a), -0.03 + 0.03 * math.sin(a), 1.25),
                      (0.08 * math.cos(a), -0.03 + 0.035 * math.sin(a), 1.32), 0.016, '#e8b84a')
        c.gem('head', 'crown_gem', (0, -0.08, 1.27), (0, -0.4, 1), 0.016, 0.035, '#ff7a9a', '#a01a3a')
    return c.finish('fly')


def phoenix(eid):
    """새끼 불사조 — a plump fledgling phoenix: flame-orange plumage fading to a gold breast, a tufted
    crest tipped with fire, feather-fan wings and long tail plumes with burning tips."""
    c = Sculpt(eid, tris=7000)
    plume = vgrad(0.85, '#ffd36a', 1.2, '#f2601e')
    c.bone('body', (0, 0, 1.0)); c.bone('head', (0, -0.08, 1.15), 'body'); c.bone('eyes', (0, -0.18, 1.2), 'head')
    c.bone('crest', (0, -0.05, 1.3), 'head'); c.bone('tail1', (0, 0.14, 0.94), 'body')
    c.blob('body', (0, 0.02, 1.0), (0.14, 0.17, 0.15), plume)
    c.blob('body', (0, -0.08, 0.97), (0.1, 0.07, 0.11), '#ffe08a', weight=1.3)
    c.blob('head', (0, -0.09, 1.19), (0.1, 0.1, 0.095), '#f57a2a')
    c.tufts('head', (0, -0.06, 1.26), [(0, 0.3, 1), (0.4, 0.3, 0.9), (-0.4, 0.3, 0.9)], 0.11, 0.04, '#ff9a3a')
    for s in (-1, 1):
        c.tuft('head', (s * 0.08, -0.12, 1.15), (s * 0.8, 0.6, -0.2), 0.06, 0.03, '#ffb44a')
        c.blob('eyes', (s * 0.052, -0.165, 1.225), (0.03, 0.025, 0.012), '#e5561a')
        c.eye('eyes', (s * 0.05, -0.17, 1.2), (s * 0.45, -1, 0.05), 0.022, '#3a1c10', iris_edge=0.4)
    c.cone_to('head', 'beak', (0, -0.18, 1.17), (0, -0.25, 1.15), 0.03, '#ffcf3a')
    c.cone_to('head', 'beak_low', (0, -0.175, 1.145), (0, -0.22, 1.14), 0.018, '#e8a628')
    for k in range(3):
        c.flame('crest', f'crest_fire{k}', (0.04 * (k - 1), -0.04, 1.33), 0.12, 0.025, lean=(0.04 * (k - 1), 0.06, 0))
    for s, side in ((-1, 'R'), (1, 'L')):
        c.bone('wing.' + side, (s * 0.12, 0.02, 1.06), 'body')
        feather_wing(c, 'wing.' + side, s, (s * 0.12, 0.03, 1.06), 0.42, 0.12, '#f2601e', '#ffd36a', '#ff9a3a', '#f57a2a', r=0.022)
        c.bone('leg.' + side, (s * 0.05, 0.02, 0.88), 'body')
        c.limb('leg.' + side, [(s * 0.05, 0.02, 0.88), (s * 0.055, 0.0, 0.8)], [0.022, 0.016], '#c87a2a')
        for j in range(3):
            c.spike('leg.' + side, f'talon{side}{j}', (s * 0.055, 0.0, 0.8), (s * 0.055 + (j - 1) * 0.02, -0.04, 0.78), 0.008, '#5a3018')
    fan_tail(c, 'tail1', (0, 0.14, 0.95), 0.36, 50, '#f2601e', '#ffd36a', n=5)
    for k in range(3):
        a = math.radians(-18 + k * 18)
        c.flame('tail1', f'plume_fire{k}', (math.sin(a) * 0.36, 0.14 + math.cos(a) * 0.36, 0.95 - 0.2), 0.12, 0.025,
                lean=(0, 0.06, 0))
    c.follow['crest'] = 1.5  # the burning crest flicks back on every wing beat

    def extra(a, clip, f, t, i, names):
        if clip == 'Cast':  # crest fire roars up with the release
            g, sh, burst, pop, settle = cast_env(t)
            k = 1 + 0.2 * g + 0.5 * burst
            a.s('crest', f, (1 + 0.4 * (k - 1), 1 + 0.4 * (k - 1), k))
    return c.finish('fly', extra)


def fire_drake(eid):
    """불꽃 드레이크 / 홍염 비룡 — a young fire dragon standing upright: pear-shaped body with cream belly
    plates, horned head with brow ridges and slit-pupil eyes, small clawed arms, digitigrade legs, a spaded tail
    and leathery wings; the elite is a crimson wyvern with gold plates and more horns."""
    c = Sculpt(eid, tris=10000)
    el = c.elite
    scale_c, dark, bellyc = ('#d8452a', '#8a2418', '#f2d29a') if not el else ('#9a1a26', '#4a0c14', '#e8b84a')
    k = 1.0 if not el else 1.12
    S = lambda x, y, z: (x * k, y * k, z * k)  # noqa: E731

    def scales(p):
        if p.y < -0.08 * k and 0.25 * k < p.z < 0.62 * k:
            band = math.sin(p.z / k * 60) > -0.6
            return bellyc if band else lerp_col(bellyc, dark, 0.4)
        return lerp_col(scale_c, dark, (p.z / k - 0.75) / 0.4) if p.z / k > 0.75 else scale_c
    c.bone('body', S(0, 0, 0.45)); c.bone('head', S(0, -0.08, 0.74), 'body'); c.bone('eyes', S(0, -0.22, 0.86), 'head')
    c.bone('jaw', S(0, -0.2, 0.78), 'head')
    c.blob('body', S(0, 0.03, 0.42), (0.2 * k, 0.18 * k, 0.23 * k), scales)
    c.blob('body', S(0, -0.04, 0.58), (0.15 * k, 0.13 * k, 0.12 * k), scales)
    c.blob('body', S(0, -0.12, 0.42), (0.14 * k, 0.06 * k, 0.17 * k), scales)
    c.limb('head', [S(0, -0.04, 0.66), S(0, -0.08, 0.76)], [0.1 * k, 0.09 * k], scales)
    c.blob('head', S(0, -0.12, 0.85), (0.12 * k, 0.12 * k, 0.1 * k), scale_c)
    c.limb('head', [S(0, -0.2, 0.84), S(0, -0.28, 0.82), S(0, -0.33, 0.81)], [0.075 * k, 0.06 * k, 0.05 * k], scale_c)
    c.limb('jaw', [S(0, -0.18, 0.78), S(0, -0.3, 0.77)], [0.055 * k, 0.04 * k], bellyc)
    for s in (-1, 1):
        c.paint(S(s * 0.02, -0.355, 0.83), (0.012, 0.008, 0.008), '#3a0a08')            # nostrils
        c.blob('head', S(s * 0.06, -0.21, 0.905), (0.045 * k, 0.04 * k, 0.022 * k), dark)  # brow ridge
        c.eye('eyes', S(s * 0.062, -0.215, 0.875), (s * 0.55, -1, 0.05), 0.026 * k, '#ffcf3a', slit=True)
        c.tube('head', f'horn{s}', [S(s * 0.07, -0.08, 0.93), S(s * 0.11, 0.0, 0.99), S(s * 0.12, 0.08, 1.0)], 0.028 * k,
               '#3a2420' if not el else '#e8d6a8', taper=0.15)
        if el:
            c.tube('head', f'horn_b{s}', [S(s * 0.1, -0.05, 0.88), S(s * 0.16, 0.0, 0.9), S(s * 0.19, 0.05, 0.94)], 0.018 * k,
                   '#e8d6a8', taper=0.15)
        c.spike('jaw', f'tooth{s}', S(s * 0.03, -0.3, 0.79), S(s * 0.03, -0.31, 0.765), 0.008 * k, '#fff4e0')
    for s, side in ((-1, 'R'), (1, 'L')):
        c.bone('arm.' + side, S(s * 0.15, -0.06, 0.56), 'body')
        c.limb('arm.' + side, [S(s * 0.15, -0.06, 0.56), S(s * 0.22, -0.12, 0.48), S(s * 0.22, -0.18, 0.42)],
               [0.05 * k, 0.04 * k, 0.035 * k], scale_c)
        for j in range(3):
            c.spike('arm.' + side, f'claw{side}{j}', S(s * 0.22 + (j - 1) * 0.02, -0.2, 0.41), S(s * 0.22 + (j - 1) * 0.025, -0.24, 0.38),
                    0.01 * k, '#f4e6c8')
        c.bone('leg.' + side, S(s * 0.11, 0.03, 0.3), 'body')
        c.blob('leg.' + side, S(s * 0.12, 0.04, 0.26), (0.09 * k, 0.12 * k, 0.12 * k), scale_c)
        c.limb('leg.' + side, [S(s * 0.13, 0.08, 0.18), S(s * 0.13, 0.1, 0.09), S(s * 0.13, 0.03, 0.04)],
               [0.06 * k, 0.045 * k, 0.045 * k], scale_c)
        c.blob('leg.' + side, S(s * 0.13, -0.03, 0.03), (0.06 * k, 0.09 * k, 0.03 * k), dark)
        c.bone('wing.' + side, S(s * 0.09, 0.1, 0.62), 'body')
        tips = [S(s * 0.5, 0.2, 0.98), S(s * 0.6, 0.24, 0.72), S(s * 0.46, 0.24, 0.5)]
        bat_wing(c, 'wing.' + side, s, S(s * 0.09, 0.1, 0.64), S(s * 0.34, 0.16, 0.86), tips, S(s * 0.12, 0.14, 0.45),
                 S(s * 0.28, 0.16, 0.68), dark, '#ff8a4a' if not el else '#c8323a', '#8a2418' if not el else '#3a0810',
                 r=0.04 * k)
    for kk, p in enumerate((S(0, 0.2, 0.32), S(0, 0.36, 0.24), S(0, 0.5, 0.2))):
        c.bone(f'tail{kk + 1}', p, 'body' if kk == 0 else f'tail{kk}')
    c.limb(['tail1', 'tail2', 'tail3'], [S(0, 0.16, 0.34), S(0, 0.34, 0.25), S(0, 0.5, 0.2), S(0, 0.64, 0.22)],
           [0.11 * k, 0.07 * k, 0.045 * k, 0.025 * k], scale_c)
    c.gem('tail3', 'tail_spade', S(0, 0.64, 0.22), (0, 1, 0.3), 0.04 * k, 0.09 * k, dark, dark, mat='M_Toon', sides=4)
    for kk in range(4):
        c.cone_to('body', f'spine{kk}', S(0, 0.06 + 0.07 * kk, 0.66 - 0.08 * kk), S(0, 0.1 + 0.07 * kk, 0.72 - 0.08 * kk),
                  0.022 * k, '#3a2420' if not el else '#e8b84a')

    def extra(a, clip, f, t, i, names):
        P = a.P
        if clip == 'Cast':  # fire breath: rear back with wings spread, then thrust the head out and hold the jaw wide
            g, sh, burst, pop, settle = cast_env(t)
            breath = window(t, 0.55, 0.6, 0.8, 0.93)
            a.r('head', f, (-26 * g + 24 * breath + 2 * sh, 0, 3 * math.sin(math.tau * 6 * t) * breath))
            a.r('jaw', f, (8 * g + 42 * breath, 0, 0))
            a.r('body', f, (P.br[0] + 8 * breath, P.br[1], P.br[2]))
        elif clip == 'Attack':  # claw swipe with a snapping bite on the hit frame
            ant, st, imp, wob = attack_env(t)
            a.r('jaw', f, (35 * window(t, 0.2, 0.33, 0.38, 0.41) + 10 * imp, 0, 0))
    return c.finish('biped', extra)


def killer_bee(eid):
    """킬러비 — a hefty bumblebee-hornet: fuzzy amber thorax with a collar of fluff, dark head with large
    glossy compound eyes, clubbed antennae, a striped abdomen ending in a stinger, two pairs of clear wings."""
    c = Sculpt(eid, tris=7000)
    c.bone('body', (0, 0, 1.0)); c.bone('head', (0, -0.12, 1.04), 'body'); c.bone('eyes', (0, -0.2, 1.08), 'head')
    c.bone('tail1', (0, 0.12, 0.96), 'body')
    c.blob('body', (0, 0.0, 1.0), (0.13, 0.12, 0.12), '#d89a22')
    c.tufts('body', (0, -0.07, 1.06), [(0.7, -0.5, 0.1), (-0.7, -0.5, 0.1), (0, -0.7, 0.5), (0.5, -0.4, -0.6),
                                       (-0.5, -0.4, -0.6)], 0.06, 0.035, '#ffe08a')
    c.blob('head', (0, -0.14, 1.05), (0.09, 0.08, 0.085), '#2a1d26')
    c.blob('head', (0, -0.21, 1.0), (0.035, 0.03, 0.03), '#3a2a30')
    for s in (-1, 1):
        c.eye('eyes', (s * 0.06, -0.18, 1.07), (s * 0.7, -0.7, 0.1), 0.042, '#2a2238', iris_edge=0.2, sclera='#2a2238')
        c.tube('head', f'antenna{s}', [(s * 0.03, -0.18, 1.12), (s * 0.06, -0.22, 1.2), (s * 0.1, -0.24, 1.24)], 0.01, '#2a1d26')
        c.orb('head', f'antenna_club{s}', (s * 0.105, -0.245, 1.245), (0.02, 0.02, 0.02), '#d89a22')
    def stripes(p):
        return '#ffc21f' if math.sin((p.y - 0.12) * 52) > -0.1 else '#2a1d26'
    c.limb('tail1', [(0, 0.1, 0.97), (0, 0.2, 0.93), (0, 0.3, 0.88), (0, 0.37, 0.83)], [0.1, 0.13, 0.11, 0.05], stripes)
    c.cone_to('tail1', 'stinger', (0, 0.39, 0.82), (0, 0.44, 0.77), 0.022, '#3a2340')
    for s, side in ((-1, 'R'), (1, 'L')):
        c.bone('wing.' + side, (s * 0.06, 0.06, 1.1), 'body')
        big = [(s * 0.07, 0.07, 1.11), (s * 0.3, 0.12, 1.3), (s * 0.48, 0.14, 1.32), (s * 0.5, 0.15, 1.24), (s * 0.3, 0.13, 1.14)]
        c.membrane('wing.' + side, f'wing{side}', (s * 0.2, 0.11, 1.18), big + [big[0]], '#d6f4ff', thick=0.004)
        small = [(s * 0.07, 0.09, 1.07), (s * 0.28, 0.14, 1.06), (s * 0.34, 0.15, 1.0), (s * 0.2, 0.13, 1.0)]
        c.membrane('wing.' + side, f'hindwing{side}', (s * 0.18, 0.12, 1.04), small + [small[0]], '#e2f8ff', thick=0.004)
        c.bone('leg.' + side, (s * 0.07, -0.02, 0.92), 'body')
        c.limb('leg.' + side, [(s * 0.07, -0.02, 0.92), (s * 0.11, -0.05, 0.84), (s * 0.1, -0.08, 0.78)], [0.025, 0.02, 0.018], '#2a1d26')
        c.bone('arm.' + side, (s * 0.08, -0.08, 0.98), 'body')
        c.limb('arm.' + side, [(s * 0.08, -0.08, 0.98), (s * 0.13, -0.13, 0.92), (s * 0.12, -0.17, 0.88)], [0.025, 0.02, 0.018], '#2a1d26')
    for p in c.parts.get('wing.L', []) + c.parts.get('wing.R', []):
        if 'wing' in p.name:
            A.paint(p, '#d6f4ff', 'M_Clear')

    def extra(a, clip, f, t, i, names):
        if clip == 'Attack':  # cock the abdomen back, then curl it under and jab the stinger forward
            ant, st, imp, wob = attack_env(t)
            a.r('tail1', f, (25 * ant - 70 * st + 10 * wob, 0, 0))
        elif clip == 'Cast':  # abdomen pumps venom
            g, sh, burst, pop, settle = cast_env(t)
            a.r('tail1', f, (-15 * g - 35 * burst + 4 * sh, 0, 0))
            a.s('tail1', f, (1 + 0.08 * g, 1 + 0.08 * g, 1 + 0.08 * g - 0.06 * burst))
        elif clip == 'Idle':  # abdomen pulses with each wing beat
            a.r('tail1', f, (-8 * math.sin(math.tau * 3 * t - 0.8), 0, 4 * math.sin(math.tau * t)))
            a.s('tail1', f, (1, 1 + 0.04 * math.sin(math.tau * 3 * t), 1 + 0.04 * math.sin(math.tau * 3 * t)))
    return c.finish('fly', extra)


def harpy(eid):
    """하피 — a fierce crimson raptor: hooked beak, swept-back crest, cream breast, broad feathered wings,
    a fanned tail and strong yellow talons."""
    c = Sculpt(eid, tris=8000)
    red, dark, cream = '#c43a2e', '#6e1c1e', '#f2dcc0'
    c.bone('body', (0, 0, 1.0)); c.bone('head', (0, -0.1, 1.2), 'body'); c.bone('eyes', (0, -0.2, 1.24), 'head')
    c.bone('tail1', (0, 0.16, 0.9), 'body')
    c.blob('body', (0, 0.02, 1.0), (0.14, 0.17, 0.17), vgrad(0.85, dark, 1.15, red))
    c.blob('body', (0, -0.09, 1.0), (0.1, 0.07, 0.13), cream, weight=1.3)
    c.limb('head', [(0, -0.05, 1.12), (0, -0.1, 1.2)], [0.09, 0.08], red)
    c.blob('head', (0, -0.12, 1.24), (0.09, 0.1, 0.085), red)
    for k, (d, L) in enumerate((((0, 1, 0.5), 0.14), ((0.3, 1, 0.3), 0.12), ((-0.3, 1, 0.3), 0.12), ((0, 1, 0.9), 0.1))):
        c.tuft('head', (0, -0.08, 1.29), d, L, 0.035, dark)
    for s in (-1, 1):
        c.blob('eyes', (s * 0.05, -0.19, 1.27), (0.035, 0.03, 0.014), dark)
        c.eye('eyes', (s * 0.05, -0.195, 1.245), (s * 0.5, -1, 0.0), 0.022, '#ffc23a')
        c.tuft('head', (s * 0.07, -0.14, 1.2), (s * 0.7, 0.7, -0.3), 0.07, 0.03, cream)
    c.tube('head', 'beak', [(0, -0.2, 1.23), (0, -0.27, 1.21), (0, -0.29, 1.17)], 0.03, '#f2c23a', taper=0.15)
    for s, side in ((-1, 'R'), (1, 'L')):
        c.bone('wing.' + side, (s * 0.13, 0.02, 1.08), 'body')
        feather_wing(c, 'wing.' + side, s, (s * 0.13, 0.03, 1.08), 0.55, 0.14, red, dark, cream, red, feathers=8, r=0.026)
        c.bone('leg.' + side, (s * 0.06, 0.02, 0.86), 'body')
        c.limb('leg.' + side, [(s * 0.06, 0.02, 0.88), (s * 0.07, 0.0, 0.78), (s * 0.07, -0.02, 0.7)], [0.04, 0.025, 0.02], '#f2c23a')
        for j in range(3):
            c.spike('leg.' + side, f'talon{side}{j}', (s * 0.07, -0.02, 0.7), (s * 0.07 + (j - 1) * 0.03, -0.07, 0.67), 0.01, '#3a2420')
    fan_tail(c, 'tail1', (0, 0.15, 0.9), 0.3, 56, red, dark, n=6)
    return c.finish('fly')


BUILDERS = {'bat': bat, 'elite_bat': bat, 'grave_bat': bat, 'phoenix': phoenix, 'fire_drake': fire_drake,
            'elite_fire_drake': fire_drake, 'killer_bee': killer_bee, 'harpy': harpy}

if __name__ == '__main__':
    eid = sys.argv[sys.argv.index('--') + 1]
    BUILDERS[eid](eid)
