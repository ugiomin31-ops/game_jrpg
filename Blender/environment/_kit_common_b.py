"""Shared builders for the ember_caverns / haunted_crypt dungeon kits (DungeonKit B2).

Conventions (see Blender/README.md "던전 키트 조각"):
- 1 cell = 4 m x 4 m, origin = cell centre on the floor (z=0). Floor tops at z=0.
- Wall blocks fill x,y in [-2,2], z in [0,4.5].
- Doors: frame plane at y=0, full cell width, passage along Y. `Door` hinge pivot at the -X jamb.
  door_locked: `Lock` parented to `Door`.
- chest faces -Y, `Lid` pivot on the back (+Y) top hinge.
- trap: `Spikes` root object, origin at spike base, exported retracted at z=-0.5 (z=0 = extended).
- overlays hug the -Y face of a wall cell (y ~ -2 .. -2.3), authored in that wall cell's space.
- stairs_down replaces the floor tile (own 4x4 floor with the opening); other props sit on a floor tile.
"""
import math
import os
import random
import sys

sys.path.append(os.path.join(os.path.dirname(os.path.abspath(__file__)), '../lib'))
import abyss_bpy as A  # noqa: E402

import bmesh  # noqa: E402
import bpy  # noqa: E402
from mathutils import Euler, Matrix, Vector, noise  # noqa: E402

CELL = 4.0
HALF = 2.0
WALL_H = 4.5


# ---------------------------------------------------------------- colour

def _rgb(c):
    return A.hexcol(c)[:3] if isinstance(c, str) else tuple(c[:3])


def mix(a, b, t):
    a, b = _rgb(a), _rgb(b)
    return tuple(a[i] * (1 - t) + b[i] * t for i in range(3))


def jit(rng, c, amt=0.06):
    """Random brightness / slight hue jitter around a colour."""
    r, g, b = _rgb(c)
    k = 1 + rng.uniform(-amt, amt)
    h = rng.uniform(-amt, amt) * 0.35
    return (min(1, max(0, r * k + h)), min(1, max(0, g * k)), min(1, max(0, b * k - h)))


def pick(rng, cols, amt=0.05):
    return jit(rng, rng.choice(cols), amt)


# ---------------------------------------------------------------- mesh primitives (bmesh, no ops)

def _obj_from_bm(name, bm, color, mat, smooth=False, recalc=True):
    if recalc:
        bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    me = bpy.data.meshes.new(name)
    bm.to_mesh(me)
    bm.free()
    o = bpy.data.objects.new(name, me)
    bpy.context.scene.collection.objects.link(o)
    if smooth:
        for p in me.polygons:
            p.use_smooth = True
    return A.paint(o, color, mat)


def _noise_off(seed):
    r = random.Random(seed)
    return Vector((r.uniform(-500, 500), r.uniform(-500, 500), r.uniform(-500, 500)))


def stone(name, size, loc=(0, 0, 0), rot=(0, 0, 0), color="#888888", mat="M_Toon", bevel=0.05,
          rough=0.0, seed=0, taper=0.0, freq=1.7, top_rough=True, cull=None):
    """Bevelled block (flat-shaded) with optional noise and top taper. size = full extents.
    cull: local axis direction(s) whose hidden faces are removed, e.g. "+Y" for blocks set against a wall core."""
    bm = bmesh.new()
    bmesh.ops.create_cube(bm, size=1.0)
    sx, sy, sz = size
    for v in bm.verts:
        k = 1.0 - taper if v.co.z > 0 else 1.0
        v.co = Vector((v.co.x * sx * k, v.co.y * sy * k, v.co.z * sz))
    if bevel > 0:
        b = min(bevel, min(size) * 0.45)
        bmesh.ops.bevel(bm, geom=list(bm.edges), offset=b, segments=1, profile=0.5, affect="EDGES",
                        clamp_overlap=True)
    if rough > 0:
        off = _noise_off(seed)
        for v in bm.verts:
            n = noise.noise_vector(v.co * freq + off)
            if not top_rough and v.co.z > sz * 0.45:
                n.z = 0
            v.co += n * rough
    if cull:
        axes = {"+X": Vector((1, 0, 0)), "-X": Vector((-1, 0, 0)), "+Y": Vector((0, 1, 0)), "-Y": Vector((0, -1, 0)),
                "+Z": Vector((0, 0, 1)), "-Z": Vector((0, 0, -1))}
        dirs = [axes[c] for c in (cull if isinstance(cull, (list, tuple)) else [cull])]
        bm.normal_update()
        dead = [f for f in bm.faces if any(f.normal.dot(d) > 0.6 for d in dirs)]
        bmesh.ops.delete(bm, geom=dead, context="FACES")
    o = _obj_from_bm(name, bm, color, mat, recalc=not cull)
    o.location = loc
    o.rotation_euler = Euler([math.radians(a) for a in rot])
    return o


def boulder(name, r=0.5, loc=(0, 0, 0), scale=(1, 1, 1), rot=(0, 0, 0), color="#555555", mat="M_Toon",
            seed=0, rough=0.28, subdiv=1, flat_bottom=None, smooth=False):
    """Low-poly faceted rock from an icosphere (subdiv 1 = 80 tris, 2 = 320)."""
    bm = bmesh.new()
    bmesh.ops.create_icosphere(bm, subdivisions=subdiv + 1 if subdiv > 0 else 1, radius=r)
    off = _noise_off(seed)
    for v in bm.verts:
        n = noise.noise(v.co * (1.6 / max(r, 0.05)) + off)
        v.co *= 1 + n * rough
        v.co = Vector((v.co.x * scale[0], v.co.y * scale[1], v.co.z * scale[2]))
        if flat_bottom is not None and v.co.z < flat_bottom:
            v.co.z = flat_bottom
    o = _obj_from_bm(name, bm, color, mat, smooth=smooth)
    o.location = loc
    o.rotation_euler = Euler([math.radians(a) for a in rot])
    return o


def poly_slab(name, pts, top=0.0, thick=0.2, color="#888888", mat="M_Toon", bevel=0.035, seed=0,
              tilt=0.0, loc=(0, 0, 0), rot=(0, 0, 0)):
    """Extruded XY polygon; top face at z=top. Top edges chamfered. For flagstones."""
    bm = bmesh.new()
    vs = [bm.verts.new((x, y, top - thick)) for (x, y) in pts]
    f = bm.faces.new(vs)
    r = bmesh.ops.extrude_face_region(bm, geom=[f])
    up = [e for e in r["geom"] if isinstance(e, bmesh.types.BMVert)]
    bmesh.ops.translate(bm, verts=up, vec=(0, 0, thick))
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    if bevel > 0:
        top_edges = [e for e in bm.edges if all(v.co.z > top - 1e-4 for v in e.verts)]
        bmesh.ops.bevel(bm, geom=top_edges, offset=bevel, segments=1, profile=0.5, affect="EDGES",
                        clamp_overlap=True)
    if tilt > 0:
        rr = random.Random(seed)
        ax, ay = rr.uniform(-tilt, tilt), rr.uniform(-tilt, tilt)
        cx = sum(p[0] for p in pts) / len(pts)
        cy = sum(p[1] for p in pts) / len(pts)
        for v in bm.verts:
            v.co.z += (v.co.x - cx) * ax + (v.co.y - cy) * ay - tilt * 0.6
    o = _obj_from_bm(name, bm, color, mat)
    o.location = loc
    o.rotation_euler = Euler([math.radians(a) for a in rot])
    return o


def prism(name, pts2d, depth, axis="X", loc=(0, 0, 0), rot=(0, 0, 0), color="#888888", mat="M_Toon",
          bevel=0.0, smooth=False):
    """Polygon extruded along `axis` (centred). pts2d are (u,v):
    axis X -> (y,z); axis Y -> (x,z); axis Z -> (x,y)."""
    bm = bmesh.new()

    def P(u, v, w):
        if axis == "X":
            return (w, u, v)
        if axis == "Y":
            return (u, w, v)
        return (u, v, w)

    a = [bm.verts.new(P(u, v, -depth / 2)) for (u, v) in pts2d]
    b = [bm.verts.new(P(u, v, depth / 2)) for (u, v) in pts2d]
    n = len(pts2d)
    bm.faces.new(a)
    bm.faces.new(list(reversed(b)))
    for i in range(n):
        j = (i + 1) % n
        bm.faces.new((a[i], a[j], b[j], b[i]))
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    if bevel > 0:
        bmesh.ops.bevel(bm, geom=list(bm.edges), offset=bevel, segments=1, profile=0.5, affect="EDGES",
                        clamp_overlap=True)
    o = _obj_from_bm(name, bm, color, mat, smooth=smooth)
    o.location = loc
    o.rotation_euler = Euler([math.radians(a) for a in rot])
    return o


def gem(name, r=0.1, loc=(0, 0, 0), rot=(0, 0, 0), color="#ff8800", mat="M_Emit", h=1.4, sides=4):
    """Faceted bipyramid gem (sides*2 tris)."""
    bm = bmesh.new()
    ring = [bm.verts.new((math.cos(2 * math.pi * i / sides) * r, math.sin(2 * math.pi * i / sides) * r, 0))
            for i in range(sides)]
    top = bm.verts.new((0, 0, r * h))
    bot = bm.verts.new((0, 0, -r * h))
    for i in range(sides):
        j = (i + 1) % sides
        bm.faces.new((ring[i], ring[j], top))
        bm.faces.new((ring[j], ring[i], bot))
    o = _obj_from_bm(name, bm, color, mat)
    o.location = loc
    o.rotation_euler = Euler([math.radians(a) for a in rot])
    return o


def shard(name, r=0.15, h=0.8, loc=(0, 0, 0), rot=(0, 0, 0), color="#2a1a2e", mat="M_Toon", sides=5, seed=0,
          tip=0.0):
    """Crystal shard: prism with pointed top (obsidian, ice, etc.)."""
    rr = random.Random(seed)
    bm = bmesh.new()
    base = []
    mid = []
    for i in range(sides):
        a = 2 * math.pi * i / sides + rr.uniform(-0.2, 0.2)
        k = rr.uniform(0.8, 1.15)
        base.append(bm.verts.new((math.cos(a) * r * k, math.sin(a) * r * k, 0)))
        mid.append(bm.verts.new((math.cos(a) * r * k * 0.95, math.sin(a) * r * k * 0.95, h * 0.72)))
    apex = bm.verts.new((rr.uniform(-r, r) * 0.3, rr.uniform(-r, r) * 0.3, h))
    bm.faces.new(list(reversed(base)))
    for i in range(sides):
        j = (i + 1) % sides
        bm.faces.new((base[i], base[j], mid[j], mid[i]))
        bm.faces.new((mid[i], mid[j], apex))
    o = _obj_from_bm(name, bm, color, mat)
    o.location = loc
    o.rotation_euler = Euler([math.radians(a) for a in rot])
    return o


def ngon_disc(name, r, z=0.0, n=24, loc=(0, 0, 0), rot=(0, 0, 0), color="#ffffff", mat="M_Toon", thick=0.0):
    """Flat disc (single n-gon, normal +Z) or thin cylinder if thick>0."""
    if thick > 0:
        return A.cyl(name, r=r, depth=thick, loc=(loc[0], loc[1], loc[2] + z), rot=rot, color=color, mat=mat,
                     seg=n, smooth=False)
    bm = bmesh.new()
    vs = [bm.verts.new((math.cos(2 * math.pi * i / n) * r, math.sin(2 * math.pi * i / n) * r, z)) for i in range(n)]
    bm.faces.new(vs)
    me = bpy.data.meshes.new(name)
    bm.to_mesh(me)
    bm.free()
    o = bpy.data.objects.new(name, me)
    bpy.context.scene.collection.objects.link(o)
    o.location = loc
    o.rotation_euler = Euler([math.radians(a) for a in rot])
    return A.paint(o, color, mat)


def ring_strip(name, r_in, r_out, z=0.0, n=32, color="#ffffff", mat="M_Emit", loc=(0, 0, 0), thick=0.0,
               a0=0.0, a1=360.0):
    """Flat annulus (or annular sector) facing +Z; with thick>0 it's a solid washer."""
    bm = bmesh.new()
    full = abs(a1 - a0) >= 359.9
    cnt = n if full else n + 1
    inner, outer = [], []
    for i in range(cnt):
        a = math.radians(a0 + (a1 - a0) * i / n)
        inner.append(bm.verts.new((math.cos(a) * r_in, math.sin(a) * r_in, z)))
        outer.append(bm.verts.new((math.cos(a) * r_out, math.sin(a) * r_out, z)))
    segs = n if full else n
    for i in range(segs):
        j = (i + 1) % cnt
        bm.faces.new((inner[i], outer[i], outer[j], inner[j]))
    if thick > 0:
        r = bmesh.ops.extrude_face_region(bm, geom=list(bm.faces))
        moved = [e for e in r["geom"] if isinstance(e, bmesh.types.BMVert)]
        bmesh.ops.translate(bm, verts=moved, vec=(0, 0, thick))
        bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    else:
        for f in bm.faces:
            if f.normal.z < 0:
                f.normal_flip()
    me = bpy.data.meshes.new(name)
    bm.to_mesh(me)
    bm.free()
    o = bpy.data.objects.new(name, me)
    bpy.context.scene.collection.objects.link(o)
    o.location = loc
    return A.paint(o, color, mat)


def star_pts(n, r_out, r_in, phase=0.0):
    pts = []
    for i in range(n * 2):
        a = math.pi * i / n + phase
        r = r_out if i % 2 == 0 else r_in
        pts.append((math.cos(a) * r, math.sin(a) * r))
    return pts


def circle_pts(n, r, phase=0.0, sx=1.0, sy=1.0):
    return [(math.cos(2 * math.pi * i / n + phase) * r * sx, math.sin(2 * math.pi * i / n + phase) * r * sy)
            for i in range(n)]


def sun_emblem(prefix, r=0.5, rays=12, loc=(0, 0, 0), rot=(0, 0, 0), ray_col="#f2c14e", disc_col="#ffd970",
               core_col="#ff8a1a", core_mat="M_Emit", depth=0.06, axis="Y"):
    """Gold sun medallion facing -Y (axis Y) or +Z (axis Z). Returns list of objects (ray star, disc, core)."""
    objs = []
    if axis == "Y":
        pr = lambda pts, d, yoff: prism(prefix + "_p", [(p[0], p[1]) for p in pts], d, axis="Y",
                                        loc=(0, -yoff, 0), color=ray_col)
    else:
        pr = lambda pts, d, yoff: prism(prefix + "_p", [(p[0], p[1]) for p in pts], d, axis="Z",
                                        loc=(0, 0, yoff), color=ray_col)
    s = pr(star_pts(rays, r, r * 0.62, math.pi / 2), depth, 0)
    objs.append(s)
    d = pr(circle_pts(14, r * 0.6), depth, depth * 0.45)
    A.paint(d, disc_col)
    objs.append(d)
    c = pr(circle_pts(10, r * 0.34), depth, depth * 0.9)
    A.paint(c, core_col, core_mat)
    objs.append(c)
    grp_place(objs, loc, rot)
    return objs


# ---------------------------------------------------------------- transforms / grouping

def grp_place(objs, loc=(0, 0, 0), rot=(0, 0, 0), scale=1.0):
    """Apply a group transform (about the group origin) to every (unparented) object.
    Uses matrix_basis, which is computed live from loc/rot/scale (matrix_world is stale until a depsgraph update)."""
    M = Matrix.Translation(Vector(loc)) @ Euler([math.radians(a) for a in rot]).to_matrix().to_4x4() @ \
        Matrix.Diagonal((scale, scale, scale, 1.0))
    for o in objs:
        o.matrix_basis = M @ o.matrix_basis
    return objs


def rotz(objs, deg):
    M = Matrix.Rotation(math.radians(deg), 4, "Z")
    for o in objs:
        o.matrix_basis = M @ o.matrix_basis
    return objs


def mirror_objs_x(objs):
    """Mirror copies across X (returns new objects; normals fixed when baked)."""
    out = []
    for o in objs:
        c = o.copy()
        c.data = o.data.copy()
        bpy.context.scene.collection.objects.link(c)
        c.matrix_basis = Matrix.Diagonal((-1, 1, 1, 1)) @ o.matrix_basis
        _bake(c)
        out.append(c)
    return out


def dup(objs, loc=(0, 0, 0), rot=(0, 0, 0)):
    out = []
    for o in objs:
        c = o.copy()
        c.data = o.data.copy()
        bpy.context.scene.collection.objects.link(c)
        out.append(c)
    return grp_place(out, loc, rot)


def four_sides(builder):
    """builder(k) builds decoration for the -Y face; result is rotated k*90 deg about Z."""
    out = []
    for k in range(4):
        objs = builder(k)
        rotz(objs, 90 * k)
        out += objs
    return out


def _bake(o):
    """Bake object transform into mesh data (no ops); flips winding for mirrored transforms."""
    mw = o.matrix_basis.copy()
    o.data.transform(mw)
    if mw.determinant() < 0:
        bm = bmesh.new()
        bm.from_mesh(o.data)
        bmesh.ops.reverse_faces(bm, faces=bm.faces)
        bm.to_mesh(o.data)
        bm.free()
    o.matrix_basis = Matrix.Identity(4)


def finish(name, objs, origin=(0, 0, 0)):
    """Join all objects into one mesh `name` whose object origin is `origin` (world)."""
    objs = [o for o in objs if o is not None]
    bpy.context.view_layer.update()
    for o in objs:
        _bake(o)
    bpy.ops.object.select_all(action="DESELECT")
    for o in objs:
        o.select_set(True)
    bpy.context.view_layer.objects.active = objs[0]
    if len(objs) > 1:
        bpy.ops.object.join()
    o = bpy.context.view_layer.objects.active
    o.name = name
    o.data.name = name
    if Vector(origin).length > 0:
        o.data.transform(Matrix.Translation(-Vector(origin)))
        o.location = origin
    bpy.context.view_layer.update()
    return o


def empty(name, loc=(0, 0, 0), size=0.3):
    e = bpy.data.objects.new(name, None)
    e.empty_display_type = "PLAIN_AXES"
    e.empty_display_size = size
    e.location = loc
    bpy.context.scene.collection.objects.link(e)
    return e


def tris(o):
    return sum(len(p.vertices) - 2 for p in o.data.polygons) if o.type == "MESH" else 0


# ---------------------------------------------------------------- layout helpers

def split_rects(rng, rect, min_size=0.7, max_size=1.6):
    """Recursive guillotine split of (x0,y0,x1,y1) into irregular rectangles."""
    x0, y0, x1, y1 = rect
    w, h = x1 - x0, y1 - y0
    if w <= max_size and h <= max_size and (rng.random() < 0.55 or (w < 2 * min_size and h < 2 * min_size)):
        return [rect]
    if (w >= h and w >= 2 * min_size) or h < 2 * min_size:
        if w < 2 * min_size:
            return [rect]
        c = rng.uniform(x0 + min_size, x1 - min_size)
        return split_rects(rng, (x0, y0, c, y1), min_size, max_size) + split_rects(rng, (c, y0, x1, y1), min_size, max_size)
    c = rng.uniform(y0 + min_size, y1 - min_size)
    return split_rects(rng, (x0, y0, x1, c), min_size, max_size) + split_rects(rng, (x0, c, x1, y1), min_size, max_size)


def chamfer_rect(rng, x0, y0, x1, y1, amt=0.18, jitter=0.04, rotj=0.0):
    """Rect with randomly cut corners and wobbly edges -> irregular hand-cut stone outline (CCW)."""
    w, h = x1 - x0, y1 - y0
    m = min(w, h)
    pts = []
    corners = [(x0, y0, 1, 1), (x1, y0, -1, 1), (x1, y1, -1, -1), (x0, y1, 1, -1)]
    for i, (cx, cy, sx, sy) in enumerate(corners):
        c1 = rng.uniform(0.25, 1.0) * amt * m
        c2 = rng.uniform(0.25, 1.0) * amt * m
        # each corner -> two points (along incoming edge, along outgoing edge), CCW order
        if i == 0:
            pts += [(cx, cy + c2), (cx + c1, cy)]
        elif i == 1:
            pts += [(cx - c1, cy), (cx, cy + c2)]
        elif i == 2:
            pts += [(cx, cy - c2), (cx - c1, cy)]
        else:
            pts += [(cx + c1, cy), (cx, cy - c2)]
    out = []
    for (x, y) in pts:
        out.append((x + rng.uniform(-jitter, jitter) * 0.5, y + rng.uniform(-jitter, jitter) * 0.5))
    if rotj > 0:
        a = rng.uniform(-rotj, rotj)
        ca, sa = math.cos(a), math.sin(a)
        mx, my = (x0 + x1) / 2, (y0 + y1) / 2
        k = 1.0 - abs(a) * 0.9
        out = [(mx + ((x - mx) * ca - (y - my) * sa) * k, my + ((x - mx) * sa + (y - my) * ca) * k) for x, y in out]
    # clamp inside rect so tiles never poke past the cell border
    return [(min(max(x, x0), x1), min(max(y, y0), y1)) for (x, y) in out]


def flagstones(prefix, rng, rect, cols, gap=0.06, min_size=0.7, max_size=1.5, top=0.0, thick=0.22,
               chamfer=0.2, tilt=0.008, bevel=0.035, skip=None, col_fn=None, rotj=0.07):
    """Paving of irregular stones inside rect with half-gap border so tiles stay seamless."""
    out = []
    for i, (x0, y0, x1, y1) in enumerate(split_rects(rng, rect, min_size, max_size)):
        cx, cy = (x0 + x1) / 2, (y0 + y1) / 2
        if skip and skip(cx, cy, (x0, y0, x1, y1)):
            continue
        g = gap / 2
        pts = chamfer_rect(rng, x0 + g, y0 + g, x1 - g, y1 - g, chamfer, rotj=rotj)
        col = col_fn(rng, cx, cy) if col_fn else pick(rng, cols)
        out.append(poly_slab(f"{prefix}{i}", pts, top=top - rng.uniform(0, 0.012), thick=thick, color=col,
                             bevel=bevel, seed=rng.randint(0, 99999), tilt=tilt))
    return out


def ashlar_face(prefix, rng, x0, x1, z0, z1, cols, y_face=-HALF, depth=0.35, course=(0.7, 1.1),
                length=(0.9, 1.7), gap=0.05, relief=0.05, bevel=0.06, rough=0.02, col_fn=None):
    """Course masonry on the plane y=y_face (outer surface, -Y facing), stones within [x0,x1]x[z0,z1]."""
    out = []
    z = z0
    row = 0
    while z < z1 - 0.05:
        ch = rng.uniform(*course)
        if z1 - (z + ch) < course[0] * 0.6:
            ch = z1 - z
        x = x0
        off = rng.uniform(0, length[0] * 0.6) if row % 2 else 0
        first = True
        while x < x1 - 0.05:
            ln = rng.uniform(*length)
            if first and off:
                ln = max(off, 0.35)
            first = False
            if x1 - (x + ln) < length[0] * 0.45:
                ln = x1 - x
            sx = ln - gap
            sz = ch - gap
            inset = rng.uniform(0, relief)
            col = col_fn(rng, x + ln / 2, z + ch / 2) if col_fn else pick(rng, cols)
            o = stone(f"{prefix}{row}_{len(out)}", (sx, depth, sz),
                      loc=(x + ln / 2, y_face + depth / 2 + inset, z + ch / 2),
                      color=col, bevel=bevel, rough=rough, seed=rng.randint(0, 99999), cull="+Y")
            out.append(o)
            x += ln
        z += ch
        row += 1
    return out


def scatter_pebbles(prefix, rng, n, rect, z, cols, r=(0.05, 0.1), avoid=None):
    out = []
    x0, y0, x1, y1 = rect
    for i in range(n):
        x, y = rng.uniform(x0, x1), rng.uniform(y0, y1)
        if avoid and avoid(x, y):
            continue
        rr = rng.uniform(*r)
        out.append(boulder(f"{prefix}{i}", rr, loc=(x, y, z + rr * 0.3), scale=(1, 1, 0.6), color=pick(rng, cols),
                           seed=rng.randint(0, 9999), subdiv=0, rough=0.25))
    return out


def chain(prefix, p0, p1, link_r=0.07, wire=0.018, color="#5a5866", sag=0.0, n=None):
    """Chain of alternating torus links from p0 to p1 (optionally sagging)."""
    p0, p1 = Vector(p0), Vector(p1)
    L = (p1 - p0).length
    step = link_r * 1.5
    n = n or max(2, int(L / step))
    out = []
    for i in range(n + 1):
        t = i / n
        p = p0.lerp(p1, t)
        p.z -= sag * 4 * t * (1 - t)
        if i < n:
            q = p0.lerp(p1, (i + 1) / n)
            q.z -= sag * 4 * ((i + 1) / n) * (1 - (i + 1) / n)
        d = (q - p).normalized() if i < n else (p1 - p0).normalized()
        o = A.torus(f"{prefix}{i}", R=link_r, r=wire, loc=p, color=color, seg=6, minor=4, scale=(1, 1.6, 1))
        # orient: link long axis (local Y) along d, alternate twist
        rot = d.to_track_quat("Y", "Z").to_matrix().to_4x4()
        tw = Matrix.Rotation(math.radians(90 if i % 2 else 0), 4, "Y")
        o.matrix_world = Matrix.Translation(p) @ rot @ tw @ Matrix.Diagonal((1, 1.6, 1, 1))
        out.append(o)
    return out


def grad3(o, c0, c1, c2, axis=2, mid=0.45):
    """Three-stop gradient along a local axis (c0 bottom, c1 at `mid`, c2 top)."""
    c0, c1, c2 = (A._as_rgba(c) for c in (c0, c1, c2))
    me = o.data
    if "Col" not in me.color_attributes:
        me.color_attributes.new("Col", "BYTE_COLOR", "CORNER")
    attr = me.color_attributes["Col"]
    vs = [v.co[axis] for v in me.vertices]
    lo, hi = min(vs), max(vs)
    span = max(hi - lo, 1e-6)
    for loop in me.loops:
        t = (me.vertices[loop.vertex_index].co[axis] - lo) / span
        if t < mid:
            a, b, u = c0, c1, t / mid
        else:
            a, b, u = c1, c2, (t - mid) / (1 - mid)
        attr.data[loop.index].color_srgb = tuple(a[i] * (1 - u) + b[i] * u for i in range(4))
    return o


def _tongue(name, s, h, seed, lobes=5, seg=10):
    rr = random.Random(seed)
    prof = [(0.0, -0.02), (0.15, 0.03), (0.2, 0.13), (0.17, 0.26), (0.11, 0.4), (0.05, 0.53), (0.0, 0.66)]
    o = A.lathe(name, [(r * s, z * s * h) for r, z in prof], seg=seg)
    ph = rr.uniform(0, 6.28)
    top = 0.66 * s * h

    def f(v):
        t = max(0.0, v.z / top)
        a = math.atan2(v.y, v.x)
        k = 1 + 0.28 * math.sin(lobes * a + t * 5 + ph) * t
        return Vector((v.x * k + math.sin(t * 4 + ph) * 0.05 * s * t, v.y * k + math.cos(t * 3 + ph) * 0.03 * s * t,
                       v.z))
    A.deform(o, f)
    return o


def flame(prefix, loc=(0, 0, 0), s=1.0, outer="#ff4a10", mid="#ffa020", inner="#fff2a8", mat="M_Emit", seed=0,
          tongues=2, sparks=2):
    """Stylised toon flame: lobed twisting main tongue + side tongues, 3-stop gradient (bright core at the base)."""
    rr = random.Random(seed)
    main = _tongue(prefix + "m", s, 1.0, seed)
    grad3(main, inner, mid, outer, mid=0.4)
    out = [main]
    for i in range(tongues):
        a = 2 * math.pi * i / max(tongues, 1) + rr.uniform(-0.4, 0.4)
        t = _tongue(prefix + f"t{i}", s * 0.55, rr.uniform(0.8, 1.1), seed + 11 * (i + 1), lobes=3, seg=8)
        grad3(t, mid, outer, outer, mid=0.5)
        t.location = (math.cos(a) * 0.1 * s, math.sin(a) * 0.1 * s, 0.0)
        t.rotation_euler = (math.sin(a) * -0.45, math.cos(a) * 0.45, 0)
        out.append(t)
    for i in range(sparks):
        a = rr.uniform(0, 6.28)
        g = gem(prefix + f"s{i}", 0.035 * s, loc=(math.cos(a) * 0.14 * s, math.sin(a) * 0.14 * s, (0.75 + 0.18 * i) * s),
                rot=(0, 0, rr.uniform(0, 90)), color=mid, h=1.6)
        out.append(g)
    for o in out:
        me = o.data
        me.materials.clear()
        me.materials.append(A._material(mat))
    grp_place(out, loc, (0, 0, rr.uniform(0, 360)))
    return out


def skull(prefix, s=1.0, loc=(0, 0, 0), rot=(0, 0, 0), color="#d8ccb4", socket="#2a1f2e", low=False):
    """Chibi skull facing -Y (cranium + jaw + eye sockets)."""
    seg, rings = (8, 6) if low else (12, 8)
    out = [A.sphere(prefix + "cr", 0.16 * s, loc=(0, 0, 0.17 * s), scale=(1, 1.05, 0.95), color=color, seg=seg, rings=rings),
           stone(prefix + "jw", (0.2 * s, 0.16 * s, 0.1 * s), loc=(0, -0.05 * s, 0.05 * s), color=color, bevel=0.03 * s)]
    for sx in (-1, 1):
        out.append(A.sphere(prefix + f"ey{sx}", 0.045 * s, loc=(0.06 * s * sx, -0.135 * s, 0.15 * s),
                            scale=(1, 0.5, 1.15), color=socket, seg=6, rings=4))
    out.append(gem(prefix + "ns", 0.02 * s, loc=(0, -0.15 * s, 0.09 * s), rot=(90, 0, 0), color=socket, mat="M_Toon", h=1.5, sides=3))
    grp_place(out, loc, rot)
    return out


def candle(prefix, h=0.3, r=0.05, loc=(0, 0, 0), wax="#efe6d0", flame_col=("#c070ff", "#e0a8ff", "#ffffff"), seed=0):
    rr = random.Random(seed)
    out = [A.cyl(prefix + "w", r=r, depth=h, loc=(0, 0, h / 2), color=jit(rr, wax, 0.04), seg=8)]
    # wax drips
    for i in range(2):
        a = rr.uniform(0, 6.28)
        out.append(A.cyl(prefix + f"d{i}", r=r * 0.28, depth=h * rr.uniform(0.3, 0.6),
                         loc=(math.cos(a) * r * 0.95, math.sin(a) * r * 0.95, h * 0.72), color=wax, seg=5))
    out += flame(prefix + "f", loc=(0, 0, h + 0.01), s=r * 2.2, outer=flame_col[0], mid=flame_col[1], inner=flame_col[2],
                 seed=seed)
    grp_place(out, loc)
    return out


# ---------------------------------------------------------------- export / preview

def export_piece(tileset, piece, objs):
    path = A.export_fbx(f"Environment/{tileset}/{piece}.fbx", objects=objs)
    if not os.path.isfile(path):
        raise RuntimeError("export failed: " + path)
    return path


def export_arena_turned(tileset, objs):
    """Export an arena authored with the enemies toward +Y. The game maps Blender (x, y, z) to Unity (x, z, -y) and puts
    the enemies at Unity +Z (Blender -Y), so the arena is exported turned 180 degrees about Z and turned back after."""
    turn = Matrix.Rotation(math.pi, 4, "Z")
    tops = [o for o in objs if o.parent is None]
    for o in tops:
        o.matrix_world = turn @ o.matrix_world
    try:
        return export_piece(tileset, "arena", objs)
    finally:
        for o in tops:
            o.matrix_world = turn @ o.matrix_world


def all_desc(objs):
    out = []
    for o in objs:
        out.append(o)
        out += list(o.children_recursive)
    return out


def label(text, loc, size=0.55, color="#ffffff"):
    cu = bpy.data.curves.new("lbl_" + text, "FONT")
    cu.body = text
    cu.size = size
    cu.align_x = "CENTER"
    o = bpy.data.objects.new("lbl_" + text, cu)
    o.location = loc
    bpy.context.scene.collection.objects.link(o)
    mat = A._material("M_Toon")
    cu.materials.append(mat)
    return o


def set_world(color):
    sc = bpy.context.scene
    sc.world = sc.world or bpy.data.worlds.new("W")
    sc.world.color = tuple(c ** 2.2 for c in _rgb(color))


def render_cam(name, loc, target, fov_deg=70, res=(1280, 720), world="#000000", hide=None):
    """Render from an explicit camera (vertical FOV) with the same Workbench look as A.render_preview."""
    sc = bpy.context.scene
    hidden = []
    for o in hide or []:
        if not o.hide_render:
            o.hide_render = True
            hidden.append(o)
    cd = bpy.data.cameras.new("QACam")
    cd.sensor_fit = "VERTICAL"
    cd.angle_y = math.radians(fov_deg)
    cd.clip_end = 2000
    cam = bpy.data.objects.new("QACam", cd)
    sc.collection.objects.link(cam)
    d = Vector(target) - Vector(loc)
    cam.location = loc
    cam.rotation_euler = d.to_track_quat("-Z", "Y").to_euler()
    sc.camera = cam
    _shading(sc, world)
    sc.render.resolution_x, sc.render.resolution_y = res
    sc.render.resolution_percentage = 100
    os.makedirs(A.PREVIEW_DIR, exist_ok=True)
    sc.render.filepath = os.path.join(A.PREVIEW_DIR, name + ".png")
    bpy.ops.render.render(write_still=True)
    bpy.data.objects.remove(cam)
    for o in hidden:
        o.hide_render = False
    return sc.render.filepath


def _shading(sc, world):
    sc.render.engine = "BLENDER_WORKBENCH"
    sh = sc.display.shading
    sh.light = "STUDIO"
    sh.color_type = "VERTEX"
    sh.show_cavity = True
    sh.cavity_type = "BOTH"
    sh.show_object_outline = True
    sh.object_outline_color = (0.05, 0.03, 0.04)
    sh.show_shadows = True
    sh.shadow_intensity = 0.35
    sc.view_settings.view_transform = "Standard"
    sc.render.film_transparent = False
    set_world(world)


def render_fit(name, objs, angle=(55, 0, 25), res=(1600, 1000), world="#2a2630", margin=1.06, ortho=True):
    """Workbench render framing exactly the given objects (uses evaluated vertices, not bound boxes)."""
    sc = bpy.context.scene
    bpy.context.view_layer.update()
    keep = set(objs)
    hidden = []
    for o in sc.objects:
        if o.type in ("MESH", "FONT", "CURVE") and o not in keep and not o.hide_render:
            o.hide_render = True
            hidden.append(o)
    rot = Euler([math.radians(a) for a in angle])
    Rm = rot.to_matrix()
    Ri = Rm.inverted()
    dg = bpy.context.evaluated_depsgraph_get()
    lo = Vector((1e9, 1e9, 1e9))
    hi = Vector((-1e9, -1e9, -1e9))
    for o in objs:
        if o.type not in ("MESH", "FONT"):
            continue
        oe = o.evaluated_get(dg)
        me = oe.to_mesh()
        mw = oe.matrix_world
        for v in me.vertices:
            p = Ri @ (mw @ v.co)
            lo = Vector(map(min, lo, p))
            hi = Vector(map(max, hi, p))
        oe.to_mesh_clear()
    c_cam = (lo + hi) / 2
    w, h = (hi.x - lo.x) * margin, (hi.y - lo.y) * margin
    cd = bpy.data.cameras.new("FitCam")
    cd.type = "ORTHO" if ortho else "PERSP"
    aspect = res[0] / res[1]
    cd.ortho_scale = max(w, h * aspect)
    cd.clip_start = 0.1
    cd.clip_end = 5000
    cam = bpy.data.objects.new("FitCam", cd)
    sc.collection.objects.link(cam)
    cam.location = Rm @ Vector((c_cam.x, c_cam.y, hi.z + 50))
    cam.rotation_euler = rot
    sc.camera = cam
    _shading(sc, world)
    sc.render.resolution_x, sc.render.resolution_y = res
    sc.render.resolution_percentage = 100
    os.makedirs(A.PREVIEW_DIR, exist_ok=True)
    sc.render.filepath = os.path.join(A.PREVIEW_DIR, name + ".png")
    bpy.ops.render.render(write_still=True)
    bpy.data.objects.remove(cam)
    for o in hidden:
        o.hide_render = False
    return sc.render.filepath


class Sheet:
    """Exports pieces, then lays them out for a labelled contact sheet and instantiates a mock layout."""

    def __init__(self, tileset):
        self.tileset = tileset
        self.pieces = {}
        self.report = []
        self.labels = {}

    def add(self, piece, objs):
        roots = [o for o in objs if o.parent is None]
        everything = all_desc(roots)
        path = export_piece(self.tileset, piece, everything)
        t = sum(tris(o) for o in everything)
        self.pieces[piece] = [roots, Vector((0, 0, 0))]
        self.report.append((piece, t, os.path.basename(path), [o.name for o in everything]))
        print(f"[kit] {self.tileset}/{piece}: {t} tris, objects={[o.name for o in everything]}")
        # free contract names (Door, Lid, Lock, Spikes, LightAnchor) for the next piece
        for o in everything:
            if o not in roots or o.name != piece:
                o.name = f"{piece}.{o.name}"
        # park far away until arranged
        self._move(piece, Vector((0, 0, -500 - 20 * len(self.pieces))))
        return path

    def _move(self, piece, off):
        roots, cur = self.pieces[piece]
        for o in roots:
            o.location += off - cur
        self.pieces[piece][1] = off.copy()
        bpy.context.view_layer.update()

    def arrange(self, names, cols, pitch, origin=(0, 0, 0), label_size=0.45, row_pitch=None):
        """Grid-place pieces (with labels) and return every object to render."""
        out = []
        row_pitch = row_pitch or pitch
        for i, n in enumerate(names):
            off = Vector(origin) + Vector(((i % cols) * pitch, -(i // cols) * row_pitch, 0))
            self._move(n, off)
            out += [o for o in all_desc(self.pieces[n][0]) if o.type == "MESH"]
            if n not in self.labels:
                t = next(r[1] for r in self.report if r[0] == n)
                self.labels[n] = label(f"{n}  {t}", (0, 0, 0), size=label_size)
            self.labels[n].location = off + Vector((0, -pitch * 0.42, 0.02))
            out.append(self.labels[n])
        bpy.context.view_layer.update()
        return out

    def instance(self, piece, cell, rot=0, base=(0, 0, 0)):
        roots, off = self.pieces[piece]
        bpy.context.view_layer.update()
        M = Matrix.Translation(Vector(base) + Vector((cell[0] * CELL, cell[1] * CELL, 0))) @ \
            Matrix.Rotation(math.radians(rot), 4, "Z") @ Matrix.Translation(-off)
        out = []
        for o in all_desc(roots):
            if o.type != "MESH":
                continue
            c = o.copy()
            c.parent = None
            bpy.context.scene.collection.objects.link(c)
            c.matrix_world = M @ o.matrix_world
            c["mock"] = 1
            out.append(c)
        bpy.context.view_layer.update()
        return out


TILE_PIECES = ("floor_a", "floor_b", "floor_c", "wall_a", "wall_b", "wall_c", "door", "door_locked", "stairs_down",
               "stairs_up", "boss_gate")


def run_kit(ts, pieces, layout, extras, walls, floors, world="#2a2630", seed=777):
    """Build + export every piece, then render contact sheets and a 5x5 mock layout, save .blend."""
    A.reset_scene()
    sheet = Sheet(ts)
    for name, fn in pieces:
        sheet.add(name, fn())
    names = [n for n, _ in pieces]
    tiles = [n for n in names if n in TILE_PIECES]
    props = [n for n in names if n not in TILE_PIECES]
    # tiles sheet
    objs = sheet.arrange(tiles, cols=6, pitch=6.5, origin=(0, 0, 0))
    render_fit(f"env_{ts}_sheet_tiles", objs, angle=(58, 0, 28), res=(1800, 1100), world=world)
    objs = sheet.arrange(props, cols=5, pitch=4.6, origin=(0, -30, 0))
    render_fit(f"env_{ts}_sheet_props", objs, angle=(58, 0, 28), res=(1800, 1300), world=world)
    # combined contact sheet of every piece
    objs = sheet.arrange(names, cols=7, pitch=6.5, origin=(0, 0, 0))
    render_fit(f"env_{ts}_sheet", objs, angle=(55, 0, 25), res=(2000, 1500), world=world)
    # mock layout
    rng = random.Random(seed)
    base = Vector((200.0, 0.0, 0.0))
    mock = []
    nrows = len(layout)
    for row, line in enumerate(layout):
        y = nrows - 1 - row
        for x, tok in enumerate(line):
            if tok == "W":
                mock += sheet.instance(rng.choice(walls), (x, y), rot=90 * rng.randint(0, 3), base=base)
                continue
            if tok != "stairs_down":
                mock += sheet.instance(rng.choice(floors), (x, y), rot=90 * rng.randint(0, 3), base=base)
            if tok != ".":
                mock += sheet.instance(tok, (x, y), base=base)
    for piece, cell, rot in extras:
        mock += sheet.instance(piece, cell, rot=rot, base=base)
    render_fit(f"env_{ts}_layout", mock, angle=(48, 0, 30), res=(1600, 1400), world=world)
    c = base + Vector((2 * CELL, 2 * CELL, 0))
    render_cam(f"env_{ts}_layout_tp", loc=c + Vector((0, -11.5, 8.5)), target=c + Vector((0, 1.0, 0.5)), fov_deg=60,
               res=(1600, 900), world=world, hide=[o for o in bpy.context.scene.objects if o not in mock])
    A.save_blend(f"env_{ts}")
    over = [(r[0], r[1]) for r in sheet.report if r[1] > 3000 or r[1] < 200]
    print("[kit] SUMMARY", [(r[0], r[1]) for r in sheet.report])
    print("[kit] OUT OF BUDGET", over)
    return sheet


def ribbon(name, z0, z1, n, width_fn, x_fn=lambda t: 0.0, y_fn=lambda t: 0.0, thick=0.06, color="#ffffff",
           mat="M_Emit"):
    """Vertical strip from z1 (t=0, top) down to z0 (t=1); width/x/y vary with t. Closed thin slab (for falls)."""
    bm = bmesh.new()
    fr, bk = [], []
    for i in range(n + 1):
        t = i / n
        z = z1 + (z0 - z1) * t
        w = width_fn(t) / 2
        x = x_fn(t)
        y = y_fn(t)
        fr.append((bm.verts.new((x - w, y - thick / 2, z)), bm.verts.new((x + w, y - thick / 2, z))))
        bk.append((bm.verts.new((x - w, y + thick / 2, z)), bm.verts.new((x + w, y + thick / 2, z))))
    for i in range(n):
        a, b = fr[i], fr[i + 1]
        bm.faces.new((a[0], a[1], b[1], b[0]))
        a, b = bk[i], bk[i + 1]
        bm.faces.new((a[1], a[0], b[0], b[1]))
        bm.faces.new((fr[i][0], fr[i + 1][0], bk[i + 1][0], bk[i][0]))
        bm.faces.new((fr[i][1], bk[i][1], bk[i + 1][1], fr[i + 1][1]))
    bm.faces.new((fr[0][0], bk[0][0], bk[0][1], fr[0][1]))
    bm.faces.new((fr[n][0], fr[n][1], bk[n][1], bk[n][0]))
    return _obj_from_bm(name, bm, color, mat)


def paint_fn(o, fn):
    """Per-corner colour from fn(local co Vector) -> rgb tuple (sRGB)."""
    me = o.data
    if "Col" not in me.color_attributes:
        me.color_attributes.new("Col", "BYTE_COLOR", "CORNER")
    attr = me.color_attributes["Col"]
    for loop in me.loops:
        c = fn(me.vertices[loop.vertex_index].co)
        attr.data[loop.index].color_srgb = (c[0], c[1], c[2], 1.0)
    return o


def ramp(stops, t):
    """stops: [(t, colour)], ascending. Linear interpolation, clamped."""
    t = min(max(t, stops[0][0]), stops[-1][0])
    for (t0, c0), (t1, c1) in zip(stops, stops[1:]):
        if t <= t1:
            return mix(c0, c1, (t - t0) / max(t1 - t0, 1e-6))
    return _rgb(stops[-1][1])
