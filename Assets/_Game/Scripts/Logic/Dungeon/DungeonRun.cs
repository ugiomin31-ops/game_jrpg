// Campaign dungeon turns and battle settlement. No Unity dependencies.
using System;
using System.Collections.Generic;
using Abyss.Logic.Game;
using Newtonsoft.Json;

namespace Abyss.Logic.Dungeon
{
    public enum ArrivalMode { Resume = 0, Town = 1, Descending = 2, Ascending = 3 }
    public enum DungeonEffect { None = 0, Blocked = 1, DoorOpened = 2, DoorLocked = 3, Treasure = 4, Key = 5, Trap = 6, Spring = 7, Warp = 8, Lore = 9, Stairs = 10, Wait = 11 }

    /// <summary>Persisted encounter identity; battle vitals are rebuilt from the saved party on resume.</summary>
    public sealed class DungeonBattleRequest
    {
        public BattleKind Kind;
        public GridPos Cell, RetreatCell;
        public string FloorId, FoeId = "", PreText = "", PostText = "";
        public List<string> EnemyGroup = new List<string>();
        public float FoePower = 1f;
        public int Seed;
        [JsonIgnore] public BattleSetup Setup;
    }
    public sealed class DungeonStepResult
    {
        public bool Moved, FloorChanged, ReturnToTown;
        public GridPos From, To;
        public DungeonEffect Effect;
        public string TextKey = "", StoryText = "";
        public object[] Args = Array.Empty<object>();
        public StoryNotice BiomeNotice;
        public TreasureContents Treasure;
        public TrapReport Trap;
        public DungeonBattleRequest Battle;
    }
    public sealed class DungeonBattleResolution
    {
        public BattleReport Report;
        public bool ReturnToTown, Ending, Defeat;
        public string PostText = "", TextKey = "battle_return";
    }

    /// <summary>
    /// Owns one expedition. State is always current, so save it directly after each operation.
    /// A step result announces effects already committed; never grant its treasure/rewards again.
    /// </summary>
    public sealed class DungeonRun
    {
        readonly GameDB db;
        readonly Func<float> trapRoll;
        public GameState State { get; }
        public DungeonGrid Grid { get; private set; }
        public DungeonBattleRequest PendingBattle => State.PendingBattle;
        public StoryNotice ArrivalNotice { get; private set; }
        public bool CanAct => State.Location == GameLocation.Dungeon && PendingBattle == null && !State.Flags.Contains(GameFlow.FlagDefeatPending);
        DungeonBattleResolution lastResolution;

        public DungeonRun(GameDB db, GameState state, int floorIndex, ArrivalMode mode = ArrivalMode.Resume, int seed = 7331)
        {
            this.db = db ?? throw new ArgumentNullException(nameof(db));
            State = state ?? throw new ArgumentNullException(nameof(state));
            trapRoll = NextFloat;
            if (state.DungeonRandomState == 0) state.DungeonRandomState = unchecked((uint)seed) == 0 ? 7331u : unchecked((uint)seed);
            if (mode == ArrivalMode.Resume)
            {
                // Resume uses the saved floor, not a UI-selected destination.
                LoadGrid(state.FloorIndex);
                if (!Grid.IsWalkable(state.Position)) state.Position = Grid.Start;
                state.Facing = GridPos.Rotate(Facing.North, (int)state.Facing);
                Grid.Explore(state.Position);
                if (state.PendingBattle != null)
                {
                    if (state.PendingBattle.FloorId != Grid.Floor.Id) throw new ArgumentException("Pending battle belongs to a different floor");
                    PrepareSetup(state.PendingBattle);
                }
            }
            else
            {
                if (state.PendingBattle != null) throw new InvalidOperationException("Resolve the battle before changing floor");
                if (mode == ArrivalMode.Town && !TownServices.Depart(db, state, floorIndex).Success) throw new ArgumentException("Departure warp is locked", nameof(floorIndex));
                EnterFloor(floorIndex, mode == ArrivalMode.Ascending ? -1 : 1, mode == ArrivalMode.Town);
            }
        }
        void LoadGrid(int index)
        {
            if (index < 0 || index >= db.Floors.Count) throw new ArgumentOutOfRangeException(nameof(index));
            State.FloorIndex = index;
            var floor = db.Floors[index];
            Grid = DungeonGrid.Parse(floor, State.Floor(floor.Id));
        }
        void EnterFloor(int index, int delta, bool town = false)
        {
            LoadGrid(index);
            State.Position = town ? Grid.Start : Grid.ArrivalCell(delta);
            State.Facing = town ? Facing.East : Grid.ArrivalDirection(delta);
            State.Location = GameLocation.Dungeon;
            State.DungeonEncounterSteps = 0;
            State.SetDeepestFloor(db, index);
            Grid.Explore(State.Position);
            ArrivalNotice = GameFlow.BiomeIntro(State, index);
        }
        public DungeonStepResult Turn(int quarterTurns)
        {
            var result = Result();
            if (CanAct) State.Facing = GridPos.Rotate(State.Facing, quarterTurns);
            return result;
        }
        public DungeonStepResult Move(RelativeMove move)
        {
            var result = Result();
            if (!CanAct) return result;
            var target = State.Position.Step(GridPos.Rotate(State.Facing, (int)move));
            if (Grid.IsClosedDoor(target)) return OpenDoor(target, result);
            if (!Grid.IsWalkable(target)) { result.Effect = DungeonEffect.Blocked; result.TextKey = "blocked"; return result; }
            var from = State.Position;
            State.Position = target; State.DungeonEncounterSteps++;
            result.Moved = true; result.To = target; Grid.Explore(target);
            int bumped = Grid.FoeAt(target);
            if (bumped >= 0) { result.Battle = StartFoe(bumped, from); return result; }
            int caught = Grid.AdvanceFoes(target, from);
            if (StartFixed(result, from)) return result;
            ApplyCell(result, true);
            if (caught >= 0) result.Battle = StartFoe(caught, from);
            else if (result.Effect == DungeonEffect.None && State.DungeonEncounterSteps >= Grid.Floor.MinEncounterSteps
                && (EncounterGuaranteed() || NextFloat() < Grid.Floor.EncounterRate))
            {
                int count = 0;
                foreach (var group in Grid.Floor.EncounterGroups) if (group.Count > 0) count++;
                if (count > 0)
                {
                    int choice = (int)(NextUInt() % (uint)count);
                    foreach (var group in Grid.Floor.EncounterGroups)
                        if (group.Count > 0 && choice-- == 0) { result.Battle = StartBattle(BattleKind.Random, group, State.Position, from); break; }
                }
            }
            result.To = State.Position;
            return result;
        }
        public DungeonStepResult Interact()
        {
            var result = Result();
            if (!CanAct) return result;
            var front = State.Position.Step(State.Facing);
            if (Grid.IsClosedDoor(front)) return OpenDoor(front, result);
            // Resume on an uncleared fixed cell remains playable without walking away and back.
            if (StartFixed(result, State.Position)) return result;
            ApplyCell(result, false);
            return result.Effect == DungeonEffect.None ? WaitTurn() : result;
        }
        public DungeonStepResult WaitTurn()
        {
            var result = Result();
            if (!CanAct) return result;
            result.Effect = DungeonEffect.Wait; result.TextKey = "wait_turn";
            int caught = Grid.AdvanceFoes(State.Position);
            if (caught >= 0) result.Battle = StartFoe(caught, State.Position);
            return result;
        }
        /// <summary>Pity timer: a random battle is forced once <see cref="FloorDef.MaxEncounterSteps"/> steps pass without one.</summary>
        bool EncounterGuaranteed() => Grid.Floor.MaxEncounterSteps > 0 && State.DungeonEncounterSteps >= Grid.Floor.MaxEncounterSteps;
        DungeonStepResult Result() => new DungeonStepResult { From = State.Position, To = State.Position };
        DungeonStepResult OpenDoor(GridPos at, DungeonStepResult result)
        {
            bool opened = Grid.OpenDoor(at);
            result.Effect = opened ? DungeonEffect.DoorOpened : DungeonEffect.DoorLocked;
            result.TextKey = opened ? "door_opened" : "door_locked";
            if (opened) Grid.Explore(State.Position);
            return result;
        }
        bool StartFixed(DungeonStepResult result, GridPos from)
        {
            if (Grid.Progress.ClearedBattles.Contains(State.Position)) return false;
            char marker = Grid.Cell(State.Position);
            if (marker == 'B')
            {
                var group = Grid.Floor.BossGroup;
                if (group.Count == 0) group = new List<string> { "boss" };
                result.Battle = StartBattle(BattleKind.Boss, group, State.Position, from); return true;
            }
            if (marker == 'E')
            {
                var group = Grid.EventGroup(State.Position);
                if (group.Count > 0) { result.Battle = StartBattle(BattleKind.Event, group, State.Position, from); return true; }
            }
            return false;
        }
        void ApplyCell(DungeonStepResult result, bool stepping)
        {
            var at = State.Position;
            switch (Grid.Cell(at))
            {
                case '>': case '<':
                    result.Effect = DungeonEffect.Stairs;
                    int delta = Grid.Cell(at) == '>' ? 1 : -1;
                    int destination = State.FloorIndex + delta;
                    if (destination < 0) { ReturnToTown(); result.ReturnToTown = true; }
                    else if (destination < db.Floors.Count)
                    {
                        EnterFloor(destination, delta); result.FloorChanged = true; result.BiomeNotice = ArrivalNotice;
                    }
                    else result.TextKey = "blocked";
                    result.To = State.Position;
                    break;
                case 'W':
                    State.WarpsUnlocked.Add(State.FloorIndex); result.Effect = DungeonEffect.Warp; result.TextKey = "warp_activated"; break;
                case 'T':
                    if (!Grid.Progress.OpenedChests.Add(at)) break;
                    result.Effect = DungeonEffect.Treasure; result.TextKey = "treasure_opened";
                    result.Treasure = Grid.TreasureAt(at);
                    State.AddContents(db, result.Treasure); break;
                case 'K':
                    if (!Grid.Progress.TakenKeys.Add(at)) break;
                    Grid.Progress.Keys++; result.Effect = DungeonEffect.Key;
                    result.TextKey = string.IsNullOrEmpty(Grid.Floor.KeyName) ? "key_found" : "key_found_named";
                    if (!string.IsNullOrEmpty(Grid.Floor.KeyName)) result.Args = new object[] { Grid.Floor.KeyName };
                    break;
                case 'X':
                    if (!stepping) break;
                    Grid.Progress.SteppedTraps.Add(at); result.Effect = DungeonEffect.Trap; result.TextKey = "trap_triggered";
                    result.Trap = PartyStats.ApplyTrap(db, State, trapRoll); break;
                case 'H':
                    PartyStats.RestoreParty(db, State); result.Effect = DungeonEffect.Spring; result.TextKey = "spring_used"; break;
                case 'N':
                    result.Effect = DungeonEffect.Lore; result.StoryText = Grid.LoreAt(at);
                    if (string.IsNullOrEmpty(result.StoryText)) result.TextKey = "lore_empty";
                    State.Flags.Add("lore_" + Grid.Floor.Id + "_" + at); break;
            }
        }
        DungeonBattleRequest StartFoe(int i, GridPos retreat)
        {
            var foe = Grid.Foes[i];
            return StartBattle(BattleKind.Foe, foe.Group, foe.Position, retreat, foe.Id, foe.Power);
        }
        DungeonBattleRequest StartBattle(BattleKind kind, List<string> group, GridPos cell, GridPos retreat, string foeId = "", float power = 1f)
        {
            var request = new DungeonBattleRequest { Kind = kind, Cell = cell, RetreatCell = retreat, FloorId = Grid.Floor.Id,
                EnemyGroup = new List<string>(group), FoeId = foeId, FoePower = power, Seed = unchecked((int)NextUInt()),
                PreText = kind == BattleKind.Boss ? Grid.Floor.BossPreText : "", PostText = kind == BattleKind.Boss ? Grid.Floor.BossPostText : "" };
            PrepareSetup(request);
            State.PendingBattle = request; lastResolution = null;
            return request;
        }
        void PrepareSetup(DungeonBattleRequest request) => request.Setup = PartyStats.BuildBattleSetup(db, State, request.Kind, request.EnemyGroup, request.FoePower, request.FloorId, request.Seed);
        /// <summary>Commit once, before showing battle rewards; saving now atomically includes map completion.</summary>
        public DungeonBattleResolution ResolveBattle(BattleOutcome outcome)
        {
            if (outcome == null || outcome.Result == BattleResult.None) throw new ArgumentException("Battle has no result", nameof(outcome));
            var request = PendingBattle;
            if (request == null) return lastResolution ?? throw new InvalidOperationException("No battle is pending");
            var result = new DungeonBattleResolution { Report = PartyStats.ApplyBattleOutcome(db, State, outcome), Defeat = outcome.Result == BattleResult.Defeat };
            bool victory = outcome.Result == BattleResult.Victory;
            if (request.Kind == BattleKind.Foe)
            {
                int i = Grid.FoeIndex(request.FoeId);
                if (victory) { Grid.DefeatFoe(i); result.TextKey = "foe_defeated"; }
                else { Grid.StaggerFoe(i); Retreat(request, result); }
            }
            else if (request.Kind == BattleKind.Boss || request.Kind == BattleKind.Event)
            {
                if (victory) Grid.Progress.ClearedBattles.Add(request.Cell);
                else Retreat(request, result);
            }
            if (victory && request.Kind == BattleKind.Boss)
            {
                State.Flags.Add(GameFlow.BossFlag(State.FloorIndex / 3 + 1));
                result.PostText = request.PostText;
                if (State.FloorIndex == db.Floors.Count - 1)
                {
                    State.Flags.Add(GameFlow.FlagCleared); State.Location = GameLocation.Town;
                    result.Ending = true; result.ReturnToTown = true;
                }
            }
            State.PendingBattle = null; State.DungeonEncounterSteps = 0;
            if (result.Defeat) State.Flags.Add(GameFlow.FlagDefeatPending);
            else if (outcome.EscapedDungeon) { ReturnToTown(); result.ReturnToTown = true; }
            Grid.Explore(State.Position);
            lastResolution = result;
            return result;
        }
        void Retreat(DungeonBattleRequest request, DungeonBattleResolution result)
        {
            if (Grid.IsWalkable(request.RetreatCell)) State.Position = request.RetreatCell;
            result.TextKey = "battle_retreat";
        }
        public void ReturnToTown()
        {
            if (PendingBattle != null) throw new InvalidOperationException("Resolve the battle before leaving");
            State.Location = GameLocation.Town;
        }
        uint NextUInt()
        {
            uint value = State.DungeonRandomState;
            value ^= value << 13; value ^= value >> 17; value ^= value << 5;
            State.DungeonRandomState = value; return value;
        }
        float NextFloat() => (NextUInt() >> 8) * (1f / 16777216f);
    }
}
