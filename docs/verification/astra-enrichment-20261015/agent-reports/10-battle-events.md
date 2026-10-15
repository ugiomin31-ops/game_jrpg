# 10 — BattleEvents and event consumption

- Requested model: `gpt-6-astra`; requested reasoning effort: `high`.
- Requested priority: Fast/priority. Actual model, effort, and service/priority tier are **not independently verified** by available session metadata; no routing/configuration change or nested agent was used.
- Verified branch: `codex/astra-enrichment-20261015`; HEAD/base: `efdc1517f48ac8887e1fcf6843b6df44df6ebc3c`.
- Reviewed current working-tree source, including the existing modified BattleEngine.cs; no source changes made.
- Method: bounded static source/data inspection only. No tests, builds, Unity/editor/browser actions, network requests, asset generation, or secret reads.
- Reports 01–06 consulted for duplicate avoidance; report 07 was absent when checked.
- Result: **1 concrete source-supported finding**. Reproduction below is a source-derived scenario, not an executed runtime reproduction.

## P2 — Random-hit retargeting leaves the replay's action target snapshot stale

**Location:** `Assets/_Game/Scripts/Logic/Battle/BattleEngine.cs:1082`; snapshot creation at `:986`.

**Reachable reproduction:** Use the shipped Elementalist skill `jb_el_tri_burst` against two living enemies A and B, with A already close to defeat. In a legal random draw where the six initial picks are A, the first hit kills A and subsequent picks redirect to B while B remains alive. This uses ordinary combat HP and the skill's existing six-hit behavior, not extreme input values.

**Source chain:**

- `Assets/_Game/Resources/Data/skills.json:656-675` defines Tri Burst with random scope 2, six hits, and presentation `pr_m_prism`; `Assets/_Game/Resources/Data/jobs.json:290` makes it a job skill.
- `Assets/_Game/Scripts/Logic/Battle/BattleEngine.cs:703-711` samples targets with replacement before resolution. `:857` emits the start event before resolving damage; `:986` copies those initial IDs into a separate list.
- `BattleEngine.cs:1075-1082` replaces a dead random target with a living opponent and updates only `action.TargetIds[pick]`. Subsequent `DamageEvent.TargetId` values use the replacement (`:1098`, `:1155`), while the previously copied `ActionStartEvent.TargetIds` remains unchanged.
- `Assets/_Game/Scripts/Runtime/Battle/BattleView.cs:280-284,791-792` uses the stale start-event targets for release camera framing. `:806-809` places the area effect using that same list; `:953-962` computes its center from the listed units' home positions.
- `Assets/_Game/Resources/Data/presentation.json:2240-2244` gives this skill the `prism_ray` area effect. In the scenario above its center remains A's home, although five damage events target B.

**Impact:** Random multi-hit actions can frame and center their main visual effect on the original victim while dealing most hits to an omitted survivor. Damage/HP events themselves remain correct. The start-event contract describing resolved targets (`BattleEvents.cs:76`) is also violated. Exact screen appearance was not observed in this audit.

## Acceptance checklist / other inspected paths

- [x] Hit/miss: `BattleEngine.cs:1087-1102,1126-1130` emits a miss instead of damage and shares a per-target hit index; dead targets stop receiving ordinary follow-up hits.
- [x] Multi-target: traced random picks, death retargeting, target snapshots, group-wave handling, and area-effect consumers; finding above recorded.
- [x] Cancellation: `BattleHUD.Menu.cs:280-285` clears targeting preview without submitting; `BattleView.cs:224-227` checks cancelled AUTO before submission. Lethal action bleed returns before ActionStart (`BattleEngine.cs:855-857`).
- [x] Duplicate feedback: `BattleEngine.cs:849-852,1149,1157` resets and gates effectiveness feedback per action/target; `BattleView.cs:194-196` blocks replay-time duplicate submission. Charge cancellation clears pending state before emitting (`BattleEngine.cs:482-486`), while BREAK suppresses its separate popup for a pending charge (`BattleView.cs:397-399,526-535`). No additional concrete duplicate-feedback defect established.
- [x] Event batches use fresh lists and monotonically assigned sequence values (`BattleEngine.cs:258-270`); replay consumes each batch entry once (`BattleView.cs:229-239`).
- [x] Only this assigned report written; no game fixes. Integration and any runtime verification remain with the main coordinator.
