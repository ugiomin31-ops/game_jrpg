"""Base chibi body parts: head + anime face, torso, arms, mitten hands, legs, boots, skirts.

Every function adds its objects to the Humanoid (H.add / H.add_blend) and returns them.
"""
import math

from humanoid import (A, V, Matrix, along, arc_band, bvh_of, capsule, chain, decal, ellipse, ellipsoid, gem, lathe,
                      lock, mix, recolor, ring, shade, sweep, xform, zgrad)

SKIN = "#ffe3cf"
SKIN_SHADE = "#f6c3ab"
LASH = "#2a1719"


# =============================================================== head & face

def hp(H, u, v, w):
    """Point in head units: u across (+X = character left), v depth (+ = back), w up; 1 = head radius."""
    r = H.P["head_r"]
    return H.j["head_c"] + V((u * r * H.P["head_sx"], v * r, w * r))


def head(H, skin=SKIN, eye="#c98a2b", eye_style="open", mouth="open", brow="#5a3520", lash=LASH, blush=True,
         ears=True, eye_size=1.0, eye_gap=1.0, eye_h=0.0, glasses=None, nose=True, brow_raise=0.0, lash_flick=True):
    j, r = H.j, H.P["head_r"]
    c = j["head_c"]
    k = r / 0.235
    sx = H.P["head_sx"]
    o = ellipsoid("head", c, (r * sx, r * 0.96, r), skin, seg=36, rings=22)

    def shape(co):
        p = co - c
        zt = p.z / r
        if zt < 0:
            t = -zt
            p.x *= 1 - 0.17 * t ** 1.8
            if p.y < 0:
                p.y *= 1 - 0.06 * t
            p.z *= 1 + 0.04 * t
        if p.y < -0.6 * r:
            p.y = -0.6 * r + (p.y + 0.6 * r) * 0.62
        return c + p
    A.deform(o, shape)
    # soft cheek warmth toward the lower face
    recolor(o, lambda p: mix(skin, SKIN_SHADE, min(1, max(0, (p.y + 0.0) / (0.9 * r)) * 0.5)) if p.y > 0 else None)
    H.add("head", o)
    H.head_obj = o
    neck = capsule("neck", j["neck"] + V((0, 0.004, -0.02)), j["head"] + V((0, 0.006, 0.03)), 0.036 * k, 0.034 * k,
                   SKIN_SHADE, seg=12)
    H.add("neck", neck)
    if ears:
        for s in (1, -1):
            e = ellipsoid("ear", (0, 0, 0), (0.020 * k, 0.034 * k, 0.050 * k), skin, seg=12, rings=8)
            xform(e, Matrix.Translation(c + V((s * r * sx * 0.93, 0.03 * k, -0.07 * k)))
                  @ Matrix.Rotation(math.radians(-s * 12), 4, "Y") @ Matrix.Rotation(math.radians(-15), 4, "X"))
            H.add("head", e)
    bvh = bvh_of([o])
    H.face_bvh = bvh
    ez = c.z - 0.045 * k + eye_h * k
    ex = 0.092 * k * eye_gap
    W, Hh = 0.080 * k * eye_size, 0.096 * k * eye_size
    dark = shade(eye, 0.42)
    for s in (1, -1):
        n = V((s * 0.32, -1, 0.04)).normalized()
        C = V((c.x + s * ex, c.y - r, ez))
        if eye_style == "open":
            decal("eye_w", ellipse(W, Hh, 24), bvh, C, n, "#fdfaf7", offset=0.0012 * k)
            ir = decal("eye_i", ellipse(W * 0.80, Hh * 0.88, 22, cy=-Hh * 0.04), bvh, C, n, eye, offset=0.0021 * k)
            zgrad(ir, ez - Hh * 0.45, mix(eye, "#ffffff", 0.35), ez + Hh * 0.25, dark)
            decal("eye_p", ellipse(W * 0.36, Hh * 0.46, 16, cy=-Hh * 0.02), bvh, C, n, shade(eye, 0.25),
                  offset=0.0028 * k)
            decal("eye_g", arc_band(W * 0.62, Hh * 0.70, Hh * 0.10, 205, 335, n=12, cy=-Hh * 0.05, taper=0.8), bvh, C, n,
                  mix(eye, "#ffffff", 0.55), offset=0.0031 * k)
            decal("eye_h1", ellipse(W * 0.30, Hh * 0.30, 14, cx=-W * 0.17, cy=Hh * 0.18), bvh, C, n, "#ffffff",
                  offset=0.0037 * k, mat="M_Emit")
            decal("eye_h2", ellipse(W * 0.13, Hh * 0.11, 10, cx=W * 0.16, cy=-Hh * 0.22), bvh, C, n, "#ffffff",
                  offset=0.0037 * k, mat="M_Emit")
            # upper lash line (thick) + outer flick, lower lash tick
            decal("lash_u", arc_band(W * 1.14, Hh * 1.06, 0.016 * k, 8 if s > 0 else 20, 160 if s > 0 else 172, n=16,
                                     cy=Hh * 0.01, taper=0.55), bvh, C, n, lash, offset=0.0040 * k)
            if lash_flick:
                fx = s * W * 0.55
                decal("lash_f", [(fx, Hh * 0.08), (fx + s * W * 0.20, Hh * 0.20), (fx - s * W * 0.02, Hh * 0.24)],
                      bvh, C, n, lash, offset=0.0040 * k, rings=1)
            decal("lash_l", arc_band(W * 0.9, Hh * 1.0, 0.005 * k, 230 if s < 0 else 270, 270 if s < 0 else 310, n=6,
                                     taper=0.6), bvh, C, n, shade(lash, 1.6), offset=0.0040 * k)
        elif eye_style == "happy":
            decal("eye_c", arc_band(W * 1.0, Hh * 0.62, 0.014 * k, 15, 165, n=16, cy=-Hh * 0.18, taper=0.5), bvh, C, n,
                  lash, offset=0.0030 * k)
        if brow:
            decal("brow", arc_band(W * 1.0, Hh * 0.42, 0.010 * k, 35, 145, n=10, cy=Hh * 0.62 + brow_raise * k,
                                   taper=0.7), bvh, C, n, brow, offset=0.0030 * k)
        if blush:
            decal("blush", ellipse(W * 0.75, Hh * 0.26, 14, cx=s * W * 0.18, cy=-Hh * 0.78), bvh, C, n,
                  mix(skin, "#ff8a96", 0.42), offset=0.0010 * k)
        if glasses:
            gc = C + V((0, 0, 0))
            hit = bvh.ray_cast(gc + n * 0.5, -n, 1.0)[0] or gc
            rg = ring("glass", hit + n * 0.016 * k, n, W * 0.72, 0.0045 * k, glasses, seg=20, minor=5)
            H.add("head", rg)
            # temple arm toward the ear
            t0 = hit + n * 0.016 * k + V((s * W * 0.70, 0, 0.004))
            t1 = c + V((s * r * sx * 0.98, 0.02, ez - c.z + 0.01))
            H.add("head", sweep("temple", [t0, t0.lerp(t1, 0.5) + V((s * 0.012, 0, 0)), t1], 0.0035 * k, glasses, seg=5))
    if glasses:
        a = bvh.ray_cast(V((c.x + ex * 0.42, c.y - 1, ez + 0.012)), V((0, 1, 0)), 2.0)[0]
        b = bvh.ray_cast(V((c.x - ex * 0.42, c.y - 1, ez + 0.012)), V((0, 1, 0)), 2.0)[0]
        if a and b:
            m = (a + b) / 2 + V((0, -0.022 * k, 0.004))
            H.add("head", sweep("bridge", [a + V((0, -0.016 * k, 0)), m, b + V((0, -0.016 * k, 0))], 0.0035 * k,
                                glasses, seg=5))
    # mouth
    mz = c.z - 0.132 * k
    n = V((0, -1, -0.12)).normalized()
    C = V((c.x, c.y - r, mz))
    if mouth == "open":
        w, h = 0.050 * k, 0.034 * k
        pts = [(w * 0.5 * math.cos(math.radians(a)), h * 0.25 + h * 0.75 * math.sin(math.radians(a)))
               for a in range(180, 361, 12)]
        pts += [(w * 0.25, h * 0.32), (-w * 0.25, h * 0.32)]
        decal("mouth", pts, bvh, C, n, "#7e2730", offset=0.0016 * k)
        decal("tongue", ellipse(w * 0.55, h * 0.48, 14, cy=-h * 0.32), bvh, C, n, "#f07a86", offset=0.0024 * k)
    elif mouth == "grin":
        w, h = 0.058 * k, 0.030 * k
        pts = [(w * 0.5 * math.cos(math.radians(a)), h * 0.2 + h * 0.8 * math.sin(math.radians(a)))
               for a in range(180, 361, 12)]
        decal("mouth", pts, bvh, C, n, "#7e2730", offset=0.0016 * k)
        decal("teeth", [(-w * 0.42, h * 0.18), (w * 0.42, h * 0.18), (w * 0.36, -h * 0.05), (-w * 0.36, -h * 0.05)],
              bvh, C, n, "#ffffff", offset=0.0024 * k, rings=1)
        decal("tongue", ellipse(w * 0.45, h * 0.40, 12, cy=-h * 0.42), bvh, C, n, "#f07a86", offset=0.0024 * k)
    elif mouth == "smile":
        decal("mouth", arc_band(0.044 * k, 0.026 * k, 0.0065 * k, 200, 340, n=12, cy=0.004 * k, taper=0.6), bvh, C, n,
              "#7e2730", offset=0.0016 * k)
    if nose:
        np_ = bvh.ray_cast(V((c.x, c.y - 1, c.z - 0.092 * k)), V((0, 1, 0)), 2.0)[0]
        if np_:
            H.add("head", ellipsoid("nose", np_ + V((0, 0.002, 0)), (0.010 * k, 0.008 * k, 0.008 * k),
                                    mix(skin, SKIN_SHADE, 0.6), seg=8, rings=6))
    # decals are created via A._from_bmesh and are not yet registered -> collect by name prefix
    for ob in list(A.bpy.context.scene.objects):
        if ob.type == "MESH" and ob.name.split(".")[0] in (
                "eye_w", "eye_i", "eye_p", "eye_g", "eye_h1", "eye_h2", "lash_u", "lash_f", "lash_l", "eye_c", "brow",
                "blush", "mouth", "tongue", "teeth") and not getattr(ob, "_bound", False) and ob not in H.registered():
            H.add("head", ob)
    return o


# =============================================================== hair helpers

def hair_cap(H, color, front=0.30, side=-0.15, back=-0.55, scale=(1.07, 1.06, 1.06), thick=0.012, center_dz=0.0,
             color_lo=None):
    """Hair skull cap: shell around the head with the face window and the underside removed.
    front: face window top (head units z), side: z where the sides stop at the ears, back: lowest z at the back."""
    r = H.P["head_r"]
    c = H.j["head_c"] + V((0, 0.006, center_dz * r))
    sx = H.P["head_sx"]

    def cut(d):
        # d: unit direction (in scaled space before offset)
        if d.y < -0.25 and d.z < front + 0.25 * (abs(d.x) ** 2):
            return True
        if d.y < 0.35 and d.z < side and abs(d.x) > 0.25:
            return True
        if d.z < back:
            return True
        return False
    from humanoid import shell
    o = shell("hair_cap", c, r, color, scale=(scale[0] * sx, scale[1] * 0.96, scale[2]), cut=cut, thick=thick, seg=32,
              rings=18)
    if color_lo:
        zgrad(o, c.z - r * 0.6, color_lo, c.z + r * 0.9, color)
    H.add("head", o)
    return o


def hair_lock(H, ctrl_head_units, width, thick, color, out=None, n=8, seg=6, bone="head", tip=0.0, belly=0.45,
              color_tip=None, wave=None, root=0.85):
    """Hair lock along bezier control points given in head units (see hp)."""
    pts = [hp(H, *p) for p in ctrl_head_units]
    if out is None:
        mid = pts[len(pts) // 2]
        out = (mid - H.j["head_c"]).normalized()
    r = H.P["head_r"]
    o = lock("hair_lock", pts, width * r, thick * r, color, out, n=n, seg=seg, tip=tip, belly=belly, wave=wave,
             root=root)
    if color_tip:
        zs = [v.co.z for v in o.data.vertices]
        zgrad(o, min(zs), color_tip, max(zs), color)
    if isinstance(bone, str):
        H.add(bone, o)
    else:
        H.add_blend(o, bone)
    return o


# =============================================================== torso, arms, hands, legs, feet

def torso(H, color, pants=None, split=None, profile=None, sy=0.74, seg=28):
    """Core torso. Colours: `color` above split (z), `pants` below."""
    j, P = H.j, H.P
    h, T, g = j["hip"].z, P["torso"], P["girth"]
    ch, b = P["chest"], P["belly"]
    prof = profile or [
        (0.0, h - 0.25 * T), (0.06 * g, h - 0.245 * T), (0.094 * g, h - 0.19 * T), (0.110 * g, h - 0.08 * T),
        (0.112 * g, h + 0.03 * T), (0.100 * g + b * 0.6, h + 0.27 * T), (0.100 * g + b, h + 0.42 * T),
        (0.108 * g * ch + b * 0.6, h + 0.62 * T), (0.110 * g * ch, h + 0.76 * T), (0.098 * g, h + 0.87 * T),
        (0.068 * g, h + 0.95 * T), (0.040, h + 0.995 * T), (0.0, h + 1.0 * T)]
    o = lathe("torso", prof, color, sy=sy, seg=seg)
    if pants and split is not None:
        recolor(o, lambda p: pants if p.z < split else None)
    H.add_blend(o, chain([("hips", h + 0.10 * T), ("spine", h + 0.40 * T), ("chest", h + 0.66 * T)]))
    H.torso_obj = o
    return o


def arm(H, s, color, upper_r=(0.040, 0.034), fore_r=(0.034, 0.029), fore_color=None, seg=14):
    S = "L" if s > 0 else "R"
    j = H.j
    g = H.P["limb"]
    ua = capsule("uarm", j["shoulder." + S], j["elbow." + S], upper_r[0] * g, upper_r[1] * g, color, seg=seg)
    fa = capsule("farm", j["elbow." + S], j["wrist." + S], fore_r[0] * g, fore_r[1] * g, fore_color or color, seg=seg)
    H.add("upper_arm." + S, ua)
    H.add("forearm." + S, fa)
    return ua, fa


def hand(H, s, color, thumb_color=None, cuff=None, cuff_r=0.036, fist=True):
    S = "L" if s > 0 else "R"
    j = H.j
    k = H.P["hand_scale"]
    w = j["wrist." + S]
    hd = (j["hand_tip." + S] - w).normalized()
    lx = V((s, 0, 0))
    lx = (lx - lx.dot(hd) * hd).normalized()  # palm normal axis (points outward = back of hand)
    ly = hd.cross(lx).normalized()
    if ly.y > 0:
        ly = -ly
    m = Matrix((lx, ly, hd)).transposed().to_4x4()
    c = w + hd * 0.036 * k
    mit = ellipsoid("mitten", (0, 0, 0), (0.025 * k, 0.034 * k, 0.040 * k), color, seg=14, rings=10)
    if fist:
        def curl(co):
            t = max(0.0, co.z / (0.040 * k))
            return V((co.x - 0.010 * k * t * t, co.y, co.z - 0.004 * k * t * t))
        A.deform(mit, curl)
    xform(mit, Matrix.Translation(c) @ m)
    th = ellipsoid("thumb", (0, 0, 0), (0.013 * k, 0.013 * k, 0.024 * k), thumb_color or color, seg=10, rings=8)
    td = (hd * 0.55 + ly * 0.8 - lx * 0.35).normalized()
    q = V((0, 0, 1)).rotation_difference(td)
    xform(th, Matrix.Translation(w + hd * 0.024 * k + ly * 0.020 * k - lx * 0.010 * k) @ q.to_matrix().to_4x4())
    H.add("hand." + S, mit, th)
    out = [mit, th]
    if cuff:
        cf = along("cuff", w - hd * 0.035, w + hd * 0.008,
                   [(cuff_r * 0.92, 0), (cuff_r, 0.15), (cuff_r * 1.12, 0.85), (cuff_r * 1.05, 1.0), (0.0, 1.0)], cuff,
                   seg=14)
        H.add("forearm." + S, cf)
        out.append(cf)
    return out


def leg(H, s, color, thigh_r=(0.056, 0.045), shin_r=(0.044, 0.035), shin_color=None, seg=14):
    S = "L" if s > 0 else "R"
    j = H.j
    g = H.P["limb"]
    th = capsule("thigh", j["hipj." + S] + V((0, 0, 0.01)), j["knee." + S], thigh_r[0] * g, thigh_r[1] * g, color,
                 seg=seg)
    sh = capsule("shin", j["knee." + S], j["ankle." + S], shin_r[0] * g, shin_r[1] * g, shin_color or color, seg=seg)
    H.add("thigh." + S, th)
    H.add("shin." + S, sh)
    return th, sh


def boot(H, s, color, top=0.20, sole="#3b2418", cuff=None, flare=1.12, toe=None, shaft_r=0.047, heel=True,
         cuff_h=0.022):
    """Chunky chibi boot: rounded toe shoe + shaft up to `top` (z) + optional folded cuff."""
    S = "L" if s > 0 else "R"
    j = H.j
    fs = H.P["foot_scale"]
    a = j["ankle." + S]
    g = H.P["limb"]
    out = []
    shaft = lathe("boot_shaft", [(shaft_r * g * 0.96, 0.0), (shaft_r * g, 0.03), (shaft_r * g * 0.98, (top - a.z) * 0.5),
                                 (shaft_r * g * flare, top - a.z - 0.004), (shaft_r * g * flare * 0.9, top - a.z)],
                  color, center=(a.x, a.y + 0.004, a.z - 0.02), seg=16)
    H.add("shin." + S, shaft)
    out.append(shaft)
    if cuff:
        cf = lathe("boot_cuff", [(shaft_r * g * flare * 0.92, -cuff_h), (shaft_r * g * flare * 1.10, -cuff_h * 0.7),
                                 (shaft_r * g * flare * 1.12, 0.0), (shaft_r * g * flare * 0.95, cuff_h * 0.25)],
                   cuff, center=(a.x, a.y + 0.004, top), seg=16)
        H.add("shin." + S, cf)
        out.append(cf)
    fc = V((a.x, a.y - 0.028 * fs, 0.042 * fs))
    shoe = ellipsoid("shoe", fc, (0.048 * fs * g, 0.080 * fs, 0.046 * fs), color, seg=18, rings=12)
    A.deform(shoe, lambda co: V((co.x, co.y, max(co.z, 0.014))))
    # toe slightly up-tilted & a bit squarer
    A.deform(shoe, lambda co: V((co.x, co.y, co.z + max(0.0, (a.y - 0.07 * fs) - co.y) * 0.25)))
    if toe:
        recolor(shoe, lambda p: toe if p.y < a.y - 0.065 * fs and p.z > 0.02 else None)
    so = ellipsoid("sole", V((a.x, a.y - 0.028 * fs, 0.012)), (0.051 * fs * g, 0.084 * fs, 0.014), sole, seg=18,
                   rings=8)
    A.deform(so, lambda co: V((co.x, co.y, min(max(co.z, 0.0), 0.022))))
    H.add("foot." + S, shoe, so)
    out += [shoe, so]
    if heel:
        hl = A.box("heel", (0.060 * fs * g, 0.040 * fs, 0.022), loc=(a.x, a.y + 0.028 * fs, 0.011), color=sole,
                   bevel=0.006, seg=2)
        A.apply_transform(hl)
        H.add("foot." + S, hl)
        out.append(hl)
    return out


def skirt_weights(H, top_z, hem_z, share=0.75, bone_top="hips"):
    """Weight fn for skirts/robes: rigid to hips at the waist, shared with the near thigh toward the hem."""
    def fn(co):
        t = (top_z - co.z) / max(top_z - hem_z, 1e-4)
        t = min(1.0, max(0.0, t))
        t = t * t * (3 - 2 * t)
        side = co.x / (abs(co.x) + 0.035)
        wl = t * share * (0.5 + 0.5 * side)
        wr = t * share * (0.5 - 0.5 * side)
        return {bone_top: max(0.0, 1 - wl - wr), "thigh.L": wl, "thigh.R": wr}
    return fn


def skirt(H, top_z, hem_z, r_top, r_hem, color, sy=0.80, seg=28, thick=0.010, a0=None, a1=None, hem_wave=0.0,
          waves=8, yshift=None, share=0.75, bulge=0.0, rows=6, flare_pow=1.0, bone="hips", name="skirt"):
    """Flared skirt/robe/tabard shell. a0/a1 = partial arc (deg, 0 = front). hem_wave adds cloth folds."""
    prof = []
    for i in range(rows + 1):
        t = i / rows
        z = top_z + (hem_z - top_z) * t
        rr = r_top + (r_hem - r_top) * (t ** flare_pow) + bulge * math.sin(math.pi * t)
        if hem_wave > 0:
            amp = hem_wave * t
            rr = (lambda base, amp: (lambda a: base + amp * math.cos(waves * a)))(rr, amp)
        prof.append((rr, z))
    o = lathe(name, prof, color, sy=sy, seg=seg, thick=thick, a0=a0, a1=a1, yshift=yshift, caps=False)
    H.add_blend(o, skirt_weights(H, top_z, hem_z, share, bone))
    return o


def belt(H, z, color, buckle=None, width=0.030, r=None, sy=0.76, thick=0.012, seg=28, bone="hips"):
    """Simple elliptical belt ring at height z."""
    j, P = H.j, H.P
    rr = r or (0.114 * P["girth"])
    o = lathe("belt", [(rr, z - width / 2), (rr + thick, z - width / 2 + 0.003), (rr + thick, z + width / 2 - 0.003),
                       (rr, z + width / 2)], color, sy=sy, seg=seg, caps=False)
    from humanoid import solidify
    solidify(o, 0.004)
    H.add(bone, o)
    out = [o]
    if buckle:
        bz = A.box("buckle", (width * 1.25, 0.010, width * 1.05), loc=(0, -(rr + thick) * sy - 0.004, z), color=buckle,
                   bevel=0.004)
        A.apply_transform(bz)
        H.add(bone, bz)
        out.append(bz)
    return out


def pouch(H, center, size, color, flap=None, bone="hips", rot_z=0.0, button=None):
    w, d, h = size
    p = A.box("pouch", (w, d, h), loc=center, rot=(0, 0, rot_z), color=color, bevel=min(w, d, h) * 0.3, seg=2)
    A.apply_transform(p)
    out = [p]
    if flap:
        f = A.box("pouch_flap", (w * 1.06, d * 1.08, h * 0.45), loc=V(center) + V((0, 0, h * 0.30)), rot=(0, 0, rot_z),
                  color=flap, bevel=min(w, d, h) * 0.2, seg=2)
        A.apply_transform(f)
        out.append(f)
    if button:
        fwd = V((math.sin(math.radians(rot_z)), -math.cos(math.radians(rot_z)), 0))
        b = ellipsoid("pouch_btn", V(center) + fwd * (d * 0.55) + V((0, 0, h * 0.12)), (w * 0.12, 0.006, w * 0.12),
                      button, seg=10, rings=6)
        out.append(b)
    H.add(bone, *out)
    return out


__all__ = ["SKIN", "SKIN_SHADE", "LASH", "hp", "head", "hair_cap", "hair_lock", "torso", "arm", "hand", "leg", "boot",
           "skirt", "skirt_weights", "belt", "pouch", "gem", "ring", "along", "capsule", "sweep", "lathe", "ellipsoid",
           "mix", "shade", "zgrad", "recolor", "decal", "ellipse", "arc_band", "bvh_of"]
