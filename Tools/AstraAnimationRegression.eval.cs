// Unity Pipeline: eval_file --file Tools/AstraAnimationRegression.eval.cs
// Statements/local functions, no NUnit or test assembly. Parent runs serially in Play mode.
// Synchronous, bounded; returns JSON. Only temporary objects are mutated, all cleaned in finally.
var flags = System.Reflection.BindingFlags.Instance | System.Reflection.BindingFlags.Public | System.Reflection.BindingFlags.NonPublic;
var roots = new System.Collections.Generic.List<GameObject>();
var clips = new System.Collections.Generic.List<AnimationClip>();
var checks = new System.Collections.Generic.List<object>();
var issues = new System.Collections.Generic.List<object>();
var skippedCases = new System.Collections.Generic.List<string>();
var originalApp = Abyss.Runtime.GameApp.Instance;
bool error = false;
int completedCases = 0, completedEntryCases = 0;
string currentCase = "preconditions";
void Check(string name, bool passed, object detail = null) {
    checks.Add(new { test = currentCase, name, passed, detail });
    if (!passed) error = true;
}
void Case(string name, System.Action run) {
    currentCase = name;
    try { run(); completedCases++; }
    catch (System.Exception e) { error = true; issues.Add(new { test = name, exception = e.ToString() }); }
}
object Read(object target, string field) => target.GetType().GetField(field, flags).GetValue(target);
void Write(object target, string field, object value) => target.GetType().GetField(field, flags).SetValue(target, value);
GameObject Root(string name, bool active = true) {
    var go = new GameObject("Astra animation eval: " + name);
    roots.Add(go); go.SetActive(active); return go;
}
AnimationClip Clip(string name, bool loop, float length = 1.5f) {
    var clip = new AnimationClip { name = name, frameRate = 30f };
    clips.Add(clip);
    clip.SetCurve("Body", typeof(Transform), "localPosition.x", AnimationCurve.Linear(0f, 0f, length, 1f));
    var settings = UnityEditor.AnimationUtility.GetAnimationClipSettings(clip);
    settings.loopTime = loop;
    UnityEditor.AnimationUtility.SetAnimationClipSettings(clip, settings);
    return clip;
}
Abyss.Runtime.Art.CharacterModel Model(string name) {
    var root = Root(name);
    var visual = new GameObject("Visual"); visual.transform.SetParent(root.transform, false);
    new GameObject("Body").transform.SetParent(visual.transform, false);
    visual.AddComponent<Animator>();
    var model = root.AddComponent<Abyss.Runtime.Art.CharacterModel>();
    var takes = new[] { Clip("Idle", true), Clip("BattleIdle", true), Clip("Attack", false), Clip("Die", false, 7f) };
    typeof(Abyss.Runtime.Art.CharacterModel).GetMethod("Setup", flags).Invoke(model,
        new object[] { "astra-eval", visual.transform, takes, false, false, false });
    var anim = (Abyss.Runtime.Art.ClipAnimator)model.Anim;
    Graph(anim).SetTimeUpdateMode(UnityEngine.Playables.DirectorUpdateMode.Manual);
    Write(anim, "_phase", .9f); anim.RestClip = "BattleIdle"; anim.Play("Attack", 0f);
    return model;
}
UnityEngine.Playables.PlayableGraph Graph(Abyss.Runtime.Art.ClipAnimator anim) =>
    (UnityEngine.Playables.PlayableGraph)Read(anim, "_graph");
float Elapsed(System.Collections.IEnumerator routine) {
    foreach (var field in routine.GetType().GetFields(flags))
        if (field.Name.StartsWith("<elapsed>") && field.FieldType == typeof(float)) return (float)field.GetValue(routine);
    throw new System.MissingFieldException("DeathRoutine elapsed state (compiler-generated field)");
}
void FinishHitStop(System.Collections.IEnumerator stop) {
    var wait = stop.Current as System.Collections.IEnumerator;
    if (wait == null) throw new System.InvalidOperationException("HitStop did not yield its real Wait routine");
    bool waiting = true;
    for (int i = 0; i < 32 && waiting; i++) waiting = wait.MoveNext();
    if (waiting) throw new System.TimeoutException("HitStop Wait exceeded 32 manual steps");
    Check("HitStop completes", !stop.MoveNext());
}
Application.LogCallback log = (message, stack, type) => {
    if (type == LogType.Error || type == LogType.Exception || type == LogType.Assert) {
        error = true; issues.Add(new { test = currentCase, type = type.ToString(), message, stack });
    }
};
Application.logMessageReceived += log;
try {
    // Entry assertions and manual graph evaluation do not depend on the current frame delta.
    Check("Play mode", Application.isPlaying);
    if (Application.isPlaying) {
        float fade = Abyss.Runtime.Art.ClipAnimator.ReturnFade;
        var entries = new[] { new[] { 1f, 1f, fade }, new[] { 1f, 2f, fade }, new[] { 1f, 0f, fade },
            new[] { 1.6f, 1f, fade }, new[] { 1f, 1f, 0f } };
        for (int i = 0; i < entries.Length; i++) {
            var values = entries[i];
            Case("entry-" + (i + 1), () => {
                var anim = (Abyss.Runtime.Art.ClipAnimator)Model(currentCase).Anim;
                anim.SetLoopBlend("BattleIdle", .3f); anim.SetClipRate("BattleIdle", values[0]);
                anim.SetSpeed(values[1]); anim.Play("Idle", values[2]);
                float remaining = (1f - anim.NormalizedTime) * anim.Length("BattleIdle") / values[0];
                Check("resolved rest clip", anim.CurrentClip == "BattleIdle");
                Check("incoming and seam fades fit", remaining >= values[2] + .3f - .00001f,
                    new { clipRate = values[0], battleSpeed = values[1], fade = values[2], remaining });
                Check("nonzero unit phase", anim.NormalizedTime > 0f);
            });
        }
        Case("explicit-start", () => {
            var anim = (Abyss.Runtime.Art.ClipAnimator)Model(currentCase).Anim;
            anim.SetLoopBlend("BattleIdle", .3f); anim.PlayFrom("BattleIdle", .9f, fade, null);
            Check("explicit phase preserved", Mathf.Abs(anim.NormalizedTime - .9f) < .00001f, anim.NormalizedTime);
        });
        Case("uncorrected-loop", () => {
            var anim = (Abyss.Runtime.Art.ClipAnimator)Model(currentCase).Anim;
            anim.Play("Idle", fade);
            Check("ordinary phase preserved", Mathf.Abs(anim.NormalizedTime - .9f) < .00001f, anim.NormalizedTime);
        });
        Case("distinct-phases", () => {
            var anim = (Abyss.Runtime.Art.ClipAnimator)Model(currentCase).Anim;
            anim.SetLoopBlend("BattleIdle", .3f); anim.Play("Idle", fade);
            float later = anim.NormalizedTime;
            anim.Play("Attack", 0f); Write(anim, "_phase", .2f); anim.Play("Idle", fade);
            Check("phase variety preserved", anim.NormalizedTime > 0f && anim.NormalizedTime < later,
                new { earlier = anim.NormalizedTime, later });
        });
        completedEntryCases = completedCases;
        Check("all eight entry cases completed", completedEntryCases == 8, completedEntryCases);
        Case("actual-playable-output", () => {
            var model = Model(currentCase); var anim = (Abyss.Runtime.Art.ClipAnimator)model.Anim;
            var graph = Graph(anim); var body = model.Visual.Find("Body");
            Check("valid graph with output", graph.IsValid() && graph.GetOutputCount() > 0);
            graph.Evaluate(0f);
            float before = anim.NormalizedTime; var pose = body.localPosition;
            graph.Evaluate(.1f);
            Check("real clip time advances", anim.NormalizedTime > before);
            Check("real transform curve evaluated", (body.localPosition - pose).sqrMagnitude > .00000001f);
            anim.SetSpeed(0f); before = anim.NormalizedTime; pose = body.localPosition;
            graph.Evaluate(.1f);
            Check("zero speed freezes graph time and pose", Mathf.Abs(anim.NormalizedTime - before) < .00001f &&
                (body.localPosition - pose).sqrMagnitude < .00000001f);
        });
        // QA deliberately runs at 20 fps. At up to .1 s/frame, one 2x death step is at most .2 s.
        // Gate only death cases; always retain the eight entry results and real graph result above.
        bool deathFrame = Time.unscaledDeltaTime >= .001f && Time.unscaledDeltaTime <= .1f;
        Check("death-only frame bound", deathFrame, new { Time.deltaTime, Time.unscaledDeltaTime });
        if (!deathFrame) { skippedCases.Add("death-hitstop-1"); skippedCases.Add("death-hitstop-2"); }
        else foreach (float speed in new[] { 1f, 2f }) Case("death-hitstop-" + speed, () => {
            // Never activate this GameApp: its Awake would initialize singleton/persistence/UI.
            var host = Root(currentCase, false);
            var app = host.AddComponent<Abyss.Runtime.GameApp>();
            var preferences = new Abyss.Runtime.Persistence.GamePreferences { BattleSpeed = speed, ReducedMotion = false };
            Write(app, "<Preferences>k__BackingField", preferences);
            var view = host.AddComponent<Abyss.Runtime.Battle.BattleView>(); Write(view, "_app", app);
            float actualStep = (float)view.GetType().GetProperty("Dt", flags).GetValue(view);
            var constants = System.Reflection.BindingFlags.Static | System.Reflection.BindingFlags.NonPublic;
            float vfxAt = (float)view.GetType().GetField("DeathDissolveAt", constants).GetRawConstantValue();
            float reducedFade = (float)view.GetType().GetField("ReducedDeathDissolve", constants).GetRawConstantValue();
            bool beforeBeats = actualStep > 0f && actualStep < vfxAt && actualStep < reducedFade;
            Check("one actual death step fits before VFX and reduced fade completion", beforeBeats,
                new { speed, actualStep, vfxAt, reducedFade });
            if (!beforeBeats) throw new System.InvalidOperationException("Death step would cross an unconfigured VFX/completion beat");
            var camera = host.AddComponent<Camera>();
            var units = (System.Collections.Generic.Dictionary<string, Abyss.Runtime.Battle.BattleDisplayUnit>)Read(view, "_units");
            Write(view, "_director", new Abyss.Runtime.Battle.BattleCameraDirector(camera, host.transform, null, units.Values));
            var model = Model(currentCase); var anim = (Abyss.Runtime.Art.ClipAnimator)model.Anim;
            var unit = new Abyss.Runtime.Battle.BattleDisplayUnit { Id = "eval-enemy", Model = model,
                Side = Abyss.Logic.Battle.BattleSide.Enemy, Facing = Quaternion.identity, Alive = false };
            units.Add(unit.Id, unit);
            var stopMethod = view.GetType().GetMethod("HitStop", flags);
            var deathMethod = view.GetType().GetMethod("DeathRoutine", flags);
            var stop = (System.Collections.IEnumerator)stopMethod.Invoke(view, new object[] { .01f });
            var death = (System.Collections.IEnumerator)deathMethod.Invoke(view, new object[] { unit });
            try {
                Check("real HitStop starts", stop.MoveNext() && (bool)Read(view, "_hitstop"));
                var position = model.transform.position; var rotation = model.transform.rotation;
                for (int step = 0; step < 3; step++) {
                    bool pending = death.MoveNext(); float elapsed = Elapsed(death);
                    Check("death remains pending during stop " + step, pending);
                    Check("death elapsed frozen " + step, elapsed == 0f, elapsed);
                    // A broken guard may advance by .2 s on its first step: fail before another step reaches VFX.
                    if (!pending || elapsed != 0f) throw new System.InvalidOperationException("Death advanced during hitstop; remaining manual steps aborted");
                }
                Check("root and dissolve frozen", model.transform.position == position &&
                    Quaternion.Angle(model.transform.rotation, rotation) < .00001f && (float)Read(model, "_dissolve") == 0f);
                float time = anim.NormalizedTime; Graph(anim).Evaluate(.05f);
                Check("death skeletal time frozen", Mathf.Abs(anim.NormalizedTime - time) < .00001f);
                FinishHitStop(stop);
                bool resumed = death.MoveNext(); // Exactly one real-delta step; do not advance into the VFX beat.
                Check("death resumes on actual frame clock", resumed && Mathf.Abs(Elapsed(death) - actualStep) < .000001f &&
                    model.transform.position != position, new { speed, actualStep, elapsed = Elapsed(death) });
                Check("resume stays before VFX", Elapsed(death) < vfxAt && (float)Read(model, "_dissolve") == 0f);
                Graph(anim).Evaluate(.05f);
                Check("skeletal time resumes", anim.NormalizedTime > time);
            } finally { (death as System.IDisposable)?.Dispose(); (stop as System.IDisposable)?.Dispose(); }

            preferences.ReducedMotion = true; model.SetDissolve(0f); anim.Play("Attack", 0f);
            string heldClip = anim.CurrentClip;
            death = (System.Collections.IEnumerator)deathMethod.Invoke(view, new object[] { unit });
            try {
                Check("reduced death starts", death.MoveNext()); // One actual step, at most .2 s of its .25 s fade.
                Check("reduced death uses actual frame clock", Mathf.Abs(Elapsed(death) - actualStep) < .000001f,
                    new { actualStep, elapsed = Elapsed(death) });
                Check("reduced death holds current take", anim.CurrentClip == heldClip && unit.DeathRate == 0f);
                float time = anim.NormalizedTime; Graph(anim).Evaluate(.05f);
                Check("reduced death stays frozen", Mathf.Abs(anim.NormalizedTime - time) < .00001f);
                float dissolve = (float)Read(model, "_dissolve");
                Check("reduced dissolve advances without completing", dissolve > 0f && dissolve < 1f, dissolve);
                // Preference is private to this inactive fixture; exercise real restoration after a later nonreduced hit.
                preferences.ReducedMotion = false;
                stop = (System.Collections.IEnumerator)stopMethod.Invoke(view, new object[] { .01f });
                try { Check("later hit starts", stop.MoveNext()); FinishHitStop(stop); }
                finally { (stop as System.IDisposable)?.Dispose(); }
                Graph(anim).Evaluate(.05f);
                Check("HitStop restoration cannot thaw reduced death", Mathf.Abs(anim.NormalizedTime - time) < .00001f);
            } finally { (death as System.IDisposable)?.Dispose(); }
        });
        Check("all bounded cases completed", completedCases == 11, completedCases);
    }
} catch (System.Exception e) { error = true; issues.Add(new { test = currentCase, exception = e.ToString() }); }
finally {
    currentCase = "cleanup";
    foreach (var root in roots) try { if (root != null) UnityEngine.Object.DestroyImmediate(root); }
        catch (System.Exception e) { error = true; issues.Add(new { cleanup = "GameObject", exception = e.ToString() }); }
    foreach (var clip in clips) try { if (clip != null) UnityEngine.Object.DestroyImmediate(clip); }
        catch (System.Exception e) { error = true; issues.Add(new { cleanup = "AnimationClip", exception = e.ToString() }); }
    Check("production GameApp singleton unchanged", Abyss.Runtime.GameApp.Instance == originalApp);
    Check("temporary objects destroyed", roots.TrueForAll(x => x == null) && clips.TrueForAll(x => x == null));
    Application.logMessageReceived -= log;
}
return Newtonsoft.Json.JsonConvert.SerializeObject(new { status = error ? "failed" : "passed", error,
    completedCases, completedEntryCases, skippedCases, checks, issues,
    limitation = "Manual graph/coroutine evaluation; rendered appearance and PlayerLoop scheduling remain parent runtime checks." },
    Newtonsoft.Json.Formatting.Indented);
