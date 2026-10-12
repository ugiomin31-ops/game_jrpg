using System;
using Abyss.Logic;
using TMPro;
using UnityEngine;
using UnityEngine.EventSystems;
using UnityEngine.UI;

namespace Abyss.UI
{
    /// <summary>
    /// Shears a graphic's quad horizontally by <c>(y - centre) * slope</c> so a plain rectangle becomes a 12 degree
    /// parallelogram without image assets. Optionally brightens the fill from left to right. Pointer hit-testing follows
    /// the sheared outline, so neighbouring plates in a diagonal stack never steal each other's taps.
    /// </summary>
    [AddComponentMenu(""), DisallowMultipleComponent, RequireComponent(typeof(Graphic))]
    public sealed class UISkew : BaseMeshEffect, ICanvasRaycastFilter
    {
        /// <summary>Plate slant in degrees (see the floor 1 polish brief: sheared 12 degrees).</summary>
        public const float Degrees = 12f;
        /// <summary>tan(12 degrees): horizontal shift per unit of height.</summary>
        public static readonly float Slope = Mathf.Tan(Degrees * Mathf.Deg2Rad);

        [SerializeField] float _slope = -1f;
        [SerializeField] bool _gradient;
        [SerializeField] Color _gradientTo = Color.white;

        float K => _slope < 0f ? Slope : _slope;

        /// <summary>Overrides the slope (0 = upright). Negative restores the default.</summary>
        public void SetSlope(float slope) { _slope = slope; Dirty(); }

        /// <summary>Multiplies the vertex colours towards <paramref name="to"/> from the left edge to the right edge.</summary>
        public void SetGradient(Color to) { _gradient = true; _gradientTo = to; Dirty(); }

        void Dirty() { if (graphic != null) graphic.SetVerticesDirty(); }

        /// <inheritdoc/>
        public override void ModifyMesh(VertexHelper vh)
        {
            if (!IsActive() || vh.currentVertCount == 0) return;
            Rect rect = graphic.rectTransform.rect;
            float cy = rect.center.y, k = K;
            UIVertex v = default;
            for (int i = 0; i < vh.currentVertCount; i++)
            {
                vh.PopulateUIVertex(ref v, i);
                Vector3 p = v.position;
                if (_gradient && rect.width > 0.01f)
                {
                    float t = Mathf.Clamp01((p.x - rect.xMin) / rect.width);
                    Color c = v.color;
                    Color e = new Color(c.r * _gradientTo.r, c.g * _gradientTo.g, c.b * _gradientTo.b, c.a * _gradientTo.a);
                    v.color = Color.Lerp(c, e, t);
                }
                p.x += (p.y - cy) * k;
                v.position = p;
                vh.SetUIVertex(v, i);
            }
        }

        /// <inheritdoc/>
        public bool IsRaycastLocationValid(Vector2 screenPoint, Camera eventCamera)
        {
            var rt = graphic.rectTransform;
            if (!RectTransformUtility.ScreenPointToLocalPointInRectangle(rt, screenPoint, eventCamera, out var local)) return false;
            Rect rect = rt.rect;
            local.x -= (local.y - rect.center.y) * K;
            return rect.Contains(local);
        }
    }

    /// <summary>
    /// A slanted plate: hard drop shadow (ink, offset 6 u), a thin edge and a navy fill. Colours are swapped per state;
    /// everything is the same white sprite sheared by <see cref="UISkew"/>.
    /// </summary>
    public sealed class UISlantPlate : MonoBehaviour
    {
        /// <summary>Hard shadow behind the plate (null when built without one).</summary>
        public Image Shadow { get; private set; }
        /// <summary>Edge colour layer.</summary>
        public Image Edge { get; private set; }
        /// <summary>Main fill.</summary>
        public Image Fill { get; private set; }
        /// <summary>The plate's RectTransform.</summary>
        public RectTransform Rect => (RectTransform)transform;

        /// <summary>Creates a plate under <paramref name="parent"/>; place it with <see cref="UIRect"/> helpers.</summary>
        public static UISlantPlate Create(Transform parent, string name, Color fill, Color edge, float edgeWidth = 2f,
            bool shadow = true, float shadowOffset = 6f, bool gradient = true)
        {
            var rt = UIFactory.Rect(parent, name);
            var plate = rt.gameObject.AddComponent<UISlantPlate>();
            plate.Build(fill, edge, edgeWidth, shadow, shadowOffset, gradient);
            return plate;
        }

        void Build(Color fill, Color edge, float edgeWidth, bool shadow, float shadowOffset, bool gradient)
        {
            var rt = Rect;
            if (shadow)
            {
                Shadow = Layer("Shadow", UISlant.ShadowColor);
                Shadow.rectTransform.anchorMin = Vector2.zero; Shadow.rectTransform.anchorMax = Vector2.one;
                Shadow.rectTransform.offsetMin = new Vector2(shadowOffset, -shadowOffset);
                Shadow.rectTransform.offsetMax = new Vector2(shadowOffset, -shadowOffset);
            }
            Fill = Layer("Fill", fill);
            Fill.rectTransform.Stretch();
            // The edge is a slim accent underline (one slanted strip), not an outline: clear unless the plate is focused/active.
            Edge = Layer("Accent", edge);
            Edge.rectTransform.anchorMin = Vector2.zero; Edge.rectTransform.anchorMax = new Vector2(1f, 0f);
            Edge.rectTransform.pivot = new Vector2(0.5f, 0f);
            Edge.rectTransform.sizeDelta = new Vector2(0f, Mathf.Max(3f, edgeWidth * 1.5f)); Edge.rectTransform.anchoredPosition = Vector2.zero;
            if (gradient) Fill.GetComponent<UISkew>().SetGradient(new Color(1.28f, 1.28f, 1.28f, 1f));
        }

        Image Layer(string name, Color color)
        {
            var img = UIFactory.Image(transform, UISprites.White, color, name);
            img.gameObject.AddComponent<UISkew>();
            return img;
        }

        /// <summary>Sets fill and edge colours.</summary>
        public void SetColors(Color fill, Color edge)
        {
            Fill.color = fill; Edge.color = edge;
        }

        /// <summary>Shows or hides the hard shadow.</summary>
        public void SetShadow(bool on) { if (Shadow != null) Shadow.enabled = on; }
    }

    /// <summary>
    /// Thin slanted value bar with a damage trail. Eases like <see cref="UIGauge"/> but is only two 4-vertex quads, so a
    /// dozen of them (tags and party plates) cost nothing.
    /// </summary>
    public sealed class UISlantBar : MonoBehaviour
    {
        Image _track, _trail, _fill;
        RectTransform _fillRt, _trailRt;
        UIGaugeKind _kind;
        Color _custom = UITheme.Gold;
        float _current, _max = 1f, _shown = 1f, _trailShown = 1f, _wait;
        bool _has;

        /// <summary>Current target value.</summary>
        public float Current => _current;
        /// <summary>Maximum value.</summary>
        public float Max => _max;
        /// <summary>Fill colour for <see cref="UIGaugeKind.Custom"/> and enemy bars.</summary>
        public Color FillColor { get => _custom; set { _custom = value; Paint(); } }

        /// <summary>Creates a bar of the given kind. <see cref="UIGaugeKind.Custom"/> uses <see cref="FillColor"/>.</summary>
        public static UISlantBar Create(Transform parent, UIGaugeKind kind, string name = "Bar")
        {
            var rt = UIFactory.Rect(parent, name);
            var bar = rt.gameObject.AddComponent<UISlantBar>();
            bar.Build(kind);
            return bar;
        }

        void Build(UIGaugeKind kind)
        {
            _kind = kind;
            _track = Layer("Track", new Color(0.03f, 0.07f, 0.1f, 0.86f));
            _track.rectTransform.Stretch();
            _trail = Layer("Trail", new Color(1f, 1f, 1f, 0.8f));
            _fill = Layer("Fill", UITheme.Gold);
            _trailRt = _trail.rectTransform; _fillRt = _fill.rectTransform;
            foreach (var r in new[] { _trailRt, _fillRt })
            {
                r.anchorMin = Vector2.zero; r.anchorMax = Vector2.one; r.offsetMin = r.offsetMax = Vector2.zero;
            }
            SetValue(1f, 1f, true);
        }

        Image Layer(string name, Color color)
        {
            var img = UIFactory.Image(transform, UISprites.White, color, name);
            img.gameObject.AddComponent<UISkew>();
            return img;
        }

        /// <summary>Sets the bar; animated in Play mode unless <paramref name="instant"/>.</summary>
        public void SetValue(float current, float max, bool instant = false)
        {
            max = Mathf.Max(0.0001f, max);
            current = Mathf.Clamp(current, 0f, max);
            float ratio = current / max, old = _has ? _current / _max : ratio;
            _current = current; _max = max; _has = true;
            if (instant || !Application.isPlaying) { _shown = _trailShown = ratio; _wait = 0f; }
            else if (ratio < old) { _trailShown = Mathf.Max(_trailShown, _shown); _wait = 0.4f; }
            else { _trailShown = Mathf.Max(_trailShown, ratio); }
            Paint();
        }

        void Update()
        {
            if (!_has) return;
            float dt = Time.unscaledDeltaTime, target = _current / _max;
            bool dirty = false;
            if (!Mathf.Approximately(_shown, target))
            {
                _shown = Mathf.MoveTowards(_shown, target, Mathf.Max(dt * 3.2f, dt * Mathf.Abs(_shown - target) * 9f));
                dirty = true;
            }
            if (_trailShown > _shown + 0.0005f)
            {
                if (_wait > 0f) _wait -= dt;
                else { _trailShown = Mathf.MoveTowards(_trailShown, _shown, dt * 0.9f); dirty = true; }
            }
            else if (!Mathf.Approximately(_trailShown, _shown)) { _trailShown = _shown; dirty = true; }
            if (dirty) Paint();
        }

        void Paint()
        {
            if (_fillRt == null) return;
            _fillRt.anchorMax = new Vector2(_shown, 1f);
            _trailRt.anchorMax = new Vector2(Mathf.Max(_trailShown, _shown), 1f);
            _fill.enabled = _shown > 0.001f;
            _trail.enabled = _trailShown > _shown + 0.001f;
            _fill.color = _kind switch
            {
                UIGaugeKind.Hp => UISlant.HpColor(_shown),
                UIGaugeKind.Mp => UISlant.Mp,
                UIGaugeKind.Tp => _shown >= 0.999f ? UITheme.GoldBright.WithAlpha(1f) : UITheme.Tp,
                _ => _custom,
            };
        }
    }

    /// <summary>Row styles of <see cref="UISlantButton"/>.</summary>
    public enum UISlantKind
    {
        /// <summary>Icon, heavy label and a one-line subline (battle commands).</summary>
        Command,
        /// <summary>Icon, name and cost on the first line; element chip and hint on the second (skills, items, targets).</summary>
        Skill,
        /// <summary>Centred label (auto, speed, manual).</summary>
        Simple,
        /// <summary>Plate-less corner hint (back, page arrows); a plate appears only while focused.</summary>
        Ghost,
    }

    /// <summary>
    /// Slanted plate button for the battle command fan. Mouse/touch via the EventSystem, keyboard/gamepad focus via
    /// <see cref="Focused"/> (the owner drives it). The focused plate turns coral and grows; clicks are debounced like
    /// <see cref="UIButton"/>.
    /// </summary>
    public sealed class UISlantButton : MonoBehaviour, IPointerEnterHandler, IPointerExitHandler, IPointerDownHandler, IPointerUpHandler, IPointerClickHandler
    {
        RectTransform _visual;
        UISlantPlate _plate;
        Image _hit, _chipBg;
        bool _interactable = true, _hover, _pressed, _focused;
        bool _ghost;
        float _nextClickAt, _focusScale = 1.1f, _homeX, _homeY, _pivotX = 0.5f, _subLeft;
        int _baseSibling = -1;
        UISlantKind _kind;
        Color _chipColor;

        /// <summary>Optional leading icon.</summary>
        public Image Icon { get; private set; }
        /// <summary>Main label.</summary>
        public TextMeshProUGUI Label { get; private set; }
        /// <summary>Second line (hint / description).</summary>
        public TextMeshProUGUI Sub { get; private set; }
        /// <summary>Right-aligned value (cost).</summary>
        public TextMeshProUGUI Right { get; private set; }
        /// <summary>Element chip text.</summary>
        public TextMeshProUGUI Chip { get; private set; }
        /// <summary>Why the plate is disabled (shown as a toast on click).</summary>
        public string DisabledReason { get; set; }
        /// <summary>Skips the confirm sound.</summary>
        public bool Quiet { get; set; }
        /// <summary>Raised on click while interactable.</summary>
        public event Action Clicked;
        /// <summary>Raised when the pointer enters.</summary>
        public event Action Hovered;
        /// <summary>The scaled child that holds the plate and content.</summary>
        public RectTransform Visual => _visual;
        /// <summary>The plate colour layers.</summary>
        public UISlantPlate Plate => _plate;

        static bool Reduced => UIRoot.Instance != null && UIRoot.Instance.ReducedMotion;

        /// <summary>Whether clicks are accepted.</summary>
        public bool Interactable
        {
            get => _interactable;
            set { if (_interactable == value) return; _interactable = value; ApplyState(false); }
        }

        /// <summary>Keyboard/gamepad (or hover) highlight.</summary>
        public bool Focused
        {
            get => _focused;
            set
            {
                if (_focused == value) return;
                _focused = value; ApplyState(false);
                if (_baseSibling >= 0 && transform.parent != null)
                    transform.SetSiblingIndex(value ? transform.parent.childCount - 1 : Mathf.Min(_baseSibling, transform.parent.childCount - 1));
            }
        }

        /// <summary>Sets the main label text.</summary>
        public void SetLabel(string text) => Label.text = text;

        /// <summary>Creates a slanted button of <paramref name="size"/>. <paramref name="big"/> picks the touch/compact type scale.</summary>
        public static UISlantButton Create(Transform parent, string name, Vector2 size, UISlantKind kind, bool big, Sprite icon = null, float hitExtraHeight = 0f)
        {
            var rt = UIFactory.Rect(parent, name);
            rt.sizeDelta = size;
            var button = rt.gameObject.AddComponent<UISlantButton>();
            button.Build(kind, size, big, icon, hitExtraHeight);
            return button;
        }

        void Build(UISlantKind kind, Vector2 size, bool big, Sprite icon, float hitExtraHeight)
        {
            _kind = kind;
            var rt = (RectTransform)transform;
            _hit = gameObject.AddComponent<Image>();
            _hit.color = Color.clear;
            _hit.raycastTarget = true;
            gameObject.AddComponent<UISkew>();
            // The painted plate is `size`; the touch target may be taller (extra hit area grows downwards).
            rt.sizeDelta = size + new Vector2(0f, hitExtraHeight);
            _visual = UIFactory.Rect(rt, "Visual");
            _visual.anchorMin = _visual.anchorMax = new Vector2(0.5f, 1f);
            // Stack plates grow towards the left (their right edge is the margin), simple buttons about the centre.
            _pivotX = kind == UISlantKind.Simple || kind == UISlantKind.Ghost ? 0.5f : 1f;
            _visual.pivot = new Vector2(_pivotX, 0.5f);
            _visual.sizeDelta = size;
            _homeX = size.x * (_pivotX - 0.5f); _homeY = -size.y * 0.5f;
            _visual.anchoredPosition = new Vector2(_homeX, _homeY);
            _plate = UISlantPlate.Create(_visual, "Plate", UISlant.Navy, UISlant.Rest, 2f, true, 5f, false);
            _plate.Rect.Stretch();
            float h = size.y;
            switch (kind)
            {
                case UISlantKind.Command:
                {
                    // One strong line: icon + heavy short label. The description lives in a single slim line under the stack.
                    float iconSize = Mathf.Min(h - 18f, big ? 46f : 42f);
                    Icon = UIFactory.Icon(_visual, icon, iconSize);
                    Icon.rectTransform.Place(UIAnchor.Left, new Vector2(30f, 0f), new Vector2(iconSize, iconSize));
                    Label = Text("Label", big ? 40f : 36f, UIFont.Heavy, UITextFx.Outline);
                    Label.rectTransform.Stretch(30f + iconSize + 18f, 0f, 24f, 0f);
                    Label.alignment = TextAlignmentOptions.MidlineLeft;
                    break;
                }
                case UISlantKind.Skill:
                {
                    float iconSize = Mathf.Min(h - 20f, big ? 44f : 40f);
                    Icon = UIFactory.Icon(_visual, icon, iconSize);
                    Icon.rectTransform.Place(UIAnchor.Left, new Vector2(28f, 0f), new Vector2(iconSize, iconSize));
                    float left = 28f + iconSize + 16f;
                    Right = Text("Cost", big ? 34f : 32f, UIFont.Heavy, UITextFx.Outline);
                    Right.rectTransform.Stretch(Mathf.Max(left, size.x - 240f), 0f, 26f, 0f);
                    Right.alignment = TextAlignmentOptions.MidlineRight;
                    Right.overflowMode = TextOverflowModes.Overflow;
                    Label = Text("Label", big ? 34f : 32f, UIFont.Heavy, UITextFx.Outline);
                    Label.rectTransform.Stretch(left, 0f, 260f, 0f);
                    Label.alignment = TextAlignmentOptions.MidlineLeft;
                    _chipBg = UIFactory.Image(_visual, UISprites.White, UISlant.Violet, "Chip");
                    _chipBg.gameObject.AddComponent<UISkew>();
                    _chipBg.rectTransform.anchorMin = _chipBg.rectTransform.anchorMax = new Vector2(1f, 0.5f);
                    _chipBg.rectTransform.pivot = new Vector2(1f, 0.5f);
                    _chipBg.rectTransform.sizeDelta = new Vector2(64f, 32f);
                    _chipBg.rectTransform.anchoredPosition = new Vector2(-190f, 0f);
                    Chip = Text("Chip text", 24f, UIFont.Bold, UITextFx.Shadow);
                    Chip.transform.SetParent(_chipBg.transform, false);
                    Chip.rectTransform.Stretch(0f, -6f, 0f, -6f);
                    Chip.alignment = TextAlignmentOptions.Center;
                    Chip.textWrappingMode = TextWrappingModes.NoWrap;
                    Chip.overflowMode = TextOverflowModes.Overflow;
                    break;
                }
                case UISlantKind.Ghost:
                {
                    // Text-only corner hint: no plate until focused. Touch targets keep their full height through hitExtraHeight.
                    Label = Text("Label", big ? 28f : 26f, UIFont.Bold, UITextFx.Outline);
                    Label.rectTransform.Stretch(8f, 0f, 8f, 0f);
                    Label.alignment = TextAlignmentOptions.Center;
                    Label.overflowMode = TextOverflowModes.Overflow;
                    _focusScale = 1.08f; _ghost = true;
                    _plate.SetShadow(false);
                    break;
                }
                default:
                {
                    Label = Text("Label", big ? 30f : 28f, UIFont.Heavy, UITextFx.Outline);
                    Label.rectTransform.Stretch(14f, 2f, 14f, 2f);
                    Label.alignment = TextAlignmentOptions.Center;
                    Label.enableAutoSizing = true;
                    Label.fontSizeMin = 24f; Label.fontSizeMax = big ? 30f : 28f;
                    if (icon != null)
                    {
                        Icon = UIFactory.Icon(_visual, icon, h - 20f);
                        Icon.rectTransform.Place(UIAnchor.Left, new Vector2(20f, 0f), new Vector2(h - 20f, h - 20f));
                    }
                    _focusScale = 1.05f;
                    break;
                }
            }
            if (Icon != null) Icon.enabled = icon != null;
            ApplyState(true);
        }

        TextMeshProUGUI Text(string name, float size, UIFont font, UITextFx fx)
        {
            var t = UIFactory.Label(_visual, "", size, font, UITheme.Text, TextAlignmentOptions.MidlineLeft, fx, name);
            t.overflowMode = TextOverflowModes.Ellipsis;
            return t;
        }

        /// <summary>Re-sizes the painted plate and the (possibly taller) touch target.</summary>
        public void Resize(Vector2 size, float hitExtraHeight)
        {
            ((RectTransform)transform).sizeDelta = size + new Vector2(0f, hitExtraHeight);
            _visual.sizeDelta = size;
            _homeX = size.x * (_pivotX - 0.5f); _homeY = -size.y * 0.5f;
            _visual.anchoredPosition = new Vector2(_homeX, _homeY);
        }

        /// <summary>Records the sibling index the plate returns to when it loses focus.</summary>
        public void RememberSibling() => _baseSibling = transform.GetSiblingIndex();

        /// <summary>Sets the element chip (hidden when <paramref name="text"/> is empty).</summary>
        public void SetChip(string text, Color color)
        {
            if (Chip == null) return;
            bool on = !string.IsNullOrEmpty(text);
            _chipBg.gameObject.SetActive(on);
            if (!on)
            {
                float cw = Right != null && !string.IsNullOrEmpty(Right.text) ? Right.GetPreferredValues(Right.text).x : 0f;
                Label.rectTransform.offsetMax = new Vector2(-(26f + cw + 16f), 0f);
                return;
            }
            _chipColor = color;
            Chip.text = text;
            float width = Mathf.Max(64f, Chip.GetPreferredValues(text).x + 26f);
            float costWidth = Right != null && !string.IsNullOrEmpty(Right.text) ? Right.GetPreferredValues(Right.text).x : 0f;
            _chipBg.rectTransform.sizeDelta = new Vector2(width, 32f);
            _chipBg.rectTransform.anchoredPosition = new Vector2(-(26f + costWidth + 14f), 0f);
            _chipBg.color = color;
            Label.rectTransform.offsetMax = new Vector2(-(26f + costWidth + 14f + width + 10f), 0f);
        }

        /// <summary>Activates the button as if clicked (flash, sound, event). Buzzer + shake when disabled.</summary>
        public void Click()
        {
            if (Time.unscaledTime < _nextClickAt) return;
            _nextClickAt = Time.unscaledTime + 0.25f;
            UIInput.Consume();
            if (!_interactable)
            {
                UISound.Play(UISoundId.Buzzer);
                if (!string.IsNullOrEmpty(DisabledReason)) UIRoot.Instance?.Toast.Show(DisabledReason, UIToastKind.Warning);
                Shake();
                return;
            }
            if (!Quiet) UISound.Play(UISoundId.Confirm);
            UITween.Kill(_visual);
            _visual.localScale = Vector3.one * (Reduced ? 1f : 0.97f);
            UITween.Scale(_visual, Reduced ? 1f : _focused ? _focusScale : 1f, Reduced ? 0f : 0.14f, UIEase.OutCubic);
            Clicked?.Invoke();
        }

        bool Highlighted => _hover || _focused;

        void ApplyState(bool instant)
        {
            if (_plate == null) return;
            Color fill, edge, text;
            if (!_interactable)
            {
                fill = new Color(0.1f, 0.12f, 0.15f, 0.85f); edge = UISlant.Rest; text = UITheme.TextDisabled;
            }
            else if (_pressed) { fill = UISlant.CoralDark; edge = UISlant.Rest; text = Color.white; }
            else if (Highlighted) { fill = UISlant.Coral; edge = UISlant.Rest; text = Color.white; }
            else { fill = UISlant.Navy; edge = UISlant.Rest; text = UITheme.Text; }
            if (_ghost) { fill = Highlighted && _interactable ? UISlant.Coral : new Color(0.03f, 0.06f, 0.1f, _interactable ? 0.72f : 0.4f); if (_interactable) text = Highlighted ? Color.white : UITheme.TextDim; }
            _plate.SetColors(fill, edge);
            Label.color = text;
            if (Sub != null) Sub.color = !_interactable ? UITheme.TextDisabled : Highlighted ? new Color(1f, 1f, 1f, 0.95f) : UITheme.TextDim;
            if (Right != null) Right.color = text;
            if (Icon != null) Icon.color = _interactable ? Color.white : new Color(0.45f, 0.45f, 0.5f, 0.8f);
            if (_chipBg != null && _chipBg.gameObject.activeSelf)
                _chipBg.color = Highlighted && _interactable ? new Color(0.1f, 0.05f, 0.1f, 0.78f) : _chipColor;
            float scale = Reduced ? 1f : _pressed && _interactable ? 0.97f : Highlighted && _interactable ? _focusScale : 1f;
            UITween.Kill(_visual);
            if (instant || !Application.isPlaying) { _visual.localScale = new Vector3(scale, scale, 1f); return; }
            UITween.Scale(_visual, scale, Reduced ? 0f : 0.12f, UIEase.OutCubic);
        }

        void Shake()
        {
            if (Reduced) return;
            UITween.Kill(_visual);
            UITween.To(_visual, 0.3f, p => _visual.anchoredPosition = new Vector2(_homeX + Mathf.Sin(p * Mathf.PI * 6f) * 8f * (1f - p), _homeY), UIEase.Linear);
        }

        void OnDisable()
        {
            _hover = _pressed = false;
            if (_visual != null) UITween.Kill(_visual);
        }

        /// <inheritdoc/>
        public void OnPointerEnter(PointerEventData e)
        {
            _hover = true;
            if (_interactable && !_focused) UISound.Play(UISoundId.Move);
            ApplyState(false);
            Hovered?.Invoke();
        }

        /// <inheritdoc/>
        public void OnPointerExit(PointerEventData e) { _hover = false; _pressed = false; ApplyState(false); }

        /// <inheritdoc/>
        public void OnPointerDown(PointerEventData e)
        {
            if (e.button != PointerEventData.InputButton.Left) return;
            _pressed = true; ApplyState(false);
        }

        /// <inheritdoc/>
        public void OnPointerUp(PointerEventData e) { _pressed = false; ApplyState(false); }

        /// <inheritdoc/>
        public void OnPointerClick(PointerEventData e)
        {
            if (e.button != PointerEventData.InputButton.Left) return;
            if (!UIInput.CanReceive(this)) return;
            Click();
        }
    }

    /// <summary>Palette and small factories shared by the slanted battle HUD.</summary>
    public static class UISlant
    {
        /// <summary>Signal coral: focus, selected target, critical, WEAK.</summary>
        public static readonly Color Coral = UITheme.Hex("ff4d6d");
        /// <summary>Resting accent: nothing drawn.</summary>
        public static readonly Color Rest = new Color(0f, 0f, 0f, 0f);
        /// <summary>Pressed coral.</summary>
        public static readonly Color CoralDark = UITheme.Hex("c93a58");
        /// <summary>Violet used for element chips and secondary plates.</summary>
        public static readonly Color Violet = UITheme.Hex("7b5cff");
        /// <summary>Plate fill (navy, slightly translucent).</summary>
        public static readonly Color Navy = new Color(0.045f, 0.08f, 0.12f, 1f);
        /// <summary>Hard drop shadow: ink at 70 %.</summary>
        public static readonly Color ShadowColor = new Color(0.031f, 0.075f, 0.106f, 0.7f);
        /// <summary>MP bar (violet-blue).</summary>
        public static readonly Color Mp = UITheme.Hex("6f8cff");
        /// <summary>Threat palette (enemy-turn banner only).</summary>
        public static readonly Color Threat = UITheme.Hex("ff3b4a");
        /// <summary>Threat plate fill (dark red).</summary>
        public static readonly Color ThreatFill = new Color(0.16f, 0.04f, 0.07f, 1f);

        /// <summary>Party HP: cyan, turning coral below half (the one critical accent).</summary>
        public static Color HpColor(float ratio)
        {
            ratio = Mathf.Clamp01(ratio);
            return ratio >= 0.5f ? UITheme.Gold : Color.Lerp(Coral, UITheme.Gold, Mathf.InverseLerp(0.2f, 0.5f, ratio));
        }

        /// <summary>Element chip colour.</summary>
        public static Color ElementColor(Element element)
        {
            switch (element)
            {
                case Element.Fire: return UITheme.Hex("c4472f");
                case Element.Ice: return UITheme.Hex("2a86b8");
                case Element.Thunder: return UITheme.Hex("b8921a");
                case Element.Dark: return UITheme.Hex("6a45c8");
                case Element.Holy: return UITheme.Hex("a88a3c");
                case Element.Slash: case Element.Blunt: case Element.Pierce: return UITheme.Hex("4b6d88");
                default: return UITheme.Hex("4a5a66");
            }
        }

        static Sprite _ring;

        /// <summary>Generated 128 px annulus (thickness 14 %) for radial TP rings; created once, never saved.</summary>
        public static Sprite Ring
        {
            get
            {
                if (_ring != null) return _ring;
                const int n = 128;
                var tex = new Texture2D(n, n, TextureFormat.RGBA32, false) { wrapMode = TextureWrapMode.Clamp, filterMode = FilterMode.Bilinear, hideFlags = HideFlags.HideAndDontSave };
                var pixels = new Color32[n * n];
                float c = (n - 1) * 0.5f, outer = n * 0.5f - 1f, inner = outer * 0.82f;
                for (int y = 0; y < n; y++)
                    for (int x = 0; x < n; x++)
                    {
                        float d = Mathf.Sqrt((x - c) * (x - c) + (y - c) * (y - c));
                        float a = Mathf.Clamp01(outer - d + 0.5f) * Mathf.Clamp01(d - inner + 0.5f);
                        pixels[y * n + x] = new Color32(255, 255, 255, (byte)Mathf.RoundToInt(a * 255f));
                    }
                tex.SetPixels32(pixels); tex.Apply(false, true);
                _ring = Sprite.Create(tex, new Rect(0, 0, n, n), new Vector2(0.5f, 0.5f), 100f);
                _ring.hideFlags = HideFlags.HideAndDontSave;
                return _ring;
            }
        }

        /// <summary>Circular face: a circle-masked sprite on a dark backdrop.</summary>
        public static Image CircleFace(Transform parent, float size, string name = "Face")
        {
            var rt = UIFactory.Rect(parent, name);
            rt.sizeDelta = new Vector2(size, size);
            var bg = rt.gameObject.AddComponent<Image>();
            bg.sprite = UISprites.Circle; bg.color = new Color(0.03f, 0.07f, 0.1f, 1f); bg.raycastTarget = false;
            rt.gameObject.AddComponent<Mask>().showMaskGraphic = true;
            var face = UIFactory.Image(rt, null, Color.white, "Sprite");
            face.rectTransform.Stretch();
            face.preserveAspect = true;
            face.enabled = false;
            return face;
        }

        /// <summary>Parallelogram face chip (turn order): sprite upright inside a sheared mask.</summary>
        public static Image SlantFace(Transform parent, Vector2 size, string name = "Face")
        {
            var rt = UIFactory.Rect(parent, name);
            rt.sizeDelta = size;
            var bg = rt.gameObject.AddComponent<Image>();
            bg.sprite = UISprites.White; bg.color = new Color(0.03f, 0.07f, 0.1f, 1f); bg.raycastTarget = false;
            rt.gameObject.AddComponent<UISkew>();
            rt.gameObject.AddComponent<Mask>().showMaskGraphic = true;
            var face = UIFactory.Image(rt, null, Color.white, "Sprite");
            face.rectTransform.Stretch(-6f, -2f, -6f, -2f);
            face.preserveAspect = true;
            face.enabled = false;
            return face;
        }

        /// <summary>Small slanted pill with one label (page indicator, damage estimate, WEAK badge).</summary>
        public static UISlantPlate Pill(Transform parent, string name, Color fill, Color edge, out TextMeshProUGUI label, float fontSize = 24f, UIFont font = UIFont.Heavy)
        {
            var plate = UISlantPlate.Create(parent, name, fill, edge, 2f, false, 0f, false);
            label = UIFactory.Label(plate.transform, "", fontSize, font, UITheme.Text, TextAlignmentOptions.Center, UITextFx.Outline, "Text");
            label.rectTransform.Stretch(8f, -5f, 8f, -5f);
            label.overflowMode = TextOverflowModes.Ellipsis;
            return plate;
        }
    }
}
