// External QA code evaluated by Unity Pipeline (unity command eval_file); never included in the shipped player.
// Floor 1 end-to-end playthrough in PLAY MODE: title -> new game -> town -> 1-1 -> 1-2 -> 1-3 boss -> post-boss text.
// Driven through the game's own UI delegates and step API (GameApp.MoveDungeon / TurnDungeon, UIButton.Click, menu rows).
// Output: docs/verification/floor1/*.png, floor1_report.json, progress.log. Saves go to a temp sandbox, never to the real campaign.
// NOTE: boss_defeat shots here are keyed to the engine outcome, which precedes the replay; Tools/Floor1BattleChecks.eval.cs measures boss death and unit offsets correctly.
// Rerun: Tools/run_floor1.ps1   (or: editor_play, then `unity command eval_file --file Tools/Floor1Playthrough.eval.cs`).

Exception Stuck(string m) => new InvalidOperationException("STUCK: " + m);

var BF = System.Reflection.BindingFlags.Instance | System.Reflection.BindingFlags.Public | System.Reflection.BindingFlags.NonPublic;
var projectRoot = System.IO.Directory.GetParent(Application.dataPath).FullName;
var outDir = System.IO.Path.Combine(projectRoot, "docs", "verification", "floor1");
System.IO.Directory.CreateDirectory(outDir);
var clock = System.Diagnostics.Stopwatch.StartNew();
var startedUtc = DateTime.UtcNow;
double Now() => clock.Elapsed.TotalSeconds;
var progressPath = System.IO.Path.Combine(outDir, "progress.log");
System.IO.File.WriteAllText(progressPath, "");
string action = "init";
void P(string msg) { System.IO.File.AppendAllText(progressPath, "[" + Now().ToString("F1") + "s] " + msg + "\n"); }

Abyss.Runtime.GameApp app = null;
var logs = new Dictionary<string, Dictionary<string, object>>();
var shots = new List<Dictionary<string, object>>();
var events = new List<Dictionary<string, object>>();
var floorsLog = new List<Dictionary<string, object>>();
var battlesLog = new List<Dictionary<string, object>>();
var retries = new List<Dictionary<string, object>>();
var checks = new List<Dictionary<string, object>>();
string failure = null;
bool bossWon = false, postBossShot = false, bossDone = false;
int totalSteps = 0, maxFloorReached = 0;
const double TotalBudgetSeconds = 85 * 60;

// ---- console capture (errors, exceptions, warnings, asserts), deduplicated with counts -------------------------------
string FirstFrame(string stack)
{
    if (string.IsNullOrEmpty(stack)) return "";
    var m = System.Text.RegularExpressions.Regex.Match(stack, @"\(at (Assets/_Game/[^)]+)\)");
    if (m.Success) return m.Groups[1].Value;
    m = System.Text.RegularExpressions.Regex.Match(stack, @"^\s*(\S.*)$", System.Text.RegularExpressions.RegexOptions.Multiline);
    return m.Success ? m.Groups[1].Value.Trim() : "";
}
Application.LogCallback logHandler = (cond, stack, type) =>
{
    if (type == LogType.Log) return;
    string first = (cond ?? "").Split('\n')[0];
    string frame = FirstFrame(stack);
    string key = type + "|" + System.Text.RegularExpressions.Regex.Replace(first, @"\d+", "#") + "|" + frame;
    if (!logs.TryGetValue(key, out var rec))
        logs[key] = rec = new Dictionary<string, object> { ["type"] = type.ToString(), ["count"] = 0, ["message"] = cond, ["firstAction"] = action, ["firstGameFrame"] = frame, ["stack"] = stack, ["firstAtSeconds"] = Math.Round(Now(), 1) };
    rec["count"] = (int)rec["count"] + 1;
};

// ---- frame / time helpers ---------------------------------------------------------------------------------------------
async System.Threading.Tasks.Task Frames(int count)
{
    int end = Time.frameCount + count;
    double deadline = Now() + 30;
    while (Time.frameCount < end) { if (Now() > deadline) throw new TimeoutException("Game frames stopped advancing"); await System.Threading.Tasks.Task.Yield(); }
}
async System.Threading.Tasks.Task Wait(double seconds)
{
    double end = Now() + seconds;
    while (Now() < end) await System.Threading.Tasks.Task.Yield();
}
void Resize(int width, int height)
{
    var assembly = typeof(UnityEditor.Editor).Assembly;
    var sizesType = assembly.GetType("UnityEditor.GameViewSizes");
    var singleton = typeof(UnityEditor.ScriptableSingleton<>).MakeGenericType(sizesType);
    var sizes = singleton.GetProperty("instance").GetValue(null);
    var getGroup = sizesType.GetMethod("GetGroup");
    var group = getGroup.Invoke(sizes, new[] { Enum.Parse(getGroup.GetParameters()[0].ParameterType, "Standalone") });
    var sizeType = assembly.GetType("UnityEditor.GameViewSize");
    var kind = assembly.GetType("UnityEditor.GameViewSizeType");
    var ctor = sizeType.GetConstructor(BF, null, new[] { kind, typeof(int), typeof(int), typeof(string) }, null);
    var size = ctor.Invoke(new object[] { Enum.ToObject(kind, 1), width, height, "Floor1 QA" });
    int index = (int)group.GetType().GetMethod("GetTotalCount").Invoke(group, null);
    group.GetType().GetMethod("AddCustomSize").Invoke(group, new[] { size });
    var viewType = assembly.GetType("UnityEditor.GameView");
    var window = UnityEditor.EditorWindow.GetWindow(viewType);
    viewType.GetProperty("selectedSizeIndex", BF).SetValue(window, index);
}
void Note(string kind, string text)
{
    if (text != null && text.Length > 240) text = text.Substring(0, 240);
    if (events.Count > 0 && (string)events[events.Count - 1]["kind"] == kind && (string)events[events.Count - 1]["text"] == text) return;
    events.Add(new Dictionary<string, object> { ["t"] = Math.Round(Now(), 1), ["kind"] = kind, ["text"] = text, ["floor"] = app?.State?.FloorIndex });
    P(kind + ": " + text);
}
void ShotNow(string name)
{
    ScreenCapture.CaptureScreenshot(System.IO.Path.Combine(outDir, name + ".png"));
    shots.RemoveAll(s => (string)s["name"] == name);
    shots.Add(new Dictionary<string, object> { ["name"] = name, ["file"] = "docs/verification/floor1/" + name + ".png", ["t"] = Math.Round(Now(), 1), ["screen"] = app?.Screen.ToString(), ["floorIndex"] = app?.State?.FloorIndex });
}
async System.Threading.Tasks.Task Shot(string name)
{
    ShotNow(name);
    await Frames(4);
    P("shot " + name);
}

// ---- state inspection ---------------------------------------------------------------------------------------------------
Abyss.UI.UIRoot R() => Abyss.UI.UIRoot.Instance;
var fWorld = typeof(Abyss.Runtime.GameApp).GetField("dungeonWorld", BF);
bool WorldBusy()
{
    var w = fWorld.GetValue(app) as UnityEngine.Object;
    if (w == null) return true;
    return (bool)w.GetType().GetProperty("Busy").GetValue(w);
}
string StateName()
{
    var r = R();
    bool uiOpen = r.Screens.Count > 0 || r.Modals.Count > 0;
    if (app.Screen == Abyss.Runtime.GameScreen.Title)
        return (r.Modals.Count > 0 || (r.Screens.Top != null && !(r.Screens.Top is Abyss.UI.GameTitleScreen))) ? "ui" : "title";
    if (app.Screen == Abyss.Runtime.GameScreen.Ending) return "ending";
    // The pending-defeat flag is set when the battle resolves, before the result dashboard; the defeat menu is the real "defeat" state.
    if (app.State != null && app.State.Flags.Contains(Abyss.Logic.Game.GameFlow.FlagDefeatPending)
        && (app.Screen != Abyss.Runtime.GameScreen.Battle || r.Screens.Top is Abyss.UI.GameMenuScreen)) return "defeat";
    if (app.Screen == Abyss.Runtime.GameScreen.Battle) return "battle";
    if (app.Screen == Abyss.Runtime.GameScreen.Story || uiOpen) return "ui";
    if (app.UI.BlocksWorldInput) return "busy";
    if (app.Screen == Abyss.Runtime.GameScreen.Dungeon) return app.Dungeon != null && app.Dungeon.CanAct && !WorldBusy() ? "dungeon-ready" : "busy";
    if (app.Screen == Abyss.Runtime.GameScreen.Town) return "town-ready";
    return "busy";
}
List<object> PartySnapshot() => app.State.Party.Select(h =>
{
    var stats = Abyss.Logic.Game.PartyStats.EffectiveStats(app.DB, h);
    return (object)new { id = h.Id, level = h.Level, hp = h.Hp, maxHp = stats.MaxHp, mp = h.Mp };
}).ToList();
double HpRatio()
{
    double lo = 1;
    foreach (var h in app.State.Party)
    {
        int max = Math.Max(1, Abyss.Logic.Game.PartyStats.EffectiveStats(app.DB, h).MaxHp);
        lo = Math.Min(lo, (double)h.Hp / max);
    }
    return lo;
}
Abyss.UI.UIButton FindButton(Func<string, bool> match)
{
    foreach (var b in UnityEngine.Object.FindObjectsByType<Abyss.UI.UIButton>(FindObjectsSortMode.None))
        if (b.isActiveAndEnabled && b.Label != null && match(b.Label.text)) return b;
    return null;
}
bool PickMenu(Func<string, bool> match)
{
    var menu = R().Screens.Top as Abyss.UI.GameMenuScreen;
    if (menu == null) return false;
    var rows = (List<Abyss.UI.UIListItem>)typeof(Abyss.UI.GameMenuScreen).GetField("rows", BF).GetValue(menu);
    foreach (var row in rows)
        if (row.Enabled && match(row.Label)) { (row.Tag as Action)?.Invoke(); return true; }
    return false;
}

// ---- battle supervision -------------------------------------------------------------------------------------------------
Abyss.Runtime.Battle.BattleView curBattle = null;
Abyss.Logic.Battle.BattleEngine curEngine = null;
Dictionary<string, object> curRec = null;
double battleStart = 0, battleEndedAt = -1, lastBurst = 0, lastResultClick = 0;
bool ended = false, bossStartShot = false, bossDefeatShot = false;
int battleCount = 0, bestFx = 0;
bool firstBattleDone = false;
// ---- per-battle presentation monitors (impact frames, unit offsets from Home) ----
var fUnits = typeof(Abyss.Runtime.Battle.BattleView).GetField("_units", BF);
var fHit = typeof(Abyss.Runtime.Battle.BattleView).GetField("_hitstop", BF);
int monsterShots = 0, heroDashShots = 0;
bool prevHs = false; HashSet<string> prevVfx = new HashSet<string>(); double lastImpactShot = -10;
var offMax = new Dictionary<string, float>(); var offSince = new Dictionary<string, double>(); var offLong = new Dictionary<string, double>();
var impacts = new List<Dictionary<string, object>>();
bool bossShotA = false, bossShotB = false, bossShotC = false, bossD2 = false, bossD3 = false, endOffsetsDone = false;
Dictionary<string, object> endOffsets = null;
float Flat(Vector3 a, Vector3 b) { a.y = 0; b.y = 0; return Vector3.Distance(a, b); }
Dictionary<string, Abyss.Runtime.Battle.BattleDisplayUnit> UnitsOf(Abyss.Runtime.Battle.BattleView b) => (Dictionary<string, Abyss.Runtime.Battle.BattleDisplayUnit>)fUnits.GetValue(b);
object BossModelState(Abyss.Runtime.Battle.BattleView b)
{
    foreach (var u in UnitsOf(b).Values)
        if (u.Boss && u.Model != null)
            return new { id = u.Id, alive = u.Alive, active = u.Model.gameObject.activeInHierarchy, scale = u.Model.transform.lossyScale.x, offsetFromHome = Math.Round(Flat(u.Model.transform.position, u.Home), 2), y = Math.Round(u.Model.transform.position.y, 2),
                renderers = u.Model.GetComponentsInChildren<Renderer>().Count(r => r.enabled) };
    return null;
}
void MonitorBattle(Abyss.Runtime.Battle.BattleView b, double age)
{
    var units = UnitsOf(b);
    bool hs = (bool)fHit.GetValue(b);
    var active = new HashSet<string>();
    var vfxRoot = GameObject.Find("Abyss VFX");
    if (vfxRoot != null) foreach (Transform c in vfxRoot.transform) if (c.gameObject.activeSelf) active.Add(c.name);
    var fresh = active.Where(n => !prevVfx.Contains(n)).ToList();
    bool trigger = (hs && !prevHs) || fresh.Count > 0;
    prevHs = hs; prevVfx = active;
    Abyss.Runtime.Battle.BattleDisplayUnit mover = null; float md = 0;
    foreach (var u in units.Values)
    {
        if (u.Model == null || !u.Alive) { offSince.Remove(u.Id); continue; }
        float d = Flat(u.Model.transform.position, u.Home);
        if (d > md) { md = d; mover = u; }
        if (age < 6) continue;
        if (!offMax.TryGetValue(u.Id, out var m) || d > m) offMax[u.Id] = d;
        if (d > 0.25f)
        {
            if (!offSince.ContainsKey(u.Id)) offSince[u.Id] = Now();
            double dur = Now() - offSince[u.Id];
            if (!offLong.TryGetValue(u.Id, out var l) || dur > l) offLong[u.Id] = dur;
        }
        else offSince.Remove(u.Id);
    }
    if (!trigger || mover == null) return;
    if (impacts.Count < 300) impacts.Add(new Dictionary<string, object> { ["t"] = Math.Round(Now(), 1), ["battle"] = battleCount, ["mover"] = mover.Id, ["side"] = mover.Side.ToString(), ["dist"] = Math.Round(md, 2), ["hitstopEdge"] = hs, ["newVfx"] = fresh });
    if (md < 0.8f || Now() - lastImpactShot < 0.5) return;
    if (mover.Side == Abyss.Logic.Battle.BattleSide.Enemy && monsterShots < 5)
    {
        monsterShots++; lastImpactShot = Now();
        ShotNow("10_monster_impact_" + monsterShots + "_" + mover.DefId);
        P("monster impact shot " + monsterShots + " mover=" + mover.DefId + " vfx=" + string.Join(",", fresh) + " dist=" + Math.Round(md, 2));
    }
    else if (mover.Side == Abyss.Logic.Battle.BattleSide.Party && heroDashShots < 4)
    {
        heroDashShots++; lastImpactShot = Now();
        ShotNow("11_hero_dash_contact_" + heroDashShots + "_" + mover.Id);
        P("hero dash shot " + heroDashShots + " mover=" + mover.Id + " vfx=" + string.Join(",", fresh) + " dist=" + Math.Round(md, 2));
    }
}
void BeginBattleRecord(Abyss.Runtime.Battle.BattleView b)
{
    curBattle = b; curEngine = b.Engine; battleStart = Now(); battleEndedAt = -1; ended = false; bossStartShot = false; bossDefeatShot = false;
    var req = app.State.PendingBattle;
    bool boss = req != null && req.Kind == Abyss.Logic.BattleKind.Boss;
    battleCount++;
    curRec = new Dictionary<string, object>
    {
        ["index"] = battleCount, ["kind"] = req?.Kind.ToString(), ["floor"] = req?.FloorId, ["group"] = req?.EnemyGroup,
        ["cell"] = req == null ? null : req.Cell.ToString(), ["startT"] = Math.Round(Now(), 1), ["partyBefore"] = PartySnapshot(),
    };
    // First battle and the boss run at 1x so the establishing shot and the full reward dashboard are exercised; the rest at 2x.
    // Slow (0.5x) while impact/dash captures are still missing so 10 fps sampling catches contact frames; boss at 1x; the rest at 2x.
    app.Preferences.BattleSpeed = boss ? 1f : ((monsterShots < 5 || heroDashShots < 4) && battleCount <= 5) ? 0.5f : 2f;
    prevHs = false; prevVfx = new HashSet<string>(); offMax.Clear(); offSince.Clear(); offLong.Clear();
    bossShotA = bossShotB = bossShotC = bossD2 = bossD3 = endOffsetsDone = false; endOffsets = null;
    app.Preferences.AutoBattle = true;
    if (!b.Auto) b.SetAuto(true);
    P("battle " + battleCount + " begins: " + req?.Kind + " " + string.Join("+", req?.EnemyGroup ?? new List<string>()));
}
void FinalizeBattle()
{
    if (curRec == null) return;
    var outcome = curEngine?.Outcome;
    curRec["result"] = outcome == null ? "unknown" : outcome.Result.ToString();
    curRec["rounds"] = curEngine?.Round;
    curRec["seconds"] = Math.Round(Now() - battleStart, 1);
    curRec["partyAfter"] = PartySnapshot();
    curRec["speed"] = app.Preferences.BattleSpeed;
    curRec["maxOffsetFromHome"] = offMax.ToDictionary(k => k.Key, k => Math.Round(k.Value, 2));
    curRec["longestOffsetSeconds"] = offLong.ToDictionary(k => k.Key, k => Math.Round(k.Value, 1));
    curRec["endOffsets"] = endOffsets;
    curRec["exp"] = outcome?.Experience; curRec["gold"] = outcome?.Gold;
    if (outcome != null && outcome.Result == Abyss.Logic.BattleResult.Victory && (string)curRec["kind"] == "Boss") bossWon = true;
    battlesLog.Add(curRec);
    P("battle " + battleCount + " done: " + curRec["result"] + " rounds=" + curRec["rounds"] + " in " + curRec["seconds"] + "s");
    if (!firstBattleDone) { firstBattleDone = true; }
    curBattle = null; curEngine = null; curRec = null;
}
async System.Threading.Tasks.Task BattleTick()
{
    var b = app.Battle;
    if (b == null) return;
    if (curBattle == null && app.State.PendingBattle == null) return;   // stale view after a defeat
    if (!ReferenceEquals(b, curBattle)) { if (curBattle != null) FinalizeBattle(); BeginBattleRecord(b); }
    double age = Now() - battleStart;
    bool boss = (string)curRec["kind"] == "Boss";
    if (age > 600) { ShotNow("stuck_battle"); await Frames(4); throw Stuck("Battle " + battleCount + " ran longer than 10 minutes (state " + curEngine?.State + ", round " + curEngine?.Round + ")"); }
    if (!b.Auto && !curBattle.Playing) b.SetAuto(true);
    // first battle: keep the frame with the most live particle systems as the "mid-action" capture
    if (battleCount == 1 && !firstBattleDone && Now() - lastBurst > 0.12 && curEngine.Round >= 1)
    {
        lastBurst = Now();
        int fx = UnityEngine.Object.FindObjectsByType<ParticleSystem>(FindObjectsSortMode.None).Count(p => p.isPlaying && p.particleCount > 0);
        if (fx > bestFx && fx >= 3) { bestFx = fx; ShotNow("04_first_battle_mid_action"); }
    }
    MonitorBattle(b, age);
    if (boss && !bossShotA && age > 0.5) { bossShotA = true; await Shot("06a_boss_intro_banner"); }
    if (boss && !bossShotB && age > 1.6) { bossShotB = true; await Shot("06_boss_battle_start"); }
    if (boss && !bossShotC && age > 3.2) { bossShotC = true; await Shot("06c_boss_battle_start_3s"); }
    if (curEngine.Outcome != null && curEngine.Outcome.Result != Abyss.Logic.BattleResult.None)
    {
        if (battleEndedAt < 0) battleEndedAt = Now();
        bool bossVictory = boss && curEngine.Outcome.Result == Abyss.Logic.BattleResult.Victory;
        if (!endOffsetsDone && Now() - battleEndedAt > 0.9 && (FindButton(t => t.Contains("모험 계속")) != null || UnityEngine.Object.FindObjectsByType<UnityEngine.UI.Button>(FindObjectsSortMode.None).Any(x => x.isActiveAndEnabled && x.gameObject.name == "Fast battle result")))   // replay finished = result UI visible (the engine outcome exists long before the replay ends)
        {
            endOffsetsDone = true;
            endOffsets = new Dictionary<string, object>();
            foreach (var u in UnitsOf(b).Values) if (u.Model != null && u.Alive) endOffsets[u.Id] = Math.Round(Flat(u.Model.transform.position, u.Home), 2);
        }
        if (bossVictory && !bossDefeatShot && Now() - battleEndedAt > 0.9) { bossDefeatShot = true; await Shot("07_boss_defeat"); curRec["bossAt0.9s"] = BossModelState(b); }
        if (bossVictory && !bossD2 && Now() - battleEndedAt > 2.0) { bossD2 = true; await Shot("07b_boss_defeat_2s"); curRec["bossAt2s"] = BossModelState(b); }
        if (bossVictory && !bossD3 && Now() - battleEndedAt > 3.2) { bossD3 = true; await Shot("07c_boss_defeat_3s"); curRec["bossAt3.2s"] = BossModelState(b); }
        if (Now() - battleEndedAt > (bossVictory ? 3.6 : 1.2) && Now() - lastResultClick > 0.5)
        {
            lastResultClick = Now();
            var ok = FindButton(t => t.Contains("모험 계속"));
            if (ok != null) ok.Click();
            else
            {
                foreach (var btn in UnityEngine.Object.FindObjectsByType<UnityEngine.UI.Button>(FindObjectsSortMode.None))
                    if (btn.isActiveAndEnabled && btn.gameObject.name == "Fast battle result") { btn.onClick.Invoke(); break; }
            }
        }
    }
}

// ---- UI dismissal (stories, loot, confirms, choice events) ----------------------------------------------------------------
async System.Threading.Tasks.Task<bool> DismissUi()
{
    var r = R();
    var modal = r.Modals.Top;
    if (modal != null)
    {
        var btns = modal.GetComponentsInChildren<Abyss.UI.UIButton>(false).Where(b => b.isActiveAndEnabled && b.Label != null).ToList();
        string desc = modal.GetType().Name + (modal is Abyss.UI.UIModal um && um.Message != null ? ": " + um.Message.text.Replace("\n", " ") : "");
        bool choice = app.Dungeon != null && app.Dungeon.PendingChoice != null;
        Note(choice ? "choice-event" : "modal", desc + (btns.Count > 0 ? "  [buttons: " + string.Join(" | ", btns.Select(b => b.Label.text)) + "]" : ""));
        if (btns.Count == 0) { modal.Close(); return true; }
        var pick = btns[0];                                      // accept / confirm / OK
        if (modal is Abyss.UI.UILootPopup) pick = btns.FirstOrDefault(b => b.Label.text.Contains("확인")) ?? btns[0];
        pick.Click();
        return true;
    }
    var screen = r.Screens.Top;
    if (screen is Abyss.UI.GameStoryScreen story)
    {
        Note("story", story.Title + " | " + (story.Pages != null && story.Pages.Count > 0 ? story.Pages[0].Replace("\n", " ") : ""));
        if (bossWon && !postBossShot)
        {
            postBossShot = true;
            await Wait(2.8);
            await Shot("08_post_boss_text");
        }
        var next = screen.GetComponentsInChildren<Abyss.UI.UIButton>(false)
            .FirstOrDefault(b => b.isActiveAndEnabled && b.Label != null && (b.Label.text.Contains("다음") || b.Label.text.Contains("계속") || b.Label.text.Contains("마치기")));
        next?.Click();
        return true;
    }
    return false;
}

// ---- settle: wait until the game is in a stable state we can act on, pumping UI and battles on the way ---------------------
async System.Threading.Tasks.Task<string> Settle(string[] expect, double timeout = 90)
{
    double lastActivity = Now(), stableSince = -1;
    string last = null;
    while (true)
    {
        if (Now() > TotalBudgetSeconds) throw Stuck("Total time budget exceeded");
        string s = StateName();
        if (s != last) { last = s; lastActivity = Now(); }
        if (s != "battle" && curBattle != null) { FinalizeBattle(); lastActivity = Now(); }
        if (s == "battle") { await BattleTick(); lastActivity = Now(); stableSince = -1; await System.Threading.Tasks.Task.Yield(); continue; }
        if (s == "ui")
        {
            if (await DismissUi()) { lastActivity = Now(); stableSince = -1; await Wait(0.3); continue; }
            if (Now() - lastActivity > 6)
            {
                var top = R().Screens.Top;
                Note("unexpected-ui", top == null ? "null" : top.GetType().Name);
                top?.Close(); lastActivity = Now();
            }
        }
        bool want = expect.Contains(s) || s == "defeat" || s == "ending";
        if (want)
        {
            if (stableSince < 0) stableSince = Now();
            else if (Now() - stableSince >= 0.4) return s;
        }
        else stableSince = -1;
        if (s == "title" && !expect.Contains("title")) throw Stuck("Unexpectedly back on the title screen");
        if (Now() - lastActivity > timeout)
        {
            ShotNow("stuck_" + s); await Frames(4);
            var top = R().Screens.Top; var mtop = R().Modals.Top;
            throw Stuck("No progress for " + timeout + "s in state '" + s + "' (screen " + app.Screen + ", ui top " + (top?.GetType().Name ?? "-") + ", modal " + (mtop?.GetType().Name ?? "-") + ", paused " + app.Paused + ")");
        }
        await System.Threading.Tasks.Task.Yield();
    }
}

// ---- route planning ---------------------------------------------------------------------------------------------------
Abyss.Logic.Dungeon.GridPos[] Dirs = { new Abyss.Logic.Dungeon.GridPos(0, -1), new Abyss.Logic.Dungeon.GridPos(1, 0), new Abyss.Logic.Dungeon.GridPos(0, 1), new Abyss.Logic.Dungeon.GridPos(-1, 0) };   // N E S W == Facing values
int Cost(Abyss.Logic.Dungeon.DungeonGrid g, Abyss.Logic.Dungeon.GridPos p, int keys)
{
    char c = g.Cell(p);
    if (c == '#') return -1;
    if (c == 'L' && !g.Progress.OpenedDoors.Contains(p)) return keys > 0 ? 4 : -1;
    int cost = 1;
    if (c == 'X') cost += 25;
    if (c == 'E' && !g.IsEventSpent(p)) cost += 4;
    return cost;
}
(Dictionary<Abyss.Logic.Dungeon.GridPos, int> dist, Dictionary<Abyss.Logic.Dungeon.GridPos, Abyss.Logic.Dungeon.GridPos> prev) Dijkstra(Abyss.Logic.Dungeon.DungeonGrid g, Abyss.Logic.Dungeon.GridPos from, int keys)
{
    var dist = new Dictionary<Abyss.Logic.Dungeon.GridPos, int> { [from] = 0 };
    var prev = new Dictionary<Abyss.Logic.Dungeon.GridPos, Abyss.Logic.Dungeon.GridPos>();
    var open = new List<Abyss.Logic.Dungeon.GridPos> { from };
    while (open.Count > 0)
    {
        int bi = 0;
        for (int i = 1; i < open.Count; i++) if (dist[open[i]] < dist[open[bi]]) bi = i;
        var cur = open[bi]; open.RemoveAt(bi);
        char cc = g.Cell(cur);
        if (cur != from && (cc == '<' || cc == '>' || cc == 'B')) continue;      // terminal: stepping there changes floor / starts the boss
        foreach (var d in Dirs)
        {
            var n = cur + d;
            int step = Cost(g, n, keys);
            if (step < 0) continue;
            int nd = dist[cur] + step;
            if (!dist.TryGetValue(n, out int old) || nd < old) { dist[n] = nd; prev[n] = cur; if (!open.Contains(n)) open.Add(n); }
        }
    }
    return (dist, prev);
}
List<Abyss.Logic.Dungeon.GridPos> PathTo(Dictionary<Abyss.Logic.Dungeon.GridPos, Abyss.Logic.Dungeon.GridPos> prev, Abyss.Logic.Dungeon.GridPos from, Abyss.Logic.Dungeon.GridPos goal)
{
    var path = new List<Abyss.Logic.Dungeon.GridPos>();
    var cur = goal;
    while (cur != from) { path.Add(cur); if (!prev.TryGetValue(cur, out cur)) return null; }
    path.Reverse();
    return path;
}

// ---- one walking step (turn + forward) ----------------------------------------------------------------------------------
Abyss.Logic.Dungeon.GridPos lastPos = Abyss.Logic.Dungeon.GridPos.None; int lastKeys = -1, lastFacing = -1, noProgress = 0, lastFloor = -1;
async System.Threading.Tasks.Task StepOnce()
{
    var st = app.State; var run = app.Dungeon; var g = run.Grid;
    int f = st.FloorIndex; var pos = st.Position;
    bool bossFloor = g.Floor.BossGroup != null && g.Floor.BossGroup.Count > 0;
    var bossCell = g.FindCell('B');
    if (bossFloor && bossCell != Abyss.Logic.Dungeon.GridPos.None && g.Progress.ClearedBattles.Contains(bossCell)) { bossDone = true; return; }
    int keys = g.Progress.Keys;
    var (dist, prev) = Dijkstra(g, pos, keys);
    Abyss.Logic.Dungeon.GridPos goal = Abyss.Logic.Dungeon.GridPos.None; string why = "exit";
    var cands = new List<(Abyss.Logic.Dungeon.GridPos p, string w)>();
    foreach (var p in g.FindCells('T')) if (!g.Progress.OpenedChests.Contains(p)) cands.Add((p, "treasure"));
    foreach (var p in g.FindCells('K')) if (!g.Progress.TakenKeys.Contains(p)) cands.Add((p, "key"));
    foreach (var p in g.FindCells('W')) if (!st.WarpsUnlocked.Contains(f)) cands.Add((p, "warp"));
    foreach (var p in g.FindCells('E')) if (!g.IsEventSpent(p)) cands.Add((p, "event"));
    if (HpRatio() < 0.6) foreach (var p in g.FindCells('H')) if (!g.Progress.SpentSprings.Contains(p)) cands.Add((p, "spring"));
    int best = int.MaxValue;
    foreach (var c in cands)
    {
        if (!dist.TryGetValue(c.p, out int d)) continue;
        int effective = c.w == "spring" ? d - 1000 : d;
        if (d > 70 && c.w != "spring") continue;
        if (effective < best) { best = effective; goal = c.p; why = c.w; }
    }
    if (goal == Abyss.Logic.Dungeon.GridPos.None)
    {
        goal = bossFloor ? bossCell : g.FindCell('>');
        why = bossFloor ? "boss" : "exit";
        if (goal == Abyss.Logic.Dungeon.GridPos.None || !dist.ContainsKey(goal)) throw Stuck("No route to " + why + " on " + g.Floor.FloorLabel + " from " + pos);
    }
    var path = PathTo(prev, pos, goal);
    if (path == null || path.Count == 0) throw Stuck("Empty route to " + goal + " (" + why + ") from " + pos);
    var next = path[0];
    var delta = next - pos;
    int dirIndex = Array.FindIndex(Dirs, d => d == delta);
    action = g.Floor.FloorLabel + " step " + pos + "->" + next + " (" + why + " " + goal + ")";
    if ((int)st.Facing != dirIndex)
    {
        int q = (dirIndex - (int)st.Facing + 4) % 4; if (q == 3) q = -1;
        app.TurnDungeon(q);
        await Frames(2);
        var ts = await Settle(new[] { "dungeon-ready" }, 40);
        if (ts != "dungeon-ready") return;
    }
    app.MoveDungeon(Abyss.Logic.Dungeon.RelativeMove.Forward);
    totalSteps++;
    if (totalSteps % 25 == 0) P("steps=" + totalSteps + " floor=" + g.Floor.FloorLabel + " pos=" + app.State.Position + " hpMin=" + Math.Round(HpRatio(), 2));
    await Frames(2);
    await Settle(new[] { "dungeon-ready", "town-ready" }, 90);
    // progress watchdog
    var now = app.State;
    bool changed = now.Position != lastPos || now.FloorIndex != lastFloor || app.Dungeon?.Grid.Progress.Keys != lastKeys || (int)now.Facing != lastFacing;
    if (changed) noProgress = 0; else if (++noProgress >= 6) throw Stuck("Walking made no progress for 6 steps at " + pos + " on " + g.Floor.FloorLabel + " heading " + next);
    lastPos = now.Position; lastFloor = now.FloorIndex; lastKeys = app.Dungeon?.Grid.Progress.Keys ?? -1; lastFacing = (int)now.Facing;
}

// ---- town / retry helpers -----------------------------------------------------------------------------------------------
async System.Threading.Tasks.Task TitleToTown()
{
    action = "title";
    if (app.Screen != Abyss.Runtime.GameScreen.Title) app.ShowTitle();
    await Wait(3.5);
    await Shot("01_title");
    action = "new game";
    var title = R().Screens.Top as Abyss.UI.GameTitleScreen;
    if (title == null) throw Stuck("Title screen not on top: " + R().Screens.Top?.GetType().Name);
    title.NewGame();
    await Wait(0.8);
    string normal = app.DB.T("difficulty_normal");
    if (!PickMenu(l => l.Contains(normal))) throw Stuck("Difficulty row '" + normal + "' not found");
    var s = await Settle(new[] { "town-ready" }, 120);
    await Wait(2.5);
    await Shot("02_town");
    Note("town", "Reached town. Party " + string.Join(",", app.State.Party.Select(h => h.Id + " L" + h.Level)));
}
async System.Threading.Tasks.Task Depart(int floorIndex)
{
    action = "depart to floor index " + floorIndex;
    app.OpenTownService("gate");
    await Wait(0.8);
    string label = app.DB.Floors[floorIndex].FloorLabel;
    if (!PickMenu(l => l.StartsWith(label))) throw Stuck("Depart row " + label + " not found");
    await Settle(new[] { "dungeon-ready" }, 120);
}
var defeatsAtLevel = new Dictionary<int, int>();
async System.Threading.Tasks.Task Recover(string reason)
{
    action = "defeat recovery";
    ShotNow("defeat_" + (retries.Count + 1)); await Frames(4);
    string recover = app.DB.T("recover");
    if (!PickMenu(l => l.Contains(recover))) throw Stuck("Defeat menu row '" + recover + "' not found");
    await Settle(new[] { "town-ready" }, 120);
    if (retries.Count >= 10) throw Stuck("Party lost " + (retries.Count + 1) + " times; giving up (" + reason + ")");
    // Policy: first defeat at a given party level -> retry at the SAME level with a full heal (what a player does after reloading);
    // a second defeat at that same level -> +2 levels, noted. Nothing is boosted silently.
    int level = app.State.Party.Max(h => h.Level);
    defeatsAtLevel[level] = defeatsAtLevel.TryGetValue(level, out var n0) ? n0 + 1 : 1;
    bool boost = defeatsAtLevel[level] >= 2;
    foreach (var h in app.State.Party) { if (boost) { h.Level = Math.Min(Abyss.Logic.Game.GameState.LevelCap, h.Level + 2); h.Xp = 0; } h.Hp = -1; h.Mp = -1; h.Tp = 0; h.Statuses.Clear(); }
    app.State.Repair(app.DB);
    retries.Add(new Dictionary<string, object> { ["t"] = Math.Round(Now(), 1), ["reason"] = reason, ["levelBeforeRetry"] = level, ["levelBoost"] = boost ? 2 : 0, ["partyAfter"] = PartySnapshot(), ["note"] = boost ? "second defeat at this level: +2 levels and full heal, then retried" : "first defeat at this level: full heal at the SAME level, then retried" });
    P("retry " + retries.Count + " after defeat: " + reason);
    // depart from the deepest available gate at or below the floor we reached
    var options = Abyss.Logic.Game.TownServices.DepartureFloors(app.DB, app.State);
    int target = options.Where(i => i <= maxFloorReached).DefaultIfEmpty(0).Max();
    await Depart(target);
}
void RecordFloorArrival()
{
    var g = app.Dungeon.Grid;
    var rec = new Dictionary<string, object>
    {
        ["label"] = g.Floor.FloorLabel, ["id"] = g.Floor.Id, ["arrivedT"] = Math.Round(Now(), 1), ["party"] = PartySnapshot(), ["stepsSoFar"] = totalSteps, ["battlesSoFar"] = battleCount,
        ["position"] = app.State.Position.ToString(),
    };
    floorsLog.Add(rec);
    P("arrived " + g.Floor.FloorLabel + " at " + app.State.Position + " steps=" + totalSteps);
}

// ---- main ---------------------------------------------------------------------------------------------------------------
async System.Threading.Tasks.Task Run()
{
    string saveBackup = null;
    try
    {
        Application.runInBackground = true;
        app = Abyss.Runtime.GameApp.Instance;
        if (app == null) throw new Exception("Play mode game missing (enter play mode first)");
        Application.logMessageReceived += logHandler;
        // never touch the real campaign: redirect saves + preferences to a sandbox in the temp folder
        saveBackup = System.IO.Path.Combine(System.IO.Path.GetTempPath(), "floor1-qa-save");
        if (System.IO.Directory.Exists(saveBackup)) System.IO.Directory.Delete(saveBackup, true);
        typeof(Abyss.Runtime.GameApp).GetField("saveDirectory", BF).SetValue(app, saveBackup);
        typeof(Abyss.Runtime.GameApp).GetField("<Saves>k__BackingField", BF).SetValue(app, new Abyss.Runtime.Persistence.SaveRepository(saveBackup, app.DB));
        app.Preferences.AutoBattle = true; app.Preferences.BattleSpeed = 1f;
        Resize(1280, 720);
        await Frames(20);
        checks.Add(new Dictionary<string, object> { ["name"] = "game view 1280x720", ["passed"] = Screen.width == 1280 && Screen.height == 720, ["detail"] = Screen.width + "x" + Screen.height });

        await TitleToTown();
        await Depart(0);
        string loggedFloorId = null;
        int floorSteps = 0;
        while (!bossDone)
        {
            if (Now() > TotalBudgetSeconds) throw Stuck("Total time budget exceeded");
            var s = await Settle(new[] { "dungeon-ready", "town-ready" }, 120);
            if (s == "ending") { Note("ending", "ending reached"); break; }
            if (s == "defeat")
            {
                await Recover("defeat on floor index " + app.State.FloorIndex + " vs " + (battlesLog.Count > 0 ? string.Join("+", (List<string>)battlesLog.Last()["group"] ?? new List<string>()) : "?"));
                loggedFloorId = null; floorSteps = 0;
                continue;
            }
            if (s == "town-ready") { await Depart(Abyss.Logic.Game.TownServices.DepartureFloors(app.DB, app.State).Where(i => i <= maxFloorReached).DefaultIfEmpty(0).Max()); loggedFloorId = null; continue; }
            if (loggedFloorId != app.Dungeon.Grid.Floor.Id)
            {
                loggedFloorId = app.Dungeon.Grid.Floor.Id; floorSteps = 0;
                maxFloorReached = Math.Max(maxFloorReached, app.State.FloorIndex);
                RecordFloorArrival();
                await Wait(0.8); await Shot("03_floor_" + app.Dungeon.Grid.Floor.FloorLabel + "_start");
            }
            if (++floorSteps > 700) throw Stuck("More than 700 steps on " + app.Dungeon.Grid.Floor.FloorLabel);
            await StepOnce();
        }
        if (bossDone)
        {
            var s = await Settle(new[] { "dungeon-ready", "town-ready", "defeat", "ending" }, 60);
            await Wait(0.8);
            await Shot("09_after_boss_dungeon");
            Note("done", "Boss cleared and post-boss text dismissed; stopping on " + app.Dungeon?.Grid.Floor.FloorLabel);
            floorsLog.Add(new Dictionary<string, object> { ["label"] = "final", ["id"] = "final", ["party"] = PartySnapshot(), ["stepsSoFar"] = totalSteps, ["battlesSoFar"] = battleCount });
        }
    }
    catch (Exception e)
    {
        failure = e.GetType().Name + ": " + e.Message;
        P("FAILED: " + e);
        try { ShotNow("zz_failure"); await Frames(4); } catch { }
        logs["EXC|" + e.Message] = new Dictionary<string, object> { ["type"] = "ScriptException", ["count"] = 1, ["message"] = e.ToString(), ["firstAction"] = action, ["firstGameFrame"] = "Tools/Floor1Playthrough.eval.cs", ["stack"] = e.StackTrace, ["firstAtSeconds"] = Math.Round(Now(), 1) };
    }
    finally
    {
        Application.logMessageReceived -= logHandler;
        try
        {
            var report = new Dictionary<string, object>
            {
                ["status"] = failure == null && bossDone ? "complete" : "failed",
                ["failure"] = failure, ["lastAction"] = action,
                ["unity"] = Application.unityVersion, ["startedUtc"] = startedUtc.ToString("o"), ["elapsedSeconds"] = Math.Round(Now(), 1),
                ["bossDefeated"] = bossWon, ["floorsReached"] = maxFloorReached + 1, ["totalSteps"] = totalSteps,
                ["impacts"] = impacts, ["floors"] = floorsLog, ["battles"] = battlesLog, ["retries"] = retries, ["events"] = events, ["screenshots"] = shots, ["checks"] = checks,
                ["consoleIssues"] = logs.Values.OrderBy(l => (double)l["firstAtSeconds"]).ToList(),
            };
            System.IO.File.WriteAllText(System.IO.Path.Combine(outDir, "floor1_report.json"), Newtonsoft.Json.JsonConvert.SerializeObject(report, Newtonsoft.Json.Formatting.Indented));
            P("report written: " + report["status"]);
        }
        catch (Exception e2) { P("report write failed: " + e2); }
        System.IO.File.WriteAllText(System.IO.Path.Combine(outDir, "DONE"), failure == null && bossDone ? "complete" : "failed");
    }
}
if (System.IO.File.Exists(System.IO.Path.Combine(outDir, "DONE"))) System.IO.File.Delete(System.IO.Path.Combine(outDir, "DONE"));
_ = Run();
return "floor1 playthrough started; watch docs/verification/floor1/progress.log, finished when docs/verification/floor1/DONE exists";
