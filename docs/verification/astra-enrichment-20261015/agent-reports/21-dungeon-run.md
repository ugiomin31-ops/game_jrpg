# 21 — DungeonRun bounded audit

- Requested model: `gpt-6-astra`; requested reasoning effort: `high`.
- Requested service tier: Fast/priority. Actual model, effort and service tier cannot be independently verified from the available session evidence; requested routing is not an attestation.
- Verified checkout: `codex/astra-enrichment-20261015`, HEAD `efdc1517f48ac8887e1fcf6843b6df44df6ebc3c` (matches expected base `efdc1517`). Inspected current working files, not an asserted clean commit snapshot.
- Method: bounded static source inspection only. No nested agents, tests, builds, application/editor/browser actions, network requests, or source/configuration changes.
- Verdict: **0 concrete reachable findings established in this bounded pass.** This is not runtime acceptance or an exhaustive correctness claim.

## Evidence and acceptance checklist

All paths are relative to the checkout root.

- [x] Movement and collision: `Assets/_Game/Scripts/Logic/Dungeon/DungeonRun.cs:137-148` checks action eligibility, opens a closed door without moving, rejects walls and commits position before entry effects. `Assets/_Game/Scripts/Logic/Dungeon/GridPos.cs:10-11,43-44` defines relative movement/rotation consistently. `Assets/_Game/Scripts/Logic/Dungeon/DungeonGrid.cs:48-57` treats out-of-bounds as walls and consumes one key only when opening a locked door.
- [x] Interaction and waiting: `DungeonRun.cs:173-202` gives the facing door precedence, allows an uncleared fixed encounter on the current cell, and advances FOEs when an otherwise empty interaction becomes Wait. Turning and opening doors do not advance FOEs; no contrary turn-cost requirement was established, so this is not reported as a defect.
- [x] Encounter/effect order: `DungeonRun.cs:147-170,204-221` handles direct FOE contact first, then FOE movement, fixed encounters and cell effects. Random encounters require no cell effect, enough steps and a nonempty encounter group. Direct contact bypasses cell effects; no independently established violated gameplay contract is claimed for that precedence.
- [x] Transition safety: `DungeonRun.cs:228-239` changes floors on stairs. The apparent risk of using an old caught-FOE index after changing floors is excluded by `DungeonGrid.cs:172,182,211-228`: FOEs cannot path onto stairs, starts, warps, boss or event cells. No cross-floor-index finding is asserted.
- [x] Trap behavior: `DungeonRun.cs:253-256` applies traps on movement only; `Assets/_Game/Scripts/Logic/Game/PartyStats.cs:377-401` preserves at least 1 HP for standing heroes and applies poison before any subsequently caught FOE battle is prepared. Thus this inspected path does not create an all-dead trap party or prepare that battle before trap damage.
- [x] Rewards/events: `DungeonRun.cs:242-260,275-326` guards chest/key/spring consumption and rescue rewards with persisted sets, blocks actions during a pending choice, and rejects stale choice objects. Dismiss keeps the choice unspent; Leave spends it; Accept creates a pending event battle. Victory settlement guards the extra event reward at `DungeonRun.cs:381-388`.
- [x] Arrival/resume/return: `DungeonRun.cs:87-129,403-426` validates the floor, restores a walkable resume position, rejects floor changes with a pending battle, resets encounter steps on arrival/settlement and blocks actions after defeat. `DungeonGrid.cs:74-98` selects ascent arrival and facing.
- [x] Actual callers: `Assets/_Game/Scripts/Runtime/World/DungeonWorld.cs:432-477` gates input and passes movement/interaction results to the app; `Assets/_Game/Scripts/Runtime/GameApp.cs:232-279` handles town/floor transitions before ordinary effect presentation and saves before starting battles. These were read, not executed.
- [x] Consulted available reports 01–06 for overlap; no report 07 was returned by the scoped inventory at inspection time. Prior reports' test results were not adopted as evidence for this audit.
- [x] Only the assigned report written; no game fixes or other deliverables created.

## Limits

No runtime reproduction was performed, as requested. Shipped dungeon-data excerpts were inspected for layout/FOE context, but complete path enumeration and every authored floor combination were outside this bounded pass. No hypothetical extreme-input issue is included.
