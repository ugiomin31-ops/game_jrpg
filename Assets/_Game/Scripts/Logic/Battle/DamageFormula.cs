// Pure combat math (port of damage_formula.gd, CONTENT_DESIGN §1.2). No state changes; every roll
// uses the battle RNG passed in, in the same order as the GDScript.
using System;

namespace Abyss.Logic.Battle
{
    /// <summary>Result of one damage roll.</summary>
    public struct HitRoll
    {
        public int Amount;
        public bool Critical;
        public bool Missed;
        public DamageType Type;
        public int Element;
        public double ElementMultiplier;
    }

    /// <summary>Damage / healing / hit-chance formulas.</summary>
    public static class DamageFormula
    {
        public const double WeaknessMultiplier = 1.5;
        public const double ResistMultiplier = 0.5;
        public const double BrokenMultiplier = 1.5;
        public const double MinHitChance = 0.25;
        public const double DefenseFactor = 0.55;
        public const double DamageVariance = 0.08;
        public const double HealVariance = 0.05;
        public const double GuardMultiplier = 0.5;

        /// <summary>One hit of a plain attack (<paramref name="skill"/> null) or a damage skill.</summary>
        public static HitRoll Damage(BattleUnit actor, BattleUnit target, SkillDef skill, GodotRng rng)
        {
            var type = DamageTypeOf(skill);
            int element = ElementOf(actor, skill);
            double power = Math.Max(0.0, skill == null ? 1.0 : Gd.D(skill.Power));
            double offense = type == DamageType.Magical ? actor.EffectiveMagic : actor.EffectiveAttack;
            double defense = type == DamageType.Magical ? target.EffectiveResistance : target.EffectiveDefense;
            double defenseIgnore = skill == null ? 0.0 : Gd.Clamp(Gd.D(skill.DefenseIgnore), 0.0, 1.0);
            defense *= 1.0 - defenseIgnore;
            double baseAmount = Math.Max(1.0, offense * power - defense * DefenseFactor);
            baseAmount *= rng.RandfRange(1.0 - DamageVariance, 1.0 + DamageVariance);

            double multiplier = ElementMultiplier(target, element);
            if (rng.Randf() > HitChance(actor, target, type))
                return new HitRoll { Amount = 0, Missed = true, Type = type, Element = element, ElementMultiplier = multiplier };

            double bonusCrit = skill == null ? 0.0 : Gd.D(skill.CritBonus);
            bool critical = type == DamageType.Physical && rng.Randf() < Gd.Clamp(actor.CritRate + bonusCrit, 0.0, 1.0);
            if (critical) baseAmount *= actor.CritMultiplier;
            baseAmount *= multiplier;
            if (target.Broken) baseAmount *= BrokenMultiplier;
            string bonusStatus = skill?.BonusVsStatus ?? "";
            if (bonusStatus != "" && target.HasStatus(bonusStatus))
                baseAmount *= Math.Max(0.0, Gd.D(skill.BonusVsStatusMult));
            if (type == DamageType.Physical) baseAmount *= target.PhysicalDamageTakenScale;
            if (target.Guarding) baseAmount *= GuardMultiplier;
            return new HitRoll
            {
                Amount = Math.Max(1, Gd.RoundI(baseAmount)), Critical = critical, Missed = false, Type = type,
                Element = element, ElementMultiplier = multiplier,
            };
        }

        /// <summary>Physical: actor.hit x BLIND - target.evade, clamped to [0.25, 1]. Magical always hits.</summary>
        public static double HitChance(BattleUnit actor, BattleUnit target, DamageType type)
        {
            if (type != DamageType.Physical) return 1.0;
            double chance = actor.HitRate * actor.AccuracyScale - target.Evade;
            return Gd.Clamp(chance, MinHitChance, 1.0);
        }

        /// <summary>Magical when the skill scales with MAG, else physical (plain attacks are physical).</summary>
        public static DamageType DamageTypeOf(SkillDef skill)
            => skill != null && skill.ScalingStat == ScalingStat.Magic ? DamageType.Magical : DamageType.Physical;

        /// <summary>Skill element; a plain attack (or basic_attack with no element) uses the unit's attack element.</summary>
        public static int ElementOf(BattleUnit actor, SkillDef skill)
        {
            if (skill == null) return actor != null ? actor.AttackElement : 0;
            int element = (int)skill.Element;
            if (element == 0 && actor != null && skill.Id == "basic_attack") return actor.AttackElement;
            return element;
        }

        /// <summary>1.5 when weak, 0.5 when resisted, else 1.</summary>
        public static double ElementMultiplier(BattleUnit target, int element)
        {
            if (target.IsWeakTo(element)) return WeaknessMultiplier;
            if (target.Resists(element)) return ResistMultiplier;
            return 1.0;
        }

        /// <summary>Healing skill amount: stat x power x randf(0.95, 1.05), minimum 1.</summary>
        public static int Healing(BattleUnit actor, SkillDef skill, GodotRng rng)
        {
            double power = Math.Max(0.0, Gd.D(skill.Power));
            double scalingValue = skill.ScalingStat == ScalingStat.Magic ? actor.EffectiveMagic : actor.EffectiveAttack;
            double amount = scalingValue * power;
            amount *= rng.RandfRange(1.0 - HealVariance, 1.0 + HealVariance);
            return Math.Max(1, Gd.RoundI(amount));
        }
    }
}
