// Moves saves made with the original 12-floor campaign (4 biomes x 3 floors, B1F..B12F) onto the 35-floor
// layout (6 chapters x 5 floors + the 5-floor trial corridor). Runs from GameState.Repair, once per save.
using System;
using System.Collections.Generic;
using Abyss.Logic.Dungeon;

namespace Abyss.Logic.Game
{
    /// <summary>One-time migration of legacy campaign progress (floor indices, warps, floor progress, story flags).</summary>
    public static class CampaignMigration
    {
        /// <summary>Present on every save already on the 35-floor layout (new games get it at creation).</summary>
        public const string FlagLayout = "layout_35f";
        /// <summary>Kept on migrated saves whose party had beaten the old final boss (now the chapter 4 boss).</summary>
        public const string FlagLegacyEnding = "legacy_ending_seen";

        /// <summary>Floor ids of the original 12-floor campaign, in floor order (B1F..B12F).</summary>
        public static readonly string[] LegacyFloorIds =
        {
            "verdant_ruins", "verdant_ruins_b2", "verdant_ruins_b3", "frost_grotto", "frost_grotto_b5", "frost_grotto_b6",
            "ember_caverns", "ember_caverns_b8", "ember_caverns_b9", "haunted_crypt", "haunted_crypt_b11", "haunted_crypt_b12",
        };

        /// <summary>
        /// Legacy floor index (biome b, floor k of 3) -> the matching floor of chapter b+1: its first floor, its
        /// middle floor, or its boss floor.
        /// </summary>
        public static int MapLegacyIndex(int legacyIndex)
        {
            int clamped = Math.Max(0, Math.Min(LegacyFloorIds.Length - 1, legacyIndex));
            int biome = clamped / 3, step = clamped % 3;
            return biome * GameFlow.FloorsPerChapter + step * 2;
        }

        /// <summary>
        /// Applies the migration when <paramref name="state"/> lacks <see cref="FlagLayout"/>. Safe on fresh states
        /// (it only adds the flag). Must run before any floor index is clamped or parsed.
        /// </summary>
        public static bool Apply(GameDB db, GameState state)
        {
            if (state.Flags.Contains(FlagLayout)) return false;
            state.Flags.Add(FlagLayout);
            if (db.Floors.Count == 0) return false;
            bool legacy = false;
            foreach (string id in state.Floors.Keys) if (Array.IndexOf(LegacyFloorIds, id) >= 0) legacy = true;
            legacy |= state.DeepestFloor > 0 || state.FloorIndex > 0 || state.WarpsUnlocked.Count > 0 || state.Flags.Contains(GameFlow.BossFlag(1));
            if (!legacy) return false;

            int last = db.Floors.Count - 1;
            state.FloorIndex = Math.Min(last, MapLegacyIndex(state.FloorIndex));
            state.DeepestFloor = Math.Min(last, MapLegacyIndex(state.DeepestFloor));
            state.DeepestFloor = Math.Max(state.DeepestFloor, state.FloorIndex);

            // Warps: each old crystal unlocks the nearest warp floor at or below its mapped floor.
            var warps = new SortedSet<int>();
            foreach (int old in state.WarpsUnlocked)
            {
                int mapped = Math.Min(last, MapLegacyIndex(old));
                for (int i = mapped; i > 0; i--)
                    if (HasMarker(db.Floors[i], 'W')) { warps.Add(i); break; }
            }
            state.WarpsUnlocked = warps;

            // Old layouts are gone: their per-floor progress (cells, chests, doors) cannot carry over.
            foreach (string id in new List<string>(state.Floors.Keys))
                if (FloorIndexOf(db, id) < 0) state.Floors.Remove(id);

            // Bosses already beaten stay beaten: their boss cell on the new boss floor counts as cleared.
            for (int chapter = 1; chapter <= 4; chapter++)
            {
                if (!state.Flags.Contains(GameFlow.BossFlag(chapter))) continue;
                int bossFloor = chapter * GameFlow.FloorsPerChapter - 1;
                if (bossFloor > last) continue;
                var floor = db.Floors[bossFloor];
                var progress = state.Floor(floor.Id);
                foreach (var cell in Cells(floor, 'B')) progress.ClearedBattles.Add(cell);
                // The old game let the party walk on into the next biome: keep that floor (and its warp) open.
                int next = Math.Min(last, bossFloor + 1);
                state.DeepestFloor = Math.Max(state.DeepestFloor, next);
                if (HasMarker(db.Floors[next], 'W')) state.WarpsUnlocked.Add(next);
                else if (HasMarker(floor, 'W')) state.WarpsUnlocked.Add(bossFloor);
            }

            // The old final boss is now the chapter 4 herald: the story continues below instead of ending.
            if (state.Flags.Remove(GameFlow.FlagCleared) | state.Flags.Remove(GameFlow.FlagEndingSeen)) state.Flags.Add(FlagLegacyEnding);

            // A save made inside an old floor resumes in town: positions and pending battles refer to old layouts.
            state.PendingBattle = null;
            state.DungeonEncounterSteps = 0;
            if (state.Location == GameLocation.Dungeon) state.Location = GameLocation.Town;
            state.Position = DungeonGrid.Parse(db.Floors[state.FloorIndex]).Start;
            state.Facing = Facing.East;
            return true;
        }

        static int FloorIndexOf(GameDB db, string id)
        {
            for (int i = 0; i < db.Floors.Count; i++) if (db.Floors[i].Id == id) return i;
            return -1;
        }

        static bool HasMarker(FloorDef floor, char marker)
        {
            foreach (string row in floor.Rows) if (row.IndexOf(marker) >= 0) return true;
            return false;
        }

        static IEnumerable<GridPos> Cells(FloorDef floor, char marker)
        {
            for (int y = 0; y < floor.Rows.Count; y++)
                for (int x = 0; x < floor.Rows[y].Length; x++)
                    if (floor.Rows[y][x] == marker) yield return new GridPos(x, y);
        }
    }
}
