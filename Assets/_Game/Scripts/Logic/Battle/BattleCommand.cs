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
}
