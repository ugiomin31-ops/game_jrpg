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

        public sealed class Result
        {
            public int Battles, Wins, Rounds;
            public double WinRate => Battles == 0 ? 0 : (double)Wins / Battles;
            public double AvgRounds => Wins == 0 ? 0 : (double)Rounds / Wins;
            public override string ToString() => Battles == 0 ? "-" : $"{WinRate * 100,3:0}% {AvgRounds,4:0.0}r";
        }

        /// <summary>AUTO battles of <paramref name="group"/>; rounds are averaged over victories.</summary>
        public static void Fight(GameDB db, GameState party, IList<string> group, BattleKind kind, float power, string floorId, int seed, Result into)
        {
            var setup = PartyStats.BuildBattleSetup(db, party, kind, group, power, floorId, seed);
            var engine = new BattleEngine(db, setup);
            BattleTestUtil.RunAuto(engine, 120);
            Assert.True(engine.State == BattleEngineState.Ended || engine.Round > 120, "battle ends: " + string.Join(",", group));
            into.Battles++;
            if (engine.State == BattleEngineState.Ended && engine.Outcome.Result == BattleResult.Victory) { into.Wins++; into.Rounds += engine.Round; }
        }
    }
}
