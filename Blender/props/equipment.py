"""28 equipment displays: hollow armour/garbs/robes and individually sculpted accessories.
Original refs: equip_heavy/light/robe1..4 and acc_antidote/ruby/sapphire/speed.
No mannequin, pedestal, texture or recolour-only variant is exported. Every object has Col.
Production export entry point: Blender/weapons/generate_all.py.
"""
import math
import os
import sys
sys.path.append(os.path.normpath(os.path.join(os.path.dirname(__file__),'..','weapons')))
import _common as W
A=W.A


def shell(name, profile, color, n=24, pleats=0):
    # Continuous exterior, rolled open neck and interior: visibly a wearable empty garment.
    sections=[]
    for rx,ry,z in profile:
        sections.append([(math.cos(2*math.pi*i/n)*rx*(1+pleats*math.cos(12*math.pi*i/n)),
                          math.sin(2*math.pi*i/n)*ry*(1+pleats*math.cos(12*math.pi*i/n)),z)for i in range(n)])
    for rx,ry,z in reversed(profile):
        sections.append([(math.cos(2*math.pi*i/n)*(rx-0.014),math.sin(2*math.pi*i/n)*(ry-0.014),z)for i in range(n)])
    sections.append(sections[0])
    return W.loft(name,sections,color=color,cap_start=False,cap_end=False,smooth_angle=35)


def torso(color, armor=False, bottom=0.32):
    profile=[(0.22,0.125,bottom),(0.19,0.115,0.48),(0.255,0.15,0.70),
             (0.28,0.135,0.80),(0.13,0.095,0.90),(0.12,0.086,0.94)]
    if armor:profile[2]=(0.265,0.165,0.70)
    return shell('hollow_bodice',profile,color)


def sleeve(side,color,long=True,bell=False):
    end=0.19 if long else 0.48
    prof=[(0.087,0.09,end),(0.11 if bell else 0.072,0.10 if bell else 0.07,end+0.05),
          (0.083,0.075,0.55),(0.10,0.10,0.70),(0.105,0.10,0.76)]
    o=shell('open_sleeve',prof,color)
    o.location=(side*0.28,0,0)
    o.rotation_euler.y=math.radians(-side*15)
    return o


def seam(p,points,color=W.GOLD,r=0.007):p.append(A.tube('piping',points,radius=r,color=color,seg=8))


def belt(p,color=W.LEATHER,z=0.48,buckle=W.GOLD):
    p.append(shell('belt',[(0.198,0.132,z-0.028),(0.202,0.135,z+0.028)],color))
    p.append(A.box('buckle',(0.075,0.022,0.065),loc=(0,-0.147,z),color=buckle,bevel=0.009))
    p.append(A.box('buckle_inset',(0.045,0.025,0.034),loc=(0,-0.158,z),color=color,bevel=0.003))


def pauldron(p,s,color,size=1):
    p.append(A.sphere('shoulder_plate',r=0.125,loc=(s*0.295,0,0.77),scale=(1.25*size,1,0.55),color=color,seg=16,rings=10))
    seam(p,[(s*0.19,-0.055,0.80),(s*0.28,-0.10,0.78),(s*0.40,-0.067,0.74)],r=0.009)


def emblem(p,z,kind='sun',color=W.GOLD):
    if kind=='sun':
        p.append(W.star('chest_sun',0.095,0.052,0.025,points=8,loc=(0,-0.174,z),color=color))
        p.append(W.gem('sun_heart',0.035,loc=(0,-0.203,z),rot=(90,0,0),color='#ffbf56'))
    elif kind=='moon':
        pts=[(0.066*math.cos(a),-0.168,z+0.066*math.sin(a))for a in [math.radians(45+i*9)for i in range(31)]]
        seam(p,pts,color=color,r=0.010)
        p.append(W.gem('moon_gem',0.023,loc=(0.028,-0.176,z),rot=(90,0,0),color='#c897ff'))
    elif kind=='leaf':
        p.append(W.flat_plate_xz('leaf_badge',[(-0.052,z),(0,z+0.065),(0.052,z),(0,z-0.065)],0.013,y=-0.174,color=color))
        seam(p,[(0,-0.185,z-0.043),(0,-0.185,z+0.045)],color='#c2e8a4',r=0.003)


def tassets(p,color,count=5,low=0.12):
    for i in range(count):
        x=(i-(count-1)/2)*0.09
        p.append(W.flat_plate_xz('articulated_tasset',[(x-0.038,0.43),(x+0.038,0.43),
                                                       (x+0.045,low+0.035),(x,low),(x-0.045,low+0.035)],
                                  0.026,y=-0.112,color=color,bevel=0.006))
        seam(p,[(x-0.031,-0.13,0.40),(x-0.037,-0.13,low+0.046),(x,-0.13,low+0.02),
                (x+0.037,-0.13,low+0.046),(x+0.031,-0.13,0.40)],r=0.004)


def scale_rows(p,color,dragon=False):
    for row in range(5):
        for col in range(5):
            x=(col-2)*0.073+(0.025 if row%2 else 0)
            z=0.52+row*0.065
            y=-0.147+abs(x)*0.1
            shape=[(x-0.035,z+0.045),(x+0.035,z+0.045),(x+0.038,z+0.01),
                   (x,z-0.022 if dragon else z-0.013),(x-0.038,z+0.01)]
            p.append(W.flat_plate_xz('overlapping_scale',shape,0.015,y=y-0.015*row,color=color,bevel=0.002))
            if dragon:seam(p,[(x,-0.16-0.015*row,z+0.031),(x,-0.163-0.015*row,z-0.003)],color='#f9a659',r=0.002)


def armor_chain():
    p=[torso('#5c6775',True,bottom=0.23)]
    for s in (-1,1):p.append(sleeve(s,'#596576',False))
    # Real interlocking surface links, not a painted mesh texture.
    for row in range(9):
        for col in range(9):
            x=(col-4)*0.045+(0.011 if row%2 else 0)
            z=0.30+row*0.053
            if abs(x)<0.19+(z-0.4)*0.15:
                p.append(A.torus('chain_link',R=0.019,r=0.0035,loc=(x,-0.154+abs(x)*0.1,z),
                                 rot=(90,0,22 if (row+col)%2 else -22),scale=(1,1,1.15),color=W.STEEL,seg=12,minor=6))
    belt(p,z=0.47,buckle=W.IRON)
    seam(p,[(-0.12,-0.089,0.93),(0,-0.111,0.91),(0.12,-0.089,0.93)],color=W.LEATHER,r=0.011)
    return W.finalize(p,'armor_chain')


def armor_scale():
    p=[torso('#454f5d',True)]
    scale_rows(p,'#a8afb5')
    for s in (-1,1):pauldron(p,s,W.STEEL,0.85)
    belt(p,z=0.47,buckle=W.BRONZE)
    tassets(p,W.STEEL,5,0.24)
    return W.finalize(p,'armor_scale')


def armor_plate():
    p=[torso('#64748b',True)]
    for s in (-1,1):
        pauldron(p,s,W.SILVER,1.2)
        p.append(W.flat_plate_xz('breastplate',[(s*0.018,0.51),(s*0.21,0.56),(s*0.25,0.77),
                                              (s*0.07,0.84),(s*0.015,0.71)],0.035,y=-0.16,color=W.SILVER,bevel=0.01))
        for j in range(3):
            p.append(A.box('shoulder_lame',(0.17,0.15,0.035),loc=(s*(0.30+j*0.018),0,0.74-j*0.045),color=W.STEEL,bevel=0.01))
    tassets(p,W.STEEL,5,0.15)
    belt(p,z=0.46,buckle=W.SILVER)
    seam(p,[(0,-0.19,0.52),(0,-0.195,0.73),(0,-0.145,0.85)],color='#e7eaf0',r=0.009)
    return W.finalize(p,'armor_plate')


def armor_dragon():
    p=[torso('#412729',True)]
    scale_rows(p,'#8e3640',True)
    for s in (-1,1):
        pauldron(p,s,'#54252d',1.25)
        for j in range(3):
            p.append(W.crystal('dragon_spike',0.025,0.12-j*0.02,loc=(s*(0.27+j*0.047),0.008,0.82-j*0.025),
                               rot=(0,s*(15+j*13),0),color='#e5c3a1',mat='M_Toon'))
    tassets(p,'#762d36',5,0.11)
    belt(p,z=0.47)
    p.append(W.gem('ember_brooch',0.034,loc=(0,-0.23,0.78),rot=(90,0,0),color='#ff7447'))
    return W.finalize(p,'armor_dragon')


def armor_dawn():
    p=[torso(W.WHITE,True)]
    for s in (-1,1):
        pauldron(p,s,W.SILVER,1.15)
        for j in range(3):
            p.append(W.flat_plate_xz('wing_pauldron',[(s*0.21,0.77-j*0.03),(s*(0.34+j*0.06),0.83-j*0.025),
                                                     (s*(0.43+j*0.035),0.92-j*0.025),(s*0.31,0.79-j*0.03)],
                                     0.035,color=W.GOLD,bevel=0.005))
        seam(p,[(s*0.15,-0.15,0.84),(s*0.23,-0.18,0.68),(s*0.16,-0.18,0.54)],r=0.012)
    tassets(p,W.WHITE,5,0.08)
    belt(p,color='#bf933c',z=0.47)
    emblem(p,0.72)
    p.append(shell('raised_gorget',[(0.13,0.10,0.91),(0.15,0.11,1.0)],W.GOLD))
    return W.finalize(p,'armor_dawn')


def lacing(p,z0=0.54,z1=0.80):
    for i in range(6):
        z=z0+(z1-z0)*i/6
        seam(p,[(-0.027,-0.165,z),(0.027,-0.165,z+0.035)],color='#dac08f',r=0.0035)
        seam(p,[(0.027,-0.166,z),(-0.027,-0.166,z+0.035)],color='#dac08f',r=0.0035)


def hood(p,color,z=0.84):
    # Draped hood with open face: outer + inner back half; opening border left visible.
    sections=[]
    for zz,rx,ry in [(z,0.15,0.14),(z+0.08,0.19,0.15),(z+0.23,0.155,0.125),(z+0.30,0.07,0.07)]:
        sections.append([(rx*math.cos(math.pi*i/16),ry*math.sin(math.pi*i/16)-0.025,zz)for i in range(17)])
    p.append(W.loft('open_hood',sections,color=color,closed=False,cap_start=False,cap_end=False))
    seam(p,[(-0.15,-0.026,z),(-0.19,-0.026,z+0.08),(-0.155,-0.026,z+0.23),(-0.07,-0.026,z+0.30),
            (0.07,-0.026,z+0.30),(0.155,-0.026,z+0.23),(0.19,-0.026,z+0.08),(0.15,-0.026,z)],color='#ccb986',r=0.009)


def garb_leather():
    p=[torso('#915732',bottom=0.30)]
    lacing(p)
    belt(p,z=0.47)
    for s in (-1,1):
        seam(p,[(s*0.08,-0.10,0.89),(s*0.2,-0.12,0.80),(s*0.24,-0.13,0.68)],color='#d49c61',r=0.007)
        p.append(A.box('hip_pouch',(0.095,0.065,0.11),loc=(s*0.185,-0.13,0.40),color=W.LEATHER_DK,bevel=0.014))
    return W.finalize(p,'garb_leather')


def garb_ranger():
    p=[torso('#56734e',bottom=0.26)]
    lacing(p)
    hood(p,'#354d38')
    # Asymmetric travelling shoulder cape with leafy hem and leather utility straps.
    p.append(W.flat_plate_xz('shoulder_cape',[(-0.34,0.80),(-0.13,0.91),(0.03,0.86),(-0.06,0.44),
                                             (-0.16,0.51),(-0.23,0.43),(-0.34,0.52)],0.025,y=0.14,color='#39563c'))
    for s in (-1,1):p.append(sleeve(s,'#526148',False))
    seam(p,[(-0.18,-0.16,0.83),(0.0,-0.18,0.66),(0.19,-0.145,0.46)],color=W.LEATHER,r=0.016)
    belt(p,z=0.47)
    emblem(p,0.74,'leaf',W.BRONZE)
    return W.finalize(p,'garb_ranger')


def garb_shadow():
    p=[torso('#29293a',bottom=0.26)]
    hood(p,'#252331')
    for s in (-1,1):
        p.append(sleeve(s,'#363346',True))
        p.append(W.flat_plate_xz('split_coattail',[(s*0.01,0.49),(s*0.19,0.48),(s*0.26,0.10),(s*0.12,0.03)],0.021,
                                 y=0.11,color='#393247'))
        pauldron(p,s,'#5b566b',0.75)
        seam(p,[(s*0.03,-0.172,0.84),(s*0.10,-0.176,0.65),(s*0.05,-0.152,0.50)],color='#a35aa3',r=0.005)
    belt(p,color='#312e38',z=0.47,buckle=W.SILVER)
    emblem(p,0.72,'moon',W.SILVER)
    return W.finalize(p,'garb_shadow')


def garb_wind():
    p=[torso('#d4ead7',bottom=0.29)]
    for s in (-1,1):
        p.append(sleeve(s,'#4c9d87',False))
        for j in range(3):
            p.append(W.flat_plate_xz('feather_shoulder',[(s*0.21,0.81-j*0.034),(s*0.31,0.85-j*0.026),
                                                        (s*(0.45-j*0.02),0.87-j*0.025),(s*0.29,0.76-j*0.045)],
                                     0.015,color='#e5f4e3',bevel=0.002))
    p.append(W.flat_plate_xz('wind_sash',[(-0.19,0.49),(0.18,0.46),(0.24,0.31),(0.41,0.20),(0.27,0.18),
                                         (0.09,0.39),(-0.17,0.42)],0.024,y=-0.14,color='#3c9b86'))
    emblem(p,0.73,'leaf',W.SILVER)
    seam(p,[(-0.15,-0.12,0.85),(0,-0.174,0.62),(0.15,-0.12,0.85)],color=W.SILVER,r=0.009)
    return W.finalize(p,'garb_wind')


def garb_dawn():
    p=[torso('#a93839',bottom=0.28)]
    for s in (-1,1):
        p.append(sleeve(s,'#7b242c',True))
        pauldron(p,s,W.GOLD,0.95)
        p.append(W.flat_plate_xz('split_tabard',[(s*0.015,0.49),(s*0.19,0.47),(s*0.30,0.08),
                                               (s*0.15,0.04)],0.024,y=-0.12,color='#b84437'))
        seam(p,[(s*0.022,-0.14,0.46),(s*0.16,-0.142,0.07),(s*0.28,-0.14,0.09)],r=0.007)
    p.append(shell('standing_collar',[(0.12,0.09,0.91),(0.14,0.10,1.02)],'#b63838'))
    belt(p,color=W.GOLD_DK,z=0.47)
    emblem(p,0.73)
    return W.finalize(p,'garb_dawn')


def robe_base(color,lining,long=True,wide=False):
    p=[torso(color)]
    p.append(shell('pleated_robe_skirt',[(0.35 if wide else 0.29,0.19,0.035),(0.28,0.16,0.19),
                                       (0.19,0.12,0.49)],color,n=36,pleats=0.04))
    for s in (-1,1):p.append(sleeve(s,color,long,bell=wide))
    p.append(shell('hem_border',[(0.35 if wide else 0.29,0.193,0.035),(0.342 if wide else 0.281,0.187,0.075)],lining,n=36))
    return p


def robe_cloth():
    p=robe_base('#a69b83','#736750')
    hood(p,'#9a8c72')
    belt(p,color='#665040',z=0.47,buckle=W.BRONZE)
    seam(p,[(0,-0.16,0.88),(0,-0.159,0.53),(0,-0.19,0.06)],color='#d1c6ad',r=0.004)
    for z in (0.64,0.72,0.80):p.append(A.sphere('wood_button',r=0.008,loc=(0,-0.168,z),color=W.WOOD,seg=10,rings=6))
    return W.finalize(p,'robe_cloth')


def robe_silk():
    p=robe_base('#5d75b9','#e6c991',wide=True)
    p.append(shell('silk_collar',[(0.12,0.09,0.92),(0.125,0.095,0.98)],'#ead4a6'))
    for s in (-1,1):
        seam(p,[(s*0.14,-0.12,0.85),(s*0.03,-0.167,0.56),(s*0.14,-0.20,0.08)],color='#e6c991',r=0.009)
    p.append(W.flat_plate_xz('silk_sash',[(-0.2,0.51),(0.2,0.48),(0.17,0.41),(-0.17,0.43)],0.02,y=-0.14,color='#d3a951'))
    p.append(W.flat_plate_xz('sash_tail',[(0.08,0.45),(0.15,0.43),(0.22,0.16),(0.13,0.20)],0.012,y=-0.18,color='#d3a951'))
    p.append(W.gem('silk_brooch',0.025,loc=(0,-0.18,0.74),rot=(90,0,0),color='#80d3ff'))
    return W.finalize(p,'robe_silk')


def robe_mystic():
    p=robe_base('#65457d','#bd9add',wide=True)
    hood(p,'#47305e')
    emblem(p,0.75,'moon')
    for s in (-1,1):
        p.append(W.flat_plate_xz('pointed_stole',[(s*0.08,0.89),(s*0.18,0.84),(s*0.14,0.40),
                                                (s*0.12,0.12),(s*0.045,0.26)],0.023,y=-0.16,color='#3b2a55'))
        for j in range(5):
            z=0.30+j*0.095
            p.append(W.flat_plate_xz('mystic_rune',[(s*0.10-0.013,z),(s*0.10,z+0.024),
                                                  (s*0.10+0.013,z),(s*0.10,z-0.024)],0.003,y=-0.18,color='#c694ff',mat='M_Emit'))
    belt(p,color='#453153',z=0.48)
    return W.finalize(p,'robe_mystic')


def robe_sage():
    p=robe_base('#eee6cd',W.GOLD,wide=True)
    p.append(shell('sage_high_collar',[(0.13,0.1,0.91),(0.16,0.12,1.05)],'#363d72'))
    for s in (-1,1):
        p.append(W.flat_plate_xz('sage_stole',[(s*0.075,0.91),(s*0.15,0.86),(s*0.13,0.47),
                                              (s*0.18,0.08),(s*0.08,0.06)],0.017,y=-0.17,color='#394373'))
        seam(p,[(s*0.079,-0.183,0.90),(s*0.079,-0.183,0.49),(s*0.083,-0.183,0.08)],r=0.005)
    belt(p,color='#4e5588',z=0.48)
    p.append(A.box('belt_spellbook',(0.105,0.065,0.14),loc=(-0.195,-0.13,0.38),color='#684079',bevel=0.012))
    p.append(A.box('book_pages',(0.08,0.058,0.116),loc=(-0.195,-0.141,0.38),color='#efddb3',bevel=0.004))
    p.append(A.box('book_front',(0.105,0.012,0.14),loc=(-0.195,-0.176,0.38),color='#684079',bevel=0.005))
    emblem(p,0.74,'moon',W.GOLD)
    return W.finalize(p,'robe_sage')


def robe_dawn():
    p=robe_base(W.WHITE,W.GOLD,wide=True)
    p.append(shell('radiant_collar',[(0.12,0.1,0.90),(0.17,0.12,1.06)],W.WHITE))
    for s in (-1,1):
        p.append(W.flat_plate_xz('radiant_stole',[(s*0.065,0.92),(s*0.15,0.86),(s*0.10,0.5),
                                                 (s*0.28,0.09),(s*0.19,0.05),(s*0.02,0.45)],0.025,y=-0.172,color=W.GOLD))
        for j in range(2):
            p.append(W.flat_plate_xz('collar_wing',[(s*0.13,0.88),(s*0.29,0.84-j*0.04),
                                                  (s*0.39,0.91-j*0.035),(s*0.21,0.96-j*0.04)],0.025,color=W.WHITE,bevel=0.003))
        seam(p,[(s*0.17,-0.12,1.05),(s*0.13,-0.11,0.94)],r=0.009)
    p.append(W.flat_plate_xz('blue_inner_tabard',[(-0.02,0.43),(0.02,0.43),(0.14,0.06),(-0.14,0.06)],0.017,y=-0.185,color='#4a91bd'))
    emblem(p,0.77)
    belt(p,color=W.GOLD,z=0.49)
    return W.finalize(p,'robe_dawn')


def ring_parts(color,r=0.15):
    return [A.torus('ring_shank',R=r,r=0.025,loc=(0,0,0.20),rot=(90,0,0),color=color,seg=32,minor=10)]


def setting(p,z,r,color,metal=W.GOLD):
    p.append(A.torus('gem_bezel',R=r,r=0.012,loc=(0,-0.033,z),rot=(90,0,0),color=metal,seg=24,minor=8))
    p.append(W.gem('set_gem',r*0.84,loc=(0,-0.045,z),rot=(90,0,0),color=color))
    for s in (-1,1):p.append(A.sphere('setting_claw',r=0.012,loc=(s*r*0.8,-0.05,z+r*0.55),color=metal,seg=10,rings=6))


def acc_antidote_ring():
    p=ring_parts(W.BRONZE)
    setting(p,0.36,0.07,'#76df78',W.BRONZE)
    for s in (-1,1):
        seam(p,[(s*0.10,-0.03,0.30),(s*0.14,-0.02,0.28),(s*0.15,-0.01,0.23)],color='#527e40',r=0.008)
    return W.finalize(p,'acc_antidote_ring')


def acc_guardian_ring():
    p=ring_parts(W.SILVER,0.17)
    p.append(W.flat_plate_xz('shield_seal',[(-0.10,0.44),(0.1,0.44),(0.085,0.33),(0,0.27),(-0.085,0.33)],0.03,y=-0.03,color=W.GOLD))
    setting(p,0.37,0.049,'#75caff')
    for s in (-1,1):
        for j in range(2):seam(p,[(s*(0.06+j*0.018),-0.033,0.33),(s*(0.15+j*0.008),-0.024,0.26)],r=0.007)
    return W.finalize(p,'acc_guardian_ring')


def pendant_base(metal=W.GOLD):
    p=[A.torus('pendant_bail',R=0.031,r=0.008,loc=(0,0,0.49),rot=(90,0,0),color=metal,seg=20,minor=8)]
    # Oval chain with actual links, all part of the display asset.
    for i in range(28):
        a=2*math.pi*i/28
        p.append(A.torus('chain_link',R=0.016,r=0.0035,loc=(0.17*math.sin(a),0.015,0.59+0.15*math.cos(a)),
                         rot=(90,0,(i%2)*65),color=metal,seg=10,minor=6))
    return p


def acc_flame_amulet():
    p=pendant_base()
    pts=[(-0.075,0.21),(-0.13,0.30),(-0.08,0.41),(-0.03,0.34),(0.005,0.48),(0.095,0.36),(0.13,0.26),(0.07,0.20)]
    p.append(W.flat_plate_xz('flame_frame',pts,0.035,color=W.GOLD,bevel=0.005))
    p.append(W.crystal('flame_ruby',0.06,0.12,loc=(0,-0.03,0.29),rot=(0,0,-15),color='#ff5139'))
    return W.finalize(p,'acc_flame_amulet')


def acc_frost_amulet():
    p=pendant_base(W.SILVER)
    p += W.rays('snowflake',6,0.055,0.145,0.012,0.023,z=0.33,color=W.SILVER)
    for i in range(6):
        a=2*math.pi*i/6
        for s in (-1,1):
            b=a+s*0.65
            seam(p,[(0.1*math.cos(a),0,0.33+0.1*math.sin(a)),
                    (0.1*math.cos(a)-0.044*math.cos(b),0,0.33+0.1*math.sin(a)-0.044*math.sin(b))],color=W.SILVER,r=0.006)
    setting(p,0.33,0.055,'#93e5ff',W.SILVER)
    return W.finalize(p,'acc_frost_amulet')


def acc_shadow_amulet():
    p=pendant_base(W.SILVER)
    p.append(W.flat_plate_xz('ward_frame',[(-0.12,0.34),(0,0.48),(0.12,0.34),(0,0.15)],0.035,color='#54516f',bevel=0.006))
    p.append(W.flat_plate_xz('ward_field',[(-0.09,0.34),(0,0.44),(0.09,0.34),(0,0.19)],0.012,y=-0.026,color='#241b38'))
    pts=[(0.06*math.cos(a),-0.045,0.34+0.065*math.sin(a))for a in [math.radians(50+i*9)for i in range(30)]]
    seam(p,pts,color='#c3a5ef',r=0.01)
    p.append(W.gem('ward_eye',0.027,loc=(0.019,-0.047,0.33),rot=(90,0,0),color='#aa6cff'))
    return W.finalize(p,'acc_shadow_amulet')


def acc_sage_pendant():
    p=pendant_base()
    p.append(W.flat_plate_xz('sage_teardrop',[(0,0.15),(-0.11,0.32),(-0.07,0.43),(0.07,0.43),(0.11,0.32)],0.032,color=W.GOLD,bevel=0.004))
    p.append(W.crystal('sage_sapphire',0.063,0.18,loc=(0,-0.035,0.23),color='#73aaff'))
    for s in (-1,1):seam(p,[(s*0.07,-0.027,0.32),(s*0.09,-0.027,0.37),(s*0.05,-0.027,0.41)],r=0.006)
    return W.finalize(p,'acc_sage_pendant')


def acc_lucky_charm():
    p=pendant_base(W.BRONZE)
    p.append(A.cyl('charm_coin',r=0.12,depth=0.022,loc=(0,0,0.33),rot=(90,0,0),color=W.BRONZE,seg=32))
    p.append(A.torus('coin_rim',R=0.109,r=0.009,loc=(0,-0.019,0.33),rot=(90,0,0),color=W.GOLD,seg=32,minor=8))
    for i in range(4):
        a=i*math.pi/2+math.pi/4
        p.append(A.sphere('clover_leaf',r=0.037,loc=(math.cos(a)*0.039,-0.03,0.345+math.sin(a)*0.039),scale=(1,0.22,1),color='#68ad58',seg=14,rings=8))
    seam(p,[(0,-0.04,0.32),(0.026,-0.04,0.275)],color='#76c164',r=0.006)
    return W.finalize(p,'acc_lucky_charm')


def acc_power_band():
    p=[shell('heavy_bracer',[(0.13,0.11,0.05),(0.145,0.12,0.09),(0.14,0.12,0.28),(0.16,0.13,0.31)],'#864229')]
    for z in (0.08,0.28):p.append(A.torus('bracer_rim',R=0.142,r=0.015,loc=(0,0,z),scale=(1,0.83,1),color=W.BRONZE,seg=24,minor=8))
    p.append(W.flat_plate_xz('power_plate',[(-0.08,0.27),(0.08,0.27),(0.09,0.12),(0,0.08),(-0.09,0.12)],0.024,y=-0.125,color=W.BRONZE))
    for s in (-1,1):
        for z in (0.13,0.24):p.append(A.sphere('bracer_rivet',r=0.012,loc=(s*0.06,-0.146,z),color=W.GOLD,seg=10,rings=6))
    p.append(W.gem('power_ruby',0.036,loc=(0,-0.151,0.19),rot=(90,0,0),color='#ef6250'))
    return W.finalize(p,'acc_power_band')


def acc_awake_bell():
    p=[A.lathe('bell_shell',[(0.13,0.06),(0.137,0.08),(0.105,0.14),(0.095,0.25),(0.055,0.31),
                           (0.02,0.34),(0.012,0.34),(0.037,0.29),(0.076,0.24),(0.085,0.14),(0.116,0.07)],color=W.GOLD,seg=32)]
    p.append(A.torus('bell_loop',R=0.028,r=0.008,loc=(0,0,0.37),rot=(90,0,0),color=W.GOLD,seg=20,minor=8))
    p.append(A.cyl('clapper_rod',r=0.012,depth=0.17,loc=(0,0,0.15),color=W.GOLD_DK,seg=12))
    p.append(A.sphere('bell_clapper',r=0.031,loc=(0,0,0.061),color=W.BRONZE,seg=16,rings=10))
    p.append(A.torus('bell_rim',R=0.127,r=0.012,loc=(0,0,0.075),color=W.GOLD_HI,seg=32,minor=8))
    p.append(W.star('bell_star',0.04,0.018,0.013,loc=(0,-0.102,0.22),color='#ece9dd'))
    p.append(W.flat_plate_xz('red_ribbon',[(-0.015,0.37),(-0.115,0.42),(-0.095,0.32),(-0.012,0.355),
                                         (0.095,0.31),(0.11,0.415),(0.015,0.37)],0.022,y=-0.025,color='#ae3946'))
    return W.finalize(p,'acc_awake_bell')


def acc_clarity_earring():
    p=[]
    for s in (-1,1):
        x=s*0.09
        p.append(A.torus('earring_hook',R=0.028,r=0.006,loc=(x,0,0.36),rot=(90,0,0),color=W.SILVER,seg=24,minor=8))
        p.append(A.torus('drop_ring',R=0.011,r=0.004,loc=(x,0,0.31),rot=(90,0,0),color=W.SILVER,seg=16,minor=6))
        p.append(W.crystal('clarity_drop',0.039,0.13,loc=(x,0,0.17),color='#9fe4ff'))
        for j in (-1,1):seam(p,[(x,0,0.29),(x+j*0.045,0,0.22),(x,0,0.13)],color=W.SILVER,r=0.006)
    return W.finalize(p,'acc_clarity_earring')


def acc_eagle_eye():
    p=pendant_base(W.BRONZE)
    p.append(W.flat_plate_xz('eagle_medallion',[(-0.14,0.34),(0,0.43),(0.14,0.34),(0,0.25)],0.025,color=W.BRONZE))
    for s in (-1,1):
        for j in range(3):
            p.append(W.flat_plate_xz('eagle_feather',[(s*0.02,0.34-j*0.016),(s*0.11,0.38-j*0.02),
                                                     (s*(0.21-j*0.024),0.42-j*0.03),(s*0.11,0.31-j*0.02)],0.017,color=W.GOLD))
    p.append(A.torus('eye_bezel',R=0.04,r=0.009,loc=(0,-0.023,0.34),rot=(90,0,0),color=W.GOLD,seg=24,minor=8))
    p.append(W.gem('eagle_eye',0.035,loc=(0,-0.039,0.34),rot=(90,0,0),color='#ffb64b'))
    p.append(A.sphere('pupil',r=0.014,loc=(0,-0.061,0.34),scale=(0.55,0.25,1),color='#392617',seg=12,rings=8))
    return W.finalize(p,'acc_eagle_eye')


def acc_hero_emblem():
    p=pendant_base()
    p.append(W.star('hero_compass',0.155,0.065,0.032,points=8,loc=(0,0,0.32),color=W.GOLD))
    p.append(A.torus('compass_rim',R=0.087,r=0.01,loc=(0,-0.03,0.32),rot=(90,0,0),color=W.SILVER,seg=32,minor=8))
    for i,c in enumerate(('#7de391','#88daff','#ff764f','#bb8bff')):
        a=i*math.pi/2
        p.append(W.gem('seal_crystal',0.028,loc=(math.sin(a)*0.065,-0.047,0.32+math.cos(a)*0.065),rot=(90,0,0),color=c))
    p.append(W.gem('hero_core',0.035,loc=(0,-0.05,0.32),rot=(90,0,0),color='#ffe293'))
    return W.finalize(p,'acc_hero_emblem')


def acc_wind_boots():
    p=[]
    for s in (-1,1):
        x=s*0.12
        boot=shell('open_boot_shaft',[(0.073,0.074,0.12),(0.073,0.067,0.25),(0.097,0.082,0.38)],'#50635c')
        boot.location.x=x
        p.append(boot)
        p.append(A.sphere('boot_toe',r=0.09,loc=(x,-0.07,0.09),scale=(0.83,1.58,0.75),color='#476152',seg=18,rings=10))
        p.append(A.box('boot_sole',(0.16,0.27,0.031),loc=(x,-0.06,0.035),color='#303631',bevel=0.022))
        for z in (0.21,0.33):
            seam(p,[(x-0.073,-0.037,z),(x,-0.082,z),(x+0.073,-0.037,z)],color=W.BRONZE,r=0.009)
        for j in range(3):
            p.append(W.flat_plate_xz('boot_wing',[(x+s*0.06,0.17+j*0.033),(x+s*0.13,0.20+j*0.04),
                                                (x+s*(0.18-j*0.014),0.26+j*0.035),(x+s*0.08,0.23+j*0.032)],
                                     0.013,color='#e6edd5',bevel=0.002))
    return W.finalize(p,'acc_wind_boots')


BUILDERS=[('armor_chain',armor_chain),('armor_scale',armor_scale),('armor_plate',armor_plate),
 ('armor_dragon',armor_dragon),('armor_dawn',armor_dawn),('garb_leather',garb_leather),
 ('garb_ranger',garb_ranger),('garb_shadow',garb_shadow),('garb_wind',garb_wind),('garb_dawn',garb_dawn),
 ('robe_cloth',robe_cloth),('robe_silk',robe_silk),('robe_mystic',robe_mystic),('robe_sage',robe_sage),
 ('robe_dawn',robe_dawn),('acc_antidote_ring',acc_antidote_ring),('acc_awake_bell',acc_awake_bell),
 ('acc_clarity_earring',acc_clarity_earring),('acc_eagle_eye',acc_eagle_eye),('acc_flame_amulet',acc_flame_amulet),
 ('acc_frost_amulet',acc_frost_amulet),('acc_guardian_ring',acc_guardian_ring),('acc_hero_emblem',acc_hero_emblem),
 ('acc_lucky_charm',acc_lucky_charm),('acc_power_band',acc_power_band),('acc_sage_pendant',acc_sage_pendant),
 ('acc_shadow_amulet',acc_shadow_amulet),('acc_wind_boots',acc_wind_boots)]
