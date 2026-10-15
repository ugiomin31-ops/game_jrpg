# battle-ui-information

Implemented under `plan/2026-10-15-astra-enrichment.md`; reviewed `design.md` and reports 40, 43, and 19 finding 2.
Requested model/effort: `gpt-6-astra` / `high`; actual model/effort and Fast/priority tier are not independently attested by these tools. No routing/configuration changes or nested agents.

## Exact source changes

- `Assets/_Game/Scripts/UI/Battle/BattleHUD.Menu.cs:59-66,120,161-164`: carry the existing skill-menu MP/TP cost and element into every target choice's first description line, including single ally/enemy, self and group confirmation. Free skills explicitly show `소모 없음`. The action name remains in the existing header; damage/healing estimates remain after the cost/element and in target rows/marks. No layout, input or submission changes.
- `Assets/_Game/Scripts/UI/Screens/GameUI.Settings.cs:36-42`: after applying preferences, update the existing battle HUD speed label from the same preference used by battle pacing. Resolve the HUD on the battle component's GameObject, where `BattleView.Initialize` creates it. No active battle is a normal no-op.
- `Assets/_Game/Scripts/UI/Screens/GameUI.Party.cs:283-285,311-312`: include EXP/gold bonus changes in the equipment verdict and show both before/after percentages and percentage-point deltas. Gold is labeled as a bonus with the existing party cap; this does not recalculate rewards or claim an uncapped party payout.

## Verification and regression handoff

- `git diff --check --` for the three files: passed. Read-only diff review confirmed 22 insertions / 5 deletions and no layout, global-style, engine, asset or unrelated UI edits.
- Tests/builds were **not run**, per assignment. No automated regression source was added: these are display/synchronization changes in Unity UI, which the existing `Tools/logic_test.py` harness does not compile; expanding that harness or adding a Unity test assembly is outside this file scope. Do not treat logic-suite success as verification of these UI changes.
- Parent focused checks after source recompilation:
  1. Select learned 파이어볼 with sufficient MP: target footer begins with MP 6 and 화염; changing enemy focus preserves both. A first target click previews, the second commits once. Cancel still spends nothing. Repeat with an allied healing skill, a group skill, a TP ultimate, and a free skill; switching back to attack/item must not retain skill cost/element.
  2. During idle manual combat at 1x, pause → settings → speed 1.5x → resume: HUD says `속도 1.5x`; clicking the HUD then shows 2x. Check wrap to 1x and changing settings outside battle without a HUD.
  3. Unequip `acc_exp_charm`: verdict `능력 하락 ↓`, EXP bonus 30% → 0% (-30%p). Unequip `acc_gold_charm`: gold bonus 25% → 0% (-25%p). Equipping reverses the verdict; swapping the two charms reports `장단점 교환`; comparing the same gear reports `동일 능력`. Cancel must leave equipment/reward bonuses unchanged.

## Limits and scope

- No rendered UI or runtime timing was inspected. Parent still owns serial source compilation, focused runtime checks, visual text-fit checks and independent review. The bounded description can still ellipsize later estimate/detail text; cost/element are deliberately first and layout is unchanged.
- All three owned source files had no pre-existing diff before this edit. Existing/concurrent changes elsewhere were preserved. No reset, revert, commit, tests, builds, Unity/browser actions, installs or configuration changes. `DungeonMapGraphic` and `GameUI.Town` were not edited.
- Deliverables for this slice: three source fixes plus this note. Integration and acceptance remain with the main coordinator.
