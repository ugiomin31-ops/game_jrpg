// 35-floor campaign balance: AUTO party at each floor's main-path level with chapter gear (by rule) against every
// encounter group, FOE, fixed event and boss. Prints two balance tables: the under-prepared player (base jobs, no forging)
// and the expected player (class changes at Lv 15 / Lv 40 and the forging of CampaignSim.ExpectedForge). Asserts the targets.
using System;
using System.Collections.Generic;
using System.Linq;
using Abyss.Logic;
using Abyss.Logic.Battle;
using Abyss.Logic.Game;

namespace Abyss.LogicTests
{
    public static class CampaignBalanceTests
    {
        enum Prep { Under, Expected }

        // Boss, FOE and superboss fights use fixed seed bases keyed by chapter / floor / level, so the two parties fight the
        // same seeds (a paired comparison) and an edit elsewhere does not reshuffle these numbers.
        const int BossSamples = 60;
        static int BossSeed(int chapter) => 500000 + chapter * 100;
        static int FoeSeed(int floorIndex) => 700000 + floorIndex * 10;

        sealed class Table
        {
            public readonly Dictionary<int, CampaignSim.Result> Random = new Dictionary<int, CampaignSim.Result>();
            public readonly Dictionary<int, CampaignSim.Result> Boss = new Dictionary<int, CampaignSim.Result>();
            public readonly Dictionary<int, List<CampaignSim.Trip>> Trips = new Dictionary<int, List<CampaignSim.Trip>>();
            public readonly List<CampaignSim.Result> Foes = new List<CampaignSim.Result>();
            public readonly List<(string Id, CampaignSim.Result Result)> Superbosses = new List<(string, CampaignSim.Result)>();
        }

        /// <summary>The party a player has at a level in a chapter, with the gear the chapter offers (and jobs/forging when expected).</summary>
        static GameState PartyFor(GameDB db, Prep prep, int level, int chapter, bool legendary = false, int forge = 0)
        {
            if (prep == Prep.Under) return CampaignSim.Party(db, level, chapter, legendary);
            return CampaignSim.Party(db, level, chapter, legendary, jobs: true, forge: forge);
        }

        static Table RunTable(GameDB db, Prep prep, string title, ref int seed)
        {
            var table = new Table();
            Console.WriteLine(title);
            Console.WriteLine("  floor  Lv  random(win rounds)  FOE          event        boss");
            foreach (var floor in db.Floors)
            {
                int c = CampaignSim.Chapter(floor.Index);
                int level = CampaignSim.FloorLevel(floor.Index);
                var party = PartyFor(db, prep, level, c, forge: CampaignSim.ExpectedForge[CampaignSim.MarketTier(c) - 1]);
                var random = new CampaignSim.Result();
                var groups = floor.EncounterGroups.Distinct(new GroupComparer()).ToList();
                for (int g = 0; g < groups.Count; g++)
                    for (int s = 0; s < 2; s++)
                    {
                        int originalSeed = seed++;
                        CampaignSim.Fight(db, party, groups[g], BattleKind.Random, 1f, floor.Id, originalSeed, random);
                        if (prep == Prep.Expected)
                        {
                            if (!table.Trips.TryGetValue(c, out var trips)) table.Trips[c] = trips = new List<CampaignSim.Trip>();
                            var trip = CampaignSim.SerialTrip(db, party, groups, g, floor.Id, originalSeed);
                            trips.Add(trip);
                            for (int fight = 0; fight < trip.Fights.Count; fight++)
                            {
                                var endpoint = trip.Fights[fight];
                                Console.WriteLine($"  trip_endpoint ch={c} floor={floor.FloorLabel} group={g} sample={s} seed={CampaignSim.TripSeed(originalSeed, fight)} fight={fight + 1} {endpoint.Outcome} timeout={endpoint.TimedOut} paidMP={endpoint.GrossMpSpent} start=[{string.Join(";", endpoint.Start)}] end=[{string.Join(";", endpoint.End)}]");
                            }
                        }
                    }
                var foe = new CampaignSim.Result();
                foreach (var f in floor.Foes)
                    for (int s = 0; s < 6; s++) CampaignSim.Fight(db, party, f.Group, BattleKind.Foe, f.Power, floor.Id, FoeSeed(floor.Index) + s, foe);
                if (foe.Battles > 0) table.Foes.Add(foe);
                var ev = new CampaignSim.Result();
                // Trial-corridor superboss events are measured with the bosses below.
                foreach (var e in floor.Events.Where(e => !e.Group.Any(id => db.Enemies[id].IsBoss)))
                    for (int s = 0; s < 2; s++) CampaignSim.Fight(db, party, e.Group, BattleKind.Event, 1f, floor.Id, seed++, ev);
                var boss = new CampaignSim.Result();
                if (floor.BossGroup.Count > 0 && c <= GameFlow.MainChapters)
                {
                    var bossParty = PartyFor(db, prep, CampaignSim.BossLevel(c), c, forge: CampaignSim.ExpectedForge[CampaignSim.MarketTier(c) - 1]);
                    for (int s = 0; s < BossSamples; s++) CampaignSim.Fight(db, bossParty, floor.BossGroup, BattleKind.Boss, 1f, floor.Id, BossSeed(c) + s, boss);
                    table.Boss[c] = boss;
                }
                if (!table.Random.TryGetValue(c, out var acc)) table.Random[c] = acc = new CampaignSim.Result();
                acc.Merge(random);
                Console.WriteLine($"  {floor.FloorLabel,-5} {level,3}  {random,-18}  {foe,-11}  {ev,-11}  {(floor.BossGroup.Count > 0 && c <= GameFlow.MainChapters ? $"{floor.BossGroup[0]}@Lv{CampaignSim.BossLevel(c)} {boss}" : "")}");
            }
            // Superbosses: the trial corridor's six echoes at the level cap with legendary gear (expected: jobs and +10 forging).
            var legendary = prep == Prep.Under
                ? CampaignSim.Party(db, SpecIds.LevelCap, GameFlow.MainChapters + 1, legendary: true)
                : CampaignSim.Party(db, SpecIds.LevelCap, GameFlow.MainChapters + 1, legendary: true, jobs: true, forge: Enhancement.MaxLevel);
            foreach (var enemy in db.Enemies.Values.Where(e => e.Id.EndsWith("_ex")).OrderBy(e => e.Level))
            {
                var r = new CampaignSim.Result();
                for (int s = 0; s < BossSamples; s++) CampaignSim.Fight(db, legendary, new[] { enemy.Id }, BattleKind.Boss, 1f, db.Floors[db.Floors.Count - 1].Id, 600000 + enemy.Level * 100 + s, r);
                table.Superbosses.Add((enemy.Id, r));
                Console.WriteLine($"  superboss {enemy.Id,-20} Lv{enemy.Level} vs Lv{SpecIds.LevelCap} legendary  {r}");
            }
            foreach (var kv in table.Random.OrderBy(kv => kv.Key))
            {
                Console.WriteLine($"  chapter {kv.Key}: random {kv.Value} [{kv.Value.Resources}]  boss {(table.Boss.TryGetValue(kv.Key, out var b) ? b.ToString() + " [" + b.Resources + "]" : "-")}");
                if (table.Trips.TryGetValue(kv.Key, out var trips))
                    Console.WriteLine($"  serial chapter {kv.Key}: complete={trips.Count(t => t.Complete)}/{trips.Count} ({(double)trips.Count(t => t.Complete) / trips.Count:P2}) medianHP={CampaignSim.Median(trips.Select(t => t.RemainingHp)):P2} medianMP={CampaignSim.Median(trips.Select(t => t.RemainingMp)):P2}");
            }
            return table;
        }

        [LogicTest]
        public static void CampaignBalanceTable()
        {
            var db = TestMain.DB;
            int seed = 4100;
            var under = RunTable(db, Prep.Under, "under-prepared player: base jobs, chapter gear, no forging", ref seed);
            var expected = RunTable(db, Prep.Expected, "expected player: Lv15 advanced job, Lv40 top job, forging per chapter (CampaignSim.ExpectedForge), +10 for superbosses", ref seed);

            var failures = new List<string>();
            void Check(bool pass, string message) { if (!pass) { failures.Add(message); Console.WriteLine("  BAND_FAIL " + message); } }

            // O9 supersedes only the under-prepared random win floor (75%); keep its original round bounds.
            // A chapter boss is winnable at its
            // level with some risk whenever the data has that chapter's gear tier (a weapon with shop_tier == chapter).
            foreach (var kv in under.Random)
            {
                Check(kv.Value.WinRate >= 0.75, $"chapter {kv.Key} random fights are won ({kv.Value})");
                Check(kv.Value.AvgRounds >= 2.5 && kv.Value.AvgRounds <= 6, $"chapter {kv.Key} random fights take a few rounds ({kv.Value})");
            }
            foreach (var kv in under.Boss)
            {
                bool geared = db.Equipment.Values.Any(p => p.ShopTier == kv.Key && p.Slot == "weapon");
                Console.WriteLine($"  chapter {kv.Key} boss {(geared ? "checked" : "not checked: no tier-" + kv.Key + " gear rows yet")}");
                // Zones 1-4: the under-prepared party (no class change) keeps a 25 % floor. From zone 5 the bosses are tuned for
                // the advanced job (Lv 12) and later the master job (Lv 36), so without them the only check is that the boss is
                // not a free win; the expected-player range below keeps every boss beatable.
                if (!geared) continue;
                if (kv.Key <= 4) Check(kv.Value.WinRate >= 0.25, $"zone {kv.Key} boss is winnable at least 25% ({kv.Value})");
                Check(kv.Value.WinRate < 1, $"zone {kv.Key} boss is not a free win ({kv.Value})");
            }

            // Expected player targets.
            foreach (var kv in expected.Random)
            {
                Check(kv.Value.WinRate >= 0.95, $"expected: chapter {kv.Key} random fights are won at least 95% ({kv.Value})");
                Check(kv.Value.AvgAttrition >= 0.08 && kv.Value.AvgAttrition <= 0.20, $"expected: chapter {kv.Key} cold-start attrition is 8-20% ({kv.Value.Resources})");
                var trips = expected.Trips[kv.Key];
                Check(trips.Count(t => t.Complete) >= trips.Count * 0.8, $"expected: chapter {kv.Key} four-fight trips complete at least 80% ({trips.Count(t => t.Complete)}/{trips.Count})");
                Check(kv.Value.AvgRounds >= 2.5 && kv.Value.AvgRounds <= 6, $"expected: chapter {kv.Key} random fights take 2.5-6 rounds ({kv.Value})");
            }
            int foesOver60 = expected.Foes.Count(f => f.WinRate >= 0.6);
            Check(foesOver60 * 3 >= expected.Foes.Count * 2, $"expected: FOEs are mostly won at 60% or more ({foesOver60} of {expected.Foes.Count} floors)");
            double? prevRounds = null;
            for (int c = 1; c <= GameFlow.MainChapters; c++)
            {
                var boss = expected.Boss[c];
                Check(boss.WinRate >= 0.55 && boss.WinRate <= 0.85, $"expected: zone {c} boss is 55-85% ({boss})");
                // Boss fights stay in a steady band zone to zone: no drop of more than 2.5 rounds, no jump of more than four (the
                // step to the final boss is the long one: 12-16 rounds after a zone 11 boss of about 11).
                if (prevRounds is double p)
                    Check(boss.AvgRounds >= p - 2.5 && boss.AvgRounds <= p + 4.0, $"expected: zone {c} boss rounds change smoothly ({boss}, previous {p:0.0}r)");
                prevRounds = boss.AvgRounds;
            }
            // The final boss is the longest fight of the main story: 12-16 rounds, longer than the zone 11 boss.
            int last = GameFlow.MainChapters;
            var final = expected.Boss[last];
            Check(final.AvgRounds >= 12 && final.AvgRounds <= 16, $"expected: final boss takes 12-16 rounds ({final})");
            Check(final.AvgRounds > expected.Boss[last - 1].AvgRounds, $"expected: final boss fight is longer than zone {last - 1} ({final} vs {expected.Boss[last - 1]})");
            // The under-prepared curve must not invert sharply in zones 1-4: a zone's boss is not much easier than the previous one.
            for (int c = 2; c <= 4; c++)
                Check(under.Boss[c].WinRate <= under.Boss[c - 1].WinRate + 0.25,
                    $"under-prepared: zone {c} boss is not much easier than zone {c - 1} ({under.Boss[c]} vs {under.Boss[c - 1]})");
            // Main-story boss HP grows zone by zone, and the final boss is clearly the largest (at least 1.1x the zone 11 boss).
            for (int c = 2; c <= last; c++)
            {
                int prevHp = db.Enemies[SpecIds.ChapterBosses[c - 2]].MaxHp, hp = db.Enemies[SpecIds.ChapterBosses[c - 1]].MaxHp;
                Check(hp > prevHp, $"boss HP grows zone by zone: zone {c} ({hp}) above zone {c - 1} ({prevHp})");
            }
            int beforeFinalHp = db.Enemies[SpecIds.ChapterBosses[last - 2]].MaxHp, finalHp = db.Enemies[SpecIds.ChapterBosses[last - 1]].MaxHp;
            Check(finalHp >= beforeFinalHp * 1.1, $"final boss HP is at least 1.1x the zone {last - 1} boss ({finalHp} vs {beforeFinalHp})");
            foreach (var (id, r) in expected.Superbosses)
                Check(r.WinRate >= 0.25 && r.WinRate <= 0.75, $"expected: superboss {id} is won 25-75% of the time ({r})");
            Assert.True(failures.Count == 0, string.Join("\n", failures));
        }

        sealed class GroupComparer : IEqualityComparer<List<string>>
        {
            public bool Equals(List<string> a, List<string> b) => a.SequenceEqual(b);
            public int GetHashCode(List<string> g) => string.Join(",", g).GetHashCode();
        }
    }
}
