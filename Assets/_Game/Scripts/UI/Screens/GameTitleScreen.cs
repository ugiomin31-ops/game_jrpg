using System;
using UnityEngine;
using TMPro;

namespace Abyss.UI
{
    public sealed class GameTitleScreen : UIScreen
    {
        public Action NewGame, ContinueGame, Settings, Credits, Quit;
        public bool HasSave;
        public override bool CloseOnCancel => false;
        protected override void Build()
        {
            UIFactory.Fill(Rect, UITheme.Ink.WithAlpha(.12f));
            UIFactory.Vignette(Rect, .42f);
            var shade = UIFactory.Image(Rect, UISprites.GradientH, UITheme.Ink.WithAlpha(.94f), "Title readability gradient");
            shade.Rt().anchorMin = Vector2.zero;
            shade.Rt().anchorMax = new Vector2(.64f, 1);
            shade.Rt().offsetMin = shade.Rt().offsetMax = Vector2.zero;
            shade.Rt().localScale = new Vector3(-1, 1, 1);
            // Phone landscape (900-unit canvas): title block higher, big thumb buttons anchored to the bottom-left.
            bool compact = UIRoot.Compact;
            float top = compact ? 52f : 115f, x = compact ? 84f : 100f;
            var eyebrow = UIFactory.Label(Rect, "A B Y S S   L A B Y R I N T H", 23, color: UITheme.Gold);
            eyebrow.Rt().Place(UIAnchor.TopLeft, new Vector2(x, -top), new Vector2(760, 40));
            var title = UIFactory.Label(Rect, "심연의 미궁", compact ? 88 : 94, UIFont.Title, UITheme.Text, TextAlignmentOptions.MidlineLeft, UITextFx.Heavy);
            title.Rt().Place(UIAnchor.TopLeft, new Vector2(x - 8, -top - 44), new Vector2(900, 140));
            var rule = UIFactory.Image(Rect, UISprites.White, UITheme.Gold, "Dawn line");
            rule.Rt().Place(UIAnchor.TopLeft, new Vector2(x + 3, -top - 194), new Vector2(430, 2));
            var motto = UIFactory.Label(Rect, "잊힌 여명을 찾아, 심연으로.", compact ? 30 : 27, color: UITheme.GoldBright);
            motto.Rt().Place(UIAnchor.TopLeft, new Vector2(x, -top - 214), new Vector2(720, 46));
            var group = UIFactory.ButtonGroup(Rect, false, compact ? 14 : 16);
            float w = compact ? 520 : 420, big = compact ? 92 : 72, small = compact ? 74 : 62;
            if (compact) group.Rt().Place(UIAnchor.BottomLeft, new Vector2(0f, 0f), new Vector2(x, 52), new Vector2(w, 2 * big + 2 * small + 3 * 14));
            else group.Rt().Place(UIAnchor.Left, new Vector2(100, -102), new Vector2(420, 444));
            group.AddButton("새로운 모험", () => NewGame?.Invoke(), w, big);
            var resume = group.AddButton("모험 이어가기", () => ContinueGame?.Invoke(), w, big);
            resume.Interactable = HasSave;
            resume.DisabledReason = "저장된 모험이 없습니다. 새로운 모험을 시작해 주세요.";
            if (!HasSave) resume.SetLabel("모험 이어가기 · 저장 없음");
            group.AddButton("설정", () => Settings?.Invoke(), w, small);
            group.AddButton("제작진", () => Credits?.Invoke(), w, small);
            // iOS apps may not quit themselves; Android keeps the button for its back-to-home habit.
            // Phones and browsers leave with the home/back gesture or by closing the tab: no quit button there.
            if (!UIRoot.TouchFirst && Application.platform != RuntimePlatform.WebGLPlayer) group.AddButton("게임 종료", () => Quit?.Invoke(), 420, 62);
            group.FocusIndex = HasSave ? 1 : 0;
            if (!UIRoot.TouchFirst)
            {
                UIFactory.KeyHint(Rect, UIAction.Confirm, "선택").Rt().Place(UIAnchor.BottomLeft, new Vector2(100, 75), new Vector2(250, 44));
                UIFactory.Label(Rect, "↑↓ 이동 · Enter / Space / Z 선택", 21, color: UITheme.TextDim)
                    .Rt().Place(UIAnchor.BottomLeft, new Vector2(365, 75), new Vector2(650, 44));
            }
            var footer = UIFactory.Label(Rect, "네 명의 동료 · 열두 층의 미궁 · 여명의 종", 22, UIFont.Bold, UITheme.TextDim,
                compact ? TextAlignmentOptions.MidlineRight : TextAlignmentOptions.MidlineLeft);
            if (compact) footer.Rt().Place(UIAnchor.BottomRight, new Vector2(-60, 30), new Vector2(850, 40));
            else footer.Rt().Place(UIAnchor.BottomLeft, new Vector2(100, 30), new Vector2(850, 40));
        }
    }
}
