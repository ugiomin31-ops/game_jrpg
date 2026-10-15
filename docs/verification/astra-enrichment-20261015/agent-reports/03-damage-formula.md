# 03 — DamageFormula audit

- Requested routing: gpt-6-astra / HIGH; no workers or reviewers spawned.
- Reference base supplied by requester: efdc151; Git was not invoked to verify it.
- Method: brief static source audit; no tests, browser, installs, or source edits.
- Findings below demonstrate boundary inputs from source, not observed gameplay failures.
- Scope: DamageFormula, numeric helpers, BattleUnit, healing callers, data definitions, relevant test source.
- Paths below are repository-relative. No independent runtime/model attestation is available.

## 1. [P2] Formula results narrow to int before enforcing an upper bound

Location: `Assets/_Game/Scripts/Logic/Battle/DamageFormula.cs:120`.
Related: same file lines 81, 138–141, 178; `Assets/_Game/Scripts/Logic/Battle/GodotRng.cs:99`.

Trigger: `FixedItemAmount(new ItemDef { Value = 1500000000 }, 1.5, false)`
computes exactly 2250000000 before `RoundI`; this exceeds int.MaxValue.
Likewise an actor with Magic=1500000000 and a Magic-scaled healing skill with
Power=2 produces approximately 2.85–3.15 billion after variance, all out of range.
Those values are accepted by the int stat / float power fields and BattleUnit's
lower-bound-only initialization (BattleUnit.cs:138–141; GameData.cs:122).

Effect: `RoundI` casts the rounded double directly to int; `Math.Max(1, ...)`
afterward cannot implement saturation. Checked conversion throws; unchecked
out-of-range floating conversion is runtime-dependent and can collapse to 1
when the conversion yields a negative value. No exact runtime result is claimed.
Defense/status scaling has the same unsafe conversion (BattleUnit.cs:224,226;
DamageFormula.cs:81), so fixing only the final hit conversion leaves that boundary.

Minimal fix: give `Gd.RoundI` explicit saturating bounds before narrowing, retaining
away-from-zero rounding for in-range inputs and defining a non-finite policy.
Keep the item Power*100 fallback in double through affinity/BREAK multiplication
so early saturation does not distort a later resistance multiplier.
Focused tests proposed, NOT RUN: assert saturation for the item example and the
healing example; assert FinalAmount(2147483648d)==int.MaxValue; verify amplified
defense saturates instead of dropping; preserve 1.5→2 and minimum damage 1.
These are boundary fixtures; this audit does not establish shipped-data reachability.

## 2. [P2] Applying valid healing can overflow HP before the maximum clamp

Location: `Assets/_Game/Scripts/Logic/Battle/BattleUnit.cs:401`.
Call path: `Assets/_Game/Scripts/Logic/Battle/BattleEngine.cs:1236–1238`.

Trigger: target MaxHp=int.MaxValue, Hp=2147483640, then Heal(10).
The target constructor accepts this state (BattleUnit.cs:134–135), and a
Magic=10, Power=1 healing skill produces approximately 10 HP with normal variance.
Effect: the int addition evaluates to 2147483650 before Math.Min; unchecked it
wraps to -2147483646, making a living target dead after healing. Checked it throws.
The returned delta can still be positive after wrapping, allowing a misleading heal event.
This is independent of finding 1: both the incoming heal and pre-heal HP fit int.

Minimal fix: widen the addition, e.g.
`Hp = (int)Math.Min(MaxHp, (long)Hp + Math.Max(amount, 0));`.
Focused test proposed, NOT RUN: with the stated HP, Heal(10) must leave HP at
int.MaxValue and return 7; verify zero/negative healing leaves HP unchanged.

## Acceptance checklist

- [x] Element inheritance/affinity, physical versus magical defense, defense-ignore clamp reviewed.
- [x] Healing formula, healing-received caller, integer conversion and HP application reviewed.
- [x] At most two findings, each with location, trigger, effect, minimal fix, proposed test.
- [x] No additional demonstrated elemental/defense-order issue asserted.
- [x] No tests executed; only this report written; unrelated work preserved.