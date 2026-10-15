# 13 — Campaign migration bounded audit

- Requested model: `gpt-6-astra`; requested reasoning effort: `high`; requested scheduling: Fast/priority. Actual model, effort and service/priority tier were not independently attested by available runtime metadata. No routing or configuration changes were made.
- Verified checkout: `codex/astra-enrichment-20261015`, HEAD `efdc1517`.
- Method: focused source/data reads only; reproduction below is a source-derived walkthrough, not an executed test. No nested agents, tests, builds, Unity/editor/browser actions, network requests, assets, secrets or outside-workspace history accessed. Only this assigned report was written.

## Finding 1 — P2: Completed legacy postgame loses its boss-clear state

**Location:** `Assets/_Game/Scripts/Logic/Game/CampaignMigration.cs:95-99` (especially line 99).

The migration collects and removes boss flags for old chapters 1 through 7, but skips chapter 7 because `OldMainChapters` is 6. It never writes the corresponding `boss_13_cleared` flag or marks the new postgame boss cell cleared. This differs from chapters 1–6, whose completion flags and boss cells are explicitly migrated at lines 100–108. Old postgame floor indices are already mapped into zone 13 at lines 50–51, so this is a missing part of the same supported 35-to-39-floor migration.

**Reachable repro (not executed):**

1. Load an ordinary completed 35-floor save: `layout_35f` present, `layout_hunter_39f` absent, `boss_7_cleared` present, and deepest floor index 34. Leave `q_ex_lord` unaccepted, as a player who defeated the final boss before taking its bounty can do.
2. `SaveCodec.Deserialize(json, db)` calls `GameState.Repair` (`SaveCodec.cs:85-87`), which applies the migration (`GameState.cs:354`). The deepest index becomes 38, but the old seventh boss flag is removed and discarded. The hunter-layout marker is already installed at `CampaignMigration.cs:65`, making the loss persist on subsequent loads.
3. Inspect the guild objective or accept `q_ex_lord`. The completion objective requires `boss_13_cleared` (`ExpeditionReadiness.cs:75-85`). The quest unlocks at index 38 and targets `abyss_lord_ex` (`Assets/_Game/Resources/Data/quests.json:723-734`), whose current boss floor is `red_gate_3` (`dungeon.json:12995,13099-13100`). Quest acceptance refreshes historical victories, but `QuestLog.BossVictories` checks the current chapter-clear flag only (`QuestLog.cs:37-44,126-129,160-166`); retained bestiary kills do not satisfy it.

**Impact:** A legitimately completed old postgame reappears as unfinished. The player must defeat the postgame boss again to restore completion and obtain retrospective bounty credit. Existing claimed/completed quest rows are not alleged to be reset. The coordinator should preserve old chapter-7 completion as current zone-13 completion, including its boss-cell state.

## Other inspected behavior and acceptance

- [x] Reviewed the 12-floor → 35-floor → 39-floor mapping, warp selection, obsolete map-progress removal, story flags, pending battle reset and town return.
- [x] Reviewed party migration order: old hero IDs are renamed before roster filtering; recognized hero objects retain their progression and then undergo normal repair (`HunterRoster.cs:35-41`; `GameState.cs:354-377,395-421`). No additional concrete party defect established.
- [x] Reviewed quest acceptance/refresh and actual current postgame content. No second sufficiently supported finding established.
- [x] Checked available reports 01–06 for overlap; report 07 was not present in the focused listing. This finding is distinct from their recorded subjects.
- [x] Stayed within the assigned read-only audit scope except for writing this report; no game fixes or runtime verification performed. Integration belongs to the main coordinator.
