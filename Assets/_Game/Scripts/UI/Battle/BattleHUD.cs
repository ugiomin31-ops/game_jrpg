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
            public Action Pick, Preview;
            public Sprite Icon;
        }
        readonly Dictionary<string, Card> _cards = new Dictionary<string, Card>();
        readonly List<Choice> _choices = new List<Choice>();
        readonly List<UIButton> _buttons = new List<UIButton>();
        readonly StringBuilder _text = new StringBuilder();
        readonly Dictionary<string, Sprite> _statusArt = new Dictionary<string, Sprite>(StringComparer.Ordinal);
        readonly StringBuilder _targetText = new StringBuilder();
        RectTransform _root, _party, _world, _menu, _rows, _detail, _cutin, _reward;
        TMP_Text _order, _log, _title, _description, _cutinTitle, _cutinText, _rewardText;
        UIButton _autoButton;
        ScrollRect _detailScroll;
        ScrollRect _rewardScroll;
        TMP_Text _menuHint, _rewardCounter;
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
        public bool CommandRootOpen => _input && _back == null && _reward == null;

        public void Initialize(Transform parent, Camera camera, GameDB db, Action<BattleCommand> submit,
            Action toggleAuto, Action<string> preview)
        {
            _camera = camera; _db = db; _submit = submit; _toggleAuto = toggleAuto; _preview = preview;
            _statusArt.Clear();
            foreach (var status in db.Statuses) _statusArt.Add(status.Key, UIArtwork.Status(status.Key));
            _root = UIFactory.Rect(parent, "Battle HUD").Stretch();
            _world = UIFactory.Rect(_root, "Enemy gauges").Stretch();
            _party = UIFactory.Rect(_root, "Party").BottomStrip(210, 16, 28, 28);
            var top = UIFactory.Panel(_root, UIPanelStyle.Glass, false);
            top.Rect.TopStrip(84, 18, 32, 330);
            _order = UIFactory.Label(top.transform, "", 23); _order.Rt().Stretch(22, 14, 22, 14);
            _order.overflowMode = TextOverflowModes.Ellipsis;
            _autoButton = UIFactory.Button(_root, "자동: OFF", ToggleAuto);
            _autoButton.Rt().Place(UIAnchor.TopRight, new Vector2(-32, -26), new Vector2(260, 62));
            var logPanel = UIFactory.Panel(_root, UIPanelStyle.Dark, false);
            logPanel.Rect.TopStrip(52, 112, 220, 220);
            _log = UIFactory.Label(logPanel.transform, "", 22, align: TextAlignmentOptions.Center);
            _log.Rt().Stretch(10, 6, 10, 6);
            _log.overflowMode = TextOverflowModes.Ellipsis;
            var menu = UIFactory.Panel(_root, UIPanelStyle.Ornate);
            _menu = menu.Rect.Place(UIAnchor.BottomRight, new Vector2(-32, 245), new Vector2(570, 510));
            _title = UIFactory.Label(menu.transform, "", 29); _title.Rt().TopStrip(54, 16, 24, 24);
            _menuHint = UIFactory.Label(menu.transform, "↑↓ 선택 · Q/E 페이지 · ←→ 상세", 18, color: UITheme.TextDim);
            _menuHint.Rt().TopStrip(25, 62, 24, 24);
            _rows = UIFactory.Rect(menu.transform, "Choices").Stretch(22, 100, 22, 72);
            var detail = UIFactory.Panel(_root, UIPanelStyle.Glass);
            _detail = detail.Rect.Place(UIAnchor.TopLeft, new Vector2(32, -178), new Vector2(1100, 100));
            _detailScroll = UIFactory.ScrollView(detail.transform, out var detailContent, name: "Command description");
            _detailScroll.Rt().Stretch(24, 12, 24, 12);
            _description = UIFactory.Paragraph(detailContent, "", 23);
            _description.overflowMode = TextOverflowModes.Overflow;
            var cutin = UIFactory.Panel(_root, UIPanelStyle.Ornate);
            _cutin = cutin.Rect.Place(UIAnchor.Center, Vector2.zero, new Vector2(1100, 255));
            _cutinTitle = UIFactory.Label(cutin.transform, "", 42, align: TextAlignmentOptions.Center);
            _cutinTitle.Rt().TopStrip(74, 26, 30, 30);
            _cutinText = UIFactory.Paragraph(cutin.transform, "", 29); _cutinText.Rt().Stretch(48, 108, 48, 22);
            _cutin.gameObject.SetActive(false);
            Lock();
        }

        public void AddUnit(BattleDisplayUnit unit)
        {
            var panel = UIFactory.Panel(unit.Side == BattleSide.Party ? _party : _world, UIPanelStyle.Glass, false);
            var card = new Card { Panel = panel, Unit = unit };
            if (unit.Side == BattleSide.Party)
                panel.Rect.Place(UIAnchor.BottomLeft, new Vector2(unit.Slot * 455, 0), new Vector2(435, 206));
            else panel.Rect.sizeDelta = new Vector2(unit.Boss ? 320 : 210, 134);
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

        public void Log(string text) { _log.text = text; }
        public void SetAuto(bool value) { _auto = value; _autoButton.SetLabel(value ? (Application.isMobilePlatform ? "자동: ON · 탭하여 해제" : "자동: ON · Esc 취소") : "자동: OFF"); }
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
            var options = engine.GetCommandOptions(_actor);
            BeginChoices(_actor.DisplayName + " · 행동", null);
            Add("공격", "장비 무기로 적 하나를 공격합니다.", options.CanAttack, null, () => Targets(BattleCommand.Attack(null)), icon: UIArtwork.Command("attack"));
            Add("스킬", "MP를 사용하여 스킬을 시전합니다.", true, null, () => Skills(false), icon: UIArtwork.Command("skill"));
            Add("궁극기", "TP 100으로 강력한 궁극기를 사용합니다.", true, null, () => Skills(true), icon: UIArtwork.Command("ultimate"));
            Add("아이템", "보유한 소비 아이템을 사용합니다.", true, null, Items, icon: UIArtwork.Command("item"));
            Add("방어", "다음 턴까지 받는 피해를 줄입니다.", options.CanGuard, null, () => Targets(BattleCommand.Guard()), icon: UIArtwork.Command("guard"));
            Add("도주", "전투에서 도주를 시도합니다.", options.CanFlee, options.FleeReasonKey, () => Targets(BattleCommand.Flee()), icon: UIArtwork.Command("flee"));
            Add("자동 " + (_auto ? "OFF" : "ON"), "자동 전투를 켜거나 끕니다. 언제든 우측 상단 버튼으로 취소할 수 있습니다.", true, null, ToggleAuto, icon: UIArtwork.Command("auto"));
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
            int first = _page * 6;
            for (int i = first; i < Math.Min(first + 6, _choices.Count); i++)
            {
                int index = i; var choice = _choices[i];
                var button = UIFactory.Button(_rows, choice.Label, () => Select(index), choice.Icon);
                button.Interactable = choice.Enabled;
                button.DisabledReason = choice.Enabled ? null : Reason(choice.Reason);
                button.Rt().Place(UIAnchor.TopLeft, new Vector2(0, -(i - first) * 56), new Vector2(526, 48));
                button.Hovered += () => Focus(index - first);
                _buttons.Add(button);
            }
            var navigation = UIFactory.Button(_menu, "← 뒤로", () => _back?.Invoke());
            navigation.Rt().Place(UIAnchor.BottomLeft, new Vector2(22, 14), new Vector2(160, 46));
            navigation.Interactable = _back != null; _buttons.Add(navigation);
            var prev = UIFactory.Button(_menu, "◀", () => Page(-1));
            prev.Rt().Place(UIAnchor.BottomLeft, new Vector2(200, 14), new Vector2(70, 46));
            prev.Interactable = _page > 0; _buttons.Add(prev);
            var next = UIFactory.Button(_menu, (_page + 1) + "/" + Math.Max(1, (_choices.Count + 5) / 6) + " ▶", () => Page(1));
            next.Rt().Place(UIAnchor.BottomRight, new Vector2(-22, 14), new Vector2(180, 46));
            next.Interactable = first + 6 < _choices.Count; _buttons.Add(next);
            Focus(0);
            if (_choices.Count == 0) _description.text = "사용 가능한 항목이 없습니다. 뒤로 돌아가세요.";
        }
        void Page(int delta)
        {
            int next = Mathf.Clamp(_page + delta, 0, Math.Max(0, (_choices.Count - 1) / 6));
            if (next == _page) return; _page = next; Render();
        }
        void Focus(int index)
        {
            int count = Math.Min(6, _choices.Count - _page * 6);
            if (count <= 0) return;
            _focus = (index % count + count) % count;
            for (int i = 0; i < _buttons.Count; i++) _buttons[i].Focused = i == _focus;
            var choice = _choices[_page * 6 + _focus];
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
        public void CutIn(string title, string text) { _cutinTitle.text = title; _cutinText.text = text; _cutin.gameObject.SetActive(true); }
        public void HideCutIn() { _cutin.gameObject.SetActive(false); }
        public void Rewards(BattleOutcome outcome, Abyss.Logic.Game.BattleReport report, Action confirmed)
        {
            Lock();
            _autoButton.gameObject.SetActive(false);
            _reward = UIFactory.Rect(_root, "Battle result").Stretch();
            UIFactory.Fill(_reward, new Color(0, 0, 0, .72f), raycast: true);
            var panel = UIFactory.Panel(_reward, UIPanelStyle.Ornate);
            panel.Rect.Place(UIAnchor.Center, Vector2.zero, new Vector2(860, 640));
            string heading = outcome.Result == BattleResult.Victory ? "승리" : outcome.Result == BattleResult.Defeat ? "패배" : "도주 성공";
            UIFactory.Label(panel.transform, heading, 48, color: UITheme.GoldBright, align: TextAlignmentOptions.Center).Rt().TopStrip(72, 28, 24, 24);
            UIFactory.Separator(panel.transform, 600).Rt().Place(UIAnchor.Top, new Vector2(0, -112), new Vector2(600, 24));
            _rewardScroll = UIFactory.ScrollView(panel.transform, out var rewardContent, name: "Battle rewards");
            _rewardScroll.Rt().Stretch(50, 145, 50, 160);
            _rewardText = UIFactory.Paragraph(rewardContent, "", 27);
            _rewardText.overflowMode = TextOverflowModes.Overflow;
            _rewardCounter = UIFactory.Label(panel.transform, "", 21, color: UITheme.TextDim, align: TextAlignmentOptions.Center);
            _rewardCounter.Rt().BottomStrip(30, 127, 50, 50);
            var drops = new List<KeyValuePair<string, int>>(report.Drops);
            int page = 0;
            Action refresh = () =>
            {
                _text.Clear();
                if (outcome.Result == BattleResult.Victory)
                {
                    _text.Append("<b>전투 보상</b>\n생존 동료당  ").Append(report.Experience).Append(" XP\n획득 골드  ").Append(report.Gold).Append(" G\n");
                    foreach (var card in _cards.Values)
                    {
                        if (card.Unit.Side != BattleSide.Party) continue;
                        int finalHp = outcome.FinalHp.TryGetValue(card.Unit.DefId, out int hp) ? hp : card.Unit.Hp;
                        _text.Append(card.Unit.Name).Append(" · ");
                        if (finalHp > 0) _text.Append('+').Append(report.Experience).Append(" XP");
                        else _text.Append("0 XP · 전투불능");
                        _text.Append('\n');
                    }
                }
                else _text.Append(outcome.Result == BattleResult.Defeat ? "파티가 쓰러졌습니다. 마을에서 재정비하세요.\n" : "전투에서 벗어났습니다.\n");
                AppendProgression(report);
                if (outcome.Result == BattleResult.Victory)
                {
                    _text.Append("\n<b>전리품</b>\n");
                    if (drops.Count == 0) _text.Append("없음\n");
                }
                for (int i = page * 10; i < Math.Min(drops.Count, (page + 1) * 10); i++)
                {
                    string name = _db.Items.TryGetValue(drops[i].Key, out var item) ? item.DisplayName :
                        _db.Equipment.TryGetValue(drops[i].Key, out var equipment) ? equipment.DisplayName :
                        throw new InvalidOperationException("Reward content is missing from the game database.");
                    _text.Append(name).Append(" ×").Append(drops[i].Value).Append('\n');
                }
                _rewardText.text = _text.ToString();
                _rewardCounter.text = drops.Count > 10 ? $"전리품 {page + 1} / {(drops.Count + 9) / 10} · ↑↓ 상세 스크롤" : "↑↓ 상세 스크롤 · 확인하면 모험을 계속합니다.";
                LayoutRebuilder.ForceRebuildLayoutImmediate(_rewardScroll.content);
                _rewardScroll.StopMovement();
                _rewardScroll.verticalNormalizedPosition = 1f;
            };
            _rewardPage = delta =>
            {
                if (Paused) return;
                page = Mathf.Clamp(page + delta, 0, Math.Max(0, (drops.Count - 1) / 10)); refresh();
            };
            if (drops.Count > 10)
            {
                UIFactory.Button(panel.transform, "이전 전리품 · Q / LB", () => _rewardPage(-1))
                    .Rt().Place(UIAnchor.BottomLeft, new Vector2(40, 90), new Vector2(300, 50));
                UIFactory.Button(panel.transform, "다음 전리품 · E / RB", () => _rewardPage(1))
                    .Rt().Place(UIAnchor.BottomRight, new Vector2(-40, 90), new Vector2(300, 50));
            }
            refresh();
            var ok = UIFactory.Button(panel.transform, "확인 · 계속", () => { if (Paused) return; UIInput.Consume(); confirmed(); });
            ok.Rt().Place(UIAnchor.Bottom, new Vector2(0, 26), new Vector2(350, 60));
            _buttons.Clear(); _buttons.Add(ok); _focus = 0; ok.Focused = true;
            _openedFrame = Time.frameCount;
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
                : UIInput.Device == UIInputDevice.Touch ? "탭하여 선택" : "↑↓ 선택 · Q/E 페이지 · ←→ 상세";
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
            else if (UIInput.Confirm && _choices.Count > 0) { Select(_page * 6 + _focus); UIInput.Consume(); }
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
