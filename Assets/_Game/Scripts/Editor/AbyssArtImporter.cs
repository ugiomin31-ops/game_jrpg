using System.Collections.Generic;
using System.IO;
using UnityEditor;
using UnityEngine;

namespace Abyss.EditorTools
{
    /// <summary>
    /// Import contract for Blender exports under Assets/_Game/Resources/Art (see Blender/README.md).
    /// - Material slots M_Toon / M_Emit / M_Clear are remapped to shared Abyss/Toon materials
    ///   (character set or environment set depending on folder).
    /// - Animated folders (Characters, Enemies, NPCs) import as Generic rigs; takes "Rig|Idle" become clip "Idle".
    /// - Humanoid art: FBXs under HumanoidAnimations/ (one take per file, clip named after the file) and character
    ///   folders holding a "HUMANOID" marker file import as Unity Humanoid and keep their own materials
    ///   (store/Mixamo/VRoid models bring their own anime shading). VRM files import through UniVRM, not here.
    /// - Textured Blender heroes (Blender/lib_humanoid/textured.py) carry &lt;id&gt;_tex/&lt;material&gt;.png next to the
    ///   FBX: each textured material gets its own persistent Abyss/Toon material (see <see cref="TexturedMaterials"/>).
    /// </summary>
    public class AbyssArtImporter : AssetPostprocessor
    {
        public const string ArtRoot = "Assets/_Game/Resources/Art/";
        public const string MaterialDir = "Assets/_Game/Materials";
        static readonly string[] AnimatedFolders = { "Characters/", "Enemies/", "NPCs/" };
        const string HumanoidAnimations = "HumanoidAnimations/";
        // Per-class takes (Art/HumanoidAnimationsByClass/<class>/<Take>.fbx) override the shared ones by name at spawn time.
        // A sibling folder, not a subfolder: Resources.LoadAll(HumanoidAnimations) is recursive and would return duplicate names.
        const string HumanoidAnimationsByClass = "HumanoidAnimationsByClass/";
        static readonly string[] SlotNames = { "M_Toon", "M_Emit", "M_Clear" };
        static readonly HashSet<string> LoopClips = new HashSet<string> { "Idle", "Run", "Walk", "Fly", "Float", "BattleIdle", "Swim", "Hover" };

        static bool IsArt(string path) => path.Replace('\\', '/').StartsWith(ArtRoot);

        // Shared effect meshes (Resources/Vfx/Meshes/<id>.fbx) and their textures: see ArtSource/_briefs/skills_vfx.md section 5.
        public const string VfxMeshFolder = "/Resources/Vfx/Meshes/";
        const string VfxMeshTexturePrefix = "/Resources/Vfx/Textures/mesh_";
        const float VfxMeshMinExtent = .05f, VfxMeshMaxExtent = 6f;
        const int VfxMeshMaxTriangles = 1200;

        static bool IsVfxMesh(string path) =>
            path.Replace('\\', '/').Contains(VfxMeshFolder) && path.EndsWith(".fbx", System.StringComparison.OrdinalIgnoreCase);

        /// <summary>One static mesh: no materials, rig, clips or blend shapes; Blender's axis conversion is baked into the vertices.</summary>
        static void PreprocessVfxMesh(ModelImporter mi)
        {
            mi.materialImportMode = ModelImporterMaterialImportMode.None;
            mi.animationType = ModelImporterAnimationType.None;
            mi.importAnimation = false;
            mi.importBlendShapes = false;
            mi.isReadable = false;
            mi.globalScale = 1f;
            mi.useFileScale = true;
            mi.bakeAxisConversion = true;
            mi.importCameras = false;
            mi.importLights = false;
            mi.importVisibility = false;
            mi.meshCompression = ModelImporterMeshCompression.Off;
            mi.importNormals = ModelImporterNormals.Import;
            mi.importTangents = ModelImporterTangents.None;
            mi.generateSecondaryUV = false;
            mi.swapUVChannels = false;
        }

        /// <summary>
        /// The runtime takes sharedMesh and ignores node transforms, so the imported prefab must already be final:
        /// exactly one mesh on an identity node chain, native size 0.05-6 m, UVs present. Violations are import errors.
        /// </summary>
        static void ValidateVfxMesh(GameObject root, string path)
        {
            var filters = root.GetComponentsInChildren<MeshFilter>(true);
            if (filters.Length != 1 || filters[0].sharedMesh == null)
            {
                Debug.LogError($"VFX mesh {path}: expected exactly one mesh, found {filters.Length}. Join or remove the extra objects in Blender.");
                return;
            }
            if (root.GetComponentInChildren<SkinnedMeshRenderer>(true) != null || root.GetComponentInChildren<Animator>(true) != null)
                Debug.LogError($"VFX mesh {path}: must be a static mesh without armature or animation.");
            for (var t = filters[0].transform; t != null && t != root.transform.parent; t = t.parent)
            {
                if (t.localPosition.sqrMagnitude > 1e-6f || Quaternion.Angle(t.localRotation, Quaternion.identity) > .01f ||
                    (t.localScale - Vector3.one).sqrMagnitude > 1e-6f)
                    Debug.LogError($"VFX mesh {path}: node '{t.name}' carries a transform (pos {t.localPosition}, euler {t.localEulerAngles}, scale {t.localScale}). " +
                                   "Apply transforms and export Unity axes at scale 1 so axes, scale and pivot are baked into the vertices.");
            }
            var mesh = filters[0].sharedMesh;
            Vector3 size = mesh.bounds.size;
            float longest = Mathf.Max(size.x, Mathf.Max(size.y, size.z));
            if (!(longest >= VfxMeshMinExtent && longest <= VfxMeshMaxExtent))
                Debug.LogError($"VFX mesh {path}: imported bounds {size} are outside {VfxMeshMinExtent}-{VfxMeshMaxExtent} m (check export scale).");
            if (mesh.uv.Length == 0) Debug.LogError($"VFX mesh {path}: no UV0.");
            if (mesh.colors.Length == 0) Debug.LogWarning($"VFX mesh {path}: no 'Col' vertex colour (fade mask); it renders fully opaque.");
            if (mesh.triangles.Length / 3 > VfxMeshMaxTriangles)
                Debug.LogWarning($"VFX mesh {path}: {mesh.triangles.Length / 3} triangles (budget about 1000).");
        }

        static bool IsAnimated(string path)
        {
            string rel = path.Replace('\\', '/').Substring(ArtRoot.Length);
            foreach (var f in AnimatedFolders)
                if (rel.StartsWith(f)) return true;
            return false;
        }

        static bool IsHumanoidAnimation(string path)
        {
            string rel = path.Replace('\\', '/').Substring(ArtRoot.Length);
            return rel.StartsWith(HumanoidAnimations) || rel.StartsWith(HumanoidAnimationsByClass);
        }

        /// <summary>A character folder opts into Unity Humanoid with an empty "HUMANOID" marker file next to its model.</summary>
        static bool IsHumanoid(string path) =>
            IsHumanoidAnimation(path) || (IsAnimated(path) && File.Exists(Path.Combine(Path.GetDirectoryName(path), "HUMANOID")));

        /// <summary>
        /// Winged enemy whose Tripo skin failed the rig gate (approved code-animation exception, 2026-10-12): an explicitly
        /// listed id (<see cref="Abyss.Runtime.Art.ArtLibrary.IsRiglessFlyer"/>) at Enemies/&lt;id&gt;/&lt;id&gt;.fbx whose folder
        /// holds a "FLYER" marker (written by the install step). It imports as a static three-part model (Body, Wing_L,
        /// Wing_R): no rig, no takes. Listed flyers still shipping rigged takes (no marker) keep the Generic import.
        /// </summary>
        public static bool IsRiglessFlyerModel(string path)
        {
            string rel = path.Replace('\\', '/');
            if (!rel.StartsWith(ArtRoot + "Enemies/", System.StringComparison.Ordinal)) return false;
            string id = Path.GetFileNameWithoutExtension(rel);
            return rel == $"{ArtRoot}Enemies/{id}/{id}.fbx" && Abyss.Runtime.Art.ArtLibrary.IsRiglessFlyer(id) &&
                   File.Exists(Path.Combine(Path.GetDirectoryName(path), "FLYER"));
        }

        public static bool IsTripo(string path) =>
            File.Exists(Path.Combine(Path.GetDirectoryName(path), "TRIPO")) ||
            File.Exists(Path.ChangeExtension(path, ".tripo"));

        public static bool IsEnvironment(string path)
        {
            string rel = path.Replace('\\', '/');
            return rel.Contains("/Art/Environment/") || rel.Contains("/Art/Town/") || rel.Contains("/Art/Props/");
        }

        static bool ReadableArena(string path)
        {
            string rel = path.Replace('\\', '/');
            return rel.Contains("/Art/Environment/") && rel.EndsWith("/arena.fbx", System.StringComparison.OrdinalIgnoreCase);
        }

        void OnPreprocessModel()
        {
            if (IsVfxMesh(assetPath)) { PreprocessVfxMesh((ModelImporter)assetImporter); return; }
            if (!IsArt(assetPath)) return;
            var mi = (ModelImporter)assetImporter;
            if (IsHumanoid(assetPath))
            {
                mi.animationType = ModelImporterAnimationType.Human;
                mi.avatarSetup = ModelImporterAvatarSetup.CreateFromThisModel;
                mi.importAnimation = true;
                mi.optimizeGameObjects = false;
                mi.importCameras = false;
                mi.importLights = false;
                mi.materialImportMode = IsHumanoidAnimation(assetPath) ? ModelImporterMaterialImportMode.None : ModelImporterMaterialImportMode.ImportStandard;
                if (IsTripo(assetPath))
                {
                    mi.globalScale = 1f;
                    mi.useFileScale = true;
                    mi.materialLocation = ModelImporterMaterialLocation.InPrefab;
                    foreach (var pair in TexturedMaterials.Existing(assetPath))
                        mi.AddRemap(new AssetImporter.SourceAssetIdentifier(typeof(Material), pair.Key), pair.Value);
                }
                return;
            }
            mi.globalScale = 1f;
            mi.useFileScale = true;
            mi.importCameras = false;
            mi.importLights = false;
            mi.importBlendShapes = false;
            mi.importVisibility = false;
            // Battle arenas stay readable: the camera director derives occluder boxes for the posts and machines of the merged props shell.
            mi.isReadable = ReadableArena(assetPath);
            mi.meshCompression = ModelImporterMeshCompression.Off;
            mi.importNormals = ModelImporterNormals.Import;
            mi.materialImportMode = ModelImporterMaterialImportMode.ImportStandard;
            mi.materialLocation = ModelImporterMaterialLocation.InPrefab;

            AbyssMaterials.EnsureAll();
            bool env = IsEnvironment(assetPath);
            foreach (var slot in SlotNames)
            {
                var mat = AbyssMaterials.Get(slot, env);
                if (mat != null)
                    mi.AddRemap(new AssetImporter.SourceAssetIdentifier(typeof(Material), slot), mat);
            }
            // Textured heroes: per-model materials that already exist (TexturedMaterials.Sync creates missing ones).
            foreach (var pair in TexturedMaterials.Existing(assetPath))
                mi.AddRemap(new AssetImporter.SourceAssetIdentifier(typeof(Material), pair.Key), pair.Value);

            if (IsRiglessFlyerModel(assetPath))
            {
                mi.animationType = ModelImporterAnimationType.None;
                mi.importAnimation = false;
                mi.optimizeGameObjects = false;
            }
            else if (IsAnimated(assetPath))
            {
                mi.animationType = ModelImporterAnimationType.Generic;
                mi.avatarSetup = ModelImporterAvatarSetup.CreateFromThisModel;
                mi.importAnimation = true;
                mi.optimizeGameObjects = false;
                mi.resampleCurves = true;
                mi.animationCompression = ModelImporterAnimationCompression.KeyframeReduction;
            }
            else
            {
                mi.animationType = ModelImporterAnimationType.None;
                mi.importAnimation = false;
            }
        }

        void OnPreprocessAnimation()
        {
            if (!IsArt(assetPath)) return;
            var mi = (ModelImporter)assetImporter;
            if (IsHumanoidAnimation(assetPath))
            {
                // Mixamo-style files carry one take named "mixamo.com": the file name is the clip name.
                var takes = mi.defaultClipAnimations;
                if (takes.Length == 0) return;
                var take = takes[0];
                take.name = Path.GetFileNameWithoutExtension(assetPath);
                take.loopTime = LoopClips.Contains(take.name) || take.name.EndsWith("Loop");
                take.lockRootRotation = take.lockRootHeightY = take.lockRootPositionXZ = true;
                take.keepOriginalOrientation = take.keepOriginalPositionY = take.keepOriginalPositionXZ = true;
                mi.clipAnimations = new[] { take };
                return;
            }
            if (!IsAnimated(assetPath) || IsRiglessFlyerModel(assetPath)) return;
            var clips = mi.defaultClipAnimations;
            var outClips = new List<ModelImporterClipAnimation>();
            var seen = new HashSet<string>();
            foreach (var c in clips)
            {
                string name = c.takeName;
                int bar = name.LastIndexOf('|');
                if (bar >= 0) name = name.Substring(bar + 1);
                if (!seen.Add(name)) continue;
                c.name = name;
                c.loopTime = LoopClips.Contains(name) || name.EndsWith("Loop");
                c.loopPose = false;
                c.lockRootRotation = false;
                c.lockRootHeightY = false;
                c.lockRootPositionXZ = false;
                outClips.Add(c);
            }
            mi.clipAnimations = outClips.ToArray();
        }

        // Textures of textured heroes (<id>_tex/*.png): sRGB, mipmapped, mobile-sized; cut-out layers keep their coverage.
        void OnPreprocessTexture()
        {
            // Effect mesh masks: U repeats so `scroll` can sweep a highlight along the mesh; V stays clamped.
            if (assetPath.Replace('\\', '/').Contains(VfxMeshTexturePrefix))
            {
                var vfx = (TextureImporter)assetImporter;
                vfx.wrapModeU = TextureWrapMode.Repeat;
                vfx.wrapModeV = TextureWrapMode.Clamp;
                return;
            }
            if (!IsArt(assetPath)) return;
            string model = TexturedMaterials.ModelForTexture(assetPath);
            if (model == null) return;
            var ti = (TextureImporter)assetImporter;
            string name = Path.GetFileNameWithoutExtension(assetPath);
            ti.textureType = TextureImporterType.Default;
            ti.sRGBTexture = true;
            ti.alphaSource = TextureImporterAlphaSource.FromInput;
            ti.alphaIsTransparency = true;
            ti.mipmapEnabled = true;
            // Tripo heroes and town buildings keep 2k; dungeon props stay at 1k.
            bool town = model.Contains("/Art/Town/");
            ti.maxTextureSize = IsTripo(model) && (town || !IsEnvironment(model)) ? 2048 : 1024;
            ti.textureCompression = TextureImporterCompression.Compressed;
            ti.mipMapsPreserveCoverage = TexturedMaterials.IsCutout(name);
            ti.alphaTestReferenceValue = 0.5f;
        }

        // Textured heroes: once the textures and the model are in, create their materials and remap them.
        static void OnPostprocessAllAssets(string[] imported, string[] deleted, string[] moved, string[] movedFrom)
        {
            var models = new HashSet<string>();
            foreach (var raw in imported)
            {
                string path = raw.Replace('\\', '/');
                if (!IsArt(path)) continue;
                string model = path.EndsWith(".fbx", System.StringComparison.OrdinalIgnoreCase)
                    ? path : TexturedMaterials.ModelForTexture(path);
                if (model == null || !IsArt(model) || (IsHumanoid(model) && !IsTripo(model)) || !TexturedMaterials.HasTextures(model)) continue;
                if (AssetImporter.GetAtPath(model) is ModelImporter) models.Add(model);
            }
            foreach (var model in models) TexturedMaterials.Sync(model);
        }

        /// <summary>
        /// Blender de-duplicates material names inside one session ("M_SubwayWall_Tripo.001" for the second tile exported
        /// from a scene that already holds "M_SubwayWall_Tripo"), and the FBX carries that name. The name-keyed remaps in
        /// <see cref="OnPreprocessModel"/> and <see cref="TexturedMaterials.Sync"/> then miss it and Unity builds a private
        /// URP/Lit copy. Strip the numeric duplicate suffix here so b/c variants bind exactly what the a variant binds:
        /// the model's own textured material, or the shared Abyss/Toon slot material.
        /// </summary>
        Material OnAssignMaterialModel(Material material, Renderer renderer)
        {
            if (material == null || !IsArt(assetPath) || IsHumanoid(assetPath)) return null;
            string name = material.name;
            int dot = name.LastIndexOf('.');
            if (dot <= 0 || name.Length - dot != 4 || !char.IsDigit(name[dot + 1]) || !char.IsDigit(name[dot + 2]) || !char.IsDigit(name[dot + 3])) return null;
            string baseName = name.Substring(0, dot);
            if (TexturedMaterials.Existing(assetPath).TryGetValue(baseName, out var own)) return own;
            if (System.Array.IndexOf(SlotNames, baseName) >= 0) return AbyssMaterials.Get(baseName, IsEnvironment(assetPath));
            return null;
        }

        // Shadows + light probes on every renderer of imported art.
        void OnPostprocessModel(GameObject root)
        {
            if (IsVfxMesh(assetPath)) { ValidateVfxMesh(root, assetPath); return; }
            if (!IsArt(assetPath)) return;
            foreach (var r in root.GetComponentsInChildren<Renderer>(true))
            {
                r.shadowCastingMode = UnityEngine.Rendering.ShadowCastingMode.On;
                r.receiveShadows = true;
            }
            if (!IsEnvironment(assetPath)) return;
            bool town = assetPath.Replace('\\', '/').Contains("/Art/Town/");
            foreach (var filter in root.GetComponentsInChildren<MeshFilter>(true))
            {
                if (!filter.name.StartsWith("Col_") || filter.sharedMesh == null) continue;
                if (town)
                {
                    // Town generators author exact local-space boxes; retain that primitive shape.
                    var box = filter.gameObject.AddComponent<BoxCollider>();
                    box.center = filter.sharedMesh.bounds.center;
                    box.size = filter.sharedMesh.bounds.size;
                }
                else
                {
                    // Cook mesh proxies during import, before non-readable vertex data is stripped.
                    var collider = filter.gameObject.AddComponent<MeshCollider>();
                    collider.sharedMesh = filter.sharedMesh;
                }
                var renderer = filter.GetComponent<MeshRenderer>();
                if (renderer != null) renderer.enabled = false;
            }
        }
    }

    /// <summary>Shared materials for the Blender slot names. Created on demand, never per-model.</summary>
    [InitializeOnLoad]
    public static class AbyssMaterials
    {
        static AbyssMaterials() { EditorApplication.delayCall += () => { EnsureAll(); TexturedMaterials.SyncAll(); RestoreToonLook(); }; }

        public static string PathFor(string slot, bool env) =>
            $"{AbyssArtImporter.MaterialDir}/{slot}{(env ? "_Env" : "_Char")}.mat";

        public static Material Get(string slot, bool env) =>
            AssetDatabase.LoadAssetAtPath<Material>(PathFor(slot, env));

        public static void EnsureAll()
        {
            var shader = Shader.Find("Abyss/Toon");
            if (shader == null) return;
            if (!Directory.Exists(AbyssArtImporter.MaterialDir)) Directory.CreateDirectory(AbyssArtImporter.MaterialDir);
            foreach (bool env in new[] { false, true })
            {
                Make("M_Toon", env, shader, m =>
                {
                    m.SetFloat("_OutlineWidth", env ? 0.004f : TexturedMaterials.VRoidOutlineWidth);
                    m.SetFloat("_NoiseStrength", env ? 0.10f : 0f);
                    m.SetFloat("_RimStrength", env ? 0.12f : 0.35f);
                });
                Make("M_Emit", env, shader, m =>
                {
                    m.SetFloat("_EmissionStrength", 1.6f);
                    m.SetFloat("_OutlineWidth", env ? 0f : 0.006f);
                    m.SetFloat("_RimStrength", 0.2f);
                });
                Make("M_Clear", env, shader, m =>
                {
                    m.SetFloat("_Alpha", 0.72f);
                    m.SetFloat("_SrcBlend", (float)UnityEngine.Rendering.BlendMode.SrcAlpha);
                    m.SetFloat("_DstBlend", (float)UnityEngine.Rendering.BlendMode.OneMinusSrcAlpha);
                    m.SetFloat("_ZWrite", 0f);
                    m.SetFloat("_OutlineWidth", 0f);
                    m.SetFloat("_RimStrength", 0.8f);
                    m.SetFloat("_Specular", 0.5f);
                    m.renderQueue = 3000;
                    m.SetOverrideTag("RenderType", "Transparent");
                });
            }
        }

        /// <summary>
        /// Undoes the toned-down "Apply Art Polish" pass (thin outlines, weak rim, soft shadow bands) on projects that
        /// already ran it. Only values that still equal that pass's exact output are reset, so hand tuning survives.
        /// </summary>
        [MenuItem("Abyss/Restore Toon Look")]
        public static void RestoreToonLook()
        {
            foreach (bool env in new[] { false, true })
            {
                var toon = Get("M_Toon", env); var emit = Get("M_Emit", env);
                Revert(toon, "_OutlineWidth", env ? .002f : .0055f, env ? .004f : .011f);
                Revert(toon, "_NoiseStrength", .065f, .10f, env);
                Revert(toon, "_RimStrength", env ? .08f : .22f, env ? .12f : .35f);
                Revert(emit, "_EmissionStrength", 1.1f, 1.6f);
                Revert(emit, "_OutlineWidth", .003f, .006f, !env);
                foreach (var m in new[] { toon, emit, Get("M_Clear", env) })
                {
                    Revert(m, "_ShadowSoftness", .12f, .06f);
                    Revert(m, "_MidBand", .16f, .25f);
                }
                Revert(toon, "_Specular", .08f, .12f);
                Revert(emit, "_Specular", .08f, .12f);
                Revert(Get("M_Clear", env), "_Specular", .35f, .5f);
            }
            if (!AssetDatabase.IsValidFolder(AbyssArtImporter.ArtRoot.TrimEnd('/'))) return;
            foreach (string guid in AssetDatabase.FindAssets("t:Material", new[] { AbyssArtImporter.ArtRoot.TrimEnd('/') }))
            {
                string path = AssetDatabase.GUIDToAssetPath(guid);
                if (!path.Contains("_mat/")) continue;
                var m = AssetDatabase.LoadAssetAtPath<Material>(path);
                if (m == null || m.shader.name != "Abyss/Toon") continue;
                Revert(m, "_OutlineWidth", .003f, .011f);
                Revert(m, "_ShadowSoftness", .12f, .06f);
                Revert(m, "_RimStrength", .18f, .35f);
            }
        }

        static void Revert(Material m, string property, float polished, float original, bool apply = true)
        {
            if (!apply || m == null || !m.HasProperty(property) || !Mathf.Approximately(m.GetFloat(property), polished)) return;
            m.SetFloat(property, original);
            EditorUtility.SetDirty(m);
        }

        static void Make(string slot, bool env, Shader shader, System.Action<Material> setup)
        {
            string path = PathFor(slot, env);
            if (AssetDatabase.LoadAssetAtPath<Material>(path) != null) return;
            var m = new Material(shader) { name = Path.GetFileNameWithoutExtension(path), enableInstancing = true };
            setup(m);
            AssetDatabase.CreateAsset(m, path);
        }
    }

    /// <summary>
    /// Textured heroes (Blender/lib_humanoid/textured.py): &lt;id&gt;.fbx keeps its material names, and every textured
    /// material &lt;name&gt; has &lt;id&gt;_tex/&lt;name&gt;.png beside it. Each gets a persistent Abyss/Toon material
    /// &lt;id&gt;_mat/&lt;name&gt;.mat with _BaseMap = that PNG, remapped onto the FBX material of the same name.
    /// The material is configured once when created and then left alone (hand tweaks survive reimports; delete it to
    /// regenerate). M_Toon / M_Emit / M_Clear on the same model keep the shared remap.
    /// VRoid name suffixes pick the setup: _FACE / _EYE alpha cutout, no outline, no shadow casting;
    /// _HAIR alpha cutout + double-sided; _CLOTH double-sided; anything else (_SKIN) opaque.
    /// </summary>
    public static class TexturedMaterials
    {
        public const string TextureSuffix = "_tex";
        public const string MaterialSuffix = "_mat";
        const string BaseMapId = "_BaseMap";

        static string Normalize(string path) => path.Replace('\\', '/');

        static string Sibling(string modelPath, string suffix)
        {
            string p = Normalize(modelPath);
            return p.Substring(0, p.LastIndexOf('/') + 1) + Path.GetFileNameWithoutExtension(p) + suffix;
        }

        public static string TextureDir(string modelPath) => Sibling(modelPath, TextureSuffix);
        public static string MaterialFolder(string modelPath) => Sibling(modelPath, MaterialSuffix);
        public static string MaterialPath(string modelPath, string name) => $"{MaterialFolder(modelPath)}/{name}.mat";
        public static bool HasTextures(string modelPath) => Directory.Exists(TextureDir(modelPath));

        static bool HasSuffix(string name, string suffix) => name.EndsWith(suffix, System.StringComparison.OrdinalIgnoreCase);
        public static bool IsDecal(string name) => HasSuffix(name, "_FACE") || HasSuffix(name, "_EYE");
        public static bool IsCutout(string name) => IsDecal(name) || HasSuffix(name, "_HAIR");
        public static bool IsDoubleSided(string name) => HasSuffix(name, "_HAIR") || HasSuffix(name, "_CLOTH");

        /// <summary>The model a texture belongs to: ".../&lt;id&gt;_tex/x.png" -> ".../&lt;id&gt;.fbx"; null for any other path.</summary>
        public static string ModelForTexture(string texturePath)
        {
            string p = Normalize(texturePath);
            if (!p.EndsWith(".png", System.StringComparison.OrdinalIgnoreCase)) return null;
            int slash = p.LastIndexOf('/');
            if (slash <= 0) return null;
            string dir = p.Substring(0, slash);
            int parentSlash = dir.LastIndexOf('/');
            string folder = dir.Substring(parentSlash + 1);
            if (folder.Length <= TextureSuffix.Length || !folder.EndsWith(TextureSuffix)) return null;
            return dir.Substring(0, parentSlash + 1) + folder.Substring(0, folder.Length - TextureSuffix.Length) + ".fbx";
        }

        static string[] TextureFiles(string modelPath)
        {
            string dir = TextureDir(modelPath);
            if (!Directory.Exists(dir)) return new string[0];
            var files = Directory.GetFiles(dir, "*.png");
            for (int i = 0; i < files.Length; i++) files[i] = Normalize(files[i]);
            System.Array.Sort(files, System.StringComparer.Ordinal);
            return files;
        }

        /// <summary>Per-model materials that already exist, keyed by source material name (used by the import remap).</summary>
        public static Dictionary<string, Material> Existing(string modelPath)
        {
            var result = new Dictionary<string, Material>();
            foreach (var tex in TextureFiles(modelPath))
            {
                string name = Path.GetFileNameWithoutExtension(tex);
                var mat = AssetDatabase.LoadAssetAtPath<Material>(MaterialPath(modelPath, name));
                if (mat != null) result[name] = mat;
            }
            return result;
        }

        /// <summary>Every textured model under the art root (domain reload / manual menu).</summary>
        [MenuItem("Abyss/Sync Textured Hero Materials")]
        public static void SyncAll()
        {
            string root = AbyssArtImporter.ArtRoot.TrimEnd('/');
            if (!Directory.Exists(root)) return;
            foreach (var dir in Directory.GetDirectories(root, "*" + TextureSuffix, SearchOption.AllDirectories))
            {
                string d = Normalize(dir);
                string model = d.Substring(0, d.Length - TextureSuffix.Length) + ".fbx";
                if (File.Exists(model) && (!File.Exists(Path.Combine(Path.GetDirectoryName(model), "HUMANOID")) || AbyssArtImporter.IsTripo(model))) Sync(model);
            }
        }

        /// <summary>
        /// Creates missing materials, refills a missing _BaseMap and remaps them onto the model, reimporting it once
        /// when the remap changed. Safe to repeat: a second call finds everything in place and does nothing.
        /// </summary>
        public static void Sync(string modelPath)
        {
            var mi = AssetImporter.GetAtPath(modelPath) as ModelImporter;
            var shader = Shader.Find("Abyss/Toon");
            if (mi == null || shader == null) return;
            var mapped = new Dictionary<string, Object>();
            foreach (var pair in mi.GetExternalObjectMap())
                if (pair.Key.type == typeof(Material)) mapped[pair.Key.name] = pair.Value;
            bool changed = false;
            foreach (var tex in TextureFiles(modelPath))
            {
                var texture = AssetDatabase.LoadAssetAtPath<Texture2D>(tex);
                if (texture == null) continue; // not imported yet: its own import calls Sync again
                string name = Path.GetFileNameWithoutExtension(tex);
                var mat = Ensure(modelPath, name, texture, shader);
                if (mapped.TryGetValue(name, out var current) && current == mat) continue;
                mi.AddRemap(new AssetImporter.SourceAssetIdentifier(typeof(Material), name), mat);
                changed = true;
            }
            if (changed) mi.SaveAndReimport();
        }

        static Material Ensure(string modelPath, string name, Texture2D texture, Shader shader)
        {
            string folder = MaterialFolder(modelPath);
            if (!AssetDatabase.IsValidFolder(folder))
            {
                int slash = folder.LastIndexOf('/');
                AssetDatabase.CreateFolder(folder.Substring(0, slash), folder.Substring(slash + 1));
            }
            string path = MaterialPath(modelPath, name);
            var mat = AssetDatabase.LoadAssetAtPath<Material>(path);
            if (mat == null)
            {
                mat = new Material(shader) { name = name, enableInstancing = true };
                Configure(mat, name, AbyssArtImporter.IsEnvironment(modelPath), AbyssArtImporter.IsTripo(modelPath));
                mat.SetTexture(BaseMapId, texture);
                AssetDatabase.CreateAsset(mat, path);
            }
            else
            {
                bool dirty = false;
                if (mat.GetTexture(BaseMapId) == null) { mat.SetTexture(BaseMapId, texture); dirty = true; }
                // Outline widths of existing materials are NOT migrated here (a folder can hold stale materials the model
                // never binds): see MigrateBoundOutlines, which only touches materials the model's renderers use.
                if (dirty)
                {
                    EditorUtility.SetDirty(mat);
                    AssetDatabase.SaveAssetIfDirty(mat);
                }
            }
            return mat;
        }

        // Stock (shader / importer default) values that the outline migration recognises. Anything else is hand tuning.
        const float StockCharacterOutlineWidth = 0.011f;   // old VRoid characters and the first Tripo import
        const float StockTripoOutlineWidth = 0.004f;       // first Tripo hull (2 px at 1080p)
        static readonly Color StockOutlineColor = new Color(0.10f, 0.07f, 0.12f, 1f);
        const float StockOutlineTintMix = 0.35f;

        // Role widths, in NDC (1 unit = half the screen height; 0.0028 is about 1.5 px at 1080p). Tripo meshes are dense,
        // noisy and layered (clothes over body, eyes inside lids). A thick screen-space hull pokes through those layers as
        // black bars across the eyes and streaks over the clothes (verified: hull off = clean). A thin hull pushed 6 cm
        // away from the camera stays hidden behind the shell and only shows as a silhouette line.
        public const float TripoOutlineWidth = 0.0028f;
        public const float TripoOutlineZOffset = 0.06f;
        /// <summary>Remaining VRoid hunters (until they are replaced by Tripo models).</summary>
        public const float VRoidOutlineWidth = 0.006f;
        /// <summary>Softer line: a dark tint of the surface (vertex colour) instead of a black stroke.</summary>
        public static readonly Color SoftOutlineColor = new Color(0.16f, 0.13f, 0.20f, 1f);
        public const float SoftOutlineTintMix = 0.55f;

        static void ApplyTripoOutline(Material m)
        {
            m.SetFloat("_OutlineWidth", TripoOutlineWidth);
            m.SetFloat("_OutlineZOffset", TripoOutlineZOffset);
            ApplySoftOutlineColor(m);
        }

        static void ApplySoftOutlineColor(Material m)
        {
            if (m.HasProperty("_OutlineColor") && SameColor(m.GetColor("_OutlineColor"), StockOutlineColor))
                m.SetColor("_OutlineColor", SoftOutlineColor);
            if (m.HasProperty("_OutlineTintMix") && Mathf.Approximately(m.GetFloat("_OutlineTintMix"), StockOutlineTintMix))
                m.SetFloat("_OutlineTintMix", SoftOutlineTintMix);
        }

        static bool SameColor(Color a, Color b) =>
            Mathf.Abs(a.r - b.r) < 0.003f && Mathf.Abs(a.g - b.g) < 0.003f && Mathf.Abs(a.b - b.b) < 0.003f;
        static bool Near(float a, float b) => Mathf.Abs(a - b) < 0.00015f;

        /// <summary>
        /// Moves an existing character material from the stock outline values to the role widths. Only identified stock
        /// values are replaced (hand tuning survives); decals (width 0) and environment models are never touched.
        /// Returns true when the material changed.
        /// </summary>
        public static bool MigrateOutline(Material m, string modelPath)
        {
            if (m == null || m.shader == null || m.shader.name != "Abyss/Toon" || AbyssArtImporter.IsEnvironment(modelPath)) return false;
            float width = m.GetFloat("_OutlineWidth"), z = m.GetFloat("_OutlineZOffset");
            if (width < 0.0001f) return false; // decal: no hull
            bool changed = false;
            if (AbyssArtImporter.IsTripo(modelPath))
            {
                bool plain = Near(width, StockCharacterOutlineWidth) && Near(z, 0f);
                bool firstHull = Near(width, StockTripoOutlineWidth) && z >= 0.0099f;
                if (plain) { ApplyTripoOutline(m); changed = true; }
                else if (firstHull) { m.SetFloat("_OutlineWidth", TripoOutlineWidth); ApplySoftOutlineColor(m); changed = true; }
            }
            else if (Near(width, StockCharacterOutlineWidth))
            {
                m.SetFloat("_OutlineWidth", VRoidOutlineWidth);
                ApplySoftOutlineColor(m);
                changed = true;
            }
            if (changed) EditorUtility.SetDirty(m);
            return changed;
        }

        /// <summary>
        /// Outline migration of one model: only the materials its prefab's renderers actually bind (and that live in the
        /// model's own _mat folder) are migrated, so stale VRoid materials left in a Tripo folder keep their GUIDs and values.
        /// </summary>
        public static int MigrateBoundOutlines(string modelPath, List<string> log = null)
        {
            var prefab = AssetDatabase.LoadAssetAtPath<GameObject>(modelPath);
            if (prefab == null) return 0;
            string folder = MaterialFolder(modelPath) + "/";
            var seen = new HashSet<Material>();
            int count = 0;
            foreach (var r in prefab.GetComponentsInChildren<Renderer>(true))
                foreach (var m in r.sharedMaterials)
                {
                    if (m == null || !seen.Add(m)) continue;
                    string path = AssetDatabase.GetAssetPath(m);
                    if (!path.StartsWith(folder, System.StringComparison.Ordinal)) continue;
                    float w0 = m.GetFloat("_OutlineWidth");
                    if (MigrateOutline(m, modelPath)) { count++; log?.Add(path + ": " + w0.ToString("0.####") + " -> " + m.GetFloat("_OutlineWidth").ToString("0.####")); }
                }
            if (count > 0) AssetDatabase.SaveAssets();
            return count;
        }

        /// <summary>Every textured character, enemy, NPC and weapon model (environment excluded).</summary>
        [MenuItem("Abyss/Migrate Bound Outline Widths")]
        public static void MigrateAllBoundOutlines()
        {
            var log = new List<string>();
            foreach (string guid in AssetDatabase.FindAssets("t:Model", new[] { AbyssArtImporter.ArtRoot.TrimEnd('/') }))
            {
                string path = AssetDatabase.GUIDToAssetPath(guid);
                if (!path.EndsWith(".fbx", System.StringComparison.OrdinalIgnoreCase) || !HasTextures(path)) continue;
                if (path.Contains("/HumanoidAnimations/") || path.Contains("/HumanoidAnimationsByClass/")) continue;
                MigrateBoundOutlines(path, log);
            }
            // The shared character toon material is bound by the town villagers / innkeeper (and old procedural models):
            // same stock 0.011 -> VRoid-role width. The environment set and M_Emit are left alone.
            var shared = AbyssMaterials.Get("M_Toon", false);
            if (shared != null && Near(shared.GetFloat("_OutlineWidth"), StockCharacterOutlineWidth))
            {
                shared.SetFloat("_OutlineWidth", VRoidOutlineWidth);
                ApplySoftOutlineColor(shared);
                EditorUtility.SetDirty(shared);
                AssetDatabase.SaveAssets();
                log.Add(AbyssMaterials.PathFor("M_Toon", false) + ": 0.011 -> " + VRoidOutlineWidth.ToString("0.####"));
            }
            Debug.Log("Outline migration: " + log.Count + " material(s)\n" + string.Join("\n", log));
        }

        static void Configure(Material m, string name, bool environment, bool tripo = false)
        {
            bool decal = IsDecal(name);
            // Character defaults of M_Toon_Char; the textures carry painted shading, so no toon specular blob
            // except on cloth.
            m.SetFloat("_OutlineWidth", decal ? 0f : environment ? 0.004f : VRoidOutlineWidth);
            if (tripo && !environment && !decal) ApplyTripoOutline(m);
            else if (!environment && !decal) ApplySoftOutlineColor(m);
            m.SetFloat("_RimStrength", environment ? 0.12f : 0.35f);
            m.SetFloat("_NoiseStrength", 0f);
            m.SetFloat("_Specular", HasSuffix(name, "_CLOTH") ? 0.12f : 0f);
            // Eyes should not go dull in the shadow band.
            if (HasSuffix(name, "_EYE")) m.SetColor("_ShadowTint", new Color(0.86f, 0.84f, 0.94f, 1f));
            if (IsCutout(name))
            {
                m.SetFloat("_AlphaClip", 1f);
                m.SetFloat("_Cutoff", 0.5f);
                m.EnableKeyword("_ALPHATEST_ON");
                m.SetOverrideTag("RenderType", "TransparentCutout");
                m.renderQueue = (int)UnityEngine.Rendering.RenderQueue.AlphaTest;
            }
            if (IsDoubleSided(name))
            {
                m.SetFloat("_Cull", (float)UnityEngine.Rendering.CullMode.Off);
                // Single-layer hair cards / cloth: push the hull 1 cm back so a card seen from behind keeps its
                // texture instead of the outline colour (the hull and the card would otherwise share a depth).
                m.SetFloat("_OutlineZOffset", 0.01f);
            }
            // Brows, lashes, eyes sit just above the face: their shadows would draw dark streaks on the skin.
            if (decal) m.SetShaderPassEnabled("ShadowCaster", false);
        }
    }
}
