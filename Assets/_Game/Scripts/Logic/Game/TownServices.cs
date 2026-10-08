// Town services of 여명의 마을: inn, shop, smithy, guild board, bestiary and departure.
// Port of scripts/town/*.gd + the economy half of game_state.gd. CONTENT_DESIGN §10.
using System;
using System.Collections.Generic;

namespace Abyss.Logic.Game
{
    /// <summary>
    /// Result of a town/party service call. <see cref="TextKey"/> is a text_ko key ("reason_*" on failure);
    /// format with <see cref="Message"/>.
    /// </summary>
    public sealed class ServiceResult
    {
        public bool Success;
        /// <summary>Failure reason id (e.g. "not_enough_gold"); "" on success.</summary>
        public string Reason = "";
        public string TextKey = "";
        public object[] Args = Array.Empty<object>();
        /// <summary>Gold gained (positive) or spent (negative).</summary>
        public int GoldDelta;
        /// <summary>The Unity layer must autosave now (inn rest).</summary>
        public bool RequestsAutosave;

        public static ServiceResult Ok(string textKey, params object[] args) => new ServiceResult { Success = true, TextKey = textKey, Args = args };
        public static ServiceResult Fail(string reason) => new ServiceResult { Success = false, Reason = reason, TextKey = "reason_" + reason };

        /// <summary>Localised message.</summary>
        public string Message(GameDB db) => Args.Length == 0 ? db.T(TextKey) : db.T(TextKey, Args);
    }

    /// <summary>One purchasable row of the shop.</summary>
    public sealed class ShopEntry
    {
        public string Id;
        public bool IsEquipment;
        public string DisplayName;
        public int Price;
        public int ShopTier;
        /// <summary>False for rows of a higher tier than unlocked (shown in the "next exploration" section).</summary>
        public bool Unlocked;
    }

    /// <summary>One smithy recipe row.</summary>
    public sealed class RecipeEntry
    {
        public EquipmentDef Equipment;
        public int Gold;
        /// <summary>material id -> (have, need).</summary>
        public List<(string ItemId, int Have, int Need)> Materials = new List<(string, int, int)>();
        public bool CanCraft;
    }

    /// <summary>One Guild board row.</summary>
    public sealed class QuestBoardEntry
    {
        public QuestDef Quest;
        public QuestBoardState State;
        public int Progress;
        public int Count;
    }

    /// <summary>One bestiary row.</summary>
    public sealed class BestiaryRow
    {
        public EnemyDef Enemy;
        public bool Seen;
        public int Kills;
        /// <summary>Discovered element ints that really are weaknesses of the enemy.</summary>
        public List<int> RevealedWeaknesses = new List<int>();
        /// <summary>Weaknesses not yet discovered (UI shows one "?" when &gt; 0).</summary>
        public int HiddenWeaknesses;
        /// <summary>Drops are public after the first kill.</summary>
        public bool DropsRevealed;
        public bool IsBoss => Enemy.IsBoss;
        public bool IsElite => Enemy.Rank > 0 && !Enemy.IsBoss;
    }

    /// <summary>Town service rules. Every mutating call returns a <see cref="ServiceResult"/>; failures change nothing.</summary>
    public static class TownServices
    {
        /// <summary>Defeat gold-loss ratio per difficulty (easy keeps all gold).</summary>
        public static float DefeatGoldLoss(Difficulty d) => d == Difficulty.Easy ? 0f : 0.5f;

        // ------------------------------------------------------------------ inn

        /// <summary>Inn price: 10 + round(4 × average party level) (14 at Lv1, 50 at Lv10).</summary>
        public static int InnCost(GameState state)
        {
            if (state.Party.Count == 0) return 10;
            int total = 0;
            foreach (var hero in state.Party) total += Math.Max(1, Math.Min(GameState.LevelCap, hero.Level));
            return 10 + PartyStats.RoundI(4.0 * total / state.Party.Count);
        }

        /// <summary>
        /// Rests at the inn: full HP/MP, revive, clear statuses, respawn every FOE (treasures, doors, keys, warps stay).
        /// <paramref name="free"/> skips the price (defeat recovery). Sets <see cref="ServiceResult.RequestsAutosave"/>.
        /// </summary>
        public static ServiceResult RestAtInn(GameDB db, GameState state, bool free = false)
        {
            int cost = free ? 0 : InnCost(state);
            if (state.Gold < cost) return ServiceResult.Fail("not_enough_gold");
            state.Gold -= cost;
            PartyStats.RestoreParty(db, state);
            foreach (var floor in state.Floors.Values) floor.DefeatedFoes.Clear();
            var result = ServiceResult.Ok("inn_rested");
            result.GoldDelta = -cost;
            result.RequestsAutosave = true;
            return result;
        }

        // ------------------------------------------------------------------ shop

        /// <summary>Floors per chapter (Tools/content/spec.py CHAPTERS: 6 chapters of 5 floors, then the postgame).</summary>
        public const int FloorsPerChapter = 5;
        /// <summary>Highest chapter / shop tier (7 = postgame 시련의 회랑).</summary>
        public const int MaxChapter = 7;

        /// <summary>Chapter 1..7 of a floor index (B1F-B5F = 1, ..., B31F+ = 7).</summary>
        public static int ChapterOfFloor(int floorIndex) => Math.Max(1, Math.Min(MaxChapter, floorIndex / FloorsPerChapter + 1));

        /// <summary>
        /// Unlocked shop tier = chapter reached (1..7); clearing the game opens tier 7. Equipment tiers T1-T2 sell at 1, T3 at 2 ...
        /// T7 at 6; T8 legendaries are never sold.
        /// </summary>
        public static int ShopTier(GameState state) =>
            state.Flags.Contains(GameFlow.FlagCleared) ? MaxChapter : ChapterOfFloor(state.DeepestFloor);

        /// <summary>
        /// Every item and equipment piece the shop ever sells (shop_tier ≥ 1, price &gt; 0), sorted by tier, price, id;
        /// rows above the unlocked tier have <see cref="ShopEntry.Unlocked"/> = false.
        /// </summary>
        public static List<ShopEntry> ShopStock(GameDB db, GameState state, bool equipment)
        {
            int tier = ShopTier(state);
            var output = new List<ShopEntry>();
            if (equipment)
            {
                foreach (var e in db.Equipment.Values)
                    if (e.ShopTier > 0 && e.Price > 0)
                        output.Add(new ShopEntry { Id = e.Id, IsEquipment = true, DisplayName = e.DisplayName, Price = e.Price, ShopTier = e.ShopTier, Unlocked = e.ShopTier <= tier });
            }
            else
            {
                foreach (var i in db.Items.Values)
                    if (i.ShopTier > 0 && i.Price > 0)
                        output.Add(new ShopEntry { Id = i.Id, DisplayName = i.DisplayName, Price = i.Price, ShopTier = i.ShopTier, Unlocked = i.ShopTier <= tier });
            }
            output.Sort((a, b) => a.ShopTier != b.ShopTier ? a.ShopTier.CompareTo(b.ShopTier) : a.Price != b.Price ? a.Price.CompareTo(b.Price) : string.CompareOrdinal(a.Id, b.Id));
            return output;
        }

        /// <summary>Sell value of one item: explicit sell_price, else half the price; key items are never sold.</summary>
        public static int ItemSellValue(GameDB db, string itemId) =>
            db.Items.TryGetValue(itemId, out var item) && item.ItemType != ItemType.Key ? (item.SellPrice > 0 ? item.SellPrice : item.Price / 2) : 0;

        /// <summary>Sell value of one equipment piece: explicit sell_price (≥ 0), else half the price.</summary>
        public static int EquipmentSellValue(GameDB db, string equipmentId) =>
            db.Equipment.TryGetValue(equipmentId, out var piece) ? (piece.SellPrice >= 0 ? piece.SellPrice : Math.Max(0, piece.Price / 2)) : 0;

        /// <summary>Buys <paramref name="count"/> items. Stack limit = min(max_stack, 99).</summary>
        public static ServiceResult BuyItem(GameDB db, GameState state, string itemId, int count = 1)
        {
            if (count < 1 || count > GameState.MaxStack) return ServiceResult.Fail("invalid_count");
            if (!db.Items.TryGetValue(itemId, out var item)) return ServiceResult.Fail("unknown_item");
            if (item.ShopTier <= 0 || item.Price <= 0) return ServiceResult.Fail("not_for_sale");
            if (item.ShopTier > ShopTier(state)) return ServiceResult.Fail("tier_locked");
            int total = item.Price * count;
            if (state.Gold < total) return ServiceResult.Fail("not_enough_gold");
            if (state.ItemCount(itemId) + count > Math.Min(Math.Max(1, item.MaxStack), GameState.MaxStack)) return ServiceResult.Fail("stack_full");
            state.Gold -= total;
            state.AddItem(itemId, count);
            QuestLog.Refresh(db, state);
            var result = ServiceResult.Ok("bought", item.DisplayName);
            result.GoldDelta = -total;
            return result;
        }

        /// <summary>Sells <paramref name="count"/> items from the inventory.</summary>
        public static ServiceResult SellItem(GameDB db, GameState state, string itemId, int count = 1)
        {
            if (count < 1 || count > GameState.MaxStack) return ServiceResult.Fail("invalid_count");
            if (!db.Items.TryGetValue(itemId, out var item)) return ServiceResult.Fail("unknown_item");
            if (state.ItemCount(itemId) < count) return ServiceResult.Fail("not_enough_items");
            int value = ItemSellValue(db, itemId);
            if (value <= 0) return ServiceResult.Fail("not_sellable");
            state.RemoveItem(itemId, count);
            state.Gold += value * count;
            QuestLog.Refresh(db, state);
            var result = ServiceResult.Ok("sold", item.DisplayName);
            result.GoldDelta = value * count;
            return result;
        }

        /// <summary>Buys equipment pieces into the bag.</summary>
        public static ServiceResult BuyEquipment(GameDB db, GameState state, string equipmentId, int count = 1)
        {
            if (count < 1 || count > GameState.MaxStack) return ServiceResult.Fail("invalid_count");
            if (!db.Equipment.TryGetValue(equipmentId, out var piece)) return ServiceResult.Fail("unknown_equipment");
            if (Array.IndexOf(GameState.EquipSlots, piece.Slot) < 0) return ServiceResult.Fail("invalid_slot");
            if (piece.ShopTier <= 0 || piece.Price <= 0) return ServiceResult.Fail("not_for_sale");
            if (piece.ShopTier > ShopTier(state)) return ServiceResult.Fail("tier_locked");
            int total = piece.Price * count;
            if (state.Gold < total) return ServiceResult.Fail("not_enough_gold");
            if (state.BagCount(equipmentId) + count > GameState.MaxStack) return ServiceResult.Fail("stack_full");
            state.Gold -= total;
            state.AddEquipment(equipmentId, count);
            var result = ServiceResult.Ok("bought", piece.DisplayName);
            result.GoldDelta = -total;
            return result;
        }

        /// <summary>Sells unequipped pieces from the bag (worn pieces must be unequipped first).</summary>
        public static ServiceResult SellEquipment(GameDB db, GameState state, string equipmentId, int count = 1)
        {
            if (count < 1 || count > GameState.MaxStack) return ServiceResult.Fail("invalid_count");
            if (!db.Equipment.TryGetValue(equipmentId, out var piece)) return ServiceResult.Fail("unknown_equipment");
            if (state.BagCount(equipmentId) < count) return ServiceResult.Fail("not_owned");
            int value = EquipmentSellValue(db, equipmentId);
            if (value <= 0) return ServiceResult.Fail("not_sellable");
            state.RemoveEquipment(equipmentId, count);
            state.Gold += value * count;
            var result = ServiceResult.Ok("sold", piece.DisplayName);
            result.GoldDelta = value * count;
            return result;
        }

        // ------------------------------------------------------------------ smithy

        /// <summary>Whether a piece has a recipe (materials or craft gold).</summary>
        public static bool IsCraftable(EquipmentDef piece) => piece.CraftMaterials.Count > 0 || piece.CraftGold > 0;

        /// <summary>A recipe is shown once any of its materials has ever been owned (§10.1); gold-only recipes always show.</summary>
        public static bool IsRecipeVisible(GameState state, EquipmentDef piece)
        {
            if (!IsCraftable(piece)) return false;
            if (piece.CraftMaterials.Count == 0) return true;
            foreach (string material in piece.CraftMaterials.Keys)
                if (state.EverOwnedItems.Contains(material) || state.ItemCount(material) > 0) return true;
            return false;
        }

        /// <summary>Visible recipes, cheapest craft gold first, then id.</summary>
        public static List<RecipeEntry> SmithyRecipes(GameDB db, GameState state)
        {
            var output = new List<RecipeEntry>();
            foreach (var piece in db.Equipment.Values)
            {
                if (!IsRecipeVisible(state, piece)) continue;
                var entry = new RecipeEntry { Equipment = piece, Gold = piece.CraftGold, CanCraft = state.Gold >= piece.CraftGold };
                foreach (var kv in piece.CraftMaterials)
                {
                    int have = state.ItemCount(kv.Key);
                    entry.Materials.Add((kv.Key, have, kv.Value));
                    if (have < kv.Value) entry.CanCraft = false;
                }
                output.Add(entry);
            }
            output.Sort((a, b) => a.Gold != b.Gold ? a.Gold.CompareTo(b.Gold) : string.CompareOrdinal(a.Equipment.Id, b.Equipment.Id));
            return output;
        }

        /// <summary>
        /// Crafts one piece: consumes the materials and craft gold, adds the piece to the bag.
        /// Reasons: unknown_equipment, invalid_slot, not_craftable, invalid_recipe, missing_materials, not_enough_gold, stack_full.
        /// </summary>
        public static ServiceResult Craft(GameDB db, GameState state, string equipmentId)
        {
            if (!db.Equipment.TryGetValue(equipmentId, out var piece)) return ServiceResult.Fail("unknown_equipment");
            if (Array.IndexOf(GameState.EquipSlots, piece.Slot) < 0) return ServiceResult.Fail("invalid_slot");
            if (piece.CraftGold < 0) return ServiceResult.Fail("invalid_recipe");
            if (!IsCraftable(piece)) return ServiceResult.Fail("not_craftable");
            foreach (var kv in piece.CraftMaterials)
            {
                if (kv.Value <= 0 || !db.Items.TryGetValue(kv.Key, out var material) || material.ItemType != ItemType.Material) return ServiceResult.Fail("invalid_recipe");
                if (state.ItemCount(kv.Key) < kv.Value) return ServiceResult.Fail("missing_materials");
            }
            if (state.Gold < piece.CraftGold) return ServiceResult.Fail("not_enough_gold");
            if (state.BagCount(equipmentId) + 1 > GameState.MaxStack) return ServiceResult.Fail("stack_full");
            foreach (var kv in piece.CraftMaterials) state.RemoveItem(kv.Key, kv.Value);
            state.Gold -= piece.CraftGold;
            state.AddEquipment(equipmentId, 1);
            QuestLog.Refresh(db, state);
            var result = ServiceResult.Ok("crafted", piece.DisplayName);
            result.GoldDelta = -piece.CraftGold;
            return result;
        }

        // ------------------------------------------------------------------ guild

        /// <summary>Guild board: complete, accepted, available, locked, claimed; then unlock floor, then id.</summary>
        public static List<QuestBoardEntry> QuestBoard(GameDB db, GameState state)
        {
            var output = new List<QuestBoardEntry>();
            foreach (var quest in db.QuestList)
                output.Add(new QuestBoardEntry { Quest = quest, State = QuestLog.BoardState(state, quest), Progress = QuestLog.Progress(state, quest), Count = Math.Max(1, quest.Count) });
            output.Sort((a, b) =>
            {
                int oa = BoardOrder(a.State), ob = BoardOrder(b.State);
                if (oa != ob) return oa.CompareTo(ob);
                if (a.Quest.UnlockFloor != b.Quest.UnlockFloor) return a.Quest.UnlockFloor.CompareTo(b.Quest.UnlockFloor);
                return string.CompareOrdinal(a.Quest.Id, b.Quest.Id);
            });
            return output;
        }

        /// <summary>Accepts a quest (see <see cref="QuestLog.Accept"/>).</summary>
        public static ServiceResult AcceptQuest(GameDB db, GameState state, string questId) => QuestLog.Accept(db, state, questId);

        /// <summary>Claims a quest's reward (see <see cref="QuestLog.Claim"/>).</summary>
        public static ServiceResult ClaimQuest(GameDB db, GameState state, string questId) => QuestLog.Claim(db, state, questId);

        static int BoardOrder(QuestBoardState s)
        {
            switch (s)
            {
                case QuestBoardState.Complete: return 0;
                case QuestBoardState.Accepted: return 1;
                case QuestBoardState.Available: return 2;
                case QuestBoardState.Locked: return 3;
                default: return 4;
            }
        }

        // ------------------------------------------------------------------ bestiary

        /// <summary>Every enemy: non-bosses first, then level, rank, id.</summary>
        public static List<BestiaryRow> BestiaryRows(GameDB db, GameState state)
        {
            var output = new List<BestiaryRow>();
            foreach (var enemy in db.Enemies.Values)
            {
                state.Bestiary.TryGetValue(enemy.Id, out var entry);
                var row = new BestiaryRow { Enemy = enemy, Kills = entry?.Kills ?? 0 };
                row.Seen = (entry?.Seen ?? false) || row.Kills > 0;
                if (entry != null)
                    foreach (int element in entry.WeakKnown)
                        if (enemy.Weaknesses.Contains(element) && !row.RevealedWeaknesses.Contains(element)) row.RevealedWeaknesses.Add(element);
                row.HiddenWeaknesses = enemy.Weaknesses.Count - row.RevealedWeaknesses.Count;
                row.DropsRevealed = row.Kills > 0;
                output.Add(row);
            }
            output.Sort((a, b) =>
            {
                if (a.Enemy.IsBoss != b.Enemy.IsBoss) return a.Enemy.IsBoss ? 1 : -1;
                if (a.Enemy.Level != b.Enemy.Level) return a.Enemy.Level.CompareTo(b.Enemy.Level);
                if (a.Enemy.Rank != b.Enemy.Rank) return a.Enemy.Rank.CompareTo(b.Enemy.Rank);
                return string.CompareOrdinal(a.Enemy.Id, b.Enemy.Id);
            });
            return output;
        }

        // ------------------------------------------------------------------ depart

        /// <summary>Departure floors: B1F (0) plus every unlocked warp floor, ascending.</summary>
        public static List<int> DepartureFloors(GameDB db, GameState state)
        {
            var output = new List<int> { 0 };
            foreach (int index in state.WarpsUnlocked)
                if (index > 0 && index < db.Floors.Count && !output.Contains(index)) output.Add(index);
            output.Sort();
            return output;
        }

        /// <summary>
        /// Validates a departure. On success the Unity layer starts
        /// <c>new DungeonRun(db, state, floorIndex, ArrivalMode.Town)</c>. Failure reason: warp_locked.
        /// </summary>
        public static ServiceResult Depart(GameDB db, GameState state, int floorIndex)
        {
            if (!DepartureFloors(db, state).Contains(floorIndex)) return ServiceResult.Fail("warp_locked");
            return ServiceResult.Ok("depart_go");
        }
    }
}
