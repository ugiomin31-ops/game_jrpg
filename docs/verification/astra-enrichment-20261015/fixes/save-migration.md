# save-migration — implementation handoff

- Approved scope: `plan/2026-10-15-astra-enrichment.md`, reports `11-save-codec.md` and `13-campaign-migration.md`; both defects rechecked against current source before edits.
- Requested routing: `gpt-6-astra` / `high`, Fast/priority where supported. Actual runtime model/effort and service tier are not independently attested by this slice. No nested agents or configuration changes.
- Baseline: branch `codex/astra-enrichment-20261015`, HEAD `efdc1517`; owned production paths had no pre-existing changes. No reset, revert, commit or edits to other workers' scopes.

## Exact changed files

1. `Assets/_Game/Scripts/Logic/Game/GameState.cs`: remove null party/reserve entries after collection initialization and before legacy hero lookup. Existing roster reconstruction, progression and duplicate precedence remain in place; no exception-catching expansion.
2. `Assets/_Game/Scripts/Logic/Game/CampaignMigration.cs`: map old chapter 7 to current postgame zone 13, using the existing completion path for the boss flag, cleared boss cells, defeated-boss credit and deepest floor. Chapters 1–6 keep their existing city/gate mapping. The hunter-layout guard still prevents repeat migration.
3. `Tools/LogicTests/SaveMigrationRepairTests.cs`: six `[LogicTest]` methods, automatically included by the existing test-source glob:
   - `NullLegacyPartyEntryLoadsAndRepairsMissingHunters`: exact report-11 JSON repro and stable reload.
   - `NullSlotsInEitherRosterPreserveLegacyHeroProgress`: four party/reserve combinations; level, XP, job, vitals, gear, skills, membership and stable reload.
   - `NullSlotsDoNotOverwriteAnExistingHunterWithLegacyDuplicate`: existing hunter precedence with null entries in both lists.
   - `CompletedLegacyPostgameRetainsBossCellObjectiveAndLateQuestCredit`: all completed zones/boss cells, completed guild objective, late bounty acceptance, one reward and stable reload.
   - `ReachingLegacyPostgameWithoutVictoryDoesNotGrantCompletion`: negative control for reaching but not defeating the old final boss.
   - `ValidHunterLayoutSaveKeepsItsCurrentZoneSevenProgress`: current-layout flags and serialized state remain unchanged; current chapter 7 is not remapped.
4. This note: `docs/verification/astra-enrichment-20261015/fixes/save-migration.md`.

`HunterRoster.cs` and `SaveCodec.cs` needed no changes.

## Verification and limits

- [x] Source traces rechecked; minimal production diff and regression source reviewed read-only.
- [x] Owned tracked production diff passes `git diff --check`.
- [x] No tests, compilation, builds, Unity/editor/browser, installs or network actions performed.
- [ ] Parent must compile current sources serially and run `python Tools/logic_test.py SaveMigrationRepairTests`; existing focused controls are `CampaignStructureTests` and `HunterRosterTests`. No pass result is claimed here.
- [ ] Independent review and integration remain with the parent coordinator.

This fixes incoming legacy saves. Saves already converted and resaved by the buggy migration have lost the old completion flag and carry the hunter-layout marker; this change deliberately does not infer or rewrite their completion. Normal unknown-ID filtering and missing-starter recovery are retained. No save files were edited.
