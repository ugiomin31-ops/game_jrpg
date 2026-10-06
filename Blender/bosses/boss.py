"""심연의 망령술사: final abyss sorcerer, faithful to the purple horned hood/void face original.
Layered shredded robes, curved ridged horns, yellow eyes, skeletal fingers, skull clasp,
bone talismans and a purple living spell flame. Cloth chains and spell have authored clips.
"""
import sys
sys.path.append(r"C:\Users\User\Desktop\game\Blender\bosses")
from _common import *

ID="boss"
A.reset_scene()
random.seed(12)
PURPLE,DARK,HIGH,BONE,GOLD="#733574","#351b49","#ab579f","#ecdb9c","#b78d48"
parts,flexible,bones,clothchains={ },[],[],{}
def put(b,*o):parts.setdefault(b,[]).extend(o)
def bone(n,h,t,p=None):bones.append((n,h,t,p))
bone("root",(0,0,0),(0,0,.5))
bone("hips",(0,0,1),(0,0,1.5),"root")
bone("spine",(0,0,1.5),(0,0,2.12),"hips")
bone("head",(0,0,2.12),(0,0,2.85),"spine")
for s,sg in (("L",1),("R",-1)):
    sh=(sg*.55,0,2.08);el=(sg*.91,-.11,1.8 if s=="R" else 2.1);wr=(sg*1.19,-.27,1.65 if s=="R" else 2.4)
    bone(f"upperarm.{s}",sh,el,"spine");bone(f"forearm.{s}",el,wr,f"upperarm.{s}")
    bone(f"hand.{s}",wr,(wr[0],wr[1]-.2,wr[2]+.1),f"forearm.{s}")
    bone(f"fingers.{s}",(wr[0],wr[1]-.17,wr[2]),(wr[0],wr[1]-.32,wr[2]+.25),f"hand.{s}")
bone("spell",(1.19,-.37,2.74),(1.19,-.37,3.35),"hand.L")
for i in range(8):
    a=TAU*i/8
    d=V(math.cos(a),math.sin(a),0)
    h=d*.48+V(0,0,1.5);m=d*.65+V(0,0,.9);t=d*(.8+.1*(i%2))+V(0,0,.18+.1*(i%3))
    bone(f"cloth{i}a",h,m,"hips");bone(f"cloth{i}b",m,t,f"cloth{i}a")
    clothchains[i]=[(f"cloth{i}a",h,m),(f"cloth{i}b",m,t)]
rig=A.armature(bones)
# Hollow purple hood, with an angular pointed upper lip, and a black face inside.
bm=bmesh.new();rings=[]
for j in range(18):
    q=.64+(math.pi-.64)*j/18
    ring=[]
    for k in range(40):
        a=TAU*k/40
        x=.76*math.sin(q)*math.cos(a)
        y=-.73*math.cos(q)
        z=2.64+.89*math.sin(q)*math.sin(a)
        # Pointed crown and slightly ragged front rim.
        if math.sin(a)>0:z+=.20*math.sin(a)**8*(1-j/18)
        if j==0:z+=.025*math.sin(k*2.3)
        ring.append(bm.verts.new((x,y,z)))
    rings.append(ring)
for ra,rb in zip(rings,rings[1:]):
    for k in range(40):bm.faces.new((ra[k],ra[(k+1)%40],rb[(k+1)%40],rb[k]))
bm.faces.new(list(reversed(rings[-1])))
hood=obj_from_bm("hollow_hood",bm)
paint_faces(hood,lambda c,n,p:mix(PURPLE,HIGH,clamp(n.z*.35-n.y*.12+nz(c*5,4)*.18)))
put("head",hood,A.sphere("void_face",.59,loc=(0,-.15,2.62),scale=(1,.8,1.08),color="#080710",seg=28,rings=18))
# Rolled hood rim and inner shadow; opening is intentionally not a human head.
front=[]
for k in range(41):
    a=TAU*k/40
    front.append((.76*math.sin(.64)*math.cos(a),-.73*math.cos(.64)-.01,2.64+.89*math.sin(.64)*math.sin(a)+(.20*math.sin(a)**8 if math.sin(a)>0 else 0)))
rim,_=sweep("hood_roll",front,.045,seg=8,color=HIGH)
put("head",rim)
for sg in (-1,1):
    put("head",A.sphere(f"golden_eye{sg}",.12,loc=(sg*.2,-.625,2.64),scale=(.62,.3,1.6),color="#ffe472",mat="M_Emit",seg=20,rings=12),
        A.sphere(f"eye_core{sg}",.052,loc=(sg*.2,-.659,2.65),scale=(.6,.2,1.8),color="#fffbc5",mat="M_Emit",seg=12,rings=8))
    ctrl=[(sg*.54,.04,3.01),(sg*.83,.02,3.24),(sg*.88,.02,3.56),(sg*.72,-.01,3.86),(sg*.57,-.12,4.08)]
    horn,frames=sweep(f"ancient_horn{sg}",catmull(ctrl,6),[.20,.18,.14,.085,.006],seg=16,color="#70554e")
    paint_faces(horn,lambda c,n,p:mix("#42323c","#a28871",clamp(n.z*.5+.3)))
    put("head",horn)
    path,T,N=frames
    for k in range(3,len(path)-3,3):
        u=k/(len(path)-1);r=KL(u,(0,.2),(.25,.18),(.5,.14),(.75,.085),(1,.006))
        ring=A.torus(f"hornridge{sg}_{k}",R=r*.98,r=.021*(1-u)+.007,loc=path[k],color="#3d3038",seg=16,minor=5)
        ring.rotation_euler=T[k].to_track_quat("Z","Y").to_euler();put("head",ring)
# Robe trunk and ragged overcoat; rich purple broken into panel colors, not plain cones.
torso=A.lathe("robe_trunk",[(.42,1.24),(.48,1.45),(.55,1.85),(.58,2.02),(.36,2.19),(.2,2.23)],seg=32,color=PURPLE)
A.deform(torso,lambda c:Vector((c.x,c.y*.8,c.z)))
paint_faces(torso,lambda c,n,p:mix(PURPLE,DARK,clamp(c.y*.4+.15+nz(c*5,3)*.2)))
put("spine",torso)
# Thirty-two overlapping cloth gores. Each has two continuous chain influences.
for i in range(32):
    a=TAU*i/32
    ci=int((i+2)//4)%8
    bm=bmesh.new();grid=[]
    for j in range(9):
        t=j/8
        rr=.44+.42*t
        z=1.5-1.27*t
        row=[]
        for k in range(5):
            ang=a+(k-2)*.045
            rag=(.17 if k in (0,4) else -.12)*(t**8)+.09*math.sin(i*4.1)*(t**5)
            row.append(bm.verts.new((rr*math.cos(ang),rr*.8*math.sin(ang),z+rag+.035*math.sin(t*math.pi*3+i))))
        grid.append(row)
    for ra,rb in zip(grid,grid[1:]):
        for k in range(4):bm.faces.new((ra[k],ra[k+1],rb[k+1],rb[k]))
    o=obj_from_bm(f"tattered_gore{i}",bm)
    paint_faces(o,lambda c,n,p,i=i:mix([PURPLE,DARK,HIGH][i%3],DARK,clamp(.25+nz(c*8,i)*.3)))
    md=o.modifiers.new("ClothThickness","SOLIDIFY");md.thickness=.035
    A.apply_modifiers(o);chain_weights(o,clothchains[ci]);flexible.append(o)
# Torn shawl tabs, hood patches, gold stitches and floating fringes.
for sg in (-1,1):
    shawl=plate(f"shawl{sg}",[(0,.25),(.48,.2),(.82,-.02),(.58,-.18),(.72,-.33),(.22,-.19),(0,-.1)],.07,(sg*.08,-.47,2.05),(0,0,0),HIGH)
    if sg<0:A.deform(shawl,lambda c:Vector((-c.x,c.y,c.z)))
    put("spine",shawl)
    for k in range(7):
        stitch,_=sweep(f"stitch{sg}{k}",[(sg*(.19+k*.055),-.59,2.04-k*.015),(sg*(.22+k*.055),-.595,2.09-k*.015)],.012,seg=5,color=GOLD)
        put("spine",stitch)
    for k in range(4):
        tear=plate(f"hoodtear{sg}{k}",[(0,0),(.045,.04),(.023,.12),(-.015,.1)],.025,(sg*(.29+k*.09),-.60+k*.06,3.12-k*.1),(0,0,sg*-25),DARK)
        put("head",tear)
# Wide bell sleeves and skeletal hands; left palm cups the conjured flame.
for s,sg in (("L",1),("R",-1)):
    sh=V(sg*.55,0,2.08);el=V(sg*.91,-.11,1.8 if s=="R" else 2.1);wr=V(sg*1.19,-.27,1.65 if s=="R" else 2.4)
    chain=[(f"upperarm.{s}",sh,el),(f"forearm.{s}",el,wr)]
    sleeve,_=sweep(f"bell_sleeve{s}",catmull([sh,el,wr-V(0,-.02,.04)],6),[.27,.31,.38],seg=24,color=PURPLE)
    paint_faces(sleeve,lambda c,n,p:mix(PURPLE,DARK,clamp(n.y*.5+.2+nz(c*6,sg)*.2)))
    chain_weights(sleeve,chain);flexible.append(sleeve)
    for k in range(8):
        a=TAU*k/8
        p=wr+V(math.cos(a)*.33,math.sin(a)*.23,-.05)
        tab=leaf(f"sleeve_rag{s}{k}",.26+.08*(k%3),.14,loc=p,rot=(180,0,k*45),color=HIGH if k%3==0 else DARK,thick=.04)
        put(f"forearm.{s}",tab)
    put(f"hand.{s}",A.sphere(f"skeletal_palm{s}",.16,loc=wr+V(0,-.09,.06),scale=(1,.55,1.15),color="#534258",seg=16,rings=10))
    for k in range(4):
        p=wr+V((k-1.5)*.075,-.15,.12)
        ctrl=[p,p+V(0,-.13,.13),p+V(0,-.13,.27),p+V(0,-.05,.33)]
        finger,_=sweep(f"bonefinger{s}{k}",catmull(ctrl,4),[.042,.04,.032,.006],seg=8,color="#9a7898")
        put(f"fingers.{s}",finger)
        for j in (1,2):put(f"fingers.{s}",A.sphere(f"knuckle{s}{k}{j}",.046,loc=ctrl[j],color="#b29aac",seg=8,rings=6))
    thumb,_=sweep(f"thumb{s}",[wr+V(-sg*.13,-.05,.02),wr+V(-sg*.21,-.17,.13),wr+V(-sg*.15,-.22,.23)],[.065,.048,.009],seg=9,color="#9a7898")
    put(f"hand.{s}",thumb)
# Bone clasp and dangling vertebrae are part of the original necromancer silhouette.
def skull(name,loc,size,bn):
    p=V(loc)
    put(bn,A.sphere(name,size,loc=p,scale=(.88,.5,1),color=BONE,seg=16,rings=12))
    for sg in (-1,1):
        put(bn,A.sphere(name+f"socket{sg}",size*.28,loc=p+V(sg*size*.35,-size*.45,size*.12),scale=(1,.3,1.1),color="#332228",seg=10,rings=6))
    for k in range(3):put(bn,A.box(name+f"tooth{k}",(size*.22,size*.36,size*.26),loc=p+V((k-1)*size*.24,-size*.12,-size*.82),color=BONE,bevel=.008,seg=1))
skull("skull_clasp",(0,-.59,1.94),.16,"spine")
put("hips",A.torus("bone_belt",R=.46,r=.045,loc=(0,0,1.38),scale=(1,.8,1),color=GOLD,seg=32,minor=6))
for k in range(7):
    x=(k-3)*.115;z=1.28-abs(k-3)*.025
    bn=f"cloth{5 if k<3 else 6}a"
    rope,_=sweep(f"talisman_rope{k}",[(x,-.42,1.42),(x*.9,-.50,z-.20),(x*.95,-.52,z-.34)],.014,seg=6,color=GOLD)
    put(bn,rope)
    for j in range(3):
        put(bn,A.sphere(f"vertebra{k}{j}",.041,loc=(x*.93,-.52,z-.15-j*.07),scale=(1.1,.7,1.3),color=BONE,seg=10,rings=6))
    if k in (1,3,5):skull(f"belt_skull{k}",(x*.95,-.52,z-.41),.065,bn)
# Living abyss flame: bright core, translucent shell and dark curling tongues.
spell=V(1.19,-.37,2.98)
put("spell",A.sphere("abyss_core",.2,loc=spell,scale=(1,1,1.16),color="#f5a0ff",mat="M_Emit",seg=24,rings=16),
    A.sphere("abyss_halo",.275,loc=spell,scale=(1,1,1.08),color="#9343d1",mat="M_Clear",seg=20,rings=14))
for k in range(7):
    a=TAU*k/7;p=spell+V(math.cos(a)*.19,math.sin(a)*.19,-.07)
    put("spell",flame(f"spectral_tongue{k}",h=.54+.16*(k%3),r=.09,loc=p,rot=(0,math.cos(a)*-18,math.degrees(a)),bottom="#542080",top="#d16bff",seed=k,seg=10,curl=.35))
curl,_=sweep("spell_curl",catmull([spell+V(0,0,.18),spell+V(.23,0,.58),spell+V(-.13,0,.9),spell+V(.03,0,1.09),spell+V(.15,0,1.01)],5),[.14,.12,.085,.04,.002],seg=10,color="#602490",mat="M_Emit")
put("spell",curl)
for k in range(5):
    a=TAU*k/5
    put("spell",crystal(f"phase_shard{k}",.035,.12,loc=spell+V(math.cos(a)*.36,math.sin(a)*.36,.12+.06*(k%2)),color="#d48aff",mat="M_Emit"))
body=skin2(parts,flexible,rig)

def cloth(P,t,amp=1,cycles=1):
    for i in range(8):
        for j,suffix in enumerate(("a","b")):
            P.r(f"cloth{i}{suffix}",(5*amp*wave(t,cycles,i*.125-j*.12),4*amp*wave(t,cycles,i*.125-j*.12+.2),2*amp*wave(t,cycles,i*.125)))
    P.r("spell",(4*amp*wave(t,cycles),5*amp*wave(t,cycles,.2),10*amp*wave(t,cycles,.3)))
    P.s("spell",1+.06*amp*wave(t,cycles,.1))

def idle(P,f,t):
    P.l("hips",(0,0,.05*wave(t)));P.r("spine",(2*wave(t,1,.2),0,2*wave(t,1,.4)));P.r("head",(-2*wave(t,1,.3),0,-2*wave(t,1,.4)))
    P.r("forearm.L",(3*wave(t,1,.3),0,0));P.r("fingers.L",(5*wave(t,1,.4),0,0));cloth(P,t)

def run(P,f,t):
    P.l("hips",(0,0,.06*wave(t,2)));P.r("spine",(15,0,3*wave(t)));P.r("head",(-12,0,-3*wave(t)))
    P.r("upperarm.R",(22*wave(t),0,0));P.r("forearm.R",(-15,0,0));P.r("upperarm.L",(-12,0,0));cloth(P,t,2,2)

def attack(P,f,t):
    wind=K(t,(0,0),(.28,1),(.4,0),(1,0));hit=K(t,(0,0),(.32,0),(.4,1),(.62,1),(1,0))
    P.r("spine",(-12*wind+17*hit,0,12*wind-16*hit));P.r("head",(5*wind-8*hit,0,-8*wind))
    P.r("upperarm.R",(-110*wind-65*hit,0,-22*wind+18*hit));P.r("forearm.R",(-35*wind+25*hit,0,0));P.r("fingers.R",(-18*wind+45*hit,0,0));P.l("root",(0,-.19*hit,0));cloth(P,t,.7+hit)

def cast(P,f,t):
    charge=K(t,(0,0),(.47,1),(.6,1.05),(.86,.2),(1,0));release=K(t,(0,0),(.54,0),(.6,1),(.85,.2),(1,0))
    P.r("spine",(-12*charge+15*release,0,-10*charge));P.r("head",(-12*charge+10*release,0,8*charge))
    P.r("upperarm.L",(-35*charge-30*release,0,-20*charge));P.r("forearm.L",(-20*charge+22*release,0,0));P.r("hand.L",(-15*charge+15*release,0,0));P.r("fingers.L",(-20*charge+35*release,0,0))
    P.r("upperarm.R",(-55*charge,0,25*charge));P.r("forearm.R",(-45*charge,0,0));P.s("spell",1+.6*charge+.35*release);P.l("hips",(0,0,.17*charge));cloth(P,t,1+charge,2)

def hit(P,f,t):
    h=K(t,(0,0),(.17,1),(1,0));P.r("spine",(-16*h,0,9*h));P.r("head",(-12*h,0,-8*h));P.l("root",(0,.18*h,0));P.r("upperarm.L",(20*h,0,10*h));cloth(P,t,1+h,2)

def die(P,f,t):
    h=K(t,(0,0),(.2,.15),(.85,1),(1,1));P.r("root",(72*h,0,-14*h));P.l("root",(0,0,.12*h));P.r("spine",(14*h,0,10*h));P.r("head",(20*h,0,-15*h))
    P.r("upperarm.L",(45*h,0,25*h));P.r("forearm.L",(-35*h,0,0));P.r("upperarm.R",(-55*h,0,-20*h));P.s("spell",1-.96*h)
    for i in range(8):P.r(f"cloth{i}a",(15*h,0,0));P.r(f"cloth{i}b",(-12*h,0,0))
    cloth(P,t,.6*(1-h),2)

def victory(P,f,t):
    h=K(t,(0,0),(.28,1),(.76,1),(1,0));P.r("spine",(-8*h,0,0));P.r("head",(-10*h,0,8*h*wave(t)));P.r("upperarm.L",(-35*h,0,-15*h));P.r("upperarm.R",(-95*h,0,25*h));P.r("forearm.R",(-25*h,0,0));P.s("spell",1+.35*h);cloth(P,t,1+h,2)

for n,l,fn in [("Idle",60,idle),("Run",24,run),("Attack",30,attack),("Cast",35,cast),("Hit",12,hit),("Die",36,die),("Victory",44,victory),("Roar",48,victory)]:bake(rig,n,l,fn)
finish(ID,rig,body,STD_PREVIEWS+[("attack",(72,0,32),"Attack",12),("cast",(72,0,32),"Cast",21),("die",(72,0,32),"Die",36)])
