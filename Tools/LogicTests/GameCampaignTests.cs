using System;
using System.Collections.Generic;
using System.IO;
using Abyss.Logic;
using Abyss.Logic.Dungeon;
using Abyss.Logic.Game;

namespace Abyss.LogicTests
{
    public static class GameCampaignTests
    {
        [LogicTest]
        public static void SaveRoundtripRetainsLocationDoorsKeysAndPendingEncounter()
        {
            var db = TestMain.DB;
            var state = GameState.NewGame(db, Difficulty.Hard);
            GameFlow.CompletePrologue(state);
            var run = new DungeonRun(db, state, 1, ArrivalMode.Descending);
            state.Facing = Facing.South;
            var progress = run.Grid.Progress;
            progress.Keys = 2;
            progress.OpenedChests.Add(new GridPos(1, 11));
            progress.TakenKeys.Add(new GridPos(2, 2));
            progress.OpenedDoors.Add(new GridPos(2, 3));
            progress.DefeatedFoes.Add("saved_foe");
            state.PendingBattle = new DungeonBattleRequest { Kind = BattleKind.Event, FloorId = run.Grid.Floor.Id,
                Cell = state.Position, RetreatCell = state.Position, EnemyGroup = new List<string> { "slime" }, Seed = 19 };
            var loaded = SaveCodec.Deserialize(SaveCodec.Serialize(state), db);
            var resumed = new DungeonRun(db, loaded, 1);
            Assert.Equal(GameLocation.Dungeon, loaded.Location, "dungeon resume");
            Assert.Equal(state.Position, loaded.Position, "exact cell");
            Assert.Equal(Facing.South, loaded.Facing, "facing");
            Assert.Equal(Difficulty.Hard, loaded.Difficulty, "difficulty");
            Assert.Equal(2, resumed.Grid.Progress.Keys, "floor keys");
            Assert.True(resumed.Grid.Progress.OpenedChests.Contains(new GridPos(1, 11)), "chest persists");
            Assert.True(!resumed.Grid.IsClosedDoor(new GridPos(2, 3)), "opened locked door remains traversable");
            Assert.True(resumed.Grid.Progress.DefeatedFoes.Contains("saved_foe"), "FOE defeat persists");
            Assert.True(!resumed.CanAct, "pending encounter locks movement");
            Assert.Equal("slime", resumed.PendingBattle.Setup.EnemyGroup[0], "request reconstructs combat setup");
            Assert.Equal(19, resumed.PendingBattle.Setup.Seed, "battle seed persists");
            Assert.Equal(state.Party[0].Hp, resumed.PendingBattle.Setup.Party[0].Hp, "current party vitals");
        }

        [LogicTest]
        public static void SaveRejectsMalformedVersionAndCoordinateAsSaveFormatException()
        {
            foreach (string json in new[] { "", "{", "{\"version\":-1}", "{\"version\":\"oops\"}", "{\"version\":999}", "{\"version\":1,\"position\":\"oops\"}" })
            {
                bool rejected = false;
                try { SaveCodec.Deserialize(json, TestMain.DB); }
                catch (SaveFormatException) { rejected = true; }
                Assert.True(rejected, "malformed save rejected: " + json);
            }
        }

        [LogicTest]
        public static void OneShotBossQuestRemainsClaimableAfterVictoryBeforeAcceptance()
        {
            var db = TestMain.DB;
            var quest = db.Quests["q_sphinx"];
            var defeatedParty = GameState.NewGame(db, Difficulty.Normal);
            defeatedParty.DeepestFloor = quest.UnlockFloor;
            defeatedParty.Bestiary[quest.TargetId] = new BestiaryEntry { Seen = true, Kills = 1 };
            Assert.True(QuestLog.Accept(db, defeatedParty, quest.Id).Success, "quest accepted");
            Assert.True(!QuestLog.Claim(db, defeatedParty, quest.Id).Success, "partial kill without campaign victory cannot complete boss quest");

            var victorious = GameState.NewGame(db, Difficulty.Normal);
            victorious.DeepestFloor = quest.UnlockFloor;
            victorious.Flags.Add(GameFlow.BossFlag(3));
            victorious = SaveCodec.Deserialize(SaveCodec.Serialize(victorious), db);
            Assert.True(QuestLog.Accept(db, victorious, quest.Id).Success, "late acceptance after saved victory");
            Assert.Equal(QuestBoardState.Complete, QuestLog.BoardState(victorious, quest), "one-shot objective remains complete");
            int gold = victorious.Gold;
            Assert.True(QuestLog.Claim(db, victorious, quest.Id).Success, "completed boss reward claim");
            Assert.Equal(gold + quest.RewardGold, victorious.Gold, "exact reward");
            Assert.True(!QuestLog.Claim(db, victorious, quest.Id).Success, "second reward refused");
            Assert.Equal(gold + quest.RewardGold, victorious.Gold, "second claim cannot duplicate gold");
        }

        [LogicTest]
        public static void ExperienceDoesNotReviveKoAndCapDiscardsOverflow()
        {
            var db = TestMain.DB;
            var state = GameState.NewGame(db, Difficulty.Normal);
            var hero = state.Party[0];
            hero.Hp = 0;
            PartyStats.AwardXp(db, hero, PartyStats.XpToNext(1));
            Assert.Equal(2, hero.Level, "level advanced");
            Assert.Equal(0, hero.Hp, "XP does not revive KO");
            var report = PartyStats.AwardXp(db, hero, PartyStats.XpToNext(1) + PartyStats.XpToNext(2));
            Assert.Equal(3, hero.Level, "level advanced twice");
            hero.Level = GameState.LevelCap - 1; hero.Xp = 0;
            PartyStats.AwardXp(db, hero, PartyStats.XpToNext(hero.Level) + 500);
            Assert.Equal(GameState.LevelCap, hero.Level, "level cap");
            Assert.Equal(0, hero.Xp, "XP overflow discarded at cap");
            Assert.True(report.NewSkills.Count == 0 || report.NewSkills.TrueForAll(id => db.Skills.ContainsKey(id)), "learned skills exist");
            var start = db.Heroes[hero.Id];
            Assert.True(start.Skills.Count >= 4, "hunters start with basic attack, a signature and two more skills");
            Assert.True(start.Skills.Exists(id => id.StartsWith("sig_")), "signature skill from Lv 1");
        }

        [LogicTest]
        public static void FieldItemsConsumeOnlyWithEffectAndCannotBypassPendingBattle()
        {
            var db = TestMain.DB;
            var state = GameState.NewGame(db, Difficulty.Normal);
            var hero = state.Party[0];
            int before = state.ItemCount("healing_potion");
            var fail = GameFlow.UseFieldItem(db, state, "healing_potion", hero.Id, false);
            Assert.True(!fail.Success, "full health has no effect");
            Assert.Equal(before, state.ItemCount("healing_potion"), "failed use costs nothing");
            hero.Hp--;
            Assert.True(GameFlow.UseFieldItem(db, state, "healing_potion", hero.Id, false).Success, "injured target healed");
            Assert.Equal(before - 1, state.ItemCount("healing_potion"), "one item consumed");
            state.PendingBattle = new DungeonBattleRequest();
            int stones = state.ItemCount("return_stone");
            Assert.True(!GameFlow.UseFieldItem(db, state, "return_stone", "", true).Success, "camp unavailable in battle");
            Assert.Equal(stones, state.ItemCount("return_stone"), "blocked escape costs nothing");
        }

        [LogicTest]
        public static void TrapNeverKosAndInnRespawnsOnlyFoes()
        {
            var db = TestMain.DB;
            var state = GameState.NewGame(db, Difficulty.Normal);
            state.Party[0].Hp = 1; state.Party[1].Hp = 0;
            var damage = PartyStats.ApplyTrap(db, state, () => 0f, 1f, 1f);
            Assert.Equal(1, state.Party[0].Hp, "trap leaves one HP");
            Assert.Equal(0, state.Party[1].Hp, "KO remains KO");
            Assert.True(!damage.Damage.ContainsKey(state.Party[1].Id), "KO takes no trap damage");
            var floor = state.Floor(db.Floors[0].Id);
            floor.DefeatedFoes.Add("foe"); floor.Keys = 2;
            floor.OpenedChests.Add(new GridPos(1, 1)); floor.ClearedBattles.Add(new GridPos(2, 1));
            floor.OpenedDoors.Add(new GridPos(3, 1)); state.WarpsUnlocked.Add(3);
            TownServices.RestAtInn(db, state, true);
            Assert.Equal(0, floor.DefeatedFoes.Count, "FOEs respawn");
            Assert.Equal(2, floor.Keys, "keys retained");
            Assert.Equal(1, floor.OpenedChests.Count, "chests retained");
            Assert.Equal(1, floor.ClearedBattles.Count, "fixed battle retained");
            Assert.Equal(1, floor.OpenedDoors.Count, "doors retained");
            Assert.True(state.WarpsUnlocked.Contains(3), "warps retained");
            Assert.Equal(PartyStats.EffectiveStats(db, state.Party[1]).MaxHp, state.Party[1].Hp, "inn revives");
        }

        [LogicTest]
        public static void QuestCollectionCanRegressAndClaimIsOneTime()
        {
            var db = GameDB.Load(table => File.ReadAllText(Path.Combine(Environment.GetEnvironmentVariable("ABYSS_DATA_DIR"), table + ".json")));
            var quest = new QuestDef { Id = "test_collect", Kind = QuestLog.KindCollect, TargetId = "healing_potion", Count = 3, RewardGold = 80 };
            db.Quests.Add(quest.Id, quest); db.QuestList.Add(quest);
            var state = GameState.NewGame(db, Difficulty.Normal);
            Assert.True(QuestLog.Accept(db, state, quest.Id).Success, "accept");
            Assert.Equal(QuestState.Complete, state.Quests[quest.Id].State, "owned items complete quest");
            state.RemoveItem("healing_potion", 1); QuestLog.Refresh(db, state);
            Assert.Equal(QuestState.Accepted, state.Quests[quest.Id].State, "spending item regresses collect quest");
            state.AddItem("healing_potion", 1); QuestLog.Refresh(db, state);
            int gold = state.Gold;
            Assert.True(QuestLog.Claim(db, state, quest.Id).Success, "claim");
            Assert.Equal(0, state.ItemCount("healing_potion"), "collect items consumed");
            Assert.Equal(gold + 80, state.Gold, "reward granted");
            Assert.True(!QuestLog.Claim(db, state, quest.Id).Success, "claim once");
            Assert.Equal(gold + 80, state.Gold, "second claim grants nothing");
        }
    }
}
