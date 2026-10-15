# 14 — Game flow bounded audit

- Requested model: `gpt-6-astra`; requested reasoning effort: `high`.
- Requested service: Fast/priority. Actual model, effort, and service tier are not independently attested by available session evidence; no configuration/model changes or substitution were performed.
- Verified branch: `codex/astra-enrichment-20261015`.
- Verified HEAD/base: `efdc1517f48ac8887e1fcf6843b6df44df6ebc3c`. Findings refer to current on-disk sources, not a claim that the working tree is clean.
- Method: bounded static source inspection. No agents, tests, builds, application/browser/editor actions, network requests, asset generation, auth reads, or game changes.
- Result: **No concrete reachable defect established in this bounded pass.** No hypothetical extreme-input finding is asserted.

## Acceptance checklist and evidence

All paths are relative to the checkout root.

- [x] Transitions and resume priority: `Assets/_Game/Scripts/Logic/Game/GameFlow.cs:105-110` prioritizes pending defeat, prologue, and unseen ending before location routing. `Assets/_Game/Scripts/Runtime/GameApp.cs:117-140` implements each route. Prologue completion clears its pending flag and sets town (`GameFlow.cs:114-120`); town entry resets carried TP/springs and saves (`GameFlow.cs:136-151`, `GameApp.cs:154-164`).
- [x] Reloading an unsettled encounter: `GameApp.cs:269-274` saves before starting the battle. `Assets/_Game/Scripts/Logic/Game/GameState.cs:167` stores the pending request; `Assets/_Game/Scripts/Logic/Game/SaveCodec.cs:55-59,83-87` serializes/deserializes state. `Assets/_Game/Scripts/Logic/Dungeon/DungeonRun.cs:20-23` persists seed while excluding derived setup. Resume rebuilds that setup from the saved request (`DungeonRun.cs:93-103,362`; `GameApp.cs:133-135`). This is encounter restart, not restoration of a mid-turn engine snapshot; no mid-turn resume contract was established.
- [x] Result commit and gameover: `DungeonRun.cs:367-369,403-408` caches the committed resolution, clears the pending request, and sets defeat pending. `Assets/_Game/Scripts/Runtime/Battle/BattleView.cs:1469-1472` resolves and saves before results presentation; its later callback (`BattleView.cs:1503-1506`, `GameApp.cs:327-331`) uses the cached resolution. Thus the apparent second ResolveBattle call is not a demonstrated duplicate-reward defect.
- [x] Defeat recovery: `GameFlow.cs:186-195` removes the defeat flag before charging the penalty, making repeat calls a no-op. `Assets/_Game/Scripts/Logic/Game/TownServices.cs:131-142` performs free whole-roster recovery and FOE respawn. `GameApp.cs:354-358` routes through town entry and its save. Loading a defeat save displays the defeat menu (`GameApp.cs:129-130`, `Assets/_Game/Scripts/UI/Screens/GameUI.cs:225-233`).
- [x] Ending progress: final-boss victory sets cleared and town location before the result save (`DungeonRun.cs:393-404`, `BattleView.cs:1471-1472`). Unseen endings resume through `GameFlow.cs:109`. Ending pages lead to credits before the completion callback (`GameUI.cs:219-223`); that callback marks the ending seen and enters/saves town (`GameApp.cs:411-415`, `GameFlow.cs:199-205`). Town's postgame notice is guarded by ending-seen and its own one-shot flag (`GameFlow.cs:148-149`).
- [x] Consulted available reports 01–06 for duplicates; no report 07 was present in the inspected report listing.
- [x] Only the assigned report written; no game fixes. Integration remains with the coordinator.

## Limits

Static evidence only: no runtime reproduction, test-pass claim, exhaustive correctness certification, or independent routing/tier verification. No actionable finding means none established within the inspected paths, not proof that all campaign states are defect-free.
