// Hunter roster: starting party, story joins after zone bosses, guild scouts, party formation, bench EXP and the
// move of saves made with the four original heroes.
using System.Linq;
using Abyss.Logic;
using Abyss.Logic.Game;
using Newtonsoft.Json.Linq;

namespace Abyss.LogicTests
{
    public static class HunterRosterTests
    {
        [LogicTest]
        public static void NewGameStartsWithFourHuntersOfDistinctClasses()
        {
            var db = TestMain.DB;
            var state = GameState.NewGame(db, Difficulty.Normal);
            Assert.True(state.Party.Select(h => h.Id).SequenceEqual(new[] { "h_dohyun", "h_seoa", "h_jiho", "h_yuna" }), "starting hunters in order");
            Assert.Equal(0, state.Reserve.Count, "empty reserve");
            foreach (var hero in state.Party)
            {
                Assert.Equal(db.ClassOf(hero.Id), hero.Job, hero.Id + " starts in its class");
                Assert.True(hero.LearnedSkills.Any(s => s.StartsWith("sig_")), hero.Id + " knows its signature skill");
            }
        }

        [LogicTest]
        public static void OldSavesWithTheFourHeroesBecomeTheStartingHunters()
        {
            var db = TestMain.DB;
            var state = GameState.NewGame(db, Difficulty.Normal);
            state.Party[0].Level = 9;
            var root = JObject.Parse(SaveCodec.Serialize(state));
            var oldIds = new[] { "warrior", "mage", "archer", "cleric" };
            var party = (JArray)root["party"];
            for (int i = 0; i < party.Count; i++) party[i]["id"] = oldIds[i];
            root.Remove("reserve");
            var loaded = SaveCodec.Deserialize(root.ToString(), db);
            Assert.True(loaded.Party.Select(h => h.Id).SequenceEqual(new[] { "h_dohyun", "h_seoa", "h_jiho", "h_yuna" }), "old heroes renamed");
            Assert.Equal(9, loaded.Hero("h_dohyun").Level, "level kept");
            Assert.Equal(0, loaded.Reserve.Count, "no duplicates in the reserve");
        }

        [LogicTest]
        public static void ZoneBossBringsAStoryHunterOnGuildReturn()
        {
            var db = TestMain.DB;
            var state = GameState.NewGame(db, Difficulty.Normal);
            foreach (var hero in state.Party) hero.Level = 6;
            state.Flags.Add(GameFlow.BossFlag(1));
            var notices = GameFlow.EnterTown(db, state);
            var join = notices.FirstOrDefault(n => n.HeroId == "h_minjun");
            Assert.True(join != null, "join notice for the zone 1 hunter");
            var minjun = state.Hero("h_minjun");
            Assert.True(minjun != null && state.Reserve.Contains(minjun), "full party: the new hunter waits in the reserve");
            Assert.Equal(6, minjun.Level, "joins at the roster's average level");
            Assert.True(!GameFlow.EnterTown(db, state).Any(n => n.HeroId != null), "joins only once");
        }

        [LogicTest]
        public static void ScoutsUnlockByZoneAndCostMoney()
        {
            var db = TestMain.DB;
            var state = GameState.NewGame(db, Difficulty.Normal);
            var bora = HunterRoster.ScoutOffers(db, state).Single(o => o.Hunter.Id == "h_bora");
            Assert.True(!bora.Unlocked, "locked before her zone");
            Assert.Equal("scout_locked", HunterRoster.Scout(db, state, "h_bora").Reason, "cannot hire early");
            state.DeepestFloor = (bora.Hunter.JoinZone - 1) * GameFlow.FloorsPerChapter;
            state.Gold = bora.Price - 1;
            Assert.Equal("reason_not_enough_gold", HunterRoster.Scout(db, state, "h_bora").Reason, "needs the fee");
            state.Gold = bora.Price + 5;
            Assert.True(HunterRoster.Scout(db, state, "h_bora").Success, "hired");
            Assert.Equal(5, state.Gold, "fee paid");
            Assert.True(state.Hero("h_bora") != null, "recruited");
            Assert.True(HunterRoster.ScoutOffers(db, state).All(o => o.Hunter.Id != "h_bora"), "gone from the list");
            var loaded = SaveCodec.Deserialize(SaveCodec.Serialize(state), db);
            Assert.True(loaded.Reserve.Any(h => h.Id == "h_bora"), "reserve survives a save");
        }

        [LogicTest]
        public static void PartyFormationSwapsAndBenchKeepsOneHunter()
        {
            var db = TestMain.DB;
            var state = GameState.NewGame(db, Difficulty.Normal);
            state.Flags.Add(GameFlow.BossFlag(1));
            GameFlow.EnterTown(db, state);
            Assert.True(HunterRoster.PutInParty(state, "h_minjun", 1).Success, "swap into slot 2");
            Assert.Equal("h_minjun", state.Party[1].Id, "in the party");
            Assert.True(state.Reserve.Any(h => h.Id == "h_seoa"), "replaced hunter benched");
            HunterRoster.SwapSlots(state, 0, 1);
            Assert.Equal("h_minjun", state.Party[0].Id, "formation order changed");
            while (state.Party.Count > 1) Assert.True(HunterRoster.Bench(state, state.Party[0].Id).Success, "bench");
            Assert.Equal("roster_last_member", HunterRoster.Bench(state, state.Party[0].Id).Reason, "keeps one hunter");
            Assert.True(HunterRoster.PutInParty(state, state.Reserve[0].Id, 9).Success, "append when there is room");
            state.Location = GameLocation.Dungeon;
            Assert.Equal("roster_town_only", HunterRoster.Bench(state, state.Party[0].Id).Reason, "only at the guild");
        }

        [LogicTest]
        public static void BenchedHuntersEarnHalfTheBattleExp()
        {
            var db = TestMain.DB;
            var state = GameState.NewGame(db, Difficulty.Normal);
            state.Flags.Add(GameFlow.BossFlag(1));
            GameFlow.EnterTown(db, state);
            var minjun = state.Hero("h_minjun");
            int xp = minjun.Xp, level = minjun.Level;
            HunterRoster.AwardBenchXp(db, state, 10);
            Assert.True(minjun.Level > level || minjun.Xp == xp + 5, "half of 10 EXP");
        }
    }
}
