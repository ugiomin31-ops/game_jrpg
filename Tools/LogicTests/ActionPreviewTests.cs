// O2 action previews (knowledge-safe, RNG-free) and display-only enemy labels.
using System;
using System.Collections;
using System.Collections.Generic;
using System.Linq;
using System.Reflection;
using System.Text;
using Abyss.Logic;
using Abyss.Logic.Battle;

namespace Abyss.LogicTests
{
    public static class ActionPreviewTests
    {
        const int Slash = (int)Element.Slash, Fire = (int)Element.Fire, Ice = (int)Element.Ice;

        static HeroCombatSpec Hero(string id, int hp = 1000, params string[] skills) => new HeroCombatSpec
        {
            HeroId = id, DisplayName = id, Level = 10, MaxHp = 1000, Hp = hp, MaxMp = 500, Mp = 500,
            Attack = 200, Magic = 150, Defense = 5, Resistance = 5, Speed = 1000, Hit = 2, Crit = 0, Skills = skills.ToList(),
        };

        static SkillDef Skill(string id, SkillKind kind, Element element, Scope scope = Scope.Single, int hits = 1,
            ScalingStat stat = ScalingStat.Attack, TargetType target = TargetType.Enemy, int mp = 5) => new SkillDef
        {
            Id = id, DisplayName = id, Kind = kind, Element = element, Scope = scope, HitCount = hits, ScalingStat = stat,
            TargetType = target, Power = 1f, MpCost = mp,
        };

        /// <summary>Golem: weak Slash, resists Fire, shield 2. Wisp: weak Ice. Mother summons golems / wisps.</summary>
        static GameDB Db()
        {
            var db = new GameDB();
            db.Enemies.Add("golem", new EnemyDef { Id = "golem", DisplayName = "Golem", MaxHp = 100000, Attack = 5, Magic = 5, Defense = 20, Resistance = 10,
                Speed = 1, Hit = 1, Evade = 0, BreakShield = 2, Weaknesses = { Slash }, Resistances = { Fire } });
            db.Enemies.Add("wisp", new EnemyDef { Id = "wisp", DisplayName = "Wisp", MaxHp = 100000, Attack = 5, Magic = 5, Defense = 10, Resistance = 10,
                Speed = 1, Hit = 1, Evade = 0, BreakShield = 3, Weaknesses = { Ice } });
            db.Enemies.Add("mother", new EnemyDef { Id = "mother", DisplayName = "Mother", MaxHp = 100000, Attack = 5, Magic = 5, Defense = 10, Resistance = 10,
                Speed = 1, Hit = 1, Evade = 0, Summons = { "golem", "wisp" }, SummonLimit = 4 });
            foreach (var s in new[]
            {
                Skill("slash3", SkillKind.Damage, Element.Slash, hits: 3),
                Skill("fire_all", SkillKind.Damage, Element.Fire, Scope.All, stat: ScalingStat.Magic),
                Skill("ice_rand", SkillKind.Damage, Element.Ice, Scope.Random, hits: 4, stat: ScalingStat.Magic),
                Skill("plain", SkillKind.Damage, Element.None),
                Skill("heal", SkillKind.Heal, Element.None, stat: ScalingStat.Magic, target: TargetType.Ally),
                Skill("buff", SkillKind.Buff, Element.None, target: TargetType.Self),
            }) db.Skills.Add(s.Id, s);
            db.Items.Add("bomb", new ItemDef { Id = "bomb", DisplayName = "Bomb", ItemType = ItemType.Damage, Value = 100, Element = Element.Fire, Target = "all_enemies" });
            db.Items.Add("potion", new ItemDef { Id = "potion", DisplayName = "Potion", ItemType = ItemType.Healing, HealAmount = 120, Target = "single_ally" });
            db.Items.Add("ether", new ItemDef { Id = "ether", DisplayName = "Ether", ItemType = ItemType.MpRestore, Value = 50, Target = "single_ally" });
            foreach (var st in TestMain.DB.Statuses) db.Statuses.Add(st.Key, st.Value);
            db.Statuses["test_barrier"] = new StatusDef { Id = "test_barrier", DisplayName = "Barrier", EffectType = StatusEffectType.Barrier, AbsorbAmount = 300, DurationTurns = 3 };
            db.Text["break"] = "%s BREAK!";
            return db;
        }

        static readonly string[] AllSkills = { "slash3", "fire_all", "ice_rand", "plain", "heal", "buff" };

        static BattleEngine Engine(int seed, IEnumerable<string> enemies, IEnumerable<string> known = null, GameDB db = null, int heroes = 2)
        {
            var setup = new BattleSetup { Seed = seed };
            for (int i = 0; i < heroes; i++) setup.Party.Add(Hero("hero" + i, 1000, AllSkills));
            setup.EnemyGroup.AddRange(enemies);
            if (known != null) foreach (var k in known) setup.KnownWeaknesses.Add(k);
            setup.Inventory["bomb"] = 3; setup.Inventory["potion"] = 3; setup.Inventory["ether"] = 3;
            var engine = new BattleEngine(db ?? Db(), setup);
            engine.Start();
            Assert.Equal(BattleEngineState.AwaitingCommand, engine.State, "a hero awaits a command");
            return engine;
        }

        static ActionPreview Preview(BattleEngine e, BattleCommand cmd, BattleUnit target)
            => e.PreviewAction(e.UnitIndexOf(e.ActiveHero), cmd, target == null ? -1 : e.UnitIndexOf(target));

        static int DamageTo(IEnumerable<BattleEvent> events, string id) => events.OfType<DamageEvent>().Where(d => d.TargetId == id && d.Type != DamageType.Status).Sum(d => d.Amount);

        // --- estimates ---------------------------------------------------------------------------------

        [LogicTest]
        public static void UnknownAffinityUsesNeutralNumbersAndNeverLeaks()
        {
            var e = Engine(1, new[] { "golem", "wisp" });
            var golem = e.Enemies[0];
            var slash = Preview(e, BattleCommand.Skill("slash3"), golem).Targets.Single();
            Assert.Equal(PreviewAffinity.Unknown, slash.Affinity, "undiscovered weakness stays Unknown");
            // base 200 - 20 x 0.55 = 189; neutral hit 174..204 (x3), no shield walk, no break.
            Assert.Equal(522, slash.Min, "unknown min uses the neutral multiplier");
            Assert.Equal(612, slash.Max, "unknown max uses the neutral multiplier");
            Assert.Equal(0, slash.ShieldDamage, "unknown affinity removes no shield in the estimate");
            Assert.True(!slash.Breaks, "no break modelled without knowledge");
            var fire = Preview(e, BattleCommand.Skill("fire_all"), null);
            Assert.Equal(PreviewAffinity.Unknown, fire.For(golem.Id).Affinity, "undiscovered resistance stays Unknown");
            var neutralFire = fire.For(golem.Id);
            Assert.True(neutralFire.Min >= 120, "unknown resist is not halved: " + neutralFire.Min);
            Assert.Equal(SkillAffinityTag.None, e.KnownSkillAffinity(e.ActiveHero, e.ActiveHero.Skills.First(s => s.Id == "slash3")), "no weak tag before discovery");
            Assert.Equal(SkillAffinityTag.None, e.KnownSkillAffinity(e.ActiveHero, e.ActiveHero.Skills.First(s => s.Id == "fire_all")), "no resist tag before observation");
            var plain = Preview(e, BattleCommand.Skill("plain"), golem).Targets.Single();
            Assert.Equal(PreviewAffinity.Neutral, plain.Affinity, "non-elemental hits are Neutral");

            // Observation this battle: Fire resisted -> Resist; Ice on golem lands neutral -> Neutral.
            e.Submit(BattleCommand.Skill("fire_all"));
            Assert.Equal(PreviewAffinity.Resist, e.KnownAffinity(golem, Fire), "resist seen this battle");
            var resisted = Preview(e, BattleCommand.Skill("fire_all"), null).For(golem.Id);
            Assert.Equal(PreviewAffinity.Resist, resisted.Affinity, "preview uses the observed resistance");
            Assert.True(resisted.Max < neutralFire.Min, "resisted estimate is lower than the neutral one");
            Assert.Equal(SkillAffinityTag.Resist, e.KnownSkillAffinity(e.ActiveHero, e.ActiveHero.Skills.First(s => s.Id == "fire_all")), "resist tag after observation");
            Assert.Equal(PreviewAffinity.Unknown, e.KnownAffinity(golem, Ice), "ice still unknown on golem");
        }

        [LogicTest]
        public static void KnownWeaknessWalksTheShieldIntoBreak()
        {
            var e = Engine(2, new[] { "golem" }, new[] { "golem:" + Slash });
            var golem = e.Enemies[0];
            var p = Preview(e, BattleCommand.Skill("slash3"), golem);
            var t = p.Targets.Single();
            Assert.Equal(PreviewKind.Damage, p.Kind, "damage kind");
            Assert.Equal(3, p.HitCount, "three hits");
            Assert.Equal(PreviewAffinity.Weak, t.Affinity, "bestiary weakness is known");
            // Weak hits 261..306 twice, then the shield (2) is empty: third hit x BREAK 391..459.
            Assert.Equal(261 + 261 + 391, t.Min, "mid-action break min");
            Assert.Equal(306 + 306 + 459, t.Max, "mid-action break max");
            Assert.Equal(2, t.ShieldDamage, "known-weak hits capped at the shield");
            Assert.True(t.Breaks, "known weak hits break the shield");
            Assert.True(!t.Lethal && !t.Shielded, "not lethal, no barrier");
            Assert.Equal(SkillAffinityTag.Weak, e.KnownSkillAffinity(e.ActiveHero, e.ActiveHero.Skills.First(s => s.Id == "slash3")), "weak tag");

            golem.Hp = 913;
            Assert.True(Preview(e, BattleCommand.Skill("slash3"), golem).Targets[0].Lethal, "min total >= HP is lethal");
            golem.Hp = 914;
            Assert.True(!Preview(e, BattleCommand.Skill("slash3"), golem).Targets[0].Lethal, "min total < HP is not lethal");
            golem.Hp = golem.MaxHp;

            golem.Shield = 5;
            var noBreak = Preview(e, BattleCommand.Skill("slash3"), golem).Targets[0];
            Assert.True(noBreak.ShieldDamage == 3 && !noBreak.Breaks && noBreak.Min == 3 * 261, "large shield: three weak hits, no break");
            golem.Shield = 2;
            golem.Broken = true;
            var broken = Preview(e, BattleCommand.Skill("slash3"), golem).Targets[0];
            Assert.True(broken.ShieldDamage == 0 && !broken.Breaks && broken.Min == 3 * 391, "already broken: every hit uses BREAK");
            golem.Broken = false;
        }

        /// <summary>When knowledge matches the truth (known weaknesses, truly neutral unknowns) every real non-crit roll is inside the range.</summary>
        [LogicTest]
        public static void PreviewRangesContainEveryRealRoll()
        {
            for (int seed = 1; seed <= 40; seed++)
            {
                var plain = Engine(seed, new[] { "golem" });
                var attack = Preview(plain, BattleCommand.Attack(null), plain.Enemies[0]).Targets[0];
                int hit = DamageTo(plain.Submit(BattleCommand.Attack(plain.Enemies[0].Id)), plain.Enemies[0].Id);
                Assert.True(attack.Affinity == PreviewAffinity.Neutral && hit >= attack.Min && hit <= attack.Max, $"seed {seed}: attack {hit} in {attack.Min}..{attack.Max}");
            }
            foreach (bool known in new[] { true })
                for (int seed = 1; seed <= 40; seed++)
                {
                    var e = Engine(seed, new[] { "golem", "wisp" }, known ? new[] { "golem:" + Slash, "wisp:" + Ice } : null);
                    var golem = e.Enemies[0];
                    var single = Preview(e, BattleCommand.Skill("slash3"), golem).Targets[0];
                    var events = e.Submit(BattleCommand.Skill("slash3", golem.Id));
                    int dealt = DamageTo(events, golem.Id);
                    Assert.True(dealt >= single.Min && dealt <= single.Max, $"seed {seed} known={known}: slash3 {dealt} in {single.Min}..{single.Max}");
                    Assert.Equal(single.Breaks, events.OfType<BreakEvent>().Any(b => b.UnitId == golem.Id), $"seed {seed}: break prediction matches");

                    var rnd = Preview(e, BattleCommand.Skill("ice_rand"), null);
                    string caster = e.ActiveHero.Id;
                    var ev2 = e.Submit(BattleCommand.Skill("ice_rand"));
                    foreach (var d in ev2.OfType<DamageEvent>().Where(d => d.SourceId == caster))
                    {
                        var row = rnd.For(d.TargetId);
                        Assert.True(row != null && d.Amount >= row.Min && d.Amount <= row.Max, $"seed {seed}: random hit {d.Amount} in {row?.Min}..{row?.Max}");
                    }
                }
        }

        [LogicTest]
        public static void AllAndRandomScopesReportPerTarget()
        {
            var e = Engine(3, new[] { "golem", "wisp" }, new[] { "wisp:" + Ice });
            var all = Preview(e, BattleCommand.Skill("fire_all"), null);
            Assert.Equal(2, all.Targets.Count, "one row per living enemy");
            Assert.True(!all.Random && all.HitCount == 1, "all scope is not random");
            Assert.Equal(2, e.PreviewAction(e.UnitIndexOf(e.ActiveHero), BattleCommand.Skill("fire_all"), 999).Targets.Count, "all scope ignores the target index");

            var rnd = Preview(e, BattleCommand.Skill("ice_rand"), null);
            Assert.True(rnd.Random && rnd.HitCount == 4 && rnd.Targets.Count == 2, "random scope: per-hit rows plus hit count");
            var wisp = rnd.For(e.Enemies[1].Id);
            var golem = rnd.For(e.Enemies[0].Id);
            Assert.Equal(PreviewAffinity.Weak, wisp.Affinity, "known ice weakness on wisp");
            Assert.Equal(PreviewAffinity.Unknown, golem.Affinity, "ice on golem unknown");
            Assert.True(!wisp.Lethal && !golem.Lethal, "random scope is never lethal");
            Assert.True(wisp.ShieldDamage == 0 && !wisp.Breaks, "random picks model no shield walk");
            e.Enemies[1].Hp = 1;
            Assert.True(!Preview(e, BattleCommand.Skill("ice_rand"), null).For(e.Enemies[1].Id).Lethal, "random never lethal even at 1 HP");
            e.Enemies[1].Hp = e.Enemies[1].MaxHp;

            var bomb = Preview(e, BattleCommand.Item("bomb"), null);
            Assert.True(bomb.Kind == PreviewKind.Damage && bomb.Targets.All(t => t.Min == 100 && t.Max == 100), "damage item: fixed value, neutral while unknown");
            var events = e.Submit(BattleCommand.Item("bomb"));
            Assert.Equal(50, DamageTo(events, e.Enemies[0].Id), "golem really resists the bomb");
            var after = Preview(e, BattleCommand.Item("bomb"), null).For(e.Enemies[0].Id);
            Assert.True(after.Affinity == PreviewAffinity.Resist && after.Min == 50, "resist observed by the item is used next time");
            Assert.Equal(PreviewAffinity.Neutral, e.KnownAffinity(e.Enemies[1], Fire), "fire landed neutral on wisp -> Neutral");
        }

        [LogicTest]
        public static void BarrierSetsShieldedAndKeepsPreAbsorptionRange()
        {
            var e = Engine(4, new[] { "golem" });
            var golem = e.Enemies[0];
            var before = Preview(e, BattleCommand.Attack(null), golem).Targets[0];
            Assert.True(!before.Shielded, "no barrier yet");
            golem.ApplyStatus(BattleStatus.FromDef(Db().Statuses["test_barrier"], golem.Id));
            var shielded = Preview(e, BattleCommand.Attack(null), golem).Targets[0];
            Assert.True(shielded.Shielded, "barrier flags the target");
            Assert.True(shielded.Min == before.Min && shielded.Max == before.Max, "range is HP damage before absorption");
            Assert.Equal(1, Preview(e, BattleCommand.Attack(null), golem).HitCount, "attack is one hit");
        }

        [LogicTest]
        public static void HealPreviewCoversRealHeals()
        {
            for (int seed = 1; seed <= 30; seed++)
            {
                var e = Engine(seed, new[] { "golem" });
                var ally = e.Party[1];
                ally.Hp = 10;
                var p = Preview(e, BattleCommand.Skill("heal"), ally);
                Assert.Equal(PreviewKind.Heal, p.Kind, "heal kind");
                var t = p.Targets.Single();
                Assert.True(!t.Lethal && !t.Shielded && t.ShieldDamage == 0, "heal has no damage flags");
                var events = e.Submit(BattleCommand.Skill("heal", ally.Id));
                int healed = events.OfType<HealEvent>().Where(h => h.TargetId == ally.Id).Sum(h => h.Amount);
                Assert.True(healed >= t.Min && healed <= t.Max, $"seed {seed}: heal {healed} in {t.Min}..{t.Max}");
            }
            var e2 = Engine(5, new[] { "golem" });
            var potion = Preview(e2, BattleCommand.Item("potion"), e2.Party[0]).Targets.Single();
            Assert.True(potion.Min == 120 && potion.Max == 120, "healing item: fixed amount");
        }

        [LogicTest]
        public static void InvalidInputsReturnNone()
        {
            var e = Engine(6, new[] { "golem", "wisp" });
            int actor = e.UnitIndexOf(e.ActiveHero), golem = e.UnitIndexOf(e.Enemies[0]);
            void None(ActionPreview p, string why) { Assert.True(ReferenceEquals(p, ActionPreview.None) && p.Kind == PreviewKind.None && p.Targets.Count == 0, why); }
            None(e.PreviewAction(-1, BattleCommand.Attack(null), golem), "negative actor index");
            None(e.PreviewAction(e.Units.Count, BattleCommand.Attack(null), golem), "actor index past the end");
            None(e.PreviewAction(golem, BattleCommand.Attack(null), actor), "enemy actor");
            None(e.PreviewAction(actor, null, golem), "null command");
            None(e.PreviewAction(actor, BattleCommand.Attack(null), -1), "single target without index");
            None(e.PreviewAction(actor, BattleCommand.Attack(null), e.Units.Count + 3), "target index past the end");
            None(e.PreviewAction(actor, BattleCommand.Attack(null), e.UnitIndexOf(e.Party[1])), "ally is not a valid attack target");
            None(e.PreviewAction(actor, BattleCommand.Skill("heal"), golem), "enemy is not a valid heal target");
            None(e.PreviewAction(actor, BattleCommand.Guard(), actor), "guard is not previewable");
            None(e.PreviewAction(actor, BattleCommand.Flee(), -1), "flee is not previewable");
            None(e.PreviewAction(actor, BattleCommand.Skill("buff"), actor), "buff is not previewable");
            None(e.PreviewAction(actor, BattleCommand.Skill("missing"), golem), "unknown skill");
            None(e.PreviewAction(actor, BattleCommand.Item("missing"), golem), "unknown item");
            None(e.PreviewAction(actor, BattleCommand.Item("ether"), actor), "MP item is not previewable");
            e.Enemies[0].Hp = 0;
            None(e.PreviewAction(actor, BattleCommand.Attack(null), golem), "dead target");
            e.Enemies[0].Hp = e.Enemies[0].MaxHp;
            var other = e.Party[1];
            other.Hp = 0;
            None(e.PreviewAction(e.UnitIndexOf(other), BattleCommand.Attack(null), golem), "dead actor");
        }

        [LogicTest]
        public static void SkillMenuPartitionsKnownWeakDamageSkillsStably()
        {
            var e = Engine(7, new[] { "golem", "wisp" });
            var hero = e.ActiveHero;
            Assert.True(e.SkillMenu(hero).Select(o => o.Id).SequenceEqual(e.GetCommandOptions(hero).Skills.Select(o => o.Id)), "nothing known: learn order");
            var known = Engine(7, new[] { "golem", "wisp" }, new[] { "golem:" + Slash, "wisp:" + Ice });
            hero = known.ActiveHero;
            hero.Mp = 0;
            var menu = known.SkillMenu(hero);
            Assert.Equal("slash3,ice_rand,fire_all,plain,heal,buff", string.Join(",", menu.Select(o => o.Id)), "known-weak damage skills first, learn order kept");
            var plainOrder = known.GetCommandOptions(hero).Skills;
            Assert.Equal("slash3,fire_all,ice_rand,plain,heal,buff", string.Join(",", plainOrder.Select(o => o.Id)), "AUTO/options order unchanged");
            foreach (var o in menu)
            {
                var p = plainOrder.First(x => x.Id == o.Id);
                Assert.True(o.Usable == p.Usable && o.ReasonKey == p.ReasonKey && o.MpCost == p.MpCost && o.TpCost == p.TpCost, o.Id + " keeps reason/costs");
            }
            Assert.Equal("reason_mp", menu[0].ReasonKey, "unusable known-weak skill keeps its reason");
            Assert.Equal(SkillAffinityTag.Weak, menu[0].KnownAffinity, "slash3 tagged weak");
            Assert.Equal(SkillAffinityTag.None, menu.First(o => o.Id == "heal").KnownAffinity, "non-damage skills have no tag");
        }

        [LogicTest]
        public static void ManaShieldAndInvincibleSetShielded()
        {
            var e = Engine(14, new[] { "golem" });
            var golem = e.Enemies[0];
            var plain = Preview(e, BattleCommand.Attack(null), golem).Targets[0];
            Assert.True(!plain.Shielded, "no shield yet");
            var mana = new StatusDef { Id = "test_mana_shield", DisplayName = "Mana Shield", EffectType = StatusEffectType.ManaShield, Magnitude = 0.5f, DurationTurns = 3 };
            golem.Mp = 0;
            golem.ApplyStatus(BattleStatus.FromDef(mana, golem.Id));
            Assert.True(!Preview(e, BattleCommand.Attack(null), golem).Targets[0].Shielded, "a mana shield without MP absorbs nothing");
            golem.Mp = 40;
            var manaShielded = Preview(e, BattleCommand.Attack(null), golem).Targets[0];
            Assert.True(manaShielded.Shielded, "mana shield with MP flags the target");
            Assert.True(manaShielded.Min == plain.Min && manaShielded.Max == plain.Max, "mana shield: range before absorption");
            golem.ClearStatuses();
            golem.Mp = 0;
            var invincible = new StatusDef { Id = "test_invincible", DisplayName = "Invincible", EffectType = StatusEffectType.Invincible, DurationTurns = 2 };
            golem.ApplyStatus(BattleStatus.FromDef(invincible, golem.Id));
            var inv = Preview(e, BattleCommand.Attack(null), golem).Targets[0];
            Assert.True(inv.Shielded, "invincible flags the target");
            Assert.True(inv.Min == plain.Min && inv.Max == plain.Max && !inv.Lethal == !plain.Lethal, "invincible: range before absorption");
            var all = Preview(e, BattleCommand.Skill("fire_all"), null).For(golem.Id);
            Assert.True(all.Shielded, "AoE rows carry the flag too");
        }

        [LogicTest]
        public static void UnknownRandomScopeMaxStaysNeutralWhenHitsExceedShield()
        {
            // Wisp is really weak to Ice (shield 3) but the player does not know it; ice_rand has 4 hits > 3 shield.
            var e = Engine(15, new[] { "wisp" });
            var wisp = e.Enemies[0];
            var skill = e.ActiveHero.Skills.First(s => s.Id == "ice_rand");
            Assert.True(skill.HitCount > wisp.Shield && wisp.IsWeakTo(Ice), "fixture: more hits than shield, real weakness");
            double baseAmount = DamageFormula.BaseAmount(e.ActiveHero, wisp, skill);
            int neutralMin = DamageFormula.FinalAmount(baseAmount * DamageFormula.LowestRoll(DamageFormula.DamageVariance));
            int neutralMax = DamageFormula.FinalAmount(baseAmount * DamageFormula.HighestRoll(DamageFormula.DamageVariance));
            var unknown = Preview(e, BattleCommand.Skill("ice_rand"), null);
            var row = unknown.For(wisp.Id);
            Assert.True(unknown.Random && unknown.HitCount == 4, "random scope, 4 hits");
            Assert.Equal(PreviewAffinity.Unknown, row.Affinity, "undiscovered weakness");
            Assert.Equal(neutralMin, row.Min, "unknown random min is neutral");
            Assert.Equal(neutralMax, row.Max, "unknown random max stays neutral: no weakness, no BREAK multiplier");
            Assert.True(!row.Breaks && row.ShieldDamage == 0 && !row.Lethal, "no break / shield / lethal modelled");
            wisp.Shield = 1;
            Assert.Equal(neutralMax, Preview(e, BattleCommand.Skill("ice_rand"), null).For(wisp.Id).Max, "still neutral with a single shield pip left");
            wisp.Shield = wisp.MaxShield;

            // Contrast: the same fixture with the weakness known models the BREAK on the max.
            var k = Engine(15, new[] { "wisp" }, new[] { "wisp:" + Ice });
            var kw = k.Enemies[0];
            int knownMax = DamageFormula.FinalAmount(DamageFormula.ApplyTargetMultipliers(baseAmount * DamageFormula.HighestRoll(DamageFormula.DamageVariance), kw, skill, DamageType.Magical, DamageFormula.WeaknessMultiplier, true));
            Assert.Equal(knownMax, Preview(k, BattleCommand.Skill("ice_rand"), null).For(kw.Id).Max, "known weakness: random max may use BREAK");
        }

        // --- labels ------------------------------------------------------------------------------------

        static void SummonOnto(BattleEngine e, BattleUnit summoner, params string[] ids)
            => typeof(BattleEngine).GetMethod("Summon", BindingFlags.Instance | BindingFlags.NonPublic).Invoke(e, new object[] { summoner, ids });

        [LogicTest]
        public static void SameNamedEnemiesGetStableDisplayLetters()
        {
            var e = Engine(8, new[] { "golem", "wisp", "golem", "golem" }, new[] { "golem:" + Slash });
            var start = new BattleEngine(Db(), new BattleSetup { Seed = 8, Party = { Hero("hero0") }, EnemyGroup = { "golem", "golem" } }).Start().OfType<BattleStartEvent>().Single();
            Assert.Equal("Golem A,Golem B", string.Join(",", start.Units.Where(u => u.Side == BattleSide.Enemy).Select(u => u.DisplayName)), "start snapshots carry labels");
            Assert.True(start.Units.Where(u => u.Side == BattleSide.Enemy).All(u => u.BaseName == "Golem"), "snapshots keep the data name");
            Assert.Equal("Golem A|Wisp|Golem B|Golem C", string.Join("|", e.Enemies.Select(u => u.DisplayName)), "initial letters in formation order; unique names unlettered");
            Assert.Equal("enemy_00_golem|enemy_01_wisp|enemy_02_golem|enemy_03_golem", string.Join("|", e.Enemies.Select(u => u.Id)), "unit ids untouched");
            Assert.True(e.Enemies.All(u => u.DefId == u.Id.Substring(9)) && e.Enemies.All(u => u.BaseName == Db().Enemies[u.DefId].DisplayName), "DefId and data names untouched");

            // Kill golem A with a known-weak slash run; the log names the letter, keys stay enemyId:element.
            var a = e.Enemies[0];
            var events = e.Submit(BattleCommand.Skill("slash3", a.Id));
            var breakMsg = events.OfType<MessageEvent>().FirstOrDefault(m => m.Key == "break");
            Assert.True(breakMsg != null && breakMsg.Text == "Golem A BREAK!", "battle log uses the label: " + breakMsg?.Text);
            a.Hp = 0;
            var b = e.Enemies[2];
            Assert.Equal("Golem B", b.DisplayName, "survivor keeps its letter after a death");
            var summoner = e.Enemies[3];
            SummonOnto(e, summoner, "golem", "wisp", "golem");
            Assert.Equal("Golem A|Wisp|Golem B|Golem C|Golem D|Wisp B", string.Join("|", e.Enemies.Select(u => u.DisplayName)),
                "summons take the next unused letter (a dead A stays used; an unlettered namesake counts as A); survivors never relabelled; cap of 5 living");
            Assert.Equal("enemy_04_golem", e.Enemies[4].Id, "summon id unchanged by labels");
            e.Enemies[2].Hp = 0;
            SummonOnto(e, summoner, "golem");
            Assert.Equal("Golem A|Wisp|Golem B|Golem C|Golem D|Wisp B|Golem E", string.Join("|", e.Enemies.Select(u => u.DisplayName)), "letters of fallen units are never reused");

            var e2 = Engine(9, new[] { "mother", "golem" });
            SummonOnto(e2, e2.Enemies[0], "wisp", "golem");
            Assert.Equal("Mother|Golem|Wisp|Golem B", string.Join("|", e2.Enemies.Select(u => u.DisplayName)), "lone original keeps its name; colliding summon gets B");
            var outcomeKeys = new BattleEngine(Db(), new BattleSetup { Seed = 1, Party = { Hero("hero0", 1000, AllSkills) }, EnemyGroup = { "golem", "golem" } });
            outcomeKeys.Start();
            outcomeKeys.Submit(BattleCommand.Skill("slash3", outcomeKeys.Enemies[1].Id));
            Assert.True(outcomeKeys.KnownWeaknessesOf(outcomeKeys.Enemies[0]).Contains(Slash), "weakness found on Golem B is known for Golem A (shared enemyId:element key)");
        }

        // --- purity ------------------------------------------------------------------------------------

        /// <summary>Deep dump of everything reachable from the engine except the shared data tables.</summary>
        static string Fingerprint(BattleEngine engine)
        {
            var sb = new StringBuilder();
            var seen = new Dictionary<object, int>(ReferenceEqualityComparer.Instance);
            Dump(engine, sb, seen, 0);
            return sb.ToString();
        }

        sealed class ReferenceEqualityComparer : IEqualityComparer<object>
        {
            public static readonly ReferenceEqualityComparer Instance = new ReferenceEqualityComparer();
            public new bool Equals(object a, object b) => ReferenceEquals(a, b);
            public int GetHashCode(object o) => System.Runtime.CompilerServices.RuntimeHelpers.GetHashCode(o);
        }

        static void Dump(object o, StringBuilder sb, Dictionary<object, int> seen, int depth)
        {
            if (o == null) { sb.Append("null;"); return; }
            var type = o.GetType();
            if (o is string || type.IsPrimitive || type.IsEnum || o is decimal)
            {
                sb.Append(o is double d ? d.ToString("R") : o is float f ? f.ToString("R") : o.ToString()).Append(';');
                return;
            }
            if (o is GameDB || o is Delegate) { sb.Append(type.Name).Append(';'); return; }
            if (depth > 40) throw new Exception("fingerprint too deep at " + type.Name);
            if (seen.TryGetValue(o, out int id)) { sb.Append("#").Append(id).Append(';'); return; }
            seen[o] = seen.Count;
            sb.Append(type.Name).Append('{');
            if (o is IDictionary dict)
            {
                foreach (DictionaryEntry kv in dict) { Dump(kv.Key, sb, seen, depth + 1); sb.Append("=>"); Dump(kv.Value, sb, seen, depth + 1); }
            }
            else if (o is IEnumerable list)
            {
                foreach (var item in list) Dump(item, sb, seen, depth + 1);
            }
            else
            {
                for (var t = type; t != null && t != typeof(object); t = t.BaseType)
                    foreach (var field in t.GetFields(BindingFlags.Instance | BindingFlags.Public | BindingFlags.NonPublic | BindingFlags.DeclaredOnly).OrderBy(x => x.Name))
                    {
                        sb.Append(field.Name).Append('=');
                        Dump(field.GetValue(o), sb, seen, depth + 1);
                    }
            }
            sb.Append('}');
        }

        static void Same(string expected, string actual, string why)
        {
            if (expected == actual) return;
            int i = 0;
            while (i < expected.Length && i < actual.Length && expected[i] == actual[i]) i++;
            int from = Math.Max(0, i - 120);
            string Cut(string s) => s.Substring(from, Math.Min(s.Length - from, 240));
            throw new Exception($"Assert failed: {why} (first difference at {i}: expected ...{Cut(expected)}... got ...{Cut(actual)}...)");
        }

        /// <summary>Every preview/menu query for the active hero against every unit index (incl. invalid ones).</summary>
        static int QueryEverything(BattleEngine e)
        {
            int n = 0;
            var hero = e.ActiveHero;
            int actor = e.UnitIndexOf(hero);
            var commands = new List<BattleCommand> { BattleCommand.Attack(null), BattleCommand.Guard(), BattleCommand.Flee(), BattleCommand.Item("bomb"), BattleCommand.Item("potion"), BattleCommand.Item("ether") };
            foreach (var s in AllSkills) commands.Add(BattleCommand.Skill(s));
            foreach (var cmd in commands)
                for (int t = -1; t <= e.Units.Count; t++)
                {
                    var p = e.PreviewAction(actor, cmd, t);
                    n += p.Targets.Count;
                    e.PreviewAction(t, cmd, t);
                }
            foreach (var o in e.SkillMenu(hero)) n += (int)o.KnownAffinity;
            foreach (var u in e.Units) for (int el = 0; el <= 8; el++) n += (int)e.KnownAffinity(u, el);
            return n;
        }

        [LogicTest]
        public static void PreviewsArePureAndKeepFutureRngStreams()
        {
            foreach (int seed in new[] { 11, 12, 13 })
            {
                var queried = Engine(seed, new[] { "golem", "wisp", "golem" }, new[] { "wisp:" + Ice });
                var plain = Engine(seed, new[] { "golem", "wisp", "golem" }, new[] { "wisp:" + Ice });
                queried.Enemies[0].ApplyStatus(BattleStatus.FromDef(Db().Statuses["test_barrier"], ""));
                plain.Enemies[0].ApplyStatus(BattleStatus.FromDef(Db().Statuses["test_barrier"], ""));
                var script = new[] { "slash3", "fire_all", "ice_rand", "heal", "plain", "bomb", "slash3", "ice_rand", "potion", "fire_all", "slash3", "plain" };
                var logA = new List<string>();
                var logB = new List<string>();
                int step = 0;
                while (queried.State == BattleEngineState.AwaitingCommand && step < 40)
                {
                    string before = Fingerprint(queried);
                    Same(Fingerprint(plain), before, $"seed {seed} step {step}: paired engines identical before queries");
                    int touched = QueryEverything(queried);
                    Assert.True(touched > 0, "queries produced previews");
                    Same(before, Fingerprint(queried), $"seed {seed} step {step}: comprehensive state unchanged by previews");
                    string pick = script[step % script.Length];
                    var hero = queried.ActiveHero;
                    BattleCommand Make(BattleEngine en)
                    {
                        var h = en.ActiveHero;
                        if (pick == "bomb" || pick == "potion") return BattleCommand.Item(pick, pick == "potion" ? h.Id : null);
                        if (pick == "heal") return BattleCommand.Skill(pick, h.Id);
                        var foe = en.Enemies.First(x => x.IsAlive);
                        return BattleCommand.Skill(pick, pick == "slash3" || pick == "plain" ? foe.Id : null);
                    }
                    logA.AddRange(queried.Submit(Make(queried)).Select(BattleTestUtil.Describe));
                    logB.AddRange(plain.Submit(Make(plain)).Select(BattleTestUtil.Describe));
                    step++;
                }
                Assert.Equal(string.Join("\n", logB), string.Join("\n", logA), $"seed {seed}: identical event streams with and without previews");
                for (int i = 0; i < 32; i++)
                    Assert.Equal(plain.Rng.Randf(), queried.Rng.Randf(), $"seed {seed}: future RNG draw {i} identical");
            }
        }
    }
}
