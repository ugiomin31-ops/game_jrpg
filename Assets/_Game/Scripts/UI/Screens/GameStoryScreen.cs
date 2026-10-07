using System;
using System.Collections.Generic;
using System.Linq;
using TMPro;
using UnityEngine;
using UnityEngine.UI;

namespace Abyss.UI
{
    public sealed class GameStoryScreen : UIScreen
    {
        public string Title;
        public IReadOnlyList<string> Pages;
        public float CharactersPerSecond = 42;
        public bool ReducedMotion;
        internal bool ReadOnly;
        public Action Completed;
        TextMeshProUGUI body, counter;
        UIButton next;
        ScrollRect scroll;
        int index;
        float revealed;
        bool finished;
        public override bool CloseOnCancel => ReadOnly;
        protected override void Build()
        {
            var backdrop = UIFactory.Fill(Rect, UITheme.Ink, raycast: true);
            UIFactory.Vignette(Rect, 0.7f);
            // Touch: a tap anywhere outside the buttons advances the text (finish typing, then next page).
            if (UIRoot.TouchFirst)
            {
                var tap = backdrop.gameObject.AddComponent<Button>();
                tap.transition = Selectable.Transition.None;
                tap.navigation = new Navigation { mode = Navigation.Mode.None };
                tap.onClick.AddListener(() => { if (IsTop) Advance(); });
            }
            bool phone = UIRoot.Compact;
            // Stories whose pages are all short (tips, floor intros, elder lines, the line-by-line prologue)
            // get a frame sized to the text instead of a mostly empty page.
            bool compact = !ReadOnly && Pages != null && Pages.Count > 0 && Pages.All(p => p.Length <= 160);
            var frame = UIFactory.Panel(Rect, UIPanelStyle.Ornate);
            if (UIRoot.TouchFirst)
            {
                var tapFrame = frame.Background.gameObject.AddComponent<Button>();
                tapFrame.transition = Selectable.Transition.None;
                tapFrame.navigation = new Navigation { mode = Navigation.Mode.None };
                tapFrame.onClick.AddListener(() => { if (IsTop) Advance(); });
            }
            if (phone) frame.Rect.Stretch(compact ? 220 : 90, compact ? 170 : 40, compact ? 220 : 90, compact ? 170 : 40);
            else if (compact) frame.Rect.Stretch(240, 300, 240, 300);
            else frame.Rect.Stretch(180, 120, 180, 120);
            var heading = UIFactory.Paragraph(frame.Rect, Title, ReadOnly ? 36 : 48, UITheme.GoldBright);
            heading.alignment = TextAlignmentOptions.Center;
            heading.overflowMode = TextOverflowModes.Ellipsis;
            heading.Rt().TopStrip(95, 35, 60, 60);
            UIFactory.Separator(frame.Rect, 900).Rt().Place(UIAnchor.Top, new Vector2(0, -142), new Vector2(900, 24));
            scroll = UIFactory.ScrollView(frame.Rect, out var storyContent, name: "Story text");
            if (compact) scroll.Rt().Stretch(90, 170, 90, 150);
            else scroll.Rt().Stretch(90, 190, 90, 160);
            // The text viewport catches raycasts for scrolling; relay plain taps on it to Advance as well.
            if (UIRoot.TouchFirst) scroll.viewport.gameObject.AddComponent<UITapArea>().Tapped += () => { if (IsTop) Advance(); };
            body = UIFactory.Paragraph(storyContent, "", ReadOnly ? (phone ? 28 : 24) : (phone ? 36 : 32));
            body.alignment = ReadOnly ? TextAlignmentOptions.TopLeft : TextAlignmentOptions.Midline;
            body.overflowMode = TextOverflowModes.Overflow;
            counter = UIFactory.Label(frame.Rect, "", 22, color: UITheme.TextDim, align: TextAlignmentOptions.Center);
            counter.Rt().BottomStrip(45, 110, 40, 40);
            counter.gameObject.SetActive(!compact || Pages.Count > 1);
            var buttons = UIFactory.ButtonGroup(frame.Rect, true, 24);
            buttons.Rt().BottomStrip(65, 35, 60, 60);
            next = buttons.AddButton("다음", Advance, 300);
            if (ReadOnly) buttons.AddButton("고지 닫기", Close, 300);
            else buttons.AddButton("이야기 건너뛰기", () => UIModal.Confirm(UIRoot.Instance.Modals, "이야기 건너뛰기", "이야기를 건너뛰고 계속할까요?", yes => { if (yes) Finish(); }, defaultYes: false), 330);
            ShowPage();
            if (UIRoot.TouchFirst)
                UIFactory.Label(frame.Rect, "화면을 탭하면 다음으로", 20, color: UITheme.TextDim, align: TextAlignmentOptions.Center)
                    .Rt().BottomStrip(32, 5, 50, 50);
            else if (!compact)
                UIFactory.Label(frame.Rect, "↑↓ 본문 스크롤 · ←→ 버튼 선택", 20, color: UITheme.TextDim, align: TextAlignmentOptions.Center)
                    .Rt().BottomStrip(32, 5, 50, 50);
        }
        void ShowPage()
        {
            scroll.StopMovement();
            if (Pages == null || Pages.Count == 0) { Finish(); return; }
            body.text = Pages[index];
            LayoutRebuilder.ForceRebuildLayoutImmediate(scroll.content);
            scroll.verticalNormalizedPosition = 1f;
            revealed = ReducedMotion ? int.MaxValue : 0;
            body.maxVisibleCharacters = ReducedMotion ? int.MaxValue : 0;
            counter.text = $"{index + 1} / {Pages.Count}";
            next.SetLabel(index == Pages.Count - 1 ? ReadOnly ? "고지 마치기" : "계속" : "다음");
        }
        void Update()
        {
            if (!IsTop || body == null || !UIInput.CanReceive(this)) return;
            if (UIInput.Navigate.y != 0)
            {
                scroll.StopMovement();
                scroll.verticalNormalizedPosition = Mathf.Clamp01(scroll.verticalNormalizedPosition + UIInput.Navigate.y * 0.15f);
                UIInput.Consume();
            }
            if (body.maxVisibleCharacters == int.MaxValue) return;
            revealed += Time.unscaledDeltaTime * CharactersPerSecond;
            body.maxVisibleCharacters = (int)revealed;
        }
        void Advance()
        {
            if (finished) return;
            if (body.maxVisibleCharacters < body.textInfo.characterCount)
            { body.maxVisibleCharacters = int.MaxValue; return; }
            if (++index >= Pages.Count) Finish(); else ShowPage();
        }
        void Finish()
        {
            if (finished) return;
            finished = true;
            Close();
            Completed?.Invoke();
        }
    }
}
