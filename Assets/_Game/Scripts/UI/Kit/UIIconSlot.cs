using System;
using TMPro;
using UnityEngine;
using UnityEngine.EventSystems;
using UnityEngine.UI;

namespace Abyss.UI
{
    /// <summary>
    /// Recessed square slot holding an icon with an optional count badge and selection glow
    /// (inventory, equipment, skill bars). Create with <see cref="UIFactory.IconSlot"/>.
    /// </summary>
    public sealed class UIIconSlot : MonoBehaviour, IPointerEnterHandler, IPointerExitHandler, IPointerClickHandler
    {
        [SerializeField] Image _frame, _icon, _glow;
        [SerializeField] TextMeshProUGUI _count;
        bool _selected, _hover;

        /// <summary>Raised on left click.</summary>
        public event Action Clicked;
        /// <summary>Raised when the pointer enters (tooltips / focus sync).</summary>
        public event Action Hovered;
        /// <summary>Raised when the pointer leaves.</summary>
        public event Action Unhovered;

        /// <summary>The icon image.</summary>
        public Image IconImage => _icon;

        internal void Build(float size)
        {
            var rt = (RectTransform)transform;
            rt.sizeDelta = new Vector2(size, size);
            _glow = UIFactory.Image(rt, UISprites.FocusGlow, new Color(1f, 1f, 1f, 0f), "Glow");
            _glow.rectTransform.Outset(20f);
            _frame = UIFactory.Image(rt, UISprites.Slot, Color.white, "Frame", raycast: true, borderScale: size < 70f ? 1.5f : 1f);
            _frame.rectTransform.Stretch();
            _icon = UIFactory.Image(rt, null, Color.white, "Icon");
            _icon.rectTransform.Stretch(size * 0.12f, size * 0.12f, size * 0.12f, size * 0.12f);
            _icon.preserveAspect = true;
            _count = UIFactory.Label(rt, "", Mathf.Max(16f, size * 0.24f), UIFont.Heavy, UITheme.Text, TextAlignmentOptions.BottomRight, UITextFx.Outline, "Count");
            _count.rectTransform.Stretch(4f, 4f, 7f, 3f);
        }

        /// <summary>Sets the icon (null = empty slot).</summary>
        public void SetIcon(Sprite sprite)
        {
            _icon.sprite = sprite;
            _icon.enabled = sprite != null;
        }

        /// <summary>Sets the count badge (hidden when &lt;= 1).</summary>
        public void SetCount(int count) => _count.text = count > 1 ? "×" + count : "";

        /// <summary>Greys the icon out (e.g. unusable item).</summary>
        public bool Dimmed
        {
            set => _icon.color = value ? new Color(0.5f, 0.5f, 0.55f, 0.6f) : Color.white;
        }

        /// <summary>Dawn selection glow (keyboard/gamepad cursor).</summary>
        public bool Selected
        {
            get => _selected;
            set { _selected = value; Refresh(); }
        }

        void Refresh()
        {
            float a = _selected ? 1f : _hover ? 0.55f : 0f;
            UITween.Kill(_glow);
            if (Application.isPlaying) UITween.Fade(_glow, a, 0.15f);
            else _glow.color = new Color(1f, 1f, 1f, a);
        }

        /// <inheritdoc/>
        public void OnPointerEnter(PointerEventData e) { _hover = true; Refresh(); Hovered?.Invoke(); }

        /// <inheritdoc/>
        public void OnPointerExit(PointerEventData e) { _hover = false; Refresh(); Unhovered?.Invoke(); }

        /// <inheritdoc/>
        public void OnPointerClick(PointerEventData e)
        {
            if (e.button == PointerEventData.InputButton.Left && UIInput.CanReceive(this)) Clicked?.Invoke();
        }
    }

    /// <summary>Key-cap hint "[Z] 결정" that swaps glyphs when the player switches device. Create with <see cref="UIFactory.KeyHint"/>.</summary>
    public sealed class UIKeyHint : MonoBehaviour
    {
        [SerializeField] UIAction _action;
        [SerializeField] TextMeshProUGUI _glyph, _label;
        [SerializeField] LayoutElement _capLayout;

        internal void Build(UIAction action, string label)
        {
            _action = action;
            ((RectTransform)transform).sizeDelta = new Vector2(120f, 36f);
            var h = gameObject.AddComponent<HorizontalLayoutGroup>();
            h.spacing = 8f;
            h.childAlignment = TextAnchor.MiddleLeft;
            h.childControlWidth = h.childControlHeight = true;
            h.childForceExpandWidth = h.childForceExpandHeight = false;
            gameObject.AddComponent<ContentSizeFitter>().horizontalFit = ContentSizeFitter.FitMode.PreferredSize;
            var cap = UIFactory.Image(transform, UISprites.KeyCap, Color.white, "Cap", borderScale: 1.4f);
            _capLayout = UIFactory.Layout(cap, 36f, 34f);
            _glyph = UIFactory.Label(cap.transform, "", 18f, UIFont.Heavy, UITheme.Ink, TextAlignmentOptions.Center, UITextFx.Plain, "Glyph");
            _glyph.rectTransform.Stretch(0f, 0f, 0f, 3f);
            _label = UIFactory.Label(transform, "", UITheme.SizeCaption + 2f, UIFont.Bold, UITheme.TextDim, TextAlignmentOptions.MidlineLeft, UITextFx.Shadow, "Text");
            SetLabel(label);
            Refresh(UIInput.Device);
        }

        /// <summary>Changes the caption (empty hides it, leaving just the key cap).</summary>
        public void SetLabel(string label)
        {
            _label.text = label;
            _label.gameObject.SetActive(!string.IsNullOrEmpty(label));
        }

        void OnEnable() => UIInput.DeviceChanged += Refresh;
        void OnDisable() => UIInput.DeviceChanged -= Refresh;

        void Refresh(UIInputDevice _)
        {
            if (_glyph == null) return;
            string g = UIInput.Glyph(_action);
            _glyph.text = g;
            _capLayout.gameObject.SetActive(g.Length > 0);
            _capLayout.preferredWidth = Mathf.Max(36f, 18f + g.Length * 11f);
        }
    }
}
