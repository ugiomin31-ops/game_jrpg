"""Shared helpers for the hunter-theme dungeon kits B: school, hospital, guild_street.

Built on Blender/environment/_kit_common_b.py (bmesh primitives, finish/export, contact sheets) and
_pipeline.py (floor/wall grid normalisation). Those shared files are not modified.

Piece contract (Blender/README.md): 1 unit = 1 m, cell = 4 m, origin = cell centre on the floor (z=0),
Blender -Y is the front, colour lives in the 'Col' attribute, materials are only M_Toon / M_Emit / M_Clear.
Wall faces are authored on the -Y side and rotated with K.four_sides.
"""
import glob
import math
import os
import random
import shutil
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ENV_DIR = os.path.normpath(os.path.join(HERE, ".."))
LIB_DIR = os.path.normpath(os.path.join(ENV_DIR, "..", "lib"))
for _p in (LIB_DIR, ENV_DIR, HERE):
    if _p not in sys.path:
        sys.path.insert(0, _p)

import bpy  # noqa: E402
from mathutils import Matrix, Vector  # noqa: E402
import abyss_bpy as A  # noqa: E402
import _kit_common_b as K  # noqa: E402
from _pipeline import run as pipeline_run, grid_piece  # noqa: E402

PREVIEW_OUT = "/mnt/project-files/art-upgrade/hunter_v1/env_b"
REPO_PREVIEW = os.path.join(A.REPO, "Blender", "preview")
A.PREVIEW_DIR = PREVIEW_OUT  # K.render_fit / K.render_cam write here

CELL = 4.0
FACE_Y = -1.93          # surface of a wall core on its -Y side; details stand out to about -2.0
FLOOR_PIECES = ("floor_a", "floor_b", "floor_c")
WALL_PIECES = ("wall_a", "wall_b", "wall_c")


def R(seed):
    return random.Random(seed)


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


# ---------------------------------------------------------------- previews

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


def corridor_render(ts, builders, plan, world, name="corridor", eye=(0, 0, 1.35), target=(0, 9, 1.35)):
    """First-person view down a corridor. plan: [(piece, (cell_x, cell_y), rot_deg, base_offset)] like DungeonWorld.Spawn."""
    A.reset_scene()
    sh = PreviewSheet(ts)
    for piece in sorted({p[0] for p in plan}):
        sh.add(piece, grid_piece(piece, builders[piece])() if piece in FLOOR_PIECES + WALL_PIECES
               else builders[piece]())
    mock = []
    for piece, cell, rot, base in plan:
        mock += sh.instance(piece, cell, rot=rot, base=base)
    hide = [o for o in bpy.context.scene.objects if o not in mock]
    return K.render_cam(f"{ts}_{name}", loc=eye, target=target, fov_deg=65, res=(1600, 900), world=world,
                        hide=hide)


def corridor_plan(walls, floors, extras, width=(-1, 1), length=(-1, 5)):
    """Corridor along +Y: floor cells at x=0, walls on both sides and at the far end (DungeonWorld layout)."""
    plan = []
    y0, y1 = length
    for y in range(y0, y1):
        plan.append((floors[(y * 5) % 3], (0, y), 0, (0, 0, 0)))
    for y in range(y0, y1 + 1):
        for x in width:
            plan.append((walls[(x * 7 + y * 3) % 3], (x, y), 0, (0, 0, 0)))
    plan.append((walls[1], (0, y1 + 1), 0, (0, 0, 0)))
    return plan + list(extras)


def torch_plan_entry(cell, side, rot_for_side=None):
    """Torch against a wall, 1.7 m out from the cell centre, facing the cell centre (DungeonWorld.Spawn rule)."""
    x = -1.7 if side < 0 else 1.7
    rot = 90 if side < 0 else -90
    return ("torch", cell, rot, (x, 0, 0))


# ---------------------------------------------------------------- arena scaffold

def arena_scene(ts, builder, sky_cols, world, lights_extra=None):
    """Export + render a 9 m battle stage. builder() -> (floor_objs, back_objs), called after the scene reset.
    sky_cols = (horizon, zenith) colours of the far backdrop sphere."""
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
    K.render_cam(f"{ts}_arena_battle", loc=(0, -12, 4), target=(0, 3, 1), fov_deg=70, res=(1600, 900), world=world,
                 hide=[collider])
    K.render_cam(f"{ts}_arena_wide", loc=(0, -24, 14), target=(0, 10, 2), fov_deg=60, res=(1600, 900), world=world,
                 hide=[collider])
    print(f"[arena] {ts}: {tris} tris", flush=True)
    return tris


# ---------------------------------------------------------------- publishing

def publish(ts, pieces, layout, extras, world, corridor, arena_fn):
    """Full pipeline for one tileset: FBX pieces + contact sheets (pipeline), corridor, arena, preview copies."""
    names = [n for n, _ in pieces]
    pipeline_run(ts, pieces, layout, extras, world=world)
    builders = dict(pieces)
    corridor_render(ts, builders, corridor(), world)
    arena_fn()
    os.makedirs(PREVIEW_OUT, exist_ok=True)
    for f in glob.glob(os.path.join(PREVIEW_OUT, f"env_{ts}_*.png")):
        os.replace(f, os.path.join(PREVIEW_OUT, os.path.basename(f)[4:]))
    for key in ("sheet", "corridor", "arena_battle"):
        src = os.path.join(PREVIEW_OUT, f"{ts}_{key}.png")
        if os.path.isfile(src):
            shutil.copy(src, os.path.join(REPO_PREVIEW, f"env_{ts}_{key}.png"))
    print(f"[hunter_b] {ts}: {len(names)} pieces published", flush=True)
