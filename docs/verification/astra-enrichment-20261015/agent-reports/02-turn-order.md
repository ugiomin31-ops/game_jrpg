# 02 — Turn order audit

- Requested model/effort: `gpt-6-astra` / `high`; no workers or reviewers spawned.
- Runtime model/effort cannot be independently attested from the available session metadata.
- Reference base supplied by parent: `efdc151`; inspected current source, without Git commands.
- Method: bounded static source trace; no tests executed and no source modified.
- Result: one demonstrated event/state-ordering issue; runtime reproduction remains unverified.

## [P2] A broken enemy can recover its shield after dying to its turn-end damage

**Location:** `Assets/_Game/Scripts/Logic/Battle/BattleEngine.cs:512-517`.

**Trigger:** An enemy enters its skipped BREAK turn with lethal poison/burn damage pending
(for example, HP 1, positive poison tick, `Broken == true`, shield 0, max shield > 0).

**Evidence:**
- `BattleEngine.cs:343-348` routes the broken actor to `FinishTurn(actor, true)`.
- `BattleEngine.cs:508` applies turn-end status damage before attempting BREAK recovery.
- `BattleEngine.cs:545-548,579-590` delivers the lethal tick and calls `OnUnitDown`.
- `BattleEngine.cs:1205-1222` clears statuses/intents and emits `UnitDownEvent`, but leaves `Broken` set.
- `BattleEngine.cs:512-517` checks only `recoverBreak && actor.Broken`, refills the dead
  actor's shield, and emits `RecoverEvent` plus `ShieldChangeEvent` after `UnitDownEvent`.
- `BattleEngine.cs:520-521` then emits the dead actor's full-shield snapshot and checks outcome.
- `Assets/_Game/Scripts/Runtime/Battle/BattleView.cs:406-408` consumes the recovery without
  an alive check and copies that full shield into presentation state.

**Effect:** A defeated unit is reported as recovering from BREAK and gains a full shield
after its death event, including immediately before `BattleEndEvent` if it was the last enemy.
This is a contradictory event/state transition; it does not revive HP or grant another action.

**Minimal fix:** Require `actor.IsAlive` in the BREAK recovery condition at line 512.
Do not move outcome evaluation ahead of normal turn-end bookkeeping.

**Focused test (proposed, not run):** Use the existing logic-test fixture with a fast hero
and one slower broken, poisoned enemy at HP 1. Submit Guard to advance into its skipped turn.
Assert one `UnitDownEvent`, no subsequent `RecoverEvent` or shield refill for that enemy,
a dead `TurnEndEvent` snapshot with shield 0, and one final victory `BattleEndEvent`.
Add a surviving-poison control asserting normal BREAK recovery still refills the shield.

## Acceptance checklist

- [x] Reviewed speed/tie ordering, dead queue entries, and revival/next-round participation.
- [x] Reviewed stun/BREAK skips, intent clearing, charge cancellation, and enemy action slots.
- [x] Reviewed bleed-before-action, turn-end damage, and outcome/event ordering.
- [x] At most two evidence-backed findings; no speculative second finding added.
- [x] Only this report written; no tests, browsers, installs, assets, source edits, or Git operations.
