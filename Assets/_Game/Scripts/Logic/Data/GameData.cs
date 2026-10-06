// Engine-free data definitions for 심연의 미궁. Field names map 1:1 to Resources/Data/*.json
// (snake_case JSON <-> PascalCase C# via SnakeCaseNamingStrategy). Numeric enum values are the
// original Godot values and MUST NOT be reordered (append-only).
using System;
using System.Collections.Generic;
using Newtonsoft.Json;
using Newtonsoft.Json.Linq;
using Newtonsoft.Json.Serialization;

namespace Abyss.Logic
{
    public enum SkillKind { Damage = 0, Heal = 1, Buff = 2, Debuff = 3, Revive = 4, Cleanse = 5 }
    public enum ScalingStat { Attack = 0, Magic = 1 }
    public enum TargetType { Enemy = 0, Ally = 1, Self = 2 }
    public enum Element { None = 0, Slash = 1, Blunt = 2, Pierce = 3, Fire = 4, Ice = 5, Thunder = 6, Dark = 7, Holy = 8 }
    public enum Scope { Single = 0, All = 1, Random = 2 }

    public enum StatusEffectType
    {
        Poison = 0, Stun = 1, AttackUp = 2, DefenseUp = 3, Burn = 4, Bleed = 5, Slow = 6, Freeze = 7, Silence = 8,
        AttackDown = 9, DefenseDown = 10, Regen = 11, Barrier = 12, Provoke = 13, Sleep = 14, Blind = 15,
        MagicUp = 16, SpeedUp = 17, ManaShield = 18, Invincible = 19,
    }

    public enum ItemType { Healing = 0, MpRestore = 1, Cure = 2, Revive = 3, EscapeDungeon = 4, FleeBattle = 5, Damage = 6, Material = 7, Buff = 8 }

    public enum Difficulty { Easy = 0, Normal = 1, Hard = 2 }

    public sealed class LearnEntry
    {
        public int Level;
        public string Skill;
    }

    public sealed class HeroDef
    {
        public string Id;
        public string DisplayName;
        public int MaxHp, MaxMp, Attack, Magic, Defense, Resistance, Speed;
        public float Hit = 0.95f, Evade = 0.05f, Crit = 0.05f;
        public float HpGrowth, MpGrowth, AtkGrowth, MagGrowth, DefGrowth, ResGrowth, SpdGrowth;
        public Dictionary<string, string> StarterEquipment = new Dictionary<string, string>();
        public List<string> Skills = new List<string>();
        public List<LearnEntry> Learnset = new List<LearnEntry>();
        public float[] ClassColor;
    }

    public sealed class DropEntry
    {
        public string Id;
        public float Chance;
    }

    public sealed class BossPhase
    {
        public float HpBelow = 1f;
        public int ActionsPerTurn = 1;
        public List<string> Skills = new List<string>();
        public List<int> Weights = new List<int>();
        public List<string> Summon = new List<string>();
        public string Line = "";
    }

    public sealed class EnemyDef
    {
        public string Id;
        public string DisplayName;
        public int Rank;
        public bool IsBoss;
        public int Level = 1;
        public int MaxHp, MaxMp, Attack, Magic, Defense, Resistance, Speed;
        public float Hit = 0.95f, Evade = 0.05f;
        public int BreakShield;
        public List<int> Weaknesses = new List<int>();
        public List<int> Resistances = new List<int>();
        public int ExperienceReward, GoldReward;
        public List<DropEntry> Drops = new List<DropEntry>();
        public float ScaleMult = 1f;
        public int ActionsPerTurn = 1;
        public string AiProfile = "basic";
        public List<string> Summons = new List<string>();
        public int SummonLimit;
        public List<int> SkillWeights = new List<int>();
        public List<string> Skills = new List<string>();
        public string Archetype = "body_only";
        public int BattleRow;
        public float[] Tint = { 1, 1, 1, 1 };
        public List<BossPhase> Phases = new List<BossPhase>();
        public List<string> Gimmicks = new List<string>();
    }

    public sealed class SkillDef
    {
        public string Id;
        public string DisplayName;
        public string Description = "";
        public SkillKind Kind;
        public ScalingStat ScalingStat;
        public TargetType TargetType;
        public Scope Scope;
        public Element Element;
        public float Power = 1f;
        public int HitCount = 1;
        public int MpCost, TpCost;
        public float CritBonus, DefenseIgnore;
        public int Tier = 2;
        public string StatusEffect;            // status id or null
        public float StatusChance;
        public List<string> ExtraStatuses = new List<string>();
        public string BonusVsStatus = "";
        public float BonusVsStatusMult = 1f;
        /// <summary>DAMAGE only: the actor heals this ratio (0..1) of the HP damage the action dealt to opponents.</summary>
        public float Drain;
        public string Presentation;            // presentation id or null
    }

    public sealed class StatusDef
    {
        public string Id;
        public string DisplayName;
        public string Description = "";
        public StatusEffectType EffectType;
        public int DurationTurns = 3;
        public float Magnitude;
        public float[] Tint = { 1, 1, 1, 1 };
        public int AbsorbAmount;
    }

    public sealed class ItemDef
    {
        public string Id;
        public string DisplayName;
        public string Description = "";
        public ItemType ItemType;
        public int HealAmount;
        public int MaxStack = 9;
        public float Power;
        public int Value;
        public string Target = "single_ally";
        public int Price, SellPrice, ShopTier;
        public string StatusId = "";
        public Element Element;
    }

    public sealed class EquipmentDef
    {
        public string Id;
        public string DisplayName;
        public string Description = "";
        public string Slot;                      // weapon | armor | accessory
        public List<string> Classes = new List<string>();
        public int Atk, Mag, Def, Res, Spd, Hp, Mp;
        public float Hit, Evade, Crit;
        public List<int> ElementResists = new List<int>();
        public List<string> StatusImmunities = new List<string>();
        public int Price;
        public int SellPrice = -1;
        public int ShopTier;
        public Dictionary<string, int> CraftMaterials = new Dictionary<string, int>();
        public int CraftGold;
    }

    public sealed class TreasureContents
    {
        public int Gold;
        public Dictionary<string, int> Items = new Dictionary<string, int>();
        public Dictionary<string, int> Equipment = new Dictionary<string, int>();
    }

    public sealed class TreasureDef
    {
        public int[] Cell;                       // [col, row]
        public TreasureContents Contents = new TreasureContents();
    }

    public sealed class EventDef
    {
        public int[] Cell;
        public List<string> Group = new List<string>();
    }

    public sealed class FoeDef
    {
        public string Id;
        public List<string> Group = new List<string>();
        public int[] Spawn;
        public List<int[]> Patrol = new List<int[]>();
        public int ChaseRange;
        public float Power = 1f;
    }

    public sealed class LoreStoneDef
    {
        public int[] Cell;
        public string Text = "";
    }

    public sealed class FloorDef
    {
        public string Id;
        public string FloorLabel;
        public string AreaName;
        public string AreaDescription;
        public List<string> Rows = new List<string>();
        public string Tileset;
        public List<List<string>> EncounterGroups = new List<List<string>>();
        public List<string> ShowcaseGroup = new List<string>();
        public List<string> BossGroup = new List<string>();
        public float[] FogColor;
        public float[] AmbientParticleTint;
        public string Overlay;
        public float EncounterRate;
        public int MinEncounterSteps;
        public List<TreasureDef> Treasures = new List<TreasureDef>();
        public List<EventDef> Events = new List<EventDef>();
        public List<FoeDef> Foes = new List<FoeDef>();
        public string KeyName = "";
        public string LoreText = "";
        public List<LoreStoneDef> LoreStones = new List<LoreStoneDef>();
        public string BossPreText = "";
        public string BossPostText = "";
        [JsonProperty("_file")] public string File;
        /// <summary>Campaign floor index 0..11 (B1F..B12F), derived from FloorLabel.</summary>
        [JsonIgnore] public int Index;
    }

    public sealed class QuestDef
    {
        public string Id;
        public string Title;
        public string Description;
        public string Kind;          // kill | collect | foe | boss | explore
        public string TargetId;
        public int Count = 1;
        public int RewardGold;
        public Dictionary<string, int> RewardItems = new Dictionary<string, int>();
        public int UnlockFloor;
    }

    public sealed class PresentationDef
    {
        public string Id;
        public int Tier = 1;
        public string ActorAction = "attack";   // attack | cast | shoot
        public string Approach = "none";        // none | lunge | dash_to_target
        public string ChargeVfx = "";
        public string TravelVfx = "";
        public string ImpactVfx = "impact";
        public float HitInterval = 0.12f;
        public float HitStop = 0.05f;
        public float Shake = 0.2f;
        public bool ScreenFlash;
        public float[] LightColor = { 1, 1, 1, 1 };
        /// <summary>Optional large effect played once per action at the centre of its targets (field / group spells).</summary>
        public string AreaVfx = "";
        /// <summary>Seconds the area effect leads the first hit (lets a meteor land before the numbers).</summary>
        public float AreaWait;
        public float AreaScale = 1f;
        public string SfxCast = "";
        public string SfxImpact = "";
    }

    /// <summary>Loaded, indexed game database. Load once at boot (Unity: from Resources/Data TextAssets).</summary>
    public sealed class GameDB
    {
        public static GameDB Instance { get; private set; }

        public readonly Dictionary<string, HeroDef> Heroes = new Dictionary<string, HeroDef>();
        public readonly List<string> HeroOrder = new List<string> { "warrior", "mage", "archer", "cleric" };
        public readonly Dictionary<string, EnemyDef> Enemies = new Dictionary<string, EnemyDef>();
        public readonly Dictionary<string, SkillDef> Skills = new Dictionary<string, SkillDef>();
        public readonly Dictionary<string, StatusDef> Statuses = new Dictionary<string, StatusDef>();
        public readonly Dictionary<string, ItemDef> Items = new Dictionary<string, ItemDef>();
        public readonly Dictionary<string, EquipmentDef> Equipment = new Dictionary<string, EquipmentDef>();
        public readonly List<FloorDef> Floors = new List<FloorDef>();          // ordered B1F..B12F
        public readonly Dictionary<string, QuestDef> Quests = new Dictionary<string, QuestDef>();
        public readonly List<QuestDef> QuestList = new List<QuestDef>();
        public readonly Dictionary<string, PresentationDef> Presentations = new Dictionary<string, PresentationDef>();
        public readonly Dictionary<string, string> Text = new Dictionary<string, string>();

        public static readonly JsonSerializerSettings JsonSettings = new JsonSerializerSettings
        {
            ContractResolver = new DefaultContractResolver { NamingStrategy = new SnakeCaseNamingStrategy() },
            MissingMemberHandling = MissingMemberHandling.Ignore,
            NullValueHandling = NullValueHandling.Ignore,
        };

        /// <summary>readTable("skills") must return the JSON text of skills.json.</summary>
        public static GameDB Load(Func<string, string> readTable)
        {
            var db = new GameDB();
            foreach (var h in Parse<HeroDef>(readTable("heroes"))) db.Heroes[h.Id] = h;
            foreach (var e in Parse<EnemyDef>(readTable("enemies"))) db.Enemies[e.Id] = e;
            foreach (var s in Parse<SkillDef>(readTable("skills"))) db.Skills[s.Id] = s;
            foreach (var s in Parse<StatusDef>(readTable("statuses"))) db.Statuses[s.Id] = s;
            foreach (var i in Parse<ItemDef>(readTable("items"))) db.Items[i.Id] = i;
            foreach (var q in Parse<EquipmentDef>(readTable("equipment"))) db.Equipment[q.Id] = q;
            foreach (var p in Parse<PresentationDef>(readTable("presentation"))) db.Presentations[p.Id] = p;
            var floors = Parse<FloorDef>(readTable("dungeon"));
            foreach (var f in floors)
            {
                // "B7F" -> 6
                string digits = f.FloorLabel.Trim('B', 'F');
                f.Index = int.Parse(digits) - 1;
            }
            floors.Sort((a, b) => a.Index.CompareTo(b.Index));
            db.Floors.AddRange(floors);
            foreach (var q in Parse<QuestDef>(readTable("quests"))) { db.Quests[q.Id] = q; db.QuestList.Add(q); }
            db.QuestList.Sort((a, b) => a.UnlockFloor != b.UnlockFloor ? a.UnlockFloor.CompareTo(b.UnlockFloor) : string.CompareOrdinal(a.Id, b.Id));
            var text = JObject.Parse(readTable("text_ko"));
            foreach (var kv in text) db.Text[kv.Key] = (string)kv.Value;
            Instance = db;
            return db;
        }

        static List<T> Parse<T>(string json) => JsonConvert.DeserializeObject<List<T>>(json, JsonSettings);

        /// <summary>Localised UI string by key; returns the key itself when missing.</summary>
        public string T(string key) => Text.TryGetValue(key, out var v) ? v : key;

        public string T(string key, params object[] args)
        {
            string fmt = T(key);
            // Godot strings use printf-style %s / %d; convert sequentially.
            var sb = new System.Text.StringBuilder();
            int ai = 0;
            for (int i = 0; i < fmt.Length; i++)
            {
                if (fmt[i] == '%' && i + 1 < fmt.Length && (fmt[i + 1] == 's' || fmt[i + 1] == 'd'))
                {
                    sb.Append(ai < args.Length ? Convert.ToString(args[ai++], System.Globalization.CultureInfo.InvariantCulture) : "");
                    i++;
                }
                else if (fmt[i] == '%' && i + 1 < fmt.Length && fmt[i + 1] == '%') { sb.Append('%'); i++; }
                else sb.Append(fmt[i]);
            }
            return sb.ToString();
        }
    }
}
