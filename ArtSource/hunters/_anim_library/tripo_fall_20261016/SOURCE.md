# Shared Humanoid Die from Tripo `fall` — 2026-10-16

- Request: `requests/motion_hero_fall.md` on branch `local-requests`; drop: `motion/motion_hero_fall_fall_only.zip` on `tripo-glb-drop` (commit a26f197).
- Tripo Studio, free preset `fall`, 0 credits. Model: h_dohyun upload `e6b794c1-a873-400a-863f-25fc43740a65` (Humanoid/Mixamo 65 bones, untextured).
- Export: FBX, Mixamo preset, skeleton on, stay in place off. Zip kept unchanged here: `motion_hero_fall_fall_only.zip`
  (SHA256 61b12648ff74cbf6f73835fed8e6611a6c6978809153387245bf8cc3a050d344), FBX `tripo_convert_58374b61-e949-460b-92b0-3e397339562a.fbx`, take `fall`, frames 0-72 @24 fps.
- Build: `build_die.py` (bpy 5.2, `-- <src.fbx> <out.fbx> 0.5`) -> `Assets/_Game/Resources/Art/HumanoidAnimations/Die.fbx`
  (SHA256 2d7211dbff385b98e9269692d287442d09ae75faf81a57fc7235c10f40a6e977).
  - Armature only, one action `Die`, object scale 0.01 applied (pose locations rescaled), axis -Z forward / Y up, no leaf bones, all 65 bones.
  - Frame 0 of the source faces 136 deg (about 45 deg off the library's -Y); the whole motion is turned +46.3 deg about Z at the frame-0 hips.
  - Hips horizontal travel scaled to 0.5 (source slides back 0.81 m, 85 % of body height; installed 0.40 m).
  - Bone nodes written in rest pose (rest key at frame -10 is the current frame during export).
- Re-import check: 65 bones, rest equals the source rest x0.01 (hips 0.5723 m), frame 1 faces -Y, hips reach the floor around frame 43 (z 0.146),
  end pose lying on the back/side (head toward +X+Y, face (0.77,-0.61,0.17)), lowest bone >= 0.014 m above the floor in every frame.
- Meta: `Die.fbx.meta` reduced to its GUID so Unity rebuilds the avatar from this rig (the old meta stored the female library rig's skeleton).
- Runtime: shared Die is now 3.0 s, under `ArtLibrary.DefeatTakeMinLength`, so the slump window and the code topple no longer apply to it.
  `BattleView.HeroDown` plays it at 1.4x; revive stands up in code (`RisesInCode`/`HeroRise`) because the shared Revive starts face down.
- Not done: Unity import, avatar mapping and in-game look.
