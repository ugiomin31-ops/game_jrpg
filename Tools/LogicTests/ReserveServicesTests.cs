using System;
using System.IO;
using System.Linq;
using Abyss.Logic;
using Abyss.Logic.Dungeon;
using Abyss.Logic.Game;

namespace Abyss.LogicTests
{
    public static class ReserveServicesTests
    {
        static GameState WithReserve()
        {
            var state = GameState.NewGame(TestMain.DB, Difficulty.Normal);
            Assert.True(HunterRoster.Bench(state, "h_dohyun").Success, "bench starting hunter with gear");
            return state;
        }

        static void Wound(GameState state)
        {
            foreach (var hero in state.AllHunters())
            {
                hero.Hp = 0;
                hero.Mp = 0;
                hero.Tp = 37;
                hero.Statuses["poison"] = 3;
            }
            var floor = state.Floor(TestMain.DB.Floors[0].Id);
            floor.SpentSprings.Add(new GridPos(2, 1));
            floor.DefeatedFoes.Add("reserve_test_foe");
        }

        static void AssertRestored(GameState state)
        {
            foreach (var hero in state.AllHunters())
            {
                var stats = PartyStats.EffectiveStats(TestMain.DB, hero);
                Assert.Equal(stats.MaxHp, hero.Hp, hero.Id + " revived to effective HP");
                Assert.Equal(stats.MaxMp, hero.Mp, hero.Id + " restored MP");
                Assert.Equal(0, hero.Statuses.Count, hero.Id + " statuses cleared");
                Assert.Equal(0, hero.Tp, hero.Id + " carried TP cleared");
            }
        }

        static void CheckRest(bool free)
        {
            var db = TestMain.DB;
            var state = WithReserve();
            Wound(state);
            int cost = free ? 0 : TownServices.InnCost(state);
            state.Gold = cost;
            var result = TownServices.RestAtInn(db, state, free);
            Assert.True(result.Success && result.RequestsAutosave, "rest succeeds and requests autosave");
            Assert.Equal(-cost, result.GoldDelta, "exact rest cost");
            Assert.Equal(0, state.Gold, "exact funds spent (free works at zero)");
            AssertRestored(state);
            Assert.True(state.Floors.Values.All(f => f.SpentSprings.Count == 0 && f.DefeatedFoes.Count == 0), "springs and FOEs reset");
            var loaded = SaveCodec.Deserialize(SaveCodec.Serialize(state), db);
            Assert.True(loaded.Reserve.Any(h => h.Id == "h_dohyun"), "reserve membership survives save");
            AssertRestored(loaded);
            Assert.Equal(0, loaded.Gold, "payment survives save");
        }

        [LogicTest]
        public static void PaidInnRestoresReserveAndSaveRoundtrip() => CheckRest(false);

        [LogicTest]
        public static void FreeInnRestoresReserveAndSaveRoundtrip() => CheckRest(true);

        [LogicTest]
        public static void UnaffordableInnChangesNothing()
        {
            var state = WithReserve();
            Wound(state);
            state.Gold = TownServices.InnCost(state) - 1;
            string before = SaveCodec.Serialize(state);
            var result = TownServices.RestAtInn(TestMain.DB, state);
            Assert.True(!result.Success && !result.RequestsAutosave, "failed rest does not request save");
            Assert.Equal("not_enough_gold", result.Reason, "payment failure");
            Assert.Equal(0, result.GoldDelta, "no payment");
            Assert.Equal(before, SaveCodec.Serialize(state), "entire campaign, reserve and floor progress unchanged");
        }

        [LogicTest]
        public static void DefaultRestoreKeepsSpringActiveOnlyAndTpSemantics()
        {
            var state = WithReserve();
            Wound(state);
            PartyStats.RestoreParty(TestMain.DB, state);
            foreach (var hero in state.Party)
            {
                var stats = PartyStats.EffectiveStats(TestMain.DB, hero);
                Assert.Equal(stats.MaxHp, hero.Hp, "active HP restored");
                Assert.Equal(stats.MaxMp, hero.Mp, "active MP restored");
                Assert.Equal(0, hero.Statuses.Count, "active statuses cleared");
            }
            var reserve = state.Reserve.Single();
            Assert.Equal(0, reserve.Hp, "reserve stays KO");
            Assert.Equal(0, reserve.Mp, "reserve MP unchanged");
            Assert.Equal(3, reserve.Statuses["poison"], "reserve status unchanged");
            Assert.True(state.AllHunters().All(h => h.Tp == 37), "default restore keeps everyone's TP");
        }

        [LogicTest]
        public static void BenchingPreservesWornOwnershipAndCandidates()
        {
            var db = TestMain.DB;
            var state = GameState.NewGame(db, Difficulty.Normal);
            string weapon = state.Hero("h_dohyun").Equipped("weapon");
            int owned = Enhancement.OwnedCount(state, weapon);
            Assert.Equal(1, owned, "one starting sword, no spare");
            Assert.True(HunterRoster.Bench(state, "h_dohyun").Success, "bench");
            Assert.Equal(1, PartyStats.EquippedCount(state, weapon), "reserve counts as worn inventory");
            Assert.Equal(owned, Enhancement.OwnedCount(state, weapon), "ownership conserved by benching");
            Assert.Equal(owned, Enhancement.Candidates(db, state).Single(e => e.Equipment.Id == weapon).Owned, "reserve sword remains listed");
        }

        [LogicTest]
        public static void ReserveOnlyGearRemainsEnhancementCandidate()
        {
            var state = WithReserve();
            string weapon = state.Reserve.Single().Equipped("weapon");
            Assert.True(Enhancement.Candidates(TestMain.DB, state).Any(e => e.Equipment.Id == weapon), "reserve-only equipment listed");
        }

        [LogicTest]
        public static void ReserveOnlyEnhancementChargesExactlyAndSurvivesSave()
        {
            var db = TestMain.DB;
            var state = WithReserve();
            var hero = state.Reserve.Single();
            string weapon = hero.Equipped("weapon");
            var cost = Enhancement.CostOf(db.Equipment[weapon], 0);
            state.Gold = cost.Gold + 7;
            state.AddItem(cost.StoneId, cost.Stones + 2);
            int attack = PartyStats.EffectiveStats(db, hero).Stats.Attack;
            var result = Enhancement.Enhance(db, state, weapon);
            Assert.True(result.Success, "reserve-only owned gear can be enhanced");
            Assert.Equal(-cost.Gold, result.GoldDelta, "exact reported cost");
            Assert.Equal(7, state.Gold, "exact gold spent");
            Assert.Equal(2, state.ItemCount(cost.StoneId), "exact stones spent");
            Assert.Equal(1, Enhancement.OwnedCount(state, weapon), "enhancing does not create or consume gear");
            int expected = attack + Enhancement.Bonus(db.Equipment[weapon].Atk, 1);
            Assert.Equal(expected, PartyStats.EffectiveStats(db, hero).Stats.Attack, "reserve wearer gets bonus");
            state.AddEquipment(weapon, 1);
            var loaded = SaveCodec.Deserialize(SaveCodec.Serialize(state), db);
            Assert.Equal(2, Enhancement.OwnedCount(loaded, weapon), "worn and spare copies survive save");
            Assert.Equal(1, Enhancement.LevelOf(loaded.Hero(hero.Id), weapon), "reserve bound to shared enhancement map");
            Assert.Equal(expected, PartyStats.EffectiveStats(db, loaded.Hero(hero.Id)).Stats.Attack, "reserve stats survive save");
            Assert.Equal(expected, PartyStats.PreviewEquipment(db, loaded.Hero(hero.Id), "weapon", weapon).Stats.Attack, "spare copy shares enhancement");
        }

        [LogicTest]
        public static void UnaffordableReserveEnhancementChangesNothing()
        {
            var state = WithReserve();
            string weapon = state.Reserve.Single().Equipped("weapon");
            var cost = Enhancement.CostOf(TestMain.DB.Equipment[weapon], 0);
            state.Gold = cost.Gold - 1;
            state.AddItem(cost.StoneId, cost.Stones);
            string before = SaveCodec.Serialize(state);
            var result = Enhancement.Enhance(TestMain.DB, state, weapon);
            Assert.Equal("not_enough_gold", result.Reason, "reserve ownership passes before payment check");
            Assert.True(!result.Success, "unaffordable enhancement fails");
            Assert.Equal(before, SaveCodec.Serialize(state), "failed enhancement consumes nothing");
        }

        [LogicTest]
        public static void ReserveEquipmentTransfersConservePieces()
        {
            var state = WithReserve();
            var hero = state.Reserve.Single();
            string weapon = hero.Equipped("weapon");
            Assert.True(PartyStats.Unequip(TestMain.DB, state, hero.Id, "weapon").Success, "unequip reserve");
            Assert.Equal(1, state.BagCount(weapon), "worn piece returned to bag");
            Assert.Equal(1, Enhancement.OwnedCount(state, weapon), "unequip conserves count");
            Assert.True(PartyStats.Equip(TestMain.DB, state, hero.Id, weapon).Success, "equip reserve");
            Assert.Equal(0, state.BagCount(weapon), "piece removed from bag");
            Assert.Equal(1, Enhancement.OwnedCount(state, weapon), "equip conserves count");
            string before = SaveCodec.Serialize(state);
            Assert.True(!TownServices.SellEquipment(TestMain.DB, state, weapon).Success, "cannot sell reserve's worn piece");
            Assert.Equal(before, SaveCodec.Serialize(state), "failed sale preserves worn piece");
            Assert.True(HunterRoster.PutInParty(state, hero.Id, 0).Success, "return reserve to party");
            Assert.Equal(1, Enhancement.OwnedCount(state, weapon), "roster swap conserves gear");
        }

        static void CheckSale(bool equipment, bool overflow, bool hugePrice = false)
        {
            var db = hugePrice ? GameDB.Load(t => File.ReadAllText(Path.Combine(Environment.GetEnvironmentVariable("ABYSS_DATA_DIR"), t + ".json"))) : TestMain.DB;
            var state = GameState.NewGame(db, Difficulty.Normal);
            string id = equipment ? "sword_iron" : "abyss_crystal";
            const int count = 3;
            if (hugePrice)
            {
                if (equipment) db.Equipment[id].SellPrice = int.MaxValue / 2 + 1;
                else db.Items[id].SellPrice = int.MaxValue / 2 + 1;
            }
            if (equipment) state.AddEquipment(id, count);
            else state.AddItem(id, count);
            int beforeCount = equipment ? state.BagCount(id) : state.ItemCount(id);
            int value = equipment ? TownServices.EquipmentSellValue(db, id) : TownServices.ItemSellValue(db, id);
            long proceeds = (long)value * count;
            state.Gold = hugePrice ? 0 : int.MaxValue - (int)proceeds + (overflow ? 1 : 0);
            string before = SaveCodec.Serialize(state);
            var result = equipment ? TownServices.SellEquipment(db, state, id, count) : TownServices.SellItem(db, state, id, count);
            if (overflow)
            {
                Assert.True(!result.Success, "overflow sale rejected");
                Assert.Equal(0, result.GoldDelta, "rejected sale reports no proceeds");
                Assert.Equal(before, SaveCodec.Serialize(state), "overflow rejected before inventory, gold or quests mutate");
            }
            else
            {
                Assert.True(result.Success, "exact upper limit accepted");
                Assert.Equal(int.MaxValue, state.Gold, "exact gold maximum");
                Assert.Equal((int)proceeds, result.GoldDelta, "exact batch proceeds");
                Assert.Equal(beforeCount - count, equipment ? state.BagCount(id) : state.ItemCount(id), "only sold pieces consumed");
            }
        }

        [LogicTest]
        public static void ItemSaleOverflowDoesNotConsumeInventory() => CheckSale(false, true);
        [LogicTest]
        public static void EquipmentSaleOverflowDoesNotConsumeInventory() => CheckSale(true, true);
        [LogicTest]
        public static void ItemSaleAtGoldLimitIsExact() => CheckSale(false, false);
        [LogicTest]
        public static void EquipmentSaleAtGoldLimitIsExact() => CheckSale(true, false);
        [LogicTest]
        public static void ItemSaleBatchMultiplicationCannotOverflow() => CheckSale(false, true, true);
        [LogicTest]
        public static void EquipmentSaleBatchMultiplicationCannotOverflow() => CheckSale(true, true, true);
    }
}
