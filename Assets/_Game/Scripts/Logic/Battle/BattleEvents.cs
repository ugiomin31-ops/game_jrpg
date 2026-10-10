// Presentation events produced by BattleEngine, in exact chronological order. Every event carries the
// values the view needs (HP after the hit, remaining turns, ...) so playback never reads live state.
using System.Collections.Generic;

namespace Abyss.Logic.Battle
{
    /// <summary>Base class of every battle event.</summary>
    public abstract class BattleEvent
    {
        /// <summary>Running index of the event within the battle (0-based).</summary>
        public int Seq { get; internal set; }
    }

    /// <summary>Element effectiveness of a hit.</summary>
    public enum Effectiveness { Normal = 0, Weak = 1, Resist = 2 }

    /// <summary>What a unit did on its action.</summary>
    public enum ActionKind { Attack = 0, Skill = 1, Item = 2, Guard = 3, Flee = 4, Summon = 5 }

    /// <summary>Why a status disappeared.</summary>
    public enum StatusRemoveReason
    {
        /// <summary>Duration ran out at the end of the holder's turn.</summary>
        Expired = 0,
        /// <summary>Removed by damage: SLEEP woke up, FREEZE shattered, BARRIER depleted.</summary>
        Damage = 1,
        /// <summary>Removed by a CLEANSE skill or cure item.</summary>
        Cleansed = 2,
        /// <summary>The holder was knocked out.</summary>
        Down = 3,
    }

    /// <summary>Battle began. Contains every unit as it enters (initial statuses included).</summary>
    public sealed class BattleStartEvent : BattleEvent
    {
        public IReadOnlyList<UnitSnapshot> Units;
    }

    /// <summary>A new round; <see cref="TurnOrder"/> is the full action order (unit ids) of this round.</summary>
    public sealed class RoundStartEvent : BattleEvent
    {
        public int Round;
        public IReadOnlyList<string> TurnOrder;
    }

    /// <summary>A unit's turn begins (guard drops). Followed by a skip, a command request or enemy actions.</summary>
    public sealed class TurnStartEvent : BattleEvent
    {
        public string UnitId;
        public int Round;
    }

    /// <summary>The unit loses its turn (BREAK or STUN/FREEZE/SLEEP). A <see cref="MessageEvent"/> follows.</summary>
    public sealed class TurnSkippedEvent : BattleEvent
    {
        public string UnitId;
        /// <summary>True when skipped because of BREAK (the unit recovers at the end of this turn).</summary>
        public bool Broken;
    }

    /// <summary>
    /// A turn finished, after status ticks/expiry and BREAK recovery. The copied state includes guard
    /// and remaining status durations, so presentation can replay them without reading live units.
    /// </summary>
    public sealed class TurnEndEvent : BattleEvent
    {
        public UnitSnapshot Unit;
    }

    /// <summary>The engine now waits for a command for this hero (always the last event of a batch).</summary>
    public sealed class CommandRequestedEvent : BattleEvent
    {
        public string UnitId;
    }

    /// <summary>An action starts. Target ids are the resolved targets (RANDOM may repeat a unit).</summary>
    public sealed class ActionStartEvent : BattleEvent
    {
        public string ActorId;
        public ActionKind Kind;
        /// <summary>Skill id (Skill), item id (Item), summoned enemy id (Summon), else null.</summary>
        public string SkillId;
        public string ItemId;
        /// <summary>Localised name of the skill / item (null for attack, guard, flee, summon).</summary>
        public string DisplayName;
        /// <summary>Presentation id (presentation.json) of the skill, or null.</summary>
        public string PresentationId;
        public IReadOnlyList<string> TargetIds;
        public Scope Scope;
        public int Element;
        public int HitCount;
        public bool IsUltimate;
        public bool IsChargeAnnounce, IsChargeRelease;
    }

    /// <summary>The action finished resolving.</summary>
    public sealed class ActionEndEvent : BattleEvent
    {
        public string ActorId;
        public ActionKind Kind;
    }

    /// <summary>HP damage to a unit (also DoT ticks and bleed: <see cref="Type"/> == Status).</summary>
    public sealed class DamageEvent : BattleEvent
    {
        public string TargetId;
        /// <summary>Attacker unit id, or the status' source for DoT ("" when unknown).</summary>
        public string SourceId;
        /// <summary>HP actually lost (0 when fully absorbed by a barrier / invincibility).</summary>
        public int Amount;
        /// <summary>Damage absorbed by BARRIER / INVINCIBLE / MANA_SHIELD.</summary>
        public int Absorbed;
        public bool Critical;
        public DamageType Type;
        public int Element;
        public Effectiveness Effectiveness;
        /// <summary>True on the first weak/resist hit of this target in this action (show the popup once).</summary>
        public bool ShowEffectiveness;
        /// <summary>0-based hit index on this target within the action (multi-hit).</summary>
        public int HitIndex;
        /// <summary>Status id that caused this damage (DoT / bleed), else null.</summary>
        public string StatusId;
        public int HpAfter;
        public int MaxHp;
        /// <summary>The hit knocked the unit out (a <see cref="UnitDownEvent"/> follows).</summary>
        public bool Killed;
    }

    /// <summary>A physical hit missed.</summary>
    public sealed class MissEvent : BattleEvent
    {
        public string TargetId;
        public string SourceId;
        public int HitIndex;
    }

    /// <summary>HP restored (skills, items, REGEN, revive).</summary>
    public sealed class HealEvent : BattleEvent
    {
        public string TargetId;
        public string SourceId;
        public int Amount;
        /// <summary>Status id for REGEN ticks, else null.</summary>
        public string StatusId;
        public int HpAfter;
        public int MaxHp;
    }

    /// <summary>MP changed (cost, restore, MANA_SHIELD absorption).</summary>
    public sealed class MpChangeEvent : BattleEvent
    {
        public string UnitId;
        public int Mp, MaxMp, Delta;
    }

    /// <summary>TP changed.</summary>
    public sealed class TpChangeEvent : BattleEvent
    {
        public string UnitId;
        public int Tp, MaxTp, Delta;
    }

    /// <summary>A status was applied (or refreshed, same id).</summary>
    public sealed class StatusAppliedEvent : BattleEvent
    {
        public string UnitId;
        public string StatusId;
        public string DisplayName;
        public StatusEffectType EffectType;
        public int Turns;
        public bool Beneficial;
        public bool Refreshed;
        public string SourceId;
    }

    /// <summary>A status ended.</summary>
    public sealed class StatusRemovedEvent : BattleEvent
    {
        public string UnitId;
        public string StatusId;
        public StatusRemoveReason Reason;
    }

    /// <summary>A status did not take because of an immunity (equipment or cc_immune).</summary>
    public sealed class StatusImmuneEvent : BattleEvent
    {
        public string UnitId;
        public string StatusId;
    }

    /// <summary>Break shield pips changed.</summary>
    public sealed class ShieldChangeEvent : BattleEvent
    {
        public string UnitId;
        public int Shield, MaxShield;
    }

    /// <summary>The unit's shield hit 0: it is BROKEN (skips its next turn, takes x1.5 damage).</summary>
    public sealed class BreakEvent : BattleEvent
    {
        public string UnitId;
    }

    /// <summary>
    /// The party's weakness chain (battle-local, 0..<see cref="BattleEngine.ChainMax"/>) changed: +1 after a party action
    /// that landed a weakness hit, 0 after a party damaging action without one, and 0 when the battle ends.
    /// </summary>
    public sealed class ChainChangedEvent : BattleEvent
    {
        public int OldValue { get; }
        public int NewValue { get; }

        public ChainChangedEvent(int oldValue, int newValue)
        {
            OldValue = oldValue;
            NewValue = newValue;
        }
    }

    /// <summary>Immutable, replayable intent snapshot (no live unit/skill references).</summary>
    public sealed class EnemyIntentPlannedEvent : BattleEvent
    {
        public EnemyIntent Intent { get; }
        public int Round => Intent.Round;
        public string EnemyUnitId => Intent.EnemyUnitId;
        public int Slot => Intent.Slot;
        public ActionKind Kind => Intent.Kind;
        public string SkillId => Intent.SkillId;
        public string PayloadId => Intent.PayloadId;
        public string TargetUnitId => Intent.TargetUnitId;
        public Scope Scope => Intent.Scope;
        public bool IsRandom => Intent.IsRandom;
        public bool IsChargeAnnounce => Intent.IsChargeAnnounce;
        public bool IsChargeRelease => Intent.IsChargeRelease;
        public EnemyIntentPlannedEvent(EnemyIntent intent) { Intent = intent; }
    }
    public sealed class IntentClearedEvent : BattleEvent
    {
        public string EnemyUnitId { get; }
        public int Slot { get; }
        public IntentClearedEvent(string enemyUnitId, int slot) { EnemyUnitId = enemyUnitId; Slot = slot; }
    }
    public sealed class ChargeStartedEvent : BattleEvent
    {
        public string EnemyUnitId { get; }
        public string SkillId { get; }
        public string TargetUnitId { get; }
        public ChargeStartedEvent(string enemyUnitId, string skillId, string targetUnitId)
        { EnemyUnitId = enemyUnitId; SkillId = skillId; TargetUnitId = targetUnitId; }
    }
    public sealed class ChargeReleasedEvent : BattleEvent
    {
        public string EnemyUnitId { get; }
        public string SkillId { get; }
        public ChargeReleasedEvent(string enemyUnitId, string skillId) { EnemyUnitId = enemyUnitId; SkillId = skillId; }
    }
    public enum ChargeCancelReason { Break = 0, Removed = 1 }
    public sealed class ChargeCancelledEvent : BattleEvent
    {
        public string EnemyUnitId { get; }
        public ChargeCancelReason Reason { get; }
        public ChargeCancelledEvent(string enemyUnitId, ChargeCancelReason reason) { EnemyUnitId = enemyUnitId; Reason = reason; }
    }

    /// <summary>The unit recovered from BREAK (shield refilled).</summary>
    public sealed class RecoverEvent : BattleEvent
    {
        public string UnitId;
        public int Shield, MaxShield;
    }

    /// <summary>The unit was knocked out.</summary>
    public sealed class UnitDownEvent : BattleEvent
    {
        public string UnitId;
    }

    /// <summary>A knocked-out unit came back.</summary>
    public sealed class ReviveEvent : BattleEvent
    {
        public string UnitId;
        public int Hp, MaxHp;
    }

    /// <summary>A weakness hit was registered for an enemy type the player did not know yet.</summary>
    public sealed class WeaknessDiscoveredEvent : BattleEvent
    {
        public string UnitId;
        public string EnemyId;
        public int Element;
    }

    /// <summary>A new enemy joined the battle.</summary>
    public sealed class SummonEvent : BattleEvent
    {
        public string SummonerId;
        public UnitSnapshot Unit;
    }

    /// <summary>A boss entered a phase (index into its phases); <see cref="Line"/> is the spoken line.</summary>
    public sealed class BossPhaseEvent : BattleEvent
    {
        public string UnitId;
        public int PhaseIndex;
        public string Line;
        public int ActionsPerTurn;
    }

    /// <summary>A berserker enraged (attack_up_berserk follows as a status event).</summary>
    public sealed class EnrageEvent : BattleEvent
    {
        public string UnitId;
    }

    /// <summary>Battle log line: text_ko key plus format args; <see cref="Text"/> is already formatted.</summary>
    public sealed class MessageEvent : BattleEvent
    {
        public string Key;
        public IReadOnlyList<string> Args;
        public string Text;
    }

    /// <summary>Flee attempt result (command or smoke bomb).</summary>
    public sealed class FleeEvent : BattleEvent
    {
        public bool Success;
        public bool SmokeBomb;
    }

    /// <summary>The battle ended; <see cref="Outcome"/> is the same object as BattleEngine.Outcome.</summary>
    public sealed class BattleEndEvent : BattleEvent
    {
        public BattleResult Result;
        public BattleOutcome Outcome;
    }

    /// <summary>A submitted command was refused; state is unchanged and the same hero is still asked.</summary>
    public sealed class CommandRejectedEvent : BattleEvent
    {
        /// <summary>text_ko key (mp_short, tp_short, silenced, item_unavailable, flee_forbidden, invalid_target, ...).</summary>
        public string Key;
        public string Text;
    }
}
