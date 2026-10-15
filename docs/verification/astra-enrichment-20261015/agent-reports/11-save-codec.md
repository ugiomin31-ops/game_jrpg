# 11-save-codec — bounded read-only source audit

- Requested model: `gpt-6-astra`; requested reasoning effort: `high`.
- Requested service: Fast/priority. Actual model, effort and service tier are not independently attested by available session metadata. No model/configuration changes or nested agents were invoked.
- Verified branch: `codex/astra-enrichment-20261015`; HEAD/base: `efdc1517f48ac8887e1fcf6843b6df44df6ebc3c`.
- Method: focused static reads of SaveCodec and its directly connected state, migration, encounter and runtime load paths. No tests, builds, runtime/UI/browser actions, network requests or source edits. The only written file is this report.
- Duplicate check: available reports 01–06 contain no SaveCodec/legacy-null finding; report 07 was absent when checked.

## Finding: P2 — null roster entries can escape the corrupt-save handler during legacy migration

**Location:** `Assets/_Game/Scripts/Logic/Game/SaveCodec.cs:87-90`; underlying ordering at `Assets/_Game/Scripts/Logic/Game/GameState.cs:355-362`, dereference at `GameState.cs:190` and migration lookup at `Assets/_Game/Scripts/Logic/Game/HunterRoster.cs:40`.

**Repro input (static trace, not executed):** With the current hunter database containing `h_dohyun` and no legacy `warrior` row, load `{"version":1,"party":[null,{"id":"warrior"}]}` through `SaveCodec.Deserialize(json, db)`, or use a legacy save with one party entry replaced by JSON null and select Continue. These are ordinary null/missing-entry corruption and a supported old hero id, without extreme numeric inputs.

**Trace:** JSON null collection elements survive deserialization; ignoring null-valued properties does not filter list entries. `Repair` calls `MigrateLegacyHeroes` before the null-dropping party reconstruction. The migration skips the null in its own iteration, then translates `warrior` to `h_dohyun` and calls `state.Hero(hunter)` to check for duplicates. `Hero` scans the original party and dereferences the null entry's `Id`. The resulting `NullReferenceException` is outside SaveCodec's exception filter. `SaveRepository.Read` (`Assets/_Game/Scripts/Runtime/Persistence/SaveRepository.cs:25`) propagates it, and `GameApp.Continue` (`Assets/_Game/Scripts/Runtime/GameApp.cs:119-121`) catches only IO/access/SaveFormat exceptions.

**Impact:** This recoverable legacy roster corruption aborts loading with an uncaught exception instead of either dropping the null entry (the repair routine's later intended behavior) or showing the normal invalid-save notification. No claim of process termination or on-disk data loss is made.

## Remaining scope checks and limits

- Roundtrip structure: public campaign/hero/floor fields are serialized through one snake-case serializer; GridPos writes `[x,y]` and reads arrays or legacy `{x,y}` objects (`SaveCodec.cs:45-59,114-127`). Pending encounter identity is persisted; its runtime `Setup` is intentionally ignored and rebuilt on dungeon resume (`DungeonRun.cs:13-23,100-103`). No additional concrete roundtrip defect was established in this bounded pass.
- Schema/older saves: current version is 1; missing version defaults to 0; negative and newer versions are rejected. The codec migration table is empty; campaign and hero migration currently occur in database-backed `Repair` (`SaveCodec.cs:37-43,74-87`). Missing additive fields receive initializers/defaults. Calling without a database intentionally skips repair.
- Corruption/nulls: empty text, malformed JSON and listed conversion exceptions are wrapped as SaveFormatException. `Repair` initializes collections, removes null quest/bestiary rows and rebuilds null floor rows (`GameState.cs:311-352`). The finding above concerns the remaining pre-filter roster lookup.
- Acceptance checklist: branch/base verified; requested routing versus verified tier distinguished; focused source inspection complete; one concrete reachable finding with locations/repro/impact; prohibited execution avoided; only assigned report written. All behavioral conclusions are static source evidence, not runtime test results. Integration belongs to the main coordinator.
