"""Promoted job outfits (tier 2 and 3) for the four heroes.

Job tree (each hero keeps their own face, hair and eyes; only the outfit changes):
  warrior -> knight -> paladin       | warrior -> berserker -> warlord
  mage    -> elementalist -> archmage | mage -> warlock -> abyssal
  archer  -> sniper -> divine_archer | archer -> ranger -> shadow_stalker
  cleric  -> priest -> saint         | cleric -> exorcist -> inquisitor
"""
import anime_body as AB
import body as B
import garments as G
import vroid_base as VB
from heroes_anime import _female_feet, hero_body
from humanoid import V, cyl, ring, shade

GOLD = G.GOLD
JOB_TREE = {
    "warrior": ("knight", "berserker"), "knight": ("paladin",), "berserker": ("warlord",),
    "mage": ("elementalist", "warlock"), "elementalist": ("archmage",), "warlock": ("abyssal",),
    "archer": ("sniper", "ranger"), "sniper": ("divine_archer",), "ranger": ("shadow_stalker",),
    "cleric": ("priest", "exorcist"), "priest": ("saint",), "exorcist": ("inquisitor",),
}
JOB_NAMES_KO = {
    "warrior": "전사", "knight": "기사", "paladin": "성기사", "berserker": "광전사", "warlord": "워로드",
    "mage": "마법사", "elementalist": "원소술사", "archmage": "대마도사", "warlock": "흑마법사", "abyssal": "심연술사",
    "archer": "궁수", "sniper": "저격수", "divine_archer": "신궁", "ranger": "레인저", "shadow_stalker": "그림자 추적자",
    "cleric": "사제", "priest": "신관", "saint": "성녀", "exorcist": "퇴마사", "inquisitor": "심판관",
}


def _grad(dark, mid, light, top="#ffffff"):
    return [(0.0, dark), (0.5, mid), (0.85, light), (1.0, top)]


def _belt(H, body, z, color="#5a3a26", buckle=GOLD, pad=0.03, width=0.040):
    bx, by = AB.section(body, z)
    return B.belt(H, z, color, buckle, width=width, r=bx + pad, sy=(by + pad) / (bx + pad))


# ================================================================ warrior line (male, auburn)
# Tier 2 changes the armour family; tier 3 adds a signature silhouette (wings, horned helm) you read at a glance.

def _plate_knight(job, steel, trim, cloth, tabard, cape, cape_inner, sleeves, emblem=GOLD, crest=None, wings=0.0,
                  long_cape=0.55, helm=True):
    H = AB.AnimeHumanoid(job)
    body = hero_body(H, "warrior")
    j = H.j
    hz = j["hip"].z
    G.drop_where(body, "Tops", lambda co, bone: G.part_of(bone) in G.TORSO + ("head", "shoulder", "thigh"))
    VB.gradient_map(body, "Tops", sleeves)
    VB.gradient_map(body, "Bottoms", _grad("#16151a", "#2c2a33", "#4a4854", "#6a6874"))
    VB.drop_material(body, "Shoes")
    H.build_rig()
    H.add_weighted(body)
    G.greaves(H, body, steel, trim_color=trim, top=j["knee.L"].z + 0.02)
    tunic = G.robe_skirt(H, body, cloth, hz - 0.30, flare=1.5, trim_color=trim, split=40, top=hz + 0.02, name="tunic")
    plate = G.cuirass(H, body, steel, trim_color=trim)
    G.tassets(H, body, steel, trim_color=trim, length=0.15, plates=4)
    G.gorget(H, body, steel, cloth=cloth, trim_color=trim)
    for S in ("L", "R"):
        G.pauldron(H, body, S, steel, trim_color=trim, lames=2, size=1.05)
        G.bracer(H, body, S, steel, trim_color=trim, reach=0.6)
    belt = _belt(H, body, hz + 0.03, "#4a3020", trim)
    G.tabard(H, body, tabard, hz - 0.36, back=False, emblem=emblem, width=18, over=[tunic] + belt, trim_color=trim)
    if wings:
        G.wings(H, body, "#fbf8f0", tip="#f2c75a", span=wings)
        G.circlet(H, body, trim, gem="#7fe8ff", wings=1.0)
    else:
        G.cape(H, body, cape, hz - long_cape, inner=cape_inner, wave=0.08, over=[tunic] + plate + belt, trim_color=trim)
    if helm:
        G.helm(H, body, steel, trim_color=trim, crest=crest)
    return H


def knight():
    """기사: full steel plate with gold trims, crested helm, navy tunic, blue tabard and long blue cape."""
    return _plate_knight("knight", "#9aa9be", GOLD, "#22325a", "#2a4a9a", "#2a4a9a", "#18284e",
                         _grad("#141c30", "#24345a", "#34497a", "#4a6496"), crest="#2a4a9a")


def paladin():
    """성기사: white-gold holy plate, white tabard, great feathered wings and a winged circlet."""
    return _plate_knight("paladin", "#ece6d6", GOLD, "#f2ede0", "#fbf8ef", "#fbf8ef", "#d8cfb8",
                         _grad("#6a5e48", "#b8a888", "#e2d6bc", "#fff8e8"), emblem="#d8a030", wings=1.0, helm=False)


def _berserker(job, iron, trim, fur, leather, cape=None, horn=0.0, heavy=False, sash="#9a2a26"):
    H = AB.AnimeHumanoid(job)
    body = hero_body(H, "warrior")
    j = H.j
    hz = j["hip"].z
    G.drop_where(body, "Tops", lambda co, bone: G.part_of(bone) in G.TORSO + ("head", "shoulder", "thigh") or
                 G.part_of(bone) in ("upper_arm", "forearm", "hand"))
    VB.gradient_map(body, "Bottoms", _grad("#1c120e", "#3a2418", "#5a3a26", "#7a5438"))
    VB.drop_material(body, "Shoes")
    H.build_rig()
    H.add_weighted(body)
    G.greaves(H, body, iron, trim_color=trim, top=j["knee.L"].z - 0.02)
    if heavy:
        plate = G.cuirass(H, body, iron, trim_color=trim)
    else:
        plate = G.cuirass(H, body, leather, trim_color=None, lames=0)
    G.tassets(H, body, leather if not heavy else iron, trim_color=trim, length=0.20, plates=5)
    G.capelet(H, body, fur, depth=0.11, trim_color=None, jag=0.04, teeth=22, wave=0.0, over=plate)
    G.pauldron(H, body, "L", iron, trim_color=trim, lames=2, size=1.25 if heavy else 1.1, spikes=3, horn=horn)
    if heavy:
        G.pauldron(H, body, "R", iron, trim_color=trim, lames=2, size=1.25, spikes=3, horn=horn)
    for S in ("L", "R"):
        G.bracer(H, body, S, iron, trim_color=trim, reach=0.75, flare=1.35)
    belt = _belt(H, body, hz + 0.03, sash, trim, width=0.07)
    if cape:
        G.cape(H, body, cape, hz - 0.55, inner=shade(cape, 0.6), wave=0.10, over=list(plate) + belt, trim_color=None,
               jag=0.07)
    if horn:
        G.helm(H, body, iron, trim_color=trim, horns=1.2, horn_color="#e6dcc4")
    return H


def berserker():
    """광전사: bare arms, leather jerkin, wolf-fur collar, one spiked iron pauldron, crimson war sash."""
    return _berserker("berserker", "#5c616e", "#b0884a", "#7a6450", "#4a3020")


def warlord():
    """워로드: black-iron heavy armour, horned helm, horned spiked pauldrons, fur and a torn crimson cape."""
    return _berserker("warlord", "#34373f", "#c0392b", "#4a3c34", "#2a1e1a", cape="#8e1c24", horn=1.0, heavy=True,
                      sash="#2a1a12")


# ================================================================ mage line (female, lavender twin tails)

def _mage(job, dress, robe=None, cap=None, cap_trim=GOLD, hat=None, hat_band="#b0864a", gem="#5fd0ff", hood=None,
          circ=None, cape=None, glow=None, boots="#3e2a24", pendant=None, horns=0.0, long=True, orbs=None,
          rune=None, book=None):
    H = AB.AnimeHumanoid(job)
    body = hero_body(H, "mage")
    j = H.j
    hz = j["hip"].z
    VB.gradient_map(body, "Tops", dress)
    H.build_rig()
    H.add_weighted(body)
    _female_feet(H, body, boots)
    over = []
    if robe:
        # The robe replaces the dress skirt (a robe over the flared dress balloons into a bell).
        G.drop_where(body, "Tops", lambda co, bone: G.part_of(bone) in ("hips", "thigh") and co.z < hz - 0.02)
        r = G.robe_skirt(H, body, robe, 0.10 if long else hz - 0.40, flare=1.3, trim_color=cap_trim, split=0,
                         top=hz + 0.06, name="robe", wave=0.05)
        over.append(r)
    belt = _belt(H, body, hz + 0.06, "#3a2420", GOLD, pad=0.012, width=0.03)
    if cap:
        c = G.capelet(H, body, cap, depth=0.12, trim_color=cap_trim, inner=shade(cap, 0.7))
        over.append(c)
    if cape:
        G.cape(H, body, cape, 0.18, inner=shade(cape, 0.6), wave=0.08, over=over + belt, trim_color=cap_trim,
               jag=0.06 if job in ("warlock", "abyssal") else 0.0)
    if hat:
        G.witch_hat(H, body, hat, band=hat_band, gem=gem, height=1.25 if job == "archmage" else 1.0)
    if hood:
        G.hood(H, body, hood, trim_color=cap_trim, peak=0.07)
    if circ:
        G.circlet(H, body, circ, gem=gem, wings=0.8 if horns == 0 else 0.0)
    if horns:
        hc, half, top = G.skull_box(H, body)
        for s_ in (1, -1):
            p0 = V((hc.x + s_ * half.x * 0.6, hc.y + half.y * 0.1, top - 0.03))
            pts = [p0, p0 + V((s_ * 0.04, 0.03, 0.06 * horns)), p0 + V((s_ * 0.03, 0.10, 0.12 * horns)),
                   p0 + V((s_ * 0.0, 0.15, 0.13 * horns))]
            from humanoid import sweep
            hn = sweep("horn", pts, [(0.020, 0.020), (0.014, 0.014), (0.007, 0.007), (0.001, 0.001)], "#2a2034", seg=10)
            G.metal(hn, "#3a2c4a", shine=0.4)
            H.add("head", hn)
    if pendant:
        G.pendant(H, [body] + over, j["chest"].z - 0.02, color=GOLD, gem=pendant, shape="medallion", size=0.04)
    if glow:
        dom = AB.dominant_bones(body)
        cy, rx, ry = G.torso_ring(body, hz + 0.06, dom=dom)
        G.glow_band(H, "hips", (hz + 0.075, cy, rx + 0.014, ry + 0.014), glow)
    if orbs:
        G.orbs(H, orbs)
    if rune:
        where, col = rune
        if where == "back":
            cy = j["chest"].y
            G.rune_ring(H, V((0, cy + 0.26, j["chest"].z + 0.04)), (0, 1, 0), 0.30, col, bone="chest", ticks=20)
        else:
            hc, half, top = G.skull_box(H, body)
            G.rune_ring(H, V((hc.x, hc.y + half.y + 0.10, hc.z + 0.03)), (0, 1, 0.15), 0.17, col, bone="head", ticks=12)
    if book:
        G.grimoire(H, body, cover=book, glow=glow or gem, side=-1)
    return H


def elementalist():
    """원소술사: teal top, long white skirt-robe, teal capelet, winged circlet and four elemental orbs."""
    return _mage("elementalist", _grad("#0e2a30", "#1e5a64", "#3a8a92", "#7ac8cc"), robe="#f2f4f6",
                 cap="#1e5a64", circ=GOLD, gem="#5fd0ff", orbs=("#ff6a2a", "#7ad8ff", "#ffe066", "#7af0a0"))


def archmage():
    """대마도사: royal blue and white, tall white-gold hat, high capelet, long cape and a great magic circle behind."""
    return _mage("archmage", _grad("#0c1838", "#1c3470", "#2e50a0", "#6a8ad0"), robe="#14244e",
                 cap="#f6f4ee", hat="#f2efe6", hat_band=GOLD, gem="#8ae0ff", cape="#1c3470", pendant="#8ae0ff",
                 rune=("back", "#8ae0ff"))


def warlock():
    """흑마법사: black-violet dress, peaked dark hood, torn short cape, violet glow and a chained grimoire."""
    return _mage("warlock", _grad("#0e0a14", "#241a34", "#3a2a52", "#5a4a78"), cap=None, hood="#1e1628",
                 cap_trim="#8a5ac8", cape="#1e1628", pendant="#b06aff", long=False, glow="#b06aff", book="#3a1e4a")


def abyssal():
    """심연술사: black robe with cyan runes, long horns, an abyss sigil behind the head, torn long cape."""
    return _mage("abyssal", _grad("#060408", "#141020", "#241c36", "#3a3050"), robe="#0e0a16",
                 cap="#141020", cap_trim="#5ae8ff", cape="#0e0a16", pendant="#5ae8ff", glow="#5ae8ff", horns=1.3,
                 gem="#5ae8ff", rune=("head", "#5ae8ff"))


# ================================================================ archer line (male, blond)

def _archer(job, top, pants, leather, cap=None, cap_trim=GOLD, jag=0.0, coat=None, scarf=None, circ=None,
            cape=None, quiver="#71492f", bracer=None, hood_up=None, armour=None, hat=None, wings=None, mask=None):
    """armour = (vest colour, tunic colour): the hoodie keeps only its sleeves and a fitted vest + tunic go on."""
    import math
    H = AB.AnimeHumanoid(job)
    body = hero_body(H, "archer")
    j = H.j
    hz, nz = j["hip"].z, j["neck"].z
    if armour:
        G.drop_where(body, "Tops", lambda co, bone: G.part_of(bone) in G.TORSO + ("head", "shoulder", "thigh"))
    elif hood_up:
        G.strip_hood(body, H)
    VB.gradient_map(body, "Tops", top)
    VB.gradient_map(body, "Bottoms", pants)
    VB.drop_material(body, "Shoes")
    H.build_rig()
    H.add_weighted(body)
    btop = j["knee.L"].z - 0.05
    for S in ("L", "R"):
        AB.boot(H, body, S, btop, leather, cuff_color=shade(leather, 1.18))
    AB.drop_faces(body, lambda co: co.z < btop - 0.03)
    over = []
    if armour:
        vest, tunic = armour
        over.append(G.robe_skirt(H, body, tunic, hz - 0.20, flare=1.35, trim_color=cap_trim, split=50, top=hz + 0.02,
                                 name="tunic"))
        over += G.cuirass(H, body, vest, trim_color=cap_trim, lames=0, pad=0.014)
        G.gorget(H, body, vest, cloth=tunic, trim_color=cap_trim)
    if coat:
        c = G.robe_skirt(H, body, coat, j["knee.L"].z - 0.02, flare=1.35, trim_color=cap_trim, split=150,
                         top=hz + 0.02, name="coat_tails", wave=0.03, over=over)
        over.append(c)
    belt = _belt(H, body, hz + 0.02, shade(leather, 0.8), GOLD, pad=0.016 if armour else 0.012)
    over += belt
    if cap:
        over.append(G.capelet(H, body, cap, depth=0.13, trim_color=cap_trim, jag=jag, teeth=14,
                              inner=shade(cap, 0.7), over=over))
    if scarf:
        G.scarf(H, body, scarf, tail=0)
    if circ:
        G.circlet(H, body, circ, gem="#8ae0ff", wings=1.0)
    if cape:
        G.cape(H, body, cape, hz - 0.45, inner=shade(cape, 0.65), wave=0.08, over=over, trim_color=cap_trim,
               jag=0.05 if jag else 0.0, arc=70)
    if wings:
        G.wings(H, body, wings[0], tip=wings[1], span=0.8, folded=0.3)
    for S in ("L", "R"):
        G.bracer(H, body, S, bracer or leather, trim_color=cap_trim if bracer else None, reach=0.6)
    if hood_up:
        G.hood(H, body, hood_up, trim_color=cap_trim if job == "shadow_stalker" else None, peak=0.06)
    if hat:
        G.brim_hat(H, body, hat[0], band=hat[1], feather=hat[2])
    if mask:
        G.mask(H, body, mask, trim_color=cap_trim if job == "shadow_stalker" else None)
    # Quiver on the back with fletchings.
    cy = j["chest"].y
    back = AB.section(body, j["chest"].z)[1]
    p0, p1 = V((-0.07, cy + back + 0.07, hz + 0.10)), V((-0.17, cy + back + 0.12, nz + 0.10))
    H.add("chest", cyl("quiver", p0, p1, 0.042, 0.050, quiver, seg=16))
    H.add("chest", ring("quiver_rim", p1, p1 - p0, 0.049, 0.006, cap_trim or GOLD, seg=18, minor=5))
    d = (p1 - p0).normalized()
    for k in range(5):
        a = math.radians(72 * k)
        off = V((math.cos(a) * 0.022, math.sin(a) * 0.022, 0))
        q = p1 + off + d * 0.05
        H.add("chest", cyl("arrow", p1 + off - d * 0.05, q, 0.004, 0.004, "#c9b48a", seg=6))
        H.add("chest", cyl("fletch", q - d * 0.01, q + d * 0.035, 0.012, 0.004, "#e8e0cc" if k % 2 else "#a83a2a",
                           seg=4))
    return H


def sniper():
    """저격수: fitted leather vest over a dark shirt, long coat, feathered marksman hat, red scarf."""
    return _archer("sniper", _grad("#1a1612", "#3a3028", "#5a4a3c", "#7a6650"), _grad("#141210", "#2a2622", "#46403a"),
                   "#4a3426", armour=("#5a3e2a", "#3a2a1e"), coat="#2e2218", scarf="#a8322c", cap_trim="#c09a5a",
                   hat=("#2e2218", "#a8322c", "#c8323a"))


def divine_archer():
    """신궁: white-gold light armour, feathered wings, winged circlet, gold bracers."""
    return _archer("divine_archer", _grad("#8a8070", "#d8d0c0", "#f4f0e6", "#ffffff"),
                   _grad("#4a4238", "#8a7e6a", "#c0b49a", "#e8dcc0"), "#e8e0d0", armour=("#f4f0e4", "#fbf8f0"),
                   cap_trim=GOLD, circ=GOLD, bracer="#e8c060", quiver="#f0e8d8", wings=("#fbf8f0", "#f2c75a"))


def ranger():
    """레인저: forest-green hood up, leafy jagged capelet, scarf, leather bracers."""
    return _archer("ranger", _grad("#0c1a0e", "#1e3a22", "#2e5a32", "#4a7a48"), _grad("#1a140c", "#3a2c1c", "#5a4630"),
                   "#5a3e28", cap="#2e5a2a", cap_trim=None, jag=0.04, scarf="#6a8a3a", hood_up="#24481f")


def shadow_stalker():
    """그림자 추적자: black leather armour, violet-edged hood and face mask, torn capelet and cape."""
    return _archer("shadow_stalker", _grad("#06060a", "#16141e", "#262234", "#3e3852"),
                   _grad("#060608", "#121218", "#22222c"), "#1e1a24", armour=("#1a1622", "#100e16"), cap="#16121e",
                   cap_trim="#8a5ac8", jag=0.05, cape="#16121e", bracer="#3a3646", quiver="#2a2230",
                   hood_up="#16121e", mask="#100e16")


# ================================================================ cleric line (female, pink bob)

def _cleric(job, dress, robe=None, cap="#fbf6ea", cap_trim=GOLD, stole=None, circ=GOLD, gem="#ff7a8a", hood=None,
            halo=False, cape=None, plate=None, boots="#6e4a34", pendant_gem="#ff5a6e", mitre=None, wings=None,
            hat=None, charms=False):
    H = AB.AnimeHumanoid(job)
    body = hero_body(H, "cleric")
    j = H.j
    hz = j["hip"].z
    VB.gradient_map(body, "Tops", dress)
    H.build_rig()
    H.add_weighted(body)
    _female_feet(H, body, boots)
    over = []
    if robe:
        # The robe replaces the dress skirt, so it can hang as a slim A-line from the hips.
        G.drop_where(body, "Tops", lambda co, bone: G.part_of(bone) in ("hips", "thigh") and co.z < hz - 0.02)
        over.append(G.robe_skirt(H, body, robe, 0.08, flare=1.3, trim_color=cap_trim, split=0, top=hz + 0.06,
                                 name="robe", wave=0.05))
    if plate:
        over += G.cuirass(H, body, plate, trim_color=cap_trim, lames=2, pad=0.012)
        for S in ("L", "R"):
            G.pauldron(H, body, S, plate, trim_color=cap_trim, lames=1, size=0.85)
            G.bracer(H, body, S, plate, trim_color=cap_trim, reach=0.6)
    belt = _belt(H, body, hz + 0.06, "#6a4630", GOLD, pad=0.012, width=0.028)
    over += belt
    c = G.capelet(H, body, cap, depth=0.13, trim_color=cap_trim, inner=shade(cap, 0.88), over=over)
    over.append(c)
    if stole:
        G.stole(H, body, stole, length=0.42 if robe else 0.30, emblem=GOLD, start=j["shoulder.L"].z - 0.13)
    if cape:
        G.cape(H, body, cape, 0.15 if robe else hz - 0.45, inner=shade(cape, 0.75), wave=0.08, over=over,
               trim_color=cap_trim)
    if wings:
        G.wings(H, body, wings[0], tip=wings[1], span=0.9)
    if hood:
        G.hood(H, body, hood, trim_color=cap_trim, open_front=0.8)
    elif mitre:
        G.mitre(H, body, mitre, trim_color=cap_trim)
    elif hat:
        G.brim_hat(H, body, hat[0], band=hat[1], feather=None, brim=1.1, tilt=4)
    elif circ:
        G.circlet(H, body, circ, gem=gem, z=0.62)
    if halo:
        G.halo(H, body)
    if charms:
        G.talismans(H, body)
    G.pendant(H, [body] + over, j["chest"].z - 0.01, gem=pendant_gem)
    return H


def priest():
    """신관: white dress and full robe with gold hem, red stole, white capelet, tall mitre with a gold cross."""
    return _cleric("priest", _grad("#8a7a68", "#d8ccb8", "#f4ecdc", "#fffaf0"), robe="#fbf8f0", stole="#b3414c",
                   mitre="#fbf8f0")


def saint():
    """성녀: white-gold-sky blue, full robe, white veil hood, halo and great white wings."""
    return _cleric("saint", _grad("#6a8aa8", "#b8d0e6", "#e8f2fa", "#ffffff"), robe="#fdfcf8", cap="#ffffff",
                   stole="#5a8ad0", hood="#ffffff", halo=True, gem="#8ad0ff", pendant_gem="#8ad0ff",
                   wings=("#ffffff", "#bfe0ff"))


def exorcist():
    """퇴마사: black dress, white capelet with silver trim, black hood, paper talismans at the belt."""
    return _cleric("exorcist", _grad("#08080c", "#1a1a22", "#2e2e3a", "#4a4a5a"), cap="#f4f2ee", cap_trim="#b8c4d0",
                   hood="#14141a", gem="#8ad0ff", pendant_gem="#c8d8ff", charms=True)


def inquisitor():
    """심판관: crimson and black, dark steel breastplate and pauldrons, wide-brimmed judge's hat, long crimson cape."""
    return _cleric("inquisitor", _grad("#0c0608", "#24141a", "#3a2028", "#5a3440"), cap="#8e1c24", cap_trim=GOLD,
                   plate="#4a4e5a", cape="#8e1c24", gem="#ff4a4a", pendant_gem="#ff4a4a", hat=("#1a1014", "#8e1c24"))


JOB_BUILDERS = dict(knight=knight, paladin=paladin, berserker=berserker, warlord=warlord,
                    elementalist=elementalist, archmage=archmage, warlock=warlock, abyssal=abyssal,
                    sniper=sniper, divine_archer=divine_archer, ranger=ranger, shadow_stalker=shadow_stalker,
                    priest=priest, saint=saint, exorcist=exorcist, inquisitor=inquisitor)
