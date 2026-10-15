# 18-jobs — bounded read-only source audit

- Requested model: `gpt-6-astra`; requested reasoning effort: `high`; requested service tier: Fast/priority.
- Observed execution: this audit used the current session without changing model, persona, configuration, or binaries. The available tool responses do not independently attest the actual model, reasoning effort, or service tier; requested priority is not verified priority.
- Verified branch: `codex/astra-enrichment-20261015`.
- Verified HEAD/base: `efdc1517f48ac8887e1fcf6843b6df44df6ebc3c` (matches expected `efdc1517`).
- Scope: `JobService.cs`, `jobs.json`, and focused supporting reads for selection, skill assignment, data loading, and unlock references. No runtime execution was performed.

## Findings

None. No concrete reachable defect was established in the requested unlock-requirement, skill-assignment, or selection-validity scope. This is a bounded static audit, not a runtime acceptance claim.

## Evidence reviewed

- **Selection validity:** `Assets/_Game/Scripts/Logic/Game/JobService.cs:48–55` filters next jobs by the hunter's base class and current parent. `:59–79` rejects unknown jobs and non-child/cross-class selections while checking level, boss, and item requirements. `:121–130` resolves an actually recruited hunter, rejects non-town/pending-battle states, and repeats the checks before consuming the item. `Assets/_Game/Scripts/UI/Screens/GameUI.Jobs.cs:55–64` uses these options; `:107–119` executes through `ChangeJob`, so the modal's captured availability is not the final authorization.
- **Recruitment and class mapping:** `Assets/_Game/Scripts/Logic/Game/GameState.cs:188–206` resolves party and reserve hunters; `Assets/_Game/Scripts/Logic/Data/GameData.cs:435–436` maps hunter IDs to base classes. All 20 rows inspected in `heroes.json` use the four base classes represented in `jobs.json`.
- **Unlock requirements:** the 20 job rows comprise four base jobs, eight tier-2 jobs requiring level 12 / `job_medal` / `forest_guardian`, and eight tier-3 jobs requiring level 36 / `master_seal` / `festival_pumpkin_king`. Promoted rows have same-class parents. Both required bosses and both required items resolve in the corresponding data files. Bosses appear in `Assets/_Game/Resources/Data/dungeon.json:1362` and `:6528`; quest rewards include the materials at `Assets/_Game/Resources/Data/quests.json:68` and `:384`. `JobService.cs:40–44` accepts recorded kills or an explicit boss flag; `PartyStats.cs:469` records defeated-enemy kills.
- **Skill assignment:** all 96 job learnset entries resolve in `skills.json`. `Assets/_Game/Scripts/Logic/Game/PartyStats.cs:127–138` builds the ancestor path, and `:257–268` combines the hunter's base skills with level-eligible skills from that path, removing duplicates. Base-job learnsets are empty in the inspected data. `JobService.cs:106–111` uses the same calculation for preview, and `:139` synchronizes after promotion. `PartyStats.cs:288–294` replaces the cached list with that calculated set; the permitted parent-to-child transitions retain predecessor skills. `GameState.cs:412–417` restores class-valid jobs and synchronizes skills on repair.
- **Loading:** `Assets/_Game/Scripts/Logic/Data/GameData.cs:396–413` uses snake-case mapping and loads `jobs`, connecting `required_level`, `required_item`, `required_boss`, and `learnset` to the inspected definitions.
- Existing report headings and job-related matches in available reports 01–06 were checked for overlap; report 07 was absent from the initial listing.

## Acceptance checklist

- [x] Checked expected branch/base and focused relevant sources only.
- [x] Covered unlock requirements, skill assignment, and selection validity.
- [x] Reported no speculative/extreme-input findings; concrete findings: 0.
- [x] No nested agents, tests, builds, Unity/editor/browser actions, network requests, asset generation, auth reads, or source changes.
- [x] Only this assigned report was written. Integration remains with the main coordinator.
- [x] Requested model/effort/tier are separated from independently verified execution evidence.

Limit: conclusions follow source/data inspection; no gameplay reproduction or visual verification was authorized or claimed.
