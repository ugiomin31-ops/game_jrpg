// External QA code evaluated by Unity Pipeline (unity command eval_file); never included in the shipped player.
// Focused battle presentation checks in PLAY MODE using the review entry point (GameApp.BeginReview), L13 party, AUTO battle:
//   (2) every unit's distance from its Home position once the replay has finished (result dashboard visible) and how long units stay displaced,
//   (3) boss death: screenshots 0.3 / 1 / 2 / 3 s after the boss display unit actually dies (not after the engine's early outcome), with model state.
// Output: docs/verification/floor1/battle_checks/*.png and battle_checks.json (+ progress_checks.log). Finished when battle_checks/DONE exists.
// Run: unity command editor_play, then `unity command --timeout 120 eval_file --file Tools/Floor1BattleChecks.eval.cs`.
var BF = System.Reflection.BindingFlags.Instance | System.Reflection.BindingFlags.Public | System.Reflection.BindingFlags.NonPublic;
var outDir = System.IO.Path.Combine(System.IO.Directory.GetParent(Application.dataPath).FullName, "docs", "verification", "floor1", "battle_checks");
System.IO.Directory.CreateDirectory(outDir);
var clock = System.Diagnostics.Stopwatch.StartNew();
double Now() => clock.Elapsed.TotalSeconds;
System.IO.File.WriteAllText(System.IO.Path.Combine(outDir, "progress_checks.log"), "");
void P(string m) { System.IO.File.AppendAllText(System.IO.Path.Combine(outDir, "progress_checks.log"), "[" + Now().ToString("F1") + "s] " + m + "\n"); }
Abyss.Runtime.GameApp app = null;
var logs = new Dictionary<string, Dictionary<string, object>>();
var results = new List<Dictionary<string, object>>();
string failure = null;
Application.LogCallback handler = (cond, stack, type) =>
{
    if (type == LogType.Log) return;
    string key = type + "|" + System.Text.RegularExpressions.Regex.Replace((cond ?? "").Split('\n')[0], @"\d+", "#");
    if (!logs.TryGetValue(key, out var r)) logs[key] = r = new Dictionary<string, object> { ["type"] = type.ToString(), ["count"] = 0, ["message"] = cond, ["stack"] = stack };
    r["count"] = (int)r["count"] + 1;
};
async System.Threading.Tasks.Task Frames(int n) { int end = Time.frameCount + n; double dl = Now() + 30; while (Time.frameCount < end) { if (Now() > dl) throw new TimeoutException("frames stopped"); await System.Threading.Tasks.Task.Yield(); } }
async System.Threading.Tasks.Task Wait(double s) { double end = Now() + s; while (Now() < end) await System.Threading.Tasks.Task.Yield(); }
async System.Threading.Tasks.Task Shot(string name) { ScreenCapture.CaptureScreenshot(System.IO.Path.Combine(outDir, name + ".png")); await Frames(4); P("shot " + name); }
float Flat(Vector3 a, Vector3 b) { a.y = 0; b.y = 0; return Vector3.Distance(a, b); }
var fUnits = typeof(Abyss.Runtime.Battle.BattleView).GetField("_units", BF);
Dictionary<string, Abyss.Runtime.Battle.BattleDisplayUnit> UnitsOf(Abyss.Runtime.Battle.BattleView b) => (Dictionary<string, Abyss.Runtime.Battle.BattleDisplayUnit>)fUnits.GetValue(b);
Abyss.UI.UIButton FindButton(Func<string, bool> match)
{
    foreach (var b in UnityEngine.Object.FindObjectsByType<Abyss.UI.UIButton>(FindObjectsSortMode.None))
        if (b.isActiveAndEnabled && b.Label != null && match(b.Label.text)) return b;
    return null;
}
UnityEngine.UI.Button FastToast()
{
    foreach (var btn in UnityEngine.Object.FindObjectsByType<UnityEngine.UI.Button>(FindObjectsSortMode.None))
        if (btn.isActiveAndEnabled && btn.gameObject.name == "Fast battle result") return btn;
    return null;
}
// Result UI objects that already existed when the battle began are stale (previous battle) and must not count as "replay finished".
var staleIds = new HashSet<int>();
Abyss.UI.UIButton ResultButton() { foreach (var b in UnityEngine.Object.FindObjectsByType<Abyss.UI.UIButton>(FindObjectsSortMode.None)) if (b.isActiveAndEnabled && b.Label != null && b.Label.text.Contains("모험 계속") && !staleIds.Contains(b.GetInstanceID())) return b; return null; }
UnityEngine.UI.Button FreshToast() { var t = FastToast(); return t != null && !staleIds.Contains(t.GetInstanceID()) ? t : null; }
bool ReplayDone() => app.Battle != null && app.Battle.Engine.Outcome != null && (ResultButton() != null || FreshToast() != null);
void ClickResult() { var ok = ResultButton(); if (ok != null) ok.Click(); else FreshToast()?.onClick.Invoke(); }
void DismissOnce()
{
    var r = Abyss.UI.UIRoot.Instance;
    var modal = r.Modals.Top;
    if (modal != null) { modal.GetComponentsInChildren<Abyss.UI.UIButton>(false).FirstOrDefault(b => b.isActiveAndEnabled)?.Click(); return; }
    if (r.Screens.Top is Abyss.UI.GameStoryScreen s)
        s.GetComponentsInChildren<Abyss.UI.UIButton>(false).FirstOrDefault(b => b.isActiveAndEnabled && b.Label != null && (b.Label.text.Contains("다음") || b.Label.text.Contains("계속")))?.Click();
}
object BossState(Abyss.Runtime.Battle.BattleView b)
{
    foreach (var u in UnitsOf(b).Values)
        if (u.Boss && u.Model != null)
        {
            var rs = u.Model.GetComponentsInChildren<Renderer>();
            return new { alive = u.Alive, hp = u.Hp, active = u.Model.gameObject.activeInHierarchy, scale = Math.Round(u.Model.transform.lossyScale.x, 2), enabledRenderers = rs.Count(r => r.enabled), y = Math.Round(u.Model.transform.position.y, 2), offsetFromHome = Math.Round(Flat(u.Model.transform.position, u.Home), 2) };
        }
    return null;
}

async System.Threading.Tasks.Task RunBattle(string label, List<string> group, Abyss.Logic.BattleKind kind, float speed)
{
    var state = app.State;
    foreach (var h in state.Party) { h.Hp = -1; h.Mp = -1; h.Tp = 0; h.Statuses.Clear(); }
    state.Repair(app.DB);
    var start = typeof(Abyss.Logic.Dungeon.DungeonRun).GetMethod("StartBattle", BF);
    var req = (Abyss.Logic.Dungeon.DungeonBattleRequest)start.Invoke(app.Dungeon, new object[] { kind, new List<string>(group), state.Position, state.Position, "", 1f });
    app.Preferences.AutoBattle = true; app.Preferences.BattleSpeed = speed;
    staleIds.Clear();
    foreach (var b0 in UnityEngine.Object.FindObjectsByType<Abyss.UI.UIButton>(FindObjectsSortMode.None)) staleIds.Add(b0.GetInstanceID());
    foreach (var b0 in UnityEngine.Object.FindObjectsByType<UnityEngine.UI.Button>(FindObjectsSortMode.None)) staleIds.Add(b0.GetInstanceID());
    app.BeginBattle(req.Setup);
    double t0 = Now();
    var rec = new Dictionary<string, object> { ["label"] = label, ["kind"] = kind.ToString(), ["group"] = group, ["speed"] = speed };
    var displaced = new Dictionary<string, double>(); var displacedSince = new Dictionary<string, double>(); var maxOff = new Dictionary<string, float>();
    double doneAt = -1, deadAt = -1; bool sampled = false; var bossShots = new HashSet<string>();
    var bossTimeline = new Dictionary<string, object>();
    while (true)
    {
        if (Now() - t0 > 900) throw new InvalidOperationException("battle " + label + " exceeded 15 min");
        var b = app.Battle;
        if (app.Screen != Abyss.Runtime.GameScreen.Battle || b == null) break;
        var units = UnitsOf(b);
        Abyss.Runtime.Battle.BattleDisplayUnit mover = null; float md = 0;
        foreach (var u in units.Values) if (u.Model != null && u.Alive) { float d = Flat(u.Model.transform.position, u.Home); if (d > md) { md = d; mover = u; } }
        foreach (var u in units.Values)
        {
            if (u.Model == null || !u.Alive) { displacedSince.Remove(u.Id); continue; }
            float d = Flat(u.Model.transform.position, u.Home);
            if (!maxOff.TryGetValue(u.Id, out var m) || d > m) maxOff[u.Id] = d;
            // a displaced unit that is NOT the current mover is a recoil / knock-back / unfinished return
            bool other = d > 0.25f && !ReferenceEquals(u, mover);
            if (other) { if (!displacedSince.ContainsKey(u.Id)) displacedSince[u.Id] = Now(); double dur = (Now() - displacedSince[u.Id]) * speed; if (!displaced.TryGetValue(u.Id, out var l) || dur > l) displaced[u.Id] = dur; }
            else displacedSince.Remove(u.Id);
        }
        if (kind == Abyss.Logic.BattleKind.Boss && b.Engine.Outcome != null)
        {
            var bu = units.Values.FirstOrDefault(u => u.Boss);
            if (deadAt < 0 && bu != null && !bu.Alive) { deadAt = Now(); P("boss display unit died after " + Math.Round(Now() - t0, 1) + "s"); }
            if (deadAt >= 0)
                foreach (var (name, at) in new[] { ("0_3s", .3), ("1s", 1.0), ("2s", 2.0), ("3s", 3.0) })
                    if (!bossShots.Contains(name) && Now() - deadAt >= at) { bossShots.Add(name); await Shot("bossdeath_" + name); bossTimeline["after_" + name] = BossState(b); }
        }
        if (doneAt < 0 && ReplayDone()) { doneAt = Now(); rec["replayDoneAtSeconds"] = Math.Round(doneAt - t0, 1); }
        if (doneAt >= 0 && !sampled && Now() - doneAt > 0.3)
        {
            sampled = true;
            var end = new Dictionary<string, object>();
            foreach (var u in units.Values) if (u.Model != null) end[u.Id] = new { alive = u.Alive, offset = Math.Round(Flat(u.Model.transform.position, u.Home), 2), yawDeg = Math.Round(Quaternion.Angle(u.Model.transform.rotation, u.Facing), 1) };
            rec["unitsAtReplayEnd"] = end;
            if (kind == Abyss.Logic.BattleKind.Boss) { rec["bossAtReplayEnd"] = BossState(b); await Shot("bossdeath_result_dashboard"); }
        }
        bool bossGate = kind != Abyss.Logic.BattleKind.Boss || deadAt < 0 || Now() - deadAt > 3.4;
        if (doneAt >= 0 && sampled && bossGate && Now() - doneAt > 1.0) ClickResult();
        await System.Threading.Tasks.Task.Yield();
    }
    rec["seconds"] = Math.Round(Now() - t0, 1);
    rec["maxOffsetFromHome"] = maxOff.ToDictionary(k => k.Key, k => Math.Round(k.Value, 2));
    rec["longestNonMoverDisplacedGameSeconds"] = displaced.ToDictionary(k => k.Key, k => Math.Round(k.Value, 1));
    rec["bossDeadAfterSeconds"] = deadAt < 0 ? (double?)null : Math.Round(deadAt - t0, 1);
    rec["bossTimeline"] = bossTimeline;
    results.Add(rec);
    P("battle " + label + " done in " + rec["seconds"]);
    // clear whatever follows (post-boss text, loot) until the dungeon is actionable again
    double d0 = Now();
    while (Now() - d0 < 40)
    {
        DismissOnce();
        if (app.Screen == Abyss.Runtime.GameScreen.Dungeon && app.Dungeon != null && app.Dungeon.CanAct && !app.UI.BlocksWorldInput) break;
        await Wait(0.4);
    }
}

async System.Threading.Tasks.Task Run()
{
    try
    {
        Application.runInBackground = true;
        app = Abyss.Runtime.GameApp.Instance;
        if (app == null) throw new Exception("Play mode game missing");
        Application.logMessageReceived += handler;
        var db = app.DB;
        var state = Abyss.Logic.Game.GameState.NewGame(db, Abyss.Logic.Difficulty.Normal);
        state.Flags.Remove(Abyss.Logic.Game.GameFlow.FlagProloguePending);
        foreach (string tip in new[] { "first_battle", "first_foe", "first_tp_full", "first_trap", "first_town" }) state.Flags.Add(Abyss.Logic.Game.GameFlow.TipFlag(tip));
        foreach (var h in state.Party) { h.Level = 13; h.Xp = 0; h.Hp = -1; h.Mp = -1; }
        state.AddItem("healing_potion", 5);
        state.FloorIndex = 2; state.Location = Abyss.Logic.Game.GameLocation.Dungeon; state.DeepestFloor = 2;
        state.Repair(db);
        app.BeginReview(state, 2);           // switches to the review-campaign save directory: the real campaign is untouched
        await Wait(3);
        var groups = new List<(string, List<string>)>
        {
            ("sewer_rat+slime", new List<string> { "sewer_rat", "slime" }),
            ("tunnel_bat x2+bee", new List<string> { "tunnel_bat", "tunnel_bat", "killer_bee" }),
            ("rabbit+bat+bat", new List<string> { "horned_rabbit", "bat", "bat" }),
            ("elite_bat+bat", new List<string> { "elite_bat", "bat" }),
        };
        foreach (var (label, group) in groups) await RunBattle(label, group, Abyss.Logic.BattleKind.Random, 2f);
        await RunBattle("BOSS subway_bat_lord", new List<string> { "subway_bat_lord" }, Abyss.Logic.BattleKind.Boss, 1f);
    }
    catch (Exception e) { failure = e.GetType().Name + ": " + e.Message; P("FAILED " + e); }
    finally
    {
        Application.logMessageReceived -= handler;
        System.IO.File.WriteAllText(System.IO.Path.Combine(outDir, "battle_checks.json"), Newtonsoft.Json.JsonConvert.SerializeObject(new { status = failure == null ? "complete" : "failed", failure, battles = results, consoleIssues = logs.Values.ToList() }, Newtonsoft.Json.Formatting.Indented));
        System.IO.File.WriteAllText(System.IO.Path.Combine(outDir, "DONE"), failure == null ? "complete" : "failed");
    }
}
if (System.IO.File.Exists(System.IO.Path.Combine(outDir, "DONE"))) System.IO.File.Delete(System.IO.Path.Combine(outDir, "DONE"));
_ = Run();
return "battle checks started; finished when docs/verification/floor1/battle_checks/DONE exists";
