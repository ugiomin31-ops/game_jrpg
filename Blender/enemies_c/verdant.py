"""Verdant-ruins v2 species: horned_rabbit, killer_bee, mandragora, rhino_beetle (+elite), pixie.
Run: blender -b --factory-startup -P Blender/enemies_c/verdant.py -- <id>
"""
import math
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from monster_kit import Monster, Head, A, INK  # noqa: E402
from mathutils import Vector  # noqa: E402


def horned_rabbit(eid):
    """뿔토끼 — fluffy B1 hopper with a spiral unicorn horn and a leaf scarf."""
    c = Monster(eid)
    fur, shade, pink = '#f7f1e8', '#e2d6c8', '#ffb3c4'
    c.bone('body', (0, 0, .22)); c.bone('head', (0, -.01, .40), 'body'); c.bone('eyes', (0, -.2, .52), 'head')
    c.bone('tail1', (0, .17, .2), 'body')
    c.orb('body', 'round_body', (0, .02, .25), (.2, .19, .19), fur)
    c.orb('body', 'belly', (0, -.12, .23), (.13, .07, .13), '#fffbf4')
    h = Head((0, -.02, .53), (.26, .22, .22))
    c.orb('head', 'big_head', tuple(h.c), tuple(h.r), fur, seg=28, rings=16)
    for s in (-1, 1):
        c.orb('head', f'cheek_fluff{s}', (s * .2, -.08, .46), (.09, .08, .07), fur)
        for k in range(3):
            c.cone_to('head', f'cheek_tuft{s}{k}', (s * .25, -.06, .47 - k * .03), (s * (.33 + k * .01), -.07, .45 - k * .05), .028, fur)
    c.eye_pair('eyes', h, .53, .105, .058, .072, '#3b6fd6', '#9be1ff', angry=.55)
    c.blush('head', h, .46, .17, .045)
    p, n = h.point(0, .475, .01)
    c.disc('head', 'nose', p, n, (.026, .02, .018), '#ff8fae')
    c.cat_mouth('head', h, .445, .032)
    for s in (-1, 1):
        p, n = h.point(s * .013, .418, .006)
        c.disc('head', f'buck_tooth{s}', p, n, (.012, .01, .02), '#ffffff', seg=8, rings=4)
    # spiral horn: ivory cone wrapped by gold bands
    base, _ = h.point(0, .69, -.02)
    tip = (0, base.y - .1, .98)
    c.cone_to('head', 'unicorn_horn', tuple(base), tip, .05, '#fff1cc', seg=12)
    for k in range(3):
        t = .2 + k * .22
        p = base.lerp(Vector(tip), t)
        c.ring('head', f'horn_band{k}', tuple(p), .042 * (1 - t) + .006, .008, '#e4b24e', rot=(-14, 0, 0))
    # ears with pink lining on their own bones (twitch)
    for s, side in ((-1, 'R'), (1, 'L')):
        c.bone('ear.' + side, (s * .11, .03, .7), 'head')
        ear = A.sphere('ear' + side, r=1, loc=(s * .17, .05, .86), scale=(.065, .035, .2), rot=(8, s * 24, 0), color=fur, seg=16, rings=10)
        c.add('ear.' + side, ear)
        inner = A.sphere('ear_in' + side, r=1, loc=(s * .165, .018, .86), scale=(.04, .02, .15), rot=(8, s * 24, 0), color=pink, seg=12, rings=8)
        c.add('ear.' + side, inner)
        c.bone('arm.' + side, (s * .14, -.03, .34), 'body'); c.bone('leg.' + side, (s * .1, 0, .13), 'body')
        c.orb('arm.' + side, 'paw' + side, (s * .17, -.11, .28), (.055, .05, .06), fur)
        c.orb('leg.' + side, 'foot' + side, (s * .11, -.07, .05), (.075, .12, .05), fur)
        c.orb('leg.' + side, 'foot_pad' + side, (s * .11, -.18, .055), (.04, .015, .03), pink, seg=10, rings=6)
        c.orb('leg.' + side, 'haunch' + side, (s * .14, .03, .14), (.09, .11, .1), shade)
    # leaf scarf: green collar + two leaf tails
    c.ring('body', 'leaf_scarf', (0, -.01, .375), .17, .035, '#58b947', scale=(1, .95, .7))
    c.petal('body', 'scarf_leaf_a', (-.03, -.17, .37), (-.35, -.25, -1), .16, .09, '#7ad354', tip='#3f8f2f')
    c.petal('body', 'scarf_leaf_b', (.03, -.17, .37), (.45, -.2, -1), .13, .08, '#7ad354', tip='#3f8f2f')
    c.orb('body', 'scarf_berry', (0, -.19, .37), (.03, .025, .03), '#ff5a5a')
    c.orb('tail1', 'puff_tail', (0, .22, .22), (.075, .07, .075), '#ffffff')
    return c.finish('hop')


def killer_bee(eid):
    """킬러비 — fat striped hornet, glassy double wings, glowing venom stinger."""
    c = Monster(eid)
    yel, blk, cream = '#ffc21f', '#2a1d26', '#fff0b8'
    c.bone('body', (0, 0, .62)); c.bone('head', (0, -.06, .76), 'body'); c.bone('eyes', (0, -.24, .86), 'head')
    c.bone('tail1', (0, .1, .58), 'body')
    c.orb('body', 'thorax', (0, 0, .64), (.16, .15, .15), '#d78a14')
    c.ring('body', 'fuzzy_collar', (0, -.02, .74), .13, .045, cream, scale=(1, 1, .8))
    h = Head((0, -.07, .87), (.2, .17, .175))
    c.orb('head', 'bee_head', tuple(h.c), tuple(h.r), yel, seg=26, rings=14)
    p, n = h.point(0, .99, .0)
    c.disc('head', 'brow_stripe', p, n, (.17, .03, .05), blk)
    c.eye_pair('eyes', h, .875, .088, .058, .068, '#e3352b', '#ffb35c', angry=.75)
    c.open_mouth('head', h, .785, .045, .03, fangs='#fff6dd')
    for s, side in ((-1, 'R'), (1, 'L')):
        a, _ = h.point(s * .06, .79, .01)
        c.cone_to('head', f'mandible{side}', tuple(a), (s * .03, a.y - .07, .74), .022, blk)
        c.bone('antenna.' + side, (s * .06, -.06, 1.02), 'head')
        c.tube('antenna.' + side, 'antenna' + side, [(s * .06, -.06, 1.0), (s * .1, -.1, 1.1), (s * .17, -.13, 1.16)], .012, blk)
        c.orb('antenna.' + side, 'antenna_tip' + side, (s * .18, -.135, 1.17), (.03, .03, .03), yel)
        c.bone('wing.' + side, (s * .08, .1, .74), 'body'); c.bone('wing2.' + side, (s * .08, .12, .68), 'body')
        big = [(0, 0), (.12, .14), (.32, .27), (.45, .27), (.48, .19), (.36, .08), (.15, -.02)]
        small = [(0, 0), (.13, .02), (.29, -.03), (.33, -.1), (.24, -.13), (.1, -.07)]
        c.shape('wing.' + side, 'wing' + side, [(s * x, z) for x, z in big], (s * .08, .13, .74), '#c8f2ff', depth=.012, mat='M_Clear')
        c.tube('wing.' + side, 'wing_vein' + side, [(s * .08, .12, .74), (s * .25, .12, .91), (s * .5, .12, .95)], .006, '#6aa9c9')
        c.shape('wing2.' + side, 'hindwing' + side, [(s * x, z) for x, z in small], (s * .08, .15, .68), '#d9f7ff', depth=.012, mat='M_Clear')
        c.bone('arm.' + side, (s * .12, -.06, .66), 'body'); c.bone('leg.' + side, (s * .07, .0, .54), 'body')
        c.tube('arm.' + side, 'arm' + side, [(s * .12, -.06, .66), (s * .19, -.12, .59), (s * .17, -.18, .55)], .024, blk)
        c.orb('arm.' + side, 'claw' + side, (s * .17, -.19, .54), (.035, .03, .03), yel)
        c.tube('leg.' + side, 'leg' + side, [(s * .07, 0, .55), (s * .11, -.02, .44), (s * .1, -.06, .37)], .02, blk, taper=.6)
    # striped abdomen hanging back, venom stinger
    for k, (y, z, r) in enumerate(((.15, .55, .14), (.24, .48, .15), (.32, .41, .13), (.38, .35, .1))):
        c.orb('tail1', f'abdomen{k}', (0, y, z), (r, r * .95, r * .85), yel if k % 2 == 0 else blk)
    c.cone_to('tail1', 'stinger', (0, .41, .3), (0, .45, .16), .04, '#3a2340', seg=10)
    c.orb('tail1', 'venom_drop', (0, .455, .145), (.025, .025, .035), '#c55bff', 'M_Emit')
    c.ring('body', 'waist', (0, .1, .58), .07, .03, blk, rot=(60, 0, 0))

    def extra(a, clip, f, t, i, names):
        hit = max(0.0, 1 - abs(t - .4) / .16)
        if clip == 'Attack':
            a.r('tail1', f, (-75 * hit, 0, 0))
        elif clip == 'Idle':
            a.r('tail1', f, (-8 * math.sin(math.tau * t), 0, 0))
    return c.finish('fly', extra)


def mandragora(eid):
    """만드라고라 — wailing root-bulb with leaf crown and a magenta bloom."""
    c = Monster(eid)
    skin, root, leaf = '#f0d2a8', '#b98a5e', '#5fbf4a'
    c.bone('body', (0, 0, .25)); c.bone('eyes', (0, -.23, .5), 'body'); c.bone('crest', (0, 0, .72), 'body')
    h = Head((0, 0, .44), (.25, .22, .28))
    c.orb('body', 'root_bulb', tuple(h.c), tuple(h.r), skin, seg=28, rings=16)
    c.orb('body', 'bulb_point', (0, .01, .2), (.12, .11, .12), skin)
    for k, z in enumerate((.3, .56)):
        rr = h.r.x * math.sqrt(max(0.0, 1 - ((z - h.c.z) / h.r.z) ** 2)) + .004
        c.ring('body', f'root_ring{k}', (0, 0, z), rr, .007, '#c79c70', scale=(1, h.r.y / h.r.x, 1))
    c.eye_pair('eyes', h, .5, .1, .058, .064, '#8a3fd1', '#e3a8ff', angry=.9, lid_color='#e2b98d')
    for s in (-1, 1):
        p, n = h.point(s * .12, .43, .01)
        c.disc('eyes', f'tear{s:+d}', p, n, (.022, .015, .04), '#9fe6ff', 'M_Clear', seg=10, rings=5)
    c.blush('body', h, .43, .18, .04)
    c.open_mouth('body', h, .37, .07, .075, fangs=None)
    for k in range(5):
        ang = math.tau * k / 5 + .3
        c.tube('body', f'root_hair{k}', [(.07 * math.cos(ang), .07 * math.sin(ang), .14), (.12 * math.cos(ang), .12 * math.sin(ang), .07), (.16 * math.cos(ang), .14 * math.sin(ang), .05)], .01, root, taper=.2)
    for k in range(6):
        ang = math.tau * k / 6 + .25
        d = (math.cos(ang) * .9, math.sin(ang) * .9, 1.0)
        c.petal('crest', f'crown_leaf{k}', (0, 0, .7), d, .3 + .05 * (k % 2), .14, leaf, tip='#2f8a35', cup=.35)
    c.tube('crest', 'flower_stalk', [(0, 0, .7), (.02, -.02, .86), (0, -.05, .98)], .016, '#3e8f37')
    for k in range(6):
        ang = math.tau * k / 6
        c.petal('crest', f'bloom_petal{k}', (0, -.05, .98), (math.cos(ang), math.sin(ang) - .3, .55), .11, .08, '#ff6fc6', tip='#c02d93', cup=.3)
    c.orb('crest', 'bloom_heart', (0, -.06, 1.0), (.035, .035, .03), '#ffe45c', 'M_Emit')
    for s, side in ((-1, 'R'), (1, 'L')):
        c.bone('arm.' + side, (s * .22, -.02, .45), 'body'); c.bone('leg.' + side, (s * .1, 0, .18), 'body')
        c.tube('arm.' + side, 'root_arm' + side, [(s * .22, -.02, .45), (s * .32, -.06, .4), (s * .36, -.1, .3)], .03, root, taper=.6)
        for j in range(3):
            c.tube('arm.' + side, f'root_finger{side}{j}', [(s * .36, -.1, .31), (s * (.37 + (j - 1) * .03), -.13, .25), (s * (.39 + (j - 1) * .04), -.12, .21)], .011, root, taper=.3)
        c.tube('leg.' + side, 'root_leg' + side, [(s * .09, 0, .2), (s * .13, -.03, .09), (s * .15, -.07, .02)], .038, root, taper=.7)
        for j in range(3):
            c.tube('leg.' + side, f'root_toe{side}{j}', [(s * .15, -.07, .03), (s * (.15 + (j - 1) * .045), -.14, .01)], .012, root, taper=.3)

    def extra(a, clip, f, t, i, names):
        wav = math.sin(math.tau * t)
        if clip == 'Cast':  # the scream: crown leaves flare
            r = max(0.0, 1 - abs(t - .6) / .25)
            a.s('crest', f, (1 + .35 * r, 1 + .35 * r, 1 - .1 * r))
            a.r('crest', f, (-8 * r, 0, 0))
        else:
            a.r('crest', f, (4 * wav, 6 * math.sin(math.tau * t + 1), 0))
    return c.finish('biped', extra)


def rhino_beetle(eid):
    """장수풍뎅이 / elite 강철 투구왕 — armoured six-legged tank with a forked horn."""
    c = Monster(eid); el = c.elite
    shell = '#3d6fa0' if el else '#2f6d4b'
    shell_hi = '#8fc0e8' if el else '#69b07d'
    dark = '#1a2230' if el else '#1c2b22'
    trim = '#e3b64c'
    c.bone('body', (0, .05, .3)); c.bone('head', (0, -.22, .32), 'body'); c.bone('eyes', (0, -.38, .33), 'head')
    for s in (-1, 1):
        c.orb('body', f'elytra{s}', (s * .11, .12, .37), (.15, .29, .18), shell, seg=24, rings=14)
        c.orb('body', f'elytra_gloss{s}', (s * .1, .02, .5), (.06, .1, .03), shell_hi)
    c.tube('body', 'elytra_seam', [(0, -.08, .53), (0, .12, .55), (0, .36, .43)], .012, dark)
    c.orb('body', 'pronotum', (0, -.13, .38), (.21, .15, .17), shell, seg=24, rings=14)
    c.orb('body', 'pronotum_gloss', (-.08, -.2, .48), (.05, .04, .03), shell_hi)
    c.orb('body', 'belly', (0, .05, .22), (.18, .3, .1), dark)
    c.cone_to('body', 'thorax_horn', (0, -.2, .5), (0, -.3, .64), .05, dark, seg=10)
    h = Head((0, -.29, .31), (.19, .14, .15))
    c.orb('head', 'beetle_head', tuple(h.c), tuple(h.r), dark if not el else '#26354a', seg=24, rings=12)
    c.eye_pair('eyes', h, .325, .095, .056, .066, '#ffcf2e', '#fff3a6', angry=.6)
    c.open_mouth('head', h, .24, .045, .025, fangs='#f2e3c4')
    horn = [(0, -.3, .43), (0, -.41, .49), (0, -.5, .61), (0, -.49, .76)]
    if el:
        horn = [(0, -.3, .43), (0, -.43, .5), (0, -.55, .66), (0, -.53, .86)]
    c.tube('head', 'great_horn', horn, .05 if not el else .06, '#3b2a22' if not el else '#2b3242', taper=.45)
    tip = horn[-1]
    for s in (-1, 1):
        c.cone_to('head', f'horn_fork{s}', tip, (s * .07, tip[1] - .02, tip[2] + .08), .022, trim if el else '#3b2a22')
    for s, side in ((-1, 'R'), (1, 'L')):
        c.bone('antenna.' + side, (s * .07, -.36, .4), 'head')
        c.tube('antenna.' + side, 'antenna' + side, [(s * .07, -.36, .4), (s * .14, -.42, .47)], .01, dark)
        c.orb('antenna.' + side, 'antenna_club' + side, (s * .15, -.43, .48), (.025, .025, .02), '#d9a33a')
        for k, y in enumerate((-.17, .0, .17)):
            b = f'leg{k + 1}.{side}'
            c.bone(b, (s * .15, y, .25), 'body')
            splay = (k - 1) * .07
            hip, knee, ankle, toe = (s * .15, y, .25), (s * .3, y + splay * .5, .3), (s * .38, y + splay, .1), (s * .42, y + splay * 1.6 - .04, .03)
            c.tube(b, f'femur{k}{side}', [hip, knee], .05, dark, taper=.85)
            c.orb(b, f'knee{k}{side}', knee, (.05, .05, .05), shell)
            c.tube(b, f'tibia{k}{side}', [knee, ankle], .042, dark, taper=.75)
            c.tube(b, f'tarsus{k}{side}', [ankle, toe], .028, dark, taper=.6)
            c.cone_to(b, f'leg_claw{k}{side}', toe, (toe[0] + s * .03, toe[1] - .05, .0), .018, '#d8c7a8')
            if el:
                c.cone_to(b, f'leg_spike{k}{side}', (s * .33, y, .22), (s * .42, y, .3), .02, trim)
    if el:
        for s in (-1, 1):
            c.tube('body', f'gold_edge{s}', [(s * .02, -.07, .5), (s * .2, .05, .42), (s * .24, .22, .32), (s * .14, .38, .3)], .014, trim)
        c.gem('body', 'shell_gem', (0, .14, .55), (0, .2, 1), .05, .1, '#9fffe9', '#2fb39a')
        for s in (-1, 1):
            for k in range(3):
                c.orb('body', f'rune_dot{s}{k}', (s * .1, .02 + k * .12, .545 - k * .05 - (k == 2) * .04), (.022, .03, .008), '#9fffe9', 'M_Emit')
            c.cone_to('body', f'gold_shoulder_horn{s}', (s * .12, -.16, .5), (s * .2, -.24, .62), .03, trim)
        c.gem('head', 'horn_gem', (0, -.41, .5), (0, -1, .35), .035, .07, '#9fffe9', '#2fb39a')

    return c.finish('crawler')


def pixie(eid):
    """숲의 요정 — flower-capped fairy healer with butterfly wings and a dandelion wand."""
    c = Monster(eid)
    skin = '#ffe1cd'
    c.bone('body', (0, 0, .6)); c.bone('head', (0, 0, .74), 'body'); c.bone('eyes', (0, -.15, .85), 'head')
    c.bone('crest', (0, 0, .98), 'head'); c.bone('orbit', (0, 0, .7), 'body')
    h = Head((0, -.01, .85), (.165, .145, .155))
    c.orb('head', 'pixie_face', tuple(h.c), tuple(h.r), skin, seg=26, rings=14)
    c.eye_pair('eyes', h, .845, .068, .045, .056, '#22a865', '#a6ffd0')
    c.blush('head', h, .8, .1, .03)
    c.cat_mouth('head', h, .79, .022)
    for k in range(11):
        ang = math.tau * k / 11 + math.pi / 2
        if abs(math.sin(ang) + 1) < .35:  # leave the face open
            continue
        d = (math.cos(ang), math.sin(ang), .25)
        c.petal('head', f'leaf_hair{k}', (h.c.x + .1 * math.cos(ang), h.c.y + .09 * math.sin(ang), .93), d, .17, .1, '#7ed957', tip='#3e9a3a', cup=.4)
    c.orb('head', 'hair_cap', (0, .01, .9), (.17, .15, .12), '#6bc24e')
    for s in (-1, 1):
        c.cone_to('head', f'pointy_ear{s}', (s * .15, -.01, .84), (s * .25, .0, .9), .03, skin)
    for k in range(5):
        ang = math.tau * k / 5
        c.petal('crest', f'hat_petal{k}', (0, 0, .98), (math.cos(ang), math.sin(ang), .7), .12, .09, '#ff9fd2', tip='#ff5aa8', cup=.3)
    c.orb('crest', 'hat_pistil', (0, 0, 1.0), (.03, .03, .03), '#ffe45a', 'M_Emit')
    c.orb('body', 'torso', (0, 0, .64), (.07, .06, .08), '#f9f3dc')
    for k in range(7):
        ang = math.tau * k / 7
        c.petal('body', f'skirt_petal{k}', (.03 * math.cos(ang), .03 * math.sin(ang), .62), (math.cos(ang), math.sin(ang), -1.1), .15, .1, '#ffb1dc', tip='#ff6fb7', cup=.3)
    for s, side in ((-1, 'R'), (1, 'L')):
        c.bone('leg.' + side, (s * .035, 0, .56), 'body'); c.bone('arm.' + side, (s * .07, -.01, .69), 'body')
        c.tube('leg.' + side, 'leg' + side, [(s * .035, 0, .56), (s * .045, -.01, .44)], .018, skin)
        c.orb('leg.' + side, 'leaf_shoe' + side, (s * .047, -.03, .43), (.025, .045, .022), '#4ea83f')
        c.tube('arm.' + side, 'arm' + side, [(s * .07, -.01, .69), (s * .13, -.04, .62), (s * .15, -.07, .57)], .016, skin)
        c.bone('wing.' + side, (s * .04, .07, .7), 'body')
        top = [(0, 0), (.1, .14), (.26, .26), (.34, .22), (.31, .1), (.16, .0)]
        low = [(0, 0), (.16, -.02), (.24, -.12), (.17, -.2), (.06, -.12)]
        c.shape('wing.' + side, 'wing_top' + side, [(s * x, z) for x, z in top], (s * .04, .09, .7), '#c2fbe0', depth=.01, mat='M_Clear')
        c.shape('wing.' + side, 'wing_low' + side, [(s * x, z) for x, z in low], (s * .04, .09, .7), '#d9f6ff', depth=.01, mat='M_Clear')
        c.orb('wing.' + side, 'wing_eyespot' + side, (s * .24, .082, .9), (.04, .006, .035), '#ff7fc9', 'M_Emit')
        c.orb('wing.' + side, 'wing_spot2' + side, (s * .16, .082, .58), (.03, .006, .025), '#7dffd3', 'M_Emit')
    c.bone('weapon.R', (-.15, -.07, .57), 'arm.R')
    c.tube('weapon.R', 'wand', [(-.15, -.07, .5), (-.16, -.08, .78)], .011, '#7a5236')
    c.orb('weapon.R', 'dandelion', (-.16, -.08, .82), (.06, .06, .06), '#fff8b0', 'M_Emit')
    for k in range(8):
        ang = math.tau * k / 8
        c.tube('weapon.R', f'fluff{k}', [(-.16, -.08, .82), (-.16 + .085 * math.cos(ang), -.08 + .02 * math.sin(ang), .82 + .085 * math.sin(ang))], .008, '#ffffff', taper=.2)
    for k in range(3):
        ang = math.tau * k / 3
        c.orb('orbit', f'sparkle{k}', (.32 * math.cos(ang), .25 * math.sin(ang), .66 + .08 * k), (.025, .025, .025), '#d6ff8a', 'M_Emit')
    return c.finish('float')


BUILDERS = {'horned_rabbit': horned_rabbit, 'killer_bee': killer_bee, 'mandragora': mandragora,
            'rhino_beetle': rhino_beetle, 'elite_rhino_beetle': rhino_beetle, 'pixie': pixie}

if __name__ == '__main__':
    eid = sys.argv[sys.argv.index('--') + 1]
    BUILDERS[eid](eid)
