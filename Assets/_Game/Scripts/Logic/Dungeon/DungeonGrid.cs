// Engine-free port of dungeon_grid.gd. FOE positions reset on entry; floor progress survives.
using System;
using System.Collections.Generic;
using Abyss.Logic.Game;

namespace Abyss.Logic.Dungeon
{
    public sealed class FoeState
    {
        public string Id;
        public List<string> Group;
        public GridPos Spawn, Position;
        public readonly List<GridPos> Patrol = new List<GridPos>();
        public int ChaseRange, Target, Rest;
        public float Power;
        public bool Alive, Chasing;
    }

    public sealed class DungeonGrid
    {
        public const float CellSize = 4f;
        public const string Markers = "#.S<>WTEBLKXHN";
        public FloorDef Floor { get; }
        public FloorProgress Progress { get; }
        public int Width { get; }
        public int Height => Floor.Rows.Count;
        public GridPos Start { get; }
        public readonly List<FoeState> Foes = new List<FoeState>();
        readonly int[] parents, depths, queue;
        readonly HashSet<GridPos> occupied = new HashSet<GridPos>();

        DungeonGrid(FloorDef floor, FloorProgress progress)
        {
            Floor = floor ?? throw new ArgumentNullException(nameof(floor));
            Progress = progress ?? new FloorProgress();
            foreach (string row in floor.Rows) Width = Math.Max(Width, row.Length);
            if (Width == 0 || Height == 0) throw new ArgumentException("Floor has no layout", nameof(floor));
            parents = new int[Width * Height]; depths = new int[parents.Length]; queue = new int[parents.Length];
            var start = FindCell('S');
            Start = start == GridPos.None ? new GridPos(1, 1) : start;
            Progress.OpenedDoors.RemoveWhere(p => Cell(p) != 'L');
            Progress.Keys = Math.Max(0, Progress.Keys);
            ResetFoes();
        }

        public static DungeonGrid Parse(FloorDef floor, FloorProgress progress = null) => new DungeonGrid(floor, progress);
        public char Cell(GridPos p) => p.Y < 0 || p.Y >= Height || p.X < 0 || p.X >= Floor.Rows[p.Y].Length ? '#' : Floor.Rows[p.Y][p.X];
        public bool Contains(GridPos p) => p.Y >= 0 && p.Y < Height && p.X >= 0 && p.X < Floor.Rows[p.Y].Length;
        public bool IsWalkable(GridPos p) => Cell(p) != '#' && (Cell(p) != 'L' || Progress.OpenedDoors.Contains(p));
        public bool IsOpaque(GridPos p) => !IsWalkable(p);
        public bool IsDoor(GridPos p) => Cell(p) == 'L';
        public bool IsClosedDoor(GridPos p) => IsDoor(p) && !Progress.OpenedDoors.Contains(p);
        public bool OpenDoor(GridPos p)
        {
            if (!IsClosedDoor(p) || Progress.Keys <= 0) return false;
            Progress.Keys--; Progress.OpenedDoors.Add(p); return true;
        }
        public GridPos FindCell(char marker)
        {
            for (int y = 0; y < Height; y++)
            {
                int x = Floor.Rows[y].IndexOf(marker);
                if (x >= 0) return new GridPos(x, y);
            }
            return GridPos.None;
        }
        public IEnumerable<GridPos> FindCells(char marker)
        {
            for (int y = 0; y < Height; y++)
                for (int x = 0; x < Floor.Rows[y].Length; x++)
                    if (Floor.Rows[y][x] == marker) yield return new GridPos(x, y);
        }
        public GridPos ArrivalCell(int delta = 1)
        {
            if (delta < 0)
            {
                var stair = FindCell('>');
                if (stair != GridPos.None)
                {
                    for (int d = 0; d < 4; d++) if (Cell(stair.Step((Facing)d)) == '.') return stair.Step((Facing)d);
                    for (int d = 0; d < 4; d++) if (FoePassable(stair.Step((Facing)d))) return stair.Step((Facing)d);
                }
            }
            return Start;
        }
        public Facing ArrivalDirection(int delta = 1)
        {
            var at = ArrivalCell(delta); var stair = FindCell(delta < 0 ? '>' : '<');
            if (stair != GridPos.None)
                for (int d = 0; d < 4; d++)
                    if (at.Step((Facing)d) == stair && IsWalkable(at.Step(GridPos.Rotate((Facing)d, 2)))) return GridPos.Rotate((Facing)d, 2);
            for (int i = 0; i < 4; i++)
            {
                var d = GridPos.Rotate(Facing.East, i);
                if (IsWalkable(at.Step(d)) && at.Step(d) != stair) return d;
            }
            return Facing.East;
        }
        public void Explore(GridPos at)
        {
            Progress.Explored.Add(at);
            for (int d = 0; d < 4; d++)
            {
                var p = at.Step((Facing)d);
                if (IsWalkable(p) || IsDoor(p)) Progress.Explored.Add(p);
            }
        }
        /// <summary>Space = unseen; traps remain ordinary floor until stepped on.</summary>
        public char MapMarker(GridPos p)
        {
            if (!Progress.Explored.Contains(p)) return ' ';
            char marker = Cell(p);
            if ((marker == 'X' && !Progress.SteppedTraps.Contains(p)) || (marker == 'T' && Progress.OpenedChests.Contains(p))
                || (marker == 'K' && Progress.TakenKeys.Contains(p)) || ((marker == 'B' || marker == 'E') && Progress.ClearedBattles.Contains(p))
                || (marker == 'L' && Progress.OpenedDoors.Contains(p))) return '.';
            return marker;
        }
        public string LoreAt(GridPos p)
        {
            foreach (var row in Floor.LoreStones) if (GridPos.FromArray(row.Cell) == p) return row.Text;
            return Floor.LoreText;
        }
        public List<string> EventGroup(GridPos p)
        {
            foreach (var row in Floor.Events) if (GridPos.FromArray(row.Cell) == p && row.Group.Count > 0) return row.Group;
            return Floor.ShowcaseGroup;
        }
        public TreasureContents TreasureAt(GridPos p)
        {
            foreach (var row in Floor.Treasures) if (GridPos.FromArray(row.Cell) == p) return row.Contents;
            return new TreasureContents { Items = new Dictionary<string, int> { ["healing_potion"] = 1 } };
        }
        public void ResetFoes()
        {
            Foes.Clear();
            foreach (var def in Floor.Foes)
            {
                if (string.IsNullOrEmpty(def.Id)) continue;
                var foe = new FoeState { Id = def.Id, Group = def.Group, Spawn = GridPos.FromArray(def.Spawn), ChaseRange = Math.Max(0, def.ChaseRange),
                    Power = float.IsNaN(def.Power) || float.IsInfinity(def.Power) || def.Power <= 0f ? 1f : def.Power, Alive = !Progress.DefeatedFoes.Contains(def.Id) };
                foreach (var point in def.Patrol) { var p = GridPos.FromArray(point); if (p != GridPos.None) foe.Patrol.Add(p); }
                if (foe.Spawn == GridPos.None && foe.Patrol.Count > 0) foe.Spawn = foe.Patrol[0];
                if (foe.Spawn == GridPos.None) continue;
                if (foe.Patrol.Count == 0) foe.Patrol.Add(foe.Spawn);
                foe.Position = foe.Spawn;
                int target = foe.Patrol.IndexOf(foe.Spawn); foe.Target = Math.Max(0, target);
                Foes.Add(foe);
            }
        }
        public int FoeAt(GridPos p) { for (int i = 0; i < Foes.Count; i++) if (Foes[i].Alive && Foes[i].Position == p) return i; return -1; }
        public int FoeIndex(string id) { for (int i = 0; i < Foes.Count; i++) if (Foes[i].Id == id) return i; return -1; }
        public void DefeatFoe(int i)
        {
            if (i < 0 || i >= Foes.Count) return;
            Foes[i].Alive = false; Foes[i].Chasing = false; Progress.DefeatedFoes.Add(Foes[i].Id);
        }
        public void StaggerFoe(int i, int turns = 1) { if (i >= 0 && i < Foes.Count) Foes[i].Rest = Math.Max(Foes[i].Rest, turns); }
        public bool FoePassable(GridPos p) => IsWalkable(p) && "S<>WBE".IndexOf(Cell(p)) < 0;
        public int AdvanceFoes(GridPos player, GridPos? vacated = null)
        {
            occupied.Clear(); foreach (var foe in Foes) if (foe.Alive) occupied.Add(foe.Position);
            int caught = -1;
            for (int i = 0; i < Foes.Count; i++)
            {
                var foe = Foes[i];
                if (!foe.Alive) continue;
                if (foe.Rest > 0) { foe.Rest--; continue; }
                int distance = foe.ChaseRange > 0 && FoePassable(player) ? PathLength(foe.Position, player, foe.ChaseRange) : -1;
                foe.Chasing = distance >= 0 && distance <= foe.ChaseRange;
                GridPos goal;
                if (foe.Chasing) goal = player;
                else
                {
                    if (foe.Position == foe.Patrol[foe.Target] && foe.Patrol.Count > 1) foe.Target = (foe.Target + 1) % foe.Patrol.Count;
                    goal = foe.Patrol[foe.Target];
                }
                var next = NextStep(foe.Position, goal);
                if (next == foe.Position || (vacated.HasValue && next == vacated.Value) || occupied.Contains(next)) continue;
                occupied.Remove(foe.Position); occupied.Add(next); foe.Position = next;
                if (next == player && caught < 0) caught = i;
            }
            return caught;
        }
        public int PathLength(GridPos from, GridPos goal, int limit = -1)
        {
            if (from == goal) return 0;
            return Search(from, goal, limit) ? depths[Index(goal)] : -1;
        }
        public GridPos NextStep(GridPos from, GridPos goal)
        {
            if (from == goal || !Search(from, goal, -1)) return from;
            int start = Index(from), next = Index(goal);
            while (parents[next] != start) next = parents[next];
            return new GridPos(next % Width, next / Width);
        }
        int Index(GridPos p) => p.Y * Width + p.X;
        bool Search(GridPos from, GridPos goal, int limit)
        {
            if (!Contains(from) || !Contains(goal)) return false;
            for (int i = 0; i < parents.Length; i++) parents[i] = -1;
            int start = Index(from), end = Index(goal), head = 0, count = 1;
            parents[start] = start; depths[start] = 0; queue[0] = start;
            while (head < count)
            {
                int current = queue[head++];
                if (current == end) return true;
                if (limit >= 0 && depths[current] >= limit) continue;
                var p = new GridPos(current % Width, current / Width);
                for (int d = 0; d < 4; d++)
                {
                    var next = p.Step((Facing)d);
                    if (!FoePassable(next)) continue;
                    int n = Index(next); if (parents[n] >= 0) continue;
                    parents[n] = current; depths[n] = depths[current] + 1; queue[count++] = n;
                }
            }
            return false;
        }
        public bool LineOfSight(GridPos from, GridPos to)
        {
            if (from == to) return IsWalkable(to);
            if (IsOpaque(to)) return false;
            int dx = to.X - from.X, dy = to.Y - from.Y;
            var step = new GridPos(Math.Sign(dx), Math.Sign(dy));
            double tdx = dx == 0 ? double.PositiveInfinity : 1.0 / Math.Abs(dx), tdy = dy == 0 ? double.PositiveInfinity : 1.0 / Math.Abs(dy);
            double tx = tdx * 0.5, ty = tdy * 0.5;
            var current = from;
            while (current != to)
            {
                if (Math.Abs(tx - ty) < 0.000001)
                {
                    if (IsOpaque(current + new GridPos(step.X, 0)) || IsOpaque(current + new GridPos(0, step.Y))) return false;
                    current += step; tx += tdx; ty += tdy;
                }
                else if (tx < ty) { current.X += step.X; tx += tdx; }
                else { current.Y += step.Y; ty += tdy; }
                if (IsOpaque(current)) return false;
            }
            return true;
        }
    }
}
