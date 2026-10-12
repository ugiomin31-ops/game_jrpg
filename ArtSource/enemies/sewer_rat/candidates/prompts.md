
## B3 candidates (ChatGPT web, GPT-6 Extra High, 2026-10-12, Haiku worker BROWSER-QUEUE 2b)
- Chat URL: https://chatgpt.com/c/6acbb765-9d00-83e8-9f5a-32b6b180898c (model GPT-6, reasoning slider 3/4 = Extra High, checked before sending)
- Prompt (lead + brief + creature frame, from ArtSource/_briefs/B3_prompts.md): "Generate FOUR separate standalone images in this one response, each its own image, not a grid or collage. One plump grey-brown subway burrowing rat wearing a thick attached yellow safety helmet and a simple painted high-visibility belly band. Large front incisors, compact ears and a thick tail attached close to the body. It stands upright on two separated feet, two distinct paw arms spread diagonally downward, palms empty, front view. Keep a rat muzzle, not a human face. One complete creature per image, chunky cute modern Seoul hunter-game toon 3D style, small socketed non-emissive eyes, glow only inside small blue/violet rift cracks, plain light-grey background, generous margins, square 1:1. No text, logos, crowns, capes, medieval ornament, transparent geometry, floating effects or thin dangling parts. Vary proportions and colour accents slightly between the four images while keeping the description."
- candidate_A.png: pass. Single creature, plain grey background, attached helmet, simple painted yellow/white band, violet cracks only, two separated feet, tail attached, rat muzzle. Arms are spread slightly down.
- candidate_B.png: pass with note. Single creature, helmet and painted band attached, cracks violet only. Stance is more upright and slimmer; the band has a small amount of extra hardware-like seam detail.
- candidate_C.png: reject-leaning. Band has metal buckles and shoulder straps (extra hardware beyond "simple painted band"); arms reach out to the side rather than diagonally down.
- candidate_D.png: reject-leaning. Band has shoulder straps and buckles (suspender look) and glowing cracks on the arms; still a single creature with a rat muzzle.
- Suggested pick: candidate_A.png (closest to the brief's simple painted band and clean silhouette). Main session makes the final pick.

## Tripo second account (2026-10-12, Haiku worker B3-TRIPO)
- Main final pick: candidate_A.png (main-approved pick)
- Source: https://studio.tripo3d.ai (Tripo Studio web, HD Model, Geometry & Texture, AI Model H3.1 - Best Quality, expected 55 credits)
- Task: ef092883-33c5-44d4-b1df-75c664f58af2  URL https://studio.tripo3d.ai/workspace/generate/ef092883-33c5-44d4-b1df-75c664f58af2
- Generate cost: 55 credits; 3260 -> 3205
- Retopo: Triangle, Smart Mesh on, target 5000 -> 4551 faces / 6605 vertices (cost 35; balance 2710 -> 2675). Off-target: none (within 3k-6k small-enemy band).
- Rig: Humanoid, Mixamo skeleton, Auto Rig (cost 20; balance 2675 -> 2655). Skeleton visible in viewport. Skin-weight check in Blender: OPEN (not run by this worker).
- Animations (free presets, no cost, balance unchanged 2655): idle, run, slash, cast_a_spell, hit_to_body_01, defeat (6/6).
- Export: FBX (Blender preset), texture 2k, Export Skeleton on, 6 animations. Downloaded construction+rat+3d+model.zip (12.5 MB) and extracted to tripo/ .
- Export path: ArtSource/enemies/sewer_rat/tripo/tripo_convert_7c268648-2e31-481a-9760-2d1ea1c6e368.fbx (+ .fbm textures). Export ID 7c268648.
- Credits spent on this asset: 110 generate+retopo+rig (55+35+20); animations 0.

## Installed 2026-10-12 (Sonnet 5.5 worker S14 B3-ENEMIES, own model, headless Blender 5.2.1)
- Source: tripo/tripo_convert_*.fbx (Humanoid/Mixamo, 4551 tris, 2305 verts, 65 bones, 6 takes). No Tripo/ChatGPT generation, no credits; actions only renamed/trimmed, nothing authored.
- Rig gate (source and again on the exported FBX): 0 unweighted of 2305; LeftArm 354 / RightArm 344 / LeftUpLeg 546 / RightUpLeg 537 verts moved >1 cm (45 deg), max 0.18 / 0.18 / 0.135 / 0.135 m. Passed.
- Takes renamed (Tripo -> clip, frames 1-based): idle -> Idle 1-369, run -> Run 1-31, slash -> Attack, cast_a_spell -> Cast, hit_to_body_01 -> Hit 1-32, defeat_02 -> Die 1-204. Exactly these 6 exported as takes Rig|Idle, Rig|Run, Rig|Attack, Rig|Cast, Rig|Hit, Rig|Die (old model had 7 incl. Victory; enemies do not need Victory). Bones in QUATERNION mode, no stale actions, armature `Rig`, skinned mesh `Body`, one material `sewer_rat`, white `Col`.
- Trim (keys only deleted and shifted, same windows as festival_pumpkin_king since it is the same Tripo preset): Attack source slash 27-86 -> 60 frames (was 159), hand-speed peak / strike at source ~50-51 -> frame ~25 of 60 = ~41% (BattleView 40%). Cast source cast_a_spell 32-85 -> 54 frames (was 130), thrust release at source ~64 -> frame 33 of 54 = ~61% (BattleView 60%). Trim only, no keyframe authored; ends are not blended back to Idle (runtime cross-fades).
- Scale: uniform, to the old model's rest height. Old: 0.837 (old rest bounds 0.456 x 1.021 incl. tail x 0.837). New: 0.837 tall, 0.837 wide (arms out) x 0.785 deep; scale x0.85596 from 0.9778. Bones, mesh and Hips location keys were scaled together (armature object stays x1.0).
- Idle frame 1 z -0.026..0.840; lowest vertex per clip: Run -0.137, Attack -0.061, Cast -0.094, Hit -0.093, Die -0.052.
- Texture: base colour only (normal/roughness/metal dropped) 2048x2048 RGBA PNG -> sewer_rat_tex/sewer_rat.png; the tinted variant rows reuse this model and keep the base texture.
- Staging (ArtSource): sewer_rat/unity_staging/sewer_rat.fbx, sewer_rat_tex/sewer_rat.png, sewer_rat_tripo.blend. Backups of the previous model: ArtSource/enemies/sewer_rat/backup_20261012/ (sewer_rat.fbx and sewer_rat.fbx.meta; there was no _tex/_mat).
- Installed: Assets/_Game/Resources/Art/Enemies/sewer_rat/ : TRIPO marker written first, then sewer_rat.fbx (existing .meta/GUID kept; its old external material remaps M_Toon/M_Emit/M_Clear stay in it, harmless) and sewer_rat_tex/sewer_rat.png. Byte-identical to the staging copies. Unity not run; _mat/ will be generated on first import.
- Re-import check (Blender import of the exported FBX): 6 clips (old had 7), Attack 60 / Cast 54 frames, 65 bones, 1 material, rig gate repeated and passed. Not verified: Unity import and in-battle playback.
- Render: scratchpad s14 (C:/Users/User/AppData/Local/Temp/claude/C--Users-User-Desktop-game/3b4b867d-2aa4-4d7d-bb1b-a832694ad641/scratchpad/s14/) sewer_rat_old_vs_new_front.png (old | new rest | new Idle f1).

## Floor fix 2026-10-12 (S14 follow-up)
- Per clip, a CONSTANT offset was added to every key (and handles) of the Hips location curve (local Y axis, 1 m = 1 m world Z) so the lowest mesh vertex over the clip is 0: Idle -0.026 -> 0.000, Run -0.137, Attack -0.061, Cast -0.094, Hit -0.093, Die -0.052 -> all 0.000 (all but Idle were below -0.03). No keys authored, no rotation changed. Re-exported and reinstalled Assets/_Game/Resources/Art/Enemies/sewer_rat/sewer_rat.fbx (staging identical). Rig gate re-run: 0 unweighted, limbs deform; clips Idle 369, Run 31, Attack 60, Cast 54, Hit 32, Die 204 unchanged. Peaks of the strike/release unchanged. Hips are now ~0.1-0.16 m higher than the raw Tripo take, so Idle-to-Run cross-fades shift the body by up to ~0.06 m. Unity not run.
