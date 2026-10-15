# 27 — Battle animation bounded audit

- Requested model: `gpt-6-astra`; requested reasoning effort: `high`.
- Requested service tier: Fast/priority. Actual model, effort and service tier are not independently attested by the available execution results; no routing/configuration changes were made.
- Verified branch: `codex/astra-enrichment-20261015`; HEAD/base: `efdc1517f48ac8887e1fcf6843b6df44df6ebc3c`.
- Method: focused static inspection of current working-tree sources and relevant authored data. Existing modifications were preserved. Reports 01–06 were consulted for overlap; no report 07 was present in the initial focused listing.
- Result: **one reachable presentation finding**. Runtime reproduction was not performed.

## 1. [P2] Concurrent enemy death advances while its skeletal animation is frozen by the next hit

**Location:** `Assets/_Game/Scripts/Runtime/Battle/BattleView.cs:1318-1331`, specifically the pause-only guard at line 1318 and elapsed-time increment at line 1320.

**Repro conditions:** Reduced Motion off; two or more enemies; use the shipped all-enemy skill `jb_ab_soul_harvest` with the first target low enough to die and a later target taking damage. Repeat at the supported 1x and 2x battle speeds. This needs ordinary combat HP values, not malformed or extreme inputs.

**Reachability and source trace:**

- `Assets/_Game/Resources/Data/jobs.json:433` grants the skill; `skills.json:165-184` defines its all-enemy damage and `pr_soul_reap` presentation. `presentation.json:1491` sets its hit-stop to 0.07 battle seconds.
- `Assets/_Game/Scripts/Logic/Battle/BattleEngine.cs:1073-1099` resolves targets sequentially; `:1153-1158` emits damage, then `:1193` and `:1209` emit the first target's death before processing the next target.
- `BattleView.cs:1183-1190` does not group across a `UnitDownEvent`; `:1257-1260` completes the first hit-stop and advances directly into that death.
- `BattleView.cs:419` starts `DeathRoutine` concurrently. The next target's damage reaches another `HitStop` at `:1257` while the first enemy's 0.66-second death staging is still running (`:91`).
- `BattleView.cs:1694-1695` freezes **every** unit's animation, including the dying enemy. `:1652` maintains that freeze; `ClipAnimator.cs:184-196` propagates zero speed to its playables.
- Meanwhile `BattleView.cs:1318-1331` checks only pause, increments its separate clock, moves/rotates the dying model and advances dissolution. It never checks `_hitstop`.

**Impact:** The dying enemy's mesh pose freezes while its body transform and dissolution keep advancing. On resume, the death pose is behind the collapse/fade schedule by the overlapping hit-stop time; additional hits accumulate the discrepancy. The same disagreement remains at accelerated speed because both schedules use the battle-speed multiplier, but only the skeletal schedule is stopped. This affects visual timing, not combat HP or outcome correctness.

**Integration direction:** Make the death transform/dissolve clock and its animation follow the same hit-stop policy. No fix was applied. The repro above is proposed verification, not an executed runtime observation.

## Acceptance and remaining scope

- [x] Event-to-animation and damage timing reviewed: sequential replay (`BattleView.cs:229-247`), contact wait (`:786-803`), repeat-hit preparation (`:1158-1173`) and snapshot HP application (`:1202-1206`).
- [x] Accelerated mode reviewed: `Dt` scales with Speed (`:143-145`), waits use that clock (`:1685-1689`), and animation/VFX speeds are propagated (`:1652-1656`). No separate concrete acceleration defect established.
- [x] Dead-unit handling reviewed: down/revive (`:410-446`), return cancellation (`:1055-1060`), concurrent death completion (`:1339-1341`) and action-end death wait (`:326-328`). Report 02's BREAK-recovery issue is not duplicated.
- [x] At most two findings; only one supported finding reported with exact locations and ordinary repro conditions.
- [x] No tests, builds, editor/browser actions, network requests, nested agents, secret/history reads, source edits or configuration changes performed.
- [x] Only this assigned report was written. Static evidence does not constitute visual acceptance or a runtime pass.
