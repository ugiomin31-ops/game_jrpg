// Report 19/20 regressions: unused auto-equip reservations and zero-benefit paid enhancement.
using System.Collections.Generic;
using System.Linq;
using Abyss.Logic;
using Abyss.Logic.Game;

namespace Abyss.LogicTests
{
    public static class EquipmentProgressionRepairTests
    {
        static GameState TwoHunters(string second = "h_minjun")
        {
            var db = TestMain.DB;
            var state = GameState.NewGame(db, Difficulty.Normal);
            state.Party.Clear();
            state.Reserve.Clear();
            state.EquipmentBag.Clear();
            foreach (string id in new[] { "h_dohyun", second })
            {
                var hero = new HeroState { Id = id, Job = db.ClassOf(id), Level = 20, EnhanceLevels = state.Enhancements };
                foreach (string slot in GameState.EquipSlots) hero.Equipment[slot] = "";
                state.Party.Add(hero);
            }
            PartyStats.RestoreParty(db, state);
            return state;
        }

        static Dictionary<string, int> Owned(GameState state) => TestMain.DB.Equipment.Keys
            .ToDictionary(id => id, id => Enhancement.OwnedCount(state, id));

        static void ApplyAndCheck(GameState state, List<AutoEquipPlan> plans)
        {
            var db = TestMain.DB;
            var owned = Owned(state);
            var beforeStats = state.Party.ToDictionary(h => h.Id, h => PartyStats.EffectiveStats(db, h).Stats);
            var results = AutoEquip.ApplyParty(db, state);
            Assert.Equal(state.Party.Count, results.Count, "one result per party member");
            foreach (var result in results) Assert.True(result.Success, result.HeroId + ": " + result.Reason);
            foreach (var plan in plans)
            {
                foreach (var slot in plan.Slots)
                    Assert.Equal(slot.RecommendedId, state.Hero(plan.HeroId).Equipped(slot.Slot), plan.HeroId + " planned " + slot.Slot);
                Assert.Near(plan.ScoreAfter, AutoEquip.ScoreOf(db, state, plan.HeroId), 1e-9, "final score matches preview");
                Assert.True(plan.ScoreAfter >= plan.ScoreBefore, "no score loss");
                var after = PartyStats.EffectiveStats(db, state.Hero(plan.HeroId)).Stats;
                Assert.Equal(after - beforeStats[plan.HeroId], plan.StatDelta, "delta uses original gear, not an intermediate plan");
            }
            foreach (var kv in owned)
                Assert.Equal(kv.Value, Enhancement.OwnedCount(state, kv.Key), "ownership conserved: " + kv.Key);
        }

        [LogicTest]
        public static void PartyBackfillUsesUnclaimedAlternativeInOneApply()
        {
            var db = TestMain.DB;
            var state = TwoHunters();
            state.Party[0].Equipment["weapon"] = "sword_iron";
            state.Party[1].Equipment["weapon"] = "sword_bronze";
            state.AddEquipment("sword_knight", 1);
            state.AddEquipment("sword_runic", 1);
            string before = SaveCodec.Serialize(state);

            var plans = AutoEquip.PlanParty(db, state);
            Assert.Equal(before, SaveCodec.Serialize(state), "planning does not mutate the campaign");
            Assert.Equal("sword_knight", plans[0].Slots.Single(s => s.Slot == "weapon").RecommendedId, "unused reserved alternative goes to the first hunter");
            Assert.Equal("sword_runic", plans[1].Slots.Single(s => s.Slot == "weapon").RecommendedId, "higher gain hunter keeps the best weapon");
            Assert.Equal("sword_iron", plans[0].Slots.Single(s => s.Slot == "weapon").CurrentId, "preview starts at actual worn gear");
            ApplyAndCheck(state, plans);
            Assert.Equal(0, state.BagCount("sword_knight"), "the leftover upgrade is used immediately");
            Assert.True(AutoEquip.PlanParty(db, state).All(p => !p.Changed), "the reported scenario needs no second click");
        }

        [LogicTest]
        public static void PartyBackfillPreservesScarceCopiesAndInventoryOrderIndependence()
        {
            var db = TestMain.DB;
            foreach (int copies in new[] { 1, 2 })
            {
                var state = TwoHunters();
                state.Party[0].Equipment["weapon"] = "sword_iron";
                state.Party[1].Equipment["weapon"] = "sword_bronze";
                state.AddEquipment("sword_runic", copies);
                state.AddEquipment("staff_ruby", 1); // Incompatible equipment must remain in the bag.
                var plans = AutoEquip.PlanParty(db, state);
                var reversed = state.EquipmentBag.Reverse().ToArray();
                state.EquipmentBag.Clear();
                foreach (var kv in reversed) state.EquipmentBag.Add(kv.Key, kv.Value);
                var again = AutoEquip.PlanParty(db, state);
                for (int i = 0; i < plans.Count; i++)
                    for (int j = 0; j < plans[i].Slots.Count; j++)
                        Assert.Equal(plans[i].Slots[j].RecommendedId, again[i].Slots[j].RecommendedId, "bag enumeration does not change the plan");
                Assert.Equal(copies == 1 ? "sword_iron" : "sword_runic", plans[0].Slots.Single(s => s.Slot == "weapon").RecommendedId, "first hero only takes a spare copy");
                Assert.Equal("sword_runic", plans[1].Slots.Single(s => s.Slot == "weapon").RecommendedId, "later higher gain is protected");
                ApplyAndCheck(state, plans);
                Assert.Equal(copies, PartyStats.EquippedCount(state, "sword_runic"), "each owned copy equipped once");
                Assert.Equal(1, state.BagCount("staff_ruby"), "class restriction retained");
            }
        }

        [LogicTest]
        public static void PartyBackfillDoesNotPromiseGearReturnedByLaterHero()
        {
            var db = TestMain.DB;
            var state = TwoHunters("h_seoa");
            state.Party[1].Equipment["accessory"] = "acc_power_band";
            state.AddEquipment("acc_lich_phylactery", 1);
            var first = AutoEquip.Plan(db, state, state.Party[0].Id);
            var later = AutoEquip.Plan(db, state, state.Party[1].Id);
            Assert.True(later.ScoreAfter - later.ScoreBefore > first.ScoreAfter - first.ScoreBefore, "mage gains more from the only phylactery");
            var plans = AutoEquip.PlanParty(db, state);
            Assert.Equal("", plans[0].Slots.Single(s => s.Slot == "accessory").RecommendedId, "later worn gear is unavailable at the first commit");
            Assert.Equal("acc_lich_phylactery", plans[1].Slots.Single(s => s.Slot == "accessory").RecommendedId, "reserved piece reaches the mage");
            ApplyAndCheck(state, plans);
            Assert.Equal(1, state.BagCount("acc_power_band"), "later returned gear becomes available only after its owner changes");
        }

        [LogicTest]
        public static void EffectOnlyEquipmentRejectsEnhancementWithoutAnyMutation()
        {
            var db = TestMain.DB;
            foreach (string id in new[] { "acc_lucky_charm", "acc_eagle_eye", "acc_exp_charm", "acc_gold_charm", "acc_sniper_scope" })
            {
                var state = GameState.NewGame(db, Difficulty.Normal);
                state.AddEquipment(id, 2);
                Assert.True(PartyStats.Equip(db, state, "h_dohyun", id).Success, "effect-only gear can still be worn");
                state.AddItem(Enhancement.Stone, 30);
                state.AddItem(Enhancement.StoneHigh, 30);
                state.Gold = 100000;
                foreach (int level in new[] { 0, 3 }) // Also protect pre-existing saves that already paid for this gear.
                {
                    if (level > 0) state.Enhancements[id] = level;
                    string before = SaveCodec.Serialize(state);
                    Assert.True(Enhancement.CostOf(db.Equipment[id], level) == null, "no paid step offered for " + id);
                    Assert.True(Enhancement.Candidates(db, state).All(e => e.Equipment.Id != id), "ineligible gear absent from smithy candidates");
                    var result = Enhancement.Enhance(db, state, id);
                    Assert.True(!result.Success, "zero-benefit enhancement rejected");
                    Assert.Equal("no_enhanceable_stats", result.Reason, "explicit eligibility reason");
                    Assert.Equal(0, result.GoldDelta, "no payment reported");
                    Assert.Equal(before, SaveCodec.Serialize(state), "gold, stones, ownership, levels and hero state unchanged");
                }
            }
        }

        [LogicTest]
        public static void UsefulEnhancementStillChargesOnceAndImprovesAllCopies()
        {
            var db = TestMain.DB;
            var state = TwoHunters();
            foreach (var hero in state.Party) hero.Equipment["weapon"] = "sword_iron";
            state.AddEquipment("sword_iron", 1);
            state.AddItem(Enhancement.Stone, 2);
            state.Gold = 100;
            var before = state.Party.Select(h => PartyStats.EffectiveStats(db, h).Stats.Attack).ToArray();
            Assert.True(Enhancement.Candidates(db, state).Single(e => e.Equipment.Id == "sword_iron").CanEnhance, "useful gear remains eligible");
            var result = Enhancement.Enhance(db, state, "sword_iron");
            Assert.True(result.Success, "useful enhancement succeeds");
            Assert.Equal(-40, result.GoldDelta, "one tier-2 step charged");
            Assert.Equal(60, state.Gold, "gold debited exactly once");
            Assert.Equal(1, state.ItemCount(Enhancement.Stone), "one stone spent for all copies");
            Assert.Equal(3, Enhancement.OwnedCount(state, "sword_iron"), "no equipment created or consumed");
            Assert.Equal(1, Enhancement.LevelOf(state, "sword_iron"), "shared level advances once");
            for (int i = 0; i < state.Party.Count; i++)
                Assert.Equal(before[i] + 1, PartyStats.EffectiveStats(db, state.Party[i]).Stats.Attack, "each worn iron sword gains attack");
        }

        [LogicTest]
        public static void SmallPositiveStatsCanProgressThroughRoundingPlateau()
        {
            var db = TestMain.DB;
            var state = GameState.NewGame(db, Difficulty.Normal);
            const string id = "acc_awake_bell";
            state.AddEquipment(id, 1);
            state.AddItem(Enhancement.Stone, 3);
            state.Gold = 10000;
            var piece = db.Equipment[id];
            Assert.Equal(Enhancement.Stats(piece, 0).Speed, Enhancement.Stats(piece, 1).Speed, "first step is a rounding plateau");
            for (int i = 0; i < 3; i++)
                Assert.True(Enhancement.Enhance(db, state, id).Success, "positive stat retains its paid progression");
            Assert.Equal(Enhancement.Stats(piece, 0).Speed + 1, Enhancement.Stats(piece, 3).Speed, "later level yields the promised stat benefit");
        }
    }
}
