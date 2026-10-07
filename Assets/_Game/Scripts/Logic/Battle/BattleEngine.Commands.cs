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
        /// Deterministic AUTO: emergency healing, revive, disabling-ailment removal, efficient healing,
        /// then useful damage or a lasting setup skill. Queries never consume RNG or inventory items.
        /// </summary>
        public BattleCommand SuggestCommand(BattleUnit unit)
        {
            if (unit == null || !unit.IsAlive) return BattleCommand.Guard();
            var usable = new List<SkillDef>();
            foreach (var option in GetCommandOptions(unit).Skills) if (option.Usable) usable.Add(option.Skill);
            var allies = unit.Side == BattleSide.Party ? _party : _enemies;
            var living = EnemyAI.Living(allies);
            var foes = EnemyAI.Living(unit.Side == BattleSide.Party ? _enemies : _party);
            if (foes.Count == 0) return BattleCommand.Guard();

            var heal = SuggestHeal(unit, usable, living);
            // Keep a dying ally alive before spending a turn reviving someone else.
            if (LowestRatio(living) < 0.3 && heal != null) return heal;
            var fallen = EnemyAI.Fallen(allies);
            BattleCommand revive = null;
            double reviveScore = -1;
            foreach (var s in usable)
            {
                if (s.Kind != SkillKind.Revive) continue;
                var targets = ValidTargets(unit, BattleCommand.Skill(s.Id));
                BattleUnit revivalTarget = null;
                foreach (var target in targets)
                    if (revivalTarget == null || RevivalValue(target) > RevivalValue(revivalTarget)) revivalTarget = target;
                if (revivalTarget == null) continue;
                bool group = SkillRule(s) == TargetRule.AllAllies;
                double score = (group ? fallen.Count : 1) * Math.Max(0.1, s.Power) / (1 + s.MpCost * 0.025);
                if (score > reviveScore) { reviveScore = score; revive = BattleCommand.Skill(s.Id, group ? null : revivalTarget.Id); }
            }
            if (revive != null) return revive;

            // Remove stun/freeze/silence before an offensive ultimate; minor ailments alone can wait.
            BattleCommand cleanse = null;
            double cleanseScore = 0;
            foreach (var s in usable)
            {
                if (s.Kind != SkillKind.Cleanse) continue;
                var targets = ValidTargets(unit, BattleCommand.Skill(s.Id));
                BattleUnit worst = null;
                double total = 0, worstScore = 0;
                foreach (var a in targets)
                {
                    double score = 0;
                    foreach (var st in a.Statuses)
                    {
                        if (st.IsBeneficial) continue;
                        if (!st.CanAct) score += 5;
                        else if (st.BlocksMpSkills && a.SkillList.Exists(x => x.MpCost > 0)) score += 4;
                        else if (st.EffectType == StatusEffectType.Burn && (double)a.Hp / a.MaxHp < 0.65) score += 3;
                        else score += 1;
                    }
                    total += score;
                    if (score > worstScore) { worstScore = score; worst = a; }
                }
                double benefit = SkillRule(s) == TargetRule.AllAllies ? total : worstScore;
                double value = benefit / (1 + s.MpCost * 0.03);
                if (worst != null && benefit >= 3 && value > cleanseScore)
                { cleanseScore = value; cleanse = BattleCommand.Skill(s.Id, SkillRule(s) == TargetRule.SingleAlly ? worst.Id : null); }
            }
            if (cleanse != null) return cleanse;
            if (heal != null) return heal;

            int reserve = HealReserve(unit);
            double freeScore = AttackScore(unit, null, foes, out var bestTarget);
            double bestScore = freeScore;
            SkillDef best = null;
            // Later skills win close ultimate ties only when using TP actually improves this turn.
            foreach (var s in usable)
            {
                if (s.Kind != SkillKind.Damage) continue;
                if (s.MpCost > 0 && unit.Mp - s.MpCost < reserve) continue;
                double score = AttackScore(unit, s, foes, out var target);
                if (s.TpCost > 0 && score <= freeScore * 1.5) continue;
                if (s.MpCost > 0) score /= 1 + 0.025 * s.MpCost;
                bool tie = s.TpCost > 0 && best?.TpCost > 0 && score >= bestScore * 0.98;
                if (score > bestScore * 1.08 || tie) { bestScore = score; best = s; bestTarget = target; }
            }

            // Setup pays off only if the fight has enough HP remaining for several party actions.
            double foeHp = 0;
            foreach (var f in foes) foeHp += f.Hp;
            if (foeHp > Math.Max(1, freeScore) * Math.Max(1, living.Count) * 2.5)
            {
                foreach (var s in usable)
                {
                    if (s.Kind != SkillKind.Buff && s.Kind != SkillKind.Debuff) continue;
                    if (s.MpCost > 0 && unit.Mp - s.MpCost < reserve) continue;
                    var targets = ValidTargets(unit, BattleCommand.Skill(s.Id));
                    bool group = SkillRule(s) == TargetRule.AllAllies || SkillRule(s) == TargetRule.AllEnemies;
                    BattleUnit target = null;
                    double total = 0, oneBest = 0;
                    foreach (var t in targets)
                    {
                        double value = SetupValue(unit, t, s, freeScore);
                        total += value;
                        if (value > oneBest) { oneBest = value; target = t; }
                    }
                    double score = (group ? total : oneBest) / (1 + s.MpCost * 0.04);
                    if (target != null && score > bestScore * 1.2)
                        return BattleCommand.Skill(s.Id, SkillRule(s) == TargetRule.SingleAlly || SkillRule(s) == TargetRule.SingleEnemy ? target.Id : null);
                }
            }
            return best == null ? BattleCommand.Attack(bestTarget?.Id)
                : BattleCommand.Skill(best.Id, SkillRule(best) == TargetRule.SingleEnemy ? bestTarget?.Id : null);
        }

        static double RevivalValue(BattleUnit target)
        {
            double value = target.MaxHp + target.MaxMp;
            foreach (var s in target.SkillList) if (s.Kind == SkillKind.Heal || s.Kind == SkillKind.Revive) value += 500;
            return value;
        }

        BattleCommand SuggestHeal(BattleUnit unit, List<SkillDef> usable, List<BattleUnit> living)
        {
            int injured = 0;
            foreach (var ally in living) if ((double)ally.Hp / ally.MaxHp < 0.75) injured++;
            if (LowestRatio(living) >= 0.65 && injured < 2) return null;
            BattleCommand best = null;
            double bestScore = 0;
            foreach (var s in usable)
            {
                if (s.Kind != SkillKind.Heal) continue;
                bool group = SkillRule(s) == TargetRule.AllAllies;
                var targets = ValidTargets(unit, BattleCommand.Skill(s.Id));
                bool emergencyTarget = false;
                foreach (var t in targets) emergencyTarget |= (double)t.Hp / t.MaxHp < 0.3;
                BattleUnit chosen = null;
                double total = 0, single = 0;
                foreach (var target in targets)
                {
                    double amount = (s.ScalingStat == ScalingStat.Magic ? unit.EffectiveMagic : unit.EffectiveAttack) * s.Power * target.HealingReceivedScale;
                    double ratio = (double)target.Hp / target.MaxHp;
                    if (!group && emergencyTarget && ratio >= 0.3) continue;
                    double score = Math.Min(target.MaxHp - target.Hp, amount) * (ratio < 0.3 ? 2 : ratio < 0.65 ? 1.4 : 1);
                    total += score;
                    if (score > single) { single = score; chosen = target; }
                }
                double utility = (group ? total : single) / (1 + s.MpCost * 0.055);
                // Reserve TP for a meaningful rescue rather than a little missing HP.
                if (s.TpCost > 0) { if (LowestRatio(living) >= 0.5 && injured < 3) continue; utility *= 0.85; }
                if (chosen != null && utility > bestScore)
                { bestScore = utility; best = BattleCommand.Skill(s.Id, SkillRule(s) == TargetRule.SingleAlly ? chosen.Id : null); }
            }
            return best;
        }

        double SetupValue(BattleUnit actor, BattleUnit target, SkillDef skill, double attackScore)
        {
            double value = 0;
            var ids = new List<string>(skill.ExtraStatuses);
            if (!string.IsNullOrEmpty(skill.StatusEffect)) ids.Add(skill.StatusEffect);
            foreach (var id in ids)
            {
                if (!_db.Statuses.TryGetValue(id, out var def) || target.HasStatus(id)) continue;
                var status = BattleStatus.FromDef(def, actor.Id);
                if (target.IsImmuneTo(status)) continue;
                double ratio = (double)target.Hp / target.MaxHp;
                switch (def.EffectType)
                {
                    case StatusEffectType.AttackUp: value += target.EffectiveAttack * def.Magnitude * 3; break;
                    case StatusEffectType.MagicUp: value += target.SkillList.Exists(x => x.ScalingStat == ScalingStat.Magic && (x.Kind == SkillKind.Damage || x.Kind == SkillKind.Heal)) ? target.EffectiveMagic * def.Magnitude * 3 : 0; break;
                    case StatusEffectType.DefenseUp: case StatusEffectType.Barrier: if (ratio < 0.7) value += attackScore * 1.6; break;
                    case StatusEffectType.Regen: value += Math.Min(target.MaxHp - target.Hp, target.MaxHp * def.Magnitude * 2); break;
                    case StatusEffectType.DefenseDown: value += attackScore * def.Magnitude * 4; break;
                    case StatusEffectType.AttackDown: value += (target.EffectiveAttack + target.EffectiveMagic) * def.Magnitude * 2; break;
                    case StatusEffectType.Silence: if (target.SkillList.Exists(x => x.MpCost > 0)) value += attackScore * 1.6; break;
                    case StatusEffectType.Sleep: case StatusEffectType.Stun: case StatusEffectType.Freeze: if (target.CanAct) value += attackScore * 1.5; break;
                }
            }
            return value * (skill.Kind == SkillKind.Debuff ? Math.Max(0, Math.Min(1, skill.StatusChance)) : 1);
        }

        static double LowestRatio(List<BattleUnit> units)
        {
            double ratio = 1;
            foreach (var u in units) ratio = Math.Min(ratio, (double)u.Hp / u.MaxHp);
            return ratio;
        }

        static int HealReserve(BattleUnit unit)
        {
            int reserve = 0;
            foreach (var s in unit.SkillList)
                if (s.Kind == SkillKind.Heal && s.TpCost == 0 && s.MpCost > 0 && (reserve == 0 || s.MpCost < reserve)) reserve = s.MpCost;
            return reserve;
        }

        /// <summary>Useful damage plus finish/break/control value, with random-hit overkill capped per foe.</summary>
        double AttackScore(BattleUnit unit, SkillDef skill, List<BattleUnit> foes, out BattleUnit bestTarget)
        {
            var rule = skill == null ? TargetRule.SingleEnemy : SkillRule(skill);
            var choosable = new List<BattleUnit>(ValidTargets(unit, skill == null ? BattleCommand.Attack(null) : BattleCommand.Skill(skill.Id)));
            int hits = Math.Max(1, skill?.HitCount ?? 1);
            bestTarget = null;
            double best = -1, total = 0;
            foreach (var target in foes)
            {
                double allocatedHits = rule == TargetRule.RandomEnemies ? (double)hits / foes.Count : hits;
                double damage = ExpectedHit(unit, target, skill) * allocatedHits;
                double useful = Math.Min(damage, target.Hp);
                if (damage >= target.Hp) useful *= 1.3;
                int element = DamageFormula.ElementOf(unit, skill);
                if (target.Shield > 0 && !target.Broken && IsWeaknessKnown(target, element))
                {
                    useful += Math.Min(target.Shield, allocatedHits) * Math.Max(6, target.EffectiveAttack * 0.2);
                    if (allocatedHits >= target.Shield) useful += target.EffectiveAttack * 0.5;
                }
                if (skill != null && damage < target.Hp && !string.IsNullOrEmpty(skill.StatusEffect)
                    && _db.Statuses.TryGetValue(skill.StatusEffect, out var status) && !target.HasStatus(status.Id))
                {
                    var effect = BattleStatus.FromDef(status, unit.Id);
                    if (!target.IsImmuneTo(effect) && !effect.IsBeneficial)
                        useful += Math.Min(target.Hp - damage, !effect.CanAct ? target.EffectiveAttack * 0.5 : target.MaxHp * 0.025) * skill.StatusChance;
                }
                if (skill != null && skill.Drain > 0) useful += Math.Min(unit.MaxHp - unit.Hp, useful * skill.Drain);
                total += useful;
                if (rule == TargetRule.SingleEnemy && choosable.Contains(target) && useful > best)
                { best = useful; bestTarget = target; }
            }
            if (rule == TargetRule.AllEnemies || rule == TargetRule.RandomEnemies) return total;
            if (bestTarget == null && choosable.Count > 0) bestTarget = choosable[0];
            return Math.Max(0, best);
        }

        double ExpectedHit(BattleUnit unit, BattleUnit target, SkillDef skill)
        {
            if (target.HasStatus("invincible")) return 0;
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
            if (target.Guarding) dmg *= DamageFormula.GuardMultiplier;
            if (type == DamageType.Physical)
            {
                dmg *= target.PhysicalDamageTakenScale;
                dmg *= DamageFormula.HitChance(unit, target, type);
                dmg *= 1.0 + Gd.Clamp(unit.CritRate + (skill == null ? 0.0 : Gd.D(skill.CritBonus)), 0, 1) * (unit.CritMultiplier - 1.0);
            }
            return dmg;
        }
    }
}
