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
import creature_face as F
from mathutils.bvhtree import BVHTree

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
    def eyes(self, bone, point, spacing=.12, size=.065, iris='#ffce45', angry=False, socket=False):
        """Hero-style painted eyes (creature_face.py) projected onto the body built so far: white, toon iris
        with a soft gradient, pupil, two tiny highlights, lash line. No dark socket, no glowing iris."""
        x,y,z=point
        bpy.context.view_layer.update()
        objs=[o for b,ps in self.parts.items() if b!=bone for o in ps if o.type=='MESH']
        verts,polys=[],[]
        for o in objs:
            mw=o.matrix_world;base=len(verts)
            verts+=[mw@v.co for v in o.data.vertices]
            polys+=[[base+i for i in p.vertices] for p in o.data.polygons]
        bvh=BVHTree.FromPolygons(verts,polys) if polys else None
        k=max(.4,size/.04)
        for s in (-1,1):
            c=Vector((x+s*spacing,y,z))
            n=Vector((s*.28,-1,.05)).normalized()
            hit=bvh.ray_cast(c+n*.6,-n,1.2) if bvh else (None,None,None,None)
            if hit[0] is None:
                surf,c=F.cap_bvh(c-n*.01,n,size*2.4),c-n*.01
            else:
                surf,c=bvh,hit[0]
                n=hit[1] if hit[1].dot(n)>0 else -hit[1]
            if socket:
                parts=F.socket_eye(f'eye{s:+d}',surf,c,n,size*2.3,size*2.5,side=s,k=k,angry=.8 if angry else 0.0)
            else:
                parts=F.eye(f'eye{s:+d}',surf,c,n,size*2.2,size*2.6,iris,side=s,k=k,angry=.8 if angry else 0.0)
            for o in parts:
                self.add(bone,o)
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
        """Seven clips from the shared monster Animator (enemies_c/monster_kit.py), keyed on every frame.
        Kinds: biped (default), heavy, fly, and wisp/jelly (hovering floaters)."""
        sys.path.insert(0,os.path.join(os.path.dirname(os.path.abspath(__file__)),'..','enemies_c'))
        from monster_kit import Animator  # lazy: monster_kit itself builds on this module
        rig=A.armature(self.bones)
        anim=Animator(self.bones,self.parts,kind or 'biped')
        for clip,length in CLIPS.items():
            with Motion(rig,clip,length) as a:
                for f in range(length+1):
                    anim.write(a,clip,f,length)
        body=A.skin(self.parts,rig)
        return rig,body
    def finish(self,kind='biped'):
        rig,body=self.animate(kind)
        A.volume_shade(body)  # same grounded, solid read as the heroes
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
