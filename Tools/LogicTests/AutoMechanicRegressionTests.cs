// AUTO's charge-break and execute estimates: shield crushers (SkillDef.BreakPower) and execute skills
// (ExecuteBelow / ExecuteMult) are counted without leaking hidden enemy weaknesses.
using System;
using System.Collections.Generic;
using System.Linq;
using System.Reflection;
using Abyss.Logic;
using Abyss.Logic.Battle;

namespace Abyss.LogicTests
{
    public static class AutoMechanicRegressionTests
    {
        const int Slash = (int)Element.Slash;
        const BindingFlags Inst = BindingFlags.Instance | BindingFlags.NonPublic;

        // --- fixtures ------------------------------------------------------------------------------------

        static HeroCombatSpec Hero(string id, int speed, int attackElement, int mp, params string[] skills) => new HeroCombatSpec
        {
            HeroId = id, DisplayName = id, Level = 10, MaxHp = 1000, Hp = 1000, MaxMp = 500, Mp = mp, AttackElement = attackElement,
            Attack = 200, Magic = 150, Defense = 5, Resistance = 5, Speed = speed, Hit = 2, Crit = 0,
            Skills = skills.ToList(),
        };

        static HeroCombatSpec Hero(string id, int speed, params string[] skills) => Hero(id, speed, 0, 500, skills);

        static SkillDef Sk(string id, Element element, int hits = 1, int breakPower = 0, Scope scope = Scope.Single, int mp = 0,
            float power = 1f, float executeBelow = 0f, float executeMult = 1f) => new SkillDef
        {
            Id = id, DisplayName = id, Kind = SkillKind.Damage, Element = element, Scope = scope, HitCount = hits, BreakPower = breakPower,
            ScalingStat = ScalingStat.Attack, TargetType = TargetType.Enemy, Power = power, MpCost = mp,
            ExecuteBelow = executeBelow, ExecuteMult = executeMult,
        };

        static EnemyDef Enemy(string id, int hp = 100000, bool boss = false, int shield = 0, string charge = "", params int[] weak)
        {
            var def = new EnemyDef
            {
                Id = id, DisplayName = id, MaxHp = hp, MaxMp = 100, Attack = 5, Magic = 5, Defense = 20, Resistance = 10,
                Speed = 1, Hit = 1, Evade = 0, BreakShield = shield, IsBoss = boss, Rank = boss ? 2 : 0, ActionsPerTurn = 1,
                AiProfile = "basic", ChargeSkill = charge,
            };
            def.Weaknesses.AddRange(weak);
            def.Skills.Add(boss ? "big" : "small");
            def.SkillWeights.Add(1);
            return def;
        }

        /// <summary>Fresh DB: a charging boss with a Slash weakness, a plain grunt, and weak / non-weak dummies with identical stats.</summary>
        static GameDB Db(int shield = 2)
        {
            var db = new GameDB();
            foreach (var s in new[]
            {
                Sk("big", Element.Fire, power: 2f),
                Sk("small", Element.None),
            }) db.Skills.Add(s.Id, s);
            db.Skills["big"].ScalingStat = ScalingStat.Magic;
            foreach (var e in new[]
            {
                Enemy("boss", boss: true, shield: shield, charge: "big", weak: Slash),
                Enemy("grunt"),
                Enemy("dummy", hp: 10000),
                Enemy("dummy_weak", hp: 10000, weak: Slash),
            }) db.Enemies.Add(e.Id, e);
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

        static BattleUnit Foe(BattleEngine e, string defId) => e.Enemies.First(u => u.DefId == defId);

        static Dictionary<string, List<BattleAction>> Planned(BattleEngine e)
            => (Dictionary<string, List<BattleAction>>)typeof(BattleEngine).GetField("_planned", Inst).GetValue(e);

        /// <summary>Engine with a boss that has just announced a charge (all remaining party turns come before the release).</summary>
        static BattleEngine Charging(GameDB db, string[] enemies, HeroCombatSpec[] heroes, bool knownSlash)
        {
            var e = Engine(db, 4, enemies, heroes, knownSlash ? new[] { "boss:" + Slash } : new string[0]);
            e.Start();
            var boss = Foe(e, "boss");
            Planned(e)[boss.Id] = new List<BattleAction>();
            boss.PendingCharge = new PendingCharge("big", null, e.Round, Scope.All);
            boss.PendingChargeSkill = db.Skills["big"];
            return e;
        }

        static BattleCommand Break(BattleEngine e)
            => (BattleCommand)typeof(BattleEngine).GetMethod("SuggestChargeBreak", Inst).Invoke(e, new object[] { e.ActiveHero });

        static (BattleCommand Command, int Points) Best(BattleEngine e, BattleUnit actor, BattleUnit enemy)
        {
            var args = new object[] { actor, enemy, 0 };
            var cmd = (BattleCommand)typeof(BattleEngine).GetMethod("BestWeakAction", Inst).Invoke(e, args);
            return (cmd, (int)args[2]);
        }

        static double Hit(BattleEngine e, BattleUnit unit, BattleUnit target, SkillDef skill)
            => (double)typeof(BattleEngine).GetMethod("ExpectedHit", Inst).Invoke(e, new object[] { unit, target, skill });

        static string RngState(GodotRng rng)
            => string.Join(",", typeof(GodotRng).GetFields(BindingFlags.Instance | BindingFlags.NonPublic).Select(f => f.GetValue(rng).ToString()));

        // --- charge-break shield contribution ------------------------------------------------------------

        [LogicTest]
        public static void KnownWeakBreakPowerSkillStacksBothShieldPointsPerHit()
        {
            var db = Db(2);
            db.Skills["wk"] = Sk("wk", Element.Slash, breakPower: 1);
            db.Skills["plain_slash"] = Sk("plain_slash", Element.Slash);
            var e = Charging(db, new[] { "boss" }, new[] { Hero("h0", 1000, "wk") }, true);
            var boss = Foe(e, "boss");
            var best = Best(e, e.ActiveHero, boss);
            Assert.Equal(2, best.Points, "known weak (1) + BreakPower (1) per hit");
            var cmd = Break(e);
            Assert.True(cmd != null && cmd.Kind == CommandKind.Skill && cmd.SkillId == "wk" && cmd.TargetId == boss.Id, "one hit empties shield 2: " + cmd);
            boss.Shield = 3;
            Assert.True(Break(e) == null, "2 points cannot empty shield 3");

            // A pure weakness hit is still just one point (existing behavior preserved).
            var f = Charging(db, new[] { "boss" }, new[] { Hero("h0", 1000, "plain_slash") }, true);
            Assert.Equal(1, Best(f, f.ActiveHero, Foe(f, "boss")).Points, "known weakness without BreakPower is one point");
            Assert.True(Break(f) == null, "one point cannot empty shield 2");
        }

        [LogicTest]
        public static void UnknownAndNeutralBreakPowerCountsWhileHiddenWeaknessAddsNothing()
        {
            var db = Db(1);
            db.Skills["crush_none"] = Sk("crush_none", Element.None, breakPower: 1);
            db.Skills["crush_slash"] = Sk("crush_slash", Element.Slash, breakPower: 1);
            db.Skills["slash_only"] = Sk("slash_only", Element.Slash);
            db.Skills["negative"] = Sk("negative", Element.None, breakPower: -5);

            // Neutral element, no knowledge needed: BreakPower alone empties shield 1.
            var e = Charging(db, new[] { "boss" }, new[] { Hero("h0", 1000, "crush_none") }, false);
            Assert.Equal(1, Best(e, e.ActiveHero, Foe(e, "boss")).Points, "neutral BreakPower counts");
            var cmd = Break(e);
            Assert.True(cmd != null && cmd.SkillId == "crush_none", "neutral crusher breaks shield 1 without knowing any weakness");

            // Slash is a hidden weakness of the boss: unknown affinity contributes only BreakPower.
            db.Enemies["boss"].BreakShield = 2;
            e = Charging(db, new[] { "boss" }, new[] { Hero("h0", 1000, "crush_slash") }, false);
            Assert.Equal(PreviewAffinity.Unknown, e.KnownAffinity(Foe(e, "boss"), Slash), "weakness stays hidden");
            Assert.Equal(1, Best(e, e.ActiveHero, Foe(e, "boss")).Points, "hidden weakness gives no extra point");
            Assert.True(Break(e) == null, "1 point against shield 2: AUTO must not act on the hidden weakness");
            e = Charging(db, new[] { "boss" }, new[] { Hero("h0", 1000, "crush_slash") }, true);
            Assert.Equal(2, Best(e, e.ActiveHero, Foe(e, "boss")).Points, "once known, the weakness adds its point");
            Assert.True(Break(e) != null, "known weakness + BreakPower empties shield 2");

            // No BreakPower, unknown affinity: nothing to contribute. Negative BreakPower is clamped to zero.
            e = Charging(db, new[] { "boss" }, new[] { Hero("h0", 1000, "slash_only", "negative") }, false);
            var none = Best(e, e.ActiveHero, Foe(e, "boss"));
            Assert.True(none.Command == null && none.Points == 0, "unknown weakness without BreakPower contributes nothing");
            e = Charging(db, new[] { "boss" }, new[] { Hero("h0", 1000, "negative") }, true);
            none = Best(e, e.ActiveHero, Foe(e, "boss"));
            Assert.True(none.Command == null && none.Points == 0, "negative BreakPower is never a contribution");
        }

        [LogicTest]
        public static void ShieldContributionMultipliesByHitCountAndClampsToIntMax()
        {
            var db = Db(6);
            db.Skills["multi"] = Sk("multi", Element.None, hits: 3, breakPower: 2);
            db.Skills["multi_weak"] = Sk("multi_weak", Element.Slash, hits: 3, breakPower: 1);
            db.Skills["zero_hits"] = Sk("zero_hits", Element.None, hits: 0, breakPower: 3);
            db.Skills["huge"] = Sk("huge", Element.None, hits: int.MaxValue, breakPower: int.MaxValue);

            var e = Charging(db, new[] { "boss" }, new[] { Hero("h0", 1000, "multi") }, false);
            Assert.Equal(6, Best(e, e.ActiveHero, Foe(e, "boss")).Points, "3 hits x BreakPower 2");
            Assert.True(Break(e) != null, "6 points empty shield 6");
            Foe(e, "boss").Shield = 7;
            Assert.True(Break(e) == null, "6 points cannot empty shield 7");

            e = Charging(db, new[] { "boss" }, new[] { Hero("h0", 1000, "multi_weak") }, true);
            Assert.Equal(6, Best(e, e.ActiveHero, Foe(e, "boss")).Points, "3 hits x (known weak 1 + BreakPower 1)");

            e = Charging(db, new[] { "boss" }, new[] { Hero("h0", 1000, "zero_hits") }, false);
            Assert.Equal(3, Best(e, e.ActiveHero, Foe(e, "boss")).Points, "HitCount below 1 counts as one hit");

            e = Charging(db, new[] { "boss" }, new[] { Hero("h0", 1000, "huge") }, false);
            Foe(e, "boss").Shield = 1000;
            Assert.Equal(int.MaxValue, Best(e, e.ActiveHero, Foe(e, "boss")).Points, "long product clamps to int.MaxValue");
            Assert.True(Break(e) != null, "clamped contribution still breaks a large shield");
        }

        [LogicTest]
        public static void RandomScopeCrusherNeedsTheChargerAsSoleValidTarget()
        {
            var db = Db(2);
            db.Skills["rand_crush"] = Sk("rand_crush", Element.None, hits: 2, breakPower: 1, scope: Scope.Random);
            var e = Charging(db, new[] { "boss", "grunt" }, new[] { Hero("h0", 1000, "rand_crush") }, false);
            Assert.True(Best(e, e.ActiveHero, Foe(e, "boss")).Command == null, "random hits are not guaranteed with two enemies");
            Assert.True(Break(e) == null, "no speculative RANDOM targeting");
            e = Charging(db, new[] { "boss" }, new[] { Hero("h0", 1000, "rand_crush") }, false);
            var best = Best(e, e.ActiveHero, Foe(e, "boss"));
            Assert.True(best.Command != null && best.Command.SkillId == "rand_crush" && best.Command.TargetId == null && best.Points == 2, "sole candidate: every random hit lands");
            var cmd = Break(e);
            Assert.True(cmd != null && cmd.SkillId == "rand_crush" && cmd.TargetId == null, "sole-target random crusher is a valid interrupt");
        }

        [LogicTest]
        public static void UnaffordableCrusherIsExcluded()
        {
            var db = Db(2);
            db.Skills["costly"] = Sk("costly", Element.None, hits: 2, breakPower: 1, mp: 50);
            var e = Charging(db, new[] { "boss" }, new[] { Hero("h0", 1000, 0, 49, "costly") }, false);
            var none = Best(e, e.ActiveHero, Foe(e, "boss"));
            Assert.True(none.Command == null && none.Points == 0, "49 MP cannot pay for a 50 MP crusher");
            Assert.True(Break(e) == null, "no interrupt from an unaffordable skill");
            e = Charging(db, new[] { "boss" }, new[] { Hero("h0", 1000, 0, 50, "costly") }, false);
            Assert.Equal(2, Best(e, e.ActiveHero, Foe(e, "boss")).Points, "exactly affordable counts");
            Assert.True(Break(e) != null, "affordable crusher interrupts");
        }

        [LogicTest]
        public static void EqualShieldContributionTiesStayWithAttackThenLearnOrder()
        {
            var db = Db(5);
            db.Skills["one_weak"] = Sk("one_weak", Element.Slash);
            db.Skills["a2"] = Sk("a2", Element.None, hits: 2, breakPower: 1);
            db.Skills["b2"] = Sk("b2", Element.None, hits: 1, breakPower: 2);
            db.Skills["c4"] = Sk("c4", Element.None, hits: 2, breakPower: 2);

            // Basic attack (known weak) = 1 point; a skill with the same single point does not displace it.
            var e = Charging(db, new[] { "boss" }, new[] { Hero("h0", 1000, Slash, 500, "one_weak") }, true);
            var best = Best(e, e.ActiveHero, Foe(e, "boss"));
            Assert.True(best.Command.Kind == CommandKind.Attack && best.Points == 1, "attack wins an equal tie: " + best.Command);

            // A strictly better skill displaces the attack.
            e = Charging(db, new[] { "boss" }, new[] { Hero("h0", 1000, Slash, 500, "a2") }, true);
            best = Best(e, e.ActiveHero, Foe(e, "boss"));
            Assert.True(best.Command.Kind == CommandKind.Skill && best.Command.SkillId == "a2" && best.Points == 2, "2 points beat the attack's 1");

            // Equal skills keep learn order; a strictly larger later one wins.
            e = Charging(db, new[] { "boss" }, new[] { Hero("h0", 1000, "a2", "b2") }, false);
            Assert.Equal("a2", Best(e, e.ActiveHero, Foe(e, "boss")).Command.SkillId, "learn-order tie: first skill stays");
            e = Charging(db, new[] { "boss" }, new[] { Hero("h0", 1000, "b2", "a2") }, false);
            Assert.Equal("b2", Best(e, e.ActiveHero, Foe(e, "boss")).Command.SkillId, "learn-order tie, reversed");
            e = Charging(db, new[] { "boss" }, new[] { Hero("h0", 1000, "a2", "b2", "c4") }, false);
            var big = Best(e, e.ActiveHero, Foe(e, "boss"));
            Assert.True(big.Command.SkillId == "c4" && big.Points == 4, "strictly greater later skill wins");
        }

        [LogicTest]
        public static void PublicAutoInterruptsAChargeWithAnUnknownAffinityCrusherAndDrawsNothing()
        {
            var db = Db(2);
            db.Skills["crush2"] = Sk("crush2", Element.None, hits: 2, breakPower: 1);
            db.Skills["strong"] = Sk("strong", Element.None, power: 3f);
            var e = Charging(db, new[] { "boss", "grunt" }, new[] { Hero("h0", 1000, "strong", "crush2") }, false);
            var boss = Foe(e, "boss");
            string rng = RngState(e.Rng);
            var cmd = e.SuggestCommand(e.ActiveHero);
            Assert.True(cmd.Kind == CommandKind.Skill && cmd.SkillId == "crush2" && cmd.TargetId == boss.Id, "AUTO interrupts the charge with the crusher: " + cmd);
            Assert.Equal(rng, RngState(e.Rng), "AUTO draws nothing");

            // The shield is now larger than the lone hero can remove: no break trigger, normal scoring resumes.
            boss.Shield = 3;
            cmd = e.SuggestCommand(e.ActiveHero);
            Assert.True(Break(e) == null && cmd.SkillId != "crush2", "no break trigger when the shield cannot be emptied: " + cmd);

            // A later, slower ally's crusher counts toward the total.
            e = Charging(db, new[] { "boss" }, new[] { Hero("h0", 1000, "crush2"), Hero("h1", 999, "crush2") }, false);
            Foe(e, "boss").Shield = 4;
            cmd = e.SuggestCommand(e.ActiveHero);
            Assert.True(cmd.SkillId == "crush2" && cmd.TargetId == Foe(e, "boss").Id, "2 + ally's 2 empties shield 4: " + cmd);
            Foe(e, "boss").Shield = 5;
            Assert.True(Break(e) == null, "2 + 2 cannot empty shield 5");
        }

        // --- execute in AUTO's expected damage ----------------------------------------------------------

        [LogicTest]
        public static void ExpectedHitAppliesExecuteMultiplierExactlyAtAndBelowThreshold()
        {
            var db = Db();
            db.Skills["plain"] = Sk("plain", Element.None);
            db.Skills["exec"] = Sk("exec", Element.None, executeBelow: 0.5f, executeMult: 3f);
            db.Skills["never"] = Sk("never", Element.None, executeBelow: 0f, executeMult: 9f);
            db.Skills["zeroed"] = Sk("zeroed", Element.None, executeBelow: 0.5f, executeMult: -2f);
            var e = Engine(db, 4, new[] { "dummy" }, new[] { Hero("h0", 1000, "plain", "exec") });
            e.Start();
            var hero = e.ActiveHero; var dummy = Foe(e, "dummy");
            Assert.Equal(10000, dummy.MaxHp, "fixture MaxHp");
            double baseline = Hit(e, hero, dummy, db.Skills["plain"]);
            Assert.True(baseline > 1, "baseline hit is meaningful");

            dummy.Hp = 5001;
            Assert.Near(baseline, Hit(e, hero, dummy, db.Skills["exec"]), 1e-9, "above threshold: no multiplier");
            dummy.Hp = 5000;
            Assert.Near(baseline * 3, Hit(e, hero, dummy, db.Skills["exec"]), 1e-9, "exactly at threshold: multiplier applies");
            dummy.Hp = 4999;
            Assert.Near(baseline * 3, Hit(e, hero, dummy, db.Skills["exec"]), 1e-9, "below threshold: multiplier applies");
            dummy.Hp = 1;
            Assert.Near(baseline, Hit(e, hero, dummy, db.Skills["never"]), 1e-9, "ExecuteBelow 0 is never an execute");
            Assert.Near(0.0, Hit(e, hero, dummy, db.Skills["zeroed"]), 1e-9, "negative ExecuteMult clamps to zero damage");

            // Null skill = basic attack: no execute, and the hit does not depend on HP.
            dummy.Hp = 10000; double basic = Hit(e, hero, dummy, null);
            dummy.Hp = 1;
            Assert.Near(basic, Hit(e, hero, dummy, null), 1e-9, "basic attack is not an execute");
            Assert.True(basic > 0, "basic attack estimate is positive");
        }

        [LogicTest]
        public static void HiddenWeaknessNeverChangesExpectedHitButKnownWeaknessDoes()
        {
            var db = Db();
            db.Skills["slash1"] = Sk("slash1", Element.Slash);
            var e = Engine(db, 4, new[] { "dummy", "dummy_weak" }, new[] { Hero("h0", 1000, "slash1") });
            e.Start();
            var hero = e.ActiveHero; var plain = Foe(e, "dummy"); var weak = Foe(e, "dummy_weak");
            Assert.Equal(PreviewAffinity.Unknown, e.KnownAffinity(weak, Slash), "unknown stays unknown");
            Assert.Near(Hit(e, hero, plain, db.Skills["slash1"]), Hit(e, hero, weak, db.Skills["slash1"]), 1e-9, "hidden weakness leaks nothing into the estimate");
            var f = Engine(db, 4, new[] { "dummy", "dummy_weak" }, new[] { Hero("h0", 1000, "slash1") }, "dummy_weak:" + Slash);
            f.Start();
            Assert.True(Hit(f, f.ActiveHero, Foe(f, "dummy_weak"), db.Skills["slash1"]) > Hit(f, f.ActiveHero, Foe(f, "dummy"), db.Skills["slash1"]) * 1.1,
                "known weakness raises the estimate");
        }

        [LogicTest]
        public static void PublicAutoPicksTheExecuteFinisherOnlyWhileTheTargetIsInExecuteRange()
        {
            var db = Db();
            db.Skills["heavy"] = Sk("heavy", Element.None, power: 2f);
            db.Skills["finisher"] = Sk("finisher", Element.None, power: 1f, executeBelow: 0.5f, executeMult: 4f);
            BattleCommand Choose(int hp)
            {
                var e = Engine(db, 4, new[] { "dummy" }, new[] { Hero("h0", 1000, "heavy", "finisher") });
                e.Start();
                Foe(e, "dummy").Hp = hp;
                return e.SuggestCommand(e.ActiveHero);
            }
            Assert.Equal("heavy", Choose(6000).SkillId, "above the execute threshold the 2x skill is better");
            Assert.Equal("finisher", Choose(3000).SkillId, "inside execute range 4x beats 2x");
            Assert.Equal("finisher", Choose(5000).SkillId, "exactly at the threshold the finisher is already chosen");
        }

        // --- state-free queries --------------------------------------------------------------------------

        [LogicTest]
        public static void BreakAndExecuteQueriesDoNotMutateStateOrConsumeRng()
        {
            var db = Db(2);
            db.Skills["crush2"] = Sk("crush2", Element.None, hits: 2, breakPower: 1);
            db.Skills["finisher"] = Sk("finisher", Element.None, executeBelow: 0.5f, executeMult: 4f);
            BattleEngine Make()
            {
                var e = Charging(db, new[] { "boss", "grunt" }, new[] { Hero("h0", 1000, "crush2", "finisher"), Hero("h1", 999, "crush2") }, false);
                Foe(e, "grunt").Hp = 1000;
                return e;
            }
            var queried = Make(); var control = Make();
            string rng = RngState(queried.Rng);
            for (int i = 0; i < 10; i++)
                foreach (var hero in queried.Party)
                {
                    queried.SuggestCommand(hero);
                    foreach (var foe in queried.Enemies)
                    {
                        Best(queried, hero, foe);
                        foreach (var skill in new[] { db.Skills["crush2"], db.Skills["finisher"], null }) Hit(queried, hero, foe, skill);
                    }
                    Break(queried);
                }
            Assert.Equal(rng, RngState(queried.Rng), "queries draw nothing");
            Assert.Equal(Foe(control, "boss").Shield, Foe(queried, "boss").Shield, "shield untouched");
            for (int turn = 0; turn < 4 && queried.State == BattleEngineState.AwaitingCommand; turn++)
            {
                var a = queried.Submit(BattleCommand.Attack(Foe(queried, "grunt").Id));
                var b = control.Submit(BattleCommand.Attack(Foe(control, "grunt").Id));
                Assert.Equal(string.Join("\n", a.Select(BattleTestUtil.Describe)), string.Join("\n", b.Select(BattleTestUtil.Describe)), "paired future events");
                Assert.Equal(RngState(control.Rng), RngState(queried.Rng), "paired future RNG");
            }
        }
    }
}
