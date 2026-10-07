"""Articulated ember/crypt enemies, following the original ember and undead sheets.
Elite drake is a winged wyvern, golem a temple colossus, skeleton an armoured general,
and scarecrow a crowned harvest king with scythe and ragged royal mantle.
"""
import math
import os
import sys
sys.path.insert(0,os.path.join(os.path.dirname(__file__),'..','enemies_a'))
from creature_kit import Creature, A


def drake(eid):
    c=Creature(eid);elite=eid.startswith('elite_')
    red='#a72b32' if elite else '#bc4030';dark='#393038'
    c.bone('body',(0,0,.39));c.bone('head',(0,-.12,.83),'body');c.bone('eyes',(0,-.28,.95),'head');c.bone('jaw',(0,-.22,.77),'head');c.bone('crest',(0,0,1.04),'head')
    c.orb('body','dragon_haunch',(0,.03,.43),(.23,.21,.29),red)
    c.orb('body','cream_belly',(0,-.15,.44),(.16,.085,.26),'#eed4a8')
    for i in range(5):c.tube('body',f'belly_segment{i}',[(-.12,-.197,.31+i*.06),(0,-.231,.31+i*.06),(.12,-.197,.31+i*.06)],.006,'#ac805c')
    c.orb('head','large_drake_head',(0,-.035,.94),(.255,.215,.245),red)
    c.orb('head','dark_brow_mask',(0,-.178,1.003),(.235,.065,.13),dark)
    c.orb('head','muzzle',(0,-.249,.845),(.125,.087,.065),'#ca6950')
    c.eyes('eyes',(0,-.242,.971),.112,.058,'#ffcf45',angry=True)
    for s in (-1,1):c.orb('head','nostril'+str(s),(s*.047,-.327,.857),(.014,.009,.012),dark,seg=10,rings=6)
    c.orb('jaw','lower_jaw',(0,-.228,.765),(.103,.081,.036),'#ead0a5')
    c.mouth('head',(0,-.268,.803),.085,True)
    for s in (-1,1):
        c.tube('crest','curved_horn'+str(s),[(s*.15,.03,1.10),(s*.23,.05,1.27),(s*.25,.08,1.41),(s*.19,.09,1.48)],.055,dark,taper=.06)
        for j in range(4):c.spike('head',f'cheek_scale{s}_{j}',(s*.19,.02,1.03-j*.065),(s*(.32-j*.014),.03,.98-j*.065),.04,'#f58d35' if j%2 else dark)
    for j in range(5):c.spike('crest',f'fire_crest{j}',((j-2)*.04,-.03,1.10),((j-2)*.054,-.04,1.25+(2-abs(j-2))*.035),.035,'#ff9c39','M_Emit')
    for s,side in ((-1,'R'),(1,'L')):
        c.bone('arm.'+side,(s*.19,0,.65),'body');c.bone('leg.'+side,(s*.17,.03,.30),'body')
        c.orb('arm.'+side,'upper_arm'+side,(s*.27,-.04,.60),(.10,.11,.12),red)
        c.orb('arm.'+side,'dragon_hand'+side,(s*.31,-.13,.51),(.10,.10,.09),dark)
        for j in range(3):c.spike('arm.'+side,f'hand_talon{side}{j}',(s*.31+(j-1)*.045,-.18,.51),(s*.31+(j-1)*.05,-.25,.46),.018,'#1d1820')
        c.orb('leg.'+side,'thigh'+side,(s*.19,.02,.23),(.12,.13,.18),red)
        c.orb('leg.'+side,'dragon_foot'+side,(s*.22,-.09,.08),(.13,.18,.08),dark)
        for j in range(3):c.spike('leg.'+side,f'foot_talon{side}{j}',(s*.22+(j-1)*.06,-.20,.08),(s*.22+(j-1)*.065,-.29,.04),.025,'#ddd3bb')
        c.box('leg.'+side,'shin_scale'+side,(s*.22,-.09,.2),(.11,.055,.11),'#dd5a34',bevel=.02)
    c.bone('tail1',(0,.19,.39),'body');c.bone('tail2',(0,.46,.48),'tail1')
    c.tube('tail1','tail_base',[(0,.18,.38),(0,.34,.42),(0,.49,.51)],.10,red,taper=.55)
    c.tube('tail2','tail_tip',[(0,.47,.49),(.08,.62,.68),(.13,.70,.83)],.062,dark,taper=.2)
    for j in range(5):
        c.spike('tail2',f'tail_flame{j}',(.1,.64,.71),(.1+(j-2)*.025,.73+(j%2)*.02,.89+(.1 if j==2 else 0)),.028,'#ff8e27','M_Emit')
    for i in range(4):c.spike('body',f'dorsal_scale{i}',(0,.08+i*.045,.64-i*.055),(0,.10+i*.045,.75-i*.045),.032,dark)
    if elite:
        # Broad membrane wings distinguish the crimson wyvern at battle distance.
        for s,side in ((-1,'R'),(1,'L')):
            c.bone('wing.'+side,(s*.16,.10,.72),'body')
            pts=[(0,0),(.28,.28),(.61,.47),(.52,.14),(.70,-.11),(.46,-.05),(.34,-.24),(.16,-.15)]
            c.shape('wing.'+side,'wyvern_wing'+side,[(s*x,z) for x,z in pts],(s*.16,.13,.72),'#b94243',depth=.028)
            for j,(x,z) in enumerate(((.61,.47),(.70,-.11),(.34,-.24))):c.tube('wing.'+side,f'wing_strut{side}{j}',[(s*.16,.10,.72),(s*.40,.11,.94),(s*(.16+x),.12,.72+z)],.021,dark,taper=.6)
            c.spike('head','royal_horn'+side,(s*.18,.10,1.19),(s*.34,.16,1.55),.051,'#d7ae5c')
        c.orb('body','chest_ember',(0,-.24,.62),(.058,.023,.072),'#ffb93c','M_Emit',seg=12,rings=8)
        for s in (-1,1):c.box('body','black_shoulder'+str(s),(s*.23,0,.73),(.20,.20,.12),dark,bevel=.04)
    return c.finish()


def golem(eid):
    c=Creature(eid);elite=eid.startswith('elite_')
    c.bone('body',(0,0,.45));c.bone('head',(0,0,.87),'body');c.bone('eyes',(0,-.28,.96),'head');c.bone('crest',(0,0,1.12),'head')
    c.orb('body','stone_core',(0,0,.59),(.34,.25,.40),'#876745',seg=16,rings=10)
    def stone(b,n,p,size,color='#d9b77d',rot=(0,0,0)):
        return c.box(b,n,p,size,color,bevel=min(size)*.28,rot=rot)
    stone('body','central_boulder',(0,-.14,.59),(.47,.25,.42),'#e0bd81')
    stone('head','face_recess',(0,-.18,.96),(.36,.16,.16),'#322718')
    for s in (-1,1):stone('head','brow_stone'+str(s),(s*.13,-.07,1.055),(.27,.30,.16),'#e9ce94',rot=(0,s*.18,0))
    c.eyes('eyes',(0,-.271,.958),.09,.041,'#ffdb55')
    stone('head','chin_stone',(0,-.11,.82),(.32,.28,.14))
    c.orb('head','sand_mantle',(0,.015,1.105),(.28,.23,.12),'#e9ce94',seg=16,rings=10)
    for s,side in ((-1,'R'),(1,'L')):
        c.bone('arm.'+side,(s*.30,0,.75),'body');c.bone('leg.'+side,(s*.21,0,.30),'body')
        stone('arm.'+side,'shoulder'+side,(s*.38,0,.73),(.25,.28,.24),'#ac8658')
        stone('arm.'+side,'forearm'+side,(s*.44,-.06,.50),(.24,.25,.30),'#caa570')
        stone('arm.'+side,'massive_fist'+side,(s*.45,-.13,.34),(.28,.29,.24),'#e3c890')
        for j in range(3):stone('arm.'+side,f'knuckle{side}{j}',(s*.45+(j-1)*.073,-.28,.39),(.07,.045,.085),'#f0d79e')
        stone('leg.'+side,'stone_thigh'+side,(s*.21,0,.27),(.23,.23,.26),'#ad8756')
        stone('leg.'+side,'block_foot'+side,(s*.23,-.08,.09),(.27,.31,.17),'#d9b77d')
        for i in range(3):stone('body',f'side_rock{side}{i}',(s*.27,.045,.43+i*.17),(.17,.25,.18),'#c2a16f',rot=(0,s*.2,i*.12))
    for i,(x,y,z) in enumerate(((-.22,.02,1.16),(.20,.05,1.13),(0,.16,1.16))):
        c.add('crest',A.lathe('broken_pot'+str(i),[(.065,0),(.10,.04),(.12,.15),(.085,.22),(.072,.225),(.069,.18)],loc=(x,y,z),color='#a66344',seg=16))
        c.ring('crest','pot_mouth'+str(i),(x,y,z+.22),.081,.012,'#713e2e')
        for j in range(8):
            ang=math.tau*j/8
            c.orb('crest',f'pot_paint{i}_{j}',(x+.112*math.cos(ang),y+.112*math.sin(ang),z+.125),(.014,.014,.009),'#e0c6a1',seg=8,rings=6)
    for i in range(12):
        ang=math.tau*i/12
        stone('body',f'sand_chip{i}',(.28*math.cos(ang),.20*math.sin(ang),.63+(i%3)*.11),(.065,.065,.045),'#e4ce96')
    if elite:
        # Monumental temple shoulders, crown obelisk and sculpted illuminated runes.
        for s,side in ((-1,'R'),(1,'L')):
            stone('arm.'+side,'temple_shoulder'+side,(s*.38,0,.89),(.35,.34,.19),'#6d7f7e')
            c.spike('arm.'+side,'obelisk'+side,(s*.43,.05,.97),(s*.45,.07,1.33),.095,'#b8ac7d')
            c.ring('arm.'+side,'gold_bracer'+side,(s*.44,-.06,.49),.143,.018,'#d9ab4d')
        stone('crest','royal_monolith',(0,.05,1.32),(.16,.18,.44),'#728889')
        c.shape('body','sun_rune',[(-.065,0),(0,.09),(.065,0),(0,-.09)],(0,-.274,.65),'#a6fff5',depth=.009,mat='M_Emit')
        for s in (-1,1):c.tube('body','rune_line'+str(s),[(s*.11,-.275,.72),(s*.15,-.275,.66),(s*.12,-.275,.58)],.010,'#a6fff5','M_Emit')
        for i in range(6):stone('body',f'ancient_skirt{i}',((i-2.5)*.085,-.14,.32),(.075,.14,.17),'#6c7c78')
    return c.finish('heavy')


def phoenix(eid):
    c=Creature(eid)
    c.bone('body',(0,0,.78));c.bone('head',(0,-.08,1.05),'body');c.bone('eyes',(0,-.20,1.11),'head');c.bone('crest',(0,0,1.23),'head');c.bone('tail1',(0,.16,.69),'body')
    c.orb('body','warm_bird_body',(0,0,.82),(.21,.18,.25),'#e96428')
    c.orb('body','yellow_breast',(0,-.13,.84),(.18,.075,.19),'#ffd45d')
    c.orb('head','round_chick_head',(0,-.035,1.12),(.215,.175,.205),'#ffe35e')
    c.eyes('eyes',(0,-.198,1.14),.091,.058,'#76352c')
    c.shape('head','beak',[(-.06,0),(0,.045),(.06,0),(0,-.06)],(0,-.232,1.045),'#743922',depth=.08)
    c.mouth('head',(0,-.245,1.004),.041)
    for i in range(5):
        x=(i-2)*.055
        c.tube('crest',f'flame_crest{i}',[(x,0,1.25),(x*1.2,.01,1.43),(x+.06,.02,1.56-abs(i-2)*.055)],.048,'#ff8a27','M_Emit',taper=.05)
    for s,side in ((-1,'R'),(1,'L')):
        c.bone('wing.'+side,(s*.15,0,.95),'body');c.bone('leg.'+side,(s*.10,0,.64),'body')
        c.orb('wing.'+side,'wing_upper'+side,(s*.26,0,1.0),(.16,.07,.12),'#f29a2c')
        # Overlapping tapered feather silhouettes, dark outer tips and bright inner coverts.
        for j in range(7):
            base=(s*(.22+.035*j),.015,1.03-j*.025)
            tip=(s*(.42+.045*j),.03,1.43-j*.11)
            c.tube('wing.'+side,f'primary{side}{j}',[base,((base[0]+tip[0])*.5,.02,(base[2]+tip[2])*.5),tip],.054,'#3a2731',taper=.05)
            c.tube('wing.'+side,f'feather_flame{side}{j}',[base,(s*(.35+.033*j),-.015,1.27-j*.07)],.043,'#ff8130',taper=.05)
            c.tube('wing.'+side,f'covert{side}{j}',[(s*.20,-.035,.98),(s*(.31+.024*j),-.035,1.16-j*.032)],.031,'#ffe163',taper=.05)
        c.tube('leg.'+side,'bird_leg'+side,[(s*.1,0,.67),(s*.12,-.025,.54)],.023,'#6a3a24')
        for j in range(3):c.tube('leg.'+side,f'talon{side}{j}',[(s*.12,-.025,.54),(s*.12+(j-1)*.035,-.07,.49),(s*.12+(j-1)*.04,-.105,.49)],.012,'#30232a',taper=.25)
    for i in range(5):
        x=(i-2)*.048
        c.tube('tail1',f'tail_plume{i}',[(x,.14,.72),(x*1.6,.32,.67),(x*1.8,.49,.72),(x*2,.60,.83)],.044,'#ee5b2b',taper=.05)
        c.tube('tail1',f'tail_gold{i}',[(x,.21,.70),(x*1.6,.45,.72),(x*1.9,.55,.81)],.024,'#ffc946','M_Emit',taper=.05)
    return c.finish('fly')


def skeleton(eid):
    c=Creature(eid);elite=eid.startswith('elite_');bone='#e8dbc0';dark='#322b33'
    c.bone('body',(0,0,.42));c.bone('head',(0,0,.91),'body');c.bone('eyes',(0,-.17,1.08),'head');c.bone('jaw',(0,-.11,.96),'head');c.bone('crest',(0,0,1.23),'head')
    c.orb('head','oversized_skull',(0,0,1.105),(.23,.19,.225),bone)
    c.eyes('eyes',(0,-.179,1.10),.091,.058,'#ffce46',angry=True,socket=True)
    c.shape('head','nasal_hole',[(-.024,0),(0,.034),(.024,0),(0,-.013)],(0,-.200,1.027),dark,depth=.012)
    c.box('jaw','jaw_bone',(0,-.06,.949),(.27,.21,.083),bone,bevel=.024)
    for i in range(7):c.box('jaw',f'teeth{i}',((i-3)*.031,-.177,.983),(.022,.022,.043),'#fff0d4',bevel=.004)
    c.tube('body','spine',[(0,.03,.42),(0,.03,.87)],.033,bone)
    c.box('body','pelvis',(0,0,.42),(.24,.13,.13),bone,bevel=.045)
    for i in range(5):
        z=.58+i*.055;w=.125-.015*i
        for s in (-1,1):c.tube('body',f'rib{s}_{i}',[(0,.025,z+.025),(s*w,.005,z+.026),(s*w,-.09,z),(s*.042,-.117,z-.017)],.015,bone)
    c.tube('body','sternum',[(0,-.121,.58),(0,-.121,.84)],.025,bone)
    c.ring('body','scarf',(0,0,.91),.13,.044,'#91363f',scale=(1,1,.55))
    c.shape('body','torn_scarf_tail',[(-.06,.1),(-.12,-.18),(-.04,-.13),(0,-.23),(.06,-.16),(.06,.1)],(-.12,.09,.88),'#91363f',depth=.026)
    for s,side in ((-1,'R'),(1,'L')):
        c.bone('arm.'+side,(s*.13,0,.82),'body');c.bone('leg.'+side,(s*.085,0,.40),'body')
        c.tube('arm.'+side,'upper_arm'+side,[(s*.14,0,.82),(s*.24,0,.67)],.029,bone)
        c.orb('arm.'+side,'elbow'+side,(s*.24,0,.66),(.044,.045,.041),bone,seg=12,rings=8)
        for j in (-1,1):c.tube('arm.'+side,'forearm'+side+str(j),[(s*.24+j*.013,0,.66),(s*.27+j*.013,-.10,.56)],.014,bone)
        c.orb('arm.'+side,'hand'+side,(s*.27,-.10,.55),(.051,.035,.044),bone,seg=12,rings=8)
        c.tube('leg.'+side,'femur'+side,[(s*.085,0,.40),(s*.12,0,.26)],.033,bone)
        c.orb('leg.'+side,'knee'+side,(s*.12,0,.24),(.047,.046,.039),bone,seg=12,rings=8)
        for j in (-1,1):c.tube('leg.'+side,'shin'+side+str(j),[(s*.12+j*.015,0,.23),(s*.14+j*.015,-.02,.09)],.017,bone)
        c.ring('leg.'+side,'boot_cuff'+side,(s*.14,-.02,.11),.06,.02,'#664337')
        for j in range(3):c.orb('leg.'+side,f'foot_bone{side}{j}',(s*.14+(j-1)*.035,-.08,.045),(.018,.079,.023),bone,seg=10,rings=6)
    c.bone('weapon.R',(-.27,-.10,.55),'arm.R');c.bone('weapon.L',(.27,-.10,.55),'arm.L')
    c.tube('weapon.R','sword_grip',[(-.27,-.12,.5),(-.27,-.12,.67)],.026,'#60422f')
    c.box('weapon.R','gold_guard',(-.27,-.12,.68),(.20,.055,.036),'#b88e43',bevel=.012)
    c.shape('weapon.R','notched_sword',[(-.046,0),(-.06,.28),(-.034,.30),(-.058,.35),(-.043,.45),(0,.54),(.055,.42),(.032,.39),(.055,.35),(.046,0)],(-.27,-.12,.7),'#b6c1cb',depth=.04)
    c.tube('weapon.R','sword_ridge',[(-.27,-.146,.72),(-.27,-.146,1.18)],.007,'#f0f2df')
    # Shield plane faces forward; metal boss and rim contrast against wood planks.
    c.orb('weapon.L','wooden_shield',(.31,-.15,.64),(.19,.04,.23),'#865b3d',seg=24,rings=12)
    c.ring('weapon.L','shield_rim',(.31,-.187,.64),.195,.014,'#b5b5a7',rot=(90,0,0),scale=(1,1.17,1))
    for x in (-.09,0,.09):c.tube('weapon.L','plank_line'+str(x),[(.31+x,-.190,.48),(.31+x,-.190,.80)],.006,'#543b2e')
    c.orb('weapon.L','shield_boss',(.31,-.199,.64),(.067,.035,.07),'#bac2bd',seg=16,rings=8)
    c.ring('body','belt',(0,0,.47),.14,.022,'#674431',scale=(1,.65,1))
    c.box('body','belt_buckle',(0,-.117,.47),(.074,.035,.057),'#ba944e',bevel=.01)
    if elite:
        c.add('crest',A.lathe('general_helmet',[(.20,1.10),(.24,1.16),(.215,1.30),(.10,1.37),(0,1.39)],color='#536b78',seg=24))
        c.tube('crest','gold_helmet_brow',[(-.20,-.14,1.19),(0,-.22,1.23),(.20,-.14,1.19)],.018,'#d5ad59')
        c.shape('crest','red_plume',[(-.11,0),(-.10,.19),(-.025,.25),(.045,.22),(.12,.08),(.08,0)],(0,.0,1.35),'#a63c47',depth=.055)
        c.shape('body','general_cape',[(-.21,.28),(-.28,-.34),(0,-.41),(.28,-.34),(.21,.28)],(0,.11,.71),'#742937',depth=.035)
        for s,side in ((-1,'R'),(1,'L')):
            c.box('arm.'+side,'pauldron'+side,(s*.17,0,.84),(.22,.22,.13),'#637b89',bevel=.045)
            c.spike('arm.'+side,'pauldron_spike'+side,(s*.21,.02,.89),(s*.27,.02,1.02),.030,'#d9b35c')
            c.box('leg.'+side,'greave'+side,(s*.13,-.032,.17),(.102,.055,.14),'#5c737e',bevel=.02)
        c.box('body','breastplate',(0,-.072,.71),(.22,.10,.23),'#5d7380',bevel=.025)
        c.shape('body','gold_insignia',[(-.036,0),(0,.05),(.036,0),(0,-.05)],(0,-.131,.74),'#ddbc65',depth=.01)
        c.shape('weapon.L','shield_crest',[(-.04,0),(0,.06),(.04,0),(0,-.06)],(.31,-.243,.64),'#eac567',depth=.015)
    return c.finish()


def scarecrow(eid):
    c=Creature(eid);elite=eid.startswith('elite_')
    c.bone('body',(0,0,.45));c.bone('head',(0,0,.98),'body');c.bone('eyes',(0,-.23,1.15),'head');c.bone('crest',(0,0,1.38),'head')
    c.tube('body','wooden_post',[(0,0,.30),(0,0,1.07)],.055,'#6d4a31')
    c.orb('body','burlap_torso',(0,0,.72),(.16,.11,.25),'#b59a70')
    c.shape('body','torn_coat',[(-.20,.25),(-.22,-.10),(-.28,-.33),(-.14,-.22),(-.11,-.40),(0,-.26),(.09,-.38),(.16,-.22),(.25,-.29),(.21,.25)],(0,.02,.73),'#493b4e',depth=.14)
    c.shape('body','burlap_apron',[(-.11,.27),(-.13,-.22),(-.065,-.15),(0,-.27),(.07,-.17),(.13,-.2),(.11,.27)],(0,-.097,.69),'#c3a779',depth=.018)
    c.tube('body','stitched_seam',[(0,-.113,.92),(.015,-.113,.59),(-.013,-.113,.48)],.007,'#664730')
    for i in range(8):c.tube('body',f'stitch{i}',[(-.025,-.119,.54+i*.042),(.030,-.119,.56+i*.042)],.004,'#3d3028')
    # Lobed pumpkin rather than a spherical orange head.
    c.orb('head','pumpkin_core',(0,0,1.15),(.255,.21,.255),'#cf5824')
    for i in range(10):
        ang=math.tau*i/10
        c.orb('head',f'pumpkin_lobe{i}',(.12*math.cos(ang),.10*math.sin(ang),1.15),(.16,.145,.245),'#ed8b2d' if i%2 else '#db6f24',seg=16,rings=12)
    for s in (-1,1):
        c.shape('eyes','cut_eye'+str(s),[(s*-.052,.027),(s*.065,.09),(s*.039,-.042)],(s*.095,-.235,1.15),'#48281c',depth=.018)
        c.shape('eyes','glowing_eye'+str(s),[(s*-.035,.025),(s*.045,.065),(s*.025,-.021)],(s*.095,-.249,1.15),'#ffe879',depth=.010,mat='M_Emit')
    c.shape('head','pumpkin_nose',[(-.025,0),(0,.035),(.025,0)],(0,-.258,1.10),'#4f2b1c',depth=.01)
    teeth=[(-.15,.04),(-.11,.01),(-.075,.035),(-.035,0),(0,.025),(.04,0),(.08,.032),(.12,.005),(.15,.04),(.11,-.047),(.07,-.018),(.025,-.052),(-.02,-.021),(-.06,-.05),(-.105,-.02)]
    c.shape('head','jagged_grin',teeth,(0,-.238,1.025),'#fbd653',depth=.016,mat='M_Emit')
    c.tube('crest','curled_stem',[(0,0,1.38),(.02,.01,1.51),(.08,.01,1.55),(.12,.01,1.51),(.085,.01,1.48)],.026,'#695638',taper=.6)
    c.shape('crest','stem_leaf',[(0,0),(-.08,.05),(-.20,.04),(-.12,-.01),(-.06,-.03)],(0,.02,1.49),'#8a9343',depth=.014)
    c.ring('body','straw_collar',(0,0,.96),.14,.045,'#c9aa65',scale=(1,1,.5))
    for s,side in ((-1,'R'),(1,'L')):
        c.bone('arm.'+side,(s*.14,0,.85),'body');c.bone('leg.'+side,(s*.065,0,.43),'body')
        c.tube('arm.'+side,'branch_arm'+side,[(s*.13,0,.86),(s*.30,.01,.76),(s*.42,-.04,.63)],.027,'#725339',taper=.65)
        c.tube('leg.'+side,'branch_leg'+side,[(s*.06,0,.44),(s*.15,0,.25),(s*.21,-.02,.06)],.030,'#725339',taper=.65)
        for j in range(3):
            c.tube('arm.'+side,f'twig_finger{side}{j}',[(s*.4,-.04,.64),(s*(.43+(j-1)*.04),-.06,.57),(s*(.46+(j-1)*.05),-.08,.54+(j%2)*.03)],.012,'#6c4b32',taper=.15)
            c.tube('leg.'+side,f'root_toe{side}{j}',[(s*.20,-.02,.06),(s*.20+(j-1)*.035,-.12,.025)],.013,'#6c4b32',taper=.12)
        c.ring('arm.'+side,'wrist_rope'+side,(s*.34,-.01,.71),.035,.010,'#cbb576')
        for j in range(7):
            c.spike('arm.'+side,f'wrist_straw{side}{j}',(s*.33+(j-3)*.006,-.015,.73),(s*(.38+j*.011),-.02+(j%2)*.035,.70+(j-3)*.025),.006,'#d3b86a')
            c.spike('body',f'neck_straw{side}{j}',(s*.10,0,.93),(s*(.17+j*.012),.0,.95+(j-3)*.018),.007,'#cfb56e')
    if elite:
        c.crown('crest',1.40,.22,'#ba9147')
        c.shape('body','royal_mantle',[(-.27,.30),(-.35,-.43),(-.16,-.35),(0,-.51),(.16,-.35),(.35,-.43),(.27,.30)],(0,.13,.84),'#70334a',depth=.026)
        c.ring('body','royal_rope',(0,0,.74),.17,.014,'#dcb96b',scale=(1,.65,1))
        c.bone('weapon.R',(-.4,-.04,.65),'arm.R');c.bone('weapon.L',(.4,-.04,.65),'arm.L')
        c.tube('weapon.R','scythe_handle',[(-.44,-.04,.14),(-.44,-.04,1.72)],.023,'#594333')
        c.shape('weapon.R','harvest_scythe',[(0,0),(.05,.05),(.27,.04),(.45,-.08),(.56,-.22),(.36,-.11),(.17,-.045),(.02,-.05)],(-.44,-.04,1.72),'#9aa4ac',depth=.027)
        c.tube('weapon.R','scythe_gold_edge',[(-.40,-.06,1.765),(-.18,-.06,1.75),(.02,-.06,1.64)],.010,'#c3a55b')
        c.orb('head','royal_eye_scar',(.17,-.23,1.2),(.012,.009,.075),'#864020',seg=10,rings=6)
    return c.finish()


def wisp(eid):
    c=Creature(eid)
    c.bone('body',(0,0,.78));c.bone('head',(0,0,.96),'body');c.bone('eyes',(0,-.245,1.0),'head');c.bone('crest',(0,0,1.18),'head');c.bone('tail1',(0,0,.69),'body')
    c.orb('body','spectral_core',(0,0,.94),(.22,.18,.24),'#3230a2','M_Clear')
    for s in (-1,1):
        pts=[(-.045,.05),(.05,.005),(.025,-.045),(-.025,-.024)]
        c.shape('eyes','wicked_eye'+str(s),[(s*x,z) for x,z in pts],(s*.10,-.245,1.00),'#fff2a5',depth=.015,mat='M_Emit')
    c.shape('head','jagged_flame_smile',[(-.12,.025),(-.075,0),(-.035,.025),(0,-.005),(.035,.02),(.08,0),(.12,.04),(.08,-.04),(.04,-.025),(0,-.06),(-.035,-.025),(-.07,-.045)],(0,-.235,.90),'#ffd89d',depth=.01,mat='M_Emit')
    # Curling turquoise flame tongues preserve the ghost/fire silhouette from all angles.
    for i in range(9):
        ang=math.tau*i/9;x=.18*math.cos(ang);y=.14*math.sin(ang)
        c.tube('crest',f'spectral_flame{i}',[(x,y,.89),(x*1.30,y*1.30,1.1),(x*1.05+.055,y*1.05,1.28),(x*.7-.025,y*.7,1.40+(i%3)*.075)],.052,'#49dafa','M_Emit',taper=.025)
    c.tube('crest','highest_flame',[(0,.015,1.1),(.08,.01,1.40),(-.06,.02,1.62),(.05,.03,1.72)],.075,'#5974fb','M_Emit',taper=.01)
    c.tube('tail1','ghost_tail',[(0,0,.77),(-.075,.02,.60),(.06,.03,.44),(-.02,.03,.30)],.092,'#58daff','M_Clear',taper=.03)
    for s,side in ((-1,'R'),(1,'L')):
        c.bone('arm.'+side,(s*.15,0,.84),'body')
        c.tube('arm.'+side,'ghost_arm'+side,[(s*.15,0,.85),(s*.28,-.02,.80),(s*.34,-.045,.85)],.045,'#45e4ed','M_Emit',taper=.75)
        for j in range(3):c.tube('arm.'+side,f'ghost_claw{side}{j}',[(s*.32,-.04,.84),(s*(.36+j*.025),-.06,.91-j*.035),(s*(.39+j*.025),-.07,.88-j*.035)],.017,'#91faff','M_Emit',taper=.08)
    for i in range(4):
        ang=math.tau*i/4
        c.tube('crest',f'detached_ember{i}',[(.34*math.cos(ang),.29*math.sin(ang),1.02),(.34*math.cos(ang)+.02,.29*math.sin(ang),1.13),(.34*math.cos(ang)-.02,.29*math.sin(ang),1.20)],.026,'#57eeff','M_Emit',taper=.03)
    return c.finish('wisp')

BUILDERS={'fire_drake':drake,'elite_fire_drake':drake,'sand_golem':golem,'elite_sand_golem':golem,'phoenix':phoenix,'skeleton':skeleton,'elite_skeleton':skeleton,'scarecrow':scarecrow,'elite_scarecrow':scarecrow,'wisp':wisp}
if __name__=='__main__':
    eid=sys.argv[sys.argv.index('--')+1]
    BUILDERS[eid](eid)
