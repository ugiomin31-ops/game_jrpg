# mushroom (enemies, Floor-2 zone 2, rank 0) — ChatGPT web candidates, 2026-10-13

Model check before send: model menu GPT-6 aria-checked=true; reasoning slider aria-valuenow=3 max=4 (Extra High, 4th of 5).
Chat: https://chatgpt.com/c/6acd6b8a-c7f8-83e8-a481-459329cffa2b
Brief source: Assets/_Game/Resources/Data/enemies.json row id mushroom: display_name 독버섯; text_ko enemy_desc_mushroom "독 포자를 흩뿌리는 버섯 마물. 해독 준비는 필수." (mushroom monster that scatters toxic spores). Style rules: ArtSource/_briefs/enemies.md (mushroom: Base light, cream cap and stem, pale spots; H rig, size S; brief "A stubby walking mushroom with a big round cap, little stem legs and arms, spore puffs as solid bumps").
Prompt (sent exactly as below):

Generate FOUR separate standalone images in this one response, each its own image, not a grid or contact sheet. One cute chunky toon mushroom monster for a modern Seoul hunter RPG: a stubby walking mushroom with a big round cap, short stem legs and two stubby arms, soft bumps of spore puffs on the cap, a poison mushroom that scatters toxic spores. Cream cap and stem with pale spots. It will become a 3D model via image-to-3D and be rigged as a humanoid. Stylised game-ready 3D asset look, clean toon shapes, chunky readable silhouette, 3D-modelling reference sheet feel, single subject centered, full body visible with margins, 3/4 front view in a neutral stance with arms clear of the body and feet apart, plain light-grey background, soft neutral shading, no shadow, square 1:1. Matte, opaque; small recessed non-emissive eyes; no glow; no text, logos, UI, symbols, crown, cape, medieval armour, skulls, runes, gold filigree or fantasy ornament. Vary cap size, stem height and spot pattern within the brief.

Results (one response, 4 images): candidate_A.png .. candidate_D.png.
pick: candidate_B.png. Reason: smooth cream body, arms and legs clearly separated, cap bumps are solid spore puffs, cute face; A has fur strands that will not survive retopo. Alternative: candidate_C.png

## Tripo (B6-TRIPO-2, 2026-10-13, third account, quality-first)
- Picked image: candidate_B.png (pick line above), uploaded exactly.
- Generate: task 89c1a712-4d78-4591-a8b9-4c9a5300fda7. H3.1 Best Quality, Ultra Mesh on, Texture on, 4K (55), PBR on, Triangle. Cost 55, balance 1010 -> 955.
- Retopo: Triangle + Smart Mesh on, 10000 (verified by zoom before click), cost 35, balance 955 -> 920. Actual faces 9506.
- Rig: Humanoid, Mixamo, Auto Rig 20, balance 920 -> 900. No T-pose charge.
- Animate (free presets): idle, walk, chop (attack substitute), hit_to_body_01, defeat (death/fall substitute), cheer (victory). An extra "afraid" take from a misclick was excluded from the export.
- Export: FBX, Blender preset, texture 2k, Export Skeleton on, 6 animations, stay-in-place off.
- Local: ArtSource/enemies/mushroom/tripo/tripo_convert_dc64106f-9441-4071-bae2-178f0a8833be.fbx (+ .fbm). Zip kept as mushroom+creature+3d+model.zip.
- Blender skin-weight check: NOT run. OPEN.


### Installed 2026-10-13 (INSTALL-B6-2, Claude Sonnet, headless Blender 5.2.1, no credits)
- Assets/_Game/Resources/Art/Enemies/mushroom/mushroom.fbx (+ TRIPO marker, mushroom_tex/mushroom.png raw 2048 px, pixel-identical). Old model + meta backed up in ArtSource/_backup_20261013_b6_2/enemies/ (GUID kept). Generic rig (same convention as sewer_rat/horned_rabbit): armature Rig (65 Mixamo bones), skinned mesh Body, one material mushroom, white Col.
- Rig gate on the raw export: 0 of 4755 verts unweighted (0 %), weight sums 1.0; LeftArm/RightArm/LeftUpLeg/RightUpLeg 45 deg and a 6-pose posing test deform with no NaN and no torn faces (edges stretching >3x: 4 of ~14265 at the extreme Head 45 deg pose, same as raw). Fresh-import checks of the installed FBX: tris 9506 = raw 9506, UV multiset 100%, uniform scale 0.97140 (rest height 0.95 m, 0.78 x 0.71), anisotropy 1.0, weights identical to raw (0 mismatches, max dw 0.0), rest bones = raw x scale within 4.8e-07 m (connected bones unscaled-twice: edit bones disconnected before scaling).
- Scale: uniform, scale 0.97140 (rest height 0.95 m, 0.78 x 0.71).
- Takes (exported as Rig|<name>): Idle=idle 369, Run=walk 57 (Hips fore/aft travel of 0.60 m per cycle removed = in-place, otherwise the body slid and snapped back each loop), Attack=chop 27-86 trimmed to 60 frames (strike at ~40 %), Hit=hit_to_body_01 32, Die=defeat_02 204 (untrimmed), Victory=cheer 291, Cast=cheer 20-79 (60 frames, a copy so BattleView's Cast / boss phase has a short take; no Tripo cast preset exists). No keys authored. Floor offsets (constant per clip on the Hips location, from the foot vertices; Die per frame for fall): Attack constant 0.0696; Cast constant 0.0441; Die constant 0.045; Hit constant 0.0782; Idle constant 0.057; Run constant 0.0885; Victory constant 0.0451. Per clip after the fix the lowest foot vertex is 0.000 m.
- Strips (raw and installed, 6 frames per take): scratchpad install_b6_2/strips/sheet_raw_mushroom.png and sheet_stage_mushroom.png; raw vs installed: install_b6_2/sbs/sheet_mon_sbs.png.
