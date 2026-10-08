"""Chapter 5 — 가라앉은 신전 (sunken temple) monsters, sculpted kit (monster v4).
Run through the production runner: python Blender/enemies_a/generate_all.py -- --only puffer
"""
import math
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from kit_v4 import (Sculpt, BossSculpt, A, lerp_col, vgrad, rgba, hexmix, fibo, spine, ellipsoid_point, teeth, blade,  # noqa: E402,F401
                    lathe_helm, paint_where, paint_fn, dome, scale_region,
                    attack_env, cast_env, die_env, window, bump, ramp, soft, DIE_HOLD)
from mathutils import Vector  # noqa: E402

TAU = math.tau


def fish_fin(c, bone, name, root, tips, color, edge, k=0.3, thick=0.007):
    """Fan fin: rays from `root` to each tip, with a soft notch between rays (membrane)."""
    root = Vector(root)
    edge_pts = [tuple(tips[0])]
    for a, b in zip(tips, tips[1:]):
        a, b = Vector(a), Vector(b)
        m = (a + b) / 2
        edge_pts += [tuple(m + (root - m) * k), tuple(b)]
    return c.membrane(bone, name, tuple(root), edge_pts, color, thick=thick, edge_color=edge)


def fan(center, radius, a0, a1, n, plane='xz', lift=0.0):
    """n+1 points on an arc (degrees a0..a1) in a plane through center; plane 'xz' (front fins), 'yz' (dorsal/tail)."""
    c = Vector(center)
    out = []
    for i in range(n + 1):
        a = math.radians(a0 + (a1 - a0) * i / n)
        if plane == 'xz':
            out.append(c + Vector((math.cos(a) * radius, lift, math.sin(a) * radius)))
        elif plane == 'yz':
            out.append(c + Vector((lift, math.cos(a) * radius, math.sin(a) * radius)))
        else:
            out.append(c + Vector((math.cos(a) * radius, math.sin(a) * radius, lift)))
    return out


def damp_body_scale(a, f, P, k=0.35, bone='body'):
    """Hard-shelled bodies keep most of their shape: scale the kit's squash back toward 1."""
    a.s(bone, f, tuple(1 + (s - 1) * k for s in P.bs))


# ---------------------------------------------------------------------------------------------- puffer
def puffer(eid):
    """복어 풍선 — an inflated pufferfish drifting in the air: round sandy body with brown saddle spots on the back,
    a cream belly, a coat of short spines, big glossy eyes under soft worried brows, a pouting coral mouth and
    fluttering orange fins."""
    c = Sculpt(eid, tris=7000, ao=0.5)
    sand, brown, cream = '#efc75e', '#8a5a2e', '#fff3d6'

    def hide(p):
        z = (p.z - 0.62) / 0.26
        spot = (math.sin(p.x * 30) * math.sin(p.y * 27 + 1.3) * math.sin(p.z * 24 + 0.4) > 0.3 and p.z > 0.8
                and p.y > -0.12)
        base = lerp_col(cream, sand, (z + 0.05) / 0.35)
        return lerp_col(base, brown, 0.7) if spot else base
    C, R = (0, 0, 0.78), (0.28, 0.27, 0.25)
    c.bone('body', C); c.bone('eyes', (0, -0.21, 0.86), 'body'); c.bone('tail1', (0, 0.26, 0.78), 'body')
    c.blob('body', C, R, hide)
    c.blob('body', (0, -0.08, 0.7), (0.2, 0.18, 0.15), cream, weight=1.2)
    c.limb('tail1', [(0, 0.2, 0.78), (0, 0.3, 0.79), (0, 0.36, 0.8)], [0.13, 0.075, 0.05], lambda p: lerp_col(sand, cream, (0.78 - p.z) / 0.06))
    for s in (-1, 1):
        c.blob('eyes', (s * 0.125, -0.205, 0.94), (0.05, 0.03, 0.014), sand, rot=(0, s * 14, 0), weight=0.9)  # soft brow
        c.eye('eyes', (s * 0.118, -0.215, 0.865), (s * 0.45, -1, 0.08), 0.064, '#2b3a58')
        c.paint((s * 0.175, -0.215, 0.79), (0.04, 0.02, 0.025), '#f4a184')                         # cheek blush
    for s in (-1, 1):  # pouting lips
        c.blob('body', (s * 0.03, -0.27, 0.735), (0.035, 0.03, 0.03), '#f2876a', weight=1.5)
    c.blob('body', (0, -0.275, 0.755), (0.04, 0.028, 0.02), '#f2876a', weight=1.5)
    c.blob('body', (0, -0.275, 0.715), (0.04, 0.028, 0.02), '#f2876a', weight=1.5)
    c.paint((0, -0.305, 0.736), (0.02, 0.03, 0.016), '#5a1f22', weight=1.8)
    k = 0
    for d in fibo(150, 0.4):
        if d.y < -0.5 and d.z > -0.55 and abs(d.x) < 0.8:      # keep the face clear
            continue
        if d.y > 0.85:                                          # and the tail root
            continue
        p, n = ellipsoid_point(C, R, d, -0.008)
        L = 0.055 + 0.02 * (0.5 + 0.5 * math.sin(k * 2.3))
        spine(c, 'body', f'spine{k}', p, n + Vector((0, 0.3, 0.1)), L, 0.012, '#f6e3b0', tip='#6b4424', seg=5)
        k += 1
    for s, side in ((-1, 'R'), (1, 'L')):
        c.bone('wing.' + side, (s * 0.25, -0.04, 0.74), 'body')
        root = (s * 0.255, -0.02, 0.74)
        tips = [Vector(root) + Vector((s * 0.17 * math.cos(math.radians(a)), 0.07 + 0.035 * i, 0.15 * math.sin(math.radians(a))))
                for i, a in enumerate((55, 25, -5, -35, -60))]
        fish_fin(c, 'wing.' + side, 'fin' + side, root, tips, '#f39a3e', '#ffd88a', k=0.2)
    tail = [Vector((0, 0.34, 0.8)) + Vector((0, 0.2 * math.cos(math.radians(a)), 0.2 * math.sin(math.radians(a))))
            for a in (70, 40, 12, -12, -40, -70)]
    fish_fin(c, 'tail1', 'tail_fin', (0, 0.33, 0.8), tail, '#f39a3e', '#ffd88a', k=0.4)
    fish_fin(c, 'body', 'dorsal', (0, 0.17, 0.96), [(0, 0.13, 1.03), (0, 0.2, 1.08), (0, 0.28, 1.02)], '#f39a3e', '#ffd88a')
    return c.finish('float')


# ---------------------------------------------------------------------------------------------- merfolk_guard
def merfolk_guard(eid):
    """어인 수비병 — a fish-headed temple soldier: wide-mouthed carp head with side-set eyes, spiny gill fins and a
    dorsal crest, teal scales over a pale belly, webbed feet, a coral-tipped spear and a scallop-shell shield."""
    c = Sculpt(eid, tris=10000)
    teal, deep, belly_c, fin = '#2f86a6', '#1d5677', '#e8efd6', '#ff8f6b'

    def scales(p):
        if p.y < -0.05 and 0.42 < p.z < 0.8 and abs(p.x) < 0.12:
            return belly_c if math.sin(p.z * 70) > -0.6 else lerp_col(belly_c, '#b8cdb4', 0.6)
        stripe = math.sin(p.z * 40 + math.sin(p.x * 20)) > 0.75
        base = lerp_col(deep, teal, (p.z - 0.2) / 0.6)
        return lerp_col(base, '#5fc0d0', 0.35) if stripe else base
    c.bone('body', (0, 0, 0.5)); c.bone('head', (0, -0.02, 0.8), 'body'); c.bone('eyes', (0, -0.12, 0.98), 'head')
    c.bone('jaw', (0, -0.1, 0.86), 'head'); c.bone('crest', (0, 0.04, 1.06), 'head')
    c.blob('body', (0, 0.0, 0.62), (0.17, 0.12, 0.17), scales)
    c.blob('body', (0, -0.01, 0.46), (0.13, 0.1, 0.1), scales)
    for s in (-1, 1):
        c.blob('body', (s * 0.14, 0.0, 0.71), (0.075, 0.08, 0.07), teal)
    # carp head: a deep, forward-reaching skull with a broad underslung mouth
    c.limb('head', [(0, -0.01, 0.76), (0, -0.03, 0.84)], [0.085, 0.09], scales)
    c.blob('head', (0, -0.06, 0.95), (0.125, 0.14, 0.12), lambda p: lerp_col(teal, deep, (p.z - 0.92) / 0.1))
    c.limb('head', [(0, -0.12, 0.95), (0, -0.2, 0.93), (0, -0.25, 0.91)], [0.1, 0.085, 0.06], teal)
    c.limb('jaw', [(0, -0.09, 0.86), (0, -0.18, 0.855), (0, -0.25, 0.865)], [0.085, 0.075, 0.05], belly_c)
    c.blob('jaw', (0, -0.27, 0.875), (0.055, 0.02, 0.02), '#f0b39a')                               # lower lip
    c.blob('head', (0, -0.29, 0.905), (0.06, 0.025, 0.022), '#f0b39a')                             # upper lip
    c.paint((0, -0.3, 0.89), (0.05, 0.03, 0.01), '#4a1d26', weight=1.5)
    for s in (-1, 1):
        c.blob('eyes', (s * 0.085, -0.13, 1.01), (0.04, 0.045, 0.02), deep, rot=(0, s * 25, 0))   # brow ridge
        c.eye('eyes', (s * 0.1, -0.14, 0.975), (s * 0.85, -0.55, 0.1), 0.032, '#ffcf3a')
        c.paint((s * 0.115, -0.04, 0.9), (0.01, 0.05, 0.05), '#163e58')                               # gill slit
        root = (s * 0.11, -0.01, 0.92)
        tips = [(s * 0.2, 0.05, 1.0), (s * 0.24, 0.07, 0.93), (s * 0.23, 0.08, 0.86), (s * 0.17, 0.05, 0.82)]
        fish_fin(c, 'head', f'gill_fin{s}', root, tips, fin, '#ffd2a0')
    crest = [(0, -0.1, 1.07), (0, -0.04, 1.17), (0, 0.02, 1.12), (0, 0.06, 1.15), (0, 0.1, 1.06), (0, 0.13, 1.04),
             (0, 0.14, 0.92), (0, 0.11, 0.78)]
    c.membrane('crest', 'crest', (0, 0.02, 0.95), crest, fin, thick=0.012, edge_color='#ffd2a0')
    # kit: shell pauldron, rope belt, kelp skirt
    c.ring('body', 'belt', (0, 0, 0.47), 0.135, 0.022, '#7a5a3a', scale=(1, 0.88, 1))
    for k in range(7):
        a = math.radians(200 + k * 23)
        c.tuft('body', (0.13 * math.cos(a), 0.11 * math.sin(a), 0.46), (0.25 * math.cos(a), 0.25 * math.sin(a), -1), 0.17, 0.03,
               '#3f8a4a' if k % 2 else '#56a35a')
    for s, side in ((-1, 'R'), (1, 'L')):
        c.bone('arm.' + side, (s * 0.15, -0.01, 0.7), 'body')
        c.limb('arm.' + side, [(s * 0.15, -0.01, 0.7), (s * 0.22, -0.04, 0.58), (s * 0.24, -0.1, 0.48)], [0.05, 0.04, 0.035], teal)
        c.blob('arm.' + side, (s * 0.245, -0.12, 0.46), (0.042, 0.04, 0.042), teal)
        fish_fin(c, 'arm.' + side, f'arm_fin{side}', (s * 0.225, 0.0, 0.58), [(s * 0.27, 0.06, 0.62), (s * 0.29, 0.07, 0.56),
                                                                              (s * 0.27, 0.05, 0.5)], fin, '#ffd2a0')
        c.bone('leg.' + side, (s * 0.09, 0, 0.42), 'body')
        c.blob('leg.' + side, (s * 0.1, 0.0, 0.34), (0.075, 0.085, 0.1), scales)
        c.limb('leg.' + side, [(s * 0.1, 0.02, 0.25), (s * 0.11, 0.04, 0.13), (s * 0.11, -0.02, 0.05)], [0.05, 0.04, 0.036], teal)
        c.blob('leg.' + side, (s * 0.11, -0.08, 0.025), (0.06, 0.1, 0.022), deep)                    # webbed foot
        for j in range(3):
            c.blob('leg.' + side, (s * 0.11 + (j - 1) * 0.035, -0.17, 0.02), (0.02, 0.035, 0.016), deep)
    c.disc('arm.R', 'pauldron', (-0.17, 0.0, 0.76), (-0.6, 0, 1), (0.1, 0.03, 0.09), '#f0c9a8', seg=16, rings=8)
    for k in range(5):
        c.tube('arm.R', f'pauldron_rib{k}', [(-0.12 - k * 0.005, -0.06 + k * 0.03, 0.8), (-0.21, -0.07 + k * 0.035, 0.74)], 0.01,
               '#d9937a')
    # coral spear in the right hand, scallop shield on the left
    c.bone('weapon.R', (-0.25, -0.12, 0.46), 'arm.R')
    c.tube('weapon.R', 'spear_shaft', [(-0.25, -0.12, 0.12), (-0.25, -0.12, 1.2)], 0.016, '#d9c7a0')
    for k, z in enumerate((0.42, 0.5)):
        c.ring('weapon.R', f'spear_wrap{k}', (-0.25, -0.12, z), 0.02, 0.007, '#6a4a30')
    spine(c, 'weapon.R', 'spear_tip', (-0.25, -0.12, 1.18), (0, 0, 1), 0.2, 0.035, '#f2f0e6', tip='#ffffff', seg=8)
    for k, (dx, dz, L) in enumerate(((0.07, 0.05, 0.09), (-0.07, 0.08, 0.08), (0.05, -0.04, 0.07), (-0.05, -0.02, 0.06))):
        base = Vector((-0.25, -0.12, 1.14 + dz * 0.3))
        c.tube('weapon.R', f'coral{k}', [tuple(base), tuple(base + Vector((dx * 0.6, 0, L * 0.6))), tuple(base + Vector((dx, 0, L)))],
               0.012, '#ff6b5e', taper=0.5)
    c.bone('weapon.L', (0.25, -0.12, 0.46), 'arm.L')
    c.add('weapon.L', scallop('shell_shield', (0.29, -0.17, 0.33), 0.2, 0.32, 0.07, '#e98f7a', '#fde6cf', yaw=-12))
    c.orb('weapon.L', 'shield_boss', (0.29, -0.245, 0.4), (0.035, 0.02, 0.035), '#ffd65a', seg=12, rings=6)
    c.follow['crest'] = 1.2
    return c.finish('biped')


# ---------------------------------------------------------------------------------------------- angler
def angler(eid):
    """초롱아귀 — a deep-sea anglerfish hanging in the dark: a huge lumpy head with a gaping underbite full of crooked
    needle teeth, small pale eyes under heavy brows, a row of glowing spots along its flanks, ragged fins, and a
    glowing lure dangling from a rod over its mouth."""
    c = Sculpt(eid, tris=8500, ao=0.55)
    dark, mid, pale = '#45385e', '#76649a', '#d9c3b9'

    def skin(p):
        base = lerp_col(pale, lerp_col(mid, dark, (p.z - 0.86) / 0.14), (p.z - 0.7) / 0.1)
        return base
    c.bone('body', (0, 0.02, 0.8)); c.bone('eyes', (0, -0.2, 0.97), 'body'); c.bone('jaw', (0, 0.0, 0.74), 'body')
    c.bone('tail1', (0, 0.25, 0.8), 'body'); c.bone('tail2', (0, 0.42, 0.82), 'tail1')
    c.blob('body', (0, -0.04, 0.86), (0.25, 0.26, 0.19), skin)
    for s in (-1, 1):
        c.blob('body', (s * 0.17, -0.12, 0.79), (0.11, 0.13, 0.11), skin)
        c.blob('eyes', (s * 0.11, -0.2, 1.0), (0.06, 0.05, 0.035), dark)                         # heavy brow
        c.eye('eyes', (s * 0.115, -0.235, 0.965), (s * 0.5, -1, 0.25), 0.032, '#e8f0e6', iris_edge=0.8)
    for k, (x, y) in enumerate(((0.1, 0.02), (-0.12, 0.06), (0.03, 0.12), (0.16, 0.1), (-0.05, -0.04))):
        c.blob('body', (x, y, 1.03), (0.05, 0.05, 0.03), dark)                                   # warty crown
    c.blob('body', (0, 0.14, 0.81), (0.19, 0.18, 0.16), skin)
    c.limb(['tail1', 'tail2'], [(0, 0.25, 0.8), (0, 0.38, 0.81), (0, 0.48, 0.82)], [0.13, 0.08, 0.05], skin)
    # underbite jaw jutting past the upper lip, mouth carved open
    c.blob('jaw', (0, -0.15, 0.69), (0.24, 0.19, 0.085), lambda p: lerp_col(pale, mid, (p.z - 0.64) / 0.1))
    c.blob('jaw', (0, -0.31, 0.715), (0.18, 0.06, 0.06), mid)
    c.blob('body', (0, -0.31, 0.79), (0.18, 0.13, 0.04), '#000000', negative=True)
    c.paint((0, -0.26, 0.775), (0.18, 0.12, 0.055), '#3a0f24', weight=1.8)
    up = [Vector((0.17 * math.sin(a), -0.22 - 0.09 * math.cos(a), 0.81)) for a in [math.radians(x) for x in range(-75, 76, 15)]]
    lo = [Vector((0.16 * math.sin(a), -0.24 - 0.11 * math.cos(a), 0.75)) for a in [math.radians(x) for x in range(-66, 67, 22)]]
    for k, p in enumerate(up):
        spine(c, 'body', f'fang_up{k}', p, (0.15 * math.sin(k * 2.1), -0.3, -1), 0.045 + 0.02 * (k % 2), 0.011, '#efe6d4',
              tip='#ffffff', seg=6)
    for k, p in enumerate(lo):
        spine(c, 'jaw', f'fang_lo{k}', p, (0.2 * math.sin(k * 1.7), -0.55, 1), 0.08 + 0.03 * (k % 2), 0.013, '#efe6d4',
              tip='#ffffff', seg=6)
    for s in (-1, 1):  # bioluminescent spots along the flanks
        for k in range(6):
            c.paint((s * (0.2 - 0.012 * k), -0.12 + 0.07 * k, 0.86 - 0.012 * k), (0.018, 0.018, 0.018), '#8ff2ff', weight=2.0)
    # lure rod with a glowing bulb
    c.bone('antenna.L', (0, -0.12, 1.03), 'body')
    c.tube('antenna.L', 'lure_rod', bezier((0, -0.1, 1.02), (0, -0.2, 1.36), (0, -0.44, 1.14), 10), 0.014, mid, taper=0.55)
    c.add('antenna.L', A.sphere('lure', r=0.05, loc=(0, -0.445, 1.09), scale=(1, 1, 1.15), color='#e6fff6', mat='M_Emit',
                                seg=16, rings=10))
    c.add('antenna.L', A.sphere('lure_halo', r=0.07, loc=(0, -0.445, 1.09), scale=(1, 1, 1.1), color='#7fe6d0', mat='M_Clear',
                                seg=16, rings=10))
    for s, side in ((-1, 'R'), (1, 'L')):
        c.bone('wing.' + side, (s * 0.24, 0.04, 0.76), 'body')
        root = (s * 0.24, 0.05, 0.76)
        tips = [Vector(root) + Vector((s * (0.16 - 0.015 * i), 0.03 + 0.04 * i, 0.1 - 0.07 * i)) for i in range(5)]
        fish_fin(c, 'wing.' + side, 'pec' + side, root, tips, '#8a72a8', '#e0cff0', k=0.35)
    dorsal = [(0, 0.0, 1.07), (0, 0.06, 1.12), (0, 0.12, 1.1), (0, 0.18, 1.08), (0, 0.24, 1.0), (0, 0.3, 0.93)]
    fish_fin(c, 'body', 'dorsal', (0, 0.15, 0.94), dorsal, '#5a4a78', '#b8a6d6', k=0.45)
    tail = [Vector((0, 0.47, 0.82)) + Vector((0, 0.2 * math.cos(math.radians(a)), 0.18 * math.sin(math.radians(a))))
            for a in (65, 35, 5, -25, -55)]
    fish_fin(c, 'tail2', 'tail_fin', (0, 0.46, 0.82), tail, '#5a4a78', '#b8a6d6', k=0.4)
    c.follow['antenna'] = 1.0
    return c.finish('float')


# ---------------------------------------------------------------------------------------------- giant_clam
def shell_mesh(name, W, L, D, hinge, sign, ribs=9, zig=0.035, color_hinge='#8a7a8f', color_rim='#f4eee2', thick=0.03,
               band='#e79ab4', res=(48, 14)):
    """Fluted bivalve half-shell: ribs radiate from the hinge to a zig-zag rim. sign=+1 upper (dome up), -1 lower.
    res: (around, outward) grid size; small ornamental shells use a coarser grid."""
    import bmesh
    H = Vector(hinge)
    bm = bmesh.new()
    NA, NS = res
    grid = []
    for i in range(NA + 1):
        a = -math.pi / 2 * 0.98 + math.pi * 0.98 * i / NA
        row = []
        for j in range(NS + 1):
            s = j / NS
            rim = H + Vector((W * math.sin(a), -L * math.cos(a) ** 0.8, 0))
            p = H.lerp(rim, s)
            dome = D * math.sin(math.pi * min(1.0, s * 0.92 + 0.08)) ** 0.7 * (0.35 + 0.65 * math.cos(a) ** 0.5)
            rib = 0.5 + 0.5 * math.cos(ribs * 2 * a)
            dome += 0.03 * s * rib * (W / 0.5)
            z = sign * dome + zig * s ** 3 * math.sin(ribs * 2 * a) * (W / 0.5)
            row.append(bm.verts.new((p.x, p.y, H.z + z)))
        grid.append(row)
    for i in range(NA):
        for j in range(NS):
            v = (grid[i][j], grid[i + 1][j], grid[i + 1][j + 1], grid[i][j + 1])
            bm.faces.new(v if sign > 0 else v[::-1])
    bmesh.ops.remove_doubles(bm, verts=bm.verts, dist=1e-5)
    me = bpy_mesh(name, bm)
    o = A._new_obj(name, me)
    md = o.modifiers.new('solid', 'SOLIDIFY')
    md.thickness = thick
    md.offset = -1
    A.apply_modifiers(o)
    A.shade_smooth(o)
    A.paint(o, color_rim)
    attr = o.data.color_attributes['Col']
    for loop in o.data.loops:
        v = o.data.vertices[loop.vertex_index].co
        d = (Vector((v.x, v.y, H.z)) - H).length / L
        a = math.atan2(v.x, -(v.y - H.y))
        rib = 0.5 + 0.5 * math.cos(ribs * 2 * a)
        col = lerp_col(color_hinge, color_rim, d ** 0.7)
        col = lerp_col(col, band, 0.55 * max(0.0, math.sin(d * 21)) ** 2 * min(1.0, d * 2))
        col = lerp_col(col, '#ffffff', 0.12 * rib * d)
        attr.data[loop.index].color_srgb = col
    return o


def scallop(name, base, W, L, D, hinge_col, rim_col, yaw=0.0, ribs=7):
    """Upright scallop shell (shield, crown ornaments): hinge at `base`, fan opening upward, dome facing -Y."""
    from mathutils import Matrix
    res = (ribs * 6, 5) if W < 0.12 else (ribs * 6, 9)
    o = shell_mesh(name, W, L, D, (0, 0, 0), 1, ribs=ribs, zig=0.0, color_hinge=hinge_col, color_rim=rim_col, thick=0.02, res=res)
    o.data.transform(Matrix.Rotation(math.radians(180), 4, 'Y') @ Matrix.Rotation(math.radians(90), 4, 'X'))
    o.data.transform(Matrix.Rotation(math.radians(yaw), 4, 'Z'))
    o.location = Vector(base)
    return o


def bpy_mesh(name, bm):
    import bpy
    me = bpy.data.meshes.new(name)
    bm.to_mesh(me)
    bm.free()
    return me


def giant_clam(eid):
    """거대 조개 — a huge fluted clam: zig-zag shells banded lilac and cream, crusted with barnacles and weed, a frilled
    blue mantle with two peeping stalk eyes, a lolling pink tongue and the big pearl it guards. It hops and snaps."""
    from mathutils import Matrix
    c = Sculpt(eid, tris=6500, ao=0.5)
    hinge = Vector((0, 0.36, 0.3))
    c.bone('body', (0, 0.0, 0.2)); c.bone('lid', tuple(hinge), 'body'); c.bone('eyes', (0, -0.22, 0.46), 'body')
    c.bone('tentacle1', (0, -0.32, 0.29), 'body')
    c.add('body', shell_mesh('shell_low', 0.5, 0.8, 0.27, hinge, -1, color_hinge='#6a3f9a', color_rim='#fff0dc'))
    up = shell_mesh('shell_up', 0.5, 0.8, 0.3, hinge, 1, color_hinge='#6a3f9a', color_rim='#fff0dc')
    up.data.transform(Matrix.Translation(hinge) @ Matrix.Rotation(math.radians(-22), 4, 'X') @ Matrix.Translation(-hinge))
    c.add('lid', up)

    def mantle(p):
        spot = math.sin(p.x * 60) * math.sin(p.y * 55) > 0.6
        return '#a8f0ff' if spot else lerp_col('#2b6fc8', '#6a3ab8', 0.5 + 0.5 * math.sin(p.x * 9))
    for k in range(13):  # frilled mantle lip following the rim, inside the shells
        a = math.radians(-78 + 156 * k / 12)
        p = (0.4 * math.sin(a), 0.36 - 0.66 * math.cos(a) ** 0.8, 0.32 + 0.015 * math.sin(k * 2.2))
        c.blob('body', p, (0.075, 0.075, 0.05), mantle)
    c.blob('body', (0, 0.02, 0.3), (0.3, 0.42, 0.08), mantle)
    for s in (-1, 1):  # stalk eyes peeping over the lower shell
        c.limb('eyes', [(s * 0.13, -0.18, 0.33), (s * 0.14, -0.22, 0.42)], [0.04, 0.035], mantle)
        c.blob('eyes', (s * 0.14, -0.225, 0.46), (0.055, 0.05, 0.05), '#3b5fc0')
        c.eye('eyes', (s * 0.14, -0.255, 0.465), (s * 0.3, -1, 0.1), 0.042, '#ffb43a')
        c.blob('eyes', (s * 0.14, -0.25, 0.505), (0.05, 0.035, 0.016), '#2b4fa8')
    c.limb('tentacle1', [(0, -0.28, 0.3), (0, -0.42, 0.31), (0, -0.54, 0.24), (0, -0.59, 0.14)], [0.07, 0.08, 0.075, 0.055],
           lambda p: lerp_col('#ff9db0', '#e0607e', (0.3 - p.z) / 0.16))
    c.paint((0, -0.45, 0.37), (0.014, 0.1, 0.03), '#c94a6a')
    pearl = A.sphere('pearl', r=0.1, loc=(0.0, -0.06, 0.43), color='#fff6f4', seg=24, rings=14)
    attr = pearl.data.color_attributes['Col']
    for loop in pearl.data.loops:
        v = pearl.data.vertices[loop.vertex_index].co
        attr.data[loop.index].color_srgb = lerp_col('#ffc9e3', '#f6fbff', 0.5 + 0.5 * v.z / 0.1)
    c.add('body', pearl)
    rot = Matrix.Translation(hinge) @ Matrix.Rotation(math.radians(-22), 4, 'X') @ Matrix.Translation(-hinge)
    for k, (x, y, r) in enumerate(((0.2, 0.05, 0.04), (-0.15, -0.05, 0.035), (0.05, 0.12, 0.03), (-0.26, 0.15, 0.03),
                                   (0.28, -0.12, 0.028))):
        p = rot @ Vector((x, y, 0.3 + 0.27 * (1 - (x / 0.5) ** 2) ** 0.5 * (1 - abs(y) * 0.6)))
        b = A.cyl(f'barnacle{k}', r=r, depth=r * 1.1, loc=tuple(p), r2=r * 0.55, color='#e2dccd', seg=8)
        c.add('lid', b)
        c.add('lid', A.cyl(f'barnacle_hole{k}', r=r * 0.45, depth=r * 0.2, loc=tuple(p + Vector((0, 0, r * 0.5))), color='#5a4a4a', seg=8))
    for k in range(4):
        p = rot @ Vector((-0.08 + 0.05 * k, 0.24, 0.55))
        c.tube('lid', f'weed{k}', [tuple(p), tuple(p + Vector((0.02 * k - 0.03, 0.05, 0.1))), tuple(p + Vector((0.04 * k - 0.06, 0.12, 0.17)))],
               0.014, '#4fa35a', taper=0.35)

    def extra(a, clip, f, t, i, names):
        damp_body_scale(a, f, a.P, 0.3)
        if clip == 'Die':
            limp = die_env(t)[4]
            a.r('lid', f, (-45 * limp, 0, 0))
            a.r('tentacle1', f, (40 * limp, 0, 0))
    return c.finish('hop', extra)


# ---------------------------------------------------------------------------------------------- sea_urchin
def sea_urchin(eid):
    """성게 — a round violet urchin waddling on two tiny feet: dense two-tone spines all over, little bumps between
    them, a clear face with big shiny eyes, rosy cheeks and a small smile."""
    c = Sculpt(eid, tris=6000, ao=0.5)
    vio, deep = '#7040a8', '#3a1f5e'
    C, R = (0, 0, 0.34), (0.25, 0.24, 0.23)
    c.bone('body', C); c.bone('eyes', (0, -0.22, 0.38), 'body')

    def shell(p):
        bump_ = math.sin(math.atan2(p.y, p.x) * 14) * math.sin(p.z * 60) > 0.7
        base = lerp_col(deep, vio, (p.z - 0.15) / 0.35)
        return lerp_col(base, '#b58ae0', 0.5) if bump_ else base
    c.blob('body', C, R, shell)
    c.blob('body', (0, -0.12, 0.33), (0.17, 0.14, 0.15), '#8f62c0')
    for s in (-1, 1):
        c.blob('eyes', (s * 0.09, -0.2, 0.45), (0.045, 0.03, 0.012), '#5a3088', rot=(0, s * -12, 0), weight=0.9)
        c.eye('eyes', (s * 0.088, -0.215, 0.385), (s * 0.35, -1, 0.05), 0.058, '#3a2a58')
        c.paint((s * 0.155, -0.19, 0.31), (0.035, 0.02, 0.022), '#ec8cc0')
    c.paint((0, -0.245, 0.305), (0.03, 0.015, 0.01), '#2a1030', weight=1.6)
    k = 0
    for d in fibo(170, 0.9):
        if d.y < -0.38 and -0.6 < d.z < 0.72 and abs(d.x) < 0.8:
            continue
        if d.z < -0.62:
            continue
        p, n = ellipsoid_point(C, R, d, -0.015)
        L = (0.13 + 0.07 * (0.5 + 0.5 * math.sin(k * 1.9))) if k % 3 else 0.08
        spine(c, 'body', f'spine{k}', p, n, L, 0.017 if k % 3 else 0.012, '#5a2f88', tip='#ffb3e6', seg=5)
        k += 1
    for s, side in ((-1, 'R'), (1, 'L')):
        c.bone('leg.' + side, (s * 0.09, -0.02, 0.14), 'body')
        c.limb('leg.' + side, [(s * 0.09, -0.02, 0.15), (s * 0.1, -0.04, 0.06)], [0.04, 0.035], '#f2b04a')
        c.blob('leg.' + side, (s * 0.1, -0.08, 0.03), (0.055, 0.075, 0.03), '#f2b04a')
    return c.finish('hop')


def bezier(p0, p1, p2, n=8):
    p0, p1, p2 = Vector(p0), Vector(p1), Vector(p2)
    return [tuple(p0 * (1 - t) ** 2 + p1 * 2 * t * (1 - t) + p2 * t * t) for t in (i / n for i in range(n + 1))]


def anime_head(c, hb, eb, C, k, skin, iris, brow, lips='#c8607a', blush=None, glint=True):
    """Stylised humanoid head on bones hb/eb centred at C (scale k ~ 1 for a 0.24 m head): cranium, cheeks and a
    small chin flowing into one surface, a hint of a nose, eyes set in sockets under lid/brow masses, painted lips."""
    x0, y0, z0 = C
    c.blob(hb, (x0, y0 + 0.005 * k, z0 + 0.012 * k), (0.1 * k, 0.105 * k, 0.108 * k), skin)
    c.blob(hb, (x0, y0 - 0.03 * k, z0 - 0.045 * k), (0.078 * k, 0.078 * k, 0.07 * k), skin)
    c.blob(hb, (x0, y0 - 0.06 * k, z0 - 0.095 * k), (0.034 * k, 0.034 * k, 0.03 * k), skin)
    c.blob(hb, (x0, y0 - 0.1 * k, z0 - 0.03 * k), (0.011 * k, 0.014 * k, 0.018 * k), skin)
    for s in (-1, 1):
        c.eye(eb, (x0 + s * 0.043 * k, y0 - 0.078 * k, z0 - 0.012 * k), (s * 0.2, -1, 0.0), 0.033 * k, iris, glint=glint)
        c.blob(eb, (x0 + s * 0.044 * k, y0 - 0.083 * k, z0 + 0.024 * k), (0.035 * k, 0.018 * k, 0.009 * k), skin)   # upper lid
        c.paint((x0 + s * 0.047 * k, y0 - 0.1 * k, z0 + 0.019 * k), (0.034 * k, 0.02 * k, 0.0045 * k), '#2a1a28',
                rot=(0, s * 6, 0), weight=1.6)                                                                     # lash line
        c.paint((x0 + s * 0.047 * k, y0 - 0.1 * k, z0 + 0.055 * k), (0.024 * k, 0.015 * k, 0.0045 * k), brow,
                rot=(0, s * 8, 0), weight=1.4)
        if blush:
            c.paint((x0 + s * 0.06 * k, y0 - 0.085 * k, z0 - 0.04 * k), (0.02 * k, 0.012 * k, 0.012 * k), blush)
    c.paint((x0, y0 - 0.096 * k, z0 - 0.072 * k), (0.017 * k, 0.012 * k, 0.006 * k), lips, weight=1.5)


def stone_col(base, dark, moss=None, seed=0.0):
    from mathutils import noise

    def f(p):
        n = noise.noise(p * 9 + Vector((seed, seed * 2, 0)))
        col = lerp_col(base, dark, 0.5 + 0.6 * n)
        if moss and noise.noise(p * 5 + Vector((3.1, seed, 1.7))) > 0.25:
            col = lerp_col(col, moss, 0.75)
        return col
    return f


def temple_guardian(eid):
    """신전 수호상 — a sunken temple's stone warrior come to life: a broad carved torso, a crested Corinthian helm with
    a dark T-slit and rune-lit eyes, faceted stone armour crusted with barnacles and shells, moss on every upward
    surface, hanging kelp and a verdigris bronze halberd."""
    c = Sculpt(eid, tris=7500, ao=0.6)
    c.post = moss_post('#5f8f48', 0.4, 2.0)
    stone = stone_col('#a7aea4', '#7b847d', None, 1.0)
    plate = '#c2c4b6'
    c.bone('body', (0, 0, 0.55)); c.bone('head', (0, -0.02, 0.98), 'body')
    c.blob('body', (0, 0, 0.85), (0.25, 0.16, 0.15), stone)
    c.blob('body', (0, -0.02, 0.68), (0.16, 0.12, 0.12), stone)
    c.blob('body', (0, 0.0, 0.52), (0.18, 0.13, 0.08), stone)
    c.blob('body', (0, -0.11, 0.86), (0.2, 0.06, 0.11), plate)                                       # pectoral plate
    c.paint((0, -0.165, 0.87), (0.006, 0.03, 0.09), '#6b726c', weight=1.4)
    c.blob('head', (0, -0.02, 1.0), (0.07, 0.07, 0.07), stone)                                      # neck
    c.blob('head', (0, -0.03, 1.08), (0.1, 0.1, 0.1), stone)
    helm = lathe_helm(c, 'head', 'helm', (0, -0.03, 1.1), 0.125, 0.27, plate,
                      profile=[(0.1, -0.135), (0.125, -0.07), (0.128, 0.02), (0.118, 0.08), (0.09, 0.12), (0.04, 0.14), (0, 0.143)],
                      scale=(1, 1.08, 1))
    paint_where(helm, lambda v: v.y < -0.08 and ((abs(v.x) < 0.085 and abs(v.z - 1.105) < 0.017) or
                                                 (abs(v.x) < 0.017 and 0.99 < v.z < 1.105)), '#151a19')
    for s in (-1, 1):
        c.add('head', A.sphere(f'rune_eye{s}', r=0.016, loc=(s * 0.045, -0.163, 1.105), scale=(1.5, 0.4, 0.6), color='#7ff5e0',
                               mat='M_Emit', seg=10, rings=6))
    crest = []
    for i in range(9):
        a = math.radians(-15 + 150 * i / 8)
        crest.append((-0.17 * math.cos(a) * 1.05, 1.1 + 0.2 * math.sin(a)))
    for i in range(8, -1, -1):
        a = math.radians(-15 + 150 * i / 8)
        crest.append((-0.13 * math.cos(a), 1.1 + 0.135 * math.sin(a)))
    cr = A.extrude_shape('helm_crest', [(y, z) for y, z in crest], depth=0.04, color='#8a6a5a')
    cr.rotation_euler = (0, 0, math.radians(90))
    cr.location = (0, -0.03, 0)
    A.apply_transform(cr)
    c.add('head', cr)
    c.add('head', A.sphere('chest_rune', r=0.032, loc=(0, -0.172, 0.8), scale=(1, 0.4, 1), color='#7ff5e0', mat='M_Emit', seg=12, rings=6))
    c.ring('body', 'belt', (0, -0.01, 0.56), 0.165, 0.025, plate, scale=(1, 0.8, 1))
    for k in range(5):
        a = math.radians(-60 + k * 30)
        c.chunk('body', f'skirt{k}', (0.17 * math.sin(a), -0.12 * math.cos(a), 0.43), (0.055, 0.025, 0.09), plate, seed=10 + k, jitter=0.06)
    for s, side in ((-1, 'R'), (1, 'L')):
        c.bone('arm.' + side, (s * 0.24, 0, 0.88), 'body')
        c.limb('arm.' + side, [(s * 0.25, 0, 0.88), (s * 0.31, -0.03, 0.72), (s * 0.33, -0.08, 0.58)], [0.08, 0.065, 0.062], stone)
        c.blob('arm.' + side, (s * 0.335, -0.1, 0.52), (0.065, 0.065, 0.065), stone)
        for j in range(3):
            c.add('arm.' + side, dome(f'pauldron{side}{j}', (s * (0.28 + 0.02 * j), 0.0, 0.95 - 0.045 * j), (0.12 - 0.01 * j, 0.12, 0.075),
                                      color=plate))
        c.blob('arm.' + side, (s * 0.335, -0.06, 0.62), (0.07, 0.075, 0.05), plate)                     # vambrace
        c.bone('leg.' + side, (s * 0.11, 0, 0.45), 'body')
        c.limb('leg.' + side, [(s * 0.11, 0, 0.45), (s * 0.12, -0.01, 0.24), (s * 0.12, 0, 0.09)], [0.085, 0.075, 0.07], stone)
        c.blob('leg.' + side, (s * 0.12, -0.05, 0.2), (0.07, 0.05, 0.1), plate)                         # greave
        c.chunk('leg.' + side, 'boot' + side, (s * 0.12, -0.04, 0.05), (0.085, 0.12, 0.055), plate, seed=30 + s, jitter=0.05)
    for k, (b, p, r) in enumerate((('body', (0.14, -0.13, 0.7), 0.03), ('body', (-0.18, -0.08, 0.95), 0.028), ('arm.L', (0.33, -0.05, 0.99), 0.03),
                                   ('arm.R', (-0.3, -0.07, 0.98), 0.025), ('leg.L', (0.16, -0.07, 0.27), 0.025), ('head', (0.08, -0.07, 1.2), 0.022),
                                   ('body', (-0.08, 0.14, 0.8), 0.03))):
        c.add(b, A.cyl(f'barnacle{k}', r=r, depth=r, loc=p, r2=r * 0.5, color='#e3ddcf', seg=8))
    c.add('arm.L', scallop('shell_a', (0.25, -0.1, 0.96), 0.06, 0.09, 0.02, '#e98f7a', '#fde6cf', yaw=20, ribs=5))
    c.add('body', scallop('shell_b', (-0.1, -0.16, 0.6), 0.05, 0.07, 0.015, '#d98fb0', '#fde6cf', yaw=-10, ribs=5))
    for k, (root, d) in enumerate((((-0.3, 0.04, 0.9), (-0.2, 0.2, -1)), ((0.3, 0.05, 0.88), (0.15, 0.3, -1)),
                                   ((0.06, 0.1, 1.22), (0.1, 0.4, -1)), ((-0.12, 0.12, 0.82), (-0.1, 0.4, -1)))):
        b = 'arm.R' if root[0] < -0.2 else 'arm.L' if root[0] > 0.2 else 'head' if root[2] > 1 else 'body'
        c.tube(b, f'kelp{k}', [root, tuple(Vector(root) + Vector(d) * 0.1), tuple(Vector(root) + Vector(d) * 0.22 + Vector((0.02, 0, 0)))],
               0.016, '#3f8a4a', taper=0.3)
    # verdigris bronze halberd
    c.bone('weapon.R', (-0.34, -0.11, 0.52), 'arm.R')
    c.tube('weapon.R', 'halberd_shaft', [(-0.34, -0.11, 0.08), (-0.34, -0.11, 1.42)], 0.022, '#5a6f66')
    br = '#4fa38a'
    axe = A.extrude_shape('halberd_axe', [(0, -0.02), (0.05, -0.05), (0.13, -0.12), (0.19, -0.1), (0.21, 0.02), (0.19, 0.14),
                                          (0.13, 0.16), (0.05, 0.09), (0, 0.06)], depth=0.035, color=br, bevel=0.008)
    paint_where(axe, lambda v: v.x > 0.17, '#a8e8d0')
    axe.rotation_euler = (0, 0, math.radians(90))
    axe.location = (-0.34, -0.11, 1.24)
    c.add('weapon.R', axe)
    hook = A.extrude_shape('halberd_hook', [(0, -0.02), (0.08, 0.0), (0.12, 0.06), (0.07, 0.03), (0, 0.03)], depth=0.025, color=br)
    hook.rotation_euler = (0, 0, math.radians(-90))
    hook.location = (-0.34, -0.11, 1.26)
    c.add('weapon.R', hook)
    spine(c, 'weapon.R', 'halberd_spike', (-0.34, -0.11, 1.4), (0, 0, 1), 0.22, 0.035, br, tip='#a8e8d0', seg=6)
    c.ring('weapon.R', 'halberd_collar', (-0.34, -0.11, 1.22), 0.03, 0.012, '#c9a04a')
    c.arm_limit = (60, 24)
    return c.finish('heavy')


def serpent_die(a, f, t, slump=82.0):
    """Die for floor-coiled serpents: the coil stays put while the raised neck sags and crashes forward."""
    stag, sway, fall, thud, limp = die_env(t)
    a.l('root', f, (0, 0, 0))
    a.r('root', f, (0, 0, 0))
    a.s('body', f, (1, 1, 1))
    a.r('body', f, (slump * fall - 12 * stag, 8 * sway, 10 * fall))
    a.r('head', f, (-10 * stag + 18 * fall, 0, 25 * limp))


def sea_serpent(eid):
    """바다뱀 — a banded sea serpent coiled on the temple floor, its neck reared in an S: a finned dragon-snake head,
    a coral-red fin crest down the neck, cream belly scales and a tail tip curling out of the coil."""
    c = Sculpt(eid, tris=8500, ao=0.55)
    teal, deep, cream, fin = '#2f9a8f', '#1b5f66', '#f2e6bf', '#ff6f5a'

    def scales(p):
        band = math.sin((p.z * 3 + math.atan2(p.y, p.x) * 0.0 + p.y * 2) * 9) > 0.55
        base = deep if band else teal
        return base

    def neck_col(p):
        if p.y < -0.12 - (p.z - 0.3) * 0.15 and abs(p.x) < 0.08:
            return cream
        return deep if math.sin(p.z * 26) > 0.55 else teal
    c.bone('body', (0, -0.1, 0.25)); c.bone('head', (0, -0.18, 0.78), 'body'); c.bone('eyes', (0, -0.36, 1.07), 'head')
    c.bone('jaw', (0, -0.3, 0.98), 'head'); c.bone('crest', (0, -0.15, 1.12), 'head')
    # coil on the floor (root): a spiral of masses
    pts, radii = [], []
    for i in range(22):
        u = i / 21
        a = math.radians(-100 + 400 * u)
        R = 0.34 - 0.14 * u
        pts.append((R * math.cos(a), 0.12 + R * math.sin(a), 0.1 + 0.05 * u + 0.04 * max(0.0, u - 0.8) * 5))
        radii.append(0.1 - 0.02 * u)
    c.limb('root', pts, radii, lambda p: cream if p.z < 0.06 else scales(p), spacing=0.45)
    # neck rising out of the coil
    neck = [(0.05, -0.2, 0.12), (0.0, -0.2, 0.32), (-0.04, -0.12, 0.52), (0.0, -0.1, 0.7), (0.0, -0.2, 0.86), (0, -0.28, 0.96)]
    c.limb(['root', 'body', 'body', 'head', 'head'], neck, [0.1, 0.095, 0.085, 0.08, 0.075, 0.07], neck_col)
    # tail tip out of the coil
    c.bone('tail1', (0.3, 0.3, 0.1)); c.bone('tail2', (0.42, 0.45, 0.14), 'tail1')
    c.limb(['tail1', 'tail2'], [(0.28, 0.25, 0.1), (0.42, 0.42, 0.13), (0.45, 0.6, 0.22)], [0.07, 0.045, 0.015], scales)
    fish_fin(c, 'tail2', 'tail_fin', (0.44, 0.5, 0.17), [(0.42, 0.62, 0.36), (0.47, 0.68, 0.26), (0.5, 0.66, 0.14)], fin, '#ffd2a0')
    # head: a long dragon-snake skull with a heavy brow and a hinged jaw
    c.blob('head', (0, -0.33, 1.02), (0.1, 0.13, 0.08), teal)
    c.limb('head', [(0, -0.4, 1.03), (0, -0.5, 1.01), (0, -0.56, 0.99)], [0.075, 0.06, 0.045], teal)
    c.limb('jaw', [(0, -0.3, 0.96), (0, -0.44, 0.955), (0, -0.54, 0.96)], [0.06, 0.045, 0.03], cream)
    c.paint((0, -0.45, 0.98), (0.07, 0.12, 0.008), '#3a1418', weight=1.6)
    for s in (-1, 1):
        c.blob('eyes', (s * 0.06, -0.38, 1.085), (0.04, 0.05, 0.022), deep, rot=(0, s * 15, 0))
        c.eye('eyes', (s * 0.065, -0.39, 1.055), (s * 0.7, -0.7, 0.1), 0.026, '#ffd23a', slit=True)
        c.paint((s * 0.02, -0.57, 1.01), (0.008, 0.008, 0.006), '#123a3a')
        spine(c, 'jaw', f'fang{s}', (s * 0.035, -0.53, 0.975), (0, -0.2, -1), 0.04, 0.009, '#fff8e8', seg=6)
        c.bone('ear.' + ('L' if s > 0 else 'R'), (s * 0.08, -0.28, 1.05), 'head')
        fish_fin(c, 'ear.' + ('L' if s > 0 else 'R'), f'head_fin{s}', (s * 0.08, -0.27, 1.04),
                 [(s * 0.17, -0.22, 1.14), (s * 0.21, -0.17, 1.07), (s * 0.19, -0.14, 0.99)], fin, '#ffd2a0', k=0.35)
    crest = [(0, -0.42, 1.1), (0, -0.33, 1.2), (0, -0.25, 1.14), (0, -0.2, 1.15), (0, -0.14, 1.03), (0, -0.08, 1.0),
             (0, -0.02, 0.86), (0, 0.04, 0.82), (0, 0.04, 0.66), (0, 0.06, 0.6), (0, 0.04, 0.46)]
    c.membrane('crest', 'crest', (0, -0.16, 0.88), crest, fin, thick=0.01, edge_color='#ffd2a0')

    def extra(a, clip, f, t, i, names):
        if clip == 'Die':
            serpent_die(a, f, t)
        else:
            a.r('root', f, (0, 0, 0))  # the coil never tips over; the neck does the acting
            a.l('root', f, (a.P.rl[0] * 0.3, a.P.rl[1] * 0.3, 0))
    return c.finish('biped', extra)


def drowned_knight(eid):
    """익사한 기사 — a drowned knight risen from the temple moat: rust-streaked steel plate with layered, barnacled
    pauldrons, a bucket great helm whose eye slit glows sea-green, kelp and weed dripping from every joint, a torn
    sea-green cape and a huge iron anchor swung two-handed."""
    c = Sculpt(eid, tris=9000, ao=0.6)
    from mathutils import noise

    def rust(p):
        n = noise.noise(p * 7 + Vector((1.3, 0.2, 0.7)))
        streak = noise.noise(Vector((p.x * 16, p.y * 16, p.z * 2.5))) > 0.3
        col = lerp_col('#a3adb6', '#6d7680', 0.5 + 0.7 * n)
        if streak:
            col = lerp_col(col, '#a0522d', 0.65)
        if noise.noise(p * 4 + Vector((0, 5, 0))) > 0.38:
            col = lerp_col(col, '#5aa088', 0.5)  # verdigris bloom
        return col
    c.post = moss_post('#3f7a4a', 0.55, 4.0, -0.3)
    steel, dark = '#929ca6', '#3a4048'
    c.bone('body', (0, 0, 0.62)); c.bone('head', (0, -0.02, 1.14), 'body'); c.bone('cape', (0, 0.15, 1.08), 'body')
    c.blob('body', (0, 0, 0.96), (0.24, 0.17, 0.19), rust)
    c.blob('body', (0, -0.02, 0.77), (0.17, 0.13, 0.14), rust)
    c.blob('body', (0, 0, 0.6), (0.19, 0.14, 0.09), rust)
    c.blob('body', (0, -0.13, 0.98), (0.18, 0.06, 0.14), rust)                                     # breastplate
    for nm, co, rr in (('cuirass', (0, -0.075, 0.97), (0.215, 0.13, 0.17)), ('fauld', (0, -0.05, 0.74), (0.17, 0.115, 0.075))):
        o = c.orb('body', nm, co, rr, steel, seg=24, rings=12)
        A.apply_transform(o)
        paint_fn(o, lambda p: rust(p) if p.z > 0.79 or p.z < 0.7 else '#3a4048')
    c.paint((0, -0.18, 0.84), (0.2, 0.05, 0.012), '#2a2e33', weight=1.3)
    c.paint((0, -0.16, 0.72), (0.18, 0.05, 0.01), '#2a2e33', weight=1.3)
    c.paint((0, -0.19, 0.99), (0.008, 0.05, 0.13), '#a9b2ba', weight=1.3)                          # keel ridge
    c.blob('head', (0, -0.02, 1.12), (0.08, 0.08, 0.06), dark)
    helm = lathe_helm(c, 'head', 'great_helm', (0, -0.03, 1.27), 0.13, 0.3, steel,
                      profile=[(0.115, -0.15), (0.13, -0.1), (0.133, 0.0), (0.127, 0.06), (0.108, 0.105), (0.075, 0.14), (0.035, 0.162), (0.0, 0.17)])
    for v in helm.data.vertices:  # pinch the face into a keel
        if v.co.y < -0.03:
            v.co.y -= 0.03 * max(0.0, 1 - abs(v.co.x) / 0.1)
    paint_where(helm, lambda v: v.y < -0.1 and abs(v.x) < 0.1 and abs(v.z - 1.29) < 0.014, '#0d1212')
    paint_where(helm, lambda v: v.y < -0.1 and abs(v.x) < 0.007 and 1.17 < v.z < 1.29, '#0d1212')
    paint_where(helm, lambda v: v.y < -0.08 and 0.02 < abs(v.x) < 0.08 and 1.17 < v.z < 1.24 and int(abs(v.x) * 90) % 2 == 0, '#20282a')
    paint_where(helm, lambda v: v.z > 1.36, '#6d7680')
    paint_where(helm, lambda v: v.z < 1.15 or (v.z > 1.33 and abs(v.x) < 0.012), '#a0522d')   # rusted rim and crest ridge
    for s in (-1, 1):
        c.add('head', A.sphere(f'drowned_eye{s}', r=0.016, loc=(s * 0.045, -0.166, 1.29), scale=(1.6, 0.4, 0.55), color='#8affd8',
                               mat='M_Emit', seg=10, rings=6))
    c.ring('head', 'helm_rim', (0, -0.03, 1.13), 0.117, 0.014, '#6b5a50')
    c.cone_to('head', 'helm_spike', (0, -0.03, 1.4), (0, 0.0, 1.5), 0.028, steel)
    for s, side in ((-1, 'R'), (1, 'L')):
        c.bone('arm.' + side, (s * 0.26, 0, 1.0), 'body')
        c.limb('arm.' + side, [(s * 0.27, 0, 1.0), (s * 0.33, -0.03, 0.82), (s * 0.35, -0.08, 0.68)], [0.075, 0.065, 0.06], rust)
        c.blob('arm.' + side, (s * 0.355, -0.1, 0.62), (0.068, 0.068, 0.068), rust)
        c.blob('arm.' + side, (s * 0.33, -0.04, 0.82), (0.06, 0.06, 0.045), steel)                    # couter
        for j in range(3):
            c.add('arm.' + side, dome(f'pauldron{side}{j}', (s * (0.29 + 0.025 * j), 0.0, 1.07 - 0.05 * j),
                                      (0.135 - 0.012 * j, 0.13 - 0.008 * j, 0.08), color=steel if j == 0 else '#6d7680'))
        c.bone('leg.' + side, (s * 0.11, 0, 0.55), 'body')
        c.limb('leg.' + side, [(s * 0.11, 0, 0.55), (s * 0.13, -0.02, 0.32), (s * 0.13, 0, 0.1)], [0.09, 0.078, 0.072], rust)
        c.blob('leg.' + side, (s * 0.13, -0.05, 0.31), (0.06, 0.05, 0.05), steel)                     # knee cop
        c.blob('leg.' + side, (s * 0.13, -0.06, 0.05), (0.08, 0.13, 0.05), rust)
    for k in range(7):
        a = math.radians(-90 + k * 30)
        c.chunk('body', f'tasset{k}', (0.19 * math.sin(a), -0.15 * math.cos(a), 0.52), (0.07, 0.025, 0.08), '#6d7680', seed=k, jitter=0.04)
    c.ring('body', 'sword_belt', (0, -0.005, 0.6), 0.19, 0.02, '#5a3a2a', scale=(1, 0.8, 1))
    tabard = [(-0.11, -0.16, 0.6), (-0.12, -0.17, 0.4), (-0.07, -0.16, 0.3), (-0.03, -0.17, 0.36), (0.02, -0.16, 0.27),
              (0.06, -0.17, 0.34), (0.1, -0.16, 0.29), (0.12, -0.17, 0.42), (0.11, -0.16, 0.6)]
    tb = c.membrane('body', 'tabard', (0, -0.17, 0.62), tabard, '#2f7a72', thick=0.01, edge_color='#1a3f3c')
    paint_where(tb, lambda v: abs(v.x) < 0.035 and 0.42 < v.z < 0.56, '#c9a04a')
    paint_where(tb, lambda v: abs(v.x) < 0.075 and 0.475 < v.z < 0.505, '#c9a04a')
    for k, (b, p, r) in enumerate((('arm.L', (0.36, -0.07, 1.1), 0.03), ('arm.L', (0.24, 0.08, 1.12), 0.025), ('arm.R', (-0.38, 0.0, 1.07), 0.03),
                                   ('body', (0.12, -0.18, 0.9), 0.025), ('head', (-0.08, -0.08, 1.38), 0.022), ('leg.R', (-0.19, -0.05, 0.3), 0.025))):
        c.add(b, A.cyl(f'barnacle{k}', r=r, depth=r, loc=p, r2=r * 0.5, color='#e3ddcf', seg=8))
    kelp = (('arm.L', (0.33, 0.02, 0.98), (0.1, 0.1, -1), 0.32), ('arm.R', (-0.34, 0.04, 0.98), (-0.05, 0.2, -1), 0.28),
            ('head', (0.11, 0.02, 1.36), (0.4, 0.1, -1), 0.3), ('head', (-0.12, 0.0, 1.33), (-0.3, 0.2, -1), 0.24),
            ('body', (0.15, -0.13, 0.6), (0.1, -0.1, -1), 0.3), ('body', (-0.08, -0.16, 0.58), (-0.05, -0.1, -1), 0.26),
            ('arm.L', (0.37, -0.1, 0.66), (0.0, 0, -1), 0.2))
    for k, (b, root, d, L) in enumerate(kelp):
        d = Vector(d).normalized()
        pts = [tuple(Vector(root) + d * L * t + Vector((0.025 * math.sin(t * 9 + k), 0, 0))) for t in (0, 0.33, 0.66, 1.0)]
        c.tube(b, f'kelp{k}', pts, 0.018, '#3f8a4a' if k % 2 else '#2f6f3a', taper=0.25)
    c.membrane('cape', 'cape', (0, 0.17, 1.0), [(-0.24, 0.12, 1.12), (-0.3, 0.26, 0.6), (-0.2, 0.3, 0.32), (-0.1, 0.27, 0.45),
                                                 (0, 0.3, 0.28), (0.1, 0.28, 0.42), (0.2, 0.3, 0.3), (0.3, 0.26, 0.6),
                                                 (0.24, 0.12, 1.12)], '#2a6a64', thick=0.012, edge_color='#173a38')
    c.bone('weapon.R', (-0.36, -0.1, 0.62), 'arm.R')
    x, y = -0.36, -0.12
    iron = '#525a62'
    c.tube('weapon.R', 'anchor_shank', [(x, y, 0.84), (x, y, 0.1)], 0.042, iron)
    c.ring('weapon.R', 'anchor_ring', (x, y, 0.9), 0.065, 0.018, '#7a5040', rot=(0, 90, 0))
    c.tube('weapon.R', 'anchor_stock', [(x, y - 0.19, 0.76), (x, y + 0.19, 0.76)], 0.03, '#6b4a3a')
    for s in (-1, 1):
        c.orb('weapon.R', f'stock_cap{s}', (x, y + s * 0.19, 0.76), (0.04, 0.04, 0.04), '#6b4a3a')
    arm_pts = [(x + 0.32 * math.sin(a), y, 0.1 + 0.2 * (1 - math.cos(a))) for a in [math.radians(v) for v in range(-75, 76, 15)]]
    c.tube('weapon.R', 'anchor_arms', arm_pts, 0.04, iron)
    for s in (-1, 1):
        tip = Vector(arm_pts[0] if s < 0 else arm_pts[-1])
        spine(c, 'weapon.R', f'fluke{s}', tip, (s * 0.35, 0, 1), 0.15, 0.065, iron, tip='#8a9098', seg=4)
    c.orb('weapon.R', 'anchor_crown', (x, y, 0.1), (0.06, 0.06, 0.06), iron)
    for k in range(3):
        c.tube('weapon.R', f'anchor_weed{k}', [(x + 0.1 * (k - 1), y, 0.2 + 0.02 * k), (x + 0.12 * (k - 1), y - 0.02, 0.1),
                                                (x + 0.1 * (k - 1), y, 0.02)], 0.012, '#3f8a4a', taper=0.3)
    c.arm_limit = (60, 24)
    return c.finish('heavy')


def moss_post(moss='#5e8a4a', up=0.45, seed=0.0, amount=0.0):
    """post-paint: moss on up-facing surfaces, broken up by noise."""
    from mathutils import noise

    def f(p, n, col):
        k = (n.z - up) / (1 - up)
        if k <= 0:
            return col
        k *= 0.5 + 0.5 * max(0.0, min(1.0, noise.noise(p * 7 + Vector((seed, 0, 0))) * 2 + 0.6 + amount))
        return lerp_col(col, moss, min(1.0, 1.4 * k))
    return f


def hair_fall(c, bone, crown, k, color, locks=9, length=0.45, spread=0.11, back=0.12, curl=0.25):
    """Long hair: a cap over the skull and locks falling down the back and beside the face (sculpted tufts)."""
    x0, y0, z0 = crown
    c.blob(bone, (x0, y0 + 0.035 * k, z0 + 0.035 * k), (0.107 * k, 0.1 * k, 0.098 * k), color)
    for i in range(locks):
        a = math.radians(-80 + 160 * i / (locks - 1))
        root = (x0 + spread * k * math.sin(a), y0 + 0.04 * k + 0.05 * k * math.cos(a), z0 - 0.01 * k)
        c.tuft(bone, root, (math.sin(a) * 0.35, back + 0.25 * math.cos(a), -1), length * k * (0.8 + 0.2 * math.cos(a)), 0.045 * k, color,
               curl=-curl * 0.2)
    for s in (-1, 1):  # side locks framing the face
        c.tuft(bone, (x0 + s * 0.095 * k, y0 - 0.03 * k, z0 + 0.02 * k), (s * 0.25, -0.05, -1), 0.2 * k, 0.03 * k, color)
    c.tufts(bone, (x0, y0 - 0.05 * k, z0 + 0.09 * k), [(0.7, -1, -0.35), (-0.6, -1, -0.4), (0.1, -1, -0.45)], 0.055 * k, 0.026 * k, color)


def coil(c, bone, center, r0, r1, turns, z0, z1, rad0, rad1, color, n=24, start=-100.0):
    """A flat spiral of masses (a serpent's coil resting on the floor)."""
    pts, radii = [], []
    for i in range(n):
        u = i / (n - 1)
        a = math.radians(start + 360 * turns * u)
        R = r0 + (r1 - r0) * u
        pts.append((center[0] + R * math.cos(a), center[1] + R * math.sin(a), z0 + (z1 - z0) * u))
        radii.append(rad0 + (rad1 - rad0) * u)
    c.limb(bone, pts, radii, color, spacing=0.45)
    return pts


def naga_priestess(eid):
    """나가 사제 — a naga priestess of the drowned temple: a jade serpent body coiled on the floor rising into a
    slender robed torso, a cobra hood fanned behind her head, long sea-green hair under a crown of pearls, gold
    armlets, and a pearl-set trident staff."""
    c = Sculpt(eid, tris=11000, ao=0.55)
    skin, jade, deep, gold, robe = '#bfe0e4', '#2f9a7f', '#1c5f55', '#e2b04a', '#4b2c86'

    def tail_col(p):
        if p.y < -0.05 and p.z < 0.65 and abs(p.x) < 0.09 and p.z > 0.2:
            return '#f1e2b0' if math.sin(p.z * 70) > -0.5 else '#d8c48a'
        band = math.sin(p.x * 22 + p.y * 18) > 0.8
        return lerp_col(deep, jade, 0.5 + 0.5 * math.sin(p.z * 6)) if not band else '#58c4a6'
    c.bone('body', (0, 0, 0.66)); c.bone('head', (0, -0.01, 1.06), 'body'); c.bone('eyes', (0, -0.1, 1.15), 'head')
    c.bone('crest', (0, 0.05, 1.12), 'head')
    coil(c, 'root', (0, 0.12, 0), 0.38, 0.18, 1.1, 0.11, 0.17, 0.12, 0.095, tail_col)
    c.limb(['root', 'root', 'body', 'body'], [(0.04, -0.24, 0.12), (0.0, -0.17, 0.3), (0.0, -0.06, 0.48), (0, -0.01, 0.62), (0, 0, 0.7)],
           [0.12, 0.115, 0.11, 0.105, 0.1], tail_col)
    c.bone('tail1', (-0.24, 0.3, 0.16)); c.bone('tail2', (-0.36, 0.48, 0.24), 'tail1'); c.bone('tail3', (-0.3, 0.64, 0.36), 'tail2')
    c.limb(['tail1', 'tail2', 'tail3'], [(-0.16, 0.24, 0.16), (-0.33, 0.42, 0.2), (-0.36, 0.58, 0.32), (-0.26, 0.7, 0.44)],
           [0.08, 0.06, 0.04, 0.015], tail_col)
    # torso
    c.blob('body', (0, 0, 0.76), (0.1, 0.08, 0.08), skin)
    c.blob('body', (0, -0.005, 0.9), (0.14, 0.09, 0.1), skin)
    for s in (-1, 1):
        c.blob('body', (s * 0.13, 0, 0.96), (0.055, 0.055, 0.05), skin)
    c.blob('head', (0, -0.005, 1.02), (0.042, 0.042, 0.06), skin)
    c.paint((0, -0.04, 0.88), (0.15, 0.08, 0.075), robe, weight=1.3)                                # vestment
    c.paint((0, -0.09, 0.92), (0.03, 0.02, 0.1), gold, weight=1.6)
    c.paint((0, -0.02, 0.73), (0.11, 0.1, 0.02), gold, weight=1.5)                                  # gold sash
    c.membrane('body', 'robe_front', (0, -0.1, 0.74), [(-0.1, -0.09, 0.74), (-0.12, -0.15, 0.5), (-0.04, -0.17, 0.38),
                                                        (0.04, -0.17, 0.38), (0.12, -0.15, 0.5), (0.1, -0.09, 0.74)], robe,
               thick=0.01, edge_color=gold)
    anime_head(c, 'head', 'eyes', (0, -0.02, 1.15), 0.95, skin, '#ffcf3a', '#1d4a48', lips='#7a3a6a')
    hair_fall(c, 'head', (0, -0.02, 1.16), 0.95, '#1f6f6a', locks=9, length=0.5)
    # pearl crown
    c.ring('head', 'crown_band', (0, -0.01, 1.26), 0.1, 0.012, gold, rot=(-8, 0, 0))
    for i in range(7):
        a = math.radians(-90 + 180 * i / 6)
        h = 0.07 if i == 3 else 0.045 - 0.008 * abs(i - 3)
        p = Vector((0.1 * math.sin(a), -0.01 - 0.1 * math.cos(a), 1.26 + 0.012 * math.cos(a)))
        c.tube('head', f'crown_tine{i}', [tuple(p), tuple(p + Vector((0, 0, h)))], 0.006, gold)
        c.orb('head', f'crown_pearl{i}', tuple(p + Vector((0, 0, h + 0.012))), (0.016, 0.016, 0.016) if i != 3 else (0.026, 0.026, 0.026),
              '#fbf3f6')
    # cobra hood fanned behind the head
    hood = []
    for i in range(11):
        a = math.radians(-100 + 200 * i / 10)
        hood.append((0.22 * math.sin(a), 0.1, 1.08 + 0.17 * math.cos(a) * (1 if math.cos(a) > 0 else 0.6)))
    hd = c.membrane('crest', 'cobra_hood', (0, 0.1, 1.06), hood, jade, thick=0.014, edge_color=deep)
    paint_where(hd, lambda v: (v.x * v.x) / 0.01 + ((v.z - 1.12) ** 2) / 0.006 < 1 and abs(v.x) > 0.06, '#f1e2b0')
    for s, side in ((-1, 'R'), (1, 'L')):
        c.bone('arm.' + side, (s * 0.14, 0, 0.95), 'body')
        c.limb('arm.' + side, [(s * 0.15, 0, 0.95), (s * 0.22, -0.02, 0.82), (s * 0.25, -0.08, 0.7)], [0.04, 0.032, 0.028], skin)
        c.blob('arm.' + side, (s * 0.255, -0.1, 0.665), (0.03, 0.03, 0.035), skin)
        c.ring('arm.' + side, f'armlet{side}', (s * 0.2, -0.015, 0.85), 0.04, 0.009, gold, rot=(0, s * 30, 0))
        c.ring('arm.' + side, f'bracelet{side}', (s * 0.245, -0.07, 0.72), 0.033, 0.008, gold, rot=(0, s * 20, 0))
    c.ring('body', 'necklace', (0, -0.005, 1.0), 0.07, 0.01, gold, rot=(-15, 0, 0))
    c.orb('body', 'necklace_pearl', (0, -0.08, 0.97), (0.022, 0.016, 0.022), '#fbf3f6')
    c.add('arm.L', A.sphere('cast_pearl', r=0.035, loc=(0.27, -0.16, 0.68), color='#bff6ff', mat='M_Emit', seg=14, rings=8))
    # trident staff
    c.bone('weapon.R', (-0.255, -0.1, 0.665), 'arm.R')
    x, y = -0.255, -0.1
    c.tube('weapon.R', 'staff', [(x, y, 0.15), (x, y, 1.42)], 0.016, '#e8dcc0')
    for z in (0.62, 0.72):
        c.ring('weapon.R', f'staff_band{z}', (x, y, z), 0.021, 0.007, gold)
    c.tube('weapon.R', 'trident_bar', [(x - 0.09, y, 1.42), (x, y, 1.4), (x + 0.09, y, 1.42)], 0.012, gold)
    for s in (-1, 0, 1):
        base = (x + s * 0.09, y, 1.42)
        c.tube('weapon.R', f'prong{s}', [base, (x + s * 0.095, y, 1.52 + (0.04 if s == 0 else 0))], 0.01, gold)
        spine(c, 'weapon.R', f'prong_tip{s}', (x + s * 0.095, y, 1.52 + (0.04 if s == 0 else 0)), (0, 0, 1), 0.06, 0.02, gold,
              tip='#fff2c0', seg=6)
    c.orb('weapon.R', 'staff_pearl', (x, y - 0.005, 1.45), (0.03, 0.03, 0.03), '#fbf3f6')
    c.follow['crest'] = 0.5
    c.arm_limit = (80, 30)

    def extra(a, clip, f, t, i, names):
        if clip == 'Die':
            serpent_die(a, f, t, slump=70)
        else:
            a.r('root', f, (0, 0, 0))
            a.l('root', f, (a.P.rl[0] * 0.3, a.P.rl[1] * 0.3, 0))
    return c.finish('biped', extra)


def turtle_titan(eid):
    """거북 타이탄 — a colossal temple turtle: a high-domed shell of mossy olive scutes carrying a small marble shrine
    with a verdigris roof and a glowing pearl, a beaked head under heavy brows, and pillar legs with blunt claws."""
    c = Sculpt(eid, tris=11000, ao=0.6)
    c.post = moss_post('#6f9a46', 0.6, 7.0, -0.2)
    C, R = Vector((0, 0.06, 0.6)), (0.5, 0.62, 0.34)
    cells = [(0, -0.36), (0, -0.12), (0, 0.12), (0, 0.36), (0, 0.56)] + [(s * 0.3, y) for s in (-1, 1) for y in (-0.3, -0.05, 0.2, 0.45)]

    def scute(p):
        if p.z < 0.42:
            return '#d9c88a' if p.y < 0.4 else '#6f6a40'
        ds = sorted(math.hypot(p.x - x, p.y - y) for x, y in cells)
        if ds[1] - ds[0] < 0.035:
            return '#3a3f22'
        return lerp_col('#9aab58', '#5f6b32', min(1.0, ds[0] / 0.2))
    skin = lambda p: lerp_col('#4f7f78', '#7fb0a2', (p.z - 0.15) / 0.5)  # noqa: E731
    c.bone('body', tuple(C)); c.bone('head', (0, -0.62, 0.5), 'body'); c.bone('eyes', (0, -0.86, 0.62), 'head')
    c.bone('jaw', (0, -0.78, 0.5), 'head'); c.bone('tail1', (0, 0.62, 0.42), 'body')
    c.blob('body', tuple(C), R, scute)
    c.blob('body', (0, 0.06, 0.66), (0.4, 0.52, 0.3), scute)
    for i in range(18):  # flared marginal scutes along the rim
        a = TAU * i / 18
        c.blob('body', (0.5 * math.cos(a), 0.06 + 0.62 * math.sin(a), 0.48), (0.09, 0.09, 0.05), '#7a8a44' if i % 2 else '#6a7a3a')
    c.blob('body', (0, 0.04, 0.36), (0.4, 0.5, 0.1), '#e2cf96')                                     # plastron
    c.limb('head', [(0, -0.5, 0.48), (0, -0.62, 0.5), (0, -0.72, 0.55)], [0.14, 0.12, 0.11], skin)
    c.blob('head', (0, -0.8, 0.58), (0.13, 0.15, 0.11), skin)
    c.blob('head', (0, -0.94, 0.56), (0.07, 0.06, 0.06), '#d9c07a')                                  # beak
    c.limb('jaw', [(0, -0.76, 0.49), (0, -0.9, 0.5)], [0.08, 0.05], '#7fb0a2')
    c.blob('jaw', (0, -0.93, 0.505), (0.05, 0.04, 0.03), '#c9b06a')
    c.paint((0, -0.88, 0.53), (0.1, 0.1, 0.008), '#2a2a1a', weight=1.6)
    for s in (-1, 1):
        c.blob('eyes', (s * 0.075, -0.87, 0.67), (0.05, 0.05, 0.025), '#4f7f78', rot=(0, s * 15, 0))   # heavy brow
        c.eye('eyes', (s * 0.08, -0.885, 0.635), (s * 0.55, -1, 0.05), 0.03, '#d9902a')
        for j in range(3):
            c.paint((s * (0.06 + 0.03 * j), -0.75, 0.68 - 0.02 * j), (0.02, 0.02, 0.02), '#3f6a62')
    for s, side in ((-1, 'R'), (1, 'L')):
        for fb, y in (('F', -0.32), ('B', 0.42)):
            b = f'leg.{fb}{side}'
            x = s * 0.38
            c.bone(b, (x, y, 0.45), 'body')
            c.limb(b, [(x, y, 0.45), (x * 1.08, y - 0.02, 0.24), (x * 1.08, y - 0.03, 0.08)], [0.14, 0.12, 0.12], skin)
            c.blob(b, (x * 1.08, y - 0.06, 0.05), (0.13, 0.14, 0.05), skin)
            for j in range(3):
                c.blob(b, (x * 1.08 + (j - 1) * 0.06, y - 0.17, 0.035), (0.03, 0.03, 0.025), '#e6dcc0')
    c.limb('tail1', [(0, 0.6, 0.42), (0, 0.72, 0.36), (0, 0.8, 0.28)], [0.07, 0.05, 0.02], skin)
    # the shrine on the shell
    top = 0.94
    marble, roof = '#ece4d0', '#4fa59a'
    c.box('body', 'shrine_base', (0, 0.06, top + 0.02), (0.5, 0.54, 0.06), '#d8cfb8', bevel=0.012)
    c.box('body', 'shrine_step', (0, -0.22, top - 0.02), (0.3, 0.1, 0.05), '#d8cfb8', bevel=0.01)
    for sx in (-1, 1):
        for sy in (-1, 1):
            p = (sx * 0.19, 0.06 + sy * 0.2, top + 0.05)
            c.add('body', A.cyl(f'column{sx}{sy}', r=0.032, depth=0.3, loc=(p[0], p[1], p[2] + 0.15), color=marble, seg=10))
            c.box('body', f'capital{sx}{sy}', (p[0], p[1], p[2] + 0.31), (0.09, 0.09, 0.03), marble, bevel=0.006)
    c.box('body', 'architrave', (0, 0.06, top + 0.385), (0.5, 0.52, 0.05), marble, bevel=0.008)
    gable = A.extrude_shape('roof', [(-0.3, 0), (0.3, 0), (0, 0.16)], depth=0.58, color=roof)
    gable.rotation_euler = (0, 0, 0)
    gable.location = (0, 0.06, top + 0.41)
    gable.rotation_euler = (0, 0, math.radians(90))
    c.add('body', gable)
    c.add('body', A.sphere('shrine_pearl', r=0.07, loc=(0, 0.06, top + 0.17), color='#d8fff6', mat='M_Emit', seg=18, rings=10))
    c.add('body', A.cyl('pearl_stand', r=0.05, depth=0.06, loc=(0, 0.06, top + 0.08), r2=0.035, color='#e2b04a', seg=12))
    for k in range(5):  # vines hanging from the roof
        x = -0.24 + 0.12 * k
        c.tube('body', f'vine{k}', [(x, -0.24, top + 0.38), (x + 0.01, -0.25, top + 0.28 - 0.03 * (k % 2)), (x - 0.01, -0.24, top + 0.2 - 0.04 * (k % 3))],
               0.01, '#4f9a4a', taper=0.4)
    for k, (x, y) in enumerate(((0.35, -0.2), (-0.32, 0.1), (0.25, 0.45), (-0.2, -0.4))):
        z = C.z + R[2] * math.sqrt(max(0.0, 1 - (x / R[0]) ** 2 - ((y - C.y) / R[1]) ** 2)) - 0.01
        c.add('body', A.cyl(f'barnacle{k}', r=0.035, depth=0.035, loc=(x, y, z), r2=0.02, color='#e3ddcf', seg=8))
    return c.finish('quad')


def siren(eid):
    """세이렌 — a sea siren: a singer with long rose hair and a pearl circlet, aqua-and-white feathered wings with
    pink tips, a downy feathered lower body with taloned bird feet and a fanned tail, holding a shell harp."""
    sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'enemies_d'))
    from flyers import feather_wing, fan_tail
    c = Sculpt(eid, tris=10000, ao=0.5)
    skin, hair, aqua, white, pink, gold = '#ffe2d4', '#f08ab8', '#5ccfd6', '#f6fbff', '#ff9ec0', '#e9c060'
    c.bone('body', (0, 0, 1.0)); c.bone('head', (0, -0.01, 1.22), 'body'); c.bone('eyes', (0, -0.1, 1.31), 'head')
    c.bone('tail1', (0, 0.12, 0.88), 'body')
    c.blob('body', (0, 0, 1.06), (0.085, 0.07, 0.07), skin)
    c.blob('body', (0, -0.005, 1.15), (0.11, 0.075, 0.07), skin)
    for s in (-1, 1):
        c.blob('body', (s * 0.1, 0, 1.19), (0.045, 0.045, 0.04), skin)
    c.blob('head', (0, -0.005, 1.23), (0.035, 0.035, 0.05), skin)
    c.paint((0, -0.05, 1.14), (0.12, 0.07, 0.05), aqua, weight=1.3)                                  # feather bodice
    c.paint((0, -0.075, 1.17), (0.09, 0.03, 0.012), gold, weight=1.6)
    # feathered lower body
    c.blob('body', (0, 0.01, 0.95), (0.12, 0.1, 0.1), white)
    for i in range(9):
        a = math.radians(-160 + 320 * i / 8)
        c.tuft('body', (0.1 * math.sin(a), 0.02 - 0.08 * math.cos(a), 0.92), (math.sin(a) * 0.3, -0.3 * math.cos(a) + 0.1, -1), 0.13,
               0.04, white if i % 2 else '#d6f4f6', curl=0.1)
    anime_head(c, 'head', 'eyes', (0, -0.01, 1.33), 0.85, skin, '#3fb6c8', '#a0406a', lips='#e0607e', blush='#ffb0b8')
    c.paint((0, -0.093, 1.27), (0.012, 0.012, 0.012), '#8a2040', weight=2.0)                          # singing mouth
    hair_fall(c, 'head', (0, -0.01, 1.34), 0.85, hair, locks=9, length=0.55, back=0.2)
    c.ring('head', 'circlet', (0, -0.005, 1.42), 0.09, 0.008, gold, rot=(-12, 0, 0))
    c.orb('head', 'circlet_pearl', (0, -0.1, 1.405), (0.016, 0.012, 0.016), '#fbf3f6')
    for s, side in ((-1, 'R'), (1, 'L')):
        c.bone('wing.' + side, (s * 0.08, 0.05, 1.18), 'body')
        feather_wing(c, 'wing.' + side, s, (s * 0.08, 0.07, 1.18), 0.62, 0.18, aqua, pink, white, aqua, feathers=8, r=0.024)
        c.bone('arm.' + side, (s * 0.11, 0, 1.19), 'body')
        c.limb('arm.' + side, [(s * 0.12, 0, 1.19), (s * 0.16, -0.06, 1.1), (s * 0.1, -0.15, 1.08)], [0.03, 0.025, 0.022], skin)
        c.blob('arm.' + side, (s * 0.09, -0.16, 1.08), (0.022, 0.022, 0.026), skin)
        c.bone('leg.' + side, (s * 0.05, 0.02, 0.9), 'body')
        c.limb('leg.' + side, [(s * 0.05, 0.02, 0.88), (s * 0.06, 0.0, 0.78), (s * 0.06, -0.02, 0.7)], [0.035, 0.022, 0.018], '#e6b85a')
        for j in range(3):
            c.spike('leg.' + side, f'talon{side}{j}', (s * 0.06, -0.02, 0.7), (s * 0.06 + (j - 1) * 0.025, -0.06, 0.67), 0.008, '#3a2420')
    fan_tail(c, 'tail1', (0, 0.1, 0.9), 0.32, 70, aqua, pink, n=7)
    # shell harp held before the chest
    c.bone('weapon.L', (0.0, -0.17, 1.08), 'arm.L')
    hx, hy = 0.02, -0.2
    for s in (-1, 1):
        c.tube('weapon.L', f'harp_arm{s}', [(hx + s * 0.03, hy, 1.0), (hx + s * 0.08, hy, 1.08), (hx + s * 0.07, hy, 1.17), (hx + s * 0.1, hy, 1.22)],
               0.011, gold, taper=0.7)
    c.tube('weapon.L', 'harp_bar', [(hx - 0.1, hy, 1.2), (hx + 0.1, hy, 1.2)], 0.008, gold)
    for k in range(5):
        x = hx - 0.05 + 0.025 * k
        c.tube('weapon.L', f'harp_string{k}', [(x, hy, 1.02), (x, hy, 1.2)], 0.0025, '#fff6d8')
    c.add('weapon.L', scallop('harp_shell', (hx, hy + 0.01, 0.95), 0.09, 0.1, 0.03, '#ff9ec0', '#fff0e6', ribs=6))
    return c.finish('fly')


# ---------------------------------------------------------------------------------------------- leviathan (boss)
def ray_fin(c, bone, name, root, axis, side, length, spread, n, color, edge, spine_col=None, k=0.32, thick=0.01, rays=True):
    """Big spined fin: n rays fanning from `root` around `axis` (the fin's mean direction) toward `side`, a
    scalloped membrane between them and a rigid tapering spine along each ray."""
    root, axis, side = Vector(root), Vector(axis).normalized(), Vector(side).normalized()
    tips = []
    for i in range(n):
        u = i / (n - 1) - 0.5
        d = (axis + side * u * spread).normalized()
        tips.append(root + d * length * (1 - 0.35 * abs(u) * 2 * 0.6))
    fish_fin(c, bone, name, root, tips, color, edge, k=k, thick=thick)
    if rays:
        for i, t in enumerate(tips):
            spine(c, bone, f'{name}_ray{i}', tuple(root), t - root, (t - root).length * 1.08, length * 0.022,
                  spine_col or color, tip=edge, seg=6)
    return tips


def leviathan(eid):
    """레비아탄 — chapter 5 boss: a colossal sea dragon reared out of its own coils on the temple floor. Indigo back,
    teal flanks and a pale ribbed belly, rows of bioluminescent cyan stripes and glowing lamps down the flanks, a
    long horned dragon skull with a fanged hinged jaw, whisker barbels, a crown of spined fins fanning around the
    back of the head, a dorsal sail down the neck, two great wing-like pectoral fins and a fan-finned tail tip."""
    k = 2.55                                      # modelled at ~1.45 m, enlarged to ~3.7 m
    c = BossSculpt(eid, scale=k, tris=20000, ao=0.6)
    navy, teal, pale, glow, fin, fin_edge = '#22397e', '#2f9cc0', '#e6f4e6', '#8ffbff', '#36b4d6', '#d4fcff'
    from mathutils import noise

    def hide(p):
        """indigo back to teal flanks, belly plates, and cyan stripes running along the body."""
        n = noise.noise(p * 9)
        if p.z > 0.36:   # reared neck: indigo back, teal flanks; glowing rings round the back of the neck
            col = lerp_col(teal, navy, 0.5 + (p.y + 0.18 - (p.z - 0.4) * 0.1) * 6 + 0.2 * n)
            stripe = math.sin(p.z * 34) > 0.8 and p.y > -0.24 - (p.z - 0.3) * 0.12
        else:            # coil: indigo top, teal sides; glowing chevrons across the top
            a = math.atan2(p.y - 0.14, p.x)
            col = lerp_col(teal, navy, 0.5 + (p.z - 0.2) * 7 + 0.2 * n)
            stripe = math.sin(a * 22 + (p.z - 0.2) * 12) > 0.8 and p.z > 0.15
        return lerp_col(col, glow, 0.8) if stripe else col

    def coil_col(p):
        if p.z < 0.07:
            return pale
        return hide(p)

    def neck_col(p):
        # the pale ribbed belly runs up the front of the reared neck
        front = -0.2 - (p.z - 0.25) * 0.22
        if p.y < front and abs(p.x) < 0.1:
            return pale if math.sin(p.z * 60) > -0.55 else lerp_col(pale, '#9fc9c0', 0.7)
        return hide(p)
    c.bone('body', (0, -0.12, 0.32)); c.bone('head', (0, -0.2, 1.15), 'body'); c.bone('eyes', (0, -0.45, 1.6), 'head')
    c.bone('jaw', (0, -0.38, 1.47), 'head'); c.bone('crest', (0, -0.24, 1.66), 'head')
    # two floor coils
    coil(c, 'root', (0, 0.14, 0), 0.44, 0.22, 1.3, 0.15, 0.19, 0.15, 0.115, coil_col, n=32, start=-95.0)
    # neck rising in an S out of the coil
    neck = [(0.06, -0.3, 0.16), (0.03, -0.27, 0.48), (-0.04, -0.13, 0.8), (-0.02, -0.08, 1.1), (0.0, -0.2, 1.38),
            (0, -0.34, 1.49)]
    c.limb(['root', 'body', 'body', 'head', 'head'], neck, [0.175, 0.155, 0.14, 0.125, 0.115, 0.11], neck_col)
    # tail tip leaving the coil
    c.bone('tail1', (0.32, 0.42, 0.16)); c.bone('tail2', (0.46, 0.62, 0.22), 'tail1'); c.bone('tail3', (0.48, 0.8, 0.34), 'tail2')
    c.limb(['tail1', 'tail2', 'tail3'], [(0.24, 0.36, 0.16), (0.42, 0.56, 0.2), (0.5, 0.74, 0.3), (0.48, 0.88, 0.44)],
           [0.11, 0.075, 0.045, 0.02], hide)
    ray_fin(c, 'tail3', 'tail_fin', (0.48, 0.84, 0.4), (0, 0.6, 1), (1, 0.2, 0), 0.34, 1.6, 7, fin, fin_edge)
    # head: long dragon skull, heavy brows, snout, hinged jaw
    m0 = len(c.masses)
    hz = 1.56

    def skull(p):
        stripe = math.sin(p.y * 40) > 0.85 and p.z > hz + 0.02
        col = lerp_col(teal, navy, (p.z - (hz - 0.07)) / 0.1)
        return lerp_col(col, glow, 0.7) if stripe else col
    c.blob('head', (0, -0.38, hz), (0.15, 0.16, 0.115), skull)
    c.blob('head', (0, -0.3, hz - 0.05), (0.13, 0.12, 0.1), skull)
    c.limb('head', [(0, -0.48, hz + 0.0), (0, -0.6, hz - 0.02), (0, -0.7, hz - 0.035)], [0.105, 0.085, 0.065], skull)
    c.blob('head', (0, -0.6, hz + 0.03), (0.07, 0.09, 0.035), navy)                    # snout ridge
    c.blob('head', (0, -0.73, hz - 0.03), (0.06, 0.035, 0.045), skull)                  # upper lip pad
    for s in (-1, 1):
        c.blob('head', (s * 0.035, -0.75, hz - 0.005), (0.018, 0.016, 0.012), '#0f1a3a')  # nostrils
        c.blob('eyes', (s * 0.09, -0.47, hz + 0.075), (0.065, 0.075, 0.03), navy, rot=(0, s * 18, 0))   # brow ridge
        c.eye('eyes', (s * 0.105, -0.495, hz + 0.035), (s * 0.75, -0.65, 0.12), 0.036, '#ffd23a', slit=True)
        c.blob('head', (s * 0.11, -0.42, hz - 0.07), (0.06, 0.09, 0.05), skull)          # cheek
    c.limb('jaw', [(0, -0.33, hz - 0.11), (0, -0.48, hz - 0.12), (0, -0.62, hz - 0.11), (0, -0.7, hz - 0.095)],
           [0.095, 0.08, 0.06, 0.045], lambda p: lerp_col(pale, teal, (p.z - (hz - 0.17)) / 0.08))
    c.paint((0, -0.56, hz - 0.075), (0.085, 0.17, 0.012), '#3a0f24', weight=1.8)       # mouth line
    up = [Vector((sx * 0.07 * (1 - 0.35 * t), -0.5 - 0.22 * t, hz - 0.065)) for t in (0.0, 0.25, 0.5, 0.75, 1.0) for sx in (-1, 1)]
    teeth(c, 'head', up, (0, -0.2, -1), 0.05, 0.012)
    lo = [Vector((sx * 0.06 * (1 - 0.35 * t), -0.5 - 0.18 * t, hz - 0.085)) for t in (0.12, 0.45, 0.8) for sx in (-1, 1)]
    teeth(c, 'jaw', lo, (0, -0.15, 1), 0.04, 0.011)
    # horns and barbels
    for s in (-1, 1):
        c.tube('head', f'horn{s}', bezier((s * 0.08, -0.36, hz + 0.09), (s * 0.18, -0.2, hz + 0.2), (s * 0.2, -0.05, hz + 0.12), 8),
               0.032, '#e9e2c8', taper=0.12)
        c.tube('jaw', f'barbel{s}', bezier((s * 0.06, -0.72, hz - 0.05), (s * 0.2, -0.78, hz - 0.12), (s * 0.24, -0.66, hz - 0.3), 8),
               0.012, fin, taper=0.2)
    # crown of spined fins fanning round the back of the skull
    for j, a in enumerate((-70, -38, 0, 38, 70)):
        r = math.radians(a)
        d = Vector((math.sin(r) * 0.9, 0.55, math.cos(r) * 0.85 + 0.25))
        root = Vector((math.sin(r) * 0.09, -0.3, hz + 0.05 + 0.04 * math.cos(r)))
        side = d.cross(Vector((0, -1, 0))).normalized()
        ray_fin(c, 'crest', f'crown_fin{j}', tuple(root), d, side, 0.3 + 0.06 * math.cos(r), 0.75, 5, fin, fin_edge)
    scale_region(c, ('head', 'eyes', 'jaw', 'crest'), (0, -0.33, hz - 0.05), 1.22, m0)
    # dorsal sail down the back of the neck
    sail = [(0, -0.24, 1.52), (0, -0.14, 1.42), (0, -0.05, 1.3), (0, 0.0, 1.14), (0, 0.04, 1.0), (0, 0.05, 0.84),
            (0, 0.03, 0.66), (0, 0.02, 0.48)]
    pts = []
    for (x, y, z), h in zip(sail, (0.04, 0.12, 0.16, 0.17, 0.16, 0.14, 0.11, 0.05)):
        pts.append(Vector((x, y + h, z + h * 0.3)))
    fish_fin(c, 'body', 'dorsal_sail', (0, -0.1, 1.0), [tuple(p) for p in pts], fin, fin_edge, k=0.25, thick=0.012)
    for i, (b, p) in enumerate(zip(sail[1:-1], pts[1:-1])):
        spine(c, 'body', f'sail_ray{i}', b, Vector(p) - Vector(b) + Vector((0, 0.02, 0.02)), (Vector(p) - Vector(b)).length * 1.12,
              0.012, navy, tip=fin_edge, seg=6)
    # great pectoral fins (wings) from the base of the neck
    for s, side in ((-1, 'R'), (1, 'L')):
        c.bone('wing.' + side, (s * 0.13, -0.2, 0.7), 'body')
        ray_fin(c, 'wing.' + side, 'pectoral' + side, (s * 0.12, -0.18, 0.7), (s * 1, 0.3, 0.55), (0, 0.4, -1), 0.62, 1.5, 7,
                fin, fin_edge, k=0.3)
    # glowing lamps along the flanks of the neck and coil
    lamps = [(s * (0.135 - 0.006 * i), -0.27 + 0.03 * i, 0.5 + 0.15 * i) for s in (-1, 1) for i in range(5)]
    for i in range(10):
        a = math.radians(-60 + 36 * i)
        lamps.append((0.41 * math.cos(a), 0.14 + 0.41 * math.sin(a), 0.2))
    for i, p in enumerate(lamps):
        b = 'root' if p[2] < 0.3 else 'body' if p[2] < 1.05 else 'head'
        c.add(b, A.sphere(f'lamp{i}', r=0.022, loc=p, scale=(1, 1, 1.3), color=glow, mat='M_Emit', seg=10, rings=6))
    c.follow['crest'] = 1.2

    def extra(a, clip, f, t, i, names):
        if clip == 'Die':
            serpent_die(a, f, t, slump=70.0)
        else:
            a.r('root', f, (0, 0, 0))   # the coils never tip over; the neck does the acting
            a.l('root', f, (a.P.rl[0] * 0.2, a.P.rl[1] * 0.2, 0))
    return c.finish('biped', extra)


BUILDERS = {'puffer': puffer, 'merfolk_guard': merfolk_guard, 'angler': angler, 'giant_clam': giant_clam,
            'sea_urchin': sea_urchin, 'temple_guardian': temple_guardian, 'sea_serpent': sea_serpent,
            'drowned_knight': drowned_knight, 'naga_priestess': naga_priestess, 'turtle_titan': turtle_titan,
            'siren': siren, 'leviathan': leviathan}

if __name__ == '__main__':
    eid = sys.argv[sys.argv.index('--') + 1]
    BUILDERS[eid](eid)
