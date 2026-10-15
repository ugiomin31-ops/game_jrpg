using System.Collections.Generic;
using System.Linq;
using Abyss.Logic;
using Abyss.Logic.Game;

namespace Abyss.LogicTests
{
    public static class ExpeditionReadinessTests
    {
        [LogicTest]
        public static void FullHealthyPartyHasNoWarnings()
        {
            var db = TestMain.DB;
            var state = GameState.NewGame(db, Difficulty.Normal);
            var report = ExpeditionReadiness.Evaluate(db, state);

            Assert.True(!report.HasWarnings, "healthy full party is ready without warnings");
            Assert.Equal(0, report.IssueLines.Count, "no issue lines for healthy party");
            Assert.True(report.SummaryText.Contains("4/4명"), "summary reports all active slots");
            Assert.True(report.ObjectiveText.Contains("현재 목표:"), "objective is present");
        }

        [LogicTest]
        public static void ReportsKnockoutAndStrictLowVitalThresholds()
        {
            var db = TestMain.DB;
            var state = GameState.NewGame(db, Difficulty.Normal);
            var knockedOut = state.Party[0];
            knockedOut.Hp = 0;
            var lowVitals = state.Party[1];
            var stats = PartyStats.EffectiveStats(db, lowVitals);
            lowVitals.Hp = (stats.MaxHp * 35) / 100;
            lowVitals.Mp = stats.MaxMp == 0 ? 0 : (stats.MaxMp * 20) / 100;

            // The threshold itself is not a warning; move one point below each threshold.
            if (lowVitals.Hp * 100 >= stats.MaxHp * 35) lowVitals.Hp--;
            if (stats.MaxMp > 0 && lowVitals.Mp * 100 >= stats.MaxMp * 20) lowVitals.Mp--;
            var report = ExpeditionReadiness.Evaluate(db, state);

            Assert.True(report.HasWarnings, "KO and low vitals produce warnings");
            Assert.True(report.IssueLines.Any(line => line.Contains("전투 불능")), "KO has an explicit issue line");
            Assert.True(!report.IssueLines.Any(line => line.Contains(db.Heroes[knockedOut.Id].DisplayName) && line.Contains("체력 낮음")), "KO does not duplicate as low HP");
            if (stats.MaxHp > 1)
                Assert.True(report.IssueLines.Any(line => line.Contains(db.Heroes[lowVitals.Id].DisplayName) && line.Contains("체력 낮음")), "HP below 35 percent is reported");
            if (stats.MaxMp > 0)
                Assert.True(report.IssueLines.Any(line => line.Contains("마나 낮음")), "MP below 20 percent is reported");
        }

        [LogicTest]
        public static void PartyCountsZeroThroughFourAreSafeAndUndersizedIsAdvisory()
        {
            var db = TestMain.DB;
            for (int count = 0; count <= GameState.PartySize; count++)
            {
                var state = GameState.NewGame(db, Difficulty.Normal);
                state.Party = state.Party.Take(count).ToList();
                var report = ExpeditionReadiness.Evaluate(db, state);

                Assert.Equal(count < GameState.PartySize, report.HasWarnings, $"party size {count} readiness warning");
                Assert.Equal(count < GameState.PartySize, report.IssueLines.Any(line => line.Contains("출전 인원이 부족")), $"party size {count} capacity issue");
                Assert.True(report.SummaryText.Contains($"{count}/4명"), $"party size {count} shown in summary");
            }
        }

        [LogicTest]
        public static void ZeroMaximumMpIsNotReportedAsLow()
        {
            var db = TestMain.DB;
            var state = GameState.NewGame(db, Difficulty.Normal);
            HeroState noMpHero = null;
            foreach (var candidate in db.Heroes.Values)
            {
                var probe = new HeroState { Id = candidate.Id, Job = db.ClassOf(candidate.Id), Level = 1, Hp = 1, Mp = 0 };
                if (PartyStats.EffectiveStats(db, probe).MaxMp == 0)
                {
                    noMpHero = probe;
                    break;
                }
            }

            if (noMpHero == null) return; // Dataset has no MP-less class; other cases still cover MP thresholds.
            state.Party = new List<HeroState> { noMpHero, state.Party[1], state.Party[2], state.Party[3] };
            var report = ExpeditionReadiness.Evaluate(db, state);
            Assert.True(!report.IssueLines.Any(line => line.StartsWith(db.Heroes[noMpHero.Id].DisplayName + ":") && line.Contains("마나 낮음")), "zero max MP is not a low-resource warning");
        }

        [LogicTest]
        public static void ObjectiveTracksCanonicalProgressionMilestones()
        {
            var db = TestMain.DB;
            var state = GameState.NewGame(db, Difficulty.Normal);
            string first = ExpeditionReadiness.Evaluate(db, state).ObjectiveText;
            state.Flags.Add(GameFlow.BossFlag(1));
            string second = ExpeditionReadiness.Evaluate(db, state).ObjectiveText;
            state.Flags.Add(GameFlow.BossFlag(2));
            string third = ExpeditionReadiness.Evaluate(db, state).ObjectiveText;
            state.Flags.Add(GameFlow.FlagCleared);
            string redGate = ExpeditionReadiness.Evaluate(db, state).ObjectiveText;
            state.Flags.Add(GameFlow.BossFlag(GameFlow.MainChapters + 1));
            string completedRedGate = ExpeditionReadiness.Evaluate(db, state).ObjectiveText;

            Assert.True(first.Contains(db.Floors[2].FloorLabel), "new campaign points to first canonical boss floor");
            Assert.True(second.Contains(db.Floors[5].FloorLabel), "first boss milestone advances to zone two");
            Assert.True(third.Contains(db.Floors[8].FloorLabel), "second boss milestone advances to zone three");
            Assert.True(redGate.Contains(db.Floors[db.Floors.Count - 1].FloorLabel), "cleared campaign points to final red-gate floor");
            Assert.True(completedRedGate.Contains("붉은 게이트 공략 완료"), "red-gate boss flag marks the postgame objective complete");
            Assert.True(!completedRedGate.Contains("격파"), "completed red gate no longer prompts a boss defeat");
            Assert.True(first != second && second != third && third != redGate && redGate != completedRedGate, "objective follows progression changes");
            Assert.True(redGate.Any(c => c >= '\uac00' && c <= '\ud7a3'), "authored Korean enemy/floor name is used");
        }

        [LogicTest]
        public static void EvaluateDoesNotMutateCampaignOrRandomState()
        {
            var db = TestMain.DB;
            var state = GameState.NewGame(db, Difficulty.Normal);
            state.Flags.Add(GameFlow.BossFlag(1));
            state.DungeonRandomState = 0x12345678;
            state.DungeonEncounterSteps = 17;
            state.Party[0].Hp = 1;
            state.Party[0].Mp = 0;
            var party = state.Party.ToArray();
            var hp = party.Select(hero => hero.Hp).ToArray();
            var mp = party.Select(hero => hero.Mp).ToArray();
            var flags = state.Flags.ToArray();
            var randomState = state.DungeonRandomState;
            var encounterSteps = state.DungeonEncounterSteps;
            var inventory = new Dictionary<string, int>(state.Inventory);
            var report = ExpeditionReadiness.Evaluate(db, state);

            Assert.True(report != null, "query returns a report");
            Assert.Equal(party.Length, state.Party.Count, "party count unchanged");
            for (int i = 0; i < party.Length; i++)
            {
                Assert.True(ReferenceEquals(party[i], state.Party[i]), $"party member {i} reference unchanged");
                Assert.Equal(hp[i], state.Party[i].Hp, $"party member {i} HP unchanged");
                Assert.Equal(mp[i], state.Party[i].Mp, $"party member {i} MP unchanged");
            }
            Assert.True(flags.SequenceEqual(state.Flags), "progression flags unchanged");
            Assert.Equal(randomState, state.DungeonRandomState, "dungeon RNG state unchanged");
            Assert.Equal(encounterSteps, state.DungeonEncounterSteps, "encounter counter unchanged");
            Assert.Equal(inventory.Count, state.Inventory.Count, "inventory entries unchanged");
            foreach (var item in inventory) Assert.Equal(item.Value, state.Inventory[item.Key], "inventory amount unchanged");
        }
    }
}
