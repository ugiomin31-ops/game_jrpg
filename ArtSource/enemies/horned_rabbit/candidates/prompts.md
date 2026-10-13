
## B3 candidates (ChatGPT web, GPT-6 Extra High, 2026-10-12, Haiku worker BROWSER-QUEUE 2b)
- Chat URL: https://chatgpt.com/c/6acbb829-68cc-83ee-b549-637028fe1964 (model GPT-6, reasoning slider 3/4 = Extra High, checked before sending)
- Prompt (lead + brief + creature frame, from ArtSource/_briefs/B3_prompts.md): "Generate FOUR separate standalone images in this one response, each its own image, not a grid or collage. One round cream-white horned rabbit standing upright on two separated large feet, short distinct forelimbs spread diagonally downward, long thick ears separated from the head. One sturdy opaque spiral forehead horn with a small violet rift crack; the whole horn does not glow. Compact attached tail, empty paws, front view. No sitting pose. One complete creature per image, chunky cute modern Seoul hunter-game toon 3D style, small socketed non-emissive eyes, glow only inside small blue/violet rift cracks, plain light-grey background, generous margins, square 1:1. No text, logos, crowns, capes, medieval ornament, transparent geometry, floating effects or thin dangling parts. Vary proportions and colour accents slightly between the four images while keeping the description."
- candidate_A.png: pass. Single creature, opaque spiral horn with a small violet crack, feet separated, ears separate from head, tail attached, plain grey background. Forelimbs are held close to the body, not spread diagonally (brief miss).
- candidate_B.png: pass with note. Tall, slim body; horn opaque with a small violet crack; ears separate; forelimbs close to the body (brief miss); faint floor shadow.
- candidate_C.png: pass. Opaque horn with a small violet crack, cream body, two separated feet, tail attached, plain background. Forelimbs are slightly forward and apart, closest to the brief among the four.
- candidate_D.png: pass with note. Ears are very wide and splayed outward with lavender tips; horn crack is small; forelimbs close to the body (brief miss).
- Suggested pick: candidate_C.png (closest to the forelimb brief, clean horn, separated feet). Runner-up: candidate_A.png. Main session makes the final pick.

## Tripo second account (2026-10-12, Haiku worker B3-TRIPO)
- Main final pick: candidate_A.png (main-approved pick)
- Source: https://studio.tripo3d.ai (Tripo Studio web, HD Model, Geometry & Texture, AI Model H3.1 - Best Quality, expected 55 credits)
- Task: 4637c50d-1cf2-47ae-a306-edd43dbe272c  URL https://studio.tripo3d.ai/workspace/generate/4637c50d-1cf2-47ae-a306-edd43dbe272c
- Generate cost: 55 credits; 3205 -> 3150

## Tripo second account (2026-10-12, Haiku worker B3-TRIPO)
- Main final pick: candidate_A.png (main-approved pick)
- Source: https://studio.tripo3d.ai (Tripo Studio web, HD Model, Geometry & Texture, H3.1 - Best Quality)
- Task: 4637c50d-1cf2-47ae-a306-edd43dbe272c  URL https://studio.tripo3d.ai/workspace/generate/4637c50d-1cf2-47ae-a306-edd43dbe272c
- Generate: 55 credits (3260 -> 3205 -> 3150 by the time of batch; this asset 3205 -> 3150)
- Retopo: Triangle, Smart Mesh on, target 5000 -> 4509 faces / 5237 vertices (cost 35; 2635 -> 2600 after rig; balance 2635 -> ... see note)
- Rig: Humanoid, Mixamo, Auto Rig (cost 20; balance 2620 -> 2600). Skeleton visible; skin-weight check in Blender: OPEN (not run by this worker).
- Animations (free presets, no cost): idle, run, slash, cast_a_spell, hit_to_body_01, defeat (6/6).
- Export: FBX (Blender preset), texture 2k, Export Skeleton on, 6 animations. Downloaded unicorn+bunny+3d+model.zip (8.9 MB) and extracted to tripo/.
- Export path: ArtSource/enemies/horned_rabbit/tripo/ (tripo_convert_*.fbx + .fbm)
- Credits spent on this asset: 110 (55+35+20); balance after: 2600.
- CORRECTION (balance chain, same asset): rabbit retopo ran at balance 2655 -> 2620 (35 credits); rig 2620 -> 2600 (20). Earlier retopo/rig line balance figures were wrong; this line is authoritative. Total 110 for this asset; balance 3260 -> 2600 after all three paid steps of rabbit plus the other batch generations, verified in header.

## Installed 2026-10-12 (Sonnet 5.5 worker S14 B3-ENEMIES, own model, headless Blender 5.2.1)
- Source: tripo/tripo_convert_*.fbx (Humanoid/Mixamo, 4509 tris, 2297 verts, 65 bones, 6 takes). No Tripo/ChatGPT generation, no credits; actions only renamed/trimmed, nothing authored.
- Rig gate (source and again on the exported FBX): 0 unweighted of 2297; LeftArm 173 / RightArm 172 / LeftUpLeg 416 / RightUpLeg 297 verts moved >1 cm (45 deg), max 0.148 / 0.145 / 0.113 / 0.098 m. Passed.
- Takes renamed (Tripo -> clip, frames 1-based): idle -> Idle 1-369, run -> Run 1-31, slash -> Attack, cast_a_spell -> Cast, hit_to_body_01 -> Hit 1-32, defeat_02 -> Die 1-204. Exactly these 6 exported as takes Rig|Idle, Rig|Run, Rig|Attack, Rig|Cast, Rig|Hit, Rig|Die (old model had 7 incl. Victory; enemies do not need Victory). Bones in QUATERNION mode, no stale actions, armature `Rig`, skinned mesh `Body`, one material `horned_rabbit`, white `Col`.
- Trim (keys only deleted and shifted, same windows as festival_pumpkin_king since it is the same Tripo preset): Attack source slash 27-86 -> 60 frames (was 159), hand-speed peak / strike at source ~50-51 -> frame ~25 of 60 = ~41% (BattleView 40%). Cast source cast_a_spell 32-85 -> 54 frames (was 130), thrust release at source ~64 -> frame 33 of 54 = ~61% (BattleView 60%). Trim only, no keyframe authored; ends are not blended back to Idle (runtime cross-fades).
- Scale: uniform, to the old model's rest height. Old: 0.887 (old rest bounds 0.411 x 0.499 x 0.887). New: 0.887 tall, 0.578 wide x 0.679 deep; scale x0.90772 from 0.9772 (new is wider/deeper than the old: ears and arms). Bones, mesh and Hips location keys were scaled together (armature object stays x1.0).
- Idle frame 1 z -0.100..0.907 (feet sit ~0.1 m under the floor in Idle, 11% of height); lowest vertex per clip: Run -0.156, Attack -0.129, Cast -0.133, Hit -0.141, Die -0.104. If the feet sink looks wrong in Unity, lift the Hips/root in Idle or accept it (same Tripo preset behaviour as the Tripo bosses).
- Texture: base colour only (normal/roughness/metal dropped) 2048x2048 RGBA PNG -> horned_rabbit_tex/horned_rabbit.png; the tinted variant rows reuse this model and keep the base texture.
- Staging (ArtSource): horned_rabbit/unity_staging/horned_rabbit.fbx, horned_rabbit_tex/horned_rabbit.png, horned_rabbit_tripo.blend. Backups of the previous model: ArtSource/enemies/horned_rabbit/backup_20261012/ (horned_rabbit.fbx and horned_rabbit.fbx.meta; there was no _tex/_mat).
- Installed: Assets/_Game/Resources/Art/Enemies/horned_rabbit/ : TRIPO marker written first, then horned_rabbit.fbx (existing .meta/GUID kept; its old external material remaps M_Toon/M_Emit/M_Clear stay in it, harmless) and horned_rabbit_tex/horned_rabbit.png. Byte-identical to the staging copies. Unity not run; _mat/ will be generated on first import.
- Re-import check (Blender import of the exported FBX): 6 clips (old had 7), Attack 60 / Cast 54 frames, 65 bones, 1 material, rig gate repeated and passed. Not verified: Unity import and in-battle playback.
- Render: scratchpad s14 (C:/Users/User/AppData/Local/Temp/claude/C--Users-User-Desktop-game/3b4b867d-2aa4-4d7d-bb1b-a832694ad641/scratchpad/s14/) horned_rabbit_old_vs_new_front.png (old | new rest | new Idle f1).

## Floor fix 2026-10-12 (S14 follow-up)
- Per clip, a CONSTANT offset was added to every key (and handles) of the Hips location curve (local Y axis, 1 m = 1 m world Z) so the lowest mesh vertex over the clip is 0: Idle -0.100 -> 0.000, Run -0.156 -> 0.000, Attack -0.129, Cast -0.133, Hit -0.141, Die -0.104 -> all 0.000. No keys authored, no rotation changed. Re-exported and reinstalled Assets/_Game/Resources/Art/Enemies/horned_rabbit/horned_rabbit.fbx (staging identical). Rig gate re-run: 0 unweighted, limbs deform; clips Idle 369, Run 31, Attack 60, Cast 54, Hit 32, Die 204 unchanged. Peaks of the strike/release unchanged. Hips are now ~0.1-0.16 m higher than the raw Tripo take, so Idle-to-Run cross-fades shift the body by up to ~0.06 m. Unity not run.

### RESTORE-TOWN-CHARS (2026-10-13, Claude Sonnet)
- Armature rest pose restored to raw x 0.90772 (max head error 3.5e-7 m, was 4.2 cm). Cause: the S14 build scaled edit-bone heads/tails in place while bones were CONNECTED, so every connected child was scaled twice (unintended). Rebuilt with the same script, bones disconnected before scaling (same method as elder_build_b), same Idle/Run/Attack/Cast/Hit/Die takes (369/31/60/54/32/204), per-clip floor offsets recomputed (lowest vertex 0.000 in every clip), mesh/UV/weights identical to the previous install (4509 tris, UV 100%). Rig gate: 0 unweighted.

### RUNFIX-RAT-RABBIT (2026-10-13, Claude Sonnet)
- Run take: forward Hips travel removed (linear detrend of the Hips fore/aft location curve, same as INSTALL-B6-2) so the body no longer slides forward and snaps back each loop. Everything else byte-equivalent (mesh/UV/weights/rest pose/texture, takes Idle/Attack/Cast/Hit/Die identical). Hips forward range over the Run cycle now ~2-3 cm (source hip sway), first->last 0.000 m. Re-exported with the same pipeline, installed in place (.meta untouched). Backup: ArtSource/_backup_20261013_runfix/. See ledger RUNFIX-RAT-RABBIT.
