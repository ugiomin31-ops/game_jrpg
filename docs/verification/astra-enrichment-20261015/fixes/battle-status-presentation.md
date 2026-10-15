# Battle status and presentation repair — 2026-10-15

Requested model/effort: `gpt-6-astra` / `high`; requested service: Fast/priority where supported. Actual routing/effort/tier are not independently exposed by this session. No model, service, or configuration was changed; no nested agents were used.

The user explicitly authorized implementation and superseded plan/approval gates. Writable scope is the three battle source files, the new focused test file, and this note. The parent owns integration and serialized compiler/test execution.

## Changes

- `Assets/_Game/Scripts/Logic/Battle/BattleStatus.cs:133-140`: holder binding now classifies Provoke as beneficial only for an empty source or a source equal to the holder ID. The optional holder-ID parameter preserves the existing max-HP-only probe in `Tools/LogicTests/BattleDecisionMechanicsTests.cs:897`. Barrier calculation is unchanged. `FromDef` remains holder-independent until application; a max-HP-only probe does not infer a missing holder identity.
- `Assets/_Game/Scripts/Logic/Battle/BattleUnit.cs:424`: application supplies `Id` to binding before both append and same-ID refresh. Existing `RefreshFrom` already copies the bound classification and source, so its duration/pool logic needs no change.
- `Assets/_Game/Scripts/Logic/Battle/BattleEngine.cs:857,982,1038,1068-1112`: `EmitActionStart` returns the event it has already appended. `Execute` passes that event through payload resolution into damage resolution. Random damage collects each living target actually attempted, after dead-target retargeting and before the hit/miss roll. Before the batch is returned, that independent list replaces the start event's provisional snapshot. Repeated targets and misses remain represented; picks with no living replacement are omitted. The authored `HitCount` is unchanged.
- Report 10's defect was confirmed against the working source: initial copied target IDs remained stale when `ResolveDamage` changed `action.TargetIds[pick]`. This repair leaves target selection, damage rolls, status payloads, event append locations, and sequence allocation in place. It adds no RNG calls and does not alias `action.TargetIds` or any reusable engine list. Nonrandom and non-damage snapshots keep their existing behavior.
- `Tools/LogicTests/BattleStatusPresentationRepairTests.cs`: six new `[LogicTest]` methods cover general Cleanse skill and remedy removal of external Provoke while preserving buffs; self/empty/null-source taunt preservation with real poison removal; refresh in both directions plus empty source, duration retention, applied-event/snapshot classification and prior-snapshot independence; legacy binding and Barrier pool preservation; lethal random retargeting with actual target/damage comparison, independent RNG replay, event order/sequence, action-list mutation and later-batch isolation; and public `Submit` with all opponents defeated before the authored random hit budget is exhausted.

The random-retarget test deliberately feeds a legal prepared allocation containing six repeats of the first target into the private action/batch boundary (the existing test suite uses reflection for such boundaries). Three ordinary opponents make retargeting consume real selection RNG after the first opponent falls. A separate test exercises the public `Submit` boundary. Tests are automatically discovered by the existing harness; no registration or runner file was modified.

## Preserved existing work and limits

- At entry, the sole existing diff in these three source files was the parent's Break recovery guard: `if (recoverBreak && actor.Broken && actor.IsAlive)` at `BattleEngine.cs:512`. It remains exactly unchanged. The HEAD-relative diff includes this pre-existing change; it is not part of this worker's repair.
- Current Provoke content still uses self-taunts. This repair corrects the supported external-source engine path without adding new skill/content behavior.
- No other source files, tests, assets, settings, binaries or configuration were edited. No commits, nested agents, network/relay requests, browser or Unity actions were performed.
- **No tests, compiler, build or game run was executed.** Static call-site review confirms that updated private signatures are passed consistently and that the pre-existing one-argument binding probe remains source-compatible. The edited tracked-source `git diff --check` completed without findings. This is not a compilation or runtime pass.

## Parent verification handoff

Run the focused class first when the parent acquires the serialized execution slot:

```text
python Tools/logic_test.py BattleStatusPresentationRepairTests
```

Then include the existing `EnemyIntentTests` (especially frozen Provoke intent and exact RNG ordering) and `BattleDecisionMechanicsTests` in the parent's regression gate. Public batch replay/rendering remains unverified here. If the targeted class fails, reproduce its failing method before any broad-suite rerun.

## Acceptance

- [x] Holder-aware Provoke classification applied before append/refresh; self/empty taunts preserved.
- [x] Random damage start-event snapshot describes attempted resolved targets and owns its list.
- [x] Existing event order/RNG call sites and parent's living-actor Break guard preserved by source review.
- [x] Six focused regression tests added in the assigned new file.
- [x] Only authorized files written; execution explicitly deferred to the parent.
