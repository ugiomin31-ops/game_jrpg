# 12 — SaveRepository bounded audit

- Requested model: `gpt-6-astra`; requested reasoning effort: `high`.
- Requested service mode: Fast/priority. Actual model routing, effort, and priority/service tier were not independently verifiable from this audit's available evidence. No model/persona/configuration changes were made.
- Verified branch: `codex/astra-enrichment-20261015`.
- Verified HEAD/base: `efdc1517f48ac8887e1fcf6843b6df44df6ebc3c` (requested base `efdc1517`).
- Method: focused static reads only. No agents, tests, builds, editor/browser actions, network requests, secret reads, or game changes. This report is the only file written.
- Duplicate check: focused keyword search of existing reports 01–06 found no overlapping persistence finding; report 07 was not present in the targeted listing.

## Finding 1 — [P2] WebGL reports save success before durable storage succeeds

**Location:** `Assets/_Game/Scripts/Runtime/Persistence/SaveRepository.cs:37-38`.

**Reachable path:** A manual save calls `GameApp.Save` → `Saves.Write` → WebGL `AtomicWrite`. The repository writes the in-memory filesystem and calls `WebStorage.Flush()`. That wrapper returns void (`Assets/_Game/Scripts/Runtime/Persistence/WebStorage.cs:12-13`). The JS bridge starts asynchronous `FS.syncfs(false, callback)` and only logs callback failures (`Assets/_Game/Plugins/WebGL/AbyssWebStorage.jslib:4`). `GameApp.Save` consequently displays “저장했습니다.” immediately (`Assets/_Game/Scripts/Runtime/GameApp.cs:146`); its synchronous exception handler cannot receive a later sync failure.

**Repro scenario (not executed):** In a WebGL build, save to a manual slot when browser persistent storage rejects the IndexedDB write, such as when its storage quota is exhausted. The success notification still appears; the callback only emits `Abyss save sync failed`. Reloading loses that newly saved progress or restores an older persistent copy. Closing the tab immediately after the success notification also has no completion guarantee while the sync remains pending.

**Impact:** Players are told their progress is saved even when persistence fails. In-session reads and slot refreshes inspect the in-memory copy, so they do not establish durability. Propagate sync completion/failure to the save UI and reserve the success notification for confirmed persistence. This finding applies specifically to WebGL; no desktop failure is claimed.

## Remaining scope and acceptance checklist

- [x] Desktop atomic path inspected: temp file, exclusive writer, write-through plus `Flush(true)`, then `File.Replace`/`File.Move` (`SaveRepository.cs:40-47`). No additional concrete reachable defect established within this bounded review.
- [x] Backup load inspected: `Read` accesses only the primary file (`:25`), and replacement passes a null backup path (`:46`). Backup generation/recovery is absent. This is recorded as current behavior, not a separate defect without an established backup requirement or production corruption path.
- [x] Slot validation inspected: `PathFor` accepts only `-1..2` (`:18-21`); current load/save menu loops stay in that range (`Assets/_Game/Scripts/UI/Screens/GameUI.cs:136,176-178`). No reachable invalid-slot finding established.
- [x] Runtime errors traced: load handles IO/access/format failures (`GameApp.cs:119-121`); save handles synchronous IO/access failures (`:146-147`); slot summaries handle read/format errors (`GameUI.cs:185-197`). The asynchronous WebGL error gap is the finding above.
- [x] At most two findings: one reported, supported by source paths and lines; no runtime reproduction claimed.
- [x] No fixes applied. Integration and any later validation remain with the main coordinator.