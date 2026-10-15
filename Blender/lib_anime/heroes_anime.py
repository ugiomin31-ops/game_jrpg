"""Anime-proportioned hero builders (archer first). Same ids, bones and clips as the chibi heroes."""
import math

import anime_body as AB
import garments as G
import vroid_base as VB
import body as B
import costumes as C
from humanoid import V, chain, cyl, lathe, mix, shade, solidify, sweep, ring, zgrad

GOLD = C.GOLD



# ---------------------------------------------------------------- the four heroes (same person through every job tier)

MALE, FEMALE = "HairSample_Male.vrm", "HairSample_Female.vrm"
_TAILS = (V((0.064, -0.022, 1.602)), V((-0.064, -0.022, 1.602)))
_EARS = (V((0.088, 0.021, 1.613)), V((-0.086, 0.021, 1.611)))

IDENTITY = {
    "warrior": dict(src=MALE, height=1.70, hair=[(0.0, "#3a1608"), (0.45, "#8a3a1c"), (0.85, "#c0622e"), (1.0, "#f3a678")],
                    iris=[(0.0, "#4a2008"), (0.5, "#c17e22"), (1.0, "#ffd890")], brow=[(0.0, "#3a1608"), (1.0, "#8a4a28")]),
    "archer": dict(src=MALE, height=1.64, hair=[(0.0, "#6b4416"), (0.45, "#c48a36"), (0.85, "#f0c870"), (1.0, "#fff0c0")],
                   iris=[(0.0, "#123018"), (0.5, "#3f8a3a"), (1.0, "#b4e48a")], brow=[(0.0, "#4a2e12"), (1.0, "#b08040")]),
    "mage": dict(src=FEMALE, height=1.56, drop=_EARS, hair=[(0.0, "#3e2f6a"), (0.5, "#9484c8"), (0.85, "#cbbfea"),
                                                           (1.0, "#f6f2ff")],
                 iris=[(0.0, "#0e2a5a"), (0.5, "#358ed4"), (1.0, "#b0e4ff")], brow=[(0.0, "#4e3e78"), (1.0, "#9a8ac8")]),
    "cleric": dict(src=FEMALE, height=1.54, drop=_EARS + _TAILS, hair=[(0.0, "#7a3048"), (0.5, "#d98aa0"),
                                                                     (0.85, "#f2b8c6"), (1.0, "#fff2f6")],
                   iris=[(0.0, "#4a1010"), (0.5, "#c86346"), (1.0, "#ffc8a8")], brow=[(0.0, "#8a4050"), (1.0, "#d08a9a")]),
}


def hero_body(H, who):
    """The hero's own face, hair and eyes on the VRoid base (shared by all of that hero's job outfits)."""
    d = IDENTITY[who]
    drop = d.get("drop")
    hd = (lambda h: any((h - p).length < 0.01 for p in drop)) if drop else None
    body = VB.build(H, d["src"], height=d["height"], hair_drop=hd,
                    island_drop=VB.female_ears if d["src"] == FEMALE else None)
    VB.gradient_map(body, "Hair", d["hair"])
    VB.gradient_map(body, "EyeIris", d["iris"], keep_bright=0.92)
    VB.gradient_map(body, "FaceBrow", d["brow"], stretch=False)
    return body


def warrior():
    """전사: navy gambeson, steel cuirass and pauldrons, leather gauntlets, steel greaves, short red cape."""
    H = AB.AnimeHumanoid("warrior")
    body = hero_body(H, "warrior")
    j = H.j
    hz = j["hip"].z
    # Armour sits on the slim body: the hoodie keeps only its sleeves (as the gambeson sleeves).
    G.drop_where(body, "Tops", lambda co, bone: G.part_of(bone) in G.TORSO + ("head", "shoulder", "thigh"))
    VB.gradient_map(body, "Tops", [(0.0, "#141c30"), (0.5, "#24345a"), (0.85, "#34497a"), (1.0, "#4a6496")])
    VB.gradient_map(body, "Bottoms", [(0.0, "#16151a"), (0.6, "#2c2a33"), (1.0, "#4a4854")])
    VB.drop_material(body, "Shoes")
    H.build_rig()
    H.add_weighted(body)
    steel, navy = "#8e9db2", "#2a3c66"
    G.greaves(H, body, steel, trim_color=G.GOLD)
    tunic = G.robe_skirt(H, body, navy, hz - 0.24, flare=1.5, trim_color=G.GOLD, split=40, top=hz + 0.02,
                         name="tunic")
    plate = G.cuirass(H, body, steel)
    G.gorget(H, body, steel, cloth=navy)
    for S in ("L", "R"):
        G.pauldron(H, body, S, steel, lames=2, size=0.85)
        G.bracer(H, body, S, "#6a4630", trim_color="#9a6e44")
    bx, by = AB.section(body, hz + 0.02)
    belt = B.belt(H, hz + 0.03, "#5a3a26", G.GOLD, width=0.040, r=bx + 0.03, sy=(by + 0.03) / (bx + 0.03))
    G.tabard(H, body, "#b8323c", hz - 0.30, back=False, emblem=G.GOLD, width=20, over=[tunic] + belt)
    G.cape(H, body, "#b8323c", hz - 0.42, inner="#7a1e28", wave=0.08, over=[tunic] + plate + belt)
    return H

def archer():
    """Ranger built on the CC0 VRoid sample: the hoodie becomes a forest-green hooded tunic, blond hair, green
    eyes, leather boots, belt and pouch, a crossbody strap and a quiver on the back."""
    H = AB.AnimeHumanoid("archer")
    body = VB.build(H, "HairSample_Male.vrm")
    j = H.j
    hz, nz = j["hip"].z, j["neck"].z
    VB.gradient_map(body, "Tops", [(0.0, "#10220f"), (0.5, "#24482a"), (0.85, "#35633a"), (1.0, "#4f8048")])
    VB.gradient_map(body, "Bottoms", [(0.0, "#2a1f17"), (0.6, "#4b3a2b"), (1.0, "#7a6450")])
    VB.gradient_map(body, "Hair", [(0.0, "#6b4416"), (0.45, "#c48a36"), (0.85, "#f0c870"), (1.0, "#fff0c0")])
    VB.gradient_map(body, "EyeIris", [(0.0, "#123018"), (0.5, "#3f8a3a"), (1.0, "#b4e48a")], keep_bright=0.92)
    VB.gradient_map(body, "FaceBrow", [(0.0, "#4a2e12"), (1.0, "#b08040")], stretch=False)
    VB.drop_material(body, "Shoes")
    H.build_rig()
    H.add_weighted(body)

    leather, dark = "#6e4a30", "#4a3020"
    btop = j["knee.L"].z - 0.05
    for S in ("L", "R"):
        AB.boot(H, body, S, btop, leather, cuff_color=shade(leather, 1.18))
    # The trouser legs inside the boots would poke through when the knees bend.
    AB.drop_faces(body, lambda co: co.z < btop - 0.03)
    # Belt and pouch over the hoodie hem, which now reads as a belted tunic.
    bz = hz + 0.02
    bx, by = AB.section(body, bz)
    B.belt(H, bz, dark, GOLD, width=0.040, r=bx + 0.010, sy=(by + 0.010) / (bx + 0.010))
    B.pouch(H, (bx * 0.72, -by * 0.86 - 0.012, bz - 0.045), (0.07, 0.04, 0.065), "#825636", "#9c6c40", button=GOLD,
            rot_z=-25)
    # Crossbody quiver strap and quiver on the back.
    sh = j["shoulder.L"]
    cy = j["chest"].y
    pts = [(sh.x * 0.55, cy - 0.04, sh.z + 0.03), (sh.x * 0.15, cy - 0.13, j["chest"].z - 0.02),
           (-sh.x * 0.35, cy - 0.13, bz + 0.12), (-sh.x * 0.75, cy - 0.06, bz + 0.03)]
    strap = sweep("strap", pts, [(0.018, 0.004)] * 4, dark, seg=6, up=(0, -1, 0))
    # Weighted along the spine only: the body's own weights near the hip belong to the hanging hand.
    AB.conform(strap, body, 0.012)
    H.add_blend(strap, chain([("hips", hz), ("spine", j["spine"].z), ("chest", j["chest"].z)]))
    back = AB.section(body, j["chest"].z)[1]
    p0, p1 = V((-0.07, cy + back + 0.05, bz + 0.10)), V((-0.17, cy + back + 0.10, nz + 0.10))
    H.add("chest", cyl("quiver", p0, p1, 0.042, 0.050, "#71492f", seg=16))
    H.add("chest", ring("quiver_rim", p1, p1 - p0, 0.049, 0.006, GOLD, seg=18, minor=5))
    for k in range(5):
        a = math.radians(72 * k)
        off = V((math.cos(a) * 0.022, math.sin(a) * 0.022, 0))
        q = p1 + off + (p1 - p0).normalized() * 0.05
        H.add("chest", cyl("arrow", p1 + off - (p1 - p0).normalized() * 0.05, q, 0.004, 0.004, "#c9b48a", seg=6))
        H.add("chest", cyl("fletch", q - (p1 - p0).normalized() * 0.01, q + (p1 - p0).normalized() * 0.035, 0.012,
                           0.004, "#e8e0cc" if k % 2 else "#a83a2a", seg=4))
    return H


def _female_feet(H, body, color, cuff=None, top=None):
    VB.drop_material(body, "Shoes")
    j = H.j
    top = j["knee.L"].z - 0.10 if top is None else top
    for S in ("L", "R"):
        AB.boot(H, body, S, top, color, cuff_color=cuff)
    AB.drop_faces(body, lambda co: co.z < top - 0.04)


def mage():
    """마법사: indigo dress, wide witch hat with a blue gem, violet capelet with gold edge, brown boots."""
    H = AB.AnimeHumanoid("mage")
    body = hero_body(H, "mage")
    j = H.j
    hz = j["hip"].z
    VB.gradient_map(body, "Tops", [(0.0, "#16112c"), (0.45, "#2e245c"), (0.85, "#4a3a8a"), (1.0, "#6a58b0")])
    H.build_rig()
    H.add_weighted(body)
    _female_feet(H, body, "#5e3a2a", cuff="#7a4e38")
    G.capelet(H, body, "#3a2462", depth=0.11, trim_color=G.GOLD, inner="#24163e")
    bx, by = AB.section(body, hz + 0.06)
    B.belt(H, hz + 0.06, "#4a2e22", G.GOLD, width=0.030, r=bx + 0.008, sy=(by + 0.008) / (bx + 0.008))
    B.pouch(H, (bx * 0.8, -by * 0.6, hz + 0.02), (0.06, 0.035, 0.055), "#7a4e30", "#9a6a40", button=G.GOLD,
            rot_z=-35)
    G.witch_hat(H, body, "#2c1f52", band="#b0864a", gem="#5fd0ff")
    return H


def cleric():
    """사제: cream dress, white hooded mantle with gold edge, red stole with gold crosses, brown boots."""
    H = AB.AnimeHumanoid("cleric")
    body = hero_body(H, "cleric")
    j = H.j
    hz = j["hip"].z
    VB.gradient_map(body, "Tops", [(0.0, "#8a7a68"), (0.5, "#d8ccb8"), (0.85, "#f4ecdc"), (1.0, "#fffaf0")])
    H.build_rig()
    H.add_weighted(body)
    _female_feet(H, body, "#6e4a34")
    cap = G.capelet(H, body, "#fbf6ea", depth=0.13, trim_color=G.GOLD, inner="#e6dcc8")
    G.pendant(H, [body, cap], j["chest"].z - 0.01, gem="#ff5a6e")
    bx, by = AB.section(body, hz + 0.06)
    B.belt(H, hz + 0.06, "#6a4630", G.GOLD, width=0.028, r=bx + 0.008, sy=(by + 0.008) / (bx + 0.008))
    G.circlet(H, body, G.GOLD, gem="#ff7a8a", z=0.62)
    return H


HERO_BUILDERS = dict(archer=archer, warrior=warrior, mage=mage, cleric=cleric)
