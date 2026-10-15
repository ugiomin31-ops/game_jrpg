# equipment-progression

- Authorized plan: `plan/2026-10-15-astra-enrichment.md`; reports 19 finding 1 and 20. Requested model/effort: `gpt-6-astra` / `high`. Runtime model/effort and Fast/priority tier are not independently verifiable in this session; no routing/configuration changes or nested agents.
- Before editing, the two owned source files had no Git changes and the assigned new test/note files did not exist. No reset/revert/commit; other scopes left untouched.

## Changes

- `Assets/_Game/Scripts/Logic/Game/AutoEquip.cs`: retain the existing first allocation, then make exactly one bounded backfill pass. Reserve the actual selected copies, start each hunter from its first planned loadout, and offer only spare inventory available in party commit order. This recovers the unused sword_knight in the reported two-warrior case, protects the later hunter's sword_runic, and keeps one final plan/result per hunter. Preview current IDs, scores and stat deltas still compare against the original equipped gear. Planning remains read-only; application still goes through PartyStats.Equip.
- `Assets/_Game/Scripts/Logic/Game/Enhancement.cs`: equipment with no positive HP/MP/ATK/MAG/DEF/RES/SPD is omitted from smithy candidates, has no quoted paid step, and returns `no_enhanceable_stats` before any payment or level write. Positive-stat equipment retains existing costs, shared per-ID enhancement, cap and rounding progression. Legacy levels on effect-only gear are preserved, not refunded or rewritten.
- `Tools/LogicTests/EquipmentProgressionRepairTests.cs`: six focused regression methods added using actual equipment data and the existing LogicTest harness.

## Regression source / parent verification

Added methods:

1. `PartyBackfillUsesUnclaimedAlternativeInOneApply`: reported leftovers, planning purity, final preview/apply agreement, original stat deltas, ownership and no second click for this scenario.
2. `PartyBackfillPreservesScarceCopiesAndInventoryOrderIndependence`: one/two copies, higher-gain reservation, reversed bag insertion order and class restrictions.
3. `PartyBackfillDoesNotPromiseGearReturnedByLaterHero`: an earlier warrior cannot consume a later mage's still-worn power band; all final commits succeed and ownership is conserved.
4. `EffectOnlyEquipmentRejectsEnhancementWithoutAnyMutation`: five authored effect-only accessories, worn and bag copies, fresh and legacy +3 levels, explicit refusal, no cost/candidate and byte-equivalent serialized state after rejection.
5. `UsefulEnhancementStillChargesOnceAndImprovesAllCopies`: iron sword +1, exact gold/stone cost and both worn copies improved without gear duplication.
6. `SmallPositiveStatsCanProgressThroughRoundingPlateau`: awake bell SPD +2 can advance through the initial rounded plateau to a real gain at +3.

Parent-owned commands, **not run here**:

```text
python Tools/logic_test.py EquipmentProgressionRepairTests
python Tools/logic_test.py AutoEquipTests
python Tools/logic_test.py GearExpansionTests.EnhancementStatAndCostMath
python Tools/logic_test.py GearExpansionTests.EnhanceAtSmithyRaisesWornStatsAndSurvivesSave
```

## Checks and limitations

- [x] Relevant plan/reports/current sources read; bounded changes and new regression source written.
- [x] Read-only diff/source review, including existing test APIs and authored fixture values; `git diff --check` clean for the modified source files.
- [ ] Compilation and test execution: deliberately deferred to the parent for serial recompilation. No test pass or runtime claim.
- [ ] Independent review: parent-owned; no nested agents used.
- Exactly one backfill pass is intentional, not a global optimizer/fixed-point search. Gear still worn by a later party member remains unavailable to earlier commits; no reordering or temporary unequip stage was introduced.
- No UI/localization changes. The new service failure uses `reason_no_enhanceable_stats`, whose localized text is outside this ownership scope. Normal smithy flow excludes these entries, so it does not display the old misleading max-level/insufficient-funds state for them. Direct callers receive the explicit machine-readable reason.
- Report 19 finding 2 (effect comparison UI) is outside this slice and remains for the coordinator.
