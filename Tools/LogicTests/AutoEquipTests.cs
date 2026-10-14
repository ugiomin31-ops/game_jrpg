// "최강 장비" auto-equip planner (Logic/Game/AutoEquip.cs): upgrades, class/job rules, single copies, purity, scores.
using System;
using System.Collections.Generic;
using Abyss.Logic;
using Abyss.Logic.Game;

namespace Abyss.LogicTests
{
    public static class AutoEquipTests
    {
        const double Eps = 1e-9;

        static void OwnEveryPiece(GameDB db, GameState state)
        {
            foreach (string id in db.Equipment.Keys) state.AddEquipment(id, 1);
        }

        static int Owned(GameState state, string equipmentId) => state.BagCount(equipmentId) + PartyStats.EquippedCount(state, equipmentId);

        [LogicTest]
        public static void PicksStrictlyBetterWeaponFromInventory()
        {
            var db = TestMain.DB;
            var state = GameState.NewGame(db, Difficulty.Normal);
            var warrior = state.Hero("h_dohyun");
            var current = db.Equipment[warrior.Equipped("weapon")];
            // The strongest warrior weapon that is at least as good in every other stat and better in attack.
            EquipmentDef upgrade = null;
            foreach (var piece in db.Equipment.Values)
            {
                if (piece.Slot != "weapon" || !PartyStats.AllowsHero(db, piece, warrior) || piece.Atk <= current.Atk) continue;
                if (piece.Mag < current.Mag || piece.Def < current.Def || piece.Res < current.Res || piece.Spd < current.Spd) continue;
                if (piece.Hp < current.Hp || piece.Mp < current.Mp || piece.Hit < current.Hit || piece.Evade < current.Evade || piece.Crit < current.Crit) continue;
                if (piece.ElementResists.Count > 0 || piece.StatusImmunities.Count > 0) continue;
                if (upgrade == null || piece.Atk > upgrade.Atk || (piece.Atk == upgrade.Atk && string.CompareOrdinal(piece.Id, upgrade.Id) < 0)) upgrade = piece;
            }
            Assert.True(upgrade != null, "data has a warrior weapon that dominates the starter");
            state.AddEquipment(upgrade.Id, 1);

            var plan = AutoEquip.Plan(db, state, "h_dohyun");
            var weapon = plan.Slots.Find(s => s.Slot == "weapon");
            Assert.True(plan.Changed && weapon.Changed, "the bag upgrade is recommended");
            Assert.True(weapon.ScoreDelta > 0, "the recommended weapon raises the score");

            // Planning alone must not equip anything; it must be at least as good as wearing the upgrade by hand.
            Assert.Equal(current.Id, warrior.Equipped("weapon"), "plan leaves the weapon worn");
            var manual = SaveCodec.Deserialize(SaveCodec.Serialize(state), db);
            Assert.True(PartyStats.Equip(db, manual, "h_dohyun", upgrade.Id).Success, "manual equip of the upgrade");
            Assert.True(plan.ScoreAfter >= AutoEquip.ScoreOf(db, manual, "h_dohyun") - Eps, "plan is not worse than the manual upgrade");

            var result = AutoEquip.Apply(db, state, "h_dohyun");
            Assert.True(result.Success && result.Changes.Count > 0, "apply succeeds");
            Assert.Equal(weapon.RecommendedId, warrior.Equipped("weapon"), "applied weapon is the planned one");
            Assert.Near(plan.ScoreAfter, AutoEquip.ScoreOf(db, state, "h_dohyun"), Eps, "applied score matches the plan");
            Assert.True(plan.StatDelta.Attack > 0 || plan.StatDelta.Defense > 0, "main stats moved up");
        }

        [LogicTest]
        public static void RespectsClassAndJobRestrictions()
        {
            var db = TestMain.DB;
            var state = GameState.NewGame(db, Difficulty.Normal);
            OwnEveryPiece(db, state);
            foreach (var hero in state.Party)
            {
                var plan = AutoEquip.Plan(db, state, hero.Id);
                foreach (var slot in plan.Slots)
                {
                    if (!slot.Changed) continue;
                    Assert.True(PartyStats.AllowsHero(db, db.Equipment[slot.RecommendedId], hero), $"{hero.Id} may wear {slot.RecommendedId}");
                }
            }

            // A class-limited top weapon for another class, and a job-limited piece for a base-job hero, are refused by Equip too.
            var mage = state.Hero("h_seoa");
            foreach (var piece in db.Equipment.Values)
            {
                if (PartyStats.AllowsClass(db, piece, "h_seoa")) continue;
                Assert.Equal("class_mismatch", PartyStats.Equip(db, SaveCodec.Deserialize(SaveCodec.Serialize(state), db), "h_seoa", piece.Id).Reason, piece.Id + " is class-locked");
                break;
            }
            foreach (var piece in db.Equipment.Values)
            {
                if (!PartyStats.AllowsClass(db, piece, "h_seoa") || piece.Jobs.Count == 0 || PartyStats.AllowsJob(db, piece, mage)) continue;
                Assert.Equal("job_mismatch", PartyStats.Equip(db, SaveCodec.Deserialize(SaveCodec.Serialize(state), db), "h_seoa", piece.Id).Reason, piece.Id + " is job-locked");
                break;
            }
        }

        [LogicTest]
        public static void OneOwnedCopyIsPlannedForOneHeroOnly()
        {
            var db = TestMain.DB;
            var state = GameState.NewGame(db, Difficulty.Normal);
            // The strongest accessory every hero may wear (no class or job limit); only one copy is owned.
            EquipmentDef prize = null;
            foreach (var piece in db.Equipment.Values)
            {
                if (piece.Slot != "accessory" || piece.Classes.Count > 0 || piece.Jobs.Count > 0) continue;
                int total = piece.Hp + piece.Mp + piece.Atk + piece.Mag + piece.Def + piece.Res + piece.Spd;
                int best = prize == null ? -1 : prize.Hp + prize.Mp + prize.Atk + prize.Mag + prize.Def + prize.Res + prize.Spd;
                if (total > best || (total == best && string.CompareOrdinal(piece.Id, prize.Id) < 0)) prize = piece;
            }
            Assert.True(prize != null, "an accessory with no class or job limit exists");
            Assert.Equal(0, PartyStats.EquippedCount(state, prize.Id), "the prize is not a starter piece");
            state.AddEquipment(prize.Id, 1);

            int planned = 0;
            foreach (var plan in AutoEquip.PlanParty(db, state))
                foreach (var slot in plan.Slots)
                    if (slot.RecommendedId == prize.Id) planned++;
            Assert.True(planned <= 1, "one copy is recommended at most once");

            AutoEquip.ApplyParty(db, state);
            Assert.Equal(1, Owned(state, prize.Id), "the single copy is still a single copy");
            Assert.Equal(planned, PartyStats.EquippedCount(state, prize.Id), "the copy sits on the planned hero");
        }

        [LogicTest]
        public static void PlanningNeverMutatesState()
        {
            var db = TestMain.DB;
            var state = GameState.NewGame(db, Difficulty.Normal);
            OwnEveryPiece(db, state);
            string before = SaveCodec.Serialize(state);
            foreach (var hero in state.Party) AutoEquip.Plan(db, state, hero.Id);
            AutoEquip.PlanParty(db, state);
            Assert.Equal(before, SaveCodec.Serialize(state), "planning leaves the campaign untouched");
        }

        [LogicTest]
        public static void PlansNeverLowerTheScoreAndAreDeterministic()
        {
            var db = TestMain.DB;
            var state = GameState.NewGame(db, Difficulty.Normal);
            OwnEveryPiece(db, state);
            foreach (var hero in state.Party)
            {
                var plan = AutoEquip.Plan(db, state, hero.Id);
                Assert.True(plan.ScoreAfter >= plan.ScoreBefore - Eps, hero.Id + ": plan never lowers the score");
                Assert.Near(plan.ScoreBefore, AutoEquip.ScoreOf(db, state, hero.Id), Eps, hero.Id + ": ScoreBefore is the worn score");
                foreach (var slot in plan.Slots)
                    if (slot.Changed) Assert.True(slot.ScoreDelta >= -Eps, $"{hero.Id} {slot.Slot}: changed slot does not lower the score");

                var again = AutoEquip.Plan(db, state, hero.Id);
                for (int i = 0; i < plan.Slots.Count; i++)
                    Assert.Equal(plan.Slots[i].RecommendedId, again.Slots[i].RecommendedId, hero.Id + ": deterministic " + plan.Slots[i].Slot);
            }
        }

        [LogicTest]
        public static void PartyApplyLeavesEveryHeroAtLeastItsScore()
        {
            var db = TestMain.DB;
            var state = GameState.NewGame(db, Difficulty.Normal);
            OwnEveryPiece(db, state);
            var scoreBefore = new Dictionary<string, double>();
            var ownedBefore = new Dictionary<string, int>();
            foreach (var hero in state.Party) scoreBefore[hero.Id] = AutoEquip.ScoreOf(db, state, hero.Id);
            foreach (string id in db.Equipment.Keys) ownedBefore[id] = Owned(state, id);

            var plans = AutoEquip.PlanParty(db, state);
            var results = AutoEquip.ApplyParty(db, state);
            Assert.Equal(state.Party.Count, results.Count, "one result per party member");
            foreach (var result in results) Assert.True(result.Success, result.HeroId + " applied: " + result.Reason);
            foreach (var hero in state.Party)
                Assert.True(AutoEquip.ScoreOf(db, state, hero.Id) >= scoreBefore[hero.Id] - Eps, hero.Id + ": score not lower after party apply");
            foreach (var plan in plans)
                foreach (var slot in plan.Slots)
                    Assert.Equal(slot.RecommendedId, state.Hero(plan.HeroId).Equipped(slot.Slot), plan.HeroId + " wears the planned " + slot.Slot);
            foreach (var kv in ownedBefore) Assert.Equal(kv.Value, Owned(state, kv.Key), kv.Key + ": copies are neither lost nor duplicated");
        }
    }
}
