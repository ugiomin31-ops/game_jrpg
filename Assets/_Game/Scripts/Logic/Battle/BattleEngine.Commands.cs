// Command-menu queries (options, targets) and the AUTO battle policy. None of these touch the RNG
// or mutate battle state.
using System;
using System.Collections.Generic;

namespace Abyss.Logic.Battle
{
    public sealed partial class BattleEngine
    {
        /// <summary>Skill / item / flee availability for a hero's command menu.</summary>
        public CommandOptions GetCommandOptions(BattleUnit unit)
        {
            var skills = new List<SkillOption>();
            var items = new List<ItemOption>();
            var result = new CommandOptions { Actor = unit, Skills = skills, Items = items };
            if (unit == null) return result;
            bool silenced = unit.IsSilenced;
            foreach (var skill in unit.SkillList)
            {
                if (skill.Id == "basic_attack") continue;
                int mp = Math.Max(0, skill.MpCost), tp = Math.Max(0, skill.TpCost);
                string reason = null;
                if (mp > 0 && silenced) reason = "reason_silence";
                else if (unit.Mp < mp) reason = "reason_mp";
                else if (unit.Tp < tp) reason = "reason_tp";
                else if (ValidTargets(unit, BattleCommand.Skill(skill.Id)).Count == 0 && SkillRule(skill) != TargetRule.None) reason = "reason_no_target";
                var option = new SkillOption
                {
                    Skill = skill, Id = skill.Id, DisplayName = skill.DisplayName, MpCost = mp, TpCost = tp,
                    IsUltimate = tp > 0, Usable = reason == null, ReasonKey = reason, Target = SkillRule(skill), Effect = SkillEffect(skill),
                };
                skills.Add(option);
                if (option.IsUltimate && option.Usable) result.UltimateReady = true;
            }
            foreach (var kv in _inventory)
            {
                if (kv.Value <= 0 || !_db.Items.TryGetValue(kv.Key, out var item)) continue;
                var effect = ItemEffect(item);
                if (effect == ActionEffect.Unusable) continue;
                string reason = null;
                if (effect == ActionEffect.Flee) { if (!FleeAllowed(true)) reason = "flee_blocked"; }
                else if (ValidTargets(unit, BattleCommand.Item(item.Id)).Count == 0 && ItemRule(item) != TargetRule.None) reason = "reason_no_target";
                items.Add(new ItemOption
                {
                    Item = item, Id = item.Id, DisplayName = item.DisplayName, Count = kv.Value, Effect = effect,
                    Target = effect == ActionEffect.Flee ? TargetRule.None : ItemRule(item), Usable = reason == null, ReasonKey = reason,
                });
            }
            result.CanFlee = FleeAllowed();
            result.FleeReasonKey = result.CanFlee ? null : "flee_blocked";
            return result;
        }

        /// <summary>Target rule of a command (SingleEnemy for Attack, Self for Guard, None for Flee / smoke).</summary>
        public TargetRule GetTargetRule(BattleUnit unit, BattleCommand cmd)
        {
            if (cmd == null) return TargetRule.None;
            switch (cmd.Kind)
            {
                case CommandKind.Attack: return TargetRule.SingleEnemy;
                case CommandKind.Guard: return TargetRule.Self;
                case CommandKind.Flee: return TargetRule.None;
                case CommandKind.Skill:
                {
                    var skill = unit != null ? FindActorSkill(unit, cmd.SkillId) : null;
                    return skill != null ? SkillRule(skill) : TargetRule.None;
                }
                case CommandKind.Item:
                    if (cmd.ItemId == null || !_db.Items.TryGetValue(cmd.ItemId, out var item)) return TargetRule.None;
                    return ItemEffect(item) == ActionEffect.Flee ? TargetRule.None : ItemRule(item);
                default: return TargetRule.None;
            }
        }

        /// <summary>
        /// Units the command may target (single rules: the choosable units; ALL / RANDOM / SELF: the units it
        /// can affect). A provoke-forced single offensive target is returned alone.
        /// </summary>
        public IReadOnlyList<BattleUnit> ValidTargets(BattleUnit unit, BattleCommand cmd)
        {
            var result = new List<BattleUnit>();
            if (unit == null || cmd == null) return result;
            ActionEffect effect;
            switch (cmd.Kind)
            {
                case CommandKind.Attack: effect = ActionEffect.Damage; break;
                case CommandKind.Guard: result.Add(unit); return result;
                case CommandKind.Flee: return result;
                case CommandKind.Skill:
                {
                    var skill = FindActorSkill(unit, cmd.SkillId);
                    if (skill == null) return result;
                    effect = SkillEffect(skill);
                    break;
                }
                case CommandKind.Item:
                {
                    if (cmd.ItemId == null || !_db.Items.TryGetValue(cmd.ItemId, out var item)) return result;
                    effect = ItemEffect(item);
                    if (effect == ActionEffect.Unusable || effect == ActionEffect.Flee) return result;
                    break;
                }
                default: return result;
            }
            var rule = GetTargetRule(unit, cmd);
            var allies = unit.Side == BattleSide.Party ? _party : _enemies;
            var opponents = unit.Side == BattleSide.Party ? _enemies : _party;
            bool reviving = effect == ActionEffect.Revive;
            var allyPool = reviving ? EnemyAI.Fallen(allies) : EnemyAI.Living(allies);
            var opponentPool = EnemyAI.Living(opponents);
            switch (rule)
            {
                case TargetRule.Self: if (!reviving) result.Add(unit); break;
                case TargetRule.None: break;
                case TargetRule.AllAllies: case TargetRule.RandomAllies: case TargetRule.SingleAlly: result.AddRange(allyPool); break;
                case TargetRule.AllEnemies: case TargetRule.RandomEnemies: result.AddRange(opponentPool); break;
                case TargetRule.All: result.AddRange(EnemyAI.Living(allies)); result.AddRange(opponentPool); break;
                default:
                {
                    var forced = IsOffensive(effect) ? ProvokeTarget(unit, opponentPool) : null;
                    if (forced != null) result.Add(forced);
                    else result.AddRange(opponentPool);
                    break;
                }
            }
            return result;
        }

        // --- AUTO battle ------------------------------------------------------------------------------

        /// <summary>
        /// AUTO policy for a hero: revive a fallen ally, heal when allies are low, fire a ready ultimate, cleanse
        /// a disabling ailment, else the strongest affordable attack (known weaknesses / BREAK exploited,
        /// healers keep MP for one heal). Never uses items. Always returns a command that Submit accepts.
        /// </summary>
        public BattleCommand SuggestCommand(BattleUnit unit)
        {
            if (unit == null || !unit.IsAlive) return BattleCommand.Guard();
            var opts = GetCommandOptions(unit);
            var usable = new List<SkillDef>();
            foreach (var o in opts.Skills) if (o.Usable) usable.Add(o.Skill);
            var living = EnemyAI.Living(unit.Side == BattleSide.Party ? _party : _enemies);
            var foes = EnemyAI.Living(unit.Side == BattleSide.Party ? _enemies : _party);
            if (foes.Count == 0) return BattleCommand.Guard();

            // 1. Revive.
            var fallen = EnemyAI.Fallen(unit.Side == BattleSide.Party ? _party : _enemies);
            if (fallen.Count > 0)
                foreach (var s in usable)
                    if (SkillEffect(s) == ActionEffect.Revive && SkillRule(s) == TargetRule.SingleAlly)
                        return BattleCommand.Skill(s.Id, fallen[0].Id);

            // 2. Heal.
            var heal = SuggestHeal(unit, usable, living);
            if (heal != null) return heal;

            // 3. Ultimate (newest learned first: a later ultimate is the stronger one).
            for (int i = usable.Count - 1; i >= 0; i--)
            {
                var s = usable[i];
                if (s.TpCost <= 0) continue;
                var effect = SkillEffect(s);
                if (effect == ActionEffect.Heal)
                {
                    if (LowestRatio(living) < 0.75) return BattleCommand.Skill(s.Id, SingleTargetFor(unit, s, living, foes));
                    continue;
                }
                if (effect == ActionEffect.Damage) return BattleCommand.Skill(s.Id, SingleTargetFor(unit, s, living, foes));
            }

            // 4. Cleanse a disabled / silenced / poisoned ally.
            foreach (var s in usable)
            {
                if (SkillEffect(s) != ActionEffect.Cleanse) continue;
                BattleUnit worst = null;
                int worstCount = 0;
                foreach (var a in living)
                {
                    int n = 0;
                    foreach (var st in a.Statuses) if (!st.IsBeneficial) n++;
                    if (n > worstCount) { worst = a; worstCount = n; }
                }
                if (worst != null && (worstCount >= 2 || !worst.CanAct || worst.IsSilenced))
                    return BattleCommand.Skill(s.Id, SkillRule(s) == TargetRule.SingleAlly ? worst.Id : null);
            }

            // 5. Strongest attack.
            int reserve = HealReserve(unit);
            double bestScore = AttackScore(unit, null, foes, out var bestTarget);
            SkillDef best = null;
            foreach (var s in usable)
            {
                if (SkillEffect(s) != ActionEffect.Damage || s.TpCost > 0) continue;
                if (s.MpCost > 0 && unit.Mp - s.MpCost < reserve) continue;
                double score = AttackScore(unit, s, foes, out var target);
                // MP skills must clearly beat the free attack.
                if (s.MpCost > 0) score /= 1.0 + 0.02 * s.MpCost;
                if (score > bestScore * 1.1)
                {
                    bestScore = score;
                    best = s;
                    bestTarget = target;
                }
            }
            if (best == null) return BattleCommand.Attack(bestTarget?.Id);
            return BattleCommand.Skill(best.Id, SkillRule(best) == TargetRule.SingleEnemy ? bestTarget?.Id : null);
        }

        BattleCommand SuggestHeal(BattleUnit unit, List<SkillDef> usable, List<BattleUnit> living)
        {
            int below60 = 0;
            BattleUnit lowest = null;
            foreach (var a in living)
            {
                double r = (double)a.Hp / a.MaxHp;
                if (r < 0.6) below60++;
                if (lowest == null || r < (double)lowest.Hp / lowest.MaxHp) lowest = a;
            }
            if (lowest == null || (double)lowest.Hp / lowest.MaxHp >= 0.5) return null;
            SkillDef group = null, single = null, bigSingle = null;
            foreach (var s in usable)
            {
                if (SkillEffect(s) != ActionEffect.Heal || s.TpCost > 0) continue;
                var rule = SkillRule(s);
                if (rule == TargetRule.AllAllies) { if (group == null || s.Power > group.Power) group = s; }
                else if (rule == TargetRule.SingleAlly)
                {
                    if (single == null || s.MpCost < single.MpCost) single = s;
                    if (bigSingle == null || s.Power > bigSingle.Power) bigSingle = s;
                }
                else if (rule == TargetRule.Self && lowest == unit) return BattleCommand.Skill(s.Id);
            }
            if (group != null && below60 >= 2) return BattleCommand.Skill(group.Id);
            if (single != null)
            {
                int deficit = lowest.MaxHp - lowest.Hp;
                var pick = unit.EffectiveMagic * single.Power >= deficit * 0.8 ? single : bigSingle;
                return BattleCommand.Skill(pick.Id, lowest.Id);
            }
            return group != null ? BattleCommand.Skill(group.Id) : null;
        }

        static double LowestRatio(List<BattleUnit> units)
        {
            double r = 1.0;
            foreach (var u in units) r = Math.Min(r, (double)u.Hp / u.MaxHp);
            return r;
        }

        string SingleTargetFor(BattleUnit unit, SkillDef s, List<BattleUnit> living, List<BattleUnit> foes)
        {
            var rule = SkillRule(s);
            if (rule == TargetRule.SingleEnemy)
            {
                AttackScore(unit, s, foes, out var t);
                return t?.Id;
            }
            if (rule == TargetRule.SingleAlly)
            {
                BattleUnit lowest = null;
                foreach (var a in living) if (lowest == null || (double)a.Hp / a.MaxHp < (double)lowest.Hp / lowest.MaxHp) lowest = a;
                return lowest?.Id;
            }
            return null;
        }

        /// <summary>MP a healer keeps for one cheapest single heal.</summary>
        static int HealReserve(BattleUnit unit)
        {
            int reserve = 0;
            foreach (var s in unit.SkillList)
                if (s.Kind == SkillKind.Heal && s.TpCost == 0 && s.MpCost > 0 && (reserve == 0 || s.MpCost < reserve)) reserve = s.MpCost;
            return reserve;
        }

        /// <summary>Expected useful damage of a plain attack (skill null) or skill; outputs the best single target.</summary>
        double AttackScore(BattleUnit unit, SkillDef skill, List<BattleUnit> foes, out BattleUnit bestTarget)
        {
            var rule = skill == null ? TargetRule.SingleEnemy : SkillRule(skill);
            var choosable = new List<BattleUnit>(ValidTargets(unit, skill == null ? BattleCommand.Attack(null) : BattleCommand.Skill(skill.Id)));
            int hits = Math.Max(1, skill?.HitCount ?? 1);
            bestTarget = null;
            double best = -1, total = 0;
            foreach (var t in foes)
            {
                double one = ExpectedHit(unit, t, skill);
                double perTarget = rule == TargetRule.RandomEnemies ? one : one * hits;
                double useful = Math.Min(perTarget, t.Hp);
                // Finishing a unit and breaking shields are worth extra.
                if (perTarget >= t.Hp) useful *= 1.25;
                int element = DamageFormula.ElementOf(unit, skill);
                if (t.MaxShield > 0 && !t.Broken && IsWeaknessKnown(t, element)) useful *= 1.15;
                total += useful;
                if (rule == TargetRule.SingleEnemy && choosable.Contains(t) && useful > best)
                {
                    best = useful;
                    bestTarget = t;
                }
            }
            switch (rule)
            {
                case TargetRule.AllEnemies: return total;
                case TargetRule.RandomEnemies: return foes.Count > 0 ? total / foes.Count * hits : 0;
                default:
                    if (bestTarget == null && choosable.Count > 0) bestTarget = choosable[0];
                    return Math.Max(0, best);
            }
        }

        double ExpectedHit(BattleUnit unit, BattleUnit target, SkillDef skill)
        {
            var type = DamageFormula.DamageTypeOf(skill);
            double power = skill == null ? 1.0 : Gd.D(skill.Power);
            double off = type == DamageType.Magical ? unit.EffectiveMagic : unit.EffectiveAttack;
            double def = type == DamageType.Magical ? target.EffectiveResistance : target.EffectiveDefense;
            def *= 1.0 - (skill == null ? 0.0 : Gd.D(skill.DefenseIgnore));
            double dmg = Math.Max(1.0, off * power - def * DamageFormula.DefenseFactor);
            int element = DamageFormula.ElementOf(unit, skill);
            if (element > 0 && IsWeaknessKnown(target, element)) dmg *= DamageFormula.WeaknessMultiplier;
            else if (element > 0 && _resistSeen.Contains(WeaknessKey(target.DefId, element))) dmg *= DamageFormula.ResistMultiplier;
            if (target.Broken) dmg *= DamageFormula.BrokenMultiplier;
            if (skill != null && !string.IsNullOrEmpty(skill.BonusVsStatus) && target.HasStatus(skill.BonusVsStatus)) dmg *= Gd.D(skill.BonusVsStatusMult);
            if (type == DamageType.Physical)
            {
                dmg *= DamageFormula.HitChance(unit, target, type);
                dmg *= 1.0 + Gd.Clamp(unit.CritRate + (skill == null ? 0.0 : Gd.D(skill.CritBonus)), 0, 1) * (unit.CritMultiplier - 1.0);
            }
            return dmg;
        }
    }
}
