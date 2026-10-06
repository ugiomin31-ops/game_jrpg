using System;
using UnityEngine;
using UnityEngine.UI;

namespace Abyss.UI
{
    /// <summary>
    /// Full-screen transitions on the top layer: colour fades and a stylised diagonal "blade" wipe
    /// (navy bands with gold leading edges sweep across, then reveal). Blocks input while covering.
    /// Access via <see cref="UIRoot.Fader"/>. Every call returns a yieldable <see cref="UITween"/>.
    /// </summary>
    public sealed class UIFader : MonoBehaviour
    {
        const int Bands = 9;
        const float Tilt = 14f;

        [SerializeField] Image _fade;
        [SerializeField] RectTransform _wipeRoot;
        [SerializeField] RectTransform[] _bands;
        UITween _current;

        /// <summary>True while a fade/wipe covers (or is covering) the screen.</summary>
        public bool IsBusy => _current != null && !_current.IsDone;
        /// <summary>True when the screen is fully covered by the fade colour.</summary>
        public bool IsOpaque => _fade != null && _fade.color.a >= 0.999f;

        internal void Build()
        {
            var rt = (RectTransform)transform;
            rt.Stretch();
            _fade = UIFactory.Fill(rt, new Color(0f, 0f, 0f, 0f), "Fade", raycast: true);
            _fade.raycastTarget = false;

            _wipeRoot = UIFactory.Rect(rt, "Wipe");
            _wipeRoot.Place(UIAnchor.Center, Vector2.zero, new Vector2(2600f, 2000f));
            _wipeRoot.localEulerAngles = new Vector3(0f, 0f, Tilt);
            _bands = new RectTransform[Bands];
            float w = 2600f / Bands;
            for (int i = 0; i < Bands; i++)
            {
                var band = UIFactory.Rect(_wipeRoot, "Band " + i);
                band.anchorMin = new Vector2((float)i / Bands, 0f);
                band.anchorMax = new Vector2((float)(i + 1) / Bands, 1f);
                band.offsetMin = Vector2.zero;
                band.offsetMax = new Vector2(1.5f, 0f); // overlap hides seams
                var fill = UIFactory.Image(band, UISprites.White, i % 2 == 0 ? UITheme.Hex("0b1129") : UITheme.Hex("0e1636"), "Fill");
                fill.rectTransform.Stretch();
                var shade = UIFactory.Image(band, UISprites.GradientH, new Color(0.25f, 0.32f, 0.7f, 0.18f), "Shade");
                shade.rectTransform.Stretch();
                var edge = UIFactory.Image(band, UISprites.White, UITheme.Gold, "Edge");
                edge.rectTransform.anchorMin = new Vector2(1f, 0f);
                edge.rectTransform.anchorMax = new Vector2(1f, 1f);
                edge.rectTransform.pivot = new Vector2(1f, 0.5f);
                edge.rectTransform.sizeDelta = new Vector2(3f, 0f);
                edge.rectTransform.anchoredPosition = Vector2.zero;
                var glow = UIFactory.Image(band, UISprites.GradientH, new Color(1f, 0.7f, 0.35f, 0.35f), "Glow");
                glow.rectTransform.anchorMin = new Vector2(1f, 0f);
                glow.rectTransform.anchorMax = new Vector2(1f, 1f);
                glow.rectTransform.pivot = new Vector2(1f, 0.5f);
                glow.rectTransform.sizeDelta = new Vector2(Mathf.Min(60f, w * 0.4f), 0f);
                glow.rectTransform.anchoredPosition = new Vector2(-3f, 0f);
                band.localScale = new Vector3(0f, 1f, 1f);
                band.pivot = new Vector2(0f, 0.5f);
                _bands[i] = band;
            }
            _wipeRoot.gameObject.SetActive(false);
        }

        /// <summary>Fades to <paramref name="color"/> (default black).</summary>
        public UITween FadeOut(float duration = 0.4f, Color? color = null)
        {
            var c = color ?? Color.black;
            Begin();
            _fade.raycastTarget = true;
            UIInput.PushLayer(transform);
            var from = _fade.color;
            if (from.a <= 0.001f) from = c.WithAlpha(0f);
            var to = c.WithAlpha(1f);
            return _current = UITween.To(_fade, duration, p => _fade.color = Color.LerpUnclamped(from, to, p), UIEase.InOutCubic);
        }

        /// <summary>Fades from the current colour back to clear.</summary>
        public UITween FadeIn(float duration = 0.4f)
        {
            Begin();
            UIInput.PushLayer(transform);
            var from = _fade.color;
            var to = from.WithAlpha(0f);
            return _current = UITween.To(_fade, duration, p => _fade.color = Color.LerpUnclamped(from, to, p), UIEase.InOutCubic)
                .OnComplete(() => { if (_fade != null) _fade.raycastTarget = false; UIInput.PopLayer(transform); });
        }

        /// <summary>
        /// Blade wipe: bands sweep in left→right, <paramref name="onCovered"/> runs while the screen is hidden
        /// (swap scenes/rooms there), then the bands retract to reveal. The returned tween completes when revealed.
        /// </summary>
        public UITween Wipe(Action onCovered, float duration = 0.9f)
        {
            Begin();
            var done = UITween.Delay(this, duration);
            _wipeRoot.gameObject.SetActive(true);
            _fade.raycastTarget = true;
            UIInput.PushLayer(transform);
            float half = duration * 0.45f, hold = duration * 0.1f, stagger = half * 0.35f / Bands, bandTime = half - stagger * (Bands - 1);
            UITween.Kill(_wipeRoot);
            for (int i = 0; i < Bands; i++)
            {
                var band = _bands[i];
                UITween.Kill(band);
                band.pivot = new Vector2(0f, 0.5f);
                band.localScale = new Vector3(0f, 1f, 1f);
                UITween.To(band, bandTime, p => band.localScale = new Vector3(p, 1f, 1f), UIEase.OutCubic, i * stagger);
            }
            UITween.Delay(_wipeRoot, half + hold * 0.5f, () =>
            {
                onCovered?.Invoke();
                if (_wipeRoot == null) return;
                for (int i = 0; i < Bands; i++)
                {
                    var band = _bands[i];
                    // Keep the band's left edge fixed while flipping the pivot so it retracts to the right.
                    band.pivot = new Vector2(1f, 0.5f);
                    band.localScale = Vector3.one;
                    UITween.To(band, bandTime, p => band.localScale = new Vector3(1f - p, 1f, 1f), UIEase.InCubic, hold * 0.5f + i * stagger);
                }
            });
            if (!Application.isPlaying) _wipeRoot.gameObject.SetActive(false);
            return _current = done.OnComplete(() =>
            {
                if (_wipeRoot == null) return;
                _wipeRoot.gameObject.SetActive(false);
                _fade.raycastTarget = _fade.color.a > 0.001f;
                if (!_fade.raycastTarget) UIInput.PopLayer(transform);
            });
        }

        /// <summary>Instantly sets the fade overlay alpha (e.g. start a scene black).</summary>
        public void SetOpacity(float alpha, Color? color = null)
        {
            Begin();
            _fade.color = (color ?? Color.black).WithAlpha(alpha);
            _fade.raycastTarget = alpha > 0.001f;
            if (alpha > 0.001f) UIInput.PushLayer(transform);
            else UIInput.PopLayer(transform);
        }

        void Begin()
        {
            _current?.Kill();
            UITween.Kill(_fade);
            UITween.Kill(_wipeRoot);
            if (_bands != null) foreach (var band in _bands) UITween.Kill(band);
            if (_wipeRoot != null) _wipeRoot.gameObject.SetActive(false);
            transform.SetAsLastSibling();
        }

        void OnDisable() => UIInput.PopLayer(transform);
    }
}
