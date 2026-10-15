// Full-MP affordability, not a promise of unlimited casts or guaranteed AI selection.
using Abyss.Logic;

namespace Abyss.LogicTests
{
    public static class EnemySkillBudgetTests
    {
        static void AssertAffordable(GameDB db, EnemyDef enemy, string skillId, string source)
        {
            Assert.True(db.Skills.ContainsKey(skillId), enemy.Id + " " + source + " missing " + skillId);
            Assert.True(db.Skills[skillId].MpCost <= enemy.MaxMp,
                enemy.Id + " " + source + " " + skillId + " exceeds full MP budget " + enemy.MaxMp);
        }

        [LogicTest]
        public static void EveryAuthoredEnemySkillFitsItsFullMpBudget()
        {
            var db = TestMain.DB;
            foreach (var enemy in db.Enemies.Values)
            {
                foreach (var skill in enemy.Skills)
                    AssertAffordable(db, enemy, skill, "base");
                foreach (var phase in enemy.Phases)
                    foreach (var skill in phase.Skills)
                        AssertAffordable(db, enemy, skill, "phase");
                if (!string.IsNullOrEmpty(enemy.ChargeSkill))
                    AssertAffordable(db, enemy, enemy.ChargeSkill, "charge");
            }
        }
    }
}
