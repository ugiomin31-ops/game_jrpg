// Engine-free battle music selection. Pure so the final-boss rule is testable without Unity.
using System.Collections.Generic;

namespace Abyss.Logic.Battle
{
    public static class BattleMusicPolicy
    {
        public const string Battle = "bgm_battle", Boss = "bgm_boss", FinalBoss = "bgm_finalboss";

        /// <summary>Enemy ids whose boss battle plays the final-boss theme, on whatever floor they appear.</summary>
        static readonly string[] FinalBossIds = { "abyss_lord", "abyss_lord_ex" };

        /// <summary>
        /// Boss battles whose formation contains a final boss select <see cref="FinalBoss"/>; other boss battles
        /// <see cref="Boss"/>; every other kind <see cref="Battle"/>, even if a final-boss id appears in the group.
        /// </summary>
        public static string Select(BattleKind kind, IReadOnlyList<string> enemyGroup)
        {
            if (kind != BattleKind.Boss) return Battle;
            if (enemyGroup != null)
                for (int i = 0; i < enemyGroup.Count; i++)
                    if (IsFinalBoss(enemyGroup[i])) return FinalBoss;
            return Boss;
        }

        public static bool IsFinalBoss(string enemyId)
        {
            if (string.IsNullOrEmpty(enemyId)) return false;
            foreach (string id in FinalBossIds) if (id == enemyId) return true;
            return false;
        }
    }
}
