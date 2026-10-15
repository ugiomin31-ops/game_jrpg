# 06 — Auto battle focused audit

- Repository: `handoff-verify-20261015`; branch `codex/astra-enrichment-20261015`; HEAD/base `efdc151`.
- Requested routing: `gpt-6-astra`, `high`; actual runtime model/effort not independently verifiable from available evidence.
- No subagents, model switching, source edits, git mutations, browser actions, installs, or broad tests.
- Existing parent changes, including `BattleEngine.cs`, were preserved; reviewed current working-tree text.
- Verdict: **No demonstrated finding** within this bounded audit. This is not exhaustive correctness certification.

## Decision paths inspected

All source paths below are relative to this repository.

- `Assets/_Game/Scripts/Logic/Battle/BattleEngine.Commands.cs:356-384`: null/dead/no-enemy guards; emergency healing before resurrection; usable revival selection and fallen healer priority.
- `Assets/_Game/Scripts/Logic/Battle/BattleEngine.Commands.cs:386-424`: charge interruption, guarding, preemptive healing, cleanse, then ordinary healing.
- `Assets/_Game/Scripts/Logic/Battle/BattleEngine.Commands.cs:681-712`: injury thresholds, valid heal targets, missing-HP utility, group healing and TP conservation.
- `Assets/_Game/Scripts/Logic/Battle/BattleEngine.Commands.cs:426-467`: MP reserve, attack/skill scoring, ultimate overkill avoidance, and setup selection.
- `Assets/_Game/Scripts/Logic/Battle/BattleEngine.Commands.cs:761-820`: legal single-target scoring, random/all-enemy aggregation, known weakness and execute estimates.

## Invalid targets and repeated actions

- `Assets/_Game/Scripts/Logic/Battle/BattleEngine.Commands.cs:11-33`: usability excludes silence, insufficient MP/TP and missing targets.
- `Assets/_Game/Scripts/Logic/Battle/BattleEngine.Commands.cs:79-126`: revival uses fallen allies; healing uses living allies; single offense respects provoke.
- `Assets/_Game/Scripts/Logic/Battle/BattleEngine.cs:230-255`: rejected commands return before execution; accepted commands finish the turn and resume progression.
- `Assets/_Game/Scripts/Logic/Battle/BattleEngine.cs:613-657` and `:666-738`: actor/resources and target membership are revalidated before execution.
- `Assets/_Game/Scripts/Runtime/Battle/BattleView.cs:222-247`: one auto submission per coroutine, followed by replay and another decision only while awaiting input.
- `Assets/_Game/Scripts/Runtime/Battle/BattleView.cs:490-492`: rejection disables AUTO, preventing an unchanged rejected suggestion from being retried indefinitely.
- `Assets/_Game/Scripts/Logic/Battle/BattleEngine.cs:278-280`: synchronous engine progression stops on command wait or battle end; no reachable infinite loop established in reviewed paths.
- Parsed shipped `Assets/_Game/Resources/Data/skills.json`: heal/revive skills use allied single/all scopes; no hypothetical random-heal or self-revive defect reported.

## Focused verification performed

Existing `Temp/LogicTests/LogicTests.exe` executed using installed Unity Mono, with `ABYSS_DATA_DIR` set to this checkout's data directory:

- Filter `QualityUpgradeTests.Auto`: **10/10 passed**, exit 0.
- Filter `AutoMechanicRegressionTests`: **11/11 passed**, exit 0.
- Covers critical healing before revival, healer revival priority, group revival/healing, self-heal targeting, ultimate conservation, buff refresh avoidance, query purity, charge breaks and execute decisions.
- No rebuild performed: the runner writes additional files, prohibited by this task. Binary/source correspondence was not established; these passes corroborate existing binary behavior only.
- Runtime browser/UI behavior was inspected in source, not exercised.

## Acceptance

- [x] Resurrection/healing/offense decisions located and reviewed.
- [x] Target validation and repeat paths inspected; no invented defect or repair proposed.
- [x] Focused checks completed; limitations disclosed.
- [x] Only this report written by this audit; pre-existing work preserved.