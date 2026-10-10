using System;
using System.Collections.Generic;
using System.Linq;
using Abyss.Logic;
using Abyss.Logic.Battle;
using Abyss.Logic.Game;
using Newtonsoft.Json;

namespace Abyss.LogicTests
{
    public static class ResourceAttritionTests
    {
        static CampaignSim.Vitals V(string id, int hp, int mp, int maxHp, int maxMp, int tp = 0)
            => new CampaignSim.Vitals { Id = id, UnitId = id, Hp = hp, Mp = mp, MaxHp = maxHp, MaxMp = maxMp, Tp = tp };

        [LogicTest]
        public static void DenominatorAllOutcomesAndWeightedMerge()
        {
            var win = new CampaignSim.Sample
            {
                Outcome = BattleResult.Victory, Rounds = 3, GrossMpSpent = 15,
                Start = new List<CampaignSim.Vitals> { V("a", 80, 20, 100, 50), V("b", 100, 50, 100, 50) },
                End = new List<CampaignSim.Vitals> { V("a", 90, 30, 999, 999), V("b", 70, 45, 100, 50) },
            };
            Assert.Equal(30, win.HpLost, "HP loss clamped per initial hero, heals don't cancel ally loss");
            Assert.Equal(300, win.InitialCapacity, "initial maxima, not current resources or changed end maxima");
            Assert.Near(0.15, win.Attrition, 1e-12, "gross paid MP participates");
            Assert.Equal(-5, win.NetMpDepletion, "net MP transparently reports regeneration separately");
            var loss = new CampaignSim.Sample
            {
                Outcome = BattleResult.Defeat, Rounds = 5, GrossMpSpent = 10,
                Start = new List<CampaignSim.Vitals> { V("a", 100, 50, 100, 50) },
                End = new List<CampaignSim.Vitals> { V("a", 0, 40, 100, 50) },
            };
            var left = new CampaignSim.Result(); left.Record(win); left.Record(win);
            var right = new CampaignSim.Result(); right.Record(loss);
            left.Merge(right);
            Assert.Equal(3, left.Battles, "all samples merged"); Assert.Equal(2, left.Wins, "defeats not wins");
            Assert.Equal(6, left.Rounds, "winning round metric remains unchanged");
            Assert.Near((0.15 * 2 + 110.0 / 150) / 3, left.AvgAttrition, 1e-12, "merge weights per sample, not per floor or wins");
            Assert.Equal(40L, left.GrossMpSpent, "gross accumulator propagated");
            Assert.Equal(0L, left.NetMpDepletion, "net accumulator propagated");
            foreach (var outcome in new[] { BattleResult.Fled, BattleResult.None })
            {
                loss.Outcome = outcome; loss.TimedOut = outcome == BattleResult.None;
                right.Record(loss);
            }
            Assert.Equal(3, right.Battles, "flee and incomplete endpoints counted");
            Assert.Equal(0, right.Wins, "incomplete never wins"); Assert.Equal(1, right.Timeouts, "timeouts explicit");
            Assert.Near(110.0 / 150, right.AvgAttrition, 1e-12, "losses retain resource metric");
        }

        [LogicTest]
        public static void ActionLinkedPaidMpExcludesAbsorptionAndRegen()
        {
            var db = TestMain.DB;
            string skill = db.Skills.Values.First(s => s.MpCost > 0).Id;
            int cost = db.Skills[skill].MpCost;
            var events = new List<BattleEvent>
            {
                new ActionStartEvent { ActorId = "hero", Kind = ActionKind.Skill, SkillId = skill },
                new MpChangeEvent { UnitId = "hero", Delta = -cost },
                new DamageEvent { TargetId = "hero", Amount = 0, Absorbed = 7 },
                new MpChangeEvent { UnitId = "hero", Delta = -7 }, // mana-shield MP is NOT a paid skill cost
                new ActionEndEvent { ActorId = "hero", Kind = ActionKind.Skill },
                new MpChangeEvent { UnitId = "hero", Delta = 5 }, // turn regen
                new ActionStartEvent { ActorId = "enemy", Kind = ActionKind.Skill, SkillId = skill },
                new MpChangeEvent { UnitId = "enemy", Delta = -cost },
                new ActionStartEvent { ActorId = "hero", Kind = ActionKind.Skill, SkillId = skill },
                new MpChangeEvent { UnitId = "hero", Delta = -cost },
                new ActionStartEvent { ActorId = "hero", Kind = ActionKind.Skill, SkillId = skill, IsChargeRelease = true },
                new MpChangeEvent { UnitId = "hero", Delta = -7 },
            };
            Assert.Equal(cost * 2, CampaignSim.PaidHeroMp(db, events, new[] { "hero" }), "only actual action-linked hero payments");
            bool refused = false;
            try { CampaignSim.PaidHeroMp(db, new BattleEvent[] { events[0], new ActionEndEvent { ActorId = "hero" } }, new[] { "hero" }); }
            catch (Exception) { refused = true; }
            Assert.True(refused, "missing payment event cannot silently undercount gross MP");
        }

        [LogicTest]
        public static void NoSettlementTimeoutAndRealEventAccounting()
        {
            var db = TestMain.DB;
            var party = CampaignSim.Party(db, 4, 1, jobs: true, forge: 3);
            string before = JsonConvert.SerializeObject(party);
            var setup = PartyStats.BuildBattleSetup(db, party, BattleKind.Random, db.Floors[0].EncounterGroups[0], 1, db.Floors[0].Id, 4100);
            var sample = CampaignSim.Measure(db, setup);
            Assert.Equal(before, JsonConvert.SerializeObject(party), "measurement doesn't settle XP, rewards, levels, vitals or knowledge");
            var replay = new BattleEngine(db, setup);
            var events = BattleTestUtil.RunAuto(replay, 120);
            // Independent oracle: at full MP, every executed positive-cost skill paid its defined cost (validated engine commands).
            var heroIds = new HashSet<string>(replay.Party.Select(h => h.Id));
            int definedCosts = events.OfType<ActionStartEvent>().Where(a => heroIds.Contains(a.ActorId) && a.Kind == ActionKind.Skill)
                .Sum(a => db.Skills[a.SkillId].MpCost);
            Assert.Equal(definedCosts, sample.GrossMpSpent, "real event ledger matches independent executed-action cost oracle");
            Assert.Equal(replay.Party.Sum(h => h.Hp), sample.End.Sum(h => h.Hp), "no RNG consumed by measurement");
            Assert.Equal(replay.Party.Sum(h => h.Mp), sample.End.Sum(h => h.Mp), "pre-settlement endpoint");
            var timeout = CampaignSim.Measure(db, setup, maxRounds: 0);
            Assert.True(timeout.TimedOut && !timeout.Won, "round-capped unfinished sample is a loss");
            var result = new CampaignSim.Result(); result.Record(timeout);
            Assert.Equal(1, result.Battles, "timeout doesn't disappear"); Assert.Equal(1, result.Timeouts, "timeout reported");
            Assert.True(timeout.InitialCapacity > 0, "timeout retains initial denominator and real endpoint");
        }

        [LogicTest]
        public static void RealSerialEndpointsMatchIndependentUnsettledReplay()
        {
            var db = TestMain.DB;
            var floor = db.Floors[0];
            var groups = floor.EncounterGroups.Take(3).Select(g => new List<string>(g)).ToList();
            var party = CampaignSim.Party(db, CampaignSim.FloorLevel(floor.Index), 1, jobs: true, forge: 3);
            string before = JsonConvert.SerializeObject(party);
            var trip = CampaignSim.SerialTrip(db, party, groups, 0, floor.Id, 5600);
            List<CampaignSim.Vitals> previous = null;
            int fights = 0;
            for (int i = 0; i < CampaignSim.TripFights; i++)
            {
                var setup = PartyStats.BuildBattleSetup(db, party, BattleKind.Random, groups[i % groups.Count], 1, floor.Id,
                    5600 + i * 1000000);
                setup.Inventory.Clear();
                foreach (var h in setup.Party)
                {
                    var p = previous?.Single(v => v.Id == h.HeroId);
                    h.Hp = p == null ? h.MaxHp : p.Hp; h.Mp = p == null ? h.MaxMp : p.Mp; h.Tp = p == null ? 0 : p.Tp;
                    h.Statuses = p == null ? new Dictionary<string, int>() : new Dictionary<string, int>(p.Statuses);
                }
                var engine = new BattleEngine(db, setup);
                var sample = trip.Fights[i];
                for (int h = 0; h < engine.Party.Count; h++)
                {
                    Assert.Equal(setup.Party[h].Hp, sample.Start[h].Hp, "serial actual HP carry");
                    Assert.Equal(setup.Party[h].Mp, sample.Start[h].Mp, "serial actual MP carry");
                    Assert.Equal(Math.Max(setup.Party[h].Tp, setup.Party[h].TpStart), sample.Start[h].Tp, "serial TP gear floor");
                }
                BattleTestUtil.RunAuto(engine, 120);
                Assert.Equal(engine.Outcome.Result, sample.Outcome, "serial outcome matches independent engine");
                Assert.Equal(engine.Round, sample.Rounds, "serial RNG unchanged");
                for (int h = 0; h < engine.Party.Count; h++)
                {
                    var unit = engine.Party[h];
                    Assert.Equal(unit.Hp, sample.End[h].Hp, "serial endpoint HP before settlement");
                    Assert.Equal(unit.Mp, sample.End[h].Mp, "serial endpoint MP before settlement");
                    Assert.Equal(engine.Outcome.FinalTp[unit.DefId], sample.End[h].Tp, "serial endpoint TP including KO");
                }
                previous = engine.Party.Select(CampaignSim.Vitals.Of).ToList();
                fights++;
                if (engine.Outcome.Result != BattleResult.Victory) break;
            }
            Assert.Equal(fights, trip.Fights.Count, "stop exactly on first non-victory");
            Assert.Equal(before, JsonConvert.SerializeObject(party), "trip never settles or changes baseline party");
            // A deterministic hopeless trip proves failures stop early and still contribute their endpoint to the median.
            var low = CampaignSim.Party(db, 1, 1);
            var failed = CampaignSim.SerialTrip(db, low, new List<List<string>> { new List<string> { "abyss_lord" } }, 0, floor.Id, 5600);
            Assert.Equal(1, failed.Fights.Count, "defeat stops trip immediately");
            Assert.True(!failed.Complete && failed.RemainingHp == 0, "failed trip preserves all-KO endpoint");
            Assert.Near((failed.RemainingHp + trip.RemainingHp) / 2,
                CampaignSim.Median(new[] { failed.RemainingHp, trip.RemainingHp }), 1e-12, "failed endpoints aren't filtered from median");
        }

        [LogicTest]
        public static void CarryPreservesKoResourcesStatusesAndGearTp()
        {
            var db = TestMain.DB;
            var setup = BattleTestUtil.Setup(20, new[] { "slime" }, 4100);
            var end = setup.Party.Select((h, i) => V(h.HeroId, i == 0 ? 0 : 17, 3, h.MaxHp, h.MaxMp, i == 0 ? 0 : 42)).ToList();
            end[1].Statuses["poison"] = 2;
            var prior = new CampaignSim.Sample { End = end };
            setup.Party[1].TpStart = 25; setup.Party[2].TpStart = 60;
            CampaignSim.Carry(setup, prior);
            var engine = new BattleEngine(db, setup);
            Assert.Equal(0, engine.Party[0].Hp, "KO never auto-revived between fights");
            Assert.Equal(17, engine.Party[1].Hp, "HP carried, not restored"); Assert.Equal(3, engine.Party[1].Mp, "MP carried");
            Assert.Equal(42, engine.Party[1].Tp, "higher carried TP survives gear floor");
            Assert.Equal(60, engine.Party[2].Tp, "gear TP remains a minimum per O7");
            Assert.Equal(2, setup.Party[1].Statuses["poison"], "carried status preserved");
            setup.Party[1].Statuses.Clear(); Assert.Equal(2, end[1].Statuses["poison"], "carry uses copies");
            Assert.Equal(3004100, CampaignSim.TripSeed(4100, 3), "fixed seed stride");
            var trip = new CampaignSim.Trip();
            trip.Fights.Add(new CampaignSim.Sample { Start = end, End = end, Outcome = BattleResult.Defeat });
            Assert.True(!trip.Complete, "failed serial sample isn't complete");
            Assert.Near(0.5, CampaignSim.Median(new[] { 0.0, 0.5, 1.0 }), 1e-12, "median includes failed endpoints");
            Assert.Near(0.25, CampaignSim.Median(new[] { 0.0, 0.5 }), 1e-12, "even-sample median");
        }
    }
}
