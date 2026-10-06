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
            /// <summary>Particles keep the texture upright (no random spin): falling arrows, rain streaks.</summary>
            public bool upright;
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
            public float Age, Duration, TravelTime, Drain;
            public Color Tint;
        }

        public static VfxLibrary Instance { get; private set; }
        public Camera Camera { get; set; }
        readonly Dictionary<string, Recipe> _recipes = new Dictionary<string, Recipe>(StringComparer.Ordinal);
        readonly Dictionary<string, Stack<int>> _free = new Dictionary<string, Stack<int>>(StringComparer.Ordinal);
        readonly Dictionary<string, Material> _materials = new Dictionary<string, Material>(StringComparer.Ordinal);
        readonly List<Effect> _effects = new List<Effect>(128);
        Mesh _quad, _ring, _arc, _sphere;
        Shader _shader;
        static readonly int TintId = Shader.PropertyToID("_Tint");
        static readonly int TexStId = Shader.PropertyToID("_MainTex_ST");

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

        public VfxHandle Play(string key, Vector3 position, Color? tint = null, float scale = 1f, float duration = 0f, Transform follow = null)
        {
            if (string.IsNullOrEmpty(key)) return default;
            if (!_recipes.TryGetValue(key, out var recipe)) throw new ArgumentException("Unknown VFX key: " + key, nameof(key));
            var free = _free[key];
            int slot = free.Count > 0 ? free.Pop() : Build(recipe);
            var effect = _effects[slot];
            effect.Generation++;
            effect.Active = true; effect.Ending = false; effect.Travel = false;
            effect.Age = 0; effect.Drain = 0; effect.Follow = follow; effect.HadFollow = follow != null;
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
                if (layer.Particles != null) layer.Particles.Stop(true, ParticleSystemStopBehavior.StopEmittingAndClear);
                if (layer.Trail != null) { layer.Trail.emitting = false; layer.Trail.Clear(); }
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
            var material = MaterialFor(recipe.texture, recipe.alpha);
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
                renderer.sharedMaterial = material;
                renderer.shadowCastingMode = ShadowCastingMode.Off;
                renderer.receiveShadows = false;
                layer.Particles = ps; layer.Renderer = renderer;
            }
            else if (recipe.kind == "trail")
            {
                var trail = go.AddComponent<TrailRenderer>();
                trail.sharedMaterial = material; trail.time = recipe.life; trail.minVertexDistance = .03f;
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
                    layer.Orbit = new Transform[Mathf.Max(1, recipe.count)];
                    layer.OrbitRenderers = new Renderer[layer.Orbit.Length];
                    for (int n = 0; n < layer.Orbit.Length; n++)
                    {
                        var child = new GameObject("Orbit glyph"); child.transform.SetParent(go.transform, false);
                        layer.OrbitRenderers[n] = AddMesh(child, _quad, material);
                        layer.Orbit[n] = child.transform;
                    }
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
            if (camera != null) _viewRotation = camera.transform.rotation;
            float dt = Time.deltaTime;
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
                    e.Root.transform.position = Vector3.Lerp(e.From, e.To, p) + Vector3.up * (Mathf.Sin(p * Mathf.PI) * Mathf.Min(.7f, Vector3.Distance(e.From, e.To) * .1f));
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

        void Tick(Effect effect, float dt)
        {
            foreach (var layer in effect.Layers)
            {
                var r = layer.Recipe;
                float elapsed = effect.Age - r.delay;
                if (elapsed < 0 || (!layer.Started && effect.Ending)) continue;
                if (!layer.Started)
                {
                    layer.Started = true;
                    layer.Transform.gameObject.SetActive(true);
                    layer.Transform.localPosition = new Vector3(0, r.y, 0);
                    var color = r.tint * effect.Tint;
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
                if (layer.Particles != null || layer.Trail != null) continue;
                float p = effect.Recipe.loop && !effect.Ending ? Mathf.Repeat(elapsed / r.life, 1) : Mathf.Clamp01(elapsed / r.life);
                float alpha = effect.Recipe.loop && !effect.Ending ? .65f + .2f * Mathf.Sin(elapsed * 3) : Mathf.Min(p * 10, 1) * (1 - p);
                if (effect.Ending) alpha *= Mathf.Clamp01(effect.Drain / Mathf.Max(.01f, r.life));
                Color tint = r.tint * effect.Tint; tint.a *= alpha;
                layer.Properties.SetColor(TintId, tint);
                if (r.tiles > 1)
                {
                    int frame = Mathf.Min(r.tiles * r.tiles - 1, Mathf.FloorToInt(p * r.tiles * r.tiles));
                    layer.Properties.SetVector(TexStId, new Vector4(1f / r.tiles, 1f / r.tiles, (float)(frame % r.tiles) / r.tiles, 1f - (float)(frame / r.tiles + 1) / r.tiles));
                }
                float size = Mathf.Lerp(r.size, r.endSize > 0 ? r.endSize : r.size, p);
                layer.Transform.localScale = new Vector3(size, r.height > 0 ? r.height : size, size);
                if (r.kind == "ring") layer.Transform.localScale = Vector3.one * size;
                layer.Transform.rotation = r.horizontal || r.kind == "ring" ? Quaternion.Euler(90, 0, r.rotation + elapsed * r.spin) : _viewRotation * Quaternion.Euler(0, 0, r.rotation + elapsed * r.spin);
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
                        glyph.localScale = Vector3.one * size; glyph.rotation = _viewRotation;
                        layer.OrbitRenderers[n].SetPropertyBlock(layer.Properties);
                    }
                }
                else layer.Renderer.SetPropertyBlock(layer.Properties);
                if (!effect.Recipe.loop && p >= 1) layer.Transform.gameObject.SetActive(false);
            }
        }

        static void End(Effect effect)
        {
            effect.Ending = true;
            effect.Drain = .05f;
            foreach (var layer in effect.Layers)
            {
                if (!layer.Started) continue;
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
