# battle-animation — implementation handoff

Authorized plan: `plan/2026-10-15-astra-enrichment.md`; reviewed reports 27, 28 and 30 plus `design.md`. Requested model/effort: `gpt-6-astra` / `high`; Fast/priority requested, not independently verified. No model/configuration changes or nested agents.

## Changes

- `Assets/_Game/Scripts/Runtime/Art/ClipAnimator.cs`, `Begin`: remap only default rest-loop phases with configured seam blending into the interval that leaves both the incoming fade and the seam fade before the first wrap. Uses the actual clip length and clip rate; global battle speed cancels from this interval. Keeps distinct per-unit phases, explicit `PlayFrom` offsets, authored windows, interrupted lane blending, attack timings and root-motion guards.
- `Assets/_Game/Scripts/Runtime/Battle/BattleView.cs`, `DeathRoutine`: stop elapsed time, root staging, burst and dissolve during `_hitstop`, matching skeletal playback; also defer final completion while hitstop is active. Existing pause and battle-speed semantics remain.
- In the same routine, Reduced Motion sets `DeathRate = 0` and immediately freezes the current pose without playing `Die`. Existing LateUpdate and HitStop restoration multiply by DeathRate, so neither restarts the motion. Existing ReviveEvent resets DeathRate to 1. Normal deaths retain their clip windows, rates, fall/held distinction, roots and timing constants.
- No edits to `BattleView.Moves.cs`, `BattleEngine`, design, plan, assets, configuration or other workers' files. Both owned production files had no pre-existing working-tree diff at the initial scoped status check; edits used focused patches.

## Regression source and verification status

Added `docs/verification/astra-enrichment-20261015/fixes/battle-animation-regression.cs`: real Unity EditMode NUnit fixture `BattleAnimationEntryRegressionTests` (eight cases). It exercises the actual ClipAnimator graph entry state with late phase 0.9, 1x/2x/paused global speed, an independent 1.6x clip rate, zero incoming fade, explicit start preservation, uncorrected-loop phase preservation, and distinct unit phases. The reserve assertions fail against the previous entry implementation. This is test source, not an executed result.

The fixture is a handoff artifact under docs, **not auto-discovered**. Parent must compile/include it in its Unity Editor test assembly referencing the game's runtime and NUnit/UnityEditor; no test assembly or configuration was created in this slice. The existing `Tools/logic_test.py` compiles only engine-free Logic sources and cannot verify these runtime files. No Unity stubs, copied implementation or substitute fake harness were introduced. Death behavior needs actual coroutine/animation verification below; no automated coverage is claimed for it.

Performed only scoped diff review and `git diff --check`; no whitespace errors reported. **No tests, compilation, Unity/editor/browser execution or installs were run.** Parent owns source recompilation, test integration/execution, independent review and runtime acceptance.

## Bounded runtime recipe (parent; not executed)

1. Compile the changed runtime sources and the supplied fixture serially; run `BattleAnimationEntryRegressionTests` in the real Unity EditMode test assembly. Expect eight cases passing. Do not pass the fixture to the engine-free logic runner.
2. In a battle with warrior BattleIdle (or Jiho/Minjun/Yuna with configured seam blending), inspect attack-to-idle returns for three ordinary attacks at 1x and 2x. Include a unit with a late assigned phase (the fixture sets 0.9 deterministically). Verify the incoming blend finishes before the seam blend; the loop crosses its end with the outgoing lane at near-zero weight, retaining unit phase variety. Check pause/resume and no root-position jump.
3. Reduced Motion off: use `jb_ab_soul_harvest` against at least two enemies, first target low enough to die and a later target taking damage. At 1x and 2x, inspect the first enemy during the later target's hitstop: pose, root staging and dissolve must all stop, then resume together. Pause/resume once during a death and ensure WaitDeaths completes. Check one boss death too; original collapse/dissolve constants must remain in effect.
4. Reduced Motion on: defeat a slime, rhino_beetle and bat; each must hold its visible pose during the existing 0.25-battle-second fade with no death jolt/squash/roll. Pause/resume during the fade. If an enemy revive is available, verify its opacity/root restore and idle playback resumes after DeathRate resets; also check an ordinary hero down/revive control (its flow was not changed).
5. Inspect actual console/player log for animation/graph exceptions and record short video or consecutive frames for steps 2–4. These runtime checks, including exact mesh appearance and frame-order behavior, remain unverified here.

## Slice checklist

- [x] Three requested issues repaired within the two owned production files.
- [x] Existing attack/death flow, root guards and timing constants preserved by source review.
- [x] Focused real-Unity regression source and bounded runtime recipe supplied.
- [x] No reset/revert/commit, tests, builds, installs, nested agents or unrelated edits.
- [ ] Parent compilation, fixture integration/execution, independent review and rendered acceptance pending.
