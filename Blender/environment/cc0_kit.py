"""CC0 part library for the dungeon kits: import pack meshes, bake colour into `Col`, recolour per biome.

Source packs (all CC0, see Blender/third_party/<pack>/README.md):
  kd = KayKit Dungeon Remastered 1.0   (Kay Lousberg)      gradient texture atlas, 8x4 swatches
  kh = KayKit Halloween Bits 1.0        (Kay Lousberg)      gradient texture atlas, 8x4 swatches
  qd = Quaternius Modular Dungeon packs (Quaternius)       flat material colours
  qn = Quaternius Ultimate Stylized Nature (Quaternius)    small colour textures (alpha cards for leaves)

Only the specific files used by the kits are vendored under Blender/third_party/. Override a pack folder with
the environment variable ABYSS_CC0_<PACK> (e.g. ABYSS_CC0_KD=/path/to/Assets/gltf) or `set_source(pack, path)`.

Pipeline contract (Blender/README.md): no textures in the output; colour lives in the face-corner sRGB colour
attribute `Col`; materials are only M_Toon / M_Emit / M_Clear. Each imported part is baked once:
  * every face corner gets the source colour (atlas sampled at its UV, clamped to the face's swatch so gradients
    survive; flat packs use the material colour, linear -> sRGB) in attribute `src`;
  * every face gets an integer `key` naming its colour family ("kd:r0c1" = KayKit atlas row 0 column 1,
    "qd:Rock" = Quaternius material "Rock").
`inst()` copies a baked part into the scene, transforms it and writes `Col` + material per face from a biome
palette: rule = (mode, colour, material) where mode "tint" keeps the source gradient (luminance ratio against the
swatch mean) on a new hue, "set" paints flat, "keep" keeps the source colour.
"""
import math
import os

import bmesh
import bpy
import numpy as np
from mathutils import Euler, Matrix, Vector

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.normpath(os.path.join(HERE, "..", ".."))
THIRD = os.path.join(REPO, "Blender", "third_party")

PACKS = {
    "kd": dict(folder="kaykit_dungeon_remastered", atlas=True, exts=(".gltf.glb", ".glb", ".gltf")),
    "kh": dict(folder="kaykit_halloween_bits", atlas=True, exts=(".gltf", ".glb")),
    "qd": dict(folder="quaternius_modular_dungeons", atlas=False, exts=(".glb", ".gltf")),
    "qn": dict(folder="quaternius_stylized_nature", atlas=False, exts=(".gltf", ".glb")),
}
_SOURCE_OVERRIDE = {}
MATS = ("M_Toon", "M_Emit", "M_Clear")


def set_source(pack, path):
    _SOURCE_OVERRIDE[pack] = path


def source_dir(pack):
    return (_SOURCE_OVERRIDE.get(pack) or os.environ.get("ABYSS_CC0_" + pack.upper())
            or os.path.join(THIRD, PACKS[pack]["folder"]))


def source_file(pack, name):
    d = source_dir(pack)
    for ext in PACKS[pack]["exts"]:
        p = os.path.join(d, name + ext)
        if os.path.isfile(p):
            return p
    raise FileNotFoundError(f"CC0 part {pack}:{name} not found in {d}")


# ---------------------------------------------------------------- colour helpers

def hexrgb(h):
    h = h.lstrip("#")
    return np.array([int(h[i:i + 2], 16) / 255 for i in (0, 2, 4)], np.float32)


def lin2srgb(c):
    c = np.clip(np.asarray(c, np.float32), 0, 1)
    return np.where(c <= 0.0031308, c * 12.92, 1.055 * np.power(c, 1 / 2.4) - 0.055)


def lum(c):
    c = np.asarray(c, np.float32)
    return c[..., 0] * 0.299 + c[..., 1] * 0.587 + c[..., 2] * 0.114


def material(name):
    """The shared slot material (same node setup as abyss_bpy._material, kept local so this module stands alone)."""
    m = bpy.data.materials.get(name)
    if m:
        return m
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    nt = m.node_tree
    bsdf = nt.nodes.get("Principled BSDF")
    attr = nt.nodes.new("ShaderNodeVertexColor")
    attr.layer_name = "Col"
    nt.links.new(attr.outputs["Color"], bsdf.inputs["Base Color"])
    bsdf.inputs["Roughness"].default_value = 0.8
    if name == "M_Emit":
        nt.links.new(attr.outputs["Color"], bsdf.inputs["Emission Color"])
        bsdf.inputs["Emission Strength"].default_value = 2.0
    if name == "M_Clear":
        bsdf.inputs["Alpha"].default_value = 0.7
    return m


# ---------------------------------------------------------------- baking source parts

_KEYS = []          # key id -> key string
_KEY_IDS = {}
_SWATCH_MEAN = {}   # key -> mean sRGB of the source swatch / material
_IMG_CACHE = {}
_PART_CACHE = {}    # (pack, name, sub) -> mesh datablock (world space, attributes src/key)
ORIGINS = {}        # (pack, name, sub) -> world-space origin of the sub object (hinge pivots etc.)


def _key_id(k):
    if k not in _KEY_IDS:
        _KEY_IDS[k] = len(_KEYS)
        _KEYS.append(k)
    return _KEY_IDS[k]


def _image_array(img):
    if img.name not in _IMG_CACHE:
        w, h = img.size
        a = np.empty(w * h * 4, np.float32)
        img.pixels.foreach_get(a)
        _IMG_CACHE[img.name] = a.reshape(h, w, 4)   # row 0 = bottom (v = 0); byte images stay display-encoded
    return _IMG_CACHE[img.name]


def _mat_source(m):
    """(image or None, base colour sRGB) of an imported glTF material."""
    if m is None or not m.node_tree:
        return None, np.array([0.8, 0.8, 0.8], np.float32)
    bsdf = next((n for n in m.node_tree.nodes if n.type == "BSDF_PRINCIPLED"), None)
    img = None
    if bsdf is not None:
        inp = bsdf.inputs["Base Color"]
        stack = [l.from_node for l in inp.links]
        seen = set()
        while stack:
            n = stack.pop()
            if n in seen:
                continue
            seen.add(n)
            if n.type == "TEX_IMAGE" and n.image:
                img = n.image
                break
            for i in n.inputs:
                stack += [l.from_node for l in i.links]
        base = np.array(inp.default_value[:3], np.float32)
    else:
        base = np.array([0.8, 0.8, 0.8], np.float32)
    return img, lin2srgb(base)


def _bake_object(o, pack):
    """Write `src` (corner colour, sRGB) and `key` (face colour family) onto o's mesh; returns alpha per face."""
    me = o.data
    nl, nf = len(me.loops), len(me.polygons)
    src = np.ones((nl, 4), np.float32)
    keys = np.zeros(nf, np.int32)
    falpha = np.ones(nf, np.float32)
    uvl = me.uv_layers.active
    uv = np.zeros(nl * 2, np.float32)
    if uvl:
        uvl.data.foreach_get("uv", uv)
    uv = uv.reshape(nl, 2)
    lstart = np.zeros(nf, np.int32)
    ltot = np.zeros(nf, np.int32)
    mi = np.zeros(nf, np.int32)
    me.polygons.foreach_get("loop_start", lstart)
    me.polygons.foreach_get("loop_total", ltot)
    me.polygons.foreach_get("material_index", mi)
    atlas = PACKS[pack]["atlas"]
    srcs = [_mat_source(m) for m in me.materials] or [(None, np.array([0.8, 0.8, 0.8], np.float32))]
    for f in range(nf):
        ls = slice(lstart[f], lstart[f] + ltot[f])
        m = me.materials[mi[f]] if len(me.materials) else None
        img, base = srcs[min(mi[f], len(srcs) - 1)]
        if img is None:
            src[ls, :3] = base
            k = f"{pack}:{(m.name.split('.')[0] if m else 'none')}"
            _SWATCH_MEAN.setdefault(k, base)
        else:
            arr = _image_array(img)
            h, w = arr.shape[:2]
            fu = uv[ls]
            if atlas:
                cu, cv = fu.mean(0) % 1.0
                col, row = min(int(cu * 8), 7), min(int((1 - cv) * 4), 3)
                u0, u1 = col / 8 + 3 / w, (col + 1) / 8 - 3 / w
                v1, v0 = 1 - row / 4 - 3 / h, 1 - (row + 1) / 4 + 3 / h
                uu = np.clip(fu[:, 0] % 1.0, u0, u1)
                vv = np.clip(fu[:, 1] % 1.0, v0, v1)
                k = f"{pack}:r{row}c{col}"
                if k not in _SWATCH_MEAN:
                    blk = arr[int(v0 * h):int(v1 * h), int(u0 * w):int(u1 * w), :3]
                    _SWATCH_MEAN[k] = blk.reshape(-1, 3).mean(0)
            else:
                uu, vv = fu[:, 0] % 1.0, fu[:, 1] % 1.0
                k = f"{pack}:{m.name.split('.')[0]}"
            px = arr[np.clip((vv * h).astype(int), 0, h - 1), np.clip((uu * w).astype(int), 0, w - 1)]
            if not atlas and (px[:, 3] < 0.5).any():   # corners on transparent texels (alpha cards): opaque colour
                ok = px[:, 3] >= 0.5
                fill = px[ok, :3].mean(0) if ok.any() else _image_mean(img)
                px = px.copy()
                px[~ok, :3] = fill
            src[ls, :3] = px[:, :3]
            falpha[f] = px[:, 3].mean()
            if not atlas:
                _SWATCH_MEAN.setdefault(k, _image_mean(img))
        keys[f] = _key_id(k)
    a = me.attributes.new("src", "FLOAT_COLOR", "CORNER")
    a.data.foreach_set("color", src.ravel())
    ka = me.attributes.new("key", "INT", "FACE")
    ka.data.foreach_set("value", keys)
    return falpha


def _image_mean(img):
    arr = _image_array(img)
    m = arr[..., 3] > 0.5
    return arr[..., :3][m].mean(0) if m.any() else arr[..., :3].reshape(-1, 3).mean(0)


def _alpha_cut(me, grid):
    """Turn alpha-card faces into geometry: subdivide each face into grid x grid cells and keep the opaque ones."""
    uvl = me.uv_layers.active
    imgs = [_mat_source(m)[0] for m in me.materials]
    bm = bmesh.new()
    bm.from_mesh(me)
    uvk = bm.loops.layers.uv.active
    faces = [f for f in bm.faces if imgs and imgs[min(f.material_index, len(imgs) - 1)] is not None]
    if not faces:
        bm.free()
        return
    bmesh.ops.subdivide_edges(bm, edges=list({e for f in faces for e in f.edges}), cuts=grid - 1, use_grid_fill=True)
    kill = []
    for f in bm.faces:
        img = imgs[min(f.material_index, len(imgs) - 1)] if imgs else None
        if img is None:
            continue
        arr = _image_array(img)
        h, w = arr.shape[:2]
        u = sum(l[uvk].uv.x for l in f.loops) / len(f.loops) % 1.0
        v = sum(l[uvk].uv.y for l in f.loops) / len(f.loops) % 1.0
        if arr[min(int(v * h), h - 1), min(int(u * w), w - 1), 3] < 0.5:
            kill.append(f)
    bmesh.ops.delete(bm, geom=kill, context="FACES")
    bm.to_mesh(me)
    bm.free()


def part(pack, name, sub=None, alpha_grid=0):
    """Baked source mesh (world space of the pack file). sub = object-name filter: None = all meshes,
    a string = objects whose name equals it, a callable(name) -> bool."""
    ck = (pack, name, sub if not callable(sub) else sub.__name__, alpha_grid)
    if ck in _PART_CACHE:
        try:
            _PART_CACHE[ck].name   # datablocks die with read_factory_settings / reset_scene
            return _PART_CACHE[ck]
        except ReferenceError:
            _PART_CACHE.clear()
            _IMG_CACHE.clear()
    path = source_file(pack, name)
    before = set(bpy.data.objects)
    bpy.ops.import_scene.gltf(filepath=path)
    new = [o for o in bpy.data.objects if o not in before]
    bpy.context.view_layer.update()
    keep = []
    for o in new:
        if o.type != "MESH":
            continue
        ok = sub is None or (sub(o.name) if callable(sub) else o.name == sub)
        if not ok:
            continue
        me = o.data.copy()
        me.transform(o.matrix_world)
        if o.matrix_world.determinant() < 0:
            me.flip_normals()
        tmp = bpy.data.objects.new("tmp_" + o.name, me)
        bpy.context.scene.collection.objects.link(tmp)
        if alpha_grid:
            _alpha_cut(me, alpha_grid)
        _bake_object(tmp, pack)
        keep.append(tmp)
        ORIGINS[(pack, name, o.name)] = o.matrix_world.translation.copy()
    if not keep:
        raise RuntimeError(f"no mesh matched {pack}:{name}:{sub}")
    for o in new:
        bpy.data.objects.remove(o, do_unlink=True)
    if len(keep) > 1:
        bpy.ops.object.select_all(action="DESELECT")
        for o in keep:
            o.select_set(True)
        bpy.context.view_layer.objects.active = keep[0]
        bpy.ops.object.join()
    o = keep[0]
    me = o.data
    me.name = f"SRC:{pack}:{name}:{ck[2]}"
    for uv in list(me.uv_layers):
        me.uv_layers.remove(uv)
    me.materials.clear()
    me.use_fake_user = True
    bpy.data.objects.remove(o, do_unlink=True)
    for m in list(bpy.data.materials):
        if m.users == 0 and m.name not in MATS:
            bpy.data.materials.remove(m)
    _PART_CACHE[ck] = me
    return me


def origin_of(pack, name, obj_name):
    if (pack, name, obj_name) not in ORIGINS:
        part(pack, name)
    return ORIGINS[(pack, name, obj_name)].copy()


def bounds(me):
    co = np.empty(len(me.vertices) * 3, np.float32)
    me.vertices.foreach_get("co", co)
    co = co.reshape(-1, 3)
    return co.min(0), co.max(0)


# ---------------------------------------------------------------- palettes and placement

def T(loc=(0, 0, 0), rot=(0, 0, 0), scale=1.0):
    s = scale if hasattr(scale, "__len__") else (scale, scale, scale)
    return (Matrix.Translation(Vector(loc)) @ Euler([math.radians(a) for a in rot]).to_matrix().to_4x4()
            @ Matrix.Diagonal((s[0], s[1], s[2], 1.0)))


class Palette:
    """Maps colour-family keys to (mode, colour, material). Patterns: exact key, or 'pack:*' fallback."""

    def __init__(self, rules=None, default=("keep", None, "M_Toon"), gain=1.0):
        self.rules = dict(rules or {})
        self.default = default
        self.gain = gain

    def derive(self, rules=None, **kw):
        p = Palette({**self.rules, **(rules or {})}, kw.get("default", self.default), kw.get("gain", self.gain))
        return p

    def rule(self, key):
        if key in self.rules:
            return self.rules[key]
        pk = key.split(":")[0] + ":*"
        return self.rules.get(pk, self.default)


def _apply_palette(me, pal, jitter=0.0, seed=0):
    nl, nf = len(me.loops), len(me.polygons)
    src = np.empty(nl * 4, np.float32)
    me.attributes["src"].data.foreach_get("color", src)
    src = src.reshape(nl, 4)
    keys = np.empty(nf, np.int32)
    me.attributes["key"].data.foreach_get("value", keys)
    lstart = np.empty(nf, np.int32)
    me.polygons.foreach_get("loop_start", lstart)
    ltot = np.empty(nf, np.int32)
    me.polygons.foreach_get("loop_total", ltot)
    face_of_loop = np.repeat(np.arange(nf), ltot)
    out = src.copy()
    mat_idx = np.zeros(nf, np.int32)
    used = []
    for kid in np.unique(keys):
        key = _KEYS[kid]
        mode, colr, matn = pal.rule(key)
        fmask = keys == kid
        lmask = fmask[face_of_loop]
        s = src[lmask, :3]
        if mode == "tint":
            ref = max(float(lum(_SWATCH_MEAN.get(key, s.mean(0)))), 0.03)
            ratio = np.clip(lum(s) / ref, 0.0, 2.5) ** 0.85
            out[lmask, :3] = np.clip(hexrgb(colr)[None, :] * ratio[:, None] * pal.gain, 0, 1)
        elif mode == "set":
            out[lmask, :3] = hexrgb(colr)
        elif mode == "grad":   # colr = (dark hex, light hex): remap source luminance between two colours
            lo, hi = hexrgb(colr[0]), hexrgb(colr[1])
            t = np.clip(lum(s), 0, 1)[:, None]
            out[lmask, :3] = lo * (1 - t) + hi * t
        if matn not in used:
            used.append(matn)
        mat_idx[fmask] = used.index(matn)
    if jitter:
        rng = np.random.default_rng(seed)
        fj = 1.0 + (rng.random(nf) - 0.5) * 2 * jitter
        out[:, :3] = np.clip(out[:, :3] * fj[face_of_loop][:, None], 0, 1)
    out[:, 3] = 1.0
    col = me.color_attributes.get("Col") or me.color_attributes.new("Col", "BYTE_COLOR", "CORNER")
    # BYTE_COLOR stores sRGB bytes; color_srgb writes the given values unchanged.
    col.data.foreach_set("color_srgb", out.ravel())
    me.color_attributes.active_color = col
    me.materials.clear()
    for m in used:
        me.materials.append(material(m))
    me.polygons.foreach_set("material_index", mat_idx)


def inst(pack, name, pal, loc=(0, 0, 0), rot=(0, 0, 0), scale=1.0, M=None, sub=None, rules=None, oname=None,
         jitter=0.0, seed=0, alpha_grid=0, pre=None):
    """Place a recoloured copy of a part. `pre` = matrix applied in source space before M (e.g. re-centring)."""
    src = part(pack, name, sub, alpha_grid)
    me = src.copy()
    me.use_fake_user = False
    Mx = M if M is not None else T(loc, rot, scale)
    if pre is not None:
        Mx = Mx @ pre
    me.transform(Mx)
    if Mx.determinant() < 0:
        me.flip_normals()
    _apply_palette(me, pal.derive(rules) if rules else pal, jitter, seed)
    o = bpy.data.objects.new(oname or f"{pack}_{name}", me)
    bpy.context.scene.collection.objects.link(o)
    return o


def recolor(o, pal):
    """Re-apply a palette to an object built by inst()/finish() that still has `src`/`key`."""
    _apply_palette(o.data, pal)


# ---------------------------------------------------------------- simple procedural glue (accents only)

def _mesh_obj(name, verts, faces, color, mat):
    me = bpy.data.meshes.new(name)
    me.from_pydata([tuple(v) for v in verts], [], [tuple(f) for f in faces])
    me.update()
    nl = len(me.loops)
    c = np.tile(np.append(hexrgb(color), 1.0), (nl, 1)).astype(np.float32)
    a = me.attributes.new("src", "FLOAT_COLOR", "CORNER")
    a.data.foreach_set("color", c.ravel())
    k = me.attributes.new("key", "INT", "FACE")
    kid = _key_id(f"proc:{mat}:{color}")
    _SWATCH_MEAN.setdefault(_KEYS[kid], hexrgb(color))
    k.data.foreach_set("value", np.full(len(me.polygons), kid, np.int32))
    _apply_palette(me, Palette({_KEYS[kid]: ("keep", None, mat)}))
    o = bpy.data.objects.new(name, me)
    bpy.context.scene.collection.objects.link(o)
    return o


def prism(name, r, h, n, color, mat="M_Toon", loc=(0, 0, 0), rot=(0, 0, 0), r_top=None, twist=0.0, M=None):
    """n-sided prism / frustum (r_top=0 -> pyramid point). Low-poly crystals, flames, posts."""
    rt = r if r_top is None else r_top
    verts, faces = [], []
    for i in range(n):
        a = 2 * math.pi * i / n
        verts.append((math.cos(a) * r, math.sin(a) * r, 0))
    if rt > 1e-5:
        for i in range(n):
            a = 2 * math.pi * i / n + twist
            verts.append((math.cos(a) * rt, math.sin(a) * rt, h))
        for i in range(n):
            j = (i + 1) % n
            faces.append((i, j, n + j, n + i))
        faces.append(tuple(range(n - 1, -1, -1)))
        faces.append(tuple(range(n, 2 * n)))
    else:
        verts.append((0, 0, h))
        for i in range(n):
            faces.append((i, (i + 1) % n, n))
        faces.append(tuple(range(n - 1, -1, -1)))
    o = _mesh_obj(name, verts, faces, color, mat)
    o.data.transform(M if M is not None else T(loc, rot))
    return o


def crystal(name, r, h, color, mat, loc=(0, 0, 0), rot=(0, 0, 0), n=6):
    """Hexagonal crystal: prism body + pointed cap."""
    verts, faces = [], []
    for i in range(n):
        a = 2 * math.pi * i / n
        verts.append((math.cos(a) * r, math.sin(a) * r, 0))
    for i in range(n):
        a = 2 * math.pi * i / n
        verts.append((math.cos(a) * r * 0.92, math.sin(a) * r * 0.92, h * 0.72))
    verts.append((0, 0, h))
    for i in range(n):
        j = (i + 1) % n
        faces.append((i, j, n + j, n + i))
        faces.append((n + i, n + j, 2 * n))
    faces.append(tuple(range(n - 1, -1, -1)))
    o = _mesh_obj(name, verts, faces, color, mat)
    o.data.transform(T(loc, rot))
    return o


def slab(name, x0, y0, x1, y1, z0, z1, color, mat="M_Toon"):
    v = [(x0, y0, z0), (x1, y0, z0), (x1, y1, z0), (x0, y1, z0), (x0, y0, z1), (x1, y0, z1), (x1, y1, z1), (x0, y1, z1)]
    f = [(0, 3, 2, 1), (4, 5, 6, 7), (0, 1, 5, 4), (1, 2, 6, 5), (2, 3, 7, 6), (3, 0, 4, 7)]
    return _mesh_obj(name, v, f, color, mat)


def disc(name, r, z, n, color, mat, loc=(0, 0, 0), r_in=0.0):
    verts, faces = [], []
    if r_in <= 0:
        verts = [(math.cos(2 * math.pi * i / n) * r, math.sin(2 * math.pi * i / n) * r, z) for i in range(n)]
        faces = [tuple(range(n))]
    else:
        for i in range(n):
            a = 2 * math.pi * i / n
            verts += [(math.cos(a) * r_in, math.sin(a) * r_in, z), (math.cos(a) * r, math.sin(a) * r, z)]
        for i in range(n):
            j = (i + 1) % n
            faces.append((2 * i, 2 * i + 1, 2 * j + 1, 2 * j))
    o = _mesh_obj(name, verts, faces, color, mat)
    o.data.transform(T(loc))
    return o


def polyline_strip(name, pts, width, z, color, mat):
    """Flat ribbon along 2D points at height z (lava veins, rune lines)."""
    verts, faces = [], []
    for i, p in enumerate(pts):
        a = Vector(pts[max(i - 1, 0)]); b = Vector(pts[min(i + 1, len(pts) - 1)])
        d = (b - a).normalized()
        nrm = Vector((-d.y, d.x)) * (width(i / max(len(pts) - 1, 1)) if callable(width) else width) / 2
        verts += [(p[0] + nrm.x, p[1] + nrm.y, z), (p[0] - nrm.x, p[1] - nrm.y, z)]
    for i in range(len(pts) - 1):
        faces.append((2 * i, 2 * i + 1, 2 * i + 3, 2 * i + 2))
    return _mesh_obj(name, verts, faces, color, mat)


def flame(name, h, r, color_out, color_in, loc=(0, 0, 0)):
    """Two nested low-poly flame tongues (M_Emit)."""
    a = prism(name + "_o", r, h, 6, color_out, "M_Emit", loc=loc, r_top=0.0, twist=0.0)
    lx, ly, lz = loc
    b = prism(name + "_i", r * 0.55, h * 0.7, 5, color_in, "M_Emit", loc=(lx, ly - r * 0.25, lz + h * 0.05), r_top=0.0)
    return [a, b]


# ---------------------------------------------------------------- assembly and export

def finish(name, objs, origin=(0, 0, 0), keep_src=False):
    """Join objects into one mesh object `name` whose object origin sits at `origin` (world)."""
    objs = [o for o in objs if o is not None]
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
    if not keep_src:
        strip(o)
    bpy.context.view_layer.update()
    return o


def strip(o):
    me = o.data
    for nm in ("src", "key"):
        if nm in me.attributes:
            me.attributes.remove(me.attributes[nm])
    for uv in list(me.uv_layers):
        me.uv_layers.remove(uv)
    me.color_attributes.active_color = me.color_attributes["Col"]
    # merge material slots that join may have duplicated, keep canonical order
    names = [m.name for m in me.materials]
    if len(set(names)) != len(names) or names != [m for m in MATS if m in names]:
        idx = np.empty(len(me.polygons), np.int32)
        me.polygons.foreach_get("material_index", idx)
        order = [m for m in MATS if m in names]
        remap = np.array([order.index(n) for n in names], np.int32)
        me.materials.clear()
        for m in order:
            me.materials.append(material(m))
        me.polygons.foreach_set("material_index", remap[idx])


def empty(name, loc, parent=None):
    e = bpy.data.objects.new(name, None)
    e.empty_display_type = "PLAIN_AXES"
    e.empty_display_size = 0.3
    e.location = loc
    bpy.context.scene.collection.objects.link(e)
    if parent is not None:
        e.parent = parent
        e.matrix_parent_inverse = parent.matrix_world.inverted()
    return e


def tris(o):
    return sum(len(p.vertices) - 2 for p in o.data.polygons) if o.type == "MESH" else 0


def clamp_floor(o, top=0.0, relief=0.0):
    """Floors: clip x/y to the cell and keep every vertex at or below top + relief."""
    me = o.data
    co = np.empty(len(me.vertices) * 3, np.float32)
    me.vertices.foreach_get("co", co)
    co = co.reshape(-1, 3)
    loc = np.array(o.location, np.float32)
    w = co + loc
    w[:, 0] = np.clip(w[:, 0], -2.0, 2.0)
    w[:, 1] = np.clip(w[:, 1], -2.0, 2.0)
    w[:, 2] = np.minimum(w[:, 2], top + relief)
    me.vertices.foreach_set("co", (w - loc).ravel())
    me.update()
