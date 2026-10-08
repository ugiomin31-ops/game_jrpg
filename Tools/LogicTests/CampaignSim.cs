// Campaign party model for balance simulations: heroes at a chapter's level, wearing the best gear the data offers
// for that chapter (chosen by rule from equipment.json, never by id) and carrying the chapter's consumables.
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
        public const int FloorsPerChapter = 5;

        /// <summary>Chapter (1-based) of a floor index.</summary>
        public static int Chapter(int floorIndex) => floorIndex / FloorsPerChapter + 1;

        /// <summary>Main-path party level on a floor: the chapter's range spread over its five floors.</summary>
        public static int FloorLevel(int floorIndex)
        {
            int c = Math.Min(SpecIds.ChapterLevels.Length, Chapter(floorIndex));
            int k = floorIndex % FloorsPerChapter;
            int lo = SpecIds.ChapterLevels[c - 1][0], hi = SpecIds.ChapterLevels[c - 1][1];
            return (int)Math.Round(lo + (hi - lo) * (k + 0.5) / FloorsPerChapter, MidpointRounding.AwayFromZero);
        }

        /// <summary>Level the party fights a chapter boss at (one below the chapter's exit level).</summary>
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
                bool sold = piece.ShopTier >= 1 && piece.ShopTier <= chapter;
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
                if (item.ItemType != type || item.ShopTier < 1 || item.ShopTier > chapter) continue;
                if (item.Target != "single_ally" || item.HealAmount >= 5000) continue; // no full-party / full-heal elixirs
                if (best == null || item.HealAmount + item.Power * 100 > best.HealAmount + best.Power * 100
                    || (item.HealAmount + item.Power * 100 == best.HealAmount + best.Power * 100 && item.Price > best.Price)) best = item;
            }
            return best?.Id;
        }

        /// <summary>A Normal-difficulty campaign state with the party at <paramref name="level"/> and chapter gear/items.</summary>
        public static GameState Party(GameDB db, int level, int chapter, bool legendary = false, Difficulty difficulty = Difficulty.Normal)
        {
            var state = GameState.NewGame(db, difficulty);
            state.Inventory.Clear();
            var pool = Available(db, chapter, legendary).ToList();
            foreach (var hero in state.Party)
            {
                hero.Level = level;
                var def = db.Heroes[hero.Id];
                foreach (string slot in GameState.EquipSlots)
                {
                    var best = pool.Where(p => p.Slot == slot && PartyStats.AllowsClass(p, hero.Id))
                        .OrderByDescending(p => Score(def, p)).ThenBy(p => p.Id, StringComparer.Ordinal).FirstOrDefault();
                    if (best != null) hero.Equipment[slot] = best.Id;
                }
                hero.Hp = -1; hero.Mp = -1;
            }
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
