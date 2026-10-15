# Dungeon arrival and expedition readiness — independent review

**Verdict: approve both logic changes and their focused regression sources. No actionable defect found in the reviewed scope. Parent integrated execution remains pending.**

Requested model/effort: `gpt-6-astra` / `high`; Fast/priority and actual runtime model/effort are not independently attested here. No routing changes, nested agents, Unity/editor, compiler or test execution. Read both implementation notes (`fixes/dungeon-arrival.md`, `fixes/readiness.md`), current production diffs, all six DungeonArrivalRepairTests and all three ReadinessRepairTests, plus relevant callers/contracts. Only this report was written.

## Arrival

- `Assets/_Game/Scripts/Logic/Dungeon/DungeonGrid.cs:74–94`: ordinary floor cells retain first priority. The fallback now accepts a cleared B encounter and spent/cleared E event, after the existing walkability/door check. S, stairs and warp cells remain excluded; no key/progress mutation is introduced. The unchanged `FoePassable` at `:181` still excludes B/E, so the fix does not broaden FOE pathfinding.
- `DungeonRun.cs:120–129` uses the selected position/direction on floor entry; `:229–238` reports the actual new position after stairs. Completion guards retain cleared-encounter behavior; the new eligibility follows `DungeonGrid.IsEventSpent` at `:150` rather than inventing a separate event completion rule.
- `Tools/LogicTests/DungeonArrivalRepairTests.cs:39–129` exercises the actual stair move and victory settlement paths, including the failing subway round trip and all 12 boss/2 event exits. It asserts landing/facing/result position, resume, no repeated battle/gold and immediate re-descent. The story-ending transition is explicitly checked before arranging a later revisit. `:141–198` adds uncleared/spent controls, preserved FOE exclusion, ordinary-cell priority and locked/open door/key behavior. Each data-mutating fixture reloads its own DB (`:13–18`); authored layouts are retained for the route tests.

## Readiness

- `Assets/_Game/Scripts/Logic/Game/ExpeditionReadiness.cs:68–83`: only living active hunters' positive-duration, defined, non-beneficial statuses contribute an advisory line. The classification reuses `GameFlow.IsBeneficial` (`GameFlow.cs:291–306`); the living/positive-duration filter agrees with combat carryover (`PartyStats.cs:333–334`). Names are sorted in a separate list and grouped per hunter. No status, turn, resource, RNG or departure permission is changed.
- `TownServices.cs:597–600` still gates departure solely on unlocked destinations. Existing HP/MP thresholds, KO warnings, objective selection and report formatting remain unchanged by the diff.
- `Tools/LogicTests/ReadinessRepairTests.cs:29–77` uses a real X-cell movement/trap, normal return, advisory evaluation and re-departure/combat-spec carryover. Healthy vitals are asserted so low HP/MP cannot mask the missing-status regression. Serialized state before/after checks guard query purity, and destination/departure assertions guard against a new progression lock. `:81–119` supplies healthy, beneficial/expired and grouped-live-ailment controls. Only the private trap DB changes authored data (`:13–25`); tests using TestMain.DB mutate fresh GameState instances, not the shared DB.

## Execution and limits

The arrival note reports its worker's failing baseline and final 6/6 run. That is attributed worker evidence, not a test result independently reproduced in this review. The readiness note correctly labels its three cases unexecuted. Parent should run DungeonArrivalRepairTests, ReadinessRepairTests and existing ExpeditionReadinessTests serially, then the planned full suite on the integrated current sources.

Arrival fixtures disable random encounters/FOEs and supply victory outcomes; they verify real settlement/transition logic, not combat simulation or a full-floor traversal. FOE protection is checked separately through passability/pathfinding assertions. Unknown/null carried statuses, KO-with-status and empty display-name fallbacks are source-reviewed branches, not additional claimed test coverage. Rendered arrival orientation and the Korean readiness text/layout remain runtime/UI checks; this review does not certify those surfaces.

## Reviewed SHA256 snapshot

| File | SHA256 |
| --- | --- |
| `DungeonGrid.cs` | `5bd9d90e1d970495570507589252abef27e3fcfc0552dc1ba3f84f5227daa905` |
| `ExpeditionReadiness.cs` | `9469b374b0a8e0e0f9cb59409d94045c226bc697521b95c9200f48bbc21a20ae` |
| `DungeonArrivalRepairTests.cs` | `5e26d1bd703e1c8420a6247035b92c0c6fd9eeb000238f49e034614247d1fa41` |
| `ReadinessRepairTests.cs` | `de50b0a013e707bc58ffe6d0dfd02b70570002b30f42353a00e51c6d71770f9f` |
