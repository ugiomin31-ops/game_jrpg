# PRODUCT TRUTH — 심연의 미궁 / Abyss Labyrinth

Evidence class: directly inspected project code, production outputs and local execution. This file does not establish third-party licensing interpretations, publisher identity, store approval or IP clearance. Dates below are last checked against this checkout. External feature copy may use only Implemented entries, respecting each stated verification scope.

## Implemented

### Campaign content and turn-based rules — verified (local C# execution) — 2026-10-07

- Four playable classes: 검사, 마법사, 궁수, 성직자. Twelve fixed dungeon floors, four biome sets, three difficulty choices, 51 enemy definitions including four bosses, 129 skills, 48 equipment definitions, 30 items and 12 quests.
- 2026-10-07: the same `Scripts/Logic/` + `Tools/LogicTests/` sources compiled with the .NET 8 SDK (Newtonsoft.Json 13.0.3, `ABYSS_LOGIC_TESTS`) on Linux: 15/15 passed, including every encounter group on B1F–B12F.
- Evidence: `Assets/_Game/Resources/Data/{heroes,dungeon,enemies,skills,equipment,items,quests}.json`; `Scripts/Logic/` under `Assets/_Game/`; actual `python Tools/logic_test.py` output: 11/11 passed, including encounter completion across all 12 floors, four battle regressions and six campaign regressions.
- A natural Lv.1 Normal campaign entered B1F, saved/restored its unresolved encounter, executed nine real engine commands with 15 damage events, won and returned to town in a throwaway C# executable. This is not proof of a complete Unity/Windows playthrough.
- Checked: 2026-10-06.

### Authored 3D asset production — verified (Blender production and Unity import) — 2026-10-06

- Four heroes, eight NPCs, 28 enemies/bosses, 48 gear, 30 items, 22 status emblems, eight element emblems, 12 UI emblems, six common props, town and four modular dungeon/arena sets have real generated geometry. Original generators and editable Blender outputs are retained.
- Evidence: `Blender/`, `Blender/blend/enemy_production_all.json`, `Assets/_Game/Resources/Art/`; successful Unity `Abyss/Validate Production Content` menu invocation. Creature report records actual saved/reimported rig, Col vertex colors, weighted vertices and required clips for all 28 IDs.
- Geometry exceeds the original aspirational polygon budgets for several heroes/enemies/environment parts; no low-end performance claim is supported by this import check.
- Checked: 2026-10-06.

### Sculpted monster rebuild (v3) — verified (Blender production and Unity import) — 2026-10-07

- 32 regular/elite monsters were remodelled with the sculpted kit (`Blender/enemies_d/`): one fused organic surface per creature, smooth multi-bone weights, Cycles-baked ambient occlusion in the vertex colours, small modelled eyeballs in sockets (no glowing or sticker eyes). The other 15 (skeletons, knights, scarecrows, golems, mimics, lich, wisp, fairies) keep their v1/v2 geometry with hero-style painted faces (`Blender/lib/creature_face.py`). All 47 bestiary icons were re-rendered.
- Evidence: Blender 5.2.2 (Linux) runs of `Blender/enemies_a/generate_all.py -- --asset ID` for all 47 ids; each `Blender/blend/enemy_production_<id>.json` records the saved and re-imported FBX (Rig + one skinned Body, Col, 0 unweighted vertices, 7 clips). Triangle counts are 7–13.5k (above the old ≤10k normal budget for several).
- Follow-up on 2026-10-07: the current 51 enemy FBX resources were imported in the isolated PR checkout with Unity 6000.3.25f1. Renderers/materials/shader support, Animator and seven required clips passed; the complete enemy contact sheet was rendered and inspected. Evidence: `docs/verification/asset-audit.json`, `docs/verification/enemies.png` and `docs/UNITY_ASSET_REVIEW.md`. This is not frame-by-frame verification of every combat animation.

### UI artwork — verified (production and local dungeon HUD rendering) — 2026-10-06

- 160 transparent 512px, 3D-derived portraits/icons cover Heroes4, NPCs8, Enemies28, Gear48, Items30, Status22, Elements8 and UI12.
- Evidence: `Blender/ui/render_icons.py`; `Assets/_Game/Resources/Icons/manifest.json`; production output `ARTWORK_COMPLETE 160`; `Scripts/UI/Kit/UIArtwork.cs` and actual rendered hero portraits in the resumed B1F HUD.
- Menu/battle consumers are wired; their complete runtime scenario coverage remains to be exercised.
- Checked: 2026-10-06.

### Title, town, prologue and first-person exploration — verified (local Unity editor execution) — 2026-10-06

- Actual rendered title and town use the authored town/NPC/hero/gear geometry. Prologue has eight real pages followed by the first-town elder tutorial. B1F renders in first person and real movement advanced (1,1)→(2,1)→(3,1)→(4,1).
- Saved B1F resumed through `GameApp.Continue(-1)`. Discovered-map rendering was repaired by requiring CanvasRenderer; fresh instantiated minimap had a renderer, 18 vertices and visible discovered tiles/player direction.
- Evidence: `Scripts/Runtime/GameApp.cs`, `Runtime/World/{TownWorld,DungeonWorld}.cs`, `UI/Screens/{GameStoryScreen,DungeonMapGraphic,DungeonMapSymbol}.cs`; actual Unity command execution and inspected game-view captures. These are local editor observations, not standalone build proof.
- Checked: 2026-10-06.

### Natural battle and town transactions — verified (local Unity editor execution) — 2026-10-06

- Real B1F movement triggered a natural encounter. Automatic combat completed three rounds with a victory; return to exploration settled rewards once, yielding 214G and the observed damage/MP costs.
- The shop's actual menu bought one `armor_chain`: gold 214→144. Party menu unequipped chain armor: bag 1→2, empty armor slot; re-equipped it: bag 2→1, `armor_chain` restored.
- Field-item target menu healed the warrior from HP142→165 and consumed exactly one healing potion (4→3), without changing gold.
- Final battle camera/help-panel composition was compiled without errors or warnings and visually inspected: four hero models remain visible, enemy plates are separate, and skill descriptions use a masked scroll view.
- Evidence: live Unity menu callbacks, observed campaign state transitions and `Store/screenshots/battle-normal-editor.png`. Not evidence of a complete campaign or native keyboard/gamepad verification.

### Original synthesized audio — verified (production; title/town playback) — 2026-10-06

- Ten BGM tracks, six jingles and 50 sound effects were actually synthesized/exported. BGM durations are 48–113 seconds with loop metadata; catalogue records zero clipped samples for the generated files.
- Evidence: `Tools/audio/`, `Assets/_Game/Resources/Audio/catalogue.json`, successful complete `python Tools/audio/export.py` output. Live Unity AudioSource observations showed `bgm_title` and `bgm_town` playing.
- All remaining in-game audio routes are wired; not every track/effect has been listened to or exercised in game.
- Checked: 2026-10-06.

### Save and preference implementation — verified (campaign tests; editor resume) — 2026-10-06

- Automatic save plus three manual slots; JSON state preserves floor/location, doors, keys and unresolved encounter. File writes use flushed temporary files and atomic replacement. Preferences cover sound, mute, resolution/fullscreen, dialogue speed and reduced motion.
- Evidence: `Scripts/Runtime/Persistence/`, `Logic/Game/SaveCodec.cs`, named `GameCampaignTests` in `Tools/LogicTests/`, actual editor B1F resume. Fullscreen/native Windows and complete menu/save scenarios still require runtime verification.
- Actual volume menu changed master volume to 0.5; reading the saved preference file returned 0.5 with mute disabled. Other settings/native-window paths remain unverified.
- Checked: 2026-10-06.

### PR UI, assets and emulated touch — verified (real Unity Editor and Windows build) — 2026-10-07

- PR #3 uses `claude/project-thread-65bpbq` / `50ecaf1` as its baseline. Pages deployment `e4f72c5` differs only in this fact file, so the game/assets baseline matches. PR changes have not been deployed to Pages. The obsolete `Assets/Temp/battle-framing-preview.png` is not current evidence.
- Actual Unity 6000.3.25f1 compilation passed. The real URP and Input System packages were used in an isolated Windows checkout and separate review save folder.
- All 298 FBX models passed material/shader checks; actors passed Animator and seven-clip checks. Hero 4 / enemy 51 / equipment 48 galleries were rendered with Unity. All 221 VFX recipes were instantiated, started and stopped with zero missing textures or failures.
- Touchscreen events through the real Input System UI module passed 21 checks at 915x412 and 21 at 1024x768: town stick move/release, service UI, confirmation cancel/duplicate guard, dungeon turn/map, four biomes, AUTO toggle/result/next encounter. Tablet battle framing was adjusted after inspecting the captures. Review encounters and unlocked floors use fixtures; this is not a natural campaign playthrough.
- Applied shared toon material/lighting polish across asset categories, reduced bright effect layers, and regenerated town FBX/Blender outputs with facility flags and fountain planting. Existing current hero/monster models were retained.
- Windows x64/Mono build succeeded. An initial command transport timeout did not stop the build; the actual Unity BuildReport is the verdict. Runtime Pipeline is intentionally disabled in player builds, generating a tooling warning. An earlier Editor graphics ring-buffer warning is retained in the review history; no minimum-device performance/FPS claim is made.
- Evidence and current limits: `docs/UNITY_ASSET_REVIEW.md`, `docs/verification/`. No physical Android/iOS device was connected, and this PR's WebGL build/Pages deploy, standalone input suite and full campaign remain unverified. Logic tests: 32/32 passed.

## Not implemented / not yet verified

- Mobile: Android APK/AAB and iOS Xcode build menus, landscape/IL2CPP/ASTC settings, touch-sized dungeon pad (hold-to-walk, strafe), tappable minimap, tap-to-target battle cards, drag-scrolling lists and a battle speed option (1x/1.5x/2x) exist in code (2026-10-07). They compile against the real Unity 6000.3.25f1 engine/editor reference assemblies with ugui/TMP/InputSystem 1.20.0 built from package source (URP replaced by a member-level stub) for both the editor and an Android player define set (2026-10-07; this check found and fixed a `PointerEventData.eventSystem` compile error in `UITouch.cs` that had removed every `Abyss/*` menu). GitHub Actions run 37569388774 (unity-builder v6, Personal license from repository secrets) built both targets on 2026-10-07: a 126 MB Android APK published to release `phone-latest`, and a WebGL build (84 MB gzip data) pushed to `gh-pages`. The WebGL build was served locally and opened in headless Chromium emulating an Android phone (915x412): it reached the title screen and a tap on 새로운 모험 opened the difficulty screen. Headless Chromium raised an HTML audio 'no supported source' error (it lacks the AAC codec); sound on real phone browsers is unverified. The APK has not been installed on a device.
- The PR Windows x64/Mono build succeeded in Unity 6000.3.25f1. Standalone native input/play verification has not yet completed. Do not call the deliverable release-ready or publish minimum specifications/FPS.
- Natural Unity battle and the listed transactions/settings are verified above; full VFX/boss/ending and remaining service/settings scenarios are not yet verified. Code/source assets alone are not full scenario proof.
- Store submission, approved publisher identity, price, release date and storefront app ID are not established by the project. Do not imply a published storefront.
- English localization is not provided by the Korean text table. Do not list English as a supported UI/story language.
- Multiplayer/cloud saves and platform achievements are not established features.
- Third-party notices are collected separately; copyright ownership/IP clearance of the original campaign and compliance with the user's Unity subscription cannot be established from this checkout.
- Checked: 2026-10-07.

## Permanently excluded

No permanent product exclusions have been confirmed in this conversation.

### Phone-first UI, battle staging, VFX and balance pass — verified (headless phone-size web build) — 2026-10-07
- Build e996880 (GitHub Actions) opened in headless Chromium emulating a 915x412 landscape phone: title (big bottom-left buttons, no quit), difficulty menu (back button top-left, card rows, no key hints), story, town (64-unit facility buttons), dungeon HUD (zoomed 9-cell minimap, chest/lore stone against the wall), battle (portrait turn order, closer camera, slim enemy plates, compact party cards), auto-battle (holy light pillar, warrior dash, enemy dash) and the result window (portraits, XP, gold) were observed.
- Found and fixed afterwards (71bb863): hidden party-card names, story text taps ignored, duplicated action log line, clipped command description. Battle intro/victory camera and projectiles were not caught on screen (headless rendering is too slow to sample them); APK not installed on a device.

### Motion, skill VFX, chest reveal and gear display pass — verified (headless phone-size web build) — 2026-10-07
- Build dd82e41 served from GitHub Pages (https://ugiomin31-ops.github.io/game_jrpg/, Pages enabled by the user on gh-pages) opened in headless Chromium at 915x412: continue → town → B1F → random battle (heroes visibly hold enlarged sword/staff/bow/mace, Double Shot drew the bow and fired the arrow, auto battle, victory pose behind the result window) → chest at B1F (10,3) showed the loot reveal ("보물 상자를 열었다!", 행운의 부적 card, rays). No exceptions in the console.
- Fixed afterwards (e4f72c5): reddish loot-card edge, revive burst played twice, victory spoils now icon slots. Hero/monster clips checked by FBX import (monsters: names and lengths unchanged; heroes: Attack/Cast/Idle/Victory longer, contact still 40 %/60 % normalised). Motion quality itself was not judged frame by frame (headless rendering too slow); APK not installed on a device.
