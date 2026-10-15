// Floor-specific encounter pools, one-shot rescue / elite-choice events (data, flow, saves, settlement) and the
// active hunter's reaction appended to lore stones.
using System;
using System.Collections.Generic;
using System.IO;
using System.Linq;
using Abyss.Logic;
using Abyss.Logic.Battle;
using Abyss.Logic.Dungeon;
using Abyss.Logic.Game;
using Newtonsoft.Json.Linq;

namespace Abyss.LogicTests
{
    public static class DungeonContentTests
    {
        const int Zones = 13;
        static readonly Dictionary<string, int[]> RareByZone = new Dictionary<string, int[]>   // Tools/content/spec.py RARE_BY_ZONE
        {
            ["gold_slime"] = new[] { 2, 3 }, ["metal_slime"] = new[] { 4, 5, 6 }, ["golden_mimic"] = new[] { 9, 10, 11 },
        };
        static readonly GridPos[] Steps = { new GridPos(1, 0), new GridPos(-1, 0), new GridPos(0, 1), new GridPos(0, -1) };

        // ------------------------------------------------------------------ fixtures
        /// <summary>Fresh database (tests may mutate floors) with random battles off.</summary>
        static GameDB Db()
        {
            var db = GameDB.Load(t => File.ReadAllText(Path.Combine(Environment.GetEnvironmentVariable("ABYSS_DATA_DIR"), t + ".json")));
            foreach (var f in db.Floors) { f.EncounterRate = 0f; f.MaxEncounterSteps = 0; f.Foes.Clear(); }
            return db;
        }
        static GameState NewState(GameDB db)
        {
            var state = GameState.NewGame(db, Difficulty.Normal);
            GameFlow.CompletePrologue(state);
            return state;
        }
        static int FloorOf(int zone, int k) => (zone - 1) * GameFlow.FloorsPerChapter + k;
        static EventDef Rescue(GameDB db, int zone) => db.Floors[FloorOf(zone, 1)].Events.Single(e => e.IsRescue);
        static EventDef Choice(GameDB db, int zone) => db.Floors[FloorOf(zone, 2)].Events.Single(e => e.IsChoice);
        /// <summary>T6 fixture: resumes the run standing next to <paramref name="cell"/>, facing it.</summary>
        public static DungeonRun BesideCell(GameDB db, GameState state, int floorIndex, GridPos cell, out GridPos beside)
        {
            var grid = DungeonGrid.Parse(db.Floors[floorIndex]);
            beside = GridPos.None; Facing facing = Facing.North;
            for (int pass = 0; pass < 2 && beside == GridPos.None; pass++)
                for (int d = 0; d < 4; d++)
                {
                    var n = cell.Step((Facing)d);
                    char c = grid.Cell(n);
                    if (pass == 0 ? c != '.' : !grid.IsWalkable(n) || c == 'E' || c == 'B') continue;
                    beside = n; facing = GridPos.Rotate((Facing)d, 2); break;
                }
            Assert.True(beside != GridPos.None, "open neighbour of " + cell);
            state.FloorIndex = floorIndex; state.Location = GameLocation.Dungeon; state.Position = beside; state.Facing = facing;
            var run = new DungeonRun(db, state, floorIndex, ArrivalMode.Resume);
            Assert.True(run.CanAct, "fixture can act");
            return run;
        }
        /// <summary>Interact without a closed door in front (a door would be opened instead of investigating the cell).</summary>
        static DungeonStepResult Interact(DungeonRun run)
        {
            for (int d = 0; d < 4 && run.Grid.IsDoor(run.State.Position.Step(run.State.Facing)); d++) run.State.Facing = GridPos.Rotate(run.State.Facing, 1);
            return run.Interact();
        }
        static DungeonStepResult StepOn(DungeonRun run, GridPos cell)
        {
            var result = run.Move(RelativeMove.Forward);
            Assert.Equal(cell, run.State.Position, "stepped onto " + cell);
            return result;
        }
        static void StepOffAndBack(DungeonRun run)
        {
            run.Move(RelativeMove.Back);
            run.Move(RelativeMove.Forward);
        }
        static BattleOutcome Outcome(BattleResult result, IEnumerable<string> defeated = null)
        {
            var outcome = new BattleOutcome { Result = result };
            if (defeated != null && result == BattleResult.Victory) outcome.DefeatedEnemies.AddRange(defeated);
            return outcome;
        }
        static int Potions(GameState s) => s.ItemCount("healing_potion");

        // ------------------------------------------------------------------ pools
        static double AvgLevel(GameDB db, List<string> g) => g.Average(id => db.Enemies[id].Level);
        static string Key(List<string> g) => string.Join(",", g);

        [LogicTest]
        public static void PoolsGrowFloorByFloorWithDuplicatesKept()
        {
            var db = TestMain.DB;
            Assert.Equal(Zones * GameFlow.FloorsPerChapter, db.Floors.Count, "13 zones of three floors");
            for (int k = 0; k < 3; k++)
                Assert.Equal(7, db.Floors[k].EncounterGroups.Count, "zone 1 keeps its authored seven-row pools " + k);
            Assert.Equal("sewer_slime,sewer_slime", Key(db.Floors[0].EncounterGroups[0]), "zone 1 starter pool untouched");
            foreach (var floor in db.Floors)
                foreach (var g in floor.EncounterGroups)
                {
                    Assert.True(g.Count > 0, floor.FloorLabel + " no empty random group");
                    foreach (var id in g) Assert.True(db.Enemies[id].Rank == 0 && !db.Enemies[id].IsBoss, floor.FloorLabel + " ordinary random enemy " + id);
                }
            for (int zone = 2; zone <= Zones; zone++)
            {
                var f1 = db.Floors[FloorOf(zone, 0)].EncounterGroups;
                var f2 = db.Floors[FloorOf(zone, 1)].EncounterGroups;
                var f3 = db.Floors[FloorOf(zone, 2)].EncounterGroups;
                int n = f2.Count;
                for (int i = 1; i < n; i++) Assert.True(AvgLevel(db, f2[i - 1]) <= AvgLevel(db, f2[i]), $"zone {zone} floor 2 sorted by average level");
                Assert.Equal((2 * n + 2) / 3, f1.Count, $"zone {zone} floor 1 keeps ceil(2N/3)");
                for (int i = 0; i < f1.Count; i++) Assert.Equal(Key(f2[i]), Key(f1[i]), $"zone {zone} floor 1 = weakest prefix");
                Assert.Equal(n + 1, f3.Count, $"zone {zone} floor 3 = all + one");
                for (int i = 0; i < n; i++) Assert.Equal(Key(f2[i]), Key(f3[i]), $"zone {zone} floor 3 keeps floor 2 order");
                // The extra copy is the strongest ordinary (non-rare, all rank 0) group by max level, summed HP, then first index.
                var ordinary = Enumerable.Range(0, n).Where(i => !f2[i].Any(RareByZone.ContainsKey)).ToList();
                int best = ordinary.OrderByDescending(i => f2[i].Max(id => db.Enemies[id].Level))
                    .ThenByDescending(i => f2[i].Sum(id => db.Enemies[id].MaxHp)).ThenBy(i => i).First();
                var extra = f3[n];
                Assert.True(!extra.Any(RareByZone.ContainsKey), $"zone {zone} extra is not rare");
                Assert.Equal(f2[best].Max(id => db.Enemies[id].Level), extra.Max(id => db.Enemies[id].Level), $"zone {zone} extra max level");
                Assert.Equal(f2[best].Sum(id => db.Enemies[id].MaxHp), extra.Sum(id => db.Enemies[id].MaxHp), $"zone {zone} extra summed HP");
                Assert.True(f2.Any(g => Key(g) == Key(extra)), $"zone {zone} extra comes from the floor 2 pool");
                // Weight duplication: the extra row raises that group's weight by exactly one copy; floor 2 duplicates survive.
                Assert.Equal(f2.Count(g => Key(g) == Key(extra)) + 1, f3.Count(g => Key(g) == Key(extra)), $"zone {zone} extra weight");
                foreach (var rare in RareByZone)
                {
                    bool here = rare.Value.Contains(zone);
                    Assert.Equal(here, f2.Any(g => g.Contains(rare.Key)), $"zone {zone} floor 2 rare {rare.Key}");
                    Assert.Equal(here, f3.Any(g => g.Contains(rare.Key)), $"zone {zone} floor 3 rare {rare.Key}");
                    if (!here) Assert.True(!f1.Any(g => g.Contains(rare.Key)), $"zone {zone} floor 1 has no foreign rare {rare.Key}");
                }
            }
            // Floor 2 of zone 2 carries authored duplicate rows (weighting); they must not be deduplicated.
            var z2 = db.Floors[FloorOf(2, 1)].EncounterGroups;
            Assert.True(z2.Select(Key).Distinct().Count() < z2.Count, "zone 2 duplicate weights preserved");
        }

        // ------------------------------------------------------------------ data
        static HashSet<GridPos> Reach(DungeonGrid grid, GridPos from, GridPos blocked)
        {
            var seen = new HashSet<GridPos> { from };
            var queue = new Queue<GridPos>(); queue.Enqueue(from);
            while (queue.Count > 0)
            {
                var p = queue.Dequeue();
                char c = grid.Cell(p);
                if ((c == '<' || c == '>') && p != from) continue;
                foreach (var d in Steps)
                {
                    var n = p + d;
                    if (n == blocked || grid.Cell(n) == '#' || !seen.Add(n)) continue;
                    queue.Enqueue(n);
                }
            }
            return seen;
        }

        [LogicTest]
        public static void EveryZoneHasOneRescueAndOneEliteChoiceOffTheCriticalPath()
        {
            var db = TestMain.DB;
            int rescues = 0, choices = 0;
            for (int i = 0; i < db.Floors.Count; i++)
            {
                var floor = db.Floors[i];
                int zone = i / GameFlow.FloorsPerChapter + 1, k = i % GameFlow.FloorsPerChapter;
                Assert.Equal(k == 1 ? 1 : 0, floor.Events.Count(e => e.IsRescue), floor.FloorLabel + " rescue on floor 2 only");
                Assert.Equal(k == 2 ? 1 : 0, floor.Events.Count(e => e.IsChoice), floor.FloorLabel + " choice on floor 3 only");
                var grid = DungeonGrid.Parse(floor);
                foreach (var ev in floor.Events.Where(e => !e.IsAmbush))
                {
                    var cell = GridPos.FromArray(ev.Cell);
                    string at = floor.FloorLabel + " " + ev.Type + " " + cell;
                    Assert.Equal('E', grid.Cell(cell), at + " is an E cell");
                    Assert.True(ev.Title.Length > 0 && ev.Text.Length > 0 && ev.Reward != null, at + " text and reward");
                    foreach (var id in ev.Reward.Items.Keys.Concat(ev.Reward.Equipment.Keys)) Assert.True(db.Items.ContainsKey(id) || db.Equipment.ContainsKey(id), at + " reward id " + id);
                    if (ev.IsRescue)
                    {
                        rescues++;
                        Assert.Equal(0, ev.Group.Count, at + " rescue never fights");
                        Assert.Equal(100 * zone, ev.Reward.Gold, at + " rescue gold");
                        Assert.Equal("healing_potion=1", string.Join(";", ev.Reward.Items.Select(kv => kv.Key + "=" + kv.Value)), at + " rescue potion");
                        Assert.Equal(0, grid.EventGroup(cell).Count, at + " no showcase fallback");
                    }
                    else
                    {
                        choices++;
                        var mid = db.Floors[FloorOf(zone, 1)].Foes.Single(f => f.Id.StartsWith("midboss_"));
                        Assert.Equal(Key(mid.Group), Key(ev.Group), at + " floor 2 mid-boss group");
                        Assert.True(ev.Group.All(db.Enemies.ContainsKey) && db.Enemies[ev.Group[0]].Rank == 1, at + " elite group");
                        Assert.Equal(200 * zone, ev.Reward.Gold, at + " choice gold");
                        Assert.Equal("healing_potion=2", string.Join(";", ev.Reward.Items.Select(kv => kv.Key + "=" + kv.Value)), at + " choice potions");
                        Assert.True(ev.AcceptLabel.Length > 0 && ev.LeaveLabel.Length > 0 && ev.AcceptLabel != ev.LeaveLabel, at + " labels");
                        Assert.Equal(0, grid.EventGroup(cell).Count, at + " never an automatic battle");
                    }
                    // Optional side cell: reachable, not beside stairs/start/warp/boss/other events, and the party can reach
                    // every stair, boss, key, door and warp without stepping on it.
                    Assert.True(Reach(grid, grid.Start, GridPos.None).Contains(cell), at + " reachable");
                    foreach (var d in Steps) Assert.True("S<>WBE".IndexOf(grid.Cell(cell + d)) < 0, at + " not beside a fixed feature");
                    var avoid = Reach(grid, grid.Start, cell);
                    foreach (char m in "<>BKLW")
                        foreach (var target in grid.FindCells(m)) Assert.True(avoid.Contains(target), at + " not on the route to " + m + target);
                    // FOE routes: never a spawn/waypoint, and every patrol leg keeps its length.
                    var open = new FloorDef { Id = floor.Id, Rows = floor.Rows.Select((r, y) => y == cell.Y ? r.Substring(0, cell.X) + "." + r.Substring(cell.X + 1) : r).ToList() };
                    var before = DungeonGrid.Parse(open);
                    foreach (var foe in floor.Foes)
                    {
                        var points = foe.Patrol.Select(GridPos.FromArray).ToList();
                        var spawn = GridPos.FromArray(foe.Spawn);
                        Assert.True(spawn != cell && !points.Contains(cell), at + " not on FOE " + foe.Id);
                        for (int p = 0; p < points.Count; p++)
                        {
                            var a = points[p]; var b = points[(p + 1) % points.Count];
                            Assert.Equal(before.PathLength(a, b), grid.PathLength(a, b), at + " FOE " + foe.Id + " leg " + p);
                        }
                    }
                }
                // Old ambush rows (and every red-gate superboss) still fight on entry.
                foreach (var ev in floor.Events.Where(e => e.IsAmbush))
                    Assert.True(ev.Group.Count > 0 && grid.EventGroup(GridPos.FromArray(ev.Cell)) == ev.Group, floor.FloorLabel + " ambush group");
            }
            Assert.Equal(Zones, rescues, "13 rescues");
            Assert.Equal(Zones, choices, "13 choices");
        }

        // ------------------------------------------------------------------ rescue
        [LogicTest]
        public static void RescuePaysOnceOnEntryAndNeverAgain()
        {
            var db = Db(); var state = NewState(db);
            int zone = 4; var ev = Rescue(db, zone); var cell = GridPos.FromArray(ev.Cell);
            var run = BesideCell(db, state, FloorOf(zone, 1), cell, out _);
            int gold = state.Gold, potions = Potions(state);
            var first = StepOn(run, cell);
            Assert.Equal(DungeonEffect.Rescue, first.Effect, "rescue effect");
            Assert.True(first.Battle == null && first.Choice == null && state.PendingBattle == null, "rescue never fights");
            Assert.True(ReferenceEquals(ev, first.Event) && first.Treasure.Gold == 400, "rescue text/loot result");
            Assert.Equal(gold + 400, state.Gold, "rescue gold once");
            Assert.Equal(potions + 1, Potions(state), "rescue potion once");
            Assert.True(state.Floor(run.Grid.Floor.Id).SpentEvents.Contains(cell) && run.CanAct, "spent committed; play continues");
            run.Grid.Explore(cell);
            Assert.Equal('.', run.Grid.MapMarker(cell), "map shows the rescue as done");
            StepOffAndBack(run);
            Assert.Equal(cell, state.Position, "back on the cell");
            var interact = Interact(run);
            Assert.True(interact.Effect == DungeonEffect.Wait && interact.Battle == null, "spent rescue: nothing on Interact");
            Assert.Equal(gold + 400, state.Gold, "no second payment");
            Assert.Equal(potions + 1, Potions(state), "no second potion");

            // Resuming on an unspent rescue cell: Interact grants it (once).
            var other = NewState(db);
            other.FloorIndex = FloorOf(zone, 1); other.Location = GameLocation.Dungeon; other.Position = cell;
            var resumed = new DungeonRun(db, other, other.FloorIndex, ArrivalMode.Resume);
            int otherGold = other.Gold;
            Assert.Equal(DungeonEffect.Rescue, Interact(resumed).Effect, "Interact rescues");
            Assert.Equal(DungeonEffect.Wait, Interact(resumed).Effect, "then nothing");
            Assert.Equal(otherGold + 400, other.Gold, "paid once via Interact");
        }

        // ------------------------------------------------------------------ choice
        [LogicTest]
        public static void ChoiceLeaveSpendsForGoodWithoutReward()
        {
            var db = Db(); var state = NewState(db);
            int zone = 1; var ev = Choice(db, zone); var cell = GridPos.FromArray(ev.Cell);
            var run = BesideCell(db, state, FloorOf(zone, 2), cell, out _);
            int gold = state.Gold, potions = Potions(state);
            var offer = StepOn(run, cell);
            Assert.Equal(DungeonEffect.Choice, offer.Effect, "choice offered");
            Assert.True(offer.Choice != null && ReferenceEquals(run.PendingChoice, offer.Choice) && offer.Battle == null, "pending decision, no battle");
            Assert.True(!run.CanAct, "pending choice blocks dungeon actions");
            Assert.True(!run.Move(RelativeMove.Back).Moved && state.Position == cell, "cannot walk away while deciding");
            Assert.True(run.ResolveChoice(offer.Choice, 7).Rejected && run.PendingChoice != null, "bad option rejected, offer kept");
            var left = run.ResolveChoice(offer.Choice, DungeonChoice.Leave);
            Assert.True(left.Left && left.Battle == null && state.PendingBattle == null, "left");
            Assert.True(run.ResolveChoice(offer.Choice, DungeonChoice.Accept).Rejected, "duplicate callback rejected");
            Assert.True(state.PendingBattle == null && run.CanAct, "no battle after a late accept");
            Assert.Equal(gold, state.Gold, "leave pays nothing"); Assert.Equal(potions, Potions(state), "no potions");
            Assert.True(state.Floor(run.Grid.Floor.Id).SpentEvents.Contains(cell), "leave is permanent");
            Assert.Equal(DungeonEffect.Wait, Interact(run).Effect, "no new offer");
            run.Grid.Explore(cell);
            Assert.Equal('.', run.Grid.MapMarker(cell), "map clears the nest");
        }

        [LogicTest]
        public static void ChoiceAcceptVictoryPaysExtraOnceAndSpends()
        {
            var db = Db(); var state = NewState(db);
            int zone = 3; var ev = Choice(db, zone); var cell = GridPos.FromArray(ev.Cell);
            var run = BesideCell(db, state, FloorOf(zone, 2), cell, out var beside);
            var offer = StepOn(run, cell);
            var accepted = run.ResolveChoice(offer.Choice, DungeonChoice.Accept);
            Assert.True(accepted.Accepted && accepted.Battle != null && ReferenceEquals(state.PendingBattle, accepted.Battle), "accept saves the battle");
            var request = state.PendingBattle;
            Assert.Equal(BattleKind.Event, request.Kind, "event battle");
            Assert.Equal(Key(ev.Group), Key(request.EnemyGroup), "event midboss group");
            Assert.Equal(1f, request.FoePower, "power 1");
            Assert.True(request.Cell == cell && request.RetreatCell == beside, "cells");
            Assert.True(request.ExtraReward != null && request.ExtraReward.Gold == 600 && request.ExtraReward.Items["healing_potion"] == 2, "extra reward copied");
            Assert.True(!ReferenceEquals(request.ExtraReward, ev.Reward), "copy, not the data row");
            Assert.True(request.Setup != null && !run.CanAct && run.PendingChoice == null, "battle pending");
            Assert.True(run.ResolveChoice(offer.Choice, DungeonChoice.Accept).Rejected, "second accept rejected");
            int gold = state.Gold, potions = Potions(state);
            var won = run.ResolveBattle(Outcome(BattleResult.Victory, ev.Group));
            Assert.True(won.ExtraReward != null && won.ExtraReward.Gold == 600, "resolution reports the extra");
            Assert.Equal(gold + won.Report.Gold + 600, state.Gold, "extra gold committed in the resolution");
            Assert.Equal(potions + 2 + (won.Report.Drops.TryGetValue("healing_potion", out int d) ? d : 0), Potions(state), "extra potions");
            var progress = state.Floor(run.Grid.Floor.Id);
            Assert.True(progress.SpentEvents.Contains(cell) && progress.ClearedBattles.Contains(cell), "spent and cleared");
            Assert.True(state.PendingBattle == null && run.CanAct, "pending battle cleared");
            int after = state.Gold;
            Assert.True(ReferenceEquals(won, run.ResolveBattle(Outcome(BattleResult.Victory, ev.Group))), "repeated settlement returns the same resolution");
            Assert.Equal(after, state.Gold, "repeated settlement pays nothing");
            Assert.True(Interact(run).Effect == DungeonEffect.Wait && state.PendingBattle == null, "won nest: no offer, no battle");
            // A reloaded copy of the settled state cannot be settled again either.
            var loaded = SaveCodec.Deserialize(SaveCodec.Serialize(state), db);
            Assert.True(loaded.PendingBattle == null && loaded.Gold == after, "reload keeps one payment");
        }

        [LogicTest]
        public static void ChoiceFleeAndDefeatLeaveTheNestUnspent()
        {
            foreach (var result in new[] { BattleResult.Fled, BattleResult.Defeat })
            {
                var db = Db(); var state = NewState(db);
                int zone = 6; var ev = Choice(db, zone); var cell = GridPos.FromArray(ev.Cell);
                var run = BesideCell(db, state, FloorOf(zone, 2), cell, out var beside);
                var offer = StepOn(run, cell);
                run.ResolveChoice(offer.Choice, DungeonChoice.Accept);
                int gold = state.Gold;
                var lost = run.ResolveBattle(Outcome(result));
                Assert.True(lost.ExtraReward == null && state.PendingBattle == null, result + ": nothing extra, battle cleared");
                Assert.Equal(beside, state.Position, result + ": retreat cell");
                var progress = state.Floor(run.Grid.Floor.Id);
                Assert.True(!progress.SpentEvents.Contains(cell) && !progress.ClearedBattles.Contains(cell), result + ": nest unspent");
                Assert.True(state.Gold <= gold, result + ": no extra gold");
                if (result == BattleResult.Defeat)
                {
                    Assert.True(state.Flags.Contains(GameFlow.FlagDefeatPending) && !run.CanAct, "defeat locks the run");
                    GameFlow.RecoverFromDefeat(db, state);
                    Assert.True(!state.Floor(run.Grid.Floor.Id).SpentEvents.Contains(cell), "recovery keeps the nest");
                    continue;
                }
                var again = StepOn(run, cell);
                Assert.Equal(DungeonEffect.Choice, again.Effect, "fled nest offers again");
            }
        }

        [LogicTest]
        public static void PendingEventBattleRoundtripsWithItsExtraLoot()
        {
            var db = Db(); var state = NewState(db);
            int zone = 2; var ev = Choice(db, zone); var cell = GridPos.FromArray(ev.Cell);
            var run = BesideCell(db, state, FloorOf(zone, 2), cell, out _);
            run.ResolveChoice(StepOn(run, cell).Choice, DungeonChoice.Accept);
            string saved = SaveCodec.Serialize(state);
            Assert.True(saved.Contains("\"extra_reward\""), "pending battle saves its extra reward");
            var loaded = SaveCodec.Deserialize(saved, db);
            Assert.True(loaded.PendingBattle?.ExtraReward != null && loaded.PendingBattle.ExtraReward.Gold == 400, "extra reward reloads");
            var resumed = new DungeonRun(db, loaded, loaded.FloorIndex, ArrivalMode.Resume);
            Assert.True(!resumed.CanAct && resumed.PendingBattle.Setup != null && resumed.PendingChoice == null, "resume relaunches the battle");
            int gold = loaded.Gold;
            var won = resumed.ResolveBattle(Outcome(BattleResult.Victory, ev.Group));
            Assert.Equal(gold + won.Report.Gold + 400, loaded.Gold, "paid once after reload");
            // Re-loading the pre-settlement save is a fresh, unpaid timeline: it pays exactly once too.
            var replay = SaveCodec.Deserialize(saved, db);
            int replayGold = replay.Gold;
            var replayWon = new DungeonRun(db, replay, replay.FloorIndex, ArrivalMode.Resume).ResolveBattle(Outcome(BattleResult.Victory, ev.Group));
            Assert.Equal(replayGold + replayWon.Report.Gold + 400, replay.Gold, "replayed save pays once");
            // An inconsistent save (nest already spent but battle still pending) never pays a second time.
            var stale = SaveCodec.Deserialize(saved, db);
            stale.Floor(db.Floors[FloorOf(zone, 2)].Id).SpentEvents.Add(cell);
            int staleGold = stale.Gold;
            var staleWon = new DungeonRun(db, stale, stale.FloorIndex, ArrivalMode.Resume).ResolveBattle(Outcome(BattleResult.Victory, ev.Group));
            Assert.True(staleWon.ExtraReward == null && stale.Gold == staleGold + staleWon.Report.Gold, "spent guard blocks a duplicate payout");
        }

        [LogicTest]
        public static void ChoiceCallbacksAreValidatedAndResumeReopensViaInteract()
        {
            var db = Db(); var state = NewState(db);
            int zone = 5; var ev = Choice(db, zone); var cell = GridPos.FromArray(ev.Cell);
            var run = BesideCell(db, state, FloorOf(zone, 2), cell, out _);
            var offer = StepOn(run, cell).Choice;
            // A decision object from another run (or a forged one) is stale.
            var forged = new DungeonChoice { FloorId = offer.FloorId, Cell = offer.Cell, RetreatCell = offer.RetreatCell, Event = offer.Event };
            Assert.True(run.ResolveChoice(forged, DungeonChoice.Accept).Rejected && run.PendingChoice == offer, "forged callback rejected");
            Assert.True(run.ResolveChoice(null, DungeonChoice.Leave).Rejected, "null rejected");
            Assert.True(!run.DismissChoice(forged) && run.DismissChoice(offer) && run.CanAct, "dismiss closes only the live offer");
            Assert.True(run.ResolveChoice(offer, DungeonChoice.Leave).Rejected, "dismissed offer is stale");
            Assert.True(!state.Floor(run.Grid.Floor.Id).SpentEvents.Contains(cell), "dismiss decides nothing");
            // The offer is never saved: a reload standing on the nest acts freely and Interact re-opens it.
            string saved = SaveCodec.Serialize(state);
            Assert.True(!saved.Contains("pending_choice"), "no saved modal state");
            var loaded = SaveCodec.Deserialize(saved, db);
            var resumed = new DungeonRun(db, loaded, loaded.FloorIndex, ArrivalMode.Resume);
            Assert.True(resumed.CanAct && resumed.PendingChoice == null && loaded.Position == cell, "resume on the nest");
            var reopened = Interact(resumed);
            Assert.True(reopened.Effect == DungeonEffect.Choice && reopened.Choice != null, "Interact re-opens the offer");
            Assert.True(resumed.ResolveChoice(offer, DungeonChoice.Accept).Rejected, "the old run's offer cannot drive the new run");
            // Validation against the cell: an offer whose party has moved is rejected and dropped.
            loaded.Position = loaded.Position.Step(Facing.North);
            Assert.True(resumed.ResolveChoice(reopened.Choice, DungeonChoice.Accept).Rejected && loaded.PendingBattle == null, "moved party: rejected");
            Assert.True(resumed.PendingChoice == null, "invalid offer dropped");
        }

        [LogicTest]
        public static void TownAndInnNeverResetEvents()
        {
            var db = Db(); var state = NewState(db);
            int zone = 1;
            var rescue = Rescue(db, zone); var rescueCell = GridPos.FromArray(rescue.Cell);
            var run = BesideCell(db, state, FloorOf(zone, 1), rescueCell, out _);
            StepOn(run, rescueCell);
            var choice = Choice(db, zone); var choiceCell = GridPos.FromArray(choice.Cell);
            run = BesideCell(db, state, FloorOf(zone, 2), choiceCell, out _);
            run.ResolveChoice(StepOn(run, choiceCell).Choice, DungeonChoice.Leave);
            run.ReturnToTown();
            GameFlow.EnterTown(db, state);
            state.Gold += 10000;
            Assert.True(TownServices.RestAtInn(db, state).Success, "inn rest");
            GameFlow.RecoverFromDefeat(db, state);
            var loaded = SaveCodec.Deserialize(SaveCodec.Serialize(state), db);
            Assert.True(loaded.Floor(db.Floors[FloorOf(zone, 1)].Id).SpentEvents.Contains(rescueCell), "rescue stays spent");
            Assert.True(loaded.Floor(db.Floors[FloorOf(zone, 2)].Id).SpentEvents.Contains(choiceCell), "left nest stays spent");
            int gold = loaded.Gold;
            var again = BesideCell(db, loaded, FloorOf(zone, 1), rescueCell, out _);
            Assert.True(StepOn(again, rescueCell).Effect != DungeonEffect.Rescue && loaded.Gold == gold, "no rescue after town/inn");
        }

        // ------------------------------------------------------------------ saves
        [LogicTest]
        public static void OldSavesWithoutEventFieldsLoadAndSpentRoundtrips()
        {
            var db = TestMain.DB;
            var state = NewState(db);
            var floor = db.Floors[1];
            var cell = GridPos.FromArray(Rescue(db, 1).Cell);
            state.Floor(floor.Id).SpentEvents.Add(cell);
            state.Floor(db.Floors[0].Id).OpenedChests.Add(new GridPos(9, 1));
            var round = SaveCodec.Deserialize(SaveCodec.Serialize(state), db);
            Assert.True(round.Floor(floor.Id).SpentEvents.SetEquals(new[] { cell }), "spent events roundtrip");
            // Old saves: no spent_events at all, or an explicit null, and an old pending battle without extra_reward.
            var root = JObject.Parse(SaveCodec.Serialize(state));
            foreach (var prop in ((JObject)root["floors"]).Properties()) ((JObject)prop.Value).Remove("spent_events");
            ((JObject)root["floors"][db.Floors[0].Id])["spent_events"] = JValue.CreateNull();
            var old = SaveCodec.Deserialize(root.ToString(), db);
            foreach (var p in old.Floors.Values) Assert.True(p.SpentEvents != null && p.SpentEvents.Count == 0, "missing/null spent events repaired");
            Assert.True(old.Floor(db.Floors[0].Id).OpenedChests.Contains(new GridPos(9, 1)), "other progress kept");
            var progress = new FloorProgress { SpentEvents = null };
            state.Floors["subway_2"] = progress;
            state.Repair(db);
            Assert.True(state.Floors["subway_2"].SpentEvents != null, "repair fills a null set");
            // Old pending ambush battle (no extra_reward) still settles normally.
            var legacy = NewState(db);
            var ambush = db.Floors[0].Events.First(e => e.IsAmbush); var ambushCell = GridPos.FromArray(ambush.Cell);
            legacy.FloorIndex = 0; legacy.Location = GameLocation.Dungeon; legacy.Position = ambushCell;
            legacy.PendingBattle = new DungeonBattleRequest { Kind = BattleKind.Event, FloorId = db.Floors[0].Id, Cell = ambushCell, RetreatCell = ambushCell, EnemyGroup = new List<string>(ambush.Group) };
            string text = SaveCodec.Serialize(legacy);
            Assert.True(!text.Contains("extra_reward"), "old-format pending battle has no extra reward");
            var loaded = SaveCodec.Deserialize(text, db);
            Assert.True(loaded.PendingBattle != null && loaded.PendingBattle.ExtraReward == null, "loads without extra");
            var run = new DungeonRun(db, loaded, 0, ArrivalMode.Resume);
            int gold = loaded.Gold;
            var won = run.ResolveBattle(Outcome(BattleResult.Victory, ambush.Group));
            Assert.True(won.ExtraReward == null && loaded.Gold == gold + won.Report.Gold, "ambush pays only the battle");
            Assert.True(loaded.Floor(db.Floors[0].Id).ClearedBattles.Contains(ambushCell) && !loaded.Floor(db.Floors[0].Id).SpentEvents.Contains(ambushCell), "ambush cleared, not 'spent'");
        }

        // ------------------------------------------------------------------ ambush / superboss
        [LogicTest]
        public static void AmbushAndSuperbossEventsStillFightOnEntry()
        {
            foreach (int index in new[] { 1, 36 })
            {
                var db = Db(); var state = NewState(db);
                var floor = db.Floors[index];
                var ev = index == 36 ? floor.Events.First(e => e.Group.Any(id => id.EndsWith("_ex"))) : floor.Events.First(e => e.IsAmbush);
                var cell = GridPos.FromArray(ev.Cell);
                var run = BesideCell(db, state, index, cell, out _);
                var step = StepOn(run, cell);
                Assert.True(step.Battle != null && step.Battle.Kind == BattleKind.Event && Key(step.Battle.EnemyGroup) == Key(ev.Group), floor.FloorLabel + " ambush battle");
                Assert.True(step.Battle.ExtraReward == null && step.Choice == null, floor.FloorLabel + " no extra, no offer");
                run.ResolveBattle(Outcome(BattleResult.Victory, ev.Group));
                Assert.True(state.Floor(floor.Id).ClearedBattles.Contains(cell), floor.FloorLabel + " cleared");
            }
        }

        // ------------------------------------------------------------------ lore reactions
        [LogicTest]
        public static void LoreStonesAddAnActiveHuntersReaction()
        {
            var db = Db(); var state = NewState(db);
            var reserveId = db.RosterOrder.First(id => !state.InParty(id));
            state.Reserve.Add(new HeroState { Id = reserveId, Hp = -1, Mp = -1 });
            state.Repair(db);
            Assert.True(state.Reserve.Any(h => h.Id == reserveId), "reserve hunter present");
            int index = 1; var floor = db.Floors[index];
            var stone = floor.LoreStones[0]; var cell = GridPos.FromArray(stone.Cell);
            var run = BesideCell(db, state, index, cell, out _);
            var lines = DungeonRun.LoreReactionKeys.Select(k => db.Text[k]).ToList();
            var partyNames = state.Party.Select(h => db.Heroes[h.Id].DisplayName).ToList();
            string reserveName = db.Heroes[reserveId].DisplayName;
            uint rng = state.DungeonRandomState;
            var first = StepOn(run, cell);
            Assert.Equal(DungeonEffect.Lore, first.Effect, "lore");
            Assert.True(first.StoryText.StartsWith(stone.Text + "\n\n"), "lore text first, reaction after");
            Assert.True(state.DungeonRandomState != rng, "speaker chosen with the dungeon RNG");
            var speakers = new HashSet<string>();
            var said = new HashSet<string>();
            for (int i = 0; i < 60; i++)
            {
                var text = i == 0 ? first.StoryText : Interact(run).StoryText;
                string reaction = text.Substring(stone.Text.Length + 2);
                int colon = reaction.IndexOf(": ", StringComparison.Ordinal);
                Assert.True(colon > 0 && reaction.IndexOf('\n') < 0, "one short reaction line");
                speakers.Add(reaction.Substring(0, colon));
                said.Add(reaction.Substring(colon + 2));
            }
            Assert.True(speakers.All(partyNames.Contains) && !speakers.Contains(reserveName), "only active hunters, by display name");
            Assert.True(speakers.Count > 1 && said.All(lines.Contains), "lines from the reaction table");
            // A knocked-out hunter stays quiet while someone is standing.
            foreach (var hero in state.Party.Skip(1)) hero.Hp = 0;
            string standing = db.Heroes[state.Party[0].Id].DisplayName;
            for (int i = 0; i < 12; i++) Assert.True(Interact(run).StoryText.Substring(stone.Text.Length + 2).StartsWith(standing + ": "), "standing hunter speaks");
        }
    }
}
