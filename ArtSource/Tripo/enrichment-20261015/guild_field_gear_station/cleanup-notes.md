# Guild field gear station cleanup — 2026-10-15

Requested model/effort: `gpt-6-astra` / `high`; actual model/service tier is not independently exposed by this session. No child agents. Blender executable: `C:/Users/User/Tools/Blender/blender.exe`, observed version **5.2.1 LTS**. Existing `Tools/verify_tripo_rig.py` and `Tools/store/render_art.py` were inspected for import, validation and rendering conventions.

## Parent import handoff

- Canonical mesh: `processed/guild_field_gear_station.fbx`.
- ArtSource PBR package: **`processed/guild_field_gear_station_tex/`**. The exported FBX references that folder; earlier `processed/textures/` is only the previous working copy. The game's basecolor-only Toon import is documented below.
- Exact material name: **`tripo_mat_3551cec0`**. One mesh object, `guild_field_gear_station`, one material slot, one `UVMap`. Parent reports the engine material was automatically created with shader **`Abyss/Toon`**.
- **Unity/FBX local dimensions X/Y/Z: 1.400000 / 1.050000 / 0.665381 metres. Visual front is +Z; up is +Y.** Source front is Blender -Y. Export flags are `axis_forward='-Z'`, `axis_up='Y'`, `bake_space_transform=True`, unit scale 1 metre; the explicit source-front conversion yields `(0, 0, 1)` and the reimported mesh-local bounds confirm width/height/depth order.
- Origin: bottom center `(0,0,0)`. Export reimport ground error approximately `-2.06e-8 m`; scale `(1,1,1)`. Blender reimport applies its expected 90-degree X axis conversion; the saved working BLEND mesh has zero rotation and applied scale.
- Parent destination: `Assets/_Game/Resources/Art/Props/GuildFieldStation/guild_field_gear_station.fbx`, with sibling `guild_field_gear_station_tex/`.
- Resource load path: **`Art/Props/GuildFieldStation/guild_field_gear_station`**.
- This worker performed no Unity launch/import, C# changes, logic compiler, network, image editing or new procedural asset geometry. Engine integration remains parent-owned.

## Final TownEnrichment helper contract

- Local **+X = width, +Y = height/up, +Z = visual front**. At unit scale the dimensions are `Vector3(1.4f, 1.05f, 0.665381f)`; the expected helper value `0.665f` is a rounded depth.
- Pivot is **bottom center**, so place the instance origin at the intended ground point; do not add half its height as a placement offset. Bounding-box center is approximately local `(0, 0.525, 0)`.
- Identity placement faces world **+Z**. Use yaw around world/local **+Y** to orient the station: 0 degrees → +Z, 90 → +X, 180 → -Z, 270 → -X. For a horizontal desired front direction, the placement rotation is `Quaternion.LookRotation(frontDirection, Vector3.up)`.
- Use unit instance scale to retain the measured dimensions. Do not add an X-axis +/-90-degree correction based on Blender's reimport rotation: that rotation is Blender's Y-up-to-Z-up conversion, already accounted for in the exported FBX.
- Resource key is exactly `Art/Props/GuildFieldStation/guild_field_gear_station` (without extension).

Parent-reported integration, recorded after cleanup:

- FBX, TRIPO marker and basecolor have been imported under `Assets/_Game/Resources/Art/Props/GuildFieldStation`.
- The current importer resolves `*_tex/<material_name>.png`. Its exact basecolor alias is **`Assets/_Game/Resources/Art/Props/GuildFieldStation/guild_field_gear_station_tex/tripo_mat_3551cec0.png`**, copied from ArtSource's `guild_field_gear_station_basecolor.PNG`.
- `Abyss/Toon` uses that basecolor. Metallic/roughness/normal maps remain in ArtSource processed; no additional PBR map import is required by this helper contract.
- Parent reports current compilation completed with **0 errors, 1 warning**. The warning has not yet been read/classified; this is parent-provided evidence, not a compiler run or warning assessment by this worker. Runtime placement/render acceptance remains parent-owned.

## Actual cleanup and checks

- Source: 1 static mesh, 3,186 vertices, **6,387 triangles**, no armatures. Initial Blender dimensions approximately `0.977631 × 0.464905 × 0.782471 m` (width/depth/height).
- One gentle COLLAPSE modifier at `5990/6387`, applied with triangulation: **2,986 vertices, 5,990 triangles**, a reduction of 397 triangles (6.216%). No remesh, new mesh components or UV unwrap.
- Width/depth scaled together to 1.4m width; height set to 1.05m (about 6.3% shorter relative to uniform scaling). Centered horizontally and grounded. Final tiny bounds correction follows decimation. No appearance-generating operations.
- Retained UVs/material; invalid UV values, invalid material indices and zero-area triangles are all **0**, before and after and in the FBX roundtrip.
- Four active textures are **1024×1024 PNG**, copied byte-for-byte from the ZIP: `guild_field_gear_station_basecolor.PNG`, `_metallic.PNG`, `_roughness.PNG`, `_normal.PNG`. Texture bytes were not resized, repainted or regenerated. The original unused 2048px `_rm.PNG` remains in staging/raw archive and is not used by the exported material.
- Corrected the imported FBX legacy mapping: authored metallic image now feeds Principled Metallic rather than Specular IOR. Existing base color, normal, roughness and alpha retained. Reimported final FBX has all four maps loaded and the Metallic connection present.
- Final FBX is mesh-only with animations disabled and relative texture paths. The saved BLEND also includes the evidence cameras/lights, which are excluded from FBX export.
- Raw ZIP SHA-256 remains `fd89c9e1560263679fa9713a749ae54f721339be9226997d019998e1e307fe6e`.
- Raw loose FBX SHA-256 remains `7ab5a2bbfbace46bbf52549b181f23485625e1d2cf9bf0ee26d40f503b2bb040`. Raw inputs were never used as Blender's writable extraction location; staging is under `processed/source_input/`.

## Evidence and acceptance

- `processed/evidence/before-front.png`, `before-rear.png`, `after-front.png`, `after-rear.png`: actual 960×960 Blender Cycles renders, CPU 4 threads, 24 samples. Before means original 6,387-triangle geometry with the **same normalized dimensions, corrected PBR material, camera and lighting** as after; it is not an untouched raw-import screenshot. No compositing or post-image editing.
- All four renders were visually inspected here. The parent explicitly approved before-front, after-front and after-rear, confirming reference D appearance and no concerning decimation difference. The subsequent `_tex` packaging changed only file references, not geometry, texture pixels, shading parameters or approved renders.
- `processed/cleanup-validation.json`: raw hashes, geometry/material/texture inspection, final dimensions, FBX roundtrip, final export hash and +Z front evidence; `passed=true`.
- `processed/blend-validation.json`: separately reopened saved BLEND, all image paths resolve inside processed and load, 5,990 triangles; `passed=true`.
- `processed/artifact-manifest.json`: final FBX/BLEND, canonical textures and render hashes. Logs: `blender-process.log`, `blender-package.log`, `blender-blend-check.log`.
- `processed/source_input/`, old `processed/textures/`, and Blender's `.blend1` packaging backup are working evidence, **not additional engine import assets**. The engine uses the canonical FBX and the basecolor alias described above; the full PBR set remains available in ArtSource.
- [x] <=6,000 triangles; target dimensions; ground/origin; UV/material validation; unchanged raw bytes; four identical 1K source textures; FBX roundtrip; saved BLEND reload; real before/after evidence; parent appearance approval.

Reproduction script: `Tools/prepare_guild_field_station.py`. Headless stages: `--stage inspect`, `--stage process`, optional `--stage package` for the existing legacy texture-folder working copy, and `--stage verify-blend`. Start with `--background --factory-startup --threads 4 --python-exit-code 1 --python Tools/prepare_guild_field_station.py -- ...`. No operation requires Unity.
