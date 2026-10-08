"""Generate the Abyss UI kit sprites (midnight glass, cut corners, champagne-gold hairlines) into Assets/_Game/Resources/UI.

Usage: python Tools/ui/gen_ui_sprites.py
Also writes deterministic Unity Sprite import metadata with nine-slice borders, and the
border manifest consumed by Assets/_Game/Editor/UIKitSpriteImporter.cs.
"""
import os

import numpy as np
from PIL import Image, ImageDraw, ImageFilter
from asset_import import texture_meta

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
OUT = os.path.join(ROOT, "Assets", "_Game", "Resources", "UI")
MANIFEST = os.path.join(ROOT, "Assets", "_Game", "Scripts", "Editor", "UI", "UISpriteBorders.txt")
SS = 4  # supersampling factor for anti-aliased vector shapes

BORDERS = {}


# ---------------------------------------------------------------- primitives
def hexc(s, a=1.0):
    s = s.lstrip("#")
    return np.array([int(s[0:2], 16) / 255, int(s[2:4], 16) / 255, int(s[4:6], 16) / 255, a], dtype=np.float32)


def blank(w, h):
    return np.zeros((h, w, 4), dtype=np.float32)  # premultiplied RGBA


def downsample(img_l, w, h):
    return np.asarray(img_l.resize((w, h), Image.LANCZOS), dtype=np.float32) / 255.0


def rrect(w, h, r, inset=0.0, corners=(True, True, True, True)):
    """Anti-aliased rounded-rect coverage. corners = (tl, tr, br, bl)."""
    im = Image.new("L", (w * SS, h * SS), 0)
    d = ImageDraw.Draw(im)
    x0, y0, x1, y1 = inset * SS, inset * SS, (w - inset) * SS - 1, (h - inset) * SS - 1
    rr = max(0.0, r - inset) * SS
    if x1 <= x0 or y1 <= y0:
        return np.zeros((h, w), np.float32)
    d.rounded_rectangle([x0, y0, x1, y1], radius=rr, fill=255, corners=corners)
    return np.clip(downsample(im, w, h), 0, 1)


def stroke(w, h, r, inset, width, corners=(True, True, True, True)):
    return np.clip(rrect(w, h, r, inset, corners) - rrect(w, h, r, inset + width, corners), 0, 1)


def ellipse(w, h, cx, cy, rx, ry=None):
    ry = rx if ry is None else ry
    im = Image.new("L", (w * SS, h * SS), 0)
    ImageDraw.Draw(im).ellipse([(cx - rx) * SS, (cy - ry) * SS, (cx + rx) * SS - 1, (cy + ry) * SS - 1], fill=255)
    return downsample(im, w, h)


def blur(mask, radius):
    im = Image.fromarray(np.clip(mask * 255, 0, 255).astype(np.uint8), "L")
    return np.asarray(im.filter(ImageFilter.GaussianBlur(radius)), dtype=np.float32) / 255.0


def vgrad(h, w, c0, c1, t0=0.0, t1=1.0):
    t = np.clip((np.linspace(0, 1, h) - t0) / max(1e-6, t1 - t0), 0, 1)[:, None, None]
    return np.broadcast_to(c0 * (1 - t) + c1 * t, (h, w, 4)).astype(np.float32)


def hgrad(h, w, c0, c1):
    t = np.linspace(0, 1, w)[None, :, None]
    return np.broadcast_to(c0 * (1 - t) + c1 * t, (h, w, 4)).astype(np.float32)


def layer(color, mask):
    """color: (4,) or (h,w,4) straight RGBA; mask: (h,w) coverage -> premultiplied layer."""
    c = np.asarray(color, np.float32)
    if c.ndim == 1:
        c = np.broadcast_to(c, mask.shape + (4,))
    a = c[..., 3] * mask
    out = np.empty(mask.shape + (4,), np.float32)
    out[..., :3] = c[..., :3] * a[..., None]
    out[..., 3] = a
    return out


def over(dst, src):
    return src + dst * (1 - src[..., 3:4])


def add(dst, src, k=1.0):
    out = dst.copy()
    out[..., :3] = np.clip(dst[..., :3] + src[..., :3] * k, 0, 1)
    out[..., 3] = np.clip(dst[..., 3] + src[..., 3] * k * 0.5, 0, 1)
    return out


def save(name, img, border=None):
    a = np.clip(img[..., 3:4], 0, 1)
    rgb = np.where(a > 1e-5, img[..., :3] / np.maximum(a, 1e-5), 0)
    straight = np.concatenate([np.clip(rgb, 0, 1), a], axis=-1)
    Image.fromarray((straight * 255 + 0.5).astype(np.uint8), "RGBA").save(os.path.join(OUT, name + ".png"))
    if border:
        BORDERS[name] = list(border)
    texture_meta(os.path.join(OUT, name + ".png"), sprite=True, border=border or (0, 0, 0, 0))


# ---------------------------------------------------------------- palette
# Midnight glass with champagne-gold hairlines and cut (chamfered) corners: the modern console-JRPG
# frame language (Trails / Star Rail / Octopath menus) instead of soft rounded web cards.
NAVY = hexc("#141d46", 0.93)
NAVY_DEEP = hexc("#0a0f28", 0.95)
INDIGO_GLOW = hexc("#7088ff", 0.30)
EDGE_DARK = hexc("#02040c", 0.95)
GOLD_HI = hexc("#fbebbd")
GOLD = hexc("#dcb76a")
GOLD_LO = hexc("#9a7536")
DAWN = hexc("#ffb15c")
DAWN_HI = hexc("#ffe3b0")


def gold_grad(h, w, top=0, bottom=None):
    bottom = h if bottom is None else bottom
    return vgrad(h, w, GOLD_HI, GOLD_LO, top / h, bottom / h)


def chamfer(w, h, cuts, inset=0.0):
    """Anti-aliased octagon coverage. cuts = (tl, tr, br, bl) corner cut lengths in px; the inset keeps
    every edge (including the diagonals) parallel, so stacked insets give even hairline borders."""
    k = 0.41421356  # tan(22.5 deg): diagonal offset for an even inset along 45-degree cuts
    x0, y0, x1, y1 = inset, inset, w - inset, h - inset
    tl, tr, br, bl = (max(0.0, c - inset * k) for c in cuts)
    pts = [(x0 + tl, y0), (x1 - tr, y0), (x1, y0 + tr), (x1, y1 - br), (x1 - br, y1), (x0 + bl, y1), (x0, y1 - bl), (x0, y0 + tl)]
    if x1 <= x0 or y1 <= y0:
        return np.zeros((h, w), np.float32)
    im = Image.new("L", (w * SS, h * SS), 0)
    ImageDraw.Draw(im).polygon([(x * SS, y * SS) for x, y in pts], fill=255)
    return np.clip(downsample(im, w, h), 0, 1)


def cline(w, h, cuts, inset, width):
    return np.clip(chamfer(w, h, cuts, inset) - chamfer(w, h, cuts, inset + width), 0, 1)


def poly(w, h, pts):
    im = Image.new("L", (w * SS, h * SS), 0)
    ImageDraw.Draw(im).polygon([(x * SS, y * SS) for x, y in pts], fill=255)
    return downsample(im, w, h)


def diamond_at(w, h, x, y, r):
    return poly(w, h, [(x, y - r), (x + r, y), (x, y + r), (x - r, y)])


# ---------------------------------------------------------------- panels
def glass_base(w, h, cuts, fill_top=hexc("#18224f", 0.93), fill_bottom=hexc("#0b1029", 0.95), glow=INDIGO_GLOW):
    img = blank(w, h)
    body = chamfer(w, h, cuts)
    img = over(img, layer(vgrad(h, w, fill_top, fill_bottom), body))
    # cool light pooling just inside the frame, strongest along the top edge
    rim = np.clip(body - blur(chamfer(w, h, cuts, 6), 6), 0, 1) * body
    img = over(img, layer(vgrad(h, w, glow, glow * np.array([1, 1, 1, 0.35], np.float32)), rim))
    sheen = vgrad(h, w, hexc("#ffffff", 0.08), hexc("#ffffff", 0.0), 0.0, 0.4)
    img = over(img, layer(sheen, chamfer(w, h, cuts, 2)))
    img = over(img, layer(EDGE_DARK, cline(w, h, cuts, 0, 1.0)))
    return img


def cut_ticks(w, h, cuts, inset):
    """Solid gold triangles filling the cut corners just outside the hairline (reads as a crisp frame accent)."""
    m = np.zeros((h, w), np.float32)
    tl, tr, br, bl = cuts
    a = inset
    if tl > 6: m = np.maximum(m, poly(w, h, [(a, a), (a + tl * 0.62, a), (a, a + tl * 0.62)]))
    if tr > 6: m = np.maximum(m, poly(w, h, [(w - a, a), (w - a - tr * 0.62, a), (w - a, a + tr * 0.62)]))
    if br > 6: m = np.maximum(m, poly(w, h, [(w - a, h - a), (w - a - br * 0.62, h - a), (w - a, h - a - br * 0.62)]))
    if bl > 6: m = np.maximum(m, poly(w, h, [(a, h - a), (a + bl * 0.62, h - a), (a, h - a - bl * 0.62)]))
    return m


def panel_glass():
    w = h = 96
    cuts = (14, 4, 14, 4)
    img = glass_base(w, h, cuts)
    img = over(img, layer(gold_grad(h, w) * np.array([1, 1, 1, 0.9], np.float32), cline(w, h, cuts, 2.5, 1.2)))
    img = over(img, layer(hexc("#dcb76a", 0.18), cline(w, h, cuts, 6, 1.0)))
    img = over(img, layer(GOLD, cut_ticks(w, h, cuts, 0.5)))
    save("panel_glass", img, (26, 26, 26, 26))


def gold_mask_layer(mask, w, h):
    """Gold-coloured layer with drop shadow + emboss for an arbitrary coverage mask."""
    shadow = np.roll(np.roll(blur(mask, 1.2), 1, 0), 1, 1)
    img = layer(hexc("#000000", 0.75), shadow)
    img = over(img, layer(gold_grad(h, w), mask))
    hi = np.clip(mask - np.roll(mask, 1, 0), 0, 1)  # top edges catch light
    img = over(img, layer(hexc("#fff6d8", 0.55), hi * mask))
    return img


def panel_ornate():
    """Window frame: double gold hairline, cut corners carrying a jewel, and short gold rails that frame the
    top and bottom edges (all inside the 46 px 9-slice corners, so they never stretch)."""
    w = h = 128
    cuts = (20, 20, 20, 20)
    img = glass_base(w, h, cuts, fill_top=hexc("#19235a", 0.94), fill_bottom=hexc("#0a0e27", 0.96))
    img = over(img, layer(gold_grad(h, w), cline(w, h, cuts, 3, 1.4)))
    img = over(img, layer(hexc("#dcb76a", 0.30), cline(w, h, cuts, 8, 1.0)))
    orn = np.zeros((h, w), np.float32)
    gem = np.zeros((h, w), np.float32)
    for cx, cy in ((9.5, 9.5), (w - 9.5, 9.5), (w - 9.5, h - 9.5), (9.5, h - 9.5)):
        orn = np.maximum(orn, diamond_at(w, h, cx, cy, 7.5))
        gem = np.maximum(gem, diamond_at(w, h, cx, cy, 4.0))
    # rails: thick gold strokes along the first part of each straight edge, tapering into the hairline
    yy, xx = np.mgrid[0:h, 0:w].astype(np.float32) + 0.5
    for y in (1.5, h - 1.5):
        rail = (np.abs(yy - y) <= 1.4) & (((xx > 22) & (xx < 42)) | ((xx > w - 42) & (xx < w - 22)))
        orn = np.maximum(orn, rail.astype(np.float32))
    for x in (1.5, w - 1.5):
        rail = (np.abs(xx - x) <= 1.4) & (((yy > 22) & (yy < 42)) | ((yy > h - 42) & (yy < h - 22)))
        orn = np.maximum(orn, rail.astype(np.float32))
    img = over(img, gold_mask_layer(blur(orn, 0.4), w, h))
    img = over(img, layer(vgrad(h, w, hexc("#ffd7a0"), hexc("#ff8a3d")), gem))
    img = over(img, layer(hexc("#fff4e0", 0.85), gem * (np.roll(gem, 2, 0) < 0.5)))
    save("panel_ornate", img, (46, 46, 46, 46))


def panel_plain():
    w = h = 64
    cuts = (10, 3, 10, 3)
    save("panel_white", layer(hexc("#ffffff"), chamfer(w, h, cuts)), (20, 20, 20, 20))
    save("panel_outline", layer(hexc("#ffffff"), cline(w, h, cuts, 0, 2)), (20, 20, 20, 20))
    save("panel_small", layer(hexc("#ffffff"), chamfer(32, 32, (6, 2, 6, 2))), (10, 10, 10, 10))


def panel_shadow():
    w = h = 128
    m = blur(chamfer(w, h, (20, 6, 20, 6), 28), 10)
    save("panel_shadow", layer(hexc("#000000", 0.85), m), (52, 52, 52, 52))


def tooltip():
    w = h = 64
    cuts = (8, 2, 8, 2)
    img = glass_base(w, h, cuts, fill_top=hexc("#121a40", 0.97), fill_bottom=hexc("#080c22", 0.97), glow=hexc("#5a6fd6", 0.28))
    img = over(img, layer(hexc("#dcb76a", 0.85), cline(w, h, cuts, 2, 1.0)))
    save("tooltip", img, (18, 18, 18, 18))


def slot():
    w = h = 80
    cuts = (12, 3, 12, 3)
    img = blank(w, h)
    body = chamfer(w, h, cuts)
    img = over(img, layer(vgrad(h, w, hexc("#05081a", 0.94), hexc("#0d1434", 0.94)), body))
    inner = np.clip(body - np.roll(chamfer(w, h, cuts, 3), 3, 0), 0, 1)
    img = over(img, layer(hexc("#000000", 0.7), blur(inner, 3) * body))
    img = over(img, layer(hexc("#4b5aa8", 0.22), np.clip(body - blur(chamfer(w, h, cuts, 6), 6), 0, 1) * body))
    img = over(img, layer(gold_grad(h, w) * np.array([1, 1, 1, 0.7], np.float32), cline(w, h, cuts, 1, 1.1)))
    save("slot", img, (24, 24, 24, 24))


# ---------------------------------------------------------------- buttons
BTN_CUTS = (12, 3, 12, 3)


def button(name, top, bottom, line, line_w, glow=None, sheen=0.12, inner_shadow=False, accent=None, ticks=None):
    w, h = 96, 64
    cuts = BTN_CUTS
    img = blank(w, h)
    body = chamfer(w, h, cuts)
    img = over(img, layer(vgrad(h, w, top, bottom), body))
    pool = np.clip(body - blur(chamfer(w, h, cuts, 4), 6), 0, 1) * body
    img = over(img, layer(vgrad(h, w, hexc("#8ea0ff", 0.0), hexc("#8ea0ff", 0.24), 0.4, 1.0), pool))
    if glow is not None:
        img = over(img, layer(glow, np.clip(body - blur(chamfer(w, h, cuts, 6), 8), 0, 1) * body))
    if inner_shadow:
        sh = np.clip(body - np.roll(chamfer(w, h, cuts, 2), 4, 0), 0, 1)
        img = over(img, layer(hexc("#000000", 0.55), blur(sh, 2) * body))
    if sheen > 0:
        gloss = chamfer(w, h, cuts, 2.5)
        gloss[int(h * 0.48):, :] *= 0.0
        img = over(img, layer(vgrad(h, w, hexc("#ffffff", sheen * 1.4), hexc("#ffffff", sheen * 0.3), 0.0, 0.48), gloss))
    img = over(img, layer(EDGE_DARK, cline(w, h, cuts, 0, 1.0)))
    img = over(img, layer(line, cline(w, h, cuts, 1.5, line_w)))
    img = over(img, layer(hexc("#ffffff", 0.12), cline(w, h, cuts, 1.5 + line_w + 1.2, 0.8)))
    if accent is not None:
        # short vertical accent bar on the left edge: the selection language of console JRPG menus
        bar = np.zeros((h, w), np.float32)
        bar[16:h - 16, 5:8] = 1
        img = over(img, layer(accent, blur(bar, 0.5)))
    if ticks is not None:
        img = over(img, layer(ticks, cut_ticks(w, h, cuts, 0.5)))
    save(name, img, (24, 24, 24, 24))


def buttons():
    gold = gold_grad(64, 96)
    button("btn_normal", hexc("#25307a", 0.97), hexc("#0d1236", 0.97), gold * np.array([1, 1, 1, 0.85], np.float32), 1.3,
           accent=hexc("#dcb76a", 0.35), ticks=hexc("#dcb76a", 0.9))
    dawn = vgrad(64, 96, DAWN_HI, DAWN)
    button("btn_hover", hexc("#4458b8", 0.98), hexc("#1a2462", 0.98), dawn, 2.0, glow=hexc("#ffb15c", 0.38), sheen=0.16,
           accent=hexc("#ffe3b0", 1.0), ticks=hexc("#ffe3b0", 1.0))
    button("btn_pressed", hexc("#0e1436", 0.97), hexc("#1e2a66", 0.97), vgrad(64, 96, GOLD, DAWN), 1.7,
           sheen=0.0, inner_shadow=True, accent=hexc("#ffb15c", 1.0), ticks=hexc("#ffcf86", 0.9))
    button("btn_disabled", hexc("#22252f", 0.85), hexc("#14161c", 0.85), hexc("#5a5e6c", 0.7), 1.0, sheen=0.04)


def focus_glow():
    w = h = 128
    cuts = (34, 25, 34, 25)  # matches the button cut once the 22 px glow margin is added
    ring = cline(w, h, cuts, 22, 3.0)
    glow = np.clip(blur(ring, 8) * 2.2, 0, 1)
    img = layer(hexc("#ff9a3c", 0.85), glow)
    img = over(img, layer(hexc("#ffdcaa", 1.0), cline(w, h, cuts, 22.5, 1.6)))
    save("focus_glow", img, (48, 48, 48, 48))


def tabs():
    w, h = 96, 56
    cuts = (12, 12, 0, 0)
    body = chamfer(w, h, cuts)
    act = layer(vgrad(h, w, hexc("#3b4ca4", 0.97), hexc("#16205a", 0.97)), body)
    act = over(act, layer(vgrad(h, w, hexc("#ffffff", 0.16), hexc("#ffffff", 0), 0, 0.5), body))
    act = over(act, layer(EDGE_DARK, cline(w, h, cuts, 0, 1.0)))
    act = over(act, layer(gold_grad(h, w), cline(w, h, cuts, 1.5, 1.3)))
    underline = np.zeros((h, w), np.float32)
    underline[h - 5:h - 1, 4:w - 4] = 1
    act = over(act, layer(hexc("#ffb15c", 0.9), blur(underline, 2.0) * 1.6))
    act = over(act, layer(hexc("#ffe3b0"), underline * 0.95))
    save("tab_active", act, (24, 6, 24, 20))
    ina = layer(vgrad(h, w, hexc("#18204e", 0.82), hexc("#0d1230", 0.82)), body)
    ina = over(ina, layer(EDGE_DARK, cline(w, h, cuts, 0, 1.0)))
    ina = over(ina, layer(hexc("#5b6aa6", 0.55), cline(w, h, cuts, 1.5, 1.0)))
    save("tab_inactive", ina, (24, 6, 24, 20))


# ---------------------------------------------------------------- bars
def bars():
    w, h, r = 48, 18, 6
    body = rrect(w, h, r)
    img = layer(hexc("#03050e", 0.88), body)
    inner = np.clip(body - np.roll(rrect(w, h, r, 1), 2, 0), 0, 1)
    img = over(img, layer(hexc("#000000", 0.6), inner))
    img = over(img, layer(vgrad(h, w, hexc("#c9a45a", 0.9), hexc("#6d5124", 0.9)), stroke(w, h, r, 0, 1.2)))
    save("bar_frame", img, (8, 8, 8, 8))

    w, h, r = 32, 12, 4
    body = rrect(w, h, r)
    shade = np.concatenate([np.linspace(1.0, 0.95, h // 2), np.linspace(0.85, 0.62, h - h // 2)])
    col = np.ones((h, w, 4), np.float32)
    col[..., :3] *= shade[:, None, None]
    img = layer(col, body)
    hl = np.zeros((h, w), np.float32)
    hl[1:3, 3:w - 3] = 1
    img = over(img, layer(hexc("#ffffff", 0.75), hl * body))
    save("bar_fill", img, (5, 5, 5, 5))
    save("bar_flat", layer(hexc("#ffffff"), body), (5, 5, 5, 5))

    # shield / break pips (diamond)
    s = 22

    def diamond(inset):
        im = Image.new("L", (s * SS, s * SS), 0)
        c = s * SS / 2
        rr = (s / 2 - inset) * SS
        ImageDraw.Draw(im).polygon([(c, c - rr), (c + rr, c), (c, c + rr), (c - rr, c)], fill=255)
        return downsample(im, s, s)

    outer, inner = diamond(1), diamond(3.2)
    on = layer(vgrad(s, s, GOLD_HI, GOLD_LO), outer)
    on = over(on, layer(vgrad(s, s, hexc("#d9f4ff"), hexc("#3d8fd6")), inner))
    hl = diamond(6.5) * (np.linspace(1, 0, s)[:, None] > 0.55)
    on = over(on, layer(hexc("#ffffff", 0.8), hl))
    save("pip_on", on)
    off = layer(hexc("#6d5a3a", 0.9), outer)
    off = over(off, layer(hexc("#0b0f22", 0.95), inner))
    save("pip_off", off)


# ---------------------------------------------------------------- portrait
def portrait():
    """Slim double gold ring with a jewel at the base and three small studs, like a console JRPG party face."""
    s = 160
    c = s / 2
    ring_i = 69
    img = layer(hexc("#000000", 0.55), np.clip(blur(ellipse(s, s, c, c, 79), 2.5) - ellipse(s, s, c, c, ring_i), 0, 1))
    band = np.clip(ellipse(s, s, c, c, 77.5) - ellipse(s, s, c, c, ring_i), 0, 1)
    img = over(img, layer(vgrad(s, s, hexc("#1a2252", 0.96), hexc("#090d24", 0.96)), band))
    outer = np.clip(ellipse(s, s, c, c, 77.5) - ellipse(s, s, c, c, 75.6), 0, 1)
    inner = np.clip(ellipse(s, s, c, c, ring_i + 1.8) - ellipse(s, s, c, c, ring_i), 0, 1)
    img = over(img, layer(vgrad(s, s, GOLD_HI, GOLD_LO), np.maximum(outer, inner)))
    img = over(img, layer(hexc("#000000", 0.8), np.clip(ellipse(s, s, c, c, ring_i) - ellipse(s, s, c, c, ring_i - 1.4), 0, 1)))
    studs = np.zeros((s, s), np.float32)
    for (x, y) in ((c, c - 73.5), (c + 73.5, c), (c - 73.5, c)):
        studs = np.maximum(studs, diamond_at(s, s, x, y, 4.5))
    img = over(img, gold_mask_layer(studs, s, s))
    jewel_set = diamond_at(s, s, c, c + 73.5, 9.5)
    jewel = diamond_at(s, s, c, c + 73.5, 5.5)
    img = over(img, gold_mask_layer(jewel_set, s, s))
    img = over(img, layer(vgrad(s, s, hexc("#ffd7a0"), hexc("#ff7f36")), jewel))
    img = over(img, layer(hexc("#ffffff", 0.8), jewel * (np.roll(jewel, 2, 0) < 0.5)))
    save("portrait_frame", img)
    save("portrait_mask", layer(hexc("#ffffff"), ellipse(s, s, c, c, ring_i + 0.5)))
    yy, xx = np.mgrid[0:s, 0:s]
    dist = np.sqrt((xx - c) ** 2 + (yy - c * 0.8) ** 2) / ring_i
    t = np.clip(dist, 0, 1)[..., None]
    col = hexc("#3d4fa8") * (1 - t) + hexc("#0b1028") * t
    bg = layer(col, ellipse(s, s, c, c, ring_i + 0.5))
    save("portrait_bg", bg)


# ---------------------------------------------------------------- ornaments
def separator():
    """Hairline with a hollow centre diamond flanked by two studs; fades out toward both ends."""
    w, h = 512, 24
    cy = h / 2
    cx = w / 2
    yy, xx = np.mgrid[0:h, 0:w].astype(np.float32) + 0.5
    line = ((np.abs(yy - cy) <= 0.7) & (np.abs(xx - cx) > 16)).astype(np.float32)
    m = blur(line, 0.4)
    m = np.maximum(m, np.clip(diamond_at(w, h, cx, cy, 8) - diamond_at(w, h, cx, cy, 5.6), 0, 1))
    m = np.maximum(m, diamond_at(w, h, cx, cy, 2.6))
    for x in (cx - 26, cx + 26):
        m = np.maximum(m, diamond_at(w, h, x, cy, 2.8))
    x = np.abs(np.linspace(-1, 1, w))
    fade = np.clip((1 - x) / 0.6, 0, 1) ** 1.3
    m = m * fade[None, :]
    img = layer(hexc("#ffb15c", 0.30), blur(m, 2.5))
    img = over(img, layer(vgrad(h, w, GOLD_HI, GOLD), m))
    save("separator", img)

    gl = np.exp(-((np.linspace(-1, 1, 16)) ** 2) / 0.12)[:, None] * np.clip((1 - np.abs(np.linspace(-1, 1, 128))) / 0.4, 0, 1)[None, :]
    save("glow_line", layer(hexc("#ffffff"), gl.astype(np.float32)))



def cursor():
    """Sleek double chevron (pointing right) with a warm glow."""
    s = 48
    m = np.maximum(poly(s, s, [(8, 11), (22, 24), (8, 37), (13, 24)]), poly(s, s, [(20, 9), (40, 24), (20, 39), (27, 24)]))
    img = layer(hexc("#ff8a2a", 0.7), np.clip(blur(m, 4) * 1.6, 0, 1))
    img = over(img, layer(hexc("#1a0c04", 0.9), np.clip(blur(m, 0.9) * 3, 0, 1)))
    img = over(img, layer(vgrad(s, s, DAWN_HI, hexc("#ff9b3d"), 0.25, 0.8), m))
    hl = np.clip(m - np.roll(m, 2, 0), 0, 1)
    img = over(img, layer(hexc("#ffffff", 0.7), hl))
    save("cursor_arrow", img)

    s = 32
    m = poly(s, s, [(6, 9), (16, 15), (26, 9), (16, 24)])
    img = layer(hexc("#ff9a3c", 0.7), np.clip(blur(m, 3) * 1.5, 0, 1))
    img = over(img, layer(hexc("#1a0c04", 0.9), np.clip(blur(m, 0.8) * 3, 0, 1)))
    img = over(img, layer(vgrad(s, s, DAWN_HI, hexc("#ffa040"), 0.3, 0.75), m))
    save("arrow_down", img)



def ribbon():
    w, h = 512, 112
    img = blank(w, h)
    band = np.zeros((h, w), np.float32)
    band[14:h - 14, :] = 1
    band = blur(band, 1.0)
    x = np.linspace(0, 1, w)
    fade = np.clip(np.minimum(x, 1 - x) / 0.28, 0, 1) ** 1.2
    body = band * fade[None, :]
    img = over(img, layer(vgrad(h, w, hexc("#1b2456", 0.92), hexc("#0a0e26", 0.92), 0.1, 0.9), body))
    glow = np.zeros((h, w), np.float32)
    glow[h // 2 - 18:h // 2 + 18, :] = 1
    img = over(img, layer(hexc("#6f84ee", 0.18), blur(glow, 14) * fade[None, :]))
    for y in (14, h - 15):
        line = np.zeros((h, w), np.float32)
        line[y:y + 2, :] = 1
        line = line * (fade[None, :] ** 0.8)
        img = over(img, layer(hexc("#ffb15c", 0.45), blur(line, 2.5)))
        img = over(img, layer(GOLD, line))
    for y in (8, h - 9):
        line = np.zeros((h, w), np.float32)
        line[y:y + 1, :] = 1
        img = over(img, layer(hexc("#d6b062", 0.45), line * (fade[None, :] ** 2)))
    save("banner_ribbon", img, (180, 0, 180, 0))


def overlays():
    s = 256
    yy, xx = np.mgrid[0:s, 0:s] / (s - 1) * 2 - 1
    d = np.sqrt((xx * 1.0) ** 2 + (yy * 1.15) ** 2) / 1.41
    a = np.clip((d - 0.35) / 0.65, 0, 1) ** 1.6 * 0.9
    save("vignette", layer(hexc("#03040c"), a.astype(np.float32)))

    s = 128
    yy, xx = np.mgrid[0:s, 0:s] / (s - 1) * 2 - 1
    d = np.sqrt(xx ** 2 + yy ** 2)
    a = np.exp(-(d ** 2) / 0.18) * np.clip(1 - d, 0, 1)
    save("soft_radial", layer(hexc("#ffffff"), a.astype(np.float32)))

    sheen = np.zeros((64, 16), np.float32) + np.clip(1 - np.linspace(0, 1, 64) / 0.65, 0, 1)[:, None] ** 1.5
    save("sheen", layer(hexc("#ffffff"), sheen))

    edge = np.broadcast_to(np.linspace(0, 1, 64)[None, :] ** 1.3, (8, 64)).astype(np.float32)
    save("gradient_h", layer(hexc("#ffffff"), np.ascontiguousarray(edge)))
    edge_v = np.broadcast_to(np.linspace(1, 0, 64)[:, None], (64, 8)).astype(np.float32)
    save("gradient_v", layer(hexc("#ffffff"), np.ascontiguousarray(edge_v)))

    w, h = 256, 48
    img = blank(w, h)
    x = np.linspace(0, 1, w)
    band = np.ones((h, w), np.float32)
    band[:2, :] = 0.0
    band[-2:, :] = 0.0
    band = blur(band, 0.8)
    alpha = (0.55 * (1 - x) ** 1.3 + 0.04)[None, :] * band
    img = over(img, layer(hexc("#ff9e4a"), alpha))
    edge_line = np.zeros((h, w), np.float32)
    edge_line[3:h - 3, 0:3] = 1
    img = over(img, layer(DAWN_HI, edge_line))
    top = np.zeros((h, w), np.float32)
    top[2:3, :] = 1
    img = over(img, layer(hexc("#ffd9a0", 0.6), top * (1 - x)[None, :] ** 2))
    img = over(img, layer(hexc("#ffd9a0", 0.6), np.flipud(top) * (1 - x)[None, :] ** 2))
    save("row_highlight", img, (6, 0, 0, 0))

    save("white", layer(hexc("#ffffff"), np.ones((4, 4), np.float32)))
    save("circle", layer(hexc("#ffffff"), ellipse(64, 64, 32, 32, 31.5)))
    im = Image.new("L", (16 * SS, 16 * SS), 0)
    ImageDraw.Draw(im).polygon([(8 * SS, 1 * SS), (15 * SS, 8 * SS), (8 * SS, 15 * SS), (1 * SS, 8 * SS)], fill=255)
    dm = downsample(im, 16, 16)
    save("diamond", layer(vgrad(16, 16, GOLD_HI, GOLD), dm))


def nameplate():
    w, h = 256, 52
    cuts = (12, 3, 18, 3)
    body = chamfer(w, h, cuts)
    img = layer(hgrad(h, w, hexc("#3a3a8c", 0.97), hexc("#141a48", 0.97)), body)
    img = over(img, layer(vgrad(h, w, hexc("#ffffff", 0.14), hexc("#ffffff", 0), 0, 0.5), chamfer(w, h, cuts, 2)))
    img = over(img, layer(EDGE_DARK, cline(w, h, cuts, 0, 1.0)))
    img = over(img, layer(gold_grad(h, w), cline(w, h, cuts, 2, 1.4)))
    img = over(img, layer(GOLD, cut_ticks(w, h, cuts, 0.5)))
    img = over(img, gold_mask_layer(diamond_at(w, h, 16, h / 2, 6), w, h))
    save("nameplate", img, (30, 20, 20, 20))



def keycap():
    s, r = 40, 8
    body = rrect(s, s, r)
    img = layer(vgrad(s, s, hexc("#f2ecdf", 0.95), hexc("#b9b2a2", 0.95)), body)
    img = over(img, layer(hexc("#6b6455", 0.9), stroke(s, s, r, 0, 1.2)))
    bottom = np.clip(body - np.roll(rrect(s, s, r), -3, 0), 0, 1)
    img = over(img, layer(hexc("#5d5648", 0.9), bottom))
    save("keycap", img, (12, 14, 12, 12))


def main():
    os.makedirs(OUT, exist_ok=True)
    os.makedirs(os.path.dirname(MANIFEST), exist_ok=True)
    panel_glass()
    panel_ornate()
    panel_plain()
    panel_shadow()
    tooltip()
    slot()
    buttons()
    focus_glow()
    tabs()
    bars()
    portrait()
    separator()
    cursor()
    ribbon()
    overlays()
    nameplate()
    keycap()
    with open(MANIFEST, "w", encoding="utf-8", newline="\n") as f:
        for name in sorted(BORDERS):
            f.write(name + " " + " ".join(str(v) for v in BORDERS[name]) + "\n")
    print(f"wrote {len(os.listdir(OUT))} files to {OUT}; {len(BORDERS)} sliced")


if __name__ == "__main__":
    main()
