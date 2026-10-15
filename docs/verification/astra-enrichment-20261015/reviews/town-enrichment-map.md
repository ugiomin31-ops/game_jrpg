# Town enrichment, station import and map contrast — independent review

**Verdict: approve the reviewed source/configuration changes. No actionable defect established. Runtime/visual acceptance remains pending.**

Requested model/effort: `gpt-6-astra` / `high`; requested Fast/priority is not independently attested. No model/configuration changes or nested agents. Reviewed working-tree files on `codex/astra-enrichment-20261015`, the current `design.md`, report 35, map fix note and station cleanup record. No Unity/editor, compile, test, browser or network execution. Only this report was written.

## Source evidence

- **Station integration and collision:** `Assets/_Game/Scripts/Runtime/World/TownWorld.cs:110–112` calls enrichment before environment processing; camera collection follows at `:137`. `TownEnrichment.cs:26–48` reuses the named station and its child collider, applies a fixed local position/rotation, and creates only one non-trigger box. The visible model is not named `Col_`; only its empty collider child is, matching `EnvironmentProcessor.cs:34–39` without stripping the station renderer. Box dimensions (1.4 × 1.05 × 0.665) and bottom-centered placement agree, within rounding, with the recorded exported FBX local dimensions (1.4 × 1.05 × 0.66538). Ground clearance, route width and silhouette still require a live scene check.
- **Tree proxy:** `TownEnrichment.cs:20–23` moves the legacy named proxy to the visual tree's world X/Z while retaining height and rotation; it uses Transform positions before physics synchronization. The related generation change at `Blender/town/guild.py:351` now uses `(-11.8, -5.4)`, matching the instance in `Blender/town/tripo_pieces.json:682–689`. Its generated collider gets a coordinate-derived name (`guild.py:253–254`); therefore the runtime legacy-name correction safely does nothing on a regenerated town whose proxy is already at the new location. Actual trunk coverage/clearance remains unmeasured here.
- **Station import configuration:** the Resources FBX exists at the exact path used in `TownEnrichment.cs:10`. Its bytes match `processed/cleanup-validation.json`'s exported SHA256. That record reports 5,990 triangles, zero armatures and grounded dimensions; I did not rerun its Blender verification. `guild_field_gear_station.fbx.meta:23–26` maps the Tripo material to GUID `6a4e434d7bdea8e42a812dabca24310e`, matching the material sidecar. The material's `_BaseMap` at `guild_field_gear_station_mat/tripo_mat_3551cec0.mat:26–27` maps to the existing texture GUID `164b2b7108162d347b59b7dcedce010d`. Import metadata uses scale 1, no generated colliders, no animation and a non-readable static mesh. These are consistent with the explicit runtime box and the small prop, whose height is below TownCamera's canopy-voxel region (`TownCamera.cs:114–119`).
- **Importer scope clarification:** `Assets/_Game/Scripts/Editor/AbyssArtImporter.cs` has no staged or unstaged diff in this checkout. I reviewed the new station import metadata/materials against its existing environment and texture-remapping paths (`:136–139`, `:174–197`), plus the station packaging/export section of `Tools/prepare_guild_field_station.py:311–365`. This is not approval of an unseen separate importer implementation.
- **Map contrast:** the only `DungeonMapGraphic.cs` diff is the fill selection at `:83–85`: W/H/R/B/E/X now use `UITheme.SurfaceRaised`. Existing Mp/Positive/Danger symbol colors remain at `:95–96`. Geometry, fog/spent-marker filtering, event classification, party/FOE display and legend were not changed. This matches the explicit map contrast contract appended to `design.md`, using existing tokens rather than changing global colors or layout.

## Parent runtime gates

1. Use the compiled current sources in a fresh title/town entry. Verify one station/one solid child collider, visible textured mesh, correct scale/orientation/grounding, and no missing-resource/import/console errors. Walk the party around the station and reach adjacent NPC/facility interactions; check camera visibility and central-scene clearance. Reapply enrichment on a controlled town instance to confirm no duplicate station/collider.
2. Inspect the legacy tree proxy against the actual trunk, traverse its previous empty location and the relocated tree with leader/followers, and verify collider height/footprint. Confirm the generation change and runtime legacy correction do not double-relocate an updated town asset.
3. Capture the same full-map floor at 1280×720 and 915×412 after recompilation. Check W/H/R/B/E/X bright symbols on the dark fill, including rescue R and the HUD minimap, plus hidden/spent tiles, player arrow and FOEs. Compare before/after images required by `design.md`; this review did not inspect new rendered captures.

These checks are outstanding acceptance work, not discovered code defects. No visual, physics, import-execution or full integration pass is claimed.

## Reviewed snapshot (SHA256)

| File | SHA256 |
| --- | --- |
| `TownEnrichment.cs` | `c9ca9ff24f7de6b4b3309d37442b348d4941fa46bdbe037c2a06c2bfe4906ae4` |
| `DungeonMapGraphic.cs` | `836753cbab01d3e60a478eee7bedd4b804d512852d396bf067492a62637b204b` |
| `AbyssArtImporter.cs` | `d1381a3f6774e5d795964cb069fb1556dbc66806ad34c114c26a49be4a41e628` |
| Station FBX | `d64da8135e4c0843d0c2a8e15516e6d450b98a29830207104ee367d35f73f78d` |
| Station FBX `.meta` | `90ce20e2b0dfb20330b8ea7215774d7018cb61fbbee9a595dfc7104307f67e64` |
