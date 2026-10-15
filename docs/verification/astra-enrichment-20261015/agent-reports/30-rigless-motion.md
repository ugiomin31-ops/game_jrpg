# 30 — Rigless motion bounded audit

- Scope: `RiglessFlyerAnimator`, `RiglessCrawlerAnimator`, `RiglessBlobAnimator`; grounding, idle, hit and death motion, with direct spawn/battle callers.
- Repository: `C:\Users\User\Desktop\GAME_JRPG\handoff-verify-20261015`.
- Verified branch: `codex/astra-enrichment-20261015`; HEAD: `efdc1517f48ac8887e1fcf6843b6df44df6ebc3c`.
- Requested model/effort: `gpt-6-astra` / `high`. Requested service tier: Fast/priority. Actual model, reasoning effort and service tier were not independently exposed by the audit tools; requested values are not runtime verification. No configuration or model changes were made.
- Method: focused static source reads, reusing pre-interruption evidence. No nested agents, tests, builds, Unity/editor/browser actions, network requests, binary changes or source changes. Only this report was written.

## Finding 1 — P2: Reduced motion still plays the rigless death animation during the fade

**Primary location:** `Assets/_Game/Scripts/Runtime/Battle/BattleView.cs:1305`.

**Reachable reproduction (for the coordinator; not executed):** Enable Reduced Motion, enter an ordinary battle containing a `rhino_beetle`, `slime` or `bat`, and defeat it at normal battle speed. Inspect the visible model during the 0.25-second death dissolve. The model still tips, squashes or flinches while disappearing, although the death routine promises a fade-only reduced-motion path (`BattleView.cs:1285`).

**Source evidence:** The reduced branch disables root push/tilt (`BattleView.cs:1307-1308`) and starts dissolving immediately (`1293-1294`), but still calls `model.Play("Die", .02f)` (`1305`). The animation speed remains positive whenever the battle is unpaused (`1652`), including the death-rate multiplier set at `1302`. The rigless backends therefore continue applying their death keys:

- `Assets/_Game/Scripts/Runtime/Art/RiglessCrawlerAnimator.cs:63-69`: initial upward/backward jolt followed by a side roll; `163-187` advances the take and writes its transforms.
- `Assets/_Game/Scripts/Runtime/Art/RiglessBlobAnimator.cs:74-79`: recoil and flattening; `190-221` advances the take and applies scale/rotation/position.
- `Assets/_Game/Scripts/Runtime/Art/RiglessFlyerAnimator.cs:157-162`: upward/backward jolt followed by a drop and wing/body rotation; `269-304` advances and applies it.

These early keys occur before the reduced fade finishes; this does not depend on extreme inputs or unusual frame times. The explicit model selection is in `ArtLibrary.cs:117-122,255-274`, and `CharacterModel.cs:71-98` instantiates these backends.

**Impact:** The accessibility preference suppresses the outer death staging but leaves the procedural creature motion active. The coordinator should make the reduced death path hold a stable visual pose while fading and ensure the per-frame speed assignment cannot restart that motion.

## Acceptance and limits

- [x] All three assigned animation sources and their direct spawn/death callers inspected.
- [x] One concrete reachable finding with exact source locations and reproduction steps.
- [x] Requested model/effort and requested-versus-verified service tier distinguished.
- [x] Only the assigned report written; no game fixes or execution-based validation performed.
- No second finding is asserted. Ground-contact accuracy against actual mesh geometry was not established by these source reads; no visual or runtime pass is claimed.
