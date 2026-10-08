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
        RectTransform hud, partyRow, padPanel;
        float hudFitWidth = -1f;
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
            UIArtwork.HeroJob = id => app.State?.Hero(id)?.Job;
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
            heroHud.Clear(); area = null; resources = null; minimap = null; partyRow = null; padPanel = null; hudFitWidth = -1f;
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
        string ItemName(string id) => app.DB.Items.TryGetValue(id, out var d) ? d.DisplayName : app.DB.Equipment.ContainsKey(id) ? EquipmentName(id) : "물품";
        /// <summary>Equipment name with its smithy enhancement ("무쇠 장검 +3").</summary>
        string EquipmentName(string id) => app.DB.Equipment.TryGetValue(id ?? "", out var e) ? Enhancement.DisplayName(e, Enhancement.LevelOf(app.State, id)) : T("slot_none");
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

        /// <summary>Chest reveal: every item, piece of gear and the gold it held, shown once as icon cards.</summary>
        public void ShowLoot(TreasureContents contents, Action closed = null)
        {
            var entries = new List<UILootEntry>();
            if (contents != null)
            {
                foreach (var kv in contents.Equipment)
                {
                    app.DB.Equipment.TryGetValue(kv.Key, out var piece);
                    entries.Add(new UILootEntry
                    {
                        Icon = UIArtwork.Gear(kv.Key), Name = ItemName(kv.Key), Count = kv.Value,
                        Tag = piece == null ? "장비" : UITheme.RarityName(piece.Rarity) + " · " + T("slot_" + piece.Slot, "장비"),
                        Accent = piece == null ? UITheme.Dawn : UITheme.RarityColor(piece.Rarity),
                    });
                }
                foreach (var kv in contents.Items)
                {
                    app.DB.Items.TryGetValue(kv.Key, out var item);
                    entries.Add(new UILootEntry
                    {
                        Icon = UIArtwork.Item(kv.Key), Name = ItemName(kv.Key), Count = kv.Value,
                        Tag = UITheme.RarityName(item?.Rarity ?? 0) + " · " + UITheme.ItemCategory(item?.ItemType ?? ItemType.Healing), Accent = UITheme.RarityColor(item?.Rarity ?? 0),
                    });
                }
            }
            UILootPopup.Show(root.Modals, T("treasure_opened", "보물 상자를 열었다!"), entries, contents?.Gold ?? 0, closed);
        }
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
                        else Confirm("새 모험 시작", $"{DifficultyName(difficulty)} 난이도로 모험을 시작할까요?", () => app.NewGame(difficulty));
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
        /// <summary>Phones, tablets and touch laptops: bigger thumb-sized HUD controls.</summary>
        static bool TouchFirst => Application.isMobilePlatform || UITouch.Supported;
        void BuildHud(bool dungeon)
        {
            bool touch = TouchFirst;
            hud = UIFactory.Rect(Content, dungeon ? "Dungeon HUD" : "Town HUD").Stretch();
            var heading = UIFactory.Panel(hud);
            heading.Rect.TopStrip(UIRoot.Compact ? 104 : 128, 0, 30, dungeon || UIRoot.Compact ? 450 : 30);
            area = UIFactory.Label(heading.Rect, "", 36, color: UITheme.GoldBright);
            area.Rt().TopStrip(54, UIRoot.Compact ? 8 : 16, 25, 25);
            resources = UIFactory.Label(heading.Rect, "", UIRoot.Compact ? 25 : 23, color: UITheme.TextDim);
            resources.Rt().BottomStrip(40, UIRoot.Compact ? 6 : 12, 25, 25);
            // Party cards live in one row that shrinks (FitHud) when the screen is too narrow for cards + pad.
            partyRow = UIFactory.Rect(hud, "Party Row");
            partyRow.Place(UIAnchor.BottomLeft, new Vector2(30, 28), new Vector2(app.State.Party.Count * 350 - 20, 176));
            for (int i = 0; i < app.State.Party.Count; i++)
            {
                var hero = app.State.Party[i];
                var panel = UIFactory.Panel(partyRow);
                panel.Rect.Place(UIAnchor.BottomLeft, new Vector2(i * 350, 0), new Vector2(330, 176));
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
                var mapView = UIFactory.Rect(mapPanel.Rect, "Minimap view").Stretch(14, 14, 14, 14);
                mapView.gameObject.AddComponent<UnityEngine.UI.RectMask2D>();
                minimap = UIFactory.Add<DungeonMapGraphic>(mapView, "Explored minimap");
                minimap.Rt().Stretch();
                // Zoomed around the party: 9 cells across reads clearly at phone size.
                minimap.Window = 9;
                // Tapping/clicking the minimap opens the full map.
                var mapHit = mapPanel.gameObject.AddComponent<UnityEngine.UI.Button>();
                mapHit.transition = UnityEngine.UI.Selectable.Transition.None;
                mapHit.navigation = new UnityEngine.UI.Navigation { mode = UnityEngine.UI.Navigation.Mode.None };
                mapHit.onClick.AddListener(() => { if (!BlocksWorldInput) OpenMapFromHud(); });
                var camp = UIFactory.Button(hud, "캠프", () => { if (!BlocksWorldInput) ShowPause(); }, UIArtwork.Command("camp"));
                camp.Rt().Place(UIAnchor.TopRight, new Vector2(-30, -312), new Vector2(335, touch ? UIRoot.TouchTargetHeight : 64));
                // 3x3 pad: strafe / forward / strafe, turn / search / turn, wait / back / map.
                // Thumb-sized on touch screens (~7 mm tall on a phone); movement repeats while held.
                Vector2 cell = touch ? new Vector2(170, 108) : new Vector2(124, 62);
                const float gap = 12f, pad = 14f;
                padPanel = UIFactory.Panel(hud).Rect;
                padPanel.Place(UIAnchor.BottomRight, new Vector2(-30, 28), new Vector2(cell.x * 3 + gap * 2 + pad * 2, cell.y * 3 + gap * 2 + pad * 2));
                Vector2 At(int col, int row) => new Vector2(pad + col * (cell.x + gap), -pad - row * (cell.y + gap));
                HudButton(padPanel, "◀ 옆", At(0, 0), cell, () => app.MoveDungeon(RelativeMove.Left), true);
                HudButton(padPanel, "▲ 전진", At(1, 0), cell, () => app.MoveDungeon(RelativeMove.Forward), true);
                HudButton(padPanel, "옆 ▶", At(2, 0), cell, () => app.MoveDungeon(RelativeMove.Right), true);
                HudButton(padPanel, "↺ 회전", At(0, 1), cell, () => app.TurnDungeon(-1), true);
                HudButton(padPanel, "조사", At(1, 1), cell, app.InteractDungeon, false);
                HudButton(padPanel, "회전 ↻", At(2, 1), cell, () => app.TurnDungeon(1), true);
                HudButton(padPanel, "대기", At(0, 2), cell, app.WaitDungeon, false);
                HudButton(padPanel, "▼ 후퇴", At(1, 2), cell, () => app.MoveDungeon(RelativeMove.Back), true);
                HudButton(padPanel, "지도", At(2, 2), cell, OpenMapFromHud, false);
            }
            else
            {
                var menu = UIFactory.Button(hud, "모험 수첩", ShowPause);
                menu.Rt().Place(UIAnchor.BottomRight, new Vector2(-30, 35), new Vector2(350, touch ? UIRoot.TouchTargetHeight : 76));
                padPanel = menu.Rt();
            }
            RefreshVitals();
            FitHud();
        }
        void HudButton(RectTransform parent, string label, Vector2 position, Vector2 size, Action action, bool movement)
        {
            var b = UIFactory.Button(parent, label, () => { if (!BlocksWorldInput) { UIInput.Consume(); action(); } });
            b.Rt().Place(UIAnchor.TopLeft, position, size);
            // Same cadence as a held key (DungeonWorld: 0.28 s); a step animates for 0.24 s.
            if (movement) { b.HoldRepeat = 0.28f; b.Quiet = true; }
        }
        /// <summary>Shrinks the party row so it never runs under the movement pad on 16:9 phones and 4:3 tablets.</summary>
        void FitHud()
        {
            if (hud == null || partyRow == null || padPanel == null) return;
            float width = hud.rect.width;
            if (width <= 0f || Mathf.Approximately(width, hudFitWidth)) return;
            hudFitWidth = width;
            float padWidth = padPanel.rect.width * padPanel.localScale.x;
            float available = width - 30f - padWidth - 30f - 24f;
            float scale = Mathf.Clamp(available / partyRow.sizeDelta.x, 0.55f, 1f);
            partyRow.localScale = new Vector3(scale, scale, 1f);
        }
        void LateUpdate() => FitHud();
        void RefreshVitals()
        {
            foreach (var h in heroHud)
            {
                var stats = PartyStats.EffectiveStats(app.DB, h.Hero);
                h.Name.text = $"{HeroLabel(h.Hero)}  Lv.{h.Hero.Level}";
                if (h.Portrait != null) h.Portrait.SetSprite(UIArtwork.Hero(h.Hero.Id));
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
