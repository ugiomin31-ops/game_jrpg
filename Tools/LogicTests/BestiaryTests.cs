// Monster book: chapter and habitat of every species, completion milestones, and the one-time rewards they grant.
using System;
using System.Collections.Generic;
using System.Linq;
using Abyss.Logic;
using Abyss.Logic.Game;

namespace Abyss.LogicTests
{
    public static class BestiaryTests
    {
        static List<string> SortedIds(GameDB db) => db.Enemies.Keys.OrderBy(id => id, StringComparer.Ordinal).ToList();

        static void Kill(GameState state, IEnumerable<string> ids)
        {
            foreach (string id in ids)
            {
                var entry = state.BestiaryOf(id);
                entry.Seen = true;
                entry.Kills = 1;
            }
        }

        [LogicTest]
        public static void EveryEnemyHasAChapterFromOneToSeven()
        {
            var db = TestMain.DB;
            var rows = TownServices.BestiaryRows(db, GameState.NewGame(db, Difficulty.Normal));
            Assert.Equal(db.Enemies.Count, rows.Count, "one row per enemy");
            var counts = new int[8];
            foreach (var row in rows)
            {
                Assert.True(row.Chapter >= 1 && row.Chapter <= 7, row.Enemy.Id + " chapter " + row.Chapter);
                counts[row.Chapter]++;
            }
            for (int chapter = 1; chapter <= 7; chapter++) Assert.True(counts[chapter] > 0, "chapter " + chapter + " lists species");
        }

        [LogicTest]
        public static void HabitatFloorsAreRealAndChapterFollowsTheFirstOne()
        {
            var db = TestMain.DB;
            var labels = db.Floors.Select(f => f.FloorLabel).ToList();
            foreach (var row in TownServices.BestiaryRows(db, GameState.NewGame(db, Difficulty.Normal)))
            {
                Assert.True(row.Habitat.Count > 0, row.Enemy.Id + " can be met on a floor");
                var indices = new List<int>();
                foreach (string label in row.Habitat)
                {
                    Assert.True(labels.Contains(label), row.Enemy.Id + " habitat " + label + " is a floor");
                    indices.Add(labels.IndexOf(label));
                }
                for (int i = 1; i < indices.Count; i++) Assert.True(indices[i] > indices[i - 1], row.Enemy.Id + " habitat ascending");
                Assert.Equal(TownServices.ChapterOfFloor(indices[0]), row.Chapter, row.Enemy.Id + " chapter of its first floor");
            }
        }

        [LogicTest]
        public static void SummonOnlySpeciesTakeTheChapterOfTheirSummoner()
        {
            var db = TestMain.DB;
            // ice_wolf is summoned by elite_ice_wolf; pretend it appears nowhere so the fallback decides its chapter.
            var habitats = TownServices.BestiaryHabitats(db);
            Assert.True(habitats.Remove("ice_wolf"), "ice_wolf has a habitat in the data");
            var chapters = TownServices.BestiaryChapters(db, habitats);
            Assert.Equal(chapters["elite_ice_wolf"], chapters["ice_wolf"], "summon-only species follows its summoner");
        }

        [LogicTest]
        public static void LevelFallbackFollowsTheChapterLevelBands()
        {
            Assert.Equal(1, TownServices.LevelChapter(1), "level 1 is chapter 1");
            Assert.Equal(1, TownServices.LevelChapter(10), "level 10 is chapter 1 (zones 1-2)");
            Assert.Equal(2, TownServices.LevelChapter(11), "level 11 enters chapter 2 (zone 3)");
            Assert.Equal(6, TownServices.LevelChapter(55), "level 55 enters chapter 6 (zone 11)");
            Assert.Equal(7, TownServices.LevelChapter(70), "level 70 is the red gate");
        }

        [LogicTest]
        public static void EveryBossCanBeMetSoAllBossesIsReachable()
        {
            var db = TestMain.DB;
            var rows = TownServices.BestiaryRows(db, GameState.NewGame(db, Difficulty.Normal));
            int bosses = 0;
            foreach (var row in rows)
            {
                if (!row.IsBoss) continue;
                bosses++;
                Assert.True(row.Habitat.Count > 0, row.Enemy.Id + " boss has a floor");
            }
            Assert.True(bosses > 0, "bosses exist");
        }

        [LogicTest]
        public static void MilestonesUnlockExactlyAtTheirThresholds()
        {
            var db = TestMain.DB;
            var ids = SortedIds(db);
            var thresholds = TownServices.BestiaryMilestones(db, GameState.NewGame(db, Difficulty.Normal))
                .Where(m => !m.AllBosses).Select(m => m.Threshold).ToList();
            Assert.Equal("10,25,40,60,80,100", string.Join(",", thresholds), "species milestones");
            foreach (int threshold in thresholds)
            {
                var state = GameState.NewGame(db, Difficulty.Normal);
                Kill(state, ids.Take(threshold - 1));
                var before = TownServices.BestiaryMilestones(db, state).Single(m => !m.AllBosses && m.Threshold == threshold);
                Assert.True(!before.Reached, threshold + " not reached with " + (threshold - 1) + " species");
                Assert.Equal(threshold - 1, before.Progress, "progress before " + threshold);
                Kill(state, ids.Skip(threshold - 1).Take(1));
                var after = TownServices.BestiaryMilestones(db, state).Single(m => !m.AllBosses && m.Threshold == threshold);
                Assert.True(after.Reached, threshold + " reached with " + threshold + " species");
                Assert.Equal(threshold, after.Progress, "progress at " + threshold);
            }
        }

        [LogicTest]
        public static void AllBossesMilestoneNeedsEveryBoss()
        {
            var db = TestMain.DB;
            var bosses = db.Enemies.Values.Where(e => e.IsBoss).Select(e => e.Id).OrderBy(id => id, StringComparer.Ordinal).ToList();
            var state = GameState.NewGame(db, Difficulty.Normal);
            Kill(state, bosses.Take(bosses.Count - 1));
            Assert.True(!TownServices.BestiaryMilestones(db, state).Single(m => m.AllBosses).Reached, "one boss short");
            Kill(state, bosses.Skip(bosses.Count - 1));
            var row = TownServices.BestiaryMilestones(db, state).Single(m => m.AllBosses);
            Assert.True(row.Reached, "every boss defeated");
            Assert.Equal(bosses.Count, row.Progress, "boss progress");
        }

        [LogicTest]
        public static void ClaimGrantsTheRewardOnceAndSetsTheFlag()
        {
            var db = TestMain.DB;
            var state = GameState.NewGame(db, Difficulty.Normal);
            Kill(state, SortedIds(db).Take(10));
            var milestone = TownServices.BestiaryMilestones(db, state)[0];
            int gold = state.Gold, stones = state.ItemCount("enhance_stone");
            var first = TownServices.ClaimBestiaryReward(db, state, 0);
            Assert.True(first.Success, "first milestone claimable at 10 species");
            Assert.Equal(milestone.Gold, first.GoldDelta, "reported gold delta");
            Assert.Equal(gold + milestone.Gold, state.Gold, "gold granted");
            Assert.Equal(stones + milestone.Items[0].Count, state.ItemCount("enhance_stone"), "item granted");
            Assert.True(state.Flags.Contains("bestiary_reward_1"), "claim flag set");
            Assert.True(TownServices.BestiaryMilestones(db, state)[0].Claimed, "row shows claimed");
            var again = TownServices.ClaimBestiaryReward(db, state, 0);
            Assert.True(!again.Success && again.Reason == "already_claimed", "second claim refused");
            Assert.Equal(gold + milestone.Gold, state.Gold, "no duplicate gold");
            Assert.Equal(stones + milestone.Items[0].Count, state.ItemCount("enhance_stone"), "no duplicate items");
            var loaded = SaveCodec.Deserialize(SaveCodec.Serialize(state), db);
            Assert.True(TownServices.BestiaryMilestones(db, loaded)[0].Claimed, "claim persists through a save");
            Assert.True(!TownServices.ClaimBestiaryReward(db, loaded, 0).Success, "claim stays refused after reload");
        }

        [LogicTest]
        public static void ClaimBeforeThresholdOrForUnknownMilestoneChangesNothing()
        {
            var db = TestMain.DB;
            var state = GameState.NewGame(db, Difficulty.Normal);
            Kill(state, SortedIds(db).Take(9));
            int gold = state.Gold, stones = state.ItemCount("enhance_stone"), flags = state.Flags.Count;
            var early = TownServices.ClaimBestiaryReward(db, state, 0);
            Assert.True(!early.Success && early.Reason == "not_reached", "9 species do not claim the 10-species reward");
            Assert.True(!TownServices.ClaimBestiaryReward(db, state, 99).Success, "index past the milestones");
            var negative = TownServices.ClaimBestiaryReward(db, state, -1);
            Assert.True(!negative.Success && negative.Reason == "invalid_milestone", "negative index");
            Assert.Equal(gold, state.Gold, "gold untouched");
            Assert.Equal(stones, state.ItemCount("enhance_stone"), "items untouched");
            Assert.Equal(flags, state.Flags.Count, "no flag written");
        }

        [LogicTest]
        public static void EveryRewardIdExistsAndIsNotEndgameGear()
        {
            var db = TestMain.DB;
            var milestones = TownServices.BestiaryMilestones(db, GameState.NewGame(db, Difficulty.Normal));
            Assert.Equal(7, milestones.Count, "six species milestones and the boss milestone");
            for (int i = 0; i < milestones.Count; i++)
            {
                var milestone = milestones[i];
                Assert.Equal(i, milestone.Index, "index matches position");
                Assert.True(milestone.Gold > 0, milestone.Label + " grants gold");
                Assert.True(milestone.Items.Count > 0, milestone.Label + " grants items");
                Assert.Equal(i + 1, int.Parse(TownServices.BestiaryRewardFlag(i).Substring("bestiary_reward_".Length)), "flag number");
                foreach (var item in milestone.Items)
                {
                    Assert.True(item.Count > 0 && item.Count <= GameState.MaxStack, item.Id + " count");
                    if (db.Items.TryGetValue(item.Id, out var consumable))
                    {
                        Assert.True(consumable.Rarity < 3, item.Id + " is not legendary");
                    }
                    else
                    {
                        Assert.True(db.Equipment.TryGetValue(item.Id, out var piece), item.Id + " exists");
                        Assert.True(piece.Rarity < 3 && piece.Tier < 8, item.Id + " is not legendary or tier 8");
                    }
                }
            }
        }
    }
}
