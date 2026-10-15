using System;
using System.Collections.Generic;
using Abyss.Logic;
using Abyss.Logic.Dungeon;
using Abyss.Logic.Game;
using TMPro;
using UnityEngine;
using UnityEngine.InputSystem;

namespace Abyss.UI
{
    /// <summary>
    /// Read-only floor map. Discovery, spent treasure and hidden traps come from DungeonGrid.MapMarker.
    /// Slanted header (지도 · AREA MAP), tabs for the visited floors of the current zone, the map on the left and the
    /// current-floor facts plus legend on the right.
    /// </summary>
    public sealed class GameMapScreen : UIScreen
    {
        public DungeonRun Run;
        public GameState State;
        public GameDB DB;
        public Action Closed;

        // Defined by the map rules: legend order and wording are unchanged from the previous screen.
        static readonly char[] Markers = { '>', '<', 'W', 'H', 'L', 'T', 'K', 'X', 'N', 'B', 'E', 'R', 'F', 'f' };
        static readonly string[] Labels = { "내려가는 계단", "올라가는 계단", "이동 게이트", "응급 키트", "잠긴 문", "보물 상자", "열쇠", "발견한 함정", "기록 단말기", "게이트 보스", "강적의 기척", "구조 요청", "배회 강적", "추격 중인 강적" };

        readonly List<int> floors = new List<int>();
        readonly List<UISlantButton> tabs = new List<UISlantButton>();
        DungeonMapGraphic map;
        TextMeshProUGUI currentEyebrow, currentTitle, currentStats, currentWhere;
        RectTransform header, mapPanel, side;
        int shown = -1;
        float u;

        protected override void Build()
        {
            // Opaque: in linear colour space even 3 % of the bright HUD bleeds through visibly.
            UIFactory.Fill(Rect, UISlant.Night, raycast: true).rectTransform.Stretch(-400f, -200f, -400f, -200f);
            bool touch = UIRoot.TouchFirst;
            float target = touch ? UIRoot.TouchTargetHeight : 0f;
            u = Mathf.Max(1f, Rect.rect.height) / 720f;
            float headerH = 110f * u;

            // ---- header -------------------------------------------------------------------------------------
            header = UIFactory.Rect(Rect, "Header");
            header.TopStrip(headerH, 0f, 0f, 0f);
            var band = UIFactory.Image(header, UISprites.White, UISlant.Band, "Band");
            band.rectTransform.Stretch(-400f, -200f, -400f, 0f);
            var block = UIFactory.Image(header, UISprites.White, UISlant.Coral, "Title block");
            block.gameObject.AddComponent<UISkew>();
            // Bleeds off the left edge (past the safe area); the slant shears about the header's centre line.
            block.rectTransform.Place(UIAnchor.TopLeft, new Vector2(-400f, 0f), new Vector2(400f + 300f * u, headerH));
            UIFactory.Label(header, "지도", 46f * u, UIFont.Title, UISlant.Paper, TextAlignmentOptions.MidlineLeft, UITextFx.Plain, "Title")
                .rectTransform.Place(UIAnchor.Left, new Vector2(40f * u, 0f), new Vector2(110f * u, headerH));
            UISlant.Eyebrow(header, "AREA MAP", 16f * u, UISlant.Paper, 30f).rectTransform.Place(UIAnchor.Left, new Vector2(150f * u, 2f * u), new Vector2(140f * u, 30f * u));

            CollectFloors();
            float tabW = 110f * u, tabH = Mathf.Max(44f * u, target), tabX = 360f * u;
            for (int i = 0; i < floors.Count; i++)
            {
                int floorIndex = floors[i];
                var tab = UISlantButton.Create(header, "Floor " + i, new Vector2(tabW, tabH), UISlantKind.Simple, touch);
                tab.SetLabel(FloorOf(floorIndex).FloorLabel);
                tab.Label.font = UITheme.Font(UIFont.Heavy);
                tab.FocusScale = 1.04f;
                tab.Rt().Place(UIAnchor.Left, new Vector2(tabX + i * (tabW + 10f * u), 0f), new Vector2(tabW, tabH));
                tab.Clicked += () => Show(floorIndex);
                tabs.Add(tab);
            }
            float closeSize = Mathf.Max(52f * u, target);
            var close = UISlantButton.Create(header, "Close", new Vector2(closeSize, closeSize), UISlantKind.Simple, touch);
            close.SetLabel("");
            close.SetColors(UISlant.Plate, UISlant.Paper);
            close.Rt().Place(UIAnchor.Right, new Vector2(-36f * u, 0f), new Vector2(closeSize, closeSize));
            for (int i = 0; i < 2; i++)
            {
                var bar = UIFactory.Image(close.Visual, UISprites.White, UISlant.Paper, "Cross");
                bar.rectTransform.Place(UIAnchor.Center, Vector2.zero, new Vector2(closeSize * 0.46f, Mathf.Max(3f, 3f * u)));
                bar.rectTransform.localEulerAngles = new Vector3(0f, 0f, i == 0 ? 45f : -45f);
            }
            close.Clicked += Close;

            // ---- map ----------------------------------------------------------------------------------------
            float sideW = 340f * u;
            mapPanel = UIFactory.Rect(Rect, "Map panel");
            mapPanel.Stretch(40f * u, headerH + 30f * u, sideW + 80f * u, 40f * u);
            UIFactory.Fill(mapPanel, UISlant.Deep, "Fill");
            BorderLines(mapPanel, UITheme.Hex("1c2647"), 2f * u);
            map = UIFactory.Add<DungeonMapGraphic>(mapPanel, "Discovered floor");
            map.Rt().Stretch(24f * u, 24f * u, 24f * u, 24f * u);

            // ---- right column: current floor + legend -------------------------------------------------------
            side = UIFactory.Rect(Rect, "Side");
            side.anchorMin = new Vector2(1f, 0f); side.anchorMax = Vector2.one; side.pivot = new Vector2(1f, 1f);
            side.offsetMin = new Vector2(-40f * u - sideW, 40f * u); side.offsetMax = new Vector2(-40f * u, -(headerH + 30f * u));

            var current = UIFactory.Rect(side, "Current");
            current.TopStrip(124f * u, 0f, 0f, 0f);
            UIFactory.Fill(current, UISlant.Band, "Fill");
            var rule = UIFactory.Image(current, UISprites.White, UISlant.Cyan, "Rule");
            rule.rectTransform.TopStrip(3f * u, 0f, 0f, 0f);
            currentEyebrow = UISlant.Eyebrow(current, "CURRENT", 12f * u, UISlant.Cyan, 30f);
            currentEyebrow.rectTransform.TopStrip(20f * u, 14f * u, 20f * u, 20f * u);
            currentTitle = UIFactory.Label(current, "", 30f * u, UIFont.Title, UISlant.Paper, TextAlignmentOptions.MidlineLeft, UITextFx.Plain, "Floor");
            currentTitle.enableAutoSizing = true; currentTitle.fontSizeMax = 30f * u; currentTitle.fontSizeMin = 20f * u;
            currentTitle.overflowMode = TextOverflowModes.Ellipsis;
            currentTitle.rectTransform.TopStrip(40f * u, 34f * u, 20f * u, 20f * u);
            currentStats = UIFactory.Label(current, "", 14f * u, UIFont.Bold, UITheme.Hex("c4ccea"), TextAlignmentOptions.MidlineLeft, UITextFx.Plain, "Stats");
            currentStats.rectTransform.TopStrip(22f * u, 76f * u, 20f * u, 20f * u);
            currentWhere = UIFactory.Label(current, "", 12f * u, UIFont.Bold, UISlant.Muted, TextAlignmentOptions.MidlineLeft, UITextFx.Plain, "Position");
            currentWhere.rectTransform.TopStrip(18f * u, 98f * u, 20f * u, 20f * u);

            var legend = UIFactory.Rect(side, "Legend");
            float rowH = 25f * u, legendTop = 124f * u + 14f * u;
            int perColumn = (Markers.Length + 1) / 2;
            float legendH = 40f * u + perColumn * rowH + 12f * u;
            legend.TopStrip(legendH, legendTop, 0f, 0f);
            UIFactory.Fill(legend, UISlant.Band, "Fill");
            UISlant.Eyebrow(legend, "LEGEND", 12f * u, UISlant.Muted, 30f).rectTransform.TopStrip(20f * u, 12f * u, 20f * u, 20f * u);
            float colW = (sideW - 40f * u) * 0.5f;
            for (int i = 0; i < Labels.Length; i++)
            {
                int col = i / perColumn, row = i % perColumn;
                float x = 20f * u + col * colW, y = -(40f * u + row * rowH);
                var swatch = UIFactory.Image(legend, UISprites.White, UISlant.Deep, "Swatch " + Labels[i]);
                swatch.rectTransform.Place(UIAnchor.TopLeft, new Vector2(x, y - 2f * u), new Vector2(20f * u, 20f * u));
                var sample = UIFactory.Add<DungeonMapSymbol>(swatch.rectTransform, Labels[i]);
                sample.Marker = Markers[i];
                sample.rectTransform.Stretch();
                UIFactory.Label(legend, Labels[i], 13f * u, UIFont.Bold, UISlant.Paper, TextAlignmentOptions.MidlineLeft, UITextFx.Plain, "Label")
                    .rectTransform.Place(UIAnchor.TopLeft, new Vector2(x + 28f * u, y), new Vector2(colW - 30f * u, 24f * u));
            }
            var note = UIFactory.Paragraph(side, "빛나는 화살표 · 현재 위치와 방향\n미탐색 구역과 밟지 않은 함정은 표시되지 않습니다.", 12f * u, UISlant.Muted, "Note");
            note.lineSpacing = 0f;
            note.rectTransform.TopStrip(44f * u, legendTop + legendH + 10f * u, 4f * u, 0f);
            if (!touch && floors.Count > 1)
                UIFactory.Label(side, "Q / E 층 전환 · M / X 닫기", 12f * u, UIFont.Bold, UISlant.Muted, TextAlignmentOptions.BottomRight, UITextFx.Plain, "Keys")
                    .rectTransform.BottomStrip(20f * u, 0f, 0f, 0f);
            else if (!touch)
                UIFactory.Label(side, "M / X 닫기", 12f * u, UIFont.Bold, UISlant.Muted, TextAlignmentOptions.BottomRight, UITextFx.Plain, "Keys")
                    .rectTransform.BottomStrip(20f * u, 0f, 0f, 0f);

            Show(State.FloorIndex);
        }

        FloorDef FloorOf(int index) => index == State.FloorIndex || DB == null ? Run.Grid.Floor : DB.Floors[index];

        /// <summary>Visited floors of the current zone (three floors per zone), always including the current one.</summary>
        void CollectFloors()
        {
            floors.Clear();
            var db = DB;
            int current = State.FloorIndex;
            if (db == null) { floors.Add(current); return; }
            int first = current / GameFlow.FloorsPerChapter * GameFlow.FloorsPerChapter;
            for (int i = first; i < Mathf.Min(first + GameFlow.FloorsPerChapter, db.Floors.Count); i++)
                if (i == current || (State.Floors.TryGetValue(db.Floors[i].Id, out var p) && p.Explored.Count > 0)) floors.Add(i);
            if (!floors.Contains(current)) floors.Add(current);
        }

        void Show(int floorIndex)
        {
            shown = floorIndex;
            bool here = floorIndex == State.FloorIndex;
            DungeonGrid grid;
            if (here) grid = Run.Grid;
            else
            {
                var floor = FloorOf(floorIndex);
                State.Floors.TryGetValue(floor.Id, out var progress);
                // A read-only view: an empty progress is used when none exists so nothing is added to the save.
                grid = DungeonGrid.Parse(floor, progress ?? new FloorProgress());
            }
            map.ShowParty = here;
            map.SetMap(grid, State);
            for (int i = 0; i < tabs.Count; i++)
            {
                bool on = floors[i] == floorIndex;
                tabs[i].SetColors(on ? UISlant.Paper : UISlant.Plate, on ? UISlant.Night : UISlant.Muted);
            }
            int open = 0, seen = 0, chests = 0;
            for (int y = 0; y < grid.Height; y++) for (int x = 0; x < grid.Width; x++)
            {
                var cell = new GridPos(x, y);
                char c = grid.Cell(cell);
                if (c == '#') continue;
                open++; if (grid.Progress.Explored.Contains(cell)) seen++;
                if (c == 'T') chests++;
            }
            currentEyebrow.text = here ? "CURRENT" : "VISITED";
            currentTitle.text = grid.Floor.FloorLabel + " " + grid.Floor.AreaName;
            currentStats.text = $"탐사 {(open == 0 ? 0 : seen * 100 / open)}%    보물 {grid.Progress.OpenedChests.Count}/{chests}    열쇠 {grid.Progress.Keys}";
            currentWhere.text = here ? $"현재 위치 ({State.Position.X + 1}, {State.Position.Y + 1})" : "다른 층 · 기록된 지도";
        }

        void Update()
        {
            if (!IsTop || !UIInput.CanReceive(this)) return;
            if (UIInput.MapToggle) { UIInput.Consume(); Close(); return; }
            int step = UIInput.TabPrev ? -1 : UIInput.TabNext ? 1 : 0;
            if (step != 0 && floors.Count > 1)
            {
                UIInput.Consume();
                int i = floors.IndexOf(shown);
                i = ((i + step) % floors.Count + floors.Count) % floors.Count;
                UISound.Play(UISoundId.Move);
                Show(floors[i]);
            }
        }

        protected override UITween AnimateIn()
        {
            bool reduced = UIRoot.Instance != null && UIRoot.Instance.ReducedMotion;
            Group.alpha = 0f;
            Rect.anchoredPosition = Vector2.zero;
            if (!reduced)
            {
                Slide(header, new Vector2(0f, 70f * u), 0f);
                Slide(mapPanel, new Vector2(-90f * u, 0f), 0.04f);
                Slide(side, new Vector2(110f * u, 0f), 0.07f);
            }
            return UITween.Fade(Group, 1f, reduced ? 0.12f : 0.16f, UIEase.OutQuad);
        }

        static void Slide(RectTransform rt, Vector2 offset, float delay)
        {
            var home = rt.anchoredPosition;
            rt.anchoredPosition = home + offset;
            UITween.Move(rt, home, 0.24f, UIEase.OutCubic, delay);
        }

        static void BorderLines(RectTransform parent, Color color, float width)
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

        protected override void OnClose() { UIInput.Consume(); Closed?.Invoke(); }
    }
}
