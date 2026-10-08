"""새벽 길드 staff: the five NPCs of the Dawn Guild hub, on the textured VRoid route (lib_anime + garments_staff).

Same ids, rig and NPC clips (Idle, Walk, Talk) as the chibi NPCs they replace, so TownWorld.cs needs no change:
  innkeeper    medic (윤 간호사 · 의무실): pink scrubs, nurse cap, clipboard, first-aid cross
  shopkeeper   hunter market (박 사장 · 헌터 마켓): teal shirt, khaki work vest, backwards cap, calculator
  smith        workshop (곽 장인 · 장비 공방): grey work shirt, dark apron, welding cap, beard, big wrench
  guild_clerk  reception (서 주임 · 접수처): navy blazer, red tie, lanyard, tablet
  elder        guild master (백 길드장 · 길드장실): black three-piece suit (open jacket), silver hair, cane

Run:  blender -b --factory-startup -P Blender/npcs/generate_staff.py -- [id ...]   (no ids = all five)
Writes Assets/_Game/Resources/Art/NPCs/<id>/<id>.fbx + <id>_tex/*.png, previews to Blender/preview/.
"""
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path[:0] = [os.path.join(HERE, "..", d) for d in ("lib_anime", "lib", "lib_humanoid")]

import anime_body as AB  # noqa: E402
import garments as G  # noqa: E402
import garments_staff as S  # noqa: E402
import heroes_anime as HA  # noqa: E402
import vroid_base as VB  # noqa: E402
from produce import produce  # noqa: E402

MALE, FEMALE = HA.MALE, HA.FEMALE
DROP_F = HA._EARS + HA._TAILS  # the female sample's twin tails and ears are dropped: short, practical hair


def _male_base(H, height, hair, brow=None):
    return S.staff_body(H, MALE, height, hair=hair,
                        iris=[(0.0, "#2a1a10"), (0.5, "#6a4426"), (1.0, "#d8a86a")],
                        brow=brow or [(0.0, "#2a1c14"), (1.0, "#5a3e2a")])


def _female_base(H, height, hair, iris, brow):
    return S.staff_body(H, FEMALE, height, hair=hair, iris=iris, brow=brow, drop=DROP_F, island=VB.female_ears)


def innkeeper():
    """윤 간호사 · 의무실: light pink scrubs, nurse cap, clipboard, first-aid cross."""
    H = AB.AnimeHumanoid("innkeeper")
    body = _female_base(H, 1.58,
                        hair=[(0.0, "#4a2a1c"), (0.5, "#8a5232"), (0.85, "#c98a5a"), (1.0, "#f3c9a0")],
                        iris=[(0.0, "#2a1a10"), (0.5, "#6a4a2a"), (1.0, "#c8a070")],
                        brow=[(0.0, "#3a2216"), (1.0, "#7a4a30")])
    VB.gradient_map(body, "Tops", [(0.0, "#e89bb0"), (0.5, "#f8c5d2"), (1.0, "#ffe6ee")])
    VB.gradient_map(body, "Bottoms", [(0.0, "#c77d92"), (0.6, "#e8a6b8"), (1.0, "#f6cfd9")])
    H.build_rig()
    H.add_weighted(body)
    S.boots(H, body, "#ffffff", cuff="#f0a0b8")
    G.mitre(H, body, color=S.WHITE, trim_color=None, height=0.075, emblem=S.RED)
    S.cross_badge(H, body, S.RED)
    S.clipboard(H, "L")
    return H


def shopkeeper():
    """박 사장 · 헌터 마켓: plain teal shirt, khaki work vest, khaki trousers, brown work boots, cap backwards."""
    H = AB.AnimeHumanoid("shopkeeper")
    body = _male_base(H, 1.72, hair=[(0.0, "#241a16"), (0.5, "#4a3228"), (0.85, "#7a5a48"), (1.0, "#b08a70")])
    G.drop_where(body, "Tops", lambda co, bone: G.part_of(bone) in G.TORSO + ("head", "thigh")
                    or (G.part_of(bone) == "shoulder" and co.z > H.j["neck"].z - 0.03))
    VB.gradient_map(body, "Tops", [(0.0, "#1f8f86"), (0.5, "#2fb3a6"), (1.0, "#7fe0d4")])
    VB.gradient_map(body, "Bottoms", [(0.0, "#8a7050"), (0.6, "#c9ad7e"), (1.0, "#e6d2a8")])
    H.build_rig()
    H.add_weighted(body)
    S.boots(H, body, "#4b3424", cuff=None)
    S.shirt(H, body, "#2fb3a6")
    S.suit_vest(H, body, "#c9ad7e", "#8a7050", width=34)
    S.cap(H, body, "#e0593f", "#c44a33", back=True)
    S.calculator(H, "R")
    return H


def smith():
    """곽 장인 · 장비 공방: grey work shirt, dark leather apron, welding cap, short beard, big wrench."""
    H = AB.AnimeHumanoid("smith")
    body = _male_base(H, 1.74, hair=[(0.0, "#2e2019"), (0.5, "#4a3226"), (0.85, "#6a4a38"), (1.0, "#9a7a62")],
                      brow=[(0.0, "#2a1c14"), (1.0, "#4a3428")])
    G.drop_where(body, "Tops", lambda co, bone: G.part_of(bone) in G.TORSO + ("head", "thigh")
                    or (G.part_of(bone) == "shoulder" and co.z > H.j["neck"].z - 0.03))
    VB.gradient_map(body, "Tops", [(0.0, "#3a3f4a"), (0.5, "#5c6370"), (1.0, "#8a92a0")])
    VB.gradient_map(body, "Bottoms", [(0.0, "#1f2530"), (0.6, "#2d3440"), (1.0, "#414a5a")])
    H.build_rig()
    H.add_weighted(body)
    S.boots(H, body, "#4b3424", cuff="#2a1c14")
    S.shirt(H, body, "#5c6370")
    S.cap(H, body, "#2f3440", "#2f3440", back=False)  # welding cap, lens-less
    hz = H.j["hip"].z
    S.apron(H, body, "#3c3a3f", trim="#b5651d", hem=hz - 0.50, width=24)
    S.wrench(H, "R")
    return H


def guild_clerk():
    """서 주임 · 접수처: navy blazer, red tie, blue lanyard with ID, tablet, navy skirt and heels."""
    H = AB.AnimeHumanoid("guild_clerk")
    body = _female_base(H, 1.62,
                        hair=[(0.0, "#1a1830"), (0.5, "#3a3560"), (0.85, "#5a5488"), (1.0, "#8a84b8")],
                        iris=[(0.0, "#1a2a4a"), (0.5, "#3a6aa8"), (1.0, "#a8d4ff")],
                        brow=[(0.0, "#1a1830"), (1.0, "#4a4870")])
    G.drop_where(body, "Tops", lambda co, bone: G.part_of(bone) in G.TORSO + ("head", "thigh"))
    VB.gradient_map(body, "Tops", [(0.0, "#16243d"), (0.5, S.NAVY), (1.0, S.NAVY_L)])
    VB.gradient_map(body, "Bottoms", [(0.0, "#141c2e"), (0.6, S.NAVY), (1.0, S.NAVY_L)])
    H.build_rig()
    H.add_weighted(body)
    S.boots(H, body, "#15161c", cuff=None, top_off=0.10)
    S.skirt(H, body, S.NAVY, S.NAVY_L, hem=H.j["hip"].z - 0.24, width=90)
    S.jacket(H, body, S.NAVY, S.NAVY_L)
    S.scarf_tie(H, body, S.RED, tail=0.20)
    S.id_lanyard(H, body)
    S.tablet(H, "L")
    return H


def elder():
    """백 길드장 · 길드장실: black three-piece suit with the jacket open over a gold-edged waistcoat, silver hair, cane."""
    H = AB.AnimeHumanoid("elder")
    body = _male_base(H, 1.70, hair=[(0.0, "#8a909c"), (0.5, "#c6cad4"), (1.0, "#f2f4f8")],
                      brow=[(0.0, "#8a8f9a"), (1.0, "#c8ccd6")])
    G.drop_where(body, "Tops", lambda co, bone: G.part_of(bone) in G.TORSO + ("head", "thigh")
                    or (G.part_of(bone) == "shoulder" and co.z > H.j["neck"].z - 0.03))
    VB.gradient_map(body, "Tops", [(0.0, S.BLACK), (0.5, S.BLACK_L), (1.0, "#3a3e4a")])
    VB.gradient_map(body, "Bottoms", [(0.0, "#101116"), (0.6, "#1b1c22"), (1.0, "#2a2c33")])
    H.build_rig()
    H.add_weighted(body)
    S.boots(H, body, "#0e0e12", cuff=None)
    S.suit_vest(H, body, "#101116", S.GOLD, width=34)
    jacket = S.jacket(H, body, S.BLACK, S.BLACK)
    # Open jacket: the front panel between the lapels is removed so the waistcoat shows.
    hz = H.j["hip"].z
    AB.drop_faces(jacket, lambda co: co.y < -0.02 and abs(co.x) < 0.07 and co.z > hz + 0.10)
    S.cane(H, "R")
    return H


BUILDERS = dict(innkeeper=innkeeper, shopkeeper=shopkeeper, smith=smith, guild_clerk=guild_clerk, elder=elder)

if __name__ == "__main__":
    args = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
    for name in args or list(BUILDERS):
        produce(name, BUILDERS[name], npc=True)
