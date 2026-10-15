// Skill expansion v2: drain, the newest-ultimate AUTO preference and the shape of every hero learnset.
using System;
using System.Collections.Generic;
using System.Linq;
using Abyss.Logic;
using Abyss.Logic.Battle;

namespace Abyss.LogicTests
{
    public static class SkillExpansionTests
    {
        [LogicTest]
        public static void DrainHealsActorByShareOfDamageDealt()
        {
            var db = new GameDB();
            db.Enemies.Add("target", new EnemyDef
            {
                Id = "target", DisplayName = "Target", MaxHp = 5000, Attack = 1, Defense = 0, Resistance = 0, Speed = 1, Hit = 1,
            });
            db.Skills.Add("drain", new SkillDef
            {
                Id = "drain", DisplayName = "Drain", Kind = SkillKind.Damage, ScalingStat = ScalingStat.Magic, Power = 2f, Drain = 0.5f,
            });
            var hero = new HeroCombatSpec
            {
                HeroId = "hero", DisplayName = "Hero", Level = 1, Hp = 10, MaxHp = 500, Mp = 10, MaxMp = 10,
                Attack = 10, Magic = 40, Defense = 20, Resistance = 20, Speed = 100, Hit = 1,
            };
            hero.Skills.Add("drain");
            var setup = new BattleSetup { Seed = 7 };
            setup.Party.Add(hero);
            setup.EnemyGroup.Add("target");
            var engine = new BattleEngine(db, setup);
            engine.Start();
            string heroId = engine.ActiveHero.Id;
            var events = engine.Submit(BattleCommand.Skill("drain", engine.Enemies[0].Id));
            int dealt = events.OfType<DamageEvent>().Where(e => e.SourceId == heroId && e.Type != DamageType.Status).Sum(e => e.Amount);
            var heal = events.OfType<HealEvent>().Single(e => e.TargetId == heroId && e.StatusId == null);
            Assert.True(dealt > 0, "drain skill dealt damage");
            Assert.Equal((int)Math.Round(dealt * 0.5, MidpointRounding.AwayFromZero), heal.Amount, "half of the damage returns as HP");
            Assert.Equal(10 + heal.Amount, heal.HpAfter, "heal snapshot carries the new HP");
            int damageIndex = events.ToList().FindIndex(e => e is DamageEvent);
            Assert.True(events.ToList().IndexOf(heal) > damageIndex, "drain heal is replayed after the hit");
        }

        [LogicTest]
        public static void AutoFiresTheNewestUltimateWhenUseful()
        {
            var setup = BattleTestUtil.Setup(38, new[] { "slime", "slime", "slime" }, 3, heroes: new[] { "h_dohyun" });
            var engine = new BattleEngine(TestMain.DB, setup);
            engine.Start();
            var hero = engine.ActiveHero;
            Assert.True(hero != null, "warrior awaits a command");
            hero.Tp = 100;
            foreach (var enemy in engine.Enemies) enemy.Hp = enemy.MaxHp = 3000;
            var cmd = engine.SuggestCommand(hero);
            Assert.Equal("ult_w_ragnarok", cmd.SkillId, "the later, stronger ultimate is preferred by AUTO");
        }

        [LogicTest]
        public static void HeroLearnsetsAreCompleteAndConsistent()
        {
            var db = TestMain.DB;
            foreach (var id in db.HeroOrder)
            {
                var hero = db.Heroes[id];
                var seen = new HashSet<string>();
                int ultimates = 0;
                foreach (var row in hero.Learnset)
                {
                    Assert.True(row.Level >= 1 && row.Level <= 40, $"{id}: {row.Skill} level {row.Level} within the cap");
                    Assert.True(seen.Add(row.Skill), $"{id}: {row.Skill} learned once");
                    Assert.True(db.Skills.TryGetValue(row.Skill, out var skill), $"{id}: {row.Skill} exists");
                    Assert.True(!string.IsNullOrEmpty(skill.DisplayName) && !string.IsNullOrEmpty(skill.Description), $"{row.Skill} has Korean text");
                    Assert.True(skill.Presentation != null && db.Presentations.ContainsKey(skill.Presentation), $"{row.Skill} has a presentation");
                    foreach (var status in new[] { skill.StatusEffect }.Concat(skill.ExtraStatuses))
                        Assert.True(status == null || db.Statuses.ContainsKey(status), $"{row.Skill}: status {status} exists");
                    Assert.True(skill.Drain == 0f || skill.Kind == SkillKind.Damage, $"{row.Skill}: drain only on damage skills");
                    if (skill.TpCost > 0) { ultimates++; Assert.Equal(0, skill.MpCost, $"{row.Skill}: ultimates cost no MP"); }
                    else Assert.True(skill.MpCost > 0, $"{row.Skill}: regular skills cost MP");
                }
                Assert.True(hero.Learnset.Count >= 20, $"{id} has a full skill list ({hero.Learnset.Count})");
                Assert.Equal(2, ultimates, $"{id} learns two ultimates");
                var spec = BattleTestUtil.Hero(id, 40);
                foreach (var row in hero.Learnset)
                {
                    var skill = db.Skills[row.Skill];
                    Assert.True(skill.MpCost <= spec.MaxMp / 2, $"{row.Skill} costs at most half of {id}'s Lv40 MP");
                }
            }
        }
    }
}
