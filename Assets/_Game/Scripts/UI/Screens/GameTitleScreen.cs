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
            var eyebrow = UIFactory.Label(Rect, "A B Y S S   L A B Y R I N T H", 23, color: UITheme.Gold);
            eyebrow.Rt().Place(UIAnchor.TopLeft, new Vector2(100, -115), new Vector2(760, 40));
            var title = UIFactory.Label(Rect, "심연의 미궁", 94, UIFont.Title, UITheme.Text, TextAlignmentOptions.MidlineLeft, UITextFx.Heavy);
            title.Rt().Place(UIAnchor.TopLeft, new Vector2(92, -162), new Vector2(900, 145));
            var rule = UIFactory.Image(Rect, UISprites.White, UITheme.Gold, "Dawn line");
            rule.Rt().Place(UIAnchor.TopLeft, new Vector2(103, -317), new Vector2(430, 2));
            var motto = UIFactory.Label(Rect, "잊힌 여명을 찾아, 심연으로.", 27, color: UITheme.GoldBright);
            motto.Rt().Place(UIAnchor.TopLeft, new Vector2(100, -345), new Vector2(720, 46));
            var group = UIFactory.ButtonGroup(Rect, false, 16);
            group.Rt().Place(UIAnchor.Left, new Vector2(100, -102), new Vector2(420, 444));
            group.AddButton("새로운 모험", () => NewGame?.Invoke(), 420, 72);
            var resume = group.AddButton("모험 이어가기", () => ContinueGame?.Invoke(), 420, 72);
            resume.Interactable = HasSave;
            resume.DisabledReason = "저장된 모험이 없습니다. 새로운 모험을 시작해 주세요.";
            if (!HasSave) resume.SetLabel("모험 이어가기 · 저장 없음");
            group.AddButton("설정", () => Settings?.Invoke(), 420, 62);
            group.AddButton("제작진", () => Credits?.Invoke(), 420, 62);
            group.AddButton("게임 종료", () => Quit?.Invoke(), 420, 62);
            group.FocusIndex = HasSave ? 1 : 0;
            UIFactory.KeyHint(Rect, UIAction.Confirm, "선택").Rt().Place(UIAnchor.BottomLeft, new Vector2(100, 75), new Vector2(250, 44));
            UIFactory.Label(Rect, "↑↓ 이동 · Enter / Space / Z 선택", 21, color: UITheme.TextDim)
                .Rt().Place(UIAnchor.BottomLeft, new Vector2(365, 75), new Vector2(650, 44));
            var footer = UIFactory.Label(Rect, "네 명의 동료 · 열두 층의 미궁 · 여명의 종", 22, color: UITheme.TextDim);
            footer.Rt().Place(UIAnchor.BottomLeft, new Vector2(100, 30), new Vector2(850, 40));
        }
    }
}
