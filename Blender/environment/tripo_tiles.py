"""Deterministic clean-up + validation for Tripo-made dungeon tiling pieces (wall / floor / stairs / door).

Contract: ArtSource/_briefs/environment_tiling.md (4 m cells, piece origin = cell centre on the floor, walls exactly
[-2,2]^2 x [0,4.5], floors top at z=0, north = -Y, Blender axes; the FBX export is the project's own
Blender/lib/abyss_bpy.py export_fbx, so Unity gets X=X, Z=-Y).  No Tripo API is touched: this only post-processes
meshes downloaded from Tripo Studio.  It never writes .meta files; writing inside Assets/ needs --install and only
replaces the .fbx (the existing .fbx.meta, and so its GUID, stays as it is).

Run (Blender 4.x, headless):
  blender -b --factory-startup -P Blender/environment/tripo_tiles.py -- <command> [options]

Commands
  process     --kind wall-module|wall|floor|stair|door|prop --input FILE --name NAME --out-dir DIR [options]
              import -> clean -> validate -> export FBX (+ texture copy) -> re-import the FBX and validate again.
  build-wall  --n FBX [--e FBX] [--s FBX] [--w FBX] --name NAME --out-dir DIR
              assemble a wall block from four processed wall-module FBXs (E/S/W default to --n): rotated copies named
              Face_N/E/S/W + a Core box (+/-1.80), then export + validate.
  validate    --kind ... --input FBX [--partner FBX ...] [--ceiling-from FBX]
              report only.  Exit code 3 when a FAIL is found.

wall-module = one 4.0 x 4.5 face slab authored as the NORTH face (front toward -Y, back plane y=-1.80, relief to
y=-2.00).  Internally the shell is rotated into a local frame whose +Z is "outward" so floors and wall faces share one
code path.  Options worth knowing (defaults follow the brief):
  --tol 0.02            snap vertices this close to a cell bound onto the bound
  --depth-mode scale    relief deeper than allowed (0.2 wall / 0.08 floor) is scaled, not clamped, so it keeps its shape
  --level-percentile P  height that counts as "the surface" (floor default 90, wall 100); bumps above it are flattened
  --band L,R,B,T        flat seam bands in metres (wall 0.12,0.12,0.25,0.30; floor 0.15 all round; 0 = off)
  --uv planar|keep      planar = u=(x+2)/4, v=z/4.5 (wall face) / v=(y+2)/4 (floor); needs --texture or --uv planar
  --rotate-z 90         rotate before fitting (floor_b = floor_a rotated; UVs are re-projected afterwards)
  --split-faces         (kind wall) split a finished block into Face_N/E/S/W (+Core) children
  --keep-from FBX       copy Ceiling*/LightAnchor*/Spot_* empties+meshes from an existing piece unchanged
  --planar-dissolve DEG optional planar dissolve (off by default: nothing is simplified unless asked)
"""
import argparse
import json
import math
import os
import shutil
import sys

import bmesh
import bpy
from mathutils import Matrix, Vector
from mathutils.bvhtree import BVHTree

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.normpath(os.path.join(HERE, "..", ".."))
sys.dont_write_bytecode = True  # do not touch the tracked __pycache__ of Blender/lib
sys.path.append(os.path.join(REPO, "Blender", "lib"))
import abyss_bpy as A  # noqa: E402  (provides export_fbx with the project's environment settings)

HALF = 2.0
WALL_H = 4.5
BACK_D = 1.80          # wall face back plane
FLAT_D = 1.98          # seam-band plane
CEIL_Z = 4.48
FLOOR_UNDER = -0.3
SPECIAL = ("Ceiling", "LightAnchor", "Spot_")
TRI_BUDGET = {"wall-module": 1000, "wall": 4200, "floor": 1000, "stair": 4000, "door": 4000, "prop": 10 ** 9}
KINDS = ("wall-module", "wall", "floor", "stair", "door", "prop")
EPS = 1e-4

# ------------------------------------------------------------------ report


class Report:
    def __init__(self, title):
        self.title = title
        self.rows = []

    def add(self, check, ok, msg, level="FAIL"):
        self.rows.append({"check": check, "status": "PASS" if ok else level, "msg": msg})
        return ok

    def info(self, check, msg):
        self.rows.append({"check": check, "status": "INFO", "msg": msg})

    @property
    def failed(self):
        return [r for r in self.rows if r["status"] == "FAIL"]

    def dump(self):
        print(f"\n=== VALIDATION {self.title} ===")
        for r in self.rows:
            print(f"[{r['status']:4}] {r['check']}: {r['msg']}")
        print(f"=== {self.title}: {len(self.failed)} FAIL, {sum(r['status'] == 'WARN' for r in self.rows)} WARN ===")

    def as_json(self):
        return {"title": self.title, "fail": len(self.failed), "rows": self.rows}


# ------------------------------------------------------------------ scene / io helpers

def clear_scene():
    bpy.ops.wm.read_factory_settings(use_empty=True)
    sc = bpy.context.scene
    sc.unit_settings.system = "METRIC"
    sc.unit_settings.scale_length = 1.0


def import_any(path):
    before = set(bpy.data.objects)
    ext = os.path.splitext(path)[1].lower()
    if ext == ".fbx":
        bpy.ops.import_scene.fbx(filepath=path)
    elif ext in (".glb", ".gltf"):
        bpy.ops.import_scene.gltf(filepath=path)
    elif ext == ".obj":
        bpy.ops.wm.obj_import(filepath=path)
    else:
        raise SystemExit(f"unsupported input {path}")
    bpy.context.view_layer.update()
    return [o for o in bpy.data.objects if o not in before]


def is_special(name):
    return name.startswith(SPECIAL)


def is_tile_part(name):
    return name.startswith("Face_") or name == "Core"


def body_objects(objs, kind):
    """Mesh objects that make up the tile itself (not Ceiling/Door/Lock/anchors)."""
    out = []
    for o in objs:
        if o.type != "MESH" or is_special(o.name):
            continue
        if kind == "door" and o.name in ("Door", "Lock"):
            continue
        out.append(o)
    return out


def world_bm(objs):
    """One bmesh holding the world-space geometry of objs (matrix baked in)."""
    bpy.context.view_layer.update()
    bm = bmesh.new()
    for o in objs:
        start = len(bm.verts)
        bm.from_mesh(o.data)
        mw = o.matrix_world
        for v in bm.verts[start:]:
            v.co = mw @ v.co
    return bm


def bake_to_single_mesh(objs, name):
    """Join mesh objects into one object with transforms applied; returns it."""
    bpy.ops.object.select_all(action="DESELECT")
    bpy.context.view_layer.update()
    for o in objs:
        mw = o.matrix_world.copy()
        o.parent = None  # parents of body meshes are only import empties
        o.data.transform(mw)
        o.matrix_world = Matrix.Identity(4)
    for o in objs:
        o.select_set(True)
    bpy.context.view_layer.objects.active = objs[0]
    if len(objs) > 1:
        bpy.ops.object.join()
    obj = bpy.context.view_layer.objects.active
    obj.name = name
    obj.data.name = name
    obj.select_set(False)
    return obj


def new_obj(name, bm, materials=()):
    me = bpy.data.meshes.new(name)
    bm.to_mesh(me)
    for m in materials:
        me.materials.append(m)
    ob = bpy.data.objects.new(name, me)
    bpy.context.scene.collection.objects.link(ob)
    return ob


def bbox_of(bm):
    if not bm.verts:
        return Vector((0, 0, 0)), Vector((0, 0, 0))
    xs = [v.co for v in bm.verts]
    return (Vector((min(c.x for c in xs), min(c.y for c in xs), min(c.z for c in xs))),
            Vector((max(c.x for c in xs), max(c.y for c in xs), max(c.z for c in xs))))


def fmt(v):
    return "(" + ", ".join(f"{c:.4f}" for c in v) + ")"


# ------------------------------------------------------------------ mesh operations (all bmesh, deterministic)

def weld(bm, dist=1e-5):
    bmesh.ops.remove_doubles(bm, verts=bm.verts[:], dist=dist)
    bmesh.ops.dissolve_degenerate(bm, dist=1e-6, edges=bm.edges[:])
    loose = [v for v in bm.verts if not v.link_edges]
    if loose:
        bmesh.ops.delete(bm, geom=loose, context="VERTS")


def snap_to_bounds(bm, lo, hi, tol):
    """Vertices within tol of (or beyond) a bound move onto it. lo/hi: per-axis bound or None. Returns moved count."""
    n = 0
    for v in bm.verts:
        for a in range(3):
            for bound in (lo[a], hi[a]):
                if bound is not None and abs(v.co[a] - bound) <= tol and v.co[a] != bound:
                    v.co[a] = bound
                    n += 1
    return n


def bisect_trim(bm, lo, hi, fill=False):
    """Cut away everything outside the box lo..hi (None = unbounded on that side). fill: cap solid cuts."""
    for a in range(3):
        for bound, sign in ((lo[a], -1.0), (hi[a], 1.0)):
            if bound is None:
                continue
            if not any(sign * (v.co[a] - bound) > 1e-6 for v in bm.verts):
                continue
            co = Vector((0, 0, 0))
            co[a] = bound
            no = Vector((0, 0, 0))
            no[a] = sign
            geom = bm.verts[:] + bm.edges[:] + bm.faces[:]
            res = bmesh.ops.bisect_plane(bm, geom=geom, dist=1e-6, plane_co=co, plane_no=no, clear_outer=True,
                                         clear_inner=False)
            if fill:
                cut = [g for g in res["geom_cut"] if isinstance(g, bmesh.types.BMEdge) and g.is_boundary]
                if cut and _forms_loops(cut):
                    bmesh.ops.triangle_fill(bm, use_beauty=True, use_dissolve=False, edges=cut)


def _forms_loops(edges):
    cnt = {}
    for e in edges:
        for v in e.verts:
            cnt[v] = cnt.get(v, 0) + 1
    return all(c == 2 for c in cnt.values())


def recalc_normals(bm):
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces[:])


def is_closed(bm):
    return bool(bm.faces) and not any(e.is_boundary or not e.is_manifold for e in bm.edges)


def triangulate(bm):
    bmesh.ops.triangulate(bm, faces=bm.faces[:], quad_method="BEAUTY", ngon_method="BEAUTY")


def set_flat(bm):
    for f in bm.faces:
        f.smooth = False


def close_perimeter(bm, h_close, eps=1e-5):
    """Close an open shell: extrude its boundary to z = h_close (local frame) and fill the new loop."""
    boundary = [e for e in bm.edges if e.is_boundary]
    if not boundary:
        return
    if not all(abs(v.co.z - h_close) < eps for e in boundary for v in e.verts):
        bmesh.ops.extrude_edge_only(bm, edges=boundary)
        boundary = [e for e in bm.edges if e.is_boundary]
        for v in {v for e in boundary for v in e.verts}:
            v.co.z = h_close
    try:
        bmesh.ops.triangle_fill(bm, use_beauty=True, use_dissolve=False, edges=boundary)
    except RuntimeError:
        bmesh.ops.holes_fill(bm, edges=boundary, sides=0)


# ------------------------------------------------------------------ shell kinds (wall-module, floor)
# Local frame: +Z = outward, x along the tile, y along the tile (floor: world y; wall: world z).

PARAMS = {
    "wall-module": dict(y0=0.0, y1=WALL_H, h_min=-0.2, h_top=0.0, h_flat=-0.02, h_close=-0.2,
                        band=(0.12, 0.12, 0.25, 0.30), percentile=100.0),
    "floor": dict(y0=-HALF, y1=HALF, h_min=-0.08, h_top=0.0, h_flat=0.0, h_close=FLOOR_UNDER,
                  band=(0.15, 0.15, 0.15, 0.15), percentile=90.0),
}


def to_local(bm, kind):
    """World -> local. Wall module (front toward -Y, back plane y=-1.8): (x,y,z) -> (x, z, -y-2) so front is h=0."""
    if kind == "wall-module":
        for v in bm.verts:
            x, y, z = v.co
            v.co = Vector((x, z, -y - HALF))


def from_local(bm, kind):
    if kind == "wall-module":
        for v in bm.verts:
            x, yy, h = v.co
            v.co = Vector((x, -h - HALF, yy))


def percentile(vals, p):
    vals = sorted(vals)
    if not vals:
        return 0.0
    k = (len(vals) - 1) * max(0.0, min(100.0, p)) / 100.0
    i = int(math.floor(k))
    j = min(i + 1, len(vals) - 1)
    return vals[i] + (vals[j] - vals[i]) * (k - i)


def process_shell(bm, kind, opt, log):
    P = PARAMS[kind]
    y0, y1 = P["y0"], P["y1"]
    h_min = -opt.relief_depth if opt.relief_depth is not None else P["h_min"]
    to_local(bm, kind)
    # fit: width -> [-2,2], tile height -> [y0,y1] (non-uniform on purpose: the brief fits the bbox of the front/top surface);
    # relief depth is never stretched, only translated so the surface level sits at h_top.
    if not opt.no_fit:
        lo, hi = bbox_of(bm)
        for v in bm.verts:
            v.co.x = -HALF + (v.co.x - lo.x) * (2 * HALF) / max(hi.x - lo.x, 1e-9)
            v.co.y = y0 + (v.co.y - lo.y) * (y1 - y0) / max(hi.y - lo.y, 1e-9)
    # surface level (percentile of heights) -> h_top
    hs = [v.co.z for v in bm.verts]
    level = percentile(hs, opt.level_percentile if opt.level_percentile is not None else P["percentile"])
    for v in bm.verts:
        v.co.z += P["h_top"] - level
    snap_to_bounds(bm, (-HALF, y0, None), (HALF, y1, None), opt.tol)
    bisect_trim(bm, (-HALF, y0, None), (HALF, y1, None), fill=False)
    snap_to_bounds(bm, (-HALF, y0, None), (HALF, y1, None), opt.tol)
    weld(bm)
    # keep only the visible shell: drop back/underside faces and the slab's own side walls lying on the trim planes
    bm.normal_update()
    kill = []
    for f in bm.faces:
        if f.normal.z < -0.35:
            kill.append(f)
            continue
        if abs(f.normal.z) < 0.2:
            for a, bounds in ((0, (-HALF, HALF)), (1, (y0, y1))):
                if any(all(abs(v.co[a] - b) < EPS for v in f.verts) for b in bounds):
                    kill.append(f)
                    break
    if kill:
        bmesh.ops.delete(bm, geom=list(set(kill)), context="FACES")
    weld(bm)
    if not bm.faces:
        raise SystemExit("process: nothing left after removing back faces - is the front facing the wrong way? try --pre-rotate")
    # relief depth: scale (default) or clamp into [h_min, h_top]; bumps above the surface are always flattened
    hs = [v.co.z for v in bm.verts]
    low = min(hs)
    if opt.depth_mode == "scale" and low < h_min and low < P["h_top"]:
        s = (h_min - P["h_top"]) / (low - P["h_top"])
        for v in bm.verts:
            if v.co.z < P["h_top"]:
                v.co.z = P["h_top"] + (v.co.z - P["h_top"]) * s
        log.append(f"relief scaled x{s:.3f} (observed depth {P['h_top'] - low:.3f} m > {P['h_top'] - h_min:.3f} m)")
    for v in bm.verts:
        v.co.z = max(h_min, min(P["h_top"], v.co.z))
    # seam bands: outer strips lie flat on h_flat so neighbours and corners meet on identical planes
    band = opt.band_tuple if opt.band_tuple is not None else P["band"]
    bl, br, bb, bt = band
    # split the mesh exactly on the band edges first, so the flat strips are really flat (no sloped triangles straddling them)
    for axis, bound, on in ((0, -HALF + bl, bl), (0, HALF - br, br), (1, y0 + bb, bb), (1, y1 - bt, bt)):
        if on:
            co = Vector((0, 0, 0))
            co[axis] = bound
            no = Vector((0, 0, 0))
            no[axis] = 1.0
            bmesh.ops.bisect_plane(bm, geom=bm.verts[:] + bm.edges[:] + bm.faces[:], dist=1e-6, plane_co=co, plane_no=no)
    n = 0
    for v in bm.verts:
        if (bl and v.co.x < -HALF + bl + 1e-6) or (br and v.co.x > HALF - br - 1e-6) or (bb and v.co.y < y0 + bb + 1e-6) or (bt and v.co.y > y1 - bt - 1e-6):
            if v.co.z != P["h_flat"]:
                v.co.z = P["h_flat"]
                n += 1
    log.append(f"flat band: {n} vertices set to h={P['h_flat']}")
    snap_to_bounds(bm, (-HALF, y0, None), (HALF, y1, None), 1e-6)
    close_perimeter(bm, P["h_close"])
    weld(bm)
    if opt.planar_dissolve > 0:
        bmesh.ops.dissolve_limit(bm, angle_limit=math.radians(opt.planar_dissolve), verts=bm.verts[:], edges=bm.edges[:],
                                 use_dissolve_boundaries=False)
    from_local(bm, kind)
    if not (opt.no_normals):
        recalc_normals(bm)


# ------------------------------------------------------------------ other kinds

def process_block(bm, kind, opt, log):
    """wall (full block), stair, door: fit/trim/snap only. Geometry is otherwise left as Tripo made it."""
    if kind == "wall":
        lo_t, hi_t = (-HALF, -HALF, 0.0), (HALF, HALF, WALL_H)
    elif kind == "stair":
        lo_t, hi_t = (-HALF, -HALF, None), (HALF, HALF, None)
    else:  # door: frame fills the cell width and height; depth is kept (centred on y)
        lo_t, hi_t = (-HALF, None, 0.0), (HALF, None, WALL_H)
    if not opt.no_fit:
        lo, hi = bbox_of(bm)
        for a in range(3):
            if lo_t[a] is not None and hi_t[a] is not None:
                for v in bm.verts:
                    v.co[a] = lo_t[a] + (v.co[a] - lo[a]) * (hi_t[a] - lo_t[a]) / max(hi[a] - lo[a], 1e-9)
        if kind == "door":
            cy = (lo.y + hi.y) / 2
            for v in bm.verts:
                v.co.y -= cy
    snap_to_bounds(bm, lo_t, hi_t, opt.tol)
    bisect_trim(bm, lo_t, hi_t, fill=True)
    snap_to_bounds(bm, lo_t, hi_t, 1e-6)
    weld(bm)
    if opt.planar_dissolve > 0:
        bmesh.ops.dissolve_limit(bm, angle_limit=math.radians(opt.planar_dissolve), verts=bm.verts[:], edges=bm.edges[:],
                                 use_dissolve_boundaries=False)
    if not opt.no_normals and is_closed(bm):
        recalc_normals(bm)
    elif not is_closed(bm):
        log.append("mesh is not closed: normals left as imported")


def uv_project(bm, kind):
    """Planar projection used by every piece so seams line up: wall face u=(x+2)/4, v=z/4.5; floor v=(y+2)/4."""
    layer = bm.loops.layers.uv.verify()
    for f in bm.faces:
        for l in f.loops:
            x, y, z = l.vert.co
            if kind == "wall-module":
                l[layer].uv = ((x + HALF) / (2 * HALF), z / WALL_H)
            else:
                l[layer].uv = ((x + HALF) / (2 * HALF), (y + HALF) / (2 * HALF))


def split_wall_faces(bm, materials):
    """Split a wall block into Face_N/E/S/W by dominant horizontal direction of each polygon centre; top/bottom -> Core."""
    groups = {"Face_N": [], "Face_E": [], "Face_S": [], "Face_W": [], "Core": []}
    bm.faces.index_update()
    bm.normal_update()
    for f in bm.faces:
        c = f.calc_center_median()
        if abs(f.normal.z) > 0.8:
            groups["Core"].append(f.index)
        elif abs(c.x) >= abs(c.y):
            groups["Face_E" if c.x > 0 else "Face_W"].append(f.index)
        else:
            groups["Face_S" if c.y > 0 else "Face_N"].append(f.index)
    out = []
    for name, idx in groups.items():
        if not idx:
            continue
        b2 = bm.copy()
        b2.faces.ensure_lookup_table()
        b2.faces.index_update()
        keep = set(idx)
        kill = [f for f in b2.faces if f.index not in keep]
        bmesh.ops.delete(b2, geom=kill, context="FACES")
        loose = [v for v in b2.verts if not v.link_faces]
        if loose:
            bmesh.ops.delete(b2, geom=loose, context="VERTS")
        out.append(new_obj(name, b2, materials))
        b2.free()
    return out


def split_door(bm, opt, log):
    """Return (door_leaf_bm, lock_bm or None, rest_bm): polygons whose vertices all sit inside the leaf box -> Door,
    inside the lock box -> Lock; everything else stays the frame."""
    leaf = [float(t) for t in opt.door_leaf_bbox.split(",")]
    lock = [float(t) for t in opt.lock_bbox.split(",")] if opt.lock_bbox else None

    def inside(f, b):
        return all(b[0] - EPS <= v.co.x <= b[3] + EPS and b[1] - EPS <= v.co.y <= b[4] + EPS and b[2] - EPS <= v.co.z <= b[5] + EPS
                   for v in f.verts)
    bm.faces.index_update()
    sel_lock = {f.index for f in bm.faces if lock and inside(f, lock)}
    sel_leaf = {f.index for f in bm.faces if inside(f, leaf) and f.index not in sel_lock}
    parts = []
    for idx in (sel_leaf, sel_lock, {f.index for f in bm.faces} - sel_leaf - sel_lock):
        b2 = bm.copy()
        b2.faces.ensure_lookup_table()
        b2.faces.index_update()
        bmesh.ops.delete(b2, geom=[f for f in b2.faces if f.index not in idx], context="FACES")
        loose = [v for v in b2.verts if not v.link_faces]
        if loose:
            bmesh.ops.delete(b2, geom=loose, context="VERTS")
        parts.append(b2)
    log.append(f"door split: leaf {len(parts[0].faces)} faces, lock {len(parts[1].faces)} faces, frame {len(parts[2].faces)} faces")
    return parts


# ------------------------------------------------------------------ materials / texture

def make_material(name, png):
    mat = bpy.data.materials.new(name)
    mat.use_nodes = True
    nt = mat.node_tree
    bsdf = nt.nodes.get("Principled BSDF")
    tex = nt.nodes.new("ShaderNodeTexImage")
    tex.image = bpy.data.images.load(png)
    nt.links.new(tex.outputs["Color"], bsdf.inputs["Base Color"])
    bsdf.inputs["Roughness"].default_value = 0.9
    return mat


# ------------------------------------------------------------------ geometry queries for validation

def tri_overlap(t1, t2, eps=1e-5):
    """Strict SAT: True when two triangles interpenetrate by more than eps (touching/coplanar is not an overlap)."""
    def edges(t):
        return [t[1] - t[0], t[2] - t[1], t[0] - t[2]]
    e1, e2 = edges(t1), edges(t2)
    axes = [e1[0].cross(e1[1]), e2[0].cross(e2[1])] + [a.cross(b) for a in e1 for b in e2]
    for ax in axes:
        if ax.length < 1e-9:
            continue
        ax = ax.normalized()
        p1 = [ax.dot(v) for v in t1]
        p2 = [ax.dot(v) for v in t2]
        if max(p1) <= min(p2) + eps or max(p2) <= min(p1) + eps:
            return False
    return True


def seg_tri(p0, p1, tri, eps=1e-9):
    """Moller-Trumbore for the segment p0-p1 against a triangle; returns the hit point or None."""
    d = p1 - p0
    e1, e2 = tri[1] - tri[0], tri[2] - tri[0]
    h = d.cross(e2)
    a = e1.dot(h)
    if abs(a) < eps:
        return None
    f = 1.0 / a
    sv = p0 - tri[0]
    u = f * sv.dot(h)
    if u < -1e-7 or u > 1 + 1e-7:
        return None
    q = sv.cross(e1)
    v = f * d.dot(q)
    if v < -1e-7 or u + v > 1 + 1e-7:
        return None
    t = f * e2.dot(q)
    return p0 + d * t if -1e-7 <= t <= 1 + 1e-7 else None


def tri_hit_points(t1, t2):
    """End points of the intersection segment of two triangles (edge-pierce points)."""
    pts = []
    for a, b in ((t1, t2), (t2, t1)):
        for i in range(3):
            h = seg_tri(a[i], a[(i + 1) % 3], b)
            if h is not None:
                pts.append(h)
    return pts


def overlap_pairs(bm_a, bm_b=None, same=False, cap=300000):
    """Exact interpenetrating triangle pairs (indices into faces; both bmeshes must be triangulated)."""
    ta = BVHTree.FromBMesh(bm_a, epsilon=0.0)
    tb = ta if bm_b is None else BVHTree.FromBMesh(bm_b, epsilon=0.0)
    bm_b = bm_a if bm_b is None else bm_b
    bm_a.faces.ensure_lookup_table()
    bm_b.faces.ensure_lookup_table()
    hits = []
    cand = ta.overlap(tb)
    for i, j in cand[:cap]:
        if same and i >= j:
            continue
        fa, fb = bm_a.faces[i], bm_b.faces[j]
        if same and set(fa.verts) & set(fb.verts):
            continue
        ta3, tb3 = [v.co.copy() for v in fa.verts], [v.co.copy() for v in fb.verts]
        if tri_overlap(ta3, tb3):
            hits.append(tri_hit_points(ta3, tb3) or [(fa.calc_center_median() + fb.calc_center_median()) / 2])
    return hits, len(cand)


def tri_bm(objs):
    bm = world_bm(objs)
    triangulate(bm)
    bm.faces.ensure_lookup_table()
    bm.faces.index_update()
    return bm


def linspace(a, b, n):
    return [a + (b - a) * i / (n - 1) for i in range(n)]


# ------------------------------------------------------------------ validation

def validate(kind, objs, rep, opt, partner_sets=()):
    """objs: all objects of the piece (meshes + empties) in the current scene."""
    meshes = [o for o in objs if o.type == "MESH"]
    body = [o for o in meshes if (o.name.startswith("Face_") or o.name == "Core")] if any(is_tile_part(o.name) for o in meshes) \
        else body_objects(meshes, kind)
    if not body:
        rep.add("body", False, "no body mesh found")
        return
    names = sorted(o.name for o in objs)
    rep.info("objects", ", ".join(f"{o.name}[{o.type[0]}]" for o in sorted(objs, key=lambda o: o.name)))
    bm = world_bm(body)
    lo, hi = bbox_of(bm)
    rep.info("bounds", f"min {fmt(lo)} max {fmt(hi)} size {fmt(hi - lo)}")
    t = 1e-3
    if kind == "wall":
        exp_lo, exp_hi = (-HALF, -HALF, 0.0), (HALF, HALF, WALL_H)
    elif kind == "wall-module":
        exp_lo, exp_hi = (-HALF, None, 0.0), (HALF, -BACK_D, WALL_H)
    elif kind == "floor":
        exp_lo, exp_hi = (-HALF, -HALF, None), (HALF, HALF, 0.0)
    elif kind == "door":
        exp_lo, exp_hi = (-HALF, None, 0.0), (HALF, None, WALL_H)
    elif kind == "stair":
        exp_lo, exp_hi = (-HALF, -HALF, None), (HALF, HALF, None)
    else:
        exp_lo, exp_hi = (None,) * 3, (None,) * 3
    bad = []
    for a, ax in enumerate("xyz"):
        if exp_lo[a] is not None and abs(lo[a] - exp_lo[a]) > t:
            bad.append(f"min {ax}={lo[a]:.4f} (want {exp_lo[a]})")
        if exp_hi[a] is not None and abs(hi[a] - exp_hi[a]) > t:
            bad.append(f"max {ax}={hi[a]:.4f} (want {exp_hi[a]})")
    if kind == "wall-module" and lo.y < -HALF - t:
        bad.append(f"relief beyond y=-2 ({lo.y:.4f})")
    if kind != "prop":
        rep.add("dimensions", not bad, "exact" if not bad else "; ".join(bad))
    if kind == "floor":
        rep.add("floor_underside", lo.z >= FLOOR_UNDER - t, f"lowest z {lo.z:.4f} (>= {FLOOR_UNDER})", level="WARN")
    if kind == "stair":
        rise = opt.stair_rise
        if opt.stair == "up":
            rep.add("stair_landing", abs(hi.z - rise) <= 0.02, f"landing top z={hi.z:.3f} (want {rise})")
        elif opt.stair == "down":
            bm.normal_update()
            tread = [f.calc_center_median().z for f in bm.faces if f.normal.z > 0.7]
            low = min(tread) if tread else lo.z
            rep.add("stair_depth", abs(low + rise) <= 0.02, f"lowest walkable surface z={low:.3f} (want {-rise}); mesh min z {lo.z:.3f}")
    # tris / topology / uv
    total = 0
    for o in body:
        b = world_bm([o])
        tris = sum(len(f.verts) - 2 for f in b.faces)
        total += tris
        boundary = [e for e in b.edges if e.is_boundary]
        nonman = [e for e in b.edges if not e.is_boundary and not e.is_manifold]
        loose = [v for v in b.verts if not v.link_edges]
        degen = [f for f in b.faces if f.calc_area() < 1e-9]
        label = f"{o.name}"
        msg = f"{tris} tris, {len(b.verts)} verts, open edges {len(boundary)}, non-manifold {len(nonman)}, loose {len(loose)}, degenerate faces {len(degen)}"
        if boundary:
            bl, bh = bbox_of_edges(boundary)
            msg += f"; open edges span {fmt(bl)}..{fmt(bh)}"
        closed_ok = not boundary and not nonman
        # sheets are legitimate for props; tiles must be watertight
        rep.add(f"topology[{label}]", closed_ok and not loose and not degen, msg, level="WARN" if kind == "prop" else "FAIL")
        if closed_ok and b.faces:
            vol = signed_volume(b)
            rep.add(f"normals[{label}]", vol > 0, f"signed volume {vol:.4f} (positive = outward)", level="WARN")
        uvl = o.data.uv_layers.active
        if uvl is not None and o.data.loops:
            us = [d.uv[0] for d in uvl.data]
            vs = [d.uv[1] for d in uvl.data]
            ok = min(us) >= -1e-3 and max(us) <= 1 + 1e-3 and min(vs) >= -1e-3 and max(vs) <= 1 + 1e-3
            rep.add(f"uv_range[{label}]", ok, f"u {min(us):.3f}..{max(us):.3f} v {min(vs):.3f}..{max(vs):.3f}", level="WARN")
        elif opt.expect_uv:
            rep.add(f"uv[{label}]", False, "no UV layer")
        b.free()
    budget = TRI_BUDGET[kind]
    if kind == "wall" and any(o.name.startswith("Face_") for o in body):
        per = [len(o.data.loop_triangles) for o in body if o.name.startswith("Face_")]
        rep.add("tri_budget_face", max(per) <= TRI_BUDGET["wall-module"], f"largest face {max(per)} tris (<= {TRI_BUDGET['wall-module']})", level="WARN")
    rep.add("tri_budget", total <= budget, f"{total} tris (<= {budget})", level="WARN")
    # outside bounds
    out = [v for v in bm.verts if any(
        (exp_lo[a] is not None and v.co[a] < exp_lo[a] - EPS) or (exp_hi[a] is not None and v.co[a] > exp_hi[a] + EPS) for a in range(3))]
    if kind != "prop":
        rep.add("verts_outside_bounds", not out, f"{len(out)} vertices outside the cell box")
    # naming
    if kind == "wall":
        faces = [o.name for o in body if o.name.startswith("Face_")]
        if faces or opt.expect_faces:
            want = {"Face_N", "Face_E", "Face_S", "Face_W"}
            rep.add("face_names", want <= set(faces), f"children {sorted(faces)}" + (" + Core" if "Core" in names else ""))
    if kind == "floor" and opt.expect_ceiling:
        rep.add("ceiling_object", any(n.startswith("Ceiling") for n in names), "Ceiling object kept")
    # overlaps
    if len(body) > 1:
        corner_bad = corner_ok = 0
        for i in range(len(body)):
            for j in range(i + 1, len(body)):
                if "Core" in (body[i].name, body[j].name):
                    continue
                ba, bb2 = tri_bm([body[i]]), tri_bm([body[j]])
                hits, _ = overlap_pairs(ba, bb2)
                for pts in hits:
                    # two face slabs overlap by design only inside the corner column (|x| and |y| >= 1.8)
                    if all(abs(p.x) >= BACK_D - 0.01 and abs(p.y) >= BACK_D - 0.01 for p in pts):
                        corner_ok += 1
                    else:
                        corner_bad += 1
                ba.free()
                bb2.free()
        rep.add("face_overlap", corner_bad == 0, f"{corner_bad} interpenetrating triangle pairs outside the corner columns, {corner_ok} inside (expected)")
    else:
        tb = tri_bm(body)
        hits, cand = overlap_pairs(tb, same=True)
        rep.add("self_overlap", len(hits) == 0, f"{len(hits)} interpenetrating triangle pairs (of {cand} bbox candidates)", level="WARN")
        tb.free()
    # seam profile / vertex match / corners / ceiling
    if kind in ("floor", "wall", "wall-module"):
        seam_checks(kind, body, bm, rep, opt, partner_sets)
    if kind == "wall" and opt.ceiling_from:
        ceiling_join(body, rep, opt)
    if kind == "door":
        door_checks(objs, rep, opt)
    bm.free()


def signed_volume(bm):
    v = 0.0
    for f in bm.faces:
        vs = [x.co for x in f.verts]
        for i in range(1, len(vs) - 1):
            v += vs[0].dot(vs[i].cross(vs[i + 1])) / 6.0
    return v


def bbox_of_edges(edges):
    vs = [v.co for e in edges for v in e.verts]
    return (Vector((min(c.x for c in vs), min(c.y for c in vs), min(c.z for c in vs))),
            Vector((max(c.x for c in vs), max(c.y for c in vs), max(c.z for c in vs))))


def profile_floor(tree, axis, side, n):
    """Top height along one cell edge, sampled just inside it. axis 0: edge x=side*2, samples along y; axis 1: along x."""
    out = []
    for s in linspace(-HALF + 0.01, HALF - 0.01, n):
        p = Vector((side * (HALF - 0.002), s, 5.0)) if axis == 0 else Vector((s, side * (HALF - 0.002), 5.0))
        hit = tree.ray_cast(p, Vector((0, 0, -1)), 20.0)
        out.append(None if hit[0] is None else hit[0].z)
    return out


def profile_wall(tree, edge_axis, side, face_side, n):
    """Outward depth of one face along one block edge. edge_axis 0: edge x=side*2, face N/S (face_side -1/+1 on y);
    edge_axis 1: edge y=side*2, face W/E (face_side -1/+1 on x). Depth = distance from the cell wall plane (2.0)."""
    out = []
    for z in linspace(0.02, WALL_H - 0.02, n):
        if edge_axis == 0:
            o = Vector((side * (HALF - 0.002), face_side * 6.0, z))
            d = Vector((0, -face_side, 0))
        else:
            o = Vector((face_side * 6.0, side * (HALF - 0.002), z))
            d = Vector((-face_side, 0, 0))
        hit = tree.ray_cast(o, d, 20.0)
        out.append(None if hit[0] is None else 6.0 - hit[3])
    return out


def edge_verts(bm, edge_axis, side, kind):
    """Rounded (other-coords) of vertices on the cell edge plane; for walls only the face ends (|other| >= 1.8)."""
    other = 1 if edge_axis == 0 else 0
    pts = set()
    for v in bm.verts:
        if abs(v.co[edge_axis] - side * HALF) < 1e-3:
            if kind == "wall" and abs(v.co[other]) < BACK_D - 1e-3:
                continue
            pts.add((round(v.co[other], 3), round(v.co[2], 3)))
    return pts


def seam_checks(kind, body, bm, rep, opt, partner_sets):
    """Place two instances side by side (one cell apart, never rotated) and compare what meets at the seam.
    floor: top height along the shared edge; wall: outward depth of the faces that run into the seam (N/S faces across an
    E-W seam, E/W faces across an N-S seam => all four faces). Also compares the edge vertex layout and reports
    outer-corner notches. Every partner is tested against the piece itself in both orders."""
    def tri_copy(b):
        c = b.copy()
        triangulate(c)
        return c
    pieces = [("self", bm, BVHTree.FromBMesh(tri_copy(bm), epsilon=0.0))]
    for name, pbm in partner_sets:
        pieces.append((name, pbm, BVHTree.FromBMesh(tri_copy(pbm), epsilon=0.0)))
    n = 49 if kind == "floor" else 61
    tol = opt.seam_tol
    worst = 0.0
    msgs = []
    vert_bad = 0
    edge_axes = ((0, "E-W"),) if kind == "wall-module" else ((0, "E-W"), (1, "N-S"))
    for ia, (na, ba, ta) in enumerate(pieces):
        for ib, (nb, bb, tb2) in enumerate(pieces):
            if ia != 0 and ib != 0:
                continue
            for edge_axis, dirname in edge_axes:
                if kind == "floor":
                    faces = [(None, "floor")]
                else:
                    faces = [(-1, "N" if edge_axis == 0 else "W")]
                    if kind == "wall":
                        faces.append((1, "S" if edge_axis == 0 else "E"))
                for face_side, fname in faces:
                    if kind == "floor":
                        pa = profile_floor(ta, edge_axis, +1, n)
                        pb = profile_floor(tb2, edge_axis, -1, n)
                    else:
                        pa = profile_wall(ta, edge_axis, +1, face_side, n)
                        pb = profile_wall(tb2, edge_axis, -1, face_side, n)
                    dd = [abs(x - y) for x, y in zip(pa, pb) if x is not None and y is not None]
                    miss = sum((x is None) != (y is None) for x, y in zip(pa, pb))
                    gap = max(dd) if dd else 0.0
                    worst = max(worst, gap)
                    if gap > tol or miss:
                        msgs.append(f"{na}->{nb} {fname} ({dirname}): step {gap*1000:.2f} mm, {miss} unmatched samples")
                if edge_verts(ba, edge_axis, +1, kind) != edge_verts(bb, edge_axis, -1, kind):
                    vert_bad += 1
    rep.add("seam_profile", not msgs, f"max step {worst*1000:.2f} mm over {len(pieces)} piece(s)"
            + ("" if not msgs else "; " + " | ".join(msgs[:6])))
    rep.add("seam_vertex_match", vert_bad == 0,
            f"{vert_bad} edge pair(s) whose boundary vertex layouts differ (collinear T-junctions; the profile check above is what shows)"
            if vert_bad else "boundary vertices identical on opposite edges", level="FAIL" if opt.strict_verts else "WARN")
    if kind == "wall":
        corner_checks(bm, rep, opt, pieces[0][2])


def corner_checks(bm, rep, opt, tree):
    """Outer corner: the N face end at x=+-2 and the E face end at y=-2 both stop short of the corner column by
    (2 - depth). A real notch is what stays visible from outside, so report the worst."""
    worst = 0.0
    where = ""
    for sx in (-1, 1):
        for sy in (-1, 1):
            for z in linspace(0.02, WALL_H - 0.02, 31):
                # N/S face ray at x = sx*(2-d) hits the face at depth dN; E/W face ray hits depth dE
                oN = Vector((sx * (HALF - 0.002), sy * 6.0, z))
                hN = tree.ray_cast(oN, Vector((0, -sy, 0)), 20.0)
                oE = Vector((sx * 6.0, sy * (HALF - 0.002), z))
                hE = tree.ray_cast(oE, Vector((-sx, 0, 0)), 20.0)
                for h, ax in ((hN, "N/S"), (hE, "E/W")):
                    if h[0] is None:
                        notch = HALF
                    else:
                        notch = HALF - (6.0 - h[3])
                    if notch > worst:
                        worst, where = notch, f"{ax} face, corner ({sx},{sy}), z={z:.2f}"
    rep.add("outer_corner_notch", worst <= opt.corner_tol, f"worst notch {worst*1000:.1f} mm ({where}) vs limit {opt.corner_tol*1000:.0f} mm")


def ceiling_join(body, rep, opt):
    obs = import_any(opt.ceiling_from)
    cl = [o for o in obs if o.type == "MESH" and o.name.startswith("Ceiling")]
    if not cl:
        rep.add("ceiling_join", False, "no Ceiling object in --ceiling-from")
        return
    cb = world_bm(cl)
    clo, chi = bbox_of(cb)
    for o in obs:
        bpy.data.objects.remove(o, do_unlink=True)
    wb = tri_bm(body)
    tree = BVHTree.FromBMesh(wb, epsilon=0.0)
    wlo, whi = bbox_of(wb)
    worst = 0.0
    for z in linspace(clo.z, chi.z, 5):
        for sg in (-1, 1):
            for t in linspace(-HALF + 0.01, HALF - 0.01, 41):
                for o, d in ((Vector((t, sg * 6.0, z)), Vector((0, -sg, 0))), (Vector((sg * 6.0, t, z)), Vector((-sg, 0, 0)))):
                    h = tree.ray_cast(o, d, 20.0)
                    worst = max(worst, HALF if h[0] is None else HALF - (6.0 - h[3]))
    rep.add("ceiling_join", whi.z >= chi.z - 1e-3 and worst <= opt.corner_tol,
            f"wall top z {whi.z:.3f} vs ceiling {clo.z:.3f}..{chi.z:.3f}; worst wall-face gap to the cell edge in that z range {worst*1000:.1f} mm")
    wb.free()
    cb.free()


def door_checks(objs, rep, opt):
    by = {o.name: o for o in objs}
    door, lock = by.get("Door"), by.get("Lock")
    rep.add("door_leaf", door is not None, "Door object present")
    if door is not None:
        w = door.matrix_world.translation
        rep.add("door_pivot", (w - Vector((-1.0, 0.0, 0.0))).length < 2e-3, f"Door origin {fmt(w)} (hinge at x=-1)")
        b = world_bm([door])
        lo, hi = bbox_of(b)
        rep.add("door_extent", lo.x >= -1.0 - 2e-3 and hi.x <= 1.0 + 2e-3 and hi.z <= 3.1 + 2e-3,
                f"leaf x {lo.x:.3f}..{hi.x:.3f}, top z {hi.z:.3f} (opening x in [-1,1], leaf up to z 3.1)")
        b.free()
    if opt.expect_lock or lock is not None:
        rep.add("lock_parent", lock is not None and lock.parent is door, "Lock present and parented to Door")


# ------------------------------------------------------------------ commands

def parse_args():
    argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
    ap = argparse.ArgumentParser(prog="tripo_tiles")
    sub = ap.add_subparsers(dest="cmd", required=True)

    def common(p):
        p.add_argument("--kind", choices=KINDS)
        p.add_argument("--name")
        p.add_argument("--out-dir")
        p.add_argument("--tol", type=float, default=0.02)
        p.add_argument("--seam-tol", type=float, default=0.001)
        p.add_argument("--corner-tol", type=float, default=0.03)
        p.add_argument("--strict-verts", action="store_true")
        p.add_argument("--partner", action="append", default=[], help="other processed FBX(s) tested for seams against this piece")
        p.add_argument("--ceiling-from")
        p.add_argument("--stair", choices=("up", "down"))
        p.add_argument("--stair-rise", type=float, default=2.5)
        p.add_argument("--expect-uv", action="store_true")
        p.add_argument("--expect-faces", action="store_true")
        p.add_argument("--expect-ceiling", action="store_true")
        p.add_argument("--expect-lock", action="store_true")
        p.add_argument("--strict", action="store_true", help="exit code 3 when any FAIL is reported")
        p.add_argument("--install", action="store_true", help="allow --out-dir inside the repo Assets/ tree")
    p = sub.add_parser("process")
    common(p)
    p.add_argument("--input", required=True)
    p.add_argument("--pre-rotate", default="0,0,0", help="degrees x,y,z applied first (orientation)")
    p.add_argument("--rotate-z", type=float, default=0.0)
    p.add_argument("--no-fit", action="store_true")
    p.add_argument("--no-normals", action="store_true")
    p.add_argument("--depth-mode", choices=("scale", "clamp"), default="scale")
    p.add_argument("--relief-depth", type=float)
    p.add_argument("--level-percentile", type=float)
    p.add_argument("--band")
    p.add_argument("--planar-dissolve", type=float, default=0.0)
    p.add_argument("--uv", choices=("keep", "planar"), default="keep")
    p.add_argument("--texture")
    p.add_argument("--keep-from")
    p.add_argument("--split-faces", action="store_true")
    p.add_argument("--door-leaf-bbox", default="-1,-0.2,0,1,0.2,3.1")
    p.add_argument("--lock-bbox")
    p = sub.add_parser("build-wall")
    common(p)
    for f in "nesw":
        p.add_argument(f"--{f}")
    p.add_argument("--texture")
    p = sub.add_parser("validate")
    common(p)
    p.add_argument("--input", required=True)
    opt = ap.parse_args(argv)
    if getattr(opt, "kind", None) is None and opt.cmd != "build-wall":
        ap.error("--kind required")
    for attr in ("input", "texture", "keep_from", "ceiling_from", "n", "e", "s", "w", "out_dir"):
        if getattr(opt, attr, None):
            setattr(opt, attr, os.path.abspath(getattr(opt, attr)))
    opt.partner = [os.path.abspath(x) for x in opt.partner]
    opt.band_tuple = None
    if getattr(opt, "band", None) is not None:
        b = [float(t) for t in opt.band.split(",")]
        opt.band_tuple = tuple(b * 4) if len(b) == 1 else tuple(b)
        if len(opt.band_tuple) != 4:
            ap.error("--band wants 1 or 4 values")
    return opt


def guard_out(opt):
    out = os.path.abspath(opt.out_dir)
    assets = os.path.join(REPO, "Assets")
    if os.path.normcase(out).startswith(os.path.normcase(assets)) and not opt.install:
        raise SystemExit("refusing to write inside Assets/ without --install")
    os.makedirs(out, exist_ok=True)
    return out


def export_piece(objs, out_dir, name, texture_png=None):
    path = os.path.join(out_dir, name + ".fbx")
    if texture_png:
        tdir = os.path.join(out_dir, name + "_tex")
        os.makedirs(tdir, exist_ok=True)
        dst = os.path.join(tdir, name + ".png")
        if os.path.abspath(texture_png) != os.path.abspath(dst):
            shutil.copyfile(texture_png, dst)
    # Tripo install tool: writes (possibly Tripo-marked) pieces on purpose, so bypass the overwrite guard
    A.export_fbx(path, objects=objs, path_mode="RELATIVE" if texture_png else "STRIP", force=True)
    meta = path + ".meta"
    return path, meta


def finish(kind, objs, out_dir, name, opt, log, texture=None):
    """Export, re-import the exported FBX in a clean scene and validate that file."""
    path, meta = export_piece(objs, out_dir, name, texture)
    print(f"[export] {path} ({os.path.getsize(path)} bytes); .meta exists next to it: {os.path.exists(meta)} (never written by this tool)")
    clear_scene()
    objs2 = import_any(path)
    partners = []
    for pth in opt.partner:
        pobs = import_any(pth)
        pb = world_bm(body_objects(pobs, kind) if not any(is_tile_part(o.name) for o in pobs if o.type == 'MESH')
                      else [o for o in pobs if o.type == 'MESH' and is_tile_part(o.name)])
        partners.append((os.path.basename(pth), pb))
        for o in pobs:
            bpy.data.objects.remove(o, do_unlink=True)
    rep = Report(f"{name} ({kind}) file: {os.path.basename(path)}")
    for l in log:
        rep.info("process", l)
    validate(kind, objs2, rep, opt, partners)
    rep.dump()
    with open(os.path.join(out_dir, name + ".report.json"), "w", encoding="utf-8") as fh:
        json.dump(rep.as_json(), fh, indent=1, ensure_ascii=False)
    return rep


def rebake_world(o, origin=None):
    """Make an imported object axis-clean: geometry in world coordinates (minus origin), identity rotation/scale."""
    bpy.context.view_layer.update()
    mw = o.matrix_world.copy()
    o.parent = None
    if o.type == "MESH":
        o.data.transform(mw if origin is None else Matrix.Translation(-origin) @ mw)
        o.matrix_world = Matrix.Identity(4) if origin is None else Matrix.Translation(origin)
    else:
        o.matrix_world = Matrix.Translation(mw.translation)
    return o


def keep_special(src, collect):
    """Copy Ceiling*/LightAnchor*/Spot_* things from an existing FBX unchanged into the current scene."""
    obs = import_any(src)
    keep = [o for o in obs if is_special(o.name)]
    for o in obs:
        if o not in keep:
            bpy.data.objects.remove(o, do_unlink=True)
    for o in keep:
        rebake_world(o)
        collect.append(o)


def cmd_process(opt):
    out_dir = guard_out(opt)
    name = opt.name or os.path.splitext(os.path.basename(opt.input))[0]
    kind = opt.kind
    clear_scene()
    objs = import_any(opt.input)
    body = body_objects(objs, kind) if kind != "prop" else [o for o in objs if o.type == "MESH"]
    if not body:
        raise SystemExit("no mesh in input")
    presplit = {}  # a door that is already Door/Lock is passed through (only re-based), not re-split
    if kind == "door":
        for o in objs:
            if o.type == "MESH" and o.name in ("Door", "Lock"):
                presplit[o.name] = o
        if "Door" in presplit:
            door_origin = presplit["Door"].matrix_world.translation.copy()
            lock_src = presplit.get("Lock")
            dobj_pre = rebake_world(presplit["Door"], origin=door_origin)
            if lock_src is not None:
                rebake_world(lock_src)
                lock_src.parent = dobj_pre
                lock_src.matrix_parent_inverse = Matrix.Translation(door_origin).inverted()
    materials = []
    for o in body:
        materials += [m for m in o.data.materials if m and m not in materials]
    obj = bake_to_single_mesh(body, name)
    # drop every other imported object (empties, armatures from the import)
    for o in list(bpy.data.objects):
        if o is not obj and o not in presplit.values():
            bpy.data.objects.remove(o, do_unlink=True)
    bm = bmesh.new()
    bm.from_mesh(obj.data)
    old_mesh = obj.data
    bpy.data.objects.remove(obj, do_unlink=True)  # frees the piece name for the cleaned object
    bpy.data.meshes.remove(old_mesh)
    log = []
    rx, ry, rz = [math.radians(float(t)) for t in opt.pre_rotate.split(",")]
    rot = Matrix.Rotation(math.radians(opt.rotate_z), 4, "Z") @ Matrix.Rotation(rz, 4, "Z") @ Matrix.Rotation(ry, 4, "Y") @ Matrix.Rotation(rx, 4, "X")
    bmesh.ops.transform(bm, matrix=rot, verts=bm.verts)
    tex_mat = None
    if opt.texture:
        tex_mat = make_material("M_" + name, opt.texture)
    if kind in PARAMS:
        process_shell(bm, kind, opt, log)
    elif kind == "prop":
        weld(bm)
        if not opt.no_normals and is_closed(bm):
            recalc_normals(bm)
    else:
        process_block(bm, kind, opt, log)
    if (opt.uv == "planar" or tex_mat) and kind in ("wall-module", "floor"):
        uv_project(bm, kind)
    triangulate(bm)
    set_flat(bm)
    mats = [tex_mat] if tex_mat else materials
    final_objs = []
    if kind == "wall" and opt.split_faces:
        final_objs += split_wall_faces(bm, mats)
    elif kind == "door" and presplit:
        final_objs.append(new_obj(name, bm, mats))
        final_objs += list(presplit.values())
        log.append("door already split into Door/Lock: passed through, origin re-based")
    elif kind == "door":
        leaf, lock, frame = split_door(bm, opt, log)
        main = new_obj(name, frame, mats)
        dobj = new_obj("Door", leaf, mats)
        # leaf origin = hinge (x=-1): shift object origin, keep geometry in place
        dobj.data.transform(Matrix.Translation((1.0, 0, 0)))
        dobj.location = (-1.0, 0.0, 0.0)
        final_objs += [main, dobj]
        if len(lock.faces):
            lobj = new_obj("Lock", lock, mats)
            lobj.parent = dobj
            lobj.matrix_parent_inverse = Matrix.Translation((1.0, 0, 0))  # geometry stays in world coordinates
            final_objs.append(lobj)
        else:
            lock.free()
        leaf.free()
        frame.free()
    else:
        final_objs.append(new_obj(name, bm, mats))
    bm.free()
    if opt.keep_from:
        keep_special(opt.keep_from, final_objs)
    rep = finish(kind, final_objs, out_dir, name, opt, log, texture=opt.texture)
    sys.exit(3 if (rep.failed and opt.strict) else 0)


def cmd_build_wall(opt):
    out_dir = guard_out(opt)
    kind = "wall"
    name = opt.name or "wall_block"
    mods = {"N": opt.n, "E": opt.e or opt.n, "S": opt.s or opt.n, "W": opt.w or opt.n}
    if not mods["N"]:
        raise SystemExit("--n required")
    clear_scene()
    final = []
    mats = []
    for letter, ang in (("N", 0), ("E", 90), ("S", 180), ("W", 270)):
        obs = import_any(mods[letter])
        src = [o for o in obs if o.type == "MESH" and not is_special(o.name)]
        o = bake_to_single_mesh(src, "Face_" + letter)
        for x in list(bpy.data.objects):
            if x not in (o, *final):
                bpy.data.objects.remove(x, do_unlink=True)
        o.data.transform(Matrix.Rotation(math.radians(ang), 4, "Z"))
        final.append(o)
        mats += [m for m in o.data.materials if m and m not in mats]
    # Core box +-1.80 x 0..4.5 (closed, hidden inside the faces)
    cb = bmesh.new()
    bmesh.ops.create_cube(cb, size=1.0)
    for v in cb.verts:
        v.co = Vector((v.co.x * 2 * BACK_D, v.co.y * 2 * BACK_D, (v.co.z + 0.5) * WALL_H))
    final.append(new_obj("Core", cb, mats[:1]))
    cb.free()
    for o in final:
        bm = bmesh.new()
        bm.from_mesh(o.data)
        recalc_normals(bm) if is_closed(bm) else None
        set_flat(bm)
        bm.to_mesh(o.data)
        bm.free()
    rep = finish(kind, final, out_dir, name, opt, ["assembled from " + ", ".join(f"{k}={os.path.basename(v)}" for k, v in mods.items())],
                 texture=opt.texture)
    sys.exit(3 if (rep.failed and opt.strict) else 0)


def cmd_validate(opt):
    clear_scene()
    objs = import_any(opt.input)
    partners = []
    for pth in opt.partner:
        pobs = import_any(pth)
        pb = world_bm(body_objects(pobs, opt.kind) if not any(is_tile_part(o.name) for o in pobs if o.type == "MESH")
                      else [o for o in pobs if o.type == "MESH" and is_tile_part(o.name)])
        partners.append((os.path.basename(pth), pb))
        for o in pobs:
            bpy.data.objects.remove(o, do_unlink=True)
    rep = Report(f"{os.path.basename(opt.input)} ({opt.kind})")
    validate(opt.kind, objs, rep, opt, partners)
    rep.dump()
    if opt.out_dir:
        out = guard_out(opt)
        with open(os.path.join(out, os.path.splitext(os.path.basename(opt.input))[0] + ".validate.json"), "w", encoding="utf-8") as fh:
            json.dump(rep.as_json(), fh, indent=1, ensure_ascii=False)
    sys.exit(3 if rep.failed else 0)


def main():
    opt = parse_args()
    {"process": cmd_process, "build-wall": cmd_build_wall, "validate": cmd_validate}[opt.cmd](opt)


if __name__ == "__main__":
    main()
