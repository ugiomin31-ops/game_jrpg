using System;
using System.Collections.Generic;
using System.Text;
using Abyss.Logic;
using Abyss.Logic.Battle;
using Abyss.Logic.Game;
using UnityEngine.EventSystems;
using Abyss.Runtime.Battle;
using TMPro;
using UnityEngine;
using UnityEngine.UI;

namespace Abyss.UI.Battle
{
    /// <summary>
    /// Snapshot HUD and command navigation; engine queries occur only at an input boundary. Slanted-plate battle HUD:
    /// compact enemy tags and slim party plates packed clear of every unit (BattleHUD.Tags.cs), the right-hand command
    /// fan (BattleHUD.Menu.cs) and published occlusion rectangles (BattleHUD.Layout.cs). Runs after the camera.
    /// </summary>
    [DefaultExecutionOrder(200)]
    public sealed partial class BattleHUD : MonoBehaviour
    {
        readonly List<UIButton> _buttons = new List<UIButton>();
        RectTransform _root, _party, _world, _menu, _rows, _detail, _headRect, _cutin, _reward, _banner, _enemyBanner, _logPanel, _top, _orderRow, _autoBanner;
        TMP_Text _log, _title, _description, _cutinTitle, _cutinText, _rewardText, _bannerText, _roundLabel, _autoBannerTitle, _chain;
        UISlantButton _autoButton, _speedButton, _manualButton;
        UISlantPlate _chainPlate;
        Action _toggleSpeed;
        ScrollRect _rewardScroll;
        TMP_Text _rewardCounter;
        RectTransform _announce, _announceBand;
        TMP_Text _announceTitle, _announceSub;
        CanvasGroup _announceGroup;
        BattleEngine _engine;
        GameDB _db;
        Camera _camera;
        Func<BattleCommand, bool> _submit;
        Func<bool> _paused;
        Action _toggleAuto, _back;
        Action<int> _rewardPage;
        Action<string> _preview;
        BattleUnit _actor;
        int _page, _focus, _openedFrame, _choiceVersion;
        bool _input, _auto;
        string _heroFocus;
        RectTransform _fastToast;
        TMP_Text _fastSummary, _fastExtra;
        Action _fastConfirmed;
        float _fastElapsed;
        int _fastOpenedFrame;
        bool _fastArmed, _fastAnswered;
        /// <summary>Live pause state of the owning view (no frame-late copy).</summary>
        public bool Paused => _paused != null && _paused();
        /// <summary>Phones/tablets: taller command rows and buttons sized for a thumb.</summary>
        static bool TouchUI => Application.isMobilePlatform || UITouch.Supported;
        /// <summary>Landscape phone (900-unit canvas): slimmer bars and cards so the arena stays visible.</summary>
        static bool Compact => UIRoot.Compact;
        int _perPage = 6;
        int PerPage => _perPage;
        // Layout key: compact mode, touch-first, touch target height, canvas scale and root (safe-area) size.
        bool _layoutReady, _layoutCompact, _layoutTouch, _ultCompact;
        float _layoutTouchTarget, _layoutScale;
        Vector2 _layoutRoot;
        readonly List<(RectTransform Root, UISlantPlate Plate, Image Face, TMP_Text Letter)> _orderChips = new List<(RectTransform, UISlantPlate, Image, TMP_Text)>();
        readonly List<string> _orderIds = new List<string>();
        readonly List<BattleDisplayUnit> _rebuildUnits = new List<BattleDisplayUnit>();
        int _orderRound;
        // Phase / enemy-ultimate call-out: requested content and lifetime (CutIn..HideCutIn) versus its resolved seat (UpdateCallout).
        string _coTitle = "", _coText = "";
        bool _coRequested, _coShown, _coRelayout, _coRibbon;
        Vector2 _coSize;
        Rect _coRect;
        string _orderActive;
        bool _orderShown;
        Vector2 _enemyBannerHome;
        public bool CommandRootOpen => _input && _back == null && _reward == null;

        /// <param name="submit">Returns true only when the view accepted the command and owns its replay.</param>
        /// <param name="paused">Live pause query; input is ignored while it returns true.</param>
        public void Initialize(Transform parent, Camera camera, GameDB db, Func<BattleCommand, bool> submit,
            Action toggleAuto, Action<string> preview, Func<bool> paused = null)
        {
            _camera = camera; _db = db; _submit = submit; _toggleAuto = toggleAuto; _preview = preview; _paused = paused;
            _statusArt.Clear();
            foreach (var status in db.Statuses) _statusArt.Add(status.Key, UIArtwork.Status(status.Key));
            _root = UIFactory.Rect(parent, "Battle HUD").Stretch();
            _world = UIFactory.Rect(_root, "Enemy tags").Stretch();
            _party = UIFactory.Rect(_root, "Party plates").Stretch();
            BuildChrome();
            BuildMenu();
            BuildEnemyBanner();
            // Boss phase / enemy ultimate call-out: slanted plate (the skill ribbon's style). CutIn/HideCutIn own its content and
            // lifetime, LayoutCallout its size and UpdateCallout (BattleHUD.Tags.cs) its seat, validated every frame so it never
            // covers a living hero, the party plates or the top controls.
            var cutin = UISlantPlate.Create(_root, "Phase call-out", new Color(0.04f, 0.08f, 0.13f, 1f), UITheme.Gold, 3f, true, 6f, true);
            _cutin = cutin.Rect;
            _cutin.anchorMin = _cutin.anchorMax = Vector2.zero; _cutin.pivot = Vector2.zero;
            _cutinTitle = UIFactory.Label(_cutin, "", 42, UIFont.Heavy, UITheme.Text, TextAlignmentOptions.Center, UITextFx.Outline, "Title");
            _cutinTitle.overflowMode = TextOverflowModes.Ellipsis;
            _cutinText = UIFactory.Paragraph(_cutin, "", 29, null, "Subtitle");
            _cutinText.alignment = TextAlignmentOptions.Top;
            _cutinText.overflowMode = TextOverflowModes.Ellipsis;
            _cutinText.maxVisibleLines = 2;
            _cutin.gameObject.SetActive(false);
            BuildSkillRibbon();
            BuildAutoBanner();
            BuildAnnounce();
            ApplyLayout();
            Lock();
        }

        /// <summary>Turn-order strip (top left), auto / speed toggles (top right), action line (top centre) and the chain pill.</summary>
        void BuildChrome()
        {
            _top = UIFactory.Rect(_root, "Turn order strip");
            _roundLabel = UIFactory.Label(_top, "", 34, UIFont.Heavy, UITheme.Text, TextAlignmentOptions.MidlineLeft, UITextFx.Outline, "Round");
            _roundLabel.fontStyle = FontStyles.Italic;
            _orderRow = UIFactory.Rect(_top, "Turn order");
            _autoButton = UISlantButton.Create(_root, "Auto battle", new Vector2(232f, 64f), UISlantKind.Simple, true);
            _autoButton.SetLabel("자동전투 OFF");
            _autoButton.Clicked += ToggleAuto;
            var logPlate = UISlantPlate.Create(_root, "Action line", UISlant.Navy, UISlant.Rest, 2f, true, 5f, false);
            _logPanel = logPlate.Rect;
            _log = UIFactory.Label(logPlate.Rect, "", 26, UIFont.Bold, UITheme.Text, TextAlignmentOptions.Center, UITextFx.Outline, "Action text");
            _log.Rt().Stretch(18, 2, 18, 2);
            _log.overflowMode = TextOverflowModes.Ellipsis;
            logPlate.gameObject.SetActive(false);
            _chainPlate = UISlantPlate.Create(_root, "Weakness chain", new Color(0.18f, 0.12f, 0.4f, 1f), UISlant.Rest, 2f, true, 5f, false);
            _chain = UIFactory.Label(_chainPlate.Rect, "연계 ×0", 26, UIFont.Heavy, UITheme.Text, TextAlignmentOptions.Center, UITextFx.Outline, "Chain text");
            _chain.Rt().Stretch(10, 0, 10, 0);
            _chain.overflowMode = TextOverflowModes.Ellipsis;
            _chainPlate.gameObject.SetActive(false);
        }

        /// <summary>Command fan shell: header tab, plate host and the description footer (a scrollable compact line).</summary>
        void BuildMenu()
        {
            _menu = UIFactory.Rect(_root, "Command fan");
            _rows = UIFactory.Rect(_menu, "Plates").Stretch();
            // Header: a short coral slash and the actor / verb in heavy type (no box).
            _headRect = UIFactory.Rect(_menu, "Header");
            var slash = UIFactory.Image(_headRect, UISprites.White, UISlant.Coral, "Slash");
            slash.gameObject.AddComponent<UISkew>();
            slash.rectTransform.anchorMin = slash.rectTransform.anchorMax = new Vector2(1f, 0.5f);
            slash.rectTransform.pivot = new Vector2(1f, 0.5f);
            slash.rectTransform.sizeDelta = new Vector2(10f, 30f);
            slash.rectTransform.anchoredPosition = new Vector2(-4f, 0f);
            _title = UIFactory.Label(_headRect, "", 30, UIFont.Heavy, UITheme.Text, TextAlignmentOptions.MidlineRight, UITextFx.Outline, "Title");
            _title.Rt().Stretch(0, 0, 26, 0);
            _title.enableAutoSizing = true; _title.fontSizeMin = 24; _title.fontSizeMax = 32;
            _title.overflowMode = TextOverflowModes.Ellipsis;
            // One slim description line for the selected command (plain text on the scene, no panel).
            var line = UISlantPlate.Create(_menu, "Description", new Color(0.03f, 0.06f, 0.1f, 0.84f), UISlant.Rest, 2f, false, 0f, false);
            _detail = line.Rect;
            _description = UIFactory.Label(_detail, "", 24, UIFont.Body, UITheme.Text, TextAlignmentOptions.MidlineLeft, UITextFx.Shadow, "Description text");
            _description.Rt().Stretch(24, 0, 20, 0);
            _description.overflowMode = TextOverflowModes.Ellipsis;
            _description.richText = true;
            _menu.gameObject.SetActive(false);
        }

        void BuildAutoBannerPlaceholder() { }

        // ---- announcements (kept) --------------------------------------------------------------------
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

        public void Log(string text)
        {
            _log.text = text;
            bool show = !string.IsNullOrEmpty(text) && !text.StartsWith("ROUND ");
            if (_logPanel != null && _logPanel.gameObject.activeSelf != show) _logPanel.gameObject.SetActive(show);
            if (show) FollowEnemyAction(text);
        }
        /// <summary>Adds the battle-speed button (left of 자동) that cycles 1x / 1.5x / 2x.</summary>
        public void EnableSpeedToggle(string label, Action toggle)
        {
            _toggleSpeed = toggle;
            _speedButton = UISlantButton.Create(_root, "Battle speed", new Vector2(150f, 64f), UISlantKind.Simple, true);
            _speedButton.SetLabel(label);
            _speedButton.Clicked += () => { if (!Paused) _toggleSpeed?.Invoke(); };
            LayoutChrome();
        }
        public void SetSpeedLabel(string label) { if (_speedButton != null) _speedButton.SetLabel(label); }
        public void SetAuto(bool value)
        {
            _auto = value; _autoButton.SetLabel(value ? "자동전투 ON" : "자동전투 OFF");
            _autoButton.Focused = value;
            RefreshAutoBanner();
            UpdateOcclusion();
        }
        void ToggleAuto() { if (!Paused) _toggleAuto?.Invoke(); }
        public void Lock()
        {
            // Battle teardown can run after the HUD's panels were destroyed with the UI root.
            _input = false; SetHeroFocus(null); ClearMarks();
            if (_menu != null && _menu.gameObject.activeSelf && !_menuClosing) CloseMenu();
            _preview?.Invoke(null);
            // Reset per-action presentation state: a cancelled action or teardown must never leave tags faded or a
            // cut-in band on the battle clock (Lock runs on new battle, on Finish and in Restore).
            SetTagsHidden(false);
            StopCutIn();
            // A suppressed (not yet seated) phase call-out must not reappear after the battle state was reset.
            CancelCallout();
        }

        /// <summary>
        /// Timed call-out in the top third of the screen: a title line plus an optional subtitle. This only records the content
        /// and its requested lifetime (until <see cref="HideCutIn"/>); the size follows <see cref="LayoutCallout"/> and the seat
        /// is validated every frame by <see cref="UpdateCallout"/>, which keeps it off living hero bodies, party plates, the
        /// top controls and the skill ribbon and suppresses it (retrying while requested) when no such seat exists.
        /// </summary>
        public void CutIn(string title, string text)
        {
            _coTitle = title ?? ""; _coText = text ?? "";
            _coRequested = true;
            HideCalloutPlate();
            LayoutCallout();
        }

        /// <summary>Slides a centred/top panel in from the left with a fade (the skill ribbon arrives, it does not pop).</summary>
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

        /// <summary>Fades a panel in at its current position (call-outs arrive; they never slide across the scene).</summary>
        void FadeIn(RectTransform rt, float duration)
        {
            if (!rt.TryGetComponent(out CanvasGroup group)) group = rt.gameObject.AddComponent<CanvasGroup>();
            group.blocksRaycasts = false;
            UITween.Kill(rt);
            if (UIRoot.Instance != null && UIRoot.Instance.ReducedMotion) { group.alpha = 1f; return; }
            group.alpha = 0f;
            UITween.To(rt, duration, t => group.alpha = t, UIEase.OutCubic);
        }

        /// <summary>Hides the call-out plate (it stays requested, see <see cref="_coRequested"/>) and forgets its seat.</summary>
        void HideCalloutPlate()
        {
            _coShown = false;
            if (_cutin == null) return;
            UITween.Kill(_cutin);
            if (_cutin.gameObject.activeSelf) _cutin.gameObject.SetActive(false);
        }

        /// <summary>Ends the requested call-out for good: nothing pending can show it again.</summary>
        void CancelCallout()
        {
            _coRequested = false; _coRelayout = false;
            HideCalloutPlate();
        }

        public void HideCutIn()
        {
            CancelCallout();
            if (_ult == null || !_ult.gameObject.activeSelf) { StopCutIn(); return; }
            // Signature and ultimate share the battle-clock band (see AdvanceCutIn): start its timed exit, so a pause
            // freezes it and 1.5x / 2x scale it; a band that is not on the clock (stale UI tween) just hides.
            if (HideBandCutIn()) return;
            _ult.gameObject.SetActive(false);
            StopCutIn();
        }

        RectTransform _ult, _ultBand, _ultFace, _ultText;
        CanvasGroup _ultGroup;
        Image _ultFlash, _ultTint, _ultFaceImage, _ultEdgeTop, _ultEdgeBottom;
        TMP_Text _ultActor, _ultSkill;
        readonly List<RectTransform> _ultLines = new List<RectTransform>();

        /// <summary>
        /// Persona / Star Rail style ultimate call-out: a dark band snaps open across the screen, the hero's face
        /// slides in on the left over speed lines in the element colour, and the skill name punches in on the right.
        /// </summary>
        void BuildUltimate()
        {
            _ultCompact = Compact;
            _ult = UIFactory.Rect(_root, "Ultimate cut-in").Stretch();
            _ultGroup = _ult.gameObject.AddComponent<CanvasGroup>();
            _ultGroup.blocksRaycasts = false; _ultGroup.interactable = false;
            _ultFlash = UIFactory.Image(_ult, UISprites.White, Color.clear, "Flash");
            _ultFlash.rectTransform.Stretch();
            _ultBand = UIFactory.Rect(_ult, "Band");
            _ultBand.anchorMin = new Vector2(0f, .5f); _ultBand.anchorMax = new Vector2(1f, .5f);
            _ultBand.sizeDelta = new Vector2(0f, Compact ? 260f : 320f); _ultBand.anchoredPosition = new Vector2(0f, 40f);
            _ultBand.gameObject.AddComponent<RectMask2D>();
            UIFactory.Image(_ultBand, UISprites.White, new Color(.02f, .03f, .09f, .9f), "Fill").rectTransform.Stretch();
            // Element tint strongest behind the face, fading out towards the skill name.
            _ultTint = UIFactory.Image(_ultBand, UISprites.GradientH, Color.white, "Tint");
            _ultTint.rectTransform.Stretch();
            _ultTint.rectTransform.localScale = new Vector3(-1f, 1f, 1f);
            var random = new System.Random(7);
            for (int i = 0; i < 16; i++)
            {
                var line = UIFactory.Image(_ultBand, UISprites.White, Color.white, "Speed line").rectTransform;
                line.anchorMin = line.anchorMax = new Vector2(.5f, .5f);
                line.sizeDelta = new Vector2(240f + (float)random.NextDouble() * 520f, 2f + (float)random.NextDouble() * 4f);
                line.anchoredPosition = new Vector2(0f, ((float)random.NextDouble() - .5f) * _ultBand.sizeDelta.y * .95f);
                _ultLines.Add(line);
            }
            float face = Compact ? 520f : 640f;
            _ultFace = UIFactory.Rect(_ultBand, "Face");
            _ultFace.anchorMin = _ultFace.anchorMax = new Vector2(0f, .5f);
            _ultFace.sizeDelta = new Vector2(face, face);
            _ultFaceImage = UIFactory.Image(_ultFace, null, Color.white, "Portrait");
            _ultFaceImage.rectTransform.Stretch();
            _ultFaceImage.preserveAspect = true;
            _ultText = UIFactory.Rect(_ultBand, "Text");
            _ultText.anchorMin = new Vector2(.36f, 0f); _ultText.anchorMax = new Vector2(1f, 1f);
            _ultText.offsetMin = new Vector2(0f, 0f); _ultText.offsetMax = new Vector2(-60f, 0f);
            _ultActor = UIFactory.Label(_ultText, "", Compact ? 30 : 34, UIFont.Bold, UITheme.Text, TextAlignmentOptions.BottomRight, UITextFx.Outline, "Actor");
            _ultActor.Rt().Stretch(0f, 0f, 0f, _ultBand.sizeDelta.y * .6f);
            _ultSkill = UIFactory.Label(_ultText, "", Compact ? 74 : 92, UIFont.Title, UITheme.GoldBright, TextAlignmentOptions.TopRight, UITextFx.Glow, "Skill");
            _ultSkill.Rt().Stretch(0f, _ultBand.sizeDelta.y * .42f, 0f, 0f);
            _ultSkill.enableAutoSizing = true; _ultSkill.fontSizeMin = 40; _ultSkill.fontSizeMax = _ultSkill.fontSize;
            _ultEdgeTop = Edge(1f); _ultEdgeBottom = Edge(0f);
            _ult.gameObject.SetActive(false);

            Image Edge(float y)
            {
                var edge = UIFactory.Image(_ult, UISprites.GlowLine, UITheme.Gold, y > .5f ? "Top edge" : "Bottom edge");
                edge.rectTransform.anchorMin = new Vector2(0f, .5f); edge.rectTransform.anchorMax = new Vector2(1f, .5f);
                edge.rectTransform.sizeDelta = new Vector2(0f, 8f);
                edge.rectTransform.anchoredPosition = new Vector2(0f, 40f + (y - .5f) * _ultBand.sizeDelta.y);
                return edge;
            }
        }

        /// <summary>Drops the ultimate cut-in built for the other layout mode; the next call-out rebuilds it.</summary>
        void DiscardUltimate()
        {
            UITween.Kill(_ult);
            _ult.gameObject.SetActive(false);
            Destroy(_ult.gameObject);
            _ult = null; _ultLines.Clear();
        }

        /// <summary>Plays the hero ultimate call-out (same battle-clock band as a signature); <see cref="HideCutIn"/> fades it out.</summary>
        public void UltimateCutIn(string heroId, string actor, string skill, Color accent)
            => PlayCutIn(false, heroId, actor, skill, accent);

        // No modal layer and no full-screen raycast: this bounded toast is owned by the locked battle HUD.
        public void FastRewards(BattleReport report, Action confirmed)
        {
            Lock(); HideSkillBanner(); HideEnemyTurn();
            if (_announce != null) { UITween.Kill(_announce); _announce.gameObject.SetActive(false); }
            _autoButton.gameObject.SetActive(false);
            if (_speedButton != null) _speedButton.gameObject.SetActive(false);
            if (_autoBanner != null) _autoBanner.gameObject.SetActive(false);
            if (_logPanel != null) _logPanel.gameObject.SetActive(false);
            _fastToast = UIFactory.Panel(_root, UIPanelStyle.Dark, false, "Fast battle result").Rect;
            _fastSummary = UIFactory.Label(_fastToast, $"승리 · {report.Gold:N0}만원 · EXP +{report.Experience:N0} · 전리품 {PositiveDropCount(report)}종", 26, UIFont.Bold, UITheme.Positive, name: "Fast result summary");
            _fastSummary.overflowMode = TextOverflowModes.Ellipsis;
            _fastExtra = UIFactory.Label(_fastToast, "", 22, color: UITheme.Text, name: "Fast result progress");
            _fastExtra.overflowMode = TextOverflowModes.Ellipsis;
            _fastExtra.text = report.NewWeaknesses.Count > 0 || report.QuestUpdates.Count > 0
                ? $"새 약점 {report.NewWeaknesses.Count}개 · 의뢰 진행 {report.QuestUpdates.Count}건 · 기록 저장 완료"
                : "기록 저장 완료 · 탭 / 확인으로 계속";
            var tap = _fastToast.gameObject.AddComponent<UnityEngine.UI.Button>();
            tap.transition = UnityEngine.UI.Selectable.Transition.None;
            tap.navigation = new UnityEngine.UI.Navigation { mode = UnityEngine.UI.Navigation.Mode.None };
            tap.onClick.AddListener(() => { if (_fastArmed && _fastElapsed >= .15f) AcknowledgeFastResults(); });
            _fastConfirmed = confirmed; _fastElapsed = 0; _fastArmed = false; _fastAnswered = false;
            _fastOpenedFrame = Time.frameCount; UIInput.Consume();
            LayoutFastToast();
        }
        static int PositiveDropCount(BattleReport report)
        { int count = 0; foreach (var drop in report.Drops) if (drop.Value > 0) count++; return count; }
        void LayoutFastToast()
        {
            float width = Mathf.Min(1000f, _root.rect.width - 44f);
            _fastToast.Place(UIAnchor.Bottom, new Vector2(0, Compact ? 230 : 300), new Vector2(width, 110));
            _fastSummary.Rt().TopStrip(40, 10, 22, 22);
            _fastExtra.Rt().BottomStrip(36, 16, 22, 22);
        }
        static bool ResultInputHeld => UIInput.ConfirmHeld
            || (UnityEngine.InputSystem.Keyboard.current?.numpadEnterKey.isPressed ?? false)
            || (UnityEngine.InputSystem.Mouse.current?.leftButton.isPressed ?? false);
        void AcknowledgeFastResults()
        {
            if (_fastAnswered || _fastToast == null || Paused || !UIInput.CanReceive(_root)) return;
            _fastAnswered = true; UIInput.Consume();
            _fastToast.gameObject.SetActive(false);
            var confirmed = _fastConfirmed; _fastConfirmed = null;
            confirmed?.Invoke();
        }

        public void Rewards(BattleOutcome outcome, Abyss.Logic.Game.BattleReport report, Action confirmed)
        {
            Lock(); HideSkillBanner(); HideEnemyTurn();
            if (_logPanel != null) _logPanel.gameObject.SetActive(false);
            _autoButton.gameObject.SetActive(false);
            if (_autoBanner != null) _autoBanner.gameObject.SetActive(false);
            if (_speedButton != null) _speedButton.gameObject.SetActive(false);
            _reward = UIFactory.Rect(_root, "Battle result").Stretch();
            UIFactory.Fill(_reward, UITheme.Ink.WithAlpha(0.8f), raycast: true);
            var panel = UIFactory.Panel(_reward, UIPanelStyle.Ornate, name: "Result dashboard");
            bool victory = outcome.Result == BattleResult.Victory;
            var panelSize = new Vector2(1240, 800);
            panel.Rect.Place(UIAnchor.Center, Vector2.zero, panelSize);
            bool reduced = UIRoot.Instance != null && UIRoot.Instance.ReducedMotion;
            panel.Rect.localScale = Vector3.one * (reduced ? 1f : 0.98f);
            UITween.Scale(panel.Rect, 1f, reduced ? 0f : 0.2f, UIEase.OutCubic);
            string heading = victory ? "전투 승리" : outcome.Result == BattleResult.Defeat ? "다시 준비할 시간" : "전투에서 벗어났습니다";
            // Victory plate: ribbon band + glowing title, the beat every console JRPG lands before the spoils.
            var ribbon = UIFactory.Image(panel.Rect, UISprites.Ribbon, Color.white, "Title ribbon");
            ribbon.rectTransform.Place(UIAnchor.Top, new Vector2(0, -8), new Vector2(760, 92));
            UIFactory.Label(panel.Rect, heading, 52, UIFont.Title, victory ? UITheme.GoldBright : UITheme.Text, TextAlignmentOptions.Center,
                victory ? UITextFx.Glow : UITextFx.Outline).Rt().TopStrip(72, 18, 36, 36);
            UIFactory.Label(panel.Rect, victory
                    ? $"{UITheme.Tag(UITheme.GoldBright)}{report.Gold:N0}만원</color>   <size=20>획득 보상금</size>        {UITheme.Tag(UITheme.Positive)}EXP +{report.Experience:N0}</color>   <size=20>생존 동료</size>"
                    : "전투 결과와 탐험 기록을 확인하세요.",
                26, UIFont.Heavy, UITheme.Text, TextAlignmentOptions.Center).Rt().TopStrip(36, 96, 36, 36);
            if (victory) BuildPartyResults(panel.Rect, panelSize.x, report, outcome);
            var growth = UIFactory.Panel(panel.Rect, UIPanelStyle.Dark, false, "Progression card");
            growth.Rect.Place(UIAnchor.TopLeft, new Vector2(32, -260), new Vector2(444, 426));
            UIFactory.Label(growth.Rect, "성장과 탐험 기록", 27, UIFont.Title, UITheme.GoldBright).Rt().TopStrip(46, 12, 22, 22);
            _rewardScroll = UIFactory.ScrollView(growth.Rect, out var rewardContent, name: "Result progression");
            _rewardScroll.Rt().Stretch(22, 70, 22, 20);
            _text.Clear();
            if (!victory) _text.Append(outcome.Result == BattleResult.Defeat ? "파티가 쓰러졌습니다. 길드에서 재정비하세요.\n" : "전투에서 벗어났습니다.\n");
            AppendProgression(report);
            if (_text.Length == 0) _text.Append("탐험 기록이 저장되었습니다.\n다음 모험을 이어가세요.");
            _rewardText = UIFactory.Paragraph(rewardContent, _text.ToString(), 24);
            _rewardText.overflowMode = TextOverflowModes.Overflow;

            var loot = UIFactory.Panel(panel.Rect, UIPanelStyle.Dark, false, "Loot collection");
            loot.Rect.Place(UIAnchor.TopRight, new Vector2(-32, -260), new Vector2(714, 426));
            int rareCount = 0;
            foreach (var drop in report.Drops) if (drop.Value > 0 && DropRarity(drop.Key) >= 1) rareCount++;
            UIFactory.Label(loot.Rect, rareCount > 0 ? $"희귀 이상 전리품 발견! · {rareCount}종" : "획득한 전리품", 27, UIFont.Title,
                rareCount > 0 ? UITheme.RarityColor(1) : UITheme.GoldBright).Rt().TopStrip(46, 12, 22, 22);
            var drops = new List<KeyValuePair<string, int>>();
            foreach (var drop in report.Drops) if (drop.Value > 0) drops.Add(drop);
            drops.Sort((a, b) => { int rarity = DropRarity(b.Key).CompareTo(DropRarity(a.Key)); return rarity != 0 ? rarity : string.CompareOrdinal(a.Key, b.Key); });
            var cards = UIFactory.Rect(loot.Rect, "Loot page").Stretch(18, 70, 18, 48);
            _rewardCounter = UIFactory.Label(loot.Rect, "", 21, color: UITheme.TextDim, align: TextAlignmentOptions.Center);
            _rewardCounter.Rt().BottomStrip(32, 8, 130, 130);
            int page = 0;
            Action refresh = () =>
            {
                for (int i = cards.childCount - 1; i >= 0; i--) { var old = cards.GetChild(i).gameObject; old.SetActive(false); Destroy(old); }
                int start = page * 6;
                if (drops.Count == 0) UIFactory.Paragraph(cards, victory ? "획득한 물품이 없습니다." : "보상금·EXP·아이템 보상은 없습니다.", 25).Rt().Stretch(18, 20, 18, 20);
                for (int i = start; i < Math.Min(drops.Count, start + 6); i++)
                {
                    string id = drops[i].Key;
                    int rarity = DropRarity(id), index = i - start;
                    var accent = UITheme.RarityColor(rarity);
                    var card = UIFactory.Panel(cards, UIPanelStyle.Glass, false, "Drop " + id);
                    card.Rect.Place(UIAnchor.TopLeft, new Vector2((index % 2) * 342, -(index / 2) * 100), new Vector2(330, 90));
                    var stripe = UIFactory.Image(card.Rect, UISprites.PanelWhite, accent, "Rarity stripe");
                    stripe.Rt().Place(UIAnchor.Left, new Vector2(0, 0), new Vector2(4, 70));
                    if (rarity > 0)
                    {
                        // Rare and better drops glow in their rarity colour so the eye finds them first.
                        var halo = UIFactory.Image(card.Rect, UISprites.SoftRadial, accent.WithAlpha(0.22f + 0.1f * rarity), "Rarity glow");
                        halo.rectTransform.Place(UIAnchor.Left, new Vector2(-6, 0), new Vector2(110, 110));
                        UIFactory.Image(card.Rect, UISprites.PanelOutline, accent.WithAlpha(0.75f), "Rarity edge").rectTransform.Stretch();
                    }
                    bool knownItem = _db.Items.ContainsKey(id), knownGear = _db.Equipment.ContainsKey(id);
                    var icon = UIFactory.Icon(card.Rect, knownItem ? UIArtwork.Item(id) : knownGear ? UIArtwork.Gear(id) : UIArtwork.Command("item"), 54);
                    icon.Rt().Place(UIAnchor.Left, new Vector2(14, 0), new Vector2(54, 54));
                    string name = _db.Items.TryGetValue(id, out var item) ? item.DisplayName : knownGear ? _db.Equipment[id].DisplayName : id;
                    var label = UIFactory.Label(card.Rect, name, 23, color: UITheme.Text);
                    label.Rt().TopStrip(36, 12, 82, 16); label.overflowMode = TextOverflowModes.Ellipsis;
                    string category = item != null ? UITheme.ItemCategory(item.ItemType) : "장비";
                    UIFactory.Label(card.Rect, $"{UITheme.RarityName(rarity)} · {category}   ×{drops[i].Value}", 20, color: accent).Rt().BottomStrip(30, 12, 82, 16);
                    // Every card can reveal its complete name and description, even if the grid title is truncated.
                    var hit = card.gameObject.AddComponent<UnityEngine.UI.Button>();
                    hit.transition = UnityEngine.UI.Selectable.Transition.None;
                    hit.navigation = new Navigation { mode = Navigation.Mode.None };
                    string description = item != null ? item.Description : knownGear ? _db.Equipment[id].Description : "물품 정보를 확인할 수 없습니다.";
                    hit.onClick.AddListener(() => { if (!Paused) UIModal.Alert(UIRoot.Instance.Modals, name, $"{UITheme.RarityName(rarity)} · {category}\n\n{description}"); });
                    if (!reduced)
                    {
                        // Spoils drop in one after another (rare ones with a bigger pop) instead of appearing as a sheet.
                        var group = card.gameObject.AddComponent<CanvasGroup>();
                        group.alpha = 0f;
                        var rt = card.Rect;
                        float from = rarity > 0 ? 1.25f : 1.1f;
                        rt.localScale = Vector3.one * from;
                        UITween.To(rt, .22f, t => { group.alpha = t; rt.localScale = Vector3.one * Mathf.Lerp(from, 1f, t); },
                            rarity > 0 ? UIEase.OutBack : UIEase.OutCubic, .25f + index * .08f);
                    }
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
                int heroXp = report.ExperienceByHero.TryGetValue(card.Unit.DefId, out int gained) ? gained : report.Experience;
                string summary = finalHp > 0 ? $"EXP +{heroXp:N0}" : "전투불능 · EXP 없음";
                foreach (var level in report.LevelUps) if (level.HeroId == card.Unit.DefId) summary = $"Lv.{level.OldLevel} → {level.NewLevel}  성장!";
                var label = UIFactory.Label(slot, summary, 20, color: finalHp > 0 ? UITheme.Positive : UITheme.TextDisabled);
                label.Rt().BottomStrip(36, 12, 88, 12); label.overflowMode = TextOverflowModes.Ellipsis;
            }
        }

        void AppendProgression(Abyss.Logic.Game.BattleReport report)
        {
            if (report.LevelUps.Count > 0) _text.Append("\n<b>헌터의 성장</b>\n");
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
                _text.Append(update.Completed ? " · 완료!\n길드 접수처에서 보상을 받으세요.\n" : " · 진행 중\n");
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
            if (_fastToast != null)
            {
                if (_fastAnswered) return;
                // Timings are real pause-aware seconds, never multiplied by the battle-speed preference.
                _fastElapsed += Time.unscaledDeltaTime;
                if (Time.frameCount != _fastOpenedFrame && !ResultInputHeld) _fastArmed = true;
                if (_fastElapsed >= 2f || (_fastArmed && _fastElapsed >= .15f && UIInput.Advance)) AcknowledgeFastResults();
                return;
            }
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
            int movement = UIInput.NavigateRows;
            if (movement != 0) { Focus(_focus + movement); UIInput.Consume(); }
            else if (UIInput.Navigate.x != 0)
            {
                Page(UIInput.Navigate.x); UIInput.Consume();
            }
            else if (UIInput.TabNext || UIInput.TabPrev)
            { Page(UIInput.TabPrev ? -1 : 1); UIInput.Consume(); }
            else if (UIInput.Cancel && _back != null) { Back(); UIInput.Consume(); }
            else if (UIInput.Confirm && _choices.Count > 0) { Select(_page * PerPage + _focus); UIInput.Consume(); }
        }
        void LateUpdate()
        {
            if (_root == null) return;
            UpdateTags();
            PulseRings();
            UpdateOcclusion();
        }
        void OnDestroy() { if (_root != null) Destroy(_root.gameObject); }
    }
}
