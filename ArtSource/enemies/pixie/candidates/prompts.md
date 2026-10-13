# pixie (enemies, Floor-2 zone 2, rank 0) — ChatGPT web candidates, 2026-10-13

Model check before send: model menu GPT-6 aria-checked=true; reasoning slider aria-valuenow=3 max=4 (Extra High, 4th of 5).
Chat: https://chatgpt.com/c/6acd6c11-d0d8-83ee-bd66-6e097d1d481b
Brief source: Assets/_Game/Resources/Data/enemies.json row id pixie: display_name 숲의 요정; text_ko enemy_desc_pixie "꽃잎 옷을 입은 숲의 요정. 동료를 치유하니 먼저 쓰러뜨리자." (forest fairy in a petal dress that heals allies, take it down first). Style rules: ArtSource/_briefs/enemies.md (pixie: Base light, H rig, size S; brief "A tiny fairy in a flower-petal dress with four rounded wings, holding nothing").
Prompt (sent exactly as below):

Generate FOUR separate standalone images in this one response, each its own image, not a grid or contact sheet. One cute chunky toon fairy creature for a modern Seoul hunter RPG: a tiny forest fairy in a flower-petal dress, four rounded wings attached to its back and spread, short limbs, a round cute face and small recessed non-emissive eyes, holding nothing. Pale and soft pastel petal colours. It will become a 3D model via image-to-3D and be rigged as a humanoid. Stylised game-ready 3D asset look, clean toon shapes, chunky readable silhouette, 3D-modelling reference sheet feel, single subject centered, full body visible with margins, 3/4 front view in a neutral stance with arms clear of the body and feet apart, plain light-grey background, soft neutral shading, no shadow, square 1:1. Matte, opaque; no glow; no text, logos, UI, symbols, crown, cape, medieval armour, skulls, runes, gold filigree or fantasy ornament. Vary wing shape, petal dress layers and hair within the brief.

Results (one response, 4 images): candidate_A.png .. candidate_D.png.
pick: candidate_D.png. Reason: four rounded petal wings as the brief asks, soft pastel palette, arms and legs clear of the body; C's wings are thin translucent blades. Alternative: candidate_C.png

## Tripo (B6-TRIPO-2, 2026-10-13, third account, quality-first)
- Picked image: candidate_D.png (pick line above), uploaded exactly.
- Generate: task c8d69352-34a1-41c0-8096-680b948f8206. H3.1 Best Quality, Ultra Mesh on, Texture on, 4K (55), PBR on, Triangle. Cost 55, balance 900 -> 845.
- Retopo: Triangle + Smart Mesh on, 10000 (verified before click), cost 35, balance 845 -> 810. Actual faces 9752.
- Rig: Humanoid, Mixamo, Auto Rig 20, balance 810 -> 790. No T-pose charge.
- Animate (free presets): idle, walk, chop (attack substitute), hit_to_body_01, defeat (death/fall substitute), cheer (victory).
- Export: FBX, Blender preset, texture 2k, Export Skeleton on, 6 animations, stay-in-place off.
- Local: ArtSource/enemies/pixie/tripo/tripo_convert_e4987680-86f4-4c9b-8a2d-aa97a8c93674.fbx (+ .fbm). Zip kept as fairy+character+3d+model.zip.
- Blender skin-weight check: NOT run. OPEN.


### Installed 2026-10-13 (INSTALL-B6-2, Claude Sonnet, headless Blender 5.2.1, no credits)
- Assets/_Game/Resources/Art/Enemies/pixie/pixie.fbx (+ TRIPO marker, pixie_tex/pixie.png raw 2048 px, pixel-identical). Old model + meta backed up in ArtSource/_backup_20261013_b6_2/enemies/ (GUID kept). Generic rig (same convention as sewer_rat/horned_rabbit): armature Rig (65 Mixamo bones), skinned mesh Body, one material pixie, white Col.
- Rig gate on the raw export: 0 of 4874 verts unweighted (0 %), weight sums 1.0; LeftArm/RightArm/LeftUpLeg/RightUpLeg 45 deg and a 6-pose posing test deform with no NaN and no torn faces (edges stretching >3x: 17 of ~14622 at the extreme Head 45 deg pose, same as raw). Fresh-import checks of the installed FBX: tris 9752 = raw 9752, UV multiset 100%, uniform scale 0.71528 (rest height 0.70 m, 0.66 x 0.35), anisotropy 1.0, weights identical to raw (0 mismatches, max dw 0.0), rest bones = raw x scale within 4.1e-07 m (connected bones unscaled-twice: edit bones disconnected before scaling).
- Scale: uniform, scale 0.71528 (rest height 0.70 m, 0.66 x 0.35).
- Takes (exported as Rig|<name>): Idle=idle 369, Run=walk 57 (Hips fore/aft travel of 1.04 m per cycle removed = in-place, otherwise the body slid and snapped back each loop), Attack=chop 27-86 trimmed to 60 frames (strike at ~40 %), Hit=hit_to_body_01 32, Die=defeat_02 204 (untrimmed), Victory=cheer 291, Cast=cheer 20-79 (60 frames, a copy so BattleView's Cast / boss phase has a short take; no Tripo cast preset exists). No keys authored. Floor offsets (constant per clip on the Hips location, from the foot vertices; Die per frame for fall): Attack constant 0.0209; Cast constant 0.0149; Die constant 0.0128; Hit constant 0.0196; Idle constant 0.016; Run constant 0.0205; Victory constant 0.0152. Per clip after the fix the lowest foot vertex is 0.000 m.
- Strips (raw and installed, 6 frames per take): scratchpad install_b6_2/strips/sheet_raw_pixie.png and sheet_stage_pixie.png; raw vs installed: install_b6_2/sbs/sheet_mon_sbs.png.
