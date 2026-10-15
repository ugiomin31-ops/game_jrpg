// Diagnostic only; parent invokes eval_file in Play. No GameApp, save, input or native OS calls.
// Runtime pacing is applied BEFORE requesting focus and restored on completion/Play exit.
var project = System.IO.Directory.GetParent(Application.dataPath).FullName;
if (!string.Equals(project, @"C:\Users\User\Desktop\GAME_JRPG\handoff-verify-20261015", System.StringComparison.OrdinalIgnoreCase))
    throw new System.InvalidOperationException("Wrong checkout for focus probe: " + project);
var outDir = System.IO.Path.Combine(project, "docs/verification/astra-enrichment-20261015/runtime/focus-probe-" + System.DateTime.UtcNow.ToString("yyyyMMdd-HHmmss-fff"));
System.IO.Directory.CreateDirectory(outDir);
var samples = new System.Collections.Generic.List<object>();
bool oldBackground = Application.runInBackground, beganInPlay = Application.isPlaying, done = false;
int oldTargetFps = Application.targetFrameRate, startFrame = Time.frameCount, lastFrame = startFrame, ticks = 0, advancingTicks = 0;
double focusedSince = -1, nextSample = 0;
int focusedStartFrame = startFrame;
UnityEditor.EditorWindow gameView = null;
var timer = System.Diagnostics.Stopwatch.StartNew();
object Snapshot(string label) {
    var window = UnityEditor.EditorWindow.focusedWindow;
    return new { label, elapsedSeconds = timer.Elapsed.TotalSeconds, editorTicks = ticks, advancingTicks,
        frame = Time.frameCount, framesSinceStart = Time.frameCount - startFrame, unscaledTime = Time.unscaledTime,
        applicationFocused = Application.isFocused, playing = Application.isPlaying, editorPlaying = UnityEditor.EditorApplication.isPlaying,
        paused = UnityEditor.EditorApplication.isPaused, compiling = UnityEditor.EditorApplication.isCompiling, updating = UnityEditor.EditorApplication.isUpdating,
        focusedWindowName = window == null ? null : window.name, focusedWindowTitle = window == null ? null : window.titleContent.text,
        focusedWindowType = window == null ? null : window.GetType().FullName, focusedWindowId = window == null ? 0 : window.GetInstanceID(),
        requestedGameViewId = gameView == null ? 0 : gameView.GetInstanceID(), gameViewSelected = gameView != null && window == gameView,
        runInBackground = Application.runInBackground, targetFrameRate = Application.targetFrameRate, vSyncCount = QualitySettings.vSyncCount,
        timeScale = Time.timeScale, captureDeltaTime = Time.captureDeltaTime };
}
void Save(string status, string reason, bool actualFocusPass, object final = null) {
    System.IO.File.WriteAllText(System.IO.Path.Combine(outDir, "result.json"), Newtonsoft.Json.JsonConvert.SerializeObject(new {
        status, reason, actualFocusPass, project, unity = Application.unityVersion, deadlineSeconds = 25,
        requestedModel = "gpt-6-astra", requestedEffort = "high", requestedTier = "Fast/priority", verifiedRouting = "not exposed",
        originalSettings = new { runInBackground = oldBackground, targetFrameRate = oldTargetFps },
        probeSettings = new { runInBackground = true, targetFrameRate = 20 },
        currentSettings = new { runInBackground = Application.runInBackground, targetFrameRate = Application.targetFrameRate },
        gameAppMutated = false, nativeWindowActivationAttempted = false, samples, final
    }, Newtonsoft.Json.Formatting.Indented));
}
void Finish(string status, string reason, bool pass) {
    if (done) return;
    done = true;
    var final = Snapshot("completion-before-pacing-restore"); samples.Add(final);
    UnityEditor.EditorApplication.update -= Poll;
    UnityEditor.EditorApplication.playModeStateChanged -= PlayState;
    Application.runInBackground = oldBackground; Application.targetFrameRate = oldTargetFps;
    Save(status, reason, pass, final);
    System.IO.File.WriteAllText(System.IO.Path.Combine(outDir, "DONE"), status);
}
void PlayState(UnityEditor.PlayModeStateChange state) {
    if (state == UnityEditor.PlayModeStateChange.ExitingPlayMode || state == UnityEditor.PlayModeStateChange.EnteredEditMode)
        Finish("stopped", "Play ended before a completed actual-focus observation.", false);
}
void Poll() {
    if (done) return;
    try {
        ticks++;
        if (Time.frameCount != lastFrame) { advancingTicks++; lastFrame = Time.frameCount; }
        double elapsed = timer.Elapsed.TotalSeconds;
        bool actual = Application.isFocused && gameView != null && UnityEditor.EditorWindow.focusedWindow == gameView
            && Application.isPlaying && !UnityEditor.EditorApplication.isPaused;
        if (actual) {
            if (focusedSince < 0) { focusedSince = elapsed; focusedStartFrame = Time.frameCount; samples.Add(Snapshot("actual-focus-observed")); }
        } else focusedSince = -1;
        if (elapsed >= nextSample) { samples.Add(Snapshot("editor-update")); nextSample = elapsed + .5; Save("running", "Observing real focus and independent editor/player progress.", false); }
        if (!beganInPlay || !Application.isPlaying) { Finish("not-in-play", "Run the diagnostic in Play; no GameApp call was made.", false); return; }
        if (elapsed >= 25) { Finish("timeout", "Actual application focus + selected GameView + advancing player frames were not sustained before the deadline. EditorWindow.Focus returning is not proof of OS focus.", false); return; }
        if (actual && elapsed - focusedSince >= .5 && Time.frameCount - focusedStartFrame >= 3)
            Finish("actual-focus-pass", "Real Application.isFocused and selected GameView held for at least 0.5s with at least three advancing player frames; this is a point-in-time preflight, not a broad-test pass.", true);
    } catch (System.Exception e) { Finish("error", e.ToString(), false); }
}
samples.Add(Snapshot("before-runtime-settings"));
Save("scheduled", "No focus claim; probe not yet observed.", false);
try {
    Application.runInBackground = true; Application.targetFrameRate = 20;
    samples.Add(Snapshot("runtime-settings-before-focus"));
    var viewType = typeof(UnityEditor.Editor).Assembly.GetType("UnityEditor.GameView");
    gameView = UnityEditor.EditorWindow.GetWindow(viewType);
    gameView.Focus(); gameView.Repaint();
    samples.Add(Snapshot("after-EditorWindow-Focus-returned"));
    UnityEditor.EditorApplication.update += Poll;
    UnityEditor.EditorApplication.playModeStateChanged += PlayState;
    Poll();
} catch (System.Exception e) { Finish("error", e.ToString(), false); }
// The eval wrapper appends a fallback return; leave that generated statement reachable.
if (System.IO.Directory.Exists(outDir)) return "Focus diagnostic: " + outDir + "; poll DONE/result.json. Only actual-focus-pass confirms the observed focus condition; pacing restores on completion.";
