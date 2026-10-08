using System;
using System.Collections.Generic;
using System.Linq;
using Abyss.Logic;
using Abyss.Logic.Battle;
using Abyss.Logic.Game;

namespace Abyss.LogicTests
{
    public static class QualityUpgradeTests
    {
        static HeroCombatSpec Hero(string id, int hp = 100, params string[] skills) => new HeroCombatSpec
        {
            HeroId = id, DisplayName = id, Level = 10, MaxHp = 100, Hp = hp, MaxMp = 100, Mp = 100,
            Attack = 50, Magic = 100, Defense = 5, Resistance = 5, Speed = 1000, Hit = 1, Skills = skills.ToList(),
        };
        static SkillDef Skill(string id, SkillKind kind, TargetType target = TargetType.Enemy, Scope scope = Scope.Single,
            float power = 1, int mp = 5, string status = null) => new SkillDef
        {
            Id = id, DisplayName = id, Kind = kind, TargetType = target, Scope = scope,
            ScalingStat = ScalingStat.Magic, Power = power, MpCost = mp, StatusEffect = status, StatusChance = 1,
        };
        static BattleEngine Engine(IEnumerable<SkillDef> skills, IEnumerable<HeroCombatSpec> party, int hp = 3000, int foes = 1)
        {
            var db = new GameDB();
            db.Enemies.Add("foe", new EnemyDef { Id = "foe", DisplayName = "Foe", MaxHp = hp, Attack = 20, Magic = 10, Defense = 5, Resistance = 5, Speed = 1, Hit = 1 });
            foreach (var s in skills) db.Skills.Add(s.Id, s);
            foreach (var st in TestMain.DB.Statuses) db.Statuses.Add(st.Key, st.Value);
            var setup = new BattleSetup { Seed = 9 };
            setup.Party.AddRange(party);
            for (int i = 0; i < foes; i++) setup.EnemyGroup.Add("foe");
            var engine = new BattleEngine(db, setup); engine.Start();
            Assert.Equal(BattleEngineState.AwaitingCommand, engine.State, "party awaits command");
            return engine;
        }
        static void Accepted(BattleEngine engine, BattleCommand command)
        {
            var events = engine.Submit(command);
            Assert.True(!events.OfType<CommandRejectedEvent>().Any(), "suggested command accepted");
        }

        [LogicTest]
        public static void AutoKeepsUltimateForAUsefulFight()
        {
            var engine = new BattleEngine(TestMain.DB, BattleTestUtil.Setup(38, new[] { "slime" }, 3, heroes: new[] { "warrior" }));
            engine.Start(); engine.ActiveHero.Tp = 100;
            engine.Enemies[0].Hp = Math.Min(engine.Enemies[0].Hp, 40); // a nearly beaten slime: one attack finishes it
            var cmd = engine.SuggestCommand(engine.ActiveHero);
            Assert.Equal(CommandKind.Attack, cmd.Kind, "free finishing attack instead of spending TP on overkill");
            Accepted(engine, cmd);
        }
        [LogicTest]
        public static void AutoHealsCriticalAllyBeforeReviving()
        {
            var skills = new[] { Skill("heal", SkillKind.Heal, TargetType.Ally, power: 1.5f), Skill("raise", SkillKind.Revive, TargetType.Ally, power: 0.5f) };
            var engine = Engine(skills, new[] { Hero("healer", 10, "heal", "raise"), Hero("fallen", 0) });
            var cmd = engine.SuggestCommand(engine.ActiveHero);
            Assert.Equal("heal", cmd.SkillId, "rescue surviving healer first");
            Assert.Equal(engine.ActiveHero.Id, cmd.TargetId, "critical ally targeted"); Accepted(engine, cmd);
        }
        [LogicTest]
        public static void AutoUsesGroupReviveForMultipleFallenAllies()
        {
            var skills = new[] { Skill("raise", SkillKind.Revive, TargetType.Ally, power: 0.35f, mp: 16), Skill("raise_all", SkillKind.Revive, TargetType.Ally, Scope.All, 0.6f, 40) };
            var engine = Engine(skills, new[] { Hero("healer", 100, "raise", "raise_all"), Hero("a", 0), Hero("b", 0) });
            var cmd = engine.SuggestCommand(engine.ActiveHero);
            Assert.Equal("raise_all", cmd.SkillId, "group resurrection used"); Accepted(engine, cmd);
        }
        [LogicTest]
        public static void AutoRevivesHealerFirst()
        {
            var skills = new[] { Skill("raise", SkillKind.Revive, TargetType.Ally, power: 0.5f), Skill("heal", SkillKind.Heal, TargetType.Ally) };
            var engine = Engine(skills, new[] { Hero("actor", 100, "raise"), Hero("fighter", 0), Hero("healer", 0, "heal") });
            var cmd = engine.SuggestCommand(engine.ActiveHero);
            Assert.Equal(engine.Party[2].Id, cmd.TargetId, "fallen healer has rescue priority"); Accepted(engine, cmd);
        }
        [LogicTest]
        public static void AutoCleansesDisablingAilmentBeforeUltimate()
        {
            var cleanse = Skill("clean", SkillKind.Cleanse, TargetType.Ally);
            var ult = Skill("ult", SkillKind.Damage, power: 5, mp: 0); ult.TpCost = 100;
            var engine = Engine(new[] { cleanse, ult }, new[] { Hero("actor", 100, "clean", "ult"), Hero("ally") });
            engine.ActiveHero.Tp = 100;
            engine.Party[1].ApplyStatus(BattleStatus.FromDef(TestMain.DB.Statuses["stun"], ""));
            var cmd = engine.SuggestCommand(engine.ActiveHero);
            Assert.Equal("clean", cmd.SkillId, "remove stun before attacking");
            Assert.Equal(engine.Party[1].Id, cmd.TargetId, "stunned ally targeted"); Accepted(engine, cmd);
        }
        [LogicTest]
        public static void AutoHealsSeveralInjuredAlliesEfficiently()
        {
            var skills = new[] { Skill("single", SkillKind.Heal, TargetType.Ally, power: 1.5f, mp: 5), Skill("group", SkillKind.Heal, TargetType.Ally, Scope.All, 1, 8) };
            var engine = Engine(skills, new[] { Hero("actor", 35, "single", "group"), Hero("ally", 35) });
            var cmd = engine.SuggestCommand(engine.ActiveHero);
            Assert.Equal("group", cmd.SkillId, "group healing has more useful recovery"); Accepted(engine, cmd);
        }
        [LogicTest]
        public static void AutoSelfHealNeverTargetsAnotherAlly()
        {
            var engine = Engine(new[] { Skill("self", SkillKind.Heal, TargetType.Self) }, new[] { Hero("actor", 100, "self"), Hero("ally", 10) });
            var cmd = engine.SuggestCommand(engine.ActiveHero);
            Assert.True(cmd.SkillId != "self", "full actor doesn't cast self heal on injured ally"); Accepted(engine, cmd);
        }
        [LogicTest]
        public static void AutoBuffsLongFightWithoutRefreshingActiveBuff()
        {
            var buff = Skill("focus", SkillKind.Buff, TargetType.Self, power: 0, mp: 3, status: "magic_up");
            var engine = Engine(new[] { buff, Skill("spell", SkillKind.Damage, mp: 90) }, new[] { Hero("actor", 100, "focus", "spell") });
            var actor = engine.ActiveHero;
            Assert.Equal("focus", engine.SuggestCommand(actor).SkillId, "focus prepares a long battle");
            actor.ApplyStatus(BattleStatus.FromDef(TestMain.DB.Statuses["magic_up"], actor.Id));
            Assert.True(engine.SuggestCommand(actor).SkillId != "focus", "don't reapply active focus");
        }
        [LogicTest]
        public static void AutoMultiHitBreaksKnownShield()
        {
            var s = Skill("double", SkillKind.Damage, power: 0.45f, mp: 2); s.ScalingStat = ScalingStat.Attack; s.Element = Element.Fire; s.HitCount = 2;
            var db = new GameDB(); db.Skills.Add(s.Id, s);
            db.Enemies.Add("shield", new EnemyDef { Id = "shield", MaxHp = 1000, Attack = 70, Speed = 1, BreakShield = 2, Weaknesses = new List<int> { (int)Element.Fire } });
            var setup = new BattleSetup { Seed = 3 }; setup.Party.Add(Hero("actor", 100, "double")); setup.EnemyGroup.Add("shield"); setup.KnownWeaknesses.Add("shield:4");
            var engine = new BattleEngine(db, setup); engine.Start();
            var cmd = engine.SuggestCommand(engine.ActiveHero);
            Assert.Equal("double", cmd.SkillId, "known two-hit break beats raw attack"); var events = engine.Submit(cmd);
            Assert.True(!events.OfType<CommandRejectedEvent>().Any(), "break action accepted");
            Assert.True(events.OfType<BreakEvent>().Any(), "shield actually broken before the enemy turn refresh");
        }
        [LogicTest]
        public static void AutoQueryDoesNotChangeRngOrConsumeItems()
        {
            var setup = BattleTestUtil.Setup(10, new[] { "slime", "mushroom" }, 567);
            setup.Inventory["healing_potion"] = 4;
            var a = new BattleEngine(TestMain.DB, setup); var b = new BattleEngine(TestMain.DB, setup); a.Start(); b.Start();
            var command = a.SuggestCommand(a.ActiveHero);
            for (int i = 0; i < 30; i++) Assert.Equal(command.ToString(), a.SuggestCommand(a.ActiveHero).ToString(), "repeat query deterministic");
            var ea = a.Submit(command).Select(BattleTestUtil.Describe).ToArray();
            var eb = b.Submit(b.SuggestCommand(b.ActiveHero)).Select(BattleTestUtil.Describe).ToArray();
            Assert.Equal(string.Join("\n", ea), string.Join("\n", eb), "AUTO query leaves RNG untouched");
        }
        [LogicTest]
        public static void EquipmentPreviewUsesEffectiveClampsAndLeavesSaveUntouched()
        {
            var state = GameState.NewGame(TestMain.DB, Difficulty.Normal);
            var hero = state.Hero("archer");
            state.AddEquipment("acc_eagle_eye", 1);
            string saved = SaveCodec.Serialize(state);
            var preview = PartyStats.PreviewEquipment(TestMain.DB, hero, "accessory", "acc_eagle_eye");
            Assert.Equal(saved, SaveCodec.Serialize(state), "preview doesn't mutate hero/bag/vitals");
            Assert.True(PartyStats.Equip(TestMain.DB, state, hero.Id, "acc_eagle_eye").Success, "equip succeeds");
            var actual = PartyStats.EffectiveStats(TestMain.DB, hero);
            Assert.Equal(preview.Stats, actual.Stats, "preview equals equipped stats");
            Assert.Near(preview.Crit, actual.Crit, 0.00001, "critical preview equals actual");
            var plain = PartyStats.PreviewEquipment(TestMain.DB, hero, "accessory", null);
            Assert.True(plain.Crit < actual.Crit, "unequip preview shows lost crit");
        }
        [LogicTest]
        public static void EquipmentPreviewIncludesResistanceAndRejectsOtherClass()
        {
            var state = GameState.NewGame(TestMain.DB, Difficulty.Normal);
            var hero = state.Hero("mage");
            var preview = PartyStats.PreviewEquipment(TestMain.DB, hero, "accessory", "acc_frost_amulet");
            Assert.True(preview.ElementResists.Contains((int)Element.Ice), "preview includes ice resistance");
            bool threw = false;
            try { PartyStats.PreviewEquipment(TestMain.DB, hero, "weapon", "sword_iron"); } catch (ArgumentException) { threw = true; }
            Assert.True(threw, "incompatible warrior weapon rejected");
        }
        [LogicTest]
        public static void EveryEnemyHasGuaranteedSpoilAndRareGear()
        {
            var db = TestMain.DB;
            foreach (var enemy in db.Enemies.Values)
            {
                Assert.True(enemy.Drops.Count >= 4, enemy.Id + " has varied loot");
                Assert.True(enemy.Drops.Any(d => d.Chance == 1), enemy.Id + " leaves a guaranteed spoil");
                // Gear the expansion plan fixes (Tools/content/spec.py) counts as rare before its rows exist.
                Assert.True(enemy.Drops.Any(d => db.Equipment.TryGetValue(d.Id, out var gear) ? gear.Rarity > 0 : SpecIds.Equipment.Contains(d.Id)), enemy.Id + " can drop rare gear");
                Assert.Equal(enemy.Drops.Count, enemy.Drops.Select(d => d.Id).Distinct().Count(), enemy.Id + " has no duplicate roll rows");
                foreach (var drop in enemy.Drops)
                {
                    Assert.True(db.Items.ContainsKey(drop.Id) || db.Equipment.ContainsKey(drop.Id) || SpecIds.Items.Contains(drop.Id) || SpecIds.Equipment.Contains(drop.Id), "valid loot id " + drop.Id);
                    Assert.True(drop.Chance > 0 && drop.Chance <= 1, "valid loot probability");
                }
            }
        }
        [LogicTest]
        public static void VictoryLootIsSeededOnceAndSummonsCannotFarmLoot()
        {
            var db = new GameDB();
            db.Enemies.Add("foe", new EnemyDef { Id = "foe", MaxHp = 1, Speed = 1, Drops = new List<DropEntry> { new DropEntry { Id = "rare", Chance = 1 }, new DropEntry { Id = "chance", Chance = 0.2f } } });
            var setup = new BattleSetup { Seed = 71 }; setup.Party.Add(Hero("actor")); setup.EnemyGroup.AddRange(new[] { "foe", "foe" });
            BattleEngine Win()
            {
                var engine = new BattleEngine(db, setup); engine.Start(); engine.Enemies[1].Summoned = true;
                while (engine.State == BattleEngineState.AwaitingCommand) engine.Submit(BattleCommand.Attack(engine.Enemies.First(e => e.IsAlive).Id));
                return engine;
            }
            var a = Win(); var b = Win();
            Assert.Equal(1, a.Outcome.Drops["rare"], "summoned enemy excluded from drops");
            Assert.Equal(string.Join(";", a.Outcome.Drops), string.Join(";", b.Outcome.Drops), "same seed yields same drops");
            var before = string.Join(";", a.Outcome.Drops); a.Submit(BattleCommand.Guard());
            Assert.Equal(before, string.Join(";", a.Outcome.Drops), "submitting after victory never rerolls loot");
        }
        [LogicTest]
        public static void EveryMonsterAndBossCompletesOnAllDifficulties()
        {
            int battles = 0, victories = 0;
            foreach (Difficulty difficulty in Enum.GetValues(typeof(Difficulty)))
                foreach (var enemy in TestMain.DB.Enemies.Values)
                {
                    var kind = enemy.IsBoss || enemy.Rank >= 2 ? BattleKind.Boss : enemy.Rank > 0 ? BattleKind.Foe : BattleKind.Random;
                    var setup = BattleTestUtil.Setup(Math.Max(3, enemy.Level), new[] { enemy.Id }, 2026 + battles, kind, difficulty);
                    var engine = new BattleEngine(TestMain.DB, setup);
                    BattleTestUtil.RunAuto(engine);
                    Assert.Equal(BattleEngineState.Ended, engine.State, enemy.Id + " finishes on " + difficulty);
                    battles++;
                    if (engine.Outcome.Result == BattleResult.Victory) victories++;
                }
            Console.WriteLine($"  every-monster simulations: {battles} finished, {victories} victories (no equipment)");
            Assert.Equal(TestMain.DB.Enemies.Count * 3, battles, "all enemy/difficulty combinations covered");
        }

        [LogicTest]
        public static void AllSkillsMonstersAndFloorsHaveValidContentReferences()
        {
            var db = TestMain.DB;
            Assert.Equal(4, db.Heroes.Count, "four distinct party roles");
            Assert.Equal(35, db.Floors.Count, "six chapters of five floors plus the five-floor trial corridor");
            foreach (var skill in db.Skills.Values)
            {
                Assert.True(skill.MpCost >= 0 && skill.TpCost >= 0 && skill.HitCount > 0, "valid skill costs/hits " + skill.Id);
                Assert.True(!string.IsNullOrEmpty(skill.DisplayName) && !string.IsNullOrEmpty(skill.Description), "localized skill " + skill.Id);
                Assert.True(skill.Presentation == null || db.Presentations.ContainsKey(skill.Presentation), "skill presentation " + skill.Id);
                foreach (var status in new[] { skill.StatusEffect }.Concat(skill.ExtraStatuses))
                    Assert.True(status == null || db.Statuses.ContainsKey(status), "skill status " + skill.Id);
            }
            foreach (var enemy in db.Enemies.Values)
            {
                Assert.True(enemy.SkillWeights.Count == 0 || enemy.SkillWeights.Count == enemy.Skills.Count, "enemy skill weights " + enemy.Id);
                foreach (var id in enemy.Skills) Assert.True(db.Skills.ContainsKey(id), "enemy skill " + id);
                foreach (var id in enemy.Summons) Assert.True(db.Enemies.ContainsKey(id), "summon " + id);
                foreach (var phase in enemy.Phases)
                {
                    Assert.True(phase.Weights.Count == 0 || phase.Weights.Count == phase.Skills.Count, "phase weights " + enemy.Id);
                    foreach (var id in phase.Skills) Assert.True(db.Skills.ContainsKey(id), "boss phase skill " + id);
                    foreach (var id in phase.Summon) Assert.True(db.Enemies.ContainsKey(id), "boss summon " + id);
                }
            }
            foreach (var floor in db.Floors)
            {
                foreach (var group in floor.EncounterGroups.Concat(floor.Events.Select(e => e.Group)).Concat(floor.Foes.Select(f => f.Group)).Append(floor.BossGroup))
                    foreach (var id in group) Assert.True(db.Enemies.ContainsKey(id), "floor enemy " + id);
                foreach (var t in floor.Treasures)
                    foreach (var id in t.Contents.Items.Keys.Concat(t.Contents.Equipment.Keys))
                        Assert.True(db.Items.ContainsKey(id) || db.Equipment.ContainsKey(id) || SpecIds.Items.Contains(id) || SpecIds.Equipment.Contains(id), "treasure id " + id);
            }
            foreach (var enemy in db.Enemies.Values)
                Assert.True(string.IsNullOrEmpty(enemy.Model) || db.Enemies.ContainsKey(enemy.Model), "variant model " + enemy.Id);
        }

        [LogicTest]
        public static void EnemyDoesNotWasteTurnRefreshingSameBuff()
        {
            var db = TestMain.DB;
            var actor = BattleUnit.FromEnemy(db, db.Enemies["rhino_beetle"], EnemyStats.Build(db.Enemies["rhino_beetle"], Difficulty.Normal), 0);
            var hero = BattleUnit.FromHero(db, Hero("actor"), 0);
            actor.ApplyStatus(BattleStatus.FromDef(db.Statuses[db.Skills["sk_harden"].StatusEffect], actor.Id));
            for (int seed = 0; seed < 30; seed++)
            {
                var action = EnemyAI.Choose(actor, new List<BattleUnit> { hero }, new List<BattleUnit> { actor }, new GodotRng((ulong)seed), Difficulty.Normal, 0);
                Assert.True(action.PayloadId != "sk_harden", "active harden not reapplied");
            }
        }
    }
}
