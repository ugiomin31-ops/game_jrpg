"""Haunted-crypt v2 species: ghost, mimic (+elite pandora), dark_knight (+elite), lich.
Run: blender -b --factory-startup -P Blender/enemies_c/crypt.py -- <id>
"""
import math
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from monster_kit import Monster, Head, A, INK  # noqa: E402


def ghost(eid):
    """원령 — classic sheet ghost with a tattered hem, sleepy menacing eyes, shackle and soul lantern."""
    c = Monster(eid)
    sheet, hem = '#ebe7ff', '#cfc6ff'
    c.bone('body', (0, 0, .55)); c.bone('eyes', (0, -.2, .9), 'body'); c.bone('tail1', (0, .02, .48), 'body')
    c.add('body', A.lathe('ghost_sheet', [(0, 1.13), (.11, 1.11), (.19, 1.03), (.225, .9), (.235, .75), (.26, .6), (.29, .5)], color=sheet, mat='M_Clear', seg=26))
    h = Head((0, 0, .88), (.225, .225, .25))
    for k in range(9):
        ang = math.tau * k / 9
        c.petal('tail1', f'tattered_hem{k}', (.27 * math.cos(ang), .27 * math.sin(ang), .52), (math.cos(ang) * .35, math.sin(ang) * .35, -1), .2 + .05 * (k % 2), .17, sheet, tip=hem, mat='M_Clear', cup=.2)
    c.eye_pair('eyes', h, .9, .095, .068, .085, '#7a3cff', '#d9bcff', angry=.4, lid_color='#d9d3fb')
    c.blush('body', h, .8, .16, .04, '#c9b4ff')
    c.open_mouth('body', h, .76, .05, .045, tongue='#9b7bd6', inner='#2b1640')
    for s, side in ((-1, 'R'), (1, 'L')):
        c.bone('arm.' + side, (s * .2, -.02, .78), 'body')
        c.tube('arm.' + side, 'sleeve' + side, [(s * .2, -.02, .78), (s * .3, -.09, .7), (s * .33, -.14, .64)], .05, sheet, 'M_Clear', taper=.55)
    c.ring('arm.R', 'shackle', (-.3, -.1, .68), .045, .014, '#6a6f7e', rot=(30, 0, 30))
    for k in range(3):
        c.ring('arm.R', f'chain_link{k}', (-.33 - k * .025, -.13 - k * .02, .6 - k * .06), .025, .008, '#6a6f7e', rot=(90 * (k % 2), 30, 0))
    c.bone('weapon.L', (.33, -.14, .64), 'arm.L')
    c.tube('weapon.L', 'lantern_chain', [(.33, -.14, .64), (.34, -.16, .52)], .006, '#3b3542')
    c.box('weapon.L', 'lantern_cap', (.34, -.16, .51), (.08, .08, .025), '#2b2632', bevel=.008)
    c.orb('weapon.L', 'soul_flame', (.34, -.16, .44), (.04, .04, .055), '#7dff9a', 'M_Emit')
    c.add('weapon.L', A.lathe('lantern_glass', [(.045, .38), (.05, .44), (.045, .5)], loc=(.34, -.16, 0), color='#bfffd0', mat='M_Clear', seg=12))
    for k in range(4):
        ang = math.tau * k / 4 + .4
        c.tube('weapon.L', f'lantern_bar{k}', [(.34 + .05 * math.cos(ang), -.16 + .05 * math.sin(ang), .38), (.34 + .05 * math.cos(ang), -.16 + .05 * math.sin(ang), .5)], .005, '#2b2632')
    c.box('weapon.L', 'lantern_base', (.34, -.16, .375), (.075, .075, .02), '#2b2632', bevel=.006)

    def extra(a, clip, f, t, i, names):
        a.r('tail1', f, (4 * math.sin(math.tau * t * 2), 0, 12 * math.sin(math.tau * t)))
    return c.finish('float', extra)


def mimic(eid):
    """미믹 / elite 판도라 상자 — treasure chest whose lid is a toothy jaw; tongue, claws, angry eyes."""
    c = Monster(eid); el = c.elite
    wood = '#8b5a32' if not el else '#3c2150'
    wood_dk = '#5e3a1f' if not el else '#26122f'
    gold = '#e3b44a'
    iron = '#4a4550' if not el else gold
    c.bone('body', (0, 0, .1)); c.bone('lid', (0, .2, .4), 'body'); c.bone('eyes', (0, -.25, .47), 'lid')
    c.box('body', 'chest_base', (0, 0, .23), (.62, .42, .34), wood, bevel=.03)
    c.box('body', 'mouth_dark', (0, -.0, .39), (.56, .36, .04), '#2a0c1c', bevel=.01)
    for x in (-.24, .24):
        c.box('body', f'base_band{x}', (x, 0, .23), (.05, .44, .36), iron, bevel=.012)
    c.box('body', 'base_rim', (0, 0, .385), (.64, .44, .035), gold, bevel=.01)
    c.box('body', 'lock_plate', (0, -.215, .3), (.1, .02, .1), gold, bevel=.01)
    c.orb('body', 'keyhole', (0, -.228, .3), (.016, .008, .025), '#1c0f12', seg=8, rings=4)
    for k in range(7):
        x = (k - 3) * .08
        c.cone_to('body', f'low_tooth{k}', (x, -.215, .38), (x, -.222, .44), .022, '#fff6e2', seg=8)
    c.tube('body', 'tongue', [(0, .0, .4), (0, -.14, .43), (.02, -.26, .38), (.05, -.3, .26)], .045, '#d9547c', taper=.6)
    lid_z = .46
    c.box('lid', 'lid_slab', (0, 0, lid_z - .02), (.63, .43, .07), wood, bevel=.02)
    lid = A.cyl('lid_dome', r=.215, depth=.62, loc=(0, 0, lid_z), rot=(0, 90, 0), scale=(1, 1, 1), color=wood, seg=20)
    c.add('lid', lid)
    lid.scale = (.6, 1, 1)
    for x in (-.24, .24):
        band = A.cyl(f'lid_band{x}', r=.222, depth=.05, loc=(x, 0, lid_z), rot=(0, 90, 0), color=iron, seg=20)
        band.scale = (.62, 1, 1)
        c.add('lid', band)
    c.box('lid', 'lid_rim', (0, -.002, .425), (.64, .44, .03), gold, bevel=.01)
    for k in range(7):
        x = (k - 3) * .08 + .04 * (k < 6)
        if k == 6:
            continue
        c.cone_to('lid', f'up_tooth{k}', (x, -.215, .43), (x, -.222, .37), .024, '#fff6e2', seg=8)
    face = Head((0, .0, .5), (2.0, .226, 2.0))
    c.eye_pair('eyes', face, .5, .13, .06, .055, '#ffcf2a' if not el else '#ff3df0', '#fff2a0' if not el else '#ffb3fa', angry=1.0)
    for s, side in ((-1, 'R'), (1, 'L')):
        c.bone('leg.' + side, (s * .22, -.1, .08), 'body')
        c.orb('leg.' + side, 'claw_foot' + side, (s * .24, -.15, .05), (.07, .08, .05), wood_dk)
        for j in range(3):
            c.cone_to('leg.' + side, f'foot_claw{side}{j}', (s * .24 + (j - 1) * .035, -.21, .05), (s * .24 + (j - 1) * .04, -.26, .01), .015, '#efe0c8')
        c.orb('body', 'back_foot' + side, (s * .24, .15, .04), (.06, .07, .04), wood_dk)
    if el:
        c.gem('lid', 'crown_gem', (0, -.05, .6), (0, -.3, 1), .06, .14, '#ff9cf5', '#a521c9')
        for s in (-1, 1):
            c.tube('lid', f'demon_horn{s}', [(s * .22, .0, .55), (s * .33, .02, .64), (s * .36, .08, .78)], .04, '#1c1222', taper=.2)
            c.gem('lid', f'side_gem{s}', (s * .12, -.2, .55), (0, -1, .5), .025, .05, '#ffe28a', '#d18a12')
            c.shape('body', f'rune_diamond{s}', [(-.035, 0), (0, .05), (.035, 0), (0, -.05)], (s * .17, -.216, .25), '#ff6ff2', depth=.01, mat='M_Emit')
            c.ring('body', f'rune_circle{s}', (s * .17, -.216, .25), .055, .006, '#ff6ff2', rot=(90, 0, 0), mat='M_Emit')
        for k in range(5):
            ang = math.pi * k / 4
            c.cone_to('lid', f'crown_spike{k}', (.16 * math.cos(ang), .05, .58 + .05 * math.sin(ang)), (.2 * math.cos(ang), .06, .68 + .06 * math.sin(ang)), .025, gold)
    return c.finish('hop')


def dark_knight(eid):
    """암흑 기사 / elite 칠흑의 기사단장 — horned helm with a burning visor slit, cape and runic greatsword."""
    c = Monster(eid); el = c.elite
    steel, hi = ('#2d3040', '#5a6078') if not el else ('#1b1a22', '#3c3a48')
    trim = '#7b4cc9' if not el else '#d9ad48'
    cape = '#4a1d5e' if not el else '#7a1424'
    c.bone('body', (0, 0, .45)); c.bone('head', (0, -.02, .86), 'body'); c.bone('eyes', (0, -.2, .96), 'head')
    c.bone('crest', (0, .02, 1.12), 'head'); c.bone('cape', (0, .14, .82), 'body')
    c.orb('body', 'breastplate', (0, -.02, .64), (.19, .15, .2), steel)
    c.orb('body', 'chest_shine', (-.07, -.14, .7), (.05, .02, .07), hi)
    c.tube('body', 'chest_trim', [(-.16, -.1, .76), (0, -.17, .66), (.16, -.1, .76)], .015, trim)
    c.gem('body', 'chest_rune', (0, -.17, .62), (0, -1, 0), .03, .05, '#d9a8ff' if not el else '#ffd98a', trim)
    c.orb('body', 'waist', (0, 0, .46), (.15, .12, .08), '#1c1c26')
    c.ring('body', 'belt', (0, 0, .46), .15, .022, trim, scale=(1, .82, 1))
    for k, x in enumerate((-.1, 0, .1)):
        c.box('body', f'tasset{k}', (x, -.11, .37), (.09, .03, .12), steel, bevel=.012, rot=(10, 0, 0))
    h = Head((0, -.03, .96), (.19, .18, .18))
    c.orb('head', 'helm', tuple(h.c), tuple(h.r), steel, seg=24, rings=14)
    p, n = h.point(0, .95, .0)
    c.disc('head', 'visor_slit', p, n, (.15, .02, .035), '#08060c', seg=14, rings=6)
    c.glow_eyes('eyes', h, .955, .06, .035, .02, '#ff2e4a' if not el else '#ffcc33', slant=10)
    for k in range(3):
        a, _ = h.point(0, .9 - k * .035, .01)
        c.tube('head', f'breath_vent{k}', [(a.x - .06, a.y, a.z), (a.x + .06, a.y, a.z)], .007, '#08060c')
    c.tube('head', 'helm_ridge', [(0, -.2, 1.0), (0, -.1, 1.13), (0, .08, 1.14), (0, .18, 1.03)], .02, trim)
    horn_len = 1.0 if not el else 1.35
    for s in (-1, 1):
        c.tube('head', f'helm_horn{s}', [(s * .15, -.02, 1.02), (s * .28, .0, 1.06), (s * (.33 + .05 * horn_len), .03, 1.1 + .15 * horn_len)], .04, '#191720' if not el else trim, taper=.15)
    if el:
        for k in range(5):
            x = (k - 2) * .04
            c.flame('crest', f'aura_flame{k}', (x, .04, 1.12), .28 - abs(k - 2) * .05, .045, outer='#a24bff', inner='#e6c7ff', lean=(x, .15, 0))
    else:
        for k in range(4):
            c.petal('crest', f'plume{k}', (0, .02 + k * .04, 1.13), (0, .7 + k * .3, 1), .2, .08, '#7b3fb8', tip='#c19cff', cup=.2)
    for s, side in ((-1, 'R'), (1, 'L')):
        c.bone('arm.' + side, (s * .2, 0, .76), 'body'); c.bone('leg.' + side, (s * .1, 0, .4), 'body')
        c.orb('arm.' + side, 'pauldron' + side, (s * .23, 0, .78), (.12, .12, .09), steel)
        c.ring('arm.' + side, 'pauldron_trim' + side, (s * .23, 0, .74), .11, .012, trim)
        for j in range(2 if not el else 3):
            c.cone_to('arm.' + side, f'pauldron_spike{side}{j}', (s * (.25 + j * .03), .02, .84), (s * (.32 + j * .05), .03, .97 - j * .03), .025, hi if not el else trim)
        c.tube('arm.' + side, 'arm' + side, [(s * .22, -.01, .7), (s * .26, -.05, .56)], .045, '#22232e')
        c.box('arm.' + side, 'gauntlet' + side, (s * .27, -.08, .5), (.1, .1, .11), steel, bevel=.02)
        c.orb('leg.' + side, 'thigh' + side, (s * .1, 0, .3), (.08, .08, .1), '#22232e')
        c.box('leg.' + side, 'greave' + side, (s * .11, -.02, .15), (.11, .12, .17), steel, bevel=.025)
        c.box('leg.' + side, 'sabaton' + side, (s * .11, -.07, .04), (.11, .18, .07), steel, bevel=.02)
        c.orb('leg.' + side, 'knee_cop' + side, (s * .11, -.07, .24), (.05, .03, .045), hi)
    c.shape('cape', 'cape', [(-.2, .02), (-.27, -.5), (-.15, -.44), (-.06, -.56), (.04, -.47), (.15, -.55), (.27, -.48), (.2, .02)], (0, .15, .8), cape, depth=.025)
    c.bone('weapon.R', (-.27, -.08, .5), 'arm.R')
    c.tube('weapon.R', 'sword_grip', [(-.27, -.1, .4), (-.27, -.1, .55)], .02, '#3a2a30')
    c.orb('weapon.R', 'pommel', (-.27, -.1, .385), (.025, .025, .025), trim)
    c.box('weapon.R', 'crossguard', (-.27, -.1, .57), (.2, .045, .035), trim, bevel=.01)
    c.shape('weapon.R', 'greatsword', [(-.05, 0), (-.055, .55), (0, .66), (.055, .55), (.05, 0)], (-.27, -.1, .59), '#9aa2b8' if not el else '#2b2836', depth=.02)
    c.tube('weapon.R', 'sword_rune', [(-.27, -.112, .63), (-.27, -.112, 1.1)], .008, '#c58cff' if not el else '#ffcc55', 'M_Emit')
    if el:
        c.bone('weapon.L', (.27, -.08, .5), 'arm.L')
        c.orb('weapon.L', 'kite_shield', (.31, -.15, .52), (.15, .03, .2), steel, seg=20, rings=10)
        c.ring('weapon.L', 'shield_rim', (.31, -.17, .52), .15, .014, trim, rot=(90, 0, 0), scale=(1, 1.3, 1))
        c.gem('weapon.L', 'shield_gem', (.31, -.18, .54), (0, -1, 0), .04, .06, '#ffe08a', '#c4861a')
    return c.finish('biped')


def lich(eid):
    """꼬마 리치 — crowned skull mage in a floating violet robe, bony hands and a soul-gem staff."""
    c = Monster(eid)
    robe, robe_dk, bone, gold, soul = '#4b2f7a', '#2a1a45', '#efe6cf', '#d9ad48', '#6dff8f'
    c.bone('body', (0, 0, .55)); c.bone('head', (0, -.02, .84), 'body'); c.bone('eyes', (0, -.19, .95), 'head')
    c.bone('crest', (0, 0, 1.08), 'head'); c.bone('orbit', (0, 0, .7), 'body'); c.bone('tail1', (0, 0, .4), 'body')
    c.add('body', A.lathe('robe', [(.05, .34), (.27, .36), (.25, .45), (.19, .62), (.15, .78), (.1, .86), (0, .87)], color=robe, seg=26))
    c.ring('body', 'robe_trim', (0, 0, .37), .265, .016, gold)
    c.tube('body', 'robe_front_trim', [(0, -.17, .76), (0, -.22, .55), (0, -.265, .38)], .013, gold)
    for k in range(9):
        ang = math.tau * k / 9
        c.petal('tail1', f'ragged_hem{k}', (.24 * math.cos(ang), .24 * math.sin(ang), .38), (math.cos(ang) * .3, math.sin(ang) * .3, -1), .16 + .04 * (k % 2), .14, robe_dk, tip='#1a0f2c', cup=.2)
    for k in range(5):
        ang = math.pi * (.1 + .8 * k / 4)
        c.petal('body', f'high_collar{k}', (.14 * math.cos(ang), .07, .84), (math.cos(ang) * .8, .4, 1), .18, .1, '#5e3f96', tip=robe_dk, cup=.3)
    h = Head((0, -.03, .96), (.165, .15, .155))
    c.orb('head', 'skull', tuple(h.c), tuple(h.r), bone, seg=22, rings=12)
    c.orb('head', 'skull_jaw', (0, -.08, .85), (.1, .09, .05), bone)
    for s in (-1, 1):
        p, n = h.point(s * .065, .965, .0)
        c.disc('head', f'eye_socket{s}', p, n, (.055, .02, .06), '#140a1e', seg=12, rings=6)
    c.glow_eyes('eyes', h, .965, .065, .03, .035, soul)
    for e in c.parts['eyes'][-2:]:
        e.location.y -= .01
    p, n = h.point(0, .905, .0)
    c.disc('head', 'nasal', p, n, (.018, .012, .022), '#140a1e', seg=8, rings=4)
    for k in range(6):
        c.box('head', f'tooth{k}', ((k - 2.5) * .025, -.165, .855), (.018, .012, .025), '#fffaf0', bevel=.003)
    c.ring('crest', 'circlet', (0, -.02, 1.06), .15, .018, gold, rot=(-10, 0, 0))
    for k in range(5):
        ang = math.pi * (.1 + .8 * k / 4)
        p = (.15 * math.cos(ang), -.02 - .15 * math.sin(ang) * .96, 1.06 + .03 * math.sin(ang))
        c.cone_to('crest', f'crown_point{k}', p, (p[0] * 1.05, p[1] * 1.05, p[2] + .09 + .04 * (k == 2)), .022, gold)
    c.gem('crest', 'crown_gem', (0, -.17, 1.07), (0, -1, .3), .03, .05, '#b6ffc8', '#18b85a')
    for s, side in ((-1, 'R'), (1, 'L')):
        c.bone('arm.' + side, (s * .17, -.02, .74), 'body')
        c.tube('arm.' + side, 'sleeve' + side, [(s * .15, -.02, .76), (s * .25, -.07, .66), (s * .29, -.1, .6)], .05, robe, taper=1.4)
        c.orb('arm.' + side, 'bone_palm' + side, (s * .31, -.13, .55), (.035, .03, .04), bone)
        for j in range(4):
            c.tube('arm.' + side, f'bone_finger{side}{j}', [(s * .31 + (j - 1.5) * .018, -.14, .53), (s * .31 + (j - 1.5) * .024, -.17, .48)], .007, bone, taper=.6)
    c.bone('weapon.R', (-.31, -.13, .55), 'arm.R')
    c.tube('weapon.R', 'staff', [(-.33, -.14, .2), (-.32, -.14, .95)], .015, '#3b2a24')
    for k in range(3):
        ang = math.tau * k / 3
        c.tube('weapon.R', f'staff_claw{k}', [(-.32, -.14, .95), (-.32 + .05 * math.cos(ang), -.14 + .05 * math.sin(ang), 1.02), (-.32 + .025 * math.cos(ang), -.14 + .025 * math.sin(ang), 1.09)], .008, '#3b2a24')
    c.orb('weapon.R', 'soul_gem', (-.32, -.14, 1.03), (.04, .04, .05), soul, 'M_Emit')
    for k in range(3):
        ang = math.tau * k / 3
        c.flame('orbit', f'soul_wisp{k}', (.36 * math.cos(ang), .3 * math.sin(ang), .62 + .08 * k), .12, .035, outer='#55f08a', inner='#d4ffe0', lean=(0, .03, 0), seg=8)

    def extra(a, clip, f, t, i, names):
        a.r('tail1', f, (3 * math.sin(math.tau * t * 2), 0, 8 * math.sin(math.tau * t)))
    return c.finish('float', extra)


BUILDERS = {'ghost': ghost, 'mimic': mimic, 'elite_mimic': mimic, 'dark_knight': dark_knight,
            'elite_dark_knight': dark_knight, 'lich': lich}

if __name__ == '__main__':
    eid = sys.argv[sys.argv.index('--') + 1]
    BUILDERS[eid](eid)
