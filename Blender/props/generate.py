"""Generate all data-ID items (30 original + 36 campaign expansion) and six interactive common props.
Real meshes, vertex colours, shared pipeline; no equipment ownership here.
Run with Blender -b --factory-startup -P Blender/props/generate.py [-- <item id> ...] (ids: only those items, no common props).
"""
import os
import sys
import math
import json
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'town'))
from _common import MB, T, RX, RY, RZ, S, A
import bpy

GOLD = '#e9bb61'
WOOD = '#845239'
DARK = '#333044'
IVORY = '#f5e6bd'


def crystal(m, color, radius=.24, height=.7, loc=(0, 0, 0), tilt=0):
    with m.at(T(*loc) @ RY(tilt)):
        m.lathe([(0, 0), (radius, .16), (radius*.85, height*.7), (0, height)], col=color, seg=6, smooth=False)
        m.lathe([(radius*.86, .19), (radius*.88, .26)], col=GOLD, seg=6, smooth=False)


def leaf(m, x, y, z, length, color, angle=0):
    with m.at(T(x, y, z) @ RZ(angle)):
        m.slab([(0, 0), (-length*.2, length*.35), (-length*.14, length*.78), (0, length), (length*.18, length*.7), (length*.22, length*.35)], .04, color, y=-.02)
        m.tube([(0, -.05, 0), (0, -.05, length*.8)], .012, GOLD, seg=5)


def bottle(m, color, tier, form='potion'):
    r = .2 + tier*.035
    profiles = {
        'potion': [(0, .04), (r*.8, .04), (r, .15), (r, .37+tier*.05), (.12, .53+tier*.06), (.115, .68+tier*.06)],
        'ether': [(0, .03), (r*.75, .03), (r, .22), (.17, .43+tier*.08), (.10, .53+tier*.08), (.1, .69+tier*.08)],
        'tonic': [(0, .03), (r, .03), (r, .38), (.12, .47), (.12, .65)],
    }
    m.lathe(profiles[form], col=color, seg=12)
    top = profiles[form][-1][1]
    m.cyl(.13, .065, (0, 0, top-.025), GOLD, seg=12)
    m.cyl(.095, .10, (0, 0, top+.04), WOOD, seg=10)
    m.cyl(r*1.015, .085, (0, 0, .14), GOLD, seg=12)
    m.box((.20, .04, .21), (0, -r, .32), IVORY)
    for n in range(tier+1):
        m.sphere(.029, ((n-tier*.5)*.075, -r-.038, .32), GOLD, seg=8, rings=5)
    if form == 'tonic':
        m.torus(.11, .02, (0, 0, top+.05), GOLD, m=RX(90), seg=12, minor=5)


def bomb(m, big=False, smoke=False):
    r = .32 if big else .24
    m.sphere(r, (0, 0, r+.04), '#6a6682' if smoke else '#303243', seg=16, rings=10)
    m.cyl(.095, .1, (0, 0, 2*r+.03), GOLD)
    m.tube([(0, 0, 2*r+.08), (.02, 0, 2*r+.22), (.12, 0, 2*r+.26)], .025, WOOD)
    m.ico(.05, (.13, 0, 2*r+.27), '#ffbd58', mat='M_Emit')
    m.torus(r, .025, (0, 0, r+.04), GOLD, m=RX(90), seg=16, minor=5)
    if big:
        m.box((.3, .055, .12), (0, -r, r+.05), '#d05346')
        m.box((.1, .055, .3), (0, -r-.004, r+.05), '#d05346')
    if smoke:
        for i in range(3):
            m.torus(.055, .016, ((i-1)*.12, -r, r+.02), '#dbe1ef', m=RX(90), seg=12, minor=5)


def key(m, color=GOLD, loc=(0, 0, 0)):
    with m.at(T(*loc)):
        m.torus(.12, .035, (0, 0, .6), color, m=RX(90), seg=16, minor=6)
        m.box((.06, .075, .4), (0, 0, .30), color)
        m.box((.18, .075, .065), (.06, 0, .15), color)
        m.box((.07, .075, .14), (.12, 0, .2), color)


def coin(m, loc, size=.1, rz=0):
    with m.at(T(*loc) @ RZ(rz)):
        m.cyl(size, .035, col=GOLD, seg=12)
        m.torus(size*.72, .008, (0, 0, .023), '#fff1a7', seg=12, minor=4)


def campfire(m):
    for i in range(9):
        a = i*math.tau/9
        m.ico(.16, (.46*math.cos(a), .46*math.sin(a), .09), '#81828c', scale=(1, 1, .7), smooth=False)
    for a in (-35, 35):
        m.cyl(.08, .75, (0, 0, .12), WOOD, rr=(0, 90, a), seg=8)
    for i in range(5):
        a=i*2.4
        m.lathe([(0, 0), (.15, .09), (.11, .28), (.04, .45), (0, .62)], loc=(.13*math.cos(a), .12*math.sin(a), .18), col='#f39036', mat='M_Emit', seg=7, smooth=False, m=RY((i-2)*12))
    m.cone(.11, .36, loc=(0, 0, .44), col='#ffdd72', mat='M_Emit', seg=7)


def chest(rare):
    m=MB()
    c='#386b9a' if rare else WOOD
    m.box((.95, .64, .43), (0, 0, .27), c)
    for x in (-.42, .42):
        m.box((.07, .69, .48), (x, 0, .27), GOLD)
        m.box((.12, .12, .09), (x, -.25, .045), DARK)
        m.box((.12, .12, .09), (x, .25, .045), DARK)
    m.box((.14, .065, .16), (0, -.35, .42), GOLD)
    m.box((.035, .035, .065), (0, -.39, .42), DARK)
    body=m.build('Chest')
    lid=MB()
    lid.lathe([(.0, -.48), (.31, -.48), (.36, -.3), (.31, -.12), (0, -.12)], col=c, seg=12, m=T(0, 0, .52) @ RY(90), scale=(1, 1, 1.0))
    # Vaulted top with visible ribs; its origin is the rear hinge, not mesh centre.
    lid.box((.98, .68, .09), (0, 0, .52), c)
    for x in (-.42, .42):
        lid.tube([(x, -.32, .53), (x, -.23, .72), (x, 0, .81), (x, .23, .72), (x, .32, .53)], .038, GOLD)
    if rare:
        lid.ico(.09, (0, -.20, .73), '#82edee', mat='M_Emit', scale=(1, .5, 1))
    top=lid.build('Lid', origin=(0, .32, .52))
    return [body, top]


def seed(m, color, accent):
    """Teardrop seed with a sprout and a glowing rune band (permanent stat seeds)."""
    m.lathe([(0, .04), (.17, .1), (.22, .25), (.16, .42), (.05, .55), (0, .58)], col=color, seg=14)
    m.torus(.2, .018, (0, 0, .25), accent, mat='M_Emit', seg=16, minor=5)
    m.tube([(0, 0, .55), (.02, 0, .68), (.08, 0, .74)], .02, '#6fae4c')
    leaf(m, .06, 0, .7, .2, '#8fd06a', -60)


def element_bomb(m, body, glow, mark):
    r = .26
    m.sphere(r, (0, 0, r+.04), body, seg=16, rings=10)
    m.cyl(.095, .1, (0, 0, 2*r+.03), GOLD)
    m.tube([(0, 0, 2*r+.08), (.02, 0, 2*r+.22), (.12, 0, 2*r+.26)], .025, WOOD)
    m.ico(.05, (.13, 0, 2*r+.27), glow, mat='M_Emit')
    m.torus(r, .025, (0, 0, r+.04), GOLD, m=RX(90), seg=16, minor=5)
    if mark == 'fire':
        m.slab([(-.08, .22), (0, .44), (.08, .22), (.03, .27), (0, .17), (-.03, .27)], .03, glow, y=-r-.01)
    elif mark == 'ice':
        for a in (0, 60, 120):
            with m.at(T(0, -r-.01, .3) @ RY(a)):
                m.box((.03, .03, .2), (0, 0, 0), glow, mat='M_Emit')
    else:
        m.slab([(-.03, .44), (.07, .44), (.0, .33), (.06, .33), (-.06, .16), (-.01, .3), (-.07, .3)], .03, glow, y=-r-.01)


def ore(m, color, glow, size=1.0):
    m.ico(.26*size, (0, 0, .24*size), '#6f6a7a', sub=1, scale=(1, .8, .9), smooth=False, jitter=.12, seed=3)
    for i in range(4):
        a = i*math.tau/4 + .3
        crystal(m, color, .08*size, .34*size, (.13*size*math.cos(a), .1*size*math.sin(a), .16*size), (i-1.5)*18)
    m.ico(.06*size, (0, -.2*size, .3*size), glow, mat='M_Emit', sub=1)


def expansion_item(m, item_id):
    """The 36 campaign-expansion items (Tools/content/spec.py NEW_ITEMS). Returns False for other ids."""
    bottles = {
        'x_potion': ('#ff5f9a', 3, 'potion'), 'max_ether': ('#5f6cff', 3, 'ether'), 'megalixir': ('#ffd84a', 3, 'ether'),
        'panacea': ('#9be3c4', 2, 'tonic'), 'magic_tonic': ('#9b6ae0', 1, 'tonic'), 'speed_tonic': ('#5ad0e8', 1, 'tonic'),
        'holy_water': ('#cfe9ff', 1, 'potion')}
    seeds = {'seed_power': ('#d8664a', '#ffb070'), 'seed_magic': ('#8a5ad8', '#d8a8ff'), 'seed_guard': ('#7a8aa0', '#d0e0f0'),
             'seed_mind': ('#4a8ad0', '#a8e0ff'), 'seed_swift': ('#5ab878', '#b8ffd0'), 'seed_life': ('#e86a8a', '#ffc0d0')}
    if item_id in bottles:
        bottle(m, *bottles[item_id])
        if item_id == 'megalixir':
            m.torus(.3, .02, (0, 0, .5), '#fff4b0', mat='M_Emit', seg=20, m=RY(20))
        if item_id == 'holy_water':
            m.box((.03, .03, .16), (0, -.275, .32), GOLD)
            m.box((.11, .03, .03), (0, -.275, .35), GOLD)
        if item_id == 'magic_tonic':
            m.ico(.05, (0, -.29, .33), '#e8c8ff', mat='M_Emit')
        if item_id == 'speed_tonic':
            m.slab([(-.07, .27), (.07, .37), (-.02, .37), (.06, .45), (-.07, .35), (.0, .35)], .02, '#e0fbff', y=-.29)
    elif item_id in ('fire_bomb', 'ice_bomb', 'thunder_bomb'):
        element_bomb(m, *{'fire_bomb': ('#b8352a', '#ffb050', 'fire'), 'ice_bomb': ('#3a78b8', '#c8f4ff', 'ice'),
                          'thunder_bomb': ('#a88a20', '#fff070', 'thunder')}[item_id])
    elif item_id == 'phoenix_plume':
        leaf(m, -.06, 0, .05, .85, '#ff6a3a', -12)
        leaf(m, .06, .02, .05, .7, '#ffb03a', 18)
        for i in range(5):
            z = .18+i*.12
            m.tube([(.0, -.05, z), (.18, -.04, z+.1)], .016, '#fff09a', mat='M_Emit')
    elif item_id == 'camp_tent':
        m.prism([(-.42, -.3), (.42, -.3), (.42, .3), (-.42, .3)], 0, .03, '#6a5a44')
        m.raw([(-.38, -.3, .03), (.38, -.3, .03), (0, -.3, .55), (-.38, .3, .03), (.38, .3, .03), (0, .3, .55)],
              [(0, 1, 2), (3, 5, 4), (0, 2, 5, 3), (1, 4, 5, 2)], "#c8884a", recalc=True)
        m.slab([(-.14, .03), (.14, .03), (0, .3)], .02, '#3a2a20', y=-.31)
        m.cyl(.015, .65, (0, -.33, .32), WOOD, seg=6)
        m.slab([(0, .62), (.16, .56), (0, .5)], .01, '#d84a3a', y=-.33)
    elif item_id in seeds:
        seed(m, *seeds[item_id])
    elif item_id == 'job_medal':
        m.cyl(.26, .05, (0, 0, .34), GOLD, seg=20, rr=(90, 0, 0))
        m.cyl(.19, .06, (0, 0, .34), '#c84a4a', seg=20, rr=(90, 0, 0))
        m.slab([(-.12, .64), (.12, .64), (.16, .9), (-.16, .9)], .03, '#3a5ab8', y=0)
        m.slab([(-.05, .34), (0, .47), (.05, .34), (0, .21)], .02, '#fff0a0', y=-.045)
        m.torus(.05, .015, (0, 0, .62), GOLD, m=RX(90), seg=12, minor=5)
    elif item_id == 'master_seal':
        m.cyl(.3, .12, (0, 0, .06), '#7a1a2a', seg=24)
        m.cyl(.22, .14, (0, 0, .07), GOLD, seg=24)
        m.lathe([(.08, .14), (.1, .3), (.07, .5), (.11, .62), (0, .66)], col='#2a2030', seg=12)
        for i in range(8):
            a = i*math.tau/8
            m.box((.03, .03, .03), (.25*math.cos(a), .25*math.sin(a), .13), GOLD)
        m.ico(.06, (0, 0, .66), '#ff5a7a', mat='M_Emit')
    elif item_id in ('enhance_stone', 'enhance_stone_hi', 'enhance_stone_abyss'):
        ore(m, *{'enhance_stone': ('#9ab4c8', '#e8f6ff', .9), 'enhance_stone_hi': ('#e8b04a', '#fff0b0', 1.0),
                 'enhance_stone_abyss': ('#8a4ae0', '#e0b8ff', 1.1)}[item_id])
    elif item_id == 'pearl':
        m.lathe([(0, .02), (.3, .06), (.36, .12), (.3, .16), (0, .14)], col='#e8b8a8', seg=16)
        m.sphere(.17, (0, -.02, .28), '#f6f2ff', mat='M_Emit', seg=16, rings=10)
    elif item_id == 'scale_blue':
        m.slab([(-.22, .54), (0, .76), (.22, .54), (.19, .24), (0, .05), (-.19, .24)], .08, '#2f7fae', y=-.04)
        m.slab([(-.14, .49), (0, .67), (.14, .49), (.12, .27), (0, .14), (-.12, .27)], .03, '#7fe0f0', y=-.07)
    elif item_id == 'temple_stone':
        m.box((.5, .3, .4), (0, 0, .2), '#b8b098')
        m.box((.3, .04, .2), (0, -.16, .24), '#4fb8b0', mat='M_Emit')
        m.ico(.08, (.2, -.1, .42), '#7aa860', sub=1, scale=(1, 1, .5))
    elif item_id == 'siren_feather':
        leaf(m, 0, 0, .05, .8, '#7ad0e0', -15)
        m.tube([(0, -.05, .1), (.06, -.05, .5), (.18, -.05, .8)], .012, '#f0faff', mat='M_Emit')
    elif item_id == 'leviathan_fin':
        m.slab([(-.3, .05), (.3, .05), (.25, .3), (0, .85), (-.12, .45)], .06, '#1e5a78', y=-.03)
        for x in (-.15, 0, .15):
            m.tube([(x, -.07, .08), (x*.4, -.07, .6)], .015, '#7ff0e0', mat='M_Emit')
    elif item_id == 'void_shard':
        crystal(m, '#3a1f5a', .2, .8)
        crystal(m, '#a45cff', .08, .4, (.18, 0, .02), 25)
        m.torus(.26, .015, (0, 0, .35), '#c89aff', mat='M_Emit', seg=16, m=RY(-20))
    elif item_id == 'shadow_pelt':
        m.slab([(-.3, .12), (-.34, .4), (-.24, .62), (-.08, .5), (0, .6), (.1, .5), (.3, .62), (.35, .32), (.26, .08), (0, .16)], .12, '#2e2838', y=-.06)
        for i in range(5):
            m.tube([((i-2)*.1, -.08, .22), ((i-2)*.09, -.08, .42)], .012, '#a45cff', mat='M_Emit')
    elif item_id == 'gargoyle_horn':
        m.tube([(0, 0, .05), (.08, 0, .3), (.02, 0, .55), (-.14, 0, .72)], .1, '#7a7480', r_end=.015)
        m.torus(.1, .02, (.02, 0, .12), GOLD, seg=14)
    elif item_id == 'fallen_feather':
        leaf(m, 0, 0, .05, .85, '#2a2236', -10)
        m.torus(.12, .012, (.05, -.06, .8), '#d8c890', m=RX(90), seg=16, minor=4)
    elif item_id == 'lord_crown':
        m.lathe([(.26, .05), (.28, .12), (.27, .22), (.26, .25)], col='#2a1f3a', seg=20)
        for i in range(6):
            a = i*math.tau/6
            m.cone(.05, .28 if i % 2 == 0 else .2, (.25*math.cos(a), .25*math.sin(a), .36), '#3a2a50', seg=6)
        m.torus(.27, .025, (0, 0, .13), GOLD, seg=20)
        m.ico(.06, (0, -.27, .17), '#a45cff', mat='M_Emit')
    elif item_id == 'trial_emblem':
        m.cyl(.28, .06, (0, 0, .34), '#e8e2d0', seg=8, rr=(90, 0, 0))
        m.cyl(.2, .07, (0, 0, .34), GOLD, seg=8, rr=(90, 0, 0))
        m.slab([(-.06, .34), (0, .52), (.06, .34), (0, .16)], .02, '#ff8a3a', y=-.05)
        m.slab([(-.15, .3), (.15, .3), (.15, .38), (-.15, .38)], .015, '#ff8a3a', y=-.045)
    elif item_id == 'metal_gel':
        m.sphere(.25, (0, 0, .18), '#c8d0e0', seg=16, rings=8, scale=(1.2, 1, .65))
        for loc in [(-.15, -.1, .2), (.14, .06, .28), (.02, -.12, .33)]:
            m.sphere(.10, loc, '#eef2fa', seg=10, rings=6)
    else:
        return False
    return True


def item_mesh(item_id):
    m=MB()
    bottles={
        'healing_potion':('#d65666', 0, 'potion'), 'hi_potion':('#ed6388', 1, 'potion'),
        'mega_potion':('#ff856e', 2, 'potion'), 'ether':('#54a7d5', 0, 'ether'),
        'hi_ether':('#7c84e7', 1, 'ether'), 'elixir':('#e6b641', 2, 'ether'),
        'guard_tonic':('#4b9ba6', 0, 'tonic'), 'power_tonic':('#d97540', 1, 'tonic'),
        'remedy':('#71b678', 1, 'tonic')}
    if item_id in bottles:
        bottle(m, *bottles[item_id])
        if item_id == 'guard_tonic':
            m.slab([(-.075,.42),(.075,.42),(.07,.32),(0,.26),(-.07,.32)], .025, '#75e4f0', y=-.26)
        if item_id == 'power_tonic':
            m.slab([(-.06,.26),(.07,.40),(.015,.40),(.055,.5),(-.07,.36),(-.015,.36)], .02, '#fff0aa', y=-.29)
    elif item_id in ('bomb','big_bomb','smoke_bomb'):
        bomb(m, item_id=='big_bomb', item_id=='smoke_bomb')
    elif item_id in ('abyss_crystal','ember_crystal','frost_crystal','verdant_crystal'):
        colors={'abyss_crystal':'#8063d3','ember_crystal':'#ed6541','frost_crystal':'#63d6e4','verdant_crystal':'#64c486'}
        crystal(m, colors[item_id], .23, .8)
        for i in range(3):
            a=i*math.tau/3
            crystal(m, colors[item_id], .1, .38, (.25*math.cos(a), .25*math.sin(a), .02), i*17-17)
        if item_id=='abyss_crystal':
            m.torus(.31,.025,(0,0,.5),'#c096f6',mat='M_Emit',seg=18,m=RY(25))
        elif item_id=='ember_crystal':
            for i in range(3):
                m.cone(.04,.16,(.14*math.cos(i*2),-.22,.3+i*.1),'#ffc568',mat='M_Emit')
        elif item_id=='frost_crystal':
            m.torus(.29,.015,(0,0,.22),'#eefbff',seg=6)
        else:
            leaf(m, -.24, -.02, .1, .45, '#a0db7c', -35)
    elif item_id=='bat_wing':
        m.slab([(-.38,.65),(-.23,.80),(-.06,.64),(.02,.12),(-.13,.34),(-.23,.25),(-.32,.45),(-.45,.39)], .055, '#674873', y=-.03)
        for end in [(-.38,0,.65),(-.23,0,.25),(-.45,0,.39)]:
            m.tube([(.02,-.055,.12),end], .018, '#c88ca2')
    elif item_id=='coral_shard':
        for i in range(4):
            x=(i-1.5)*.11
            m.tube([(0,0,.06),(x,0,.25),(x*.8,.02,.45+i*.07)], .07, '#e7948c', r_end=.025)
            m.tube([(x,0,.25),(x+.12,.02,.37)], .035, '#edb2a0', r_end=.015)
        m.ico(.17,(0,0,.08),'#d26e86',scale=(1,1,.6))
    elif item_id=='cursed_straw':
        for i in range(13):
            a=i*2.4
            m.tube([(.13*math.cos(a),.08*math.sin(a),.06),(.035*math.cos(a),.03*math.sin(a),.3),(.17*math.cos(a),.1*math.sin(a),.6+i%3*.06)], .016, '#c0a266')
        m.torus(.075,.023,(0,0,.29),'#735579',seg=10)
        m.sphere(.045,(0,-.055,.34),'#a877dd',mat='M_Emit',seg=8,rings=5)
    elif item_id=='drake_scale':
        m.slab([(-.22,.54),(0,.76),(.22,.54),(.19,.24),(0,.05),(-.19,.24)], .09, '#a34345', y=-.045)
        m.slab([(-.14,.49),(0,.67),(.14,.49),(.12,.27),(0,.14),(-.12,.27)], .035, '#e87d4a', y=-.075)
        m.tube([(0,-.095,.15),(0,-.095,.63)], .023, GOLD)
    elif item_id=='forest_fiber':
        for i in range(4):
            m.torus(.21,.035,(0,0,.09+i*.08),'#7ba263',seg=16,minor=6)
        m.tube([(-.21,0,.1),(-.3,-.03,.35),(-.21,-.04,.6)], .027, '#476c49')
        leaf(m,-.21,-.04,.47,.25,'#8bc877',-45)
    elif item_id=='frost_fur':
        m.slab([(-.29,.12),(-.33,.37),(-.24,.61),(-.09,.5),(0,.59),(.11,.5),(.3,.61),(.34,.33),(.26,.08),(0,.16)], .13, '#bde1e7',y=-.06)
        for i in range(8):
            m.tube([((i-3.5)*.065,-.085,.2),((i-3.5)*.06,-.085,.4)], .012, '#f6fbeb')
    elif item_id=='ghost_essence':
        m.lathe([(0,.03),(.18,.08),(.23,.25),(.14,.44),(.09,.6),(0,.78)],col='#90d9d6',mat='M_Emit',seg=10)
        for x in (-.07,.07): m.ico(.035,(x,-.19,.32),DARK)
        m.torus(.25,.02,(0,0,.18),'#b5a8e9',seg=16)
    elif item_id=='golem_sandstone':
        m.ico(.32,(0,0,.29),'#ba9166',sub=1,scale=(1,.75,1),smooth=False,jitter=.15,seed=1)
        m.tube([(-.12,-.24,.15),(-.12,-.27,.36),(.1,-.26,.36),(.1,-.23,.49)], .024, '#7ac5aa',mat='M_Emit')
    elif item_id=='jelly_core':
        m.sphere(.26,(0,0,.32),'#80bad7',scale=(1,1,.8),seg=16,rings=10)
        m.ico(.12,(0,-.23,.34),'#ffe7bd',mat='M_Emit',sub=2)
        for i in range(4):
            a=i*math.tau/4
            m.tube([(.17*math.cos(a),.17*math.sin(a),.2),(.23*math.cos(a),.23*math.sin(a),.07)],.035,'#b0dded')
    elif item_id=='magma_core':
        m.ico(.3,(0,0,.31),DARK,sub=2,jitter=.15,seed=8,smooth=False)
        for i in range(5):
            a=i*math.tau/5
            m.tube([(.22*math.sin(a),-.2,.13),(.16*math.sin(a),-.26,.3),(.19*math.sin(a),-.18,.5)],.026,'#ff9a47',mat='M_Emit')
    elif item_id=='old_bone':
        m.cyl(.07,.45,(0,0,.36),IVORY,seg=10,rr=(0,20,0))
        for z in (.13,.6):
            for x in (-.055,.055): m.sphere(.095,(x+(z-.36)*.34,0,z),IVORY,seg=10,rings=6)
    elif item_id=='phoenix_feather':
        leaf(m,0,0,.05,.8,'#f28e46',-20)
        for i in range(4):
            z=.2+i*.12
            m.tube([(.04,-.05,z),(.17,-.04,z+.10)],.018,'#ffdc6f',mat='M_Emit')
    elif item_id=='return_stone':
        m.ico(.28,(0,0,.26),'#77959e',sub=2,scale=(1,.7,1),smooth=False)
        m.torus(.13,.023,(0,-.21,.29),'#a4eee5',mat='M_Emit',m=RX(90),seg=16)
        m.tube([(-.07,-.235,.29),(0,-.235,.36),(.07,-.235,.29)],.025,'#a4eee5',mat='M_Emit')
        m.box((.035,.025,.11),(0,-.235,.26),'#a4eee5',mat='M_Emit')
    elif item_id=='slime_gel':
        m.sphere(.25,(0,0,.18),'#92d07b',seg=16,rings=8,scale=(1.2,1,.65))
        for loc in [(-.15,-.1,.2),(.14,.06,.28),(.02,-.12,.33)]: m.sphere(.10,loc,'#bde89a',seg=10,rings=6)
    elif not expansion_item(m, item_id):
        raise ValueError('Unimplemented item ID: '+item_id)
    return [m.build(item_id)]


def common_mesh(name):
    if name.startswith('chest_'): return chest(name=='chest_rare')
    m=MB()
    if name=='gold_pile':
        for i in range(27):
            a=i*2.4; r=.035*math.sqrt(i)
            coin(m,(r*math.cos(a),r*math.sin(a),.035+(3-i%4)*.03),.085,i*27)
        for i in range(4): coin(m,(.12,0,.18+i*.035),.1)
    elif name=='key_item': key(m)
    elif name=='campfire': campfire(m)
    elif name=='banner_party':
        m.cyl(.035,1.55,(0,0,.8),GOLD,seg=10)
        m.cyl(.17,.08,(0,0,.04),DARK,seg=10)
        m.ico(.08,(0,0,1.63),GOLD)
        m.slab([(0,1.5),(.62,1.5),(.58,.8),(.34,.65),(0,.8)],.035,'#3d7f98',y=-.02)
        m.slab([(.26,1.31),(.36,1.17),(.48,1.13),(.36,1.07),(.29,.91),(.22,1.07),(.12,1.13),(.23,1.17)],.025,GOLD,y=-.05)
    else: raise ValueError(name)
    return [m.build(name)]


def output(category, name, objects):
    A.export_fbx('Props/%s/%s.fbx'%(category,name),objects)
    A.save_blend('prop_'+name)
    A.render_preview('prop_'+name,objects,angle=(75,0,15),size=512)


def main():
    data_path=os.path.join(A.REPO,'Assets','_Game','Resources','Data','items.json')
    with open(data_path,encoding='utf-8') as f: ids=[entry['id'] for entry in json.load(f)]
    selected=sys.argv[sys.argv.index('--')+1:] if '--' in sys.argv else []
    for name in ids:
        if selected and name not in selected: continue
        A.reset_scene(); output('Items',name,item_mesh(name))
    if selected:
        print('PROPS_COMPLETE items=%d'%len(selected),flush=True); return
    for name in ('chest_common','chest_rare','gold_pile','key_item','campfire','banner_party'):
        A.reset_scene(); output('Common',name,common_mesh(name))
    print('PROPS_COMPLETE items=%d common=6'%len(ids),flush=True)

if __name__=='__main__': main()
