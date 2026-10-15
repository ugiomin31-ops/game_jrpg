using System;
using System.Collections.Generic;
using Abyss.Logic;
using Abyss.Logic.Battle;
using Abyss.Runtime.Battle;
using TMPro;
using UnityEngine;
using UnityEngine.EventSystems;
using UnityEngine.UI;

namespace Abyss.UI.Battle
{
    /// <summary>Press-and-hold detector for enemy tags (opens the full card without selecting).</summary>
    sealed class UITagPress : MonoBehaviour, IPointerDownHandler, IPointerUpHandler, IPointerExitHandler
    {
        public Action LongPress;
        float _downAt = -1f;
        bool _fired;
        /// <summary>True once when the last press was a long one (the following click must be ignored).</summary>
        public bool ConsumeLong() { bool value = _fired; _fired = false; return value; }
        public void OnPointerDown(PointerEventData e) { _downAt = Time.unscaledTime; _fired = false; }
        public void OnPointerUp(PointerEventData e) { _downAt = -1f; }
        public void OnPointerExit(PointerEventData e) { _downAt = -1f; }
        void Update()
        {
            if (_downAt < 0f || Time.unscaledTime - _downAt < 0.45f) return;
            _downAt = -1f; _fired = true;
            LongPress?.Invoke();
        }
    }

    public sealed partial class BattleHUD
    {
        enum TagLevel { Compact, Full, Icon, Edge, Hidden }

        sealed class Card
        {
            public BattleDisplayUnit Unit;
            public bool Party;
            public RectTransform Root;
            public UISlantPlate Plate;
            public TMP_Text Name, HpText, HpLine, IntentLine, IconLabel, PillText, ThreatText;
            public UISlantBar Hp, Mp;
            public Image Face, Ring, RingTrack, IntentIcon, IntentDot;
            public UIPips Shield;
            public UISlantPlate Pill, ThreatChip;
            public readonly Image[] StatusIcons = new Image[6];
            public readonly Image[] WeakIcons = new Image[4];
            public RectTransform Reticle;
            public readonly List<Image> ReticleBars = new List<Image>();
            public UITagPress Press;
            public bool PillDirty;
            public bool Threatened, Marked, Pinned, HasIntent, IntentCharge, ExtraRow, EnemyThreat, PillOn;
            public int WeakCount, StatusCount;
            public TagLevel Level = TagLevel.Compact, LaidLevel = TagLevel.Hidden;
            public Vector2 LaidSize;
            public bool Dirty = true, LaidExtra;
            public int LastKey = -1;
            public Rect UnitRect, TagRect;
            public bool HasRect, OnScreen;
            public List<Renderer> Renderers;
            public readonly List<Transform> Bones = new List<Transform>();
            public int RendererScan = -1000;
            public Vector2 PlatePos;
            /// <summary>Cached preferred widths (canvas units) of the enemy name at the tag's name size and of the icon-level label.</summary>
            public string NameKey, IconKey;
            public float NameW, IconW;
        }

        sealed class TargetMark
        {
            public string Id, Pill;
            public bool Ally;
        }

        sealed class Choice
        {
            public string Label, Description, Reason, Hint, Right, ChipText;
            public Color ChipColor;
            public bool Enabled = true;
            public string TargetId;
            public Action Pick, Preview;
            public Sprite Icon;
            public readonly List<TargetMark> Marks = new List<TargetMark>();
        }

        readonly Dictionary<string, Card> _cards = new Dictionary<string, Card>();
        readonly Dictionary<string, TargetMark> _marks = new Dictionary<string, TargetMark>();
        readonly HashSet<string> _threatened = new HashSet<string>();
        readonly Dictionary<string, Sprite> _statusArt = new Dictionary<string, Sprite>(StringComparer.Ordinal);
        readonly System.Text.StringBuilder _text = new System.Text.StringBuilder();

        // ---- building -------------------------------------------------------------------------------

        public void AddUnit(BattleDisplayUnit unit)
        {
            if (unit.Side == BattleSide.Party) AddPartyPlate(unit); else AddEnemyTag(unit);
        }

        Vector2 PlatePosition(int slot) => new Vector2((Compact ? 22f : 30f) + slot * (_partyW + _partyGap), _partyMargin);

        void AttachTap(Card card)
        {
            var hit = card.Root.gameObject.AddComponent<Image>();
            hit.color = Color.clear; hit.raycastTarget = true;
            card.Root.gameObject.AddComponent<UISkew>();
            string unitId = card.Unit.Id;
            var tap = card.Root.gameObject.AddComponent<Button>();
            tap.transition = Selectable.Transition.None;
            tap.navigation = new Navigation { mode = Navigation.Mode.None };
            tap.targetGraphic = hit;
            if (!card.Party)
            {
                card.Press = card.Root.gameObject.AddComponent<UITagPress>();
                card.Press.LongPress = () => { if (!Paused && _reward == null) { card.Pinned = !card.Pinned; card.Dirty = true; } };
            }
            tap.onClick.AddListener(() =>
            {
                if (card.Press != null && card.Press.ConsumeLong()) return;
                TapUnit(unitId);
            });
        }

        Image NewIcon(Transform parent, float size, string name = "Icon")
        {
            var icon = UIFactory.Icon(parent, null, size, name);
            icon.enabled = false; icon.raycastTarget = false;
            return icon;
        }

        /// <summary>Slim party plate: circular face inside a TP ring, name, big HP number, HP/MP bars, status icons.</summary>
        void AddPartyPlate(BattleDisplayUnit unit)
        {
            bool compact = Compact;
            var card = new Card { Unit = unit, Party = true, Level = TagLevel.Compact };
            var plate = UISlantPlate.Create(_party, "Party plate " + unit.Name, UISlant.Navy, UISlant.Rest, 2f, true, 5f, false);
            card.Plate = plate; card.Root = plate.Rect;
            card.PlatePos = PlatePosition(unit.Slot);
            plate.Rect.Place(UIAnchor.BottomLeft, card.PlatePos, new Vector2(_partyW, _partyH));
            AttachTap(card);
            float h = _partyH, w = _partyW;
            float ring = h - (compact ? 10f : 12f), face = ring * 0.72f;
            card.RingTrack = UIFactory.Image(plate.Rect, UISlant.Ring, new Color(1f, 1f, 1f, 0.16f), "TP track");
            card.RingTrack.rectTransform.Place(UIAnchor.Left, new Vector2(14f, 0f), new Vector2(ring, ring));
            card.Ring = UIFactory.Image(plate.Rect, UISlant.Ring, UITheme.Tp, "TP ring");
            card.Ring.rectTransform.Place(UIAnchor.Left, new Vector2(14f, 0f), new Vector2(ring, ring));
            card.Ring.type = Image.Type.Filled; card.Ring.fillMethod = Image.FillMethod.Radial360;
            card.Ring.fillOrigin = (int)Image.Origin360.Top; card.Ring.fillClockwise = true;
            card.Face = UISlant.CircleFace(plate.Rect, face);
            card.Face.rectTransform.parent.GetComponent<RectTransform>().Place(UIAnchor.Left, new Vector2(14f + (ring - face) * 0.5f, 0f), new Vector2(face, face));
            card.Face.sprite = UIArtwork.Hero(unit.DefId); card.Face.enabled = true;
            float textX = 14f + ring + 12f, right = 18f, hpWidth = compact ? 112f : 128f;
            card.Name = UIFactory.Label(plate.Rect, unit.Name, compact ? 26 : 28, UIFont.Bold, UITheme.Text, TextAlignmentOptions.MidlineLeft, UITextFx.Outline, "Name");
            card.Name.overflowMode = TextOverflowModes.Ellipsis;
            card.Name.rectTransform.Stretch(textX, 3f, right + hpWidth, h - (compact ? 45f : 55f));
            card.HpText = UIFactory.Label(plate.Rect, "", compact ? 34 : 38, UIFont.Heavy, UITheme.Text, TextAlignmentOptions.MidlineRight, UITextFx.Outline, "HP");
            card.HpText.rectTransform.Stretch(w - right - hpWidth, 1f, right, h - (compact ? 45f : 55f));
            float barW = w - textX - right;
            card.Hp = UISlantBar.Create(plate.Rect, UIGaugeKind.Hp, "HP bar");
            card.Hp.GetComponent<RectTransform>().Place(UIAnchor.TopLeft, new Vector2(textX, compact ? -48f : -58f), new Vector2(barW, compact ? 10f : 12f));
            card.Mp = UISlantBar.Create(plate.Rect, UIGaugeKind.Mp, "MP bar");
            card.Mp.GetComponent<RectTransform>().Place(UIAnchor.TopLeft, new Vector2(textX, compact ? -62f : -74f), new Vector2(barW, compact ? 7f : 8f));
            for (int i = 0; i < card.StatusIcons.Length; i++)
            {
                var icon = NewIcon(plate.Rect, compact ? 20f : 22f, "Status");
                icon.rectTransform.Place(UIAnchor.TopLeft, new Vector2(textX + i * (compact ? 24f : 26f), compact ? -72f : -88f), new Vector2(compact ? 20f : 22f, compact ? 20f : 22f));
                card.StatusIcons[i] = icon;
            }
            card.ThreatChip = UISlant.Pill(plate.Rect, "Threat chip", UISlant.Threat, Color.white, out var chipText, 24f);
            card.ThreatText = chipText; chipText.text = "위협 대상";
            card.ThreatChip.Rect.Place(UIAnchor.TopRight, new Vector2(1f, 0f), new Vector2(-14f, -2f), new Vector2(150f, 30f));
            card.ThreatChip.gameObject.SetActive(false);
            card.Pill = UISlant.Pill(plate.Rect, "Estimate pill", UISlant.Navy, UITheme.Positive, out var pillText, 26f);
            card.PillText = pillText;
            card.Pill.Rect.Place(UIAnchor.TopLeft, new Vector2(0f, 0f), new Vector2(18f, -2f), new Vector2(220f, 36f));
            card.Pill.gameObject.SetActive(false);
            _cards.Add(unit.Id, card);
            Sync(unit, true);
        }

        /// <summary>
        /// Enemy tag: name, thin HP bar, known weakness icons, intent icon; status icons and shield pips on an optional third
        /// row. Sizes and positions are decided every frame by the packer (see BattleHUD.Tags.cs).
        /// </summary>
        void AddEnemyTag(BattleDisplayUnit unit)
        {
            var card = new Card { Unit = unit, Party = false };
            var plate = UISlantPlate.Create(_world, "Enemy tag " + unit.Name, UISlant.Navy, UISlant.Rest, 2f, true, 5f, false);
            card.Plate = plate; card.Root = plate.Rect;
            plate.Rect.anchorMin = plate.Rect.anchorMax = Vector2.zero; plate.Rect.pivot = Vector2.zero;
            plate.Rect.sizeDelta = new Vector2(unit.Boss ? 320f : 264f, 62f);
            AttachTap(card);
            card.Name = UIFactory.Label(plate.Rect, unit.Name, 24, UIFont.Bold, UITheme.Text, TextAlignmentOptions.MidlineLeft, UITextFx.Outline, "Name");
            card.Name.overflowMode = TextOverflowModes.Ellipsis;
            card.Hp = UISlantBar.Create(plate.Rect, UIGaugeKind.Custom, "HP bar");
            card.Hp.FillColor = UISlant.Coral;
            for (int i = 0; i < card.WeakIcons.Length; i++) card.WeakIcons[i] = NewIcon(plate.Rect, 24f, "Weakness");
            for (int i = 0; i < card.StatusIcons.Length; i++) card.StatusIcons[i] = NewIcon(plate.Rect, 22f, "Status");
            card.Shield = UIFactory.Pips(plate.Rect, unit.MaxShield, 15f);
            card.IntentIcon = NewIcon(plate.Rect, 28f, "Intent");
            card.IntentDot = UIFactory.Image(plate.Rect, UISprites.Circle, UISlant.Coral, "Intent mark");
            card.IntentDot.rectTransform.sizeDelta = new Vector2(12f, 12f); card.IntentDot.enabled = false;
            card.HpLine = UIFactory.Label(plate.Rect, "", 24, UIFont.Body, UITheme.TextDim, TextAlignmentOptions.MidlineLeft, UITextFx.Shadow, "HP line");
            card.HpLine.overflowMode = TextOverflowModes.Ellipsis;
            card.IntentLine = UIFactory.Label(plate.Rect, "", 24, UIFont.Bold, UITheme.Warning, TextAlignmentOptions.MidlineLeft, UITextFx.Shadow, "Intent line");
            card.IntentLine.overflowMode = TextOverflowModes.Ellipsis;
            card.IconLabel = UIFactory.Label(plate.Rect, "", 24, UIFont.Heavy, UITheme.Text, TextAlignmentOptions.Center, UITextFx.Outline, "Short label");
            card.IconLabel.overflowMode = TextOverflowModes.Ellipsis;
            // The predicted-damage pill is its own plate in the tag layer so the packer can seat it independently of the tag.
            card.Pill = UISlant.Pill(_world, "Enemy tag pill " + unit.Name, UISlant.Navy, UISlant.Coral, out var pillText, 34f);
            card.PillText = pillText; pillText.richText = true; pillText.enableAutoSizing = true; pillText.fontSizeMin = 26f; pillText.fontSizeMax = 34f;
            card.Pill.Rect.anchorMin = card.Pill.Rect.anchorMax = Vector2.zero; card.Pill.Rect.pivot = Vector2.zero;
            card.Pill.gameObject.SetActive(false);
            _cards.Add(unit.Id, card);
            Sync(unit, true);
        }

        void RebuildCards()
        {
            var states = new Dictionary<string, (bool Pinned, bool EnemyThreat)>();
            _rebuildUnits.Clear();
            foreach (var card in _cards.Values)
            {
                _rebuildUnits.Add(card.Unit);
                states.Add(card.Unit.Id, (card.Pinned, card.EnemyThreat));
            }
            foreach (var card in _cards.Values)
            {
                if (card.Reticle != null) Destroy(card.Reticle.gameObject);
                if (!card.Party && card.Pill != null) Destroy(card.Pill.gameObject);
                card.Root.gameObject.SetActive(false); Destroy(card.Root.gameObject);
            }
            _cards.Clear();
            foreach (var unit in _rebuildUnits) AddUnit(unit);
            _rebuildUnits.Clear();
            foreach (var card in _cards.Values)
            {
                var state = states[card.Unit.Id];
                card.Pinned = state.Pinned;
                card.EnemyThreat = state.EnemyThreat;
            }
            // ApplyMarks also refreshes plate colours, threat chips and raised positions after restoration.
            ApplyMarks();
        }

        void LayoutParty()
        {
            foreach (var card in _cards.Values)
                if (card.Party)
                {
                    card.PlatePos = PlatePosition(card.Unit.Slot);
                    card.Root.sizeDelta = new Vector2(_partyW, _partyH);
                }
        }

        // ---- sync -----------------------------------------------------------------------------------

        public void Sync(BattleDisplayUnit unit, bool instant = false)
        {
            if (!_cards.TryGetValue(unit.Id, out var card)) return;
            card.Hp.SetValue(unit.Hp, unit.MaxHp, instant);
            card.Mp?.SetValue(unit.Mp, unit.MaxMp, instant);
            card.Name.text = unit.Name;
            card.Name.color = unit.Alive ? UITheme.Text : new Color(.6f, .6f, .65f);
            int statusIndex = 0;
            foreach (var status in unit.Statuses.Values)
            {
                if (statusIndex == card.StatusIcons.Length) break;
                var icon = card.StatusIcons[statusIndex++];
                icon.sprite = _statusArt[status.Id];
                icon.enabled = true;
            }
            card.StatusCount = statusIndex;
            while (statusIndex < card.StatusIcons.Length) card.StatusIcons[statusIndex++].enabled = false;
            if (card.Party)
            {
                card.HpText.text = unit.Hp.ToString("N0");
                card.HpText.color = unit.Alive && unit.MaxHp > 0 && unit.Hp * 4 <= unit.MaxHp ? UISlant.Coral : UITheme.Text;
                float tp = unit.MaxTp > 0 ? (float)unit.Tp / unit.MaxTp : 0f;
                card.Ring.fillAmount = Mathf.Clamp01(tp);
                card.Face.color = unit.Alive ? Color.white : new Color(.45f, .45f, .5f, 1f);
                card.Plate.Fill.color = unit.Alive ? UISlant.Navy : new Color(0.08f, 0.09f, 0.11f, 0.92f);
            }
            else
            {
                int weak = 0;
                foreach (int element in unit.Weaknesses)
                {
                    if (weak == card.WeakIcons.Length) break;
                    var sprite = UIArtwork.Element((Element)element);
                    if (sprite == null) continue;
                    var icon = card.WeakIcons[weak++];
                    icon.sprite = sprite; icon.enabled = true;
                }
                card.WeakCount = weak;
                while (weak < card.WeakIcons.Length) card.WeakIcons[weak++].enabled = false;
                card.Shield.Set(unit.Shield, unit.MaxShield);
                _text.Clear();
                _text.Append("HP ").Append(unit.Hp.ToString("N0")).Append(" / ").Append(unit.MaxHp.ToString("N0"));
                if (unit.MaxShield > 0) _text.Append("  실드 ").Append(unit.Shield).Append('/').Append(unit.MaxShield);
                if (unit.Broken) _text.Append("  BREAK");
                card.HpLine.text = _text.ToString();
                card.ExtraRow = card.StatusCount > 0 || unit.MaxShield > 0;
                card.IconLabel.text = IconText(unit);
                card.Hp.FillColor = unit.Broken ? UITheme.Warning : UISlant.Coral;
            }
            SyncWarnings(card);
            RefreshThreats();
            card.Dirty = true;
        }

        /// <summary>Icon-level label: the lane letter when the enemy has one, otherwise its full name (never a two-glyph stub).</summary>
        static string IconText(BattleDisplayUnit unit) => string.IsNullOrEmpty(unit.Suffix) ? unit.Name : unit.Suffix;

        static string FirstGlyph(string name) => string.IsNullOrEmpty(name) ? "?" : name.Substring(0, Mathf.Min(2, name.Length));

        public void SetChain(int value)
        {
            _chain.text = $"연계 ×{value}  +{value * 10}%";
            if (_chainPlate != null) _chainPlate.gameObject.SetActive(value > 0);
        }

        // ---- warnings / threats ----------------------------------------------------------------------

        string IntentAction(ActionKind kind, string skillId)
        {
            if (!string.IsNullOrEmpty(skillId) && _db.Skills.TryGetValue(skillId, out var skill)) return skill.DisplayName;
            switch (kind) { case ActionKind.Guard: return "방어"; case ActionKind.Flee: return "도주"; case ActionKind.Summon: return "소환"; default: return "공격"; }
        }

        string IntentTarget(Scope scope, string targetId)
        {
            if (scope == Scope.Random) return "무작위";
            if (scope == Scope.All) return "전체";
            return targetId != null && _cards.TryGetValue(targetId, out var target) ? target.Unit.Name : "대상 없음";
        }

        void SyncWarnings(Card card)
        {
            if (card.Party || card.IntentIcon == null) return;
            var unit = card.Unit; var pending = unit.DisplayCharge; var next = unit.LeadingIntent;
            bool visible = unit.Alive && (pending != null || next != null);
            card.HasIntent = visible;
            if (!visible)
            {
                card.IntentIcon.enabled = false; card.IntentDot.enabled = false; card.IntentLine.text = "";
                card.IntentCharge = false;
                return;
            }
            string skillId = pending?.SkillId ?? next.SkillId;
            ActionKind kind = pending != null ? ActionKind.Skill : next.Kind;
            bool charge = pending != null || next.IsChargeAnnounce || next.IsChargeRelease;
            card.IntentCharge = charge;
            card.IntentIcon.sprite = charge ? UIArtwork.Command("skill") : kind == ActionKind.Skill && _db.Skills.TryGetValue(skillId, out var skill)
                ? UIArtwork.Element(skill.Element) ?? UIArtwork.Command("attack")
                : UIArtwork.Command(kind == ActionKind.Guard ? "guard" : kind == ActionKind.Flee ? "flee" : "attack");
            card.IntentIcon.enabled = true;
            card.IntentDot.enabled = charge;
            int remaining = unit.Intents.Count - (next != null ? 1 : 0);
            if (pending != null && next != null && !next.IsChargeRelease) remaining++;
            _text.Clear();
            _text.Append(charge ? "준비 중! " : "").Append(IntentAction(kind, skillId)).Append(" → ")
                .Append(IntentTarget(pending?.Scope ?? next.Scope, pending != null ? pending.TargetUnitId : next.TargetUnitId));
            if (remaining > 0) _text.Append("  (+").Append(remaining).Append(')');
            else if (charge) _text.Append("  · BREAK로 저지");
            card.IntentLine.text = _text.ToString();
            card.IntentLine.color = charge ? UISlant.Coral : UITheme.Warning;
        }

        bool WarnsHero(ActionKind kind, string skillId, Scope scope, string targetId, string heroId)
        {
            if (heroId == null || scope == Scope.Random) return false;
            if (kind != ActionKind.Attack && kind != ActionKind.Skill) return false;
            if (kind == ActionKind.Skill && (!_db.Skills.TryGetValue(skillId, out var skill) || skill.Kind != SkillKind.Damage || skill.TargetType != TargetType.Enemy)) return false;
            return scope == Scope.All || targetId == heroId;
        }

        bool WarnsHero(BattleDisplayUnit enemy, string heroId)
        {
            if (!enemy.Alive) return false;
            var pending = enemy.DisplayCharge;
            if (pending != null && WarnsHero(ActionKind.Skill, pending.SkillId, pending.Scope, pending.TargetUnitId, heroId)) return true;
            foreach (var intent in enemy.Intents.Values)
                if (WarnsHero(intent.Kind, intent.SkillId, intent.Scope, intent.TargetUnitId, heroId)) return true;
            return false;
        }

        public void SetHeroFocus(string id) { _heroFocus = id; RefreshThreats(); }

        void RefreshThreats()
        {
            foreach (var card in _cards.Values)
            {
                bool show = false;
                if (_heroFocus != null && card.Unit.Alive)
                {
                    if (card.Unit.Side == BattleSide.Enemy) show = WarnsHero(card.Unit, _heroFocus);
                    else foreach (var enemy in _cards.Values)
                        if (enemy.Unit.Side == BattleSide.Enemy && WarnsHero(enemy.Unit, _heroFocus) && WarnsHero(enemy.Unit, card.Unit.Id)) { show = true; break; }
                }
                card.Threatened = show;
            }
            RefreshPlateStates();
        }

        /// <summary>Edge colours and the raised acting hero; cheap, called after any state change.</summary>
        void RefreshPlateStates()
        {
            bool reduced = UIRoot.Instance != null && UIRoot.Instance.ReducedMotion;
            foreach (var card in _cards.Values)
            {
                // Teardown (BattleView.Restore while play mode stops) can run after the plates died with the UI root.
                if (card.Plate == null || card.Root == null) continue;
                bool threat = card.EnemyThreat;
                bool active = card.Party && _input && _actor != null && _actor.Id == card.Unit.Id;
                bool target = card.Marked;
                Color edge = threat ? UISlant.Threat : target ? UISlant.Coral : card.Threatened ? UITheme.Warning : active ? UISlant.Coral : UISlant.Rest;
                Color fill = threat ? UISlant.ThreatFill : UISlant.Navy;
                if (!card.Unit.Alive) fill = new Color(0.08f, 0.09f, 0.11f, 0.92f);
                card.Plate.SetColors(fill, edge);
                if (card.ThreatChip != null) card.ThreatChip.gameObject.SetActive(threat && card.Unit.Alive);
                if (card.Party)
                {
                    float y = card.PlatePos.y + (active || threat ? _partyRaise : 0f);
                    var rt = card.Root;
                    if (!Mathf.Approximately(rt.anchoredPosition.y, y) || !Mathf.Approximately(rt.anchoredPosition.x, card.PlatePos.x))
                    {
                        UITween.Kill(rt);
                        if (reduced || !Application.isPlaying) rt.anchoredPosition = new Vector2(card.PlatePos.x, y);
                        else UITween.Move(rt, new Vector2(card.PlatePos.x, y), 0.12f, UIEase.OutCubic);
                    }
                }
            }
        }

        // ---- turn order -----------------------------------------------------------------------------

        public void ShowOrder(int round, IReadOnlyList<string> order, string active)
        {
            _orderRound = round; _orderActive = active; _orderShown = true;
            _orderIds.Clear();
            for (int i = 0; i < order.Count; i++) _orderIds.Add(order[i]);
            RefreshOrder();
            if (active != null && _cards.TryGetValue(active, out var actor) && !actor.Party && actor.Unit.Alive) ShowEnemyTurn(actor);
            else HideEnemyTurn();
        }

        /// <summary>Redraws the chip strip from the cached round/order/active state (at most 7 living units, active first).</summary>
        void RefreshOrder()
        {
            _roundLabel.text = "<size=80%>TURN</size> " + _orderRound;
            int start = _orderIds.IndexOf(_orderActive);
            int n = 0, count = _orderIds.Count;
            float x = 0f;
            for (int step = 0; step < count && n < 7; step++)
            {
                string id = _orderIds[(Mathf.Max(0, start) + step) % count];
                if (!_cards.TryGetValue(id, out var card) || !card.Unit.Alive) continue;
                if (n == _orderChips.Count) _orderChips.Add(BuildChip());
                var chip = _orderChips[n++];
                bool now = id == _orderActive, party = card.Party;
                float scale = now ? 1.3f : 1f;
                chip.Root.gameObject.SetActive(true);
                chip.Root.localScale = new Vector3(scale, scale, 1f);
                chip.Root.anchoredPosition = new Vector2(x + 66f * scale * 0.5f, 0f);
                x += 62f * scale + (now ? 12f : 6f);
                chip.Face.sprite = party ? UIArtwork.Hero(card.Unit.DefId) : UIArtwork.Enemy(card.Unit.DefId);
                chip.Face.enabled = true;
                chip.Plate.SetColors(UISlant.Navy, now ? UISlant.Coral : party ? UITheme.Gold : new Color(0.75f, 0.28f, 0.34f, 1f));
                chip.Letter.text = party ? "" : card.Unit.Suffix ?? "";
            }
            for (int i = n; i < _orderChips.Count; i++) _orderChips[i].Root.gameObject.SetActive(false);
        }

        (RectTransform Root, UISlantPlate Plate, Image Face, TMP_Text Letter) BuildChip()
        {
            var plate = UISlantPlate.Create(_orderRow, "Chip", UISlant.Navy, UITheme.Gold, 2f, true, 4f, false);
            var rt = plate.Rect;
            rt.anchorMin = rt.anchorMax = new Vector2(0f, 0.5f); rt.pivot = new Vector2(0.5f, 0.5f);
            rt.sizeDelta = new Vector2(66f, 54f);
            var face = UISlant.SlantFace(rt, new Vector2(60f, 48f));
            face.rectTransform.parent.GetComponent<RectTransform>().Place(UIAnchor.Center, Vector2.zero, new Vector2(60f, 48f));
            var letter = UIFactory.Label(rt, "", 26, UIFont.Heavy, UITheme.Text, TextAlignmentOptions.BottomRight, UITextFx.Outline, "Letter");
            letter.rectTransform.Place(UIAnchor.BottomRight, new Vector2(-2f, 0f), new Vector2(34f, 30f));
            return (rt, plate, face, letter);
        }

        // ---- marks (reticle + estimate pill) -------------------------------------------------------

        void SetMarks(List<TargetMark> marks)
        {
            _marks.Clear();
            if (marks != null) foreach (var mark in marks) _marks[mark.Id] = mark;
            ApplyMarks();
        }

        void ClearMarks() { if (_marks.Count == 0) return; _marks.Clear(); ApplyMarks(); }

        void ApplyMarks()
        {
            foreach (var card in _cards.Values)
            {
                bool marked = _marks.TryGetValue(card.Unit.Id, out var mark) && card.Unit.Alive;
                card.Marked = marked;
                card.Dirty = true;
                if (marked)
                {
                    card.PillOn = !string.IsNullOrEmpty(mark.Pill);
                    if (card.Party) card.Pill.gameObject.SetActive(card.PillOn);
                    if (card.PillOn) card.PillText.text = mark.Pill;
                    card.PillDirty = true;
                    EnsureReticle(card);
                    var color = mark.Ally ? UITheme.GoldBright : UISlant.Coral;
                    foreach (var bar in card.ReticleBars) bar.color = color;
                    if (card.Party) card.Pill.Edge.color = UITheme.Positive;
                    else card.Pill.Edge.color = UISlant.Coral;
                }
                else { card.PillOn = false; card.Pill.gameObject.SetActive(false); }
                if (card.Reticle != null) card.Reticle.gameObject.SetActive(marked);
            }
            RefreshPlateStates();
        }

        void EnsureReticle(Card card)
        {
            if (card.Reticle != null) return;
            card.Reticle = UIFactory.Rect(_world, "Reticle " + card.Unit.Name);
            card.Reticle.anchorMin = card.Reticle.anchorMax = Vector2.zero; card.Reticle.pivot = Vector2.zero;
            // Four L brackets: each is a horizontal + vertical bar anchored to a corner of the reticle rect.
            for (int corner = 0; corner < 4; corner++)
            {
                float ax = corner % 2, ay = corner / 2;
                for (int bar = 0; bar < 2; bar++)
                {
                    var img = UIFactory.Image(card.Reticle, UISprites.White, UISlant.Coral, "Bracket");
                    var rt = img.rectTransform;
                    rt.anchorMin = rt.anchorMax = new Vector2(ax, ay);
                    rt.pivot = new Vector2(ax, ay);
                    rt.sizeDelta = bar == 0 ? new Vector2(34f, 5f) : new Vector2(5f, 34f);
                    rt.anchoredPosition = Vector2.zero;
                    card.ReticleBars.Add(img);
                }
            }
        }
    }
}
