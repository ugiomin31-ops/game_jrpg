using System;
using System.Collections;
using System.Collections.Generic;
using System.Reflection;
using Abyss.Logic;
using Abyss.Logic.Battle;
using Abyss.Logic.Dungeon;
using Abyss.Logic.Game;
using UnityEngine;
using UnityEngine.UI;

namespace Abyss.Runtime
{
    /// <summary>
    /// Visual review of battles in a player build, without playing up to them. Off unless the page URL (WebGL) or the command
    /// line carries <c>review=battle</c>, e.g.
    /// <c>index.html?review=battle&amp;party=h_bora,h_hana,h_iseul,h_eunbi&amp;level=30&amp;floor=12&amp;groups=ice_wolf+orc;slime&amp;speed=1</c>.
    /// It builds that party at that level (their authored starter gear, every skill of the level), stands it on the floor and
    /// runs each enemy group (';' between battles, '+' inside a group) in AUTO battle, acknowledging each result and looping.
    /// Progress goes to the browser console as "REVIEW ..." lines (the player log elsewhere).
    /// </summary>
    public sealed class ReviewBoot : MonoBehaviour
    {
        Dictionary<string, string> _args;

        [RuntimeInitializeOnLoadMethod(RuntimeInitializeLoadType.AfterSceneLoad)]
        static void Boot()
        {
            var args = Parse();
            if (args == null || !args.TryGetValue("review", out var mode) || mode != "battle") return;
            var go = new GameObject("Review boot");
            DontDestroyOnLoad(go);
            go.AddComponent<ReviewBoot>()._args = args;
        }

        static Dictionary<string, string> Parse()
        {
            string query = null;
            string url = Application.absoluteURL;
            if (!string.IsNullOrEmpty(url) && url.IndexOf('?') >= 0) query = url.Substring(url.IndexOf('?') + 1);
            var cmd = Environment.GetCommandLineArgs();
            for (int i = 0; i + 1 < cmd.Length; i++) if (cmd[i] == "-review") query = cmd[i + 1];
            if (string.IsNullOrEmpty(query)) return null;
            var map = new Dictionary<string, string>();
            foreach (string pair in query.Split('&'))
            {
                int eq = pair.IndexOf('=');
                if (eq > 0) map[Uri.UnescapeDataString(pair.Substring(0, eq))] = Uri.UnescapeDataString(pair.Substring(eq + 1));
            }
            return map;
        }

        string Arg(string key, string fallback) => _args.TryGetValue(key, out var v) && !string.IsNullOrEmpty(v) ? v : fallback;

        IEnumerator Start()
        {
            while (GameApp.Instance == null || GameApp.Instance.DB == null) yield return null;
            yield return null;
            var app = GameApp.Instance;
            var db = app.DB;
            int level = Mathf.Clamp(int.Parse(Arg("level", "20")), 1, GameState.LevelCap);
            int floor = Mathf.Clamp(int.Parse(Arg("floor", "0")), 0, db.Floors.Count - 1);
            var state = GameState.NewGame(db, Difficulty.Normal);
            state.Flags.Remove(GameFlow.FlagProloguePending);
            foreach (string tip in new[] { "first_battle", "first_foe", "first_tp_full", "first_trap", "first_town" }) state.Flags.Add(GameFlow.TipFlag(tip));
            var party = Arg("party", string.Join(",", db.HeroOrder)).Split(',');
            state.Party.Clear(); state.Reserve.Clear();
            foreach (string id in party) HunterRoster.Recruit(db, state, id.Trim());
            foreach (var hero in state.AllHunters()) { hero.Level = level; hero.Hp = -1; hero.Mp = -1; }
            state.AddItem("healing_potion", 5);
            state.FloorIndex = floor; state.Location = GameLocation.Dungeon;
            state.DeepestFloor = Math.Max(state.DeepestFloor, floor);
            state.Repair(db);
            app.Preferences.AutoBattle = true;
            app.Preferences.BattleSpeed = ParseSpeed(Arg("speed", "1"));
            app.BeginReview(state, floor);
            var groups = new List<List<string>>();
            foreach (string group in Arg("groups", "slime").Split(';'))
                if (group.Trim().Length > 0) groups.Add(new List<string>(group.Trim().Split('+')));
            var start = typeof(DungeonRun).GetMethod("StartBattle", BindingFlags.Instance | BindingFlags.NonPublic);
            int round = 0;
            for (int loop = 0; loop < int.Parse(Arg("loops", "99")); loop++)
                foreach (var group in groups)
                {
                    yield return new WaitForSecondsRealtime(.5f);
                    // Every battle starts fresh: full vitals, no carried TP or statuses.
                    foreach (var hero in state.Party) { hero.Hp = -1; hero.Mp = -1; hero.Tp = 0; hero.Statuses.Clear(); }
                    state.Repair(db);
                    var request = (DungeonBattleRequest)start.Invoke(app.Dungeon,
                        new object[] { BattleKind.Random, new List<string>(group), state.Position, state.Position, "", 1f });
                    Debug.Log("REVIEW battle " + (++round) + " " + string.Join("+", group));
                    app.BeginBattle(request.Setup);
                    yield return new WaitForSecondsRealtime(1f);
                    // Monitor every launched battle (the last one too) until it is over and acknowledged; abort on defeat or route exit.
                    while (app.Screen != GameScreen.Dungeon)
                    {
                        if (PartyDefeated(state) || app.Screen == GameScreen.Town || app.Screen == GameScreen.Title)
                        {
                            Debug.LogError("REVIEW aborted: " + (PartyDefeated(state) ? "the party was defeated" : "left the dungeon (" + app.Screen + ")") + " during battle " + round + ".");
                            yield break;
                        }
                        ClickContinue();
                        yield return new WaitForSecondsRealtime(.5f);
                    }
                }
        }

        static bool PartyDefeated(GameState state)
        {
            if (state.Party.Count == 0) return false;
            foreach (var hero in state.Party) if (hero.Hp > 0) return false;
            return true;
        }

        /// <summary>Invariant-culture speed: unparsable, NaN, infinite or &lt;= 0 gives 1; otherwise clamped to [1, 2].</summary>
        static float ParseSpeed(string text)
        {
            if (!float.TryParse(text, System.Globalization.NumberStyles.Float, System.Globalization.CultureInfo.InvariantCulture, out float speed)
                || float.IsNaN(speed) || float.IsInfinity(speed) || speed <= 0f) return 1f;
            return Mathf.Clamp(speed, 1f, 2f);
        }

        /// <summary>Acknowledges a battle result / reward window (its "continue" button) so the loop can go on.</summary>
        static void ClickContinue()
        {
            foreach (var button in FindObjectsByType<Button>(FindObjectsSortMode.None))
            {
                if (!button.isActiveAndEnabled || !button.interactable) continue;
                var label = button.GetComponentInChildren<TMPro.TMP_Text>();
                if (label != null && (label.text.Contains("계속") || label.text.Contains("확인"))) { button.onClick.Invoke(); return; }
            }
        }
    }
}
