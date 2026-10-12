using System.Collections.Generic;
using Abyss.Logic;
using Abyss.Logic.Game;
using UnityEngine;

namespace Abyss.Runtime.Art
{
    /// <summary>
    /// Makes equipped gear read at phone size: weapons are held larger with a bold outline and a rank-coloured rim,
    /// better weapons trail sparkles, and armour / accessory rank shows as a body rim and an orbiting gem, so a swap
    /// is visible on the model in town and in battle.
    /// </summary>
    public static class GearDisplay
    {
        /// <summary>Held-size boost by weapon family: one-handers grow most, staves already reach shoulder height.</summary>
        public static float WeaponScale(string weaponId)
        {
            switch (string.IsNullOrEmpty(weaponId) ? "" : Family(weaponId))
            {
                case "staff": return 1.1f;
                case "bow": return 1.2f;
                default: return 1.35f;
            }
        }
        /// <summary>Held-weapon outline widths (MaterialPropertyBlock): Tripo hull materials / everything else.</summary>
        public const float TripoWeaponOutlineWidth = 0.003f, WeaponOutlineWidth = 0.008f;
        static readonly int RimColorId =Shader.PropertyToID("_RimColor");
        static readonly int RimStrengthId = Shader.PropertyToID("_RimStrength");
        static readonly int OutlineWidthId = Shader.PropertyToID("_OutlineWidth");
        static readonly int OutlineZOffsetId = Shader.PropertyToID("_OutlineZOffset");
        static readonly int OutlineColorId = Shader.PropertyToID("_OutlineColor");
        static readonly int EmissionId = Shader.PropertyToID("_EmissionStrength");
        static Material _sparkMaterial, _glowMaterial;

        /// <summary>0 (starter) .. 4 (legendary): position of the piece among gear of the same slot and family by power.</summary>
        public static int Rank(GameDB db, string id)
        {
            if (db == null || string.IsNullOrEmpty(id) || !db.Equipment.TryGetValue(id, out var piece)) return 0;
            string family = piece.Slot == "weapon" ? Family(id) : piece.Slot;
            int power = Power(piece), below = 0, total = 0;
            foreach (var other in db.Equipment.Values)
            {
                if (other.Slot != piece.Slot || (piece.Slot == "weapon" && Family(other.Id) != family)) continue;
                total++;
                if (Power(other) < power) below++;
            }
            if (total <= 1) return 0;
            return Mathf.Clamp(Mathf.RoundToInt(below * 4f / (total - 1)), 0, 4);
        }

        static string Family(string id) { int cut = id.IndexOf('_'); return cut < 0 ? id : id.Substring(0, cut); }
        static int Power(EquipmentDef e) => e.Atk + e.Mag + e.Def + e.Res + e.Spd + e.Hp / 5 + e.Mp / 3 + e.Price / 200;

        /// <summary>Rank colour: plain steel, white, sky blue, violet, gold.</summary>
        public static Color RankColor(int rank)
        {
            switch (rank)
            {
                case 1: return new Color(0.95f, 0.95f, 1f);
                case 2: return new Color(0.4f, 0.78f, 1f);
                case 3: return new Color(0.78f, 0.48f, 1f);
                case 4: return new Color(1f, 0.8f, 0.3f);
                default: return new Color(1f, 0.95f, 0.85f);
            }
        }

        /// <summary>Weapon prefab of an equipment row: its "model" field (palette variants reuse another FBX), else its id.</summary>
        public static GameObject LoadWeapon(GameDB db, string weaponId)
        {
            if (string.IsNullOrEmpty(weaponId)) return null;
            string path = ArtLibrary.WeaponPath(ArtVariants.GearModel(db, weaponId));
            var prefab = ArtLibrary.LoadPrefab(path);
            if (prefab == null) throw new System.InvalidOperationException("Missing equipped weapon art: " + path);
            return prefab;
        }

        /// <summary>Attaches an equipment row's weapon (or clears the socket): model + palette tint from the data, rank dressing.</summary>
        public static GameObject AttachWeapon(GameDB db, CharacterModel model, string socket, string weaponId)
        {
            var weapon = AttachWeapon(model, socket, LoadWeapon(db, weaponId), Rank(db, weaponId), weaponId);
            var tint = ArtVariants.GearTint(db, weaponId);
            if (weapon != null && tint != null) model.SetAttachmentTint(weapon, ArtLibrary.ToColor(tint));
            return weapon;
        }

        /// <summary>Attaches the weapon (or clears the socket) and dresses it for its rank.</summary>
        public static GameObject AttachWeapon(CharacterModel model, string socket, GameObject prefab, int rank, string weaponId = null)
        {
            var weapon = model.Attach(socket, prefab);
            if (weapon == null) return null;
            weapon.AddComponent<GearTag>();
            weapon.transform.localScale *= WeaponScale(weaponId ?? prefab.name);
            Color rim = RankColor(rank);
            var block = new MaterialPropertyBlock();
            foreach (var r in weapon.GetComponentsInChildren<Renderer>(true))
            {
                if (r is ParticleSystemRenderer) continue;
                r.GetPropertyBlock(block);
                block.SetColor(RimColorId, rim);
                block.SetFloat(RimStrengthId, 0.9f + rank * 0.22f);
                // Tripo weapon materials carry their own thin hull (6 cm Z offset, see TexturedMaterials), so they only get a
                // slightly stronger line (0.003, about 1.6 px at 1080p); other weapons keep a bolder one (0.008). The old
                // 0.02 rank outline made both look like thick black halos.
                var shared = r.sharedMaterial;
                bool tripoHull = shared != null && shared.HasProperty(OutlineZOffsetId) && shared.GetFloat(OutlineZOffsetId) >= 0.05f;
                block.SetFloat(OutlineWidthId, tripoHull ? TripoWeaponOutlineWidth : WeaponOutlineWidth);
                block.SetColor(OutlineColorId, rank >= 2 ? Color.Lerp(new Color(0.08f, 0.06f, 0.1f), rim, 0.35f) : new Color(0.08f, 0.06f, 0.1f));
                // Lifts the blade out of dark dungeon lighting; better weapons glow a little more.
                block.SetFloat(EmissionId, 0.18f + rank * 0.08f);
                r.SetPropertyBlock(block);
            }
            if (rank >= 2) AddSparkles(weapon, rim, rank);
            return weapon;
        }

        /// <summary>
        /// Armour rank tints the body rim; accessory rank adds a small gem of light circling the hero. The hunter's
        /// current job is re-read from the running game (<see cref="GameDB.Instance"/> + GameApp state) so a persistent
        /// model picks up a promotion on its next equipment refresh; without state the job stored at spawn is kept.
        /// </summary>
        public static void DressBody(CharacterModel model, int armorRank, int accessoryRank)
        {
            if (model == null) return;
            model.SetBodyArmorRank(armorRank);
            ResolvePromotion(model, CurrentJob(model));
            ApplyBodyRim(model);
            // Detach before the deferred Destroy so a second dress in the same frame cannot find (and keep) a stale orb.
            for (int i = model.transform.childCount - 1; i >= 0; i--)
            {
                var old = model.transform.GetChild(i);
                if (old.name != AccessoryOrbName) continue;
                old.gameObject.SetActive(false);
                old.SetParent(null, false);
                Object.Destroy(old.gameObject);
            }
            if (accessoryRank < 1) return;
            var orb = new GameObject(AccessoryOrbName);
            orb.transform.SetParent(model.transform, false);
            orb.AddComponent<GearTag>();
            orb.AddComponent<GearOrbit>().Setup(model.Height, RankColor(Mathf.Max(2, accessoryRank)), accessoryRank);
        }

        const string AccessoryOrbName = "Accessory Orb";
        static readonly Color BaseRim = new Color(1f, 0.95f, 0.85f);
        static MaterialPropertyBlock _bodyBlock;

        /// <summary>
        /// Promotion dressing for a hunter model (called by <see cref="ArtLibrary.SpawnHero"/>): stores the job's branch
        /// colour and tier intensity on the model and re-applies the body rim. Idempotent: no objects, no materials.
        /// </summary>
        public static void DressPromotion(CharacterModel model, string jobId)
        {
            if (model == null) return;
            ResolvePromotion(model, jobId);
            // A base-job model nobody has dressed yet already shows the material's default rim: leave its renderers alone.
            if (model.PromotionIntensity > 0f || model.BodyRimDressed) ApplyBodyRim(model);
        }

        /// <summary>Rim intensity a job tier adds: base (Tier 1) 0, advanced (Tier 2) .18, master (Tier 3) .32.</summary>
        public static float PromotionIntensity(int tier) => tier >= 3 ? 0.32f : tier == 2 ? 0.18f : 0f;

        /// <summary>Fixed branch colour of a promoted job (advanced and master job of a branch share it).</summary>
        public static Color PromotionColor(GameDB db, string jobId)
        {
            for (int depth = 0; depth < 4 && !string.IsNullOrEmpty(jobId); depth++)
            {
                switch (jobId)
                {
                    case "knight": case "paladin": return new Color(0.36f, 0.6f, 1f);           // blue
                    case "berserker": case "warlord": return new Color(0.92f, 0.16f, 0.26f);    // crimson
                    case "elementalist": case "archmage": return new Color(0.3f, 0.92f, 1f);    // cyan
                    case "warlock": case "abyssal": return new Color(0.68f, 0.38f, 1f);         // violet
                    case "sniper": case "divine_archer": return new Color(1f, 0.8f, 0.28f);     // gold
                    case "ranger": case "shadow_stalker": return new Color(0.2f, 0.82f, 0.7f);  // teal
                    case "priest": case "saint": return new Color(1f, 0.93f, 0.68f);            // ivory-gold
                    case "exorcist": case "inquisitor": return new Color(1f, 0.5f, 0.42f);      // coral
                }
                // Unlisted promoted jobs inherit their parent branch's colour.
                if (db == null || !db.Jobs.TryGetValue(jobId, out var job)) break;
                jobId = job.Parent;
            }
            return BaseRim;
        }

        /// <summary>The hunter's job in the running game, else the job the model was spawned / last dressed with.</summary>
        static string CurrentJob(CharacterModel model)
        {
            var db = GameDB.Instance;
            var app = Abyss.Runtime.GameApp.Instance;
            var hero = db != null && app != null && app.State != null ? app.State.Hero(model.ModelId) : null;
            if (hero == null) return model.PromotionJob;
            return PartyStats.JobOf(db, hero)?.Id ?? db.ClassOf(hero.Id);
        }

        static void ResolvePromotion(CharacterModel model, string jobId)
        {
            var db = GameDB.Instance;
            int tier = db != null && !string.IsNullOrEmpty(jobId) && db.Jobs.TryGetValue(jobId, out var job) ? job.Tier : 1;
            float intensity = PromotionIntensity(tier);
            model.SetPromotion(jobId, intensity > 0f ? PromotionColor(db, jobId) : BaseRim, intensity);
        }

        /// <summary>
        /// Body rim = armour-rank rim with the promotion branch colour blended in (static, subtle). Only the rim
        /// properties are written; the block is read first so hit flash, dissolve and palette colour survive, and
        /// gear (weapons, orb) is skipped so weapon rims keep their rank colour.
        /// </summary>
        static void ApplyBodyRim(CharacterModel model)
        {
            int armorRank = model.BodyArmorRank;
            Color rim = Color.Lerp(BaseRim, RankColor(armorRank), armorRank >= 2 ? 0.75f : 0.2f);
            float strength = 0.35f + armorRank * 0.14f;
            float promotion = model.PromotionIntensity;
            if (promotion > 0f)
            {
                rim = Color.Lerp(rim, model.PromotionColor, Mathf.Clamp01(promotion * 2f));
                strength += promotion;
            }
            var block = _bodyBlock ?? (_bodyBlock = new MaterialPropertyBlock());
            foreach (var r in model.GetComponentsInChildren<Renderer>(true))
            {
                if (r is ParticleSystemRenderer || r.GetComponentInParent<GearTag>(true) != null) continue;
                r.GetPropertyBlock(block);
                block.SetColor(RimColorId, rim);
                block.SetFloat(RimStrengthId, strength);
                r.SetPropertyBlock(block);
            }
            model.MarkBodyRimDressed();
        }

        static void AddSparkles(GameObject weapon, Color color, int rank)
        {
            // Mesh bounds in the weapon's own space, so the emitter box follows the blade however it is held.
            var toWeapon = weapon.transform.worldToLocalMatrix;
            var bounds = new Bounds();
            bool any = false;
            foreach (var filter in weapon.GetComponentsInChildren<MeshFilter>(true))
            {
                if (filter.sharedMesh == null) continue;
                var m = toWeapon * filter.transform.localToWorldMatrix;
                var b = filter.sharedMesh.bounds;
                for (int i = 0; i < 8; i++)
                {
                    var corner = m.MultiplyPoint3x4(b.center + Vector3.Scale(b.extents, new Vector3((i & 1) == 0 ? -1 : 1, (i & 2) == 0 ? -1 : 1, (i & 4) == 0 ? -1 : 1)));
                    if (!any) { bounds = new Bounds(corner, Vector3.zero); any = true; } else bounds.Encapsulate(corner);
                }
            }
            if (!any) return;
            var go = new GameObject("Rank Sparkles");
            go.AddComponent<GearTag>();
            go.transform.SetParent(weapon.transform, false);
            go.transform.localPosition = bounds.center;
            var ps = go.AddComponent<ParticleSystem>();
            ps.Stop(true, ParticleSystemStopBehavior.StopEmittingAndClear);
            var main = ps.main;
            main.loop = true;
            main.playOnAwake = true;
            main.duration = 1f;
            main.startLifetime = new ParticleSystem.MinMaxCurve(0.45f, 0.8f);
            main.startSpeed = new ParticleSystem.MinMaxCurve(0.02f, 0.12f);
            main.startSize = new ParticleSystem.MinMaxCurve(0.05f + rank * 0.012f, 0.11f + rank * 0.02f);
            main.startColor = new ParticleSystem.MinMaxGradient(color, Color.Lerp(color, Color.white, 0.6f));
            main.startRotation = new ParticleSystem.MinMaxCurve(0f, Mathf.PI);
            main.gravityModifier = -0.04f;
            // World space: a swing leaves a short trail of sparkles behind the blade.
            main.simulationSpace = ParticleSystemSimulationSpace.World;
            main.maxParticles = 60;
            var emission = ps.emission;
            emission.rateOverTime = 6f + rank * 5f;
            // Local scaling ignores the rig's scale chain, so sizes are world metres and the box is the blade's.
            main.scalingMode = ParticleSystemScalingMode.Local;
            var shape = ps.shape;
            shape.shapeType = ParticleSystemShapeType.Box;
            shape.scale = bounds.size * weapon.transform.lossyScale.x * 0.9f;
            var fade = ps.colorOverLifetime;
            fade.enabled = true;
            var gradient = new Gradient();
            gradient.SetKeys(new[] { new GradientColorKey(Color.white, 0f), new GradientColorKey(Color.white, 1f) },
                new[] { new GradientAlphaKey(0f, 0f), new GradientAlphaKey(1f, 0.2f), new GradientAlphaKey(0f, 1f) });
            fade.color = gradient;
            var size = ps.sizeOverLifetime;
            size.enabled = true;
            size.size = new ParticleSystem.MinMaxCurve(1f, AnimationCurve.EaseInOut(0f, 1f, 1f, 0.2f));
            var renderer = go.GetComponent<ParticleSystemRenderer>();
            renderer.sharedMaterial = SparkMaterial();
            renderer.shadowCastingMode = UnityEngine.Rendering.ShadowCastingMode.Off;
            renderer.receiveShadows = false;
            ps.Play();
        }

        internal static Material SparkMaterial() => _sparkMaterial != null ? _sparkMaterial : (_sparkMaterial = VfxMaterial("star4", "Gear sparkle"));
        internal static Material GlowMaterial() => _glowMaterial != null ? _glowMaterial : (_glowMaterial = VfxMaterial("glow", "Gear glow"));

        static Material VfxMaterial(string texture, string name)
        {
            var shader = Shader.Find("Abyss/VfxUnlit");
            var tex = Resources.Load<Texture2D>("Vfx/Textures/" + texture);
            if (shader == null || tex == null) throw new System.InvalidOperationException("Missing gear VFX shader or texture: " + texture);
            var material = new Material(shader) { name = name, mainTexture = tex };
            material.SetFloat("_DstBlend", (float)UnityEngine.Rendering.BlendMode.One);
            material.SetFloat("_Cel", 0f);
            return material;
        }
    }

    /// <summary>Marks runtime gear dressing so body-rim passes skip it.</summary>
    public sealed class GearTag : MonoBehaviour { }

    /// <summary>A small glowing gem circling the hero at chest height (accessory rank).</summary>
    public sealed class GearOrbit : MonoBehaviour
    {
        Transform _gem;
        float _radius, _height, _phase;

        public void Setup(float modelHeight, Color color, int rank)
        {
            _radius = 0.42f;
            _height = modelHeight * 0.62f;
            _phase = Random.value * 6.28f;
            var gem = new GameObject("Gem");
            gem.transform.SetParent(transform, false);
            _gem = gem.transform;
            var ps = gem.AddComponent<ParticleSystem>();
            ps.Stop(true, ParticleSystemStopBehavior.StopEmittingAndClear);
            var main = ps.main;
            main.loop = true;
            main.startLifetime = 0.5f;
            main.startSpeed = 0f;
            main.startSize = 0.1f + rank * 0.025f;
            main.startColor = color;
            main.simulationSpace = ParticleSystemSimulationSpace.World;
            main.scalingMode = ParticleSystemScalingMode.Local;
            main.maxParticles = 40;
            var emission = ps.emission;
            emission.rateOverTime = 26f;
            var shape = ps.shape;
            shape.enabled = false;
            var fade = ps.colorOverLifetime;
            fade.enabled = true;
            var gradient = new Gradient();
            gradient.SetKeys(new[] { new GradientColorKey(Color.white, 0f), new GradientColorKey(Color.white, 1f) },
                new[] { new GradientAlphaKey(0.9f, 0f), new GradientAlphaKey(0f, 1f) });
            fade.color = gradient;
            var size = ps.sizeOverLifetime;
            size.enabled = true;
            size.size = new ParticleSystem.MinMaxCurve(1f, AnimationCurve.Linear(0f, 1f, 1f, 0.3f));
            var renderer = gem.GetComponent<ParticleSystemRenderer>();
            renderer.sharedMaterial = GearDisplay.GlowMaterial();
            renderer.shadowCastingMode = UnityEngine.Rendering.ShadowCastingMode.Off;
            renderer.receiveShadows = false;
            Place();
            ps.Play();
        }

        void Place()
        {
            if (_gem == null) return;
            float a = _phase + Time.time * 2.2f;
            _gem.position = transform.position + new Vector3(Mathf.Cos(a) * _radius, _height + Mathf.Sin(a * 1.7f) * 0.08f, Mathf.Sin(a) * _radius);
        }

        void LateUpdate() => Place();
    }
}
