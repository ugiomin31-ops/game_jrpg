# 17-roster — bounded read-only audit

- Requested model: `gpt-6-astra`; requested reasoning effort: `high`.
- Requested service priority: Fast/priority. Actual model routing, effort and service tier were not independently verifiable from this session's exposed metadata; no configuration or model changes were made.
- Verified branch: `codex/astra-enrichment-20261015`; HEAD: `efdc1517f48ac8887e1fcf6843b6df44df6ebc3c` (expected base).
- Method: focused source reads and call-site searches in the assigned workspace. Existing working-tree changes were preserved. Reports 01–06 were searched for overlapping findings; no report 07 was returned by the scoped filename search.

## Result

**No concrete reachable findings identified within this bounded static audit.** This is not a runtime acceptance result.

## Evidence reviewed

- **Recruitment and duplicates:** `Assets/_Game/Scripts/Logic/Game/HunterRoster.cs:49–61` rejects already recruited IDs before allocating a member. `GameState.cs:188–192` searches both party and reserve; `GameState.cs:356–377` deduplicates loaded membership, restores missing starters, limits the active party to four, and repairs each hunter. `HunterRoster.cs:109–115` recomputes scout eligibility before payment, so a repeated successful scout request becomes unavailable before a second charge.
- **Swap and bench:** `HunterRoster.cs:123–150` checks town/pending-battle state, moves the existing member between lists, restores a removed reserve member on a full-party failure, and prevents benching the final member. `Assets/_Game/Scripts/UI/Screens/GameUI.Party.cs:38–58` also gates the exposed formation actions. `SwapSlots` lacks its own town guard (`HunterRoster.cs:154–157`), but the located UI callers require `FormationOpen`; no reachable bypass was established, so this is not reported as a finding.
- **Dead reserve:** `HunterRoster.cs:160–169` intentionally grants EXP to every reserve member. `Assets/_Game/Scripts/Logic/Game/PartyStats.cs:423–426` keeps a KO'd member at zero HP during level-up. `Assets/_Game/Scripts/Logic/Game/TownServices.cs:126–136` restores the whole roster at the inn. Dead members can be exchanged, with current HP shown in `GameUI.Party.cs:61–74`; no demonstrated recovery lock was found. The documented bench-EXP rule does not exclude KO'd reserves, so its difference from active-party EXP eligibility is not treated as a defect.
- **Progression gates:** `HunterRoster.cs:30,79–116` uses deepest-floor zone for scouts and the corresponding boss-cleared flag for story joins, with affordability checked before spending. `Assets/_Game/Scripts/Logic/Game/GameFlow.cs:136–157` invokes story recruitment on entering town. `Assets/_Game/Scripts/UI/Screens/GameUI.Town.cs:198–203,227–243` exposes scouting through the guild and disables locked/unaffordable offers. No normal-call-path gate bypass was established.

## Acceptance checklist

- [x] Recruit/swap, duplicate membership, dead reserve, and recruitment progression gates inspected.
- [x] At most two findings: zero supported findings reported; hypothetical/corrupt-state issues excluded.
- [x] No agents, tests, builds, Unity/editor/browser actions, network requests, asset generation, secret reads, or unrelated history access.
- [x] No source, configuration, UI, application binary, or game fixes; only this assigned report written.
- [x] Runtime behavior remains unverified; integration belongs to the main coordinator.
