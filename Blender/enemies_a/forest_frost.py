"""Forest/frost species from the original forest__sheet and frost__sheet references.
Mushroom poison monarch, bat lord and crypt bat are sculptural variants, not tints.
"""
import math
import os
import sys
sys.path.insert(0,os.path.dirname(__file__))
from creature_kit import Creature, A
from mathutils import Vector


def mushroom(eid):
    c=Creature(eid); elite=eid.startswith('elite_')
    c.bone('body',(0,0,.3));c.bone('head',(0,0,.6),'body')
    c.bone('crest',(0,0,.85),'head');c.bone('eyes',(0,-.285,.553),'head')
    c.orb('body','plump_stem',(0,0,.43),(.28,.23,.39),'#efdaa8')
    c.orb('body','belly',(0,-.197,.42),(.20,.055,.25),'#fff0c3')
    c.orb('head','dark_face',(0,-.230,.566),(.18,.048,.078),'#664937')
    c.eyes('eyes',(0,-.285,.553),.087,.033,'#c9ff6a' if elite else '#ffe24a')
    # Wide domed cap, thick curled rim and radial under-cap gills.
    capcolor='#863cb3' if elite else '#e34b3c'
    c.add('crest',A.lathe('mushroom_cap',[(0,.93),(.13,.92),(.29,.85),(.39,.76),(.44,.65),(.40,.61),(.30,.64),(.13,.70),(0,.70)],color=capcolor,seg=32))
    c.ring('crest','cap_rim',(0,0,.635),.407,.031,'#e3bd9b',scale=(1,1,.7))
    for i in range(18):
        ang=math.tau*i/18
        c.tube('crest',f'gill{i}',[(.10*math.cos(ang),.10*math.sin(ang),.69),(.29*math.cos(ang),.29*math.sin(ang),.65),(.39*math.cos(ang),.39*math.sin(ang),.632)],.008,'#9e6d78')
    for i in range(13):
        ang=math.tau*i*.382
        r=.12+.20*((i%4)/3)
        # Match the actual dome profile and orient each spot along its surface normal.
        if r <= .13:
            z, slope = .93-r*.01/.13, .01/.13
        elif r <= .29:
            z, slope = .92-(r-.13)*.07/.16, .07/.16
        else:
            z, slope = .85-(r-.29)*.09/.10, .09/.10
        normal = Vector((slope*math.cos(ang), slope*math.sin(ang), 1)).normalized()
        center = Vector((r*math.cos(ang), r*math.sin(ang), z)) + normal*.006
        spot = c.orb('crest',f'cap_spot{i}',center,(.045+(i%3)*.018,.045+(i%3)*.018,.012),'#f8e3b3',seg=14,rings=6)
        spot.rotation_euler = normal.to_track_quat('Z','Y').to_euler()
    for s,side in ((-1,'R'),(1,'L')):
        c.bone('arm.'+side,(s*.23,0,.51),'body');c.bone('leg.'+side,(s*.14,0,.2),'body')
        c.orb('arm.'+side,'arm'+side,(s*.29,0,.40),(.11,.12,.17),'#dfc9a1')
        c.orb('arm.'+side,'shoulder_cap'+side,(s*.30,0,.52),(.15,.13,.07),capcolor)
        c.orb('leg.'+side,'foot'+side,(s*.16,-.08,.075),(.115,.16,.075),'#c6aa83')
        for j in range(3):
            x=s*.16+(j-1)*.06
            c.spike('leg.'+side,f'toe{side}{j}',(x,-.17,.055),(x,-.235,.027),.027,'#765037')
        for j in range(2):
            c.spike('arm.'+side,f'finger{side}{j}',(s*(.27+j*.055),-.065,.32),(s*(.27+j*.055),-.11,.25),.025,'#765037')
    for i in range(15):
        z=.28+.27*((i%5)/4);ang=-math.pi/2+(i//5-1)*.45
        c.orb('body',f'stem_freckle{i}',(.25*math.cos(ang),.26*math.sin(ang),z),(.014,.009,.021),'#bf986f',seg=8,rings=6)
    if elite:
        c.crown('crest',.94,.16)
        for s in (-1,1):
            # Secondary poisonous caps form a royal shoulder mantle.
            c.orb('body','poison_pod'+str(s),(s*.25,.14,.69),(.13,.13,.13),'#a14fbe')
            c.orb('body','pod_eye'+str(s),(s*.25,.025,.72),(.035,.016,.04),'#b8ff62','M_Emit',seg=12,rings=6)
        for i in range(6):
            ang=math.tau*i/6
            c.tube('crest',f'poison_drip{i}',[(.4*math.cos(ang),.4*math.sin(ang),.67),(.42*math.cos(ang),.42*math.sin(ang),.55)],.018,'#a7ee56','M_Emit',taper=.35)
        c.ring('body','royal_collar',(0,0,.59),.24,.038,'#6d308a')
    return c.finish()


def bat(eid):
    c=Creature(eid); elite=eid=='elite_bat';grave=eid=='grave_bat'
    fur='#647079' if grave else '#4d2c79';mem='#78a196' if grave else '#a34e9b'
    c.bone('body',(0,0,.72));c.bone('head',(0,0,.95),'body');c.bone('eyes',(0,-.20,1.0),'head');c.bone('jaw',(0,-.14,.86),'head')
    c.orb('body','bat_torso',(0,0,.76),(.16,.12,.24),fur)
    c.orb('head','large_bat_head',(0,-.015,1.0),(.235,.17,.195),fur)
    c.eyes('eyes',(0,-.173,1.025),.102,.046,'#9bffe4' if grave else '#ffdc49',angry=elite)
    c.mouth('jaw',(0,-.191,.897),.067,True)
    c.orb('head','nose',(0,-.202,.963),(.045,.029,.028),'#d693b0')
    c.orb('body','cream_ruff',(0,-.035,.84),(.23,.13,.12),'#d8c5b0')
    for i in range(11):
        ang=math.tau*i/11
        c.spike('body',f'ruff_point{i}',(.16*math.cos(ang),.095*math.sin(ang),.84),(.26*math.cos(ang),.13*math.sin(ang),.77),.041,'#e6d5bc')
    for s,side in ((-1,'R'),(1,'L')):
        c.shape('head','ear'+side,[(-.075,0),(-.06,.19),(.01,.34),(.075,.09),(.07,0)],(s*.165,0,1.13),fur,depth=.06)
        c.shape('head','inner_ear'+side,[(-.042,.04),(-.03,.17),(.01,.28),(.045,.09)],(s*.165,-.036,1.13),'#c47e9f',depth=.01)
        c.bone('wing.'+side,(s*.14,0,.87),'body')
        # Scalloped membranes: fingers meet distinct concave trailing lobes.
        pts=[(.0,.0),(.25,.22),(.60,.44),(.56,.20),(.64,-.12),(.51,-.02),(.40,-.16),(.33,-.36),(.24,-.23),(.12,-.29),(.08,-.11)]
        c.shape('wing.'+side,'membrane'+side,[(s*x,z) for x,z in pts],(s*.14,.025,.87),mem,depth=.023)
        origin=(s*.14,-.005,.87)
        for j,(x,z) in enumerate(((.60,.44),(.64,-.12),(.33,-.36),(.12,-.29))):
            c.tube('wing.'+side,f'finger{side}{j}',[origin,(s*.37,-.008,1.02),(s*(.14+x),-.005,.87+z)],.014,fur,taper=.5)
        c.orb('wing.'+side,'thumb'+side,(s*.40,-.02,1.08),(.038,.034,.052),fur,seg=12,rings=8)
        c.spike('wing.'+side,'thumbclaw'+side,(s*.40,-.025,1.10),(s*.42,-.04,1.17),.016,'#efe4d2')
        c.bone('leg.'+side,(s*.09,0,.60),'body')
        c.tube('leg.'+side,'leg'+side,[(s*.09,0,.6),(s*.12,-.02,.45)],.032,fur)
        for j in range(3):c.spike('leg.'+side,f'footclaw{side}{j}',(s*.12+(j-1)*.022,-.02,.46),(s*.12+(j-1)*.03,-.075,.39),.012,'#d8ccbd')
    if elite:
        c.crown('head',1.20,.17)
        c.orb('body','ruby_clasp',(0,-.169,.79),(.055,.02,.07),'#c7335d','M_Emit',seg=12,rings=8)
        c.shape('body','lord_cape',[(-.20,.1),(-.26,-.31),(-.12,-.24),(0,-.36),(.12,-.24),(.26,-.31),(.20,.1)],(0,.12,.82),'#5a173b',depth=.025)
        for s,side in ((-1,'R'),(1,'L')):
            for j in range(3):c.spike('wing.'+side,f'lord_wingspur{side}{j}',(s*(.39+j*.13),.018,1.15+j*.07),(s*(.39+j*.14),.01,1.27+j*.09),.021,'#d1ac53')
    if grave:
        c.orb('head','skull_mask',(0,-.178,1.0),(.18,.035,.145),'#d9d5bc')
        # Eyes sit outside the bone mask rather than hidden in it.
        c.eyes('eyes',(0,-.215,1.025),.092,.039,'#b3ffe1')
        c.shape('head','skull_nose',[(-.026,0),(0,.035),(.026,0)],(0,-.222,.972),'#2d4441',depth=.009)
        for j in range(5):c.box('head',f'mask_tooth{j}',((j-2)*.034,-.215,.89),(.023,.014,.033),'#eee9d3',bevel=.003)
        for s,side in ((-1,'R'),(1,'L')):
            for j in range(3):c.tube('wing.'+side,f'exposed_wingbone{side}{j}',[(s*.4,-.016,1.01),(s*(.46+j*.12),-.02,.92-j*.1)],.018,'#d3d2b5',taper=.75)
        c.ring('body','crypt_chain',(0,0,.76),.17,.012,'#8e9b9d',scale=(1,.7,1))
    return c.finish('fly')


def jellyfish(eid):
    c=Creature(eid)
    c.bone('body',(0,0,1.05));c.bone('eyes',(0,-.26,1.13),'body');c.bone('crest',(0,0,1.3),'body')
    c.add('body',A.lathe('clear_bell',[(0,1.44),(.16,1.42),(.28,1.33),(.34,1.18),(.35,1.05),(.31,1.0),(.23,1.04),(0,1.06)],color='#5cd9ee',mat='M_Clear',seg=32))
    c.orb('body','visible_jelly_core',(0,0,1.18),(.16,.15,.13),'#51a3e9','M_Emit')
    c.eyes('eyes',(0,-.302,1.22),.10,.044,'#29395d')
    c.mouth('body',(0,-.34,1.08),.055)
    for i in range(10):
        ang=math.tau*i/10
        c.orb('body',f'bell_scallop{i}',(.29*math.cos(ang),.29*math.sin(ang),1.055),(.085,.085,.055),'#9cefff','M_Clear',seg=14,rings=8)
    for i in range(8):
        ang=math.tau*i/8;x=.15*math.cos(ang);y=.15*math.sin(ang)
        b='tentacle'+str(i);c.bone(b,(x,y,1.04),'body')
        pts=[(x,y,1.04),(x*1.25,y*1.25,.82),(x*1.55+.05*math.sin(ang),y*1.5,.57),(x*1.45+.09,y*1.6,.34),(x*1.9+.1,y*1.8,.20)]
        c.tube(b,'jelly_tendril'+str(i),pts,.023,'#6adfed','M_Clear',taper=.2)
        if i%2==0:
            c.tube(b,'frilled_arm'+str(i),[(x,y,1.0),(x*2,y*2,.84),(x*2.3,y*2,.62),(x*1.7,y*1.8,.47)],.055,'#93f0fa','M_Clear',taper=.25)
            for j in range(4):c.orb(b,f'ruffle{i}_{j}',(x*(1.5+j*.2),y*(1.4+j*.2),.88-j*.09),(.065,.045,.05),'#b7faff','M_Clear',seg=12,rings=6)
    for i in range(6):
        ang=math.tau*i/6
        c.orb('crest',f'floating_waterdrop{i}',(.43*math.cos(ang),.43*math.sin(ang),1.13+.22*math.sin(ang*2)),(.034,.033,.048),'#b6f8ff','M_Clear',seg=12,rings=8)
    return c.finish('jelly')


def penguin(eid):
    c=Creature(eid)
    c.bone('body',(0,0,.4));c.bone('head',(0,-.025,.75),'body');c.bone('eyes',(0,-.24,.79),'head');c.bone('crest',(0,0,.91),'head')
    c.orb('body','penguin_body',(0,0,.41),(.28,.23,.36),'#233c78')
    c.orb('body','cream_bib',(0,-.17,.42),(.23,.11,.30),'#fff0c9')
    c.orb('head','penguin_head',(0,-.018,.78),(.245,.21,.23),'#283f87')
    c.orb('head','face_patch',(0,-.19,.79),(.19,.048,.155),'#fff4d6')
    c.eyes('eyes',(0,-.235,.835),.092,.046,'#172c56')
    c.shape('head','upper_beak',[(-.065,0),(0,.065),(.065,0),(0,-.03)],(0,-.269,.756),'#f6b72a',depth=.085)
    c.mouth('head',(0,-.276,.716),.041)
    c.add('crest',A.lathe('wizard_hat',[(.31,.91),(.285,.96),(.22,1.03),(.16,1.21),(.09,1.39),(0,1.48)],color='#2d589d',seg=24))
    c.ring('crest','white_hat_fur',(0,0,.947),.282,.042,'#f8eddf')
    c.tube('crest','hat_curl',[(0,0,1.38),(.08,.025,1.46),(.15,.045,1.43),(.18,.05,1.36)],.054,'#2d589d',taper=.3)
    # Embroidered snowflakes are visible geometry, not a texture dependency.
    for z,x in ((1.11,.09),(1.27,-.03)):
        y=-.18 if z<1.2 else -.10
        for j in range(3):
            ang=math.pi*j/3
            c.tube('crest',f'hat_snowflake{z}_{j}',[(x-.042*math.cos(ang),y,z-.042*math.sin(ang)),(x+.042*math.cos(ang),y,z+.042*math.sin(ang))],.006,'#95edff','M_Emit')
    c.shape('body','cape',[(-.32,.22),(-.35,-.30),(-.23,-.25),(0,-.34),(.23,-.25),(.35,-.30),(.32,.22)],(0,.10,.63),'#315691',depth=.05)
    c.ring('body','cape_fur',(0,0,.68),.25,.034,'#fff1df',scale=(1,.8,1))
    c.orb('body','brooch',(0,-.265,.65),(.067,.024,.079),'#57dafa','M_Emit',seg=12,rings=8)
    for s,side in ((-1,'R'),(1,'L')):
        c.bone('arm.'+side,(s*.24,0,.57),'body');c.bone('leg.'+side,(s*.15,0,.12),'body')
        c.orb('arm.'+side,'flipper'+side,(s*.30,-.015,.46),(.083,.10,.18),'#233c78')
        c.shape('leg.'+side,'webbed_foot'+side,[(-.09,0),(-.11,.05),(-.06,.08),(0,.045),(.07,.08),(.11,.02),(.08,-.02)],(s*.15,-.115,.047),'#f5b42c',depth=.17)
    c.bone('weapon.R',(-.30,-.055,.43),'arm.R');c.bone('weapon.L',(.30,-.055,.43),'arm.L')
    c.tube('weapon.R','twisted_staff',[(-.34,-.08,.12),(-.35,-.08,.66),(-.38,-.06,1.06),(-.32,-.06,1.15)],.028,'#6b4739')
    for j in range(3):c.spike('weapon.R',f'staff_crystal{j}',(-.34+(j-1)*.065,-.06,1.03),(-.34+(j-1)*.10,-.06,1.36-(j%2)*.11),.045,'#8ef2ff','M_Emit')
    return c.finish()

BUILDERS={'mushroom':mushroom,'elite_mushroom':mushroom,'bat':bat,'elite_bat':bat,'grave_bat':bat,'jellyfish':jellyfish,'penguin_mage':penguin}
if __name__=='__main__':
    eid=sys.argv[sys.argv.index('--')+1]
    BUILDERS[eid](eid)
