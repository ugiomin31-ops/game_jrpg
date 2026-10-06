"""Dungeon kits v3: the four biome tilesets, each with its own architecture (CC0 KayKit / Quaternius parts +
procedural rock, ice, vault and foliage from arch_geo.py), recoloured per biome.

Replaces the procedural kits for every dungeon piece (the battle `arena.fbx` is untouched). Same 26 piece names,
same grid (1 cell = 4 x 4 m, origin = cell centre floor, floor top z = 0, wall blocks fill x,y in [-2,2] and z in
[0,4.5]; natural rock / ice faces bulge up to ~0.35 m into the corridor and lean in up to ~0.9 m under the
ceiling), same contract objects (`Door` hinged on the -X jamb with `Lock` as its child, `Lid` hinged at the back
top, `Spikes` retracted at z=-0.5, `LightAnchor*` / `Spot_*` empties).
New: in ember / frost / crypt every floor piece (and stairs_down, which replaces the floor) carries a second root
object `Ceiling` hanging below z = 4.48 (cave rock + stalactites, ice + icicles, gothic rib vault);
DungeonWorld turns its shadow casting off. Verdant ruins stay open to the sky. decor_1..6 / overlay_1..2 are
placed by DungeonWorld.Dress (footprint rules at build_decor / build_overlay).

Run (Blender 5.x, headless):
  blender -b --factory-startup -P Blender/environment/dungeon_cc0.py -- [--biome ember_caverns] [--pieces wall_a,door]
                                                                   [--no-export] [--blend]
Sources come from Blender/third_party/<pack>/ (override with ABYSS_CC0_KD / _KH / _QD / _QN, see cc0_kit.py).
"""
import math
import os
import random
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.join(HERE, "..", "lib"))
import bpy  # noqa: E402
from mathutils import Matrix, Vector  # noqa: E402

import abyss_bpy as A  # noqa: E402
import arch_geo as G  # noqa: E402
import cc0_kit as C  # noqa: E402
from cc0_kit import T, Palette, empty, finish, inst  # noqa: E402

PIECES = (
    "floor_a", "floor_b", "floor_c", "wall_a", "wall_b", "wall_c", "door", "door_locked",
    "stairs_down", "stairs_up", "chest", "lore_stone", "trap", "spring", "warp", "torch",
    "decor_1", "decor_2", "decor_3", "decor_4", "decor_5", "decor_6", "overlay_1", "overlay_2",
    "boss_gate", "foe_marker",
)
TILESETS = ("ember_caverns", "frost_grotto", "haunted_crypt", "verdant_ruins")
WALL_H = 4.5
WALL_SZ = 1.125          # KayKit walls are 4 m tall -> 4.5 m
WALL_LEN = 0.9975        # 5 mm short at each end so faces of one block never z-fight at the corners
C_CEIL = G.CEIL          # cave / vault ceilings hang below this (floor pieces carry them as a `Ceiling` object)


# ---------------------------------------------------------------- biome palettes

def palette(c):
    """Colour families of the four packs -> biome colours (sRGB hex). See cc0_kit.Palette for the modes."""
    vein = c["vein"]
    flame = ("tint", c["flame"], "M_Emit")
    r = {
        # KayKit Dungeon atlas
        "kd:r0c1": ("tint", c["stone"], "M_Toon"), "kd:r0c0": ("tint", c["stone_dark"], "M_Toon"),
        "kd:r0c5": ("tint", c["floor"], "M_Toon"), "kd:r0c7": ("tint", c["rock"], "M_Toon"),
        "kd:r0c4": ("tint", c["wood"], "M_Toon"), "kd:r0c2": ("tint", c["wood_light"], "M_Toon"),
        "kd:r0c3": ("tint", c["iron"], "M_Toon"), "kd:r1c0": ("tint", c["metal"], "M_Toon"),
        "kd:r1c2": ("tint", c["metal"], "M_Toon"), "kd:r1c1": ("tint", c["cloth"], "M_Toon"),
        "kd:r0c6": ("tint", c["accent_warm"], "M_Toon"), "kd:r2c0": vein, "kd:r2c1": vein,
        "kd:r2c3": ("tint", c["banner"], "M_Toon"), "kd:r2c6": ("tint", c["banner2"], "M_Toon"),
        "kd:r2c7": flame, "kd:r2c5": ("tint", c["gold"], "M_Toon"), "kd:r3c0": ("tint", c["wax"], "M_Toon"),
        # KayKit Halloween atlas
        "kh:r0c3": ("tint", c["grave"], "M_Toon"), "kh:r0c2": ("tint", c["stone_dark"], "M_Toon"),
        "kh:r0c4": ("tint", c["wax"], "M_Toon"), "kh:r1c2": ("tint", c["bone"], "M_Toon"),
        "kh:r1c7": ("tint", c["wood"], "M_Toon"), "kh:r0c0": ("tint", c["iron"], "M_Toon"),
        "kh:r0c1": ("tint", c["iron"], "M_Toon"), "kh:r3c2": flame, "kh:r1c6": ("tint", c["floor"], "M_Toon"),
        "kh:r1c5": ("tint", c["cloth"], "M_Toon"),
        # Quaternius flat colours
        "qd:Rock": ("tint", c["rock"], "M_Toon"), "qd:RockLight": ("tint", c["stone"], "M_Toon"),
        "qd:Marble": ("tint", c["stone"], "M_Toon"), "qd:Statue": ("tint", c["grave"], "M_Toon"),
        "qd:Bones": ("tint", c["bone"], "M_Toon"), "qd:Bone": ("tint", c["bone"], "M_Toon"),
        "qd:Cobweb": ("set", c["web"], "M_Clear"), "qd:DarkMetal": ("tint", c["iron"], "M_Toon"),
        "qd:Metal": ("tint", c["iron"], "M_Toon"), "qd:DarkSteel": ("tint", c["iron"], "M_Toon"),
        "qd:Steel": ("tint", c["metal"], "M_Toon"), "qd:Iron": ("tint", c["iron"], "M_Toon"),
        "qd:Fire": flame, "qd:Wood": ("tint", c["wood"], "M_Toon"), "qd:DarkWood": ("tint", c["wood"], "M_Toon"),
        "qd:Candle": ("tint", c["wax"], "M_Toon"), "qd:Gold": ("tint", c["gold"], "M_Toon"),
        "qd:Black": ("tint", c["iron"], "M_Toon"), "qd:Rock_002": ("tint", c["rock"], "M_Toon"),
        # Quaternius nature
        "qn:Grass": ("grad", c["grass"], "M_Toon"), "qn:Flowers": ("keep", None, "M_Toon"),
        "qn:Bush_Leaves": ("grad", c["grass"], "M_Toon"),
    }
    return Palette(r)


BIOMES = {
    "ember_caverns": dict(
        stone="#76574e", stone_dark="#3a2926", floor="#6b4f45", rock="#4f3832", wood="#5b3122",
        wood_light="#7d4a31", iron="#211817", metal="#c79a6a", cloth="#a4664a", accent_warm="#d4572a",
        vein=("set", "#ff8a2a", "M_Emit"), banner="#b5222a", banner2="#d4572a", flame="#ffa23a", gold="#ffc94a",
        wax="#e9cfae", grave="#6a524c", bone="#e2c9a6", web="#d8c8c0", grass=("#4a2a1e", "#8a4a2a"),
        glow="#ff6a1a", glow_hi="#ffd36a", crystal="#ff7a2a", crystal_mat="M_Emit", accent="#ff5a1a",
        world="#3f170c", fog=(0.25, 0.09, 0.05), fog_range=(14, 48), sun=(1.0, 0.78, 0.62), torch=(1.0, 0.55, 0.25),
    ),
    "frost_grotto": dict(
        stone="#a6bfd3", stone_dark="#5d7590", floor="#93abc1", rock="#7f97ad", wood="#6c7388",
        wood_light="#8d93a8", iron="#2a3546", metal="#e3f1ff", cloth="#cfe2f0", accent_warm="#7fb6e0",
        vein=("tint", "#c4efff", "M_Clear"), banner="#2f6db8", banner2="#5aa7e0", flame="#86e4ff", gold="#d8ecff",
        wax="#eef6ff", grave="#b5c8da", bone="#e8eef4", web="#f2f8ff", grass=("#8fb3c8", "#e8f4ff"),
        glow="#7fdcff", glow_hi="#e6fbff", crystal="#a8e8ff", crystal_mat="M_Clear", accent="#5fd0ff",
        world="#122038", fog=(0.12, 0.2, 0.32), fog_range=(14, 50), sun=(0.82, 0.92, 1.05), torch=(0.55, 0.85, 1.0),
    ),
    "haunted_crypt": dict(
        stone="#7b7390", stone_dark="#3d3549", floor="#655d72", rock="#514860", wood="#4d3444",
        wood_light="#6a4a5a", iron="#1c1822", metal="#b9b0cc", cloth="#8a7a96", accent_warm="#8a5aa8",
        vein=("set", "#a86bff", "M_Emit"), banner="#5d2a80", banner2="#3c6a78", flame="#8effd8", gold="#d9c27a",
        wax="#e6ddcc", grave="#7e7690", bone="#e4dac4", web="#e8e4f2", grass=("#3a3446", "#6a5f78"),
        glow="#9a5cff", glow_hi="#dcc8ff", crystal="#b48cff", crystal_mat="M_Emit", accent="#7affd0",
        world="#0b0a16", fog=(0.07, 0.06, 0.13), fog_range=(10, 42), sun=(0.78, 0.76, 1.0), torch=(0.6, 0.9, 0.85),
    ),
    "verdant_ruins": dict(
        stone="#9ea592", stone_dark="#4f7a3c", floor="#878b74", rock="#6f7560", wood="#7a5236",
        wood_light="#9a6a42", iron="#2c3228", metal="#d8c27e", cloth="#d9c79c", accent_warm="#c9853a",
        vein=("tint", "#5aa83c", "M_Toon"), banner="#2f7d4a", banner2="#c9853a", flame="#ffb84d", gold="#f2cc5a",
        wax="#f2e8d0", grave="#9aa086", bone="#e6dcc0", web="#eef2e0", grass=("#2f6a2a", "#9ad25a"),
        glow="#8cffb0", glow_hi="#e8ffe8", crystal="#7dffb0", crystal_mat="M_Emit", accent="#ffd36a",
        world="#1c3329", fog=(0.16, 0.24, 0.2), fog_range=(16, 55), sun=(1.0, 0.96, 0.86), torch=(1.0, 0.82, 0.5),
    ),
}


class Biome:
    def __init__(self, ts):
        self.ts = ts
        self.c = BIOMES[ts]
        self.pal = palette(self.c)
        self.rng = random.Random(ts)

    def __getattr__(self, k):
        try:
            return self.__dict__["c"][k]
        except KeyError:
            raise AttributeError(k)

    def is_(self, *names):
        return self.ts in names


# ---------------------------------------------------------------- shared accents

def crystals(b, center, n=5, size=1.0, spread=0.35, seed=0, tilt=22, mat=None, color=None):
    """Cluster of hexagonal crystals (ice in frost = M_Clear, glowing elsewhere)."""
    rng = random.Random(seed)
    out = []
    for i in range(n):
        a = rng.uniform(0, 360)
        d = spread * (0 if i == 0 else rng.uniform(0.4, 1.0))
        h = size * (1.0 if i == 0 else rng.uniform(0.45, 0.8))
        loc = (center[0] + math.cos(math.radians(a)) * d, center[1] + math.sin(math.radians(a)) * d, center[2])
        out.append(C.crystal(f"cr{i}", 0.09 * size + 0.05 * h, h, color or b.crystal, mat or b.crystal_mat,
                             loc=loc, rot=(rng.uniform(-tilt, tilt) if i else 0, rng.uniform(-tilt, tilt) if i else 0, rng.uniform(0, 60))))
    return out


def icicles(b, y, z, x0, x1, n, seed, depth=1, length=(0.35, 0.9)):
    """Row of icicles hanging below z on the face y (pointing down)."""
    rng = random.Random(seed)
    out = []
    for i in range(n):
        x = x0 + (x1 - x0) * (i + rng.uniform(0.2, 0.8)) / n
        L = rng.uniform(*length)
        out.append(C.prism(f"ic{i}", rng.uniform(0.06, 0.12), L, 5, b.crystal, "M_Clear",
                           M=T((x, y, z), (180, 0, rng.uniform(0, 70)))))
    return out


def grass(b, pts, scale=0.8, seed=0, small=False):
    """Quaternius grass clumps (Grass_Large_Extruded = 516 tris, Grass_Small = 58 tris for scatter)."""
    rng = random.Random(seed)
    name = "Grass_Small" if small else "Grass_Large_Extruded"
    k = 1.6 if small else 1.0
    return [inst("qn", name, b.pal, loc=p, rot=(0, 0, rng.uniform(0, 360)),
                 scale=k * scale * rng.uniform(0.75, 1.15)) for p in pts]


def vines(b, seed, n=5, x0=-1.8, x1=1.8, face_y=-2.0, lmin=1.0, lmax=3.0, top=None):
    """Hanging ivy strands with leaves on the S wall face (plane y = face_y), from the wall top (default 4.5 m) down."""
    top = WALL_H if top is None else top
    rng = random.Random(seed)
    out = []
    for k in range(n):
        x = x0 + (x1 - x0) * (k + rng.uniform(0.2, 0.8)) / n
        L = rng.uniform(lmin, lmax)
        pts = [(x + 0.07 * math.sin(j * 1.7 + k), top - L * j / 8) for j in range(9)]
        strip = C.polyline_strip(f"vine{k}", pts, 0.13, 0.0, "#3f7a2c", "M_Toon")
        strip.data.transform(Matrix(((1, 0, 0, 0), (0, 0, -1, face_y - 0.02 - 0.004 * k), (0, 1, 0, 0), (0, 0, 0, 1))))
        out.append(strip)
        for j in range(1, 9, 2):
            px, pz = pts[j]
            out.append(C.prism(f"leaf{k}_{j}", 0.13, 0.05, 5, ("#5fae3e", "#78c24a", "#4f9a36")[j % 3], "M_Toon",
                               M=T((px + rng.uniform(-0.06, 0.06), face_y - 0.05, pz), (90, 0, rng.uniform(0, 90)))))
    return out


def lowpoly(pack, name, ratio):
    """Name of a decimated copy of a CC0 part, registered in cc0_kit's part cache so inst(pack, <name>) uses it
    (phone budget: e.g. the 344-tri KayKit skull repeated in every burial niche). Rebuilt after a scene reset."""
    key = f"{name}@{ratio}"
    ck = (pack, key, None, 0)
    me = C._PART_CACHE.get(ck)
    try:
        if me is not None:
            me.name
            return key
    except ReferenceError:
        pass
    src = C.part(pack, name)
    m2 = src.copy()
    o = bpy.data.objects.new("lp", m2)
    bpy.context.scene.collection.objects.link(o)
    mod = o.modifiers.new("dec", "DECIMATE")
    mod.ratio = ratio
    bpy.context.view_layer.objects.active = o
    bpy.ops.object.select_all(action="DESELECT")
    o.select_set(True)
    bpy.ops.object.modifier_apply(modifier=mod.name)
    m2 = o.data
    bpy.data.objects.remove(o, do_unlink=True)
    m2.name = f"SRC:{pack}:{key}"
    m2.use_fake_user = True
    C._PART_CACHE[ck] = m2
    return key


def cobweb(b, at, size=1.0, rot=0.0):
    """Corner cobweb: radial threads + sagging rings as thin translucent strips (~60 tris; the CC0 one is 1.1k)."""
    x0, y0, z0 = at
    out = []
    spokes = [math.radians(a) for a in (-90, -60, -30, 0)]   # a quarter fan hanging from the top corner
    for k, a in enumerate(spokes):
        pts = [(0.0, 0.0), (math.cos(a) * size, math.sin(a) * size)]
        out.append(C.polyline_strip(f"web_s{k}", pts, 0.025, 0.0, b.web, "M_Clear"))
    for j, rr in enumerate((0.35, 0.65, 0.95)):
        pts = []
        for k in range(len(spokes) * 2 - 1):
            a = spokes[0] + (spokes[-1] - spokes[0]) * k / (len(spokes) * 2 - 2)
            sag = 0.9 if k % 2 else 1.0
            pts.append((math.cos(a) * rr * size * sag, math.sin(a) * rr * size * sag))
        out.append(C.polyline_strip(f"web_r{j}", pts, 0.02, 0.0, b.web, "M_Clear"))
    for o in out:   # strips are authored in the (x, y) plane: stand them on the wall plane (x, z) at y0
        o.data.transform(T((x0, y0, z0), (0, 0, 0)) @ Matrix(((1, 0, 0, 0), (0, 0, -1, 0), (0, 1, 0, 0), (0, 0, 0, 1)))
                         @ Matrix.Rotation(math.radians(rot), 4, "Z"))
    return out


def candle_flame(b, x, y, z, s=1.0):
    return C.flame("fl", 0.16 * s, 0.045 * s, b.flame, b.glow_hi, loc=(x, y, z))


def rune_glyph(b, cx, y, cz, s=1.0, mat="M_Emit"):
    """A glowing rune (strips on the plane y = const, facing -Y)."""
    strokes = [[(0, -0.5), (0, 0.5)], [(-0.3, 0.25), (0, 0.5), (0.3, 0.25)], [(-0.28, -0.1), (0.28, 0.15)],
               [(-0.25, -0.45), (0.0, -0.25), (0.25, -0.45)]]
    out = []
    for i, st in enumerate(strokes):
        pts = [(cx + p[0] * s, cz + p[1] * s) for p in st]
        o = C.polyline_strip(f"rune{i}", pts, 0.07 * s, 0.0, b.glow, mat)
        o.data.transform(Matrix(((1, 0, 0, 0), (0, 0, -1, y), (0, 1, 0, 0), (0, 0, 0, 1))))  # (x,z) plane at y
        out.append(o)
    return out


# ---------------------------------------------------------------- biome architecture (shared by walls, overlays)
#
# Each biome has its own silhouette (references: Etrian Odyssey strata, DQ caves, Octopath ruins):
#   ember_caverns  natural basalt cave: bulging rock faces that lean in under a rock ceiling, embedded lava veins,
#                  obsidian columns, stalactites, hex-basalt / lava-pool floors.
#   frost_grotto   ice cavern: big faceted ice shards (some translucent over a deep-blue core), snowdrifts,
#                  ice pillars, frozen falls, icicle ceiling, frozen-lake floors.
#   haunted_crypt  gothic crypt: bays of pilasters + cornice, burial niches with skulls/urns, iron grilles,
#                  lancet-arch shrines, rib-vaulted ceiling, tomb-slab floors.
#   verdant_ruins  overgrown ruins under open sky: masonry of mixed heights (full / low / colonnade) with grass
#                  crowns and trees, vines, flower meadows. No ceiling.

def ember_base(z):
    """Shared bulge of ember rock faces: rocky foot, ~0.06 m at torch height, leaning 0.86 m in at the top."""
    return 0.06 + 0.3 * max(0.0, 1 - z / 1.1) ** 2 + 0.8 * max(0.0, (z - 3.0) / 1.5) ** 2


def ember_amp(z):
    return 0.1 + 0.2 * max(0.0, 1 - z) + 0.28 * max(0.0, (z - 3.0) / 1.5)


def frost_base(z):
    return 0.07 + 0.22 * max(0.0, 1 - z / 0.8) ** 2 + 0.5 * max(0.0, (z - 3.3) / 1.2) ** 2


def frost_amp(z):
    return 0.28 + 0.12 * max(0.0, (z - 3.3) / 1.2)


NATURAL_BASE = {"ember_caverns": ember_base, "frost_grotto": frost_base}


def base_of(b):
    return NATURAL_BASE.get(b.ts, lambda z: 0.0)


def ember_rock_col(cu, cz, n, rng):
    up = max(n[2], 0.0)
    down = max(-n[2], 0.0)
    c = G.mix(G.rgb("#6e4636"), G.rgb("#a8735a"), 0.2 + 0.6 * up + 0.2 * G.smooth(0, 4.5, cz))
    c = c * (1 - 0.3 * down)
    c = G.mix(c, G.rgb("#b0533a"), 0.35 * G.smooth(1.2, 0.0, cz))   # lava light bouncing on the foot
    if rng.random() < 0.06:
        c = G.rgb("#3a2c34")
    return c * rng.uniform(0.9, 1.08), "M_Toon"


ICE = ("#a9d8f2", "#8cc4ea", "#c4e8fa", "#7ab0dc", "#b5e0f6")


def frost_ice_col(cu, cz, n, rng):
    if n[2] > 0.45:
        return G.rgb("#eef6ff") * rng.uniform(0.95, 1.02), "M_Toon"
    c = G.rgb(rng.choice(ICE))
    c = G.mix(c, G.rgb("#5d8fc6"), 0.45 * G.smooth(1.4, 0.0, cz))
    c = c * (1 - 0.25 * max(-n[2], 0))
    if rng.random() < 0.14:
        return G.rgb("#c8f0ff"), "M_Clear"   # translucent shard over the deep-blue core
    return c * rng.uniform(0.93, 1.06), "M_Toon"


def rock_ceiling_col(cx, cy, n, rng):
    return G.rgb(rng.choice(("#5a3d33", "#6a473a", "#4c342c"))) * rng.uniform(0.9, 1.1), "M_Toon"


def ice_ceiling_col(cx, cy, n, rng):
    if rng.random() < 0.12:
        return G.rgb("#c8f0ff"), "M_Clear"
    return G.rgb(rng.choice(("#7fb0d8", "#93c4e6", "#6a9cc8"))) * rng.uniform(0.92, 1.06), "M_Toon"


# ---------------------------------------------------------------- floors and ceilings

def floor_tile(b, name, loc=(0, 0, 0), rot=0, scale=1.0, rules=None):
    return inst("kd", name, b.pal, M=T((loc[0], loc[1], loc[2] - 0.05 * (scale if not hasattr(scale, "__len__") else scale[2])),
                                       (0, 0, rot), scale), rules=rules)


def build_ceiling(b, piece):
    """Separate `Ceiling` object (Unity: no shadow casting, see DungeonWorld.Spawn). None for open-sky biomes."""
    seed = sum(map(ord, b.ts + piece))
    if b.is_("ember_caverns"):
        objs = [G.cave_ceiling("ceil", seed, 0.45, rock_ceiling_col)]
        objs += G.stalactites(seed + 1, {"floor_a": 4, "floor_b": 6, "floor_c": 3}.get(piece, 4),
                              ("#4a302b", "#5a3a32", "#3a2622"), length=(0.5, 1.3))
        if piece == "floor_c":   # ember crystals glowing in the rock overhead
            for cr in crystals(b, (1.3, -1.2, C_CEIL), 3, 0.55, seed=seed, mat="M_Emit", color=b.glow_hi):
                cr.data.transform(Matrix.Translation((1.3, -1.2, C_CEIL)) @ Matrix.Rotation(math.pi, 4, "X")
                                  @ Matrix.Translation((-1.3, 1.2, -C_CEIL)))
                objs.append(cr)
    elif b.is_("frost_grotto"):
        objs = [G.cave_ceiling("ceil", seed, 0.35, ice_ceiling_col)]
        objs += G.stalactites(seed + 1, {"floor_a": 7, "floor_b": 9, "floor_c": 6}.get(piece, 7),
                              ("#c8f0ff", "#a8e0ff"), mat="M_Clear", length=(0.4, 1.2), radius=(0.07, 0.16), sides=5)
    elif b.is_("haunted_crypt"):
        objs = G.vault_ceiling("vault", "#241f2e", b.stone, b.glow)
        if piece == "floor_b":   # a hanging lantern every few cells (light comes from torches; this is mood)
            objs.append(inst("kh", "lantern_hanging", b.pal, M=T((0, 0, C_CEIL - 0.2), (0, 0, 20), 0.9)))
    else:
        return None
    return finish("Ceiling", objs)


def build_floor(b, piece):
    objs = []
    relief = 0.0
    seed = sum(map(ord, b.ts + piece))
    r = random.Random(seed)
    if b.is_("ember_caverns"):
        if piece == "floor_a":     # rough basalt ground, a thin lava crack and loose stones
            objs.append(floor_tile(b, "floor_dirt_large_rocky", rot=90, rules={"kd:r0c5": ("tint", "#6a4a3e", "M_Toon")}))
            objs.append(C.polyline_strip("crack", [(-1.7, -0.6), (-0.9, -0.3), (-0.4, 0.35), (0.5, 0.5), (1.1, 1.2), (1.7, 1.45)],
                                         lambda t: 0.09 * (1 - abs(t - 0.5)), 0.012, b.glow, "M_Emit"))
            relief = 0.3
        elif piece == "floor_b":   # basalt hex columns, lava glowing in the seams
            objs.append(G.hex_columns("hex", seed, 0.44, 0.9, (-0.06, 0.0), ("#4a3a3e", "#55413f", "#3e3036"), rim="#241a1e"))
            objs.append(C.slab("lava", -2.0, -2.0, 2.0, 2.0, -0.2, -0.16, b.glow, "M_Emit"))
        else:                      # dark ash ground with a lava pool tucked into one corner
            objs.append(floor_tile(b, "floor_dirt_large", rot=180, rules={"kd:r0c5": ("tint", "#5e4038", "M_Toon")}))
            objs.append(C.disc("pool", 0.62, 0.015, 9, "#ff8a2a", "M_Emit", loc=(1.25, 1.25, 0)))
            objs.append(C.disc("pool_hi", 0.3, 0.02, 7, "#ffd36a", "M_Emit", loc=(1.3, 1.2, 0)))
            for k in range(6):
                a = math.radians(k * 60 + 15)
                objs.append(inst("qd", "modular_dungeon_pack/Rock5", b.pal, M=T((1.25 + math.cos(a) * 0.68, 1.25 + math.sin(a) * 0.68, -0.05), (0, 0, k * 47), 0.75)))
            relief = 0.25
    elif b.is_("frost_grotto"):
        if piece == "floor_a":     # packed snow with drifts along two edges
            objs.append(floor_tile(b, "floor_dirt_large", rot=90, rules={"kd:r0c5": ("tint", "#dbe8f3", "M_Toon")}))
            objs.append(G.mound("drift1", -2, 2, 0.45, 0.14, seed, "#f4f9ff", "#cfe0ef", y_face=2.0))
            d2 = G.mound("drift2", -2, 2, 0.4, 0.12, seed + 1, "#f4f9ff", "#cfe0ef", y_face=2.0)
            d2.data.transform(G.side("N"))   # rotate 180: the second drift hugs the opposite edge
            objs.append(d2)
            relief = 0.2
        elif piece == "floor_b":   # frozen lake: faceted blue ice with a snowy rim
            objs.append(G.faceted_plane("ice", seed, 7, lambda x, y, rr: (G.rgb(rr.choice(("#9fd0ee", "#b8e2f7", "#8cc0e6", "#c9ecfa"))), "M_Toon"),
                                        z=-0.005))
            objs.append(C.slab("under", -2.0, -2.0, 2.0, 2.0, -0.12, -0.02, "#5a86b8"))
            for k, (pts) in enumerate(([(-1.6, -0.2), (-0.6, 0.1), (0.2, -0.4), (1.5, -0.1)], [(0.2, -0.4), (0.4, -1.5)], [(-0.6, 0.1), (-0.3, 1.4)])):
                objs.append(C.polyline_strip(f"crack{k}", pts, 0.035, 0.004, "#eaf8ff", "M_Toon"))
            relief = 0.01
        else:                      # snow with frozen puddles and a crystal growth in a corner
            objs.append(floor_tile(b, "floor_dirt_large", rot=0, rules={"kd:r0c5": ("tint", "#d4e3ef", "M_Toon")}))
            for i, (cx, cy, rad) in enumerate([(-0.8, 0.6, 0.8), (0.7, -0.9, 0.6)]):
                pts = [(cx + math.cos(2 * math.pi * k / 9) * rad * r.uniform(0.75, 1.1),
                        cy + math.sin(2 * math.pi * k / 9) * rad * r.uniform(0.75, 1.1), 0.006) for k in range(9)]
                objs.append(C._mesh_obj(f"puddle{i}", pts, [tuple(range(9))], "#a9dcf5", "M_Toon"))
            objs += crystals(b, (-1.55, -1.55, 0), 4, 0.75, seed=seed)
            relief = 0.8
    elif b.is_("haunted_crypt"):
        if piece == "floor_a":     # worn flagstones, a few bones in the corners
            objs.append(floor_tile(b, "floor_tile_large", rot=90 * r.randint(0, 3)))
            objs.append(inst("kh", lowpoly("kh", "bone_A", 0.5), b.pal, M=T((-1.55, 1.5, 0.05), (0, 0, 35), 0.7)))
            objs.append(inst("kh", lowpoly("kh", "bone_B", 0.5), b.pal, M=T((1.5, -1.6, 0.05), (0, 0, -20), 0.7)))
            relief = 0.12
        elif piece == "floor_b":   # tomb slab set into the paving
            for (x, y), n in zip([(-1, -1), (1, -1), (-1, 1), (1, 1)],
                                 ["floor_tile_small_broken_A", "floor_tile_small", "floor_tile_small", "floor_tile_small_broken_B"]):
                objs.append(floor_tile(b, n, (x, y, 0), 90 * r.randint(0, 3)))
            objs.append(C.slab("slab", -0.75, -1.25, 0.75, 1.25, -0.05, 0.02, "#8a8298"))
            objs.append(C.slab("slab_in", -0.6, -1.1, 0.6, 1.1, 0.02, 0.025, "#6e6680"))
            objs.append(C.polyline_strip("cross_v", [(0, -0.75), (0, 0.85)], 0.09, 0.03, "#3a3346", "M_Toon"))
            objs.append(C.polyline_strip("cross_h", [(-0.4, 0.4), (0.4, 0.4)], 0.09, 0.031, "#3a3346", "M_Toon"))
            relief = 0.03
        else:                      # iron grate over a glowing ossuary pit
            objs.append(floor_tile(b, "floor_tile_big_grate", rot=0))
            objs.append(C.slab("glow", -1.52, -1.52, 1.52, 1.52, -0.75, -0.7, b.glow, "M_Emit"))
            objs.append(inst("kh", lowpoly("kh", "skull", 0.35), b.pal, M=T((0.4, 0.3, -0.69), (0, 0, 40), 0.45)))
            objs.append(inst("kh", lowpoly("kh", "skull", 0.35), b.pal, M=T((-0.5, -0.4, -0.69), (0, 0, 200), 0.4)))
    else:  # verdant_ruins
        if piece == "floor_a":     # meadow with stepping stones along both walking lines
            objs.append(floor_tile(b, "floor_dirt_large", rot=90, rules={"kd:r0c5": ("tint", "#5f8a3f", "M_Toon")}))
            for k, (x, y) in enumerate([(0, -1.3), (0.1, 0.0), (-0.05, 1.3), (-1.3, 0.05), (1.3, -0.05)]):
                objs.append(floor_tile(b, "floor_tile_small", (x, y, 0.07), r.uniform(-20, 20), (0.42, 0.42, 1.0)))
            objs += grass(b, [(-1.6, 1.6, 0), (1.55, -1.6, 0), (1.6, 1.5, 0), (-1.6, -1.5, 0), (0.8, 0.9, 0)], 0.55, seed=11, small=True)
            relief = 0.3
        elif piece == "floor_b":   # old paving, broken and weedy
            names = ["floor_tile_small_weeds_A", "floor_tile_small", "floor_tile_small_broken_A", "floor_tile_small_weeds_B"]
            for (x, y), n in zip([(-1, -1), (1, -1), (-1, 1), (1, 1)], names):
                objs.append(floor_tile(b, n, (x, y, 0), 90 * r.randint(0, 3)))
            objs += grass(b, [(-1.85, 0.2, 0), (0.15, 1.85, 0), (1.8, -0.9, 0)], 0.5, seed=13, small=True)
            relief = 0.22
        else:                      # flower meadow
            objs.append(floor_tile(b, "floor_dirt_large", rot=0, rules={"kd:r0c5": ("tint", "#6f9a48", "M_Toon")}))
            objs += grass(b, [(-1.2, -1.0, 0), (0.9, 1.1, 0), (1.5, -1.4, 0), (-1.5, 1.5, 0), (0.1, -1.7, 0), (-0.4, 0.9, 0)], 0.5, seed=5, small=True)
            objs += flowers(b, [(-1.4, -1.5, 0), (1.45, 1.4, 0), (1.5, -0.6, 0), (-1.5, 0.7, 0), (0.7, -1.55, 0), (-0.6, 1.55, 0),
                                (-1.0, -0.9, 0), (0.9, 0.5, 0)], seed, 0.75)
            relief = 0.6
    o = finish(piece, objs)
    C.clamp_floor(o, 0.0, relief)
    out = [o]
    ceil = build_ceiling(b, piece)
    if ceil is not None:
        out.append(ceil)
    return out


# ---------------------------------------------------------------- walls

SIDES = {"N": ((0, 1.5, 0), 180), "E": ((1.5, 0, 0), 90), "S": ((0, -1.5, 0), 0), "W": ((-1.5, 0, 0), -90)}


def side_matrix(side, local=Matrix.Identity(4)):
    """Matrix that maps a part authored on the S face (outward -Y, face plane y=-2) onto `side`."""
    return G.side(side) @ local


def wall_face(b, name, side, rules=None, zscale=1.0):
    loc, rz = SIDES[side]
    return inst("kd", name, b.pal, M=T(loc, (0, 0, rz), (WALL_LEN, 1, WALL_SZ * zscale)), rules=rules)


def on_side(objs, sd):
    for o in objs:
        o.data.transform(side_matrix(sd))
    return objs


def build_wall(b, piece):
    seed = sum(map(ord, b.ts + piece)) * 13
    builder = {"ember_caverns": ember_wall, "frost_grotto": frost_wall, "haunted_crypt": crypt_wall,
               "verdant_ruins": verdant_wall}[b.ts]
    # foot plug: fills the sliver between bevelled floor-tile edges and the face bottoms (background showed through)
    foot = C.slab("foot", -2.0, -2.0, 2.0, 2.0, -0.3, 0.01, {"ember_caverns": "#3a2620", "frost_grotto": "#cfe0ef",
                                                            "haunted_crypt": "#2a2433", "verdant_ruins": "#3d5a2a"}[b.ts])
    return [finish(piece, builder(b, piece, seed) + [foot])]


def ember_wall(b, piece, seed):
    """Natural basalt: four irregular faces, lava veins embedded in the facets, rubble at the foot."""
    r = random.Random(seed)
    n_cracks = {"wall_a": (1, 0, 1, 0), "wall_b": (1, 1, 0, 1), "wall_c": (2, 2, 1, 2)}[piece]
    objs = [C.slab("core", -1.99, -1.99, 1.99, 1.99, 0.0, WALL_H, "#2a1d1a"),
            C.slab("top", -2.0, -2.0, 2.0, 2.0, WALL_H - 0.01, WALL_H, "#2a1d1a")]
    for k, sd in enumerate("NESW"):
        f = G.relief_face(f"rock{sd}", seed + k, ember_base, ember_amp, ember_rock_col, nu=12, nz=12, jitter=0.32,
                          cracks=G.crack_paths(seed * 3 + k, n_cracks[k]), crack_w=0.1, crack_col=G.rgb("#ff6a1e"))
        acc = []
        for j in range(r.randint(1, 2)):   # loose rocks at the foot
            u = r.uniform(-1.6, 1.6)
            acc.append(inst("qd", r.choice(("modular_dungeon_pack/Rock2", "modular_dungeon_pack/Rock4")), b.pal,
                            M=T(G.face_point(ember_base, u, 0, 0.05)[:2] + (-0.03,), (0, 0, r.uniform(0, 360)), r.uniform(0.7, 1.1))))
        if piece == "wall_b" and sd in "EW":   # obsidian columns
            for j in range(5):
                u = (1.2 if j % 2 else -1.2) + r.uniform(-0.3, 0.3)
                h = r.uniform(0.7, 1.9)
                acc.append(C.crystal(f"obs{j}", r.uniform(0.1, 0.16), h, r.choice(("#2b2233", "#3b2f48", "#463a58")), "M_Toon",
                                     loc=G.face_point(ember_base, u, 0.4, 0.1)[:2] + (0.0,),
                                     rot=(r.uniform(-12, 12), r.uniform(-12, 12), r.uniform(0, 60))))
        if piece == "wall_c" and sd in "NS":   # ember crystals breaking out of the foot
            acc += crystals(b, G.face_point(ember_base, r.choice((-1.1, 1.1)), 0, 0.1), 4, 0.8, seed=seed + k, mat="M_Emit")
        objs += on_side([f] + acc, sd)
    return objs


def frost_wall(b, piece, seed):
    """Ice: big faceted shards, a few translucent over a deep-blue core, snowdrifts at the foot, icicles at the lip."""
    r = random.Random(seed)
    objs = [C.slab("core", -1.99, -1.99, 1.99, 1.99, 0.0, WALL_H, "#1d4a78"),
            C.slab("top", -2.0, -2.0, 2.0, 2.0, WALL_H - 0.01, WALL_H, "#eef6ff")]
    for k, sd in enumerate("NESW"):
        f = G.relief_face(f"ice{sd}", seed + k, frost_base, frost_amp, frost_ice_col, nu=7, nz=7, jitter=0.4)
        acc = [G.mound(f"drift{sd}", -2, 2, 0.55, 0.32, seed + 10 * k, "#f4f9ff", "#d2e3f1", y_face=-2.0 - frost_base(0.0) + 0.1)]
        lip = G.face_point(frost_base, 0, WALL_H - 0.1)[1]
        acc += icicles(b, lip + 0.05, WALL_H - 0.08, -1.8, 1.8, 4 if piece == "wall_a" else 6, seed=seed + k, length=(0.3, 0.9))
        if piece == "wall_b" and sd in "NE":   # ice pillars standing against the face
            for j, u in enumerate((-1.2, 1.25)):
                p = G.face_point(frost_base, u, 0.5, 0.12)
                acc.append(C.crystal(f"pillar{j}", r.uniform(0.26, 0.34), r.uniform(2.6, 3.8), "#c8f0ff", "M_Clear", loc=p[:2] + (0.0,),
                                     rot=(r.uniform(-5, 5), r.uniform(-5, 5), r.uniform(0, 60))))
                acc += crystals(b, p[:2] + (0.0,), 3, 0.7, seed=seed + j)
        if piece == "wall_c" and sd in "SW":   # small frozen fall
            acc += frozen_fall(b, seed + k, 0.45, 1.6)
        objs += on_side([f] + acc, sd)
    return objs


def frozen_fall(b, seed, u0, u1):
    """Translucent rippled ice tongues flowing down the face between u0 and u1 + a white foam heap at the foot."""
    r = random.Random(seed)
    out = []
    n = 4
    for k in range(n):
        u = u0 + (u1 - u0) * (k + 0.5) / n
        pts = []
        for j in range(10):
            z = WALL_H * (1 - j / 9)
            p = G.face_point(frost_base, u + 0.05 * math.sin(j * 1.3 + k), z, 0.1 + 0.03 * k)
            pts.append((p[0], z, p[1]))
        verts, faces = [], []
        w = (u1 - u0) / n * 0.75
        for (x, z, y) in pts:
            verts += [(x - w, y, z), (x + w, y, z)]
        for j in range(len(pts) - 1):
            faces.append((2 * j, 2 * j + 2, 2 * j + 3, 2 * j + 1))
        out.append(G.colored_mesh(f"fall{k}", verts, faces, [G.rgb("#d6f4ff")] * len(faces), ["M_Clear"] * len(faces)))
    out.append(G.blob("foam", G.face_point(frost_base, (u0 + u1) / 2, 0, 0.2)[:2] + (0.05,), (u1 - u0) * 0.55, "#f2f9ff", seed, squash=0.45))
    return out


CRYPT_FACES = {"wall_a": ("loculi", "banner", "loculi", "arch"),
               "wall_b": ("gate", "loculi", "arch", "loculi"),
               "wall_c": ("arch", "gate", "banner", "loculi")}


def crypt_wall(b, piece, seed):
    """Gothic bays: plinth, cornice and pilasters on every face; each face is burial niches, an iron grille,
    a lancet-arch shrine or a banner wall."""
    objs = [C.slab("core", -1.0, -1.0, 1.0, 1.0, 0.0, WALL_H - 0.03, "#0b0910"),
            C.slab("top", -2.0, -2.0, 2.0, 2.0, WALL_H - 0.02, WALL_H, b.stone_dark)]
    for k, (sd, kind) in enumerate(zip("NESW", CRYPT_FACES[piece])):
        objs += on_side(crypt_face(b, kind, seed + 17 * k), sd)
    return objs


def crypt_frame(b):
    st, dk = b.stone, b.stone_dark
    return [C.slab("plinth", -2.0, -2.17, 2.0, -1.98, 0.0, 0.32, dk),
            C.slab("cornice", -2.0, -2.26, 2.0, -1.98, 3.95, 4.2, st),
            C.slab("cornice2", -2.0, -2.16, 2.0, -1.98, 4.2, 4.5, dk),
            C.slab("pil_l", -2.0, -2.2, -1.72, -1.98, 0.32, 3.95, "#8a82a0"),
            C.slab("pil_r", 1.72, -2.2, 2.0, -1.98, 0.32, 3.95, "#8a82a0"),
            C.slab("pil_lc", -2.0, -2.26, -1.66, -1.98, 3.7, 3.95, st),
            C.slab("pil_rc", 1.66, -2.26, 2.0, -1.98, 3.7, 3.95, st)]


def crypt_face(b, kind, seed):
    r = random.Random(seed)
    objs = crypt_frame(b)
    if kind == "loculi":
        objs += loculi(b, seed)
    elif kind == "gate":
        objs.append(wall_face(b, "wall_gated", "S"))
    elif kind == "arch":
        objs.append(wall_face(b, "wall", "S"))
        objs += lancet(b, 0.0, 0.95, 0.32, 2.05, -2.0)
        objs += rune_glyph(b, 0.0, -2.02, 2.75, 0.75)
        shrine = inst("kh", "shrine_candles", b.pal, M=T((0, -2.22, 0.0), (0, 0, 180), 0.62))
        objs.append(shrine)
        for (x, y, z) in candle_tips(shrine, "kh:r0c4"):
            objs += candle_flame(b, x, y, z, 0.6)
    else:  # banner wall
        objs.append(wall_face(b, "wall", "S"))
        objs.append(tattered_banner(b, seed, 0.0))
        cx = r.choice((-1.66, 1.66))
        objs += cobweb(b, (cx, -2.03, 3.92), 0.9, 0 if cx < 0 else -90)
    return objs


def loculi(b, seed):
    """Masonry face with 2 x 3 burial niches recessed 0.55 m, each holding a skull, bones, an urn or a candle."""
    r = random.Random(seed)
    us = [-1.72, -1.5, -0.4, 0.4, 1.5, 1.72]
    zs = [0.32, 0.55, 1.3, 1.6, 2.35, 2.65, 3.4, 3.95]
    holes = {(1, 1), (3, 1), (1, 3), (3, 3), (1, 5), (3, 5)}
    verts, faces, cols = [], [], []
    stone = [G.rgb(c) for c in ("#6f6782", "#7b7390", "#655d76", "#837a98")]
    for i in range(len(us) - 1):
        for j in range(len(zs) - 1):
            if (i, j) in holes:
                continue
            n = len(verts)
            verts += [(us[i], -2.0, zs[j]), (us[i + 1], -2.0, zs[j]), (us[i + 1], -2.0, zs[j + 1]), (us[i], -2.0, zs[j + 1])]
            faces.append((n, n + 1, n + 2, n + 3))
            cols.append(r.choice(stone))
    D = -1.45
    for (i, j) in holes:   # niche box (faces point into the niche)
        u0, u1, z0, z1 = us[i], us[i + 1], zs[j], zs[j + 1]
        n = len(verts)
        verts += [(u0, -2.0, z0), (u1, -2.0, z0), (u1, -2.0, z1), (u0, -2.0, z1), (u0, D, z0), (u1, D, z0), (u1, D, z1), (u0, D, z1)]
        faces += [(n + 4, n + 5, n + 6, n + 7), (n, n + 1, n + 5, n + 4), (n + 3, n + 7, n + 6, n + 2),
                  (n, n + 4, n + 7, n + 3), (n + 1, n + 2, n + 6, n + 5)]   # back, floor, roof, left, right
        cols += [G.rgb("#17121f"), G.rgb("#3a3248"), G.rgb("#221c2c"), G.rgb("#2a2335"), G.rgb("#2a2335")]
    objs = [G.colored_mesh("loculi", verts, faces, cols, ["M_Toon"] * len(faces))]
    for (i, j) in sorted(holes):   # sills + contents
        u0, u1, z0 = us[i], us[i + 1], zs[j]
        cu = (u0 + u1) / 2
        objs.append(C.slab(f"sill{i}{j}", u0 - 0.06, -2.1, u1 + 0.06, -1.98, z0 - 0.08, z0, b.stone))
        what = r.choice(("skull", "skull", "bones", "urn", "candle", "skulls"))
        y = -1.75
        if what == "skull":
            objs.append(inst("kh", lowpoly("kh", "skull", 0.35), b.pal, M=T((cu + r.uniform(-0.2, 0.2), y, z0), (0, 0, 180 + r.uniform(-25, 25)), 0.42)))
        elif what == "skulls":
            for dx in (-0.25, 0.22):
                objs.append(inst("kh", lowpoly("kh", "skull", 0.35), b.pal, M=T((cu + dx, y, z0), (0, 0, 180 + r.uniform(-30, 30)), 0.34)))
        elif what == "bones":
            objs.append(inst("kh", lowpoly("kh", "bone_A", 0.5), b.pal, M=T((cu, y, z0 + 0.06), (0, 0, r.uniform(-15, 15)), 0.85)))
            objs.append(inst("kh", lowpoly("kh", "bone_B", 0.5), b.pal, M=T((cu + 0.1, y + 0.1, z0 + 0.12), (0, 0, r.uniform(20, 50)), 0.8)))
        elif what == "urn":
            objs.append(inst("qd", "modular_dungeon_1/Vase", b.pal, M=T((cu, y, z0), (0, 0, 0), 1.25), pre=T((0, -1.085, 0))))
        else:
            objs.append(inst("kh", "candle_melted", b.pal, M=T((cu, y, z0), (0, 0, r.uniform(0, 90)), 0.5)))
            objs += candle_flame(b, cu, y, z0 + 0.3, 0.7)
    return objs


def lancet(b, cu, w, z0, zs, y, depth=0.16, band=0.18):
    """Pointed (equilateral) arch frame on the plane y with a dark recess inside."""
    def outline(ww, n=7):
        left = [(cu - ww, z0)] + [(cu + ww - 2 * ww * math.cos(math.radians(60 * k / n)), zs + 2 * ww * math.sin(math.radians(60 * k / n)))
                                  for k in range(n + 1)]
        right = [(2 * cu - x, z) for (x, z) in reversed(left[:-1])]
        return left + right
    out_o = outline(w)
    out_i = outline(w - band)
    verts, faces, cols = [], [], []
    for (x, z), (xi, zi) in zip(out_o, out_i):
        verts += [(x, y - depth, z), (xi, y - depth, zi), (xi, y - 0.01, zi)]
    for k in range(len(out_o) - 1):
        a, c = 3 * k, 3 * k + 3
        faces += [(a, a + 1, c + 1, c), (a + 1, a + 2, c + 2, c + 1)]   # front band (faces -Y), inner reveal
        cols += [G.rgb("#9a92ae"), G.rgb("#4a4258")]
    o = G.colored_mesh("lancet", verts, faces, cols, ["M_Toon"] * len(faces))
    inner = [(xi, y - 0.012, zi) for (xi, zi) in out_i]
    rec = G.colored_mesh("recess", inner, [tuple(range(len(inner)))[::-1]], [G.rgb("#3a3048")], ["M_Toon"])
    return [o, rec]


def tattered_banner(b, seed, u):
    """KayKit banner recoloured, its bottom hem torn into uneven tongues."""
    o = inst("kd", "banner_white", b.pal, M=T((u, -1.5, 0.1)), rules={"kd:r3c0": ("tint", b.banner, "M_Toon")})
    r = random.Random(seed)
    me = o.data
    zmin = min(v.co.z for v in me.vertices)
    for v in me.vertices:
        if v.co.z < zmin + 0.45:
            v.co.z += r.uniform(0.0, 0.5) * (1 - (v.co.z - zmin) / 0.45)
    return o


FLOWER_TINTS = ({"qn:Flowers": ("grad", ("#b8325e", "#ffd6e6"), "M_Toon")},
                {"qn:Flowers": ("grad", ("#d89a18", "#fff4a8"), "M_Toon")},
                {"qn:Flowers": ("grad", ("#7a7ad8", "#f0f0ff"), "M_Toon")})
LEAVES = ("#3f8a34", "#4c9a3a", "#357a2e", "#5aa842")


def flowers(b, pts, seed, scale=0.8):
    r = random.Random(seed)
    return [inst("qn", r.choice(("Flower_3_Clump", "Flower_4_Clump")), b.pal, M=T(p, (0, 0, r.uniform(0, 360)), scale * r.uniform(0.85, 1.15)),
                 rules=r.choice(FLOWER_TINTS)) for p in pts]


def verdant_wall(b, piece, seed):
    """Ruins under open sky, three silhouettes: a living wall of trees and dense foliage (a, Etrian-style forest
    maze), a low broken masonry wall crowned by turf and a tree (b), a colonnade fragment with broken masonry and
    a pine (c)."""
    r = random.Random(seed)
    moss = {"kd:r0c0": ("tint", "#4f7a3c", "M_Toon"), "kd:r0c1": ("tint", "#a3a890", "M_Toon")}
    objs = []
    if piece == "wall_a":
        objs.append(C.slab("core", -1.9, -1.9, 1.9, 1.9, 0.0, 3.6, "#1f3d1c"))
        for k, (x, y) in enumerate([(-1.45, -1.4), (1.35, -1.5), (1.4, 1.35), (-1.5, 1.45), (0.1, 0.05)]):
            objs.append(C.prism(f"trunk{k}", r.uniform(0.2, 0.3), r.uniform(2.6, 3.6), 6, r.choice(("#6a4a32", "#5a3e2a", "#7a5838")),
                                M=T((x, y, 0), (r.uniform(-6, 6), r.uniform(-6, 6), r.uniform(0, 60))), r_top=0.14))
            objs += G.roots(seed + k, (x, y, 0), 3, length=(0.5, 0.9))
        # leaf masses: low ring hugging the four faces, high crowns above; protrude at most ~0.25 m past the faces
        for sd in "NESW":
            ring = []
            for j, u in enumerate((-1.3, 0.0, 1.3)):
                rad = r.uniform(0.85, 1.05)
                ring.append(G.blob(f"hedge{sd}{j}", (u + r.uniform(-0.15, 0.15), -2.0 + rad * 0.78, r.uniform(1.0, 1.5)), rad,
                                   r.choice(LEAVES), seed + 31 * j + ord(sd), squash=1.0))
                ring.append(G.blob(f"hedgeup{sd}{j}", (u + r.uniform(-0.3, 0.3), -2.0 + rad * 0.85, r.uniform(2.5, 3.1)), rad * 0.95,
                                   r.choice(LEAVES), seed + 57 * j + ord(sd), squash=1.0))
            objs += on_side(ring, sd)
        for k, (x, y) in enumerate([(-0.8, -0.7), (0.9, 0.8), (0.7, -0.9), (-0.9, 0.8)]):
            objs.append(G.blob(f"crown{k}", (x, y, r.uniform(3.8, 4.6)), r.uniform(1.3, 1.6), r.choice(LEAVES), seed + 90 + k, squash=0.8))
        return objs
    if piece == "wall_b":
        h = 2.8
        objs += [wall_face(b, "wall", s, rules=moss, zscale=h / WALL_H) for s in "NESW"]
    else:
        h = 3.6
        objs += [wall_face(b, ("wall_broken" if s == "N" else "wall"), s, rules=moss, zscale=h / WALL_H) for s in "NESW"]
    objs.append(C.slab("core", -0.98, -0.98, 0.98, 0.98, 0.0, h - 0.03, "#1e3a1c"))
    objs.append(C.slab("turf", -2.04, -2.04, 2.04, 2.04, h - 0.02, h + 0.08, "#4f8a36"))
    objs.append(G.blob("turf_hump", (r.uniform(-0.5, 0.5), r.uniform(-0.5, 0.5), h), 1.7, "#5a9a3c", seed, squash=0.25))
    for s in "NESW":   # turf spilling over the edge, ivy, weeds and shrubs at the foot
        g = [G.blob(f"lip{s}{j}", (u, -1.95, h + 0.05), 0.42, r.choice(LEAVES), seed + j + ord(s), squash=0.6) for j, u in enumerate((-1.2, 0.2, 1.4))]
        g += grass(b, [(r.uniform(-1.6, 1.6), -2.1, 0)], 0.8, seed=r.randint(0, 99), small=True)
        g += vines(b, r.randint(0, 9999), n=2 if s in "NS" else 3, lmin=0.7, lmax=h - 0.5, top=h + 0.05)
        if r.random() < 0.6:
            g.append(G.blob(f"shrub{s}", (r.choice((-1.3, 1.3)), -2.15, 0.25), 0.5, r.choice(LEAVES), seed + ord(s) * 3, squash=0.8))
        objs += on_side(g, s)
    if piece == "wall_b":
        objs += G.round_tree(seed, (r.uniform(-0.4, 0.4), r.uniform(-0.4, 0.4), h), height=4.6, crown=1.55)
        for k, (x, y) in enumerate([(-1.6, -1.5), (1.6, 1.5)]):   # rubble on the broken crown
            objs.append(inst("qd", "modular_dungeon_pack/Rock2", b.pal, M=T((x, y, h), (0, 0, r.uniform(0, 360)), 0.9),
                             rules={"qd:Rock": ("tint", b.stone, "M_Toon")}))
    else:
        objs.append(inst("qd", "modular_dungeon_pack/Column", b.pal, M=T((-1.5, -1.5, 0), (0, 0, 0), (0.62, 0.62, 1.0)),
                         rules={"qd:Rock": ("tint", "#b5b8a2", "M_Toon")}))
        objs.append(inst("kh", "tree_pine_yellow_medium", b.pal, M=T((0.5, 0.6, h), (0, 0, r.uniform(0, 360)), 0.85),
                         rules={"kh:r1c1": ("grad", ("#1f5a2a", "#6fbf4a"), "M_Toon"), "kh:r1c7": ("tint", "#6a4a32", "M_Toon")}))
    return objs


# ---------------------------------------------------------------- doors / gates / stairs

def build_door(b, piece):
    frame = [inst("kd", "wall_doorway", b.pal, sub="wall_doorway", M=T(scale=(1, 1, WALL_SZ)))]
    leaf_rules = None
    if b.is_("frost_grotto"):
        frame += icicles(b, -0.52, 4.0, -1.8, 1.8, 6, seed=3, length=(0.25, 0.6))
        frame += icicles(b, 0.52, 4.0, -1.8, 1.8, 6, seed=4, length=(0.25, 0.6))
        frame += crystals(b, (-1.65, -0.62, 0), 4, 0.8, seed=5) + crystals(b, (1.6, 0.62, 0), 3, 0.7, seed=6)
    elif b.is_("ember_caverns"):
        frame.append(C.slab("sill", -1.0, -0.5, 1.0, 0.5, 0.0, 0.025, b.glow, "M_Emit"))
    elif b.is_("haunted_crypt"):
        for y, r in ((-0.55, 0), (0.55, 180)):
            frame.append(inst("kh", lowpoly("kh", "skull", 0.35), b.pal, M=T((0, y, 3.55), (0, 0, r), 0.42)))
    else:
        frame += grass(b, [(-1.6, -0.62, 0), (1.5, 0.6, 0), (1.7, -0.6, 0)], 0.8, seed=8)
    body = finish(piece, frame)
    hinge = Vector((-0.82, 0, 0))
    leaf = inst("kd", "wall_doorway", b.pal, sub="wall_doorway_door", M=T(scale=(1, 1, WALL_SZ)), rules=leaf_rules)
    door = finish("Door", [leaf], origin=hinge)
    out = [body, door]
    if piece == "door_locked":
        parts = []
        for y in (-1, 1):
            parts += padlock(b, Vector((0.3, 0.33 * y, 1.45)), y)
        lock = finish("Lock", parts, origin=(0.3, 0, 1.45))
        lock.parent = door
        lock.matrix_parent_inverse = door.matrix_world.inverted()
        out.append(lock)
    return out


def padlock(b, at, side):
    """Small padlock on one face of the door (side -1 = -Y face)."""
    x, y, z = at
    d = 0.05 * side
    body = C.slab("lockbody", x - 0.17, y - 0.06, x + 0.17, y + 0.06, z - 0.2, z + 0.1, b.gold)
    s1 = C.slab("sh1", x - 0.13, y - 0.03, x - 0.08, y + 0.03, z + 0.1, z + 0.3, b.iron)
    s2 = C.slab("sh2", x + 0.08, y - 0.03, x + 0.13, y + 0.03, z + 0.1, z + 0.3, b.iron)
    s3 = C.slab("sh3", x - 0.13, y - 0.03, x + 0.13, y + 0.03, z + 0.28, z + 0.34, b.iron)
    gem = C.crystal("gem", 0.05, 0.08, b.accent, "M_Emit", loc=(x, y + d + 0.02 * side, z - 0.05), rot=(90 * side, 0, 0))
    return [body, s1, s2, s3, gem]


def build_stairs(b, piece):
    objs = []
    ceil = None
    if piece == "stairs_up":
        objs.append(inst("kd", "stairs_narrow", b.pal, M=T((0, 2, 0))))
        lamp_z = 0.0
    else:
        # own 4x4 floor replaced by the stairwell: top step at y=-2 (z=0), down to z=-4 at y=+2
        objs.append(inst("kd", "stairs_narrow", b.pal, M=T((0, -2, -4), (0, 0, 180))))
        objs.append(C.slab("back", -2.0, 1.9, 2.0, 2.0, -4.0, 0.0, b.stone_dark))
        objs.append(C.slab("void", -2.0, -2.0, 2.0, 2.0, -4.05, -4.0, "#05030a"))
        objs.append(inst("kd", "barrier", b.pal, M=T((0, 1.85, 0), (0, 0, 0), (0.98, 0.6, 0.8))))
        lamp_z = 0.0
        ceil = build_ceiling(b, "floor_a")   # this cell gets no floor piece, so it carries its own ceiling
    # biome dressing on the landing corners
    if b.is_("frost_grotto"):
        objs += crystals(b, (-1.7, -1.75, lamp_z), 4, 0.8, seed=21) + crystals(b, (1.7, -1.75, lamp_z), 3, 0.7, seed=22)
    elif b.is_("ember_caverns"):
        objs += crystals(b, (-1.75, -1.8, lamp_z), 3, 0.6, seed=23, mat="M_Emit") + crystals(b, (1.75, -1.8, lamp_z), 3, 0.55, seed=24, mat="M_Emit")
    elif b.is_("haunted_crypt"):
        objs.append(inst("kh", "candle_triple", b.pal, M=T((-1.7, -1.75, 0), (0, 0, 30), 0.7)))
        objs += candle_flame(b, -1.7, -1.78, 0.56, 0.9)
        objs.append(inst("kh", "candle_melted", b.pal, M=T((1.72, -1.75, 0), (0, 0, 0), 0.8)))
        objs += candle_flame(b, 1.72, -1.75, 0.5, 0.9)
    else:
        objs += grass(b, [(-1.75, -1.8, 0), (1.7, -1.8, 0)], 0.8, seed=25)
    out = [finish(piece, objs)]
    if piece == "stairs_down" and ceil is not None:
        out.append(ceil)
    return out


def build_boss_gate(b):
    objs = [inst("kh", "arch", b.pal, M=T((0, 0, 0), (0, 0, 0), (0.948, 1.2, 1.0)))]
    objs.append(inst("kd", "sword_shield_gold", b.pal, M=T((0, -0.5, 4.0), (0, 0, 0), 0.7),
                     rules={"kd:r2c7": ("tint", b.gold, "M_Toon")}))
    empties = []
    for sx in (-1, 1):
        x = 1.65 * sx
        if b.is_("haunted_crypt"):
            objs.append(inst("kh", lowpoly("kh", "skull_candle", 0.45), b.pal, M=T((x, -0.75, 0), (0, 0, 180 + 20 * sx), 0.7)))
            objs += candle_flame(b, x, -0.68, 0.86, 1.0)
            light_z = 1.0
        else:
            objs.append(inst("qd", "modular_dungeon_1/Woodfire", b.pal, M=T((x, -0.85, 0), (0, 0, 40 * sx), 1.1)))
            light_z = 0.9
            if b.is_("frost_grotto"):
                objs += crystals(b, (x, 0.0, 4.35), 4, 0.9, seed=31 + sx)
            elif b.is_("verdant_ruins"):
                objs += grass(b, [(x, 0.0, 0), (x + 0.4 * sx, 0.45, 0)], 0.9, seed=33 + sx)
            else:
                objs += crystals(b, (x, 0.0, 4.35), 3, 0.7, seed=35 + sx, mat="M_Emit")
        empties.append(("LightAnchor_gate_" + ("L" if sx < 0 else "R"), (x, -0.85, light_z)))
    body = finish("boss_gate", objs)
    out = [body]
    for n, p in empties:
        out.append(empty(n, p))
    out.append(empty("Spot_boss", (0, 0, 0)))
    return out


# ---------------------------------------------------------------- interactables

def build_chest(b):
    s = 0.72
    metal = {"ember_caverns": "#3a2a26", "frost_grotto": "#d6e6f5", "haunted_crypt": "#b9b0cc", "verdant_ruins": "#c9a85a"}[b.ts]
    rules = {"kd:r0c1": ("tint", metal, "M_Toon"), "kd:r2c7": ("tint", b.gold, "M_Toon"),
             "kd:r0c4": ("tint", {"ember_caverns": "#8a2c22", "frost_grotto": "#5a6f96",
                                  "haunted_crypt": "#5d3a72", "verdant_ruins": "#8a5a32"}[b.ts], "M_Toon")}
    body = inst("kd", "chest_gold", b.pal, sub="chest_gold", M=T(scale=s), rules=rules)
    extras = []
    if b.is_("frost_grotto"):
        extras += crystals(b, (0.72, 0.35, 0), 3, 0.6, seed=41)
    elif b.is_("verdant_ruins"):
        extras += grass(b, [(-0.7, 0.3, 0), (0.75, -0.2, 0)], 0.6, seed=42)
    elif b.is_("haunted_crypt"):
        extras.append(inst("kh", "candle_melted", b.pal, M=T((0.78, 0.25, 0), (0, 0, 0), 0.6)))
        extras += candle_flame(b, 0.78, 0.25, 0.38, 0.8)
    elif b.is_("ember_caverns"):
        extras += crystals(b, (-0.75, 0.3, 0), 3, 0.45, seed=43, mat="M_Emit")
    chest = finish("chest", [body] + extras)
    hinge = C.origin_of("kd", "chest_gold", "chest_gold_lid") * s
    lid = finish("Lid", [inst("kd", "chest_gold", b.pal, sub="chest_gold_lid", M=T(scale=s), rules=rules)], origin=hinge)
    return [chest, lid]


def build_lore_stone(b):
    objs = [inst("kh", "gravestone", b.pal, M=T((0, 0, 0), (0, 0, 0), (0.9, 1.2, 1.35)),
                 rules={"kh:r0c3": ("tint", b.grave, "M_Toon")})]
    objs.append(inst("kd", "floor_tile_small", b.pal, M=T((0, 0, 0.0), (0, 0, 0), (0.8, 0.5, 1.0))))
    objs += rune_glyph(b, 0.0, -0.26, 1.15, 0.85)
    if b.is_("frost_grotto"):
        objs += crystals(b, (0.75, -0.25, 0), 4, 0.8, seed=51)
    elif b.is_("ember_caverns"):
        objs += crystals(b, (-0.7, -0.2, 0), 3, 0.55, seed=52, mat="M_Emit")
    elif b.is_("haunted_crypt"):
        objs.append(inst("kh", "candle_triple", b.pal, M=T((-0.62, -0.35, 0), (0, 0, 20), 0.6)))
        objs += candle_flame(b, -0.62, -0.38, 0.48, 0.8)
        objs.append(inst("kh", lowpoly("kh", "skull", 0.35), b.pal, M=T((0.6, -0.4, 0), (0, 0, 200), 0.32)))
    else:
        objs += grass(b, [(-0.65, -0.3, 0), (0.7, -0.25, 0), (0.1, 0.35, 0)], 0.75, seed=53)
    return [finish("lore_stone", objs)]


def build_trap(b):
    plate = inst("kd", "floor_tile_big_spikes", b.pal, sub="floor_tile_big_spikes", M=T((0, 0, -0.06), (0, 0, 0), (0.7, 0.7, 0.9)))
    rim = C.polyline_strip("warn", [(-1.4, -1.4), (1.4, -1.4), (1.4, 1.4), (-1.4, 1.4), (-1.4, -1.4)], 0.06, 0.035, b.accent, "M_Emit")
    trap = finish("trap", [plate, rim])
    sp = inst("kd", "floor_tile_big_spikes", b.pal, sub="spikes", M=T((0, 0, -0.5), (0, 0, 0), (0.7, 0.7, 0.27)))
    spikes = finish("Spikes", [sp], origin=(0, 0, -0.5))
    return [trap, spikes]


def build_spring(b):
    stone = b.stone
    objs = [C.prism("basin_out", 1.38, 0.42, 8, stone, r_top=1.32),
            C.disc("basin_rim", 1.32, 0.426, 8, b.stone_dark, "M_Toon", r_in=1.12)]
    water = {"ember_caverns": ("#ffb050", "M_Emit"), "frost_grotto": ("#9fe8ff", "M_Clear"),
             "haunted_crypt": ("#7affd0", "M_Emit"), "verdant_ruins": ("#7dffc8", "M_Emit")}[b.ts]
    objs.append(C.disc("water", 1.14, 0.43, 16, water[0], water[1]))
    objs.append(inst("qd", "modular_dungeon_1/Pedestal2", b.pal, M=T((0, 0, 0.3), (0, 0, 22.5), (0.42, 0.42, 0.45))))
    objs += crystals(b, (0, 0, 1.33), 4, 0.75, spread=0.12, seed=61, mat="M_Emit" if b.crystal_mat == "M_Emit" else "M_Clear")
    if b.is_("verdant_ruins"):
        objs += grass(b, [(1.3, 0.6, 0), (-1.2, -0.8, 0), (0.4, -1.35, 0)], 0.8, seed=62)
    elif b.is_("haunted_crypt"):
        for a in (45, 135, 225, 315):
            x, y = 1.22 * math.cos(math.radians(a)), 1.22 * math.sin(math.radians(a))
            objs.append(inst("kh", "candle_melted", b.pal, M=T((x, y, 0.42), (0, 0, a), 0.45)))
            objs += candle_flame(b, x, y, 0.68, 0.7)
    out = [finish("spring", objs), empty("LightAnchor_spring", (0, 0, 1.2))]
    return out


def build_warp(b):
    objs = [C.prism("pad", 1.55, 0.08, 16, b.stone_dark, r_top=1.5),
            C.disc("ring_o", 1.42, 0.085, 32, b.glow, "M_Emit", r_in=1.3),
            C.disc("ring_i", 0.95, 0.086, 32, b.glow, "M_Emit", r_in=0.86)]
    for k in range(6):   # spokes between the rings
        a = math.radians(30 + 60 * k)
        objs.append(C.polyline_strip(f"sp{k}", [(math.cos(a) * 0.95, math.sin(a) * 0.95), (math.cos(a) * 1.3, math.sin(a) * 1.3)],
                                     0.06, 0.086, b.glow_hi, "M_Emit"))
    star = []
    for k in range(7):
        a = math.radians(90 + k * 360 / 6 * 2)
        star.append((math.cos(a) * 0.86, math.sin(a) * 0.86))
    objs.append(C.polyline_strip("star", star, 0.05, 0.087, b.glow, "M_Emit"))
    for k in range(4):
        a = math.radians(45 + 90 * k)
        p = (math.cos(a) * 1.55, math.sin(a) * 1.55, 0)
        if b.is_("haunted_crypt"):
            objs.append(inst("kh", "candle_triple", b.pal, M=T(p, (0, 0, 90 * k), 0.6)))
            objs += candle_flame(b, p[0], p[1] - 0.03, 0.48, 0.8)
        else:
            objs += crystals(b, p, 3, 0.65, spread=0.15, seed=70 + k, mat="M_Emit" if b.crystal_mat == "M_Emit" else "M_Clear")
    return [finish("warp", objs), empty("LightAnchor_warp", (0, 0, 0.8)), empty("Spot_warp", (0, 0, 0))]


TORCH_S = 1.45


def build_torch(b):
    """Wall torch for DungeonWorld: spawned 1.7 m from the cell centre toward the wall, rotated so local -Y faces
    the room -> the bracket plate sits on the wall face at local y = +0.30."""
    M = T((0, 0.30, 1.75), (0, 0, 0), TORCH_S)
    body = inst("kd", "torch_mounted", b.pal, M=M, rules={"kd:r0c1": ("tint", b.metal if not b.is_("ember_caverns") else "#3d2b26", "M_Toon")})
    # flame = the flame faces of KayKit torch_lit, set into the mounted torch's basket and enlarged so it reads
    # from the corridor; a smaller bright core sits inside it
    seat = M @ T((0, -0.215, -0.01), (18, 0, 0))
    objs = [body]
    for k, (sc, col) in enumerate(((1.75, b.flame), (1.05, b.glow_hi))):
        fl = inst("kd", "torch_lit", b.pal, M=seat @ T((0, -0.02 * k, 0.31)) @ T(scale=sc) @ T((0, 0, -0.31)),
                  rules={"kd:r2c7": ("tint", col, "M_Emit")})
        _keep_material(fl, "M_Emit")
        objs.append(fl)
    if b.is_("frost_grotto"):
        objs += icicles(b, -0.02, 1.75 - 0.2, -0.2, 0.2, 3, seed=81, length=(0.15, 0.35))
    return [finish("torch", objs), empty("LightAnchor", (0, 0.30 - 0.38 * TORCH_S, 1.75 + 0.8 * TORCH_S))]


def _keep_material(o, matname):
    import bmesh
    me = o.data
    idx = [i for i, m in enumerate(me.materials) if m and m.name == matname]
    bm = bmesh.new()
    bm.from_mesh(me)
    bmesh.ops.delete(bm, geom=[f for f in bm.faces if f.material_index not in idx], context="FACES")
    bm.to_mesh(me)
    bm.free()


def build_foe_marker(b):
    objs = [inst("kh", "post_skull", b.pal, M=T((0, 0.4, 0), (0, 0, 0), 0.75))]
    objs.append(C.disc("ring", 1.15, 0.02, 24, b.accent, "M_Emit", r_in=1.02))
    return [finish("foe_marker", objs), empty("Spot_foe", (0, 0, 0))]


# ---------------------------------------------------------------- decor & overlays
#
# DungeonWorld places decor_N against a wall beside the walking line: origin 1.45 m from the cell centre toward
# the wall and 1.0 m sideways, local -Y facing the room. Keep each decor inside a ~0.5 m radius footprint.
# overlay_N is spawned on the wall cell itself, rotated so its dressed -Y face (plane y = -2) faces the open cell.

def candle_tips(o, key, cell=0.07):
    """Top point of every candle (faces of colour family `key`) of an inst() object, for flames."""
    me = o.data
    keys = [a.value for a in me.attributes["key"].data]
    tops = {}
    for p in me.polygons:
        if C._KEYS[keys[p.index]] != key:
            continue
        for vi in p.vertices:
            v = me.vertices[vi].co
            k = (round(v.x / cell), round(v.y / cell))
            if k not in tops or v.z > tops[k][2]:
                tops[k] = (v.x, v.y, v.z)
    pts = sorted(tops.values(), key=lambda q: -q[2])
    out = []
    for q in pts:   # one flame per candle: drop lower points of the same candle
        if all((q[0] - o2[0]) ** 2 + (q[1] - o2[1]) ** 2 > (cell * 1.6) ** 2 for o2 in out):
            out.append(q)
    return out


def flames_on(b, o, key, s=0.7, zoff=-0.02):
    out = []
    for (x, y, z) in candle_tips(o, key):
        out += candle_flame(b, x, y, z + zoff, s)
    return out


def build_decor(b, i):
    ts = b.ts
    o = []
    r = random.Random(ts + str(i))
    if ts == "ember_caverns":
        if i == 1:     # obsidian spires
            for k in range(5):
                a = r.uniform(0, 360)
                d = 0 if k == 0 else r.uniform(0.15, 0.35)
                o.append(C.crystal(f"obs{k}", r.uniform(0.1, 0.18), r.uniform(0.6, 1.7) * (1.0 if k == 0 else 0.7),
                                   r.choice(("#2b2233", "#231b2a", "#3b2f48")), "M_Toon",
                                   loc=(math.cos(math.radians(a)) * d, math.sin(math.radians(a)) * d, 0),
                                   rot=(r.uniform(-14, 14), r.uniform(-14, 14), r.uniform(0, 60))))
            o.append(C.disc("glow", 0.3, 0.01, 7, b.glow, "M_Emit"))
        elif i == 2:   # lava vent: rock cone with a glowing throat
            o.append(C.prism("cone", 0.55, 0.5, 8, "#4a312b", r_top=0.26))
            o.append(C.prism("rim", 0.27, 0.06, 8, "#2f201d", loc=(0, 0, 0.5), r_top=0.22))
            o.append(C.disc("throat", 0.22, 0.53, 8, "#ffb04a", "M_Emit"))
            o += C.flame("vent", 0.55, 0.16, b.flame, b.glow_hi, loc=(0, 0, 0.5))
        elif i == 3:   # rock pile with ember crystals
            o.append(inst("qd", "modular_dungeon_pack/Rock2", b.pal, scale=1.0))
            o.append(inst("qd", "modular_dungeon_pack/Rock4", b.pal, loc=(0.35, 0.25, 0), scale=0.8, rot=(0, 0, 70)))
            o.append(inst("qd", "modular_dungeon_pack/Rock5", b.pal, loc=(-0.35, -0.2, 0), scale=1.0, rot=(0, 0, 20)))
            o += crystals(b, (-0.1, 0.3, 0.2), 4, 0.6, seed=91, mat="M_Emit")
        elif i == 4:   # stalagmites
            for k, (x, y, h, rr) in enumerate([(0, 0.1, 1.6, 0.3), (0.35, -0.15, 0.9, 0.22), (-0.3, -0.2, 0.7, 0.2), (0.05, 0.4, 0.5, 0.16)]):
                o.append(C.prism(f"stg{k}", rr, h, 6, r.choice(("#4c312b", "#5e3e35")), loc=(x, y, -0.02), r_top=0.0,
                                 rot=(r.uniform(-5, 5), r.uniform(-5, 5), r.uniform(0, 60))))
        elif i == 5:   # scorched remains
            o.append(inst("qd", "modular_dungeon_pack/Bones2", b.pal, scale=0.55, rot=(0, 0, 30)))
            o.append(inst("kh", lowpoly("kh", "skull", 0.35), b.pal, loc=(0.25, -0.2, 0), scale=0.38, rot=(0, 0, 160)))
            o.append(inst("qd", "modular_dungeon_pack/Rock5", b.pal, loc=(-0.3, 0.3, 0), scale=1.0))
        else:          # big ember crystal growth
            o += crystals(b, (0, 0, 0), 6, 1.4, spread=0.35, seed=96, mat="M_Emit")
            o.append(inst("qd", "modular_dungeon_pack/Rock4", b.pal, loc=(0.1, -0.1, -0.05), scale=0.9))
    elif ts == "frost_grotto":
        if i == 1:     # snow heap with crystals
            o.append(G.blob("snow", (0, 0, 0), 0.55, "#f2f8ff", 1, squash=0.5))
            o += crystals(b, (0.15, 0.1, 0.15), 4, 0.8, seed=92)
        elif i == 2:   # translucent ice stalagmites
            for k, (x, y, h) in enumerate([(0, 0.05, 1.5), (0.3, -0.2, 0.9), (-0.28, -0.15, 0.75), (0.1, 0.35, 0.6)]):
                o.append(C.prism(f"istg{k}", 0.13 + 0.08 * h, h, 6, "#c8f0ff", "M_Clear", loc=(x, y, 0), r_top=0.0,
                                 rot=(r.uniform(-6, 6), r.uniform(-6, 6), r.uniform(0, 60))))
            o.append(G.blob("snow", (0, 0, 0), 0.5, "#eef6ff", 2, squash=0.3))
        elif i == 3:   # frozen supply crate half buried in snow
            o.append(inst("kd", "box_small", b.pal, scale=0.7, rot=(0, 0, 15), rules={"kd:r0c4": ("tint", "#8a6a52", "M_Toon")}))
            o.append(G.blob("cap", (0.0, 0.0, 0.62), 0.45, "#f4f9ff", 3, squash=0.3))
            o.append(G.blob("drift", (0.15, -0.1, 0.0), 0.6, "#eef6ff", 7, squash=0.45))
            o += crystals(b, (-0.4, 0.25, 0), 3, 0.5, seed=93)
        elif i == 4:   # ice pillar
            o.append(C.crystal("pillar", 0.26, 2.2, "#c8f0ff", "M_Clear", rot=(0, 0, 15)))
            o += crystals(b, (0.25, -0.2, 0), 3, 0.6, seed=94)
            o.append(G.blob("snow", (0, 0, 0), 0.5, "#eef6ff", 4, squash=0.3))
        elif i == 5:   # a lost explorer's bones frozen in ice
            o.append(inst("qd", "modular_dungeon_pack/Bones2", b.pal, scale=0.5, rot=(0, 0, 20)))
            o.append(C.crystal("block", 0.48, 0.65, "#c8f0ff", "M_Clear", rot=(0, 0, 10), n=6))
        else:          # icy boulder under snow
            o.append(inst("qd", "modular_dungeon_pack/Rock2", b.pal, scale=1.1, rules={"qd:Rock": ("tint", "#7f97ad", "M_Toon")}))
            o.append(G.blob("cap", (0.05, 0.0, 0.32), 0.48, "#f4f9ff", 6, squash=0.35))
            o += crystals(b, (-0.35, 0.3, 0), 3, 0.55, seed=96)
    elif ts == "haunted_crypt":
        if i == 1:     # tall candelabrum
            cb = inst("qd", lowpoly("qd", "modular_dungeon_pack/Candelabrum_tall", 0.55), b.pal, scale=1.0, rules={"qd:Gold": ("tint", "#8a7650", "M_Toon")})
            o.append(cb)
            o += flames_on(b, cb, "qd:Candle", 0.8)
        elif i == 2:   # coffin along the wall, lid ajar
            o.append(inst("kh", "coffin", b.pal, scale=0.62, rot=(0, 0, 90)))
            o.append(inst("kh", "candle_thin", b.pal, loc=(0.55, 0.3, 0), scale=0.55))
            o += candle_flame(b, 0.55, 0.3, 0.52, 0.6)
        elif i == 3:   # skull pile with a skull candle
            sc = inst("kh", lowpoly("kh", "skull_candle", 0.45), b.pal, scale=0.5, rot=(0, 0, 180))
            o.append(sc)
            o += flames_on(b, sc, "kh:r0c4", 0.8)
            for k, (x, y, rot) in enumerate([(0.32, 0.05, 150), (-0.3, 0.1, 210), (0.05, 0.3, 190)]):
                o.append(inst("kh", lowpoly("kh", "skull", 0.35), b.pal, loc=(x, y, 0), scale=0.34, rot=(0, 0, rot)))
        elif i == 4:   # broken grave with melted candles
            o.append(inst("kh", "grave_A_destroyed", b.pal, scale=0.55, rot=(0, 0, 180)))
            cm = inst("kh", "candle_melted", b.pal, loc=(0.42, -0.25, 0), scale=0.55)
            o.append(cm)
            o += flames_on(b, cm, "kh:r0c4", 0.65)
        elif i == 5:   # ossuary heap
            o.append(inst("qd", "modular_dungeon_pack/Bones2", b.pal, scale=0.6))
            o.append(inst("kh", lowpoly("kh", "ribcage", 0.25), b.pal, loc=(0.3, 0.25, 0.25), scale=0.6, rot=(0, 0, 40)))
            o.append(inst("kh", lowpoly("kh", "skull", 0.35), b.pal, loc=(-0.25, -0.1, 0.1), scale=0.36, rot=(0, 0, 200)))
        else:          # funerary urns
            for k, (x, y, s) in enumerate([(0, 0.1, 1.6), (0.32, -0.12, 1.2), (-0.3, -0.1, 1.0)]):
                o.append(inst("qd", "modular_dungeon_1/Vase", b.pal, M=T((x, y, 0), (0, 0, k * 40), s), pre=T((0, -1.085, 0)),
                              rules={"qd:Ceramic": ("tint", ("#5d4a6e", "#6e5a52", "#4a3f5c")[k], "M_Toon")}))
    else:
        if i == 1:     # broken column stump
            o.append(inst("qd", "modular_dungeon_pack/Column_Broken2", b.pal, scale=0.55, rules={"qd:Rock": ("tint", "#b5b8a2", "M_Toon")}))
            o += grass(b, [(0.4, -0.3, 0), (-0.35, -0.35, 0)], 0.8, seed=97, small=True)
        elif i == 2:   # flowering bush
            o.append(G.blob("bush", (0, 0, 0.35), 0.55, "#4c8f34", 21))
            o.append(G.blob("bush2", (0.3, -0.15, 0.25), 0.38, "#5aa23e", 22))
            o += flowers(b, [(-0.3, -0.35, 0), (0.35, -0.4, 0), (0.0, -0.5, 0)], 21, 0.8)
        elif i == 3:   # mossy boulder
            o.append(inst("qd", "modular_dungeon_pack/Rock1", b.pal, scale=1.0, rules={"qd:Rock": ("tint", "#8a8f78", "M_Toon")}))
            o.append(G.blob("moss", (0.0, 0.05, 0.42), 0.36, "#5a9a3c", 23, squash=0.35))
            o += flowers(b, [(0.4, -0.3, 0), (-0.35, -0.35, 0)], 23, 0.8)
        elif i == 4:   # fallen column drum
            o.append(inst("qd", "modular_dungeon_pack/Column", b.pal, M=T((0, 0, 0.32), (0, 90, 15), (0.32, 0.32, 0.22)),
                          pre=T((0, 0, -2.45)), rules={"qd:Rock": ("tint", "#b5b8a2", "M_Toon")}))
            o += grass(b, [(0.35, -0.4, 0), (-0.4, -0.35, 0)], 0.8, seed=100, small=True)
        elif i == 5:   # old stump with roots and mushrooms
            o.append(C.prism("stump", 0.32, 0.5, 7, "#6a4a32", r_top=0.28))
            o.append(C.disc("rings", 0.27, 0.505, 7, "#b08a5a", "M_Toon"))
            o += G.roots(25, (0, 0, 0), 4, length=(0.5, 0.7))
            for k, (x, y) in enumerate([(0.3, -0.3), (-0.25, -0.35)]):
                o.append(C.prism(f"stem{k}", 0.04, 0.16, 5, "#efe6d2", loc=(x, y, 0)))
                o.append(C.prism(f"cap{k}", 0.12, 0.08, 6, "#d8452f", loc=(x, y, 0.15), r_top=0.0))
        else:          # flower patch
            o += flowers(b, [(0, 0, 0), (0.35, 0.2, 0), (-0.32, 0.18, 0), (0.1, -0.35, 0), (-0.25, -0.3, 0), (0.4, -0.25, 0)], 26, 0.85)
            o += grass(b, [(0.0, 0.4, 0), (0.4, -0.15, 0)], 0.7, seed=102, small=True)
    return [finish(f"decor_{i}", o)]


def build_overlay(b, i):
    """Wall dressing hugging the -Y face of a wall block placed in the same cell (face plane y = -2, natural faces
    bulge to y = -2 - base(z)); stays within u in [-1.3, 1.3] and ~0.5 m of the face."""
    o = []
    ts = b.ts
    base = base_of(b)
    r = random.Random(ts + "ov" + str(i))
    if ts == "ember_caverns":
        if i == 1:     # lava fall pouring from under the overhang into a small pool
            for k, u in enumerate((-0.32, 0.0, 0.3)):
                verts, faces = [], []
                n = 12
                w = (0.2, 0.28, 0.18)[k]
                for j in range(n + 1):
                    z = (WALL_H - 0.1) * (1 - j / n)
                    uu = u + 0.05 * math.sin(j * 1.1 + k)
                    y = -2.0 - base(z) - 0.09 - 0.012 * k
                    verts += [(uu - w / 2, y, z), (uu + w / 2, y, z)]
                for j in range(n):
                    faces.append((2 * j, 2 * j + 2, 2 * j + 3, 2 * j + 1))
                col = G.rgb(("#ff8a2a", "#ffb04a", "#ff6a1a")[k])
                o.append(G.colored_mesh(f"fall{k}", verts, faces, [col] * n, ["M_Emit"] * n))
            o.append(C.disc("pool", 0.55, 0.02, 9, "#ff8a2a", "M_Emit", loc=(0, -2.0 - base(0) - 0.2, 0)))
            o.append(C.disc("pool_hi", 0.3, 0.025, 7, "#ffd36a", "M_Emit", loc=(0, -2.0 - base(0) - 0.22, 0)))
            for k, u in enumerate((-0.6, 0.55)):
                o.append(inst("qd", "modular_dungeon_pack/Rock4", b.pal, M=T(G.face_point(base, u, 0, 0.15)[:2] + (-0.05,), (0, 0, k * 70), 0.7)))
        else:          # obsidian growth and a glowing fissure
            for k in range(4):
                u = 0.75 + r.uniform(-0.25, 0.25)
                p = G.face_point(base, u, 0, 0.12)
                o.append(C.crystal(f"obs{k}", r.uniform(0.1, 0.17), r.uniform(0.6, 1.5), r.choice(("#2b2233", "#3b2f48")), "M_Toon",
                                   loc=p, rot=(r.uniform(-15, 5), r.uniform(-12, 12), r.uniform(0, 60))))
            pts = [(-0.7, 0.1), (-0.55, 0.9), (-0.8, 1.6), (-0.5, 2.5), (-0.65, 3.3)]
            verts, faces = [], []
            for j, (u, z) in enumerate(pts):
                y = -2.0 - base(z) - 0.12
                w = 0.13 * (1 - j / len(pts)) + 0.04
                verts += [(u - w, y, z), (u + w, y, z)]
            for j in range(len(pts) - 1):
                faces.append((2 * j, 2 * j + 2, 2 * j + 3, 2 * j + 1))
            o.append(G.colored_mesh("fissure", verts, faces, [G.rgb("#ff7a26")] * len(faces), ["M_Emit"] * len(faces)))
    elif ts == "frost_grotto":
        if i == 1:     # frozen waterfall + icicle curtain
            o += frozen_fall(b, 112, -0.9, 0.9)
            lip = G.face_point(base, 0, WALL_H - 0.1)[1]
            o += icicles(b, lip - 0.02, WALL_H - 0.1, -1.3, 1.3, 7, seed=113, length=(0.5, 1.3))
        else:          # crystal outcrop on the wall + snow at the foot
            for k, (u, z, s) in enumerate([(-0.8, 0.0, 1.0), (0.7, 0.0, 0.8), (0.1, 2.0, 0.8)]):
                cl = crystals(b, (0, 0, 0), 4, 0.9 * s, seed=114 + k)
                p = G.face_point(base, u, z, 0.05)
                for c in cl:
                    c.data.transform(T(p, (80 if z > 0 else 0, 0, 0)))
                o += cl
            o.append(G.blob("snow", G.face_point(base, -0.1, 0, 0.15)[:2] + (0.0,), 0.6, "#f2f9ff", 115, squash=0.35))
    elif ts == "haunted_crypt":
        if i == 1:     # torn banner and cobwebs
            o.append(tattered_banner(b, 116, 0.0))
            o += cobweb(b, (-1.66, -2.28, 3.92), 1.0, 0) + cobweb(b, (1.66, -2.28, 3.92), 0.8, -90)
        else:          # wall shelf of candles and skulls
            sh = inst("kd", "shelf_small_candles", b.pal, M=T((0, -2.0, 1.5), (0, 0, 0), 1.0), rules={"kd:r2c7": ("tint", b.flame, "M_Emit")})
            o.append(sh)
            for k, x in enumerate((-0.55, 0.6)):
                o.append(inst("kh", lowpoly("kh", "skull", 0.35), b.pal, M=T((x, -2.2, 0.0), (0, 0, 180 + 25 * (k * 2 - 1)), 0.38)))
            o += cobweb(b, (1.66, -2.28, 3.92), 0.9, -90)
    else:
        if i == 1:     # ivy curtain
            o += vines(b, 117, n=7, x0=-1.3, x1=1.3, lmin=1.2, lmax=3.4)
            o += grass(b, [(-1.0, -2.15, 0), (0.6, -2.2, 0)], 0.9, seed=118, small=True)
        else:          # moss, a climbing root and a flowering shrub at the foot
            for k, (u, z, s) in enumerate([(-0.6, 3.3, 0.5), (0.3, 2.6, 0.4), (-0.2, 1.6, 0.35)]):
                o.append(G.blob(f"moss{k}", (u, -2.0, z), s, ("#4f8a36", "#5a9a3c")[k % 2], 120 + k, squash=1.0))
                o[-1].data.transform(Matrix.Translation((u, -2.0, z)) @ Matrix.Diagonal((1, 0.25, 1, 1)) @ Matrix.Translation((-u, 2.0, -z)))
            o.append(C.polyline_strip("root", [(-0.9, 0.0), (-0.7, 1.0), (-0.5, 1.8), (-0.6, 2.8), (-0.3, 3.6)], 0.12, 0.0, "#5a3e2a", "M_Toon"))
            o[-1].data.transform(Matrix(((1, 0, 0, 0), (0, 0, -1, -2.03), (0, 1, 0, 0), (0, 0, 0, 1))))
            o.append(G.blob("shrub", (0.6, -2.35, 0.3), 0.5, "#4c8f34", 121))
            o += flowers(b, [(0.2, -2.4, 0), (-0.1, -2.3, 0)], 122, 0.8)
    return [finish(f"overlay_{i}", o)]


# ---------------------------------------------------------------- driver

def build_piece(b, piece):
    if piece.startswith("floor_"):
        return build_floor(b, piece)
    if piece.startswith("wall_"):
        return build_wall(b, piece)
    if piece in ("door", "door_locked"):
        return build_door(b, piece)
    if piece in ("stairs_up", "stairs_down"):
        return build_stairs(b, piece)
    if piece.startswith("decor_"):
        return build_decor(b, int(piece[-1]))
    if piece.startswith("overlay_"):
        return build_overlay(b, int(piece[-1]))
    return {"chest": build_chest, "lore_stone": build_lore_stone, "trap": build_trap, "spring": build_spring,
            "warp": build_warp, "torch": build_torch, "boss_gate": build_boss_gate, "foe_marker": build_foe_marker}[piece](b)


def park(objs, piece, offset):
    """Rename contract objects so the next piece can reuse the names, and move the roots out of the way."""
    for o in objs:
        o.name = f"{piece}|{o.name}"
        if o.parent is None:
            o.location += offset


def build_kit(ts, pieces=PIECES, export=True, keep=False):
    """Build (and export) pieces of one tileset. keep=True leaves every piece in the scene (renamed `piece|obj`)."""
    b = Biome(ts)
    report = []
    built = {}
    for n, piece in enumerate(pieces):
        roots = build_piece(b, piece)
        allobjs = []
        for r in roots:
            allobjs += [r] + list(r.children_recursive)
        allobjs = list(dict.fromkeys(allobjs))
        t = sum(C.tris(o) for o in allobjs)
        path = None
        if export:
            path = A.export_fbx(f"Environment/{ts}/{piece}.fbx", objects=allobjs)
        report.append(dict(piece=piece, tris=t, objects=[o.name for o in allobjs], path=path))
        print(f"[cc0kit] {ts}/{piece}: {t} tris {[o.name for o in allobjs]}", flush=True)
        if keep:
            park(allobjs, piece, Vector((0, 0, 0)))
            built[piece] = allobjs
        else:
            for o in allobjs:
                me = o.data if o.type == "MESH" else None
                bpy.data.objects.remove(o, do_unlink=True)
                if me is not None and me.users == 0:
                    bpy.data.meshes.remove(me)
    return report, built


def main():
    argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
    sel = argv[argv.index("--biome") + 1].split(",") if "--biome" in argv else list(TILESETS)
    pieces = argv[argv.index("--pieces") + 1].split(",") if "--pieces" in argv else list(PIECES)
    export = "--no-export" not in argv
    if "--out" in argv:   # write the FBX tree somewhere else (dry runs); default = Assets/_Game/Resources/Art
        A.ASSETS = argv[argv.index("--out") + 1]
    import json
    for ts in sel:
        A.reset_scene()
        rep, _ = build_kit(ts, pieces, export=export)
        if export and pieces == list(PIECES):
            os.makedirs(A.BLEND_DIR, exist_ok=True)
            with open(os.path.join(A.BLEND_DIR, f"env_cc0_{ts}.json"), "w") as f:
                json.dump(rep, f, indent=1)
    print("[cc0kit] DONE", flush=True)


if __name__ == "__main__":
    main()
