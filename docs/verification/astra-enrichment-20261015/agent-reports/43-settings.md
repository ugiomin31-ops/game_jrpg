# 43-settings — bounded read-only audit

- Repository: C:\Users\User\Desktop\GAME_JRPG\handoff-verify-20261015
- Observed branch/base: `codex/astra-enrichment-20261015`, `efdc1517`.
- Requested model: `gpt-6-astra`; requested reasoning: `high`; requested service tier: Fast/priority. Actual model/effort/tier are not independently exposed by the source-inspection tools used here; priority is a request, not a verified execution claim. No model or configuration changes were made.
- Scope: `GamePreferences.cs`, `GameUI.Settings.cs`, and direct persistence, pause-menu and battle/UI consumers. Static source inspection only; no tests, builds, Unity/editor/browser execution, network requests or nested agents. Existing unrelated working-tree changes were preserved.

## Finding 1 — P2: Pause-menu speed changes leave the battle speed button stale

**Location:** `Assets/_Game/Scripts/UI/Screens/GameUI.Settings.cs:25` and `:35`.

The settings action updates `Preferences.BattleSpeed`, applies/saves preferences, and refreshes only the settings menu. An existing battle reads that updated value dynamically (`Assets/_Game/Scripts/Runtime/Battle/BattleView.cs:144-145`), but its speed-button label is set only during battle initialization (`:177`) and when clicking the battle speed toggle itself (`:211-220`). The label is stored directly on the button (`Assets/_Game/Scripts/UI/Battle/BattleHUD.cs:225-233`); no other call to `SetSpeedLabel` exists in the battle runtime/UI sources.

**Reachable reproduction (source-derived, not executed):** Start a battle at 1x and wait for player command input. Open the pause menu, select Settings, and click Battle Speed once (1x → 1.5x). Close settings and resume. The battle runs at 1.5x while the HUD still says `속도 1x`. Clicking that stale HUD button then advances the actual value from 1.5x to 2x, so the visible label jumps from 1x to 2x. This pause/settings route is available during an idle battle (`Assets/_Game/Scripts/UI/Screens/GameUI.cs:19-21`, `:244-266`).

**Impact:** Players receive an incorrect live speed indication after a normal settings change, and the next visible speed transition appears to skip a choice. The value itself is applied and saved; the defect is synchronization of the existing battle control.

## Acceptance checklist

- [x] Confirmed requested branch and base.
- [x] Traced settings changes through `GameApp.ApplyPreferences` / `SavePreferences` (`GameApp.cs:70-80`) and preferences read/normalize/save (`GamePreferences.cs:32-85`).
- [x] Checked speed cycling and dynamic battle consumption, plus reduced-motion propagation to UI root (`GameUI.Settings.cs:35`) and battle camera/effect gates (`BattleView.cs:142`, `:1657-1676`). No additional concrete finding established in those inspected paths.
- [x] Searched available reports 01..07 for settings/speed/motion overlap; no matching settings finding found.
- [x] Reported one concrete reachable finding with exact source locations and reproduction; no runtime verification claimed.
- [x] Wrote only this assigned report. No game fixes; integration belongs to the main coordinator.
