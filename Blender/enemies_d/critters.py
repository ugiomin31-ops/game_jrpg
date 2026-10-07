"""Sculpted critters (monster v3): horned_rabbit, yeti / elite_yeti, penguin_mage, lizardman.
Run through the production runner: blender -b --factory-startup -P Blender/enemies_a/generate_all.py -- --asset yeti
"""
import math
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from sculpt_kit import Sculpt, A, lerp_col, vgrad  # noqa: E402,F401
from mathutils import Vector  # noqa: E402


def horned_rabbit(eid):
    """뿔토끼 — a sitting wild rabbit: heavy haunches, fluffy chest and cheeks, long upright ears,
    a short spiral unicorn horn, a cotton tail and a leaf scarf."""
    c = Sculpt(eid, tris=7000)
    fur, pale, pink = '#f3ece2', '#fffaf2', '#f2a7b6'
    furry = lambda p: lerp_col('#d9cdbd', fur, (p.z - 0.04) / 0.2)  # noqa: E731
    c.bone('body', (0, 0.02, 0.22)); c.bone('head', (0, -0.04, 0.4), 'body'); c.bone('eyes', (0, -0.17, 0.48), 'head')
    c.bone('tail1', (0, 0.2, 0.2), 'body')
    c.blob('body', (0, 0.05, 0.24), (0.16, 0.18, 0.17), furry)
    c.blob('body', (0, -0.08, 0.3), (0.12, 0.09, 0.13), pale, weight=1.3)
    c.tufts('body', (0, -0.12, 0.32), [(0.5, -0.5, -0.6), (-0.5, -0.5, -0.6), (0, -0.6, -0.8)], 0.07, 0.04, pale, weight=1.3)
    c.blob('head', (0, -0.07, 0.47), (0.12, 0.115, 0.11), fur)
    for s in (-1, 1):
        c.blob('head', (s * 0.07, -0.12, 0.42), (0.06, 0.06, 0.05), pale, weight=1.25)
        c.tuft('head', (s * 0.1, -0.1, 0.42), (s * 1, 0.4, -0.3), 0.06, 0.03, pale)
        c.blob('eyes', (s * 0.058, -0.155, 0.505), (0.035, 0.03, 0.014), fur)                     # brow
        c.eye('eyes', (s * 0.06, -0.16, 0.48), (s * 0.55, -1, 0.05), 0.024, '#7a3a4a')
    c.blob('head', (0, -0.17, 0.43), (0.05, 0.04, 0.035), pale)                                    # muzzle
    c.paint((0, -0.205, 0.445), (0.016, 0.01, 0.01), '#d47a90')                                    # nose
    c.paint((0, -0.205, 0.415), (0.006, 0.01, 0.018), '#a06070')                                   # philtrum
    c.cone_to('head', 'horn', (0, -0.13, 0.55), (0, -0.19, 0.74), 0.035, '#fff1cc', seg=12)
    for k in range(3):
        p = Vector((0, -0.13, 0.55)).lerp(Vector((0, -0.19, 0.74)), 0.2 + 0.22 * k)
        c.ring('head', f'horn_band{k}', tuple(p), 0.03 * (1 - 0.2 * k), 0.006, '#e4b24e', rot=(-14, 0, 0))
    for s, side in ((-1, 'R'), (1, 'L')):
        c.bone('ear.' + side, (s * 0.05, -0.03, 0.56), 'head')
        for k, (x, z, w, h) in enumerate(((0.055, 0.6, 0.042, 0.06), (0.065, 0.69, 0.048, 0.07), (0.072, 0.79, 0.04, 0.06),
                                          (0.075, 0.86, 0.025, 0.035))):
            c.blob('ear.' + side, (s * x, -0.02, z), (w, 0.02, h), fur, rot=(-6, s * 6, 0))
        c.paint((s * 0.066, -0.045, 0.72), (0.03, 0.02, 0.1), pink)
        c.bone('arm.' + side, (s * 0.07, -0.1, 0.24), 'body')
        c.limb('arm.' + side, [(s * 0.07, -0.1, 0.24), (s * 0.075, -0.15, 0.12), (s * 0.075, -0.17, 0.05)], [0.04, 0.032, 0.035], fur)
        c.bone('leg.' + side, (s * 0.1, 0.06, 0.16), 'body')
        c.blob('leg.' + side, (s * 0.11, 0.07, 0.15), (0.09, 0.12, 0.11), furry)                 # haunch
        c.blob('leg.' + side, (s * 0.1, -0.05, 0.035), (0.05, 0.12, 0.03), furry)                # long hind foot
    c.blob('tail1', (0, 0.22, 0.22), (0.06, 0.06, 0.06), pale)
    c.ring('body', 'leaf_scarf', (0, -0.05, 0.37), 0.135, 0.024, '#58b947', scale=(1, 0.95, 0.7))
    c.petal('body', 'scarf_leaf_a', (-0.02, -0.15, 0.36), (-0.35, -0.25, -1), 0.12, 0.07, '#7ad354', tip='#3f8f2f')
    c.petal('body', 'scarf_leaf_b', (0.02, -0.15, 0.36), (0.45, -0.2, -1), 0.1, 0.06, '#7ad354', tip='#3f8f2f')
    return c.finish('hop')


def yeti(eid):
    """꼬마 설인 / 설산의 폭군 — a hulking snow ape: massive shaggy shoulders, a blue face under a heavy brow,
    tusks and curled horns, long arms ending in big blue fists, short sturdy legs; the tyrant carries an
    icicle club and ice-crusted shoulders."""
    c = Sculpt(eid, tris=10000)
    el = c.elite
    fur, shade, blue = ('#f1f5fc', '#c9d6ea', '#7fa8e0') if not el else ('#e2e9f6', '#aebfdc', '#4f78c4')
    shag = lambda p: lerp_col(shade, fur, (p.z - 0.15) / 0.5)  # noqa: E731
    c.bone('body', (0, 0, 0.42)); c.bone('head', (0, -0.08, 0.74), 'body'); c.bone('eyes', (0, -0.25, 0.8), 'head')
    c.bone('jaw', (0, -0.22, 0.7), 'head')
    c.blob('body', (0, 0, 0.48), (0.28, 0.24, 0.3), shag)
    c.blob('body', (0, -0.13, 0.42), (0.18, 0.12, 0.2), lerp_col(shade, '#9fb4d6', 0.3))
    for s in (-1, 1):
        c.blob('body', (s * 0.22, -0.02, 0.66), (0.15, 0.15, 0.13), fur)
        for k in range(4):
            a = math.radians(-60 + k * 40)
            c.tuft('body', (s * 0.3, 0.0, 0.7), (s * math.cos(a), 0.3, math.sin(a)), 0.12, 0.06, fur, curl=0.2)
    for k in range(7):  # shaggy hem around the hips and back (none in front)
        a = math.radians(-20 + k * 36.7)
        c.tuft('body', (0.24 * math.cos(a), 0.2 * math.sin(a), 0.3), (math.cos(a), math.sin(a), -0.35), 0.1, 0.055, shag, curl=0.3)
    c.blob('head', (0, -0.1, 0.8), (0.16, 0.14, 0.14), fur)
    c.blob('head', (0, -0.2, 0.77), (0.11, 0.06, 0.1), blue)                                      # face
    c.blob('head', (0, -0.235, 0.86), (0.13, 0.04, 0.03), fur)                                     # brow
    c.blob('head', (0, -0.26, 0.74), (0.07, 0.045, 0.045), lerp_col(blue, '#203a6a', 0.2))         # muzzle
    c.paint((0, -0.3, 0.75), (0.03, 0.01, 0.01), '#203050')
    c.limb('jaw', [(0, -0.2, 0.68), (0, -0.27, 0.68)], [0.07, 0.05], blue)
    c.tufts('head', (0, -0.08, 0.92), [(0, 0.2, 1), (0.6, 0.2, 0.8), (-0.6, 0.2, 0.8), (0, 0.8, 0.6)], 0.12, 0.05, fur, curl=0.15)
    for s in (-1, 1):
        c.eye('eyes', (s * 0.05, -0.245, 0.82), (s * 0.4, -1, 0.0), 0.024, '#ffb21f')
        c.spike('jaw', f'tusk{s}', (s * 0.045, -0.29, 0.69), (s * 0.06, -0.31, 0.77), 0.016, '#fff8e8')
        horn = [(s * 0.12, -0.06, 0.9), (s * 0.2, -0.03, 0.96), (s * 0.24, 0.03, 1.04)]
        if el:
            horn = [(s * 0.12, -0.06, 0.9), (s * 0.23, -0.02, 0.95), (s * 0.3, 0.05, 1.06), (s * 0.27, 0.09, 1.16)]
        c.tube('head', f'horn{s}', horn, 0.04 if not el else 0.05, '#e8d8b6' if not el else '#30405f', taper=0.25)
    for s, side in ((-1, 'R'), (1, 'L')):
        c.bone('arm.' + side, (s * 0.28, -0.02, 0.66), 'body')
        c.limb('arm.' + side, [(s * 0.3, -0.02, 0.64), (s * 0.39, -0.06, 0.44), (s * 0.41, -0.1, 0.27)], [0.1, 0.085, 0.07], fur)
        c.tufts('arm.' + side, (s * 0.38, -0.02, 0.46), [(s * 0.6, 0.8, -0.2), (s * 0.8, 0.4, -0.5)], 0.08, 0.045, fur)
        c.blob('arm.' + side, (s * 0.42, -0.13, 0.2), (0.1, 0.1, 0.09), blue)
        c.bone('leg.' + side, (s * 0.15, 0, 0.24), 'body')
        c.limb('leg.' + side, [(s * 0.15, 0, 0.26), (s * 0.16, -0.02, 0.09)], [0.11, 0.1], shag)
        c.blob('leg.' + side, (s * 0.16, -0.08, 0.04), (0.1, 0.14, 0.045), blue)
    if el:
        for s, side in ((-1, 'R'), (1, 'L')):
            for j in range(4):
                c.gem('arm.' + side, f'shoulder_ice{side}{j}', (s * (0.3 + j * 0.03), 0.0, 0.74 - j * 0.02),
                      (s * (0.4 + j * 0.3), -0.1 + j * 0.1, 1), 0.045, 0.18 - j * 0.02, '#e6fcff', '#3aa6e8')
        c.bone('weapon.R', (-0.42, -0.14, 0.22), 'arm.R')
        c.tube('weapon.R', 'club_grip', [(-0.42, -0.16, 0.12), (-0.42, -0.18, 0.44)], 0.03, '#6b4a3a')
        c.gem('weapon.R', 'icicle_club', (-0.42, -0.18, 0.4), (0, -0.15, 1), 0.1, 0.5, '#e9fdff', '#4fb8f2', mat='M_Clear', sides=7)
    return c.finish('heavy')


def penguin_mage(eid):
    """펭귄 마법사 — a portly emperor penguin in a fur-trimmed wizard hat and short cape, with a crystal
    staff: navy back, cream breast with a gold blush, orange beak and feet, flipper hands."""
    c = Sculpt(eid, tris=8000)
    navy, cream = '#22386e', '#fff3d8'

    def plumage(p):
        if p.y < -0.06 and p.z < 0.78:
            return lerp_col(cream, '#ffd9a0', (p.z - 0.55) / 0.2) if p.z > 0.55 else cream
        return navy
    c.bone('body', (0, 0, 0.4)); c.bone('head', (0, -0.02, 0.74), 'body'); c.bone('eyes', (0, -0.18, 0.82), 'head')
    c.bone('crest', (0, 0, 0.93), 'head')
    c.blob('body', (0, 0, 0.4), (0.25, 0.21, 0.33), plumage)
    c.blob('body', (0, -0.04, 0.22), (0.22, 0.18, 0.15), plumage)
    c.blob('head', (0, -0.03, 0.82), (0.17, 0.155, 0.15), lambda p: cream if p.y < -0.13 and abs(p.x) < 0.11 else navy)
    for s in (-1, 1):
        c.blob('eyes', (s * 0.06, -0.165, 0.865), (0.04, 0.03, 0.014), navy)
        c.eye('eyes', (s * 0.06, -0.165, 0.835), (s * 0.4, -1, 0.05), 0.026, '#2a3a6a')
    c.cone_to('head', 'beak', (0, -0.17, 0.79), (0, -0.27, 0.77), 0.045, '#f6b72a')
    c.cone_to('head', 'beak_low', (0, -0.165, 0.765), (0, -0.23, 0.76), 0.028, '#e09a1a')
    for s, side in ((-1, 'R'), (1, 'L')):
        c.bone('arm.' + side, (s * 0.23, 0, 0.55), 'body')
        for k, z in enumerate((0.52, 0.44, 0.36)):
            c.blob('arm.' + side, (s * (0.26 + 0.02 * k), -0.01, z), (0.05 - 0.008 * k, 0.07 - 0.01 * k, 0.07), navy)
        c.bone('leg.' + side, (s * 0.12, 0, 0.12), 'body')
        c.blob('leg.' + side, (s * 0.12, -0.12, 0.03), (0.07, 0.1, 0.025), '#f5b42c')
        for j in range(3):
            c.blob('leg.' + side, (s * 0.12 + (j - 1) * 0.04, -0.2, 0.025), (0.025, 0.04, 0.02), '#f5b42c')
    c.add('crest', A.lathe('wizard_hat', [(0.22, 0.92), (0.2, 0.97), (0.15, 1.04), (0.11, 1.2), (0.06, 1.36), (0, 1.44)],
                           color='#2d589d', seg=24))
    c.ring('crest', 'hat_fur', (0, 0, 0.95), 0.2, 0.035, '#f8eddf')
    c.tube('crest', 'hat_curl', [(0, 0, 1.36), (0.07, 0.02, 1.43), (0.13, 0.04, 1.4), (0.15, 0.05, 1.33)], 0.045, '#2d589d', taper=0.3)
    c.membrane('body', 'cape', (0, 0.12, 0.55), [(-0.24, 0.06, 0.68), (-0.3, 0.2, 0.3), (0, 0.26, 0.22), (0.3, 0.2, 0.3),
                                                (0.24, 0.06, 0.68)], '#315691', thick=0.012, edge_color='#22386e')
    c.ring('body', 'cape_fur', (0, 0, 0.66), 0.2, 0.03, '#fff1df', scale=(1, 0.85, 1))
    c.orb('body', 'brooch', (0, -0.2, 0.66), (0.04, 0.02, 0.05), '#57dafa', 'M_Emit')
    c.bone('weapon.R', (-0.3, -0.06, 0.38), 'arm.R')
    c.tube('weapon.R', 'staff', [(-0.32, -0.08, 0.08), (-0.33, -0.08, 0.62), (-0.36, -0.06, 1.0), (-0.3, -0.06, 1.08)], 0.024, '#6b4739')
    for j in range(3):
        c.spike('weapon.R', f'staff_crystal{j}', (-0.32 + (j - 1) * 0.05, -0.06, 0.98), (-0.32 + (j - 1) * 0.08, -0.06, 1.26 - (j % 2) * 0.1),
                0.035, '#8ef2ff', 'M_Emit')
    return c.finish('biped')


def lizardman(eid):
    """리자드맨 — a lean desert lizard warrior: long snouted head with a finned crest, cream throat and belly,
    digitigrade legs, a heavy tail, red sash and loincloth, scimitar and brass buckler."""
    c = Sculpt(eid, tris=10000)
    scale_c, belly_c, red, brass = '#3a9a74', '#efdca6', '#c2362f', '#d1a443'

    def scales(p):
        if p.y < -0.06 and 0.3 < p.z < 0.75:
            return belly_c if math.sin(p.z * 70) > -0.7 else lerp_col(belly_c, '#c9ad72', 0.6)
        return lerp_col('#2a7a5a', scale_c, (p.z - 0.2) / 0.6)
    c.bone('body', (0, 0, 0.42)); c.bone('head', (0, -0.03, 0.8), 'body'); c.bone('eyes', (0, -0.2, 0.95), 'head')
    c.bone('jaw', (0, -0.2, 0.86), 'head'); c.bone('crest', (0, 0.02, 1.02), 'head')
    c.blob('body', (0, 0.0, 0.6), (0.15, 0.12, 0.17), scales)
    c.blob('body', (0, -0.02, 0.44), (0.12, 0.1, 0.1), scales)
    for s in (-1, 1):
        c.blob('body', (s * 0.13, 0.0, 0.7), (0.07, 0.08, 0.07), scale_c)
    c.limb('head', [(0, -0.02, 0.74), (0, -0.05, 0.84)], [0.07, 0.065], scales)
    c.blob('head', (0, -0.06, 0.93), (0.1, 0.11, 0.09), scale_c)
    c.limb('head', [(0, -0.13, 0.92), (0, -0.22, 0.9), (0, -0.28, 0.885)], [0.075, 0.06, 0.045], scale_c)
    c.limb('jaw', [(0, -0.1, 0.86), (0, -0.25, 0.855)], [0.055, 0.035], belly_c)
    c.paint((0, -0.16, 0.875), (0.08, 0.1, 0.006), '#5a2a2a')                                       # mouth line
    for s in (-1, 1):
        c.paint((s * 0.018, -0.3, 0.9), (0.01, 0.008, 0.006), '#1c3b2e')
        c.blob('eyes', (s * 0.055, -0.15, 0.985), (0.035, 0.035, 0.016), '#2a7a5a')
        c.eye('eyes', (s * 0.06, -0.155, 0.955), (s * 0.7, -0.8, 0.05), 0.025, '#ffc21f', slit=True)
        c.spike('jaw', f'fang{s}', (s * 0.03, -0.25, 0.875), (s * 0.03, -0.255, 0.85), 0.008, '#ffffff')
    frill = [(0, -0.12, 0.98)]
    for k in range(6):  # spined sail from the brow down the back of the neck
        y, z = -0.1 + k * 0.05, 1.0 - k * 0.035
        frill += [(0, y + 0.02, z + 0.13 - k * 0.012), (0, y + 0.045, z + 0.03)]
    frill.append((0, 0.06, 0.78))
    c.membrane('crest', 'frill', (0, 0.0, 0.92), frill, '#ff8a3a', thick=0.012, edge_color='#ffd04a')
    c.ring('body', 'sash', (0, 0, 0.45), 0.14, 0.03, red, scale=(1, 0.9, 1))
    c.membrane('body', 'loincloth', (0, -0.12, 0.44), [(-0.08, -0.12, 0.45), (-0.09, -0.13, 0.27), (0, -0.14, 0.23),
                                                       (0.09, -0.13, 0.27), (0.08, -0.12, 0.45)], red, thick=0.012)
    c.tube('body', 'strap', [(-0.14, -0.06, 0.74), (0, -0.14, 0.6), (0.13, -0.08, 0.46)], 0.018, '#7a4a2a')
    for s, side in ((-1, 'R'), (1, 'L')):
        c.bone('arm.' + side, (s * 0.15, -0.01, 0.7), 'body')
        c.orb('arm.' + side, 'pauldron' + side, (s * 0.17, 0, 0.74), (0.075, 0.075, 0.055), '#8a5530')
        c.limb('arm.' + side, [(s * 0.15, -0.01, 0.7), (s * 0.22, -0.04, 0.58), (s * 0.24, -0.1, 0.48)], [0.045, 0.037, 0.033], scale_c)
        c.blob('arm.' + side, (s * 0.245, -0.12, 0.46), (0.04, 0.04, 0.04), scale_c)
        c.bone('leg.' + side, (s * 0.09, 0, 0.4), 'body')
        c.blob('leg.' + side, (s * 0.1, 0.0, 0.33), (0.075, 0.09, 0.1), scale_c)
        c.limb('leg.' + side, [(s * 0.11, 0.03, 0.24), (s * 0.12, 0.06, 0.13), (s * 0.12, -0.02, 0.05)], [0.045, 0.035, 0.033], scale_c)
        c.blob('leg.' + side, (s * 0.12, -0.07, 0.03), (0.05, 0.09, 0.025), '#2a7a5a')
        for j in range(3):
            c.spike('leg.' + side, f'claw{side}{j}', (s * 0.12 + (j - 1) * 0.028, -0.15, 0.03),
                    (s * 0.12 + (j - 1) * 0.032, -0.19, 0.012), 0.01, '#f5ead2')
    c.bone('tail1', (0, 0.1, 0.42), 'body'); c.bone('tail2', (0, 0.3, 0.2), 'tail1')
    c.limb(['tail1', 'tail2', 'tail2'], [(0, 0.08, 0.44), (0, 0.22, 0.32), (0, 0.34, 0.18), (0.06, 0.52, 0.05)],
           [0.08, 0.06, 0.04, 0.015], scales)
    c.bone('weapon.R', (-0.25, -0.12, 0.46), 'arm.R'); c.bone('weapon.L', (0.25, -0.12, 0.46), 'arm.L')
    c.tube('weapon.R', 'hilt', [(-0.25, -0.12, 0.4), (-0.25, -0.12, 0.52)], 0.018, '#5a3a24')
    c.box('weapon.R', 'guard', (-0.25, -0.12, 0.53), (0.12, 0.04, 0.025), brass, bevel=0.008)
    c.shape('weapon.R', 'scimitar', [(-0.025, 0), (-0.03, 0.2), (-0.015, 0.36), (0.04, 0.48), (0.09, 0.5), (0.05, 0.38),
                                     (0.035, 0.2), (0.03, 0)], (-0.25, -0.12, 0.54), '#d3dde6', depth=0.018)
    c.orb('weapon.L', 'buckler', (0.3, -0.15, 0.5), (0.13, 0.035, 0.13), brass, seg=24, rings=10)
    c.ring('weapon.L', 'buckler_rim', (0.3, -0.172, 0.5), 0.125, 0.012, '#8a5530', rot=(90, 0, 0))
    c.gem('weapon.L', 'buckler_gem', (0.3, -0.18, 0.5), (0, -1, 0), 0.035, 0.05, '#9ffff0', '#1fb3a0')
    return c.finish('biped')


BUILDERS = {'horned_rabbit': horned_rabbit, 'yeti': yeti, 'elite_yeti': yeti, 'penguin_mage': penguin_mage,
            'lizardman': lizardman}

if __name__ == '__main__':
    eid = sys.argv[sys.argv.index('--') + 1]
    BUILDERS[eid](eid)
