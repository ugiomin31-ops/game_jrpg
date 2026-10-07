using UnityEngine;
using UnityEngine.Rendering;
using UnityEngine.Rendering.Universal;

namespace Abyss.Runtime.World
{
    /// <summary>Lighting + fog + post-processing preset for an area (town, each biome, battle variants).</summary>
    public sealed class AtmospherePreset
    {
        public Color SunColor = Color.white;
        public float SunIntensity = 1.2f;
        public Vector3 SunEuler = new Vector3(50, -30, 0);
        public Color AmbientSky = new Color(0.5f, 0.55f, 0.7f);
        public Color AmbientEquator = new Color(0.35f, 0.35f, 0.45f);
        public Color AmbientGround = new Color(0.2f, 0.18f, 0.22f);
        public Color FogColor = new Color(0.08f, 0.1f, 0.17f);
        public float FogStart = 18f, FogEnd = 60f;
        public Color BackgroundColor = new Color(0.04f, 0.05f, 0.08f);
        public float Bloom = 0.9f, BloomThreshold = 0.95f;
        public float Exposure = 0f, Contrast = 12f, Saturation = 12f;
        public Color ColorFilter = Color.white;
        public float Vignette = 0.28f;
        public float Temperature = 0f;
        public Color TorchColor = new Color(1f, 0.7f, 0.4f);

        /// <summary>
        /// First-person dungeon mood per biome (ForTileset stays the battle-arena look): ember = close red haze and
        /// warm lava bounce from below, frost = bright blue mist, crypt = near-black short fog with dim moonlight,
        /// verdant = open sky with a long soft haze. Cave biomes have ceilings, so the background only shows down
        /// long corridors and through the fog.
        /// </summary>
        public static AtmospherePreset ForDungeon(string tileset)
        {
            var p = ForTileset(tileset);
            switch (tileset)
            {
                case "ember_caverns":
                    p.SunIntensity = 1.0f; p.SunColor = new Color(1f, 0.6f, 0.38f);
                    p.AmbientSky = new Color(0.55f, 0.32f, 0.24f); p.AmbientEquator = new Color(0.42f, 0.22f, 0.15f); p.AmbientGround = new Color(0.36f, 0.12f, 0.05f);
                    p.FogColor = new Color(0.24f, 0.08f, 0.04f); p.FogStart = 6; p.FogEnd = 36; p.BackgroundColor = new Color(0.12f, 0.04f, 0.02f);
                    p.Bloom = .65f; p.BloomThreshold = 1.15f; p.Saturation = 18; p.Temperature = 20;
                    break;
                case "frost_grotto":
                    p.SunIntensity = 1.15f; p.SunColor = new Color(0.78f, 0.9f, 1f);
                    p.AmbientSky = new Color(0.55f, 0.7f, 0.95f); p.AmbientEquator = new Color(0.36f, 0.5f, 0.7f); p.AmbientGround = new Color(0.45f, 0.55f, 0.7f);
                    p.FogColor = new Color(0.42f, 0.58f, 0.75f); p.FogStart = 7; p.FogEnd = 40; p.BackgroundColor = new Color(0.3f, 0.45f, 0.62f);
                    p.Bloom = .55f; p.BloomThreshold = 1.1f; p.Saturation = 6; p.Temperature = -16;
                    break;
                case "haunted_crypt":
                    p.SunIntensity = 0.6f; p.SunColor = new Color(0.55f, 0.55f, 0.9f);
                    p.AmbientSky = new Color(0.3f, 0.26f, 0.48f); p.AmbientEquator = new Color(0.18f, 0.16f, 0.28f); p.AmbientGround = new Color(0.08f, 0.06f, 0.12f);
                    p.FogColor = new Color(0.05f, 0.04f, 0.09f); p.FogStart = 4; p.FogEnd = 26; p.BackgroundColor = new Color(0.02f, 0.02f, 0.05f);
                    p.Bloom = .6f; p.BloomThreshold = 1.1f; p.Saturation = 0; p.Vignette = 0.38f; p.Temperature = -10;
                    break;
                case "verdant_ruins":
                    p.SunIntensity = 1.4f; p.SunColor = new Color(1f, 0.94f, 0.8f);
                    p.AmbientSky = new Color(0.62f, 0.75f, 0.8f); p.AmbientEquator = new Color(0.42f, 0.52f, 0.4f); p.AmbientGround = new Color(0.22f, 0.26f, 0.16f);
                    p.FogColor = new Color(0.6f, 0.74f, 0.76f); p.FogStart = 14; p.FogEnd = 60; p.BackgroundColor = new Color(0.55f, 0.75f, 0.85f);
                    p.Bloom = .45f; p.Saturation = 12; p.Temperature = 6; p.Vignette = 0.2f;
                    break;
            }
            return p;
        }

        public static AtmospherePreset ForTileset(string tileset)
        {
            switch (tileset)
            {
                case "verdant_ruins":
                    return new AtmospherePreset
                    {
                        SunColor = new Color(1f, 0.93f, 0.78f), SunIntensity = 1.35f, SunEuler = new Vector3(55, -35, 0),
                        AmbientSky = new Color(0.55f, 0.7f, 0.65f), AmbientEquator = new Color(0.36f, 0.46f, 0.36f), AmbientGround = new Color(0.18f, 0.22f, 0.14f),
                        FogColor = new Color(0.16f, 0.24f, 0.2f), FogStart = 16, FogEnd = 55, BackgroundColor = new Color(0.12f, 0.2f, 0.17f),
                        Bloom = 0.8f, Saturation = 18, Temperature = 6, TorchColor = new Color(1f, 0.82f, 0.5f),
                    };
                case "frost_grotto":
                    return new AtmospherePreset
                    {
                        SunColor = new Color(0.75f, 0.88f, 1f), SunIntensity = 1.1f, SunEuler = new Vector3(60, 20, 0),
                        AmbientSky = new Color(0.5f, 0.65f, 0.9f), AmbientEquator = new Color(0.3f, 0.42f, 0.6f), AmbientGround = new Color(0.15f, 0.2f, 0.3f),
                        FogColor = new Color(0.12f, 0.2f, 0.32f), FogStart = 14, FogEnd = 50, BackgroundColor = new Color(0.07f, 0.12f, 0.22f),
                        Bloom = .6f, BloomThreshold = 1.1f, Saturation = 10, Temperature = -14, TorchColor = new Color(0.55f, 0.85f, 1f),
                    };
                case "ember_caverns":
                    return new AtmospherePreset
                    {
                        SunColor = new Color(1f, 0.62f, 0.38f), SunIntensity = 1.15f, SunEuler = new Vector3(48, 140, 0),
                        AmbientSky = new Color(0.6f, 0.38f, 0.3f), AmbientEquator = new Color(0.42f, 0.24f, 0.18f), AmbientGround = new Color(0.3f, 0.1f, 0.05f),
                        FogColor = new Color(0.25f, 0.09f, 0.05f), FogStart = 14, FogEnd = 48, BackgroundColor = new Color(0.16f, 0.05f, 0.03f),
                        Bloom = .6f, BloomThreshold = 1.15f, Saturation = 12, Temperature = 18, TorchColor = new Color(1f, 0.55f, 0.25f),
                    };
                case "haunted_crypt":
                    return new AtmospherePreset
                    {
                        SunColor = new Color(0.62f, 0.6f, 0.95f), SunIntensity = 0.75f, SunEuler = new Vector3(65, -60, 0),
                        AmbientSky = new Color(0.36f, 0.32f, 0.55f), AmbientEquator = new Color(0.22f, 0.2f, 0.34f), AmbientGround = new Color(0.1f, 0.08f, 0.14f),
                        FogColor = new Color(0.07f, 0.06f, 0.13f), FogStart = 10, FogEnd = 42, BackgroundColor = new Color(0.03f, 0.03f, 0.07f),
                        Bloom = .55f, BloomThreshold = 1.1f, Saturation = 4, Temperature = -8, TorchColor = new Color(0.6f, 0.9f, 0.85f),
                    };
                case "town_night":
                    return new AtmospherePreset
                    {
                        SunColor = new Color(0.58f, 0.66f, 1f), SunIntensity = 0.7f, SunEuler = new Vector3(42, -50, 0),
                        AmbientSky = new Color(0.32f, 0.36f, 0.62f), AmbientEquator = new Color(0.24f, 0.24f, 0.4f), AmbientGround = new Color(0.12f, 0.1f, 0.14f),
                        FogColor = new Color(0.1f, 0.11f, 0.22f), FogStart = 30, FogEnd = 110, BackgroundColor = new Color(0.06f, 0.07f, 0.16f),
                        Bloom = .55f, BloomThreshold = 1.1f, Saturation = 8, Temperature = -6, TorchColor = new Color(1f, 0.72f, 0.42f),
                    };
                case "town_dawn":
                    return new AtmospherePreset
                    {
                        SunColor = new Color(1f, 0.92f, 0.8f), SunIntensity = 1.15f, SunEuler = new Vector3(18, 70, 0),
                        AmbientSky = new Color(.64f, .72f, .8f), AmbientEquator = new Color(.42f, .5f, .56f), AmbientGround = new Color(.2f, .22f, .26f),
                        FogColor = new Color(.61f, .72f, .75f), FogStart = 40, FogEnd = 140, BackgroundColor = new Color(.66f, .77f, .86f),
                        Bloom = .45f, BloomThreshold = 1.2f, Saturation = 5, Temperature = 4, TorchColor = new Color(1f, 0.8f, 0.55f),
                    };
                default:
                    return new AtmospherePreset();
            }
        }
    }

    /// <summary>Owns the scene's sun, ambient, fog and the global post-processing Volume.</summary>
    public sealed class Atmosphere : MonoBehaviour
    {
        public Light Sun { get; private set; }
        public Volume Volume { get; private set; }
        public AtmospherePreset Current { get; private set; }

        Bloom _bloom;
        ColorAdjustments _color;
        Vignette _vignette;
        WhiteBalance _white;
        Tonemapping _tone;

        public static Atmosphere Create(Transform parent = null)
        {
            var go = new GameObject("Atmosphere");
            if (parent != null) go.transform.SetParent(parent, false);
            var a = go.AddComponent<Atmosphere>();
            a.Build();
            return a;
        }

        void Build()
        {
            var sunGo = new GameObject("Sun");
            sunGo.transform.SetParent(transform, false);
            Sun = sunGo.AddComponent<Light>();
            Sun.type = LightType.Directional;
            Sun.shadows = LightShadows.Soft;
            Sun.shadowStrength = 0.85f;
            RenderSettings.sun = Sun;

            Volume = gameObject.AddComponent<Volume>();
            Volume.isGlobal = true;
            Volume.priority = 0;
            var profile = ScriptableObject.CreateInstance<VolumeProfile>();
            Volume.sharedProfile = profile;
            _tone = profile.Add<Tonemapping>(true);
            _tone.mode.Override(TonemappingMode.Neutral);
            _bloom = profile.Add<Bloom>(true);
            _bloom.scatter.Override(0.72f);
            _bloom.highQualityFiltering.Override(true);
            _color = profile.Add<ColorAdjustments>(true);
            _vignette = profile.Add<Vignette>(true);
            _vignette.smoothness.Override(0.45f);
            _white = profile.Add<WhiteBalance>(true);
        }

        public void Apply(AtmospherePreset p)
        {
            Current = p;
            Sun.color = p.SunColor;
            Sun.intensity = p.SunIntensity;
            Sun.transform.rotation = Quaternion.Euler(p.SunEuler);
            RenderSettings.ambientMode = AmbientMode.Trilight;
            RenderSettings.ambientSkyColor = p.AmbientSky;
            RenderSettings.ambientEquatorColor = p.AmbientEquator;
            RenderSettings.ambientGroundColor = p.AmbientGround;
            RenderSettings.fog = true;
            RenderSettings.fogMode = FogMode.Linear;
            RenderSettings.fogColor = p.FogColor;
            RenderSettings.fogStartDistance = p.FogStart;
            RenderSettings.fogEndDistance = p.FogEnd;
            _bloom.intensity.Override(p.Bloom);
            _bloom.threshold.Override(p.BloomThreshold);
            _color.postExposure.Override(p.Exposure);
            _color.contrast.Override(p.Contrast);
            _color.saturation.Override(p.Saturation);
            _color.colorFilter.Override(p.ColorFilter);
            _vignette.intensity.Override(p.Vignette);
            _white.temperature.Override(p.Temperature);
        }

        /// <summary>Configure a camera for this look (post-processing on, background colour, HDR).</summary>
        public void SetupCamera(Camera cam)
        {
            if (cam == null) return;
            cam.clearFlags = CameraClearFlags.SolidColor;
            cam.backgroundColor = Current != null ? Current.BackgroundColor : Color.black;
            cam.allowHDR = true;
            var data = cam.GetUniversalAdditionalCameraData();
            data.renderPostProcessing = true;
            data.antialiasing = AntialiasingMode.SubpixelMorphologicalAntiAliasing;
            data.antialiasingQuality = AntialiasingQuality.High;
        }
    }
}
