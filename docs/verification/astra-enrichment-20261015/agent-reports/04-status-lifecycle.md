# 04 — Status lifecycle audit

- Requested model/effort: `gpt-6-astra` / `high`; actual routing not independently verifiable in this session.
- Requested base: `efdc151` (user supplied; no Git commands used).
- Method: brief static audit of current working files; no tests executed or source changes made.
- Scope: BattleStatus.cs, BattleUnit.cs, relevant BattleEngine/EnemyAI call sites, StatusDef, and existing focused test source.
- Paths below are relative to the repository root.

## Finding 1 — P2: externally applied Provoke cannot be cleansed as an ailment

**Location:** `Assets/_Game/Scripts/Logic/Battle/BattleStatus.cs:25` and `:115`.

**Trigger:** Apply Provoke to a living holder with another unit's nonempty SourceId, then use a general Cleanse (no specific item StatusId) on that holder before expiration.

**Demonstrated source chain:**
- `BattleStatus.cs:21-25,115` classifies every Provoke as beneficial, regardless of its holder/source relationship.
- `Assets/_Game/Scripts/Logic/Battle/BattleUnit.cs:297-301` explicitly treats that relationship as forced targeting; `:305-311` separately recognizes self/empty-source Provoke as taunting.
- `Assets/_Game/Scripts/Logic/Battle/BattleEngine.cs:1295-1301` removes only `!s.IsBeneficial` for general Cleanse, so the externally imposed targeting restriction survives.
- `Tools/LogicTests/EnemyIntentTests.cs:336-340` already constructs external Provoke and asserts its forced-target behavior. This is a supported code path, not a claim about its frequency in shipped encounters.

**Effect:** General ailment removal cannot remove external Provoke. The status also reports Beneficial=true in snapshots/events. Self-taunt should remain beneficial.

**Minimal fix:** Classify Provoke using the holder ID when binding it in `BattleUnit.ApplyStatus`; beneficial only when SourceId is empty or equals the holder ID, matching IsTaunting. Preserve that classification when RefreshFrom replaces SourceId and `_beneficial` (`BattleStatus.cs:146,155`). Do not simply remove Provoke from BeneficialTypes, which would make self-taunt cleansable as an ailment.

**Focused test proposal (not run):** Apply external Provoke, execute an untargeted-by-status Cleanse, assert the status is removed and Beneficial was false. Repeat with self/empty-source Provoke and assert it remains beneficial and survives. Refresh the same ID from self to external and back, checking classification each time. Do not assert that cleansing rewrites an already frozen enemy intent; existing tests explicitly preserve that intent.

## Remaining audited behavior

- Duration is clamped to at least one at creation (`BattleStatus.cs:63`); holder turn-end effects run before countdown/removal (`BattleEngine.cs:508-511`, `BattleUnit.cs:452-463`).
- Same-ID application refreshes one instance (`BattleUnit.cs:424-434`), keeping the longer duration and larger remaining barrier pool (`BattleStatus.cs:142,152`); distinct IDs coexist and stat scales multiply (`BattleUnit.cs:232-236`). No stacking-cap contract exists in StatusDef (`GameData.cs:144-154`).
- Engine application and initial registration check immunity (`BattleEngine.cs:1380-1388,1520-1523`); ID/type matching is case-insensitive (`BattleStatus.cs:119-130`).
- Consumed barriers, awakened Sleep, and physically shattered Freeze are removed inside ReceiveDamage (`BattleUnit.cs:347-392`), without ticking unrelated durations.
- No additional demonstrated issue identified in this bounded pass; these observations are static evidence, not a runtime pass.

## Acceptance checklist

- [x] Durations, stacking, immunity, and expiry paths inspected.
- [x] One finding with exact locations, trigger, effect, minimal fix, and focused test proposal.
- [x] No subagents, tests, browsers, asset generation, installation, source edits, or Git operations.
- [x] Only the designated report written; report is under 80 lines.