using System.Linq;
using Abyss.Logic;
using Abyss.Logic.Dungeon;
using Abyss.Logic.Game;
using Newtonsoft.Json.Linq;

namespace Abyss.LogicTests
{
    public static class SaveMigrationRepairTests
    {
        [LogicTest]
        public static void NullLegacyPartyEntryLoadsAndRepairsMissingHunters()
        {
            var loaded = SaveCodec.Deserialize("{\"version\":1,\"party\":[null,{\"id\":\"warrior\"}]}", TestMain.DB);
            Assert.Equal(GameState.PartySize, loaded.Party.Count, "missing starters restored");
            Assert.Equal("h_dohyun", loaded.Party[0].Id, "legacy warrior retained in formation");
            Assert.True(loaded.AllHunters().All(h => h != null), "null entries removed");
            AssertStableReload(loaded);
        }

        [LogicTest]
        public static void NullSlotsInEitherRosterPreserveLegacyHeroProgress()
        {
            var db = TestMain.DB;
            foreach (bool legacyInReserve in new[] { false, true })
            foreach (string nullableRoster in new[] { "party", "reserve" })
            {
                var state = GameState.NewGame(db, Difficulty.Normal);
                var original = state.Party[0];
                original.Level = 9; original.Xp = 37;
                state.Repair(db);
                var root = JObject.Parse(SaveCodec.Serialize(state));
                root["flags"] = new JArray(CampaignMigration.FlagLayout);
                var party = (JArray)root["party"];
                var reserve = (JArray)root["reserve"];
                var legacy = (JObject)party[0];
                legacy["id"] = "warrior";
                if (legacyInReserve) { party.RemoveAt(0); reserve.Add(legacy); }
                ((JArray)root[nullableRoster]).Insert(0, JValue.CreateNull());

                var loaded = SaveCodec.Deserialize(root.ToString(), db);
                var hunter = loaded.Hero("h_dohyun");
                Assert.True(hunter != null, "legacy hunter survives null " + nullableRoster);
                Assert.Equal(legacyInReserve, loaded.Reserve.Contains(hunter), "formation membership kept");
                Assert.Equal(9, hunter.Level, "level kept");
                Assert.Equal(37, hunter.Xp, "XP kept");
                Assert.Equal(original.Job, hunter.Job, "job kept");
                Assert.Equal(original.Hp, hunter.Hp, "HP kept");
                Assert.Equal(original.Mp, hunter.Mp, "MP kept");
                foreach (string slot in GameState.EquipSlots)
                    Assert.Equal(original.Equipped(slot), hunter.Equipped(slot), "equipment kept: " + slot);
                Assert.True(original.LearnedSkills.SequenceEqual(hunter.LearnedSkills), "learned skills kept");
                Assert.Equal(4, loaded.AllHunters().Count(), "no extra or missing starters");
                Assert.True(loaded.AllHunters().All(h => h != null), "both rosters have no nulls");
                AssertStableReload(loaded);
            }
        }

        [LogicTest]
        public static void NullSlotsDoNotOverwriteAnExistingHunterWithLegacyDuplicate()
        {
            var loaded = SaveCodec.Deserialize("{\"version\":1,\"party\":[null,{\"id\":\"warrior\",\"level\":9}],"
                + "\"reserve\":[null,{\"id\":\"h_dohyun\",\"level\":12}]}", TestMain.DB);
            Assert.Equal(1, loaded.AllHunters().Count(h => h.Id == "h_dohyun"), "one current hunter retained");
            Assert.Equal(12, loaded.Hero("h_dohyun").Level, "existing hunter takes precedence");
            Assert.True(loaded.Reserve.Contains(loaded.Hero("h_dohyun")), "existing reserve placement kept");
            AssertStableReload(loaded);
        }

        [LogicTest]
        public static void CompletedLegacyPostgameRetainsBossCellObjectiveAndLateQuestCredit()
        {
            var db = TestMain.DB;
            var state = LegacyPostgame(completed: true);
            int gold = state.Gold;
            var loaded = SaveCodec.Deserialize(SaveCodec.Serialize(state), db);
            Assert.Equal(38, loaded.FloorIndex, "old final floor mapped to current postgame boss floor");
            Assert.Equal(38, loaded.DeepestFloor, "postgame progress retained");
            Assert.Equal(GameLocation.Town, loaded.Location, "old dungeon position resumes in town");
            for (int zone = 1; zone <= 13; zone++)
            {
                Assert.True(loaded.Flags.Contains(GameFlow.BossFlag(zone)), "completed zone retained: " + zone);
                var floor = db.Floors[zone * GameFlow.FloorsPerChapter - 1];
                var grid = DungeonGrid.Parse(floor, loaded.Floor(floor.Id));
                Assert.True(grid.Progress.ClearedBattles.Contains(grid.FindCell('B')), "boss stays cleared: " + zone);
            }
            Assert.True(loaded.Flags.Contains(JobService.BossDefeatedFlag("abyss_lord_ex")), "postgame boss credit retained");
            Assert.True(ExpeditionReadiness.Evaluate(db, loaded).ObjectiveText.Contains("붉은 게이트 공략 완료"), "guild recognizes completion");
            Assert.True(QuestLog.Accept(db, loaded, "q_ex_lord").Success, "late postgame bounty accepted");
            Assert.Equal(QuestState.Complete, loaded.Quests["q_ex_lord"].State, "old victory satisfies late bounty");
            Assert.Equal(gold, loaded.Gold, "migration and acceptance do not grant rewards");
            Assert.True(QuestLog.Claim(db, loaded, "q_ex_lord").Success, "bounty claim succeeds");
            Assert.Equal(gold + db.Quests["q_ex_lord"].RewardGold, loaded.Gold, "reward paid once");
            var reloaded = SaveCodec.Deserialize(SaveCodec.Serialize(loaded), db);
            Assert.True(!QuestLog.Claim(db, reloaded, "q_ex_lord").Success, "reload does not allow another reward");
            AssertStableReload(reloaded);
        }

        [LogicTest]
        public static void ReachingLegacyPostgameWithoutVictoryDoesNotGrantCompletion()
        {
            var db = TestMain.DB;
            var loaded = SaveCodec.Deserialize(SaveCodec.Serialize(LegacyPostgame(completed: false)), db);
            Assert.Equal(38, loaded.DeepestFloor, "boss floor remains reachable");
            Assert.True(!loaded.Flags.Contains(GameFlow.BossFlag(13)), "unbeaten postgame stays unbeaten");
            var floor = db.Floors[38];
            var grid = DungeonGrid.Parse(floor, loaded.Floor(floor.Id));
            Assert.True(!grid.Progress.ClearedBattles.Contains(grid.FindCell('B')), "boss cell is not cleared by floor reach");
            Assert.True(QuestLog.Accept(db, loaded, "q_ex_lord").Success, "bounty unlocked by reaching floor");
            Assert.Equal(QuestState.Accepted, loaded.Quests["q_ex_lord"].State, "bounty still needs victory");
            AssertStableReload(loaded);
        }

        [LogicTest]
        public static void ValidHunterLayoutSaveKeepsItsCurrentZoneSevenProgress()
        {
            var db = TestMain.DB;
            var state = GameState.NewGame(db, Difficulty.Normal);
            GameFlow.CompletePrologue(state);
            for (int zone = 1; zone <= 7; zone++) state.Flags.Add(GameFlow.BossFlag(zone));
            state.DeepestFloor = 21;
            string saved = SaveCodec.Serialize(state);
            var loaded = SaveCodec.Deserialize(saved, db);
            Assert.Equal(saved, SaveCodec.Serialize(loaded), "valid current-layout save unchanged");
            Assert.True(!loaded.Flags.Contains(GameFlow.BossFlag(13)), "current zone seven is not legacy postgame");
        }

        static GameState LegacyPostgame(bool completed)
        {
            var state = GameState.NewGame(TestMain.DB, Difficulty.Normal);
            GameFlow.CompletePrologue(state);
            state.Flags.Remove(CampaignMigration.FlagHunterLayout);
            state.Flags.Add(GameFlow.FlagCleared);
            state.Flags.Add(GameFlow.FlagEndingSeen);
            for (int chapter = 1; chapter <= (completed ? 7 : 6); chapter++)
                state.Flags.Add(GameFlow.BossFlag(chapter));
            state.FloorIndex = 34; state.DeepestFloor = 34;
            state.Location = GameLocation.Dungeon;
            return state;
        }

        static void AssertStableReload(GameState state)
        {
            string once = SaveCodec.Serialize(state);
            Assert.Equal(once, SaveCodec.Serialize(SaveCodec.Deserialize(once, TestMain.DB)), "repeated repair is idempotent");
        }
    }
}
