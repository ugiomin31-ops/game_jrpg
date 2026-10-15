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
            foreach (string id in new[] { "innkeeper", "shopkeeper", "smith", "guild_clerk", "elder", "villager_a", "villager_b", "villager_c" }) require(ArtLibrary.NpcPath(id));
            foreach (var id in db.Enemies.Keys) require(ArtLibrary.EnemyPath(id));
            foreach (var gear in db.Equipment.Values) require(gear.Slot == "weapon" ? ArtLibrary.WeaponPath(gear.Id) : ArtLibrary.PropPath("Equipment", gear.Id));
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
