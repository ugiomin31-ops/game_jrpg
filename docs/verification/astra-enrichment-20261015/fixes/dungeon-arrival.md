# Dungeon arrival repair — audit 22

Requested model/effort: `gpt-6-astra` / `high`; requested service tier: Fast/priority. Runtime model/effort and service tier were not independently exposed or verified. No routing/configuration changes were made.

## Change

Ascending from the next floor now lands beside the previous floor's exit on its cleared boss/event cell instead of falling back to the entrance. The reproduced route was `subway_3 > gate_e_1 > subway_3`: expected `(6,9)`, previously received `(6,1)`.

Files written:

- `Assets/_Game/Scripts/Logic/Dungeon/DungeonGrid.cs:82`: use a player-arrival predicate. At line 88, the new predicate accepts cleared `B` cells and cleared/spent `E` cells while retaining walkability, door and special-cell restrictions. Ordinary `.` cells retain priority. FOE passability/pathfinding is unchanged.
- `Tools/LogicTests/DungeonArrivalRepairTests.cs`: six regression tests; no harness changes.
- This implementation note.

`DungeonGrid.cs` and `DungeonRun.cs` had no existing scoped diff before work. No overlapping writer was observed; `DungeonRun.cs` did not need modification. Existing/concurrent work was preserved.

## Executed verification

Commands ran serially from `C:\Users\User\Desktop\GAME_JRPG\handoff-verify-20261015` using the existing standalone runner, without launching Unity:

1. Before the repair: `python Tools/logic_test.py DungeonArrivalRepairTests.SubwayBossRoundTripReturnsToClearedExit` — **0/1**, exit **1**. Actual failure: `ascending lands beside the exit, not at the entrance (expected (6,9), got (6,1))`.
2. First repaired class run: `python Tools/logic_test.py DungeonArrivalRepairTests` — **5/6**, exit **1**. The authored-route fixture stopped at `gate_s_3 descended` because its first boss victory correctly triggers the story ending and returns to town. Corrected only the fixture to assert that transition and set up the later post-ending visit at the cleared exit.
3. Narrow fixture verification: `python Tools/logic_test.py DungeonArrivalRepairTests.AllAuthoredClearedBattleExitsPermitRoundTrip` — **1/1**, exit **0**.
4. Final fresh compilation and execution: `python Tools/logic_test.py DungeonArrivalRepairTests` — **6/6**, exit **0**.
5. `git diff --check -- Assets/_Game/Scripts/Logic/Dungeon/DungeonGrid.cs` — clean.

Coverage: actual stair movement and victory settlement across all **12 boss exits and 2 red-gate event exits**; correct landing/facing/result position; resume and immediate re-descent; no repeated fixed battle or gold payout; uncleared encounters excluded; spent noncombat events accepted without inventing a victory; ordinary-floor priority; locked/open doors and key preservation; cleared/spent encounter cells remain excluded from FOE traversal.

## Limits

Tests use fresh in-memory databases, preserve authored layouts, disable random encounters/FOEs in those fixtures, and supply victory outcomes to real settlement. They start at exit encounters rather than traversing entire floors; the ending-floor case explicitly sets up a later revisit. FOE restrictions are additionally checked with grid passability/pathfinding assertions. This is focused engine-free proof, not full combat simulation or rendered gameplay acceptance. No full suite, Unity/editor, WebGL, browser, network, nested agents, resets or commits were run. Parent owns integrated verification and acceptance.
