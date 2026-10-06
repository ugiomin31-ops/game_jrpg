"""불꽃 스핑크스: regal volcanic lion, striped nemes, cobra diadem, feathered fire wings.
Reference: abyss_ref/art/enemies/flame_sphinx/parts/body.png. Generates complete rigged boss,
phase gems, layered wing feathers, articulated paws/tail and eight baked animation takes.
"""
import sys
sys.path.append(r"C:\Users\User\Desktop\game\Blender\bosses")
from _common import *

ID="flame_sphinx"
A.reset_scene()
random.seed(91)
SAND,CREAM,GOLD,RED,ROCK,EMBER="#dba15c","#ffdea0","#ffca4b","#9e271d","#443634","#ff6a16"
parts, flexible, bones = {}, [], []
def put(b,*o): parts.setdefault(b,[]).extend(o)
def bone(n,h,t,p=None): bones.append((n,h,t,p))
bone("root",(0,0,0),(0,0,.5))
bone("body",(0,.35,1.15),(0,-.35,1.6),"root")
bone("chest",(0,-.35,1.6),(0,-.65,2.23),"body")
bone("neck",(0,-.65,2.23),(0,-.8,2.65),"chest")
bone("head",(0,-.8,2.65),(0,-.88,3.25),"neck")
bone("jaw",(0,-1.06,2.62),(0,-1.4,2.55),"head")
bone("mane",(0,-.3,2.4),(0,-.25,3.15),"neck")
bone("diadem",(0,-.9,3.15),(0,-.9,3.7),"head")
for s,sg in (("L",1),("R",-1)):
    for label,y,z in (("front",-.65,1.65),("rear",.82,1.25)):
        x=.62*sg
        h=(x,y,z); k=(x*1.15,y+.07,.7); a=(x*1.18,y-.12,.22)
        bone(f"{label}upper.{s}",h,k,"chest" if label=="front" else "body")
        bone(f"{label}lower.{s}",k,a,f"{label}upper.{s}")
        bone(f"{label}paw.{s}",a,(x*1.18,y-.5,.14),f"{label}lower.{s}")
    bone(f"wing0.{s}",(.48*sg,.02,2.02),(1.22*sg,.22,2.62),"chest")
    bone(f"wing1.{s}",(1.22*sg,.22,2.62),(2.05*sg,.5,3.02),f"wing0.{s}")
    bone(f"feathers.{s}",(2.05*sg,.5,3.02),(2.65*sg,.65,3.27),f"wing1.{s}")
tailpoints=[(0,1.12,1.12),(.12,1.6,1.02),(.2,2.04,1.35),(.13,2.35,1.87),(0,2.3,2.25)]
tailchain=[]
for k in range(4):
    n=f"tail{k}"
    bone(n,tailpoints[k],tailpoints[k+1],"body" if k==0 else f"tail{k-1}")
    tailchain.append((n,tailpoints[k],tailpoints[k+1]))
rig=A.armature(bones)
put("body",A.sphere("lion_trunk",.9,loc=(0,.24,1.28),scale=(.9,1.3,.86),color=SAND,seg=32,rings=20))
put("chest",A.sphere("proud_chest",.76,loc=(0,-.5,1.82),scale=(.94,.82,1.1),color=CREAM,seg=28,rings=18))
put("neck",A.sphere("neck_fur",.56,loc=(0,-.64,2.3),scale=(1,.9,1.08),color=CREAM,seg=24,rings=14))
put("head",A.sphere("feline_skull",.62,loc=(0,-.8,2.94),scale=(1,.88,1.03),color=ROCK,seg=28,rings=18))
for sg in (-1,1):
    put("head",A.sphere(f"muzzle{sg}",.25,loc=(sg*.17,-1.3,2.73),scale=(1.1,.8,.8),color=CREAM,seg=18,rings=12))
    ear=plate(f"ear{sg}",[(0,0),(.43,0),(.38,.65),(.08,.42)],.17,(sg*.28,-.72,3.19),(0,sg*-18,0),ROCK)
    inner=plate(f"innerear{sg}",[(.08,.08),(.34,.08),(.32,.49),(.15,.32)],.06,(sg*.28,-.83,3.19),(0,sg*-18,0),"#ce7537")
    if sg<0:
        A.deform(ear,lambda c:Vector((-c.x,c.y,c.z)))
        A.deform(inner,lambda c:Vector((-c.x,c.y,c.z)))
    put("head",ear,inner)
    put("head",A.sphere(f"socket{sg}",.22,loc=(sg*.31,-1.245,3.02),scale=(1,.32,.64),rot=(0,sg*-18,0),color="#241c22",seg=18,rings=10),
        A.sphere(f"eye{sg}",.17,loc=(sg*.31,-1.29,3.02),scale=(1,.25,.58),rot=(0,sg*-18,0),color="#fff14b",mat="M_Emit",seg=16,rings=10),
        A.sphere(f"iris{sg}",.045,loc=(sg*.31,-1.335,3.02),scale=(.4,.3,1.6),color="#57220e",seg=10,rings=6))
    brow,_=sweep(f"brow{sg}",[(sg*.09,-1.22,3.17),(sg*.34,-1.29,3.17),(sg*.53,-1.16,3.23)],[.09,.10,.02],seg=8,color=ROCK)
    put("head",brow)
put("head",plate("nose",[(-.12,0),(.12,0),(0,-.11)],.07,(0,-1.48,2.78),(0,0,0),"#38251c"))
put("jaw",A.sphere("lower_muzzle",.25,loc=(0,-1.25,2.57),scale=(1.25,.8,.5),color=CREAM,seg=16,rings=10))
for sg in (-1,1):
    put("jaw",A.cone(f"fang{sg}",r=.035,depth=.16,loc=(sg*.23,-1.4,2.55),rot=(180,0,0),color="#fff5d3",seg=8))
# Nemes: draped striped cloth on both sides; alternating geometry/color bands.
for sg,s in ((1,"L"),(-1,"R")):
    for k in range(11):
        z=3.38-k*.108
        width=.29+.10*math.sin(k/10*math.pi)
        x=sg*(.51+.14*math.sin(k/10*math.pi))
        band=A.box(f"nemes{s}{k}",(width,.34,.108),loc=(x,-.93,z),rot=(-4,sg*-12,0),color=GOLD if k%2==0 else RED,bevel=.025,seg=1)
        put("head",band)
    put("head",leaf(f"nemes_tip{s}",.29,.3,loc=(sg*.62,-.99,2.23),rot=(180,sg*-12,0),color=GOLD,thick=.18))
put("head",A.torus("headband",R=.57,r=.07,loc=(0,-.77,3.32),scale=(1,.87,1),color=GOLD,seg=28,minor=6))
# Cobra diadem, scarlet diamond and eyes.
cobra,_=sweep("cobra",catmull([(0,-1.23,3.23),(0,-1.22,3.52),(0,-1.16,3.79),(0,-1.31,3.89)],4),[.09,.075,.12,.08],seg=10,color=GOLD)
put("diadem",cobra,plate("cobra_hood",[(-.16,0),(-.18,.2),(0,.3),(.18,.2),(.16,0)],.08,(0,-1.14,3.56),(0,0,0),GOLD),
    plate("diadem_gem",ngon(4,.14,math.pi/2,rz=.19),.06,(0,-1.32,3.28),(0,0,0),"#ff431e","M_Emit"))
# Lion limbs, obsidian shoulder/haunch plates, broad claws and ornate cuffs.
for s,sg in (("L",1),("R",-1)):
    for label,y,z in (("front",-.65,1.65),("rear",.82,1.25)):
        x=.62*sg
        upper=f"{label}upper.{s}"; lower=f"{label}lower.{s}"; paw=f"{label}paw.{s}"
        limb,_=sweep(f"{label}limb{s}",[(x,y,z),(x*1.15,y+.07,.7)],[.32 if label=="front" else .4,.24],seg=18,color=SAND)
        calf,_=sweep(f"{label}calf{s}",[(x*1.15,y+.07,.7),(x*1.18,y-.12,.22)],[.25,.19],seg=16,color=CREAM)
        put(upper,limb); put(lower,calf)
        armor=blob(f"{label}armor{s}",.34,loc=(x,y-.06,z-.16),scale=(1.08,1.05,1.15),color=ROCK,amp=.18,subdiv=2,flat=True,seed=sg*z)
        put(upper,armor)
        for k in range(3):
            crack,_=sweep(f"lavacrack{label}{s}{k}",[(x-.22+k*.16,y-.37,z-.34),(x-.1+k*.11,y-.41,z-.12),(x-.2+k*.18,y-.36,z+.05)],.017,seg=6,color="#ffae26",mat="M_Emit")
            put(upper,crack)
        put(lower,A.torus(f"cuff{label}{s}",R=.245,r=.055,loc=(x*1.18,y-.07,.39),color=GOLD,seg=20,minor=6),
            plate(f"cuffgem{label}{s}",ngon(4,.12,math.pi/2),.06,(x*1.18,y-.32,.4),(0,0,0),RED,"M_Emit"))
        put(paw,A.sphere(f"paw{label}{s}",.29,loc=(x*1.18,y-.29,.18),scale=(1.28,1.46,.62),color=ROCK,seg=20,rings=12))
        for k in range(3):
            claw,_=sweep(f"claw{label}{s}{k}",[(x*1.18+(k-1)*.19,y-.45,.21),(x*1.18+(k-1)*.21,y-.66,.15),(x*1.18+(k-1)*.21,y-.72,.05)],[.10,.065,.002],seg=9,color="#2a2021")
            put(paw,claw)
# Broad neck pectoral, embossed chevrons and central solar phase core.
put("chest",A.torus("gold_pectoral",R=.57,r=.085,loc=(0,-.59,2.05),rot=(19,0,0),scale=(1.17,1,1),color=GOLD,seg=32,minor=6),
    plate("pectoral_plate",[(0,-.25),(-.6,.12),(-.43,.25),(0,.02),(.43,.25),(.6,.12)],.1,(0,-1.03,1.97),(0,0,0),GOLD),
    plate("solar_core",ngon(4,.18,math.pi/2,rz=.27),.08,(0,-1.14,1.95),(0,0,0),"#ff7622","M_Emit"),
    plate("solar_center",ngon(4,.08,math.pi/2,rz=.12),.09,(0,-1.19,1.95),(0,0,0),"#fff186","M_Emit"))
# Twenty-four independently readable mane flames, outlined by darker orange roots.
for k in range(24):
    a=TAU*k/24
    x=math.cos(a)*.59; z=2.65+math.sin(a)*.64
    rot=(0,math.degrees(math.pi/2-a),0)
    put("mane",flame(f"mane_flame{k}",h=.53+.16*(k%3),r=.16,loc=(x,-.33,z),rot=rot,bottom="#f45112",top="#fff27d",seed=k,curl=.2,seg=10))
# Wings: sturdy gold leading edges, overlapping flattened feather fans in three hues.
for s,sg in (("L",1),("R",-1)):
    spar,_=sweep(f"wing_spar{s}",[(sg*.48,.02,2.02),(sg*1.22,.22,2.62),(sg*2.05,.5,3.02),(sg*2.65,.65,3.27)],[.16,.14,.10,.015],seg=12,color=GOLD)
    chain=[(f"wing0.{s}",(sg*.48,.02,2.02),(sg*1.22,.22,2.62)),(f"wing1.{s}",(sg*1.22,.22,2.62),(sg*2.05,.5,3.02)),(f"feathers.{s}",(sg*2.05,.5,3.02),(sg*2.65,.65,3.27))]
    chain_weights(spar,chain);flexible.append(spar)
    for row,count in ((0,14),(1,11),(2,8)):
        for k in range(count):
            u=k/(count-1)
            start=V(sg*(.75+1.64*u),.24+u*.33,2.25+.76*u)
            ln=.95-row*.17+.20*math.sin(u*math.pi)
            end=start+V(sg*(.38+.38*u),.1+.25*row,-ln)
            pts=catmull([start,start+(end-start)*.48+V(0,-.03,.08),end],4)
            feather,_=sweep(f"feather{s}{row}_{k}",pts,lambda t:.13*math.sin(math.pi*t)**.65+.005,
                            seg=10,n0=(1,0,0),shape=lambda t,a:1 if abs(math.cos(a))>.9 else .35,color=[ROCK,EMBER,"#ffcb44"][row])
            chain_weights(feather,chain);flexible.append(feather)
    put(f"wing0.{s}",plate(f"wing_gold{s}",[(0,0),(.45,.05),(.62,.52),(.33,.75),(.08,.28)],.09,(sg*.75,.03,2.1),(0,sg*24,0),GOLD),
        crystal(f"wing_phase{s}",.12,.33,loc=(sg*.95,-.06,2.52),rot=(0,sg*30,0),color="#ff4a18",mat="M_Emit"))
tail,_=sweep("lion_tail",catmull(tailpoints,6),[.15,.13,.105,.08,.04],seg=12,color=ROCK)
chain_weights(tail,tailchain);flexible.append(tail)
put("tail3",flame("tail_blaze",h=.77,r=.22,loc=tailpoints[-1],seed=8,seg=12))
for k in (1,2):
    put(f"tail{k}",A.torus(f"tail_ring{k}",R=.13,r=.035,loc=tailpoints[k],rot=(20,0,0),color=GOLD,seg=18,minor=6))
body=skin2(parts,flexible,rig)

def secondary(P,t,amp=1,cycles=1):
    for s,sg in (("L",1),("R",-1)):
        P.r(f"wing0.{s}",(3*amp*wave(t,cycles),sg*5*amp*wave(t,cycles,.1),0))
        P.r(f"wing1.{s}",(2*amp*wave(t,cycles,.15),sg*7*amp*wave(t,cycles,.15),0))
        P.r(f"feathers.{s}",(3*amp*wave(t,cycles,.25),sg*4*amp*wave(t,cycles,.25),0))
    for k in range(4):P.r(f"tail{k}",(3*amp*wave(t,cycles,k*.13),4*amp*wave(t,cycles,k*.13+.2),6*amp*wave(t,cycles,k*.13)))
    P.s("mane",1+.02*amp*wave(t,cycles,.2))

def idle(P,f,t):
    P.r("chest",(1.2*wave(t),0,0));P.s("chest",(1+.015*wave(t),1+.015*wave(t),1))
    P.r("head",(-2*wave(t,1,.2),0,2*wave(t,1,.5)))
    secondary(P,t)

def run(P,f,t):
    P.l("body",(0,0,.08*wave(t,2)));P.r("body",(3*wave(t),0,0))
    for s,phase in (("L",0),("R",.5)):
        for label,offset in (("front",0),("rear",.5)):
            w=wave(t,1,phase+offset)
            P.r(f"{label}upper.{s}",(30*w,0,0));P.r(f"{label}lower.{s}",(-30*max(0,w),0,0));P.r(f"{label}paw.{s}",(-10*w,0,0))
    P.r("head",(-7,0,0));secondary(P,t,1.6,2)

def attack(P,f,t):
    wind=K(t,(0,0),(.27,1),(.4,0),(1,0));hit=K(t,(0,0),(.3,0),(.4,1),(.65,1),(1,0))
    P.r("chest",(-10*wind+12*hit,0,-13*wind+18*hit));P.r("head",(5*wind-8*hit,0,6*wind))
    P.r("frontupper.R",(-90*wind-50*hit,0,-15*wind+30*hit));P.r("frontlower.R",(-20*wind+25*hit,0,0));P.r("frontpaw.R",(-20*wind+35*hit,0,0))
    P.l("root",(0,-.26*hit,0));P.r("jaw",(8*wind+12*hit,0,0));secondary(P,t,.7)

def cast(P,f,t):
    charge=K(t,(0,0),(.48,1),(.6,1),(.85,.2),(1,0));release=K(t,(0,0),(.55,0),(.6,1),(.8,.2),(1,0))
    P.r("chest",(-14*charge+17*release,0,0));P.r("head",(-16*charge+12*release,0,0));P.r("jaw",(22*release,0,0))
    P.s("mane",1+.12*charge);P.s("diadem",1+.08*charge)
    for s,sg in (("L",1),("R",-1)):
        P.r(f"wing0.{s}",(-12*charge,-sg*24*charge+sg*18*release,0));P.r(f"wing1.{s}",(0,-sg*22*charge+sg*25*release,0))
    secondary(P,t,.5,2)

def hit(P,f,t):
    h=K(t,(0,0),(.15,1),(1,0));P.r("chest",(-12*h,0,-8*h));P.r("head",(-14*h,0,8*h));P.l("root",(0,.18*h,0));secondary(P,t,1+h,2)

def die(P,f,t):
    h=K(t,(0,0),(.2,.15),(.8,1),(1,1));P.l("root",(0,0,-.56*h));P.r("body",(0,45*h,0));P.r("chest",(18*h,0,0));P.r("head",(22*h,0,-15*h))
    for s,sg in (("L",1),("R",-1)):
        for label in ("front","rear"):
            P.r(f"{label}upper.{s}",(30*h,0,sg*15*h));P.r(f"{label}lower.{s}",(-55*h,0,0))
        P.r(f"wing0.{s}",(25*h,sg*22*h,0));P.r(f"wing1.{s}",(15*h,sg*12*h,0))
    P.s("mane",1-.2*h);secondary(P,t,.8*(1-h))

def victory(P,f,t):
    h=K(t,(0,0),(.25,1),(.75,1),(1,0));P.r("chest",(-12*h,0,0));P.r("head",(-18*h,0,10*h*wave(t)));P.r("jaw",(16*h,0,0))
    for s,sg in (("L",1),("R",-1)):P.r(f"wing0.{s}",(0,-sg*22*h,0))
    secondary(P,t,1+h,2)

for n,l,fn in [("Idle",60,idle),("Run",24,run),("Attack",30,attack),("Cast",35,cast),("Hit",12,hit),("Die",36,die),("Victory",44,victory),("Roar",48,victory)]:bake(rig,n,l,fn)
finish(ID,rig,body,STD_PREVIEWS+[("attack",(72,0,32),"Attack",12),("cast",(72,0,32),"Cast",21),("die",(72,0,32),"Die",36)])
