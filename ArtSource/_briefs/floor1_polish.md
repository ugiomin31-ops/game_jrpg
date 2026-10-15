# Floor 1 polish — outlines, battle camera, battle UI, skills, monsters (plan, 2026-10-12)

Scope: everything the player sees from the guild town through **zone 1 = subway 1-1 · 1-2 · 1-3** (`dungeon.json`
`subway_1..3`, tileset `subway`, boss `subway_bat_lord` on 1-3). Goal: a playable, visibly better floor 1 first from
**zero-credit code work**, then paid assets only where code cannot get there.

User request (2026-10-12, Korean, summarised): outlines too thick; can't zoom to see the characters; skills must "really
fire" with Tripo-made effects; control UI is ugly; battle camera and battle UI should be stylish like Persona 5 /
Metaphor: ReFantazio (reference only, never copied); fix monsters, boss, characters, battle, skills and motions up to
floor 1 so they are smooth and polished.

Fixed pipeline rules: images = ChatGPT web GPT-6 Extra High (one request = 4 candidates); 3D, rig and animation = Tripo
Studio web (Humanoid for bipeds); code animation allowed for blobs and flyers (approved); install and cleanup = headless
Blender by Sonnet workers; reviews by Sol 6.1; **Unity capture after every batch**. No commits unless the user asks.

---

## 0. Findings (code read 2026-10-12, line numbers are current)

| # | finding | evidence |
|---|---|---|
| F1 | Unity build is **landscape only** (autorotate left/right, portrait off). The 540×960 portrait loop is from the Godot era. Plan targets landscape 16:9 (1920×1080 canvas) and compact 20:9 (1600×900 canvas, `UIRoot.Compact`); portrait is a sanity capture only. | `ProjectSettings/ProjectSettings.asset:62-65`, `UIRoot.cs:143-152` |
| F2 | Outline = inverted hull in `AbyssToon` "Outline" pass, constant in NDC up to 6 m (`min(cs.w, 6.0)`), shrinking beyond. 0.004 ≈ 2 px at 1080p; 0.011 ≈ 6 px. | `AbyssToon.shader:286-288` |
| F3 | **Party leader h_dohyun is still the old VRoid model** (0.011 hull, no TRIPO/HUMANOID marker). Its Tripo version is staged with an install guide but never installed. | `Art/Characters/h_dohyun/` (fbx dated 10-09), `ArtSource/hunters/h_dohyun/staging/INSTALL.md` |
| F4 | **Boss subway_bat_lord is a Tripo mesh without a `TRIPO` marker** → it got the VRoid 0.011 hull with Z offset 0 (thick line + streaks). | `Art/Enemies/subway_bat_lord/` (no marker, mat `_OutlineWidth 0.011`), `AbyssArtImporter.cs:121-123, 551-556` |
| F5 | Tripo hunter folders still hold stale VRoid materials (`*_CLOTH.mat` 0.011, Z 0.01) referenced by the FBX external-object map; which ones bind at runtime is unverified. Weapon hulls: non-Tripo 0.02, Tripo 0.006 (MaterialPropertyBlock). | `h_jiho.fbx.meta externalObjects`, `GearDisplay.cs:99-103` |
| F6 | Battle camera: one fixed establishing shot high behind the party (`CameraHome (0,3.6,-10.2)`, aim `(1.4,1.05,0.6)`, FOV 42); actions only dolly ±0.5 m (`ActiveShot`). Heroes are only seen from behind; enemies are 5–6 m away. Smoothing is an exponential lerp (`_cameraRate`), shake/FOV punch additive. | `BattleView.cs:56-62, 1036-1053, 1089-1108` |
| F7 | Floor hotspot = arena empty **`LightAnchor_stage` at (0,0,5)** → point light 2.2 / range 7 straight above the centre of a cream floor, then bloom (threshold 0.92). | `Blender/environment/_arenas_a.py:170`, `EnvironmentProcessor.cs:38-46`, `BattleView.cs:102-103`, `Atmosphere.cs:149-157` |
| F8 | HUD is code-built **uGUI** (`UIFactory`/`UIPanel`, TMP, `UITween`), no prefabs, no UI Toolkit. Party cards 435×206 (compact 356×148) across the bottom; enemy cards 210×134 projected at the head and clamped into rows → they sit over the enemies; description box 1100×144 top-left; command menu = plain vertical list (6 rows/page) bottom-right. | `BattleHUD.cs:105-178, 252-324, 395-404, 1503-1539, 749-768` |
| F9 | Town camera: fixed offset (6.5, 8, −9.5) ≈ 14 m, FOV 45, no zoom/rotate; touch has one-finger stick + tap only. Party screen shows 2D portraits only, no 3D model view. | `TownWorld.cs:297-308`, `UITouch.cs`, `GameUI.Party.cs` |
| F10 | Skills: presentation beats exist (charge → wind-up → travel → area → impact → hit-stop/shake/flash/punch, ult cut-in with dim). Hunters have no `Skill`/`Ultimate` takes: the shared humanoid set is Attack/Cast/Die/Guard/Hit/Idle/Revive/Run/Talk/Victory/Walk, so every skill plays Attack or Cast. No effect meshes installed yet (`Resources/Vfx/Meshes/` missing). | `BattleView.cs:488-590`, `Art/HumanoidAnimations/`, `ArtLibrary.cs:118` |
| F11 | Floor-1 roster: slime, sewer_slime (model slime), sewer_rat, horned_rabbit, bat, tunnel_bat (model bat), killer_bee, elite_bat, boss subway_bat_lord. **Tripo-installed: sewer_rat, horned_rabbit (Humanoid clips), bat (code flyer), boss (rigged, marker missing).** Old: slime (code blob, old mesh), killer_bee, elite_bat. Tripo meshes already exported locally for killer_bee, elite_bat (`ArtSource/enemies/*/tripo/`) and slime (`ArtSource/tripo-test/slime_rigged*`, rig unusable) → **all floor-1 monsters can be finished for 0 credits.** | `dungeon.json` subway_1..3, `enemies.json`, `_tripo_ledger.md` B3 table, `ArtLibrary.cs:127-140` |
| F12 | Death dissolve, hit flash, knock-back, hit-stop (VFX slowed to 10 %), crits, BREAK already exist; crossfades are short and fixed (Hit .045, strike .05, cast .12); move = out-quad, return hop .3 s arc .4. | `BattleView.cs:294-296, 592-605, 1121-1166` |

---

## 1. Design rules (phone-readable, apply to every workstream)

- Canvas units: 1600×900 compact / 1920×1080 full. **Body text ≥ 24 u, labels ≥ 26 u, numbers ≥ 34 u, titles ≥ 40 u.**
  Touch targets ≥ `UIRoot.TouchTargetHeight` (84 u on phones). One thumb reach: primary commands in the right-hand 35 %.
- **Screen budget in battle:** HUD may cover at most the bottom 18 % and top 9 % of the screen plus the command fan on the
  right (≤ 34 % width, only while choosing). The camera must keep every living unit's body bounds **outside** HUD rects
  (W2 `HudSafeRect`, W3 publishes the rects).
- **Never cover a unit:** enemy tags and party plates are placed by their projected renderer bounds, not head points.
- Palette (hunter): ink `#08131B`, navy `#101C28`, cyan `#59D6CC` (existing `UITheme.Gold`), violet `#7B5CFF`, text
  `#EDF5F6`. **One accent: signal coral `#FF4D6D`** = focus, selected target, critical, "WEAK". Amber `#FFC93D` stays TP only.
  Contrast ≥ 4.5 : 1 for text; text never sits on the bright floor without a plate.
- Shape language (P5/Metaphor *principles*, not assets): parallelogram plates sheared 12°, asymmetric layout (stack
  steps left as it goes down), heavy type for verbs, thin type for numbers' units, hard drop shadow (offset 6 u, ink
  70 %), no rounded "card" boxes, no ornate filigree in battle. No red-black P5 colour scheme, no ransom-note lettering,
  no copied icons, logos, fonts or layouts.
- Motion: UI 120–280 ms, `OutCubic` for moves, `OutBack` (≤ 1.08 overshoot) for focus, 25–40 ms stagger. Camera blends
  0.25–0.5 s eased (see W2). **Reduced motion:** no dutch, speed lines, whip pans, overshoot; 150 ms fades only.
- Every task's acceptance = Unity compile with 0 errors + captures (Tools/ review harness, scripts kept outside the repo)
  at **1280×720 desktop** and **2400×1080 compact touch** (the PR6 compact harness), reviewed by the main session.

---

## W1 — Outlines and character viewing (0 credits)

### Decision: final outline rule
1. **Line weight by role, thinner everywhere** (material values, set by the importer):
   - Tripo characters/enemies/NPCs: `_OutlineWidth 0.0028`, `_OutlineZOffset 0.06` (was 0.004).
   - Remaining VRoid characters (until replaced): 0.006 (was 0.011). Environment unchanged (0.004 / 0).
   - Weapons (`GearDisplay.cs:103`): Tripo 0.003 (was 0.006), non-Tripo 0.008 (was 0.02).
2. **Shader global controls** in `AbyssToon.shader` Outline pass (all per-camera, set with `Shader.SetGlobalFloat`):
   `_AbyssOutlineScale` (default 1), `_AbyssOutlineRefDepth` (default 6, replaces the literal 6.0), and a far fade
   `saturate((_AbyssOutlineFadeEnd − w) / (_AbyssOutlineFadeEnd − _AbyssOutlineFadeStart))` (defaults 30 / 40 = no
   change). Width = `_OutlineWidth * _AbyssOutlineScale * min(w, RefDepth) * fade`. Values: battle 1.0 / 6 / 30 / 40;
   town 0.75 / 8 / 18 / 26; inspect view 1.15 / 3 / – ; dungeon first-person 0.8 / 4 / 14 / 22.
3. **Softer line colour:** default `_OutlineColor` (0.16, 0.13, 0.20) and base-colour mix 0.35 → 0.55, so the line
   reads as a dark tint of the surface, not a black stroke.
4. Target: a 1.3 m hunter at the battle command shot shows a 1.5–2 px silhouette at 1080p and no inner black streaks.

### Tasks
- **W1-T1 Outline fix** — files: `Shaders/AbyssToon.shader` (Outline pass only), `Editor/AbyssArtImporter.cs:567-587`
  (constants + migrate untouched 0.004→0.0028 and 0.011→0.006), `Runtime/Art/GearDisplay.cs:99-103`,
  `Runtime/World/Atmosphere.cs` (`SetupCamera` sets the globals; add per-context presets), marker file
  `Art/Enemies/subway_bat_lord/TRIPO` (+ reimport so the boss migrates to the Tripo hull). Runtime audit: a temporary
  editor script (scratchpad, not the repo) logs every renderer's bound material + outline width for the 4 starting
  hunters, floor-1 enemies and NPCs; any stale VRoid material still bound is remapped to the Tripo material in the FBX
  meta. Acceptance captures: battle command shot, town default zoom, boss close-up — no black bars over eyes or chest,
  silhouette line visible but thin.
- **W1-T2 Town camera zoom + rotate** — `Runtime/World/TownWorld.cs:297-308`, `UI/Kit/UITouch.cs`,
  `UI/Screens/GameUI.Town.cs`. Orbit rig: yaw (default current heading 214°), distance 5.5–15 m (default 9 m), pitch
  derived from distance (22° at 5.5 m → 40° at 15 m), FOV 40, target = leader chest (1.1 m). Inputs: pinch (2 fingers,
  cancels the stick), two-finger horizontal drag = yaw, mouse wheel = zoom, Q/E or right stick = yaw, RS/middle-drag = yaw;
  on-screen "＋/－" zoom and a "시점 초기화" pill (top-right, 84 u). Spring-damped (ω 9) with the existing SphereCast
  collision; zoom and yaw persist in `GamePreferences`. Acceptance: captures at near / default / far + rotated 90°; hunters
  ≥ 180 px tall at near (1080p); stick still works one-handed.
- **W1-T3 Hunter inspect view (turntable)** — new `UI/Screens/GameUI.Inspect.cs` + `Runtime/Art/InspectStage.cs`.
  Opened from the party screen (`GameUI.Party.cs`, button "3D 보기" on the selected hunter) and by long-press on a
  town party plate. Stage at y = −500 (own layer 30), dedicated camera → RenderTexture (1024², ×2 on ≥ 1440p) shown in a
  RawImage; key + rim + fill lights culled to the layer; dark navy gradient backdrop with a slanted cyan floor disc.
  Model = `ArtLibrary.SpawnCharacter` + `GearDisplay` (same gear as the party). Drag = yaw (inertia), pinch/wheel =
  zoom between full body (3.2 m) and bust (1.1 m), double-tap = reset; pose buttons: 대기 / 공격 / 스킬 / 승리 (plays
  clips that exist). Reduced motion: no inertia. Acceptance: full-body and bust captures for each starting hunter,
  outline thin, face readable.

---

## W2 — Battle camera (0 credits)

### Decision: shot system
Extract the camera from `BattleView` into **`Runtime/Battle/BattleCameraDirector.cs`**: `Shot { Vector3 pos, look;
float fov, dutch, blend; Ease ease; }`, `Play(Shot)`, `Cut(Shot)`, additive layers kept exactly as today (trauma
shake, FOV punch, hit-stop does not freeze the camera). Blending = eased interpolation over `blend` seconds from the
current *pose* (position, look point, fov, roll) — not the exponential chase — plus a critically damped follow
(ω 10) for moving subjects. **Framing helper** `Frame(Bounds[] subjects, Rect anchor, Rect hudSafe)`: dollies along the
view axis until the subjects' projected bounds fit the anchor rect inside the HUD-safe rect (rects from W3). All
offsets are in arena space (`transform.TransformPoint`), aspect-aware like `FramingFov`.

### Shot list (arena space: party z −3 … −4.6, enemies z +2.2 … +4)
| shot | when | camera | blend |
|---|---|---|---|
| S0 Establishing | intro end, between rounds, auto | current home lowered: pos (0, 2.6, −8.6), aim (0.6, 1.0, 1.2), FOV 40 | 0.5 s InOutCubic |
| **S1 Command** | `CommandRequestedEvent` (menu open) | low 3/4 **over the active hero's right shoulder**: hero + (1.05, 1.45, −2.3) → enemy-group centre at 0.9 m; FOV 38, dutch 0. Hero fills lower-left third (anchor x 0.08–0.38, feet above the party HUD), enemies centre (0.35–0.72) clear of the right-hand command fan | 0.45 s OutCubic, 0.12 s slight push-in (FOV −1.5) on arrival |
| S2 Target select | `PreviewTarget` | same side, dolly 35 % toward target, look at target chest, FOV 33, hero at frame edge; ally targets: reverse over the target ally | 0.25 s OutCubic |
| S3 Strike follow | melee approach (`Move` toward target) | outside 3/4 track at 1.1 m height, 4.2 m off the line, follows actor (damped); at contact −4 FOV punch + existing shake/hit-stop | follow; 0.2 s into it |
| S4 Shot/cast | ranged basic, projectile skills, spells | behind caster, low (0.9 m), 15° off-axis; on release a **0.18 s whip** to the impact framing (target + 1 neighbour) | cut on whip |
| **S5 Skill cut-in** | skills tier ≥ 2 and all ultimates | **fast push-in on the caster's face/upper body** (0.22 s OutExpo, FOV 42→28), **dutch 8°** (ult 12°), speed-line + colour-flash overlay (W3-T5) for 0.35 s (ult: existing portrait cut-in 0.95 s on top) → then S3/S4 | hard cut in, eased out |
| **S6 Enemy turn** | enemy `ActionStartEvent` | **reverse angle from behind the acting enemy** toward the party: enemy + (−1.4, 1.6, +2.6) → target hero chest; FOV 40 → heroes seen from the front | 0.35 s OutCubic |
| S7 Hit reaction | big hit / crit on a hero | 0.3 s hold on the target from the front, then back to the turn's shot | 0.15 s |
| S8 Victory | `Finish` victory | front of party, 1.4 m high, slow 25° orbit over 2.4 s, party poses; then results | 0.6 s |
| S9 Boss entrance | existing `BossEntrance` | keep, re-expressed as shots (low angle at boss, FOV 34) | as today |

Rules: shots never place a living unit's bounds under HUD rects; if `Frame` cannot fit, widen FOV up to +8° then fall
back to S0. Reduced motion: S0 only (+ static target highlight), as today. Speed setting scales blends.

### Tasks
- **W2-T1 Kill the hotspot + rim light** — `BattleView.cs:102-103`, `EnvironmentProcessor.cs:20-46`, `Atmosphere.cs`
  battle presets. In battles skip `LightAnchor_stage`, edge anchors 1.1 intensity / range 5; battle bloom threshold
  ≥ 1.05; add one cool rim directional light (cyan-violet, 0.5, from behind the enemies) for silhouette separation.
  Acceptance: battle start capture — no blown-out floor (centre floor pixels below 0.85 luminance), units separated from
  background.
- **W2-T2 Camera director + S0/S1/S2/S6/S8** — new `BattleCameraDirector.cs`; `BattleView.cs` keeps calling it from the
  same places (`Establishing`, `ActiveShot`, `PreviewTarget`, `StageOutcome`, `LateUpdate` layers move into the
  director). Acceptance: captures of S1 for each of the 4 heroes, S2 on each enemy lane, S6 for a bat and the rat,
  S8; existing trauma/hit-stop feel unchanged (compare clips).
- **W2-T3 S3/S4/S5/S7** — follow, whip, cut-in shot + hooks for the W3-T5 overlay; ultimate path keeps
  `UltimateCutIn`. Acceptance: 3-frame sequences (start / contact / settle) for sig_dohyun, fireball, sig_jiho,
  holy_light and the boss's sk_crow_swarm.

---

## W3 — Battle UI redesign + control UI style pass

### Mock-ups first (ChatGPT web, GPT-6 Extra High, 4 candidates per request → **8 requests = 32 images**)
Save to `ArtSource/ui_mockups/<id>/candidates/` with `prompts.md`. Common lead: *"Generate FOUR separate standalone
images… Original game UI mock-up for a modern Korean urban-fantasy hunter RPG on a landscape phone (20:9). Stylish,
high-contrast, kinetic layout inspired by modern JRPG menu design principles (asymmetric diagonal composition, bold
parallelogram plates, strong typography, motion implied by slants) — but an ORIGINAL look: palette deep navy, ink
black, cyan and violet with one coral-red accent; no Persona or Metaphor logos, characters, fonts, icons or red-black
colour scheme; Korean UI text; clean 3D toon battle scene behind the UI."* Then per screen:
1. `battle_command` — over-the-shoulder hero lower-left, two slimes centre, diagonal command fan right (공격/스킬/궁극기/아이템/방어/도주), compact turn-order chips top-left, slim party plates bottom.
2. `battle_skills` — skill list with element chips, MP/TP pills, WEAK badge, one-line description on the focused plate.
3. `battle_target` — target ring + bracket reticle on an enemy, compact enemy tag (name, thin HP bar, weakness icons) floating above it, damage estimate pill.
4. `battle_enemy_turn` — reverse angle, enemy intent banner, party plates highlighting the threatened hero.
5. `battle_cutin` — skill cut-in: diagonal colour band, speed lines, hero bust slice, skill name in heavy type.
6. `battle_result` — victory: party pose, EXP bars, drops on slanted plates.
7. `town_hud` — guild street, slanted header ribbon (goal), facility list as plates, slim party plates, zoom buttons.
8. `ui_kit_sheet` — component sheet: plates (idle/focus/disabled), pills, bars, chips, icons frame, buttons — flat on navy.
Picks: Haiku ranks each set against §1 rules (main session approves). Only approved images go to implementation; they
are references, not textures.

### Tasks (all 0 credits)
- **W3-T1 HUD geometry (no restyle yet)** — `BattleHUD.cs`. Enemy cards → **compact tags** (name 24 u, HP bar 140×10,
  weakness icons once known, intent icon); placed from the projected **renderer bounds** above the top edge (below the
  feet if clipped), pushed apart horizontally, never overlapping any unit bounds; full card only while targeting or on
  long-press. Party cards → slim plates (compact h 96, full h 120: portrait, name, HP big, MP thin, TP ring on the
  portrait). Remove the top description box: the description becomes the focused plate's subline (long text in a
  tooltip on long-press). Turn order → chip strip top-left (≤ 7 chips, active 1.3×). Action log → the skill ribbon only.
  Publish `HudSafeRect` (screen rect free of HUD) for W2. Acceptance: compact + desktop captures for 2-, 3- and 4-enemy
  groups and the boss: no tag or plate overlaps any unit.
- **W3-T2 UI kit: slant plates** — `UI/Kit/UISkew.cs` (`BaseMeshEffect` shearing x by y·tan 12°), `UIFactory`
  `UIPanelStyle.Slant` + `SlantButton`, theme tokens (violet, signal coral) in `UITheme.cs`, hard drop shadow helper.
  Acceptance: kit capture scene (scratchpad) matching the picked `ui_kit_sheet`.
- **W3-T3 Command fan** — `BattleHUD.cs` `ShowCommands`/`Render`/`LayoutMenu`: 6 slanted plates stepping left 18 u per
  row from bottom-right; focused plate 1.12×, coral fill, heavy label, subline; slide-in from right 160 ms with 30 ms
  stagger, OutBack; select flash + others slide out; page arrows become a small "1/2" pill. Skills/items/targets reuse
  the fan (element chip, MP/TP pills, WEAK badge). Keyboard/gamepad navigation and paging unchanged.
- **W3-T4 Target indicator** — world ring decal under the target (accent, rotating 30°/s, pulses on focus) + screen
  bracket reticle + damage-estimate pill + "WEAK" callout; ally targets cyan.
- **W3-T5 Cut-in overlay** — `BattleHUD.SkillCutIn(color, name, heroId, tier)`: diagonal colour band wipe (90 ms),
  radial/diagonal speed-line sprite (generated once with `Tools/ui/gen_ui_sprites.py`), white flash 60 ms, heavy skill
  name sliding along the band; ultimates keep the existing portrait cut-in restyled to the band. Driven by W2 S5.
- **W3-T6 Control UI style pass** — town HUD (`GameUI.Town.cs`: goal ribbon, facility plates, party plates, zoom
  pills), main menu and party screen (`GameMenuScreen.cs`, `GameUI.Party.cs`) switch to `UIPanelStyle.Slant`; touch
  stick ring restyled. Acceptance: town, menu, party captures vs the picked mock-ups.

---

## W4 — Skills that really fire

### Floor-1 skill set
- Starting kits (Lv 1): **h_dohyun** basic_attack, sig_dohyun, strong_attack, stunning_slam · **h_seoa** basic_attack
  (attack_mage), sig_seoa, fireball · **h_jiho** basic_attack, sig_jiho, sk_poison_arrow · **h_yuna** basic_attack,
  sig_yuna, holy_light, sk_c_protect, sk_cure.
- Likely learned during floor 1 (Lv 4–6): sk_provoke, sk_w_rally, sk_cleave, sk_ice_lance, sk_m_sleep,
  sk_m_shadow_bolt, sk_a_ice_arrow, sk_hunter_mark, sk_c_regen, sk_c_blessing, sk_heal_all. Ultimates unlock at Lv 8.
- Enemies: sk_screech, sk_bleed_edge, strong_attack, sk_poison_arrow, poison_spore, sk_acid_spit; boss adds
  sk_crow_swarm, sk_twin_bite.

### Mesh subset (from the 28 in `skills_vfx.md` §4)
| priority | meshes | why |
|---|---|---|
| A — B4 (candidates exist, pick only) | slash_crescent, energy_arrow, energy_orb, impact_crater, shield_dome, light_pillar | dohyun kit, jiho kit, fireball/spark/acid, stunning_slam, protect, ult charge |
| B — floor-1 core | ground_seal, flame_plume, lightning_bolt, thrust_spike, heal_bloom, holy_cross, energy_lance, nova_wave, rock_debris, feather, crystal_prism | every Lv-1 charge, sig_seoa, fireball, sig_jiho, yuna kit, screech, crow_swarm, mage basic attack |
| C — boss signature | bite_jaws (optional #27) | sk_twin_bite |
| D — floor-1 level-ups (later) | ice_shard, shadow_tendril | sk_ice_lance, sk_a_ice_arrow, sk_m_shadow_bolt |
B4 picks to finish: the 6 candidate sets in `ArtSource/vfx/*/candidates` (Haiku ranks vs the effect contract, main approves).

### Presentation beats (per skill: charge → cast pose → travel → impact → aftermath → camera)
| skill | charge | pose | travel | impact | aftermath | camera |
|---|---|---|---|---|---|---|
| sig_dohyun (twin slash) | weapon glint 0.15 s | dash + Skill take | — | 2× slash_crescent crossing, sparks | cut lines fade | S5 light → S3, hs .06 |
| strong_attack | dust at feet | big wind-up | — | slash_crescent big + flash | sparks fall | S3, punch −4, hs .08 |
| stunning_slam | ground_seal pulse | leap slam | — | impact_crater + rock_debris + shock ring | dust settles | S5 → S3 low, sh .48 |
| sig_seoa (spark) | ground_seal + crackle | Cast | energy_orb (spark) | lightning_bolt from above, white flash | after-sparks | S5 → S4 whip |
| fireball | ground_seal + embers | Cast | energy_orb + flame_plume tail | flame_plume burst | embers, smoke | S4 whip, hs .08 |
| sig_jiho (double shot) | bow glint | draw | 2× energy_arrow | thrust_spike ×2 | streak lines | S4 behind archer → whip |
| sk_poison_arrow | — | draw | energy_arrow (green) | energy_orb bubble burst | poison status loop | S4 |
| holy_light | ground_seal (gold) | Cast | energy_lance short | holy_cross small, gold flash | feathers | S5 light → S4 |
| sig_yuna / sk_cure | ground_seal (green) | Cast | — | heal_bloom (+ nova_wave on cure) | petals, motes | S2-style on ally, no shake |
| sk_c_protect | ground_seal | Cast | — | shield_dome rises 0.25 s | status aura loop | ally framing |
| enemy screech / crow_swarm / twin_bite | — | enemy take | — | nova_wave · feather burst + thrust_spike · bite_jaws | — | S6 reverse angle |

### Hunter skill motions (Tripo, paid)
Shared humanoid takes lack `Skill`/`Ultimate`. Plan: rig **one** hunter on the second account (upload the local
h_seoa/h_dohyun FBX, Humanoid/Mixamo auto rig 20) and buy text-to-motion clips per class: **Skill + Ultimate + battle
stance idle** × 4 classes = 12 clips × 20 = 240. Clips retarget through Unity Humanoid to every hunter of that class.
Code: `ArtLibrary.SpawnCharacter` (`ArtLibrary.cs:118`) loads `Art/HumanoidAnimations/<class>/` over the shared set
(same-name clips override); contact points per clip go in `BattleView.Contact` (`BattleView.cs:605`).

### Tasks
- **W4-T1 Pick B4 meshes + install** (paid, VFX-1: 6 × 90 = 540) → mesh layers on the floor-1 recipes in
  `Tools/vfx/gen_effects.py` `MESH_UPGRADES`; regenerate `effects.json`.
- **W4-T2 Floor-1 core meshes** (paid: 11 × 90 = 990, + bite_jaws 90) — images B first, one Tripo run each, retopo
  ≤ contract tris.
- **W4-T3 Beat timing pass** (0 credits) — `presentation.json` rows above (charge, hit_stop, shake, flash within the
  §2 family ranges) + `BattleView.StartAction` hooks for S5/S4 camera. Acceptance: 3-frame captures per skill in the table.
- **W4-T4 Hunter motions** (paid ≈ 260) after W2 lands, so cut-ins are timed against the real takes.

---

## W5 — Floor-1 monsters, boss and motion smoothness

| unit | now | action | credits |
|---|---|---|---|
| h_dohyun (party leader) | old VRoid | install the staged Tripo model per `ArtSource/hunters/h_dohyun/staging/INSTALL.md` (Humanoid + shared clips), Blender posing check first | 0 |
| slime / sewer_slime | old mesh, code blob | strip bones from `ArtSource/tripo-test/slime_rigged`, retopo already done → static mesh at `Art/Enemies/slime/slime.fbx` + `TRIPO` marker; keeps `RiglessBlobAnimator`; sewer tint unchanged | 0 |
| killer_bee | old | flyer route like bat: split Body/Wing_L/Wing_R in Blender from `ArtSource/enemies/killer_bee/tripo/`, `FLYER` + `TRIPO` markers | 0 |
| elite_bat | old | same flyer route from `ArtSource/enemies/elite_bat/tripo/` (11.6k tris → decimate to ≤ 8k), red authored tint kept | 0 |
| bat / tunnel_bat | Tripo flyer | none (tune flyer idle, W5-T4) | 0 |
| sewer_rat, horned_rabbit | Tripo Humanoid | Blender skin-weight check result logged (ledger says open) | 0 |
| subway_bat_lord | Tripo, marker missing | `TRIPO` marker (W1-T1); verify takes: Idle, Attack, Cast, Hit, Die (+ optional roar). Optional paid: 3 text-to-motion clips (roar, swarm cast, bite) after re-rig on the second account: 20 + 60 = **80** | 0 / 80 |

Smoothness (W5-T4, 0 credits, `BattleView.cs`, `ClipAnimator.cs`, rigless animators):
- Crossfades: strike 0.05 → 0.08, Hit 0.045 → 0.07, cast 0.12 → 0.15, return-to-Idle 0.12 → 0.2; blend from current
  pose always (already true for rigless).
- Approach: 0.06 s anticipation (lean back), then ease-in-out run with a 4 % overshoot settle at the contact point;
  return hop 0.3 s → 0.34 s, arc 0.4 → 0.22, land with a 0.06 s squash on blobs.
- Idle variety: random start phase and ±6 % speed per unit; flyers random bob phase; enemies play a fidget/roar take
  every 6–10 s if present.
- Hit reactions: knock-back direction from attacker (not facing), 1.3× on crit; blobs squash 0.8 / flyers tumble 15°.
- Death: element-tinted dissolve edge, 0.12 s hold on the last Die frame before dissolve, small drop of the flyer.
Acceptance: 60 fps capture sequences (start / mid / end) of approach, hit, death for each floor-1 enemy; no pops.

---

## 2. Order (playable improved floor 1 first)

| # | task | owner | credits | gate |
|---|---|---|---|---|
| 1 | W1-T1 outline fix + boss TRIPO marker + material audit | Sonnet | 0 | battle/town/boss captures |
| 2 | W2-T1 hotspot + rim light | Haiku | 0 | battle start capture |
| 3 | W5 installs: h_dohyun, slime, killer_bee, elite_bat (headless Blender, markers) | Sonnet | 0 | Blender pose/split checks + battle captures |
| 4 | Mock-ups: 8 ChatGPT requests (32 images) + B4 VFX picks ranking | Haiku (browser loop) | 0 | main session approves picks |
| 5 | W2-T2 camera director + S0/S1/S2/S6/S8 | Sonnet | 0 | shot captures |
| 6 | W3-T1 HUD geometry (tags, plates, HudSafeRect) | Sonnet | 0 | no-overlap captures |
| 7 | W1-T2 town zoom/rotate · W1-T3 inspect turntable | Sonnet | 0 | captures |
| 8 | W3-T2/T3/T4 slant kit, command fan, target indicator | Sonnet | 0 | vs mock-ups |
| 9 | W2-T3 + W3-T5 cut-in shots and overlay | Sonnet | 0 | sequences |
| 10 | W5-T4 smoothness pass · W4-T3 beat timing | Sonnet | 0 | sequences |
| 11 | W4-T1 B4 VFX-1 (6 meshes) | Haiku loop + Sonnet install | 540 | effect captures |
| 12 | W4-T2 floor-1 core meshes (11) | Haiku loop + Sonnet install | 990 | effect captures |
| 13 | W4-T4 hunter Skill/Ultimate/stance motions | Haiku loop + Sonnet install | ≈ 260 | Blender skin check + captures |
| 14 | W3-T6 control UI style pass (town, menu, party) | Sonnet | 0 | vs mock-ups |
| 15 | optional: bite_jaws (90), boss clips (80), ice_shard + shadow_tendril (180) | — | ≤ 350 | only if balance allows |

Steps 1–10 give the playable improved floor 1 with zero credits. Sol reviews each batch; captures after every batch.

## 3. Credits (second Tripo account ≈ 2,260)
Required: 540 + 990 + 260 = **1,790** → ≈ **470 left**. Optional set ≤ 350 → worst case ≈ 120 left. B4's zone-2
humanoids (sprout, mandragora, goblin, goblin_shaman, 440) are **deferred** (not floor 1). Read cost on the button and
the header balance before every paid step; log in `_tripo_ledger.md` and each sidecar.

## 4. Risks
- **R1 Uploading a local FBX to Tripo for rigging** may cost more than the 20 auto-rig (unknown import cost); read the
  button first, stop and ask if > 75.
- **R2 Text-to-motion quality** for weapon skills (no weapon in Tripo) — clips may need Blender trims/contacts; budget
  one retry via image-free prompt edits only (no second purchase per clip without approval).
- R3 Camera shots vs arena geometry (pillars, train walls) — `Frame` must SphereCast like the town camera; fallback S0.
- R4 Compact-HUD tags vs 4–5 enemies + summons: tags may stack; rule = shrink to icon-only tags before overlapping.
- R5 Outline change also affects environment/NPC looks (global params) — capture town + dungeon too.
- R6 Stale VRoid materials in Tripo folders: deleting them changes GUIDs referenced by FBX metas — remap, don't delete,
  in this pass.
- R7 Unity must be closed for installs (h_dohyun guide); serialize Unity-using tasks (one Unity worker at a time).
- R8 P5/Metaphor likeness: mock-up prompts and the kit forbid their logos, fonts, red-black scheme and layouts; main
  session rejects anything that reads as a copy.
- R9 Portrait is not shipped (F1); if the user expects portrait, that is a separate project decision.

## Amendments after Sol 6.1 review (2026-10-12) — binding for workers
- Order (single Unity owner): F1 model installs (Unity closed) -> TASK 1 outlines -> TASK 2 battle hotspot -> TASK 6 HUD geometry/contract -> TASK 5 camera director. Browser mock-ups may run in parallel; no UI restyle before approved mock-ups. B4 effect-mesh picks are done (slash_crescent B, energy_arrow C, energy_orb A, impact_crater D, shield_dome A, light_pillar A).
- Outlines: per-camera values set at each camera's render boundary and restored afterwards (no single global set in Atmosphere.SetupCamera); guard fade denominators; globals outside the material CBUFFER. The outline colour modulation uses vertex colour, not albedo — name it accordingly. Keep environment widths; town/dungeon changes independently reversible. Migrate only identified stock values on actually bound materials; no blanket deletion/remapping.
- HUD/camera contract: the HUD publishes normalized viewport occlusion rectangles (top bar, bottom party plates, right command fan) including device safe-area insets. Camera framing runs before tag placement each frame; tags never feed back into camera fitting.
- Framing rule (main decision): close shots (S1/S2/S6) require the actor and the target to be fully visible; other units are optional. The establishing shot S0 requires all living units. Use projected eight-corner bounds, near-plane handling, bounded fitting iterations and hysteresis; validate reverse shots against arena occlusion, not only SphereCast.
- Camera hooks cover menu reopen, cancel, auto battle, charge announcements, summons, reduced motion and restore; CommandRequestedEvent must not be overwritten by a later Establishing call during replay (BattleView.cs:174–178, 201–203).
- Rim light and bloom changes are battle-local and restored on exit; shared subway dungeon presets stay unchanged.
- Every task captures 1280×720 and 2400×1080 with touch/Compact enabled, plus regressions.
