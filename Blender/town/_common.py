"""Town-group helpers: a fast batched mesh builder (per-face colour/material/smooth),
collision boxes, Spot_/LightAnchor empties and preview cameras.

Generators import:  sys.path.append(<this dir>); from _common import *
"""
import math
import os
import random
import sys

import bmesh
import bpy
import numpy as np
from mathutils import Euler, Matrix, Vector, noise

sys.path.append(os.path.join(os.path.dirname(os.path.abspath(__file__)), '../lib'))
import abyss_bpy as A  # noqa: E402

MATS = ("M_Toon", "M_Emit", "M_Clear")


def rgba(c):
    if isinstance(c, str):
        return A.hexcol(c)
    return tuple(c) if len(c) == 4 else (c[0], c[1], c[2], 1.0)


def mix(a, b, t):
    a, b = rgba(a), rgba(b)
    return tuple(a[i] * (1 - t) + b[i] * t for i in range(4))


def shade(c, f):
    c = rgba(c)
    return (min(c[0] * f, 1), min(c[1] * f, 1), min(c[2] * f, 1), c[3])


def T(x=0.0, y=0.0, z=0.0):
    return Matrix.Translation((x, y, z))


def RZ(deg):
    return Matrix.Rotation(math.radians(deg), 4, "Z")


def RX(deg):
    return Matrix.Rotation(math.radians(deg), 4, "X")


def RY(deg):
    return Matrix.Rotation(math.radians(deg), 4, "Y")


def S(x, y=None, z=None):
    y = x if y is None else y
    z = x if z is None else z
    return Matrix.Diagonal((x, y, z, 1.0))


def rot(rx=0, ry=0, rz=0):
    return Euler((math.radians(rx), math.radians(ry), math.radians(rz))).to_matrix().to_4x4()


def face_angle(dx, dy):
    """Z rotation (deg) that turns the local front (-Y) toward direction (dx, dy)."""
    return math.degrees(math.atan2(dx, -dy))


def smoothstep(a, b, x):
    t = min(max((x - a) / (b - a), 0.0), 1.0)
    return t * t * (3 - 2 * t)


# ---------------------------------------------------------------- batched mesh builder

class MB:
    """Accumulates many primitives into flat arrays (linear time) with per-face colour, material
    and smooth flags. A transform stack (push/pop or `with mb.at(matrix)`) gives local frames."""

    def __init__(self):
        self.V = []          # numpy (n,3) chunks
        self.F = []          # face index lists (global)
        self.FC = []         # colour index per face
        self.FM = []         # material index per face
        self.FS = []         # smooth flag per face
        self.nv = 0
        self.pal = []
        self.palix = {}
        self.stack = [Matrix()]

    @property
    def M(self):
        return self.stack[-1]

    def push(self, m):
        self.stack.append(self.stack[-1] @ m)
        return self

    def pop(self):
        self.stack.pop()

    def at(self, m):
        mb = self

        class _Ctx:
            def __enter__(self_):
                mb.push(m)
                return mb

            def __exit__(self_, *a):
                mb.pop()
        return _Ctx()

    def W(self, p):
        """Local point -> world (current frame)."""
        return self.M @ Vector(p)

    def ci(self, col):
        c = rgba(col)
        key = tuple(round(v, 4) for v in c)
        if key not in self.palix:
            self.palix[key] = len(self.pal)
            self.pal.append(c)
        return self.palix[key]

    # core flush -----------------------------------------------------------
    def _flush(self, bm, m, col, mat, smooth, recalc=True, face_cols=None, flat_ngons=False):
        if recalc:
            bmesh.ops.recalc_face_normals(bm, faces=bm.faces[:])
        bm.verts.index_update()
        co = np.array([v.co[:] for v in bm.verts], dtype=np.float64).reshape(-1, 3)
        M = np.array(self.M @ (m or Matrix()))
        co = co @ M[:3, :3].T + M[:3, 3]
        if np.linalg.det(M[:3, :3]) < 0:
            flip = True
        else:
            flip = False
        off = self.nv
        cidx = self.ci(col)
        midx = MATS.index(mat)
        for k, f in enumerate(bm.faces):
            ids = [v.index + off for v in f.verts]
            if flip:
                ids.reverse()
            self.F.append(ids)
            self.FC.append(self.ci(face_cols[k]) if face_cols and face_cols[k] is not None else cidx)
            self.FM.append(midx)
            self.FS.append(bool(smooth) and not (flat_ngons and len(ids) > 4))
        self.V.append(co)
        self.nv += len(co)
        bm.free()
        return self

    # primitives -------------------------------------------------------------
    def box(self, size, loc=(0, 0, 0), col="#888888", mat="M_Toon", r=(0, 0, 0), m=None, face_cols=None):
        """face_cols order (create_cube): use None. Single colour box."""
        bm = bmesh.new()
        bmesh.ops.create_cube(bm, size=1.0)
        return self._flush(bm, T(*loc) @ rot(*r) @ (m or Matrix()) @ S(*size), col, mat, False)

    def bbox(self, lo, hi, col="#888888", mat="M_Toon"):
        """Axis-aligned box from corner lo to corner hi (local frame)."""
        size = [hi[i] - lo[i] for i in range(3)]
        loc = [(hi[i] + lo[i]) / 2 for i in range(3)]
        return self.box(size, loc, col, mat)

    def pillow(self, size, loc=(0, 0, 0), col="#888888", mat="M_Toon", rz=0.0, inset=0.3, top_col=None, m=None):
        """Box with chamfered top edge, no bottom face (cobble / block / cushion)."""
        sx, sy, sz = size
        bm = bmesh.new()
        hx, hy = sx / 2, sy / 2
        ch = min(sz * 0.5, min(sx, sy) * inset * 0.5)
        ix, iy = hx - ch, hy - ch
        b = [bm.verts.new((x, y, 0)) for x, y in ((-hx, -hy), (hx, -hy), (hx, hy), (-hx, hy))]
        md = [bm.verts.new((x, y, sz - ch)) for x, y in ((-hx, -hy), (hx, -hy), (hx, hy), (-hx, hy))]
        t = [bm.verts.new((x, y, sz)) for x, y in ((-ix, -iy), (ix, -iy), (ix, iy), (-ix, iy))]
        fc = []
        for i in range(4):
            j = (i + 1) % 4
            bm.faces.new((b[i], b[j], md[j], md[i]))
            fc.append(None)
            bm.faces.new((md[i], md[j], t[j], t[i]))
            fc.append(None)
        bm.faces.new(t)
        fc.append(top_col)
        return self._flush(bm, T(*loc) @ RZ(rz) @ (m or Matrix()), col, mat, False, recalc=False, face_cols=fc)

    def cyl(self, r, depth, loc=(0, 0, 0), col="#888888", mat="M_Toon", seg=12, r2=None, rr=(0, 0, 0), smooth=True, m=None, cap=True, scale=(1, 1, 1)):
        bm = bmesh.new()
        bmesh.ops.create_cone(bm, cap_ends=cap, cap_tris=False, segments=seg, radius1=r,
                              radius2=r if r2 is None else r2, depth=depth)
        return self._flush(bm, T(*loc) @ rot(*rr) @ (m or Matrix()) @ S(*scale), col, mat, smooth, recalc=cap, flat_ngons=True)

    def cone(self, r, depth, loc=(0, 0, 0), col="#888888", **kw):
        return self.cyl(r, depth, loc=loc, col=col, r2=0.0, **kw)

    def ico(self, r, loc=(0, 0, 0), col="#888888", mat="M_Toon", sub=1, scale=(1, 1, 1), smooth=True, jitter=0.0, seed=0.0, m=None):
        bm = bmesh.new()
        bmesh.ops.create_icosphere(bm, subdivisions=sub, radius=r)
        if jitter:
            off = Vector((seed * 3.1, seed * 1.7, seed * 0.3))
            for v in bm.verts:
                n = noise.noise(v.co * (1.8 / max(r, 1e-3)) + off)
                v.co *= 1.0 + jitter * n
        return self._flush(bm, T(*loc) @ (m or Matrix()) @ S(*scale), col, mat, smooth)

    def sphere(self, r, loc=(0, 0, 0), col="#888888", mat="M_Toon", seg=12, rings=8, scale=(1, 1, 1), m=None, smooth=True):
        bm = bmesh.new()
        bmesh.ops.create_uvsphere(bm, u_segments=seg, v_segments=rings, radius=r)
        return self._flush(bm, T(*loc) @ (m or Matrix()) @ S(*scale), col, mat, smooth)

    def torus(self, R, r, loc=(0, 0, 0), col="#888888", mat="M_Toon", seg=24, minor=8, m=None, arc=1.0):
        bm = bmesh.new()
        rings = []
        n = seg if arc >= 1.0 else seg + 1
        for i in range(n):
            a = 2 * math.pi * arc * i / seg
            c, s = math.cos(a), math.sin(a)
            ring = []
            for j in range(minor):
                b = 2 * math.pi * j / minor
                rr = R + r * math.cos(b)
                ring.append(bm.verts.new((c * rr, s * rr, r * math.sin(b))))
            rings.append(ring)
        pairs = list(zip(rings, rings[1:])) + ([(rings[-1], rings[0])] if arc >= 1.0 else [])
        for ra, rb in pairs:
            for j in range(minor):
                k = (j + 1) % minor
                bm.faces.new((ra[j], rb[j], rb[k], ra[k]))
        if arc < 1.0:
            bm.faces.new(rings[0])
            bm.faces.new(rings[-1])
        return self._flush(bm, T(*loc) @ (m or Matrix()), col, mat, True)

    def lathe(self, profile, loc=(0, 0, 0), col="#888888", mat="M_Toon", seg=16, cols=None, m=None, smooth=True, scale=(1, 1, 1)):
        """profile [(radius, z)] bottom->top, optional per-band colours (len(profile)-1)."""
        bm = bmesh.new()
        rings = []
        for rad, z in profile:
            if rad < 1e-5:
                rings.append([bm.verts.new((0, 0, z))])
            else:
                rings.append([bm.verts.new((math.cos(2 * math.pi * i / seg) * rad, math.sin(2 * math.pi * i / seg) * rad, z)) for i in range(seg)])
        fc = []
        for k, (a, b) in enumerate(zip(rings, rings[1:])):
            c = cols[k] if cols else None
            for i in range(seg):
                j = (i + 1) % seg
                if len(a) == 1 and len(b) == 1:
                    break
                if len(a) == 1:
                    bm.faces.new((a[0], b[j], b[i]))
                elif len(b) == 1:
                    bm.faces.new((a[i], a[j], b[0]))
                else:
                    bm.faces.new((a[i], a[j], b[j], b[i]))
                fc.append(c)
        if len(rings[0]) > 1:
            bm.faces.new(list(reversed(rings[0])))
            fc.append(cols[0] if cols else None)
        if len(rings[-1]) > 1:
            bm.faces.new(rings[-1])
            fc.append(cols[-1] if cols else None)
        return self._flush(bm, T(*loc) @ (m or Matrix()) @ S(*scale), col, mat, smooth, face_cols=fc, flat_ngons=True)

    def prism(self, pts, z0, z1, col="#888888", mat="M_Toon", m=None, top_col=None):
        """Polygon pts [(x, y)] extruded from z0 to z1."""
        bm = bmesh.new()
        lo = [bm.verts.new((x, y, z0)) for x, y in pts]
        hi = [bm.verts.new((x, y, z1)) for x, y in pts]
        n = len(pts)
        fc = [None]
        bm.faces.new(list(reversed(lo)))
        for i in range(n):
            j = (i + 1) % n
            bm.faces.new((lo[i], lo[j], hi[j], hi[i]))
            fc.append(None)
        bm.faces.new(hi)
        fc.append(top_col)
        return self._flush(bm, m, col, mat, False, face_cols=fc)

    def slab(self, pts, depth, col="#888888", mat="M_Toon", m=None, y=0.0):
        """Polygon in the XZ plane [(x, z)] extruded along +Y from y to y+depth (front face at y)."""
        bm = bmesh.new()
        fr = [bm.verts.new((x, y, z)) for x, z in pts]
        bk = [bm.verts.new((x, y + depth, z)) for x, z in pts]
        n = len(pts)
        bm.faces.new(fr)
        for i in range(n):
            j = (i + 1) % n
            bm.faces.new((fr[j], fr[i], bk[i], bk[j]))
        bm.faces.new(list(reversed(bk)))
        return self._flush(bm, m, col, mat, False)

    def tube(self, pts, r, col="#888888", mat="M_Toon", seg=6, r_end=None, smooth=True):
        bm = bmesh.new()
        pts = [Vector(p) for p in pts]
        n = len(pts)
        rings = []
        prev_a = None
        for i, p in enumerate(pts):
            d = (pts[min(i + 1, n - 1)] - pts[max(i - 1, 0)]).normalized()
            if prev_a is None:
                up = Vector((0, 0, 1)) if abs(d.z) < 0.9 else Vector((1, 0, 0))
                a = d.cross(up).normalized()
            else:
                a = (prev_a - d * prev_a.dot(d)).normalized()
            prev_a = a
            b = d.cross(a).normalized()
            rr = r if r_end is None else r + (r_end - r) * i / max(n - 1, 1)
            rings.append([bm.verts.new(p + (a * math.cos(2 * math.pi * k / seg) + b * math.sin(2 * math.pi * k / seg)) * rr) for k in range(seg)])
        for ra, rb in zip(rings, rings[1:]):
            for k in range(seg):
                j = (k + 1) % seg
                bm.faces.new((ra[k], ra[j], rb[j], rb[k]))
        bm.faces.new(list(reversed(rings[0])))
        bm.faces.new(rings[-1])
        return self._flush(bm, None, col, mat, smooth, flat_ngons=True)

    def raw(self, verts, faces, col="#888888", mat="M_Toon", smooth=False, face_cols=None, recalc=False):
        bm = bmesh.new()
        vs = [bm.verts.new(v) for v in verts]
        for f in faces:
            bm.faces.new([vs[i] for i in f])
        return self._flush(bm, None, col, mat, smooth, recalc=recalc, face_cols=face_cols)

    def tris(self):
        return sum(len(f) - 2 for f in self.F)

    def build(self, name, origin=None):
        V = np.concatenate(self.V) if self.V else np.zeros((0, 3))
        if origin is not None:
            V = V - np.array(origin)
        me = bpy.data.meshes.new(name)
        me.from_pydata(V.tolist(), [], self.F)
        me.validate(clean_customdata=False)
        npoly = len(me.polygons)
        fc = np.array(self.FC[:npoly], dtype=np.int64)
        fm = np.array(self.FM[:npoly], dtype=np.int64)
        fs = np.array(self.FS[:npoly], dtype=bool)
        used = sorted(set(fm.tolist()))
        for u in used:
            me.materials.append(A._material(MATS[u]))
        remap = np.zeros(3, dtype=np.int64)
        for k, u in enumerate(used):
            remap[u] = k
        me.polygons.foreach_set("material_index", remap[fm].astype(np.int32))
        me.polygons.foreach_set("use_smooth", fs)
        tot = np.zeros(npoly, dtype=np.int32)
        me.polygons.foreach_get("loop_total", tot)
        pal = np.array(self.pal if self.pal else [(1, 1, 1, 1)], dtype=np.float32)
        loopcol = pal[np.repeat(fc, tot)]
        ca = me.color_attributes.new("Col", "BYTE_COLOR", "CORNER")
        ca.data.foreach_set("color_srgb", loopcol.ravel())
        me.color_attributes.active_color = ca
        me.update()
        o = bpy.data.objects.new(name, me)
        bpy.context.scene.collection.objects.link(o)
        if origin is not None:
            o.location = origin
        return o


# ---------------------------------------------------------------- scene objects

ANCHORS = []
SPOTS = {}
COLS = []


def col_box(name, size, loc, rz=0.0):
    """Invisible collision box (Unity strips the renderer + adds MeshCollider). Object name Col_<name>."""
    name = name if name.startswith("Col_") else "Col_" + name
    mb = MB()
    mb.box(size, (0, 0, 0), "#ff00ff")
    o = mb.build(name)
    o.location = loc
    o.rotation_euler = (0, 0, math.radians(rz))
    o.hide_render = True
    o.display_type = "WIRE"
    COLS.append(o)
    return o


def empty(name, loc, rz=0.0, kind="PLAIN_AXES", size=0.5, matrix=None):
    e = bpy.data.objects.new(name, None)
    e.empty_display_type = kind
    e.empty_display_size = size
    bpy.context.scene.collection.objects.link(e)
    if matrix is not None:
        e.matrix_world = matrix
    else:
        e.location = loc
        e.rotation_euler = (0, 0, math.radians(rz))
    return e


def anchor(loc, tag="lamp"):
    n = len(ANCHORS) + 1
    e = empty("LightAnchor_%s_%02d" % (tag, n), tuple(loc), kind="SPHERE", size=0.25)
    ANCHORS.append(e)
    return e


def spot(name, loc, rz=0.0):
    e = empty(name, tuple(loc), rz, kind="SINGLE_ARROW", size=0.8)
    # SINGLE_ARROW points +Z; Spots only use location + Z yaw (front = local -Y like characters).
    SPOTS[name] = e
    return e


def look_matrix(loc, target):
    d = Vector(target) - Vector(loc)
    q = d.to_track_quat("-Z", "Y")
    return Matrix.Translation(loc) @ q.to_matrix().to_4x4()


# ---------------------------------------------------------------- preview cameras

def setup_preview_scene(world_col=(0.08, 0.10, 0.22)):
    sc = bpy.context.scene
    sc.render.engine = "BLENDER_WORKBENCH"
    sh = sc.display.shading
    sh.light = "STUDIO"
    sh.color_type = "VERTEX"
    sh.show_cavity = True
    sh.show_object_outline = True
    sh.show_shadows = True
    sc.world = sc.world or bpy.data.worlds.new("W")
    sc.world.color = world_col
    sc.render.film_transparent = False


def shot(name, loc, target, lens=24, size=(1280, 720), ortho=None):
    sc = bpy.context.scene
    setup_preview_scene()
    cd = bpy.data.cameras.new("ShotCam")
    cd.lens = lens
    cd.clip_start = 0.1
    cd.clip_end = 3000
    if ortho:
        cd.type = "ORTHO"
        cd.ortho_scale = ortho
    cam = bpy.data.objects.new("ShotCam", cd)
    sc.collection.objects.link(cam)
    cam.matrix_world = look_matrix(Vector(loc), target)
    sc.camera = cam
    sc.render.resolution_x, sc.render.resolution_y = size
    os.makedirs(A.PREVIEW_DIR, exist_ok=True)
    sc.render.filepath = os.path.join(A.PREVIEW_DIR, name + ".png")
    bpy.ops.render.render(write_still=True)
    bpy.data.objects.remove(cam)
    bpy.data.cameras.remove(cd)
    return sc.render.filepath
