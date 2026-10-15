"""빙해의 크라켄 여왕: eight curling sucker-lined arms, ice diadem and royal trident.
Original identity: abyss_ref/art/enemies/frost_kraken/parts/body.png.
All appendages have deforming chains; icy crown, cheek fins and snow ridges remain distinct.
"""
import sys
sys.path.append(r"C:\Users\User\Desktop\game\Blender\bosses")
from _common import *

ID = "frost_kraken"
A.reset_scene()
random.seed(26)
BLUE, DARK, PALE, ICE = "#278bd0", "#174686", "#b8f6ff", "#63d9ff"
parts, flexible, bones, chains = {}, [], [], {}

def put(b, *o):
    parts.setdefault(b, []).extend(o)

def bone(n, h, t, parent=None):
    bones.append((n, h, t, parent))

bone("root", (0, 0, 0), (0, 0, .5))
bone("mantle", (0, 0, .9), (0, 0, 2.05), "root")
bone("head", (0, -.1, 2), (0, -.1, 3), "mantle")
bone("crown", (0, 0, 2.9), (0, 0, 3.65), "head")
# Arms alternate between raised defensive curls and low advancing coils.
for i in range(8):
    a = TAU * i / 8 - math.pi / 2
    d = V(math.cos(a), math.sin(a), 0)
    side = V(-d.y, d.x, 0)
    high = i in (2, 6)
    points = [d * .58 + V(0, 0, 1.12), d * 1.1 + V(0, 0, .65),
              d * 1.85 + V(0, 0, .48), d * 2.5 + V(0, 0, 1.0 if high else .56),
              d * 2.7 + V(0, 0, 2.25 if high else 1.25),
              d * 2.35 + side * .1 + V(0, 0, 2.85 if high else 1.45),
              d * 2.12 + side * .16 + V(0, 0, 2.55 if high else 1.18)]
    chain = []
    for k in range(6):
        n = f"arm{i}.{k}"
        parent = "mantle" if k == 0 else f"arm{i}.{k-1}"
        bone(n, tuple(points[k]), tuple(points[k+1]), parent)
        chain.append((n, points[k], points[k+1]))
    chains[i] = chain
    tube, frames = sweep(f"royal_tentacle{i}", catmull(points, 5),
                         lambda t: .38 * (1-t) ** .7 + .045, seg=14, n0=(0, 0, -1), color=BLUE)
    def arm_color(c, n, p, tube=tube, i=i):
        underside = face_attr(tube, p, "side")
        if underside > .32:
            return mix(PALE, ICE, .15 + .15*nz(c*4, i))
        return mix(BLUE, DARK, clamp(.4 - n.z*.4 + nz(c*3, i)*.3))
    paint_faces(tube, arm_color)
    chain_weights(tube, chain)
    flexible.append(tube)
    # Raised arms show suction cups on their front face; lower arms on undersides.
    path, tangents, normals = frames
    for k in range(8):
        idx = 5 + k*3
        t = idx / (len(path)-1)
        radius = .38 * (1-t)**.7 + .045
        normal = V(0, -1, -.35).normalized() if high else normals[idx]
        pos = path[idx] + normal * radius * .87
        cup = A.torus(f"sucker{i}_{k}", R=.115*(1-t)+.055, r=.035*(1-t)+.014,
                      loc=pos, color=PALE, seg=10, minor=5)
        cup.rotation_euler = normal.to_track_quat("Z", "Y").to_euler()
        center = A.sphere(f"suckerwell{i}_{k}", .065*(1-t)+.026, loc=pos+normal*.006,
                          scale=(1, 1, .3), color="#55afdc", seg=8, rings=4)
        center.rotation_euler = cup.rotation_euler
        obj = A.join([cup, center], f"suction{i}_{k}")
        chain_weights(obj, chain)
        flexible.append(obj)
    # Snow rests on the top ridge rather than hiding the suction cups.
    for k in range(3):
        idx = 7+k*8
        p = path[idx]
        t = idx/(len(path)-1)
        snow = blob(f"snow{i}_{k}", .24*(1-t)+.08, p+V(0,0,.27*(1-t)),
                    (1.45, .8, .28), color="#ecfbff", seed=i*3+k, amp=.22, subdiv=1)
        chain_weights(snow, chain)
        flexible.append(snow)

rig = A.armature(bones)
put("mantle", A.sphere("mantle", .92, loc=(0, .1, 1.35), scale=(1, .82, 1), color=DARK, seg=28, rings=16))
head = A.sphere("queen_head", .95, loc=(0, -.08, 2.35), scale=(1, .83, 1.03), color=BLUE, seg=32, rings=20)
paint_faces(head, lambda c,n,p: mix(BLUE, DARK, clamp(n.z*-.3 + c.y*.35 + nz(c*4, 8)*.18)))
put("head", head)
face = A.sphere("cyan_face", .75, loc=(0, -.56, 2.2), scale=(1, .44, .73), color=PALE, seg=28, rings=16)
put("head", face)
for s in (-1, 1):
    socket = A.sphere(f"lash{s}", .24, loc=(s*.37,-.85,2.38), scale=(1,.32,1.3), rot=(0,s*-23,0), color=DARK, seg=16, rings=10)
    eye = A.sphere(f"queeneye{s}", .17, loc=(s*.37,-.919,2.38), scale=(1,.23,1.2), rot=(0,s*-23,0), color="#41ecff", mat="M_Emit", seg=16,rings=10)
    pupil = A.sphere(f"pupil{s}", .052,loc=(s*.36,-.963,2.38),scale=(.5,.2,1.9),color="#f3ffff",mat="M_Emit",seg=10,rings=6)
    put("head",socket,eye,pupil)
    for k in range(3):
        lash,_ = sweep(f"eyelash{s}{k}",[(s*(.47+k*.055),-.89,2.55),(s*(.58+k*.08),-.87,2.69+k*.035)], [.045,.002],seg=6,color=DARK)
        put("head",lash)
    for k in range(5):
        fin = leaf(f"cheekfin{s}{k}", .68-k*.055, .27,loc=(s*.75,-.12,2.18-k*.13),
                   rot=(15,s*(50+k*19),s*10),color=PALE if k%2 else ICE,thick=.055)
        gem = crystal(f"fingem{s}{k}",.048,.13,loc=(s*(.85+k*.018),-.24,2.2-k*.12),color=ICE,mat="M_Emit")
        put("head",fin,gem)
mouth,_ = sweep("delicate_smile",[(-.13,-.905,2.06),(0,-.927,2.015),(.13,-.905,2.06)], .013,seg=6,color=DARK)
put("head",mouth)
# Ice tiara: a coherent five-spike crown with a central diamond and snow cap.
put("crown",A.torus("crown_band",R=.69,r=.095,loc=(0,.02,2.98),scale=(1,.84,1),color=ICE,mat="M_Clear",seg=28,minor=6))
for k in range(7):
    a = TAU*k/7
    h = 1.05 if k == 0 else (.65 if k%2 else .8)
    put("crown",crystal(f"tiara{k}",.16,h,loc=(math.sin(a)*.65,-math.cos(a)*.54,2.98),
                         rot=(math.cos(a)*-12,math.sin(a)*18,0),color=ICE,mat="M_Clear"))
    put("crown",blob(f"crown_snow{k}",.18,loc=(math.sin(a)*.65,-math.cos(a)*.54,3),scale=(1.4,1,.42),color="#f4feff",subdiv=1,seed=k))
put("crown",plate("royal_diamond",ngon(4,.24,math.pi/2,rz=.39),.075,(0,-.73,3.03),(0,0,0),"#aaffff","M_Emit"))
# Faceted collar and floating phase beads.
for k in range(11):
    a = -1.45+k*.29
    x,y = math.sin(a)*.82,-math.cos(a)*.68
    put("mantle",crystal(f"collar{k}",.1,.33+(1-abs(k-5)/5)*.25,loc=(x,y,1.9),rot=(180,0,0),color=ICE,mat="M_Clear"))
for k in range(8):
    a=TAU*k/8
    put("crown",A.sphere(f"phase_bead{k}",.07,loc=(math.sin(a)*1.14,math.cos(a)*.92,2.9+.17*(k%3)),color="#58ffff",mat="M_Emit",seg=10,rings=6))
# Original queen's trident is carried by the left outer tentacle.
end=chains[2][-1][2]
shaft,_=sweep("ice_scepter",[end+V(0,0,-.3),end+V(0,0,1.15)],.045,seg=10,color=PALE)
put("arm2.5",shaft)
for s in (-1,0,1):
    put("arm2.5",crystal(f"trident{s}",.16 if s==0 else .11,.85 if s==0 else .58,
                        loc=end+V(s*.32,0,.95 if s==0 else .82),rot=(0,s*20,0),color=ICE,mat="M_Clear"))
    if s:
        tine,_=sweep(f"tine{s}",[end+V(0,0,.72),end+V(s*.28,0,.72),end+V(s*.32,0,.92)],.065,seg=8,color=ICE,mat="M_Clear")
        put("arm2.5",tine)
put("arm2.5",crystal("scepterheart",.2,.4,loc=end+V(0,-.08,.61),color="#d4ffff",mat="M_Emit"))
body=skin2(parts,flexible,rig)

def sway(P,t,amp=1,cycles=1):
    for i,chain in chains.items():
        for k,(n,_,_) in enumerate(chain):
            P.r(n,(amp*(3+k*1.1)*wave(t,cycles,i*.125-k*.12),amp*3*wave(t,cycles,i*.125-k*.12+.3),amp*3*wave(t,cycles,i*.125)))
    P.r("crown",(2*amp*wave(t,cycles,.2),0,2*amp*wave(t,cycles,.5)))

def idle(P,f,t):
    P.l("mantle",(0,0,.035*wave(t)))
    P.s("head",(1+.012*wave(t),1+.018*wave(t),1))
    P.r("head",(-2*wave(t,1,.2),0,2*wave(t,1,.3)))
    sway(P,t)

def run(P,f,t):
    P.l("mantle",(0,0,.10*wave(t,2)))
    P.r("mantle",(10,0,3*wave(t)))
    P.r("head",(-8,0,-3*wave(t)))
    sway(P,t,2.2,2)
    for i in range(8):
        P.r(f"arm{i}.0",(14*wave(t,1,i*.125),0,0))

def attack(P,f,t):
    wind=K(t,(0,0),(.28,1),(.4,0),(1,0))
    strike=K(t,(0,0),(.31,0),(.4,1),(.65,1),(1,0))
    P.r("mantle",(-10*wind+15*strike,0,6*wind))
    P.r("head",(-7*wind+8*strike,0,-6*wind))
    for i in (0,1,7):
        for k in range(4):
            P.r(f"arm{i}.{k}",(-24*wind+22*strike,0,(i-1)*4*strike))
    P.l("root",(0,-.3*strike,0))
    sway(P,t,.5)

def cast(P,f,t):
    charge=K(t,(0,0),(.48,1),(.6,1.2),(.78,.3),(1,0))
    release=K(t,(0,0),(.55,0),(.6,1),(.82,.4),(1,0))
    P.l("mantle",(0,0,.18*charge))
    P.s("crown",1+.12*charge)
    P.r("head",(-12*charge+14*release,0,0))
    for i in range(8):
        for k in range(3):
            P.r(f"arm{i}.{k}",(-13*charge+18*release,0,4*charge*(-1 if i>3 else 1)))
    P.r("arm2.0",(-30*charge,0,-12*charge))
    sway(P,t,1+charge,2)

def hit(P,f,t):
    h=K(t,(0,0),(.17,1),(1,0))
    P.r("mantle",(-13*h,0,8*h))
    P.r("head",(-14*h,0,-7*h))
    P.l("root",(0,.17*h,0))
    sway(P,t,1+2*h,2)

def die(P,f,t):
    h=K(t,(0,0),(.2,.2),(.8,1),(1,1))
    P.l("mantle",(0,0,-.6*h))
    P.r("head",(25*h,0,-12*h))
    P.r("crown",(12*h,0,0))
    for i,chain in chains.items():
        for k,(n,_,_) in enumerate(chain):
            P.r(n,(8*h if k<3 else -23*h,0,(-1 if i<4 else 1)*4*h))
    sway(P,t,.8*(1-h),2)

def victory(P,f,t):
    h=K(t,(0,0),(.3,1),(.76,1),(1,0))
    P.l("mantle",(0,0,.15*h))
    P.r("head",(-12*h,0,8*h*wave(t)))
    for i in (2,6):
        P.r(f"arm{i}.0",(-20*h,0,(-1 if i==2 else 1)*15*h))
    sway(P,t,1+h,2)

for n,l,fn in [("Idle",60,idle),("Run",24,run),("Attack",30,attack),("Cast",35,cast),("Hit",12,hit),("Die",36,die),("Victory",44,victory),("Roar",48,victory)]:
    bake(rig,n,l,fn,step=1)
finish(ID,rig,body,STD_PREVIEWS+[("attack",(72,0,32),"Attack",12),("cast",(72,0,32),"Cast",21),("die",(72,0,32),"Die",36)])
