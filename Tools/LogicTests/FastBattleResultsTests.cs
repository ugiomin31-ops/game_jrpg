using System;
using System.Collections.Generic;
using System.Linq;
using Newtonsoft.Json;
using Abyss.Logic;
using Abyss.Logic.Game;

namespace Abyss.LogicTests
{
    public static class FastBattleResultsTests
    {
        static GameDB DB => TestMain.DB;
        static BattleSetup Setup() => new BattleSetup
        {
            Kind = BattleKind.Random, EnemyGroup = new List<string> { "slime" },
            Party = new List<HeroCombatSpec> { new HeroCombatSpec { HeroId = "h_seoa" } }
        };
        static BattleOutcome Win() => new BattleOutcome { Result = BattleResult.Victory, SeenEnemies = new List<string> { "slime" }, DefeatedEnemies = new List<string> { "slime" } };
        static BattleReport Report() => new BattleReport { Result = BattleResult.Victory, Experience = 10, Gold = 20 };
        static bool Fast(BattleSetup setup, BattleOutcome outcome, BattleReport report) => PartyStats.CanUseFastResults(DB, setup, outcome, report);

        [LogicTest] public static void OrdinaryVictoryAndProgressAreFast()
        {
            var setup = Setup(); var win = Win(); var report = Report();
            Assert.True(Fast(setup, win, report), "ordinary random victory");
            report.NewWeaknesses.Add("slime:4");
            report.QuestUpdates.Add(new QuestUpdate { QuestId = "fixture", OldProgress = 1, NewProgress = 2 });
            Assert.True(Fast(setup, win, report), "weakness and quest progress add toast line, not full-screen gate");
            report.NewBestiaryEntries.Add("slime");
            Assert.True(!Fast(setup, win, report), "new bestiary uses full screen");
        }
        [LogicTest] public static void NonRandomAndNonVictoryAlwaysUseFullResults()
        {
            foreach (BattleKind kind in Enum.GetValues(typeof(BattleKind)))
            {
                var setup = Setup(); setup.Kind = kind;
                Assert.Equal(kind == BattleKind.Random, Fast(setup, Win(), Report()), "kind " + kind);
            }
            foreach (BattleResult result in Enum.GetValues(typeof(BattleResult)))
            {
                var win = Win(); var report = Report(); win.Result = report.Result = result;
                Assert.Equal(result == BattleResult.Victory, Fast(Setup(), win, report), "result " + result);
            }
            var mismatch = Report(); mismatch.Result = BattleResult.Defeat;
            Assert.True(!Fast(Setup(), Win(), mismatch), "mismatched report fails closed");
        }
        [LogicTest] public static void BossAndFoeDefinitionsCannotMasqueradeAsRandom()
        {
            var dangerous = DB.Enemies.Values.Where(e => e.IsBoss || e.Rank == 1).ToList();
            Assert.True(dangerous.Any(e => e.IsBoss) && dangerous.Any(e => e.Rank == 1), "boss and FOE fixtures exist");
            foreach (var enemy in dangerous)
            {
                var setup = Setup(); setup.EnemyGroup[0] = enemy.Id;
                Assert.True(!Fast(setup, Win(), Report()), "initial dangerous " + enemy.Id);
                var win = Win(); win.SeenEnemies.Add(enemy.Id);
                Assert.True(!Fast(Setup(), win, Report()), "seen/summoned dangerous " + enemy.Id);
                win = Win(); win.DefeatedEnemies.Add(enemy.Id);
                Assert.True(!Fast(Setup(), win, Report()), "defeated dangerous " + enemy.Id);
            }
        }
        [LogicTest] public static void RankTwoBossIsExcludedEvenWithoutBossFlag()
        {
            // BattleUnit recognizes Rank=2 as boss too. Clone the DB row locally; never mutate the shared test DB.
            var copy = new GameDB();
            var enemy = JsonConvert.DeserializeObject<EnemyDef>(JsonConvert.SerializeObject(DB.Enemies["slime"]));
            enemy.IsBoss = false; enemy.Rank = 2; copy.Enemies["slime"] = enemy;
            Assert.True(!PartyStats.CanUseFastResults(copy, Setup(), Win(), Report()), "actual enemy rank excludes boss with missing flag");
        }
        [LogicTest] public static void ActiveLevelUpsGateButReserveLevelUpsDoNot()
        {
            var report = Report();
            report.LevelUps.Add(new LevelUpReport { HeroId = "h_jun", OldLevel = 1, NewLevel = 2 });
            Assert.True(Fast(Setup(), Win(), report), "reserve ignored");
            report.LevelUps.Add(new LevelUpReport { HeroId = "h_seoa", OldLevel = 1, NewLevel = 1 });
            Assert.True(Fast(Setup(), Win(), report), "no actual increase ignored");
            report.LevelUps.Add(new LevelUpReport { HeroId = "h_seoa", OldLevel = 1, NewLevel = 2 });
            Assert.True(!Fast(Setup(), Win(), report), "active increase uses full screen");
            var setup = Setup(); setup.Party.Add(new HeroCombatSpec { HeroId = "h_jun", Hp = 0 });
            report.LevelUps.RemoveAll(l => l.HeroId == "h_seoa");
            Assert.True(!Fast(setup, Win(), report), "active scope includes KO party member if report contains level-up");
        }
        [LogicTest] public static void EveryItemAndEquipmentRarityUsesPositiveQuantityOnly()
        {
            foreach (var item in DB.Items.Values) CheckDrop(item.Id, item.Rarity);
            foreach (var gear in DB.Equipment.Values) CheckDrop(gear.Id, gear.Rarity);
        }
        static void CheckDrop(string id, int rarity)
        {
            foreach (int quantity in new[] { -1, 0, 1, 3 })
            {
                var report = Report(); report.Drops[id] = quantity;
                Assert.Equal(quantity <= 0 || rarity < 1, Fast(Setup(), Win(), report), "report drop " + id + " x" + quantity + " rarity " + rarity);
                var win = Win(); win.Drops[id] = quantity;
                Assert.Equal(quantity <= 0 || rarity < 1, Fast(Setup(), win, Report()), "outcome drop " + id + " x" + quantity + " rarity " + rarity);
            }
        }
        [LogicTest] public static void UnknownPositiveDropsAndEnemiesFailClosed()
        {
            foreach (int count in new[] { -1, 0, 1 })
            {
                var report = Report(); report.Drops["not_a_content_id"] = count;
                Assert.Equal(count <= 0, Fast(Setup(), Win(), report), "unknown quantity " + count);
                var win = Win(); win.Drops["not_a_content_id"] = count;
                Assert.Equal(count <= 0, Fast(Setup(), win, Report()), "unknown outcome quantity " + count);
            }
            var setup = Setup(); setup.EnemyGroup[0] = "unknown_enemy";
            Assert.True(!Fast(setup, Win(), Report()), "unknown enemy fails closed");
            Assert.True(!Fast(null, Win(), Report()), "null setup");
            Assert.True(!Fast(Setup(), null, Report()), "null outcome");
            Assert.True(!Fast(Setup(), Win(), null), "null report");
        }
        [LogicTest] public static void EligibilityIsPureAndSettlementRemainsCached()
        {
            var state = GameState.NewGame(DB, Difficulty.Normal);
            var run = new Abyss.Logic.Dungeon.DungeonRun(DB, state, 0, Abyss.Logic.Dungeon.ArrivalMode.Town);
            var flags = System.Reflection.BindingFlags.Instance | System.Reflection.BindingFlags.NonPublic;
            var request = (Abyss.Logic.Dungeon.DungeonBattleRequest)typeof(Abyss.Logic.Dungeon.DungeonRun).GetMethod("StartBattle", flags).Invoke(run,
                new object[] { BattleKind.Random, new List<string> { "slime" }, state.Position, state.Position, "", 1f });
            state.BestiaryOf("slime").Seen = true;
            var win = Win(); win.Experience = 1; win.Gold = 10;
            var settled = run.ResolveBattle(win);
            string before = JsonConvert.SerializeObject(new { state, setup = request.Setup, win, report = settled.Report });
            for (int i = 0; i < 20; i++) Fast(request.Setup, win, settled.Report);
            Assert.Equal(before, JsonConvert.SerializeObject(new { state, setup = request.Setup, win, report = settled.Report }), "eligibility never changes settlement/campaign");
            var cached = run.ResolveBattle(win);
            Assert.True(ReferenceEquals(settled, cached), "cached resolution instance retained");
            Assert.Equal(1, state.TotalWins, "settled once");
            Assert.Equal(before, JsonConvert.SerializeObject(new { state, setup = request.Setup, win, report = settled.Report }), "cached resolve does not reapply");
        }
    }
}
