# 09 — Break mechanics: bounded read-only audit

- Requested model: `gpt-6-astra`; requested reasoning effort: `high`.
- Requested scheduling: Fast/priority. Actual model, effort and service/priority tier are not independently verified by available session evidence. No model/persona/configuration changes or agents invoked.
- Verified branch: `codex/astra-enrichment-20261015`; HEAD: `efdc1517` (expected base). Reviewed current working-tree files, including existing coordinator changes; HEAD does not attest those files are pristine.
- Result: **0 concrete new reachable findings established in this bounded pass.** This is static inspection, not a runtime correctness or test-pass claim.
- Scope: weakness reveal, shield loss/BREAK, recovery ordering, guard and multi-hit interactions. Paths below are repository-relative.

## Acceptance checklist and source evidence

- [x] Weakness visibility: `Assets/_Game/Scripts/Logic/Battle/BattleEngine.cs:165-184` exposes only known/discovered enemy keys; `BattleEngine.Commands.cs:136-145` preserves Unknown for unseen elemental affinity. A landed weakness hit reaches discovery at `BattleEngine.cs:1170-1173`; `:1197-1202` deduplicates reveal events by enemy definition and element. `:1627` copies discoveries into the outcome. Misses bypass DealHit at `:1091-1095`.
- [x] Shield/BREAK timing: `Assets/_Game/Scripts/Logic/Battle/BattleEngine.cs:1152-1188` applies HP damage first, then shield loss only for a surviving, shield-bearing, unbroken target. Weakness contributes one pip and BreakPower contributes extra pips; zero shield sets Broken, emits BREAK, cancels charge and awards TP. Already broken targets cannot repeatedly award break TP.
- [x] Multi-hit: `Assets/_Game/Scripts/Logic/Battle/BattleEngine.cs:1067-1106` rolls each hit against current target state and stops hitting a dead target. Thus the shield-emptying hit uses the prior state and subsequent hits receive BREAK amplification through `Assets/_Game/Scripts/Logic/Battle/DamageFormula.cs:56,97`. Random picks whose original target died select from remaining living opponents at `BattleEngine.cs:1076-1083`.
- [x] Recovery ordering: `Assets/_Game/Scripts/Logic/Battle/BattleEngine.cs:343-348` skips the broken actor's entire next turn. `:505-521` applies turn-end effects, expires surviving-holder statuses, then restores the shield only when the actor remains alive. `:544-548` stops turn-end processing after lethal damage.
- [x] Guard: `Assets/_Game/Scripts/Logic/Battle/BattleEngine.cs:909-911` sets guarding and `:341` clears it at the actor's next turn start. `Assets/_Game/Scripts/Logic/Battle/DamageFormula.cs:93-111` applies guard after element/BREAK/status multipliers for each ordinary damage hit; guard does not suppress weakness discovery or shield loss. Fixed damage items use their separate documented affinity/BREAK formula (`BattleEngine.cs:1133-1143`); no unestablished guard contract is asserted for those items.
- [x] Multi-hit previews: `Assets/_Game/Scripts/Logic/Battle/BattleEngine.Commands.cs:249-265` advances shield/BREAK state between hits without modifying the target. Random previews intentionally return per-hit bounds without a guaranteed break (`:242-247`). Current authored BreakPower skills in `Assets/_Game/Resources/Data/skills.json` are four single-target, single-hit skills; no reachable random-BreakPower defect was established from that data.

## Prior-report reconciliation and limits

Reports 01–06 were consulted for overlap; no report 07 existed during inspection. Report 02 describes recovery after lethal poison, but the current `Assets/_Game/Scripts/Logic/Battle/BattleEngine.cs:512` already includes `actor.IsAlive`. That prior issue is not repeated as a current finding. Existing `Tools/LogicTests/BreakRecoveryTests.cs` contains lethal-poison and surviving-poison cases; these were read, not executed. Relevant assertions in `Tools/LogicTests/ActionPreviewTests.cs` were also inspected as source only.

- [x] Focused source/data/report reads only; no broad repository or Library scan.
- [x] No tests, builds, Unity/editor/browser actions, network requests, asset generation, secret reads, source changes or nested agents.
- [x] Only this assigned report written. Integration and runtime acceptance remain with the main coordinator.
