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

        /// <summary>
        /// One hit of a plain attack (<paramref name="skill"/> null) or a damage skill. <paramref name="elementDamageScale"/>
        /// (e.g. the weakness chain bonus) multiplies the element multiplier used for the amount; the returned
        /// <see cref="HitRoll.ElementMultiplier"/> stays the raw affinity. Draw order and rounding do not depend on it.
        /// <paramref name="powerScale"/> scales the offensive power term before defense subtraction (charged release), not net damage.
        /// </summary>
        public static HitRoll Damage(BattleUnit actor, BattleUnit target, SkillDef skill, GodotRng rng, double elementDamageScale = 1.0, double powerScale = 1.0)
        {
            var type = DamageTypeOf(skill);
            int element = ElementOf(actor, skill);
            double baseAmount = BaseAmount(actor, target, skill, powerScale);
            baseAmount *= rng.RandfRange(1.0 - DamageVariance, 1.0 + DamageVariance);

            double multiplier = ElementMultiplier(target, element);
            if (rng.Randf() > HitChance(actor, target, type))
                return new HitRoll { Amount = 0, Missed = true, Type = type, Element = element, ElementMultiplier = multiplier };

            double bonusCrit = skill == null ? 0.0 : Gd.D(skill.CritBonus);
            bool critical = type == DamageType.Physical && rng.Randf() < Gd.Clamp(actor.CritRate + bonusCrit, 0.0, 1.0);
            if (critical) baseAmount *= actor.CritMultiplier;
            baseAmount = ApplyTargetMultipliers(baseAmount, target, skill, type, multiplier * elementDamageScale, target.Broken);
            return new HitRoll
            {
                Amount = FinalAmount(baseAmount), Critical = critical, Missed = false, Type = type,
                Element = element, ElementMultiplier = multiplier,
            };
        }

        // --- Pure formula terms (shared by the roll above and by RNG-free previews) -----------------

        /// <summary>Offense x power - defense x factor (defense ignore applied), at least 1, before variance.
        /// Optional targetTurnsElapsed forecasts target status expiry without changing the unit; 0 preserves live/default math.</summary>
        public static double BaseAmount(BattleUnit actor, BattleUnit target, SkillDef skill, double powerScale = 1.0, int targetTurnsElapsed = 0)
        {
            var type = DamageTypeOf(skill);
            double power = Math.Max(0.0, skill == null ? 1.0 : Gd.D(skill.Power));
            double offense = type == DamageType.Magical ? actor.EffectiveMagic : actor.EffectiveAttack;
            double defense;
            if (targetTurnsElapsed <= 0) defense = type == DamageType.Magical ? target.EffectiveResistance : target.EffectiveDefense;
            else
            {
                double scale = 1;
                foreach (var status in target.Statuses)
                    if (status.TurnsRemaining > targetTurnsElapsed)
                        scale *= type == DamageType.Magical ? status.ResistanceScale : status.DefenseScale;
                defense = Math.Max(0, Gd.RoundI((type == DamageType.Magical ? target.Resistance : target.Defense) * scale));
            }
            double defenseIgnore = skill == null ? 0.0 : Gd.Clamp(Gd.D(skill.DefenseIgnore), 0.0, 1.0);
            defense *= 1.0 - defenseIgnore;
            return Math.Max(1.0, offense * power * powerScale - defense * DefenseFactor);
        }

        /// <summary>
        /// Multipliers applied after variance (and crit), in the roll's exact order: element, BREAK, bonus vs
        /// status, physical damage taken, guard. <paramref name="broken"/> is passed in so previews can model a
        /// mid-action BREAK without touching the unit.
        /// </summary>
        public static double ApplyTargetMultipliers(double amount, BattleUnit target, SkillDef skill, DamageType type, double elementMultiplier, bool broken,
            int targetTurnsElapsed = 0, bool? guarding = null)
        {
            amount *= elementMultiplier;
            if (broken) amount *= BrokenMultiplier;
            string bonusStatus = skill?.BonusVsStatus ?? "";
            bool bonusActive = false;
            foreach (var status in target.Statuses)
                if ((targetTurnsElapsed <= 0 || status.TurnsRemaining > targetTurnsElapsed) && bonusStatus != "" && status.Matches(bonusStatus)) bonusActive = true;
            if (bonusActive) amount *= Math.Max(0.0, Gd.D(skill.BonusVsStatusMult));
            if (type == DamageType.Physical)
            {
                double scale = 1;
                foreach (var status in target.Statuses)
                    if (targetTurnsElapsed <= 0 || status.TurnsRemaining > targetTurnsElapsed) scale *= status.PhysicalDamageTakenScale;
                amount *= scale;
            }
            if (guarding ?? target.Guarding) amount *= GuardMultiplier;
            return amount;
        }

        /// <summary>Rounded hit amount (minimum 1).</summary>
        public static int FinalAmount(double amount) => Math.Max(1, Gd.RoundI(amount));

        /// <summary>Lowest value <see cref="GodotRng.RandfRange"/> can return for 1 +/- <paramref name="variance"/> (float arithmetic).</summary>
        public static double LowestRoll(double variance) => (float)(1.0 - variance);

        /// <summary>Highest value <see cref="GodotRng.RandfRange"/> can return for 1 +/- <paramref name="variance"/> (randf just below 1).</summary>
        public static double HighestRoll(double variance)
        {
            float from = (float)(1.0 - variance), to = (float)(1.0 + variance);
            float r = 0.99999994f; // largest float below 1
            float scaled = r * (to - from);
            return scaled + from;
        }

        /// <summary>DAMAGE item amount: fixed value (or power x 100) x element multiplier (x BREAK), minimum 1; never misses.</summary>
        public static int FixedItemAmount(ItemDef item, double elementMultiplier, bool broken)
        {
            int baseAmount = item.Value;
            if (baseAmount <= 0) baseAmount = Gd.RoundI(Math.Max(0.0, Gd.D(item.Power)) * 100.0);
            double amount = baseAmount * elementMultiplier;
            if (broken) amount *= BrokenMultiplier;
            return Math.Max(1, Gd.RoundI(amount));
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
            double amount = HealingBase(actor, skill);
            amount *= rng.RandfRange(1.0 - HealVariance, 1.0 + HealVariance);
            return Math.Max(1, Gd.RoundI(amount));
        }

        /// <summary>Healing skill amount before variance: scaling stat x power.</summary>
        public static double HealingBase(BattleUnit actor, SkillDef skill)
        {
            double power = Math.Max(0.0, Gd.D(skill.Power));
            double scalingValue = skill.ScalingStat == ScalingStat.Magic ? actor.EffectiveMagic : actor.EffectiveAttack;
            return scalingValue * power;
        }
    }
}
