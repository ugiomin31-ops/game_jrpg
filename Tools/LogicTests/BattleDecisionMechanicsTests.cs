// O6 weakness chain, O7 TP carry / town reset and O8 phase-limited boss crowd-control resistance.
using System;
using System.Collections.Generic;
using System.Linq;
using System.Reflection;
using Abyss.Logic;
using Abyss.Logic.Battle;
using Abyss.Logic.Dungeon;
using Abyss.Logic.Game;
using Newtonsoft.Json.Linq;

namespace Abyss.LogicTests
{
    public static class BattleDecisionMechanicsTests
    {
        const int Slash = (int)Element.Slash, Fire = (int)Element.Fire;

        // --- fixtures ------------------------------------------------------------------------------------

        static HeroCombatSpec Hero(string id, int speed = 1000, int hp = 1000, int tp = 0, int tpStart = 0) => new HeroCombatSpec
        {
            HeroId = id, DisplayName = id, Level = 10, MaxHp = 1000, Hp = hp, MaxMp = 500, Mp = 500,
            Attack = 200, Magic = 150, Defense = 5, Resistance = 5, Speed = speed, Hit = 2, Crit = 0, Tp = tp, TpStart = tpStart,
            Skills = AllSkills.ToList(),
        };

        static SkillDef Skill(string id, SkillKind kind, Element element, Scope scope = Scope.Single, int hits = 1,
            TargetType target = TargetType.Enemy, string status = null, float chance = 0f, params string[] extra) => new SkillDef
        {
            Id = id, DisplayName = id, Kind = kind, Element = element, Scope = scope, HitCount = hits, ScalingStat = ScalingStat.Attack,
            TargetType = target, Power = 1f, MpCost = 0, StatusEffect = status, StatusChance = chance, ExtraStatuses = extra.ToList(),
        };

        static EnemyDef Enemy(string id, int hp = 100000, int shield = 0, int speed = 1, int attack = 5, bool boss = false, params int[] weak)
        {
            var def = new EnemyDef { Id = id, DisplayName = id, MaxHp = hp, Attack = attack, Magic = 5, Defense = 20, Resistance = 10,
                Speed = speed, Hit = 1, Evade = 0, BreakShield = shield, IsBoss = boss, Rank = boss ? 2 : 0 };
            def.Weaknesses.AddRange(weak);
            return def;
        }

        static readonly string[] AllSkills = { "slash1", "slash3", "slash_all", "plain", "heal", "buff", "stun_ray", "stun_chance", "dual_cc", "poison_ray" };

        static GameDB Db()
        {
            var db = new GameDB();
            foreach (var e in new[]
            {
                Enemy("dummy", weak: Slash),               // weak to Slash, no shield
                Enemy("dummy2", weak: Slash),
                Enemy("pip", shield: 1, weak: Slash),      // breaks on one weakness hit
                Enemy("softie", hp: 400, weak: Slash),
                Enemy("plainy"),
                Enemy("fire_weak", weak: Fire),
                Enemy("brute", attack: 5000, speed: 2000),
                Enemy("grunt"),
                Enemy("lord", boss: true),
                Enemy("warden", boss: true),
                Enemy("stubborn", boss: true),
            }) db.Enemies.Add(e.Id, e);
            db.Enemies["warden"].Gimmicks.Add("cc_immune");
            db.Enemies["stubborn"].Gimmicks.Add("cc_resist");
            db.Enemies["lord"].Gimmicks.Add("dot_resist");
            db.Enemies["lord"].Phases.Add(new BossPhase { HpBelow = 0.5f, ActionsPerTurn = 1, Line = "phase two" });
            foreach (var s in new[]
            {
                Skill("slash1", SkillKind.Damage, Element.Slash),
                Skill("slash3", SkillKind.Damage, Element.Slash, hits: 3),
                Skill("slash_all", SkillKind.Damage, Element.Slash, Scope.All),
                Skill("plain", SkillKind.Damage, Element.None),
                Skill("heal", SkillKind.Heal, Element.None, target: TargetType.Ally),
                Skill("buff", SkillKind.Buff, Element.None, target: TargetType.Self, status: "attack_up"),
                Skill("stun_ray", SkillKind.Debuff, Element.None, status: "stun"),
                Skill("stun_chance", SkillKind.Debuff, Element.None, status: "stun", chance: 0.6f),
                Skill("dual_cc", SkillKind.Debuff, Element.None, status: "stun", extra: "sleep"),
                Skill("poison_ray", SkillKind.Debuff, Element.None, status: "poison"),
            }) db.Skills.Add(s.Id, s);
            db.Items.Add("bomb", new ItemDef { Id = "bomb", DisplayName = "Bomb", ItemType = ItemType.Damage, Value = 100, Element = Element.Fire, Target = "all_enemies" });
            db.Items.Add("potion", new ItemDef { Id = "potion", DisplayName = "Potion", ItemType = ItemType.Healing, HealAmount = 120, Target = "single_ally" });
            db.Items.Add("ether", new ItemDef { Id = "ether", DisplayName = "Ether", ItemType = ItemType.MpRestore, Value = 50, Target = "single_ally" });
            db.Items.Add("flash", new ItemDef { Id = "flash", DisplayName = "Flash", ItemType = ItemType.Buff, StatusId = "stun", Target = "single_enemy" });
            foreach (var st in TestMain.DB.Statuses) db.Statuses.Add(st.Key, st.Value);
            return db;
        }

        static BattleEngine Engine(int seed, IEnumerable<string> enemies, IEnumerable<string> known = null, GameDB db = null,
            BattleKind kind = BattleKind.Random, params HeroCombatSpec[] heroes)
        {
            var setup = new BattleSetup { Seed = seed, Kind = kind };
            if (heroes.Length == 0) heroes = new[] { Hero("hero0", 1000), Hero("hero1", 999) };
            setup.Party.AddRange(heroes);
            setup.EnemyGroup.AddRange(enemies);
            if (known != null) foreach (var k in known) setup.KnownWeaknesses.Add(k);
            setup.Inventory["bomb"] = 9; setup.Inventory["potion"] = 9; setup.Inventory["ether"] = 9; setup.Inventory["flash"] = 60;
            return new BattleEngine(db ?? Db(), setup);
        }

        static BattleEngine Started(BattleEngine e)
        {
            e.Start();
            Assert.Equal(BattleEngineState.AwaitingCommand, e.State, "a hero awaits a command");
            return e;
        }

        static List<ChainChangedEvent> Chains(IEnumerable<BattleEvent> events) => events.OfType<ChainChangedEvent>().ToList();

        /// <summary>Events of the active hero's own action (ActionStart .. ActionEnd) within a submitted batch.</summary>
        static List<BattleEvent> OwnAction(IReadOnlyList<BattleEvent> events, string actorId)
        {
            int start = -1;
            for (int i = 0; i < events.Count; i++) if (events[i] is ActionStartEvent a && a.ActorId == actorId) { start = i; break; }
            Assert.True(start >= 0, "action of " + actorId + " found");
            var list = new List<BattleEvent>();
            for (int i = start; i < events.Count; i++)
            {
                list.Add(events[i]);
                if (events[i] is ActionEndEvent end && end.ActorId == actorId) break;
            }
            return list;
        }

        /// <summary>Submits for the active hero and returns that hero's own action events.</summary>
        static List<BattleEvent> Act(BattleEngine e, BattleCommand cmd)
        {
            string actor = e.ActiveHero.Id;
            return OwnAction(e.Submit(cmd), actor);
        }

        static int TpDelta(IEnumerable<BattleEvent> events, string unitId) => events.OfType<TpChangeEvent>().Where(t => t.UnitId == unitId).Sum(t => t.Delta);

        static void SetChain(BattleEngine e, int value)
            => typeof(BattleEngine).GetField("_chain", BindingFlags.Instance | BindingFlags.NonPublic).SetValue(e, value);

        /// <summary>The next Randf of a generator, without advancing it.</summary>
        static float PeekRandf(GodotRng rng)
        {
            var copy = new GodotRng(0);
            foreach (var f in typeof(GodotRng).GetFields(BindingFlags.Instance | BindingFlags.NonPublic)) f.SetValue(copy, f.GetValue(rng));
            return copy.Randf();
        }

        static string RngState(GodotRng rng)
            => string.Join(",", typeof(GodotRng).GetFields(BindingFlags.Instance | BindingFlags.NonPublic).Select(f => f.GetValue(rng).ToString()));

        static BattleUnit Foe(BattleEngine e, string defId, int nth = 0) => e.Enemies.Where(u => u.DefId == defId).ElementAt(nth);

        // --- O6 chain ------------------------------------------------------------------------------------

        [LogicTest]
        public static void ChainAdvancesOncePerWeakActionAndCapsAtFive()
        {
            var e = Started(Engine(21, new[] { "dummy", "plainy" }));
            var dummy = Foe(e, "dummy");
            Assert.Equal(0, e.Chain, "battles start at chain 0");
            var all = new List<BattleEvent>();
            for (int i = 1; i <= 7; i++)
            {
                var evs = e.Submit(BattleCommand.Skill(i == 2 ? "slash3" : "slash1", dummy.Id));
                all.AddRange(evs);
                var mine = Chains(evs);
                int expected = Math.Min(BattleEngine.ChainMax, i);
                Assert.Equal(expected, e.Chain, $"action {i}: chain {expected}");
                if (i <= BattleEngine.ChainMax)
                    Assert.True(mine.Count == 1 && mine[0].OldValue == i - 1 && mine[0].NewValue == i, $"action {i}: one ChainChanged({i - 1},{i})" + (i == 2 ? " for three weak hits" : ""));
                else Assert.Equal(0, mine.Count, $"action {i}: no event at the cap");
            }
            // Every chain change comes right before the party action's ActionEnd (once per action, after it resolved).
            for (int i = 0; i < all.Count; i++)
                if (all[i] is ChainChangedEvent)
                    Assert.True(all[i + 1] is ActionEndEvent end && e.Party.Any(p => p.Id == end.ActorId), "chain changes close a party action");
        }

        [LogicTest]
        public static void ChainResetsOnlyOnDamagingActionsWithoutWeakness()
        {
            var e = Started(Engine(22, new[] { "dummy", "plainy", "fire_weak" }));
            var dummy = Foe(e, "dummy");
            var plainy = Foe(e, "plainy");
            e.Submit(BattleCommand.Skill("slash1", dummy.Id));
            e.Submit(BattleCommand.Skill("slash1", dummy.Id));
            Assert.Equal(2, e.Chain, "two weak actions");

            // Non-damaging actions and enemy turns never touch the chain.
            foreach (var cmd in new Func<BattleUnit, BattleCommand>[]
            {
                h => BattleCommand.Skill("heal", h.Id), h => BattleCommand.Skill("buff"), h => BattleCommand.Guard(),
                h => BattleCommand.Item("potion", h.Id), h => BattleCommand.Item("ether", h.Id), h => BattleCommand.Skill("stun_ray", plainy.Id),
            })
            {
                var evs = e.Submit(cmd(e.ActiveHero));
                Assert.True(!(evs.Count == 1 && evs[0] is CommandRejectedEvent), "accepted");
                Assert.Equal(0, Chains(evs).Count, "non-damaging action / enemy turns leave the chain");
                Assert.Equal(2, e.Chain, "still 2");
            }

            // A damaging action with no weakness hit resets: plain attack, non-weak skill, non-weak damage item.
            var reset = e.Submit(BattleCommand.Attack(dummy.Id));
            Assert.True(Chains(reset).Single().OldValue == 2 && Chains(reset).Single().NewValue == 0 && e.Chain == 0, "plain (non-elemental) attack resets 2 -> 0");
            e.Submit(BattleCommand.Skill("slash1", dummy.Id));
            Assert.Equal(1, e.Chain, "advanced again");
            e.Submit(BattleCommand.Skill("slash1", plainy.Id));
            Assert.Equal(0, e.Chain, "slash on a non-weak enemy resets");
            Assert.Equal(0, Chains(e.Submit(BattleCommand.Skill("plain", plainy.Id))).Count, "reset at 0 emits nothing");

            // Damaging items: Fire bomb hits fire_weak (weak) -> +1 even though the others are neutral.
            var bomb = e.Submit(BattleCommand.Item("bomb"));
            Assert.True(e.Chain == 1 && Chains(bomb).Single().NewValue == 1, "damaging item with a weakness hit advances");
            Foe(e, "fire_weak").Hp = 0;
            e.Submit(BattleCommand.Item("bomb"));
            Assert.Equal(0, e.Chain, "damaging item without a weakness hit resets");
        }

        [LogicTest]
        public static void AoeAdvancesOnceAndFleeAttemptKeepsChain()
        {
            var e = Started(Engine(23, new[] { "dummy", "dummy2", "plainy" }));
            var evs = e.Submit(BattleCommand.Skill("slash_all"));
            Assert.Equal(2, OwnAction(evs, e.Party[0].Id).OfType<DamageEvent>().Count(d => d.Effectiveness == Effectiveness.Weak), "two weakness hits");
            Assert.True(e.Chain == 1 && Chains(evs).Count == 1, "an AoE with several weakness hits advances once");

            // A failed flee attempt leaves the chain (seeded search for a failing attempt).
            bool failedSeen = false;
            for (int seed = 1; seed <= 200 && !failedSeen; seed++)
            {
                var f = Started(Engine(seed, new[] { "plainy" }, heroes: new[] { Hero("slow0", 1), Hero("slow1", 1) }));
                SetChain(f, 3);
                var res = f.Submit(BattleCommand.Flee());
                var flee = res.OfType<FleeEvent>().Single();
                if (flee.Success) { Assert.Equal(0, f.Chain, "a fled battle ends and resets the chain"); continue; }
                failedSeen = true;
                Assert.True(f.Chain == 3 && !Chains(res).Any(), "a failed flee attempt keeps the chain");
            }
            Assert.True(failedSeen, "found a failed flee attempt");
        }

        [LogicTest]
        public static void WeaknessHitsCarryThePreActionChainBonus()
        {
            var e = Started(Engine(24, new[] { "dummy" }, new[] { "dummy:" + Slash }));
            var dummy = Foe(e, "dummy");
            // Weak per hit at chain 0: 189 x roll x 1.5 -> 261..306 (ActionPreviewTests).
            var chain0 = e.PreviewAction(e.UnitIndexOf(e.ActiveHero), BattleCommand.Skill("slash1"), e.UnitIndexOf(dummy)).Targets.Single();
            Assert.True(chain0.Min == 261 && chain0.Max == 306, $"chain 0 weak hit 261..306 ({chain0.Min}..{chain0.Max})");
            e.Submit(BattleCommand.Skill("slash1", dummy.Id));
            e.Submit(BattleCommand.Skill("slash1", dummy.Id));
            Assert.Equal(2, e.Chain, "chain 2");
            var p = e.PreviewAction(e.UnitIndexOf(e.ActiveHero), BattleCommand.Skill("slash3"), e.UnitIndexOf(dummy)).Targets.Single();
            double low = DamageFormula.LowestRoll(DamageFormula.DamageVariance), high = DamageFormula.HighestRoll(DamageFormula.DamageVariance);
            int lo = DamageFormula.FinalAmount(189 * low * (1.5 * BattleEngine.ChainFactor(2)));
            int hi = DamageFormula.FinalAmount(189 * high * (1.5 * BattleEngine.ChainFactor(2)));
            Assert.True(lo > 306, "chain 2 lifts the weak hit above the chain-0 maximum: " + lo);
            Assert.True(p.Min == 3 * lo && p.Max == 3 * hi, $"preview: three hits at the pre-action chain 2 ({p.Min}..{p.Max} vs {3 * lo}..{3 * hi})");
            string actor = e.ActiveHero.Id;
            var hits = OwnAction(e.Submit(BattleCommand.Skill("slash3", dummy.Id)), actor).OfType<DamageEvent>().ToList();
            Assert.Equal(3, hits.Count, "three hits");
            foreach (var h in hits) Assert.True(h.Amount >= lo && h.Amount <= hi, $"every hit uses the pre-action chain 2 bonus ({h.Amount} in {lo}..{hi})");
            Assert.Equal(3, e.Chain, "+1 after the action");
            // Non-weak hits get no bonus.
            var plain = e.PreviewAction(e.UnitIndexOf(e.ActiveHero), BattleCommand.Skill("plain"), e.UnitIndexOf(dummy)).Targets.Single();
            Assert.True(plain.Min == 174 && plain.Max == 204, $"neutral hits unaffected by the chain ({plain.Min}..{plain.Max})");
            // Damaging items: Fire bomb on a known-weak target, chain 3 -> 100 x 1.5 x 1.3.
            var f = Started(Engine(25, new[] { "fire_weak" }, new[] { "fire_weak:" + Fire }));
            SetChain(f, 3);
            var bombPreview = f.PreviewAction(f.UnitIndexOf(f.ActiveHero), BattleCommand.Item("bomb"), -1).Targets.Single();
            int expectedBomb = DamageFormula.FixedItemAmount(Db().Items["bomb"], 1.5 * BattleEngine.ChainFactor(3), false);
            Assert.True(bombPreview.Min == expectedBomb && expectedBomb == 195, "item preview includes the chain: " + bombPreview.Min);
            Assert.Equal(expectedBomb, Act(f, BattleCommand.Item("bomb")).OfType<DamageEvent>().Single().Amount, "damaging item carries the chain bonus");
        }

        [LogicTest]
        public static void PreviewChainMultiplierIsForKnownWeaknessOnly()
        {
            var e = Started(Engine(26, new[] { "dummy", "dummy2" }, new[] { "dummy:" + Slash }));
            SetChain(e, 4);
            int actor = e.UnitIndexOf(e.ActiveHero);
            var known = e.PreviewAction(actor, BattleCommand.Skill("slash1"), e.UnitIndexOf(Foe(e, "dummy"))).Targets.Single();
            var unknown = e.PreviewAction(actor, BattleCommand.Skill("slash1"), e.UnitIndexOf(Foe(e, "dummy2"))).Targets.Single();
            double low = DamageFormula.LowestRoll(DamageFormula.DamageVariance);
            Assert.Equal(PreviewAffinity.Weak, known.Affinity, "known weak");
            Assert.Equal(DamageFormula.FinalAmount(189 * low * (1.5 * BattleEngine.ChainFactor(4))), known.Min, "known weakness: chain multiplier included");
            Assert.Equal(PreviewAffinity.Unknown, unknown.Affinity, "dummy2's real weakness is undiscovered");
            Assert.True(unknown.Min == 174 && unknown.Max == 204, $"unknown affinity stays neutral, no chain ({unknown.Min}..{unknown.Max})");
            var all = e.PreviewAction(actor, BattleCommand.Skill("slash_all"), -1);
            Assert.True(all.For(Foe(e, "dummy").Id).Min == known.Min && all.For(Foe(e, "dummy2").Id).Min == 174, "AoE rows: chain only on the known-weak row");

            // AUTO reads knowledge only: an undiscovered weakness changes nothing at any chain value.
            var dbWeak = Db();
            var dbPlain = Db();
            dbPlain.Enemies["dummy2"].Weaknesses.Clear();
            foreach (int chain in new[] { 0, 3, 5 })
            {
                var a = Started(Engine(27, new[] { "dummy2", "plainy" }, db: dbWeak));
                var b = Started(Engine(27, new[] { "dummy2", "plainy" }, db: dbPlain));
                SetChain(a, chain); SetChain(b, chain);
                Assert.Equal(b.SuggestCommand(b.ActiveHero).ToString(), a.SuggestCommand(a.ActiveHero).ToString(), $"chain {chain}: AUTO ignores the undiscovered weakness");
                var pa = a.PreviewAction(a.UnitIndexOf(a.ActiveHero), BattleCommand.Skill("slash_all"), -1);
                var pb = b.PreviewAction(b.UnitIndexOf(b.ActiveHero), BattleCommand.Skill("slash_all"), -1);
                Assert.True(pa.Targets.Select(t => t.Min + ":" + t.Max + ":" + t.Affinity).SequenceEqual(pb.Targets.Select(t => t.Min + ":" + t.Max + ":" + t.Affinity)), $"chain {chain}: previews identical");
            }
        }

        [LogicTest]
        public static void ChainBreakBonusGivesTpPerBrokenEnemyFromChainThree()
        {
            foreach (int chain in new[] { 2, 3 })
            {
                var e = Started(Engine(28, new[] { "dummy", "pip", "pip" }, heroes: new[] { Hero("hero0", 1000), Hero("hero1", 999), Hero("down", 998, hp: 0) }));
                SetChain(e, chain);
                foreach (var p in e.Party) p.Tp = 0;
                string actor = e.ActiveHero.Id, other = e.Party.First(p => p.Id != actor && p.IsAlive).Id;
                var mine = OwnAction(e.Submit(BattleCommand.Skill("slash_all")), actor);
                Assert.Equal(2, mine.OfType<BreakEvent>().Count(), "both pips break");
                int perBreak = BattleEngine.TpOnBreak + (chain >= BattleEngine.ChainBreakFrom ? BattleEngine.TpOnChainBreak : 0);
                Assert.Equal(2 * perBreak, TpDelta(mine, other), $"chain {chain}: ally gains {perBreak} per broken enemy");
                Assert.Equal(2 * perBreak + BattleEngine.TpOnDeal, TpDelta(mine, actor), $"chain {chain}: actor gains the same plus dealing TP");
                Assert.Equal(0, e.Party.Single(p => p.DefId == "down").Tp, "KO'd members gain nothing");
                Assert.Equal(chain + 1, e.Chain, "AoE advanced once");
            }

            // Killed before the shield breaks: the hit counts as a weakness hit, but there is no break (and no bonus).
            var k = Started(Engine(29, new[] { "pip", "dummy" }));
            SetChain(k, 3);
            foreach (var p in k.Party) p.Tp = 0;
            var pip = Foe(k, "pip");
            pip.Hp = 1;
            string a0 = k.ActiveHero.Id, a1 = k.Party.First(p => p.Id != a0).Id;
            var kill = OwnAction(k.Submit(BattleCommand.Skill("slash1", pip.Id)), a0);
            Assert.True(!pip.IsAlive && !kill.OfType<BreakEvent>().Any(), "killed outright, no BREAK");
            Assert.Equal(0, TpDelta(kill, a1), "no break TP without a break");
            Assert.Equal(4, k.Chain, "the killing weakness hit still advances the chain");
        }

        [LogicTest]
        public static void ChainResetsAtBattleEndAndEventsAreImmutable()
        {
            var e = Started(Engine(30, new[] { "softie" }));
            var softie = Foe(e, "softie");
            e.Submit(BattleCommand.Skill("slash1", softie.Id));
            Assert.Equal(1, e.Chain, "chain 1");
            var end = e.Submit(BattleCommand.Skill("slash3", softie.Id));
            Assert.Equal(BattleEngineState.Ended, e.State, "softie falls");
            var changes = Chains(end);
            Assert.True(changes.Count == 2 && changes[0].NewValue == 2 && changes[1].OldValue == 2 && changes[1].NewValue == 0, "advance, then reset at battle end");
            int resetIndex = end.ToList().IndexOf(changes[1]);
            Assert.True(end[resetIndex + 1] is BattleEndEvent, "the end-of-battle reset precedes BattleEnd");
            Assert.Equal(0, e.Chain, "chain is battle-local");
            foreach (var prop in typeof(ChainChangedEvent).GetProperties().Where(p => p.Name != "Seq"))
                Assert.True(prop.GetSetMethod(true) == null, "ChainChangedEvent." + prop.Name + " has no setter");
            Assert.True(typeof(ChainChangedEvent).GetFields(BindingFlags.Instance | BindingFlags.Public).Length == 0, "no public mutable fields");
        }

        // --- O7 TP carry ---------------------------------------------------------------------------------

        [LogicTest]
        public static void BattleStartTpIsMaxOfCarriedAndGear()
        {
            var e = Engine(31, new[] { "plainy" }, heroes: new[]
            {
                Hero("carried", tp: 50, tpStart: 30), Hero("gear", tp: 20, tpStart: 30), Hero("over", tp: 150), Hero("ko", hp: 0, tp: 50, tpStart: 30),
            });
            Assert.Equal(50, e.Party[0].Tp, "carried 50 beats gear 30");
            Assert.Equal(30, e.Party[1].Tp, "gear 30 beats carried 20");
            Assert.Equal(100, e.Party[2].Tp, "clamped to 100");
            Assert.Equal(0, e.Party[3].Tp, "KO'd heroes start at 0");
        }

        [LogicTest]
        public static void TpIsKeptThroughVictoryFleeAndDefeat()
        {
            // Victory: no end-of-battle TP wipe, outcome reports the final TP.
            var win = Engine(32, new[] { "softie" }, heroes: new[] { Hero("a", tp: 60), Hero("b", 999, tp: 10) });
            var events = BattleTestUtil.RunAuto(win);
            Assert.Equal(BattleResult.Victory, win.Outcome.Result, "won");
            foreach (var h in win.Party) Assert.Equal(h.Tp, win.Outcome.FinalTp[h.DefId], "FinalTp " + h.DefId);
            Assert.True(win.Outcome.FinalTp["a"] >= 60, "carried TP kept (and grown): " + win.Outcome.FinalTp["a"]);
            int endIndex = events.FindIndex(x => x is BattleEndEvent);
            int lastAction = events.FindLastIndex(x => x is ActionEndEvent);
            Assert.True(!events.Skip(lastAction).Take(endIndex - lastAction).OfType<TpChangeEvent>().Any(), "no TP reset events at battle end");

            // Flee: TP kept.
            bool fled = false;
            for (int seed = 1; seed <= 50 && !fled; seed++)
            {
                var run = Started(Engine(seed, new[] { "plainy" }, heroes: new[] { Hero("a", tp: 45), Hero("b", 999, tp: 5) }));
                while (run.State == BattleEngineState.AwaitingCommand) run.Submit(BattleCommand.Flee());
                if (run.Outcome.Result != BattleResult.Fled) continue;
                fled = true;
                Assert.True(run.Outcome.FinalTp["a"] >= 45 && run.Outcome.FinalTp["a"] == run.Party[0].Tp, "fled: TP kept " + run.Outcome.FinalTp["a"]);
            }
            Assert.True(fled, "a flee succeeded");

            // Defeat: everyone is down, so every FinalTp is 0 (OnUnitDown already zeroes it).
            var lose = Engine(33, new[] { "brute" }, heroes: new[] { Hero("a", hp: 10, tp: 70), Hero("b", 999, hp: 10, tp: 70) });
            BattleTestUtil.RunAuto(lose);
            Assert.Equal(BattleResult.Defeat, lose.Outcome.Result, "lost");
            Assert.True(lose.Outcome.FinalTp.Count == 2 && lose.Outcome.FinalTp.Values.All(v => v == 0), "defeat: KO'd heroes carry 0");
        }

        static GameState Campaign(int tp = 40)
        {
            var db = TestMain.DB;
            var state = GameState.NewGame(db, Difficulty.Normal);
            HunterRoster.Recruit(db, state, "h_bora");
            Assert.True(state.Reserve.Count > 0, "a reserve hunter exists");
            foreach (var h in state.AllHunters()) h.Tp = tp;
            return state;
        }

        static void AllTp(GameState state, int expected, string why)
        {
            foreach (var h in state.AllHunters()) Assert.Equal(expected, h.Tp, why + " (" + h.Id + (state.InParty(h.Id) ? "" : ", reserve") + ")");
        }

        [LogicTest]
        public static void OutcomeTpReachesHeroStateAndCombatSpec()
        {
            var db = TestMain.DB;
            var state = Campaign(0);
            var a = state.Party[0];
            var b = state.Party[1];
            var c = state.Party[2];
            var outcome = new BattleOutcome { Result = BattleResult.Fled };
            outcome.FinalHp[a.Id] = 10; outcome.FinalTp[a.Id] = 73;
            outcome.FinalHp[b.Id] = 0; outcome.FinalTp[b.Id] = 55; // inconsistent input: KO'd -> 0
            outcome.FinalTp[c.Id] = 400;
            PartyStats.ApplyBattleOutcome(db, state, outcome);
            Assert.Equal(73, a.Tp, "fled outcome TP stored");
            Assert.Equal(0, b.Tp, "KO'd hero stores 0");
            Assert.Equal(HeroState.MaxTp, c.Tp, "clamped to 100");
            state.Party[3].Tp = 12;
            PartyStats.ApplyBattleOutcome(db, state, new BattleOutcome { Result = BattleResult.Fled });
            Assert.Equal(12, state.Party[3].Tp, "an outcome without the hero keeps its TP");
            Assert.Equal(73, PartyStats.BuildCombatSpec(db, state, a.Id).Tp, "combat spec carries TP");
            Assert.Equal(0, PartyStats.BuildCombatSpec(db, state, b.Id).Tp, "KO'd spec carries 0");
            var setup = PartyStats.BuildBattleSetup(db, state, BattleKind.Random, new[] { "slime" }, 1f, db.Floors[0].Id, 5);
            var engine = new BattleEngine(db, setup);
            Assert.Equal(Math.Max(73, setup.Party[0].TpStart), engine.Party[0].Tp, "battle starts from the carried TP");
        }

        [LogicTest]
        public static void TpSurvivesSavesAndOldSavesLoadAtZero()
        {
            var db = TestMain.DB;
            var state = Campaign(37);
            state.Reserve[0].Tp = 12;
            var loaded = SaveCodec.Deserialize(SaveCodec.Serialize(state), db);
            Assert.True(loaded.Party.All(h => h.Tp == 37) && loaded.Reserve[0].Tp == 12, "TP round-trips (party and reserve)");

            // Old save: no "tp" key anywhere.
            var root = JObject.Parse(SaveCodec.Serialize(state));
            int removed = 0;
            foreach (var list in new[] { "party", "reserve" })
                foreach (JObject hero in (JArray)root[list]) if (hero.Remove("tp")) removed++;
            Assert.Equal(state.AllHunters().Count(), removed, "every hunter had a tp field");
            var old = SaveCodec.Deserialize(root.ToString(), db);
            AllTp(old, 0, "missing field loads as 0");

            // Clamp on load: above 100, negative, and KO'd heroes.
            var bad = JObject.Parse(SaveCodec.Serialize(state));
            var party = (JArray)bad["party"];
            party[0]["tp"] = 250;
            party[1]["tp"] = -9;
            party[2]["tp"] = 40; party[2]["hp"] = 0;
            ((JArray)bad["reserve"])[0]["tp"] = 101;
            var clamped = SaveCodec.Deserialize(bad.ToString(), db);
            Assert.Equal(100, clamped.Party[0].Tp, "clamped down to 100");
            Assert.Equal(0, clamped.Party[1].Tp, "negative clamped to 0");
            Assert.Equal(0, clamped.Party[2].Tp, "KO'd hero repaired to 0");
            Assert.Equal(100, clamped.Reserve[0].Tp, "reserve clamped too");
            Assert.Equal(SaveCodec.CurrentVersion, (int)JObject.Parse(SaveCodec.Serialize(clamped))["version"], "save version unchanged");
        }

        [LogicTest]
        public static void EveryTownRouteAndInnRestClearsTpForTheWholeRoster()
        {
            var db = TestMain.DB;

            var s = Campaign();
            var run = new DungeonRun(db, s, 0, ArrivalMode.Town);
            foreach (var h in s.AllHunters()) h.Tp = 40;
            run.ReturnToTown();
            AllTp(s, 0, "DungeonRun.ReturnToTown (return stone / escape)");

            s = Campaign();
            run = new DungeonRun(db, s, 0, ArrivalMode.Town);
            foreach (var h in s.AllHunters()) h.Tp = 40;
            var grid = run.Grid;
            s.Position = grid.FindCells('<').Single();
            var up = run.Interact();
            Assert.True(up.ReturnToTown, "B1F stairs up lead to town");
            AllTp(s, 0, "stairs back to town");

            s = Campaign(); GameFlow.EnterTown(db, s); AllTp(s, 0, "EnterTown(db)");
            s = Campaign(); GameFlow.EnterTown(s); AllTp(s, 0, "EnterTown()");
            s = Campaign(); GameFlow.CompletePrologue(s); AllTp(s, 0, "prologue");
            s = Campaign(); GameFlow.MarkEndingSeen(s); AllTp(s, 0, "ending");
            s = Campaign(); s.Flags.Add(GameFlow.FlagDefeatPending); GameFlow.RecoverFromDefeat(db, s); AllTp(s, 0, "defeat recovery");
            s = Campaign(); s.Gold = 100000;
            Assert.True(TownServices.RestAtInn(db, s).Success, "paid inn");
            AllTp(s, 0, "successful inn rest");
            s = Campaign(); s.Gold = 0;
            Assert.True(!TownServices.RestAtInn(db, s).Success, "inn refused");
            AllTp(s, 40, "failed inn payment changes nothing");

            // Battle settlements that put the party in town: escape item outcome, and the ending boss.
            s = Campaign();
            run = new DungeonRun(db, s, 0, ArrivalMode.Town);
            var request = new DungeonBattleRequest { Kind = BattleKind.Random, FloorId = db.Floors[0].Id, Cell = s.Position, RetreatCell = s.Position, EnemyGroup = { "slime" } };
            s.PendingBattle = request;
            foreach (var h in s.AllHunters()) h.Tp = 40;
            var escape = new BattleOutcome { Result = BattleResult.Fled, EscapedDungeon = true };
            foreach (var h in s.Party) { escape.FinalHp[h.Id] = h.Hp; escape.FinalTp[h.Id] = 40; }
            Assert.True(run.ResolveBattle(escape).ReturnToTown, "escaped to town");
            AllTp(s, 0, "escape outcome");

            s = Campaign();
            int endIndex = db.Floors.FindIndex(f => f.Ending);
            var endFloor = db.Floors[endIndex];
            var bossCell = DungeonGrid.Parse(endFloor).FindCells('B').First();
            s.Location = GameLocation.Dungeon; s.FloorIndex = endIndex; s.DeepestFloor = endIndex; s.Position = bossCell;
            s.PendingBattle = new DungeonBattleRequest { Kind = BattleKind.Boss, FloorId = endFloor.Id, Cell = bossCell, RetreatCell = bossCell, EnemyGroup = new List<string>(endFloor.BossGroup) };
            run = new DungeonRun(db, s, endIndex, ArrivalMode.Resume);
            var win = new BattleOutcome { Result = BattleResult.Victory };
            foreach (var h in s.Party) { win.FinalHp[h.Id] = h.Hp; win.FinalTp[h.Id] = 90; }
            var resolution = run.ResolveBattle(win);
            Assert.True(resolution.Ending && s.Location == GameLocation.Town, "final boss ends the story in town");
            AllTp(s, 0, "ending settlement");
        }

        [LogicTest]
        public static void SpringsTentsHealingItemsAndRestorePartyKeepTp()
        {
            var db = TestMain.DB;
            int springFloor = db.Floors.FindIndex(f => DungeonGrid.Parse(f).FindCells('H').Any());
            Assert.True(springFloor >= 0, "some floor has a spring");
            var s = Campaign();
            var floor = db.Floors[springFloor];
            s.Location = GameLocation.Dungeon; s.FloorIndex = springFloor; s.DeepestFloor = springFloor;
            var spring = DungeonGrid.Parse(floor).FindCells('H').First();
            s.Position = spring;
            var run = new DungeonRun(db, s, springFloor, ArrivalMode.Resume);
            Assert.True(run.CanAct && s.Position == spring, "standing on the spring");
            foreach (var h in s.Party) h.Hp = 1;
            for (int turn = 0; turn < 4 && run.Grid.IsClosedDoor(s.Position.Step(s.Facing)); turn++) run.Turn(1);
            var used = run.Interact();
            Assert.Equal(DungeonEffect.Spring, used.Effect, "spring used");
            foreach (var h in s.Party) Assert.Equal(PartyStats.EffectiveStats(db, h).MaxHp, h.Hp, "spring heals " + h.Id);
            AllTp(s, 40, "springs keep TP");

            s = Campaign();
            foreach (var h in s.Party) h.Hp = 5;
            s.AddItem("camp_tent", 1);
            Assert.True(GameFlow.UseFieldItem(db, s, "camp_tent", null, true).Success, "tent used");
            AllTp(s, 40, "tents keep TP");
            foreach (var h in s.Party) h.Hp = 5;
            s.AddItem("megalixir", 1);
            Assert.True(GameFlow.UseFieldItem(db, s, "megalixir", null, true).Success, "full-heal item used");
            AllTp(s, 40, "full-heal items keep TP");
            PartyStats.RestoreParty(db, s);
            AllTp(s, 40, "generic RestoreParty keeps TP");
        }

        // Independent reference of the pre-consolidation roll, including RNG order and final rounding.
        static HitRoll ReferenceDamage(BattleUnit actor, BattleUnit target, SkillDef skill, GodotRng rng, double scale)
        {
            var type = DamageFormula.DamageTypeOf(skill);
            int element = DamageFormula.ElementOf(actor, skill);
            double power = Math.Max(0, skill == null ? 1.0 : Gd.D(skill.Power));
            double offense = type == DamageType.Magical ? actor.EffectiveMagic : actor.EffectiveAttack;
            double defense = type == DamageType.Magical ? target.EffectiveResistance : target.EffectiveDefense;
            defense *= 1 - (skill == null ? 0 : Gd.Clamp(Gd.D(skill.DefenseIgnore), 0, 1));
            double amount = Math.Max(1, offense * power - defense * DamageFormula.DefenseFactor);
            amount *= rng.RandfRange(1 - DamageFormula.DamageVariance, 1 + DamageFormula.DamageVariance);
            double affinity = DamageFormula.ElementMultiplier(target, element);
            if (rng.Randf() > DamageFormula.HitChance(actor, target, type))
                return new HitRoll { Missed = true, Amount = 0, Type = type, Element = element, ElementMultiplier = affinity };
            bool crit = type == DamageType.Physical && rng.Randf() < Gd.Clamp(actor.CritRate + (skill == null ? 0 : Gd.D(skill.CritBonus)), 0, 1);
            if (crit) amount *= actor.CritMultiplier;
            amount *= affinity * scale;
            if (target.Broken) amount *= DamageFormula.BrokenMultiplier;
            if (skill != null && !string.IsNullOrEmpty(skill.BonusVsStatus) && target.HasStatus(skill.BonusVsStatus)) amount *= Math.Max(0, Gd.D(skill.BonusVsStatusMult));
            if (type == DamageType.Physical) amount *= target.PhysicalDamageTakenScale;
            if (target.Guarding) amount *= DamageFormula.GuardMultiplier;
            return new HitRoll { Amount = Math.Max(1, Gd.RoundI(amount)), Critical = crit, Type = type, Element = element, ElementMultiplier = affinity };
        }

        static GodotRng CopyRng(GodotRng rng)
        {
            var copy = new GodotRng(0);
            foreach (var field in typeof(GodotRng).GetFields(BindingFlags.Instance | BindingFlags.NonPublic)) field.SetValue(copy, field.GetValue(rng));
            return copy;
        }

        [LogicTest]
        public static void SharedDamageRollMatchesReferenceAndPreservesPairedRng()
        {
            var db = Db();
            var hero = Hero("roller"); hero.Hit = 0.55f; hero.Crit = 0.5f;
            var engine = Engine(61, new[] { "dummy" }, db: db, heroes: new[] { hero });
            var actor = engine.Party[0]; var target = engine.Enemies[0];
            var magic = Skill("magic_slash", SkillKind.Damage, Element.Slash); magic.ScalingStat = ScalingStat.Magic;
            var physical = db.Skills["slash1"];
            physical.DefenseIgnore = 0.2f; physical.CritBonus = 0.1f; physical.BonusVsStatus = "freeze"; physical.BonusVsStatusMult = 1.2f;
            target.ApplyStatus(BattleStatus.FromDef(db.Statuses["freeze"], ""));
            target.Guarding = true; target.Broken = true;
            int misses = 0, crits = 0, normal = 0, magicalHits = 0;
            foreach (var skill in new SkillDef[] { null, physical, magic })
                foreach (double scale in new[] { 1.0, BattleEngine.ChainFactor(2), BattleEngine.ChainFactor(5) })
                    for (ulong seed = 1; seed <= 100; seed++)
                    {
                        var expectedRng = new GodotRng(seed); var actualRng = new GodotRng(seed);
                        var expected = ReferenceDamage(actor, target, skill, expectedRng, scale);
                        var actual = DamageFormula.Damage(actor, target, skill, actualRng, scale);
                        Assert.Equal(expected.Amount, actual.Amount, $"seed {seed} scale {scale}: amount");
                        Assert.True(expected.Critical == actual.Critical && expected.Missed == actual.Missed && expected.Type == actual.Type && expected.Element == actual.Element && expected.ElementMultiplier == actual.ElementMultiplier, "roll metadata matches (raw affinity, not chain-scaled)");
                        Assert.Equal(DamageFormula.ElementMultiplier(target, DamageFormula.ElementOf(actor, skill)), actual.ElementMultiplier, "raw affinity returned");
                        Assert.Equal(RngState(expectedRng), RngState(actualRng), "same variance/hit/crit draw order and count");
                        for (int i = 0; i < 4; i++) Assert.Equal(expectedRng.NextUInt(), actualRng.NextUInt(), "paired future RNG");
                        if (scale == 1.0)
                        {
                            var defaultRng = new GodotRng(seed);
                            var defaultRoll = DamageFormula.Damage(actor, target, skill, defaultRng);
                            Assert.Equal(expected.Amount, defaultRoll.Amount, "default factor 1 equivalent to the old formula");
                            var explicitRng = new GodotRng(seed); DamageFormula.Damage(actor, target, skill, explicitRng, 1.0);
                            Assert.Equal(RngState(explicitRng), RngState(defaultRng), "omitted factor 1 preserves RNG");
                        }
                        if (actual.Type == DamageType.Magical) { Assert.True(!actual.Missed && !actual.Critical, "magical hit has no miss or crit"); magicalHits++; }
                        else if (actual.Missed) misses++; else if (actual.Critical) crits++; else normal++;
                    }
            Assert.True(misses > 0 && crits > 0 && normal > 0 && magicalHits > 0, $"covered misses {misses}, crits {crits}, normal {normal}, magic {magicalHits}");
        }

        [LogicTest]
        public static void SharedRollMultiHitUsesPreActionChainAndMatchesPreview()
        {
            for (int seed = 1; seed <= 20; seed++)
            {
                var e = Started(Engine(seed, new[] { "dummy" }, new[] { "dummy:" + Slash }));
                SetChain(e, 2);
                var actor = e.ActiveHero; var target = e.Enemies[0]; var skill = actor.Skills.Single(s => s.Id == "slash3");
                var preview = e.PreviewAction(e.UnitIndexOf(actor), BattleCommand.Skill(skill.Id), e.UnitIndexOf(target)).Targets.Single();
                var rng = CopyRng(e.Rng);
                var expected = Enumerable.Range(0, 3).Select(_ => ReferenceDamage(actor, target, skill, rng, BattleEngine.ChainFactor(2))).ToList();
                var hits = Act(e, BattleCommand.Skill(skill.Id, target.Id)).OfType<DamageEvent>().ToList();
                Assert.True(hits.Select(h => h.Amount).SequenceEqual(expected.Select(h => h.Amount)), "engine uses the shared scaled roll for all three hits");
                Assert.True(hits.Sum(h => h.Amount) >= preview.Min && hits.Sum(h => h.Amount) <= preview.Max, "multi-hit total stays inside pre-action chain preview");
                Assert.Equal(3, e.Chain, "chain increments only after all hits");
                Assert.Equal(RngState(rng), RngState(e.Rng), "no extra draws from chain or shared formula");
            }
        }

        [LogicTest]
        public static void ResistantBossItemCcStacksChanceAndCountsRefreshes()
        {
            var db = Db();
            var apply = typeof(BattleEngine).GetMethod("ApplyItemStatus", BindingFlags.Instance | BindingFlags.NonPublic);
            var outField = typeof(BattleEngine).GetField("_out", BindingFlags.Instance | BindingFlags.NonPublic);
            foreach (int count in new[] { 0, 1, 2 })
            {
                int successes = 0, failures = 0, distinguishingRolls = 0;
                double chance = count == 0 ? 0.25 : count == 1 ? 0.125 : 0;
                for (int seed = 1; seed <= 100; seed++)
                {
                    var e = Started(Engine(seed, new[] { "stubborn" }, db: db));
                    var boss = e.Enemies[0]; boss.PhaseCcSuccesses = count;
                    boss.ApplyStatus(BattleStatus.FromDef(db.Statuses["stun"], "")); // every success must be a refresh
                    var expectedRng = CopyRng(e.Rng);
                    string before = RngState(e.Rng);
                    float roll = count < 2 ? expectedRng.Randf() : 0;
                    if (count < 2 && roll >= chance && roll < chance * 2) distinguishingRolls++;
                    var events = (List<BattleEvent>)outField.GetValue(e); int oldEvents = events.Count;
                    apply.Invoke(e, new object[] { e.Party[0], new List<BattleUnit> { boss }, db.Items["flash"] });
                    var applied = events.Skip(oldEvents).OfType<StatusAppliedEvent>().ToList();
                    bool expected = count < 2 && roll < chance;
                    Assert.Equal(expected, applied.Count == 1, $"count {count} seed {seed}: resistant boss item chance {chance}, roll {roll}");
                    Assert.Equal(count + (expected ? 1 : 0), boss.PhaseCcSuccesses, "failure leaves count unchanged; success increments once");
                    if (expected) { successes++; Assert.True(applied.Single().Refreshed, "successful item refresh increments the phase count"); }
                    else failures++;
                    Assert.Equal(RngState(expectedRng), RngState(e.Rng), "exactly one roll below count 2; no RNG draw at count 2");
                    if (count == 2) Assert.Equal(before, RngState(e.Rng), "exhausted resistant boss draws nothing");
                }
                if (count < 2) Assert.True(successes > 0 && failures > 0 && distinguishingRolls > 0, $"chance {chance}: successes/failures and rolls that reject the unhalved chance covered");
                else Assert.True(successes == 0 && failures == 100, "count 2 blocks every item attempt");
            }
        }

        // --- O8 boss crowd control -------------------------------------------------------------------------

        static bool Landed(IEnumerable<BattleEvent> events, BattleUnit target, string status)
            => events.OfType<StatusAppliedEvent>().Any(s => s.UnitId == target.Id && s.StatusId == status);

        [LogicTest]
        public static void BossCcChanceHalvesQuartersThenStopsWithinAPhase()
        {
            Assert.True(BattleEngine.BossCcChanceScale(0) == 0.5 && BattleEngine.BossCcChanceScale(1) == 0.25 && BattleEngine.BossCcChanceScale(2) == 0 && BattleEngine.BossCcChanceScale(7) == 0, "0.5 / 0.25 / 0");
            int successes = 0, failures = 0, blocked = 0;
            foreach (int seed in new[] { 41, 42, 43 })
            {
                var e = Started(Engine(seed, new[] { "lord" }));
                var lord = Foe(e, "lord");
                for (int i = 0; i < 60 && e.State == BattleEngineState.AwaitingCommand; i++)
                {
                    int before = lord.PhaseCcSuccesses;
                    double chance = BattleEngine.BossCcChanceScale(before); // stun_ray: status-only, chance 1
                    float roll = PeekRandf(e.Rng);
                    string actor = e.ActiveHero.Id;
                    var mine = OwnAction(e.Submit(BattleCommand.Skill("stun_ray", lord.Id)), actor);
                    bool landed = Landed(mine, lord, "stun");
                    Assert.Equal(roll < chance, landed, $"seed {seed} attempt {i}: roll {roll} vs chance {chance}");
                    Assert.Equal(before + (landed ? 1 : 0), lord.PhaseCcSuccesses, "a landing counts once");
                    if (chance == 0) blocked++; else if (landed) successes++; else failures++;
                }
                Assert.Equal(2, lord.PhaseCcSuccesses, $"seed {seed}: two landings, then none this phase");
                Assert.True(!lord.PhasesDone.Any(), "no phase change happened");
            }
            Assert.True(successes == 6 && failures > 0 && blocked > 0, $"successes {successes}, failures {failures}, blocked {blocked}");
        }

        [LogicTest]
        public static void BossCcRefreshItemsAndMultiEntryPayloads()
        {
            var db = Db();
            // Refresh of an existing stun counts.
            var e = Started(Engine(44, new[] { "lord" }, db: db));
            var lord = Foe(e, "lord");
            bool refreshed = false;
            for (int i = 0; i < 30 && !refreshed && e.State == BattleEngineState.AwaitingCommand; i++)
            {
                if (!lord.HasStatus("stun")) lord.ApplyStatus(BattleStatus.FromDef(db.Statuses["stun"], ""));
                float roll = PeekRandf(e.Rng);
                var mine = Act(e, BattleCommand.Skill("stun_ray", lord.Id));
                if (roll >= 0.5) { Assert.True(!Landed(mine, lord, "stun") && lord.PhaseCcSuccesses == 0, "failed roll"); continue; }
                var applied = mine.OfType<StatusAppliedEvent>().Single(x => x.UnitId == lord.Id);
                Assert.True(applied.Refreshed && lord.PhaseCcSuccesses == 1, "refreshing a CC counts as a success");
                refreshed = true;
            }
            Assert.True(refreshed, "a refresh happened");

            // Items: one roll on a boss (chance 0.5 / 0.25 / 0), none on ordinary monsters (always land).
            var it = Started(Engine(45, new[] { "lord", "grunt" }, db: db));
            var boss = Foe(it, "lord");
            var grunt = Foe(it, "grunt");
            for (int i = 0; i < 40 && it.State == BattleEngineState.AwaitingCommand; i++)
            {
                if (i % 2 == 0)
                {
                    int before = boss.PhaseCcSuccesses;
                    double chance = BattleEngine.BossCcChanceScale(before);
                    float roll = PeekRandf(it.Rng);
                    bool landed = Landed(Act(it, BattleCommand.Item("flash", boss.Id)), boss, "stun");
                    Assert.Equal(chance > 0 && roll < chance, landed, $"item attempt {i}: roll {roll} vs {chance}");
                    Assert.Equal(before + (landed ? 1 : 0), boss.PhaseCcSuccesses, "item landings count");
                }
                else
                {
                    Assert.True(Landed(Act(it, BattleCommand.Item("flash", grunt.Id)), grunt, "stun"), "ordinary monsters: item CC always lands");
                    Assert.Equal(0, grunt.PhaseCcSuccesses, "ordinary monsters keep no CC count");
                }
            }
            // O4 plans skills/targets at StartRound, deliberately moving this seed's CC draws.
            // Keep the integration path above (each actual roll and counter checked); prove exhaustion
            // independently with fixed PCG states rather than hunting a more favourable battle seed.
            var isolated = Started(Engine(45, new[] { "lord", "stubborn" }, db: db));
            var applyFixedItem = typeof(BattleEngine).GetMethod("ApplyItemStatus", BindingFlags.Instance | BindingFlags.NonPublic);
            var stateField = typeof(GodotRng).GetField("_state", BindingFlags.Instance | BindingFlags.NonPublic);
            foreach (var target in isolated.Enemies)
            {
                for (int phaseSuccesses = 0; phaseSuccesses < 2; phaseSuccesses++)
                {
                    double threshold = BattleEngine.BossCcChanceScale(phaseSuccesses) * (target.HasGimmick("cc_resist") ? 0.5 : 1);
                    // Max state yields a >=0.5 draw; zero yields exactly zero. Both are fixed, not searched seeds.
                    stateField.SetValue(isolated.Rng, ulong.MaxValue);
                    float failureRoll = PeekRandf(isolated.Rng);
                    Assert.True(failureRoll >= threshold, "fixed failure is above actual threshold " + threshold);
                    var failurePair = CopyRng(isolated.Rng); failurePair.Randf();
                    applyFixedItem.Invoke(isolated, new object[] { isolated.Party[0], new List<BattleUnit> { target }, db.Items["flash"] });
                    Assert.Equal(phaseSuccesses, target.PhaseCcSuccesses, "above-threshold item does not count");
                    Assert.Equal(RngState(failurePair), RngState(isolated.Rng), "failure consumes exactly one paired Randf");
                    stateField.SetValue(isolated.Rng, 0UL);
                    Assert.True(PeekRandf(isolated.Rng) == 0 && threshold > 0, "fixed success is below threshold " + threshold);
                    var successPair = CopyRng(isolated.Rng); successPair.Randf();
                    applyFixedItem.Invoke(isolated, new object[] { isolated.Party[0], new List<BattleUnit> { target }, db.Items["flash"] });
                    Assert.Equal(phaseSuccesses + 1, target.PhaseCcSuccesses, "fixed item landing/refresh counts once");
                    Assert.Equal(RngState(successPair), RngState(isolated.Rng), "success consumes exactly one paired Randf");
                }
                Assert.Equal(2, target.PhaseCcSuccesses, "item landings exhaust the phase too");
                string exhaustedState = RngState(isolated.Rng);
                applyFixedItem.Invoke(isolated, new object[] { isolated.Party[0], new List<BattleUnit> { target }, db.Items["flash"] });
                Assert.Equal(2, target.PhaseCcSuccesses, "exhausted item never increments");
                Assert.Equal(exhaustedState, RngState(isolated.Rng), "exhausted item consumes no draw");
            }

            // RNG use of the item path: none for an ordinary monster or an exhausted boss, exactly one draw otherwise.
            var nd = Started(Engine(46, new[] { "grunt", "lord" }, db: db));
            var applyItem = typeof(BattleEngine).GetMethod("ApplyItemStatus", BindingFlags.Instance | BindingFlags.NonPublic);
            void UseFlash(BattleUnit target) => applyItem.Invoke(nd, new object[] { nd.Party[0], new List<BattleUnit> { target }, db.Items["flash"] });
            string s0 = RngState(nd.Rng);
            UseFlash(Foe(nd, "grunt"));
            Assert.True(Foe(nd, "grunt").HasStatus("stun") && RngState(nd.Rng) == s0, "ordinary monster: lands without a draw");
            var ndLord = Foe(nd, "lord");
            ndLord.PhaseCcSuccesses = 2;
            UseFlash(ndLord);
            Assert.True(!ndLord.HasStatus("stun") && RngState(nd.Rng) == s0 && ndLord.PhaseCcSuccesses == 2, "exhausted boss: no draw, no landing");
            ndLord.PhaseCcSuccesses = 0;
            float next = PeekRandf(nd.Rng);
            UseFlash(ndLord);
            Assert.True(RngState(nd.Rng) != s0, "boss: one draw");
            Assert.Equal(next < 0.5, ndLord.HasStatus("stun"), "boss item chance 0.5");
            Assert.Equal(next < 0.5 ? 1 : 0, ndLord.PhaseCcSuccesses, "counted when landed");

            // Several CC statuses in one payload: one roll, one count.
            var m = Started(Engine(47, new[] { "lord" }, db: db));
            var mb = Foe(m, "lord");
            bool both = false;
            for (int i = 0; i < 30 && !both && m.State == BattleEngineState.AwaitingCommand; i++)
            {
                int before = mb.PhaseCcSuccesses;
                double chance = BattleEngine.BossCcChanceScale(before);
                float roll = PeekRandf(m.Rng);
                var mine = Act(m, BattleCommand.Skill("dual_cc", mb.Id));
                bool stun = Landed(mine, mb, "stun"), sleep = Landed(mine, mb, "sleep");
                Assert.True(stun == sleep && stun == (roll < chance), $"one roll decides both entries (roll {roll}, chance {chance})");
                Assert.Equal(before + (stun ? 1 : 0), mb.PhaseCcSuccesses, "a multi-CC payload counts once");
                both = stun;
            }
            Assert.True(both, "a double CC landed");
        }

        [LogicTest]
        public static void BossCcResetsOnlyWhenAPhaseActivates()
        {
            var e = Started(Engine(48, new[] { "lord" }));
            var lord = Foe(e, "lord");
            lord.PhaseCcSuccesses = 2;
            var hit = e.Submit(BattleCommand.Attack(lord.Id));
            Assert.True(!hit.OfType<BossPhaseEvent>().Any() && lord.PhaseCcSuccesses == 2, "no phase activation: count kept");
            lord.Hp = lord.MaxHp / 2 + 1;
            var phase = e.Submit(BattleCommand.Attack(lord.Id));
            Assert.True(phase.OfType<BossPhaseEvent>().Any(p => p.UnitId == lord.Id), "phase two activates");
            Assert.Equal(0, lord.PhaseCcSuccesses, "a phase activation restores CC resistance");
            lord.PhaseCcSuccesses = 1;
            e.Submit(BattleCommand.Attack(lord.Id));
            Assert.Equal(1, lord.PhaseCcSuccesses, "phases fire once; later hits do not reset again");
            float roll = PeekRandf(e.Rng);
            var mine = Act(e, BattleCommand.Skill("stun_ray", lord.Id));
            Assert.Equal(roll < 0.25, Landed(mine, lord, "stun"), "count 1 -> chance 0.25");
        }

        [LogicTest]
        public static void OrdinaryMonstersImmunitiesResistAndDotAreUnchanged()
        {
            // Ordinary monster: status-only CC always lands, any number of times; chance skills use the plain chance.
            var e = Started(Engine(49, new[] { "grunt" }));
            var grunt = Foe(e, "grunt");
            for (int i = 0; i < 6; i++)
                Assert.True(Landed(Act(e, BattleCommand.Skill("stun_ray", grunt.Id)), grunt, "stun"), "ordinary monster: CC lands every time " + i);
            Assert.Equal(0, grunt.PhaseCcSuccesses, "no count on ordinary monsters");
            for (int i = 0; i < 10; i++)
            {
                float roll = PeekRandf(e.Rng);
                Assert.Equal(roll < 0.6, Landed(Act(e, BattleCommand.Skill("stun_chance", grunt.Id)), grunt, "stun"), "plain 60% on ordinary monsters");
            }

            // Explicit immunity (cc_immune) still wins on a boss: immune popup, nothing counted.
            var w = Started(Engine(50, new[] { "warden" }));
            var warden = Foe(w, "warden");
            for (int i = 0; i < 4; i++)
            {
                var mine = Act(w, BattleCommand.Skill("stun_ray", warden.Id));
                Assert.True(mine.OfType<StatusImmuneEvent>().Any(x => x.UnitId == warden.Id) && !Landed(mine, warden, "stun"), "cc_immune boss stays immune");
            }
            Assert.Equal(0, warden.PhaseCcSuccesses, "immunity is not a success");

            // cc_resist stacks multiplicatively on a boss: 0.6 x 0.5 (resist) x 0.5 (phase count 0).
            var r = Started(Engine(51, new[] { "stubborn" }));
            var stubborn = Foe(r, "stubborn");
            for (int i = 0; i < 12 && stubborn.PhaseCcSuccesses == 0; i++)
            {
                float roll = PeekRandf(r.Rng);
                Assert.Equal(roll < 0.6 * 0.5 * 0.5, Landed(Act(r, BattleCommand.Skill("stun_chance", stubborn.Id)), stubborn, "stun"), "stacked chance");
            }

            // Non-CC statuses on a boss are not limited (poison lands every time) and dot_resist still quarters ticks.
            var p = Started(Engine(52, new[] { "lord" }));
            var lord = Foe(p, "lord");
            var events = new List<BattleEvent>();
            for (int i = 0; i < 4; i++)
            {
                var all = p.Submit(BattleCommand.Skill("poison_ray", lord.Id));
                events.AddRange(all);
                Assert.True(all.OfType<StatusAppliedEvent>().Any(x => x.UnitId == lord.Id && x.StatusId == "poison"), "poison is not crowd control");
            }
            Assert.Equal(0, lord.PhaseCcSuccesses, "poison does not count");
            var tick = events.OfType<DamageEvent>().First(d => d.TargetId == lord.Id && d.StatusId == "poison");
            var poisonDef = TestMain.DB.Statuses["poison"];
            var probe = BattleStatus.FromDef(poisonDef, "");
            probe.BindTo(lord.MaxHp);
            int raw = Math.Max(probe.DamagePerTurn, probe.MaxHpDamageRatio > 0 ? Math.Max(1, (int)Math.Round(lord.MaxHp * probe.MaxHpDamageRatio, MidpointRounding.AwayFromZero)) : 0);
            Assert.Equal(Math.Max(1, (int)Math.Round(raw * 0.25, MidpointRounding.AwayFromZero)), tick.Amount + tick.Absorbed, "dot_resist quarters the poison tick as before");
        }
    }
}
