"""Campaign expansion weapons: tiers T5-T7 of the four weapon lines and the 16 job signature weapons.

Ids come from Tools/content/spec.py (GEAR_LINES, JOB_WEAPONS). Same conventions as swords/arcane/bows:
origin = grip, weapon along +Z, blade flats in the YZ plane (edge -Y), staff/mace heads face -Y.
Each design changes the silhouette (guard, head architecture, limb shape), not just the colour.
Run: blender -b --factory-startup -P Blender/weapons/generate_all.py -- <id> ...
"""
import math
import os
import sys

sys.path.append(os.path.dirname(os.path.abspath(__file__)))
import _common as W  # noqa: E402
import swords as S  # noqa: E402
import arcane as R  # noqa: E402
import bows as B  # noqa: E402

A = W.A

VOID = "#2a1f3d"
VOID_DK = "#160f22"
VOID_GLOW = "#a45cff"
TEAL = "#2fb5b0"
TEAL_HI = "#8ff1e4"
PEARL = "#f3ecf6"
CORAL = "#ff7f73"
BONE = "#e6dcc4"
BONE_DK = "#b6a888"
GHOST = "#7dffd0"
CRIMSON = "#b3122a"
HOLY = "#fff2c2"


# ------------------------------------------------------------------ shared sword pieces

def sword_core(name, prof, color, hone, gradient=None):
    b = W.blade(name, prof, color=color, edge_frac=0.6)
    if gradient:
        A.gradient(b, gradient[0], gradient[1])
    S.edge_hone(b, hone)
    return b, S.thick_fn(prof)


def sword_hilt(P, z_top, grip, band, metal, pommel_gem=None, pommel="ball", length=0.13):
    P += W.wrap_grip("grip", z_top - length, z_top, 0.0168, turns=6, color=grip, band=band)
    P.append(W.band("fer_top", z_top, 0.0215, 0.014, color=metal))
    P.append(W.band("fer_bot", z_top - length - 0.003, 0.0215, 0.014, color=metal))
    zp = z_top - length - 0.03
    if pommel == "ball":
        P.append(A.sphere("pommel", r=0.027, loc=(0, 0, zp), scale=(0.85, 1, 1), color=metal, seg=18, rings=10))
    elif pommel == "spike":
        P.append(A.lathe("pommel", [(0.0, zp - 0.05), (0.012, zp - 0.03), (0.026, zp), (0.02, zp + 0.016), (0.0, zp + 0.018)], color=metal, seg=12))
    elif pommel == "ring":
        P.append(A.torus("pommel", R=0.026, r=0.008, loc=(0, 0, zp - 0.006), rot=(0, 90, 0), color=metal, seg=24, minor=8))
    if pommel_gem:
        P += S.side_gems("pgem", 0.012, zp, 0.02 if pommel != "ring" else 0.006, pommel_gem)


def quillons(P, color, trim=None, spread=0.11, rise=0.03, z=0.07, width=0.017, down=False):
    for s in (1, -1):
        dz = -rise if down else rise
        path = W.curve_pts([(0, s * 0.015, z), (0, s * spread * 0.5, z + dz * 0.2), (0, s * spread * 0.9, z + dz * 0.7), (0, s * spread, z + dz * 1.4)], 22)
        P.append(W.sweep(f"quil{s}", path, lambda t: width * (1 - 0.7 * t), lambda t: width * 0.9 * (1 - 0.5 * t), color=color, up=(1, 0, 0)))
        if trim:
            P.append(A.sphere(f"qend{s}", r=width * 0.8, loc=path[-1], color=trim, seg=12, rings=8))


# ------------------------------------------------------------------ T5-T7 swords

def sword_runic():
    """T5 (crypt): dark steel with a square-tipped, stepped blade and glowing cyan rune ladder."""
    P = []
    prof = [(0.085, 0.044, 0.011), (0.2, 0.046, 0.0105), (0.62, 0.044, 0.009), (0.74, 0.04, 0.008),
            (0.8, 0.03, 0.0065), (0.86, 0.0, 0.003)]
    b, surf = sword_core("blade", prof, "#59606e", "#c9d6e6")
    P.append(b)
    for s in (1, -1):
        P.append(S.inlay(f"chan{s}", S.strip(0.14, 0.72, 0.012), s, surf, depth=0.0022, color="#20262f"))
        for i in range(7):
            z = 0.18 + i * 0.075
            glyph = [(-0.008, z), (0.0, z + 0.022), (0.008, z), (0.0, z + 0.008)] if i % 2 else [(-0.007, z), (0.007, z), (0.007, z + 0.02), (-0.007, z + 0.02), (0.0, z + 0.01)]
            P.append(S.inlay(f"rune{s}{i}", glyph, s, surf, depth=0.0016, lift=0.0016, color="#5ee7ff", mat="M_Emit"))
    # angular stepped guard (three stacked bars) and rune stone in the centre
    for i, (w, h) in enumerate([(0.11, 0.07), (0.085, 0.085), (0.05, 0.1)]):
        P.append(A.box(f"guard{i}", (0.034, w * 2, 0.016), loc=(0, 0, h - 0.008), color="#3a404c" if i % 2 else "#7f8898", bevel=0.004))
    P += S.side_gems("rune_stone", 0.017, 0.082, 0.018, "#5ee7ff")
    sword_hilt(P, 0.055, "#1f2632", "#3a4658", "#7f8898", "#5ee7ff", pommel="spike")
    return W.finalize(P, "sword_runic")


def sword_tidal():
    """T6 (sunken temple): curved sabre-like blade with a wave crest back edge, coral guard and pearl."""
    P = []
    curve = lambda z: 0.035 * ((z - 0.09) / 0.8) ** 2  # noqa: E731
    prof = [(0.09, 0.042, 0.0105, curve(0.09))]
    z = 0.15
    while z < 0.84:
        prof.append((z, 0.044 + 0.012 * math.sin((z - 0.15) / 0.69 * math.pi), 0.0095 - 0.003 * (z - 0.15) / 0.7, curve(z)))
        z += 0.05
    prof += [(0.88, 0.024, 0.005, curve(0.88)), (0.93, 0.0, 0.003, curve(0.93) + 0.012)]
    b, surf = sword_core("blade", prof, "#7fd6dc", "#effffd", gradient=("#2a7f9a", "#bff6f2"))
    P.append(b)
    for s in (1, -1):
        # wave crests along the spine side of the blade
        for i in range(6):
            zc = 0.2 + i * 0.11
            yc = curve(zc) + 0.02
            crest = [(yc - 0.004, zc - 0.03), (yc + 0.016, zc - 0.006), (yc + 0.006, zc + 0.002), (yc + 0.012, zc + 0.024), (yc - 0.008, zc + 0.01)]
            P.append(S.inlay(f"crest{s}{i}", crest, s, surf, depth=0.002, lift=0.0008, color=TEAL_HI, mat="M_Emit"))
    # coral-branch guard
    for s in (1, -1):
        P.append(R.prong(f"coral{s}", [(0, 0, 0.07), (0, s * 0.05, 0.075), (0, s * 0.085, 0.11), (0, s * 0.1, 0.15)], CORAL, 0.018))
        P.append(R.prong(f"coral_b{s}", [(0, s * 0.045, 0.074), (0.0, s * 0.07, 0.05), (0, s * 0.09, 0.035)], "#ff9d8a", 0.012))
    P.append(A.lathe("shell", [(0.0, 0.04), (0.03, 0.05), (0.036, 0.075), (0.02, 0.1), (0.0, 0.105)], scale=(0.7, 1.2, 1), color=PEARL, seg=10))
    P += S.side_gems("pearl", 0.016, 0.075, 0.022, "#bdf6ff")
    sword_hilt(P, 0.04, "#1c5866", "#0f3640", "#d8c27a", None)
    P.append(A.sphere("pearl_pommel", r=0.024, loc=(0, 0, -0.12), color=PEARL, mat="M_Emit", seg=16, rings=10))
    return W.finalize(P, "sword_tidal")


def sword_void():
    """T7 (abyss): black jagged blade split by a violet glowing core, thorned guard."""
    P = []
    prof = [(0.09, 0.046, 0.011), (0.2, 0.05, 0.0105), (0.34, 0.044, 0.01), (0.42, 0.056, 0.0095), (0.56, 0.046, 0.009),
            (0.64, 0.058, 0.0085), (0.78, 0.042, 0.007), (0.88, 0.022, 0.005), (0.96, 0.0, 0.003)]
    b, surf = sword_core("blade", prof, VOID, "#8a72b8")
    P.append(b)
    for s in (1, -1):
        crack = []
        for i in range(15):
            z = 0.12 + i * 0.055
            crack.append(((0.006 if i % 2 else -0.006), z))
        left = [(y - 0.005, z) for y, z in crack]
        right = [(y + 0.005, z) for y, z in reversed(crack)]
        P.append(S.inlay(f"core{s}", left + [(0.0, 0.92)] + right, s, surf, depth=0.0022, lift=0.0006, color=VOID_GLOW, mat="M_Emit"))
    for s in (1, -1):
        for j, (zz, reach) in enumerate([(0.07, 0.12), (0.095, 0.09), (0.05, 0.08)]):
            path = W.curve_pts([(0, s * 0.02, zz), (0, s * reach * 0.6, zz + 0.01), (0, s * reach, zz + (0.05 if j != 2 else -0.04))], 16)
            P.append(W.sweep(f"thorn{s}{j}", path, lambda t: 0.015 * (1 - 0.95 * t), lambda t: 0.012 * (1 - 0.6 * t), color=VOID_DK, up=(1, 0, 0)))
    P.append(W.gem("eye", 0.026, loc=(0, -0.0, 0.075), rot=(0, 90, 0), color=VOID_GLOW))
    P.append(W.gem("eye_b", 0.026, loc=(0, 0.0, 0.075), rot=(0, -90, 0), color=VOID_GLOW))
    sword_hilt(P, 0.04, VOID_DK, "#4a2f6e", "#3c2c55", VOID_GLOW, pommel="spike")
    return W.finalize(P, "sword_void")


# ------------------------------------------------------------------ job swords

def sword_aegis():
    """Knight: broad straight blade, kite-shield guard with a blue field."""
    P = []
    prof = [(0.1, 0.05, 0.011), (0.2, 0.052, 0.0105), (0.66, 0.048, 0.009), (0.78, 0.04, 0.0075), (0.87, 0.0, 0.003)]
    b, surf = sword_core("blade", prof, W.SILVER, "#ffffff")
    P.append(b)
    for s in (1, -1):
        P.append(S.inlay(f"full{s}", S.strip(0.2, 0.7, 0.01), s, surf, depth=0.0022, color="#2c4f9e"))
    shield = [(-0.09, 0.13), (-0.09, 0.07), (-0.06, 0.035), (0.0, 0.0), (0.06, 0.035), (0.09, 0.07), (0.09, 0.13)]
    P.append(W.flat_plate("shield", shield, 0.03, color=W.GOLD, bevel=0.004))
    inner = [(y * 0.78, 0.075 + (z - 0.075) * 0.78) for y, z in shield]
    for s in (1, -1):
        P.append(W.flat_plate(f"field{s}", inner, 0.004, x=s * 0.016, color="#2c4f9e"))
        P.append(W.flat_plate(f"crossv{s}", [(-0.008, 0.12), (0.008, 0.12), (0.008, 0.03), (-0.008, 0.03)], 0.003, x=s * 0.019, color=W.GOLD_HI))
        P.append(W.flat_plate(f"crossh{s}", [(-0.05, 0.095), (0.05, 0.095), (0.05, 0.08), (-0.05, 0.08)], 0.003, x=s * 0.019, color=W.GOLD_HI))
    sword_hilt(P, 0.0, "#243c78", "#162650", W.GOLD, "#3f8cff", length=0.12)
    return W.finalize(P, "sword_aegis")


def sword_ravager():
    """Berserker: oversized cleaver with serrated back, chained grip, blood-red edge."""
    P = []
    prof = [(0.08, 0.05, 0.012), (0.18, 0.07, 0.012, -0.012), (0.5, 0.085, 0.011, -0.02), (0.72, 0.09, 0.01, -0.02),
            (0.82, 0.07, 0.008, -0.01), (0.9, 0.0, 0.004, 0.03)]
    b, surf = sword_core("blade", prof, "#3b3437", "#ff3a3a")
    P.append(b)
    for i in range(9):  # serrated teeth on the spine (+Y)
        z = 0.2 + i * 0.07
        y0 = 0.065 if z < 0.5 else 0.07
        P.append(W.flat_plate(f"tooth{i}", [(y0 - 0.005, z), (y0 + 0.028, z + 0.02), (y0 - 0.005, z + 0.04)], 0.016, color="#5c4f52"))
    for s in (1, -1):
        P.append(S.inlay(f"blood{s}", [(-0.07, 0.2), (-0.075, 0.72), (-0.06, 0.8), (-0.05, 0.72), (-0.05, 0.2)], s, surf, depth=0.002, color=CRIMSON, mat="M_Emit"))
        P.append(A.cyl(f"rivet{s}", r=0.012, depth=0.006, loc=(s * 0.013, -0.02, 0.14), rot=(0, 90, 0), color=W.IRON, seg=10))
    P.append(A.box("guard", (0.04, 0.2, 0.03), loc=(0, -0.005, 0.07), color="#2a2224", bevel=0.006))
    for s in (1, -1):
        P.append(A.cone(f"spike{s}", r=0.014, depth=0.06, loc=(0, s * 0.12, 0.07), rot=(-s * 90, 0, 0), color="#8e8a8c", seg=8))
    P += W.wrap_grip("grip", -0.15, 0.05, 0.02, turns=8, color="#511414", band="#1e0d0d")
    for i in range(5):
        P.append(A.torus(f"chain{i}", R=0.014, r=0.004, loc=(0.0, 0.0, -0.17 - i * 0.022), rot=(0, 90 * (i % 2), 0), color=W.IRON, seg=12, minor=6))
    P.append(A.sphere("pommel", r=0.028, loc=(0, 0, -0.29), color="#2a2224", seg=12, rings=8))
    return W.finalize(P, "sword_ravager")


def sword_holy_avenger():
    """Paladin: long white-gold blade, angel-wing guard, sun gem."""
    P = []
    prof = [(0.11, 0.042, 0.0105), (0.24, 0.044, 0.01), (0.78, 0.04, 0.0085), (0.9, 0.03, 0.0065), (0.99, 0.0, 0.003)]
    b, surf = sword_core("blade", prof, "#f4f6ff", "#ffffff", gradient=("#fff0c6", "#f4f6ff"))
    P.append(b)
    for s in (1, -1):
        P.append(S.inlay(f"gold{s}", S.strip(0.17, 0.85, 0.011), s, surf, depth=0.0022, color=W.GOLD))
        P.append(S.inlay(f"light{s}", S.strip(0.19, 0.82, 0.006), s, surf, depth=0.0018, lift=0.0014, color=HOLY, mat="M_Emit"))
    for s in (1, -1):
        for j in range(4):
            z = 0.07 + j * 0.022
            P.append(W.flat_plate(f"wing{s}{j}", [(s * 0.02, z), (s * (0.07 + j * 0.02), z + 0.02 + j * 0.01), (s * (0.13 - j * 0.012), z + 0.06 + j * 0.015), (s * 0.05, z + 0.02)], 0.02, color=W.WHITE if j % 2 else W.GOLD_HI, bevel=0.002))
    P.append(A.sphere("sun", r=0.03, loc=(0, 0, 0.085), scale=(0.75, 1, 1), color=W.GOLD, seg=16, rings=10))
    P += S.side_gems("sun_gem", 0.02, 0.085, 0.02, "#ffb43c")
    sword_hilt(P, 0.05, "#f4efe4", "#d8cbb0", W.GOLD, "#ffb43c", length=0.15)
    return W.finalize(P, "sword_holy_avenger")


def sword_conqueror():
    """Warlord: massive greatsword, crowned crossguard, black-gold blade with banner ribbon."""
    P = []
    prof = [(0.12, 0.06, 0.013), (0.26, 0.062, 0.012), (0.8, 0.056, 0.01), (0.94, 0.045, 0.008), (1.05, 0.0, 0.004)]
    b, surf = sword_core("blade", prof, "#2b2730", "#f2d48a")
    P.append(b)
    for s in (1, -1):
        P.append(S.inlay(f"gold{s}", S.strip(0.2, 0.92, 0.02), s, surf, depth=0.0024, color=W.GOLD))
        P.append(S.inlay(f"dark{s}", S.strip(0.22, 0.9, 0.012), s, surf, depth=0.0018, lift=0.0016, color="#7a1a22"))
    # crown guard: a ring of five spikes
    P.append(A.box("guard", (0.05, 0.26, 0.04), loc=(0, 0, 0.09), color=W.GOLD_DK, bevel=0.008))
    for i, y in enumerate((-0.11, -0.055, 0.0, 0.055, 0.11)):
        P.append(A.cone(f"crown{i}", r=0.016, depth=0.07 if i == 2 else 0.05, loc=(0, y, 0.135 if i == 2 else 0.125), color=W.GOLD, seg=8))
        P.append(W.gem(f"cg{i}", 0.01, loc=(0.026, y, 0.09), rot=(0, 90, 0), color="#ff2a3a"))
    P.append(W.sweep("ribbon", W.curve_pts([(0.0, 0.03, 0.13), (0.03, 0.06, 0.08), (0.02, 0.05, 0.0), (0.04, 0.08, -0.08)], 18), lambda t: 0.018 * (1 - 0.3 * t), lambda t: 0.003, color="#a01822", up=(1, 0, 0)))
    sword_hilt(P, 0.065, "#1d1a22", W.GOLD_DK, W.GOLD, "#ff2a3a", length=0.2)
    return W.finalize(P, "sword_conqueror")


# ------------------------------------------------------------------ T5-T7 staves

def staff_bone():
    """T5 (crypt): bone-segment shaft with a horned skull cradling a ghost-green flame orb."""
    p = R.shaft_parts(0.62, BONE_DK, BONE, "#3a3a2c")
    for i in range(6):
        p.append(A.sphere(f"knuckle{i}", r=0.026, loc=(0, 0, 0.16 + i * 0.08), scale=(1, 1, 0.55), color=BONE, seg=12, rings=8))
    p.append(A.sphere("skull", r=0.062, loc=(0, 0, 0.7), scale=(0.9, 1, 1.0), color=BONE, seg=18, rings=12))
    p.append(A.box("jaw", (0.07, 0.06, 0.03), loc=(0, -0.02, 0.645), color=BONE_DK, bevel=0.008))
    for s in (-1, 1):
        p.append(A.sphere(f"socket{s}", r=0.016, loc=(s * 0.022, -0.05, 0.71), color=GHOST, mat="M_Emit", seg=10, rings=6))
        p.append(R.prong(f"horn{s}", [(s * 0.04, 0, 0.74), (s * 0.1, 0.0, 0.8), (s * 0.11, 0, 0.9), (s * 0.07, 0, 0.96)], BONE_DK, 0.022))
    p.append(A.sphere("soul", r=0.05, loc=(0, 0, 0.88), color=GHOST, mat="M_Emit", seg=16, rings=10))
    p.append(W.crystal("flame", 0.03, 0.12, loc=(0, 0, 0.9), color="#c4ffe8"))
    return W.finalize(p, "staff_bone")


def staff_coral():
    """T6 (sunken temple): branching coral head holding a glowing pearl, shell collar."""
    p = R.shaft_parts(0.64, "#d8c27a", "#2f6f80", "#18404d")
    p.append(A.lathe("shell", [(0.03, 0.62), (0.07, 0.65), (0.085, 0.69), (0.05, 0.71)], color=PEARL, seg=10))
    branches = [((0, 0, 0.66), (0.06, 0, 0.76), (0.12, 0, 0.84), (0.1, 0, 0.94)),
                ((0, 0, 0.66), (-0.07, 0, 0.74), (-0.12, 0.0, 0.86), (-0.09, 0.0, 0.97)),
                ((0, 0, 0.66), (0.0, 0.05, 0.78), (0.02, 0.07, 0.9)),
                ((0.06, 0, 0.76), (0.13, 0.02, 0.75), (0.17, 0.02, 0.8)),
                ((-0.07, 0, 0.74), (-0.14, -0.01, 0.72), (-0.17, -0.01, 0.77))]
    for i, br in enumerate(branches):
        p.append(R.prong(f"coral{i}", list(br), CORAL if i < 3 else "#ff9d8a", 0.024 if i < 3 else 0.015))
    p.append(A.sphere("pearl", r=0.055, loc=(0, -0.01, 0.82), color="#e8fbff", mat="M_Emit", seg=20, rings=12))
    p.append(A.torus("bubble_ring", R=0.085, r=0.006, loc=(0, -0.01, 0.82), rot=(70, 0, 20), color=TEAL_HI, mat="M_Emit", seg=28, minor=6))
    R.rune_chain(p, 0.18, 0.56, TEAL_HI, count=5)
    return W.finalize(p, "staff_coral")


def staff_void():
    """T7 (abyss): split black prongs around a floating void orb inside two crossed rings."""
    p = R.shaft_parts(0.66, "#5a4378", VOID, VOID_DK)
    for s in (-1, 1):
        p.append(R.prong(f"fork{s}", [(0, 0, 0.62), (s * 0.12, 0, 0.7), (s * 0.15, 0, 0.86), (s * 0.08, 0, 1.0)], VOID_DK, 0.03))
    p.append(A.sphere("void", r=0.065, loc=(0, 0, 0.84), color="#1a0d2b", seg=20, rings=12))
    p.append(A.sphere("void_glow", r=0.03, loc=(0, -0.045, 0.84), color=VOID_GLOW, mat="M_Emit", seg=12, rings=8))
    p.append(A.torus("ring_a", R=0.1, r=0.007, loc=(0, 0, 0.84), rot=(90, 0, 30), color=VOID_GLOW, mat="M_Emit", seg=32, minor=6))
    p.append(A.torus("ring_b", R=0.1, r=0.007, loc=(0, 0, 0.84), rot=(90, 0, -30), color="#d0a8ff", mat="M_Emit", seg=32, minor=6))
    for i in range(3):
        a = i * 2 * math.pi / 3
        p.append(W.crystal(f"shard{i}", 0.018, 0.07, loc=(0.13 * math.cos(a), 0.05 * math.sin(a), 0.98 + 0.02 * i), rot=(0, 20, 0), color=VOID_GLOW))
    R.rune_chain(p, 0.16, 0.58, VOID_GLOW, count=6)
    return W.finalize(p, "staff_void")


# ------------------------------------------------------------------ job staves

def staff_prism():
    """Elementalist: a clear prism ringed by four elemental crystals (fire, ice, thunder, earth)."""
    p = R.shaft_parts(0.66, W.SILVER, "#e9e4f2", "#55607a")
    p.append(W.crystal("prism", 0.06, 0.24, loc=(0, 0, 0.74), color="#f2fbff", seg=3, base=0.3))
    for i, color in enumerate(("#ff5a2a", "#7fd8ff", "#ffe14a", "#8fd66b")):
        a = math.pi / 4 + i * math.pi / 2
        x, y = 0.11 * math.cos(a), 0.11 * math.sin(a)
        p.append(R.prong(f"arm{i}", [(0, 0, 0.66), (x * 0.7, y * 0.7, 0.7), (x, y, 0.76)], W.SILVER, 0.012))
        p.append(W.crystal(f"elem{i}", 0.024, 0.09, loc=(x, y, 0.76), color=color))
    p.append(A.torus("halo", R=0.12, r=0.006, loc=(0, 0, 0.8), color=W.GOLD, seg=36, minor=6))
    return W.finalize(p, "staff_prism")


def staff_hex():
    """Warlock: twisted black wood ending in a hooked crook with a cursed green eye and dangling charms."""
    def wob(z):
        return 0.01 * math.sin(z * 22), 0.01 * math.cos(z * 17)
    p = [W.shaft("shaft", [(0.0, -0.41), (0.018, -0.38), (0.022, 0.1), (0.026, 0.6), (0.02, 0.66)], color="#2b2233", wobble=wob)]
    p += W.wrap_grip("grip", -0.065, 0.065, 0.026, turns=6, color="#3d5a2a", band="#1d2b14")
    p.append(W.helix("vine", 0.1, 0.6, 0.027, 4, radius=0.004, color="#5c8a3a"))
    path = W.curve_pts([(0.0, 0, 0.64), (0.05, 0, 0.74), (0.03, 0, 0.84), (-0.04, 0, 0.86), (-0.07, 0, 0.8)], 30)
    p.append(W.sweep("crook", path, lambda t: 0.026 * (1 - 0.5 * t), lambda t: 0.022 * (1 - 0.4 * t), color="#2b2233", up=(0, 1, 0)))
    p.append(A.sphere("eye", r=0.04, loc=(0.0, -0.0, 0.76), color="#e8ffd8", seg=16, rings=10))
    p.append(A.sphere("iris", r=0.022, loc=(0.0, -0.028, 0.76), color="#5aff6a", mat="M_Emit", seg=12, rings=8))
    p.append(A.sphere("pupil", r=0.009, loc=(0.0, -0.045, 0.76), color="#101010", seg=8, rings=6))
    for i, x in enumerate((-0.07, -0.05)):
        p.append(A.tube(f"cord{i}", [(x, 0, 0.8), (x - 0.005, 0, 0.72 - i * 0.03)], radius=0.003, color="#c8b07a", seg=6))
        p.append(W.gem(f"charm{i}", 0.014, loc=(x - 0.005, 0, 0.7 - i * 0.03), rot=(180, 0, 0), color="#a45cff"))
    return W.finalize(p, "staff_hex")


def staff_arcanum():
    """Archmage: tall gold staff, great blue orb inside three orbiting rings, open book wings."""
    p = R.shaft_parts(0.72, W.GOLD, "#26306a", "#4a3a8c")
    p.append(A.sphere("orb", r=0.075, loc=(0, 0, 0.9), color="#5fb4ff", mat="M_Emit", seg=24, rings=14))
    for i, rot in enumerate(((90, 0, 0), (30, 0, 60), (30, 0, -60))):
        p.append(A.torus(f"orbit{i}", R=0.11 + i * 0.012, r=0.006, loc=(0, 0, 0.9), rot=rot, color=W.GOLD_HI, seg=40, minor=6))
    p.append(A.lathe("cup", [(0.02, 0.7), (0.05, 0.74), (0.07, 0.8), (0.055, 0.83)], color=W.GOLD, seg=16))
    for s in (-1, 1):
        R.wing(p, s, 0.74, W.GOLD, 3)
    p.append(W.star("crest", 0.04, 0.017, loc=(0, 0, 1.02), color=W.GOLD_HI))
    R.rune_chain(p, 0.16, 0.66, "#9fd0ff", count=8)
    return W.finalize(p, "staff_arcanum")


def staff_abyss_eye():
    """Abyssal: tentacles curl up around a giant violet eye."""
    p = R.shaft_parts(0.62, "#4a3060", VOID_DK, "#3a2050")
    for i in range(5):
        a = i * 2 * math.pi / 5
        x, y = math.cos(a), math.sin(a)
        p.append(R.prong(f"tentacle{i}", [(0.02 * x, 0.02 * y, 0.6), (0.1 * x, 0.1 * y, 0.68), (0.12 * x, 0.12 * y, 0.8), (0.06 * x, 0.06 * y, 0.92), (0.0, 0.0, 0.95)], "#3c1f55", 0.024))
    p.append(A.sphere("eyeball", r=0.07, loc=(0, 0, 0.78), color="#f2e8ff", seg=20, rings=12))
    p.append(A.sphere("iris", r=0.04, loc=(0, -0.042, 0.78), scale=(1, 0.6, 1), color=VOID_GLOW, mat="M_Emit", seg=16, rings=10))
    p.append(A.box("pupil", (0.012, 0.01, 0.05), loc=(0, -0.068, 0.78), color="#0b0612", bevel=0.004))
    for i in range(6):
        a = i * math.pi / 3
        p.append(A.sphere(f"small_eye{i}", r=0.011, loc=(0.035 * math.cos(a), -0.02 + 0.0 * a, 0.6 + 0.03 * math.sin(a)), color="#ff6aff", mat="M_Emit", seg=8, rings=6))
    return W.finalize(p, "staff_abyss_eye")


# ------------------------------------------------------------------ T5-T7 bows

def bow_wraith():
    """T5 (crypt): pale bone limbs wrapped in ghost chains with spectral flames at the nocks."""
    p = B.bow_base("wraith", 0.58, 0.2, "#7f8898", BONE, "#2f2f3a", 2)
    for s in (-1, 1):
        for j in range(5):
            z = 0.12 + j * 0.07
            p.append(A.torus(f"chain{s}{j}", R=0.014, r=0.0038, loc=(0, 0.06 + j * 0.022, s * z), rot=(90 * (j % 2), 0, 0), color="#5a6270", seg=12, minor=6))
        p.append(W.crystal(f"wisp{s}", 0.022, 0.08, loc=(0, 0.075, s * 0.6), rot=(0, 0, 0 if s > 0 else 180), color=GHOST))
        for j in range(3):
            p.append(W.flat_plate(f"rib{s}{j}", [(0.07 + j * 0.03, s * (0.2 + j * 0.06)), (0.14 + j * 0.02, s * (0.21 + j * 0.06)), (0.12 + j * 0.02, s * (0.24 + j * 0.06))], 0.016, color=BONE_DK))
    p.append(A.sphere("skull_grip", r=0.03, loc=(0, 0.02, 0), color=BONE, seg=12, rings=8))
    return W.finalize(p, "bow_wraith")


def bow_tide():
    """T6 (sunken temple): fin-shaped limbs with a scalloped membrane and pearl nocks."""
    p = B.bow_base("tide", 0.6, 0.21, "#d8c27a", "#1e7a86", "#14424c", 2)
    for s in (-1, 1):
        pts = [(0.03, s * 0.09), (0.16, s * 0.18), (0.24, s * 0.32), (0.22, s * 0.46), (0.17, s * 0.5), (0.2, s * 0.4), (0.15, s * 0.3), (0.09, s * 0.22)]
        p.append(W.flat_plate(f"fin{s}", pts, 0.008, color=TEAL_HI, bevel=0.001))
        for j in range(4):
            p.append(A.tube(f"ray{s}{j}", [(0.0, 0.05 + j * 0.03, s * (0.14 + j * 0.06)), (0.0, 0.17 + j * 0.015, s * (0.24 + j * 0.06))], radius=0.003, color=TEAL, seg=6))
        p.append(A.sphere(f"pearl{s}", r=0.02, loc=(0, 0.07, s * 0.6), color=PEARL, mat="M_Emit", seg=12, rings=8))
    p.append(A.lathe("shell_grip", [(0.0, -0.04), (0.035, -0.02), (0.035, 0.02), (0.0, 0.04)], loc=(0, 0.02, 0), scale=(1, 0.6, 1), color=PEARL, seg=10))
    return W.finalize(p, "bow_tide")


def bow_void():
    """T7 (abyss): black thorned recurve with violet energy veins and a floating crescent above the grip."""
    p = B.bow_base("void", 0.64, 0.22, "#5a4378", VOID, VOID_DK, 3)
    for s in (-1, 1):
        for j in range(5):
            z = 0.14 + j * 0.08
            p.append(W.flat_plate(f"thorn{s}{j}", [(0.08 + j * 0.022, s * z), (0.13 + j * 0.02, s * (z + 0.015)), (0.22 + j * 0.005, s * (z + 0.07))], 0.018, color=VOID_DK))
        path = W.curve_pts([(0, 0.03, s * 0.1), (0, 0.12, s * 0.26), (0, 0.21, s * 0.42), (0, 0.16, s * 0.55)], 30)
        p.append(A.tube(f"vein{s}", [(0.019, y, z) for x, y, z in path], radius=0.004, color=VOID_GLOW, mat="M_Emit", seg=6))
        p.append(A.tube(f"vein_b{s}", [(-0.019, y, z) for x, y, z in path], radius=0.004, color=VOID_GLOW, mat="M_Emit", seg=6))
    p.append(W.gem("void_core", 0.03, loc=(0, 0.0, 0.0), rot=(0, 90, 0), color=VOID_GLOW))
    return W.finalize(p, "bow_void")


# ------------------------------------------------------------------ job bows

def bow_longshot():
    """Sniper: very long, shallow limbs, a brass scope tube above the grip and a stabiliser rod."""
    p = B.bow_base("longshot", 0.74, 0.13, W.BRONZE, "#4a3a2a", "#2a3a2a", 1)
    p.append(A.cyl("scope", r=0.018, depth=0.17, loc=(0.0, 0.0, 0.14), color=W.BRONZE, seg=14))
    p.append(A.cyl("scope_lens", r=0.02, depth=0.01, loc=(0, 0, 0.225), color="#7fd8ff", mat="M_Emit", seg=14))
    p.append(A.box("scope_mount", (0.016, 0.03, 0.05), loc=(0, 0.0, 0.08), color=W.IRON_DK, bevel=0.003))
    p.append(A.cyl("stabiliser", r=0.007, depth=0.22, loc=(0, -0.12, -0.02), rot=(90, 0, 0), color=W.IRON_DK, seg=10))
    p.append(A.cyl("weight", r=0.016, depth=0.04, loc=(0, -0.23, -0.02), rot=(90, 0, 0), color=W.BRONZE, seg=12))
    return W.finalize(p, "bow_longshot")


def bow_thornvine():
    """Ranger: living-wood bow, vines spiralling round the limbs, leaves and a blossom at each tip."""
    p = B.bow_base("thornvine", 0.56, 0.17, "#4f7a32", "#6b4a2a", "#3d5a2a", 2)
    for s in (-1, 1):
        for j in range(6):
            z = 0.1 + j * 0.07
            y = 0.05 + 0.12 * math.sin(min(1.0, z / 0.36) * math.pi / 2)
            p.append(A.extrude_shape(f"leaf{s}{j}", [(0, 0), (0.03, 0.02), (0.05, 0.0), (0.03, -0.012)], depth=0.004,
                                     loc=(0.012 * (1 if j % 2 else -1), y, s * z), rot=(0, s * (30 + 20 * j), 90), color="#6fbf4a"))
            p.append(A.cone(f"thorn{s}{j}", r=0.006, depth=0.025, loc=(0, y + 0.02, s * (z + 0.03)), rot=(-90, 0, 0), color="#c9b68a", seg=6))
        p.append(A.sphere(f"blossom{s}", r=0.022, loc=(0, 0.06, s * 0.56), scale=(1, 1, 0.6), color="#ff8fb8", seg=12, rings=8))
    return W.finalize(p, "bow_thornvine")


def bow_heavens():
    """Divine archer: white-gold limbs that become feathered angel wings, halo above the grip."""
    p = B.bow_base("heavens", 0.62, 0.2, W.GOLD, "#f4f2ea", "#c9a24a", 3)
    for s in (-1, 1):
        for j in range(5):
            z = 0.14 + j * 0.075
            p.append(W.flat_plate(f"feather{s}{j}", [(0.07 + j * 0.02, s * z), (0.15 + j * 0.02, s * (z + 0.02)), (0.24 + j * 0.01, s * (z + 0.09)), (0.14 + j * 0.02, s * (z + 0.06))], 0.016, color=W.WHITE if j % 2 else HOLY, bevel=0.002))
    p.append(A.torus("halo", R=0.06, r=0.007, loc=(0, 0.02, 0.0), rot=(0, 90, 0), color=W.GOLD_HI, mat="M_Emit", seg=28, minor=6))
    p.append(W.star("grip_star", 0.04, 0.018, 0.016, points=8, loc=(0, -0.031, 0), color=W.GOLD))
    return W.finalize(p, "bow_heavens")


def bow_nightfall():
    """Shadow stalker: compact black recurve with curved blades on both tips and a violet moon at the grip."""
    p = B.bow_base("nightfall", 0.5, 0.17, "#4a4458", "#1d1a26", "#2b2236", 2)
    for s in (-1, 1):
        path = W.curve_pts([(0, 0.06, s * 0.48), (0, 0.13, s * 0.53), (0, 0.17, s * 0.62), (0, 0.13, s * 0.7)], 20)
        p.append(W.sweep(f"tip_blade{s}", path, lambda t: 0.018 * (1 - 0.95 * t), lambda t: 0.004, color="#cfd4e0", up=(1, 0, 0)))
        p.append(W.sweep(f"grip_blade{s}", W.curve_pts([(0, -0.02, s * 0.08), (0, -0.07, s * 0.14), (0, -0.09, s * 0.22)], 14), lambda t: 0.014 * (1 - 0.95 * t), lambda t: 0.004, color="#cfd4e0", up=(1, 0, 0)))
    moon = [(math.cos(math.radians(a)) * 0.045, math.sin(math.radians(a)) * 0.045) for a in range(-120, 121, 15)]
    moon += [(math.cos(math.radians(a)) * 0.03 + 0.016, math.sin(math.radians(a)) * 0.03) for a in range(100, -101, -20)]
    p.append(W.flat_plate("moon", [(y, z) for y, z in moon], 0.012, x=0.0, color="#b88aff"))
    return W.finalize(p, "bow_nightfall")


# ------------------------------------------------------------------ T5-T7 maces

def mace_requiem():
    """T5 (crypt): iron bell head with a skull knocker, ghost-light lantern slits."""
    p = R.shaft_parts(0.44, W.IRON, "#3d3f4a", "#24242c", staff=False)
    p.append(A.lathe("bell", [(0.02, 0.45), (0.05, 0.47), (0.065, 0.53), (0.085, 0.6), (0.095, 0.63), (0.0, 0.64)], color="#4a4f5c", seg=20))
    for i in range(6):
        a = i * math.pi / 3
        p.append(A.box(f"slit{i}", (0.012, 0.012, 0.05), loc=(0.07 * math.cos(a), 0.07 * math.sin(a), 0.55), rot=(0, 0, math.degrees(a)), color=GHOST, mat="M_Emit"))
    p.append(A.sphere("skull", r=0.035, loc=(0, 0, 0.67), color=BONE, seg=14, rings=10))
    for s in (-1, 1):
        p.append(A.sphere(f"socket{s}", r=0.008, loc=(s * 0.012, -0.03, 0.675), color=GHOST, mat="M_Emit", seg=8, rings=6))
    p.append(A.torus("rim", R=0.093, r=0.008, loc=(0, 0, 0.625), color=W.IRON_DK, seg=24, minor=6))
    return W.finalize(p, "mace_requiem")


def mace_pearl():
    """T6 (sunken temple): an open scallop shell head holding a large glowing pearl."""
    p = R.shaft_parts(0.45, "#d8c27a", "#e6f2f2", "#2a6f7c", staff=False)
    for i in range(7):
        a = math.radians(-60 + i * 20)
        rib = W.flat_plate_xz(f"scallop{i}", [(0.0, 0.0), (0.03, 0.03), (0.04, 0.13), (0.0, 0.16), (-0.04, 0.13), (-0.03, 0.03)], 0.012, y=0.03, color="#f6d6c8" if i % 2 else "#ffbfae")
        rib.rotation_euler = (0, a, 0)
        rib.location = (0, 0.0, 0.47)
        A.apply_transform(rib)
        p.append(rib)
    p.append(A.sphere("pearl", r=0.055, loc=(0, -0.03, 0.56), color="#f6fbff", mat="M_Emit", seg=20, rings=12))
    p.append(A.torus("clasp", R=0.06, r=0.008, loc=(0, -0.0, 0.47), color="#d8c27a", seg=24, minor=6))
    return W.finalize(p, "mace_pearl")


def mace_judgment():
    """T7 (abyss): heavy black-gold warhammer, one face a blunt block and the other a spike, scale emblem."""
    p = R.shaft_parts(0.46, W.GOLD, "#2a2430", "#4a1e28", staff=False)
    p.append(A.box("head", (0.2, 0.08, 0.09), loc=(0, 0, 0.53), color="#2b2632", bevel=0.01))
    p.append(A.box("face", (0.03, 0.1, 0.11), loc=(0.11, 0, 0.53), color=W.GOLD, bevel=0.008))
    p.append(A.cone("spike", r=0.04, depth=0.11, loc=(-0.15, 0, 0.53), rot=(0, -90, 0), color="#6c6478", seg=8))
    p.append(A.box("emblem_bar", (0.08, 0.01, 0.008), loc=(0, -0.045, 0.56), color=W.GOLD_HI, bevel=0.002))
    p.append(A.box("emblem_post", (0.008, 0.01, 0.05), loc=(0, -0.045, 0.54), color=W.GOLD_HI, bevel=0.002))
    for s in (-1, 1):
        p.append(A.lathe(f"pan{s}", [(0.0, 0.0), (0.016, 0.004), (0.02, 0.012)], loc=(s * 0.035, -0.05, 0.515), rot=(90, 0, 0), color=W.GOLD_HI, seg=12))
    p.append(W.crystal("top", 0.03, 0.09, loc=(0, 0, 0.58), color=VOID_GLOW))
    return W.finalize(p, "mace_judgment")


# ------------------------------------------------------------------ job maces

def mace_grace():
    """Priest: slim white rod with a blooming lily of gold petals around a light crystal."""
    p = R.shaft_parts(0.5, W.GOLD, W.WHITE, "#7a9ac8", staff=False)
    for i in range(6):
        a = i * math.pi / 3
        petal = W.flat_plate_xz(f"petal{i}", [(0.0, 0.0), (0.04, 0.06), (0.05, 0.13), (0.02, 0.18), (0.0, 0.16)], 0.008, y=0.0, color=W.WHITE if i % 2 else HOLY)
        petal.rotation_euler = (math.radians(-18), 0, a)
        petal.location = (0, 0, 0.5)
        A.apply_transform(petal)
        p.append(petal)
    p.append(W.crystal("light", 0.028, 0.12, loc=(0, 0, 0.56), color="#fff6c8"))
    p.append(A.torus("halo", R=0.07, r=0.005, loc=(0, 0.0, 0.7), color=W.GOLD_HI, seg=28, minor=6))
    return W.finalize(p, "mace_grace")


def mace_purifier():
    """Exorcist: spiked iron morning-star bound with paper talismans and a sacred rope."""
    p = R.shaft_parts(0.44, W.IRON, "#5a3a2a", "#2a1a14", staff=False)
    p.append(A.sphere("ball", r=0.07, loc=(0, 0, 0.53), color="#505664", seg=18, rings=12))
    for i in range(14):
        th = math.acos(1 - 2 * (i + 0.5) / 14)
        ph = i * math.pi * (3 - math.sqrt(5))
        d = (math.sin(th) * math.cos(ph), math.sin(th) * math.sin(ph), math.cos(th))
        rot = (math.degrees(math.acos(d[2])), 0, math.degrees(math.atan2(d[1], d[0])) + 90)
        p.append(A.cone(f"spike{i}", r=0.016, depth=0.05, loc=(d[0] * 0.08, d[1] * 0.08, 0.53 + d[2] * 0.08), rot=(rot[0], 0, rot[2]), color="#c8ccd6", seg=6))
    p.append(A.torus("rope", R=0.074, r=0.009, loc=(0, 0, 0.53), color="#e8d8a8", seg=28, minor=8))
    for i in range(4):
        a = i * math.pi / 2 + 0.4
        tag = W.flat_plate_xz(f"talisman{i}", [(-0.016, 0.0), (0.016, 0.0), (0.016, -0.08), (-0.016, -0.08)], 0.002, y=0.0, color="#f4ead0")
        tag.rotation_euler = (0, 0, a)
        tag.location = (0.08 * math.cos(a), 0.08 * math.sin(a), 0.52)
        A.apply_transform(tag)
        p.append(tag)
        mark = W.flat_plate_xz(f"seal{i}", [(-0.008, -0.02), (0.008, -0.02), (0.008, -0.05), (-0.008, -0.05)], 0.003, y=0.0, color="#d0202a")
        mark.rotation_euler = (0, 0, a)
        mark.location = (0.08 * math.cos(a), 0.08 * math.sin(a), 0.52)
        A.apply_transform(mark)
        p.append(mark)
    return W.finalize(p, "mace_purifier")


def mace_seraph():
    """Saint: six stacked seraph wings around a radiant core, double halo."""
    p = R.shaft_parts(0.5, W.GOLD_HI, W.WHITE, "#d0a050", staff=False)
    p.append(W.crystal("core", 0.06, 0.2, loc=(0, 0, 0.56), color="#fff8de"))
    for s in (-1, 1):
        R.wing(p, s, 0.5, W.WHITE, 3)
        R.wing(p, s, 0.6, W.GOLD, 2)
    p.append(A.torus("halo_a", R=0.12, r=0.008, loc=(0, 0.03, 0.66), rot=(90, 0, 0), color=W.GOLD, seg=36, minor=8))
    p.append(A.torus("halo_b", R=0.085, r=0.006, loc=(0, 0.03, 0.66), rot=(90, 0, 0), color=HOLY, mat="M_Emit", seg=32, minor=6))
    p += W.rays("ray", 10, 0.13, 0.17, 0.012, 0.012, z=0.66, y=0.035, color=W.GOLD_HI)
    return W.finalize(p, "mace_seraph")


def mace_verdict():
    """Inquisitor: a great gavel hammer with iron bands, chained tome and red seal."""
    p = R.shaft_parts(0.48, W.IRON, "#3a2a22", "#5a1a1a", staff=False)
    p.append(A.cyl("hammer", r=0.065, depth=0.24, loc=(0, 0, 0.55), rot=(0, 90, 0), color="#5a3a2a", seg=20))
    for x in (-0.1, -0.04, 0.04, 0.1):
        p.append(A.cyl(f"band{x}", r=0.07, depth=0.016, loc=(x, 0, 0.55), rot=(0, 90, 0), color=W.IRON_DK, seg=20))
    for s in (-1, 1):
        p.append(A.cyl(f"face{s}", r=0.07, depth=0.012, loc=(s * 0.124, 0, 0.55), rot=(0, 90, 0), color=W.GOLD, seg=20))
    p.append(A.box("tome", (0.06, 0.02, 0.08), loc=(0, -0.08, 0.46), color="#6a1a20", bevel=0.004))
    p.append(A.cyl("seal", r=0.016, depth=0.006, loc=(0, -0.092, 0.46), rot=(90, 0, 0), color="#d0202a", seg=12))
    p.append(A.tube("chain", [(0, -0.06, 0.5), (0, -0.075, 0.49)], radius=0.003, color=W.IRON, seg=6))
    return W.finalize(p, "mace_verdict")


BUILDERS = [
    ("sword_runic", sword_runic), ("sword_tidal", sword_tidal), ("sword_void", sword_void),
    ("staff_bone", staff_bone), ("staff_coral", staff_coral), ("staff_void", staff_void),
    ("bow_wraith", bow_wraith), ("bow_tide", bow_tide), ("bow_void", bow_void),
    ("mace_requiem", mace_requiem), ("mace_pearl", mace_pearl), ("mace_judgment", mace_judgment),
    ("sword_aegis", sword_aegis), ("sword_ravager", sword_ravager), ("sword_holy_avenger", sword_holy_avenger), ("sword_conqueror", sword_conqueror),
    ("staff_prism", staff_prism), ("staff_hex", staff_hex), ("staff_arcanum", staff_arcanum), ("staff_abyss_eye", staff_abyss_eye),
    ("bow_longshot", bow_longshot), ("bow_thornvine", bow_thornvine), ("bow_heavens", bow_heavens), ("bow_nightfall", bow_nightfall),
    ("mace_grace", mace_grace), ("mace_purifier", mace_purifier), ("mace_seraph", mace_seraph), ("mace_verdict", mace_verdict),
]
