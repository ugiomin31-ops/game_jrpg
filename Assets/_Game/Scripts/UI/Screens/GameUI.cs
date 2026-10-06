using System;
using System.Collections.Generic;
using System.IO;
using Abyss.Logic;
using Abyss.Logic.Dungeon;
using Abyss.Logic.Game;
using Abyss.Runtime;
using TMPro;
using UnityEngine;

namespace Abyss.UI
{
    public sealed partial class GameUI : MonoBehaviour
    {
        public RectTransform Content { get; private set; }
        public bool BlocksWorldInput => app == null || root == null || root.Screens.Count > 0 || root.Modals.Count > 0 || app.Paused || (app.Screen != GameScreen.Town && app.Screen != GameScreen.Dungeon);
        // Battle targeting always blocks world movement, but idle command/reward UI may be paused.
        public bool CanOpenPause => app != null && root != null && root.Screens.Count == 0 && root.Modals.Count == 0 && !app.Paused
            && (app.Screen == GameScreen.Town || app.Screen == GameScreen.Dungeon
                || (app.Screen == GameScreen.Battle && app.Battle != null && !app.Battle.Playing));
        GameApp app;
        UIRoot root;
        RectTransform hud;
        TextMeshProUGUI area, resources;
        DungeonMapGraphic minimap;
        readonly List<HeroHud> heroHud = new List<HeroHud>();
        sealed class HeroHud
        {
            public HeroState Hero;
            public TextMeshProUGUI Name, Status;
            public UIGauge Hp, Mp;
            public UIPortrait Portrait;
        }
        public void Initialize(GameApp owner)
        {
            app = owner;
            root = UIRoot.Create();
            root.ReducedMotion = app.Preferences.ReducedMotion;
            Content = UIFactory.Rect(root.Hud, "Game Content").Stretch();
        }
        public void Clear()
        {
            root.Screens.Clear(); root.Modals.Clear(); root.Tooltip.Hide(); root.Dialog.Close();
            ClearHud();
        }
        void ClearHud()
        {
            heroHud.Clear(); area = null; resources = null; minimap = null;
            if (hud != null) { hud.gameObject.SetActive(false); Destroy(hud.gameObject); }
            hud = null;
            // BattleView owns children under Content and releases them when its route closes.
        }
        GameMenuScreen Menu(string title, string subtitle, Action<GameMenuScreen> refresh, string[] tabs = null, bool cancel = true)
        {
            return root.Screens.Push<GameMenuScreen>(m =>
            { m.Title = title; m.Subtitle = subtitle; m.RefreshContent = refresh; m.TabLabels = tabs; m.AllowCancel = cancel; });
        }
        string T(string key, string fallback = null) => app.DB.Text.TryGetValue(key, out var value) ? value : fallback ?? "정보를 확인할 수 없습니다.";
        string HeroName(string id) => app.DB.Heroes.TryGetValue(id, out var d) ? d.DisplayName : "동료";
        string ItemName(string id) => app.DB.Items.TryGetValue(id, out var d) ? d.DisplayName : app.DB.Equipment.TryGetValue(id, out var e) ? e.DisplayName : "물품";
        string EquipmentName(string id) => app.DB.Equipment.TryGetValue(id, out var e) ? e.DisplayName : T("slot_none");
        string DifficultyName(Difficulty d) => T(d == Difficulty.Easy ? "difficulty_easy" : d == Difficulty.Hard ? "difficulty_hard" : "difficulty_normal");
        void Confirm(string title, string message, Action action) => UIModal.Confirm(root.Modals, title, message, yes => { if (yes) action(); }, defaultYes: false);
        void Execute(ServiceResult result, GameMenuScreen screen = null)
        {
            if (result.Success)
            {
                Notify(LocalResult(result));
                if (result.RequestsAutosave) app.Save();
                screen?.Refresh(); RefreshVitals(); RefreshTown();
            }
            else UIModal.Alert(root.Modals, "할 수 없는 행동", LocalResult(result));
        }
        string LocalResult(ServiceResult result) => app.DB.Text.ContainsKey(result.TextKey) ? result.Message(app.DB) : T("reason_generic");
        public void Notify(string text) => root.Toast.Show(text, UIToastKind.Info);
        public void ShowTitle()
        {
            Clear();
            root.Screens.Push<GameTitleScreen>(screen =>
            {
                screen.HasSave = app.Saves.Exists(-1) || app.Saves.Exists(0) || app.Saves.Exists(1) || app.Saves.Exists(2);
                screen.NewGame = ShowNewGame;
                screen.ContinueGame = () => ShowSlots(false);
                screen.Settings = ShowSettings;
                screen.Credits = () => ShowCredits(null);
                screen.Quit = () => Confirm("게임 종료", "게임을 종료할까요?", app.Quit);
            });
        }
        void ShowNewGame()
        {
            Menu(T("difficulty_title"), T("difficulty_hint"), m =>
            {
                foreach (Difficulty d in Enum.GetValues(typeof(Difficulty)))
                {
                    var difficulty = d;
                    m.Add(DifficultyName(d), () =>
                    {
                        if (app.Saves.Exists(-1)) Confirm("새 모험 시작", "새 모험의 자동 저장이 기존 자동 저장을 덮어씁니다. 수동 저장 슬롯은 유지됩니다. 시작할까요?", () => app.NewGame(difficulty));
                        else app.NewGame(difficulty);
                    }, T(d == Difficulty.Easy ? "easy" : d == Difficulty.Hard ? "hard" : "normal"));
                }
            });
        }
        void ShowSlots(bool saving)
        {
            Menu(saving ? T("save") : T("continue"), saving ? "세 개의 수동 슬롯에 저장할 수 있습니다. 자동 저장은 별도로 유지됩니다." : "슬롯을 선택하면 해당 지점부터 계속합니다.", m =>
            {
                for (int i = saving ? 0 : -1; i < 3; i++)
                {
                    int slot = i;
                    bool exists = app.Saves.Exists(slot);
                    string name = slot == -1 ? "자동 저장" : $"저장 슬롯 {slot + 1}";
                    string description = "비어 있는 슬롯입니다.";
                    bool readable = true;
                    if (exists)
                    {
                        try
                        {
                            var s = app.Saves.Summary(slot);
                            var played = TimeSpan.FromSeconds(s.PlayTimeSeconds);
                            var lines = new List<string> { s.Location == GameLocation.Town ? T("town") : s.FloorLabel, $"{DifficultyName(s.Difficulty)} · {s.Gold:N0} G", $"최심부 {s.DeepestFloorLabel}", $"플레이 시간 {(long)played.TotalHours:00}:{played.Minutes:00}:{played.Seconds:00}" };
                            foreach (var hero in s.Levels) lines.Add($"{HeroName(hero.Key)} · Lv.{hero.Value}");
                            var date = app.Saves.SlotTime(slot);
                            if (date.HasValue) lines.Add(date.Value.ToLocalTime().ToString("yyyy-MM-dd HH:mm"));
                            if (s.Cleared) lines.Add("여명을 되찾은 모험");
                            description = string.Join("\n", lines);
                        }
                        catch (Exception e) when (e is IOException || e is UnauthorizedAccessException || e is SaveFormatException || e is Newtonsoft.Json.JsonException)
                        { description = "저장 데이터를 읽을 수 없습니다. 다른 슬롯을 선택해 주세요."; readable = false; }
                    }
                    m.Add(name, () =>
                    {
                        if (!saving)
                        {
                            if (app.Screen == GameScreen.Title) app.Continue(slot);
                            else Confirm("저장 불러오기", "저장하지 않은 진행은 잃게 됩니다. 이 모험을 불러올까요?", () => app.Continue(slot));
                            return;
                        }
                        void Save() { app.Save(slot); m.Refresh(); }
                        if (exists) Confirm("저장 덮어쓰기", $"{name}의 기존 모험을 덮어쓸까요?", Save); else Save();
                    }, description, exists ? "저장 있음" : "비어 있음", saving || (exists && readable), exists ? "읽기 오류" : T("no_save"));
                }
            });
        }
        public void ShowStory(string title, IReadOnlyList<string> lines, Action completed)
        {
            Clear();
            root.Screens.Push<GameStoryScreen>(s =>
            { s.Title = title; s.Pages = lines; s.CharactersPerSecond = app.Preferences.TextSpeed; s.ReducedMotion = app.Preferences.ReducedMotion; s.Completed = completed; });
        }
        public void ShowEnding(Action completed)
        {
            var pages = new List<string>();
            foreach (var key in GameFlow.EndingKeys) pages.Add(T(key));
            ShowStory(T("ending_title"), pages, () => ShowCredits(completed));
        }
        public void ShowDefeat()
        {
            Clear();
            Menu(T("game_over"), T("game_over_body"), m =>
            {
                m.Add(T("recover"), app.RecoverFromDefeat, T(app.State.Difficulty == Difficulty.Easy ? "defeat_easy" : "defeat_penalty"));
                m.Add("저장 불러오기", () => ShowSlots(false));
                m.Add(T("title_return"), ReturnTitle);
            }, cancel: false);
        }
        public void ShowPause()
        {
            if (!CanOpenPause) return;
            UIInput.Consume();
            app.SetPaused(true);
            var pause = Menu(app.Screen == GameScreen.Dungeon ? T("camp_title") : "모험 수첩", T("camp_hint"), m =>
            {
                bool inBattle = app.Screen == GameScreen.Battle;
                if (app.Screen == GameScreen.Town) m.Add("마을 시설", ShowTownDirectory, T("town_subtitle"));
                m.Add(T("party"), ShowParty, "동료의 능력치, 장비와 습득한 기술을 확인합니다.", icon: UIArtwork.Command("party"));
                m.Add(T("cmd_item"), ShowFieldItems, inBattle ? T("battle_unavailable") : T("camp_hint"), enabled: !inBattle, reason: T("battle_unavailable"), icon: UIArtwork.Command("item"));
                m.Add("의뢰 수첩", () => ShowQuests(false));
                m.Add(T("tool_map"), ShowMap, T("map_hint"), icon: UIArtwork.Command("map"));
                m.Add(T("save"), () => ShowSlots(true), inBattle ? "전투가 끝난 뒤 저장할 수 있습니다. 전투 이전의 자동 저장은 유지됩니다." : "현재 모험을 저장합니다.", enabled: !inBattle, reason: T("battle_unavailable"));
                m.Add("저장 불러오기", () => ShowSlots(false));
                m.Add(T("settings"), ShowSettings);
                m.Add(T("credits"), () => ShowCredits(null));
                m.Add(T("title_return"), ReturnTitle);
                m.Add("모험 계속", () => root.Screens.Pop());
            });
            pause.CloseOnMenu = true;
            pause.Closed = () => { UIInput.Consume(); app.SetPaused(false); };
        }
        void ReturnTitle() => Confirm(T("title_return"), "저장하지 않은 진행은 잃게 됩니다. 타이틀로 돌아갈까요?", app.ShowTitle);
        void Update()
        {
            if (app == null || root == null || !CanOpenPause) return;
            if (UIInput.Menu || (UIInput.Cancel && (app.Screen != GameScreen.Battle || app.Battle.CanOpenPause)))
            { ShowPause(); }
        }
        public void ShowDungeon()
        {
            if (hud != null && minimap != null) { RefreshDungeon(); return; }
            Clear();
            BuildHud(true);
            RefreshDungeon();
        }
        public void RefreshDungeon()
        {
            if (app.Dungeon == null || hud == null) return;
            var grid = app.Dungeon.Grid;
            area.text = $"{grid.Floor.FloorLabel}  ·  {grid.Floor.AreaName}";
            int explored = 0, total = 0;
            for (int y = 0; y < grid.Height; y++) for (int x = 0; x < grid.Width; x++)
            {
                var cell = new GridPos(x, y);
                if (grid.Cell(cell) == '#') continue;
                total++; if (grid.Progress.Explored.Contains(cell)) explored++;
            }
            resources.text = $"{app.State.Gold:N0} G  ·  열쇠 {grid.Progress.Keys}  ·  탐사 {Math.Min(100, total == 0 ? 0 : explored * 100 / total)}%";
            minimap.SetMap(grid, app.State);
            RefreshVitals();
        }
        void BuildHud(bool dungeon)
        {
            hud = UIFactory.Rect(Content, dungeon ? "Dungeon HUD" : "Town HUD").Stretch();
            var heading = UIFactory.Panel(hud);
            heading.Rect.TopStrip(128, 0, 30, dungeon ? 390 : 30);
            area = UIFactory.Label(heading.Rect, "", 36, color: UITheme.GoldBright);
            area.Rt().TopStrip(54, 16, 25, 25);
            resources = UIFactory.Label(heading.Rect, "", 23, color: UITheme.TextDim);
            resources.Rt().BottomStrip(40, 12, 25, 25);
            for (int i = 0; i < app.State.Party.Count; i++)
            {
                var hero = app.State.Party[i];
                var panel = UIFactory.Panel(hud);
                panel.Rect.Place(UIAnchor.BottomLeft, new Vector2(30 + i * 350, 28), new Vector2(330, 176));
                var view = new HeroHud { Hero = hero };
                view.Portrait = UIFactory.Portrait(panel.Rect, 58);
                view.Portrait.Rt().Place(UIAnchor.TopLeft, new Vector2(12, -8), new Vector2(58, 58));
                view.Portrait.SetSprite(UIArtwork.Hero(hero.Id));
                view.Name = UIFactory.Label(panel.Rect, "", 24, color: UITheme.GoldBright);
                view.Name.Rt().TopStrip(30, 12, 82, 12);
                view.Hp = UIFactory.Gauge(panel.Rect, UIGaugeKind.Hp, 228, 14, UIGaugeText.Above);
                view.Hp.Rt().Place(UIAnchor.TopLeft, new Vector2(82, -74), new Vector2(228, 14));
                view.Mp = UIFactory.Gauge(panel.Rect, UIGaugeKind.Mp, 290, 12, UIGaugeText.Above);
                view.Mp.Rt().Place(UIAnchor.TopLeft, new Vector2(20, -121), new Vector2(290, 12));
                view.Status = UIFactory.Label(panel.Rect, "", 18, color: UITheme.TextDim);
                view.Status.Rt().BottomStrip(28, 8, 18, 18);
                heroHud.Add(view);
            }
            if (dungeon)
            {
                var mapPanel = UIFactory.Panel(hud);
                mapPanel.Rect.Place(UIAnchor.TopRight, new Vector2(-30, -10), new Vector2(335, 290));
                minimap = UIFactory.Add<DungeonMapGraphic>(mapPanel.Rect, "Explored minimap");
                minimap.Rt().Stretch(14, 14, 14, 14);
                var controls = UIFactory.Panel(hud);
                controls.Rect.Place(UIAnchor.BottomRight, new Vector2(-30, 28), new Vector2(430, 355));
                HudButton(controls.Rect, "전진", new Vector2(0, -25), () => app.MoveDungeon(RelativeMove.Forward));
                HudButton(controls.Rect, "좌회전", new Vector2(-135, -95), () => app.TurnDungeon(-1));
                HudButton(controls.Rect, "조사", new Vector2(0, -95), app.InteractDungeon);
                HudButton(controls.Rect, "우회전", new Vector2(135, -95), () => app.TurnDungeon(1));
                HudButton(controls.Rect, "후퇴", new Vector2(0, -165), () => app.MoveDungeon(RelativeMove.Back));
                HudButton(controls.Rect, "대기", new Vector2(-135, -165), app.WaitDungeon);
                HudButton(controls.Rect, "지도", new Vector2(135, -165), OpenMapFromHud);
                HudButton(controls.Rect, "캠프", new Vector2(0, -245), ShowPause);
                // Phones: the 1920x1080 layout makes this pad tiny under a thumb, so grow it from its bottom-right corner.
                if (Application.isMobilePlatform) controls.Rect.localScale = Vector3.one * 1.35f;
            }
            else
            {
                var menu = UIFactory.Button(hud, "모험 수첩", ShowPause);
                menu.Rt().Place(UIAnchor.BottomRight, new Vector2(-30, 35), new Vector2(350, 76));
            }
            RefreshVitals();
        }
        void HudButton(RectTransform parent, string label, Vector2 position, Action action)
        {
            var b = UIFactory.Button(parent, label, () => { if (!BlocksWorldInput) { UIInput.Consume(); action(); } });
            b.Rt().Place(UIAnchor.Top, position, new Vector2(124, 62));
        }
        void RefreshVitals()
        {
            foreach (var h in heroHud)
            {
                var stats = PartyStats.EffectiveStats(app.DB, h.Hero);
                h.Name.text = $"{HeroName(h.Hero.Id)}  Lv.{h.Hero.Level}";
                h.Hp.SetValue(h.Hero.Hp, stats.MaxHp); h.Mp.SetValue(h.Hero.Mp, stats.MaxMp);
                var status = new List<string>();
                if (h.Hero.Hp <= 0) status.Add(T("knocked_out"));
                foreach (var id in h.Hero.Statuses.Keys) status.Add(app.DB.Statuses.TryGetValue(id, out var d) ? d.DisplayName : "상태 이상");
                h.Status.text = status.Count == 0 ? "정상" : string.Join(" · ", status);
            }
        }
        void OpenMapFromHud()
        {
            if (app.Dungeon == null || root.Screens.Count > 0 || root.Modals.Count > 0) return;
            UIInput.Consume();
            app.SetPaused(true);
            ShowMap();
            if (root.Screens.Top is GameMapScreen map) map.Closed = () => { UIInput.Consume(); app.SetPaused(false); };
        }
        void ShowMap()
        {
            if (app.State.Location != GameLocation.Dungeon || app.Dungeon == null)
            { UIModal.Alert(root.Modals, T("map_title"), "미궁 안에서 현재 층의 지도를 펼칠 수 있습니다."); return; }
            root.Screens.Push<GameMapScreen>(s => { s.Run = app.Dungeon; s.State = app.State; });
        }
    }
}
