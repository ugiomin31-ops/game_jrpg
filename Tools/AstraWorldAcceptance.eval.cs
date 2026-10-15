// External Unity Pipeline eval_file statements/local functions, following Pr6Acceptance.eval.cs.
// Parent runs SERIALIZED, in a fresh Main Play session; this fixture requests GameView focus.
// unity command eval_file --file Tools/AstraWorldAcceptance.eval.cs
// Returns immediately. Poll the returned run directory's DONE (<=25 seconds per poll).
// Never run this worker-side. No original campaign save is loaded or restored.
// BeginReview is the FIRST mutating GameApp call; QA persistence stays isolated until Play ends.
// Screenshots/real behavior evidence require parent review. No portrait support is claimed.
// Set this capture label before the parent runs; build fingerprints, not the label, establish before/after provenance.
const string CaptureIntent = "after-map-contrast";
// Parent first reruns only shop in fresh Play; set false for the single subsequent full world/map run.
bool ShopOnly = false;
var expectedProject = System.IO.Path.GetFullPath(@"C:\Users\User\Desktop\GAME_JRPG\handoff-verify-20261015");
var project = System.IO.Directory.GetParent(Application.dataPath).FullName;
if (!Application.isPlaying || Abyss.Runtime.GameApp.Instance == null)
    throw new System.InvalidOperationException("Fresh Main Play Mode with GameApp is required.");
if (!string.Equals(expectedProject, project, System.StringComparison.OrdinalIgnoreCase)
    || UnityEngine.SceneManagement.SceneManager.GetActiveScene().name != "Main")
    throw new System.InvalidOperationException("Wrong Unity project/scene: " + project + " / " + UnityEngine.SceneManagement.SceneManager.GetActiveScene().path);
if (GameObject.Find("AstraWorldAcceptance_BUSY") != null || GameObject.Find("AstraTownTrailAcceptance_BUSY") != null)
    throw new System.InvalidOperationException("An Astra world acceptance run is already active.");
var app = Abyss.Runtime.GameApp.Instance;
var flags = System.Reflection.BindingFlags.Instance | System.Reflection.BindingFlags.Public | System.Reflection.BindingFlags.NonPublic;
var outDir = System.IO.Path.Combine(project, "docs/verification/astra-enrichment-20261015/runtime/world-" + (ShopOnly ? "shop-only-" : "") + CaptureIntent + "-" + System.DateTime.UtcNow.ToString("yyyyMMdd-HHmmss-fff"));
var qaSave = System.IO.Path.Combine(outDir, "qa-save");
System.IO.Directory.CreateDirectory(outDir);
var checks = new System.Collections.Generic.List<object>();
var issues = new System.Collections.Generic.List<object>();
var images = new System.Collections.Generic.List<object>();
var observations = new System.Collections.Generic.List<object>();
var manual = new System.Collections.Generic.List<string> {
    "Inspect every PNG for clipping/overlap, readable Korean labels, world visibility, focus, and nonblank models/effects.",
    "Synthetic keyboard / real widget calls do not certify physical keyboard, controller or touch raycasts.",
    "Map is all-revealed QA content on the authored floor with most distinct feature markers; other floors/zones, hidden/spent transitions and a chasing FOE remain manual.",
    "Follower controller ownership and solid sweeps are exercised; breadcrumb following around town corners and TownEnrichment asset/tree alignment still need runtime traversal and visual review.",
    "Battle event consumption and AreaCenter/Targets are exercised; camera composition and moving VFX placement still need visual review."
};
bool failed = false, isolated = false;
string phase = "preconditions";
var originalPreferences = app.Preferences;
bool originalBackground = Application.runInBackground;
GameObject lockRoot = null, physicsFixture = null;
Abyss.Runtime.World.TownWorld disabledTown = null;
UnityEngine.InputSystem.Keyboard testKeyboard = null;
var previousKeyboard = UnityEngine.InputSystem.Keyboard.current;
object sizeGroup = null;
UnityEditor.EditorWindow gameView = null;
System.Reflection.PropertyInfo selectedSize = null;
int originalSize = -1;
var customSizes = new System.Collections.Generic.List<int>();
void Check(string name, bool pass, object detail = null) {
    checks.Add(new { phase, name, passed = pass, detail }); if (!pass) failed = true;
}
void Require(bool pass, string message) { Check(message, pass); if (!pass) throw new System.InvalidOperationException(message); }
object Read(object target, string field) => target.GetType().GetField(field, flags).GetValue(target);
object Call(object target, string method, params object[] args) => target.GetType().GetMethod(method, flags).Invoke(target, args);
string Hash(string path) {
    if (!System.IO.File.Exists(path)) return "missing";
    using (var hash = System.Security.Cryptography.SHA256.Create())
        return System.BitConverter.ToString(hash.ComputeHash(System.IO.File.ReadAllBytes(path))).Replace("-", "").ToLowerInvariant();
}
var build = new {
    project, scene = UnityEngine.SceneManagement.SceneManager.GetActiveScene().path,
    module = typeof(Abyss.Runtime.GameApp).Module.ModuleVersionId.ToString(), unity = Application.unityVersion,
    mapSourceSha256 = Hash(System.IO.Path.Combine(project, "Assets/_Game/Scripts/UI/Screens/DungeonMapGraphic.cs")),
    mapScreenSha256 = Hash(System.IO.Path.Combine(project, "Assets/_Game/Scripts/UI/Screens/GameMapScreen.cs")),
    assemblySha256 = Hash(typeof(Abyss.Runtime.GameApp).Assembly.Location),
    fixtureSha256 = Hash(System.IO.Path.Combine(project, "Tools/AstraWorldAcceptance.eval.cs")),
    captureIntent = CaptureIntent, initialFrame = Time.frameCount, initialScreen = app.Screen.ToString(), initialCaptureDeltaTime = Time.captureDeltaTime
};
void Report(string status) => System.IO.File.WriteAllText(System.IO.Path.Combine(outDir, "result.json"),
    Newtonsoft.Json.JsonConvert.SerializeObject(new { status, phase, build, isolated, qaSave, checks, issues, images, observations,
        scope = ShopOnly ? "shop-only; map, followers, blocked input, screenshots and battle not rerun" : "full-world", expectedPngs = ShopOnly ? 0 : 8,
        manualRemaining = manual, visualAccepted = false, requestedModel = "gpt-6-astra", requestedEffort = "high",
        requestedTier = "Fast/priority", verifiedTier = "not exposed" }, Newtonsoft.Json.Formatting.Indented));
async System.Threading.Tasks.Task Until(System.Func<bool> condition, string label, int seconds = 25) {
    var deadline = System.DateTime.UtcNow.AddSeconds(seconds);
    while (!condition()) {
        if (!Application.isPlaying) throw new System.InvalidOperationException("Play stopped: " + label);
        if (System.DateTime.UtcNow > deadline) throw new System.TimeoutException(label);
        await System.Threading.Tasks.Task.Yield();
    }
}
async System.Threading.Tasks.Task Frames(int count) { int end = Time.frameCount + count; await Until(() => Time.frameCount >= end, "frames " + count); }
async System.Threading.Tasks.Task Step(string name, System.Func<System.Threading.Tasks.Task> body) {
    if (ShopOnly && name != "actual-shop-quantity-boundary") return;
    phase = name; Report("running");
    try { await body(); } catch (System.Exception e) { failed = true; issues.Add(new { phase, exception = e.ToString() }); }
    Report("running");
}
void Isolate() {
    typeof(Abyss.Runtime.GameApp).GetField("saveDirectory", flags).SetValue(app, qaSave);
    typeof(Abyss.Runtime.GameApp).GetField("<Saves>k__BackingField", flags).SetValue(app, new Abyss.Runtime.Persistence.SaveRepository(qaSave, app.DB));
    isolated = (string)Read(app, "saveDirectory") == qaSave;
    if (!isolated) throw new System.InvalidOperationException("QA persistence isolation failed");
}
Abyss.Logic.Game.GameState NewState() {
    var state = Abyss.Logic.Game.GameState.NewGame(app.DB, Abyss.Logic.Difficulty.Normal);
    Abyss.Logic.Game.GameFlow.CompletePrologue(state);
    foreach (var h in state.Party) { h.Level = 20; h.Hp = -1; h.Mp = -1; }
    foreach (string tip in new[] { "first_town", "first_battle", "first_foe", "first_trap", "first_tp_full" })
        state.Flags.Add(Abyss.Logic.Game.GameFlow.TipFlag(tip));
    state.Flags.Add("biome_0_seen"); state.Repair(app.DB);
    // Consume first-town notices on this detached QA state, before any GameApp mutation.
    Abyss.Logic.Game.GameFlow.EnterTown(app.DB, state);
    return state;
}
void Review(Abyss.Logic.Game.GameState state, int floor) {
    state.FloorIndex = floor; state.Location = Abyss.Logic.Game.GameLocation.Dungeon;
    state.Position = Abyss.Logic.Dungeon.DungeonGrid.Parse(app.DB.Floors[floor], state.Floor(app.DB.Floors[floor].Id)).Start;
    try { app.BeginReview(state, floor); } finally { Isolate(); }
}
void FocusGameView() {
    if (gameView == null) {
        var viewType = typeof(UnityEditor.Editor).Assembly.GetType("UnityEditor.GameView");
        gameView = UnityEditor.EditorWindow.GetWindow(viewType);
        selectedSize = viewType.GetProperty("selectedSizeIndex", flags);
        originalSize = (int)selectedSize.GetValue(gameView);
    }
    gameView.Focus();
}
void Resize(int width, int height) {
    FocusGameView();
    var assembly = typeof(UnityEditor.Editor).Assembly;
    var sizesType = assembly.GetType("UnityEditor.GameViewSizes");
    var sizes = typeof(UnityEditor.ScriptableSingleton<>).MakeGenericType(sizesType).GetProperty("instance").GetValue(null);
    var getGroup = sizesType.GetMethod("GetGroup");
    sizeGroup = getGroup.Invoke(sizes, new[] { System.Enum.Parse(getGroup.GetParameters()[0].ParameterType, "Standalone") });
    var sizeType = assembly.GetType("UnityEditor.GameViewSize");
    var kind = assembly.GetType("UnityEditor.GameViewSizeType");
    var ctor = sizeType.GetConstructor(flags, null, new[] { kind, typeof(int), typeof(int), typeof(string) }, null);
    int index = (int)Call(sizeGroup, "GetTotalCount");
    Call(sizeGroup, "AddCustomSize", ctor.Invoke(new object[] { System.Enum.ToObject(kind, 1), width, height, "Astra QA temporary" }));
    customSizes.Add(index); // Unity RemoveCustomSize takes the absolute group index, including built-ins.
    selectedSize.SetValue(gameView, index); gameView.Focus();
}
async System.Threading.Tasks.Task Size(int w, int h) { Resize(w, h); await Until(() => Screen.width == w && Screen.height == h, "GameView resize"); await Frames(6); }
async System.Threading.Tasks.Task Snap(string label, int w, int h) {
    Require(Screen.width == w && Screen.height == h, "actual screenshot resolution " + label);
    Canvas.ForceUpdateCanvases();
    string path = System.IO.Path.Combine(outDir, label + "-" + w + "x" + h + ".png");
    ScreenCapture.CaptureScreenshot(path);
    await Frames(3); await Until(() => System.IO.File.Exists(path) && new System.IO.FileInfo(path).Length > 32, "screenshot written " + label);
    var bytes = System.IO.File.ReadAllBytes(path);
    int pw = (bytes[16] << 24) | (bytes[17] << 16) | (bytes[18] << 8) | bytes[19];
    int ph = (bytes[20] << 24) | (bytes[21] << 16) | (bytes[22] << 8) | bytes[23];
    Check("PNG dimensions " + label, pw == w && ph == h, new { pw, ph });
    images.Add(new { label, path, width = pw, height = ph, bytes = bytes.Length, sha256 = Hash(path), screen = app.Screen.ToString(), frame = Time.frameCount });
}
System.Collections.Generic.List<Abyss.Runtime.Art.CharacterModel> Party(Abyss.Runtime.World.TownWorld town)
    => (System.Collections.Generic.List<Abyss.Runtime.Art.CharacterModel>)Read(town, "party");
void Controllers(Abyss.Runtime.World.TownWorld town, string label) {
    var models = Party(town);
    var bodies = models.Select(m => m.GetComponent<CharacterController>()).ToArray();
    var followers = (System.Collections.IList)Read(town, "followers");
    Require(models.Count == app.State.Party.Count && models.Count == 4, label + " four rendered party models");
    Check(label + " controller ownership", bodies.All(b => b != null && b.enabled) && models.All(m => m.GetComponents<CharacterController>().Length == 1)
        && followers.Count == models.Count - 1 && object.ReferenceEquals(Read(town, "controller"), bodies[0]));
    for (int i = 1; i < bodies.Length; i++) {
        Check(label + " follower record " + i, object.ReferenceEquals(Read(followers[i - 1], "Body"), bodies[i]));
        for (int j = 0; j < i; j++) Check(label + " ignored party collision " + i + "/" + j, Physics.GetIgnoreCollision(bodies[i], bodies[j]));
    }
}
void IdleAfter(Abyss.Runtime.World.TownWorld town, string reason, System.Action block) {
    var models = Party(town);
    foreach (var m in models) m.Play("Idle", 0f);
    var idle = models.Select(m => m.Anim.CurrentClip).ToArray();
    foreach (var m in models) m.Play("Walk", 0f);
    Require(models.Select((m, i) => m.Anim.CurrentClip != idle[i]).All(v => v), reason + " nonidle precondition for all members");
    var before = models.Select(m => m.transform.position).ToArray();
    block(); Call(town, "Update");
    Check(reason + " all members return to their resolved idle", models.Select((m, i) => m.Anim.CurrentClip == idle[i]).All(v => v),
        models.Select(m => new { m.ModelId, clip = m.Anim.CurrentClip }).ToArray());
    Check(reason + " no party movement", models.Select((m, i) => (m.transform.position - before[i]).sqrMagnitude < .000001f).All(v => v));
}
void Key(bool move) {
    UnityEngine.InputSystem.InputSystem.QueueStateEvent(testKeyboard, move
        ? new UnityEngine.InputSystem.LowLevel.KeyboardState(UnityEngine.InputSystem.Key.W)
        : new UnityEngine.InputSystem.LowLevel.KeyboardState());
    UnityEngine.InputSystem.InputSystem.Update();
}
Abyss.UI.UIList MenuList() {
    var menu = Abyss.UI.UIRoot.Instance.Screens.Top as Abyss.UI.GameMenuScreen;
    if (menu == null) throw new System.InvalidOperationException("Expected actual GameMenuScreen");
    return (Abyss.UI.UIList)Read(menu, "list");
}
Application.LogCallback log = (message, stack, type) => {
    if (type == LogType.Error || type == LogType.Exception || type == LogType.Assert) {
        failed = true; issues.Add(new { phase, type = type.ToString(), message, stack });
    }
};
async System.Threading.Tasks.Task Run() {
    await System.Threading.Tasks.Task.Yield();
    Application.logMessageReceived += log;
    try {
        phase = "game-view-focus";
        FocusGameView();
        await Until(() => Application.isFocused && UnityEditor.EditorWindow.focusedWindow == gameView, "GameView must acquire real application focus", 10);
        Require(Application.isFocused && UnityEditor.EditorWindow.focusedWindow == gameView, "actual focused GameView before QA app mutations");
        phase = "review-isolation";
        var state = NewState();
        // Reveal authored cells/traps ONLY in this new QA state; no shared DB, geometry or marker logic is replaced.
        if (!ShopOnly) foreach (var floor in app.DB.Floors) {
            var progress = state.Floor(floor.Id);
            for (int y = 0; y < floor.Rows.Count; y++) for (int x = 0; x < floor.Rows[y].Length; x++) {
                var pos = new Abyss.Logic.Dungeon.GridPos(x, y); progress.Explored.Add(pos);
                if (floor.Rows[y][x] == 'X') progress.SteppedTraps.Add(pos);
            }
        }
        int mapFloor = ShopOnly ? 0 : app.DB.Floors.Select((f, i) => new { i, features = string.Concat(f.Rows).Distinct().Count(c => "><WHLTKXNBE".Contains(c)) })
            .OrderByDescending(v => v.features).ThenBy(v => v.i).First().i;
        Review(state, mapFloor); // FIRST mutating GameApp call; BeginReview isolates before it adopts State.
        Require(isolated, "BeginReview followed by dedicated per-run QA persistence");
        lockRoot = new GameObject("AstraWorldAcceptance_BUSY");
        typeof(Abyss.Runtime.GameApp).GetField("<Preferences>k__BackingField", flags).SetValue(app,
            Newtonsoft.Json.JsonConvert.DeserializeObject<Abyss.Runtime.Persistence.GamePreferences>(Newtonsoft.Json.JsonConvert.SerializeObject(originalPreferences)));
        app.Preferences.AutoBattle = false; app.Preferences.BattleSpeed = 1f; app.Preferences.ReducedMotion = false;
        Application.runInBackground = true;
        await Step("map-" + CaptureIntent + "-first", async () => {
            var grid = app.Dungeon.Grid;
            var counts = new System.Collections.Generic.Dictionary<char, int>();
            for (int y = 0; y < grid.Height; y++) for (int x = 0; x < grid.Width; x++) {
                var p = new Abyss.Logic.Dungeon.GridPos(x, y); char marker = grid.MapMarker(p);
                if (marker == 'E') marker = (char)typeof(Abyss.UI.DungeonMapGraphic).GetMethod("EventMarker", System.Reflection.BindingFlags.Static | System.Reflection.BindingFlags.NonPublic).Invoke(null, new object[] { grid, p });
                if (!counts.ContainsKey(marker)) counts[marker] = 0; counts[marker]++;
            }
            Check("authored map cells are revealed", grid.Progress.Explored.Count >= grid.Floor.Rows.Sum(row => row.Length), new { mapFloor, grid.Floor.Id, counts, liveFoes = grid.Foes.Count(f => f.Alive) });
            foreach (var size in new[] { new[] {1280,720}, new[] {915,412} }) {
                await Size(size[0], size[1]); Call(app.UI, "OpenMapFromHud"); await Frames(10);
                var screen = Abyss.UI.UIRoot.Instance.Screens.Top as Abyss.UI.GameMapScreen;
                Require(screen != null && app.Paused, "real map screen opened through HUD route");
                var graphic = screen.GetComponentInChildren<Abyss.UI.DungeonMapGraphic>();
                // Borrow the renderer-owned mesh for inspection; do not destroy or mutate it.
                var mesh = graphic.canvasRenderer.GetMesh();
                Check("actual map mesh is populated", mesh != null && mesh.vertexCount > 0, mesh == null ? 0 : mesh.vertexCount);
                await Snap("map-" + CaptureIntent + "-all-revealed-floor-" + mapFloor, size[0], size[1]);
                screen.Close(); await Frames(3);
            }
        });
        phase = "town-entry"; app.EnterTown();
        await Until(() => app.Screen == Abyss.Runtime.GameScreen.Town && !app.UI.BlocksWorldInput, "Town ready");
        await Frames(8);
        var town = (Abyss.Runtime.World.TownWorld)Read(app, "townWorld");
        Require(town != null, "actual town world exists");
        await Step("followers-lifecycle-and-collision", async () => {
            Controllers(town, "initial");
            var old = Party(town).Select(m => m.gameObject).ToArray();
            app.RefreshRosterVisuals();
            Check("replaced roster objects immediately inactive", old.All(o => o == null || !o.activeSelf));
            await Frames(3); Check("replaced roster objects destroyed", old.All(o => o == null));
            Controllers(town, "roster rebuild");
            for (int i = 0; i < 2; i++) {
                var hero = app.State.Party[i];
                var job = Abyss.Logic.Game.JobService.NextJobs(app.DB, hero).FirstOrDefault(j =>
                    Abyss.Runtime.Art.ArtLibrary.HeroModelPath(hero.Id, j.Id) != Abyss.Runtime.Art.ArtLibrary.HeroModelPath(hero.Id, hero.Job));
                if (job == null) { manual.Add("No authored alternate model path for party slot " + i + "; job controller replacement not exercised (roster rebuild is exercised)."); continue; }
                hero.Level = System.Math.Max(hero.Level, job.RequiredLevel);
                if (!string.IsNullOrEmpty(job.RequiredBoss)) app.State.Flags.Add(Abyss.Logic.Game.JobService.BossDefeatedFlag(job.RequiredBoss));
                if (!string.IsNullOrEmpty(job.RequiredItem)) app.State.AddItem(job.RequiredItem, 1);
                var previous = Party(town)[i].gameObject;
                Require(Abyss.Logic.Game.JobService.ChangeJob(app.DB, app.State, hero.Id, job.Id).Success, "real job service accepts QA promotion");
                app.RefreshJobVisuals(); await Frames(3);
                Check("old job model destroyed " + i, previous == null); Controllers(town, "job slot " + i);
            }
            town.enabled = false; disabledTown = town;
            physicsFixture = new GameObject("Astra temporary collision solid");
            var solid = physicsFixture.AddComponent<BoxCollider>();
            var anchor = new Vector3(5000f, 10f, 5000f);
            solid.size = new Vector3(.2f, 4f, 4f); solid.transform.position = anchor + new Vector3(1.2f, 1f, 0f);
            foreach (var model in Party(town).Skip(1)) {
                var body = model.GetComponent<CharacterController>(); var position = model.transform.position;
                try {
                    body.enabled = false; model.transform.position = anchor; body.enabled = true; Physics.SyncTransforms();
                    var hit = body.Move(Vector3.right * 3f);
                    Check("actual follower controller sweeps against solid " + model.ModelId,
                        (hit & CollisionFlags.Sides) != 0 && model.transform.position.x < anchor.x + 1.1f,
                        new { hit = hit.ToString(), x = model.transform.position.x - anchor.x });
                } finally { body.enabled = false; model.transform.position = position; body.enabled = true; Physics.SyncTransforms(); }
            }
            UnityEngine.Object.Destroy(physicsFixture); physicsFixture = null;
            town.enabled = true; disabledTown = null;
        });
        // The next case also restores temporary controls if the preceding case failed.
        if (town != null) town.enabled = true; disabledTown = null;
        await Step("town-blocks-pending-talk-and-input-consumption", async () => {
            app.UI.ShowTown(); app.SetPaused(false); await Frames(3);
            town.enabled = false; disabledTown = town;
            try {
                IdleAfter(town, "pause", () => app.SetPaused(true)); app.SetPaused(false); await Frames(2);
                IdleAfter(town, "facility UI", () => app.OpenTownService("party"));
                app.UI.ShowTown(); await Frames(3);
                var services = (System.Collections.IList)Read(town, "services");
                var spot = services.Cast<object>().First(s => (string)Read(s, "Id") == "shopkeeper");
                var player = (Transform)Read(town, "player"); var body = (CharacterController)Read(town, "controller");
                var position = player.position;
                try {
                    body.enabled = false; player.position = ((Transform)Read(spot, "Marker")).position + Vector3.right * 1.5f; body.enabled = true;
                    Physics.SyncTransforms(); Call(town, "Interact", spot);
                    Require(Read(town, "pendingTalk") != null, "real NPC interaction schedules delayed facility");
                    await Frames(1);
                    IdleAfter(town, "pending talk", () => { });
                    Require(Read(town, "pendingTalk") != null, "delayed NPC request is still pending before explicit facility entry");
                    app.OpenTownService("gate"); // Explicit non-NPC facility must supersede the delay.
                    Require(Read(town, "pendingTalk") == null && (float)Read(town, "pendingTimer") == 0f, "explicit gate cancels prior NPC request");
                    var gateScreen = Abyss.UI.UIRoot.Instance.Screens.Top;
                    await Frames(3); Call(town, "Update");
                    Check("explicit gate remains the active facility", object.ReferenceEquals(gateScreen, Abyss.UI.UIRoot.Instance.Screens.Top));
                    gateScreen.Close();
                    float afterDelay = Time.unscaledTime + 1.1f;
                    while (Time.unscaledTime < afterDelay) { await Frames(1); Call(town, "Update"); }
                    Check("closing explicit facility does not reopen stale NPC menu after original delay",
                        Abyss.UI.UIRoot.Instance.Screens.Count == 0 && Read(town, "pendingTalk") == null);
                } finally { body.enabled = false; player.position = position; body.enabled = true; Physics.SyncTransforms(); }
                app.UI.ShowTown(); await Frames(3);
                testKeyboard = UnityEngine.InputSystem.InputSystem.AddDevice<UnityEngine.InputSystem.Keyboard>(); testKeyboard.MakeCurrent();
                Key(true); var before = player.position; Call(town, "Update");
                Check("positive control: actual W input moves unblocked town leader", (player.position - before).sqrMagnitude > .000001f);
                Key(false); app.OpenTownService("party"); await Frames(3);
                var menu = Abyss.UI.UIRoot.Instance.Screens.Top;
                var back = menu.GetComponentsInChildren<Abyss.UI.UIButton>().First(b => b.Label != null && b.Label.text.Contains("돌아가기"));
                Key(true);
                IdleAfter(town, "actual back button consumed frame", () => {
                    back.Click(); Require(Abyss.UI.UIInput.ConsumedThisFrame && !app.UI.BlocksWorldInput, "real widget closes menu and consumes this frame");
                });
                Key(false); await Frames(2);
                Check("consumption expires on later frame", !Abyss.UI.UIInput.ConsumedThisFrame);
            } finally {
                if (testKeyboard != null) { Key(false); UnityEngine.InputSystem.InputSystem.RemoveDevice(testKeyboard); testKeyboard = null; previousKeyboard?.MakeCurrent(); }
                town.enabled = true; disabledTown = null; app.SetPaused(false); app.UI.ShowTown();
            }
        });
        await Step("actual-shop-quantity-boundary", async () => {
            app.UI.ShowTown();
            var entry = Abyss.Logic.Game.TownServices.ShopStock(app.DB, app.State, false).FirstOrDefault(e => e.Unlocked && e.Price > 0
                && app.DB.Items[e.Id].MaxStack >= 3 && app.DB.Items[e.Id].MaxStack < Abyss.Logic.Game.GameState.MaxStack);
            Require(entry != null, "authored item with per-item stack cap exists");
            int cap = app.DB.Items[entry.Id].MaxStack;
            app.State.Inventory[entry.Id] = cap - 2; app.State.Gold = entry.Price * 5;
            app.OpenTownService("shopkeeper"); await Frames(3);
            var stock = MenuList(); int index = stock.Items.ToList().FindIndex(r => r.Label == entry.DisplayName);
            Require(index >= 0, "actual shop row found"); stock.Select(index, false); stock.Submit(); await Frames(3);
            var quantities = MenuList();
            Require(quantities.Items.Count == 2 && quantities.Items[0].Label == "1개" && quantities.Items[1].Label == "2개", "UI offers only remaining capacity");
            int gold = app.State.Gold; quantities.Select(1, false); quantities.Submit();
            var modal = Abyss.UI.UIRoot.Instance.Modals.Top as Abyss.UI.UIModal;
            Require(modal != null, "real transaction confirmation opens");
            var confirm = modal.GetComponentsInChildren<Abyss.UI.UIButton>().First(b => b.Label.text == "실행");
            float acceptAfter = (float)Read(modal, "_acceptAfter");
            observations.Add(new { phase, stage = "modal-opened", frame = Time.frameCount, now = Time.unscaledTime, acceptAfter,
                nextClickAt = (float)Read(confirm, "_nextClickAt"), modal.IsTop, confirm.isActiveAndEnabled, confirm.Interactable,
                consumed = Abyss.UI.UIInput.ConsumedThisFrame, actual = app.State.ItemCount(entry.Id), app.State.Gold });
            if (ShopOnly) {
                // Reproduce the timing hazard through the actual button/Answer path, without waiting or bypassing its guards.
                Require(Time.unscaledTime < acceptAfter, "early-click regression starts inside the actual modal guard");
                confirm.Click();
                Check("actual early confirm leaves transaction pending and resources unchanged", !(bool)Read(modal, "_answered") && modal.IsTop
                    && app.State.ItemCount(entry.Id) == cap - 2 && app.State.Gold == gold,
                    new { now = Time.unscaledTime, acceptAfter, nextClickAt = (float)Read(confirm, "_nextClickAt") });
            }
            // Three rendered frames can be less than UIModal's 0.35s guard; wait for the production deadlines, not a frame guess.
            await Until(() => modal == null || (Time.unscaledTime >= acceptAfter
                && Time.unscaledTime >= (float)Read(confirm, "_nextClickAt")), "transaction modal/button acceptance deadlines");
            Require(modal != null && modal.IsTop && modal.Group.interactable && confirm.isActiveAndEnabled && confirm.Interactable
                && Abyss.UI.UIInput.CanReceive(confirm) && !(bool)Read(modal, "_answered"), "same real modal is ready for one accepted confirm");
            float clickAt = Time.unscaledTime;
            confirm.Click(); // One accepted attempt; never call Answer or TownServices directly to force a pass.
            bool answered = (bool)Read(modal, "_answered");
            observations.Add(new { phase, stage = "accepted-click-returned", frame = Time.frameCount, clickAt, acceptAfter,
                answered, modal.IsOpen, actual = app.State.ItemCount(entry.Id), app.State.Gold });
            await Frames(3);
            bool committed = answered && app.State.ItemCount(entry.Id) == cap && app.State.Gold == gold - entry.Price * 2;
            Check("real transaction fills exact cap and charges once", committed,
                new { entry.Id, cap, actual = app.State.ItemCount(entry.Id), app.State.Gold, expectedGold = gold - entry.Price * 2, clickAt, acceptAfter, answered });
            if (!committed) throw new System.InvalidOperationException("Transaction did not commit; inspect modal timing observations before interpreting stock-row state.");
            stock = MenuList(); index = stock.Items.ToList().FindIndex(r => r.Label == entry.DisplayName);
            Require(index >= 0 && !stock.Items[index].Enabled, "full item row is disabled after actual transaction");
            var stable = Abyss.Logic.Game.SaveCodec.Serialize(app.State); stock.Select(index, false); stock.Submit();
            Check("disabled row cannot transact", stable == Abyss.Logic.Game.SaveCodec.Serialize(app.State));
            Check("transaction persistence route remains isolated", (string)Read(app, "saveDirectory") == qaSave);
            app.UI.ShowTown(); await Frames(3);
        });
        await Step("town-screenshots", async () => {
            foreach (var size in new[] { new[] {1280,720}, new[] {915,412} }) {
                await Size(size[0], size[1]); app.UI.ShowTown(); await Frames(10); await Snap("town", size[0], size[1]);
            }
        });
        foreach (var size in new[] { new[] {1280,720}, new[] {915,412} }) await Step("battle-playback-" + size[0], async () => {
            await Size(size[0], size[1]); Review(NewState(), 0);
            var request = (Abyss.Logic.Dungeon.DungeonBattleRequest)Call(app.Dungeon, "StartBattle", Abyss.Logic.BattleKind.Random,
                new System.Collections.Generic.List<string> { "slime", "slime" }, app.State.Position, app.State.Position, "", 1f);
            const string skillId = "jb_el_tri_burst";
            var skill = app.DB.Skills[skillId];
            Require(skill.Scope == Abyss.Logic.Scope.Random && skill.HitCount == 6, "authored six-hit random skill");
            foreach (var hero in request.Setup.Party) { if (!hero.Skills.Contains(skillId)) hero.Skills.Add(skillId); hero.Mp = hero.MaxMp = 100; }
            app.BeginBattle(request.Setup);
            await Until(() => app.Battle != null && !app.Battle.Playing && app.Battle.Engine.ActiveHero != null, "manual battle command ready");
            var view = app.Battle; await Frames(8); await Snap("battle", size[0], size[1]);
            var engine = view.Engine; var actor = engine.ActiveHero;
            // QA-only combat stimulus, after idle capture: first target is wounded, survivor endures all remaining hits.
            typeof(Abyss.Logic.Battle.BattleUnit).GetProperty("Hp").SetValue(engine.Enemies[0], 1);
            typeof(Abyss.Logic.Battle.BattleUnit).GetProperty("MaxHp").SetValue(engine.Enemies[1], 3000);
            typeof(Abyss.Logic.Battle.BattleUnit).GetProperty("Hp").SetValue(engine.Enemies[1], 3000);
            ulong seed = 0; bool found = false;
            for (; seed < 2048; seed++) {
                var probe = new Abyss.Logic.Battle.GodotRng(seed); bool repeats = true;
                for (int i = 0; i < 6; i++) if (probe.RandiRange(0, 1) != 0) repeats = false;
                if (repeats) { found = true; break; }
            }
            Require(found, "legal repeated-target seed found using production RNG"); engine.Rng.Seed(seed);
            Require(view.Submit(Abyss.Logic.Battle.BattleCommand.Skill(skillId)), "actual BattleView accepts random skill");
            await Until(() => (Read(view, "_action") as Abyss.Logic.Battle.ActionStartEvent)?.SkillId == skillId, "BattleView presents random ActionStart");
            var start = (Abyss.Logic.Battle.ActionStartEvent)Read(view, "_action");
            var batch = (System.Collections.Generic.IReadOnlyList<Abyss.Logic.Battle.BattleEvent>)Read(view, "_events");
            var end = batch.OfType<Abyss.Logic.Battle.ActionEndEvent>().First(e => e.Seq > start.Seq && e.ActorId == actor.Id);
            var damage = batch.OfType<Abyss.Logic.Battle.DamageEvent>().Where(e => e.SourceId == actor.Id && e.Seq > start.Seq && e.Seq < end.Seq).ToArray();
            Check("presented event targets equal actual damage sequence", damage.Length == 6 && start.TargetIds.SequenceEqual(damage.Select(e => e.TargetId)),
                new { seed, start = start.TargetIds.ToArray(), hits = damage.Select(e => new { e.TargetId, e.Amount, e.Killed }).ToArray() });
            Check("first kill followed by survivor hits", damage.Length == 6 && damage[0].Killed && damage.Skip(1).All(e => e.TargetId == engine.Enemies[1].Id));
            var displayTargets = (System.Collections.Generic.List<Abyss.Runtime.Battle.BattleDisplayUnit>)Call(view, "Targets", start);
            Check("actual BattleView target resolver retains retargeted survivor", displayTargets.Select(u => u.Id).SequenceEqual(start.TargetIds));
            object[] centerArgs = { start.TargetIds, Vector3.zero };
            bool hasCenter = (bool)Call(view, "AreaCenter", centerArgs);
            Check("actual AreaCenter resolves revised targets", hasCenter, centerArgs[1].ToString());
            var snapshot = start.TargetIds.ToArray(); await Snap("battle-random-action-start", size[0], size[1]);
            await Until(() => !view.Playing, "random skill playback completed");
            Check("snapshot stable through actual replay", start.TargetIds.SequenceEqual(snapshot));
            Check("battle remains ready after replay", engine.ActiveHero != null && view.CanOpenPause);
        });
    } catch (System.Exception e) { failed = true; issues.Add(new { phase, exception = e.ToString() }); }
    finally {
        try {
            if (testKeyboard != null) { Key(false); UnityEngine.InputSystem.InputSystem.RemoveDevice(testKeyboard); previousKeyboard?.MakeCurrent(); }
            if (disabledTown != null) disabledTown.enabled = true;
            if (physicsFixture != null) UnityEngine.Object.Destroy(physicsFixture);
            if (isolated) { app.SetPaused(false); typeof(Abyss.Runtime.GameApp).GetField("<Preferences>k__BackingField", flags).SetValue(app, originalPreferences); }
            Application.runInBackground = originalBackground;
            if (gameView != null && selectedSize != null) selectedSize.SetValue(gameView, originalSize);
            if (sizeGroup != null) for (int i = customSizes.Count - 1; i >= 0; i--) Call(sizeGroup, "RemoveCustomSize", customSizes[i]);
            if (lockRoot != null) UnityEngine.Object.Destroy(lockRoot);
        } catch (System.Exception e) { failed = true; issues.Add(new { phase = "cleanup", exception = e.ToString() }); }
        Application.logMessageReceived -= log;
        phase = "finished"; Report(failed ? "failed" : "automated-checks-passed-visual-review-required");
        System.IO.File.WriteAllText(System.IO.Path.Combine(outDir, "DONE"), failed ? "failed" : "visual-review-required");
    }
}
// eval_file supplies a trailing fallback return; keep it reachable if Play has ended before scheduling.
if (Application.isPlaying) {
    Report("scheduled");
    _ = Run();
    return "Astra world acceptance scheduled; poll " + System.IO.Path.Combine(outDir, "DONE") + " and inspect result.json + PNGs. No portrait claim; stop Play before normal gameplay.";
}
