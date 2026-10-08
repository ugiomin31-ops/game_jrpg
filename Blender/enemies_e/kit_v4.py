"""Monster v4 helpers on top of the sculpted kit (enemies_d/sculpt_kit.py).

* `Sculpt` is used unchanged for regular and elite monsters (same bones, Animator kinds and seven clips).
* `spine`/`spines` add rigid, two-tone cones (urchin and puffer spines, teeth, barnacles) aimed along a direction,
  `fibo` spreads directions evenly over a sphere.
* `BossSculpt` builds bosses (4-5 m) with the same kit: the voxel size scales with the creature, the Animator's
  translation scale follows the real height (the regular kit clamps it for 1 m monsters), the eighth clip `Roar`
  is keyed, and the output follows the boss conventions of Blender/bosses (boss_<id>.blend, six 720 px previews).
"""
import json
import math
import os
import sys

import bpy  # noqa: E402

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, '..', 'enemies_d'))
from sculpt_kit import Sculpt as SculptBase, A, lerp_col, vgrad, belly, rgba, hexmix  # noqa: E402,F401
import monster_kit as MK  # noqa: E402
from monster_kit import (Animator, CLIPS, Motion, DIE_HOLD, attack_env, cast_env, hit_env, die_env, window, bump,  # noqa: E402,F401
                         ramp, soft, arc)
from mathutils import Vector  # noqa: E402

TAU = math.tau


def fibo(n, seed=0.0):
    """n unit directions spread evenly over a sphere (Fibonacci lattice)."""
    out = []
    ga = math.pi * (3 - math.sqrt(5))
    for i in range(n):
        z = 1 - 2 * (i + 0.5) / n
        r = math.sqrt(max(0.0, 1 - z * z))
        a = ga * i + seed
        out.append(Vector((r * math.cos(a), r * math.sin(a), z)))
    return out


def spine(c, bone, name, base, direction, length, r, color, tip=None, mat='M_Toon', seg=7):
    """Rigid cone from base along direction; colour fades to `tip` toward the point."""
    d = Vector(direction).normalized()
    o = A.cyl(name, r=r, depth=length, loc=(0, 0, length / 2), r2=0.0, color=color, mat=mat, seg=seg)
    A.apply_transform(o)
    if tip:
        attr = o.data.color_attributes['Col']
        for loop in o.data.loops:
            z = o.data.vertices[loop.vertex_index].co.z / length
            attr.data[loop.index].color_srgb = lerp_col(color, tip, (z - 0.25) / 0.6)
    o.location = Vector(base)
    o.rotation_mode = 'QUATERNION'
    o.rotation_quaternion = d.to_track_quat('Z', 'Y')
    return c.add(bone, o)


def ellipsoid_point(center, radii, d, out=0.0):
    """Point on an ellipsoid (centre, half-sizes) in direction d, pushed `out` along the surface normal."""
    d = Vector(d).normalized()
    rx, ry, rz = radii
    k = 1.0 / math.sqrt((d.x / rx) ** 2 + (d.y / ry) ** 2 + (d.z / rz) ** 2)
    p = Vector(center) + d * k
    n = Vector(((p.x - center[0]) / rx ** 2, (p.y - center[1]) / ry ** 2, (p.z - center[2]) / rz ** 2)).normalized()
    return p + n * out, n


def teeth(c, bone, pts, inward, length, r, color='#f6eedc'):
    """A row of fangs at pts, pointing along `inward` (a vector or a function of the point)."""
    for k, p in enumerate(pts):
        d = inward(Vector(p)) if callable(inward) else Vector(inward)
        spine(c, bone, f'tooth_{bone}_{k}_{len(c.parts[bone])}', p, d, length, r, color, tip='#ffffff', seg=6)


def blade(c, bone, name, base, length, width, color, edge=None, depth=0.02, tip_len=0.18, guard=None, axis=(0, 0, 1),
          mat='M_Toon'):
    """Flat sword blade from base along +Z (then aimed along axis); the flat faces -Y."""
    w = width / 2
    pts = [(-w, 0), (-w, length * (1 - tip_len)), (0, length), (w, length * (1 - tip_len)), (w, 0)]
    o = A.extrude_shape(name, pts, depth=depth, color=color, mat=mat)
    if edge:
        attr = o.data.color_attributes['Col']
        for loop in o.data.loops:
            v = o.data.vertices[loop.vertex_index].co
            if abs(v.x) > w * 0.62 or v.z > length * (1 - tip_len) + 0.01:
                attr.data[loop.index].color_srgb = rgba(edge)
    o.location = Vector(base)
    o.rotation_mode = 'QUATERNION'
    o.rotation_quaternion = Vector(axis).to_track_quat('Z', 'Y')
    return c.add(bone, o)


class Sculpt(SculptBase):
    """The v3 sculpted kit plus `post`: an optional fn(position, normal, colour) -> colour applied to the fused
    surface after the mass colours (moss on up-facing stone, wet sheen on top of armour, ...)."""
    post = None

    def _paint_and_weight(self, o):
        super()._paint_and_weight(o)
        if not self.post:
            return
        me = o.data
        attr = me.color_attributes['Col']
        cache = {}
        for loop in me.loops:
            vi = loop.vertex_index
            if vi not in cache:
                v = me.vertices[vi]
                cache[vi] = self.post(v.co, v.normal, tuple(attr.data[loop.index].color_srgb))
            attr.data[loop.index].color_srgb = cache[vi]


def lathe_helm(c, bone, name, center, r, h, color, profile=None, seg=24, scale=(1, 1, 1)):
    """Rigid helmet/bucket shape turned around Z at `center` (r: radius, h: height); returns the object so the
    caller can paint slits/visors with `paint_where`."""
    prof = profile or [(r * 0.94, -h * 0.5), (r, -h * 0.22), (r * 0.99, h * 0.12), (r * 0.88, h * 0.34), (r * 0.6, h * 0.48),
                       (r * 0.2, h * 0.53), (0.0, h * 0.535)]
    o = A.lathe(name, prof, loc=center, color=color, seg=seg, scale=scale)
    A.apply_transform(o)
    A.shade_smooth(o)
    return c.add(bone, o)


def paint_where(o, test, color):
    """Recolour the corners of `o` whose (world-space, transforms applied) vertex passes test(co)."""
    attr = o.data.color_attributes['Col']
    col = rgba(color)
    for loop in o.data.loops:
        if test(o.data.vertices[loop.vertex_index].co):
            attr.data[loop.index].color_srgb = col
    return o


def dome(name, center, radii, cut=-0.25, color='#888888', seg=20, rings=10, mat='M_Toon'):
    """Shallow shell (pauldron lame, shell plate): an ellipsoid whose underside below `cut` (fraction of the z radius)
    is flattened into a lip."""
    o = A.sphere(name, r=1, loc=center, scale=radii, color=color, seg=seg, rings=rings, mat=mat)
    for v in o.data.vertices:
        if v.co.z < cut:
            v.co.z = cut + (v.co.z - cut) * 0.15
    A.apply_transform(o)
    return o


class BossSculpt(Sculpt):
    """Sculpted boss: same kit, boss output conventions, an extra `Roar` clip."""

    ROAR = 48
    PREVIEWS = [('front', (72, 0, 32), 'Idle', 0), ('side', (80, 0, 90), 'Idle', 0), ('back', (70, 0, 160), 'Idle', 0),
                ('attack', (72, 0, 32), 'Attack', 10), ('cast', (72, 0, 32), 'Cast', 21), ('die', (72, 0, 32), 'Die', 30)]

    def __init__(self, eid, scale=1.0, voxel=0.0065, tris=22000, **kw):
        """The boss is modelled at monster size (about 1.4 m) and enlarged by `scale` before rigging, so the same
        kit proportions, voxel detail and part sizes carry over."""
        super().__init__(eid, voxel=voxel * scale, tris=tris, **kw)
        self.scale = scale

    def _upscale(self):
        from mathutils import Matrix
        k = self.scale
        if k == 1.0:
            return
        for m in self.masses:
            m['co'] = m['co'] * k
            m['r'] = m['r'] * k
        self.bones = [(n, tuple(Vector(h) * k), tuple(Vector(h) * k + Vector((0, 0, 0.1 * k))), p) for n, h, _, p in self.bones]
        bpy.context.view_layer.update()
        S = Matrix.Scale(k, 4)
        for parts in self.parts.values():
            for o in parts:
                o.matrix_world = S @ o.matrix_world
        bpy.context.view_layer.update()

    def animate(self, kind='biped', extra=None):
        rig = A.armature(self.bones)
        anim = Animator(self.bones, self.parts, kind, self.masses, self.follow, self.arm_limit)
        anim.S = anim.H / 0.8 * 0.55  # a 4 m boss moves in metres like a scaled-up 1 m monster, a little heavier
        names = anim.names
        clips = dict(CLIPS)
        clips['Roar'] = self.ROAR
        for clip, length in clips.items():
            src = 'Cast' if clip == 'Roar' else clip
            with Motion(rig, clip, length) as a:
                a.anim = anim
                for f in range(length + 1):
                    anim.write(a, src, f, length)
                    if extra:
                        t = min(f / length, DIE_HOLD) if clip == 'Die' else f / length
                        a.P = anim.at(src, t)
                        extra(a, clip, f, t, f, names)
        body = self.skin(rig)
        return rig, body

    def finish(self, kind='biped', extra=None, previews=None):
        self._upscale()
        rig, body = self.animate(kind, extra)
        A.volume_shade(body)
        tris = sum(len(p.vertices) - 2 for p in body.data.polygons)
        need = list(CLIPS) + ['Roar']
        if not all(n in bpy.data.actions for n in need):
            raise RuntimeError('Missing boss action')
        mats = [m.name for m in body.data.materials]
        if any(m not in A.MATERIALS for m in mats):
            raise RuntimeError(f'Unexpected materials {mats}')
        rig.animation_data.action = bpy.data.actions['Idle']
        bpy.context.scene.frame_set(0)
        path = A.export_fbx(f'Enemies/{self.eid}/{self.eid}.fbx', [rig, body], animated=True)
        A.save_blend('boss_' + self.eid)
        for suffix, angle, clip, frame in previews or self.PREVIEWS:
            A.render_preview(f'boss_{self.eid}_{suffix}', objects=[rig, body], action=clip, frame=frame, angle=angle, size=720)
        manifest = {'id': self.eid, 'fbx': path, 'triangles': tris, 'bones': list(self.parts),
                    'dimensions': [round(v, 3) for v in body.dimensions],
                    'clips': {n: list(bpy.data.actions[n].frame_range) for n in need}, 'materials': mats}
        print('ENEMY_EXPORT ' + json.dumps(manifest), flush=True)
        return manifest


def paint_fn(o, fn):
    """Recolour every corner of `o` with fn(world-space vertex position) (transforms applied)."""
    attr = o.data.color_attributes['Col']
    cache = {}
    for loop in o.data.loops:
        vi = loop.vertex_index
        if vi not in cache:
            cache[vi] = rgba(fn(o.data.vertices[vi].co.copy()))
        attr.data[loop.index].color_srgb = cache[vi]
    return o


def scale_region(c, bones, pivot, k, masses_from=0):
    """Enlarge everything built so far on `bones` (fused masses from index `masses_from` on, and rigid parts)
    about `pivot` by k: used to give bosses a bigger, more imposing head without retyping every offset."""
    from mathutils import Matrix
    pv = Vector(pivot)
    for m in c.masses[masses_from:]:
        if m['bone'] in bones or (m['bone'] is None and (m['co'] - pv).length < 0.4):
            m['co'] = pv + (m['co'] - pv) * k
            m['r'] = m['r'] * k
    bpy.context.view_layer.update()
    M = Matrix.Translation(pv) @ Matrix.Scale(k, 4) @ Matrix.Translation(-pv)
    for b in bones:
        for o in c.parts.get(b, []):
            o.matrix_world = M @ o.matrix_world
    bpy.context.view_layer.update()
