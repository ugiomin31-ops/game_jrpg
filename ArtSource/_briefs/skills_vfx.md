# Skill VFX — mesh effects through the image → Tripo pipeline

Written 2026-10-12 (planner, read-only investigation). Sources: `Assets/_Game/Resources/Data/skills.json` (300 rows),
`presentation.json` (156 rows), `Resources/Vfx/effects.json` (227 recipes, built by `Tools/vfx/gen_effects.py` +
`Tools/vfx/effects_extra.json`), `Scripts/Presentation/Vfx/VfxLibrary.cs`, `Scripts/Runtime/Battle/BattleView.cs`,
`Shaders/VfxUnlit.shader`, `Scripts/UI/Kit/UINumberPopup.cs`.

## 1. What exists today (findings)

**Skills.** 300 rows: 212 used by hunters/jobs/gear, 103 by enemies (16 shared, `sk_e_thunder_all` unused).
Kind: Damage 207, Buff 47, Debuff 24, Heal 16, Revive 4, Cleanse 2. Element (`GameData.cs:15`): None 109, Pierce 36,
Dark 36, Holy 29, Slash 24, Blunt 20, Fire 17, Ice 16, Thunder 13. Target: enemy 231 / ally 45 / self 24; scope
single 154 / all 130 / random 16. Every skill except `basic_attack` names a `presentation` row; 149 of the 156 rows are
used (the other 7 are class/enemy default attacks and `pr_buff_party/self`).

**Presentation is already fully data-driven** (`PresentationDef`, `GameData.cs:341-362`): `actor_action`
(attack/cast/shoot), `approach` (none/lunge/dash_to_target), four VFX keys `charge_vfx` (14 distinct),
`travel_vfx` (17), `impact_vfx` (74), `area_vfx` (82, with `area_wait`, `area_scale`), plus `hit_stop`, `shake`,
`screen_flash`, `light_color`, `hit_interval`, `sfx_cast`, `sfx_impact`. `gen_effects.py:1575-1580` fails the build if
any presentation key has no recipe.

**Trigger points in BattleView.cs**
| beat | code | what plays |
|---|---|---|
| anticipation | `StartAction` 471; charge at 560-561 | `charge_vfx` follows the actor for the action length; lunge/dash move |
| area | 579-585 | `area_vfx` once at the target centre, ground-pinned, `area_wait` lead, dim + `AddTrauma(shake*.6)` + flash |
| travel | 568-610 | `_vfx.Travel(travel_vfx, from, to, time)`; one per hit when multi-hit and no area |
| impact | `Damage` 696-747; ally impacts 258, 635-638 | `impact_vfx` at `HitPoint`, scale ×1.3 on crit |
| feedback | 711-745 | hit anim, model flash, knock-back recoil, trauma shake, FOV punch (−1.5 / −3 crit), screen flash (crit white or `screen_flash`), hit-stop (`HitStop` 1118: freezes unit anims; ×1.6 crit, ×1.3 weak), damage numbers (`UINumberPopup`: Damage/Critical style with 0→1.5→1 pop and after-images, weak/resist tags), BREAK sequence 277-281 |

**VFX runtime** (`VfxLibrary.cs`): pooled recipes of layers. Layer kinds quad (billboard or `horizontal`), orbit,
burst/emitter (ParticleSystem, billboard only), ring/arc (procedural ribbons), sphere (procedural barrier sphere),
trail. One shader `Abyss/VfxUnlit` (additive or `alpha`, `Cull Off`, `ZWrite Off`, output = vertex colour × `_Tint` ×
texture). Colour = layer colour × `light_color` tint, so shared keys stay near-white and get tinted. 72 textures in
`Resources/Vfx/Textures`. **No mesh support**: the only 3D shapes are the code-built ring, arc and sphere. Hit-stop does
not slow VFX (`BattleView.cs:1063` sets `_vfx.TimeScale = Speed` even during `_hitstop`).

Conclusion: the impact/feedback stack is already rich; what is missing is **solid 3D shape** (everything is flat
billboards). The cheapest high-impact change is one new layer kind that draws a Tripo mesh, so the existing 227 recipes
gain mesh layers through data, with almost no BattleView change.

## 2. Effect families (anticipation → travel → impact → aftermath)

Every presentation row is assigned one family (table in §8). ULT = job/ultimate rows (`pr_jb_*`, `pr_ult_*` with a
`job_*`/`ultimate_*` area): they use their element family plus the ULT extras. Feedback columns are the target ranges
for `presentation.json` (data-only normalisation, task V-D below); crit/weak multipliers stay in code.

| family | anticipation | travel | impact | aftermath | hit_stop | shake | flash |
|---|---|---|---|---|---|---|---|
| BLADE (slash) | weapon glint, lunge/dash | — | `slash_crescent` sweeping (scroll), spark burst | thin cut line fades, sparks fall | .05–.08 (combo hits .04) | .20–.35 | crit only |
| HEAVY (blunt) | wind-up, dust at feet | dash | `impact_crater` slams flat, `rock_debris` mesh burst, shock ring | dust, settling debris | .09–.12 | .45–.60 | tier 3 |
| PIERCE (arrow/thrust) | bow charge glint | `energy_arrow` aligned to flight + trail | `thrust_spike` punches through target | streak lines | .04–.06 (snipe .11) | .15–.30 | snipe/deadeye |
| FIRE | `ground_seal` + embers | `energy_orb` + `flame_plume` tail | `flame_plume` burst, heat flash | embers, smoke | .06–.09 | .35–.55 | area rows |
| ICE | `ground_seal`, frost motes | `ice_shard` | `ice_shard` mesh burst / `ice_spike_cluster` erupting | shards linger then shatter | .08–.10 (freeze feel) | .25–.40 | area rows (cyan) |
| THUNDER | `ground_seal`, crackle | `energy_orb` (spark) | `lightning_bolt` strike from above | after-sparks | .03–.05 per hit | .40–.55 | always (white) |
| VOID (dark) | `ground_seal`, dimming | `energy_orb` / `energy_lance` | `shadow_tendril` grab, `rift_gate` tear | drifting ash | .07–.10 | .35–.50 | no (dim instead) |
| HOLY | `ground_seal`, rising motes | `energy_lance` (short) | `holy_cross` / `light_pillar` | feathers, halo ring | .06–.09 | .25–.45 | yes (gold) |
| ARCANE (none-element magic) | `ground_seal` | `energy_lance`/`energy_orb` | `crystal_prism` shards, beam | prism glints | .06–.09 | .30–.50 | tier 3 |
| NATURE (poison/plant/sand) | — | arrow/spit | `vine_coil` bind, bubble burst (`energy_orb` alpha) | spores, mist | .03–.05 | .10–.25 | no |
| SUPPORT (heal/revive/cleanse) | `ground_seal` (heal) | — | `heal_bloom` opens, `light_pillar` on revive | petals, motes | 0 | 0 | revive soft gold |
| GUARD (buff/shield/war cry) | `ground_seal`, aura | — | `shield_dome` / `barrier_panel` / `nova_wave` | looping status aura (existing `status_*`) | 0 | 0–.15 (guard thud) | no |
| HEX (debuff/control) | `ground_seal` | — | `chain_ring` snaps shut, `nova_wave` (screech) | status loop | 0–.03 | 0–.15 | no |
| ULT extras | charge_grand: seal + thin `light_pillar`, existing dim/cut-in | — | family impact at 1.5–2× scale + `sword_phantom` orbit or `meteor_rock`/`rift_gate` set piece | big `nova_wave`, debris | .12–.14 | .55–.70 | yes |

Damage-number pop: already scales on crits (`UINumberPopup.cs:234-240`); no change needed. Optional later: tier-3
skills use the Critical pop curve without the CRITICAL tag (not in this plan).

## 3. Split: Tripo meshes vs Unity particles/shaders

- **Tripo mesh** = any shape that must read as a solid 3D object from the 3/4 battle camera: blades, arcs, spikes,
  shards, pillars, domes, bolts, petals, chains, vines, tears. Rendered with `Abyss/VfxUnlit` (additive by default,
  `alpha` for dark/solid looks), tinted per element, animated by the layer (scale, alpha envelope, spin, UV scroll).
- **Stays particles/quads** (existing): sparks, embers, smoke, mist, glows, hit flashes, star glints, speed lines,
  status icons, sleep `zzz`, music notes, ink cloud, all flipbooks (`flame_sheet`, `lightning_sheet`, `explosion_sheet`).
- **Stays procedural code meshes**: the flat ground `ring` ribbon, `arc` ribbon, `trail`. The Tripo meshes are added
  on top; existing layers are kept unless the upgrade says "replace", so every recipe still works if a mesh is missing.

## 4. Shared effect meshes (28: 26 core + 2 optional)

Install path `Assets/_Game/Resources/Vfx/Meshes/<id>.fbx`, texture `Assets/_Game/Resources/Vfx/Textures/mesh_<id>.png`.
Size = longest dimension at layer `size` 1 (metres). "Used by" = skills whose recipes get the mesh (§8).

| # | id | shape brief (for the image) | pivot / orientation | size | tris | used by |
|---|---|---|---|---|---|---|
| 1 | ground_seal | flat round seal disc: 3 concentric raised rings, 8 spokes, notched outer rim, **no runes or letters** | bottom centre, lies in XZ | 2.0 Ø | ≤800 | 185 |
| 2 | slash_crescent | thick crescent blade arc, sharp at both tips, bevelled edge, thicker at the middle, slight twist | arc centre (swing pivot), arc in XY, faces +Z | 2.0 chord | ≤600 | 68 |
| 3 | light_pillar | tall column of light: hexagonal shaft, flared base ring, tapering top | bottom centre, +Y up | 3.0 tall | ≤600 | 61 |
| 4 | thrust_spike | cone burst: one long central spike with 6 shorter spikes around it, like a star-shaped spearhead | base centre, tip toward +Z | 1.6 | ≤600 | 60 |
| 5 | energy_arrow | faceted arrowhead with a short shaft and three swept fins (no feathers, no wood) | centre of mass, tip +Z | 1.0 | ≤400 | 48 |
| 6 | nova_wave | thick donut wave with a curling crest on its outer edge (like a breaking wave ring) | centre, lies in XZ | 2.0 Ø | ≤800 | 43 |
| 7 | shadow_tendril | curved claw-like tendril, thick root narrowing to a hooked tip, smooth segments | root at origin, rises +Y, curls toward +Z | 1.8 | ≤700 | 43 |
| 8 | holy_cross | thick four-armed cross of light with pointed ends and a bevelled diamond core (star-cross, no religious ornament, no runes) | centre, faces +Z | 1.6 | ≤500 | 39 |
| 9 | flame_plume | stylised cartoon flame tongue with three lobes curling upward, solid sculpted | bottom centre, +Y | 1.2 | ≤600 | 38 |
| 10 | heal_bloom | open flower of 8 broad petals around a round bud | bottom centre, opens upward | 1.6 Ø | ≤800 | 38 |
| 11 | impact_crater | flat ground crater ring: raised cracked rim, radial cracks, sunken centre | bottom centre, XZ | 2.4 Ø | ≤900 | 34 |
| 12 | energy_orb | sphere wrapped in two swirling shell bands (like a planet with crossed swirl ribbons) | centre | 0.6 Ø | ≤500 | 32 |
| 13 | tornado_funnel | funnel/whirlwind cone of 4 spiralling bands, open in the middle | bottom tip at origin, +Y | 2.4 tall | ≤900 | 27 |
| 14 | chain_ring | closed ring of 10 chunky chain links | centre, lies in XZ | 1.6 Ø | ≤900 | 25 |
| 15 | lightning_bolt | jagged zigzag thunderbolt pillar with 2 short side forks, chunky | bottom tip at origin, +Y | 3.0 tall | ≤400 | 25 |
| 16 | rock_debris | cluster of 5 chunky angular rock chunks (also used as a mesh-particle) | centre | 0.6 | ≤400 | 24 |
| 17 | ice_shard | single long faceted crystal shard, hexagonal, pointed both ends | centre, long axis +Z | 0.8 | ≤300 | 22 |
| 18 | shield_dome | half dome of hexagon panels with a thick rim at the base | bottom centre, +Y | 2.4 Ø | ≤1000 | 21 |
| 19 | energy_lance | long lance of light, diamond cross-section, ring guard 1/3 from the back | centre, tip +Z | 2.4 | ≤400 | 19 |
| 20 | sword_phantom | plain straight broad blade with a simple cross-guard, no ornament (spirit sword) | guard centre, blade +Y | 1.4 | ≤400 | 18 |
| 21 | feather | single broad stylised feather, slight S-curve | quill base, +Y | 0.6 | ≤300 | 18 |
| 22 | crystal_prism | faceted elongated gem/prism with a flat top (cut-gem look) | centre, +Y | 0.7 | ≤300 | 15 |
| 23 | rift_gate | vertical oval tear with jagged cracked rim, hollow centre | bottom centre, faces +Z | 2.6 tall | ≤900 | 14 |
| 24 | barrier_panel | curved shield wall: 3×3 hexagon panels on a gentle arc with a thick frame | bottom centre, concave side faces +Z | 2.4 wide | ≤800 | 13 |
| 25 | ice_spike_cluster | 7 ice spikes erupting from one cracked base, the middle one tallest | bottom centre, +Y | 1.8 tall | ≤800 | 9 |
| 26 | vine_coil | thorny vine twisting in a 2-turn open spiral | bottom centre, +Y | 1.6 tall | ≤800 | 6 |
| 27 | bite_jaws *(optional)* | upper + lower jaw rows of big rounded fangs, no skull | hinge centre, faces +Z | 1.2 | ≤600 | 3 |
| 28 | meteor_rock *(optional)* | round rock with deep glowing cracks (cracks as grooves) | centre | 1.0 Ø | ≤600 | 2 (signature ults) |

Optional ones go last; drop them if credits are short (the existing `meteor.png` / `bite.png` quads stay).

## 5. Asset contract (every effect mesh)

- **Image (ChatGPT web, GPT-6 Extra High, 4 candidates)**: the effect *shape* as a **solid matte sculpture**, so
  image-to-3D reads it as an object: "one solid stylised toon sculpture of <shape>, made of smooth matte white
  porcelain with soft light-grey shading in the grooves, chunky readable silhouette, no glow, no transparency, no
  particles, no motion blur, no text, runes or symbols, plain mid-grey background, three-quarter view, whole object
  with margins, 1:1". The colour/glow comes from Unity tint + additive shader, so the model must be white/grey.
- **Tripo**: H3.1 image→3D (55) → Retopo Triangle Smart Mesh (35) at the lowest offered target; export FBX, no rig.
- **Blender (headless, Sonnet worker)**: apply transforms; orient and pivot per §4; scale to the §4 size at scale 1;
  decimate (planar/collapse) to the tri budget; delete hidden/back interior faces; make normals consistent; **write a
  `Col` vertex colour layer**: RGB white, alpha = soft fade mask (edges/tips → 0.3, tail of `slash_crescent` and
  `energy_arrow` → 0, body → 1) because `VfxUnlit` multiplies vertex colour; UV: keep Tripo UVs, except
  `slash_crescent`/`nova_wave`/`tornado_funnel`/`chain_ring` get a **U along the sweep** (0→1 from tail to head) so
  `scroll` can sweep a highlight. One material slot, no armature, no animation. Export FBX (Unity axes, scale 1).
- **Texture**: convert the Tripo albedo to a **greyscale luminance mask** (levels: body ~0.6, grooves ~0.35, edge
  highlights ~0.8; VfxUnlit's cel ramp burns anything above ~0.72 to white, verified by the V0-R test 2026-10-12),
  256² (≤ 1.0 m meshes) or 512² (larger); PNG, sRGB, no alpha needed.
- **Axes**: Blender export forward `-Z`, up `Y` maps Blender +Y to Unity +Z; author projectiles with the tip on
  Blender +Y (the V0-R test dart came out reversed otherwise). Path
  `Resources/Vfx/Textures/mesh_<id>.png` (the generator validates texture files there).
- **Material**: none in the FBX (runtime builds `Abyss/VfxUnlit` per texture, `MaterialFor`). Additive by default;
  `alpha: true` layers for void/stone looks.
- **Budget**: ≤1000 tris each; whole library ≤18k tris; an effect may draw ≤6 mesh instances plus mesh particles
  (bursts capped by `maxParticles`).
- **Sidecar**: `ArtSource/vfx/<id>/candidates/prompts.md` (prompt, model check, pick + why, Tripo credits/balance,
  final tris, texture size).

## 6. Code hooks (small, isolated; mesh-less recipes behave exactly as today)

| id | file | change |
|---|---|---|
| H1 | `Scripts/Presentation/Vfx/VfxLibrary.cs` | `LayerRecipe` + `public string mesh; public float scroll;`. New cache `Dictionary<string, Mesh> _meshes` + `Mesh MeshFor(string id)`: `Resources.Load<GameObject>("Vfx/Meshes/" + id)` → first `MeshFilter.sharedMesh` in children, throw `InvalidOperationException("Missing VFX mesh: " + id)` like `MaterialFor`. **New kind `mesh`**: `AddMesh(go, MeshFor(r.mesh), material)`. **`orbit` + mesh**: children use the mesh and face along their tangent (`Quaternion.LookRotation(tangent)`) instead of `_viewRotation`. **`burst`/`emitter` + mesh**: `renderer.renderMode = ParticleSystemRenderMode.Mesh; renderer.mesh = MeshFor(..); renderer.alignment = ParticleSystemRenderSpace.Local; main.startRotation3D = true` (random XYZ unless `upright`). In `Tick`, for kind `mesh`: scale = lerp(size, endSize) with `height` as Y; rotation = `horizontal` → `Euler(0, roll, 0)`; `align` while travelling → `LookRotation(To − From) * Euler(0, 0, roll)`; otherwise yaw-to-camera (`LookRotation(flat(camera − position)) * Euler(0, 0, roll)`). `scroll ≠ 0` → `_MainTex_ST = (1, 1, p·scroll, 0)`. Ground pinning (`y ≤ −0.7`) works unchanged. |
| H2 | `Tools/vfx/gen_effects.py` | `allowed` += `mesh`, `scroll`; `kinds` += `mesh`; validation: a `mesh` field needs `Assets/_Game/Resources/Vfx/Meshes/<mesh>.fbx`, kind `mesh` requires the field. Builder `mesh_layer(mesh, color, life, size, end=0, **v)` (texture defaults to `mesh_<mesh>`). New `MESH_UPGRADES = {recipe_key: [layers]}` appended in `main()` **after** `effects_extra.json` merge and **before** `GROW`/`WIDEN`, so authored scale factors apply to mesh layers too. A key in `MESH_UPGRADES` without its FBX on disk is skipped with a printed warning (lets meshes land batch by batch). |
| H3 | `Tools/vfx/preview_effects.py` | skip `mesh` layers (print one warning per key); the Unity capture is the real check. |
| H4 | `Scripts/Runtime/Battle/BattleView.cs:1063` | hit-stop also slows VFX: `_vfx.TimeScale = _app.Paused ? 0 : _hitstop ? Speed * HitStopVfxRate : Speed;` with `const float HitStopVfxRate = .1f;`. Reduced mode is untouched (`HitStop` returns early at 1120). |
| H5 | `Scripts/Editor/AbyssArtImporter.cs` `OnPreprocessModel` | before the `IsArt` guard: if the path contains `/Resources/Vfx/Meshes/`: `materialImportMode = None`, `animationType = None`, `importAnimation = false`, `importBlendShapes = false`, `isReadable = false`, `globalScale = 1`, `useFileScale = true`, `importCameras = importLights = false`; return. |
| V-D | `Resources/Data/presentation.json` (data only) | clamp `hit_stop`/`shake`/`screen_flash` into the §2 family ranges (script, report the diff); `pr_ult_mage2.impact_vfx`: `critical` → `arcane_hit` (arcane ult currently borrows the blade crit). |

Order: H1+H2+H3+H5 land **before** any Tripo spend, tested with 2 Blender placeholder meshes (a cone and a torus with
`Col`, not shipped). H4 and V-D are independent.

## 7. Pilot and verification

- **V0 (0 credits)**: H1–H5, placeholder meshes on `slash` and `barrier`; regenerate `effects.json`; Unity compile +
  battle capture (540×960) of `attack_warrior`, `pr_c_barrier`, a multi-hit (`pr_w_combo`) and a projectile
  (`attack_archer`) — check orientation, ground pinning, pooling reuse, hit-stop slow-down, no exceptions.
- **VFX-1 pilot (6 meshes)**: `slash_crescent`, `energy_arrow`, `energy_orb`, `impact_crater`, `shield_dome`,
  `light_pillar` → upgrades for slash, twin_slash, critical, strong_hit, arrow (+ element arrows), orb_*, impact,
  blunt, stun_slam, barrier, protect, aegis, banish, revive. VERIFY: capture one skill per family touched,
  before/after strips, frame time unchanged within 10 %.
- **VFX-2 (10)**: ground_seal, thrust_spike, nova_wave, shadow_tendril, holy_cross, flame_plume, heal_bloom,
  lightning_bolt, ice_shard, rock_debris. **VFX-3 (10)**: tornado_funnel, chain_ring, energy_lance, sword_phantom,
  feather, crystal_prism, rift_gate, barrier_panel, ice_spike_cluster, vine_coil. **VFX-4 (optional 2)**: bite_jaws,
  meteor_rock. Each followed by V-D tuning for the families it completes and a capture of every ULT it touches.

## 8. Every skill → recipe (156 presentation rows, 300 skills)

Columns: family · presentation row · skills using it · recipe keys (C charge, T travel, I impact, A area) → mesh
layers added by `MESH_UPGRADES` · current feedback (hs hit_stop, sh shake, fl screen_flash). `x2/x3` = that many mesh
layers with staggered `delay`/`rotation`; `burst` = mesh particles; `orbit` = mesh orbit; `(big)/(huge)` ≈ size 1.6/2.4;
`-` = keep current particles. One key upgrade serves every row that uses the key.

| family | presentation | skills | recipe keys → meshes | feedback now |
|---|---|---|---|---|
| ARCANE | `attack_mage` | (class/enemy default attack) | T:bolt_dark → energy_orb; I:arcane_hit → crystal_prism burst | hs 0.06 · sh 0.25 · fl - |
| ARCANE | `pr_jb_starfall` | jb_am_starfall | C:magic_circle → ground_seal; I:arcane_hit → crystal_prism burst; A:prism_ray → crystal_prism+light_pillar(beam) | hs 0.09 · sh 0.5 · fl Y |
| ARCANE | `pr_m_prism` | jb_el_tri_burst, sk_m_prism, sig_rina | C:charge_grand → ground_seal+light_pillar(thin); T:bolt_holy → energy_lance(short); I:prism_hit → crystal_prism burst; A:prism_ray → crystal_prism+light_pillar(beam) | hs 0.06 · sh 0.34 · fl Y |
| ARCANE | `pr_ult_mage2` | ult_m_arcana_nova | C:charge_grand → ground_seal+light_pillar(thin); I:critical → slash_crescent+thrust_spike; A:arcana_nova → crystal_prism burst+nova_wave | hs 0.1 · sh 0.5 · fl Y |
| BLADE | `attack_party` | (class/enemy default attack) | I:slash → slash_crescent | hs 0.05 · sh 0.22 · fl - |
| BLADE | `attack_warrior` | (class/enemy default attack) | I:slash → slash_crescent | hs 0.07 · sh 0.28 · fl - |
| BLADE | `pr_bite` | sk_e_deep_bite, sk_e_shadow_bite, sk_twin_bite | I:twin_bite → bite_jaws | hs 0.06 · sh 0.3 · fl - |
| BLADE | `pr_slash_all` | sk_cleave, sk_e_black_wings | I:slash → slash_crescent; A:cleave_sweep → slash_crescent(horizontal, big) | hs 0.06 · sh 0.4 · fl - |
| BLADE | `pr_slash_bleed` | jb_be_blood_thirst, sk_bleed_edge | I:bleed_slash → slash_crescent | hs 0.07 · sh 0.38 · fl - |
| BLADE | `pr_w_combo` | jb_be_rend, sk_w_twin_slash, sig_dohyun | I:twin_slash → slash_crescent x2 | hs 0.06 · sh 0.3 · fl - |
| BLADE | `pr_w_crimson` | jb_wl_conquer, sk_w_crimson_fury | I:crimson_slash → slash_crescent x2; A:job_berserker → slash_crescent x3(red)+impact_crater | hs 0.06 · sh 0.34 · fl - |
| BLADE | `pr_w_power_break` | sk_w_power_break | I:power_break → slash_crescent+rock_debris | hs 0.08 · sh 0.45 · fl - |
| BLADE | `pr_w_whirlwind` | jb_be_rampage, sk_w_whirlwind, sig_bora | I:slash → slash_crescent; A:whirlwind → slash_crescent orbit(spin)+tornado_funnel | hs 0.05 · sh 0.4 · fl - |
| BLADE | `strong_attack` | jb_be_reckless, strong_attack | I:strong_hit → slash_crescent(big) | hs 0.08 · sh 0.4 · fl - |
| FIRE | `fireball` | fireball | C:charge_fire → ground_seal; T:orb_fire → energy_orb+flame_plume; I:fire → flame_plume burst | hs 0.08 · sh 0.42 · fl - |
| FIRE | `pr_a_blaze_rain` | sk_a_blaze_rain | I:fire_arrow_hit → thrust_spike+flame_plume; A:blaze_rain → energy_arrow burst(falling)+flame_plume | hs 0.06 · sh 0.38 · fl - |
| FIRE | `pr_arrow_fire` | sk_flame_arrow | T:arrow_fire → energy_arrow; I:fire_arrow_hit → thrust_spike+flame_plume | hs 0.07 · sh 0.4 · fl - |
| FIRE | `pr_breath` | sk_fire_breath, sk_lev_abyss_breath | C:charge_fire → ground_seal; I:fire → flame_plume burst; A:fire_breath → flame_plume burst(cone) | hs 0.07 · sh 0.42 · fl - |
| FIRE | `pr_fire_all` | sk_flame_wave, sig_taeyang | C:charge_fire → ground_seal; I:flame → flame_plume burst; A:flame_wave → nova_wave+flame_plume ring | hs 0.07 · sh 0.42 · fl - |
| FIRE | `pr_inferno` | sk_inferno | C:charge_fire → ground_seal; I:flame → flame_plume burst; A:inferno → flame_plume ring(tall)+tornado_funnel | hs 0.07 · sh 0.42 · fl - |
| FIRE | `pr_m_blaze` | jb_el_fire_spirit, sk_m_blaze | C:charge_fire → ground_seal; T:orb_fire → energy_orb+flame_plume; I:fire → flame_plume burst; A:blaze → flame_plume ring | hs 0.09 · sh 0.5 · fl - |
| FIRE | `pr_m_hellfire` | jb_el_eruption, sk_m_hellfire | C:charge_fire → ground_seal; I:flame → flame_plume burst; A:hellfire → impact_crater+flame_plume ring | hs 0.11 · sh 0.62 · fl Y |
| FIRE | `pr_solar_flare` | sk_solar_flare | C:charge_holy → ground_seal; I:fire → flame_plume burst; A:solar_flare → energy_orb(huge sun)+nova_wave | hs 0.07 · sh 0.42 · fl - |
| FIRE | `pr_sun_judgment` | sk_ex_solar_apocalypse, sk_sun_judgment | C:charge_holy → ground_seal; I:flame → flame_plume burst; A:sun_judgment → light_pillar+holy_cross+impact_crater | hs 0.08 · sh 0.45 · fl - |
| FIRE | `pr_w_blade_fire` | sk_w_flame_blade | C:enchant → sword_phantom(glint); I:blade_fire → slash_crescent+flame_plume | hs 0.08 · sh 0.45 · fl - |
| GUARD | `pr_a_focus` | jb_sn_steady_aim, sk_a_hawk_eye | C:charge_bow; I:hawk_eye → ground_seal(small) | hs 0 · sh 0 · fl - |
| GUARD | `pr_abyss_wall` | jb_ab_abyss_ward, sk_abyss_wall, sk_e_crystal_shell, sk_e_mirror_guard | C:charge_dark → ground_seal; I:abyss_wall → barrier_panel(void) | hs 0.0 · sh 0.0 · fl - |
| GUARD | `pr_buff_party` | (class/enemy default attack) | C:magic_circle → ground_seal; I:buff → nova_wave(small); A:area_buff → ground_seal+nova_wave | hs 0.0 · sh 0.0 · fl - |
| GUARD | `pr_buff_self` | (class/enemy default attack) | C:magic_circle → ground_seal; I:buff → nova_wave(small); A:aura → tornado_funnel(aura) | hs 0.0 · sh 0.0 · fl - |
| GUARD | `pr_c_barrier` | jb_ex_ward, jb_pr_holy_wall, sk_c_barrier | C:charge_holy → ground_seal; I:barrier → shield_dome | hs 0 · sh 0 · fl - |
| GUARD | `pr_c_haste` | jb_ra_wind_step, sk_c_haste | C:charge_holy → ground_seal; I:haste → tornado_funnel(small) | hs 0 · sh 0 · fl - |
| GUARD | `pr_c_hymn_swift` | jb_da_blessing_wind, jb_sa_angel_song, sk_c_hymn_swift | C:charge_holy → ground_seal; I:haste → tornado_funnel(small); A:hymn_swift → tornado_funnel(light) | hs 0.0 · sh 0.0 · fl - |
| GUARD | `pr_c_protect` | sk_c_protect | C:charge_holy → ground_seal; I:protect → shield_dome | hs 0 · sh 0 · fl - |
| GUARD | `pr_c_protect_all` | jb_kn_guard_aura, jb_pr_bless_all, sk_c_protect_all | C:charge_holy → ground_seal; I:guard → barrier_panel; A:protect_all → shield_dome(big) | hs 0.0 · sh 0.0 · fl - |
| GUARD | `pr_c_sanctuary` | jb_pa_sanctuary_guard, jb_sa_divine_shield, sk_sanctuary | C:charge_holy → ground_seal; I:regen → heal_bloom(small); A:sanctuary → ground_seal+shield_dome | hs 0.0 · sh 0.0 · fl - |
| GUARD | `pr_c_single_buff` | sk_c_blessing | C:charge_holy → ground_seal; I:blessing → ground_seal+feather burst | hs 0 · sh 0 · fl - |
| GUARD | `pr_harden` | sk_e_puff_up, sk_e_stone_skin, sk_harden | I:harden → shield_dome(stone)+rock_debris | hs 0.0 · sh 0.0 · fl - |
| GUARD | `pr_jb_veil` | jb_ss_shadow_veil | I:smoke | hs 0.0 · sh 0.0 · fl - |
| GUARD | `pr_m_focus` | jb_am_mana_tide, jb_el_resonance, sk_m_focus | I:mana_focus → crystal_prism orbit | hs 0 · sh 0 · fl - |
| GUARD | `pr_photosynthesis` | sk_photosynthesis | C:charge_heal → ground_seal; I:photosynthesis → heal_bloom | hs 0.0 · sh 0.0 · fl - |
| GUARD | `pr_sun_aegis` | sk_lord_crown, sk_sun_aegis | C:charge_holy → ground_seal; I:sun_aegis → shield_dome+light_pillar | hs 0.0 · sh 0.0 · fl - |
| GUARD | `pr_w_aegis` | jb_kn_fortress, jb_pa_divine_ward, sk_w_aegis, sig_dana | C:aura → tornado_funnel(aura); I:guard → barrier_panel; A:aegis → shield_dome(big) | hs 0 · sh 0 · fl - |
| GUARD | `pr_w_berserk` | jb_be_frenzy, sk_w_berserk, sig_gunwoo | I:blood_rage → flame_plume(red)+nova_wave | hs 0 · sh 0.3 · fl - |
| GUARD | `pr_w_iron_wall` | sk_iron_wall | C:aura → tornado_funnel(aura); I:guard → barrier_panel; A:iron_wall → barrier_panel x3 | hs 0.0 · sh 0.0 · fl - |
| GUARD | `pr_w_provoke` | jb_kn_vow, sk_provoke, sig_minjun | I:provoke_roar → nova_wave | hs 0.0 · sh 0.2 · fl - |
| GUARD | `pr_w_rally` | sk_w_rally | I:buff → nova_wave(small); A:warcry → nova_wave | hs 0 · sh 0.25 · fl - |
| GUARD | `pr_w_war_cry` | jb_wl_war_banner, sk_war_cry | C:warcry → nova_wave; I:buff → nova_wave(small); A:war_cry_party → nova_wave+ground_seal | hs 0.0 · sh 0.25 · fl - |
| HEAVY | `attack_enemy` | (class/enemy default attack) | I:impact → impact_crater | hs 0.06 · sh 0.25 · fl - |
| HEAVY | `pr_blunt_all` | jb_kn_rampart_crash, sk_e_dark_trample, sk_e_drowning_sweep, sk_e_shell_quake, sk_titan_crash | I:blunt → impact_crater+rock_debris; A:area_quake → impact_crater+rock_debris | hs 0.08 · sh 0.48 · fl - |
| HEAVY | `pr_heavy_enemy` | sk_e_anchor_smash, sk_e_burrow_strike, sk_e_clamp, sk_e_halberd, sk_e_stone_dive, sk_lev_tail_crush, sk_tentacle_crush | I:tentacle_crush → shadow_tendril+impact_crater | hs 0.09 · sh 0.5 · fl - |
| HEAVY | `pr_w_armor_break` | jb_be_skull_split, sk_w_armor_break | I:armor_break → slash_crescent+rock_debris | hs 0.09 · sh 0.48 · fl - |
| HEAVY | `pr_w_cataclysm` | jb_wl_earthshaker, sk_w_cataclysm | C:enchant → sword_phantom(glint); I:blunt → impact_crater+rock_debris; A:cataclysm → impact_crater(big)+rock_debris+nova_wave | hs 0.11 · sh 0.68 · fl Y |
| HEAVY | `stunning_slam` | jb_kn_shield_bash, sk_e_shell_bash, stunning_slam | I:stun_slam → impact_crater+rock_debris | hs 0.09 · sh 0.48 · fl - |
| HEX | `pr_curse_screech` | sk_curse_screech, sk_e_nightmare, sk_lord_eclipse | I:curse_screech → nova_wave+chain_ring | hs 0.03 · sh 0.15 · fl - |
| HEX | `pr_debuff` | jb_iq_interrogate, jb_wk_wither, sk_e_death_mark, sk_hex | C:magic_circle → ground_seal; I:debuff → chain_ring | hs 0.03 · sh 0.15 · fl - |
| HEX | `pr_dread_stare` | sk_dread_stare, sk_e_lure | C:charge_dark → ground_seal; I:dread_stare → shadow_tendril | hs 0.03 · sh 0.15 · fl - |
| HEX | `pr_hunter_mark` | sk_hunter_mark | C:charge_bow; I:hunter_mark → thrust_spike(down)+ground_seal | hs 0.03 · sh 0.15 · fl - |
| HEX | `pr_ink_cloud` | sk_ink_cloud | I:ink_cloud | hs 0.03 · sh 0.15 · fl - |
| HEX | `pr_jb_overlord` | jb_wl_overlord | C:aura → tornado_funnel(aura); I:debuff → chain_ring; A:warcry → nova_wave | hs 0.05 · sh 0.35 · fl - |
| HEX | `pr_lullaby` | sk_e_siren_song, sk_lullaby | C:charge_heal → ground_seal; I:lullaby → feather burst; A:sleep_mist → ground_seal | hs 0.03 · sh 0.15 · fl - |
| HEX | `pr_m_curse` | sk_m_curse | C:charge_dark → ground_seal; I:debuff → chain_ring; A:job_warlock → rift_gate+shadow_tendril burst | hs 0.03 · sh 0.2 · fl - |
| HEX | `pr_m_silence` | jb_ab_oblivion, jb_am_time_stop, jb_ex_spirit_chain, sk_m_silence | C:magic_circle → ground_seal; I:silence_hit → chain_ring; A:silence_field → chain_ring(big)+ground_seal | hs 0.03 · sh 0.15 · fl - |
| HEX | `pr_m_sleep` | jb_wk_nightmare, sk_m_sleep | C:magic_circle → ground_seal; I:sleep_hit; A:sleep_mist → ground_seal | hs 0 · sh 0 · fl - |
| HEX | `pr_riddle_silence` | sk_riddle_silence | C:magic_circle → ground_seal; I:riddle_silence → chain_ring | hs 0.03 · sh 0.15 · fl - |
| HEX | `pr_screech` | sk_lev_deep_roar, sk_screech | I:screech → nova_wave | hs 0.03 · sh 0.15 · fl - |
| HOLY | `attack_cleric` | (class/enemy default attack) | T:bolt_holy → energy_lance(short); I:light_hit → holy_cross(small) | hs 0.06 · sh 0.24 · fl - |
| HOLY | `holy_light` | holy_light | C:charge_holy → ground_seal; T:bolt_holy → energy_lance(short); I:holy → holy_cross(small) | hs 0.08 · sh 0.4 · fl - |
| HOLY | `pr_a_holy` | jb_da_sacred_arrow, sk_a_holy_arrow | T:arrow_holy → energy_arrow; I:holy_arrow_hit → thrust_spike+holy_cross(small) | hs 0.08 · sh 0.4 · fl - |
| HOLY | `pr_c_banish` | jb_ex_holy_seal, sk_c_banish, sig_eunbi | C:charge_holy → ground_seal; I:banish → light_pillar | hs 0.09 · sh 0.42 · fl - |
| HOLY | `pr_c_exorcism` | jb_ex_banishment, sk_c_exorcism, sig_youngsu | C:charge_holy → ground_seal; I:holy → holy_cross(small); A:job_exorcist → holy_cross+chain_ring | hs 0.09 · sh 0.48 · fl - |
| HOLY | `pr_c_holy_lance` | jb_ex_smite, jb_iq_crimson_cross, sk_c_holy_lance | C:charge_holy → ground_seal; I:light_hit → holy_cross(small); A:holy_lance → energy_lance(falling)+light_pillar | hs 0.09 · sh 0.5 · fl - |
| HOLY | `pr_c_inquisitor` | jb_iq_verdict, sk_c_judgment_cross, sig_mirae | C:charge_holy → ground_seal; I:holy → holy_cross(small); A:judgment_cross → holy_cross | hs 0.11 · sh 0.62 · fl Y |
| HOLY | `pr_holy_all` | jb_ex_purge, jb_sa_holy_nova, sk_divine_judgment, sk_e_pearl_beam | C:charge_holy → ground_seal; I:holy → holy_cross(small); A:area_holy → light_pillar x3 | hs 0.07 · sh 0.42 · fl - |
| HOLY | `pr_w_blade_holy` | jb_pa_holy_smite, sk_w_holy_blade | C:enchant → sword_phantom(glint); I:blade_holy → slash_crescent+holy_cross(small) | hs 0.08 · sh 0.48 · fl - |
| HOLY | `pr_w_grand_cross` | jb_pa_judgment_blade, sk_w_grand_cross | C:enchant → sword_phantom(glint); I:holy → holy_cross(small); A:grand_cross → holy_cross(ground, big) | hs 0.11 · sh 0.62 · fl Y |
| ICE | `pr_a_ice` | sk_a_ice_arrow | T:arrow_ice → energy_arrow; I:ice_arrow_hit → thrust_spike+ice_shard burst | hs 0.07 · sh 0.4 · fl - |
| ICE | `pr_blizzard` | sk_blizzard | C:charge_ice → ground_seal; I:ice → ice_shard burst; A:blizzard → tornado_funnel+ice_shard burst | hs 0.06 · sh 0.38 · fl - |
| ICE | `pr_freezing_tide` | sk_e_tidal_wave, sk_ex_abyss_tide, sk_freezing_tide, sk_lev_maelstrom | C:charge_ice → ground_seal; I:ice → ice_shard burst; A:freezing_tide → nova_wave+ice_spike_cluster | hs 0.07 · sh 0.42 · fl - |
| ICE | `pr_ice` | sk_e_water_jet, sk_ice_lance | C:charge_ice → ground_seal; T:lance_ice → ice_shard(long); I:ice_lance_hit → ice_shard burst | hs 0.08 · sh 0.45 · fl - |
| ICE | `pr_ice_all` | sk_frost_nova, sig_hana | C:charge_ice → ground_seal; I:ice → ice_shard burst; A:frost_nova → ice_spike_cluster | hs 0.07 · sh 0.42 · fl - |
| ICE | `pr_ice_shard` | sk_e_crystal_spike, sk_ice_shard | C:charge_ice → ground_seal; T:bolt_ice → ice_shard; I:ice → ice_shard burst | hs 0.07 · sh 0.4 · fl - |
| ICE | `pr_m_absolute_zero` | sk_m_absolute_zero | C:charge_ice → ground_seal; I:ice → ice_shard burst; A:absolute_zero → ice_spike_cluster+nova_wave | hs 0.11 · sh 0.62 · fl Y |
| ICE | `pr_m_glacier` | jb_el_frost_spirit, sk_m_glacier | C:charge_ice → ground_seal; I:ice → ice_shard burst; A:glacier_spike → ice_spike_cluster(big) | hs 0.09 · sh 0.52 · fl - |
| ICE | `pr_w_blade_ice` | sk_w_frost_blade | C:enchant → sword_phantom(glint); I:blade_ice → slash_crescent+ice_shard burst | hs 0.08 · sh 0.45 · fl - |
| NATURE | `poison_spore` | poison_spore | I:poison_hit → energy_orb burst(bubbles); A:spore_burst → energy_orb burst(bubbles) | hs 0.04 · sh 0.2 · fl - |
| NATURE | `pr_a_venom` | jb_ss_venom_fang, sk_a_venom_storm | I:poison_hit → energy_orb burst(bubbles); A:venom_rain → energy_arrow burst(falling)+energy_orb bubbles | hs 0.05 · sh 0.35 · fl - |
| NATURE | `pr_acid_spit` | sk_acid_spit | I:acid_spit → energy_orb burst(bubbles) | hs 0.05 · sh 0.25 · fl - |
| NATURE | `pr_arrow_poison` | sk_e_venom_fang, sk_poison_arrow | T:arrow_poison → energy_arrow; I:poison_hit → energy_orb burst(bubbles) | hs 0.05 · sh 0.28 · fl - |
| NATURE | `pr_root` | jb_ra_snare, sk_e_constrict, sk_root_bind | I:root_bind → vine_coil | hs 0.05 · sh 0.3 · fl - |
| NATURE | `pr_sand` | sk_sandstorm | I:smoke; A:sandstorm → tornado_funnel(sand) | hs 0.04 · sh 0.35 · fl - |
| NATURE | `pr_toxic_cloud` | jb_wk_plague, sk_toxic_cloud | I:poison_hit → energy_orb burst(bubbles); A:area_poison → energy_orb burst(bubbles) | hs 0.04 · sh 0.2 · fl - |
| NATURE | `pr_vine_lash` | sk_ex_ancient_wrath, sk_vine_lash | I:vine_lash → vine_coil | hs 0.05 · sh 0.3 · fl - |
| PIERCE | `attack_archer` | (class/enemy default attack) | T:arrow → energy_arrow; I:pierce → thrust_spike | hs 0.06 · sh 0.25 · fl - |
| PIERCE | `double_shot` | double_shot, sig_jiho | T:arrow → energy_arrow; I:pierce → thrust_spike | hs 0.06 · sh 0.28 · fl - |
| PIERCE | `pr_a_deadeye` | jb_da_true_shot, jb_sn_headshot, sk_a_deadeye, sig_siwoo | C:charge_bow; T:arrow → energy_arrow; I:critical → slash_crescent+thrust_spike; A:deadeye → energy_lance+thrust_spike(big) | hs 0.13 · sh 0.62 · fl Y |
| PIERCE | `pr_a_flash` | jb_sn_disarm, sk_a_flash_arrow | T:arrow → energy_arrow; I:pierce → thrust_spike; A:flash_burst → nova_wave | hs 0.05 · sh 0.35 · fl - |
| PIERCE | `pr_a_gale` | jb_ra_thorn_volley, jb_sn_suppress, sk_a_gale | I:pierce → thrust_spike; A:gale_dance → tornado_funnel+slash_crescent | hs 0.04 · sh 0.26 · fl - |
| PIERCE | `pr_a_piercing_gale` | jb_ra_storm_arrows, sk_piercing_gale, sig_iseul | T:arrow → energy_arrow; I:pierce → thrust_spike; A:piercing_gale → tornado_funnel(horizontal)+energy_arrow | hs 0.06 · sh 0.4 · fl - |
| PIERCE | `pr_a_triple` | jb_ra_quick_draw, sk_a_triple_shot | T:arrow → energy_arrow; I:pierce_triple → thrust_spike x3 | hs 0.05 · sh 0.26 · fl - |
| PIERCE | `pr_arrow_all` | jb_da_judgment_rain, sk_arrow_rain, sk_e_spike_burst | T:arrow → energy_arrow; I:pierce → thrust_spike; A:arrow_rain → energy_arrow burst(falling) | hs 0.05 · sh 0.35 · fl - |
| PIERCE | `pr_arrow_sleep` | sk_sleep_arrow | T:arrow_sleep → energy_arrow; I:sleep_hit | hs 0.04 · sh 0.2 · fl - |
| PIERCE | `pr_arrow_snipe` | jb_sn_aimed_shot, sk_e_coral_spear, sk_weak_point | C:charge_bow; T:arrow → energy_arrow; I:snipe_hit → thrust_spike(big) | hs 0.1 · sh 0.48 · fl - |
| PIERCE | `pr_crow_swarm` | jb_ra_falcon, sk_crow_swarm, sk_e_feather_storm, sk_e_tentacle_flail | I:pierce → thrust_spike; A:crow_swarm → feather burst | hs 0.05 · sh 0.26 · fl - |
| PIERCE | `pr_jb_armor_pierce` | jb_sn_armor_pierce | C:charge_bow; T:arrow → energy_arrow; I:snipe_hit → thrust_spike(big) | hs 0.08 · sh 0.35 · fl - |
| PIERCE | `pr_jb_lance` | jb_kn_lance_charge | I:void_pierce → thrust_spike+rift_gate(small) | hs 0.09 · sh 0.4 · fl - |
| SUPPORT | `heal` | heal, sig_yuna | C:charge_heal → ground_seal; I:heal → heal_bloom; A:heal_bloom → heal_bloom | hs 0.0 · sh 0.0 · fl - |
| SUPPORT | `pr_c_benediction` | jb_sa_grace, sk_c_benediction | C:charge_heal → ground_seal; I:regen → heal_bloom(small); A:job_priest → heal_bloom+light_pillar | hs 0 · sh 0 · fl - |
| SUPPORT | `pr_c_cleanse` | sk_cure | C:charge_heal → ground_seal; I:cleanse → heal_bloom+nova_wave | hs 0 · sh 0 · fl - |
| SUPPORT | `pr_c_purify_all` | sk_c_purify_all | C:charge_heal → ground_seal; I:cleanse → heal_bloom+nova_wave; A:purify_light → light_pillar+nova_wave | hs 0 · sh 0 · fl - |
| SUPPORT | `pr_c_regen` | jb_pr_renew, sk_c_regen | C:charge_heal → ground_seal; I:regen → heal_bloom(small) | hs 0 · sh 0 · fl - |
| SUPPORT | `pr_c_resurrection` | sk_c_resurrection | C:charge_holy → ground_seal; I:revive → light_pillar+feather burst; A:area_revive → light_pillar+feather burst | hs 0 · sh 0 · fl Y |
| SUPPORT | `pr_greater_heal` | jb_pr_full_heal, sk_greater_heal, sig_jaehyun | C:charge_heal → ground_seal; I:heal → heal_bloom; A:greater_heal → heal_bloom+light_pillar | hs 0.0 · sh 0.0 · fl - |
| SUPPORT | `pr_heal_all` | jb_iq_absolution, jb_pr_prayer, sk_e_naga_hymn, sk_heal_all | C:charge_heal → ground_seal; I:heal → heal_bloom; A:area_heal → heal_bloom(big) | hs 0.0 · sh 0.0 · fl - |
| SUPPORT | `pr_rebirth_flame` | sk_rebirth_flame | C:charge_fire → ground_seal; I:heal → heal_bloom; A:rebirth_flame → flame_plume+feather burst | hs 0.0 · sh 0.0 · fl - |
| SUPPORT | `pr_revive` | jb_pr_revive_light, sk_revive | C:charge_holy → ground_seal; I:revive → light_pillar+feather burst | hs 0.0 · sh 0.0 · fl - |
| THUNDER | `pr_a_thunder` | sk_a_thunder_arrow | T:arrow_thunder → energy_arrow; I:thunder_arrow_hit → thrust_spike+lightning_bolt(small) | hs 0.08 · sh 0.42 · fl - |
| THUNDER | `pr_chain_spark` | sk_chain_spark | C:charge_thunder → ground_seal; T:orb_spark → energy_orb; I:chain_spark_hit → lightning_bolt(small) | hs 0.05 · sh 0.26 · fl - |
| THUNDER | `pr_m_indra` | sk_m_indra | C:charge_thunder → ground_seal; I:thunder → lightning_bolt; A:indra → lightning_bolt x3(huge) | hs 0.11 · sh 0.65 · fl Y |
| THUNDER | `pr_m_lightning` | jb_el_storm_spirit, sk_m_lightning | C:charge_thunder → ground_seal; I:spark_hit → lightning_bolt(small); A:lightning_bolt → lightning_bolt | hs 0.09 · sh 0.52 · fl - |
| THUNDER | `pr_thunder` | sk_e_thunder, sk_m_spark, sig_seoa | C:charge_thunder → ground_seal; T:orb_spark → energy_orb; I:spark_hit → lightning_bolt(small) | hs 0.06 · sh 0.35 · fl - |
| THUNDER | `pr_thunder_all` | sk_e_thunder_all, sk_lev_thunder_fin, sk_thunder_storm | C:charge_thunder → ground_seal; I:thunder → lightning_bolt; A:thunder_storm → lightning_bolt x4 | hs 0.07 · sh 0.42 · fl - |
| THUNDER | `pr_w_blade_thunder` | sk_w_thunder_blade | C:enchant → sword_phantom(glint); I:blade_thunder → slash_crescent+lightning_bolt(small) | hs 0.08 · sh 0.48 · fl - |
| ULT/ARCANE | `pr_jb_elementalist` | ult_jb_elementalist | C:charge_grand → ground_seal+light_pillar(thin); I:prism_hit → crystal_prism burst; A:job_elementalist → crystal_prism+flame_plume+ice_shard+lightning_bolt | hs 0.11 · sh 0.55 · fl Y |
| ULT/BLADE | `pr_jb_berserker` | ult_jb_berserker | C:charge_grand → ground_seal+light_pillar(thin); I:crimson_slash → slash_crescent x2; A:job_berserker → slash_crescent x3(red)+impact_crater | hs 0.11 · sh 0.55 · fl Y |
| ULT/BLADE | `pr_jb_knight` | ult_jb_knight | C:charge_grand → ground_seal+light_pillar(thin); I:critical → slash_crescent+thrust_spike; A:job_knight → sword_phantom orbit+shield_dome | hs 0.11 · sh 0.55 · fl Y |
| ULT/BLADE | `pr_ult_warrior` | ult_heaven_rend | C:charge_grand → ground_seal+light_pillar(thin); I:critical → slash_crescent+thrust_spike; A:ultimate_warrior → sword_phantom orbit+slash_crescent(huge) | hs 0.13 · sh 0.7 · fl Y |
| ULT/BLADE | `pr_ult_warrior2` | ult_w_ragnarok | C:charge_grand → ground_seal+light_pillar(thin); I:critical → slash_crescent+thrust_spike; A:ultimate_warrior2 → slash_crescent cross(huge)+nova_wave | hs 0.12 · sh 0.6 · fl Y |
| ULT/FIRE | `pr_jb_archmage` | ult_jb_archmage | C:charge_grand → ground_seal+light_pillar(thin); I:flame → flame_plume burst; A:job_archmage → meteor_rock+ground_seal | hs 0.11 · sh 0.55 · fl Y |
| ULT/FIRE | `pr_ult_mage` | ult_meteor | C:charge_grand → ground_seal+light_pillar(thin); I:flame → flame_plume burst; A:ultimate_mage → meteor_rock+impact_crater+flame_plume ring | hs 0.1 · sh 0.5 · fl Y |
| ULT/HEAVY | `pr_jb_warlord` | ult_jb_warlord | C:charge_grand → ground_seal+light_pillar(thin); I:critical → slash_crescent+thrust_spike; A:job_warlord → impact_crater(big)+rock_debris+nova_wave | hs 0.11 · sh 0.55 · fl Y |
| ULT/HOLY | `pr_jb_divine_archer` | ult_jb_divine_archer | C:charge_grand → ground_seal+light_pillar(thin); I:holy_arrow_hit → thrust_spike+holy_cross(small); A:job_divine_archer → energy_arrow burst(falling)+feather burst | hs 0.11 · sh 0.55 · fl Y |
| ULT/HOLY | `pr_jb_exorcist` | ult_jb_exorcist | C:charge_grand → ground_seal+light_pillar(thin); I:holy → holy_cross(small); A:job_exorcist → holy_cross+chain_ring | hs 0.11 · sh 0.55 · fl Y |
| ULT/HOLY | `pr_jb_inquisitor` | ult_jb_inquisitor | C:charge_grand → ground_seal+light_pillar(thin); I:judgment_cross → holy_cross; A:job_inquisitor → holy_cross+energy_lance(falling) | hs 0.11 · sh 0.55 · fl Y |
| ULT/HOLY | `pr_jb_paladin` | ult_jb_paladin | C:charge_grand → ground_seal+light_pillar(thin); I:holy → holy_cross(small); A:job_paladin → holy_cross+light_pillar+shield_dome | hs 0.11 · sh 0.55 · fl Y |
| ULT/HOLY | `pr_ult_archer2` | ult_a_heaven_arrow | C:charge_grand → ground_seal+light_pillar(thin); I:holy_arrow_hit → thrust_spike+holy_cross(small); A:job_divine_archer → energy_arrow burst(falling)+feather burst | hs 0.1 · sh 0.45 · fl Y |
| ULT/PIERCE | `pr_jb_ranger` | ult_jb_ranger | C:charge_grand → ground_seal+light_pillar(thin); T:arrow → energy_arrow; I:pierce → thrust_spike; A:job_ranger → energy_arrow burst+vine_coil | hs 0.11 · sh 0.55 · fl Y |
| ULT/PIERCE | `pr_jb_sniper` | ult_jb_sniper | C:charge_grand → ground_seal+light_pillar(thin); T:arrow → energy_arrow; I:snipe_hit → thrust_spike(big); A:job_sniper → energy_lance+thrust_spike(big) | hs 0.11 · sh 0.55 · fl Y |
| ULT/PIERCE | `pr_ult_archer` | ult_starfall_volley | C:charge_grand → ground_seal+light_pillar(thin); T:arrow → energy_arrow; I:pierce → thrust_spike; A:ultimate_archer → energy_arrow burst(falling)+light_pillar | hs 0.07 · sh 0.32 · fl Y |
| ULT/SUPPORT | `pr_jb_priest` | ult_jb_priest | C:charge_grand → ground_seal+light_pillar(thin); I:heal → heal_bloom; A:job_priest → heal_bloom+light_pillar | hs 0.11 · sh 0.55 · fl Y |
| ULT/SUPPORT | `pr_jb_saint` | ult_jb_saint | C:charge_grand → ground_seal+light_pillar(thin); I:revive → light_pillar+feather burst; A:job_saint → feather burst+light_pillar+heal_bloom | hs 0.11 · sh 0.55 · fl Y |
| ULT/SUPPORT | `pr_ult_cleric` | ult_seraph_hymn | C:charge_grand → ground_seal+light_pillar(thin); I:heal → heal_bloom; A:ultimate_cleric → heal_bloom(huge)+feather burst | hs 0.0 · sh 0.0 · fl Y |
| ULT/SUPPORT | `pr_ult_cleric2` | ult_c_miracle | C:charge_grand → ground_seal+light_pillar(thin); I:heal → heal_bloom; A:job_saint → feather burst+light_pillar+heal_bloom | hs 0 · sh 0 · fl Y |
| ULT/VOID | `pr_jb_abyssal` | ult_jb_abyssal | C:charge_grand → ground_seal+light_pillar(thin); I:void_pierce → thrust_spike+rift_gate(small); A:job_abyssal → rift_gate+energy_lance(void) | hs 0.11 · sh 0.55 · fl Y |
| ULT/VOID | `pr_jb_shadow_stalker` | ult_jb_shadow_stalker | C:charge_grand → ground_seal+light_pillar(thin); I:critical → slash_crescent+thrust_spike; A:job_shadow_stalker → sword_phantom orbit(void)+slash_crescent | hs 0.11 · sh 0.55 · fl Y |
| ULT/VOID | `pr_jb_warlock` | ult_jb_warlock | C:charge_grand → ground_seal+light_pillar(thin); I:dark → shadow_tendril; A:job_warlock → rift_gate+shadow_tendril burst | hs 0.11 · sh 0.55 · fl Y |
| VOID | `pr_a_phantom` | jb_ss_night_raid, sk_a_phantom_raid, sig_jun | I:slash → slash_crescent; A:phantom_raid → sword_phantom orbit+slash_crescent | hs 0.05 · sh 0.3 · fl - |
| VOID | `pr_a_shadow` | jb_ss_assassinate, sk_a_shadow_stitch, sig_sora | T:arrow_shadow → energy_arrow; I:shadow_stitch → thrust_spike+chain_ring | hs 0.08 · sh 0.42 · fl - |
| VOID | `pr_dark` | jb_wk_hex_bolt, sk_abyss_bolt, sk_e_trident, sk_e_void_gaze, sk_m_shadow_bolt | C:charge_dark → ground_seal; T:bolt_dark → energy_orb; I:dark → shadow_tendril | hs 0.07 · sh 0.4 · fl - |
| VOID | `pr_dark_all` | sk_abyss_wave, sk_lord_dominion | C:charge_dark → ground_seal; I:dark → shadow_tendril; A:abyss_wave → nova_wave(void) | hs 0.07 · sh 0.42 · fl - |
| VOID | `pr_harvest_reap` | sk_e_void_scythe, sk_harvest_reap | I:slash → slash_crescent; A:harvest_reap → slash_crescent(horizontal, big) | hs 0.06 · sh 0.4 · fl - |
| VOID | `pr_m_abyss_gate` | jb_ab_void_rift, sk_ex_true_void, sk_lord_annihilation, sk_m_abyss_gate, sig_haneul | C:charge_dark → ground_seal; I:dark → shadow_tendril; A:abyss_gate → rift_gate(big)+shadow_tendril burst | hs 0.11 · sh 0.65 · fl Y |
| VOID | `pr_m_drain` | jb_wk_soul_drain, sk_e_devour, sk_lord_soul_drain, sk_m_drain | C:charge_dark → ground_seal; I:dark → shadow_tendril; A:drain → shadow_tendril+energy_orb(return) | hs 0.07 · sh 0.4 · fl - |
| VOID | `pr_soul_reap` | jb_ab_soul_harvest, sk_ex_requiem, sk_soul_reap | C:charge_dark → ground_seal; I:dark → shadow_tendril; A:soul_reap → slash_crescent(void)+shadow_tendril | hs 0.07 · sh 0.42 · fl - |
| VOID | `pr_spirit_fire` | sk_spirit_fire | C:charge_dark → ground_seal; T:orb_spirit → energy_orb; I:spirit_fire_hit → flame_plume(alpha) | hs 0.07 · sh 0.38 · fl - |
| VOID | `pr_void_lance` | jb_am_annihilate, jb_wk_doom, sk_e_mirror_strike, sk_void_lance | C:charge_dark → ground_seal; T:lance_void → energy_lance; I:void_pierce → thrust_spike+rift_gate(small) | hs 0.09 · sh 0.48 · fl - |
| VOID | `pr_w_giga` | sk_e_fallen_blade, sk_lord_void_blade, sk_w_giga_slash | C:enchant → sword_phantom(glint); I:blade_thunder → slash_crescent+lightning_bolt(small); A:giga_slash → slash_crescent(huge)+lightning_bolt | hs 0.1 · sh 0.62 · fl Y |

`basic_attack` has no `presentation`; it plays the actor default rows above (`attack_warrior/party/archer/mage/cleric/enemy`), so it is covered by those upgrades.
