# battle-logic — independent review

**Verdict: scoped source approval; no actionable regression found in the reviewed diff.** This reviewer did not author these changes. The approval rests on the paths below, not solely on the reported test totals.

- Requested model/effort: `gpt-6-astra` / `high`. Actual routing/effort and Fast/priority tier are not independently exposed by the inspection tools. No model/configuration changes or nested agents.
- Scope: current HEAD-relative changes in `BattleStatus.cs`, `BattleUnit.cs`, `BattleEngine.cs`; full source of `BattleStatusPresentationRepairTests.cs` and the parent's `BreakRecoveryTests.cs`; directly connected event, damage-formula, cleanse/AI and replay consumers.
- Parent/user reports **18/18 focused and 279/279 full PASS**. These are supplied execution results, not independently rerun or independently matched to the hashes below. No tests, compilation or Unity/browser actions were performed for this review.

## Event snapshot, retargeting and RNG

- `Assets/_Game/Scripts/Logic/Battle/BattleEngine.cs:258-271,982-1013`: `Emit` only assigns `Seq` and appends to the private batch. It invokes no subscriber/reentrant resolver. Returning the same start-event object therefore permits its target snapshot to be finalized before `EndBatch` returns, without moving the event or changing sequence allocation.
- `BattleEngine.cs:1068-1112`: random target IDs are appended **after** the existing dead-target replacement and living-target guard, but **before** `RollDamage`. Consequently misses and fully absorbed attempts remain represented, repeated targets remain repeated, and picks with no living replacement are omitted. The independent list is assigned before drain/status/self-status processing and is not reused by later batches or aliased to `action.TargetIds`.
- The existing replacement draw, original damage roll and payload-status order are unchanged. The diff adds no random draw or extra formula call. `DamageFormula.cs:35-59` still draws variance, hit chance and (for landed physical damage) critical chance in the existing order.
- `Execute` passes the emitted event through every updated damage call (`BattleEngine.cs:857-907,1038-1053`). Nonrandom actions retain their original copied targets; non-damage payloads and charge announcements retain existing behavior. Authored `HitCount` is not rewritten to the number of surviving targets.
- `BattleStatusPresentationRepairTests.cs:160-224` meaningfully compares actual retarget sequence/damage against an independent paired RNG stream, checks the next RNG value, sequence continuity, action-list mutation and later-batch isolation, and exercises public `Submit` when the hit budget outlives all opponents.

## Misses and counter/reaction boundaries

- A miss is collected by the same pre-roll append as a hit, then emits the existing `MissEvent` (`BattleEngine.cs:1088-1097`). No success-only filtering was introduced.
- The new retarget fixtures use accurate magical attacks and do **not** explicitly assert a mixed miss/hit target sequence. Miss correctness here is source-reviewed, not independently covered by a newly executed/dedicated test. This is a coverage limit, not a demonstrated defect.
- `BattleEngine.cs:1153-1202` resolves damage, shield/break/death and phases without a nested counterattack or reflection `Execute` call. No such reaction producer exists in the inspected battle logic; comments in the presentation layer mentioning counters are not evidence of an implemented counter mechanic.
- The replay layer distinguishes ordinary action strikes from other damage using source ID and `StatusId`, rather than trusting membership in the start-target list (`Assets/_Game/Scripts/Runtime/Battle/BattleView.cs:1195-1202`). Misses likewise check source identity (`:331-345`); wave lookahead checks damage/miss events (`:1140-1190`). The snapshot change does not turn another source's damage into a strike or add reaction damage to the target snapshot. No runtime counter/reaction verification is claimed.

## Beneficial status classification

- `Assets/_Game/Scripts/Logic/Battle/BattleStatus.cs:134-140` agrees with existing `BattleUnit.ProvokedBy`/`IsTaunting` semantics (`BattleUnit.cs:298-314`): external-source Provoke is harmful; self/empty-source Provoke is a beneficial taunt. `FromDef` already normalizes null source to empty.
- `BattleUnit.cs:424-434` binds to the holder before both append and refresh. `BattleStatus.RefreshFrom` copies source and `_beneficial` while preserving the longer duration and existing barrier-pool behavior. Applied events read the resulting attached instance (`BattleEngine.cs:1384-1402`); snapshots copy the beneficial flag, so old snapshots/events do not change after refresh.
- General cleanse reads attached `IsBeneficial` (`BattleEngine.cs:1292-1311`); item-specific status removal still follows its explicit status key. Attached-status AI cleanse decisions also consume the updated classification. Immunity checks use status identity/type rather than the beneficial flag, so the earlier immunity check is not invalidated by deferred holder binding.
- `FromDef` remains holder-independent until binding. The existing unbound offensive-status scoring probe (`BattleEngine.Commands.cs:783-785`) still has its pre-existing type-based view; no new RNG/application/cleanse regression follows from this change, and the shipped Provoke payloads remain self-taunts.
- The four status-focused tests cover skill/item cleanse, accompanying poison removal, self/empty/null source, refresh both directions, old snapshot independence, longer duration retention and unchanged ratio-barrier binding. They use actual application/cleanse paths rather than asserting the new assignment in isolation.

## Parent Break recovery change

- `BattleEngine.cs:504-522`: the added alive guard is evaluated after turn-end effects. A lethal DOT therefore cannot refill the dead unit's shield or emit recovery events; surviving broken units retain normal recovery and the final turn snapshot is emitted in both cases.
- `Tools/LogicTests/BreakRecoveryTests.cs:43-65` covers the reported lethal poison case (death/shield/snapshot/one victory) and the survival control. Revival already resets `Broken` in `BattleEngine.cs:1276-1287`; the changed guard does not introduce persistent broken state after revival.

## Reviewed SHA-256 snapshot

```text
Assets/_Game/Scripts/Logic/Battle/BattleStatus.cs 97897f04950eae509deff72c0e9130b4989d51fc7e835139bfd536ae5b6c5175
Assets/_Game/Scripts/Logic/Battle/BattleUnit.cs 7df9ca95f0ee144e47b3709c2bd578da1898d6ae1d0a4bed73f88225332db0d9
Assets/_Game/Scripts/Logic/Battle/BattleEngine.cs 2495cb067cd2684a4a6f1b36c43bc5b9715d0c00d5a90b202890b14366795525
Tools/LogicTests/BattleStatusPresentationRepairTests.cs 9635ec9f27942b9604b6beb20ec037774d8c352bf65610a57a327e678160b937
Tools/LogicTests/BreakRecoveryTests.cs 85b88587f5a0f44fb322b69665a4d7bfa9f4855082dcc5603add9b76fa11df48
```

Only this review report was written. No source or test changes. Presentation rendering and final integration remain parent-owned.
