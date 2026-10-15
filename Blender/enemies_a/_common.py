"""Shared helpers for the enemies_a group (slime, sprout, mushroom, bat family, jellyfish,
coral_crab, penguin_mage, ice_wolf + elites).

Conventions used by every generator here:
- Every bone points straight up (+Z) with roll 0, so its local axes are: X = world X,
  Y = world Z (up), Z = world -Y (front). `Act` wraps `A.Anim` so animation code is written
  in WORLD axes:  a.r(bone, f, ax, ay, az)  rotates about world X / Y / Z (degrees),
                  a.l(bone, f, x, y, z)     offsets in world metres,
                  a.s(bone, f, x, y, z)     scales along world axes.
  Sign cheat-sheet (creature faces -Y):  +ax = top tips forward (bow / jaw opens),
  +ay = top leans to the creature's left (+X), +az = turns its face toward +X.
- Generators take the variant id as the first argument after `--`
  (e.g. `blender -b --factory-startup -P mushroom.py -- elite_mushroom`).
"""
import math
import os
import sys

sys.path.append(r"C:\Users\User\Desktop\game\Blender\lib")
import abyss_bpy as A  # noqa: E402

import bmesh  # noqa: E402
import bpy  # noqa: E402
from mathutils import Matrix, Vector  # noqa: E402

REQUIRED_ACTIONS = ("Idle", "Run", "Attack", "Cast", "Hit", "Die", "Victory")


def variant(default):
    argv = sys.argv
    if "--" in argv:
        rest = argv[argv.index("--") + 1:]
        if rest:
            return rest[0]
    return default


def rgb(c):
    return A._as_rgba(c)


def mix(a, b, t):
    a, b = rgb(a), rgb(b)
    return tuple(a[i] * (1 - t) + b[i] * t for i in range(4))


def tinted(c, tint, k=1.0):
    """Multiply a colour by a data tint (partially, k=0..1)."""
    c = rgb(c)
    return tuple(c[i] * (1 - k + k * tint[i]) for i in range(3)) + (1.0,)


# ---------------------------------------------------------------- colour

def paint_fn(o, fn, mat=None):
    """Per-face colour: fn(face_center_local, face_normal_local, face_index) -> colour."""
    me = o.data
    if "Col" not in me.color_attributes:
        me.color_attributes.new("Col", "BYTE_COLOR", "CORNER")
    attr = me.color_attributes["Col"]
    for p in me.polygons:
        c = rgb(fn(p.center, p.normal, p.index))
        for li in p.loop_indices:
            attr.data[li].color_srgb = c
    if mat:
        me.materials.clear()
        me.materials.append(A._material(mat))
        for p in me.polygons:
            p.material_index = 0
    return o


def paint_vert_fn(o, fn):
    """Per-vertex colour (smooth blends): fn(vertex_co_local) -> colour."""
    me = o.data
    if "Col" not in me.color_attributes:
        me.color_attributes.new("Col", "BYTE_COLOR", "CORNER")
    attr = me.color_attributes["Col"]
    for loop in me.loops:
        attr.data[loop.index].color_srgb = rgb(fn(me.vertices[loop.vertex_index].co))
    return o


def set_mat(o, mat):
    me = o.data
    me.materials.clear()
    me.materials.append(A._material(mat))
    for p in me.polygons:
        p.material_index = 0
    return o


# ---------------------------------------------------------------- placement

def basis(fwd, up=(0, 0, 1)):
    """Rotation whose local -Y points along fwd and local +Z is as close to up as possible."""
    f = Vector(fwd).normalized()
    y = -f
    u = Vector(up)
    z = u - y * u.dot(y)
    if z.length < 1e-4:
        z = Vector((0, 0, 1)) if abs(y.z) < 0.9 else Vector((0, 1, 0))
        z = z - y * z.dot(y)
    z.normalize()
    x = y.cross(z)
    m = Matrix((x, y, z)).transposed()
    return m


def orient(o, loc, fwd, up=(0, 0, 1), offset=0.0):
    """Bake o's own transform, then place it at loc with local -Y facing fwd."""
    A.apply_transform(o)
    o.matrix_world = Matrix.Translation(Vector(loc) + Vector(fwd).normalized() * offset) @ basis(fwd, up).to_4x4()
    A.apply_transform(o)
    return o


def surf(target, center, direction):
    """Ray-cast from outside toward center along -direction. Returns (location, normal) in world.
    target must have identity transform (apply_transform first)."""
    bpy.context.view_layer.update()
    d = Vector(direction).normalized()
    origin = Vector(center) + d * 10.0
    ok, loc, nor, _ = target.ray_cast(origin, -d)
    if not ok:
        raise RuntimeError(f"surf miss on {target.name} from {direction}")
    return loc, nor


def dir_from(yaw, pitch):
    """Direction for a point on a creature facing -Y. yaw: + toward creature's left (+X), pitch: + up."""
    y, p = math.radians(yaw), math.radians(pitch)
    return Vector((math.sin(y) * math.cos(p), -math.cos(y) * math.cos(p), math.sin(p)))


def dup(o, name=None):
    c = o.copy()
    c.data = o.data.copy()
    c.name = name or (o.name + "_dup")
    bpy.context.scene.collection.objects.link(c)
    return c


def mirror(o, name=None):
    return A.mirror_x(o, name or (o.name + "_R"))


def solidify(o, t=0.01):
    md = o.modifiers.new("solid", "SOLIDIFY")
    md.thickness = t
    md.offset = 0.0
    md.use_even_offset = True
    A.apply_modifiers(o)
    return o


def recalc_normals(o):
    bm = bmesh.new()
    bm.from_mesh(o.data)
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    bm.to_mesh(o.data)
    bm.free()
    o.data.update()
    return o


# ---------------------------------------------------------------- shape kits

def ellipsoid(name, radii, loc=(0, 0, 0), color="#888888", mat="M_Toon", seg=24, rings=14):
    o = A.sphere(name, r=1.0, loc=loc, scale=radii, color=color, mat=mat, seg=seg, rings=rings)
    A.apply_transform(o)
    return o


def leaf(name, length=0.2, width=0.09, fold=0.25, curl=0.35, segs=6, light="#7fd14a", dark="#4c9a2c",
         thick=0.008, tip_pinch=1.0):
    """Two-tone folded leaf along local +Y (base at origin), lying in XY plane, normal +Z.
    fold: midrib V depth relative to width; curl: tip droop (radians-ish) bending down -Z."""
    bm = bmesh.new()
    rows = []
    for i in range(segs + 1):
        t = i / segs
        w = width * 0.5 * math.sin(math.pi * min(1.0, t ** 0.8)) ** tip_pinch
        y = t * length
        bend = curl * t * t * length
        row = [bm.verts.new((-w, y, -bend - w * fold * 0.0)),
               bm.verts.new((0, y, -bend + w * fold)),
               bm.verts.new((w, y, -bend - w * fold * 0.0))]
        rows.append(row)
    for a, b in zip(rows, rows[1:]):
        for j in range(2):
            vs = [a[j], a[j + 1], b[j + 1], b[j]]
            # collapse degenerate quads at base/tip (w=0)
            uniq = []
            for v in vs:
                if all((v.co - u.co).length > 1e-6 for u in uniq):
                    uniq.append(v)
            if len(uniq) >= 3:
                try:
                    bm.faces.new(uniq)
                except ValueError:
                    pass
    bmesh.ops.remove_doubles(bm, verts=bm.verts, dist=1e-6)
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    for f in bm.faces:
        if f.normal.z < 0:
            f.normal_flip()
    me = bpy.data.meshes.new(name)
    bm.to_mesh(me)
    bm.free()
    o = A._new_obj(name, me)
    paint_fn(o, lambda c, n, i: dark if c.x > 0 else light, "M_Toon")
    solidify(o, thick)
    A.shade_smooth(o)
    return o


def skin_leaf(name, target, center, yaw, pitch, length=0.15, width=0.08, curl=0.8, lift=0.25, back=0.3,
              light="#8fdc4e", dark="#4a9a2c", fold=0.3, spin=0.0):
    """Leaf lying on target's surface, rooted up-slope at dir_from(yaw, pitch) and hanging downhill.
    spin rotates the downhill direction around the surface normal (degrees)."""
    p, n = surf(target, center, dir_from(yaw, pitch))
    down = Vector((0, 0, -1))
    t = down - n * down.dot(n)
    if t.length < 1e-3:
        h = dir_from(yaw, 0)
        t = h - n * h.dot(n)
    t.normalize()
    if spin:
        t = Matrix.Rotation(math.radians(spin), 3, n) @ t
    d = (t + n * lift).normalized()
    lf = leaf(name, length=length, width=width, fold=fold, curl=curl, light=light, dark=dark)
    return place_leaf(lf, p + n * 0.008 - t * length * back, d, up=n)


def place_leaf(lf, base, direction, up=(0, 0, 1), roll=0.0):
    """Point the leaf's +Y along direction from base; leaf normal near up."""
    d = Vector(direction).normalized()
    u = Vector(up)
    z = u - d * u.dot(d)
    if z.length < 1e-4:
        z = Vector((1, 0, 0))
    z.normalize()
    x = d.cross(z)
    m = Matrix((x, d, z)).transposed().to_4x4()
    if roll:
        m = m @ Matrix.Rotation(math.radians(roll), 4, "Y")
    lf.matrix_world = Matrix.Translation(base) @ m
    A.apply_transform(lf)
    return lf


def crystal(name, r=0.06, h=0.3, light="#bff0ff", dark="#4aa6e8", mat="M_Emit", sides=6, taper=0.85, base_pt=0.12):
    """Faceted bipyramid crystal along local +Z (base at origin), two-tone facets, flat shaded."""
    prof = [(0.0, -h * base_pt), (r, h * 0.08), (r * taper, h * 0.72), (0.0, h)]
    bm = bmesh.new()
    rings = []
    for (rad, z) in prof:
        ring = []
        for i in range(sides):
            a = 2 * math.pi * (i + 0.5) / sides
            ring.append(bm.verts.new((math.cos(a) * rad, math.sin(a) * rad, z)))
        rings.append(ring)
    for a, b in zip(rings, rings[1:]):
        for i in range(sides):
            j = (i + 1) % sides
            bm.faces.new((a[i], a[j], b[j], b[i]))
    bmesh.ops.remove_doubles(bm, verts=bm.verts, dist=1e-6)
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    me = bpy.data.meshes.new(name)
    bm.to_mesh(me)
    bm.free()
    o = A._new_obj(name, me)
    for p in o.data.polygons:
        p.use_smooth = False

    def col(c, n, i):
        k = (math.atan2(n.y, n.x) / (2 * math.pi) + 1.0) % 1.0
        shade = 0.5 + 0.5 * math.cos(2 * math.pi * (k - 0.15))
        if c.z > h * 0.72:
            shade = min(1.0, shade + 0.35)
        return mix(dark, light, shade)
    paint_fn(o, col, mat)
    return o


def aim(o, base, direction, roll=0.0):
    """Rotate object built along local +Z so +Z points along direction, then move to base."""
    d = Vector(direction).normalized()
    q = Vector((0, 0, 1)).rotation_difference(d)
    m = q.to_matrix().to_4x4()
    if roll:
        m = m @ Matrix.Rotation(math.radians(roll), 4, "Z")
    A.apply_transform(o)
    o.matrix_world = Matrix.Translation(base) @ m
    A.apply_transform(o)
    return o


def cute_eye(name, loc, normal, w=0.07, h=0.09, iris="#2a3a8a", pupil="#121528", hl="#ffffff",
             up=(0, 0, 1), depth=0.025, lid=None):
    """Big anime eye on a surface: dark oval + iris lower half + 2 highlights (all outward along normal)."""
    parts = []
    base = A.sphere(name, r=1.0, scale=(w, depth, h), color=pupil, seg=20, rings=10)
    parts.append(orient(base, loc, normal, up, offset=0.0))
    if iris:
        ir = A.sphere(name + "_iris", r=1.0, scale=(w * 0.72, depth * 0.7, h * 0.5), color=iris, seg=16, rings=8)
        n = Vector(normal).normalized()
        b = basis(n, up)
        upv = b.col[2]
        parts.append(orient(ir, Vector(loc) - upv * h * 0.38, n, up, offset=depth * 0.42))
    n = Vector(normal).normalized()
    b = basis(n, up)
    upv, side = b.col[2], b.col[0]
    h1 = A.sphere(name + "_hl1", r=1.0, scale=(w * 0.32, depth * 0.6, h * 0.26), color=hl, seg=12, rings=6)
    parts.append(orient(h1, Vector(loc) + upv * h * 0.38 - side * w * 0.28, n, up, offset=depth * 0.6))
    h2 = A.sphere(name + "_hl2", r=1.0, scale=(w * 0.16, depth * 0.6, h * 0.13), color=hl, seg=10, rings=6)
    parts.append(orient(h2, Vector(loc) - upv * h * 0.42 + side * w * 0.35, n, up, offset=depth * 0.6))
    if lid:
        ld = A.sphere(name + "_lid", r=1.0, scale=(w * 1.12, depth * 0.8, h * 0.3), color=lid, seg=16, rings=6)
        parts.append(orient(ld, Vector(loc) + upv * h * 0.86, n, up, offset=depth * 0.3))
    return parts


def glow_eye(name, loc, normal, w=0.05, h=0.07, color="#ffe066", depth=0.02, up=(0, 0, 1)):
    o = A.sphere(name, r=1.0, scale=(w, depth, h), color=color, mat="M_Emit", seg=16, rings=8)
    return orient(o, loc, normal, up)


def disc_shape(name, pts2d, loc, normal, color, depth=0.01, mat="M_Toon", up=(0, 0, 1), offset=0.0):
    """Flat outline (x across, z up) on a surface, facing outward along normal."""
    o = A.extrude_shape(name, pts2d, depth=depth, color=color, mat=mat)
    return orient(o, loc, normal, up, offset)


def arc_pts(rx, rz, a0, a1, n, cx=0.0, cz=0.0):
    return [(cx + rx * math.cos(math.radians(a0 + (a1 - a0) * i / (n - 1))),
             cz + rz * math.sin(math.radians(a0 + (a1 - a0) * i / (n - 1)))) for i in range(n)]


def smile_mouth(name, loc, normal, w=0.06, h=0.05, up=(0, 0, 1), inner="#7a1f2e", tongue="#ff7f8f", fang=None):
    """Open 'D' smile: flat top, round bottom, with tongue. fang: colour -> two little fangs."""
    pts = arc_pts(w, h, 180, 360, 12)
    parts = [disc_shape(name, pts, loc, normal, inner, depth=0.012, up=up)]
    tpts = arc_pts(w * 0.62, h * 0.55, 180, 360, 10, cz=-h * 0.42)
    tpts = [(x, max(z, -h * 0.97)) for x, z in tpts]
    parts.append(disc_shape(name + "_tongue", tpts, loc, normal, tongue, depth=0.012, up=up, offset=0.003))
    if fang:
        for s in (-1, 1):
            fp = [(s * w * 0.75, 0.0), (s * w * 0.42, 0.0), (s * w * 0.6, -h * 0.55)]
            parts.append(disc_shape(name + f"_fang{s}", fp, loc, normal, fang, depth=0.014, up=up, offset=0.004))
    return parts


def claw(name, base, direction, length=0.06, r=0.012, color="#f2e6d0", curve=0.4, up=(0, 0, 1), seg=8):
    d = Vector(direction).normalized()
    u = Vector(up)
    side = d.cross(u)
    if side.length < 1e-4:
        side = Vector((1, 0, 0))
    bend = side.cross(d).normalized()
    pts = []
    for i in range(5):
        t = i / 4
        p = Vector(base) + d * length * t - bend * curve * length * t * t
        pts.append(tuple(p))
    return A.tube(name, pts, radius=r, color=color, seg=seg, taper_end=0.05)


def count_tris(o):
    return sum(len(p.vertices) - 2 for p in o.data.polygons)


# ---------------------------------------------------------------- rig + anim

def make_rig(bones, length=0.08):
    """bones: list of (name, head(x,y,z), parent). All bones point +Z (see module doc)."""
    spec = []
    for name, head, parent in bones:
        h = Vector(head)
        spec.append((name, tuple(h), tuple(h + Vector((0, 0, length))), parent))
    return A.armature(spec)


class Act(A.Anim):
    """A.Anim in world-axis terms (valid because every bone points +Z with roll 0)."""

    def r(self, bone, f, ax=0.0, ay=0.0, az=0.0):
        self.rot(bone, f, (ax, az, -ay))

    def l(self, bone, f, x=0.0, y=0.0, z=0.0):
        self.loc(bone, f, (x, z, -y))

    def s(self, bone, f, x=1.0, y=1.0, z=1.0):
        self.scl(bone, f, (x, z, y))

    def su(self, bone, f, k=1.0):
        self.scl(bone, f, (k, k, k))

    def loop_r(self, bone, n, fn):
        """Key n+1 evenly spaced rotation keys over the action; fn(t in 0..1) -> (ax, ay, az)."""
        for i in range(n + 1):
            t = i / n
            self.r(bone, round(self.length * t), *fn(t % 1.0))

    def loop_l(self, bone, n, fn):
        for i in range(n + 1):
            t = i / n
            self.l(bone, round(self.length * t), *fn(t % 1.0))

    def loop_s(self, bone, n, fn):
        for i in range(n + 1):
            t = i / n
            self.s(bone, round(self.length * t), *fn(t % 1.0))

    def keys_r(self, bone, keys):
        for f, v in keys:
            self.r(bone, f, *v)

    def keys_l(self, bone, keys):
        for f, v in keys:
            self.l(bone, f, *v)

    def keys_s(self, bone, keys):
        for f, v in keys:
            if isinstance(v, (int, float)):
                v = (v, v, v)
            self.s(bone, f, *v)


def S(t, phase=0.0):
    return math.sin(2 * math.pi * (t + phase))


def C(t, phase=0.0):
    return math.cos(2 * math.pi * (t + phase))


def set_linear_hold_last(action_name):
    """Make the last key of Die hold (constant extrapolation is default). No-op helper kept simple."""
    return bpy.data.actions.get(action_name)


# ---------------------------------------------------------------- finish

def check_actions(rig, required=REQUIRED_ACTIONS):
    names = {a.name for a in bpy.data.actions}
    missing = [n for n in required if n not in names]
    if missing:
        raise RuntimeError(f"missing actions: {missing}")
    for n in required:
        act = bpy.data.actions[n]
        print(f"[enemies_a] action {n}: frames {tuple(act.frame_range)}")


def finish(eid, rig, body, previews=True, extra=()):
    """Verify, export FBX, save .blend, render previews. Returns FBX path."""
    check_actions(rig)
    assert rig.name == "Rig", rig.name
    assert body.name == "Body", body.name
    mats = [m.name for m in body.data.materials]
    assert all(m in A.MATERIALS for m in mats), mats
    tris = count_tris(body)
    print(f"[enemies_a] {eid}: tris={tris} mats={mats} bones={len(rig.data.bones)}")
    path = A.export_fbx(f"Enemies/{eid}/{eid}.fbx", objects=[rig, body], animated=True)
    assert os.path.exists(path), path
    print(f"[enemies_a] exported {path}")
    A.save_blend(f"enemy_{eid}")
    if previews:
        A.render_preview(f"enemy_{eid}", angle=(70, 0, 35), action="Idle", frame=0)
        A.render_preview(f"enemy_{eid}_side", angle=(80, 0, 90), action="Idle", frame=0)
        att = bpy.data.actions["Attack"]
        A.render_preview(f"enemy_{eid}_attack", angle=(75, 0, 55), action="Attack",
                         frame=round(att.frame_range[1] * 0.4))
        for (suffix, act, frac, ang) in extra:
            a = bpy.data.actions[act]
            A.render_preview(f"enemy_{eid}_{suffix}", angle=ang, action=act, frame=round(a.frame_range[1] * frac))
    return path
