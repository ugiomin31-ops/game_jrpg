using System;
using Abyss.Logic.Dungeon;
using Abyss.Logic.Game;
using UnityEngine;
using UnityEngine.InputSystem;

namespace Abyss.UI
{
    /// <summary>Read-only floor map. Discovery, spent treasure and hidden traps come from DungeonGrid.MapMarker.</summary>
    public sealed class GameMapScreen : UIScreen
    {
        public DungeonRun Run;
        public GameState State;
        public Action Closed;
        protected override void Build()
        {
            UIFactory.Fill(Rect, UITheme.Ink.WithAlpha(0.97f), raycast: true);
            var frame = UIFactory.Panel(Rect, UIPanelStyle.Ornate);
            bool compact = UIRoot.Compact;
            if (compact) frame.Rect.Stretch(26, 18, 26, 18); else frame.Rect.Stretch(100, 55, 100, 55);
            var grid = Run.Grid;
            var title = UIFactory.Paragraph(frame.Rect, "탐색 지도 · " + grid.Floor.FloorLabel + " · " + grid.Floor.AreaName, 36, UITheme.GoldBright);
            title.overflowMode = TMPro.TextOverflowModes.Ellipsis;
            title.Rt().TopStrip(65, 30, 45, 45);
            int open = 0, seen = 0;
            for (int y = 0; y < grid.Height; y++) for (int x = 0; x < grid.Width; x++)
            {
                var cell = new GridPos(x, y);
                if (grid.Cell(cell) == '#') continue;
                open++; if (grid.Progress.Explored.Contains(cell)) seen++;
            }
            UIFactory.Label(frame.Rect, $"탐사율 {(open == 0 ? 0 : seen * 100 / open)}% · 열쇠 {grid.Progress.Keys} · 현재 위치 ({State.Position.X + 1}, {State.Position.Y + 1})", 24, color: UITheme.TextDim)
                .Rt().TopStrip(42, 105, 45, 45);
            var mapPanel = UIFactory.Panel(frame.Rect, UIPanelStyle.Dark, false);
            mapPanel.Rect.Stretch(45, 165, 460, 110);
            var map = UIFactory.Add<DungeonMapGraphic>(mapPanel.Rect, "Discovered floor");
            map.Rt().Stretch(18, 18, 18, 18); map.SetMap(grid, State);
            var legend = UIFactory.Panel(frame.Rect, UIPanelStyle.Dark, false);
            legend.Rect.anchorMin = new Vector2(1, 0); legend.Rect.anchorMax = Vector2.one;
            legend.Rect.offsetMin = new Vector2(-420, 110); legend.Rect.offsetMax = new Vector2(-45, -165);
            UIFactory.Label(legend.Rect, "범례", 28, color: UITheme.GoldBright).Rt().TopStrip(42, 14, 20, 20);
            char[] markers = { '>', '<', 'W', 'H', 'L', 'T', 'K', 'X', 'N', 'B', 'E', 'F', 'f' };
            string[] labels = { "내려가는 계단", "올라가는 계단", "전송 수정", "치유의 샘", "잠긴 문", "보물 상자", "열쇠", "발견한 함정", "미궁의 비석", "봉인의 수호자", "강적의 기척", "배회 강적", "추격 중인 강적" };
            for (int i = 0; i < labels.Length; i++)
            {
                var sample = UIFactory.Add<DungeonMapSymbol>(legend.Rect, labels[i]);
                sample.Marker = markers[i];
                float step = compact ? 37f : 42f;
                sample.Rt().Place(UIAnchor.TopLeft, new Vector2(22, -70 - i * step), new Vector2(28, 28));
                UIFactory.Label(legend.Rect, labels[i], compact ? 24 : 23).Rt().Place(UIAnchor.TopLeft, new Vector2(66, -66 - i * step), new Vector2(285, 36));
            }
            UIFactory.Paragraph(frame.Rect, "빛나는 화살표 · 현재 위치와 방향\n미탐색 구역과 밟지 않은 함정은 표시되지 않습니다.", 21, UITheme.TextDim)
                .Rt().BottomStrip(68, 24, 45, 340);
            var buttons = UIFactory.ButtonGroup(frame.Rect, true);
            buttons.Rt().Place(UIAnchor.BottomRight, new Vector2(-45, 28), new Vector2(240, 62));
            buttons.AddButton("지도 닫기", Close, 240);
        }
        void Update()
        {
            if (IsTop && UIInput.CanReceive(this) && (Keyboard.current?.mKey.wasPressedThisFrame ?? false))
            { UIInput.Consume(); Close(); }
        }
        protected override void OnClose() { UIInput.Consume(); Closed?.Invoke(); }
    }
}
