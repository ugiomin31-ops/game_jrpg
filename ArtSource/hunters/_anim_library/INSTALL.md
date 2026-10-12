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
