"""Procedural texture generator for the Abyss VFX library (anime / cel style).

Writes RGBA PNGs into Assets/_Game/Resources/Vfx/Textures and a labelled preview sheet to Temp/vfx_textures.png.

How the textures are read (Assets/_Game/Shaders/VfxUnlit.shader, _Cel = 1):
  * ALPHA is the shape. The shader posterises it into three bands, so anything below 1/3 vanishes,
    1/3..2/3 draws a dim band, 2/3..1 a mid band and a fully solid 1.0 the full-strength band.
    The art below is therefore painted in deliberate plateaus: CORE (1.0), MID (~0.82), DIM (~0.5).
    Noise in those plateaus makes the shape erode organically when the layer fades (the shader raises
    the cut-off as the tint alpha drops).
  * RED is "heat" on additive layers: where R is high AND the neighbourhood is solid, the band burns
    white-hot (HDR, bloom picks it up). Strokes thinner than ~3% of the texture keep the tint.
    HOT (1.0) marks white cores, TINT (0.45) keeps a solid area coloured.
  * RGB is two-tone shading on alpha-blended layers (smoke, debris, icons): luminance > .55 is the lit
    tone, .25..55 the shadow tone, < .25 ink that stays dark.
Flipbooks are N x N grids read left-to-right, top-to-bottom (VfxLibrary `tiles`).

Usage: python Tools/vfx/gen_textures.py [name ...]   (names limit the run to those textures)
Deterministic (fixed seeds) so re-running produces identical files. Existing .meta files are never
rewritten (GUIDs and import settings stay as Unity has them); a .meta is only created for a new texture.
"""
import math
import os
import sys

import numpy as np
from PIL import Image, ImageDraw, ImageFilter

ROOT = os.path.normpath(os.path.join(os.path.dirname(__file__), "..", ".."))
OUT = os.path.join(ROOT, "Assets", "_Game", "Resources", "Vfx", "Textures")
PREVIEW = os.path.join(ROOT, "Temp", "vfx_textures.png")
sys.path.insert(0, os.path.join(ROOT, "Tools", "ui"))
from asset_import import texture_meta  # noqa: E402

RNG = np.random.default_rng(1234)
WRITTEN = []
ONLY = set(a for a in sys.argv[1:] if not a.startswith("-"))

CORE, MID, DIM = 1.0, 0.82, 0.5     # alpha plateaus -> shader bands 1, 2/3, 1/3
HOT, TINT = 1.0, 0.45                # red-channel heat: white core vs solid tint


# ----------------------------------------------------------------------------- helpers

def grid(w, h=None):
    """Centred coordinates: u right, v up, both in [-1, 1]."""
    h = h or w
    y, x = np.mgrid[0:h, 0:w].astype(np.float64)
    u = (x + 0.5) / w * 2 - 1
    v = 1 - (y + 0.5) / h * 2
    return u, v


def sstep(e0, e1, x):
    t = np.clip((x - e0) / (e1 - e0), 0, 1)
    return t * t * (3 - 2 * t)


def gauss_blur(a, sigma, wrap=False):
    """Gaussian blur via FFT (edges clamp unless wrap)."""
    if sigma <= 0:
        return a
    r = int(math.ceil(sigma * 3))
    p = np.pad(a, r, mode="wrap" if wrap else "edge")
    fy = np.fft.fftfreq(p.shape[0])[:, None]
    fx = np.fft.rfftfreq(p.shape[1])[None, :]
    g = np.exp(-2 * (math.pi * sigma) ** 2 * (fx * fx + fy * fy))
    out = np.fft.irfft2(np.fft.rfft2(p) * g, s=p.shape)
    return out[r:-r, r:-r]


def conv_blur(a, sigma):
    """Original separable convolution blur (kept so the legacy icon textures stay pixel-identical)."""
    r = int(math.ceil(sigma * 3))
    k = np.exp(-0.5 * (np.arange(-r, r + 1) / sigma) ** 2)
    k /= k.sum()
    p = np.pad(a, ((r, r), (r, r)), mode="edge")
    tmp = np.apply_along_axis(lambda m: np.convolve(m, k, mode="valid"), 1, p)
    return np.apply_along_axis(lambda m: np.convolve(m, k, mode="valid"), 0, tmp)


def tile_noise(n, beta=2.0, seed=0):
    """Tileable fractal noise via spectral synthesis, normalised to [0, 1]."""
    rng = np.random.default_rng(seed)
    white = rng.standard_normal((n, n))
    fx = np.fft.fftfreq(n)[None, :]
    fy = np.fft.fftfreq(n)[:, None]
    f = np.sqrt(fx * fx + fy * fy)
    f[0, 0] = 1
    spec = np.fft.fft2(white) / f ** (beta / 2)
    spec[0, 0] = 0
    out = np.real(np.fft.ifft2(spec))
    out -= out.min()
    return out / out.max()


def nsample(n, x, y):
    """Bilinear, wrapping lookup of a square noise tile at texel coordinates x, y."""
    N = n.shape[0]
    x0 = np.floor(x).astype(int)
    y0 = np.floor(y).astype(int)
    fx, fy = x - x0, y - y0
    x0 %= N
    y0 %= N
    x1, y1 = (x0 + 1) % N, (y0 + 1) % N
    return (n[y0, x0] * (1 - fx) * (1 - fy) + n[y0, x1] * fx * (1 - fy)
            + n[y1, x0] * (1 - fx) * fy + n[y1, x1] * fx * fy)


def ang_noise(theta, harmonics, seed, falloff=1.0):
    """Periodic 1-D noise over an angle, roughly in [-1, 1]."""
    rng = np.random.default_rng(seed)
    out = np.zeros_like(theta)
    total = 0
    for k in range(1, harmonics + 1):
        amp = 1 / k ** falloff
        out += amp * np.sin(k * theta + rng.uniform(0, 2 * math.pi))
        total += amp
    return out / total * 1.6


def canvas(w, h=None, ss=4):
    h = h or w
    img = Image.new("L", (w * ss, h * ss), 0)
    return img, ImageDraw.Draw(img), ss


def to_alpha(img, w, h=None):
    h = h or w
    return np.asarray(img.resize((w, h), Image.LANCZOS), dtype=np.float64) / 255.0


def glowify(a, sigma, amount, core=1.0):
    """Adds a soft halo around a hard alpha mask (legacy icons)."""
    halo = conv_blur(a, sigma)
    halo = halo / max(halo.max(), 1e-6)
    return np.clip(np.maximum(a * core, halo * amount), 0, 1)


def halo(mask, sigma, level=DIM, reach=0.5):
    """A flat DIM band that hugs a shape (blurred mask thresholded softly)."""
    b = gauss_blur(mask, sigma)
    return sstep(reach * 0.25, reach * 0.6, b) * level


def save(name, alpha, rgb=1.0):
    if ONLY and name not in ONLY:
        return
    alpha = np.clip(alpha, 0, 1)
    h, w = alpha.shape
    if np.isscalar(rgb):
        rgb = np.full((h, w, 3), rgb)
    elif rgb.ndim == 2:
        rgb = np.repeat(rgb[:, :, None], 3, axis=2)
    arr = np.dstack([np.clip(rgb, 0, 1), alpha])
    os.makedirs(OUT, exist_ok=True)
    path = os.path.join(OUT, name + ".png")
    pixels = (arr * 255 + 0.5).astype(np.uint8)
    unchanged = False
    if os.path.exists(path):   # keep byte-identical files when the pixels did not change (no git churn)
        with Image.open(path) as old:
            unchanged = old.mode == "RGBA" and np.array_equal(np.asarray(old), pixels)
    if not unchanged:
        Image.fromarray(pixels, "RGBA").save(path, optimize=True)
    if not os.path.exists(path + ".meta"):   # never rewrite an existing importer/GUID
        texture_meta(path, repeat=name in ("noise", "cells", "trail", "beam"))
    WRITTEN.append(name)


def rot(points, ang, cx=0.0, cy=0.0):
    c, s = math.cos(ang), math.sin(ang)
    return [(cx + x * c - y * s, cy + x * s + y * c) for x, y in points]


def px(points, w, h, ss):
    """Map centred [-1,1] coordinates (v up) to supersampled pixel coordinates."""
    return [((x + 1) * 0.5 * w * ss, (1 - y) * 0.5 * h * ss) for x, y in points]


def poly_mask(w, h, polys, ss=4, width=0):
    img, d, ss = canvas(w, h, ss)
    for p in polys:
        if width:
            d.line(px(p, w, h, ss), fill=255, width=max(1, int(width * ss)), joint="curve")
        else:
            d.polygon(px(p, w, h, ss), fill=255)
    return to_alpha(img, w, h)


def disc(d, w, h, ss, x, y, r, fill=255, outline=None, width=0):
    q = px([(x, y)], w, h, ss)[0]
    rx, ry = r * w * ss / 2, r * w * ss / 2
    if outline is not None:
        d.ellipse([q[0] - rx, q[1] - ry, q[0] + rx, q[1] + ry], outline=outline, width=max(1, int(width * ss)))
    else:
        d.ellipse([q[0] - rx, q[1] - ry, q[0] + rx, q[1] + ry], fill=fill)


def lens(length, width, n=24, power=1.0):
    """Closed polygon of a pointed lens along +x from 0..length (blade / ray / feather)."""
    top, bot = [], []
    for k in range(n + 1):
        t = k / n
        wd = width * math.sin(math.pi * t) ** power
        top.append((t * length, wd))
        bot.append((t * length, -wd))
    return top + bot[::-1]


def ray(length, width, n=16, power=1.3):
    """Polygon that starts at width at the origin and tapers to a point at +length."""
    top, bot = [], []
    for k in range(n + 1):
        t = k / n
        wd = width * (1 - t) ** power
        top.append((t * length, wd))
        bot.append((t * length, -wd))
    return top + bot[::-1]


# ----------------------------------------------------------------------------- basic shapes

def glow():
    """Round bloom: white core, then two clean colour bands."""
    u, v = grid(128)
    r = np.sqrt(u * u + v * v)
    a = np.maximum(sstep(0.22, 0.18, r), np.exp(-r * r * 3.2) * 0.97) * sstep(1.0, 0.82, r)
    save("glow", a, sstep(0.2, 0.1, r) * HOT + TINT * 0.6)


def glow_hard():
    u, v = grid(128)
    r = np.sqrt(u * u + v * v)
    a = np.maximum.reduce([sstep(0.42, 0.38, r) * CORE, sstep(0.60, 0.56, r) * MID, sstep(0.82, 0.76, r) * DIM])
    save("glow_hard", a, sstep(0.36, 0.30, r) * HOT + TINT * 0.5)


def dot():
    u, v = grid(64)
    r = np.sqrt(u * u + v * v)
    a = np.maximum(sstep(0.62, 0.52, r), sstep(0.92, 0.84, r) * DIM)
    save("dot", a, sstep(0.6, 0.4, r))


def square():
    """Angular glass/shield fragment with two facets (break, debris)."""
    w = 64
    rng = np.random.default_rng(42)
    pts = [(-0.7, 0.55), (0.1, 0.9), (0.8, 0.2), (0.35, -0.85), (-0.55, -0.45)]
    pts = [(x + rng.uniform(-0.05, 0.05), y + rng.uniform(-0.05, 0.05)) for x, y in pts]
    outer = poly_mask(w, w, [pts])
    face = poly_mask(w, w, [[pts[0], pts[1], pts[2], (0.0, 0.0)]])
    a = np.maximum(outer * MID, face * CORE)
    save("square", a, face * HOT * 0.95 + (1 - face) * 0.55)


def spark():
    """Sharp diamond streak: white needle core, coloured lens, dim tips."""
    u, v = grid(128, 32)
    t = np.clip(1 - np.abs(u), 0, 1)
    av = np.abs(v)
    core = sstep(0.34 * t ** 1.4 + 0.01, 0.30 * t ** 1.4, av) * (t > 0.02)
    mid = sstep(0.62 * t ** 1.2 + 0.02, 0.56 * t ** 1.2, av)
    dim = sstep(0.95 * t ** 0.9 + 0.03, 0.85 * t ** 0.9, av)
    a = np.maximum.reduce([core * CORE, mid * MID, dim * DIM])
    save("spark", a, np.clip(core * HOT * sstep(0.2, 0.6, t) + TINT * 0.4, 0, 1))


def ember():
    """Tiny four-point ember/glint used by drifting particles."""
    w = 64
    polys = []
    for k, L in enumerate((0.95, 0.55, 0.95, 0.55)):
        polys.append(rot(ray(L, 0.16 if L > 0.6 else 0.12, power=1.2), k * math.pi / 2))
    core = poly_mask(w, w, polys)
    u, v = grid(w)
    r = np.sqrt(u * u + v * v)
    a = np.maximum.reduce([core * CORE, sstep(0.5, 0.42, r) * MID, sstep(0.7, 0.6, r) * DIM])
    save("ember", a, sstep(0.3, 0.12, r) * HOT + TINT * 0.6)


def star_glint(name, size, rays, diag, seed=0):
    """Anime star glint: needle rays (white core + colour sheath), short diagonals, round bloom."""
    polys_core, polys_sheath = [], []
    for ang, length, width in rays:
        polys_core.append(rot(ray(length, width * 0.45, power=1.6), ang))
        polys_sheath.append(rot(ray(length * 1.02, width, power=1.25), ang))
    for ang, length, width in diag:
        polys_sheath.append(rot(ray(length, width, power=1.3), ang))
    core = poly_mask(size, size, polys_core)
    sheath = poly_mask(size, size, polys_sheath)
    u, v = grid(size)
    r = np.sqrt(u * u + v * v)
    hub = sstep(0.11, 0.08, r)
    bloom = sstep(0.34, 0.28, r)
    a = np.maximum.reduce([np.maximum(core, hub) * CORE, sheath * MID, bloom * DIM, halo(sheath, size / 90, DIM, 0.6)])
    heat = np.maximum(core, hub) * HOT * sstep(0.75, 0.1, r) + TINT * 0.5
    save(name, a, heat)


def star4():
    star_glint("star4", 256,
               [(math.pi / 2, 1.0, 0.07), (-math.pi / 2, 1.0, 0.07), (0, 0.78, 0.065), (math.pi, 0.78, 0.065)],
               [(math.pi / 4 + k * math.pi / 2, 0.32, 0.04) for k in range(4)])


def star8():
    rays = []
    for k in range(8):
        long = k % 2 == 0
        rays.append((k * math.pi / 4 + math.pi / 2, 1.0 if long else 0.6, 0.075 if long else 0.06))
    star_glint("star8", 256, rays, [(k * math.pi / 4 + math.pi / 8 + math.pi / 2, 0.28, 0.03) for k in range(8)])


def star5():
    """Chunky cartoon 5-point star with a dark outline (alpha blended icons, stun)."""
    w = 128
    img, d, ss = canvas(w)
    pts = []
    for i in range(10):
        th = math.pi / 2 + i * math.pi / 5
        rr = 0.86 if i % 2 == 0 else 0.40
        pts.append((rr * math.cos(th), rr * math.sin(th) - 0.04))
    d.polygon(px(pts, w, w, ss), fill=255)
    outer = to_alpha(img, w)
    inner_img, d2, _ = canvas(w)
    d2.polygon(px([(x * 0.78, y * 0.78 - 0.01) for x, y in pts], w, w, ss), fill=255)
    inner = to_alpha(inner_img, w)
    u, v = grid(w)
    shade = 0.55 + 0.45 * sstep(-0.6, 0.5, v + u * 0.3)
    rgb = inner * shade + (1 - inner) * 0.18
    save("star5", outer, rgb)


def hit_flash():
    """The classic anime hit spark: three nested jagged spike stars (white / colour / dim) plus needles."""
    w = 256
    rng = np.random.default_rng(77)
    n = 13
    angles = [k * 2 * math.pi / n + rng.uniform(-0.12, 0.12) for k in range(n)]
    lengths = [rng.uniform(0.62, 1.0) for _ in range(n)]
    valleys = [rng.uniform(0.22, 0.32) for _ in range(n)]

    def jag(scale, valley_scale):
        pts = []
        for k in range(n):
            a0, a1 = angles[k], angles[(k + 1) % n] + (2 * math.pi if k == n - 1 else 0)
            pts.append((lengths[k] * scale * math.cos(a0), lengths[k] * scale * math.sin(a0)))
            am = (a0 + a1) / 2
            pts.append((valleys[k] * valley_scale * math.cos(am), valleys[k] * valley_scale * math.sin(am)))
        return pts

    outer = poly_mask(w, w, [jag(0.97, 1.0)])
    mid = poly_mask(w, w, [jag(0.74, 0.85)])
    inner = poly_mask(w, w, [jag(0.48, 0.75)])
    needles = poly_mask(w, w, [rot(ray(1.0, 0.025, power=1.0), angles[k] + 0.5 * (angles[(k + 1) % n] - angles[k]))
                               for k in range(0, n, 3)])
    u, v = grid(w)
    r = np.sqrt(u * u + v * v)
    a = np.maximum.reduce([inner * CORE, mid * MID, outer * DIM, needles * MID]) * sstep(1.0, 0.96, r)
    save("hit_flash", a, inner * HOT + TINT * 0.4)


def ring():
    """Crisp ring: white line, colour sheath and a dim inner sheen."""
    u, v = grid(256)
    r = np.sqrt(u * u + v * v)
    r0 = 0.86
    d = np.abs(r - r0)
    a = np.maximum.reduce([sstep(0.028, 0.02, d) * CORE, sstep(0.055, 0.047, d) * MID,
                           (sstep(0.68, 0.72, r) * sstep(r0 + 0.01, r0, r)) * DIM])
    save("ring", a, sstep(0.024, 0.012, d) * HOT + TINT * 0.4)


def shockwave():
    """Anime shock ring: hard white front, broken colour body, radial speed-streak wake."""
    w = 512
    u, v = grid(w)
    r = np.sqrt(u * u + v * v)
    th = np.arctan2(v, u)
    wob = ang_noise(th, 9, 31) * 0.012
    rr = r + wob
    front = 0.9
    streak = 0.5 + 0.5 * ang_noise(th, 60, 32, 0.6)
    streak2 = 0.5 + 0.5 * ang_noise(th, 40, 33, 0.5)
    edge = sstep(front + 0.012, front, rr) * sstep(front - 0.05, front - 0.035, rr)
    body = sstep(front + 0.01, front, rr) * sstep(front - 0.13 - 0.06 * streak, front - 0.10 - 0.06 * streak, rr)
    wake = sstep(front, front - 0.01, rr) * sstep(front - 0.42 * streak2 - 0.06, front - 0.40 * streak2 - 0.04, rr)
    a = np.maximum.reduce([edge * CORE, body * MID, wake * DIM * (streak2 > 0.25)])
    save("shockwave", a * sstep(1.0, 0.97, r), edge * HOT + TINT * 0.4)


def sunburst():
    """Radiant wedge rays (holy / critical): white hub, long/short colour wedges, dim fill disc."""
    w = 512
    rng = np.random.default_rng(7)
    n = 24
    core_polys, ray_polys = [], []
    for i in range(n):
        th = i * 2 * math.pi / n + rng.uniform(-0.04, 0.04)
        long = i % 2 == 0
        L = rng.uniform(0.88, 1.0) if long else rng.uniform(0.5, 0.68)
        wd = (0.11 if long else 0.08)
        ray_polys.append(rot(ray(L, wd, power=1.15), th))
        core_polys.append(rot(ray(L * 0.7, wd * 0.42, power=1.4), th))
    rays_m = poly_mask(w, w, ray_polys)
    core_m = poly_mask(w, w, core_polys)
    u, v = grid(w)
    r = np.sqrt(u * u + v * v)
    hub = sstep(0.17, 0.15, r)
    a = np.maximum.reduce([np.maximum(hub, core_m * sstep(0.6, 0.3, r)) * CORE, rays_m * MID, sstep(0.42, 0.39, r) * DIM])
    save("sunburst", a, np.maximum(hub, core_m * sstep(0.5, 0.2, r)) * HOT + TINT * 0.4)


def speed_lines():
    """Radial anime focus lines with a hollow centre (anticipation / ultimate framing)."""
    w = 512
    rng = np.random.default_rng(91)
    polys, thin = [], []
    for i in range(54):
        th = rng.uniform(0, 2 * math.pi)
        r0 = rng.uniform(0.45, 0.75)
        wd = rng.uniform(0.012, 0.035)
        p = [(1.45, wd), (r0, 0.0), (1.45, -wd)]
        (polys if wd > 0.02 else thin).append(rot(p, th))
    m = poly_mask(w, w, polys)
    t = poly_mask(w, w, thin)
    u, v = grid(w)
    r = np.sqrt(u * u + v * v)
    fade = sstep(1.0, 0.92, np.maximum(np.abs(u), np.abs(v)))
    a = np.maximum(m * MID, t * DIM) * fade
    save("speed_lines", a, TINT * 0.6)


# ----------------------------------------------------------------------------- blades, trails, beams

def slash_arc():
    """Crescent slash billboard: white cutting edge, saturated body, streaky fading wake."""
    w, h = 512, 256
    u, v = grid(w, h)
    x, y = u, v * 0.5
    cx, cy, R = 0.0, -1.18, 1.55
    r = np.sqrt((x - cx) ** 2 + (y - cy) ** 2)
    ang = np.arctan2(x - cx, y - cy)
    span = 0.66
    s = np.clip((ang + span) / (2 * span), 0, 1)          # 0 trailing horn .. 1 leading horn
    taper = np.sin(np.pi * s ** 0.8) ** 0.9 * (s > 0) * (s < 1)
    d = R - r                                              # depth inside the outer edge
    n = tile_noise(128, 1.6, 41)
    streak = nsample(n, s * 90, d * 300)                   # streaks run along the swing
    edge = sstep(-0.006, 0.0, d) * sstep(0.06 * taper + 0.002, 0.05 * taper, d)
    body = sstep(-0.006, 0.0, d) * sstep(0.15 * taper + 0.003, 0.135 * taper, d)
    tail_depth = 0.33 * taper * (0.75 + 0.35 * streak)
    wake = sstep(-0.006, 0.0, d) * sstep(tail_depth + 0.004, tail_depth - 0.01, d)
    wake *= sstep(0.15, 0.3, streak + 0.35 * s)
    a = np.maximum.reduce([edge * CORE, body * MID, wake * DIM])
    save("slash_arc", a, edge * HOT * sstep(0.1, 0.4, s) + TINT * 0.5)


def slash_strip():
    """Mesh slash strip (arc mesh): U along the swing, V across (1 = outer cutting edge)."""
    w, h = 256, 128
    y, x = np.mgrid[0:h, 0:w].astype(np.float64)
    vv = 1 - (y + 0.5) / h
    uu = (x + 0.5) / w
    n = tile_noise(128, 1.5, 12)
    streak = nsample(n, uu * 40, vv * 260)
    edge = sstep(0.86, 0.89, vv) * sstep(0.995, 0.975, vv)
    body = sstep(0.70, 0.73, vv) * sstep(1.0, 0.99, vv)
    wake_edge = 0.62 - 0.38 * streak - 0.15 * (1 - uu)
    wake = sstep(wake_edge, wake_edge + 0.03, vv)
    wake *= sstep(0.0, 0.18, uu)
    a = np.maximum.reduce([edge * CORE, body * MID, wake * DIM])
    save("slash_strip", a, edge * HOT * sstep(0.05, 0.3, uu) + TINT * 0.5)


def slash_cross():
    """Two crossing crescent slashes with a glint at the crossing (critical / shadow strikes)."""
    w = 512
    u, v = grid(w)
    acc = np.zeros_like(u)
    heat = np.zeros_like(u)
    for sign, seed in ((1, 51), (-1, 52)):
        ca, sa = math.cos(sign * math.pi / 4), math.sin(sign * math.pi / 4)
        x = u * ca + v * sa
        y = -u * sa + v * ca
        cx, cy, R = 0.0, -1.55, 1.6
        r = np.sqrt((x - cx) ** 2 + (y - cy) ** 2)
        ang = np.arctan2(x - cx, y - cy)
        span = 0.62
        s = np.clip((ang + span) / (2 * span), 0, 1)
        taper = np.sin(np.pi * s) ** 0.9 * (s > 0) * (s < 1)
        d = R - r
        n = tile_noise(128, 1.6, seed)
        streak = nsample(n, s * 80, d * 260)
        edge = sstep(-0.006, 0.0, d) * sstep(0.05 * taper + 0.002, 0.04 * taper, d)
        body = sstep(-0.006, 0.0, d) * sstep(0.11 * taper + 0.003, 0.095 * taper, d)
        tail = 0.22 * taper * (0.7 + 0.4 * streak)
        wake = sstep(-0.006, 0.0, d) * sstep(tail + 0.004, tail - 0.01, d) * sstep(0.3, 0.5, streak + 0.3 * s)
        acc = np.maximum.reduce([acc, edge * CORE, body * MID, wake * DIM])
        heat = np.maximum(heat, edge)
    r = np.sqrt(u * u + (v - 0.05) ** 2)
    glint = sstep(0.07, 0.05, r)
    acc = np.maximum(acc, glint * CORE)
    save("slash_cross", acc, np.maximum(heat, glint) * HOT + TINT * 0.5)


def trail():
    """Ribbon profile for trails and the ring mesh (U along length, V across)."""
    w, h = 128, 64
    u, v = grid(w, h)
    av = np.abs(v)
    a = np.maximum.reduce([sstep(0.2, 0.15, av) * CORE, sstep(0.45, 0.4, av) * MID, sstep(0.78, 0.7, av) * DIM])
    save("trail", a, sstep(0.18, 0.1, av) * HOT + TINT * 0.5)


def beam():
    """Light pillar: thin white core, slim colour sheath, streaked dim aura; the top dissolves into
    vertical light threads, the base flares into a small foot glow."""
    w, h = 256, 512
    u, v = grid(w, h)
    au = np.abs(u)
    n = tile_noise(256, 2.0, 5)
    streak = nsample(n, u * 40 + 7, v * 6)             # long vertical threads
    base = sstep(-1.0, -0.94, v)
    flare = sstep(1.0, 0.8, np.sqrt((u / 0.55) ** 2 + ((v + 0.93) / 0.07) ** 2))
    core = sstep(0.075, 0.06, au) * base * sstep(0.75, 0.55, v + 0.25 * streak)
    sheath = sstep(0.17, 0.155, au) * base * sstep(0.95, 0.7, v + 0.45 * (streak - 0.5) + 0.1)
    aura = sstep(0.36, 0.34, au) * base * sstep(0.7, 0.45, v + 0.6 * (streak - 0.5)) * sstep(0.32, 0.38, streak)
    a = np.maximum.reduce([core * CORE, sheath * MID, aura * DIM, flare * MID])
    save("beam", a, np.maximum(core, flare * sstep(0.6, 0.0, au)) * HOT + TINT * 0.4)


def arrow_streak():
    """Light arrow pointing +U: white head and shaft, three speed lines trailing back."""
    w, h = 256, 64
    head = [(0.98, 0.0), (0.62, 0.42), (0.70, 0.0), (0.62, -0.42)]
    shaft = [(0.70, 0.06), (-0.95, 0.015), (-0.95, -0.015), (0.70, -0.06)]
    lines = [[(0.55, o + 0.04), (-0.98, o), (0.55, o - 0.04)] for o in (0.42, -0.42)]
    hm = poly_mask(w, h, [head])
    sm = poly_mask(w, h, [shaft])
    lm = poly_mask(w, h, lines)
    u, v = grid(w, h)
    sheath = poly_mask(w, h, [[(1.0, 0.0), (0.58, 0.62), (0.3, 0.2), (-0.98, 0.04), (-0.98, -0.04), (0.3, -0.2), (0.58, -0.62)]])
    a = np.maximum.reduce([hm * CORE, sm * CORE * sstep(-0.9, 0.2, u), lm * DIM, sheath * MID * sstep(-0.95, 0.3, u)])
    save("arrow_streak", a, np.maximum(hm, sm * sstep(-0.2, 0.5, u)) * HOT + TINT * 0.4)


def arrow_rain():
    """Falling light arrow for `upright` particles (square canvas because particles are square):
    points DOWN, white head and shaft, colour fletching sheath, dim streak above."""
    w = 256
    head = [(0.0, -0.98), (0.17, -0.62), (0.0, -0.7), (-0.17, -0.62)]
    shaft = [(-0.035, -0.7), (0.035, -0.7), (0.02, 0.55), (-0.02, 0.55)]
    fletch = [(0.0, 0.3), (0.14, 0.62), (0.0, 0.52), (-0.14, 0.62)]
    sheath = [(0.0, -1.0), (0.26, -0.58), (0.07, -0.5), (0.05, 0.95), (-0.05, 0.95), (-0.07, -0.5), (-0.26, -0.58)]
    core = poly_mask(w, w, [head, shaft])
    fl = poly_mask(w, w, [fletch])
    sh = poly_mask(w, w, [sheath])
    u, v = grid(w)
    a = np.maximum.reduce([core * CORE, fl * MID, sh * MID * sstep(1.0, 0.2, v), halo(sh, 3, DIM, 0.5) * sstep(1.0, 0.0, v)])
    save("arrow_rain", a, core * HOT * sstep(0.7, -0.2, v) + TINT * 0.4)


def light_streak():
    """Vertical falling light drop for `upright` rain particles: white bead at the bottom, tapering tail."""
    w = 128
    u, v = grid(w)
    t = np.clip((v + 0.75) / 1.7, 0, 1)               # 0 at the bead .. 1 at the tail end
    width = 0.13 * (1 - t) ** 0.9
    bead = sstep(0.13, 0.1, np.sqrt(u * u + (v + 0.75) ** 2))
    tail = sstep(width + 0.01, width, np.abs(u)) * (v > -0.75)
    sheath = sstep(width * 1.8 + 0.03, width * 1.8 + 0.02, np.abs(u)) * (v > -0.92) * sstep(0.95, 0.7, v)
    a = np.maximum.reduce([np.maximum(bead, tail * sstep(0.2, -0.3, v)) * CORE, tail * MID, sheath * DIM,
                           sstep(0.22, 0.2, np.sqrt(u * u + (v + 0.75) ** 2)) * MID])
    save("light_streak", a, bead * HOT + TINT * 0.4)


def claw():
    w = 256
    core_polys, body_polys = [], []
    for i, off in enumerate((-0.42, 0.0, 0.42)):
        for poly_list, scale in ((body_polys, 1.0), (core_polys, 0.42)):
            L, R = [], []
            n = 40
            for k in range(n + 1):
                t = k / n
                y = 0.88 - 1.76 * t
                x = off + 0.28 * math.sin(t * math.pi * 0.9) - 0.12 + 0.24 * t
                wdt = 0.11 * math.sin(t * math.pi) ** 0.8 * (1.15 if i == 1 else 0.9) * scale
                L.append((x - wdt, y))
                R.append((x + wdt * 0.45, y))
            poly_list.append(L + R[::-1])
    body = poly_mask(w, w, body_polys)
    core = poly_mask(w, w, core_polys)
    a = np.maximum.reduce([core * CORE, body * MID, halo(body, 3, DIM, 0.6)])
    save("claw", a, core * HOT + TINT * 0.4)


def bite():
    """Fang arc: crescent with triangular teeth (two mirrored particles make a bite)."""
    w, h = 256, 128
    img, d, ss = canvas(w, h)
    outer, inner = [], []
    n = 48
    for k in range(n + 1):
        t = k / n
        x = -0.95 + 1.9 * t
        y_out = 0.55 - 0.9 * (x ** 2) * 0.55
        outer.append((x, y_out + 0.2))
        inner.append((x, y_out - 0.15 * math.sin(t * math.pi) ** 0.5))
    d.polygon(px(outer + inner[::-1], w, h, ss), fill=255)
    timg, td, _ = canvas(w, h)
    for k in range(6):
        t = (k + 0.5) / 6
        x = -0.8 + 1.6 * t
        y = 0.55 - 0.9 * (x ** 2) * 0.55 - 0.1
        L = 0.55 if k in (0, 5) else 0.38
        td.polygon(px([(x - 0.09, y + 0.05), (x + 0.09, y + 0.05), (x, y - L)], w, h, ss), fill=255)
    gum = to_alpha(img, w, h)
    teeth = to_alpha(timg, w, h)
    a = np.maximum.reduce([teeth * CORE, gum * MID, halo(np.maximum(gum, teeth), 3, DIM, 0.6)])
    save("bite", a, teeth * HOT + TINT * 0.4)


# ----------------------------------------------------------------------------- flipbooks & noise

def noise():
    n = tile_noise(256, 2.0, 3)
    n2 = tile_noise(256, 1.4, 4)
    m = np.clip(n * 0.7 + n2 * 0.3, 0, 1)
    m = (m - m.min()) / (m.max() - m.min())
    save("noise", np.ones_like(m), m)


def cell_noise():
    """Tileable soft voronoi cells (energy/caustics)."""
    n = 256
    rng = np.random.default_rng(21)
    pts = rng.uniform(0, n, (40, 2))
    y, x = np.mgrid[0:n, 0:n].astype(np.float64)
    d1 = np.full((n, n), 1e9)
    d2 = np.full((n, n), 1e9)
    for px_, py_ in pts:
        for ox in (-n, 0, n):
            for oy in (-n, 0, n):
                dd = np.sqrt((x - px_ - ox) ** 2 + (y - py_ - oy) ** 2)
                d2 = np.where(dd < d1, d1, np.minimum(d2, dd))
                d1 = np.minimum(d1, dd)
    edge = 1 - np.clip((d2 - d1) / 10, 0, 1)
    save("cells", np.ones_like(edge), edge)


def atlas(cell, N, frame_fn):
    A = np.zeros((cell * N, cell * N))
    C = np.zeros((cell * N, cell * N))
    for i in range(N * N):
        a, c = frame_fn(i, i / (N * N - 1))
        r0, c0 = (i // N) * cell, (i % N) * cell
        A[r0:r0 + cell, c0:c0 + cell] = a
        C[r0:r0 + cell, c0:c0 + cell] = c
    return A, C


def smoke_sheet():
    """4x4 life cycle of a cel smoke puff (alpha blended): bloom out, billow, tear apart.
    RGB is a two-tone split: each visible ball is lit from the upper left with a crisp shadow crescent."""
    cell, N = 128, 4
    rng = np.random.default_rng(100)
    balls = np.array([(rng.uniform(-0.42, 0.42), rng.uniform(-0.32, 0.32), rng.uniform(0.2, 0.3)) for _ in range(13)])
    balls[:, :2] -= balls[:, :2].mean(axis=0)
    nz = tile_noise(128, 2.2, 9)
    u, v = grid(cell)
    light = np.array([-0.55, 0.6, 0.58])

    def frame(i, t):
        grow = 0.45 + 0.55 * (1 - (1 - min(1, t * 1.8)) ** 2.5)
        hf = np.full_like(u, -1.0)
        lit = np.zeros_like(u, dtype=bool)
        for bx, by, br in balls:
            cx, cy = bx * (0.8 + 0.45 * t), by * (0.8 + 0.45 * t) + 0.1 * t
            rr = br * grow
            d2 = (u - cx) ** 2 + (v - cy) ** 2
            hgt = np.sqrt(np.clip(rr * rr - d2, 0, None))
            hgt = np.where(d2 < rr * rr, hgt + bx * -0.3 + by * 0.3, -1)   # larger balls sit in front
            top = hgt > hf
            nrm = ((u - cx) / rr) * light[0] + ((v - cy) / rr) * light[1] + np.sqrt(np.clip(1 - d2 / (rr * rr), 0, 1)) * light[2]
            lit = np.where(top, nrm > 0.32, lit)
            hf = np.maximum(hf, hgt)
        inside = sstep(-0.01, 0.01, hf)
        n = nsample(nz, (u + 1) * 32 + i * 5.3, (v + 1) * 32 - i * 3.1)
        dissolve = sstep(0.0, 0.06, n - (max(0.0, t - 0.5) / 0.5) * 0.85)
        a = inside * dissolve
        a = np.maximum(a * CORE, halo(a, 1.4, MID, 0.9) * (t < 0.8))
        shade = np.where(lit, 0.9, 0.42)
        a *= sstep(0.99, 0.93, np.maximum(np.abs(u), np.abs(v)))
        return a, shade

    A, C = atlas(cell, N, frame)
    save("smoke_sheet", A, C)


def flame_sheet():
    """4x4 fire burst life cycle (1024): ignition bulb -> five licking tongues -> detached wisps.
    Smooth low-frequency contours so the cel bands read as clean anime flame shapes; white heat
    only in the root of the main tongues. Frames read top-left to bottom-right."""
    cell, N = 256, 4
    smooth = tile_noise(256, 2.8, 13)
    u, v = grid(cell)
    rng = np.random.default_rng(15)
    tongues = [(0.0, 1.0, 0.42, 0.0), (-0.3, 0.7, 0.3, 1.3), (0.3, 0.78, 0.3, 2.1), (-0.52, 0.42, 0.2, 3.3),
               (0.52, 0.48, 0.2, 4.4)]

    def frame(i, t):
        rise = 1 - (1 - min(1.0, t / 0.28)) ** 2
        die = sstep(0.5, 1.0, t)
        base = -0.82
        F = np.full_like(u, -1.0)
        root = np.zeros_like(u)
        n = nsample(smooth, (u + 1) * 22 + 40, (v + 1) * 22 - t * 70)
        for x0, hk, wk, ph in tongues:
            H = (0.35 + 1.25 * hk * rise) * (1 - 0.35 * die)
            yb = base + die * 0.55 * hk                  # the tongue lifts off its root as it dies
            y = (v - yb) / H
            sway = 0.16 * math.sin(t * 9 + ph) * np.clip(y, 0, 1) ** 1.5 + (n - 0.5) * 0.35 * np.clip(y, 0, 1)
            x = u - x0 * (0.6 + 0.4 * rise) - sway
            W = wk * (0.75 + 0.35 * rise) * np.clip(1 - y, 0, 1) ** 1.35 * sstep(-0.02, 0.22, y)
            W += wk * 0.55 * sstep(0.25, 0.0, y) * sstep(-0.18, 0.02, y) * (1 - die)
            f = 1 - np.abs(x) / np.maximum(W, 1e-4)
            f = np.where(W > 1e-4, f, -1)
            F = np.maximum(F, f)
            root = np.maximum(root, f * sstep(0.62, 0.25, y) * (hk > 0.6))
        # wisps that tear off the tips late in the life
        for k in range(4):
            wx = rng.uniform(-0.4, 0.4)
            ty = -0.1 + 1.6 * die + k * 0.18 - 0.2
            wr = 0.12 * (1 - die) + 0.03
            d = np.sqrt(((u - wx - 0.1 * math.sin(t * 7 + k)) / wr) ** 2 + ((v - ty) / (wr * 2.2)) ** 2)
            F = np.maximum(F, (1 - d) * (die > 0.05) * 0.9)
        F -= die * 0.35 * n
        core = sstep(0.5, 0.55, root - 0.25 * die)
        mid = sstep(0.3, 0.35, F)
        dim = sstep(0.0, 0.05, F)
        a = np.maximum.reduce([core * CORE, mid * MID, dim * DIM])
        a *= sstep(1.0, 0.95, np.maximum(np.abs(u), np.abs(v)))
        return a, core * HOT + TINT * 0.4

    A, C = atlas(cell, N, frame)
    save("flame_sheet", A, C)


def explosion_sheet():
    """4x4 anime explosion (1024): spike flash, billowing cauliflower fireball with a white heart,
    then a burnt-out ring that tears into fragments."""
    cell, N = 256, 4
    nz = tile_noise(256, 2.6, 61)
    u, v = grid(cell)
    r = np.sqrt(u * u + v * v)
    th = np.arctan2(v, u)
    lobes = 0.5 + 0.5 * np.cos(th * 9 + ang_noise(th, 3, 62) * 1.2)
    bumps = lobes ** 2 * 0.6 + 0.4 * (0.5 + 0.5 * ang_noise(th, 6, 63, 0.7))

    def frame(i, t):
        if i == 0:
            spikes = 0.5 + 0.5 * ang_noise(th, 11, 64, 0.2)
            s = 0.2 + 0.32 * spikes ** 3
            a = np.maximum.reduce([sstep(s * 0.6 + 0.01, s * 0.6, r) * CORE, sstep(s + 0.01, s, r) * MID, sstep(s * 1.45, s * 1.4, r) * DIM])
            return a, sstep(s * 0.6, s * 0.4, r) * HOT
        R = 0.3 + 0.62 * (1 - (1 - t) ** 2.4)
        n = nsample(nz, (u + 1) * 26 + i * 4, (v + 1) * 26 - i * 3)
        rr = r / R - 0.13 * bumps - 0.14 * (n - 0.5)
        hollow = sstep(0.3, 1.0, t) * 0.75
        tear = sstep(0.55, 1.0, t) * 0.7
        holes = sstep(0.0, 0.04, n - tear)
        ring_r = 0.78 - 0.08 * bumps
        body = sstep(1.0, 0.98, rr) * sstep(hollow - 0.02, hollow, rr) * holes
        mid = sstep(ring_r, ring_r - 0.02, rr) * sstep(hollow + 0.06, hollow + 0.08, rr) * holes
        core_r = max(0.0, 0.6 - 0.95 * t)
        core = sstep(core_r, core_r - 0.03, rr + 0.1 * bumps) if core_r > 0.02 else np.zeros_like(r)
        a = np.maximum.reduce([core * CORE, mid * MID, body * DIM])
        a = np.maximum(a, mid * CORE * (t < 0.3))
        a *= sstep(1.0, 0.95, np.maximum(np.abs(u), np.abs(v)))
        return a, np.maximum(core, mid * (t < 0.3)) * HOT + TINT * 0.4

    A, C = atlas(cell, N, frame)
    save("explosion_sheet", A, C)


def lightning_sheet():
    """4x4 grid (1024) of full-height forked bolts, each with a white trunk, colour sheath and branch
    forks. Played on a stretched quad the frames flicker between different strikes."""
    cell, N = 256, 4
    A = np.zeros((cell * N, cell * N))
    C = np.zeros((cell * N, cell * N))
    ss = 3
    for i in range(N * N):
        rng = np.random.default_rng(300 + i)
        W = cell * ss
        trunk_img = Image.new("L", (W, W), 0)
        sheath_img = Image.new("L", (W, W), 0)
        dt = ImageDraw.Draw(trunk_img)
        ds = ImageDraw.Draw(sheath_img)

        def bolt(x0, y0, x1, y1, disp, depth, width, branch):
            pts = [(x0, y0), (x1, y1)]
            for _ in range(depth):
                new = [pts[0]]
                for (ax, ay), (bx, by) in zip(pts, pts[1:]):
                    mx, my = (ax + bx) / 2 + rng.uniform(-disp, disp), (ay + by) / 2 + rng.uniform(-disp, disp) * 0.25
                    new += [(mx, my), (bx, by)]
                pts = new
                disp *= 0.56
            n = len(pts)
            for k in range(n - 1):
                taper = 1 - 0.65 * k / n
                ds.line([pts[k], pts[k + 1]], fill=255, width=max(1, int(width * 2.6 * taper)))
                dt.line([pts[k], pts[k + 1]], fill=255, width=max(1, int(width * taper)))
            return pts

        x_top = W / 2 + rng.uniform(-0.15, 0.15) * W
        x_bot = W / 2 + rng.uniform(-0.25, 0.25) * W
        main = bolt(x_top, 0, x_bot, W, W * 0.16, 7, 6.5 * ss, True)
        for _ in range(rng.integers(2, 5)):
            i0 = rng.integers(len(main) // 8, len(main) * 3 // 4)
            sx, sy = main[i0]
            ex = sx + rng.choice([-1, 1]) * rng.uniform(0.15, 0.4) * W
            ey = sy + rng.uniform(0.15, 0.35) * W
            bolt(sx, sy, ex, min(ey, W), W * 0.06, 5, 2.8 * ss, False)
        trunk = np.asarray(trunk_img.resize((cell, cell), Image.LANCZOS), dtype=np.float64) / 255
        sheath = np.asarray(sheath_img.resize((cell, cell), Image.LANCZOS), dtype=np.float64) / 255
        y = np.linspace(0, 1, cell)[:, None]
        fade = sstep(0.0, 0.03, y) * sstep(1.0, 0.95, y)
        a = np.maximum.reduce([trunk * CORE, sheath * MID, halo(sheath, 3.0, DIM, 0.5)]) * fade
        r0, c0 = (i // N) * cell, (i % N) * cell
        A[r0:r0 + cell, c0:c0 + cell] = a
        C[r0:r0 + cell, c0:c0 + cell] = trunk * HOT + TINT * 0.5
    save("lightning_sheet", A, C)


# ----------------------------------------------------------------------------- magic circles

def rune_glyphs(count, seed):
    """Pseudo-script glyphs on a 2x3 stroke grid: lines, hooks, small arcs, rings and dots."""
    rng = np.random.default_rng(seed)
    gl = []
    nodes = [(gx, gy) for gx in (-0.5, 0.0, 0.5) for gy in (-0.75, 0.0, 0.75)]
    for _ in range(count):
        strokes = [("line", (0.0, -0.8), (0.0, 0.8))] if rng.random() < 0.55 else []
        for _ in range(rng.integers(2, 4)):
            kind = rng.choice(["line", "line", "arc", "ring", "dot"], p=[0.3, 0.3, 0.2, 0.1, 0.1])
            if kind == "line":
                a, b = rng.choice(len(nodes), 2, replace=False)
                strokes.append(("line", nodes[a], nodes[b]))
            elif kind == "arc":
                c = nodes[rng.integers(len(nodes))]
                strokes.append(("arc", c, float(rng.uniform(0.3, 0.5)), int(rng.integers(0, 4)) * 90))
            elif kind == "ring":
                strokes.append(("ring", nodes[rng.integers(len(nodes))], 0.22))
            else:
                strokes.append(("dot", nodes[rng.integers(len(nodes))]))
        gl.append(strokes)
    return gl


def draw_runes(d, w, ss, radius, count, size, width, seed):
    glyphs = rune_glyphs(count, seed)
    for i, g in enumerate(glyphs):
        th = math.pi / 2 - i * 2 * math.pi / count
        cx, cy = radius * math.cos(th), radius * math.sin(th)
        ang = th - math.pi / 2
        for s in g:
            if s[0] == "line":
                p = rot([(s[1][0] * size, s[1][1] * size), (s[2][0] * size, s[2][1] * size)], ang, cx, cy)
                d.line(px(p, w, w, ss), fill=255, width=max(1, int(width * ss)))
            elif s[0] == "arc":
                (gx, gy), rr, start = s[1], s[2] * size, s[3]
                pts = [(gx * size + rr * math.cos(math.radians(start + k * 15)), gy * size + rr * math.sin(math.radians(start + k * 15)))
                       for k in range(13)]
                d.line(px(rot(pts, ang, cx, cy), w, w, ss), fill=255, width=max(1, int(width * ss)), joint="curve")
            elif s[0] == "ring":
                p = rot([(s[1][0] * size, s[1][1] * size)], ang, cx, cy)[0]
                disc(d, w, w, ss, p[0], p[1], s[2] * size, outline=255, width=width * 0.8)
            else:
                p = rot([(s[1][0] * size, s[1][1] * size)], ang, cx, cy)[0]
                disc(d, w, w, ss, p[0], p[1], width * 1.3 / w * 2 * 1.0)


def circle_line(d, w, ss, r, width):
    c = w * ss / 2
    rr = r * w * ss / 2
    d.ellipse([c - rr, c - rr, c + rr, c + rr], outline=255, width=max(1, int(width * ss)))


def poly_line(d, w, ss, pts, width):
    d.line(px(pts + pts[:1], w, w, ss), fill=255, width=int(width * ss), joint="curve")


def ngon(n, r, phase=math.pi / 2):
    return [(r * math.cos(phase + i * 2 * math.pi / n), r * math.sin(phase + i * 2 * math.pi / n)) for i in range(n)]


def star_polygon(n, step, r, phase=math.pi / 2):
    pts = ngon(n, r, phase)
    return [pts[(k * step) % n] for k in range(n)]


def ticks(d, w, ss, r0, r1, count, width, major_every=0, major_r=None):
    for i in range(count):
        th = i * 2 * math.pi / count
        a, b = (r0, r1) if not (major_every and i % major_every == 0) else major_r
        d.line(px([(a * math.cos(th), a * math.sin(th)), (b * math.cos(th), b * math.sin(th))], w, w, ss),
               fill=255, width=max(1, int(width * ss)))


def finish_circle(name, lines_img, w, bands=(), hot_r=None):
    """Lines become the MID colour band, a DIM halo hugs them, `bands` are (r0, r1) annuli filled DIM.
    `hot_r` (r0, r1) annulus lines burn white."""
    lines = to_alpha(lines_img, w)
    u, v = grid(w)
    r = np.sqrt(u * u + v * v)
    fill = np.zeros_like(r)
    for r0, r1 in bands:
        fill = np.maximum(fill, sstep(r0 - 0.004, r0, r) * sstep(r1 + 0.004, r1, r))
    thick = sstep(0.35, 0.6, gauss_blur(lines, 1.2))
    a = np.maximum.reduce([lines * MID, thick * CORE, halo(lines, 2.2, DIM, 0.45), fill * DIM])
    heat = thick * HOT
    if hot_r:
        heat = np.maximum(heat, lines * sstep(hot_r[0] - 0.01, hot_r[0], r) * sstep(hot_r[1] + 0.01, hot_r[1], r))
    save(name, a * sstep(1.0, 0.985, r), heat * 0.9 + TINT * 0.5)


def magic_circle_a():
    """Classic hexagram circle: double rim, rune band, interlocking triangles, vertex orbs."""
    w = 512
    img, d, ss = canvas(w)
    circle_line(d, w, ss, 0.975, 5)
    circle_line(d, w, ss, 0.94, 1.5)
    ticks(d, w, ss, 0.94, 0.975, 96, 1.2)
    circle_line(d, w, ss, 0.86, 1.5)
    draw_runes(d, w, ss, 0.80, 28, 0.032, 1.8, 1)
    circle_line(d, w, ss, 0.74, 3)
    circle_line(d, w, ss, 0.71, 1.2)
    poly_line(d, w, ss, ngon(3, 0.71), 3)
    poly_line(d, w, ss, ngon(3, 0.71, -math.pi / 2), 3)
    poly_line(d, w, ss, ngon(6, 0.41, 0), 1.5)
    circle_line(d, w, ss, 0.36, 2.5)
    draw_runes(d, w, ss, 0.29, 10, 0.026, 1.6, 11)
    circle_line(d, w, ss, 0.21, 2)
    poly_line(d, w, ss, star_polygon(8, 3, 0.2, 0), 1.5)
    circle_line(d, w, ss, 0.07, 3)
    for p in ngon(6, 0.71, math.pi / 2):
        disc(d, w, w, ss, p[0], p[1], 0.05, outline=255, width=2.5)
        disc(d, w, w, ss, p[0], p[1], 0.018)
    finish_circle("magic_circle_a", img, w, bands=[(0.86, 0.94)], hot_r=(0.96, 0.99))


def magic_circle_b():
    """Support seal: graduated rim, two crossed squares, inner rune ring and octagon flower."""
    w = 512
    img, d, ss = canvas(w)
    circle_line(d, w, ss, 0.975, 4)
    circle_line(d, w, ss, 0.88, 2)
    ticks(d, w, ss, 0.88, 0.95, 72, 1.6, 6, (0.80, 0.975))
    poly_line(d, w, ss, ngon(4, 0.80, math.pi / 4), 3)
    poly_line(d, w, ss, ngon(4, 0.80, 0), 3)
    circle_line(d, w, ss, 0.57, 3)
    circle_line(d, w, ss, 0.53, 1.2)
    draw_runes(d, w, ss, 0.45, 14, 0.034, 1.8, 2)
    circle_line(d, w, ss, 0.36, 2.5)
    for k in range(8):
        th = k * math.pi / 4
        c = (0.2 * math.cos(th), 0.2 * math.sin(th))
        disc(d, w, w, ss, c[0], c[1], 0.12, outline=255, width=1.6)
    circle_line(d, w, ss, 0.08, 3)
    finish_circle("magic_circle_b", img, w, bands=[(0.53, 0.57)], hot_r=(0.96, 0.99))


def magic_circle_c():
    """Thin double rune band only (counter-rotating overlay layer)."""
    w = 512
    img, d, ss = canvas(w)
    circle_line(d, w, ss, 0.985, 3)
    circle_line(d, w, ss, 0.955, 1.2)
    draw_runes(d, w, ss, 0.895, 36, 0.026, 1.7, 3)
    circle_line(d, w, ss, 0.835, 1.2)
    circle_line(d, w, ss, 0.81, 2.5)
    ticks(d, w, ss, 0.74, 0.79, 48, 1.2, 4, (0.70, 0.79))
    finish_circle("magic_circle_c", img, w, bands=[(0.955, 0.985)])


def magic_circle_d():
    """Jagged abyss/summoning sigil: saw rim, pentagram, eye-like core."""
    w = 512
    img, d, ss = canvas(w)
    circle_line(d, w, ss, 0.97, 5)
    pts = []
    for i in range(40):
        th = math.pi / 2 + i * 2 * math.pi / 40
        rr = 0.93 if i % 2 == 0 else 0.80
        pts.append((rr * math.cos(th), rr * math.sin(th)))
    poly_line(d, w, ss, pts, 2.5)
    circle_line(d, w, ss, 0.76, 3)
    poly_line(d, w, ss, star_polygon(5, 2, 0.76), 3.2)
    draw_runes(d, w, ss, 0.63, 18, 0.034, 2.0, 4)
    circle_line(d, w, ss, 0.5, 3)
    for i in range(5):
        th = math.pi / 2 + i * 2 * math.pi / 5 + math.pi / 5
        c = (0.34 * math.cos(th), 0.34 * math.sin(th))
        disc(d, w, w, ss, c[0], c[1], 0.07, outline=255, width=3)
        disc(d, w, w, ss, c[0], c[1], 0.022)
    eye = [(-0.2, 0.0)] + [(x, 0.11 * (1 - (x / 0.2) ** 2)) for x in np.linspace(-0.2, 0.2, 15)] + \
          [(x, -0.11 * (1 - (x / 0.2) ** 2)) for x in np.linspace(0.2, -0.2, 15)]
    d.line(px(eye, w, w, ss), fill=255, width=3 * ss, joint="curve")
    disc(d, w, w, ss, 0, 0, 0.05)
    finish_circle("magic_circle_d", img, w, bands=[(0.76, 0.80)], hot_r=(0.95, 0.99))


def magic_circle_e():
    """Grand arcane seal (archmage): triple rune bands, heptagram, orbiting sub-circles, inner star."""
    w = 512
    img, d, ss = canvas(w)
    circle_line(d, w, ss, 0.98, 4)
    draw_runes(d, w, ss, 0.935, 44, 0.02, 1.4, 21)
    circle_line(d, w, ss, 0.89, 2)
    ticks(d, w, ss, 0.84, 0.89, 120, 1.0, 10, (0.80, 0.89))
    circle_line(d, w, ss, 0.80, 2.5)
    poly_line(d, w, ss, star_polygon(7, 3, 0.80), 2.4)
    poly_line(d, w, ss, star_polygon(7, 2, 0.80), 1.4)
    for p in ngon(7, 0.80):
        disc(d, w, w, ss, p[0], p[1], 0.075, outline=255, width=2.2)
        disc(d, w, w, ss, p[0], p[1], 0.045, outline=255, width=1.2)
        disc(d, w, w, ss, p[0], p[1], 0.014)
    circle_line(d, w, ss, 0.47, 2.5)
    draw_runes(d, w, ss, 0.42, 16, 0.026, 1.5, 22)
    circle_line(d, w, ss, 0.37, 1.5)
    poly_line(d, w, ss, star_polygon(6, 1, 0.33, 0), 1.6)
    poly_line(d, w, ss, star_polygon(12, 5, 0.33, 0), 1.2)
    circle_line(d, w, ss, 0.14, 3)
    poly_line(d, w, ss, ngon(4, 0.14, math.pi / 2), 2)
    finish_circle("magic_circle_e", img, w, bands=[(0.89, 0.98), (0.37, 0.47)], hot_r=(0.79, 0.82))


def magic_circle_f():
    """Holy sun seal: twelve-ray star, cross at the centre, laurel ticks and a script band."""
    w = 512
    img, d, ss = canvas(w)
    circle_line(d, w, ss, 0.975, 3)
    circle_line(d, w, ss, 0.945, 1.2)
    for i in range(48):
        th = i * 2 * math.pi / 48
        leaf = rot(lens(0.06, 0.016), th + math.pi / 2 * 0.6, 0.96 * math.cos(th), 0.96 * math.sin(th))
        d.polygon(px(leaf, w, w, ss), fill=255)
    circle_line(d, w, ss, 0.86, 2)
    draw_runes(d, w, ss, 0.80, 24, 0.03, 1.7, 31)
    circle_line(d, w, ss, 0.74, 3)
    sun = []
    for i in range(24):
        th = math.pi / 2 + i * 2 * math.pi / 24
        rr = 0.72 if i % 2 == 0 else 0.42
        sun.append((rr * math.cos(th), rr * math.sin(th)))
    poly_line(d, w, ss, sun, 2.2)
    circle_line(d, w, ss, 0.36, 2.5)
    cross = [(-0.05, 0.3), (0.05, 0.3), (0.05, 0.08), (0.2, 0.08), (0.2, -0.02), (0.05, -0.02), (0.05, -0.3),
             (-0.05, -0.3), (-0.05, -0.02), (-0.2, -0.02), (-0.2, 0.08), (-0.05, 0.08)]
    d.polygon(px(cross, w, w, ss), outline=255, fill=0)
    d.line(px(cross + cross[:1], w, w, ss), fill=255, width=int(2.5 * ss))
    circle_line(d, w, ss, 0.13, 1.5)
    finish_circle("magic_circle_f", img, w, bands=[(0.86, 0.945)], hot_r=(0.0, 0.33))


def hex_grid():
    """Hex lattice for the barrier sphere. The sphere maps U around (2*pi) and V pole to pole (pi), so the
    lattice is built in isotropic units (X spans 2, Y spans 1) and wraps seamlessly in U."""
    w, h = 256, 256
    y, x = np.mgrid[0:h, 0:w].astype(np.float64)
    X, Y = (x + 0.5) / w * 2.0, (y + 0.5) / h
    s = 2.0 / 10                                  # 10 cells around the equator
    best = np.full((h, w), 1e9)
    for j in range(-1, int(1 / (s * 0.866)) + 3):
        for i in range(-1, 16):
            cx, cy = i * s + (s / 2 if j % 2 else 0.0), j * s * 0.866
            for ox in (-2.0, 0.0, 2.0):
                dx, dy = np.abs(X - cx - ox), np.abs(Y - cy)
                best = np.minimum(best, np.maximum(dx, dx * 0.5 + dy * 0.866))
    m = best / (s / 2)                            # 0 at the cell centre, 1 on the border
    edge = sstep(0.9, 0.93, m)
    rim = sstep(0.82, 0.85, m)
    a = np.maximum.reduce([edge * CORE, rim * MID, sstep(0.66, 0.7, m) * DIM])
    save("hex", a, edge * HOT * 0.85 + TINT * 0.4)


def swirl():
    """Abyss vortex: five tapering spiral arms, white inner rim, hollow eye."""
    w = 512
    u, v = grid(w)
    r = np.sqrt(u * u + v * v) + 1e-6
    th = np.arctan2(v, u)
    arms = 5
    phase = th * arms + np.log(r) * 7.5
    s = 0.5 + 0.5 * np.cos(phase)
    width_k = sstep(1.0, 0.25, r)                            # arms thin out toward the rim
    arm_core = sstep(0.93 - 0.18 * width_k, 0.95 - 0.18 * width_k, s)
    arm_body = sstep(0.75 - 0.35 * width_k, 0.78 - 0.35 * width_k, s)
    arm_dim = sstep(0.45 - 0.35 * width_k, 0.5 - 0.35 * width_k, s)
    radial = sstep(0.98, 0.8, r) * sstep(0.08, 0.14, r)
    eye_rim = sstep(0.17, 0.15, r) * sstep(0.1, 0.12, r)
    a = np.maximum.reduce([arm_core * radial * sstep(0.7, 0.45, r), arm_body * radial * MID, arm_dim * radial * DIM,
                           eye_rim * CORE, sstep(0.3, 0.27, r) * sstep(0.12, 0.14, r) * DIM])
    save("swirl", a, np.maximum(eye_rim, arm_core * sstep(0.45, 0.2, r)) * HOT + TINT * 0.4)


# ----------------------------------------------------------------------------- nature / shards

def leaf():
    """Two-tone leaf (lit left half, shadow right half, ink vein)."""
    w = 128
    pts = []
    for k in range(41):
        t = k / 40
        y = -0.85 + 1.75 * t
        x = 0.44 * math.sin(math.pi * t) ** 0.85 * (1 - 0.25 * t)
        pts.append((x, y))
    body = poly_mask(w, w, [pts + [(-x, y) for x, y in pts[::-1]]])
    stem = poly_mask(w, w, [[(0, -0.97), (0, 0.85)]], width=2.2)
    vimg, vd, ss = canvas(w)
    for k in range(5):
        y0 = -0.5 + k * 0.28
        vd.line(px([(0, y0), (0.24, y0 + 0.2)], w, w, ss), fill=255, width=int(1.4 * ss))
        vd.line(px([(0, y0), (-0.24, y0 + 0.2)], w, w, ss), fill=255, width=int(1.4 * ss))
    veins = to_alpha(vimg, w) * body
    u, v = grid(w)
    shade = np.where(u < 0.02, 0.72, 0.44)
    shade = np.where(veins > 0.4, 0.4, shade)
    a = np.maximum(body, stem * (np.abs(u) < 0.05))
    save("leaf", a, np.where(stem > 0.5, 0.35, shade))


def petal():
    """Sakura petal with a notched tip, lit/shadow split."""
    w = 64
    pts = []
    for k in range(41):
        t = k / 40
        y = -0.9 + 1.75 * t
        x = 0.62 * math.sin(math.pi * min(1, t * 1.05)) ** 0.7 * (1 - 0.15 * t)
        pts.append((x, y))
    outline = pts + [(-x, y) for x, y in pts[::-1]]
    body = poly_mask(w, w, [outline])
    notch = poly_mask(w, w, [[(-0.16, 0.95), (0.0, 0.62), (0.16, 0.95)]])
    a = np.clip(body - notch, 0, 1)
    u, v = grid(w)
    shade = np.where(u + 0.25 * v < 0.05, 0.72, 0.46)
    save("petal", a, shade)


def snowflake():
    w = 128
    arms = poly_mask(w, w, [], 0)
    img, d, ss = canvas(w)
    for i in range(6):
        th = i * math.pi / 3 + math.pi / 2
        c, s = math.cos(th), math.sin(th)
        d.line(px([(0, 0), (0.9 * c, 0.9 * s)], w, w, ss), fill=255, width=int(4 * ss))
        for t, L in ((0.42, 0.3), (0.66, 0.22)):
            bx, by = t * c, t * s
            for sg in (-1, 1):
                th2 = th + sg * math.pi / 3.2
                d.line(px([(bx, by), (bx + L * math.cos(th2), by + L * math.sin(th2))], w, w, ss), fill=255, width=int(3 * ss))
    arms = to_alpha(img, w)
    hub = poly_mask(w, w, [ngon(6, 0.2)])
    a = np.maximum.reduce([hub * CORE, arms * MID * 1.1, halo(arms, 2.0, DIM, 0.5)])
    save("snowflake", np.clip(a, 0, 1), hub * HOT + TINT * 0.6)


def ice_shard():
    """Faceted crystal: lit facet (white-hot ridge), shade facet in the mid band, dim frost rim."""
    w, h = 128, 256
    top, bot = (0.05, 0.98), (-0.04, -0.98)
    left, right, mid = (-0.6, -0.12), (0.55, 0.08), (0.06, 0.02)
    lf = poly_mask(w, h, [[top, left, bot, mid]])
    rf = poly_mask(w, h, [[top, mid, bot, right]])
    ridge = poly_mask(w, h, [[top, (0.2, 0.3), mid, (0.0, 0.35)]])
    whole = np.maximum(lf, rf)
    a = np.maximum.reduce([rf * CORE, lf * MID, halo(whole, 2.0, DIM, 0.5)])
    save("ice_shard", a, ridge * HOT + (1 - ridge) * np.where(rf > 0.5, 0.6, 0.4))


def crystal():
    """Ice crystal cluster bursting from the ground: seven faceted prisms fanning upward."""
    w = 256
    rng = np.random.default_rng(81)
    a = np.zeros((w, w))
    heat = np.zeros((w, w))
    specs = [(-0.0, 0.0, 1.0, 0.16), (-0.35, -0.42, 0.62, 0.12), (0.33, 0.38, 0.7, 0.13), (-0.62, -0.75, 0.42, 0.1),
             (0.6, 0.72, 0.45, 0.1), (-0.15, -0.18, 0.5, 0.1), (0.18, 0.2, 0.55, 0.1)]
    for bx, lean, L, wd in specs:
        ang = math.pi / 2 - lean * 0.9
        base = (bx * 0.55, -0.88)
        tip = (base[0] + L * 1.7 * math.cos(ang), base[1] + L * 1.7 * math.sin(ang))
        nx, ny = -math.sin(ang), math.cos(ang)
        shoulder = 0.78
        sl = (base[0] + (tip[0] - base[0]) * shoulder + nx * wd, base[1] + (tip[1] - base[1]) * shoulder + ny * wd)
        sr = (base[0] + (tip[0] - base[0]) * shoulder - nx * wd, base[1] + (tip[1] - base[1]) * shoulder - ny * wd)
        bl = (base[0] + nx * wd, base[1] + ny * wd)
        br = (base[0] - nx * wd, base[1] - ny * wd)
        cm = (base[0] + (tip[0] - base[0]) * shoulder + nx * wd * 0.1, base[1] + (tip[1] - base[1]) * shoulder + ny * wd * 0.1)
        left = poly_mask(w, w, [[bl, sl, tip, cm, base]])
        right = poly_mask(w, w, [[base, cm, tip, sr, br]])
        shard = np.maximum(left, right)
        ridge = poly_mask(w, w, [[cm, tip]], width=2.2)
        a = np.where(shard > 0.5, np.maximum(left * MID, right * CORE), np.maximum(a, shard * CORE))
        heat = np.where(shard > 0.5, ridge * HOT + right * 0.3, heat)
    u, v = grid(w)
    a = np.maximum(a, halo(sstep(0.3, 0.7, a), 2.5, DIM, 0.5))
    save("crystal", a, heat + TINT * 0.4)


def thorn():
    """Curved vine spike (root eruption), two-tone."""
    w, h = 128, 256
    L, R = [], []
    for k in range(41):
        t = k / 40
        y = -1 + 1.95 * t
        x = 0.25 * math.sin(t * 2.4) - 0.1
        wd = 0.32 * (1 - t) ** 1.2
        L.append((x - wd, y))
        R.append((x + wd, y))
    polys = [L + R[::-1]]
    for t, sg in ((0.3, 1), (0.5, -1), (0.68, 1)):
        y = -1 + 1.95 * t
        x = 0.25 * math.sin(t * 2.4) - 0.1
        wd = 0.32 * (1 - t) ** 1.2
        polys.append([(x + sg * wd * 0.8, y - 0.08), (x + sg * wd * 0.8, y + 0.08), (x + sg * (wd + 0.3), y + 0.2)])
    a = poly_mask(w, h, polys)
    u, v = grid(w, h)
    spine = np.array([0.25 * math.sin(((vv + 1) / 1.95) * 2.4) - 0.1 for vv in v[:, 0]])[:, None]
    shade = np.where(u > spine - 0.02, 0.72, 0.42)
    save("thorn", a, shade)


def feather():
    """Feather with a lit left vane, mid right vane and barb separations."""
    w, h = 128, 256
    Lp, Rp = [], []
    for k in range(41):
        t = k / 40
        y = -0.95 + 1.9 * t
        wd = 0.55 * math.sin(math.pi * min(1, t * 1.08)) ** 0.7 * (1 - 0.3 * t)
        sway = 0.12 * math.sin(t * 2.0)
        Lp.append((sway - wd * 0.75, y))
        Rp.append((sway + wd, y))
    spine = [(0.12 * math.sin(t * 2.0), -0.95 + 1.9 * t) for t in np.linspace(0, 1, 41)]
    left = poly_mask(w, h, [Lp + spine[::-1]])
    right = poly_mask(w, h, [spine + Rp[::-1]])
    bimg, bd, ss = canvas(w, h)
    for k in range(4):
        t = 0.3 + k * 0.16
        y = -0.95 + 1.9 * t
        s = 0.12 * math.sin(t * 2.0)
        bd.line(px([(s, y), (s + 0.7, y + 0.32)], w, h, ss), fill=255, width=int(2.2 * ss))
    for k in range(3):
        t = 0.38 + k * 0.18
        y = -0.95 + 1.9 * t
        s = 0.12 * math.sin(t * 2.0)
        bd.line(px([(s, y), (s - 0.6, y + 0.3)], w, h, ss), fill=255, width=int(2.2 * ss))
    cuts = to_alpha(bimg, w, h)
    shaft = poly_mask(w, h, [spine[:-2]], width=2.4)
    a = np.maximum.reduce([np.clip(left - cuts * 0.6, 0, 1) * CORE, np.clip(right - cuts * 0.5, 0, 1) * MID, shaft * CORE])
    save("feather", a, np.maximum(left * 0.78, right * 0.5) * (1 - cuts * 0.4) + shaft * 0.2)


def wings():
    """Spread angelic wings (square, for square/tall quads). Three feather rows hang from a curved arm:
    long primaries (mid band) behind secondaries (solid colour) and white-hot coverts; every feather is
    outlined by a thin lower band so the rows read as separate cel shapes."""
    final = 512
    w = final * 2          # drawn on a 2x canvas in +-2 units, then fitted to the square
    ss = 2
    level = Image.new("L", (w * ss, w * ss), 0)
    heat = Image.new("L", (w * ss, w * ss), 0)
    dl, dh = ImageDraw.Draw(level), ImageDraw.Draw(heat)

    def bez(t, p0, p1, p2):
        return ((1 - t) ** 2 * p0[0] + 2 * (1 - t) * t * p1[0] + t * t * p2[0],
                (1 - t) ** 2 * p0[1] + 2 * (1 - t) * t * p1[1] + t * t * p2[1])

    shoulder, ctrl, tip = (0.07, 0.0), (0.3, 0.95), (0.78, 1.05)
    rows = [  # count, t-range along arm, length(t), angle deg (t), width, level, heat
        (12, (0.08, 1.0), lambda t: 0.5 + 0.55 * t ** 0.8, lambda t: -98 + 52 * t, 0.075, int(MID * 255), 0),
        (11, (0.04, 0.85), lambda t: 0.3 + 0.24 * t, lambda t: -100 + 48 * t, 0.07, 255, 110),
        (10, (0.02, 0.75), lambda t: 0.13 + 0.08 * t, lambda t: -102 + 45 * t, 0.06, 255, 255),
    ]
    for side in (-1, 1):
        def place(pts):
            return px([(side * x * 0.5, y * 0.5) for x, y in pts], w, w, ss)
        for count, (t0, t1), length, angle, width, lv, ht in rows:
            for k in range(count - 1, -1, -1):
                t = t0 + (t1 - t0) * k / (count - 1)
                root = bez(t, shoulder, ctrl, tip)
                poly = rot(lens(length(t), width * (0.8 + 0.4 * t), n=18, power=0.6), math.radians(angle(t)), *root)
                p = place(poly)
                dl.polygon(p, fill=lv)
                dl.line(p + p[:1], fill=max(0, int(lv * 0.55)), width=int(1.4 * ss))
                dh.polygon(p, fill=ht)
                dh.line(p + p[:1], fill=0, width=int(1.4 * ss))
        arm = [bez(t, shoulder, ctrl, tip) for t in np.linspace(0, 1, 24)]
        arm_poly = [(x, y + 0.035) for x, y in arm] + [(x, y - 0.05) for x, y in arm[::-1]]
        dl.polygon(place(arm_poly), fill=255)
        dh.polygon(place(arm_poly), fill=255)
    box = level.getbbox()
    cx, cy = (box[0] + box[2]) / 2, (box[1] + box[3]) / 2
    half = max(box[2] - box[0], box[3] - box[1]) / 2 * 1.06
    crop = (int(cx - half), int(cy - half), int(cx + half), int(cy + half))
    a = np.asarray(level.crop(crop).resize((final, final), Image.LANCZOS), dtype=np.float64) / 255
    hm = np.asarray(heat.crop(crop).resize((final, final), Image.LANCZOS), dtype=np.float64) / 255
    a = np.maximum(a, halo(sstep(0.3, 0.6, a), 3, DIM * 0.9, 0.5))
    save("wings", a, hm * HOT + TINT * 0.5 * (1 - hm))


def halo_ring():
    """Saint's halo: white ring with outward thorn-rays, inner bead ring and a dim inner sheen."""
    w = 256
    u, v = grid(w)
    r = np.sqrt(u * u + v * v)
    th = np.arctan2(v, u)
    band = sstep(0.045, 0.035, np.abs(r - 0.66))
    rays = []
    for k in range(16):
        ang = k * 2 * math.pi / 16
        L = 0.3 if k % 2 == 0 else 0.16
        rays.append(rot([(0.0, 0.035), (L, 0.0), (0.0, -0.035)], ang, 0.69 * math.cos(ang), 0.69 * math.sin(ang)))
    rm = poly_mask(w, w, rays)
    beads = np.zeros_like(r)
    for k in range(24):
        ang = k * 2 * math.pi / 24
        bx, by = 0.55 * math.cos(ang), 0.55 * math.sin(ang)
        beads = np.maximum(beads, sstep(0.024, 0.016, np.sqrt((u - bx) ** 2 + (v - by) ** 2)))
    sheen = sstep(0.5, 0.53, r) * sstep(0.7, 0.67, r)
    a = np.maximum.reduce([band * CORE, rm * MID, beads * MID, sheen * DIM, halo(band, 3, DIM, 0.5)])
    save("halo", a * sstep(1.0, 0.97, r), band * HOT + TINT * 0.5)


def cross():
    """Judgment cross: long flared cross, white inner core, colour rim, dim aura and centre star."""
    w, h = 256, 512
    def cross_poly(s, flare):
        x0, x1, y_bar = 0.13 * s, 0.13 * s + flare, 0.42
        bar = 0.08 * s
        return [(-x0, 0.98 - (1 - s) * 0.1), (x0, 0.98 - (1 - s) * 0.1),
                (x0, y_bar + bar), (0.82 - (1 - s) * 0.12, y_bar + bar + flare * 0.3), (0.82 - (1 - s) * 0.12, y_bar - bar - flare * 0.3),
                (x0, y_bar - bar), (x0 + flare * 0.5, -0.92 + (1 - s) * 0.1), (0.0, -0.99 + (1 - s) * 0.12),
                (-x0 - flare * 0.5, -0.92 + (1 - s) * 0.1), (-x0, y_bar - bar),
                (-0.82 + (1 - s) * 0.12, y_bar - bar - flare * 0.3), (-0.82 + (1 - s) * 0.12, y_bar + bar + flare * 0.3), (-x0, y_bar + bar)]
    outer = poly_mask(w, h, [cross_poly(1.0, 0.05)])
    inner = poly_mask(w, h, [cross_poly(0.45, 0.0)])
    u, v = grid(w, h)
    r = np.sqrt(u * u + ((v - 0.42) * 2) ** 2)
    star = poly_mask(w, h, [rot(ray(0.42, 0.06), k * math.pi / 4 + math.pi / 8, 0, 0.42) for k in range(8)])
    a = np.maximum.reduce([inner * CORE, outer * MID, star * MID, halo(outer, 4, DIM, 0.5), sstep(0.3, 0.26, r) * CORE])
    save("cross", a, np.maximum(inner, sstep(0.26, 0.2, r)) * HOT + TINT * 0.45)


def rift():
    """Abyss rift for ALPHA blending: a jagged vertical tear, void-dark inside with a lit rim."""
    w, h = 256, 512
    outline, _ = rift_shape(w, h)
    inside = poly_mask(w, h, [outline])
    rim_m = poly_mask(w, h, [outline + outline[:1]], width=7)
    a = np.maximum(inside, rim_m)
    shade = np.where(rim_m > 0.5, 0.95, 0.06)
    save("rift", a, shade)


def rift_shape(w, h):
    rng = np.random.default_rng(71)
    n = 26
    left, right = [], []
    for k in range(n + 1):
        t = k / n
        y = 0.95 - 1.9 * t
        wd = 0.42 * math.sin(math.pi * t) ** 1.2 + 0.0
        jag = rng.uniform(-0.12, 0.12) * math.sin(math.pi * t)
        left.append((-wd + jag - 0.08 * math.sin(t * 6), y))
        right.append((wd + jag * 0.7 - 0.08 * math.sin(t * 6), y))
    return left + right[::-1], (left, right)


def rift_glow():
    """Additive edge glow for the rift: white seam, colour tendrils licking outward."""
    w, h = 256, 512
    outline, (left, right) = rift_shape(w, h)
    seam = poly_mask(w, h, [outline + outline[:1]], width=5)
    sheath = poly_mask(w, h, [outline + outline[:1]], width=16)
    rng = np.random.default_rng(72)
    tend = []
    for side, pts in ((-1, left), (1, right)):
        for k in range(3, len(pts) - 3, 2):
            x, y = pts[k]
            L = rng.uniform(0.12, 0.35) * math.sin(math.pi * k / len(pts))
            tend.append(rot(ray(L, 0.035, power=1.2), math.pi / 2 - side * rng.uniform(0.6, 1.3), x, y))
    tm = poly_mask(w, h, tend)
    a = np.maximum.reduce([seam * CORE, sheath * MID, tm * DIM, halo(sheath, 5, DIM, 0.4)])
    save("rift_glow", a, seam * HOT + TINT * 0.4)


def meteor():
    """Falling meteor (head at the bottom): white-hot head, colour mantle, streaming split flame tail."""
    w, h = 256, 512
    u, v = grid(w, h)
    x, y = u, v * 2                                       # isotropic units: x -1..1, y -2..2
    hx, hy, hr = 0.0, -1.3, 0.4
    d = np.sqrt((x - hx) ** 2 + (y - hy) ** 2)
    n = tile_noise(128, 1.8, 83)
    streak = nsample(n, u * 14 + 9, v * 1.5)
    t = np.clip((y - hy) / 3.1, 0, 1)                     # 0 at the head .. 1 at the tail end
    above = y > hy
    tail_w = hr * (1 - t) ** 0.7
    strands = (np.abs(x) < tail_w * (0.55 + 0.6 * streak)) & above
    mantle = np.maximum(sstep(hr + 0.015, hr, d), strands * sstep(0.95, 0.75, t))
    core_w = hr * 0.58 * np.clip(1 - t / 0.45, 0, 1)
    core = np.maximum(sstep(hr * 0.6 + 0.015, hr * 0.6, d), ((np.abs(x) < core_w) & above).astype(float))
    dim = np.maximum(sstep(hr * 1.3 + 0.015, hr * 1.3, d), ((np.abs(x) < tail_w * 1.25 + 0.04) & above & (streak > 0.38)) * 1.0)
    a = np.maximum.reduce([core * CORE, mantle * MID, dim * DIM])
    a *= sstep(1.0, 0.9, v) * sstep(-1.0, -0.97, v)
    save("meteor", a, core * HOT + TINT * 0.4)


def rock():
    """Debris chunk for dust bursts (alpha blended): lit top facet, shadow side, ink outline."""
    w = 64
    pts = [(-0.75, 0.15), (-0.3, 0.75), (0.45, 0.62), (0.82, -0.05), (0.4, -0.72), (-0.45, -0.68)]
    body = poly_mask(w, w, [pts])
    inner = poly_mask(w, w, [[(x * 0.8, y * 0.8) for x, y in pts]])
    top = poly_mask(w, w, [[(-0.6, 0.12), (-0.25, 0.6), (0.38, 0.5), (0.25, 0.05)]])
    shade = np.where(top > 0.5, 0.82, 0.45) * (inner > 0.5) + (inner <= 0.5) * 0.14
    save("rock", body, shade)


def skull_wisp():
    w = 256
    img, d, ss = canvas(w)
    tail = []
    for k in range(31):
        t = k / 30
        y = -0.15 - 0.85 * t
        x = 0.18 * math.sin(t * 7) * t
        tail.append((x, y, 0.42 * (1 - t) ** 1.3))
    d.polygon(px([(x - wd, y) for x, y, wd in tail] + [(x + wd, y) for x, y, wd in tail[::-1]], w, w, ss), fill=255)
    c = px([(0, 0.25)], w, w, ss)[0]
    r = 0.5 * w * ss / 2
    d.ellipse([c[0] - r, c[1] - r * 0.95, c[0] + r, c[1] + r * 1.0], fill=255)
    d.rectangle(px([(-0.28, 0.0)], w, w, ss) + px([(0.28, -0.32)], w, w, ss), fill=255)
    for ex in (-0.19, 0.19):
        q = px([(ex, 0.22)], w, w, ss)[0]
        er = 0.13 * w * ss / 2
        d.ellipse([q[0] - er, q[1] - er * 0.85, q[0] + er, q[1] + er * 1.1], fill=0)
    d.polygon(px([(0, 0.02), (-0.06, -0.1), (0.06, -0.1)], w, w, ss), fill=0)
    for tx in (-0.15, -0.05, 0.05, 0.15):
        d.rectangle(px([(tx - 0.02, -0.18)], w, w, ss) + px([(tx + 0.02, -0.32)], w, w, ss), fill=0)
    a = to_alpha(img, w)
    a = glowify(a, 5, 0.5)
    save("skull_wisp", a)


def chevron(name, up=True):
    w = 128
    img, d, ss = canvas(w)
    s = 1 if up else -1
    for k, y in enumerate((-0.25, 0.25)):
        y *= s
        d.polygon(px([(-0.7, y - 0.2 * s), (0, y + 0.45 * s), (0.7, y - 0.2 * s), (0.7, y - 0.48 * s), (0, y + 0.17 * s), (-0.7, y - 0.48 * s)], w, w, ss), fill=255)
    a = to_alpha(img, w)
    save(name, glowify(a, 3, 0.5))


def droplet():
    w, h = 64, 128
    img, d, ss = canvas(w, h)
    pts = []
    for k in range(41):
        t = k / 40 * 2 * math.pi
        x = 0.8 * math.sin(t)
        y = -0.35 + 0.55 * math.cos(t)
        if math.cos(t) > 0:
            y = -0.35 + 1.3 * math.cos(t) ** 1.6
            x = 0.8 * math.sin(t) * (1 - 0.0)
        pts.append((x * (1 - 0.6 * max(0, (y + 0.35) / 1.3)), y))
    d.polygon(px(pts, w, h, ss), fill=255)
    a = to_alpha(img, w, h)
    u, v = grid(w, h)
    hl = np.exp(-(((u + 0.3) / 0.15) ** 2 + ((v + 0.35) / 0.2) ** 2))
    save("droplet", a, np.clip(0.75 + 0.25 * hl + 0.2 * sstep(0.2, -0.8, v), 0, 1))


def bubble():
    u, v = grid(128)
    r = np.sqrt(u * u + v * v)
    rim = np.exp(-((r - 0.84) / 0.07) ** 2) + sstep(0.86, 0.3, r) * 0.15
    hl = np.exp(-(((u + 0.35) / 0.16) ** 2 + ((v - 0.38) / 0.12) ** 2)) * 0.9
    a = np.clip((rim + hl) * sstep(0.95, 0.9, r), 0, 1)
    save("bubble", a)


def text_glyph(name, draw_fn, w=128, outline=True):
    img, d, ss = canvas(w)
    draw_fn(d, w, ss)
    fill = to_alpha(img, w)
    if outline:
        o = np.asarray(img.filter(ImageFilter.MaxFilter(ss * 4 + 1)).resize((w, w), Image.LANCZOS), dtype=np.float64) / 255
        a = np.maximum(fill, o)
        rgb = fill * 1.0 + (1 - fill) * 0.15
        save(name, a, rgb)
    else:
        save(name, glowify(fill, 3, 0.5))


def zzz(d, w, ss):
    def z(cx, cy, s, wd):
        pts = [(-1, 1), (1, 1), (1, 0.62), (-0.35, -0.62), (1, -0.62), (1, -1), (-1, -1), (-1, -0.62), (0.35, 0.62), (-1, 0.62)]
        d.polygon(px([(cx + x * s, cy + y * s) for x, y in pts], w, w, ss), fill=255)
    z(-0.25, -0.25, 0.42, 1)
    z(0.42, 0.45, 0.26, 1)


def note(d, w, ss):
    c = px([(-0.25, -0.5)], w, w, ss)[0]
    r = 0.26 * w * ss / 2
    d.ellipse([c[0] - r * 1.25, c[1] - r * 0.9, c[0] + r * 1.25, c[1] + r * 0.9], fill=255)
    d.polygon(px([(-0.02, -0.5), (0.1, -0.5), (0.1, 0.85), (-0.02, 0.85)], w, w, ss), fill=255)
    d.polygon(px([(0.1, 0.85), (0.6, 0.45), (0.6, 0.15), (0.1, 0.55)], w, w, ss), fill=255)


def hymn(d, w, ss):
    """Holy glyph: cross with halo ring and four sparkle dots."""
    d.polygon(px([(-0.1, -0.85), (0.1, -0.85), (0.1, 0.25), (0.42, 0.25), (0.42, 0.43), (0.1, 0.43), (0.1, 0.85), (-0.1, 0.85), (-0.1, 0.43), (-0.42, 0.43), (-0.42, 0.25), (-0.1, 0.25)], w, w, ss), fill=255)
    c = px([(0, 0.34)], w, w, ss)[0]
    r = 0.55 * w * ss / 2
    d.ellipse([c[0] - r, c[1] - r, c[0] + r, c[1] + r], outline=255, width=int(3 * ss))


def silence(d, w, ss):
    c = px([(0, 0.1)], w, w, ss)[0]
    r = 0.72 * w * ss / 2
    d.ellipse([c[0] - r, c[1] - r * 0.78, c[0] + r, c[1] + r * 0.78], fill=255)
    d.polygon(px([(-0.35, -0.35), (-0.55, -0.85), (-0.05, -0.45)], w, w, ss), fill=255)
    for dx in (-0.36, 0.0, 0.36):
        q = px([(dx, 0.1)], w, w, ss)[0]
        rr = 0.09 * w * ss / 2
        d.ellipse([q[0] - rr, q[1] - rr, q[0] + rr, q[1] + rr], fill=0)
    d.line(px([(-0.8, -0.75), (0.8, 0.9)], w, w, ss), fill=0, width=int(14 * ss))
    d.line(px([(-0.8, -0.75), (0.8, 0.9)], w, w, ss), fill=255, width=int(7 * ss))


def anger(d, w, ss):
    """Anime anger mark: four curved brackets forming a cross-popping vein."""
    for q in range(4):
        ang = q * math.pi / 2 + math.pi / 4
        pts = []
        for k in range(13):
            t = -0.75 + 1.5 * k / 12
            r = 0.62 - 0.25 * (1 - t * t)
            pts.append((r * math.cos(ang + t * 0.55), r * math.sin(ang + t * 0.55)))
        d.line(px(pts, w, w, ss), fill=255, width=int(11 * ss), joint="curve")


def blind(d, w, ss):
    pts_u = [(-0.85, 0.0)] + [(x, 0.45 * (1 - x * x / 0.72)) for x in np.linspace(-0.85, 0.85, 20)] + [(0.85, 0.0)]
    pts_d = [(x, -0.45 * (1 - x * x / 0.72)) for x in np.linspace(0.85, -0.85, 20)]
    d.polygon(px(pts_u + pts_d, w, w, ss), fill=255)
    c = px([(0, 0)], w, w, ss)[0]
    r = 0.25 * w * ss / 2
    d.ellipse([c[0] - r, c[1] - r, c[0] + r, c[1] + r], fill=0)
    d.line(px([(-0.8, -0.8), (0.8, 0.8)], w, w, ss), fill=0, width=int(14 * ss))
    d.line(px([(-0.8, -0.8), (0.8, 0.8)], w, w, ss), fill=255, width=int(7 * ss))


def tornado():
    """Whirlwind funnel (1:2, narrow foot at the bottom): wrapping wind bands with white leading edges."""
    w, h = 256, 512
    u, v = grid(w, h)
    t = (v + 1) * 0.5                                     # 0 at the foot .. 1 at the top
    half = 0.16 + 0.78 * t ** 1.35                        # funnel half-width
    x = u / half                                          # -1..1 across the funnel
    inside = sstep(1.04, 0.96, np.abs(x)) * sstep(1.0, 0.95, t)
    n = tile_noise(128, 2.4, 97)
    wob = nsample(n, x * 3 + 31, t * 9) - 0.5
    # Bands wrap around the funnel: phase follows the visible arc (asin of x) plus a climb with height.
    arc = np.arcsin(np.clip(x, -1, 1))
    s1 = 0.5 + 0.5 * np.cos(arc * 1.4 + t * 46 + wob * 1.6)
    s2 = 0.5 + 0.5 * np.cos(arc * 2.1 + t * 71 + 1.3 + wob * 2.4)
    edge = np.maximum(sstep(0.93, 0.96, s1), sstep(0.965, 0.985, s2) * sstep(0.15, 0.4, t))
    band = np.maximum(sstep(0.7, 0.74, s1), sstep(0.86, 0.9, s2))
    body = sstep(0.25, 0.3, s1)
    rim = sstep(0.82, 0.95, np.abs(x)) * sstep(1.02, 0.96, np.abs(x))
    a = np.maximum.reduce([edge * CORE, band * MID, body * DIM, rim * MID]) * inside
    a *= sstep(0.0, 0.12, t)                              # foot dissolves into the ground
    save("tornado", a, edge * HOT + TINT * 0.4)

def sword():
    """Giant holy sword (point down, 1:2): white fuller, colour blade, winged guard, gem pommel."""
    w, h = 256, 512
    blade = [(-0.24, 0.5), (0.24, 0.5), (0.22, -0.66), (0.0, -0.99), (-0.22, -0.66)]
    fuller = [(-0.07, 0.46), (0.07, 0.46), (0.06, -0.62), (0.0, -0.8), (-0.06, -0.62)]
    guard = [(-0.95, 0.62), (-0.7, 0.52), (-0.25, 0.5), (0.25, 0.5), (0.7, 0.52), (0.95, 0.62),
             (0.6, 0.6), (0.3, 0.62), (0.0, 0.66), (-0.3, 0.62), (-0.6, 0.6)]
    grip = [(-0.08, 0.62), (0.08, 0.62), (0.08, 0.86), (-0.08, 0.86)]
    bm = poly_mask(w, h, [blade])
    fm = poly_mask(w, h, [fuller])
    gm = poly_mask(w, h, [guard, grip])
    img, d, ss = canvas(w, h)
    disc(d, w, h, ss, 0, 0.92, 0.13)
    disc(d, w, h, ss, 0, 0.56, 0.11)
    gems = to_alpha(img, w, h)
    whole = np.maximum.reduce([bm, gm, gems])
    a = np.maximum.reduce([fm * CORE, gems * CORE, bm * MID, gm * CORE, halo(whole, 4, DIM, 0.5)])
    save("sword", a, np.maximum(fm, gems) * HOT + gm * 0.5 + TINT * 0.3)


def plus():
    """Rounded heal cross: white centre, colour body, dim outline."""
    w = 128
    def cross_poly(s):
        a, b = 0.22 * s, 0.82 * s
        return [(-a, -b), (a, -b), (a, -a), (b, -a), (b, a), (a, a), (a, b), (-a, b), (-a, a), (-b, a), (-b, -a), (-a, -a)]
    outer = poly_mask(w, w, [cross_poly(1.0)])
    inner = poly_mask(w, w, [cross_poly(0.55)])
    a = np.maximum.reduce([inner * CORE, outer * MID, halo(outer, 2.5, DIM, 0.5)])
    save("plus", a, inner * HOT + TINT * 0.6)


# ----------------------------------------------------------------------------- skill signature shapes

def lance():
    """Long spear of light/ice (1:4, point up): white-hot fuller, faceted diamond head, flared guard, tapering tail."""
    w, h = 128, 512
    head = [(0.0, 0.995), (0.62, 0.62), (0.3, 0.5), (0.0, 0.47), (-0.3, 0.5), (-0.62, 0.62)]
    head_lit = [(0.0, 0.995), (0.62, 0.62), (0.3, 0.5), (0.0, 0.47)]
    guard = [(-0.95, 0.47), (-0.3, 0.44), (0.3, 0.44), (0.95, 0.47), (0.55, 0.38), (0.0, 0.4), (-0.55, 0.38)]
    shaft = [(-0.16, 0.45), (0.16, 0.45), (0.1, -0.9), (0.0, -0.995), (-0.1, -0.9)]
    fuller = [(-0.05, 0.9), (0.05, 0.9), (0.04, -0.75), (0.0, -0.85), (-0.04, -0.75)]
    hm, hl, gm, sm, fm = (poly_mask(w, h, [p]) for p in (head, head_lit, guard, shaft, fuller))
    whole = np.maximum.reduce([hm, gm, sm])
    a = np.maximum.reduce([fm * CORE, hl * CORE, hm * MID, gm * MID, sm * MID, halo(whole, 4, DIM, 0.5)])
    save("lance", a, np.maximum(fm, hl * 0.7) * HOT + gm * 0.6 + TINT * 0.35)


def crow():
    """Crow silhouette with spread wings for ALPHA blending: ink body, shadow-tone feathers, bright eye."""
    w = 128
    img, d, ss = canvas(w)
    wing_l = [(-0.08, 0.05), (-0.45, 0.4), (-0.95, 0.55), (-0.8, 0.38), (-0.9, 0.3), (-0.72, 0.18), (-0.82, 0.08),
              (-0.6, 0.0), (-0.66, -0.1), (-0.3, -0.08)]
    wing_r = [(-x, y) for x, y in wing_l]
    body = [(-0.14, 0.12), (0.0, 0.2), (0.14, 0.12), (0.12, -0.4), (0.26, -0.72), (0.0, -0.58), (-0.26, -0.72), (-0.12, -0.4)]
    for poly in (wing_l, wing_r, body):
        d.polygon(px(poly, w, w, ss), fill=255)
    disc(d, w, w, ss, 0.0, 0.26, 0.2)
    d.polygon(px([(0.0, 0.48), (-0.07, 0.3), (0.07, 0.3)], w, w, ss), fill=255)    # beak
    a = to_alpha(img, w)
    u, v = grid(w)
    eye = np.exp(-(((u - 0.06) / 0.04) ** 2 + ((v - 0.29) / 0.04) ** 2))
    feather = 0.32 + 0.12 * sstep(0.0, 0.6, np.abs(u)) * sstep(0.0, 0.4, v)
    outline = halo(a, 1.2, 1.0, 0.9)
    save("crow", np.maximum(a, outline * 0.9), np.clip(np.where(a > 0.5, feather, 0.1) + eye * 0.8, 0, 1))


def eye():
    """Evil eye: almond outline with a burning iris, slit pupil and short radiating lashes (dread / hawk eye)."""
    w = 128
    u, v = grid(w)
    lid = np.abs(v) - 0.42 * np.clip(1 - (u / 0.92) ** 2, 0, 1) ** 0.75
    almond = sstep(0.03, -0.03, lid)
    rim = sstep(0.06, 0.0, np.abs(lid + 0.0)) * (np.abs(u) < 0.95)
    r = np.sqrt(u * u + v * v)
    iris = sstep(0.34, 0.3, r) * almond
    pupil = sstep(0.08, 0.05, np.abs(u) * (1 + 0.0)) * sstep(0.3, 0.26, r)
    lashes = poly_mask(w, w, [rot(ray(0.36, 0.07), math.pi / 2 + k * 0.36, 0.22 * k, 0.4 - 0.05 * abs(k))
                              for k in (-2, -1, 0, 1, 2)])
    a = np.maximum.reduce([rim * CORE, np.clip(iris - pupil, 0, 1) * CORE, almond * DIM, lashes * MID,
                           halo(np.maximum(rim, lashes), 2.5, DIM, 0.5)])
    save("eye", a, np.clip(iris - pupil, 0, 1) * HOT * 0.9 + rim * 0.6 + TINT * 0.4)


def reticle():
    """Lock-on reticle: double ring with a gap, four inward ticks, centre diamond (hunter mark / snipe)."""
    w = 128
    u, v = grid(w)
    r = np.sqrt(u * u + v * v)
    th = np.arctan2(v, u)
    gaps = sstep(0.12, 0.2, np.abs(np.sin(2 * th)))      # breaks at the four tick positions
    ring1 = sstep(0.05, 0.02, np.abs(r - 0.78)) * gaps
    ring2 = sstep(0.025, 0.01, np.abs(r - 0.6))
    ticks = poly_mask(w, w, [rot([(0.92, 0.05), (0.92, -0.05), (0.5, 0.0)], k * math.pi / 2) for k in range(4)])
    dia = poly_mask(w, w, [[(0, 0.14), (0.14, 0), (0, -0.14), (-0.14, 0)]])
    lines = np.maximum.reduce([ring1, ticks, dia])
    a = np.maximum.reduce([lines * CORE, ring2 * MID, halo(lines, 2.0, DIM, 0.5)])
    save("reticle", a, np.maximum(ticks, dia) * HOT + TINT * 0.45)


def crest():
    """Heraldic shield crest: solid rim, mid face, white-hot cross emblem (protect / iron wall)."""
    w = 128
    def shield(s):
        pts = [(-0.78 * s, 0.82 * s), (0.0, 0.92 * s), (0.78 * s, 0.82 * s)]
        for k in range(1, 13):
            t = k / 12
            x = 0.78 * s * (1 - t ** 1.8)
            y = 0.82 * s - (0.82 * s + 0.95 * s) * t
            pts.append((x, y))
        pts += [(-x, y) for x, y in pts[3:][::-1]]
        return pts
    outer = poly_mask(w, w, [shield(1.0)])
    inner = poly_mask(w, w, [shield(0.78)])
    emblem = poly_mask(w, w, [[(-0.09, 0.6), (0.09, 0.6), (0.09, 0.18), (0.42, 0.18), (0.42, 0.02), (0.09, 0.02),
                               (0.09, -0.55), (-0.09, -0.55), (-0.09, 0.02), (-0.42, 0.02), (-0.42, 0.18), (-0.09, 0.18)]])
    rimband = np.clip(outer - inner, 0, 1)
    a = np.maximum.reduce([rimband * CORE, inner * DIM * 1.4, emblem * CORE, halo(outer, 3, DIM, 0.5)])
    save("crest", np.clip(a, 0, 1), emblem * HOT + rimband * 0.55 + TINT * 0.3)


def soundwave():
    """Sonic boom: three concentric arc pairs radiating left and right from a bright centre (screech / roar)."""
    w = 128
    u, v = grid(w)
    r = np.sqrt(u * u + v * v)
    th = np.abs(np.arctan2(v, np.abs(u)))                 # 0 on the horizontal axis
    cone = sstep(0.95, 0.7, th)
    arcs = np.zeros_like(r)
    for k, rr in enumerate((0.38, 0.62, 0.86)):
        arcs = np.maximum(arcs, sstep(0.05 - k * 0.008, 0.015, np.abs(r - rr)) * cone)
    core = sstep(0.16, 0.12, r)
    a = np.maximum.reduce([arcs * CORE, core * CORE, halo(arcs, 2.0, DIM, 0.5)])
    save("soundwave", a, core * HOT + TINT * 0.5)


# ----------------------------------------------------------------------------- preview sheet

def preview():
    cell = 160
    cols = 8
    rows = (len(WRITTEN) + cols - 1) // cols
    sheet = Image.new("RGBA", (cols * cell, rows * cell), (24, 22, 34, 255))
    d = ImageDraw.Draw(sheet)
    for i, name in enumerate(WRITTEN):
        im = Image.open(os.path.join(OUT, name + ".png")).convert("RGBA")
        im.thumbnail((cell - 20, cell - 26))
        x, y = (i % cols) * cell, (i // cols) * cell
        bg = Image.new("RGBA", im.size, (40, 36, 60, 255))
        bg.alpha_composite(im)
        sheet.alpha_composite(bg, (x + (cell - im.size[0]) // 2, y + 4))
        d.text((x + 6, y + cell - 16), name, fill=(255, 220, 120, 255))
    os.makedirs(os.path.dirname(PREVIEW), exist_ok=True)
    sheet.save(PREVIEW)


def main():
    for fn in (glow, glow_hard, dot, square, spark, ember, star4, star8, star5, hit_flash, ring, shockwave, sunburst,
               speed_lines, arrow_rain, light_streak, slash_arc, slash_strip, slash_cross, trail, beam, claw, bite, noise, cell_noise,
               smoke_sheet, flame_sheet, explosion_sheet, lightning_sheet,
               magic_circle_a, magic_circle_b, magic_circle_c, magic_circle_d, magic_circle_e, magic_circle_f,
               hex_grid, swirl, leaf, petal, snowflake, ice_shard, crystal, thorn, feather, wings, halo_ring, cross,
               rift, rift_glow, meteor, rock, skull_wisp, arrow_streak,
               lambda: chevron("arrow_up", True), lambda: chevron("arrow_down", False), droplet, bubble,
               lambda: text_glyph("zzz", zzz), lambda: text_glyph("note", note), lambda: text_glyph("hymn", hymn, outline=False),
               lambda: text_glyph("silence", silence), lambda: text_glyph("anger", anger), lambda: text_glyph("blind", blind),
               sword, plus, tornado, lance, crow, eye, reticle, crest, soundwave):
        fn()
    if not ONLY:
        preview()
    print(f"wrote {len(WRITTEN)} textures to {OUT}")


if __name__ == "__main__":
    main()
