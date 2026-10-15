// Stair arrival regressions: exercise authored routes with real movement and battle settlement.
using System;
using System.Collections.Generic;
using System.IO;
using Abyss.Logic;
using Abyss.Logic.Dungeon;
using Abyss.Logic.Game;

namespace Abyss.LogicTests
{
    public static class DungeonArrivalRepairTests
    {
        static GameDB Db()
        {
            var db = GameDB.Load(t => File.ReadAllText(Path.Combine(Environment.GetEnvironmentVariable("ABYSS_DATA_DIR"), t + ".json")));
            // Isolate stair behavior without changing the shared test database or authored layouts.
            foreach (var floor in db.Floors) { floor.EncounterRate = 0f; floor.MaxEncounterSteps = 0; floor.Foes.Clear(); }
            return db;
        }

        static GameState NewState(GameDB db)
        {
            var state = GameState.NewGame(db, Difficulty.Normal);
            GameFlow.CompletePrologue(state);
            return state;
        }

        static DungeonStepResult StepTo(DungeonRun run, GridPos target)
        {
            for (int d = 0; d < 4; d++)
                if (run.State.Position.Step((Facing)d) == target)
                {
                    run.State.Facing = (Facing)d;
                    return run.Move(RelativeMove.Forward);
                }
            throw new Exception("Expected adjacent destination " + target + " from " + run.State.Position);
        }

        [LogicTest]
        public static void SubwayBossRoundTripReturnsToClearedExit()
        {
            var db = Db(); var state = NewState(db);
            int subway = db.Floors.FindIndex(f => f.Id == "subway_3");
            var boss = new GridPos(6, 9);
            state.FloorIndex = subway; state.Location = GameLocation.Dungeon;
            state.Position = boss; state.Facing = Facing.East;
            var run = new DungeonRun(db, state, subway);
            var fight = run.Interact().Battle;
            Assert.True(fight != null && fight.Kind == BattleKind.Boss, "authored boss starts before descent");
            var outcome = new BattleOutcome { Result = BattleResult.Victory };
            outcome.DefeatedEnemies.AddRange(fight.EnemyGroup);
            run.ResolveBattle(outcome);
            Assert.True(run.Grid.Progress.ClearedBattles.Contains(boss), "victory clears the boss cell");

            var down = StepTo(run, new GridPos(7, 9));
            Assert.True(down.FloorChanged, "descended from subway_3");
            Assert.Equal("gate_e_1", run.Grid.Floor.Id, "next authored floor");
            Assert.Equal(new GridPos(17, 16), state.Position, "descent still uses the entrance");
            var up = StepTo(run, new GridPos(17, 17));

            Assert.True(up.FloorChanged, "ascended through gate_e_1 return stair");
            Assert.Equal("subway_3", run.Grid.Floor.Id, "returned to the boss floor");
            Assert.Equal(boss, state.Position, "ascending lands beside the exit, not at the entrance");
            Assert.Equal(boss, up.To, "step result reports the actual landing");
            Assert.Equal(Facing.West, state.Facing, "arrival faces away from the exit");
            Assert.True(run.Grid.IsWalkable(state.Position.Step(state.Facing)), "arrival permits forward movement");
            Assert.True(run.PendingBattle == null, "arrival does not restart the cleared battle");
            int gold = state.Gold;
            Assert.True(run.Interact().Battle == null, "interacting on the cleared landing does not restart the boss");
            Assert.Equal(gold, state.Gold, "backtracking does not pay boss rewards again");
            Assert.True(StepTo(run, new GridPos(7, 9)).FloorChanged, "immediate descent remains possible");
        }

        [LogicTest]
        public static void AllAuthoredClearedBattleExitsPermitRoundTrip()
        {
            var db = Db(); int bosses = 0, events = 0;
            for (int index = 0; index + 1 < db.Floors.Count; index++)
            {
                var floor = db.Floors[index]; var grid = DungeonGrid.Parse(floor);
                var stair = grid.FindCell('>'); var landing = GridPos.None;
                Facing towardStair = Facing.North;
                if (stair == GridPos.None) continue;
                for (int d = 0; d < 4; d++)
                {
                    var cell = stair.Step((Facing)d); char marker = grid.Cell(cell);
                    if (marker != 'B' && marker != 'E') continue;
                    landing = cell; towardStair = GridPos.Rotate((Facing)d, 2); break;
                }
                if (landing == GridPos.None) continue;

                var state = NewState(db);
                state.Location = GameLocation.Dungeon; state.FloorIndex = index;
                state.Position = landing; state.Facing = towardStair;
                var run = new DungeonRun(db, state, index);
                var fight = run.Interact().Battle;
                Assert.True(fight != null, floor.Id + " exit encounter starts");
                if (fight.Kind == BattleKind.Boss) bosses++; else events++;
                var outcome = new BattleOutcome { Result = BattleResult.Victory };
                outcome.DefeatedEnemies.AddRange(fight.EnemyGroup);
                var resolution = run.ResolveBattle(outcome);
                if (resolution.Ending)
                {
                    Assert.Equal(GameLocation.Town, state.Location, floor.Id + " story ending still returns to town");
                    // Set up the later post-ending visit at this already-cleared exit.
                    run = new DungeonRun(db, state, index, ArrivalMode.Descending);
                    state.Position = landing; state.Facing = towardStair;
                }
                Assert.True(StepTo(run, stair).FloorChanged, floor.Id + " descended");
                Assert.Equal(index + 1, state.FloorIndex, floor.Id + " next floor");
                var up = StepTo(run, run.Grid.FindCell('<'));

                Assert.True(up.FloorChanged, floor.Id + " ascended");
                Assert.Equal(index, state.FloorIndex, floor.Id + " returned floor");
                Assert.Equal(landing, state.Position, floor.Id + " returns to its cleared exit encounter");
                Assert.Equal(landing, up.To, floor.Id + " result position");
                Assert.Equal(GridPos.Rotate(towardStair, 2), state.Facing, floor.Id + " faces away from stairs");
                Assert.True(run.Grid.IsWalkable(landing.Step(state.Facing)), floor.Id + " forward path remains walkable");
                Assert.True(!run.Grid.FoePassable(landing), floor.Id + " landing remains a FOE safe zone");
                int gold = state.Gold;
                var resumed = new DungeonRun(db, state, index);
                Assert.Equal(landing, state.Position, floor.Id + " resume preserves the landing");
                state.Facing = towardStair; // Avoid an unrelated closed door when interacting.
                Assert.True(resumed.Interact().Battle == null, floor.Id + " cleared encounter does not restart");
                Assert.Equal(gold, state.Gold, floor.Id + " no repeated rewards");
                Assert.True(StepTo(resumed, stair).FloorChanged, floor.Id + " can immediately descend again");
            }
            Assert.Equal(12, bosses, "all twelve authored main-route boss exits covered");
            Assert.Equal(2, events, "both red-gate event exits covered");
        }

        static DungeonGrid ExitFixture(char marker, FloorProgress progress)
        {
            return DungeonGrid.Parse(new FloorDef
            {
                Id = "arrival_fixture",
                Rows = new List<string> { "#######", "#S....#", "#####" + marker + "#", "#####>#", "#######" },
            }, progress);
        }

        [LogicTest]
        public static void UnclearedEncountersAreExcludedAndClearedLandingsKeepFoeProtection()
        {
            var landing = new GridPos(5, 2);
            foreach (char marker in new[] { 'B', 'E' })
            {
                var progress = new FloorProgress(); var grid = ExitFixture(marker, progress);
                Assert.Equal(grid.Start, grid.ArrivalCell(-1), marker + " uncleared encounter is not an arrival candidate");
                progress.ClearedBattles.Add(landing);
                Assert.Equal(landing, grid.ArrivalCell(-1), marker + " cleared encounter is a usable landing");
                Assert.Equal(Facing.North, grid.ArrivalDirection(-1), marker + " faces toward the corridor");
                Assert.True(!grid.FoePassable(landing), marker + " still blocks FOE traversal");
                Assert.Equal(-1, grid.PathLength(new GridPos(5, 1), landing), marker + " FOE path cannot reach landing");
                Assert.Equal(grid.Start, grid.ArrivalCell(1), marker + " descending still uses the entrance");
                Assert.Equal(1, progress.ClearedBattles.Count, marker + " arrival leaves completion intact");
                Assert.Equal(0, progress.SpentEvents.Count, marker + " arrival does not spend events");
            }
        }

        [LogicTest]
        public static void SpentEventAllowsArrivalWithoutInventingBattleCompletion()
        {
            var progress = new FloorProgress(); var grid = ExitFixture('E', progress);
            var landing = new GridPos(5, 2);
            progress.SpentEvents.Add(landing);
            Assert.Equal(landing, grid.ArrivalCell(-1), "spent rescue or choice event is a usable landing");
            Assert.Equal(0, progress.ClearedBattles.Count, "arrival does not invent a victory");
            Assert.Equal(1, progress.SpentEvents.Count, "arrival preserves the one-shot event record");
            Assert.True(!grid.FoePassable(landing), "spent event remains excluded from FOE paths");

            var bossGrid = ExitFixture('B', progress);
            Assert.Equal(bossGrid.Start, bossGrid.ArrivalCell(-1), "spent-event record alone cannot clear a boss");
        }

        [LogicTest]
        public static void OrdinaryFloorRemainsPreferredOverClearedEncounter()
        {
            var progress = new FloorProgress(); progress.ClearedBattles.Add(new GridPos(3, 2));
            var grid = DungeonGrid.Parse(new FloorDef
            {
                Id = "arrival_preference",
                Rows = new List<string> { "#######", "#S....#", "###B###", "###>..#", "#######" },
            }, progress);
            Assert.Equal(new GridPos(4, 3), grid.ArrivalCell(-1), "ordinary floor wins over a northward cleared boss");
            Assert.Equal(Facing.East, grid.ArrivalDirection(-1), "ordinary arrival still faces away from stairs");
        }

        [LogicTest]
        public static void ArrivalDoesNotUnlockDoorsOrSpendKeys()
        {
            var progress = new FloorProgress { Keys = 1 }; var grid = ExitFixture('L', progress);
            var door = new GridPos(5, 2);
            Assert.Equal(grid.Start, grid.ArrivalCell(-1), "closed door is not an arrival candidate");
            Assert.Equal(1, progress.Keys, "looking for a landing does not consume a key");
            Assert.True(grid.IsClosedDoor(door), "looking for a landing does not open a door");
            Assert.True(grid.OpenDoor(door), "player can open the door normally");
            Assert.Equal(door, grid.ArrivalCell(-1), "opened door retains its existing arrival behavior");
            Assert.Equal(0, progress.Keys, "arrival consumes no extra key");
        }
    }
}
