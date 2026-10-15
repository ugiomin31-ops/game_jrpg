"""The 20 playable hunters (Tools/content/spec.py HUNTERS): modern Korean hunter outfits on the CC0 VRoid samples.

Each hunter: the VRoid base for its gender, hair (the spec's three stops plus a lighter highlight), eyes and brows
recoloured from the spec, the hoodie recoloured or cut into the outfit, and a silhouette piece (cap, helmet, hood,
beret, glasses, headphones, long coat, poncho, cape, vest, shield, ponytail, buzz cut, ...). No fantasy armour:
the pieces are jackets, vests, bags, sportswear, uniforms and accessories.
"""
import os
import sys

import bmesh

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path[:0] = [os.path.join(HERE, "..", "..", "Tools", "content")]
import spec  # noqa: E402

import abyss_bpy as A  # noqa: E402
import anime_body as AB  # noqa: E402
import body as B  # noqa: E402
import garments as G  # noqa: E402
import garments_modern as M  # noqa: E402
import vroid_base as VB  # noqa: E402
from humanoid import V, ellipsoid, solidify  # noqa: E402
from humanoid import mix as _mix, shade as _shade  # noqa: E402


def _hx(c):
    """Hex string for an RGBA/RGB tuple (gradient_map takes hex stops; the humanoid colour helpers return tuples)."""
    if isinstance(c, str):
        return c
    return "#%02x%02x%02x" % tuple(int(round(min(1.0, max(0.0, v)) * 255)) for v in c[:3])


def mix(a, b, t):
    return _hx(_mix(a, b, t))


def shade(c, k):
    return _hx(_shade(c, k))

MALE, FEMALE = "HairSample_Male.vrm", "HairSample_Female.vrm"
SPEC = {h["id"]: h for h in spec.HUNTERS}
GOLD, SILVER, WHITE = G.GOLD, M.SILVER, "#f4f2ec"

# Female sample hair roots (native frame): the cat ears are removed by island (VB.female_ears) for every female
# hunter; _TAILS are the twin tails (removed for the hunters who wear their hair down or up).
_EARS = (V((0.088, 0.021, 1.613)), V((-0.086, 0.021, 1.611)))
_TAILS = (V((0.064, -0.022, 1.602)), V((-0.064, -0.022, 1.602)))

HEIGHT = dict(h_dohyun=1.74, h_seoa=1.56, h_jiho=1.66, h_yuna=1.54, h_minjun=1.80, h_sora=1.60, h_taeyang=1.72,
              h_eunbi=1.56, h_gunwoo=1.76, h_hana=1.56, h_siwoo=1.68, h_mirae=1.58, h_jaehyun=1.76, h_dana=1.62,
              h_iseul=1.62, h_haneul=1.82, h_bora=1.64, h_youngsu=1.70, h_rina=1.52, h_jun=1.74)


# ---------------------------------------------------------------- base body

def _hair_stops(hair):
    h0, h1, h2 = hair
    return [(0.0, h0), (0.45, h1), (0.85, h2), (1.0, mix(h2, "#ffffff", 0.45))]


def _body(H, sp, drop=None):
    """VRoid base for the hunter: drop=None | tuple of hair roots | 'all' (buzz/shaved head)."""
    female = sp["gender"] == "F"
    if drop == "all":
        hd = lambda h: True  # noqa: E731
    elif drop:
        hd = lambda h: any((h - p).length < 0.01 for p in drop)  # noqa: E731
    else:
        hd = None
    body = VB.build(H, FEMALE if female else MALE, height=HEIGHT[sp["id"]], hair_drop=hd,
                    island_drop=VB.female_ears if female else None)
    VB.gradient_map(body, "Hair", _hair_stops(sp["hair"]))
    VB.gradient_map(body, "EyeIris", [(0.0, shade(sp["eyes"], 0.4)), (0.5, sp["eyes"]),
                                       (1.0, mix(sp["eyes"], "#ffffff", 0.5))], keep_bright=0.92)
    VB.gradient_map(body, "FaceBrow", [(0.0, sp["hair"][0]), (1.0, sp["hair"][2])], stretch=False)
    return body


def _start(hid, drop=None):
    sp = SPEC[hid]
    H = AB.AnimeHumanoid(hid)
    body = _body(H, sp, drop)
    return H, body, sp


def _cut_tops_below(body, z):
    """Deletes the base top's faces below z. The female VRoid tunic runs down past the hips and balloons under a
    short jacket, so the hip line ends it and the legs take over."""
    mn = [m.name if m else "" for m in body.data.materials]
    bm = bmesh.new()
    bm.from_mesh(body.data)
    bm.faces.ensure_lookup_table()
    dead = [f for f in bm.faces if "Tops" in mn[f.material_index] and f.calc_center_median().z < z]
    bmesh.ops.delete(bm, geom=dead, context="FACES")
    bmesh.ops.delete(bm, geom=[v for v in bm.verts if not v.link_faces], context="VERTS")
    bm.to_mesh(body.data)
    bm.free()


def _ready(H, body, tops, bottoms, hood=False):
    """Recolours the hoodie (tops) and trousers (bottoms), then rigs the body. The hoodie's hood is cut off unless
    the hunter wears it (its corners would read as spikes on the shoulders)."""
    if not hood:
        G.strip_hood(body, H)
    VB.gradient_map(body, "Tops", tops)
    VB.gradient_map(body, "Bottoms", bottoms)
    H.build_rig()
    H.add_weighted(body)


def _ramp(c0, c1, c2, c3=None):
    """Four-stop luminance ramp for a recoloured VRoid texture (dark -> light)."""
    return [(0.0, c0), (0.5, c1), (0.85, c2), (1.0, c3 or mix(c2, "#ffffff", 0.3))]


def _boots(H, body, top, color, cuff=None):
    """Boots whose shaft ends at `top` (ankle, knee or dress-shoe height); the VRoid shoes are removed."""
    VB.drop_material(body, "Shoes")
    for S in ("L", "R"):
        AB.boot(H, body, S, top, color, cuff_color=cuff)
    AB.drop_faces(body, lambda co: co.z < top - 0.04)


def _bracer(H, body, S, color, reach=0.62, flare=1.05, trim_color=None):
    """Forearm guard with a gentle elbow flare: the library default (1.25) sticks out past the sleeve like spikes."""
    return G.bracer(H, body, S, color, trim_color=trim_color, reach=reach, flare=flare)


def _belt(H, body, color, buckle, width=0.040, pad=0.010, z=None, thick=0.007):
    """Waist belt at hip + 0.03 (or z). pad = how far the belt stands off the bare body: a jacket or vest worn over
    the waist needs pad above its own shell offset (~0.034 for a 0.024 jacket), or the belt sinks inside it.
    thick = strap thickness (the default 0.012 reads as a plank on the slim hunters)."""
    z = H.j["hip"].z + 0.03 if z is None else z
    bx, by = AB.section(body, z)
    return B.belt(H, z, color, buckle, width=width, r=bx + pad, sy=(by + pad) / (bx + pad), thick=thick)


def _buzz(H, body, color):
    """Buzz-cut stubble: a short dark skull shell over the scalp (hair removed by the caller)."""
    c, half, top = G.skull_box(H, body)
    R = V((half.x * 1.04 + 0.004, half.y * 1.04 + 0.004, half.z * 1.00 + 0.004))
    cc = V((c.x, c.y, c.z + 0.002))
    els = [88 - (88 - 20) * k / 14 for k in range(15)]
    o = G._head_grid("buzz", cc, R, els, lambda el: (0.0, 360.0), cols=40)
    A.paint(o, color)
    solidify(o, 0.003)
    H.add_blend(o, G._head_weights(H.j))
    return o


# ---------------------------------------------------------------- the 20 hunters

def h_dohyun():
    """Protagonist: black hoodie (hood kept) under an olive tactical vest, cargo pants, red scarf, fingerless gloves."""
    H, body, sp = _start("h_dohyun")
    _ready(H, body, _ramp("#0e0f14", "#1c1e26", "#2e3240", "#434858"), _ramp("#1e2019", "#33352a", "#4a4d3e"), hood=True)
    M.vest(H, body, "#56612f", pockets=4, pad=0.030, trim_color="#c8323c")
    _belt(H, body, "#1d1d1d", "#8a8a8a", 0.034, pad=0.040)
    M.belt_pouch(H, body, "#4f5a30", side=-1, flap="#3d4626")
    G.scarf(H, body, "#b8323c", tail=0.22)
    for S in ("L", "R"):
        _bracer(H, body, S, "#161616", reach=0.30)
    return H


def h_seoa():
    """University student: cropped beige trench over a white knit, navy skirt, ankle boots, thin round glasses with
    clear lenses, burgundy trim on the coat, belt."""
    H, body, sp = _start("h_seoa", drop=_TAILS)
    _ready(H, body, _ramp("#8e877c", "#c9c2b4", "#eae5da", "#fbf8f2"), _ramp("#050508", "#15151c", "#2a2a34"))
    M.jacket(H, body, "#c3ae83", hem=H.j["hip"].z - 0.02, split=36, trim_color="#7a2e3a", lining="#a8946c")
    M.sleeves(H, body, "#c3ae83")
    _belt(H, body, "#5a4a3a", "#c8b070", 0.028, pad=0.040)
    G.robe_skirt(H, body, "#4a4e63", hem=H.j["knee.L"].z + 0.05, flare=1.12, trim_color=None, wave=0.0,
                 name="skirt", narrow=True)
    M.glasses(H, body, "#b89a5a", lens="#e8f4ff", style="round", tube=0.0016)
    _boots(H, body, H.j["ankle.L"].z + 0.07, "#2a1f1a")
    return H


def h_jiho():
    """Ex national archery athlete: navy track jacket with white stripes, white snapback with a navy brim, arm guard,
    a sports bag strap, grey joggers."""
    H, body, sp = _start("h_jiho")
    _ready(H, body, _ramp("#c9cdd4", "#e4e7ec", "#f4f6f9"), _ramp("#4a4f5a", "#7d8390", "#a4aab5"))
    M.jacket(H, body, "#1d2f57", hem=H.j["hip"].z - 0.10, split=0, pad=0.020, trim_color="#f2f2f2")
    M.sleeves(H, body, "#1d2f57", bands=(0.34, 0.70), band_color="#f2f2f2")
    M.cap(H, body, "#eeeeee", brim="#1d2f57", brim_len=0.075)
    _belt(H, body, "#f2f2f2", "#8a8a8a", 0.030, pad=0.034)
    _bracer(H, body, "L", "#2a2f3a", reach=0.52, trim_color="#f2f2f2")
    M.bag(H, body, "#2a2f3a", strap="#f2f2f2", side=-1)
    return H


def h_yuna():
    """Nursing student: white cardigan over a light-blue scrub top, red-cross armband, white shoes, low ponytail,
    first-aid pouch."""
    H, body, sp = _start("h_yuna", drop=_TAILS)
    _ready(H, body, _ramp("#6aa4cc", "#94c4e4", "#b6dbf0"), _ramp("#1f3d60", "#2d5278", "#3c6894"))
    M.jacket(H, body, "#f5f2ea", hem=H.j["hip"].z - 0.10, split=60, trim_color="#e0362f")
    sl = M.sleeves(H, body, "#f5f2ea")
    M.armband(H, body, "L", "#e0362f", cross="#ffffff", over=sl)
    M.ponytail(H, body, sp["hair"][1], length=0.17, thick=0.034, low=True)
    _belt(H, body, "#1f3d60", "#f4f4f4", 0.030, pad=0.034)
    M.belt_pouch(H, body, "#e0362f", side=-1, flap="#ffffff")
    _boots(H, body, H.j["ankle.L"].z + 0.05, "#f4f4f4", cuff="#dcdcdc")
    return H


def h_minjun():
    """Ex firefighter tank: orange turnout coat with reflective bands, navy trousers, yellow hard-hat cap (brow and
    eyes uncovered), heavy gloves, a manhole-cover shield on the left arm."""
    H, body, sp = _start("h_minjun")
    _ready(H, body, _ramp("#2a2a30", "#3a3a42", "#4e4e58"), _ramp("#1a2440", "#26335a", "#34437a"))
    M.jacket(H, body, "#e7741e", hem=H.j["hip"].z - 0.22, split=14, pad=0.026, name="turnout", narrow=0.86,
             bands=(H.j["hip"].z - 0.02, H.j["hip"].z - 0.06, H.j["chest"].z + 0.02), band_color="#dfe6ee")
    M.sleeves(H, body, "#e7741e", bands=(0.55,), band_color="#dfe6ee")
    M.cap(H, body, "#f2c230", brim="#2a2a2a", brim_len=0.10, band="#2a2a2a")
    for S in ("L", "R"):
        _bracer(H, body, S, "#2a2a2a", reach=0.45, trim_color="#d0d0d0")
    M.shield(H, body, "L", "#4b515c", rim="#2b2f36", boss="#c9c9c9", R=0.21)
    _belt(H, body, "#2b2a28", "#9a9a9a", 0.042, pad=0.040)
    _boots(H, body, H.j["knee.L"].z - 0.22, "#2b2a28")
    return H


def h_sora():
    """Assassin: black bomber jacket with violet edges, hood, fitted dark pants, violet belt, thigh straps with knives.
    No face mask: the face stays fully visible."""
    H, body, sp = _start("h_sora", drop=None)
    _ready(H, body, _ramp("#0c0b12", "#17161f", "#25242f"), _ramp("#0d0c12", "#1d1c28", "#2c2b3a"), hood=True)
    VB.drop_material(body, "Bottoms")  # the base skirt balloons: fitted dark tights instead
    _cut_tops_below(body, H.j["hip"].z)
    M.jacket(H, body, "#15141c", hem=H.j["hip"].z + 0.005, split=8, trim_color="#8a5cff", pad=0.024, narrow=0.9)
    M.sleeves(H, body, "#15141c", bands=(0.42,), band_color="#8a5cff")
    _belt(H, body, "#2a2838", "#8a5cff", 0.024, pad=0.036)
    for S in ("L", "R"):
        M.tights(H, body, S, "#24222f")
        M.thigh_strap(H, body, S, "#2a2838", knife="#c8c8d8")
    _boots(H, body, H.j["ankle.L"].z + 0.10, "#101014")
    return H


def h_taeyang():
    """Factory engineer fire mage: orange coveralls, black tank top, welding goggles on the forehead, tool belt,
    burn-proof gloves."""
    H, body, sp = _start("h_taeyang")
    _ready(H, body, _ramp("#8a3f12", "#d8702a", "#f09048"), _ramp("#8a3f12", "#d8702a", "#f09048"))
    M.vest(H, body, "#171717", pad=0.020)
    M.goggles(H, body, strap="#2a2a2a", lens="#e0a030", lift=0.092)
    _belt(H, body, "#3a2a1e", "#8a8a8a", 0.046, pad=0.030)
    M.belt_pouch(H, body, "#4a3424", side=-1)
    M.belt_pouch(H, body, "#4a3424", side=1, flap="#3a2a1c")
    for S in ("L", "R"):
        _bracer(H, body, S, "#2b2b2b", reach=0.40, trim_color="#ffa040")
    _boots(H, body, H.j["ankle.L"].z + 0.08, "#3b2a1e")
    return H


def h_eunbi():
    """Shaman exorcist: white short jacket with a red goreum ribbon, dark long skirt, talismans on a cord, bell
    bracelet, long straight hair."""
    H, body, sp = _start("h_eunbi", drop=_TAILS)
    _ready(H, body, _ramp("#e6e0d2", "#f2ede2", "#fbf8f0"), _ramp("#101018", "#1a1c28", "#262a3a"))
    cz = H.j["chest"].z
    M.jacket(H, body, "#f2efe6", top=H.j["neck"].z - 0.03, hem=H.j["hip"].z + 0.02, split=0, trim_color="#c8282c")
    M.sleeves(H, body, "#f2efe6")
    M.ribbon(H, body, "#c8282c", z=cz - 0.04)
    _belt(H, body, "#c8282c", "#e8c060", 0.030, pad=0.040)
    G.robe_skirt(H, body, "#1d2236", hem=H.j["knee.L"].z + 0.02, flare=1.2, trim_color="#c8282c", wave=0.0,
                 name="skirt", narrow=True)
    G.talismans(H, body, paper="#f4ecd8", ink="#b02a2a", n=5)
    M.bracelet(H, body, "L", "#c9a24a", bell="#e8c060")
    return H


def h_gunwoo():
    """MMA berserker: sleeveless black compression top, red boxing shorts, white bandaged forearms, buzz cut, chain."""
    H, body, sp = _start("h_gunwoo", drop="all")
    G.drop_where(body, "Tops", lambda co, bone: G.part_of(bone) in ("upper_arm", "forearm"))
    G.drop_where(body, "Bottoms", lambda co, bone: co.z < H.j["knee.L"].z + 0.02)
    _ready(H, body, _ramp("#0a0a0c", "#17171b", "#26262c"), _ramp("#8a1c1c", "#b82a2a", "#d83a3a"))
    _buzz(H, body, "#1d1b1f")
    for S in ("L", "R"):
        _bracer(H, body, S, "#efefef", reach=0.70)
    M.neck_beads(H, body, "#c9ced6", n=24, r=0.0045, chain=True, span=62)
    M.armband(H, body, "R", "#e0362f")
    _belt(H, body, "#111111", "#c8c8c8", 0.034)
    return H


def h_hana():
    """Idol ice mage: white-and-ice-blue stage jacket with silver trim, short pleated skirt, star hairpin, knee boots,
    headset mic."""
    H, body, sp = _start("h_hana")
    _ready(H, body, _ramp("#c8d6e6", "#eef7ff", "#ffffff"), _ramp("#c8d6e6", "#dbe8f5", "#eef6ff"))
    M.jacket(H, body, "#eef7ff", hem=H.j["hip"].z - 0.10, split=26, trim_color=SILVER)
    M.sleeves(H, body, "#eef7ff", bands=(0.50,), band_color=SILVER)
    _belt(H, body, "#7fb4e8", SILVER, 0.030, pad=0.034)
    G.robe_skirt(H, body, "#bfe0ff", hem=H.j["hip"].z - 0.20, flare=1.2, trim_color=None, wave=0.03, name="skirt")
    M.star_pin(H, body, "#ffd76a", side=-1.0)
    M.headset(H, body, "#2c3340", cups="#eef7ff", mic="#c8d2dc")
    _boots(H, body, H.j["knee.L"].z + 0.04, "#e8f2ff", cuff=SILVER)
    return H


def h_siwoo():
    """High-school sniper: navy blazer with a crest, loosened tie, white shirt, grey slacks, headphones round the neck."""
    H, body, sp = _start("h_siwoo")
    _ready(H, body, _ramp("#c8cacd", "#e4e5e8", "#ffffff"), _ramp("#4a4f58", "#6d727b", "#8a9099"))
    M.jacket(H, body, "#1f2c4e", hem=H.j["hip"].z - 0.12, split=12, trim_color="#c8a040")
    M.sleeves(H, body, "#1f2c4e")
    _belt(H, body, "#1a1a1a", "#c8c8c8", 0.030, pad=0.034)
    M.badge(H, body, GOLD, pad=0.03, x=-0.07)
    M.tie(H, body, "#7a1f2a", length=0.17, loosen=0.035)
    M.neck_headphones(H, body, "#2c2f36", cups="#3a3f4a")
    return H


def h_mirae():
    """Inquisitor: long white military coat with gold buttons and a cross, black gloves, peaked cap, knee boots,
    golden braid."""
    H, body, sp = _start("h_mirae", drop=_TAILS)
    _ready(H, body, _ramp("#c8bfae", "#e6dfd0", "#f6f2e8"), _ramp("#1a1a20", "#26262e", "#33333c"))
    hem = H.j["knee.L"].z + 0.02
    coat = M.jacket(H, body, "#f3efe4", hem=hem, split=6, flare=0.0, trim_color=GOLD, pad=0.024, name="coat",
                    narrow=0.88)
    M.sleeves(H, body, "#f3efe4", bands=(0.96,), band_color=GOLD)
    hz, cz = H.j["hip"].z, H.j["chest"].z
    _belt(H, body, "#15151b", GOLD, 0.030, pad=0.036, z=hz + 0.06)
    M.buttons(H, body, [cz - 0.02, cz - 0.10, hz + 0.02], GOLD, x=-0.035, pad=0.036)
    M.buttons(H, body, [cz - 0.02, cz - 0.10, hz + 0.02], GOLD, x=0.035, pad=0.036)
    G.pendant(H, [body, coat], cz - 0.06, color=GOLD, size=0.05, shape="cross")
    M.cap(H, body, "#f3efe4", brim="#14141a", brim_len=0.10, band=GOLD)
    for S in ("L", "R"):
        _bracer(H, body, S, "#16161c", reach=0.28)
    M.braid(H, body, "#f0d080", side=-1.0)
    _boots(H, body, H.j["knee.L"].z + 0.06, "#15151b")
    return H


def h_jaehyun():
    """Doctor healer: white doctor coat over teal scrubs, stethoscope, ID badge, rimless glasses, neat short hair."""
    H, body, sp = _start("h_jaehyun")
    _ready(H, body, _ramp("#2a7a78", "#2f8f8c", "#3aa6a2"), _ramp("#2a7e7b", "#33938f", "#3fa8a4"))
    M.jacket(H, body, "#f5f6f8", hem=H.j["hip"].z - 0.20, split=12, trim_color="#3aa6a2")
    sl = M.sleeves(H, body, "#f5f6f8")
    _belt(H, body, "#2a2f3a", "#c8d0dc", 0.030, pad=0.034)
    M.armband(H, body, "L", "#e0362f", cross="#ffffff", over=sl)
    M.stethoscope(H, body, "#3a3f4a")
    M.badge(H, body, "#3aa0ff", pad=0.03, x=-0.07)
    M.glasses(H, body, "#c8d0dc", lens="#d8f0ff", style="rimless")
    return H


def h_dana():
    """Ex-marine guardian: camouflage jacket with rolled sleeves, plate carrier, knee pads, combat boots, short
    ponytail, red beret."""
    H, body, sp = _start("h_dana")
    _ready(H, body, _ramp("#3a4128", "#4b5a36", "#5f6e44"), _ramp("#363b2a", "#4a5036", "#5e6544"))
    jk = M.jacket(H, body, "#4f5b36", hem=H.j["hip"].z - 0.05, split=0, pad=0.024)
    M.camo(jk, ["#4f5b36", "#6b5a3a", "#2e3523", "#8a7a55"], scale=1.0)
    G.edge_trim(jk, "#b8242c", 0.010)
    M.sleeves(H, body, "#4f5b36")
    _belt(H, body, "#2a2a22", "#8a8a8a", 0.034, pad=0.032, z=H.j["hip"].z - 0.02)
    M.vest(H, body, "#2b3024", pad=0.052, pockets=2, plates="#363c2c", open_front=0)
    for S in ("L", "R"):
        M.knee_pads(H, body, S, "#2b3024")
    _boots(H, body, H.j["ankle.L"].z + 0.13, "#262a22", cuff="#1a1d17")
    M.ponytail(H, body, sp["hair"][1], length=0.12, thick=0.028, low=True)
    M.beret(H, body, "#b8242c", tilt=-14.0, shift=0.22)
    return H


def h_iseul():
    """Guild scout captain: green field poncho over a utility vest, cargo pants, binoculars, bandana, fingerless
    gloves."""
    H, body, sp = _start("h_iseul")
    _ready(H, body, _ramp("#3a3f2c", "#4f5a3a", "#64714a"), _ramp("#3a4128", "#4d5634", "#606b40"))
    M.vest(H, body, "#5a4a2e", pockets=4, pad=0.022, trim_color="#c4422f")
    hz, nz = H.j["hip"].z, H.j["neck"].z
    _belt(H, body, "#2a2a2a", "#8a8a8a", 0.032, pad=0.012, z=hz - 0.02)
    M.jacket(H, body, "#4e6e3a", hem=hz + 0.06, top=nz - 0.005, split=60, flare=0.0, pad=0.030, name="poncho", seg=48)
    M.binoculars(H, body, "#2a2a2a")
    M.headband(H, body, "#c4422f", width=0.030)
    for S in ("L", "R"):
        _bracer(H, body, S, "#2a2a2a", reach=0.25)
    return H


def h_haneul():
    """S-rank dark mage: long black coat with a violet lining and high collar, black gloves, silver hair, floating
    violet runes, dress shoes."""
    H, body, sp = _start("h_haneul")
    _ready(H, body, _ramp("#14121c", "#1e1b2a", "#2a2638"), _ramp("#0f0d16", "#1a1824", "#27242f"))
    cy = G.torso_ring(body, H.j["chest"].z)[0]
    M.jacket(H, body, "#15121e", hem=H.j["knee.L"].z - 0.04, split=12, flare=0.0, pad=0.026, lining="#6a3ad0",
             trim_color="#8a5cff")
    M.sleeves(H, body, "#15121e")
    _belt(H, body, "#1b1828", "#c8b0ff", 0.034, pad=0.036)
    M.high_collar(H, body, "#15121e", lining="#6a3ad0")
    for S in ("L", "R"):
        _bracer(H, body, S, "#0c0b10", reach=0.28)
    G.orbs(H, ["#9a5cff", "#c79cff", "#6a3ad0"], radius=0.32, size=0.042)
    _boots(H, body, H.j["ankle.L"].z + 0.035, "#101014")
    return H


def h_bora():
    """Bodyguard: black suit with the jacket open, red tie, sunglasses on the head, earpiece, leather gloves."""
    H, body, sp = _start("h_bora")
    _ready(H, body, _ramp("#c8c4bc", "#e6e2da", "#f6f4ef"), _ramp("#0c0c10", "#16161c", "#22222a"))
    M.jacket(H, body, "#16161a", hem=H.j["hip"].z - 0.10, split=26, pad=0.024, trim_color="#b8242c")
    M.sleeves(H, body, "#16161a")
    _belt(H, body, "#111114", "#c8c8c8", 0.030, pad=0.034)
    M.tie(H, body, "#b8242c", length=0.22)
    M.sunglasses(H, body, frame="#111111", lens="#101015")
    M.earpiece(H, body, "#2a2a2a", coil="#2a2a2a")
    for S in ("L", "R"):
        _bracer(H, body, S, "#2a1a1a", reach=0.25)
    _boots(H, body, H.j["ankle.L"].z + 0.03, "#111114")
    return H


def h_youngsu():
    """Temple monk exorcist, dressed as a styled long coat: olive coat with gold edges and a belt, a cream vest
    under it (visible through the front opening), prayer beads, straw sandals, shaved head, wooden moktak on the belt."""
    H, body, sp = _start("h_youngsu", drop="all")
    _ready(H, body, _ramp("#6e7074", "#8c8e93", "#a6a8ad"), _ramp("#5e6064", "#76787d", "#8c8e93"))
    hz, knee = H.j["hip"].z, H.j["knee.L"].z
    M.vest(H, body, "#e6dcc4", pad=0.018, open_front=0, trim_color="#a8783a")
    M.jacket(H, body, "#3e4a2c", hem=knee - 0.02, split=62, flare=0.1, pad=0.026, trim_color="#c9a050", narrow=0.9)
    M.sleeves(H, body, "#3e4a2c")
    _belt(H, body, "#2a1d12", "#c9a050", 0.050, pad=0.040)
    M.neck_beads(H, body, "#5a3a22", n=15, r=0.0072)
    M.bracelet(H, body, "R", "#5a3a22")
    _boots(H, body, H.j["ankle.L"].z + 0.03, "#c9a95b", cuff="#c9a95b")
    cy, rx, ry = G.torso_ring(body, H.j["hip"].z)
    H.add("hips", ellipsoid("moktak", V((-(rx + 0.040), cy - 0.02, hz - 0.04)), (0.040, 0.045, 0.032),
                              "#9a6a3a", seg=12, rings=6))
    return H


def h_rina():
    """Magical-girl mage: pink-and-white frilled jacket with a ribbon, small pink cape, pleated skirt, knee boots,
    star hairpin, twin tails kept."""
    H, body, sp = _start("h_rina")
    _ready(H, body, _ramp("#e88ac0", "#ff9ad0", "#ffc4e4"), _ramp("#ffb8dc", "#ffd0ea", "#fff0f8"))
    cz, nz = H.j["chest"].z, H.j["neck"].z
    M.jacket(H, body, "#ff9ad0", hem=H.j["hip"].z - 0.02, split=0, trim_color="#ffffff", pad=0.024)
    M.sleeves(H, body, "#ff9ad0", bands=(0.92,), band_color="#ffffff")
    M.frill(H, body, "#fff3fa", z=nz - 0.04, pad=0.03)
    M.ribbon(H, body, "#ff5aa8", z=cz - 0.04)
    _belt(H, body, "#ff5aa8", "#fff07a", 0.030, pad=0.034)
    G.robe_skirt(H, body, "#ffd6ee", hem=H.j["knee.L"].z + 0.02, flare=1.08, trim_color="#ffffff", wave=0.03,
                 name="skirt", narrow=True)
    G.capelet(H, body, "#ffb0d8", depth=0.12, trim_color="#ffffff")
    M.star_pin(H, body, "#fff07a", side=1.0)
    _boots(H, body, H.j["knee.L"].z + 0.05, "#ff6fb0", cuff="#ffffff")
    return H


def h_jun():
    """Courier rider assassin: black hooded windbreaker with neon stripes, motorcycle gloves, helmet clipped to the
    belt, crossbow on the back, delivery bag."""
    H, body, sp = _start("h_jun")
    _ready(H, body, _ramp("#0c0c0f", "#17171b", "#26262c"), _ramp("#15151a", "#1f1f26", "#2a2a33"), hood=True)
    M.jacket(H, body, "#111114", hem=H.j["hip"].z - 0.10, split=0, pad=0.024, trim_color="#e6ff1a")
    M.sleeves(H, body, "#111114", bands=(0.35, 0.62), band_color="#e6ff1a")
    for S in ("L", "R"):
        _bracer(H, body, S, "#17171a", reach=0.35, trim_color="#e6ff1a")
    M.helmet_on_hip(H, body, "#f0f0f0", side=1)
    M.crossbow(H, body, "#2a2a2e")
    M.bag(H, body, "#e6ff1a", strap="#111114", side=-1)
    _belt(H, body, "#1a1a1e", "#e6ff1a", 0.030, pad=0.034)
    return H


HUNTER_BUILDERS = {
    "h_dohyun": h_dohyun, "h_seoa": h_seoa, "h_jiho": h_jiho, "h_yuna": h_yuna, "h_minjun": h_minjun,
    "h_sora": h_sora, "h_taeyang": h_taeyang, "h_eunbi": h_eunbi, "h_gunwoo": h_gunwoo, "h_hana": h_hana,
    "h_siwoo": h_siwoo, "h_mirae": h_mirae, "h_jaehyun": h_jaehyun, "h_dana": h_dana, "h_iseul": h_iseul,
    "h_haneul": h_haneul, "h_bora": h_bora, "h_youngsu": h_youngsu, "h_rina": h_rina, "h_jun": h_jun,
}
assert set(HUNTER_BUILDERS) == {h["id"] for h in spec.HUNTERS}, "HUNTER_BUILDERS must cover spec.HUNTERS"
