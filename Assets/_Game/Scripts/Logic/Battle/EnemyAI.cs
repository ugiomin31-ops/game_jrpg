// Enemy decision making (port of enemy_ai.gd, CONTENT_DESIGN §7.1). Reads units and consumes only the
// supplied battle RNG; returns one action. The engine freezes it at planning and handles execution fallback.
// Profiles: basic (weighted random), aggressive (lowest HP % target), caster (75 % non-basic skills),
// support (revive / heal below 60 % / cleanse first), summoner (35 % summon while slots are free),
// berserker (lowest HP % target once enraged), boss (phase skills/weights). Hard: basic acts
// aggressive 40 % of the time.
using System.Collections.Generic;

namespace Abyss.Logic.Battle
{
    /// <summary>Internal resolved action (port of battle_action.gd).</summary>
    internal sealed class BattleAction
    {
        public ActionKind Kind;
        public string ActorId;
        public List<string> TargetIds = new List<string>();
        public string PayloadId = "";
        public SkillDef Skill;
        public ItemDef Item;
        /// <summary>0 single, 1 all, 2 random (filled by target resolution).</summary>
        public int Scope;
        public bool FrozenSingleTarget, LowestHpTarget;
        public bool IsChargeAnnounce, IsChargeRelease;
        public double PowerScale = 1.0;

        public static BattleAction Make(ActionKind kind, string actorId, IEnumerable<string> targets = null, string payloadId = "", SkillDef skill = null)
        {
            var a = new BattleAction { Kind = kind, ActorId = actorId, PayloadId = payloadId ?? "", Skill = skill };
            if (targets != null) a.TargetIds.AddRange(targets);
            return a;
        }
    }

    internal static class EnemyAI
    {
        const double HardAggressiveChance = 0.4;
        const double SupportHealBelow = 0.6;
        const double SummonChance = 0.35;
        /// <summary>Rare-monster profile: each turn it may run away (no rewards); otherwise it acts like "basic".</summary>
        public const string RunnerProfile = "runner";
        public const double RunnerFleeChance = 0.4;

        struct Option
        {
            public SkillDef Skill;
            public double Weight;
            public bool Basic;
        }

        public static BattleAction Choose(BattleUnit actor, List<BattleUnit> opponents, List<BattleUnit> allies,
            GodotRng rng, Difficulty difficulty, int summonSlots, bool excludeCharge = false)
        {
            excludeCharge |= actor.PendingCharge != null;
            var livingOpponents = Living(opponents);
            var livingAllies = Living(allies);
            if (livingOpponents.Count == 0)
                return BattleAction.Make(ActionKind.Guard, actor.Id, new[] { actor.Id });

            if (actor.AiProfile == RunnerProfile && rng.Randf() < RunnerFleeChance)
                return BattleAction.Make(ActionKind.Flee, actor.Id);
            string profile = actor.AiProfile;
            if (profile == "basic" && difficulty == Difficulty.Hard && rng.Randf() < HardAggressiveChance)
                profile = "aggressive";

            var fallenAllies = Fallen(allies);
            if (profile == "support")
            {
                var support = SupportAction(actor, livingAllies, fallenAllies);
                if (support != null) return support;
            }
            else if (profile == "summoner")
            {
                if (summonSlots > 0 && actor.Summons.Count > 0 && rng.Randf() < SummonChance)
                {
                    string summonId = actor.Summons[rng.RandiRange(0, actor.Summons.Count - 1)];
                    return BattleAction.Make(ActionKind.Summon, actor.Id, null, summonId);
                }
            }

            var options = SkillOptions(actor, livingAllies, fallenAllies, excludeCharge);
            bool lowestHp = profile == "aggressive" || (profile == "berserker" && actor.Enraged);

            if (options.Count == 0) return AttackAction(actor, livingOpponents, lowestHp, rng);

            SkillDef selected;
            if (profile == "caster")
            {
                var spells = new List<Option>();
                foreach (var o in options) if (!o.Basic) spells.Add(o);
                if (spells.Count > 0 && rng.Randf() < 0.75) selected = WeightedSkill(spells, rng);
                else return AttackAction(actor, livingOpponents, lowestHp, rng);
            }
            else
            {
                selected = WeightedSkill(options, rng);
            }
            if (selected.Id == "basic_attack") return AttackAction(actor, livingOpponents, lowestHp, rng);
            var action = SkillAction(actor, selected, livingOpponents, livingAllies, fallenAllies, lowestHp, rng);
            action.LowestHpTarget = lowestHp;
            return action;
        }

        static List<Option> SkillOptions(BattleUnit actor, List<BattleUnit> livingAllies, List<BattleUnit> fallenAllies, bool excludeCharge)
        {
            var options = new List<Option>();
            for (int i = 0; i < actor.SkillList.Count; i++)
            {
                var skill = actor.SkillList[i];
                if (excludeCharge && skill.Id == actor.ChargeSkill) continue;
                if (!IsAffordable(actor, skill)) continue;
                double weight = i < actor.SkillWeights.Count ? actor.SkillWeights[i] : 1.0;
                if (weight <= 0.0) continue;
                switch (skill.Kind)
                {
                    case SkillKind.Heal: if (skill.TargetType == TargetType.Self ? actor.Hp >= actor.MaxHp : MostInjured(livingAllies, 0.999) == null) continue; break;
                    case SkillKind.Revive: if (fallenAllies.Count == 0) continue; break;
                    case SkillKind.Cleanse: if (skill.TargetType == TargetType.Self ? !HasAilment(actor) : Afflicted(livingAllies) == null) continue; break;
                    case SkillKind.Buff:
                        if (skill.TargetType == TargetType.Self ? !NeedsBuff(actor, skill) : !livingAllies.Exists(a => NeedsBuff(a, skill))) continue;
                        break;
                }
                options.Add(new Option { Skill = skill, Weight = weight, Basic = skill.Id == "basic_attack" });
            }
            return options;
        }

        static bool NeedsBuff(BattleUnit unit, SkillDef skill)
        {
            if (!string.IsNullOrEmpty(skill.StatusEffect) && !unit.HasStatus(skill.StatusEffect)) return true;
            foreach (var id in skill.ExtraStatuses) if (!unit.HasStatus(id)) return true;
            return false;
        }
        static bool HasAilment(BattleUnit unit)
        {
            foreach (var status in unit.Statuses) if (!status.IsBeneficial) return true;
            return false;
        }

        /// <summary>MP / TP affordable and not blocked by silence.</summary>
        public static bool IsAffordable(BattleUnit actor, SkillDef skill)
        {
            int mp = System.Math.Max(0, skill.MpCost), tp = System.Math.Max(0, skill.TpCost);
            if (actor.Mp < mp || actor.Tp < tp) return false;
            return !(mp > 0 && actor.IsSilenced);
        }

        static BattleAction SupportAction(BattleUnit actor, List<BattleUnit> livingAllies, List<BattleUnit> fallenAllies)
        {
            SkillDef heal = null, revive = null, cleanse = null;
            for (int i = 0; i < actor.SkillList.Count; i++)
            {
                var skill = actor.SkillList[i];
                if (i < actor.SkillWeights.Count && actor.SkillWeights[i] <= 0) continue;
                if (!IsAffordable(actor, skill)) continue;
                switch (skill.Kind)
                {
                    case SkillKind.Heal: heal ??= skill; break;
                    case SkillKind.Revive: revive ??= skill; break;
                    case SkillKind.Cleanse: cleanse ??= skill; break;
                }
            }
            if (revive != null && fallenAllies.Count > 0) return MakeSkill(actor, revive, fallenAllies[0]);
            var injured = MostInjured(livingAllies, SupportHealBelow);
            if (heal != null && injured != null)
            {
                if (heal.TargetType == TargetType.Self)
                {
                    if ((double)actor.Hp / actor.MaxHp < SupportHealBelow) return MakeSkill(actor, heal, actor);
                }
                else return MakeSkill(actor, heal, injured);
            }
            var afflicted = Afflicted(livingAllies);
            if (cleanse != null && afflicted != null) return MakeSkill(actor, cleanse, afflicted);
            return null;
        }

        static BattleAction SkillAction(BattleUnit actor, SkillDef skill, List<BattleUnit> livingOpponents,
            List<BattleUnit> livingAllies, List<BattleUnit> fallenAllies, bool lowestHp, GodotRng rng)
        {
            if (skill.TargetType == TargetType.Self) return MakeSkill(actor, skill, actor);
            if (skill.Scope != Scope.Single)
                return BattleAction.Make(ActionKind.Skill, actor.Id, null, skill.Id, skill);
            BattleUnit target;
            switch (skill.Kind)
            {
                case SkillKind.Heal: target = MostInjured(livingAllies, 0.999); break;
                case SkillKind.Revive: target = fallenAllies.Count > 0 ? fallenAllies[0] : null; break;
                case SkillKind.Cleanse: target = Afflicted(livingAllies); break;
                default:
                    if (skill.Kind == SkillKind.Buff) target = PickTarget(livingAllies.FindAll(a => NeedsBuff(a, skill)), false, rng);
                    else if (skill.TargetType == TargetType.Ally) target = PickTarget(livingAllies, false, rng);
                    else target = PickTarget(livingOpponents, lowestHp, rng);
                    break;
            }
            if (target == null) return AttackAction(actor, livingOpponents, lowestHp, rng);
            return MakeSkill(actor, skill, target);
        }

        /// <summary>Retarget the selected payload, never reroll its skill. Used only when its frozen target is invalid.</summary>
        internal static string Retarget(BattleUnit actor, BattleAction action, List<BattleUnit> opponents, List<BattleUnit> allies, GodotRng rng)
        {
            var living = Living(allies);
            var skill = action.Skill;
            BattleUnit target = null;
            if (skill?.TargetType == TargetType.Self) target = actor;
            else if (skill?.Kind == SkillKind.Revive) { var fallen = Fallen(allies); if (fallen.Count > 0) target = fallen[0]; }
            else if (skill?.Kind == SkillKind.Heal) target = MostInjured(living, 0.999) ?? PickTarget(living, false, rng);
            else if (skill?.Kind == SkillKind.Cleanse) target = Afflicted(living) ?? PickTarget(living, false, rng);
            else if (skill?.Kind == SkillKind.Buff) target = PickTarget(living.FindAll(a => NeedsBuff(a, skill)), false, rng) ?? PickTarget(living, false, rng);
            else target = PickTarget(skill?.TargetType == TargetType.Ally ? living : Living(opponents), action.LowestHpTarget, rng);
            return target?.Id;
        }

        static BattleAction MakeSkill(BattleUnit actor, SkillDef skill, BattleUnit target)
            => BattleAction.Make(ActionKind.Skill, actor.Id, target != null ? new[] { target.Id } : null, skill.Id, skill);

        static BattleAction AttackAction(BattleUnit actor, List<BattleUnit> livingOpponents, bool lowestHp, GodotRng rng)
        {
            var target = PickTarget(livingOpponents, lowestHp, rng);
            var action = BattleAction.Make(ActionKind.Attack, actor.Id, new[] { target.Id });
            action.LowestHpTarget = lowestHp;
            return action;
        }

        static SkillDef WeightedSkill(List<Option> options, GodotRng rng)
        {
            double total = 0.0;
            foreach (var o in options) total += o.Weight;
            double roll = rng.Randf() * total;
            foreach (var o in options)
            {
                roll -= o.Weight;
                if (roll <= 0.0) return o.Skill;
            }
            return options[options.Count - 1].Skill;
        }
        internal static bool AnyLiving(List<BattleUnit> units)
        {
            foreach (var unit in units) if (unit.IsAlive) return true;
            return false;
        }

        internal static int CountLiving(List<BattleUnit> units)
        {
            int count = 0;
            foreach (var unit in units) if (unit.IsAlive) count++;
            return count;
        }


        internal static List<BattleUnit> Living(List<BattleUnit> units)
        {
            var r = new List<BattleUnit>();
            foreach (var u in units) if (u.IsAlive) r.Add(u);
            return r;
        }

        internal static List<BattleUnit> Fallen(List<BattleUnit> units)
        {
            var r = new List<BattleUnit>();
            foreach (var u in units) if (!u.IsAlive && !u.Summoned && !u.Escaped) r.Add(u);
            return r;
        }

        static BattleUnit MostInjured(List<BattleUnit> units, double belowRatio)
        {
            BattleUnit best = null;
            double bestRatio = belowRatio;
            foreach (var u in units)
            {
                double ratio = (double)u.Hp / u.MaxHp;
                if (ratio < bestRatio) { bestRatio = ratio; best = u; }
            }
            return best;
        }

        static BattleUnit Afflicted(List<BattleUnit> units)
        {
            foreach (var u in units)
                foreach (var s in u.Statuses)
                    if (!s.IsBeneficial) return u;
            return null;
        }

        static BattleUnit PickTarget(List<BattleUnit> units, bool lowestHp, GodotRng rng)
        {
            if (units.Count == 0) return null;
            if (lowestHp)
            {
                var lowest = units[0];
                foreach (var u in units)
                    if ((double)u.Hp / u.MaxHp < (double)lowest.Hp / lowest.MaxHp) lowest = u;
                return lowest;
            }
            return units[rng.RandiRange(0, units.Count - 1)];
        }
    }
}
