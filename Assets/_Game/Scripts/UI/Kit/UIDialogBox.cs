using System;
using System.Collections;
using TMPro;
using UnityEngine;
using UnityEngine.UI;

namespace Abyss.UI
{
    /// <summary>
    /// Story dialog window: ornate panel at the bottom of the screen, speaker name plate, optional circular
    /// portrait, typewriter text (punctuation pauses, hold confirm to fast-forward) and a bobbing advance arrow.
    /// Confirm / click completes the line, then advances. Create with <see cref="UIFactory.DialogBox"/>.
    /// </summary>
    public sealed class UIDialogBox : MonoBehaviour
    {
        const float Width = 1520f, Height = 250f;

        [SerializeField] RectTransform _window;
        [SerializeField] CanvasGroup _group;
        [SerializeField] RectTransform _plate, _arrow;
        [SerializeField] TextMeshProUGUI _speaker, _text;
        [SerializeField] UIPortrait _portrait;
        float _visible;
        int _total;
        bool _typing, _waiting, _open;

        /// <summary>Characters revealed per second.</summary>
        public float CharsPerSecond { get; set; } = 42f;
        /// <summary>True while text is being revealed.</summary>
        public bool IsTyping => _typing;
        /// <summary>True when the line is fully shown and the box waits for advance input.</summary>
        public bool IsWaiting => _waiting;
        /// <summary>When false, the box ignores input (scripted advance only).</summary>
        public bool InputEnabled { get; set; } = true;
        /// <summary>Portrait widget (use <see cref="UIPortrait.Raw"/> for render textures).</summary>
        public UIPortrait Portrait => _portrait;
        /// <summary>Body text component.</summary>
        public TextMeshProUGUI Text => _text;

        /// <summary>Raised when the player advances past a fully shown line.</summary>
        public event Action Advanced;

        internal void Build()
        {
            var rt = (RectTransform)transform;
            rt.Stretch();
            _window = UIFactory.Rect(rt, "Window");
            _window.Place(UIAnchor.Bottom, new Vector2(0f, 40f), new Vector2(Width, Height));
            _group = _window.gameObject.AddComponent<CanvasGroup>();
            var panel = UIFactory.Panel(_window, UIPanelStyle.Ornate, true, "Panel");
            panel.Rect.Stretch();

            _portrait = UIFactory.Portrait(_window, 210f);
            _portrait.Rt().Place(UIAnchor.Left, new Vector2(34f, 6f), new Vector2(210f, 210f));

            var plateImg = UIFactory.Image(_window, UISprites.NamePlate, Color.white, "NamePlate");
            _plate = plateImg.rectTransform;
            _plate.Place(UIAnchor.TopLeft, new Vector2(0f, 0.5f), new Vector2(270f, 0f), new Vector2(300f, 56f));
            _speaker = UIFactory.Label(_plate, "", UITheme.SizeLabel + 2f, UIFont.Heavy, UITheme.GoldBright, TextAlignmentOptions.MidlineLeft, UITextFx.Outline, "Speaker");
            _speaker.rectTransform.Stretch(34f, 0f, 20f, 2f);

            _text = UIFactory.Paragraph(_window, "", UITheme.SizeLabel + 1f, UITheme.Text, "Text");
            _text.rectTransform.Stretch(282f, 52f, 70f, 34f);
            _text.lineSpacing = 14f;
            _text.font = UITheme.Font(UIFont.Bold);
            _text.fontSharedMaterial = UITheme.TextMaterial(UIFont.Bold, UITextFx.Shadow);

            var arrow = UIFactory.Image(_window, UISprites.ArrowDown, Color.white, "Advance");
            _arrow = arrow.rectTransform;
            _arrow.Place(UIAnchor.BottomRight, new Vector2(-44f, 30f), new Vector2(32f, 32f));
            _arrow.gameObject.SetActive(false);
            _group.alpha = 0f;
            _window.gameObject.SetActive(false);
        }

        /// <summary>
        /// Shows a line. <paramref name="speaker"/> null/empty hides the name plate; a null portrait hides the
        /// portrait and widens the text. Pass a Sprite via <see cref="UIPortrait.SetSprite"/> on <see cref="Portrait"/> if preferred.
        /// </summary>
        public void Show(string speaker, string text, Texture portrait = null)
        {
            Open();
            bool hasSpeaker = !string.IsNullOrEmpty(speaker);
            _plate.gameObject.SetActive(hasSpeaker);
            _speaker.text = speaker ?? "";
            if (hasSpeaker)
                _plate.sizeDelta = new Vector2(Mathf.Max(220f, _speaker.GetPreferredValues(speaker).x + 70f), 56f);
            bool hasPortrait = portrait != null || _portrait.SpriteImage.enabled;
            if (portrait != null) _portrait.SetTexture(portrait);
            _portrait.gameObject.SetActive(hasPortrait);
            float left = hasPortrait ? 282f : 70f;
            _text.rectTransform.Stretch(left, 52f, 70f, 34f);
            _plate.anchoredPosition = new Vector2(hasPortrait ? 270f : 48f, 0f);

            _text.text = text ?? "";
            _text.ForceMeshUpdate();
            _total = _text.textInfo.characterCount;
            _visible = 0f;
            _typing = _total > 0;
            _waiting = !_typing;
            _text.maxVisibleCharacters = 0;
            _arrow.gameObject.SetActive(_waiting);
            if (!Application.isPlaying || (UIRoot.Instance != null && UIRoot.Instance.ReducedMotion)) Complete();
        }

        /// <summary>Reveals the whole line immediately.</summary>
        public void Complete()
        {
            _typing = false;
            _waiting = true;
            _visible = _total;
            _text.maxVisibleCharacters = _total;
            _arrow.gameObject.SetActive(true);
        }

        /// <summary>Shows the line and yields until the player advances: <c>yield return dialog.Say("리나", "…");</c></summary>
        public IEnumerator Say(string speaker, string text, Texture portrait = null)
        {
            bool done = false;
            void OnAdvanced() => done = true;
            Advanced += OnAdvanced;
            Show(speaker, text, portrait);
            while (!done && this != null) yield return null;
            Advanced -= OnAdvanced;
        }

        /// <summary>Opens the window (animated).</summary>
        public void Open()
        {
            if (_open) return;
            _open = true;
            UIInput.Consume();
            UIInput.PushLayer(transform);
            _window.gameObject.SetActive(true);
            UITween.Kill(_group);
            UITween.Kill(_window);
            if (!Application.isPlaying) { _group.alpha = 1f; return; }
            _group.alpha = 0f;
            bool reduced = UIRoot.Instance != null && UIRoot.Instance.ReducedMotion;
            _window.anchoredPosition = new Vector2(0f, reduced ? 40f : 20f);
            UITween.Fade(_group, 1f, 0.2f);
            UITween.Move(_window, new Vector2(0f, 40f), reduced ? 0f : 0.22f, UIEase.OutCubic);
        }

        /// <summary>Closes the window (animated).</summary>
        public UITween Close()
        {
            _open = false;
            UIInput.PopLayer(transform);
            _typing = _waiting = false;
            UITween.Kill(_group);
            return UITween.Fade(_group, 0f, 0.18f).OnComplete(() => { if (!_open && _window != null) _window.gameObject.SetActive(false); });
        }

        void Update()
        {
            if (!_open) return;
            if (_waiting) _arrow.anchoredPosition = new Vector2(-44f, 30f + (UIRoot.Instance != null && UIRoot.Instance.ReducedMotion ? 0f : Mathf.Abs(Mathf.Sin(Time.unscaledTime * 4f)) * 5f));
            if (_typing)
            {
                if (UIRoot.Instance != null && UIRoot.Instance.ReducedMotion) Complete();
                float speed = CharsPerSecond * (UIInput.ConfirmHeld && InputEnabled ? 3f : 1f);
                int before = (int)_visible;
                _visible += Time.unscaledDeltaTime * speed * PauseFactor(before);
                int now = Mathf.Min(_total, (int)_visible);
                if (now != before)
                {
                    _text.maxVisibleCharacters = now;
                    if (now / 2 != before / 2) UISound.Play(UISoundId.Type);
                }
                if (now >= _total) Complete();
            }
            if (!InputEnabled || !UIInput.CanReceive(this) || !UIInput.Advance) return;
            UIInput.Consume();
            if (_typing) Complete();
            else if (_waiting)
            {
                _waiting = false;
                _arrow.gameObject.SetActive(false);
                UISound.Play(UISoundId.Confirm);
                Advanced?.Invoke();
            }
        }

        void OnDisable() => UIInput.PopLayer(transform);

        /// <summary>Slows the reveal right after punctuation.</summary>
        float PauseFactor(int index)
        {
            if (index <= 0 || index > _total) return 1f;
            char c = _text.textInfo.characterInfo[index - 1].character;
            switch (c)
            {
                case '.': case '!': case '?': case '…': return 0.12f;
                case ',': return 0.3f;
                default: return 1f;
            }
        }
    }
}
