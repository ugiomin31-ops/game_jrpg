"""Offline previewer for Resources/Vfx/effects.json (no Unity needed).

Approximates what VfxLibrary.cs + the Abyss/VfxUnlit cel shader draw: every layer kind (quad, orbit, burst,
emitter, ring, arc, sphere, trail) is simulated with the same timing rules (delay, life, size -> endSize,
quad fade envelope, particle colour/size-over-lifetime curves, gravity, flipbook frames) and shaded with the
shader's three-band alpha posterisation, erosion fade and white-hot core, then composited (additive or alpha)
over a dark dungeon backdrop seen from a battle-like camera (15 degree pitch), with a cheap bloom.
It is an approximation (billboards are screen aligned, particle randomness is not Unity's), good for judging
layering, timing, colour and scale, not for pixel-exact matching.

Usage:
  python Tools/vfx/preview_effects.py                     # effect grid -> Temp/vfx_effects.png
  python Tools/vfx/preview_effects.py --keys fire,ice --out some.png [--time 0.3] [--tint FF8040]
  python Tools/vfx/preview_effects.py --textures OLD_DIR --out sheet.png   # before/after texture sheet
"""
import argparse
import json
import math
import os

import numpy as np
from PIL import Image, ImageDraw, ImageFont

ROOT = os.path.normpath(os.path.join(os.path.dirname(__file__), "..", ".."))
TEX_DIR = os.path.join(ROOT, "Assets", "_Game", "Resources", "Vfx", "Textures")
EFFECTS = os.path.join(ROOT, "Assets", "_Game", "Resources", "Vfx", "effects.json")

LAYER_DEFAULTS = dict(color="FFFFFF", life=0.6, size=1.0, endSize=0.0, height=0.0, speed=0.0, gravity=0.0, rate=12.0,
                      radius=0.2, delay=0.0, y=0.0, spin=0.0, rotation=0.0, count=20, tiles=1, alpha=False, horizontal=False, upright=False)

# Representative element tints (BattleView multiplies every layer colour by the skill's light colour).
DEFAULT_TINTS = {
    "fire": "FF7722", "flame": "FF7722", "heal": "33FF88", "ring": "FFEBA8", "smoke": "7AD13B", "spark": "FFED45",
    "magic_circle": "C8D8FF", "buff": "FFE073", "debuff": "B86BFF", "critical": "FFF2C2", "slash": "9ED6FF",
    "impact": "FFB547",
}


# ----------------------------------------------------------------------------- textures & shading

_TEX = {}


def texture(name, directory=TEX_DIR):
    key = (directory, name)
    if key not in _TEX:
        im = Image.open(os.path.join(directory, name + ".png")).convert("RGBA")
        _TEX[key] = np.asarray(im, dtype=np.float32) / 255.0
    return _TEX[key]


def sample(tex, u, v):
    """Bilinear clamp sample. u, v in UV space (v = 0 at the bottom row like Unity)."""
    h, w = tex.shape[:2]
    x = np.clip(u, 0, 1) * w - 0.5
    y = (1 - np.clip(v, 0, 1)) * h - 0.5
    x0 = np.clip(np.floor(x).astype(int), 0, w - 1)
    y0 = np.clip(np.floor(y).astype(int), 0, h - 1)
    x1 = np.clip(x0 + 1, 0, w - 1)
    y1 = np.clip(y0 + 1, 0, h - 1)
    fx = np.clip(x - x0, 0, 1)[..., None]
    fy = np.clip(y - y0, 0, 1)[..., None]
    return (tex[y0, x0] * (1 - fx) * (1 - fy) + tex[y0, x1] * fx * (1 - fy)
            + tex[y1, x0] * (1 - fx) * fy + tex[y1, x1] * fx * fy)


def smoothstep(e0, e1, x):
    t = np.clip((x - e0) / (e1 - e0), 0, 1)
    return t * t * (3 - 2 * t)


def cel_shade(tex, u, v, color, fade, additive, st=(1, 1, 0, 0), bands=3, core_start=0.72, core_radius=0.014, intensity=1.6):
    """Emulates Abyss/VfxUnlit (_Cel = 1). Returns (rgb, alpha) for the covered pixels.
    color: (..., 3) linear-ish tint, fade: (...) tint alpha."""
    su, sv = u * st[0] + st[2], v * st[1] + st[3]
    t = sample(tex, su, sv)
    a = t[..., 3]
    fade = np.clip(fade, 0, 1)
    threshold = (1 - fade) * 0.85
    shape = np.clip((a - threshold) / np.maximum(1 - threshold, 1e-3), 0, 1)
    q = shape * bands
    banded = (np.floor(q) + smoothstep(0.82, 1.0, q - np.floor(q))) / bands
    alpha = banded * np.clip(fade * 3, 0, 1)
    if additive:
        d = core_radius
        solid = (sample(tex, su + d, sv + d)[..., 3] + sample(tex, su + d, sv - d)[..., 3]
                 + sample(tex, su - d, sv + d)[..., 3] + sample(tex, su - d, sv - d)[..., 3]) * 0.25
        heat = banded * np.minimum(t[..., 0], solid)
        core = smoothstep(core_start, 1.0, heat)[..., None]
        rgb = (color * (1 - core) + (1 + color * 0.25) * core) * intensity
    else:
        lum = t[..., 0] * 0.299 + t[..., 1] * 0.587 + t[..., 2] * 0.114
        toon = np.where(lum > 0.55, 1.05, np.where(lum > 0.25, 0.62, lum))
        ratio = t[..., :3] / np.maximum(lum, 1e-3)[..., None]
        rgb = color * (t[..., :3] * 0.25 + (toon[..., None] * ratio) * 0.75)
    inside = ((su >= st[2] - 1e-4) & (su <= st[2] + st[0] + 1e-4) & (sv >= st[3] - 1e-4) & (sv <= st[3] + st[1] + 1e-4))
    return rgb, alpha * inside


def hex_color(s):
    s = s.strip("#")
    return np.array([int(s[i:i + 2], 16) / 255.0 for i in (0, 2, 4)], dtype=np.float32)


# ----------------------------------------------------------------------------- camera & canvas

class Canvas:
    def __init__(self, w, h, look=(0, 1.25, 0), distance=7.4, pitch=15.0, fov=36.0, yaw=0.0):
        self.w, self.h = w, h
        p, yw = math.radians(pitch), math.radians(yaw)
        fwd = np.array([math.sin(yw) * math.cos(p), -math.sin(p), math.cos(yw) * math.cos(p)])
        self.cam = np.array(look, dtype=np.float64) - fwd * distance
        self.f = fwd / np.linalg.norm(fwd)
        self.r = np.cross(np.array([0, 1.0, 0]), self.f)
        self.r /= np.linalg.norm(self.r)
        self.u = np.cross(self.f, self.r)
        self.focal = (h / 2) / math.tan(math.radians(fov) / 2)
        self.buf = np.zeros((h, w, 3), dtype=np.float32)

    def project(self, p):
        d = np.asarray(p, dtype=np.float64) - self.cam
        z = d @ self.f
        return self.w / 2 + (d @ self.r) / z * self.focal, self.h / 2 - (d @ self.u) / z * self.focal, z

    def rays(self, x0, y0, x1, y1):
        ys, xs = np.mgrid[y0:y1, x0:x1].astype(np.float64)
        dx = (xs + 0.5 - self.w / 2) / self.focal
        dy = -(ys + 0.5 - self.h / 2) / self.focal
        dirs = self.r[None, None] * dx[..., None] + self.u[None, None] * dy[..., None] + self.f[None, None]
        return dirs, xs.astype(int), ys.astype(int)

    def clip_box(self, xs, ys, pad=1):
        x0 = int(max(0, math.floor(min(xs)) - pad))
        x1 = int(min(self.w, math.ceil(max(xs)) + pad))
        y0 = int(max(0, math.floor(min(ys)) - pad))
        y1 = int(min(self.h, math.ceil(max(ys)) + pad))
        return (x0, y0, x1, y1) if x1 > x0 and y1 > y0 else None

    def composite(self, box, rgb, alpha, additive):
        x0, y0, x1, y1 = box
        region = self.buf[y0:y1, x0:x1]
        a = alpha[..., None]
        if additive:
            region += rgb * a
        else:
            region *= (1 - a)
            region += rgb * a

    # --- primitives ----------------------------------------------------------------------
    def sprite(self, tex, center, width, height, rotation_deg, color, fade, additive, st=(1, 1, 0, 0)):
        """Camera-facing quad (billboard) of world size width x height, rotated in the view plane."""
        sx, sy, z = self.project(center)
        if z <= 0.1:
            return
        hw, hh = width / z * self.focal / 2, height / z * self.focal / 2
        if hw < 0.3 or hh < 0.3:
            return
        rad = math.radians(rotation_deg)
        c, s = math.cos(rad), math.sin(rad)
        ex, ey = abs(hw * c) + abs(hh * s), abs(hw * s) + abs(hh * c)
        box = self.clip_box([sx - ex, sx + ex], [sy - ey, sy + ey])
        if box is None:
            return
        x0, y0, x1, y1 = box
        ys, xs = np.mgrid[y0:y1, x0:x1].astype(np.float64)
        dx, dy = xs + 0.5 - sx, -(ys + 0.5 - sy)
        lx = (dx * c + dy * s) / (2 * hw) + 0.5
        ly = (-dx * s + dy * c) / (2 * hh) + 0.5
        inside = (lx >= 0) & (lx <= 1) & (ly >= 0) & (ly <= 1)
        if not inside.any():
            return
        rgb, a = cel_shade(tex, lx, ly, color, fade, additive, st)
        self.composite(box, rgb, a * inside, additive)

    def plane(self, tex, origin, ax, ay, extent, uv_fn, color, fade, additive, st=(1, 1, 0, 0)):
        """World-space planar primitive: point = origin + lx*ax + ly*ay, (lx, ly) within +-extent.
        uv_fn(lx, ly) -> (u, v, mask)."""
        corners = [origin + sx_ * extent * ax + sy_ * extent * ay for sx_ in (-1, 1) for sy_ in (-1, 1)]
        pts = [self.project(p) for p in corners]
        if min(p[2] for p in pts) <= 0.1:
            return
        box = self.clip_box([p[0] for p in pts], [p[1] for p in pts])
        if box is None:
            return
        x0, y0, x1, y1 = box
        dirs, _, _ = self.rays(x0, y0, x1, y1)
        n = np.cross(ax, ay)
        denom = dirs @ n
        t = ((origin - self.cam) @ n) / np.where(np.abs(denom) < 1e-9, 1e-9, denom)
        hit = self.cam[None, None] + dirs * t[..., None] - origin
        bx, by = np.cross(ay, n), np.cross(n, ax)
        lx = (hit @ bx) / (ax @ bx)
        ly = (hit @ by) / (ay @ by)
        u, v, mask = uv_fn(lx, ly)
        if not mask.any():
            return
        rgb, a = cel_shade(tex, u, v, color, fade, additive, st)
        self.composite(box, rgb, a * mask, additive)

    def sphere(self, tex, center, radius, spin_deg, color, fade, additive):
        sx, sy, z = self.project(center)
        rr = radius / z * self.focal * 1.15
        box = self.clip_box([sx - rr, sx + rr], [sy - rr, sy + rr])
        if box is None:
            return
        x0, y0, x1, y1 = box
        dirs, _, _ = self.rays(x0, y0, x1, y1)
        dirs = dirs / np.linalg.norm(dirs, axis=-1, keepdims=True)
        oc = self.cam - center
        b = dirs @ oc
        c = oc @ oc - radius * radius
        disc = b * b - c
        mask = disc > 0
        sq = np.sqrt(np.clip(disc, 0, None))
        for t in (-b + sq, -b - sq):   # back face first, then front (Cull Off)
            p = (self.cam[None, None] + dirs * t[..., None] - center) / radius
            ang = math.radians(spin_deg)
            px_ = p[..., 0] * math.cos(ang) - p[..., 2] * math.sin(ang)
            pz_ = p[..., 0] * math.sin(ang) + p[..., 2] * math.cos(ang)
            u = (np.arctan2(pz_, px_) % (2 * math.pi)) / (2 * math.pi)
            v = np.arccos(np.clip(p[..., 1], -1, 1)) / math.pi
            rgb, a = cel_shade(tex, u, v, color, fade, additive)
            self.composite(box, rgb, a * mask, additive)


# ----------------------------------------------------------------------------- backdrop

def backdrop(cv):
    h, w = cv.h, cv.w
    dirs, _, _ = cv.rays(0, 0, w, h)
    t = -cv.cam[1] / np.where(dirs[..., 1] < -1e-6, dirs[..., 1], -1e-6)
    hit = cv.cam[None, None] + dirs * t[..., None]
    floor = dirs[..., 1] < -1e-3
    gx, gz = hit[..., 0], hit[..., 2]
    tile = (np.abs(((gx / 1.1) % 1) - 0.5) > 0.47) | (np.abs(((gz / 1.1 + 0.5 * (np.floor(gx / 1.1) % 2)) % 1) - 0.5) > 0.47)
    dist = np.sqrt(gx ** 2 + gz ** 2)
    fl = np.array([0.075, 0.07, 0.10]) * (1.0 - 0.35 * tile[..., None]) * (1.2 - 0.35 * np.clip(dist / 6, 0, 1))[..., None]
    yy = np.linspace(1, 0, h)[:, None, None]
    xx = np.linspace(-1, 1, w)[None, :, None]
    wall = np.array([0.05, 0.045, 0.085]) * (0.6 + 0.6 * yy) * (1 - 0.25 * xx ** 2)
    bricks = ((np.floor(np.linspace(0, 9, h))[:, None] % 1) + (np.abs(((np.linspace(0, 6, w)[None, :] + 0.5 * (np.floor(np.linspace(0, 9, h))[:, None] % 2)) % 1) - 0.5) > 0.48)) > 0
    wall = wall * (1 - 0.18 * bricks[..., None])
    cv.buf[:] = np.where(floor[..., None], fl, wall)
    # a faint figure stand-in so scale reads (1.6 m silhouette at the origin)
    figure = []
    for y in np.linspace(0.05, 1.55, 12):
        figure.append(cv.project(np.array([0, y, 0.25])))
    xs, ys = [f[0] for f in figure], [f[1] for f in figure]
    width = 0.42 / figure[0][2] * cv.focal / 2
    box = cv.clip_box([min(xs) - width, max(xs) + width], [min(ys) - width * 0.6, max(ys)])
    if box:
        x0, y0, x1, y1 = box
        yy2, xx2 = np.mgrid[y0:y1, x0:x1]
        cx = np.mean(xs)
        head_y = min(ys) + width * 0.6
        body = (np.abs(xx2 - cx) < width * (0.55 + 0.35 * np.clip((yy2 - head_y) / (max(ys) - head_y), 0, 1))) & (yy2 > head_y + width * 0.55)
        head = (xx2 - cx) ** 2 + (yy2 - head_y) ** 2 < (width * 0.5) ** 2
        m = (body | head)[..., None]
        cv.buf[y0:y1, x0:x1] = np.where(m, cv.buf[y0:y1, x0:x1] * 0.45 + np.array([0.09, 0.085, 0.12]), cv.buf[y0:y1, x0:x1])


def blur(img, sigma):
    if sigma <= 0:
        return img
    r = int(math.ceil(sigma * 3))
    p = np.pad(img, ((r, r), (r, r), (0, 0)), mode="edge")
    fy = np.fft.fftfreq(p.shape[0])[:, None]
    fx = np.fft.rfftfreq(p.shape[1])[None, :]
    g = np.exp(-2 * (math.pi * sigma) ** 2 * (fx * fx + fy * fy))
    out = np.stack([np.fft.irfft2(np.fft.rfft2(p[..., c]) * g, s=p.shape[:2]) for c in range(3)], axis=-1)
    return out[r:-r, r:-r]


def finish(cv):
    hdr = cv.buf
    bright = np.clip(hdr - 0.85, 0, None)
    s = cv.h / 360
    bloom = blur(bright, 4 * s) * 0.55 + blur(bright, 14 * s) * 0.45
    out = hdr + bloom
    out = out / (1 + np.clip(out - 1, 0, None) * 0.15)   # gentle shoulder for very hot spots
    return Image.fromarray((np.clip(out, 0, 1) ** (1 / 1.0) * 255 + 0.5).astype(np.uint8), "RGB")


# ----------------------------------------------------------------------------- recipe simulation

def size_curve(t, additive):
    end = 0.05 if additive else 1.6
    return np.where(t < 0.2, 0.45 + (1 - 0.45) * t / 0.2, 1 + (end - 1) * (t - 0.2) / 0.8)


def alpha_curve(t):
    return np.interp(t, [0, 0.1, 0.6, 1.0], [0, 1, 0.7, 0])


def unit_sphere(rng, n):
    d = rng.normal(size=(n, 3))
    return d / np.linalg.norm(d, axis=1, keepdims=True)


class Particle:
    __slots__ = ("pos", "size", "rot", "age", "life")


def simulate_particles(L, elapsed, end_time, seed):
    """Returns list of (pos(3), size, rotation_deg, normalised_age) for one burst/emitter layer."""
    rng = np.random.default_rng(seed)
    g = np.array([0, -9.81 * L["gravity"], 0])
    out = []
    max_particles = int(np.clip(math.ceil(L["rate"] * L["life"] * 3) + L["count"] * 2, 32, 512))
    if L["kind"] == "burst":
        n = L["count"]
        dirs = unit_sphere(rng, n)
        r0 = L["radius"] * rng.uniform(0, 1, n) ** (1 / 3)
        speed = rng.uniform(0.4, 1.0, n) * L["speed"]
        life = rng.uniform(0.7, 1.0, n) * L["life"]
        size = rng.uniform(0.6, 1.0, n) * L["size"]
        rot = np.zeros(n) if L["upright"] else rng.uniform(-180, 180, n)
        for i in range(n):
            age = elapsed
            if age < 0 or age >= life[i]:
                continue
            p = dirs[i] * r0[i] + dirs[i] * speed[i] * age + 0.5 * g * age * age
            out.append((p, size[i], rot[i], age / life[i]))
    else:  # emitter: horizontal disc, upward drift
        spawn_until = min(elapsed, end_time)
        count = int(spawn_until * L["rate"]) + 1
        times = np.arange(count) / max(L["rate"], 1e-3)
        n = len(times)
        ang = rng.uniform(0, 2 * math.pi, n)
        rad = L["radius"] * np.sqrt(rng.uniform(0, 1, n))
        vx = rng.uniform(-0.15, 0.15, n)
        vz = rng.uniform(-0.15, 0.15, n)
        vy = rng.uniform(0.7, 1.2, n) * L["speed"]
        life = rng.uniform(0.7, 1.0, n) * L["life"]
        size = rng.uniform(0.6, 1.0, n) * L["size"]
        rot = np.zeros(n) if L["upright"] else rng.uniform(-180, 180, n)
        alive = 0
        for i in range(n - 1, -1, -1):
            age = elapsed - times[i]
            if age < 0 or age >= life[i] or times[i] > end_time:
                continue
            alive += 1
            if alive > max_particles:
                break
            p = np.array([math.cos(ang[i]) * rad[i] + vx[i] * age, vy[i] * age, math.sin(ang[i]) * rad[i] + vz[i] * age]) + 0.5 * g * age * age
            out.append((p, size[i], rot[i], age / life[i]))
    return out


def flip_st(tiles, frame):
    t = tiles
    return (1.0 / t, 1.0 / t, (frame % t) / t, 1.0 - (frame // t + 1) / t)


def norm_layer(L):
    out = dict(LAYER_DEFAULTS)
    out.update(L)
    return out


def ring_uv(lx, ly):
    r = np.sqrt(lx * lx + ly * ly)
    u = (np.arctan2(ly, lx) % (2 * math.pi)) / (2 * math.pi)
    v = (r - 0.44) / 0.06
    return u, v, (v >= 0) & (v <= 1)


def arc_uv(lx, ly):
    r = np.sqrt(lx * lx + ly * ly)
    a = np.degrees(np.arctan2(ly, lx))
    t = a / 135.0
    inner = 0.5 - 0.18 * np.sin(np.clip(t, 0, 1) * math.pi)
    v = (r - inner) / np.maximum(0.5 - inner, 1e-4)
    return t, v, (t >= 0) & (t <= 1) & (v >= 0) & (v <= 1) & (r <= 0.5)


def quad_uv(lx, ly):
    u, v = lx + 0.5, ly + 0.5
    return u, v, (u >= 0) & (u <= 1) & (v >= 0) & (v <= 1)


def render_effect(cv, recipe, t, origin=(0, 0.9, 0), tint=(1, 1, 1), scale=1.0, tex_dir=TEX_DIR, seed=0):
    origin = np.asarray(origin, dtype=np.float64)
    tint = np.asarray(tint, dtype=np.float32)
    loop = recipe.get("loop", False)
    duration = recipe.get("duration", 1.2)
    view_rot = 0.0
    for li, raw in enumerate(recipe["layers"]):
        L = norm_layer(raw)
        elapsed = t - L["delay"]
        if elapsed < 0:
            continue
        if not loop and t > duration and L["kind"] not in ("burst", "emitter", "trail"):
            # Ending drain: quads keep fading over their own life; approximate by just continuing below.
            pass
        tex = texture(L["texture"], tex_dir)
        color = hex_color(L["color"]) * tint
        additive = not L["alpha"]
        pos = origin + np.array([0, L["y"] * scale, 0])
        kind = L["kind"]
        if kind in ("burst", "emitter"):
            end_time = (math.inf if loop else duration) - L["delay"]
            parts = simulate_particles(L, elapsed, end_time, seed * 101 + li)
            parts.sort(key=lambda p: -float((p[0] + pos - cv.cam) @ cv.f))
            for p, size, rot, age in parts:
                s = size * float(size_curve(age, additive)) * scale
                fade = float(alpha_curve(age))
                st = (1, 1, 0, 0)
                if L["tiles"] > 1:
                    frame = min(L["tiles"] ** 2 - 1, int(age * L["tiles"] ** 2))
                    st = flip_st(L["tiles"], frame)
                cv.sprite(tex, pos + p * scale, s, s, rot, color, fade, additive, st)
            continue
        if kind == "trail":
            # Trails only draw while the effect travels; preview it as a ribbon streaming left.
            length = 6.0 * L["life"] * scale
            n = 10
            for k in range(n):
                f0 = k / n
                p = pos + np.array([-length * (f0 + 0.5 / n), 0, 0])
                cv.sprite(tex, p, length / n * 1.25, L["size"] * scale * (1 - f0), 0, color, 1 - f0, additive)
            continue
        life = max(L["life"], 1e-3)
        if loop:
            p = (elapsed / life) % 1.0
            fade = 0.65 + 0.2 * math.sin(elapsed * 3)
        else:
            p = min(1.0, elapsed / life)
            if p >= 1:
                continue
            fade = min(p * 10, 1) * (1 - p)
        size = L["size"] + ((L["endSize"] if L["endSize"] > 0 else L["size"]) - L["size"]) * p
        st = (1, 1, 0, 0)
        if L["tiles"] > 1:
            frame = min(L["tiles"] ** 2 - 1, int(p * L["tiles"] ** 2))
            st = flip_st(L["tiles"], frame)
        rot = L["rotation"] + elapsed * L["spin"]
        if kind == "orbit":
            n = max(1, L["count"])
            for k in range(n):
                ang = math.radians(elapsed * L["spin"]) + k * 2 * math.pi / n
                gp = pos + np.array([math.cos(ang) * L["radius"], math.sin(elapsed * 2 + k) * 0.08, math.sin(ang) * L["radius"]]) * scale
                cv.sprite(tex, gp, size * scale, size * scale, 0, color, fade, additive, st)
            continue
        if kind == "sphere":
            cv.sphere(tex, pos, 0.5 * size * scale, elapsed * L["spin"], color, fade, additive)
            continue
        sx_ = size * scale
        sy_ = (L["height"] if L["height"] > 0 else size) * scale
        if kind == "ring" or (kind == "quad" and L["horizontal"]) or (kind == "arc" and L["horizontal"]):
            if kind == "ring":
                sx_ = sy_ = size * scale
            a = math.radians(rot)
            ax = np.array([math.cos(a), 0, math.sin(a)]) * sx_
            ay = np.array([-math.sin(a), 0, math.cos(a)]) * sy_
            fn = ring_uv if kind == "ring" else arc_uv if kind == "arc" else quad_uv
            cv.plane(tex, pos, ax, ay, 0.5, fn, color, fade, additive, st)
            continue
        if kind == "arc":
            a = math.radians(rot)
            ax = (cv.r * math.cos(a) + cv.u * math.sin(a)) * sx_
            ay = (-cv.r * math.sin(a) + cv.u * math.cos(a)) * sy_
            cv.plane(tex, pos, ax, ay, 0.5, arc_uv, color, fade, additive, st)
            continue
        cv.sprite(tex, pos, sx_, sy_, rot, color, fade, additive, st)


def effect_energy(recipe, t, tint, tex_dir):
    cv = Canvas(96, 96)
    render_effect(cv, recipe, t, tint=tint, tex_dir=tex_dir)
    return float(np.clip(cv.buf, 0, 1.5).sum())


def peak_time(recipe, tint, tex_dir=TEX_DIR):
    dur = recipe.get("duration", 1.2)
    span = min(dur, 1.6) if recipe.get("loop") else dur
    times = np.linspace(0.04, max(0.08, span * 0.9), 14)
    scores = [effect_energy(recipe, float(t), tint, tex_dir) for t in times]
    return float(times[int(np.argmax(scores))])


# ----------------------------------------------------------------------------- sheets

def font(size):
    for path in ("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", "/usr/share/fonts/dejavu/DejaVuSans-Bold.ttf",
                 os.path.join(ROOT, "Assets", "TextMesh Pro", "Fonts", "LiberationSans.ttf")):
        if os.path.exists(path):
            return ImageFont.truetype(path, size)
    return ImageFont.load_default()


def render_cell(recipe, size, tint, t=None, tex_dir=TEX_DIR, distance=8.2, look_y=1.45):
    if t is None:
        t = peak_time(recipe, tint, tex_dir)
    cv = Canvas(size, size, look=(0, look_y, 0), distance=distance)
    backdrop(cv)
    render_effect(cv, recipe, t, tint=tint, tex_dir=tex_dir)
    return finish(cv), t


def effect_grid(keys, out, recipes, cell=300, cols=6, title=None, tints=None, strip=True):
    pad, label_h, strip_h = 8, 34, (cell // 3 if strip else 0)
    rows = (len(keys) + cols - 1) // cols
    head = 54 if title else 0
    W = cols * (cell + pad) + pad
    H = head + rows * (cell + strip_h + label_h + pad) + pad
    sheet = Image.new("RGB", (W, H), (14, 12, 22))
    d = ImageDraw.Draw(sheet)
    f_big, f, f_small = font(26), font(17), font(12)
    if title:
        d.text((pad + 4, 12), title, fill=(255, 226, 150), font=f_big)
    for i, key in enumerate(keys):
        if isinstance(key, tuple):
            key, label = key
        else:
            label = key
        recipe = recipes[key]
        tint = (tints or {}).get(key, hex_color(DEFAULT_TINTS.get(key, "FFFFFF")))
        img, t = render_cell(recipe, cell, tint)
        x = pad + (i % cols) * (cell + pad)
        y = head + pad + (i // cols) * (cell + strip_h + label_h + pad)
        sheet.paste(img, (x, y))
        if strip:
            dur = recipe.get("duration", 1.2)
            sw = cell // 3
            for k, frac in enumerate((0.12, 0.45, 0.8)):
                tt = max(0.03, min(dur if not recipe.get("loop") else 1.5, 1.6) * frac)
                small, _ = render_cell(recipe, sw * 2, tint, tt)
                sheet.paste(small.resize((sw, sw), Image.LANCZOS), (x + k * sw, y + cell))
                d.text((x + k * sw + 3, y + cell + 2), f"{tt:.2f}s", fill=(200, 200, 220), font=f_small)
        d.text((x + 4, y + cell + strip_h + 4), label, fill=(255, 230, 170), font=f)
        d.text((x + 4, y + 4), f"peak {t:.2f}s", fill=(190, 190, 210), font=f_small)
    sheet.save(out)
    return out


def texture_sheet(old_dir, new_dir, out, cell=150, cols=8):
    """Before/after sheet: each texture shown raw (alpha over checker-free dark) and as the cel shader
    draws it (additive, warm tint). New-only textures are marked NEW."""
    names = sorted(set(f[:-4] for f in os.listdir(new_dir) if f.endswith(".png")))
    olds = set(f[:-4] for f in os.listdir(old_dir) if f.endswith(".png"))
    pad, label_h = 6, 22
    pair_w = cell * 2 + 4
    rows = (len(names) + cols - 1) // cols
    head = 60
    W = cols * (pair_w + pad) + pad
    H = head + rows * (cell + label_h + pad) + pad
    sheet = Image.new("RGB", (W, H), (14, 12, 22))
    d = ImageDraw.Draw(sheet)
    f_big, f = font(24), font(13)
    d.text((pad + 4, 10), "VFX textures: left = before (HEAD), right = after; both drawn through the cel shader (additive, tinted)",
           fill=(255, 226, 150), font=f_big)
    d.text((pad + 4, 38), "alpha-blended art (smoke, icons, leaf, petal, rock, rift) shown alpha-blended; flipbooks show the whole sheet",
           fill=(190, 190, 210), font=f)
    alpha_names = {"smoke_sheet", "leaf", "petal", "rock", "rift", "thorn", "star5", "zzz", "note", "silence", "anger", "blind", "droplet"}

    def shaded(directory, name):
        tex = texture(name, directory)
        h, w = tex.shape[:2]
        aspect = w / h
        cw, ch = (cell, int(cell / aspect)) if aspect >= 1 else (int(cell * aspect), cell)
        img = np.zeros((cell, cell, 3), np.float32) + np.array([0.06, 0.055, 0.1], np.float32)
        ys, xs = np.mgrid[0:ch, 0:cw].astype(np.float64)
        u, v = (xs + 0.5) / cw, 1 - (ys + 0.5) / ch
        additive = name not in alpha_names
        color = np.array([1.0, 0.72, 0.38], np.float32) if additive else np.array([0.85, 0.8, 0.95], np.float32)
        if name in ("hex", "noise", "cells"):
            color = np.array([0.5, 0.8, 1.0], np.float32)
        rgb, a = cel_shade(tex, u, v, color, np.ones_like(u), additive, core_radius=0.014)
        oy, ox = (cell - ch) // 2, (cell - cw) // 2
        region = img[oy:oy + ch, ox:ox + cw]
        if additive:
            region += rgb * a[..., None]
        else:
            region[:] = region * (1 - a[..., None]) + rgb * a[..., None]
        bright = np.clip(img - 0.85, 0, None)
        img = img + blur(bright, 3) * 0.6
        return Image.fromarray((np.clip(img, 0, 1) * 255).astype(np.uint8)), (w, h)

    total_old = total_new = 0
    for i, name in enumerate(names):
        x = pad + (i % cols) * (pair_w + pad)
        y = head + (i // cols) * (cell + label_h + pad)
        if name in olds:
            img, (w0, h0) = shaded(old_dir, name)
            total_old += w0 * h0 * 4
            sheet.paste(img, (x, y))
        else:
            d.rectangle([x, y, x + cell - 1, y + cell - 1], fill=(26, 22, 38))
            d.text((x + cell // 2 - 18, y + cell // 2 - 8), "NEW", fill=(120, 255, 170), font=font(18))
        img, (w1, h1) = shaded(new_dir, name)
        total_new += w1 * h1 * 4
        sheet.paste(img, (x + cell + 4, y))
        d.text((x + 2, y + cell + 3), f"{name}  {w1}x{h1}", fill=(255, 230, 170), font=f)
    d.text((W - 520, 38), f"RGBA32 memory: before {total_old / 2**20:.1f} MiB, after {total_new / 2**20:.1f} MiB",
           fill=(160, 255, 200), font=f)
    sheet.save(out)
    return total_old, total_new


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--keys", default="")
    ap.add_argument("--out", default=os.path.join(ROOT, "Temp", "vfx_effects.png"))
    ap.add_argument("--time", type=float, default=None)
    ap.add_argument("--tint", default=None)
    ap.add_argument("--cell", type=int, default=300)
    ap.add_argument("--cols", type=int, default=6)
    ap.add_argument("--title", default=None)
    ap.add_argument("--no-strip", action="store_true")
    ap.add_argument("--textures", default=None, help="old texture dir for a before/after sheet")
    args = ap.parse_args()
    os.makedirs(os.path.dirname(os.path.abspath(args.out)), exist_ok=True)
    if args.textures:
        old, new = texture_sheet(args.textures, TEX_DIR, args.out)
        print(f"texture sheet -> {args.out} (before {old / 2**20:.1f} MiB, after {new / 2**20:.1f} MiB)")
        return
    recipes = {r["key"]: r for r in json.load(open(EFFECTS, encoding="utf-8"))["effects"]}
    keys = [k for k in args.keys.split(",") if k] or [k for k in recipes if not k.startswith(("status_", "environment_"))]
    tints = None
    if args.tint:
        tints = {k: hex_color(args.tint) for k in keys}
    if args.time is not None:
        for k in keys:
            img, _ = render_cell(recipes[k], args.cell, (tints or {}).get(k, hex_color(DEFAULT_TINTS.get(k, "FFFFFF"))), args.time)
            img.save(args.out if len(keys) == 1 else args.out.replace(".png", f"_{k}.png"))
        return
    effect_grid(keys, args.out, recipes, cell=args.cell, cols=args.cols, title=args.title, tints=tints, strip=not args.no_strip)
    print("effect grid ->", args.out)


if __name__ == "__main__":
    main()
