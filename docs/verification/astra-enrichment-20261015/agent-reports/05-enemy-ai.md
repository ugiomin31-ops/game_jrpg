# 05 — Enemy AI single-pass audit

- Requested routing: `gpt-6-astra`, HIGH; no workers or reviewers spawned.
- Reference base supplied by requester: `efdc151`; Git was not invoked.
- Audited the current on-disk source, not an independently verified commit snapshot.
- Method: static source/data inspection only; no tests or game execution.
- Verdict: **0 demonstrated issues** within this bounded pass.

## Acceptance checklist and evidence

- [x] Legal skill selection: `Assets/_Game/Scripts/Logic/Battle/EnemyAI.cs:103-124`
  filters the actor's current list by affordability, positive weight, useful support
  targets and charge exclusion. `BattleUnit.cs:186-188` resolves known definitions.
- [x] MP/TP and silence: `EnemyAI.cs:140-144` checks current resources and silence;
  `BattleEngine.cs:443-445` revalidates planned skills, and `:623-628` checks again
  before execution. `:866-874` deducts resources for ordinary casts.
- [x] Multiple action slots: `BattleEngine.cs:302-318` plans without reserving MP,
  but `:380-386` replans unaffordable slots before execution. This is not evidence
  of overspending; no guaranteed repeat-cast budget is assumed.
- [x] Empty candidates: `EnemyAI.cs:56-57` guards when no living opponents remain;
  `:83` attacks when no eligible skills remain; `:90-91` handles an empty caster
  subset; `:287` safely returns null for an empty target pool. Weighted selection
  is reached only with a nonempty option list in the inspected flow.
- [x] Boss behavior: `BattleEngine.cs:1402-1449` applies phase lists/weights and
  action counts; `:443-445` detects removed planned skills. `:305-313` uses the
  stored pending charge for release. `:428-429` marks eligible announcements,
  `:876-881` stores charges, and `:625` makes their release resource-free.
- [x] Authored-data context: read `Assets/_Game/Resources/Data/enemies.json` and
  `skills.json`, including boss/phase skill costs and support loadouts. The
  inspected support loadouts use ally healing; no authored self-cleanse trigger
  was established, so no hypothetical self-cleanse defect is reported.
- [x] Existing focused test sources inspected, not executed:
  `Tools/LogicTests/EnemySkillBudgetTests.cs:8-27` (full-MP authored skill budgets);
  `Tools/LogicTests/EnemyIntentTests.cs:281-295` (silence/MP replan),
  `:442-469` (charge payment, exclusion and release).
- [x] No source edits, Git commands, test runs, browsers, assets or installations.

## Limits

No runtime correctness or test-pass claim is made. No fix or new focused test is
proposed because this pass did not establish an actionable defect. Paths without
an explicit prefix above are under `Assets/_Game/Scripts/Logic/Battle/`.