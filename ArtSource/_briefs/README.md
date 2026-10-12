# Visual overhaul — brief catalogs, batch plan, pipeline rules

Scope (user, 2026-10-11): replace **all** visual 3D assets with Tripo models: weapons, monsters, dungeon props,
town buildings and props, hunters and NPCs. Credits are no longer the constraint, but the rules stay: **one Tripo
generation per asset and no duplicate work**. Every brief comes from the data rows, not the legacy asset ids (id ≠ object;
see weapons.md). Generated 2026-10-11 by reading `Assets/_Game/Resources/Data/*.json`, `ArtVariants.cs`,
`GearDisplay.cs`, `AbyssArtImporter.cs`, `Blender/environment/**`, `Blender/town/guild.py`, `Blender/npcs/generate_staff.py`.

| file | content | to make |
|---|---|---|
| `weapons.md` | 48 weapon models (no shared rows) | 43 (5 queued today) |
| `enemies.md` | 86 models from 134 rows, plus 3 proposed splits | 83 (+ crystal_cave_lord BLOCKED; slime reuses its existing mesh; 4 done) |
| `hunters.md` | 20 hunters | 18 (h_dohyun exported, h_seoa staged) |
| `npcs.md` | 5 guild staff (+ 3 orphaned villagers) | 5 |
| `environment.md` | 10 tilesets × 15 non-tiling pieces | 145 (2 done; 1 shared foe_marker; guild_street torch = town street_lamp) |
| `town.md` | hub buildings and street props | 35 (15 buildings, 20 props) |
| **total** | | **329 Tripo generations** |
| `skills_vfx.md` (2026-10-12) | 28 shared effect meshes (26 core + 2 optional) mapped onto all 300 skills / 156 presentation rows | 28 |
| `environment_tiling.md` (2026-10-12) | walls, floors, door_locked, boss_gate for 10 tilesets (stairs re-skinned, plain `door` unused) | 60 |
| `artifacts.md` (2026-10-12) | chest / lore_stone / spring / warp per tileset (moved out of the prop batches) + shared key_item; 16 relic icons (image only) | 1 new (key_item) + 16 images |

Decide-later lists (not counted): dungeon floors/walls/doors/stairs/boss gates/arenas (120 pieces), town ground and
roads, string lights, colliders.

## Credits (rough)
Prices seen: image→3D H3.1 Best Quality 55; Retopo Triangle/Smart Mesh 35 at ≤5000, 40 at 10000 (20k price not seen
yet; assume 40–45); Auto Rig 20; export free; free retry on server errors.
| type | per asset | count | subtotal |
|---|---|---|---|
| weapon / small prop (55 + 35) | 90 | 43 + 145 + 20 town props | 18,720 |
| building (55 + ~40) | 95 | 15 | 1,425 |
| enemy, rigged (55 + 35/40 + 20) | 110–115 | 81 | ~9,150 |
| enemy, no rig (magma_slime, sea_urchin) | 90 | 2 | 180 |
| hunter / NPC (55 + 40 + 20) | 115 | 23 | 2,645 |
| **total** | | 329 | **≈ 32,100** + Tripo animation cost (unknown) |
Optional extras: h_seoa regeneration from its data profile (115), 3 villagers (345), one rig retry for crystal_cave_lord
(user said no third paid rig).

## Hunter animation blocker (mapping decision pending)
Runtime clips for hunters: **Idle, Run, Walk, Attack, Cast, Hit, Die, Victory, Guard, Revive** (BattleView.cs uses
Idle/Run/Attack/Skill/Cast/Hit/Die/Guard/Revive; ClipAnimator requires Idle). The Tripo presets found so far cover Idle
and Run; tiles also exist for cast, hit, cheer and walk. A Tripo humanoid preset inventory is running separately.
| runtime clip | Tripo preset | fallback |
|---|---|---|
| Idle | (found) | — |
| Run | (found) | — |
| Walk | walk tile — TBD | |
| Attack | TBD | |
| Cast | cast tile — TBD | |
| Hit | hit tile — TBD | |
| Die | TBD | |
| Victory | cheer tile? — TBD | |
| Guard | TBD | |
| Revive | TBD | |
NPCs need Idle, Walk, Talk. Enemies need Idle (required), Attack, Hit, Die (optional Skill, Cast, Roar). Blob or
failed-rig enemies get those takes from Blender. Hold hunter installs (h_seoa, h_dohyun) until this table is filled.

## Revised batch order (2026-10-12) — monsters, skill VFX, tiling, artifacts

User request 2026-10-12: (1) every regular monster through the pipeline, applied and verified in game; (2) skill
visuals with varied effects and impact (image → Tripo effect meshes, applied in game); (3) walls, floors and artifacts
through image + Tripo, including the former "tiling — decide later" pieces. This section **supersedes the batch table
below from B4 on**; B1–B3 are unchanged (B1, B2 done; B3 images in progress).

### Tracks
- **M — monsters.** 87 models: 10 done or in B3 (4 bosses, festival_pumpkin_king, B3's sewer_rat, horned_rabbit, bat,
  killer_bee, elite_bat). Remaining: **52 regular** (rank 0: 24 Humanoid rig, 23 Other rig, 5 blobs: slime [reuse
  mesh], magma_slime, giant_clam, sea_urchin, chaos_spawn), **19 elite** (11 H, 8 O), **6 boss** (3 H, 3 O), + the
  locker_mimic split; crystal_cave_lord stays blocked. Humanoid-rig monsters get their clips free from the shared
  `Art/HumanoidAnimations` library (`ArtLibrary.cs:113`, with a `HUMANOID` marker). Other-rig creatures need their own
  Idle/Attack/Hit/Die takes from Tripo (budgeted as 3 × text-to-motion 20; **measure on B3's bat first**).
- **V — skill VFX** (`skills_vfx.md`): V0 code hooks (0 credits) then 6 + 10 + 10 (+2 optional) meshes.
- **T — tiling** (`environment_tiling.md`): T0 hooks + Blender script (0 credits), then 6 generations per tileset,
  subway pilot first.
- **A — artifacts** (`artifacts.md`): per tileset chest, lore_stone, spring, warp right after that tileset's T batch;
  shared key_item with the subway pilot; relic icons are images only (0 credits).
- **P — carried-over props/gear/hunters/town**: the superseded table's content (old B4–B31) minus all enemies (now M)
  and minus chest/lore_stone/spring/warp (now A). Runs in its old order whenever credits allow; it is not re-listed here.

### Credit unit costs (seen in Tripo Studio)
generate 55 · retopo 35 · auto rig 20 · text-to-motion 20 per clip. Mesh/prop/tile = 90; humanoid monster = 110;
creature = 110 + 3 clips = 170 (estimate); elite/boss + 5 for the larger retopo.

### Order
| batch | track | assets | credits | gate |
|---|---|---|---|---|
| V0 + T0 | code | H1–H5 (`skills_vfx.md` §6), E-H1 (`environment_tiling.md` §4), `Blender/environment/tripo_tiles.py`; tested with Blender placeholder meshes | 0 | Unity compile + battle and dungeon capture unchanged |
| **B4** | V + M | **VFX-1**: slash_crescent, energy_arrow, energy_orb, impact_crater, shield_dome, light_pillar · **zone-2 humanoids**: sprout, mandragora, goblin, goblin_shaman | 540 + 440 = **980** | V0 passed |
| **B5** | T + A | **subway tiling pilot**: wall_base + floor_base first (180) → VERIFY → wall_accent, floor_accent, door_locked, boss_gate (360); stairs re-skin (0) · **key_item** (90) | **630** | B4 VERIFY |
| B6 | M | mushroom, pixie, scrap_bot, snow_fairy, yeti, penguin_mage, ice_golem (H) + rhino_beetle (first Other creature after B3) | 770 + 170 = 940 | B3 Other-rig result |
| B7 | V | VFX-2: ground_seal, thrust_spike, nova_wave, shadow_tendril, holy_cross, flame_plume, heal_bloom, lightning_bolt, ice_shard, rock_debris | 900 | |
| B8 | A + T | subway chest, lore_stone, spring, warp · verdant_ruins tiling (6) | 360 + 540 = 900 | subway complete after this |
| B9 | M | wisp, sand_scorpion, frost_spider, ice_wolf, jellyfish, coral_crab (O) + magma_slime (blob) | 1,020 + 90 = 1,110 | blob decision D1 |
| B10 | V | VFX-3: tornado_funnel, chain_ring, energy_lance, sword_phantom, feather, crystal_prism, rift_gate, barrier_panel, ice_spike_cluster, vine_coil | 900 | |
| B11 | A + T | verdant artifacts (4) · factory tiling (6) | 900 | |
| B12 | M | cave_mole, lizardman, sand_golem, harpy, scarecrow, skeleton, lich, dark_knight (H) | 880 | |
| B13 | M | flame_elemental, grave_bat, hellhound, fire_drake, phoenix, mimic, ghost, locker_mimic (O) | 1,360 | |
| B14 | A + T | factory artifacts · frost_grotto tiling | 900 | |
| B15 | M | merfolk_guard, temple_guardian, orc, gargoyle, doppelganger (H) + giant_clam, sea_urchin, chaos_spawn (blobs) | 550 + 270 = 820 | D1 |
| B16 | M | mummy_pup, puffer, angler, sea_serpent, siren, void_eye, shadow_beast, nightmare, abyss_worm (O) | 1,530 | **all regular monsters done** |
| B17–B22 | A + T | one per batch: frost arts + cave tiles · cave arts + ember tiles · ember arts + school tiles · school arts + crypt tiles · crypt arts + hospital tiles · hospital arts + guild_street tiles | 6 × 900 | |
| B23 | A + V + icons | guild_street artifacts (360) · VFX-4 optional bite_jaws, meteor_rock (180) · 16 relic icons (0) | 540 | |
| B24 | M | elites H: elite_mushroom, elite_sand_golem, elite_yeti, crystal_horror, elite_scarecrow, elite_skeleton, elite_dark_knight, drowned_knight, high_orc, fallen_angel, void_reaper | ≈ 1,265 | |
| B25 | M | elites O + bosses: elite_rhino_beetle, elite_ice_wolf, elite_coral_crab, elite_hellhound, elite_fire_drake, elite_mimic, turtle_titan, naga_priestess · forest_guardian, boss, abyss_lord, frost_kraken, flame_sphinx, leviathan | ≈ 2,300 | |

Totals for the new tracks: M ≈ 10,600 (regular ≈ 7,100 incl. locker_mimic; elite ≈ 2,700; boss ≈ 870), V 2,520
(2,340 core), T 5,400, A 3,690 → **≈ 22,200**, plus the P track (old estimate ≈ 32,100 minus what is done).

**Budget now:** second account ≈ 3,300. B3 (5 enemies incl. 4 Other-rig creatures, 4 weapons, street lamp) will
take ≈ 1,150–1,400 → **≈ 1,900–2,150 left**, enough for **B4 + B5 (1,610)**. Everything from B6 on needs a top-up or
another account; stop and tell the user before B6.

### VERIFY (after every batch, before the next one starts)
1. Install per the pipeline rules (markers first, GUIDs kept, backups, sidecars, ledger rows with credits).
2. Blender checks: rigged monsters pose a bone and the mesh follows; tiles/meshes pass their validation script.
3. Unity: reimport, compile with zero errors, play the 540×960 capture loop (QA scripts outside the repo):
   - **M**: each new model in a battle (idle, attack, hit, die, scale next to the party) and as a dungeon FOE.
   - **V**: one presentation per touched family + every ULT touched, before/after strips; frame time within 10 %.
   - **T**: corridor, outer corner, T-junction, door closed/open, stairs, boss gate, torch light; seams; frame time
     within 15 % of the procedural build.
   - **A**: chest lid swing and pivot, lore stone, spring light, warp spot, key bob.
4. Sol 6.1 reviews the capture set and the diff summary; main approves. A failure blocks the next batch of that track
   (other tracks may continue).

### Decisions taken by main (2026-10-12; reviewed by Sol 6.1)
- D1: (b) code-driven rigless animator for the five blob models — implemented (IModelAnimator, RiglessBlobAnimator; ArtLibrary.IsRiglessBlob). Unity check pending.
- D2: confirm on the B3 bat (one Other-rig attempt); re-budget after.
- D3: Tripo retopo for every VFX mesh (rule kept).
- D4: floors made with Tripo.
- D5: stairs made with Tripo (environment_tiling.md updated: 8 generations per tileset).
- D6: relic icons straight from ChatGPT transparent images; acc_crystal_crown and lord_crown restyled as modern crown-shaped gear without medieval ornament.
- D7: icons for Tripo-installed weapons/monsters made from the approved candidate image as ChatGPT transparent 512² icons (Sol's Sprite import settings), not by render_icons.py.

### Open decisions as originally listed (superseded by the block above)
- **D1 blob animation** with no Blender-authored takes: slime, magma_slime, giant_clam, sea_urchin, chaos_spawn (and
  any failed Other rig). Options: (a) one Tripo Other-rig attempt each (failed before on slime); (b) a small
  code-driven squash/bob animator for rigless models (CharacterModel/ClipAnimator change); (c) redesign with limbs.
- **D2 creature clip cost**: confirm on B3 whether Tripo animation for Other rigs is text-to-motion (20/clip) or
  presets; re-budget B6+.
- **D3 VFX retopo**: Tripo retopo (35) per mesh as the rules say, or Blender decimation only (saves 980; rule exception).
- **D4 floors**: Tripo relief slab (plan) or texture-only floors (saves 180 per tileset).
- **D5 stairs**: procedural geometry re-skinned (plan, 0 credits) or Tripo.
- **D6 relic icons** straight from ChatGPT images (no Tripo; `render_icons.py` cannot render textured models) and the
  two crown restyles (acc_crystal_crown, lord_crown).
- **D7** `render_icons.py:201` needs a `Col` layer on every mesh: icons of Tripo-installed weapons/monsters will not
  re-render until the icon script supports textures (separate task).

## Batch plan (2026-10-11, superseded from B4 on by the section above; kept for the P-track contents)
Zero-credit work alongside B1: install h_dohyun; decide the h_seoa identity conflict; finish the 5 queued weapons
(sword_bronze, sword_iron, staff_oak, mace_wood, bow_short); add Blender squash takes to the existing slime mesh.
| batch | assets |
|---|---|
| **B1 starting party + hub hero (10)** | h_jiho, h_yuna, h_minjun; bow_hunter, staff_crystal, mace_silver; town guild_hq, gate_portal, guard_booth, fountain |
| **B2 hub staff + buildings (10)** | NPC innkeeper, shopkeeper, smith, guild_clerk, elder; town guild_clinic, guild_market, guild_workshop, notice_board, banner |
| **B3 zone-1 enemies + t3 gear (10)** | sewer_rat, horned_rabbit, bat, killer_bee, elite_bat; sword_knight, bow_composite, staff_sage, mace_blessed; town street_lamp (also guild_street/torch) |
| B4 subway props A (11) | subway decor_2…6, chest, lore_stone, spring, torch, warp, foe_marker |
| B5 subway rest + street props (10) | subway trap, overlay_1, overlay_2; town bench, tree, planter, food_cart, cafe_set, flower_bed, scooter |
| B6 zone-2 enemies (10) | sprout, mandragora, mushroom, elite_mushroom, rhino_beetle, elite_rhino_beetle, goblin, goblin_shaman, pixie, forest_guardian |
| B7 verdant props A (12) | verdant_ruins decor_1…6, chest, lore_stone, spring, torch, warp, foe_marker |
| B8 (12) | verdant trap, overlay_1, overlay_2; h_sora; sword_flamberge, bow_gale, staff_ruby, mace_saint; car_sedan, car_taxi, car_police, car_hatchback |
| B9 zone-3 (10) | magma_slime, scrap_bot, wisp, sand_scorpion, elite_sand_golem; h_taeyang, h_bora; traffic_light, trash_bins, market_crates |
| B10 factory props A (12) | factory decor_2…6, chest, lore_stone, spring, torch, trap, warp, foe_marker |
| B11 (10) | factory overlay_1, overlay_2; town cargo, anvil_barrel, barricade; skyline_building_A…E |
| B12 zone-4 enemies (12) | frost_spider, ice_wolf, elite_ice_wolf, jellyfish, snow_fairy, coral_crab, elite_coral_crab, yeti, elite_yeti, penguin_mage, ice_golem, frost_kraken |
| B13 (10) | h_eunbi; skyline_building_F…H; sword_aegis, sword_ravager, sword_runic, bow_longshot, bow_thornvine, bow_wraith |
| B14 frost props A (12) | frost_grotto decor_1…6, chest, lore_stone, spring, torch, warp, foe_marker |
| B15 (9) | frost trap, overlay_1, overlay_2; elite_hellhound, flame_elemental, cave_mole, lizardman, grave_bat, sand_golem |
| B16 cave props A (12) | cave decor_1…6, chest, lore_stone, spring, torch, warp, foe_marker |
| B17 (10) | cave trap, overlay_1, overlay_2; h_gunwoo; staff_bone, staff_hex, staff_prism, mace_grace, mace_purifier, mace_requiem |
| B18 zone-6 (8) | hellhound, fire_drake, elite_fire_drake, harpy, phoenix, flame_sphinx; h_hana, h_youngsu |
| B19 ember props A (12) | ember_caverns decor_1…6, chest, lore_stone, spring, torch, warp, foe_marker |
| B20 (11) | ember trap, overlay_1, overlay_2; mimic, locker_mimic, elite_mimic, scarecrow, elite_scarecrow, festival_pumpkin_king, ghost; h_siwoo |
| B21 school props A (12) | school decor_1…6, chest, lore_stone, spring, torch, warp, foe_marker (shared with hospital and guild_street) |
| B22 (11) | school trap, overlay_1, overlay_2; skeleton, elite_skeleton, lich, dark_knight, elite_dark_knight, boss; h_mirae, h_rina |
| B23 crypt props A (12) | haunted_crypt decor_1…6, chest, lore_stone, spring, torch, warp, foe_marker |
| B24 (10) | crypt trap, overlay_1, overlay_2; mummy_pup, drowned_knight; h_jaehyun; sword_tidal, bow_tide, staff_coral, mace_pearl |
| B25 hospital props (12) | hospital decor_1…6, chest, lore_stone, spring, torch, trap, warp |
| B26 (10) | hospital overlay_1, overlay_2; turtle_titan, puffer, merfolk_guard, naga_priestess, giant_clam, angler, sea_serpent, sea_urchin |
| B27 (9) | siren, temple_guardian, leviathan; h_dana, h_jun; sword_void, bow_void, staff_void, mace_judgment |
| B28 zone-11 (10) | high_orc, orc, void_eye, gargoyle, shadow_beast, nightmare, doppelganger, fallen_angel, crystal_horror; h_iseul |
| B29 guild_street props (12) | guild_street decor_1…6, chest, lore_stone, spring, trap, warp, overlay_1 |
| B30 (10) | guild_street overlay_2; void_reaper, chaos_spawn, abyss_worm, abyss_lord; h_haneul; sword_conqueror, sword_dawn, sword_holy_avenger, bow_heavens |
| B31 t8 gear (8) | bow_nightfall, bow_star, staff_abyss_eye, staff_arcanum, staff_starlight, mace_dawn, mace_seraph, mace_verdict |
Coverage check: 31 batches, 329 assets, each asset in exactly one batch. Run B1 as the pilot and check the whole
pipeline end to end before starting B2.

## Open decisions for main (collected from the catalogs)
1. h_seoa: the staged model does not match the data `profile` (hunters.md).
2. Tint families with strong hue shifts (enemies.md conflict 4): light base, base-row tint (ArtVariants.cs:22), or split.
3. Splits: festival_pumpkin_king, crystal_cave_lord (blocked), locker_mimic.
4. Wand scale: 8 `staff_*` wands get the smallest held boost (GearDisplay.cs:16-23); mace_wood is a full staff.
5. Fantasy motifs in tier 5–8 weapon text and a few enemy texts (crown, wings, halo, cape): keep the restyle?
6. Town integration: import the Tripo FBXs inside guild.py (keeps markers and colliders), or spawn in Unity (code).
7. Villagers a/b/c look orphaned (npcs.md).
8. Factory decor_1: the script makes a conveyor, the installed Tripo model is a cabinet. Is the conveyor gone?
9. The 4 Tripo bosses have no `TRIPO` marker in `Art/Enemies/<id>/`. Verify their import settings.

## Pipeline rules (every asset)
1. **Brief → one ChatGPT web request** (chatgpt.com, GPT-6, reasoning Extra High = 4th of 5 stops, checked before
   sending): one prompt asking for **4–6 varied candidates** (pose, proportion, palette, detail within the brief),
   each its own image. Download once (memory: one programmatic download per Chrome tab; combine into a strip if needed).
2. **Main picks** (Haiku may pre-pick against the brief; main has the final say). Criteria: matches the brief and art
   direction, single subject, clean readable silhouette, full body, plain background, no text, attached solid parts;
   humanoids in a symmetric A-pose front view with empty hands.
3. **One Tripo Studio generation** (studio.tripo3d.ai, subscription account, never the API) per asset; free retries
   only on server errors. Read the cost on the button and the balance in the header before each paid step, and log
   both.
4. **Retopo: Triangle, Smart Mesh**, always before rig or export. Targets: small enemy/prop 3–6k, normal enemy/NPC
   6–10k, hero/elite/boss/building 10–20k. Texture 2k (1k small props).
5. **Rig** (characters/creatures only): Humanoid (Mixamo) for bipeds, Other for creatures; quadrupeds, serpents and
   blobs are rig risks. Export **FBX** for Unity with the skeleton on. In Blender, pose a bone and check that the mesh
   follows (skin weights); a rig without weights is a failure, so do not install it.
6. **Close the Tripo tab** right after the export downloads (software WebGL pins the CPU).
7. **Marker before FBX/PNG**: create the importer marker **before** copying the FBX or textures into `Assets/`
   (`Assets/_Game/Scripts/Editor/AbyssArtImporter.cs:40-46`): `<name>.tripo` next to a weapon/prop FBX, or a `TRIPO`
   file in a character/enemy folder; add a `HUMANOID` file for Unity Humanoid characters.
8. **GUID preserved**: overwrite the existing `<id>.fbx` in place and keep its `.fbx.meta`; never delete and recreate.
   Keep file names and the folder layout (`Art/<Category>/<id>/<id>.fbx`, `<id>_tex/`, `<id>_mat/`).
9. **Backups**: before overwriting, copy the old FBX/textures to `ArtSource/<category>/<id>/backup_YYYYMMDD/`.
10. **Sidecar**: `ArtSource/<category>/<id>/candidates/prompts.md` with the exact prompt, model/effort check, chat
    URL, candidate files, the pick and why, every Tripo step with credits and balance, retopo tris, the rig check
    result and the export path.
11. Re-add Blender empties and splits listed in environment.md (Lid, trap spikes, LightAnchor/Spot empties) before export.

## Prompt frames (prepend to each brief)
- **Effect mesh**: `skills_vfx.md` §5. **Wall / floor module, door, boss gate**: `environment_tiling.md` §3 step 1.
  **Relic icon**: `artifacts.md` §2.
- **Weapon**: "Generate N separate standalone square images in this one response, each its own image (not a grid):
  one weapon for a present-day Seoul Korean hunter RPG, <brief>. Chunky clean stylised toon 3D game asset, single
  continuous solid object, upright, front three-quarter view, the whole weapon visible with margins, plain light-grey
  background, soft light, no shadow, 1:1. No hands, text, logos, floating effects or thin dangling parts. Vary
  silhouette and palette between images."
- **Monster**: "...one gate monster that will become a 3D model via image-to-3D and be rigged as <biped/creature>:
  <brief>. Chunky, cute, round toon proportions, small socketed glowing eyes, faint blue/violet gate-rift cracks,
  present-day Seoul hunter story. No crown, cape, royal or medieval items, no text. Full body, front view (bipeds in a
  symmetric A-pose with arms clear), plain light-grey background, no shadow, 1:1."
- **Hunter / NPC**: "...adult Korean <role>, slim adult anime proportions about 7 heads (not chibi), <brief>, modern
  Seoul hunter streetwear. Empty hands, no weapon or props, no cape, crown or medieval armour, no text or logos.
  Full-body straight front view, symmetric A-pose, hands clear of the body, feet apart, plain light-grey background,
  generous margins, 1:1, solid attached details, nothing dangling."
- **Prop / building**: "...one environment prop (or building) for a chunky stylised toon 3D game set in present-day
  Seoul: <brief>. Single object, three-quarter view from slightly above, the whole object visible, plain light-grey
  background, no shadow, 1:1, solid attached parts, no readable text (signs as blank panels or abstract strokes)."
