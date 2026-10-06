using System.Collections.Generic;
using TMPro;
using UnityEngine;
using UnityEngine.UI;

namespace Abyss.UI
{
    /// <summary>Gauge colour behaviour.</summary>
    public enum UIGaugeKind
    {
        /// <summary>Colour shifts red → yellow → green with the ratio.</summary>
        Hp,
        /// <summary>Blue.</summary>
        Mp,
        /// <summary>Gold; glows when full.</summary>
        Tp,
        /// <summary>Uses <see cref="UIGauge.FillColor"/>.</summary>
        Custom,
    }

    /// <summary>Where the gauge prints its label and value.</summary>
    public enum UIGaugeText
    {
        /// <summary>No text.</summary>
        None,
        /// <summary>Caption ("HP") left and value right, above the bar.</summary>
        Above,
        /// <summary>Value centred on the bar.</summary>
        Inline,
    }

    /// <summary>
    /// Animated bar: the fill eases to new values, damage leaves a red trail that drains after a short delay,
    /// heals show a bright preview ahead of the fill, and the number counts. Unscaled time; instant outside Play mode.
    /// Create with <see cref="UIFactory.Gauge"/>.
    /// </summary>
    public sealed class UIGauge : MonoBehaviour
    {
        const float FillSpeed = 2.4f;      // ratio per second when rising
        const float DropTime = 0.12f;      // fill snap on damage
        const float TrailDelay = 0.45f;
        const float TrailSpeed = 0.9f;
        const float CountTime = 0.35f;

        [SerializeField] UIGaugeKind _kind;
        [SerializeField] RectTransform _fillRect, _trailRect;
        [SerializeField] Image _fill, _trail, _glow;
        [SerializeField] TextMeshProUGUI _caption, _value;
        float _current, _max = 1f;
        float _shownRatio, _trailRatio, _shownNumber;
        float _trailWait, _countFrom, _countT = 1f;
        bool _hasValue, _draining;
        Color _custom = Color.white;

        /// <summary>Caption text component ("HP"/"MP"/"TP"); null when text is None/Inline.</summary>
        public TextMeshProUGUI Caption => _caption;
        /// <summary>Value text component; null when text is None.</summary>
        public TextMeshProUGUI ValueText => _value;
        /// <summary>Current target value.</summary>
        public float Current => _current;
        /// <summary>Maximum value.</summary>
        public float Max => _max;
        /// <summary>Show "cur/max" (true) or just "cur" (false).</summary>
        public bool ShowMax { get; set; } = true;
        /// <summary>Show the value as a percentage instead (TP).</summary>
        public bool ShowPercent { get; set; }

        /// <summary>Fill colour for <see cref="UIGaugeKind.Custom"/>.</summary>
        public Color FillColor
        {
            get => _custom;
            set { _custom = value; Render(); }
        }

        internal void Build(UIGaugeKind kind, float width, float height, UIGaugeText text)
        {
            _kind = kind;
            var rt = (RectTransform)transform;
            rt.sizeDelta = new Vector2(width, height);

            _glow = UIFactory.Image(rt, UISprites.FocusGlow, new Color(1f, 0.8f, 0.3f, 0f), "Glow");
            _glow.rectTransform.Outset(20f);
            var frame = UIFactory.Image(rt, UISprites.BarFrame, Color.white, "Frame");
            frame.rectTransform.Stretch();
            var area = UIFactory.Rect(rt, "Area").Stretch(2.5f, 2.5f, 2.5f, 2.5f);
            area.gameObject.AddComponent<RectMask2D>();
            _trail = UIFactory.Image(area, UISprites.BarFlat, UITheme.Trail, "Trail");
            _trailRect = _trail.rectTransform;
            _fill = UIFactory.Image(area, UISprites.BarFill, Color.white, "Fill");
            _fillRect = _fill.rectTransform;
            foreach (var r in new[] { _trailRect, _fillRect })
            {
                r.anchorMin = Vector2.zero;
                r.anchorMax = new Vector2(1f, 1f);
                r.offsetMin = r.offsetMax = Vector2.zero;
            }
            if (height < 12f) _fill.pixelsPerUnitMultiplier = _trail.pixelsPerUnitMultiplier = 12f / height;

            string cap = kind == UIGaugeKind.Hp ? "HP" : kind == UIGaugeKind.Mp ? "MP" : kind == UIGaugeKind.Tp ? "TP" : "";
            if (text == UIGaugeText.Above)
            {
                _caption = UIFactory.Label(rt, cap, UITheme.SizeCaption, UIFont.Heavy, UITheme.Gold, TextAlignmentOptions.BottomLeft, UITextFx.Outline, "Caption");
                _caption.rectTransform.Place(UIAnchor.TopLeft, Vector2.zero, new Vector2(2f, 1f), new Vector2(60f, 30f));
                _value = UIFactory.Label(rt, "", UITheme.SizeLabel, UIFont.Heavy, UITheme.Text, TextAlignmentOptions.BottomRight, UITextFx.Outline, "Value");
                _value.rectTransform.anchorMin = new Vector2(0f, 1f);
                _value.rectTransform.anchorMax = new Vector2(1f, 1f);
                _value.rectTransform.pivot = new Vector2(1f, 0f);
                _value.rectTransform.offsetMin = new Vector2(30f, -2f);
                _value.rectTransform.offsetMax = new Vector2(-2f, 32f);
            }
            else if (text == UIGaugeText.Inline)
            {
                _value = UIFactory.Label(rt, "", Mathf.Clamp(height * 0.95f, 14f, UITheme.SizeLabel), UIFont.Heavy, UITheme.Text, TextAlignmentOptions.Center, UITextFx.Outline, "Value");
                _value.rectTransform.Stretch(0f, -6f, 0f, -6f);
            }
            SetValue(1f, 1f, true);
        }

        /// <summary>Sets the gauge. Animated in Play mode unless <paramref name="instant"/>.</summary>
        public void SetValue(float current, float max, bool instant = false)
        {
            max = Mathf.Max(0.0001f, max);
            current = Mathf.Clamp(current, 0f, max);
            float ratio = current / max;
            float old = _hasValue ? _current / _max : ratio;
            _countFrom = _hasValue ? _shownNumber : current;
            _current = current;
            _max = max;
            _hasValue = true;
            _countT = 0f;
            if (instant || !Application.isPlaying)
            {
                _shownRatio = _trailRatio = ratio;
                _shownNumber = current;
                _countT = 1f;
                _draining = false;
            }
            else if (ratio < old)
            {
                _trailRatio = Mathf.Max(_trailRatio, _shownRatio);
                _trailWait = TrailDelay;
                _draining = true;
                _trail.color = UITheme.Trail;
            }
            else if (ratio > old)
            {
                _trailRatio = ratio;
                _draining = false;
                _trail.color = UITheme.HealTrail;
            }
            Render();
        }

        void Update()
        {
            if (!_hasValue) return;
            float dt = Time.unscaledDeltaTime;
            float target = _current / _max;
            bool dirty = false;
            if (!Mathf.Approximately(_shownRatio, target))
            {
                _shownRatio = target < _shownRatio
                    ? Mathf.MoveTowards(_shownRatio, target, Mathf.Max(dt / DropTime * (_shownRatio - target), dt * 0.5f))
                    : Mathf.MoveTowards(_shownRatio, target, dt * FillSpeed * Mathf.Max(0.25f, target - _shownRatio + 0.2f));
                dirty = true;
            }
            if (_draining)
            {
                if (_trailRatio <= _shownRatio) _draining = false;
                else if (_trailWait > 0f) _trailWait -= dt;
                else { _trailRatio = Mathf.MoveTowards(_trailRatio, _shownRatio, dt * TrailSpeed); dirty = true; }
            }
            else if (!Mathf.Approximately(_trailRatio, target))
            {
                _trailRatio = target;
                dirty = true;
            }
            if (_countT < 1f)
            {
                _countT = Mathf.Min(1f, _countT + dt / CountTime);
                _shownNumber = Mathf.Lerp(_countFrom, _current, UITween.Evaluate(UIEase.OutCubic, _countT));
                dirty = true;
            }
            if (_kind == UIGaugeKind.Tp && _shownRatio >= 0.999f)
            {
                var c = _glow.color;
                c.a = UIRoot.Instance != null && UIRoot.Instance.ReducedMotion ? 0.7f : 0.55f + 0.35f * Mathf.Sin(Time.unscaledTime * 5f);
                _glow.color = c;
            }
            if (dirty) Render();
        }

        void Render()
        {
            if (_fillRect == null) return;
            _fillRect.anchorMax = new Vector2(_shownRatio, 1f);
            _trailRect.anchorMax = new Vector2(Mathf.Max(_trailRatio, _shownRatio), 1f);
            _fill.enabled = _shownRatio > 0.001f;
            _trail.enabled = _trailRatio > _shownRatio + 0.001f;
            float ratio = _current / _max;
            _fill.color = _kind switch
            {
                UIGaugeKind.Hp => UITheme.HpColor(_shownRatio),
                UIGaugeKind.Mp => UITheme.Mp,
                UIGaugeKind.Tp => _shownRatio >= 0.999f ? UITheme.GoldBright : UITheme.Tp,
                _ => _custom,
            };
            if (_kind != UIGaugeKind.Tp || _shownRatio < 0.999f) _glow.color = new Color(1f, 0.8f, 0.3f, 0f);
            else if (!Application.isPlaying) _glow.color = new Color(1f, 0.8f, 0.3f, 0.8f);
            if (_value == null) return;
            int shown = Mathf.RoundToInt(_shownNumber);
            if (ShowPercent) _value.text = Mathf.RoundToInt(_shownNumber / _max * 100f) + "<size=70%>%</size>";
            else if (ShowMax) _value.text = shown + "<size=62%><color=#aab3d6>/" + Mathf.RoundToInt(_max) + "</color></size>";
            else _value.text = shown.ToString();
            _value.color = _kind == UIGaugeKind.Hp && ratio <= 0.25f ? UITheme.Danger : UITheme.Text;
        }
    }

    /// <summary>Row of diamond pips (enemy shields / break counters). Create with <see cref="UIFactory.Pips"/>.</summary>
    public sealed class UIPips : MonoBehaviour
    {
        [SerializeField] List<Image> _pips = new List<Image>();
        [SerializeField] float _size;
        int _current = -1;

        /// <summary>Filled pip count.</summary>
        public int Current => _current;

        internal void Build(int max, float size)
        {
            _size = size;
            var h = gameObject.AddComponent<HorizontalLayoutGroup>();
            h.spacing = -size * 0.18f;
            h.childAlignment = TextAnchor.MiddleLeft;
            h.childControlWidth = h.childControlHeight = false;
            h.childForceExpandWidth = h.childForceExpandHeight = false;
            Set(max, max);
        }

        /// <summary>Sets filled/maximum pips; losing pips pops them with a flash in Play mode.</summary>
        public void Set(int current, int max)
        {
            max = Mathf.Max(0, max);
            current = Mathf.Clamp(current, 0, max);
            while (_pips.Count < max)
            {
                var img = UIFactory.Image(transform, UISprites.PipOn, Color.white, "Pip");
                img.rectTransform.sizeDelta = new Vector2(_size, _size);
                _pips.Add(img);
            }
            for (int i = 0; i < _pips.Count; i++)
            {
                var p = _pips[i];
                p.gameObject.SetActive(i < max);
                bool on = i < current;
                bool lost = _current >= 0 && !on && i < _current;
                p.sprite = on ? UISprites.PipOn : UISprites.PipOff;
                if (lost && Application.isPlaying && !(UIRoot.Instance != null && UIRoot.Instance.ReducedMotion))
                {
                    p.transform.localScale = Vector3.one * 1.6f;
                    p.color = new Color(1f, 0.9f, 0.6f, 1f);
                    UITween.Scale(p.transform, 1f, 0.3f, UIEase.OutBack);
                    UITween.Color(p, Color.white, 0.3f);
                }
            }
            _current = current;
        }
    }
}
