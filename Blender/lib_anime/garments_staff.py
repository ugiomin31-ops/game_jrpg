"""Modern guild-staff garments for the textured VRoid route (Blender/npcs/generate_staff.py).

New helpers only: they call the shared garments.py / anime_body.py / humanoid.py functions and never change them.
Everything is built in the rest pose on the measured body (like cuirass/tabard) and weighted to the body's own bones
through H.add / H.add_blend, so the staff keep the game's 20-bone rig and clips.
"""
import math

import bpy
from mathutils import Matrix, Vector

import abyss_bpy as A
import anime_body as AB
import garments as G
import vroid_base as VB
from humanoid import V, ellipsoid, lathe, sweep

# staff palette
NAVY, NAVY_L = "#1f3556", "#2c4a78"
BLACK, BLACK_L = "#17181c", "#2a2c33"
WHITE = "#fbf6ea"
RED, RED_D = "#e2535e", "#b53a48"
GOLD = G.GOLD


# ---------------------------------------------------------------- body

def staff_body(H, src, height, hair, iris, brow, drop=None, island=None):
    """Face, hair and eyes of a staff member on a VRoid sample (same recolour pipeline as heroes_anime.hero_body)."""
    hd = (lambda h: any((h - p).length < 0.01 for p in drop)) if drop else None
    body = VB.build(H, src, height=height, hair_drop=hd, island_drop=island)
    VB.gradient_map(body, "Hair", hair)
    VB.gradient_map(body, "EyeIris", iris, keep_bright=0.92)
    VB.gradient_map(body, "FaceBrow", brow, stretch=False)
    return body


def boots(H, body, color, cuff=None, top_off=0.05):
    """Ankle boots / sneakers from the knee down; trouser legs under the top are dropped (as the archer does)."""
    VB.drop_material(body, "Shoes")
    j = H.j
    btop = j["knee.L"].z - top_off
    for S in ("L", "R"):
        AB.boot(H, body, S, btop, color, cuff_color=cuff)
    AB.drop_faces(body, lambda co: co.z < btop - 0.03)


def torso_cloth(H, body, color, bottom, top, pad=0.014, name="cloth", pattern=None, lapel=None, seg=40):
    """A closed torso shell over the clothes: rings measured from the body between `bottom` and `top`, closed at the
    neck. `pattern` and `lapel` are paint_faces callbacks (co, n) -> colour or None."""
    j = H.j
    hz = j["hip"].z
    dom = AB.dominant_bones(body)
    rings = []
    for k in range(6):
        z = bottom + (top - bottom) * k / 5
        cy, rx, ry = G.torso_ring(body, z, dom=dom)
        bust = 0.022 * max(0.0, 1 - abs(z - (j["chest"].z - 0.01)) / 0.08)
        rings.append((z, cy - bust * 0.5, rx + pad, ry + pad + bust * 0.5))
    ncy, nrx, nry = G.torso_ring(body, j["neck"].z - 0.02, dom=dom)
    rings.append((j["neck"].z - 0.025, ncy, nrx + 0.03, nry + 0.025))
    o = G.ring_shell(name, rings, color, seg=seg, p=2.2)
    G.conform_to(o, body, 0.008)
    if pattern:
        AB.paint_faces(o, pattern)
    if lapel:
        AB.paint_faces(o, lapel)
    H.add_blend(o, G.chain_w([("hips", hz), ("spine", j["spine"].z), ("chest", j["chest"].z)]))
    return o


def jacket(H, body, color, lapel_color, bottom=None, top=None, name="jacket"):
    """Single-breasted blazer: the torso shell with a lapel V painted on the front."""
    j = H.j
    bottom = j["hip"].z + 0.02 if bottom is None else bottom
    top = j["shoulder.L"].z - 0.02 if top is None else top

    def lapel(co, n):
        if n.y < -0.55 and 0.02 < abs(co.x) < 0.075 and co.z > bottom + 0.30 * (top - bottom):
            return lapel_color
        return None
    return torso_cloth(H, body, color, bottom, top, pad=0.016, name=name, lapel=lapel)


def shirt(H, body, color, bottom=None, top=None, pattern=None, name="shirt"):
    """Fitted shirt over the trousers' top. `pattern` paints the front faces (Hawaiian print)."""
    j = H.j
    bottom = j["hip"].z + 0.04 if bottom is None else bottom
    top = j["shoulder.L"].z - 0.02 if top is None else top
    return torso_cloth(H, body, color, bottom, top, pad=0.010, name=name, pattern=pattern)


def hawaiian(color_a, color_b, color_c):
    """Front print: small flowers (rounded dots) on a grid, in three colours, shifted row by row."""
    def fn(co, n):
        if n.y > -0.4:
            return None
        gx, gz = co.x * 22.0, co.z * 22.0
        row = math.floor(gz)
        col = math.floor(gx + (0.5 if row % 2 else 0.0))
        fx, fz = gx - col - (0.5 if row % 2 else 0.0), gz - row
        if (fx * fx + (fz - 0.5) ** 2) < 0.12:
            return (color_a, color_b, color_c)[(col * 3 + row) % 3]
        return None
    return fn


def apron(H, body, color, trim, hem, width=22):
    """Front apron (no back panel) with a border, from the waist down to `hem`."""
    return G.tabard(H, body, color, hem, trim_color=trim, back=False, width=width)


def cap(H, body, color, brim_color, back=True):
    """Baseball cap: a fitted crown and a brim arc (lathe 0 deg = front -Y). back=True turns the brim to the back."""
    c, half, top = G.skull_box(H, body)
    R = max(half.x, half.y) * 1.06 + 0.008
    cz = top - half.z * 0.45
    h = 0.095
    a0, a1 = (100, 260) if back else (-80, 80)
    crown = lathe("cap_crown", [(R * 1.02, 0.0), (R * 1.0, h * 0.45), (R * 0.93, h * 0.8), (R * 0.72, h * 0.97),
                                (R * 0.45, h * 1.0), (0.004, h * 1.01)], color, center=(c.x, c.y, cz), sy=0.94, seg=32)
    brim = lathe("cap_brim", [(R * 0.96, -0.003), (R * 1.50, -0.010), (R * 1.54, -0.003), (R * 1.0, 0.006)],
                 brim_color, center=(c.x, c.y, cz), sy=0.98, seg=40, thick=0.005, caps=False, a0=a0, a1=a1)
    band = lathe("cap_band", [(R * 1.025, 0.0), (R * 1.01, 0.014)], brim_color, center=(c.x, c.y, cz), sy=0.94,
                 seg=32, caps=False)
    out = [crown, brim, band]
    for o in out:
        H.add("head", o)
    return out


def beard(H, body, color):
    """Short full beard and moustache built from ellipsoids on the jaw (rigid to the head)."""
    c, half, top = G.skull_box(H, body)
    out = [ellipsoid("beard", V((c.x, c.y - half.y * 0.25, c.z - half.z * 0.78)),
                     (half.x * 0.66, half.y * 0.62, half.z * 0.50), color, seg=18, rings=10),
           ellipsoid("moustache", V((c.x, c.y - half.y * 0.93, c.z - half.z * 0.40)),
                     (half.x * 0.40, half.y * 0.22, half.z * 0.12), color, seg=14, rings=6)]
    for o in out:
        H.add("head", o)
    return out


def scarf_tie(H, body, color, tail=0.22):
    """Narrow neck tie / scarf in front of the collar."""
    return G.scarf(H, body, color, tail=tail, trim_color=None)


def cross_badge(H, body, color=RED, z_off=0.06):
    """A small first-aid cross pinned on the chest, on the front of the torso."""
    j = H.j
    z = j["chest"].z - z_off
    cy, rx, ry = G.torso_ring(body, z, dom=AB.dominant_bones(body))
    y = cy - ry - 0.012
    out = [A.box("cross_v", (0.024, 0.010, 0.072), loc=(0.0, y, z), color=color),
           A.box("cross_h", (0.072, 0.010, 0.024), loc=(0.0, y - 0.001, z), color=color)]
    for o in out:
        A.apply_transform(o)
        H.add("chest", o)
    return out


def id_lanyard(H, body, card="#ffffff", strap="#2f6fc4"):
    """Coloured lanyard from the neck to an ID card on the chest."""
    j = H.j
    nz, cz = j["neck"].z, j["chest"].z
    cy, rx, ry = G.torso_ring(body, cz, dom=AB.dominant_bones(body))
    y = cy - ry - 0.045  # outside the blazer shell (pad 0.016) and its lapels
    strap_o = sweep("lanyard", [V((0.0, cy - ry * 0.5, nz - 0.02)), V((0.0, y - 0.01, cz + 0.02)),
                                V((0.0, y - 0.005, cz - 0.04))], [0.006, 0.006, 0.006], strap, seg=6)
    card_o = A.box("id_card", (0.075, 0.008, 0.10), loc=(0.0, y - 0.02, cz - 0.06), color=card)
    band_o = A.box("id_band", (0.075, 0.010, 0.02), loc=(0.0, y - 0.02, cz - 0.02), color=strap)
    A.apply_transform(card_o)
    A.apply_transform(band_o)
    H.add("chest", strap_o, card_o, band_o)
    return [strap_o, card_o, band_o]


def clipboard(H, side="L"):
    """A clipboard with a paper sheet, held against the forearm."""
    j = H.j
    e = (j[f"elbow.{side}"] + j[f"wrist.{side}"]) * 0.5
    board = A.box("clipboard", (0.20, 0.012, 0.27), loc=(e.x, e.y - 0.07, e.z), color="#8b5e3c")
    paper = A.box("clip_paper", (0.17, 0.010, 0.23), loc=(e.x, e.y - 0.080, e.z), color="#fffdf5")
    clip = A.box("clip_top", (0.05, 0.016, 0.02), loc=(e.x, e.y - 0.085, e.z + 0.13), color="#9aa3ad")
    for o in (board, paper, clip):
        A.apply_transform(o)
    H.add("forearm." + side, board, paper, clip)
    return [board, paper, clip]


def handheld_box(H, bone, name, loc, size, color, screen=None):
    """A small rigid prop (calculator, tablet) on a forearm, with an optional emissive screen."""
    out = [A.box(name, size, loc=loc, color=color)]
    if screen:
        out.append(A.box(name + "_screen", (size[0] * 0.72, 0.004, size[2] * 0.6),
                         loc=(loc[0], loc[1] - size[1] * 0.5 - 0.002, loc[2]), color=screen, mat="M_Emit"))
    for o in out:
        A.apply_transform(o)
    H.add(bone, *out)
    return out


def tablet(H, side="L"):
    j = H.j
    e = (j[f"elbow.{side}"] + j[f"wrist.{side}"]) * 0.5
    return handheld_box(H, "forearm." + side, "tablet", (e.x, e.y - 0.06, e.z), (0.15, 0.014, 0.21),
                        "#2b313b", screen="#8fe0ff")


def calculator(H, side="R"):
    j = H.j
    e = (j[f"elbow.{side}"] + j[f"wrist.{side}"]) * 0.5
    return handheld_box(H, "forearm." + side, "calc", (e.x, e.y - 0.06, e.z), (0.11, 0.022, 0.15),
                        "#e9e4da", screen="#8ff0a4")


def wrench(H, side="R", color="#9aa6b8"):
    """Big open-end wrench hanging from the hand: a thick shaft and a jaw with an opening at its lower end."""
    j = H.j
    g = j[f"grip.{side}"]
    shaft = sweep("wrench_shaft", [V((g.x, g.y - 0.02, g.z)), V((g.x, g.y - 0.05, g.z - 0.30)),
                                   V((g.x, g.y - 0.05, g.z - 0.46))], [0.022, 0.022, 0.024], color, seg=10)
    jaw = A.box("wrench_jaw", (0.11, 0.045, 0.10), loc=(g.x, g.y - 0.05, g.z - 0.55), color=color)
    slot = A.box("wrench_slot", (0.05, 0.05, 0.06), loc=(g.x, g.y - 0.05, g.z - 0.52), color="#4a5467")
    A.apply_transform(jaw)
    A.apply_transform(slot)
    H.add("hand." + side, shaft, jaw, slot)
    return [shaft, jaw, slot]


def cane(H, side="R", wood="#5b3e2c", gold=GOLD):
    """Walking cane: a shaft from the floor to the hand, with a gold crook handle."""
    j = H.j
    g = j[f"grip.{side}"]
    x, y = g.x, g.y - 0.03
    shaft = sweep("cane_shaft", [V((x, y, 0.0)), V((x, y, g.z * 0.5)), V((x, y, g.z + 0.02))],
                  [0.014, 0.014, 0.015], wood, seg=8)
    crook = sweep("cane_crook", [V((x, y, g.z + 0.02)), V((x, y - 0.02, g.z + 0.10)),
                                 V((x, y - 0.09, g.z + 0.10)), V((x, y - 0.11, g.z + 0.04))],
                  [0.015, 0.016, 0.016, 0.015], gold, seg=8)
    H.add("hand." + side, shaft, crook)
    return [shaft, crook]


def skirt(H, body, color, trim, hem, width=90):
    """Full A-line skirt from the waist to `hem` (front and back panels)."""
    return G.tabard(H, body, color, hem, trim_color=trim, back=True, width=width)


def suit_vest(H, body, color, trim, bottom=None, top=None, width=24):
    """Waistcoat: a closed front panel from the waist to the chest, gold edge, no back."""
    j = H.j
    hz = j["hip"].z
    bottom = hz + 0.02 if bottom is None else bottom
    top = j["chest"].z + 0.02 if top is None else top
    return G.tabard(H, body, color, hem=top, trim_color=trim, back=False, width=width, top=bottom)
