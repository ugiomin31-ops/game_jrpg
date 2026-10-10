// Shared helpers for the battle logic tests.
using System;
using System.Collections.Generic;
using System.Linq;
using Abyss.Logic;
using Abyss.Logic.Battle;

namespace Abyss.LogicTests
{
    public static class BattleTestUtil
    {
        /// <summary>Hero spec at a level, stats = round(base + growth x (L - 1)), skills by learnset (no equipment).</summary>
        public static HeroCombatSpec Hero(string id, int level)
        {
            var h = TestMain.DB.Heroes[id];
            int steps = Math.Max(0, level - 1);
            int R(double v) => (int)Math.Round(v, MidpointRounding.AwayFromZero);
            double G(float f) => double.Parse(f.ToString("R"));
            var spec = new HeroCombatSpec
            {
                HeroId = id, DisplayName = h.DisplayName, Level = level,
                MaxHp = R(h.MaxHp + G(h.HpGrowth) * steps), MaxMp = R(h.MaxMp + G(h.MpGrowth) * steps),
                Attack = R(h.Attack + G(h.AtkGrowth) * steps), Magic = R(h.Magic + G(h.MagGrowth) * steps),
                Defense = R(h.Defense + G(h.DefGrowth) * steps), Resistance = R(h.Resistance + G(h.ResGrowth) * steps),
                Speed = R(h.Speed + G(h.SpdGrowth) * steps), Hit = h.Hit, Evade = h.Evade, Crit = h.Crit,
            };
            spec.Hp = spec.MaxHp;
            spec.Mp = spec.MaxMp;
            foreach (var s in h.Skills) if (!spec.Skills.Contains(s)) spec.Skills.Add(s);
            foreach (var l in h.Learnset.OrderBy(l => l.Level))
                if (l.Level <= level && !spec.Skills.Contains(l.Skill)) spec.Skills.Add(l.Skill);
            return spec;
        }

        public static BattleSetup Setup(int level, IEnumerable<string> enemies, int seed, BattleKind kind = BattleKind.Random,
            Difficulty difficulty = Difficulty.Normal, params string[] heroes)
        {
            var setup = new BattleSetup { Kind = kind, Difficulty = difficulty, Seed = seed };
            foreach (var id in heroes.Length > 0 ? heroes : new[] { "h_dohyun", "h_seoa", "h_jiho", "h_yuna" }) setup.Party.Add(Hero(id, level));
            setup.EnemyGroup.AddRange(enemies);
            return setup;
        }

        /// <summary>Runs AUTO for every hero until the end (or a round cap). Returns all events.</summary>
        public static List<BattleEvent> RunAuto(BattleEngine engine, int maxRounds = 200)
        {
            var all = new List<BattleEvent>(engine.Start());
            int guard = 0;
            while (engine.State == BattleEngineState.AwaitingCommand && engine.Round <= maxRounds)
            {
                var cmd = engine.SuggestCommand(engine.ActiveHero);
                var evs = engine.Submit(cmd);
                Assert.True(!(evs.Count == 1 && evs[0] is CommandRejectedEvent), "auto command rejected: " + cmd + " " + (evs[0] as CommandRejectedEvent)?.Key);
                all.AddRange(evs);
                if (++guard > 100000) throw new Exception("runaway battle");
            }
            return all;
        }

        /// <summary>Compact text log of events for replay comparisons.</summary>
        public static string Describe(BattleEvent e)
        {
            switch (e)
            {
                case EnemyIntentPlannedEvent p: return $"intent r{p.Round} {p.EnemyUnitId} s{p.Slot} {p.Kind} {p.SkillId} payload{p.PayloadId} ->{p.TargetUnitId} {p.Scope} prep{p.IsChargeAnnounce} release{p.IsChargeRelease}";
                case IntentClearedEvent c: return $"intent_clear {c.EnemyUnitId} s{c.Slot}";
                case ChargeStartedEvent c: return $"charge_start {c.EnemyUnitId} {c.SkillId} ->{c.TargetUnitId}";
                case ChargeReleasedEvent c: return $"charge_release {c.EnemyUnitId} {c.SkillId}";
                case ChargeCancelledEvent c: return $"charge_cancel {c.EnemyUnitId} {c.Reason}";
                case DamageEvent d: return $"dmg {d.TargetId} {d.Amount} c{(d.Critical ? 1 : 0)} {d.Type} e{d.Element} {d.Effectiveness} hp{d.HpAfter}";
                case HealEvent h: return $"heal {h.TargetId} {h.Amount} hp{h.HpAfter}";
                case MissEvent m: return $"miss {m.TargetId}";
                case ActionStartEvent a: return $"act {a.ActorId} {a.Kind} {a.SkillId ?? a.ItemId} [{string.Join(",", a.TargetIds)}]";
                case StatusAppliedEvent s: return $"st+ {s.UnitId} {s.StatusId} {s.Turns}";
                case StatusRemovedEvent s: return $"st- {s.UnitId} {s.StatusId} {s.Reason}";
                case TpChangeEvent t: return $"tp {t.UnitId} {t.Tp}";
                case MpChangeEvent m: return $"mp {m.UnitId} {m.Mp}";
                case RoundStartEvent r: return $"round {r.Round} [{string.Join(",", r.TurnOrder)}]";
                case TurnEndEvent t: return $"turn_end {t.Unit.Id} guard{(t.Unit.Guarding ? 1 : 0)} [{string.Join(",", t.Unit.Statuses.Select(s => s.Id + ":" + s.Turns))}]";
                case MessageEvent m: return $"msg {m.Key}";
                case BattleEndEvent b: return $"end {b.Result}";
                case SummonEvent s: return $"summon {s.Unit.Id}";
                case BossPhaseEvent p: return $"phase {p.UnitId} {p.PhaseIndex}";
                default: return e.GetType().Name;
            }
        }
    }
}
