"""Strung bows based on equip_bow1..4 original icon silhouettes.
All grips are centred at origin. +Z is upper tip; -Y is shooting-facing side.
The original Korean data says crossbow, but source art consistently depicts longbows.
"""
import math
import os
import sys
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
import _common as W
A=W.A


def bow_base(name,length,reach,metal,wood,grip,mode):
    p=W.wrap_grip('grip',-0.07,0.07,0.025,turns=6,color=grip,band='#302a27')
    for z in (-0.08,0.08):p.append(W.band('grip_collar',z,0.033,0.02,color=metal))
    tips=[]
    for s in (-1,1):
        # Asymmetrical YZ curves give a recognizable curved bow profile at identity.
        ctrl=[(0,0,s*0.075),(0,reach*0.42,s*length*0.24),(0,reach,s*length*0.65),
              (0,reach*0.76,s*length*0.88),(0,reach*0.33,s*length)]
        if mode>=2:ctrl.insert(-1,(0,reach*0.32,s*length*0.94))
        path=W.curve_pts(ctrl,48)
        p.append(W.sweep('limb',path,lambda t:0.032*(1-0.62*t),lambda t:0.017*(1-0.5*t),
                         color=wood,up=(1,0,0)))
        # Thin contrasting lamination follows each curved limb, not a recolour tier.
        if mode>=1:
            for side in (-1,1):
                p.append(A.tube('lamination',[(side*0.014,y,z)for x,y,z in path],radius=0.0035,color=metal,seg=6))
        tips.append(ctrl[-1])
        p.append(A.sphere('string_nock',r=0.015,loc=ctrl[-1],color=metal,seg=12,rings=8))
    p.append(A.tube('taut_bowstring',[tips[0],(0,-0.052,0),tips[1]],radius=0.0028,color='#f4ead4',seg=6))
    p.append(A.tube('serving',[ (0,-0.052,-0.045),(0,-0.052,0.045)],radius=0.0045,color='#735844',seg=6))
    p.append(A.box('arrow_rest',(0.056,0.023,0.014),loc=(0,-0.029,0.075),color=metal,bevel=0.004))
    return p


def bow_short():
    p=bow_base('short',0.39,0.095,W.BRONZE,W.WOOD,W.LEATHER,0)
    # Separate pegged joint, grain lines, and modest hand-carved tip.
    for s in (-1,1):
        p.append(A.cyl('joint_rivet',r=0.009,depth=0.048,loc=(0,0.025,s*0.13),rot=(0,90,0),color=W.BRONZE,seg=10))
        p.append(A.tube('woodgrain',[(0.019,0.05,s*0.18),(0.015,0.087,s*0.25),(0.01,0.08,s*0.31)],radius=0.0018,color=W.WOOD_DK,seg=6))
    return W.finalize(p,'bow_short')


def bow_hunter():
    p=bow_base('hunter',0.47,0.135,W.IRON,'#683e29','#495440',1)
    # Strong horn siyahs and practical metal bracing.
    for s in (-1,1):
        p.append(W.flat_plate('horn_tip',[(0.09,s*0.34),(0.077,s*0.405),(0.027,s*0.49),
                                         (0.041,s*0.47),(0.065,s*0.415),(0.11,s*0.365)],0.031,color='#e2ceaa',bevel=0.002))
        for z in (0.16,0.29):
            p.append(A.box('limb_binding',(0.044,0.017,0.025),loc=(0,0.06 if z<0.2 else 0.13,s*z),color=W.IRON_DK,bevel=0.003))
        p.append(A.tube('leather_tie',[(0.024,0.024,s*0.15),(0.035,0.025,s*0.19),(0.02,0.016,s*0.24)],radius=0.004,color=W.LEATHER,seg=6))
    return W.finalize(p,'bow_hunter')


def bow_composite():
    p=bow_base('composite',0.52,0.17,W.GOLD,'#363a56','#733c3e',2)
    for s in (-1,1):
        # Double parallel composite brace and a pointed metal shoulder around the limb.
        path=W.curve_pts([(0,0.015,s*0.09),(0,0.1,s*0.24),(0,0.126,s*0.34),(0,0.075,s*0.45)],30)
        p.append(W.sweep('support_brace',path,lambda t:0.012*(1-0.65*t),lambda t:0.013,color=W.GOLD,up=(1,0,0)))
        p.append(W.flat_plate('shoulder_plate',[(0.055,s*0.14),(0.1,s*0.19),(0.2,s*0.30),
                                               (0.181,s*0.325),(0.125,s*0.28)],0.04,color=W.STEEL,bevel=0.003))
        for side in (-1,1):
            p.append(W.gem('garnet',0.022,loc=(side*0.024,0.13,s*0.26),rot=(0,side*90,0),color='#e84754'))
        p.append(A.tube('engraving',[(0.024,0.057,s*0.16),(0.024,0.135,s*0.27),(0.024,0.151,s*0.33)],radius=0.0028,color=W.GOLD_HI,seg=6))
    return W.finalize(p,'bow_composite')


def bow_gale():
    p=bow_base('gale',0.57,0.19,W.SILVER,'#296365','#245a55',2)
    # Feather fins jut beyond the main recurved limbs: readable at combat camera distance.
    for s in (-1,1):
        for j in range(3):
            z=0.19+j*0.065
            p.append(W.flat_plate('wind_feather',[(0.085+j*0.025,s*z),(0.17+j*0.025,s*(z+0.035)),
                                                  (0.23+j*0.012,s*(z+0.115)),(0.16+j*0.022,s*(z+0.072))],
                                  0.025,color=W.SILVER,bevel=0.002))
            p.append(A.tube('feather_vein',[(0.016,0.1+j*0.027,s*(z+0.015)),
                                           (0.016,0.195+j*0.017,s*(z+0.085))],radius=0.003,color='#84e5ce',mat='M_Emit',seg=6))
        p.append(W.crystal('wind_crystal',0.026,0.09,loc=(0,0.14,s*0.34),rot=(0,0,0 if s>0 else 180),color='#8affde'))
    for side in (-1,1):p.append(W.gem('grip_jewel',0.019,loc=(side*0.03,0,0),rot=(0,side*90,0),color='#83f5ce'))
    return W.finalize(p,'bow_gale')


def bow_star():
    p=bow_base('star',0.63,0.205,W.SILVER,'#38254b','#523178',3)
    for s in (-1,1):
        # Silver thorn points over a violet energy channel, open diamond cages at shoulders.
        for j in range(4):
            z=0.16+j*0.075
            p.append(W.flat_plate('astral_thorn',[(0.085+j*0.02,s*z),(0.14+j*0.015,s*(z+0.03)),
                                                  (0.26-j*0.007,s*(z+0.11)),(0.16+j*0.013,s*(z+0.062))],
                                  0.023,color=W.SILVER,bevel=0.002))
        diamond=[(0,0.11,s*0.24),(0,0.185,s*0.30),(0,0.20,s*0.40),(0,0.125,s*0.34),(0,0.11,s*0.24)]
        p.append(A.tube('open_star_cage',diamond,radius=0.009,color=W.GOLD,seg=8))
        p.append(W.gem('star_ruby',0.035,loc=(0,0.153,s*0.32),rot=(0,90,0),color='#ff53b1'))
        path=W.curve_pts([(0,0.03,s*0.1),(0,0.11,s*0.26),(0,0.2,s*0.42),(0,0.155,s*0.51)],30)
        p.append(A.tube('astral_inlay',[(0.02,y,z)for x,y,z in path],radius=0.004,color='#b88aff',mat='M_Emit',seg=6))
    p.append(W.star('grip_star',0.045,0.02,0.018,points=4,loc=(0,-0.031,0),color=W.GOLD))
    return W.finalize(p,'bow_star')


BUILDERS=[('bow_short',bow_short),('bow_hunter',bow_hunter),('bow_composite',bow_composite),
          ('bow_gale',bow_gale),('bow_star',bow_star)]
