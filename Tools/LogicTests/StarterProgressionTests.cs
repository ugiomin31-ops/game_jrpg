// Actual unboosted starter outings: fixed authored sampling, real once-only campaign settlement.
// This is not physical walking and not the expected/geared CampaignBalanceTests cohort.
using System;
using System.Collections.Generic;
using System.Linq;
using Newtonsoft.Json;
using Abyss.Logic;
using Abyss.Logic.Battle;
using Abyss.Logic.Game;

namespace Abyss.LogicTests
{
    public static class StarterProgressionTests
    {
        const int Trips = 60, Fights = 4, RoundCap = 120;
        static string Snapshot(object value) => JsonConvert.SerializeObject(value);
        static GameState Starter(GameDB db)
        {
            var state = GameState.NewGame(db, Difficulty.Normal);
            GameFlow.CompletePrologue(state);
            Assert.True(state.Party.All(h => h.Level == 1 && h.Xp == 0), "fresh Lv1 starters");
            Assert.Equal(3, state.ItemCount("healing_potion"), "three initial potions");
            Assert.Equal(1, state.ItemCount("return_stone"), "one initial return stone");
            Assert.True(!state.KnownWeaknessKeys().Any(), "no preloaded knowledge");
            return state;
        }
        static object Endpoint(GameState state) => new
        {
            party = state.Party.Select(h => new { h.Id, h.Level, h.Xp, h.Hp, h.Mp, h.Tp, h.Statuses }).ToArray(),
            knowledge = state.KnownWeaknessKeys().OrderBy(x => x).ToArray(), state.Gold, state.TotalWins, state.Inventory,
        };
        static BattleSetup Setup(GameDB db, GameState state, int trip, int fight)
        {
            var floor = db.Floors[0];
            return PartyStats.BuildBattleSetup(db, state, BattleKind.Random,
                floor.EncounterGroups[(trip + 3 * fight) % 7], 1f, floor.Id, 240000 + trip + 1000000 * fight);
        }
        static void VerifySetup(GameDB db, GameState state, BattleSetup setup)
        {
            foreach (var spec in setup.Party)
            {
                var hero = state.Hero(spec.HeroId);
                Assert.Equal(hero.Hp, spec.Hp, "settled HP carried, not raw pre-level endpoint");
                Assert.Equal(hero.Mp, spec.Mp, "settled MP carried");
                Assert.Equal(hero.Tp, spec.Tp, "carried TP before equipment minimum");
                Assert.Equal(hero.Level, spec.Level, "settled level carried");
                Assert.Equal(Snapshot(hero.Statuses), Snapshot(spec.Statuses), "carried statuses");
                Assert.True(hero.LearnedSkills.SequenceEqual(spec.Skills), "settled learned skills carried");
            }
            Assert.True(new HashSet<string>(state.KnownWeaknessKeys()).SetEquals(setup.KnownWeaknesses), "settled known weaknesses carried");
            var engine = new BattleEngine(db, setup);
            foreach (var unit in engine.Party)
            {
                var spec = setup.Party.Single(h => h.HeroId == unit.DefId);
                Assert.Equal(unit.IsAlive ? Math.Max(spec.Tp, spec.TpStart) : 0, unit.Tp, "engine gear TP minimum, not a reset");
            }
        }
        static void VerifySettlement(GameDB db, GameState before, GameState after, BattleOutcome outcome, BattleReport report)
        {
            bool victory = outcome.Result == BattleResult.Victory;
            Assert.Equal(before.TotalWins + (victory ? 1 : 0), after.TotalWins, "settlement counted once");
            Assert.Equal(before.Gold + (victory ? report.Gold : 0), after.Gold, "gold settled once, no failed reward");
            foreach (var hero in after.Party)
            {
                var old = before.Hero(hero.Id);
                var oldMax = PartyStats.EffectiveStats(db, old);
                var newMax = PartyStats.EffectiveStats(db, hero);
                int hp = outcome.FinalHp[hero.Id], mp = outcome.FinalMp[hero.Id];
                Assert.Equal(hp <= 0 ? 0 : Math.Min(newMax.MaxHp, hp + Math.Max(0, newMax.MaxHp - oldMax.MaxHp)), hero.Hp, "level-up is max gain, not full healing");
                Assert.Equal(Math.Min(newMax.MaxMp, mp + Math.Max(0, newMax.MaxMp - oldMax.MaxMp)), hero.Mp, "MP max gain only");
                Assert.Equal(hp <= 0 ? 0 : outcome.FinalTp[hero.Id], hero.Tp, "TP carry and KO clear");
                if (hp <= 0 || !victory)
                {
                    Assert.Equal(old.Level, hero.Level, "KO/nonvictory no active level reward");
                    Assert.Equal(old.Xp, hero.Xp, "KO/nonvictory no active XP");
                }
                else
                {
                    int paidXp = report.ExperienceByHero[hero.Id], level = old.Level, xp = old.Xp + paidXp;
                    while (level < GameState.LevelCap && xp >= PartyStats.XpToNext(level)) { xp -= PartyStats.XpToNext(level); level++; }
                    Assert.Equal(level, hero.Level, "independent XP progression");
                    Assert.Equal(level == GameState.LevelCap ? 0 : xp, hero.Xp, "independent XP remainder");
                }
                var statuses = hp <= 0 ? new Dictionary<string, int>() : outcome.FinalStatuses[hero.Id];
                Assert.Equal(Snapshot(statuses), Snapshot(hero.Statuses), "outcome statuses carried, KO cleared");
            }
            foreach (string id in before.Inventory.Keys.Concat(after.Inventory.Keys).Concat(outcome.Drops.Keys).Distinct())
            {
                int used = outcome.ItemsUsed.TryGetValue(id, out int u) ? u : 0;
                int drop = victory && db.Items.ContainsKey(id) && outcome.Drops.TryGetValue(id, out int d) ? d : 0;
                Assert.Equal(before.ItemCount(id) - used + drop, after.ItemCount(id), "inventory only actual consumption/rewards");
            }
            foreach (string id in before.EverOwnedItems) Assert.True(after.EverOwnedItems.Contains(id), "ever-owned never forgotten");
            foreach (string id in outcome.SeenEnemies) Assert.True(after.BestiaryOf(id).Seen, "seen knowledge retained");
            foreach (string key in outcome.DiscoveredWeaknesses) Assert.True(after.KnownWeaknessKeys().Contains(key), "discovered weakness settled");
        }

        [LogicTest]
        public static void FixedSixtyActualStarterTripsMeetOutingTargets()
        {
            var db = TestMain.DB;
            Assert.Equal("subway_1", db.Floors[0].Id, "actual first floor");
            Assert.Equal(7, db.Floors[0].EncounterGroups.Count, "seven authored rows");
            int firstAll = 0, two = 0, four = 0, timeouts = 0, gross = 0, net = 0;
            var costs = new List<int>();
            var groupTotals = Enumerable.Range(0, 7).ToDictionary(i => i, i => new int[3]);
            var failures = new List<string>();
            for (int t = 0; t < Trips; t++)
            {
                var state = Starter(db); int wins = 0, tripCost = 0;
                for (int f = 0; f < Fights; f++)
                {
                    string pre = Snapshot(Endpoint(state)), campaign = SaveCodec.Serialize(state);
                    var setup = Setup(db, state, t, f);
                    VerifySetup(db, state, setup);
                    Assert.Equal(campaign, SaveCodec.Serialize(state), "setup query pure including XP/gear/inventory");
                    var engine = new BattleEngine(db, setup);
                    int startMp = engine.Party.Sum(h => h.Mp);
                    var events = BattleTestUtil.RunAuto(engine, RoundCap);
                    var raw = engine.Party.Select(CampaignSim.Vitals.Of).ToArray();
                    bool timeout = engine.State != BattleEngineState.Ended;
                    int paid = CampaignSim.PaidHeroMp(db, events, engine.Party.Select(h => h.Id));
                    gross += paid; tripCost += paid; net += startMp - raw.Sum(h => h.Mp);
                    int row = (t + 3 * f) % 7; groupTotals[row][0]++;
                    if (timeout)
                    {
                        timeouts++; failures.Add($"t={t} f={f + 1} row={row} timeout pre={pre} raw={Snapshot(raw)} post={Snapshot(Endpoint(state))}");
                        Assert.Equal(campaign, SaveCodec.Serialize(state), "unfinished battle cannot settle/reward"); break;
                    }
                    Assert.True(engine.Outcome.ItemsUsed.Values.All(n => n == 0), "AUTO uses no consumables");
                    var before = SaveCodec.Deserialize(campaign, db);
                    var report = PartyStats.ApplyBattleOutcome(db, state, engine.Outcome); // Exactly once, only completed battle.
                    VerifySettlement(db, before, state, engine.Outcome, report);
                    bool win = engine.Outcome.Result == BattleResult.Victory;
                    if (win) { wins++; groupTotals[row][1]++; }
                    if (win && state.Party.All(h => h.Hp > 0)) { groupTotals[row][2]++; if (f == 0) firstAll++; }
                    if (!win)
                    {
                        failures.Add($"t={t} f={f + 1} row={row} {engine.Outcome.Result} paidMP={paid} pre={pre} raw={Snapshot(raw)} post={Snapshot(Endpoint(state))}"); break;
                    }
                }
                if (wins >= 2) two++; if (wins == Fights) four++; costs.Add(tripCost);
            }
            Console.WriteLine($"starter60 firstAll={firstAll}/60 two={two}/60 four={four}/60 timeout={timeouts} grossMP={gross} netMP={net} tripMPmin={costs.Min()} median={CampaignSim.Median(costs.Select(x => (double)x))} max={costs.Max()}");
            foreach (var g in groupTotals) Console.WriteLine($"starter_group row={g.Key} attempts={g.Value[0]} wins={g.Value[1]} all4alive={g.Value[2]}");
            foreach (var failure in failures) Console.WriteLine("starter_failed_endpoint " + failure);
            Assert.True(firstAll >= 48, "first victory with all four alive >=48/60");
            Assert.True(two >= 54, "two victories >=54/60");
            Assert.True(four >= 48, "four victories >=48/60");
            Assert.Equal(0, timeouts, "zero starter timeouts"); Assert.True(gross > 0, "actual positive skill MP expenditure");
        }

        [LogicTest]
        public static void PaymentMeasurementIsPureAndPairedReplayDeterministic()
        {
            var db = TestMain.DB;
            foreach (int trip in new[] { 0, 7, 31 })
            {
                var state = Starter(db);
                for (int fight = 0; fight < 4; fight++)
                {
                    string before = SaveCodec.Serialize(state);
                    var setup = Setup(db, state, trip, fight); var engine = new BattleEngine(db, setup);
                    var events = BattleTestUtil.RunAuto(engine, RoundCap);
                    string units = Snapshot(engine.Units.Select(u => new { u.Id, u.Hp, u.Mp, u.Tp, statuses = u.Statuses.Select(s => new { s.Id, s.TurnsRemaining }).ToArray() }));
                    string outcome = Snapshot(engine.Outcome), trace = Snapshot(events);
                    int paid = CampaignSim.PaidHeroMp(db, events, engine.Party.Select(h => h.Id));
                    var heroIds = new HashSet<string>(engine.Party.Select(h => h.Id));
                    int oracle = events.OfType<ActionStartEvent>().Where(a => heroIds.Contains(a.ActorId) && a.Kind == ActionKind.Skill && !a.IsChargeRelease && db.Skills[a.SkillId].MpCost > 0).Sum(a => db.Skills[a.SkillId].MpCost);
                    Assert.Equal(oracle, paid, "independent executed skill cost oracle");
                    Assert.Equal(before, SaveCodec.Serialize(state), "battle/ledger never mutates campaign before settlement");
                    Assert.Equal(units, Snapshot(engine.Units.Select(u => new { u.Id, u.Hp, u.Mp, u.Tp, statuses = u.Statuses.Select(s => new { s.Id, s.TurnsRemaining }).ToArray() })), "ledger engine purity");
                    Assert.Equal(outcome, Snapshot(engine.Outcome), "ledger outcome purity"); Assert.Equal(trace, Snapshot(events), "ledger event purity");
                    var replay = new BattleEngine(db, setup); var replayEvents = BattleTestUtil.RunAuto(replay, RoundCap);
                    Assert.Equal(string.Join("\n", events.Select(BattleTestUtil.Describe)), string.Join("\n", replayEvents.Select(BattleTestUtil.Describe)), "paired immutable event trace");
                    Assert.Equal(outcome, Snapshot(replay.Outcome), "paired raw outcome");
                    if (engine.State != BattleEngineState.Ended) break;
                    PartyStats.ApplyBattleOutcome(db, state, engine.Outcome);
                    string settled = SaveCodec.Serialize(state); VerifySetup(db, state, Setup(db, state, trip, fight + 1));
                    Assert.Equal(settled, SaveCodec.Serialize(state), "next setup is pure");
                    if (engine.Outcome.Result != BattleResult.Victory) break;
                }
            }
        }

        [LogicTest]
        public static void ExplicitDamagedLevelUpKoAndFailureSettlementRules()
        {
            var db = TestMain.DB; var state = Starter(db); var before = SaveCodec.Deserialize(SaveCodec.Serialize(state), db);
            var outcome = new BattleOutcome { Result = BattleResult.Victory, Experience = PartyStats.XpToNext(1), Gold = 17 };
            foreach (var h in state.Party)
            {
                outcome.FinalHp[h.Id] = h == state.Party[0] ? 0 : 9;
                outcome.FinalMp[h.Id] = 1; outcome.FinalTp[h.Id] = 37;
                outcome.FinalStatuses[h.Id] = new Dictionary<string, int> { { "poison", 1 } };
            }
            outcome.SeenEnemies.Add("slime"); outcome.DefeatedEnemies.Add("slime"); outcome.DiscoveredWeaknesses.Add("slime:4"); outcome.Drops["healing_potion"] = 2;
            var report = PartyStats.ApplyBattleOutcome(db, state, outcome);
            VerifySettlement(db, before, state, outcome, report);
            Assert.Equal(0, state.Party[0].Hp, "KO remains KO"); Assert.Equal(1, state.Party[0].Level, "KO receives no XP");
            Assert.True(state.Party.Skip(1).All(h => h.Level == 2 && h.Hp < PartyStats.EffectiveStats(db, h).MaxHp && h.Mp < PartyStats.EffectiveStats(db, h).MaxMp), "damaged low-MP levelup not full heal");
            Assert.Equal(5, state.ItemCount("healing_potion"), "initial potions plus earned drops"); Assert.Equal(1, state.ItemCount("return_stone"), "initial returnstone retained");
            var failed = Starter(db); var failedBefore = SaveCodec.Deserialize(SaveCodec.Serialize(failed), db);
            outcome.Result = BattleResult.Defeat; outcome.Gold = 999;
            var noReward = PartyStats.ApplyBattleOutcome(db, failed, outcome); VerifySettlement(db, failedBefore, failed, outcome, noReward);
            Assert.Equal(0, failed.TotalWins, "failed endpoint not a victory"); Assert.Equal(150, failed.Gold, "failed outcome has no rewards");
            var timeoutState = Starter(db); string pristine = SaveCodec.Serialize(timeoutState);
            var timeoutEngine = new BattleEngine(db, Setup(db, timeoutState, 0, 0)); BattleTestUtil.RunAuto(timeoutEngine, 0);
            Assert.True(timeoutEngine.State != BattleEngineState.Ended, "explicit cap retains failure denominator");
            Assert.Equal(pristine, SaveCodec.Serialize(timeoutState), "unfinished outcome not settled or rewarded");
        }
    }
}
