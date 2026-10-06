// Grid coordinates and facing for the first-person dungeon (engine-free).
using System;

namespace Abyss.Logic.Dungeon
{
    /// <summary>Cardinal facing. Numeric values match the original (N=0, E=1, S=2, W=3) and are saved.</summary>
    public enum Facing { North = 0, East = 1, South = 2, West = 3 }

    /// <summary>Movement relative to the current facing (facing itself does not change).</summary>
    public enum RelativeMove { Forward = 0, Right = 1, Back = 2, Left = 3 }

    /// <summary>Cell coordinate: X = column (0 = west), Y = row (0 = north), as authored in FloorDef.Rows.</summary>
    public struct GridPos : IEquatable<GridPos>, IComparable<GridPos>
    {
        public int X;
        public int Y;

        /// <summary>Sentinel for "no cell".</summary>
        public static readonly GridPos None = new GridPos(-1, -1);

        public GridPos(int x, int y) { X = x; Y = y; }

        /// <summary>Converts an authored [col, row] array (FloorDef cells); null/short arrays give <see cref="None"/>.</summary>
        public static GridPos FromArray(int[] cell) => cell != null && cell.Length >= 2 ? new GridPos(cell[0], cell[1]) : None;

        /// <summary>The adjacent cell in <paramref name="facing"/>.</summary>
        public GridPos Step(Facing facing) => this + Offset(facing);

        /// <summary>Unit offset of a facing (north is -Y).</summary>
        public static GridPos Offset(Facing facing)
        {
            switch (facing)
            {
                case Facing.North: return new GridPos(0, -1);
                case Facing.East: return new GridPos(1, 0);
                case Facing.South: return new GridPos(0, 1);
                default: return new GridPos(-1, 0);
            }
        }

        /// <summary>Facing rotated by <paramref name="quarterTurns"/> clockwise steps (negative = counter-clockwise).</summary>
        public static Facing Rotate(Facing facing, int quarterTurns) => (Facing)((((int)facing + quarterTurns) % 4 + 4) % 4);

        public static GridPos operator +(GridPos a, GridPos b) => new GridPos(a.X + b.X, a.Y + b.Y);
        public static GridPos operator -(GridPos a, GridPos b) => new GridPos(a.X - b.X, a.Y - b.Y);
        public static bool operator ==(GridPos a, GridPos b) => a.X == b.X && a.Y == b.Y;
        public static bool operator !=(GridPos a, GridPos b) => !(a == b);

        public bool Equals(GridPos other) => this == other;
        public override bool Equals(object obj) => obj is GridPos p && this == p;
        public override int GetHashCode() => (X * 397) ^ Y;
        /// <summary>Row-major order (Y, then X).</summary>
        public int CompareTo(GridPos other) => Y != other.Y ? Y.CompareTo(other.Y) : X.CompareTo(other.X);
        public override string ToString() => "(" + X + "," + Y + ")";
    }
}
