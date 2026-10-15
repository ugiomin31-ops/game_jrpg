// Parent only, idle PLAY MODE: unity command eval_file --file Tools/TripoAtmosphereChecks.eval.cs
// Requested route: gpt-6-astra/high/priority; actual routing not verified by this probe.
// Returns immediately. Poll returned evidence directory/DONE; destruction wait is bounded to 25s.
// No Apply(), persistent scene/save changes or asset writes. Only probe-owned objects are cleaned up.
if (!UnityEngine.Application.isPlaying)
    throw new System.InvalidOperationException("Run in idle Play Mode.");
var outDir = System.IO.Path.GetFullPath(".git/codex-runs/20261015-165918-tripo-motion/fix-atmosphere/runtime-" + System.Guid.NewGuid().ToString("N"));
System.IO.Directory.CreateDirectory(outDir);
var owned = new System.Collections.Generic.List<UnityEngine.Object>();
var survivors = new System.Collections.Generic.List<UnityEngine.Object>();
var cleanup = new System.Collections.Generic.List<UnityEngine.Object>();
var originalSun = UnityEngine.RenderSettings.sun;
UnityEngine.GameObject root = null;
int checks = 0;
void Check(bool condition, string label)
{
    if (!condition) throw new System.InvalidOperationException("ATMOSPHERE_FAIL: " + label);
    checks++;
}
void Track(UnityEngine.Rendering.VolumeProfile profile, System.Collections.Generic.List<UnityEngine.Object> target)
{
    target.Add(profile);
    cleanup.Add(profile);
    foreach (var component in profile.components) { target.Add(component); cleanup.Add(component); }
}
Abyss.Runtime.World.Atmosphere Create()
{
    var atmosphere = Abyss.Runtime.World.Atmosphere.Create(root.transform);
    // Suppress the test lights/volumes before yielding to a rendered frame.
    atmosphere.Sun.enabled = false;
    atmosphere.Volume.enabled = false;
    UnityEngine.RenderSettings.sun = originalSun;
    Check(atmosphere.Volume.sharedProfile.components.Count == 5, "five generated effects");
    Check(!atmosphere.Volume.HasInstantiatedProfile(), "no implicit profile clone");
    return atmosphere;
}
async System.Threading.Tasks.Task Run()
{
    string failure = null;
    try
    {
        root = new UnityEngine.GameObject("TripoAtmosphereChecks_Isolated");
        var survivor = Create();
        survivors.Add(survivor.gameObject);
        Track(survivor.Volume.sharedProfile, survivors);
        var normal = Create();
        owned.Add(normal.gameObject);
        Track(normal.Volume.sharedProfile, owned);
        var replaced = Create();
        owned.Add(replaced.gameObject);
        var replacedProfile = replaced.Volume.sharedProfile;
        Track(replacedProfile, owned);
        var borrowed = UnityEngine.ScriptableObject.CreateInstance<UnityEngine.Rendering.VolumeProfile>();
        var borrowedEffect = borrowed.Add<UnityEngine.Rendering.Universal.Bloom>(true);
        Track(borrowed, survivors);
        replaced.Volume.sharedProfile = borrowed;
        replaced.Volume.profile = borrowed;
        // Mutable profile lists are not ownership ledgers: removed owned effects still need destruction,
        // while an externally supplied effect must survive even if present in the owned profile.
        replacedProfile.components.RemoveAt(0);
        replacedProfile.components.Add(borrowedEffect);
        UnityEngine.Object.Destroy(normal.gameObject);
        UnityEngine.Object.Destroy(replaced.gameObject);
        var clock = System.Diagnostics.Stopwatch.StartNew();
        while (owned.Exists(item => item != null))
        {
            if (!UnityEngine.Application.isPlaying || clock.Elapsed.TotalSeconds >= 25)
                throw new System.TimeoutException("Owned atmosphere/profile/effect destruction exceeded 25s; alive=" + owned.FindAll(item => item != null).Count);
            await System.Threading.Tasks.Task.Delay(16); // preserve Unity synchronization context
        }
        foreach (var item in owned) Check(item == null, "owned object destroyed");
        foreach (var item in survivors) Check(item != null, "other atmosphere/borrowed object alive");
        Check(survivor.Volume.sharedProfile != null && survivor.Volume.sharedProfile.components.Count == 5, "survivor profile intact");
        Check(borrowed.components.Count == 1 && borrowed.components[0] == borrowedEffect, "borrowed profile intact");
        Check(UnityEngine.RenderSettings.sun == originalSun, "scene sun unchanged");
    }
    catch (System.Exception e) { failure = e.ToString(); }
    finally
    {
        UnityEngine.RenderSettings.sun = originalSun;
        if (root != null) UnityEngine.Object.Destroy(root);
        // All entries were created by this probe; also cleans up failures against the old implementation.
        foreach (var item in cleanup) if (item != null) UnityEngine.Object.Destroy(item);
        string status = failure == null ? "ATMOSPHERE_PASS" : "ATMOSPHERE_FAIL";
        System.IO.File.WriteAllText(System.IO.Path.Combine(outDir, "checks.json"), Newtonsoft.Json.JsonConvert.SerializeObject(new { status, checks, failure }, Newtonsoft.Json.Formatting.Indented));
        System.IO.File.WriteAllText(System.IO.Path.Combine(outDir, "DONE"), status);
    }
}
_ = Run();
return "Atmosphere ownership probe started; poll DONE in " + outDir;
