// Unity Pipeline eval_file, PLAY MODE, idle scene (no active VFX). Parent executes this probe.
// unity command eval_file --file Tools/TripoVfxTimingChecks.eval.cs
// Synchronous property/pool regression; no screenshots, files, gameplay, or global Time.timeScale changes.
// This does NOT prove native point ages are retimed or that TimeScale=0 alone freezes trails.
var flags = System.Reflection.BindingFlags.Instance | System.Reflection.BindingFlags.NonPublic | System.Reflection.BindingFlags.Public;
var type = typeof(Abyss.Presentation.Vfx.VfxLibrary);
if (!UnityEngine.Application.isPlaying) throw new System.InvalidOperationException("Run in Play Mode.");
var library = Abyss.Presentation.Vfx.VfxLibrary.Instance;
bool created = library == null;
if (created) library = Abyss.Presentation.Vfx.VfxLibrary.Create();
var effects = (System.Collections.IList)type.GetField("_effects", flags).GetValue(library);
foreach (object effect in effects)
    if ((bool)effect.GetType().GetField("Active", flags).GetValue(effect))
        throw new System.InvalidOperationException("Active VFX found: use an idle Play Mode scene; do not interrupt a battle.");
float originalScale = library.TimeScale;
float originalTrailRate = (float)type.GetField("_trailTimeScale", flags).GetValue(library);
int checks = 0;
void Check(bool condition, string label)
{
    if (!condition) throw new System.InvalidOperationException("TRAIL_TIMING_FAIL: " + label);
    checks++;
}
void Lifetime(UnityEngine.TrailRenderer trail, float expected, string label)
{
    Check(!float.IsNaN(trail.time) && !float.IsInfinity(trail.time) && trail.time > 0f, label + " finite positive");
    Check(UnityEngine.Mathf.Abs(trail.time - expected) < .00001f, label + " expected " + expected + ", got " + trail.time);
}
UnityEngine.TrailRenderer Arrow(bool forceBuild)
{
    if (forceBuild)
    {
        // Force BuildLayer at the current rate even when a prewarmed arrow pool already exists.
        var recipes = (System.Collections.IDictionary)type.GetField("_recipes", flags).GetValue(library);
        int slot = (int)type.GetMethod("Build", flags).Invoke(library, new object[] { recipes["arrow"] });
        var free = (System.Collections.IDictionary)type.GetField("_free", flags).GetValue(library);
        ((System.Collections.Generic.Stack<int>)free["arrow"]).Push(slot);
        object built = effects[slot];
        var root = (UnityEngine.GameObject)built.GetType().GetField("Root", flags).GetValue(built);
        Lifetime(root.GetComponentInChildren<UnityEngine.TrailRenderer>(true), .12f / library.TimeScale, "creation");
    }
    var handle = library.Travel("arrow", UnityEngine.Vector3.zero, UnityEngine.Vector3.right * 3f, .3f);
    int index = (int)typeof(Abyss.Presentation.Vfx.VfxHandle).GetField("_slot", flags).GetValue(handle);
    object active = effects[index];
    var activeRoot = (UnityEngine.GameObject)active.GetType().GetField("Root", flags).GetValue(active);
    return activeRoot.GetComponentInChildren<UnityEngine.TrailRenderer>(true);
}
try
{
    library.TimeScale = 1f;
    var arrow = Arrow(true);
    Lifetime(arrow, .12f, "1x");
    library.TimeScale = 2f;
    Lifetime(arrow, .06f, "live change to 2x");
    // Verify speed changes do not explicitly discard the existing path. No claim about native point ages.
    arrow.AddPosition(UnityEngine.Vector3.zero);
    arrow.AddPosition(UnityEngine.Vector3.right);
    int points = arrow.positionCount;
    Check(points >= 2, "seeded trail points");
    library.TimeScale = .1f;
    Lifetime(arrow, 1.2f, "hitstop 0.1x");
    Check(arrow.positionCount == points, "no Clear on rate change");
    foreach (float invalid in new[] { 0f, -1f, float.NaN, float.PositiveInfinity, float.NegativeInfinity })
    {
        library.TimeScale = invalid;
        Check(library.TimeScale == 0f, "invalid/zero clock sanitized");
        Lifetime(arrow, 1.2f, "zero/invalid retains last positive trail rate");
    }
    library.StopAll();
    var pausedReuse = Arrow(false);
    Lifetime(pausedReuse, 1.2f, "reuse at zero is finite");
    library.TimeScale = 2f;
    library.StopAll();
    arrow = Arrow(true);
    Lifetime(arrow, .06f, "new arrow created at 2x");
    library.StopAll();
    library.TimeScale = 1f;
    Lifetime(arrow, .12f, "inactive pooled arrow at 1x");
    library.TimeScale = 2f;
    arrow.time = .777f; // Deliberately stale pooled state; same rate means the setter will not repair it.
    var reused = Arrow(false);
    Check(object.ReferenceEquals(arrow, reused), "same pooled TrailRenderer reused");
    Lifetime(reused, .06f, "Play reapplies scale on reuse");
    library.TimeScale = float.Epsilon;
    Lifetime(reused, 60f, "tiny positive rate bounded");
    library.TimeScale = float.MaxValue;
    Lifetime(reused, .0001f, "huge positive rate bounded");
    library.TimeScale = 1f;
    Lifetime(reused, .12f, "restore 1x");
}
finally
{
    library.StopAll();
    library.TimeScale = originalTrailRate;
    library.TimeScale = originalScale;
    if (created) UnityEngine.Object.Destroy(library.gameObject);
}
return "TRAIL_TIMING_PASS: " + checks + " assertions; native point-age transitions and screenshots require separate runtime review.";
