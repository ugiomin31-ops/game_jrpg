using System.Collections.Generic;
using System.Linq;
using Abyss.Logic;
using Abyss.Logic.Battle;

namespace Abyss.LogicTests
{
    public static class BreakRecoveryTests
    {
        static List<BattleEvent> PoisonedBreakTurn(int hp, out BattleUnit enemy)
        {
            var db = new GameDB();
            db.Enemies.Add("target", new EnemyDef
            {
                Id = "target", DisplayName = "Target", MaxHp = 100, Attack = 1,
                Speed = 1, Hit = 1, BreakShield = 3,
            });
            var setup = new BattleSetup { Seed = 123 };
            setup.Party.Add(new HeroCombatSpec
            {
                HeroId = "hero", DisplayName = "Hero", Level = 1,
                MaxHp = 100, Hp = 100, Speed = 100, Attack = 1, Hit = 1,
            });
            setup.EnemyGroup.Add("target");
            var engine = new BattleEngine(db, setup);
            engine.Start();
            enemy = engine.Enemies[0];
            enemy.Hp = hp;
            enemy.Broken = true;
            enemy.Shield = 0;
            enemy.ApplyStatus(BattleStatus.FromDef(new StatusDef
            {
                Id = "poison", EffectType = StatusEffectType.Poison,
                DurationTurns = 2, Magnitude = 0.1f,
            }, "hero"));
            return new List<BattleEvent>(engine.Submit(BattleCommand.Guard()));
        }

        [LogicTest]
        public static void LethalPoisonDoesNotRecoverBreak()
        {
            var events = PoisonedBreakTurn(1, out var enemy);
            Assert.True(!enemy.IsAlive, "poison defeats the broken enemy");
            Assert.Equal(0, enemy.Shield, "dead enemy keeps its depleted shield");
            Assert.Equal(1, events.OfType<UnitDownEvent>().Count(), "one defeat event");
            Assert.Equal(0, events.OfType<RecoverEvent>().Count(), "no recovery after death");
            Assert.Equal(0, events.OfType<ShieldChangeEvent>().Count(), "no shield refill after death");
            var snapshot = events.OfType<TurnEndEvent>().Single(e => e.Unit.Id == enemy.Id).Unit;
            Assert.Equal(0, snapshot.Hp, "final turn snapshot records death");
            Assert.Equal(0, snapshot.Shield, "final turn snapshot has no recovered shield");
            Assert.Equal(1, events.OfType<BattleEndEvent>().Count(), "victory settles once");
        }

        [LogicTest]
        public static void SurvivingPoisonStillRecoversBreak()
        {
            var events = PoisonedBreakTurn(100, out var enemy);
            Assert.True(enemy.IsAlive, "control survives poison");
            Assert.True(!enemy.Broken, "living enemy recovers from break");
            Assert.Equal(enemy.MaxShield, enemy.Shield, "living enemy regains shield");
            Assert.Equal(1, events.OfType<RecoverEvent>().Count(), "normal recovery emitted once");
        }
    }
}
