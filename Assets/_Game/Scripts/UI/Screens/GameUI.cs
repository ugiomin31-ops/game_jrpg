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
        public bool BlocksWorldInput => app == null || root == null || root.Screens.Count > 0 || root.Modals.Count > 0 || app.Paused || UIAreaCard.Blocking
            || (app.Screen != GameScreen.Town && app.Screen != GameScreen.Dungeon);
        // Battle targeting always blocks world movement, but idle command/reward UI may be paused.
        public bool CanOpenPause => app != null && root != null && root.Screens.Count == 0 && root.Modals.Count == 0 && !app.Paused && !UIAreaCard.Blocking
            && (app.Screen == GameScreen.Town || app.Screen == GameScreen.Dungeon
                || (app.Screen == GameScreen.Battle && app.Battle != null && !app.Battle.Playing));
        GameApp app;
        UIRoot root;
        RectTransform hud, townPanel, partyRow, padPanel;
        float hudFitWidth = -1f;
        /// <summary>How much further from the right edge than its usual margin the pad / key sits (the town key moved beside the facility stack).</summary>
        float padReserveExtra;
        TextMeshProUGUI area, resources, townObjective, townReadiness, townIssues;
        DungeonMapGraphic minimap;
        readonly List<HeroHud> heroHud = new List<HeroHud>();
        sealed class HeroHud
        {
            public HeroState Hero;
            public TextMeshProUGUI Name, Status;
            public UIGauge Hp, Mp;
            public UIPortrait Portrait;
            // Exploration plates (slim slanted variant).
            public TextMeshProUGUI Level, HpText, MpText;
            public UISlantBar HpBar, MpBar;
            public UnityEngine.UI.Image Face;
            public GameObject StatusChip;
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
            heroHud.Clear(); area = null; resources = null; townPanel = null; townObjective = null; townReadiness = null; townIssues = null; townReadyStrip = null; townBadge = null; minimap = null; partyRow = null; padPanel = null; hudFitWidth = -1f; padReserveExtra = 0f;
            ClearDungeonHud();
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
        string HeroName(string id) => app.DB.Heroes.TryGetValue(id, out var d) ? d.DisplayName : "헌터";
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
                screen.ContinueDetail = screen.HasSave ? LatestSaveLine() : null;
                screen.NewGame = ShowNewGame;
                screen.ContinueGame = () => ShowSlots(false);
                screen.Settings = ShowSettings;
                screen.Credits = () => ShowCredits(null);
                screen.Quit = () => Confirm("게임 종료", "게임을 종료할까요?", app.Quit);
            });
        }
        /// <summary>Most recently written readable save at a glance: "1-3 변전실 · Lv.4" (leader level) or the town name.</summary>
        string LatestSaveLine()
        {
            string line = null;
            DateTime newest = DateTime.MinValue;
            for (int slot = -1; slot < 3; slot++)
            {
                if (!app.Saves.Exists(slot)) continue;
                try
                {
                    var time = app.Saves.SlotTime(slot) ?? DateTime.MinValue;
                    if (line != null && time <= newest) continue;
                    var s = app.Saves.Summary(slot);
                    string where = T("town", "새벽 길드");
                    if (s.Location != GameLocation.Town)
                    {
                        where = s.FloorLabel;
                        foreach (var floor in app.DB.Floors) if (floor.FloorLabel == s.FloorLabel) { where = floor.FloorLabel + " " + floor.AreaName; break; }
                    }
                    line = s.Levels.Count > 0 ? $"{where} · Lv.{s.Levels[0].Value}" : where;
                    newest = time;
                }
                catch (Exception e) when (e is IOException || e is UnauthorizedAccessException || e is SaveFormatException || e is Newtonsoft.Json.JsonException) { }
            }
            return line;
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
                            var lines = new List<string> { s.Location == GameLocation.Town ? T("town") : s.FloorLabel, $"{DifficultyName(s.Difficulty)} · {s.Gold:N0}만원", $"최심부 {s.DeepestFloorLabel}", $"플레이 시간 {(long)played.TotalHours:00}:{played.Minutes:00}:{played.Seconds:00}" };
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
                m.Add(T("recover"), app.RecoverFromDefeat, DefeatPenaltyText());
                m.Add("저장 불러오기", () => ShowSlots(false));
                m.Add(T("title_return"), ReturnTitle);
            }, cancel: false);
        }
        /// <summary>Defeat menu hint: the gold the guild restart takes (percent and amount), or the no-loss line when it takes none.</summary>
        string DefeatPenaltyText()
        {
            var state = app.State;
            int lost = TownServices.DefeatGoldLossAmount(state);
            if (lost <= 0) return T(state.Difficulty == Difficulty.Easy ? "defeat_easy" : "defeat_no_loss");
            int percent = (int)Math.Round(TownServices.DefeatGoldLoss(state.Difficulty) * 100);
            return app.DB.T("defeat_penalty", percent, lost.ToString("N0", System.Globalization.CultureInfo.InvariantCulture));
        }
        public void ShowPause()
        {
            if (!CanOpenPause) return;
            UIInput.Consume();
            app.SetPaused(true);
            var pause = Menu(app.Screen == GameScreen.Dungeon ? T("camp_title") : "모험 수첩", T("camp_hint"), m =>
            {
                bool inBattle = app.Screen == GameScreen.Battle;
                if (app.Screen == GameScreen.Town) m.Add("길드 시설", ShowTownDirectory, T("town_subtitle"));
                m.Add(T("party"), ShowParty, "헌터의 능력치, 장비와 기술을 확인하고 파티를 편성합니다.", icon: UIArtwork.Command("party"));
                m.Add(T("cmd_item"), ShowFieldItems, inBattle ? T("battle_unavailable") : T("camp_hint"), enabled: !inBattle, reason: T("battle_unavailable"), icon: UIArtwork.Command("item"));
                m.Add("의뢰 수첩", () => ShowQuests(false));
                m.Add("마물 도감", ShowBestiary, "발견한 마물과 장별 토벌 기록, 도감 달성 보상을 확인합니다.");
                m.Add(T("tool_map"), ShowMap, T("map_hint"), icon: UIArtwork.Command("map"));
                m.Add(T("save"), () => ShowSlots(true), inBattle ? "전투가 끝난 뒤 저장할 수 있습니다. 전투 이전의 자동 저장은 유지됩니다." : "현재 모험을 저장합니다.", enabled: !inBattle, reason: T("battle_unavailable"));
                m.Add("저장 불러오기", () => ShowSlots(false));
                m.Add(T("settings"), ShowSettings);
                m.Add(T("credits"), () => ShowCredits(null));
                m.Add(T("title_return"), ReturnTitle);
                m.Add("계속하기", () => root.Screens.Pop());
            });
            pause.CloseOnMenu = true;
            pause.Closed = () => { UIInput.Consume(); app.SetPaused(false); };
        }
        void ReturnTitle() => Confirm(T("title_return"), "저장하지 않은 진행은 잃게 됩니다. 타이틀로 돌아갈까요?", app.ShowTitle);
        void Update()
        {
            if (app == null || root == null) return;
            // M opens the full map while exploring (the map screen closes with M too).
            if (app.Screen == GameScreen.Dungeon && minimap != null && !BlocksWorldInput && UIInput.MapToggle)
            { OpenMapFromHud(); return; }
            if (!CanOpenPause) return;
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
            if (app.Dungeon == null || hud == null || minimap == null) return;
            RefreshDungeonHud();
        }
        /// <summary>Phones, tablets and touch laptops: bigger thumb-sized HUD controls.</summary>
        static bool TouchFirst => Application.isMobilePlatform || UITouch.Supported;
        void BuildHud(bool dungeon)
        {
            bool touch = TouchFirst;
            hud = UIFactory.Rect(Content, dungeon ? "Dungeon HUD" : "Town HUD").Stretch();
            if (dungeon)
            {
                BuildDungeonHud();
                RefreshVitals();
                FitHud();
                return;
            }
            // Town HUD (GameUI.TownHud.cs; the exploration HUD lives in GameUI.DungeonHud.cs).
            BuildTownHud();
            RefreshVitals();
            FitHud();
        }
        /// <summary>Shrinks the party row so it never runs under the movement pad on 16:9 phones and 4:3 tablets.</summary>
        void FitHud()
        {
            if (hud == null || partyRow == null || padPanel == null) return;
            float width = hud.rect.width;
            if (width <= 0f || Mathf.Approximately(width, hudFitWidth)) return;
            hudFitWidth = width;
            float padWidth = padPanel.rect.width * padPanel.localScale.x;
            float available = width - 30f - padWidth - padReserveExtra - 30f - 24f;
            if (minimap != null) available = width - 20f * hudUnit - padWidth - 36f * hudUnit - 24f * hudUnit;
            float scale = Mathf.Clamp(available / partyRow.sizeDelta.x, 0.55f, 1f);
            partyRow.localScale = new Vector3(scale, scale, 1f);
        }
        void LateUpdate()
        {
            FitHud();
            if (minimap != null && app?.State != null) RefreshCompass(false);
        }
        void RefreshVitals()
        {
            foreach (var h in heroHud)
            {
                var stats = PartyStats.EffectiveStats(app.DB, h.Hero);
                var status = new List<string>();
                if (h.Hero.Hp <= 0) status.Add(T("knocked_out"));
                foreach (var id in h.Hero.Statuses.Keys) status.Add(app.DB.Statuses.TryGetValue(id, out var d) ? d.DisplayName : "상태 이상");
                if (h.HpBar != null)
                {
                    // Slim exploration plate: name, level, thin HP/MP bars with numbers, a coral chip only when something is wrong.
                    h.Name.text = HeroLabel(h.Hero);
                    h.Level.text = $"Lv.{h.Hero.Level}";
                    if (h.Face != null) { h.Face.sprite = UIArtwork.Hero(h.Hero.Id); h.Face.enabled = h.Face.sprite != null; }
                    float ratio = stats.MaxHp > 0 ? (float)h.Hero.Hp / stats.MaxHp : 0f;
                    h.HpBar.FillColor = UISlant.FieldHpColor(ratio);
                    h.HpBar.SetValue(h.Hero.Hp, Mathf.Max(1, stats.MaxHp));
                    h.MpBar.SetValue(h.Hero.Mp, Mathf.Max(1, stats.MaxMp));
                    h.HpText.text = h.Hero.Hp.ToString();
                    h.HpText.color = h.Hero.Hp <= 0 ? UISlant.Coral : UISlant.Paper;
                    h.MpText.text = h.Hero.Mp.ToString();
                    bool bad = status.Count > 0;
                    h.StatusChip.SetActive(bad);
                    if (bad) h.Status.text = status.Count == 1 ? status[0] : $"{status[0]} 외 {status.Count - 1}";
                    if (h.Face != null) h.Face.color = h.Hero.Hp <= 0 ? new Color(0.45f, 0.45f, 0.5f, 1f) : Color.white;
                    continue;
                }
                h.Name.text = $"{HeroLabel(h.Hero)}  Lv.{h.Hero.Level}";
                if (h.Portrait != null) h.Portrait.SetSprite(UIArtwork.Hero(h.Hero.Id));
                h.Hp.SetValue(h.Hero.Hp, stats.MaxHp); h.Mp.SetValue(h.Hero.Mp, stats.MaxMp);
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
            { UIModal.Alert(root.Modals, T("map_title"), "게이트 안에서 현재 층의 지도를 펼칠 수 있습니다."); return; }
            root.Screens.Push<GameMapScreen>(s => { s.Run = app.Dungeon; s.State = app.State; s.DB = app.DB; });
        }
    }
}
