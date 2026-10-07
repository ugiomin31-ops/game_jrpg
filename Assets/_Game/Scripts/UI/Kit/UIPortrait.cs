using UnityEngine;
using UnityEngine.UI;

namespace Abyss.UI
{
    /// <summary>
    /// Circular portrait with a quiet slate rim. Feed it a texture (render texture / illustration) or sprite;
    /// supports an "active turn" halo, hit flash and shake. Create with <see cref="UIFactory.Portrait"/>.
    /// </summary>
    public sealed class UIPortrait : MonoBehaviour
    {
        [SerializeField] RectTransform _body;
        [SerializeField] Image _halo, _flash, _sprite;
        [SerializeField] RawImage _raw;
        bool _active;

        /// <summary>Masked RawImage slot (render textures, illustrations).</summary>
        public RawImage Raw => _raw;
        /// <summary>Masked sprite slot (used by <see cref="SetSprite"/>).</summary>
        public Image SpriteImage => _sprite;

        internal void Build(float size)
        {
            var rt = (RectTransform)transform;
            rt.sizeDelta = new Vector2(size, size);
            _halo = UIFactory.Image(rt, UISprites.SoftRadial, UITheme.Dawn.WithAlpha(0f), "Halo");
            _halo.rectTransform.Outset(size * 0.32f);
            _body = UIFactory.Rect(rt, "Body").Stretch();
            var bg = UIFactory.Image(_body, UISprites.Circle, UITheme.Border, "Backdrop");
            bg.rectTransform.Stretch();
            var mask = UIFactory.Image(_body, UISprites.PortraitMask, Color.white, "Mask");
            mask.rectTransform.Stretch(3, 3, 3, 3);
            mask.gameObject.AddComponent<Mask>().showMaskGraphic = false;
            _raw = UIFactory.RawImage(mask.transform, null, "Raw");
            _raw.rectTransform.Stretch();
            _raw.enabled = false;
            _sprite = UIFactory.Image(mask.transform, null, Color.white, "Sprite");
            _sprite.rectTransform.Stretch();
            _sprite.preserveAspect = true;
            _sprite.enabled = false;
            _flash = UIFactory.Image(mask.transform, UISprites.White, new Color(1f, 1f, 1f, 0f), "Flash");
            _flash.rectTransform.Stretch();
        }

        /// <summary>Shows a texture (null hides it). <paramref name="uv"/> crops it (defaults to the full texture).</summary>
        public void SetTexture(Texture texture, Rect? uv = null)
        {
            _raw.texture = texture;
            _raw.uvRect = uv ?? new Rect(0f, 0f, 1f, 1f);
            _raw.enabled = texture != null;
            if (texture != null) _sprite.enabled = false;
        }

        /// <summary>Shows a sprite (null hides it).</summary>
        public void SetSprite(Sprite sprite)
        {
            _sprite.sprite = sprite;
            _sprite.enabled = sprite != null;
            if (sprite != null) _raw.enabled = false;
        }

        /// <summary>Warm halo marking the acting character (pulses in Play mode).</summary>
        public bool ActiveTurn
        {
            get => _active;
            set
            {
                _active = value;
                UITween.Kill(_halo);
                _halo.color = UITheme.Dawn.WithAlpha(value ? 0.75f : 0f);
            }
        }

        /// <summary>Brief colour flash over the face (hit = red, heal = green).</summary>
        public void Flash(Color color, float duration = 0.35f)
        {
            UITween.Kill(_flash);
            if (UIRoot.Instance != null && UIRoot.Instance.ReducedMotion) { _flash.color = color.WithAlpha(0f); return; }
            _flash.color = color.WithAlpha(0.75f);
            UITween.Fade(_flash, 0f, duration, UIEase.OutQuad);
        }

        /// <summary>Horizontal hit shake.</summary>
        public void Shake(float strength = 10f, float duration = 0.35f)
        {
            UITween.Kill(_body);
            if (UIRoot.Instance != null && UIRoot.Instance.ReducedMotion) { _body.anchoredPosition = Vector2.zero; return; }
            UITween.To(_body, duration, p => _body.anchoredPosition = new Vector2(Mathf.Sin(p * Mathf.PI * 7f) * strength * (1f - p), 0f), UIEase.Linear)
                .OnComplete(() => _body.anchoredPosition = Vector2.zero);
        }

        void Update()
        {
            if (!_active) return;
            float a = UIRoot.Instance != null && UIRoot.Instance.ReducedMotion ? 0.75f : 0.55f + 0.3f * Mathf.Sin(Time.unscaledTime * 4f);
            _halo.color = UITheme.Dawn.WithAlpha(a);
        }
    }
}
