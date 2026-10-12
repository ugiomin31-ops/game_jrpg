# Enemies — brief catalog (data-driven)

Source of truth: `Assets/_Game/Resources/Data/enemies.json` (134 rows), descriptions `text_ko.json` `enemy_desc_<id>`,
zone appearances from `dungeon.json` (encounter_groups, events, foes, boss_group). Model resolution
`ArtVariants.EnemyModel` (`Assets/_Game/Scripts/Logic/Data/ArtVariants.cs:10`: `model` field, else id).
Generated 2026-10-11.

- 134 rows → **86 distinct models** (all 86 have an FBX under `Art/Enemies/<model>/` today, mostly procedural).
- Done (Tripo installed): subway_bat_lord, scrap_colossus, plague_lich, abyss_herald → **4**.
- Proposed splits (new models, see Conflicts): festival_pumpkin_king (concept picked; Tripo task lost),
  crystal_cave_lord (BLOCKED: Tripo "Other" rig failed twice on its quadruped mesh; the user set no third paid rig),
  locker_mimic. Total to make: 86 − 4 + 3 = **85** (84 if crystal_cave_lord stays blocked).
- **Tint rule** (ArtVariants.cs:20-24): only rows whose `model` differs from their id are tinted at runtime (RGBA multiply).
  Rows that own their model ignore their `tint` (the elite tints are expected to be baked into the texture).
  Base texture = what the base row shows untinted, and a multiply can only darken or pull toward the tint colour.
  Column **Base**: `light` = keep the body light and low-saturation (strong hue-shift variants); `authored` = author
  in the row's own colours (no variants, or only the mild warm `· 진` tint 1.0/0.85/0.5).
- **Rig**: `H` = Tripo Humanoid (Mixamo). `O` = Tripo Other. `O!` = Other, rig risk (quadruped, many legs, serpent,
  shell; Other failed on the armadillo and the slime). `none` = blob, no Tripo rig (animate in Blender). Bipeds rig
  reliably, so where the data allows a standing pose the brief asks for one.
- **Size**: S = small 3–6k tris, N = normal 6–10k, E = elite/boss 10–20k.
- **Clips the runtime needs** (`Assets/_Game/Scripts/Runtime/Battle/BattleView.cs`): Idle (required by ClipAnimator),
  Attack, Hit, Die; optional Skill, Cast, Roar. Blob and failed-rig models still need these takes from Blender.
- Art direction for every brief: chunky, cute, round toon gate creature; small socketed glowing eyes; gate-rift glow
  (blue/violet cracks); motifs from the location the gate opened in. No crowns, capes, royal props, medieval armour or
  heraldry. The shared prompt frame is in `README.md`.

## Conflicts found
1. **festival_pumpkin_king** 「축제의 호박왕」 (boss, 7-3) uses `elite_scarecrow` 「허수아비 왕」 tinted. A boss sharing an
   elite's mesh. Split: own model (concept C already picked in `ArtSource/hunter-bosses/festival_pumpkin_king/`).
2. **crystal_cave_lord** 「수정 동굴의 주인」 (boss, 5-3) uses `crystal_horror` 「수정 괴수」 tinted. Split planned; BLOCKED.
3. **locker_mimic** 「사물함 미믹」 uses `mimic` (a treasure chest). A school locker is a different object, so split it.
4. Hue-shift families whose base row is saturated, where a multiply cannot reach the variant colour:
   fire_drake→tide_drake (red→teal), ice_golem→coral_golem (ice→coral pink), magma_slime→oil_slime (lava→oily
   purple-grey), phoenix→inferno_phoenix (fire→violet), wisp→flame/spark/void wisp, killer_bee→frost/ember/syringe bee.
   Options (main decides): (a) light low-saturation base and accept a paler base row; (b) let base rows take a tint too
   (code change at ArtVariants.cs:22); (c) split the worst pair (tide_drake, coral_golem).
5. Rows with their own model plus a non-identity `tint`, which the runtime ignores: all 13 `elite_*` rows and
   `grave_bat`. Bake those colours into the texture.
6. Shared rows that describe different details (mild, keep shared): hellhound's fire mane vs street/crypt/shadow hounds;
   coral_crab (hermit crab) vs abyss_crab (crab); ghost (chain + lantern) vs school_ghost (singing after-school ghost);
   killer_bee vs syringe_bee (syringe stinger); slime vs pill_slime (made of pills). Keep the base design generic enough.
7. Direction tension: lich 「꼬마 리치」 is described with a crown; dark_knight/elite_dark_knight/void_knight/
   drowned_knight/skeleton rows are knights. Briefs keep the identity but drop the crown and heraldry and use rounded,
   hollow "gate armour" shells. Main confirms.
8. No `.tripo` or `TRIPO` marker exists under `Art/Enemies/` (only factory/subway decor_1 and sword_iron have one), yet
   4 bosses are Tripo-installed. Verify that the importer settings for those 4 survive a reimport.

---

## Zone 1 · subway (1-1 2호선 승강장, 1-2 선로 터널, 1-3 변전실)
Motifs: white glossy wall tiles, yellow tactile/safety stripes, line-2 green, turnstile and fluorescent-tube parts, grime.

**slime** · rows: slime 「점액 슬라임」 · sewer_slime 「하수구 슬라임」 [0.62,0.78,0.5] · gold_slime 「황금 슬라임」 [1,0.82,0.32] · metal_slime 「메탈 슬라임」 [0.78,0.82,0.92] · ice_slime 「얼음 슬라임」 [0.55,0.85,1] · crystal_slime 「수정 슬라임」 [0.7,0.6,1] · pill_slime 「알약 슬라임」 [1,0.7,0.8] — at 1-x…9-x — rig none — S — Base **light** (7 variants) — status: Tripo mesh exists in `ArtSource/tripo-test/slime_rigged*` (rig unusable, 4 bones without weights). Reuse that mesh with Blender squash clips; generate new only if main rejects the look.
Brief: A round, glossy, pale-mint jelly drop with a little peak on top, two small socketed eyes and a tiny mouth, a faint subway-tile reflection on the skin.

**sewer_rat** · sewer_rat 「땅굴쥐」 — 1-1, 1-3 — H (stand it up) — S — authored.
Brief: A chubby rat in a yellow safety hard hat standing on its hind legs, big front teeth, little work-glove paws and a striped hi-vis band on its belly.

**horned_rabbit** · horned_rabbit 「뿔토끼」; snow_rabbit 「설원 뿔토끼」 [0.92,0.96,1] — 1-x, 4-x — O! (quadruped) or H if standing — S — Base light (cream/white fur; the snow tint is near-white).
Brief: A round cream bunny with one glowing spiral horn on its forehead, tiny violet rift cracks on the horn, sitting upright on big feet.

**bat** · bat 「동굴 박쥐」; tunnel_bat 「터널 박쥐」 [0.75,0.75,0.85] — 1-1…1-3 — O (the bat lord rig worked) — S — Base light-ish grey-violet.
Brief: A round fuzzy bat-ball with wide leathery wings, small socketed glowing eyes and a tiny fang, wing membranes edged in tunnel-signal green.

**killer_bee** · killer_bee 「킬러비」; frost_bee 「서리벌」 [0.6,0.85,1]; ember_bee 「화염벌」 [1,0.45,0.25]; syringe_bee 「주사벌」 [0.75,0.95,1] — 1-2…9-x — O — S — Base **light** (hue shifts).
Brief: A chubby round wasp with a pale cream body, soft grey stripes, stubby clear wings and a long needle stinger (works for the syringe variant).

**elite_bat** · elite_bat 「밤의 박쥐 군주」 (tint baked [1,0.45,0.45]) — 1-2, 1-3 — O — E — authored red.
Brief: A bigger red-black bat with sharp claws on its wing hands and a ragged subway-ad-poster scrap stuck on one wing (no text), fierce small eyes. No crown or cape.

**subway_bat_lord** · subway_bat_lord 「지하철 박쥐 군주」 — 1-3 boss — **DONE** (Tripo installed).

## Zone 2 · E-rank gate forest (2-1 초록 숲 입구, 2-2 덩굴 회랑, 2-3 고목의 성소)
Motifs: inside the gate, but the gate opened from a Seoul park: ginkgo leaves, trimmed park shrubs, moss, faint rift cracks.

**sprout** · sprout 「풀뿌리」 — 2-x — H — S — authored.
Brief: A small walking tree spirit with a stump body, two root legs, twig arms and a ginkgo-leaf tuft on top.

**mandragora** · mandragora 「만드라고라」 — 2-x — H — S — authored.
Brief: A screaming root creature with a pale radish body, a leafy top and wide open mouth, standing on forked root legs.

**mushroom** · mushroom 「독버섯」; poison_mushroom 「독버섯」 [0.72,0.45,0.95]; ghost_mushroom 「유령 버섯」 [0.7,0.9,0.95] — 2-x, 7-x — H — S — Base **light** (cream cap and stem, pale spots).
Brief: A stubby walking mushroom with a big round cap, little stem legs and arms, spore puffs as solid bumps.

**elite_mushroom** · elite_mushroom 「독왕 버섯」 (baked [0.72,0.45,1]) — 2-2 — H — E — authored purple.
Brief: A large purple poison mushroom boss-ling with a wide drooping cap and toxic cloud bulbs fused round its base. No crown: use a ring of small mushroom caps instead.

**rhino_beetle** · rhino_beetle 「장수풍뎅이」; lava_beetle 「용암 장수풍뎅이」 [1,0.42,0.22]; iron_beetle 「강철 풍뎅이」 [0.72,0.78,0.86] — 2-x, 3-x, 6-x — O! (6 legs) — S/N — Base **light** (pale bronze shell).
Brief: A chunky rhinoceros beetle with a big glossy shell and one thick horn, short stubby legs.

**elite_rhino_beetle** · elite_rhino_beetle 「강철 투구왕」 (baked [0.6,0.75,1]) — 2-1…2-3 — O! — E — authored steel-blue.
Brief: A huge steel-blue beetle with a forked horn and plate-like shell segments shining like brushed metal.

**goblin** · goblin 「고블린」 — 2-x — H — S — authored.
Brief: A small green goblin in an oversized leather cap holding a wooden club fused to its hand, cheeky grin. The E-gate regular.

**goblin_shaman** · goblin_shaman 「고블린 주술사」 — 2-x — H — S — authored.
Brief: A goblin with a feather headdress, a bead necklace and a root-staff fused to its hand, glowing green palm.

**pixie** · pixie 「숲의 요정」; dark_pixie 「어둠 요정」 [0.6,0.4,0.9] — 2-x, 7-x — H — S — Base light.
Brief: A tiny fairy in a flower-petal dress with four rounded wings, holding nothing.

**forest_guardian** · forest_guardian 「고목 수호자」; forest_guardian_ex 「고목 수호자 · 진」 [1,0.85,0.5] — 2-3 boss, R-1 — H — E — authored.
Brief: A massive old-tree guardian with a trunk body, mossy shoulders, root legs, vine arms and a glowing knot-hole face; ginkgo and park-shrub growth on its back.

## Zone 3 · factory (3-1 공장 정문, 3-2 마석 창고, 3-3 폐공장 중앙 라인)
Motifs: rust, yellow-black hazard stripes, bolts, oil, gate-stone crates, sparks.

**magma_slime** · magma_slime 「용암 슬라임」; oil_slime 「기름 슬라임」 [0.42,0.36,0.5] — 3-x — rig none — S — Base: conflict 4 (light orange-cream if shared).
Brief: A molten slime with a cracked dark crust over glowing orange goo, two eyes in the cracks.

**scrap_bot** · scrap_golem 「고철 로봇」 — 3-x — H — N — authored.
Brief: A small boxy robot of factory scrap with a wrench fused to one hand, hazard-stripe chest plate and one big round lens eye.

**wisp** · wisp 「도깨비불」; flame_wisp 「불꽃 도깨비불」 [1,0.55,0.2]; void_wisp 「공허의 도깨비불」 [0.55,0.35,0.95]; spark_wisp 「전기 도깨비불」 [1,0.95,0.45] — 3-x, 6-x, 7-x, 12-x — O (floating) — S — Base **light** (white-blue flame).
Brief: A floating teardrop flame spirit with two small dark eyes and a curling tail, pale white-blue so tints read.

**sand_scorpion** · sand_scorpion 「모래 전갈」; crimson_scorpion 「진홍 전갈」 [1,0.3,0.3] — 3-x, 6-x — O! (8 legs) — S/N — Base light sand.
Brief: A round sandy scorpion with big chunky pincers and a curled tail stinger, rivet-like bumps on its shell.

**elite_sand_golem** · elite_sand_golem 「철광 거인」 (baked [0.95,0.8,0.5]) — 3-x, 5-2 — H — E — authored.
Brief: An iron-ore giant built of ore blocks and steel beams, holding a slab shield fused to one forearm, hazard-stripe paint on the shoulder.

**scrap_colossus** · scrap_colossus 「고철 거상」 — 3-3 boss — **DONE**.

## Zone 4 · D-rank ice gate (4-1 얼음 입구, 4-2 얼음 창고, 4-3 얼음 심장부)
Motifs: cold-storage warehouse: frost, plastic strip curtains, ice blocks, fish-market crates; ice-blue rift glow.

**frost_spider** · frost_spider 「서리 거미」; cave_spider 「동굴 거미」 [0.8,0.62,0.45] — 4-x, 5-x — O! — S — Base light.
Brief: A round spider with chunky legs and ice crystals growing on its back, small cluster of glowing eyes.

**ice_wolf** · ice_wolf 「서리 늑대」 — 4-x — O! (quadruped) — N — authored.
Brief: A fluffy pale-blue wolf with frost-spiked fur on its shoulders and icy breath bulbs at the muzzle.

**elite_ice_wolf** · elite_ice_wolf 「설원의 우두머리」 (baked [0.75,0.9,1]) — 4-1, 4-3 — O! — E — authored.
Brief: A larger alpha frost wolf with a thick ice-crystal mane and a scarred ear, howling stance.

**jellyfish** · jellyfish 「물방울 해파리」; deep_jelly 「심해 해파리」 [0.55,0.45,1] — 4-x, 10-x — O — S — Base light.
Brief: A floating round jellyfish dome with short thick tentacles, a soft inner glow and two dot eyes.

**snow_fairy** · snow_fairy 「눈꽃 요정」 — 4-x — H — S — authored.
Brief: A tiny ice fairy with snowflake wings and a frosty dress, a snowflake wand fused to her hand.

**coral_crab** · coral_crab 「산호 소라게」; abyss_crab 「심연 게」 [0.5,0.35,0.8] — 4-x, 12-x — O! — S/N — Base light coral-cream.
Brief: A round crab carrying a coral-encrusted shell on its back, chunky claws, eyes on short stalks.

**elite_coral_crab** · elite_coral_crab 「거대 산호 집게」 (baked [1,0.55,0.4]) — 4-2, 4-3 — O! — E — authored.
Brief: A boulder-sized coral crab with one oversized slamming claw and a reef growing on its back.

**yeti** · yeti 「꼬마 설인」; chaos_yeti 「혼돈의 설인」 [0.6,0.35,0.8] — 4-x, R — H — N — Base light (white fur).
Brief: A small snowball-round yeti with white shaggy fur, a blue face and stubby horns.

**elite_yeti** · elite_yeti 「설산의 폭군」 (baked [0.75,0.85,1]) — 4-2, 4-3 — H — E — authored.
Brief: A big muscular yeti swinging an icicle club fused to its hand, frost on its shoulders.

**penguin_mage** · penguin_mage 「펭귄 마법사」 — 4-x — H — S — authored.
Brief: A round penguin in a knitted beanie with a snowflake wand fused to its flipper (a modern cold-gear look).

**ice_golem** · ice_golem 「얼음 골렘」; coral_golem 「산호 골렘」 [1,0.55,0.6] — 4-x, 10-x — H — N — Base: conflict 4.
Brief: A chunky golem of stacked cold-storage ice blocks with a glowing blue core.

**frost_kraken** · frost_kraken 「빙해의 크라켄 여왕」; frost_kraken_ex 「빙해의 크라켄 여왕 · 진」 [1,0.85,0.5] — 4-3 boss, R-1 — O! (tentacles) — E — authored.
Brief: A giant pale-blue kraken rising from an ice hole, round head and thick tentacles, frosted spots. No crown: use an icy crest of spikes.

## Zone 5 · underground water vein / crystal cave (5-1 지하 수맥 입구, 5-2 게이트 맥 통로, 5-3 수정 동굴 심장)
Motifs: mining: hard hats, lamps, timber, ore carts, blue-violet crystals.

**elite_hellhound** · elite_hellhound 「오르트로스」 (baked [1,0.55,0.5]) — 5-x, 6-2 — O! (two-headed quadruped) — E — authored.
Brief: A two-headed hound with flame manes on both necks, chunky paws and glowing collar studs.

**flame_elemental** · flame_elemental 「불꽃 정령」 — 5-x — O (floating) — N — authored.
Brief: A fire spirit with obsidian armour chunks floating round a living flame core.

**cave_mole** · cave_mole 「굴착 두더지」 — 5-x — H — S — authored.
Brief: A plump mole in goggles standing upright, huge digging claws, crystal chips stuck to its fur.

**lizardman** · lizardman 「리자드맨」; swamp_lizardman 「늪 리자드맨」 [0.45,0.8,0.5] — 5-x, 9-x — H — N — Base light green-cream.
Brief: An upright lizard warrior with a curved blade and a round shield fused to its hands, scaly tail.

**grave_bat** · grave_bat 「무덤 박쥐」 (own model; its tint is ignored, bake [0.62,0.52,0.85]) — 5-x — O — S — authored violet.
Brief: A gaunt violet bat with a bony skull-shaped face and tattered wings.

**sand_golem** · sand_golem 「모래 골렘」 — 5-x — H — N — authored.
Brief: A golem of packed sand and sandstone blocks with crumbling edges and a glowing seam face.

**crystal_horror** · crystal_horror 「수정 괴수」 — 11-2, 11-3, R-2 — H if possible — E — authored (crystal_cave_lord split away).
Brief: A hulking beast made of crystallised wishes, violet-blue crystal shards jutting from its back, small glowing eyes.

**crystal_cave_lord** (proposed split) · crystal_cave_lord 「수정 동굴의 주인」 — 5-3 boss — **BLOCKED** (Tripo mesh exists in `ArtSource/hunter-bosses/crystal_cave_lord/`, its rig failed twice).

## Zone 6 · C-rank fire gate (6-1 모래 입구, 6-2 용암 협곡, 6-3 불꽃 신전 제단)
Motifs: lava cracks, basalt, sun-temple sandstone; keep it gate-world, with rift glow.

**hellhound** · hellhound 「헬하운드」; crypt_hound 「묘소 사냥개」 [0.55,0.6,0.75]; shadow_hound 「그림자 사냥개」 [0.35,0.3,0.5]; street_hound 「거리의 사냥개」 [0.6,0.6,0.7] — 6-x, 8-x, 11-x, 12-x — O! — N — Base light grey (mane as separate tintable part).
Brief: A lean chunky hound with a short flame-shaped mane and glowing collar studs; the mane should read as fire or smoke.

**fire_drake** · fire_drake 「불꽃 드레이크」; tide_drake 「조류 드레이크」 [0.35,0.8,0.85] — 6-x, 10-x — O! — N — Base: conflict 4.
Brief: A small round dragon with stubby wings and a big head, belly plates, ember breath bulbs at its mouth.

**elite_fire_drake** · elite_fire_drake 「홍염 비룡」 (baked [1,0.35,0.3]) — 6-x — O — E — authored.
Brief: A winged crimson wyvern with wide wings and a flame-tipped tail, chunky toon proportions.

**harpy** · harpy 「하피」; storm_harpy 「폭풍 하피」 [0.7,0.55,1] — 6-x, 9-x — H (winged arms) — N — Base light.
Brief: A bird-woman with feathered wing-arms, talon feet and a feathered crest. Cute, not sexualised.

**phoenix** · phoenix 「새끼 불사조」; inferno_phoenix 「업화의 불사조」 [0.75,0.35,1] — 6-x, R — O — S — Base: conflict 4.
Brief: A round baby firebird with flame-tipped feathers and a big flame tail.

**flame_sphinx** · flame_sphinx 「불꽃 스핑크스」; flame_sphinx_ex 「불꽃 스핑크스 · 진」 [1,0.85,0.5] — 6-3 boss, R-2 — O! (lion body) — E — authored.
Brief: A sandstone-and-gold lion-bodied sphinx with a stylised headdress (no crown), sun-disc emblem on the chest, flame mane.

## Zone 7 · school festival (7-1 축제 교문, 7-2 교실 복도, 7-3 축제 무대)
Motifs: festival lanterns and garlands, lockers, PE uniforms, classroom items.

**mimic** · mimic 「미믹」; golden_mimic 「황금 미믹」 [1,0.8,0.3] — 7-x, 9-x…11-x — O! — S/N — Base light wood-cream.
Brief: A treasure chest monster with a toothy lid-mouth, a lolling tongue and short legs.

**locker_mimic** (proposed split) · locker_mimic 「사물함 미믹」 [0.6,0.72,0.9] — 7-x — H (locker on legs) — N — authored blue.
Brief: A school steel locker come alive: the door is a toothy jaw, vent slots are eyes, stubby legs below, festival garland stuck on top.

**elite_mimic** · elite_mimic 「판도라 상자」 (baked [0.7,0.45,1]) — 7-x — O! — E — authored.
Brief: An ornate violet chest-monster leaking rift light from its lid seams, chained shut but grinning.

**scarecrow** · scarecrow 「호박 허수아비」 — 7-x — H — N — authored.
Brief: A pumpkin-headed scarecrow in a school PE tracksuit stuffed with straw, a crow perched on the shoulder.

**elite_scarecrow** · elite_scarecrow 「허수아비 왕」 (baked [0.55,0.35,0.7]) — 7-2 — H — E — authored.
Brief: A tall purple scarecrow with a harvest scythe fused to its hands and a lantern-lit pumpkin head. No crown.

**festival_pumpkin_king** (proposed split) · festival_pumpkin_king 「축제의 호박왕」 — 7-3 boss — H — E — concept C picked (`ArtSource/hunter-bosses/festival_pumpkin_king/concept.png`); the Tripo task shows "Project not found", so it needs one generation.

**ghost** · ghost 「원령」; phantom 「망령」 [0.5,0.6,1]; school_ghost 「방과 후 유령」 [0.85,0.9,1] — 7-x, 8-x, 9-x — O (floating) — S — Base **light** (white sheet).
Brief: A round sheet-ghost holding a little soul lantern fused to its hand, a short chain loop at the hem.

## Zone 8 · B-rank crypt gate (8-1 묘소 입구, 8-2 납골실, 8-3 묘소 심부)
Motifs: Korean grave-mound and stone-lantern shapes, paper talismans, violet soul fire. No gothic heraldry.

**skeleton** · skeleton 「해골 병사」; skeleton_mage 「해골 마법사」 [0.75,0.6,1] — 8-x — H — N — Base light bone.
Brief: A chunky cute skeleton soldier with a big skull, a simple round helmet and a spear fused to its hand.

**elite_skeleton** · elite_skeleton 「해골 장군」 (baked [0.6,0.65,0.85]) — 8-x, 9-x — H — E — authored.
Brief: A big skeleton commander with a heavy rounded helmet and shoulder guards, a broad blade fused to its hand, violet eye glow.

**lich** · lich 「꼬마 리치」; elder_lich 「고대 리치」 [1,0.85,0.45] — 8-x, 12-x, R — H (floating robe) — S — Base light. The data says a crown; the brief drops it.
Brief: A small floating skull mage in a hooded rag robe, a soul-fire orb in one hand, with a ring of tiny floating bone spikes over the head instead of a crown.

**dark_knight** · dark_knight 「암흑 기사」; void_knight 「공허 기사」 [0.55,0.4,0.95] — 8-x, 12-x, R — H — N — Base light steel-grey.
Brief: A hollow rounded armour shell with violet smoke inside the visor slit and a greatsword fused to its hands. Gate armour, no heraldry.

**elite_dark_knight** · elite_dark_knight 「칠흑의 기사단장」 (baked [0.55,0.5,0.7]) — 8-2, 8-3 — H — E — authored.
Brief: A larger jet-black armour shell with violet battle aura flaring from the helmet crest. No cape.

**boss** · boss 「심연의 전령 모르데인」; boss_ex 「심연의 망령술사 · 진」 [1,0.85,0.5] — 8-3 boss, R-2 — H — E — authored.
Brief: A fallen former S-rank hunter consumed by the abyss: a modern long hunter coat torn into shadow, a cracked hunter-licence badge on the chest, violet void cracks across the face.

## Zone 9 · hospital (9-1 응급실 입구, 9-2 병동 복도, 9-3 격리 병동)
Motifs: mint tiles, IV stands, bandages, red crosses (no text), pills.

**mummy_pup** · bandage_ghost 「붕대 미라」 — 9-x — O! (dog) — S — authored.
Brief: A puppy mummy wrapped in hospital bandages, one eye peeking out, a tiny IV tag on its collar.

**drowned_knight** · drowned_knight 「익사한 기사」 — 9-2, 10-x — H — E — authored.
Brief: A barnacled, water-logged armour shell dripping seawater, a rusty anchor fused to its hands as a weapon.

**plague_lich** · plague_lich 「역병의 리치」 — 9-3 boss — **DONE**.

## Zone 10 · A-rank sunken temple gate (10-1 잠긴 참배로, 10-2 진주 회랑, 10-3 레비아탄의 수문)
Motifs: aquarium glass, coral, pearls, sea-blue rift light.

**turtle_titan** · turtle_titan 「거북 타이탄」 — 10-x — O! — E — authored.
Brief: A giant turtle carrying a tiny mossy shrine on its shell, thick pillar legs.

**puffer** · puffer 「복어 풍선」 — 10-x — O — S — authored.
Brief: An inflated round pufferfish balloon with short spikes and small fins, worried eyes.

**merfolk_guard** · merfolk_guard 「어인 수비병」 — 10-x — H — N — authored.
Brief: A fish-headed soldier with a coral spear and a clam-shell shield fused to its hands.

**naga_priestess** · naga_priestess 「나가 사제」 — 10-2 — O! (serpent tail) — E — authored. The data says a pearl crown; use a pearl hair ornament.
Brief: A serpent-tailed priestess with a pearl hair ornament, holding a shell censer fused to her hand.

**giant_clam** · giant_clam 「거대 조개」 — 10-2, 10-3 — none/O! (hinge) — N — authored.
Brief: A giant clam with a wavy shell open to show a glowing pearl and two eyes peeking over the lip.

**angler** · angler 「초롱아귀」 — 10-x — O — N — authored.
Brief: A round anglerfish with a big toothy grin and a glowing lure bulb on a short thick stalk.

**sea_serpent** · sea_serpent 「바다뱀」 — 10-x — O! — N — authored.
Brief: A sea snake rising in an S-curve from the floor, fin crest, fangs.

**sea_urchin** · sea_urchin 「성게」 — 10-x — none — S — authored.
Brief: A round spiky urchin on tiny feet with two eyes between the spines (thick, short spines).

**siren** · siren 「세이렌」 — 10-x — O! (fish tail) — N — authored.
Brief: A mermaid with a shell harp fused to her hands, flowing hair as solid shapes, singing.

**temple_guardian** · temple_guardian 「신전 수호상」 — 10-x — H — N — authored.
Brief: A stone temple statue warrior covered in barnacles and moss, holding a halberd.

**leviathan** · leviathan 「레비아탄」; leviathan_ex 「레비아탄 · 진」 [1,0.85,0.5] — 10-3 boss, R-3 — O! (sea dragon) — E — authored.
Brief: A massive sea dragon rising from water, fin crest, glowing aqua belly, coiled body.

## Zone 11 · guild street (11-1 새벽 길드 앞 대로, 11-2 상가 골목, 11-3 길드 본부 앞 광장)
Motifs: night street, neon shop signs (no text), traffic cones, power cables, violet rifts across shopfronts.

**high_orc** · high_orc 「하이 오크」 — 11-1, 11-3 — H — E — authored. The data says a red cloak; use a red hi-vis jacket instead of a cape.
Brief: An orc captain in a torn red hi-vis jacket swinging a cleaver-like greatsword, shouting.

**orc** · orc 「오크 전사」 — 11-x — H — N — authored.
Brief: A small orc in a horned hard-hat helmet with a big two-hand axe.

**void_eye** · void_eye 「공허의 눈」 — 11-x — O — N — authored.
Brief: A floating giant eyeball with short tentacles and a ring of small eyes round it.

**gargoyle** · gargoyle 「가고일」 — 11-x — H (winged) — N — authored.
Brief: A stone gargoyle with bat wings, crouched like it was pried off a building ledge.

**shadow_beast** · shadow_beast 「그림자 짐승」 — 11-x — O! — N — authored.
Brief: A wolf-like beast of thick dark smoke with a very solid, real jaw of teeth.

**nightmare** · nightmare 「나이트메어」 — 11-x — O! (horse) — N — authored.
Brief: A black horse with a violet flame mane and tail and glowing hooves.

**doppelganger** · doppelganger 「도플갱어」 — 11-x — H — N — authored.
Brief: A faceless mirror-surfaced humanoid in a plain hoodie, reflections across its body.

**fallen_angel** · fallen_angel 「타락 천사」 — 11-2…R — H (winged) — E — authored.
Brief: A winged figure with torn black wings and a broken halo-ring hovering just behind the head (attached), dark modern clothing.

**abyss_herald** · abyss_herald 「심연의 사도」 — 11-3 boss — **DONE**.

## Zone 12 · S-rank abyss gate (12-1 심연의 입구, 12-2 공허의 회랑, 12-3 심연의 옥좌) and Red Gate (R-1…R-3)
Motifs: void black-violet, abyss cracks, the final gate. The red gate reuses these with tints.

**void_reaper** · void_reaper 「공허의 사신」 — 12-x, R — H (floating) — E — authored.
Brief: A hooded reaper of void cloth with a large scythe fused to its hands and a death-mark glowing on its chest.

**chaos_spawn** · chaos_spawn 「혼돈의 촉수」 — 12-x — none/O — N — authored.
Brief: A blob with one huge mouth and tangled tentacles growing from it.

**abyss_worm** · abyss_worm 「심연 벌레」 — 12-x, R — O! — N — authored.
Brief: A giant worm bursting from the floor with a round mouth ringed by teeth.

**abyss_lord** · abyss_lord 「심연의 군주」; abyss_lord_ex 「심연의 군주 · 진」 [1,0.85,0.5] — 12-3 boss, R-3 boss — H — E — authored. No crown or throne motif in the mesh.
Brief: The final boss: a tall armoured abyss sovereign of black void plates with violet rift cracks and a corona of dark spikes over the shoulders.
