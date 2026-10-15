# 01-command-validation — bounded source audit
- Requested model/effort: gpt-6-astra / HIGH; no workers or model substitutions invoked.
- Runtime model/effort identity is not exposed by the available session metadata; requested routing is not independently attested.
- Base verified: efdc1517f48ac8887e1fcf6843b6df44df6ebc3c.
- Scope: command-menu validation and the directly connected command submission/resolution path.
- Method: static source audit only. No tests executed, UI/browser opened, packages installed, or source/Git mutations performed.
- Verdict: **No concrete actionable bug established within this bounded pass.**
- Paths below are repository-relative; line numbers refer to the inspected checkout.

## Actual call paths
- Manual input: Assets/_Game/Scripts/Runtime/Battle/BattleView.cs:192-196 calls Engine.Submit.
- AUTO input: Assets/_Game/Scripts/Runtime/Battle/BattleView.cs:222-227 calls SuggestCommand then Submit.
- Assets/_Game/Scripts/Logic/Battle/BattleEngine.cs:230-255 checks input state and actor, converts the command, calls Prepare, returns on rejection, then executes and advances.
- Assets/_Game/Scripts/Logic/Battle/BattleEngine.Commands.cs:11-51 supplies menu availability; :79-126 supplies target candidates. Neither is the authoritative execution gate.

## Verified source properties
- Unknown command kinds become an invalid ActionKind at BattleEngine.cs:595-605 and are rejected at :652-653.
- Unknown/unlearned skills, silence on MP-cost skills, and insufficient MP/TP reject at BattleEngine.cs:622-628.
- Unknown/empty inventory, unusable items and forbidden smoke escape reject at BattleEngine.cs:630-635.
- Explicit single targets must belong to the correct team and eligible living/fallen pool at BattleEngine.cs:675-679, :717-724.
- Revive uses fallen allies; ordinary ally actions use living allies. Self-target mismatches reject at BattleEngine.cs:684-686.
- An omitted single target intentionally picks the first valid unit at BattleEngine.cs:726; BattleCommand.cs:27 documents that behavior.
- Provoke can redirect a legal offensive single target at BattleEngine.cs:727-730; Commands.cs:120-122 exposes the forced target in the menu.
- Empty target pools reject at BattleEngine.cs:735, before Execute.
- MP/TP deduction occurs in Execute at BattleEngine.cs:866-874, after Prepare succeeds.
- Item accounting occurs at BattleEngine.cs:897-898 and :1546-1550, also after Prepare.
- Action bleed is inside Execute at BattleEngine.cs:855, :1027-1034; rejected commands do not reach it.
- Random target selection consumes RNG at BattleEngine.cs:708-711 only with a nonempty pool; the remaining checked path then accepts. An empty pool rejects without a random draw.
- Rejection emits an event and advances the event sequence (BattleEngine.cs:267-276). This observable bookkeeping is distinct from combat-resource or turn mutation and is not classified as a bug.

## Existing regression evidence and limits
- Tools/LogicTests/BattleRegressionTests.cs:43-57 already checks unknown-kind rejection, a sole rejection event, the same active actor, unchanged enemy HP and unchanged RNG.
- This is source evidence of assertions, not a claim that tests passed during this audit.
- No runtime reproduction was executed; concurrent source changes and all authored-data combinations were not exhaustively audited.
- Optional focused follow-up: extend the existing refusal fixture with unknown skill/item, insufficient MP/TP, wrong-side/dead targets and revive-on-living cases; compare actor HP/MP/TP, inventory, active actor, round and RNG with a same-seed control.
- That follow-up is a verification suggestion, not an asserted defect or a second finding.

## Acceptance
- [x] Traced actual callers and authoritative validation.
- [x] Inspected target legality, resource spending and mutation order.
- [x] Recorded zero findings rather than speculative issues.
- [x] Recorded model-attestation and runtime-verification uncertainty.
- [x] Only this designated report was written; report is under 100 lines.