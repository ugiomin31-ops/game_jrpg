"""Modern clothes and accessories for the Korean hunters (jackets, coats, vests, caps, glasses, headsets, bags,
armbands, ties, ...).

Same method as garments.py: every piece is measured on the VRoid body (torso rings, head boxes, eye positions),
conformed to it and given the body's weights (chain weights for torso pieces, the body's own for sleeve shells),
so the clothes bend with the hunter. Helpers only add to the outfit; the caller decides what the hoodie keeps.
"""
import math

from mathutils import Matrix, Vector

import abyss_bpy as A
import anime_body as AB
import body as B
import garments as G
from humanoid import V, along, cyl, ellipsoid, lathe, ring, solidify, sweep

GOLD = G.GOLD
SILVER = "#c8d2dc"


# ---------------------------------------------------------------- measuring

def _front_at(body, z, x=0.0, extra=0.0):
    """World y of the torso front at height z and lateral x (negative = in front of the body)."""
    cy, rx, ry = G.torso_ring(body, z)
    k = math.sqrt(max(0.0, 1.0 - min(1.0, abs(x) / max(rx, 1e-3)) ** 2))
    return cy - ry * k - extra


def _face_front(body, z, half_x=0.11):
    """Front-most y of the head (skin and hair without long strands) at height z."""
    dom = AB.dominant_bones(body)
    me = body.data
    ys = [(body.matrix_world @ v.co).y for v in me.vertices if dom[v.index] == "head"
          and abs((body.matrix_world @ v.co).z - z) < 0.012 and abs((body.matrix_world @ v.co).x) < half_x]
    return min(ys) if ys else -0.09


def _arm_t(H, co):
    """Fraction (0 shoulder, 1 wrist) at which co projects onto the arm nearest to it."""
    j = H.j
    best_perp, best_t = 1e9, 1.0
    for S in ("L", "R"):
        sh, wr = j["shoulder." + S], j["wrist." + S]
        d = wr - sh
        t = (co - sh).dot(d) / d.dot(d)
        perp = (co - (sh + d * t)).length
        if perp < best_perp:
            best_perp, best_t = perp, t
    return best_t


def _arm_near(H, co, S_list, ts, reach=0.02):
    """True when co lies on the arm (each side listed) at one of the fractions ts along shoulder->wrist."""
    j = H.j
    for S in S_list:
        sh, wr = j["shoulder." + S], j["wrist." + S]
        d = wr - sh
        s = (co - sh).dot(d) / d.dot(d)
        perp = (co - (sh + d * s)).length
        for t in ts:
            if abs(s - t) < reach and perp < 0.11:
                return True
    return False


# ---------------------------------------------------------------- torso layers

def jacket(H, body, color, hem=None, top=None, split=40, flare=0.0, pad=0.024, trim_color=None, lining=None,
           name="jacket", seg=44):
    """Open jacket or coat over the torso: rings measured from the collar to the hem, a front opening of `split`
    degrees (0 = closed), `flare` widens the hem (long coats). The arms stay as the hoodie sleeves unless the
    caller builds sleeves() first. lining colours the inside of the opening."""
    j = H.j
    hz, nz = j["hip"].z, j["neck"].z
    top = nz - 0.035 if top is None else top
    hem = hz - 0.12 if hem is None else hem
    dom = AB.dominant_bones(body)
    rings = []
    zs = [top + (hem - top) * t for t in (0.0, 0.2, 0.45, 0.7, 1.0)]
    for i, z in enumerate(zs):
        cy, rx, ry = G.torso_ring(body, z, dom=dom)
        grow = pad + flare * (i / (len(zs) - 1)) * 0.5
        rings.append((z, cy, rx + grow, ry + grow))
    a0, a1 = (split / 2, 360 - split / 2) if split else (None, None)
    o = G.ring_shell(name, rings, color, seg=seg, a0=a0, a1=a1, p=2.3)
    G.conform_to(o, body, 0.010, keep_outside=True)
    solidify(o, 0.007)
    if lining and split:
        cy = rings[len(rings) // 2][1]

        def inner(co, n):
            return lining if n.dot(Vector((co.x, co.y - cy, 0.0))) < -0.2 else None
        AB.paint_faces(o, inner)
    if trim_color:
        G.edge_trim(o, trim_color, 0.010)
    H.add_blend(o, G.chain_w([("hips", hz), ("spine", j["spine"].z), ("chest", j["chest"].z)]))
    return o


def vest(H, body, color, trim_color=None, pad=0.022, open_front=26, pockets=0, plates=None, name="vest"):
    """Sleeveless vest or plate carrier over the torso: pockets are boxes on the chest, plates a rectangle of a
    second colour over the sternum."""
    j = H.j
    hz, sz = j["hip"].z, j["shoulder.L"].z
    top, hem = sz - 0.030, hz + 0.02
    dom = AB.dominant_bones(body)
    zs = [top + (hem - top) * t for t in (0.0, 0.35, 0.7, 1.0)]
    rings = []
    for z in zs:
        cy, rx, ry = G.torso_ring(body, z, dom=dom)
        rings.append((z, cy, rx + pad, ry + pad))
    a0, a1 = (open_front / 2, 360 - open_front / 2) if open_front else (None, None)
    o = G.ring_shell(name, rings, color, seg=44, a0=a0, a1=a1, p=2.4)
    G.conform_to(o, body, 0.008, keep_outside=True)
    solidify(o, 0.006)
    if trim_color:
        G.edge_trim(o, trim_color, 0.008)
    H.add_blend(o, G.chain_w([("hips", hz), ("spine", j["spine"].z), ("chest", j["chest"].z)]))
    out = [o]
    zc = sz - 0.085
    for k in range(pockets):
        x = (-0.075 if k % 2 == 0 else 0.075) if pockets > 1 else 0.0
        y = _front_at(body, zc, x, pad + 0.004)
        b = A.box("pocket", (0.072, 0.016, 0.080), loc=(x, y, zc - 0.02 * (k // 2)), color=color, bevel=0.004, seg=2)
        A.apply_transform(b)
        H.add("chest", b)
        out.append(b)
    if plates:
        y = _front_at(body, sz - 0.11, 0.0, pad + 0.006)
        p = A.box("plate", (0.19, 0.020, 0.25), loc=(0.0, y, sz - 0.12), color=plates, bevel=0.010, seg=2)
        A.apply_transform(p)
        H.add("chest", p)
        out.append(p)
    return out


def poncho(H, body, color, hem=None, pad=0.05, trim_color=None):
    """A closed cape-like poncho from the collar to the hip, wider at the hem."""
    j = H.j
    return jacket(H, body, color, hem=hem if hem is not None else j["hip"].z - 0.06, top=j["neck"].z - 0.005,
                  split=0, flare=0.35, pad=pad, trim_color=trim_color, name="poncho", seg=48)


def sleeves(H, body, color, bands=(), band_color=None):
    """Jacket sleeves as two tapered tubes per arm (upper arm rigid to upper_arm, forearm rigid to forearm), sized
    from the measured limb radius; the hoodie's arm faces are then removed from the body. The wrist stays bare.
    bands: fractions along shoulder->wrist painted as thin rings in band_color. Returns the sleeve objects."""
    j = H.j
    out = []
    radii = {}
    for S in ("L", "R"):
        sh, el, wr = j["shoulder." + S], j["elbow." + S], j["wrist." + S]
        ru = G.limb_radius(body, "upper_arm." + S, sh, el) * 1.05 + 0.007
        rf = G.limb_radius(body, "forearm." + S, el, wr) * 1.05 + 0.006
        radii[S] = (ru, rf)
        up = along("sleeve_upper", sh, el, [(ru * 0.92, 0.0), (ru, 0.14), (ru * 1.02, 0.5), (ru * 0.98, 0.9),
                                            (ru * 1.02, 1.0)], color, seg=24)
        lo = along("sleeve_lower", el, el.lerp(wr, 0.92), [(rf * 1.02, 0.0), (rf, 0.5), (rf * 0.90, 1.0)], color,
                   seg=24)
        H.add("upper_arm." + S, up)
        H.add("forearm." + S, lo)
        out += [up, lo]
        for t in bands:
            if band_color is None:
                break
            on_upper = t < 0.5
            a0, a1, r = (sh, el, ru) if on_upper else (el, wr, rf)
            tt = t / 0.5 if on_upper else (t - 0.5) / 0.5
            ring_o = ring("sleeve_band", a0.lerp(a1, tt), (a1 - a0).normalized(), r * 1.03, 0.007, band_color,
                          seg=28, minor=6)
            H.add("upper_arm." + S if on_upper else "forearm." + S, ring_o)
            out.append(ring_o)
    G.drop_where(body, "Tops", lambda co, bone: G.part_of(bone) in ("upper_arm", "forearm"))
    return out


def camo(o, colors, scale=1.0):
    """Blotchy camouflage painted on the faces of a garment (deterministic, from the face centres)."""
    def fn(co, n):
        a = math.sin(co.x * 29.0 * scale + 1.3 * math.sin(co.z * 11.0)) + math.sin(co.z * 23.0 + co.y * 17.0)
        return colors[int(abs(math.sin(2.7 * a)) * len(colors)) % len(colors)]
    AB.paint_faces(o, fn)
    return o


def buttons(H, body, zs, color, x=0.0, pad=0.03, r=0.008):
    out = []
    for z in zs:
        y = _front_at(body, z, x, pad)
        out.append(H.add("chest", ellipsoid("button", V((x, y, z)), (r, 0.005, r), color, seg=10, rings=6)))
    return out


def belt_pouch(H, body, color, side=1, flap=None, button=None):
    """A utility pouch hanging from the hip on one side (body.pouch keeps the hips bone)."""
    hz = H.j["hip"].z
    cy, rx, ry = G.torso_ring(body, hz + 0.02)
    return B.pouch(H, (side * (rx * 0.82), cy - ry * 0.05, hz - 0.035), (0.07, 0.05, 0.07), color, flap=flap,
                   rot_z=0.0, button=button)


def bag(H, body, color, strap, side=1):
    """Shoulder bag (messenger or delivery bag) on one hip with its strap across the chest."""
    j = H.j
    hz, sz = j["hip"].z, j["shoulder.L"].z
    cy, rx, ry = G.torso_ring(body, hz + 0.04)
    b = A.box("bag", (0.12, 0.06, 0.20), loc=(side * (rx + 0.035), cy, hz - 0.06), color=color, bevel=0.012, seg=2)
    A.apply_transform(b)
    f = _front_at(body, sz - 0.06, 0.0, 0.02)
    pts = [V((side * (rx + 0.02), cy, hz + 0.05)), V((side * (rx * 0.5), f - 0.01, hz + 0.25)),
           V((-side * (rx * 0.6), f - 0.012, sz - 0.02)), V((-side * (rx * 0.9), cy, sz + 0.02))]
    s = sweep("bag_strap", pts, [(0.012, 0.004)] * 4, strap, seg=6, up=V((0, -1, 0)))
    H.add("hips", b)
    H.add("chest", s)
    return [b, s]


def tie(H, body, color, length=0.20, loosen=0.0):
    """Necktie hanging from the collar; loosen tilts the tail to one side (a loosened tie)."""
    j = H.j
    nz = j["neck"].z
    f = _front_at(body, nz - 0.05, 0.0, 0.012)
    top = V((0.0, f, nz - 0.03))
    pts = [top, top + V((0.0, -0.004, -0.06)), top + V((loosen, -0.008, -0.14)), top + V((loosen * 1.2, -0.010, -length))]
    t = sweep("tie", pts, [(0.012, 0.004), (0.019, 0.005), (0.023, 0.005), (0.016, 0.004)], color, seg=8,
              up=V((0, -1, 0)))
    knot = ellipsoid("tie_knot", top + V((0.0, -0.004, 0.008)), (0.016, 0.012, 0.016), color, seg=10, rings=6)
    H.add("chest", t, knot)
    return [t, knot]


def ribbon(H, body, color, z, side=0.0):
    """Two long ribbon tails (goreum) hanging from the chest, a small bow at the top."""
    f = _front_at(body, z, 0.0, 0.016)
    out = []
    for s in (-1, 1):
        pts = [V((side + s * 0.012, f, z)), V((side + s * 0.03, f - 0.01, z - 0.10)),
               V((side + s * 0.05, f - 0.02, z - 0.22))]
        out.append(sweep("ribbon", pts, [(0.012, 0.003), (0.016, 0.003), (0.010, 0.002)], color, seg=6, up=V((0, -1, 0))))
    out.append(ellipsoid("ribbon_bow", V((side, f - 0.006, z + 0.006)), (0.025, 0.008, 0.016), color, seg=10, rings=6))
    H.add("chest", *out)
    return out


def frill(H, body, color, z, pad=0.02):
    """Ruffled collar around the neck (lolita-style frills)."""
    cy, rx, ry = G.torso_ring(body, z)
    rings = [(z, cy, rx + pad, ry + pad), (z - 0.035, cy, rx + pad + 0.05, ry + pad + 0.05)]
    o = G.ring_shell("frill", rings, color, seg=72, p=2.0, wave=lambda a, k: 0.10 * math.sin(16 * a) * k)
    G.conform_to(o, body, 0.004, keep_outside=True)
    solidify(o, 0.004)
    H.add_blend(o, G.chain_w([("neck", H.j["neck"].z), ("chest", H.j["chest"].z)]))
    return o


def high_collar(H, body, color, lining=None):
    """Stand-up collar of a long coat (wraps the neck, the inside lined)."""
    j = H.j
    nz = j["neck"].z
    cy, rx, ry = G.torso_ring(body, nz - 0.02)
    rings = [(nz - 0.03, cy, rx + 0.03, ry + 0.03), (nz + 0.06, cy + 0.004, rx + 0.012, ry + 0.012)]
    o = G.ring_shell("high_collar", rings, color, seg=40, p=2.0, a0=20, a1=340)
    G.conform_to(o, body, 0.004, keep_outside=True)
    solidify(o, 0.005)
    if lining:
        AB.paint_faces(o, lambda co, n: lining if n.dot(Vector((co.x, co.y - cy, 0.0))) < -0.1 else None)
    H.add_blend(o, G.chain_w([("neck", nz), ("chest", j["chest"].z)]))
    return o


def neck_beads(H, body, color, n=15, r=0.0068, z_off=-0.035, chain=False, span=78):
    """A row of beads (prayer beads) or a fine chain (chain=True: one tube) across the front of the neck."""
    nz = H.j["neck"].z + z_off
    cy, rx, ry = G.torso_ring(body, nz)
    pts = []
    for k in range(n):
        a = math.radians(-span + 2 * span * k / (n - 1))
        x = math.sin(a) * rx * 0.82
        pts.append(V((x, _front_at(body, nz, x, 0.010), nz)))
    if chain:
        o = sweep("chain", pts, r * 0.7, color, seg=6, up=V((0, 0, 1)))
        H.add("neck", o)
        return [o]
    out = [H.add("neck", ellipsoid("bead", p, (r, r, r), color, seg=8, rings=5)) for p in pts]
    return out


def stethoscope(H, body, color, chest_steel="#c9ced6"):
    """Stethoscope: two tubes from the collar down to a chest piece."""
    nz = H.j["neck"].z
    f = _front_at(body, nz - 0.06, 0.0, 0.010)
    left = sweep("steth_l", [V((-0.06, f - 0.004, nz - 0.02)), V((-0.04, f - 0.02, nz - 0.12)),
                             V((0.0, f - 0.035, nz - 0.22))], 0.0045, color, seg=6, up=V((0, -1, 0)))
    right = sweep("steth_r", [V((0.06, f - 0.004, nz - 0.02)), V((0.05, f - 0.02, nz - 0.12)),
                              V((0.0, f - 0.035, nz - 0.22))], 0.0045, color, seg=6, up=V((0, -1, 0)))
    disc = ellipsoid("steth_disc", V((0.035, f - 0.030, nz - 0.20)), (0.022, 0.008, 0.022), chest_steel, seg=12,
                     rings=6)
    H.add("chest", left, right, disc)
    return [left, right, disc]


def badge(H, body, color, pad=0.03, x=-0.07, z_off=0.04):
    """A clipped ID badge on the chest, over a jacket."""
    z = H.j["chest"].z - z_off
    y = _front_at(body, z, x, pad + 0.002)
    b = A.box("id_badge", (0.058, 0.006, 0.040), loc=(x, y, z), color=color, bevel=0.002, seg=2)
    A.apply_transform(b)
    H.add("chest", b)
    return b


def armband(H, body, S, color, cross=None, over=(), at=0.30):
    """A band on the upper arm; cross = colour of a plus sign on its outer side (medic armband)."""
    j = H.j
    sh, el = j["shoulder." + S], j["elbow." + S]
    r = G.limb_radius(body, "upper_arm." + S, sh, el)
    p0 = sh.lerp(el, at)
    d = (el - sh).normalized()
    o = along("armband", p0, p0 + d * 0.05, [(r * 1.10, 0.0), (r * 1.13, 0.5), (r * 1.10, 1.0)], color, seg=20)
    G.conform_to(o, body, 0.018, over=over, keep_outside=False)
    parts = [o]
    if cross:
        sg = 1 if S == "L" else -1
        outward = Vector((sg * r * 1.25, 0, 0))
        parts.append(A.box("cross_v", (0.005, 0.012, 0.040), loc=p0 + outward, color=cross, bevel=0.0015, seg=2))
        parts.append(A.box("cross_h", (0.005, 0.040, 0.012), loc=p0 + outward, color=cross, bevel=0.0015, seg=2))
        for p in parts[1:]:
            A.apply_transform(p)
    H.add("upper_arm." + S, *parts)
    return parts


def bracelet(H, body, S, color, bell=None):
    """Bangle ring on the wrist with an optional bell."""
    j = H.j
    wr, el = j["wrist." + S], j["elbow." + S]
    d = (wr - el).normalized()
    r = G.limb_radius(body, "forearm." + S, wr, el)
    c = wr + d * 0.025
    o = ring("bracelet_" + S, c, d, r * 1.08, 0.0055, color, seg=24, minor=6)
    out = [o]
    if bell:
        sg = 1 if S == "L" else -1
        out.append(ellipsoid("bracelet_bell", c + Vector((sg * r * 1.05, 0.0, -0.006)), (0.008, 0.008, 0.008), bell,
                             seg=8, rings=5))
    H.add("hand." + S, *out)
    return out


def thigh_strap(H, body, S, color, knife=None):
    """A band around the thigh (holster or knife strap); knife = blade colour on the front."""
    j = H.j
    hip, kn = j["hipj." + S], j["knee." + S]
    d = (kn - hip).normalized()
    p = hip.lerp(kn, 0.34)
    r = G.limb_radius(body, "thigh." + S, hip, kn)
    o = along("thigh_strap", p, p + d * 0.035, [(r * 1.12, 0.0), (r * 1.15, 0.5), (r * 1.12, 1.0)], color, seg=24)
    G.conform_to(o, body, 0.004, keep_outside=True)
    out = [o]
    if knife:
        sg = 1 if S == "L" else -1
        out.append(A.box("knife", (0.012, 0.004, 0.06), loc=p + Vector((sg * r * 0.4, -r * 1.2, -0.03)),
                         color=knife, bevel=0.002, seg=2))
        A.apply_transform(out[-1])
    H.add("thigh." + S, *out)
    return out


def knee_pads(H, body, S, color):
    """Cloth/plastic knee pads on the front of each knee."""
    j = H.j
    k = j["knee." + S]
    front = _face_front_knee(body, k, S)
    pad = ellipsoid("knee_pad", V((k.x, front + 0.008, k.z + 0.004)), (0.040, 0.014, 0.034), color, seg=16, rings=8)
    H.add("shin." + S, pad)
    return pad


def _face_front_knee(body, k, S):
    dom = AB.dominant_bones(body)
    ys = [(body.matrix_world @ v.co).y for v in body.data.vertices if dom[v.index] in ("thigh." + S, "shin." + S)
          and abs((body.matrix_world @ v.co).z - k.z) < 0.02]
    return min(ys) if ys else k.y - 0.05


def shield(H, body, S, color, rim, boss, R=0.22, fwd=0.095):
    """Round shield held out from the forearm, face turned outward (manhole-cover style: a thick disc with a rim)."""
    j = H.j
    w, e = j["wrist." + S], j["elbow." + S]
    sg = 1 if S == "L" else -1
    c = w.lerp(e, 0.50) + Vector((sg * fwd, -0.02, 0.0))
    disc = lathe("shield", [(R, -0.012), (R * 1.02, 0.0), (R, 0.012)], color, seg=40)
    disc.data.transform(Matrix.Translation(c) @ Matrix.Rotation(sg * math.pi / 2, 4, "Y"))
    rim_o = ring("shield_rim", c + Vector((sg * 0.012, 0, 0)), (sg, 0, 0), R * 1.0, 0.012, rim, seg=48, minor=8)
    bos = ellipsoid("shield_boss", c + Vector((sg * 0.016, 0, 0)), (0.030, 0.045, 0.045), boss, seg=14, rings=8)
    H.add("forearm." + S, disc, rim_o, bos)
    return [disc, rim_o, bos]


def crossbow(H, body, color, wood="#6a4630"):
    """Crossbow slung across the back: stock on the spine, bow limbs along the shoulders."""
    j = H.j
    cy, rx, ry = G.torso_ring(body, j["chest"].z)
    back = cy + ry + 0.035
    z = j["chest"].z + 0.07
    stock = A.box("crossbow_stock", (0.035, 0.06, 0.40), loc=(0.0, back, z - 0.08), color=wood, bevel=0.008, seg=2)
    A.apply_transform(stock)
    pts = [V(((t - 0.5) * 0.46, back + 0.02 + 0.05 * (1 - (2 * t - 1) ** 2), z + 0.02)) for t in
           [k / 8 for k in range(9)]]
    limb = sweep("crossbow_limb", pts, 0.009, color, seg=6, up=V((0, 0, 1)))
    H.add("chest", stock, limb)
    return [stock, limb]


def helmet_on_hip(H, body, color, side=1):
    """A motorcycle helmet clipped to the belt at the hip."""
    hz = H.j["hip"].z
    cy, rx, ry = G.torso_ring(body, hz)
    o = ellipsoid("bike_helmet", V((side * (rx + 0.035), cy, hz - 0.10)), (0.075, 0.085, 0.080), color, seg=18,
                  rings=10)
    H.add("hips", o)
    return o


# ---------------------------------------------------------------- head and face

def _hair_envelope(body, cc):
    """Half sizes and top height of the head with its hair, counting only what rises above the head centre (side
    tails and long strands below it are ignored), so a cap or helmet shell encloses the hair."""
    dom = AB.dominant_bones(body)
    pts = [body.matrix_world @ v.co for v in body.data.vertices if dom[v.index] == "head"]
    up = [p for p in pts if p.z > cc.z] or pts
    return (max(abs(p.x - cc.x) for p in up), max(abs(p.y - cc.y) for p in up), max(p.z for p in up))


def cap(H, body, color, brim=None, brim_len=0.085, band=None):
    """Baseball/snapback cap: a smooth crown enclosing the hair, its lower edge at the brow line, and a front brim.
    Peaked caps pass a dark brim colour; band is a thin trim ring just above the brim."""
    c, half, top = G.skull_box(H, body)
    cc = V((c.x, c.y + half.y * 0.02, c.z + half.z * 0.10))
    hx, hy, ht = _hair_envelope(body, cc)
    R = V((hx * 1.04 + 0.008, hy * 1.04 + 0.008, (ht - cc.z) * 1.03 + 0.006))
    els = [86 - (86 - 24) * k / 16 for k in range(17)]
    crown = G._head_grid("cap", cc, R, els, lambda el: (0.0, 360.0), cols=48)
    A.paint(crown, color)
    solidify(crown, 0.005)
    out = [crown]
    zb = cc.z + R.z * math.sin(math.radians(24))
    rx, ry = R.x * math.cos(math.radians(24)) * 0.99, R.y * math.cos(math.radians(24)) * 0.99
    rings = [(zb, cc.y, rx, ry),
             (zb - 0.006, cc.y - brim_len * 0.5, rx + brim_len * 0.7, ry + brim_len * 0.5)]
    out.append(G.ring_shell("cap_brim", rings, brim or color, seg=28, a0=-72, a1=72, p=2.2))
    solidify(out[-1], 0.004)
    if band:
        bz = zb + 0.004
        out.append(G.ring_shell("cap_band", [(bz, cc.y, rx * 1.01, ry * 1.01), (bz + 0.012, cc.y, rx * 1.01, ry * 1.01)],
                                band, seg=36))
        solidify(out[-1], 0.004)
    H.add("head", *out)
    return out


def beret(H, body, color, tilt=-14.0, shift=0.22):
    """Flat beret, tilted to one side on the crown."""
    c, half, top = G.skull_box(H, body)
    R = half.x * 1.08 + 0.012
    prof = [(R * 0.80, 0.0), (R * 1.02, 0.018), (R * 1.14, 0.040), (R * 1.10, 0.058), (R * 0.84, 0.072),
            (R * 0.50, 0.082), (0.02, 0.088)]
    o = lathe("beret", prof, color, seg=36)
    o.data.transform(Matrix.Translation((c.x + shift * R, c.y - half.y * 0.02, top - half.z * 0.30))
                     @ Matrix.Rotation(math.radians(tilt), 4, "Z"))
    H.add("head", o)
    return o


def headband(H, body, color, z_off=0.02, width=0.024, sag=0.0):
    """Cloth headband or bandana across the forehead."""
    c, half, top = G.skull_box(H, body)
    z = H.eyes["L"][0].z + 0.085 + z_off if getattr(H, "eyes", None) else top - half.z * 0.3
    rx, ry = half.x * 1.03, half.y * 1.03
    o = G.ring_shell("headband", [(z, c.y, rx, ry), (z + width, c.y, rx, ry)], color, seg=40)
    solidify(o, 0.005)
    H.add("head", o)
    return o


def _lenses(H, body, frame, lens, style, z_lift=0.0):
    """Rims (round/square) or a lens-only frame (rimless: a fine line of lens; sun: a dark lens), bridge included."""
    eL, eR = H.eyes["L"][0], H.eyes["R"][0]
    z = (eL.z + eR.z) / 2 + z_lift
    fy = _face_front(body, z)
    out = []
    for e in (eL, eR):
        cnt = V((e.x, fy - 0.006, z))
        if style in ("round", "square"):
            out.append(ring("glass_rim", cnt, (0, 1, 0), 0.028 if style == "round" else 0.026, 0.0034, frame,
                            seg=28 if style == "round" else 4, minor=6))
        if style == "sun":
            out.append(ellipsoid("glass_lens", cnt - V((0, 0.003, 0)), (0.026, 0.0025, 0.022), lens, seg=16, rings=8,
                                 mat="M_Clear"))
        if style == "rimless":
            out.append(ellipsoid("glass_lens", cnt - V((0, 0.003, 0)), (0.022, 0.0016, 0.018), lens, seg=14, rings=6,
                                 mat="M_Clear"))
    bridge = sweep("glass_bridge", [V((eL.x - 0.026, fy - 0.006, z)), V((0.0, fy - 0.010, z + 0.004)),
                                    V((eR.x + 0.026, fy - 0.006, z))], 0.0028, frame, seg=5, up=V((0, 0, 1)))
    out.append(bridge)
    return out


def glasses(H, body, frame, lens="#bfe3ff", style="round"):
    """Glasses over the eyes (round, square or rimless); the rims are rigid to the head."""
    parts = _lenses(H, body, frame, lens, style)
    H.add("head", *parts)
    return parts


def sunglasses(H, body, frame, lens="#101015"):
    """Sunglasses worn up on the crown of the head, lenses dark."""
    parts = _lenses(H, body, frame, lens, "square", z_lift=0.075)
    H.add("head", *parts)
    return parts


def goggles(H, body, strap, lens="#f0a03a"):
    """Welding/sport goggles: a strap around the forehead, two tinted lenses over the eyes."""
    c, half, top = G.skull_box(H, body)
    z = (H.eyes["L"][0].z + H.eyes["R"][0].z) / 2 + 0.058
    rx, ry = half.x * 1.04, half.y * 1.04
    band = G.ring_shell("goggle_strap", [(z, c.y, rx, ry), (z + 0.022, c.y, rx, ry)], strap, seg=44)
    solidify(band, 0.006)
    fy = c.y - half.y * 1.0 - 0.008
    out = [band]
    for e in (H.eyes["L"][0], H.eyes["R"][0]):
        out.append(ellipsoid("goggle_lens", V((e.x, fy, z + 0.012)), (0.036, 0.010, 0.030), lens, seg=16, rings=8,
                             mat="M_Clear"))
        out.append(ring("goggle_rim", V((e.x, fy + 0.002, z + 0.012)), (0, 1, 0), 0.036, 0.0045, strap, seg=24, minor=5))
    H.add("head", *out)
    return out


def headset(H, body, color, cups=None, mic=None, neck=False):
    """Over-ear headphones: a band over the crown, two ear cups and an optional boom mic to the mouth."""
    c, half, top = G.skull_box(H, body)
    cups = cups or color
    rx, ry = half.x * 1.06, half.y * 1.05
    z0 = c.z - 0.005
    pts = []
    for k in range(10):
        a = math.pi * k / 9
        pts.append(V((-math.cos(a) * rx, c.y, z0 + math.sin(a) * (top - z0 + 0.02))))
    band = sweep("headset_band", pts, 0.0065, color, seg=8, up=V((0, 1, 0)))
    out = [band]
    for s in (-1, 1):
        out.append(ellipsoid("headset_cup", V((s * rx * 1.02, c.y - 0.004, z0 - 0.01)), (0.027, 0.034, 0.036), cups,
                             seg=14, rings=8))
    if mic:
        fy = c.y - half.y - 0.02
        boom = sweep("mic_boom", [V((rx * 0.98, c.y - 0.01, z0 - 0.04)), V((rx * 0.75, fy - 0.02, z0 - 0.10)),
                                  V((0.02, fy - 0.03, z0 - 0.12))], 0.0045, mic, seg=6, up=V((0, 0, 1)))
        out += [boom, ellipsoid("mic_head", V((0.02, fy - 0.035, z0 - 0.12)), (0.011, 0.010, 0.011), mic, seg=8, rings=5)]
    H.add("head", *out)
    return out


def neck_headphones(H, body, color, cups=None):
    """Headphones worn around the neck (the band behind the neck, cups at the collar)."""
    j = H.j
    nz = j["neck"].z
    cy, rx, ry = G.torso_ring(body, nz - 0.02)
    pts = []
    for k in range(11):
        a = math.radians(-100 + 200 * k / 10)
        # Back of the neck (cos a = 1) sits behind the centre; the ends curl forward at the collarbones.
        pts.append(V((math.sin(a) * rx, cy + math.cos(a) * ry * 0.95, nz - 0.02 + 0.01 * math.cos(a))))
    band = sweep("neck_phones", pts, 0.008, color, seg=8, up=V((0, 0, 1)))
    out = [band]
    for s in (-1, 1):
        out.append(ellipsoid("neck_cup", V((s * rx * 1.04, cy - ry * 0.45, nz - 0.03)), (0.024, 0.030, 0.034),
                             cups or color, seg=14, rings=8))
    H.add("neck", *out)
    return out


def earpiece(H, body, color, coil=None):
    """Earpiece on the right ear with its coil running down into the collar (security staff)."""
    c, half, top = G.skull_box(H, body)
    nz = H.j["neck"].z
    f = _front_at(body, nz - 0.03, 0.0, 0.010)
    ear = V((-half.x * 1.02, c.y - 0.005, c.z - 0.005))
    o = [ellipsoid("earpiece", ear, (0.012, 0.012, 0.012), color, seg=8, rings=5)]
    o.append(sweep("earpiece_coil", [ear + V((0.0, 0.0, -0.01)), V((-0.05, f - 0.01, nz - 0.03)),
                                     V((-0.02, f - 0.02, nz - 0.07))], 0.0025, coil or color, seg=4, up=V((1, 0, 0))))
    H.add("head", o[0])
    H.add("neck", o[1])
    return o


def star_pin(H, body, color, side=1.0):
    """A star hairpin on the side of the crown."""
    c, half, top = G.skull_box(H, body)
    p = V((c.x + side * half.x * 0.92, c.y - half.y * 0.55, top - half.z * 0.30))
    o = ellipsoid("star_pin", p, (0.022, 0.006, 0.022), color, seg=10, rings=6)
    H.add("head", o)
    return o


def ponytail(H, body, color, length=0.19, thick=0.030, low=True):
    """A ponytail (low = at the nape, otherwise high on the crown) built from a tapered tube."""
    c, half, top = G.skull_box(H, body)
    back = c.y + half.y * 0.95
    z0 = c.z - half.z * (0.50 if low else 0.05)
    p0 = V((0.0, back - 0.01, z0))
    pts = [p0, p0 + V((0.0, 0.035, -0.035)), p0 + V((0.0, 0.085, -0.10)), p0 + V((0.0, 0.095, -0.10 - length))]
    o = sweep("ponytail", pts, [(thick, thick), (thick * 0.95, thick * 0.9), (thick * 0.7, thick * 0.6),
                                 (0.008, 0.008)], color, seg=10, up=V((1, 0, 0)))
    H.add("head", o)
    return o


def braid(H, body, color, side=1.0):
    """A long braid over one shoulder, down to the waist, with bead-like swells."""
    j = H.j
    c, half, top = G.skull_box(H, body)
    sz = j["shoulder.L"].z
    f = _front_at(body, sz - 0.04, 0.0, 0.018)
    pts = [V((side * half.x * 0.85, c.y - 0.02, top - half.z * 0.55)), V((side * 0.14, c.y - 0.05, sz + 0.02)),
           V((side * 0.16, f - 0.01, sz - 0.10)), V((side * 0.15, f - 0.02, sz - 0.25)),
           V((side * 0.14, f - 0.02, j["hip"].z))]
    radii = [(0.016, 0.016), (0.018, 0.018), (0.021, 0.021), (0.017, 0.017), (0.012, 0.012)]
    o = sweep("braid", pts, radii, color, seg=10, up=V((0, -1, 0)))
    H.add("chest", o)
    return o


def hat_pin(H, body, color):
    """Small brooch on a coat lapel."""
    z = H.j["chest"].z + 0.02
    y = _front_at(body, z, -0.05, 0.035)
    o = ellipsoid("lapel_pin", V((-0.05, y, z)), (0.010, 0.004, 0.010), color, seg=8, rings=5)
    H.add("chest", o)
    return o


def boot(H, body, S, top, color, cuff=None, shaft=0.047, sole=None):
    """A short boot or shoe whose top is at `top` (used for ankle boots, knee boots, dress shoes)."""
    return AB.boot(H, body, S, top, color, cuff_color=cuff)


def stripes(o, color, zs, width=0.010):
    """Horizontal reflective bands at the heights zs (world z) painted over a garment."""
    return G.trim(o, lambda co, n: any(abs(co.z - z) < width for z in zs), color)


def binoculars(H, body, color, pad=0.070):
    """A pair of binoculars hanging on the chest (strap at the collar)."""
    z = H.j["chest"].z - 0.03
    out = []
    for x in (-0.030, 0.030):
        y = _front_at(body, z, x, pad)
        out.append(cyl("binocular", V((x, y - 0.012, z)), V((x, y - 0.045, z)), 0.022, 0.022, color, seg=14))
    H.add("chest", *out)
    return out
