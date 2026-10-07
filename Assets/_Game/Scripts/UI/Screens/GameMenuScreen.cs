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
            // Touch screens: fewer, taller rows so each one is a comfortable thumb target.
            bool touch = Application.isMobilePlatform || UITouch.Supported;
            list = touch ? UIFactory.List(frame.Rect, 6, 90, 180) : UIFactory.List(frame.Rect, 8, 67, 180);
            list.Rt().anchorMin = new Vector2(0, 0);
            list.Rt().anchorMax = new Vector2(0.56f, 1);
            list.Rt().offsetMin = new Vector2(48, 110);
            list.Rt().offsetMax = new Vector2(-30, -bodyTop);
            list.EmptyText = "표시할 항목이 없습니다.";
            list.SelectionChanged += (_, row) => SetDetails(row);
            list.Submitted += (_, row) => (row.Tag as Action)?.Invoke();
            list.Rejected += (_, row) => UIRoot.Instance.Toast.Show(row.DisabledReason ?? "지금은 사용할 수 없습니다.", UIToastKind.Warning);
            var detailFrame = UIFactory.Panel(frame.Rect, UIPanelStyle.Dark, false);
            detailFrame.Rect.anchorMin = new Vector2(0.57f, 0);
            detailFrame.Rect.anchorMax = Vector2.one;
            detailFrame.Rect.offsetMin = new Vector2(0, 110);
            detailFrame.Rect.offsetMax = new Vector2(-48, -bodyTop);
            detailScroll = UIFactory.ScrollView(detailFrame.Rect, out var detailContent, spacing: 16f, name: "Description");
            detailScroll.Rt().Stretch(26, 24, 26, 24);
            detailHeading = UIFactory.Paragraph(detailContent, "", 29, UITheme.GoldBright);
            detailReason = UIFactory.Paragraph(detailContent, "", 22, UITheme.Danger);
            details = UIFactory.Paragraph(detailContent, "", 24);
            details.overflowMode = TextOverflowModes.Overflow;
            var back = UIFactory.Button(frame.Rect, "돌아가기", Close);
            back.Rt().Place(UIAnchor.BottomRight, new Vector2(-48, touch ? 18 : 30), new Vector2(240, touch ? 84 : 62));
            back.gameObject.SetActive(AllowCancel);
            UIFactory.KeyHint(frame.Rect, UIAction.Confirm, "결정 / 선택").Rt().Place(UIAnchor.BottomLeft, new Vector2(48, 46), new Vector2(280, 45));
            UIFactory.Label(frame.Rect, touch ? "탭: 선택 · 위아래로 끌어 목록 넘기기" : "↑↓ 항목 · ←→ 상세 스크롤", 21, color: UITheme.TextDim).Rt().Place(UIAnchor.BottomLeft, new Vector2(660, 46), new Vector2(540, 45));
            var cancelHint = UIFactory.KeyHint(frame.Rect, UIAction.Cancel, "돌아가기");
            cancelHint.Rt().Place(UIAnchor.BottomLeft, new Vector2(350, 46), new Vector2(280, 45));
            cancelHint.gameObject.SetActive(AllowCancel);
            Refresh();
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
        public void Add(string label, Action action, string description = "", string cost = null, bool enabled = true, string reason = null, Sprite icon = null)
        {
            rows.Add(new UIListItem(label, cost, enabled, reason, icon, tag: action) { Description = description });
        }
        protected override void OnFocus() { if (list != null) { list.Focused = true; Refresh(); } }
        protected override void OnBlur() { if (list != null) list.Focused = false; }
        protected override void OnClose() => Closed?.Invoke();
    }
}
