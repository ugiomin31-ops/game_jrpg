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
        /// Model of a hunter: its own Art/Characters/&lt;id&gt;/&lt;id&gt; model. A hunter without its own model yet wears its
        /// job's outfit (Art/Characters/&lt;job&gt;) or its class's model.
        /// </summary>
        public static string HeroModelPath(string heroId, string jobId)
        {
            if (Exists(HeroPath(heroId))) return HeroPath(heroId);
            if (!string.IsNullOrEmpty(jobId) && Exists(HeroPath(jobId))) return HeroPath(jobId);
            return HeroPath(Abyss.Logic.GameDB.Instance?.ClassOf(heroId) ?? heroId);
        }

        /// <summary>
        /// Spawns a hero (model id = hero id) wearing the outfit of <paramref name="jobId"/> when it has one; an
        /// advanced / master job also tints its body rim with the branch colour (<see cref="GearDisplay.DressPromotion"/>).
        /// </summary>
        public static CharacterModel SpawnHero(string heroId, Transform parent = null, string jobId = null)
        {
            var model = SpawnCharacter(HeroModelPath(heroId, jobId), heroId, parent);
            if (model.Height > HeroDisplayHeight * 1.12f)
            {
                model.transform.localScale *= HeroDisplayHeight / model.Height;
                model.RecomputeBounds();
            }
            GearDisplay.DressPromotion(model, jobId);
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
            // Explicit D1 rule: only the listed blobs, and only while they ship no authored Idle take.
            bool rigless = IsRiglessBlob(id) && !HasIdle(clips);
            // Approved exception (2026-10-12): flyers whose Tripo rig failed, by resolved model id AND enemy resource path,
            // and only while they ship no authored Idle (a listed flyer that still has takes keeps the strict clip path).
            bool flyer = IsRiglessFlyer(id) && path == EnemyPath(id) && !HasIdle(clips);
            string classId = null;
            HashSet<string> classNames = null;
            if (!rigless && !flyer && animator != null && animator.isHuman && !HasIdle(clips))
            {
                clips = LoadClips(HumanoidAnimationsPath);
                classId = Abyss.Logic.GameDB.Instance?.ClassOf(id) ?? id;
                clips = MergeClassClips(clips, classId, out classNames);
            }
            model.Setup(id, visual, clips, rigless, flyer);
            model.SetClassClips(classId, classNames);
            return model;
        }

        /// <summary>
        /// Per-class takes (Art/HumanoidAnimationsByClass/&lt;class&gt;/, a sibling of the shared folder because LoadAll is recursive)
        /// replace the shared take of the same name; every take a class does not ship falls back to the shared one.
        /// </summary>
        public const string HumanoidClassAnimationsPath = "Art/HumanoidAnimationsByClass";

        static readonly Dictionary<string, (AnimationClip[] Clips, HashSet<string> Names)> MergedCache =
            new Dictionary<string, (AnimationClip[], HashSet<string>)>();

        static AnimationClip[] MergeClassClips(AnimationClip[] shared, string classId, out HashSet<string> classNames)
        {
            string key = classId ?? "";
            if (MergedCache.TryGetValue(key, out var cached)) { classNames = cached.Names; return cached.Clips; }
            var own = LoadClips(HumanoidClassAnimationsPath + "/" + classId);
            classNames = new HashSet<string>();
            AnimationClip[] merged = shared;
            if (own.Length > 0)
            {
                var byName = new Dictionary<string, AnimationClip>();
                foreach (var clip in shared) if (clip != null) byName[clip.name] = clip;
                foreach (var clip in own)
                {
                    if (clip == null || clip.name.StartsWith("__preview__", System.StringComparison.Ordinal)) continue;
                    byName[clip.name] = clip; classNames.Add(clip.name);
                }
                merged = new AnimationClip[byName.Count];
                byName.Values.CopyTo(merged, 0);
            }
            MergedCache[key] = (merged, classNames);
            return merged;
        }

        /// <summary>
        /// Contact / release point (fraction of the take) of per-class takes whose strike is not at the shared default
        /// (Attack 40%, Cast 60%, Skill 50%). Authored values: ArtSource/hunters/_anim_library/INSTALL.md class mapping table.
        /// </summary>
        static readonly Dictionary<string, float> ClassContact = new Dictionary<string, float>
        {
            { "warrior/Attack", .396f }, { "cleric/Attack", .14f }, { "mage/Skill", .50f },
        };

        /// <summary>Per-class takes whose tail is a held recovery pose: only this fraction of the take plays before the return fade.</summary>
        static readonly Dictionary<string, float> ClassEnd = new Dictionary<string, float> { { "warrior/Attack", .68f } };

        public static float ClassEndFraction(string classId, string clip) =>
            classId != null && ClassEnd.TryGetValue(classId + "/" + clip, out var f) ? f : 1f;

        /// <summary>Contact fraction of <paramref name="clip"/> for a class that ships its own take of that name; -1 when none is known.</summary>
        public static float ClassContactFraction(string classId, string clip) =>
            classId != null && ClassContact.TryGetValue(classId + "/" + clip, out var f) ? f : -1f;

        /// <summary>
        /// Model ids with no skeleton and no authored takes; they animate through <see cref="RiglessBlobAnimator"/>.
        /// Every other model must ship its takes (a missing one is a content error).
        /// </summary>
        static readonly HashSet<string> RiglessBlobIds = new HashSet<string>
        {
            "slime", "magma_slime", "giant_clam", "sea_urchin", "chaos_spawn",
        };

        public static bool IsRiglessBlob(string modelId) => modelId != null && RiglessBlobIds.Contains(modelId);

        /// <summary>
        /// Winged enemy model ids animated by code (<see cref="RiglessFlyerAnimator"/>) because their Tripo skin failed the rig gate.
        /// The list is explicit; a model id is never treated as a flyer merely because it lacks takes.
        /// </summary>
        static readonly HashSet<string> RiglessFlyerIds = new HashSet<string> { "bat", "killer_bee", "elite_bat" };

        public static bool IsRiglessFlyer(string modelId) => modelId != null && RiglessFlyerIds.Contains(modelId);

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
