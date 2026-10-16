# Humanoid animation library: install notes (S3, 2026-10-11)

Source: `tripo_export/tripo_convert_0860c4ca-c3c8-42da-8d15-1477434f2105.fbx` (Tripo Humanoid, Mixamo bone names, 65 bones, 24 fps).
Output: `Assets/_Game/Resources/Art/HumanoidAnimations/<Name>.fbx` (10 files, no .meta yet; Unity creates them and the importer
`AbyssArtImporter.OnPreprocessAnimation` names the clip after the file).
Tool: headless Blender 5.2.1 (`-b --factory-startup`). Scripts (session scratchpad, not in repo): `.../scratchpad/s3/build.py` (export), `verify.py`, `render.py`.
Unity was NOT run: import, avatar validity and in-game look are unverified.

## Rig gate (source)
6906 vertices, 0 unweighted. Posing `mixamorig:RightArm` by 60 deg moved 1079 vertices (max 0.37 m). Passed.

## Clip table (frames are source frames, inclusive; length = (last-first)/24 s)

| Clip | Source take | Frames kept | Loop | Hips XY travel / const. offset from rest (m) |
|---|---|---|---|---|
| Idle | idle | 1-368 of 369 (dup. end frame dropped) | yes | 0.0000 / 0.000 |
| Run | run | 1-31 (all) | yes | 0.0000 / 0.000 after recentre (source: -0.031, -0.579) |
| Walk | walk | 1-56 of 57 (dup. end frame dropped) | yes | 0.0000 / 0.000 |
| Attack | slash | 17-104 of 159 | no | 0.0000 / 0.000 |
| Cast | cast_a_spell | 9-92 of 130 | no | 0.0000 / 0.000 |
| Hit | hit_to_body_01 | 1-32 (all) | no | 0.0000 / 0.000 |
| Die | defeat_02 | 1-204 (all) | no | 0.0000 / 0.000 |
| Victory | cheer | 1-291 (all) | no | 0.0004 / 0.001 |
| Guard | "Standing defensive guard stance..." | 1-120 (all) | no (see notes) | 0.0000 / (0.004, -0.022) |
| Revive | "Lying face up on the ground..." | 1-120 (all) | no | 0.0000 / (-0.015, 0.022) (hips rise 0.05 -> 0.50 in Z, intended) |

"Loop" is what `AbyssArtImporter.LoopClips` does by file name (Idle, Run, Walk only). Hips XY travel = max-min of the hips world X and Y over the clip,
measured on the re-imported output FBX; hips height is 0.587 m. Every other clip has no XY drift; only vertical motion.

## Export recipe (identical for every file)
One armature object, no mesh, no camera/light; exactly one action (renamed to the clip name; all other takes removed, no NLA).
Trim = manual action frame range (no key moved or deleted); exporter bakes only that range, times start at 0.
Axis `-Z` forward, `Y` up (same as `Blender/lib/abyss_bpy.py export_fbx`), `FBX_SCALE_ALL`, `add_leaf_bones=False`, `bake_anim=True`,
`bake_anim_use_all_actions=True` (only one exists), `bake_anim_use_all_bones=True`, no simplify, `bake_space_transform=False`,
`use_armature_deform_only=False` (so the 13 non-weighted end bones stay and all 10 files have the same 65 bones).
Exporter patch: stock Blender writes the bone Model nodes in the pose of the current frame, so a plain export gives every file a different "rest" (Revive's was
the lying pose, 0.99 m off). The build script writes the REST pose into the bone nodes instead (animation curves untouched). Verified by re-importing every
output: rest bone positions equal the source within 5e-7 m in all 10 files, bone names identical, posed bone positions equal the source within 2e-4 m
at first/middle/last frame (Run differs by the recentre only).

## Avatar notes
Armature-only was chosen: the mesh is not needed for a valid Humanoid avatar (Unity builds it from the bone hierarchy and names), it would add 10 copies of a 6906-vertex
skinned mesh plus textures, and importer sets `materialImportMode = None` for this folder anyway. Rest pose is a T-pose (hands at x = +/-0.19 m, shoulder height), which Unity
needs for auto-mapping. All 65 `mixamorig:` bones present; Unity should auto-map the standard 15 bones plus fingers (needs checking in the Avatar inspector).
Note: ArtLibrary only uses these clips for Human models without their own "Idle".

## Timing evidence (BattleView: Attack contact at 40%, Cast release at 60%)
Fraction = (event frame - first) / (last - first), the same normalisation as Unity normalized time.
- Attack: strike = peak right-hand speed at source frame 51 (R 0.140 m/frame; left hand peaks at 50-51 too). Before: 50/158 = 31.6% of 159 frames (6.6 s).
  After (17-104): 34/87 = 39.1%. Length 3.63 s. Start trimmed to drop the 16-frame idle lead-in, end trimmed after the hands have settled (pose-to-rest 0.14).
- Cast: release = peak right-hand speed entering the held cast pose, frame 59 (59-60 tie, 0.091 m/frame; an earlier equal peak at 29-30 is the hand-gathering circle, not the release). Before: 58/129 = 45.0% of 130 frames (5.4 s).
  After (9-92): 50/83 = 60.2%. Length 3.46 s. The cut lands at the end of the static hold, just as the retract starts.
- These are still long (3.5 s) because Tripo presets run at 24 fps with slow wind-ups. `_actionLength` equals clip length, so battle actions with these clips take 3.5 s each. Only trimming was allowed; shortening needs a speed multiplier in ClipAnimator or a different source take.

## Visual check (renders in the scratchpad `s3/renders/`)
- Guard frames 1/60/120: both forearms raised in front of face and chest, knees bent, held with slight breathing. Reads as guarding. Installed.
- Revive frames 1/30/60/90/120: starts lying on the ground (hips height 0.05 m), pushes up on the arms, kneels, rises to a bent-knee ready stance. Installed. The first frame looks prone (face down), not face up as prompted.
- Attack strike frame 51 and Cast release frame 59 were also rendered and show a forward lunge and an extended arm.

## Deviations and open items
1. Run: the source take has a constant hips offset of (-0.031, -0.579) m (about one leg length forward of the origin). Because the importer sets keepOriginalPositionXZ and bake-into-pose, Unity would likely keep that offset. The build subtracts the constant from the hips location curves of Run only (rigid shift, shape untouched). To undo, remove "Run" from `RECENTER` in build.py.
2. Guard and Revive keep their ~2 cm constant hips XY offset (left alone, below one percent of body height).
3. Guard is a hold but is not in `LoopClips`; it plays once at 5 s (`BattleView` uses `Anim.Length("Guard")` as the action length). Revive likewise.
4. Names code asks for but this library does not provide: Skill, Ultimate, Roar, buff, Talk. Not in the Tripo take list.
5. Slash/Cast/Guard/Revive are text-to-motion or free presets; `Attack` is a hunched sweep rather than a sword slash.

## Impact list (who starts using this library)
Rule (ArtLibrary.SpawnCharacter): Animator.isHuman and no own exact "Idle" clip. A folder is Human only if it has a `HUMANOID` marker file next to its FBX.
Checked all of `Art/Characters` (24 folders: archer, cleric, mage, warrior, h_bora ... h_yuna) and `Art/NPCs` (8 folders: elder, guild_clerk, innkeeper, shopkeeper, smith, villager_a/b/c):
- No `HUMANOID` marker file exists anywhere under `Assets/_Game/Resources/Art` (also no `TRIPO` marker).
- Every `*.fbx.meta` there currently has `animationType: 2` (Generic); none is Human.
=> No existing model is affected by installing the library. A new Tripo hunter that gets a `HUMANOID` marker and has no "Idle" take of its own will pick these clips up automatically.

## Follow-up: short 2 s takes (2026-10-11)
Source: `tripo_export_short/tripo_convert_8dda4b54-3d59-45d3-9f20-9c55fe4159df.fbx` (2 takes, 48 frames, 24 fps). Old long clips copied to `old_long/` (Attack.fbx, Cast.fbx).
- Gate: 0 of 6906 vertices unweighted; RightArm 60 deg moved 1069 vertices (max 0.38 m). Same 65 bone names, rest positions identical to the long-library source (max diff 0.0 m).
- **Attack: replaced** with the short take, frames 6-48 of 48 (1.75 s, start trimmed). Right-hand peak speed (0.129 m/frame) at frame 23: before 22/47 = 46.8%, after 17/42 = 40.5%. Re-import check: rest 5e-7 m, posed bones within 3e-6 m of the source. Hips XY travel 0.0; constant offset (-0.018, 0.010) m left alone (hips also sit 0.07 m below rest height: a crouched stance). Renders (`renders2/sheet_sAttack.png`): ready stance, right hand rises overhead (frames 14-20), swings down in front (frame 23), recovers. Reads as a one-handed overhead swing (open hand, no weapon).
- **Cast: NOT replaced; old long Cast (9-92, release at 60.2%) stays.** The short take never extends the arm: hand-to-shoulder distance stays 0.19-0.25 m (arm length about 0.32), peak right-hand speed is only 0.039 m/frame, and the hand ends 0.15 m behind the hips (drawn back), so there is no forward palm release (`renders2/sheet_sCast.png`). A usable Cast would need a new Tripo prompt that emphasises a hard forward thrust.
- No `.meta` files exist in HumanoidAnimations (Unity not run).

## Follow-up: Cast take 3 (`tripo_export_cast3/extracted/tripo_convert_395a46c2-...fbx`, 48 frames, 2 s)
- Gate passed: 0 of 6906 vertices unweighted, RightArm 60 deg moved 1069 vertices, 65 bones, rest identical to the library source (0.0 m).
- **Not installed; the current long Cast (frames 9-92, release at 60.2%) stays.** The motion is in the wrong order: hand-to-shoulder distance is 0.314 m at frame 2 (full extension, palm forward at shoulder height, hand z 0.82), then the hand is drawn back (y +0.24 m behind the hips, ext 0.21 m) by frame 16 and held there to frame 48. It starts at the extension and ends drawn back, so there is no release at about 60%. Peak right-hand speed 0.049 m/frame at frames 3-12 (the pull-back). Trimming cannot fix the order.
- Hips XY travel 0.0 (constant offset (-0.025, 0.021) m, not touched). Renders: `renders3/sheet.png` (frames 1, 4, 8, 12, 20, 30, 48).
- Cast would work if the take were played reversed (draw back, then thrust), but reversing keys is more than trimming; not done.

## Follow-up: Cast shortened (long take, source frames 36-74)
`Cast.fbx` now trims `cast_a_spell` to frames 36-74 of 130 (39 frames, 1.58 s; was 9-92, 3.46 s). Release stays at source frame 59 (peak right-hand speed): (59-36)/(74-36) = 60.5%. Start at 36 is where the gather circle (peak at 29-30) has slowed to 0.03 m/frame (a calm pause follows at 38-45); starting later would drop the clip under 1.6 s at 60%. The end sits in the static hold, so the retract is cut (as before). Re-import check: rest 5e-7 m, posed bones within 5e-6 m of the source, hips XY travel 0.0, no offset. Renders (`renders4/sheet.png`, frames 36/48/59/66/74): the first frame is a one-foot-raised gathering pose with hands at the hip, then the right arm drives forward with a step-in at 59 and holds. The release reads clearly. Old long version stays in `old_long/Cast.fbx`.

## Follow-up (2026-10-12): Talk clip
Source: `tripo_export_talk/extracted/tripo_convert_d68d3626-...fbx` (4 takes: agree 97 f, greet_01 85 f, "Standing in place having a friendly conversation..." 120 f, wave_goodbye_01 159 f; 24 fps).
- Gate: 0 of 6906 vertices unweighted, RightArm 60 deg moved 1069 vertices, 65 bones, rest identical to the library source (0.0 m).
- **Installed: `Talk.fbx`** = the 5 s conversation take, frames 1-120 untrimmed. Re-import: rest 5e-7 m, posed bones within 2e-6 m, hips XY travel 0.0 (constant offset 3 mm, left alone). Renders (`renders5/sheet.png`, frames 1/30/60/90/120): standing, both hands gesturing at the chest, relaxed. Reads as talking.
- **Loop:** the take is not a seamless loop (pose difference first vs last 0.177, an ordinary step is 0.023). It does not need to loop: the only caller is `TownWorld.cs:273`, `nearest.Npc?.PlayOnce("Talk")`, which plays one cycle and returns to "Idle" (`ClipAnimator.PlayOnce`, then `Update` queues `Idle` at normalized time 1). `AbyssArtImporter` keeps `Talk` non-looping (not in `LoopClips`), which is right for this. One cycle is 5 s; there is a 0.12 s fade into Idle with a visible pose jump from the end gesture.
- **Clip names the runtime asks for** (grep over all .cs and .json under Assets/_Game): Idle, Run, Walk, Attack, Cast, Hit, Die, Guard, Revive, Skill, Ultimate, Roar (battle/town/dungeon) and **Talk** (town NPC). No code asks for Greet, Wave, Nod or Agree (only dialogue text keys `npc_*_greeting`). So greet_01, wave_goodbye_01 and agree are NOT installed. `Skill` / `Ultimate` / `Roar` are still not in the library.
- `ClipAnimator.Begin` throws "Missing authored animation take" if a requested clip is absent, so any Human model without its own Idle (and its own Talk) needs `Talk.fbx`; it is now present.

### Impact list update (supersedes the earlier "no HUMANOID marker exists")
After the first impact check, parallel work added `HUMANOID` markers. Now present: Characters/h_jiho, h_minjun, h_seoa, h_yuna, and NPCs/elder (this task). Their FBXs carry no action, so all five load this whole library via `ArtLibrary.SpawnCharacter`. That is intended. Models without a marker are unchanged.

## NPC elder: Tripo install (2026-10-12)
See `ArtSource/npcs/elder/candidates/prompts.md` (section "Installed 2026-10-12") for the full record.

## Follow-up (2026-10-12): class motions, STAGING ONLY (not in Assets)
Source: `tripo_export_class/tripo_convert_14929035-...fbx` (shopkeeper rig, 7068-vertex mesh, 12 takes, 24 fps). Staged in `class_staging/`. Same exporter and rest-pose patch as above; each file carries the class FBX's own rest pose.
- **Gate:** 0 of 7068 vertices unweighted; RightArm 60 deg moved 898 vertices (max 0.36 m). 65 bones, names/order/parents identical to the library source.
- **Rest differences vs the library source:** this is a different body. Hips z 0.529 (lib 0.587), LeftArm head (0.105, 0.029, 0.766) vs (0.075, 0.036, 0.805), LeftFoot x 0.094 vs 0.124; max bone-head diff 0.073 m; bone-axis matrices differ up to 1.38 (roll differs on some bones). Unity Humanoid retargets per avatar, so a class file must keep its own rest; the staged files re-import with rest = the class FBX rest (7e-7 m) and posed bones within 9e-6 m of the source. Mixing these clips with the library clips onto one model is Unity's retarget job; unverified here.
- **Skill timing in BattleView:** `Contact("Skill")` is **0.5** (`BattleView.cs:622`), not 0.6 (Cast .6, Ultimate 44/66, Attack .4). `Skill` is used when the actor has a "Skill" clip and the action is a Skill (`BattleView.cs:541`), played with a 0.05 s fade and `Idle` after. I timed Skill to 50%.
- **Ranged note:** `rangedBasic` (non-warrior party basic attack) uses the Attack clip without the approach step, so archer/mage/cleric Attack stay in place.

| File | Source take | Frames kept (of source) | Length | Key moment | Loop | Hips drift (XY range) | Verdict |
|---|---|---|---|---|---|---|---|
| `BattleIdle.fbx` | Combat ready stance | 12-47 of 72 | 1.5 s | n/a | yes (name `BattleIdle`) | 0.011 / 0.010 m, offset 0.03 | **staged**. A boxer-style guard with both hands at the face, not the "weapon low at side" in the prompt. Not perfectly seamless: first vs last pose difference 0.052 (quaternion norm over 52 bones) vs 0.005 for a normal step, about 0.8 deg rms per bone. The full take (1-72) was worse (0.111). Best loop point found by search, only trimming. |
| `warrior/Attack.fbx` | From a combat ready stance, a powerful one-handed overhead swing | 1-44 of 48 | 1.83 s | right-hand peak speed at frame 18: 17/43 = 39.5% | no | 0.033 / 0.054 m | **staged**, caveat: right hand rises to head height (not fully overhead), then a forward lunge-down at frame 18; no weapon. |
| `mage/Skill.fbx` | Spell channel | 12-72 of 72 | 2.5 s | both palms thrust forward at frames 41-43 (peak 42): 30/60 = 50.0% | no | 0.012 / 0.013 m | **staged**, caveat: modest. Hands gather at the chest, then both arms extend forward at waist-chest height and hold. Start and end poses differ (0.83), so it needs a fade back to Idle. |

Rejected after rendering (not staged; renders in `scratchpad/s3/rc1/sheet_*.png`):
- **Attack_archer**: right arm goes up beside the head like a wave or head scratch; no bow-draw, left arm never extends forward; start/end differ (0.51).
- **Attack_mage**: crouching twist with hands at the waist; no forward wand flick; start/end differ (0.83).
- **Attack_cleric**: the right arm does sweep horizontally across the body (reads fine) but the whole swing is frames 4-12 (hand-speed peak at frame 5 = 8% of the clip); with trim-only and a 1.2 s minimum the strike cannot reach 40%, and the arm rests on the left for the remaining 3/4 of the clip. Could be staged if the contact fraction is changed or the start is allowed to be cut.
- **Skill_warrior**: the whole body travels and spins out of frame; hips XY range 0.53 x 0.49 m, not a constant offset, so it cannot be recentred.
- **Skill_archer**: raised right arm waves; no bow, no three draws.
- **Skill_cleric**: starts hunched (hips down 0.1 m), ends in a side-on upright pose; hips XY range 0.17 x 0.14 m; no raised cane or prayer reading.
- Presets `standing_relax` (423 f, loops: first/last 0.019), `chop` (159 f, loops: first/last 0.0), `shoot` (218 f, hips travel 2.6 m forward) were not requested and not staged.

## Follow-up (2026-10-12): cleric Attack, free presets, class mapping (still STAGING ONLY)
New staged files (same exporter; re-import: rest 7e-7 m, posed bones within 1e-5 m of source):
- `cleric/Attack.fbx` (Attack_cleric): frames 1-36 of 48, 1.5 s. Strike = right-hand peak speed at frame 5-6 (using 6): **contact fraction 5/35 = 14%** (the take starts with only a 4-frame wind-up, nothing earlier to keep). Renders (1/6/12/24/36): relaxed stance, right arm sweeps right to left across the chest, ends with hands on hips. Hips XY range 0.037 x 0.022 m. Staged.
- `warrior/Attack.fbx` is now the **`chop` preset**, source frames 30-83 (54 f, 2.25 s), strike (peak hand speed, both fists slam down) at frame 51: **39.6%**. Two-handed overhead chop: fists go overhead at frame 42, slam at 51. Caveat: starts and ends in a forward-bent hunch (not a ready stance), so it needs fades; hips lean 0.06 x 0.12 m (body motion, not drift). Rest/rig as above (65 bones, same class rest). The earlier one-handed take is kept as `alt/warrior_1hand/Attack.fbx` (39.5%).
- `alt/relaxed/BattleIdle.fbx` = **`standing_relax`**, frames 1-422 (17.6 s, duplicate end dropped). Calm standing, arms low and loose, weight on one leg, small head turns, smiling; NOT a combat stance (reads casual). Loops seamlessly only as the whole take: first vs last pose 0.019 (normal step 0.009); every window under 100 frames is worse (best 0.09). Hips drift 0.12 x 0.03 m (sway). Recommended as BattleIdle for weapon/staff holders (mage, cleric, archer).
- `shoot` preset: rejected. The body travels 2.6 m forward in frames 1-41 and then kneels on one knee fiddling with both hands at the chest (hips z 0.17-0.2); no aiming or shooting reads; not recentrable.
- `chop` and `standing_relax` rig notes: same class rig/rest as above, takes 159 f and 423 f.

### Shared-library fallbacks (installed in `Assets/.../HumanoidAnimations/`)
- `Attack` (short one-handed overhead swing, 1.75 s, contact 40.5%): serviceable for warrior and cleric; for archer/mage it reads as a melee swing.
- `Cast` (forward palm release, 1.58 s, release 60.5%): good as the basic attack or Skill for mage and cleric (needs a per-clip contact value if used as Skill, runtime Skill is 0.5).
- `Hit`, `Idle`, `Guard`, `Die`, `Revive`, `Victory`, `Run`, `Walk`, `Talk` are class-neutral; `Idle` is the upright attention pose and no shared clip is a combat-ready loop.

### Final mapping (class x clip -> staged file, contact fraction)
| class | BattleIdle | Attack | Skill |
|---|---|---|---|
| warrior | `class_staging/BattleIdle.fbx` (guard stance, loop gap 0.052) | `warrior/Attack.fbx` (chop) 39.6% (alt `alt/warrior_1hand/Attack.fbx` 39.5%) | missing (Skill_warrior rejected; fall back to shared `Attack` or `Cast`) |
| archer | `alt/relaxed/BattleIdle.fbx` (relaxed, not ready) | missing (Attack_archer, shoot rejected; shared `Attack` is a melee swing) | missing (Skill_archer rejected) |
| mage | `alt/relaxed/BattleIdle.fbx` | missing (Attack_mage rejected; fall back to shared `Cast` 60.5%) | `mage/Skill.fbx` 50.0% |
| cleric | `alt/relaxed/BattleIdle.fbx` | `cleric/Attack.fbx` 14% (strike frame 6 of 1-36) | missing (Skill_cleric rejected; fall back to shared `Cast`) |

## B5-TRIPO-2 motion review (2026-10-13): Attack_archer2, Skill_archer2, Attack_mage2, Skill_warrior2, Skill_cleric2
Sources: `tripo_export_class2/tripo_convert_9e8509dd-...fbx` (16-take bundle, shopkeeper rig) and `tripo_export_class3/Skill_cleric2/tripo_convert_fc2b008b-...fbx` (re-rigged base mesh, 1 take).
- **Rig gate (Blender 5.2, headless):** bundle 7068 vertices, 0 unweighted (0.00 %), weights sum 1.000 everywhere, 52 groups, 65 bones; posing RightArm 60 deg moved 980 vertices (max 0.28 m), LeftUpLeg 3233, Spine1 5627, Head 5557. Cleric2 FBX 7078 vertices, 0 unweighted, RightArm 943 / LeftUpLeg 3118 / Spine1 5605 / Head 5510 vertices moved (max 0.42 m). Both pass. Note: the cleric2 skeleton rests facing -X with the arms along Y (the shopkeeper class rig faces -Y), a re-rig orientation difference that Unity Humanoid should absorb but nobody has verified.
- **Routing facts (BattleView.cs:599-605):** a hero plays `Cast` for every `actor_action == cast` presentation, `Skill` only for non-cast Skill actions that have a `Skill` clip, else `Attack`. Over heroes.json learnsets: warrior 95 attack + 30 cast, mage 120 cast, archer 100 shoot + 10 cast, cleric 120 cast. So a per-class `Skill` is only reachable for warrior and archer; cleric/mage `Skill` is never played, and the archer's 100 shoot skills play `Attack` unless an archer `Skill` exists.
- Strips (6 frames, front 3/4 plus side views, class mesh, 0.25 m floor grid): scratchpad `b5_2/d/strip_A.png`, `strip_A2.png`, `strip_B.png`; installed references `strip_ref1.png` (shared Attack, shared Cast, warrior chop), `strip_ref2.png` (mage Skill, cleric Attack).

| Candidate | Verdict | Evidence |
|---|---|---|
| Attack_archer2 (Fist Snap Motion, 48 f) | **INSTALLED** as `HumanoidAnimationsByClass/archer/Attack.fbx`, contact 0.51, end 0.85 | Reads as a bow draw: body turns to the side (chest yaw -65 deg at f22), left arm extends forward at shoulder height (hand 0.30 m in front of the hips, f16-28), right hand pulled to the cheek (hand-to-head 0.13 m vs 0.24 at rest, f19-25), hold f19-28, then the arm lowers and the hand moves forward (recoil) from f26. Feet planted: foot XY range 0.019 x 0.007 m, hips range 0.054 x 0.038 m, no per-frame joint rotation above 40 deg, no limb flip. Replaces the shared `Attack` (wide martial-arts guard, `strip_ref1.png` row 1), which was the archer's basic attack and all 100 shoot skills. Fingers are not animated in any Tripo take, so there is no hand-open at release; release is placed where the draw ends and the hand starts moving forward: frame 25 of 1-48 -> (25-1)/47 = 0.51. First vs last pose differ (0.40), the take needs the normal fades. |
| Skill_archer2 (Arm Snap Motion, 72 f) | rejected | Only the left arm moves (extends to shoulder height by f7, hand to the forehead at f44); the right hand stays at the hip (z 0.45-0.50 for the whole take), so there is no draw, no three snaps; reads as pointing then saluting. |
| Attack_mage2 (Arm Pointing Gesture, 48 f) | rejected | The right hand only travels to the left shoulder/neck (0.2 m in front of the hips at most, hand 0.23 m from the head, never leaves the shoulder) and back: reads as scratching the neck, no point forward. The installed fallback (shared `Cast`, forward palm release) is better. |
| Skill_warrior2 (360 Degree Turn in Place, 72 f) | rejected | Not a 360: the torso turns to -104 deg by f43 and stays there (back to the camera for the last 30 frames); right foot slides 0.21 x 0.18 m; arm never reads as a swing. Installed warrior takes (chop `Attack`) stay; warrior has no `Skill` and still falls back to `Attack`. |
| Skill_cleric2 (Blessing Gesture, 72 f) | rejected | The gesture is gentle (both forearms raised to chest height, palms up, f10-40), natural weight and planted feet, but (1) the game never plays a cleric `Skill` (all cleric skills are cast actions -> `Cast`), (2) as a `Cast` replacement it would also serve cleric damage spells, (3) different rest orientation (-X facing) unverified in Unity. Keep for a possible future `cleric/Cast` for heals. |

Install recipe (same as the existing class takes): `build_cls3.py` (copy of the scratchpad `s3/build_cls2.py`: exporter patch writing the REST pose into the bone nodes, one action, manual frame range, armature only, `-Z` forward / `Y` up, no leaf bones, STRIP paths) with source action `Stand sideways to the target...` frames 1-48, written to `class_staging/archer/Attack.fbx` and copied to `Assets/_Game/Resources/Art/HumanoidAnimationsByClass/archer/Attack.fbx`. Re-import check: 1 action `Attack`, 65 bones, rest identical to the installed `archer/BattleIdle.fbx` (0.0 m), rest vs source 7e-7 m, posed bones within 3e-6 m at first/middle/last frame. No `.meta` written (Unity creates it). `ArtLibrary.ClassContact["archer/Attack"] = .51f`, `ClassEnd["archer/Attack"] = .85f` (the last 15 % is the hands settling).

### Updated mapping (archer Attack added)
| class | BattleIdle | Attack | Skill |
|---|---|---|---|
| archer | `alt/relaxed/BattleIdle.fbx` | `archer/Attack.fbx` 51 % (end 85 %) | none (plays Attack) |

## Per-hero layer and free motion fixes (2026-10-14, code only, no assets)

### Clip layers (ArtLibrary.MergeLayers)
A Unity-Humanoid model with no `Idle` take of its own gets, in order (later layers replace a take of the same name):
1. `Assets/_Game/Resources/Art/HumanoidAnimations/<Take>.fbx` (shared library)
2. `Assets/_Game/Resources/Art/HumanoidAnimationsByClass/<classId>/<Take>.fbx` (`GameDB.ClassOf(id)`; for an NPC this is the NPC id, so this folder is already per-NPC)
3. `Assets/_Game/Resources/Art/HumanoidAnimationsByHero/<heroId>/<Take>.fbx` (only for heroes, whose class id differs from their id)

Contract (same for every layer): one clip per FBX, the clip is named after the file by `AbyssArtImporter`; take names are the ones the runtime asks for (`Idle`, `BattleIdle`, `Run`, `Walk`, `Attack`, `Cast`, `Skill`, `Ultimate`, `Hit`, `Die`, `Guard`, `Revive`, `Victory`, `Talk`); `Idle`/`BattleIdle`/`Run`/`Walk` loop by file name. A missing or empty class/hero folder simply falls through. Nothing has to exist for the hero layer today.

Timing values live in `ArtLibrary`, keyed `<layer id>/<Take>` where the layer id is the class id or the hero id that supplied the take:
- `ClassContact` strike / release fraction (default Attack .40, Cast .60, Skill .50, Ultimate 44/66);
- `ClassEnd` fraction after which the one-shot fades back to the rest loop (held recovery tails);
- `ClassLoopBlend` seconds of self cross-fade before a loop wraps (for loops whose first and last pose differ).
Example for a future per-hero take: `HumanoidAnimationsByHero/h_dohyun/Attack.fbx` + `{ "h_dohyun/Attack", .40f }` in `ClassContact`.

### Runtime behaviour changed (no asset touched)
- Standing loops (`Idle`, `BattleIdle`) start at a per-unit phase (from the object's instance id), so heroes, NPCs and monsters no longer breathe in lockstep. One-shots and explicit `PlayFrom` are unaffected.
- `warrior/BattleIdle`: 0.3 s self cross-fade before each wrap (`ClassLoopBlend`). Measured on h_dohyun: peak bone speed 39 deg/s at the wrap without it, 14 deg/s with it.
- `cleric/Attack`: contact .14 -> .17 (the mace/cane head is furthest forward in front of the body at frame 6 of 35 on the h_yuna retarget; the speed peak is frame 4) and end .50 (the sweep is over at frame 17; the rest walks the hand back to the hip).
- `mage/Skill` (two-handed channel) now plays for mage cast skills with group scope, tier 3 or the signature; quick single-target spells keep the shared `Cast`. Rule is generic: any caster whose class/hero layer has `Skill` but no `Cast`.
- `Die` takes of 6 s or more (Tripo `defeat_02`: still for 15 %, slumps at 20-50 %, stands up again) play only the window .18 -> .50 and hold the slump (heroes and monsters).
- Enemy dash: the body arcs 0.12-0.40 m (6 % of the travel) and `Run` plays at up to 3x; no foot is planted while the body crosses the arena, so it no longer glides. Same arc on the run home.

### Free presets for the Tripo pass (not installed; no local per-slot files exist yet)
- Already local but not cut into clips: `agree`, `greet_01`, `wave_goodbye_01` (`tripo_export_talk/extracted/tripo_convert_d68d3626-...fbx`, female hunter rig) and `standing_relax` (`tripo_export_class/...14929035...fbx`, already used as BattleIdle). They can be cut with the existing build script into `HumanoidAnimationsByHero/<heroId>/Victory.fbx` (h_jiho `agree`, h_yuna `wave_goodbye_01`, h_seoa `greet_01`) and `HumanoidAnimationsByClass/<npcId>/Idle.fbx` (innkeeper / shopkeeper `standing_relax`) without Tripo, or re-exported from rig 5de41bd4 for the same body as the new clips.
- Must be exported on the monsters' own account-3 rigs (Generic in Unity): `fall` (Die) and `run` (Run) for sprout ab222847, mushroom 89c1a712, pixie c8d69352 (forest_guardian 880cb170 already has `fall`).

## MOTIONS-20261014 install (2026-10-14, headless Blender 5.2 + Unity, no credits)

Sources (raw, unchanged): `tripo_export_hero_20261014/hero_bundle_B_18takes.fbx`, `tripo_export_hero_20261014b/tripo_convert_5c20a009-...fbx` (rig 5de41bd4), and the monster exports under `ArtSource/enemies/<id>/tripo_motion_20261014(b)/` (moved there from the task-id folders, bytes unchanged; ledger paths updated).
Gate: hero rig 7078 verts, 0 unweighted, RightArm 45 deg moved 809 verts; monsters 0 unweighted (sprout 4950, mushroom 4755, pixie 4874, guardian 9561 verts), arm/leg posing deforms. Rest facing: hero rig faces -X -> turned +90 deg about Z in the export (the Tripo action also keys the armature object with constant identity; those object curves are removed so the turn sticks); re-import faces -Y like every installed library/class file. Monster rigs face -Y (no turn).
Scripts (scratchpad `motion14/`): `inspect.py` (gate, facing, per-take stats, 8-frame strips), `speed.py` (per-frame hand/head/foot speed), `build_hero.py` / `build_hero_b.py` (armature-only, rest-pose patch, optional post-contact hips ramp), `build_mon2.py` (INSTALL-B6-2 builder on the new export: same uniform scale, Run detrend, per-frame floor for `fall`, white Col, same basecolor), `verify_mon.py`.

| # | Clip | Verdict | Installed as | Contact / end |
|---|---|---|---|---|
| 1 | Sword Slash Motion | good (diagonal slash with a lunge step) | `HumanoidAnimationsByHero/h_dohyun/Attack` | .34 / .85 |
| 2 | Sword Slash Sequence | good (low horizontal cut, rising cut overhead) | `h_dohyun/Skill` | .45 (first cut) |
| 3 | Chest Pound and Shout | acceptable (chest pound, arm opens, chin up) | `h_minjun/Cast` | .55 |
| 4 | Shoulder Check and Sword Swipe | good; ends 0.32 m forward -> hips eased back after frame 18 | `h_minjun/Attack` | .36 / .80 |
| 5 | Power Jump and Slam | partial (crouch-gather, small hop, crouching slam; no high jump) -> trimmed 1-45 so the slam lands near 44/66 | `HumanoidAnimations/Ultimate` (all hunters) | slam .61 |
| 6 | Healing Gesture | BAD (hands go to the face / head) -> replaced by the earlier paid Blessing Gesture on the same rig | `h_yuna/Cast` = Blessing | .28 / .60 |
| 7 | Magic Spell Cast | BAD (no visible release, ends hunched) -> shared Cast kept | - | - |
| 8 | Arm Snap Motion (double shot) | BAD (right hand never draws; same failure as Skill_archer2) -> archer Attack kept for skills | - | - |
| 18 | Sword Fighter Stance | BAD (falls over and lies on the floor) -> warrior BattleIdle kept (loop blend) | - | - |
| 20 | One-Handed Mace Strike | good (overhead strike in front) | `h_yuna/Attack` | .26 / .80 |
| b | Hold a bow low (h_jiho BattleIdle) | acceptable (alert stance, little motion) | `h_jiho/BattleIdle` | loop blend .3 |
| b | Shield-bearer stance (h_minjun BattleIdle) | good | `h_minjun/BattleIdle` | loop blend .3 |
| 19 | Nervous young healer (h_yuna BattleIdle) | acceptable (fidgets, turns aside; big loop seam) | `h_yuna/BattleIdle` | loop blend .45 |
| b | Staff jab (h_seoa Attack) | good; 0.11 m forward drift eased back after frame 12 | `h_seoa/Attack` | .20 / .85 |
| free | agree | good (understated) | `h_jiho/Victory` | - |
| free | greet_01 | BAD as victory (walks 2.2 m while waving) | not used; h_seoa keeps shared cheer | - |
| free | wave_goodbye_01 | BAD as victory (seated pose) | not used; h_yuna Victory = Blessing | - |
| free | standing_relax | good | `HumanoidAnimationsByClass/innkeeper/Idle`, `.../shopkeeper/Idle` | - |
| free | cheer | already the shared Victory (h_dohyun, h_minjun, h_seoa) | - | - |

Monsters (takes merged into `Art/Enemies/<id>/<id>.fbx`; geometry, UVs, weights, bones and basecolor verified identical to the previous install):
| Monster | Attack | Cast | Other |
|---|---|---|---|
| sprout | #12 Crouching Hop and Headbutt (modest lunge; hips eased back after f24), .45 | #17 Stomping Stance (subtle), .50 | Run = free `run` (detrended), Die = free `fall` |
| mushroom | #13 Head Hammer is BAD (static) -> `chop` kept (27-86), .40 | #15 Crouch and Spring Up, .27 | Run `run`, Die `fall` |
| pixie | #14 Tiptoe Skip and Push (hips eased back after f19), .37 | #16 Fairy Sprinkling Light (gentle), .42 | Run `run`, Die `fall` |
| forest_guardian | #10 Giant Arm Sweep, .25 | #11 Giant Slam Pose, .37 | Roar = #9 Giant Roar Pose (boss intro), Skill = vine whip (11-take export), .34; Run `run`, Die `fall` |
Monster contact values live in `ArtLibrary.ClassContact` keyed `<model id>/<take>` (a model with its own takes is its own timing layer). `fall` Die takes (2-6 s) start at .3 and are not toppled by code; `defeat_02` (>= 6 s) keeps the slump window + topple.

### Signature objects wiring (2026-10-14)
- `h_yuna` sig `응급 처치`: presentation `pr_c_first_aid` (copy of `heal`, set through `Tools/content/spec.py` sig third field + `hunters.py`), with the new presentation field `heal_vfx: first_aid` (HealEvent uses it instead of the shared `heal`). Effect `first_aid` = `heal` layers + heal bloom + the `aid_kit` mesh (pops over the ally, 1.0 s, alpha, `untinted`).
- `h_minjun` sig `구조대의 함성`: presentation `pr_w_rescue_shield` (copy of `pr_w_provoke`), effect `rescue_shield` = provoking roar + the `riot_shield` mesh set down 0.75 m ahead of him (`align` + `upright`: yaw toward his facing, `untinted`). No held shield on his arm (not attempted: needs a fitted attach point and re-QA of every warrior take).
- New VFX layer fields (Tools/vfx/gen_effects.py allow-list + VfxLibrary.LayerRecipe): `untinted` (keeps the texture's own colours), `ahead` (metres along the effect facing). `upright` on an aligned mesh layer = yaw only. Self-cast effects now get the caster's forward as their facing (BattleView.FacingFrom); no existing recipe aligns a self-cast layer, so only the new `ahead` layer uses it.
- effects.json regenerated with gen_effects.py only (byte-reproducible run to run).

## Die replaced with Tripo `fall` (2026-10-16)
`HumanoidAnimations/Die.fbx` is now the free Tripo `fall` preset (3.0 s, falls backwards and lies on the back/side), built by
`tripo_fall_20261016/build_die.py`; details and checks in `tripo_fall_20261016/SOURCE.md`. The old `defeat_02` Die is in git history.
