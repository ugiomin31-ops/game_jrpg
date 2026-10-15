# 25-readiness — bounded read-only source audit

- Requested model: `gpt-6-astra`; requested reasoning effort: `high`.
- Requested service tier: Fast/priority. Actual model, effort and service tier are not independently exposed/verified by this session; no routing or configuration changes made.
- Verified branch: `codex/astra-enrichment-20261015`; HEAD: `efdc1517f48ac8887e1fcf6843b6df44df6ebc3c` (requested base).
- Method: focused static inspection of current working-tree sources and existing reports 01–06. No agents, tests, builds, Unity/editor/browser actions, network requests, secret reads or source edits.
- Result: **1 concrete source-supported finding**. Reproduction below is a source-traced gameplay sequence, not an executed runtime test.

## P2 — Carried poison can receive an all-clear departure assessment

**Location:** `Assets/_Game/Scripts/Logic/Game/ExpeditionReadiness.cs:59-66` (checks end without inspecting `hero.Statuses`); all-clear text at `:20-23`.

**Reachable reproduction:** Start with four healthy hunters and normal MP. Step on a dungeon trap that poisons a hunter, return to town without resting/cleansing, and inspect readiness. A single trap removes approximately 8% of maximum HP, so the hunter remains well above the 35% warning threshold; MP remains above 20%. With no other warnings, readiness says `출발 준비 양호: 4/4명` despite active poison. Depart without treatment and the poison is carried into combat.

**Evidence chain:**
- `Assets/_Game/Scripts/Logic/Dungeon/DungeonRun.cs:253-256`: stepping on a trap calls `PartyStats.ApplyTrap`.
- `Assets/_Game/Scripts/Logic/Game/PartyStats.cs:378-398`: default trap damage is 8%, poison probability is 30%, and successful poison writes the carried status for its authored duration.
- `Assets/_Game/Scripts/Logic/Dungeon/DungeonRun.cs:421-426` and `Assets/_Game/Scripts/Logic/Game/GameFlow.cs:136-151`: normal town return clears carried TP/refills springs but does not clear hunter statuses or restore HP/MP.
- `Assets/_Game/Scripts/Logic/Game/ExpeditionReadiness.cs:43-66`: readiness checks party count, KO, HP below 35%, and MP below 20%; carried harmful statuses never create an issue.
- `Assets/_Game/Scripts/UI/Screens/GameUI.Town.cs:40-51`: zero issues displays the all-clear summary using the positive color.
- `Assets/_Game/Scripts/Logic/Game/PartyStats.cs:333-334`: living hunters' positive-duration statuses are copied into their combat specifications.
- `Assets/_Game/Resources/Data/statuses.json:211-216`: ordinary poison lasts three turns and deals 6% maximum HP per turn; `Assets/_Game/Scripts/Logic/Battle/BattleStatus.cs:70` maps its magnitude to turn damage, consumed by `Assets/_Game/Scripts/Logic/Battle/BattleEngine.cs:532-540`.

**Impact:** The departure advisory gives a false all-clear for a normal persistent damage condition, allowing avoidable HP loss on the next expedition without a readiness warning. This is an advisory omission, not a demonstrated softlock or an assertion that all other UI conceals the status.

## Other checks and limits

- Readiness evaluation itself does not deduct resources or alter party/campaign/RNG state in the inspected implementation.
- `Assets/_Game/Scripts/Logic/Game/TownServices.cs:597-600` gates departure by unlocked floors, independently of readiness warnings; no readiness-induced progression lock established.
- Effective HP/MP maxima include job, seeds and equipment (`PartyStats.cs:187-198`); comparisons widen to `long` before multiplication (`ExpeditionReadiness.cs:61,65`).
- Objective selection follows `GameFlow.StoryChapter` and the red-gate completion flag (`ExpeditionReadiness.cs:73-111`, `GameFlow.cs:65-70`); no concrete objective mismatch established in this pass.
- No second finding asserted. Runtime reproduction and exhaustive content validation were outside the authorized scope.

## Acceptance

- [x] Focused readiness and directly connected caller/resource paths inspected.
- [x] At most two findings; one includes exact location, normal gameplay trigger and impact.
- [x] Requested routing distinguished from independently verified execution metadata.
- [x] Only the assigned report written; no game fixes or execution performed.