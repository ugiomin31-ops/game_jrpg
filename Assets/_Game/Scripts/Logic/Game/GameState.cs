// Persistent campaign state (everything a save slot holds, minus user settings).
// Port of scripts/core/game_state.gd: field semantics are kept, storage is typed.
using System;
using System.Collections.Generic;
using Abyss.Logic.Dungeon;
using Newtonsoft.Json;
using Newtonsoft.Json.Linq;

namespace Abyss.Logic.Game
{
    /// <summary>Where the party is when the game is resumed.</summary>
    public enum GameLocation { Town = 0, Dungeon = 1 }

    /// <summary>Quest row state. A quest absent from <see cref="GameState.Quests"/> is not accepted.</summary>
    public enum QuestState { Accepted = 0, Complete = 1, Claimed = 2 }

    /// <summary>One party member's persistent state.</summary>
    public sealed class HeroState
    {
        public string Id;
        /// <summary>Current job id (jobs.json); the hero id itself is the base job. Saves without it load as the base job.</summary>
        public string Job;
        public int Level = 1;
        /// <summary>XP accumulated toward the next level (resets on level up; 0 at the cap).</summary>
        public int Xp;
        /// <summary>Current HP/MP (0 HP = knocked out). Always within the effective maximum.</summary>
        public int Hp, Mp;
        /// <summary>
        /// TP carried between battles (0..<see cref="MaxTp"/>; 0 while knocked out). Kept by springs, tents and healing items;
        /// cleared for every hunter whenever the party is put in town (<see cref="GameState.ClearCarriedTp"/>). Saves without it load as 0.
        /// </summary>
        public int Tp;
        /// <summary>TP cap (same as the battle cap).</summary>
        public const int MaxTp = Battle.BattleUnit.MaxTpValue;
        /// <summary>slot ("weapon" | "armor" | "accessory") -> equipment id, "" when empty. All three keys always exist.</summary>
        public Dictionary<string, string> Equipment = new Dictionary<string, string>();
        /// <summary>Skill ids usable in battle (basic_attack, Lv1 skills and every learnset entry reached), in learn order.</summary>
        public List<string> LearnedSkills = new List<string>();
        /// <summary>Statuses carried between battles (status id -> turns left), e.g. trap poison.</summary>
        public Dictionary<string, int> Statuses = new Dictionary<string, int>();
        /// <summary>Permanent seed bonuses: stat key (max_hp, max_mp, attack, magic, defense, resistance, speed) -> amount.</summary>
        public Dictionary<string, int> Seeds = new Dictionary<string, int>();
        /// <summary>The campaign's shared enhancement map (<see cref="GameState.Enhancements"/>), bound by <see cref="GameState.Repair"/>; not saved per hero.</summary>
        [JsonIgnore] public IReadOnlyDictionary<string, int> EnhanceLevels;

        /// <summary>Equipped id in <paramref name="slot"/> or "".</summary>
        public string Equipped(string slot) => Equipment.TryGetValue(slot, out var id) && id != null ? id : "";
    }

    /// <summary>Progress of one accepted quest.</summary>
    public sealed class QuestProgress
    {
        public QuestState State;
        public int Progress;
    }

    /// <summary>Bestiary record of one enemy id.</summary>
    public sealed class BestiaryEntry
    {
        public bool Seen;
        public int Kills;
        /// <summary>Element ints the party has hit as a weakness (sorted, unique).</summary>
        public List<int> WeakKnown = new List<int>();
    }

    /// <summary>Per-floor map progress (keyed by floor id in <see cref="GameState.Floors"/>).</summary>
    public sealed class FloorProgress
    {
        /// <summary>Cells drawn on the map.</summary>
        public SortedSet<GridPos> Explored = new SortedSet<GridPos>();
        /// <summary>Opened `T` cells (one-time).</summary>
        public SortedSet<GridPos> OpenedChests = new SortedSet<GridPos>();
        /// <summary>Won `E` event battles and the `B` boss cell (one-time).</summary>
        public SortedSet<GridPos> ClearedBattles = new SortedSet<GridPos>();
        /// <summary>Picked-up `K` cells (one-time).</summary>
        public SortedSet<GridPos> TakenKeys = new SortedSet<GridPos>();
        /// <summary>`X` cells already triggered (drawn on the map from then on; they keep triggering).</summary>
        public SortedSet<GridPos> SteppedTraps = new SortedSet<GridPos>();
        /// <summary>`H` cells used this outing; refilled only on town arrival or successful inn rest.</summary>
        [JsonConverter(typeof(SpentSpringCellsConverter))]
        public SortedSet<GridPos> SpentSprings = new SortedSet<GridPos>();
        /// <summary>`L` doors opened with a key (permanently open).</summary>
        public SortedSet<GridPos> OpenedDoors = new SortedSet<GridPos>();
        /// <summary>FOE ids defeated since the last inn rest.</summary>
        public SortedSet<string> DefeatedFoes = new SortedSet<string>(StringComparer.Ordinal);
        /// <summary>Unused keys of this floor.</summary>
        public int Keys;
    }

    /// <summary>
    /// Tolerant reader for the additive spring field only. Valid cells use the codec's existing GridPos converter;
    /// malformed/null entries are discarded without weakening validation of any other saved progress.
    /// </summary>
    sealed class SpentSpringCellsConverter : JsonConverter<SortedSet<GridPos>>
    {
        public override void WriteJson(JsonWriter writer, SortedSet<GridPos> value, JsonSerializer serializer)
        {
            writer.WriteStartArray();
            if (value != null) foreach (var cell in value) serializer.Serialize(writer, cell);
            writer.WriteEndArray();
        }
        public override SortedSet<GridPos> ReadJson(JsonReader reader, Type objectType, SortedSet<GridPos> existingValue, bool hasExistingValue, JsonSerializer serializer)
        {
            var cells = new SortedSet<GridPos>();
            var token = JToken.Load(reader);
            if (!(token is JArray entries)) return cells;
            foreach (var entry in entries)
            {
                bool valid = entry is JArray a && a.Count == 2 && a[0].Type == JTokenType.Integer && a[1].Type == JTokenType.Integer
                    || entry is JObject o && o["x"]?.Type == JTokenType.Integer && o["y"]?.Type == JTokenType.Integer;
                if (!valid) continue;
                try { cells.Add(entry.ToObject<GridPos>(serializer)); }
                catch (Exception e) when (e is JsonException || e is FormatException || e is InvalidCastException || e is OverflowException) { }
            }
            return cells;
        }
    }

    /// <summary>Campaign state. Create with <see cref="NewGame"/> or <see cref="SaveCodec.Deserialize(string, GameDB)"/>.</summary>
    public sealed class GameState
    {
        public const int LevelCap = 70;
        public const int StartingGold = 150;
        public const int MaxStack = 99;
        public const int PartySize = 4;
        public static readonly string[] EquipSlots = { "weapon", "armor", "accessory" };

        /// <summary>Active party in formation order (1..<see cref="PartySize"/> hunters).</summary>
        public List<HeroState> Party = new List<HeroState>();
        /// <summary>Recruited hunters waiting at the guild (benched; they earn <see cref="HunterRoster.BenchXpShare"/> of battle EXP).</summary>
        public List<HeroState> Reserve = new List<HeroState>();
        /// <summary>Item id -> count (consumables and materials).</summary>
        public Dictionary<string, int> Inventory = new Dictionary<string, int>();
        /// <summary>Equipment id -> count of UNEQUIPPED pieces owned.</summary>
        public Dictionary<string, int> EquipmentBag = new Dictionary<string, int>();
        /// <summary>Equipment id -> enhancement level 1..10, shared by every copy of that id (see <see cref="Enhancement"/>).</summary>
        public Dictionary<string, int> Enhancements = new Dictionary<string, int>();
        /// <summary>Every item id that has ever been in the inventory (smithy recipe visibility, §10.1).</summary>
        public SortedSet<string> EverOwnedItems = new SortedSet<string>(StringComparer.Ordinal);
        public int Gold;
        public Difficulty Difficulty = Difficulty.Normal;
        public GameLocation Location = GameLocation.Town;
        /// <summary>Deepest floor index reached (0 = B1F).</summary>
        public int DeepestFloor;
        /// <summary>Current / last floor index.</summary>
        public int FloorIndex;
        public GridPos Position;
        public Facing Facing = Facing.East;
        /// <summary>Floor id -> map progress.</summary>
        public Dictionary<string, FloorProgress> Floors = new Dictionary<string, FloorProgress>();
        /// <summary>Floor indices whose warp crystal is active (town departure targets besides B1F).</summary>
        public SortedSet<int> WarpsUnlocked = new SortedSet<int>();
        /// <summary>Quest id -> progress (absent = not accepted).</summary>
        public Dictionary<string, QuestProgress> Quests = new Dictionary<string, QuestProgress>();
        /// <summary>Enemy id -> bestiary record.</summary>
        public Dictionary<string, BestiaryEntry> Bestiary = new Dictionary<string, BestiaryEntry>();
        /// <summary>One-shot flags: tips (tip_*), story beats, boss_N_cleared, cleared, ending_seen... See <see cref="GameFlow"/>.</summary>
        public SortedSet<string> Flags = new SortedSet<string>(StringComparer.Ordinal);
        public int TotalWins;
        public double PlayTimeSeconds;
        /// <summary>Unsettled encounter identity (relaunch on resume), never a second reward grant.</summary>
        public DungeonBattleRequest PendingBattle;
        public uint DungeonRandomState;
        public int DungeonEncounterSteps;

        /// <summary>Fresh campaign: the starting hunters at Lv1 with starter gear and full vitals, 150 G, 3 healing_potion, 1 return_stone (§2.2).</summary>
        public static GameState NewGame(GameDB db, Difficulty difficulty)
        {
            var s = new GameState { Difficulty = difficulty, Gold = StartingGold, Location = GameLocation.Town };
            foreach (string id in db.HeroOrder) s.Party.Add(new HeroState { Id = id, Job = db.ClassOf(id), Level = 1, Hp = -1, Mp = -1 });
            s.AddItem("healing_potion", 3);
            s.AddItem("return_stone", 1);
            var first = db.Floors[0];
            s.FloorIndex = 0;
            s.Position = DungeonGrid.Parse(first).Start;
            s.Facing = Facing.East;
            s.Flags.Add(GameFlow.FlagProloguePending);
            s.Repair(db);
            return s;
        }

        /// <summary>Recruited hunter (party or reserve) by id, or null.</summary>
        public HeroState Hero(string heroId)
        {
            foreach (var h in Party) if (h.Id == heroId) return h;
            foreach (var h in Reserve) if (h.Id == heroId) return h;
            return null;
        }

        /// <summary>True when the hunter is in the active party.</summary>
        public bool InParty(string heroId)
        {
            foreach (var h in Party) if (h.Id == heroId) return true;
            return false;
        }

        /// <summary>Every recruited hunter: the party in formation order, then the reserve.</summary>
        public IEnumerable<HeroState> AllHunters()
        {
            foreach (var h in Party) yield return h;
            foreach (var h in Reserve) yield return h;
        }

        /// <summary>
        /// Clears carried TP for every recruited hunter (party and reserve). The one reset used by every route that puts the
        /// party in town (return to town, town arrival, prologue, ending, defeat recovery) and by a successful inn rest.
        /// </summary>
        public void ClearCarriedTp()
        {
            foreach (var hero in AllHunters()) if (hero != null) hero.Tp = 0;
        }

        /// <summary>Pure spring readiness query; never creates or repairs a floor record.</summary>
        public bool IsSpringSpent(string floorId, GridPos cell) => floorId != null && Floors != null
            && Floors.TryGetValue(floorId, out var progress) && (progress?.SpentSprings?.Contains(cell) ?? false);

        /// <summary>Refills every visited floor's springs without resetting map or FOE progress. Idempotent.</summary>
        public void RefillSprings()
        {
            if (Floors == null) return;
            foreach (var progress in Floors.Values) progress?.SpentSprings?.Clear();
        }

        /// <summary>Progress record for a floor id (created on first access).</summary>
        public FloorProgress Floor(string floorId)
        {
            if (!Floors.TryGetValue(floorId, out var p)) Floors[floorId] = p = new FloorProgress();
            return p;
        }

        /// <summary>Owned inventory count of an item.</summary>
        public int ItemCount(string itemId) => Inventory.TryGetValue(itemId, out int n) ? n : 0;

        /// <summary>Owned unequipped count of an equipment id.</summary>
        public int BagCount(string equipmentId) => EquipmentBag.TryGetValue(equipmentId, out int n) ? n : 0;

        /// <summary>Adds items (count &gt; 0) to the inventory and records them as ever owned.</summary>
        public void AddItem(string itemId, int count)
        {
            if (count <= 0 || string.IsNullOrEmpty(itemId)) return;
            Inventory[itemId] = ItemCount(itemId) + count;
            EverOwnedItems.Add(itemId);
        }

        /// <summary>Removes up to <paramref name="count"/> items; the key disappears at 0.</summary>
        public void RemoveItem(string itemId, int count) => RemoveCount(Inventory, itemId, count);

        /// <summary>Adds unequipped equipment pieces.</summary>
        public void AddEquipment(string equipmentId, int count)
        {
            if (count <= 0 || string.IsNullOrEmpty(equipmentId)) return;
            EquipmentBag[equipmentId] = BagCount(equipmentId) + count;
        }

        /// <summary>Removes unequipped equipment pieces.</summary>
        public void RemoveEquipment(string equipmentId, int count) => RemoveCount(EquipmentBag, equipmentId, count);

        /// <summary>Adds a reward/drop id: equipment ids go to the bag, everything else to the inventory.</summary>
        public void AddContent(GameDB db, string id, int count)
        {
            if (db.Equipment.ContainsKey(id)) AddEquipment(id, count);
            else AddItem(id, count);
        }

        /// <summary>Grants chest contents once; the caller commits the opened cell alongside this change.</summary>
        public void AddContents(GameDB db, TreasureContents contents)
        {
            if (contents == null) return;
            Gold += Math.Max(0, contents.Gold);
            foreach (var kv in contents.Items) AddContent(db, kv.Key, kv.Value);
            foreach (var kv in contents.Equipment) AddContent(db, kv.Key, kv.Value);
            QuestLog.Refresh(db, this);
        }

        /// <summary>Records a floor as entered: updates <see cref="DeepestFloor"/> and explore quests.</summary>
        public void SetDeepestFloor(GameDB db, int index)
        {
            int clamped = Math.Max(0, Math.Min(db.Floors.Count - 1, index));
            if (clamped > DeepestFloor) DeepestFloor = clamped;
            QuestLog.Refresh(db, this);
        }

        /// <summary>Bestiary record (created on first access).</summary>
        public BestiaryEntry BestiaryOf(string enemyId)
        {
            if (!Bestiary.TryGetValue(enemyId, out var e)) Bestiary[enemyId] = e = new BestiaryEntry();
            return e;
        }

        /// <summary>"enemyId:element" strings for <see cref="BattleSetup.KnownWeaknesses"/>.</summary>
        public HashSet<string> KnownWeaknessKeys()
        {
            var output = new HashSet<string>();
            foreach (var kv in Bestiary)
                foreach (int element in kv.Value.WeakKnown) output.Add(kv.Key + ":" + element);
            return output;
        }

        /// <summary>
        /// Normalises loaded or freshly built state against the database: every hero exists once with all
        /// slots, levels/XP within range, starter gear for heroes that lost theirs, learned skills synced with
        /// the learnset, vitals clamped, and quest rows refreshed.
        /// </summary>
        public void Repair(GameDB db)
        {
            Party ??= new List<HeroState>();
            Inventory ??= new Dictionary<string, int>();
            EquipmentBag ??= new Dictionary<string, int>();
            Enhancements ??= new Dictionary<string, int>();
            foreach (var id in new List<string>(Enhancements.Keys))
            {
                int level = Math.Min(Enhancement.MaxLevel, Enhancements[id]);
                if (level <= 0 || !db.Equipment.ContainsKey(id)) Enhancements.Remove(id);
                else Enhancements[id] = level;
            }
            EverOwnedItems ??= new SortedSet<string>(StringComparer.Ordinal);
            Floors ??= new Dictionary<string, FloorProgress>();
            WarpsUnlocked ??= new SortedSet<int>();
            Quests ??= new Dictionary<string, QuestProgress>();
            Bestiary ??= new Dictionary<string, BestiaryEntry>();
            Flags ??= new SortedSet<string>(StringComparer.Ordinal);
            foreach (var id in new List<string>(Quests.Keys)) if (Quests[id] == null) Quests.Remove(id);
            foreach (var id in new List<string>(Bestiary.Keys))
            {
                if (Bestiary[id] == null) Bestiary.Remove(id);
                else Bestiary[id].WeakKnown ??= new List<int>();
            }
            foreach (var id in new List<string>(Floors.Keys))
            {
                var p = Floors[id] ?? new FloorProgress();
                Floors[id] = p;
                p.Explored ??= new SortedSet<GridPos>();
                p.OpenedChests ??= new SortedSet<GridPos>();
                p.ClearedBattles ??= new SortedSet<GridPos>();
                p.TakenKeys ??= new SortedSet<GridPos>();
                p.SteppedTraps ??= new SortedSet<GridPos>();
                p.SpentSprings ??= new SortedSet<GridPos>();
                // Invalid/stale spring cells must not affect valid map progress or consume an unrelated spring.
                FloorDef springFloor = null;
                foreach (var floor in db.Floors) if (floor.Id == id) { springFloor = floor; break; }
                p.SpentSprings.RemoveWhere(cell => springFloor == null || cell.Y < 0 || cell.Y >= springFloor.Rows.Count
                    || cell.X < 0 || cell.X >= springFloor.Rows[cell.Y].Length || springFloor.Rows[cell.Y][cell.X] != 'H');
                p.OpenedDoors ??= new SortedSet<GridPos>();
                p.DefeatedFoes ??= new SortedSet<string>(StringComparer.Ordinal);
                p.Keys = Math.Max(0, p.Keys);
            }
            Reserve ??= new List<HeroState>();
            CampaignMigration.Apply(db, this);
            HunterRoster.MigrateLegacyHeroes(db, this);
            // Every recruited hunter exists once (party first); unknown ids are dropped. The starting hunters are
            // always recruited (saves missing one get it back at the roster's lowest level).
            var seen = new HashSet<string>();
            var party = new List<HeroState>();
            var reserve = new List<HeroState>();
            foreach (var h in Party) if (h != null && h.Id != null && db.Heroes.ContainsKey(h.Id) && seen.Add(h.Id)) party.Add(h);
            foreach (var h in Reserve) if (h != null && h.Id != null && db.Heroes.ContainsKey(h.Id) && seen.Add(h.Id)) reserve.Add(h);
            int lowest = int.MaxValue;
            foreach (var h in party) lowest = Math.Min(lowest, h.Level);
            foreach (var h in reserve) lowest = Math.Min(lowest, h.Level);
            foreach (string id in db.HeroOrder)
            {
                if (seen.Contains(id)) continue;
                seen.Add(id);
                var fresh = new HeroState { Id = id, Job = db.ClassOf(id), Level = lowest == int.MaxValue ? 1 : lowest, Hp = -1, Mp = -1 };
                if (party.Count < PartySize) party.Add(fresh); else reserve.Add(fresh);
            }
            while (party.Count > PartySize) { reserve.Insert(0, party[party.Count - 1]); party.RemoveAt(party.Count - 1); }
            while (party.Count == 0 && reserve.Count > 0) { party.Add(reserve[0]); reserve.RemoveAt(0); }
            Party = party;
            Reserve = reserve;
            foreach (var hero in AllHunters()) RepairHero(db, hero);
            Gold = Math.Max(0, Gold);
            FloorIndex = Math.Max(0, Math.Min(db.Floors.Count - 1, FloorIndex));
            DeepestFloor = Math.Max(FloorIndex, Math.Min(db.Floors.Count - 1, DeepestFloor));
            if (!Enum.IsDefined(typeof(Difficulty), Difficulty)) Difficulty = Difficulty.Normal;
            if (!Enum.IsDefined(typeof(GameLocation), Location)) Location = GameLocation.Town;
            Facing = GridPos.Rotate(Facing.North, (int)Facing);
            DungeonEncounterSteps = Math.Max(0, DungeonEncounterSteps);
            PlayTimeSeconds = double.IsNaN(PlayTimeSeconds) || double.IsInfinity(PlayTimeSeconds) ? 0 : Math.Max(0, PlayTimeSeconds);
            WarpsUnlocked.RemoveWhere(index => index < 0 || index >= db.Floors.Count);
            var activeGrid = DungeonGrid.Parse(db.Floors[FloorIndex], Floor(db.Floors[FloorIndex].Id));
            if (!activeGrid.IsWalkable(Position)) Position = activeGrid.Start;
            activeGrid.Explore(Position);
            foreach (var kv in Inventory) if (kv.Value > 0) EverOwnedItems.Add(kv.Key);
            QuestLog.Refresh(db, this);
        }

        /// <summary>Normalises one hunter: slots, seeds, job (must be on the hunter's class tree), level/XP, skills, vitals.</summary>
        internal void RepairHero(GameDB db, HeroState hero)
        {
            // A hero without any slot record (fresh or legacy) gets starter gear; emptied slots stay empty.
            bool missingEquipment = hero.Equipment == null || hero.Equipment.Count == 0;
            hero.Equipment ??= new Dictionary<string, string>();
            hero.Statuses ??= new Dictionary<string, int>();
            hero.LearnedSkills ??= new List<string>();
            hero.Seeds ??= new Dictionary<string, int>();
            foreach (var key in new List<string>(hero.Seeds.Keys))
            {
                int amount = Math.Min(PartyStats.SeedCap(key), hero.Seeds[key]);
                if (amount <= 0) hero.Seeds.Remove(key);
                else hero.Seeds[key] = amount;
            }
            hero.EnhanceLevels = Enhancements;
            foreach (string slot in EquipSlots)
                if (!hero.Equipment.TryGetValue(slot, out var eq) || eq == null) hero.Equipment[slot] = "";
            string cls = db.ClassOf(hero.Id);
            if (string.IsNullOrEmpty(hero.Job) || !db.Jobs.TryGetValue(hero.Job, out var job) || job.Hero != cls) hero.Job = cls;
            if (missingEquipment) EquipStarterGear(db, hero);
            hero.Level = Math.Max(1, Math.Min(LevelCap, hero.Level));
            hero.Xp = hero.Level >= LevelCap ? 0 : Math.Max(0, hero.Xp);
            PartyStats.SyncLearnedSkills(db, hero);
            var stats = PartyStats.EffectiveStats(db, hero);
            hero.Hp = hero.Hp < 0 ? stats.MaxHp : Math.Min(hero.Hp, stats.MaxHp);
            hero.Mp = hero.Mp < 0 ? stats.MaxMp : Math.Min(hero.Mp, stats.MaxMp);
            hero.Tp = hero.Hp <= 0 ? 0 : Math.Max(0, Math.Min(HeroState.MaxTp, hero.Tp));
        }

        /// <summary>Authored starter piece per empty slot; when absent, the cheapest eligible tier-1 piece (original rule).</summary>
        internal static void EquipStarterGear(GameDB db, HeroState hero)
        {
            db.Heroes.TryGetValue(hero.Id, out var def);
            foreach (string slot in EquipSlots)
            {
                if (hero.Equipped(slot) != "") continue;
                if (def != null && def.StarterEquipment.TryGetValue(slot, out var authored))
                {
                    if (string.IsNullOrEmpty(authored)) continue;
                    if (db.Equipment.TryGetValue(authored, out var piece) && piece.Slot == slot && PartyStats.AllowsClass(db, piece, hero.Id))
                    {
                        hero.Equipment[slot] = authored;
                        continue;
                    }
                }
                EquipmentDef best = null;
                foreach (var piece in db.Equipment.Values)
                {
                    if (piece.Slot != slot || piece.ShopTier != 1 || !PartyStats.AllowsClass(db, piece, hero.Id) || (piece.Jobs != null && piece.Jobs.Count > 0)) continue;
                    if (best == null || piece.Price < best.Price || (piece.Price == best.Price && string.CompareOrdinal(piece.Id, best.Id) < 0)) best = piece;
                }
                if (best != null) hero.Equipment[slot] = best.Id;
            }
        }

        static void RemoveCount(Dictionary<string, int> source, string key, int count)
        {
            if (count <= 0) return;
            if (!source.TryGetValue(key, out int have)) return;
            int left = have - count;
            if (left > 0) source[key] = left;
            else source.Remove(key);
        }
    }
}
