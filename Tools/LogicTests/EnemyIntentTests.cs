// O3-O5: planned enemy intents, boss charge announce/release/cancel, and intent-aware AUTO.
using System;
using System.Collections.Generic;
using System.Linq;
using System.Reflection;
using Abyss.Logic;
using Abyss.Logic.Battle;

namespace Abyss.LogicTests
{
    public static class EnemyIntentTests
    {
        const int Slash = (int)Element.Slash;

        // --- fixtures ------------------------------------------------------------------------------------

        static HeroCombatSpec Hero(string id, int speed, params string[] skills) => new HeroCombatSpec
        {
            HeroId = id, DisplayName = id, Level = 10, MaxHp = 1000, Hp = 1000, MaxMp = 500, Mp = 500,
            Attack = 200, Magic = 150, Defense = 5, Resistance = 5, Speed = speed, Hit = 2, Crit = 0,
            Skills = skills.Length > 0 ? skills.ToList() : new List<string> { "slash1", "slash3", "heal" },
        };

        static SkillDef Skill(string id, SkillKind kind, Element element, Scope scope = Scope.Single, int hits = 1,
            TargetType target = TargetType.Enemy, int mp = 0, float power = 1f, ScalingStat scaling = ScalingStat.Attack) => new SkillDef
        {
            Id = id, DisplayName = id, Kind = kind, Element = element, Scope = scope, HitCount = hits, ScalingStat = scaling,
            TargetType = target, Power = power, MpCost = mp,
        };

        static EnemyDef Enemy(string id, int hp = 100000, int speed = 1, int attack = 5, int magic = 5, bool boss = false,
            int shield = 0, int actions = 1, string ai = "basic", string charge = "", string[] skills = null, int[] weights = null, params int[] weak)
        {
            var def = new EnemyDef
            {
                Id = id, DisplayName = id, MaxHp = hp, MaxMp = 100, Attack = attack, Magic = magic, Defense = 20, Resistance = 10,
                Speed = speed, Hit = 1, Evade = 0, BreakShield = shield, IsBoss = boss, Rank = boss ? 2 : 0, ActionsPerTurn = actions,
                AiProfile = ai, ChargeSkill = charge,
            };
            def.Weaknesses.AddRange(weak);
            if (skills != null) def.Skills.AddRange(skills);
            if (weights != null) def.SkillWeights.AddRange(weights);
            return def;
        }

        static GameDB Db()
        {
            var db = new GameDB();
            foreach (var s in new[]
            {
                Skill("slash1", SkillKind.Damage, Element.Slash),
                Skill("slash3", SkillKind.Damage, Element.Slash, hits: 3),
                Skill("rand3", SkillKind.Damage, Element.Slash, Scope.Random, hits: 3),
                Skill("heal", SkillKind.Heal, Element.None, target: TargetType.Ally, power: 2f, scaling: ScalingStat.Magic),
                Skill("big", SkillKind.Damage, Element.Fire, mp: 10, power: 2f, scaling: ScalingStat.Magic),
                Skill("small", SkillKind.Damage, Element.None),
                Skill("old_hit", SkillKind.Damage, Element.None),
                Skill("phase_hit", SkillKind.Damage, Element.None),
                Skill("zap", SkillKind.Damage, Element.None, mp: 5),
            }) db.Skills.Add(s.Id, s);
            string[] chargeSkills = { "big", "small" };
            int[] chargeWeights = { 1, 0 }; // "big" is the only option until charge exclusion turns the slot into an attack
            foreach (var e in new[]
            {
                Enemy("grunt", skills: new[] { "small" }, weights: new[] { 1 }),
                Enemy("striker", skills: new[] { "small" }, weights: new[] { 1 }),
                Enemy("caster", skills: new[] { "zap", "small" }, weights: new[] { 1, 0 }),
                Enemy("runner", ai: "runner", skills: new[] { "small" }, weights: new[] { 1 }),
                Enemy("brute", attack: 1000, speed: 1),
                Enemy("charger", boss: true, magic: 300, shield: 2, actions: 2, charge: "big", skills: chargeSkills, weights: chargeWeights, weak: Slash),
                Enemy("charger_fast", boss: true, magic: 300, speed: 2000, actions: 1, charge: "big", skills: chargeSkills, weights: chargeWeights),
                Enemy("fragile", hp: 400, boss: true, magic: 300, actions: 1, charge: "big", skills: chargeSkills, weights: chargeWeights),
                Enemy("phaser", hp: 300, boss: true, skills: new[] { "old_hit" }, weights: new[] { 1 }),
                Enemy("phaser2", hp: 300, boss: true, actions: 2, skills: new[] { "old_hit" }, weights: new[] { 1 }),
                Enemy("phase_charger", boss: true, magic: 300, actions: 1, charge: "big", skills: chargeSkills, weights: chargeWeights),
                Enemy("plain_boss", boss: true, skills: new[] { "big" }, weights: new[] { 1 }),
            }) db.Enemies.Add(e.Id, e);
            db.Enemies["phaser"].Phases.Add(new BossPhase { HpBelow = 0.5f, ActionsPerTurn = 2, Skills = new List<string> { "phase_hit" }, Weights = new List<int> { 1 }, Summon = new List<string> { "grunt" } });
            db.Enemies["phaser2"].Phases.Add(new BossPhase { HpBelow = 0.5f, ActionsPerTurn = 1 });
            db.Enemies["phase_charger"].Phases.Add(new BossPhase { HpBelow = 0.999f, ActionsPerTurn = 1, Skills = new List<string> { "small" }, Weights = new List<int> { 1 } });
            foreach (var st in TestMain.DB.Statuses) db.Statuses.Add(st.Key, st.Value);
            return db;
        }

        static BattleEngine Engine(GameDB db, int seed, string[] enemies, HeroCombatSpec[] heroes, params string[] known)
        {
            var setup = new BattleSetup { Seed = seed, Kind = BattleKind.Random };
            setup.Party.AddRange(heroes);
            setup.EnemyGroup.AddRange(enemies);
            foreach (var k in known) setup.KnownWeaknesses.Add(k);
            return new BattleEngine(db, setup);
        }

        static HeroCombatSpec[] Trio() => new[] { Hero("h0", 1000), Hero("h1", 999), Hero("h2", 998) };

        static string RngState(GodotRng rng)
            => string.Join(",", typeof(GodotRng).GetFields(BindingFlags.Instance | BindingFlags.NonPublic).Select(f => f.GetValue(rng).ToString()));

        static Dictionary<string, List<BattleAction>> Planned(BattleEngine e)
            => (Dictionary<string, List<BattleAction>>)typeof(BattleEngine).GetField("_planned", BindingFlags.Instance | BindingFlags.NonPublic).GetValue(e);

        static object Call(BattleEngine e, string name, params object[] args)
            {
            var method = typeof(BattleEngine).GetMethod(name, BindingFlags.Instance | BindingFlags.NonPublic);
            var parameters = method.GetParameters();
            var full = new object[parameters.Length];
            for (int i = 0; i < full.Length; i++) full[i] = i < args.Length ? args[i] : parameters[i].DefaultValue;
            return method.Invoke(e, full);
        }

        static BattleUnit Foe(BattleEngine e, string defId) => e.Enemies.First(u => u.DefId == defId);

        /// <summary>Submits Guard (or a given command) for heroes until the battle reaches a new round or ends.</summary>
        static List<BattleEvent> FinishRound(BattleEngine e, Func<BattleUnit, BattleCommand> command = null)
        {
            var all = new List<BattleEvent>();
            int round = e.Round;
            while (e.State == BattleEngineState.AwaitingCommand && e.Round == round)
                all.AddRange(e.Submit(command?.Invoke(e.ActiveHero) ?? BattleCommand.Guard()));
            return all;
        }

        static void Silence(GameDB db, BattleUnit unit, string status = "silence")
            => unit.ApplyStatus(BattleStatus.FromDef(db.Statuses[status], ""));

        /// <summary>Segment of enemy-turn events for one actor (TurnStart .. TurnEnd).</summary>
        static List<BattleEvent> TurnOf(IReadOnlyList<BattleEvent> events, string unitId)
        {
            int start = events.ToList().FindIndex(x => x is TurnStartEvent t && t.UnitId == unitId);
            Assert.True(start >= 0, "turn of " + unitId);
            var r = new List<BattleEvent>();
            for (int i = start; i < events.Count; i++)
            {
                r.Add(events[i]);
                if (events[i] is TurnEndEvent end && end.Unit.Id == unitId) break;
            }
            return r;
        }

        // --- O4 planning ---------------------------------------------------------------------------------

        [LogicTest]
        public static void IntentsArePlannedAfterRoundOrderInUnitAndSlotOrderAndAreImmutable()
        {
            var db = Db();
            var e = Engine(db, 11, new[] { "charger", "grunt", "striker" }, Trio());
            var events = e.Start().ToList();
            int round = events.FindIndex(x => x is RoundStartEvent);
            int firstTurn = events.FindIndex(x => x is TurnStartEvent);
            var planned = events.OfType<EnemyIntentPlannedEvent>().ToList();
            Assert.Equal(4, planned.Count, "charger has two slots, grunts one each");
            Assert.True(planned.All(p => events.IndexOf(p) > round && events.IndexOf(p) < firstTurn), "planning follows RoundStart, before any turn");
            var order = planned.Select(p => (e.UnitIndexOf(p.EnemyUnitId), p.Slot)).ToList();
            Assert.True(order.SequenceEqual(order.OrderBy(x => x.Item1).ThenBy(x => x.Item2)), "unit index then slot");
            Assert.True(planned.All(p => p.Round == 1), "round stamped");
            var charge = planned.First(p => p.EnemyUnitId == Foe(e, "charger").Id && p.Slot == 0);
            Assert.True(charge.IsChargeAnnounce && charge.SkillId == "big" && charge.TargetUnitId != null && !charge.IsRandom, "first slot announces with a frozen single target");
            var second = planned.First(p => p.EnemyUnitId == Foe(e, "charger").Id && p.Slot == 1);
            Assert.True(second.Kind == ActionKind.Attack && second.SkillId == "basic_attack" && !second.IsChargeAnnounce, "charging excludes the charge skill from the other slot");

            string rng = RngState(e.Rng);
            var query = e.EnemyIntents;
            Assert.Equal(4, query.Count, "query lists unconsumed slots");
            Assert.Equal(rng, RngState(e.Rng), "intent query draws nothing");
            foreach (var type in new[] { typeof(EnemyIntent), typeof(PendingCharge), typeof(EnemyIntentPlannedEvent), typeof(IntentClearedEvent),
                         typeof(ChargeStartedEvent), typeof(ChargeReleasedEvent), typeof(ChargeCancelledEvent) })
            {
                Assert.True(type.GetFields(BindingFlags.Instance | BindingFlags.Public).Length == 0, type.Name + " exposes no mutable fields");
                Assert.True(type.GetProperties(BindingFlags.Instance | BindingFlags.Public)
                    .All(p => p.Name == "Seq" || p.SetMethod == null || !p.SetMethod.IsPublic), type.Name + " has no public setters");
                Assert.True(type.GetProperties().All(p => p.PropertyType != typeof(SkillDef) && p.PropertyType != typeof(BattleUnit)), type.Name + " holds no live references");
            }
            string before = string.Join("|", planned.Select(p => $"{p.EnemyUnitId}{p.Slot}{p.Kind}{p.SkillId}{p.TargetUnitId}{p.Scope}"));
            FinishRound(e, h => BattleCommand.Attack(Foe(e, "grunt").Id));
            FinishRound(e);
            Assert.Equal(before, string.Join("|", planned.Select(p => $"{p.EnemyUnitId}{p.Slot}{p.Kind}{p.SkillId}{p.TargetUnitId}{p.Scope}")), "replayed intents never change");
        }

        [LogicTest]
        public static void StoredActionsExecuteAndReplayDeterministically()
        {
            var db = TestMain.DB;
            int actions = 0, retargets = 0, fallbacks = 0;
            foreach (var group in new[] { new[] { "slime", "slime", "bat" }, new[] { "boss" }, new[] { "abyss_lord" }, new[] { "leviathan" }, new[] { "festival_pumpkin_king" } })
                for (int seed = 1; seed <= 3; seed++)
                {
                    string Run(out List<BattleEvent> evs)
                    {
                        var setup = BattleTestUtil.Setup(group[0] == "slime" ? 5 : 40, group, seed, group.Length == 1 ? BattleKind.Boss : BattleKind.Random);
                        evs = BattleTestUtil.RunAuto(new BattleEngine(db, setup), 60);
                        return string.Join("\n", evs.Select(x => BattleTestUtil.Describe(x) + (x is EnemyIntentPlannedEvent p ? $" {p.EnemyUnitId}/{p.Slot}/{p.Kind}/{p.SkillId}/{p.TargetUnitId}/{p.IsChargeAnnounce}{p.IsChargeRelease}" : "")));
                    }
                    string a = Run(out var events), b = Run(out _);
                    Assert.Equal(a, b, "same seed, same events and intents");
                    var open = new Dictionary<(string, int), EnemyIntentPlannedEvent>();
                    var lastCleared = new Dictionary<string, IntentClearedEvent>();
                    var down = new HashSet<string>();
                    for (int i = 0; i < events.Count; i++)
                    {
                        switch (events[i])
                        {
                            case EnemyIntentPlannedEvent p: open[(p.EnemyUnitId, p.Slot)] = p; break;
                            case UnitDownEvent d: down.Add(d.UnitId); break;
                            case ReviveEvent r: down.Remove(r.UnitId); break;
                            case IntentClearedEvent c: lastCleared[c.EnemyUnitId] = c; break;
                            case ActionStartEvent act when lastCleared.TryGetValue(act.ActorId, out var cleared):
                            {
                                lastCleared.Remove(act.ActorId); // bleed may sit between the clear and the action
                                var intent = open[(cleared.EnemyUnitId, cleared.Slot)];
                                actions++;
                                Assert.Equal(intent.Kind, act.Kind, "executed kind equals the stored intent");
                                if (act.Kind == ActionKind.Skill) Assert.Equal(intent.SkillId, act.SkillId, "stored skill is never rerolled");
                                if (intent.TargetUnitId != null && act.TargetIds.Count > 0 && act.TargetIds[0] != intent.TargetUnitId)
                                {
                                    Assert.True(down.Contains(intent.TargetUnitId), "retarget only when the frozen target went down");
                                    retargets++;
                                }
                                break;
                            }
                            case ActionStartEvent act when db.Enemies.ContainsKey(act.ActorId.Substring(9)):
                                fallbacks++;
                                break;
                        }
                    }
                }
            Console.WriteLine($"  intent replay: {actions} enemy actions matched, {retargets} retargets, {fallbacks} unmatched");
            Assert.True(actions > 100 && fallbacks == 0, "every enemy action follows a stored or announced intent");
        }

        [LogicTest]
        public static void InvalidFrozenTargetRetargetsWithoutRerollingTheSkill()
        {
            var db = Db();
            var e = Engine(db, 5, new[] { "striker" }, Trio());
            var start = e.Start();
            var intent = start.OfType<EnemyIntentPlannedEvent>().Single();
            Assert.True(intent.Kind == ActionKind.Skill && intent.SkillId == "small", "planned skill");
            while (e.ActiveHero != null && e.ActiveHero.Id == intent.TargetUnitId) e.Submit(BattleCommand.Guard());
            e.UnitById(intent.TargetUnitId).Hp = 0; // frozen target removed after planning
            var events = FinishRound(e);
            var turn = TurnOf(events, intent.EnemyUnitId);
            Assert.True(!turn.OfType<EnemyIntentPlannedEvent>().Any(), "no reroll");
            var act = turn.OfType<ActionStartEvent>().Single();
            Assert.Equal("small", act.SkillId, "the frozen skill is kept");
            Assert.True(act.TargetIds.Single() != intent.TargetUnitId && e.UnitById(act.TargetIds.Single()).IsAlive, "retargeted onto a living hero");
        }

        [LogicTest]
        public static void PhaseRerollsMissingSkillAddsSlotsAndSummonsJoinNextRound()
        {
            var db = Db();
            var e = Engine(db, 7, new[] { "phaser" }, Trio());
            var phaser = Foe(e, "phaser");
            Assert.Equal(1, e.Start().OfType<EnemyIntentPlannedEvent>().Count(), "one slot before the phase");
            var hit = e.Submit(BattleCommand.Skill("slash1", phaser.Id));
            Assert.True(hit.OfType<BossPhaseEvent>().Any() && hit.OfType<SummonEvent>().Any(), "phase with a summon");
            string summoned = hit.OfType<SummonEvent>().Single().Unit.Id;
            var events = FinishRound(e);
            var turn = TurnOf(hit.Concat(events).ToList(), phaser.Id);
            var cleared = turn.OfType<IntentClearedEvent>().First();
            Assert.Equal(0, cleared.Slot, "the planned old skill is withdrawn");
            var acts = turn.OfType<ActionStartEvent>().ToList();
            Assert.True(acts.Count == 2 && acts.All(a => a.SkillId == "phase_hit"), "rerolled slot and the added slot use the phase list");
            var newIntents = turn.OfType<EnemyIntentPlannedEvent>().ToList();
            Assert.True(newIntents.Select(p => p.Slot).SequenceEqual(new[] { 0, 1 }), "an intent is emitted for each newly rolled slot");
            Assert.True(turn.IndexOf(newIntents[1]) < turn.IndexOf(acts[1]) && turn.IndexOf(newIntents[1]) > turn.IndexOf(acts[0]), "the extra slot is rolled right before it acts");
            Assert.True(!hit.Concat(events).OfType<EnemyIntentPlannedEvent>().Any(p => p.EnemyUnitId == summoned && p.Round == 1), "summons do not act/plan in their arrival round");
            var next = events.OfType<EnemyIntentPlannedEvent>().Where(p => p.Round == 2).ToList();
            Assert.True(next.Any(p => p.EnemyUnitId == summoned) && next.Count(p => p.EnemyUnitId == phaser.Id) == 2, "summons join the next StartRound planning");

            var lower = Engine(db, 7, new[] { "phaser2" }, Trio());
            var p2 = Foe(lower, "phaser2");
            Assert.Equal(2, lower.Start().OfType<EnemyIntentPlannedEvent>().Count(), "two slots");
            var drop = lower.Submit(BattleCommand.Skill("slash1", p2.Id));
            var removed = drop.OfType<IntentClearedEvent>().Single();
            Assert.True(removed.EnemyUnitId == p2.Id && removed.Slot == 1, "lowered slot count drops the extra intent");
            var rest = FinishRound(lower);
            Assert.Equal(1, TurnOf(rest, p2.Id).OfType<ActionStartEvent>().Count(), "only one action after lowering");
        }

        [LogicTest]
        public static void SilenceAndMissingMpRerollTheSlot()
        {
            var db = Db();
            foreach (bool silence in new[] { true, false })
            {
                var e = Engine(db, 3, new[] { "caster" }, Trio());
                var caster = Foe(e, "caster");
                Assert.Equal("zap", e.Start().OfType<EnemyIntentPlannedEvent>().Single().SkillId, "MP skill planned");
                if (silence) Silence(db, caster); else caster.Mp = 0;
                var turn = TurnOf(FinishRound(e), caster.Id);
                Assert.True(turn.OfType<IntentClearedEvent>().First().Slot == 0, "invalid planned skill withdrawn");
                var re = turn.OfType<EnemyIntentPlannedEvent>().Single();
                Assert.True(re.Kind == ActionKind.Attack && turn.OfType<ActionStartEvent>().Single().Kind == ActionKind.Attack, "rerolled at execution");
            }
        }

        [LogicTest]
        public static void RunnerFleeIsAPlannedAction()
        {
            var db = Db();
            int fled = 0, stayed = 0;
            for (int seed = 1; seed <= 20; seed++)
            {
                var e = Engine(db, seed, new[] { "runner" }, Trio());
                var intent = e.Start().OfType<EnemyIntentPlannedEvent>().Single();
                var events = FinishRound(e);
                var runner = Foe(e, "runner");
                if (intent.Kind == ActionKind.Flee)
                {
                    fled++;
                    Assert.True(runner.Escaped && e.Outcome?.Result == BattleResult.Fled && e.Outcome.Experience == 0, "planned flee leaves without rewards");
                    Assert.True(events.OfType<ActionStartEvent>().Any(a => a.ActorId == runner.Id && a.Kind == ActionKind.Flee), "flee replayed as an action");
                }
                else
                {
                    stayed++;
                    Assert.True(!runner.Escaped && runner.IsAlive, "non-flee intent does not bolt");
                }
            }
            Assert.True(fled > 0 && stayed > 0, $"both runner branches occur ({fled} fled, {stayed} stayed)");
        }

        [LogicTest]
        public static void FrozenTargetAndProvokeAreResolvedAtPlanningOnly()
        {
            var db = Db();
            var e = Engine(db, 5, new[] { "striker" }, Trio());
            var intent = e.Start().OfType<EnemyIntentPlannedEvent>().Single();
            var striker = Foe(e, "striker");
            var other = e.Party.First(h => h.Id != intent.TargetUnitId);
            striker.ApplyStatus(BattleStatus.FromDef(db.Statuses["provoke"], other.Id));
            var act = TurnOf(FinishRound(e), striker.Id).OfType<ActionStartEvent>().Single();
            Assert.Equal(intent.TargetUnitId, act.TargetIds.Single(), "post-planning provoke does not override frozen single target");

            var forced = Engine(db, 5, new[] { "striker" }, Trio());
            var actor = Foe(forced, "striker");
            actor.ApplyStatus(BattleStatus.FromDef(db.Statuses["provoke"], forced.Party[2].Id));
            var frozen = forced.Start().OfType<EnemyIntentPlannedEvent>().Single();
            Assert.Equal(forced.Party[2].Id, frozen.TargetUnitId, "provoke at planning is frozen");
            actor.ClearStatuses();
            Assert.Equal(frozen.TargetUnitId, TurnOf(FinishRound(forced), actor.Id).OfType<ActionStartEvent>().Single().TargetIds.Single(), "expired provoke leaves planned target unchanged");
        }

        [LogicTest]
        public static void PlanningAndExecutionUseTheExactExpectedRngDrawOrder()
        {
            var db = Db();
            db.Skills["random_hit"] = Skill("random_hit", SkillKind.Damage, Element.Fire, Scope.Random, hits: 4, scaling: ScalingStat.Magic);
            db.Skills["all_hit"] = Skill("all_hit", SkillKind.Damage, Element.None, Scope.All, scaling: ScalingStat.Magic);
            db.Enemies["random"] = Enemy("random", skills: new[] { "random_hit" }, weights: new[] { 1 });
            db.Enemies["all"] = Enemy("all", skills: new[] { "all_hit" }, weights: new[] { 1 });
            var e = Engine(db, 61, new[] { "random", "all" }, Trio());
            var paired = new GodotRng(61);
            // Unit-index planning: weighted skill selection, no random per-hit picks or all targets at planning.
            paired.Randf(); paired.Randf();
            var plans = e.Start().OfType<EnemyIntentPlannedEvent>().ToList();
            Assert.Equal(RngState(paired), RngState(e.Rng), "planning rolls selection only, in unit/slot order");
            Assert.True(plans[0].IsRandom && plans[0].Scope == Scope.Random && plans[0].TargetUnitId == null, "random intent has no frozen allocation");
            Assert.True(!plans[1].IsRandom && plans[1].Scope == Scope.All && plans[1].TargetUnitId == null, "all intent has no single target");
            var picks = new List<string>();
            for (int h = 0; h < 4; h++) picks.Add(e.Party[paired.RandiRange(0, e.Party.Count - 1)].Id);
            foreach (var id in picks) DamageFormula.Damage(Foe(e, "random"), e.UnitById(id), db.Skills["random_hit"], paired);
            foreach (var hero in e.Party) DamageFormula.Damage(Foe(e, "all"), hero, db.Skills["all_hit"], paired);
            // Next round planning: same two weighted selections, still no target allocations.
            paired.Randf(); paired.Randf();
            var events = FinishRound(e);
            var randomAct = TurnOf(events, Foe(e, "random").Id).OfType<ActionStartEvent>().Single();
            Assert.True(randomAct.TargetIds.SequenceEqual(picks), "per-hit picks made at execution only");
            Assert.Equal(RngState(paired), RngState(e.Rng), "execution draws picks then normal damage, followed by next-round selections");
        }

        [LogicTest]
        public static void FrozenSupportTargetsKeepSelectedHealAndRetargetOnlyWhenInvalid()
        {
            var db = Db();
            db.Enemies["support"] = Enemy("support", skills: new[] { "heal", "small" }, weights: new[] { 1, 0 }, ai: "support");
            var e = Engine(db, 7, new[] { "support", "grunt", "striker" }, Trio());
            var support = Foe(e, "support"); var grunt = Foe(e, "grunt"); var striker = Foe(e, "striker");
            grunt.Hp = grunt.MaxHp / 4;
            var plan = e.Start().OfType<EnemyIntentPlannedEvent>().First(p => p.EnemyUnitId == support.Id);
            Assert.True(plan.SkillId == "heal" && plan.TargetUnitId == grunt.Id, "injured ally frozen");
            grunt.Hp = grunt.MaxHp; striker.Hp = 1;
            var act = TurnOf(FinishRound(e), support.Id).OfType<ActionStartEvent>().First();
            Assert.True(act.SkillId == "heal" && act.TargetIds.Single() == grunt.Id, "target changed injury rank, but stayed valid; skill and target retained");

            var other = Engine(db, 7, new[] { "support", "grunt", "striker" }, Trio());
            support = Foe(other, "support"); grunt = Foe(other, "grunt"); striker = Foe(other, "striker");
            grunt.Hp /= 4; striker.Hp /= 2;
            other.Start(); grunt.Hp = 0;
            var turn = TurnOf(FinishRound(other), support.Id);
            act = turn.OfType<ActionStartEvent>().First();
            Assert.True(act.SkillId == "heal" && act.TargetIds.Single() == striker.Id, "dead support target: keep heal, normal most-injured retarget");
            Assert.True(!turn.OfType<EnemyIntentPlannedEvent>().Any(), "no skill reroll");
        }

        [LogicTest]
        public static void PlannedSummonFallsBackWhenSlotsFillAndJoinsPlanningNextRound()
        {
            var db = Db();
            db.Enemies["summoner"] = Enemy("summoner", ai: "summoner");
            db.Enemies["summoner"].Summons.Add("grunt"); db.Enemies["summoner"].SummonLimit = 1;
            var e = Engine(db, 3, new[] { "summoner" }, Trio());
            var summoner = Foe(e, "summoner");
            // Fixed PCG state zero yields the summon chance roll0, no favorable seed search.
            typeof(GodotRng).GetField("_state", BindingFlags.Instance | BindingFlags.NonPublic).SetValue(e.Rng, 0UL);
            var intent = e.Start().OfType<EnemyIntentPlannedEvent>().First();
            Assert.True(intent.Kind == ActionKind.Summon && intent.SkillId == "" && intent.PayloadId == "grunt", "summon uses explicit kind and payload, no fake skill ID");
            var events = FinishRound(e);
            string summoned = events.OfType<SummonEvent>().Single().Unit.Id;
            Assert.True(!events.OfType<TurnStartEvent>().Any(t => t.UnitId == summoned), "arrival round has no turn");
            Assert.True(events.OfType<EnemyIntentPlannedEvent>().Any(p => p.Round == 2 && p.EnemyUnitId == summoned), "next round plans the summon");

            var full = Engine(db, 3, new[] { "summoner" }, Trio());
            summoner = Foe(full, "summoner");
            typeof(GodotRng).GetField("_state", BindingFlags.Instance | BindingFlags.NonPublic).SetValue(full.Rng, 0UL);
            Assert.Equal(ActionKind.Summon, full.Start().OfType<EnemyIntentPlannedEvent>().First().Kind, "summon planned with room");
            Call(full, "Summon", summoner, new[] { "grunt" }); // consumes its summon slot before the planned action
            var turn = TurnOf(FinishRound(full), summoner.Id);
            Assert.True(!turn.OfType<SummonEvent>().Any() && turn.OfType<ActionStartEvent>().First().Kind == ActionKind.Attack, "stale summon slots safely fall back, no double summon");
        }

        // --- O3/O4 charge --------------------------------------------------------------------------------

        static (int lo, int hi) MagicRange(BattleUnit actor, BattleUnit target, SkillDef skill, double scale)
        {
            int Hit(double roll) => DamageFormula.FinalAmount(DamageFormula.ApplyTargetMultipliers(
                DamageFormula.BaseAmount(actor, target, skill, scale) * roll, target, skill, DamageType.Magical,
                DamageFormula.ElementMultiplier(target, DamageFormula.ElementOf(actor, skill)), target.Broken));
            return (Hit(DamageFormula.LowestRoll(DamageFormula.DamageVariance)), Hit(DamageFormula.HighestRoll(DamageFormula.DamageVariance)));
        }

        [LogicTest]
        public static void ChargeAnnouncesWithoutDamageAndReleasesNextRoundAtPowerOneAndAHalf()
        {
            var db = Db();
            var big = db.Skills["big"];
            var e = Engine(db, 9, new[] { "charger" }, Trio());
            var charger = Foe(e, "charger");
            e.Start();
            var round1 = FinishRound(e);
            var turn = TurnOf(round1, charger.Id);
            int start = turn.FindIndex(x => x is ActionStartEvent a && a.IsChargeAnnounce);
            int end = turn.FindIndex(start, x => x is ActionEndEvent);
            var announce = turn.GetRange(start, end - start + 1);
            Assert.True(!announce.OfType<DamageEvent>().Any() && !announce.OfType<MissEvent>().Any(), "announcement deals no damage");
            Assert.Equal(-10, announce.OfType<MpChangeEvent>().Single().Delta, "MP is paid once at announcement");
            var started = announce.OfType<ChargeStartedEvent>().Single();
            Assert.True(started.SkillId == "big" && started.TargetUnitId != null, "charge stored with frozen target");
            Assert.True(!round1.OfType<ChargeReleasedEvent>().Any(), "no same-round release");
            var slot1 = TurnOf(round1, charger.Id).OfType<ActionStartEvent>().Last();
            Assert.True(slot1.Kind == ActionKind.Attack, "other slot acts normally without the charge skill");
            Assert.Equal(90, charger.Mp, "MP after announcement");

            var plan2 = round1.OfType<EnemyIntentPlannedEvent>().Where(p => p.Round == 2).ToList();
            Assert.True(plan2[0].Slot == 0 && plan2[0].IsChargeRelease && plan2[0].SkillId == "big" && plan2[0].TargetUnitId == started.TargetUnitId, "slot 0 forced to the release");
            Assert.True(plan2[1].SkillId != "big", "remaining slots exclude the charge skill");
            // Release needs no MP, ignores silence and uses the stored skill.
            Silence(db, charger); charger.Mp = 0;
            var target = e.UnitById(started.TargetUnitId);
            var round2 = FinishRound(e, h => BattleCommand.Attack(charger.Id));
            // Ranges after the round: the target's round-1 guard dropped at its own turn start, before the release.
            var scaled = MagicRange(charger, target, big, 1.5);
            var plain = MagicRange(charger, target, big, 1.0);
            var release = TurnOf(round2, charger.Id);
            Assert.True(release.OfType<ChargeReleasedEvent>().Single().SkillId == "big" && release.OfType<ActionStartEvent>().First().IsChargeRelease, "released");
            var damage = release.OfType<DamageEvent>().First(d => d.SourceId == charger.Id);
            Assert.True(damage.TargetId == target.Id && damage.Amount >= scaled.lo && damage.Amount <= scaled.hi && damage.Amount > plain.hi,
                $"x1.5 power: {damage.Amount} in {scaled.lo}-{scaled.hi}, above unscaled max {plain.hi}");
            Assert.True(!release.OfType<MpChangeEvent>().Any(m => m.UnitId == charger.Id), "no second MP payment");
            Assert.True(big.Power == 2f && big.MpCost == 10, "shared SkillDef untouched");
            Assert.True(charger.PendingCharge == null, "consumed");
            Assert.True(!round2.OfType<ChargeStartedEvent>().Any(), "no re-announce in the release round");
        }

        [LogicTest]
        public static void BreakCancelsTheChargeImmediatelyWithoutRefund()
        {
            var db = Db();
            var e = Engine(db, 9, new[] { "charger" }, Trio());
            var charger = Foe(e, "charger");
            e.Start();
            FinishRound(e);
            Assert.True(charger.PendingCharge != null, "announced");
            var hit = e.Submit(BattleCommand.Skill("slash3", charger.Id)).ToList();
            int brk = hit.FindIndex(x => x is BreakEvent b && b.UnitId == charger.Id);
            Assert.True(brk >= 0 && hit[brk + 1] is ChargeCancelledEvent c && c.Reason == ChargeCancelReason.Break && c.EnemyUnitId == charger.Id, "저지: cancelled right at BREAK");
            Assert.True(hit[brk + 2] is IntentClearedEvent ic && ic.Slot == 0, "release intent withdrawn");
            Assert.True(charger.PendingCharge == null && charger.Mp == 90, "no refund");
            var rest = FinishRound(e).Concat(FinishRound(e)).ToList();
            Assert.True(!rest.OfType<ChargeReleasedEvent>().Any(), "never released");
        }

        [LogicTest]
        public static void TurnSkipDelaysReleaseAndPhaseChangeDoesNotCancel()
        {
            var db = Db();
            var e = Engine(db, 9, new[] { "charger" }, Trio());
            var charger = Foe(e, "charger");
            e.Start();
            FinishRound(e);
            Silence(db, charger, "stun");
            var round2 = FinishRound(e);
            Assert.True(round2.OfType<TurnSkippedEvent>().Any(t => t.UnitId == charger.Id), "stunned turn skipped");
            Assert.True(!round2.OfType<ChargeReleasedEvent>().Any() && !round2.OfType<ChargeCancelledEvent>().Any() && charger.PendingCharge != null, "kept pending");
            var round3 = FinishRound(e);
            Assert.True(round2.OfType<EnemyIntentPlannedEvent>().Any(p => p.Round == 3 && p.Slot == 0 && p.IsChargeRelease), "replanned");
            Assert.True(round3.OfType<ChargeReleasedEvent>().Any(), "released on its next actual action");

            var p = Engine(db, 9, new[] { "phase_charger" }, Trio());
            var pc = Foe(p, "phase_charger");
            p.Start();
            FinishRound(p);
            Assert.True(pc.PendingCharge != null, "announced");
            var round = FinishRound(p, h => BattleCommand.Attack(pc.Id));
            Assert.True(round.OfType<BossPhaseEvent>().Any() && !pc.Skills.Any(s => s.Id == "big"), "phase removed the skill");
            Assert.True(!round.OfType<ChargeCancelledEvent>().Any() && round.OfType<ChargeReleasedEvent>().Any(), "phase does not cancel; stored skill released");
        }

        [LogicTest]
        public static void RemovalCancelsAndRewardsRollOnce()
        {
            var db = Db();
            var e = Engine(db, 9, new[] { "fragile" }, Trio());
            var boss = Foe(e, "fragile");
            e.Start();
            FinishRound(e);
            Assert.True(boss.PendingCharge != null, "announced");
            var all = FinishRound(e, h => BattleCommand.Attack(boss.Id));
            var cancel = all.OfType<ChargeCancelledEvent>().Single();
            Assert.Equal(ChargeCancelReason.Removed, cancel.Reason, "death cancels");
            Assert.True(all.IndexOf(cancel) < all.FindIndex(x => x is UnitDownEvent), "cancel precedes the down event");
            Assert.Equal(1, all.OfType<BattleEndEvent>().Count(), "one battle end / reward roll");
            Assert.True(e.EnemyIntents.Count == 0, "no intents after the battle");
        }

        [LogicTest]
        public static void PowerScaleScalesSkillPowerBeforeDefenseAndDefaultsExactly()
        {
            var db = Db();
            var e = Engine(db, 2, new[] { "charger" }, Trio());
            var boss = Foe(e, "charger"); var hero = e.Party[0];
            var big = db.Skills["big"];
            double baseline = DamageFormula.BaseAmount(boss, hero, big);
            double scaled = DamageFormula.BaseAmount(boss, hero, big, 1.5);
            Assert.Near(300 * 2 * 1.5 - 5 * DamageFormula.DefenseFactor, scaled, 1e-9, "power term x1.5 before defense");
            Assert.True(Math.Abs(scaled - baseline * 1.5) > 1, "differs from post-defense damage x1.5");
            for (ulong seed = 1; seed <= 200; seed++)
            {
                var a = new GodotRng(seed); var b = new GodotRng(seed);
                var x = DamageFormula.Damage(boss, hero, big, a);
                var y = DamageFormula.Damage(boss, hero, big, b, 1.0, 1.0);
                Assert.True(x.Amount == y.Amount && RngState(a) == RngState(b), "default equals explicit 1.0");
                var c = new GodotRng(seed);
                DamageFormula.Damage(boss, hero, big, c, 1.0, 1.5);
                Assert.Equal(RngState(a), RngState(c), "scaling draws nothing extra");
            }
        }

        [LogicTest]
        public static void ChargeTpAndMpArePaidOnlyOnceAndStoredTargetRetargetsOnRelease()
        {
            var db = Db();
            db.Skills["big"].TpCost = 25;
            var e = Engine(db, 9, new[] { "charger" }, Trio());
            var boss = Foe(e, "charger"); boss.Tp = 25;
            e.Start();
            var round1 = FinishRound(e);
            Assert.True(round1.OfType<TpChangeEvent>().Single(t => t.UnitId == boss.Id).Delta == -25 && boss.Tp == 0 && boss.Mp == 90, "costs paid on announcement");
            string target = boss.PendingCharge.TargetUnitId;
            Assert.True(target != e.ActiveHero.Id, "fixture target is not the currently waiting hero");
            e.UnitById(target).Hp = 0;
            var release = TurnOf(FinishRound(e), boss.Id);
            Assert.True(release.OfType<ChargeReleasedEvent>().Any() && !release.OfType<MpChangeEvent>().Any(m => m.UnitId == boss.Id)
                && !release.OfType<TpChangeEvent>().Any(t => t.UnitId == boss.Id), "zero MP/TP still releases without a second cost");
            var act = release.OfType<ActionStartEvent>().First();
            Assert.True(act.IsChargeRelease && act.SkillId == "big" && act.TargetIds.Single() != target, "invalid stored target retargeted without skill reroll");
            Assert.Equal("big", round1.OfType<ChargeStartedEvent>().Single().SkillId, "earlier charge event is immutable");
        }

        [LogicTest]
        public static void AllAndRandomChargeAnnounceNoAllocationsOrHits()
        {
            foreach (Scope scope in new[] { Scope.All, Scope.Random })
            {
                var db = Db();
                db.Skills["big"].Scope = scope; db.Skills["big"].HitCount = 3;
                var e = Engine(db, 9, new[] { "charger" }, Trio()); var boss = Foe(e, "charger");
                var intent = e.Start().OfType<EnemyIntentPlannedEvent>().First();
                Assert.True(intent.TargetUnitId == null && intent.Scope == scope && intent.IsRandom == (scope == Scope.Random), "scope is explicit, no single target");
                var round1 = FinishRound(e); var turn = TurnOf(round1, boss.Id);
                var announce = turn.OfType<ActionStartEvent>().First();
                Assert.True(announce.IsChargeAnnounce && announce.TargetIds.Count == 0 && announce.Scope == scope, "announce allocates no All/Random targets");
                Assert.True(boss.PendingCharge.TargetUnitId == null && boss.PendingCharge.Scope == scope, "stored scope");
                var round2 = FinishRound(e);
                var release = TurnOf(round2, boss.Id).OfType<ActionStartEvent>().First();
                Assert.True(release.IsChargeRelease && release.Scope == scope && release.TargetIds.Count == 3, "targets allocated at release");
            }
        }

        [LogicTest]
        public static void AllCrowdControlSkipsDelayAndNeverCancelTheCharge()
        {
            foreach (string status in new[] { "stun", "sleep", "freeze" })
            {
                var db = Db(); var e = Engine(db, 9, new[] { "charger" }, Trio()); var boss = Foe(e, "charger");
                e.Start(); FinishRound(e); Silence(db, boss, status);
                var skipped = FinishRound(e);
                Assert.True(skipped.OfType<TurnSkippedEvent>().Any(t => t.UnitId == boss.Id) && boss.PendingCharge != null && !skipped.OfType<ChargeCancelledEvent>().Any(), status + " delays, never cancels");
                boss.ClearStatuses();
                Assert.True(FinishRound(e).OfType<ChargeReleasedEvent>().Any(), status + " release after recovery");
            }
        }

        // --- O5 AUTO --------------------------------------------------------------------------------------

        static void Pending(BattleEngine e, GameDB db, BattleUnit enemy, int announcedRound, string target = null)
        {
            enemy.PendingCharge = new PendingCharge("big", target, announcedRound, target == null ? Scope.All : Scope.Single);
            enemy.PendingChargeSkill = db.Skills["big"];
        }

        [LogicTest]
        public static void AutoBreaksAPendingChargeWithKnownWeaknessOnly()
        {
            var db = Db();
            db.Enemies["plain_boss"].BreakShield = 3; db.Enemies["plain_boss"].Weaknesses.Add(Slash);
            string key = "plain_boss:" + Slash;
            BattleEngine Make(string[] enemies, HeroCombatSpec[] heroes, bool known)
            {
                var x = Engine(db, 4, enemies, heroes, known ? new[] { key } : new string[0]);
                x.Start();
                var boss = Foe(x, "plain_boss");
                Planned(x)[boss.Id] = new List<BattleAction>();
                Pending(x, db, boss, x.Round);
                return x;
            }
            // Own three hits empty the shield.
            var e = Make(new[] { "plain_boss", "grunt" }, new[] { Hero("h0", 1000, "slash3", "slash1"), Hero("h1", 999, "slash1") }, true);
            var cmd = e.SuggestCommand(e.ActiveHero);
            Assert.True(cmd.Kind == CommandKind.Skill && cmd.SkillId == "slash3" && cmd.TargetId == Foe(e, "plain_boss").Id, "break the charge: " + cmd);
            string rng = RngState(e.Rng);
            e.SuggestCommand(e.ActiveHero);
            Assert.Equal(rng, RngState(e.Rng), "AUTO draws nothing");
            // Unknown weakness: no break trigger.
            e = Make(new[] { "plain_boss", "grunt" }, new[] { Hero("h0", 1000, "slash3"), Hero("h1", 999, "slash1") }, false);
            Assert.True(Call(e, "SuggestChargeBreak", e.ActiveHero) == null, "no known weakness, no break rule");
            // Greedy party: 1 + 1 < 3 fails; 1 + 3 succeeds and the actor uses its own highest-hit action.
            e = Make(new[] { "plain_boss" }, new[] { Hero("h0", 1000, "slash1"), Hero("h1", 999, "slash1") }, true);
            Assert.True(Call(e, "SuggestChargeBreak", e.ActiveHero) == null, "1+1 hits cannot empty shield 3");
            e = Make(new[] { "plain_boss" }, new[] { Hero("h0", 1000, "slash1"), Hero("h1", 999, "slash3") }, true);
            var greedy = (BattleCommand)Call(e, "SuggestChargeBreak", e.ActiveHero);
            Assert.True(greedy != null && greedy.SkillId == "slash1", "1+3 hits: actor commits its best");
            // A later ally that is unable to act contributes nothing.
            e = Make(new[] { "plain_boss" }, new[] { Hero("h0", 1000, "slash1"), Hero("h1", 999, "slash3") }, true);
            Silence(db, e.Party[1], "stun");
            Assert.True(Call(e, "SuggestChargeBreak", e.ActiveHero) == null, "stunned ally excluded");
            // Random scope: only when the charger is the sole valid target.
            e = Make(new[] { "plain_boss", "grunt" }, new[] { Hero("h0", 1000, "rand3") }, true);
            Assert.True(Call(e, "SuggestChargeBreak", e.ActiveHero) == null, "random hits are not guaranteed with two enemies");
            e = Make(new[] { "plain_boss" }, new[] { Hero("h0", 1000, "rand3") }, true);
            var sole = (BattleCommand)Call(e, "SuggestChargeBreak", e.ActiveHero);
            Assert.True(sole != null && sole.SkillId == "rand3" && sole.TargetId == null, "sole target: random hits all land on it");
        }

        [LogicTest]
        public static void AutoBreakCountsOnlyPartyTurnsBeforeTheRelease()
        {
            var db = Db();
            db.Enemies["plain_boss"].BreakShield = 3; db.Enemies["plain_boss"].Weaknesses.Add(Slash);
            foreach (int bossSpeed in new[] { 500, 1 })
            {
                db.Enemies["plain_boss"].Speed = bossSpeed;
                var e = Engine(db, 4, new[] { "plain_boss" }, new[] { Hero("h0", 1000, "slash1"), Hero("h1", 2, "slash3") }, "plain_boss:" + Slash);
                e.Start();
                var boss = Foe(e, "plain_boss");
                Planned(e)[boss.Id] = new List<BattleAction>();
                Pending(e, db, boss, e.Round - 1); // due: releases on the boss's turn this round
                var cmd = (BattleCommand)Call(e, "SuggestChargeBreak", e.ActiveHero);
                if (bossSpeed == 500) Assert.True(cmd == null, "ally acting after the release cannot help");
                else Assert.True(cmd != null && cmd.SkillId == "slash1", "ally acting before the release counts");
                Pending(e, db, boss, e.Round); // announced this round: releases next round, every remaining party turn counts
                Assert.True(Call(e, "SuggestChargeBreak", e.ActiveHero) != null, "fresh charge: both party turns count");
            }
        }

        static BattleAction Strike(BattleUnit enemy, BattleUnit target)
        {
            var a = BattleAction.Make(ActionKind.Attack, enemy.Id, new[] { target.Id });
            a.Scope = 0;
            return a;
        }

        static int Threat(BattleEngine e, BattleUnit enemy, BattleAction action, BattleUnit hero, bool active)
            => (int)Call(e, "ThreatMaximum", enemy, action, hero, active);

        [LogicTest]
        public static void AutoGuardsOnlyWhenGuardTurnsALethalHitSurvivable()
        {
            var db = Db();
            var e = Engine(db, 4, new[] { "brute", "grunt" }, new[] { Hero("h0", 1000), Hero("h1", 999) });
            e.Start();
            var brute = Foe(e, "brute"); var h0 = e.ActiveHero; var h1 = e.Party[1];
            var strike = Strike(brute, h0);
            Planned(e)[brute.Id] = new List<BattleAction> { strike };
            Planned(e)[Foe(e, "grunt").Id] = new List<BattleAction>();
            int max = Threat(e, brute, strike, h0, false);
            h0.Hp = max;
            Assert.Equal(CommandKind.Guard, e.SuggestCommand(h0).Kind, "lethal max, survivable when guarded");
            h0.Hp = max / 2;
            Assert.True(!(bool)Call(e, "ShouldGuardThreat", h0), "max/2 >= HP: guarding cannot save");
            h0.Hp = max + 1;
            Assert.True(!(bool)Call(e, "ShouldGuardThreat", h0), "not lethal");
            h0.Hp = max;
            Planned(e)[brute.Id] = new List<BattleAction> { Strike(brute, h1) };
            Assert.True(!(bool)Call(e, "ShouldGuardThreat", h0), "aimed at someone else");
            var random = BattleAction.Make(ActionKind.Skill, brute.Id, null, "rand3", db.Skills["rand3"]); random.Scope = 2;
            Planned(e)[brute.Id] = new List<BattleAction> { random };
            Assert.True(!(bool)Call(e, "ShouldGuardThreat", h0), "random allocations are not known threats");

            // A pending release next round ahead of the hero counts (x1.5 power).
            var f = Engine(db, 4, new[] { "charger_fast" }, new[] { Hero("h0", 1000) });
            f.Start();
            var fast = Foe(f, "charger_fast");
            Assert.True(fast.PendingCharge != null && fast.PendingCharge.TargetUnitId == f.ActiveHero.Id, "announced before the hero acts");
            var release = BattleAction.Make(ActionKind.Skill, fast.Id, new[] { f.ActiveHero.Id }, "big", db.Skills["big"]);
            release.PowerScale = 1.5;
            int releaseMax = Threat(f, fast, release, f.ActiveHero, false);
            Assert.True(releaseMax > MagicRange(fast, f.ActiveHero, db.Skills["big"], 1.0).hi, "threat uses x1.5 power");
            f.ActiveHero.Hp = releaseMax;
            Assert.Equal(CommandKind.Guard, f.SuggestCommand(f.ActiveHero).Kind, "guard the coming release");
        }

        [LogicTest]
        public static void AutoPrehealsAnAllyThatCannotGuardInTime()
        {
            var db = Db();
            // Healer acts first; the brute (speed 500) strikes before the ally (speed 1) can decide.
            foreach (bool before in new[] { true, false })
            {
                db.Enemies["brute"].Speed = before ? 500 : 1;
                var e = Engine(db, 4, new[] { "brute" }, new[] { Hero("healer", 1000, "heal"), Hero("ally", before ? 1 : 999) });
                e.Start();
                var brute = Foe(e, "brute"); var ally = e.Party[1];
                Planned(e)[brute.Id] = new List<BattleAction> { Strike(brute, ally) };
                ally.Hp = 700; // 70 %: no ordinary heal threshold
                var cmd = e.SuggestCommand(e.ActiveHero);
                if (before) Assert.True(cmd.Kind == CommandKind.Skill && cmd.SkillId == "heal" && cmd.TargetId == ally.Id, "pre-heal: " + cmd);
                else Assert.True(cmd.SkillId != "heal", "ally acts before the hit and can guard itself: " + cmd);
            }
            // An ally who already acted and is still guarding survives: no pre-heal.
            db.Enemies["brute"].Speed = 1;
            foreach (bool guarded in new[] { false, true })
            {
                var g = Engine(db, 4, new[] { "brute" }, new[] { Hero("ally", 1000), Hero("healer", 999, "heal") });
                g.Start();
                g.Submit(guarded ? BattleCommand.Guard() : BattleCommand.Attack(Foe(g, "brute").Id));
                var brute = Foe(g, "brute"); var ally = g.Party[0];
                Planned(g)[brute.Id] = new List<BattleAction> { Strike(brute, ally) };
                ally.Hp = 700;
                var strike = Strike(brute, ally);
                Assert.True(Threat(g, brute, strike, ally, false) >= 700 && Threat(g, brute, strike, ally, true) < 700 == guarded, "guard state models the hit");
                var cmd = g.SuggestCommand(g.ActiveHero);
                Assert.Equal(!guarded, cmd.SkillId == "heal" && cmd.TargetId == ally.Id, "already-acted ally pre-healed only when the hit is lethal");
            }
        }
        [LogicTest]
        public static void AutoThreatUsesKnownHeroAffinitiesAndBarrierWithoutMutation()
        {
            var db = Db(); var e = Engine(db, 4, new[] { "brute" }, new[] { Hero("h0", 1000), Hero("h1", 999) });
            e.Start(); var brute = Foe(e, "brute"); var hero = e.Party[0];
            var a = Strike(brute, hero); int plain = Threat(e, brute, a, hero, false);
            hero.ApplyStatus(BattleStatus.FromDef(new StatusDef { Id = "barrier_test", EffectType = StatusEffectType.Barrier, AbsorbAmount = 500, DurationTurns = 2 }, ""));
            var barrier = hero.Statuses.Single(); string rng = RngState(e.Rng); int mp = hero.Mp;
            Assert.Equal(plain - 500, Threat(e, brute, a, hero, true), "active barrier subtracts deterministic absorption");
            Assert.True(barrier.BarrierRemaining == 500 && hero.Mp == mp && RngState(e.Rng) == rng, "pure absorption estimate");
            hero.ClearStatuses();
            hero.ApplyStatus(BattleStatus.FromDef(new StatusDef { Id = "inv", EffectType = StatusEffectType.Invincible, DurationTurns = 2 }, ""));
            Assert.Equal(0, Threat(e, brute, a, hero, true), "active invincible means no preheal threat");
            hero.ClearStatuses();
            hero.ApplyStatus(BattleStatus.FromDef(new StatusDef { Id = "mana", EffectType = StatusEffectType.ManaShield, Magnitude = 0.5f, DurationTurns = 2 }, ""));
            Assert.Equal(plain - Math.Min(hero.Mp, Gd.RoundI(plain * 0.5)), Threat(e, brute, a, hero, true), "pure mana-shield budget");
            Assert.Equal(mp, hero.Mp, "no MP absorption spent by query");
        }

        [LogicTest]
        public static void AutoPrehealHandlesUnsurvivableGuardAndLowestRatioLearnOrder()
        {
            var db = Db();
            var e = Engine(db, 4, new[] { "brute" }, new[] { Hero("healer", 1000, "heal"), Hero("ally", 999) });
            e.Start(); var brute = Foe(e, "brute"); var ally = e.Party[1];
            var action = Strike(brute, ally);
            Planned(e)[brute.Id] = new List<BattleAction> { action };
            ally.MaxHp = 600; ally.Hp = 450; // 75%, but max/2 >450: ally's later Guard cannot save it
            var cmd = e.SuggestCommand(e.ActiveHero);
            Assert.True(cmd.SkillId == "heal" && cmd.TargetId == ally.Id, "preheal even when ally will act, if its guard cannot survive");
            // Lower ratio chooses the ally; no ordinary heal threshold, first applicable affordable heal wins.
            db.Skills["heal_second"] = Skill("heal_second", SkillKind.Heal, Element.None, target: TargetType.Ally, power: 3f);
            db.Skills["heal_self"] = Skill("heal_self", SkillKind.Heal, Element.None, target: TargetType.Self, power: 10f);
            var f = Engine(db, 4, new[] { "brute" }, new[] { Hero("healer", 1000, "heal_self", "heal", "heal_second"), Hero("a", 999), Hero("b", 998) });
            f.Start(); brute = Foe(f, "brute");
            f.Party[0].MaxHp = f.Party[0].Hp = 5000; // the healer itself is not threatened, so Guard does not outrank preheal
            f.Party[1].MaxHp = 600; f.Party[1].Hp = 480;
            f.Party[2].MaxHp = 600; f.Party[2].Hp = 450;
            var all = BattleAction.Make(ActionKind.Skill, brute.Id, null, "small", db.Skills["small"]); all.Scope = 1;
            Planned(f)[brute.Id] = new List<BattleAction> { all };
            cmd = f.SuggestCommand(f.ActiveHero);
            Assert.True(cmd.SkillId == "heal" && cmd.TargetId == f.Party[2].Id, "lowest HP ratio, skips self-only, preserves learn order");
            f.Party[1].Hp = 450;
            cmd = f.SuggestCommand(f.ActiveHero);
            Assert.Equal(f.Party[1].Id, cmd.TargetId, "equal ratio ties choose lowest unit index");
        }

        [LogicTest]
        public static void AutoAndPreviewQueriesLeaveFullChargeAndIntentStateAndFutureRngUntouched()
        {
            string Snapshot(BattleEngine e)
            {
                string unit(BattleUnit u) => $"{u.Id}/{u.Hp}/{u.Mp}/{u.Tp}/{u.Shield}/{u.Broken}/{u.Guarding}/{u.PhaseCcSuccesses}/"
                    + string.Join(",", u.Statuses.Select(st => $"{st.Id}:{st.TurnsRemaining}:{st.BarrierRemaining}:{st.SourceId}"))
                    + (u.PendingCharge == null ? "" : $"C{u.PendingCharge.SkillId}{u.PendingCharge.TargetUnitId}{u.PendingCharge.AnnouncedRound}{u.PendingCharge.Scope}");
                return $"{e.Round}/{e.TurnIndex}/{e.State}/{e.ActiveHero?.Id}/{e.Chain}/" + string.Join("|", e.Units.Select(unit))
                    + string.Join("|", e.EnemyIntents.Select(x => $"{x.Round}{x.EnemyUnitId}{x.Slot}{x.Kind}{x.SkillId}{x.TargetUnitId}{x.Scope}{x.IsChargeAnnounce}{x.IsChargeRelease}"))
                    + string.Join("|", e.Inventory.Select(x => x.Key + x.Value)) + RngState(e.Rng);
            }
            var db = Db();
            BattleEngine Make()
            {
                var e = Engine(db, 9, new[] { "charger", "grunt" }, Trio(), "charger:" + Slash);
                e.Start(); FinishRound(e);
                e.Party[1].ApplyStatus(BattleStatus.FromDef(db.Statuses["barrier"], ""));
                return e;
            }
            var queried = Make(); var control = Make();
            string before = Snapshot(queried);
            for (int i = 0; i < 10; i++)
                foreach (var hero in queried.Party)
                {
                    queried.SuggestCommand(hero); queried.GetCommandOptions(hero);
                    foreach (var foe in queried.Enemies)
                    {
                        queried.PreviewAction(queried.UnitIndexOf(hero), BattleCommand.Skill("slash3", foe.Id), queried.UnitIndexOf(foe));
                        queried.KnownAffinity(foe, Slash);
                    }
                    _ = queried.EnemyIntents; _ = Foe(queried, "charger").PendingCharge;
                }
            Assert.Equal(before, Snapshot(queried), "all queries leave the complete charge/intent/hero/knowledge/RNG state untouched");
            for (int turn = 0; turn < 6; turn++)
            {
                var a = queried.Submit(BattleCommand.Attack(Foe(queried, "grunt").Id));
                var b = control.Submit(BattleCommand.Attack(Foe(control, "grunt").Id));
                Assert.Equal(string.Join("\n", a.Select(BattleTestUtil.Describe)), string.Join("\n", b.Select(BattleTestUtil.Describe)), "paired future events/RNG");
                Assert.Equal(Snapshot(control), Snapshot(queried), "paired future full states");
            }
        }

        [LogicTest]
        public static void AllEighteenBossesOwnExactlyTheApprovedChargeSkills()
        {
            var mapped = new Dictionary<string, string>
            {
                ["boss"] = "sk_soul_reap", ["flame_sphinx"] = "sk_sun_judgment", ["forest_guardian"] = "strong_attack",
                ["frost_kraken"] = "sk_freezing_tide", ["leviathan"] = "sk_lev_abyss_breath", ["abyss_lord"] = "sk_lord_annihilation",
                ["subway_bat_lord"] = "sk_crow_swarm", ["scrap_colossus"] = "sk_titan_crash", ["crystal_cave_lord"] = "sk_e_crystal_spike",
                ["festival_pumpkin_king"] = "sk_crow_swarm", ["plague_lich"] = "sk_spirit_fire", ["abyss_herald"] = "sk_soul_reap",
                ["forest_guardian_ex"] = "sk_ex_ancient_wrath", ["frost_kraken_ex"] = "sk_ex_abyss_tide",
                ["flame_sphinx_ex"] = "sk_sun_judgment", ["boss_ex"] = "sk_ex_requiem", ["leviathan_ex"] = "sk_lev_abyss_breath", ["abyss_lord_ex"] = "sk_ex_true_void",
            };
            int bosses = 0;
            foreach (var def in TestMain.DB.Enemies.Values)
            {
                if (!def.IsBoss) { Assert.True(def.ChargeSkill == "", def.Id + ": non-boss has no charge"); continue; }
                bosses++;
                Assert.Equal(mapped[def.Id], def.ChargeSkill, def.Id + ": approved mapping");
                Assert.True(!def.Gimmicks.Contains("cc_immune") && def.Skills.Contains(def.ChargeSkill), def.Id + ": charge data and CC resistance");
            }
            Assert.Equal(18, bosses, "exactly all 18 bosses");
            Assert.True(TestMain.DB.Enemies["metal_slime"].Gimmicks.Contains("cc_immune"), "non-boss immunity preserved");
            Assert.True(new EnemyDef().ChargeSkill == "", "old data defaults safely to no charge");
        }

        [LogicTest]
        public static void AutoBreakAffordabilityUsesOneBestActionPerActorAndStableEnemyTies()
        {
            var db = Db();
            db.Enemies["plain_boss"].BreakShield = 5; db.Enemies["plain_boss"].Weaknesses.Add(Slash);
            db.Skills["costly3"] = Skill("costly3", SkillKind.Damage, Element.Slash, hits: 3, mp: 50);
            db.Skills["ulti3"] = Skill("ulti3", SkillKind.Damage, Element.Slash, hits: 3);
            db.Skills["ulti3"].TpCost = 100;
            var e = Engine(db, 4, new[] { "plain_boss", "plain_boss" }, new[] { Hero("h0", 1000, "slash1"), Hero("h1", 999, "costly3", "ulti3") }, "plain_boss:" + Slash);
            e.Start();
            foreach (var boss in e.Enemies) { Planned(e)[boss.Id] = new List<BattleAction>(); Pending(e, db, boss, e.Round); }
            e.Party[1].Mp = 50; e.Party[1].Tp = 100;
            Assert.True(Call(e, "SuggestChargeBreak", e.ActiveHero) == null, "1+max(3,3)=4, not 1+3+3: each ally gets only one action");
            foreach (var boss in e.Enemies) boss.Shield = 4;
            var cmd = (BattleCommand)Call(e, "SuggestChargeBreak", e.ActiveHero);
            Assert.Equal(e.Enemies[0].Id, cmd.TargetId, "equal charges choose lowest engine unit index");
            e.Party[1].Mp = 49; e.Party[1].Tp = 99;
            Assert.True(Call(e, "SuggestChargeBreak", e.ActiveHero) == null, "MP and TP unaffordable, no future contribution");
            e.Party[1].Tp = 100;
            Assert.True(Call(e, "SuggestChargeBreak", e.ActiveHero) != null, "affordable ultimate contributes");
            e.Party[1].Tp = 0; e.Party[1].Mp = 50; Silence(db, e.Party[1]);
            Assert.True(Call(e, "SuggestChargeBreak", e.ActiveHero) == null, "silenced MP skill contributes nothing");
        }

        [LogicTest]
        public static void ThreatsRespectHeroResistanceAndBarrierExpiryBeforeTheHit()
        {
            var db = Db();
            var a = Hero("h0", 1000); var b = Hero("h1", 999); b.ElementResists.Add((int)Element.Fire);
            var e = Engine(db, 4, new[] { "charger" }, new[] { a, b });
            e.Start(); var enemy = Foe(e, "charger");
            var skillAction = BattleAction.Make(ActionKind.Skill, enemy.Id, new[] { e.Party[0].Id }, "big", db.Skills["big"]);
            int neutral = Threat(e, enemy, skillAction, e.Party[0], false);
            int resisted = Threat(e, enemy, skillAction, e.Party[1], false);
            Assert.True(resisted < neutral && Math.Abs(resisted * 2 - neutral) <= 1, "heroes' own known resistances apply to threat damage");
            var hero = e.Party[0];
            hero.ApplyStatus(BattleStatus.FromDef(new StatusDef { Id = "last_barrier", EffectType = StatusEffectType.Barrier, AbsorbAmount = 500, DurationTurns = 1 }, ""));
            Assert.Equal(Math.Max(0, neutral - 500), Threat(e, enemy, skillAction, hero, true), "before hero turn the barrier absorbs");
            Assert.Equal(neutral, (int)Call(e, "ThreatMaximum", enemy, skillAction, hero, true, false, true), "after hero turn the one-turn barrier is expired");
            Assert.Equal(500, hero.Statuses.Single().BarrierRemaining, "local threat simulation never consumes actual barrier");
        }

        [LogicTest]
        public static void ChargeCanOnlyStartWhenItsSkillIsInTheCurrentPhaseList()
        {
            var db = Db();
            db.Enemies["phase_charger"].Phases.Clear();
            db.Enemies["phase_charger"].Phases.Add(new BossPhase { HpBelow = 1f, ActionsPerTurn = 1, Skills = new List<string> { "small" }, Weights = new List<int> { 1 } });
            var e = Engine(db, 9, new[] { "phase_charger" }, Trio());
            var plans = e.Start().OfType<EnemyIntentPlannedEvent>().ToList();
            Assert.True(plans.Single().SkillId == "small" && !plans.Single().IsChargeAnnounce, "phase lacks charge skill, no start");
            var events = FinishRound(e).Concat(FinishRound(e)).ToList();
            Assert.True(!events.OfType<ChargeStartedEvent>().Any() && Foe(e, "phase_charger").PendingCharge == null, "actor-level setting never injects an absent skill");
        }

        [LogicTest]
        public static void PrehealDoesNotCarryGuardAcrossASkippedTurnStart()
        {
            var db = Db(); var e = Engine(db, 4, new[] { "brute" }, new[] { Hero("healer", 1000, "heal"), Hero("ally", 999) });
            e.Start(); var ally = e.Party[1]; var brute = Foe(e, "brute");
            Planned(e)[brute.Id] = new List<BattleAction> { Strike(brute, ally) };
            ally.Hp = 700; ally.Guarding = true; Silence(db, ally, "stun");
            var cmd = e.SuggestCommand(e.ActiveHero);
            Assert.True(cmd.SkillId == "heal" && cmd.TargetId == ally.Id, "ally skips before hit: carried guard drops at TurnStart, cannot choose another Guard");
        }

        [LogicTest]
        public static void CurrentActorsExpiringAbsorptionNeverSuppressesRequiredPreheal()
        {
            foreach (var type in new[] { StatusEffectType.Barrier, StatusEffectType.ManaShield, StatusEffectType.Invincible })
                foreach (int duration in new[] { 1, 2 })
                {
                    var db = Db(); db.Enemies["brute"].Attack = 1800;
                    var e = Engine(db, 4, new[] { "brute" }, new[] { Hero("healer", 1000, "heal") });
                    e.Start(); var hero = e.ActiveHero; var enemy = Foe(e, "brute");
                    hero.Hp = 700; hero.Mp = hero.MaxMp = 2500;
                    hero.ApplyStatus(BattleStatus.FromDef(new StatusDef { Id = "def", EffectType = type, AbsorbAmount = 2500, Magnitude = 1f, DurationTurns = duration }, ""));
                    Planned(e)[enemy.Id] = new List<BattleAction> { Strike(enemy, hero) };
                    string rng = RngState(e.Rng); int barrier = hero.Statuses.Single().BarrierRemaining;
                    var options = new List<SkillDef> { db.Skills["heal"] };
                    var cmd = (BattleCommand)Call(e, "SuggestThreatHeal", hero, options, new List<BattleUnit> { hero });
                    Assert.Equal(duration == 1, cmd?.SkillId == "heal", type + " duration " + duration + ": imminent TurnEnd expires1, retains2");
                    Assert.Equal(duration == 1, e.SuggestCommand(hero).SkillId == "heal", "public AUTO respects the current actor's imminent expiry");
                    Assert.Equal(duration, hero.Statuses.Single().TurnsRemaining, "query does not tick live defense");
                    Assert.True(hero.Mp == 2500 && hero.Statuses.Single().BarrierRemaining == barrier && RngState(e.Rng) == rng, "query purity");
                }
        }

        [LogicTest]
        public static void ThreatForecastExpiresDefenseStatsInPhysicalAndMagicalChannels()
        {
            foreach (bool magical in new[] { false, true })
            {
                var db = Db(); db.Enemies["brute"].Attack = db.Enemies["brute"].Magic = 1000;
                var hero = Hero("h0", 1000); hero.Defense = hero.Resistance = 1000;
                var e = Engine(db, 4, new[] { "brute" }, new[] { Hero("healer", 2000), hero });
                e.Start(); var target = e.Party[1]; var enemy = Foe(e, "brute");
                var action = magical ? BattleAction.Make(ActionKind.Skill, enemy.Id, new[] { target.Id }, "big", db.Skills["big"]) : Strike(enemy, target);
                if (magical) action.Skill = Skill("magic", SkillKind.Damage, Element.None, scaling: ScalingStat.Magic);
                int unbuffed = Threat(e, enemy, action, target, false);
                target.ApplyStatus(BattleStatus.FromDef(new StatusDef { Id = "def_up", EffectType = StatusEffectType.DefenseUp, Magnitude = 1f, DurationTurns = 1 }, ""));
                Assert.Equal(1, Threat(e, enemy, action, target, false), "before holder acts the defense buff survives");
                Assert.Equal(unbuffed, (int)Call(e, "ThreatMaximum", enemy, action, target, false, false, true), "post-holder defense/resistance must use expired status forecast");
                target.Statuses.Single().TurnsRemaining = 2;
                Assert.Equal(1, (int)Call(e, "ThreatMaximum", enemy, action, target, false, false, true), "duration2 stat buff survives");
                Assert.Equal(2, target.Statuses.Single().TurnsRemaining, "pure stat forecast");
            }
        }

        [LogicTest]
        public static void DefinitelySkippedEnemySlotsNeverTriggerGuardOrPreheal()
        {
            foreach (string status in new[] { "stun", "sleep", "freeze" })
            {
                var db = Db(); db.Enemies["brute"].Speed = 500;
                var e = Engine(db, 4, new[] { "brute" }, new[] { Hero("healer", 1000, "heal"), Hero("ally", 1) });
                e.Start(); var enemy = Foe(e, "brute"); var hero = e.ActiveHero; var ally = e.Party[1];
                hero.Hp = 900; ally.Hp = 700;
                Planned(e)[enemy.Id] = new List<BattleAction> { Strike(enemy, hero), Strike(enemy, ally) };
                Assert.True((bool)Call(e, "ShouldGuardThreat", hero), "control: lethal executable slot");
                Silence(db, enemy, status); enemy.Statuses.Single().TurnsRemaining = 3;
                string rng = RngState(e.Rng);
                Assert.True(!(bool)Call(e, "ShouldGuardThreat", hero), status + " guarantees skipped planned slots");
                Assert.True(Call(e, "SuggestThreatHeal", hero, new List<SkillDef> { db.Skills["heal"] }, e.Party.ToList()) == null, status + " no preheal for a skipped slot");
                Assert.True(RngState(e.Rng) == rng && enemy.Statuses.Single().TurnsRemaining == 3, "queries never tick CC or RNG");
            }
        }

        [LogicTest]
        public static void PendingReleaseThreatOnlyCountsWhenCcRecoversBeforeNextDecision()
        {
            foreach (string status in new[] { "stun", "sleep", "freeze" })
                foreach (int duration in new[] { 1, 2, 3 })
                {
                    var db = Db();
                    db.Enemies["charger"].Speed = 500; // currently behind hero; next-round speed-up puts it ahead
                    var e = Engine(db, 4, new[] { "charger" }, new[] { Hero("h0", 1000) });
                    e.Start(); var enemy = Foe(e, "charger"); var hero = e.ActiveHero;
                    Planned(e)[enemy.Id] = new List<BattleAction>();
                    Pending(e, db, enemy, e.Round - 1, hero.Id);
                    Silence(db, enemy, status); enemy.Statuses.Single().TurnsRemaining = duration;
                    enemy.ApplyStatus(BattleStatus.FromDef(new StatusDef { Id = "spd", EffectType = StatusEffectType.SpeedUp, Magnitude = 1f, DurationTurns = 3 }, ""));
                    // Speed tie at1000 favours party, so use a slowed hero for next-round ordering without changing this fixed queue.
                    hero.ApplyStatus(BattleStatus.FromDef(new StatusDef { Id = "slow", EffectType = StatusEffectType.Slow, Magnitude = 0.5f, DurationTurns = 3 }, ""));
                    hero.Hp = 900;
                    string rng = RngState(e.Rng);
                    Assert.Equal(duration == 1, (bool)Call(e, "ShouldGuardThreat", hero), status + duration + ": current skipped turn ticks1; next-round slot0 releases only after recovery");
                    Assert.True(enemy.PendingCharge != null && enemy.Statuses.First(x => x.Id == status).TurnsRemaining == duration && RngState(e.Rng) == rng, "query leaves charge, CC and RNG unchanged");
                }
            // Enemy already acted this round: no extra CC tick is available before next-round release.
            var d = Db(); var f = Engine(d, 4, new[] { "charger_fast" }, new[] { Hero("h0", 1000) });
            f.Start(); var fast = Foe(f, "charger_fast"); Silence(d, fast, "stun");
            Assert.True(!(bool)Call(f, "ShouldGuardThreat", f.ActiveHero), "already acted, duration1 still delays next-round release");
        }

        [LogicTest]
        public static void ForecastExpiryAndSkippedChargeQueriesPreservePairedFutureStreams()
        {
            var db = Db();
            BattleEngine Make()
            {
                var e = Engine(db, 4, new[] { "charger" }, Trio()); e.Start(); FinishRound(e);
                var enemy = Foe(e, "charger"); Silence(db, enemy, "stun"); enemy.Statuses.Single().TurnsRemaining = 2;
                e.Party[0].ApplyStatus(BattleStatus.FromDef(new StatusDef { Id = "def", EffectType = StatusEffectType.DefenseUp, Magnitude = 1f, DurationTurns = 1 }, ""));
                e.Party[1].ApplyStatus(BattleStatus.FromDef(new StatusDef { Id = "bar", EffectType = StatusEffectType.Barrier, AbsorbAmount = 1500, DurationTurns = 1 }, ""));
                return e;
            }
            var queried = Make(); var control = Make(); string rng = RngState(queried.Rng);
            var pending = Foe(queried, "charger").PendingCharge;
            for (int i = 0; i < 10; i++)
            {
                queried.SuggestCommand(queried.ActiveHero);
                Call(queried, "ShouldGuardThreat", queried.ActiveHero);
                Call(queried, "SuggestThreatHeal", queried.ActiveHero, new List<SkillDef> { db.Skills["heal"] }, queried.Party.ToList());
            }
            Assert.Equal(rng, RngState(queried.Rng), "no forecasting draws");
            Assert.True(ReferenceEquals(pending, Foe(queried, "charger").PendingCharge) && queried.Party[0].Statuses.Single().TurnsRemaining == 1
                && queried.Party[1].Statuses.Single().BarrierRemaining == 1500, "no charge/status mutation");
            for (int i = 0; i < 9; i++)
            {
                var a = queried.Submit(BattleCommand.Guard()); var b = control.Submit(BattleCommand.Guard());
                Assert.Equal(string.Join("\n", a.Select(BattleTestUtil.Describe)), string.Join("\n", b.Select(BattleTestUtil.Describe)), "paired future expiry/CC/release events");
                Assert.Equal(RngState(control.Rng), RngState(queried.Rng), "paired future RNG");
            }
        }

    }
}
