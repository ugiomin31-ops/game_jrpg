using System;
using System.Collections.Generic;
using TMPro;
using UnityEngine;
using UnityEngine.UI;

namespace Abyss.UI
{
    /// <summary>
    /// Centred ornate dialog over a dimmer with title, message and a row of buttons. Cancel picks the
    /// cancel choice. Use <see cref="Confirm"/> / <see cref="Alert"/> / <see cref="Choice"/>.
    /// </summary>
    public sealed class UIModal : UIScreen
    {
        string _title, _message;
        readonly List<string> _choices = new List<string>();
        int _cancelIndex, _defaultIndex;
        Action<int> _onResult;
        bool _answered;
        Image _dim;
        UIPanel _panel;
        ScrollRect _messageScroll;

        /// <summary>The button row (index = choice index).</summary>
        public UIButtonGroup Buttons { get; private set; }
        /// <summary>Message label (rich text allowed).</summary>
        public TextMeshProUGUI Message { get; private set; }

        /// <summary>Yes/No confirmation. <paramref name="onResult"/> receives true for yes; cancel = no.</summary>
        public static UIModal Confirm(UIScreenStack stack, string title, string message, Action<bool> onResult,
            string yes = "예", string no = "아니오", bool defaultYes = true)
        {
            return Choice(stack, title, message, new[] { yes, no }, i => onResult?.Invoke(i == 0), cancelIndex: 1, defaultIndex: defaultYes ? 0 : 1);
        }

        /// <summary>Single-button notice.</summary>
        public static UIModal Alert(UIScreenStack stack, string title, string message, Action onClose = null, string ok = "확인")
        {
            return Choice(stack, title, message, new[] { ok }, _ => onClose?.Invoke(), cancelIndex: 0, defaultIndex: 0);
        }

        /// <summary>
        /// Generic multi-choice modal. <paramref name="cancelIndex"/> is reported on cancel (-1 = cancel disabled).
        /// </summary>
        public static UIModal Choice(UIScreenStack stack, string title, string message, IList<string> choices, Action<int> onResult,
            int cancelIndex = -1, int defaultIndex = 0)
        {
            return stack.Push<UIModal>(m =>
            {
                m._title = title;
                m._message = message;
                m._choices.AddRange(choices);
                m._onResult = onResult;
                m._cancelIndex = cancelIndex;
                m._defaultIndex = defaultIndex;
            });
        }

        /// <inheritdoc/>
        public override bool CloseOnCancel => _cancelIndex >= 0;

        /// <inheritdoc/>
        protected override void Build()
        {
            _dim = UIFactory.Fill(Rect, UITheme.Dim, "Dim", raycast: true);
            _panel = UIFactory.Panel(Rect, UIPanelStyle.Ornate, true, "Window");
            _panel.Rect.Place(UIAnchor.Center, Vector2.zero, new Vector2(820f, 0f));
            var v = _panel.gameObject.AddComponent<VerticalLayoutGroup>();
            v.padding = new RectOffset(64, 64, 46, 44);
            v.spacing = 14f;
            v.childAlignment = TextAnchor.UpperCenter;
            v.childControlWidth = v.childControlHeight = true;
            v.childForceExpandWidth = true;
            v.childForceExpandHeight = false;
            _panel.gameObject.AddComponent<ContentSizeFitter>().verticalFit = ContentSizeFitter.FitMode.PreferredSize;

            if (!string.IsNullOrEmpty(_title))
            {
                var title = UIFactory.Label(_panel.Rect, _title, UITheme.SizeHeader + 4f, UIFont.Title, UITheme.GoldBright, TextAlignmentOptions.Center, UITextFx.Outline, "Title");
                title.textWrappingMode = TextWrappingModes.Normal;
                title.overflowMode = TextOverflowModes.Ellipsis;
                UIFactory.Layout(title, -1f, Mathf.Clamp(title.GetPreferredValues(_title, 692f, 0f).y, 48f, 96f));
                var sep = UIFactory.Separator(_panel.Rect, 520f);
                sep.preserveAspect = true;
                UIFactory.Layout(sep, -1f, 22f);
            }
            _messageScroll = UIFactory.ScrollView(_panel.Rect, out var content, name: "Notice text");
            Message = UIFactory.Paragraph(content, _message, UITheme.SizeLabel - 1f, UITheme.Text, "Message");
            Message.alignment = TextAlignmentOptions.TopLeft;
            Message.overflowMode = TextOverflowModes.Overflow;
            float messageHeight = Message.GetPreferredValues(_message, 674f, 0f).y + 18f;
            UIFactory.Layout(_messageScroll, -1f, Mathf.Clamp(messageHeight, 90f, 360f));
            var hint = UIFactory.Label(_panel.Rect, "↑↓ 본문 스크롤 · ←→ 선택", 20f, color: UITheme.TextDim, align: TextAlignmentOptions.Center);
            UIFactory.Layout(hint, -1f, 30f);

            Buttons = UIFactory.ButtonGroup(_panel.Rect, true, 26f);
            UIFactory.Layout(Buttons, -1f, 72f);
            for (int i = 0; i < _choices.Count; i++)
            {
                int idx = i;
                float width = Mathf.Min(240f, (692f - 26f * (_choices.Count - 1)) / Mathf.Max(1, _choices.Count));
                Buttons.AddButton(_choices[i], () => Answer(idx), width, 64f);
            }
            Buttons.SetFocus(_defaultIndex, true);
        }

        void Update()
        {
            if (!IsTop || !UIInput.CanReceive(this) || _messageScroll == null) return;
            int direction = UIInput.Navigate.y;
            if (direction == 0) return;
            _messageScroll.StopMovement();
            _messageScroll.verticalNormalizedPosition = Mathf.Clamp01(_messageScroll.verticalNormalizedPosition + direction * 0.16f);
            UIInput.Consume();
        }

        void Answer(int index)
        {
            if (_answered) return;
            _answered = true;
            Close();
            _onResult?.Invoke(index);
        }

        /// <inheritdoc/>
        protected override void OnCancel()
        {
            if (_cancelIndex < 0) return;
            UISound.Play(UISoundId.Cancel);
            Answer(_cancelIndex);
        }

        /// <inheritdoc/>
        protected override UITween AnimateIn()
        {
            Group.alpha = 1f;
            _dim.color = UITheme.Dim.WithAlpha(0f);
            UITween.Fade(_dim, UITheme.Dim.a, 0.2f);
            if (!_panel.TryGetComponent(out CanvasGroup cg)) cg = _panel.gameObject.AddComponent<CanvasGroup>();
            cg.alpha = 0f;
            bool reduced = UIRoot.Instance != null && UIRoot.Instance.ReducedMotion;
            _panel.transform.localScale = Vector3.one * (reduced ? 1f : 0.97f);
            UITween.Scale(_panel.transform, 1f, reduced ? 0f : 0.22f, UIEase.OutCubic);
            return UITween.Fade(cg, 1f, 0.18f);
        }

        /// <inheritdoc/>
        protected override UITween AnimateOut()
        {
            UITween.Scale(_panel.transform, UIRoot.Instance != null && UIRoot.Instance.ReducedMotion ? 1f : 0.98f, 0.14f, UIEase.InCubic);
            return UITween.Fade(Group, 0f, 0.16f);
        }
    }
}
