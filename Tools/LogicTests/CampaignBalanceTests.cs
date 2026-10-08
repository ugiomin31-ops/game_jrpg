// 35-floor campaign balance: AUTO party at each floor's main-path level with chapter gear (by rule) against every
// encounter group, FOE, fixed event and boss. Prints the balance table; asserts the targets that hold with the
// gear present in the data.
using System;
using System.Collections.Generic;
using System.Linq;
using Abyss.Logic;
using Abyss.Logic.Battle;

namespace Abyss.LogicTests
{
    public static class CampaignBalanceTests
    {
        [LogicTest]
        public static void CampaignBalanceTable()
        {
            var db = TestMain.DB;
            Console.WriteLine("  floor  Lv  random(win rounds)  FOE          event        boss");
            var randomByChapter = new Dictionary<int, CampaignSim.Result>();
            var bossByChapter = new Dictionary<int, CampaignSim.Result>();
            int seed = 4100;
            foreach (var floor in db.Floors)
            {
                int c = CampaignSim.Chapter(floor.Index);
                int level = CampaignSim.FloorLevel(floor.Index);
                var party = CampaignSim.Party(db, level, c);
                var random = new CampaignSim.Result();
                foreach (var group in floor.EncounterGroups.Distinct(new GroupComparer()))
                    for (int s = 0; s < 2; s++) CampaignSim.Fight(db, party, group, BattleKind.Random, 1f, floor.Id, seed++, random);
                var foe = new CampaignSim.Result();
                foreach (var f in floor.Foes)
                    for (int s = 0; s < 3; s++) CampaignSim.Fight(db, party, f.Group, BattleKind.Foe, f.Power, floor.Id, seed++, foe);
                var ev = new CampaignSim.Result();
                // Trial-corridor superboss events are measured with the bosses below.
                foreach (var e in floor.Events.Where(e => !e.Group.Any(id => db.Enemies[id].IsBoss)))
                    for (int s = 0; s < 2; s++) CampaignSim.Fight(db, party, e.Group, BattleKind.Event, 1f, floor.Id, seed++, ev);
                var boss = new CampaignSim.Result();
                if (floor.BossGroup.Count > 0 && c < 7)
                {
                    var bossParty = CampaignSim.Party(db, CampaignSim.BossLevel(c), c);
                    for (int s = 0; s < 16; s++) CampaignSim.Fight(db, bossParty, floor.BossGroup, BattleKind.Boss, 1f, floor.Id, seed++, boss);
                    bossByChapter[c] = boss;
                }
                if (!randomByChapter.TryGetValue(c, out var acc)) randomByChapter[c] = acc = new CampaignSim.Result();
                acc.Battles += random.Battles; acc.Wins += random.Wins; acc.Rounds += random.Rounds;
                Console.WriteLine($"  {floor.FloorLabel,-5} {level,3}  {random,-18}  {foe,-11}  {ev,-11}  {(floor.BossGroup.Count > 0 && c < 7 ? $"{floor.BossGroup[0]}@Lv{CampaignSim.BossLevel(c)} {boss}" : "")}");
            }
            // Superbosses: the trial corridor's six echoes at the level cap with legendary gear.
            var legendary = CampaignSim.Party(db, SpecIds.LevelCap, 7, legendary: true);
            var superRates = new List<double>();
            foreach (var enemy in db.Enemies.Values.Where(e => e.Id.EndsWith("_ex")).OrderBy(e => e.Level))
            {
                var r = new CampaignSim.Result();
                for (int s = 0; s < 12; s++) CampaignSim.Fight(db, legendary, new[] { enemy.Id }, BattleKind.Boss, 1f, db.Floors[db.Floors.Count - 1].Id, seed++, r);
                superRates.Add(r.WinRate);
                Console.WriteLine($"  superboss {enemy.Id,-20} Lv{enemy.Level} vs Lv{SpecIds.LevelCap} legendary  {r}");
            }
            foreach (var kv in randomByChapter.OrderBy(kv => kv.Key))
                Console.WriteLine($"  chapter {kv.Key}: random {kv.Value}  boss {(bossByChapter.TryGetValue(kv.Key, out var b) ? b.ToString() : "-")}");

            // Targets that hold with the shipped gear tiers (chapters 1-4; later chapters depend on the T5-T8 gear rows).
            for (int c = 1; c <= 4; c++)
            {
                var r = randomByChapter[c];
                Assert.True(r.WinRate >= 0.9, $"chapter {c} random fights are won ({r})");
                Assert.True(r.AvgRounds >= 2 && r.AvgRounds <= 7, $"chapter {c} random fights take a few rounds ({r})");
                Assert.True(bossByChapter[c].WinRate >= 0.25, $"chapter {c} boss is winnable at its level ({bossByChapter[c]})");
            }
        }

        sealed class GroupComparer : IEqualityComparer<List<string>>
        {
            public bool Equals(List<string> a, List<string> b) => a.SequenceEqual(b);
            public int GetHashCode(List<string> g) => string.Join(",", g).GetHashCode();
        }
    }
}
