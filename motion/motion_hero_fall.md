# motion_hero_fall — Tripo preset export (request requests/motion_hero_fall.md)

Source: Tripo Studio web (studio.tripo3d.ai, Chrome "Browser 2"), 2026-10-16. Credits 0 (balance 2490 before and after).
Model: Dohyun upload `e6b794c1-a873-400a-863f-25fc43740a65`, already rigged (Mixamo 65 bones), 9,435 tris, untextured (no texture-size option was offered).
Export: FBX, preset Mixamo, Export Skeleton ON, Animation stay in Place OFF.

| File | Export | Take inside (Blender 5.2 import) |
|---|---|---|
| `motion_hero_fall.zip` | as requested: `fall` + `defeat` in one export | ONE take `defeat_02_fall`, 203 f (8.46 s @24). Content = `fall` (down by ~f45), then holds lying until f203. `defeat` is NOT a separate take — Tripo merges multi-animation FBX exports. |
| `motion_hero_fall_fall_only.zip` | `fall` only | take `fall`, 72 f = 3.0 s |
| `motion_hero_fall_defeat_only.zip` | `defeat` only | take `defeat_02`, 203 f = 8.46 s (the UI card "defeat" is internally `defeat_02` = the current shared Die) |

All zips are unchanged Tripo downloads (renamed only). Copies also in `C:\Users\User\Downloads` (`C:\Users\tmdgn` does not exist on this PC).

Blender checks (all three): 1 mesh, 52 vertex groups, 4711/4711 verts weighted; posing mixamorig:LeftArm moves 752 verts → skin OK.

`fall` details (fall_only take, model units, hero ~0.95 tall):
- f0 standing facing -X; falls backwards; hips reach floor height ~f48 (hips z 0.49 → 0.15).
- End f72: lying on the back, face up (Head bone Z axis → +Z, 0.97).
- Root travel: hips move ~0.8 along +X (backwards) — about 85% of body height. With stay-in-place OFF the body slides out of the capsule; consider root-motion off / pinning hips XY in Unity.
- Last frames still settle slightly (no hard freeze), but the pose is on the floor at the end.
