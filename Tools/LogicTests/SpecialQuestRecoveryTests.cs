using System.Linq;
using Abyss.Logic;
using Abyss.Logic.Battle;
using Abyss.Logic.Dungeon;
using Abyss.Logic.Game;
using Newtonsoft.Json.Linq;

namespace Abyss.LogicTests
{
    public static class SpecialQuestRecoveryTests
    {
        static readonly string[] QuestIds = { "q_ex_forest", "q_ex_herald" };

        static GameState NewState(QuestDef quest)
        {
            var state = GameState.NewGame(TestMain.DB, Difficulty.Normal);
            GameFlow.CompletePrologue(state);
            state.DeepestFloor = quest.UnlockFloor;
            return state;
        }

        static FloorDef Floor(QuestDef quest) => TestMain.DB.Floors.Single(f => f.Events.Any(e => e.Group.Contains(quest.TargetId)));
        static EventDef Event(QuestDef quest) => Floor(quest).Events.Single(e => e.Group.Contains(quest.TargetId));

        // Enter the real authored event and settle a supplied outcome through the production map/quest path.
        // This is an engine-free settlement test, not a combat simulation or Unity runtime test.
        static DungeonRun Settle(GameState state, QuestDef quest, BattleResult result)
        {
            var db = TestMain.DB;
            var floor = Floor(quest);
            var ev = Event(quest);
            Assert.True(ev.IsAmbush && ev.Group.Count == 1, "unique one-shot event target");
            var cell = GridPos.FromArray(ev.Cell);
            var run = DungeonContentTests.BesideCell(db, state, db.Floors.IndexOf(floor), cell, out _);
            var step = run.Move(RelativeMove.Forward);
            Assert.True(step.Battle != null && step.Battle.Kind == BattleKind.Event, "real event starts");
            Assert.Equal(quest.TargetId, step.Battle.EnemyGroup.Single(), "actual event target");
            var outcome = new BattleOutcome { Result = result };
            // Even partial kills recorded during a loss must not become successful quest evidence.
            outcome.DefeatedEnemies.Add(quest.TargetId);
            run.ResolveBattle(outcome);
            Assert.Equal(result == BattleResult.Victory, state.Floor(floor.Id).ClearedBattles.Contains(cell), "only victory clears event");
            return run;
        }

        static void ClaimOnce(GameState state, QuestDef quest)
        {
            int gold = state.Gold;
            var items = quest.RewardItems.ToDictionary(kv => kv.Key, kv => state.ItemCount(kv.Key));
            Assert.True(QuestLog.Claim(TestMain.DB, state, quest.Id).Success, "first claim succeeds");
            Assert.Equal(gold + quest.RewardGold, state.Gold, "exact gold reward");
            foreach (var kv in quest.RewardItems)
                Assert.Equal(items[kv.Key] + kv.Value, state.ItemCount(kv.Key), "exact item reward");
            QuestLog.Refresh(TestMain.DB, state);
            Assert.True(!QuestLog.Claim(TestMain.DB, state, quest.Id).Success, "second claim rejected");
            Assert.Equal(gold + quest.RewardGold, state.Gold, "no duplicate gold");
            foreach (var kv in quest.RewardItems)
                Assert.Equal(items[kv.Key] + kv.Value, state.ItemCount(kv.Key), "no duplicate items");
        }

        static void LateAcceptance(string id)
        {
            var quest = TestMain.DB.Quests[id];
            var state = NewState(quest);
            var run = Settle(state, quest, BattleResult.Victory);
            Assert.True(run.Interact().Battle == null && state.PendingBattle == null, "cleared event cannot replay");
            Assert.True(QuestLog.Accept(TestMain.DB, state, id).Success, "late acceptance succeeds");
            Assert.Equal(QuestBoardState.Complete, QuestLog.BoardState(state, quest), "late acceptance recovers victory");
            Assert.Equal(1, QuestLog.Progress(state, quest), "one recovered victory");
            ClaimOnce(state, quest);
        }

        [LogicTest] public static void ForestDefeatBeforeAccept() => LateAcceptance("q_ex_forest");
        [LogicTest] public static void HeraldDefeatBeforeAccept() => LateAcceptance("q_ex_herald");

        [LogicTest]
        public static void AcceptBeforeVictoryStillCompletesBothQuests()
        {
            foreach (string id in QuestIds)
            {
                var quest = TestMain.DB.Quests[id]; var state = NewState(quest);
                Assert.True(QuestLog.Accept(TestMain.DB, state, id).Success, "early acceptance");
                Assert.Equal(QuestBoardState.Accepted, QuestLog.BoardState(state, quest), "initially incomplete");
                Settle(state, quest, BattleResult.Victory);
                Assert.Equal(QuestBoardState.Complete, QuestLog.BoardState(state, quest), "victory completes accepted quest");
                ClaimOnce(state, quest);
            }
        }

        [LogicTest]
        public static void UncompletedAndLostEventsNeverAward()
        {
            foreach (string id in QuestIds)
            foreach (var result in new[] { BattleResult.None, BattleResult.Defeat, BattleResult.Fled })
            foreach (bool acceptFirst in new[] { false, true })
            {
                var quest = TestMain.DB.Quests[id]; var state = NewState(quest);
                if (acceptFirst) Assert.True(QuestLog.Accept(TestMain.DB, state, id).Success, "early acceptance");
                if (result != BattleResult.None) Settle(state, quest, result);
                if (!acceptFirst) Assert.True(QuestLog.Accept(TestMain.DB, state, id).Success, "late acceptance");
                int gold = state.Gold;
                QuestLog.Refresh(TestMain.DB, state);
                Assert.Equal(QuestBoardState.Accepted, QuestLog.BoardState(state, quest), "no successful event");
                Assert.Equal(0, QuestLog.Progress(state, quest), "no recovered progress");
                Assert.True(!QuestLog.Claim(TestMain.DB, state, id).Success, "reward unavailable");
                Assert.Equal(gold, state.Gold, "claim gives no gold");
                foreach (var kv in quest.RewardItems) Assert.Equal(0, state.ItemCount(kv.Key), "no reward items");
            }
        }

        [LogicTest]
        public static void WrongFloorCellAndSpentOnlyAreNotVictoryEvidence()
        {
            foreach (string id in QuestIds)
            {
                var quest = TestMain.DB.Quests[id]; var state = NewState(quest);
                var cell = GridPos.FromArray(Event(quest).Cell);
                state.Floor("red_gate_3").ClearedBattles.Add(cell);
                state.Floor(Floor(quest).Id).ClearedBattles.Add(GridPos.None);
                state.Floor(Floor(quest).Id).SpentEvents.Add(cell);
                state.BestiaryOf(quest.TargetId).Kills = 1;
                Assert.True(QuestLog.Accept(TestMain.DB, state, id).Success, "accept with unrelated evidence");
                Assert.Equal(0, QuestLog.Progress(state, quest), "requires correct cleared event");
                Assert.True(!QuestLog.Claim(TestMain.DB, state, id).Success, "unrelated evidence cannot pay");
            }
        }

        [LogicTest]
        public static void OrdinaryKillQuestsRemainProspective()
        {
            var db = TestMain.DB;
            var quest = db.Quests.Values.First(q => q.Kind == QuestLog.KindKill && !QuestIds.Contains(q.Id));
            var state = NewState(quest);
            state.BestiaryOf(quest.TargetId).Kills = quest.Count;
            foreach (var floor in db.Floors)
                foreach (var ev in floor.Events) state.Floor(floor.Id).ClearedBattles.Add(GridPos.FromArray(ev.Cell));
            Assert.True(QuestLog.Accept(db, state, quest.Id).Success, "ordinary quest accepted");
            Assert.Equal(0, QuestLog.Progress(state, quest), "ordinary kill history is not retroactive");
            Assert.True(!QuestLog.Claim(db, state, quest.Id).Success, "ordinary quest still needs new kills");
        }

        [LogicTest]
        public static void SavedVictoryRecoversBeforeAcceptanceAndClaimPersists()
        {
            var db = TestMain.DB;
            foreach (string id in QuestIds)
            {
                var quest = db.Quests[id]; var state = NewState(quest);
                Settle(state, quest, BattleResult.Victory);
                state = SaveCodec.Deserialize(SaveCodec.Serialize(state), db);
                Assert.True(QuestLog.Accept(db, state, id).Success, "accept saved victory");
                ClaimOnce(state, quest);
                int gold = state.Gold;
                state = SaveCodec.Deserialize(SaveCodec.Serialize(state), db);
                Assert.Equal(QuestBoardState.Claimed, QuestLog.BoardState(state, quest), "claimed state reloads");
                Assert.True(!QuestLog.Claim(db, state, id).Success, "reload cannot reclaim");
                Assert.Equal(gold, state.Gold, "reload claim gives no gold");
            }
        }

        [LogicTest]
        public static void PreviouslyStuckAcceptedSaveRecoversOnLoad()
        {
            foreach (string id in QuestIds)
            {
                var quest = TestMain.DB.Quests[id]; var state = NewState(quest);
                Settle(state, quest, BattleResult.Victory);
                state.Quests[id] = new QuestProgress { State = QuestState.Accepted, Progress = 0 };
                state = SaveCodec.Deserialize(SaveCodec.Serialize(state), TestMain.DB);
                Assert.Equal(QuestBoardState.Complete, QuestLog.BoardState(state, quest), "existing stuck save repaired");
                ClaimOnce(state, quest);
            }
        }

        [LogicTest]
        public static void LegacySaveWithoutClearedBattlesStaysIncomplete()
        {
            foreach (string id in QuestIds)
            {
                var quest = TestMain.DB.Quests[id]; var state = NewState(quest);
                state.Floor(Floor(quest).Id);
                Assert.True(QuestLog.Accept(TestMain.DB, state, id).Success, "accept uncompleted quest");
                var json = JObject.Parse(SaveCodec.Serialize(state));
                foreach (var floor in ((JObject)json["floors"]).Properties()) ((JObject)floor.Value).Remove("cleared_battles");
                state = SaveCodec.Deserialize(json.ToString(), TestMain.DB);
                Assert.Equal(QuestBoardState.Accepted, QuestLog.BoardState(state, quest), "legacy save loads without fabricated victory");
                Assert.True(!QuestLog.Claim(TestMain.DB, state, id).Success, "legacy missing evidence cannot pay");
            }
        }
    }
}
