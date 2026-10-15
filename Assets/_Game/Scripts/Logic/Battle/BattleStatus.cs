// Runtime status instance (port of battle_status_effect.gd). Semantics per StatusEffectType:
// POISON/BURN tick at turn end (max HP ratio), BLEED hurts whenever the holder acts, REGEN heals at
// turn end, STUN/FREEZE/SLEEP block actions (SLEEP wakes on damage, FREEZE shatters on the next
// physical hit), SILENCE blocks MP skills, BARRIER absorbs a damage pool, MANA_SHIELD moves damage
// to MP, INVINCIBLE blocks all damage, PROVOKE locks single-target attacks onto its source.
using System.Collections.Generic;

namespace Abyss.Logic.Battle
{
    /// <summary>One status currently affecting a <see cref="BattleUnit"/>.</summary>
    public sealed class BattleStatus
    {
        /// <summary>Lower-case effect names, index = effect type (immunities / bonus_vs_status matching).</summary>
        static readonly string[] TypeNames =
        {
            "poison", "stun", "attack_up", "defense_up", "burn", "bleed", "slow", "freeze", "silence",
            "attack_down", "defense_down", "regen", "barrier", "provoke", "sleep", "blind", "magic_up",
            "speed_up", "mana_shield", "invincible",
        };

        static readonly HashSet<StatusEffectType> BeneficialTypes = new HashSet<StatusEffectType>
        {
            StatusEffectType.AttackUp, StatusEffectType.DefenseUp, StatusEffectType.Regen, StatusEffectType.Barrier,
            StatusEffectType.MagicUp, StatusEffectType.SpeedUp, StatusEffectType.ManaShield, StatusEffectType.Invincible,
            StatusEffectType.Provoke,
        };

        /// <summary>Status id (statuses.json id).</summary>
        public string Id { get; private set; }
        /// <summary>Localised status name.</summary>
        public string DisplayName { get; private set; }
        /// <summary>Source definition.</summary>
        public StatusDef Def { get; private set; }
        /// <summary>Effect type.</summary>
        public StatusEffectType EffectType { get; private set; }
        /// <summary>Turns left; counts down at the end of the holder's own turn.</summary>
        public int TurnsRemaining { get; internal set; }
        /// <summary>Unit id of whoever applied it ("" for pre-battle statuses).</summary>
        public string SourceId { get; private set; } = "";
        /// <summary>Remaining BARRIER absorption pool.</summary>
        public int BarrierRemaining { get; internal set; }
        /// <summary>Buff (true) or ailment (false); ailments are removed by CLEANSE / remedy.</summary>
        public bool IsBeneficial => _beneficial;

        internal double AttackScale = 1, DefenseScale = 1, MagicScale = 1, ResistanceScale = 1, SpeedScale = 1;
        internal int DamagePerTurn, HealPerTurn;
        internal double MaxHpDamageRatio, HealRatioPerTurn, BleedRatio;
        internal double HealingReceivedScale = 1, PhysicalDamageTakenScale = 1, AccuracyScale = 1;
        internal bool CanAct = true, BlocksMpSkills, WakesOnDamage, BreaksOnPhysical, Provoke, Invincible;
        internal double ManaShieldRatio;
        internal bool BarrierFullHit;
        internal double BarrierRatio;
        bool _beneficial;

        /// <summary>Builds a status instance from data (BattleStatusEffect.from_data).</summary>
        public static BattleStatus FromDef(StatusDef def, string appliedBy)
        {
            var s = new BattleStatus
            {
                Def = def,
                Id = def.Id,
                DisplayName = string.IsNullOrEmpty(def.DisplayName) ? def.Id : def.DisplayName,
                TurnsRemaining = System.Math.Max(1, def.DurationTurns),
                EffectType = def.EffectType,
                SourceId = appliedBy ?? "",
            };
            double magnitude = Gd.Clamp(Gd.D(def.Magnitude), 0.0, 1.0);
            switch (def.EffectType)
            {
                case StatusEffectType.Poison: s.MaxHpDamageRatio = magnitude; break;
                case StatusEffectType.Stun: s.CanAct = false; break;
                case StatusEffectType.AttackUp: s.AttackScale = 1.0 + magnitude; break;
                case StatusEffectType.DefenseUp:
                    s.DefenseScale = 1.0 + magnitude;
                    s.ResistanceScale = 1.0 + magnitude;
                    break;
                case StatusEffectType.Burn:
                    s.MaxHpDamageRatio = OrDefault(magnitude, 0.04);
                    s.HealingReceivedScale = 0.5;
                    break;
                case StatusEffectType.Bleed: s.BleedRatio = OrDefault(magnitude, 0.03); break;
                case StatusEffectType.Slow: s.SpeedScale = 1.0 - OrDefault(magnitude, 0.25); break;
                case StatusEffectType.Freeze:
                    s.CanAct = false;
                    s.PhysicalDamageTakenScale = 1.0 + OrDefault(magnitude, 0.3);
                    s.BreaksOnPhysical = true;
                    break;
                case StatusEffectType.Silence: s.BlocksMpSkills = true; break;
                case StatusEffectType.AttackDown:
                    s.AttackScale = 1.0 - OrDefault(magnitude, 0.25);
                    s.MagicScale = s.AttackScale;
                    break;
                case StatusEffectType.DefenseDown:
                    s.DefenseScale = 1.0 - OrDefault(magnitude, 0.25);
                    s.ResistanceScale = s.DefenseScale;
                    break;
                case StatusEffectType.Regen: s.HealRatioPerTurn = OrDefault(magnitude, 0.06); break;
                case StatusEffectType.Barrier:
                    int pool = System.Math.Max(0, def.AbsorbAmount);
                    s.BarrierRemaining = pool;
                    s.BarrierFullHit = false;
                    s.BarrierRatio = pool <= 0 ? magnitude : 0.0;
                    break;
                case StatusEffectType.Provoke: s.Provoke = true; break;
                case StatusEffectType.Sleep:
                    s.CanAct = false;
                    s.WakesOnDamage = true;
                    break;
                case StatusEffectType.Blind: s.AccuracyScale = 1.0 - OrDefault(magnitude, 0.4); break;
                case StatusEffectType.MagicUp: s.MagicScale = 1.0 + magnitude; break;
                case StatusEffectType.SpeedUp: s.SpeedScale = 1.0 + magnitude; break;
                case StatusEffectType.ManaShield: s.ManaShieldRatio = OrDefault(magnitude, 0.5); break;
                case StatusEffectType.Invincible: s.Invincible = true; break;
            }
            s._beneficial = BeneficialTypes.Contains(def.EffectType);
            return s;
        }

        /// <summary>True when this status matches an id or effect-type name (immunities, bonus_vs_status, cures).</summary>
        public bool Matches(string key)
        {
            if (string.IsNullOrEmpty(key)) return false;
            string lowered = key.ToLowerInvariant();
            return Id == key || Id.ToLowerInvariant() == lowered || TypeName() == lowered;
        }

        string TypeName()
        {
            int t = (int)EffectType;
            return t >= 0 && t < TypeNames.Length ? TypeNames[t] : "";
        }

        /// <summary>Resolves holder-relative values (BARRIER magnitude x max HP) when applied.</summary>
        internal void BindTo(int holderMaxHp)
        {
            if (EffectType == StatusEffectType.Barrier && BarrierRemaining <= 0 && !BarrierFullHit)
                BarrierRemaining = System.Math.Max(0, Gd.RoundI(holderMaxHp * BarrierRatio));
        }

        internal void RefreshFrom(BattleStatus o)
        {
            TurnsRemaining = System.Math.Max(TurnsRemaining, o.TurnsRemaining);
            AttackScale = o.AttackScale; DefenseScale = o.DefenseScale; MagicScale = o.MagicScale;
            ResistanceScale = o.ResistanceScale; SpeedScale = o.SpeedScale;
            DamagePerTurn = o.DamagePerTurn; MaxHpDamageRatio = o.MaxHpDamageRatio; HealPerTurn = o.HealPerTurn;
            CanAct = o.CanAct; SourceId = o.SourceId; EffectType = o.EffectType;
            HealRatioPerTurn = o.HealRatioPerTurn; BleedRatio = o.BleedRatio;
            HealingReceivedScale = o.HealingReceivedScale; PhysicalDamageTakenScale = o.PhysicalDamageTakenScale;
            AccuracyScale = o.AccuracyScale; BlocksMpSkills = o.BlocksMpSkills; WakesOnDamage = o.WakesOnDamage;
            BreaksOnPhysical = o.BreaksOnPhysical; Provoke = o.Provoke; Invincible = o.Invincible;
            ManaShieldRatio = o.ManaShieldRatio;
            BarrierRemaining = System.Math.Max(BarrierRemaining, o.BarrierRemaining);
            BarrierFullHit = BarrierFullHit || o.BarrierFullHit;
            Def = o.Def;
            _beneficial = o._beneficial;
        }

        /// <summary>Counts one turn down; true when expired.</summary>
        internal bool Tick()
        {
            TurnsRemaining -= 1;
            return TurnsRemaining <= 0;
        }

        static double OrDefault(double value, double fallback) => value > 0.0 ? value : fallback;
    }
}
