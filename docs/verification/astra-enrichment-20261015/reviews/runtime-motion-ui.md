# Runtime motion and UI — independent source review

2026-10-15. Checkout: `codex/astra-enrichment-20261015`. Requested model/effort: `gpt-6-astra` / `high` only; Fast/priority requested by the standing instruction. Actual model, effort and tier were not independently exposed by these tool results. No model/configuration changes or delegation.

**Verdict: scoped source approval. No concrete blocking finding established in the five reviewed diffs.** This does not approve compilation, frame-by-frame animation behavior or rendered UI. Parent owns runtime acceptance.

## Evidence reviewed

- `Assets/_Game/Scripts/Runtime/Art/ClipAnimator.cs:157–165`: the default rest-phase remapping reserves incoming fade plus seam-blend time in clip-time units. With clip length L, clip rate r, fade F and seam B, the phase is scaled by `clamp01(1 - (F+B)*r/L)`. For a take long enough to contain both fades, this leaves the intended reserve. Global speed scales both clip progression (`:183,206`) and blend progression (`:228`), so a positive slow speed does not invalidate that reserve. At speed zero neither clock advances; the new calculation does not divide by global speed. Explicit `PlayFrom` offsets and authored windows bypass the remapping. Existing lane weights, queued transitions and seam logic (`:170–188,231–247`) were inspected; the diff does not change their ownership or storage.
- `Assets/_Game/Scripts/Runtime/Battle/BattleView.cs:1303–1307,1318–1339`: reduced-motion enemy deaths retain the current pose with `DeathRate = 0` and immediate animator speed zero; root push/tilt and burst remain disabled. LateUpdate and hitstop restoration multiply by DeathRate (`:1655,1701`), so they do not restart a frozen death. Revive restores DeathRate to one before playback (`:432–440`). The rigless blob/crawler/flyer implementations also scale pose time and blend time by their speed; no battle caller found depends on the dead enemy's `CurrentClip` being `Die`.
- Death elapsed time, root staging and dissolve now pause together during hitstop. `HitStop` finishes through `Wait`, which is pause-aware but does not wait on `_hitstop` (`BattleView.cs:1688–1701`); therefore the added death wait does not introduce a cyclic dependency. The routine decrements `_dying` after completion, while `WaitDeaths` waits on that counter (`:1338–1344`). Supported preferences clamp battle speed to 1–2 (`Runtime/Persistence/GamePreferences.cs:55`); speed-zero animator freezing is distinct from a zero battle clock.
- `Assets/_Game/Scripts/UI/Battle/BattleHUD.Menu.cs:59–66,120,161–165`: skill cost/element are prepended before the first newline, which matches the actual `Focus` rendering path (`:413–416`). Captured skill values and target callbacks remain consistent. Both single-target and group/self confirmation paths receive the information. `BeginChoices` clears prior choices (`:296–304`), so attack/item menus do not retain the skill prefix. Target validity, knowledge-safe estimates, pointer arming, cancel and commit paths are unchanged.
- `Assets/_Game/Scripts/UI/Screens/GameUI.Party.cs:283–285,311–312`: EXP/gold contributions participate in the existing mixed/up/down verdict and use the existing percentage-point formatter (`:317–323`). Values come from effective/preview equipment stats. The gold label accurately describes the party cap implemented at `Logic/Game/PartyStats.cs:562–568`; it does not present the individual contribution as the final party payout.
- `Assets/_Game/Scripts/UI/Screens/GameUI.Settings.cs:35–42`: applying a setting refreshes the HUD from the applied preference, and a missing battle/HUD is a no-op. `BattleView.Initialize` adds the HUD to that same GameObject (`Runtime/Battle/BattleView.cs:173`); its label setter exists (`UI/Battle/BattleHUD.cs:233`). No change to the speed-cycle logic or menu refresh ordering was found.

## Verification boundary

Inspected both implementation notes and `fixes/battle-animation-regression.cs`. The supplied eight cases exercise real ClipAnimator **entry state**, including speed zero, explicit offsets and distinct phases; they do not advance the graph to prove a seam or freeze/resume over multiple frames. No slow-positive-speed timeline, death-coroutine or UI-runtime test result is claimed. The fixture remains a docs handoff artifact rather than an automatically discovered test.

Scoped `git diff --check` passed. **No compilation, tests, Unity, browser, source edits, installs or configuration changes were performed. Only this review report was written.**

Parent acceptance still needs: actual attack-to-idle seams at 1x/2x and a slow-positive animator speed; zero-speed hold/resume; later-hit hitstop while an earlier enemy dissolves; pause/resume and WaitDeaths completion; reduced-motion blob/crawler/flyer death and revive; target cost/element text fit and two-click/cancel behavior; speed-label settings/HUD agreement; and charm equip/unequip/mixed-bonus comparisons. Existing handoff recipes provide the detailed scenarios. Text ellipsis, authored clip durations and actual frame-order behavior were not visually verified.

## Reviewed source identity

Git blob hashes of working files after the reads matched the diff versions inspected:

| File (under `Assets/_Game/Scripts`) | Blob hash |
| --- | --- |
| `Runtime/Art/ClipAnimator.cs` | `3cbb61a94227f1cbb1c7e81bd7ae37dd34a9303a` |
| `Runtime/Battle/BattleView.cs` | `43d7f0562ec426a0bff2ee8822f542f4a909d9b6` |
| `UI/Battle/BattleHUD.Menu.cs` | `b31e2ef0c696eaf32c44bca0e715dc7d2b36025a` |
| `UI/Screens/GameUI.Party.cs` | `8cdae7226b0644f451953e1e535775cbae343147` |
| `UI/Screens/GameUI.Settings.cs` | `1b19424e1e20d35eaac3e5a9d2957a7e17aced37` |

Later changes to these files require a delta review; concurrent unrelated work was not assessed.
