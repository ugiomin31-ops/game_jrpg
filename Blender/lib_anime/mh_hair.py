"""Anime hair grown on the real head shape.

Anime hair reads as a few big, clean clumps: a cap that follows the skull, bangs that fall in separate
pointed locks with gaps for the eyes, side locks framing the face, and layered locks flaring at the nape
(reference: Genshin Impact / VRoid hair, built as clumps rather than strands). Each lock here is a tapered,
flattened sweep whose path is wrapped onto the skull with a growing offset, so the hair has volume
but never cuts into the head.
"""
import math

import numpy as np
from mathutils import Vector

import anime_body as AB
from humanoid import V, bvh_of, lock, mix, shade, zgrad


class Head:
    """Skull frame measured from the body mesh: centre, radii and a ray-cast surface."""

    def __init__(self, H, body):
        dom = AB.dominant_bones(body)
        eL, _ = H.eyes["L"]
        self.ez = eL.z
        pts = np.array([tuple(body.matrix_world @ v.co) for v in body.data.vertices
                        if dom[v.index] == "head" and v.co.z > eL.z - 0.01])
        lo, hi = pts.min(axis=0), pts.max(axis=0)
        # Ears stick out: take the width from the upper cranium only.
        upper = pts[pts[:, 2] > eL.z + 0.04]
        self.rx = float(np.abs(upper[:, 0]).max())
        self.c = Vector(((lo[0] + hi[0]) / 2, (lo[1] + hi[1]) / 2, eL.z + 0.012))
        self.top = float(hi[2])
        self.front = float(lo[1])
        self.back = float(hi[1])
        self.bvh = bvh_of([body])

    def dir(self, az, el):
        """az: 0 = front (-Y), +90 = character left (+X); el: 0 = level with the centre, 90 = up."""
        a, e = math.radians(az), math.radians(el)
        return Vector((math.sin(a) * math.cos(e), -math.cos(a) * math.cos(e), math.sin(e)))

    def surface(self, d):
        hit = self.bvh.ray_cast(self.c + d * 0.5, -d, 0.6)
        if hit[0] is None:
            return self.c + d * 0.1
        return hit[0]

    def path(self, a0, e0, a1, e1, off0, off1, n=7, sag=0.0):
        """Points from (a0, e0) to (a1, e1) over the skull, offset off0 -> off1 above it.
        Below the centre the path drops straight down (hair hangs) instead of following the jaw."""
        out = []
        for i in range(n):
            t = i / (n - 1)
            az = a0 + (a1 - a0) * t
            el = e0 + (e1 - e0) * t
            d = self.dir(az, max(el, -5))
            p = self.surface(d) + d * (off0 + (off1 - off0) * t + sag * math.sin(math.pi * t))
            if el < -5:
                p.z -= (math.radians(-5 - el)) * 0.11
            out.append(p)
        return out


def cap(H, body, head, color, hairline=0.042, nape=-0.075, offset=0.008):
    """Hair cap: the scalp cut along an anime hairline (high on the forehead, in front of the ears,
    down to the nape) and pushed out."""
    c, ez = head.c, head.ez

    def keep(co):
        d = co - c
        if d.length < 1e-6:
            return False
        az = math.degrees(math.atan2(d.x, -d.y))  # 0 front, +-180 back
        a = abs(az)
        if a < 60:      # forehead: hairline arcs up to the temples
            return co.z > ez + hairline + 0.006 * (a / 60) ** 2
        if a < 105:     # temples / in front of the ear
            return co.z > ez + hairline * (1 - (a - 60) / 45) * 0.6 + 0.004
        return co.z > ez + nape * min(1, (a - 105) / 45)
    o = AB.cloth_shell("hair_cap", body, keep, color, offset=offset, thick=0.004)
    md = o.modifiers.new("smooth", "SMOOTH")
    md.factor = 0.8
    md.iterations = 6
    AB.A.apply_modifiers(o)
    zgrad(o, ez - 0.06, shade(color, 0.72), head.top, color)
    for g in list(o.vertex_groups):
        o.vertex_groups.remove(g)
    H.add("head", o)
    return o


def _lock(H, pts, width, thick, color, tip_color, out, n=10, tip=0.0, belly=0.35):
    o = lock("hair_lock", pts, width, thick, color, out, n=n, seg=6, tip=tip, belly=belly, root=0.9)
    zs = [v.co.z for v in o.data.vertices]
    zgrad(o, min(zs), tip_color, max(zs), color)
    H.add("head", o)
    return o


def shine(objs, head, color, el_lo=48, el_hi=58):
    """The anime 'angel ring': a light band where the hair turns toward the light."""
    hi = mix(color, "#ffffff", 0.45)
    for o in objs:
        attr = o.data.color_attributes["Col"]
        for loop in o.data.loops:
            co = o.matrix_world @ o.data.vertices[loop.vertex_index].co
            d = (co - head.c)
            if d.length < 1e-6:
                continue
            el = math.degrees(math.asin(max(-1, min(1, d.normalized().z))))
            az = abs(math.degrees(math.atan2(d.x, -d.y)))
            if el_lo < el < el_hi and az < 120:
                attr.data[loop.index].color_srgb = hi


def short_anime(H, body, color, bangs=9, swept=0.0):
    """Short layered male cut: separated bangs, side locks in front of the ears, flared nape layers."""
    head = Head(H, body)
    tipc = shade(color, 0.80)
    made = [cap(H, body, head, color)]
    # Back and crown layers: locks radiate from the whorl and flare out at the nape.
    for row, (e0, e1, n, w, flare) in enumerate(((80, -14, 12, 0.058, 0.010), (58, -26, 10, 0.052, 0.016))):
        for i in range(n):
            az = 70 + 220 * (i + 0.5 * row) / n
            if az > 180:
                az -= 360
            made.append(_lock(H, head.path(az * 0.85, e0, az, e1, 0.006 + 0.003 * row, 0.006 + flare, n=8,
                                           sag=0.006), w, 0.010, mix(color, "#fff4cc", 0.04 * (i % 3)), tipc,
                              (head.dir(az, 30)), tip=0.0))
    # Side locks in front of the ears, down to the jaw.
    for s in (1, -1):
        for k, (a, low, w) in enumerate(((68, -38, 0.030), (80, -30, 0.034), (94, -24, 0.034))):
            made.append(_lock(H, head.path(s * (a - 25), 62, s * a, low, 0.007, 0.006, n=8, sag=0.004), w, 0.008,
                              color, tipc, head.dir(s * a, 10)))
    # Bangs: fall from the crown over the forehead to the brow, in separate pointed locks with gaps.
    for i in range(bangs):
        f = (i / (bangs - 1)) * 2 - 1           # -1 .. 1 across the forehead
        az0 = f * 40
        az1 = f * 46 + swept * 18 + (6 if i % 2 else -4)
        low = 15 - 7 * (1 - abs(f)) - (3 if i % 3 == 1 else 0)  # longest in the middle
        w = 0.036 + 0.008 * (1 - abs(f))
        made.append(_lock(H, head.path(az1 * 0.7, 76, az1, low, 0.008, 0.005 + 0.003 * abs(f), n=9, sag=0.007),
                          w, 0.007, mix(color, "#fff4cc", 0.05 * (i % 2)), tipc, head.dir(az1, 30), belly=0.3))
    shine(made, head, color)
    return made
