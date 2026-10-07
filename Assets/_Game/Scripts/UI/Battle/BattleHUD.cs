using System;
using System.Collections.Generic;
using System.Text;
using Abyss.Logic;
using Abyss.Logic.Battle;
using Abyss.Runtime.Battle;
using TMPro;
using UnityEngine;
using UnityEngine.UI;

namespace Abyss.UI.Battle
{
    /// <summary>Snapshot HUD and command navigation; engine queries occur only at an input boundary.</summary>
    public sealed class BattleHUD : MonoBehaviour
    {
        sealed class Card
        {
            public UIPanel Panel;
            public TMP_Text Name, Status;
            public UIGauge Hp, Mp, Tp;
            public UIPips Shield;
            public BattleDisplayUnit Unit;
            public UIPortrait Portrait;
            public readonly Image[] StatusIcons = new Image[6];
        }
        sealed class Choice
        {
            public string Label, Description, Reason;
            public bool Enabled = true;
            public string TargetId;
            public Action Pick, Preview;
            public Sprite Icon;
        }
        readonly Dictionary<string, Card> _cards = new Dictionary<string, Card>();
        readonly List<Choice> _choices = new List<Choice>();
        readonly List<UIButton> _buttons = new List<UIButton>();
        readonly StringBuilder _text = new StringBuilder();
        readonly Dictionary<string, Sprite> _statusArt = new Dictionary<string, Sprite>(StringComparer.Ordinal);
        readonly StringBuilder _targetText = new StringBuilder();
        RectTransform _root, _party, _world, _menu, _rows, _detail, _cutin, _reward, _banner;
        TMP_Text _order, _log, _title, _description, _cutinTitle, _cutinText, _rewardText, _bannerText;
        UIButton _autoButton, _speedButton;
        Action _toggleSpeed;
        ScrollRect _detailScroll;
        ScrollRect _rewardScroll;
        TMP_Text _menuHint, _rewardCounter;
        RectTransform _announce, _announceBand;
        TMP_Text _announceTitle, _announceSub;
        CanvasGroup _announceGroup;
        BattleEngine _engine;
        GameDB _db;
        Camera _camera;
        Action<BattleCommand> _submit;
        Action _toggleAuto, _back;
        Action<int> _rewardPage;
        Action<string> _preview;
        BattleUnit _actor;
        int _page, _focus, _openedFrame;
        bool _input, _auto;
        public bool Paused { get; set; }
        /// <summary>Phones/tablets: taller command rows and buttons sized for a thumb.</summary>
        static bool TouchUI => Application.isMobilePlatform || UITouch.Supported;
        static int PerPage => TouchUI ? 4 : 6;
        /// <summary>Landscape phone (900-unit canvas): slimmer bars and cards so the arena stays visible.</summary>
        static bool Compact => UIRoot.Compact;
        static float RowHeight => TouchUI ? UIRoot.TouchTargetHeight : 48f;
        static float RowStep => TouchUI ? RowHeight + 6f : 56f;
        static float NavHeight => TouchUI ? UIRoot.TouchTargetHeight : 46f;
        static float MenuWidth => Compact ? 500f : 570f;
        RectTransform _logPanel, _orderRow;
        TMP_Text _roundLabel;
        readonly List<(RectTransform Root, UIPortrait Face, Image Mark)> _orderChips = new List<(RectTransform, UIPortrait, Image)>();
        public bool CommandRootOpen => _input && _back == null && _reward == null;

        public void Initialize(Transform parent, Camera camera, GameDB db, Action<BattleCommand> submit,
            Action toggleAuto, Action<string> preview)
        {
            _camera = camera; _db = db; _submit = submit; _toggleAuto = toggleAuto; _preview = preview;
            _statusArt.Clear();
            foreach (var status in db.Statuses) _statusArt.Add(status.Key, UIArtwork.Status(status.Key));
            _root = UIFactory.Rect(parent, "Battle HUD").Stretch();
            _world = UIFactory.Rect(_root, "Enemy gauges").Stretch();
            _party = UIFactory.Rect(_root, "Party").BottomStrip(Compact ? 150 : 210, Compact ? 10 : 16, Compact ? 22 : 28, 28);
            var top = UIFactory.Panel(_root, UIPanelStyle.Glass, false);
            top.Rect.TopStrip(Compact ? 64 : 84, Compact ? 12 : 18, Compact ? 22 : 32, Compact ? 440 : 500);
            _order = UIFactory.Label(top.transform, "", Compact ? 25 : 23); _order.Rt().Stretch(22, Compact ? 8 : 14, 22, Compact ? 8 : 14);
            _order.overflowMode = TextOverflowModes.Ellipsis;
            if (Compact)
            {
                // Phones: the turn order is a row of portraits (active one enlarged) instead of a line of names.
                _order.gameObject.SetActive(false);
                _roundLabel = UIFactory.Label(top.transform, "", 26, UIFont.Title, UITheme.GoldBright);
                _roundLabel.Rt().Place(UIAnchor.Left, new Vector2(18, 0), new Vector2(110, 50));
                _orderRow = UIFactory.Rect(top.transform, "Turn order");
                _orderRow.Stretch(128, 0, 12, 0);
            }
            _autoButton = UIFactory.Button(_root, "자동: OFF", ToggleAuto);
            _autoButton.Rt().Place(UIAnchor.TopRight, Compact ? new Vector2(-22, -12) : new Vector2(-32, -26), Compact ? new Vector2(230, TouchUI ? UIRoot.TouchTargetHeight : 64) : new Vector2(260, TouchUI ? UIRoot.TouchTargetHeight : 62));
            var logPanel = UIFactory.Panel(_root, UIPanelStyle.Dark, false);
            _logPanel = logPanel.Rect;
            if (Compact) logPanel.Rect.Place(UIAnchor.Top, new Vector2(0, -88), new Vector2(820, 48));
            else logPanel.Rect.TopStrip(52, 112, 220, 220);
            _log = UIFactory.Label(logPanel.transform, "", Compact ? 25 : 22, align: TextAlignmentOptions.Center);
            _log.Rt().Stretch(10, 4, 10, 4);
            _log.overflowMode = TextOverflowModes.Ellipsis;
            logPanel.gameObject.SetActive(false);
            var menu = UIFactory.Panel(_root, UIPanelStyle.Ornate);
            float menuHeight = Compact ? 74 + PerPage * RowStep + NavHeight + 30 : TouchUI ? 100 + PerPage * RowStep + NavHeight + 40 : 510;
            _menu = menu.Rect.Place(UIAnchor.BottomRight, Compact ? new Vector2(-22, 170) : new Vector2(-32, 245), new Vector2(MenuWidth, menuHeight));
            _title = UIFactory.Label(menu.transform, "", Compact ? 30 : 29, UIFont.Title, UITheme.GoldBright); _title.Rt().TopStrip(54, Compact ? 12 : 16, 24, 24);
            _menuHint = UIFactory.Label(menu.transform, "↑↓ 선택 · Q/E 페이지 · ←→ 상세", 18, color: UITheme.TextDim);
            _menuHint.Rt().TopStrip(25, 62, 24, 24);
            _menuHint.gameObject.SetActive(!Compact);
            _rows = UIFactory.Rect(menu.transform, "Choices").Stretch(22, Compact ? 70 : 100, 22, NavHeight + 26);
            var detail = UIFactory.Panel(_root, UIPanelStyle.Glass);
            _detail = Compact ? detail.Rect.Place(UIAnchor.TopLeft, new Vector2(22, -86), new Vector2(760, 124))
                : detail.Rect.Place(UIAnchor.TopLeft, new Vector2(32, -178), new Vector2(1100, 100));
            _detailScroll = UIFactory.ScrollView(detail.transform, out var detailContent, name: "Command description");
            _detailScroll.Rt().Stretch(24, 12, 24, 12);
            _description = UIFactory.Paragraph(detailContent, "", Compact ? 25 : 23);
            _description.overflowMode = TextOverflowModes.Overflow;
            var cutin = UIFactory.Panel(_root, UIPanelStyle.Ornate);
            _cutin = cutin.Rect.Place(UIAnchor.Center, Vector2.zero, new Vector2(1100, 255));
            _cutinTitle = UIFactory.Label(cutin.transform, "", 42, align: TextAlignmentOptions.Center);
            _cutinTitle.Rt().TopStrip(74, 26, 30, 30);
            _cutinText = UIFactory.Paragraph(cutin.transform, "", 29); _cutinText.Rt().Stretch(48, 108, 48, 22);
            _cutin.gameObject.SetActive(false);
            var banner = UIFactory.Panel(_root, UIPanelStyle.Dark, false);
            _banner = banner.Rect.Place(UIAnchor.Top, new Vector2(0, Compact ? -150 : -182), new Vector2(760, 74));
            _bannerText = UIFactory.Label(banner.transform, "", 36, align: TextAlignmentOptions.Center);
            _bannerText.Rt().Stretch(16, 6, 16, 6);
            _bannerText.overflowMode = TextOverflowModes.Ellipsis;
            _banner.gameObject.SetActive(false);
            BuildAnnounce();
            Lock();
        }

        /// <summary>Centre-screen call-out for battle start / victory / defeat: a light band that opens, big title, subtitle.</summary>
        void BuildAnnounce()
        {
            _announce = UIFactory.Rect(_root, "Announce");
            _announce.anchorMin = new Vector2(0f, 0.5f); _announce.anchorMax = new Vector2(1f, 0.5f);
            _announce.sizeDelta = new Vector2(0f, 250f); _announce.anchoredPosition = new Vector2(0f, 70f);
            _announceGroup = _announce.gameObject.AddComponent<CanvasGroup>();
            _announceGroup.blocksRaycasts = false; _announceGroup.interactable = false;
            _announceBand = UIFactory.Rect(_announce, "Band");
            _announceBand.anchorMin = Vector2.zero; _announceBand.anchorMax = Vector2.one; _announceBand.sizeDelta = Vector2.zero;
            var band = UIFactory.Image(_announceBand, UISprites.White, new Color(0.02f, 0.03f, 0.1f, 0.78f), "Fill");
            band.rectTransform.Stretch();
            foreach (float y in new[] { 0f, 1f })
            {
                var line = UIFactory.Image(_announceBand, UISprites.GlowLine, UITheme.Gold, y == 0f ? "Bottom line" : "Top line");
                line.rectTransform.anchorMin = new Vector2(0f, y); line.rectTransform.anchorMax = new Vector2(1f, y);
                line.rectTransform.sizeDelta = new Vector2(0f, 6f); line.rectTransform.anchoredPosition = Vector2.zero;
            }
            _announceTitle = UIFactory.Label(_announce, "", 104, UIFont.Title, UITheme.GoldBright, TextAlignmentOptions.Center, UITextFx.Heavy, "Title");
            _announceTitle.Rt().Stretch(40f, 12f, 40f, 72f);
            _announceSub = UIFactory.Label(_announce, "", 34, UIFont.Bold, UITheme.Text, TextAlignmentOptions.Center, UITextFx.Outline, "Subtitle");
            _announceSub.Rt().Stretch(40f, 182f, 40f, 14f);
            _announce.gameObject.SetActive(false);
        }

        /// <summary>Plays the call-out: band opens (0.2 s), title punches in, holds, then fades. Returns the total time.</summary>
        public float Announce(string title, string subtitle, Color accent, float hold = 1.1f)
        {
            if (_announce == null) return 0f;
            UITween.Kill(_announce);
            _announce.gameObject.SetActive(true);
            _announce.SetAsLastSibling();
            _announceTitle.text = title;
            _announceTitle.color = Color.Lerp(UITheme.GoldBright, accent, 0.35f);
            _announceSub.text = subtitle ?? "";
            _announceGroup.alpha = 1f;
            _announceBand.localScale = new Vector3(1f, 0f, 1f);
            _announceTitle.transform.localScale = Vector3.one * 1.7f;
            _announceTitle.alpha = 0f; _announceSub.alpha = 0f;
            UITween.To(_announce, 0.22f, t => _announceBand.localScale = new Vector3(1f, t, 1f), UIEase.OutCubic);
            UITween.To(_announce, 0.32f, t =>
            {
                _announceTitle.transform.localScale = Vector3.one * Mathf.Lerp(1.7f, 1f, t);
                _announceTitle.alpha = t;
            }, UIEase.OutBack, 0.12f);
            UITween.To(_announce, 0.3f, t => _announceSub.alpha = t, UIEase.OutCubic, 0.32f);
            float total = 0.45f + hold + 0.35f;
            UITween.To(_announce, 0.35f, t => _announceGroup.alpha = 1f - t, UIEase.InQuad, 0.45f + hold)
                .OnComplete(() => { if (_announce != null) _announce.gameObject.SetActive(false); });
            return total;
        }

        public void AddUnit(BattleDisplayUnit unit)
        {
            var panel = UIFactory.Panel(unit.Side == BattleSide.Party ? _party : _world, UIPanelStyle.Glass, false);
            var card = new Card { Panel = panel, Unit = unit };
            if (unit.Side == BattleSide.Party)
            {
                if (Compact) panel.Rect.Place(UIAnchor.BottomLeft, new Vector2(unit.Slot * 368, 0), new Vector2(356, 148));
                else panel.Rect.Place(UIAnchor.BottomLeft, new Vector2(unit.Slot * 455, 0), new Vector2(435, 206));
            }
            else panel.Rect.sizeDelta = Compact ? new Vector2(unit.Boss ? 300 : 210, 92) : new Vector2(unit.Boss ? 320 : 210, 134);
            if (Compact) { AddCompactCard(unit, panel); return; }
            // Tapping/clicking a unit's card picks it while a single target is being chosen.
            string unitId = unit.Id;
            var tap = panel.gameObject.AddComponent<Button>();
            tap.transition = Selectable.Transition.None;
            tap.navigation = new Navigation { mode = Navigation.Mode.None };
            tap.onClick.AddListener(() => TapUnit(unitId));
            card.Name = UIFactory.Label(panel.transform, unit.Name, unit.Side == BattleSide.Party ? 23 : 21);
            card.Name.Rt().TopStrip(34, 8, unit.Side == BattleSide.Party ? 90 : 16, 16);
            card.Name.overflowMode = TextOverflowModes.Ellipsis;
            float width = unit.Side == BattleSide.Party ? 395 : (unit.Boss ? 280 : 170);
            if (unit.Side == BattleSide.Party)
            {
                card.Portrait = UIFactory.Portrait(panel.transform, 64);
                card.Portrait.Rt().Place(UIAnchor.TopLeft, new Vector2(12, -8), new Vector2(64, 64));
                card.Portrait.SetSprite(UIArtwork.Hero(unit.DefId));
            }
            float hpLeft = unit.Side == BattleSide.Party ? 90 : 20;
            float hpWidth = unit.Side == BattleSide.Party ? 325 : width;
            card.Hp = UIFactory.Gauge(panel.transform, UIGaugeKind.Hp, hpWidth, 13, UIGaugeText.Above);
            card.Hp.Rt().Place(UIAnchor.TopLeft, new Vector2(hpLeft, unit.Side == BattleSide.Party ? -76 : -58), new Vector2(hpWidth, 13));
            if (unit.Side == BattleSide.Party)
            {
                card.Mp = UIFactory.Gauge(panel.transform, UIGaugeKind.Mp, width, 9, UIGaugeText.Above);
                card.Mp.Rt().Place(UIAnchor.TopLeft, new Vector2(20, -121), new Vector2(width, 9));
                card.Tp = UIFactory.Gauge(panel.transform, UIGaugeKind.Tp, width, 9, UIGaugeText.Above);
                card.Tp.Rt().Place(UIAnchor.TopLeft, new Vector2(20, -163), new Vector2(width, 9));
            }
            else
            {
                card.Shield = UIFactory.Pips(panel.transform, unit.MaxShield, 14);
                card.Shield.Rt().Place(UIAnchor.TopLeft, new Vector2(16, -82), new Vector2(width, 14));
            }
            card.Status = UIFactory.Label(panel.transform, "", 17);
            card.Status.Rt().BottomStrip(unit.Side == BattleSide.Party ? 26 : 28, 6, 12, 12);
            card.Status.overflowMode = TextOverflowModes.Ellipsis;
            for (int i = 0; i < card.StatusIcons.Length; i++)
            {
                var icon = UIFactory.Icon(panel.transform, null, 20);
                icon.rectTransform.Place(UIAnchor.TopLeft, new Vector2(14 + i * 24, 24), new Vector2(20, 20));
                icon.enabled = false;
                card.StatusIcons[i] = icon;
            }
            _cards.Add(unit.Id, card); Sync(unit, true);
        }

        /// <summary>
        /// Phone cards. Party: portrait, name, HP bar with numbers, MP and TP side by side, status line (148 tall).
        /// Enemy: slim name plate with HP bar, shield pips and weakness line (92 tall) so it covers less of the monster.
        /// </summary>
        void AddCompactCard(BattleDisplayUnit unit, UIPanel panel)
        {
            var card = new Card { Panel = panel, Unit = unit };
            string unitId = unit.Id;
            var tap = panel.gameObject.AddComponent<Button>();
            tap.transition = Selectable.Transition.None;
            tap.navigation = new Navigation { mode = Navigation.Mode.None };
            tap.onClick.AddListener(() => TapUnit(unitId));
            bool party = unit.Side == BattleSide.Party;
            float w = panel.Rect.sizeDelta.x;
            card.Name = UIFactory.Label(panel.transform, unit.Name, party ? 26 : 21, UIFont.Bold, party ? UITheme.GoldBright : Color.white);
            card.Name.overflowMode = TextOverflowModes.Ellipsis;
            if (party)
            {
                card.Portrait = UIFactory.Portrait(panel.transform, 62);
                card.Portrait.Rt().Place(UIAnchor.TopLeft, new Vector2(8, -8), new Vector2(62, 62));
                card.Portrait.SetSprite(UIArtwork.Hero(unit.DefId));
                // TMP's ellipsis hides a line taller than its rect, so the name strip is a little taller than the type.
                card.Name.Rt().TopStrip(38, 2, 80, 12);
                card.Hp = UIFactory.Gauge(panel.transform, UIGaugeKind.Hp, w - 94, 14, UIGaugeText.Above);
                card.Hp.Rt().Place(UIAnchor.TopLeft, new Vector2(80, -68), new Vector2(w - 94, 14));
                float half = (w - 40) * 0.5f;
                card.Mp = UIFactory.Gauge(panel.transform, UIGaugeKind.Mp, half, 9, UIGaugeText.Above);
                card.Mp.Rt().Place(UIAnchor.TopLeft, new Vector2(14, -110), new Vector2(half, 9));
                card.Tp = UIFactory.Gauge(panel.transform, UIGaugeKind.Tp, half, 9, UIGaugeText.Above);
                card.Tp.Rt().Place(UIAnchor.TopLeft, new Vector2(26 + half, -110), new Vector2(half, 9));
                card.Status = UIFactory.Label(panel.transform, "", 18);
                card.Status.Rt().BottomStrip(26, 2, 12, 12);
            }
            else
            {
                card.Name.Rt().TopStrip(30, 4, 12, 12);
                card.Hp = UIFactory.Gauge(panel.transform, UIGaugeKind.Hp, w - 24, 11, UIGaugeText.None);
                card.Hp.Rt().Place(UIAnchor.TopLeft, new Vector2(12, -40), new Vector2(w - 24, 11));
                card.Shield = UIFactory.Pips(panel.transform, unit.MaxShield, 15);
                card.Shield.Rt().Place(UIAnchor.TopLeft, new Vector2(12, -58), new Vector2(w - 24, 15));
                card.Status = UIFactory.Label(panel.transform, "", 17, UIFont.Bold, UITheme.GoldBright);
                card.Status.Rt().BottomStrip(20, 2, 12, 12);
            }
            card.Status.overflowMode = TextOverflowModes.Ellipsis;
            for (int i = 0; i < card.StatusIcons.Length; i++)
            {
                var icon = UIFactory.Icon(panel.transform, null, 24);
                icon.rectTransform.Place(UIAnchor.TopLeft, new Vector2(10 + i * 28, 28), new Vector2(24, 24));
                icon.enabled = false;
                card.StatusIcons[i] = icon;
            }
            _cards.Add(unit.Id, card); Sync(unit, true);
        }

        public void Sync(BattleDisplayUnit unit, bool instant = false)
        {
            if (!_cards.TryGetValue(unit.Id, out var card)) return;
            card.Hp.SetValue(unit.Hp, unit.MaxHp, instant);
            card.Mp?.SetValue(unit.Mp, unit.MaxMp, instant); card.Tp?.SetValue(unit.Tp, unit.MaxTp, instant);
            card.Shield?.Set(unit.Shield, unit.MaxShield);
            _text.Clear();
            if (!unit.Alive) _text.Append("전투불능 ");
            if (unit.Broken) _text.Append("BREAK! ");
            if (unit.Guarding) _text.Append("방어 ");
            foreach (var status in unit.Statuses.Values) _text.Append(status.Name).Append('(').Append(status.Turns).Append(") ");
            if (unit.Side == BattleSide.Enemy)
                foreach (int element in unit.Weaknesses) _text.Append(ElementName(element)).Append("↓ ");
            card.Status.text = _text.ToString();
            int statusIndex = 0;
            foreach (var status in unit.Statuses.Values)
            {
                if (statusIndex == card.StatusIcons.Length) break;
                var icon = card.StatusIcons[statusIndex++];
                icon.sprite = _statusArt[status.Id];
                icon.enabled = true;
            }
            while (statusIndex < card.StatusIcons.Length) card.StatusIcons[statusIndex++].enabled = false;
            card.Name.color = unit.Alive ? Color.white : new Color(.6f, .6f, .65f);
        }

        public void ShowOrder(int round, IReadOnlyList<string> order, string active)
        {
            if (_orderRow != null) { ShowOrderChips(round, order, active); return; }
            _text.Clear(); _text.Append("ROUND ").Append(round).Append("    ");
            foreach (string id in order)
            {
                if (!_cards.TryGetValue(id, out var card) || !card.Unit.Alive) continue;
                if (id == active) _text.Append("<color=#FFE29A>▶ ");
                _text.Append(card.Unit.Name);
                if (id == active) _text.Append("</color>");
                _text.Append("  ›  ");
            }
            _order.text = _text.ToString();
        }

        /// <summary>Action line under the turn order; hidden when empty and for round numbers (the order bar shows them).</summary>
        void ShowOrderChips(int round, IReadOnlyList<string> order, string active)
        {
            _roundLabel.text = "R" + round;
            int n = 0;
            float x = 0f;
            foreach (string id in order)
            {
                if (!_cards.TryGetValue(id, out var card) || !card.Unit.Alive) continue;
                if (n == _orderChips.Count)
                {
                    var root = UIFactory.Rect(_orderRow, "Chip");
                    root.anchorMin = root.anchorMax = new Vector2(0f, 0.5f);
                    root.pivot = new Vector2(0f, 0.5f);
                    var mark = UIFactory.Image(root, UISprites.Circle, Color.white, "Side");
                    mark.rectTransform.Stretch(-3f, -3f, -3f, -3f);
                    root.sizeDelta = new Vector2(56f, 56f);
                    var face = UIFactory.Portrait(root, 56f);
                    face.Rt().Place(UIAnchor.Center, Vector2.zero, new Vector2(56f, 56f));
                    _orderChips.Add((root, face, mark));
                }
                var chip = _orderChips[n++];
                bool now = id == active, party = card.Unit.Side == BattleSide.Party;
                float scale = now ? 1f : 0.78f;
                chip.Root.gameObject.SetActive(true);
                chip.Root.localScale = new Vector3(scale, scale, 1f);
                chip.Root.anchoredPosition = new Vector2(x, 0f);
                x += 56f * scale + 8f;
                chip.Face.SetSprite(party ? UIArtwork.Hero(card.Unit.DefId) : UIArtwork.Enemy(card.Unit.DefId));
                chip.Mark.color = now ? UITheme.Dawn : party ? new Color(0.35f, 0.6f, 1f, 0.9f) : new Color(1f, 0.3f, 0.35f, 0.9f);
            }
            for (int i = n; i < _orderChips.Count; i++) _orderChips[i].Root.gameObject.SetActive(false);
        }

        public void Log(string text)
        {
            _log.text = text;
            bool show = !string.IsNullOrEmpty(text) && !text.StartsWith("ROUND ");
            if (_logPanel != null && _logPanel.gameObject.activeSelf != show) _logPanel.gameObject.SetActive(show);
        }
        /// <summary>Adds the battle-speed button (left of 자동) that cycles 1x / 1.5x / 2x.</summary>
        public void EnableSpeedToggle(string label, Action toggle)
        {
            _toggleSpeed = toggle;
            _speedButton = UIFactory.Button(_root, label, () => { if (!Paused) _toggleSpeed?.Invoke(); });
            _speedButton.Rt().Place(UIAnchor.TopRight, Compact ? new Vector2(-266, -12) : new Vector2(-306, -26), new Vector2(150, TouchUI ? UIRoot.TouchTargetHeight : 62));
        }
        public void SetSpeedLabel(string label) { if (_speedButton != null) _speedButton.SetLabel(label); }
        public void SetAuto(bool value) { _auto = value; _autoButton.SetLabel(value ? "자동전투 ON" : "자동전투 OFF"); }
        void ToggleAuto() { if (!Paused) _toggleAuto?.Invoke(); }
        public void Lock()
        {
            // Battle teardown can run after the HUD's panels were destroyed with the UI root.
            _input = false;
            if (_menu != null) _menu.gameObject.SetActive(false);
            if (_detail != null) _detail.gameObject.SetActive(false);
            _preview?.Invoke(null);
        }
        public void ShowCommands(BattleEngine engine)
        {
            _engine = engine; _actor = engine.ActiveHero;
            if (_actor == null) { Lock(); return; }
            // Choosing a command: the description panel takes the top-left; the last action line steps aside.
            if (Compact && _logPanel != null) _logPanel.gameObject.SetActive(false);
            var options = engine.GetCommandOptions(_actor);
            BeginChoices(_actor.DisplayName + " · 행동", null);
            Add("공격", "장비 무기로 적 하나를 공격합니다.", options.CanAttack, null, () => Targets(BattleCommand.Attack(null)), icon: UIArtwork.Command("attack"));
            Add("스킬", "MP를 사용하여 스킬을 시전합니다.", true, null, () => Skills(false), icon: UIArtwork.Command("skill"));
            Add("궁극기", "TP 100으로 강력한 궁극기를 사용합니다.", true, null, () => Skills(true), icon: UIArtwork.Command("ultimate"));
            Add("아이템", "보유한 소비 아이템을 사용합니다.", true, null, Items, icon: UIArtwork.Command("item"));
            Add("방어", "다음 턴까지 받는 피해를 줄입니다.", options.CanGuard, null, () => Targets(BattleCommand.Guard()), icon: UIArtwork.Command("guard"));
            Add("도주", "전투에서 도주를 시도합니다.", options.CanFlee, options.FleeReasonKey, () => Targets(BattleCommand.Flee()), icon: UIArtwork.Command("flee"));
            Add("자동 " + (_auto ? "OFF" : "ON"), "자동 전투 설정은 다음 전투에도 유지됩니다. 회복·해제·약점·버프를 판단하며, 소모 아이템은 직접 사용하세요. 상단 버튼으로 끌 수 있습니다.", true, null, ToggleAuto, icon: UIArtwork.Command("auto"));
            Render();
        }
        void Skills(bool ultimate, Action back = null)
        {
            Action returnToCommands = back ?? RememberChoices(() => ShowCommands(_engine));
            BeginChoices(ultimate ? "궁극기" : "스킬", returnToCommands);
            foreach (var option in _engine.GetCommandOptions(_actor).Skills)
            {
                if (option.IsUltimate != ultimate) continue;
                var captured = option;
                Add(option.DisplayName + "  MP " + option.MpCost + " / TP " + option.TpCost,
                    option.Skill.Description + "\n" + ElementName((int)option.Skill.Element) + " · " + RuleName(option.Target) + " · " + option.Skill.HitCount + "회",
                    option.Usable, option.ReasonKey, () => Targets(BattleCommand.Skill(captured.Id), RememberChoices(() => Skills(ultimate, returnToCommands))), icon: UIArtwork.Element(option.Skill.Element));
            }
            Render();
        }
        void Items() => Items(null);
        void Items(Action back)
        {
            Action returnToCommands = back ?? RememberChoices(() => ShowCommands(_engine));
            BeginChoices("아이템", returnToCommands);
            foreach (var option in _engine.GetCommandOptions(_actor).Items)
            {
                var captured = option;
                Add(option.DisplayName + " ×" + option.Count, option.Item.Description + "\n" + RuleName(option.Target),
                    option.Usable, option.ReasonKey, () => Targets(BattleCommand.Item(captured.Id), RememberChoices(() => Items(returnToCommands))), icon: UIArtwork.Item(captured.Id));
            }
            Render();
        }
        Action RememberChoices(Action rebuild)
        {
            int page = _page, focus = _focus;
            return () => { rebuild(); Page(page); Focus(focus); };
        }
        void Targets(BattleCommand command, Action back = null)
        {
            var targets = _engine.ValidTargets(_actor, command);
            var rule = _engine.GetTargetRule(_actor, command);
            BeginChoices("대상 선택 · " + RuleName(rule), back ?? RememberChoices(() => ShowCommands(_engine)));
            if (rule == TargetRule.SingleEnemy || rule == TargetRule.SingleAlly)
            {
                foreach (var target in targets)
                {
                    string id = target.Id;
                    Add(target.DisplayName, TargetDescription(id), true, null,
                        () => { command.TargetId = id; Commit(command); }, () => _preview?.Invoke(id), target.Side == BattleSide.Party ? UIArtwork.Hero(target.DefId) : UIArtwork.Enemy(target.DefId));
                    _choices[_choices.Count - 1].TargetId = id;
                }
            }
            else
            {
                _targetText.Clear();
                foreach (var target in targets) _targetText.Append(TargetDescription(target.Id)).Append('\n');
                Add("확인 · " + RuleName(rule), _targetText.ToString(), targets.Count > 0 || rule == TargetRule.None,
                    "reason_no_target", () => Commit(command), () => _preview?.Invoke(targets.Count == 1 ? targets[0].Id : null));
            }
            Render();
        }
        /// <summary>Card tap: first tap on an unfocused target focuses it (preview + details), the next tap confirms.</summary>
        void TapUnit(string id)
        {
            if (!_input || Paused || _reward != null) return;
            int index = _choices.FindIndex(c => c.TargetId == id);
            if (index < 0) return;
            int page = index / PerPage;
            if (page != _page) { _page = page; Render(); }
            if (_focus == index % PerPage) { UIInput.Consume(); Select(index); }
            else { UISound.Play(UISoundId.Move); Focus(index % PerPage); }
        }
        string TargetDescription(string id)
        {
            if (!_cards.TryGetValue(id, out var c)) return id;
            var u = c.Unit;
            _text.Clear(); _text.Append(u.Name).Append("  HP ").Append(u.Hp).Append('/').Append(u.MaxHp);
            if (u.MaxShield > 0) _text.Append("  실드 ").Append(u.Shield).Append('/').Append(u.MaxShield);
            if (u.Broken) _text.Append("  BREAK · 받는 피해 증가");
            if (!u.Alive) _text.Append("  전투불능");
            _text.Append("\n알려진 약점: ");
            if (u.Weaknesses.Count == 0) _text.Append("미확인");
            foreach (int element in u.Weaknesses) _text.Append(ElementName(element)).Append(' ');
            foreach (var status in u.Statuses.Values) _text.Append("\n").Append(status.Name).Append(" · ").Append(status.Turns).Append("턴");
            return _text.ToString();
        }
        void Commit(BattleCommand command) { Lock(); UIInput.Consume(); _submit(command); }
        void BeginChoices(string title, Action back)
        {
            _choices.Clear(); _page = 0; _focus = 0; _back = back; _title.text = title;
            _menu.gameObject.SetActive(true); _detail.gameObject.SetActive(true);
            _input = true; _openedFrame = Time.frameCount;
        }
        void Add(string label, string description, bool enabled, string reason, Action pick, Action preview = null, Sprite icon = null)
        {
            _choices.Add(new Choice { Label = label, Description = description, Enabled = enabled, Reason = reason, Pick = pick, Preview = preview, Icon = icon });
        }
        void Render()
        {
            foreach (var b in _buttons) { b.gameObject.SetActive(false); Destroy(b.gameObject); }
            _buttons.Clear();
            int first = _page * PerPage;
            for (int i = first; i < Math.Min(first + PerPage, _choices.Count); i++)
            {
                int index = i; var choice = _choices[i];
                var button = UIFactory.Button(_rows, choice.Label, () => Select(index), choice.Icon);
                button.Interactable = choice.Enabled;
                button.DisabledReason = choice.Enabled ? null : Reason(choice.Reason);
                button.Rt().Place(UIAnchor.TopLeft, new Vector2(0, -(i - first) * RowStep), new Vector2(MenuWidth - 44, RowHeight));
                button.Hovered += () => Focus(index - first);
                _buttons.Add(button);
            }
            var navigation = UIFactory.Button(_menu, "← 뒤로", () => _back?.Invoke());
            navigation.Rt().Place(UIAnchor.BottomLeft, new Vector2(22, 14), new Vector2(160, NavHeight));
            navigation.Interactable = _back != null; _buttons.Add(navigation);
            var prev = UIFactory.Button(_menu, "◀", () => Page(-1));
            prev.Rt().Place(UIAnchor.BottomLeft, new Vector2(200, 14), new Vector2(TouchUI ? 110 : 70, NavHeight));
            prev.Interactable = _page > 0; _buttons.Add(prev);
            var next = UIFactory.Button(_menu, (_page + 1) + "/" + Math.Max(1, (_choices.Count + PerPage - 1) / PerPage) + " ▶", () => Page(1));
            next.Rt().Place(UIAnchor.BottomRight, new Vector2(-22, 14), new Vector2(180, NavHeight));
            next.Interactable = first + PerPage < _choices.Count; _buttons.Add(next);
            Focus(0);
            if (_choices.Count == 0) _description.text = "사용 가능한 항목이 없습니다. 뒤로 돌아가세요.";
        }
        void Page(int delta)
        {
            int next = Mathf.Clamp(_page + delta, 0, Math.Max(0, (_choices.Count - 1) / PerPage));
            if (next == _page) return; _page = next; Render();
        }
        void Focus(int index)
        {
            int count = Math.Min(PerPage, _choices.Count - _page * PerPage);
            if (count <= 0) return;
            _focus = (index % count + count) % count;
            for (int i = 0; i < _buttons.Count; i++) _buttons[i].Focused = i == _focus;
            var choice = _choices[_page * PerPage + _focus];
            _description.text = choice.Label + (choice.Enabled ? "" : " · 사용 불가: " + Reason(choice.Reason)) + "\n" + choice.Description;
            LayoutRebuilder.ForceRebuildLayoutImmediate(_detailScroll.content);
            _detailScroll.StopMovement();
            _detailScroll.verticalNormalizedPosition = 1f;
            choice.Preview?.Invoke();
        }
        void Select(int index)
        {
            if (!_input || Paused || Time.frameCount == _openedFrame) return;
            var choice = _choices[index];
            if (choice.Enabled) choice.Pick();
            else
            {
                UISound.Play(UISoundId.Buzzer);
                UIRoot.Instance?.Toast.Show(Reason(choice.Reason), UIToastKind.Warning);
            }
        }
        string Reason(string key) => key != null && _db.Text.TryGetValue(key, out var value) ? value : "사용할 수 없습니다";
        static string RuleName(TargetRule rule)
        {
            switch (rule)
            {
                case TargetRule.SingleEnemy: return "적 하나";
                case TargetRule.SingleAlly: return "아군 하나";
                case TargetRule.AllEnemies: return "적 전체";
                case TargetRule.AllAllies: return "아군 전체";
                case TargetRule.RandomEnemies: return "무작위 적";
                case TargetRule.RandomAllies: return "무작위 아군";
                case TargetRule.Self: return "자신";
                case TargetRule.All: return "모든 대상";
                default: return "대상 없음";
            }
        }
        public static string ElementName(int e)
        {
            switch ((Element)e)
            {
                case Element.Slash: return "참격"; case Element.Blunt: return "타격"; case Element.Pierce: return "관통";
                case Element.Fire: return "화염"; case Element.Ice: return "냉기"; case Element.Thunder: return "번개";
                case Element.Dark: return "암흑"; case Element.Holy: return "신성"; default: return "무속성";
            }
        }
        public void CutIn(string title, string text)
        {
            _cutinTitle.text = title; _cutinText.text = text; _cutin.gameObject.SetActive(true);
            SlideIn(_cutin, 520f, 0.2f);
        }
        /// <summary>Slides a centred/top panel in from the left with a fade (call-outs should arrive, not pop).</summary>
        void SlideIn(RectTransform rt, float from, float duration)
        {
            if (!rt.TryGetComponent(out CanvasGroup group)) group = rt.gameObject.AddComponent<CanvasGroup>();
            group.blocksRaycasts = false;
            UITween.Kill(rt);
            Vector2 home = rt.anchoredPosition; home.x = 0f;
            rt.anchoredPosition = home - new Vector2(from, 0f);
            group.alpha = 0f;
            UITween.To(rt, duration, t => { rt.anchoredPosition = home - new Vector2(from * (1f - t), 0f); group.alpha = t; }, UIEase.OutCubic);
        }
        public void HideCutIn() { _cutin.gameObject.SetActive(false); }
        /// <summary>JRPG skill-name plate shown while a skill or item resolves (tinted by its element / light colour).</summary>
        public void SkillBanner(string text, Color color)
        {
            if (_banner == null) return;
            _bannerText.text = text; _bannerText.color = Color.Lerp(Color.white, color, .45f);
            _banner.gameObject.SetActive(true);
            // The banner names the skill; the log line above it would only repeat it.
            if (_logPanel != null) _logPanel.gameObject.SetActive(false);
            SlideIn(_banner, 260f, 0.18f);
        }
        public void HideSkillBanner() { if (_banner != null) _banner.gameObject.SetActive(false); }
        public void Rewards(BattleOutcome outcome, Abyss.Logic.Game.BattleReport report, Action confirmed)
        {
            Lock(); HideSkillBanner();
            if (_logPanel != null) _logPanel.gameObject.SetActive(false);
            _autoButton.gameObject.SetActive(false);
            if (_speedButton != null) _speedButton.gameObject.SetActive(false);
            _reward = UIFactory.Rect(_root, "Battle result").Stretch();
            UIFactory.Fill(_reward, UITheme.Ink.WithAlpha(0.8f), raycast: true);
            var panel = UIFactory.Panel(_reward, name: "Result dashboard");
            bool victory = outcome.Result == BattleResult.Victory;
            var panelSize = new Vector2(1240, 800);
            panel.Rect.Place(UIAnchor.Center, Vector2.zero, panelSize);
            bool reduced = UIRoot.Instance != null && UIRoot.Instance.ReducedMotion;
            panel.Rect.localScale = Vector3.one * (reduced ? 1f : 0.98f);
            UITween.Scale(panel.Rect, 1f, reduced ? 0f : 0.2f, UIEase.OutCubic);
            string heading = victory ? "전투 승리" : outcome.Result == BattleResult.Defeat ? "다시 준비할 시간" : "전투에서 벗어났습니다";
            UIFactory.Label(panel.Rect, heading, 44, UIFont.Bold, victory ? UITheme.DawnBright : UITheme.Text,
                fx: UITextFx.Plain).Rt().TopStrip(62, 22, 36, 36);
            UIFactory.Label(panel.Rect, victory ? $"획득 골드  {report.Gold:N0} G   ·   생존 동료 EXP +{report.Experience:N0}" : "전투 결과와 탐험 기록을 확인하세요.",
                25, color: UITheme.TextDim).Rt().TopStrip(38, 86, 36, 36);
            if (victory) BuildPartyResults(panel.Rect, panelSize.x, report, outcome);
            var growth = UIFactory.Panel(panel.Rect, UIPanelStyle.Dark, false, "Progression card");
            growth.Rect.Place(UIAnchor.TopLeft, new Vector2(32, -260), new Vector2(444, 426));
            UIFactory.Label(growth.Rect, "성장과 탐험 기록", 27, color: UITheme.Text).Rt().TopStrip(46, 12, 22, 22);
            _rewardScroll = UIFactory.ScrollView(growth.Rect, out var rewardContent, name: "Result progression");
            _rewardScroll.Rt().Stretch(22, 70, 22, 20);
            _text.Clear();
            if (!victory) _text.Append(outcome.Result == BattleResult.Defeat ? "파티가 쓰러졌습니다. 마을에서 재정비하세요.\n" : "전투에서 벗어났습니다.\n");
            AppendProgression(report);
            if (_text.Length == 0) _text.Append("탐험 기록이 저장되었습니다.\n다음 모험을 이어가세요.");
            _rewardText = UIFactory.Paragraph(rewardContent, _text.ToString(), 24);
            _rewardText.overflowMode = TextOverflowModes.Overflow;

            var loot = UIFactory.Panel(panel.Rect, UIPanelStyle.Dark, false, "Loot collection");
            loot.Rect.Place(UIAnchor.TopRight, new Vector2(-32, -260), new Vector2(714, 426));
            UIFactory.Label(loot.Rect, "획득한 전리품", 27, color: UITheme.Text).Rt().TopStrip(46, 12, 22, 22);
            var drops = new List<KeyValuePair<string, int>>(report.Drops);
            drops.Sort((a, b) => { int rarity = DropRarity(b.Key).CompareTo(DropRarity(a.Key)); return rarity != 0 ? rarity : string.CompareOrdinal(a.Key, b.Key); });
            var cards = UIFactory.Rect(loot.Rect, "Loot page").Stretch(18, 70, 18, 48);
            _rewardCounter = UIFactory.Label(loot.Rect, "", 21, color: UITheme.TextDim, align: TextAlignmentOptions.Center);
            _rewardCounter.Rt().BottomStrip(32, 8, 130, 130);
            int page = 0;
            Action refresh = () =>
            {
                for (int i = cards.childCount - 1; i >= 0; i--) { var old = cards.GetChild(i).gameObject; old.SetActive(false); Destroy(old); }
                int start = page * 6;
                if (drops.Count == 0) UIFactory.Paragraph(cards, victory ? "획득한 물품이 없습니다." : "골드·EXP·아이템 보상은 없습니다.", 25).Rt().Stretch(18, 20, 18, 20);
                for (int i = start; i < Math.Min(drops.Count, start + 6); i++)
                {
                    string id = drops[i].Key;
                    int rarity = DropRarity(id), index = i - start;
                    var accent = UITheme.RarityColor(rarity);
                    var card = UIFactory.Panel(cards, UIPanelStyle.Glass, false, "Drop " + id);
                    card.Rect.Place(UIAnchor.TopLeft, new Vector2((index % 2) * 342, -(index / 2) * 100), new Vector2(330, 90));
                    var stripe = UIFactory.Image(card.Rect, UISprites.PanelWhite, accent, "Rarity stripe");
                    stripe.Rt().Place(UIAnchor.Left, new Vector2(0, 0), new Vector2(4, 70));
                    var icon = UIFactory.Icon(card.Rect, _db.Items.ContainsKey(id) ? UIArtwork.Item(id) : UIArtwork.Gear(id), 54);
                    icon.Rt().Place(UIAnchor.Left, new Vector2(14, 0), new Vector2(54, 54));
                    string name = _db.Items.TryGetValue(id, out var item) ? item.DisplayName : _db.Equipment[id].DisplayName;
                    var label = UIFactory.Label(card.Rect, name, 23, color: UITheme.Text);
                    label.Rt().TopStrip(36, 12, 82, 16); label.overflowMode = TextOverflowModes.Ellipsis;
                    string category = item != null ? item.ItemType == ItemType.Material ? "재료" : "소모품" : "장비";
                    UIFactory.Label(card.Rect, $"{UITheme.RarityName(rarity)} · {category}   ×{drops[i].Value}", 20, color: accent).Rt().BottomStrip(30, 12, 82, 16);
                    // Every card can reveal its complete name and description, even if the grid title is truncated.
                    var hit = card.gameObject.AddComponent<UnityEngine.UI.Button>();
                    hit.transition = UnityEngine.UI.Selectable.Transition.None;
                    hit.navigation = new Navigation { mode = Navigation.Mode.None };
                    string description = item != null ? item.Description : _db.Equipment[id].Description;
                    hit.onClick.AddListener(() => { if (!Paused) UIModal.Alert(UIRoot.Instance.Modals, name, $"{UITheme.RarityName(rarity)} · {category}\n\n{description}"); });
                }
                _rewardCounter.text = drops.Count == 0 ? "보상 없음" : $"{page + 1} / {Math.Max(1, (drops.Count + 5) / 6)}   ·   {drops.Count}종 획득";
            };
            _rewardPage = delta => { if (!Paused) { page = Mathf.Clamp(page + delta, 0, Math.Max(0, (drops.Count - 1) / 6)); refresh(); } };
            var previous = UIFactory.Button(loot.Rect, "◀", () => _rewardPage(-1));
            previous.Rt().Place(UIAnchor.BottomLeft, new Vector2(18, 6), new Vector2(94, TouchUI ? 72 : 38));
            var next = UIFactory.Button(loot.Rect, "▶", () => _rewardPage(1));
            next.Rt().Place(UIAnchor.BottomRight, new Vector2(-18, 6), new Vector2(94, TouchUI ? 72 : 38));
            previous.gameObject.SetActive(drops.Count > 6); next.gameObject.SetActive(drops.Count > 6);
            refresh();
            UIFactory.Label(panel.Rect, TouchUI ? "전리품을 탭하면 상세 보기 · 기록은 끌어서 스크롤" : "↑↓ 기록 스크롤 · Q/E 또는 LB/RB 전리품 페이지",
                21, color: UITheme.TextDim).Rt().BottomStrip(34, TouchUI ? 48 : 82, 36, TouchUI ? 380 : 36);
            bool answered = false;
            float acceptAfter = Time.unscaledTime + 0.4f;
            var ok = UIFactory.Button(panel.Rect, "모험 계속", () =>
            { if (Paused || answered || Time.unscaledTime < acceptAfter) return; answered = true; UIInput.Consume(); confirmed(); });
            ok.Rt().Place(UIAnchor.BottomRight, new Vector2(-36, 18), new Vector2(312, TouchUI ? UIRoot.TouchTargetHeight : 58));
            _buttons.Clear(); _buttons.Add(ok); _focus = 0; ok.Focused = true;
            _openedFrame = Time.frameCount; UIInput.Consume();
        }

        int DropRarity(string id) => _db.Items.TryGetValue(id, out var item) ? item.Rarity : _db.Equipment.TryGetValue(id, out var gear) ? gear.Rarity : 0;

        void BuildPartyResults(Transform panel, float width, Abyss.Logic.Game.BattleReport report, BattleOutcome outcome)
        {
            var heroes = new List<Card>();
            foreach (var card in _cards.Values) if (card.Unit.Side == BattleSide.Party) heroes.Add(card);
            heroes.Sort((a, b) => a.Unit.Slot.CompareTo(b.Unit.Slot));
            float column = (width - 64) / Math.Max(1, heroes.Count);
            for (int i = 0; i < heroes.Count; i++)
            {
                var card = heroes[i];
                var slot = UIFactory.Panel(panel, UIPanelStyle.Glass, false, "Growth " + card.Unit.Name).Rect;
                slot.Place(UIAnchor.TopLeft, new Vector2(32 + i * column, -142), new Vector2(column - 12, 98));
                var face = UIFactory.Portrait(slot, 64);
                face.Rt().Place(UIAnchor.Left, new Vector2(12, 0), new Vector2(64, 64));
                face.SetSprite(UIArtwork.Hero(card.Unit.DefId));
                UIFactory.Label(slot, card.Unit.Name, 24).Rt().TopStrip(32, 12, 88, 12);
                int finalHp = outcome.FinalHp.TryGetValue(card.Unit.DefId, out int hp) ? hp : card.Unit.Hp;
                string summary = finalHp > 0 ? $"EXP +{report.Experience:N0}" : "전투불능 · EXP 없음";
                foreach (var level in report.LevelUps) if (level.HeroId == card.Unit.DefId) summary = $"Lv.{level.OldLevel} → {level.NewLevel}  성장!";
                var label = UIFactory.Label(slot, summary, 20, color: finalHp > 0 ? UITheme.Positive : UITheme.TextDisabled);
                label.Rt().BottomStrip(36, 12, 88, 12); label.overflowMode = TextOverflowModes.Ellipsis;
            }
        }

        void AppendProgression(Abyss.Logic.Game.BattleReport report)
        {
            if (report.LevelUps.Count > 0) _text.Append("\n<b>동료의 성장</b>\n");
            foreach (var level in report.LevelUps)
            {
                _text.Append(_db.Heroes[level.HeroId].DisplayName).Append(" · Lv.").Append(level.OldLevel)
                    .Append(" → Lv.").Append(level.NewLevel).Append('\n');
                var gain = level.StatDeltas;
                AppendStatGain("최대 HP", gain.MaxHp);
                AppendStatGain("최대 MP", gain.MaxMp);
                AppendStatGain("공격", gain.Attack);
                AppendStatGain("마력", gain.Magic);
                AppendStatGain("방어", gain.Defense);
                AppendStatGain("저항", gain.Resistance);
                AppendStatGain("속도", gain.Speed);
                _text.Append('\n');
                foreach (string id in level.NewSkills)
                    _text.Append("새 기술 · ").Append(_db.Skills[id].DisplayName).Append('\n');
                _text.Append('\n');
            }
            if (report.QuestUpdates.Count > 0) _text.Append("\n<b>의뢰 진행</b>\n");
            foreach (var update in report.QuestUpdates)
            {
                var quest = _db.Quests[update.QuestId];
                _text.Append(quest.Title).Append(" · ").Append(update.OldProgress).Append(" → ")
                    .Append(update.NewProgress).Append('/').Append(Math.Max(1, quest.Count));
                _text.Append(update.Completed ? " · 완료!\n마을 길드에서 보상을 수령하세요.\n" : " · 진행 중\n");
            }
            if (report.NewBestiaryEntries.Count > 0) _text.Append("\n<b>마물 도감에 새로 기록</b>\n");
            foreach (string id in report.NewBestiaryEntries)
                _text.Append(_db.Enemies[id].DisplayName).Append('\n');
            if (report.NewWeaknesses.Count > 0) _text.Append("\n<b>새로 밝혀진 약점</b>\n");
            foreach (string key in report.NewWeaknesses)
            {
                int colon = key.LastIndexOf(':');
                if (colon <= 0 || !int.TryParse(key.Substring(colon + 1), out int element))
                    throw new InvalidOperationException("Battle report contains an invalid weakness record.");
                _text.Append(_db.Enemies[key.Substring(0, colon)].DisplayName).Append(" · ")
                    .Append(ElementName(element)).Append(" 약점\n");
            }
        }

        void AppendStatGain(string name, int value)
        {
            if (value == 0) return;
            _text.Append(name).Append(' ');
            if (value > 0) _text.Append('+');
            _text.Append(value).Append("  ");
        }
        void Update()
        {
            if (Paused || !UIInput.CanReceive(_root) || Time.frameCount == _openedFrame) return;
            if (_reward != null)
            {
                if (UIInput.Navigate.y != 0)
                {
                    _rewardScroll.StopMovement();
                    _rewardScroll.verticalNormalizedPosition = Mathf.Clamp01(_rewardScroll.verticalNormalizedPosition + UIInput.Navigate.y * 0.16f);
                    UIInput.Consume();
                }
                if (UIInput.Confirm) { UIInput.Consume(); _buttons[0].Click(); }
                else if (UIInput.TabPrev || UIInput.TabNext || UIInput.Navigate.x != 0)
                {
                    _rewardPage(UIInput.TabPrev ? -1 : UIInput.TabNext ? 1 : UIInput.Navigate.x);
                    UIInput.Consume();
                }
                return;
            }
            // Automatic actions lock command choices, but Cancel must still stop the next auto input.
            if (_auto && UIInput.Cancel)
            {
                ToggleAuto(); UIInput.Consume(); return;
            }
            if (!_input) return;
            _menuHint.text = UIInput.Device == UIInputDevice.Gamepad ? "↑↓ 선택 · LB/RB 페이지 · ←→ 상세"
                : UIInput.Device == UIInputDevice.Touch ? "탭하여 선택 · 적/아군 카드를 탭해도 대상 지정" : "↑↓ 선택 · Q/E 페이지 · ←→ 상세";
            int movement = UIInput.NavigateRows;
            if (movement != 0) { Focus(_focus + movement); UIInput.Consume(); }
            else if (UIInput.Navigate.x != 0)
            {
                _detailScroll.StopMovement();
                _detailScroll.verticalNormalizedPosition = Mathf.Clamp01(_detailScroll.verticalNormalizedPosition - UIInput.Navigate.x * 0.2f);
                UIInput.Consume();
            }
            else if (UIInput.TabNext || UIInput.TabPrev)
            { Page(UIInput.TabPrev ? -1 : 1); UIInput.Consume(); }
            else if (UIInput.Cancel && _back != null) { _back(); UIInput.Consume(); }
            else if (UIInput.Confirm && _choices.Count > 0) { Select(_page * PerPage + _focus); UIInput.Consume(); }
        }
        void LateUpdate()
        {
            foreach (var card in _cards.Values)
            {
                if (card.Unit.Side != BattleSide.Enemy || card.Unit.Model == null) continue;
                Vector3 screen = _camera.WorldToScreenPoint(card.Unit.Model.HeadPoint + Vector3.up * .25f);
                card.Panel.gameObject.SetActive(screen.z > 0 && card.Unit.Alive);
                if (screen.z <= 0) continue;
                RectTransformUtility.ScreenPointToLocalPointInRectangle(_world, screen, null, out var point);
                card.Panel.Rect.anchorMin = card.Panel.Rect.anchorMax = new Vector2(.5f, .5f);
                card.Panel.Rect.pivot = new Vector2(.5f, 0);
                card.Panel.Rect.anchoredPosition = point;
            }
        }
        void OnDestroy() { if (_root != null) Destroy(_root.gameObject); }
    }
}
