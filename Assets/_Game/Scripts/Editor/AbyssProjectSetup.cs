using System;
using System.Collections.Generic;
using System.IO;
using System.Linq;
using System.Reflection;
using Abyss.Logic;
using Abyss.Runtime;
using Abyss.Runtime.Art;
using UnityEditor;
using UnityEditor.Build.Reporting;
using UnityEditor.SceneManagement;
using UnityEngine;
using UnityEngine.Audio;
using UnityEngine.SceneManagement;

namespace Abyss.EditorTools
{
    public static class AbyssProjectSetup
    {
        public const string MainScenePath = "Assets/_Game/Scenes/Main.unity";
        const string MixerPath = "Assets/_Game/Resources/Audio/AbyssMixer.mixer";
        const BindingFlags InstanceFlags = BindingFlags.Instance | BindingFlags.Public | BindingFlags.NonPublic;

        [MenuItem("Abyss/Prepare Game")]
        public static void Prepare()
        {
            if (EditorApplication.isPlaying) throw new InvalidOperationException("Stop play mode before preparing the project.");
            AbyssMaterials.EnsureAll();
            TexturedMaterials.SyncAll(); // textured anime heroes: per-texture Abyss/Toon materials, also in batch builds
            AbyssMaterials.RestoreToonLook();
            EnsureMixer();
            EnsureVfxShader();
            Directory.CreateDirectory("Assets/_Game/Scenes");
            if (AssetDatabase.LoadAssetAtPath<SceneAsset>(MainScenePath) == null)
            {
                var scene = EditorSceneManager.NewScene(NewSceneSetup.EmptyScene, NewSceneMode.Single);
                new GameObject("Abyss Game").AddComponent<GameApp>();
                EditorSceneManager.SaveScene(scene, MainScenePath);
            }
            else EditorSceneManager.OpenScene(MainScenePath, OpenSceneMode.Single);
            EditorBuildSettings.scenes = new[] { new EditorBuildSettingsScene(MainScenePath, true) };
            PlayerSettings.productName = "Abyss Labyrinth";
            PlayerSettings.defaultScreenWidth = 1920;
            PlayerSettings.defaultScreenHeight = 1080;
            PlayerSettings.resizableWindow = true;
            PlayerSettings.runInBackground = true;
            PlayerSettings.SetScriptingBackend(UnityEditor.Build.NamedBuildTarget.Standalone, ScriptingImplementation.Mono2x);
            AssetDatabase.SaveAssets();
            Debug.Log("Abyss main scene, audio mixer and shader resources prepared.");
        }

        static void EnsureVfxShader()
        {
            const string path = "Assets/_Game/Resources/Vfx/RuntimeShader.mat";
            if (AssetDatabase.LoadAssetAtPath<Material>(path) != null) return;
            var shader = Shader.Find("Abyss/VfxUnlit");
            if (shader == null) throw new InvalidOperationException("Missing VFX shader.");
            Directory.CreateDirectory(Path.GetDirectoryName(path));
            AssetDatabase.CreateAsset(new Material(shader) { name = "Abyss Runtime VFX" }, path);
        }

        static void EnsureMixer()
        {
            if (AssetDatabase.LoadAssetAtPath<AudioMixer>(MixerPath) != null) return;
            // Unity's mixer asset factory is editor-internal. Signatures are inspected against this pinned editor version.
            var type = typeof(UnityEditor.Editor).Assembly.GetType("UnityEditor.Audio.AudioMixerController", true);
            var factory = type.GetMethod("CreateMixerControllerAtPath", BindingFlags.Static | BindingFlags.Public | BindingFlags.NonPublic);
            Directory.CreateDirectory(Path.GetDirectoryName(MixerPath));
            var controller = (UnityEngine.Object)factory.Invoke(null, new object[] { MixerPath });
            var master = type.GetProperty("masterGroup", InstanceFlags).GetValue(controller);
            var groupType = master.GetType();
            var groups = Array.CreateInstance(groupType, 2);
            var createGroup = type.GetMethod("CreateNewGroup", InstanceFlags);
            groups.SetValue(createGroup.Invoke(controller, new object[] { "Music", false }), 0);
            groups.SetValue(createGroup.Invoke(controller, new object[] { "Effects", false }), 1);
            groupType.GetProperty("children", InstanceFlags).SetValue(master, groups);
            var parameterType = type.Assembly.GetType("UnityEditor.Audio.ExposedAudioParameter", true);
            var exposed = Array.CreateInstance(parameterType, 3);
            object[] volumeGroups = { master, groups.GetValue(0), groups.GetValue(1) };
            string[] names = { "MasterVolume", "MusicVolume", "EffectsVolume" };
            for (int i = 0; i < volumeGroups.Length; i++)
            {
                var parameter = Activator.CreateInstance(parameterType);
                parameterType.GetField("guid", InstanceFlags).SetValue(parameter, groupType.GetMethod("GetGUIDForVolume", InstanceFlags).Invoke(volumeGroups[i], null));
                parameterType.GetField("name", InstanceFlags).SetValue(parameter, names[i]);
                exposed.SetValue(parameter, i);
                var group = (UnityEngine.Object)volumeGroups[i];
                if (!AssetDatabase.Contains(group)) AssetDatabase.AddObjectToAsset(group, controller);
            }
            type.GetProperty("exposedParameters", InstanceFlags).SetValue(controller, exposed);
            type.GetMethod("SanitizeGroupViews", InstanceFlags).Invoke(controller, null);
            EditorUtility.SetDirty(controller);
            EditorUtility.SetDirty((UnityEngine.Object)master);
            AssetDatabase.SaveAssets();
        }

        [MenuItem("Abyss/Validate Production Content")]
        public static void ValidateContent()
        {
            var db = GameDB.Load(table => File.ReadAllText("Assets/_Game/Resources/Data/" + table + ".json"));
            var missing = new List<string>();
            Action<string> require = resource =>
            {
                if (Resources.Load<GameObject>(resource) == null) missing.Add(resource);
            };
            foreach (var id in db.HeroOrder) require(ArtLibrary.HeroPath(id));
            foreach (var job in db.Jobs.Values) if (job.Id != job.Hero) require(ArtLibrary.HeroPath(job.Id)); // job outfits (Blender/heroes/generate_anime.py)
            foreach (string id in new[] { "innkeeper", "shopkeeper", "smith", "guild_clerk", "elder", "villager_a", "villager_b", "villager_c" }) require(ArtLibrary.NpcPath(id));
            foreach (var id in db.Enemies.Keys) require(ArtLibrary.EnemyPath(ArtVariants.EnemyModel(db, id)));
            foreach (var gear in db.Equipment.Values) require(gear.Slot == "weapon" ? ArtLibrary.WeaponPath(ArtVariants.GearModel(gear)) : ArtLibrary.PropPath("Equipment", ArtVariants.GearModel(gear)));
            foreach (var id in db.Items.Keys) require(ArtLibrary.PropPath("Items", id));
            foreach (var id in db.Statuses.Keys) require(ArtLibrary.PropPath("Status", id));
            foreach (var id in new[] { "slash", "blunt", "pierce", "fire", "ice", "thunder", "dark", "holy" }) require(ArtLibrary.PropPath("Elements", id));
            foreach (var id in new[] { "attack", "skill", "ultimate", "item", "guard", "flee", "auto", "gold", "key", "map", "party", "camp" }) require(ArtLibrary.PropPath("UI", id));
            foreach (var id in new[] { "chest_common", "chest_rare", "gold_pile", "key_item", "campfire", "banner_party" }) require(ArtLibrary.PropPath("Common", id));
            var pieces = new List<string> { "floor_a", "floor_b", "floor_c", "wall_a", "wall_b", "wall_c", "door", "door_locked", "stairs_down", "stairs_up", "chest", "lore_stone", "trap", "spring", "warp", "torch", "overlay_1", "overlay_2", "boss_gate", "foe_marker", "arena" };
            for (int i = 1; i <= 6; i++) pieces.Add("decor_" + i);
            foreach (string tileset in db.Floors.Select(f => f.Tileset).Distinct()) foreach (string piece in pieces) require(ArtLibrary.EnvPath(tileset, piece));
            require(ArtLibrary.TownPath);
            if (missing.Count > 0) throw new InvalidOperationException("Missing production art:\n" + string.Join("\n", missing));
            if (AssetDatabase.LoadAssetAtPath<AudioMixer>(MixerPath) == null) throw new InvalidOperationException("Prepare audio mixer first.");
            Debug.Log("All production 3D content resource paths resolve.");
        }

        [MenuItem("Abyss/Build Windows")]
        public static void BuildWindows()
        {
            Prepare();
            ValidateContent();
            string output = "Build/Windows/AbyssLabyrinth.exe";
            Directory.CreateDirectory(Path.GetDirectoryName(output));
            var report = BuildPipeline.BuildPlayer(new BuildPlayerOptions
            {
                scenes = new[] { MainScenePath }, locationPathName = output,
                target = BuildTarget.StandaloneWindows64, options = BuildOptions.None
            });
            if (report.summary.result != BuildResult.Succeeded) throw new InvalidOperationException("Windows build failed: " + report.summary.result);
            Debug.Log($"Windows build: {report.summary.totalSize} bytes at {output}");
        }

        // ---- mobile ------------------------------------------------------------------------------------
        // Requires the Android Build Support module (IL2CPP, OpenJDK, Android SDK & NDK) or iOS Build Support in Unity Hub.
        // Batch: Unity -batchmode -quit -projectPath . -executeMethod Abyss.EditorTools.AbyssProjectSetup.BuildAndroid

        /// <summary>Player settings shared by phones and tablets: landscape only, IL2CPP/ARM64, no forced desktop resolution.</summary>
        static void ConfigureMobile()
        {
            PlayerSettings.defaultInterfaceOrientation = UIOrientation.AutoRotation;
            PlayerSettings.allowedAutorotateToLandscapeLeft = true;
            PlayerSettings.allowedAutorotateToLandscapeRight = true;
            PlayerSettings.allowedAutorotateToPortrait = false;
            PlayerSettings.allowedAutorotateToPortraitUpsideDown = false;
            PlayerSettings.SetScriptingBackend(UnityEditor.Build.NamedBuildTarget.Android, ScriptingImplementation.IL2CPP);
            PlayerSettings.SetScriptingBackend(UnityEditor.Build.NamedBuildTarget.iOS, ScriptingImplementation.IL2CPP);
            PlayerSettings.Android.targetArchitectures = AndroidArchitecture.ARM64;
            PlayerSettings.Android.minSdkVersion = AndroidSdkVersions.AndroidApiLevel25;
            PlayerSettings.Android.targetSdkVersion = AndroidSdkVersions.AndroidApiLevelAuto;
            PlayerSettings.Android.preferredInstallLocation = AndroidPreferredInstallLocation.Auto;
            PlayerSettings.Android.renderOutsideSafeArea = false;
            PlayerSettings.iOS.targetOSVersionString = "15.0";
            PlayerSettings.iOS.requiresFullScreen = true;
            PlayerSettings.iOS.hideHomeButton = true;
            EditorUserBuildSettings.androidBuildSubtarget = MobileTextureSubtarget.ASTC;
        }

        [MenuItem("Abyss/Build Android (APK)")]
        public static void BuildAndroid() => BuildAndroidPlayer(false, "Build/Android/AbyssLabyrinth.apk");

        [MenuItem("Abyss/Build Android (Google Play AAB)")]
        public static void BuildAndroidBundle() => BuildAndroidPlayer(true, "Build/Android/AbyssLabyrinth.aab");

        static void BuildAndroidPlayer(bool bundle, string output)
        {
            if (!BuildPipeline.IsBuildTargetSupported(BuildTargetGroup.Android, BuildTarget.Android))
                throw new InvalidOperationException("Android Build Support (IL2CPP, OpenJDK, SDK & NDK) is not installed for this editor.");
            if (EditorUserBuildSettings.activeBuildTarget != BuildTarget.Android)
                EditorUserBuildSettings.SwitchActiveBuildTarget(BuildTargetGroup.Android, BuildTarget.Android);
            Prepare();
            ValidateContent();
            ConfigureMobile();
            EditorUserBuildSettings.buildAppBundle = bundle;
            Directory.CreateDirectory(Path.GetDirectoryName(output));
            var report = BuildPipeline.BuildPlayer(new BuildPlayerOptions
            {
                scenes = new[] { MainScenePath }, locationPathName = output,
                target = BuildTarget.Android, options = BuildOptions.None
            });
            if (report.summary.result != BuildResult.Succeeded) throw new InvalidOperationException("Android build failed: " + report.summary.result);
            Debug.Log($"Android build: {report.summary.totalSize} bytes at {output}");
        }

        /// <summary>
        /// Browser build that phones can open from a URL. Gzip with the JavaScript decompression fallback, because
        /// static hosts such as GitHub Pages do not send Content-Encoding headers for Unity's .gz files.
        /// </summary>
        [MenuItem("Abyss/Build Web (WebGL)")]
        public static void BuildWeb() => BuildWebPlayer("Build/Web");

        static void BuildWebPlayer(string output)
        {
            if (!BuildPipeline.IsBuildTargetSupported(BuildTargetGroup.WebGL, BuildTarget.WebGL))
                throw new InvalidOperationException("Web Build Support is not installed for this editor.");
            if (EditorUserBuildSettings.activeBuildTarget != BuildTarget.WebGL)
                EditorUserBuildSettings.SwitchActiveBuildTarget(BuildTargetGroup.WebGL, BuildTarget.WebGL);
            Prepare();
            ValidateContent();
            ConfigureMobile();
            PlayerSettings.WebGL.compressionFormat = WebGLCompressionFormat.Gzip;
            PlayerSettings.WebGL.decompressionFallback = true;
            PlayerSettings.WebGL.dataCaching = true;
            PlayerSettings.WebGL.exceptionSupport = WebGLExceptionSupport.ExplicitlyThrownExceptionsOnly;
            PlayerSettings.WebGL.nameFilesAsHashes = false;
            PlayerSettings.WebGL.template = "APPLICATION:Default";
            Directory.CreateDirectory(output);
            var report = BuildPipeline.BuildPlayer(new BuildPlayerOptions
            {
                scenes = new[] { MainScenePath }, locationPathName = output,
                target = BuildTarget.WebGL, options = BuildOptions.None
            });
            if (report.summary.result != BuildResult.Succeeded) throw new InvalidOperationException("Web build failed: " + report.summary.result);
            Debug.Log($"Web build: {report.summary.totalSize} bytes at {output} (serve the folder over http/https; index.html is the entry)");
        }

        /// <summary>
        /// Entry point for GitHub Actions (game-ci/unity-builder buildMethod). The builder passes -buildTarget and
        /// -customBuildPath; the output lands where the workflow uploads it from.
        /// </summary>
        public static void BuildFromCommandLine()
        {
            string[] args = Environment.GetCommandLineArgs();
            string Arg(string name)
            {
                int i = Array.IndexOf(args, name);
                return i >= 0 && i + 1 < args.Length ? args[i + 1] : null;
            }
            string target = Arg("-buildTarget") ?? Arg("-customBuildTarget") ?? "";
            string path = Arg("-customBuildPath");
            Debug.Log($"[Abyss CI] target={target} path={path}");
            switch (target)
            {
                case "Android":
                    bool bundle = path != null && path.EndsWith(".aab", StringComparison.OrdinalIgnoreCase);
                    BuildAndroidPlayer(bundle, path ?? "build/Android/AbyssLabyrinth.apk");
                    break;
                case "WebGL":
                    // The builder passes a folder (build/WebGL/<buildName>); index.html is written inside it.
                    BuildWebPlayer(path == null ? "build/WebGL/Web" : path.TrimEnd('/', '\\'));
                    break;
                default:
                    throw new InvalidOperationException("Unsupported CI build target: " + target);
            }
            // game-ci/cli only accepts a custom build method's run when the log carries this exact line.
            Debug.Log("Build succeeded!");
        }

        [MenuItem("Abyss/Build iOS (Xcode project)")]
        public static void BuildIos()
        {
            if (!BuildPipeline.IsBuildTargetSupported(BuildTargetGroup.iOS, BuildTarget.iOS))
                throw new InvalidOperationException("iOS Build Support is not installed for this editor.");
            if (EditorUserBuildSettings.activeBuildTarget != BuildTarget.iOS)
                EditorUserBuildSettings.SwitchActiveBuildTarget(BuildTargetGroup.iOS, BuildTarget.iOS);
            Prepare();
            ValidateContent();
            ConfigureMobile();
            const string output = "Build/iOS";
            Directory.CreateDirectory(output);
            var report = BuildPipeline.BuildPlayer(new BuildPlayerOptions
            {
                scenes = new[] { MainScenePath }, locationPathName = output,
                target = BuildTarget.iOS, options = BuildOptions.None
            });
            if (report.summary.result != BuildResult.Succeeded) throw new InvalidOperationException("iOS build failed: " + report.summary.result);
            Debug.Log($"iOS Xcode project: {output} (open in Xcode on a Mac to sign and run)");
        }
    }

    public sealed class AbyssAudioImporter : AssetPostprocessor
    {
        void OnPreprocessAudio()
        {
            if (!assetPath.StartsWith("Assets/_Game/Resources/Audio/", StringComparison.Ordinal)) return;
            var importer = (AudioImporter)assetImporter;
            bool music = assetPath.Contains("/bgm/");
            importer.forceToMono = false;
            importer.loadInBackground = music;
            var settings = importer.defaultSampleSettings;
            settings.preloadAudioData = !music;
            settings.loadType = music ? AudioClipLoadType.Streaming : AudioClipLoadType.CompressedInMemory;
            settings.compressionFormat = AudioCompressionFormat.Vorbis;
            settings.quality = music ? .7f : .8f;
            settings.sampleRateSetting = AudioSampleRateSetting.PreserveSampleRate;
            importer.defaultSampleSettings = settings;
        }
    }
}
