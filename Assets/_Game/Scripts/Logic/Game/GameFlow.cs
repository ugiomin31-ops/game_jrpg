// Campaign flow rules from main.gd: resume routing, prologue/ending, one-shot tips, elder lines,
// biome intros, defeat recovery and field (camp) item use. Scene routing itself lives in Unity.
using System;
using System.Collections.Generic;

namespace Abyss.Logic.Game
{
    /// <summary>Screen to show when a save is continued.</summary>
    public enum ResumeRoute { Prologue = 0, Town = 1, Dungeon = 2, GameOver = 3, Ending = 4 }

    /// <summary>A line to show once (tip, elder line, biome intro). Keys are text_ko keys.</summary>
    public sealed class StoryNotice
    {
        /// <summary>Speaker name key ("elder", "tip_title", "lore"...).</summary>
        public string TitleKey;
        public string TextKey;
        /// <summary>Literal text shown instead of <see cref="TextKey"/> (hunter join notices).</summary>
        public string Text;
        /// <summary>Hunter id whose portrait goes with the notice (join notices), else null.</summary>
        public string HeroId;
    }

    /// <summary>Result of using an item outside battle.</summary>
    public sealed class FieldItemResult
    {
        public bool Success;
        /// <summary>"used" on success (format with the item name), else a failure key (item_missing, item_unavailable, invalid_target, no_effect).</summary>
        public string TextKey;
        /// <summary>return_stone in the dungeon: the Unity layer goes back to town.</summary>
        public bool ReturnToTown;
    }

    /// <summary>Campaign flow helpers. All flags live in <see cref="GameState.Flags"/>.</summary>
    public static class GameFlow
    {
        public const string FlagProloguePending = "prologue_pending";
        public const string FlagDefeatPending = "defeat_pending";
        /// <summary>Final boss defeated.</summary>
        public const string FlagCleared = "cleared";
        public const string FlagEndingSeen = "ending_seen";
        public const int ProloguePages = 8;
        public const int EndingPages = 12;
        /// <summary>Floors per zone ("chapter" in older code): 1-1..1-3 is zone 1. Floor 3 of a zone holds its boss.</summary>
        public const int FloorsPerChapter = 3;
        /// <summary>Story zones before the postgame (zone 13 = 붉은 게이트, open after the ending).</summary>
        public const int MainChapters = 12;
        /// <summary>Guild licence grade from the zone bosses beaten (E at the start, S after the final boss).</summary>
        public static string GuildRank(GameState state)
        {
            int beaten = 0;
            for (int i = 1; i <= MainChapters; i++) if (state.Flags.Contains(BossFlag(i))) beaten++;
            if (state.Flags.Contains(FlagCleared)) return "S";
            return beaten >= 10 ? "A" : beaten >= 8 ? "B" : beaten >= 6 ? "C" : beaten >= 3 ? "D" : "E";
        }
        /// <summary>One-shot notice shown in town after the ending: the trial corridor is open.</summary>
        public const string FlagPostgameNotice = "postgame_notice_seen";

        /// <summary>Chapter (1-based) of a floor index.</summary>
        public static int ChapterOf(int floorIndex) => Math.Max(0, floorIndex) / FloorsPerChapter + 1;

        /// <summary>"boss_N_cleared" for chapter N = 1..7.</summary>
        public static string BossFlag(int chapter) => "boss_" + chapter + "_cleared";

        /// <summary>Story chapter the party is in: 1 + bosses beaten in order, 7 after the ending.</summary>
        public static int StoryChapter(GameState state)
        {
            if (state.Flags.Contains(FlagCleared)) return MainChapters + 1;
            int chapter = 1;
            while (chapter <= MainChapters && state.Flags.Contains(BossFlag(chapter))) chapter++;
            return Math.Min(chapter, MainChapters);
        }

        /// <summary>
        /// Town greeting text key for an NPC: "npc_&lt;id&gt;_greeting_&lt;chapter&gt;" when authored for the current
        /// story chapter (or the latest earlier one), else the base "npc_&lt;id&gt;_greeting".
        /// </summary>
        public static string GreetingKey(GameDB db, GameState state, string npcId)
        {
            for (int chapter = StoryChapter(state); chapter >= 1; chapter--)
            {
                string key = "npc_" + npcId + "_greeting_" + chapter;
                if (db.Text.ContainsKey(key)) return key;
            }
            return "npc_" + npcId + "_greeting";
        }

        /// <summary>Elder's talk pages: greeting, one line per chapter boss beaten, the postgame line after the ending.</summary>
        public static List<string> ElderLineKeys(GameDB db, GameState state)
        {
            var keys = new List<string> { GreetingKey(db, state, "elder") };
            for (int i = 1; i <= MainChapters; i++)
                if (state.Flags.Contains(BossFlag(i)) && db.Text.ContainsKey("elder_" + i)) keys.Add("elder_" + i);
            if (state.Flags.Contains(FlagCleared) && db.Text.ContainsKey("postgame_unlocked")) keys.Add("postgame_unlocked");
            return keys;
        }
        /// <summary>"tip_&lt;key&gt;"; also the tip's text key.</summary>
        public static string TipFlag(string key) => "tip_" + key;

        /// <summary>Prologue page text keys prologue_1..8 (title key "prologue_title").</summary>
        public static IReadOnlyList<string> PrologueKeys => Keys("prologue", ProloguePages);
        /// <summary>Ending page text keys ending_1..12 (title key "ending_title").</summary>
        public static IReadOnlyList<string> EndingKeys => Keys("ending", EndingPages);

        /// <summary>Where a continued save resumes (defeat screen, prologue, unseen ending, town or dungeon).</summary>
        public static ResumeRoute ResumeRouteOf(GameState state)
        {
            if (state.Flags.Contains(FlagDefeatPending)) return ResumeRoute.GameOver;
            if (state.Flags.Contains(FlagProloguePending)) return ResumeRoute.Prologue;
            if (state.Flags.Contains(FlagCleared) && !state.Flags.Contains(FlagEndingSeen)) return ResumeRoute.Ending;
            return state.Location == GameLocation.Town ? ResumeRoute.Town : ResumeRoute.Dungeon;
        }

        /// <summary>Prologue finished: go to town (carried TP cleared).</summary>
        public static void CompletePrologue(GameState state)
        {
            state.Flags.Remove(FlagProloguePending);
            state.Location = GameLocation.Town;
            state.ClearCarriedTp();
            state.RefillSprings();
        }

        /// <summary>Marks a one-shot tip shown. True only the first time (then show text key <c>tip_&lt;key&gt;</c>).</summary>
        public static bool TryTip(GameState state, string key) => state.Flags.Add(TipFlag(key));

        /// <summary>
        /// Arrival in town (sets location). Returns notices to show in order: the first_town tip once, then the
        /// elder's line once after each of the chapter 1-5 bosses (elder_1..5), then the trial-corridor notice once
        /// after the ending. The Unity layer autosaves after.
        /// </summary>
        public static List<StoryNotice> EnterTown(GameState state) => EnterTown(null, state);

        /// <summary>
        /// As <see cref="EnterTown(GameState)"/>, plus (with a database) the hunters who join now that their zone boss has
        /// fallen (<see cref="HunterRoster.SyncStoryJoins"/>): one notice each, after the guild master's lines.
        /// </summary>
        public static List<StoryNotice> EnterTown(GameDB db, GameState state)
        {
            state.Location = GameLocation.Town;
            state.ClearCarriedTp();
            state.RefillSprings();
            var output = new List<StoryNotice>();
            if (TryTip(state, "first_town")) output.Add(new StoryNotice { TitleKey = "tip_title", TextKey = TipFlag("first_town") });
            var joins = db == null ? new List<StoryNotice>() : JoinNotices(db, state);
            // Chapter 6's closing words are the ending itself; the trial corridor notice follows the ending once.
            for (int i = 1; i < MainChapters; i++)
                if (state.Flags.Contains(BossFlag(i)) && state.Flags.Add("elder_" + i + "_seen"))
                    output.Add(new StoryNotice { TitleKey = "elder", TextKey = "elder_" + i });
            if (state.Flags.Contains(FlagEndingSeen) && state.Flags.Add(FlagPostgameNotice))
                output.Add(new StoryNotice { TitleKey = "elder", TextKey = "postgame_unlocked" });
            output.AddRange(joins);
            return output;
        }

        static List<StoryNotice> JoinNotices(GameDB db, GameState state)
        {
            var output = new List<StoryNotice>();
            foreach (var hero in HunterRoster.SyncStoryJoins(db, state))
            {
                var def = db.Heroes[hero.Id];
                string where = state.InParty(hero.Id) ? "파티에 합류했습니다." : "대기 헌터로 등록됐습니다. 헌터 관리에서 편성할 수 있어요.";
                string job = PartyStats.JobName(db, hero);
                output.Add(new StoryNotice
                {
                    TitleKey = "hunter_join_title",
                    HeroId = hero.Id,
                    Text = $"{def.Rank}급 {job} {def.DisplayName} (Lv.{hero.Level})\n\n\"{def.Line}\"\n\n{where}",
                });
            }
            return output;
        }

        /// <summary>Chapter intro (biome_0..6) on the first visit of a chapter's first floor, else null.</summary>
        public static StoryNotice BiomeIntro(GameState state, int floorIndex)
        {
            int biome = floorIndex / FloorsPerChapter;
            if (floorIndex % FloorsPerChapter != 0 || !state.Flags.Add("biome_" + biome + "_seen")) return null;
            return new StoryNotice { TitleKey = "lore", TextKey = "biome_" + biome };
        }

        /// <summary>
        /// "마을에서 다시 시작" after a defeat: loses 50 % gold (normal/hard, rounded down; easy loses none),
        /// then a free inn rest (full recovery, FOEs respawn, carried TP cleared) in town. Returns the gold lost (text key "recovered").
        /// No-op returning 0 when no defeat is pending.
        /// </summary>
        public static int RecoverFromDefeat(GameDB db, GameState state)
        {
            if (!state.Flags.Remove(FlagDefeatPending)) return 0;
            int lost = (int)Math.Floor(state.Gold * (double)TownServices.DefeatGoldLoss(state.Difficulty));
            state.Gold -= lost;
            TownServices.RestAtInn(db, state, free: true);
            state.Location = GameLocation.Town;
            state.ClearCarriedTp();
            state.RefillSprings();
            return lost;
        }

        /// <summary>Ending and credits watched: the next continue goes to town (carried TP cleared).</summary>
        public static void MarkEndingSeen(GameState state)
        {
            state.Flags.Add(FlagCleared);
            state.Flags.Add(FlagEndingSeen);
            state.Location = GameLocation.Town;
            state.ClearCarriedTp();
            state.RefillSprings();
        }

        /// <summary>
        /// Uses a consumable from the camp menu (HEALING / MP_RESTORE / CURE / REVIVE on <paramref name="heroId"/>
        /// or every hero for all_allies items; ESCAPE_DUNGEON in the dungeon; SEED on <paramref name="heroId"/>, permanent,
        /// failing with reason_seed_cap at the cap). Nothing is consumed without effect.
        /// </summary>
        public static FieldItemResult UseFieldItem(GameDB db, GameState state, string itemId, string heroId, bool inDungeon)
        {
            if (state.PendingBattle != null || state.Flags.Contains(FlagDefeatPending)) return Fail("item_unavailable");
            if (!db.Items.TryGetValue(itemId, out var item) || state.ItemCount(itemId) <= 0) return Fail("item_missing");
            if (item.ItemType == ItemType.EscapeDungeon)
            {
                if (!inDungeon) return Fail("no_effect");
                state.RemoveItem(itemId, 1);
                return new FieldItemResult { Success = true, TextKey = "used", ReturnToTown = true };
            }
            if (item.ItemType == ItemType.Seed)
            {
                var eater = state.Hero(heroId);
                if (eater == null) return Fail("invalid_target");
                if (PartyStats.ApplySeed(db, eater, item) <= 0) return Fail("reason_seed_cap");
                state.RemoveItem(itemId, 1);
                QuestLog.Refresh(db, state);
                return new FieldItemResult { Success = true, TextKey = "used" };
            }
            if (item.ItemType != ItemType.Healing && item.ItemType != ItemType.MpRestore && item.ItemType != ItemType.Cure && item.ItemType != ItemType.Revive)
                return Fail("item_unavailable");
            var targets = new List<HeroState>();
            foreach (var hero in state.Party) if (item.Target == "all_allies" || hero.Id == heroId) targets.Add(hero);
            if (targets.Count == 0) return Fail("invalid_target");
            bool changed = false;
            foreach (var hero in targets)
            {
                var stats = PartyStats.EffectiveStats(db, hero);
                switch (item.ItemType)
                {
                    case ItemType.Healing:
                        if (hero.Hp > 0 && hero.Hp < stats.MaxHp)
                        {
                            hero.Hp = Math.Min(stats.MaxHp, hero.Hp + (item.Value > 0 ? item.Value : item.HealAmount));
                            changed = true;
                        }
                        if (hero.Hp > 0 && item.MpAmount > 0 && hero.Mp < stats.MaxMp)
                        {
                            hero.Mp = Math.Min(stats.MaxMp, hero.Mp + item.MpAmount);
                            changed = true;
                        }
                        break;
                    case ItemType.MpRestore:
                        if (hero.Hp > 0 && hero.Mp < stats.MaxMp && item.Value > 0)
                        {
                            hero.Mp = Math.Min(stats.MaxMp, hero.Mp + item.Value);
                            changed = true;
                        }
                        break;
                    case ItemType.Revive:
                        if (hero.Hp == 0 && item.Power > 0f)
                        {
                            hero.Hp = Math.Max(1, Math.Min(stats.MaxHp, PartyStats.RoundI(stats.MaxHp * PartyStats.D(item.Power))));
                            hero.Statuses.Clear();
                            changed = true;
                        }
                        break;
                    case ItemType.Cure:
                        if (hero.Hp <= 0) break;
                        foreach (string statusId in new List<string>(hero.Statuses.Keys))
                        {
                            bool removes = !string.IsNullOrEmpty(item.StatusId)
                                ? statusId == item.StatusId
                                : db.Statuses.TryGetValue(statusId, out var status) && !IsBeneficial(status.EffectType);
                            if (!removes) continue;
                            hero.Statuses.Remove(statusId);
                            changed = true;
                        }
                        break;
                }
            }
            if (!changed) return Fail("no_effect");
            state.RemoveItem(itemId, 1);
            QuestLog.Refresh(db, state);
            return new FieldItemResult { Success = true, TextKey = "used" };
        }

        /// <summary>Buff-type statuses (kept by cures).</summary>
        public static bool IsBeneficial(StatusEffectType type)
        {
            switch (type)
            {
                case StatusEffectType.AttackUp:
                case StatusEffectType.DefenseUp:
                case StatusEffectType.Regen:
                case StatusEffectType.Barrier:
                case StatusEffectType.MagicUp:
                case StatusEffectType.SpeedUp:
                case StatusEffectType.ManaShield:
                case StatusEffectType.Invincible:
                case StatusEffectType.Provoke:
                    return true;
                default:
                    return false;
            }
        }

        static FieldItemResult Fail(string key) => new FieldItemResult { Success = false, TextKey = key };

        static string[] Keys(string prefix, int count)
        {
            var keys = new string[count];
            for (int i = 0; i < count; i++) keys[i] = prefix + "_" + (i + 1);
            return keys;
        }
    }
}
