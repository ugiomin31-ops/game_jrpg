# Map marker contrast fix

Status: source change applied; post-change Unity capture and final visual acceptance belong to the parent coordinator.

Requested model: `gpt-6-astra`; effort: `high`; requested tier: Fast/priority. These are the requested settings, not independently verified runtime model/effort/tier telemetry. No model/configuration changes or nested agents were used.

## Before evidence inspected

Read `docs/verification/astra-enrichment-20261015/runtime/world-20261015-134913-394/result.json` and personally opened both map PNGs with `view_image` before editing:

- `map-before-fix-all-revealed-floor-2-1280x720.png`, SHA256 `19576f62ca91b384efa494df56dfade5e9e3fa789f0f92e7ae609eeb78530b8f`.
- `map-before-fix-all-revealed-floor-2-915x412.png`, SHA256 `a586aabf8e6e24e5359bda57b2ee825405f0dacfd4ca39f88b9ee2dd79d8f366`.

Both PNG hashes match the supplied result record. Both images show solid red encounter/boss/trap tiles, a solid green healing tile and a solid blue warp tile, whereas the legend visibly contains their distinct bright shapes. This corroborates report 44's same-color fill/foreground defect. Only these two map images were reviewed here, not the other six world captures.

Pre-edit `DungeonMapGraphic.cs` SHA256 was `3ab4dc8d542124539c7be2f529a2b7593b807bc756696a5797e05a321b58b476`, matching `build.mapSourceSha256` in the result. This establishes the source match; the parent's compiled-assembly identity and wider runtime checks were not rerun or independently certified here.

## Change

At `Assets/_Game/Scripts/UI/Screens/DungeonMapGraphic.cs:83–85`, `TileColor` now returns the existing `UITheme.SurfaceRaised` token for `W`, `H`, `R`, `B`, `E` and `X`. The token is the existing opaque #192B38 surface (`Assets/_Game/Scripts/UI/Kit/UITheme.cs:101`). Their existing bright Mp/Positive/Danger symbol colors remain in `DrawSymbol`, matching the unchanged legend. No new palette values, geometry, layout, alpha or rendering passes were introduced.

All other tile colors, `MapMarker` calls, fog/spent suppression, event classification, player position/direction, FOE rules, symbol geometry and legend code are unchanged. Full-map and minimap callers share this corrected tile fill.

Appended only the map marker contrast contract to `design.md:37–38`; previous design content was preserved.

Post-edit source SHA256: `836753cbab01d3e60a478eee7bedd4b804d512852d396bf067492a62637b204b`.

## Verification and handoff

- [x] Inspected actual before PNGs at 1280x720 and 915x412; verified their hashes and the source hash against `result.json`.
- [x] Reviewed the final source diff: one localized switch change, with no fog/spent logic, shape, legend or layout edits.
- [x] `git diff --check` passed for the source and design append.
- [x] Only the owned source, this fix note and the explicitly allowed design append were written.
- [ ] Parent: capture the same floor/resolutions using the compiled changed source; confirm distinct bright boss/encounter/trap/healing/warp symbols on the dark fill. Include rescue `R` and the HUD minimap, and retain the existing hidden/spent checks for final acceptance.

No Unity/editor actions, compilation, tests, browser actions or network requests were performed. No after screenshot was created or visually accepted by this worker; the supplied before-run PASS is not evidence for this changed source.
