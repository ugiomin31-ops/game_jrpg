using UnityEngine;
using UnityEngine.Rendering;

namespace Abyss.Runtime.Art
{
    /// <summary>Which scene a camera is rendering; picks the toon outline profile (see <see cref="OutlineCamera"/>).</summary>
    public enum OutlineContext { Default, Battle, Town, Dungeon, Inspect }

    /// <summary>Camera-scoped controls of the Abyss/Toon "Outline" pass: width scale, reference depth and far fade.</summary>
    public readonly struct OutlineProfile
    {
        public readonly float Scale, RefDepth, FadeStart, FadeEnd;
        public OutlineProfile(float scale, float refDepth, float fadeStart, float fadeEnd)
        { Scale = scale; RefDepth = refDepth; FadeStart = fadeStart; FadeEnd = fadeEnd; }
    }

    /// <summary>
    /// Applies a per-context outline profile to ONE camera. The values are shader globals, written in that camera's
    /// beginCameraRendering and put back to the neutral profile in endCameraRendering, so another camera (render
    /// texture, scene view, inspect stage) never inherits them and nothing leaks when the camera is disabled.
    /// Material widths are untouched: the profile only scales them (width * Scale, constant in pixels up to RefDepth,
    /// then shrinking, fading out between FadeStart and FadeEnd metres; FadeEnd &lt;= FadeStart disables the fade).
    /// </summary>
    [DisallowMultipleComponent]
    public sealed class OutlineCamera : MonoBehaviour
    {
        static readonly int ScaleId = Shader.PropertyToID("_AbyssOutlineScale");
        static readonly int RefDepthId = Shader.PropertyToID("_AbyssOutlineRefDepth");
        static readonly int FadeStartId = Shader.PropertyToID("_AbyssOutlineFadeStart");
        static readonly int FadeEndId = Shader.PropertyToID("_AbyssOutlineFadeEnd");

        /// <summary>Neutral look: the legacy behaviour (scale 1, 6 m reference, fade 30..40 m which only touches far haze).</summary>
        public static readonly OutlineProfile Neutral = new OutlineProfile(1f, 6f, 30f, 40f);

        /// <summary>Independent switches: a context whose switch is off renders with <see cref="Neutral"/>.</summary>
        /// <remarks>Town ships on (scale 1 so environment and character widths are unchanged; only the far end differs).
        /// Dungeon ships OFF: the 0.8 / 4 m / 14-22 m first-person profile would thin the subway environment, which must stay as is.</remarks>
        public static bool TownProfileEnabled = true;
        public static bool DungeonProfileEnabled = false;

        public static OutlineProfile ProfileFor(OutlineContext context)
        {
            switch (context)
            {
                case OutlineContext.Battle: return new OutlineProfile(1.0f, 6f, 30f, 40f);
                case OutlineContext.Town: return TownProfileEnabled ? new OutlineProfile(1.0f, 8f, 18f, 26f) : Neutral;
                case OutlineContext.Dungeon: return DungeonProfileEnabled ? new OutlineProfile(0.8f, 4f, 14f, 22f) : Neutral;
                case OutlineContext.Inspect: return new OutlineProfile(1.15f, 3f, 0f, 0f);
                default: return Neutral;
            }
        }

        public OutlineContext Context = OutlineContext.Default;
        Camera _camera;

        /// <summary>The controller on a camera (added when missing); <paramref name="context"/> null keeps the current one.</summary>
        public static OutlineCamera Ensure(Camera camera, OutlineContext? context = null)
        {
            if (camera == null) return null;
            var c = camera.GetComponent<OutlineCamera>();
            if (c == null) c = camera.gameObject.AddComponent<OutlineCamera>();
            if (context.HasValue) c.Context = context.Value;
            return c;
        }

        void OnEnable()
        {
            _camera = GetComponent<Camera>();
            RenderPipelineManager.beginCameraRendering += OnBegin;
            RenderPipelineManager.endCameraRendering += OnEnd;
        }

        void OnDisable()
        {
            RenderPipelineManager.beginCameraRendering -= OnBegin;
            RenderPipelineManager.endCameraRendering -= OnEnd;
            Apply(Neutral);
        }

        void OnBegin(ScriptableRenderContext context, Camera camera)
        {
            if (camera == _camera) Apply(ProfileFor(Context));
        }

        void OnEnd(ScriptableRenderContext context, Camera camera)
        {
            if (camera == _camera) Apply(Neutral);
        }

        static void Apply(in OutlineProfile p)
        {
            Shader.SetGlobalFloat(ScaleId, p.Scale);
            Shader.SetGlobalFloat(RefDepthId, p.RefDepth);
            Shader.SetGlobalFloat(FadeStartId, p.FadeStart);
            Shader.SetGlobalFloat(FadeEndId, p.FadeEnd);
        }
    }
}
