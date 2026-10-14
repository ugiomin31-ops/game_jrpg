// Player command input and the command-menu description returned by BattleEngine.GetCommandOptions.
using System.Collections.Generic;

namespace Abyss.Logic.Battle
{
    /// <summary>Hero command kinds.</summary>
    public enum CommandKind { Attack = 0, Skill = 1, Item = 2, Guard = 3, Flee = 4 }

    /// <summary>How an action picks its targets.</summary>
    public enum TargetRule
    {
        None = 0,
        Self = 1,
        SingleEnemy = 2,
        SingleAlly = 3,
        AllEnemies = 4,
        AllAllies = 5,
        RandomEnemies = 6,
        RandomAllies = 7,
        /// <summary>Every living unit on both sides.</summary>
        All = 8,
    }

    /// <summary>Effect family of a skill / item.</summary>
    public enum ActionEffect { Damage = 0, DamageFixed = 1, Heal = 2, Buff = 3, Debuff = 4, Status = 5, Revive = 6, Cleanse = 7, RestoreMp = 8, Flee = 9, Unusable = 10 }

    /// <summary>One hero command. <see cref="TargetId"/> is a unit id; null lets the engine pick (ALL / RANDOM / SELF / first valid).</summary>
    public sealed class BattleCommand
    {
        public CommandKind Kind;
        public string SkillId;
        public string ItemId;
        public string TargetId;

        public static BattleCommand Attack(string targetId) => new BattleCommand { Kind = CommandKind.Attack, TargetId = targetId };
        public static BattleCommand Skill(string skillId, string targetId = null) => new BattleCommand { Kind = CommandKind.Skill, SkillId = skillId, TargetId = targetId };
        public static BattleCommand Item(string itemId, string targetId = null) => new BattleCommand { Kind = CommandKind.Item, ItemId = itemId, TargetId = targetId };
        public static BattleCommand Guard() => new BattleCommand { Kind = CommandKind.Guard };
        public static BattleCommand Flee() => new BattleCommand { Kind = CommandKind.Flee };

        public override string ToString()
        {
            switch (Kind)
            {
                case CommandKind.Skill: return $"Skill({SkillId}->{TargetId})";
                case CommandKind.Item: return $"Item({ItemId}->{TargetId})";
                case CommandKind.Attack: return $"Attack({TargetId})";
                default: return Kind.ToString();
            }
        }
    }

    /// <summary>A skill entry of the command menu (basic_attack is the Attack command and is not listed).</summary>
    public sealed class SkillOption
    {
        public SkillDef Skill;
        public string Id;
        public string DisplayName;
        public int MpCost;
        public int TpCost;
        /// <summary>TP-cost skill (ultimate); silence does not block it.</summary>
        public bool IsUltimate;
        public bool Usable;
        /// <summary>text_ko key when unusable: reason_silence, reason_mp, reason_tp, reason_no_target; else null.</summary>
        public string ReasonKey;
        public TargetRule Target;
        public ActionEffect Effect;
        /// <summary>Known weak/resist tag against living enemies; filled only by <see cref="BattleEngine.SkillMenu"/>.</summary>
        public SkillAffinityTag KnownAffinity;
    }

    /// <summary>A consumable entry of the item menu.</summary>
    public sealed class ItemOption
    {
        public ItemDef Item;
        public string Id;
        public string DisplayName;
        public int Count;
        public ActionEffect Effect;
        public TargetRule Target;
        public bool Usable;
        /// <summary>text_ko key when unusable (flee_blocked, reason_no_target); else null.</summary>
        public string ReasonKey;
    }

    /// <summary>Everything the command menu needs for one hero.</summary>
    public sealed class CommandOptions
    {
        public BattleUnit Actor;
        public IReadOnlyList<SkillOption> Skills;
        public IReadOnlyList<ItemOption> Items;
        /// <summary>True when an ultimate (TP skill) is usable right now.</summary>
        public bool UltimateReady;
        public bool CanFlee;
        /// <summary>"flee_blocked" when fleeing is not allowed, else null.</summary>
        public string FleeReasonKey;
        public bool CanAttack = true;
        public bool CanGuard = true;
    }

    /// <summary>What a preview estimates.</summary>
    public enum PreviewKind { None = 0, Damage = 1, Heal = 2 }

    /// <summary>
    /// The player's knowledge of how a target takes an element (never the hidden truth). Unknown previews use the
    /// neutral multiplier and must be shown as "?". There is no immunity: the formula has none.
    /// </summary>
    public enum PreviewAffinity { Unknown = 0, Neutral = 1, Weak = 2, Resist = 3 }

    /// <summary>Estimate for one target of a previewed command. Immutable.</summary>
    public sealed class TargetPreview
    {
        /// <summary>Engine unit index (position in <see cref="BattleEngine.Units"/>).</summary>
        public int UnitIndex { get; }
        public string UnitId { get; }
        /// <summary>
        /// Non-crit range at the lowest / highest variance roll: the sum over all hits for single / all scope,
        /// one hit for random scope (<see cref="ActionPreview.Random"/>). HP damage before barrier / mana-shield
        /// absorption; misses ignored. For heals, the HP restored (before the missing-HP cap).
        /// </summary>
        public int Min { get; }
        public int Max { get; }
        /// <summary>Known affinity to the action's element (damage only; Neutral for heals and non-elemental hits).</summary>
        public PreviewAffinity Affinity { get; }
        /// <summary>Shield points the action removes: known-weak hits capped at the current shield (0 when Unknown or random).</summary>
        public int ShieldDamage { get; }
        /// <summary>The known-weak hits empty the shield during this action (later hits use the BREAK multiplier).</summary>
        public bool Breaks { get; }
        /// <summary>Total minimum damage reaches the target's current HP (never for random scope or heals).</summary>
        public bool Lethal { get; }
        /// <summary>Barrier / mana shield / invincibility would absorb part of the damage.</summary>
        public bool Shielded { get; }

        public TargetPreview(int unitIndex, string unitId, int min, int max, PreviewAffinity affinity, int shieldDamage, bool breaks, bool lethal, bool shielded)
        {
            UnitIndex = unitIndex; UnitId = unitId; Min = min; Max = max; Affinity = affinity;
            ShieldDamage = shieldDamage; Breaks = breaks; Lethal = lethal; Shielded = shielded;
        }
    }

    /// <summary>
    /// Knowledge-safe, RNG-free estimate of a hero command (<see cref="BattleEngine.PreviewAction"/>). Immutable;
    /// <see cref="None"/> means "show no numbers".
    /// </summary>
    public sealed class ActionPreview
    {
        public static readonly ActionPreview None = new ActionPreview(PreviewKind.None, false, 0, 0, null);

        public PreviewKind Kind { get; }
        /// <summary>Random scope: each target's Min/Max is one hit and <see cref="HitCount"/> hits land on random targets.</summary>
        public bool Random { get; }
        /// <summary>Hits per target (single / all) or random picks (random scope); 1 for heals and items.</summary>
        public int HitCount { get; }
        /// <summary>Element of the action (0 = none).</summary>
        public int Element { get; }
        /// <summary>One entry per affected target, in target order.</summary>
        public IReadOnlyList<TargetPreview> Targets { get; }

        public ActionPreview(PreviewKind kind, bool random, int hitCount, int element, IList<TargetPreview> targets)
        {
            Kind = kind; Random = random; HitCount = hitCount; Element = element;
            Targets = new System.Collections.ObjectModel.ReadOnlyCollection<TargetPreview>(targets != null ? new List<TargetPreview>(targets) : new List<TargetPreview>());
        }

        /// <summary>The entry for a unit id, or null.</summary>
        public TargetPreview For(string unitId)
        {
            foreach (var t in Targets) if (t.UnitId == unitId) return t;
            return null;
        }
    }

    /// <summary>Immutable public value of one planned enemy action. IDs are stable unit IDs, never indices.</summary>
    public sealed class EnemyIntent
    {
        public int Round { get; }
        public string EnemyUnitId { get; }
        public int Slot { get; }
        public ActionKind Kind { get; }
        public string SkillId { get; }
        public string PayloadId { get; }
        public string TargetUnitId { get; }
        public Scope Scope { get; }
        public bool IsRandom => Scope == Scope.Random;
        public bool IsChargeAnnounce { get; }
        public bool IsChargeRelease { get; }

        internal EnemyIntent(int round, string enemyId, int slot, BattleAction action)
        {
            Round = round; EnemyUnitId = enemyId; Slot = slot; Kind = action.Kind;
            SkillId = action.Kind == ActionKind.Attack ? "basic_attack" : action.Kind == ActionKind.Skill ? action.PayloadId : "";
            PayloadId = action.Kind == ActionKind.Summon || action.Kind == ActionKind.Item ? action.PayloadId : "";
            Scope = (Scope)action.Scope;
            TargetUnitId = action.Scope == 0 && action.TargetIds.Count > 0 ? action.TargetIds[0] : null;
            IsChargeAnnounce = action.IsChargeAnnounce; IsChargeRelease = action.IsChargeRelease;
        }
    }

    /// <summary>Announced charge: immutable identifiers only; the engine keeps the prepared skill privately.</summary>
    public sealed class PendingCharge
    {
        public string SkillId { get; }
        public string TargetUnitId { get; }
        public int AnnouncedRound { get; }
        public Scope Scope { get; }
        public PendingCharge(string skillId, string targetUnitId, int announcedRound, Scope scope)
        { SkillId = skillId; TargetUnitId = targetUnitId; AnnouncedRound = announcedRound; Scope = scope; }
    }

    /// <summary>Known affinity tag of a skill against the current living enemies (knowledge only).</summary>
    public enum SkillAffinityTag { None = 0, Weak = 1, Resist = 2 }
}
