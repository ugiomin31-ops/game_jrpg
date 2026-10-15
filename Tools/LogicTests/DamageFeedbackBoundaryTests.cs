using System.Linq;
using Abyss.Logic;
using Abyss.Logic.Battle;

namespace Abyss.LogicTests
{
    public static class DamageFeedbackBoundaryTests
    {
        const ulong CritOneSeed = 4154868180439371147UL;

        static HeroCombatSpec Hero(float crit = 0) => new HeroCombatSpec
        {
            HeroId = "feedback_hero", MaxHp = 1000, Hp = 1000, MaxMp = 100, Mp = 100, Attack = 100,
            Magic = 100, Speed = 1000, Hit = 2, Crit = crit,
        };

        static void CheckCrit(float crit, float bonus, bool expected)
        {
            var db = new GameDB();
            var actor = BattleUnit.FromHero(db, Hero(crit), 0);
            var target = BattleUnit.FromHero(db, Hero(), 1);
            var rng = new GodotRng(CritOneSeed);
            var oracle = new GodotRng(CritOneSeed);
            double variance = oracle.RandfRange(0.92, 1.08);
            Assert.True(oracle.Randf() <= DamageFormula.HitChance(actor, target, DamageType.Physical), "seed hits");
            Assert.Equal(1f, oracle.Randf(), "seed reaches inclusive upper crit boundary");
            var skill = new SkillDef { Power = 1, ScalingStat = ScalingStat.Attack, CritBonus = bonus };
            var hit = DamageFormula.Damage(actor, target, skill, rng);
            Assert.Equal(oracle.NextUInt(), rng.NextUInt(), "physical hit still consumes exactly three float draws");
            Assert.True(!hit.Missed, "hit succeeds");
            Assert.Equal(expected, hit.Critical, "critical probability endpoint");
            int amount = DamageFormula.FinalAmount(DamageFormula.BaseAmount(actor, target, skill) * variance * (expected ? 1.5 : 1));
            Assert.Equal(amount, hit.Amount, "critical multiplier reaches actual damage amount");
        }

        [LogicTest] public static void GuaranteedCritAtRandfOne() => CheckCrit(1, 0, true);
        [LogicTest] public static void BonusClampedCritAtRandfOne() => CheckCrit(0.5f, 0.75f, true);
        [LogicTest] public static void ZeroCritAtRandfOne() => CheckCrit(0, 0, false);
        [LogicTest] public static void PartialCritAtRandfOne() => CheckCrit(0.5f, 0, false);

        [LogicTest]
        public static void ZeroCritAtRandfZero()
        {
            const ulong seed = 9820130206980517218UL;
            var db = new GameDB();
            var actor = BattleUnit.FromHero(db, Hero(), 0);
            var target = BattleUnit.FromHero(db, Hero(), 1);
            var rng = new GodotRng(seed);
            var oracle = new GodotRng(seed);
            oracle.RandfRange(0.92, 1.08); oracle.Randf();
            Assert.Equal(0f, oracle.Randf(), "seed reaches inclusive lower crit boundary");
            var hit = DamageFormula.Damage(actor, target, null, rng);
            Assert.True(!hit.Critical && !hit.Missed, "zero percent never crits, even at zero roll");
            Assert.Equal(oracle.NextUInt(), rng.NextUInt(), "zero endpoint preserves RNG state");
        }

        [LogicTest]
        public static void MagicalHitKeepsTwoDrawsAndNeverCrits()
        {
            var db = new GameDB();
            var actor = BattleUnit.FromHero(db, Hero(1), 0);
            var target = BattleUnit.FromHero(db, Hero(), 1);
            var rng = new GodotRng(CritOneSeed);
            var oracle = new GodotRng(CritOneSeed);
            oracle.RandfRange(0.92, 1.08); oracle.Randf();
            var hit = DamageFormula.Damage(actor, target, new SkillDef { Power = 1, ScalingStat = ScalingStat.Magic }, rng);
            Assert.True(!hit.Critical && !hit.Missed, "magic hits without crit");
            Assert.Equal(oracle.NextUInt(), rng.NextUInt(), "magic consumes no crit draw");
        }

        static void AddShield(BattleUnit unit, StatusEffectType type, int pool = 0, float ratio = 0.5f)
            => unit.ApplyStatus(BattleStatus.FromDef(new StatusDef
            {
                Id = "feedback_" + type, EffectType = type, DurationTurns = 3,
                AbsorbAmount = pool, Magnitude = ratio,
            }, ""));

        static void CheckShield(int mp, int barrier, bool invincible, int hpLoss, int absorbed, int mpLoss, float ratio = 0.5f)
        {
            var db = new GameDB();
            db.Enemies.Add("target", new EnemyDef
            {
                Id = "target", MaxHp = 1000, MaxMp = 100, Attack = 1,
                Speed = 1, Hit = 1, Evade = 0,
            });
            db.Items.Add("bomb", new ItemDef
            {
                Id = "bomb", ItemType = ItemType.Damage, Value = 100,
                Element = Element.None, Target = "single_enemy",
            });
            var setup = new BattleSetup { Seed = 123 };
            setup.Party.Add(Hero());
            setup.EnemyGroup.Add("target");
            setup.Inventory["bomb"] = 1;
            var engine = new BattleEngine(db, setup);
            engine.Start();
            Assert.Equal(BattleEngineState.AwaitingCommand, engine.State, "hero can use damage item");
            var target = engine.Enemies[0];
            target.Mp = mp;
            AddShield(target, StatusEffectType.ManaShield, ratio: ratio);
            if (barrier > 0) AddShield(target, StatusEffectType.Barrier, barrier);
            if (invincible) AddShield(target, StatusEffectType.Invincible);
            int hpBefore = target.Hp;
            var events = engine.Submit(BattleCommand.Item("bomb", target.Id));
            var hit = events.OfType<DamageEvent>().Single(e => e.TargetId == target.Id);
            Assert.Equal(DamageType.Item, hit.Type, "real engine damage item event");
            Assert.Equal(hpLoss, hit.Amount, "event actual HP loss");
            Assert.Equal(hpBefore - hpLoss, hit.HpAfter, "event HP after");
            Assert.Equal(hit.HpAfter, target.Hp, "event HP matches live unit");
            Assert.Equal(mp - mpLoss, target.Mp, "live MP conversion");
            if (invincible && barrier > 0)
                Assert.Equal(barrier, target.Statuses.Single(s => s.EffectType == StatusEffectType.Barrier).BarrierRemaining, "invincibility preserves barrier pool");
            var mpEvents = events.OfType<MpChangeEvent>().Where(e => e.UnitId == target.Id).ToList();
            Assert.Equal(mpLoss > 0 ? 1 : 0, mpEvents.Count, "only actual MP loss emits MP change");
            if (mpLoss > 0)
            {
                Assert.Equal(-mpLoss, mpEvents[0].Delta, "event MP delta");
                Assert.Equal(mp - mpLoss, mpEvents[0].Mp, "event remaining MP");
                Assert.Equal(100, mpEvents[0].MaxMp, "event maximum MP");
            }
            Assert.Equal(absorbed, hit.Absorbed, "event includes barrier and MP absorption");
            Assert.Equal(100, hit.Amount + hit.Absorbed, "nonlethal damage is fully accounted for");
        }

        [LogicTest] public static void ManaShieldEventAccountsForConversion() => CheckShield(100, 0, false, 50, 50, 50);
        [LogicTest] public static void LimitedMpCapsAbsorption() => CheckShield(20, 0, false, 80, 20, 20);
        [LogicTest] public static void EmptyMpDoesNotAbsorb() => CheckShield(0, 0, false, 100, 0, 0);
        [LogicTest] public static void BarrierThenManaShield() => CheckShield(100, 40, false, 30, 70, 30);
        [LogicTest] public static void BarrierThenLimitedMp() => CheckShield(20, 40, false, 40, 60, 20);
        [LogicTest] public static void FullBarrierPreservesMp() => CheckShield(100, 150, false, 0, 100, 0);
        [LogicTest] public static void InvinciblePreservesBarrierAndMp() => CheckShield(100, 40, true, 0, 100, 0);
        [LogicTest] public static void FullManaShieldProducesZeroHpEvent() => CheckShield(100, 0, false, 0, 100, 100, 1);
    }
}
