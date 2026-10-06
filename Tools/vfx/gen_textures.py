"""Procedural texture generator for the Abyss VFX library.

Writes RGBA PNGs into Assets/_Game/Resources/Vfx/Textures (white/grey shading in RGB, shape in alpha;
particle/vertex colour tints them at runtime) and a labelled preview sheet to Temp/vfx_textures.png.

Usage: python Tools/vfx/gen_textures.py
Deterministic (fixed seeds) so re-running produces identical files.
"""
import math
import os
import sys

import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont

ROOT = os.path.normpath(os.path.join(os.path.dirname(__file__), "..", ".."))
OUT = os.path.join(ROOT, "Assets", "_Game", "Resources", "Vfx", "Textures")
PREVIEW = os.path.join(ROOT, "Temp", "vfx_textures.png")
sys.path.insert(0, os.path.join(ROOT, "Tools", "ui"))
from asset_import import texture_meta
RNG = np.random.default_rng(1234)
WRITTEN = []


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


def gauss_blur(a, sigma):
    """Separable gaussian blur of a float array (edges clamp)."""
    if sigma <= 0:
        return a
    r = int(math.ceil(sigma * 3))
    k = np.exp(-0.5 * (np.arange(-r, r + 1) / sigma) ** 2)
    k /= k.sum()
    p = np.pad(a, ((r, r), (r, r)), mode="edge")
    tmp = np.apply_along_axis(lambda m: np.convolve(m, k, mode="valid"), 1, p)
    return np.apply_along_axis(lambda m: np.convolve(m, k, mode="valid"), 0, tmp)


def gauss_blur_wrap(a, sigma):
    r = int(math.ceil(sigma * 3))
    k = np.exp(-0.5 * (np.arange(-r, r + 1) / sigma) ** 2)
    k /= k.sum()
    p = np.pad(a, ((r, r), (r, r)), mode="wrap")
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


def canvas(w, h=None, ss=4):
    h = h or w
    img = Image.new("L", (w * ss, h * ss), 0)
    return img, ImageDraw.Draw(img), ss


def to_alpha(img, w, h=None):
    h = h or w
    return np.asarray(img.resize((w, h), Image.LANCZOS), dtype=np.float64) / 255.0


def glowify(a, sigma, amount, core=1.0):
    """Adds a soft halo around a hard alpha mask."""
    halo = gauss_blur(a, sigma)
    halo = halo / max(halo.max(), 1e-6)
    return np.clip(np.maximum(a * core, halo * amount), 0, 1)


def save(name, alpha, rgb=1.0):
    alpha = np.clip(alpha, 0, 1)
    h, w = alpha.shape
    if np.isscalar(rgb):
        rgb = np.full((h, w, 3), rgb)
    elif rgb.ndim == 2:
        rgb = np.repeat(rgb[:, :, None], 3, axis=2)
    arr = np.dstack([np.clip(rgb, 0, 1), alpha])
    os.makedirs(OUT, exist_ok=True)
    Image.fromarray((arr * 255 + 0.5).astype(np.uint8), "RGBA").save(os.path.join(OUT, name + ".png"))
    texture_meta(os.path.join(OUT, name + ".png"), repeat=name in ("noise", "cell_noise", "hex_grid", "trail", "beam"))
    WRITTEN.append(name)


def rot(points, ang, cx=0.0, cy=0.0):
    c, s = math.cos(ang), math.sin(ang)
    return [(cx + x * c - y * s, cy + x * s + y * c) for x, y in points]


def px(points, w, h, ss):
    """Map centred [-1,1] coordinates (v up) to supersampled pixel coordinates."""
    return [((x + 1) * 0.5 * w * ss, (1 - y) * 0.5 * h * ss) for x, y in points]


# ----------------------------------------------------------------------------- basic shapes

def glow():
    u, v = grid(128)
    r = np.sqrt(u * u + v * v)
    a = np.exp(-r * r * 5.5) * sstep(1.0, 0.75, r)
    save("glow", a)


def glow_hard():
    u, v = grid(128)
    r = np.sqrt(u * u + v * v)
    a = np.maximum(sstep(0.42, 0.30, r), np.exp(-r * r * 7) * 0.75) * sstep(1.0, 0.8, r)
    save("glow_hard", a)


def dot():
    u, v = grid(64)
    r = np.sqrt(u * u + v * v)
    save("dot", sstep(0.9, 0.7, r))


def square():
    u, v = grid(32)
    m = np.maximum(np.abs(u), np.abs(v))
    save("square", sstep(0.95, 0.85, m))


def spark():
    """Horizontal streak (stretched-billboard friendly): hot thin core, tapered ends."""
    u, v = grid(128, 32)
    taper = np.clip(1 - np.abs(u), 0, 1) ** 0.7
    width = 0.08 + 0.55 * taper
    core = np.exp(-(v / np.maximum(width * 0.35, 1e-3)) ** 2) * taper
    halo = np.exp(-(v / np.maximum(width, 1e-3)) ** 2) * taper ** 2 * 0.45
    save("spark", np.clip(core + halo, 0, 1))


def star(points, name, size=256, long=1.0, short=0.45, thin=0.035):
    u, v = grid(size)
    r = np.sqrt(u * u + v * v) + 1e-6
    ang = np.arctan2(v, u)
    a = np.zeros_like(u)
    for i in range(points):
        th = i * math.pi * 2 / points
        length = long if (i % 2 == 0 or points == 4) else short
        along = u * math.cos(th) + v * math.sin(th)
        across = np.abs(-u * math.sin(th) + v * math.cos(th))
        t = np.clip(along / length, 0, 1)
        width = thin * (1 - t) ** 1.6 + 0.002
        ray = sstep(width, width * 0.3, across) * (along > 0) * (1 - t) ** 0.6
        a = np.maximum(a, ray)
    core = np.exp(-r * r * 60)
    halo = np.exp(-r * r * 9) * 0.35
    save(name, np.clip(np.maximum(a, core) + halo, 0, 1))


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
    rgb = np.where(inner > 0.5, 1.0, 0.0) * shade + (1 - inner) * 0.18
    rgb = inner * shade + (1 - inner) * 0.18
    save("star5", outer, rgb)


def ring():
    u, v = grid(256)
    r = np.sqrt(u * u + v * v)
    core = np.exp(-((r - 0.86) / 0.022) ** 2)
    halo = np.exp(-((r - 0.86) / 0.08) ** 2) * 0.5
    save("ring", np.clip(core + halo, 0, 1) * sstep(1.0, 0.97, r))


def shockwave():
    u, v = grid(256)
    r = np.sqrt(u * u + v * v)
    edge = sstep(0.97, 0.90, r)
    inner = sstep(0.35, 0.92, r) ** 2.2
    a = edge * inner
    save("shockwave", a, 0.75 + 0.25 * sstep(0.7, 0.92, r))


def sunburst():
    u, v = grid(256)
    r = np.sqrt(u * u + v * v) + 1e-6
    ang = np.arctan2(v, u)
    rng = np.random.default_rng(7)
    rays = np.zeros_like(u)
    n = 28
    for i in range(n):
        th = i * 2 * math.pi / n + rng.uniform(-0.05, 0.05)
        length = rng.uniform(0.55, 0.98) if i % 2 else rng.uniform(0.8, 1.0)
        d = np.angle(np.exp(1j * (ang - th)))
        width = rng.uniform(0.02, 0.05) * (1 - r / length).clip(0, 1)
        rays = np.maximum(rays, sstep(width + 1e-3, width * 0.2, np.abs(d)) * np.sqrt(np.clip(1 - r / length, 0, 1)))
    core = np.exp(-r * r * 20)
    save("sunburst", np.clip(rays * 0.9 + core + np.exp(-r * r * 4) * 0.25, 0, 1))


def slash_arc():
    """Crescent slash (billboard): sharp outer edge, tapered horns, inner fade."""
    w, h = 512, 256
    u, v = grid(w, h)
    x, y = u, v * 0.5 + 0.0
    cx, cy, R = 0.0, -0.9, 1.45
    r = np.sqrt((x - cx) ** 2 + (y - cy) ** 2)
    ang = np.arctan2(x - cx, y - cy)
    span = 0.85
    t = np.clip(1 - np.abs(ang) / span, 0, 1)
    thick = 0.30 * t ** 0.8
    d = R - r
    blade = sstep(-0.012, 0.006, d) * sstep(thick + 0.001, 0.0, d) ** 1.6 * (t > 0)
    edge = np.exp(-(d / 0.018) ** 2) * t
    a = np.clip(blade * 0.85 + edge, 0, 1)
    save("slash_arc", a, 0.7 + 0.3 * np.clip(edge * 2, 0, 1))


def slash_strip():
    """Mesh slash/trail strip: U along the swing, V across (V=1 outer edge sharp, inner soft)."""
    w, h = 256, 128
    y, x = np.mgrid[0:h, 0:w].astype(np.float64)
    vv = 1 - (y + 0.5) / h
    uu = (x + 0.5) / w
    rng = np.random.default_rng(11)
    streak = np.ones_like(vv)
    for _ in range(9):
        p = rng.uniform(0.15, 0.85)
        streak -= 0.18 * np.exp(-((vv - p) / 0.012) ** 2) * (0.5 + 0.5 * np.sin(uu * math.pi * 2 * rng.integers(1, 3) + rng.uniform(0, 6)))
    body = sstep(0.0, 0.85, vv) ** 2.0 * sstep(1.0, 0.93, vv)
    edge = np.exp(-((vv - 0.93) / 0.03) ** 2)
    a = np.clip(body * 0.75 * streak + edge, 0, 1)
    save("slash_strip", a, np.clip(0.75 + 0.25 * edge + 0.0 * uu, 0, 1))


def trail():
    """Soft horizontal strip for trails/ribbons (U along length, tileable in U)."""
    w, h = 128, 64
    u, v = grid(w, h)
    a = np.exp(-(v / 0.45) ** 2) * sstep(1.0, 0.85, np.abs(v))
    core = np.exp(-(v / 0.12) ** 2)
    save("trail", np.clip(a * 0.6 + core, 0, 1))


def beam():
    """Vertical light pillar: soft sides, bright centre line, fades at bottom/top ends."""
    w, h = 128, 512
    u, v = grid(w, h)
    side = np.exp(-(u / 0.42) ** 2) * 0.55 + np.exp(-(u / 0.1) ** 2)
    ends = sstep(-1.0, -0.82, v) * sstep(1.0, 0.2, v)
    n = tile_noise(128, 2.2, 5)
    nn = np.array(Image.fromarray((n * 255).astype(np.uint8)).resize((w, h), Image.BICUBIC)) / 255.0
    streaks = 0.75 + 0.25 * np.sin(u * 23 + nn * 3)
    save("beam", np.clip(side * ends * streaks, 0, 1))


def claw():
    w = 256
    img, d, ss = canvas(w)
    for i, off in enumerate((-0.42, 0.0, 0.42)):
        pts_l, pts_r = [], []
        n = 40
        for k in range(n + 1):
            t = k / n
            y = 0.85 - 1.7 * t
            x = off + 0.28 * math.sin(t * math.pi * 0.9) - 0.12 + 0.24 * t
            wdt = 0.10 * math.sin(t * math.pi) ** 0.8 * (1.1 if i == 1 else 0.9)
            pts_l.append((x - wdt, y))
            pts_r.append((x + wdt * 0.35, y))
        d.polygon(px(pts_l + pts_r[::-1], w, w, ss), fill=255)
    a = to_alpha(img, w)
    save("claw", glowify(a, 4, 0.5))


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
    for k in range(6):
        t = (k + 0.5) / 6
        x = -0.8 + 1.6 * t
        y = 0.55 - 0.9 * (x ** 2) * 0.55 - 0.1
        L = 0.55 if k in (0, 5) else 0.38
        d.polygon(px([(x - 0.09, y + 0.05), (x + 0.09, y + 0.05), (x, y - L)], w, h, ss), fill=255)
    a = to_alpha(img, w, h)
    save("bite", glowify(a, 3, 0.45))


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


def smoke_sheet():
    """4x4 flipbook of distinct shaded puffs (random-frame usage)."""
    cell, N = 128, 4
    atlas_a = np.zeros((cell * N, cell * N))
    atlas_c = np.zeros((cell * N, cell * N))
    nz = tile_noise(128, 2.1, 9)
    for i in range(N * N):
        rng = np.random.default_rng(100 + i)
        u, v = grid(cell)
        a = np.zeros_like(u)
        for _ in range(rng.integers(5, 9)):
            cx, cy = rng.uniform(-0.35, 0.35, 2)
            rr = rng.uniform(0.25, 0.45)
            a = np.maximum(a, sstep(rr, rr * 0.55, np.sqrt((u - cx) ** 2 + (v - cy) ** 2)))
        a = gauss_blur(a, 2.5)
        nn = np.roll(np.roll(nz, rng.integers(0, 128), 0), rng.integers(0, 128), 1)
        a = np.clip(a * (0.65 + 0.6 * nn) - 0.15, 0, 1)
        a = sstep(0.05, 0.6, a) * sstep(0.98, 0.75, np.sqrt(u * u + v * v))
        gy, gx = np.gradient(gauss_blur(a, 3))
        light = np.clip(0.62 + (-gx + gy) * 9, 0.35, 1.0)
        shade = light * (0.8 + 0.2 * nn)
        r0, c0 = (i // N) * cell, (i % N) * cell
        atlas_a[r0:r0 + cell, c0:c0 + cell] = a * 0.92
        atlas_c[r0:r0 + cell, c0:c0 + cell] = shade
    save("smoke_sheet", atlas_a, atlas_c)


def flame_sheet():
    """4x4 looping flame tongue animation (heat stored in alpha, RGB white)."""
    cell, N = 128, 4
    atlas = np.zeros((cell * N, cell * N))
    big = tile_noise(128, 1.9, 13)
    det = tile_noise(128, 1.4, 14)
    for i in range(N * N):
        t = i / (N * N)
        y, x = np.mgrid[0:cell, 0:cell].astype(np.float64)
        u = (x + 0.5) / cell * 2 - 1
        v = 1 - (y + 0.5) / cell * 2
        sy = ((y + t * cell) % cell).astype(int)
        sy2 = ((y + t * cell * 2) % cell).astype(int)
        xi = x.astype(int)
        n1 = big[sy, xi]
        n2 = det[sy2, xi]
        h = (v + 1) / 2  # 0 bottom .. 1 top
        dx = (n1 - 0.5) * 0.55 * h
        uu = u + dx
        width = 0.62 * (1 - h) ** 0.75 * (0.6 + 0.4 * sstep(0.0, 0.25, h))
        body = sstep(width + 0.02, width * 0.2, np.abs(uu)) * sstep(0.0, 0.08, h + 0.04)
        heat = body * (1.15 - h * 0.95) - n2 * 0.45 * h - (n1 - 0.5) * 0.25
        a = sstep(0.05, 0.55, heat)
        r0, c0 = (i // N) * cell, (i % N) * cell
        atlas[r0:r0 + cell, c0:c0 + cell] = a
    save("flame_sheet", atlas)


# ----------------------------------------------------------------------------- magic circles

def rune_glyphs(count, seed):
    rng = np.random.default_rng(seed)
    gl = []
    for _ in range(count):
        pts = [(gx, gy) for gx in (-1, 0, 1) for gy in (-1, 0, 1, 2)]
        strokes = []
        for _ in range(rng.integers(2, 5)):
            a, b = rng.choice(len(pts), 2, replace=False)
            strokes.append((pts[a], pts[b]))
        if rng.random() < 0.5:
            strokes.append(("dot", pts[rng.integers(len(pts))]))
        gl.append(strokes)
    return gl


def draw_runes(d, w, ss, radius, count, size, width, seed):
    glyphs = rune_glyphs(count, seed)
    for i, g in enumerate(glyphs):
        th = math.pi / 2 - i * 2 * math.pi / count
        cx, cy = radius * math.cos(th), radius * math.sin(th)
        ang = th - math.pi / 2
        for s in g:
            if s[0] == "dot":
                p = rot([(s[1][0] * size, (s[1][1] - 0.5) * size)], ang, cx, cy)[0]
                q = px([p], w, w, ss)[0]
                rr = width * ss * 1.2
                d.ellipse([q[0] - rr, q[1] - rr, q[0] + rr, q[1] + rr], fill=255)
                continue
            (x0, y0), (x1, y1) = s
            p = rot([(x0 * size, (y0 - 0.5) * size), (x1 * size, (y1 - 0.5) * size)], ang, cx, cy)
            d.line(px(p, w, w, ss), fill=255, width=int(width * ss))


def circle_line(d, w, ss, r, width):
    c = w * ss / 2
    rr = r * w * ss / 2
    d.ellipse([c - rr, c - rr, c + rr, c + rr], outline=255, width=max(1, int(width * ss)))


def poly_line(d, w, ss, pts, width):
    d.line(px(pts + pts[:1], w, w, ss), fill=255, width=int(width * ss), joint="curve")


def ngon(n, r, phase=math.pi / 2):
    return [(r * math.cos(phase + i * 2 * math.pi / n), r * math.sin(phase + i * 2 * math.pi / n)) for i in range(n)]


def finish_circle(name, img, w, halo=0.45):
    a = to_alpha(img, w)
    u, v = grid(w)
    r = np.sqrt(u * u + v * v)
    fill = sstep(0.95, 0.2, r) * 0.10
    save(name, np.clip(glowify(a, 3.5, halo) + fill, 0, 1))


def magic_circle_a():
    """Classic hexagram circle with rune band."""
    w = 512
    img, d, ss = canvas(w)
    circle_line(d, w, ss, 0.97, 4)
    circle_line(d, w, ss, 0.92, 2)
    circle_line(d, w, ss, 0.74, 3)
    circle_line(d, w, ss, 0.70, 1.5)
    draw_runes(d, w, ss, 0.82, 24, 0.035, 2.2, 1)
    tri1 = ngon(3, 0.70)
    tri2 = ngon(3, 0.70, -math.pi / 2)
    poly_line(d, w, ss, tri1, 3)
    poly_line(d, w, ss, tri2, 3)
    circle_line(d, w, ss, 0.35, 2.5)
    circle_line(d, w, ss, 0.12, 2)
    for p in ngon(6, 0.70, math.pi / 2):
        q = px([p], w, w, ss)[0]
        rr = 0.035 * w * ss / 2
        d.ellipse([q[0] - rr, q[1] - rr, q[0] + rr, q[1] + rr], outline=255, width=2 * ss)
    finish_circle("magic_circle_a", img, w)


def magic_circle_b():
    """Squares-in-circle with radial ticks (support / buff)."""
    w = 512
    img, d, ss = canvas(w)
    circle_line(d, w, ss, 0.97, 3)
    circle_line(d, w, ss, 0.88, 2)
    for i in range(72):
        th = i * 2 * math.pi / 72
        r0, r1 = (0.88, 0.95) if i % 6 else (0.80, 0.97)
        d.line(px([(r0 * math.cos(th), r0 * math.sin(th)), (r1 * math.cos(th), r1 * math.sin(th))], w, w, ss), fill=255, width=2 * ss)
    poly_line(d, w, ss, ngon(4, 0.80, math.pi / 4), 3)
    poly_line(d, w, ss, ngon(4, 0.80, 0), 3)
    circle_line(d, w, ss, 0.56, 2.5)
    draw_runes(d, w, ss, 0.45, 12, 0.04, 2.2, 2)
    circle_line(d, w, ss, 0.30, 2.5)
    poly_line(d, w, ss, ngon(8, 0.28, 0), 2)
    finish_circle("magic_circle_b", img, w)


def magic_circle_c():
    """Thin rune ring only (counter-rotating overlay layer)."""
    w = 512
    img, d, ss = canvas(w)
    circle_line(d, w, ss, 0.98, 2)
    circle_line(d, w, ss, 0.84, 2)
    draw_runes(d, w, ss, 0.91, 30, 0.028, 2.0, 3)
    finish_circle("magic_circle_c", img, w, 0.35)


def magic_circle_d():
    """Jagged abyss/summoning sigil."""
    w = 512
    img, d, ss = canvas(w)
    circle_line(d, w, ss, 0.96, 4)
    pts = []
    for i in range(32):
        th = math.pi / 2 + i * 2 * math.pi / 32
        rr = 0.93 if i % 2 == 0 else 0.78
        pts.append((rr * math.cos(th), rr * math.sin(th)))
    poly_line(d, w, ss, pts, 2.5)
    poly_line(d, w, ss, [ngon(5, 0.74)[k * 2 % 5] for k in range(5)], 3)
    circle_line(d, w, ss, 0.74, 2.5)
    draw_runes(d, w, ss, 0.62, 16, 0.04, 2.5, 4)
    circle_line(d, w, ss, 0.48, 3)
    for i in range(5):
        th = math.pi / 2 + i * 2 * math.pi / 5
        c = (0.3 * math.cos(th), 0.3 * math.sin(th))
        q = px([c], w, w, ss)[0]
        rr = 0.06 * w * ss / 2
        d.ellipse([q[0] - rr, q[1] - rr, q[0] + rr, q[1] + rr], outline=255, width=3 * ss)
    finish_circle("magic_circle_d", img, w)


def hex_grid():
    """Tileable hex lattice lines for barrier domes (wrap in both axes)."""
    w, h = 256, 256
    y, x = np.mgrid[0:h, 0:w].astype(np.float64)
    s = 4.0
    qx = x / w * s * math.sqrt(3)
    qy = y / h * s * 3.0 / 1.0 / 1.5 * 1.5
    pts = []
    best = np.full((h, w), 1e9)
    second = np.full((h, w), 1e9)
    cols, rows = 4, 4
    for i in range(-1, cols + 1):
        for j in range(-1, rows * 2 + 1):
            cx = (i + (0.5 if j % 2 else 0)) / cols * w
            cy = j / (rows * 2) * h
            dd = np.sqrt((x - cx) ** 2 + ((y - cy) * 1.0) ** 2)
            second = np.where(dd < best, best, np.minimum(second, dd))
            best = np.minimum(best, dd)
    edge = np.exp(-((second - best) / 3.0) ** 2)
    fill = 0.15 + 0.1 * sstep(0, 30, best)
    save("hex", np.clip(edge + fill * 0.4, 0, 1))


def swirl():
    u, v = grid(256)
    r = np.sqrt(u * u + v * v) + 1e-6
    ang = np.arctan2(v, u)
    arms = 0.5 + 0.5 * np.cos(ang * 4 + r * 9)
    a = sstep(0.35, 1.0, arms) * sstep(1.0, 0.6, r) * sstep(0.02, 0.25, r)
    core = np.exp(-r * r * 30) * 0.6
    save("swirl", np.clip(a + core, 0, 1), 0.6 + 0.4 * arms)


# ----------------------------------------------------------------------------- nature / shards

def leaf():
    w = 128
    img, d, ss = canvas(w)
    pts = []
    for k in range(41):
        t = k / 40
        y = -0.85 + 1.75 * t
        x = 0.42 * math.sin(math.pi * t) ** 0.9 * (1 - 0.25 * t)
        pts.append((x, y))
    d.polygon(px(pts + [(-x, y) for x, y in pts[::-1]], w, w, ss), fill=255)
    a = to_alpha(img, w)
    vimg, vd, _ = canvas(w)
    vd.line(px([(0, -0.95), (0, 0.85)], w, w, ss), fill=255, width=3 * ss)
    for k in range(5):
        y0 = -0.5 + k * 0.28
        vd.line(px([(0, y0), (0.25, y0 + 0.22)], w, w, ss), fill=255, width=2 * ss)
        vd.line(px([(0, y0), (-0.25, y0 + 0.22)], w, w, ss), fill=255, width=2 * ss)
    vein = to_alpha(vimg, w)
    u, v = grid(w)
    shade = 0.78 + 0.22 * sstep(-0.3, 0.3, u)
    stem = np.clip(vein, 0, 1)
    save("leaf", np.maximum(a, stem * (np.abs(u) < 0.05)), shade * (1 - 0.35 * stem))


def snowflake():
    w = 128
    img, d, ss = canvas(w)
    for i in range(6):
        th = i * math.pi / 3 + math.pi / 2
        c, s = math.cos(th), math.sin(th)
        d.line(px([(0, 0), (0.9 * c, 0.9 * s)], w, w, ss), fill=255, width=int(3.5 * ss))
        for t, L in ((0.45, 0.28), (0.68, 0.2)):
            bx, by = t * c, t * s
            for sg in (-1, 1):
                th2 = th + sg * math.pi / 3.2
                d.line(px([(bx, by), (bx + L * math.cos(th2), by + L * math.sin(th2))], w, w, ss), fill=255, width=int(2.5 * ss))
    a = to_alpha(img, w)
    save("snowflake", glowify(a, 2.5, 0.5))


def ice_shard():
    w, h = 128, 256
    img_l, dl, ss = canvas(w, h)
    img_r, dr, _ = canvas(w, h)
    top, bot, mid = (0.05, 0.98), (-0.05, -0.98), 0.0
    left = (-0.62, -0.15)
    right = (0.55, 0.05)
    dl.polygon(px([top, left, bot, (mid, 0.0)], w, h, ss), fill=255)
    dr.polygon(px([top, (mid, 0.0), bot, right], w, h, ss), fill=255)
    al = to_alpha(img_l, w, h)
    ar = to_alpha(img_r, w, h)
    a = np.clip(al + ar, 0, 1)
    eimg, ed, _ = canvas(w, h)
    ed.line(px([top, left, bot, right, top], w, h, ss), fill=255, width=3 * ss)
    ed.line(px([top, (mid, 0.0), bot], w, h, ss), fill=255, width=2 * ss)
    edge = to_alpha(eimg, w, h) * a
    u, v = grid(w, h)
    shade = al * (0.55 + 0.25 * (v + 1) / 2) + ar * (0.85 + 0.15 * (v + 1) / 2)
    rgb = np.clip(shade + edge, 0, 1)
    save("ice_shard", np.clip(a * 0.85 + edge * 0.15, 0, 1), rgb)


def thorn():
    """Curved vine spike (root eruption)."""
    w, h = 128, 256
    img, d, ss = canvas(w, h)
    L, R = [], []
    for k in range(41):
        t = k / 40
        y = -1 + 1.95 * t
        x = 0.25 * math.sin(t * 2.4) - 0.1
        wd = 0.32 * (1 - t) ** 1.2
        L.append((x - wd, y))
        R.append((x + wd, y))
    d.polygon(px(L + R[::-1], w, h, ss), fill=255)
    for t, sg in ((0.3, 1), (0.5, -1), (0.68, 1)):
        y = -1 + 1.95 * t
        x = 0.25 * math.sin(t * 2.4) - 0.1
        wd = 0.32 * (1 - t) ** 1.2
        d.polygon(px([(x + sg * wd * 0.8, y - 0.08), (x + sg * wd * 0.8, y + 0.08), (x + sg * (wd + 0.3), y + 0.2)], w, h, ss), fill=255)
    a = to_alpha(img, w, h)
    u, v = grid(w, h)
    shade = 0.55 + 0.45 * sstep(-0.3, 0.3, u + 0.1)
    save("thorn", a, shade)


def lightning_sheet():
    """4 columns of vertical bolts with branches (128x512 each)."""
    cw, h, n = 128, 512, 4
    atlas = np.zeros((h, cw * n))
    for c in range(n):
        rng = np.random.default_rng(300 + c)
        img = Image.new("L", (cw * 2, h * 2), 0)
        d = ImageDraw.Draw(img)

        def bolt(x0, y0, x1, y1, disp, depth, width):
            pts = [(x0, y0), (x1, y1)]
            for _ in range(depth):
                new = [pts[0]]
                for (ax, ay), (bx, by) in zip(pts, pts[1:]):
                    mx, my = (ax + bx) / 2, (ay + by) / 2
                    mx += rng.uniform(-disp, disp)
                    new += [(mx, my), (bx, by)]
                pts = new
                disp *= 0.55
            d.line(pts, fill=255, width=width, joint="curve")
            return pts

        main = bolt(cw, 0, cw + rng.uniform(-30, 30), h * 2, 70, 7, 7)
        for _ in range(3):
            i0 = rng.integers(10, len(main) - 30)
            sx, sy = main[i0]
            bolt(sx, sy, sx + rng.uniform(-90, 90), sy + rng.uniform(120, 300), 30, 5, 3)
        a = np.asarray(img.resize((cw, h), Image.LANCZOS), dtype=np.float64) / 255
        a = glowify(a, 4, 0.55)
        y = np.linspace(0, 1, h)[:, None]
        a *= sstep(0.0, 0.04, y) * sstep(1.0, 0.94, y)
        atlas[:, c * cw:(c + 1) * cw] = a
    save("lightning_sheet", atlas)


def feather():
    w, h = 128, 256
    img, d, ss = canvas(w, h)
    L, R = [], []
    for k in range(41):
        t = k / 40
        y = -0.95 + 1.9 * t
        wd = 0.55 * math.sin(math.pi * min(1, t * 1.1)) ** 0.7 * (1 - 0.3 * t)
        sway = 0.12 * math.sin(t * 2.0)
        L.append((sway - wd * 0.8, y))
        R.append((sway + wd, y))
    d.polygon(px(L + R[::-1], w, h, ss), fill=255)
    a = to_alpha(img, w, h)
    bimg, bd, _ = canvas(w, h)
    for k in range(18):
        t = 0.1 + k * 0.05
        y = -0.95 + 1.9 * t
        sway = 0.12 * math.sin(t * 2.0)
        bd.line(px([(sway, y), (sway + 0.6, y + 0.25)], w, h, ss), fill=255, width=ss)
        bd.line(px([(sway, y), (sway - 0.5, y + 0.25)], w, h, ss), fill=255, width=ss)
    barbs = to_alpha(bimg, w, h)
    simg, sd, _ = canvas(w, h)
    sd.line(px([(0.12 * math.sin(t * 2.0), -0.95 + 1.9 * t) for t in np.linspace(-0.05, 1, 30)], w, h, ss), fill=255, width=3 * ss)
    shaft = to_alpha(simg, w, h)
    rgb = np.clip(0.92 - 0.18 * barbs * a, 0, 1)
    save("feather", np.clip(np.maximum(a * 0.95, shaft), 0, 1), np.clip(rgb + shaft * 0.1, 0, 1))


def wings():
    """Pair of stylised angel wings (512x256) built from layered feather rows."""
    w, h = 512, 256
    img, d, ss = canvas(w, h)
    rimg, rd, _ = canvas(w, h)
    for side in (-1, 1):
        for row, (count, length, y0) in enumerate(((7, 0.62, 0.15), (6, 0.48, 0.32), (5, 0.32, 0.45))):
            for k in range(count):
                t = k / (count - 1)
                ax = side * (0.08 + 0.78 * t)
                ay = y0 + 0.35 * math.sin(t * math.pi * 0.85) - row * 0.02
                ang = -math.pi / 2 - side * (0.15 + 0.6 * t)
                L = length * (1.15 - 0.45 * t)
                wd = 0.05 + 0.02 * (2 - row)
                tip = (ax + L * math.cos(ang) * 0.5, ay + L * math.sin(ang) * 2.0)
                base_l = (ax - wd, ay)
                base_r = (ax + wd, ay)
                pts = [base_l, ((ax + tip[0]) / 2 - wd * 1.2, (ay + tip[1]) / 2), tip, ((ax + tip[0]) / 2 + wd * 1.2, (ay + tip[1]) / 2), base_r]
                d.polygon(px(pts, w, h, ss), fill=255)
                rd.line(px([(ax, ay), tip], w, h, ss), fill=255, width=2 * ss)
        arm = [(side * 0.06, 0.25), (side * 0.45, 0.80), (side * 0.92, 0.72), (side * 0.88, 0.55), (side * 0.40, 0.55), (side * 0.06, 0.05)]
        d.polygon(px(arm, w, h, ss), fill=255)
    a = to_alpha(img, w, h)
    lines = to_alpha(rimg, w, h)
    u, v = grid(w, h)
    shade = 0.8 + 0.2 * (v + 1) / 2 - 0.25 * lines
    save("wings", glowify(a, 3, 0.4), np.clip(shade, 0, 1))


def skull_wisp():
    w = 256
    img, d, ss = canvas(w)
    # wispy tail
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


def arrow_streak():
    """Light arrow pointing +U: bright head, long tapering tail."""
    w, h = 256, 64
    u, v = grid(w, h)
    tail_t = np.clip((u + 1) / 1.6, 0, 1)
    width = 0.06 + 0.22 * tail_t ** 2
    tail = np.exp(-(v / width) ** 2) * tail_t ** 1.5 * (u < 0.62)
    head_img, d, ss = canvas(w, h)
    d.polygon(px([(0.98, 0.0), (0.55, 0.55), (0.62, 0.0), (0.55, -0.55)], w, h, ss), fill=255)
    head = to_alpha(head_img, w, h)
    a = np.clip(np.maximum(tail, head) + gauss_blur(head, 3) * 0.6, 0, 1)
    save("arrow_streak", a)


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


def sword():
    """Giant holy sword silhouette (vertical, point down) with glowing edge."""
    w, h = 128, 512
    img, d, ss = canvas(w, h)
    blade = [(-0.32, 0.55), (0.32, 0.55), (0.30, -0.70), (0.0, -0.99), (-0.30, -0.70)]
    d.polygon(px(blade, w, h, ss), fill=255)
    d.polygon(px([(-0.95, 0.55), (0.95, 0.55), (0.85, 0.63), (-0.85, 0.63)], w, h, ss), fill=255)
    d.polygon(px([(-0.13, 0.63), (0.13, 0.63), (0.13, 0.9), (-0.13, 0.9)], w, h, ss), fill=255)
    c = px([(0, 0.94)], w, h, ss)[0]
    r = 0.2 * w * ss / 2
    d.ellipse([c[0] - r, c[1] - r, c[0] + r, c[1] + r], fill=255)
    a = to_alpha(img, w, h)
    u, v = grid(w, h)
    fuller = np.exp(-(u / 0.06) ** 2) * (v < 0.5) * (v > -0.6)
    rgb = np.clip(0.75 + 0.25 * fuller + 0.1 * sstep(-0.1, 0.3, np.abs(u)), 0, 1)
    save("sword", glowify(a, 4, 0.55), rgb)


def plus():
    w = 64
    img, d, ss = canvas(w)
    d.polygon(px([(-0.2, -0.8), (0.2, -0.8), (0.2, -0.2), (0.8, -0.2), (0.8, 0.2), (0.2, 0.2), (0.2, 0.8), (-0.2, 0.8), (-0.2, 0.2), (-0.8, 0.2), (-0.8, -0.2), (-0.2, -0.2)], w, w, ss), fill=255)
    save("plus", glowify(to_alpha(img, w), 2.5, 0.55))


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
    for fn in (glow, glow_hard, dot, square, spark, lambda: star(4, "star4"), lambda: star(8, "star8", long=1.0, short=0.5),
               star5, ring, shockwave, sunburst, slash_arc, slash_strip, trail, beam, claw, bite, noise, cell_noise,
               smoke_sheet, flame_sheet, magic_circle_a, magic_circle_b, magic_circle_c, magic_circle_d, hex_grid, swirl,
               leaf, snowflake, ice_shard, thorn, lightning_sheet, feather, wings, skull_wisp, arrow_streak,
               lambda: chevron("arrow_up", True), lambda: chevron("arrow_down", False), droplet, bubble,
               lambda: text_glyph("zzz", zzz), lambda: text_glyph("note", note), lambda: text_glyph("hymn", hymn, outline=False),
               lambda: text_glyph("silence", silence), lambda: text_glyph("anger", anger), lambda: text_glyph("blind", blind),
               sword, plus):
        fn()
    preview()
    print(f"wrote {len(WRITTEN)} textures to {OUT}")


if __name__ == "__main__":
    main()
