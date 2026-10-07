using System;
using System.Collections.Generic;
using TMPro;
using UnityEngine;
using UnityEngine.UI;

namespace Abyss.UI
{
    /// <summary>One line of a <see cref="UILootPopup"/>: icon, name, a small tag ("무기", "소모품") and the count.</summary>
    public struct UILootEntry
    {
        public Sprite Icon;
        public string Name, Tag;
        public int Count;
        public Color Accent;
    }

    /// <summary>
    /// "What did I just get?" reveal: a burst of light, the title, then each item card pops in one after another.
    /// Tap anywhere (after a short guard), Confirm or Cancel closes it.
    /// </summary>
    public sealed class UILootPopup : UIScreen
    {
        const int MaxCards = 6;
        string _title;
        int _gold;
        Action _onClose;
        readonly List<UILootEntry> _entries = new List<UILootEntry>();
        Image _dim, _glow;
        RectTransform _rays, _window;
        float _openedAt;
        bool _done;

        public static UILootPopup Show(UIScreenStack stack, string title, IList<UILootEntry> entries, int gold, Action onClose = null)
        {
            return stack.Push<UILootPopup>(p =>
            {
                p._title = title;
                p._gold = gold;
                p._onClose = onClose;
                if (entries != null) p._entries.AddRange(entries);
            });
        }

        protected override void Build()
        {
            bool compact = UIRoot.Compact;
            _dim = UIFactory.Fill(Rect, UITheme.Ink.WithAlpha(0.78f), "Dim", raycast: true);
            _dim.gameObject.AddComponent<UITapArea>().Tapped += TryClose;

            // Light burst behind the cards: a warm radial glow and slowly turning rays.
            _glow = UIFactory.Image(Rect, UISprites.SoftRadial, UITheme.Dawn.WithAlpha(0.55f), "Glow");
            _glow.Rt().Place(UIAnchor.Center, new Vector2(0, 40), new Vector2(1100, 1100));
            _rays = UIFactory.Rect(Rect, "Rays");
            _rays.Place(UIAnchor.Center, new Vector2(0, 40), new Vector2(10, 10));
            for (int i = 0; i < 12; i++)
            {
                var ray = UIFactory.Image(_rays, UISprites.GlowLine, UITheme.GoldBright.WithAlpha(i % 2 == 0 ? 0.32f : 0.18f), "Ray");
                ray.Rt().Place(UIAnchor.Center, Vector2.zero, new Vector2(1500, i % 2 == 0 ? 46 : 26));
                ray.transform.localRotation = Quaternion.Euler(0, 0, i * 15f);
            }

            int shown = Mathf.Min(MaxCards, _entries.Count);
            int columns = shown <= 3 ? Mathf.Max(1, shown) : Mathf.CeilToInt(shown / 2f);
            int rows = shown <= 3 ? 1 : 2;
            float cardW = compact ? 400f : 380f, cardH = compact ? 132f : 120f, gap = 22f;
            float gridW = Mathf.Max(1, columns) * cardW + (columns - 1) * gap;
            float width = Mathf.Max(compact ? 900f : 820f, gridW + 120f);
            float height = 210f + (shown == 0 ? 0f : rows * cardH + (rows - 1) * gap) + (_gold > 0 ? 70f : 0f) + 110f;

            var panel = UIFactory.Panel(Rect, UIPanelStyle.Ornate, true, "Window");
            _window = panel.Rect;
            _window.Place(UIAnchor.Center, new Vector2(0, 0), new Vector2(width, height));
            _window.gameObject.AddComponent<UITapArea>().Tapped += TryClose;

            var title = UIFactory.Label(_window, _title, compact ? 56f : 50f, UIFont.Title, UITheme.GoldBright, TextAlignmentOptions.Center, UITextFx.Glow, "Title");
            title.Rt().TopStrip(80, 40, 40, 40);
            title.transform.localScale = Vector3.one * 1.5f;
            UITween.Scale(title.transform, 1f, 0.4f, UIEase.OutBack, 0.05f);
            var sep = UIFactory.Separator(_window, 560f);
            sep.Rt().Place(UIAnchor.Top, new Vector2(0, -128), new Vector2(560, 22));

            float top = 170f;
            for (int i = 0; i < shown; i++)
            {
                int r = rows == 1 ? 0 : i / columns, c = rows == 1 ? i : i % columns;
                int inRow = rows == 1 ? shown : (r == 0 ? columns : shown - columns);
                float rowW = inRow * cardW + (inRow - 1) * gap;
                float x = -rowW / 2f + cardW / 2f + c * (cardW + gap);
                float y = -top - cardH / 2f - r * (cardH + gap);
                BuildCard(_entries[i], new Vector2(x, y), new Vector2(cardW, cardH), 0.25f + i * 0.12f);
            }
            if (_entries.Count > shown)
            {
                var more = UIFactory.Label(_window, $"외 {_entries.Count - shown}종", 26, UIFont.Bold, UITheme.TextDim, TextAlignmentOptions.Center);
                more.Rt().BottomStrip(34, (_gold > 0 ? 70f : 0f) + 104f, 40, 40);
            }
            if (_gold > 0)
            {
                var gold = UIFactory.Label(_window, $"+ {_gold:N0} G", compact ? 46f : 40f, UIFont.Heavy, UITheme.GoldBright, TextAlignmentOptions.Center, UITextFx.Glow, "Gold");
                gold.Rt().BottomStrip(60, 112, 40, 40);
                gold.transform.localScale = Vector3.zero;
                UITween.Scale(gold.transform, 1f, 0.35f, UIEase.OutBack, 0.3f + shown * 0.12f);
            }
            var ok = UIFactory.Button(_window, "확인", TryClose);
            ok.Rt().Place(UIAnchor.Bottom, new Vector2(0, 26), new Vector2(compact ? 320 : 280, compact ? 80 : 66));
        }

        void BuildCard(UILootEntry entry, Vector2 position, Vector2 size, float delay)
        {
            var card = UIFactory.Panel(_window, UIPanelStyle.Dark, false, "Loot " + entry.Name);
            card.Rect.Place(UIAnchor.Top, new Vector2(0.5f, 0.5f), position, size);
            var accent = entry.Accent.a > 0f ? entry.Accent : UITheme.Gold;
            // Thin accent outline (the warm focus-glow sprite tinted toward red read as an error state).
            var edge = UIFactory.Image(card.Rect, UISprites.PanelOutline, accent.WithAlpha(0.9f), "Edge");
            edge.type = Image.Type.Sliced;
            edge.Rt().Stretch(-3, -3, -3, -3);
            float iconSize = size.y - 28f;
            var halo = UIFactory.Image(card.Rect, UISprites.SoftRadial, accent.WithAlpha(0.5f), "Halo");
            halo.Rt().Place(UIAnchor.Left, new Vector2(14 + iconSize / 2f - (iconSize * 1.5f) / 2f, 0), new Vector2(iconSize * 1.5f, iconSize * 1.5f));
            var slot = UIFactory.IconSlot(card.Rect, iconSize);
            slot.Rt().Place(UIAnchor.Left, new Vector2(14, 0), new Vector2(iconSize, iconSize));
            slot.SetIcon(entry.Icon);
            float textLeft = iconSize + 32f;
            var name = UIFactory.Label(card.Rect, entry.Name, 32, UIFont.Heavy, UITheme.Text, TextAlignmentOptions.Left, UITextFx.Outline, "Name");
            name.Rt().Stretch(textLeft, 16, 16, size.y * 0.48f);
            name.enableAutoSizing = true; name.fontSizeMin = 22; name.fontSizeMax = 32;
            name.overflowMode = TextOverflowModes.Ellipsis;
            var tag = UIFactory.Label(card.Rect, entry.Tag ?? "", 24, UIFont.Bold, accent, TextAlignmentOptions.Left, UITextFx.Plain, "Tag");
            tag.Rt().Stretch(textLeft, size.y * 0.55f, 110, 12);
            var count = UIFactory.Label(card.Rect, "×" + Mathf.Max(1, entry.Count), 34, UIFont.Heavy, UITheme.GoldBright, TextAlignmentOptions.Right, UITextFx.Outline, "Count");
            count.Rt().Stretch(textLeft, size.y * 0.5f, 18, 8);

            if (!card.TryGetComponent(out CanvasGroup cg)) cg = card.gameObject.AddComponent<CanvasGroup>();
            cg.alpha = 0f;
            card.transform.localScale = Vector3.one * 0.6f;
            UITween.Fade(cg, 1f, 0.2f, UIEase.OutQuad, delay);
            UITween.Scale(card.transform, 1f, 0.38f, UIEase.OutBack, delay);
            UITween.Delay(this, delay, () => UISound.Play(UISoundId.Confirm));
        }

        void Update()
        {
            if (_rays != null) _rays.localRotation = Quaternion.Euler(0, 0, Time.unscaledTime * 12f);
            if (_glow != null) _glow.transform.localScale = Vector3.one * (1f + Mathf.Sin(Time.unscaledTime * 2.4f) * 0.05f);
            if (!IsTop || !UIInput.CanReceive(this)) return;
            if (UIInput.Confirm) { UIInput.Consume(); TryClose(); }
        }

        void TryClose()
        {
            // Ignore the tap/press that opened the chest still echoing through the input system.
            if (_done || Time.unscaledTime - _openedAt < 0.45f) return;
            _done = true;
            Close();
        }

        protected override void OnOpen() => _openedAt = Time.unscaledTime;

        protected override void OnCancel()
        {
            UISound.Play(UISoundId.Cancel);
            TryClose();
        }

        protected override void OnClose() => _onClose?.Invoke();

        protected override UITween AnimateIn()
        {
            Group.alpha = 1f;
            _dim.color = UITheme.Ink.WithAlpha(0f);
            UITween.Fade(_dim, 0.78f, 0.2f);
            bool reduced = UIRoot.Instance != null && UIRoot.Instance.ReducedMotion;
            _rays.localScale = Vector3.one * (reduced ? 1f : 0.2f);
            UITween.Scale(_rays, 1f, reduced ? 0f : 0.5f, UIEase.OutCubic);
            if (!_window.TryGetComponent(out CanvasGroup cg)) cg = _window.gameObject.AddComponent<CanvasGroup>();
            cg.alpha = 0f;
            _window.localScale = Vector3.one * (reduced ? 1f : 0.85f);
            UITween.Scale(_window, 1f, reduced ? 0f : 0.3f, UIEase.OutBack);
            return UITween.Fade(cg, 1f, 0.18f);
        }
    }
}
