# Artifacts — inventory and briefs

Written 2026-10-12 (planner). The data has **no "artifact" or "relic" type** (no match in `Resources/Data/*.json` or
`Scripts/`). Interpretation used here: the objects a player *finds and activates* in a gate dungeon, plus the rare relic
items they bring home. Sources: `DungeonWorld.cs:82-104` (marker → piece), `ArtLibrary.cs:19` (`PropPath`),
`AbyssProjectSetup.cs:110-116` (required art), `UIArtwork.cs:66-68` (icons), `Blender/ui/render_icons.py`,
`equipment.json` (43 accessories), `items.json` (65 items), `dungeon.json` (39 floors).

## 1. Inventory

### A. Dungeon artifacts — runtime 3D, Tripo (41 generations)
| piece | marker / count in all floors | placement (DungeonWorld) | per tileset? | special parts |
|---|---|---|---|---|
| chest | `T` 317 | `AgainstWall(…, 1.3)`, faces the cell centre (−Y front) | yes (10) | `Lid` hinged on the back top edge, opens −105° about X (`_kit_interact_a.py:141-163`, `common_b.make_lid`) |
| lore_stone | `N` 98 | `AgainstWall(…, 1.35)` | yes (10) | none; readable at 1.35 m eye height |
| spring | `H` 26 | `AgainstWall(…, 1.1)` | yes (10) | `LightAnchor*` empties (lights added by `EnvironmentProcessor`) |
| warp | `W` 25 | cell centre | yes (10) | `Spot_warp` empty |
| key_item | `K` 85 | `Props/Common/key_item`, 0.8 m up, against a wall, proximity scale bob (`DungeonWorld.cs:252-268`) | **one shared** | none; 27 different key names share it (`점검구 열쇠`, `병동 출입증`, `옥좌의 열쇠` …) |

Chest, lore_stone, spring and warp briefs already exist per tileset in `environment.md` (rows `chest`, `lore_stone`,
`spring`, `warp`); they move from the prop batches to the artifact batches here. trap, torch, foe_marker, decor and
overlays stay props (`environment.md`).

### B. Structural set pieces — see `environment_tiling.md`
`door_locked` (L 85), `boss_gate` (B 13), `stairs_up/down` (39/38). Plain `door` is never spawned.

### C. Relic items — icon only (no runtime 3D)
Items, accessories and armour exist as FBX under `Art/Props/{Items,Equipment}` only to be rendered into 512² icons
(`Blender/ui/render_icons.py` → `Resources/Icons/{Items,Gear}`; the UI loads sprites, `UIArtwork.cs:66-68`). Rare
pieces with a story and their current (shared) model:
| id | name | rarity/tier | current model (shared) | why it is a relic |
|---|---|---|---|---|
| acc_abyss_heart | 심연의 심장 | 3/8 | acc_flame_amulet | heart left by the Abyss Lord |
| acc_crystal_crown | 수정 왕관 | 3/8 | acc_hero_emblem | crafted from the lord's crown shard + gate stones |
| acc_dragon_fang | 해룡의 송곳니 | 3/6 | acc_flame_amulet | Leviathan fang |
| acc_kraken_eye | 크라켄의 눈 | 3/3 | acc_shadow_amulet | frost kraken eye |
| acc_lich_phylactery | 리치의 성물함 | 3/5 | acc_clarity_earring | lich's soul vessel |
| acc_sphinx_riddle | 스핑크스의 수수께끼 | 3/4 | acc_hero_emblem | riddle tablet of the flame sphinx |
| acc_ribbon | 여신의 리본 | 3/8 | acc_awake_bell | top-tier status ward |
| acc_hero_emblem | 영웅의 문장 | 3/5 | own | four gate stones joined |
| acc_guardian_ring | 수호의 반지 | 3/4 | own | guild guardian ring |
| job_medal | 각성의 증표 (item) | 2 | own | 1st awakening token |
| master_seal | 초월의 인장 (item) | 3 | own | 2nd awakening token |
| trial_emblem | 붉은 게이트 문장 (item) | 2 | own | Red Gate boss proof |
| lord_crown | 군주의 왕관 (item) | 2 | own | Abyss Lord horn-crown shard |
| abyss_crystal | 심연 마석 (item) | 2 | own | last-gate black stone |
| enhance_stone_abyss | 심연 강화석 (item) | 2 | own | T6–T8 upgrade stone |
| phoenix_plume | 소생 앰플(상급) (item) | 2 | own | full revive (id says plume, data says ampoule) |

**Pipeline for C: ChatGPT web image → icon directly, no Tripo.** Reasons: they are only ever seen as 512² sprites;
a Tripo model costs 90 and `render_icons.py` cannot render it anyway (it requires a `Col` vertex-colour layer on every
mesh, `render_icons.py:201`; Tripo output is UV-textured). Icon contract: 512×512 PNG, transparent background (ask GPT
for a plain flat background and cut it out if transparency fails), object centred with 8 % margin, same 3/4 lighting
and toon style as the existing icons in `Resources/Icons/Gear`; overwrite `Icons/Gear/<id>.png` /
`Icons/Items/<id>.png` in place (keep `.meta`). Per-row icons already exist (115 gear, 64 item sprites), so no data
change is needed even where the 3D model is shared.

### D. Not used at runtime — skip
`Props/Common/chest_common`, `chest_rare`, `gold_pile`, `campfire`, `banner_party` are only listed as required in
`AbyssProjectSetup.cs:115`; no spawn site. Leave them procedural.

## 2. Briefs

### key_item (shared, 1 Tripo, small prop: 3–6k tris, 1k texture)
"A chunky modern gate key: a short brass key blade joined to a rounded plastic keycard tag, the tag holds a small
violet gate-crystal chip set into a recess, a thick split ring through the tag. Reads as a key and an access pass at
once. Upright, front three-quarter view." Pivot: centre of mass (it floats 0.8 m up), front −Y. No text on the tag.

### Per-tileset chest / lore_stone / spring / warp
Use the `environment.md` rows verbatim (they are already data-checked), with these artifact rules on top:
- **chest**: image shows the chest **closed, straight front three-quarter**, lid clearly separate by a visible seam,
  hinge side at the back. Blender: split the lid at the seam into `Lid` with the origin on the back top hinge line;
  body footprint ≤ 1.6 × 0.9 m, height ≤ 1.0 m (subway reference 1.5 × 0.84 × 0.92); back within 0.7 m of the origin
  (placed 1.3 m from the cell centre, the wall face is at 2.0).
- **lore_stone**: height 1.6–2.1 m, footprint ≤ 1.1 × 0.9 m; the readable face is −Y; glowing parts are an emissive
  colour band only (no text, no runes; abstract stroke shapes).
- **spring**: footprint ≤ 1.6 × 0.9 m, back within 0.9 m; re-create the `LightAnchor*` empties at the glowing water.
- **warp**: footprint ≤ 3.0 m Ø, centred, flat base at z = 0 (stepped on); `Spot_warp` at the centre.
- Small-prop budget: 3–6k tris, 1k texture (importer cap for dungeon props).

### Relic icons (GPT web only; 16 images)
Frame: "Generate FOUR separate standalone square images… one game item icon for a present-day Seoul hunter RPG:
<brief>. Chunky stylised toon 3D render, single object, three-quarter view, soft studio light, plain flat light-grey
background, centred with margins, no hands, text, letters or numbers, 1:1."
| id | brief |
|---|---|
| acc_abyss_heart | a dark crystal heart in a steel cage pendant, violet core glow, short chain loop |
| acc_crystal_crown | **restyled (no crown, hunter direction)**: a crystal circlet-visor shard set in a steel band, gate-stone chips |
| acc_dragon_fang | a huge sea-serpent fang capped in teal steel, cord loop |
| acc_kraken_eye | a frosted glass sphere with a slit pupil, set in a ring mount, ice-blue |
| acc_lich_phylactery | a small sealed soul canister: steel ends, frosted glass tube with a teal wisp inside |
| acc_sphinx_riddle | a palm-sized sandstone tablet with abstract carved grooves (no glyphs), gold corner caps |
| acc_ribbon | a white satin ribbon charm with a small pearl clasp, soft glow at the knot |
| acc_hero_emblem | a round guild emblem badge with four coloured gate-stones set at the compass points |
| acc_guardian_ring | a thick steel ring with a blue guild-shield stone |
| job_medal | a bronze guild hunter medal on a short ribbon, blank embossed sun shape |
| master_seal | a heavy silver signet seal with a violet gate-stone handle, blank face |
| trial_emblem | a red-enamel badge with a crack of red rift light across it |
| lord_crown | **restyled**: a broken black horn fragment with a gold band, violet cracks |
| abyss_crystal | a black faceted crystal leaking violet light at the cracks |
| enhance_stone_abyss | a dark hexagonal upgrade stone with a violet glowing core seam |
| phoenix_plume | a premium revive ampoule: thick glass vial with a flame-orange liquid, gold cap and a feather-shaped clip |

Open decisions for main: the two crown restyles (names stay); whether icon replacement may skip Tripo (recommended).

## 3. Credits and order
- A: 40 per-tileset pieces + key_item = **41 × 90 = 3,690** (no rig). Run per tileset right after that tileset's
  tiling batch so each dungeon is verified complete (README).
- B: counted in `environment_tiling.md`.
- C: **0 credits** (ChatGPT web only); one batch of 16 images, can run any time.
- VERIFY per artifact batch: Unity capture of a chest open (lid swing and pivot), a lore stone read, spring light, warp
  spot, and the key bob at 1-1-style placement against the new walls.
