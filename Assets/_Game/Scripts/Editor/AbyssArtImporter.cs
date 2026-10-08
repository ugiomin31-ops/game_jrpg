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
        static readonly string[] SlotNames = { "M_Toon", "M_Emit", "M_Clear" };
        static readonly HashSet<string> LoopClips = new HashSet<string> { "Idle", "Run", "Walk", "Fly", "Float", "BattleIdle", "Swim", "Hover" };

        static bool IsArt(string path) => path.Replace('\\', '/').StartsWith(ArtRoot);

        static bool IsAnimated(string path)
        {
            string rel = path.Replace('\\', '/').Substring(ArtRoot.Length);
            foreach (var f in AnimatedFolders)
                if (rel.StartsWith(f)) return true;
            return false;
        }

        static bool IsHumanoidAnimation(string path) => path.Replace('\\', '/').Substring(ArtRoot.Length).StartsWith(HumanoidAnimations);

        /// <summary>A character folder opts into Unity Humanoid with an empty "HUMANOID" marker file next to its model.</summary>
        static bool IsHumanoid(string path) =>
            IsHumanoidAnimation(path) || (IsAnimated(path) && File.Exists(Path.Combine(Path.GetDirectoryName(path), "HUMANOID")));

        public static bool IsEnvironment(string path)
        {
            string rel = path.Replace('\\', '/');
            return rel.Contains("/Art/Environment/") || rel.Contains("/Art/Town/") || rel.Contains("/Art/Props/");
        }

        void OnPreprocessModel()
        {
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
                return;
            }
            mi.globalScale = 1f;
            mi.useFileScale = true;
            mi.importCameras = false;
            mi.importLights = false;
            mi.importBlendShapes = false;
            mi.importVisibility = false;
            mi.isReadable = false;
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

            if (IsAnimated(assetPath))
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
            if (!IsAnimated(assetPath)) return;
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
            if (!IsArt(assetPath) || TexturedMaterials.ModelForTexture(assetPath) == null) return;
            var ti = (TextureImporter)assetImporter;
            string name = Path.GetFileNameWithoutExtension(assetPath);
            ti.textureType = TextureImporterType.Default;
            ti.sRGBTexture = true;
            ti.alphaSource = TextureImporterAlphaSource.FromInput;
            ti.alphaIsTransparency = true;
            ti.mipmapEnabled = true;
            ti.maxTextureSize = 1024;
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
                if (model == null || !IsArt(model) || IsHumanoid(model) || !TexturedMaterials.HasTextures(model)) continue;
                if (AssetImporter.GetAtPath(model) is ModelImporter) models.Add(model);
            }
            foreach (var model in models) TexturedMaterials.Sync(model);
        }

        // Shadows + light probes on every renderer of imported art.
        void OnPostprocessModel(GameObject root)
        {
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
                    m.SetFloat("_OutlineWidth", env ? 0.004f : 0.011f);
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
                if (File.Exists(model) && !File.Exists(Path.Combine(Path.GetDirectoryName(model), "HUMANOID"))) Sync(model);
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
                Configure(mat, name);
                mat.SetTexture(BaseMapId, texture);
                AssetDatabase.CreateAsset(mat, path);
            }
            else if (mat.GetTexture(BaseMapId) == null)
            {
                mat.SetTexture(BaseMapId, texture);
                EditorUtility.SetDirty(mat);
                AssetDatabase.SaveAssetIfDirty(mat);
            }
            return mat;
        }

        static void Configure(Material m, string name)
        {
            bool decal = IsDecal(name);
            // Character defaults of M_Toon_Char; the textures carry painted shading, so no toon specular blob
            // except on cloth.
            m.SetFloat("_OutlineWidth", decal ? 0f : 0.011f);
            m.SetFloat("_RimStrength", 0.35f);
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
