// Class change (job) rules: requirements, stats, skill retention, job-restricted gear, old saves.
using System;
using System.Collections.Generic;
using System.IO;
using System.Linq;
using Abyss.Logic;
using Abyss.Logic.Game;
using Newtonsoft.Json.Linq;

namespace Abyss.LogicTests
{
    public static class JobTests
    {
        static void SetLevel(GameDB db, HeroState hero, int level)
        {
            hero.Level = level;
            hero.Xp = 0;
            PartyStats.SyncLearnedSkills(db, hero);
            PartyStats.RestoreParty(db, new GameState { Party = new List<HeroState> { hero } });
        }

        static void Qualify(GameDB db, GameState state, HeroState hero, int level, string boss, string item)
        {
            SetLevel(db, hero, level);
            state.BestiaryOf(boss).Kills = 1;
            state.AddItem(item, 1);
        }

        [LogicTest]
        public static void JobDataCoversTheTreeWithValidSkills()
        {
            var db = TestMain.DB;
            Assert.Equal(20, db.Jobs.Count, "20 jobs incl. the four base jobs");
            foreach (var job in db.Jobs.Values)
            {
                Assert.True(db.Heroes.Values.Any(h => h.Class == job.Hero), job.Id + ": some hunter has this class");
                Assert.True(!string.IsNullOrEmpty(job.DisplayName) && !string.IsNullOrEmpty(job.Description), job.Id + ": Korean text");
                if (job.Tier == 1) { Assert.Equal(job.Hero, job.Id, "base job id is the class id"); continue; }
                Assert.True(db.Jobs.TryGetValue(job.Parent, out var parent) && parent.Tier == job.Tier - 1 && parent.Hero == job.Hero, job.Id + ": parent one tier up");
                Assert.True(db.Items.ContainsKey(job.RequiredItem), job.Id + ": class change item exists");
                Assert.True(db.Enemies.TryGetValue(job.RequiredBoss, out var boss) && boss.IsBoss, job.Id + ": required boss exists");
                // The hunter of this class with the least MP: every job skill must stay affordable for all of them.
                var maxMp = db.Heroes.Values.Where(h => h.Class == job.Hero).Min(h => PartyStats.JobLevelStats(h, job, GameState.LevelCap).MaxMp);
                int ultimates = 0;
                Assert.True(job.Learnset.Count >= (job.Tier == 2 ? 6 : 4), job.Id + ": learnset size");
                foreach (var row in job.Learnset)
                {
                    Assert.True(row.Level >= job.RequiredLevel, $"{job.Id}: {row.Skill} not before the class change level");
                    Assert.True(db.Skills.TryGetValue(row.Skill, out var skill), $"{job.Id}: {row.Skill} exists");
                    Assert.True(!string.IsNullOrEmpty(skill.DisplayName) && !string.IsNullOrEmpty(skill.Description), row.Skill + ": Korean text");
                    Assert.True(skill.Presentation != null && db.Presentations.ContainsKey(skill.Presentation), row.Skill + ": presentation exists");
                    foreach (var status in new[] { skill.StatusEffect }.Concat(skill.ExtraStatuses))
                        Assert.True(status == null || db.Statuses.ContainsKey(status), $"{row.Skill}: status {status} exists");
                    if (skill.TpCost > 0)
                    {
                        ultimates++;
                        Assert.Equal(0, skill.MpCost, row.Skill + ": ultimates cost no MP");
                        Assert.Equal("job_" + job.Id, db.Presentations[skill.Presentation].AreaVfx, row.Skill + ": signature effect");
                    }
                    else
                    {
                        Assert.True(skill.MpCost > 0, row.Skill + ": regular skills cost MP");
                        Assert.True(skill.MpCost <= maxMp / 2, $"{row.Skill} costs at most half of the job's top MP");
                    }
                }
                Assert.Equal(1, ultimates, job.Id + ": one signature ultimate");
            }
        }

        [LogicTest]
        public static void ClassChangeNeedsLevelBossAndMedal()
        {
            var db = TestMain.DB;
            var state = GameState.NewGame(db, Difficulty.Normal);
            var warrior = state.Hero("h_dohyun");
            Assert.Equal("warrior", warrior.Job, "new heroes start in their base job");
            var options = JobService.Options(db, state, warrior);
            Assert.True(options.Select(o => o.Job.Id).SequenceEqual(new[] { "knight", "berserker" }), "warrior branches to knight and berserker");
            SetLevel(db, warrior, 14);
            Assert.Equal("job_level", JobService.Check(db, state, warrior, "knight").Reason, "Lv14 is too low");
            SetLevel(db, warrior, 15);
            Assert.Equal("job_boss", JobService.Check(db, state, warrior, "knight").Reason, "chapter 1 boss not yet defeated");
            state.BestiaryOf("forest_guardian").Kills = 1;
            Assert.Equal("job_item", JobService.Check(db, state, warrior, "knight").Reason, "no medal");
            var fail = JobService.ChangeJob(db, state, "h_dohyun", "knight");
            Assert.True(!fail.Success && warrior.Job == "warrior", "failed change keeps the job");
            state.AddItem("job_medal", 2);
            Assert.True(JobService.Check(db, state, warrior, "knight").Available, "all requirements met");
            Assert.Equal("job_not_next", JobService.Check(db, state, warrior, "paladin").Reason, "master job is not reachable from the base job");
            Assert.Equal("job_not_next", JobService.Check(db, state, warrior, "priest").Reason, "another hero's job");

            state.Location = GameLocation.Dungeon;
            Assert.Equal("job_battle", JobService.ChangeJob(db, state, "h_dohyun", "knight").Reason, "town only");
            state.Location = GameLocation.Town;
            var ok = JobService.ChangeJob(db, state, "h_dohyun", "knight");
            Assert.True(ok.Success, "class change succeeds");
            Assert.Equal("job_changed_msg", ok.TextKey, "success message");
            Assert.Equal("knight", warrior.Job, "job set");
            Assert.Equal(1, state.ItemCount("job_medal"), "one medal consumed");
            Assert.Equal("job_not_next", JobService.Check(db, state, warrior, "berserker").Reason, "no sideways change");
            Assert.True(JobService.Options(db, state, warrior).Select(o => o.Job.Id).SequenceEqual(new[] { "paladin" }), "knight leads to paladin");

            var paladin = JobService.Check(db, state, warrior, "paladin");
            Assert.Equal("job_level", paladin.Reason, "master needs Lv40");
            Assert.Equal(3, paladin.Requirements.Count, "level, boss and seal lines");
            Assert.True(paladin.Requirements.All(r => !r.Met), "none met yet");
            Qualify(db, state, warrior, 40, "boss", "master_seal");
            Assert.True(JobService.ChangeJob(db, state, "h_dohyun", "paladin").Success, "master change");
            Assert.Equal(0, state.ItemCount("master_seal"), "seal consumed");

            // A flag set by story/quest scripts counts as the boss defeat as well.
            var mage = state.Hero("h_seoa");
            SetLevel(db, mage, 15);
            state.AddItem("job_medal", 1);
            state.Bestiary.Remove("forest_guardian");
            Assert.Equal("job_boss", JobService.Check(db, state, mage, "warlock").Reason, "boss gate without kill");
            state.Flags.Add(JobService.BossDefeatedFlag("forest_guardian"));
            Assert.True(JobService.ChangeJob(db, state, "h_seoa", "warlock").Success, "flag satisfies the boss gate");
        }

        [LogicTest]
        public static void JobsChangeStatsAsDesigned()
        {
            var db = TestMain.DB;
            var state = GameState.NewGame(db, Difficulty.Normal);
            var warrior = state.Hero("h_dohyun");
            SetLevel(db, warrior, 20);
            var basic = PartyStats.EffectiveStats(db, warrior);
            var knight = JobService.PreviewStats(db, warrior, "knight");
            var berserker = JobService.PreviewStats(db, warrior, "berserker");
            Assert.True(knight.Stats.Defense > basic.Stats.Defense && knight.MaxHp > basic.MaxHp, "knight is tankier");
            Assert.True(berserker.Stats.Attack > basic.Stats.Attack && berserker.Stats.Defense < basic.Stats.Defense, "berserker trades defence for attack");
            Assert.True(berserker.Crit > basic.Crit, "berserker crits more");
            var mage = state.Hero("h_seoa");
            SetLevel(db, mage, 20);
            Assert.True(JobService.PreviewStats(db, mage, "elementalist").Stats.Magic > PartyStats.EffectiveStats(db, mage).Stats.Magic, "elementalist magic");
            var archer = state.Hero("h_jiho");
            SetLevel(db, archer, 20);
            Assert.True(JobService.PreviewStats(db, archer, "sniper").Crit > PartyStats.EffectiveStats(db, archer).Crit, "sniper crit");
            Assert.True(JobService.PreviewStats(db, archer, "ranger").Stats.Speed > PartyStats.EffectiveStats(db, archer).Stats.Speed, "ranger speed");

            int hpBefore = warrior.Hp;
            Qualify(db, state, warrior, 20, "forest_guardian", "job_medal");
            hpBefore = warrior.Hp;
            Assert.True(JobService.ChangeJob(db, state, "h_dohyun", "knight").Success, "promote");
            var after = PartyStats.EffectiveStats(db, warrior);
            Assert.Equal(knight.MaxHp, after.MaxHp, "preview matches the real stats");
            Assert.Equal(knight.Stats.Defense, after.Stats.Defense, "preview defence");
            Assert.Equal(hpBefore + (after.MaxHp - basic.MaxHp), warrior.Hp, "current HP rises with the new maximum");
            var spec = PartyStats.BuildCombatSpec(db, state, "h_dohyun");
            Assert.Equal(after.Stats.Defense, spec.Defense, "battle uses job stats");
            Assert.Equal(db.Heroes["h_dohyun"].DisplayName, spec.DisplayName, "battle shows the hunter's name after a job change");
            Assert.Equal(db.Heroes["h_seoa"].DisplayName, PartyStats.BuildCombatSpec(db, state, "h_seoa").DisplayName, "base job keeps the hunter's name");
        }

        [LogicTest]
        public static void ClassChangeKeepsSkillsAndAddsJobSkills()
        {
            var db = TestMain.DB;
            var state = GameState.NewGame(db, Difficulty.Normal);
            var cleric = state.Hero("h_yuna");
            Qualify(db, state, cleric, 30, "forest_guardian", "job_medal");
            var before = new List<string>(cleric.LearnedSkills);
            var preview = JobService.PreviewNewSkills(db, cleric, "priest");
            Assert.True(JobService.ChangeJob(db, state, "h_yuna", "priest").Success, "promote to priest");
            Assert.True(before.All(cleric.LearnedSkills.Contains), "every skill learned before is kept");
            foreach (var row in db.Jobs["priest"].Learnset)
                Assert.True(cleric.LearnedSkills.Contains(row.Skill), "Lv30 priest knows " + row.Skill);
            Assert.True(preview.SequenceEqual(cleric.LearnedSkills.Except(before)), "preview lists exactly the new skills");
            Assert.True(PartyStats.BuildCombatSpec(db, state, "h_yuna").Skills.Contains("ult_jb_priest"), "job ultimate usable in battle");

            Qualify(db, state, cleric, 40, "boss", "master_seal");
            var priestSkills = new List<string>(cleric.LearnedSkills);
            Assert.True(JobService.ChangeJob(db, state, "h_yuna", "saint").Success, "promote to saint");
            Assert.True(priestSkills.All(cleric.LearnedSkills.Contains), "advanced job skills survive the master change");
            Assert.True(cleric.LearnedSkills.Contains("ult_jb_saint"), "master signature at Lv40");
            Assert.True(!cleric.LearnedSkills.Contains("jb_sa_angel_song") || GameState.LevelCap >= 56, "Lv56 skill waits for its level");
            Assert.True(!cleric.LearnedSkills.Any(s => s.StartsWith("jb_ex_")), "sibling job skills are not learned");

            // Levelling while in the job learns the job's later skills.
            var mage = state.Hero("h_seoa");
            Qualify(db, state, mage, 15, "forest_guardian", "job_medal");
            Assert.True(JobService.ChangeJob(db, state, "h_seoa", "elementalist").Success, "promote at Lv15");
            Assert.True(!mage.LearnedSkills.Contains("jb_el_eruption"), "Lv29 skill not yet");
            var report = PartyStats.AwardXp(db, mage, PartyStats.CumulativeXp(30));
            Assert.True(report != null && report.NewSkills.Contains("jb_el_eruption") && report.NewSkills.Contains("ult_jb_elementalist"), "level-up report lists new job skills");
            Assert.True(PartyStats.UpcomingSkills(db, mage).Count == 0 || PartyStats.UpcomingSkills(db, mage).All(r => r.Level > mage.Level), "upcoming list only shows higher levels");
        }

        [LogicTest]
        public static void JobWeaponsNeedTheirJob()
        {
            string dir = Environment.GetEnvironmentVariable("ABYSS_DATA_DIR");
            var db = GameDB.Load(t => File.ReadAllText(Path.Combine(dir, t + ".json")));
            try
            {
                db.Equipment["test_aegis"] = new EquipmentDef { Id = "test_aegis", DisplayName = "시험용 방패검", Slot = "weapon", Classes = { "warrior" }, Jobs = { "knight" }, Atk = 30 };
                db.Equipment["test_avenger"] = new EquipmentDef { Id = "test_avenger", DisplayName = "시험용 성검", Slot = "weapon", Classes = { "warrior" }, Jobs = { "paladin" }, Atk = 60 };
                var state = GameState.NewGame(db, Difficulty.Normal);
                var warrior = state.Hero("h_dohyun");
                state.AddEquipment("test_aegis", 1);
                state.AddEquipment("test_avenger", 1);
                Assert.True(PartyStats.CanEquip(db, "h_dohyun", "test_aegis"), "class-only check still passes");
                Assert.True(!PartyStats.CanEquip(db, warrior, "test_aegis"), "base warrior cannot wear the knight weapon");
                Assert.Equal("job_mismatch", PartyStats.Equip(db, state, "h_dohyun", "test_aegis").Reason, "equip refuses another job's weapon");
                Assert.Equal(1, state.BagCount("test_aegis"), "refused piece stays in the bag");
                bool threw = false;
                try { PartyStats.PreviewEquipment(db, warrior, "weapon", "test_aegis"); } catch (ArgumentException) { threw = true; }
                Assert.True(threw, "preview rejects a job-locked piece");

                Qualify(db, state, warrior, 15, "forest_guardian", "job_medal");
                Assert.True(JobService.ChangeJob(db, state, "h_dohyun", "knight").Success, "become a knight");
                Assert.True(PartyStats.Equip(db, state, "h_dohyun", "test_aegis").Success, "knight wears the knight weapon");
                Assert.True(!PartyStats.CanEquip(db, warrior, "test_avenger"), "knight cannot wear the paladin weapon yet");
                Qualify(db, state, warrior, 40, "boss", "master_seal");
                Assert.True(JobService.ChangeJob(db, state, "h_dohyun", "paladin").Success, "become a paladin");
                Assert.Equal("test_aegis", warrior.Equipped("weapon"), "a paladin keeps the knight weapon (job path)");
                Assert.True(PartyStats.Equip(db, state, "h_dohyun", "test_avenger").Success, "paladin wears the paladin weapon");

                var archer = state.Hero("h_jiho");
                Assert.True(!PartyStats.AllowsHero(db, db.Equipment["test_aegis"], archer), "other heroes are still blocked by class");
            }
            finally { TestMain.DB = GameDB.Load(t => File.ReadAllText(Path.Combine(dir, t + ".json"))); }
        }

        [LogicTest]
        public static void OldSavesWithoutJobLoadAsBaseJob()
        {
            var db = TestMain.DB;
            var state = GameState.NewGame(db, Difficulty.Normal);
            var root = JObject.Parse(SaveCodec.Serialize(state));
            foreach (var hero in (JArray)root["party"]) ((JObject)hero).Remove("job");
            Assert.True(!root.ToString().Contains("\"job\""), "save stripped of job fields");
            var loaded = SaveCodec.Deserialize(root.ToString(), db);
            foreach (var hero in loaded.Party) Assert.Equal(db.ClassOf(hero.Id), hero.Job, hero.Id + " loads as its base job");
            Assert.Equal(PartyStats.EffectiveStats(db, state.Hero("h_dohyun")).MaxHp, PartyStats.EffectiveStats(db, loaded.Hero("h_dohyun")).MaxHp, "same stats as before");

            var archer = state.Hero("h_jiho");
            Qualify(db, state, archer, 16, "forest_guardian", "job_medal");
            Assert.True(JobService.ChangeJob(db, state, "h_jiho", "ranger").Success, "promote");
            var again = SaveCodec.Deserialize(SaveCodec.Serialize(state), db);
            Assert.Equal("ranger", again.Hero("h_jiho").Job, "job survives a save round trip");
            Assert.True(again.Hero("h_jiho").LearnedSkills.Contains("jb_ra_quick_draw"), "job skills restored on load");

            var broken = JObject.Parse(SaveCodec.Serialize(state));
            foreach (var hero in (JArray)broken["party"]) if ((string)hero["id"] == "h_seoa") hero["job"] = "ranger";
            Assert.Equal("mage", SaveCodec.Deserialize(broken.ToString(), db).Hero("h_seoa").Job, "another hero's job is repaired to the base job");
        }
    }
}
