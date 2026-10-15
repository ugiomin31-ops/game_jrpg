// Unity Pipeline eval_file. This is an external acceptance harness, not player code.
// Run after importing assets, in Play Mode: unity command eval_file --file Tools/TripoEnrichmentAcceptance.eval.cs
// Populate Manifest below with imported Resources paths and required named takes. Empty manifest is an explicit failure.
// Evidence is written only under .git/codex-runs/20261015-enrichment. No scenes/assets/saves are modified.
// Requested worker route: gpt-6-astra / high / priority (not a routing receipt).

// Add only assets imported into Resources. Character/Monster/SkillMotion entries must name real Abyss.Runtime.Art.ArtLibrary takes.
// Example (not evidence): ("Character", "hero_id", "Art/Characters/hero_id/hero_id", new[] { "Idle", "Skill" }, 10000, 20000)
// Use statement/local-function eval syntax, matching TripoBattleAcceptance (no type or using declarations).
var Manifest = new (string Kind, string Id, string ResourcePath, string[] Motions, int MinTriangles, int MaxTriangles)[] { };
var EvidenceRoot = System.IO.Path.GetFullPath(".git/codex-runs/20261015-enrichment");
var RunDir = System.IO.Path.Combine(EvidenceRoot, "acceptance-" + System.DateTime.UtcNow.ToString("yyyyMMdd-HHmmss-fff"));
const int PreviewLayer = 31;
var StartedUtc = System.DateTime.UtcNow.ToString("O");
var checks = new System.Collections.Generic.List<object>();
var issues = new System.Collections.Generic.List<string>();
var spawned = new System.Collections.Generic.List<GameObject>();
var textures = new System.Collections.Generic.List<RenderTexture>();
var ownedMeshes = new System.Collections.Generic.List<Mesh>();
var logs = new System.Collections.Generic.List<object>();
var evidenceNames = new System.Collections.Generic.HashSet<string>(System.StringComparer.OrdinalIgnoreCase);
System.IO.FileStream lease = null;
bool failed = false;
bool IsFinite(Vector3 v) => !(float.IsNaN(v.x) || float.IsNaN(v.y) || float.IsNaN(v.z) || float.IsInfinity(v.x) || float.IsInfinity(v.y) || float.IsInfinity(v.z));
string SafeName(string value) => string.Concat(value.Select(c => char.IsLetterOrDigit(c) || c == '-' || c == '_' ? c : '_'));
Application.LogCallback handler = (message, stack, type) => {
    if (type == LogType.Warning || type == LogType.Error || type == LogType.Exception || type == LogType.Assert) {
        logs.Add(new { type = type.ToString(), message, stack });
        if (type != LogType.Warning) { failed = true; issues.Add("Unity " + type + ": " + message); }
    }
};

void Check(string name, bool passed, object detail = null)
{
    checks.Add(new { name, passed, detail });
    if (!passed) { failed = true; issues.Add(name); }
}
void Require(bool passed, string label)
{
    Check(label, passed);
    if (!passed) throw new System.InvalidOperationException("ENRICHMENT_FAIL: " + label);
}
void SetLayer(GameObject go, int layer)
{
    go.layer = layer;
    foreach (Transform child in go.transform) SetLayer(child.gameObject, layer);
}
int TriangleCount(GameObject go)
{
    long total = 0;
    foreach (var filter in go.GetComponentsInChildren<MeshFilter>(true))
        if (filter.sharedMesh != null) for (int s = 0; s < filter.sharedMesh.subMeshCount; s++) if (filter.sharedMesh.GetTopology(s) == MeshTopology.Triangles) total += filter.sharedMesh.GetIndexCount(s) / 3;
    foreach (var skin in go.GetComponentsInChildren<SkinnedMeshRenderer>(true))
        if (skin.sharedMesh != null) for (int s = 0; s < skin.sharedMesh.subMeshCount; s++) if (skin.sharedMesh.GetTopology(s) == MeshTopology.Triangles) total += skin.sharedMesh.GetIndexCount(s) / 3;
    if (total > int.MaxValue) throw new System.InvalidOperationException("Triangle count overflow");
    return (int)total;
}
object BoundsDetail(GameObject go)
{
    var renderers = go.GetComponentsInChildren<Renderer>(true).Where(r => r != null && !(r is ParticleSystemRenderer)).ToArray();
    if (renderers.Length == 0) return new { rendererCount = 0, bounds = (object)null };
    var bounds = renderers[0].bounds;
    for (int i = 1; i < renderers.Length; i++) bounds.Encapsulate(renderers[i].bounds);
    // Serialize scalars: Vector3.normalized recursively exposes another Vector3 to Json.NET.
    return new { rendererCount = renderers.Length, bounds = new { center = new[] { bounds.center.x, bounds.center.y, bounds.center.z }, size = new[] { bounds.size.x, bounds.size.y, bounds.size.z } } };
}
bool MaterialsValid(GameObject go, out object detail, bool requireWorldBounds = true)
{
    int renderers = 0, slots = 0, missing = 0, invalidMeshes = 0;
    foreach (var r in go.GetComponentsInChildren<Renderer>(true))
    {
        if (r == null || r is ParticleSystemRenderer) continue;
        renderers++;
        var mats = r.sharedMaterials;
        slots += mats.Length;
        missing += mats.Count(m => m == null || m.shader == null || !m.shader.isSupported || m.shader.name == "Hidden/InternalErrorShader");
        var mesh = r is SkinnedMeshRenderer skin ? skin.sharedMesh : r.GetComponent<MeshFilter>()?.sharedMesh;
        if (mesh == null || mesh.vertexCount == 0 || mesh.subMeshCount == 0) { invalidMeshes++; continue; }
        if (mats.Length < mesh.subMeshCount) missing++;
        for (int s = 0; s < mesh.subMeshCount; s++)
            if (mesh.GetTopology(s) != MeshTopology.Triangles || mesh.GetIndexCount(s) == 0 || mesh.GetIndexCount(s) % 3 != 0) invalidMeshes++;
        if (!IsFinite(mesh.bounds.center) || !IsFinite(mesh.bounds.size) || float.IsInfinity(mesh.bounds.size.sqrMagnitude) || mesh.bounds.size.sqrMagnitude <= 1e-8f ||
            (requireWorldBounds && (!IsFinite(r.bounds.center) || !IsFinite(r.bounds.size) || float.IsInfinity(r.bounds.size.sqrMagnitude) || r.bounds.size.sqrMagnitude <= 1e-8f))) invalidMeshes++;
    }
    detail = new { renderers, materialSlots = slots, invalidMaterials = missing, invalidMeshes };
    return renderers > 0 && slots > 0 && missing == 0 && invalidMeshes == 0;
}
bool HasRealBoneWeights(SkinnedMeshRenderer skin, out object detail)
{
    var mesh = skin.sharedMesh;
    var bones = skin.bones;
    var bindposes = mesh.bindposes;
    int influenced = 0, invalidBoneIndices = 0, invalidWeights = 0, validBones = bones == null ? 0 : bones.Count(b => b != null);
    var counts = mesh.GetBonesPerVertex();
    var weights = mesh.GetAllBoneWeights();
    try
    {
        int offset = 0;
        for (int i = 0; i < counts.Length; i++)
        {
            bool vertexInfluenced = false;
            float sum = 0f;
            for (int j = 0; j < counts[i]; j++)
            {
                if (offset + j >= weights.Length) throw new System.InvalidOperationException("Bone weight count exceeds buffer");
                var weight = weights[offset + j];
                if (float.IsNaN(weight.weight) || float.IsInfinity(weight.weight) || weight.weight < 0f) invalidWeights++;
                sum += weight.weight;
                if (weight.weight > 0f)
                {
                    vertexInfluenced = true;
                    if (bones == null || weight.boneIndex < 0 || weight.boneIndex >= bones.Length || bones[weight.boneIndex] == null || weight.boneIndex >= bindposes.Length || !bones[weight.boneIndex].IsChildOf(skin.transform.root)) invalidBoneIndices++;
                }
            }
            if (vertexInfluenced) influenced++;
            if (float.IsNaN(sum) || float.IsInfinity(sum) || Mathf.Abs(sum - 1f) > .02f) invalidWeights++;
            offset += counts[i];
        }
        if (offset != weights.Length || counts.Length != mesh.vertexCount) invalidWeights++;
        foreach (var pose in bindposes)
            for (int i = 0; i < 16; i++) if (float.IsNaN(pose[i]) || float.IsInfinity(pose[i])) invalidWeights++;
    }
    finally { counts.Dispose(); weights.Dispose(); }
    detail = new { vertices = mesh.vertexCount, influencedVertices = influenced, boneCount = bones == null ? 0 : bones.Length, bindposeCount = bindposes.Length, validBones, invalidInfluences = invalidBoneIndices, invalidWeights };
    return bones != null && bones.Length > 0 && validBones > 0 && mesh.vertexCount > 0 && influenced == mesh.vertexCount && invalidBoneIndices == 0 && invalidWeights == 0;
}
float BakeDelta(SkinnedMeshRenderer skin, Mesh baked, Vector3[] previous)
{
    skin.BakeMesh(baked);
    var current = baked.vertices;
    if (current.Length == 0 || current.Length != previous.Length) throw new System.InvalidOperationException("BakeMesh vertex count changed or empty");
    float deltaSquared = 0f;
    for (int i = 0; i < current.Length; i++)
    {
        if (!IsFinite(current[i]) || !IsFinite(previous[i])) throw new System.InvalidOperationException("BakeMesh produced nonfinite vertices");
        float delta = (current[i] - previous[i]).sqrMagnitude;
        if (float.IsInfinity(delta)) throw new System.InvalidOperationException("BakeMesh delta overflow");
        deltaSquared = Mathf.Max(deltaSquared, delta);
    }
    return deltaSquared;
}
float ProbeWeightedBone(SkinnedMeshRenderer skin)
{
    // Synchronous probe on a clone: no graph tick occurs between pose and restoration.
    // This proves bone-driven skinning independently of blend-shape-only clip movement.
    var weights = skin.sharedMesh.GetAllBoneWeights();
    int index = -1;
    float strongest = 0f;
    try
    {
        foreach (var weight in weights)
        {
            if (weight.weight <= 0f) continue;
            var candidate = skin.bones[weight.boneIndex];
            if (candidate == skin.transform || skin.transform.IsChildOf(candidate)) continue;
            if (weight.weight > strongest) { strongest = weight.weight; index = weight.boneIndex; }
        }
    }
    finally { weights.Dispose(); }
    if (index < 0) throw new System.InvalidOperationException("No weighted bone to probe");
    var bone = skin.bones[index];
    if (!bone.IsChildOf(skin.transform.root)) throw new System.InvalidOperationException("Probe bone is outside clone hierarchy");
    var position = bone.localPosition;
    var baked = new Mesh { name = "TripoEnrichmentAcceptance_BoneProbe" };
    ownedMeshes.Add(baked);
    try
    {
        skin.BakeMesh(baked);
        var before = baked.vertices;
        bone.position += Vector3.right * .05f;
        return BakeDelta(skin, baked, before);
    }
    finally { bone.localPosition = position; }
}
void RenderEvidence(GameObject subject, string fileStem)
{
    Require(evidenceNames.Add(fileStem), "render evidence filename is unique: " + fileStem);
    var cameraGo = new GameObject("TripoEnrichmentAcceptance_Camera");
    spawned.Add(cameraGo);
    SetLayer(cameraGo, PreviewLayer);
    var camera = cameraGo.AddComponent<Camera>();
    camera.enabled = false;
    camera.clearFlags = CameraClearFlags.SolidColor;
    camera.backgroundColor = new Color(.055f, .065f, .085f, 1f);
    camera.cullingMask = 1 << PreviewLayer;
    camera.fieldOfView = 32f;
    camera.nearClipPlane = .01f;
    camera.farClipPlane = 100f;
    camera.allowHDR = false;
    var renderers = subject.GetComponentsInChildren<Renderer>(true).Where(r => r != null && !(r is ParticleSystemRenderer)).ToArray();
    if (renderers.Length == 0) throw new System.InvalidOperationException("No renderers for preview: " + fileStem);
    var bounds = renderers[0].bounds;
    foreach (var r in renderers.Skip(1)) bounds.Encapsulate(r.bounds);
    camera.farClipPlane = Mathf.Max(100f, bounds.size.magnitude * 10f);
    camera.transform.position = bounds.center + new Vector3(0f, bounds.extents.y * .18f, -Mathf.Max(bounds.size.x, bounds.size.y, bounds.size.z) * 2.8f - .5f);
    camera.transform.LookAt(bounds.center);
    var rt = new RenderTexture(512, 512, 24, RenderTextureFormat.ARGB32);
    rt.name = "TripoEnrichmentAcceptance_RenderTarget";
    textures.Add(rt);
    camera.targetTexture = rt;
    camera.Render();
    var prior = RenderTexture.active;
    var image = new Texture2D(512, 512, TextureFormat.RGB24, false);
    try
    {
        RenderTexture.active = rt;
        image.ReadPixels(new Rect(0, 0, 512, 512), 0, 0);
        image.Apply();
        System.IO.File.WriteAllBytes(System.IO.Path.Combine(RunDir, fileStem + ".png"), image.EncodeToPNG());
    }
    finally
    {
        RenderTexture.active = prior;
        camera.targetTexture = null;
        UnityEngine.Object.Destroy(image);
    }
}
async System.Threading.Tasks.Task Frames(int count)
{
    int stop = Time.frameCount + count;
    var deadline = System.DateTime.UtcNow.AddSeconds(20);
    while (Time.frameCount < stop)
    {
        if (!Application.isPlaying || System.DateTime.UtcNow >= deadline) throw new System.TimeoutException("Unity frames stopped while sampling animation");
        await System.Threading.Tasks.Task.Delay(16);
    }
}

async System.Threading.Tasks.Task<string> Run()
{
await System.Threading.Tasks.Task.Yield(); // Keep Unity synchronization context; return eval control before work.
Application.logMessageReceived += handler;
try
{
Check("Unity is already in Play Mode; harness never starts Play", Application.isPlaying);
Check("manifest contains at least one explicitly imported asset", Manifest != null && Manifest.Length > 0);
if (Application.isPlaying && Manifest != null && Manifest.Length > 0)
{
    var ids = new System.Collections.Generic.HashSet<string>(System.StringComparer.Ordinal);
    var fileIds = new System.Collections.Generic.HashSet<string>(System.StringComparer.OrdinalIgnoreCase);
    foreach (var asset in Manifest)
    {
        GameObject root = null;
        int issueCount = issues.Count;
        try
        {
            Require(!string.IsNullOrWhiteSpace(asset.Id) && !string.IsNullOrWhiteSpace(asset.ResourcePath), "manifest row has id and Resources path");
            Require(new[] { "Character", "Monster", "SkillMotion", "Prop" }.Contains(asset.Kind), asset.Id + " has a recognized kind");
            Require(ids.Add(asset.Id), "manifest id is unique: " + asset.Id);
            Require(fileIds.Add(SafeName(asset.Id)), asset.Id + " evidence filename is unique");
            Require(asset.MinTriangles > 0 && asset.MaxTriangles >= asset.MinTriangles && asset.MaxTriangles <= 20000, asset.Id + " has a valid game-ready triangle range (max 20000)");
            Require(!asset.ResourcePath.StartsWith("/") && !asset.ResourcePath.Contains("\\") && !asset.ResourcePath.Contains(".") && !asset.ResourcePath.Contains(":"), asset.Id + " uses an extensionless Resources-relative path");
            bool animated = asset.Kind != "Prop";
            Require(asset.Motions != null && (animated ? asset.Motions.Length > 0 : asset.Motions.Length == 0), asset.Id + " declares required motions according to asset kind");
            Require(asset.Motions.All(m => !string.IsNullOrWhiteSpace(m)) && asset.Motions.Distinct().Count() == asset.Motions.Length, asset.Id + " motions are nonempty and unique");
            Require(asset.Motions.Select(SafeName).Distinct(System.StringComparer.OrdinalIgnoreCase).Count() == asset.Motions.Length, asset.Id + " motion evidence filenames are unique");
            var prefab = Resources.Load<GameObject>(asset.ResourcePath);
            Require(prefab != null, asset.Id + " Resources.Load<GameObject>(" + asset.ResourcePath + ")");
            Require(MaterialsValid(prefab, out var sourceDetail, false), asset.Id + " source mesh/material validation: " + Newtonsoft.Json.JsonConvert.SerializeObject(sourceDetail));
            var sourceTriangles = TriangleCount(prefab);
            Check(asset.Id + " source triangle range", sourceTriangles >= asset.MinTriangles && sourceTriangles <= asset.MaxTriangles, new { sourceTriangles, asset.MinTriangles, asset.MaxTriangles });

            root = new GameObject("TripoEnrichmentAcceptance_" + asset.Id);
            spawned.Add(root);
            Abyss.Runtime.Art.CharacterModel model = null;
            GameObject view;
            if (asset.Kind == "Prop")
            {
                view = UnityEngine.Object.Instantiate(prefab, root.transform, false);
            }
            else
            {
                // Uses production Resources paths, clip merging, Abyss.Runtime.Art.CharacterModel.Setup and Abyss.Runtime.Art.ClipAnimator.Init contracts.
                Require(Abyss.Runtime.Art.ArtLibrary.LoadPrefab(asset.ResourcePath) == prefab, asset.Id + " production cache matches explicit resource");
                model = Abyss.Runtime.Art.ArtLibrary.SpawnCharacter(asset.ResourcePath, asset.Id, root.transform);
                view = model.gameObject;
                var animator = model.Anim as Abyss.Runtime.Art.ClipAnimator;
                Require(animator != null, asset.Id + " resolves to authored Abyss.Runtime.Art.ClipAnimator (no silent rigless fallback)");
                foreach (string motion in asset.Motions)
                    Require(!string.IsNullOrWhiteSpace(motion) && animator.HasClip(motion), asset.Id + " contains required imported take " + motion);
            }
            SetLayer(root, PreviewLayer);
            Require(view.activeInHierarchy && view.GetComponentsInChildren<Renderer>(true).Any(r => r.enabled && r.gameObject.activeInHierarchy), asset.Id + " has an active renderer");
            Require(MaterialsValid(view, out var materialDetail), asset.Id + " has renderers and non-null materials: " + Newtonsoft.Json.JsonConvert.SerializeObject(materialDetail));
            var triangles = TriangleCount(view);
            Check(asset.Id + " triangle count in declared range", triangles >= asset.MinTriangles && triangles <= asset.MaxTriangles, new { triangles, asset.MinTriangles, asset.MaxTriangles });
            var bounds = BoundsDetail(view);
            bool visibleBounds = view.GetComponentsInChildren<Renderer>(true).Where(r => !(r is ParticleSystemRenderer)).All(r => IsFinite(r.bounds.center) && IsFinite(r.bounds.size) && r.bounds.size.sqrMagnitude > 1e-8f);
            Require(visibleBounds, asset.Id + " has finite nonzero rendered bounds: " + Newtonsoft.Json.JsonConvert.SerializeObject(bounds));

            if (animated)
            {
                var skins = view.GetComponentsInChildren<SkinnedMeshRenderer>(true).Where(s => s != null && s.sharedMesh != null).ToArray();
                Require(skins.Length > 0, asset.Id + " has a skinned mesh");
                var validSkins = new System.Collections.Generic.List<SkinnedMeshRenderer>();
                foreach (var skin in skins)
                {
                    skin.updateWhenOffscreen = true; // Clone only; preserve imported source and live actors.
                    bool valid = HasRealBoneWeights(skin, out var weightsDetail);
                    Check(asset.Id + " skin has real bone influences", valid, weightsDetail);
                    if (valid)
                    {
                        float boneDelta = ProbeWeightedBone(skin);
                        Check(asset.Id + " weighted bone moves mesh: " + skin.name, boneDelta > 1e-10f, new { maxVertexDeltaSquared = boneDelta });
                        validSkins.Add(skin);
                    }
                }
                Require(validSkins.Count > 0, asset.Id + " has at least one skin with valid weighted bones");
                foreach (string motion in asset.Motions)
                {
                    var clipAnimator = (Abyss.Runtime.Art.ClipAnimator)model.Anim;
                    clipAnimator.PlayFrom(motion, 0f, 0f, null);
                    await Frames(2);
                    var samples = new System.Collections.Generic.List<(SkinnedMeshRenderer Skin, Mesh Mesh, Vector3[] Before)>();
                    foreach (var skin in validSkins)
                    {
                        var baked = new Mesh { name = "TripoEnrichmentAcceptance_Baked" };
                        ownedMeshes.Add(baked);
                        skin.BakeMesh(baked);
                        samples.Add((skin, baked, baked.vertices));
                    }
                    RenderEvidence(root, SafeName(asset.Id + "-" + motion + "-start"));
                    float delta = 0f;
                    var fractions = new[] { .15f, .3f, .5f, .7f, .9f };
                    foreach (float fraction in fractions)
                    {
                        clipAnimator.PlayFrom(motion, fraction, 0f, null);
                        await Frames(2);
                        Require(model.Anim.CurrentClip == motion && !float.IsNaN(model.Anim.NormalizedTime) && !float.IsInfinity(model.Anim.NormalizedTime), asset.Id + " samples requested take: " + motion);
                        foreach (var sample in samples) delta = Mathf.Max(delta, BakeDelta(sample.Skin, sample.Mesh, sample.Before));
                    }
                    Check(asset.Id + " motion deforms baked mesh: " + motion, delta > 1e-10f, new { maxVertexDeltaSquared = delta, normalizedSampleFractions = fractions, normalizedTime = model.Anim.NormalizedTime });
                    RenderEvidence(root, SafeName(asset.Id + "-" + motion + "-sample"));
                }
            }
            else RenderEvidence(root, SafeName(asset.Id + "-render"));

            checks.Add(new { name = asset.Id + " asset summary", passed = issues.Count == issueCount, detail = new { asset.Kind, asset.ResourcePath, triangles, bounds, motions = asset.Motions } });
        }
        catch (System.Exception e) { failed = true; issues.Add(asset.Id + ": " + e.Message); checks.Add(new { name = asset.Id + " asset evaluation", passed = false, detail = e.ToString() }); }
        finally { if (root != null) root.SetActive(false); } // Never overlap assets in later previews.
    }
}
}
catch (System.Exception e) { failed = true; issues.Add(e.ToString()); }
finally
{
try
{
foreach (var mesh in ownedMeshes) if (mesh != null) UnityEngine.Object.Destroy(mesh);
foreach (var rt in textures) if (rt != null) { rt.Release(); UnityEngine.Object.Destroy(rt); }
foreach (var go in spawned) if (go != null) UnityEngine.Object.Destroy(go);
}
catch (System.Exception e) { failed = true; issues.Add("Cleanup: " + e); }
finally { Application.logMessageReceived -= handler; }
try
{
var status = failed ? "ENRICHMENT_FAIL" : "ENRICHMENT_PASS_VISUAL_REVIEW_REQUIRED";
System.IO.File.WriteAllText(System.IO.Path.Combine(RunDir, "checks.json"), Newtonsoft.Json.JsonConvert.SerializeObject(new
{
    status,
    requestedModel = "gpt-6-astra",
    requestedEffort = "high",
    requestedServiceTier = "priority",
    routingEvidence = "requested only; runtime model route not attested by this harness",
    startedUtc = StartedUtc,
    completedUtc = System.DateTime.UtcNow.ToString("O"),
    manifestCount = Manifest == null ? 0 : Manifest.Length,
    checks,
    failures = issues,
    consoleIssues = logs,
    visualApproval = "pending parent inspection of rendered PNG evidence",
    evidenceDirectory = RunDir
}, Newtonsoft.Json.Formatting.Indented));
System.IO.File.WriteAllText(System.IO.Path.Combine(RunDir, "DONE"), status);
}
finally { lease.Dispose(); }
}
return (failed ? "ENRICHMENT_FAIL" : "ENRICHMENT_PASS_VISUAL_REVIEW_REQUIRED") + "; evidence: " + RunDir + "; rendered PNGs require parent inspection.";
}
// Fail synchronously on inaccessible output or overlapping runs instead of returning a false Started receipt.
System.IO.Directory.CreateDirectory(RunDir);
lease = new System.IO.FileStream(System.IO.Path.Combine(EvidenceRoot, "acceptance.lock"), System.IO.FileMode.OpenOrCreate, System.IO.FileAccess.ReadWrite, System.IO.FileShare.None);
_ = Run();
return "Started Unity-context enrichment acceptance; poll DONE in " + RunDir;
