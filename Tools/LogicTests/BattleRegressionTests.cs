// Regression coverage for command refusal, replay snapshots and deterministic range/boss edges.
using System;
using System.Collections.Generic;
using System.Linq;
using Abyss.Logic;
using Abyss.Logic.Battle;

namespace Abyss.LogicTests
{
    public static class BattleRegressionTests
    {
        static BattleEngine WaitingBattle(int seed = 41, bool withStatus = false)
        {
            var db = new GameDB();
            db.Enemies.Add("target", new EnemyDef
            {
                Id = "target", DisplayName = "Target", MaxHp = 5000, Attack = 1,
                Defense = 0, Resistance = 0, Speed = 1, Hit = 1, Evade = 0,
            });
            var hero = new HeroCombatSpec
            {
                HeroId = "hero", DisplayName = "Hero", Level = 1, Hp = 100, MaxHp = 100,
                Mp = 10, MaxMp = 10, Attack = 10, Magic = 10, Defense = 20,
                Resistance = 20, Speed = 100, Hit = 1,
            };
            if (withStatus)
            {
                db.Statuses.Add("attack_up", new StatusDef
                {
                    Id = "attack_up", EffectType = StatusEffectType.AttackUp,
                    DurationTurns = 3, Magnitude = 0.25f,
                });
                hero.Statuses.Add("attack_up", 3);
            }
            var setup = new BattleSetup { Seed = seed };
            setup.Party.Add(hero);
            setup.EnemyGroup.Add("target");
            var engine = new BattleEngine(db, setup);
            engine.Start();
            return engine;
        }

        [LogicTest]
        public static void UnknownCommandCannotSilentlyAttack()
        {
            var engine = WaitingBattle();
            var control = WaitingBattle();
            var actor = engine.ActiveHero;
            var command = new BattleCommand { Kind = (CommandKind)99 };
            Assert.Equal(TargetRule.None, engine.GetTargetRule(actor, command), "invalid command has no target rule");
            Assert.Equal(0, engine.ValidTargets(actor, command).Count, "invalid command has no menu targets");
            var events = engine.Submit(command);
            Assert.Equal(1, events.Count, "refusal is the only event");
            Assert.Equal("invalid_action", ((CommandRejectedEvent)events[0]).Key, "unknown kind rejected");
            Assert.True(ReferenceEquals(actor, engine.ActiveHero), "same hero still awaiting input");
            Assert.Equal(control.Enemies[0].Hp, engine.Enemies[0].Hp, "refusal deals no damage");
            Assert.Equal(control.Rng.NextUInt(), engine.Rng.NextUInt(), "refusal consumes no RNG");
        }

        [LogicTest]
        public static void TurnEndCopiesGuardAndRemainingStatusDuration()
        {
            var engine = WaitingBattle(withStatus: true);
            string heroId = engine.ActiveHero.Id;
            var events = engine.Submit(BattleCommand.Guard());
            var end = events.OfType<TurnEndEvent>().First(e => e.Unit.Id == heroId);
            Assert.True(end.Unit.Guarding, "guard is visible at the end of the guarded turn");
            Assert.Equal(2, end.Unit.Statuses.Single().Turns, "surviving status ticks are visible");
            Assert.True(engine.State == BattleEngineState.AwaitingCommand, "next round awaits hero");
            Assert.True(!engine.ActiveHero.Guarding, "guard expires at next turn start");
            engine.Submit(BattleCommand.Guard());
            Assert.Equal(2, end.Unit.Statuses.Single().Turns, "earlier replay snapshot cannot change");
            Assert.True(end.Unit.Guarding, "earlier guard snapshot cannot change");
        }

        [LogicTest]
        public static void RankTwoUsesHardBossScaleWithoutExplicitFlag()
        {
            var enemy = new EnemyDef
            {
                Id = "rank_boss", Rank = 2, MaxHp = 100, Attack = 100, Magic = 100,
                ExperienceReward = 100, GoldReward = 100,
            };
            var build = EnemyStats.Build(enemy, Difficulty.Hard);
            Assert.Equal(120, build.MaxHp, "boss HP override agrees with BattleUnit.IsBoss");
            Assert.Equal(110, build.Attack, "boss attack override");
            Assert.Equal(110, build.Magic, "boss magic override");
            Assert.Equal(110, build.ExperienceReward, "hard reward scale applied once");
            Assert.Equal(120, build.GoldReward, "hard gold scale applied once");
        }

        [LogicTest]
        public static void RngInclusiveRangeHandlesAllSignedIntegers()
        {
            var rng = new GodotRng(813);
            var raw = new GodotRng(813);
            int expected = (int)((long)int.MinValue + raw.NextUInt());
            Assert.Equal(expected, rng.RandiRange(int.MinValue, int.MaxValue), "full range uses one raw draw");
            expected = (int)((long)int.MinValue + raw.NextUInt());
            Assert.Equal(expected, rng.RandiRange(int.MaxValue, int.MinValue), "reversed range stays deterministic");
            Assert.Equal(17, rng.RandiRange(17, 17), "singleton range");
            Assert.Equal(raw.NextUInt(), rng.NextUInt(), "singleton consumes no RNG");
        }
    }
}
