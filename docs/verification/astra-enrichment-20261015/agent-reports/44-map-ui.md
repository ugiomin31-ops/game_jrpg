# 44-map-ui — bounded read-only audit

- Repository: `C:\Users\User\Desktop\GAME_JRPG\handoff-verify-20261015`
- Verified branch: `codex/astra-enrichment-20261015`; HEAD/base: `efdc1517f48ac8887e1fcf6843b6df44df6ebc3c`.
- Requested model: `gpt-6-astra`; requested reasoning effort: `high`; requested service tier: Fast/priority. The available audit outputs do not independently attest the executing model, effort or service tier; requested priority is not a verified tier. No model/configuration changes or nested agents were used.
- Method: focused static inspection of the three assigned map classes and their grid, position, theme and HUD call sites. No tests, builds, Unity/editor/browser actions, network requests or source edits. Reports 01–07 available in the permitted directory were searched for map-related duplicates; none matched.

## Finding 1 — P2: map symbols disappear into identically colored tile backgrounds

**Primary location:** `Assets/_Game/Scripts/UI/Screens/DungeonMapGraphic.cs:95–96`.

`OnPopulateMesh` first paints a filled tile and then its symbol (`DungeonMapGraphic.cs:47–50`). `TileColor` gives `B`, `E` and `X` the same `UITheme.Danger` background (`:85`), and `DrawSymbol` uses that exact color for their crown, triangle and trap shapes (`:95`, `:130–137`, `:149–150`). At ordinary map/minimap cell sizes these shapes sit wholly within the filled tile, so the three markers appear as identical solid red squares. The same problem hides `H`/`R` shapes against `Positive` and `W` against `Mp` (`:83–84`, `:96`). The legend remains distinguishable because its symbols are drawn over `UISlant.Deep` swatches (`GameMapScreen.cs:126–130`), making its promised shapes unavailable on the actual map.

**Reachable repro for the coordinator (not executed):** In ordinary dungeon exploration, reveal an uncleared `E` encounter or `B` boss cell, then open the map. Separately, step on an `X` trap, move off it so the party arrow does not cover it, and reopen the map. `DungeonGrid.MapMarker` exposes explored encounter/boss cells and stepped traps (`Assets/_Game/Scripts/Logic/Dungeon/DungeonGrid.cs:110–119`); normal movement reveals cells and stepping on a trap records it (`DungeonRun.cs:145–146`, `:255`). Compare these tiles with the legend: the red crown, encounter triangle and trap cross cannot contrast with their identical red backgrounds. A revealed healing kit and rescue event likewise both become plain green tiles.

**Impact:** Players cannot distinguish known traps, fixed encounters and bosses by the documented map symbols, or distinguish healing kits from rescue events. This affects both the full map and HUD minimap, which share `DungeonMapGraphic`. Use a contrasting symbol foreground or a darker tile fill while preserving marker semantics.

## Acceptance record

- [x] Scope limited to assigned map behavior and directly relevant sources.
- [x] One concrete finding, with exact source locations and a normal gameplay reproduction path; no hypothetical extreme input findings.
- [x] Reveal filtering, spent-marker suppression, off-floor party/FOE hiding, coordinate inversion and player-arrow direction inspected; no additional concrete defect established in these paths.
- [x] Only this assigned report written. Runtime/visual verification remains with the main coordinator; this is not a visual acceptance claim.
