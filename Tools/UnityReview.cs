// Run from a connected Unity Editor:
// unity command run_script --project-path <project> -- --file Tools/UnityReview.cs --entry UnityReview.Audit
// Output is kept outside Assets so a review never triggers an import or ships in a player.
using System;
using System.Collections.Generic;
using System.IO;
using System.Linq;
using System.Reflection;
using Abyss.Logic;
using Abyss.Runtime.Art;
using Newtonsoft.Json;
using Newtonsoft.Json.Linq;
using Abyss.Presentation.Vfx;
using UnityEditor;
using UnityEngine;

public static class UnityReview
{
    const string Output = "Review";
    static readonly string[] RequiredClips = { "Idle", "Run", "Attack", "Cast", "Hit", "Die", "Victory" };

    public static object BuildWindows()
    {
        if (EditorApplication.isPlayingOrWillChangePlaymode || EditorApplication.isCompiling)
            throw new InvalidOperationException("Wait until Play mode and script reloads have fully stopped before building.");
        Directory.CreateDirectory(Output);
        File.WriteAllText(Output + "/windows-build.json", "{\"status\":\"running\"}");
        try
        {
            Abyss.EditorTools.AbyssProjectSetup.BuildWindows();
            var report = UnityEditor.Build.Reporting.BuildReport.GetLatestReport();
            var summary = report.summary;
            var messages = report.steps.SelectMany(step => step.messages)
                .Where(message => message.type == LogType.Error || message.type == LogType.Warning || message.type == LogType.Exception)
                .Select(message => new { type = message.type.ToString(), message.content }).ToArray();
            var result = new
            {
                status = "complete", unity = Application.unityVersion, result = summary.result.ToString(),
                summary.outputPath, summary.totalSize, seconds = summary.totalTime.TotalSeconds,
                summary.totalErrors, summary.totalWarnings, messages
            };
            File.WriteAllText(Output + "/windows-build.json", JsonConvert.SerializeObject(result, Formatting.Indented));
            return result;
        }
        catch (Exception error)
        {
            File.WriteAllText(Output + "/windows-build.json", JsonConvert.SerializeObject(new { status = "failed", error = error.ToString() }, Formatting.Indented));
            throw;
        }
    }

    public static object Audit()
    {
        Directory.CreateDirectory(Output);
        var problems = new List<string>();
        var rows = new List<object>();
        var db = GameDB.Load(t => Resources.Load<TextAsset>("Data/" + t).text);
        foreach (string path in AssetDatabase.GetAllAssetPaths().Where(p => p.StartsWith("Assets/_Game/Resources/Art/") && p.EndsWith(".fbx")))
        {
            var prefab = AssetDatabase.LoadAssetAtPath<GameObject>(path);
            if (prefab == null) { problems.Add("Missing prefab: " + path); continue; }
            var renderers = prefab.GetComponentsInChildren<Renderer>(true);
            foreach (var r in renderers.Where(r => !r.name.StartsWith("Col_")))
                foreach (var mat in r.sharedMaterials)
                    if (mat == null || mat.shader == null || !mat.shader.isSupported) problems.Add("Missing/unsupported material: " + path + "/" + r.name);
            var clips = AssetDatabase.LoadAllAssetsAtPath(path).OfType<AnimationClip>().Where(c => !c.name.StartsWith("__preview")).Select(c => c.name).ToArray();
            bool actor = path.Contains("/Characters/") || path.Contains("/Enemies/") || path.Contains("/NPCs/");
            if (actor)
            {
                if (prefab.GetComponentInChildren<Animator>() == null) problems.Add("Missing Animator: " + path);
                foreach (var name in RequiredClips)
                    if (!clips.Contains(name)) problems.Add("Missing " + name + ": " + path);
            }
            int triangles = AssetDatabase.LoadAllAssetsAtPath(path).OfType<Mesh>().Sum(m => Enumerable.Range(0, m.subMeshCount).Sum(i => (int)m.GetIndexCount(i) / 3));
            rows.Add(new { path, triangles, renderers = renderers.Length, clips });
        }
        foreach (var id in db.Heroes.Keys) Require(ArtLibrary.HeroPath(id), problems);
        foreach (var id in db.Enemies.Keys) Require(ArtLibrary.EnemyPath(id), problems);
        foreach (var id in db.Equipment.Keys)
            Require(ArtLibrary.Exists(ArtLibrary.WeaponPath(id)) ? ArtLibrary.WeaponPath(id) : ArtLibrary.PropPath("Equipment", id), problems);
        foreach (var biome in db.Floors.Select(f => f.Tileset).Distinct()) Require(ArtLibrary.EnvPath(biome, "arena"), problems);
        Require(ArtLibrary.TownPath, problems);
        var report = new { unity = Application.unityVersion, models = rows.Count, heroes = db.Heroes.Count, enemies = db.Enemies.Count, equipment = db.Equipment.Count, problems, assets = rows };
        File.WriteAllText(Output + "/asset-audit.json", JsonConvert.SerializeObject(report, Formatting.Indented));
        return new { models = rows.Count, problems };
    }

    static void Require(string path, List<string> problems)
    {
        if (!ArtLibrary.Exists(path)) problems.Add("Missing catalog asset: " + path);
    }

    public static object AuditEffects()
    {
        if (!Application.isPlaying) throw new InvalidOperationException("Enter Play mode before instantiating effects.");
        Directory.CreateDirectory(Output);
        var library = VfxLibrary.Create();
        var problems = new List<string>();
        var effects = (JArray)JObject.Parse(Resources.Load<TextAsset>("Vfx/effects").text)["effects"];
        foreach (var effect in effects)
        {
            string key = (string)effect["key"];
            try
            {
                foreach (var layer in effect["layers"])
                    if (Resources.Load<Texture2D>("Vfx/Textures/" + (string)layer["texture"]) == null)
                        problems.Add("Missing texture: " + key + "/" + layer["texture"]);
                var handle = library.Play(key, new Vector3(500, 500, 500), duration: .05f);
                if (!handle.IsPlaying) problems.Add("Effect did not start: " + key);
                handle.Stop();
            }
            catch (Exception error) { problems.Add(key + ": " + error.Message); }
        }
        var report = new { unity = Application.unityVersion, effects = effects.Count, problems };
        File.WriteAllText(Output + "/vfx-audit.json", JsonConvert.SerializeObject(report, Formatting.Indented));
        return report;
    }

    public static object Gallery(string category)
    {
        if (!Application.isPlaying) throw new InvalidOperationException("Enter Play mode before capturing the gallery.");
        Directory.CreateDirectory(Output);
        var db = GameDB.Instance;
        string[] paths = category == "heroes" ? db.HeroOrder.Select(ArtLibrary.HeroPath).ToArray()
            : category == "enemies" ? db.Enemies.Keys.OrderBy(x => x).Select(ArtLibrary.EnemyPath).ToArray()
            : db.Equipment.Keys.OrderBy(x => x).Select(id => ArtLibrary.Exists(ArtLibrary.WeaponPath(id)) ? ArtLibrary.WeaponPath(id) : ArtLibrary.PropPath("Equipment", id)).ToArray();
        const int size = 256, columns = 6;
        var sheet = new Texture2D(columns * size, ((paths.Length + columns - 1) / columns) * size, TextureFormat.RGB24, false);
        var stage = new GameObject("Review gallery stage");
        stage.transform.position = new Vector3(500, 500, 500);
        var camera = new GameObject("Review gallery camera").AddComponent<Camera>();
        camera.clearFlags = CameraClearFlags.SolidColor;
        camera.backgroundColor = new Color(.075f, .1f, .14f);
        camera.orthographic = true;
        var rt = new RenderTexture(size, size, 24);
        camera.targetTexture = rt;
        var previous = RenderTexture.active;
        bool fog = RenderSettings.fog;
        RenderSettings.fog = false;
        try
        {
            for (int index = 0; index < paths.Length; index++)
            {
                var model = UnityEngine.Object.Instantiate(ArtLibrary.LoadPrefab(paths[index]), stage.transform, false);
                var renderers = model.GetComponentsInChildren<Renderer>();
                var bounds = renderers[0].bounds;
                foreach (var renderer in renderers) bounds.Encapsulate(renderer.bounds);
                camera.orthographicSize = Mathf.Max(bounds.extents.y, bounds.extents.x) * 1.22f;
                camera.transform.position = bounds.center + (category == "equipment" ? new Vector3(.65f, .28f, 1f).normalized * Mathf.Max(4, bounds.size.magnitude * 2) : new Vector3(0, bounds.extents.y * .15f, Mathf.Max(4, bounds.size.magnitude * 2)));
                camera.transform.LookAt(bounds.center);
                camera.Render();
                RenderTexture.active = rt;
                int x = index % columns * size, y = sheet.height - (index / columns + 1) * size;
                sheet.ReadPixels(new Rect(0, 0, size, size), x, y, false);
                model.SetActive(false);
                UnityEngine.Object.DestroyImmediate(model);
            }
            sheet.Apply();
            File.WriteAllBytes(Output + "/" + category + ".png", sheet.EncodeToPNG());
            File.WriteAllText(Output + "/" + category + "-index.json", JsonConvert.SerializeObject(paths, Formatting.Indented));
        }
        finally
        {
            RenderTexture.active = previous;
            RenderSettings.fog = fog;
            camera.targetTexture = null;
            rt.Release();
            UnityEngine.Object.DestroyImmediate(rt);
            UnityEngine.Object.DestroyImmediate(sheet);
            UnityEngine.Object.DestroyImmediate(camera.gameObject);
            UnityEngine.Object.DestroyImmediate(stage);
        }
        return new { category, models = paths.Length, path = Output + "/" + category + ".png" };
    }

    public static object PhoneView(int width, int height)
    {
        // Unity has no public Editor API for a fixed Game view resolution.
        // Keep the reflection in this external review tool, away from shipped code.
        var assembly = typeof(Editor).Assembly;
        var sizesType = assembly.GetType("UnityEditor.GameViewSizes");
        var singleton = typeof(ScriptableSingleton<>).MakeGenericType(sizesType);
        var sizes = singleton.GetProperty("instance").GetValue(null);
        var getGroup = sizesType.GetMethod("GetGroup");
        var group = getGroup.Invoke(sizes, new[] { Enum.Parse(getGroup.GetParameters()[0].ParameterType, "Standalone") });
        var sizeType = assembly.GetType("UnityEditor.GameViewSize");
        var kind = assembly.GetType("UnityEditor.GameViewSizeType");
        var ctor = sizeType.GetConstructor(BindingFlags.Public | BindingFlags.NonPublic | BindingFlags.Instance, null, new[] { kind, typeof(int), typeof(int), typeof(string) }, null);
        var size = ctor.Invoke(new object[] { Enum.ToObject(kind, 1), width, height, "Codex mobile review" });
        int index = (int)group.GetType().GetMethod("GetTotalCount").Invoke(group, null);
        group.GetType().GetMethod("AddCustomSize").Invoke(group, new[] { size });
        var viewType = assembly.GetType("UnityEditor.GameView");
        var window = EditorWindow.GetWindow(viewType);
        viewType.GetProperty("selectedSizeIndex", BindingFlags.Instance | BindingFlags.Public | BindingFlags.NonPublic).SetValue(window, index);
        return new { width, height };
    }
}
