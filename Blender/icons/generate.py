"""22 status, eight element, twelve command emblems, facing local -Y.
Embossed symbol geometry (not text or textures), readable independent of colour.
"""
import os
import sys
import math
import json
sys.path.insert(0,os.path.join(os.path.dirname(__file__),'..','town'))
from _common import MB,T,RX,RY,RZ,S,A

GOLD='#e8bc6a'
INK='#303449'
PALE='#fff0c7'


def poly(m,pts,col=PALE,y=-.09,depth=.07):
    m.slab(pts,depth,col,y=y)


def line(m,pts,col=PALE,r=.025,y=-.13):
    m.tube([(x,y,z) for x,z in pts],r,col,seg=7)


def ring(m,x,z,r=.18,col=PALE,y=-.12,thick=.028):
    m.torus(r,thick,(x,y,z),col,m=RX(90),seg=24,minor=6)


def star(m,x=0,z=0,r=.3,col=PALE,n=5):
    pts=[]
    for i in range(n*2):
        a=math.pi/2+i*math.pi/n; rr=r if i%2==0 else r*.43
        pts.append((x+math.cos(a)*rr,z+math.sin(a)*rr))
    poly(m,pts,col)


def sword(m,col=PALE,angle=0):
    with m.at(RY(angle)):
        poly(m,[(-.045,-.21),(.045,-.21),(.06,.22),(0,.39),(-.06,.22)],col)
        poly(m,[(-.16,-.21),(.16,-.21),(.16,-.15),(-.16,-.15)],GOLD,y=-.14)
        line(m,[(0,-.23),(0,-.36)],GOLD,.04)
        ring(m,0,-.39,.035,GOLD)


def shield(m,col=PALE,double=False):
    pts=[(-.26,.27),(.26,.27),(.24,-.08),(.13,-.27),(0,-.38),(-.13,-.27),(-.24,-.08)]
    poly(m,pts,col)
    poly(m,[(x*.7,z*.7) for x,z in pts],INK,y=-.18)
    if double:
        line(m,[(-.11,-.08),(0,.05),(.11,-.08)],GOLD,y=-.25)
        line(m,[(-.11,.07),(0,.2),(.11,.07)],GOLD,y=-.25)
    else:
        line(m,[(0,-.19),(0,.15)],GOLD,y=-.25)
        line(m,[(-.12,0),(.12,0)],GOLD,y=-.25)


def arrow(m,up,col=PALE,x=.28):
    sign=1 if up else -1
    poly(m,[(x-.045,-.29*sign),(x+.045,-.29*sign),(x+.045,.12*sign),(x+.13,.12*sign),(x,.3*sign),(x-.13,.12*sign),(x-.045,.12*sign)],col,y=-.25)


def drop(m,col=PALE,x=0,z=0,scale=1):
    pts=[(0,.35),(.12,.15),(.2,-.05),(.16,-.23),(0,-.3),(-.16,-.23),(-.2,-.05),(-.12,.15)]
    poly(m,[(x+px*scale,z+pz*scale) for px,pz in pts],col)


def flame(m,col=PALE):
    poly(m,[(0,-.34),(-.23,-.22),(-.26,-.04),(-.17,.17),(-.13,.04),(-.02,.37),(.10,.15),(.16,.21),(.26,-.05),(.20,-.23)],col)
    poly(m,[(-.1,-.21),(-.07,-.08),(0,.14),(.09,-.08),(.1,-.21),(0,-.29)],'#ffd16e',y=-.18)


def snow(m,col=PALE,ice=False):
    for a in range(0,180,60):
        with m.at(RY(a)):
            line(m,[(0,-.35),(0,.35)],col,.025)
            for s in (-1,1):
                line(m,[(-.1,.17*s),(0,.25*s),(.1,.17*s)],col,.023)
    if ice:
        poly(m,[(-.07,-.08),(-.13,.03),(0,.18),(.13,.03),(.07,-.08)],'#80d9f2',y=-.17)


def lightning(m,col=PALE):
    poly(m,[(.08,.38),(-.24,.01),(-.04,.01),(-.09,-.37),(.25,.10),(.04,.10)],col)


def eye(m,closed=False,col=PALE):
    pts=[(-.34,0),(-.21,.15),(0,.21),(.21,.15),(.34,0),(.21,-.15),(0,-.21),(-.21,-.15)]
    poly(m,pts,col)
    ring(m,0,0,.11,INK,y=-.19,thick=.038)
    if closed: line(m,[(-.28,-.27),(.28,.27)],'#e37e8d',.043,y=-.26)


def skull(m,strong=False):
    poly(m,[(-.22,-.08),(-.28,.08),(-.23,.27),(0,.35),(.23,.27),(.28,.08),(.22,-.08),(.14,-.08),(.14,-.25),(-.14,-.25),(-.14,-.08)],PALE)
    for x in (-.105,.105): ring(m,x,.08,.052,INK,y=-.19,thick=.035)
    poly(m,[(-.04,-.03),(0,.04),(.04,-.03)],INK,y=-.19)
    for x in (-.07,0,.07): line(m,[(x,-.14),(x,-.25)],INK,.014,y=-.19)
    if strong:
        for a in (-45,45):
            with m.at(RY(a)): line(m,[(-.29,-.30),(.29,-.30)],'#99e367',.034,y=-.23)


def boot(m,col=PALE):
    poly(m,[(-.2,.26),(.08,.26),(.06,-.06),(.27,-.12),(.31,-.26),(-.19,-.26)],col)
    line(m,[(-.14,.14),(.03,.14)],GOLD,.023,y=-.20)
    line(m,[(-.15,.03),(.02,.03)],GOLD,.023,y=-.20)


def moon(m,col=PALE,x=0,z=0,scale=1):
    pts=[]
    for i in range(17):
        a=math.pi/2+i*math.pi/16
        pts.append((x+.29*math.cos(a)*scale,z+.29*math.sin(a)*scale))
    for i in range(16,-1,-1):
        a=math.pi/2+i*math.pi/16
        pts.append((x+(.12+.19*math.cos(a))*scale,z+.29*math.sin(a)*scale))
    poly(m,pts,col)


def bottle(m):
    poly(m,[(-.09,.31),(.09,.31),(.09,.15),(.19,.02),(.19,-.28),(-.19,-.28),(-.19,.02),(-.09,.15)],PALE)
    poly(m,[(-.12,-.02),(.12,-.02),(.12,-.20),(-.12,-.20)],'#7fd49b',y=-.19)
    line(m,[(-.08,.31),(.08,.31)],GOLD,.04,y=-.2)


def glyph(m,name):
    if name in ('attack','slash','attack_up','attack_down','attack_up_berserk'):
        sword(m,angle=-24 if name=='slash' else 0)
        if name in ('attack_up','attack_down'): arrow(m,name=='attack_up','#91e3ab' if name=='attack_up' else '#f89591')
        if name=='attack_up_berserk':
            for a in (-35,35):
                with m.at(T(0,0,.22)@RY(a)): poly(m,[(-.02,0),(.03,0),(.055,.2),(-.08,.13)],'#f29570',y=-.24)
        if name=='slash': line(m,[(-.31,-.28),(-.18,-.32),(.10,-.12),(.34,.16)],GOLD)
    elif name in ('defense_up','defense_down','defense_up_l','guard','barrier','barrier_abyss'):
        shield(m,'#addef0' if name!='barrier_abyss' else '#b592eb',name=='defense_up_l')
        if name in ('defense_up','defense_down'): arrow(m,name=='defense_up','#91e3ab' if name=='defense_up' else '#f89591')
        if name.startswith('barrier'):
            ring(m,0,0,.39,'#a5dcec' if name=='barrier' else '#c399f1',thick=.022)
            if name=='barrier_abyss': moon(m,'#c79cf0',.26,.2,.42)
    elif name in ('bleed','burn','fire'):
        if name=='bleed':
            drop(m,'#fa8f94'); drop(m,'#ffbdc2',.26,-.23,.32)
        else: flame(m,'#f3956f' if name=='burn' else '#ffb071')
    elif name=='blind': eye(m,True)
    elif name in ('freeze','ice'): snow(m,ice=name=='freeze')
    elif name in ('magic_up','skill'):
        star(m,r=.22,col='#bdd2ff',n=4)
        ring(m,0,0,.33,GOLD,thick=.018)
        if name=='magic_up': arrow(m,True,'#b3a0f0',x=.31)
        else:
            for a in (0,120,240):
                rad=math.radians(a); star(m,.3*math.cos(rad),.3*math.sin(rad),.065,GOLD,n=4)
    elif name in ('poison','poison_strong'): skull(m,name=='poison_strong')
    elif name=='provoke':
        poly(m,[(-.1,-.14),(.1,-.14),(.14,.31),(-.14,.31)],'#ffc37d')
        ring(m,0,-.29,.055,'#ffc37d',thick=.025)
        for s in (-1,1): line(m,[(s*.22,-.1),(s*.33,.1),(s*.22,.26)],PALE)
    elif name=='regen':
        poly(m,[(-.07,-.25),(.07,-.25),(.07,-.07),(.25,-.07),(.25,.07),(.07,.07),(.07,.25),(-.07,.25),(-.07,.07),(-.25,.07),(-.25,-.07),(-.07,-.07)],'#9ee7a8')
        ring(m,0,0,.36,GOLD,thick=.018)
    elif name=='silence':
        poly(m,[(-.28,-.03),(-.2,.12),(0,.17),(.2,.12),(.28,-.03),(.14,-.1),(-.14,-.1)],PALE)
        line(m,[(-.21,-.27),(.21,.28)],'#ee8eaa',.04,y=-.23)
    elif name=='sleep':
        moon(m,'#d5c8ff'); star(m,.22,.17,.09,GOLD)
        line(m,[(.06,-.08),(.22,-.08),(.06,-.22),(.22,-.22)],PALE,.021)
    elif name in ('slow','speed_up','flee'):
        boot(m,'#d8d0f2' if name=='slow' else PALE)
        if name=='slow':
            for x in (-.24,-.1): ring(m,x,-.29,.07,INK,y=-.22)
        elif name=='speed_up': arrow(m,True,'#96e5d4')
        else:
            for z in (.2,.04,-.12): line(m,[(-.38,z),(-.25,z)],GOLD)
    elif name=='stun':
        for x,z,r in [(-.21,.14,.12),(.19,.2,.11),(0,-.2,.14)]: star(m,x,z,r,GOLD,n=5)
        ring(m,0,0,.35,PALE,thick=.015)
    elif name=='blunt':
        poly(m,[(-.045,-.35),(.045,-.35),(.045,.12),(-.045,.12)],GOLD)
        poly(m,[(-.27,.10),(.27,.10),(.27,.3),(-.27,.3)],PALE)
        for x in (-.18,.18): line(m,[(x,.1),(x,.3)],GOLD,.026,y=-.19)
    elif name=='pierce':
        poly(m,[(-.028,-.35),(.028,-.35),(.028,.14),(-.028,.14)],GOLD)
        poly(m,[(-.13,.11),(0,.4),(.13,.11),(0,.18)],PALE)
        for s in (-1,1): line(m,[(0,-.19),(s*.12,-.29)],PALE)
    elif name=='thunder': lightning(m,'#ffe48c')
    elif name=='dark':
        moon(m,'#c39bea'); star(m,.2,.09,.12,'#eeceff',n=4)
    elif name=='holy':
        star(m,r=.27,col='#fff1b3',n=4); ring(m,0,0,.35,GOLD,thick=.026)
        for a in range(0,360,45):
            rad=math.radians(a); line(m,[(.4*math.cos(rad),.4*math.sin(rad)),(.46*math.cos(rad),.46*math.sin(rad))],GOLD,.015)
    elif name=='ultimate':
        star(m,r=.34,col='#ffd382',n=8); star(m,r=.17,col=INK,n=4)
    elif name=='item': bottle(m)
    elif name=='auto':
        for a in (0,180):
            with m.at(RY(a)):
                line(m,[(-.27,0),(-.21,.22),(0,.3),(.25,.2)],PALE,.03)
                poly(m,[(.25,.32),(.35,.10),(.12,.12)],GOLD)
        poly(m,[(-.07,-.13),(.14,0),(-.07,.13)],'#9ee0bd',y=-.2)
    elif name=='gold':
        ring(m,0,0,.29,GOLD,thick=.05)
        poly(m,[(-.065,-.19),(.065,-.19),(.12,0),(.065,.19),(-.065,.19),(-.12,0)],GOLD)
        line(m,[(-.18,-.25),(.17,.25)],'#ffeeb4',.018,y=-.22)
    elif name=='key':
        ring(m,-.1,.15,.14,GOLD,thick=.04)
        line(m,[(-.1,0),(-.1,-.31)],GOLD,.033)
        line(m,[(-.1,-.22),(.13,-.22),(.13,-.12)],GOLD,.033)
    elif name=='map':
        for i,c in enumerate(('#dbd4ae','#f5e5bd','#d9c5a1')):
            poly(m,[(-.32+i*.21,-.26),(-.11+i*.21,-.19),(-.11+i*.21,.29),(-.32+i*.21,.22)],c)
        line(m,[(-.25,-.13),(-.07,.05),(.10,-.02),(.23,.19)],'#bd6662',.018,y=-.21)
        star(m,.23,.19,.058,'#bd6662',n=4)
    elif name=='party':
        for x,z,s in [(-.23,-.04,.8),(.23,-.04,.8),(0,.06,1)]:
            ring(m,x,z+.18,.067*s,PALE,thick=.035)
            poly(m,[(x-.10*s,z-.20*s),(x+.10*s,z-.20*s),(x+.08*s,z+.07*s),(x-.08*s,z+.07*s)],'#9bcbe0',y=-.16 if x==0 else -.09)
    elif name=='camp':
        poly(m,[(-.34,-.22),(0,.32),(.34,-.22)],'#9acaaf')
        poly(m,[(-.12,-.22),(0,.06),(.12,-.22)],INK,y=-.18)
        line(m,[(-.38,-.25),(.38,-.25)],GOLD)
    else: raise ValueError('No symbol for '+name)


def make(name,category):
    m=MB()
    colors={'Status':'#4a4565','Elements':'#355368','UI':'#37545a'}
    # Different family frames; symbol itself is always distinct and raised.
    if category=='Status':
        poly(m,[(-.48,-.32),(-.48,.32),(-.32,.48),(.32,.48),(.48,.32),(.48,-.32),(.32,-.48),(-.32,-.48)],GOLD,y=.035,depth=.11)
        poly(m,[(-.44,-.30),(-.44,.30),(-.30,.44),(.30,.44),(.44,.30),(.44,-.30),(.30,-.44),(-.30,-.44)],colors[category],y=.012,depth=.05)
    elif category=='Elements':
        poly(m,[(-.49,0),(-.245,.425),(.245,.425),(.49,0),(.245,-.425),(-.245,-.425)],GOLD,y=.035,depth=.11)
        poly(m,[(-.455,0),(-.225,.395),(.225,.395),(.455,0),(.225,-.395),(-.225,-.395)],colors[category],y=.012,depth=.05)
    else:
        ring(m,0,0,.46,GOLD,y=.07,thick=.028)
        m.cyl(.445,.10,(0,.08,0),colors[category],rr=(90,0,0),seg=32)
    glyph(m,name)
    return m.build(name)


def main():
    with open(os.path.join(A.REPO,'Assets','_Game','Resources','Data','statuses.json'),encoding='utf-8') as f: statuses=[s['id'] for s in json.load(f)]
    groups={'Status':statuses,'Elements':['slash','blunt','pierce','fire','ice','thunder','dark','holy'],'UI':['attack','skill','ultimate','item','guard','flee','auto','gold','key','map','party','camp']}
    for category,names in groups.items():
        for name in names:
            A.reset_scene(); obj=make(name,category)
            A.export_fbx('Props/%s/%s.fbx'%(category,name),[obj])
            A.save_blend('emblem_'+category.lower()+'_'+name)
            A.render_preview('emblem_'+category.lower()+'_'+name,[obj],angle=(90,0,0),size=384)
    print('EMBLEMS_COMPLETE status=%d elements=8 ui=12'%len(statuses),flush=True)

if __name__=='__main__': main()
