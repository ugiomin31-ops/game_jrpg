using System;
using System.Collections.Generic;
using Abyss.Logic.Game;
using TMPro;
using UnityEngine;

namespace Abyss.UI
{
    /// <summary>
    /// Town HUD in the slanted exploration style (town_hud pick candidate_A): guild badge + area plate, gold chip and the
    /// objective / readiness ribbon (top left), the guild facilities as a stack of slanted plates with the coral gate
    /// departure on top (right), slim party plates (bottom left) and the 모험 수첩 key with input hints (bottom right).
    /// Only the plates take pointer input: the gaps keep the town's right-half look drag (UITouch ignores touches over UI).
    /// </summary>
    public sealed partial class GameUI
    {
        /// <summary>Facility plates, top to bottom: id, title text key (or literal), sub-line text key (empty = none).</summary>
        static readonly (string Id, string Title, string Sub)[] TownFacilities =
        {
            ("gate", "menu_depart", "menu_depart_sub"),
            ("innkeeper", "menu_inn", "menu_inn_sub"),
            ("shopkeeper", "menu_shop", "menu_shop_sub"),
            ("smith", "menu_smithy", "menu_smithy_sub"),
            ("guild_clerk", "menu_guild", "menu_guild_sub"),
            ("bestiary", "menu_bestiary", "menu_bestiary_sub"),
            ("party", "menu_party", "menu_party_sub"),
            ("elder", "길드장실", ""),
        };

        RectTransform townReadyStrip;
        TextMeshProUGUI townBadge;

        void BuildTownHud()
        {
            bool touch = TouchFirst;
            float u = hudUnit = Mathf.Max(1f, hud.rect.height) / 720f;
            float target = touch ? UIRoot.TouchTargetHeight : 0f;

            // ---- top left: guild badge, area plate, gold chip, objective + readiness ribbon ---------------------
            var topLeft = UIFactory.Rect(hud, "Guild cluster");
            topLeft.Place(UIAnchor.TopLeft, Vector2.zero, new Vector2(780f * u, 300f * u));
            townPanel = topLeft;
            areaPlate = UISlantPlate.Create(topLeft, "Area plate", UISlant.Deep.WithAlpha(0.94f), UISlant.Cyan, 2f * u, true, 5f * u, false).Rect;
            areaPlate.Place(UIAnchor.TopLeft, new Vector2(108f * u, -24f * u), new Vector2(320f * u, 76f * u));
            area = UIFactory.Label(areaPlate, "", 30f * u, UIFont.Title, UISlant.Paper, TextAlignmentOptions.MidlineLeft, UITextFx.Shadow, "Guild name");
            area.overflowMode = TextOverflowModes.Ellipsis;
            area.rectTransform.Stretch(34f * u, 8f * u, 30f * u, 30f * u);
            resources = UIFactory.Label(areaPlate, "", 13f * u, UIFont.Bold, UISlant.Muted, TextAlignmentOptions.MidlineLeft, UITextFx.Plain, "Guild facts");
            resources.overflowMode = TextOverflowModes.Ellipsis;
            resources.rectTransform.Stretch(30f * u, 46f * u, 30f * u, 10f * u);
            var badge = UISlantPlate.Create(topLeft, "Rank badge", UISlant.Coral, UISlant.Rest, 2f, true, 5f * u, false);
            UISlant.SetShadow(badge, UISlant.Night.WithAlpha(0.8f), 5f * u);
            badge.Rect.Place(UIAnchor.TopLeft, new Vector2(-14f * u, -24f * u), new Vector2(132f * u, 76f * u));
            UISlant.Eyebrow(badge.Rect, "RANK", 10f * u, Color.white, 30f).rectTransform.TopStrip(18f * u, 6f * u, 30f * u, 10f * u);
            townBadge = UIFactory.Label(badge.Rect, "", 40f * u, UIFont.Heavy, Color.white, TextAlignmentOptions.Center, UITextFx.Plain, "Rank");
            townBadge.enableAutoSizing = true; townBadge.fontSizeMax = 40f * u; townBadge.fontSizeMin = 22f * u;
            townBadge.rectTransform.Stretch(26f * u, 18f * u, 10f * u, 2f * u);

            chipRow = UIFactory.Rect(topLeft, "Resource chips");
            chipRow.Place(UIAnchor.TopLeft, new Vector2(24f * u, -112f * u), new Vector2(600f * u, 30f * u));
            goldChip = UISlant.Chip(chipRow, "Gold", UISlant.Amber, 13f * u, 30f * u);
            ((RectTransform)goldChip.transform.parent).Place(UIAnchor.Left, Vector2.zero, new Vector2(120f * u, 30f * u));

            objectiveStrip = UIFactory.Rect(topLeft, "Objective");
            objectiveStrip.Place(UIAnchor.TopLeft, new Vector2(24f * u, -154f * u), new Vector2(300f * u, 52f * u));
            Ribbon(objectiveStrip, "OBJECTIVE", UISlant.Coral, u);
            townObjective = UIFactory.Label(objectiveStrip, "", 14f * u, UIFont.Heavy, UISlant.Paper, TextAlignmentOptions.MidlineLeft, UITextFx.Plain, "Objective text");
            townObjective.overflowMode = TextOverflowModes.Ellipsis;
            townObjective.rectTransform.Stretch(14f * u, 22f * u, 14f * u, 6f * u);

            townReadyStrip = UIFactory.Rect(topLeft, "Readiness");
            townReadyStrip.Place(UIAnchor.TopLeft, new Vector2(24f * u, -212f * u), new Vector2(300f * u, 70f * u));
            Ribbon(townReadyStrip, "READY", UISlant.Cyan, u);
            townReadiness = UIFactory.Label(townReadyStrip, "", 14f * u, UIFont.Heavy, UITheme.Positive, TextAlignmentOptions.MidlineLeft, UITextFx.Plain, "Departure readiness");
            townReadiness.overflowMode = TextOverflowModes.Ellipsis;
            townReadiness.rectTransform.TopStrip(20f * u, 24f * u, 14f * u, 14f * u);
            townIssues = UIFactory.Label(townReadyStrip, "", 12f * u, UIFont.Bold, UISlant.Muted, TextAlignmentOptions.TopLeft, UITextFx.Plain, "Readiness notes");
            townIssues.overflowMode = TextOverflowModes.Ellipsis;
            townIssues.rectTransform.Stretch(14f * u, 46f * u, 14f * u, 4f * u);

            // ---- right: facility stack (coral gate departure on top) ------------------------------------------
            float plateW = (UIRoot.Compact ? 300f : 320f) * u, plateH = Mathf.Max(50f * u, target), gap = 6f * u;
            var stack = UIFactory.Rect(hud, "Guild facilities");
            stack.Place(UIAnchor.TopRight, new Vector2(-24f * u, -24f * u), new Vector2(plateW, TownFacilities.Length * (plateH + gap) - gap));
            for (int i = 0; i < TownFacilities.Length; i++)
            {
                var (id, titleKey, subKey) = TownFacilities[i];
                string title = titleKey.StartsWith("menu_", StringComparison.Ordinal) ? T(titleKey, id) : titleKey;
                string sub = string.IsNullOrEmpty(subKey) ? "" : T(subKey, "");
                bool gate = id == "gate";
                var plate = FacilityPlate(stack, id, title, sub, plateW, plateH, u, touch, gate);
                // A gentle stair-step to the left as the stack descends (the slant of the plates continues the line).
                plate.Rt().Place(UIAnchor.TopRight, new Vector2(-i * 4f * u, -i * (plateH + gap)), new Vector2(plateW, plateH));
            }

            // ---- bottom right: 모험 수첩 + hints ----------------------------------------------------------------
            float keyH = Mathf.Max(48f * u, target), keyW = 200f * u;
            var notebook = SlantKey(hud, "모험 수첩", new Vector2(keyW, keyH), touch, ShowPause, false);
            // On short screens the stack (whose plates keep their touch height) reaches down to the key: the key then
            // stands just left of the stack, at the same margin, so every plate and the key keep their own hit area.
            float stackBottom = 24f * u + TownFacilities.Length * (plateH + gap) - gap;
            float keyTop = Mathf.Max(1f, hud.rect.height) - 24f * u - keyH;
            float stackLeft = 24f * u + plateW + (TownFacilities.Length - 1) * 4f * u;
            float keyRight = stackBottom + gap > keyTop ? stackLeft + 24f * u : 24f * u;
            notebook.Rt().Place(UIAnchor.BottomRight, new Vector2(-keyRight, 24f * u), new Vector2(keyW, keyH));
            padPanel = notebook.Rt();
            padReserveExtra = keyRight - 24f * u;   // FitHud keeps the party row clear of the key wherever it stands
            string help = touch
                ? "이동 · 왼쪽 끌기  ·  시점 · 오른쪽 끌기 / 두 손가락  ·  대화 · 근처에서 탭"
                : "이동 WASD · 시점 Q/E · 우클릭 드래그 · 휠  ·  대화 E  ·  수첩 Tab";
            var hints = UIFactory.Label(hud, help, 12f * u, UIFont.Bold, UISlant.Muted, touch ? TextAlignmentOptions.BottomLeft : TextAlignmentOptions.BottomRight, UITextFx.Shadow, "Key hints");
            // Touch: the facility stack reaches the 모험 수첩 key on phones, so the gesture line sits above the party plates.
            if (touch) hints.rectTransform.Place(UIAnchor.BottomLeft, new Vector2(24f * u, 22f * u + 74f * u * (UIRoot.Compact ? 1.2f : 1f) + 8f * u), new Vector2(760f * u, 20f * u));
            else hints.rectTransform.Place(UIAnchor.BottomRight, new Vector2(-24f * u, 24f * u + keyH + 8f * u), new Vector2(760f * u, 20f * u));

            // ---- bottom left: slim party plates (same as the exploration HUD) ---------------------------------
            float k = UIRoot.Compact ? 1.2f : 1f;
            float pw = 196f * u * k, ph = 74f * u * k, pgap = 10f * u;
            int count = app.State.Party.Count;
            partyRow = UIFactory.Rect(hud, "Party Row");
            partyRow.Place(UIAnchor.BottomLeft, new Vector2(20f * u, 22f * u), new Vector2(Mathf.Max(1, count) * (pw + pgap) - pgap, ph));
            for (int i = 0; i < count; i++) heroHud.Add(PartyPlate(app.State.Party[i], i, pw, ph, pgap, u * k));

            AnimateTownHudIn(u, topLeft, stack, notebook.Rt(), partyRow);
        }

        /// <summary>A navy ribbon with a coloured top rule and an eyebrow (the dungeon objective strip style).</summary>
        static void Ribbon(RectTransform strip, string eyebrow, Color accent, float u)
        {
            UIFactory.Fill(strip, UISlant.Deep.WithAlpha(0.86f), "Fill");
            var rule = UIFactory.Image(strip, UISprites.White, accent, "Rule");
            rule.rectTransform.anchorMin = new Vector2(0f, 1f); rule.rectTransform.anchorMax = Vector2.one;
            rule.rectTransform.pivot = new Vector2(0.5f, 1f); rule.rectTransform.sizeDelta = new Vector2(0f, 2f * u); rule.rectTransform.anchoredPosition = Vector2.zero;
            UISlant.Eyebrow(strip, eyebrow, 11f * u, accent, 30f).rectTransform.TopStrip(18f * u, 5f * u, 14f * u, 14f * u);
        }

        /// <summary>One facility plate: portrait icon, heavy title and a muted sub line; the gate departure is coral.</summary>
        UISlantButton FacilityPlate(RectTransform parent, string id, string title, string sub, float w, float h, float u, bool touch, bool gate)
        {
            var b = UISlantButton.Create(parent, "Facility " + id, new Vector2(w, h), UISlantKind.Simple, touch, TownArtwork(id));
            b.SetLabel(title);
            b.FocusScale = 1.04f;
            if (gate) { b.SetColors(UISlant.Coral, Color.white, UITheme.Hex("ff7591")); UISlant.SetShadow(b.Plate, UISlant.Night, 5f * u); }
            else b.SetColors(UISlant.Plate.WithAlpha(0.94f), UISlant.Paper);
            float icon = b.Icon != null && b.Icon.enabled ? h - 16f * u : 0f;
            if (b.Icon != null && b.Icon.enabled) b.Icon.rectTransform.Place(UIAnchor.Left, new Vector2(18f * u, 0f), new Vector2(icon, icon));
            float left = 18f * u + (icon > 0f ? icon + 12f * u : 6f * u), right = 18f * u + h * 0.5f * UISkew.Slope;
            var label = b.Label;
            label.alignment = string.IsNullOrEmpty(sub) ? TextAlignmentOptions.MidlineLeft : TextAlignmentOptions.BottomLeft;
            label.enableAutoSizing = true; label.fontSizeMax = 21f * u; label.fontSizeMin = 14f * u;
            label.font = UITheme.Font(UIFont.Heavy);
            label.rectTransform.anchorMin = Vector2.zero; label.rectTransform.anchorMax = Vector2.one;
            label.rectTransform.offsetMin = new Vector2(left, string.IsNullOrEmpty(sub) ? 0f : h * 0.42f);
            label.rectTransform.offsetMax = new Vector2(-right, string.IsNullOrEmpty(sub) ? 0f : -2f * u);
            if (!string.IsNullOrEmpty(sub))
            {
                var s = UIFactory.Label(b.Visual, sub, 12f * u, UIFont.Bold, gate ? new Color(1f, 1f, 1f, 0.85f) : UISlant.Muted, TextAlignmentOptions.TopLeft, UITextFx.Plain, "Sub");
                s.overflowMode = TextOverflowModes.Ellipsis;
                s.rectTransform.anchorMin = Vector2.zero; s.rectTransform.anchorMax = Vector2.one;
                s.rectTransform.offsetMin = new Vector2(left, 2f * u);
                s.rectTransform.offsetMax = new Vector2(-right, -h * 0.6f);
            }
            b.Clicked += () => { if (!BlocksWorldInput) ShowTownService(id); };
            return b;
        }

        void AnimateTownHudIn(float u, params RectTransform[] parts)
        {
            if (root.ReducedMotion || !Application.isPlaying) return;
            Vector2[] from = { new Vector2(-120f * u, 0f), new Vector2(140f * u, 0f), new Vector2(140f * u, 0f), new Vector2(0f, -120f * u) };
            for (int i = 0; i < parts.Length; i++)
            {
                var rt = parts[i];
                if (rt == null) continue;
                var home = rt.anchoredPosition;
                rt.anchoredPosition = home + from[Mathf.Min(i, from.Length - 1)];
                UITween.Move(rt, home, 0.26f, UIEase.OutCubic, 0.03f * i);
            }
        }

        /// <summary>Header text, chips and ribbon widths for the town HUD (data only; layout hugs the text).</summary>
        void RefreshTownHud()
        {
            if (areaPlate == null || area == null) return;
            float u = hudUnit;
            area.text = T("town", "새벽 길드");
            resources.text = $"최심부 {DeepestLabel}  ·  {DifficultyName(app.State.Difficulty)}";
            townBadge.text = GameFlow.GuildRank(app.State).ToString();
            float textW = Mathf.Max(area.GetPreferredValues(area.text).x, resources.GetPreferredValues(resources.text).x);
            areaPlate.sizeDelta = new Vector2(Mathf.Clamp(textW + 70f * u, 240f * u, 460f * u), areaPlate.sizeDelta.y);
            UISlant.FitChip(goldChip, GoldLine);
        }

        /// <summary>Objective and readiness ribbons, sized to their text.</summary>
        void RefreshTownRibbons(string objective, string readiness, Color readinessColor, string issues)
        {
            float u = hudUnit;
            objectiveStrip.gameObject.SetActive(!string.IsNullOrEmpty(objective));
            townObjective.text = objective ?? "";
            if (!string.IsNullOrEmpty(objective))
                objectiveStrip.sizeDelta = new Vector2(Mathf.Clamp(townObjective.GetPreferredValues(objective).x + 30f * u, 240f * u, 460f * u), objectiveStrip.sizeDelta.y);
            townReadiness.text = readiness; townReadiness.color = readinessColor;
            townIssues.text = issues;
            float w = Mathf.Max(townReadiness.GetPreferredValues(readiness).x, townIssues.GetPreferredValues(issues).x) + 30f * u;
            townReadyStrip.sizeDelta = new Vector2(Mathf.Clamp(w, 240f * u, 460f * u), townReadyStrip.sizeDelta.y);
            // No objective: the readiness ribbon moves up into its place.
            townReadyStrip.anchoredPosition = new Vector2(townReadyStrip.anchoredPosition.x, (string.IsNullOrEmpty(objective) ? -154f : -212f) * u);
        }
    }
}
