"""Hunter-theme monsters (monster v5, 아기자기 direction): goblin, goblin_shaman, sewer_rat, scrap_bot, cave_mole,
mummy_pup, orc, high_orc. Round chibi bodies, big glossy eyes, soft colours; nothing gross or creepy.

Built with the v3 sculpt kit (enemies_d/sculpt_kit.py) and produced by the shared runner:
  blender -b --factory-startup --python-exit-code 1 -P Blender/enemies_a/generate_all.py -- --asset goblin
"""
import math
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'enemies_d'))
from sculpt_kit import Sculpt, A, lerp_col, vgrad  # noqa: E402,F401
from monster_kit import cast_env, window  # noqa: E402
from mathutils import Vector  # noqa: E402


def _skin_tone(dark, light, z0, z1):
    return lambda p: lerp_col(dark, light, (p.z - z0) / (z1 - z0))


def goblin(eid):
    """고블린 — small green goblin: big pointed ears, oversized leather cap, cream belly, wooden club."""
    c = Sculpt(eid, tris=6500)
    skin, skin_d, belly, leather, wood = '#8fd166', '#5fae4a', '#e4f5a8', '#8a5a34', '#9a6a3c'
    tone = _skin_tone(skin_d, skin, 0.1, 0.8)
    c.bone('body', (0, 0, 0.3)); c.bone('head', (0, -0.02, 0.62), 'body'); c.bone('eyes', (0, -0.19, 0.64), 'head')
    c.bone('ear.L', (0.15, 0.0, 0.66), 'head'); c.bone('ear.R', (-0.15, 0.0, 0.66), 'head')
    c.bone('arm.L', (0.17, -0.01, 0.42), 'body'); c.bone('arm.R', (-0.17, -0.01, 0.42), 'body')
    c.bone('leg.L', (0.08, 0, 0.14), 'body'); c.bone('leg.R', (-0.08, 0, 0.14), 'body')
    c.bone('weapon.R', (-0.245, -0.09, 0.25), 'arm.R')
    # torso and head
    c.blob('body', (0, 0, 0.3), (0.17, 0.15, 0.17), tone)
    c.blob('body', (0, -0.08, 0.28), (0.11, 0.08, 0.12), belly, weight=1.2)
    c.blob('head', (0, -0.02, 0.62), (0.19, 0.17, 0.17), tone)
    c.blob('head', (0, -0.1, 0.53), (0.1, 0.07, 0.05), belly, weight=1.2)
    # oversized leather cap
    c.blob('head', (0, -0.01, 0.76), (0.165, 0.16, 0.085), leather)
    c.ring('head', 'cap_brim', (0, -0.04, 0.72), 0.19, 0.025, leather, rot=(-6, 0, 0), scale=(1, 0.92, 1))
    c.orb('head', 'cap_pom', (0, 0.02, 0.87), (0.04, 0.04, 0.04), '#ffd65a')
    # pointed ears: tapering fused tufts on their own bones so they flop
    for s, side in ((1, 'L'), (-1, 'R')):
        c.tuft('ear.' + side, (s * 0.14, 0.0, 0.66), (s * 1, 0.1, 0.45), 0.2, 0.04, skin_d, curl=0.0)
    # big round eyes with a small smile
    for s in (-1, 1):
        c.eye('eyes', (s * 0.08, -0.18, 0.63), (s * 0.25, -1, 0.1), 0.06, '#6a3a1a', sclera='#ffffff')
    c.paint((0, -0.19, 0.555), (0.035, 0.012, 0.008), '#3a2016')
    for s, side in ((1, 'L'), (-1, 'R')):
        c.paint((s * 0.12, -0.15, 0.58), (0.03, 0.01, 0.02), '#f59a9a')
    # arms and legs
    for s, side in ((1, 'L'), (-1, 'R')):
        c.limb('arm.' + side, [(s * 0.17, -0.01, 0.42), (s * 0.22, -0.05, 0.33), (s * 0.24, -0.08, 0.26)],
               [0.05, 0.042, 0.04], skin)
        c.blob('arm.' + side, (s * 0.25, -0.09, 0.245), (0.05, 0.05, 0.045), skin_d)
        c.limb('leg.' + side, [(s * 0.08, 0, 0.14), (s * 0.09, 0.0, 0.05)], [0.06, 0.05], skin_d)
        c.blob('leg.' + side, (s * 0.09, -0.05, 0.04), (0.07, 0.1, 0.04), leather)
    # wooden club held in the right hand
    c.tube('weapon.R', 'club_grip', [(-0.245, -0.09, 0.25), (-0.27, -0.13, 0.52)], 0.028, wood)
    c.orb('weapon.R', 'club_head', (-0.28, -0.14, 0.62), (0.085, 0.07, 0.11), wood)
    c.ring('weapon.R', 'club_band', (-0.28, -0.14, 0.56), 0.04, 0.012, '#c9a14a', rot=(0, 0, 0), scale=(1, 0.9, 1))
    c.follow['ear'] = 1.3

    def extra(a, clip, f, t, i, names):
        if clip == 'Attack':  # overhead club bonk: wind up over the head, slam down with a squash
            up = window(t, 0.02, 0.3, 0.36, 0.41)
            imp = math.exp(-(t - 0.4) * 16) if t >= 0.4 else 0.0
            ax, abd, tw = a.P.arm['R']
            a.r('arm.R', f, (ax + 105 * up, abd, -tw))
            a.s('body', f, (1 + 0.08 * imp, 1 + 0.08 * imp, 1 - 0.14 * imp))
    return c.finish('biped', extra)


def goblin_shaman(eid):
    """고블린 주술사 — a goblin shaman: feather headdress, cream poncho over the shoulders, a bone staff with a
    glowing blue orb. Casts by raising the staff and sending a soft blue burst."""
    c = Sculpt(eid, tris=6500)
    skin, skin_d, belly = '#8fd166', '#5fae4a', '#e4f5a8'
    poncho, poncho_d, feather, bone, orb = '#d9634a', '#b24a38', '#ffd65a', '#f4ecd8', '#7fe8ff'
    tone = _skin_tone(skin_d, skin, 0.1, 0.8)
    c.bone('body', (0, 0, 0.3)); c.bone('head', (0, -0.02, 0.62), 'body'); c.bone('eyes', (0, -0.19, 0.64), 'head')
    c.bone('ear.L', (0.15, 0.0, 0.66), 'head'); c.bone('ear.R', (-0.15, 0.0, 0.66), 'head')
    c.bone('arm.L', (0.17, -0.01, 0.42), 'body'); c.bone('arm.R', (-0.17, -0.01, 0.42), 'body')
    c.bone('leg.L', (0.08, 0, 0.14), 'body'); c.bone('leg.R', (-0.08, 0, 0.14), 'body')
    c.bone('weapon.R', (-0.245, -0.09, 0.25), 'arm.R')
    c.blob('body', (0, 0, 0.3), (0.17, 0.15, 0.17), tone)
    c.blob('body', (0, -0.08, 0.28), (0.11, 0.08, 0.12), belly, weight=1.2)
    # poncho: a soft cape-like mass over the shoulders, with a scalloped hem
    c.blob('body', (0, -0.01, 0.4), (0.22, 0.18, 0.1), poncho)
    c.blob('body', (0, 0.0, 0.31), (0.2, 0.17, 0.1), lambda p: poncho if p.z > 0.27 else poncho_d)
    for k in range(4):
        x = -0.15 + k * 0.1
        c.blob('body', (x, -0.12, 0.27), (0.04, 0.03, 0.03), poncho)
    c.blob('head', (0, -0.02, 0.62), (0.19, 0.17, 0.17), tone)
    c.blob('head', (0, -0.1, 0.53), (0.1, 0.07, 0.05), belly, weight=1.2)
    # feather headdress: a crown of fanned feathers
    for k, (x, z, d) in enumerate([(-0.1, 0.75, (-0.5, -0.1, 1)), (0.0, 0.79, (0, -0.1, 1)), (0.1, 0.75, (0.5, -0.1, 1))]):
        c.petal('head', f'feather{k}', (x, -0.02, z), d, 0.24, 0.07, feather, tip='#ff8a3a', thick=0.02, cup=0.2)
    c.blob('head', (0, -0.02, 0.75), (0.14, 0.14, 0.05), poncho_d)  # headband
    for s, side in ((1, 'L'), (-1, 'R')):
        c.tuft('ear.' + side, (s * 0.14, 0.0, 0.66), (s * 1, 0.1, 0.45), 0.2, 0.04, skin_d)
    for s in (-1, 1):
        c.eye('eyes', (s * 0.08, -0.18, 0.63), (s * 0.25, -1, 0.1), 0.06, '#2a4a8a', sclera='#ffffff')
    c.paint((0, -0.19, 0.555), (0.035, 0.012, 0.008), '#3a2016')
    for s, side in ((1, 'L'), (-1, 'R')):
        c.limb('arm.' + side, [(s * 0.17, -0.01, 0.42), (s * 0.22, -0.05, 0.33), (s * 0.24, -0.08, 0.26)],
               [0.05, 0.042, 0.04], skin)
        c.blob('arm.' + side, (s * 0.25, -0.09, 0.245), (0.05, 0.05, 0.045), skin_d)
        c.limb('leg.' + side, [(s * 0.08, 0, 0.14), (s * 0.09, 0.0, 0.05)], [0.06, 0.05], skin_d)
        c.blob('leg.' + side, (s * 0.09, -0.05, 0.04), (0.07, 0.1, 0.04), '#7a5a3a')
    # bone staff with a glowing orb (held in the right hand)
    c.tube('weapon.R', 'staff', [(-0.245, -0.09, 0.25), (-0.3, -0.1, 0.7), (-0.31, -0.1, 1.0)], 0.022, '#7a5030')
    c.orb('weapon.R', 'staff_orb', (-0.31, -0.1, 1.06), (0.085, 0.085, 0.085), orb, 'M_Emit')
    c.ring('weapon.R', 'staff_bone', (-0.305, -0.1, 0.92), 0.04, 0.012, bone, rot=(0, 0, 0))
    c.follow['ear'] = 1.3

    def extra(a, clip, f, t, i, names):
        if clip == 'Cast':  # staff raised and tipped forward on the release
            g, sh, burst, pop, settle = cast_env(t)
            a.r('weapon.R', f, (-30 * g + 45 * burst + 2 * sh, 0, 0))
    return c.finish('biped', extra)


def sewer_rat(eid):
    """땅굴쥐 — a chubby grey rat standing on its hind legs: a slightly bigger head with round ears that stand out
    from the yellow miner's hard hat, two buck teeth, a tiny helmet lamp, and a long curved pink tail."""
    c = Sculpt(eid, tris=6500)
    fur, belly, pink, helmet = '#bcb6c4', '#ece6f0', '#f2a7b6', '#f2c24a'
    c.bone('body', (0, 0, 0.28)); c.bone('head', (0, -0.04, 0.58), 'body'); c.bone('eyes', (0, -0.18, 0.62), 'head')
    c.bone('ear.L', (0.13, 0.0, 0.76), 'head'); c.bone('ear.R', (-0.13, 0.0, 0.76), 'head')
    c.bone('arm.L', (0.13, -0.02, 0.36), 'body'); c.bone('arm.R', (-0.13, -0.02, 0.36), 'body')
    c.bone('leg.L', (0.08, 0, 0.14), 'body'); c.bone('leg.R', (-0.08, 0, 0.14), 'body')
    c.bone('weapon.R', (-0.19, -0.12, 0.2), 'arm.R')
    c.bone('tail1', (0, 0.1, 0.26), 'body'); c.bone('tail2', (0, 0.3, 0.2), 'tail1')
    c.blob('body', (0, 0, 0.28), (0.16, 0.15, 0.18), fur)
    c.blob('body', (0, -0.08, 0.26), (0.11, 0.08, 0.13), belly, weight=1.2)
    c.blob('head', (0, -0.03, 0.58), (0.17, 0.16, 0.155), fur)
    c.limb('head', [(0, -0.1, 0.56), (0, -0.21, 0.52)], [0.075, 0.055], fur)
    c.blob('head', (0, -0.235, 0.52), (0.032, 0.027, 0.026), pink)
    c.blob('head', (0, -0.02, 0.69), (0.165, 0.155, 0.075), helmet)  # yellow miner's hard hat
    c.ring('head', 'hat_brim', (0, -0.02, 0.69), 0.172, 0.017, helmet)
    c.orb('head', 'lamp', (0, -0.18, 0.71), (0.03, 0.03, 0.03), '#fff6c0', 'M_Emit')
    for s_, side in ((1, 'L'), (-1, 'R')):
        c.blob('ear.' + side, (s_ * 0.13, 0.0, 0.76), (0.07, 0.03, 0.07), fur)  # round ears outside the hat
        c.paint((s_ * 0.13, -0.03, 0.76), (0.045, 0.01, 0.045), pink)
        c.limb('arm.' + side, [(s_ * 0.13, -0.02, 0.36), (s_ * 0.18, -0.08, 0.27), (s_ * 0.19, -0.12, 0.2)],
               [0.04, 0.035, 0.03], fur)
        c.blob('arm.' + side, (s_ * 0.19, -0.13, 0.19), (0.035, 0.035, 0.03), pink)
        c.limb('leg.' + side, [(s_ * 0.08, 0, 0.14), (s_ * 0.09, -0.02, 0.04)], [0.05, 0.045], fur)
        c.blob('leg.' + side, (s_ * 0.09, -0.06, 0.03), (0.05, 0.08, 0.03), pink)
    for s_ in (-1, 1):
        c.eye('eyes', (s_ * 0.07, -0.17, 0.61), (s_ * 0.2, -1, 0.1), 0.05, '#2a1a20', sclera='#ffffff')
        c.blob('head', (s_ * 0.018, -0.245, 0.465), (0.012, 0.012, 0.02), '#fffaf0', weight=0.5)  # buck teeth
    # long curved pink tail: arcs up off the back and curls at the tip
    c.limb(['tail1', 'tail1', 'tail2', 'tail2', 'tail2'],
           [(0, 0.1, 0.26), (0.0, 0.25, 0.22), (0.04, 0.4, 0.18), (0.04, 0.55, 0.13), (-0.02, 0.67, 0.1), (-0.1, 0.74, 0.13)],
           [0.03, 0.026, 0.022, 0.018, 0.014, 0.011], pink)
    c.follow['ear'] = 1.3
    c.follow['tail'] = 1.2

    def extra(a, clip, f, t, i, names):
        if clip == 'Attack':  # nibble: the head dips forward to snap at the foe
            dip = window(t, 0.2, 0.38, 0.44, 0.66)
            a.r('head', f, (a.P.hr[0] + 30 * dip, a.P.hr[1], a.P.hr[2]))
    return c.finish('biped', extra)


def scrap_bot(eid):
    """고철 로봇 — a round rusty scrap robot: one big glowing lamp eye, two antennae with bulb tips, rivets,
    and a wrench in one hand. Stubby legs, chunky wheel feet."""
    c = Sculpt(eid, tris=6500)
    steel, steel_d, rust, rivet, lamp = '#aab6c2', '#6e7b88', '#c17a45', '#e6eef4', '#8ff0ff'
    c.bone('body', (0, 0, 0.34)); c.bone('head', (0, -0.02, 0.68), 'body'); c.bone('eyes', (0, -0.2, 0.7), 'head')
    c.bone('antenna.L', (0.07, 0.0, 0.8), 'head'); c.bone('antenna.R', (-0.07, 0.0, 0.8), 'head')
    c.bone('arm.L', (0.19, -0.02, 0.36), 'body'); c.bone('arm.R', (-0.19, -0.02, 0.36), 'body')
    c.bone('leg.L', (0.1, 0, 0.12), 'body'); c.bone('leg.R', (-0.1, 0, 0.12), 'body')
    c.bone('weapon.R', (-0.27, -0.06, 0.26), 'arm.R')
    lower = lambda p: rust if p.z < 0.3 else steel  # noqa: E731
    c.blob('body', (0, 0, 0.34), (0.21, 0.19, 0.2), lower)
    c.blob('body', (0, -0.12, 0.34), (0.1, 0.05, 0.1), steel_d)  # chest panel
    c.blob('head', (0, -0.02, 0.68), (0.19, 0.17, 0.16), steel)
    c.blob('head', (0, -0.1, 0.62), (0.11, 0.05, 0.07), rust, weight=0.9)  # rust patch
    for s in (-1, 1):
        c.orb('head', f'rivet{s}', (s * 0.16, -0.1, 0.72), (0.02, 0.02, 0.02), rivet)
        c.orb('body', f'rivet_b{s}', (s * 0.17, -0.12, 0.3), (0.02, 0.02, 0.02), rivet)
    # one big lamp eye in a bezel
    c.orb('eyes', 'lamp_lens', (0, -0.2, 0.7), (0.08, 0.04, 0.08), lamp, 'M_Emit')
    c.ring('eyes', 'lamp_bezel', (0, -0.19, 0.7), 0.088, 0.018, steel_d, rot=(90, 0, 0))
    c.orb('eyes', 'lamp_glint', (0.02, -0.225, 0.72), (0.02, 0.01, 0.02), '#ffffff', 'M_Emit')
    for s, side in ((1, 'L'), (-1, 'R')):
        c.limb('antenna.' + side, [(s * 0.07, 0, 0.8), (s * 0.1, 0, 0.9), (s * 0.11, 0, 0.95)], [0.02, 0.018, 0.018], steel_d)
        c.orb('antenna.' + side, 'antenna_tip' + side, (s * 0.11, 0, 0.97), (0.03, 0.03, 0.03), '#ff6f6f', 'M_Emit')
        c.limb('arm.' + side, [(s * 0.19, -0.02, 0.36), (s * 0.25, -0.04, 0.3), (s * 0.27, -0.06, 0.26)],
               [0.04, 0.035, 0.035], steel_d)
        c.blob('arm.' + side, (s * 0.28, -0.07, 0.25), (0.05, 0.05, 0.045), rust)
        c.limb('leg.' + side, [(s * 0.1, 0, 0.12), (s * 0.1, 0, 0.05)], [0.06, 0.06], steel_d)
        c.blob('leg.' + side, (s * 0.1, -0.04, 0.04), (0.08, 0.1, 0.04), rust)
    # wrench in the right hand
    c.tube('weapon.R', 'wrench_handle', [(-0.27, -0.06, 0.26), (-0.31, -0.08, 0.5)], 0.024, steel)
    c.box('weapon.R', 'wrench_head', (-0.32, -0.09, 0.56), (0.12, 0.05, 0.1), steel, bevel=0.012)
    c.box('weapon.R', 'wrench_jaw', (-0.36, -0.09, 0.56), (0.03, 0.05, 0.05), steel_d, bevel=0.008)
    c.follow['antenna'] = 1.4
    return c.finish('heavy')


def cave_mole(eid):
    """굴착 두더지 — a plump mole with huge digging claws, a pink nose and brass goggles on its head."""
    c = Sculpt(eid, tris=6500)
    fur, fur_d, belly, pink, ivory, brass = '#8a6a58', '#6a4e40', '#c0a08a', '#f08aa8', '#f4ecd8', '#d1a443'
    c.bone('body', (0, 0, 0.3)); c.bone('head', (0, -0.04, 0.56), 'body'); c.bone('eyes', (0, -0.18, 0.6), 'head')
    c.bone('ear.L', (0.12, 0.0, 0.7), 'head'); c.bone('ear.R', (-0.12, 0.0, 0.7), 'head')
    c.bone('arm.L', (0.2, -0.02, 0.36), 'body'); c.bone('arm.R', (-0.2, -0.02, 0.36), 'body')
    c.bone('leg.L', (0.1, 0, 0.14), 'body'); c.bone('leg.R', (-0.1, 0, 0.14), 'body')
    c.blob('body', (0, 0, 0.3), (0.22, 0.2, 0.2), fur)
    c.blob('body', (0, -0.1, 0.28), (0.14, 0.09, 0.13), belly, weight=1.2)
    c.blob('head', (0, -0.04, 0.56), (0.17, 0.15, 0.15), fur)
    c.blob('head', (0, -0.17, 0.5), (0.07, 0.07, 0.06), belly, weight=1.2)  # snout
    c.blob('head', (0, -0.23, 0.5), (0.035, 0.03, 0.03), pink)  # nose
    for s, side in ((1, 'L'), (-1, 'R')):
        c.blob('ear.' + side, (s * 0.12, 0, 0.7), (0.03, 0.02, 0.03), fur)
        c.limb('arm.' + side, [(s * 0.2, -0.02, 0.36), (s * 0.28, -0.08, 0.28), (s * 0.31, -0.12, 0.22)],
               [0.05, 0.045, 0.04], fur)
        c.blob('arm.' + side, (s * 0.32, -0.14, 0.2), (0.06, 0.06, 0.05), belly)
        for j in range(3):  # three ivory digging claws
            x = s * (0.3 + j * 0.02)
            c.spike('arm.' + side, f'claw{side}{j}', (x, -0.17 - j * 0.005, 0.18), (x + s * 0.01, -0.2, 0.09),
                    0.014, ivory)
        c.limb('leg.' + side, [(s * 0.1, 0, 0.14), (s * 0.1, -0.02, 0.04)], [0.06, 0.055], fur)
        c.blob('leg.' + side, (s * 0.1, -0.06, 0.035), (0.07, 0.09, 0.035), belly)
    for s in (-1, 1):
        c.eye('eyes', (s * 0.08, -0.175, 0.6), (s * 0.2, -1, 0.05), 0.045, '#2a1a18', sclera='#ffffff')
        c.ring('eyes', f'goggle{s}', (s * 0.07, -0.2, 0.6), 0.05, 0.015, brass, rot=(90, 0, 0))
    c.ring('head', 'goggle_strap', (0, -0.03, 0.66), 0.165, 0.01, '#7a4a2a', rot=(0, 0, 0))
    c.follow['ear'] = 1.2
    return c.finish('biped')


def mummy_pup(eid):
    """붕대 미라 — a chibi mummy puppy: a big round bandaged head (about 55 % of its height) with floppy dog ears,
    two big shiny eyes peeking between diagonal wraps, a small pink nose, a short stubby body and paws, and a loose
    bandage tail trailing behind. It pounces with a headbutt."""
    c = Sculpt(eid, tris=6500)
    cloth, cloth_hi, cloth_d, wrap, nose = '#f6ead0', '#fbf3e2', '#e2cfa6', '#c9ab72', '#e88ca0'
    c.bone('body', (0, 0, 0.14)); c.bone('head', (0, -0.02, 0.45), 'body'); c.bone('eyes', (0, -0.17, 0.46), 'head')
    c.bone('ear.L', (0.17, 0.0, 0.53), 'head'); c.bone('ear.R', (-0.17, 0.0, 0.53), 'head')
    c.bone('arm.L', (0.1, -0.03, 0.16), 'body'); c.bone('arm.R', (-0.1, -0.03, 0.16), 'body')
    c.bone('leg.L', (0.06, 0, 0.07), 'body'); c.bone('leg.R', (-0.06, 0, 0.07), 'body')
    c.bone('tail1', (0, 0.1, 0.16), 'body'); c.bone('tail2', (0, 0.26, 0.1), 'tail1')
    # body: short and round, warm cream with a shaded underside
    c.blob('body', (0, 0, 0.14), (0.13, 0.115, 0.11), _skin_tone(cloth_d, cloth, 0.0, 0.26))
    c.blob('body', (0, -0.06, 0.13), (0.09, 0.06, 0.08), cloth_hi, weight=1.2)
    for k, z in enumerate((0.1, 0.17)):
        c.ring('body', f'wrap_b{k}', (0, 0, z), 0.13, 0.016, wrap, scale=(1, 0.9, 1))
    # big round head: warm cream with a shaded lower face
    c.blob('head', (0, -0.02, 0.45), (0.2, 0.19, 0.19), lambda p: lerp_col(cloth_d, cloth, (p.z - 0.27) / 0.36))
    c.blob('head', (0, -0.16, 0.4), (0.075, 0.06, 0.055), cloth_hi, weight=1.2)  # muzzle
    c.orb('head', 'nose', (0, -0.205, 0.43), (0.032, 0.025, 0.026), nose)
    c.blob('head', (0.03, -0.08, 0.63), (0.07, 0.05, 0.04), cloth_d, weight=0.8)  # loose bandage tuft on top
    # diagonal wrap lines across the head; the eyes sit in the gaps between them
    for k, (z, r) in enumerate(((0.37, 0.165), (0.53, 0.17))):  # radii sized to the head surface at each height
        c.ring('head', f'wrap_h{k}', (0, -0.02, z), r, 0.015, wrap, rot=(0, 14, 0), scale=(1, 0.95, 1))
    for s_ in (-1, 1):
        c.eye('eyes', (s_ * 0.075, -0.17, 0.46), (s_ * 0.25, -1, 0.1), 0.05, '#3a2418', sclera='#ffffff')
    # floppy dog ears hanging down beside the head
    for s_, side in ((1, 'L'), (-1, 'R')):
        c.tuft('ear.' + side, (s_ * 0.17, 0.0, 0.53), (s_ * 0.4, 0.05, -1), 0.2, 0.05, cloth_d)
    # stubby arms and paws
    for s_, side in ((1, 'L'), (-1, 'R')):
        c.limb('arm.' + side, [(s_ * 0.1, -0.03, 0.16), (s_ * 0.13, -0.07, 0.1)], [0.04, 0.036], cloth)
        c.blob('arm.' + side, (s_ * 0.14, -0.09, 0.07), (0.05, 0.05, 0.04), cloth_hi)
        c.limb('leg.' + side, [(s_ * 0.06, 0, 0.07), (s_ * 0.07, -0.02, 0.02)], [0.05, 0.05], cloth_d)
        c.blob('leg.' + side, (s_ * 0.07, -0.06, 0.03), (0.065, 0.08, 0.035), cloth)
    # loose bandage tail trailing behind and dragging on the floor
    c.limb(['tail1', 'tail1', 'tail2', 'tail2'],
           [(0, 0.1, 0.16), (0.01, 0.2, 0.13), (0.03, 0.32, 0.07), (0.04, 0.4, 0.03), (0.02, 0.46, 0.02)],
           [0.04, 0.036, 0.03, 0.026, 0.02], cloth)
    c.follow['tail'] = 1.3
    c.follow['ear'] = 1.2

    def extra(a, clip, f, t, i, names):
        if clip == 'Attack':  # pounce: dive forward, headbutt on the strike
            dive = window(t, 0.2, 0.38, 0.44, 0.66)
            a.r('body', f, (a.P.br[0] + 8 * dive, a.P.br[1], a.P.br[2]))
            a.r('head', f, (a.P.hr[0] + 34 * dive, a.P.hr[1], a.P.hr[2]))
    return c.finish('biped', extra)


def orc(eid, elite=False):
    """오크 전사 — a chibi green orc: round belly, two small tusks, a horned steel helmet and a big axe.
    The elite (하이 오크) adds a red cape, shoulder plates, scars and a two-handed cleaver."""
    c = Sculpt(eid, tris=10000 if elite else 7500)
    skin, skin_d, belly, tusk, horn, steel, wood = '#7dbb5c', '#4f8f3f', '#b8dc86', '#fff4dc', '#e8d8b6', '#8a8f9a', '#8a5a34'
    if elite:
        steel, horn, skin = '#5f6876', '#d9c8a0', '#6fb04f'
    tone = _skin_tone(skin_d, skin, 0.1, 1.0)
    c.bone('body', (0, 0, 0.42)); c.bone('head', (0, -0.04, 0.9), 'body'); c.bone('eyes', (0, -0.22, 0.92), 'head')
    c.bone('jaw', (0, -0.2, 0.8), 'head')
    c.bone('arm.L', (0.26, -0.02, 0.5), 'body'); c.bone('arm.R', (-0.26, -0.02, 0.5), 'body')
    c.bone('leg.L', (0.12, 0, 0.2), 'body'); c.bone('leg.R', (-0.12, 0, 0.2), 'body')
    c.bone('weapon.R', (-0.36, -0.1, 0.3), 'arm.R')
    c.blob('body', (0, 0, 0.42), (0.26, 0.22, 0.26), tone)
    c.blob('body', (0, -0.12, 0.4), (0.17, 0.11, 0.17), belly, weight=1.2)  # round belly
    c.blob('head', (0, -0.04, 0.9), (0.24, 0.2, 0.2), tone)
    c.blob('head', (0, -0.2, 0.84), (0.13, 0.07, 0.07), belly, weight=1.2)  # cheeks
    c.blob('head', (0, -0.23, 0.86), (0.05, 0.03, 0.03), skin_d)  # snout
    # helmet with two curved horns
    c.blob('head', (0, -0.02, 1.03), (0.2, 0.18, 0.09), steel)
    c.ring('head', 'helmet_rim', (0, -0.04, 0.99), 0.2, 0.018, steel, rot=(0, 0, 0), scale=(1, 0.9, 1))
    for s in (-1, 1):
        c.cone_to('head', f'horn{s}', (s * 0.17, -0.02, 1.0), (s * 0.27, -0.02, 1.13), 0.058, horn, r2=0.02)
    # eyes and tusks
    for s in (-1, 1):
        c.eye('eyes', (s * 0.1, -0.21, 0.92), (s * 0.2, -1, 0.05), 0.06, '#c8a02a', sclera='#ffffff')
        c.spike('jaw', f'tusk{s}', (s * 0.07, -0.22, 0.8), (s * 0.085, -0.27, 0.85), 0.02, tusk)
    if elite:
        for s in (-1, 1):
            c.paint((s * 0.2, -0.17, 0.98), (0.012, 0.03, 0.08), '#c9584a', rot=(0, 0, 25 * s))  # scar
            c.orb('body', f'pauldron{s}', (s * 0.27, -0.02, 0.6), (0.11, 0.1, 0.07), steel)
        c.membrane('body', 'cape', (0, 0.12, 0.55), [(-0.24, 0.06, 0.7), (-0.3, 0.22, 0.25), (0, 0.28, 0.2),
                                                    (0.3, 0.22, 0.25), (0.24, 0.06, 0.7)], '#b8323a', thick=0.012,
                   edge_color='#7a1a24')
    else:
        c.paint((0.13, -0.19, 0.99), (0.012, 0.03, 0.05), '#c9584a', rot=(0, 0, 0))
    # arms and legs (chunky)
    for s, side in ((1, 'L'), (-1, 'R')):
        c.limb('arm.' + side, [(s * 0.26, -0.02, 0.5), (s * 0.33, -0.05, 0.38), (s * 0.36, -0.1, 0.3)],
               [0.07, 0.06, 0.055], skin)
        c.blob('arm.' + side, (s * 0.37, -0.12, 0.27), (0.07, 0.07, 0.065), skin_d)
        c.limb('leg.' + side, [(s * 0.12, 0, 0.2), (s * 0.13, -0.02, 0.06)], [0.1, 0.09], skin_d)
        c.blob('leg.' + side, (s * 0.13, -0.08, 0.05), (0.1, 0.13, 0.05), '#4a3a2a')
    # big axe (two-handed look for the elite: a wide cleaver)
    c.tube('weapon.R', 'axe_handle', [(-0.36, -0.1, 0.3), (-0.42, -0.14, 0.95)], 0.026, wood)
    if elite:
        c.box('weapon.R', 'cleaver', (-0.44, -0.16, 1.02), (0.14, 0.05, 0.36), '#c9d4de', bevel=0.012)
        c.box('weapon.R', 'cleaver_edge', (-0.44, -0.16, 1.02), (0.15, 0.052, 0.04), '#e4ecf3', bevel=0.006)
        c.ring('weapon.R', 'cleaver_band', (-0.42, -0.14, 0.9), 0.034, 0.012, steel, rot=(0, 0, 0))
    else:
        c.shape('weapon.R', 'axe_blade', [(-0.02, 0.0), (-0.2, 0.06), (-0.24, 0.2), (-0.2, 0.34), (-0.03, 0.38)],
                (-0.42, -0.14, 0.82), '#c9d4de', depth=0.03)
        c.gem('weapon.R', 'axe_gem', (-0.42, -0.15, 0.9), (0, -1, 0), 0.02, 0.03, '#ffe36a', '#c09030', mat='M_Toon')
    c.follow['ear'] = 1.0

    def extra(a, clip, f, t, i, names):
        if clip == 'Attack':  # two-handed overhead chop: both arms rise over the head, lean back, then chop
            up = window(t, 0.02, 0.3, 0.36, 0.41)
            imp = math.exp(-(t - 0.4) * 14) if t >= 0.4 else 0.0
            for s_, side in ((1, 'L'), (-1, 'R')):
                ax, abd, tw = a.P.arm[side]
                a.r('arm.' + side, f, (ax + 100 * up, -s_ * abd, s_ * tw))
            a.r('body', f, (a.P.br[0] - 8 * up, a.P.br[1], a.P.br[2]))
            a.s('body', f, (1 + 0.06 * imp, 1 + 0.06 * imp, 1 - 0.1 * imp))
    return c.finish('heavy', extra)


def high_orc(eid):
    return orc(eid, elite=True)


BUILDERS = {'goblin': goblin, 'goblin_shaman': goblin_shaman, 'sewer_rat': sewer_rat, 'scrap_bot': scrap_bot,
            'cave_mole': cave_mole, 'mummy_pup': mummy_pup, 'orc': orc, 'high_orc': high_orc}

if __name__ == '__main__':
    eid = sys.argv[sys.argv.index('--') + 1]
    BUILDERS[eid](eid)
