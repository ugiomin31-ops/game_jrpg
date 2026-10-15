// External Unity Pipeline eval; NOT a runtime/player source file.
// Requested worker route: gpt-6-astra / high / priority (not a runtime routing receipt).
// Parent only, in a fresh Play session with GameApp initialized, no ReviewBoot or other QA running:
// unity command eval_file --file Tools/TripoBattleAcceptance.eval.cs
// Returns immediately; poll the returned evidence directory's DONE (<=25s per poll).
// Uses GameState.NewGame/HunterRoster.Recruit, GameApp.BeginReview/BeginBattle,
// DungeonRun.StartBattle (reflection), BattleView._units, IModelAnimator.CurrentClip/
// NormalizedTime, SkinnedMeshRenderer.BakeMesh, ScreenCapture.CaptureScreenshot.
// Does not Continue/Read player saves. Existing GameApp startup predates this eval.
// BeginReview resets persistence; redirect again synchronously before yielding.
// QA persistence intentionally stays isolated after completion. Stop Play before normal play.
// This is one manual-input battle, no campaign, attacks, auto battle or paid asset work.
// Screenshot heuristics are not visual approval: parent must inspect both PNGs and player log.
var root = System.IO.Path.GetFullPath(".git/codex-runs/20261015-165918-tripo-motion");
var savePath = System.IO.Path.Combine(root, "qa-save");
var outDir = System.IO.Path.Combine(root, "battle-acceptance-" + System.DateTime.UtcNow.ToString("yyyyMMdd-HHmmss-fff"));
var flags = System.Reflection.BindingFlags.Instance | System.Reflection.BindingFlags.Public | System.Reflection.BindingFlags.NonPublic;
var checks = new System.Collections.Generic.List<object>();
var logs = new System.Collections.Generic.List<object>();
bool failed = false;
string failure = null;
void Check(string name, bool passed, object detail = null) { checks.Add(new { name, passed, detail }); if (!passed) failed = true; }
async System.Threading.Tasks.Task Until(System.Func<bool> ready, string label) {
    var deadline = System.DateTime.UtcNow.AddSeconds(25);
    while (!ready()) {
        if (!Application.isPlaying || System.DateTime.UtcNow >= deadline) throw new System.TimeoutException(label);
        await System.Threading.Tasks.Task.Delay(16); // capture Unity synchronization context, never Task.Run
    }
}
async System.Threading.Tasks.Task Frames(int count) {
    int end = Time.frameCount + count;
    await Until(() => Time.frameCount >= end, "Frames stopped advancing");
}
var app = Abyss.Runtime.GameApp.Instance;
if (!Application.isPlaying || app == null || app.DB == null || app.Preferences == null)
    return "NOT STARTED: fresh Play session with initialized GameApp required";
if (UnityEngine.Object.FindAnyObjectByType<Abyss.Runtime.ReviewBoot>() != null || app.Screen != Abyss.Runtime.GameScreen.Title)
    return "NOT STARTED: require idle Title, no ReviewBoot; stop/restart Play first";
System.IO.Directory.CreateDirectory(root);
// FileShare.None rejects overlapping copies of this harness without overwriting their evidence.
var lease = new System.IO.FileStream(System.IO.Path.Combine(root, "battle-acceptance.lock"), System.IO.FileMode.OpenOrCreate, System.IO.FileAccess.ReadWrite, System.IO.FileShare.None);
System.IO.Directory.CreateDirectory(outDir);
var originalPreferences = app.Preferences;
string preferenceJson = Newtonsoft.Json.JsonConvert.SerializeObject(originalPreferences);
bool originalBackground = Application.runInBackground;
float originalTimeScale = Time.timeScale;
var editorAssembly = typeof(UnityEditor.Editor).Assembly;
var viewType = editorAssembly.GetType("UnityEditor.GameView");
UnityEditor.EditorWindow gameView = null;
object sizeGroup = null;
int originalSize = -1;
var addedSizes = new System.Collections.Generic.List<int>();
Application.LogCallback handler = (message, stack, type) => {
    if (type == LogType.Warning || type == LogType.Error || type == LogType.Exception || type == LogType.Assert) {
        logs.Add(new { type = type.ToString(), message, stack });
        if (type != LogType.Warning) failed = true;
    }
};
void Isolate() {
    typeof(Abyss.Runtime.GameApp).GetField("saveDirectory", flags).SetValue(app, savePath);
    typeof(Abyss.Runtime.GameApp).GetField("<Saves>k__BackingField", flags).SetValue(app, new Abyss.Runtime.Persistence.SaveRepository(savePath, app.DB));
}
void Resize(int width, int height) {
    var sizesType = editorAssembly.GetType("UnityEditor.GameViewSizes");
    var singleton = typeof(UnityEditor.ScriptableSingleton<>).MakeGenericType(sizesType);
    var sizes = singleton.GetProperty("instance").GetValue(null);
    var getGroup = sizesType.GetMethod("GetGroup");
    sizeGroup = getGroup.Invoke(sizes, new[] { System.Enum.Parse(getGroup.GetParameters()[0].ParameterType, "Standalone") });
    var kind = editorAssembly.GetType("UnityEditor.GameViewSizeType");
    var sizeType = editorAssembly.GetType("UnityEditor.GameViewSize");
    var ctor = sizeType.GetConstructor(flags, null, new[] { kind, typeof(int), typeof(int), typeof(string) }, null);
    int index = (int)sizeGroup.GetType().GetMethod("GetTotalCount").Invoke(sizeGroup, null);
    sizeGroup.GetType().GetMethod("AddCustomSize").Invoke(sizeGroup, new[] { ctor.Invoke(new object[] { System.Enum.ToObject(kind, 1), width, height, "Tripo battle QA" }) });
    addedSizes.Add(index); // RemoveCustomSize takes the absolute group index, including built-ins.
    if (gameView == null) {
        gameView = UnityEditor.EditorWindow.GetWindow(viewType);
        originalSize = (int)viewType.GetProperty("selectedSizeIndex", flags).GetValue(gameView);
    }
    viewType.GetProperty("selectedSizeIndex", flags).SetValue(gameView, index);
    gameView.Focus();
}
async System.Threading.Tasks.Task Snap(int width, int height, bool overview = false) {
    Resize(width, height);
    await Until(() => Screen.width == width && Screen.height == height, "GameView resize " + width + "x" + height);
    await Frames(8);
    var director = (Abyss.Runtime.Battle.BattleCameraDirector)typeof(Abyss.Runtime.Battle.BattleView).GetField("_director", flags).GetValue(app.Battle);
    var displayed = (System.Collections.Generic.Dictionary<string, Abyss.Runtime.Battle.BattleDisplayUnit>)typeof(Abyss.Runtime.Battle.BattleView).GetField("_units", flags).GetValue(app.Battle);
    if (overview) director.Establishing(true);
    else director.Command(displayed[app.Battle.Engine.ActiveHero.Id]);
    await Until(() => !director.Blending, "Camera blend settles");
    await Frames(3);
    Canvas.ForceUpdateCanvases();
    var camera = app.MainCamera;
    Check("battle camera at capture", camera != null && camera.isActiveAndEnabled, new { width, height });
    if (camera != null) {
        var hud = UnityEngine.Object.FindAnyObjectByType<Abyss.UI.Battle.BattleHUD>();
        Rect free = hud.FreeViewport;
        // S0 frames everybody; S1 deliberately frames the actor and enemies, not off-duty teammates.
        var subjects = overview ? displayed.Values.Where(u => u.Alive).ToArray()
            : displayed.Values.Where(u => u.Alive && (u.Id == app.Battle.Engine.ActiveHero.Id || u.Side == Abyss.Logic.Battle.BattleSide.Enemy)).ToArray();
        foreach (var unit in subjects) {
            object[] args = { unit, new Bounds(), false };
            bool hasBody = (bool)typeof(Abyss.Runtime.Battle.BattleCameraDirector).GetMethod("BodyBox", flags).Invoke(director, args);
            Bounds box = (Bounds)args[1];
            bool inside = hasBody;
            for (int k = 0; k < 8; k++) {
                var p = camera.WorldToViewportPoint(new Vector3((k & 1) == 0 ? box.min.x : box.max.x, (k & 2) == 0 ? box.min.y : box.max.y, (k & 4) == 0 ? box.min.z : box.max.z));
                inside &= p.z > camera.nearClipPlane && p.x >= free.xMin - .005f && p.x <= free.xMax + .005f && p.y >= free.yMin - .005f && p.y <= free.yMax + .005f;
            }
            Check("required subject body inside HUD-free viewport", inside, new { unit.Id, width, height, overview, director.LastChoice });
        }
    }
    string path = System.IO.Path.Combine(outDir, (overview ? "overview-" : "battle-") + width + "x" + height + ".png");
    ScreenCapture.CaptureScreenshot(path); // full GameView, including screen-space overlay canvas
    await Frames(3);
    await Until(() => System.IO.File.Exists(path) && new System.IO.FileInfo(path).Length > 100, "Screenshot write");
    var texture = new Texture2D(2, 2);
    try {
        Check("PNG decoded", ImageConversion.LoadImage(texture, System.IO.File.ReadAllBytes(path)), path);
        Check("PNG dimensions", texture.width == width && texture.height == height, new { path, texture.width, texture.height });
        var pixels = texture.GetPixels32();
        var colors = new System.Collections.Generic.HashSet<int>();
        for (int i = 0; i < pixels.Length; i += 97) colors.Add((pixels[i].r << 16) | (pixels[i].g << 8) | pixels[i].b);
        Check("nonuniform rendered frame (heuristic)", colors.Count > 32, new { path, sampledColors = colors.Count });
    } finally { UnityEngine.Object.Destroy(texture); }
    int canvases = 0, labels = 0;
    foreach (var canvas in UnityEngine.Object.FindObjectsByType<Canvas>(FindObjectsSortMode.None)) if (canvas.isActiveAndEnabled) canvases++;
    foreach (var label in UnityEngine.Object.FindObjectsByType<TMPro.TMP_Text>(FindObjectsSortMode.None)) if (label.isActiveAndEnabled && !string.IsNullOrWhiteSpace(label.text)) labels++;
    Check("active canvas and text", canvases > 0 && labels > 0, new { width, height, canvases, labels });
}
async System.Threading.Tasks.Task Run() {
    await System.Threading.Tasks.Task.Yield(); // promptly return eval control; Unity APIs remain on Unity thread
    Application.logMessageReceived += handler;
    try {
        Isolate();
        typeof(Abyss.Runtime.GameApp).GetField("<Preferences>k__BackingField", flags).SetValue(app,
            Newtonsoft.Json.JsonConvert.DeserializeObject<Abyss.Runtime.Persistence.GamePreferences>(preferenceJson));
        app.Preferences.AutoBattle = false; app.Preferences.BattleSpeed = 1f; app.Preferences.ReducedMotion = false;
        Application.runInBackground = true; Time.timeScale = 1f;
        Resize(1280, 720);
        await Until(() => Screen.width == 1280 && Screen.height == 720, "Initial GameView resize");
        await Frames(8);
        var state = Abyss.Logic.Game.GameState.NewGame(app.DB, Abyss.Logic.Difficulty.Normal);
        state.Flags.Remove(Abyss.Logic.Game.GameFlow.FlagProloguePending);
        foreach (string tip in new[] { "first_battle", "first_foe", "first_tp_full", "first_trap", "first_town" }) state.Flags.Add(Abyss.Logic.Game.GameFlow.TipFlag(tip));
        var heroes = new[] { "h_minjun", "h_jiho", "h_bora", "h_hana" };
        state.Party.Clear(); state.Reserve.Clear();
        foreach (string id in heroes) Abyss.Logic.Game.HunterRoster.Recruit(app.DB, state, id);
        Check("four nonnull recruited heroes", state.Party.Count == 4 && state.Party.All(h => h != null), heroes);
        if (failed) throw new System.InvalidOperationException("Party fixture failed");
        foreach (var hero in state.AllHunters()) { hero.Level = 20; hero.Hp = -1; hero.Mp = -1; }
        state.FloorIndex = 0; state.Location = Abyss.Logic.Game.GameLocation.Dungeon;
        state.Repair(app.DB);
        try { app.BeginReview(state, 0); } finally { Isolate(); }
        Check("save directory isolated", (string)typeof(Abyss.Runtime.GameApp).GetField("saveDirectory", flags).GetValue(app) == savePath);
        var request = (Abyss.Logic.Dungeon.DungeonBattleRequest)typeof(Abyss.Logic.Dungeon.DungeonRun).GetMethod("StartBattle", flags).Invoke(app.Dungeon,
            new object[] { Abyss.Logic.BattleKind.Random, new System.Collections.Generic.List<string> { "slime", "slime" }, state.Position, state.Position, "", 1f });
        app.BeginBattle(request.Setup);
        await Until(() => app.Battle != null && !app.Battle.Playing && app.Battle.Engine.ActiveHero != null, "Battle manual input");
        await Frames(15);
        Check("actual battle manual input", app.Screen == Abyss.Runtime.GameScreen.Battle && !app.Battle.Auto && app.Battle.CanOpenPause);
        var units = (System.Collections.Generic.Dictionary<string, Abyss.Runtime.Battle.BattleDisplayUnit>)typeof(Abyss.Runtime.Battle.BattleView).GetField("_units", flags).GetValue(app.Battle);
        Check("known displayed heroes", heroes.All(id => units.Values.Any(u => u != null && u.Side == Abyss.Logic.Battle.BattleSide.Party && u.DefId == id)));
        Check("two displayed slimes", units.Values.Count(u => u != null && u.Side == Abyss.Logic.Battle.BattleSide.Enemy && u.DefId == "slime") == 2);
        foreach (var unit in units.Values) {
            bool valid = unit != null && unit.Model != null && unit.Model.Anim != null;
            Check("nonnull display model", valid, unit == null ? "null unit" : unit.Id);
            if (!valid) continue;
            var anim = unit.Model.Anim;
            string clip = anim.CurrentClip; float before = anim.NormalizedTime;
            Check("current clip", !string.IsNullOrEmpty(clip) && anim.HasClip(clip), new { unit.Id, clip, before });
            var skin = unit.Model.GetComponentsInChildren<SkinnedMeshRenderer>().FirstOrDefault(s => s.enabled && s.sharedMesh != null && s.bones.Length > 0);
            var mesh = new Mesh();
            try {
                Vector3[] pose = null;
                if (skin != null) { skin.BakeMesh(mesh); pose = mesh.vertices; }
                await Frames(12);
                float after = anim.NormalizedTime;
                Check("clip time advances", !float.IsNaN(after) && !float.IsInfinity(after) && System.Math.Abs(after - before) > 0.00001f, new { unit.Id, clip, before, after });
                if (unit.Side == Abyss.Logic.Battle.BattleSide.Party) {
                    float delta = 0;
                    if (skin != null && pose != null) {
                        skin.BakeMesh(mesh); var now = mesh.vertices;
                        if (now.Length == pose.Length) for (int i = 0; i < now.Length; i++) delta = Mathf.Max(delta, (now[i] - pose[i]).sqrMagnitude);
                    }
                    Check("hero skin pose deforms", skin != null && delta > 0.0000000001f, new { unit.Id, maxVertexDeltaSquared = delta });
                }
            } finally { UnityEngine.Object.Destroy(mesh); }
        }
        var camera = app.MainCamera;
        Check("active scene camera", camera != null && camera.isActiveAndEnabled);
        await Snap(1280, 720);
        await Snap(915, 412);
        await Snap(1280, 720, true);
        await Snap(915, 412, true);
    } catch (System.Exception e) { failed = true; failure = e.ToString(); }
    finally {
        try {
            if (app != null) {
                // Keep QA state away from player persistence even after a partial failure.
                Isolate();
                typeof(Abyss.Runtime.GameApp).GetField("<Preferences>k__BackingField", flags).SetValue(app, originalPreferences);
                Check("preferences restored", Newtonsoft.Json.JsonConvert.SerializeObject(app.Preferences) == preferenceJson);
            }
            if (gameView != null && originalSize >= 0) viewType.GetProperty("selectedSizeIndex", flags).SetValue(gameView, originalSize);
            if (sizeGroup != null) for (int i = addedSizes.Count - 1; i >= 0; i--) sizeGroup.GetType().GetMethod("RemoveCustomSize").Invoke(sizeGroup, new object[] { addedSizes[i] });
        } catch (System.Exception e) { failed = true; failure = (failure ?? "") + "\nCleanup: " + e; }
        finally {
            Application.runInBackground = originalBackground; Time.timeScale = originalTimeScale;
            Application.logMessageReceived -= handler;
            try {
                string status = failed ? "failed" : "checks-passed-visual-review-required";
                System.IO.File.WriteAllText(System.IO.Path.Combine(outDir, "checks.json"), Newtonsoft.Json.JsonConvert.SerializeObject(new { status, failure, savePath, checks, consoleIssues = logs, visualApproval = "pending-parent-review", persistence = "QA isolation retained until Play stops" }, Newtonsoft.Json.Formatting.Indented));
                System.IO.File.WriteAllText(System.IO.Path.Combine(outDir, "DONE"), status);
            } finally { lease.Dispose(); }
        }
    }
}
_ = Run();
return "Started background Unity-context Task; evidence: " + outDir + "; poll DONE; inspect both PNGs. Stop Play before normal play.";
