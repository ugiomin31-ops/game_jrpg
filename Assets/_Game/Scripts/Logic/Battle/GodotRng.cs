// Bit-exact port of Godot 4's RandomNumberGenerator (RandomPCG / pcg32) so that a battle seed
// produces the same rolls as the original GDScript battle state machine.
using System;
using System.Globalization;

namespace Abyss.Logic.Battle
{
    /// <summary>
    /// Deterministic PCG32 generator with Godot's seeding, <c>randf</c>, <c>randf_range</c> and
    /// <c>randi_range</c> semantics. Every combat roll of <see cref="BattleEngine"/> goes through one instance.
    /// </summary>
    public sealed class GodotRng
    {
        const ulong DefaultInc = 1442695040888963407UL; // PCG_DEFAULT_INC_64 (Godot RandomPCG::DEFAULT_INC)
        const ulong Multiplier = 6364136223846793005UL;

        ulong _state;
        ulong _inc;

        /// <summary>Creates a generator seeded like <c>RandomNumberGenerator.seed = seed</c>.</summary>
        public GodotRng(ulong seed) { Seed(seed); }

        /// <summary>Re-seeds (pcg32_srandom_r with Godot's default stream).</summary>
        public void Seed(ulong seed)
        {
            _state = 0;
            _inc = (DefaultInc << 1) | 1UL;
            NextUInt();
            _state += seed;
            NextUInt();
        }

        /// <summary>Raw 32-bit output (pcg32_random_r).</summary>
        public uint NextUInt()
        {
            ulong old = _state;
            _state = unchecked(old * Multiplier + _inc);
            uint xorshifted = (uint)(((old >> 18) ^ old) >> 27);
            int rot = (int)(old >> 59);
            return (xorshifted >> rot) | (xorshifted << ((-rot) & 31));
        }

        /// <summary>Unbiased integer in [0, bound) (pcg32_boundedrand_r).</summary>
        public uint NextBounded(uint bound)
        {
            uint threshold = unchecked((uint)(-bound)) % bound;
            while (true)
            {
                uint r = NextUInt();
                if (r >= threshold) return r % bound;
            }
        }

        /// <summary>Godot <c>randf()</c>: single-precision float in [0, 1].</summary>
        public float Randf()
        {
            uint protoExpOffset = NextUInt();
            if (protoExpOffset == 0) return 0f;
            uint bits = NextUInt() | 0x80000001u;
            float significand = (float)(double)bits; // correctly rounded uint -> float
            return (float)(significand * Pow2(-32 - LeadingZeros(protoExpOffset)));
        }

        /// <summary>Godot <c>randf_range(from, to)</c> (float arithmetic, as in RandomPCG::random(float, float)).</summary>
        public float RandfRange(double from, double to)
        {
            float f = (float)from, t = (float)to;
            float r = Randf();
            float span = t - f;
            float scaled = r * span;
            return scaled + f;
        }

        /// <summary>Godot <c>randi_range(from, to)</c>, inclusive; consumes nothing when from == to.</summary>
        public int RandiRange(int from, int to)
        {
            if (from == to) return from;
            int lower = Math.Min(from, to), upper = Math.Max(from, to);
            ulong span = (ulong)((long)upper - lower) + 1UL;
            uint offset = span == (1UL << 32) ? NextUInt() : NextBounded((uint)span);
            return (int)((long)lower + offset);
        }

        static double Pow2(int e) => BitConverter.Int64BitsToDouble((long)(1023 + e) << 52);

        static int LeadingZeros(uint x)
        {
            int n = 0;
            if (x == 0) return 32;
            while ((x & 0x80000000u) == 0) { x <<= 1; n++; }
            return n;
        }
    }

    /// <summary>GDScript numeric helpers (roundi semantics, float32 data -> authored double).</summary>
    internal static class Gd
    {
        /// <summary>GDScript <c>roundi</c>: round half away from zero.</summary>
        public static int RoundI(double x) => (int)Math.Round(x, MidpointRounding.AwayFromZero);

        /// <summary>
        /// The JSON tables are loaded into float fields; Godot held the authored decimal as a double.
        /// Recovers the authored value (shortest round-trip text of the float) so formulas match exactly.
        /// </summary>
        public static double D(float f) => double.Parse(f.ToString("R", CultureInfo.InvariantCulture), CultureInfo.InvariantCulture);

        public static double Clamp(double v, double lo, double hi) => v < lo ? lo : (v > hi ? hi : v);
        public static int Clamp(int v, int lo, int hi) => v < lo ? lo : (v > hi ? hi : v);
    }
}
