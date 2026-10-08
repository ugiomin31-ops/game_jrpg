// Gear / item / enhancement expansion (Tools/content/gear_items.py, CONTENT_20H_PLAN).
using System;
using System.Collections.Generic;
using System.IO;
using System.Linq;
using Abyss.Logic;
using Abyss.Logic.Battle;
using Abyss.Logic.Game;

namespace Abyss.LogicTests
{
    public static class GearExpansionTests
    {
        static string ResourcesDir => Path.GetFullPath(Path.Combine(Environment.GetEnvironmentVariable("ABYSS_DATA_DIR"), ".."));

        [LogicTest]
        public static void EnhancementStatAndCostMath()
        {
            var db = TestMain.DB;
            var iron = db.Equipment["sword_iron"];
            Assert.Equal(2, iron.Tier, "sword_iron is T2");
            Assert.Equal(14, Enhancement.Stats(iron, 0).Attack, "+0 keeps the base");
            Assert.Equal(18, Enhancement.Stats(iron, 3).Attack, "+3 = 14 + round(14 x 0.3)");
            Assert.Equal(28, Enhancement.Stats(iron, 10).Attack, "+10 doubles the base");
            Assert.Equal(0, Enhancement.Bonus(-10, 5), "negative trade-offs do not grow");
            var cost = Enhancement.CostOf(iron, 0);
            Assert.Equal(Enhancement.Stone, cost.StoneId, "T2 uses the basic stone");
            Assert.Equal(1, cost.Stones, "+1 costs one stone");
            Assert.Equal(40, cost.Gold, "+1 gold = 40 x 1");
            var step4 = Enhancement.CostOf(iron, 3);
            Assert.Equal(2, step4.Stones, "+4 costs two stones");
            Assert.Equal(160, step4.Gold, "+4 gold = 40 x 4");
            Assert.Equal(4, Enhancement.CostOf(iron, 9).Stones, "+10 costs four stones");
            Assert.True(Enhancement.CostOf(iron, 10) == null, "no step past +10");
            Assert.Equal(Enhancement.StoneHigh, Enhancement.CostOf(db.Equipment["sword_runic"], 0).StoneId, "T5 uses the high stone");
            Assert.Equal(Enhancement.StoneAbyss, Enhancement.CostOf(db.Equipment["sword_tidal"], 0).StoneId, "T6 uses the abyss stone");
            Assert.Equal("무쇠 장검 +3", Enhancement.DisplayName(iron, 3), "displayed name");
            Assert.Equal("무쇠 장검", Enhancement.DisplayName(iron, 0), "+0 has no suffix");
        }

        [LogicTest]
        public static void EnhanceAtSmithyRaisesWornStatsAndSurvivesSave()
        {
            var db = TestMain.DB;
            var state = GameState.NewGame(db, Difficulty.Normal);
            var warrior = state.Hero("warrior");
            string weapon = warrior.Equipped("weapon");
            int before = PartyStats.EffectiveStats(db, warrior).Stats.Attack;
            Assert.Equal("missing_materials", Enhancement.Enhance(db, state, weapon).Reason, "needs stones");
            Assert.Equal("not_owned", Enhancement.Enhance(db, state, "sword_void").Reason, "only owned pieces");
            state.AddItem(Enhancement.Stone, 30);
            state.Gold = 100000;
            for (int i = 0; i < 10; i++) Assert.True(Enhancement.Enhance(db, state, weapon).Success, "enhance step " + (i + 1));
            Assert.Equal("max_enhance", Enhancement.Enhance(db, state, weapon).Reason, "+10 is the cap");
            Assert.Equal(10, Enhancement.LevelOf(state, weapon), "level stored per id");
            var piece = db.Equipment[weapon];
            int after = PartyStats.EffectiveStats(db, warrior).Stats.Attack;
            Assert.Equal(before + piece.Atk, after, "+10 adds 100 % of the weapon's attack");
            Assert.Equal(30 - (1 + 1 + 1 + 2 + 2 + 2 + 3 + 3 + 3 + 4), state.ItemCount(Enhancement.Stone), "stones spent");
            var preview = PartyStats.PreviewEquipment(db, warrior, "weapon", weapon);
            Assert.Equal(after, preview.Stats.Attack, "gear compare preview includes enhancement");
            state.AddEquipment(weapon, 1);
            Assert.Equal(2, Enhancement.Candidates(db, state).First(e => e.Equipment.Id == weapon).Owned, "copies share the level");

            var loaded = SaveCodec.Deserialize(SaveCodec.Serialize(state), db);
            Assert.Equal(10, Enhancement.LevelOf(loaded, weapon), "enhancement saved");
            Assert.Equal(after, PartyStats.EffectiveStats(db, loaded.Hero("warrior")).Stats.Attack, "loaded hero bound to the map");
            var old = Newtonsoft.Json.Linq.JObject.Parse(SaveCodec.Serialize(state));
            old.Remove("enhancements");
            var legacy = SaveCodec.Deserialize(old.ToString(), db);
            Assert.Equal(0, Enhancement.LevelOf(legacy, weapon), "old saves load as +0");
            Assert.Equal(before, PartyStats.EffectiveStats(db, legacy.Hero("warrior")).Stats.Attack, "old save stats unchanged");
        }

        [LogicTest]
        public static void SeedsArePermanentCappedAndFieldOnly()
        {
            var db = TestMain.DB;
            var state = GameState.NewGame(db, Difficulty.Normal);
            var warrior = state.Hero("warrior");
            int atk = PartyStats.EffectiveStats(db, warrior).Stats.Attack;
            int hp = PartyStats.EffectiveStats(db, warrior).MaxHp;
            state.AddItem("seed_power", 2);
            state.AddItem("seed_life", 1);
            Assert.True(GameFlow.UseFieldItem(db, state, "seed_power", "warrior", false).Success, "seed used in town");
            Assert.True(GameFlow.UseFieldItem(db, state, "seed_life", "warrior", false).Success, "life seed used");
            Assert.Equal(atk + 2, PartyStats.EffectiveStats(db, warrior).Stats.Attack, "+2 attack");
            Assert.Equal(hp + 20, PartyStats.EffectiveStats(db, warrior).MaxHp, "+20 max HP");
            Assert.Equal(hp + 20, warrior.Hp, "current HP rises with the max");
            Assert.Equal(1, state.ItemCount("seed_power"), "one seed consumed");
            var loaded = SaveCodec.Deserialize(SaveCodec.Serialize(state), db);
            Assert.Equal(atk + 2, PartyStats.EffectiveStats(db, loaded.Hero("warrior")).Stats.Attack, "seed bonus saved");
            warrior.Seeds["attack"] = PartyStats.SeedCap("attack");
            var capped = GameFlow.UseFieldItem(db, state, "seed_power", "warrior", false);
            Assert.True(!capped.Success && capped.TextKey == "reason_seed_cap", "capped seed fails");
            Assert.Equal(1, state.ItemCount("seed_power"), "nothing consumed at the cap");
            state.AddItem("job_medal", 1);
            state.AddItem("camp_tent", 1);
            state.AddItem("megalixir", 1);
            var setup = PartyStats.BuildBattleSetup(db, state, BattleKind.Random, new[] { "slime" }, 1f, db.Floors[0].Id, 1);
            Assert.True(!setup.Inventory.ContainsKey("seed_power"), "seeds are not battle items");
            Assert.True(!setup.Inventory.ContainsKey("job_medal"), "key items are not battle items");
            Assert.True(!setup.Inventory.ContainsKey("camp_tent"), "tent is field only");
            Assert.True(setup.Inventory.ContainsKey("megalixir"), "megalixir is a battle item");
            Assert.Equal("not_sellable", TownServices.SellItem(db, state, "job_medal").Reason, "key items cannot be sold");
        }

        [LogicTest]
        public static void MegalixirAndTentRestoreMp()
        {
            var db = TestMain.DB;
            var state = GameState.NewGame(db, Difficulty.Normal);
            foreach (var h in state.Party) { h.Mp = 0; h.Hp = 5; }
            state.AddItem("camp_tent", 1);
            Assert.True(GameFlow.UseFieldItem(db, state, "camp_tent", null, true).Success, "tent used in the dungeon");
            foreach (var h in state.Party)
            {
                var stats = PartyStats.EffectiveStats(db, h);
                Assert.Equal(stats.MaxMp, h.Mp, "tent fills MP " + h.Id);
                Assert.Equal(stats.MaxHp, h.Hp, "tent fills HP " + h.Id);
            }

            var setup = BattleTestUtil.Setup(30, new[] { "slime" }, 7, BattleKind.Random, Difficulty.Normal, "warrior");
            setup.Party[0].Mp = 0;
            setup.Party[0].Hp = 10;
            setup.Inventory["megalixir"] = 1;
            var engine = new BattleEngine(db, setup);
            engine.Start();
            Assert.True(engine.State == BattleEngineState.AwaitingCommand, "hero turn");
            engine.Submit(BattleCommand.Item("megalixir", engine.ActiveHero.Id));
            var hero = engine.Party[0];
            Assert.True(hero.Mp >= hero.MaxMp - 1, "megalixir restores MP in battle");
            Assert.True(engine.InventoryCount("megalixir") == 0, "consumed");
        }

        [LogicTest]
        public static void GearEffectsReachBattleAndRewards()
        {
            var db = TestMain.DB;
            var state = GameState.NewGame(db, Difficulty.Normal);
            state.AddEquipment("acc_exp_charm", 1);
            state.AddEquipment("acc_gold_charm", 1);
            Assert.True(PartyStats.Equip(db, state, "warrior", "acc_exp_charm").Success, "exp charm on");
            Assert.True(PartyStats.Equip(db, state, "mage", "acc_gold_charm").Success, "gold charm on");
            int gold = state.Gold;
            var outcome = new BattleOutcome { Result = BattleResult.Victory, Experience = 10, Gold = 100 };
            var report = PartyStats.ApplyBattleOutcome(db, state, outcome);
            Assert.Equal(13, report.ExperienceByHero["warrior"], "wearer gets +30 % EXP");
            Assert.Equal(10, report.ExperienceByHero["mage"], "others get the base EXP");
            Assert.Equal(125, report.Gold, "party gold +25 %");
            Assert.Equal(gold + 125, state.Gold, "gold credited");

            state.AddEquipment("acc_regen_ring", 1);
            state.AddEquipment("sword_holy_avenger", 1);
            PartyStats.Equip(db, state, "warrior", "acc_regen_ring");
            PartyStats.Equip(db, state, "warrior", "sword_holy_avenger");
            var spec = PartyStats.BuildCombatSpec(db, state, "warrior");
            Assert.Equal((int)Element.Holy, spec.AttackElement, "weapon element on plain attacks");
            Assert.Near(0.05, spec.HpRegen, 1e-6, "regen ring ratio");

            var setup = BattleTestUtil.Setup(30, new[] { "slime", "slime" }, 11, BattleKind.Random, Difficulty.Normal, "warrior");
            var w = setup.Party[0];
            w.HpRegen = 0.1f; w.MpRegen = 5; w.TpStart = 30; w.AttackElement = (int)Element.Fire;
            w.Hp = w.MaxHp / 2; w.Mp = 0;
            var engine = new BattleEngine(db, setup);
            Assert.Equal(30, engine.Party[0].Tp, "battle starts with gear TP");
            Assert.Equal((int)Element.Fire, engine.Party[0].AttackElement, "attack element from the spec");
            var events = BattleTestUtil.RunAuto(engine);
            string id = engine.Party[0].Id;
            Assert.True(events.OfType<HealEvent>().Any(e => e.TargetId == id && e.StatusId == null), "end-of-turn HP regen");
            Assert.True(events.OfType<MpChangeEvent>().Any(e => e.UnitId == id && e.Delta > 0), "end-of-turn MP regen");
        }

        [LogicTest]
        public static void ShopTierFollowsChaptersAndLegendariesAreNeverSold()
        {
            var db = TestMain.DB;
            Assert.Equal(1, TownServices.ChapterOfFloor(0), "B1F chapter 1");
            Assert.Equal(1, TownServices.ChapterOfFloor(4), "B5F chapter 1");
            Assert.Equal(2, TownServices.ChapterOfFloor(5), "B6F chapter 2");
            Assert.Equal(6, TownServices.ChapterOfFloor(29), "B30F chapter 6");
            Assert.Equal(7, TownServices.ChapterOfFloor(30), "postgame");
            Assert.Equal(7, TownServices.ChapterOfFloor(99), "capped");
            var state = GameState.NewGame(db, Difficulty.Normal);
            state.Gold = 1000000;
            Assert.Equal(1, TownServices.ShopTier(state), "start");
            Assert.Equal("tier_locked", TownServices.BuyEquipment(db, state, "sword_runic").Reason, "T5 locked in chapter 1");
            state.DeepestFloor = 15;
            Assert.Equal(4, TownServices.ShopTier(state), "chapter 4");
            Assert.True(TownServices.BuyEquipment(db, state, "sword_runic").Success, "T5 sold in chapter 4");
            Assert.Equal("tier_locked", TownServices.BuyEquipment(db, state, "sword_tidal").Reason, "T6 needs chapter 5");
            state.DeepestFloor = 0;
            state.Flags.Add(GameFlow.FlagCleared);
            Assert.Equal(7, TownServices.ShopTier(state), "clearing opens the postgame shop");
            var stock = TownServices.ShopStock(db, state, true);
            foreach (var line in new[] { "sword", "staff", "bow", "mace", "armor", "robe", "garb" })
            {
                var pieces = db.Equipment.Values.Where(e => e.Id.StartsWith(line + "_") && e.Jobs.Count == 0 && e.Slot != "accessory").ToList();
                Assert.Equal(8, pieces.Count, line + " has 8 tiers");
                for (int t = 1; t <= 8; t++) Assert.Equal(1, pieces.Count(p => p.Tier == t), line + " T" + t);
            }
            Assert.True(stock.All(r => db.Equipment[r.Id].Tier < 8), "no T8 in the shop");
            Assert.True(stock.All(r => db.Equipment[r.Id].Jobs.Count == 0), "job weapons are crafted, not sold");
            Assert.True(stock.Where(r => db.Equipment[r.Id].Slot != "accessory").All(r => r.ShopTier == Math.Max(1, db.Equipment[r.Id].Tier - 1)), "shop tier = chapter of the tier");
        }

        [LogicTest]
        public static void VariantModelsResolveThroughData()
        {
            var db = TestMain.DB;
            var variant = new EnemyDef { Id = "ice_slime", Model = "slime", Tint = new[] { 0.55f, 0.85f, 1f, 1f } };
            Assert.Equal("slime", ArtVariants.EnemyModel(variant), "variant uses the base model");
            Assert.Near(0.55, ArtVariants.EnemyTint(variant)[0], 1e-6, "variant tint");
            var own = new EnemyDef { Id = "elite_bat", Tint = new[] { 1f, 0.45f, 0.45f, 1f } };
            Assert.Equal("elite_bat", ArtVariants.EnemyModel(own), "own model by default");
            Assert.True(ArtVariants.EnemyTint(own) == null, "own-model tints are baked into the FBX, not re-applied");
            Assert.Equal("unknown_id", ArtVariants.EnemyModel(db, "unknown_id"), "unknown ids resolve to themselves");
            Assert.Equal("armor_dawn", ArtVariants.GearModel(db, "armor_void"), "armour reuses a model");
            Assert.Equal(4, ArtVariants.GearTint(db, "armor_void").Length, "armour tint");
            Assert.Equal("sword_runic", ArtVariants.GearModel(db, "sword_runic"), "new weapons have their own model");
            Assert.True(ArtVariants.GearTint(db, "sword_runic") == null, "and no tint");
            Assert.Equal(1f, ArtVariants.Normalise(new[] { 0.5f, 0.5f, 0.5f })[3], "alpha defaults to 1");
        }

        [LogicTest]
        public static void EveryGearAndItemHasArtIconAndValidRecipe()
        {
            var db = TestMain.DB;
            string res = ResourcesDir;
            var missing = new List<string>();
            foreach (var piece in db.Equipment.Values)
            {
                if (!File.Exists(Path.Combine(res, "Icons", "Gear", piece.Id + ".png"))) missing.Add("icon Gear/" + piece.Id);
                string model = ArtVariants.GearModel(piece);
                string fbx = piece.Slot == "weapon" ? Path.Combine(res, "Art", "Weapons", model + ".fbx") : Path.Combine(res, "Art", "Props", "Equipment", model + ".fbx");
                if (!File.Exists(fbx)) missing.Add("model " + fbx);
                Assert.True(piece.Tier >= 1 && piece.Tier <= 8, piece.Id + " tier");
                Assert.True(piece.Jobs != null, piece.Id + " jobs list");
                foreach (var kv in piece.CraftMaterials)
                    Assert.True(db.Items.TryGetValue(kv.Key, out var m) && m.ItemType == ItemType.Material && kv.Value > 0, piece.Id + " recipe material " + kv.Key);
                foreach (string status in piece.StatusImmunities) Assert.True(db.Statuses.ContainsKey(status), piece.Id + " immunity " + status);
            }
            foreach (var item in db.Items.Values)
            {
                if (!File.Exists(Path.Combine(res, "Icons", "Items", item.Id + ".png"))) missing.Add("icon Items/" + item.Id);
                if (!File.Exists(Path.Combine(res, "Art", "Props", "Items", ArtVariants.ItemModel(item) + ".fbx"))) missing.Add("model Items/" + item.Id);
                if (item.ItemType == ItemType.Seed) Assert.True(PartyStats.SeedCap(item.Stat) > 0 && item.Value > 0, item.Id + " seed stat");
                if (item.ItemType == ItemType.Buff) Assert.True(db.Statuses.ContainsKey(item.StatusId), item.Id + " buff status");
            }
            Assert.True(missing.Count == 0, "missing art:\n" + string.Join("\n", missing));
            int jobWeapons = db.Equipment.Values.Count(e => e.Jobs.Count > 0);
            Assert.Equal(16, jobWeapons, "16 job weapons");
        }
    }
}
