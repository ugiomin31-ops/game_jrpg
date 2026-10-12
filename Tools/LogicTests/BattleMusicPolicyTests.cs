// Battle music selection: the final-boss theme follows the formation, not the floor index.
using System.Collections.Generic;
using Abyss.Logic;
using Abyss.Logic.Battle;

namespace Abyss.LogicTests
{
    public static class BattleMusicPolicyTests
    {
        static List<string> Group(params string[] ids) => new List<string>(ids);

        [LogicTest]
        static void FinalBossSelectsFinalTheme()
        {
            Assert.Equal(BattleMusicPolicy.FinalBoss, BattleMusicPolicy.Select(BattleKind.Boss, Group("abyss_lord")), "abyss_lord boss");
            Assert.Equal(BattleMusicPolicy.FinalBoss, BattleMusicPolicy.Select(BattleKind.Boss, Group("abyss_lord_ex")), "abyss_lord_ex boss");
        }

        [LogicTest]
        static void FinalBossThemeIsFloorIndependent()
        {
            // Every floor that stages a final boss in its boss group gets the final theme, whatever its index.
            int finals = 0, offEleven = 0;
            foreach (var floor in TestMain.DB.Floors)
            {
                if (floor.BossGroup == null || floor.BossGroup.Count == 0) continue;
                bool final = floor.BossGroup.Contains("abyss_lord") || floor.BossGroup.Contains("abyss_lord_ex");
                string music = BattleMusicPolicy.Select(BattleKind.Boss, floor.BossGroup);
                Assert.Equal(final ? BattleMusicPolicy.FinalBoss : BattleMusicPolicy.Boss, music, "boss music on " + floor.Id);
                if (final) { finals++; if (floor.Index != 11) offEleven++; }
            }
            Assert.True(finals >= 2, "both final-boss floors are covered (got " + finals + ")");
            Assert.True(offEleven >= 1, "a final boss outside floor index 11 still gets the final theme");
            // The selector has no floor input: the same group on any floor gives the same theme.
            Assert.Equal(BattleMusicPolicy.FinalBoss, BattleMusicPolicy.Select(BattleKind.Boss, Group("abyss_lord_ex")), "ex final boss off floor 11");
        }

        [LogicTest]
        static void NonFinalBossSelectsBossTheme()
        {
            foreach (string id in new[] { "boss", "boss_ex", "forest_guardian", "leviathan_ex", "abyss_herald" })
                Assert.Equal(BattleMusicPolicy.Boss, BattleMusicPolicy.Select(BattleKind.Boss, Group(id)), "non-final boss " + id);
            Assert.Equal(BattleMusicPolicy.Boss, BattleMusicPolicy.Select(BattleKind.Boss, Group()), "empty boss group");
            Assert.Equal(BattleMusicPolicy.Boss, BattleMusicPolicy.Select(BattleKind.Boss, null), "null boss group");
            Assert.Equal(BattleMusicPolicy.Boss, BattleMusicPolicy.Select(BattleKind.Boss, Group("abyss_lord_x", "Abyss_Lord")), "near-miss ids");
        }

        [LogicTest]
        static void NonBossKindsIgnoreFinalBossIds()
        {
            foreach (var kind in new[] { BattleKind.Random, BattleKind.Foe, BattleKind.Event })
            {
                Assert.Equal(BattleMusicPolicy.Battle, BattleMusicPolicy.Select(kind, Group("abyss_lord")), kind + " with abyss_lord");
                Assert.Equal(BattleMusicPolicy.Battle, BattleMusicPolicy.Select(kind, Group("abyss_lord_ex", "slime")), kind + " with abyss_lord_ex");
                Assert.Equal(BattleMusicPolicy.Battle, BattleMusicPolicy.Select(kind, Group("slime")), kind + " ordinary group");
            }
        }

        [LogicTest]
        static void MixedGroupsFollowAnyFinalBossMember()
        {
            Assert.Equal(BattleMusicPolicy.FinalBoss, BattleMusicPolicy.Select(BattleKind.Boss, Group("void_knight", "abyss_lord", "void_wisp")), "final boss mid-group");
            Assert.Equal(BattleMusicPolicy.FinalBoss, BattleMusicPolicy.Select(BattleKind.Boss, Group("boss", "abyss_lord_ex")), "final boss after another boss");
            Assert.Equal(BattleMusicPolicy.FinalBoss, BattleMusicPolicy.Select(BattleKind.Boss, Group(null, "", "abyss_lord")), "null and empty ids skipped");
            Assert.Equal(BattleMusicPolicy.Boss, BattleMusicPolicy.Select(BattleKind.Boss, Group("boss", "skeleton", "skeleton")), "mixed group without final boss");
        }
    }
}
