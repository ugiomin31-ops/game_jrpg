// Guild quest rules (port of game_state.gd quest_event/_refresh_quests/accept/claim). CONTENT_DESIGN §9.
using System;
using System.Collections.Generic;

namespace Abyss.Logic.Game
{
    /// <summary>Board state of a quest as shown at the Guild.</summary>
    public enum QuestBoardState { Locked = 0, Available = 1, Accepted = 2, Complete = 3, Claimed = 4 }

    /// <summary>Quest acceptance, progress and claiming.</summary>
    public static class QuestLog
    {
        public const string KindKill = "kill";
        public const string KindCollect = "collect";
        public const string KindFoe = "foe";
        public const string KindBoss = "boss";
        public const string KindExplore = "explore";

        /// <summary>Board state of one quest.</summary>
        public static QuestBoardState BoardState(GameState state, QuestDef quest)
        {
            if (state.Quests.TryGetValue(quest.Id, out var row))
                return row.State == QuestState.Claimed ? QuestBoardState.Claimed : row.State == QuestState.Complete ? QuestBoardState.Complete : QuestBoardState.Accepted;
            return quest.UnlockFloor > state.DeepestFloor ? QuestBoardState.Locked : QuestBoardState.Available;
        }

        /// <summary>Progress toward <see cref="QuestDef.Count"/> (claimed and complete quests report the full count).</summary>
        public static int Progress(GameState state, QuestDef quest)
        {
            int need = Math.Max(1, quest.Count);
            if (!state.Quests.TryGetValue(quest.Id, out var row)) return 0;
            return row.State == QuestState.Accepted ? Math.Min(need, row.Progress) : need;
        }

        /// <summary>Accepts an unlocked quest. Failure reasons: unknown_quest, already_claimed, already_accepted, locked.</summary>
        public static ServiceResult Accept(GameDB db, GameState state, string questId)
        {
            if (!db.Quests.TryGetValue(questId, out var quest)) return ServiceResult.Fail("unknown_quest");
            if (state.Quests.TryGetValue(questId, out var row))
                return ServiceResult.Fail(row.State == QuestState.Claimed ? "already_claimed" : "already_accepted");
            if (quest.UnlockFloor > state.DeepestFloor) return ServiceResult.Fail("locked");
            state.Quests[questId] = new QuestProgress { State = QuestState.Accepted };
            Refresh(db, state);
            return ServiceResult.Ok("quest_accepted");
        }

        /// <summary>
        /// Claims a completed quest: collect quests consume their items, then gold and reward items/equipment are
        /// granted. Atomic: nothing changes on failure (not_accepted, already_claimed, not_complete, unknown_quest).
        /// </summary>
        public static ServiceResult Claim(GameDB db, GameState state, string questId)
        {
            if (!db.Quests.TryGetValue(questId, out var quest)) return ServiceResult.Fail("unknown_quest");
            if (!state.Quests.TryGetValue(questId, out var row)) return ServiceResult.Fail("not_accepted");
            if (row.State == QuestState.Claimed) return ServiceResult.Fail("already_claimed");
            int need = Math.Max(1, quest.Count);
            bool complete = row.State == QuestState.Complete;
            if (quest.Kind == KindCollect) complete = state.ItemCount(quest.TargetId) >= need;
            else if (quest.Kind == KindExplore) complete = complete || FloorReached(db, state, quest.TargetId);
            if (!complete) return ServiceResult.Fail("not_complete");
            if (quest.Kind == KindCollect) state.RemoveItem(quest.TargetId, need);
            int gold = Math.Max(0, quest.RewardGold);
            state.Gold += gold;
            foreach (var kv in quest.RewardItems) if (kv.Value > 0) state.AddContent(db, kv.Key, kv.Value);
            state.Quests[questId] = new QuestProgress { State = QuestState.Claimed, Progress = need };
            Refresh(db, state);
            return new ServiceResult { Success = true, TextKey = "quest_claimed", Args = new object[] { RewardText(db, quest) }, GoldDelta = gold };
        }

        /// <summary>"1,500 G  ·  회복약 ×3" style reward summary.</summary>
        public static string RewardText(GameDB db, QuestDef quest)
        {
            var parts = new List<string>();
            if (quest.RewardGold > 0) parts.Add(quest.RewardGold.ToString("N0", System.Globalization.CultureInfo.InvariantCulture) + "만원");
            foreach (var kv in quest.RewardItems)
            {
                string name = db.Items.TryGetValue(kv.Key, out var item) ? item.DisplayName
                    : db.Equipment.TryGetValue(kv.Key, out var piece) ? piece.DisplayName : kv.Key;
                parts.Add(name + " ×" + kv.Value);
            }
            return parts.Count == 0 ? "-" : string.Join("  ·  ", parts);
        }

        /// <summary>
        /// Advances accepted quests of <paramref name="kind"/> on <paramref name="targetId"/> (kill/foe/boss; collect and
        /// explore are derived by <see cref="Refresh"/>). Appends changes to <paramref name="updates"/> when given.
        /// </summary>
        public static void Advance(GameDB db, GameState state, string kind, string targetId, int amount, List<QuestUpdate> updates = null)
        {
            if (amount <= 0 || kind == KindCollect || kind == KindExplore) return;
            foreach (var kv in state.Quests)
            {
                if (kv.Value.State != QuestState.Accepted) continue;
                if (!db.Quests.TryGetValue(kv.Key, out var quest) || quest.Kind != kind || quest.TargetId != targetId) continue;
                int need = Math.Max(1, quest.Count);
                int old = kv.Value.Progress;
                kv.Value.Progress = Math.Min(need, old + amount);
                bool done = kv.Value.Progress >= need;
                if (done) kv.Value.State = QuestState.Complete;
                Record(updates, kv.Key, old, kv.Value.Progress, done);
            }
        }

        /// <summary>
        /// Re-derives collect quests from the inventory (they can fall back to accepted when items are spent) and
        /// completes explore and one-shot boss quests from persistent successful progress. Appends changes when given.
        /// </summary>
        public static void Refresh(GameDB db, GameState state, List<QuestUpdate> updates = null)
        {
            foreach (var kv in state.Quests)
            {
                var row = kv.Value;
                if (row.State == QuestState.Claimed || !db.Quests.TryGetValue(kv.Key, out var quest)) continue;
                int need = Math.Max(1, quest.Count);
                int old = row.Progress;
                if (quest.Kind == KindCollect)
                {
                    int have = state.ItemCount(quest.TargetId);
                    bool wasComplete = row.State == QuestState.Complete;
                    row.Progress = Math.Min(need, have);
                    row.State = have >= need ? QuestState.Complete : QuestState.Accepted;
                    if (row.Progress != old || (row.State == QuestState.Complete) != wasComplete)
                        Record(updates, kv.Key, old, row.Progress, row.State == QuestState.Complete && !wasComplete);
                }
                else if (quest.Kind == KindBoss && row.State == QuestState.Accepted)
                {
                    row.Progress = Math.Min(need, Math.Max(old, BossVictories(db, state, quest.TargetId)));
                    if (row.Progress >= need) row.State = QuestState.Complete;
                    if (row.Progress != old) Record(updates, kv.Key, old, row.Progress, row.State == QuestState.Complete);
                }
                else if (quest.Kind == KindExplore && row.State == QuestState.Accepted && FloorReached(db, state, quest.TargetId))
                {
                    row.Progress = need;
                    row.State = QuestState.Complete;
                    Record(updates, kv.Key, old, need, true);
                }
            }
        }

        static int BossVictories(GameDB db, GameState state, string enemyId)
        {
            int victories = 0;
            for (int i = 0; i < db.Floors.Count; i++)
                if (db.Floors[i].BossGroup.Contains(enemyId) && state.Flags.Contains(GameFlow.BossFlag(GameFlow.ChapterOf(i))))
                    victories++;
            return victories;
        }

        /// <summary>Floor id reached: visited, current, or at/above the deepest floor index.</summary>
        public static bool FloorReached(GameDB db, GameState state, string floorId)
        {
            for (int i = 0; i < db.Floors.Count; i++)
                if (db.Floors[i].Id == floorId) return i <= state.DeepestFloor || state.Floors.ContainsKey(floorId);
            return false;
        }

        static void Record(List<QuestUpdate> updates, string questId, int old, int now, bool completed)
        {
            if (updates == null) return;
            foreach (var u in updates)
            {
                if (u.QuestId != questId) continue;
                u.NewProgress = now;
                u.Completed |= completed;
                return;
            }
            updates.Add(new QuestUpdate { QuestId = questId, OldProgress = old, NewProgress = now, Completed = completed });
        }
    }
}
