# 23 — Exploration resources: bounded read-only audit

- Requested model: `gpt-6-astra`; requested reasoning effort: `high`.
- Requested service tier: Fast/priority. Actual model, effort and service tier are not independently attested by the available session metadata; no routing/configuration changes were made.
- Branch verified during this audit: `codex/astra-enrichment-20261015`; HEAD/base: `efdc1517f48ac8887e1fcf6843b6df44df6ebc3c`.
- Scope: exploration attrition, traps, springs, field consumables and recovery routes. Sources were inspected in the working tree; branch/HEAD verification does not establish that every working-tree file equals the commit.
- Method: focused source reads only. Resumed using evidence collected before the reconnection; no tests, builds, Unity/editor/browser actions, network requests, nested agents, secret reads or source changes.
- Result: **0 concrete reachable findings established in this bounded pass.** No hypothetical extreme-input finding is included.

## Evidence

Paths are repository-relative. These are static observations, not executed reproductions.

- **Trap attrition does not directly wipe the party:** `Assets/_Game/Scripts/Logic/Dungeon/DungeonRun.cs:253-256` applies traps only when stepping onto the cell. `Assets/_Game/Scripts/Logic/Game/PartyStats.cs:377-400` skips fallen hunters, clamps each standing hunter to at least 1 HP, and may apply poison. Poison can still endanger the next battle; the clamp is not a claim of immunity to subsequent defeat.
- **Springs cannot repeatedly heal during the same outing:** `Assets/_Game/Scripts/Logic/Dungeon/DungeonRun.cs:257-260` adds the cell to persisted `SpentSprings` before restoration and rejects another use. `Assets/_Game/Scripts/Logic/Game/PartyStats.cs:366-374` restores active-party HP/MP, clears statuses and revives fallen hunters. It does not restore reserve hunters or manufacture items.
- **Spring reset follows explicit recovery boundaries:** `Assets/_Game/Scripts/Logic/Dungeon/DungeonRun.cs:421-426` refills springs on return to town; `Assets/_Game/Scripts/Logic/Game/GameFlow.cs:136-140` does so on town entry. `Assets/_Game/Scripts/Logic/Game/TownServices.cs:131-143` checks inn payment before recovery, also refilling springs and respawning FOEs. Returning to town and revisiting a spring is consistent with the documented per-outing rule, so it is not classified as an exploit without a contrary contract.
- **Defeat supplies a recovery path even without gold or consumables:** `Assets/_Game/Scripts/Logic/Dungeon/DungeonRun.cs:403-405` clears the pending battle and records defeat. `Assets/_Game/Scripts/Logic/Game/GameFlow.cs:186-195` consumes that flag once, applies the difficulty-dependent gold loss and requests a free inn rest. `Assets/_Game/Scripts/UI/Screens/GameUI.cs:230` exposes recovery; `Assets/_Game/Scripts/Runtime/GameApp.cs:354-358` invokes it and enters town. This prevents an asserted permanent resource lock based solely on exhaustion; it is not a full campaign solvability proof.
- **Field recovery consumes an item only after an effect:** `Assets/_Game/Scripts/Logic/Game/GameFlow.cs:213-236` rejects pending battles, pending defeat, missing inventory and invalid targets. `:243-281` handles living-only HP/MP recovery, fallen-only revival and eligible status removal; `:284-285` rejects no-effect use before deduction. The shipped tent at `Assets/_Game/Resources/Data/items.json:75-92` explicitly excludes fallen allies, matching the healing implementation. `Assets/_Game/Scripts/UI/Screens/GameUI.Party.cs:349-387` calls this path from the inventory UI and routes a successful escape consumable to town; `Assets/_Game/Scripts/Runtime/GameApp.cs:349-352` performs that return.
- **Battle attrition is carried back into exploration:** `Assets/_Game/Scripts/Logic/Game/PartyStats.cs:444-458` commits final HP/MP/TP/statuses and removes used items. `Assets/_Game/Scripts/Logic/Dungeon/DungeonRun.cs:367-369,403-408` guards settlement with the pending request and clears it after settlement; a repeated resolution returns the prior result rather than deducting resources again.
- **Food scope:** focused searches of the game logic, field-item UI, `GameState.cs` and `items.json` did not identify a separate hunger/food/meal subsystem. Consumable recovery was therefore assessed through the actual field-item path; no absent food mechanic is reported as a defect.

## Limits and acceptance

- [x] Traced traps, one-use springs, town/inn/defeat recovery, field items and battle resource settlement.
- [x] Used ordinary reachable source paths; reported none rather than speculative findings.
- [x] Recorded requested model/effort and distinguished requested priority from verified execution metadata.
- [x] Wrote only `docs/verification/astra-enrichment-20261015/agent-reports/23-exploration-resources.md`; no game fixes or configuration changes.
- [x] No tests, builds, runtime actions or nested agents were performed.

This bounded pass does not certify every authored map, encounter balance or save/resume interleaving. Runtime behavior was not exercised, and previously collected line references were reused after reconnection. Integration and final acceptance remain with the main coordinator.
