// Boundary types between the game/progression layer (Abyss.Logic.Game) and the battle engine
// (Abyss.Logic.Battle). Owned by the lead: fields may be ADDED by either side, never renamed/removed.
using System.Collections.Generic;

namespace Abyss.Logic
{
    public enum BattleKind { Random = 0, Foe = 1, Event = 2, Boss = 3 }
    public enum BattleResult { None = 0, Victory = 1, Defeat = 2, Fled = 3 }

    /// <summary>Fully resolved combat stats of one hero (level, growth and equipment already applied).</summary>
    public sealed class HeroCombatSpec
    {
        public string HeroId;
        public string DisplayName;
        public int Level;
        public int Hp, MaxHp, Mp, MaxMp;          // current HP may be 0 (KO'd going in)
        public int Attack, Magic, Defense, Resistance, Speed;
        public float Hit, Evade, Crit;
        public List<string> Skills = new List<string>();          // usable skill ids incl. basic_attack and ultimates
        public List<int> ElementResists = new List<int>();        // from equipment
        public List<string> StatusImmunities = new List<string>();// from equipment
        public string WeaponId;                                   // for presentation (model attach)
        public string ArmorId, AccessoryId;                       // for presentation (gear aura)
        public int Row;                                           // 0 front, 1 back (if formation is used)
        public Dictionary<string, int> Statuses = new Dictionary<string, int>(); // statuses carried into battle (status id -> turns left), e.g. trap poison
    }

    public sealed class BattleSetup
    {
        public BattleKind Kind = BattleKind.Random;
        public Difficulty Difficulty = Difficulty.Normal;
        public List<HeroCombatSpec> Party = new List<HeroCombatSpec>();
        public List<string> EnemyGroup = new List<string>();      // enemy ids, in formation order
        public float FoePower = 1f;                               // FOE battles only (see CONTENT_DESIGN §8.3)
        public Dictionary<string, int> Inventory = new Dictionary<string, int>(); // consumables available (item id -> count); engine reports usage
        public HashSet<string> KnownWeaknesses = new HashSet<string>();         // "enemyId:element" already discovered
        public string FloorId;                                    // for flavour / backdrop
        public int Seed;
    }

    public sealed class BattleOutcome
    {
        public BattleResult Result;
        public int Experience;
        public int Gold;
        public Dictionary<string, int> Drops = new Dictionary<string, int>();        // item id -> count
        public Dictionary<string, int> ItemsUsed = new Dictionary<string, int>();    // item id -> count consumed
        public List<string> DefeatedEnemies = new List<string>();                    // enemy ids (for quests/bestiary)
        public Dictionary<string, int> FinalHp = new Dictionary<string, int>();      // hero id -> hp
        public Dictionary<string, int> FinalMp = new Dictionary<string, int>();      // hero id -> mp
        public HashSet<string> DiscoveredWeaknesses = new HashSet<string>();
        public bool EscapedDungeon;                                                  // return_stone etc. if usable in battle
        public Dictionary<string, Dictionary<string, int>> FinalStatuses = new Dictionary<string, Dictionary<string, int>>(); // hero id -> status id -> turns left (KO'd = empty)
        public List<string> SeenEnemies = new List<string>();                        // every enemy id that appeared, incl. summons (bestiary "seen")
    }
}
