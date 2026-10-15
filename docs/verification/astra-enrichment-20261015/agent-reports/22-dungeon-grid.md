# 22-dungeon-grid — bounded read-only audit

- Requested model: `gpt-6-astra`; requested reasoning effort: `high`; requested service tier: Fast/priority.
- Actual model/effort and service tier are not independently exposed/verified by this audit. No model, persona, configuration or routing change was made.
- Verified branch: `codex/astra-enrichment-20261015`; HEAD/base: `efdc1517f48ac8887e1fcf6843b6df44df6ebc3c`.
- Scope: `DungeonGrid.cs`, authored `dungeon.json`, and focused `DungeonRun.cs`/`GridPos.cs` caller context. Reports 01–06 consulted for duplication; 07 was not present in the listing.
- Method: static source reads and JSON field/coordinate extraction only. No tests, builds, Unity/editor/browser actions, network, nested agents or source edits. Coordinates below are zero-based (x,y).
- Result: **1 concrete reachable finding**, statically established; no runtime reproduction claimed.

## [P2] Ascending past a boss/event floor returns the party to its entrance

**Location:** `Assets/_Game/Scripts/Logic/Dungeon/DungeonGrid.cs:81-85`; related exclusion at `:172`.

**Authored repro:** Clear the subway_3 boss normally, descend through `>` at (7,9) into gate_e_1, then return through gate_e_1's `<` at (17,17). The latter is adjacent to its arrival start at (17,16), so this requires only an ordinary return step after descent.

**Evidence:**
- `Assets/_Game/Resources/Data/dungeon.json:441,448-450` places subway_3's start at (6,1), its exit at (7,9), walls north/east/south of the exit, and the boss tile `B` west at (6,9).
- `Assets/_Game/Resources/Data/dungeon.json:681-682` places gate_e_1's start and return stair at the coordinates above.
- `Assets/_Game/Scripts/Logic/Dungeon/DungeonRun.cs:228-235` follows the return stair with delta -1; `:120-124` assigns the result of `ArrivalCell(-1)` directly to the player position.
- `DungeonGrid.cs:81` finds no ordinary `.` neighbor. Its fallback at `:82` calls `FoePassable`, which excludes `B` and `E` unconditionally at `:172`, even after their battles are cleared. Therefore `:85` returns (6,1), the floor entrance, instead of the walkable cleared boss tile next to the exit.
- The same authored pattern occurs at the other eleven main-route boss floors and at red_gate_1/red_gate_2 exits. For example, `dungeon.json:12608-12610` surrounds red_gate_2's (19,25) exit with walls and an `E` tile at (20,25).

**Impact:** Normal stair backtracking unexpectedly relocates the party across the previous floor. A player who immediately returns to the newer floor must traverse the older floor again, with its encounters and reset surviving FOEs. This is an arrival-position defect, not a claim that progression is permanently blocked.

## Coverage and limits

- [x] Read grid walkability, locked-door/key consumption, arrival selection, FOE reset and path search; traced ordinary movement and stair callers.
- [x] Extracted S/< />/K/L locations across all 39 authored floors: each has a start and return stair; only the final red_gate_3 lacks a descending stair. Reviewed all 38 descending-stair neighborhoods.
- [x] Compared authored FOE spawn/patrol coordinates with their row markers; the extraction found no wall or S/< />/W/B/E coordinates among those entries. This does not prove patrol-route connectivity.
- [x] Inspected key/door counts and representative row layouts. Door opening consumes one key and preserves the opened-door state; keys are collected once through TakenKeys. No additional concrete locked-path defect established.
- [x] No exhaustive connectivity/key-order state exploration or runtime acceptance was performed, as execution tests were outside authorization. No universal reachability guarantee is made.
- [x] At most two findings; one reported. Only this assigned report was written; game fixes remain with the coordinator.
