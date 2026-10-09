"""Shared helpers for the hunter-theme dungeon kits B: school, hospital, guild_street.

Built on Blender/environment/_kit_common_b.py (bmesh primitives, finish/export, contact sheets), cc0_kit.py
(KayKit City / Furniture / Restaurant Bits parts baked into `Col`) and cc0_preview.py (the Workbench + post pass
used for the dungeon_v2 previews: torch light pools, fog, bloom). Those shared files are not modified.

Piece contract (Blender/README.md): 1 unit = 1 m, cell = 4 m, origin = cell centre on the floor (z=0),
Blender -Y is the front, colour lives in the 'Col' attribute, materials are only M_Toon / M_Emit / M_Clear.
Wall faces are authored on the -Y side and rotated with K.four_sides. Floor pieces may carry a second root
object named `Ceiling` (z <= CEIL, normals down); DungeonWorld turns its shadow casting off.
"""
import glob
import json
import math
import os
import random
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ENV_DIR = os.path.normpath(os.path.join(HERE, ".."))
LIB_DIR = os.path.normpath(os.path.join(ENV_DIR, "..", "lib"))
for _p in (LIB_DIR, ENV_DIR, HERE):
    if _p not in sys.path:
        sys.path.insert(0, _p)

import bpy  # noqa: E402
from mathutils import Euler, Matrix, Vector  # noqa: E402
import abyss_bpy as A  # noqa: E402
import _kit_common_b as K  # noqa: E402
import cc0_kit as C  # noqa: E402
import cc0_preview as P  # noqa: E402
from _pipeline import PIECE_NAMES  # noqa: E402

PREVIEW_OUT = "/mnt/project-files/art-upgrade/hunter_v2/kits"
A.PREVIEW_DIR = PREVIEW_OUT          # K.render_fit / K.render_cam write here

CELL = 4.0
HALF = 2.0
WALL_TOP = 4.5
CEIL = 4.48              # ceilings hang just under the wall top (walls pierce them, no slit)
FACE_Y = -1.93           # surface of a wall core on its -Y side; details stand out to about -2.0
SLAB_D = 0.43            # depth of the decorated face slab (y from FACE_Y to FACE_Y + SLAB_D)
CORE_Y0 = FACE_Y + SLAB_D  # back of the face slab = front of the wall core (-1.50)
FLOOR_PIECES = ("floor_a", "floor_b", "floor_c")
WALL_PIECES = ("wall_a", "wall_b", "wall_c")
ATMOS_JSON = os.path.join(HERE, "atmosphere_b.json")


def R(seed):
    return random.Random(seed)


def smooth01(x):
    t = min(max(x, 0.0), 1.0)
    return t * t * (3 - 2 * t)


# ---------------------------------------------------------------- primitives (every call returns one object)

def blk(name, size, loc=(0, 0, 0), color="#888888", mat="M_Toon", bevel=0.025, rot=(0, 0, 0), taper=0.0,
        seed=0, rough=0.0, cull=None):
    """Flat-shaded bevelled block; size = full extents."""
    return K.stone(name, size, loc=loc, rot=rot, color=color, mat=mat, bevel=bevel, taper=taper, seed=seed,
                   rough=rough, cull=cull)


def bx(name, size, loc=(0, 0, 0), color="#888888", mat="M_Toon", rot=(0, 0, 0)):
    return A.box(name, size=size, loc=loc, rot=rot, color=color, mat=mat)


def cy(name, r, h, loc=(0, 0, 0), color="#888888", rot=(0, 0, 0), mat="M_Toon", seg=12, r2=None):
    return A.cyl(name, r=r, depth=h, loc=loc, rot=rot, color=color, mat=mat, seg=seg, r2=r2, smooth=False)


def cone(name, r, h, loc=(0, 0, 0), color="#888888", rot=(0, 0, 0), mat="M_Toon", seg=10):
    return A.cyl(name, r=r, depth=h, loc=loc, rot=rot, color=color, mat=mat, seg=seg, r2=0.0, smooth=False)


def ball(name, r, loc=(0, 0, 0), color="#888888", mat="M_Toon", scale=(1, 1, 1), seg=10, rings=6):
    return A.sphere(name, r=r, loc=loc, scale=scale, color=color, mat=mat, seg=seg, rings=rings)


def lathe(name, prof, loc=(0, 0, 0), color="#888888", mat="M_Toon", seg=14):
    return A.lathe(name, prof, loc=loc, color=color, mat=mat, seg=seg)


def pz(name, pts, depth, axis="Y", loc=(0, 0, 0), color="#888888", mat="M_Toon", rot=(0, 0, 0), bevel=0.0):
    """Polygon extruded along axis (centred). axis Y: pts are (x, z) on the XZ plane."""
    return K.prism(name, pts, depth, axis=axis, loc=loc, rot=rot, color=color, mat=mat, bevel=bevel)


def ring(name, big_r, r, loc=(0, 0, 0), color="#888888", rot=(0, 0, 0), mat="M_Toon", seg=24, minor=6):
    return A.torus(name, R=big_r, r=r, loc=loc, rot=rot, color=color, mat=mat, seg=seg, minor=minor)


def tube(name, pts, r, color="#888888", mat="M_Toon", seg=6):
    return A.tube(name, pts, radius=r, color=color, mat=mat, seg=seg)


def fin(name, objs, origin=(0, 0, 0)):
    return K.finish(name, [o for o in objs if o is not None], origin=origin)


def grp(objs, loc=(0, 0, 0), rot=(0, 0, 0), scale=1.0):
    return K.grp_place(objs, loc, rot, scale)


def face_y(depth):
    """Centre y for a detail of this depth that stands on the wall core face (sticks out toward -Y)."""
    return FACE_Y - depth / 2 + 0.01


def panel(name, x0, x1, z0, z1, y, color, depth=0.04, mat="M_Toon"):
    """Flat rectangular plate standing on plane y (sticks out toward -Y)."""
    return bx(name, (x1 - x0, depth, z1 - z0), ((x0 + x1) / 2, y - depth / 2, (z0 + z1) / 2), color, mat)


def rect_pts(x0, y0, x1, y1, g=0.0):
    return [(x0 + g, y0 + g), (x1 - g, y0 + g), (x1 - g, y1 - g), (x0 + g, y1 - g)]


# ---------------------------------------------------------------- signage: hangul-like strokes (no Korean font in the pipeline)

_PATTERNS = [
    [("h", 0.0, 0.36, 0.9), ("h", 0.0, -0.06, 0.7), ("v", -0.3, -0.12, 0.8), ("o", 0.2, -0.24, 0.17)],
    [("h", 0.0, 0.38, 0.9), ("v", -0.3, -0.04, 0.84), ("v", 0.3, -0.04, 0.84)],
    [("o", 0.0, 0.04, 0.36), ("h", 0.0, -0.42, 0.9)],
    [("v", -0.28, 0.0, 0.9), ("h", 0.0, 0.0, 0.8), ("o", 0.22, 0.22, 0.2)],
    [("h", 0.0, 0.38, 0.9), ("o", 0.0, -0.14, 0.4)],
]


def glyphs(prefix, rng, x0, x1, z0, z1, y, color, n=3, depth=0.025, mat="M_Toon"):
    """n syllable-like blocks of strokes filling [x0,x1]x[z0,z1]; y = surface plane, strokes stand out toward -Y."""
    out = []
    w, h = x1 - x0, z1 - z0
    cw = w / n
    s = min(cw, h) * 0.84
    t = max(s * 0.15, 0.022)
    yy = y - depth / 2
    for i in range(n):
        cx = x0 + cw * (i + 0.5)
        cz = z0 + h / 2
        for k, (kind, dx, dz, L) in enumerate(rng.choice(_PATTERNS)):
            px, pz_ = cx + dx * s, cz + dz * s
            nm = f"{prefix}{i}{k}"
            if kind == "h":
                out.append(bx(nm, (L * s, depth, t), (px, yy, pz_), color, mat))
            elif kind == "v":
                out.append(bx(nm, (t, depth, L * s), (px, yy, pz_), color, mat))
            else:
                out.append(ring(nm, L * s * 0.5, t * 0.6, (px, yy, pz_), color, rot=(90, 0, 0), mat=mat, seg=12, minor=4))
    return out


def sign(prefix, rng, x0, x1, z0, z1, y, bg, fg, n=3, depth=0.05, frame=None, pad=0.13, mat="M_Toon"):
    """Signboard: coloured plate, optional frame strips, hangul-like strokes on the front."""
    out = [panel(prefix + "p", x0, x1, z0, z1, y, bg, depth)]
    if frame:
        f = 0.05
        out.append(panel(prefix + "fa", x0, x0 + f, z0, z1, y - depth + 0.004, frame, 0.02))
        out.append(panel(prefix + "fb", x1 - f, x1, z0, z1, y - depth + 0.004, frame, 0.02))
        out.append(panel(prefix + "fc", x0, x1, z0, z0 + f, y - depth + 0.004, frame, 0.02))
        out.append(panel(prefix + "fd", x0, x1, z1 - f, z1, y - depth + 0.004, frame, 0.02))
    out += glyphs(prefix + "g", rng, x0 + pad, x1 - pad, z0 + pad * 0.7, z1 - pad * 0.7, y - depth, fg, n=n,
                  depth=0.025, mat=mat)
    return out


# ---------------------------------------------------------------- common assemblies

def garland(prefix, x0, x1, zs, sag, y, n, colors, flag_w=0.13, flag_h=0.2, string_col="#6b5a4a", seg=24):
    """Pennant string from (x0, zs[0]) to (x1, zs[1]) on plane y, sagging by `sag`; flags hang toward -Y side."""
    m = seg

    def z_at(t):
        return zs[0] + (zs[1] - zs[0]) * t - sag * 4 * t * (1 - t)

    pts = [(x0 + (x1 - x0) * i / m, y, z_at(i / m)) for i in range(m + 1)]
    out = [tube(prefix + "str", pts, 0.012, string_col, seg=3)]
    for i in range(n):
        t = (i + 0.5) / n
        out.append(pz(f"{prefix}f{i}", [(-flag_w / 2, 0), (flag_w / 2, 0), (0, -flag_h)], 0.015, axis="Y",
                      loc=(x0 + (x1 - x0) * t, y - 0.008, z_at(t) - 0.01), color=colors[i % len(colors)]))
    return out


def door_frame(prefix, wall_col, trim_col, w=2.3, h=3.25, depth=0.9, top=4.5):
    """Passage in a wall cell: solid jambs + lintel, opening x in [-w/2,w/2], z in [0,h], passage along Y."""
    jw = (2.0 - w / 2)
    out = [blk(prefix + "jl", (jw, depth, top), (-(2.0 + w / 2) / 2, 0, top / 2), wall_col, bevel=0.03),
           blk(prefix + "jr", (jw, depth, top), ((2.0 + w / 2) / 2, 0, top / 2), wall_col, bevel=0.03),
           blk(prefix + "li", (w, depth, top - h), (0, 0, (top + h) / 2), wall_col, bevel=0.03)]
    # trim strips around the opening on both faces of the frame
    for sy in (-1, 1):
        yy = sy * (depth / 2 + 0.02)
        out.append(blk(prefix + f"tl{sy}", (0.08, 0.05, h), (-w / 2 - 0.03, yy, h / 2), trim_col, bevel=0.012))
        out.append(blk(prefix + f"tr{sy}", (0.08, 0.05, h), (w / 2 + 0.03, yy, h / 2), trim_col, bevel=0.012))
        out.append(blk(prefix + f"tt{sy}", (w + 0.14, 0.05, 0.08), (0, yy, h + 0.03), trim_col, bevel=0.012))
    return out


def make_door(name, frame_objs, leaf_objs, w, lock_objs=None):
    """Frame root `name`; leaf `Door` hinged on its -X jamb (origin at x=-w/2); optional `Lock` parented to Door."""
    root = fin(name, frame_objs)
    leaf = fin("Door", leaf_objs, origin=(-w / 2 + 0.02, 0, 0))
    out = [root, leaf]
    if lock_objs:
        lock = fin("Lock", lock_objs, origin=(0, 0, 0))
        lock.parent = leaf
        lock.matrix_parent_inverse = leaf.matrix_world.inverted()
        out.append(lock)
    return out


def make_lid(parts, depth, height, name="Lid"):
    """Lid object with its hinge on the back top edge (origin at +Y side, top height)."""
    return fin(name, parts, origin=(0, depth / 2, height))


# ---------------------------------------------------------------- KayKit parts (CC0, baked into Col by cc0_kit)

def kpart(pack, name, loc=(0, 0, 0), rot=(0, 0, 0), scale=1.0, M=None):
    """A KayKit part copied into the scene with its own colours (no texture), `src`/`key` stripped."""
    o = C.inst(pack, name, C.Palette(), loc=loc, rot=rot, scale=scale, M=M)
    C.strip(o)
    return o


def kfit(pack, name, box, center=(0.0, 0.0), z0=0.0, rot_z=0.0):
    """A KayKit part stretched to a box (w, d, h) in metres, centred on (x, y), standing on z0."""
    lo, hi = C.bounds(C.part(pack, name))
    lo = Vector(map(float, lo))
    hi = Vector(map(float, hi))
    size = hi - lo
    s = [box[i] / max(size[i], 1e-6) for i in range(3)]
    mid = Vector(((lo.x + hi.x) / 2, (lo.y + hi.y) / 2, lo.z))
    M = (Matrix.Translation((center[0], center[1], z0)) @ Matrix.Rotation(math.radians(rot_z), 4, "Z")
         @ Matrix.Diagonal((s[0], s[1], s[2], 1.0)) @ Matrix.Translation(-mid))
    return kpart(pack, name, M=M)


def kbox_of(pack, name):
    """World-space (size, lo, hi) of a KayKit part (source units = metres)."""
    lo, hi = C.bounds(C.part(pack, name))
    lo = Vector(map(float, lo))
    hi = Vector(map(float, hi))
    return hi - lo, lo, hi


def kstand(pack, name, center=(0.0, 0.0), z0=0.0, scale=1.0, rot_z=0.0):
    """A KayKit part, uniformly scaled, footprint centred on `center`, bottom on z0."""
    _, lo, hi = kbox_of(pack, name)
    mid = Vector(((lo.x + hi.x) / 2, (lo.y + hi.y) / 2, lo.z))
    M = (Matrix.Translation((center[0], center[1], z0)) @ Matrix.Rotation(math.radians(rot_z), 4, "Z")
         @ Matrix.Diagonal((scale, scale, scale, 1.0)) @ Matrix.Translation(-mid))
    return kpart(pack, name, M=M)


# ---------------------------------------------------------------- fake AO / bevel colour

def ao_paint(o, base, dark, band=0.4, corner=0.22, half=1.93, edge_dark=0.28, edge_axes=True):
    """Per-corner colour on a wall block: `dark` for the lowest `band` metres, darker near vertical edges (corners).
    Works in the block's own local space + o.location (blocks are never rotated before finish)."""
    loc = Vector(o.location)

    def fn(co):
        p = co + loc
        t = smooth01(p.z / band)
        c = 0.0
        if edge_axes:
            ex = min(half - abs(p.x), half - abs(p.y))
            c = smooth01(1.0 - ex / corner)
        col = K.mix(dark, base, t)
        k = 1.0 - edge_dark * c
        return tuple(v * k for v in col)

    K.paint_fn(o, fn)
    return o


# ---------------------------------------------------------------- face slab with an optional window recess

def slab_boxes(prefix, col, hole=None, x0=-1.93, x1=1.93, z0=0.0, z1=WALL_TOP - 0.08, bevel=0.012, color_fn=None):
    """Solid face slab (y from FACE_Y to CORE_Y0) with an optional rectangular hole (hx0, hx1, hz0, hz1).
    The hole is a recess: its back is the wall core face, its floor is the slab top at hz0."""
    yc = FACE_Y + SLAB_D / 2
    if hole is None:
        rects = [(x0, x1, z0, z1)]
    else:
        hx0, hx1, hz0, hz1 = hole
        rects = [(x0, hx0, z0, z1), (hx1, x1, z0, z1), (hx0, hx1, z0, hz0), (hx0, hx1, hz1, z1)]
    out = []
    for i, (a, b, c, d) in enumerate(rects):
        if b - a <= 1e-3 or d - c <= 1e-3:
            continue
        out.append(bx(f"{prefix}{i}", (b - a, SLAB_D, d - c), ((a + b) / 2, yc, (c + d) / 2), col))
    return out


def wall_core(prefix, col, h=4.42, cap="#d8cfbd"):
    """Centred core square [-1.5, 1.5]^2 (the back of every face slab) plus the top cap. Face slabs cover the rest."""
    s = -CORE_Y0 * 2
    core = bx(prefix + "core", (s, s, h), (0, 0, h / 2), col)
    return [core, bx(prefix + "cap", (3.96, 3.96, 0.08), (0, 0, WALL_TOP - 0.04), cap)]


def recess_glass(prefix, hole, color="#c9efff"):
    """Glass pane closing a recess window at the face plane."""
    hx0, hx1, hz0, hz1 = hole
    return [bx(prefix + "gl", (hx1 - hx0, 0.02, hz1 - hz0), ((hx0 + hx1) / 2, FACE_Y - 0.005, (hz0 + hz1) / 2),
               color, "M_Clear")]


def frame_strips(prefix, hole, color, w=0.07, depth=0.04):
    """Frame around a recess window (proud of the face slab by `depth`)."""
    hx0, hx1, hz0, hz1 = hole
    y = FACE_Y - depth / 2
    out = [bx(prefix + "fl", (w, depth, hz1 - hz0 + 2 * w), (hx0 - w / 2, y, (hz0 + hz1) / 2), color),
           bx(prefix + "fr", (w, depth, hz1 - hz0 + 2 * w), (hx1 + w / 2, y, (hz0 + hz1) / 2), color),
           bx(prefix + "ft", (hx1 - hx0 + 2 * w, depth, w), ((hx0 + hx1) / 2, y, hz1 + w / 2), color),
           bx(prefix + "fb", (hx1 - hx0 + 2 * w, depth, w), ((hx0 + hx1) / 2, y, hz0 - w / 2), color)]
    return out


# ---------------------------------------------------------------- ceilings

def ceil_panel(name, x0, y0, x1, y1, color, thick=0.1):
    """Ceiling plate whose underside is z = CEIL - thick (hangs just under the wall top)."""
    return bx(name, (x1 - x0, y1 - y0, thick), ((x0 + x1) / 2, (y0 + y1) / 2, CEIL - thick / 2), color)


def fixture(name, x, y, z_top, L, W, rot_z=0.0, housing="#f2f4f5", lamp="#ffffff"):
    """Hanging light: housing bar under z_top plus an M_Emit lens underneath (rot_z in degrees)."""
    h = bx(name + "h", (W + 0.06, L + 0.06, 0.06), (x, y, z_top - 0.03), housing, rot=(0, 0, rot_z))
    lens = bx(name + "l", (W, L, 0.02), (x, y, z_top - 0.07), lamp, "M_Emit", rot=(0, 0, rot_z))
    return [h, lens]


def round_lamp(name, x, y, z_top, r=0.42, ring_col="#dfe9ec", lens="#ffffff"):
    """Round ceiling lamp: white dome, emissive lens and a thin trim ring (hospital)."""
    out = [cy(name + "d", r, 0.1, (x, y, z_top - 0.05), ring_col, seg=18),
           cy(name + "l", r * 0.82, 0.02, (x, y, z_top - 0.11), lens, mat="M_Emit", seg=18),
           ring(name + "r", r * 0.98, 0.025, (x, y, z_top - 0.1), ring_col, seg=20, minor=4)]
    return out


def hang_string(prefix, p0, p1, sag, n, colors, bulb=0.05, mat="M_Emit", string_col="#4a4046", seg=20):
    """Festival string: a sagging wire from p0 to p1 (3D points) with n glowing bulbs along it."""
    pts = []
    for i in range(seg + 1):
        t = i / seg
        x = p0[0] + (p1[0] - p0[0]) * t
        y = p0[1] + (p1[1] - p0[1]) * t
        z = p0[2] + (p1[2] - p0[2]) * t - sag * 4 * t * (1 - t)
        pts.append((x, y, z))
    out = [tube(prefix + "w", pts, 0.012, string_col, seg=3)]
    for i in range(n):
        t = (i + 0.5) / n
        x = p0[0] + (p1[0] - p0[0]) * t
        y = p0[1] + (p1[1] - p0[1]) * t
        z = p0[2] + (p1[2] - p0[2]) * t - sag * 4 * t * (1 - t)
        out.append(ball(f"{prefix}b{i}", bulb, (x, y, z - 0.03), colors[i % len(colors)], mat=mat, seg=6, rings=4))
    return out


def paper_lantern(prefix, x, y, z, color, glow, r=0.16, cord_top=None, cord_col="#4a4046"):
    """Paper lantern on a short cord; M_Emit inner glow. z = lantern centre."""
    out = [ball(prefix + "l", r, (x, y, z), color, scale=(1, 1, 1.18), seg=10, rings=6),
           ball(prefix + "i", r * 0.72, (x, y, z), glow, mat="M_Emit", scale=(1, 1, 1.15), seg=8, rings=5),
           cy(prefix + "k", r * 0.28, 0.05, (x, y, z + r * 1.2), "#c9a24a", seg=8)]
    if cord_top is not None:
        out.append(cy(prefix + "c", 0.006, cord_top - (z + r * 1.2), (x, y, (cord_top + z + r * 1.2) / 2), cord_col,
                      seg=4))
    return out


# ---------------------------------------------------------------- previews: cc0_preview post pass

def atmos_for(ts):
    """AtmospherePreset-style dict (cc0_preview.post keys) from atmosphere_b.json."""
    with open(ATMOS_JSON) as f:
        j = json.load(f)[ts]
    return dict(fog=tuple(j["FogColor"]), fog_range=(j["FogStart"], j["FogEnd"]), bg=tuple(j["BackgroundColor"]),
                sun=tuple(j["SunColor"]), torch=tuple(j["TorchColor"]), bloom=j["Bloom"],
                sat=1.0 + j["Saturation"] / 100.0, dim=1.0)


def post_render(ts, name, eye, target, fov, res, anchors, at, label=None):
    """Workbench frame + cc0_preview post (torch pools, emissive bloom, fog, vignette) -> PREVIEW_OUT/<ts>_<name>.png"""
    sc = bpy.context.scene
    cd = bpy.data.cameras.new("PostCam")
    cd.sensor_fit = "VERTICAL"
    cd.angle_y = math.radians(fov)
    cd.clip_start = 0.1
    cd.clip_end = 300
    cam = bpy.data.objects.new("PostCam", cd)
    sc.collection.objects.link(cam)
    cam.location = Vector(eye)
    cam.rotation_euler = (Vector(target) - Vector(eye)).to_track_quat("-Z", "Y").to_euler()
    sc.camera = cam
    bpy.context.view_layer.update()
    P.workbench(sc, res, tuple(P.srgb_to_lin(at["bg"])))
    base = os.path.join(PREVIEW_OUT, f"{ts}_{name}")
    os.makedirs(PREVIEW_OUT, exist_ok=True)
    rgb, z = P.render_exr(sc, base + "_raw.exr")
    mask = P.emissive_mask(sc, base + "_emit.exr")
    img = P.post(rgb, z, mask, cam, cd, res, anchors, at)
    if label:
        img = P.stamp_label(img, label)
    P.save_png(img, base + ".png")
    for p in (base + "_raw.exr", base + "_emit.exr"):
        if os.path.exists(p):
            os.remove(p)
    bpy.data.objects.remove(cam)
    return base + ".png"


# ---------------------------------------------------------------- pipeline: grid normalisation (ceiling-aware)

def grid_piece(name, builder):
    """Same normalisation as _pipeline.grid_piece, except that a `Ceiling` root keeps its own heights."""
    def build():
        objs = builder()
        if name.startswith("floor_"):
            for o in objs:
                if o.type != "MESH" or o.name.startswith("Ceiling"):
                    continue
                for v in o.data.vertices:
                    v.co.x = max(-2.0, min(2.0, v.co.x))
                    v.co.y = max(-2.0, min(2.0, v.co.y))
                    v.co.z = min(0.0, v.co.z)
                o.data.update()
        elif name.startswith("wall_"):
            meshes = [o for o in objs if o.type == "MESH"]
            verts = [v for o in meshes for v in o.data.vertices]
            lo = [min(v.co[a] for v in verts) for a in range(3)]
            hi = [max(v.co[a] for v in verts) for a in range(3)]
            for v in verts:
                for a in range(3):
                    target_lo, size = (-2.0, 4.0) if a < 2 else (0.0, 4.5)
                    v.co[a] = target_lo + (v.co[a] - lo[a]) * size / (hi[a] - lo[a])
            for o in meshes:
                o.data.update()
        return objs
    return build


def run_kit_b(ts, pieces, layout, extras, world):
    names = [n for n, _ in pieces]
    if len(names) != len(set(names)) or set(names) != set(PIECE_NAMES):
        raise RuntimeError(f"Incomplete or duplicate environment pieces for {ts}: {names}")
    return K.run_kit(ts, [(n, grid_piece(n, fn)) for n, fn in pieces], layout, extras,
                     walls=WALL_PIECES, floors=FLOOR_PIECES, world=world)


# ---------------------------------------------------------------- corridor (first-person) preview

class PreviewSheet(K.Sheet):
    """Sheet that keeps pieces in memory for corridor previews (no FBX export)."""

    def add(self, piece, objs):
        roots = [o for o in objs if o.parent is None]
        everything = K.all_desc(roots)
        self.pieces[piece] = [roots, Vector((0, 0, 0))]
        for o in everything:
            if o not in roots or o.name != piece:
                o.name = f"{piece}.{o.name}"
        return None


def place(sheet, piece, cell, rot=0, base=(0, 0, 0)):
    """Mock instance of a piece at a cell (DungeonWorld.Spawn rule). Returns (mesh copies, LightAnchor points)."""
    roots, off = sheet.pieces[piece]
    bpy.context.view_layer.update()
    M = (Matrix.Translation(Vector(base) + Vector((cell[0] * CELL, cell[1] * CELL, 0)))
         @ Matrix.Rotation(math.radians(rot), 4, "Z") @ Matrix.Translation(-off))
    out, anchors = [], []
    for o in K.all_desc(roots):
        if o.type == "MESH":
            c = o.copy()
            c.parent = None
            bpy.context.scene.collection.objects.link(c)
            c.matrix_world = M @ o.matrix_world
            c["mock"] = 1
            out.append(c)
        elif "LightAnchor" in o.name:
            anchors.append(M @ o.matrix_world.translation)
    bpy.context.view_layer.update()
    return out, anchors


def corridor_preview(ts, builders, plan, label=True):
    """First-person view down a corridor assembled like DungeonWorld (plan from corridor()); eye 1.35 m."""
    A.reset_scene()
    sh = PreviewSheet(ts)
    for piece in sorted({p[0] for p in plan}):
        sh.add(piece, grid_piece(piece, builders[piece])() if piece in FLOOR_PIECES + WALL_PIECES
               else builders[piece]())
    mock, anchors = [], []
    for piece, cell, rot, base in plan:
        m, a = place(sh, piece, cell, rot, base)
        mock += m
        anchors += a
    keep = set(mock)
    for o in bpy.context.scene.objects:
        if o.type == "MESH" and o not in keep:
            o.hide_render = True
    return post_render(ts, "corridor", (0, 0, 1.35), (0, 9, 1.35), 65, (1600, 900), anchors, atmos_for(ts),
                       label=ts if label else None)


# ---------------------------------------------------------------- arena (battle backdrop) export + previews

def arena_scene(ts, builder, sky_cols, world, lights_extra=None):
    """Export + preview a 9 m battle stage. builder() -> (floor_objs, back_objs), called after the scene reset.
    back_objs carry the enclosure (walls, ceiling or facades). sky_cols = (horizon, zenith) of the far sphere."""
    A.reset_scene()
    floor_objs, back_objs = builder()
    floor = K.finish("arena_floor", floor_objs)
    backdrop = K.finish("arena_backdrop", back_objs)
    sky = A.sphere("arena_sky", r=95, loc=(0, 10, 8), color="#ffffff", mat="M_Emit", seg=32, rings=16)
    hz, zn = sky_cols
    K.paint_fn(sky, lambda v: K.ramp([(0.0, hz), (0.5, hz), (1.0, zn)], min(max((v.z + 95) / 190.0, 0.0), 1.0)))
    collider = K.ngon_disc("Col_Ground", 9.4, z=0.0, n=64, color="#888888")
    roots = [floor, backdrop, sky, collider]
    roots += [K.empty("Spot_party", (0, -4, 0)), K.empty("Spot_enemies", (0, 4, 0)),
              K.empty("Spot_camera", (0, -12, 4)), K.empty("LightAnchor_stage", (0, 0, 5))]
    for i, (x, y) in enumerate(((-10.5, 4), (10.5, 4), (-10.5, 14), (10.5, 14))):
        roots.append(K.empty(f"LightAnchor_edge_{i}", (x, y, 2.2)))
    if lights_extra:
        roots += lights_extra
    K.export_piece(ts, "arena", roots)
    collider.hide_render = True
    K.A.save_blend(f"env_{ts}_arena")
    tris = sum(K.tris(o) for o in roots)
    anchors = [o.matrix_world.translation.copy() for o in K.all_desc(roots) if o.name.startswith("LightAnchor")]
    at = atmos_for(ts)
    post_render(ts, "arena_battle", (0, -12, 4), (0, 3, 1), 70, (1600, 900), anchors, at)
    post_render(ts, "arena_wide", (0, -24, 14), (0, 10, 2), 60, (1600, 900), anchors, at)
    # game-camera preview: the in-game battle camera with grey 1.6 m stand-ins at the party and enemy spots
    # (preview only, added after the export so they never reach arena.fbx)
    standins = arena_standins()
    post_render(ts, "arena_game", (0, -10.2, 3.6), (1.4, 0.6, 1.05), 43, (1600, 1000), anchors, at)
    for o in standins:
        bpy.data.objects.remove(o)
    print(f"[arena] {ts}: {tris} tris", flush=True)
    return tris


def arena_standins():
    """Grey 1.6 m capsule stand-ins (cylinder + two end spheres) at the party spots (y -3) and enemy spots (y 3)."""
    out = []
    spots = [(-3.0, -3.0), (-1.0, -3.0), (1.0, -3.0), (3.0, -3.0), (-2.5, 3.0), (0.0, 3.0), (2.5, 3.0)]
    for i, (x, y) in enumerate(spots):
        out.append(A.cyl(f"StandIn_{i}_body", r=0.3, depth=1.0, loc=(x, y, 0.8), color="#8c9096", mat="M_Toon",
                         seg=12, smooth=False))
        for z, tag in ((0.3, "lo"), (1.3, "hi")):
            out.append(A.sphere(f"StandIn_{i}_{tag}", r=0.3, loc=(x, y, z), color="#8c9096", mat="M_Toon",
                                seg=12, rings=8))
    return out


# ---------------------------------------------------------------- publishing

def publish(ts, pieces, layout, extras, world, corridor, arena_fn):
    """Full pipeline for one tileset: FBX pieces + contact sheets, corridor and arena previews."""
    names = [n for n, _ in pieces]
    run_kit_b(ts, pieces, layout, extras, world=world)
    builders = dict(pieces)
    corridor_preview(ts, builders, corridor())
    arena_fn()
    for f in glob.glob(os.path.join(PREVIEW_OUT, f"env_{ts}_*.png")):
        os.replace(f, os.path.join(PREVIEW_OUT, f"{ts}_" + os.path.basename(f)[len(f"env_{ts}_"):]))
    print(f"[hunter_b] {ts}: {len(names)} pieces published", flush=True)
