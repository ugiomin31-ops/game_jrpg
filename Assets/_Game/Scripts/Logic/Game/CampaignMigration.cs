// Moves saves made with older campaign layouts onto the hunter layout (12 zones x 3 floors + the 3-floor
// postgame, 39 floors). Two older layouts exist: the original 12 floors (4 biomes x 3, B1F..B12F) and the
// 35-floor fantasy campaign (6 chapters x 5 floors + the 5-floor trial corridor). Runs from GameState.Repair,
// once per save. The four original heroes become the starting hunters in HunterRoster.MigrateLegacyHeroes.
using System;
using System.Collections.Generic;
using Abyss.Logic.Dungeon;

namespace Abyss.Logic.Game
{
    /// <summary>One-time migration of older campaign progress (floor indices, warps, floor progress, story flags).</summary>
    public static class CampaignMigration
    {
        /// <summary>Present on every save of the 35-floor layout or later (kept so old checks stay meaningful).</summary>
        public const string FlagLayout = "layout_35f";
        /// <summary>Present on every save already on the hunter layout (new games get it at creation).</summary>
        public const string FlagHunterLayout = "layout_hunter_39f";
        /// <summary>Kept on migrated saves whose party had beaten the original 12-floor final boss.</summary>
        public const string FlagLegacyEnding = "legacy_ending_seen";

        /// <summary>Floor ids of the original 12-floor campaign, in floor order (B1F..B12F).</summary>
        public static readonly string[] LegacyFloorIds =
        {
            "verdant_ruins", "verdant_ruins_b2", "verdant_ruins_b3", "frost_grotto", "frost_grotto_b5", "frost_grotto_b6",
            "ember_caverns", "ember_caverns_b8", "ember_caverns_b9", "haunted_crypt", "haunted_crypt_b11", "haunted_crypt_b12",
        };

        /// <summary>Floors per chapter and main chapters of the 35-floor layout.</summary>
        const int OldFloorsPerChapter = 5, OldMainChapters = 6;

        /// <summary>
        /// Original 12-floor index (biome b, floor k of 3) -> 35-floor index: chapter b+1's first floor, middle floor
        /// or boss floor.
        /// </summary>
        public static int MapLegacyIndex(int legacyIndex)
        {
            int clamped = Math.Max(0, Math.Min(LegacyFloorIds.Length - 1, legacyIndex));
            int biome = clamped / 3, step = clamped % 3;
            return biome * OldFloorsPerChapter + step * 2;
        }

        /// <summary>
        /// 35-floor index -> hunter index. Old chapter c (1..6) spans the city zone 2c-1 and the gate zone 2c (six
        /// floors): its floors 1..5 land on offsets 0, 1, 2, 4, 5, so the old chapter boss floor is the gate's boss
        /// floor. The trial corridor (old 31..35) maps onto the postgame zone.
        /// </summary>
        public static int Map35Index(int oldIndex)
        {
            int i = Math.Max(0, oldIndex);
            if (i >= OldMainChapters * OldFloorsPerChapter)
                return OldMainChapters * 2 * GameFlow.FloorsPerChapter + Math.Min(GameFlow.FloorsPerChapter - 1, (i - 30) * GameFlow.FloorsPerChapter / 5);
            int chapter = i / OldFloorsPerChapter, k = i % OldFloorsPerChapter;
            return chapter * 2 * GameFlow.FloorsPerChapter + (int)Math.Round(k * 6.0 / 5.0, MidpointRounding.AwayFromZero);
        }

        /// <summary>
        /// Applies the migration when <paramref name="state"/> lacks <see cref="FlagHunterLayout"/>. Safe on fresh states
        /// (it only adds the flags). Must run before any floor index is clamped or parsed.
        /// </summary>
        public static bool Apply(GameDB db, GameState state)
        {
            if (state.Flags.Contains(FlagHunterLayout)) return false;
            bool on35 = state.Flags.Contains(FlagLayout);
            state.Flags.Add(FlagLayout);
            state.Flags.Add(FlagHunterLayout);
            if (db.Floors.Count == 0) return false;
            bool legacy12 = false;
            if (!on35)
            {
                foreach (string id in state.Floors.Keys) if (Array.IndexOf(LegacyFloorIds, id) >= 0) legacy12 = true;
                legacy12 |= state.DeepestFloor > 0 || state.FloorIndex > 0 || state.WarpsUnlocked.Count > 0 || state.Flags.Contains(GameFlow.BossFlag(1));
                if (!legacy12) return false;   // a fresh game
            }

            int last = db.Floors.Count - 1;
            Func<int, int> map = old => Math.Min(last, Map35Index(legacy12 ? MapLegacyIndex(old) : old));
            state.FloorIndex = map(state.FloorIndex);
            state.DeepestFloor = Math.Max(state.FloorIndex, map(state.DeepestFloor));

            // Warps: each old crystal unlocks the nearest warp floor at or below its mapped floor.
            var warps = new SortedSet<int>();
            foreach (int old in state.WarpsUnlocked)
            {
                for (int i = map(old); i > 0; i--)
                    if (HasMarker(db.Floors[i], 'W')) { warps.Add(i); break; }
            }
            state.WarpsUnlocked = warps;

            // Old layouts are gone: their per-floor progress (cells, chests, doors) cannot carry over.
            foreach (string id in new List<string>(state.Floors.Keys))
                if (FloorIndexOf(db, id) < 0) state.Floors.Remove(id);

            // Old chapter c's boss is the boss of gate zone 2c; the city zone before it counts as cleared too.
            var oldBosses = new List<int>();
            for (int chapter = 1; chapter <= OldMainChapters + 1; chapter++)
                if (state.Flags.Remove(GameFlow.BossFlag(chapter))) oldBosses.Add(chapter);
            foreach (int chapter in oldBosses)
            {
                if (chapter > OldMainChapters) continue;
                foreach (int zone in new[] { 2 * chapter - 1, 2 * chapter })
                {
                    state.Flags.Add(GameFlow.BossFlag(zone));
                    int bossFloor = zone * GameFlow.FloorsPerChapter - 1;
                    if (bossFloor > last) continue;
                    var floor = db.Floors[bossFloor];
                    var progress = state.Floor(floor.Id);
                    foreach (var cell in Cells(floor, 'B')) progress.ClearedBattles.Add(cell);
                    foreach (var boss in floor.BossGroup) state.Flags.Add(JobService.BossDefeatedFlag(boss));
                    int next = Math.Min(last, bossFloor + 1);
                    state.DeepestFloor = Math.Max(state.DeepestFloor, next);
                    if (HasMarker(db.Floors[next], 'W')) state.WarpsUnlocked.Add(next);
                }
            }
            // Story notices already seen under old chapter numbers would replay with new texts: mark the new ones seen.
            foreach (string flag in new List<string>(state.Flags))
                if (flag.StartsWith("elder_", StringComparison.Ordinal) || flag.StartsWith("biome_", StringComparison.Ordinal)) state.Flags.Remove(flag);
            for (int zone = 1; zone <= GameFlow.MainChapters; zone++)
                if (state.Flags.Contains(GameFlow.BossFlag(zone))) state.Flags.Add("elder_" + zone + "_seen");
            for (int zone = 0; zone <= GameFlow.ChapterOf(state.DeepestFloor) - 1; zone++) state.Flags.Add("biome_" + zone + "_seen");

            // The original 12-floor final boss was the chapter 4 herald: the story continues instead of ending.
            if (legacy12 && (state.Flags.Remove(GameFlow.FlagCleared) | state.Flags.Remove(GameFlow.FlagEndingSeen))) state.Flags.Add(FlagLegacyEnding);

            // A save made inside an old floor resumes at the guild: positions and pending battles refer to old layouts.
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
