"""Ember-caverns v2 species: hellhound (+elite twin-headed orthrus), flame_elemental, sand_scorpion,
lizardman, harpy.
Run: blender -b --factory-startup -P Blender/enemies_c/ember.py -- <id>
"""
import math
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from monster_kit import Monster, Head, A, INK  # noqa: E402


def _hound_head(c, hb, eb, jb, cx, k, fur, lava):
    """One hellhound head (bones hb/eb/jb), centred at x=cx, scaled by k."""
    h = Head((cx, -.31, .6), (.19 * k, .17 * k, .17 * k))
    c.orb(hb, f'hound_skull{hb}', tuple(h.c), tuple(h.r), fur, seg=24, rings=14)
    m = Head((cx, -.31 - .16 * k, .54), (.105 * k, .1 * k, .075 * k))
    c.orb(hb, f'muzzle{hb}', tuple(m.c), tuple(m.r), '#3d3342')
    p, n = m.point(cx, .54 + .045 * k, .005)
    c.disc(hb, f'nose{hb}', p, n, (.035 * k, .025, .022 * k), '#120c14')
    c.eye_pair(eb, h, .63, .085 * k, .05 * k, .058 * k, '#ff8a1c', '#ffe066', angry=.9, tag=hb)
    c.open_mouth(jb, m, .505, .07 * k, .035 * k, fangs='#fff3dc', tag=hb)
    for s in (-1, 1):
        c.cone_to(hb, f'ear{hb}{s}', (cx + s * .11 * k, -.27, .72), (cx + s * .2 * k, -.22, .9), .055 * k, fur)
        c.cone_to(hb, f'ear_in{hb}{s}', (cx + s * .11 * k, -.29, .73), (cx + s * .185 * k, -.25, .86), .028 * k, lava, 'M_Emit')
        c.tube(hb, f'brow_lava{hb}{s}', [(cx + s * .03 * k, -.47 * 1, .7), (cx + s * .14 * k, -.42, .74)], .008, lava, 'M_Emit')
    for j in range(5):
        ang = math.pi * (.15 + .7 * j / 4)
        base = (cx + .14 * k * math.cos(ang), -.22, .6 + .13 * k * math.sin(ang))
        c.flame(hb, f'mane{hb}{j}', base, .26 * k, .06 * k, lean=(.08 * math.cos(ang) * k, .14, 0))
    return h


def hellhound(eid):
    """헬하운드 / elite 오르트로스 — charcoal fire hound with a burning mane; the elite has two heads."""
    c = Monster(eid); el = c.elite
    fur = '#2d2532' if not el else '#3a1c26'
    lava = '#ff7a1a'
    c.bone('body', (0, .05, .4))
    c.orb('body', 'torso', (0, .07, .43), (.2, .32, .2), fur, seg=24, rings=14)
    c.orb('body', 'chest', (0, -.15, .45), (.21, .17, .21), fur)
    c.orb('body', 'belly', (0, .02, .33), (.14, .26, .1), '#4b3a46')
    for s in (-1, 1):
        c.tube('body', f'lava_vein{s}', [(s * .19, -.05, .5), (s * .2, .08, .44), (s * .19, .2, .48), (s * .17, .3, .42)], .011, lava, 'M_Emit')
    c.ring('body', 'spiked_collar', (0, -.2, .55), .16, .03, '#7a2a24', rot=(60, 0, 0))
    for j in range(7):
        ang = math.pi * (j / 6)
        p = (.16 * math.cos(ang), -.2 - .08 * math.sin(ang), .55 + .14 * math.sin(ang))
        c.cone_to('body', f'collar_spike{j}', p, (p[0] * 1.45, p[1] - .04, p[2] + .05), .022, '#e0b452')
    if not el:
        c.bone('head', (0, -.22, .58), 'body'); c.bone('eyes', (0, -.47, .63), 'head'); c.bone('jaw', (0, -.4, .52), 'head')
        _hound_head(c, 'head', 'eyes', 'jaw', 0, 1.0, fur, lava)
    else:
        for b, cx in (('head', -.18), ('head2', .18)):
            sfx = '' if b == 'head' else '2'
            c.bone(b, (cx, -.2, .58), 'body'); c.bone('eyes' + sfx, (cx, -.45, .63), b); c.bone('jaw' + sfx, (cx, -.38, .52), b)
            _hound_head(c, b, 'eyes' + sfx, 'jaw' + sfx, cx, .8, fur, lava)
            c.cone_to(b, f'horn{b}', (cx, -.3, .74), (cx + (cx > 0 and .06 or -.06), -.25, .9), .03, '#e0b452')
        c.box('body', 'gold_back_plate', (0, .1, .62), (.26, .36, .05), '#c99a3e', bevel=.02)
        c.gem('body', 'plate_gem', (0, .02, .64), (0, -.2, 1), .04, .08, '#ffd1a1', '#ff5a1a')
    for code, (x, y) in (('FL', (.13, -.17)), ('FR', (-.13, -.17)), ('BL', (.13, .27)), ('BR', (-.13, .27))):
        b = 'leg.' + code
        c.bone(b, (x, y, .36), 'body')
        c.orb(b, 'thigh' + code, (x * 1.05, y, .32), (.08, .1, .11), fur)
        c.tube(b, 'shin' + code, [(x * 1.05, y, .26), (x * 1.08, y - .02, .08)], .045, fur, taper=.8)
        c.orb(b, 'paw' + code, (x * 1.08, y - .05, .045), (.065, .085, .045), '#3d3342')
        for j in range(3):
            c.cone_to(b, f'claw{code}{j}', (x * 1.08 + (j - 1) * .03, y - .12, .04), (x * 1.08 + (j - 1) * .035, y - .16, .01), .012, '#efe4cf')
    c.bone('tail1', (0, .36, .48), 'body'); c.bone('tail2', (0, .52, .62), 'tail1'); c.bone('flame_tail', (0, .58, .74), 'tail2')
    c.tube('tail1', 'tail_base', [(0, .35, .47), (0, .46, .55), (0, .53, .63)], .045, fur, taper=.8)
    c.tube('tail2', 'tail_tip', [(0, .53, .63), (0, .58, .72)], .036, fur)
    c.flame('flame_tail', 'tail_flame', (0, .58, .72), .3, .07, lean=(0, .1, 0))

    def extra(a, clip, f, t, i, names):
        if 'head2' in names:  # mirror the main head's idle motion with an offset
            if clip == 'Idle':
                a.r('head2', f, (3 * math.sin(math.tau * t + 2), -4 * math.sin(math.tau * t), 0))
            elif clip in ('Attack', 'Victory', 'Cast'):
                p = math.sin(math.pi * t)
                a.r('head2', f, (-12 * p, -6 * p, 0))
                a.r('jaw2', f, (25 * p, 0, 0))
            elif clip == 'Hit':
                a.r('head2', f, (-14 * max(0, 1 - abs(t - .22) / .22), 6, 0))
    return c.finish('quad', extra)


def flame_elemental(eid):
    """불꽃 정령 — living flame with obsidian armour shards, flame hair and orbiting cinders."""
    c = Monster(eid)
    hot, core, obs, lava = '#ff7a1a', '#ffd23a', '#2a1f28', '#ff9a2a'
    c.bone('body', (0, 0, .6)); c.bone('head', (0, -.02, .82), 'body'); c.bone('eyes', (0, -.18, .92), 'head')
    c.bone('flame_hair', (0, .0, 1.0), 'head'); c.bone('tail1', (0, 0, .5), 'body'); c.bone('orbit', (0, 0, .7), 'body')
    c.add('body', A.lathe('flame_torso', [(.05, .42), (.17, .5), (.2, .62), (.17, .74), (.1, .8), (0, .82)], color=hot, mat='M_Emit', seg=20))
    c.orb('body', 'heart_glow', (0, -.12, .63), (.08, .05, .09), core, 'M_Emit')
    c.chunk('body', 'obsidian_chest', (0, -.08, .68), (.16, .09, .08), obs, seed=21, seg=7, rings=5)
    c.chunk('body', 'obsidian_belt', (0, -.02, .5), (.17, .14, .05), obs, seed=22, seg=8, rings=4)
    c.tube('body', 'chest_crack', [(-.07, -.17, .7), (0, -.18, .66), (.06, -.17, .71)], .01, lava, 'M_Emit')
    h = Head((0, -.03, .92), (.17, .15, .16))
    c.orb('head', 'flame_head', tuple(h.c), tuple(h.r), '#ffab2e', 'M_Emit', seg=22, rings=12)
    c.eye_pair('eyes', h, .93, .072, .048, .06, '#ff3d00', '#ffb000', angry=.7, sclera='#fff8de', pupil='#4a0d00')
    c.open_mouth('head', h, .85, .045, .03, fangs=None, tongue='#ffd23a', inner='#5a1200')
    for s in (-1, 1):
        c.cone_to('head', f'obsidian_horn{s}', (s * .11, -.0, 1.0), (s * .2, .04, 1.14), .035, obs)
    for k in range(7):
        x = (k - 3) * .045
        c.flame('flame_hair', f'hair_flame{k}', (x, .02 + abs(k - 3) * .01, .99 - abs(k - 3) * .02), .34 - abs(k - 3) * .04, .06, lean=(x * 1.2, .2, 0))
    c.tube('tail1', 'flame_tail', [(0, 0, .46), (.03, .04, .36), (-.03, .09, .27), (.04, .15, .2)], .12, hot, 'M_Emit', taper=.05)
    c.tube('tail1', 'flame_tail_core', [(0, -.02, .46), (.02, .02, .38), (-.02, .06, .3)], .07, core, 'M_Emit', taper=.1)
    for s, side in ((-1, 'R'), (1, 'L')):
        c.bone('arm.' + side, (s * .16, -.02, .72), 'body')
        c.tube('arm.' + side, 'flame_arm' + side, [(s * .16, -.02, .72), (s * .26, -.06, .62), (s * .3, -.1, .52)], .05, hot, 'M_Emit', taper=.8)
        c.chunk('arm.' + side, 'obsidian_gauntlet' + side, (s * .31, -.11, .5), (.07, .07, .07), obs, seed=30 + s, seg=7, rings=5)
        c.chunk('arm.' + side, 'obsidian_pauldron' + side, (s * .18, -.01, .76), (.09, .09, .06), obs, seed=33 + s, seg=7, rings=5)
        for j in range(3):
            c.cone_to('arm.' + side, f'flame_claw{side}{j}', (s * .31 + (j - 1) * .03, -.15, .46), (s * .32 + (j - 1) * .04, -.2, .4), .018, core, 'M_Emit')
    for s in (-1, 1):
        for j in range(3):
            c.flame('body', f'shoulder_flame{s}{j}', (s * (.12 + .04 * j), .04, .76 - .05 * j), .2 - .04 * j, .05, lean=(s * .1, .08, 0))
    for k in range(3):
        ang = math.tau * k / 3
        p = (.34 * math.cos(ang), .28 * math.sin(ang), .62 + .12 * (k % 2))
        c.chunk('orbit', f'cinder{k}', p, (.04, .04, .04), obs, seed=40 + k, seg=6, rings=4)
        c.orb('orbit', f'cinder_glow{k}', (p[0], p[1], p[2] + .03), (.025, .025, .02), lava, 'M_Emit')
    return c.finish('float')


def sand_scorpion(eid):
    """모래 전갈 — chunky desert scorpion: crab-like pincers, arched tail with a glowing venom bulb."""
    c = Monster(eid)
    sand, plate, cream, dark = '#e0a04a', '#a5582a', '#f5d9a0', '#4a2a1c'
    c.bone('body', (0, .05, .26)); c.bone('head', (0, -.18, .3), 'body'); c.bone('eyes', (0, -.36, .36), 'head')
    c.orb('body', 'carapace', (0, .06, .28), (.21, .29, .13), sand, seg=24, rings=12)
    for k in range(4):
        c.ring('body', f'plate_band{k}', (0, -.08 + k * .1, .3), .2 - k * .015, .018, plate, rot=(90, 0, 0), scale=(1, 1, .62))
    c.orb('body', 'underside', (0, .05, .2), (.17, .25, .07), cream)
    h = Head((0, -.22, .31), (.18, .14, .13))
    c.orb('head', 'scorp_head', tuple(h.c), tuple(h.r), sand, seg=22, rings=12)
    c.orb('head', 'head_plate', (0, -.2, .4), (.15, .12, .05), plate)
    c.eye_pair('eyes', h, .335, .085, .058, .07, '#18c9b0', '#a9fff0', angry=.15)
    c.blush('head', h, .27, .13, .03)
    c.cat_mouth('head', h, .25, .028)
    tail = [(0, .3, .3), (0, .4, .4), (0, .44, .55), (0, .41, .7), (0, .32, .8)]
    for k in range(4):
        b = f'tail{k + 1}'
        c.bone(b, tail[k], 'body' if k == 0 else f'tail{k}')
        r = .09 - k * .012
        c.orb(b, f'tail_seg{k}', tail[k], (r, r, r), sand if k % 2 == 0 else plate)
        c.tube(b, f'tail_link{k}', [tail[k], tail[k + 1]], r * .7, sand)
    c.orb('tail4', 'venom_bulb', (0, .3, .8), (.07, .07, .065), '#9b45d6')
    c.orb('tail4', 'venom_glow', (0, .26, .79), (.04, .03, .04), '#e08cff', 'M_Emit')
    c.cone_to('tail4', 'stinger', (0, .26, .79), (0, .21, .74), .028, dark)
    for s, side in ((-1, 'R'), (1, 'L')):
        c.bone('arm.' + side, (s * .16, -.22, .28), 'body')
        c.tube('arm.' + side, 'pincer_arm' + side, [(s * .16, -.22, .28), (s * .27, -.32, .3), (s * .3, -.42, .3)], .045, plate)
        c.orb('arm.' + side, 'pincer_palm' + side, (s * .31, -.5, .31), (.09, .11, .075), sand)
        # rounded mitten pincers
        c.orb('arm.' + side, 'pincer_outer' + side, (s * .345, -.6, .32), (.05, .08, .05), plate)
        c.orb('arm.' + side, 'pincer_inner' + side, (s * .275, -.59, .31), (.04, .06, .04), sand)
        for k, y in enumerate((-.06, .07, .2)):
            b = f'leg{k + 1}.{side}'
            c.bone(b, (s * .15, y, .24), 'body')
            c.stubby_leg(b, f'leg{k}{side}', (s * .15, y, .24), (s * .29, y + (k - 1) * .06, .04), .042, plate, cream)

    def extra(a, clip, f, t, i, names):
        hit = max(0.0, 1 - abs(t - .4) / .16)
        wind = max(0.0, 1 - abs(t - .2) / .16)
        if clip == 'Attack':
            for k, w in ((1, 10), (2, 22), (3, 28), (4, 30)):
                a.r(f'tail{k}', f, (-8 * wind * k / 4 + w * hit, 0, 0))
        elif clip == 'Cast':
            r = max(0.0, 1 - abs(t - .6) / .2)
            a.r('tail4', f, (20 * r, 0, 0))
    return c.finish('crawler', extra)


def lizardman(eid):
    """리자드맨 — desert lizard warrior: slit golden eyes, fin crest, scimitar and brass buckler."""
    c = Monster(eid)
    scale, belly, red, brass = '#3aa57c', '#f1dda4', '#c2362f', '#d1a443'
    c.bone('body', (0, 0, .42)); c.bone('head', (0, -.03, .76), 'body'); c.bone('eyes', (0, -.2, .93), 'head')
    c.bone('jaw', (0, -.2, .84), 'head'); c.bone('crest', (0, .02, 1.04), 'head')
    c.orb('body', 'torso', (0, 0, .58), (.17, .14, .2), scale)
    c.orb('body', 'belly_plate', (0, -.1, .56), (.12, .07, .17), belly)
    for k in range(4):
        c.tube('body', f'belly_line{k}', [(-.09, -.16, .46 + k * .06), (0, -.175, .46 + k * .06), (.09, -.16, .46 + k * .06)], .005, '#c9ad72')
    c.ring('body', 'sash', (0, 0, .43), .16, .035, red, scale=(1, .9, 1))
    c.shape('body', 'loincloth', [(-.08, 0), (-.1, -.18), (0, -.22), (.1, -.18), (.08, 0)], (0, -.15, .42), red, depth=.02)
    c.tube('body', 'shoulder_strap', [(-.15, -.06, .72), (0, -.15, .58), (.14, -.08, .44)], .02, '#7a4a2a')
    h = Head((0, -.04, .93), (.18, .16, .16))
    c.orb('head', 'lizard_head', tuple(h.c), tuple(h.r), scale, seg=24, rings=14)
    m = Head((0, -.19, .86), (.11, .1, .065))
    c.orb('head', 'snout', tuple(m.c), tuple(m.r), '#4cb88d')
    for s in (-1, 1):
        p, n = m.point(s * .035, .89, .004)
        c.disc('head', f'nostril{s}', p, n, (.012, .01, .008), '#1c3b2e', seg=8, rings=4)
    c.eye_pair('eyes', h, .955, .085, .05, .058, '#ffc21f', '#fff07a', angry=.6, slit=True)
    c.orb('jaw', 'jaw', (0, -.16, .81), (.09, .09, .04), belly)
    for s in (-1, 1):
        c.cone_to('jaw', f'fang{s}', (s * .04, -.25, .83), (s * .04, -.255, .8), .012, '#ffffff')
    c.ring('head', 'headband', (0, -.02, 1.04), .15, .02, red, rot=(-18, 0, 0))
    c.tube('head', 'headband_tail', [(0, .13, 1.0), (.05, .22, .95), (.09, .26, .86)], .02, red, taper=.6)
    for k in range(5):
        y = -.06 + k * .07
        c.petal('crest', f'fin{k}', (0, y, 1.05 - k * .04), (0, .45, 1), .16 - k * .015, .1, '#ff8a3a', tip='#ffd04a', thick=.012, cup=.0)
    for s, side in ((-1, 'R'), (1, 'L')):
        c.bone('arm.' + side, (s * .16, -.01, .7), 'body'); c.bone('leg.' + side, (s * .09, 0, .4), 'body')
        c.orb('arm.' + side, 'pauldron' + side, (s * .18, 0, .73), (.08, .08, .06), '#8a5530')
        c.tube('arm.' + side, 'arm' + side, [(s * .17, -.01, .7), (s * .23, -.04, .58), (s * .25, -.1, .48)], .04, scale)
        c.orb('arm.' + side, 'hand' + side, (s * .25, -.12, .46), (.045, .045, .045), scale)
        c.thigh = c.orb('leg.' + side, 'thigh' + side, (s * .1, -.0, .32), (.08, .09, .11), scale)
        c.tube('leg.' + side, 'shin' + side, [(s * .11, .02, .24), (s * .12, .05, .12), (s * .12, -.02, .05)], .035, scale)
        c.orb('leg.' + side, 'foot' + side, (s * .12, -.07, .035), (.06, .1, .035), '#2f8a63')
        for j in range(3):
            c.cone_to('leg.' + side, f'toe_claw{side}{j}', (s * .12 + (j - 1) * .03, -.16, .03), (s * .12 + (j - 1) * .035, -.2, .01), .012, '#f5ead2')
    c.bone('tail1', (0, .12, .42), 'body'); c.bone('tail2', (0, .32, .2), 'tail1')
    c.tube('tail1', 'tail', [(0, .1, .44), (0, .22, .33), (0, .33, .2)], .07, scale, taper=.7)
    c.tube('tail2', 'tail_tip', [(0, .33, .2), (.04, .45, .08), (.08, .55, .04)], .05, scale, taper=.2)
    c.bone('weapon.R', (-.25, -.12, .46), 'arm.R'); c.bone('weapon.L', (.25, -.12, .46), 'arm.L')
    c.tube('weapon.R', 'hilt', [(-.25, -.12, .4), (-.25, -.12, .52)], .018, '#5a3a24')
    c.box('weapon.R', 'guard', (-.25, -.12, .53), (.12, .04, .025), brass, bevel=.008)
    c.shape('weapon.R', 'scimitar', [(-.025, 0), (-.03, .2), (-.015, .36), (.04, .48), (.09, .5), (.05, .38), (.035, .2), (.03, 0)], (-.25, -.12, .54), '#d3dde6', depth=.018)
    c.tube('weapon.R', 'scimitar_edge', [(-.27, -.132, .56), (-.265, -.132, .75), (-.25, -.132, .9), (-.2, -.132, 1.0)], .005, '#ffffff')
    c.orb('weapon.L', 'buckler', (.3, -.15, .5), (.13, .035, .13), brass, seg=24, rings=10)
    c.ring('weapon.L', 'buckler_rim', (.3, -.172, .5), .125, .012, '#8a5530', rot=(90, 0, 0))
    c.gem('weapon.L', 'buckler_gem', (.3, -.18, .5), (0, -1, 0), .035, .05, '#9ffff0', '#1fb3a0')
    return c.finish('biped')


def harpy(eid):
    """하피 — crimson desert harpy: owl-disc face with a gold beak, fanned wing-arms and talons."""
    c = Monster(eid)
    red, gold, cream, teal = '#c63b3a', '#f2b33d', '#ffe8c6', '#1fb9a8'
    c.bone('body', (0, 0, .6)); c.bone('head', (0, -.02, .8), 'body'); c.bone('eyes', (0, -.17, .92), 'head')
    c.bone('crest', (0, .02, 1.05), 'head'); c.bone('tail1', (0, .08, .52), 'body')
    c.orb('body', 'feather_body', (0, 0, .64), (.16, .14, .18), red)
    for k in range(5):
        ang = math.pi * (.15 + .7 * k / 4)
        c.petal('body', f'chest_fluff{k}', (.07 * math.cos(ang) * 1.2, -.11, .74), (math.cos(ang) * .6, -.4, -1), .14, .09, cream, tip='#ffd29a', cup=.3)
    c.ring('body', 'turquoise_necklace', (0, -.04, .77), .12, .015, gold, rot=(20, 0, 0))
    c.gem('body', 'necklace_gem', (0, -.16, .73), (0, -1, -.3), .028, .05, '#a8fff2', teal)
    h = Head((0, -.04, .92), (.17, .15, .16))
    c.orb('head', 'feather_hood', (0, .0, .94), (.19, .17, .18), red, seg=24, rings=14)
    face = Head((0, -.085, .91), (.14, .11, .13))
    c.orb('head', 'face_disc', tuple(face.c), tuple(face.r), cream, seg=22, rings=12)
    c.eye_pair('eyes', face, .93, .062, .045, .058, teal, '#b7fff0', angry=.55)
    p, n = face.point(0, .865, .0)
    c.cone_to('head', 'beak', tuple(p), (0, p.y - .06, .83), .03, gold, seg=8)
    c.blush('head', face, .87, .1, .028, '#ff9c8a')
    for k in range(5):
        x = (k - 2) * .05
        c.petal('crest', f'crest_plume{k}', (x, .02, 1.05), (x * 2.5, .5, 1), .22 - abs(k - 2) * .03, .07, red if k % 2 else gold, tip='#7a1f2a' if k % 2 else '#ff6a3a', cup=.2)
    for s, side in ((-1, 'R'), (1, 'L')):
        c.bone('wing.' + side, (s * .13, .02, .76), 'body')
        c.orb('wing.' + side, 'wing_shoulder' + side, (s * .17, .02, .74), (.08, .07, .08), red)
        for k in range(7):
            ang = math.radians(60 - k * 17)
            d = (s * math.cos(ang), .1, math.sin(ang))
            c.petal('wing.' + side, f'primary{side}{k}', (s * (.18 + .02 * k), .03, .74 - .01 * k), d, .32 + .04 * min(k, 6 - k), .17, red, tip=gold, cup=.15, thick=.014)
        for k in range(4):
            ang = math.radians(40 - k * 20)
            c.petal('wing.' + side, f'covert{side}{k}', (s * .18, .0, .76), (s * math.cos(ang), .05, math.sin(ang)), .18, .13, cream, tip='#ffd29a', cup=.2, thick=.012)
        c.gem('wing.' + side, f'wing_talon{side}', (s * .26, -.02, .86), (s * .3, -.2, 1), .018, .07, '#fff6e0', '#b88a4a', mat='M_Toon')
        c.bone('leg.' + side, (s * .07, 0, .5), 'body')
        c.orb('leg.' + side, 'thigh_feathers' + side, (s * .08, 0, .5), (.07, .07, .08), red)
        c.tube('leg.' + side, 'bird_leg' + side, [(s * .08, -.01, .44), (s * .09, -.03, .32)], .02, gold)
        for j in range(3):
            c.tube('leg.' + side, f'talon{side}{j}', [(s * .09, -.03, .32), (s * .09 + (j - 1) * .035, -.08, .29), (s * .09 + (j - 1) * .04, -.1, .25)], .011, '#3a2a2a', taper=.3)
    for k in range(5):
        x = (k - 2) * .05
        c.petal('tail1', f'tail_feather{k}', (x * .5, .1, .54), (x * 2, 1, -.6), .3 - abs(k - 2) * .04, .12, red, tip=teal if k == 2 else gold, cup=.15)
    return c.finish('fly')


BUILDERS = {'hellhound': hellhound, 'elite_hellhound': hellhound, 'flame_elemental': flame_elemental,
            'sand_scorpion': sand_scorpion, 'lizardman': lizardman, 'harpy': harpy}

if __name__ == '__main__':
    eid = sys.argv[sys.argv.index('--') + 1]
    BUILDERS[eid](eid)
