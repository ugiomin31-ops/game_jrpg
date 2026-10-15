# 55 — Defeat and recovery audit

- Scope: full-party defeat, town respawn, revive costs, and reachable recovery softlocks. Static source inspection only.
- Repository: `C:\Users\User\Desktop\GAME_JRPG\handoff-verify-20261015`.
- Observed branch: `codex/astra-enrichment-20261015`; observed HEAD/base: `efdc1517f48ac8887e1fcf6843b6df44df6ebc3c`.
- Requested execution: model `gpt-6-astra`, reasoning effort `high`, Fast/priority service tier. Actual model/effort and service tier are not independently verifiable from the permitted source inspection; requested priority is not a verified tier claim. No routing or configuration changes made.

## Findings

**None.** No concrete reachable recovery softlock was identified in the bounded paths inspected. This is a static audit conclusion, not runtime acceptance.

## Evidence and traced scenarios

1. **Full-party defeat at zero gold still has a recovery path.** `Assets/_Game/Scripts/Logic/Battle/BattleEngine.cs:1557` ends combat as defeat when no party member survives and enemies remain. `Assets/_Game/Scripts/Logic/Dungeon/DungeonRun.cs:403-405` clears the pending encounter and records `defeat_pending`. `Assets/_Game/Scripts/UI/Screens/GameUI.cs:225-233` exposes recovery without a money requirement. `Assets/_Game/Scripts/Logic/Game/GameFlow.cs:186-195` removes that flag, deducts the percentage penalty, invokes `RestAtInn(..., free: true)`, and sets town location. `Assets/_Game/Scripts/Logic/Game/TownServices.cs:109-113` makes zero gold incur zero loss; lines 133-139 make the recovery rest cost zero and restore the entire roster. `Assets/_Game/Scripts/Logic/Game/PartyStats.cs:366-374` restores HP/MP and clears statuses, including KO. Thus spending all money/items and then losing does not require a paid revive to resume.

2. **Saving/reloading the defeated state retains recovery, and town arrival persists it.** `Assets/_Game/Scripts/Runtime/Battle/BattleView.cs:1469-1472` resolves and saves before result acknowledgement; lines 1497-1506 route onward after acknowledgement. `Assets/_Game/Scripts/Runtime/GameApp.cs:327-331` opens defeat recovery. On reload, `Assets/_Game/Scripts/Logic/Game/GameFlow.cs:105-110` prioritizes the defeat flag and `Assets/_Game/Scripts/Runtime/GameApp.cs:129-130` reopens that screen. Recovery calls `EnterTown` at lines 354-358; lines 154-164 rebuild town and save the recovered state. Recovery removes the pending flag before returning, so a repeated recovery call does not reapply the penalty.

3. **Ordinary revive prices are not mandatory recovery tolls.** `Assets/_Game/Resources/Data/items.json:762-773` defines the 30% revive at 300, and lines 780-791 define the full revive at 2,000. Field revival requires a KO target and restores at least 1 HP (`Assets/_Game/Scripts/Logic/Game/GameFlow.cs:262-268`). Ordinary inn rest costs `10 + round(4 × average party level)` (`Assets/_Game/Scripts/Logic/Game/TownServices.cs:118-123`) and restores active/reserve hunters together at lines 131-139. The defeat route bypasses this charge, so unavailable shop tiers or unaffordable items do not prevent defeat recovery.

4. **Re-entry and alternative recovery remain available.** `Assets/_Game/Scripts/Logic/Game/TownServices.cs:584-600` always includes floor 0 and validates departure by unlocked destination, without a fee or HP gate. Its menu exposes those destinations (`Assets/_Game/Scripts/UI/Screens/GameUI.Town.cs:325-332`). Springs restore the active party without payment (`Assets/_Game/Scripts/Logic/Dungeon/DungeonRun.cs:257-260`); town return refills springs at lines 421-426, and the first-floor upward stair returns to town at lines 228-232. Traps preserve at least 1 HP (`Assets/_Game/Scripts/Logic/Game/PartyStats.cs:389-393`). These checks did not reveal an economic recovery lock.

## Completion checklist

- [x] Verified expected branch and base commit.
- [x] Traced defeat detection, pending state, result acknowledgement, reload, town recovery, costs, and re-entry.
- [x] Checked relevant matches in available reports 01–06 for overlap; report 07 was not present in the inspected listing.
- [x] No tests, builds, Unity/editor/browser actions, network calls, nested agents, secret reads, or source/configuration changes. Only this assigned report was written.
- [x] No runtime repro claimed; final integration and acceptance remain with the main coordinator.
