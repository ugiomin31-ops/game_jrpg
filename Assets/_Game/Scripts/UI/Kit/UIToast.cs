using System.Collections.Generic;
using TMPro;
using UnityEngine;
using UnityEngine.UI;

namespace Abyss.UI
{
    /// <summary>Toast accent.</summary>
    public enum UIToastKind
    {
        /// <summary>Gold accent (loot, info).</summary>
        Info,
        /// <summary>Green accent (success, level up).</summary>
        Good,
        /// <summary>Red accent (warnings, failures).</summary>
        Warning,
    }

    /// <summary>
    /// Notifications: small toasts sliding in at the top-right (stacking, auto-expire) and a large centre
    /// ribbon banner ("B3F 이끼 낀 유적", "전투 승리!"). Access via <see cref="UIRoot.Toast"/>.
    /// </summary>
    public sealed class UIToast : MonoBehaviour
    {
        const float ToastWidth = 520f, ToastHeight = 64f, Gap = 10f;
        const int MaxToasts = 4;

        sealed class Entry
        {
            public RectTransform Rect;
            public CanvasGroup Group;
            public float Expire;
            public bool Leaving;
        }

        readonly List<Entry> _toasts = new List<Entry>();
        RectTransform _toastRoot, _banner;
        CanvasGroup _bannerGroup;
        TextMeshProUGUI _bannerTitle, _bannerSub;
        Image _bannerGlow;
        UITween _bannerTween;

        internal void Build()
        {
            var rt = (RectTransform)transform;
            rt.Stretch();
            _toastRoot = UIFactory.Rect(rt, "Toasts");
            _toastRoot.Place(UIAnchor.TopRight, new Vector2(-36f, -36f), new Vector2(ToastWidth, 400f));

            _banner = UIFactory.Rect(rt, "Banner");
            _banner.Place(UIAnchor.Center, new Vector2(0f, 150f), new Vector2(1500f, 150f));
            _bannerGroup = _banner.gameObject.AddComponent<CanvasGroup>();
            _bannerGroup.blocksRaycasts = false;
            _bannerGlow = UIFactory.Image(_banner, UISprites.SoftRadial, new Color(1f, 0.7f, 0.35f, 0.25f), "Glow");
            _bannerGlow.rectTransform.Stretch(250f, -40f, 250f, -40f);
            var ribbon = UIFactory.Image(_banner, UISprites.Ribbon, Color.white, "Ribbon");
            ribbon.rectTransform.Stretch();
            _bannerTitle = UIFactory.Label(_banner, "", UITheme.SizeBanner, UIFont.Title, UITheme.GoldBright, TextAlignmentOptions.Center, UITextFx.Glow, "Title");
            _bannerTitle.rectTransform.Stretch(0f, 14f, 0f, 46f);
            _bannerTitle.characterSpacing = 6f;
            _bannerSub = UIFactory.Label(_banner, "", UITheme.SizeBody, UIFont.Bold, UITheme.TextDim, TextAlignmentOptions.Center, UITextFx.Shadow, "Subtitle");
            _bannerSub.rectTransform.Stretch(0f, 98f, 0f, 16f);
            _bannerSub.characterSpacing = 4f;
            _bannerGroup.alpha = 0f;
            _banner.gameObject.SetActive(false);
        }

        /// <summary>Shows a toast for <paramref name="duration"/> seconds (unscaled). Rich text allowed.</summary>
        public void Show(string text, UIToastKind kind = UIToastKind.Info, float duration = 2.6f, Sprite icon = null)
        {
            while (_toasts.Count >= MaxToasts) Dismiss(_toasts[0], true);
            var panel = UIFactory.Panel(_toastRoot, UIPanelStyle.Glass, true, "Toast");
            var rt = panel.Rect;
            rt.anchorMin = rt.anchorMax = new Vector2(1f, 1f);
            rt.pivot = new Vector2(1f, 1f);
            rt.sizeDelta = new Vector2(ToastWidth, ToastHeight);
            panel.Background.raycastTarget = false;
            var accentColor = kind == UIToastKind.Good ? UITheme.Positive : kind == UIToastKind.Warning ? UITheme.Danger : UITheme.Gold;
            var accent = UIFactory.Image(rt, UISprites.GradientH, accentColor.WithAlpha(0.35f), "Accent");
            accent.rectTransform.Stretch(4f, 4f, ToastWidth * 0.55f, 4f);
            accent.rectTransform.localScale = new Vector3(-1f, 1f, 1f);
            float x;
            if (icon != null)
            {
                var ic = UIFactory.Icon(rt, icon, 40f);
                ic.rectTransform.Place(UIAnchor.Left, new Vector2(16f, 0f), new Vector2(40f, 40f));
                x = 66f;
            }
            else
            {
                var dot = UIFactory.Image(rt, UISprites.Diamond, accentColor, "Bullet");
                dot.rectTransform.Place(UIAnchor.Left, new Vector2(20f, 0f), new Vector2(16f, 16f));
                x = 46f;
            }
            var label = UIFactory.Label(rt, text, UITheme.SizeBody, UIFont.Bold, UITheme.Text, TextAlignmentOptions.MidlineLeft);
            label.rectTransform.Stretch(x, 0f, 18f, 0f);
            label.overflowMode = TextOverflowModes.Ellipsis;

            var e = new Entry { Rect = rt, Group = panel.gameObject.AddComponent<CanvasGroup>(), Expire = Time.unscaledTime + duration };
            e.Group.blocksRaycasts = false;
            _toasts.Add(e);
            Layout(e, true);
            UISound.Play(UISoundId.Notify);
        }

        /// <summary>Shows the centre ribbon banner; it slides in, holds for <paramref name="duration"/> and fades.</summary>
        public UITween Banner(string title, string subtitle = null, float duration = 2.2f)
        {
            _bannerTitle.text = title;
            _bannerSub.text = subtitle ?? "";
            _bannerSub.gameObject.SetActive(!string.IsNullOrEmpty(subtitle));
            _banner.gameObject.SetActive(true);
            UITween.Kill(_bannerGroup);
            UITween.Kill(_banner);
            UITween.Kill(_bannerTitle);
            _bannerTween?.Kill();
            UISound.Play(UISoundId.Notify);
            if (!Application.isPlaying)
            {
                _bannerGroup.alpha = 1f;
                return _bannerTween = UITween.To(this, 0f, null);
            }
            if (UIRoot.Instance != null && UIRoot.Instance.ReducedMotion)
            {
                _banner.localScale = Vector3.one;
                _bannerTitle.characterSpacing = 6f;
                _bannerGroup.alpha = 0f;
                UITween.Fade(_bannerGroup, 1f, 0.2f);
                return _bannerTween = UITween.Delay(this, duration).OnComplete(() =>
                    UITween.Fade(_bannerGroup, 0f, 0.25f).OnComplete(() => { if (_banner != null) _banner.gameObject.SetActive(false); }));
            }
            _bannerGroup.alpha = 0f;
            _banner.localScale = new Vector3(1.25f, 0.2f, 1f);
            _bannerTitle.characterSpacing = 40f;
            UITween.Fade(_bannerGroup, 1f, 0.25f);
            UITween.To(_banner, 0.4f, p => _banner.localScale = Vector3.LerpUnclamped(new Vector3(1.25f, 0.2f, 1f), Vector3.one, p), UIEase.OutBack);
            UITween.To(_bannerTitle, 0.6f, p => _bannerTitle.characterSpacing = Mathf.LerpUnclamped(40f, 6f, p), UIEase.OutQuint);
            return _bannerTween = UITween.Delay(this, 0.4f + duration).OnComplete(() =>
            {
                if (this == null) return;
                UITween.Fade(_bannerGroup, 0f, 0.35f);
                UITween.To(_banner, 0.35f, p => _banner.localScale = Vector3.LerpUnclamped(Vector3.one, new Vector3(1.08f, 0.6f, 1f), p), UIEase.InCubic)
                    .OnComplete(() => { if (_banner != null && _bannerGroup.alpha <= 0.01f) _banner.gameObject.SetActive(false); });
            });
        }

        void Update()
        {
            float now = Time.unscaledTime;
            for (int i = _toasts.Count - 1; i >= 0; i--)
                if (!_toasts[i].Leaving && now >= _toasts[i].Expire) Dismiss(_toasts[i], false);
        }

        void Dismiss(Entry e, bool instant)
        {
            _toasts.Remove(e);
            e.Leaving = true;
            if (instant || !Application.isPlaying)
            {
                if (Application.isPlaying) Destroy(e.Rect.gameObject); else DestroyImmediate(e.Rect.gameObject);
            }
            else
            {
                UITween.Kill(e.Rect);
                if (!(UIRoot.Instance != null && UIRoot.Instance.ReducedMotion))
                    UITween.Move(e.Rect, e.Rect.anchoredPosition + new Vector2(60f, 0f), 0.25f, UIEase.InCubic);
                UITween.Fade(e.Group, 0f, 0.25f).OnComplete(() => { if (e.Rect != null) Destroy(e.Rect.gameObject); });
            }
            for (int i = 0; i < _toasts.Count; i++) Layout(_toasts[i], false);
        }

        void Layout(Entry e, bool fresh)
        {
            int i = _toasts.IndexOf(e);
            var target = new Vector2(0f, -i * (ToastHeight + Gap));
            UITween.Kill(e.Rect);
            if (!Application.isPlaying || (UIRoot.Instance != null && UIRoot.Instance.ReducedMotion))
            {
                e.Rect.anchoredPosition = target;
                e.Group.alpha = 1f;
                return;
            }
            if (fresh)
            {
                e.Group.alpha = 0f;
                e.Rect.anchoredPosition = target + new Vector2(80f, 0f);
                UITween.Fade(e.Group, 1f, 0.2f);
            }
            UITween.Move(e.Rect, target, 0.3f, UIEase.OutBack);
        }
    }
}
