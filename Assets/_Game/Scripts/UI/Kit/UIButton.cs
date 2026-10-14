using System;
using System.Collections.Generic;
using TMPro;
using UnityEngine;
using UnityEngine.EventSystems;
using UnityEngine.UI;

namespace Abyss.UI
{
    /// <summary>
    /// Framed button with hover/focus glow, press squash (0.96) and sounds. Mouse is handled through the
    /// EventSystem; keyboard/gamepad focus is driven by an owner (see <see cref="UIButtonGroup"/>) via <see cref="Focused"/>.
    /// Create with <see cref="UIFactory.Button"/>.
    /// </summary>
    public sealed class UIButton : MonoBehaviour, IPointerEnterHandler, IPointerExitHandler, IPointerDownHandler, IPointerUpHandler, IPointerClickHandler
    {
        [SerializeField] RectTransform _visual;
        [SerializeField] Image _background;
        [SerializeField] Image _glow;
        [SerializeField] TextMeshProUGUI _label;
        [SerializeField] Image _icon;
        [SerializeField] bool _interactable = true;
        bool _hover, _pressed, _focused, _repeated;
        float _repeatAt, _nextClickAt;
        internal string DisabledReason { get; set; }

        /// <summary>Seconds between repeated clicks while a pointer or finger is held on the button (0 = off).
        /// The first repeat waits <see cref="UIInput.RepeatDelay"/>; a release after repeats does not click again.</summary>
        public float HoldRepeat { get; set; }

        /// <summary>Skips the confirm sound (buttons whose action plays its own sound, such as movement).</summary>
        public bool Quiet { get; set; }
        bool ReducedMotion => UIRoot.Instance != null && UIRoot.Instance.ReducedMotion;

        /// <summary>Raised on click / submit while interactable.</summary>
        public event Action Clicked;
        /// <summary>Raised when the pointer enters (owners sync keyboard focus to the mouse).</summary>
        public event Action Hovered;

        /// <summary>Label text component.</summary>
        public TextMeshProUGUI Label => _label;
        /// <summary>Optional leading icon (disabled when no sprite).</summary>
        public Image Icon => _icon;
        /// <summary>Background image (sprite swapped per state).</summary>
        public Image Background => _background;

        /// <summary>Whether the button reacts to clicks (disabled look otherwise).</summary>
        public bool Interactable
        {
            get => _interactable;
            set { if (_interactable == value) return; _interactable = value; ApplyState(false); }
        }

        /// <summary>Keyboard/gamepad focus highlight (same look as hover).</summary>
        public bool Focused
        {
            get => _focused;
            set { if (_focused == value) return; _focused = value; ApplyState(false); }
        }

        /// <summary>Sets the label text.</summary>
        public void SetLabel(string text) => _label.text = text;

        internal void Build(string label, Sprite icon)
        {
            var rt = (RectTransform)transform;
            rt.sizeDelta = new Vector2(260f, 64f);
            var hit = gameObject.AddComponent<Image>();
            hit.color = Color.clear;
            _visual = UIFactory.Rect(rt, "Visual").Stretch();
            _glow = UIFactory.Image(_visual, UISprites.FocusGlow, new Color(1f, 1f, 1f, 0f), "Glow");
            _glow.rectTransform.Outset(22f);
            _background = UIFactory.Image(_visual, UISprites.ButtonNormal, Color.white, "Background");
            _background.rectTransform.Stretch();
            var row = UIFactory.HStack(_visual, 10f, null, TextAnchor.MiddleCenter, "Content");
            row.Rt().Stretch(18f, 4f, 18f, 4f);
            _icon = UIFactory.Icon(row.transform, icon, 34f);
            UIFactory.Layout(_icon, 34f, 34f);
            _icon.gameObject.SetActive(icon != null);
            _label = UIFactory.Label(row.transform, label, UITheme.SizeLabel, UIFont.Bold, UITheme.Text, TextAlignmentOptions.Center);
            _label.enableAutoSizing = true;
            _label.fontSizeMin = 19f;
            _label.fontSizeMax = UITheme.SizeLabel;
            _label.overflowMode = TextOverflowModes.Ellipsis;
            UIFactory.Layout(_label, flexibleWidth: 1f);
            ApplyState(true);
        }

        /// <summary>Tall (thumb-sized) buttons get proportionally larger labels: 40 % of the height, 28–38 pt.</summary>
        void OnRectTransformDimensionsChange()
        {
            if (_label == null) return;
            float h = ((RectTransform)transform).rect.height;
            _label.fontSizeMax = Mathf.Clamp(h * 0.4f, UITheme.SizeLabel, 38f);
        }

        /// <summary>Activates the button as if clicked (press bounce, sound, event). Plays a buzzer when not interactable.</summary>
        public void Click()
        {
            // A quick double tap must not buy, equip or confirm twice; held movement buttons keep repeating.
            if (HoldRepeat <= 0f && Time.unscaledTime < _nextClickAt) return;
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
            _visual.localScale = Vector3.one * (ReducedMotion ? 1f : 0.97f);
            UITween.Scale(_visual, ReducedMotion ? 1f : Highlighted ? 1.015f : 1f, ReducedMotion ? 0f : 0.16f, UIEase.OutCubic);
            Clicked?.Invoke();
        }

        bool Highlighted => _hover || _focused;

        void ApplyState(bool instant)
        {
            if (_background == null) return;
            _background.sprite = !_interactable ? UISprites.ButtonDisabled
                : _pressed ? UISprites.ButtonPressed
                : Highlighted ? UISprites.ButtonHover : UISprites.ButtonNormal;
            _label.color = !_interactable ? UITheme.TextDisabled : Highlighted ? UITheme.DawnBright : UITheme.Text;
            if (_icon != null) _icon.color = _interactable ? Color.white : new Color(0.45f, 0.45f, 0.5f, 0.8f);
            float scale = ReducedMotion ? 1f : _pressed && _interactable ? 0.97f : Highlighted ? 1.015f : 1f;
            float glow = Highlighted ? 1f : 0f;
            UITween.Kill(_visual);
            UITween.Kill(_glow);
            if (instant || !Application.isPlaying)
            {
                _visual.localScale = new Vector3(scale, scale, 1f);
                _glow.color = new Color(1f, 1f, 1f, glow);
                return;
            }
            UITween.Scale(_visual, scale, ReducedMotion ? 0f : _pressed ? 0.06f : 0.14f, UIEase.OutCubic);
            UITween.Fade(_glow, glow, 0.18f);
        }

        void Shake()
        {
            if (ReducedMotion) return;
            UITween.Kill(_visual);
            UITween.To(_visual, 0.3f, p => _visual.anchoredPosition = new Vector2(Mathf.Sin(p * Mathf.PI * 6f) * 8f * (1f - p), 0f), UIEase.Linear);
        }

        void OnDisable()
        {
            _hover = _pressed = false;
            if (_visual != null)
            {
                UITween.Kill(_visual);
                _visual.anchoredPosition = Vector2.zero;
            }
            ApplyState(true);
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
        public void OnPointerExit(PointerEventData e)
        {
            _hover = false;
            _pressed = false;
            ApplyState(false);
        }

        /// <inheritdoc/>
        public void OnPointerDown(PointerEventData e)
        {
            if (e.button != PointerEventData.InputButton.Left) return;
            _pressed = true;
            _repeated = false;
            _repeatAt = Time.unscaledTime + Mathf.Max(HoldRepeat, UIInput.RepeatDelay);
            ApplyState(false);
        }

        void Update()
        {
            if (HoldRepeat <= 0f || !_pressed || !_interactable || Time.unscaledTime < _repeatAt) return;
            _repeatAt = Time.unscaledTime + HoldRepeat;
            if (!UIInput.CanReceive(this)) return;
            _repeated = true;
            Click();
        }

        /// <inheritdoc/>
        public void OnPointerUp(PointerEventData e)
        {
            _pressed = false;
            ApplyState(false);
        }

        /// <inheritdoc/>
        public void OnPointerClick(PointerEventData e)
        {
            if (e.button != PointerEventData.InputButton.Left) return;
            if (_repeated) { _repeated = false; return; }
            if (!UIInput.CanReceive(this)) return;
            Click();
        }
    }

    /// <summary>
    /// Keyboard/gamepad navigation across a row or column of <see cref="UIButton"/>s (layout included).
    /// Arrows move focus (wrapping), Confirm clicks the focused button; mouse hover moves focus.
    /// </summary>
    public sealed class UIButtonGroup : MonoBehaviour
    {
        readonly List<UIButton> _buttons = new List<UIButton>();
        [SerializeField] bool _horizontal;
        int _index;

        /// <summary>When false the group ignores keyboard/gamepad input (mouse still works).</summary>
        public bool InputEnabled { get; set; } = true;

        /// <summary>Buttons in navigation order.</summary>
        public IReadOnlyList<UIButton> Buttons => _buttons;

        /// <summary>Index of the focused button.</summary>
        public int FocusIndex
        {
            get => _index;
            set => SetFocus(value, false);
        }

        internal void Build(bool horizontal, float spacing)
        {
            _horizontal = horizontal;
            HorizontalOrVerticalLayoutGroup g = horizontal
                ? (HorizontalOrVerticalLayoutGroup)gameObject.AddComponent<HorizontalLayoutGroup>()
                : gameObject.AddComponent<VerticalLayoutGroup>();
            g.spacing = spacing;
            g.childAlignment = TextAnchor.MiddleCenter;
            g.childControlWidth = false;
            g.childControlHeight = false;
            g.childForceExpandWidth = false;
            g.childForceExpandHeight = false;
        }

        /// <summary>Creates and appends a button.</summary>
        public UIButton AddButton(string label, Action onClick, float width = 260f, float height = 64f)
        {
            var b = UIFactory.Button(transform, label, onClick);
            ((RectTransform)b.transform).sizeDelta = new Vector2(width, height);
            Add(b);
            return b;
        }

        /// <summary>Appends an existing button (re-parented under the group).</summary>
        public void Add(UIButton button)
        {
            button.transform.SetParent(transform, false);
            int i = _buttons.Count;
            _buttons.Add(button);
            button.Hovered += () => SetFocus(i, true);
            SetFocus(_index, true);
        }

        /// <summary>Moves focus (silent = no sound).</summary>
        public void SetFocus(int index, bool silent)
        {
            if (_buttons.Count == 0) return;
            index = (index % _buttons.Count + _buttons.Count) % _buttons.Count;
            if (index != _index && !silent) UISound.Play(UISoundId.Move);
            _index = index;
            for (int i = 0; i < _buttons.Count; i++) _buttons[i].Focused = i == _index;
        }

        void Update()
        {
            if (!InputEnabled || _buttons.Count == 0 || !UIInput.CanReceive(this)) return;
            var nav = UIInput.Navigate;
            int step = _horizontal ? nav.x : -nav.y;
            if (step != 0) SetFocus(_index + step, false);
            if (UIInput.Confirm)
            {
                UIInput.Consume();
                _buttons[_index].Click();
            }
        }
    }
}
