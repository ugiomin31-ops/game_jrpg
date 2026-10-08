// "최강 장비" auto-equip: for each hero, the owned piece per slot that maximises a weighted score of the hero's
// effective stats. Plan / PlanParty are pure (they never touch the state); Apply / ApplyParty commit the plan through
// PartyStats.Equip, so bag counts, class/job rules and vitals behave exactly like manual equipping.
//
// Score, per point of effective stat: HP 0.1, MP 0.05, DEF 1.0, RES 0.8, SPD 0.5. ATK and MAG share one role budget by
// the hero's base profile: ATK = 0.3 + 1.2 x attack share, MAG = 0.3 + 1.2 x magic share (a warrior values ATK ~1.2 and
// MAG ~0.6, a mage the reverse). Hit / evade / crit count 3.0 per 1.0 (100 %); each element resist and status immunity
// adds 1.0. Ties keep the current piece.
//
// Rules:
// - Candidates per slot: the piece worn now, plus each owned unequipped copy of that slot that AllowsHero allows.
//   A piece has one slot, so one owned copy can only be planned for one hero and one slot. Pieces worn by other
//   heroes are never taken from them.
// - Inside one hero, the three slots are optimised by best-response passes until nothing moves. Every accepted swap
//   strictly raises the hero's score, so the plan is never below the current loadout.
// - Party order (PlanParty / ApplyParty): heroes are planned in party order against the bag the earlier heroes leave.
//   Greedy blocking rule: a hero does not take a bag copy when a later member who may wear it would gain strictly more
//   from it. An earlier hero therefore cannot block a better class- or job-specific piece for someone behind it.
using System;
using System.Collections.Generic;

namespace Abyss.Logic.Game
{
    /// <summary>One slot of a plan: what is worn now, what the plan wears, and that slot's effect in the final loadout.</summary>
    public sealed class AutoEquipSlot
    {
        public string Slot;
        /// <summary>Piece worn now ("" = empty).</summary>
        public string CurrentId = "";
        /// <summary>Piece worn after the plan ("" = empty).</summary>
        public string RecommendedId = "";
        /// <summary>Score of the final loadout minus the score with this slot back on its current piece.</summary>
        public double ScoreDelta;
        /// <summary>Effective-stat change of this slot in the final loadout (same reference as <see cref="ScoreDelta"/>).</summary>
        public StatBlock StatDelta;

        public bool Changed => CurrentId != RecommendedId;
    }

    /// <summary>Recommended gear of one hero. Built without touching the state it was planned from.</summary>
    public sealed class AutoEquipPlan
    {
        public string HeroId;
        public List<AutoEquipSlot> Slots = new List<AutoEquipSlot>();
        public double ScoreBefore, ScoreAfter;
        /// <summary>Effective-stat change of the whole loadout.</summary>
        public StatBlock StatDelta;

        public bool Changed
        {
            get
            {
                foreach (var slot in Slots) if (slot.Changed) return true;
                return false;
            }
        }
    }

    /// <summary>Outcome of applying a plan. Success with empty <see cref="Changes"/> means the gear was already the best.</summary>
    public sealed class AutoEquipResult
    {
        public string HeroId;
        public bool Success = true;
        /// <summary>Failure reason as in <see cref="ServiceResult.Reason"/> (empty on success).</summary>
        public string Reason = "";
        /// <summary>Slots that were re-equipped, in slot order.</summary>
        public List<AutoEquipSlot> Changes = new List<AutoEquipSlot>();
        /// <summary>Effective-stat change of the whole loadout.</summary>
        public StatBlock StatDelta;
    }

    public static class AutoEquip
    {
        const double WeightHp = 0.1, WeightMp = 0.05, WeightDef = 1.0, WeightRes = 0.8, WeightSpd = 0.5;
        const double WeightAccuracy = 3.0, WeightResistOrImmunity = 1.0;
        const double RoleFloor = 0.3, RoleSpan = 1.2;
        const double Epsilon = 1e-9;
        const int MaxPasses = 16;

        /// <summary>Best gear for one hero from the current bag. Never mutates <paramref name="state"/>.</summary>
        public static AutoEquipPlan Plan(GameDB db, GameState state, string heroId)
        {
            var hero = state.Hero(heroId);
            if (hero == null) return new AutoEquipPlan { HeroId = heroId };
            return PlanHero(db, state, hero, state.EquipmentBag, new List<HeroState>());
        }

        /// <summary>Plans every party member in party order against the bag the earlier members leave. Never mutates <paramref name="state"/>.</summary>
        public static List<AutoEquipPlan> PlanParty(GameDB db, GameState state)
        {
            var bag = new Dictionary<string, int>(state.EquipmentBag);
            var plans = new List<AutoEquipPlan>();
            for (int i = 0; i < state.Party.Count; i++)
            {
                var later = state.Party.GetRange(i + 1, state.Party.Count - i - 1);
                var plan = PlanHero(db, state, state.Party[i], bag, later);
                foreach (var slot in plan.Slots)
                {
                    if (!slot.Changed) continue;
                    AddCount(bag, slot.RecommendedId, -1);
                    AddCount(bag, slot.CurrentId, 1);
                }
                plans.Add(plan);
            }
            return plans;
        }

        /// <summary>Equips the best gear for one hero (same rules as <see cref="Plan"/>).</summary>
        public static AutoEquipResult Apply(GameDB db, GameState state, string heroId)
        {
            if (state.Hero(heroId) == null) return new AutoEquipResult { HeroId = heroId, Success = false, Reason = "unknown_member" };
            return Commit(db, state, Plan(db, state, heroId));
        }

        /// <summary>Equips every party member as <see cref="PlanParty"/> planned it. One result per member, in party order.</summary>
        public static List<AutoEquipResult> ApplyParty(GameDB db, GameState state)
        {
            var results = new List<AutoEquipResult>();
            foreach (var plan in PlanParty(db, state)) results.Add(Commit(db, state, plan));
            return results;
        }

        /// <summary>Current weighted score of a hero's worn gear, on the same scale as the plans (0 for an unknown hero).</summary>
        public static double ScoreOf(GameDB db, GameState state, string heroId)
        {
            var hero = state.Hero(heroId);
            return hero == null ? 0 : new Scorer(db, state, hero).Value(LoadoutOf(hero));
        }

        static AutoEquipPlan PlanHero(GameDB db, GameState state, HeroState hero, Dictionary<string, int> bag, List<HeroState> later)
        {
            var scorer = new Scorer(db, state, hero);
            var original = LoadoutOf(hero);
            double originalScore = scorer.Value(original);
            var pools = new Dictionary<string, List<string>>();
            foreach (string slot in GameState.EquipSlots)
                pools[slot] = Candidates(db, state, scorer, hero, slot, original, originalScore, bag, later);

            var loadout = new Dictionary<string, string>(original);
            for (int pass = 0; pass < MaxPasses; pass++)
            {
                bool moved = false;
                foreach (string slot in GameState.EquipSlots)
                {
                    string chosen = loadout[slot];
                    double chosenScore = scorer.Value(loadout);
                    foreach (string id in pools[slot])
                    {
                        if (id == loadout[slot]) continue;
                        double score = scorer.Value(With(loadout, slot, id));
                        if (score > chosenScore + Epsilon) { chosen = id; chosenScore = score; }
                    }
                    if (chosen != loadout[slot]) { loadout[slot] = chosen; moved = true; }
                }
                if (!moved) break;
            }

            var plan = new AutoEquipPlan { HeroId = hero.Id, ScoreBefore = originalScore, ScoreAfter = scorer.Value(loadout) };
            var finalStats = scorer.Stats(loadout).Stats;
            plan.StatDelta = finalStats - scorer.Stats(original).Stats;
            foreach (string slot in GameState.EquipSlots)
            {
                var reverted = With(loadout, slot, original[slot]);
                plan.Slots.Add(new AutoEquipSlot
                {
                    Slot = slot,
                    CurrentId = original[slot],
                    RecommendedId = loadout[slot],
                    ScoreDelta = plan.ScoreAfter - scorer.Value(reverted),
                    StatDelta = finalStats - scorer.Stats(reverted).Stats,
                });
            }
            return plan;
        }

        /// <summary>Slot candidates in id order: the piece worn now first, then owned copies this hero may take.</summary>
        static List<string> Candidates(GameDB db, GameState state, Scorer scorer, HeroState hero, string slot, Dictionary<string, string> original,
            double originalScore, Dictionary<string, int> bag, List<HeroState> later)
        {
            var output = new List<string>();
            string worn = original[slot];
            if (worn != "") output.Add(worn);
            var ids = new List<string>();
            foreach (var kv in bag)
            {
                if (kv.Value <= 0 || kv.Key == worn || !db.Equipment.TryGetValue(kv.Key, out var piece) || piece.Slot != slot) continue;
                if (!PartyStats.AllowsHero(db, piece, hero)) continue;
                double gain = scorer.Value(With(original, slot, piece.Id)) - originalScore;
                if (WantedByLater(db, state, slot, piece, gain, later)) continue;
                ids.Add(kv.Key);
            }
            ids.Sort(StringComparer.Ordinal);
            output.AddRange(ids);
            return output;
        }

        /// <summary>True when a later party member who may wear <paramref name="piece"/> would gain strictly more from it than the planning hero.</summary>
        static bool WantedByLater(GameDB db, GameState state, string slot, EquipmentDef piece, double heroGain, List<HeroState> later)
        {
            foreach (var other in later)
            {
                if (!PartyStats.AllowsHero(db, piece, other)) continue;
                var scorer = new Scorer(db, state, other);
                var loadout = LoadoutOf(other);
                if (scorer.Value(With(loadout, slot, piece.Id)) - scorer.Value(loadout) > heroGain + Epsilon) return true;
            }
            return false;
        }

        static AutoEquipResult Commit(GameDB db, GameState state, AutoEquipPlan plan)
        {
            var result = new AutoEquipResult { HeroId = plan.HeroId, StatDelta = plan.StatDelta };
            foreach (var slot in plan.Slots)
            {
                if (!slot.Changed) continue;
                // A planned swap always has a bag copy and an allowed wearer, so Equip only fails if the state changed underneath.
                var outcome = PartyStats.Equip(db, state, plan.HeroId, slot.RecommendedId);
                if (!outcome.Success) { result.Success = false; result.Reason = outcome.Reason; break; }
                result.Changes.Add(slot);
            }
            return result;
        }

        static Dictionary<string, string> LoadoutOf(HeroState hero)
        {
            var loadout = new Dictionary<string, string>();
            foreach (string slot in GameState.EquipSlots) loadout[slot] = hero.Equipped(slot);
            return loadout;
        }

        static Dictionary<string, string> With(Dictionary<string, string> loadout, string slot, string id)
        {
            var copy = new Dictionary<string, string>(loadout);
            copy[slot] = id;
            return copy;
        }

        static void AddCount(Dictionary<string, int> bag, string id, int delta)
        {
            if (string.IsNullOrEmpty(id)) return;
            int count = (bag.TryGetValue(id, out int have) ? have : 0) + delta;
            if (count > 0) bag[id] = count;
            else bag.Remove(id);
        }

        /// <summary>Scores one hero's loadouts with that hero's role weights (ATK/MAG split from its base stats).</summary>
        sealed class Scorer
        {
            readonly GameDB db;
            readonly GameState state;
            readonly HeroState hero;
            readonly double atkWeight, magWeight;

            public Scorer(GameDB db, GameState state, HeroState hero)
            {
                this.db = db;
                this.state = state;
                this.hero = hero;
                var basis = PartyStats.BaseStats(db, hero);
                double total = Math.Max(1, basis.Attack + basis.Magic);
                double share = basis.Attack / total;
                atkWeight = RoleFloor + RoleSpan * share;
                magWeight = RoleFloor + RoleSpan * (1 - share);
            }

            public HeroStats Stats(Dictionary<string, string> loadout) => PartyStats.EffectiveStats(db, new HeroState
            {
                Id = hero.Id, Job = hero.Job, Level = hero.Level, Seeds = hero.Seeds, Equipment = loadout,
                EnhanceLevels = hero.EnhanceLevels ?? state.Enhancements,
            });

            public double Value(Dictionary<string, string> loadout)
            {
                var s = Stats(loadout);
                var v = s.Stats;
                return WeightHp * v.MaxHp + WeightMp * v.MaxMp + atkWeight * v.Attack + magWeight * v.Magic
                    + WeightDef * v.Defense + WeightRes * v.Resistance + WeightSpd * v.Speed
                    + WeightAccuracy * (s.Hit + s.Evade + s.Crit)
                    + WeightResistOrImmunity * (s.ElementResists.Count + s.StatusImmunities.Count);
            }
        }
    }
}
