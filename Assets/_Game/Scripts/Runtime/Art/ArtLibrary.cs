using System.Collections.Generic;
using UnityEngine;

namespace Abyss.Runtime.Art
{
    /// <summary>
    /// Loads and instantiates Blender-exported art from Resources/Art using the paths fixed in Blender/README.md.
    /// Missing production assets are errors; incomplete content must not silently become stand-in geometry.
    /// </summary>
    public static class ArtLibrary
    {
        static readonly Dictionary<string, GameObject> PrefabCache = new Dictionary<string, GameObject>();
        static readonly Dictionary<string, AnimationClip[]> ClipCache = new Dictionary<string, AnimationClip[]>();

        public static string HeroPath(string id) => $"Art/Characters/{id}/{id}";
        public static string NpcPath(string id) => $"Art/NPCs/{id}/{id}";
        public static string EnemyPath(string id) => $"Art/Enemies/{id}/{id}";
        public static string WeaponPath(string id) => $"Art/Weapons/{id}";
        public static string PropPath(string category, string id) => $"Art/Props/{category}/{id}";
        public static string EnvPath(string tileset, string piece) => $"Art/Environment/{tileset}/{piece}";
        public const string TownPath = "Art/Town/town";
        /// <summary>
        /// Shared Unity-Humanoid takes (one clip per FBX, named by file: Idle, Run, Walk, Attack, Cast, Hit, Die,
        /// Victory, Guard, Revive, Talk). Used by humanoid characters (VRoid/VRM, store or Mixamo models) that ship no takes of their own.
        /// </summary>
        public const string HumanoidAnimationsPath = "Art/HumanoidAnimations";

        public static GameObject LoadPrefab(string path)
        {
            if (PrefabCache.TryGetValue(path, out var p)) return p;
            p = Resources.Load<GameObject>(path);
            if (p != null) PrefabCache[path] = p;
            return p;
        }

        public static bool Exists(string path) => LoadPrefab(path) != null;

        static AnimationClip[] LoadClips(string path)
        {
            if (!ClipCache.TryGetValue(path, out var c))
            {
                c = Resources.LoadAll<AnimationClip>(path);
                ClipCache[path] = c;
            }
            return c;
        }

        /// <summary>
        /// Heroes stand at the chibi height the battle arena, town and monster sizes were laid out for. The textured
        /// anime heroes are modelled at full height (~1.75 m), so they are scaled down uniformly (weapons follow).
        /// </summary>
        public const float HeroDisplayHeight = 1.3f;

        /// <summary>
        /// Model of a hero in a job: Art/Characters/&lt;job&gt;/&lt;job&gt; when that outfit exists, else the hero's own model.
        /// </summary>
        public static string HeroModelPath(string heroId, string jobId) =>
            !string.IsNullOrEmpty(jobId) && jobId != heroId && Exists(HeroPath(jobId)) ? HeroPath(jobId) : HeroPath(heroId);

        /// <summary>Spawns a hero (model id = hero id) wearing the outfit of <paramref name="jobId"/> when it has one.</summary>
        public static CharacterModel SpawnHero(string heroId, Transform parent = null, string jobId = null)
        {
            var model = SpawnCharacter(HeroModelPath(heroId, jobId), heroId, parent);
            if (model.Height > HeroDisplayHeight * 1.12f)
            {
                model.transform.localScale *= HeroDisplayHeight / model.Height;
                model.RecomputeBounds();
            }
            return model;
        }
        public static CharacterModel SpawnNpc(string npcId, Transform parent = null) => SpawnCharacter(NpcPath(npcId), npcId, parent);
        /// <summary>Instantiate an enemy by its art model id (no palette; see the <see cref="Abyss.Logic.GameDB"/> overload).</summary>
        public static CharacterModel SpawnEnemy(string modelId, Transform parent = null) => SpawnCharacter(EnemyPath(modelId), modelId, parent);

        /// <summary>
        /// Instantiate an enemy row: the model comes from its "model" field (palette variants reuse a base enemy's FBX)
        /// and its "tint" multiplies the toon colours (<see cref="Abyss.Logic.ArtVariants"/>).
        /// </summary>
        public static CharacterModel SpawnEnemy(Abyss.Logic.GameDB db, string enemyId, Transform parent = null)
        {
            string modelId = Abyss.Logic.ArtVariants.EnemyModel(db, enemyId);
            var model = SpawnCharacter(EnemyPath(modelId), modelId, parent);
            model.gameObject.name = enemyId;
            var tint = Abyss.Logic.ArtVariants.EnemyTint(db, enemyId);
            if (tint != null) model.SetPalette(ToColor(tint));
            return model;
        }

        /// <summary>RGBA array (see ArtVariants.Normalise) as a Unity colour.</summary>
        public static Color ToColor(float[] rgba) => new Color(rgba[0], rgba[1], rgba[2], rgba[3]);

        /// <summary>Instantiate an animated character. The returned root faces +Z, feet at y=0.</summary>
        public static CharacterModel SpawnCharacter(string path, string id, Transform parent = null)
        {
            var prefab = LoadPrefab(path);
            if (prefab == null) throw new System.InvalidOperationException("Missing character art: " + path);
            var root = new GameObject(id);
            if (parent != null) root.transform.SetParent(parent, false);
            var visual = Object.Instantiate(prefab, root.transform, false).transform;
            visual.name = "Model";
            var model = root.AddComponent<CharacterModel>();
            var clips = LoadClips(path);
            var animator = visual.GetComponent<Animator>();
            if (animator != null && animator.isHuman && !HasIdle(clips)) clips = LoadClips(HumanoidAnimationsPath);
            model.Setup(id, visual, clips);
            return model;
        }

        static bool HasIdle(AnimationClip[] clips)
        {
            foreach (var clip in clips) if (clip != null && clip.name == "Idle") return true;
            return false;
        }

        /// <summary>Instantiate a required static model (environment piece, prop, weapon).</summary>
        public static GameObject SpawnStatic(string path, Transform parent = null)
        {
            var prefab = LoadPrefab(path);
            if (prefab == null) throw new System.InvalidOperationException("Missing static art: " + path);
            var go = Object.Instantiate(prefab, parent, false);
            go.name = prefab.name;
            return go;
        }

    }
}
