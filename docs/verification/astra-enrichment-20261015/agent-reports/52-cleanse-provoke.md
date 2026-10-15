# 52 — Cleanse / Provoke classification verification

- Requested execution: `gpt-6-astra`, reasoning `high`, Fast/priority service where supported.
- Observed execution: this session exposes no independently verifiable model/effort or service-tier receipt. Requested priority is not verified priority; no model or configuration changes were made. No child agents were launched.
- Repository: `C:\Users\User\Desktop\GAME_JRPG\handoff-verify-20261015`.
- Verified branch: `codex/astra-enrichment-20261015`; HEAD and requested base both resolve to `efdc1517f48ac8887e1fcf6843b6df44df6ebc3c`.
- Method: bounded static reads of report 04, status binding/refresh, cleansing, targeting, relevant data and existing test source. No tests or runtime actions executed. Paths below are repository-relative.

## Verdict and one qualified finding

**Report 04's classification defect is confirmed for the supported external-Provoke engine path. Current shipped-content player reachability is not established.** Its P2 should therefore be treated as an engine-contract issue, not evidence that normal use of the existing self-taunt skills fails.

**Location:** `Assets/_Game/Scripts/Logic/Battle/BattleStatus.cs:25,115` classifies every Provoke as beneficial. `Assets/_Game/Scripts/Logic/Battle/BattleEngine.cs:1298` excludes every beneficial status from general Cleanse.

**Concrete engine repro (source-derived, not executed):** Use the established setup in `Tools/LogicTests/EnemyIntentTests.cs:336-340`: apply `BattleStatus.FromDef(db.Statuses["provoke"], forced.Party[2].Id)` to the living opposing actor. The existing assertion establishes this as the forced-target form. While it remains active, have that actor or an ally submit an ordinary ally-targeted Cleanse skill. Because the source differs from the holder, the holder is constrained by `BattleUnit.cs:297-301`, but `IsBeneficial` remains true and the loop at `BattleEngine.cs:1295-1303` leaves it attached. A Cure item with empty `StatusId` follows the same predicate (`BattleEngine.cs:1289`; the real remedy is `Assets/_Game/Resources/Data/items.json:816-828`).

**Impact:** General ailment removal leaves externally imposed forced targeting intact for future target resolution. Applied-status events and snapshots also label this form beneficial (`BattleEngine.cs:1394`; `BattleUnit.cs:496`). Self/empty-source Provoke is intentionally a taunt buff (`BattleUnit.cs:305-311`) and must remain beneficial.

**Reachability limit:** The three Provoke payloads found in `Assets/_Game/Resources/Data/skills.json` belong to `jb_kn_vow` (`:1033,1038,1051`), `sk_provoke` (`:5003,5008,5021`) and `sig_minjun` (`:7076,7081,7094`). Each has `target_type: 2`, meaning Self (`Assets/_Game/Scripts/Logic/Data/GameData.cs:14`). The existing test deliberately installs external Provoke; it does not prove these shipped skills produce it. No second finding is reported.

## Smallest safe implementation proposal — not applied

1. Extend the existing internal binder at `Assets/_Game/Scripts/Logic/Battle/BattleStatus.cs:134` to accept the holder ID: `BindTo(int holderMaxHp, string holderId)`. Preserve its barrier calculation and add:

   ```csharp
   if (EffectType == StatusEffectType.Provoke)
       _beneficial = SourceId == "" || SourceId == holderId;
   ```

2. Change the existing call at `Assets/_Game/Scripts/Logic/Battle/BattleUnit.cs:424` to `effect.BindTo(MaxHp, Id)`. Binding already runs before either append or refresh. The focused battle-source search found this single call site.
3. Leave `RefreshFrom` unchanged: it already copies both `SourceId` (`BattleStatus.cs:146`) and `_beneficial` (`:155`) from the incoming, now-bound instance. This handles self → external and external → self refreshes without a second classification path. Keep the existing maximum-duration and barrier-pool semantics (`:142,152`).

This confines implementation to two files and retains the public `FromDef` signature. Holder-relative classification becomes authoritative on application. Do not remove Provoke from `BeneficialTypes` wholesale, special-case only Cleanse, alter targeting, change data, or add a holder field: those are unnecessary for this defect. Existing events are emitted after binding (`BattleEngine.cs:1388-1394`), so they receive the corrected classification automatically.

## Meaningful regression tests for the coordinator — proposed, not run

Use the existing logic harness and ordinary multi-turn statuses; `Tools/LogicTests/QualityUpgradeTests.cs:12-39` provides a deterministic command fixture, and `EnemyIntentTests.cs:325-342` documents frozen-intent behavior.

1. **External Provoke + real Cleanse resolution:** Apply Provoke from a living opposing unit; assert attached status and snapshot are nonbeneficial. Submit an accepted Cleanse skill through `BattleEngine.Submit`; assert the status is absent and exactly one matching `StatusRemovedEvent` has `Reason=Cleansed`. Repeat through a Cure item with empty `StatusId`. Choose a duration that survives the command so expiration cannot produce a false pass. These removal assertions fail on the audited implementation.
2. **Self/empty-source preservation:** For source equal to holder ID, empty string, and null (normalized to empty at `BattleStatus.cs:65`), apply Provoke together with Poison. Execute general Cleanse; assert Poison is removed, Provoke remains beneficial, and `IsTaunting` remains true. This prevents a wholesale removal from `BeneficialTypes` from appearing correct.
3. **Same-ID refresh in both directions:** Apply self Provoke, refresh externally, then refresh back to self/empty source in isolated cases. Assert one attached instance, updated source and classification, preserved longer duration, and matching snapshot values. A general Cleanse must remove only the externally refreshed form. Exercise application through the engine for `StatusAppliedEvent.Beneficial` and `Refreshed` assertions, rather than testing only an unbound `FromDef` object.
4. **Actual targeting consequence:** With two living opponents and neither self-taunting, externally provoke a hero. Its single-target attack must resolve to the source before cleansing; after a successful cleanse, a newly submitted attack must honor the other selected opponent. Keep `EnemyIntentTests.FrozenTargetAndProvokeAreResolvedAtPlanningOnly` unchanged: clearing a status must not rewrite an already frozen enemy intent.
5. **Binder collateral check:** Apply a normal percentage Barrier and refresh it; retain the existing max-HP-derived pool and maximum remaining-pool behavior. This guards the only unrelated behavior in the method whose signature changes.

## Acceptance checklist

- [x] Report 04's classification claim independently compared with current relevant source.
- [x] One concrete engine-path finding with exact lines, repro, impact and explicit shipped-content limitation.
- [x] Smallest implementation and behavioral regression proposals recorded; no implementation or test changes.
- [x] No nested agents, network/relay access, auth reads, configuration changes, builds, tests, Unity/editor/browser actions or unrelated history access.
- [x] Only assigned report written; integration and execution of verification remain with the main coordinator.
