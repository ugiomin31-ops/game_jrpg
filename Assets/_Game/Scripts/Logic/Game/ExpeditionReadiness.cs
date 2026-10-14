using System;
using System.Collections.Generic;
using System.Collections.ObjectModel;
using Abyss.Logic;

namespace Abyss.Logic.Game
{
    /// <summary>Advisory summary of the active party before an expedition.</summary>
    public sealed class ExpeditionReadinessReport
    {
        public string ObjectiveText { get; }
        public string SummaryText { get; }
        public bool HasWarnings { get; }
        public IReadOnlyList<string> IssueLines { get; }

        internal ExpeditionReadinessReport(string objectiveText, List<string> issueLines, int partyCount)
        {
            ObjectiveText = objectiveText;
            IssueLines = new ReadOnlyCollection<string>(issueLines);
            HasWarnings = issueLines.Count > 0;
            SummaryText = HasWarnings
                ? $"출발 점검: {partyCount}/{GameState.PartySize}명 · 주의 {issueLines.Count}건"
                : $"출발 준비 양호: {partyCount}/{GameState.PartySize}명";
        }
    }

    /// <summary>Pure, advisory departure-readiness query for the current active party.</summary>
    public static class ExpeditionReadiness
    {
        private const int LowHpPercent = 35;
        private const int LowMpPercent = 20;

        /// <summary>
        /// Builds a read-only report from the campaign's canonical next story chapter and effective hunter stats.
        /// This never changes campaign state, party members, or random state; warnings do not gate departure.
        /// </summary>
        public static ExpeditionReadinessReport Evaluate(GameDB db, GameState state)
        {
            if (db == null) throw new ArgumentNullException(nameof(db));
            if (state == null) throw new ArgumentNullException(nameof(state));

            var issues = new List<string>();
            int partyCount = state.Party == null ? 0 : state.Party.Count;
            if (partyCount < GameState.PartySize)
                issues.Add($"출전 인원이 부족합니다 ({partyCount}/{GameState.PartySize}명).");

            if (state.Party != null)
            {
                foreach (var hero in state.Party)
                {
                    if (hero == null || string.IsNullOrEmpty(hero.Id) || !db.Heroes.TryGetValue(hero.Id, out var definition))
                        continue;

                    string name = string.IsNullOrEmpty(definition.DisplayName) ? hero.Id : definition.DisplayName;
                    HeroStats stats = PartyStats.EffectiveStats(db, hero);
                    int maxHp = stats.MaxHp;
                    int maxMp = stats.MaxMp;

                    if (hero.Hp <= 0)
                        issues.Add($"{name}: 전투 불능 (HP {hero.Hp}/{maxHp}).");
                    else if (maxHp > 0 && (long)hero.Hp * 100 < (long)maxHp * LowHpPercent)
                        issues.Add($"{name}: 체력 낮음 (HP {hero.Hp}/{maxHp}, 35% 미만).");

                    // A zero maximum means MP is not a usable resource, so it cannot be low.
                    if (maxMp > 0 && (long)hero.Mp * 100 < (long)maxMp * LowMpPercent)
                        issues.Add($"{name}: 마나 낮음 (MP {hero.Mp}/{maxMp}, 20% 미만).");
                }
            }

            return new ExpeditionReadinessReport(CurrentObjective(db, state), issues, partyCount);
        }

        private static string CurrentObjective(GameDB db, GameState state)
        {
            int redGateChapter = GameFlow.MainChapters + 1;
            if (state.Flags.Contains(GameFlow.BossFlag(redGateChapter)))
            {
                int completedFloorIndex = db.Floors.Count - 1;
                if (completedFloorIndex >= 0)
                {
                    FloorDef completedFloor = db.Floors[completedFloorIndex];
                    string completedFloorLabel = string.IsNullOrEmpty(completedFloor.FloorLabel) ? completedFloor.Id : completedFloor.FloorLabel;
                    return $"현재 목표: {completedFloorLabel} · 붉은 게이트 공략 완료";
                }
                return "현재 목표: 붉은 게이트 공략 완료";
            }

            int chapter = GameFlow.StoryChapter(state);
            int floorIndex = chapter * GameFlow.FloorsPerChapter - 1;
            if (floorIndex < 0 || floorIndex >= db.Floors.Count)
                return "현재 목표 정보 없음";

            FloorDef floor = db.Floors[floorIndex];
            string floorLabel = string.IsNullOrEmpty(floor.FloorLabel) ? floor.Id : floor.FloorLabel;
            string bossName = null;
            if (floor.BossGroup != null)
            {
                foreach (string enemyId in floor.BossGroup)
                {
                    if (db.Enemies.TryGetValue(enemyId, out var enemy))
                    {
                        bossName = string.IsNullOrEmpty(enemy.DisplayName) ? enemyId : enemy.DisplayName;
                        break;
                    }
                }
            }

            if (string.IsNullOrEmpty(bossName))
                return $"현재 목표: {floorLabel}";

            return $"현재 목표: {floorLabel} · {bossName} 격파";
        }
    }
}
