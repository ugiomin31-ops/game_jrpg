# 28 — ClipAnimator bounded source audit

- Requested model: `gpt-6-astra`; requested reasoning effort: `high`; requested service tier: Fast/priority.
- Independently verified runtime model, effort and service tier: unavailable in this audit interface. Requested settings are not execution evidence; no configuration/model/persona changes were made.
- Verified branch: `codex/astra-enrichment-20261015`; HEAD: `efdc1517` (matches the expected base).
- Scope: ClipAnimator and directly related character initialization, animation settings, battle/town call sites, and warrior BattleIdle import metadata. Reports 01–06 were searched for animation overlap; report 07 was not present in the inspected listing.
- Method: static source inspection only. No agents, tests, builds, editor/browser actions, network requests, asset generation, secret reads or game changes.

## Finding 1 — P2: Random rest-loop entry can bypass the seam blend and repeat a visible wrap after actions

**Location:** `Assets/_Game/Scripts/Runtime/Art/ClipAnimator.cs:232–237` (seam processing requires `_fade >= 1f`), together with `:157` and `:173` (rest entry starts at the persistent random phase).

**Reachable path:** Battle initialization selects BattleIdle as RestClip (`Assets/_Game/Scripts/Runtime/Battle/BattleView.cs:555`). Normal attacks queue Idle (`BattleView.cs:880–886`), which resolves to BattleIdle and returns with a 0.22-second fade (`ClipAnimator.cs:226–230`, `:29`). The warrior loop explicitly requires a 0.3-second seam blend (`Assets/_Game/Scripts/Runtime/Art/ArtLibrary.cs:228–231`); its imported take has looping enabled (`Assets/_Game/Resources/Art/HumanoidAnimationsByClass/warrior/BattleIdle.fbx.meta:35–46`). CharacterModel installs that setting at `Assets/_Game/Scripts/Runtime/Art/CharacterModel.cs:313–318`.

**Source-level reproduction:** Use a warrior with its naturally assigned rest phase near the end of BattleIdle, perform an ordinary attack, and let its queued Idle return run. For example, a phase leaving 0.15 seconds before the wrap crosses the end during the 0.22-second incoming fade. The seam branch is skipped while that fade is incomplete, so the incoming loop wraps with roughly 68% weight instead of fading its outgoing end pose to zero. Once the incoming fade finishes, modulo time is already near the beginning and the seam check cannot repair the missed wrap. The phase is fixed for that unit, so subsequent action-to-idle returns can repeat this behavior. Even an entry leaving slightly more than 0.22 seconds starts the full 0.3-second seam blend too late to finish before the wrap.

**Impact:** The intentionally corrected first/last-pose discontinuity can still produce an idle snap after normal battle actions for units with late rest phases. This requires neither extreme input nor frame stalls. The code itself documents the warrior end/start mismatch at `ClipAnimator.cs:75–76`. The missed seam follows from the control flow; its rendered severity was not observed because runtime actions were prohibited.

## Acceptance checklist

- [x] Branch/base checked without switching or modifying them.
- [x] Selection, lane blending, loop handling, duration/window/rate logic and root-motion setting inspected.
- [x] At most two concrete reachable findings: one reported.
- [x] No additional source-supported scale/root-motion defect established in this bounded inspection; this is not visual certification.
- [x] Only this assigned report written; no fixes or prohibited verification performed.
