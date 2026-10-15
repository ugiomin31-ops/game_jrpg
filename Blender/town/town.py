"""Hearthvale: an explorable storybook square with five service porches,
three dwellings, kitchen garden, mountain gate and distant alpine silhouette.
Coordinates and exported markers are documented in town/markers.json.
Service interactions are outdoors; houses are solid, not false empty interiors.
"""
import os
import sys
import math
import random
import json
sys.path.insert(0,os.path.dirname(__file__))
from _common import MB,T,RX,RY,RZ,S,A,col_box,spot,empty,anchor,look_matrix,shot,shade,SPOTS,ANCHORS,COLS
from mathutils import Vector
import bpy

RNG=random.Random(3821)
CREAM='#efd5a5'; WOOD='#77513e'; BEAM='#513a38'; STONE='#9e9d9c'; GOLD='#e3b96c'


def transformed_col(name,size,loc,frame,angle):
    p=frame@Vector(loc)
    return col_box(name,size,p,angle)


def barrel(m,loc,scale=1):
    with m.at(T(*loc)@S(scale)):
        m.lathe([(.26,0),(.30,.1),(.34,.36),(.30,.62),(.26,.70)],col=WOOD,seg=12)
        for z,r in ((.12,.31),(.57,.32)):
            m.cyl(r,.05,(0,0,z),'#606a73',seg=12)
        m.cyl(.25,.025,(0,0,.70),'#bc8e58',seg=12)


def planter(m,x,y,z,length=1.6):
    m.box((length,.45,.35),(x,y,z+.18),'#a96c48')
    m.box((length+.08,.49,.055),(x,y,z+.36),'#d49962')
    for i in range(max(3,int(length*5))):
        px=x-length*.42+i*length*.84/max(1,int(length*5)-1)
        m.tube([(px,y,z+.36),(px,y,z+.63)],.016,'#52815c',seg=5)
        m.ico(.09,(px,y,z+.62),('#efad73','#d97994','#f3d47f')[i%3],sub=1)
        m.ico(.07,(px-.04,y-.05,z+.45),'#75a86b',scale=(1.5,.6,.6))


def lamp(m,x,y):
    m.cyl(.07,2.5,(x,y,1.25),BEAM,seg=10)
    m.cyl(.16,.12,(x,y,.08),STONE,seg=10)
    m.box((.42,.35,.48),(x,y,2.5),'#ffd48a',mat='M_Emit')
    for dx in (-.22,.22):
        for dy in (-.19,.19): m.box((.045,.045,.51),(x+dx,y+dy,2.5),BEAM)
    m.cone(.36,.25,(x,y,2.87),'#416c73',seg=4)
    m.box((.5,.42,.06),(x,y,2.21),BEAM)
    anchor((x,y,2.5),'street')


def tree(m,x,y,size=1):
    with m.at(T(x,y,0)@S(size)):
        m.cyl(.19,1.8,(0,0,.9),WOOD,seg=9,r2=.12)
        m.tube([(0,0,1),(-.5,0,1.9)],.10,WOOD,r_end=.045)
        m.tube([(0,0,1.3),(.5,.2,2.1)],.085,WOOD,r_end=.03)
        for i,(dx,dy,dz,r) in enumerate([(-.6,0,2.3,1),(0,.3,2.65,1.2),(.6,-.15,2.3,.95),(0,-.5,2.3,.9)]):
            m.ico(r,(dx,dy,dz),('#78a967','#92bc73','#5c9765','#a4c279')[i],sub=2,smooth=False,jitter=.1,seed=i+3)


def pine(m,x,y,size=1):
    with m.at(T(x,y,0)@S(size)):
        m.cyl(.17,2.9,(0,0,1.45),WOOD,seg=7)
        for i in range(3):
            m.cone(1.3-i*.29,2.2-i*.35,(0,0,1.9+i*.7),('#456d69','#54816e','#709884')[i],seg=8)


def bench(m,x,y,angle=0):
    with m.at(T(x,y,0)@RZ(angle)):
        for xx in (-.63,.63):
            m.box((.12,.55,.45),(xx,0,.23),BEAM)
            m.box((.1,.10,.84),(xx,.2,.60),BEAM)
        for yy in (-.18,0,.18): m.box((1.65,.14,.08),(0,yy,.49),'#c19464')
        for z in (.72,.94): m.box((1.65,.075,.16),(0,.23,z),'#c19464')
    col_box('Bench_%s_%s'%(x,y),(1.75,.6,1.05),(x,y,.52),angle)


def window(m,x,y,z,w=.75,h=.85):
    m.box((w+.18,.15,h+.18),(x,y,z),BEAM)
    m.box((w,.17,h),(x,y-.03,z),'#739eab')
    m.box((.055,.19,h),(x,y-.04,z),GOLD)
    m.box((w,.19,.055),(x,y-.04,z),GOLD)
    for sx in (-1,1):
        m.box((.24,.16,h+.12),(x+sx*(w*.5+.19),y,z),'#a87552')
        for zz in (-.24,0,.24): m.box((.23,.025,.025),(x+sx*(w*.5+.19),y-.09,z+zz),BEAM)
    m.box((w+.42,.32,.09),(x,y-.09,z-h*.5-.13),WOOD)


def sign(m,kind,x,y,z):
    m.box((.10,.10,.8),(x,y,z+.38),BEAM)
    m.box((.75,.08,.10),(x+.31,y,z+.69),BEAM)
    m.box((.65,.12,.64),(x+.53,y,z+.15),WOOD)
    m.box((.55,.035,.53),(x+.53,y-.09,z+.15),'#e6c28d')
    # Shop-language is an embossed object, not unreadable tiny lettering.
    with m.at(T(x+.53,y-.125,z+.14)):
        if kind=='inn':
            m.slab([(-.18,.12),(.18,.12),(.18,.20),(-.18,.20)],.03,'#547da0',y=-.02)
            m.slab([(-.18,-.14),(-.18,.12),(-.06,.12),(-.06,-.04),(.18,-.04),(.18,-.14)],.03,'#547da0',y=-.02)
        elif kind=='shop':
            m.lathe([(.08,-.19),(.13,-.17),(.13,.02),(.07,.10),(.07,.2)],col='#648c68',seg=10,m=RX(90))
            m.box((.1,.04,.24),(0,-.035,0),'#648c68')
        elif kind=='smith':
            m.box((.08,.05,.36),(0,0,-.03),'#59657a',r=(0,20,0))
            m.box((.33,.07,.14),(.05,0,.15),'#59657a')
        elif kind=='guild':
            m.slab([(-.19,.20),(.19,.20),(.17,-.03),(0,-.21),(-.17,-.03)],.04,'#6a8c9e',y=-.02)
            m.slab([(-.04,-.11),(.04,-.11),(.04,.1),(-.04,.1)],.03,GOLD,y=-.07)
        else:
            m.slab([(-.18,-.13),(0,-.18),(.18,-.13),(.18,.18),(0,.13),(-.18,.18)],.04,'#8a679b',y=-.02)
            m.box((.025,.05,.27),(0,-.06,0),GOLD)


def building(name,x,y,w,d,h,roof,angle=0,kind='home'):
    frame=T(x,y,0)@RZ(angle)
    m=MB()
    with m.at(frame):
        m.box((w+.28,d+.28,.45),(0,0,.225),STONE)
        m.box((w,d,h),(0,0,h*.5+.30),CREAM)
        for xx in (-w*.5+.09,w*.5-.09):
            for yy in (-d*.5+.05,d*.5-.05): m.box((.20,.20,h+.15),(xx,yy,h*.5+.3),BEAM)
        for z in (.48,h*.55+.3,h+.3):
            m.box((w+.15,.17,.17),(0,-d*.5-.045,z),BEAM)
            m.box((w+.15,.17,.17),(0,d*.5+.045,z),BEAM)
        # Gable roof, tiled as readable curved eaves and alternating broad shingles.
        rise=w*.36
        m.slab([(-w*.5-.48,h+.2),(0,h+rise+.40),(w*.5+.48,h+.2)],d+.9,roof,y=-d*.5-.45)
        m.slab([(-w*.5,h+.31),(0,h+rise+.18),(w*.5,h+.31)],.08,CREAM,y=-d*.5-.08)
        m.tube([(-w*.5-.48,-d*.5-.49,h+.21),(0,-d*.5-.49,h+rise+.40),(w*.5+.48,-d*.5-.49,h+.21)],.095,BEAM,seg=6)
        for sx in (-1,1):
            for row in range(6):
                t=(row+.5)/6; xx=sx*(w*.5+.47)*t; zz=h+rise+.4-(rise+.2)*t
                for col in range(max(4,int(d/.55))):
                    yy=-d*.5-.30+col*.55
                    m.box((w/12+.09,.50,.055),(xx,yy,zz+.035),roof if (row+col)%3 else '#b97b69',r=(0,sx*math.degrees(math.atan2(rise+.2,w*.5+.47)),0))
        m.cyl(.12,d+.9,(0,0,h+rise+.41),BEAM,rr=(90,0,0),seg=8)
        m.box((.62,.6,1.7),(w*.27,d*.20,h+rise*.5+.8),'#b3a391')
        m.box((.79,.76,.15),(w*.27,d*.20,h+rise*.5+1.65),BEAM)
        # Covered service porch. Door hinge is a separate mesh origin.
        door=MB()
        with door.at(frame):
            door.box((1.03,.13,1.96),(.015,-d*.5-.11,1.28),'#95623f')
            for dx in (-.36,-.18,0,.18,.36): door.box((.022,.025,1.77),(dx,-d*.5-.19,1.28),BEAM)
            door.box((.95,.04,.07),(.015,-d*.5-.20,.6),BEAM)
            door.box((.95,.04,.07),(.015,-d*.5-.20,1.9),BEAM)
            door.ico(.06,(.35,-d*.5-.24,1.25),GOLD,sub=2)
        hinge=frame@Vector((-.50,-d*.5-.11,.3))
        door.build('Door_'+name,origin=tuple(hinge))
        m.box((1.32,.3,.12),(0,-d*.5-.05,2.34),BEAM)
        for xx in (-.63,.63): m.box((.13,.27,2.2),(xx,-d*.5-.05,1.27),BEAM)
        m.box((2.8,1.75,.10),(0,-d*.5-.80,.05),STONE)
        for xx in (-1.23,1.23):
            m.box((.13,.13,2.45),(xx,-d*.5-1.48,1.28),WOOD)
        m.box((2.95,1.90,.15),(0,-d*.5-.86,2.57),roof,r=(9,0,0))
        for xx in (-w*.29,w*.29):
            window(m,xx,-d*.5-.11,1.65)
            if h>3.8: window(m,xx,-d*.5-.11,3.7,.63,.70)
        if kind!='home': sign(m,kind,w*.5+.18,-d*.5-.22,2.3)
        for xx in (-w*.28,w*.28): planter(m,xx,-d*.5-.42,.45,1.3)
        barrel(m,(w*.5+.48,-d*.20,0),.85)
        if kind=='inn':
            m.box((1.0,.8,.08),(-w*.5-1.0,-d*.5-.9,.82),WOOD)
            m.cyl(.08,.8,(-w*.5-1,-d*.5-.9,.4),BEAM)
            m.lathe([(.0,.86),(.12,.86),(.13,1.08)],loc=(-w*.5-1,-d*.5-.9,0),col='#bb9a6b',seg=10)
        elif kind=='shop':
            m.box((1.7,.8,.65),(-w*.5-1.0,-d*.5+.15,.325),WOOD)
            for i,c in enumerate(('#d65f62','#e7be5e','#88b978')):
                for j in range(4): m.ico(.10,(-w*.5-1.55+i*.48,-d*.5+.05+j*.1,.74),c,sub=2)
            m.box((1.8,1.0,.1),(-w*.5-1,-d*.5+.1,2.05),'#85aaa0')
        elif kind=='smith':
            m.box((.9,.68,.6),(-w*.5-.9,-d*.5-.1,.3),STONE)
            m.box((.82,.52,.22),(-w*.5-.9,-d*.5-.1,.73),'#4a5360')
            m.box((1.2,.38,.16),(-w*.5-.84,-d*.5-.1,.89),'#596573')
            m.cone(.18,.55,(w*.5+.6,-d*.5-.3,.9),'#ffb463',mat='M_Emit',seg=7)
            m.cyl(.44,.55,(w*.5+.6,-d*.5-.3,.3),STONE,seg=10)
            anchor(frame@Vector((w*.5+.6,-d*.5-.3,1.0)),'forge')
        elif kind=='guild':
            m.box((1.1,.10,1.45),(-w*.5-.85,-d*.5-.15,1.1),WOOD)
            for i in range(3): m.box((.24,.025,.37),(-w*.5-1.15+i*.3,-d*.5-.22,1.3),'#ecdbae')
            for i in range(2): m.box((.33,.025,.26),(-w*.5-1.03+i*.43,-d*.5-.22,.81),'#c4d6c0')
        elif kind=='elder':
            m.cyl(.13,2.2,(w*.5+.65,-d*.5-.3,1.1),BEAM,seg=10)
            m.torus(.35,.04,(w*.5+.65,-d*.5-.3,2.18),GOLD,m=RX(90),seg=20)
            m.ico(.16,(w*.5+.65,-d*.5-.3,2.18),'#b3dcce',mat='M_Emit',sub=2)
    m.build('House_'+name)
    transformed_col(name,(w+.25,d+.25,h+1), (0,0,(h+1)*.5),frame,angle)
    # Stalls remain outside the broad central travel routes.
    if kind=='smith': transformed_col(name+'_anvil',(.95,.7,1),(-w*.5-.9,-d*.5-.1,.5),frame,angle)
    if kind=='shop': transformed_col(name+'_stall',(1.7,.8,.8),(-w*.5-1,-d*.5+.15,.4),frame,angle)


def ground():
    m=MB()
    m.box((70,70,.40),(0,0,-.22),'#83a56c')
    m.box((25,25,.06),(0,0,-.005),'#afa79a')
    m.box((5,57,.065),(0,0,-.005),'#b9afa0')
    m.box((49,4,.065),(0,0,-.005),'#b9afa0')
    for ix in range(-15,16):
        for iy in range(-15,16):
            x=ix*.77+(iy%2)*.34; y=iy*.77
            if x*x+y*y<3.3: continue
            m.pillow((.70,.69,.06),(x,y,-.025),('#b8b0a2','#c4b9a9','#a9a59b')[(ix+iy)%3],inset=.25)
    for y in list(range(-28,-12))+list(range(13,29)):
        for x in (-1.6,-.8,0,.8,1.6): m.pillow((.73,.91,.055),(x,y,-.025),'#bdb2a0')
    for x in list(range(-25,-12))+list(range(13,26)):
        for y in (-1.5,-.5,.5,1.5): m.pillow((.90,.89,.055),(x,y,-.025),'#b7afa0')
    # Square edge edging establishes readable pedestrian space.
    for x in (-12.4,12.4):
        for y in range(-12,13): m.pillow((.25,.92,.12),(x,y,0),'#d6c3a1')
    for y in (-12.4,12.4):
        for x in range(-12,13):
            if abs(x)>2: m.pillow((.92,.25,.12),(x,y,0),'#d6c3a1')
    m.build('Ground_CobbledSquare')
    col_box('Ground',(70,70,.4),(0,0,-.23))


def fountain():
    m=MB()
    m.cyl(1.80,.17,(0,0,.08),'#c7bda5',seg=24)
    m.lathe([(1.4,.16),(1.5,.24),(1.5,.62),(1.35,.72),(1.15,.68),(1.15,.28)],col='#a0a6a2',seg=24)
    m.cyl(1.16,.035,(0,0,.54),'#76bac3',seg=24)
    m.lathe([(.45,.18),(.36,.38),(.20,.64),(.22,1.1),(.62,1.18),(.61,1.33),(.16,1.36),(.13,1.96),(.37,2.05),(.35,2.18),(.1,2.21)],col='#d6c5a0',seg=16)
    m.ico(.15,(0,0,2.38),'#a6e4d3',sub=2,mat='M_Emit')
    for i in range(6):
        a=i*math.tau/6
        m.tube([(.34*math.cos(a),.34*math.sin(a),2.07),(.48*math.cos(a),.48*math.sin(a),1.80),(.56*math.cos(a),.56*math.sin(a),1.28)],.019,'#a4dae1')
        m.tube([(.58*math.cos(a),.58*math.sin(a),1.20),(.86*math.cos(a),.86*math.sin(a),1.0),(1.03*math.cos(a),1.03*math.sin(a),.57)],.025,'#a4dae1')
    m.build('Fountain_Hearthwell')
    col_box('Fountain',(3.4,3.4,2.5),(0,0,1.25))


def garden():
    m=MB()
    for x in (-18.8,-15.8,-12.8):
        m.box((2.5,6.5,.12),(x,-19,.04),'#76583c')
        for row in range(7):
            for col in range(3):
                xx=x+(col-1)*.63; yy=-21.7+row*.82
                if x==-18.8:
                    m.ico(.20,(xx,yy,.16),'#8faa6c',sub=2,scale=(1,1,.6))
                    for a in range(3): m.ico(.10,(xx+.08*math.cos(a*2.1),yy+.08*math.sin(a*2.1),.22),'#bac68b',scale=(1.3,.7,.5))
                elif x==-15.8:
                    m.tube([(xx,yy,.1),(xx,yy,.7)],.016,'#657d49')
                    for z in (.35,.55): m.ico(.08,(xx+.09,yy,z),'#ce6860',sub=2)
                    m.ico(.12,(xx,yy,.62),'#7f9e55',scale=(1,1,.35))
                else:
                    m.cone(.06,.24,(xx,yy,.08),'#d99851',seg=8)
                    for a in (-35,0,35): m.tube([(xx,yy,.17),(xx+.1*math.sin(math.radians(a)),yy,.37)],.016,'#729958')
    for x in (-20.7,-11.0):
        for y in range(-23,-14): m.box((.12,.13,.9),(x,y,.45),WOOD)
        for z in (.35,.7): m.box((.1,8.4,.09),(x,-19,z),'#ac8960')
        col_box('GardenSide'+str(x),(.22,9,1),(x,-19,.5))
    for x in (-19,-17,-15,-13,-11): m.box((.12,.13,.9),(x,-23.3,.45),WOOD)
    for z in (.35,.7): m.box((9.7,.1,.09),(-15.9,-23.3,z),'#ac8960')
    col_box('GardenBack',(10,.22,1),(-16,-23.3,.5))
    barrel(m,(-12,-14.8,0),1)
    # A scarecrow: actual prop rather than an NPC stand-in.
    m.cyl(.045,1.9,(-20,-16,.95),WOOD,seg=8)
    m.box((1.0,.08,.08),(-20,-16,1.25),WOOD,r=(0,9,0))
    m.sphere(.20,(-20,-16,1.61),'#caac78',seg=10,rings=6)
    m.cone(.33,.28,(-20,-16,1.91),'#9c754c',seg=10)
    m.lathe([(.29,.57),(.21,1.34),(.1,1.45)],loc=(-20,-16,0),col='#6b8b9b',seg=10)
    m.build('KitchenGarden')


def gate():
    m=MB()
    for x in (-3.75,3.75):
        m.box((2.5,2.8,5.3),(x,28,2.65),'#a9a297')
        m.box((2.9,3.15,.25),(x,28,5.35),'#d5c8ac')
        m.cone(2.3,2.6,(x,28,6.75),'#698ba0',seg=4)
        for z in (.7,1.4,2.1,2.8,3.5,4.2):
            for sx in (-.7,0,.7): m.box((.64,.08,.29),(x+sx,26.56,z),'#bdb2a0')
        window(m,x,26.52,3.4,.45,.8)
        col_box('GateTower'+str(x),(2.6,2.9,5.4),(x,28,2.7))
    m.box((5.4,2.1,.65),(0,28,4.7),'#bfb49d')
    m.slab([(-2.65,4.5),(-2.45,3.35),(-1.8,4.04),(0,4.42),(1.8,4.04),(2.45,3.35),(2.65,4.5)],2.2,'#bfb49d',y=26.9)
    # Raised portcullis never crosses the walking opening.
    for x in (-1.9,-1.27,-.64,0,.64,1.27,1.9): m.box((.06,.07,1.45),(x,27,5.42),'#6a6a74')
    for z in (4.82,5.42,6.02): m.box((4.1,.07,.06),(0,27,z),'#6a6a74')
    for x in (-8,8):
        m.box((6,1.3,2.6),(x,28,1.3),'#9fa293')
        for xx in range(-2,3): m.box((.65,1.4,.5),(x+xx,28,2.84),'#beb8a4')
        col_box('GateWall'+str(x),(6,1.4,3.1),(x,28,1.55))
    for sx in (-1,1):
        m.cyl(.04,2,(sx*3.7,26.35,4.2),GOLD,seg=8)
        m.slab([(sx*3.7,4.2),(sx*3.7+.55,4.2),(sx*3.7+.55,3.3),(sx*3.7+.25,3.12),(sx*3.7,3.3)],.06,'#81669e',y=26.31)
    m.build('Gate_MountainPass')


def scenery():
    m=MB()
    # Soft mountain bowl surrounds the entire playable plateau, not the roads.
    for i in range(17):
        a=math.radians(15+i*12)
        x=70*math.cos(a); y=59*math.sin(a)+12
        height=RNG.uniform(16,30); radius=RNG.uniform(12,18)
        m.cone(radius,height,(x,y,height*.5-2),('#748e94','#80999e','#929ea7')[i%3],seg=6)
        m.cone(radius*.37,height*.31,(x,y,height*.84-2),'#d3ddd4',seg=6)
    for i in range(10):
        x=RNG.choice((-1,1))*RNG.uniform(39,50); y=RNG.uniform(-32,32)
        m.ico(RNG.uniform(6,10),(x,y,1),'#789280',sub=2,scale=(1,1,.65),jitter=.15,seed=i,smooth=False)
    for x,y,s in [(-28,-23,1.2),(-28,-13,1.1),(-26,3,1.25),(-25,18,1.1),(27,-23,1.25),(27,-13,1.1),(26,5,1.25),(26,18,1.2),(-9,24,.9),(9,24,.9),(-7,-23,1.0),(7,-23,.9)]:
        tree(m,x,y,s)
        col_box('Tree_%d_%d'%(x,y),(.55,.55,2.2),(x,y,1.1))
    for i in range(26):
        x=RNG.choice((-1,1))*RNG.uniform(31,42); y=RNG.uniform(-30,41)
        pine(m,x,y,RNG.uniform(1,1.7))
    for x,y in [(-8,-9),(8,-9),(-8,8),(8,8),(-22,8),(22,8)]:
        m.ico(1.1,(x,y,.38),'#648d64',sub=2,scale=(1.3,.65,.5),smooth=False)
        for i in range(6): m.ico(.08,(x+(i-2.5)*.33,y-.3,.68),('#e8c97c','#d6949e')[i%2],sub=1)
    for i in range(50):
        x=RNG.uniform(-31,31); y=RNG.choice((-1,1))*RNG.uniform(25,31)
        for a in (-.1,0,.1): m.tube([(x+a,y,0),(x+a*2,y,.21)],.012,'#b2ba72',seg=4)
    m.build('Scenery_AlpineBowl')
    # Outer perimeter is invisible in FBX and leaves the square/gate freely accessible.
    for name,size,loc in [('West',(1,66,8),(-32,0,4)),('East',(1,66,8),(32,0,4)),('South',(66,1,8),(0,-32,4)),('North',(66,1,8),(0,32,4))]: col_box('Boundary'+name,size,loc)


def wayfinding():
    """A readable town silhouette: service-colour cloth standards and a planted fountain border.
    Posts sit outside the main walkway; cloth stays above head height. No interaction markers move.
    """
    m = MB()
    for x, y, colour in [(-7, -11, '#b76882'), (-7, 12, '#4b9a91'),
                          (7, -11, '#cc865c'), (7, 12, '#628bb3')]:
        m.cyl(.075, 4.6, (x, y, 2.3), '#455562', seg=10)
        m.ico(.14, (x, y, 4.7), GOLD, sub=1)
        m.box((1.25, .075, .075), (x + .48, y, 4.4), GOLD)
        # A folded cloth silhouette with a gold hem. Slabs have thickness and show from both sides.
        for i in range(5):
            xx = x + .08 + i * .22
            yy = y + math.sin(i * .9) * .09
            m.box((.235, .045, 1.35), (xx, yy, 3.69), shade(colour, .9 + i * .025))
            m.box((.235, .052, .055), (xx, yy, 3.05), GOLD)
        m.ico(.15, (x + .52, y - .08, 3.74), '#f1dfb3', sub=1, scale=(1, .3, 1))
        m.cyl(.27, .15, (x, y, .075), STONE, seg=10)
        col_box('Standard_%s_%s' % (x, y), (.3, .3, 4.5), (x, y, 2.25))
    # Two curved flower beds frame the fountain without obstructing the north/south route.
    for side in (-1, 1):
        for i in range(7):
            a = math.radians(-45 + i * 15)
            x, y = side * 2.7 * math.cos(a), 2.7 * math.sin(a)
            m.pillow((.62, .62, .2), (x, y, .08), '#a3a79a', inset=.08)
            m.ico(.23, (x, y, .26), '#547e69', sub=1, scale=(1, 1, .7))
            for dx, dy, c in [(-.12, -.08, '#e5b8b9'), (.12, .08, '#e8d6a3')]:
                m.ico(.07, (x + dx, y + dy, .43), c, sub=1)
    m.build('Square_StandardsAndFlowers')


def markers():
    entries=[
        ('Spot_spawn',(0,-15,0),0),('Spot_innkeeper',(-8,-4,0),90),
        ('Spot_shopkeeper',(-8,8.5,0),90),('Spot_smith',(8,-4,0),-90),
        ('Spot_guild_clerk',(8,9,0),-90),('Spot_elder',(0,15,0),0),
        ('Spot_gate',(0,25,0),180),('Spot_villager_1',(-5,-7,0),-35),
        ('Spot_villager_2',(5,5,0),140),('Spot_villager_3',(-10,-15,0),60)]
    for name,loc,yaw in entries: spot(name,loc,yaw)
    cam=empty('Spot_camera_title',(-27,-36,26),kind='CUBE',size=1,matrix=look_matrix(Vector((-27,-36,26)),Vector((0,5,2))))
    SPOTS[cam.name]=cam
    manifest={
        'asset':'Art/Town/town','units':'metres','blender_axes':'Z-up; humanoid forward -Y',
        'unity_position_mapping':'(Blender x, Blender z, -Blender y)',
        'usage':'Use imported Spot_ transform positions for actors. NPC yaw faces the square. Spot_gate is an interaction anchor, not an obstacle. Title camera target is explicit below; imported Empty camera axes may differ from Unity Camera local axes.',
        'playable_bounds_blender':{'min':[-31.5,-31.5,0],'max':[31.5,31.5,0]},
        'camera_title_target_blender':[0,5,2],'camera_title_target_unity':[0,2,-5],
        'camera_title_lens_mm':30,
        'markers':{},
        'collision':'All Col_ meshes are hidden from Blender renders; Unity strips renderers and creates MeshColliders. Col_Ground top=-0.03m. Houses are solid exterior interaction buildings; central pathways and gate opening are clear.',
        'doors':'Door_<building> meshes use rear-of-door left hinge origins; they are cosmetic service entrances, not entry portals.',
        'light_anchors':[{'name':e.name,'blender_position':list(e.location),'unity_position':[e.location.x,e.location.z,-e.location.y]} for e in ANCHORS],
    }
    for name,e in SPOTS.items():
        q=e.matrix_world.to_quaternion(); p=e.location
        manifest['markers'][name]={'blender_position':list(p),'blender_euler_deg':[math.degrees(v) for v in e.rotation_euler],'blender_quaternion_xyzw':[q.x,q.y,q.z,q.w],'unity_position':[p.x,p.z,-p.y]}
    with open(os.path.join(os.path.dirname(__file__),'markers.json'),'w',encoding='utf-8') as f: json.dump(manifest,f,ensure_ascii=False,indent=2)


def main():
    A.reset_scene(); SPOTS.clear(); ANCHORS.clear(); COLS.clear()
    ground(); fountain()
    building('Inn',-16,-4,7.5,6.0,4.9,'#956779',90,'inn')
    building('Shop',-16,10,6.0,5.5,3.0,'#608985',90,'shop')
    building('Smith',16,-4,6.8,5.8,3.2,'#b57559',-90,'smith')
    building('Guild',16,10,7.3,6.0,4.8,'#67879c',-90,'guild')
    building('Elder',0,21,7.2,5.3,3.6,'#847399',0,'elder')
    building('WillowHome',-24,19,4.5,4.6,2.8,'#a48267',45)
    building('BirchHome',24,20,4.6,4.6,2.9,'#71928b',-45)
    building('RoseHome',18,-20,5.4,4.8,3.0,'#ad7783',-25)
    garden(); gate(); scenery()
    m=MB()
    for x,y in [(-5,-10),(5,-10),(-5,10),(5,10),(-4,22),(4,22),(-4,-22),(4,-22)]: lamp(m,x,y)
    for x,y,a in [(-5,0,90),(5,0,-90),(-5,5,90),(5,-5,-90)]: bench(m,x,y,a)
    for x,y in [(-6,-6),(6,6)]: planter(m,x,y,0,2.1)
    m.build('Square_Furniture')
    wayfinding(); markers()
    objects=[o for o in bpy.context.scene.objects if o.type in ('MESH','EMPTY')]
    A.export_fbx('Town/town.fbx',objects)
    A.save_blend('town')
    A.render_preview('town',angle=(52,0,30),size=1400,dist=190)
    shot('town_square',(-18,-24,17),(0,5,1.6),lens=30,size=(1600,1000))
    shot('town_title',(-27,-36,26),(0,5,2),lens=30,size=(1600,1000))
    shot('town_gate',(0,13,7),(0,28,3.4),lens=28,size=(1280,800))
    shot('town_garden',(-29,-29,11),(-15,-18,1),lens=35,size=(1280,800))
    print('TOWN_COMPLETE markers=%d colliders=%d light_anchors=%d'%(len(SPOTS),len(COLS),len(ANCHORS)),flush=True)

if __name__=='__main__': main()
