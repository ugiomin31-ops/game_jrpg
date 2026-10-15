// Floor 1 (subway_1..3) fairness: the real BattleEngine + AUTO with the real NewGame starter party and gear, Normal
// difficulty, no items, full HP/MP at the start of each fight, fixed seeds. The zone-1 bats and the bat lord are sized
// for the levels the design gives the party (Tools/content/build_world.py --levels: 1-1 enter L1, 1-2 L2, 1-3 L4, boss L5).
using System;
using System.Collections.Generic;
using System.Linq;
using Abyss.Logic;
using Abyss.Logic.Battle;
using Abyss.Logic.Game;

namespace Abyss.LogicTests
{
    public static class Floor1BalanceTests
    {
        const int Samples = 60;

        sealed class Rate
        {
            public int Wins, N;
            public readonly List<int> WinRounds = new List<int>();
            public double Pct => N == 0 ? 0 : 100.0 * Wins / N;
            public double MedianRounds { get { if (WinRounds.Count == 0) return 0; var a = WinRounds.OrderBy(x => x).ToArray(); return a[a.Length / 2]; } }
            public override string ToString() => $"win {Pct,5:0.0}% medRounds {MedianRounds,4:0.0} (n={N})";
        }

        static Rate Measure(GameDB db, int level, IEnumerable<string> group, BattleKind kind, float power, string floorId, int seedBase)
        {
            var rate = new Rate();
            for (int s = 0; s < Samples; s++)
            {
                var state = GameState.NewGame(db, Difficulty.Normal);
                foreach (var h in state.Party) { h.Level = level; h.Hp = -1; h.Mp = -1; h.Tp = 0; }
                state.Repair(db);
                var setup = PartyStats.BuildBattleSetup(db, state, kind, group, power, floorId, seedBase + s * 7919);
                foreach (var h in setup.Party) { h.Hp = h.MaxHp; h.Mp = h.MaxMp; h.Tp = 0; }
                setup.Inventory.Clear();
                var engine = new BattleEngine(db, setup);
                BattleTestUtil.RunAuto(engine);
                rate.N++;
                if (engine.State == BattleEngineState.Ended && engine.Outcome.Result == BattleResult.Victory)
                {
                    rate.Wins++;
                    rate.WinRounds.Add(engine.Round);
                }
            }
            return rate;
        }

        static FloorDef Floor(GameDB db, string id) => db.Floors.First(f => f.Id == id);

        [LogicTest]
        public static void Floor1AmbushIsWinnableAtLevel1()
        {
            var db = TestMain.DB;
            var floor = Floor(db, "subway_1");
            var ambushes = floor.Events.Where(e => e.IsAmbush && e.Group.Count > 0).ToList();
            Assert.True(ambushes.Count > 0, "1-1 has its forced ambush");
            foreach (var e in ambushes)
            {
                var r = Measure(db, 1, e.Group, BattleKind.Event, 1f, floor.Id, 810000);
                Console.WriteLine($"  1-1 ambush [{string.Join(",", e.Group)}] L1: {r}");
                Assert.True(r.Pct >= 85.0, $"1-1 ambush [{string.Join(",", e.Group)}] at L1 won only {r.Pct:0.0}% (need >= 85%)");
            }
        }

        [LogicTest]
        public static void Floor1RandomGroupsAreSafeAtLevel1()
        {
            var db = TestMain.DB;
            var floor = Floor(db, "subway_1");
            int index = 0;
            foreach (var g in floor.EncounterGroups)
            {
                var r = Measure(db, 1, g, BattleKind.Random, 1f, floor.Id, 820000 + 1000 * index++);
                Console.WriteLine($"  1-1 random [{string.Join(",", g)}] L1: {r}");
                Assert.True(r.Pct >= 95.0, $"1-1 random [{string.Join(",", g)}] at L1 won only {r.Pct:0.0}% (need >= 95%)");
            }
        }

        [LogicTest]
        public static void Floor1BossIsRealButNotAWall()
        {
            var db = TestMain.DB;
            var floor = Floor(db, "subway_3");
            Assert.True(floor.BossGroup.Count == 1 && floor.BossGroup[0] == "subway_bat_lord", "1-3 boss is the bat lord");
            var l5 = Measure(db, 5, floor.BossGroup, BattleKind.Boss, 1f, floor.Id, 830000);
            var l7 = Measure(db, 7, floor.BossGroup, BattleKind.Boss, 1f, floor.Id, 840000);
            Console.WriteLine($"  1-3 subway_bat_lord L5 starter gear: {l5}");
            Console.WriteLine($"  1-3 subway_bat_lord L7 starter gear: {l7}");
            Assert.True(l5.Pct >= 35.0 && l5.Pct <= 75.0, $"bat lord at the design boss level L5 won {l5.Pct:0.0}% (need 35-75%)");
            Assert.True(l7.Pct >= 80.0, $"bat lord at L7 won only {l7.Pct:0.0}% (need >= 80%)");
        }

        [LogicTest]
        public static void Floor1MidbossFoeIsFairAtLevel3()
        {
            var db = TestMain.DB;
            var floor = Floor(db, "subway_2");
            var foe = floor.Foes.FirstOrDefault(f => f.Group.Contains("elite_bat"));
            Assert.True(foe != null, "1-2 has the elite_bat mid-boss FOE");
            var r = Measure(db, 3, foe.Group, BattleKind.Foe, foe.Power, floor.Id, 850000);
            Console.WriteLine($"  1-2 FOE [{string.Join(",", foe.Group)}] x{foe.Power} L3: {r}");
            Assert.True(r.Pct >= 60.0, $"1-2 mid-boss FOE at L3 won only {r.Pct:0.0}% (need >= 60%)");
        }
    }
}
