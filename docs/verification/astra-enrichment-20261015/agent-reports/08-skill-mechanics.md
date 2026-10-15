# 08 — Skill mechanics bounded audit

- Requested model: `gpt-6-astra`; requested reasoning effort: `high`.
- Requested service priority: Fast/priority. Actual model, effort and service tier are not independently attested by available session metadata; this report does not claim verified priority routing. No model/configuration changes or agents were invoked.
- Verified branch: `codex/astra-enrichment-20261015`; HEAD short ID: `efdc151`, consistent with the supplied base `efdc1517`. Reviewed current working files, not an independently pristine commit snapshot.
- Scope: authored skill expansion data, loader bindings, execute multipliers, break shields, defensive barriers, damage-triggered self buffs and target resolution.
- Method: focused static reads and JSON inspection only. No tests, builds, Unity/editor/browser actions, network requests, secret reads or source changes.

## Result

**0 concrete reachable findings established in this bounded pass.** No speculative extreme-input issue is reported. This is not runtime verification or an exhaustive correctness certification.

## Source evidence

All paths are repository-relative; line numbers refer to the inspected working files.

- Data binding: `Assets/_Game/Scripts/Logic/Data/GameData.cs:134-140` declares ExecuteBelow, ExecuteMult, BreakPower and SelfStatus. The snake-case resolver at `:396-400` and skill/status deserialization at `:415-416` connect the authored JSON keys to those fields.
- Authored expansion data: `Assets/_Game/Resources/Data/skills.json:6478-6985` contains four shield-crusher skills, six execute skills and four self-buff damage skills. All 14 target opponents; execute skills use a 30% HP threshold and 1.5x or 1.6x multiplier. `sk_m_mana_surge` is random-target, four-hit; the other self buffs use single targets. Representative playable learnset references exist in `Assets/_Game/Resources/Data/heroes.json:63`, `:75`, `:91`, `:246`, `:556`.
- Execute: `Assets/_Game/Scripts/Logic/Battle/DamageFormula.cs:103,115-117` applies the multiplier inclusively at the threshold using current target HP. `Assets/_Game/Scripts/Logic/Battle/BattleEngine.cs:1087-1090` rolls each surviving hit separately, so subsequent hits observe updated HP.
- Break shields: `Assets/_Game/Scripts/Logic/Battle/BattleEngine.cs:1091-1099` skips missed hits and scopes BreakPower to the damage hit with a finally reset. `:1168-1185` adds the weakness point and opponent-only BreakPower, clamps shield at zero, and breaks/cancels charge only for a living, shield-bearing, unbroken target. Absorbed weakness hits are explicitly intended to count (`:1172`); their shield interaction is not reported as a defect.
- Self buffs: `Assets/_Game/Scripts/Logic/Battle/BattleEngine.cs:1096-1113` tracks landed hits independently of target survival, applies the self status once after the damage action, and requires a living caster. Thus killing the target still grants the buff; an entirely missed action does not. This matches the declared contract in `GameData.cs:139`.
- Defensive barrier: `Assets/_Game/Resources/Data/skills.json:6753` refers to `barrier`; `Assets/_Game/Resources/Data/statuses.json:51-63` defines 20% max-HP absorption for three turns. `Assets/_Game/Scripts/Logic/Battle/BattleStatus.cs:98-102,133-137` and `Assets/_Game/Scripts/Logic/Battle/BattleUnit.cs:424` bind its pool to the holder's max HP. `BattleUnit.cs:343-363,387-392` consumes and removes exhausted barriers. Same-ID refresh uses the larger remaining/new pool rather than adding pools (`BattleStatus.cs:152`).
- Target edge cases: `Assets/_Game/Scripts/Logic/Battle/BattleEngine.cs:675-735` uses living offensive pools and rejects illegal single targets or empty pools before execution. `:1075-1085` retargets random damage picks when an earlier hit killed the selected opponent, and skips them if no living opponent remains. Authored damage skills inspected contain no allied target type; no hypothetical random-ally damage issue is asserted.

## Limits and acceptance

- [x] Execute, shields, self buffs and target edge cases inspected against authored data.
- [x] Existing reports 01-06 consulted to avoid duplicate findings; report 07 was not present at inspection.
- [x] Existing test sources were read only; no test pass or runtime reproduction is claimed.
- [x] Requested model/effort and requested versus verified priority distinguished.
- [x] Only the assigned report written; integration and any subsequent changes belong to the main coordinator.
