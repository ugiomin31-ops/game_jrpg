"""Per-enemy recipes for cc0_monsters.build(): source model, clip mapping, size, recolour rules, elite dressing.

Enemy ids not listed in SPECS keep their procedural generator (Blender/enemies_a, enemies_b, bosses):
see GAPS for why. Colours are sRGB hex. Rules are applied first-match-wins to every face corner of the
baked source colours (see cc0_monsters.recolour for the keys).
"""
import math

from mathutils import Vector, noise

import cc0_monsters as C

A = C.A
Q = "quaternius_ultimate_monsters/"
K = "kaykit_skeletons/"

# Size of the procedural enemy each model replaces, measured from the previous FBX in its Idle pose:
# (height, bottom z, width) in metres. None = do not match that dimension (flyers keep their own hover,
# wide-winged flyers are matched on wingspan instead of height). Unity multiplies elites by scale_mult itself.
TARGETS = {
    "slime": (0.74, 0.0, None),
    "magma_slime": (0.84, 0.0, 1.23),          # 'mean' fit: spikes are long
    "mushroom": (0.94, 0.0, None),
    "elite_mushroom": (1.16, 0.0, None),
    "sprout": (1.05, 0.0, None),
    "bat": (None, None, 1.90),
    "elite_bat": (None, None, 1.90),
    "grave_bat": (None, None, 1.90),
    "fire_drake": (None, None, 2.40),
    "elite_fire_drake": (None, None, 2.60),
    "phoenix": (None, None, 2.00),
    "wisp": (1.42, 0.30, None),               # CANDIDATES only
    "penguin_mage": (1.15, 0.0, None),         # body; + wizard hat ~0.3 m = old 1.47 m
    "skeleton": (1.31, 0.0, None),
    "elite_skeleton": (1.58, 0.0, None),
}

GAPS = {
    "coral_crab": "no crab / hermit-crab body in either pack",
    "elite_coral_crab": "no crab / hermit-crab body in either pack",
    "jellyfish": "no jellyfish; Squidle / Hywirl are winged imps, not bells with tentacles",
    "ice_wolf": "no quadruped wolf (Blob/Dog is a dog head only)",
    "elite_ice_wolf": "no quadruped wolf",
    "sand_golem": "no golem body (Goleling is a winged head)",
    "elite_sand_golem": "no golem body",
    "scarecrow": "no pumpkin scarecrow",
    "elite_scarecrow": "no pumpkin scarecrow",
    "boss": "boss needs a 10-25k tri unique rig with a Roar clip; Skeleton_Mage is a 4.6k tri minion",
    "forest_guardian": "no tree giant",
    "frost_kraken": "no kraken",
    "flame_sphinx": "no sphinx / lion body",
    "wisp": "only Flying/Ghost (a winged imp) is close; recoloured it does not read as a flame wisp (see CANDIDATES)",
}

# ---------------------------------------------------------------- shared rule pieces

EYE_WHITE = {"near": "#8f92a0", "tol": 0.05, "to": "#f4f4f8"}
PUPIL = {"near": "#1e1f22", "tol": 0.05, "to": "#18141f"}


def noisy(freq, lo, hi=9.0, seed=(0.0, 0.0, 0.0)):
    """where() predicate: 3D Perlin noise of the face centre (metres) between lo and hi."""
    off = Vector(seed)

    def f(info):
        v = noise.noise(info["co"] * freq + off)
        return lo <= v <= hi
    return f


def spots(freq, r, seed=(0.0, 0.0, 0.0)):
    """where() predicate: round spots (Voronoi cells of size 1/freq m, spot radius r in cell units)."""
    off = Vector(seed)

    def f(info):
        d = noise.voronoi(info["co"] * freq + off, distance_metric="DISTANCE", exponent=2.5)[0][0]
        return d < r
    return f


def veins(freq, width, seed=(0.0, 0.0, 0.0)):
    """where() predicate: thin crack lines along the zero set of Perlin noise."""
    off = Vector(seed)
    return lambda info: abs(noise.noise(info["co"] * freq + off)) < width


def above(z):
    return lambda info: info["p"][2] >= z


def below(z):
    return lambda info: info["p"][2] < z


def bones(*names):
    return lambda info: bool(info["bones"] & set(names))


# ---------------------------------------------------------------- clip maps per source family

BLOB_CLIPS = {
    "Idle": dict(src="Idle", len=60),
    "Run": dict(src="Walk", len=16),
    "Attack": dict(src="Bite_Front", len=21),
    "Cast": dict(src="Yes", len=33, release=0.45),
    "Hit": dict(src="HitRecieve", len=12),
    "Die": dict(src="Death", len=28, play=16),
    "Victory": dict(src="Dance", len=40, repeat=2),
}
BLOB_IMPACT = ("Head", "Head2", "Head3")

FLY_CLIPS = {
    "Idle": dict(src="Flying_Idle", len=42),
    "Run": dict(src="Fast_Flying", len=24),
    "Attack": dict(src="Headbutt", len=27),
    "Cast": dict(src="Punch", len=36, release=0.45),
    "Hit": dict(src="HitReact", len=13),
    "Die": dict(src="Death", len=30, play=20),
    "Victory": dict(src="Yes", len=42),
}
FLY_IMPACT = ("Head", "Neck")

BIG_CLIPS = {
    "Idle": dict(src="Idle", len=60, repeat=2),
    "Run": dict(src="Run", len=17),
    "Attack": dict(src="Weapon", len=24),
    "Cast": dict(src="Punch", len=34, release=0.45),
    "Hit": dict(src="HitReact", len=13),
    "Die": dict(src="Death", len=30, play=23),
    "Victory": dict(src="Wave", len=46),
}
BIG_IMPACT = ("LowerArm.R", "LowerArm.L", "Index3.R", "Index3.L")

KAY_CLIPS = {
    "Idle": dict(src="Idle", len=48),
    "Run": dict(src="Running_A", len=24),
    "Attack": dict(src="1H_Melee_Attack_Chop", len=26),
    "Cast": dict(src="Spellcast_Shoot", len=33, release=0.40),
    "Hit": dict(src="Hit_A", len=14),
    "Die": dict(src="Death_C_Skeletons", len=36, play=34),
    "Victory": dict(src="Cheer", len=46),
}
KAY_IMPACT = ("hand.r", "handslot.r")
# A KayKit prop parented to a hand slot keeps its glTF (Y-up) frame inside the bone: undo the importer's
# Y-up -> Z-up conversion of the prop inside the bone frame.
GLTF_IN_BONE = (-90, 0, 0)


# ---------------------------------------------------------------- elite / costume dressing

def penguin_hat(rig, body):
    centre, top, lo, hi = C.bone_cap(body, ["Head", "Neck"])
    r = (hi.x - lo.x) * 0.36
    at = Vector((centre.x, centre.y + r * 0.1, top - r * 0.55))
    brim = A.cyl("hat_brim", r=r * 1.25, depth=r * 0.12, loc=at, color="#2c3f9e", seg=28)
    cone = A.cone("hat_cone", r=r * 0.78, depth=r * 2.1, loc=(at.x, at.y + r * 0.15, at.z + r * 1.05),
                  rot=(-14, 0, 0), color="#3550c8", seg=24)
    band = A.cyl("hat_band", r=r * 0.8, depth=r * 0.2, loc=(at.x, at.y, at.z + r * 0.14), color="#9fe7ff",
                 mat="M_Emit", seg=24)
    star = A.sphere("hat_star", r=r * 0.17, loc=(at.x, at.y - r * 0.76, at.z + r * 0.62), color="#bff3ff",
                    mat="M_Emit", seg=10, rings=6)
    return [("Head", o) for o in (brim, cone, band, star)]


def wisp_flames(rig, body):
    centre, top, lo, hi = C.bone_cap(body, ["Head"])
    r = (hi.x - lo.x) * 0.16
    out = []
    for i, (dx, h, tilt) in enumerate(((0.0, 2.6, 0), (-0.9, 1.7, 18), (0.9, 1.7, -18))):
        f = A.cone(f"wisp_flame{i}", r=r * (1.0 if i == 0 else 0.7), depth=r * h,
                   loc=(centre.x + dx * r, centre.y + r * 0.2, top - r * 0.6 + r * h * 0.5), rot=(0, tilt, 0),
                   color="#9ff4ff", mat="M_Emit", seg=10)
        out.append(("Head", f))
    return out


# ---------------------------------------------------------------- the table

SPECS = {
    # --- verdant ruins -------------------------------------------------------------------------
    "slime": dict(
        source=Q + "Blob/GreenBlob.gltf", clips=BLOB_CLIPS, impact_bones=BLOB_IMPACT,
        rules=[EYE_WHITE, PUPIL,
               {"near": "#3d5235", "to": "#5ed46b", "mat": "M_Clear", "shade": False}],
    ),
    "sprout": dict(
        source=Q + "Blob/Alien.gltf", clips=BLOB_CLIPS, impact_bones=BLOB_IMPACT,
        rules=[EYE_WHITE, PUPIL,
               {"near": "#4f7935", "to": "#7fd34e", "shade": False},          # curled sprouts
               {"near": "#542964", "where": above(0.55), "to": "#a9773f", "shade": False},
               {"near": "#542964", "to": "#8a5a30", "shade": False}],          # root bulb
    ),
    "mushroom": dict(
        source=Q + "Blob/Mushnub.gltf", clips=BLOB_CLIPS, impact_bones=BLOB_IMPACT,
        subdivide=[dict(near="#2a6f8b", cuts=2)],
        rules=[EYE_WHITE, PUPIL,
               {"near": "#2a6f8b", "where": spots(6.0, 0.30), "to": "#fff3dc", "shade": False},  # spots
               {"near": "#2a6f8b", "to": "#d63d3d", "shade": False},           # cap
               {"near": "#a58c72", "to": "#f1dcc0", "shade": False}],          # stem / face
    ),
    "elite_mushroom": dict(
        source=Q + "Blob/Mushnub_Evolved.gltf", clips=BLOB_CLIPS, impact_bones=BLOB_IMPACT,
        rules=[EYE_WHITE, PUPIL,
               {"near": "#2a6f8b", "to": "#8b46d8", "shade": False},
               {"near": "#cc9129", "to": "#b6ff4a", "mat": "M_Emit", "shade": False},   # toxic spikes
               {"near": "#a58c72", "to": "#efdcc8", "shade": False},
               {"near": "#5b354a", "to": "#4a2350", "shade": False}],
    ),
    "bat": dict(
        source=Q + "Flying/Goleling.gltf", clips=FLY_CLIPS, impact_bones=FLY_IMPACT, fit="width",
        rules=[EYE_WHITE, PUPIL,
               {"near": "#738636", "to": "#5a4a8c", "shade": False},
               {"near": "#5b354a", "to": "#c06ab8", "shade": False}],
    ),
    # --- frost grotto --------------------------------------------------------------------------
    "elite_bat": dict(
        source=Q + "Flying/Goleling_Evolved.gltf", clips=FLY_CLIPS, impact_bones=FLY_IMPACT, fit="width",
        rules=[EYE_WHITE, PUPIL,
               {"near": "#738636", "to": "#7b2a3e", "shade": False},
               {"near": "#5b354a", "to": "#e0505a", "shade": False},
               {"near": "#a58c72", "to": "#f0c9a8", "shade": False},
               {"near": "#cc9129", "to": "#ffd24a", "shade": False}],
    ),
    "penguin_mage": dict(
        source=Q + "Big/Birb.gltf", clips=BIG_CLIPS, impact_bones=BIG_IMPACT,
        rules=[EYE_WHITE, PUPIL,
               {"near": "#979593", "where": above(0.72), "to": "#a8ecff", "mat": "M_Emit", "shade": False},  # crest
               {"near": "#979593", "to": "#f2f5fb", "shade": False},                     # white belly
               {"near": "#962118", "to": "#ffb12e", "shade": False},                     # beak / feet
               {"near": "#355a96", "to": "#26324f", "shade": False}],
        dress=penguin_hat,
    ),
    # --- ember caverns -------------------------------------------------------------------------
    "magma_slime": dict(
        source=Q + "Blob/GreenSpikyBlob.gltf", clips=BLOB_CLIPS, impact_bones=BLOB_IMPACT, fit="mean",
        subdivide=[dict(near="#3d5235", cuts=1)],
        rules=[{"near": "#8f92a0", "where": lambda i: i["p"][1] < -0.55 and i["n"][1] < -0.5, "to": "#fff6e8",
                "shade": False},
               PUPIL,
               {"near": "#8f92a0", "to": "#ffb43a", "mat": "M_Emit", "shade": False},  # molten spikes
               {"near": "#3d5235", "where": veins(3.2, 0.10), "to": "#ff7a1c", "mat": "M_Emit", "shade": False},
               {"near": "#3d5235", "to": "#3d2522", "shade": False}],                  # basalt crust
    ),
    "fire_drake": dict(
        source=Q + "Flying/Dragon.gltf", clips=dict(FLY_CLIPS, Attack=dict(src="Punch", len=27),
                                                     Cast=dict(src="Headbutt", len=36, release=0.5)),
        impact_bones=("Head", "Wing4.L", "Wing4.R"), fit="width",
        rules=[EYE_WHITE, PUPIL,
               {"near": "#965221", "to": "#e2582a", "shade": False},
               {"near": "#5b354a", "to": "#ffd27a", "shade": False}],
    ),
    "elite_fire_drake": dict(
        source=Q + "Flying/Dragon_Evolved.gltf", clips=dict(FLY_CLIPS, Attack=dict(src="Punch", len=27),
                                                             Cast=dict(src="Headbutt", len=36, release=0.5)),
        impact_bones=("Head", "Wing4.L", "Wing4.R"), fit="width",
        rules=[EYE_WHITE, PUPIL,
               {"near": "#965221", "to": "#b52632", "shade": False},
               {"near": "#5b354a", "to": "#ffbe3d", "mat": "M_Emit", "shade": False}],
    ),
    "phoenix": dict(
        source=Q + "Flying/Pigeon.gltf", clips=FLY_CLIPS, impact_bones=FLY_IMPACT, fit="width",
        rules=[{"near": "#8f92a0", "where": bones("Head", "Neck"), "to": "#f4f4f8", "shade": False},
               PUPIL,
               {"near": "#8f92a0", "to": "#ffcf3a", "mat": "M_Emit", "shade": False},   # flame wings
               {"near": "#5c458b", "to": "#ff6a26", "shade": False},
               {"near": "#cc9129", "to": "#ffe07a", "shade": False}],
    ),
    # --- haunted crypt -------------------------------------------------------------------------
    "skeleton": dict(
        source=K + "Characters/Skeleton_Minion.glb", clips=KAY_CLIPS, impact_bones=KAY_IMPACT,
        attach=[dict(rel=K + "Assets/Skeleton_Blade.gltf", bone="handslot.r", rot=GLTF_IN_BONE)],
        rules=[{"glow": True, "to": "#ffd84a", "mat": "M_Emit", "shade": False}],
    ),
    "elite_skeleton": dict(
        source=K + "Characters/Skeleton_Warrior.glb",
        clips=dict(KAY_CLIPS, Attack=dict(src="1H_Melee_Attack_Slice_Diagonal", len=26)),
        impact_bones=KAY_IMPACT,
        attach=[dict(rel=K + "Assets/Skeleton_Axe.gltf", bone="handslot.r", rot=GLTF_IN_BONE),
                dict(rel=K + "Assets/Skeleton_Shield_Large_A.gltf", bone="handslot.l", rot=GLTF_IN_BONE)],
        rules=[{"glow": True, "to": "#ff5a3c", "mat": "M_Emit", "shade": False},
               {"sat": (0.0, 0.12), "val": (0.0, 0.75), "to": lambda c: (c[0] * 0.78, c[1] * 0.86, c[2] * 1.12)}],
    ),
    "grave_bat": dict(
        source=Q + "Flying/Goleling.gltf", clips=FLY_CLIPS, impact_bones=FLY_IMPACT, fit="width",
        rules=[{"near": "#8f92a0", "to": "#d8fff4", "mat": "M_Emit", "shade": False},   # ghost-light eyes
               PUPIL,
               {"near": "#738636", "to": "#56607a", "shade": False},
               {"near": "#5b354a", "to": "#5fb3a6", "mat": "M_Clear", "shade": False}],
    ),
}

# Built only on request (generate_all.py --only <id>): matches judged too weak to replace the procedural model.
# wisp: the Ghost imp recoloured as a blue spirit does not read as a will-o'-wisp flame; the procedural flame stays.
CANDIDATES = {
    "wisp": dict(
        source=Q + "Flying/Ghost.gltf", clips=FLY_CLIPS, impact_bones=("Head", "LowerArm.L", "LowerArm.R"),
        rules=[{"near": "#8f92a0", "to": "#ffffff", "mat": "M_Emit", "shade": False},
               PUPIL,
               {"near": "#2a1030", "where": below(0.30), "to": "#8ff0ff", "mat": "M_Emit", "shade": False},
               {"near": "#2a1030", "to": "#4a8dff", "mat": "M_Clear", "shade": False}],
        dress=wisp_flames,
    ),
}

# Side by side with the procedural models (Blender/preview/enemy_cc0_before_after.png) only these read as a clear
# upgrade; the other matches stay buildable on request but the procedural model ships.
SHIPPED = ("skeleton", "elite_skeleton", "magma_slime")
for _id in [k for k in SPECS if k not in SHIPPED]:
    CANDIDATES[_id] = SPECS.pop(_id)
    GAPS[_id] = "CC0 match built (generate_all.py --only %s) but the procedural model reads better" % _id

ALL = {**SPECS, **CANDIDATES}
