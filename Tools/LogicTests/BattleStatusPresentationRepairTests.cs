using System;
using System.Collections.Generic;
using System.Linq;
using System.Reflection;
using Abyss.Logic;
using Abyss.Logic.Battle;

namespace Abyss.LogicTests
{
    public static class BattleStatusPresentationRepairTests
    {
        static StatusDef Status(string id, StatusEffectType type, int turns = 5, float magnitude = 0.1f)
            => new StatusDef { Id = id, DisplayName = id, EffectType = type, DurationTurns = turns, Magnitude = magnitude };

        static BattleEngine Engine(out GameDB db, int foes = 2)
        {
            db = new GameDB();
            db.Statuses.Add("provoke", Status("provoke", StatusEffectType.Provoke));
            db.Statuses.Add("poison", Status("poison", StatusEffectType.Poison));
            db.Statuses.Add("defense", Status("defense", StatusEffectType.DefenseUp));
            db.Skills.Add("clean", new SkillDef
            {
                Id = "clean", DisplayName = "clean", Kind = SkillKind.Cleanse,
                TargetType = TargetType.Ally, MpCost = 5,
            });
            db.Skills.Add("scatter", new SkillDef
            {
                Id = "scatter", DisplayName = "scatter", Kind = SkillKind.Damage,
                TargetType = TargetType.Enemy, Scope = Scope.Random, HitCount = 6,
                ScalingStat = ScalingStat.Magic, Power = 1, MpCost = 5,
            });
            db.Items.Add("remedy", new ItemDef { Id = "remedy", DisplayName = "remedy", ItemType = ItemType.Cure });
            db.Enemies.Add("foe", new EnemyDef
            {
                Id = "foe", DisplayName = "foe", MaxHp = 3000, Attack = 10, Magic = 10,
                Defense = 5, Resistance = 5, Speed = 1, Hit = 1,
            });
            var setup = new BattleSetup { Seed = 9 };
            for (int i = 0; i < 2; i++) setup.Party.Add(new HeroCombatSpec
            {
                HeroId = "hero" + i, DisplayName = "hero" + i, Level = 10,
                MaxHp = 1000, Hp = 1000, MaxMp = 100, Mp = 100,
                Attack = 100, Magic = 100, Defense = 5, Resistance = 5, Speed = 1000 - i * 100,
                Hit = 1, Skills = new List<string> { "clean", "scatter" },
            });
            for (int i = 0; i < foes; i++) setup.EnemyGroup.Add("foe");
            setup.Inventory.Add("remedy", 3);
            var engine = new BattleEngine(db, setup);
            engine.Start();
            Assert.Equal(engine.Party[0].Id, engine.ActiveHero.Id, "fixture starts with cleanser/caster");
            return engine;
        }

        static object Call(BattleEngine engine, string method, params object[] args)
            => typeof(BattleEngine).GetMethod(method, BindingFlags.Instance | BindingFlags.NonPublic).Invoke(engine, args);

        static StatusAppliedEvent Apply(BattleEngine engine, BattleUnit source, BattleUnit holder, StatusDef status)
        {
            Assert.True((bool)Call(engine, "ApplyStatusTo", source, holder, status), "status application accepted");
            var events = (List<BattleEvent>)typeof(BattleEngine).GetField("_out", BindingFlags.Instance | BindingFlags.NonPublic).GetValue(engine);
            return events.OfType<StatusAppliedEvent>().Last();
        }

        static IReadOnlyList<BattleEvent> Cleanse(BattleEngine engine, BattleUnit holder, bool item)
        {
            var events = engine.Submit(item ? BattleCommand.Item("remedy", holder.Id) : BattleCommand.Skill("clean", holder.Id));
            Assert.True(!events.OfType<CommandRejectedEvent>().Any(), "cleanse command accepted");
            return events;
        }

        [LogicTest]
        public static void GeneralSkillAndItemCleanseRemoveExternalProvokeAndPreserveBuffs()
        {
            foreach (bool item in new[] { false, true })
            {
                var engine = Engine(out var db);
                var holder = engine.Party[1];
                var applied = Apply(engine, engine.Enemies[0], holder, db.Statuses["provoke"]);
                holder.ApplyStatus(BattleStatus.FromDef(db.Statuses["defense"], holder.Id));
                Assert.True(!applied.Beneficial && !holder.Snapshot().Statuses.Single(s => s.Id == "provoke").Beneficial,
                    "external provoke is an ailment in the applied event and snapshot");
                Assert.Equal(engine.Enemies[0].Id, holder.ProvokedBy(), "external provoke forces the opponent");

                var events = Cleanse(engine, holder, item);
                Assert.True(!holder.Statuses.Any(s => s.Id == "provoke"), "general cleanse removes external provoke");
                Assert.Equal("", holder.ProvokedBy(), "cleanse releases future forced targeting");
                Assert.True(holder.Statuses.Any(s => s.Id == "defense" && s.IsBeneficial), "ordinary buff survives");
                Assert.Equal(1, events.OfType<StatusRemovedEvent>().Count(e => e.UnitId == holder.Id
                    && e.StatusId == "provoke" && e.Reason == StatusRemoveReason.Cleansed), "one cleanse removal, not expiry");
            }
        }

        [LogicTest]
        public static void GeneralCleansesKeepSelfEmptyAndNullSourceTaunts()
        {
            foreach (string sourceKind in new[] { "self", "empty", "null" })
            foreach (bool item in new[] { false, true })
            {
                var engine = Engine(out var db);
                var holder = engine.Party[1];
                string source = sourceKind == "self" ? holder.Id : sourceKind == "empty" ? "" : null;
                holder.ApplyStatus(BattleStatus.FromDef(db.Statuses["provoke"], source));
                holder.ApplyStatus(BattleStatus.FromDef(db.Statuses["poison"], engine.Enemies[0].Id));
                var events = Cleanse(engine, holder, item);
                Assert.True(holder.Statuses.Single().IsBeneficial && holder.IsTaunting, "self/unsourced taunt remains a buff");
                Assert.True(holder.Snapshot().Statuses.Single().Beneficial, "taunt snapshot remains beneficial");
                Assert.Equal("provoke", holder.Statuses.Single().Id, "poison removed, taunt retained");
                Assert.True(events.OfType<StatusRemovedEvent>().Any(e => e.StatusId == "poison" && e.Reason == StatusRemoveReason.Cleansed),
                    "the cleanse executed and removed the accompanying ailment");
                Assert.True(!events.OfType<StatusRemovedEvent>().Any(e => e.StatusId == "provoke"), "taunt was never removed");
            }
        }

        [LogicTest]
        public static void RefreshReclassifiesProvokeBothWaysWithoutChangingOldSnapshots()
        {
            foreach (string finalSource in new[] { "external", "self", "empty" })
            {
                var engine = Engine(out var db);
                var holder = engine.Party[1];
                bool beneficial = finalSource != "external";
                var first = Apply(engine, beneficial ? engine.Enemies[0] : holder, holder, db.Statuses["provoke"]);
                var retained = holder.Statuses.Single();
                var oldSnapshot = holder.Snapshot().Statuses.Single();
                var source = finalSource == "external" ? engine.Enemies[0] : finalSource == "self" ? holder : null;
                var refreshed = Apply(engine, source, holder, Status("provoke", StatusEffectType.Provoke, turns: 2));

                Assert.True(ReferenceEquals(retained, holder.Statuses.Single()), "same-id refresh retains one instance");
                Assert.Equal(source?.Id ?? "", retained.SourceId, "refreshed source installed");
                Assert.Equal(5, retained.TurnsRemaining, "refresh preserves the longer duration");
                Assert.Equal(beneficial, retained.IsBeneficial, "bound classification copied during refresh");
                Assert.True(refreshed.Refreshed && refreshed.Beneficial == beneficial, "refresh event reports the new classification");
                Assert.Equal(beneficial, holder.Snapshot().Statuses.Single().Beneficial, "new snapshot agrees");
                Assert.True(first.Beneficial == !beneficial && oldSnapshot.Beneficial == !beneficial, "old event/snapshot remain independent");

                Cleanse(engine, holder, false);
                Assert.Equal(beneficial, holder.Statuses.Any(s => s.Id == "provoke"), "cleanse uses refreshed classification");
            }
        }

        [LogicTest]
        public static void HolderBindingPreservesBarrierPoolsAndLegacyMaxHpProbe()
        {
            var engine = Engine(out var db);
            var holder = engine.Party[1];
            var barrier = Status("barrier", StatusEffectType.Barrier, magnitude: 0.25f);
            var probe = BattleStatus.FromDef(barrier, "");
            probe.BindTo(holder.MaxHp);
            Assert.Equal(250, probe.BarrierRemaining, "legacy max-HP-only binding remains available");
            holder.ApplyStatus(BattleStatus.FromDef(barrier, holder.Id));
            var attached = holder.Statuses.Single();
            Assert.Equal(250, attached.BarrierRemaining, "holder-aware binding preserves ratio calculation");
            attached.BarrierRemaining = 200;
            holder.ApplyStatus(BattleStatus.FromDef(Status("barrier", StatusEffectType.Barrier, turns: 2, magnitude: 0.1f), holder.Id));
            Assert.Equal(200, attached.BarrierRemaining, "refresh keeps the larger remaining pool");
            Assert.True(attached.IsBeneficial && attached.TurnsRemaining == 5, "barrier buff and duration unchanged");
        }

        [LogicTest]
        public static void RandomRetargetStartSnapshotMatchesHitsWithoutAliasingOrExtraRng()
        {
            var engine = Engine(out var db, foes: 3);
            var actor = engine.ActiveHero;
            var fragile = engine.Enemies[0];
            fragile.Hp = 1;
            var skill = db.Skills["scatter"];
            // A legal already-prepared random allocation: six picks of the first opponent.
            var action = BattleAction.Make(ActionKind.Skill, actor.Id, Enumerable.Repeat(fragile.Id, 6), skill.Id, skill);
            action.Scope = 2;
            engine.Rng.Seed(37);
            var paired = new GodotRng(37);
            var expectedTargets = new List<string> { fragile.Id };
            var expectedAmounts = new List<int> { Math.Min(fragile.Hp, DamageFormula.Damage(actor, fragile, skill, paired).Amount) };
            for (int i = 1; i < 6; i++)
            {
                var target = engine.Enemies[1 + paired.RandiRange(0, 1)];
                expectedTargets.Add(target.Id);
                expectedAmounts.Add(DamageFormula.Damage(actor, target, skill, paired).Amount);
            }

            Call(engine, "BeginBatch");
            Call(engine, "Execute", action);
            var events = (IReadOnlyList<BattleEvent>)Call(engine, "EndBatch");
            var start = events.OfType<ActionStartEvent>().Single();
            var damage = events.OfType<DamageEvent>().Where(e => e.SourceId == actor.Id).ToList();
            Assert.Equal(6, damage.Count, "one lethal hit and five redirected hits resolved");
            Assert.True(damage.Select(e => e.TargetId).SequenceEqual(expectedTargets), "retarget picks retain their RNG order");
            Assert.True(damage.Select(e => e.Amount).SequenceEqual(expectedAmounts), "damage rolls retain their RNG order");
            Assert.Equal(paired.NextUInt(), engine.Rng.NextUInt(), "snapshot repair consumes no additional RNG");
            Assert.True(start.TargetIds.SequenceEqual(damage.Select(e => e.TargetId)), "start targets describe actual resolved hits");
            Assert.True(!ReferenceEquals(start.TargetIds, action.TargetIds), "event does not alias the mutable action");
            Assert.True(events[0] == start && events.Last() is ActionEndEvent, "start/end event order preserved");
            Assert.True(events.Zip(events.Skip(1), (a, b) => b.Seq == a.Seq + 1).All(x => x), "event sequence remains contiguous");
            Assert.True(start.Seq < damage[0].Seq && damage.Last().Seq < events.Last().Seq, "hits stay between start and end");

            var retained = start.TargetIds.ToArray();
            action.TargetIds.Clear();
            action.TargetIds.Add(actor.Id);
            engine.Submit(BattleCommand.Guard());
            Assert.True(start.TargetIds.SequenceEqual(retained), "action reuse and a later batch cannot rewrite the prior snapshot");
        }

        [LogicTest]
        public static void RandomSubmitOmitsUnexecutedPicksAfterLastOpponentFalls()
        {
            var engine = Engine(out var db);
            var actor = engine.ActiveHero;
            foreach (var enemy in engine.Enemies) enemy.Hp = 1;
            var events = engine.Submit(BattleCommand.Skill("scatter"));
            Assert.True(!events.OfType<CommandRejectedEvent>().Any(), "public random command accepted");
            var start = events.OfType<ActionStartEvent>().Single(e => e.ActorId == actor.Id);
            var damage = events.OfType<DamageEvent>().Where(e => e.SourceId == actor.Id).ToList();
            Assert.Equal(2, damage.Count, "each living opponent receives its lethal hit");
            Assert.True(start.TargetIds.SequenceEqual(damage.Select(e => e.TargetId)), "no dead-target placeholders remain in returned snapshot");
            Assert.Equal(6, start.HitCount, "authored hit budget remains available for presentation");
            Assert.True(start.Seq < damage[0].Seq, "public batch still starts the action before its damage");
            Assert.Equal(BattleResult.Victory, engine.Outcome.Result, "battle resolution is unchanged");
        }
    }
}
