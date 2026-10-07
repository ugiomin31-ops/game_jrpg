"""In-game-style previews of the CC0 dungeon kits, rendered from the exported FBX files.

* corridor: first-person view down a corridor assembled exactly like Unity's DungeonWorld.Initialize
  (dungeon_layout(): Unity->Blender axes, wall variant (x*17 + y*31) % 3, buried walls skipped, torches on
  (x*13 + y*7) % 9 == 0 cells, decor/overlay dressing from the same CellHash, door_locked rotation, Ceiling
  without shadows), camera at the game's eye height (1.35 m), facing north, vertical FOV 65. Workbench (toon-ish studio light, cavity, outline)
  plus a numpy post pass using the biome's Unity AtmospherePreset: torch point-light pools from the LightAnchor
  empties, emissive bloom, linear fog, background colour, vignette.
* props: contact sheet of the props of every biome (one row per biome).

  blender -b --factory-startup -P Blender/environment/cc0_preview.py -- corridor ember_caverns out.png [--src DIR]
  blender -b --factory-startup -P Blender/environment/cc0_preview.py -- props out.png [--src DIR]
--src = folder holding <tileset>/<piece>.fbx (default Assets/_Game/Resources/Art/Environment).
"""
import math
import os
import struct
import sys

import bpy
import numpy as np
from mathutils import Matrix, Vector

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.normpath(os.path.join(HERE, "..", ".."))
ENV = os.path.join(REPO, "Assets", "_Game", "Resources", "Art", "Environment")
CELL = 4.0

# Unity AtmospherePreset.ForDungeon values (Assets/_Game/Scripts/Runtime/World/Atmosphere.cs): fog colour/range,
# camera background, sun colour, torch colour; bloom/sat approximate the URP volume.
ATMOS = {
    "ember_caverns": dict(fog=(0.24, 0.08, 0.04), fog_range=(6, 36), bg=(0.12, 0.04, 0.02), sun=(1.0, 0.6, 0.38),
                          torch=(1.0, 0.55, 0.25), bloom=1.45, sat=1.18),
    "frost_grotto": dict(fog=(0.42, 0.58, 0.75), fog_range=(7, 40), bg=(0.3, 0.45, 0.62), sun=(0.78, 0.9, 1.0),
                         torch=(0.55, 0.85, 1.0), bloom=1.15, sat=1.05),
    "haunted_crypt": dict(fog=(0.05, 0.04, 0.09), fog_range=(4, 26), bg=(0.02, 0.02, 0.05), sun=(0.55, 0.55, 0.9),
                          torch=(0.6, 0.9, 0.85), bloom=1.3, sat=1.0, dim=0.72),
    "verdant_ruins": dict(fog=(0.6, 0.74, 0.76), fog_range=(14, 60), bg=(0.55, 0.75, 0.85), sun=(1.0, 0.94, 0.8),
                          torch=(1.0, 0.82, 0.5), bloom=0.7, sat=1.2, dim=1.05),
}


# ---------------------------------------------------------------- EXR (uncompressed, Blender multi-part) reader

def _hdr(b, p):
    attrs = {}
    while b[p] != 0:
        e = b.index(b"\0", p); name = b[p:e].decode(); p = e + 1
        e = b.index(b"\0", p); typ = b[p:e].decode(); p = e + 1
        n = struct.unpack("<i", b[p:p + 4])[0]; p += 4
        attrs[name] = (typ, b[p:p + n]); p += n
    return attrs, p + 1


def read_exr(path):
    b = open(path, "rb").read()
    multi = bool(b[5] & 0x10)
    p, headers = 8, []
    while True:
        h, p = _hdr(b, p)
        headers.append(h)
        if not multi or b[p] == 0:
            break
    p += 1 if multi else 0
    out = {}
    for h in headers:
        x0, y0, x1, y1 = struct.unpack("<iiii", h["dataWindow"][1])
        w, hh = x1 - x0 + 1, y1 - y0 + 1
        n = struct.unpack("<i", h["chunkCount"][1])[0] if "chunkCount" in h else hh
        offs = struct.unpack("<%dQ" % n, b[p:p + 8 * n]); p += 8 * n
        chl, q, chans = h["channels"][1], 0, []
        while chl[q] != 0:
            e = chl.index(b"\0", q); chans.append((chl[q:e].decode(), struct.unpack("<i", chl[e + 1:e + 5])[0])); q = e + 17
        for nm, _ in chans:
            out[nm] = np.zeros((hh, w), np.float32)
        for off in offs:
            q = off + (4 if multi else 0)
            y = struct.unpack("<i", b[q:q + 4])[0] - y0; q += 8
            for nm, pt in chans:
                dt, sz = (np.float16, 2) if pt == 1 else (np.float32, 4)
                out[nm][y] = np.frombuffer(b, dt, w, q).astype(np.float32); q += sz * w
    return out


# ---------------------------------------------------------------- scene helpers

_PROTO = {}


def load_piece(src, ts, piece):
    """Import <src>/<ts>/<piece>.fbx once; returns the root objects (hidden prototypes)."""
    key = (ts, piece)
    if key in _PROTO:
        return _PROTO[key]
    before = set(bpy.data.objects)
    bpy.ops.import_scene.fbx(filepath=os.path.join(src, ts, piece + ".fbx"))
    new = [o for o in bpy.data.objects if o not in before]
    for o in new:
        o.name = f"P:{ts}:{piece}:{o.name}"
        o.hide_render = True
        o.hide_set(True)
    _PROTO[key] = [o for o in new if o.parent is None]
    return _PROTO[key]


def place(src, ts, piece, loc, rz=0.0, extra=None):
    """Instance a piece at a world position (Blender), rotation about Z in degrees. Returns (meshes, anchors)."""
    M = Matrix.Translation(Vector(loc)) @ Matrix.Rotation(math.radians(rz), 4, "Z")
    if extra is not None:
        M = M @ extra
    meshes, anchors = [], []
    for root in load_piece(src, ts, piece):
        for o in [root] + list(root.children_recursive):
            if o.type == "MESH":
                c = o.copy()
                c.parent = None
                c.hide_render = False
                bpy.context.scene.collection.objects.link(c)
                c.matrix_world = M @ o.matrix_world
                c.hide_set(False)
                meshes.append(c)
            elif o.type == "EMPTY" and o.name.split(":")[-1].startswith("LightAnchor"):
                anchors.append(M @ o.matrix_world.translation)
    return meshes, anchors


def text(body, loc, size, rot=(0, 0, 0)):
    cu = bpy.data.curves.new("lbl", "FONT")
    cu.body = body
    cu.size = size
    o = bpy.data.objects.new("lbl", cu)
    o.location = loc
    o.rotation_euler = [math.radians(a) for a in rot]
    bpy.context.scene.collection.objects.link(o)
    return o


def workbench(sc, res, world_rgb, outline=True):
    sc.render.engine = "BLENDER_WORKBENCH"
    sh = sc.display.shading
    sh.light = "STUDIO"
    sh.color_type = "VERTEX"
    sh.show_cavity = True
    sh.cavity_type = "BOTH"
    sh.cavity_ridge_factor = 0.6
    sh.cavity_valley_factor = 1.0
    sh.show_object_outline = outline
    sh.object_outline_color = (0.03, 0.02, 0.03)
    sh.show_shadows = True
    sh.shadow_intensity = 0.45
    sh.show_specular_highlight = False
    sc.display.light_direction = (0.35, -0.45, 0.82)
    sc.view_settings.view_transform = "Standard"
    sc.render.resolution_x, sc.render.resolution_y = res
    sc.render.resolution_percentage = 100
    sc.render.film_transparent = False
    sc.world = sc.world or bpy.data.worlds.new("W")
    sc.world.color = world_rgb


def render_exr(sc, path):
    sc.view_layers[0].use_pass_z = True
    s = sc.render.image_settings
    s.media_type = "MULTI_LAYER_IMAGE"
    s.file_format = "OPEN_EXR_MULTILAYER"
    s.exr_codec = "NONE"
    s.color_depth = "32"
    sc.render.filepath = path
    bpy.ops.render.render(write_still=True)
    d = read_exr(path)
    rgb = np.stack([d[k] for k in sorted(d) if k.endswith("Combined.R")] +
                   [d[k] for k in sorted(d) if k.endswith("Combined.G")] +
                   [d[k] for k in sorted(d) if k.endswith("Combined.B")], -1)   # EXR scanline 0 = top row
    z = [d[k] for k in d if k.endswith("Depth.Z") or k.endswith(".Z")]
    return rgb, (z[0] if z else None)


def emissive_mask(sc, path):
    """Second Workbench pass: flat white for M_Emit, black elsewhere."""
    sh = sc.display.shading
    saved = (sh.color_type, sh.light, sh.show_cavity, sh.show_object_outline, sh.show_shadows)
    cols = {}
    for m in bpy.data.materials:
        cols[m.name] = tuple(m.diffuse_color)
        m.diffuse_color = (1, 1, 1, 1) if m.name.startswith("M_Emit") else (0, 0, 0, 1)
    hidden = [o for o in sc.objects if o.type == "FONT" and not o.hide_render]
    for o in hidden:
        o.hide_render = True
    sh.color_type, sh.light, sh.show_cavity, sh.show_object_outline, sh.show_shadows = "MATERIAL", "FLAT", False, False, False
    wc = tuple(sc.world.color)
    sc.world.color = (0, 0, 0)
    rgb, _ = render_exr(sc, path)
    sc.world.color = wc
    for o in hidden:
        o.hide_render = False
    sh.color_type, sh.light, sh.show_cavity, sh.show_object_outline, sh.show_shadows = saved
    for m in bpy.data.materials:
        m.diffuse_color = cols[m.name]
    return rgb.mean(-1)


def blur(img, r):
    """Approximate gaussian: three box blurs along each axis (cumsum)."""
    out = img.astype(np.float32)
    for _ in range(3):
        for ax in (0, 1):
            pad = [(0, 0)] * out.ndim
            pad[ax] = (r + 1, r)
            c = np.cumsum(np.pad(out, pad, mode="edge"), axis=ax)
            n = out.shape[ax]
            out = (np.take(c, np.arange(2 * r + 1, 2 * r + 1 + n), axis=ax) - np.take(c, np.arange(0, n), axis=ax)) / (2 * r + 1)
    return out


def srgb_to_lin(c):
    c = np.asarray(c, np.float32)
    return np.where(c <= 0.04045, c / 12.92, ((c + 0.055) / 1.055) ** 2.4)


def lin_to_srgb(c):
    c = np.clip(c, 0, 1)
    return np.where(c <= 0.0031308, c * 12.92, 1.055 * np.power(c, 1 / 2.4) - 0.055)


def save_png(rgb_srgb, path):
    h, w = rgb_srgb.shape[:2]
    img = bpy.data.images.new("out", w, h, alpha=False)
    px = np.ones((h, w, 4), np.float32)
    px[..., :3] = np.clip(rgb_srgb, 0, 1)[::-1]
    img.pixels.foreach_set(px.ravel())
    img.filepath_raw = path
    img.file_format = "PNG"
    img.save()
    bpy.data.images.remove(img)


# ---------------------------------------------------------------- corridor scene

# A dungeon.json-style floor ('#' wall, '.' floor, S start, T chest, L locked door). Row 0 is north (far); the
# camera stands on S facing north. ORIGIN shifts the cells inside a virtual floor so the per-cell hashes match a
# real map position (the game derives wall variants, torches and dressing from absolute cell coordinates).
CORRIDOR = [
    "#########",
    "####.####",
    "####L####",
    "####T####",
    "##.....##",
    "####.####",
    "####.####",
    "####.####",
    "####S####",
    "#########",
]
ORIGIN = (8, 1)
DIRS = [(0, -1), (1, 0), (0, 1), (-1, 0)]   # Facing North, East, South, West as grid offsets (north = -y)


def cell_hash(x, y, salt):
    """DungeonWorld.CellHash (uint32 arithmetic)."""
    m = 0xFFFFFFFF
    h = (x * 374761393 + y * 668265263 + salt * 2246822519) & m
    h = ((h ^ (h >> 13)) * 1274126177) & m
    return (h ^ (h >> 16)) & 0x7FFFFFFF


def to_blender(ux, uy, uz):
    """Unity world point -> Blender (FBX export: Blender -Y = Unity +Z, Blender +X = Unity -X)."""
    return (-ux, -uz, uy)


def look_yaw(dx, dz):
    """Blender Z rotation (degrees) of Unity Quaternion.LookRotation((dx, 0, dz)) for a piece whose front is -Y."""
    bx, by = -dx, -dz
    return math.degrees(math.atan2(bx, -by))


def dungeon_layout(rows, origin=(0, 0)):
    """Replicates DungeonWorld.Initialize: [(piece, unity_pos, unity_yaw_dir or None)] for every spawned piece."""
    def cell(x, y):
        gx, gy = x - origin[0], y - origin[1]
        if gy < 0 or gy >= len(rows) or gx < 0 or gx >= len(rows[gy]):
            return "#"
        return rows[gy][gx]

    def pos(x, y):
        return (x * CELL, 0.0, -y * CELL)

    out = []
    for gy, line in enumerate(rows):
        for gx in range(len(line)):
            x, y = gx + origin[0], gy + origin[1]
            m = cell(x, y)
            variant = (x * 17 + y * 31) % 3
            if m == "#":
                if any(cell(x + dx, y + dy) != "#" for dx in (-1, 0, 1) for dy in (-1, 0, 1)):
                    out.append(("wall_" + "abc"[variant], pos(x, y), None))
                continue
            if m != ">":
                out.append(("floor_" + "abc"[variant], pos(x, y), None))
            piece = {"T": "chest", "L": "door_locked", ">": "stairs_down", "<": "stairs_up", "H": "spring", "W": "warp",
                     "N": "lore_stone", "X": "trap", "B": "boss_gate"}.get(m)
            if piece == "door_locked" and cell(x, y - 1) == "#" and cell(x, y + 1) == "#":
                out.append((piece, pos(x, y), (1.0, 0.0)))   # Rotate(0, 90, 0): faces +X
            elif piece:
                out.append((piece, pos(x, y), None))
            torch = -1
            if (x * 13 + y * 7) % 9 == 0:
                torch = next((f for f, (dx, dy) in enumerate(DIRS) if cell(x + dx, y + dy) == "#"), -1)
            if torch >= 0:
                dx, dy = DIRS[torch]
                p = pos(x, y)
                out.append(("torch", (p[0] + dx * 1.7, 0.0, p[2] - dy * 1.7), (-dx, dy)))
            if m in ("L", "B", "<", ">"):
                continue
            decor_done = False
            for f, (dx, dy) in enumerate(DIRS):
                if f == torch or cell(x + dx, y + dy) != "#":
                    continue
                h = cell_hash(x, y, f)
                wall = pos(x + dx, y + dy)
                tw = (dx, -dy)          # unit vector cell -> wall in Unity XZ
                if h % 100 < OVERLAY_CHANCE:
                    out.append(("overlay_" + ("1" if h % 2 == 0 else "2"), wall, (-tw[0], -tw[1])))
                if m in ".SE" and not decor_done and (h // 100) % 100 < DECOR_CHANCE:
                    sgn = -1.0 if (h >> 20) & 1 == 0 else 1.0
                    side = (tw[1] * sgn, -tw[0] * sgn)        # Vector3.Cross(up, toWall) * sgn
                    p = pos(x, y)
                    dp = (p[0] + tw[0] * 1.45 + side[0] * 1.0, 0.0, p[2] + tw[1] * 1.45 + side[1] * 1.0)
                    jitter = math.radians(((h >> 21) % 5 - 2) * 12.0)
                    fx, fz = -tw[0], -tw[1]
                    rot = (fx * math.cos(jitter) + fz * math.sin(jitter), -fx * math.sin(jitter) + fz * math.cos(jitter))
                    out.append(("decor_" + str(1 + (h // 10000) % 6), dp, rot))
                    decor_done = True
    return out


OVERLAY_CHANCE = 18   # DungeonWorld.OverlayChance
DECOR_CHANCE = 26     # DungeonWorld.DecorChance


def corridor(src, ts, out, res=(1600, 900), labels=True, rows=CORRIDOR, origin=ORIGIN):
    bpy.ops.wm.read_factory_settings(use_empty=True)
    _PROTO.clear()
    sc = bpy.context.scene
    at = ATMOS[ts]
    anchors = []
    for piece, upos, udir in dungeon_layout(rows, origin):
        rz = look_yaw(*udir) if udir else 0.0
        meshes, a = place(src, ts, piece, to_blender(*upos), rz)
        anchors += a
        for o in meshes:   # Unity: DungeonWorld turns shadow casting off for `Ceiling` renderers
            if o.name.split(":")[-1].startswith("Ceiling"):
                o.visible_shadow = False
    sy, sx = next((gy, line.index("S")) for gy, line in enumerate(rows) if "S" in line)
    ux, uz = (sx + origin[0]) * CELL, -(sy + origin[1]) * CELL
    eye = Vector(to_blender(ux, 1.35, uz))          # DungeonWorld: cell centre + 1.35 m, facing north (Unity +Z)
    cd = bpy.data.cameras.new("Eye")
    cd.sensor_fit = "VERTICAL"
    cd.angle_y = math.radians(65)
    cd.clip_start = 0.1
    cd.clip_end = 300
    cam = bpy.data.objects.new("Eye", cd)
    sc.collection.objects.link(cam)
    cam.location = eye
    cam.rotation_euler = (math.radians(90), 0, math.radians(180))   # level, looking Blender -Y = Unity +Z
    sc.camera = cam
    bg = srgb_to_lin(at["bg"])
    workbench(sc, res, tuple(bg))
    base = os.path.splitext(out)[0]
    rgb, z = render_exr(sc, base + "_raw.exr")
    mask = emissive_mask(sc, base + "_emit.exr")
    img = post(rgb, z, mask, cam, cd, res, anchors, at)
    if labels:
        img = stamp_label(img, ts)
    save_png(img, out)
    for p in (base + "_raw.exr", base + "_emit.exr"):
        if os.path.exists(p):
            os.remove(p)
    return out


def post(rgb, z, mask, cam, cd, res, anchors, at):
    h, w = rgb.shape[:2]
    sky = z > 1e5
    lin = rgb.copy()
    # sun/ambient tint of the toon light (Workbench studio light is neutral): mostly white, a touch of the sun hue
    sun = np.array(at["sun"], np.float32)
    tint = 0.7 + 0.3 * sun / max(sun.max(), 1e-3)
    lin *= tint * 1.25
    # world positions from depth
    aspect = w / h
    ty = math.tan(cd.angle_y / 2)
    tx = ty * aspect
    xs = (np.arange(w) + 0.5) / w * 2 - 1
    ys = 1 - (np.arange(h) + 0.5) / h * 2
    X, Y = np.meshgrid(xs * tx, ys * ty)
    zc = np.where(sky, 1000.0, z)
    pc = np.stack([X * zc, Y * zc, -zc], -1)
    R = np.array(cam.matrix_world.to_3x3(), np.float32)
    t = np.array(cam.matrix_world.translation, np.float32)
    pw = pc @ R.T + t
    # torch light pools (Unity: point light intensity 1.5, range 5.5, no shadows)
    light = np.zeros_like(lin)
    tc = np.array(at["torch"], np.float32)
    for a in anchors:
        d = np.linalg.norm(pw - np.array(a, np.float32), axis=-1)
        f = np.clip(1 - d / 7.0, 0, 1) ** 2
        light += f[..., None] * tc * 1.5
    light[sky] = 0
    lin = lin * (0.8 + light) * at.get("dim", 1.0)
    # emissive surfaces glow at full strength + bloom
    em = (mask > 0.5)[..., None]
    emis = rgb * em * 2.2
    lin = np.where(em, np.maximum(lin, emis), lin)
    glow = blur(emis, 5) * 1.0 + blur(emis, 16) * 0.8 + blur(emis, 42) * 0.5
    lin += glow * at["bloom"] * 0.8
    # linear fog on geometry, background colour elsewhere
    f0, f1 = at["fog_range"]
    fog = np.clip((zc - f0) / (f1 - f0), 0, 1)[..., None]
    fogc = srgb_to_lin(at["fog"])
    lin = lin * (1 - fog) + fogc * fog
    lin[sky] = srgb_to_lin(at["bg"])
    # saturation + vignette
    l = (lin * np.array([0.2126, 0.7152, 0.0722], np.float32)).sum(-1, keepdims=True)
    lin = np.clip(l + (lin - l) * at["sat"], 0, None)
    vx, vy = np.meshgrid(np.linspace(-1, 1, w), np.linspace(-1, 1, h))
    vig = 1 - 0.28 * np.clip((vx ** 2 * 0.8 + vy ** 2) - 0.25, 0, 1) ** 1.2
    lin *= vig[..., None]
    # gentle filmic shoulder
    lin = lin / (1 + 0.25 * lin)
    return lin_to_srgb(lin * 1.12)


# ---------------------------------------------------------------- tiny bitmap font for labels (no PIL)

_FONT = {
    "a": "01110000010111110001011110", "b": "10000100001111010001111100", "c": "00000011101000010000011100",
    "d": "00001000010111110001011110", "e": "01110100011111110000011100", "f": "00110010000111001000010000",
    "g": "01111100010111100001011100", "h": "10000100001111010001100010", "i": "00100000000010000100001000",
    "k": "10000100101110010010100010", "l": "01000010000100001000000110", "m": "00000110101010110101101010",
    "n": "00000111101000110001100010", "o": "00000011101000110001011100", "p": "11110100011111010000100000",
    "r": "00000101101100010000100000", "s": "01111100000111000001111100", "t": "01000111100100001000000110",
    "u": "00000100011000110001011110", "v": "00000100011000101010001000", "w": "00000100011010110101010100",
    "_": "00000000000000000000111110", " ": "00000000000000000000000000", "x": "00000100010101000100010101",
    "y": "10001100010111100001011100", "z": "00000111110001000100011111", "j": "00010000000001000010011000",
    "q": "01111100010111100001000010", "0": "01110100011000110001011100", "1": "00100011000010000100001110",
    "2": "01110000010011001000111110", "3": "11110000010111000001111100", "4": "00010001100101011111000010",
    "5": "11111100001111000001111100", "6": "01110100001111010001011100", "7": "11111000010001000100001000",
    "8": "01110100010111010001011100", "9": "01110100010111100001011100", "/": "00001000100010001000100000",
    "-": "00000000000111000000000000", ".": "00000000000000000000001000", "v_": "",
}


def stamp_label(img, label, scale=4, at=(24, 24), color=(1.0, 0.96, 0.88)):
    """Draw a lowercase label (5x5 bitmap glyphs + shadow) into an sRGB image (row 0 = top)."""
    out = img.copy()
    x0, y0 = at
    for dx, dy, col in ((2, 2, (0, 0, 0)), (0, 0, color)):
        x = x0
        for chr_ in label.lower():
            g = _FONT.get(chr_, _FONT[" "])
            for i in range(25):
                if g[i] == "1":
                    r, c = divmod(i, 5)
                    yy, xx = y0 + dy + r * scale, x + dx + c * scale
                    out[yy:yy + scale, xx:xx + scale] = col
            x += 6 * scale
    return out


# ---------------------------------------------------------------- props sheet

PROP_ROW = ["chest", "torch", "lore_stone", "spring", "warp", "trap",
            "decor_1", "decor_2", "decor_3", "decor_4", "decor_5", "decor_6", "overlay_1", "overlay_2"]


def props(src, out, tilesets=("ember_caverns", "frost_grotto", "haunted_crypt", "verdant_ruins"), width=2600):
    """One rendered strip per biome (same camera), stacked with a label band above each."""
    strips = []
    pitch = 3.3
    for ts in tilesets:
        bpy.ops.wm.read_factory_settings(use_empty=True)
        _PROTO.clear()
        sc = bpy.context.scene
        for i, piece in enumerate(PROP_ROW):
            loc = (i * pitch, 0, 0)
            extra = Matrix.Translation((0, -0.3, -1.1)) if piece == "torch" else None
            if piece.startswith("overlay"):   # authored on the wall face plane y = -2: pull it back into the row
                extra = Matrix.Translation((0, 2.4, -0.9)) @ Matrix.Diagonal((0.7, 0.7, 0.7, 1))
            m, _ = place(src, ts, piece, loc, 0, extra)
            for o in m:
                nm = o.name.split(":")[-1]
                if nm.startswith("Lid"):      # opened like DungeonWorld (Unity -105 deg about X = Blender -X)
                    o.matrix_world = o.matrix_world @ Matrix.Rotation(math.radians(-100), 4, "X")
                if nm.startswith("Spikes"):   # shown extended (exported retracted at z = -0.5)
                    o.matrix_world = Matrix.Translation((0, 0, 0.5)) @ o.matrix_world
        cd = bpy.data.cameras.new("Sheet")
        cd.type = "ORTHO"
        cd.ortho_scale = len(PROP_ROW) * pitch * 1.01
        cam = bpy.data.objects.new("Sheet", cd)
        sc.collection.objects.link(cam)
        rot = Matrix.Rotation(math.radians(68), 4, "X") @ Matrix.Rotation(math.radians(0), 4, "Z")
        cam.rotation_euler = rot.to_euler()
        c = Vector(((len(PROP_ROW) - 1) * pitch / 2, 0, 1.05))
        cam.location = c + rot.to_3x3() @ Vector((0, 0, 60))
        cd.clip_end = 500
        sc.camera = cam
        res = (width, int(width * 3.6 / (len(PROP_ROW) * pitch * 1.01)))
        workbench(sc, res, tuple(srgb_to_lin((0.09, 0.08, 0.11))))
        base = os.path.splitext(out)[0] + "_" + ts
        rgb, z = render_exr(sc, base + "_raw.exr")
        mask = emissive_mask(sc, base + "_emit.exr")
        em = (mask > 0.5)[..., None]
        emis = rgb * em * 1.5
        lin = np.where(em, np.maximum(rgb, emis), rgb) + (blur(emis, 5) * 0.6 + blur(emis, 16) * 0.4) * 0.6
        strip = lin_to_srgb(lin / (1 + 0.2 * lin) * 1.15)
        band = np.full((44, width, 3), 0.06, np.float32)
        band = stamp_label(band, ts, scale=4, at=(16, 12))
        strips += [band, strip]
        for pth in (base + "_raw.exr", base + "_emit.exr"):
            if os.path.exists(pth):
                os.remove(pth)
    foot = np.full((40, width, 3), 0.06, np.float32)
    colw = width / (len(PROP_ROW) * 1.01)
    for i, p in enumerate(PROP_ROW):
        name = p.replace("_", " ")
        cx = width / 2 + (i - (len(PROP_ROW) - 1) / 2) * colw
        foot = stamp_label(foot, name, scale=3, at=(max(0, int(cx - len(name) * 9 + 1.5)), 10), color=(0.75, 0.72, 0.68))
    save_png(np.concatenate(strips + [foot], 0), out)
    return out


def load_png(path):
    img = bpy.data.images.load(path)
    w, h = img.size
    a = np.empty(w * h * 4, np.float32)
    img.pixels.foreach_get(a)
    bpy.data.images.remove(img)
    return a.reshape(h, w, 4)[::-1, :, :3]


def grid2x2(paths, out, gap=8):
    ims = [load_png(p) for p in paths]
    h, w = ims[0].shape[:2]
    sheet = np.full((2 * h + gap, 2 * w + gap, 3), 0.05, np.float32)
    for i, im in enumerate(ims):
        r, c = divmod(i, 2)
        sheet[r * (h + gap):r * (h + gap) + h, c * (w + gap):c * (w + gap) + w] = im
    save_png(sheet, out)
    return out


def main():
    argv = sys.argv[sys.argv.index("--") + 1:]
    src = argv[argv.index("--src") + 1] if "--src" in argv else ENV
    if argv[0] == "corridor":
        corridor(src, argv[1], argv[2])
    elif argv[0] == "all":   # all four corridors + props sheet + 2x2 sheet into folder argv[1]
        outs = []
        for ts in ("ember_caverns", "frost_grotto", "haunted_crypt", "verdant_ruins"):
            outs.append(corridor(src, ts, os.path.join(argv[1], f"corridor_{ts}.png")))
        props(src, os.path.join(argv[1], "props_sheet.png"))
        grid2x2(outs, os.path.join(argv[1], "dungeon_sheet.png"))
    elif argv[0] == "props":
        props(src, argv[1])


if __name__ == "__main__":
    main()
