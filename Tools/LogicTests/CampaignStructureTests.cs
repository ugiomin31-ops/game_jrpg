// 35-floor campaign structure: floor layouts and chapter roles, story flags and the ending, legacy save migration,
// rare-monster escapes and the quest board (job items).
using System;
using System.Collections.Generic;
using System.Linq;
using Abyss.Logic;
using Abyss.Logic.Battle;
using Abyss.Logic.Dungeon;
using Abyss.Logic.Game;

namespace Abyss.LogicTests
{
    public static class CampaignStructureTests
    {
        static readonly GridPos[] Steps = { new GridPos(1, 0), new GridPos(-1, 0), new GridPos(0, 1), new GridPos(0, -1) };

        static HashSet<GridPos> Reach(DungeonGrid grid, GridPos from, bool doorsOpen)
        {
            var seen = new HashSet<GridPos> { from };
            var queue = new Queue<GridPos>(); queue.Enqueue(from);
            while (queue.Count > 0)
            {
                var p = queue.Dequeue();
                char c = grid.Cell(p);
                if ((c == '<' || c == '>') && p != from) continue;   // stairs change floor
                foreach (var d in Steps)
                {
                    var n = p + d; char m = grid.Cell(n);
                    if (m == '#' || (m == 'L' && !doorsOpen) || !seen.Add(n)) continue;
                    queue.Enqueue(n);
                }
            }
            return seen;
        }

        [LogicTest]
        public static void FloorsFollowTheChapterPlan()
        {
            var db = TestMain.DB;
            int lastSize = 0;
            for (int i = 0; i < db.Floors.Count; i++)
            {
                var floor = db.Floors[i];
                int chapter = i / GameFlow.FloorsPerChapter + 1, k = i % GameFlow.FloorsPerChapter;
                Assert.Equal(i, floor.Index, "floor order " + floor.FloorLabel);
                var grid = DungeonGrid.Parse(floor);
                Assert.True(grid.Width == grid.Height && grid.Width % 2 == 1 && grid.Width >= 21 && grid.Width <= 27, floor.FloorLabel + " size");
                Assert.True(grid.Width >= lastSize, floor.FloorLabel + " floors grow chapter by chapter");
                lastSize = grid.Width;
                Assert.Equal(1, grid.FindCells('S').Count(), floor.FloorLabel + " one start");
                Assert.Equal(1, grid.FindCells('<').Count(), floor.FloorLabel + " one way up");
                // With every door open the whole floor is one region, and there are enough keys for the doors.
                var all = Reach(grid, grid.Start, true);
                for (int y = 0; y < grid.Height; y++)
                    for (int x = 0; x < grid.Width; x++)
                        if (grid.Cell(new GridPos(x, y)) != '#') Assert.True(all.Contains(new GridPos(x, y)), $"{floor.FloorLabel} cell {x},{y} reachable");
                Assert.True(grid.FindCells('K').Count() >= grid.FindCells('L').Count(), floor.FloorLabel + " keys for every door");
                // Without any key some key is reachable whenever there are doors (no locked start).
                var free = Reach(grid, grid.Start, false);
                if (grid.FindCells('L').Any()) Assert.True(grid.FindCells('K').Any(free.Contains), floor.FloorLabel + " first key reachable");
                Assert.True(floor.LoreStones.Count >= 1 && floor.LoreStones.All(s => grid.Cell(GridPos.FromArray(s.Cell)) == 'N' && s.Text.Length > 0), floor.FloorLabel + " lore stones");
                Assert.Equal(grid.FindCells('T').Count(), floor.Treasures.Count, floor.FloorLabel + " every chest has contents");
                Assert.Equal(grid.FindCells('E').Count(), floor.Events.Count, floor.FloorLabel + " every event cell has a group");
                foreach (var foe in floor.Foes)
                    foreach (var p in foe.Patrol) Assert.True(grid.FoePassable(GridPos.FromArray(p)), floor.FloorLabel + " FOE route " + foe.Id);
                Assert.True(floor.EncounterRate > 0 && floor.EncounterRate < 0.2 && floor.MaxEncounterSteps > floor.MinEncounterSteps, floor.FloorLabel + " encounter pacing");
                // Chapter roles: floor 3 = mid-boss FOE, floor 5 = chapter boss guarding the stairs.
                if (k == 2) Assert.True(floor.Foes.Any(f => f.Id.StartsWith("midboss_") && db.Enemies[f.Group[0]].Rank == 1), floor.FloorLabel + " mid-boss");
                if (k == 4 && chapter <= GameFlow.MainChapters)
                {
                    Assert.Equal(SpecIds.ChapterBosses[chapter - 1], floor.BossGroup.Single(), floor.FloorLabel + " chapter boss");
                    Assert.True(floor.BossPreText.Length > 0 && floor.BossPostText.Length > 0, floor.FloorLabel + " boss lines");
                }
                if (k != 4 && chapter <= GameFlow.MainChapters) Assert.Equal(0, floor.BossGroup.Count, floor.FloorLabel + " no boss");
                if (i < db.Floors.Count - 1) Assert.Equal(1, grid.FindCells('>').Count(), floor.FloorLabel + " way down");
            }
            Assert.Equal("abyss_lord_ex", db.Floors[db.Floors.Count - 1].BossGroup.Single(), "trial corridor ends with the last echo");
            Assert.Equal(1, db.Floors.Count(f => f.Ending), "one floor ends the story");
            Assert.True(db.Floors[GameFlow.MainChapters * GameFlow.FloorsPerChapter - 1].Ending, "B30F's boss ends the story");
            // The five trial floors each hold a superbosses' echo (event battles before the stairs).
            for (int i = 30; i < 35; i++)
                Assert.True(db.Floors[i].Events.Any(e => e.Group.Any(id => id.EndsWith("_ex"))), db.Floors[i].FloorLabel + " superboss");
        }

        static DungeonBattleResolution WinBoss(GameDB db, GameState state, int floorIndex)
        {
            var run = new DungeonRun(db, state, floorIndex, ArrivalMode.Descending);
            var cell = run.Grid.FindCell('B');
            state.PendingBattle = new DungeonBattleRequest { Kind = BattleKind.Boss, FloorId = run.Grid.Floor.Id, Cell = cell, RetreatCell = cell,
                EnemyGroup = new List<string>(run.Grid.Floor.BossGroup), PostText = run.Grid.Floor.BossPostText };
            var outcome = new BattleOutcome { Result = BattleResult.Victory };
            outcome.DefeatedEnemies.AddRange(run.Grid.Floor.BossGroup);
            return run.ResolveBattle(outcome);
        }

        [LogicTest]
        public static void ChapterBossesSetFlagsAndOnlyTheAbyssLordEndsTheStory()
        {
            var db = TestMain.DB;
            var state = GameState.NewGame(db, Difficulty.Normal);
            GameFlow.CompletePrologue(state);
            for (int chapter = 1; chapter <= GameFlow.MainChapters; chapter++)
            {
                var result = WinBoss(db, state, chapter * GameFlow.FloorsPerChapter - 1);
                Assert.True(state.Flags.Contains(GameFlow.BossFlag(chapter)), "boss flag " + chapter);
                Assert.Equal(chapter == GameFlow.MainChapters, result.Ending, "ending only after chapter " + GameFlow.MainChapters);
                Assert.Equal(chapter == GameFlow.MainChapters, state.Flags.Contains(GameFlow.FlagCleared), "cleared flag after chapter " + chapter);
                Assert.True(result.PostText.Length > 0, "boss post text " + chapter);
                if (chapter < GameFlow.MainChapters) Assert.Equal(chapter + 1, GameFlow.StoryChapter(state), "story chapter advances");
            }
            Assert.Equal(GameFlow.MainChapters + 1, GameFlow.StoryChapter(state), "postgame chapter");
            var final = WinBoss(db, state, db.Floors.Count - 1);
            Assert.True(!final.Ending, "the trial corridor's last echo does not replay the ending");
            Assert.True(state.Flags.Contains(GameFlow.BossFlag(7)), "trial corridor cleared flag");
            state.Flags.Add(GameFlow.FlagEndingSeen);
            var notices = GameFlow.EnterTown(state);
            Assert.True(notices.Any(n => n.TextKey == "postgame_unlocked"), "postgame notice once");
            Assert.True(!GameFlow.EnterTown(state).Any(n => n.TextKey == "postgame_unlocked"), "postgame notice not repeated");
            foreach (string key in GameFlow.ElderLineKeys(db, state)) Assert.True(db.Text.ContainsKey(key), "elder line " + key);
            for (int b = 0; b <= 6; b++) Assert.True(db.Text.ContainsKey("biome_" + b), "chapter intro " + b);
            for (int p = 1; p <= GameFlow.EndingPages; p++) Assert.True(db.Text.ContainsKey("ending_" + p), "ending page " + p);
        }

        static GameState Legacy(GameDB db)
        {
            var state = GameState.NewGame(db, Difficulty.Normal);
            state.Flags.Remove(CampaignMigration.FlagLayout);
            return state;
        }

        [LogicTest]
        public static void LegacyTwelveFloorSavesMoveOntoTheNewLayout()
        {
            var db = TestMain.DB;
            var state = Legacy(db);
            GameFlow.CompletePrologue(state);
            state.FloorIndex = 5; state.DeepestFloor = 7;            // old B6F (frost boss floor), deepest old B8F
            state.WarpsUnlocked.Add(3); state.WarpsUnlocked.Add(6);
            state.Flags.Add(GameFlow.BossFlag(1)); state.Flags.Add(GameFlow.BossFlag(2));
            var old = new FloorProgress { Keys = 1 };
            old.OpenedChests.Add(new GridPos(1, 11)); old.DefeatedFoes.Add("foe_b6_1");
            state.Floors["frost_grotto_b6"] = old;
            state.Floors["verdant_ruins"] = new FloorProgress();
            state.Location = GameLocation.Dungeon; state.Position = new GridPos(7, 7);
            state.Quests["q_frost_survey"] = new QuestProgress { State = QuestState.Accepted };
            state.Party[0].Level = 22;
            var loaded = SaveCodec.Deserialize(SaveCodec.Serialize(state), db);

            Assert.True(loaded.Flags.Contains(CampaignMigration.FlagLayout), "migrated once");
            Assert.True(!loaded.Floors.ContainsKey("frost_grotto_b6") && !loaded.Floors.ContainsKey("verdant_ruins"), "old layouts' progress dropped");
            Assert.Equal(GameLocation.Town, loaded.Location, "resume in town");
            Assert.True(loaded.PendingBattle == null, "no stale battle");
            Assert.Equal(CampaignMigration.MapLegacyIndex(5), loaded.FloorIndex, "current floor mapped");
            Assert.Equal(9, loaded.FloorIndex, "old frost boss floor -> chapter 2 boss floor (B10F)");
            Assert.True(loaded.DeepestFloor >= 10, "beaten chapter 2 boss keeps chapter 3 open");
            Assert.True(loaded.Flags.Contains(GameFlow.BossFlag(1)) && loaded.Flags.Contains(GameFlow.BossFlag(2)), "boss flags kept");
            foreach (int chapterBoss in new[] { 4, 9 })
            {
                var floor = db.Floors[chapterBoss];
                var grid = DungeonGrid.Parse(floor, loaded.Floor(floor.Id));
                Assert.True(grid.Progress.ClearedBattles.Contains(grid.FindCell('B')), floor.FloorLabel + " boss stays beaten");
            }
            Assert.True(loaded.WarpsUnlocked.Count > 0, "warps carried over");
            foreach (int warp in loaded.WarpsUnlocked)
                Assert.True(DungeonGrid.Parse(db.Floors[warp]).FindCells('W').Any(), "warp floor has a crystal " + warp);
            foreach (int floor in TownServices.DepartureFloors(db, loaded)) Assert.True(floor <= loaded.DeepestFloor, "departures within reach");
            Assert.Equal(22, loaded.Party[0].Level, "heroes untouched");
            Assert.True(loaded.Quests["q_frost_survey"].State != QuestState.Claimed, "accepted quest kept (now complete: its floor is behind the party)");
            string once = SaveCodec.Serialize(loaded);
            Assert.Equal(once, SaveCodec.Serialize(SaveCodec.Deserialize(once, db)), "migration is idempotent");
            int deepestWarp = TownServices.DepartureFloors(db, loaded).Max();
            Assert.Equal(10, deepestWarp, "the chapter 3 entrance warp is open (the old party had walked into biome 3's floors)");
            var run = new DungeonRun(db, loaded, deepestWarp, ArrivalMode.Town);
            Assert.True(run.CanAct, "migrated save can depart to its deepest warp");

            // A save that had seen the old ending: the herald is now chapter 4's boss and the story continues below.
            var ended = Legacy(db);
            GameFlow.CompletePrologue(ended);
            ended.FloorIndex = 11; ended.DeepestFloor = 11;
            for (int b = 1; b <= 4; b++) ended.Flags.Add(GameFlow.BossFlag(b));
            ended.Flags.Add(GameFlow.FlagCleared); ended.Flags.Add(GameFlow.FlagEndingSeen);
            var after = SaveCodec.Deserialize(SaveCodec.Serialize(ended), db);
            Assert.True(!after.Flags.Contains(GameFlow.FlagCleared) && !after.Flags.Contains(GameFlow.FlagEndingSeen), "story no longer cleared");
            Assert.True(after.Flags.Contains(CampaignMigration.FlagLegacyEnding), "old ending remembered");
            Assert.Equal(4 * GameFlow.FloorsPerChapter, after.DeepestFloor, "chapter 5 is open");
            Assert.Equal(5, GameFlow.StoryChapter(after), "story resumes at chapter 5");

            // New games are already on the new layout: loading them never changes anything.
            var fresh = GameState.NewGame(db, Difficulty.Normal);
            string text = SaveCodec.Serialize(fresh);
            Assert.Equal(text, SaveCodec.Serialize(SaveCodec.Deserialize(text, db)), "fresh save untouched");
        }

        [LogicTest]
        public static void RareRunnersEscapeWithoutRewards()
        {
            var db = TestMain.DB;
            foreach (string id in new[] { "metal_slime", "gold_slime" })
            {
                Assert.Equal(EnemyAI.RunnerProfile, db.Enemies[id].AiProfile, id + " runs");
                var setup = BattleTestUtil.Setup(20, new[] { id }, 31);
                var engine = new BattleEngine(db, setup);
                engine.Start();
                while (engine.State == BattleEngineState.AwaitingCommand && engine.Round < 60) engine.Submit(BattleCommand.Guard());
                Assert.Equal(BattleEngineState.Ended, engine.State, id + " battle ends");
                Assert.Equal(BattleResult.Fled, engine.Outcome.Result, id + " escaped");
                Assert.Equal(0, engine.Outcome.Experience, id + " no EXP when it escapes");
                Assert.Equal(0, engine.Outcome.DefeatedEnemies.Count, id + " not counted as defeated");
            }
            var metal = db.Enemies["metal_slime"];
            Assert.True(metal.MaxHp <= 10 && metal.Defense >= 500 && metal.ExperienceReward > db.Enemies["ice_golem"].ExperienceReward * 10, "metal slime: tiny HP, huge defence, big EXP");
            Assert.True(db.Enemies["gold_slime"].GoldReward >= 1000, "gold slime pays out");
        }

        [LogicTest]
        public static void QuestBoardCoversTheCampaignAndJobItems()
        {
            var db = TestMain.DB;
            Assert.True(db.QuestList.Count >= 45, "about fifty quests");
            var inDungeon = new HashSet<string>();
            var foes = new HashSet<string>();
            foreach (var f in db.Floors)
            {
                foreach (var g in f.EncounterGroups.Concat(f.Events.Select(e => e.Group)).Append(f.BossGroup)) inDungeon.UnionWith(g);
                foreach (var foe in f.Foes) { inDungeon.UnionWith(foe.Group); foes.Add(foe.Group[0]); }
            }
            foreach (var q in db.QuestList)
            {
                Assert.True(q.UnlockFloor >= 0 && q.UnlockFloor < db.Floors.Count, "unlock floor " + q.Id);
                Assert.True(q.Title.Length > 0 && q.Description.Length > 0, "quest text " + q.Id);
                switch (q.Kind)
                {
                    case QuestLog.KindKill: Assert.True(inDungeon.Contains(q.TargetId), "kill target appears " + q.Id); break;
                    case QuestLog.KindFoe: Assert.True(foes.Contains(q.TargetId) && db.Enemies[q.TargetId].Rank == 1, "FOE target patrols " + q.Id); break;
                    case QuestLog.KindBoss: Assert.True(db.Floors.Any(f => f.BossGroup.Contains(q.TargetId)), "boss target " + q.Id); break;
                    case QuestLog.KindExplore: Assert.True(db.Floors.Any(f => f.Id == q.TargetId), "explore target " + q.Id); break;
                    case QuestLog.KindCollect: Assert.True(db.Items.ContainsKey(q.TargetId) || SpecIds.Items.Contains(q.TargetId), "collect target " + q.Id); break;
                    default: throw new Exception("unknown quest kind " + q.Kind);
                }
                foreach (var id in q.RewardItems.Keys)
                    Assert.True(db.Items.ContainsKey(id) || db.Equipment.ContainsKey(id) || SpecIds.Items.Contains(id) || SpecIds.Equipment.Contains(id), "reward " + id);
            }
            // Four of each class-change item, all reachable by the chapter that needs them.
            int BossFloor(string enemy) => db.Floors.First(f => f.BossGroup.Contains(enemy)).Index;
            (int count, int latest) Sources(string item)
            {
                int count = 0, latest = 0;
                foreach (var q in db.QuestList.Where(q => q.RewardItems.ContainsKey(item))) { count += q.RewardItems[item]; latest = Math.Max(latest, q.UnlockFloor); }
                foreach (var e in db.Enemies.Values.Where(e => e.IsBoss && e.Drops.Any(d => d.Id == item && d.Chance >= 1f)))
                {
                    Assert.True(db.Floors.Any(f => f.BossGroup.Contains(e.Id)), item + " boss is in the dungeon");
                    count++; latest = Math.Max(latest, BossFloor(e.Id));
                }
                return (count, latest);
            }
            var medals = Sources("job_medal");
            Assert.Equal(4, medals.count, "four job medals");
            Assert.True(db.Enemies["forest_guardian"].Drops.Any(d => d.Id == "job_medal" && d.Chance >= 1f), "the chapter 1 boss leaves a job medal");
            Assert.True(medals.latest < 2 * GameFlow.FloorsPerChapter, "job medals within chapter 2");
            var seals = Sources("master_seal");
            Assert.Equal(4, seals.count, "four master seals");
            Assert.True(db.Enemies["boss"].Drops.Any(d => d.Id == "master_seal" && d.Chance >= 1f), "the chapter 4 herald leaves a master seal");
            Assert.True(seals.latest < 5 * GameFlow.FloorsPerChapter, "master seals within chapter 5");
            Assert.True(db.QuestList.Where(q => q.RewardItems.ContainsKey("master_seal")).All(q => q.UnlockFloor >= 4 * GameFlow.FloorsPerChapter), "master seal trials open after the herald");
        }
    }
}
