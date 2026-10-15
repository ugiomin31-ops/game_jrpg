# h_dohyun Tripo model: install

The Tripo model goes in as a **Unity Humanoid** with no animation of its own. Unity retargets the hunter's existing
Blender clips onto it from `h_dohyun_anim.fbx`. That file is the old `h_dohyun.fbx` skeleton: no mesh, bones renamed
to Mixamo names, and all 12 takes rebased to the same T-pose rest the Tripo model uses. The rebase was verified frame
by frame after an FBX round trip: at most 2e-6 m and 0 degrees of error. Both FBXs use a T-pose rest, so their
avatars line up whether or not Unity enforces a T-pose on import.

Do this only after the QA agent has finished with Unity (Unity closed, or at least not importing).

## 1. Apply the C# patch (repo root)

```
git apply ArtSource/hunters/h_dohyun/staging/hunter_tripo.patch
```
It changes three files:
- `Editor/AbyssArtImporter.cs`
  - HUMANOID models with a `<id>_tex/` folder get the textured Abyss/Toon material remap, so rim glow, flash and dissolve work.
  - `*_anim.fbx` files import without materials.
  - Humanoid takes bake root motion into the pose (Based upon Original).
  - `TexturedMaterials` sync no longer skips HUMANOID folders.
- `Runtime/Art/ArtLibrary.cs`: a humanoid model with no `Idle` loads clips from `<model path>_anim` first, then the shared `Art/HumanoidAnimations`.
- `Runtime/Art/CharacterModel.cs`: humanoid `Radius` comes from the trunk and leg bones, not from the T-pose renderer bounds (the arms span about 1.75 m).

The patch compiles. I checked it with Unity 6000.3.25f1's Roslyn against the project's DLLs, runtime and editor.

## 2. Files (all under `Assets/_Game/Resources/Art/Characters/h_dohyun/`)

| Action | Path |
|---|---|
| delete (with `.meta`) | `h_dohyun_tex/*.png`: the 13 old VRoid textures (`F00_…`, `M00_…`) |
| delete (with `.meta`) | `h_dohyun_mat/*.mat`: the 13 old VRoid materials. Keep the two folders and their `.meta` |
| delete | `h_dohyun.fbx.meta`, so the old Generic import settings and remaps don't carry over (Resources-loaded, the GUID is unused) |
| copy, overwriting | `staging/h_dohyun.fbx` → `h_dohyun.fbx` (the new model) |
| copy | `staging/h_dohyun_tex/h_dohyun.png` → `h_dohyun_tex/h_dohyun.png` |
| copy | `staging/h_dohyun_anim.fbx` → `h_dohyun_anim.fbx` (the old clips; this is the only copy of them that stays in Assets) |
| create (empty, no extension) | `HUMANOID` (marker: every FBX in this folder imports as Humanoid) |

Don't copy `staging/*.blend`, `*_report.json` or `preview/`. They are for inspection only.

## 3. Check in Unity

1. `h_dohyun.fbx` → Rig: Animation Type **Humanoid**, Avatar Definition Create From This Model, no avatar errors.
   Under Configure, every required bone should be green: Hips=`mixamorig:Hips`, Spine=`Spine`, Chest=`Spine1`, UpperChest=`Spine2`,
   arms `LeftArm/LeftForeArm/LeftHand`, legs `LeftUpLeg/LeftLeg/LeftFoot`, toes `LeftToeBase`. Fingers are optional and should map too.
   The model should show in a T-pose. **Pose → Enforce T-Pose should change nothing.**
   Materials tab: `h_dohyun` → `h_dohyun_mat/h_dohyun.mat` (Abyss/Toon, `_BaseMap` = `h_dohyun.png`). Sync creates it; if it's
   missing, run `Abyss/Sync Textured Hero Materials`.
2. `h_dohyun_anim.fbx` → Rig: **Humanoid**, valid avatar with the same bone mapping, no fingers, Chest=`Spine1`, no UpperChest.
   Animation tab: 12 clips: Attack Cast Die Guard Hit Idle Revive Run Skill Ultimate Victory Walk.
   Idle, Run and Walk loop. Root Transform Rotation / Position Y / Position XZ are all *Bake Into Pose*, based on *Original*.
   Clip previews shouldn't show red muscle-range warnings.
3. Play (battle, town, dungeon):
   - The hunter stands at the same 1.3 m as before (`HeroDisplayHeight`; the model is authored 1.81 m like the old one).
   - Idle, Walk and Run play with feet on the ground. Die ends lying on the floor, not hovering.
   - The sword sits in the right fist. The rig has real `weapon.R` / `weapon.L` sockets, so the humanoid hand fallback isn't used.
     Bows go on `weapon.L`.
   - Hit flash, dissolve and the job/armour rim glow all show on the body.
   - Selection rings, approach distance and the camera framing match the old model (`Radius` ≈ 0.25).
   - Watch Victory / Ultimate (arms overhead) and Guard for arms clipping the body. That's the main retarget risk.

## 4. Regenerate

```
blender -b --factory-startup --python-exit-code 1 -P Blender/hunters_tripo/convert.py -- h_dohyun ArtSource/hunters/h_dohyun/tripo_export/tripo_convert_64e1b735-29f5-46f7-8bfd-8d262eacb1a0.fbx
blender -b --factory-startup --python-exit-code 1 -P Blender/hunters_tripo/anim_source.py -- h_dohyun --src <OLD h_dohyun.fbx>
blender -b --factory-startup --python-exit-code 1 -P Blender/hunters_tripo/retarget_preview.py -- h_dohyun --old <OLD h_dohyun.fbx>
```
After install, `Characters/h_dohyun/h_dohyun.fbx` is the Tripo model. To regenerate, pass the old Blender hero explicitly with
`--src` / `--old`: use git history or rebuild it with `Blender/heroes/generate_hunters.py`, writing outside Assets.
Use `C:\Users\User\Tools\Blender\blender.exe` (Blender 5.2).

## Rollback
`git checkout -- Assets/_Game/Resources/Art/Characters/h_dohyun` and `git apply -R` the patch. Then delete `HUMANOID`,
`h_dohyun_anim.fbx` and `h_dohyun_tex/h_dohyun.png` (+ metas).
