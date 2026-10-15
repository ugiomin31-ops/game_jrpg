// Parent-only SERIAL Unity Pipeline eval_file; fresh Main Play at Title, no active campaign/other eval.
// unity command eval_file --file Tools/AstraUIContentAcceptance.eval.cs --timeout 20000
// Asynchronous: poll returned DONE in <=25-second slices, then inspect result.json and EVERY PNG.
// Authored DB assets + real widgets/presentation; QA progression/stock/position setup is disclosed below.
// This file does not certify pointer raycasts, natural progression, unseen regions, or visual acceptance.
// Parent: run true first; after a passing narrow result, set false and run the full fixture once.
const bool NarrowGearStory = true;
var project = System.IO.Directory.GetParent(Application.dataPath).FullName;
if (!Application.isPlaying || Abyss.Runtime.GameApp.Instance == null
    || !string.Equals(project, @"C:\Users\User\Desktop\GAME_JRPG\handoff-verify-20261015", System.StringComparison.OrdinalIgnoreCase)
    || UnityEngine.SceneManagement.SceneManager.GetActiveScene().name != "Main")
    throw new System.InvalidOperationException("Expected this checkout's Main scene already playing.");
var app = Abyss.Runtime.GameApp.Instance;
if (app.Screen != Abyss.Runtime.GameScreen.Title || app.State != null || app.Battle != null || app.Paused)
    throw new System.InvalidOperationException("Start a fresh Play session at Title. Do not run on a user's live campaign or a previous QA session.");
foreach (string busy in new[] { "AstraWorldAcceptance_BUSY", "AstraUIContentAcceptance_BUSY", "AstraAnimationRegression_BUSY" })
    if (GameObject.Find(busy) != null) throw new System.InvalidOperationException("Another fixture is active: " + busy);
var flags = System.Reflection.BindingFlags.Instance | System.Reflection.BindingFlags.Public | System.Reflection.BindingFlags.NonPublic;
// UIRoot.ReducedMotion is internal; eval_file compiles into a separate assembly.
var reducedMotionProperty = typeof(Abyss.UI.UIRoot).GetProperty("ReducedMotion", flags)
    ?? throw new System.MissingMemberException(typeof(Abyss.UI.UIRoot).FullName, "ReducedMotion");
if (reducedMotionProperty.PropertyType != typeof(bool) || reducedMotionProperty.GetGetMethod(true) == null
    || reducedMotionProperty.GetSetMethod(true) == null)
    throw new System.InvalidOperationException("Expected UIRoot's readable/writable bool ReducedMotion property.");
object Read(object target, string field) => (target.GetType().GetField(field, flags)
    ?? throw new System.MissingFieldException(target.GetType().FullName, field)).GetValue(target);
void Set(object target, string field, object value) => (target.GetType().GetField(field, flags)
    ?? throw new System.MissingFieldException(target.GetType().FullName, field)).SetValue(target, value);
object Call(object target, string name, params object[] args) {
    var methods = target.GetType().GetMethods(flags).Where(m => m.Name == name && m.GetParameters().Length == args.Length).ToArray();
    if (methods.Length != 1) throw new System.MissingMethodException(target.GetType().FullName, name + "/" + args.Length);
    return methods[0].Invoke(target, args);
}
string Json(object value) => Newtonsoft.Json.JsonConvert.SerializeObject(value, Newtonsoft.Json.Formatting.Indented);
string Hash(string path) {
    if (!System.IO.File.Exists(path)) return "missing";
    using (var hash = System.Security.Cryptography.SHA256.Create())
        return System.BitConverter.ToString(hash.ComputeHash(System.IO.File.ReadAllBytes(path))).Replace("-", "").ToLowerInvariant();
}
string Plain(string text) => System.Text.RegularExpressions.Regex.Replace(text ?? "", "<[^>]+>", "");
var outDir = System.IO.Path.Combine(project, "docs/verification/astra-enrichment-20261015/runtime/ui-content-" + System.DateTime.UtcNow.ToString("yyyyMMdd-HHmmss-fff"));
var qaSave = System.IO.Path.Combine(outDir, "qa-save");
var originalDirectory = (string)Read(app, "saveDirectory");
var originalRepository = app.Saves;
var originalPreferences = app.Preferences;
string originalPreferencesJson = Json(originalPreferences);
bool originalBackground = Application.runInBackground, originalReduced = (bool)reducedMotionProperty.GetValue(Abyss.UI.UIRoot.Instance);
float originalTimeScale = Time.timeScale;
int originalFrameRate = Application.targetFrameRate, originalVsync = QualitySettings.vSyncCount;
var originalFocus = UnityEditor.EditorWindow.focusedWindow;
System.Collections.Generic.Dictionary<string, string> SaveHashes() {
    var result = new System.Collections.Generic.Dictionary<string, string>();
    if (System.IO.Directory.Exists(originalDirectory))
        foreach (string file in System.IO.Directory.GetFiles(originalDirectory, "*", System.IO.SearchOption.TopDirectoryOnly).OrderBy(p => p))
            result.Add(System.IO.Path.GetFileName(file), Hash(file));
    return result;
}
var beforeSaves = SaveHashes(); // Hash only; never load a user campaign or copy its contents into the report.
var sourcePaths = new[] {
    "Tools/AstraUIContentAcceptance.eval.cs", "Tools/AstraWorldAcceptance.eval.cs",
    "Assets/_Game/Scripts/UI/Battle/BattleHUD.Menu.cs", "Assets/_Game/Scripts/UI/Screens/GameUI.Settings.cs",
    "Assets/_Game/Scripts/UI/Screens/GameUI.Party.cs", "Assets/_Game/Scripts/UI/Screens/GameStoryScreen.cs",
    "Assets/_Game/Scripts/Runtime/GameApp.cs", "Assets/_Game/Resources/Data/dungeon.json",
    "Assets/_Game/Resources/Data/skills.json", "Assets/_Game/Resources/Data/text_ko.json"
};
var sourceHashes = sourcePaths.ToDictionary(p => p, p => Hash(System.IO.Path.Combine(project, p)));
var build = new { project, unity = Application.unityVersion, scene = UnityEngine.SceneManagement.SceneManager.GetActiveScene().path,
    module = typeof(Abyss.Runtime.GameApp).Module.ModuleVersionId.ToString(), assemblySha256 = Hash(typeof(Abyss.Runtime.GameApp).Assembly.Location), sourceHashes };
var checks = new System.Collections.Generic.List<object>();
var images = new System.Collections.Generic.List<object>();
var issues = new System.Collections.Generic.List<object>();
var bypasses = new[] {
    "Fresh Title only. BeginReview adopts detached QA states; per-run saves/preferences isolate all transactions. No user campaign is adopted or rewritten; normal Title rendering may read save summaries.",
    "QA levels/resources/stock and main-story flags seed legal test states; they do not prove progression, balance, acquisition or TP accrual.",
    "Battle uses an authored mage and its learned skills against authored slimes, started through DungeonRun.StartBattle. No fake skill/menu description is supplied to Targets.",
    "Real UIList.Submit, UISlantButton.Click and UIButton.Click exercise callbacks; private paging/ShowGear and position setup bypass physical input/navigation.",
    "A pass-through submit observer counts real BattleView submissions and restores the original delegate. No command or cost is replaced.",
    "Rescue fixtures start on real authored event cells, call DungeonRun.Interact then GameApp.HandleDungeonStep; walking, encounter avoidance and other ten regions' rendering are not certified.",
    "Mirror skill is verified in the loaded DB only; no enemy AI execution, reflection/counter mechanic, or mirror battle rendering is certified.",
    "TMP glyph/clip checks and PNG dimensions are automated evidence, not a judgment of legibility, overlap, lighting or overall visual quality. Parent must review every PNG."
};
bool failed = false, isolated = false, restored = false, bodyCompleted = false;
string phase = "scheduled";
GameObject lockRoot = null;
UnityEditor.EditorWindow gameView = null;
System.Reflection.PropertyInfo selectedSize = null;
object sizeGroup = null;
int originalSize = -1;
var customSizes = new System.Collections.Generic.List<int>();
void Check(string name, bool pass, object detail = null) { checks.Add(new { phase, name, passed = pass, detail }); if (!pass) failed = true; }
void Require(bool pass, string name) { Check(name, pass); if (!pass) throw new System.InvalidOperationException(name); }
void Report(string status) {
    System.IO.File.WriteAllText(System.IO.Path.Combine(outDir, "result.json"), Json(new {
        status, scope = NarrowGearStory ? "gear-story-only" : "full", phase, build, qaSave, isolated, restored, bodyCompleted, checks, issues, images, bypasses,
        visualAccepted = false, requestedModel = "gpt-6-astra", requestedEffort = "high",
        requestedTier = "Fast/priority", observedModelEffort = "not independently exposed", verifiedTier = "not exposed" }));
}
void Phase(string name) { phase = name; Report("running"); }
async System.Threading.Tasks.Task Until(System.Func<bool> condition, string label, int seconds = 25) {
    var end = System.DateTime.UtcNow.AddSeconds(seconds);
    while (!condition()) {
        if (!Application.isPlaying || app == null) throw new System.InvalidOperationException("Play ended: " + label);
        if (System.DateTime.UtcNow > end) throw new System.TimeoutException(label);
        await System.Threading.Tasks.Task.Yield();
    }
}
async System.Threading.Tasks.Task Frames(int count) { int end = Time.frameCount + count; await Until(() => Time.frameCount >= end, "render frames"); }
async System.Threading.Tasks.Task Settle() { float end = Time.unscaledTime + .4f; await Until(() => Time.unscaledTime >= end, "widget debounce/transition"); await Frames(2); }
bool TransitionsClear() => !Abyss.UI.UIAreaCard.Active && !Abyss.UI.UIRoot.Instance.Fader.IsBusy && !Abyss.UI.UIRoot.Instance.Fader.IsOpaque;
async System.Threading.Tasks.Task WaitTransitions() {
    await Until(TransitionsClear, "area card fully swept out and fader clear"); await Frames(2);
    Require(TransitionsClear(), "no covering transition after render frames");
}
void Isolate() {
    Set(app, "saveDirectory", qaSave);
    Set(app, "<Saves>k__BackingField", new Abyss.Runtime.Persistence.SaveRepository(qaSave, app.DB));
    isolated = (string)Read(app, "saveDirectory") == qaSave && (string)Read(app.Saves, "directory") == qaSave;
    Require(isolated, "campaign and preference persistence isolated");
}
void Review(Abyss.Logic.Game.GameState state, int floor) {
    // BeginReview internally switches to review-campaign before adopting State; it performs no save itself.
    // Rebind immediately in finally, including when world initialization throws.
    if (state.FloorIndex != floor)
        state.Position = Abyss.Logic.Dungeon.DungeonGrid.Parse(app.DB.Floors[floor], state.Floor(app.DB.Floors[floor].Id)).Start;
    state.FloorIndex = floor; state.Location = Abyss.Logic.Game.GameLocation.Dungeon;
    Isolate();
    try { app.BeginReview(state, floor); } finally { Isolate(); }
}
Abyss.Logic.Game.GameState NewState() {
    var state = Abyss.Logic.Game.GameState.NewGame(app.DB, Abyss.Logic.Difficulty.Normal);
    Abyss.Logic.Game.GameFlow.CompletePrologue(state);
    foreach (string key in new[] { "first_town", "first_battle", "first_foe", "first_trap", "first_tp_full" })
        state.Flags.Add(Abyss.Logic.Game.GameFlow.TipFlag(key));
    for (int zone = 0; zone < 13; zone++) state.Flags.Add("biome_" + zone + "_seen");
    return state;
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
async System.Threading.Tasks.Task Size(int w, int h) {
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
    Call(sizeGroup, "AddCustomSize", ctor.Invoke(new object[] { System.Enum.ToObject(kind, 1), w, h, "Astra UI content temporary" }));
    customSizes.Add(index); selectedSize.SetValue(gameView, index);
    await Until(() => Screen.width == w && Screen.height == h, "GameView exact resolution"); await Frames(6);
}
async System.Threading.Tasks.Task Snap(string label, int w, int h) {
    await WaitTransitions();
    Require(Screen.width == w && Screen.height == h, "actual capture resolution " + label);
    Canvas.ForceUpdateCanvases(); await Frames(2);
    Require(TransitionsClear(), "capture unobstructed by transition: " + label);
    string path = System.IO.Path.Combine(outDir, label + "-" + w + "x" + h + ".png");
    ScreenCapture.CaptureScreenshot(path);
    await Frames(3); await Until(() => System.IO.File.Exists(path) && new System.IO.FileInfo(path).Length > 32, "PNG flush " + label);
    var bytes = System.IO.File.ReadAllBytes(path);
    int pw = (bytes[16] << 24) | (bytes[17] << 16) | (bytes[18] << 8) | bytes[19];
    int ph = (bytes[20] << 24) | (bytes[21] << 16) | (bytes[22] << 8) | bytes[23];
    Require(bytes[0] == 137 && bytes[1] == 80 && bytes[2] == 78 && bytes[3] == 71 && pw == w && ph == h, "valid PNG dimensions " + label);
    images.Add(new { label, path, width = pw, height = ph, bytes = bytes.Length, sha256 = Hash(path), frame = Time.frameCount, screen = app.Screen.ToString() });
    Report("running");
}
string Parsed(TMPro.TMP_Text text) {
    Canvas.ForceUpdateCanvases(); text.ForceMeshUpdate();
    return new string(text.textInfo.characterInfo.Take(text.textInfo.characterCount).Select(c => c.character).ToArray());
}
Rect GlyphInk(TMPro.TMP_CharacterInfo c) {
    // TMP quad corners include transparent SDF effect padding. Test the actual font glyph's ink bounds.
    var metrics = c.textElement.glyph.metrics;
    float left = c.origin + metrics.horizontalBearingX * c.scale;
    float top = c.baseLine + metrics.horizontalBearingY * c.scale;
    return new Rect(left, top - metrics.height * c.scale, metrics.width * c.scale, metrics.height * c.scale);
}
string GlyphProblem(TMPro.TMP_Text text, int i) {
    if (!TransitionsClear()) return "transition-overlay";
    if (!text.isActiveAndEnabled || text.canvasRenderer.cull || text.color.a < .01f) return "inactive/culled/transparent-label";
    if (text.GetComponentsInParent<CanvasGroup>().Any(g => g.alpha < .01f)) return "transparent-ancestor";
    var c = text.textInfo.characterInfo[i];
    if (!c.isVisible || c.color.a == 0 || i >= text.maxVisibleCharacters) return "character-not-rendered";
    if (c.textElement == null || c.textElement.glyph == null) return "missing-glyph";
    var ink = GlyphInk(c);
    if (ink.width <= 0 || ink.height <= 0) return "empty-ink-bounds";
    var canvas = text.canvas.rootCanvas;
    var camera = canvas.renderMode == RenderMode.ScreenSpaceOverlay ? null : canvas.worldCamera;
    var world = new[] { new Vector3(ink.xMin, ink.yMin), new Vector3(ink.xMin, ink.yMax),
        new Vector3(ink.xMax, ink.yMin), new Vector3(ink.xMax, ink.yMax) }.Select(p => text.transform.TransformPoint(p));
    foreach (var point in world) {
        var pixel = RectTransformUtility.WorldToScreenPoint(camera, point);
        if (pixel.x < 0 || pixel.y < 0 || pixel.x > Screen.width || pixel.y > Screen.height) return "ink-outside-screen";
        foreach (var mask in text.GetComponentsInParent<UnityEngine.UI.RectMask2D>()) {
            if (!mask.isActiveAndEnabled) continue;
            var rt = (RectTransform)mask.transform; var local = rt.InverseTransformPoint(point);
            var clip = rt.rect; var pad = mask.padding;
            if (local.x < clip.xMin + pad.x || local.x > clip.xMax - pad.z
                || local.y < clip.yMin + pad.y || local.y > clip.yMax - pad.w) return "ink-outside-mask:" + mask.name;
        }
    }
    return null;
}
bool GlyphVisible(TMPro.TMP_Text text, int i) => GlyphProblem(text, i) == null;
object GlyphEvidence(TMPro.TMP_Text text, int i) {
    var c = text.textInfo.characterInfo[i];
    return new { glyphIndex = i, sourceIndex = c.index, character = c.character.ToString(), code = (int)c.character,
        c.isVisible, problem = GlyphProblem(text, i), c.origin, c.baseLine, c.scale,
        quad = new[] { c.bottomLeft.x, c.bottomLeft.y, c.topRight.x, c.topRight.y },
        ink = c.textElement == null || c.textElement.glyph == null ? null : new[] { GlyphInk(c).xMin, GlyphInk(c).yMin, GlyphInk(c).xMax, GlyphInk(c).yMax } };
}
void TextProof(TMPro.TMP_Text text, string label, params string[] tokens) {
    Require(text != null && text.isActiveAndEnabled, label + " actual active TMP label");
    string parsed = Parsed(text);
    foreach (string token in tokens) {
        int at = parsed.IndexOf(token, System.StringComparison.Ordinal);
        // Parsed is built one-for-one from TMP characterInfo, never indexed into the rich-text source.
        var missing = at < 0 ? new int[0] : System.Linq.Enumerable.Range(at, token.Length)
            .Where(i => !char.IsWhiteSpace(text.textInfo.characterInfo[i].character) && !GlyphVisible(text, i)).ToArray();
        Check(label + " visible glyphs: " + token, at >= 0 && missing.Length == 0,
            new { parsed, token, missing = missing.Select(i => GlyphEvidence(text, i)).ToArray() });
    }
}
async System.Threading.Tasks.Task Reveal(UnityEngine.UI.ScrollRect scroll, TMPro.TMP_Text label, string token) {
    UnityEngine.UI.LayoutRebuilder.ForceRebuildLayoutImmediate(scroll.content); string parsed = Parsed(label);
    int at = parsed.IndexOf(token, System.StringComparison.Ordinal); Require(at >= 0, "scroll target exists: " + token);
    var c = label.textInfo.characterInfo[at];
    var local = scroll.viewport.InverseTransformPoint(label.transform.TransformPoint((c.bottomLeft + c.topRight) * .5f));
    float hidden = RectTransformUtility.CalculateRelativeRectTransformBounds(scroll.viewport, scroll.content).size.y - scroll.viewport.rect.height;
    scroll.StopMovement();
    if (hidden > .1f) scroll.verticalNormalizedPosition = Mathf.Clamp01(scroll.verticalNormalizedPosition - (scroll.viewport.rect.center.y - local.y) / hidden);
    await Frames(3);
}
async System.Threading.Tasks.Task ScrollProof(Abyss.UI.GameStoryScreen story, string expected, string name, int w, int h) {
    await WaitTransitions();
    Require(Abyss.UI.UIRoot.Instance.Screens.Top == story, name + " actual story remains top after transition");
    var body = (TMPro.TMP_Text)Read(story, "body"); var scroll = (UnityEngine.UI.ScrollRect)Read(story, "scroll");
    Parsed(body);
    if (body.maxVisibleCharacters < body.textInfo.characterCount) { ((Abyss.UI.UIButton)Read(story, "next")).Click(); await Settle(); }
    string parsed = Parsed(body); Require(parsed == expected, name + " actual story body equals authored content");
    var seen = new bool[parsed.Length];
    float hidden = Mathf.Max(0, scroll.content.rect.height - scroll.viewport.rect.height);
    int steps = Mathf.Max(1, Mathf.CeilToInt(hidden / Mathf.Max(1f, scroll.viewport.rect.height * .65f)));
    Require(steps <= 20, "bounded story scrolling");
    for (int i = 0; i <= steps; i++) {
        scroll.StopMovement(); scroll.verticalNormalizedPosition = 1f - i / (float)steps; await Frames(3); Parsed(body);
        for (int c = 0; c < parsed.Length; c++) seen[c] |= char.IsWhiteSpace(body.textInfo.characterInfo[c].character) || GlyphVisible(body, c);
        await Snap(name + "-page-" + i, w, h);
        if (hidden <= .1f) break;
    }
    Check(name + " every story glyph visible across captured scroll positions", seen.All(v => v), new { chars = parsed.Length, unseen = seen.Count(v => !v),
        missing = System.Linq.Enumerable.Range(0, seen.Length).Where(i => !seen[i]).Select(i => GlyphEvidence(body, i)).ToArray() });
}
Abyss.UI.GameMenuScreen Menu() {
    var menu = Abyss.UI.UIRoot.Instance.Screens.Top as Abyss.UI.GameMenuScreen;
    Require(menu != null, "actual GameMenuScreen on top"); return menu;
}
Abyss.UI.UIList List(Abyss.UI.GameMenuScreen menu) => (Abyss.UI.UIList)Read(menu, "list");
void SelectRow(Abyss.UI.GameMenuScreen menu, string label, bool submit) {
    var list = List(menu); int index = list.Items.ToList().FindIndex(r => Plain(r.Label) == label);
    Require(index >= 0 && list.Items[index].Enabled, "enabled real menu row: " + label);
    list.Select(index, false); if (submit) list.Submit();
}
async System.Threading.Tasks.Task HudPick(Abyss.UI.Battle.BattleHUD hud, string label) {
    var choices = (System.Collections.IList)Read(hud, "_choices");
    int index = System.Linq.Enumerable.Range(0, choices.Count).Where(i => (string)Read(choices[i], "Label") == label).DefaultIfEmpty(-1).First();
    Require(index >= 0, "actual HUD choice: " + label);
    int perPage = (int)Read(hud, "_perPage"), currentPage = (int)Read(hud, "_page");
    if (currentPage != index / perPage) Call(hud, "Page", index / perPage - currentPage);
    await Settle();
    var plates = (System.Collections.Generic.List<Abyss.UI.UISlantButton>)Read(hud, "_plates");
    Require(index % perPage < plates.Count && plates[index % perPage].Interactable, "real HUD button enabled");
    plates[index % perPage].Click(); await Settle();
}
// Exact expected regional content is frozen at authoring time, NOT read from the runtime DB to form the oracle.
var expectedRescues = new[] {
    new { Floor = "subway_2", X = 15, Y = 1, Gold = 100, Title = "마지막 유도등", Text = "꺼진 선로 끝에서 유도등 하나가 세 번 깜박였다. 탈진한 헌터가 마지막 승객의 이름을 출입 명부에서 지우지 못한 채 앉아 있었다. 우리는 그가 떨어뜨린 무전기를 건네고 응급 처치를 마쳤다. ‘모두 나갔다는 답을 들었어요. 이제 저도 돌아갈 수 있겠네요.’ 그는 감사의 표시로 비상금과 회복약을 건넸다." },
    new { Floor = "gate_e_2", X = 9, Y = 13, Gold = 200, Title = "가시 속의 씨앗 봉투", Text = "덩굴 회랑에서 가시에 옷이 걸린 헌터를 발견했다. 덩굴을 잘라 내자 그는 품속의 씨앗 봉투부터 살폈다. ‘여기에도 원래 꽃이 피었대요. 길드 화분에서라도 키워 보려고요.’ 상처를 감아 주니 헌터가 비상금과 회복약을 나누어 주었다." },
    new { Floor = "factory_2", X = 5, Y = 9, Gold = 300, Title = "놓지 못한 작업 장갑", Text = "마석 창고 선반 아래에 헌터의 작업 장갑이 끼어 있었다. 손을 빼낸 뒤에도 그는 장갑을 놓지 않았다. 손등 안쪽에는 먼저 철수한 동료들의 이름이 빼곡했다. 붕대를 감아 주자 그가 멋쩍게 웃었다. ‘값싼 장갑인데, 잃어버리면 혼나요.’ 그는 감사의 표시로 비상금과 회복약을 건넸다." },
    new { Floor = "gate_d_2", X = 7, Y = 1, Gold = 400, Title = "소매 속 손난로", Text = "얼음 창고에서 미끄러진 헌터가 벽에 기대 떨고 있었다. 발목을 고정해 주자 그가 소매 속의 다 식은 손난로를 꺼냈다. ‘따뜻할 때는 귀찮아서 빼 두었는데요.’ 헌터는 쑥스럽게 웃으며 비상금과 회복약으로 고마움을 전했다." },
    new { Floor = "cave_2", X = 9, Y = 11, Gold = 500, Title = "맥박 사이의 세 번", Text = "수정 기둥의 맥박 사이로 짧은 금속음이 세 번씩 들렸다. 게이트 맥 통로에 고립된 헌터가 칼집으로 벽을 두드리고 있었다. 다친 손을 감싸 주자 그가 안도의 숨을 내쉬었다. ‘저 소리에 묻힐까 봐 계속 박자를 바꿨어요.’ 헌터가 비상금과 회복약을 건넸다." },
    new { Floor = "gate_c_2", X = 11, Y = 17, Gold = 600, Title = "목소리 대신 호루라기", Text = "용암 협곡의 열기 속에서 희미한 호루라기 소리가 났다. 바위 그늘에 웅크린 헌터는 목이 쉬어 말도 잇지 못했다. 잠시 함께 쉬며 화상을 처치하자 그가 호루라기를 꼭 쥐었다. ‘다음에는 목부터 아끼려고요.’ 헌터는 비상금과 회복약을 내밀며 고개를 숙였다." },
    new { Floor = "school_2", X = 7, Y = 16, Gold = 700, Title = "교실 문 앞의 출석부", Text = "교실 문 앞에 주저앉은 헌터가 출석부를 꼭 안고 있었다. 텅 빈 복도에서 이름을 부르는 소리가 들릴 때마다 대답해야 할 것 같았다고 했다. 우리는 그를 진정시키고 다친 발목을 감쌌다. ‘적어도 제 이름은 제가 기억해야겠죠.’ 헌터는 출석부를 내려놓고 비상금과 회복약으로 감사를 전했다." },
    new { Floor = "gate_b_2", X = 1, Y = 23, Gold = 800, Title = "돌아갈 사람의 이름", Text = "납골실 벽감 앞에 부상당한 헌터가 앉아 있었다. 그는 낡은 면허증의 이름을 자기 수첩에 옮겨 적고 있었다. ‘돌아가면 이분들을 기억하는 사람이 있는지 찾아보려고요.’ 응급 처치를 마치자 헌터는 수첩을 품에 넣고 비상금과 회복약을 건넸다." },
    new { Floor = "hospital_2", X = 19, Y = 21, Gold = 900, Title = "멈춘 진료 순번", Text = "병동 복도의 의자 밑에서 헌터가 손을 흔들었다. 굴러다니는 링거대를 피해 숨다가 다리를 다쳤다고 했다. 상처를 감아 주자 그가 구겨진 번호표를 펴 보였다. ‘진료 차례를 기다리던 건 아닌데, 이것만 쥐고 있었네요.’ 헌터는 비상금과 회복약으로 감사를 전했다." },
    new { Floor = "gate_a_2", X = 15, Y = 19, Gold = 1000, Title = "진주빛을 세는 사람", Text = "진주 회랑에서 헌터가 천장의 불빛을 세고 있었다. 발을 다친 채 같은 진주를 몇 번이나 세었는지 모르겠다고 했다. 붕대를 감아 주며 말을 걸자 굳었던 표정이 풀렸다. ‘이번엔 빛 말고 사람 목소리를 따라가야겠어요.’ 헌터가 비상금과 회복약을 건넸다." },
    new { Floor = "guild_street_2", X = 11, Y = 13, Gold = 1100, Title = "내리지 못한 셔터", Text = "상가 골목의 반쯤 내려온 셔터 아래에 헌터가 끼어 있었다. 사냥개를 피해 들어가다 어깨를 다쳤다고 했다. 몸을 빼내고 처치해 주자 그가 깨진 간판을 올려다봤다. ‘어릴 때 여기서 운동화를 샀는데, 이런 데서 뵙네요.’ 헌터는 비상금과 회복약을 꺼내 감사를 전했다." },
    new { Floor = "gate_s_2", X = 15, Y = 5, Gold = 1200, Title = "벽 너머의 손짓", Text = "투명해지는 벽 앞에서 헌터가 허공에 손을 뻗고 있었다. 공허 너머에 동료가 보이는 것 같다고 했다. 우리는 그의 팔을 붙잡아 앉히고 다친 손을 감쌌다. ‘이번에는 잡히는 손이네요.’ 숨을 고른 헌터가 비상금과 회복약을 건넸다." },
};
const string ExpectedPostgame = "마지막 게이트가 닫힌 뒤, 심연 아래에서 붉은 게이트가 열렸다는 보고가 들어왔소. 쓰러뜨린 보스들의 메아리가 되살아나 기다린다 하오. 12-3 · 심연의 옥좌에서 아래층으로 내려가는 계단을 이용하면 붉은 게이트로 들어갈 수 있소.";
const string ExpectedMirror = "거울에 모은 마력으로 적 하나에게 무속성 마법 피해를 1회 줍니다.";
Application.LogCallback log = (message, stack, type) => {
    if (type == LogType.Error || type == LogType.Exception || type == LogType.Assert) {
        failed = true; issues.Add(new { phase, type = type.ToString(), message, stack });
    }
};
async System.Threading.Tasks.Task BattleChecks(int w, int h) {
    Phase("battle-target-cost-and-settings-" + w);
    var state = NewState(); var mage = state.Hero("h_seoa");
    foreach (var other in state.Party.ToArray()) if (other != mage) Abyss.Logic.Game.HunterRoster.Bench(state, other.Id);
    mage.Level = 30; mage.Hp = -1; mage.Mp = -1; mage.Tp = 100; state.Repair(app.DB);
    Review(state, 0);
    var request = (Abyss.Logic.Dungeon.DungeonBattleRequest)Call(app.Dungeon, "StartBattle", Abyss.Logic.BattleKind.Random,
        new System.Collections.Generic.List<string> { "slime", "slime" }, state.Position, state.Position, "", 1f);
    app.Preferences.AutoBattle = false; app.Preferences.BattleSpeed = 1f;
    app.BeginBattle(request.Setup);
    await Until(() => app.Battle != null && app.Battle.CanOpenPause && app.Battle.Engine.ActiveHero?.DefId == "h_seoa", "natural mage command turn");
    var view = app.Battle; var hud = view.GetComponent<Abyss.UI.Battle.BattleHUD>(); var engine = view.Engine; var actor = engine.ActiveHero;
    Require(engine.GetCommandOptions(actor).Skills.Any(s => s.Id == "fireball" && s.Usable), "authored learned fireball usable");
    Require(engine.GetCommandOptions(actor).Skills.Any(s => s.Id == "ult_meteor" && s.Usable), "authored learned meteor usable at seeded legal TP");
    var speed = (Abyss.UI.UISlantButton)Read(hud, "_speedButton");
    foreach (float expected in new[] { 1.5f, 2f, 1f }) {
        app.UI.ShowPause(); await Settle(); var pause = Menu();
        SelectRow(pause, app.DB.T("settings"), true); await Settle(); var settings = Menu();
        SelectRow(settings, "전투 속도", true);
        // Deliberately synchronous: no yield/frame/rebuild between the settings callback and label assertion.
        Check("speed label updates in same settings callback", app.Preferences.BattleSpeed == expected && speed.Label.text == $"속도 {expected:0.#}x", speed.Label.text);
        Check("speed preference persisted only to QA directory", (string)Read(app, "saveDirectory") == qaSave
            && Abyss.Runtime.Persistence.GamePreferences.Read(qaSave).BattleSpeed == expected);
        await Settle(); settings.Close(); await Settle(); pause.Close(); await Settle();
        TextProof(speed.Label, "resumed speed", $"속도 {expected:0.#}x");
        await Snap("battle-settings-speed-" + expected.ToString("0.#", System.Globalization.CultureInfo.InvariantCulture), w, h);
    }
    int accepted = 0;
    var originalSubmit = (System.Func<Abyss.Logic.Battle.BattleCommand, bool>)Read(hud, "_submit");
    Set(hud, "_submit", new System.Func<Abyss.Logic.Battle.BattleCommand, bool>(command => { bool ok = originalSubmit(command); if (ok) accepted++; return ok; }));
    string CombatSnapshot() => Json(new { units = engine.Units.Select(u => new { u.Id, u.Hp, u.Mp, u.Tp, u.Shield }).ToArray(), rng = Read(engine.Rng, "_state") });
    try {
        string before = CombatSnapshot();
        await HudPick(hud, "스킬"); await HudPick(hud, app.DB.Skills["fireball"].DisplayName);
        var description = (TMPro.TMP_Text)Read(hud, "_description");
        TextProof(description, "single target confirmation cost/element", "MP 6", "화염");
        await Snap("battle-fireball-target", w, h);
        var targets = (System.Collections.Generic.List<Abyss.UI.UISlantButton>)Read(hud, "_plates");
        Require(targets.Count >= 2, "two actual target buttons"); targets[1].Click(); await Settle();
        TextProof(description, "changed target keeps cost/element", "MP 6", "화염");
        Check("first target click previews without command/resource/RNG mutation", accepted == 0 && before == CombatSnapshot());
        await Snap("battle-fireball-target-preview", w, h);
        Call(hud, "Back"); await Settle(); Call(hud, "Back"); await Settle();
        Check("cancel keeps resource and RNG state", accepted == 0 && before == CombatSnapshot());
        await HudPick(hud, "궁극기"); await HudPick(hud, app.DB.Skills["ult_meteor"].DisplayName);
        TextProof(description, "group confirmation cost/element", "TP 100", "화염");
        await Snap("battle-meteor-group-confirmation", w, h);
        Call(hud, "Back"); await Settle(); Call(hud, "Back"); await Settle();
        await HudPick(hud, "공격");
        Check("attack target does not inherit previous skill cost", !Plain(description.text).Contains("TP 100") && !Plain(description.text).Contains("MP 6"));
        Call(hud, "Back"); await Settle();
        await HudPick(hud, "스킬"); await HudPick(hud, app.DB.Skills["fireball"].DisplayName);
        targets = (System.Collections.Generic.List<Abyss.UI.UISlantButton>)Read(hud, "_plates");
        targets[0].Click(); await Settle(); TextProof(description, "armed confirmation", "MP 6", "화염");
        await Snap("battle-fireball-armed", w, h);
        int mp = actor.Mp; var targetButton = targets[0]; targetButton.Click();
        Check("second target click commits once", accepted == 1);
        Check("real engine spends fireball MP once", actor.Mp == mp - 6, new { before = mp, after = actor.Mp });
        // Same target callback after commit is guarded by HUD input lock, not an artificial mock result.
        Call(hud, "PointerSelect", 0);
        Check("duplicate target callback cannot commit twice", accepted == 1 && actor.Mp == mp - 6);
        await Until(() => !view.Playing, "committed fireball playback completes");
    } finally { if (hud != null) Set(hud, "_submit", originalSubmit); }
}
async System.Threading.Tasks.Task GearChecks(int w, int h) {
    Phase("party-gear-bonuses-" + w);
    var state = NewState(); state.EquipmentBag["acc_exp_charm"] = 2; state.EquipmentBag["acc_gold_charm"] = 2;
    Review(state, 0); app.EnterTown(); await Until(() => app.Screen == Abyss.Runtime.GameScreen.Town && !app.UI.BlocksWorldInput && TransitionsClear(), "QA town for gear");
    var hero = state.Party[0];
    foreach (string worn in new[] { "acc_exp_charm", "acc_gold_charm" }) {
        Require(Abyss.Logic.Game.PartyStats.Equip(app.DB, state, hero.Id, worn).Success, "production equip seeds authored accessory: " + worn);
        Call(app.UI, "ShowGear", hero, "accessory"); await Settle(); var menu = Menu();
        var details = (TMPro.TMP_Text)Read(menu, "details"); var scroll = (UnityEngine.UI.ScrollRect)Read(menu, "detailScroll");
        SelectRow(menu, app.DB.T("remove"), false); await Frames(3);
        TextProof(details, "unequip verdict", "능력 하락 ↓"); await Snap(worn + "-remove-verdict", w, h);
        string field = worn == "acc_exp_charm" ? "획득 경험치 보너스" : "획득 보상금 보너스 (파티 합산 최대 +100%)";
        string rate = worn == "acc_exp_charm" ? "30" : "25";
        await Reveal(scroll, details, field);
        TextProof(details, "unequip bonus comparison", field, rate + "% → 0%", "(-" + rate + "%p)");
        await Snap(worn + "-remove-bonus", w, h);
        // Actual confirmation/cancel, while clock is frozen so serialized state is comparable.
        app.SetPaused(true); string unchanged = Abyss.Logic.Game.SaveCodec.Serialize(state);
        List(menu).Submit(); await Settle(); var modal = Abyss.UI.UIRoot.Instance.Modals.Top as Abyss.UI.UIModal;
        Require(modal != null && Plain(modal.Message.text).Contains(field), "actual equipment confirmation retains bonus details");
        modal.GetComponentsInChildren<Abyss.UI.UIButton>().Single(b => b.Label.text == "취소").Click(); await Settle();
        Check("equipment cancellation keeps campaign unchanged", unchanged == Abyss.Logic.Game.SaveCodec.Serialize(state)); app.SetPaused(false);
        if (worn == "acc_exp_charm") {
            SelectRow(menu, app.DB.Equipment["acc_gold_charm"].DisplayName, false); await Frames(3);
            Check("EXP to gold charm row reports tradeoff", List(menu).Selected.Cost == "장단점 교환");
            foreach (string token in new[] { "획득 경험치 보너스", "획득 보상금 보너스 (파티 합산 최대 +100%)" }) {
                await Reveal(scroll, details, token);
                bool exp = token == "획득 경험치 보너스";
                TextProof(details, "charm swap delta", token, exp ? "30% → 0%" : "0% → 25%", exp ? "(-30%p)" : "(+25%p)");
                await Snap(exp ? "gear-swap-exp" : "gear-swap-gold", w, h);
            }
            SelectRow(menu, app.DB.Equipment["acc_exp_charm"].DisplayName, false); await Frames(3);
            Check("same accessory reports identical ability", List(menu).Selected.Cost == "동일 능력");
        }
        menu.Close(); await Settle();
    }
}
async System.Threading.Tasks.Task RescueChecks(string floorId, int w, int h) {
    Phase("rescue-" + floorId + "-" + w);
    int floor = app.DB.Floors.FindIndex(f => f.Id == floorId); Require(floor >= 0, "representative authored floor exists");
    var row = app.DB.Floors[floor].Events.Single(e => e.IsRescue);
    var state = NewState(); state.FloorIndex = state.DeepestFloor = floor; state.Location = Abyss.Logic.Game.GameLocation.Dungeon;
    state.Position = Abyss.Logic.Dungeon.GridPos.FromArray(row.Cell); state.Facing = Abyss.Logic.Dungeon.Facing.East;
    Review(state, floor); await Frames(5);
    Require(state.Position == Abyss.Logic.Dungeon.GridPos.FromArray(row.Cell), "actual authored rescue cell");
    int gold = state.Gold, potions = state.ItemCount("healing_potion");
    var result = app.Dungeon.Interact();
    Require(result.Effect == Abyss.Logic.Dungeon.DungeonEffect.Rescue && object.ReferenceEquals(result.Event, row), "production Interact resolves authored rescue");
    Call(app, "HandleDungeonStep", result); await Settle();
    var story = Abyss.UI.UIRoot.Instance.Screens.Top as Abyss.UI.GameStoryScreen;
    Require(story != null && story.Title == row.Title && story.Pages.Count == 1 && story.Pages[0] == row.Text, "real rescue story receives exact event content");
    Check("rescue rewards committed once before story", state.Gold == gold + row.Reward.Gold && state.ItemCount("healing_potion") == potions + 1);
    var persisted = app.Saves.Read(-1);
    Check("QA autosave records reward and spent cell before story", persisted.Gold == state.Gold && persisted.Floor(floorId).SpentEvents.Contains(state.Position));
    await ScrollProof(story, row.Text, "rescue-" + floorId + "-story", w, h);
    await Settle(); ((Abyss.UI.UIButton)Read(story, "next")).Click(); await Settle(); await Settle();
    var loot = Abyss.UI.UIRoot.Instance.Modals.Top as Abyss.UI.UILootPopup;
    Require(loot != null && app.Screen == Abyss.Runtime.GameScreen.Dungeon, "real story completion opens event reward popup");
    Check("reward popup uses actual reward", (int)Read(loot, "_gold") == row.Reward.Gold);
    var rewardText = loot.GetComponentsInChildren<TMPro.TMP_Text>().FirstOrDefault(t => Plain(t.text).Contains(app.DB.Items["healing_potion"].DisplayName));
    TextProof(rewardText, "actual rescue item rendered", app.DB.Items["healing_potion"].DisplayName);
    await Snap("rescue-" + floorId + "-reward", w, h); loot.Close(); await Settle();
    int paid = state.Gold; int owned = state.ItemCount("healing_potion");
    var again = app.Dungeon.Interact();
    Check("spent rescue cannot pay again", again.Effect != Abyss.Logic.Dungeon.DungeonEffect.Rescue && paid == state.Gold && owned == state.ItemCount("healing_potion"));
}
async System.Threading.Tasks.Task PostgameChecks(int w, int h) {
    Phase("postgame-notice-" + w);
    var state = NewState();
    for (int zone = 1; zone <= 12; zone++) { state.Flags.Add(Abyss.Logic.Game.GameFlow.BossFlag(zone)); state.Flags.Add("elder_" + zone + "_seen"); }
    Abyss.Logic.Game.HunterRoster.SyncStoryJoins(app.DB, state); // Seed earned joins so the notice under test is the only unread one.
    state.Flags.Add(Abyss.Logic.Game.GameFlow.FlagCleared); state.Flags.Add(Abyss.Logic.Game.GameFlow.FlagEndingSeen);
    state.DeepestFloor = 35;
    Review(state, 35); app.EnterTown();
    await Until(() => Abyss.UI.UIRoot.Instance.Screens.Top is Abyss.UI.GameStoryScreen && TransitionsClear(), "real postgame notice after town card has left"); await Settle();
    var story = (Abyss.UI.GameStoryScreen)Abyss.UI.UIRoot.Instance.Screens.Top;
    Require(story.Pages.Count == 1 && story.Pages[0] == ExpectedPostgame, "actual postgame story uses corrected stair hint");
    await ScrollProof(story, ExpectedPostgame, "postgame-stair-hint", w, h);
    ((Abyss.UI.UIButton)Read(story, "next")).Click(); await Settle();
    Check("postgame notice completes in town and is marked seen", app.Screen == Abyss.Runtime.GameScreen.Town && state.Flags.Contains(Abyss.Logic.Game.GameFlow.FlagPostgameNotice));
}
async System.Threading.Tasks.Task Run() {
    await System.Threading.Tasks.Task.Yield(); Application.logMessageReceived += log;
    try {
        Phase("isolation"); Isolate();
        Set(app, "<Preferences>k__BackingField", Newtonsoft.Json.JsonConvert.DeserializeObject<Abyss.Runtime.Persistence.GamePreferences>(originalPreferencesJson));
        app.Preferences.AutoBattle = false; app.Preferences.BattleSpeed = 1f; app.Preferences.ReducedMotion = false; app.Preferences.TextSpeed = 42;
        reducedMotionProperty.SetValue(Abyss.UI.UIRoot.Instance, false); Application.runInBackground = true;
        FocusGameView(); await Until(() => Application.isFocused && UnityEditor.EditorWindow.focusedWindow == gameView, "actual focused GameView", 10);
        if (!NarrowGearStory) {
        Phase("exact-loaded-content"); Require(expectedRescues.Length == 12, "exactly twelve regional content contracts");
        foreach (var expected in expectedRescues) {
            var floor = app.DB.Floors.Single(f => f.Id == expected.Floor); var rows = floor.Events.Where(e => e.IsRescue).ToArray();
            Require(rows.Length == 1, "one regional rescue: " + expected.Floor); var row = rows[0];
            Check("exact regional content: " + expected.Floor, row.Title == expected.Title && row.Text == expected.Text
                && row.Cell.SequenceEqual(new[] { expected.X, expected.Y }) && floor.Rows[expected.Y][expected.X] == 'E'
                && row.Group.Count == 0 && row.Reward.Gold == expected.Gold && row.Reward.Equipment.Count == 0
                && row.Reward.Items.Count == 1 && row.Reward.Items.TryGetValue("healing_potion", out int n) && n == 1,
                new { expected, actualTitle = row.Title, actualText = row.Text, row.Cell, row.Reward });
        }
        Check("all floor/rescue counts preserved", app.DB.Floors.Count == 39 && app.DB.Floors.Sum(f => f.Events.Count(e => e.IsRescue)) == 13);
        Check("exact postgame hint and actual adjacent stair destination", app.DB.T("postgame_unlocked") == ExpectedPostgame
            && app.DB.Floors[35].Id == "gate_s_3" && app.DB.Floors[35].Rows.Any(r => r.Contains(">")) && app.DB.Floors[36].Id == "red_gate_1");
        var mirror = app.DB.Skills["sk_e_mirror_strike"];
        Check("mirror text describes its authored single magic hit", mirror.DisplayName == "거울 마탄" && mirror.Description == ExpectedMirror
            && mirror.Kind == Abyss.Logic.SkillKind.Damage && mirror.ScalingStat == Abyss.Logic.ScalingStat.Magic
            && mirror.TargetType == Abyss.Logic.TargetType.Enemy && mirror.Scope == Abyss.Logic.Scope.Single
            && mirror.Element == Abyss.Logic.Element.None && mirror.HitCount == 1 && Mathf.Abs(mirror.Power - 1.5f) < .0001f
            && mirror.MpCost == 6 && mirror.TpCost == 0,
            new { mirror.Id, mirror.DisplayName, mirror.Description, mirror.MpCost, mirror.TpCost });
        }
        foreach (var size in new[] { new[] { 1280, 720 }, new[] { 915, 412 } }) {
            await Size(size[0], size[1]);
            if (!NarrowGearStory) await BattleChecks(size[0], size[1]);
            await GearChecks(size[0], size[1]);
            foreach (string representative in new[] { "subway_2", "school_2" }) await RescueChecks(representative, size[0], size[1]);
            await PostgameChecks(size[0], size[1]);
        }
        bodyCompleted = true;
    } catch (System.Exception e) { failed = true; issues.Add(new { phase, exception = e.ToString() }); }
    finally {
        phase = "restore";
        // Restore routing only AFTER QA callbacks/world/state are gone. On any failure, leave QA persistence isolated.
        try {
            if (app != null && isolated) {
                app.UI.Clear(); app.ShowTitle(); await Frames(3);
                Set(app, "<State>k__BackingField", null); Set(app, "<Dungeon>k__BackingField", null);
                Set(app, "<Preferences>k__BackingField", originalPreferences); originalPreferences.Apply();
                reducedMotionProperty.SetValue(Abyss.UI.UIRoot.Instance, originalReduced);
                Require(app.Screen == Abyss.Runtime.GameScreen.Title && app.State == null && app.Battle == null, "QA world/state removed before restoring persistence");
                Set(app, "<Saves>k__BackingField", originalRepository); Set(app, "saveDirectory", originalDirectory);
                app.UI.ShowTitle();
                restored = object.ReferenceEquals(app.Saves, originalRepository) && object.ReferenceEquals(app.Preferences, originalPreferences)
                    && (string)Read(app, "saveDirectory") == originalDirectory && Json(app.Preferences) == originalPreferencesJson;
                Check("original Title/save routing/preferences restored", restored);
            }
        } catch (System.Exception e) { failed = true; issues.Add(new { phase = "restore-app", exception = e.ToString() }); }
        try {
            Application.runInBackground = originalBackground; Time.timeScale = originalTimeScale;
            Application.targetFrameRate = originalFrameRate; QualitySettings.vSyncCount = originalVsync;
            if (gameView != null && selectedSize != null && originalSize >= 0) selectedSize.SetValue(gameView, originalSize);
            if (sizeGroup != null) for (int i = customSizes.Count - 1; i >= 0; i--) Call(sizeGroup, "RemoveCustomSize", customSizes[i]);
            if (originalFocus != null) originalFocus.Focus();
        } catch (System.Exception e) { failed = true; issues.Add(new { phase = "restore-gameview", exception = e.ToString() }); }
        try {
            var afterSaves = SaveHashes();
            Check("original user-save directory byte hashes unchanged", beforeSaves.Count == afterSaves.Count && beforeSaves.All(kv => afterSaves.TryGetValue(kv.Key, out string value) && value == kv.Value), new { beforeSaves, afterSaves });
            Check("captured source set unchanged during run", sourcePaths.All(p => sourceHashes[p] == Hash(System.IO.Path.Combine(project, p))));
        } catch (System.Exception e) { failed = true; issues.Add(new { phase = "preservation-proof", exception = e.ToString() }); }
        Application.logMessageReceived -= log;
        if (lockRoot != null) UnityEngine.Object.Destroy(lockRoot);
        phase = "finished";
        string status = failed || !restored || !bodyCompleted ? "failed" : NarrowGearStory
            ? "narrow-checks-passed-visual-review-required" : "automated-checks-passed-visual-review-required";
        Report(status); System.IO.File.WriteAllText(System.IO.Path.Combine(outDir, "DONE"), status);
    }
}
System.IO.Directory.CreateDirectory(outDir);
lockRoot = new GameObject("AstraUIContentAcceptance_BUSY");
if (Application.isPlaying) {
    Report("scheduled"); _ = Run();
    return "Astra UI/content acceptance scheduled. Poll " + System.IO.Path.Combine(outDir, "DONE") + "; inspect result.json and every PNG. Fresh Title/save route is restored in finally; no visual pass is automatic.";
}
