"""Swords T1-T5: sword_bronze, sword_iron, sword_knight, sword_flamberge, sword_dawn.
Origin = grip centre, blade along +Z, edge faces -Y (blade flat lies in the YZ plane, thickness along X).
Run: blender -b --factory-startup -P Blender/weapons/swords.py
"""
import math
import os
import sys

sys.path.append(os.path.dirname(os.path.abspath(__file__)))
import _common as W  # noqa: E402

A = W.A

SAPPHIRE = "#3f8cff"
RUBY = "#ff2a3a"
SUN_CORE = "#ffb43c"
SUN_GLOW = "#ffd27a"


def edge_hone(o, color):
    """Lighter colour on the bevelled cutting edges (faces whose normal points mostly along Y)."""
    return W.paint_faces(o, lambda c, n: abs(n.x) < 0.9 and abs(n.z) < 0.9, color)


def thick_fn(prof):
    """Half-thickness of a blade profile as a function of z (linear interpolation)."""
    rows = [(r[0], r[2]) for r in prof]

    def f(z):
        if z <= rows[0][0]:
            return rows[0][1]
        for (z0, t0), (z1, t1) in zip(rows, rows[1:]):
            if z <= z1:
                return t0 + (t1 - t0) * (z - z0) / max(z1 - z0, 1e-6)
        return rows[-1][1]
    return f


def inlay(name, pts_yz, side, surf, depth=0.003, lift=0.0, color="#555", mat="M_Toon"):
    """Plate on a blade flat that follows the blade's taper: inner face sunk 0.5 mm, outer face proud."""
    o = W.flat_plate(name, pts_yz, depth, x=0.0, color=color, mat=mat)

    def f(v):
        v.x = side * (surf(v.z) - 0.0005 + lift + (v.x + depth / 2))
        return v
    A.deform(o, f)
    return o


def strip(z0, z1, w, yfn=None, n=16, point=True):
    """Polygon (y, z) for a centred strip from z0 to z1 with half width w (pointed top)."""
    left, right = [], []
    for i in range(n + 1):
        z = z0 + (z1 - z0) * i / n
        yo = yfn(z) if yfn else 0.0
        ww = w if (i < n or not point) else 0.0
        left.append((yo - ww, z))
        right.append((yo + ww, z))
    return left + list(reversed(right[:-1] if point else right))


def side_gems(name, r, z, x, color, y=0.0):
    return [W.gem(name + "_l", r, loc=(x, y, z), rot=(0, 90, 0), color=color),
            W.gem(name + "_r", r, loc=(-x, y, z), rot=(0, -90, 0), color=color)]


def turn_yz(objs):
    """Objects built in the XZ plane (front-facing) -> rotate into the blade's YZ plane."""
    for o in objs:
        o.rotation_euler = (0, 0, math.radians(90))
        A.apply_transform(o)
    return objs


# ---------------------------------------------------------------- T1 bronze
def sword_bronze():
    P = []
    prof = [(0.07, 0.036, 0.010), (0.12, 0.040, 0.010), (0.30, 0.044, 0.0095), (0.47, 0.051, 0.009),
            (0.56, 0.046, 0.008), (0.63, 0.026, 0.006), (0.68, 0.0, 0.003)]
    surf = thick_fn(prof)
    b = W.blade("blade", prof, color=W.BRONZE, edge_frac=0.55)
    edge_hone(b, W.BRONZE_HI)
    P.append(b)
    for s in (1, -1):  # raised midrib, darker bronze
        P.append(inlay(f"rib{s}", strip(0.085, 0.57, 0.0065), s, surf, depth=0.003, color="#a4672c"))
    # guard: rounded bar with ball ends
    P.append(A.cyl("guard", r=0.016, depth=0.15, loc=(0, 0, 0.058), rot=(90, 0, 0), color=W.BRONZE, seg=14))
    P.append(A.box("guard_c", (0.036, 0.046, 0.036), loc=(0, 0, 0.058), color=W.BRONZE, bevel=0.007))
    for s in (1, -1):
        P.append(A.sphere(f"gend{s}", r=0.021, loc=(0, s * 0.078, 0.058), color=W.BRONZE_HI, seg=14, rings=8))
    P += side_gems("gem", 0.012, 0.058, 0.019, "#4aa8ff")
    P += W.wrap_grip("grip", -0.07, 0.04, 0.0165, turns=5)
    P.append(A.cyl("ferrule", r=0.02, depth=0.012, loc=(0, 0, -0.072), color=W.BRONZE, seg=14))
    P.append(A.sphere("pommel", r=0.028, loc=(0, 0, -0.097), scale=(1, 1, 0.8), color=W.BRONZE, seg=20, rings=12))
    return W.finalize(P, "sword_bronze")


# ---------------------------------------------------------------- T2 iron
def sword_iron():
    P = []
    prof = [(0.075, 0.040, 0.010), (0.15, 0.041, 0.0095), (0.56, 0.038, 0.008), (0.68, 0.031, 0.0065),
            (0.76, 0.0, 0.003)]
    surf = thick_fn(prof)
    b = W.blade("blade", prof, color=W.STEEL, edge_frac=0.62)
    edge_hone(b, "#e6edf5")
    P.append(b)
    for s in (1, -1):  # dark fuller
        P.append(inlay(f"fuller{s}", strip(0.1, 0.6, 0.009), s, surf, depth=0.0025, color=W.STEEL_DK))
    # guard: iron bar, ends angled toward the blade
    pts = [(-0.1, 0.088), (-0.088, 0.072), (-0.022, 0.048), (0.022, 0.048), (0.088, 0.072), (0.1, 0.088),
           (0.094, 0.098), (0.022, 0.076), (-0.022, 0.076), (-0.094, 0.098)]
    P.append(W.flat_plate("guard", pts, 0.036, color=W.IRON, bevel=0.005))
    P.append(A.box("guard_c", (0.044, 0.054, 0.044), loc=(0, 0, 0.062), color=W.IRON_DK, bevel=0.007))
    for s in (1, -1):
        P.append(A.sphere(f"rivet{s}", r=0.008, loc=(s * 0.022, 0, 0.062), scale=(0.6, 1, 1), color=W.IRON, seg=10, rings=6))
    P += W.wrap_grip("grip", -0.075, 0.04, 0.0165, turns=6, color="#3d2a1e", band="#5e4030")
    P.append(A.cyl("ferrule", r=0.0205, depth=0.014, loc=(0, 0, -0.078), color=W.IRON, seg=14))
    # wheel pommel
    P.append(A.cyl("pommel", r=0.033, depth=0.024, loc=(0, 0, -0.105), rot=(0, 90, 0), color=W.IRON, seg=22))
    for s in (1, -1):
        P.append(A.cyl(f"pboss{s}", r=0.017, depth=0.008, loc=(s * 0.014, 0, -0.105), rot=(0, 90, 0), color="#9aa2ad", seg=14))
    return W.finalize(P, "sword_iron")


# ---------------------------------------------------------------- T3 knight
def sword_knight():
    P = []
    prof = [(0.085, 0.042, 0.0105), (0.17, 0.042, 0.010), (0.62, 0.038, 0.0085), (0.74, 0.031, 0.007),
            (0.83, 0.0, 0.003)]
    surf = thick_fn(prof)
    b = W.blade("blade", prof, color=W.SILVER, edge_frac=0.62)
    edge_hone(b, "#ffffff")
    P.append(b)
    for s in (1, -1):
        P.append(inlay(f"fgold{s}", strip(0.165, 0.66, 0.0125), s, surf, depth=0.0022, color=W.GOLD))
        P.append(inlay(f"fuller{s}", strip(0.172, 0.65, 0.0085), s, surf, depth=0.0022, lift=0.0012, color="#2c4f9e"))
        # knight crest: gold shield with blue field and gold cross on the ricasso
        sh = [(-0.024, 0.14), (-0.024, 0.11), (-0.013, 0.096), (0.0, 0.089), (0.013, 0.096), (0.024, 0.11), (0.024, 0.14)]
        P.append(inlay(f"crest{s}", sh, s, surf, depth=0.003, color=W.GOLD))
        inner = [(y * 0.74, 0.115 + (z - 0.115) * 0.74) for (y, z) in sh]
        P.append(inlay(f"crestb{s}", inner, s, surf, depth=0.002, lift=0.0018, color="#2c4f9e"))
        P.append(inlay(f"crossv{s}", [(-0.0032, 0.131), (0.0032, 0.131), (0.0032, 0.1), (-0.0032, 0.1)], s, surf, depth=0.0015, lift=0.003, color=W.GOLD_HI))
        P.append(inlay(f"crossh{s}", [(-0.012, 0.121), (0.012, 0.121), (0.012, 0.1145), (-0.012, 0.1145)], s, surf, depth=0.0015, lift=0.003, color=W.GOLD_HI))
    # ornate gold guard: swept quillons curling toward the blade
    for s in (1, -1):
        path = W.curve_pts([(0, s * 0.02, 0.065), (0, s * 0.06, 0.07), (0, s * 0.097, 0.086), (0, s * 0.112, 0.11), (0, s * 0.1, 0.126)], 22)
        P.append(W.sweep(f"quil{s}", path, lambda t: 0.016 * (1 - 0.45 * t), lambda t: 0.016 * (1 - 0.4 * t), color=W.GOLD, up=(1, 0, 0)))
        P.append(A.sphere(f"qball{s}", r=0.013, loc=(0, s * 0.099, 0.128), color=W.GOLD_HI, seg=12, rings=8))
    dia = [(0.0, 0.036), (0.034, 0.068), (0.0, 0.1), (-0.034, 0.068)]
    P.append(W.flat_plate("guard_c", dia, 0.034, color=W.GOLD, bevel=0.005))
    P += side_gems("gem", 0.015, 0.068, 0.018, SAPPHIRE)
    P += W.wrap_grip("grip", -0.08, 0.045, 0.0165, turns=6, color="#243c78", band="#162650")
    P.append(W.helix("gwire", -0.075, 0.04, 0.0178, 3, radius=0.0024, color=W.GOLD, phase=1.0))
    P.append(W.band("fer_top", 0.045, 0.021, 0.014, color=W.GOLD))
    P.append(W.band("fer_bot", -0.082, 0.021, 0.014, color=W.GOLD))
    P.append(A.lathe("pommel", [(0.0, -0.132), (0.012, -0.13), (0.025, -0.116), (0.028, -0.101), (0.019, -0.089), (0.013, -0.087), (0.0, -0.087)], color=W.GOLD, seg=20))
    P += side_gems("pgem", 0.012, -0.107, 0.024, SAPPHIRE)
    return W.finalize(P, "sword_knight")


# ---------------------------------------------------------------- T4 flamberge
def sword_flamberge():
    P = []
    amp, k = 0.0055, 2 * math.pi / 0.085

    def wave(z):
        return amp * math.sin((z - 0.17) * k) * min(1.0, (z - 0.15) / 0.05) if z > 0.15 else 0.0

    prof = []
    z = 0.085
    while z < 0.80:
        prof.append((z, 0.043 - 0.006 * (z - 0.085) / 0.7, 0.0105 - 0.003 * (z - 0.085) / 0.7, wave(z)))
        z += 0.0085
    prof += [(0.83, 0.028, 0.006, wave(0.83)), (0.875, 0.015, 0.0045, wave(0.875)), (0.91, 0.0, 0.003, wave(0.91))]
    surf = thick_fn(prof)
    b = W.blade("blade", prof, color="#3a3d48", edge_frac=0.55, smooth_angle=20)
    edge_hone(b, "#dfe6ef")
    P.append(b)
    for s in (1, -1):
        # crimson channel following the wave, glowing ember runes along it
        P.append(inlay(f"chan{s}", strip(0.16, 0.77, 0.0105, yfn=wave, n=70), s, surf, depth=0.0022, color="#9c1a1c"))
        zz, i = 0.2, 0
        while zz < 0.74:
            yo = wave(zz)
            h = 0.026 if i % 2 == 0 else 0.016
            rune = [(yo, zz - h / 2), (yo + 0.0065, zz), (yo, zz + h / 2), (yo - 0.0065, zz)]
            P.append(inlay(f"rune{s}_{i}", rune, s, surf, depth=0.0018, lift=0.0014, color="#ff6a1f", mat="M_Emit"))
            zz += 0.06
            i += 1
    # ricasso wrap
    P.append(A.cyl("ricasso", r=0.021, depth=0.05, loc=(0, 0, 0.12), scale=(0.62, 1.55, 1), color="#5a1e1e", seg=14))
    P.append(A.cyl("ric_b", r=0.022, depth=0.009, loc=(0, 0, 0.148), scale=(0.68, 1.62, 1), color=W.GOLD, seg=14))
    # flame guard: swept black quillons with gold trim, small down-curling lower prongs
    for s in (1, -1):
        path = W.curve_pts([(0, s * 0.015, 0.07), (0, s * 0.06, 0.06), (0, s * 0.102, 0.076), (0, s * 0.128, 0.112), (0, s * 0.114, 0.155)], 26)
        P.append(W.sweep(f"quil{s}", path, lambda t: 0.019 * (1 - 0.85 * t), lambda t: 0.015 * (1 - 0.6 * t), color="#2a1a1a", up=(1, 0, 0)))
        P.append(W.sweep(f"qtrim{s}", path[:-4], lambda t: 0.0055 * (1 - 0.5 * t), lambda t: 0.0175 * (1 - 0.6 * t), color=W.GOLD, up=(1, 0, 0)))
        path2 = W.curve_pts([(0, s * 0.02, 0.07), (0, s * 0.052, 0.05), (0, s * 0.075, 0.03), (0, s * 0.082, 0.01)], 16)
        P.append(W.sweep(f"quil2{s}", path2, lambda t: 0.012 * (1 - 0.85 * t), lambda t: 0.011 * (1 - 0.5 * t), color=W.GOLD, up=(1, 0, 0)))
    flame_c = [(0.0, 0.033), (0.034, 0.06), (0.026, 0.087), (0.013, 0.079), (0.0, 0.108), (-0.013, 0.079), (-0.026, 0.087), (-0.034, 0.06)]
    P.append(W.flat_plate("guard_c", flame_c, 0.036, color=W.GOLD, bevel=0.004))
    P += side_gems("ruby", 0.017, 0.065, 0.019, RUBY)
    P += W.wrap_grip("grip", -0.085, 0.045, 0.0165, turns=7, color="#7a1c1c", band="#2a1414")
    P.append(W.band("fer_top", 0.045, 0.021, 0.014, color=W.GOLD))
    P.append(W.band("fer_bot", -0.087, 0.021, 0.014, color=W.GOLD))
    # flame pommel: teardrop with a ruby tip
    P.append(A.lathe("pommel", [(0.0, -0.15), (0.008, -0.14), (0.023, -0.12), (0.026, -0.105), (0.017, -0.093), (0.0, -0.09)], color="#2a1a1a", seg=16))
    P.append(W.band("pband", -0.112, 0.0265, 0.009, color=W.GOLD))
    P.append(W.gem("pgem", 0.013, loc=(0, 0, -0.152), rot=(180, 0, 0), color=RUBY))
    return W.finalize(P, "sword_flamberge")


# ---------------------------------------------------------------- T5 dawn (sunrise motif)
def sword_dawn():
    P = []
    prof = [(0.11, 0.043, 0.0105), (0.2, 0.045, 0.010), (0.55, 0.048, 0.009), (0.68, 0.054, 0.0085),
            (0.77, 0.046, 0.0075), (0.85, 0.025, 0.0055), (0.91, 0.0, 0.003)]
    surf = thick_fn(prof)
    b = W.blade("blade", prof, color="#f2f4fb", edge_frac=0.62)
    A.gradient(b, "#ffe2b0", "#f4f6ff")
    edge_hone(b, "#ffffff")
    P.append(b)

    def beam(scale, z0=0.16):  # sunbeam widening toward the tip
        return [(-0.006 * scale, z0), (-0.018 * scale, 0.62), (-0.022 * scale, 0.71), (0.0, 0.80),
                (0.022 * scale, 0.71), (0.018 * scale, 0.62), (0.006 * scale, z0)]
    for s in (1, -1):
        P.append(inlay(f"bgold{s}", beam(1.4), s, surf, depth=0.0022, color=W.GOLD))
        P.append(inlay(f"bcore{s}", [(y, max(z, 0.175)) for (y, z) in beam(0.95, 0.175)], s, surf, depth=0.0018, lift=0.0014, color=SUN_GLOW, mat="M_Emit"))
    # sunrise guard: half sun disc on a horizon bar, long rays fanning out as quillons
    P.append(W.sweep("horizon", W.curve_pts([(0, -0.085, 0.078), (0, -0.04, 0.066), (0, 0.04, 0.066), (0, 0.085, 0.078)], 20),
                     lambda t: 0.012, lambda t: 0.02, color=W.GOLD_DK, up=(1, 0, 0)))
    disc = [(math.cos(math.radians(a)) * 0.06, 0.072 + math.sin(math.radians(a)) * 0.06) for a in range(0, 181, 10)]
    P.append(W.flat_plate("disc", disc, 0.032, color=W.GOLD, bevel=0.004))
    disc_in = [(math.cos(math.radians(a)) * 0.043, 0.077 + math.sin(math.radians(a)) * 0.043) for a in range(0, 181, 10)]
    for s in (1, -1):
        P.append(W.flat_plate(f"disc_in{s}", disc_in, 0.004, x=s * 0.0165, color="#ffe9b0"))
    P += turn_yz(W.rays("ray", 11, 0.055, 0.15, 0.012, 0.022, arc=(0, 180), z=0.072, color=W.GOLD_HI, alt=0.1))
    P += side_gems("sun", 0.022, 0.098, 0.018, SUN_CORE)
    P += W.wrap_grip("grip", -0.085, 0.06, 0.0165, turns=6, color="#f4efe4", band="#d8cbb0")
    P.append(W.helix("gwire", -0.08, 0.055, 0.0178, 3, radius=0.0025, color=W.GOLD, phase=0.5))
    P.append(W.band("fer_top", 0.058, 0.0215, 0.015, color=W.GOLD))
    P.append(W.band("fer_bot", -0.088, 0.0215, 0.015, color=W.GOLD))
    # pommel: small sun
    P.append(A.sphere("pommel", r=0.026, loc=(0, 0, -0.117), scale=(0.8, 1, 1), color=W.GOLD, seg=18, rings=10))
    P += turn_yz(W.rays("pray", 8, 0.022, 0.044, 0.009, 0.014, arc=(0, 360), z=-0.117, color=W.GOLD_HI))
    P += side_gems("pgem", 0.014, -0.117, 0.018, SUN_CORE)
    return W.finalize(P, "sword_dawn")


BUILDERS = [("sword_bronze", sword_bronze), ("sword_iron", sword_iron), ("sword_knight", sword_knight),
            ("sword_flamberge", sword_flamberge), ("sword_dawn", sword_dawn)]


def main():
    A.reset_scene()
    items = [(wid, fn()) for wid, fn in BUILDERS]
    W.export_items(items, "Weapons")
    W.preview_items(items, "weapon_", {"_side": (90, 0, 90), "_34": (70, 0, 55)}, size=640)
    W.contact_sheet(items, "weapon_sheet_swords", spacing=0.3, axis=(0, 1, 0), angle=(90, 0, 90), size=1280)
    A.save_blend("weapons_swords")


if __name__ == "__main__":
    main()
