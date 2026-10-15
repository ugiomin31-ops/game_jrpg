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
            // Per-model display scale for Tripo models authored smaller than their role (applied to the Visual, so battle
            // and dungeon code that sets the root scale from EnemyDef.ScaleMult still multiplies on top).
            if (ModelScale.TryGetValue(id, out float modelScale) && path == EnemyPath(id)) visual.localScale *= modelScale;
            var model = root.AddComponent<CharacterModel>();
            var clips = LoadClips(path);
            var animator = visual.GetComponent<Animator>();
            // Explicit D1 rule: only the listed blobs, and only while they ship no authored Idle take.
            bool rigless = IsRiglessBlob(id) && !HasIdle(clips);
            // Approved exception (2026-10-12): flyers whose Tripo rig failed, by resolved model id AND enemy resource path,
            // and only while they ship no authored Idle (a listed flyer that still has takes keeps the strict clip path).
            bool flyer = IsRiglessFlyer(id) && path == EnemyPath(id) && !HasIdle(clips);
            // Rigid static creatures (Tripo shell, no skeleton): same explicit-list rule as the flyers.
            bool crawler = IsRiglessCrawler(id) && path == EnemyPath(id) && !HasIdle(clips);
            Dictionary<string, string> owners = null;
            if (!rigless && !flyer && !crawler && animator != null && animator.isHuman && !HasIdle(clips))
            {
                clips = LoadClips(HumanoidAnimationsPath);
                string classId = Abyss.Logic.GameDB.Instance?.ClassOf(id) ?? id;
                // A hero's own layer sits above its class; an NPC's class id is its own id, so its class folder is already per-NPC.
                string heroId = classId != id ? id : null;
                clips = MergeLayers(clips, classId, heroId, out owners);
            }
            else
            {
                owners = ModelTimingLayer(id);
                // A Blender-rig hero's extra takes (Slash, Smash, Channel, ...) live beside its model in <id>_moves.fbx and bind
                // by transform path; its own takes win on a name clash.
                if (!rigless && !flyer && !crawler && path.StartsWith("Art/Characters/", System.StringComparison.Ordinal))
                    clips = MergeMoves(clips, LoadClips(path + "_moves"));
            }
            model.Setup(id, visual, clips, rigless, flyer, crawler);
            model.SetClipOwners(owners);
            return model;
        }

        /// <summary>
        /// Per-class takes (Art/HumanoidAnimationsByClass/&lt;class&gt;/, a sibling of the shared folder because LoadAll is recursive)
        /// replace the shared take of the same name; every take a class does not ship falls back to the shared one.
        /// </summary>
        public const string HumanoidClassAnimationsPath = "Art/HumanoidAnimationsByClass";
        /// <summary>
        /// Per-hero takes (Art/HumanoidAnimationsByHero/&lt;heroId&gt;/), same take-name contract, layered above the class folder
        /// so two heroes of one class can move differently. A missing or empty folder falls through to class, then shared.
        /// </summary>
        public const string HumanoidHeroAnimationsPath = "Art/HumanoidAnimationsByHero";

        static readonly Dictionary<string, (AnimationClip[] Clips, Dictionary<string, string> Owners)> MergedCache =
            new Dictionary<string, (AnimationClip[], Dictionary<string, string>)>();

        /// <summary>
        /// Shared takes overlaid by the class folder, then by the hero folder. <paramref name="owners"/> maps every overriding take
        /// to the layer id that supplied it (the class id or the hero id), which keys its contact / end / loop-blend values.
        /// </summary>
        static AnimationClip[] MergeLayers(AnimationClip[] shared, string classId, string heroId, out Dictionary<string, string> owners)
        {
            string key = (classId ?? "") + "|" + (heroId ?? "");
            if (MergedCache.TryGetValue(key, out var cached)) { owners = cached.Owners; return cached.Clips; }
            var layers = new Dictionary<string, string>();
            var byName = new Dictionary<string, AnimationClip>();
            foreach (var clip in shared) if (clip != null) byName[clip.name] = clip;
            void Overlay(string folder, string layer)
            {
                if (layer == null) return;
                foreach (var clip in LoadClips(folder + "/" + layer))
                {
                    if (clip == null || clip.name.StartsWith("__preview__", System.StringComparison.Ordinal)) continue;
                    byName[clip.name] = clip; layers[clip.name] = layer;
                }
            }
            Overlay(HumanoidClassAnimationsPath, classId);
            Overlay(HumanoidHeroAnimationsPath, heroId);
            var merged = layers.Count == 0 ? shared : new AnimationClip[byName.Count];
            if (layers.Count > 0) byName.Values.CopyTo(merged, 0);
            owners = layers;
            MergedCache[key] = (merged, layers);
            return merged;
        }

        /// <summary>
        /// Contact / release point (fraction of the take) of class / hero takes whose strike is not at the shared default
        /// (Attack 40%, Cast 60%, Skill 50%), keyed "&lt;layer id&gt;/&lt;take&gt;" (class id or hero id). Authored values:
        /// ArtSource/hunters/_anim_library/INSTALL.md class mapping table. cleric/Attack: the cane head is furthest forward in
        /// front of the body at frame 6 of 35 on the Humanoid retarget (measured on h_yuna, 2026-10-14), not at the speed peak.
        /// </summary>
        static readonly Dictionary<string, float> ClassContact = new Dictionary<string, float>
        {
            { "warrior/Attack", .396f }, { "cleric/Attack", .17f }, { "mage/Skill", .50f }, { "archer/Attack", .51f },
            // MOTIONS-20261014, measured on the hero retarget (hand-speed peak / impact frame; MOTION_PLAN_20261014.md).
            { "h_dohyun/Attack", .34f }, { "h_dohyun/Skill", .45f }, { "h_minjun/Attack", .36f }, { "h_minjun/Cast", .55f },
            { "h_yuna/Attack", .26f }, { "h_yuna/Cast", .28f }, { "h_seoa/Attack", .20f },
            // Own-take monsters (layer id = model id): impact / release frame of their 2026-10-14 Tripo takes.
            { "sprout/Attack", .45f }, { "sprout/Cast", .50f }, { "mushroom/Cast", .27f }, { "pixie/Attack", .37f }, { "pixie/Cast", .42f },
            { "forest_guardian/Attack", .25f }, { "forest_guardian/Cast", .37f }, { "forest_guardian/Skill", .34f },
            // elite_mushroom (2026-10-15 Tripo presets): box_01 left-hand punch fully extended at frame 15 of 54; cast_a_spell
            // (trimmed to 89 frames before its recovery) releases its right-hand thrust at frame 61.
            { "elite_mushroom/Attack", .26f }, { "elite_mushroom/Cast", .68f },
        };

        /// <summary>
        /// Class / hero takes whose tail is a held recovery pose: only this fraction of the take plays before the return fade.
        /// cleric/Attack: the sweep ends at frame 17 of 35; the rest walks the hand back to the hip.
        /// </summary>
        static readonly Dictionary<string, float> ClassEnd = new Dictionary<string, float>
        {
            { "warrior/Attack", .68f }, { "archer/Attack", .85f }, { "cleric/Attack", .5f },
            { "h_dohyun/Attack", .85f }, { "h_minjun/Attack", .8f }, { "h_yuna/Attack", .8f }, { "h_yuna/Cast", .6f }, { "h_seoa/Attack", .85f },
        };

        /// <summary>
        /// Timing layer of a model that ships its own takes (monsters): every take with a <see cref="ClassContact"/> or
        /// <see cref="ClassEnd"/> entry keyed "&lt;model id&gt;/&lt;take&gt;" is owned by the model id; null when it has none.
        /// </summary>
        static Dictionary<string, string> ModelTimingLayer(string modelId)
        {
            Dictionary<string, string> owners = null;
            string prefix = modelId + "/";
            foreach (var key in ClassContact.Keys) if (key.StartsWith(prefix, System.StringComparison.Ordinal)) (owners ??= new Dictionary<string, string>())[key.Substring(prefix.Length)] = modelId;
            foreach (var key in ClassEnd.Keys) if (key.StartsWith(prefix, System.StringComparison.Ordinal)) (owners ??= new Dictionary<string, string>())[key.Substring(prefix.Length)] = modelId;
            return owners;
        }

        /// <summary>Loops whose first and last poses differ: seconds of self cross-fade before the wrap (see <see cref="ClipAnimator.SetLoopBlend"/>).</summary>
        static readonly Dictionary<string, float> ClassLoopBlend = new Dictionary<string, float>
        {
            { "warrior/BattleIdle", .3f }, { "h_jiho/BattleIdle", .3f }, { "h_minjun/BattleIdle", .3f }, { "h_yuna/BattleIdle", .45f },
        };

        public static float ClassEndFraction(string layer, string clip) =>
            layer != null && ClassEnd.TryGetValue(layer + "/" + clip, out var f) ? f : 1f;

        /// <summary>Contact fraction of <paramref name="clip"/> for the layer that ships its own take of that name; -1 when none is known.</summary>
        public static float ClassContactFraction(string layer, string clip) =>
            layer != null && ClassContact.TryGetValue(layer + "/" + clip, out var f) ? f : -1f;

        public static float ClassLoopBlendSeconds(string layer, string clip) =>
            layer != null && ClassLoopBlend.TryGetValue(layer + "/" + clip, out var f) ? f : 0f;

        /// <summary>
        /// Tripo's free <c>defeat_02</c> preset (the Die take of most Tripo humanoids and of the shared hunter library) never falls:
        /// it stands still for its first 15 %, slumps from 20 % to 50 % (spine bend up to 32 deg, head lean 26 deg) and then stands
        /// back up. Any Die take this long plays only that window and holds the slump.
        /// </summary>
        public const float DefeatTakeMinLength = 6f, DefeatWindowStart = .18f, DefeatWindowHold = .5f;

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

        /// <summary>
        /// Rigid creature model ids animated by code (<see cref="RiglessCrawlerAnimator"/>): their Tripo model is a static shell
        /// (no skeleton, no takes). Palette variants that reuse the model (iron / lava / elite beetles) follow automatically.
        /// </summary>
        static readonly HashSet<string> RiglessCrawlerIds = new HashSet<string> { "rhino_beetle" };

        /// <summary>
        /// Enemy model ids whose Tripo mesh is authored smaller than the creature it plays. forest_guardian (zone-2 boss):
        /// the 1.63 m Tripo model reads ~2.4 m in battle (×1.5 boss readability); ×1.4 makes it ~3.4 m, as dominant in
        /// frame as scrap_colossus (2.2 m × 1.5) against the old 4.66 m tree giant.
        /// </summary>
        static readonly Dictionary<string, float> ModelScale = new Dictionary<string, float> { { "forest_guardian", 1.4f } };

        public static bool IsRiglessCrawler(string modelId) => modelId != null && RiglessCrawlerIds.Contains(modelId);

        static AnimationClip[] MergeMoves(AnimationClip[] own, AnimationClip[] moves)
        {
            if (moves == null || moves.Length == 0) return own;
            var names = new HashSet<string>();
            var merged = new List<AnimationClip>(own);
            foreach (var clip in own) if (clip != null) names.Add(clip.name);
            foreach (var clip in moves)
                if (clip != null && !clip.name.StartsWith("__preview__", System.StringComparison.Ordinal) && names.Add(clip.name)) merged.Add(clip);
            return merged.ToArray();
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
