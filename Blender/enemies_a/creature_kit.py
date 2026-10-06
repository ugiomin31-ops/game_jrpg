"""Articulated creature construction and seven-clip authoring for the enemy roster.
All geometry is vertex-coloured; each visible appendage belongs to a named joint.
"""
import math
import os
import sys
import json
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'lib'))
import abyss_bpy as A
import bpy
from mathutils import Vector

CLIPS = {'Idle': 48, 'Run': 20, 'Attack': 25, 'Cast': 35, 'Hit': 12, 'Die': 30, 'Victory': 44}

class Motion(A.Anim):
    def r(self, bone, frame, xyz):
        self.rot(bone, frame, (xyz[0], xyz[2], -xyz[1]))
    def l(self, bone, frame, xyz):
        self.loc(bone, frame, (xyz[0], xyz[2], -xyz[1]))
    def s(self, bone, frame, xyz):
        self.scl(bone, frame, (xyz[0], xyz[2], xyz[1]))

class Creature:
    def __init__(self, eid):
        A.reset_scene()
        self.eid = eid
        self.bones = []
        self.parts = {}
        self.bone('root', (0, 0, 0), None)
    def bone(self, name, point, parent='root'):
        self.bones.append((name, point, tuple(Vector(point) + Vector((0, 0, .1))), parent))
        self.parts[name] = []
        return name
    def add(self, bone, obj):
        self.parts[bone].append(obj)
        return obj
    def orb(self, bone, name, point, radii, color, mat='M_Toon', seg=20, rings=12):
        return self.add(bone, A.sphere(name, r=1, loc=point, scale=radii, color=color, mat=mat, seg=seg, rings=rings))
    def box(self, bone, name, point, size, color, bevel=.06, rot=(0,0,0)):
        return self.add(bone, A.box(name, loc=point, size=size, color=color, bevel=bevel, rot=rot))
    def tube(self, bone, name, pts, radius, color, mat='M_Toon', taper=1):
        return self.add(bone, A.tube(name, pts, radius=radius, color=color, mat=mat, seg=8, taper_end=taper))
    def shape(self, bone, name, pts, loc, color, depth=.025, mat='M_Toon'):
        return self.add(bone, A.extrude_shape(name, pts, loc=loc, depth=depth, color=color, mat=mat))
    def spike(self, bone, name, base, tip, radius, color, mat='M_Toon'):
        base, tip = Vector(base), Vector(tip)
        o = A.cone(name, r=radius, depth=(tip-base).length, loc=(base+tip)/2, color=color, mat=mat, seg=8)
        o.rotation_euler = (tip-base).to_track_quat('Z','Y').to_euler()
        return self.add(bone,o)
    def ring(self, bone, name, point, radius, tube, color, rot=(0,0,0), scale=(1,1,1), mat='M_Toon'):
        return self.add(bone,A.torus(name,R=radius,r=tube,loc=point,rot=rot,scale=scale,color=color,mat=mat,seg=24,minor=8))
    def eyes(self, bone, point, spacing=.12, size=.065, iris='#ffce45', angry=False):
        x,y,z=point
        for s in (-1,1):
            self.orb(bone,f'eye_socket{s}',(x+s*spacing,y,z),(size*1.3,.024,size*1.5),'#211829',seg=16,rings=8)
            self.orb(bone,f'iris{s}',(x+s*spacing,y-.024,z),(size*.77,.015,size*1.16),iris,'M_Emit',seg=16,rings=8)
            self.orb(bone,f'eye_glint{s}',(x+s*spacing+size*.17,y-.039,z+size*.38),(size*.23,.009,size*.28),'#fff7e6',seg=10,rings=6)
            if angry:
                self.tube(bone,f'brow{s}',[(x+s*(spacing-size),y-.043,z+size*.7),(x+s*(spacing+size),y-.038,z+size*1.45)],.018,'#291e32')
    def mouth(self,bone,point,w=.08,fangs=False):
        x,y,z=point
        self.orb(bone,'mouth',(x,y,z),(w,.02,w*.65),'#451327',seg=16,rings=8)
        self.orb(bone,'tongue',(x,y-.018,z-w*.3),(w*.6,.012,w*.22),'#ff8a99',seg=12,rings=6)
        if fangs:
            for s in (-1,1):
                self.spike(bone,f'fang{s}',(x+s*w*.6,y-.03,z+w*.45),(x+s*w*.53,y-.04,z-w*.25),w*.18,'#fff6dd')
    def crown(self,bone,z,r=.22,color='#d5ad42'):
        self.ring(bone,'crown_band',(0,0,z),r,.025,color)
        for i in range(7):
            t=2*math.pi*i/7
            p=(r*math.cos(t),r*math.sin(t),z)
            q=(r*1.07*math.cos(t),r*1.07*math.sin(t),z+.15+(i%2)*.04)
            self.spike(bone,f'crown_point{i}',p,q,.05,color)
            self.orb(bone,f'crown_jewel{i}',q,(.025,.025,.032),'#a9ffe2','M_Emit',seg=10,rings=6)
    def animate(self,kind='biped'):
        rig=A.armature(self.bones)
        names=set(self.parts)
        flying=kind in ('fly','jelly','wisp')
        heavy=kind=='heavy'
        for clip,length in CLIPS.items():
            with Motion(rig,clip,length) as a:
                frames = {round(i * length / 12) for i in range(13)}
                if clip == 'Attack':
                    frames.add(round(length * .4))
                elif clip == 'Cast':
                    frames.add(round(length * .6))
                for i, f in enumerate(sorted(frames)):
                    t = f / length
                    wave=math.sin(math.tau*t)
                    pulse=math.sin(math.pi*t)
                    # All clips are authored in place; lunges return to the origin.
                    if clip=='Idle':
                        a.l('root',f,(0,0,.025*wave if flying else .008*wave))
                    elif clip=='Run':
                        a.l('root',f,(0,0,.04*(1-math.cos(math.tau*t*2))))
                        if 'body' in names: a.r('body',f,(8 if not flying else -10,0,0))
                    elif clip=='Attack':
                        hit=max(0,1-abs(t-.4)/.18)
                        wind=max(0,1-abs(t-.2)/.2)
                        a.l('root',f,(0,.07*wind-.3*hit,.10*hit if flying else .02*hit))
                        if 'body' in names:a.r('body',f,(-12*wind+24*hit,0,0))
                    elif clip=='Cast':
                        release=max(0,1-abs(t-.6)/.2)
                        a.l('root',f,(0,0,.10*pulse if flying else .025*release))
                        if 'head' in names:a.r('head',f,(-20*pulse,0,0))
                        if 'crest' in names:a.s('crest',f,(1+.25*release,1+.25*release,1+.45*release))
                    elif clip=='Hit':
                        recoil=max(0,1-abs(t-.2)/.2)
                        a.l('root',f,(0,.13*recoil,0))
                        if 'body' in names:a.r('body',f,(-22*recoil,8*recoil,0))
                    elif clip=='Die':
                        fall=min(1,max(0,(t-.15)/.65))
                        if flying:
                            # Collapse by scaling around the ground root: no below-floor hover offset.
                            a.s('root',f,(1-.75*fall,1-.75*fall,1-.95*fall))
                        else:
                            a.r('root',f,(82*fall,0,-12*fall))
                            a.l('root',f,(0,.18*fall,.10*fall))
                    elif clip=='Victory':
                        a.l('root',f,(0,0,.10*abs(math.sin(math.tau*t))))
                        if 'head' in names:a.r('head',f,(-10*pulse,0,8*wave))
                    for name in names:
                        if name.startswith('wing.'):
                            side=1 if name.endswith('L') else -1
                            flap=(22 if clip=='Idle' else 40)*math.sin(math.tau*t*(2 if clip=='Run' else 1))
                            if clip=='Die':flap=-65*t
                            elif clip=='Cast':flap=50*pulse
                            a.r(name,f,(0,side*flap,side*8*pulse))
                        elif name.startswith('tentacle'):
                            phase=int(name.replace('tentacle',''))*.62
                            sway=math.sin(math.tau*t+phase)-math.sin(phase)
                            a.r(name,f,(18*sway,12*sway,5*sway))
                        elif name.startswith(('leg.','arm.')):
                            side=1 if name.endswith('L') else -1
                            isarm=name.startswith('arm.')
                            angle=(22 if isarm else 30)*side*wave if clip=='Run' else 3*wave
                            if heavy:angle*=.6
                            if clip=='Attack' and isarm:
                                angle=-45*max(0,1-abs(t-.22)/.22)+75*max(0,1-abs(t-.4)/.2)
                            elif clip=='Cast' and isarm:angle=-95*pulse
                            elif clip=='Victory' and isarm:angle=-115*pulse
                            elif clip=='Die':angle=30*t
                            a.r(name,f,(angle,0,side*(12*pulse if clip in ('Cast','Victory') else 0)))
                        elif name.startswith('tail'):
                            a.r(name,f,(5*wave,0,20*wave*(.2 if clip=='Die' else 1)))
                        elif name=='jaw':
                            a.r(name,f,(20*pulse if clip in ('Attack','Cast','Victory') else 4*wave,0,0))
                        elif name=='eyes' and clip in ('Idle','Hit','Die'):
                            blink=.12 if (clip=='Idle' and i==9) or (clip=='Hit' and i in (2,3)) or (clip=='Die' and i>7) else 1
                            a.s(name,f,(1,1,blink))
        body=A.skin(self.parts,rig)
        return rig,body
    def finish(self,kind='biped'):
        rig,body=self.animate(kind)
        tris=sum(len(p.vertices)-2 for p in body.data.polygons)
        if not all(name in bpy.data.actions for name in CLIPS):raise RuntimeError('Missing creature action')
        rig.animation_data.action=bpy.data.actions['Idle']
        bpy.context.scene.frame_set(0)
        path=A.export_fbx(f'Enemies/{self.eid}/{self.eid}.fbx',[rig,body],animated=True)
        A.save_blend('enemy_'+self.eid)
        for suffix,clip,frame,angle in [('','Idle',0,(70,0,25)),('_side','Idle',0,(80,0,90)),('_attack','Attack',10,(75,0,35)),('_cast','Cast',21,(70,0,25)),('_die','Die',30,(65,0,35))]:
            A.render_preview('enemy_'+self.eid+suffix,objects=[rig,body],action=clip,frame=frame,angle=angle,size=480)
        manifest={'id':self.eid,'fbx':path,'triangles':tris,'bones':list(self.parts),'clips':{n:list(bpy.data.actions[n].frame_range) for n in CLIPS},'missing_clips':[]}
        print('ENEMY_EXPORT '+json.dumps(manifest),flush=True)
        return manifest
