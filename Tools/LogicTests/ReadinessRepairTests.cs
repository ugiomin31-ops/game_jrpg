using System;
using System.Collections.Generic;
using System.IO;
using System.Linq;
using Abyss.Logic;
using Abyss.Logic.Dungeon;
using Abyss.Logic.Game;

namespace Abyss.LogicTests
{
    public static class ReadinessRepairTests
    {
        static GameDB TrapDatabase()
        {
            // Private fixture: do not mutate the shared database used by the combined runner.
            var db = GameDB.Load(table => File.ReadAllText(Path.Combine(
                Environment.GetEnvironmentVariable("ABYSS_DATA_DIR"), table + ".json")));
            var floor = db.Floors[0];
            floor.Rows = new List<string> { "#####", "#SX.#", "#<.>#", "#####" };
            floor.Foes.Clear();
            floor.Events.Clear();
            floor.EncounterGroups.Clear();
            floor.EncounterRate = 0f;
            floor.MaxEncounterSteps = 0;
            return db;
        }

        [LogicTest]
        public static void PoisonTrapTownReturnWarnsWithoutLockingDepartureOrCleansing()
        {
            var db = TrapDatabase();
            var state = GameState.NewGame(db, Difficulty.Normal);
            GameFlow.CompletePrologue(state);
            state.DungeonRandomState = 1u; // The first trap roll poisons; no random search or retries.
            var run = new DungeonRun(db, state, 0, ArrivalMode.Town);
            var step = run.Move(RelativeMove.Forward);
            Assert.Equal(DungeonEffect.Trap, step.Effect, "step onto the adjacent actual X cell");
            Assert.True(step.Battle == null && step.Trap != null, "trap resolves without a fixture battle");
            Assert.True(step.Trap.Poisoned.Count > 0, "deterministic trap produces carried poison");

            var poison = db.Statuses.Values.Where(s => s.EffectType == StatusEffectType.Poison)
                .OrderBy(s => s.Id, StringComparer.Ordinal).First();
            var carried = state.Party.Where(h => h.Statuses.ContainsKey(poison.Id))
                .ToDictionary(h => h.Id, h => h.Statuses[poison.Id]);
            Assert.True(carried.Count > 0, "poison is present on the campaign hunters");
            foreach (var hero in state.Party)
            {
                var stats = PartyStats.EffectiveStats(db, hero);
                Assert.True((long)hero.Hp * 100 >= (long)stats.MaxHp * 35, "ordinary trap remains above low-HP threshold");
                Assert.True(stats.MaxMp == 0 || (long)hero.Mp * 100 >= (long)stats.MaxMp * 20, "MP does not explain a warning");
            }

            run.ReturnToTown();
            GameFlow.EnterTown(db, state);
            Assert.Equal(GameLocation.Town, state.Location, "normal town return completes");
            var destinations = TownServices.DepartureFloors(db, state).ToArray();
            string before = SaveCodec.Serialize(state);
            var report = ExpeditionReadiness.Evaluate(db, state);
            Assert.Equal(before, SaveCodec.Serialize(state), "readiness changes neither status, resources, flags nor RNG");
            Assert.True(report.HasWarnings, "carried poison cannot receive an all-clear");
            Assert.True(!report.SummaryText.StartsWith("출발 준비 양호", StringComparison.Ordinal), "summary switches to advisory warning");
            Assert.Equal(carried.Count, report.IssueLines.Count, "one issue per poisoned hunter with otherwise healthy vitals");
            foreach (var entry in carried)
                Assert.True(report.IssueLines.Any(line => line.Contains(db.Heroes[entry.Key].DisplayName)
                    && line.Contains(poison.DisplayName)), "warning identifies the hunter and authored poison name");
            Assert.True(destinations.SequenceEqual(TownServices.DepartureFloors(db, state)), "unlocked destinations remain unchanged");
            foreach (int destination in destinations)
                Assert.True(TownServices.Depart(db, state, destination).Success, "warning does not lock an unlocked departure");

            var departed = new DungeonRun(db, state, 0, ArrivalMode.Town);
            Assert.Equal(GameLocation.Dungeon, departed.State.Location, "poisoned party really departs again");
            foreach (var entry in carried)
            {
                Assert.Equal(entry.Value, state.Hero(entry.Key).Statuses[poison.Id], "departure does not cleanse poison");
                Assert.Equal(entry.Value, PartyStats.BuildCombatSpec(db, state, entry.Key).Statuses[poison.Id],
                    "the warned status is carried into the next combat specification");
            }
        }

        [LogicTest]
        public static void HealthyTownPartyStillReceivesAllClearAndDeparts()
        {
            var db = TestMain.DB;
            var state = GameState.NewGame(db, Difficulty.Normal);
            GameFlow.CompletePrologue(state);
            GameFlow.EnterTown(db, state);
            string before = SaveCodec.Serialize(state);
            var report = ExpeditionReadiness.Evaluate(db, state);
            Assert.True(!report.HasWarnings && report.IssueLines.Count == 0, "healthy party has no advisory issues");
            Assert.True(report.SummaryText.StartsWith("출발 준비 양호", StringComparison.Ordinal), "healthy all-clear is preserved");
            Assert.Equal(before, SaveCodec.Serialize(state), "healthy query is read-only");
            Assert.True(TownServices.Depart(db, state, 0).Success, "healthy party retains its unlocked departure");
            var departed = new DungeonRun(db, state, 0, ArrivalMode.Town);
            Assert.Equal(GameLocation.Dungeon, departed.State.Location, "healthy departure still enters the dungeon");
        }

        [LogicTest]
        public static void BenefitsAndExpiredStatusesStayClearWhileLiveAilmentsAreGrouped()
        {
            var db = TestMain.DB;
            var state = GameState.NewGame(db, Difficulty.Normal);
            var hero = state.Party[0];
            hero.Statuses["attack_up"] = 3;
            hero.Statuses["poison"] = 0;
            hero.Statuses["burn"] = -1;
            var clear = ExpeditionReadiness.Evaluate(db, state);
            Assert.True(!clear.HasWarnings, "a benefit and expired ailments are not harmful carried conditions");

            hero.Statuses["poison"] = 2;
            hero.Statuses["burn"] = 1;
            string before = SaveCodec.Serialize(state);
            var warning = ExpeditionReadiness.Evaluate(db, state);
            Assert.Equal(1, warning.IssueLines.Count, "multiple ailments on one hunter use one compact issue line");
            string issue = warning.IssueLines[0];
            Assert.True(issue.Contains(db.Heroes[hero.Id].DisplayName), "affected hunter is named");
            Assert.True(issue.Contains(db.Statuses["poison"].DisplayName) && issue.Contains(db.Statuses["burn"].DisplayName),
                "both live harmful conditions are identified");
            Assert.True(!issue.Contains(db.Statuses["attack_up"].DisplayName), "beneficial condition is omitted");
            Assert.Equal(before, SaveCodec.Serialize(state), "grouping does not modify or expire statuses");
        }
    }
}
