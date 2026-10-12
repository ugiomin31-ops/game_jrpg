using System;
using System.Collections.Generic;
using Abyss.Logic;
using Abyss.Logic.Dungeon;
using Abyss.Logic.Game;
using TMPro;
using UnityEngine;
using UnityEngine.EventSystems;
using UnityEngine.UI;

namespace Abyss.UI
{
    /// <summary>
    /// Exploration HUD: slanted floor badge + area plate, resource chips and objective (top left), compass (top
    /// centre), minimap with 지도 / 캠프 (top right), a slanted movement cluster (bottom right) and slim party plates
    /// (bottom left). Area / floor transition cards are built here too.
    /// </summary>
    public sealed partial class GameUI
    {
        static readonly string[] CompassLetters = { "N", "E", "S", "W" };

        TextMeshProUGUI floorBadge, areaName, areaSub, goldChip, keyChip, objectiveText, mapFloor;
        RectTransform areaPlate, chipRow, objectiveStrip, compassStrip;
        readonly TextMeshProUGUI[] compass = new TextMeshProUGUI[3];
        int compassFacing = -1;
        float hudUnit = 1.5f;

        void ClearDungeonHud()
        {
            floorBadge = areaName = areaSub = goldChip = keyChip = objectiveText = mapFloor = null;
            areaPlate = chipRow = objectiveStrip = compassStrip = null;
            compass[0] = compass[1] = compass[2] = null;
            compassFacing = -1;
        }

        void BuildDungeonHud()
        {
            bool touch = TouchFirst;
            float u = hudUnit = Mathf.Max(1f, hud.rect.height) / 720f;
            float target = touch ? UIRoot.TouchTargetHeight : 0f;

            // ---- top left: floor badge, area plate, chips, objective -----------------------------------------
            var topLeft = UIFactory.Rect(hud, "Area cluster");
            topLeft.Place(UIAnchor.TopLeft, Vector2.zero, new Vector2(760f * u, 280f * u));
            areaPlate = UISlantPlate.Create(topLeft, "Area plate", UISlant.Deep.WithAlpha(0.94f), UISlant.Cyan, 2f * u, true, 5f * u, false).Rect;
            areaPlate.Place(UIAnchor.TopLeft, new Vector2(108f * u, -24f * u), new Vector2(320f * u, 76f * u));
            areaName = UIFactory.Label(areaPlate, "", 30f * u, UIFont.Title, UISlant.Paper, TextAlignmentOptions.MidlineLeft, UITextFx.Shadow, "Area name");
            areaName.overflowMode = TextOverflowModes.Ellipsis;
            areaName.rectTransform.Stretch(34f * u, 8f * u, 30f * u, 30f * u);
            areaSub = UIFactory.Label(areaPlate, "", 13f * u, UIFont.Bold, UISlant.Muted, TextAlignmentOptions.MidlineLeft, UITextFx.Plain, "Area sub");
            areaSub.overflowMode = TextOverflowModes.Ellipsis;
            areaSub.rectTransform.Stretch(30f * u, 46f * u, 30f * u, 10f * u);
            var badge = UISlantPlate.Create(topLeft, "Floor badge", UISlant.Coral, UISlant.Rest, 2f, true, 5f * u, false);
            UISlant.SetShadow(badge, UISlant.Night.WithAlpha(0.8f), 5f * u);
            badge.Rect.Place(UIAnchor.TopLeft, new Vector2(-14f * u, -24f * u), new Vector2(132f * u, 76f * u));
            floorBadge = UIFactory.Label(badge.Rect, "", 44f * u, UIFont.Heavy, Color.white, TextAlignmentOptions.Center, UITextFx.Plain, "Floor");
            floorBadge.enableAutoSizing = true; floorBadge.fontSizeMax = 44f * u; floorBadge.fontSizeMin = 26f * u;
            floorBadge.rectTransform.Stretch(26f * u, 4f * u, 10f * u, 4f * u);

            chipRow = UIFactory.Rect(topLeft, "Resource chips");
            chipRow.Place(UIAnchor.TopLeft, new Vector2(24f * u, -112f * u), new Vector2(600f * u, 30f * u));
            goldChip = UISlant.Chip(chipRow, "Gold", UISlant.Amber, 13f * u, 30f * u);
            ((RectTransform)goldChip.transform.parent).Place(UIAnchor.Left, Vector2.zero, new Vector2(120f * u, 30f * u));
            keyChip = UISlant.Chip(chipRow, "Keys", UISlant.Cyan, 13f * u, 30f * u);
            ((RectTransform)keyChip.transform.parent).Place(UIAnchor.Left, new Vector2(130f * u, 0f), new Vector2(80f * u, 30f * u));

            objectiveStrip = UIFactory.Rect(topLeft, "Objective");
            objectiveStrip.Place(UIAnchor.TopLeft, new Vector2(24f * u, -154f * u), new Vector2(300f * u, 52f * u));
            UIFactory.Fill(objectiveStrip, UISlant.Deep.WithAlpha(0.86f), "Fill");
            var rule = UIFactory.Image(objectiveStrip, UISprites.White, UISlant.Coral, "Rule");
            rule.rectTransform.anchorMin = new Vector2(0f, 1f); rule.rectTransform.anchorMax = Vector2.one;
            rule.rectTransform.pivot = new Vector2(0.5f, 1f); rule.rectTransform.sizeDelta = new Vector2(0f, 2f * u); rule.rectTransform.anchoredPosition = Vector2.zero;
            UISlant.Eyebrow(objectiveStrip, "OBJECTIVE", 11f * u, UISlant.Coral, 30f).rectTransform.Stretch(14f * u, 7f * u, 14f * u, 30f * u);
            objectiveText = UIFactory.Label(objectiveStrip, "", 14f * u, UIFont.Heavy, UISlant.Paper, TextAlignmentOptions.MidlineLeft, UITextFx.Plain, "Objective text");
            objectiveText.overflowMode = TextOverflowModes.Ellipsis;
            objectiveText.rectTransform.Stretch(14f * u, 22f * u, 14f * u, 6f * u);

            // ---- top centre: compass --------------------------------------------------------------------------
            compassStrip = UIFactory.Rect(hud, "Compass");
            compassStrip.Place(UIAnchor.Top, new Vector2(0f, -22f * u), new Vector2(340f * u, 30f * u));
            UIFactory.Fill(compassStrip, UISlant.Deep.WithAlpha(0.86f), "Fill");
            string[] slots = { "L", "·", "·", "C", "·", "·", "R" };
            for (int i = 0; i < slots.Length; i++)
            {
                bool centre = slots[i] == "C", dot = slots[i] == "·";
                var t = UIFactory.Label(compassStrip, dot ? "·" : "", centre ? 18f * u : 13f * u, UIFont.Heavy, centre ? UISlant.Paper : UISlant.Muted,
                    TextAlignmentOptions.Center, UITextFx.Plain, centre ? "Heading" : dot ? "Tick" : "Side");
                t.rectTransform.anchorMin = new Vector2((i + 0.5f) / slots.Length, 0f); t.rectTransform.anchorMax = new Vector2((i + 0.5f) / slots.Length, 1f);
                t.rectTransform.sizeDelta = new Vector2(40f * u, 0f); t.rectTransform.anchoredPosition = Vector2.zero;
                if (slots[i] == "L") compass[0] = t; else if (centre) compass[1] = t; else if (slots[i] == "R") compass[2] = t;
            }
            var pointer = UIPolygon.Create(compassStrip, "Pointer", UIPolygon.Down, UISlant.Coral);
            pointer.rectTransform.Place(UIAnchor.Bottom, new Vector2(0.5f, 1f), Vector2.zero, new Vector2(12f * u, 8f * u));

            // ---- top right: minimap, 지도 / 캠프 -------------------------------------------------------------
            float mapSize = 220f * u;
            var mapPanel = UIFactory.Rect(hud, "Minimap");
            mapPanel.Place(UIAnchor.TopRight, new Vector2(-24f * u, -24f * u), new Vector2(mapSize, mapSize));
            var mapFill = UIFactory.Fill(mapPanel, UISlant.Deep.WithAlpha(0.9f), "Fill", raycast: true);
            Border(mapPanel, UISlant.Line, 2f * u);
            UISlant.Eyebrow(mapPanel, "MAP", 11f * u, UISlant.Cyan, 30f).rectTransform.TopStrip(24f * u, 4f * u, 10f * u, 10f * u);
            mapFloor = UIFactory.Label(mapPanel, "", 11f * u, UIFont.Heavy, UISlant.Cyan, TextAlignmentOptions.MidlineRight, UITextFx.Plain, "Floor");
            mapFloor.characterSpacing = 20f;
            mapFloor.rectTransform.TopStrip(24f * u, 4f * u, 10f * u, 10f * u);
            var mapView = UIFactory.Rect(mapPanel, "Minimap view").Stretch(8f * u, 28f * u, 8f * u, 8f * u);
            mapView.gameObject.AddComponent<RectMask2D>();
            minimap = UIFactory.Add<DungeonMapGraphic>(mapView, "Explored minimap");
            minimap.Rt().Stretch();
            // Zoomed around the party: 9 cells across reads clearly at phone size.
            minimap.Window = 9;
            // Tapping/clicking the minimap opens the full map.
            var mapHit = mapPanel.gameObject.AddComponent<Button>();
            mapHit.targetGraphic = mapFill;
            mapHit.transition = Selectable.Transition.None;
            mapHit.navigation = new Navigation { mode = Navigation.Mode.None };
            mapHit.onClick.AddListener(() => { if (!BlocksWorldInput) OpenMapFromHud(); });
            float toolH = Mathf.Max(44f * u, target), toolW = (mapSize - 8f * u) * 0.5f;
            var mapButton = SlantKey(hud, "지도", new Vector2(toolW, toolH), touch, OpenMapFromHud, false);
            mapButton.Rt().Place(UIAnchor.TopRight, new Vector2(-24f * u - toolW - 8f * u, -24f * u - mapSize - 10f * u), new Vector2(toolW, toolH));
            var campButton = SlantKey(hud, "캠프", new Vector2(toolW, toolH), touch, ShowPause, false);
            campButton.Rt().Place(UIAnchor.TopRight, new Vector2(-24f * u, -24f * u - mapSize - 10f * u), new Vector2(toolW, toolH));

            // ---- bottom right: movement cluster --------------------------------------------------------------
            float gap = 10f * u, drop = 30f * u;
            float side = Mathf.Max(100f * u, target * 1.2f), mid = Mathf.Max(110f * u, target * 1.3f);
            float r1 = Mathf.Max(66f * u, target), r2 = Mathf.Max(60f * u, target), r3 = Mathf.Max(52f * u, target);
            float padW = side * 2f + mid + gap * 2f, padH = drop + r1 + gap + r2 + gap + r3;
            padPanel = UIFactory.Rect(hud, "Movement pad");
            padPanel.Place(UIAnchor.BottomRight, new Vector2(-36f * u, 30f * u), new Vector2(padW, padH));
            float xL = 0f, xM = side + gap, xR = side + gap + mid + gap;
            float yRow2 = drop + r1 + gap, yRow3 = yRow2 + r2 + gap;
            var forward = PadArrow.Create(padPanel, "전진", touch, u);
            forward.Rt().Place(UIAnchor.TopLeft, new Vector2(xM, 0f), new Vector2(mid, drop + r1));
            forward.HoldRepeat = 0.28f;
            forward.Clicked += () => PadAction(() => app.MoveDungeon(RelativeMove.Forward));
            PadKey("↺ 회전", xL, drop, side, r1, () => app.TurnDungeon(-1), true, touch);
            PadKey("회전 ↻", xR, drop, side, r1, () => app.TurnDungeon(1), true, touch);
            PadKey("◀ 옆", xL, yRow2, side, r2, () => app.MoveDungeon(RelativeMove.Left), true, touch);
            var search = PadKey("조사", xM, yRow2, mid, r2, app.InteractDungeon, false, touch);
            search.SetColors(UISlant.Coral, Color.white, UITheme.Hex("ff7591"));
            UISlant.SetShadow(search.Plate, UISlant.Night, 5f * u);
            search.Label.font = UITheme.Font(UIFont.Heavy);
            PadKey("옆 ▶", xR, yRow2, side, r2, () => app.MoveDungeon(RelativeMove.Right), true, touch);
            PadKey("▼ 후퇴", xM, yRow3, mid, r3, () => app.MoveDungeon(RelativeMove.Back), true, touch);
            var wait = PadKey("대기", xR, yRow3, side, r3, app.WaitDungeon, false, touch);
            wait.SetColors(UISlant.Deep.WithAlpha(0.94f), UISlant.Muted);
            if (!touch)
            {
                var keys = UIFactory.Label(hud, "W/S 전진·후퇴 · A/D 회전 · Q/R 옆 · E 조사 · . 대기 · M 지도 · Tab 캠프", 12f * u, UIFont.Bold, UISlant.Muted,
                    TextAlignmentOptions.BottomRight, UITextFx.Shadow, "Key hints");
                keys.rectTransform.Place(UIAnchor.BottomRight, new Vector2(-36f * u, 30f * u + padH + 8f * u), new Vector2(900f * u, 20f * u));
            }

            // ---- bottom left: slim party plates --------------------------------------------------------------
            float k = UIRoot.Compact ? 1.2f : 1f;
            float pw = 196f * u * k, ph = 74f * u * k, pgap = 10f * u;
            int count = app.State.Party.Count;
            partyRow = UIFactory.Rect(hud, "Party Row");
            partyRow.Place(UIAnchor.BottomLeft, new Vector2(20f * u, 22f * u), new Vector2(Mathf.Max(1, count) * (pw + pgap) - pgap, ph));
            for (int i = 0; i < count; i++) heroHud.Add(PartyPlate(app.State.Party[i], i, pw, ph, pgap, u * k));

            AnimateHudIn(u, topLeft, compassStrip, mapPanel, mapButton.Rt(), campButton.Rt(), padPanel, partyRow);
        }

        void PadAction(Action action)
        {
            if (BlocksWorldInput) return;
            UIInput.Consume();
            action();
        }

        UISlantButton PadKey(string label, float x, float y, float w, float h, Action action, bool movement, bool touch)
        {
            var b = SlantKey(padPanel, label, new Vector2(w, h), touch, action, movement);
            b.Rt().Place(UIAnchor.TopLeft, new Vector2(x, -y), new Vector2(w, h));
            return b;
        }

        UISlantButton SlantKey(RectTransform parent, string label, Vector2 size, bool touch, Action action, bool movement)
        {
            var b = UISlantButton.Create(parent, "Key " + label, size, UISlantKind.Simple, touch);
            b.SetLabel(label);
            b.SetColors(UISlant.Plate.WithAlpha(0.94f), UISlant.Paper);
            b.FocusScale = 1.04f;
            b.Clicked += () => PadAction(action);
            // Same cadence as a held key (DungeonWorld: 0.28 s); a step animates for 0.24 s.
            if (movement) { b.HoldRepeat = 0.28f; b.Quiet = true; }
            return b;
        }

        static void Border(RectTransform parent, Color color, float width)
        {
            for (int i = 0; i < 4; i++)
            {
                var img = UIFactory.Image(parent, UISprites.White, color, "Border");
                var r = img.rectTransform;
                bool horizontal = i < 2;
                float edge = i % 2 == 0 ? 0f : 1f;
                r.anchorMin = horizontal ? new Vector2(0f, edge) : new Vector2(edge, 0f);
                r.anchorMax = horizontal ? new Vector2(1f, edge) : new Vector2(edge, 1f);
                r.pivot = horizontal ? new Vector2(0.5f, edge) : new Vector2(edge, 0.5f);
                r.sizeDelta = horizontal ? new Vector2(0f, width) : new Vector2(width, 0f);
                r.anchoredPosition = Vector2.zero;
            }
        }

        HeroHud PartyPlate(HeroState hero, int index, float w, float h, float gap, float u)
        {
            var plate = UISlantPlate.Create(partyRow, "Party plate " + hero.Id, UISlant.Deep.WithAlpha(0.92f), index == 0 ? UISlant.Coral : UISlant.Cyan, 2f, true, 5f * u, false);
            plate.Rect.Place(UIAnchor.BottomLeft, new Vector2(index * (w + gap), 0f), new Vector2(w, h));
            // The accent becomes the top border (leader coral, others cyan).
            var e = plate.Edge.rectTransform;
            e.anchorMin = new Vector2(0f, 1f); e.anchorMax = Vector2.one; e.pivot = new Vector2(0.5f, 1f);
            e.sizeDelta = new Vector2(0f, 3f * u); e.anchoredPosition = Vector2.zero;
            var view = new HeroHud { Hero = hero };
            float face = 46f * u, lean = h * 0.5f * UISkew.Slope;
            var faceImg = UISlant.SlantFace(plate.Rect, new Vector2(face, face));
            faceImg.rectTransform.parent.GetComponent<RectTransform>().Place(UIAnchor.Left, new Vector2(10f * u, 0f), new Vector2(face, face));
            faceImg.sprite = UIArtwork.Hero(hero.Id); faceImg.enabled = faceImg.sprite != null;
            view.Face = faceImg;
            float x = 10f * u + face + 10f * u, right = 12f * u + lean, numW = 40f * u;
            view.Name = UIFactory.Label(plate.Rect, "", 15f * u, UIFont.Heavy, UISlant.Paper, TextAlignmentOptions.MidlineLeft, UITextFx.Plain, "Name");
            view.Name.overflowMode = TextOverflowModes.Ellipsis;
            view.Name.rectTransform.Place(UIAnchor.TopLeft, new Vector2(x, -8f * u), new Vector2(w - x - right - 44f * u, 22f * u));
            view.Level = UIFactory.Label(plate.Rect, "", 12f * u, UIFont.Heavy, UISlant.Muted, TextAlignmentOptions.MidlineRight, UITextFx.Plain, "Level");
            view.Level.rectTransform.Place(UIAnchor.TopRight, new Vector2(-right, -8f * u), new Vector2(44f * u, 22f * u));
            float barW = w - x - right - numW - 6f * u;
            view.HpBar = UISlantBar.Create(plate.Rect, UIGaugeKind.Custom, "HP bar");
            view.HpBar.GetComponent<RectTransform>().Place(UIAnchor.TopLeft, new Vector2(x, -38f * u), new Vector2(barW, 6f * u));
            view.HpText = UIFactory.Label(plate.Rect, "", 13f * u, UIFont.Heavy, UISlant.Paper, TextAlignmentOptions.MidlineRight, UITextFx.Plain, "HP");
            view.HpText.rectTransform.Place(UIAnchor.TopRight, new Vector2(-right, -32f * u), new Vector2(numW, 18f * u));
            view.MpBar = UISlantBar.Create(plate.Rect, UIGaugeKind.Mp, "MP bar");
            view.MpBar.GetComponent<RectTransform>().Place(UIAnchor.TopLeft, new Vector2(x, -54f * u), new Vector2(barW, 4f * u));
            view.MpText = UIFactory.Label(plate.Rect, "", 12f * u, UIFont.Heavy, UISlant.Muted, TextAlignmentOptions.MidlineRight, UITextFx.Plain, "MP");
            view.MpText.rectTransform.Place(UIAnchor.TopRight, new Vector2(-right, -47f * u), new Vector2(numW, 16f * u));
            var chip = UISlant.Pill(plate.Rect, "Status", UISlant.Coral, UISlant.Rest, out var chipText, 11f * u, UIFont.Heavy);
            chip.Rect.Place(UIAnchor.TopRight, new Vector2(1f, 0.5f), new Vector2(-right, 0f), new Vector2(110f * u, 20f * u));
            view.StatusChip = chip.gameObject; view.Status = chipText;
            chip.gameObject.SetActive(false);
            return view;
        }

        void AnimateHudIn(float u, RectTransform topLeft, RectTransform compassRt, RectTransform map, RectTransform mapButton, RectTransform campButton, RectTransform pad, RectTransform party)
        {
            if (root.ReducedMotion || !Application.isPlaying) return;
            void Slide(RectTransform rt, Vector2 from, float delay)
            {
                if (rt == null) return;
                var home = rt.anchoredPosition;
                rt.anchoredPosition = home + from;
                UITween.Move(rt, home, 0.26f, UIEase.OutCubic, delay);
            }
            Slide(topLeft, new Vector2(-120f * u, 0f), 0f);
            Slide(compassRt, new Vector2(0f, 60f * u), 0.04f);
            Slide(map, new Vector2(120f * u, 0f), 0.03f);
            Slide(mapButton, new Vector2(140f * u, 0f), 0.07f);
            Slide(campButton, new Vector2(140f * u, 0f), 0.1f);
            Slide(pad, new Vector2(160f * u, 0f), 0.06f);
            Slide(party, new Vector2(0f, -120f * u), 0.08f);
        }

        void RefreshDungeonHud()
        {
            var grid = app.Dungeon.Grid;
            float u = hudUnit;
            floorBadge.text = grid.Floor.FloorLabel;
            mapFloor.text = grid.Floor.FloorLabel;
            areaName.text = grid.Floor.AreaName;
            int percent = ExploredPercent(grid.Floor, grid.Progress);
            areaSub.text = grid.Cell(app.State.Position) == 'H'
                ? T(app.State.IsSpringSpent(grid.Floor.Id, app.State.Position) ? "spring_cell_spent" : "spring_cell_unused")
                : $"탐사 {percent}%";
            // The plate hugs its text but stops short of the compass.
            float maxPlate = hud.rect.width * 0.5f - 170f * u - 16f * u - 108f * u;
            float textW = Mathf.Max(areaName.GetPreferredValues(areaName.text).x, areaSub.GetPreferredValues(areaSub.text).x);
            areaPlate.sizeDelta = new Vector2(Mathf.Clamp(textW + 70f * u, 240f * u, Mathf.Max(240f * u, maxPlate)), areaPlate.sizeDelta.y);
            float gw = UISlant.FitChip(goldChip, $"{app.State.Gold:N0}만원");
            UISlant.FitChip(keyChip, $"열쇠 {grid.Progress.Keys}");
            ((RectTransform)keyChip.transform.parent).anchoredPosition = new Vector2(gw + 8f * u, 0f);
            string objective = ObjectiveLine();
            objectiveStrip.gameObject.SetActive(!string.IsNullOrEmpty(objective));
            objectiveText.text = objective ?? "";
            if (!string.IsNullOrEmpty(objective))
                objectiveStrip.sizeDelta = new Vector2(Mathf.Clamp(objectiveText.GetPreferredValues(objective).x + 30f * u, 240f * u, 420f * u), objectiveStrip.sizeDelta.y);
            minimap.SetMap(grid, app.State);
            RefreshCompass(true);
            RefreshVitals();
        }

        /// <summary>The campaign's current story objective without its "현재 목표:" prefix; null when there is none.</summary>
        string ObjectiveLine()
        {
            string text;
            try { text = ExpeditionReadiness.Evaluate(app.DB, app.State).ObjectiveText; }
            catch (Exception e) when (e is ArgumentException || e is InvalidOperationException || e is KeyNotFoundException) { return null; }
            if (string.IsNullOrEmpty(text) || text.Contains("정보 없음")) return null;
            const string prefix = "현재 목표:";
            return text.StartsWith(prefix, StringComparison.Ordinal) ? text.Substring(prefix.Length).Trim() : text;
        }

        void RefreshCompass(bool force)
        {
            if (compass[1] == null || app.State == null) return;
            int f = (int)app.State.Facing;
            if (!force && f == compassFacing) return;
            bool changed = compassFacing >= 0 && f != compassFacing;
            compassFacing = f;
            compass[0].text = CompassLetters[(f + 3) % 4];
            compass[1].text = CompassLetters[f % 4];
            compass[2].text = CompassLetters[(f + 1) % 4];
            if (changed && !root.ReducedMotion)
            {
                var c = compass[1].rectTransform;
                UITween.Kill(c);
                c.localScale = new Vector3(1.3f, 1.3f, 1f);
                UITween.Scale(c, 1f, 0.18f, UIEase.OutCubic);
            }
        }

        /// <summary>Walkable cells explored, in percent (doors and walls excluded like the old HUD line).</summary>
        static int ExploredPercent(FloorDef floor, FloorProgress progress)
        {
            int explored = 0, total = 0;
            for (int y = 0; y < floor.Rows.Count; y++)
            {
                string row = floor.Rows[y];
                for (int x = 0; x < row.Length; x++)
                {
                    if (row[x] == '#') continue;
                    total++;
                    if (progress != null && progress.Explored.Contains(new GridPos(x, y))) explored++;
                }
            }
            return Math.Min(100, total == 0 ? 0 : explored * 100 / total);
        }

        // ---- transition cards ---------------------------------------------------------------------------------

        /// <summary>Covers the screen with the area card, runs <paramref name="covered"/>, then reveals.</summary>
        public void Transition(Func<UIAreaCardInfo> info, Action covered, Action revealed = null) => UIAreaCard.Play(info, covered, revealed);

        /// <summary>Card for a dungeon floor: label, area name, description, enemy level range, exploration, boss state.</summary>
        public UIAreaCardInfo FloorCard(int index)
        {
            var floor = app.DB.Floors[Mathf.Clamp(index, 0, app.DB.Floors.Count - 1)];
            var info = new UIAreaCardInfo { Label = floor.FloorLabel, Name = floor.AreaName, Line = floor.AreaDescription, Ghost = floor.FloorLabel };
            int lo = int.MaxValue, hi = 0;
            foreach (var group in floor.EncounterGroups)
                foreach (string id in group)
                    if (app.DB.Enemies.TryGetValue(id, out var enemy)) { lo = Math.Min(lo, enemy.Level); hi = Math.Max(hi, enemy.Level); }
            if (hi > 0) info.Chip(lo == hi ? $"출현 마물 Lv.{lo}" : $"출현 마물 Lv.{lo}–{hi}", UISlant.Coral);
            app.State.Floors.TryGetValue(floor.Id, out var progress);
            info.Chip($"탐사 {ExploredPercent(floor, progress)}%", UISlant.Amber);
            var boss = GridPos.None;
            for (int y = 0; y < floor.Rows.Count && boss == GridPos.None; y++)
            {
                int x = floor.Rows[y].IndexOf('B');
                if (x >= 0) boss = new GridPos(x, y);
            }
            if (boss != GridPos.None)
                info.Chip(progress != null && progress.ClearedBattles.Contains(boss) ? "게이트 보스 토벌 완료" : "게이트 보스 구역", UISlant.Cyan);
            return info;
        }

        /// <summary>Town variant: guild name and the same facts as the town HUD header.</summary>
        public UIAreaCardInfo TownCard()
        {
            var info = new UIAreaCardInfo { Town = true, Name = T("town", "새벽 길드"), Line = T("town_subtitle", ""), Ghost = "GUILD" };
            if (app.State == null) return info;
            return info.Chip(GoldLine, UISlant.Amber)
                .Chip($"{T("rank_title", "길드 등급")} {GameFlow.GuildRank(app.State)}", UISlant.Cyan)
                .Chip($"최심부 {DeepestLabel}", UISlant.Coral);
        }
    }

    /// <summary>The big 전진 key: a paper-white upward pentagon with a chevron; coral while pressed or hovered. Repeats while held.</summary>
    internal sealed class PadArrow : MonoBehaviour, IPointerEnterHandler, IPointerExitHandler, IPointerDownHandler, IPointerUpHandler, IPointerClickHandler
    {
        UIPolygon shape, chevronL, chevronR;
        TextMeshProUGUI label;
        RectTransform visual;
        bool hover, pressed, repeated;
        float repeatAt, nextClickAt;
        public float HoldRepeat;
        public event Action Clicked;
        static bool Reduced => UIRoot.Instance != null && UIRoot.Instance.ReducedMotion;

        public static PadArrow Create(Transform parent, string text, bool touch, float u)
        {
            var rt = UIFactory.Rect(parent, "Key " + text);
            var key = rt.gameObject.AddComponent<PadArrow>();
            key.visual = UIFactory.Rect(rt, "Visual").Stretch();
            key.shape = UIPolygon.Create(key.visual, "Shape", UIPolygon.Pentagon(0.66f), UISlant.Paper, raycast: true);
            key.shape.rectTransform.Stretch();
            // Chevron: two thin slanted bars meeting at the top.
            var chevron = UIFactory.Rect(key.visual, "Chevron");
            chevron.Place(UIAnchor.Center, new Vector2(0f, 14f * u), new Vector2(26f * u, 14f * u));
            key.chevronL = UIPolygon.Create(chevron, "Left", new[] { new Vector2(0f, 0f), new Vector2(0.5f, 1f), new Vector2(0.5f, 0.55f), new Vector2(0.17f, 0f) }, UISlant.Night);
            key.chevronL.rectTransform.Stretch();
            key.chevronR = UIPolygon.Create(chevron, "Right", new[] { new Vector2(1f, 0f), new Vector2(0.83f, 0f), new Vector2(0.5f, 0.55f), new Vector2(0.5f, 1f) }, UISlant.Night);
            key.chevronR.rectTransform.Stretch();
            key.label = UIFactory.Label(key.visual, text, touch ? 30f : 26f, UIFont.Heavy, UISlant.Night, TextAlignmentOptions.Center, UITextFx.Plain, "Label");
            key.label.rectTransform.Place(UIAnchor.Bottom, new Vector2(0f, 8f * u), new Vector2(0f, 30f * u));
            key.label.rectTransform.anchorMin = new Vector2(0f, 0f); key.label.rectTransform.anchorMax = new Vector2(1f, 0f);
            key.Paint();
            return key;
        }

        void Paint()
        {
            bool lit = hover || pressed;
            shape.color = pressed ? UISlant.CoralDark : lit ? UISlant.Coral : UISlant.Paper;
            var ink = lit ? Color.white : UISlant.Night;
            chevronL.color = chevronR.color = ink; label.color = ink;
            UITween.Kill(visual);
            float s = Reduced ? 1f : pressed ? 0.96f : hover ? 1.03f : 1f;
            if (!Application.isPlaying) { visual.localScale = new Vector3(s, s, 1f); return; }
            UITween.Scale(visual, s, Reduced ? 0f : 0.1f, UIEase.OutCubic);
        }

        void Click()
        {
            if (HoldRepeat <= 0f && Time.unscaledTime < nextClickAt) return;
            nextClickAt = Time.unscaledTime + 0.25f;
            UIInput.Consume();
            Clicked?.Invoke();
        }

        void Update()
        {
            if (HoldRepeat <= 0f || !pressed || Time.unscaledTime < repeatAt) return;
            repeatAt = Time.unscaledTime + HoldRepeat;
            if (!UIInput.CanReceive(this)) return;
            repeated = true;
            Click();
        }

        void OnDisable() { hover = pressed = false; }
        public void OnPointerEnter(PointerEventData e) { hover = true; Paint(); }
        public void OnPointerExit(PointerEventData e) { hover = false; pressed = false; Paint(); }
        public void OnPointerDown(PointerEventData e)
        {
            if (e.button != PointerEventData.InputButton.Left) return;
            pressed = true; repeated = false;
            repeatAt = Time.unscaledTime + Mathf.Max(HoldRepeat, UIInput.RepeatDelay);
            Paint();
        }
        public void OnPointerUp(PointerEventData e) { pressed = false; Paint(); }
        public void OnPointerClick(PointerEventData e)
        {
            if (e.button != PointerEventData.InputButton.Left) return;
            if (repeated) { repeated = false; return; }
            if (!UIInput.CanReceive(this)) return;
            Click();
        }
    }
}
