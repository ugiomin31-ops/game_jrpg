using System;
using System.Collections.Generic;
using System.Text;
using Abyss.Logic;
using Abyss.Logic.Battle;
using TMPro;
using UnityEngine;
using UnityEngine.UI;

namespace Abyss.UI.Battle
{
    public sealed partial class BattleHUD
    {
        readonly List<Choice> _choices = new List<Choice>();
        readonly List<UISlantButton> _plates = new List<UISlantButton>();
        readonly List<GameObject> _navObjects = new List<GameObject>();
        readonly StringBuilder _targetText = new StringBuilder();
        UISlantKind _kind = UISlantKind.Command;
        bool _animateNext, _menuClosing;
        float _stackBottom;
        string _armedTargetId;

        // ---- command root ---------------------------------------------------------------------------

        public void ShowCommands(BattleEngine engine)
        {
            _engine = engine; _actor = engine.ActiveHero;
            if (_actor == null) { Lock(); return; }
            HideEnemyTurn();
            var options = engine.GetCommandOptions(_actor);
            BeginChoices(_actor.DisplayName + " · 행동", null, UISlantKind.Command);
            Command("공격", "장비 무기로 적 하나를 공격합니다.", options.CanAttack, null,
                () => Targets(BattleCommand.Attack(null), null, "공격", "장비 무기로 적 하나를 공격합니다."), "attack");
            Command("스킬", "MP를 사용하여 스킬을 시전합니다.", true, null, () => Skills(false), "skill");
            Command("궁극기", "TP 100으로 강력한 궁극기를 사용합니다.", true, null, () => Skills(true), "ultimate");
            Command("아이템", "보유한 소비 아이템을 사용합니다.", true, null, Items, "item");
            Command("방어", "다음 턴까지 받는 피해를 줄입니다.", options.CanGuard, null,
                () => Targets(BattleCommand.Guard(), null, "방어", "다음 턴까지 받는 피해를 줄입니다."), "guard");
            Command("도주", "전투에서 도주를 시도합니다.", options.CanFlee, options.FleeReasonKey,
                () => Targets(BattleCommand.Flee(), null, "도주", "전투에서 도주를 시도합니다."), "flee");
            Render(); SetHeroFocus(_actor.Id);
        }

        void Command(string label, string description, bool enabled, string reason, Action pick, string icon)
        {
            var choice = AddChoice(label, description, enabled, reason, pick, null, UIArtwork.Command(icon));
        }

        void Skills(bool ultimate, Action back = null)
        {
            Action returnToCommands = back ?? RememberChoices(() => ShowCommands(_engine));
            BeginChoices(ultimate ? "궁극기" : "스킬", returnToCommands, UISlantKind.Skill);
            // Damage skills that can hit a KNOWN weakness come first (learn order kept); tags use knowledge only.
            foreach (var option in _engine.SkillMenu(_actor))
            {
                if (option.IsUltimate != ultimate) continue;
                var captured = option;
                string name = option.DisplayName;
                string description = option.Skill.Description + "\n" + ElementName((int)option.Skill.Element) + " · " + RuleName(option.Target) + " · " + option.Skill.HitCount + "회"
                    + (option.KnownAffinity == SkillAffinityTag.Weak ? "\n" + UITheme.Tag(UISlant.Coral) + "약점</color> 알려진 약점을 찌를 수 있는 적이 있습니다."
                        : option.KnownAffinity == SkillAffinityTag.Resist ? "\n" + UITheme.Tag(UITheme.TextDim) + "내성</color> 이 속성에 내성인 적이 확인되었습니다." : "");
                var choice = AddChoice(name, description, option.Usable, option.ReasonKey,
                    () => Targets(BattleCommand.Skill(captured.Id), RememberChoices(() => Skills(ultimate, returnToCommands)), name, description), null, UIArtwork.Element(option.Skill.Element) ?? UIArtwork.Command("skill"));
                choice.Right = (option.KnownAffinity == SkillAffinityTag.Weak ? UITheme.Tag(UISlant.Coral) + "<size=70%>약점</size></color> " : "") + CostText(option.MpCost, option.TpCost);
                choice.ChipText = option.Skill.Element == Element.None ? "무속성" : ElementName((int)option.Skill.Element);
                choice.ChipColor = UISlant.ElementColor(option.Skill.Element);
                choice.Hint = (option.KnownAffinity == SkillAffinityTag.Weak ? UITheme.Tag(UISlant.Coral) + "약점</color> · "
                    : option.KnownAffinity == SkillAffinityTag.Resist ? UITheme.Tag(UITheme.TextDim) + "내성</color> · " : "")
                    + RuleName(option.Target) + " · " + option.Skill.HitCount + "회";
            }
            Render();
        }

        /// <summary>Cost text of a skill row: MP in violet-blue, TP in amber, unit smaller than the number (nothing when free).</summary>
        static string CostText(int mp, int tp)
        {
            string text = "";
            if (mp > 0) text += "<color=#9db2ff><size=70%>MP</size> " + mp + "</color>";
            if (tp > 0) text += (text.Length > 0 ? " " : "") + "<color=#ffc93d><size=70%>TP</size> " + tp + "</color>";
            return text;
        }

        void Items() => Items(null);

        void Items(Action back)
        {
            Action returnToCommands = back ?? RememberChoices(() => ShowCommands(_engine));
            BeginChoices("아이템", returnToCommands, UISlantKind.Skill);
            foreach (var option in _engine.GetCommandOptions(_actor).Items)
            {
                var captured = option;
                string name = option.DisplayName;
                string description = option.Item.Description + "\n" + RuleName(option.Target);
                var choice = AddChoice(name, description, option.Usable, option.ReasonKey,
                    () => Targets(BattleCommand.Item(captured.Id), RememberChoices(() => Items(returnToCommands)), name, description), null, UIArtwork.Item(captured.Id));
                choice.Right = "<size=70%>×</size>" + option.Count;
                choice.Hint = RuleName(option.Target);
            }
            Render();
        }

        Action RememberChoices(Action rebuild)
        {
            // Absolute index, so returning after a layout change still lands on the same choice.
            int selected = _page * _perPage + _focus;
            return () => { rebuild(); ClampSelection(selected); Render(); };
        }

        void ClampSelection(int absolute)
        {
            if (_choices.Count == 0) { _page = 0; _focus = 0; return; }
            absolute = Mathf.Clamp(absolute, 0, _choices.Count - 1);
            _page = absolute / _perPage; _focus = absolute % _perPage;
        }

        // ---- targets --------------------------------------------------------------------------------

        void Targets(BattleCommand command, Action back = null, string actionLabel = null, string actionDescription = null)
        {
            var targets = _engine.ValidTargets(_actor, command);
            var rule = _engine.GetTargetRule(_actor, command);
            _armedTargetId = null;
            BeginChoices((actionLabel == null ? "대상 선택" : actionLabel) + " · " + RuleName(rule), back ?? RememberChoices(() => ShowCommands(_engine)), UISlantKind.Skill);
            string targetContext = actionLabel == null ? null : actionLabel + "\n" + actionDescription;
            int actorIndex = _engine.UnitIndexOf(_actor);
            if (rule == TargetRule.SingleEnemy || rule == TargetRule.SingleAlly)
            {
                foreach (var target in targets)
                {
                    string id = target.Id;
                    var preview = _engine.PreviewAction(actorIndex, command, _engine.UnitIndexOf(target));
                    // The estimate leads the details so it is visible without scrolling.
                    string estimate = PreviewLine(preview, id);
                    var choice = AddChoice(target.DisplayName, (estimate == null ? "" : estimate + "\n") + WithTargetContext(targetContext, TargetDescription(id)), true, null,
                        () => { command.TargetId = id; Commit(command); }, () => _preview?.Invoke(id), target.Side == BattleSide.Party ? UIArtwork.Hero(target.DefId) : UIArtwork.Enemy(target.DefId));
                    choice.TargetId = id;
                    choice.Right = PreviewHint(preview, id) ?? "";
                    choice.Marks.Add(new TargetMark { Id = id, Pill = PillText(preview, id), Ally = target.Side == BattleSide.Party });
                }
            }
            else
            {
                _targetText.Clear();
                var preview = _engine.PreviewAction(actorIndex, command, -1);
                var marks = new List<TargetMark>();
                foreach (var target in targets)
                {
                    string estimate = PreviewLine(preview, target.Id);
                    if (estimate != null) _targetText.Append(target.DisplayName).Append(" · ").Append(estimate).Append('\n');
                    marks.Add(new TargetMark { Id = target.Id, Pill = PillText(preview, target.Id), Ally = target.Side == BattleSide.Party });
                }
                if (_targetText.Length > 0) _targetText.Append('\n');
                foreach (var target in targets) _targetText.Append(WithTargetContext(targetContext, TargetDescription(target.Id))).Append('\n');
                var choice = AddChoice("확인", _targetText.ToString(), targets.Count > 0 || rule == TargetRule.None,
                    "reason_no_target", () => Commit(command), () => _preview?.Invoke(targets.Count == 1 ? targets[0].Id : null), UIArtwork.Command("attack"));
                choice.Hint = RuleName(rule);
                choice.Marks.AddRange(marks);
            }
            Render();
        }

        string HpPercent(string id)
        {
            if (!_cards.TryGetValue(id, out var card) || card.Unit.MaxHp <= 0) return "";
            return "<size=70%>HP</size> " + Mathf.CeilToInt(card.Unit.Hp * 100f / card.Unit.MaxHp) + "<size=70%>%</size>";
        }

        /// <summary>Card tap: first tap on an unfocused target focuses it (preview + details), the next tap confirms.</summary>
        void TapUnit(string id)
        {
            if (!_input || Paused || _reward != null) return;
            int index = _choices.FindIndex(c => c.TargetId == id);
            if (index < 0) return;
            int page = index / PerPage;
            if (page != _page) { _page = page; _focus = index - page * PerPage; Render(); }
            PointerSelect(index);
        }

        /// <summary>
        /// One knowledge-safe estimate line: "예상 120–140 · 약점 · 실드 −2 · 처치", "예상 80–95 · ?",
        /// "1타 30–36 ×4 무작위", "회복 210–240", plus "방어막" while a barrier/mana shield absorbs. Null when the
        /// command shows no numbers.
        /// </summary>
        static string PreviewLine(ActionPreview preview, string targetId)
        {
            var t = preview?.For(targetId);
            if (t == null || preview.Kind == PreviewKind.None) return null;
            var sb = new StringBuilder();
            if (preview.Kind == PreviewKind.Heal)
            {
                sb.Append(UITheme.Tag(UITheme.Positive)).Append("회복 ").Append(t.Min).Append('–').Append(t.Max).Append("</color>");
                if (preview.Random) sb.Append(" ×").Append(preview.HitCount).Append(" 무작위");
                return sb.ToString();
            }
            sb.Append(UITheme.Tag(UITheme.GoldBright));
            if (preview.Random) sb.Append("1타 ").Append(t.Min).Append('–').Append(t.Max).Append(" ×").Append(preview.HitCount).Append(" 무작위");
            else sb.Append("예상 ").Append(t.Min).Append('–').Append(t.Max);
            sb.Append("</color>");
            bool unknown = t.Affinity == PreviewAffinity.Unknown;
            if (t.Affinity == PreviewAffinity.Weak) sb.Append(" · ").Append(UITheme.Tag(UISlant.Coral)).Append("약점</color>");
            else if (t.Affinity == PreviewAffinity.Resist) sb.Append(" · ").Append(UITheme.Tag(UITheme.TextDim)).Append("내성</color>");
            else if (unknown) sb.Append(" · ").Append(UITheme.Tag(UITheme.TextDim)).Append("?</color>");
            if (t.ShieldDamage > 0) sb.Append(" · 실드 −").Append(t.ShieldDamage).Append(t.Breaks ? " BREAK" : "");
            if (t.Lethal) sb.Append(" · ").Append(UITheme.Tag(UITheme.Positive)).Append(unknown ? "처치?" : "처치").Append("</color>");
            if (t.Shielded) sb.Append(" · ").Append(UITheme.Tag(UITheme.TextDim)).Append("방어막</color>");
            return sb.ToString();
        }

        /// <summary>Short estimate for a target row: "120–140", with weakness / lethal flags.</summary>
        static string PreviewHint(ActionPreview preview, string targetId)
        {
            var t = preview?.For(targetId);
            if (t == null || preview.Kind == PreviewKind.None) return null;
            var sb = new StringBuilder();
            if (preview.Kind == PreviewKind.Heal)
                return sb.Append(UITheme.Tag(UITheme.Positive)).Append("회복 ").Append(t.Min).Append('–').Append(t.Max).Append("</color>").ToString();
            sb.Append(UITheme.Tag(UITheme.GoldBright)).Append(t.Min).Append('–').Append(t.Max);
            if (preview.Random) sb.Append(" ×").Append(preview.HitCount);
            sb.Append("</color>");
            if (t.Affinity == PreviewAffinity.Weak) sb.Append(' ').Append(UITheme.Tag(UISlant.Coral)).Append("약점</color>");
            if (t.Lethal) sb.Append(' ').Append(UITheme.Tag(UITheme.Positive)).Append("처치</color>");
            return sb.ToString();
        }

        /// <summary>Predicted-damage pill text shown at the target ("예상 피해 143"); null when the command shows no numbers.</summary>
        static string PillText(ActionPreview preview, string targetId)
        {
            var t = preview?.For(targetId);
            if (t == null || preview.Kind == PreviewKind.None) return null;
            var sb = new StringBuilder();
            string range = t.Min == t.Max ? t.Min.ToString() : t.Min + "–" + t.Max;
            if (preview.Kind == PreviewKind.Heal)
                return sb.Append("<size=70%>회복</size> ").Append(UITheme.Tag(UITheme.Positive)).Append(range).Append("</color>").ToString();
            sb.Append("<size=70%>").Append(preview.Random ? "1타" : "예상 피해").Append("</size> ").Append(UITheme.Tag(UISlant.Coral)).Append(range).Append("</color>");
            if (preview.Random) sb.Append("<size=70%> ×").Append(preview.HitCount).Append("</size>");
            if (t.Affinity == PreviewAffinity.Weak) sb.Append(" <size=60%>").Append(UITheme.Tag(UITheme.Warning)).Append("약점</color></size>");
            if (t.Lethal) sb.Append(" <size=60%>").Append(UITheme.Tag(UITheme.Positive)).Append("처치</color></size>");
            return sb.ToString();
        }

        static string WithTargetContext(string context, string target)
            => string.IsNullOrEmpty(context) ? target : target + "\n\n" + context;

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

        /// <summary>
        /// Hands the command to the view. Only an accepted submission consumes and hides the menu; a declined one
        /// (paused or already replaying) keeps the same submenu, selection and armed target, re-rendered.
        /// </summary>
        void Commit(BattleCommand command)
        {
            if (!_input) return;
            int version = _choiceVersion;
            UIInput.Consume();
            bool accepted = _submit != null && _submit(command);
            if (accepted)
            {
                // A replay that synchronously reopened choices owns the menu now.
                if (version == _choiceVersion) Lock();
                return;
            }
            if (version != _choiceVersion || !_input || _reward != null) return;
            UISound.Play(UISoundId.Buzzer);
            Render();
        }

        void Back()
        {
            if (!_input || _back == null) return;
            _armedTargetId = null;
            _preview?.Invoke(null);
            _back();
        }

        // ---- choice list ----------------------------------------------------------------------------

        void BeginChoices(string title, Action back, UISlantKind kind = UISlantKind.Skill)
        {
            _choices.Clear(); _page = 0; _focus = 0; _back = back; _title.text = title; _kind = kind;
            _armedTargetId = null; _choiceVersion++;
            ClearMarks();
            _menuClosing = false;
            UITween.Kill(_menu);
            _menu.gameObject.SetActive(true);
            _input = true; _openedFrame = Time.frameCount; _animateNext = true;
        }

        Choice AddChoice(string label, string description, bool enabled, string reason, Action pick, Action preview = null, Sprite icon = null)
        {
            var choice = new Choice { Label = label, Description = description, Enabled = enabled, Reason = reason, Pick = pick, Preview = preview, Icon = icon };
            _choices.Add(choice);
            return choice;
        }

        void PlaceRight(RectTransform rt, float xOffset, float y, float width, float height)
        {
            rt.anchorMin = rt.anchorMax = new Vector2(1f, 0f);
            rt.pivot = new Vector2(1f, 0f);
            rt.anchoredPosition = new Vector2(-xOffset, y);
            rt.sizeDelta = new Vector2(width, height);
        }

        /// <summary>Sizes the fan for <paramref name="rows"/> visible plates: corner hints at the bottom, one description line, the stack, then the header.</summary>
        void LayoutFan(int rows)
        {
            float navBlock = _showNav ? _navH : 0f;
            float stack = rows * _rowStep;
            float height = navBlock + _footH + stack + _headH + 4f;
            float width = _fanW + (rows + 1) * StepX + 24f;
            _menu.Place(UIAnchor.BottomRight, new Vector2(-_rightMargin, _fanBottom), new Vector2(width, height));
            _rows.Stretch();
            PlaceRight(_detail, Mathf.Max(0, rows - 1) * StepX + 8f, navBlock + 4f, _fanW, _footH - 6f);
            _stackBottom = navBlock + _footH;
            PlaceRight(_headRect, 0f, _stackBottom + stack + 2f, _fanW * 0.8f, _headH);
        }

        float PlateHeight => _rowStep - 12f;

        void Render()
        {
            ResolvePaging();
            int pages = Math.Max(1, (_choices.Count + PerPage - 1) / PerPage);
            _page = Mathf.Clamp(_page, 0, pages - 1);
            foreach (var plate in _plates) { plate.gameObject.SetActive(false); Destroy(plate.gameObject); }
            _plates.Clear();
            foreach (var o in _navObjects) { o.SetActive(false); Destroy(o); }
            _navObjects.Clear();
            int first = _page * PerPage, count = Math.Max(0, Math.Min(PerPage, _choices.Count - first));
            LayoutFan(count);
            bool big = Compact || TouchUI;
            for (int r = 0; r < count; r++)
            {
                int index = first + r; var choice = _choices[index];
                // The painted plate is slimmer than its step; the gap is still part of the touch target.
                var plate = UISlantButton.Create(_rows, "Plate " + choice.Label, new Vector2(_fanW, PlateHeight), _kind, big, choice.Icon, 12f);
                plate.Interactable = choice.Enabled;
                plate.DisabledReason = choice.Enabled ? null : Reason(choice.Reason);
                PlaceRight(plate.Rt(), r * StepX, _stackBottom + (count - 1 - r) * _rowStep, _fanW, _rowStep);
                plate.Label.text = choice.Label;
                if (plate.Right != null) plate.Right.text = choice.Right ?? "";
                plate.SetChip(choice.ChipText, choice.ChipColor);
                plate.Hovered += () => Focus(index - first);
                plate.Clicked += () => PointerSelect(index);
                plate.RememberSibling();
                _plates.Add(plate);
            }
            if (_showNav) BuildNav(first, pages);
            _focus = Mathf.Clamp(_focus, 0, Math.Max(0, count - 1));
            Focus(_focus);
            if (_choices.Count == 0) _description.text = "사용 가능한 항목이 없습니다. 뒤로 돌아가세요.";
            bool animate = _animateNext; _animateNext = false;
            AnimateIn(animate);
            UpdateOcclusion();
        }

        /// <summary>Corner hints along the stack's diagonal: "← 뒤로", "◀ 1/2 ▶". Plate-less; a plate shows only while focused.</summary>
        void BuildNav(int first, int pages)
        {
            bool big = Compact || TouchUI;
            float xOff = Mathf.Max(0, _plates.Count) * StepX, visual = 40f, extra = Mathf.Max(0f, _navH - visual);
            float nextW = 60f, labelW = 84f, prevW = 60f, backW = 130f;
            var next = UISlantButton.Create(_rows, "Next page", new Vector2(nextW, visual), UISlantKind.Ghost, big, null, extra);
            next.SetLabel("▶"); next.Interactable = first + PerPage < _choices.Count; next.Clicked += () => Page(1);
            PlaceRight(next.Rt(), xOff, 0f, nextW, visual + extra);
            var label = UIFactory.Label(_rows, (_page + 1) + "/" + pages, big ? 28 : 26, UIFont.Heavy, UITheme.Text, TextAlignmentOptions.Center, UITextFx.Outline, "Page");
            PlaceRight(label.rectTransform, xOff + nextW, extra, labelW, visual);
            label.alignment = TextAlignmentOptions.Center;
            var prev = UISlantButton.Create(_rows, "Previous page", new Vector2(prevW, visual), UISlantKind.Ghost, big, null, extra);
            prev.SetLabel("◀"); prev.Interactable = _page > 0; prev.Clicked += () => Page(-1);
            PlaceRight(prev.Rt(), xOff + nextW + labelW, 0f, prevW, visual + extra);
            var back = UISlantButton.Create(_rows, "Back", new Vector2(backW, visual), UISlantKind.Ghost, big, null, extra);
            back.SetLabel("← 뒤로"); back.Interactable = _back != null; back.Clicked += Back;
            PlaceRight(back.Rt(), xOff + nextW + labelW + prevW + 14f, 0f, backW, visual + extra);
            foreach (var go in new[] { next.gameObject, label.gameObject, prev.gameObject, back.gameObject }) _navObjects.Add(go);
        }

        void Page(int delta)
        {
            int next = Mathf.Clamp(_page + delta, 0, Math.Max(0, (_choices.Count - 1) / PerPage));
            if (next == _page) return;
            _armedTargetId = null;
            _page = next; _focus = 0; _animateNext = true; Render();
        }

        void Focus(int index)
        {
            int count = Math.Min(PerPage, _choices.Count - _page * PerPage);
            if (count <= 0) return;
            _focus = (index % count + count) % count;
            var choice = _choices[_page * PerPage + _focus];
            if (_armedTargetId != null && _armedTargetId != choice.TargetId) _armedTargetId = null;
            for (int i = 0; i < _plates.Count; i++) _plates[i].Focused = i == _focus;
            // One slim line: the first line of the command text (target rows lead with the estimate), or why it is unusable.
            string firstLine = choice.Description ?? "";
            int newline = firstLine.IndexOf((char)10);
            if (newline >= 0) firstLine = firstLine.Substring(0, newline);
            _description.text = choice.Enabled ? firstLine : UITheme.Tag(UITheme.Danger) + "사용 불가 · " + Reason(choice.Reason) + "</color>";
            SetMarks(choice.Marks);
            choice.Preview?.Invoke();
            SetHeroFocus(choice.TargetId != null && _cards.TryGetValue(choice.TargetId, out var target) && target.Unit.Side == BattleSide.Party ? choice.TargetId : _actor?.Id);
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

        void PointerSelect(int index)
        {
            if (!_input || Paused || Time.frameCount == _openedFrame || index < 0 || index >= _choices.Count) return;
            var choice = _choices[index];
            if (!choice.Enabled) { Select(index); return; }
            if (string.IsNullOrEmpty(choice.TargetId)) { Select(index); return; }

            UIInput.Consume();
            string targetId = choice.TargetId;
            if (_armedTargetId != targetId)
            {
                _armedTargetId = targetId;
                UISound.Play(UISoundId.Move);
                Focus(index - _page * PerPage);
                return;
            }
            Select(index);
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

        // ---- motion ---------------------------------------------------------------------------------

        static bool ReducedMotion => UIRoot.Instance != null && UIRoot.Instance.ReducedMotion;

        /// <summary>Slides a fan element in from the right (160 ms OutBack, 30 ms stagger) with a fade; reduced motion: 150 ms fade only.</summary>
        void Arrive(RectTransform rt, float delay, Vector2? homeOverride = null)
        {
            if (!rt.TryGetComponent(out CanvasGroup group)) group = rt.gameObject.AddComponent<CanvasGroup>();
            UITween.Kill(rt);
            Vector2 home = homeOverride ?? rt.anchoredPosition;
            rt.anchoredPosition = home;
            if (!Application.isPlaying) { group.alpha = 1f; return; }
            group.alpha = 0f;
            if (ReducedMotion)
            {
                UITween.To(rt, 0.15f, t => group.alpha = t, UIEase.Linear, delay);
                return;
            }
            rt.anchoredPosition = home + new Vector2(300f, 0f);
            UITween.To(rt, 0.16f, t => { rt.anchoredPosition = home + new Vector2(300f * (1f - t), 0f); group.alpha = Mathf.Clamp01(t * 3f); }, UIEase.OutBack, delay);
        }

        void AnimateIn(bool animate)
        {
            if (!animate)
            {
                foreach (var plate in _plates) if (plate.TryGetComponent(out CanvasGroup g)) g.alpha = 1f;
                return;
            }
            for (int i = 0; i < _plates.Count; i++) Arrive(_plates[i].Rt(), i * 0.03f);
            Arrive(_headRect, 0f);
            Arrive(_detail, _plates.Count * 0.03f);
            for (int i = 0; i < _navObjects.Count; i++) Arrive((RectTransform)_navObjects[i].transform, (_plates.Count + 1) * 0.03f);
        }

        /// <summary>Command accepted: the picked plate flashes, the rest slide out right (140 ms), then the fan closes.</summary>
        void CloseMenu()
        {
            if (!Application.isPlaying || ReducedMotion || _plates.Count == 0 || !isActiveAndEnabled) { _menu.gameObject.SetActive(false); return; }
            _menuClosing = true;
            UITween.Kill(_menu);
            if (_focus >= 0 && _focus < _plates.Count) _plates[_focus].Plate.Fill.color = Color.white;
            int n = _plates.Count;
            for (int i = 0; i < n; i++) Leave(_plates[i].Rt(), i * 0.02f);
            Leave(_headRect, 0f); Leave(_detail, 0f);
            foreach (var go in _navObjects) Leave((RectTransform)go.transform, 0f);
            UITween.Delay(_menu, 0.14f + 0.02f * n, () => { _menuClosing = false; if (_menu != null) _menu.gameObject.SetActive(false); });
        }

        void Leave(RectTransform rt, float delay)
        {
            UITween.Kill(rt);
            Vector2 from = rt.anchoredPosition;
            if (!rt.TryGetComponent(out CanvasGroup group)) group = rt.gameObject.AddComponent<CanvasGroup>();
            UITween.To(rt, 0.14f, t => { rt.anchoredPosition = from + new Vector2(380f * t, 0f); group.alpha = 1f - t * 0.6f; }, UIEase.InCubic, delay);
        }
    }
}
