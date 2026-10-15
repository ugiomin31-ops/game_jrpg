# 41-town-ui — bounded read-only logic audit

- Requested model: `gpt-6-astra`; requested reasoning effort: `high`; requested service tier: Fast/priority.
- Observed model/effort/tier: no independent runtime attestation exposed by the available tools. Requested priority is not proof of the delivered tier. No model/configuration changes or nested agents were used.
- Verified checkout at initial inspection: branch `codex/astra-enrichment-20261015`, HEAD/base `efdc1517`.
- Scope: `Assets/_Game/Scripts/UI/Screens/GameUI.Town.cs`, `GameUI.TownHud.cs`, and focused direct references for facility entry, menu return, refresh and pending dialogue.
- Method: static working-tree source inspection only; prior evidence reused after reconnection. No tests, builds, Unity/editor/browser actions, network requests, auth reads, or source changes.
- Result: **1 concrete reachable logic finding**. Reproduction below is source-derived, not executed.

## [P2] A facility shortcut leaves an earlier NPC interaction queued, reopening it after return

**Location:** `Assets/_Game/Scripts/UI/Screens/GameUI.Town.cs:63-65` (facility entry does not supersede pending interaction), reached through `Assets/_Game/Scripts/UI/Screens/GameUI.TownHud.cs:163`.

**Repro:** With reduced motion off, stand near the innkeeper and press E. During the ordinary 0.8-second conversation-camera delay, click the HUD bestiary facility button. Close the bestiary. The inn menu then opens automatically without another interaction, instead of returning to free town control. Clicking the inn shortcut itself during the delay similarly makes the inn reopen after closing it.

**Source trace:**

- `Assets/_Game/Scripts/Runtime/World/TownWorld.cs:307-321` accepts the nearby interaction, sets `pendingTalk` and schedules a 0.8-second delay.
- `Assets/_Game/Scripts/UI/Screens/GameUI.cs:16-17` does not include pending NPC dialogue in `BlocksWorldInput`; before a menu appears, the facility callback at `GameUI.TownHud.cs:163` remains eligible.
- `GameUI.Town.cs:63-75` consumes the current input, calls `BeginTownTalk(id)` and opens the selected facility. `Assets/_Game/Scripts/Runtime/GameApp.cs:192` forwards this to `TownWorld.BeginTalk`.
- `TownWorld.cs:381-396` only adjusts camera/dialogue focus; it never clears `pendingTalk`. Bestiary has no NPC service, so this call simply returns false (the caller ignores that return).
- While the selected menu is open, `TownWorld.cs:262` returns before advancing the pending timer. After closing it, `:264-269` resumes the old timer and calls `app.OpenTownService` for the original NPC.

**Impact:** Returning from a deliberately selected facility unexpectedly opens a stale facility menu and interrupts town control. This is a pending-action ownership/state issue, independent of visual layout. It does not demonstrate duplicated purchases or other resource mutation.

**Integration direction:** Have explicit facility entry cancel or consume an outstanding world interaction, or consistently block shortcuts during that pending interaction. The coordinator should choose and validate the intended behavior; no fix was applied here.

## Other checked paths and limits

- Successful services refresh the owner menu, vitals and town state through `GameUI.cs:76-84`; town refresh reaches header, gold and readiness through `GameUI.Town.cs:30-36`.
- Returning from child menus restores focus and refreshes content through `Assets/_Game/Scripts/UI/Kit/UIScreen.cs:193-202` and `GameMenuScreen.cs:186`. No second concrete return-state defect established in this bounded pass.
- Facility ID lists and dispatch cases in the two assigned files agree. No unknown-ID or malformed-save hypothetical is reported.
- Reports 01–06 were consulted for overlap; no matching town finding was found. Report 07 was not present in the initial matching file listing.
- No runtime or visual correctness certification is made.

## Acceptance

- [x] Assigned facility/return/state paths inspected with focused reads.
- [x] At most two findings; one finding includes exact locations, reachable repro and impact.
- [x] Requested routing distinguished from independently verified runtime evidence.
- [x] No prohibited execution, nested delegation, source edits or configuration changes.
- [x] Only this assigned report written; integration remains with the main coordinator.