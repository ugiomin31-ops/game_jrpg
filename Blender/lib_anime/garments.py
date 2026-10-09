"""Garments and armour fitted to the VRoid bodies.

Anime armour (Genshin Impact, Granblue Fantasy, Tales of) reads as a few clean plates with bright trims over cloth,
so each piece here is cut from the body surface it covers (it bends with the same weights), pushed out, relaxed
into a smooth plate and given a trim band. Capes, tabards and robes hang from rings measured on the body.
"""
import math

import bmesh
import bpy
from mathutils import Vector

import abyss_bpy as A
import anime_body as AB
import body as B
from humanoid import V, ellipsoid, lathe, mix, rgb, shade, shell, solidify, sweep, zgrad

GOLD = "#e8b84a"
STEEL = "#b9c7d6"
DARK_STEEL = "#4b5463"


# ---------------------------------------------------------------- measuring

def part_of(bone):
    return AB.bone_side(bone)


def face_bones(o):
    dom = AB.dominant_bones(o)
    out = {}
    for p in o.data.polygons:
        names = [dom[v] for v in p.vertices]
        out[p.index] = max(set(names), key=names.count)
    return out


def head_box(H, body):
    """(centre, half sizes, top z) of the head including hair, in world space."""
    dom = AB.dominant_bones(body)
    pts = [body.matrix_world @ v.co for v in body.data.vertices if dom[v.index] == "head"]
    lo = Vector((min(p.x for p in pts), min(p.y for p in pts), min(p.z for p in pts)))
    hi = Vector((max(p.x for p in pts), max(p.y for p in pts), max(p.z for p in pts)))
    return (lo + hi) / 2, (hi - lo) / 2, hi.z


def skull_box(H, body):
    """(centre, half sizes, top z) of the head without long hair: the skin/face part of the head plus the hair
    that sits on the crown (twin tails and long strands hanging below the jaw are ignored)."""
    dom = AB.dominant_bones(body)
    me = body.data
    hair = {i for i, m in enumerate(me.materials) if m and "HAIR" in m.name.upper()}
    vmat = {}
    for f in me.polygons:
        for vi in f.vertices:
            vmat[vi] = f.material_index
    face = [body.matrix_world @ v.co for v in me.vertices if dom[v.index] == "head" and vmat.get(v.index) not in hair]
    lo = Vector((min(p.x for p in face), min(p.y for p in face), min(p.z for p in face)))
    hi = Vector((max(p.x for p in face), max(p.y for p in face), max(p.z for p in face)))
    crown = [body.matrix_world @ v.co for v in me.vertices if dom[v.index] == "head" and vmat.get(v.index) in hair
             and (body.matrix_world @ v.co).z > (lo.z + hi.z) / 2]
    if crown:
        lo.x = min(lo.x, min(p.x for p in crown if abs(p.x) < 0.11) if any(abs(p.x) < 0.11 for p in crown) else lo.x)
        hi.x = max(hi.x, max(p.x for p in crown if abs(p.x) < 0.11) if any(abs(p.x) < 0.11 for p in crown) else hi.x)
        hi.y = max(hi.y, max(p.y for p in crown if p.y < 0.15) if any(p.y < 0.15 for p in crown) else hi.y)
        hi.z = max(hi.z, max(p.z for p in crown))
    return (lo + hi) / 2, (hi - lo) / 2, hi.z


def limb_radius(body, bone, a, b):
    """Mean distance of a bone's vertices from the a->b axis (sleeve included)."""
    dom = AB.dominant_bones(body)
    d = (b - a).normalized()
    rs = []
    for v in body.data.vertices:
        if dom[v.index] == bone:
            p = body.matrix_world @ v.co - a
            rs.append((p - d * p.dot(d)).length)
    rs.sort()
    return rs[int(len(rs) * 0.8)] if rs else 0.05


# ---------------------------------------------------------------- collision proxies

_PROXY_PARTS = ("hips", "spine", "chest", "neck", "thigh", "shin", "foot", "shoulder")


def proxy(body, extra=()):
    """Temporary collider for conforming hanging cloth: the body without arms and head, plus garments it must
    clear (skirts, belts, armour). Delete with drop_proxy()."""
    o = body.copy()
    o.data = body.data.copy()
    o.modifiers.clear()
    bpy.context.scene.collection.objects.link(o)
    fb = face_bones(o)
    bm = bmesh.new()
    bm.from_mesh(o.data)
    bm.faces.ensure_lookup_table()
    bmesh.ops.delete(bm, geom=[f for f in bm.faces if part_of(fb[f.index]) not in _PROXY_PARTS], context="FACES")
    bm.to_mesh(o.data)
    bm.free()
    parts = [o]
    for e in extra:
        c = e.copy()
        c.data = e.data.copy()
        c.modifiers.clear()
        bpy.context.scene.collection.objects.link(c)
        parts.append(c)
    if len(parts) > 1:
        bpy.ops.object.select_all(action="DESELECT")
        for q in parts:
            q.select_set(True)
        bpy.context.view_layer.objects.active = o
        bpy.ops.object.join()
    o.hide_render = True
    return o


def drop_proxy(p):
    bpy.data.objects.remove(p)


def conform_to(o, body, offset, over=(), keep_outside=False):
    p = proxy(body, over)
    AB.conform(o, p, offset, keep_outside)
    drop_proxy(p)


# ---------------------------------------------------------------- surface pieces

def surface_shell(name, body, keep, color, offset=0.010, thick=0.006, relax=6, mats=None):
    """A plate/garment cut from the body faces where keep(centre, bone) holds (optionally only faces whose
    material name contains one of `mats`), pushed out by offset, relaxed and thickened. Keeps the body weights."""
    o = body.copy()
    o.data = me = body.data.copy()
    o.name = name
    o.modifiers.clear()
    bpy.context.scene.collection.objects.link(o)
    fb = face_bones(o)
    mnames = [m.name if m else "" for m in me.materials]
    bm = bmesh.new()
    bm.from_mesh(me)
    bm.faces.ensure_lookup_table()
    dead = []
    for f in bm.faces:
        if mats is not None and not any(k in mnames[f.material_index] for k in mats):
            dead.append(f)
            continue
        if not keep(o.matrix_world @ f.calc_center_median(), fb[f.index]):
            dead.append(f)
    bmesh.ops.delete(bm, geom=dead, context="FACES")
    bmesh.ops.delete(bm, geom=[v for v in bm.verts if not v.link_faces], context="VERTS")
    bmesh.ops.remove_doubles(bm, verts=bm.verts, dist=0.0015)
    bm.normal_update()
    for v in bm.verts:
        v.co += v.normal * offset
    bm.to_mesh(me)
    bm.free()
    for uv in list(me.uv_layers):
        me.uv_layers.remove(uv)
    A.paint(o, color)
    if relax:
        AB.relax(o, relax)
    if thick > 0:
        md = o.modifiers.new("thick", "SOLIDIFY")
        md.thickness = thick
        md.offset = 1.0
        md.use_even_offset = True
        md.use_rim = True
        A.apply_modifiers(o)
    for p in o.data.polygons:
        p.use_smooth = True
    return o


def metal(o, color, shine=0.55, light=(-0.45, -0.55, 0.7), smooth=True):
    """Toon metal in hard bands from a fixed key light: shadow side, base, lit face, a small glint.
    Call it on the clean analytic shape (before conforming) so the bands stay smooth."""
    me = o.data
    attr = me.color_attributes["Col"]
    L = Vector(light).normalized()
    dark, base = rgb(shade(color, 0.66)), rgb(color)
    lit, glint = rgb(mix(color, "#ffffff", 0.22)), rgb(mix(color, "#ffffff", shine))
    for loop in me.loops:
        n = me.vertices[loop.vertex_index].normal if smooth else me.polygons[loop.index // 3].normal
        t = n.dot(L)
        c = dark if t < -0.05 else base if t < 0.62 else lit if t < 0.9 else glint
        attr.data[loop.index].color_srgb = (*c[:3], 1.0)
    return o


def trim(o, test, color):
    """Paints a trim band on the faces where test(centre, normal) holds."""
    AB.paint_faces(o, lambda co, n: color if test(co, n) else None)
    return o


def edge_trim(o, color, width=0.012):
    """Paints the faces within `width` of the piece's open border (the classic gold edge on armour)."""
    bm = bmesh.new()
    bm.from_mesh(o.data)
    border = [v.co.copy() for v in bm.verts if v.is_boundary]
    bm.free()
    if not border:
        return o
    from mathutils.kdtree import KDTree
    kd = KDTree(len(border))
    for i, c in enumerate(border):
        kd.insert(c, i)
    kd.balance()
    AB.paint_faces(o, lambda co, n: color if kd.find(o.matrix_world.inverted() @ co)[2] < width else None)
    return o


# ---------------------------------------------------------------- outfit edits on the VRoid clothes

def strip_hood(body, H):
    """Takes the hood off the VRoid hoodie so it reads as a tunic/gambeson."""
    j = H.j
    nz, ny = j["neck"].z, j["neck"].y
    fb = face_bones(body)
    mn = [m.name if m else "" for m in body.data.materials]
    bm = bmesh.new()
    bm.from_mesh(body.data)
    bm.faces.ensure_lookup_table()
    dead = []
    for f in bm.faces:
        if "Tops" not in mn[f.material_index]:
            continue
        c = f.calc_center_median()
        if c.z > nz - 0.035 and (c.y > ny - 0.01 or c.z > nz + 0.01):
            dead.append(f)
    bmesh.ops.delete(bm, geom=dead, context="FACES")
    bmesh.ops.delete(bm, geom=[v for v in bm.verts if not v.link_faces], context="VERTS")
    bm.to_mesh(body.data)
    bm.free()


def drop_where(body, mat_key, test):
    """Deletes faces of materials containing mat_key whose centre/bone satisfy test(co, bone)."""
    fb = face_bones(body)
    mn = [m.name if m else "" for m in body.data.materials]
    bm = bmesh.new()
    bm.from_mesh(body.data)
    bm.faces.ensure_lookup_table()
    dead = [f for f in bm.faces if mat_key in mn[f.material_index]
            and test(body.matrix_world @ f.calc_center_median(), fb[f.index])]
    bmesh.ops.delete(bm, geom=dead, context="FACES")
    bmesh.ops.delete(bm, geom=[v for v in bm.verts if not v.link_faces], context="VERTS")
    bm.to_mesh(body.data)
    bm.free()


# ---------------------------------------------------------------- armour pieces

TORSO = ("hips", "spine", "chest", "neck")


def torso_ring(body, z, band=0.012, parts=TORSO, dom=None):
    """(centre y, half width, half depth) of the torso cut at z (arms and legs excluded)."""
    dom = dom or AB.dominant_bones(body)
    xs, ys = [], []
    for v in body.data.vertices:
        co = body.matrix_world @ v.co
        if abs(co.z - z) < band and part_of(dom[v.index]) in parts:
            xs.append(abs(co.x))
            ys.append(co.y)
    if not xs:
        return 0.0, 0.05, 0.05
    xs.sort()
    ys.sort()
    rx = xs[int(len(xs) * 0.97)]
    y0, y1 = ys[int(len(ys) * 0.02)], ys[int(len(ys) * 0.98)]
    return (y0 + y1) / 2, rx, (y1 - y0) / 2


def superellipse(rx, ry, p=2.6, wave=None):
    def r(a):
        s, c = abs(math.sin(a)), abs(math.cos(a))
        v = ((s / rx) ** p + (c / ry) ** p) ** (-1.0 / p)
        return v * (1 + wave(a)) if wave else v
    return r


def ring_shell(name, rings, color, seg=36, a0=None, a1=None, p=2.6, wave=None):
    """Lathe through measured rings [(z, cy, rx, ry)]; each ring is a superellipse around its own centre."""
    zs = [r[0] for r in rings]
    cys = [r[1] for r in rings]

    def yshift(zz):
        for (z0, c0), (z1, c1) in zip(zip(zs, cys), list(zip(zs, cys))[1:]):
            if min(z0, z1) - 1e-6 <= zz <= max(z0, z1) + 1e-6:
                t = (zz - z0) / (z1 - z0) if z1 != z0 else 0
                return c0 + (c1 - c0) * t
        return cys[0] if abs(zz - zs[0]) < abs(zz - zs[-1]) else cys[-1]
    prof = [(superellipse(rx, ry, p, (lambda a, k=k: wave(a, k)) if wave else None), z)
            for k, (z, cy, rx, ry) in enumerate(rings)]
    return lathe(name, prof, color, seg=seg, a0=a0, a1=a1, caps=False, yshift=yshift)


def band(name, ring, color, h=0.014, out=0.006, p=2.6, seg=36):
    z, cy, rx, ry = ring
    o = lathe(name, [(superellipse(rx + out, ry + out, p), z - h / 2), (superellipse(rx + out, ry + out, p), z + h / 2)],
              color, seg=seg, caps=False, yshift=lambda zz: cy)
    solidify(o, 0.005)
    metal(o, color, shine=0.65)
    return o


def cuirass(H, body, color, trim_color=GOLD, bottom=None, pad=0.022, lames=3, name="cuirass"):
    """Breastplate measured from the torso (over the clothes), conformed outside it, with gold edge bands and
    lames over the belly."""
    j = H.j
    dom = AB.dominant_bones(body)
    hz, nz, cz = j["hip"].z, j["neck"].z, j["chest"].z
    bottom = hz + 0.02 if bottom is None else bottom
    top = j["shoulder.L"].z - 0.02
    zs = [bottom + (top - bottom) * t for t in (0.0, 0.2, 0.4, 0.6, 0.8, 1.0)]
    rings = []
    for z in zs:
        cy, rx, ry = torso_ring(body, z, dom=dom)
        bust = 0.022 * max(0.0, 1 - abs(z - (cz - 0.01)) / 0.08)
        rings.append((z, cy - bust * 0.5, rx + pad, ry + pad + bust * 0.5))
    ncy, nrx, nry = torso_ring(body, nz - 0.02, dom=dom)
    rings.append((nz - 0.025, ncy, nrx + 0.035, nry + 0.03))
    o = ring_shell(name, rings, color, seg=40, p=2.2)
    metal(o, color)
    conform_to(o, body, 0.008)
    for k in range(1, lames + 1):
        zz = bottom + 0.03 * k
        trim(o, lambda co, n, zz=zz: abs(co.z - zz) < 0.0035, shade(color, 0.55))
    solidify(o, 0.006)
    H.add_blend(o, chain_w([("hips", hz), ("spine", j["spine"].z), ("chest", cz)]))
    out = [o]
    if trim_color:
        for r, nm in ((rings[0], "cuirass_hem"),):
            t = band(nm, r, trim_color)
            H.add_blend(t, chain_w([("hips", hz), ("spine", j["spine"].z), ("chest", cz)]))
            out.append(t)
    return out


def gorget(H, body, color, cloth=None, trim_color=GOLD):
    """Padded collar (cloth) with a steel gorget over it, covering the neck base above the cuirass."""
    j = H.j
    dom = AB.dominant_bones(body)
    nz, sz = j["neck"].z, j["shoulder.L"].z
    ncy, nrx, nry = torso_ring(body, nz - 0.01, dom=dom)
    out = []
    if cloth:
        c = ring_shell("collar", [(sz - 0.04, ncy, nrx + 0.05, nry + 0.04), (nz + 0.035, ncy + 0.003, nrx + 0.012,
                                                                             nry + 0.012)], cloth, seg=32, p=2.0)
        AB.conform(c, body, 0.004)
        solidify(c, 0.006)
        H.add_blend(c, lambda co: {"chest": 0.6, "neck": 0.4})
        out.append(c)
    g = ring_shell("gorget", [(sz - 0.035, ncy, nrx + 0.075, nry + 0.06), (nz - 0.005, ncy + 0.002, nrx + 0.03,
                                                                           nry + 0.028)], color, seg=32, p=2.0)
    metal(g, color)
    if trim_color:
        edge_trim(g, trim_color, 0.008)
    solidify(g, 0.006)
    H.add("chest", g)
    out.append(g)
    return out


def chain_w(pts):
    from humanoid import chain
    return chain(pts)


def arm_frame(H, S):
    """(shoulder, up along the arm, outward, forward) unit frame for the upper arm."""
    j = H.j
    sh, el = j["shoulder." + S], j["elbow." + S]
    sx = 1 if S == "L" else -1
    u = (sh - el).normalized()
    f = Vector((0, -1, 0))
    f = (f - u * f.dot(u)).normalized()
    o = f.cross(u).normalized()       # right-handed (o, f, u); o points to +X
    return sh, u, o, f, (1 if o.x * sx > 0 else -1)


def pauldron(H, body, S, color, trim_color=GOLD, size=1.0, lames=2, spikes=0, horn=0.0):
    """Domed shoulder plate over the deltoid with overlapping lames below it."""
    from mathutils import Matrix
    j = H.j
    sh, u, ox, f, sg = arm_frame(H, S)
    o_ = ox * sg  # outward
    r_arm = limb_radius(body, "upper_arm." + S, sh, j["elbow." + S])
    R = (r_arm + 0.03) * size
    M = Matrix((ox, f, u)).transposed().to_4x4()   # local x=+X side, y=front, z=up the arm
    out = []
    for k in range(lames + 1):
        sc = 1.0 + 0.05 * k
        lo = -0.05 if k == 0 else -0.05 - 0.26 * k
        hi = 1.1 if k == 0 else lo + 0.50

        def cut(d, lo=lo, hi=hi, k=k):
            if k == 0:
                return d.z < lo or d.x * sg < -0.35
            return d.z < lo or d.z > hi or d.x * sg < -0.2
        piece = shell("pauldron", (0, 0, 0), 1.0, color, scale=(R * sc * 0.95, R * sc * 1.0, R * sc * 0.85), cut=cut,
                      thick=0.0, seg=32, rings=18)
        c = sh + u * (0.020 * size - 0.016 * k * size) + o_ * (0.012 + 0.004 * k)
        piece.data.transform(Matrix.Translation(c) @ M)
        piece.data.update()
        metal(piece, color)
        if trim_color:
            edge_trim(piece, trim_color, 0.010)
        solidify(piece, 0.006)
        H.add_blend(piece, lambda co, S=S: {"shoulder." + S: 0.35, "upper_arm." + S: 0.65})
        out.append(piece)
    for i in range(spikes):
        a = math.radians(-30 + 60 * i / max(1, spikes - 1)) if spikes > 1 else 0.0
        base = sh + u * (0.022 * size + R * 0.55) + o_ * (0.018 + R * 0.55) + f * (math.sin(a) * R * 0.5)
        tip = base + (u * 0.6 + o_ * 0.8).normalized() * (0.07 * size)
        sp = __import__("humanoid").cyl("pauldron_spike", base, tip, 0.016 * size, 0.001, color, seg=10)
        metal(sp, color)
        H.add_blend(sp, lambda co, S=S: {"shoulder." + S: 0.35, "upper_arm." + S: 0.65})
        out.append(sp)
    if horn:
        base = sh + u * (0.022 * size + R * 0.6) + o_ * 0.03
        pts = [base, base + u * 0.05 * horn + o_ * 0.03 * horn, base + u * 0.11 * horn + o_ * 0.02 * horn - f * 0.02]
        hn = sweep("pauldron_horn", pts, [(0.020, 0.020), (0.012, 0.012), (0.002, 0.002)], "#e8dcc0", seg=10)
        H.add_blend(hn, lambda co, S=S: {"shoulder." + S: 0.35, "upper_arm." + S: 0.65})
        out.append(hn)
    return out


def bracer(H, body, S, color, trim_color=None, reach=0.62, flare=1.25, gloves=None):
    """Forearm guard from the wrist up `reach` of the forearm, flaring at the elbow end."""
    from humanoid import along
    j = H.j
    w, e = j["wrist." + S], j["elbow." + S]
    r = limb_radius(body, "forearm." + S, w, e)
    p1 = w.lerp(e, reach)
    o = along("bracer", w - (e - w).normalized() * 0.012, p1,
              [(r * 1.02, 0.0), (r * 1.06, 0.5), (r * flare * 1.05, 1.0)], color, seg=20, caps=False)
    metal(o, color, shine=0.45)
    AB.conform(o, body, 0.004)
    if trim_color:
        trim(o, lambda co, n: (co - w).dot((e - w).normalized()) > (p1 - w).length - 0.016 or
             (co - w).dot((e - w).normalized()) < 0.0, trim_color)
    solidify(o, 0.004)
    H.add("forearm." + S, o)
    return o


def gauntlet(H, body, S, color, cuff_color=None, reach=0.55, offset=0.006):
    return bracer(H, body, S, color, trim_color=cuff_color, reach=reach)


def greaves(H, body, color, trim_color=None, top=None):
    """Steel boots to below the knee, a clean trim ring at the top and a knee cop on the knee."""
    j = H.j
    top = j["knee.L"].z - 0.04 if top is None else top
    dom = AB.dominant_bones(body)
    out = []
    for S in ("L", "R"):
        b = AB.boot(H, body, S, top, color, cuff_color=None)[0]
        metal(b, color, shine=0.5)
        out.append(b)
        k = j["knee." + S]
        pts = [body.matrix_world @ v.co for v in body.data.vertices
               if dom[v.index] in ("thigh." + S, "shin." + S) and abs((body.matrix_world @ v.co).z - k.z) < 0.02]
        front = min(p.y for p in pts) if pts else k.y - 0.05
        cop = ellipsoid("knee_cop", V((k.x, front + 0.006, k.z + 0.008)), (0.036, 0.010, 0.028), color, seg=18,
                        rings=10)
        metal(cop, shade(color, 0.9))
        H.add("shin." + S, cop)
        out.append(cop)
        if trim_color:
            zt = top - 0.012
            ps = [b.matrix_world @ v.co for v in b.data.vertices if abs((b.matrix_world @ v.co).z - zt) < 0.01]
            if ps:
                c = sum(ps, Vector()) / len(ps)
                ds = sorted(((p - c) * Vector((1, 1, 0))).length for p in ps)
                rr = ds[int(len(ds) * 0.6)] + 0.004
                from humanoid import ring
                t = ring("greave_trim", V((c.x, c.y, zt)), (0, 0, 1), rr, 0.006, trim_color, seg=28, minor=6)
                metal(t, trim_color, shine=0.65)
                H.add("shin." + S, t)
                out.append(t)
    AB.drop_faces(body, lambda co: co.z < top - 0.03)
    return out


# ---------------------------------------------------------------- cloth that hangs

def _extent(objs, z, band=0.045, skip_arms=None):
    """(max back y, max |x|) of all vertices of objs within band of z (skip_arms: body whose arm/head verts are
    ignored)."""
    back, half = -1.0, 0.0
    for o in objs:
        dom = AB.dominant_bones(o) if o is skip_arms else None
        M = o.matrix_world
        for v in o.data.vertices:
            co = M @ v.co
            if abs(co.z - z) > band:
                continue
            if dom is not None and part_of(dom[v.index]) not in _PROXY_PARTS:
                continue
            back = max(back, co.y)
            half = max(half, abs(co.x))
    return back, half


def cape(H, body, color, hem, trim_color=GOLD, width=1.0, wave=0.035, inner=None, collar=True, arc=78, over=(),
         jag=0.0):
    """Cape that sits on the shoulders (over pauldrons) and falls to `hem` with soft vertical folds; every ring
    is measured to clear the body and the garments in `over`."""
    j = H.j
    nz, sz = j["neck"].z, j["shoulder.L"].z
    dom = AB.dominant_bones(body)
    ncy, nrx, nry = torso_ring(body, nz - 0.02, dom=dom)
    ccy, crx, cry = torso_ring(body, sz - 0.04, dom=dom)
    shx = abs(j["shoulder.L"].x) + 0.07 * width
    objs = [body] + list(over)
    back0, _ = _extent(objs, sz - 0.06, skip_arms=body)
    H.add_bone("cape", (0, back0 * 0.6, sz), (0, back0 + 0.08, hem), "chest")
    n = 10
    rings = [(nz - 0.015, ncy + 0.004, nrx + 0.03, nry + 0.03),
             (sz + 0.005, ccy + 0.01, shx, cry + 0.05)]
    clear = 0.02
    prev_back = back0 + clear
    prev_rx = shx
    for i in range(1, n + 1):
        t = i / n
        z = sz + 0.005 + (hem - sz - 0.005) * t
        back, half = _extent(objs, z, skip_arms=body)
        back = max(back + clear, prev_back - 0.004)  # hangs straight: never tucks back in under a bulge
        prev_back = back
        rx = max(shx * (1 + 0.22 * t), half + 0.035, prev_rx)  # A-line: never narrows below a wide skirt
        prev_rx = rx
        cy = ccy
        rings.append((z, cy, rx, max(0.05, back - cy)))

    def folds(a, k):
        t = max(0.0, (k - 1) / n)
        return wave * t * math.cos(9 * a + 0.6 * math.sin(3 * a))
    o = ring_shell("cape", rings, color, seg=56, a0=180 - arc, a1=180 + arc, p=2.2, wave=folds)
    jag_hem(o, hem, jag, 11, ccy)
    # Hem sways a little; folds read as soft vertical shade stripes.
    lift = lambda a: 0.018 * math.sin(7 * a + 1.3)  # noqa: E731
    me = o.data
    for v in me.vertices:
        if v.co.z < hem + 0.01:
            v.co.z += lift(math.atan2(v.co.x, -(v.co.y - ccy)))
    attr = me.color_attributes["Col"]
    base, dark = rgb(color), rgb(shade(color, 0.78))
    for loop in me.loops:
        co = me.vertices[loop.vertex_index].co
        a = math.atan2(co.x, -(co.y - ccy))
        t = max(0.0, min(1.0, (sz - co.z) / max(sz - hem, 0.1)))
        f = 0.5 + 0.5 * math.cos(9 * a + 0.6 * math.sin(3 * a))
        k = (f > 0.72) * min(1.0, t * 2.2)
        c = tuple(base[i] + (dark[i] - base[i]) * k for i in range(3))
        attr.data[loop.index].color_srgb = (*c, 1.0)
    if inner:
        AB.paint_faces(o, lambda co, n_: inner if n_.y < -0.15 else None)
    if trim_color:
        trim(o, lambda co, n_: co.z < hem + 0.04 and co.z < hem + 0.022 + lift(math.atan2(co.x, -(co.y - ccy))),
             trim_color)
    solidify(o, 0.007)
    top = sz + 0.005

    def w(co):
        t = max(0.0, min(1.0, (top - co.z) / 0.12))
        return {"chest": 1 - t, "cape": t}
    H.add_blend(o, w)
    out = [o]
    if collar:
        c = ring_shell("cape_collar", [(nz - 0.045, ncy, nrx + 0.045, nry + 0.045), (nz + 0.015, ncy + 0.004,
                                       nrx + 0.03, nry + 0.032)], color, seg=32, a0=70, a1=290)
        if trim_color:
            trim(c, lambda co, n_: co.z > nz + 0.002, trim_color)
        solidify(c, 0.006)
        H.add("chest", c)
        out.append(c)
    return out


def panel(name, H, rings, color, a0, a1, trim_color=None, border=0.012, weights=None, seg=10):
    """Open cloth panel through rings (tabard, apron, coat tails) with a painted border."""
    o = ring_shell(name, rings, color, seg=seg, a0=a0, a1=a1, p=2.4)
    if trim_color:
        edge_trim(o, trim_color, border)
    solidify(o, 0.006)
    return o


def tabard(H, body, color, hem, trim_color=GOLD, emblem=None, width=26, back=True, top=None, over=()):
    """Front (and back) cloth panel from the belt to `hem`, gold border, optional emblem colour diamond."""
    from body import skirt_weights
    j = H.j
    hz = j["hip"].z
    top = hz + 0.04 if top is None else top
    dom = AB.dominant_bones(body)
    cy, rx, ry = torso_ring(body, hz, dom=dom)
    rings = []
    for i in range(6):
        t = i / 5
        z = top + (hem - top) * t
        rings.append((z, cy, rx + 0.02 + 0.03 * t, ry + 0.02 + 0.03 * t))
    out = []
    for a0, a1 in ((-width, width),) + (((180 - width, 180 + width),) if back else ()):
        o = panel("tabard", H, rings, color, a0, a1, trim_color)
        conform_to(o, body, 0.01, over, keep_outside=True)
        if emblem and a0 < 0:
            ez = top - 0.13
            AB.paint_faces(o, lambda co, n: emblem if abs(co.x) * 1.0 + abs(co.z - ez) * 0.8 < 0.03 else None)
        H.add_blend(o, skirt_weights(H, top, hem, 0.6, "hips"))
        out.append(o)
    return out


def tassets(H, body, color, trim_color=GOLD, length=0.16, plates=4):
    """Layered hip plates over the front/side of each thigh (open at the front centre and the back)."""
    j = H.j
    hz = j["hip"].z
    dom = AB.dominant_bones(body)
    cy, rx, ry = torso_ring(body, hz - 0.02, dom=dom, parts=("hips", "thigh"))
    out = []
    lames = max(2, min(4, plates - 1))
    step = length / lames
    for side in (1, -1):
        for k in range(lames):
            z0 = hz + 0.015 - k * step * 0.8
            a0, a1 = (18, 88) if side > 0 else (272, 342)
            o = B.skirt(H, z0, z0 - step * 1.25, rx + 0.016 + 0.006 * k, rx + 0.034 + 0.008 * k, color,
                        sy=(ry + 0.016) / (rx + 0.016), a0=a0, a1=a1, seg=8, rows=2, share=0.75, name="tasset",
                        thick=0.005, yshift=lambda zz, c=cy: c)
            metal(o, color)
            if trim_color:
                trim(o, lambda co, n, zz=z0 - step * 1.25: co.z < zz + 0.010, trim_color)
            out.append(o)
    return out


def robe_skirt(H, body, color, hem, flare=1.25, trim_color=GOLD, split=0, wave=0.04, top=None, name="robe",
               back_split=0, over=(), narrow=False):
    """Skirt/robe/coat tails measured from the hips: fitted at the waist, flaring to `hem` with folds.
    split opens the front by that many degrees (back_split the back). narrow=True measures the hips without the
    thigh verts, so the skirt flares from the hip line instead of from the width of both legs (a box)."""
    from body import skirt_weights
    j = H.j
    hz = j["hip"].z
    top = hz + 0.04 if top is None else top
    dom = AB.dominant_bones(body)
    parts0 = ("hips", "spine") if narrow else ("hips", "spine", "thigh")
    partsh = ("hips",) if narrow else ("hips", "thigh")
    cy0, rx0, ry0 = torso_ring(body, top, dom=dom, parts=parts0)
    cyh, rxh, ryh = torso_ring(body, hz - 0.03 if narrow else hz - 0.08, dom=dom, parts=partsh)
    n = 8
    rings = []
    for i in range(n + 1):
        t = i / n
        z = top + (hem - top) * t
        rx = (rx0 + 0.012) + ((max(rxh, rx0) + 0.02) * flare - rx0) * min(1.0, t * 1.6) ** 0.8
        ry = (ry0 + 0.012) + ((max(ryh, ry0) + 0.02) * flare - ry0) * min(1.0, t * 1.6) ** 0.8
        rings.append((z, cy0 + (cyh - cy0) * min(1.0, t * 1.6), rx, ry))

    def folds(a, k):
        return wave * (k / n) * math.cos(10 * a + 0.7 * math.sin(4 * a))
    a0, a1 = None, None
    if split and back_split:
        raise ValueError("one split per skirt")
    if split:
        a0, a1 = split / 2, 360 - split / 2
    if back_split:
        a0, a1 = -180 + back_split / 2, 180 - back_split / 2
    o = ring_shell(name, rings, color, seg=44, a0=a0, a1=a1, p=2.2, wave=folds)
    conform_to(o, body, 0.008, over, keep_outside=True)
    zgrad(o, hem, shade(color, 0.85), top, color)
    if trim_color:
        trim(o, lambda co, n_: co.z < hem + 0.026, trim_color)
    solidify(o, 0.006)
    H.add_blend(o, skirt_weights(H, top, hem, 0.8, "hips"))
    return o


def mantle(H, body, color, depth=0.10, trim_color=None, jag=0, offset=0.02, mats=None, fur=False):
    """Shoulder mantle/capelet: everything above the chest line pushed out; jag > 0 cuts a fur-like hem."""
    j = H.j
    z0 = j["shoulder.L"].z - depth
    top = j["neck"].z + 0.01

    def keep(co, bone):
        p = part_of(bone)
        return p in ("chest", "shoulder", "upper_arm", "neck", "spine") and z0 < co.z < top
    o = surface_shell("mantle", body, keep, color, offset=offset, thick=0.006 if not fur else 0.0, relax=10, mats=mats)
    if jag:
        bm = bmesh.new()
        bm.from_mesh(o.data)
        for v in bm.verts:
            if v.co.z < z0 + 0.03:
                a = math.atan2(v.co.x, -v.co.y)
                v.co.z -= jag * (0.5 + 0.5 * math.cos(a * 14))
        bm.to_mesh(o.data)
        bm.free()
    if fur:
        zgrad(o, z0 - jag, shade(color, 0.7), top, mix(color, "#ffffff", 0.15))
        solidify(o, 0.014)
    if trim_color:
        edge_trim(o, trim_color, 0.012)
    H.add_weighted(o)
    return o


def scarf(H, body, color, tail=0.25, trim_color=None):
    j = H.j
    nz = j["neck"].z
    o = lathe("scarf", [(0.060, nz - 0.03), (0.066, nz - 0.005), (0.062, nz + 0.02)], color, sy=0.9, seg=24,
              thick=0.016, caps=False, yshift=lambda zz: j["neck"].y)
    H.add("neck", o)
    if not tail:
        return [o]
    pts = [V((0.03, j["neck"].y + 0.06, nz - 0.01)), V((0.06, j["neck"].y + 0.10, nz - 0.08)),
           V((0.07, j["neck"].y + 0.11, nz - 0.08 - tail * 0.6)), V((0.06, j["neck"].y + 0.10, nz - 0.08 - tail))]
    t = sweep("scarf_tail", pts, [(0.04, 0.006), (0.045, 0.006), (0.05, 0.006), (0.045, 0.006)], color, seg=6,
              up=(0, 1, 0))
    H.add("chest", t)
    return [o, t]


# ---------------------------------------------------------------- headwear

def witch_hat(H, body, color, band="#a77a44", brim=1.0, height=1.0, gem=None, droop=0.30):
    c, half, top = head_box(H, body)
    cz = top - half.z * 0.42
    R = max(half.x, half.y) * 1.02
    out = []
    out.append(lathe("hat_brim", [(R * 0.9, -0.004), (R * 1.75 * brim, -0.012), (R * 1.82 * brim, -0.004),
                                  (R * 1.0, 0.012)], color, center=(c.x, c.y, cz), sy=0.92, seg=40, thick=0.007,
                     caps=False))
    h = 0.30 * height
    out.append(lathe("hat_crown", [(R * 1.02, 0.0), (R * 0.98, h * 0.18), (R * 0.72, h * 0.48), (R * 0.42, h * 0.78),
                                   (R * 0.14, h), (0.004, h * 1.02)], color, center=(c.x, c.y, cz), sy=0.95, seg=32,
                     xshift=lambda zz: droop * h * (zz / h) ** 3 * 0.6, yshift=lambda zz: droop * h * (zz / h) ** 3))
    out.append(lathe("hat_band", [(R * 1.03, 0.008), (R * 1.0, 0.045)], band, center=(c.x, c.y, cz), sy=0.95, seg=32,
                     caps=False, thick=0.005))
    zgrad(out[1], cz, shade(color, 0.85), cz + h, mix(color, "#ffffff", 0.12))
    if gem:
        out.append(ellipsoid("hat_gem", V((c.x, c.y - R * 0.98, cz + 0.026)), (0.016, 0.008, 0.018), gem, mat="M_Emit"))
    for o in out:
        H.add("head", o)
    return out


def _head_grid(name, cc, R, els, az_range, cols=52, bend=None):
    """Surface around the head in (azimuth, elevation): az_range(el) -> (a0, a1) degrees (0 = front, -Y), rows at
    elevations els (top first). bend(d, co) -> co reshapes it. Gives smooth opening edges where a cut sphere steps."""
    bm = bmesh.new()
    grid = []
    for el in els:
        a0, a1 = az_range(el)
        row = []
        ce, se = math.cos(math.radians(el)), math.sin(math.radians(el))
        for i in range(cols + 1):
            az = math.radians(a0 + (a1 - a0) * i / cols)
            d = V((math.sin(az) * ce, -math.cos(az) * ce, se))
            co = V((d.x * R.x, d.y * R.y, d.z * R.z))
            if bend:
                co = bend(d, co)
            row.append(bm.verts.new(cc + co))
        grid.append(row)
    for ra, rb in zip(grid, grid[1:]):
        for i in range(cols):
            bm.faces.new((ra[i], ra[i + 1], rb[i + 1], rb[i]))
    bmesh.ops.remove_doubles(bm, verts=bm.verts, dist=1e-5)
    bm.normal_update()
    for f in bm.faces:
        if f.normal.dot(f.calc_center_median() - cc) < 0:
            f.normal_flip()
    return A._from_bmesh(name, bm)


def _oval_window(aw, e_top, e_mid):
    """az_range for a face opening: closed above e_top, an oval up to aw degrees wide, open below e_mid."""
    def rng(el):
        if el >= e_top:
            ao = 0.0
        elif el <= e_mid:
            ao = aw
        else:
            t = (el - e_mid) / (e_top - e_mid)
            ao = aw * math.sqrt(max(0.0, 1 - t * t))
        return ao, 360 - ao
    return rng


def _head_weights(j):
    return lambda co: {"head": max(0.0, min(1.0, (co.z - (j["neck"].z - 0.02)) / 0.08)),
                       "chest": 1 - max(0.0, min(1.0, (co.z - (j["neck"].z - 0.02)) / 0.08))}


def hood(H, body, color, trim_color=None, open_front=0.75, drape=0.10, peak=0.0):
    """Hood over the hair with a clean oval face opening, falling onto the shoulders. open_front (0..1) widens the
    opening; peak pulls the crown back into a point."""
    c, half, top = skull_box(H, body)
    j = H.j
    R = V((half.x * 1.16 + 0.010, half.y * 1.12 + 0.010, half.z * 1.04 + 0.006))
    cc = V((c.x, c.y + half.y * 0.08, c.z + 0.004))
    els = [86 - (86 + 72) * k / 26 for k in range(27)]

    def bend(d, co):
        if d.z < 0:
            k = -d.z
            co = co + V((d.x * 0.30 * k * R.x, d.y * 0.18 * k * R.y + 0.02 * k, -drape * k))
        if peak and d.y > 0 and d.z > 0:
            co = co + V((0, peak * d.y * d.z, peak * 0.35 * d.z * d.y))
        return co
    o = _head_grid("hood", cc, R, els, _oval_window(38 + 34 * open_front, 34.0, -8.0), bend=bend)
    A.paint(o, color)
    zgrad(o, cc.z - R.z - drape, shade(color, 0.8), cc.z + R.z, color)
    if trim_color:
        edge_trim(o, trim_color, 0.012)
    solidify(o, 0.006)
    H.add_blend(o, _head_weights(j))
    return o


def helm(H, body, color, trim_color=GOLD, horns=0.0, wings=0.0, crest=None, horn_color="#e8dcc0"):
    """Open-faced helmet over the hair: domed skull, cheek guards, brow band; optional horns, wings or a crest."""
    c, half, top = skull_box(H, body)
    j = H.j
    R = V((half.x * 1.20 + 0.012, half.y * 1.14 + 0.012, half.z * 1.06 + 0.010))
    cc = V((c.x, c.y + half.y * 0.06, c.z + 0.006))
    els = [86 - (86 + 38) * k / 22 for k in range(23)]

    def bend(d, co):
        if d.z < 0:  # cheek guards and nape flare out a little
            co = co + V((d.x * 0.12 * -d.z * R.x, d.y * 0.10 * -d.z * R.y, 0))
        return co
    o = _head_grid("helm", cc, R, els, _oval_window(78, 40.0, 6.0), bend=bend)
    A.paint(o, color)
    metal(o, color, shine=0.6)
    if trim_color:
        edge_trim(o, trim_color, 0.010)
        trim(o, lambda co, n: abs(co.z - (cc.z + R.z * 0.70)) < 0.008, trim_color)
    solidify(o, 0.007)
    H.add_blend(o, _head_weights(j))
    out = [o]
    for s_ in (1, -1):
        if horns:
            p0 = cc + V((s_ * R.x * 0.80, 0.0, R.z * 0.55))
            pts = [p0, p0 + V((s_ * 0.06, 0.00, 0.03)) * horns, p0 + V((s_ * 0.10, -0.01, 0.10)) * horns,
                   p0 + V((s_ * 0.09, -0.02, 0.17)) * horns]
            hn = sweep("helm_horn", pts, [(0.024, 0.024), (0.019, 0.019), (0.011, 0.011), (0.001, 0.001)],
                       horn_color, seg=12)
            zgrad(hn, p0.z, shade(horn_color, 0.75), p0.z + 0.17 * horns, horn_color)
            H.add("head", hn)
            out.append(hn)
        if wings:
            p0 = cc + V((s_ * R.x * 0.95, 0.01, R.z * 0.15))
            for k in range(3):
                pts = [p0 + V((0, 0.01 * k, -0.02 * k)), p0 + V((s_ * 0.04, 0.03 + 0.01 * k, 0.04 - 0.02 * k)) * wings,
                       p0 + V((s_ * 0.05, 0.08 + 0.02 * k, 0.10 - 0.03 * k)) * wings]
                w = sweep("helm_wing", pts, [(0.016, 0.003), (0.020, 0.003), (0.003, 0.002)], trim_color or color,
                          seg=6, up=V((s_, 0, 0)))
                metal(w, trim_color or color, shine=0.65)
                H.add("head", w)
                out.append(w)
    if crest:
        pts = [cc + V((0, -R.y * 0.6, R.z * 0.85)), cc + V((0, 0, R.z * 1.12)), cc + V((0, R.y * 0.9, R.z * 0.95)),
               cc + V((0, R.y * 1.5, R.z * 0.35))]
        cr = sweep("helm_crest", pts, [(0.010, 0.030), (0.012, 0.045), (0.012, 0.040), (0.004, 0.015)], crest, seg=8,
                   up=V((0, 0, 1)))
        H.add("head", cr)
        out.append(cr)
    return out


def mask(H, body, color, trim_color=None):
    """Cloth mask over the mouth and nose (assassins)."""
    c, half, top = skull_box(H, body)
    j = H.j
    R = V((half.x * 1.06 + 0.006, half.y * 1.05 + 0.008, half.z * 1.0))
    cc = V((c.x, c.y, c.z))
    els = [-26 - 44 * k / 10 for k in range(11)]
    o = _head_grid("mask", cc, R, els, lambda el: (-78, 78), cols=24,
                   bend=lambda d, co: co + V((0, -0.006, 0)) if d.z > -0.3 else co + V((d.x * 0.1 * R.x, -0.01, 0)))
    A.paint(o, color)
    if trim_color:
        edge_trim(o, trim_color, 0.008)
    solidify(o, 0.004)
    H.add_blend(o, _head_weights(j))
    return o


def brim_hat(H, body, color, band="#6a4630", feather="#c8323a", brim=1.0, tilt=8.0):
    """Wide-brimmed adventurer's hat with a rounded crown and a long feather sweeping back."""
    c, half, top = skull_box(H, body)
    R = max(half.x, half.y) * 1.08 + 0.01
    cz = top - half.z * 0.45
    h = 0.11
    out = [lathe("hat_brim", [(R * 0.9, -0.004), (R * 1.9 * brim, -0.016), (R * 1.95 * brim, -0.006), (R * 1.0, 0.010)],
                 color, center=(c.x, c.y, cz), sy=0.95, seg=40, thick=0.006, caps=False),
           lathe("hat_crown", [(R * 1.03, 0.0), (R * 1.0, h * 0.55), (R * 0.88, h * 0.9), (R * 0.5, h * 1.04), (0.004, h * 1.06)],
                 color, center=(c.x, c.y, cz), sy=0.92, seg=32),
           lathe("hat_band", [(R * 1.05, 0.006), (R * 1.03, 0.032)], band, center=(c.x, c.y, cz), sy=0.93, seg=32,
                 caps=False, thick=0.004)]
    zgrad(out[1], cz, shade(color, 0.8), cz + h, mix(color, "#ffffff", 0.1))
    if feather:
        p0 = V((c.x + R * 0.95, c.y + R * 0.1, cz + 0.02))
        pts = [p0, p0 + V((0.02, 0.06, 0.05)), p0 + V((0.02, 0.15, 0.09)), p0 + V((0.0, 0.24, 0.10))]
        f = sweep("hat_feather", pts, [(0.006, 0.002), (0.022, 0.003), (0.020, 0.003), (0.002, 0.001)], feather, seg=6,
                  up=V((1, 0, 0)))
        zgrad(f, 0, feather, 1, feather)
        out.append(f)
    import mathutils
    rot = mathutils.Matrix.Rotation(math.radians(-tilt), 4, "X")
    piv = V((c.x, c.y, cz))
    for o in out:
        o.data.transform(mathutils.Matrix.Translation(piv) @ rot @ mathutils.Matrix.Translation(-piv))
        H.add("head", o)
    return out


def mitre(H, body, color="#fbf6ea", trim_color=GOLD, height=0.20, emblem=GOLD):
    """Tall pointed cleric's mitre (front view an arch, side view narrow) with gold bands and a cross."""
    c, half, top = skull_box(H, body)
    R = max(half.x, half.y) * 1.02 + 0.006
    cz = top - half.z * 0.40
    prof = [(R * 1.02, 0.0)] + [(R * max(0.02, 1.0 - (t ** 1.8)) * (1.0 + 0.18 * math.sin(math.pi * t)), height * t)
                               for t in [k / 10 for k in range(1, 11)]]
    o = lathe("mitre", prof, color, center=(c.x, c.y, cz), sx=1.0, sy=0.62, seg=40)
    zgrad(o, cz, shade(color, 0.85), cz + height, color)
    if trim_color:
        trim(o, lambda co, n: co.z < cz + 0.018 or (abs(co.x - c.x) < 0.010 and co.z < cz + height * 0.8), trim_color)
    H.add("head", o)
    out = [o]
    if emblem:
        fc = V((c.x, c.y - R * 0.66, cz + height * 0.42))
        for sz_ in ((0.012, 0.006, 0.05), (0.034, 0.006, 0.012)):
            b = A.box("mitre_cross", sz_, loc=fc + V((0, 0, 0.008 if sz_[0] > 0.02 else 0)), color=emblem, bevel=0.002)
            A.apply_transform(b)
            metal(b, emblem, shine=0.7)
            H.add("head", b)
            out.append(b)
    return out


def wings(H, body, color="#fbf8f0", tip=None, span=1.0, folded=0.0):
    """Feathered wings on the back: primaries from the wrist, secondaries along the arm, coverts on top, as layered
    flat feather cards with a tip colour. folded > 0 sweeps them back closer to the body."""
    j = H.j
    dom = AB.dominant_bones(body)
    cz = j["chest"].z
    cy, rx, ry = torso_ring(body, cz, dom=dom)
    out = []
    for s_ in (1, -1):
        root = V((s_ * 0.05, cy + ry + 0.03, cz + 0.04))
        o_dir = V((s_, 0.55 + 0.6 * folded, 0.0)).normalized()
        u_dir = V((0, 0.30, 1.0)).normalized()
        n_dir = o_dir.cross(u_dir).normalized()
        wrist = root + o_dir * 0.30 * span * (1 - 0.4 * folded) + u_dir * 0.20 * span
        bm = bmesh.new()
        cols = []
        layer = [0]

        def feather(origin, ang, length, width, col):
            d = (o_dir * math.cos(math.radians(ang)) + u_dir * math.sin(math.radians(ang))).normalized()
            w = n_dir.cross(d).normalized()
            off = n_dir * (0.0035 * layer[0] * s_)
            layer[0] += 1
            mid, left, right = [], [], []
            for k in range(7):
                t = k / 6
                hw = width * (math.sin(math.pi * min(1.0, t * 1.15)) ** 0.6) * (1 - 0.35 * t)
                p = origin + d * length * t + off
                mid.append(bm.verts.new(p + n_dir * 0.004 * s_ * math.sin(math.pi * t)))
                left.append(bm.verts.new(p + w * hw))
                right.append(bm.verts.new(p - w * hw))
            for k in range(6):
                for a_, b_ in ((left, mid), (mid, right)):
                    bm.faces.new((a_[k], a_[k + 1], b_[k + 1], b_[k]))
                    cols.append((col, k / 5))
        n1, n2, n3 = 7, 7, 6
        for k in range(n1):
            feather(wrist - (wrist - root) * 0.06 * k, 30 - 16 * k, 0.46 * span * (1 - 0.05 * k), 0.075 * span, 1)
        for k in range(n2):
            t = 0.80 - 0.75 * k / (n2 - 1)
            feather(root + (wrist - root) * t, -88 - 3 * k, 0.32 * span * (1 - 0.04 * k), 0.07 * span, 1)
        for k in range(n3):
            t = 0.95 - 0.85 * k / (n3 - 1)
            feather(root + (wrist - root) * t + u_dir * 0.015, -70 - 4 * k, 0.16 * span, 0.06 * span, 0)
        o = A._from_bmesh("wing", bm)
        A.paint(o, color)
        me = o.data
        attr = me.color_attributes["Col"]
        base, dark, tp = rgb(color), rgb(shade(color, 0.86)), rgb(tip or color)
        for poly, (kind, t) in zip(me.polygons, cols):
            if tip and t > 0.75:
                c_ = tp
            else:
                c_ = dark if kind == 0 else base
            for li in poly.loop_indices:
                attr.data[li].color_srgb = c_
        solidify(o, 0.004)
        H.add("chest", o)
        out.append(o)
    return out


def rune_ring(H, center, axis, R, color, bone="chest", ticks=16, inner=0.78):
    """Floating emissive magic circle: two thin rings and rune marks between them."""
    from humanoid import ring
    axis = V(axis).normalized()
    out = [ring("rune_ring", center, axis, R, 0.004, color, seg=56, minor=5, mat="M_Emit"),
           ring("rune_ring_in", center, axis, R * inner, 0.003, color, seg=48, minor=5, mat="M_Emit")]
    a = axis.orthogonal().normalized()
    b = axis.cross(a).normalized()
    for k in range(ticks):
        ang = 2 * math.pi * k / ticks
        p = center + (a * math.cos(ang) + b * math.sin(ang)) * R * (1 + inner) / 2
        e = ellipsoid("rune", p, (0.008, 0.008, 0.008), color, mat="M_Emit", seg=4, rings=2)
        out.append(e)
    for o in out:
        H.add(bone, o)
    return out


def orbs(H, colors, radius=0.32, z=None, size=0.042):
    """Elemental orbs floating around the waist (fixed to the hips so they follow the body)."""
    j = H.j
    z = j["hip"].z + 0.18 if z is None else z
    out = []
    n = len(colors)
    for k, col in enumerate(colors):
        ang = math.radians(-60 + 300 * k / max(1, n - 1))
        p = V((math.sin(ang) * radius, -math.cos(ang) * radius * 0.6 + 0.04, z + 0.06 * math.sin(3 * ang)))
        core = ellipsoid("orb", p, (size, size, size), col, mat="M_Emit", seg=16, rings=10)
        from humanoid import ring
        halo_ = ring("orb_ring", p, V((0.3, 0.2, 1.0)), size * 1.7, 0.003, mix(col, "#ffffff", 0.4), seg=24, minor=4,
                     mat="M_Emit")
        H.add("hips", core, halo_)
        out += [core, halo_]
    return out


def talismans(H, body, paper="#f4ecd8", ink="#b02a2a", n=5, z=None):
    """Paper charms hanging from the belt (exorcist)."""
    j = H.j
    z = j["hip"].z + 0.04 if z is None else z
    cy, rx, ry = torso_ring(body, z, dom=AB.dominant_bones(body), parts=("hips", "spine", "thigh"))
    out = []
    for k in range(n):
        p = V((math.sin(math.radians(-60 + 120 * k / (n - 1))) * (rx + 0.03),
               cy - math.cos(math.radians(-60 + 120 * k / (n - 1))) * (ry + 0.03), z))
        b = A.box("talisman", (0.030, 0.003, 0.10), loc=p + V((0, 0, -0.06)), color=paper)
        A.apply_transform(b)
        AB.paint_faces(b, lambda co, n_, p=p: ink if abs(co.z - (p.z - 0.06)) < 0.025 and abs(co.x - p.x) < 0.008
                       else None)
        H.add_blend(b, lambda co: {"hips": 0.6, "thigh.L" if co.x > 0 else "thigh.R": 0.4})
        out.append(b)
    return out


def grimoire(H, body, cover="#3a1e4a", trim_color=GOLD, side=1, glow=None):
    """A spellbook on a chain at the hip."""
    j = H.j
    hz = j["hip"].z
    cy, rx, ry = torso_ring(body, hz, dom=AB.dominant_bones(body), parts=("hips", "spine", "thigh"))
    p = V((side * (rx + 0.04), cy + 0.01, hz - 0.03))
    bk = A.box("grimoire", (0.022, 0.085, 0.11), loc=p, color=cover, bevel=0.004)
    A.apply_transform(bk)
    pages = A.box("grimoire_pages", (0.016, 0.078, 0.10), loc=p + V((0, -0.006, 0)), color="#efe6cc")
    A.apply_transform(pages)
    out = [bk, pages]
    if trim_color:
        AB.paint_faces(bk, lambda co, n: trim_color if abs(co.y - p.y) > 0.036 or abs(co.z - p.z) > 0.048 else None)
    if glow:
        g = ellipsoid("grimoire_gem", p + V((side * 0.013, 0, 0)), (0.004, 0.014, 0.014), glow, mat="M_Emit", seg=10,
                      rings=6)
        out.append(g)
    for o in out:
        H.add_blend(o, lambda co: {"hips": 0.5, "thigh.L" if side > 0 else "thigh.R": 0.5})
    return out


def circlet(H, body, color=GOLD, gem=None, wings=0.0, z=0.55):
    """Thin metal band around the brow; wings > 0 adds swept ornaments at the temples."""
    c, half, top = skull_box(H, body)
    cz = c.z + half.z * (z - 0.5) * 0.9
    o = lathe("circlet", [(1.0, -0.006), (1.0, 0.006)], color, center=(c.x, c.y, cz), sx=half.x * 1.04,
              sy=half.y * 1.06, seg=40, thick=0.005, caps=False)
    metal(o, color, shine=0.6)
    H.add("head", o)
    out = [o]
    if gem:
        out.append(ellipsoid("circlet_gem", V((c.x, c.y - half.y * 1.07, cz + 0.004)), (0.012, 0.006, 0.016), gem,
                             mat="M_Emit"))
        H.add("head", out[-1])
    if wings:
        for s in (-1, 1):
            p0 = V((c.x + s * half.x * 1.02, c.y - half.y * 0.2, cz))
            pts = [p0, p0 + V((s * 0.02, 0.02, 0.03 * wings)), p0 + V((s * 0.03, 0.05, 0.07 * wings))]
            w = sweep("circlet_wing", pts, [(0.012, 0.003), (0.018, 0.003), (0.004, 0.002)], color, seg=6,
                      up=V((s, 0, 0)))
            metal(w, color, shine=0.6)
            H.add("head", w)
            out.append(w)
    return out


def halo(H, body, color="#ffe9a0", r=0.13, lift=0.10):
    c, half, top = skull_box(H, body)
    from humanoid import ring
    o = ring("halo", V((c.x, c.y + half.y * 0.6, top + lift * 0.3)), V((0, 0.35, 1)), r, 0.006, color, seg=40,
             minor=6, mat="M_Emit")
    H.add("head", o)
    return o


def stole(H, body, color, length=0.42, trim_color=GOLD, width=0.045, emblem=None, start=None):
    """Priest's stole: two strips from behind the neck down the front of the chest."""
    j = H.j
    nz = j["neck"].z
    dom = AB.dominant_bones(body)
    out = []
    for s_ in (1, -1):
        pts = []
        for k in range(6):
            t = k / 5
            z0 = nz - 0.02 if start is None else start
            z = z0 - length * t
            cy, rx, ry = torso_ring(body, z, dom=dom)
            x = s_ * (0.045 + 0.02 * t)
            front = min((body.matrix_world @ v.co).y for v in body.data.vertices
                        if abs((body.matrix_world @ v.co).z - z) < 0.015 and abs((body.matrix_world @ v.co).x - x) < 0.02
                        and part_of(dom[v.index]) in TORSO + ("thigh",)) if True else cy - ry
            pts.append(V((x, front - 0.008, z)))
        ws = [width * (0.8 + 0.35 * k / (len(pts) - 1)) for k in range(len(pts))]
        o = sweep("stole", pts, [(w_, 0.004) for w_ in ws], color, seg=8, up=(0, -1, 0))
        if trim_color:
            def side(co, n, pts=pts, ws=ws):
                k = min(range(len(pts)), key=lambda i: abs(pts[i].z - co.z))
                return trim_color if abs(co.x - pts[k].x) > ws[k] * 0.72 or co.z < pts[-1].z + 0.012 else None
            AB.paint_faces(o, side)
        if emblem:
            e = pts[-2]
            AB.paint_faces(o, lambda co, n, e=e: emblem if (abs(co.x - e.x) < 0.012 and abs(co.z - e.z) < 0.03) or
                           (abs(co.z - e.z - 0.008) < 0.006 and abs(co.x - e.x) < 0.024) else None)
        from humanoid import chain
        H.add_blend(o, chain([("hips", j["hip"].z), ("spine", j["spine"].z), ("chest", j["chest"].z)]))
        out.append(o)
    return out


def jag_hem(o, hem, jag, teeth=16, cy=0.0):
    """Saw-tooth hem (fur, tattered cloth): lowers the bottom ring in alternating points."""
    if not jag:
        return o
    for v in o.data.vertices:
        if v.co.z < hem + 0.012:
            a = math.atan2(v.co.x, -(v.co.y - cy))
            f = (a * teeth / (2 * math.pi)) % 1.0
            v.co.z -= jag * (1 - abs(2 * f - 1))
    return o


def capelet(H, body, color, depth=0.12, trim_color=GOLD, flare=0.035, wave=0.02, inner=None, front_open=0,
            over=(), jag=0.0, teeth=18):
    """Short cape around the shoulders, measured from the body including the upper arms, with a clean hem."""
    j = H.j
    nz, sz = j["neck"].z, j["shoulder.L"].z
    dom = AB.dominant_bones(body)
    ncy, nrx, nry = torso_ring(body, nz - 0.01, dom=dom)
    hem = sz - depth
    zs = [nz - 0.005, sz + 0.03, sz - 0.01] + [sz - 0.01 - (depth - 0.01) * t for t in (0.35, 0.7, 1.0)]
    rings = [(zs[0], ncy, nrx + 0.022, nry + 0.022)]
    objs = [body] + list(over)
    for k, z in enumerate(zs[1:]):
        xs, ys = [], []
        for o in objs:
            M = o.matrix_world
            for v in o.data.vertices:
                co = M @ v.co
                if abs(co.z - z) < 0.02 and (o is not body or part_of(dom[v.index]) not in ("hand", "head")):
                    xs.append(abs(co.x))
                    ys.append(co.y)
        t = k / (len(zs) - 2)
        rx = max(xs) + 0.02 + flare * t
        y0, y1 = min(ys), max(ys)
        rings.append((z, (y0 + y1) / 2, rx, (y1 - y0) / 2 + 0.02 + flare * t * 0.6))

    def folds(a, k):
        return wave * (k / len(zs)) * math.cos(12 * a)
    a0, a1 = (None, None) if not front_open else (front_open / 2, 360 - front_open / 2)
    o = ring_shell("capelet", rings, color, seg=72 if jag else 56, a0=a0, a1=a1, p=2.0, wave=folds)
    jag_hem(o, hem, jag, teeth, ncy)
    zgrad(o, hem - jag, shade(color, 0.80 if jag else 0.86), nz, color)
    if inner:
        AB.paint_faces(o, lambda co, n_: inner if n_.dot(Vector((co.x, co.y - ncy, 0)).normalized()) < -0.2 else None)
    if trim_color:
        trim(o, lambda co, n_: co.z < hem + 0.02, trim_color)
    # Drape: snap onto the shoulders (body incl. arms) at the top, letting the hem hang free.
    snap = body.copy()
    snap.data = body.data.copy()
    snap.modifiers.clear()
    bpy.context.scene.collection.objects.link(snap)
    vg = o.vertex_groups.new(name="drape")
    for v in o.data.vertices:
        t = max(0.0, min(1.0, (v.co.z - hem) / max(nz - hem, 1e-3)))
        vg.add([v.index], 0.25 + 0.75 * t ** 0.7, "REPLACE")
    md = o.modifiers.new("drape", "SHRINKWRAP")
    md.target = snap
    md.wrap_method = "NEAREST_SURFACEPOINT"
    md.wrap_mode = "ABOVE_SURFACE"
    md.offset = 0.014
    md.vertex_group = "drape"
    A.apply_modifiers(o)
    bpy.data.objects.remove(snap)
    if "drape" in o.vertex_groups:
        o.vertex_groups.remove(o.vertex_groups["drape"])
    AB.conform(o, body, 0.012)
    AB.relax(o, 6)
    solidify(o, 0.006)
    H.add_blend(o, lambda co: {"chest": 1.0})
    return o


def pendant(H, over, z, color=GOLD, gem=None, size=0.05, shape="cross"):
    """A flat cross/medallion hanging on the chest in front of `over` (list of objects) at height z."""
    front = min((o.matrix_world @ v.co).y for o in over for v in o.data.vertices
                if abs((o.matrix_world @ v.co).z - z) < 0.02 and abs((o.matrix_world @ v.co).x) < 0.03)
    c = V((0, front - 0.008, z))
    out = []
    if shape == "cross":
        for sz_ in ((size * 0.28, 0.008, size), (size * 0.75, 0.008, size * 0.26)):
            b = A.box("pendant", sz_, loc=c + V((0, 0, size * 0.18 if sz_[0] > size * 0.5 else 0)), color=color,
                      bevel=0.003, seg=2)
            A.apply_transform(b)
            metal(b, color, shine=0.7)
            out.append(b)
    else:
        b = ellipsoid("medallion", c, (size * 0.5, 0.008, size * 0.5), color, seg=20, rings=8)
        metal(b, color, shine=0.7)
        out.append(b)
    if gem:
        out.append(ellipsoid("pendant_gem", c + V((0, -0.006, size * 0.1)), (0.009, 0.005, 0.009), gem, mat="M_Emit"))
    for b in out:
        H.add("chest", b)
    return out


def glow_band(H, bone, ring, color, h=0.006, out=0.008, p=2.4, a0=None, a1=None):
    """Thin emissive band around a measured ring (abyss/holy runes)."""
    z, cy, rx, ry = ring
    o = lathe("glow", [(superellipse(rx + out, ry + out, p), z - h / 2), (superellipse(rx + out, ry + out, p), z + h / 2)],
              color, seg=40, caps=False, yshift=lambda zz: cy, a0=a0, a1=a1, mat="M_Emit")
    solidify(o, 0.003)
    H.add(bone, o) if isinstance(bone, str) else H.add_blend(o, bone)
    return o


def bare_arms(body, upper=True):
    """Removes the sleeves (all of them, or only the forearms when upper=False)."""
    keep_parts = ("forearm", "hand") if upper else ("forearm", "hand")
    drop_where(body, "Tops", lambda co, bone: part_of(bone) in (("upper_arm", "forearm", "hand", "shoulder") if upper
                                                                else ("forearm", "hand")))
