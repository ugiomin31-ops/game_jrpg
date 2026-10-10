// Campaign party model for balance simulations: the four starting hunters at a zone's level, wearing the best gear the
// guild market offers in that zone (chosen by rule from equipment.json, never by id) and carrying its consumables.
// "Chapter" below is the zone (1-12, 13 = the red gate); the market tier advances every two zones (MarketTier).
using System;
using System.Collections.Generic;
using System.Linq;
using Abyss.Logic;
using Abyss.Logic.Battle;
using Abyss.Logic.Game;

namespace Abyss.LogicTests
{
    public static class CampaignSim
    {
        public const int FloorsPerChapter = GameFlow.FloorsPerChapter;

        /// <summary>Chapter (1-based) of a floor index.</summary>
        public static int Chapter(int floorIndex) => floorIndex / FloorsPerChapter + 1;

        /// <summary>Main-path party level on a floor: the zone's range spread over its three floors.</summary>
        public static int FloorLevel(int floorIndex)
        {
            int c = Math.Min(SpecIds.ChapterLevels.Length, Chapter(floorIndex));
            int k = floorIndex % FloorsPerChapter;
            int lo = SpecIds.ChapterLevels[c - 1][0], hi = SpecIds.ChapterLevels[c - 1][1];
            return (int)Math.Round(lo + (hi - lo) * (k + 0.5) / FloorsPerChapter, MidpointRounding.AwayFromZero);
        }

        /// <summary>Guild market tier (shop_tier) open in a zone: one tier per two zones, 7 for the red gate.</summary>
        public static int MarketTier(int zone) => Math.Min(TownServices.MaxChapter, (zone + 1) / 2);

        /// <summary>Level the party fights a zone boss at (one below the zone's exit level).</summary>
        public static int BossLevel(int chapter) => SpecIds.ChapterLevels[chapter - 1][1] - 1;

        /// <summary>
        /// Gear a party owns in chapter <paramref name="chapter"/>: every piece sold up to that shop tier (shop_tier 1..c),
        /// plus legendary pieces (rarity 3, not sold) when <paramref name="legendary"/>. Job signature weapons are skipped
        /// (they need a class change).
        /// </summary>
        public static IEnumerable<EquipmentDef> Available(GameDB db, int chapter, bool legendary)
        {
            foreach (var piece in db.Equipment.Values)
            {
                if (SpecIds.JobWeapons.Contains(piece.Id)) continue;
                bool sold = piece.ShopTier >= 1 && piece.ShopTier <= MarketTier(chapter);
                bool legend = legendary && piece.Rarity >= 3;
                if (sold || legend) yield return piece;
            }
        }

        static double Score(HeroDef hero, EquipmentDef p)
        {
            double atkW = hero.AtkGrowth >= hero.MagGrowth ? 1.0 : 0.3, magW = hero.MagGrowth > hero.AtkGrowth ? 1.0 : 0.15;
            return p.Atk * atkW + p.Mag * magW + p.Def * 0.7 + p.Res * 0.6 + p.Hp * 0.12 + p.Mp * 0.05 + p.Spd * 0.6
                + (p.Crit + p.Hit + p.Evade) * 60 + p.ElementResists.Count * 2 + p.StatusImmunities.Count * 1.5;
        }

        /// <summary>Best consumable of a type a chapter's shop sells (by effect size).</summary>
        static string BestItem(GameDB db, int chapter, ItemType type)
        {
            ItemDef best = null;
            foreach (var item in db.Items.Values)
            {
                if (item.ItemType != type || item.ShopTier < 1 || item.ShopTier > MarketTier(chapter)) continue;
                if (item.Target != "single_ally" || item.HealAmount >= 5000) continue; // no full-party / full-heal elixirs
                if (best == null || item.HealAmount + item.Power * 100 > best.HealAmount + best.Power * 100
                    || (item.HealAmount + item.Power * 100 == best.HealAmount + best.Power * 100 && item.Price > best.Price)) best = item;
            }
            return best?.Id;
        }

        /// <summary>
        /// Forging level of the expected player per market tier (index = MarketTier(zone) - 1), applied to every worn piece.
        /// Derived from the game's economy (estimated from Resources/Data: random fights, events, FOEs, bosses, chests and quest
        /// rewards; enhance stones from drops and from the shop at 80 / 450 / 1600 gold from chapter 1 / 3 / 5):
        /// - gold earned through each chapter: 16k, 56k, 125k, 247k, 427k, 711k, 1.25M;
        /// - the player spends at most 25 % of that gold on forging and buys the stones it lacks at the shop;
        /// - all 12 worn pieces (3 slots x 4 heroes, no shared ids, the expensive case) go to the same level;
        /// - +L costs TierGold[tier] x L(L+1)/2 gold per piece and 1 + (l-1)/3 stones per step l (Enhancement.CostOf).
        /// The highest level that fits the budget for the tier worn in each chapter (T2, T3, T4, T5, T6, T7, T7) is 3, 4, 3, 4, 3, 4, 6.
        /// The dips at chapters 3 and 5 are the stone grades: hi stones cost 450 and abyss stones 1600 each in the shop.
        /// Superbosses are the exception: the postgame player forges legendary pieces to +10 (Enhancement.MaxLevel) on purpose.
        /// </summary>
        public static readonly int[] ExpectedForge = { 3, 4, 3, 4, 3, 4, 6 };

        /// <summary>
        /// Job a player has reached in <paramref name="chapter"/> at <paramref name="level"/>: each class change in jobs.json
        /// order (the first listed branch) once its level (RequiredLevel: 12 advanced, 36 top) is reached AND the zone boss
        /// it requires (RequiredBoss: the zone 2 boss for the advanced job, the zone 7 boss for the top job) was defeated before
        /// this zone's fights, i.e. that boss's zone is earlier than <paramref name="chapter"/>. Random, FOE and boss fights
        /// of a zone all use the same gate, so the expected party is advanced from zone 3, top from zone 8.
        /// </summary>
        static void Promote(GameDB db, HeroState hero, int chapter)
        {
            for (var next = JobService.NextJobs(db, hero); next.Count > 0; next = JobService.NextJobs(db, hero))
            {
                var job = next[0];
                bool bossDone = string.IsNullOrEmpty(job.RequiredBoss) || Array.IndexOf(SpecIds.ChapterBosses, job.RequiredBoss) + 1 < chapter;
                if (job.RequiredLevel > hero.Level || !bossDone) return;
                hero.Job = job.Id;
            }
        }

        /// <summary>
        /// A campaign state with the party at <paramref name="level"/> and chapter gear/items. The default is the under-prepared
        /// player: base jobs, no forging. <paramref name="jobs"/> adds the class changes (see <see cref="Promote"/>) and the job
        /// signature weapons a promoted hero can craft (tier up to the chapter's sold tier, like the shop); <paramref name="forge"/>
        /// sets every worn piece to that enhancement level.
        /// </summary>
        public static GameState Party(GameDB db, int level, int chapter, bool legendary = false, Difficulty difficulty = Difficulty.Normal,
            bool jobs = false, int forge = 0)
        {
            var state = GameState.NewGame(db, difficulty);
            state.Inventory.Clear();
            var pool = Available(db, chapter, legendary).ToList();
            if (jobs) pool.AddRange(db.Equipment.Values.Where(p => SpecIds.JobWeapons.Contains(p.Id) && p.Tier <= MarketTier(chapter) + 1));
            foreach (var hero in state.Party)
            {
                hero.Level = level;
                if (jobs) Promote(db, hero, chapter);
                var def = db.Heroes[hero.Id];
                foreach (string slot in GameState.EquipSlots)
                {
                    var best = pool.Where(p => p.Slot == slot && PartyStats.AllowsClass(db, p, hero.Id) && (!jobs || PartyStats.AllowsJob(db, p, hero)))
                        .OrderByDescending(p => Score(def, p)).ThenBy(p => p.Id, StringComparer.Ordinal).FirstOrDefault();
                    if (best != null) hero.Equipment[slot] = best.Id;
                }
                hero.Hp = -1; hero.Mp = -1;
            }
            if (forge > 0)
                foreach (var hero in state.Party)
                    foreach (string slot in GameState.EquipSlots)
                        if (hero.Equipped(slot) != "") state.Enhancements[hero.Equipped(slot)] = Math.Min(Enhancement.MaxLevel, forge);
            foreach (var (type, count) in new[] { (ItemType.Healing, 6), (ItemType.MpRestore, 3), (ItemType.Revive, 2), (ItemType.Cure, 2) })
            {
                string id = BestItem(db, chapter, type);
                if (id != null) state.AddItem(id, count);
            }
            state.Repair(db);
            return state;
        }

        public sealed class Vitals
        {
            public string Id, UnitId;
            public int Hp, Mp, Tp, MaxHp, MaxMp;
            public Dictionary<string, int> Statuses = new Dictionary<string, int>();
            public static Vitals Of(BattleUnit u) => new Vitals
            {
                Id = u.DefId, UnitId = u.Id, Hp = u.Hp, Mp = u.Mp, Tp = u.IsAlive ? u.Tp : 0,
                MaxHp = u.MaxHp, MaxMp = u.MaxMp,
                Statuses = u.IsAlive ? u.Statuses.Where(s => s.TurnsRemaining > 0).ToDictionary(s => s.Id, s => s.TurnsRemaining)
                    : new Dictionary<string, int>(),
            };
            public override string ToString() => $"{Id}:{Hp}/{MaxHp}hp,{Mp}/{MaxMp}mp,{Tp}tp";
        }

        public sealed class Sample
        {
            public BattleResult Outcome;
            public int Rounds, GrossMpSpent;
            public bool TimedOut;
            public List<Vitals> Start, End;
            public int HpLost => Start.Sum(s => Math.Max(0, s.Hp - End.Single(e => e.Id == s.Id).Hp));
            public int NetMpDepletion => Start.Sum(s => s.Mp - End.Single(e => e.Id == s.Id).Mp);
            public int InitialCapacity => Start.Sum(s => s.MaxHp + s.MaxMp);
            public double Attrition => InitialCapacity == 0 ? 0 : (double)(HpLost + GrossMpSpent) / InitialCapacity;
            public bool Won => !TimedOut && Outcome == BattleResult.Victory;
        }

        public sealed class Result
        {
            public int Battles, Wins, Rounds, Timeouts;
            public long HpLost, GrossMpSpent, NetMpDepletion;
            public double AttritionSum;
            public double WinRate => Battles == 0 ? 0 : (double)Wins / Battles;
            public double AvgRounds => Wins == 0 ? 0 : (double)Rounds / Wins;
            // Every initial sample counts, including defeats/flees/timeouts; sample-normalized arithmetic mean.
            public double AvgAttrition => Battles == 0 ? 0 : AttritionSum / Battles;
            public void Record(Sample sample)
            {
                Battles++;
                if (sample.Won) { Wins++; Rounds += sample.Rounds; }
                if (sample.TimedOut) Timeouts++;
                HpLost += sample.HpLost; GrossMpSpent += sample.GrossMpSpent; NetMpDepletion += sample.NetMpDepletion;
                AttritionSum += sample.Attrition;
            }
            public void Merge(Result other)
            {
                Battles += other.Battles; Wins += other.Wins; Rounds += other.Rounds; Timeouts += other.Timeouts;
                HpLost += other.HpLost; GrossMpSpent += other.GrossMpSpent; NetMpDepletion += other.NetMpDepletion;
                AttritionSum += other.AttritionSum;
            }
            public string Resources => Battles == 0 ? "-" : $"n={Battles} wins={Wins} rounds={Rounds} attr={AvgAttrition:P2} HP_loss={HpLost} MP_paid={GrossMpSpent} MP_net={NetMpDepletion} timeout={Timeouts}";
            public override string ToString() => Battles == 0 ? "-" : $"{WinRate * 100,3:0}% {AvgRounds,4:0.0}r";
        }

        /// <summary>
        /// Execute emits the paid-cost MP event immediately after Skill ActionStart, before its payload. Count that
        /// action-linked actual delta once, not subsequent mana-shield damage, regen or restoration events. No RNG queries.
        /// </summary>
        public static int PaidHeroMp(GameDB db, IEnumerable<BattleEvent> events, IEnumerable<string> heroUnitIds)
        {
            var heroes = new HashSet<string>(heroUnitIds);
            ActionStartEvent payment = null;
            int total = 0;
            foreach (var e in events)
            {
                if (payment != null)
                {
                    Assert.True(e is MpChangeEvent cost && cost.UnitId == payment.ActorId && cost.Delta < 0,
                        "every executed positive-cost hero skill has an immediate actual payment event");
                    var mp = (MpChangeEvent)e;
                    Assert.Equal(Math.Max(0, db.Skills[payment.SkillId].MpCost), -mp.Delta, "action-linked paid MP equals cost");
                    total -= mp.Delta;
                }
                payment = e is ActionStartEvent a && a.Kind == ActionKind.Skill && heroes.Contains(a.ActorId)
                    && !a.IsChargeRelease && db.Skills[a.SkillId].MpCost > 0 ? a : null;
            }
            Assert.True(payment == null, "event stream cannot truncate a pending hero payment");
            return total;
        }

        /// <summary>Runs without campaign settlement; even incomplete battles retain their actual resource endpoint.</summary>
        public static Sample Measure(GameDB db, BattleSetup setup, int maxRounds = 120)
        {
            var engine = new BattleEngine(db, setup);
            var start = engine.Party.Select(Vitals.Of).ToList();
            var events = BattleTestUtil.RunAuto(engine, maxRounds);
            bool ended = engine.State == BattleEngineState.Ended;
            Assert.True(ended || engine.Round > maxRounds, "battle ends or is recorded as timeout");
            return new Sample
            {
                Outcome = ended ? engine.Outcome.Result : BattleResult.None, TimedOut = !ended, Rounds = engine.Round,
                Start = start, End = engine.Party.Select(Vitals.Of).ToList(),
                GrossMpSpent = PaidHeroMp(db, events, start.Select(s => s.UnitId)),
            };
        }

        /// <summary>AUTO cold-start battles; the caller's fixed party is never settled or mutated.</summary>
        public static void Fight(GameDB db, GameState party, IList<string> group, BattleKind kind, float power, string floorId, int seed, Result into)
        {
            var setup = PartyStats.BuildBattleSetup(db, party, kind, group, power, floorId, seed);
            foreach (var h in setup.Party) { h.Hp = h.MaxHp; h.Mp = h.MaxMp; h.Tp = 0; }
            into.Record(Measure(db, setup));
        }

        // Original expected cold-start seed is the trip seed. Subsequent fights add this fixed stride, never advance
        // the original shared sample counter. Group j advances cyclically through that floor's original distinct groups.
        public const int TripFights = 4, TripSeedStride = 1000000;
        public static int TripSeed(int originalSeed, int fight) => originalSeed + fight * TripSeedStride;

        public static void Carry(BattleSetup setup, Sample previous)
        {
            foreach (var h in setup.Party)
            {
                var end = previous.End.Single(e => e.Id == h.HeroId);
                h.Hp = end.Hp; h.Mp = end.Mp; h.Tp = end.Tp;
                h.Statuses = new Dictionary<string, int>(end.Statuses);
            }
        }

        public sealed class Trip
        {
            public readonly List<Sample> Fights = new List<Sample>();
            public bool Complete => Fights.Count == TripFights && Fights.All(f => f.Won);
            public double RemainingHp => (double)Fights.Last().End.Sum(e => e.Hp) / Fights[0].Start.Sum(s => s.MaxHp);
            public double RemainingMp => Fights[0].Start.Sum(s => s.MaxMp) == 0 ? 1
                : (double)Fights.Last().End.Sum(e => e.Mp) / Fights[0].Start.Sum(s => s.MaxMp);
        }

        /// <summary>No items, rest, rewards, XP, newly favourable knowledge, or between-fight healing. KO stays KO.</summary>
        public static Trip SerialTrip(GameDB db, GameState party, IList<List<string>> groups, int groupIndex, string floorId, int originalSeed)
        {
            var trip = new Trip();
            for (int fight = 0; fight < TripFights; fight++)
            {
                var setup = PartyStats.BuildBattleSetup(db, party, BattleKind.Random, groups[(groupIndex + fight) % groups.Count],
                    1f, floorId, TripSeed(originalSeed, fight));
                setup.Inventory.Clear();
                if (fight == 0) foreach (var h in setup.Party) { h.Hp = h.MaxHp; h.Mp = h.MaxMp; h.Tp = 0; }
                else Carry(setup, trip.Fights.Last()); // Engine applies O7 max(carried TP, gear TP) on every battle start.
                var result = Measure(db, setup);
                trip.Fights.Add(result);
                if (!result.Won) break;
            }
            return trip;
        }

        public static double Median(IEnumerable<double> values)
        {
            var sorted = values.OrderBy(x => x).ToArray();
            Assert.True(sorted.Length > 0, "median includes every trip endpoint");
            int mid = sorted.Length / 2;
            return sorted.Length % 2 == 0 ? (sorted[mid - 1] + sorted[mid]) / 2 : sorted[mid];
        }
    }
}
