// Smithy enhancement +0..+10 (CONTENT_20H_PLAN "강화").
//
// Rule: one enhancement level per equipment ID, shared by every copy the party owns (GameState.Enhancements).
// Owning two 무쇠 장검 and enhancing to +3 makes both +3. This keeps the bag a plain id -> count map, so buying,
// selling, crafting, chest rewards and old saves need no instance tracking; a save without the map loads as all +0.
//
// Each level adds 10 % of the piece's base integer stats (positive stats only; negative trade-offs such as the
// berserker ring's -DEF and the float rates hit/evade/crit stay as authored): bonus = round(base x 0.1 x level).
// Enhancing never fails or breaks the piece. Cost per step to level L (1..10): enhance stones of the piece's tier grade
// (T1-T3 강화석, T4-T5 상급 강화석, T6-T8 심연 강화석), count 1 + (L-1)/3, plus TierGold[tier] x L gold.
using System;
using System.Collections.Generic;

namespace Abyss.Logic.Game
{
    /// <summary>Price of one enhancement step.</summary>
    public sealed class EnhanceCost
    {
        public string StoneId;
        public int Stones;
        public int Gold;
    }

    /// <summary>One smithy enhancement row (owned piece).</summary>
    public sealed class EnhanceEntry
    {
        public EquipmentDef Equipment;
        public int Level;
        /// <summary>Cost of the next step (null at the maximum).</summary>
        public EnhanceCost Cost;
        public int StonesOwned;
        public bool CanEnhance;
        /// <summary>Pieces of this id owned (bag + worn).</summary>
        public int Owned;
    }

    public static class Enhancement
    {
        public const int MaxLevel = 10;
        public const double StepRatio = 0.1;
        public const string Stone = "enhance_stone", StoneHigh = "enhance_stone_hi", StoneAbyss = "enhance_stone_abyss";
        static readonly int[] TierGold = { 0, 20, 40, 80, 150, 250, 400, 600, 900 };

        /// <summary>Enhancement level of an equipment id in this campaign (0 when never enhanced).</summary>
        public static int LevelOf(GameState state, string equipmentId) =>
            state?.Enhancements != null && equipmentId != null && state.Enhancements.TryGetValue(equipmentId, out int n) ? Clamp(n) : 0;

        /// <summary>Level as seen by a hero's stat calculation (the shared map the hero was bound to by <see cref="GameState.Repair"/>).</summary>
        public static int LevelOf(HeroState hero, string equipmentId) =>
            hero?.EnhanceLevels != null && equipmentId != null && hero.EnhanceLevels.TryGetValue(equipmentId, out int n) ? Clamp(n) : 0;

        static int Clamp(int n) => Math.Max(0, Math.Min(MaxLevel, n));

        /// <summary>Integer bonus of one base stat at a level.</summary>
        public static int Bonus(int baseValue, int level) => baseValue <= 0 || level <= 0 ? 0 : PartyStats.RoundI(baseValue * StepRatio * Clamp(level));

        /// <summary>The piece's integer stats at an enhancement level (base + bonus).</summary>
        public static StatBlock Stats(EquipmentDef piece, int level) => new StatBlock
        {
            MaxHp = piece.Hp + Bonus(piece.Hp, level), MaxMp = piece.Mp + Bonus(piece.Mp, level),
            Attack = piece.Atk + Bonus(piece.Atk, level), Magic = piece.Mag + Bonus(piece.Mag, level),
            Defense = piece.Def + Bonus(piece.Def, level), Resistance = piece.Res + Bonus(piece.Res, level),
            Speed = piece.Spd + Bonus(piece.Spd, level),
        };

        /// <summary>Stone grade for a tier.</summary>
        public static string StoneFor(int tier) => tier >= 6 ? StoneAbyss : tier >= 4 ? StoneHigh : Stone;

        /// <summary>Cost of enhancing a piece from <paramref name="currentLevel"/> to the next level; null at the maximum.</summary>
        public static EnhanceCost CostOf(EquipmentDef piece, int currentLevel)
        {
            if (piece == null || currentLevel >= MaxLevel) return null;
            int next = Clamp(currentLevel) + 1;
            int tier = Math.Max(1, Math.Min(8, piece.Tier));
            return new EnhanceCost { StoneId = StoneFor(tier), Stones = 1 + (next - 1) / 3, Gold = TierGold[tier] * next };
        }

        /// <summary>"무쇠 장검 +3" (plain name at +0).</summary>
        public static string DisplayName(EquipmentDef piece, int level) => piece == null ? "" : level > 0 ? piece.DisplayName + " +" + level : piece.DisplayName;

        public static string DisplayName(GameDB db, GameState state, string equipmentId) =>
            db.Equipment.TryGetValue(equipmentId ?? "", out var piece) ? DisplayName(piece, LevelOf(state, equipmentId)) : equipmentId ?? "";

        /// <summary>Copies of an id the party owns (bag + worn).</summary>
        public static int OwnedCount(GameState state, string equipmentId) => state.BagCount(equipmentId) + PartyStats.EquippedCount(state, equipmentId);

        /// <summary>Owned pieces in tier, slot, id order with their next-step cost.</summary>
        public static List<EnhanceEntry> Candidates(GameDB db, GameState state)
        {
            var ids = new HashSet<string>(StringComparer.Ordinal);
            foreach (var kv in state.EquipmentBag) if (kv.Value > 0) ids.Add(kv.Key);
            foreach (var hero in state.Party) foreach (string slot in GameState.EquipSlots) if (hero.Equipped(slot) != "") ids.Add(hero.Equipped(slot));
            var output = new List<EnhanceEntry>();
            foreach (string id in ids)
            {
                if (!db.Equipment.TryGetValue(id, out var piece)) continue;
                int level = LevelOf(state, id);
                var cost = CostOf(piece, level);
                var entry = new EnhanceEntry { Equipment = piece, Level = level, Cost = cost, Owned = OwnedCount(state, id) };
                entry.StonesOwned = cost == null ? 0 : state.ItemCount(cost.StoneId);
                entry.CanEnhance = cost != null && entry.StonesOwned >= cost.Stones && state.Gold >= cost.Gold;
                output.Add(entry);
            }
            output.Sort((a, b) =>
            {
                int sa = Array.IndexOf(GameState.EquipSlots, a.Equipment.Slot), sb = Array.IndexOf(GameState.EquipSlots, b.Equipment.Slot);
                if (sa != sb) return sa.CompareTo(sb);
                if (a.Equipment.Tier != b.Equipment.Tier) return b.Equipment.Tier.CompareTo(a.Equipment.Tier);
                return string.CompareOrdinal(a.Equipment.Id, b.Equipment.Id);
            });
            return output;
        }

        /// <summary>
        /// Raises an owned piece by one level (never fails once paid). Reasons: unknown_equipment, not_owned, max_enhance,
        /// missing_stones, not_enough_gold. Worn copies keep their HP/MP within the new maxima.
        /// </summary>
        public static ServiceResult Enhance(GameDB db, GameState state, string equipmentId)
        {
            if (!db.Equipment.TryGetValue(equipmentId ?? "", out var piece)) return ServiceResult.Fail("unknown_equipment");
            if (OwnedCount(state, equipmentId) <= 0) return ServiceResult.Fail("not_owned");
            int level = LevelOf(state, equipmentId);
            var cost = CostOf(piece, level);
            if (cost == null) return ServiceResult.Fail("max_enhance");
            if (state.ItemCount(cost.StoneId) < cost.Stones) return ServiceResult.Fail("missing_stones");
            if (state.Gold < cost.Gold) return ServiceResult.Fail("not_enough_gold");
            state.RemoveItem(cost.StoneId, cost.Stones);
            state.Gold -= cost.Gold;
            state.Enhancements[equipmentId] = level + 1;
            foreach (var hero in state.Party) PartyStats.ClampVitals(db, hero);
            QuestLog.Refresh(db, state);
            var result = ServiceResult.Ok("enhanced", DisplayName(piece, level + 1));
            result.GoldDelta = -cost.Gold;
            return result;
        }
    }
}
