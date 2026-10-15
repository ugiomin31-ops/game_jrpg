# Audit 12 — WebGL save durability assessment

## Decision

**Confirmed source-level WebGL completion/error-propagation defect; separate WebGL release gate, not a blocker attributable to the native Windows save path.** Do not expand a Windows-only acceptance run into an unvalidated persistence rewrite. If the coordinator includes WebGL in the deliverable, fix and verify this path before claiming browser saves survive a reload after the success notification.

Checkout inspected: `C:\Users\User\Desktop\GAME_JRPG\handoff-verify-20261015`, branch `codex/astra-enrichment-20261015`, HEAD `efdc1517`. Requested model/effort: `gpt-6-astra` / `high`; actual served routing/effort/tier is not independently exposed. No nested agents or configuration changes. This assessment is the only file written in this audit; no tests, builds, Unity/browser actions, external documentation, network calls or save-data access occurred.

## Current target support and build evidence

| Local primary evidence | What it establishes |
|---|---|
| `Assets/_Game/Scripts/Editor/AbyssProjectSetup.cs:125-138` | An explicit Windows build entry produces `Build/Windows/AbyssLabyrinth.exe` using `BuildTarget.StandaloneWindows64`. |
| Same file `:196-221` | WebGL is intentionally supported in source. `BuildWebPlayer` checks installed platform support, switches target, and builds `Build/Web` through the menu entry. The existence of this check does not establish that the module is currently installed. |
| Same file `:228-250` | CLI build entry accepts Android and WebGL. Its fallback WebGL output is `build/WebGL/Web`. |
| `.github/workflows/phone-build.yml:14-20,40-46,119-135` | The phone workflow includes Android/WebGL and WebGL publication. The current `codex/astra-enrichment-20261015` branch is absent from its automatic push-branch list; manual dispatch exists. This is configuration evidence, not evidence of a successful run or current deployment. |
| `ProjectSettings/ProjectVersion.txt:1` | Project editor version is `6000.3.25f1`. |
| Exact local artifact checks | `Build/Windows/AbyssLabyrinth.exe`, `Build/Web/index.html` and `build/WebGL/Web/index.html` are all absent in this checkout. No installed player or historical build elsewhere was inferred from that result. |

The editor's live active target, installed WebGL module and any current published site's revision remain unverified under this read-only/no-Unity/no-network scope. A native Windows run can proceed with its own save regression evidence; it cannot close the WebGL item.

## Precise reachable failure and impact

1. Manual slot selection calls `app.Save(slot)` and immediately refreshes the menu (`Assets/_Game/Scripts/UI/Screens/GameUI.cs:209-210`). `GameApp.Save` writes and immediately emits `저장했습니다.` for manual slots; its catch handles only synchronous IO/access exceptions (`Assets/_Game/Scripts/Runtime/GameApp.cs:143-147`).
2. `SaveRepository.AtomicWrite` selects its browser branch only under `UNITY_WEBGL && !UNITY_EDITOR`: it writes the in-memory file and calls `WebStorage.Flush()` (`Assets/_Game/Scripts/Runtime/Persistence/SaveRepository.cs:35-38`). The bridge returns `void` and provides no completion channel (`WebStorage.cs:11-15`).
3. `Assets/_Game/Plugins/WebGL/AbyssWebStorage.jslib:3-4` starts `FS.syncfs(false, callback)`. A later callback error only reaches `console.warn`. If `FS`/`FS.syncfs` is unavailable, the guard silently does nothing. Neither case can inform the existing save-success branch.
4. The native/editor branch instead writes a temporary file with `WriteThrough`, calls `Flush(true)`, then replaces/moves it before returning (`SaveRepository.cs:40-47`). This asynchronous IndexedDB gap does not execute in that branch. This is not a blanket claim about all native storage/power-loss scenarios.

**Concrete reproduction to execute later:** in a WebGL player, delay the sync callback after a manual save. The success toast and menu refresh occur while persistence is still pending. Then complete with a storage error: the current bridge only warns, so the toast remains a false confirmation. Closing/reloading before a successful sync, or after a failed sync, can expose missing or older progress. Failure means persistence is unconfirmed; it does not prove every byte was rolled back or that the newest data is always absent. A later whole-filesystem sync can also persist earlier in-memory changes.

The impact extends to existing callers without introducing a second root cause:

- **Autosave:** town arrival and dungeon transitions (`GameApp.cs:162,210,239`), rescue/event handling (`:254-255,271,288`), and battle resolution (`Runtime/Battle/BattleView.cs:1472-1475`) use the same `Save()` path. They have no manual success toast, but async failures remain invisible to game code. Reopening can restore an older reward/event/battle state. This is a rollback risk, not proof of a particular duplication exploit.
- **Preferences:** `GamePreferences.Save` calls the same `AtomicWrite` for `preferences.json` (`Runtime/Persistence/GamePreferences.cs:81-85`), while `GameApp.SavePreferences` catches only synchronous exceptions (`GameApp.cs:77-80`). Battle auto/speed controls call it at `BattleView.cs:203,219`. Those settings share the sync failure and overlap risk.
- **In-session checks are insufficient:** `Exists`, `SlotTime`, `Read` and `Summary` examine the current filesystem (`SaveRepository.cs:23-26`); seeing new slot contents before a successful callback is not proof of IndexedDB persistence.
- **Lifecycle calls do not fix the gap:** `GameApp.cs:383-400` attempts saves at quit/pause but has no completion barrier. `WebStorage.cs:6-7` overstates closing immediately after saving. A future fix must not promise completion after the page is already closing.

## Surgical design if WebGL remediation is approved

Prefer a small completion-callback contract. No save-format migration, backup subsystem, build-target switch, broad `async` conversion or gameplay-state rewrite is required.

| Production file | Bounded change |
|---|---|
| `Assets/_Game/Plugins/WebGL/AbyssWebStorage.jslib` | Accept a request ID and stable Unity callback target; return exactly one success/error result from `FS.syncfs`. Explicitly report missing FS and synchronous bridge exceptions. Do not treat starting sync as success. |
| `Assets/_Game/Scripts/Runtime/Persistence/WebStorage.cs` | Own one in-flight WebGL write/sync request and a FIFO; correlate responses and ignore duplicate/stale IDs. Add a small preserved Unity callback receiver outside disposable UI/world objects, plus pending/completion state. Deliver callbacks on the Unity thread. |
| `Assets/_Game/Scripts/Runtime/Persistence/SaveRepository.cs` | Add completion to `Write`/`AtomicWrite`. Serialize state into immutable bytes at the call site, before waiting in the queue. For WebGL, queue the **file write plus sync**, not just the sync call. Keep the native temp/write-through/replace sequence and invoke completion only after it returns. |
| `Assets/_Game/Scripts/Runtime/Persistence/GamePreferences.cs` | Pass its already serialized bytes and completion through the same queue so preferences cannot bypass ordering. |
| `Assets/_Game/Scripts/Runtime/GameApp.cs` | Success toast only on confirmed manual-save completion; async failure notification for manual/autosave/preferences. Expose a pending state. Preserve synchronous native error handling and existing parameterless autosave call sites. |
| `Assets/_Game/Scripts/UI/Screens/GameUI.cs` | Refresh the manual slot on completion and show/disable the saving action while pending; guard against a menu destroyed before completion. Refreshing RAM contents must not imply persistent success. No layout redesign. |

The callback payload should carry a request ID and a small status/error code. The receiver should survive `ResetWorld` (`GameApp.cs:83-91` destroys world/UI content), and be preserved against WebGL stripping. Verify the selected JS→Unity callback mechanism in the actual build; a mocked JS call alone is not interop acceptance.

Ordering is material: if request B writes the same slot while A is still syncing, A's completion cannot reliably be associated with A's captured snapshot. Queue the immutable path/bytes **and** the subsequent flush as one unit across campaign and preferences. Do not use `.Wait()`, `.Result`, sleeps or a busy loop on the WebGL main thread. A timeout, if added, means unconfirmed/error, never success. Completion bookkeeping must run even if a UI callback is no longer usable.

**Keep scope explicit:** the six-file change fixes truthful persistence acknowledgement, async error visibility and ordered requests. It does not by itself wait for persistence before every battle/story presentation. If the acceptance contract requires the battle comment's “save before ceremony” to mean *confirmed persistence*, add one deliberate coroutine barrier at `BattleView.cs:1474-1475`: resolve the battle once, snapshot/save once, await completion, and handle failure/retry without calling `ResolveBattle` again. Rescue/story callers would need equally explicit decisions. Do not silently add those gameplay timing changes to a Windows-only patch.

Confirmed `syncfs` completion is the application's browser-storage acknowledgement, not a guarantee against later user deletion, browser eviction or arbitrary process/storage failure. A pending-state UI makes that boundary truthful; an unload handler cannot manufacture completion after closure.

## Testability and acceptance gates (proposal only; nothing executed)

Current `Tools/logic_test.py:1-2,39-49,60-62` compiles only `Scripts/Logic/**/*.cs` and `Tools/LogicTests/**/*.cs`. It does **not** compile Runtime persistence or the JS bridge. `.github/workflows/logic-check.yml:4` also filters changes to logic/data/tests/harness paths. Existing logic-test success cannot validate this fix.

| Layer | Focused evidence required |
|---|---|
| JS bridge, headless controlled harness | Capture `mergeInto` registration; fake `FS.syncfs` with a held callback. Assert no premature completion; exactly one response for delayed success/failure, missing FS, synchronous throw and duplicate callback. No real user browser storage needed for this unit check. |
| C# request coordination | A tiny injectable sync transport or isolated non-Unity queue helper allows deterministic delayed completions. Queue A/B to the same slot and a preferences write: bytes must be captured at request time, write/sync order serial, no success before that request's callback, and failures/duplicates must not mis-complete another request. Exercise a callback whose menu has closed. |
| Native regression | Temporary-directory first save, replacement, readback, and injected synchronous failure. Confirm the existing atomic path and immediate post-write completion remain intact. Link the needed production persistence/helper files explicitly into a focused harness; do not pretend the current logic harness includes them. |
| Actual WebGL gate | Build the exact reviewed revision, verify JS callback linkage and pending/error UI, delay/fail sync deliberately, and confirm no early success. After an acknowledged successful manual save, reopen a fresh player instance at the same origin and verify progress. Repeat with autosave and preferences. Same-session `Read` is not this gate. |
| Close while pending | Confirm no completed-save claim before callback. Reopen and report actual persisted state; do not require an impossible guarantee that an already-closed page finishes its pending work. |

A minimal test follow-up therefore needs production coordination coverage plus a small JS harness, and CI path/include wiring for those specific files. Keep that separate from the existing pure game-logic suite; only broaden after focused checks pass. Real WebGL execution is still required to close the platform gate, and was explicitly excluded from this assessment.

The old `Tools/Pr6NativeSaveSandbox.ps1:3-6` embeds the live LocalLow store and a different historical checkout. It was read but not executed; do not reuse it blindly for this handoff. Future native tests should use an explicitly isolated temporary directory and preserve the user's existing saves.

## Coordinator disposition

- **Native Windows acceptance now:** record audit 12 as WebGL-specific; continue the native gate without changing persistence for this finding.
- **WebGL deliverable:** retain an open platform gate, implement the six-file acknowledgement/ordering fix with focused tests, then obtain actual WebGL reopen evidence. WebGL is maintained by local source/CI, so do not dismiss the item as unsupported merely because no current artifact exists here.
- **Assessment complete:** branch/base, target code/CI, bridge, manual/autosave/preferences/lifecycle callers and test coverage inspected. Only this report was written. No runtime reproduction or build success is claimed.
