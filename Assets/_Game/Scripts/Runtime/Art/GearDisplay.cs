using System.Collections.Generic;
using Abyss.Logic;
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
        static readonly int RimColorId = Shader.PropertyToID("_RimColor");
        static readonly int RimStrengthId = Shader.PropertyToID("_RimStrength");
        static readonly int OutlineWidthId = Shader.PropertyToID("_OutlineWidth");
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
                block.SetFloat(OutlineWidthId, 0.02f);
                block.SetColor(OutlineColorId, rank >= 2 ? Color.Lerp(new Color(0.08f, 0.06f, 0.1f), rim, 0.35f) : new Color(0.08f, 0.06f, 0.1f));
                // Lifts the blade out of dark dungeon lighting; better weapons glow a little more.
                block.SetFloat(EmissionId, 0.18f + rank * 0.08f);
                r.SetPropertyBlock(block);
            }
            if (rank >= 2) AddSparkles(weapon, rim, rank);
            return weapon;
        }

        /// <summary>Armour rank tints the body rim; accessory rank adds a small gem of light circling the hero.</summary>
        public static void DressBody(CharacterModel model, int armorRank, int accessoryRank)
        {
            var block = new MaterialPropertyBlock();
            foreach (var r in model.GetComponentsInChildren<Renderer>(true))
            {
                if (r is ParticleSystemRenderer || r.GetComponentInParent<GearTag>() != null) continue;
                r.GetPropertyBlock(block);
                block.SetColor(RimColorId, Color.Lerp(new Color(1f, 0.95f, 0.85f), RankColor(armorRank), armorRank >= 2 ? 0.75f : 0.2f));
                block.SetFloat(RimStrengthId, 0.35f + armorRank * 0.14f);
                r.SetPropertyBlock(block);
            }
            var old = model.transform.Find("Accessory Orb");
            if (old != null) Object.Destroy(old.gameObject);
            if (accessoryRank < 1) return;
            var orb = new GameObject("Accessory Orb");
            orb.transform.SetParent(model.transform, false);
            orb.AddComponent<GearTag>();
            orb.AddComponent<GearOrbit>().Setup(model.Height, RankColor(Mathf.Max(2, accessoryRank)), accessoryRank);
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
