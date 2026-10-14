// Motion variety: every monster and hunter action resolves to a staged style, and the roster really varies.
using System;
using System.Collections.Generic;
using System.Linq;
using Abyss.Logic;
using Abyss.Logic.Battle;

namespace Abyss.LogicTests
{
    public static class MotionStylesTests
    {
        static readonly HashSet<string> AuthoredTakes = new HashSet<string>
        { "Attack", "Slash", "Thrust", "Smash", "Spin", "Spell", "Channel", "Throw", "Rally", "Kneel" };

        static string ModelOf(EnemyDef def) => string.IsNullOrEmpty(def.Model) ? def.Id : def.Model;

        [LogicTest]
        static void EveryMonsterActionHasAStyleAndTheRosterVaries()
        {
            var moves = new HashSet<EnemyMove>();
            var flourishes = new HashSet<CastFlourish>();
            int repeatsAvoided = 0, basics = 0;
            foreach (var def in TestMain.DB.Enemies.Values)
            {
                foreach (string skill in def.Skills)
                {
                    var move = MotionStyles.EnemyApproach(ModelOf(def), def.Archetype, def.IsBoss, skill, 0);
                    Assert.True(Enum.IsDefined(typeof(EnemyMove), move), def.Id + "/" + skill + " move");
                    moves.Add(move);
                    flourishes.Add(MotionStyles.EnemyCast(ModelOf(def), def.Archetype, skill));
                }
                // Consecutive basic attacks of a walking monster change move within a few uses (blobs only bounce).
                var family = MotionStyles.FamilyOf(ModelOf(def), def.Archetype);
                if (family == BodyFamily.Blob) continue;
                basics++;
                var seen = new HashSet<EnemyMove>();
                for (int use = 0; use < 4; use++) seen.Add(MotionStyles.EnemyApproach(ModelOf(def), def.Archetype, def.IsBoss, "basic_attack", use));
                if (seen.Count >= 2) repeatsAvoided++;
            }
            Assert.True(moves.Count >= 9, "at least nine distinct monster approaches are in use (got " + moves.Count + ": " + string.Join(",", moves) + ")");
            Assert.True(flourishes.Count >= 3, "rear / hover / stomp cast flourishes are all used (got " + flourishes.Count + ")");
            Assert.True(repeatsAvoided == basics, $"every non-blob monster varies its basic attack ({repeatsAvoided}/{basics})");
        }

        [LogicTest]
        static void SkillNamesPickFittingMonsterMoves()
        {
            Assert.Equal(EnemyMove.Burrow, MotionStyles.EnemyApproach("abyss_worm", "body_only", false, "sk_e_burrow_strike", 0), "burrow strike burrows");
            Assert.Equal(EnemyMove.Swoop, MotionStyles.EnemyApproach("gargoyle", "flyer", false, "sk_e_stone_dive", 0), "a flyer dives");
            Assert.Equal(EnemyMove.Slam, MotionStyles.EnemyApproach("yeti", "body_only", false, "stunning_slam", 0), "a slam slams");
            Assert.Equal(EnemyMove.Charge, MotionStyles.EnemyApproach("nightmare", "body_only", false, "sk_e_dark_trample", 0), "a trample charges");
            Assert.Equal(EnemyMove.Spin, MotionStyles.EnemyApproach("orc", "body_only", false, "sk_cleave", 0), "a cleave spins");
            Assert.Equal(EnemyMove.Blink, MotionStyles.EnemyApproach("doppelganger", "body_only", false, "sk_e_mirror_strike", 0), "a spirit blinks");
            Assert.Equal(EnemyMove.Bounce, MotionStyles.EnemyApproach("slime", "blob", false, "basic_attack", 3), "a slime bounces");
            Assert.Equal(EnemyMove.Pounce, MotionStyles.EnemyApproach("ice_wolf", "body_only", false, "sk_twin_bite", 0), "a wolf pounces to bite");
            // A boss keeps its footing whatever the rotation says.
            foreach (var def in TestMain.DB.Enemies.Values.Where(d => d.IsBoss))
                for (int use = 0; use < 6; use++)
                {
                    var move = MotionStyles.EnemyApproach(ModelOf(def), def.Archetype, true, "basic_attack", use);
                    Assert.True(move != EnemyMove.Bounce && move != EnemyMove.Zigzag && move != EnemyMove.Pounce, def.Id + " boss move " + move);
                }
        }

        [LogicTest]
        static void HeroPlansUseKnownTakesAndVary()
        {
            var takes = new HashSet<string>();
            var flourishes = new HashSet<HeroFlourish>();
            foreach (var hero in TestMain.DB.Heroes.Values)
            {
                string cls = TestMain.DB.ClassOf(hero.Id);
                var learned = new List<string>(hero.Skills);
                if (hero.Learnset != null) learned.AddRange(hero.Learnset.Select(l => l.Skill));
                foreach (string id in learned.Distinct())
                {
                    if (!TestMain.DB.Skills.TryGetValue(id, out var skill)) continue;
                    PresentationDef pres = null;
                    if (!string.IsNullOrEmpty(skill.Presentation)) TestMain.DB.Presentations.TryGetValue(skill.Presentation, out pres);
                    bool melee = pres != null && pres.Approach != "none" && pres.ActorAction != "cast";
                    bool allies = skill.TargetType != TargetType.Enemy;
                    var plan = MotionStyles.Hero(cls, ActionKind.Skill, id, pres?.ActorAction, melee, allies, skill.HitCount, pres?.Tier ?? 1, 0);
                    Assert.True(AuthoredTakes.Contains(plan.Take), hero.Id + "/" + id + " take " + plan.Take);
                    foreach (string combo in plan.Combo) Assert.True(AuthoredTakes.Contains(combo), id + " combo take " + combo);
                    if (skill.HitCount <= 1) Assert.Equal(0, plan.Combo.Count, id + " single hit has no combo");
                    takes.Add(plan.Take); flourishes.Add(plan.Flourish);
                }
            }
            Assert.True(takes.Count >= 8, "hero skills use at least eight different takes (got " + string.Join(",", takes) + ")");
            Assert.True(flourishes.Count >= 5, "hero skills use at least five flourishes (got " + string.Join(",", flourishes) + ")");
            // Basic melee attacks rotate; clerics never stab with a mace.
            var warrior = Enumerable.Range(0, 4).Select(i => MotionStyles.Hero("warrior", ActionKind.Attack, null, null, true, false, 1, 1, i).Take).ToList();
            Assert.True(warrior.Distinct().Count() >= 3, "warrior basic attacks rotate (got " + string.Join(",", warrior) + ")");
            var cleric = Enumerable.Range(0, 4).Select(i => MotionStyles.Hero("cleric", ActionKind.Attack, null, null, true, false, 1, 1, i).Take).ToList();
            Assert.True(!cleric.Contains("Thrust"), "cleric basic attacks never thrust");
            Assert.Equal("Throw", MotionStyles.Hero("mage", ActionKind.Item, "healing_potion", null, false, true, 1, 1, 0).Take, "items are tossed");
        }

        [LogicTest]
        static void MonsterBasicAttacksHitWithTheirFamilyBlow()
        {
            // The effect / sound keys exist (Resources/Vfx/effects.json, Resources/Audio/catalogue.json next to the data).
            string data = Environment.GetEnvironmentVariable("ABYSS_DATA_DIR");
            string effects = System.IO.File.ReadAllText(System.IO.Path.Combine(data, "..", "Vfx", "effects.json"));
            string audio = System.IO.File.ReadAllText(System.IO.Path.Combine(data, "..", "Audio", "catalogue.json"));
            foreach (var (impact, sfx) in MotionStyles.AllBasicStrikes())
            {
                Assert.True(effects.Contains("\"key\": \"" + impact + "\""), "basic strike effect exists: " + impact);
                Assert.True(audio.Contains("\"" + sfx + "\""), "basic strike sound exists: " + sfx);
            }
            var impacts = new HashSet<string>();
            foreach (var def in TestMain.DB.Enemies.Values)
                for (int use = 0; use < 2; use++) impacts.Add(MotionStyles.EnemyBasicStrike(ModelOf(def), def.Archetype, use).Impact);
            Assert.True(impacts.Count >= 8, "monster basic attacks use at least eight different impacts (got " + string.Join(",", impacts) + ")");
            Assert.True(!impacts.Contains("impact"), "no monster basic attack falls back to the shared spark");
            // No two different monster melee skills share one presentation's impact any more, except the deliberate reuses.
            int heavy = TestMain.DB.Skills.Values.Count(s => s.Presentation == "pr_heavy_enemy");
            Assert.Equal(1, heavy, "only the tentacle crush keeps pr_heavy_enemy");
        }

        [LogicTest]
        static void ComboWavesCycleThroughTakes()
        {
            var plan = MotionStyles.Hero("warrior", ActionKind.Skill, "sk_w_twin_slash", "attack", true, false, 3, 2, 0);
            Assert.Equal("Slash", MotionStyles.WaveTake(plan, 1), "first wave");
            Assert.True(MotionStyles.WaveTake(plan, 2) != MotionStyles.WaveTake(plan, 1), "second wave changes take");
            Assert.True(MotionStyles.WaveTake(plan, 3) != MotionStyles.WaveTake(plan, 2), "third wave changes take");
            Assert.Equal("Attack", MotionStyles.WaveTake(null, 2), "no plan -> Attack");
        }
    }
}
