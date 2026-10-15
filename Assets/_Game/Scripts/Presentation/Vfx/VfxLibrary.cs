using System;
using System.Collections.Generic;
using UnityEngine;
using UnityEngine.Rendering;

namespace Abyss.Presentation.Vfx
{
    /// <summary>Generation-safe reference to a pooled effect. A stale handle cannot stop a reused effect.</summary>
    public readonly struct VfxHandle
    {
        readonly VfxLibrary _library;
        readonly int _slot, _generation;
        internal VfxHandle(VfxLibrary library, int slot, int generation) { _library = library; _slot = slot; _generation = generation; }
        internal int Slot => _slot;
        public bool IsPlaying => _library != null && _library.IsPlaying(_slot, _generation);
        public void Stop() { if (_library != null) _library.Stop(_slot, _generation); }
    }

    /// <summary>
    /// Resource-authored particle/mesh/trail library. Play uses world coordinates; follow keeps an effect
    /// on an actor. Travel moves a pooled projectile along a shallow arc. Looping auras/statuses/environment
    /// effects persist until their handle is stopped, or a positive duration override expires.
    /// No per-frame allocations or material instances. Recipes: Resources/Vfx/effects.json.
    /// </summary>
    [DisallowMultipleComponent]
    public sealed class VfxLibrary : MonoBehaviour
    {
        [Serializable] sealed class Catalog { public Recipe[] effects; }
        [Serializable] sealed class Recipe
        {
            public string key, description;
            public float duration;
            public bool loop;
            public LayerRecipe[] layers;
        }
        [Serializable] sealed class LayerRecipe
        {
            public string kind, texture, color = "FFFFFF";
            public float life = .6f, size = 1, endSize, height, speed, gravity, rate = 12, radius = .2f;
            public float delay, y, spin, rotation;
            public int count = 20, tiles = 1;
            public bool alpha, horizontal;
            /// <summary>Particles keep the texture upright (no random spin): falling arrows, rain streaks. Aligned mesh layers: yaw only (a standing object).</summary>
            public bool upright;
            /// <summary>Billboard quads turn their +U axis along a projectile's screen-space travel direction, or along the blow (caster toward target) for a non-travelling impact that was given a facing.</summary>
            public bool align;
            /// <summary>Resources/Vfx/Meshes/&lt;id&gt;: one baked mesh (axes, scale, pivot), see skills_vfx.md. Kinds mesh, orbit, burst, emitter.</summary>
            public string mesh;
            /// <summary>Mesh layers: texture U offset travelled over the layer life (needs a Repeat-wrapped texture).</summary>
            public float scroll;
            /// <summary>
            /// Big layer (ground seals, pillars, domes, wide flashes; marked by Tools/vfx/gen_effects.py): always dimmed,
            /// semi-transparent and coloured by its element, so it never whites out the units it plays over.
            /// </summary>
            public bool big;
            /// <summary>
            /// Authored blend policy (Tools/vfx/gen_effects.py): "add" for brief sparks and cores, "alpha" for broad
            /// sustained ground / pillar / area contributors that must stay translucent and keep their element colour.
            /// Empty falls back to <see cref="alpha"/> (legacy recipes / hand-authored extras).
            /// </summary>
            public string blend;
            /// <summary>Keeps its own colours: the effect's tint (element / presentation colour) is not applied. Real objects
            /// carried by an effect (a first-aid case, a riot shield) use it so they are not dyed green or red.</summary>
            public bool untinted;
            /// <summary>Metres (effect scale) the layer stands ahead of the anchor along the effect's facing (the blow, or the
            /// caster's forward for a self-cast); 0 or no facing: on the anchor. A riot shield set down in front of its bearer.</summary>
            public float ahead;
            [NonSerialized] public Color tint;
        }
        sealed class Layer
        {
            public LayerRecipe Recipe;
            public Transform Transform;
            public ParticleSystem Particles;
            public Renderer Renderer;
            public TrailRenderer Trail;
            public MaterialPropertyBlock Properties;
            public bool Started;
            public Transform[] Orbit;
            public Renderer[] OrbitRenderers;
            /// <summary>Set when the layer draws a mesh asset (kind mesh, or orbit with a mesh).</summary>
            public MeshAsset Mesh;
        }
        /// <summary>An imported effect mesh: a shared asset (cached, never destroyed) plus how its native axes lie.</summary>
        sealed class MeshAsset
        {
            public Mesh Mesh;
            /// <summary>The thinnest bounds axis is Y: the mesh already lies in XZ, so `horizontal` must not tilt it again.</summary>
            public bool FlatXZ;
            /// <summary>Rigid local basis only: preserves restored Tripo vertices, UVs and scale; composed after the presentation facing.</summary>
            public Quaternion Basis;
        }
        sealed class Effect
        {
            public Recipe Recipe;
            public GameObject Root;
            public Layer[] Layers;
            public int Generation;
            public bool Active, Travel, Ending;
            public Vector3 From, To, Offset;
            public Transform Follow;
            public bool HadFollow;
            public float Age, Duration, TravelTime, Drain, Angle;
            /// <summary>World-space unit tangent of the travel arc (guarded), valid once HasTangent is set.</summary>
            public Vector3 Tangent;
            public bool HasTangent;
            /// <summary>World direction of the blow (attacker toward target) for non-travelling impacts; `align` mesh layers point +Z along it.</summary>
            public Vector3 Facing;
            public bool HasFacing;
            /// <summary>World floor height for ground layers (y &lt;= GroundLayerY), NaN when unset.</summary>
            public float Ground;
            public Color Tint;
        }

        public static VfxLibrary Instance { get; private set; }
        public Camera Camera { get; set; }
        /// <summary>Playback rate for effects and particles. Trails use an inverse lifetime; zero stops our clock,
        /// but native trail points still age unless Unity's global clock is also paused.</summary>
        public float TimeScale
        {
            get => _timeScale;
            set
            {
                if (float.IsNaN(value) || float.IsInfinity(value) || value < 0f) value = 0f;
                if (value == _timeScale) return;
                _timeScale = value;
                if (value > 0f) _trailTimeScale = value;
                foreach (var effect in _effects)
                    foreach (var layer in effect.Layers)
                    {
                        if (layer.Particles != null) { var main = layer.Particles.main; main.simulationSpeed = value; }
                        if (layer.Trail != null) layer.Trail.time = TrailLifetime(layer.Recipe.life);
                    }
            }
        }
        float _timeScale = 1f;
        float _trailTimeScale = 1f;
        // Changing time does not retime existing native point timestamps: transitions can shorten or lengthen
        // the visible history. Keep that history (no Clear on speed changes). Zero retains the last positive rate.
        // Bound extreme finite rates to a finite 0.1 ms..60 s lifetime instead of overflowing native trail storage.
        float TrailLifetime(float life) => Mathf.Clamp(life / _trailTimeScale, .0001f, 60f);
        /// <summary>Layers authored at or below this offset sit on the floor rather than hang from the anchor.</summary>
        const float GroundLayerY = -.7f;
        readonly Dictionary<string, Recipe> _recipes = new Dictionary<string, Recipe>(StringComparer.Ordinal);
        readonly Dictionary<string, Stack<int>> _free = new Dictionary<string, Stack<int>>(StringComparer.Ordinal);
        readonly Dictionary<string, Material> _materials = new Dictionary<string, Material>(StringComparer.Ordinal);
        readonly Dictionary<string, MeshAsset> _meshes = new Dictionary<string, MeshAsset>(StringComparer.Ordinal);
        readonly List<Effect> _effects = new List<Effect>(128);
        Mesh _quad, _ring, _arc, _sphere;
        Shader _shader;
        static readonly int TintId = Shader.PropertyToID("_Tint");
        static readonly int TexStId = Shader.PropertyToID("_MainTex_ST");
        static readonly int GlowId = Shader.PropertyToID("_Glow");
        // Brightness control by screen coverage: a layer covering more than CoverageStart of the view starts losing its white
        // core, gain and opacity, fully at CoverageFull; `big` layers never go below BigFloor. Caps keep the target readable.
        const float CoverageStart = .04f, CoverageFull = .3f, BigFloor = .6f, MinGain = .6f, MinOpacity = .35f, BigShellOpacity = .5f;

        public static VfxLibrary Create(Transform parent = null)
        {
            if (Instance != null) return Instance;
            var go = new GameObject("Abyss VFX");
            if (parent != null) go.transform.SetParent(parent, false);
            return go.AddComponent<VfxLibrary>();
        }

        void Awake()
        {
            if (Instance != null && Instance != this) { Destroy(gameObject); return; }
            Instance = this;
            _shader = Shader.Find("Abyss/VfxUnlit");
            if (_shader == null) throw new InvalidOperationException("Abyss/VfxUnlit shader is missing.");
            var json = Resources.Load<TextAsset>("Vfx/effects");
            if (json == null) throw new InvalidOperationException("Resources/Vfx/effects.json is missing. Run Tools/vfx/gen_effects.py.");
            var catalog = JsonUtility.FromJson<Catalog>(json.text);
            foreach (var recipe in catalog.effects)
            {
                foreach (var layer in recipe.layers)
                    if (!ColorUtility.TryParseHtmlString("#" + layer.color, out layer.tint)) layer.tint = Color.white;
                _recipes.Add(recipe.key, recipe);
                _free.Add(recipe.key, new Stack<int>());
            }
            _quad = MakeQuad();
            _ring = MakeRibbon(64, 360, .06f, "Vfx ring");
            _arc = MakeRibbon(40, 135, .18f, "Vfx slash arc");
            _sphere = MakeSphere();
        }

        public bool Supports(string key) => key != null && _recipes.ContainsKey(key);
        public float Duration(string key) => key != null && _recipes.TryGetValue(key, out var recipe) ? recipe.duration : 0;

        /// <summary>Prebuild pooled instances outside action timing. Subsequent playback reuses them.</summary>
        public void Prewarm(string key, int count = 2)
        {
            if (!_recipes.TryGetValue(key, out var recipe)) throw new ArgumentException("Unknown VFX key: " + key, nameof(key));
            while (_free[key].Count < count)
            {
                int slot = Build(recipe);
                _free[key].Push(slot);
            }
        }

        /// <summary>
        /// <paramref name="groundY"/> (world height of the floor under the anchor) pins ground layers to the floor
        /// instead of offsetting them from <paramref name="position"/> by a scaled amount; NaN keeps the authored offset.
        /// </summary>
        /// <param name="facing">Direction of the blow (attacker toward target); `align` mesh layers of a non-travelling effect point their +Z along it.</param>
        public VfxHandle Play(string key, Vector3 position, Color? tint = null, float scale = 1f, float duration = 0f, Transform follow = null,
            float groundY = float.NaN, Vector3? facing = null)
        {
            if (string.IsNullOrEmpty(key)) return default;
            if (!_recipes.TryGetValue(key, out var recipe)) throw new ArgumentException("Unknown VFX key: " + key, nameof(key));
            var free = _free[key];
            int slot = free.Count > 0 ? free.Pop() : Build(recipe);
            var effect = _effects[slot];
            effect.Generation++;
            effect.Active = true; effect.Ending = false; effect.Travel = false;
            effect.Age = 0; effect.Drain = 0; effect.Angle = 0; effect.Ground = groundY;
            effect.Tangent = Vector3.forward; effect.HasTangent = false;
            effect.HasFacing = facing.HasValue && facing.Value.sqrMagnitude > 1e-4f;
            effect.Facing = effect.HasFacing ? facing.Value.normalized : Vector3.forward;
            effect.Follow = follow; effect.HadFollow = follow != null;
            effect.Offset = follow != null ? position - follow.position : Vector3.zero;
            effect.Duration = duration > 0 ? duration : recipe.loop ? float.PositiveInfinity : recipe.duration;
            effect.Tint = tint ?? Color.white;
            effect.Root.transform.position = position;
            effect.Root.transform.rotation = Quaternion.identity;
            effect.Root.transform.localScale = Vector3.one * Mathf.Max(.01f, scale);
            foreach (var layer in effect.Layers)
            {
                layer.Started = false;
                layer.Transform.gameObject.SetActive(false);
                ResetProperties(layer);
                if (layer.Particles != null) layer.Particles.Stop(true, ParticleSystemStopBehavior.StopEmittingAndClear);
                if (layer.Trail != null)
                {
                    layer.Trail.emitting = false; layer.Trail.Clear();
                    layer.Trail.time = TrailLifetime(layer.Recipe.life);
                }
            }
            effect.Root.SetActive(true);
            Tick(effect, 0);
            return new VfxHandle(this, slot, effect.Generation);
        }

        public VfxHandle Travel(string key, Vector3 from, Vector3 to, float duration = .35f, Color? tint = null, float scale = 1f)
        {
            var handle = Play(key, from, tint, scale, Mathf.Max(.01f, duration));
            if (!handle.IsPlaying) return handle;
            var effect = _effects[handle.Slot];
            effect.Travel = true;
            effect.From = from;
            effect.To = to;
            effect.TravelTime = Mathf.Max(.01f, duration);
            Aim(effect, Camera != null ? Camera : UnityEngine.Camera.main, 0);
            Tick(effect, 0);
            return handle;
        }

        internal bool IsPlaying(int slot, int generation) => slot >= 0 && slot < _effects.Count && _effects[slot].Active && _effects[slot].Generation == generation;
        internal void Stop(int slot, int generation)
        {
            if (!IsPlaying(slot, generation)) return;
            End(_effects[slot]);
        }

        public void StopAll()
        {
            for (int i = 0; i < _effects.Count; i++) if (_effects[i].Active) Recycle(i);
        }

        int Build(Recipe recipe)
        {
            var effect = new Effect { Recipe = recipe, Root = new GameObject("VFX " + recipe.key), Layers = new Layer[recipe.layers.Length] };
            effect.Root.SetActive(false);
            effect.Root.transform.SetParent(transform, false);
            for (int i = 0; i < recipe.layers.Length; i++) effect.Layers[i] = BuildLayer(effect.Root.transform, recipe.layers[i]);
            int slot = _effects.Count;
            _effects.Add(effect);
            return slot;
        }

        Layer BuildLayer(Transform parent, LayerRecipe recipe)
        {
            var go = new GameObject(recipe.kind + " " + recipe.texture);
            go.transform.SetParent(parent, false);
            var layer = new Layer { Recipe = recipe, Transform = go.transform, Properties = new MaterialPropertyBlock() };
            var material = MaterialFor(recipe.texture, BlendAlpha(recipe));
            if (recipe.kind == "burst" || recipe.kind == "emitter")
            {
                var ps = go.AddComponent<ParticleSystem>();
                ps.Stop(true, ParticleSystemStopBehavior.StopEmittingAndClear);
                var main = ps.main;
                main.playOnAwake = false;
                main.loop = recipe.kind == "emitter";
                main.duration = Mathf.Max(.1f, recipe.life);
                main.startLifetime = new ParticleSystem.MinMaxCurve(recipe.life * .7f, recipe.life);
                main.startSize = new ParticleSystem.MinMaxCurve(recipe.size * .6f, recipe.size);
                main.startSpeed = recipe.kind == "burst" ? new ParticleSystem.MinMaxCurve(recipe.speed * .4f, recipe.speed) : 0;
                main.startRotation = recipe.upright ? new ParticleSystem.MinMaxCurve(0) : new ParticleSystem.MinMaxCurve(-Mathf.PI, Mathf.PI);
                main.gravityModifier = recipe.gravity;
                main.simulationSpace = ParticleSystemSimulationSpace.Local;
                main.maxParticles = Mathf.Clamp(Mathf.CeilToInt(recipe.rate * recipe.life * 3) + recipe.count * 2, 32, 512);
                main.scalingMode = ParticleSystemScalingMode.Hierarchy;
                main.simulationSpeed = _timeScale;
                var emission = ps.emission;
                emission.enabled = recipe.kind == "emitter";
                emission.rateOverTime = recipe.rate;
                var shape = ps.shape;
                shape.enabled = true;
                shape.shapeType = ParticleSystemShapeType.Sphere;
                shape.radius = recipe.radius;
                if (recipe.kind == "emitter")
                {
                    shape.shapeType = ParticleSystemShapeType.Circle;
                    shape.rotation = new Vector3(-90, 0, 0);
                    var velocity = ps.velocityOverLifetime;
                    velocity.enabled = true;
                    velocity.space = ParticleSystemSimulationSpace.Local;
                    velocity.x = new ParticleSystem.MinMaxCurve(-.15f, .15f);
                    velocity.y = new ParticleSystem.MinMaxCurve(recipe.speed * .7f, recipe.speed * 1.2f);
                    velocity.z = new ParticleSystem.MinMaxCurve(-.15f, .15f);
                }
                var color = ps.colorOverLifetime;
                color.enabled = true;
                var gradient = new Gradient();
                gradient.SetKeys(new[] { new GradientColorKey(Color.white, 0), new GradientColorKey(Color.white, 1) },
                    new[] { new GradientAlphaKey(0, 0), new GradientAlphaKey(1, .1f), new GradientAlphaKey(.7f, .6f), new GradientAlphaKey(0, 1) });
                color.color = gradient;
                var size = ps.sizeOverLifetime;
                size.enabled = true;
                size.size = new ParticleSystem.MinMaxCurve(1, new AnimationCurve(new Keyframe(0, .45f), new Keyframe(.2f, 1), new Keyframe(1, recipe.alpha ? 1.6f : .05f)));
                if (recipe.tiles > 1)
                {
                    var sheet = ps.textureSheetAnimation;
                    sheet.enabled = true; sheet.numTilesX = sheet.numTilesY = recipe.tiles;
                    sheet.animation = ParticleSystemAnimationType.WholeSheet;
                    sheet.frameOverTime = new ParticleSystem.MinMaxCurve(1, AnimationCurve.Linear(0, 0, 1, 1));
                    sheet.cycleCount = 1;
                }
                var renderer = go.GetComponent<ParticleSystemRenderer>();
                if (!string.IsNullOrEmpty(recipe.mesh))
                {
                    // Mesh particles: random 3D tumble, or `upright` (falling arrows, shards) pointing the mesh's +Z along its velocity.
                    renderer.renderMode = ParticleSystemRenderMode.Mesh;
                    layer.Mesh = MeshFor(recipe.mesh);
                    renderer.mesh = layer.Mesh.Mesh;
                    renderer.alignment = recipe.upright ? ParticleSystemRenderSpace.Velocity : ParticleSystemRenderSpace.Local;
                    // Velocity alignment supplies the presentation frame (+Z forward); start rotation supplies the native
                    // mesh basis once. Tumbling debris has no facing constraint, but starts from that same local basis.
                    main.startRotation3D = true;
                    Vector3 basis = layer.Mesh.Basis.eulerAngles * Mathf.Deg2Rad;
                    main.startRotationX = recipe.upright ? new ParticleSystem.MinMaxCurve(basis.x) : new ParticleSystem.MinMaxCurve(basis.x - Mathf.PI, basis.x + Mathf.PI);
                    main.startRotationY = recipe.upright ? new ParticleSystem.MinMaxCurve(basis.y) : new ParticleSystem.MinMaxCurve(basis.y - Mathf.PI, basis.y + Mathf.PI);
                    main.startRotationZ = recipe.upright ? new ParticleSystem.MinMaxCurve(basis.z) : new ParticleSystem.MinMaxCurve(basis.z - Mathf.PI, basis.z + Mathf.PI);
                }
                renderer.sharedMaterial = material;
                renderer.shadowCastingMode = ShadowCastingMode.Off;
                renderer.receiveShadows = false;
                layer.Particles = ps; layer.Renderer = renderer;
            }
            else if (recipe.kind == "trail")
            {
                var trail = go.AddComponent<TrailRenderer>();
                trail.sharedMaterial = material; trail.time = TrailLifetime(recipe.life); trail.minVertexDistance = .03f;
                trail.widthMultiplier = recipe.size; trail.widthCurve = AnimationCurve.Linear(0, 1, 1, 0);
                trail.numCapVertices = 3; trail.numCornerVertices = 3;
                trail.shadowCastingMode = ShadowCastingMode.Off; trail.receiveShadows = false;
                trail.textureMode = LineTextureMode.Stretch;
                layer.Trail = trail; layer.Renderer = trail;
            }
            else
            {
                if (recipe.kind == "orbit")
                {
                    if (!string.IsNullOrEmpty(recipe.mesh)) layer.Mesh = MeshFor(recipe.mesh);
                    layer.Orbit = new Transform[Mathf.Max(1, recipe.count)];
                    layer.OrbitRenderers = new Renderer[layer.Orbit.Length];
                    for (int n = 0; n < layer.Orbit.Length; n++)
                    {
                        var child = new GameObject("Orbit glyph"); child.transform.SetParent(go.transform, false);
                        layer.OrbitRenderers[n] = AddMesh(child, layer.Mesh != null ? layer.Mesh.Mesh : _quad, material);
                        layer.Orbit[n] = child.transform;
                    }
                }
                else if (recipe.kind == "mesh")
                {
                    layer.Mesh = MeshFor(recipe.mesh);
                    layer.Renderer = AddMesh(go, layer.Mesh.Mesh, material);
                }
                else layer.Renderer = AddMesh(go, recipe.kind == "ring" ? _ring : recipe.kind == "arc" ? _arc : recipe.kind == "sphere" ? _sphere : _quad, material);
            }
            return layer;
        }

        static MeshRenderer AddMesh(GameObject go, Mesh mesh, Material material)
        {
            go.AddComponent<MeshFilter>().sharedMesh = mesh;
            var renderer = go.AddComponent<MeshRenderer>();
            renderer.sharedMaterial = material; renderer.shadowCastingMode = ShadowCastingMode.Off; renderer.receiveShadows = false;
            return renderer;
        }

        /// <summary>A pooled layer starts clean: no tint, flipbook frame or scroll offset left over from its previous play.</summary>
        static void ResetProperties(Layer layer)
        {
            layer.Properties.Clear();
            if (layer.Particles != null || layer.Trail != null) return;
            if (layer.Renderer != null) layer.Renderer.SetPropertyBlock(layer.Properties);
            if (layer.OrbitRenderers != null) foreach (var renderer in layer.OrbitRenderers) renderer.SetPropertyBlock(layer.Properties);
        }

        const float MinMeshExtent = .05f, MaxMeshExtent = 6f;

        /// <summary>
        /// Loads Resources/Vfx/Meshes/&lt;id&gt; once. The asset must be exactly one mesh whose axes, scale and pivot are baked
        /// by the importer (node transforms are ignored here): sharedMesh is taken and its imported bounds are validated.
        /// The mesh is a shared asset: cached for the library's life and never destroyed.
        /// </summary>
        MeshAsset MeshFor(string id)
        {
            if (string.IsNullOrEmpty(id)) throw new InvalidOperationException("VFX mesh layer without a mesh id.");
            if (_meshes.TryGetValue(id, out var cached)) return cached;
            var prefab = Resources.Load<GameObject>("Vfx/Meshes/" + id);
            if (prefab == null) throw new InvalidOperationException("Missing VFX mesh: " + id);
            var filters = prefab.GetComponentsInChildren<MeshFilter>(true);
            if (filters.Length != 1 || filters[0].sharedMesh == null || prefab.GetComponentInChildren<SkinnedMeshRenderer>(true) != null)
                throw new InvalidOperationException("VFX mesh must be exactly one static mesh: " + id);
            var mesh = filters[0].sharedMesh;
            Vector3 size = mesh.bounds.size;
            float longest = Mathf.Max(size.x, Mathf.Max(size.y, size.z));
            if (!(longest >= MinMeshExtent && longest <= MaxMeshExtent) || float.IsNaN(mesh.bounds.center.x + mesh.bounds.center.y + mesh.bounds.center.z))
                throw new InvalidOperationException("VFX mesh " + id + " has implausible imported bounds " + size + " (expected 0.05-6 m, scale baked at 1).");
            // Restored originals keep their native axes: these three projectile bodies point up (+Y), not forward;
            // the panel's convex face is +Z. Rotate at presentation time, never rewrite the downloaded mesh/UVs.
            Quaternion basis = id == "thrust_spike" || id == "energy_arrow" || id == "ice_shard" ? Quaternion.Euler(90f, 0f, 0f)
                : id == "barrier_panel" ? Quaternion.Euler(0f, 180f, 0f) : Quaternion.identity;
            var asset = new MeshAsset { Mesh = mesh, FlatXZ = size.y <= size.x && size.y <= size.z, Basis = basis };
            _meshes.Add(id, asset);
            return asset;
        }

        /// <summary>
        /// Blend policy for a layer (Tools/vfx/gen_effects.py): an explicit "alpha"/"add" wins; otherwise broad shapes
        /// (big ground / pillar / area contributors and anything authored <see cref="LayerRecipe.alpha"/>) are alpha-blended
        /// so they stay translucent and element-coloured, while brief sparks and cores stay additive. Broad layers therefore
        /// keep a bounded, non-additive contribution no matter how many overlap.
        /// </summary>
        static bool BlendAlpha(LayerRecipe recipe) => recipe.blend switch
        {
            "alpha" => true,
            "add" => false,
            _ => recipe.big || recipe.alpha
        };

        Material MaterialFor(string texture, bool alpha)
        {
            string key = texture + (alpha ? ":alpha" : ":add");
            if (_materials.TryGetValue(key, out var material)) return material;
            var resource = Resources.Load<Texture2D>("Vfx/Textures/" + texture);
            if (resource == null) throw new InvalidOperationException("Missing VFX texture: " + texture);
            material = new Material(_shader) { name = "VFX " + key, mainTexture = resource };
            material.SetFloat("_DstBlend", (float)(alpha ? BlendMode.OneMinusSrcAlpha : BlendMode.One));
            material.SetFloat("_Additive", alpha ? 0f : 1f);
            _materials.Add(key, material);
            return material;
        }

        void Update()
        {
            var camera = Camera != null ? Camera : UnityEngine.Camera.main;
            if (camera != null) { _viewRotation = camera.transform.rotation; _viewYaw = FlatLook(camera.transform, _viewYaw); }
            float dt = Time.deltaTime * _timeScale;
            for (int i = 0; i < _effects.Count; i++)
            {
                var e = _effects[i];
                if (!e.Active) continue;
                e.Age += dt;
                if (e.HadFollow && e.Follow == null && !e.Ending) End(e);
                if (e.Follow != null) e.Root.transform.position = e.Follow.position + e.Offset;
                if (e.Travel)
                {
                    float p = Mathf.Clamp01(e.Age / e.TravelTime);
                    e.Root.transform.position = TravelPoint(e, p);
                    Aim(e, camera, p);
                }
                if (e.Age >= e.Duration && !e.Ending) End(e);
                Tick(e, dt);
                if (e.Ending)
                {
                    e.Drain -= dt;
                    if (e.Drain <= 0) Recycle(i);
                }
            }
        }
        Quaternion _viewRotation = Quaternion.identity;
        /// <summary>Camera heading flattened onto the floor: upright mesh layers face the camera by yaw only.</summary>
        Quaternion _viewYaw = Quaternion.identity;

        static Quaternion FlatLook(Transform camera, Quaternion previous)
        {
            Vector3 forward = camera.forward; forward.y = 0;
            if (forward.sqrMagnitude < 1e-4f) { forward = camera.up; forward.y = 0; }
            return forward.sqrMagnitude < 1e-4f ? previous : Quaternion.LookRotation(forward.normalized, Vector3.up);
        }

        static Vector3 TravelPoint(Effect e, float p) =>
            Vector3.Lerp(e.From, e.To, p) + Vector3.up * (Mathf.Sin(p * Mathf.PI) * Mathf.Min(.7f, Vector3.Distance(e.From, e.To) * .1f));

        static Vector3 TravelTangent(Effect e, float p)
        {
            Vector3 d = e.To - e.From;
            return d + Vector3.up * (Mathf.Cos(p * Mathf.PI) * Mathf.PI * Mathf.Min(.7f, d.magnitude * .1f));
        }

        /// <summary>Screen-space heading of a projectile at progress <paramref name="p"/>, for `align` layers.</summary>
        static void Aim(Effect e, Camera camera, float p)
        {
            // World-space tangent of the same arc TravelPoint draws; kept when the arc degenerates (From == To) or is not finite.
            if (p < 1)
            {
                Vector3 tangent = TravelTangent(e, p);
                float sqr = tangent.sqrMagnitude;
                if (sqr > 1e-6f && !float.IsInfinity(sqr)) { e.Tangent = tangent / Mathf.Sqrt(sqr); e.HasTangent = true; }
            }
            if (camera == null || p >= 1) return;
            Vector3 a = camera.WorldToScreenPoint(TravelPoint(e, p)), b = camera.WorldToScreenPoint(TravelPoint(e, Mathf.Min(1, p + .05f)));
            if ((b - a).sqrMagnitude > .01f) e.Angle = Mathf.Atan2(b.y - a.y, b.x - a.x) * Mathf.Rad2Deg;
        }

        /// <summary>
        /// Screen-space heading (degrees, +U of an `align` quad) of a non-travelling blow, so impact streaks continue from caster through
        /// target instead of always pointing screen-right. Uses the same readable direction as the mesh layers; refreshed each tick because
        /// the battle camera keeps moving.
        /// </summary>
        void AimFacing(Effect effect)
        {
            Vector3 d = ReadableFacing(effect.Facing);
            Quaternion view = _viewRotation;
            float x = Vector3.Dot(d, view * Vector3.right), y = Vector3.Dot(d, view * Vector3.up);
            if (x * x + y * y > 1e-4f) effect.Angle = Mathf.Atan2(y, x) * Mathf.Rad2Deg;
        }

        void Tick(Effect effect, float dt)
        {
            if (!effect.Travel && effect.HasFacing) AimFacing(effect);
            foreach (var layer in effect.Layers)
            {
                var r = layer.Recipe;
                float elapsed = effect.Age - r.delay;
                if (elapsed < 0 || (!layer.Started && effect.Ending)) continue;
                // Emit() on a system whose simulationSpeed is 0 (battle paused) births particles at NaN positions (invalid
                // bounds and "Invalid AABB" spam every frame they live): particle layers start on the first unpaused tick.
                if (!layer.Started && layer.Particles != null && _timeScale <= 0f) continue;
                if (!layer.Started)
                {
                    layer.Started = true;
                    layer.Transform.gameObject.SetActive(true);
                    Vector3 ahead = r.ahead != 0f && effect.HasFacing ? new Vector3(effect.Facing.x, 0f, effect.Facing.z).normalized * r.ahead : Vector3.zero;
                    layer.Transform.localPosition = new Vector3(ahead.x, r.y, ahead.z);
                    var color = r.untinted ? r.tint : r.tint * effect.Tint;
                    if (!float.IsNaN(effect.Ground) && r.y <= GroundLayerY) PlaceOnGround(effect, layer);
                    if (layer.Particles != null)
                    {
                        var main = layer.Particles.main; main.startColor = color;
                        layer.Particles.Play();
                        if (r.kind == "burst") layer.Particles.Emit(r.count);
                    }
                    if (layer.Trail != null)
                    {
                        layer.Trail.Clear(); layer.Trail.startColor = color; layer.Trail.endColor = new Color(color.r, color.g, color.b, 0);
                        layer.Trail.emitting = true;
                    }
                }
                if (effect.Follow != null && !float.IsNaN(effect.Ground) && r.y <= GroundLayerY) PlaceOnGround(effect, layer);
                // Particles and trails keep their authored blend (BlendAlpha, fixed at build) but get the same
                // coverage-driven brightness policy as meshes, so a wide flame/smoke emitter cannot white the target out.
                if (layer.Particles != null || layer.Trail != null)
                {
                    ApplyGlow(layer);
                    // Meshes set the block below; particles/trails take the early exit, so apply it here.
                    if (layer.Renderer != null) layer.Renderer.SetPropertyBlock(layer.Properties);
                    continue;
                }
                float p = effect.Recipe.loop && !effect.Ending ? Mathf.Repeat(elapsed / r.life, 1) : Mathf.Clamp01(elapsed / r.life);
                // Looping projectile bodies stay solid in flight; looping markers breathe.
                float alpha = effect.Recipe.loop && !effect.Ending ? (effect.Travel ? 1 : .65f + .2f * Mathf.Sin(elapsed * 3)) : Mathf.Min(p * 10, 1) * (1 - p);
                if (effect.Ending) alpha *= Mathf.Clamp01(effect.Drain / Mathf.Max(.01f, r.life));
                Color tint = r.untinted ? r.tint : r.tint * effect.Tint; tint.a *= alpha;
                layer.Properties.SetColor(TintId, tint);
                ApplyGlow(layer);
                if (r.tiles > 1)
                {
                    int frame = Mathf.Min(r.tiles * r.tiles - 1, Mathf.FloorToInt(p * r.tiles * r.tiles));
                    layer.Properties.SetVector(TexStId, new Vector4(1f / r.tiles, 1f / r.tiles, (float)(frame % r.tiles) / r.tiles, 1f - (float)(frame / r.tiles + 1) / r.tiles));
                }
                float size = Mathf.Lerp(r.size, r.endSize > 0 ? r.endSize : r.size, p);
                layer.Transform.localScale = new Vector3(size, r.height > 0 ? r.height : size, size);
                if (r.kind == "ring") layer.Transform.localScale = Vector3.one * size;
                float roll = r.rotation + elapsed * r.spin + (r.align ? effect.Angle : 0);
                if (layer.Mesh != null && layer.Orbit == null)
                {
                    layer.Transform.rotation = MeshRotation(effect, layer, elapsed);
                    // Scroll sweeps the texture along U; every other mesh layer keeps the default offset (properties are reset per play).
                    if (r.scroll != 0) layer.Properties.SetVector(TexStId, new Vector4(1, 1, p * r.scroll, 0));
                }
                else layer.Transform.rotation = r.horizontal || r.kind == "ring" ? Quaternion.Euler(90, 0, roll) : _viewRotation * Quaternion.Euler(0, 0, roll);
                if (r.kind == "sphere") layer.Transform.rotation = Quaternion.Euler(0, elapsed * r.spin, 0);
                if (layer.Orbit != null)
                {
                    // Parent does not scale orbit radius along with the glyphs.
                    layer.Transform.localScale = Vector3.one;
                    layer.Transform.rotation = Quaternion.identity;
                    for (int n = 0; n < layer.Orbit.Length; n++)
                    {
                        float angle = elapsed * r.spin * Mathf.Deg2Rad + n * Mathf.PI * 2 / layer.Orbit.Length;
                        var glyph = layer.Orbit[n];
                        glyph.localPosition = new Vector3(Mathf.Cos(angle) * r.radius, Mathf.Sin(elapsed * 2 + n) * .08f, Mathf.Sin(angle) * r.radius);
                        glyph.localScale = Vector3.one * size;
                        if (layer.Mesh != null)
                        {
                            // Mesh glyphs point (+Z) along their orbit tangent instead of billboarding.
                            var tangent = new Vector3(-Mathf.Sin(angle), 0, Mathf.Cos(angle)) * (r.spin < 0 ? -1f : 1f);
                            glyph.localRotation = Quaternion.LookRotation(tangent, Vector3.up) * Quaternion.Euler(0, 0, r.rotation) * layer.Mesh.Basis;
                        }
                        else glyph.rotation = _viewRotation;
                        layer.OrbitRenderers[n].SetPropertyBlock(layer.Properties);
                    }
                }
                else layer.Renderer.SetPropertyBlock(layer.Properties);
                if (!effect.Recipe.loop && p >= 1) layer.Transform.gameObject.SetActive(false);
            }
        }

        /// <summary>
        /// Glow control from the layer's screen coverage (its renderers' bounds projected by the view camera): the bigger the
        /// layer on screen, the less white core, gain and opacity, the more element colour. `big` layers start at
        /// <see cref="BigFloor"/>. Allocation-free.
        /// </summary>
        void ApplyGlow(Layer layer)
        {
            float coverage = 0f;
            var camera = Camera != null ? Camera : UnityEngine.Camera.main;
            if (camera != null)
            {
                if (layer.OrbitRenderers != null) foreach (var renderer in layer.OrbitRenderers) coverage += Coverage(camera, renderer);
                // An empty particle system / trail has no valid bounds (reading them logs "Invalid AABB" every frame).
                else if (layer.Renderer != null && (layer.Particles != null ? layer.Particles.particleCount > 0 : layer.Trail == null || layer.Trail.positionCount > 1))
                    coverage = Coverage(camera, layer.Renderer);
            }
            float k = Mathf.SmoothStep(0f, 1f, (coverage - CoverageStart) / (CoverageFull - CoverageStart));
            if (layer.Recipe.big) k = Mathf.Max(k, BigFloor);
            // Alpha-blended broad layers keep a readable opacity floor; additive layers may drop lower (their gain already
            // curbs the white-out), so a stack of overlapping additive sparks never over-brightens the target.
            bool alpha = BlendAlpha(layer.Recipe);
            float opacity = Mathf.Lerp(1f, alpha ? MinOpacity : MinOpacity * .5f, k);
            // Big alpha-blended mesh shells (seals, pillars, domes, waves) cel-shade their baked grey texture into flat
            // solid colour; at the usual floor they read as tinted plastic, so they stay a thin translucent shell.
            if (alpha && layer.Recipe.big && layer.Mesh != null) opacity = Mathf.Lerp(BigShellOpacity, MinOpacity * .8f, k);
            layer.Properties.SetVector(GlowId, new Vector4(1f - k, Mathf.Lerp(1f, MinGain, k), opacity, (layer.Recipe.big ? .8f : .4f) * k));
        }

        /// <summary>Share of the viewport covered by a renderer's world bounds (clipped to the screen; 1 when the camera is inside).</summary>
        static float Coverage(Camera camera, Renderer renderer)
        {
            var b = renderer.bounds;
            if (!(b.extents.sqrMagnitude < 1e8f)) return 0f;   // non-finite / degenerate bounds: no coverage
            if (b.Contains(camera.transform.position)) return 1f;
            float x0 = float.MaxValue, y0 = float.MaxValue, x1 = float.MinValue, y1 = float.MinValue;
            Vector3 lo = b.min, hi = b.max;
            for (int k = 0; k < 8; k++)
            {
                var v = camera.WorldToViewportPoint(new Vector3((k & 1) == 0 ? lo.x : hi.x, (k & 2) == 0 ? lo.y : hi.y, (k & 4) == 0 ? lo.z : hi.z));
                if (v.z <= 0f) return 1f;   // straddles the camera: treat as full screen
                if (v.x < x0) x0 = v.x; if (v.x > x1) x1 = v.x; if (v.y < y0) y0 = v.y; if (v.y > y1) y1 = v.y;
            }
            float w = Mathf.Min(x1, 1f) - Mathf.Max(x0, 0f), h = Mathf.Min(y1, 1f) - Mathf.Max(y0, 0f);
            return w > 0f && h > 0f ? w * h : 0f;
        }

        /// <summary>
        /// Orientation of a mesh layer. `horizontal`: native-XZ meshes only yaw (no quad-style 90 degree tilt), XY meshes tilt flat like the
        /// quad. `align` while travelling: +Z along the world trajectory tangent, `rotation`/`spin` roll about it. Otherwise upright: yaw to the
        /// camera, `rotation` tilts about the facing axis (Z) and `spin` turns the mesh about its own up axis (Y).
        /// </summary>
        Quaternion MeshRotation(Effect effect, Layer layer, float elapsed)
        {
            var r = layer.Recipe;
            float spin = elapsed * r.spin;
            if (r.horizontal)
                return (layer.Mesh.FlatXZ ? Quaternion.Euler(0, r.rotation + spin, 0) : Quaternion.Euler(90, 0, r.rotation + spin)) * layer.Mesh.Basis;
            if (r.align && effect.Travel && effect.HasTangent)
                return Quaternion.LookRotation(effect.Tangent, Vector3.up) * Quaternion.Euler(0, 0, r.rotation + spin) * layer.Mesh.Basis;
            if (r.align && !effect.Travel && effect.HasFacing && r.upright)
            {
                // Standing objects (a riot shield set down in front of its bearer): yaw toward the facing only.
                Vector3 flat = new Vector3(effect.Facing.x, 0f, effect.Facing.z);
                if (flat.sqrMagnitude > 1e-4f) return Quaternion.LookRotation(flat, Vector3.up) * Quaternion.Euler(0, r.rotation + spin, 0) * layer.Mesh.Basis;
            }
            if (r.align && !effect.Travel && effect.HasFacing)
                return Quaternion.LookRotation(ReadableFacing(effect.Facing), _viewRotation * Vector3.up) * Quaternion.Euler(0, 0, r.rotation + spin) * layer.Mesh.Basis;
            return _viewYaw * Quaternion.Euler(0, 0, r.rotation) * Quaternion.Euler(0, spin, 0) * layer.Mesh.Basis;
        }

        /// <summary>
        /// A pointed mesh seen head-on collapses into a flat star. When the blow runs closer than ~58 degrees to the view axis the
        /// direction is swung toward the screen plane so the tip still reads as a spike, keeping the sign of its depth.
        /// </summary>
        Vector3 ReadableFacing(Vector3 direction)
        {
            const float MinLateral = .85f;
            Vector3 view = _viewRotation * Vector3.forward;
            float depth = Vector3.Dot(direction, view);
            Vector3 lateral = direction - view * depth;
            float length = lateral.magnitude;
            if (length >= MinLateral) return direction;
            Vector3 side = length > 1e-3f ? lateral / length : _viewRotation * Vector3.right;
            float sign = depth < 0f ? -1f : 1f;
            return side * MinLateral + view * (sign * Mathf.Sqrt(1f - MinLateral * MinLateral));
        }

        /// <summary>Floor layers keep the anchor's x/z but sit just above the floor, unscaled by the effect size.</summary>
        static void PlaceOnGround(Effect effect, Layer layer)
        {
            var anchor = effect.Root.transform.position;
            layer.Transform.position = new Vector3(anchor.x, effect.Ground + .02f, anchor.z);
        }

        static void End(Effect effect)
        {
            effect.Ending = true;
            effect.Drain = .05f;
            foreach (var layer in effect.Layers)
            {
                if (!layer.Started) continue;
                // An arrived projectile's body vanishes on contact; only its trail and sparks drain.
                if (effect.Travel && layer.Particles == null && layer.Trail == null) { layer.Transform.gameObject.SetActive(false); continue; }
                effect.Drain = Mathf.Max(effect.Drain, layer.Recipe.life);
                if (layer.Particles != null) layer.Particles.Stop(true, ParticleSystemStopBehavior.StopEmitting);
                if (layer.Trail != null) layer.Trail.emitting = false;
            }
        }

        void Recycle(int slot)
        {
            var e = _effects[slot];
            foreach (var layer in e.Layers)
            {
                if (layer.Particles != null) layer.Particles.Stop(true, ParticleSystemStopBehavior.StopEmittingAndClear);
                if (layer.Trail != null) { layer.Trail.emitting = false; layer.Trail.Clear(); }
            }
            e.Root.SetActive(false); e.Active = false; e.Follow = null;
            _free[e.Recipe.key].Push(slot);
        }

        static Mesh MakeQuad()
        {
            var mesh = new Mesh { name = "VFX quad" };
            mesh.vertices = new[] { new Vector3(-.5f,-.5f,0), new Vector3(.5f,-.5f,0), new Vector3(.5f,.5f,0), new Vector3(-.5f,.5f,0) };
            mesh.uv = new[] { new Vector2(0,0), new Vector2(1,0), new Vector2(1,1), new Vector2(0,1) };
            mesh.colors = new[] { Color.white, Color.white, Color.white, Color.white };
            mesh.triangles = new[] { 0,1,2,0,2,3 }; mesh.RecalculateBounds(); return mesh;
        }

        static Mesh MakeRibbon(int segments, float degrees, float width, string name)
        {
            var vertices = new Vector3[(segments + 1) * 2]; var uv = new Vector2[vertices.Length];
            var colors = new Color[vertices.Length]; var triangles = new int[segments * 6];
            for (int i = 0; i <= segments; i++)
            {
                float t = (float)i / segments, a = t * degrees * Mathf.Deg2Rad;
                float w = degrees >= 360 ? width : width * Mathf.Sin(t * Mathf.PI);
                var v = new Vector3(Mathf.Cos(a), Mathf.Sin(a), 0);
                vertices[i*2] = v * (.5f - w); vertices[i*2+1] = v * .5f;
                uv[i*2] = new Vector2(t,0); uv[i*2+1] = new Vector2(t,1);
                colors[i*2] = colors[i*2+1] = Color.white;
                if (i == segments) continue;
                int k=i*6, n=i*2;
                triangles[k]=n; triangles[k+1]=n+1; triangles[k+2]=n+3;
                triangles[k+3]=n; triangles[k+4]=n+3; triangles[k+5]=n+2;
            }
            var mesh = new Mesh { name=name, vertices=vertices, uv=uv, colors=colors, triangles=triangles }; mesh.RecalculateBounds(); return mesh;
        }

        static Mesh MakeSphere()
        {
            const int rows=16, columns=24;
            var vertices=new Vector3[(rows+1)*(columns+1)]; var uv=new Vector2[vertices.Length]; var colors=new Color[vertices.Length]; var triangles=new int[rows*columns*6];
            for (int y=0;y<=rows;y++) for(int x=0;x<=columns;x++)
            {
                int i=y*(columns+1)+x; float a=(float)x/columns*Mathf.PI*2, b=(float)y/rows*Mathf.PI;
                vertices[i]=new Vector3(Mathf.Sin(b)*Mathf.Cos(a),Mathf.Cos(b),Mathf.Sin(b)*Mathf.Sin(a))*.5f;
                uv[i]=new Vector2((float)x/columns,(float)y/rows); colors[i]=Color.white;
                if(y==rows||x==columns) continue;
                int k=(y*columns+x)*6,n=i+columns+1;
                triangles[k]=i;triangles[k+1]=n;triangles[k+2]=i+1;triangles[k+3]=i+1;triangles[k+4]=n;triangles[k+5]=n+1;
            }
            var mesh=new Mesh { name="VFX barrier sphere", vertices=vertices, uv=uv, colors=colors, triangles=triangles }; mesh.RecalculateBounds(); return mesh;
        }

        void OnDestroy()
        {
            if (Instance == this) Instance = null;
            foreach (var material in _materials.Values) if (material != null) Destroy(material);
            if (_quad != null) Destroy(_quad); if (_ring != null) Destroy(_ring); if (_arc != null) Destroy(_arc); if (_sphere != null) Destroy(_sphere);
        }
    }
}
