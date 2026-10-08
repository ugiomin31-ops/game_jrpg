using System;
using System.Collections.Generic;
using TMPro;
using UnityEngine;
using UnityEngine.UI;

namespace Abyss.UI
{
    /// <summary>One focused, scrollable menu; all pointer and controller paths use the same actions.</summary>
    public sealed class GameMenuScreen : UIScreen
    {
        public string Title, Subtitle;
        public string[] TabLabels;
        public Action<GameMenuScreen> RefreshContent;
        public Action Closed;
        public bool AllowCancel = true;
        public bool CloseOnMenu;
        public bool FullBackdrop;
        public int TabIndex;
        UIList list;
        UITabs tabs;
        TextMeshProUGUI heading, subtitle, detailHeading, detailReason, details;
        ScrollRect detailScroll;
        readonly List<UIListItem> rows = new List<UIListItem>();
        public override bool CloseOnCancel => AllowCancel;
        public int Selection => list == null ? 0 : Math.Max(0, list.SelectedIndex);
        public override bool HideWhenCovered => true;

        protected override void Build()
        {
            UIFactory.Fill(Rect, UITheme.Ink.WithAlpha(FullBackdrop ? 0.98f : 0.84f), raycast: true);
            UIFactory.Vignette(Rect, 0.55f);
            if (UIRoot.Compact) BuildCompact(); else BuildWide();
            Refresh();
        }

        /// <summary>
        /// Landscape phone: back button and title share a slim top bar (thumb reach, no wasted header), the list fills
        /// the left 56 % with 6 tall card rows, details on the right in larger type. No keyboard hints.
        /// </summary>
        void BuildCompact()
        {
            var frame = UIFactory.Panel(Rect, UIPanelStyle.Ornate);
            frame.Rect.Stretch(26, 18, 26, 18);
            var back = UIFactory.Button(frame.Rect, "◀ 돌아가기", Close);
            back.Rt().Place(UIAnchor.TopLeft, new Vector2(22, -18), new Vector2(232, 84));
            back.gameObject.SetActive(AllowCancel);
            float titleLeft = AllowCancel ? 280f : 40f;
            heading = UIFactory.Label(frame.Rect, Title, 44, UIFont.Title, UITheme.GoldBright, fx: UITextFx.Outline);
            heading.Rt().TopStrip(60, 14, titleLeft, 40);
            heading.overflowMode = TextOverflowModes.Ellipsis;
            subtitle = UIFactory.Label(frame.Rect, Subtitle ?? "", 25, UIFont.Bold, UITheme.TextDim);
            subtitle.Rt().TopStrip(34, 72, titleLeft, 40);
            subtitle.overflowMode = TextOverflowModes.Ellipsis;
            float bodyTop = 120f;
            if (TabLabels != null && TabLabels.Length > 0)
            {
                tabs = UIFactory.Tabs(frame.Rect, TabLabels, Math.Min(240f, 1380f / TabLabels.Length), 72f);
                tabs.Rt().TopStrip(72, bodyTop, 26, 26);
                tabs.Select(TabIndex, false);
                tabs.Changed += i => { TabIndex = i; Refresh(); };
                bodyTop += 84f;
            }
            // Rows fill the height left under the header: 900-unit canvas minus frame margins and bottom padding.
            float available = UIRoot.PhoneReference.y - 36f - bodyTop - 24f;
            const int visible = 6;
            float rowHeight = Mathf.Clamp(Mathf.Floor(available / visible), 80f, 104f);
            list = UIFactory.List(frame.Rect, visible, rowHeight, 200);
            list.Rt().anchorMin = new Vector2(0, 1);
            list.Rt().anchorMax = new Vector2(0.56f, 1);
            list.Rt().pivot = new Vector2(0.5f, 1);
            list.Rt().offsetMin = new Vector2(22, -bodyTop - visible * rowHeight);
            list.Rt().offsetMax = new Vector2(-14, -bodyTop);
            WireList();
            var detailFrame = UIFactory.Panel(frame.Rect, UIPanelStyle.Dark, false);
            detailFrame.Rect.anchorMin = new Vector2(0.56f, 0);
            detailFrame.Rect.anchorMax = Vector2.one;
            detailFrame.Rect.offsetMin = new Vector2(8, 24);
            detailFrame.Rect.offsetMax = new Vector2(-24, -bodyTop);
            BuildDetails(detailFrame.Rect, 34, 27, 29);
        }

        void BuildWide()
        {
            var frame = UIFactory.Panel(Rect, UIPanelStyle.Ornate);
            frame.Rect.Stretch(100, 70, 100, 70);
            heading = UIFactory.Label(frame.Rect, Title, 44, color: UITheme.GoldBright);
            heading.Rt().TopStrip(65, 35, 48, 48);
            heading.overflowMode = TextOverflowModes.Ellipsis;
            subtitle = UIFactory.Paragraph(frame.Rect, Subtitle ?? "", 23, UITheme.TextDim);
            subtitle.Rt().TopStrip(65, 107, 48, 48);
            subtitle.overflowMode = TextOverflowModes.Ellipsis;
            if (TabLabels != null && TabLabels.Length > 0)
            {
                tabs = UIFactory.Tabs(frame.Rect, TabLabels, Math.Min(215f, 1450f / TabLabels.Length));
                tabs.Rt().TopStrip(56, 175, 48, 48);
                tabs.Select(TabIndex, false);
                tabs.Changed += i => { TabIndex = i; Refresh(); };
            }
            float bodyTop = tabs == null ? 195f : 250f;
            bool touch = Application.isMobilePlatform || UITouch.Supported;
            list = touch ? UIFactory.List(frame.Rect, 6, 90, 180) : UIFactory.List(frame.Rect, 8, 67, 180);
            list.Rt().anchorMin = new Vector2(0, 0);
            list.Rt().anchorMax = new Vector2(0.56f, 1);
            list.Rt().offsetMin = new Vector2(48, 110);
            list.Rt().offsetMax = new Vector2(-30, -bodyTop);
            WireList();
            var detailFrame = UIFactory.Panel(frame.Rect, UIPanelStyle.Dark, false);
            detailFrame.Rect.anchorMin = new Vector2(0.57f, 0);
            detailFrame.Rect.anchorMax = Vector2.one;
            detailFrame.Rect.offsetMin = new Vector2(0, 110);
            detailFrame.Rect.offsetMax = new Vector2(-48, -bodyTop);
            BuildDetails(detailFrame.Rect, 29, 22, 24);
            var back = UIFactory.Button(frame.Rect, "돌아가기", Close);
            back.Rt().Place(UIAnchor.BottomRight, new Vector2(-48, touch ? 18 : 30), new Vector2(240, touch ? 84 : 62));
            back.gameObject.SetActive(AllowCancel);
            if (touch)
            {
                UIFactory.Label(frame.Rect, "탭: 선택 · 위아래로 끌어 목록 넘기기", 21, color: UITheme.TextDim).Rt().Place(UIAnchor.BottomLeft, new Vector2(48, 46), new Vector2(620, 45));
                return;
            }
            UIFactory.KeyHint(frame.Rect, UIAction.Confirm, "결정 / 선택").Rt().Place(UIAnchor.BottomLeft, new Vector2(48, 46), new Vector2(280, 45));
            UIFactory.Label(frame.Rect, "↑↓ 항목 · ←→ 상세 스크롤", 21, color: UITheme.TextDim).Rt().Place(UIAnchor.BottomLeft, new Vector2(660, 46), new Vector2(540, 45));
            var cancelHint = UIFactory.KeyHint(frame.Rect, UIAction.Cancel, "돌아가기");
            cancelHint.Rt().Place(UIAnchor.BottomLeft, new Vector2(350, 46), new Vector2(280, 45));
            cancelHint.gameObject.SetActive(AllowCancel);
        }

        void WireList()
        {
            list.EmptyText = "표시할 항목이 없습니다.";
            list.SelectionChanged += (_, row) => SetDetails(row);
            list.Submitted += (_, row) => (row.Tag as Action)?.Invoke();
            list.Rejected += (_, row) => UIRoot.Instance.Toast.Show(row.DisabledReason ?? "지금은 사용할 수 없습니다.", UIToastKind.Warning);
        }

        void BuildDetails(RectTransform parent, float headingSize, float reasonSize, float bodySize)
        {
            detailScroll = UIFactory.ScrollView(parent, out var detailContent, spacing: 16f, name: "Description");
            detailScroll.Rt().Stretch(26, 24, 26, 24);
            detailHeading = UIFactory.Paragraph(detailContent, "", headingSize, UITheme.GoldBright);
            detailReason = UIFactory.Paragraph(detailContent, "", reasonSize, new Color(1f, 0.62f, 0.55f));
            details = UIFactory.Paragraph(detailContent, "", bodySize);
            details.overflowMode = TextOverflowModes.Overflow;
        }
        public void Refresh()
        {
            if (list == null) return;
            int selection = Selection;
            rows.Clear();
            RefreshContent?.Invoke(this);
            heading.text = Title;
            subtitle.text = Subtitle ?? "";
            list.SetItems(rows, selection);
            if (list.Selected == null) SetDetails(null);
        }
        void SetDetails(UIListItem row)
        {
            detailHeading.text = row?.Label ?? "표시할 항목이 없습니다.";
            detailReason.text = row != null && !row.Enabled ? "사용 불가 · " + (row.DisabledReason ?? "지금은 사용할 수 없습니다.") : "";
            detailReason.gameObject.SetActive(!string.IsNullOrEmpty(detailReason.text));
            details.text = row?.Description ?? "";
            // Refresh wrapped text height before resetting scroll, including a shorter next selection.
            LayoutRebuilder.ForceRebuildLayoutImmediate(detailScroll.content);
            detailScroll.StopMovement();
            detailScroll.verticalNormalizedPosition = 1f;
        }
        void Update()
        {
            if (!IsTop || !UIInput.CanReceive(this) || detailScroll == null) return;
            if (CloseOnMenu && UIInput.Menu) { UIInput.Consume(); Close(); return; }
            // Horizontal navigation scrolls long descriptions without stealing list selection.
            int direction = UIInput.Navigate.x;
            if (direction != 0)
            {
                detailScroll.StopMovement();
                detailScroll.verticalNormalizedPosition = Mathf.Clamp01(detailScroll.verticalNormalizedPosition - direction * 0.16f);
                UIInput.Consume();
            }
        }
        public void Add(string label, Action action, string description = "", string cost = null, bool enabled = true, string reason = null, Sprite icon = null, Color? labelColor = null)
        {
            rows.Add(new UIListItem(label, cost, enabled, reason, icon, tag: action) { Description = description, LabelColor = labelColor });
        }
        protected override void OnFocus() { if (list != null) { list.Focused = true; Refresh(); } }
        protected override void OnBlur() { if (list != null) list.Focused = false; }
        protected override void OnClose() => Closed?.Invoke();
    }
}
