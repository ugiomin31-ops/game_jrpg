"""Frost-grotto v2 species: frost_spider, snow_fairy, yeti (+elite), ice_golem.
Run: blender -b --factory-startup -P Blender/enemies_c/frost.py -- <id>
"""
import math
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from monster_kit import Monster, Head, A, INK  # noqa: E402


def snowflake(c, bone, name, center, r, color='#dffaff', mat='M_Emit', facing='Y', tube=.008):
    x, y, z = center
    for k in range(3):
        ang = math.pi * k / 3
        dx, dz = math.cos(ang) * r, math.sin(ang) * r
        if facing == 'Y':
            a, b = (x - dx, y, z - dz), (x + dx, y, z + dz)
        else:
            a, b = (x - dx, y - dz, z), (x + dx, y + dz, z)
        c.tube(bone, f'{name}_arm{k}', [a, b], tube, color, mat)
    c.orb(bone, name + '_core', center, (r * .25, r * .25, r * .25), color, mat)


def frost_spider(eid):
    """서리 거미 — round ice-blue spider: big anime eyes, frost-fur collar, crystal-studded abdomen."""
    c = Monster(eid)
    shell, navy, white = '#86cbf5', '#28467f', '#eefaff'
    c.bone('body', (0, .05, .3)); c.bone('head', (0, -.12, .36), 'body'); c.bone('eyes', (0, -.33, .42), 'head')
    c.bone('tail1', (0, .14, .38), 'body')
    h = Head((0, -.17, .38), (.2, .17, .17))
    c.orb('head', 'cephalothorax', tuple(h.c), tuple(h.r), shell, seg=26, rings=14)
    for k in range(9):
        ang = math.tau * k / 9
        c.cone_to('body', f'fur_tuft{k}', (.17 * math.cos(ang), -.02 + .05 * math.sin(ang), .4 + .15 * math.sin(ang)),
                  (.25 * math.cos(ang), .02 + .07 * math.sin(ang), .42 + .22 * math.sin(ang)), .04, white)
    c.eye_pair('eyes', h, .41, .085, .055, .066, '#22c8ff', '#c6fbff', angry=.35)
    c.glow_eyes('eyes', h, .5, .05, .022, .022, '#7af6ff', tag='small')
    c.blush('head', h, .35, .14, .035, '#a7c8ff')
    for s in (-1, 1):
        a, _ = h.point(s * .045, .3, .0)
        c.cone_to('head', f'chelicera{s}', tuple(a), (s * .035, a.y - .06, .24), .03, white)
        c.cone_to('head', f'palp{s}', (s * .12, a.y + .03, .3), (s * .16, a.y - .08, .22), .022, navy)
    c.orb('tail1', 'abdomen', (0, .27, .45), (.25, .27, .23), navy, seg=26, rings=14)
    c.orb('tail1', 'abdomen_frost', (0, .27, .55), (.2, .22, .13), '#3b6bb5')
    snowflake(c, 'tail1', 'back_flake', (0, .28, .68), .1, facing='Z')
    for k, (x, y, z, dx, dy) in enumerate(((-.14, .2, .58, -.6, -.2), (.14, .2, .58, .6, -.2), (-.12, .4, .55, -.5, .5), (.12, .4, .55, .5, .5), (0, .47, .5, 0, 1))):
        c.gem('tail1', f'ice_spike{k}', (x, y, z), (dx, dy, 1), .045, .16, '#d8fbff', '#3fb2ea')
    for s, side in ((-1, 'R'), (1, 'L')):
        for k, y in enumerate((-.22, -.1, .02, .14)):
            b = f'leg{k + 1}.{side}'
            spread = (k - 1.5) * .09
            c.bone(b, (s * .14, y, .32), 'body')
            knee = (s * .34, y + spread, .48)
            foot = (s * .5, y + spread * 1.8, .02)
            c.tube(b, f'leg_upper{k}{side}', [(s * .14, y, .32), knee], .036, navy)
            c.orb(b, f'leg_knee{k}{side}', knee, (.042, .042, .042), white)
            c.tube(b, f'leg_lower{k}{side}', [knee, foot], .03, navy, taper=.5)
            c.cone_to(b, f'leg_tip{k}{side}', (foot[0] * .97, foot[1], .1), foot, .02, white)

    def extra(a, clip, f, t, i, names):
        if clip == 'Idle':
            a.s('tail1', f, (1 + .03 * math.sin(math.tau * t), 1, 1 + .03 * math.sin(math.tau * t)))
        elif clip == 'Cast':
            r = max(0.0, 1 - abs(t - .6) / .2)
            a.r('tail1', f, (-25 * r, 0, 0))
    return c.finish('crawler', extra)


def snow_fairy(eid):
    """눈꽃 요정 — hooded snow sprite in a floating fur-trimmed cloak, crystal wings and flake staff."""
    c = Monster(eid)
    cloak, fur, skin = '#79c3f2', '#ffffff', '#fff1f2'
    c.bone('body', (0, 0, .5)); c.bone('head', (0, 0, .72), 'body'); c.bone('eyes', (0, -.15, .82), 'head')
    c.bone('crest', (0, .04, 1.0), 'head'); c.bone('orbit', (0, 0, .6), 'body')
    c.add('body', A.lathe('floating_cloak', [(.04, .27), (.22, .29), (.235, .36), (.19, .52), (.12, .68), (0, .73)], color=cloak, seg=28))
    c.ring('body', 'hem_fur', (0, 0, .3), .22, .04, fur)
    for k in range(10):
        ang = math.tau * k / 10
        c.cone_to('body', f'hem_icicle{k}', (.2 * math.cos(ang), .2 * math.sin(ang), .27), (.21 * math.cos(ang), .21 * math.sin(ang), .17 - .04 * (k % 2)), .028, '#c9f3ff', 'M_Clear')
    c.orb('body', 'snow_brooch', (0, -.15, .6), (.035, .02, .035), '#7ff0ff', 'M_Emit')
    snowflake(c, 'body', 'cloak_flake', (0, -.2, .45), .06, '#ffffff', 'M_Toon', tube=.007)
    h = Head((0, -.03, .83), (.15, .13, .14))
    c.orb('head', 'hood', (0, .02, .86), (.2, .18, .2), cloak, seg=24, rings=14)
    c.orb('head', 'face', tuple(h.c), tuple(h.r), skin, seg=24, rings=14)
    c.ring('head', 'hood_fur_rim', (0, -.12, .85), .15, .035, fur, rot=(90, 0, 0), scale=(1, 1.08, 1))
    for k in range(5):
        x = (k - 2) * .045
        a, _ = h.point(x, .95, .0)
        c.petal('head', f'silver_bang{k}', tuple(a), (x * 1.5, -.25, -1), .08, .06, '#e5f2ff', tip='#bcd6ff', cup=.3)
    c.eye_pair('eyes', h, .82, .065, .044, .056, '#3d87ff', '#b8f0ff')
    c.blush('head', h, .77, .1, .03)
    c.cat_mouth('head', h, .755, .02)
    c.tube('crest', 'hood_tip', [(0, .1, .98), (0, .17, 1.08), (.04, .26, 1.12)], .06, cloak, taper=.3)
    c.orb('crest', 'pompom', (.05, .28, 1.12), (.05, .05, .05), fur)
    for s, side in ((-1, 'R'), (1, 'L')):
        c.bone('arm.' + side, (s * .14, -.02, .62), 'body')
        c.tube('arm.' + side, 'sleeve' + side, [(s * .14, -.02, .62), (s * .22, -.07, .53)], .045, cloak, taper=1.2)
        c.orb('arm.' + side, 'mitten' + side, (s * .23, -.09, .5), (.045, .04, .045), fur)
        c.bone('wing.' + side, (s * .07, .14, .62), 'body')
        for k, (dx, dz, ln) in enumerate(((.9, .6, .26), (1, .1, .22), (.8, -.35, .16))):
            c.gem('wing.' + side, f'crystal_wing{k}{side}', (s * .07, .15, .62), (s * dx, .35, dz), .035, ln, '#e9fdff', '#55c8f5')
    c.bone('weapon.R', (-.23, -.09, .5), 'arm.R')
    c.tube('weapon.R', 'staff', [(-.24, -.1, .25), (-.24, -.1, .82)], .013, '#c8e8ff')
    snowflake(c, 'weapon.R', 'staff_flake', (-.24, -.1, .9), .08)
    c.gem('weapon.R', 'staff_gem', (-.24, -.1, .84), (0, 0, 1), .025, .12, '#ffffff', '#62d6ff')
    for k in range(3):
        ang = math.tau * k / 3
        snowflake(c, 'orbit', f'orbit_flake{k}', (.36 * math.cos(ang), .3 * math.sin(ang), .55 + .1 * k), .04, tube=.006)
    return c.finish('float')


def yeti(eid):
    """꼬마 설인 / elite 설산의 폭군 — snowball brawler with blue face and fists; elite wields an icicle club."""
    c = Monster(eid); el = c.elite
    fur = '#eef4ff' if not el else '#dfe7f7'
    shade = '#cfdcf1' if not el else '#b9c8e3'
    blue = '#86b4ea' if not el else '#5d84c9'
    c.bone('body', (0, 0, .32)); c.bone('head', (0, -.05, .55), 'body'); c.bone('eyes', (0, -.3, .62), 'head')
    c.bone('jaw', (0, -.25, .5), 'head')
    c.orb('body', 'snowball_body', (0, 0, .42), (.33, .29, .32), fur, seg=26, rings=14)
    c.orb('body', 'belly_patch', (0, -.2, .3), (.19, .1, .15), shade)
    h = Head((0, -.17, .62), (.19, .14, .15))
    c.orb('head', 'head_fur', (0, -.03, .7), (.27, .24, .21), fur, seg=24, rings=14)
    c.orb('head', 'blue_face', tuple(h.c), tuple(h.r), blue, seg=24, rings=14)
    c.eye_pair('eyes', h, .64, .085, .052, .06, '#ffb21f', '#ffef8c', angry=1.0 if el else .8)
    p, n = h.point(0, .585, .005)
    c.disc('head', 'snout', p, n, (.05, .03, .03), '#5a7fc0')
    c.open_mouth('jaw', h, .53, .075, .04, fangs='#ffffff')
    for s in (-1, 1):
        a, _ = h.point(s * .065, .505, .015)
        c.cone_to('jaw', f'tusk{s}', tuple(a), (s * .08, a.y - .02, .6), .018, '#fff8e8')
        horn = [(s * .16, -.04, .86), (s * .25, -.02, .95), (s * .28, .02, 1.05)]
        if el:
            horn = [(s * .16, -.04, .86), (s * .29, -.0, .93), (s * .36, .05, 1.06), (s * .32, .08, 1.18)]
        c.tube('head', f'horn{s}', horn, .045 if not el else .055, '#e8d8b6' if not el else '#30405f', taper=.25)
    for k in range(9):
        ang = math.pi * (k / 8)
        c.cone_to('head', f'crown_tuft{k}', (.2 * math.cos(ang), .04, .78 + .06 * math.sin(ang)), (.27 * math.cos(ang), .07, .9 + .07 * math.sin(ang)), .05, fur)
    for k in range(14):
        ang = math.tau * k / 14
        z = .3 + .12 * (k % 3)
        c.cone_to('body', f'fur_spike{k}', (.3 * math.cos(ang), .26 * math.sin(ang), z), (.4 * math.cos(ang), .34 * math.sin(ang), z - .06), .055, fur)
    for s, side in ((-1, 'R'), (1, 'L')):
        c.bone('arm.' + side, (s * .3, -.02, .5), 'body'); c.bone('leg.' + side, (s * .15, 0, .14), 'body')
        c.orb('arm.' + side, 'furry_arm' + side, (s * .38, -.04, .38), (.12, .12, .19), fur)
        c.orb('arm.' + side, 'blue_fist' + side, (s * .42, -.1, .2), (.11, .1, .095), blue)
        for j in range(3):
            c.gem('arm.' + side, f'ice_knuckle{side}{j}', (s * .42 + (j - 1) * .045, -.17, .26), (s * .2 * (j - 1), -.5, 1), .022, .08, '#e6fcff', '#58c3f3')
        c.orb('leg.' + side, 'foot' + side, (s * .16, -.07, .06), (.11, .14, .07), fur)
        c.orb('leg.' + side, 'sole' + side, (s * .16, -.19, .055), (.07, .02, .05), blue)
    if el:
        for s, side in ((-1, 'R'), (1, 'L')):
            for j in range(4):
                c.gem('arm.' + side, f'shoulder_ice{side}{j}', (s * (.32 + j * .03), .0, .58 - j * .02), (s * (.4 + j * .3), -.1 + j * .1, 1), .05, .2 - j * .02, '#e6fcff', '#3aa6e8')
        for s in (-1, 1):
            c.tube('body', f'rune_tattoo{s}', [(s * .03, -.27, .44), (s * .1, -.25, .38), (s * .06, -.26, .3)], .012, '#6ff2ff', 'M_Emit')
        c.bone('weapon.R', (-.42, -.12, .22), 'arm.R')
        c.tube('weapon.R', 'club_grip', [(-.42, -.14, .14), (-.42, -.16, .45)], .03, '#6b4a3a')
        c.gem('weapon.R', 'icicle_club', (-.42, -.16, .4), (0, -.15, 1), .1, .5, '#e9fdff', '#4fb8f2', mat='M_Clear', sides=7)
        for j in range(3):
            ang = math.tau * j / 3
            c.gem('weapon.R', f'club_spike{j}', (-.42 + .07 * math.cos(ang), -.18 + .07 * math.sin(ang), .62), (math.cos(ang), math.sin(ang), .3), .03, .12, '#e9fdff', '#4fb8f2')
    return c.finish('heavy')


def ice_golem(eid):
    """얼음 골렘 — faceted translucent ice chunks around a glowing core, snow-capped head, huge crystal fists."""
    c = Monster(eid)
    ice, snow, packed, deep = '#8fdcff', '#ffffff', '#cdeefc', '#5aa9e0'
    c.bone('body', (0, 0, .4)); c.bone('head', (0, -.08, .86), 'body'); c.bone('eyes', (0, -.25, .96), 'head')
    c.bone('crest', (0, -.05, 1.08), 'head')
    c.chunk('body', 'ice_torso', (0, 0, .64), (.34, .27, .3), ice, 'M_Clear', seed=3, seg=9, rings=6)
    c.chunk('body', 'chest_plate', (0, -.14, .68), (.24, .14, .2), packed, seed=4, seg=7, rings=5)
    c.orb('body', 'frost_core', (0, -.27, .68), (.075, .03, .075), '#5ff6ff', 'M_Emit')
    c.gem('body', 'core_shard', (0, -.29, .66), (0, -.3, 1), .035, .13, '#ffffff', '#5ff6ff')
    c.chunk('body', 'hip_chunk', (0, .0, .38), (.26, .22, .13), deep, seed=5, seg=8, rings=5)
    h = Head((0, -.1, .96), (.17, .14, .13))
    c.chunk('head', 'packed_head', tuple(h.c), (.19, .16, .15), packed, seed=6, seg=8, rings=6, jitter=.06)
    c.orb('crest', 'snow_cap', (0, -.08, 1.09), (.2, .17, .07), snow)
    for k, x in enumerate((-.11, 0, .11)):
        c.gem('crest', f'crown_icicle{k}', (x, -.05, 1.1), (x * 2.5, .15, 1), .045, .17 + .07 * (k == 1), '#e8fdff', '#59c3f5')
    for s in (-1, 1):
        p, n = h.point(s * .065, .965, .0)
        c.disc('eyes', f'eye_socket{s}', p, n, (.06, .02, .042), '#21476e', seg=12, rings=6, roll=-s * 14)
    c.glow_eyes('eyes', h, .96, .065, .045, .03, '#c8fdff', slant=14)
    c.parts['eyes'][-1].location.y -= .012; c.parts['eyes'][-2].location.y -= .012
    for s in (-1, 1):
        a, _ = h.point(s * .02, 1.0, .03)
        b, _ = h.point(s * .12, 1.04, .03)
        c.tube('head', f'ice_brow{s}', [tuple(a), tuple(b)], .018, '#3b6f9c')
    p, n = h.point(0, .88, .01)
    c.disc('head', 'mouth_crack', p, n, (.07, .02, .012), '#3b6f9c', seg=10, rings=4)
    for k in range(4):
        c.gem('body', f'back_crystal{k}', ((k - 1.5) * .12, .2, .74 + .05 * (k in (1, 2))), ((k - 1.5) * .45, .8, 1), .07, .32 - .06 * abs(k - 1.5), '#e3fcff', '#3fb0ee')
    for s, side in ((-1, 'R'), (1, 'L')):
        c.bone('arm.' + side, (s * .3, -.02, .78), 'body'); c.bone('leg.' + side, (s * .15, 0, .32), 'body')
        c.chunk('arm.' + side, 'shoulder_chunk' + side, (s * .38, -.02, .8), (.15, .15, .13), deep, seed=10 + s, seg=7, rings=5)
        c.orb('arm.' + side, 'shoulder_snow' + side, (s * .38, -.02, .9), (.14, .13, .06), snow)
        c.chunk('arm.' + side, 'forearm' + side, (s * .45, -.05, .58), (.13, .13, .17), ice, 'M_Clear', seed=12 + s, seg=7, rings=5)
        c.chunk('arm.' + side, 'crystal_fist' + side, (s * .48, -.1, .34), (.17, .16, .15), packed, seed=14 + s, seg=8, rings=6)
        for j in range(3):
            c.gem('arm.' + side, f'fist_spike{side}{j}', (s * .48 + (j - 1) * .08, -.18, .42), ((j - 1) * .4, -.5, 1), .04, .14, '#e9fdff', '#4fb8f2')
        c.gem('arm.' + side, 'shoulder_crystal' + side, (s * .42, .02, .9), (s * .5, .15, 1), .065, .24, '#e3fcff', '#3fb0ee')
        c.chunk('leg.' + side, 'leg_chunk' + side, (s * .17, 0, .2), (.12, .13, .13), ice, 'M_Clear', seed=16 + s, seg=7, rings=5)
        c.chunk('leg.' + side, 'foot_chunk' + side, (s * .18, -.05, .06), (.15, .18, .07), packed, seed=18 + s, seg=7, rings=5)
    return c.finish('heavy')


BUILDERS = {'frost_spider': frost_spider, 'snow_fairy': snow_fairy, 'yeti': yeti, 'elite_yeti': yeti, 'ice_golem': ice_golem}

if __name__ == '__main__':
    eid = sys.argv[sys.argv.index('--') + 1]
    BUILDERS[eid](eid)
