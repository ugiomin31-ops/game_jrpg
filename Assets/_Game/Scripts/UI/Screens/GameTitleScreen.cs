using System;
using System.Collections.Generic;
using TMPro;
using UnityEngine;
using UnityEngine.EventSystems;
using UnityEngine.UI;

namespace Abyss.UI
{
    /// <summary>
    /// Title screen over the live night town: a dark slanted panel with the title block on the left, a coral / cyan
    /// slash, and a diagonal stack of slanted menu plates on the right (selected plate coral with a white offset shadow).
    /// </summary>
    public sealed class GameTitleScreen : UIScreen
    {
        public Action NewGame, ContinueGame, Settings, Credits, Quit;
        public bool HasSave;
        /// <summary>Latest save at a glance ("1-3 변전실 · Lv.4"); empty when unknown.</summary>
        public string ContinueDetail;
        public override bool CloseOnCancel => false;

        readonly List<TitlePlate> plates = new List<TitlePlate>();
        RectTransform backdrop, slash, titleBlock, footer;
        int focus;
        float u;

        protected override void Build()
        {
            bool compact = UIRoot.Compact;
            u = Mathf.Max(1f, Rect.rect.height) / 720f;
            float left = 72f * u;

            // Readability over the 3D town: slanted dark panel on the left, a soft shade on the right behind the menu.
            backdrop = UIFactory.Rect(Rect, "Backdrop");
            backdrop.Place(UIAnchor.Left, new Vector2(0f, 0.5f), new Vector2(-420f * u, 0f), new Vector2(1200f * u, Rect.rect.height + 200f));
            var panel = UIFactory.Image(backdrop, UISprites.White, UISlant.Band.WithAlpha(0.9f), "Night panel");
            panel.rectTransform.Stretch();
            panel.gameObject.AddComponent<UISkew>().SetGradient(new Color(1f, 1f, 1f, 0.72f));
            var shade = UIFactory.Image(Rect, UISprites.GradientH, UISlant.Night.WithAlpha(0.6f), "Menu shade");
            shade.rectTransform.anchorMin = new Vector2(0.55f, 0f); shade.rectTransform.anchorMax = new Vector2(1f, 1f);
            shade.rectTransform.offsetMin = new Vector2(0f, -100f); shade.rectTransform.offsetMax = new Vector2(400f, 100f);

            slash = UIFactory.Rect(Rect, "Slash");
            slash.Place(UIAnchor.Left, new Vector2(0f, 0.5f), new Vector2(520f * u, 0f), new Vector2(158f * u, Rect.rect.height + 200f));
            var coral = UIFactory.Image(slash, UISprites.White, UISlant.Coral.WithAlpha(0.94f), "Coral slash");
            coral.rectTransform.Stretch(0f, 0f, 50f * u, 0f);
            coral.gameObject.AddComponent<UISkew>();
            var cyan = UIFactory.Image(slash, UISprites.White, UISlant.Cyan, "Cyan slash");
            cyan.rectTransform.anchorMin = new Vector2(1f, 0f); cyan.rectTransform.anchorMax = Vector2.one;
            cyan.rectTransform.pivot = new Vector2(1f, 0.5f);
            cyan.rectTransform.sizeDelta = new Vector2(18f * u, 0f); cyan.rectTransform.anchoredPosition = Vector2.zero;
            cyan.gameObject.AddComponent<UISkew>();

            // Title block.
            titleBlock = UIFactory.Rect(Rect, "Title block");
            titleBlock.Place(UIAnchor.TopLeft, new Vector2(left, -(compact ? 70f : 96f) * u), new Vector2(760f * u, 340f * u));
            var eyebrow = UISlant.Eyebrow(titleBlock, "ABYSS GATE", 18f * u, UISlant.Cyan, 45f);
            eyebrow.rectTransform.Place(UIAnchor.TopLeft, Vector2.zero, new Vector2(600f * u, 26f * u));
            var title = UIFactory.Label(titleBlock, "심연의\n게이트", 112f * u, UIFont.Title, UISlant.Paper, TextAlignmentOptions.TopLeft, UITextFx.Outline, "Title");
            title.fontStyle = FontStyles.Italic;
            title.lineSpacing = -18f;
            title.rectTransform.Place(UIAnchor.TopLeft, new Vector2(-4f * u, -30f * u), new Vector2(760f * u, 230f * u));
            var dash = UIFactory.Image(titleBlock, UISprites.White, UISlant.Coral, "Motto dash");
            dash.gameObject.AddComponent<UISkew>();
            dash.rectTransform.Place(UIAnchor.TopLeft, new Vector2(2f * u, -284f * u), new Vector2(48f * u, 6f * u));
            var motto = UIFactory.Label(titleBlock, "E급 헌터에서 S급까지, 게이트 너머로.", 18f * u, UIFont.Heavy, UISlant.Paper, TextAlignmentOptions.MidlineLeft, UITextFx.Shadow, "Motto");
            motto.rectTransform.Place(UIAnchor.TopLeft, new Vector2(62f * u, -272f * u), new Vector2(680f * u, 30f * u));

            BuildMenu(compact);

            // Footer: facts about the content, then the build version.
            footer = UIFactory.Rect(Rect, "Footer");
            footer.Place(UIAnchor.BottomLeft, new Vector2(left, 30f * u), new Vector2(900f * u, 24f * u));
            var facts = UIFactory.Label(footer, "헌터 20명 · 12개 구역 · 붉은 게이트", 13f * u, UIFont.Bold, UISlant.Muted, TextAlignmentOptions.MidlineLeft, UITextFx.Shadow, "Facts");
            float fw = facts.GetPreferredValues(facts.text).x;
            facts.rectTransform.Place(UIAnchor.Left, Vector2.zero, new Vector2(fw + 4f, 24f * u));
            var dot = UIFactory.Image(footer, UISprites.White, UISlant.Muted, "Dot");
            dot.rectTransform.Place(UIAnchor.Left, new Vector2(fw + 14f * u, 0f), new Vector2(4f * u, 4f * u));
            UISlant.Eyebrow(footer, "VER " + Application.version, 13f * u, UISlant.Muted, 20f, "Version")
                .rectTransform.Place(UIAnchor.Left, new Vector2(fw + 30f * u, 0f), new Vector2(300f * u, 24f * u));

            var gate = UIFactory.Label(Rect, "GATE", 64f * u, UIFont.Heavy, UISlant.Band.WithAlpha(0.85f), TextAlignmentOptions.BottomRight, UITextFx.Plain, "Watermark");
            gate.characterSpacing = 5f;
            gate.rectTransform.Place(UIAnchor.BottomRight, new Vector2(-64f * u, 20f * u), new Vector2(400f * u, 80f * u));

            if (!UIRoot.TouchFirst)
            {
                var hints = UIFactory.Rect(Rect, "Key hints");
                hints.Place(UIAnchor.BottomRight, new Vector2(-64f * u, 100f * u), new Vector2(600f * u, 30f * u));
                var line = UIFactory.Label(hints, "↑↓ 이동 · Enter / Space / Z 선택", 13f * u, UIFont.Bold, UISlant.Muted, TextAlignmentOptions.MidlineRight, UITextFx.Shadow, "Keys");
                line.rectTransform.Stretch();
            }
        }

        void BuildMenu(bool compact)
        {
            bool showQuit = !UIRoot.TouchFirst && Application.platform != RuntimePlatform.WebGLPlayer;
            float touch = UIRoot.TouchFirst ? UIRoot.TouchTargetHeight : 0f;
            float bigH = Mathf.Max(64f * u, touch + 12f), smallH = Mathf.Max(54f * u, touch), gap = 14f * u;
            float right = 64f * u, top = (compact ? 190f : 210f) * u;
            float[] widths = { 400f, 360f, 330f, 300f, 270f };
            float[] shifts = { -36f, -18f, 0f, 14f, 28f };
            var rows = new List<(string label, Action action, bool enabled, string detail, string reason)>();
            if (HasSave)
            {
                rows.Add(("이어하기", () => ContinueGame?.Invoke(), true, ContinueDetail, null));
                rows.Add(("새로운 시작", () => NewGame?.Invoke(), true, null, null));
            }
            else
            {
                rows.Add(("새로운 시작", () => NewGame?.Invoke(), true, null, null));
                rows.Add(("이어하기", () => ContinueGame?.Invoke(), false, "저장 없음", "저장된 기록이 없습니다. 새로 시작해 주세요."));
            }
            rows.Add(("설정", () => Settings?.Invoke(), true, null, null));
            rows.Add(("제작진", () => Credits?.Invoke(), true, null, null));
            // iOS apps may not quit themselves; phones and browsers leave with the home/back gesture or by closing the tab.
            if (showQuit) rows.Add(("게임 종료", () => Quit?.Invoke(), true, null, null));
            float y = -top;
            for (int i = 0; i < rows.Count; i++)
            {
                var row = rows[i];
                bool primary = i == 0;
                float h = primary ? bigH : smallH;
                float w = widths[Mathf.Min(i, widths.Length - 1)] * u * (compact ? 1.08f : 1f);
                var plate = TitlePlate.Create(Rect, (i + 1).ToString("00"), row.label, row.detail, new Vector2(w, h), primary, u);
                plate.Rect.Place(UIAnchor.TopRight, new Vector2(-right - shifts[Mathf.Min(i, shifts.Length - 1)] * u, y), new Vector2(w, h));
                plate.Home = plate.Rect.anchoredPosition;
                plate.Interactable = row.enabled;
                plate.DisabledReason = row.reason;
                var action = row.action;
                int index = i;
                plate.Clicked += () => action();
                plate.Hovered += () => SetFocus(index, true);
                plates.Add(plate);
                y -= h + gap;
            }
            SetFocus(0, true);
        }

        void SetFocus(int index, bool silent)
        {
            if (plates.Count == 0) return;
            index = (index % plates.Count + plates.Count) % plates.Count;
            if (index != focus && !silent) UISound.Play(UISoundId.Move);
            focus = index;
            for (int i = 0; i < plates.Count; i++) plates[i].Focused = i == focus;
        }

        void Update()
        {
            if (!IsTop || plates.Count == 0 || !UIInput.CanReceive(this)) return;
            int step = -UIInput.Navigate.y;
            if (step != 0) SetFocus(focus + step, false);
            if (UIInput.Confirm) { UIInput.Consume(); plates[focus].Click(); }
        }

        protected override UITween AnimateIn()
        {
            bool reduced = UIRoot.Instance != null && UIRoot.Instance.ReducedMotion;
            Group.alpha = 0f;
            Rect.anchoredPosition = Vector2.zero;
            if (!reduced)
            {
                SlideFrom(backdrop, new Vector2(-260f * u, 0f), 0f, 0.28f);
                SlideFrom(slash, new Vector2(-180f * u, 0f), 0.04f, 0.26f);
                SlideFrom(titleBlock, new Vector2(-70f * u, 0f), 0.08f, 0.26f);
                for (int i = 0; i < plates.Count; i++)
                {
                    var plate = plates[i];
                    plate.Rect.anchoredPosition = plate.Home + new Vector2(260f * u, 0f);
                    UITween.Move(plate.Rect, plate.Home, 0.24f, UIEase.OutCubic, 0.1f + i * 0.035f);
                }
            }
            return UITween.Fade(Group, 1f, reduced ? 0.12f : 0.18f, UIEase.OutQuad);
        }

        static void SlideFrom(RectTransform rt, Vector2 offset, float delay, float duration)
        {
            if (rt == null) return;
            var home = rt.anchoredPosition;
            rt.anchoredPosition = home + offset;
            UITween.Move(rt, home, duration, UIEase.OutCubic, delay);
        }
    }

    /// <summary>One slanted title menu plate: index, label, optional detail; coral with a white offset shadow when selected.</summary>
    internal sealed class TitlePlate : MonoBehaviour, IPointerEnterHandler, IPointerExitHandler, IPointerDownHandler, IPointerUpHandler, IPointerClickHandler
    {
        RectTransform visual;
        UISlantPlate plate;
        TextMeshProUGUI index, label, detail;
        bool interactable = true, hover, pressed, focused;
        float nextClickAt, unit;
        public Vector2 Home;
        public string DisabledReason;
        public event Action Clicked, Hovered;
        public RectTransform Rect => (RectTransform)transform;
        static bool Reduced => UIRoot.Instance != null && UIRoot.Instance.ReducedMotion;

        public bool Interactable { get => interactable; set { interactable = value; Paint(true); } }
        public bool Focused
        {
            get => focused;
            set { if (focused == value) return; focused = value; Paint(false); if (value) transform.SetAsLastSibling(); }
        }

        public static TitlePlate Create(Transform parent, string number, string text, string info, Vector2 size, bool primary, float u)
        {
            var rt = UIFactory.Rect(parent, "Menu " + text);
            rt.sizeDelta = size;
            var hit = rt.gameObject.AddComponent<Image>();
            hit.color = Color.clear; hit.raycastTarget = true;
            rt.gameObject.AddComponent<UISkew>();
            var p = rt.gameObject.AddComponent<TitlePlate>();
            p.unit = u;
            // Grow from the right edge, like the battle command stack.
            p.visual = UIFactory.Rect(rt, "Visual");
            p.visual.Place(UIAnchor.Right, Vector2.zero, size);
            p.plate = UISlantPlate.Create(p.visual, "Plate", UISlant.Plate, UISlant.Cyan, 2f, true, 8f * u, false);
            p.plate.Rect.Stretch();
            // The accent becomes a left edge bar.
            var e = p.plate.Edge.rectTransform;
            e.anchorMin = Vector2.zero; e.anchorMax = new Vector2(0f, 1f); e.pivot = new Vector2(0f, 0.5f);
            e.sizeDelta = new Vector2(6f * u, 0f); e.anchoredPosition = Vector2.zero;
            float pad = (primary ? 28f : 26f) * u + size.y * 0.5f * UISkew.Slope;
            p.index = UISlant.Eyebrow(p.visual, number, (primary ? 16f : 15f) * u, UISlant.Cyan, 20f, "Index");
            p.index.rectTransform.Place(UIAnchor.Left, new Vector2(pad, 0f), new Vector2(40f * u, size.y));
            p.label = UIFactory.Label(p.visual, text, (primary ? 30f : 24f) * u, primary ? UIFont.Heavy : UIFont.Bold, UISlant.Paper, TextAlignmentOptions.MidlineLeft, UITextFx.Shadow, "Label");
            float lx = pad + 40f * u;
            float lw = p.label.GetPreferredValues(text).x + 6f;
            p.label.rectTransform.Place(UIAnchor.Left, new Vector2(lx, 0f), new Vector2(lw, size.y));
            p.detail = UIFactory.Label(p.visual, info ?? "", 14f * u, UIFont.Bold, UISlant.Paper, TextAlignmentOptions.MidlineRight, UITextFx.Shadow, "Detail");
            p.detail.overflowMode = TextOverflowModes.Ellipsis;
            p.detail.rectTransform.Stretch(lx + lw + 12f * u, 0f, 22f * u + size.y * 0.5f * UISkew.Slope, 0f);
            p.detail.gameObject.SetActive(!string.IsNullOrEmpty(info));
            p.Paint(true);
            return p;
        }

        public void Click()
        {
            if (Time.unscaledTime < nextClickAt) return;
            nextClickAt = Time.unscaledTime + 0.25f;
            UIInput.Consume();
            if (!interactable)
            {
                UISound.Play(UISoundId.Buzzer);
                if (!string.IsNullOrEmpty(DisabledReason)) UIRoot.Instance?.Toast.Show(DisabledReason, UIToastKind.Warning);
                return;
            }
            UISound.Play(UISoundId.Confirm);
            UITween.Kill(visual);
            visual.localScale = Vector3.one * (Reduced ? 1f : 0.97f);
            UITween.Scale(visual, Reduced ? 1f : focused ? 1.05f : 1f, Reduced ? 0f : 0.14f, UIEase.OutCubic);
            Clicked?.Invoke();
        }

        void Paint(bool instant)
        {
            if (plate == null) return;
            bool lit = (focused || hover) && interactable;
            Color fill = !interactable ? UISlant.Deep.WithAlpha(0.88f) : pressed ? UISlant.CoralDark : lit ? UISlant.Coral : UISlant.Plate.WithAlpha(0.96f);
            Color edge = !interactable ? UISlant.Line : lit ? Color.clear : UISlant.Cyan;
            plate.SetColors(fill, edge);
            UISlant.SetShadow(plate, lit ? UISlant.Paper : (focused ? UISlant.Line : Color.clear), 8f * unit);
            label.color = !interactable ? UITheme.TextDisabled : lit ? Color.white : UISlant.Paper;
            index.color = !interactable ? UITheme.TextDisabled : lit ? Color.white : UISlant.Cyan;
            detail.color = !interactable ? UITheme.TextDisabled : lit ? Color.white : UISlant.Muted;
            float scale = Reduced ? 1f : pressed && interactable ? 0.97f : focused ? 1.05f : 1f;
            UITween.Kill(visual);
            if (instant || !Application.isPlaying) { visual.localScale = new Vector3(scale, scale, 1f); return; }
            // Snappy select: OutBack overshoot stays under 1.08.
            UITween.Scale(visual, scale, Reduced ? 0f : focused ? 0.2f : 0.12f, focused ? UIEase.OutBack : UIEase.OutCubic);
        }

        void OnDisable() { hover = pressed = false; }
        public void OnPointerEnter(PointerEventData e) { hover = true; Paint(false); Hovered?.Invoke(); }
        public void OnPointerExit(PointerEventData e) { hover = false; pressed = false; Paint(false); }
        public void OnPointerDown(PointerEventData e) { if (e.button == PointerEventData.InputButton.Left) { pressed = true; Paint(false); } }
        public void OnPointerUp(PointerEventData e) { pressed = false; Paint(false); }
        public void OnPointerClick(PointerEventData e)
        {
            if (e.button != PointerEventData.InputButton.Left || !UIInput.CanReceive(this)) return;
            Click();
        }
    }
}
