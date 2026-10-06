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
    /// </summary>
    public class AbyssArtImporter : AssetPostprocessor
    {
        const string ArtRoot = "Assets/_Game/Resources/Art/";
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
        static AbyssMaterials() { EditorApplication.delayCall += EnsureAll; }

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

        static void Make(string slot, bool env, Shader shader, System.Action<Material> setup)
        {
            string path = PathFor(slot, env);
            if (AssetDatabase.LoadAssetAtPath<Material>(path) != null) return;
            var m = new Material(shader) { name = Path.GetFileNameWithoutExtension(path), enableInstancing = true };
            setup(m);
            AssetDatabase.CreateAsset(m, path);
        }
    }
}
