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
        /// <summary>Story chapter the species is listed under (1-6, 7 = 시련의 회랑); see <see cref="TownServices.BestiaryChapters"/>.</summary>
        public int Chapter;
        /// <summary>Floor labels ("B12F") where the species can be met (encounter groups, FOEs, events, boss group), ascending.</summary>
        public List<string> Habitat = new List<string>();
        public bool IsBoss => Enemy.IsBoss;
        public bool IsElite => Enemy.Rank > 0 && !Enemy.IsBoss;
    }

    /// <summary>One bestiary completion milestone: species with kills (or every boss) and the reward for reaching it.</summary>
    public sealed class BestiaryMilestoneRow
    {
        /// <summary>0-based position in <see cref="TownServices.BestiaryMilestones"/>; the argument of <see cref="TownServices.ClaimBestiaryReward"/>.</summary>
        public int Index;
        /// <summary>Species needed (0 for the all-bosses milestone).</summary>
        public int Threshold;
        public bool AllBosses;
        /// <summary>"토벌 25종" or "모든 보스 토벌".</summary>
        public string Label = "";
        /// <summary>Reward summary, e.g. "1,000 G  ·  상급 강화석 ×2".</summary>
        public string RewardText = "";
        public int Gold;
        /// <summary>Item or equipment ids and counts granted with the gold.</summary>
        public IReadOnlyList<(string Id, int Count)> Items = Array.Empty<(string, int)>();
        /// <summary>Species killed (or bosses killed) so far.</summary>
        public int Progress;
        /// <summary>Progress needed.</summary>
        public int Goal;
        public bool Reached;
        public bool Claimed;
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

        /// <summary>
        /// Every enemy: non-bosses first, then level, rank, id. Chapter and habitat come from the floors
        /// (see <see cref="BestiaryChapters"/>).
        /// </summary>
        public static List<BestiaryRow> BestiaryRows(GameDB db, GameState state)
        {
            var habitats = BestiaryHabitats(db);
            var chapters = BestiaryChapters(db, habitats);
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
                row.Chapter = chapters[enemy.Id];
                if (habitats.TryGetValue(enemy.Id, out var floors))
                    foreach (int index in floors) row.Habitat.Add(db.Floors[index].FloorLabel);
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

        /// <summary>
        /// Floor indices (ascending, unique) where each enemy id can be met: encounter groups, FOE groups, event groups
        /// and the floor's boss group. Showcase groups are display only and do not count.
        /// </summary>
        public static Dictionary<string, List<int>> BestiaryHabitats(GameDB db)
        {
            var output = new Dictionary<string, List<int>>(StringComparer.Ordinal);
            for (int index = 0; index < db.Floors.Count; index++)
            {
                var floor = db.Floors[index];
                var ids = new List<string>();
                foreach (var group in floor.EncounterGroups) ids.AddRange(group);
                foreach (var foe in floor.Foes) ids.AddRange(foe.Group);
                foreach (var ev in floor.Events) ids.AddRange(ev.Group);
                ids.AddRange(floor.BossGroup);
                foreach (string id in ids)
                {
                    if (!db.Enemies.ContainsKey(id)) continue;
                    if (!output.TryGetValue(id, out var list)) output[id] = list = new List<int>();
                    if (list.Count == 0 || list[list.Count - 1] != index) list.Add(index);
                }
            }
            return output;
        }

        /// <summary>
        /// Chapter per enemy id (1-6 main, 7 = 시련의 회랑). Rule: (1) the chapter of the first floor the species appears on
        /// (5 floors per chapter, <see cref="GameFlow.ChapterOf"/>); (2) a species that appears nowhere (summons only)
        /// takes the earliest chapter of an enemy that summons it (one hop, via Summons or boss phase summons);
        /// (3) otherwise the chapter of the party level band it is met at (<see cref="LevelChapter"/>).
        /// </summary>
        public static Dictionary<string, int> BestiaryChapters(GameDB db, Dictionary<string, List<int>> habitats)
        {
            var chapters = new Dictionary<string, int>(StringComparer.Ordinal);
            foreach (var enemy in db.Enemies.Values)
                if (habitats.TryGetValue(enemy.Id, out var floors) && floors.Count > 0) chapters[enemy.Id] = GameFlow.ChapterOf(floors[0]);
            var met = new Dictionary<string, int>(chapters, StringComparer.Ordinal);
            foreach (var enemy in db.Enemies.Values)
            {
                if (chapters.ContainsKey(enemy.Id)) continue;
                int best = 0;
                foreach (var summoner in db.Enemies.Values)
                {
                    if (!met.TryGetValue(summoner.Id, out int chapter) || !Summons(summoner, enemy.Id)) continue;
                    if (best == 0 || chapter < best) best = chapter;
                }
                chapters[enemy.Id] = best > 0 ? best : LevelChapter(enemy.Level);
            }
            return chapters;
        }

        /// <summary>Whether <paramref name="summoner"/> can call <paramref name="enemyId"/> (own summons or a boss phase summon).</summary>
        static bool Summons(EnemyDef summoner, string enemyId)
        {
            if (summoner.Summons != null && summoner.Summons.Contains(enemyId)) return true;
            if (summoner.Phases == null) return false;
            foreach (var phase in summoner.Phases)
                if (phase?.Summon != null && phase.Summon.Contains(enemyId)) return true;
            return false;
        }

        /// <summary>Chapter whose party level band (<see cref="ChapterLevelEntries"/>) contains <paramref name="level"/>.</summary>
        public static int LevelChapter(int level)
        {
            int chapter = 1;
            foreach (int entry in ChapterLevelEntries) if (level >= entry) chapter++;
            return Math.Min(7, chapter);
        }

        /// <summary>Party level at which chapters 2-7 begin (chapter 1 starts at level 1).</summary>
        static readonly int[] ChapterLevelEntries = { 12, 24, 34, 44, 54, 64 };

        /// <summary>
        /// Milestones: species with kills (12 / 25 / 40 / 60 / 80 / 100 of 108), then every boss defeated. Rewards use
        /// existing items and equipment only; the top accessory is epic (rarity 2), no legendary or tier-8 gear.
        /// </summary>
        static readonly BestiaryMilestoneDef[] BestiaryMilestoneDefs =
        {
            Milestone(10, 300, ("enhance_stone", 3)),
            Milestone(25, 1000, ("enhance_stone_hi", 2)),
            Milestone(40, 2500, ("seed_life", 1), ("mega_potion", 2)),
            Milestone(60, 5000, ("enhance_stone_hi", 4), ("seed_power", 1)),
            Milestone(80, 8000, ("enhance_stone_abyss", 2), ("phoenix_plume", 2)),
            Milestone(100, 12000, ("seed_magic", 1), ("seed_mind", 1), ("x_potion", 3)),
            new BestiaryMilestoneDef { AllBosses = true, Gold = 20000, Items = new[] { ("acc_regen_ring", 1) } },
        };

        static BestiaryMilestoneDef Milestone(int threshold, int gold, params (string Id, int Count)[] items) =>
            new BestiaryMilestoneDef { Threshold = threshold, Gold = gold, Items = items };

        sealed class BestiaryMilestoneDef
        {
            public int Threshold;
            public bool AllBosses;
            public int Gold;
            public (string Id, int Count)[] Items = Array.Empty<(string, int)>();
        }

        /// <summary>Flag that records a claimed milestone: "bestiary_reward_&lt;n&gt;", n = 1-based milestone number.</summary>
        public static string BestiaryRewardFlag(int index) => "bestiary_reward_" + (index + 1);

        /// <summary>Milestone rows in order, with progress, reached and claimed state.</summary>
        public static List<BestiaryMilestoneRow> BestiaryMilestones(GameDB db, GameState state)
        {
            int killedSpecies = 0, bosses = 0, bossesKilled = 0;
            foreach (var enemy in db.Enemies.Values)
            {
                bool killed = BestiaryKilled(state, enemy.Id);
                if (killed) killedSpecies++;
                if (enemy.IsBoss)
                {
                    bosses++;
                    if (killed) bossesKilled++;
                }
            }
            var output = new List<BestiaryMilestoneRow>();
            for (int i = 0; i < BestiaryMilestoneDefs.Length; i++)
            {
                var def = BestiaryMilestoneDefs[i];
                var row = new BestiaryMilestoneRow
                {
                    Index = i, Threshold = def.Threshold, AllBosses = def.AllBosses, Gold = def.Gold, Items = def.Items,
                    Label = def.AllBosses ? "모든 보스 토벌" : $"토벌 {def.Threshold}종",
                    RewardText = BestiaryRewardText(db, def),
                    Progress = def.AllBosses ? bossesKilled : killedSpecies,
                    Goal = def.AllBosses ? bosses : def.Threshold,
                    Claimed = state.Flags.Contains(BestiaryRewardFlag(i)),
                };
                row.Reached = bosses > 0 && row.Progress >= row.Goal;
                output.Add(row);
            }
            return output;
        }

        /// <summary>
        /// Grants milestone <paramref name="index"/> (0-based, see <see cref="BestiaryMilestones"/>): gold and items, then
        /// the flag. Atomic. Failure reasons: invalid_milestone, already_claimed, not_reached.
        /// </summary>
        public static ServiceResult ClaimBestiaryReward(GameDB db, GameState state, int index)
        {
            if (index < 0 || index >= BestiaryMilestoneDefs.Length) return ServiceResult.Fail("invalid_milestone");
            string flag = BestiaryRewardFlag(index);
            if (state.Flags.Contains(flag)) return ServiceResult.Fail("already_claimed");
            var milestone = BestiaryMilestones(db, state)[index];
            if (!milestone.Reached) return ServiceResult.Fail("not_reached");
            var def = BestiaryMilestoneDefs[index];
            state.Gold += def.Gold;
            foreach (var item in def.Items) state.AddContent(db, item.Id, item.Count);
            state.Flags.Add(flag);
            QuestLog.Refresh(db, state);
            var result = ServiceResult.Ok("bestiary_reward_claimed", milestone.RewardText);
            result.GoldDelta = def.Gold;
            return result;
        }

        static bool BestiaryKilled(GameState state, string enemyId) => state.Bestiary.TryGetValue(enemyId, out var entry) && entry != null && entry.Kills > 0;

        static string BestiaryRewardText(GameDB db, BestiaryMilestoneDef def)
        {
            var parts = new List<string>();
            if (def.Gold > 0) parts.Add(def.Gold.ToString("N0", System.Globalization.CultureInfo.InvariantCulture) + " G");
            foreach (var item in def.Items)
            {
                string name = db.Items.TryGetValue(item.Id, out var consumable) ? consumable.DisplayName
                    : db.Equipment.TryGetValue(item.Id, out var piece) ? piece.DisplayName : item.Id;
                parts.Add(name + " ×" + item.Count);
            }
            return string.Join("  ·  ", parts);
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
