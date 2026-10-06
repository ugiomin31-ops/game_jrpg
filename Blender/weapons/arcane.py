"""Five staffs and five cleric maces, authored from original equip_staff/mace icons.
Grip is world zero; head is +Z. Tier upgrades change head architecture, not just colour.
Run generate_all.py to export FBX, individual blend sources and previews.
"""
import math
import os
import sys
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
import _common as W
A = W.A


def shaft_parts(length, metal, body, grip, staff=True):
    low = -0.38 if staff else -0.11
    p = [W.shaft('shaft', [(0.0, low-0.03), (0.018, low), (0.021, low+0.025),
                           (0.018, 0.14), (0.023, length-0.06), (0.028, length)], color=body)]
    p += W.wrap_grip('grip', -0.065, 0.065, 0.025, turns=6, color=grip, band='#382b35')
    for z in (low+0.025, -0.072, 0.072, length-0.045, length):
        p.append(W.band('collar', z, 0.029, 0.014, color=metal))
    return p


def front_gem(name, z, r, color, y=-0.035, x=0):
    return W.gem(name, r, loc=(x, y, z), rot=(90, 0, 0), color=color)


def rune_chain(p, z0, z1, color, radius=0.022, count=6):
    for i in range(count):
        z = z0 + (z1-z0)*i/max(1, count-1)
        p.append(W.flat_plate_xz('engraved_rune', [(-0.009,z), (0,z+0.018), (0.009,z), (0,z-0.018)],
                                 0.002, y=-radius, color=color, mat='M_Emit'))


def prong(name, path, color, width=0.025):
    return W.sweep(name, W.curve_pts(path, 28), lambda t: width*(1-0.98*t),
                   lambda t: width*0.65*(1-0.7*t), color=color, up=(0,1,0))


def staff_oak():
    p = shaft_parts(0.61, W.BRONZE, W.WOOD, W.LEATHER)
    # A carved crook and living twig silhouette rather than a sphere on a rod.
    path = W.curve_pts([(0,0,0.57),(-0.032,0,0.67),(-0.068,0,0.73),(-0.052,0,0.80),
                       (0.025,0,0.83),(0.082,0,0.78),(0.075,0,0.72),(0.037,0,0.705)],32)
    p.append(W.sweep('oak_crook',path,lambda t:0.027*(1-0.4*t),lambda t:0.022,color=W.WOOD))
    p.append(W.gem('amber',0.043,loc=(0.027,-0.01,0.75),rot=(90,0,0),color='#8cce65'))
    for s in (-1,1):
        p.append(prong('twig',[(0,0,0.58),(s*0.05,0.01,0.63),(s*0.1,0.015,0.68)],W.WOOD_DK,0.013))
        p.append(A.extrude_shape('leaf',[(0,0),(0.025,0.035),(0.018,0.065),(-0.014,0.04)],depth=0.006,
                                  loc=(s*0.075,0.012,0.62),rot=(0,0,s*25),color='#64a954'))
    p.append(W.helix('wood_grain',0.13,0.56,0.021,2.3,radius=0.002,color=W.WOOD_DK))
    return W.finalize(p,'staff_oak')


def staff_crystal():
    p=shaft_parts(0.67,W.SILVER,'#345578','#213952')
    p.append(W.crystal('ice_focus',0.072,0.22,loc=(0,0,0.73),color='#84dbff'))
    # Four split silver claws cradle the crystal; a secondary crystal cluster at its base.
    for i in range(4):
        a=i*math.pi/2
        path=[(0,0,0.63),(0.076*math.cos(a),0.076*math.sin(a),0.72),
              (0.063*math.cos(a),0.063*math.sin(a),0.85)]
        p.append(prong('silver_claw',path,W.SILVER,0.019))
    for s in (-1,1):
        p.append(W.crystal('small_ice',0.026,0.115,loc=(s*0.085,0,0.70),rot=(0,s*22,0),color='#b6edff'))
    rune_chain(p,0.19,0.57,'#73bfff')
    return W.finalize(p,'staff_crystal')


def staff_ruby():
    p=shaft_parts(0.66,W.GOLD,'#392439','#832237')
    p.append(W.gem('ruby_focus',0.09,h=0.2,loc=(0,0,0.825),color='#ff324b'))
    p.append(A.torus('ruby_crown',R=0.074,r=0.012,loc=(0,0,0.77),color=W.GOLD,seg=24,minor=8))
    for s in (-1,1):
        p.append(prong('flame_fork',[(0,0,0.64),(s*0.11,0,0.71),(s*0.145,0,0.86),
                                    (s*0.10,0,0.96),(s*0.055,0,0.92)],W.GOLD,0.032))
        p.append(prong('black_flame',[(s*0.035,0.02,0.68),(s*0.1,0.025,0.81),
                                     (s*0.075,0.02,0.89)],'#461826',0.018))
    p.append(W.helix('spiral_inlay',0.12,0.62,0.024,4,radius=0.003,color=W.GOLD))
    rune_chain(p,0.20,0.57,'#ff794e',count=5)
    return W.finalize(p,'staff_ruby')


def staff_sage():
    p=shaft_parts(0.65,W.GOLD,'#28305a','#70518c')
    # Open crescent, orbiting pearl, book-like double wing plates.
    outer=[(0.105*math.cos(a),0,0.82+0.105*math.sin(a)) for a in [math.radians(-50+i*10) for i in range(29)]]
    p.append(W.sweep('crescent',outer,lambda t:0.025*math.sin(math.pi*t)+0.002,
                     lambda t:0.013,color=W.GOLD,up=(0,1,0)))
    p.append(A.sphere('sage_orb',r=0.065,loc=(0.008,0,0.82),color='#9781ff',mat='M_Emit',seg=20,rings=12))
    p.append(A.torus('orb_orbit',R=0.087,r=0.005,loc=(0.008,0,0.82),rot=(65,25,0),color=W.SILVER,seg=28,minor=6))
    for s in (-1,1):
        p.append(W.flat_plate_xz('book_wing',[(s*0.015,0.64),(s*0.075,0.67),(s*0.135,0.74),
                                            (s*0.115,0.64),(s*0.04,0.595)],0.018,color=W.GOLD))
        for j in range(3):
            p.append(A.tube('page_engraving',[(s*0.035,-0.012,0.645-j*0.01),
                                            (s*0.105,-0.012,0.692-j*0.01)],radius=0.002,color='#efe1bc',seg=6))
    rune_chain(p,0.17,0.57,'#baa3ff',count=7)
    return W.finalize(p,'staff_sage')


def staff_starlight():
    p=shaft_parts(0.68,W.SILVER,'#e4dff4','#42385d')
    p.append(W.star('astral_star',0.13,0.055,0.042,points=6,loc=(0,0,0.86),color=W.SILVER))
    p.append(W.star('inner_star',0.087,0.038,0.032,points=6,loc=(0,-0.035,0.86),color='#8563de',mat='M_Emit'))
    p.append(front_gem('star_heart',0.86,0.042,'#f4c1ff',y=-0.06))
    p.append(A.torus('astral_halo',R=0.155,r=0.008,loc=(0,0.012,0.86),rot=(90,0,0),color=W.GOLD,seg=40,minor=8))
    for s in (-1,1):
        p.append(prong('lunar_prong',[(0,0,0.65),(s*0.13,0.02,0.73),(s*0.18,0.02,0.88),
                                     (s*0.15,0.02,1.04)],W.SILVER,0.026))
        for j in range(3):
            p.append(W.crystal('satellite',0.014,0.047,loc=(s*(0.105+j*0.022),-0.01,0.71+j*0.055),
                               rot=(0,s*25,0),color='#b899ff'))
    p.append(W.helix('astral_wire',0.10,0.63,0.023,5,radius=0.003,color=W.GOLD))
    rune_chain(p,0.16,0.58,'#b4a8ff')
    return W.finalize(p,'staff_starlight')


def mace_wood():
    p=shaft_parts(0.43,W.BRONZE,W.WOOD,W.LEATHER,staff=False)
    p.append(A.lathe('carved_club',[(0.03,0.40),(0.065,0.43),(0.082,0.49),(0.071,0.57),(0.035,0.60)],
                     color=W.WOOD,seg=12))
    for z in (0.44,0.56):
        p.append(W.band('head_iron_band',z,0.078,0.023,color=W.IRON_DK,seg=12))
    for i in range(6):
        a=math.pi*i/3
        p.append(A.tube('carved_groove',[(0.078*math.cos(a),0.078*math.sin(a),0.465),
                                       (0.075*math.cos(a),0.075*math.sin(a),0.545)],radius=0.0025,color=W.WOOD_DK,seg=6))
    return W.finalize(p,'mace_wood')


def mace_silver():
    p=shaft_parts(0.45,W.SILVER,'#647389','#364766',staff=False)
    p.append(A.sphere('core',r=0.066,loc=(0,0,0.52),scale=(1,1,1.2),color=W.STEEL_DK,seg=16,rings=10))
    for i in range(6):
        fin=W.flat_plate_xz('flange',[(0.018,0.43),(0.085,0.45),(0.105,0.53),(0.075,0.59),(0.018,0.59)],0.018,color=W.SILVER,bevel=0.003)
        fin.rotation_euler.z=i*math.pi/3
        p.append(fin)
    p.append(W.crystal('top_spike',0.032,0.075,loc=(0,0,0.59),color=W.SILVER,mat='M_Toon'))
    p.append(front_gem('silver_sapphire',0.52,0.025,'#73c3ff',y=-0.075))
    return W.finalize(p,'mace_silver')


def mace_blessed():
    p=shaft_parts(0.45,W.GOLD,'#e8e2d5','#426292',staff=False)
    p.append(A.sphere('blessed_core',r=0.07,loc=(0,0,0.55),color='#b1d9ff',mat='M_Emit',seg=20,rings=12))
    for i in range(4):
        fin=W.flat_plate_xz('petal_flange',[(0.015,0.44),(0.055,0.465),(0.105,0.54),(0.08,0.62),(0.015,0.65)],0.019,color=W.GOLD,bevel=0.003)
        fin.rotation_euler.z=i*math.pi/2
        p.append(fin)
    p.append(A.box('holy_cross_v',(0.022,0.018,0.11),loc=(0,-0.081,0.55),color=W.WHITE,bevel=0.003))
    p.append(A.box('holy_cross_h',(0.077,0.018,0.02),loc=(0,-0.081,0.566),color=W.WHITE,bevel=0.003))
    p.append(W.star('cap_star',0.03,0.012,loc=(0,0,0.66),color=W.GOLD_HI))
    rune_chain(p,0.17,0.39,'#eacb73',count=4)
    return W.finalize(p,'mace_blessed')


def wing(p,s,z,metal,rows=3):
    for j in range(rows):
        p.append(W.flat_plate_xz('feather',[(s*0.035,z-0.055+j*0.025),(s*(0.105+j*0.028),z+0.012+j*0.03),
                                           (s*(0.13+j*0.024),z+0.065+j*0.03),(s*0.067,z+0.015+j*0.025)],
                                 0.018,y=0.012*j,color=metal,bevel=0.003))


def mace_saint():
    p=shaft_parts(0.46,W.GOLD,W.WHITE,'#52639c',staff=False)
    p.append(W.crystal('saint_diamond',0.065,0.18,loc=(0,0,0.53),color='#9ad8ff'))
    for s in (-1,1): wing(p,s,0.51,W.SILVER,3)
    p.append(A.torus('saint_halo',R=0.12,r=0.008,loc=(0,0.025,0.59),rot=(90,0,0),color=W.GOLD,seg=32,minor=8))
    p.append(front_gem('saint_seal',0.485,0.029,'#48a4ff',y=-0.045))
    p.append(W.helix('shaft_filigree',0.10,0.43,0.022,3,radius=0.0028,color=W.GOLD))
    return W.finalize(p,'mace_saint')


def mace_dawn():
    p=shaft_parts(0.46,W.GOLD_HI,W.WHITE,'#cc9350',staff=False)
    p.append(W.crystal('dawn_focus',0.071,0.22,loc=(0,0,0.55),color='#d9f4ff'))
    for s in (-1,1): wing(p,s,0.54,W.GOLD,4)
    p += W.rays('sun_ray',12,0.096,0.165,0.016,0.018,z=0.61,y=0.04,color=W.GOLD_HI,alt=0.132)
    p.append(A.torus('sun_ring',R=0.107,r=0.009,loc=(0,0.03,0.61),rot=(90,0,0),color=W.GOLD,seg=32,minor=8))
    p.append(front_gem('dawn_seal',0.49,0.034,'#ffb94c',y=-0.05))
    p.append(W.helix('gold_script',0.10,0.43,0.023,4,radius=0.003,color=W.GOLD))
    rune_chain(p,0.18,0.39,'#ffd472',count=4)
    p.append(W.gem('pommel_gem',0.024,loc=(0,0,-0.145),rot=(180,0,0),color='#83dfff'))
    return W.finalize(p,'mace_dawn')


BUILDERS=[('staff_oak',staff_oak),('staff_crystal',staff_crystal),('staff_ruby',staff_ruby),
          ('staff_sage',staff_sage),('staff_starlight',staff_starlight),('mace_wood',mace_wood),
          ('mace_silver',mace_silver),('mace_blessed',mace_blessed),('mace_saint',mace_saint),('mace_dawn',mace_dawn)]
