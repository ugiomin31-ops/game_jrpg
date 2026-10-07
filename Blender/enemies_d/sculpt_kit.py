"""Sculpted creature kit (monster v3): one continuous, clay-like body per monster.

Why: the v1/v2 monsters were built from separate primitives (spheres, tubes, cones) glued together, with a
face painted or stuck on — they read as "a ball with a face". Here the body is modelled the way a sculptor
blocks a creature out: overlapping ellipsoid masses (`blob`, `limb`) are fused into ONE surface (metaballs ->
voxel remesh -> smoothing -> decimation), so necks, shoulders, haunches and bellies flow into each other.

* Skinning: every vertex is weighted to the bones of the masses that formed it (smooth falloff, up to three
  bones), so legs bend out of the body instead of rotating as rigid sticks. Hard props (horns, claws, crystals,
  weapons) are still rigid `add` parts.
* Colour: each mass carries a colour (or a function of position); colours blend softly where masses meet,
  like painted regions on a figure. Ambient occlusion is then baked with Cycles into the vertex colour, so the
  model is shaded like the heroes (creases, armpits, under the jaw darken) without textures.
* Eyes: `eye` builds a real eyeball (sclera, iris, pupil, one small glint) set into the head; masses placed over
  it become lids/brows. Eyes are sized like an animal's, never glowing, never anime stickers.

Bones and animation are exactly the v2 kit's (enemies_c/monster_kit.py), so the seven clips, kinds
(biped/heavy/quad/crawler/fly/float/hop) and the production checks stay the same.
"""
import math
import os
import sys

import bpy  # noqa: E402

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, '..', 'enemies_c'))
from monster_kit import Monster, A, hexmix  # noqa: E402,F401
from mathutils import Euler, Vector  # noqa: E402

SURFACE = 0.573  # metaball surface radius / element radius (stiffness 2, threshold 0.6), measured


def rgba(c):
    return A._as_rgba(c)


def lerp_col(a, b, t):
    a, b = rgba(a), rgba(b)
    t = max(0.0, min(1.0, t))
    return tuple(a[i] * (1 - t) + b[i] * t for i in range(4))


def vgrad(z0, c0, z1, c1):
    """Colour function: vertical gradient between heights z0 (c0) and z1 (c1)."""
    return lambda p: lerp_col(c0, c1, (p.z - z0) / (z1 - z0))


def belly(axis_y, front_col, back_col, soft=0.08):
    """Colour function: lighter underside/front (y < axis_y) blending into the back colour."""
    return lambda p: lerp_col(front_col, back_col, 0.5 + (p.y - axis_y) / (2 * soft))


class Sculpt(Monster):
    def __init__(self, eid, voxel=0.0065, tris=8000, ao=0.6, smooth=3, material='M_Toon'):
        super().__init__(eid)
        self.material = material
        self.masses = []
        self.voxel = voxel
        self.target_tris = tris
        self.ao_strength = ao
        self.smooth_iterations = smooth
        self.arm_limit = (75, 28)  # fused shoulders stretch into webbing beyond this; big swings are compressed

    # ------------------------------------------------------------ modelling
    def blob(self, bone, co, radii, color, rot=(0, 0, 0), stiff=2.0, negative=False, weight=1.0):
        """One ellipsoid mass of the fused body. radii are the visible half-sizes (m); rot in degrees."""
        r = Vector(radii) if hasattr(radii, '__len__') else Vector((radii, radii, radii))
        self.masses.append(dict(bone=bone, co=Vector(co), r=r, q=Euler([math.radians(a) for a in rot]).to_quaternion(),
                                color=color, stiff=stiff, neg=negative, w=weight, ghost=False))

    def paint(self, co, radii, color, rot=(0, 0, 0), weight=1.0):
        """Colour-only mass: tints the fused surface (markings, spots, mouth interior) without adding volume."""
        r = Vector(radii) if hasattr(radii, '__len__') else Vector((radii, radii, radii))
        self.masses.append(dict(bone=None, co=Vector(co), r=r, q=Euler([math.radians(a) for a in rot]).to_quaternion(),
                                color=color, stiff=2.0, neg=False, w=weight, ghost=True))

    def limb(self, bones, pts, radii, color, spacing=0.5, **kw):
        """A tapered limb/tail/neck through pts with radius radii[i] at each point (masses every r*spacing).
        bones: one bone name, or one per segment."""
        for i in range(len(pts) - 1):
            a, b = Vector(pts[i]), Vector(pts[i + 1])
            ra, rb = radii[i], radii[i + 1]
            n = max(1, int((b - a).length / (min(ra, rb) * spacing)))
            bone = bones if isinstance(bones, str) else bones[i]
            last = i == len(pts) - 2
            for k in range(n + (1 if last else 0)):
                t = k / n
                self.blob(bone, a.lerp(b, t), ra + (rb - ra) * t, color, **kw)

    def eye(self, bone, center, look, r, iris, pupil='#1b1418', sclera='#efe8dc', slit=False, glint=True, iris_edge=0.6):
        """Modelled eyeball facing `look`: sclera, iris with a darker upper half, pupil, one small glint.
        Embed it ~40 % into the head and add a lid/brow mass over it for a natural socket."""
        c, look = Vector(center), Vector(look).normalized()
        o = A.sphere('eyeball', r=r, loc=tuple(c), color=sclera, seg=20, rings=12)
        A.apply_transform(o)
        up = Vector((0, 0, 1))
        side = up.cross(look).normalized()
        upv = look.cross(side).normalized()
        hl = (look * 0.82 + upv * 0.45 - side * 0.35 * (1 if c.x >= 0 else -1)).normalized()
        dark, light = rgba(hexmix(iris, '#000000', 0.45)), rgba(hexmix(iris, '#ffffff', 0.3))
        me = o.data
        attr = me.color_attributes['Col']
        for loop in me.loops:
            d = (me.vertices[loop.vertex_index].co - c).normalized()
            ca = d.dot(look)
            up_t = d.dot(upv)
            if glint and d.dot(hl) > 0.975:
                col = (1, 1, 1, 1)
            elif slit and ca > 0.84 and abs(d.dot(side)) < 0.1:
                col = rgba(pupil)
            elif not slit and ca > 0.9:
                col = rgba(pupil)
            elif ca > iris_edge:
                col = lerp_col(light, dark, 0.5 + up_t * 2.2)
            elif ca > iris_edge - 0.06:
                col = rgba('#1d1720')
            else:
                col = rgba(sclera)
            attr.data[loop.index].color_srgb = col
        return self.add(bone, o)

    def tuft(self, bone, root, direction, length, r, color, curl=0.0, weight=1.0):
        """A sculpted fur/feather clump fused into the body: a tapering run of masses from `root` along
        `direction`, ending in a soft point (curl bends the tip downward)."""
        d = Vector(direction).normalized()
        pts, radii = [], []
        for k in range(5):
            t = k / 4
            pts.append(Vector(root) + d * length * t + Vector((0, 0, -curl * length * t * t)))
            radii.append(r * (1 - 0.78 * t))
        self.limb(bone, pts, radii, color, spacing=0.45, weight=weight)

    def tufts(self, bone, root, directions, length, r, color, curl=0.0, weight=1.0):
        for d in directions:
            self.tuft(bone, root, d, length, r, color, curl, weight)

    def membrane(self, bone, name, root, edge, color, thick=0.006, edge_color=None):
        """Wing membrane: triangle fan from `root` to the 3D `edge` points (scalloped edges stay valid when
        triangulated), given a little thickness so both sides render."""
        import bmesh
        bm = bmesh.new()
        r = bm.verts.new(Vector(root))
        vs = [bm.verts.new(Vector(p)) for p in edge]
        for a, b in zip(vs, vs[1:]):
            bm.faces.new((r, a, b))
        me = bpy.data.meshes.new(name)
        bm.to_mesh(me)
        bm.free()
        o = bpy.data.objects.new(name, me)
        bpy.context.scene.collection.objects.link(o)
        md = o.modifiers.new('solid', 'SOLIDIFY')
        md.thickness = thick
        md.offset = 0
        A.apply_modifiers(o)
        A.paint(o, color)
        if edge_color:
            attr = o.data.color_attributes['Col']
            rv = Vector(root)
            far = max((Vector(p) - rv).length for p in edge)
            for loop in o.data.loops:
                t = (o.data.vertices[loop.vertex_index].co - rv).length / far
                attr.data[loop.index].color_srgb = lerp_col(color, edge_color, max(0.0, (t - 0.55) / 0.45))
        return self.add(bone, o)

    # ------------------------------------------------------------ fusing
    def _level(self, m, p):
        """Normalised ellipsoid distance (1 on the mass surface)."""
        d = m['q'].inverted() @ (p - m['co'])
        return Vector((d.x / m['r'].x, d.y / m['r'].y, d.z / m['r'].z)).length

    def _organic(self):
        mb = bpy.data.metaballs.new('Sculpt')
        mb.resolution = self.voxel * 0.9
        mb.render_resolution = self.voxel * 0.9
        mb.threshold = 0.6
        ob = bpy.data.objects.new('Sculpt', mb)
        bpy.context.scene.collection.objects.link(ob)
        for m in self.masses:
            if m['ghost']:
                continue
            e = mb.elements.new(type='ELLIPSOID')
            big = max(m['r'])
            e.co = m['co']
            e.radius = big / SURFACE
            e.size_x, e.size_y, e.size_z = (m['r'].x / big, m['r'].y / big, m['r'].z / big)
            e.rotation = m['q']
            e.stiffness = m['stiff']
            e.use_negative = m['neg']
        bpy.context.view_layer.update()
        dg = bpy.context.evaluated_depsgraph_get()
        me = bpy.data.meshes.new_from_object(ob.evaluated_get(dg))
        bpy.data.objects.remove(ob)
        o = bpy.data.objects.new('Organic', me)
        bpy.context.scene.collection.objects.link(o)
        bpy.ops.object.select_all(action='DESELECT')
        bpy.context.view_layer.objects.active = o
        o.select_set(True)
        rm = o.modifiers.new('remesh', 'REMESH')
        rm.mode = 'VOXEL'
        rm.voxel_size = self.voxel
        bpy.ops.object.modifier_apply(modifier='remesh')
        sm = o.modifiers.new('smooth', 'SMOOTH')
        sm.factor = 0.5
        sm.iterations = self.smooth_iterations
        bpy.ops.object.modifier_apply(modifier='smooth')
        tris = sum(len(p.vertices) - 2 for p in o.data.polygons)
        if tris > self.target_tris:
            dm = o.modifiers.new('decimate', 'DECIMATE')
            dm.ratio = self.target_tris / tris
            bpy.ops.object.modifier_apply(modifier='decimate')
        for p in o.data.polygons:
            p.use_smooth = True
        A.paint(o, '#ffffff', self.material)
        self._paint_and_weight(o)
        return o

    def _paint_and_weight(self, o):
        me = o.data
        solids = [m for m in self.masses if not m['neg']]
        vcol, vbones = [], []
        for v in me.vertices:
            p = v.co
            infl = []
            for m in solids:
                q = self._level(m, p)
                f = max(0.0, 1.45 - q)
                infl.append(f * m['w'])
            # colour: sharp blend so regions read as painted areas with soft edges
            cw = [f ** 9 for f in infl]
            tot = sum(cw) or 1.0
            col = [0.0, 0.0, 0.0, 0.0]
            for m, w in zip(solids, cw):
                if w <= 0:
                    continue
                c = rgba(m['color'](p)) if callable(m['color']) else rgba(m['color'])
                for i in range(4):
                    col[i] += c[i] * w / tot
            if tot == 1.0 and not any(cw):
                nearest = min((m for m in solids if not m['ghost']), key=lambda m: self._level(m, p))
                col = list(rgba(nearest['color'](p)) if callable(nearest['color']) else rgba(nearest['color']))
            vcol.append(tuple(col))
            # weights: smoother blend across joints
            bw = {}
            for m, f in zip(solids, infl):
                if f > 0 and not m['ghost']:
                    bw[m['bone']] = bw.get(m['bone'], 0.0) + f ** 3
            if not bw:
                nearest = min((m for m in solids if not m['ghost']), key=lambda m: self._level(m, p))
                bw = {nearest['bone']: 1.0}
            top = sorted(bw.items(), key=lambda kv: -kv[1])[:3]
            s = sum(w for _, w in top)
            vbones.append([(b, w / s) for b, w in top if w / s > 0.02])
        attr = me.color_attributes['Col']
        for loop in me.loops:
            attr.data[loop.index].color_srgb = vcol[loop.vertex_index]
        groups = {}
        for i, bw in enumerate(vbones):
            for b, w in bw:
                g = groups.get(b) or o.vertex_groups.new(name=b)
                groups[b] = g
                g.add([i], w, 'REPLACE')

    def _bake_ao(self, body):
        sc = bpy.context.scene
        if sc.world is None:
            sc.world = bpy.data.worlds.new('AO')
        lo = min((body.matrix_world @ v.co).z for v in body.data.vertices)
        hi = max((body.matrix_world @ v.co).z for v in body.data.vertices)
        sc.world.light_settings.distance = max(0.08, (hi - lo) * 0.22)
        me = body.data
        ao = me.color_attributes.new('AO', 'BYTE_COLOR', 'CORNER')
        me.color_attributes.active_color = ao
        engine = sc.render.engine
        sc.render.engine = 'CYCLES'
        sc.cycles.device = 'CPU'
        sc.cycles.samples = 48
        sc.render.bake.target = 'VERTEX_COLORS'
        bpy.ops.object.select_all(action='DESELECT')
        bpy.context.view_layer.objects.active = body
        body.select_set(True)
        bpy.ops.object.bake(type='AO')
        sc.render.engine = engine
        col = me.color_attributes['Col']
        names = [m.name.split('.')[0] for m in me.materials]
        for p in me.polygons:
            if names[p.material_index] == 'M_Emit':
                continue
            for li in p.loop_indices:
                a = ao.data[li].color[0] ** 0.75
                k = 1.0 - self.ao_strength * (1.0 - a)
                c = col.data[li].color_srgb
                col.data[li].color_srgb = (c[0] * k, c[1] * k, c[2] * k, c[3])
        me.color_attributes.remove(me.color_attributes['AO'])
        me.color_attributes.active_color = me.color_attributes['Col']

    def skin(self, rig):
        organic = self._organic()
        objs = [organic]
        for bone, parts in self.parts.items():
            for p in parts:
                A.bind(p, bone)
                objs.append(p)
        body = A.join(objs, 'Body')
        self._bake_ao(body)
        md = body.modifiers.new('Armature', 'ARMATURE')
        md.object = rig
        body.parent = rig
        return body
