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

        // --- Knowledge-safe previews ---------------------------------------------------------------------

        /// <summary>
        /// What the player knows about how <paramref name="target"/> takes <paramref name="element"/>: weakness in
        /// the bestiary or found this battle, resist / neutral observed this battle, else Unknown. Non-elemental
        /// hits are Neutral; heroes' own affinities are known. Never reads the hidden enemy tables.
        /// </summary>
        public PreviewAffinity KnownAffinity(BattleUnit target, int element)
        {
            if (target == null || element <= 0) return PreviewAffinity.Neutral;
            if (target.Side == BattleSide.Party)
                return target.IsWeakTo(element) ? PreviewAffinity.Weak : target.Resists(element) ? PreviewAffinity.Resist : PreviewAffinity.Neutral;
            string key = WeaknessKey(target.DefId, element);
            if (_known.Contains(key) || _discovered.Contains(key)) return PreviewAffinity.Weak;
            if (_resistSeen.Contains(key)) return PreviewAffinity.Resist;
            if (_neutralSeen.Contains(key)) return PreviewAffinity.Neutral;
            return PreviewAffinity.Unknown;
        }

        /// <summary>
        /// RNG-free, state-free estimate of <paramref name="cmd"/> by the party unit at <paramref name="actorUnitIndex"/>
        /// (engine unit indices). Single-target rules use <paramref name="targetUnitIndex"/>, which must be a valid
        /// target; other rules ignore it and cover every unit they can affect. Attack / damage skill / damage item ->
        /// Damage, healing skill / item -> Heal, anything else (or an invalid index / dead actor / unknown id) -> None.
        /// </summary>
        public ActionPreview PreviewAction(int actorUnitIndex, BattleCommand cmd, int targetUnitIndex)
        {
            if (cmd == null || actorUnitIndex < 0 || actorUnitIndex >= _units.Count) return ActionPreview.None;
            var actor = _units[actorUnitIndex];
            if (actor == null || actor.Side != BattleSide.Party || !actor.IsAlive) return ActionPreview.None;
            SkillDef skill = null;
            ItemDef item = null;
            PreviewKind kind;
            switch (cmd.Kind)
            {
                case CommandKind.Attack:
                    kind = PreviewKind.Damage;
                    break;
                case CommandKind.Skill:
                {
                    skill = FindActorSkill(actor, cmd.SkillId);
                    if (skill == null) return ActionPreview.None;
                    var effect = SkillEffect(skill);
                    kind = effect == ActionEffect.Damage ? PreviewKind.Damage : effect == ActionEffect.Heal ? PreviewKind.Heal : PreviewKind.None;
                    break;
                }
                case CommandKind.Item:
                {
                    if (cmd.ItemId == null || !_db.Items.TryGetValue(cmd.ItemId, out item)) return ActionPreview.None;
                    var effect = ItemEffect(item);
                    kind = effect == ActionEffect.DamageFixed ? PreviewKind.Damage : effect == ActionEffect.Heal ? PreviewKind.Heal : PreviewKind.None;
                    break;
                }
                default:
                    return ActionPreview.None;
            }
            if (kind == PreviewKind.None) return ActionPreview.None;

            var rule = GetTargetRule(actor, cmd);
            var pool = ValidTargets(actor, cmd);
            var targets = new List<BattleUnit>();
            switch (rule)
            {
                case TargetRule.None:
                    return ActionPreview.None;
                case TargetRule.SingleEnemy:
                case TargetRule.SingleAlly:
                {
                    if (targetUnitIndex < 0 || targetUnitIndex >= _units.Count) return ActionPreview.None;
                    var chosen = _units[targetUnitIndex];
                    bool valid = false;
                    foreach (var u in pool) valid |= ReferenceEquals(u, chosen);
                    if (!valid) return ActionPreview.None;
                    targets.Add(chosen);
                    break;
                }
                default:
                    targets.AddRange(pool);
                    break;
            }
            if (targets.Count == 0) return ActionPreview.None;

            bool random = rule == TargetRule.RandomEnemies || rule == TargetRule.RandomAllies;
            int hits = item != null ? 1 : Math.Max(1, skill?.HitCount ?? 1);
            int element = item != null ? (int)item.Element : DamageFormula.ElementOf(actor, skill);
            var rows = new List<TargetPreview>(targets.Count);
            foreach (var target in targets)
                rows.Add(kind == PreviewKind.Heal ? HealPreview(actor, target, skill, item)
                    : DamagePreview(actor, target, skill, item, element, hits, random));
            if (kind == PreviewKind.Heal) { element = 0; hits = random ? hits : 1; }
            return new ActionPreview(kind, random, hits, element, rows);
        }

        /// <summary>
        /// Sum of per-hit non-crit damage at the lowest / highest variance roll (known weakness hits include the current
        /// chain bonus). Only a KNOWN weakness lowers the shield; the hit that empties it switches the remaining hits to the BREAK multiplier. Random scope returns
        /// one hit instead (its max uses BREAK when enough known-weak picks could empty the shield first).
        /// </summary>
        TargetPreview DamagePreview(BattleUnit actor, BattleUnit target, SkillDef skill, ItemDef item, int element, int hits, bool random)
        {
            var affinity = KnownAffinity(target, element);
            double multiplier = affinity == PreviewAffinity.Weak ? DamageFormula.WeaknessMultiplier
                : affinity == PreviewAffinity.Resist ? DamageFormula.ResistMultiplier : 1.0;
            bool knownWeak = affinity == PreviewAffinity.Weak;
            // The chain bonus rides on KNOWN weakness hits only (the action would start at the current chain).
            if (knownWeak && target.Side == BattleSide.Enemy && _chain > 0) multiplier *= ChainFactor(_chain);
            bool broken = target.Broken;
            int shield = broken ? 0 : target.Shield;
            int shieldDamage = 0;
            bool breaks = false;
            var type = DamageFormula.DamageTypeOf(skill);
            double baseAmount = item != null ? 0.0 : DamageFormula.BaseAmount(actor, target, skill);
            double low = DamageFormula.LowestRoll(DamageFormula.DamageVariance), high = DamageFormula.HighestRoll(DamageFormula.DamageVariance);
            if (random)
            {
                bool mayBreak = knownWeak && !broken && target.MaxShield > 0 && hits > shield;
                int lo = HitAmount(actor, target, skill, item, type, baseAmount, low, multiplier, broken);
                int hi = HitAmount(actor, target, skill, item, type, baseAmount, high, multiplier, broken || mayBreak);
                return new TargetPreview(_units.IndexOf(target), target.Id, lo, hi, affinity, 0, false, false, target.HasDamageShield);
            }
            long min = 0, max = 0;
            for (int h = 0; h < hits; h++)
            {
                min += HitAmount(actor, target, skill, item, type, baseAmount, low, multiplier, broken);
                max += HitAmount(actor, target, skill, item, type, baseAmount, high, multiplier, broken);
                if (knownWeak && !broken && target.MaxShield > 0)
                {
                    if (shield > 0) shieldDamage++;
                    shield = Math.Max(0, shield - 1);
                    if (shield == 0) { broken = true; breaks = true; }
                }
            }
            int minClamped = (int)Math.Min(int.MaxValue, min), maxClamped = (int)Math.Min(int.MaxValue, max);
            return new TargetPreview(_units.IndexOf(target), target.Id, minClamped, maxClamped, affinity, shieldDamage, breaks, minClamped >= target.Hp, target.HasDamageShield);
        }

        /// <summary>One non-crit hit at a given variance roll (items: their fixed amount).</summary>
        static int HitAmount(BattleUnit actor, BattleUnit target, SkillDef skill, ItemDef item, DamageType type, double baseAmount, double roll, double multiplier, bool broken)
            => item != null ? DamageFormula.FixedItemAmount(item, multiplier, broken)
                : DamageFormula.FinalAmount(DamageFormula.ApplyTargetMultipliers(baseAmount * roll, target, skill, type, multiplier, broken));

        /// <summary>HP restored at the lowest / highest heal variance (healing-received scale applied, before the missing-HP cap).</summary>
        TargetPreview HealPreview(BattleUnit actor, BattleUnit target, SkillDef skill, ItemDef item)
        {
            int min, max;
            if (item != null) min = max = Math.Max(0, item.HealAmount);
            else
            {
                double amount = DamageFormula.HealingBase(actor, skill);
                min = Math.Max(1, Gd.RoundI(amount * DamageFormula.LowestRoll(DamageFormula.HealVariance)));
                max = Math.Max(1, Gd.RoundI(amount * DamageFormula.HighestRoll(DamageFormula.HealVariance)));
            }
            min = Gd.RoundI(min * target.HealingReceivedScale);
            max = Gd.RoundI(max * target.HealingReceivedScale);
            return new TargetPreview(_units.IndexOf(target), target.Id, min, max, PreviewAffinity.Neutral, 0, false, false, false);
        }

        /// <summary>
        /// Weak when a living enemy the skill can target has a KNOWN weakness to its element, else Resist when one
        /// is known to resist it, else None. Damage skills only; knowledge only.
        /// </summary>
        public SkillAffinityTag KnownSkillAffinity(BattleUnit actor, SkillDef skill)
        {
            if (actor == null || skill == null || SkillEffect(skill) != ActionEffect.Damage) return SkillAffinityTag.None;
            int element = DamageFormula.ElementOf(actor, skill);
            if (element <= 0) return SkillAffinityTag.None;
            bool resist = false;
            foreach (var target in ValidTargets(actor, BattleCommand.Skill(skill.Id)))
            {
                if (target.Side != BattleSide.Enemy || !target.IsAlive) continue;
                var affinity = KnownAffinity(target, element);
                if (affinity == PreviewAffinity.Weak) return SkillAffinityTag.Weak;
                resist |= affinity == PreviewAffinity.Resist;
            }
            return resist ? SkillAffinityTag.Resist : SkillAffinityTag.None;
        }

        /// <summary>
        /// Skill menu for the command window: <see cref="GetCommandOptions"/> skills tagged with
        /// <see cref="KnownSkillAffinity"/>, stable-partitioned so damage skills with a known-weak target come first
        /// (learn order kept within each group; costs and unavailable reasons unchanged). AUTO keeps the plain order.
        /// </summary>
        public List<SkillOption> SkillMenu(BattleUnit unit)
        {
            var first = new List<SkillOption>();
            var rest = new List<SkillOption>();
            foreach (var option in GetCommandOptions(unit).Skills)
            {
                option.KnownAffinity = KnownSkillAffinity(unit, option.Skill);
                (option.KnownAffinity == SkillAffinityTag.Weak ? first : rest).Add(option);
            }
            first.AddRange(rest);
            return first;
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

            if (unit.Side == BattleSide.Party)
            {
                var interrupt = SuggestChargeBreak(unit);
                if (interrupt != null) return interrupt;
                if (ShouldGuardThreat(unit)) return BattleCommand.Guard();
                var preheal = SuggestThreatHeal(unit, usable, living);
                if (preheal != null) return preheal;
            }

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

        // O5: no RNG, unknown affinities remain neutral, no speculative RANDOM targeting.
        BattleCommand SuggestChargeBreak(BattleUnit actor)
        {
            foreach (var enemy in _enemies) // registration order is the engine unit-index tie break
            {
                if (!enemy.IsAlive || enemy.Broken || enemy.PendingCharge == null || enemy.Shield <= 0) continue;
                var command = BestWeakAction(actor, enemy, out int ownHits);
                if (command == null || !BeforeChargeRelease(actor, enemy)) continue;
                long available = ownHits;
                for (int i = _turnIndex; i < _queue.Count; i++)
                {
                    var ally = _queue[i];
                    if (ally == actor || ally.Side != BattleSide.Party || !ally.CanAct || ally.Broken || !BeforeChargeRelease(ally, enemy)) continue;
                    BestWeakAction(ally, enemy, out int hits);
                    available += Math.Min(enemy.Shield, hits);
                }
                if (available >= enemy.Shield) return command;
            }
            return null;
        }

        bool BeforeChargeRelease(BattleUnit actor, BattleUnit enemy)
        {
            int partyTurn = _queue.IndexOf(actor);
            if (partyTurn < _turnIndex) return false;
            // A charge announced this round cannot release in it. A due release executes on the charger's next actual
            // action: later this round only when it still has a turn it can use, otherwise next round.
            int enemyTurn = _queue.IndexOf(enemy);
            bool releasesThisRound = enemy.PendingCharge.AnnouncedRound < Round && enemyTurn >= _turnIndex && enemy.CanAct;
            return !releasesThisRound || partyTurn < enemyTurn;
        }

        BattleCommand BestWeakAction(BattleUnit actor, BattleUnit enemy, out int bestHits)
        {
            bestHits = 0;
            BattleCommand best = null;
            if (KnownAffinity(enemy, actor.AttackElement) == PreviewAffinity.Weak
                && ContainsTarget(ValidTargets(actor, BattleCommand.Attack(enemy.Id)), enemy))
            { best = BattleCommand.Attack(enemy.Id); bestHits = 1; }
            foreach (var option in GetCommandOptions(actor).Skills)
            {
                var skill = option.Skill;
                if (!option.Usable || skill.Kind != SkillKind.Damage || KnownAffinity(enemy, DamageFormula.ElementOf(actor, skill)) != PreviewAffinity.Weak) continue;
                var targets = ValidTargets(actor, BattleCommand.Skill(skill.Id));
                if (!ContainsTarget(targets, enemy)) continue;
                var rule = SkillRule(skill);
                if (rule == TargetRule.RandomEnemies && targets.Count != 1) continue;
                int hits = Math.Max(1, skill.HitCount);
                if (hits <= bestHits) continue; // stable learn-order ties, attack first
                bestHits = hits;
                best = BattleCommand.Skill(skill.Id, rule == TargetRule.SingleEnemy ? enemy.Id : null);
            }
            return best;
        }

        static bool ContainsTarget(IReadOnlyList<BattleUnit> targets, BattleUnit target)
        {
            foreach (var unit in targets) if (unit == target) return true;
            return false;
        }

        // Relevant threats before a hero's next actual turn. Current round uses the fixed queue;
        // next round uses deterministic effective speed (CompareTurns), never a variance roll.
        IEnumerable<(BattleUnit Enemy, BattleAction Action, bool NextRound)> ThreatsTo(BattleUnit hero, bool afterDecision = false)
        {
            int heroTurn = _queue.IndexOf(hero);
            foreach (var enemy in _enemies)
            {
                if (!enemy.IsAlive || enemy.Broken) continue;
                bool pendingShown = false;
                if (enemy.CanAct && _planned.TryGetValue(enemy.Id, out var slots))
                    foreach (var action in slots)
                    {
                        if (action == null || action.IsChargeAnnounce || action.Kind != ActionKind.Attack && action.Kind != ActionKind.Skill) continue;
                        if (action.Kind == ActionKind.Skill && SkillEffect(action.Skill) != ActionEffect.Damage) continue;
                        int enemyTurn = _queue.IndexOf(enemy);
                        bool inWindow = enemyTurn >= _turnIndex && (heroTurn <= _turnIndex || afterDecision || enemyTurn < heroTurn);
                        if (!inWindow) continue;
                        if (action.IsChargeRelease) pendingShown = true;
                        if (ThreatTargets(action, hero)) yield return (enemy, action, false);
                    }
                if (enemy.PendingCharge == null || pendingShown || heroTurn > _turnIndex && !afterDecision || CompareTurns(enemy, hero) >= 0) continue;
                // An upcoming skipped turn ticks CC; an already-ended turn has ticked it already.
                int enemyTurnsBeforeNextRound = _queue.IndexOf(enemy) >= _turnIndex ? 1 : 0;
                if (!CanActAfterTurns(enemy, enemyTurnsBeforeNextRound)) continue;
                var pending = enemy.PendingCharge;
                var release = BattleAction.Make(ActionKind.Skill, enemy.Id,
                    pending.TargetUnitId != null ? new[] { pending.TargetUnitId } : null, pending.SkillId, enemy.PendingChargeSkill);
                release.Scope = (int)pending.Scope; release.PowerScale = 1.5; release.IsChargeRelease = true;
                if (ThreatTargets(release, hero)) yield return (enemy, release, true);
            }
        }

        static bool CanActAfterTurns(BattleUnit enemy, int turns)
        {
            foreach (var status in enemy.Statuses)
                if (!status.CanAct && status.TurnsRemaining > turns) return false;
            return enemy.IsAlive;
        }

        bool HolderTurnBeforeThreat(BattleUnit hero, BattleUnit enemy, bool nextRound)
        {
            int holder = _queue.IndexOf(hero);
            // Current decision finishes before a later hit; skipped future turns also tick/drop defenses.
            return holder == _turnIndex || holder > _turnIndex && (nextRound || _queue.IndexOf(enemy) > holder);
        }

        static bool ThreatTargets(BattleAction action, BattleUnit hero)
            => action.Scope != 2 && (action.Scope == 1 && (action.Skill == null || action.Skill.TargetType == TargetType.Enemy)
                || action.Scope == 0 && action.TargetIds.Count > 0 && action.TargetIds[0] == hero.Id);

        int ThreatMaximum(BattleUnit enemy, BattleAction action, BattleUnit hero, bool activeDefense = false, bool guardRemains = true, bool holderActsFirst = false)
        {
            int hits = Math.Max(1, action.Skill?.HitCount ?? 1);
            double amount = DamageFormula.BaseAmount(enemy, hero, action.Skill, action.PowerScale, holderActsFirst ? 1 : 0)
                * DamageFormula.HighestRoll(DamageFormula.DamageVariance);
            double multiplier = DamageFormula.ElementMultiplier(hero, DamageFormula.ElementOf(enemy, action.Skill));
            // Guard-policy maximum is unguarded; active defenses use carried Guard only while it survives.
            int hit = DamageFormula.FinalAmount(DamageFormula.ApplyTargetMultipliers(amount, hero, action.Skill,
                DamageFormula.DamageTypeOf(action.Skill), multiplier, hero.Broken, holderActsFirst ? 1 : 0,
                activeDefense && guardRemains && hero.Guarding));
            if (!activeDefense) return (int)Math.Min(int.MaxValue, (long)hit * hits);
            // Pure local absorption model: never ReceiveDamage/Prepare a live unit. Simulate each hit's barrier/MP budget.
            var barrierLeft = new List<int>();
            var fullHit = new List<bool>();
            double manaRatio = 0;
            foreach (var status in hero.Statuses)
            {
                if (status.TurnsRemaining <= (holderActsFirst ? 1 : 0)) continue;
                if (status.Invincible) return 0;
                if (status.EffectType == StatusEffectType.Barrier) { barrierLeft.Add(status.BarrierRemaining); fullHit.Add(status.BarrierFullHit); }
                if (manaRatio <= 0 && status.ManaShieldRatio > 0) manaRatio = status.ManaShieldRatio;
            }
            int mp = hero.Mp;
            long total = 0;
            for (int h = 0; h < hits; h++)
            {
                int left = hit;
                for (int i = 0; i < barrierLeft.Count && left > 0; i++)
                {
                    if (fullHit[i]) { left = 0; fullHit[i] = false; barrierLeft[i] = 0; }
                    else { int used = Math.Min(barrierLeft[i], left); left -= used; barrierLeft[i] -= used; }
                }
                int toMp = Math.Min(mp, Gd.RoundI(left * manaRatio));
                mp -= toMp; left -= toMp; total += left;
            }
            return (int)Math.Min(int.MaxValue, total);
        }

        bool ShouldGuardThreat(BattleUnit hero, bool futureDecision = false)
        {
            foreach (var threat in ThreatsTo(hero, futureDecision))
            {
                bool holderActsFirst = HolderTurnBeforeThreat(hero, threat.Enemy, threat.NextRound);
                int max = ThreatMaximum(threat.Enemy, threat.Action, hero, holderActsFirst: holderActsFirst);
                if (max >= hero.Hp && max / 2.0 < hero.Hp) return true;
            }
            return false;
        }

        BattleCommand SuggestThreatHeal(BattleUnit actor, List<SkillDef> usable, List<BattleUnit> living)
        {
            var candidates = new List<BattleUnit>(living);
            candidates.Sort((a, b) =>
            {
                int ratio = ((double)a.Hp / a.MaxHp).CompareTo((double)b.Hp / b.MaxHp);
                return ratio != 0 ? ratio : UnitIndexOf(a).CompareTo(UnitIndexOf(b));
            });
            foreach (var ally in candidates)
            {
                bool lethal = false;
                int allyTurn = _queue.IndexOf(ally);
                bool canDecide = allyTurn > _turnIndex && ally.CanAct && !ally.Broken;
                foreach (var threat in ThreatsTo(ally, afterDecision: true))
                {
                    bool holderActsFirst = HolderTurnBeforeThreat(ally, threat.Enemy, threat.NextRound);
                    // TurnStart drops carried guard even on a skipped turn; ability to decide is separate.
                    bool guardRemains = !holderActsFirst;
                    if (ThreatMaximum(threat.Enemy, threat.Action, ally, activeDefense: true, guardRemains: guardRemains, holderActsFirst: holderActsFirst) < ally.Hp) continue;
                    // A future ally can guard only threats after its upcoming decision. Lethal strikes before it cannot wait.
                    if (holderActsFirst && canDecide)
                    {
                        int max = ThreatMaximum(threat.Enemy, threat.Action, ally, holderActsFirst: holderActsFirst);
                        if (max / 2.0 < ally.Hp) continue;
                    }
                    lethal = true; break;
                }
                if (!lethal) continue;
                foreach (var skill in usable)
                {
                    if (skill.Kind != SkillKind.Heal || !ContainsTarget(ValidTargets(actor, BattleCommand.Skill(skill.Id)), ally)) continue;
                    var rule = SkillRule(skill);
                    if (rule == TargetRule.RandomAllies && ValidTargets(actor, BattleCommand.Skill(skill.Id)).Count != 1) continue;
                    return BattleCommand.Skill(skill.Id, rule == TargetRule.SingleAlly ? ally.Id : null);
                }
            }
            return null;
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
                    case StatusEffectType.Sleep: case StatusEffectType.Stun: case StatusEffectType.Freeze: if (target.CanAct) value += attackScore * 1.5 * BossCcScaleFor(target); break;
                }
            }
            return value * (skill.Kind == SkillKind.Debuff ? Math.Max(0, Math.Min(1, skill.StatusChance)) : 1);
        }

        /// <summary>AUTO's view of a CC chance on this target: bosses scale it by the CC already landed this phase.</summary>
        static double BossCcScaleFor(BattleUnit target)
            => target.Side == BattleSide.Enemy && target.IsBoss ? BossCcChanceScale(target.PhaseCcSuccesses) : 1.0;

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
                        useful += Math.Min(target.Hp - damage, !effect.CanAct ? target.EffectiveAttack * 0.5 * BossCcScaleFor(target) : target.MaxHp * 0.025) * skill.StatusChance;
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
            if (element > 0 && IsWeaknessKnown(target, element))
                dmg *= DamageFormula.WeaknessMultiplier * (unit.Side == BattleSide.Party && target.Side == BattleSide.Enemy ? ChainFactor(_chain) : 1.0);
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
