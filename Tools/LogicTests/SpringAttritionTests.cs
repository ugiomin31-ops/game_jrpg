using System;
using System.Collections.Generic;
using System.IO;
using System.Linq;
using Abyss.Logic;
using Abyss.Logic.Dungeon;
using Abyss.Logic.Game;
using Newtonsoft.Json.Linq;

namespace Abyss.LogicTests
{
    public static class SpringAttritionTests
    {
        static readonly GridPos Spring = new GridPos(2, 1), OtherSpring = new GridPos(4, 1);
        static GameDB Db()
        {
            var db = GameDB.Load(t => File.ReadAllText(Path.Combine(Environment.GetEnvironmentVariable("ABYSS_DATA_DIR"), t + ".json")));
            // Independent open fixture: two springs at the same coordinates on two distinct floors.
            for (int i = 0; i < 2; i++)
            {
                var f = db.Floors[i];
                f.Rows = new List<string> { "########", "#SH.H..#", "#<....>#", "########" };
                f.Foes.Clear(); f.Events.Clear(); f.EncounterGroups.Clear(); f.EncounterRate = 0;
            }
            return db;
        }
        static GameState State(GameDB db)
        {
            var state = GameState.NewGame(db, Difficulty.Normal);
            GameFlow.CompletePrologue(state);
            state.Reserve.Add(new HeroState { Id = "h_minjun", Hp = -1, Mp = -1 });
            state.Repair(db);
            foreach (var hero in state.AllHunters()) hero.Tp = 43;
            return state;
        }
        static DungeonRun Run(GameDB db, GameState state)
        {
            state.Location = GameLocation.Dungeon;
            return new DungeonRun(db, state, state.FloorIndex, ArrivalMode.Resume);
        }
        static void Wound(GameState state)
        {
            foreach (var hero in state.AllHunters()) { hero.Hp = 1; hero.Mp = 0; hero.Statuses["poison"] = 3; }
        }
        static string Vitals(GameState state) => string.Join("|", state.AllHunters().Select(h => h.Id + ":" + h.Hp + ":" + h.Mp + ":" + h.Tp + ":" + string.Join(",", h.Statuses.Select(s => s.Key + "=" + s.Value))));
        static void SeedSpent(GameDB db, GameState state)
        {
            foreach (var floor in db.Floors.Take(2))
            {
                state.Floor(floor.Id).SpentSprings.Add(Spring);
                state.Floor(floor.Id).SpentSprings.Add(OtherSpring);
            }
        }
        static void Refilled(GameState state, string why)
        {
            Assert.True(state.Floors.Values.All(f => f.SpentSprings.Count == 0), why + ": all cells/floors refilled");
            Assert.True(state.AllHunters().All(h => h.Tp == 0), why + ": existing whole-roster TP reset preserved");
        }

        [LogicTest]
        public static void SteppingAndInteractConsumeOnceThenPreserveAllVitals()
        {
            var db = Db(); var state = State(db); var run = Run(db, state); Wound(state);
            uint rng = state.DungeonRandomState;
            var first = run.Move(RelativeMove.Forward);
            Assert.Equal(Spring, state.Position, "stepped onto first H");
            Assert.Equal("spring_used", first.TextKey, "existing first-use feedback retained");
            Assert.Equal(DungeonEffect.Spring, first.Effect, "spring effect");
            Assert.True(state.IsSpringSpent(db.Floors[0].Id, Spring), "first step marks spent");
            foreach (var hero in state.Party)
            {
                var stats = PartyStats.EffectiveStats(db, hero);
                Assert.Equal(stats.MaxHp, hero.Hp, "restored HP"); Assert.Equal(stats.MaxMp, hero.Mp, "restored MP");
                Assert.Equal(0, hero.Statuses.Count, "cleared statuses");
            }
            Assert.True(state.AllHunters().All(h => h.Tp == 43), "spring preserves active and reserve TP");
            Assert.Equal(rng, state.DungeonRandomState, "spring uses no RNG");
            Wound(state); string before = Vitals(state);
            Assert.Equal("spring_spent", run.Interact().TextKey, "immediate investigation explains spent");
            Assert.Equal(before, Vitals(state), "repeat interact changes no HP/MP/status/TP");
            run.Move(RelativeMove.Back); var revisit = run.Move(RelativeMove.Forward);
            Assert.Equal("spring_spent", revisit.TextKey, "walking away and back cannot heal twice");
            Assert.Equal(before, Vitals(state), "revisit changes no vitals");
        }

        [LogicTest]
        public static void InteractFirstRevivesButFullPartyStillConsumesUse()
        {
            var db = Db(); var state = State(db); state.Position = Spring; var run = Run(db, state);
            state.Party[0].Hp = 0; state.Party[0].Tp = 0;
            Assert.Equal("spring_used", run.Interact().TextKey, "first interaction on resumed H heals");
            Assert.Equal(PartyStats.EffectiveStats(db, state.Party[0]).MaxHp, state.Party[0].Hp, "KO revived");
            Assert.Equal(0, state.Party[0].Tp, "revive never invents carried TP");
            state.Position = OtherSpring;
            Assert.Equal("spring_used", run.Interact().TextKey, "full party still uses this spring");
            Wound(state); string before = Vitals(state);
            Assert.Equal("spring_spent", run.Interact().TextKey, "full-health use is not reusable");
            Assert.Equal(before, Vitals(state), "no second healing");
        }

        [LogicTest]
        public static void SeparateCellsAndFloorsRemainIndependentAcrossStairs()
        {
            var db = Db(); var state = State(db); var run = Run(db, state);
            state.Position = Spring; run.Interact();
            Assert.True(!state.IsSpringSpent(db.Floors[0].Id, OtherSpring), "different H unused");
            state.Position = OtherSpring; Wound(state); Assert.Equal("spring_used", run.Interact().TextKey, "second cell independently heals");
            state.Position = new GridPos(6, 2);
            Assert.True(run.Interact().FloorChanged, "descended through actual stairs");
            Assert.True(state.IsSpringSpent(db.Floors[0].Id, Spring), "descending never refills previous floor");
            Assert.True(!state.IsSpringSpent(db.Floors[1].Id, Spring), "same coordinates on another floor unused");
            state.Position = Spring; Wound(state); Assert.Equal("spring_used", run.Interact().TextKey, "other floor heals independently");
            state.Position = new GridPos(1, 2); Assert.True(run.Interact().FloorChanged, "ascending through stairs");
            state.Position = Spring; Wound(state); var before = Vitals(state);
            Assert.Equal("spring_spent", run.Interact().TextKey, "previous H remains spent"); Assert.Equal(before, Vitals(state), "no traversal heal");
            Assert.True(state.IsSpringSpent(db.Floors[1].Id, Spring), "ascending never refills other floor");
        }

        [LogicTest]
        public static void SaveRoundtripAndPendingBattleResumeKeepSpentCells()
        {
            var db = Db(); var state = State(db); var run = Run(db, state); SeedSpent(db, state); state.Position = Spring;
            var json = SaveCodec.Serialize(state); var raw = JObject.Parse(json);
            Assert.Equal(SaveCodec.CurrentVersion, (int)raw["version"], "no version bump");
            Assert.Equal("[[2,1],[4,1]]", raw["floors"][db.Floors[0].Id]["spent_springs"].ToString(Newtonsoft.Json.Formatting.None), "existing compact GridPos schema, deterministic and unique");
            var loaded = SaveCodec.Deserialize(json, db); var resumed = Run(db, loaded); Wound(loaded);
            var before = Vitals(loaded);
            Assert.Equal("spring_spent", resumed.Interact().TextKey, "save resume never refills"); Assert.Equal(before, Vitals(loaded), "resumed spent H cannot heal");
            loaded.PendingBattle = new DungeonBattleRequest { Kind = BattleKind.Random, FloorId = db.Floors[0].Id, Cell = Spring, RetreatCell = Spring, EnemyGroup = { "slime" }, Seed = 12 };
            loaded = SaveCodec.Deserialize(SaveCodec.Serialize(loaded), db); resumed = Run(db, loaded);
            Assert.True(!resumed.CanAct && loaded.IsSpringSpent(db.Floors[1].Id, OtherSpring), "pending battle resume keeps all floors spent");
            resumed.ResolveBattle(new BattleOutcome { Result = BattleResult.Fled });
            Assert.Equal("spring_spent", resumed.Interact().TextKey, "ordinary battle flee is not town return");
        }

        [LogicTest]
        public static void OldNullAndMalformedSpringFieldsRepairWithoutLosingProgress()
        {
            var db = Db(); var state = State(db); SeedSpent(db, state);
            var progress = state.Floor(db.Floors[0].Id); progress.Keys = 2; progress.OpenedChests.Add(OtherSpring); progress.DefeatedFoes.Add("preserve_foe");
            var raw = JObject.Parse(SaveCodec.Serialize(state));
            ((JObject)raw["floors"][db.Floors[0].Id]).Remove("spent_springs"); raw["floors"][db.Floors[1].Id]["spent_springs"] = null;
            var old = SaveCodec.Deserialize(raw.ToString(), db);
            Assert.True(old.Floors.Values.All(f => f.SpentSprings.Count == 0), "old absent/null collection empty");
            var entries = JArray.Parse("[[2,1],[2,1],null,\"bad\",[4],[],[999,999],[-1,-1],[1,1],[2,null],[2,\"1\"],[2.5,1],[999999999999,1],{\"x\":4,\"y\":1},{\"x\":2},{}]");
            raw["floors"][db.Floors[0].Id]["spent_springs"] = entries;
            var repaired = SaveCodec.Deserialize(raw.ToString(), db); var p = repaired.Floor(db.Floors[0].Id);
            Assert.True(p.SpentSprings.SetEquals(new[] { Spring, OtherSpring }), "malformed/null/duplicate/stale positions repaired, valid array/object kept");
            Assert.Equal(2, p.Keys, "unrelated keys preserved"); Assert.True(p.OpenedChests.Contains(OtherSpring) && p.DefeatedFoes.Contains("preserve_foe"), "unrelated progress preserved");
            foreach (var invalid in new JToken[] { new JObject(), new JValue("bad"), new JValue(3) })
            {
                raw["floors"][db.Floors[0].Id]["spent_springs"] = invalid;
                Assert.Equal(0, SaveCodec.Deserialize(raw.ToString(), db).Floor(db.Floors[0].Id).SpentSprings.Count, "malformed collection repairs empty");
            }
            repaired.Floor(db.Floors[0].Id).SpentSprings = null; repaired.Repair(db);
            Assert.Equal(0, repaired.Floor(db.Floors[0].Id).SpentSprings.Count, "direct null collection repaired");
        }

        [LogicTest]
        public static void ReadinessQueriesArePureAndNeverCreateFloorProgress()
        {
            var db = Db(); var state = State(db); SeedSpent(db, state); var before = SaveCodec.Serialize(state);
            for (int i = 0; i < 30; i++)
            {
                Assert.True(state.IsSpringSpent(db.Floors[0].Id, Spring), "spent query");
                Assert.True(!state.IsSpringSpent(db.Floors[0].Id, GridPos.None) && !state.IsSpringSpent("unvisited", Spring), "unused/missing queries");
            }
            Assert.Equal(before, SaveCodec.Serialize(state), "queries change no campaign state or RNG");
            Assert.True(!state.Floors.ContainsKey("unvisited"), "no mutating Floor call");
            state.Floors["null_floor"] = null; state.Floor(db.Floors[0].Id).SpentSprings = null;
            Assert.True(!state.IsSpringSpent("null_floor", Spring) && !state.IsSpringSpent(db.Floors[0].Id, Spring) && !state.IsSpringSpent(null, Spring), "null records queried without repair");
            state.Floors = null; Assert.True(!state.IsSpringSpent("any", Spring), "null map query safe");
        }

        [LogicTest]
        public static void TownPrologueEndingAndDefeatRoutesRefillAllButKeepMapAndFoes()
        {
            var db = Db();
            foreach (var reset in new Action<GameState>[] { s => GameFlow.EnterTown(db, s), s => GameFlow.EnterTown(s), GameFlow.CompletePrologue, GameFlow.MarkEndingSeen,
                s => { s.Flags.Add(GameFlow.FlagDefeatPending); GameFlow.RecoverFromDefeat(db, s); } })
            {
                var state = State(db); state.Location = GameLocation.Dungeon; SeedSpent(db, state);
                reset(state); Refilled(state, "town/story reset"); Assert.Equal(GameLocation.Town, state.Location, "actual town entry");
                reset(state); Refilled(state, "idempotent route");
            }
            var s2 = State(db); var run = Run(db, s2); SeedSpent(db, s2);
            var p = run.Grid.Progress; p.Keys = 2; p.OpenedChests.Add(OtherSpring); p.DefeatedFoes.Add("preserve_foe");
            run.ReturnToTown(); Refilled(s2, "ReturnToTown");
            Assert.Equal(2, p.Keys, "town keeps keys"); Assert.True(p.OpenedChests.Contains(OtherSpring) && p.DefeatedFoes.Contains("preserve_foe"), "town doesn't reset chests or FOE policy");
            run = new DungeonRun(db, s2, 0, ArrivalMode.Town); s2.Position = Spring; Wound(s2);
            Assert.Equal("spring_used", run.Interact().TextKey, "next outing spring works again");
        }

        [LogicTest]
        public static void TownStairsReturnStoneAndBattleEscapeRefillOnlyOnActualReturn()
        {
            var db = Db(); var state = State(db); var run = Run(db, state); SeedSpent(db, state);
            state.Position = new GridPos(1, 2);
            Assert.True(run.Interact().ReturnToTown, "first-floor up stairs return town"); Refilled(state, "town stairs");
            state = State(db); run = Run(db, state); SeedSpent(db, state);
            var stone = GameFlow.UseFieldItem(db, state, "return_stone", null, true);
            Assert.True(stone.Success && stone.ReturnToTown, "stone requests town routing");
            Assert.True(state.IsSpringSpent(db.Floors[0].Id, Spring), "request alone is not actual town entry");
            run.ReturnToTown(); Refilled(state, "return stone applied route");
            state = State(db); run = Run(db, state); SeedSpent(db, state);
            state.PendingBattle = new DungeonBattleRequest { Kind = BattleKind.Random, FloorId = db.Floors[0].Id, Cell = state.Position, RetreatCell = state.Position, EnemyGroup = { "slime" } };
            var pendingBefore = SaveCodec.Serialize(state); bool rejected = false;
            try { run.ReturnToTown(); } catch (InvalidOperationException) { rejected = true; }
            Assert.True(rejected, "pending battle prevents town return"); Assert.Equal(pendingBefore, SaveCodec.Serialize(state), "rejected return never refills");
            Assert.True(run.ResolveBattle(new BattleOutcome { Result = BattleResult.Fled, EscapedDungeon = true }).ReturnToTown, "battle escape actual town return"); Refilled(state, "battle escape");
        }

        [LogicTest]
        public static void EndingBossSettlementRefillsBeforeCreditsAndIsIdempotent()
        {
            var db = Db(); var state = State(db); SeedSpent(db, state);
            int index = db.Floors.FindIndex(f => f.Ending); var floor = db.Floors[index]; var cell = DungeonGrid.Parse(floor).FindCells('B').First();
            state.FloorIndex = index; state.Position = cell;
            state.PendingBattle = new DungeonBattleRequest { Kind = BattleKind.Boss, FloorId = floor.Id, Cell = cell, RetreatCell = cell, EnemyGroup = new List<string>(floor.BossGroup) };
            var run = Run(db, state); var outcome = new BattleOutcome { Result = BattleResult.Victory };
            var resolution = run.ResolveBattle(outcome);
            Assert.True(resolution.Ending && resolution.ReturnToTown, "ending boss actual entry to town"); Refilled(state, "ending settlement");
            Assert.True(ReferenceEquals(resolution, run.ResolveBattle(outcome)), "cached resolution retained");
        }

        [LogicTest]
        public static void InnRestSuccessRefillsButFailedInnPurchasesAndGenericHealingDoNot()
        {
            var db = Db(); var state = State(db); SeedSpent(db, state); Wound(state); state.Gold = 0;
            var before = SaveCodec.Serialize(state);
            Assert.True(!TownServices.RestAtInn(db, state).Success, "failed inn payment"); Assert.Equal(before, SaveCodec.Serialize(state), "failed rest no mutation");
            Assert.True(!TownServices.BuyItem(db, state, "healing_potion").Success, "failed purchase"); Assert.Equal(before, SaveCodec.Serialize(state), "failed purchase no mutation");
            state.Gold = 10000; Assert.True(TownServices.BuyItem(db, state, "healing_potion").Success, "successful purchase");
            PartyStats.RestoreParty(db, state); Assert.True(state.IsSpringSpent(db.Floors[0].Id, Spring), "generic healing never refills");
            Wound(state); state.AddItem("camp_tent", 1); Assert.True(GameFlow.UseFieldItem(db, state, "camp_tent", null, true).Success, "tent used");
            Assert.True(state.IsSpringSpent(db.Floors[1].Id, OtherSpring) && state.AllHunters().All(h => h.Tp == 43), "tent keeps spent springs and TP");
            state.AddItem("megalixir", 1); Wound(state); Assert.True(GameFlow.UseFieldItem(db, state, "megalixir", null, true).Success, "full-heal used");
            Assert.True(state.IsSpringSpent(db.Floors[0].Id, Spring), "full-heal doesn't refill");
            state.Floor(db.Floors[0].Id).DefeatedFoes.Add("inn_foe");
            Assert.True(TownServices.RestAtInn(db, state).Success, "paid rest succeeds"); Refilled(state, "paid inn");
            Assert.Equal(0, state.Floor(db.Floors[0].Id).DefeatedFoes.Count, "existing inn FOE reset retained");
            SeedSpent(db, state); Assert.True(TownServices.RestAtInn(db, state, free: true).Success, "free defeat-recovery rest"); Refilled(state, "free inn");
        }
    }
}
