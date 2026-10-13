using Abyss.Logic.Battle;
using Abyss.Runtime.Battle;
using TMPro;
using UnityEngine;
using UnityEngine.UI;

namespace Abyss.UI.Battle
{
    public sealed partial class BattleHUD
    {
        UISlantPlate _enemyBannerPlate, _bannerPlate;
        TMP_Text _enemyBannerTitle;
        Image _bannerAccent;
        string _enemyTurnId, _enemyAction, _enemyTarget;

        /// <summary>
        /// Enemy-turn call-out in the top band: red-coral threat palette (the one place it is allowed), "적 행동" tag, the
        /// announced action and its target. The threatened hero plates are raised and edged in the same palette.
        /// </summary>
        void BuildEnemyBanner()
        {
            _enemyBanner = UIFactory.Rect(_root, "Enemy turn banner");
            _enemyBannerPlate = UISlantPlate.Create(_enemyBanner, "Plate", UISlant.ThreatFill, UISlant.Threat, 3f, true, 6f, true);
            _enemyBannerPlate.Rect.Stretch();
            var chip = UISlant.Pill(_enemyBanner, "Caption", UISlant.Threat, new Color(1f, 0.82f, 0.85f, 1f), out var tag, 28f);
            tag.text = "적 행동";
            chip.Rect.Place(UIAnchor.Left, new Vector2(20f, 0f), new Vector2(128f, 42f));
            _enemyBannerTitle = UIFactory.Label(_enemyBanner, "", 34, UIFont.Heavy, UITheme.Text, TextAlignmentOptions.MidlineLeft, UITextFx.Outline, "Action");
            _enemyBannerTitle.rectTransform.Stretch(166f, 2f, 24f, 2f);
            _enemyBannerTitle.overflowMode = TextOverflowModes.Ellipsis;
            _enemyBannerTitle.enableAutoSizing = true; _enemyBannerTitle.fontSizeMin = 26f; _enemyBannerTitle.fontSizeMax = 34f;
            _enemyBanner.gameObject.SetActive(false);
        }

        void ShowEnemyTurn(Card actor)
        {
            var unit = actor.Unit;
            _enemyTurnId = unit.Id;
            var pending = unit.DisplayCharge; var next = unit.LeadingIntent;
            if (pending != null || next != null)
            {
                string skillId = pending?.SkillId ?? next.SkillId;
                ActionKind kind = pending != null ? ActionKind.Skill : next.Kind;
                bool charge = pending != null || next.IsChargeAnnounce || next.IsChargeRelease;
                _enemyAction = (charge ? "준비 중! " : "") + IntentAction(kind, skillId);
                _enemyTarget = IntentTarget(pending?.Scope ?? next.Scope, pending != null ? pending.TargetUnitId : next.TargetUnitId);
            }
            else { _enemyAction = unit.Name; _enemyTarget = null; }
            RefreshEnemyBanner();
            foreach (var card in _cards.Values)
                if (card.Party) card.EnemyThreat = card.Unit.Alive && WarnsHero(unit, card.Unit.Id);
            RefreshPlateStates();
            if (!_enemyBanner.gameObject.activeSelf)
            {
                _enemyBanner.gameObject.SetActive(true);
                Arrive(_enemyBanner, 0f, _enemyBannerHome);
            }
        }

        void RefreshEnemyBanner() =>
            _enemyBannerTitle.text = _enemyAction + (string.IsNullOrEmpty(_enemyTarget) ? "" : "  <size=80%>→</size>  " + _enemyTarget);

        public void HideEnemyTurn()
        {
            _enemyTurnId = null;
            if (_enemyBanner != null && _enemyBanner.gameObject.activeSelf) _enemyBanner.gameObject.SetActive(false);
            bool any = false;
            foreach (var card in _cards.Values) if (card.EnemyThreat) { card.EnemyThreat = false; any = true; }
            if (any) RefreshPlateStates();
        }

        /// <summary>The replay names the real action ("이름 · 행동"): the banner follows it.</summary>
        void FollowEnemyAction(string text)
        {
            if (_enemyTurnId == null || !_cards.TryGetValue(_enemyTurnId, out var card)) return;
            string prefix = card.Unit.Name + " · ";
            if (!text.StartsWith(prefix, System.StringComparison.Ordinal)) return;
            _enemyAction = text.Substring(prefix.Length);
            RefreshEnemyBanner();
        }

        // ---- auto battle notice ---------------------------------------------------------------------

        /// <summary>
        /// Shown at the command fan's position while automatic battle owns party decisions, so the missing command
        /// window is explained and manual control is one tap away. Switching off takes effect at the next decision.
        /// </summary>
        void BuildAutoBanner()
        {
            var plate = UISlantPlate.Create(_root, "Auto battle notice", UISlant.Navy, UISlant.Rest, 2f, true, 5f, false);
            _autoBanner = plate.Rect;
            _autoBannerTitle = UIFactory.Label(plate.Rect, "자동전투 진행 중", 30, UIFont.Heavy, UITheme.Text, TextAlignmentOptions.MidlineLeft, UITextFx.Outline, "Title");
            _autoBannerTitle.overflowMode = TextOverflowModes.Ellipsis;
            _manualButton = UISlantButton.Create(plate.Rect, "Manual control", new Vector2(180f, 56f), UISlantKind.Simple, true);
            _manualButton.SetLabel("직접 조작");
            _manualButton.Clicked += ManualControl;
            _autoBanner.gameObject.SetActive(false);
        }

        void ManualControl() { if (!Paused && _auto) _toggleAuto?.Invoke(); }

        void RefreshAutoBanner()
        {
            if (_autoBanner == null) return;
            bool show = _auto && _reward == null && _fastToast == null;
            if (_autoBanner.gameObject.activeSelf != show) _autoBanner.gameObject.SetActive(show);
        }

        // ---- skill ribbon ---------------------------------------------------------------------------

        /// <summary>Slanted ribbon that names the skill while it resolves, edged and tinted in the element colour.</summary>
        void BuildSkillRibbon()
        {
            _bannerPlate = UISlantPlate.Create(_root, "Skill ribbon", new Color(0.04f, 0.08f, 0.13f, 1f), UITheme.Gold, 3f, true, 6f, true);
            _banner = _bannerPlate.Rect;
            _bannerAccent = UIFactory.Image(_banner, UISprites.White, UISlant.Coral, "Accent");
            _bannerAccent.gameObject.AddComponent<UISkew>();
            _bannerAccent.rectTransform.Place(UIAnchor.Left, new Vector2(10f, 0f), new Vector2(10f, 44f));
            _bannerText = UIFactory.Label(_banner, "", 40, UIFont.Title, UITheme.Text, TextAlignmentOptions.Center, UITextFx.Heavy, "Skill name");
            _bannerText.rectTransform.Stretch(34f, 4f, 24f, 4f);
            _bannerText.overflowMode = TextOverflowModes.Ellipsis;
            _banner.gameObject.SetActive(false);
        }

        /// <summary>JRPG skill-name ribbon shown while a skill or item resolves (tinted by its element / light colour).</summary>
        public void SkillBanner(string text, Color color)
        {
            if (_banner == null) return;
            _bannerText.text = text; _bannerText.color = Color.Lerp(Color.white, color, .25f);
            _bannerPlate.SetColors(new Color(0.04f, 0.08f, 0.13f, 1f), Color.Lerp(UITheme.Gold, color, .75f));
            _bannerAccent.color = color;
            _banner.gameObject.SetActive(true);
            // The ribbon names the skill; the action line would only repeat it.
            if (_logPanel != null) _logPanel.gameObject.SetActive(false);
            SlideIn(_banner, 260f, 0.18f);
        }

        public void HideSkillBanner() { if (_banner != null) _banner.gameObject.SetActive(false); }

        // ---- signature / ultimate cut-in ------------------------------------------------------------

        /// <summary>
        /// Slanted portrait band for a hero's signature technique or ultimate (hero portrait sliding in, big slanted TMP
        /// skill name punching in, speed lines). The band runs on the battle clock (see <see cref="AdvanceCutIn"/>), so a
        /// pause freezes the entrance, drift and exit and 1.5x / 2x scale them with the battle; the view holds it shorter
        /// for a signature than for an ultimate and never shows a signature under reduced motion. Hide with <see cref="HideCutIn"/>.
        /// </summary>
        /// <param name="signature">True: caption as the hunter's signature technique; false: an ultimate call-out.</param>
        public void PlayCutIn(bool signature, string heroId, string actor, string skill, Color accent)
        {
            if (_ult != null && _ultCompact != Compact) DiscardUltimate();
            if (_ult == null) BuildUltimate();
            UITween.Kill(_ult);
            _ult.gameObject.SetActive(true);
            _ult.SetAsLastSibling();
            _ultGroup.alpha = 1f;
            _ultFaceImage.sprite = UIArtwork.Hero(heroId);
            _ultActor.text = signature ? actor + "  ·  시그니처" : actor;
            _ultSkill.text = skill;
            _ultSkill.color = Color.Lerp(UITheme.GoldBright, accent, .25f);
            _ultTint.color = new Color(accent.r, accent.g, accent.b, .55f);
            _ultEdgeTop.color = _ultEdgeBottom.color = Color.Lerp(UITheme.Gold, accent, .5f);
            Color lineColor = Color.Lerp(Color.white, accent, .4f);
            for (int i = 0; i < _ultLines.Count; i++)
                _ultLines[i].GetComponent<Image>().color = new Color(lineColor.r, lineColor.g, lineColor.b, .18f + .3f * ((i * 37) % 10) / 10f);
            _bandTime = 0f; _bandExit = -1f;
            ApplyCutIn(0f);
        }

        // Band timeline in battle seconds (the same beats as the old per-tween UI: .14 snap, .24 face slide, .26 name punch,
        // .32 lines), advanced by the view with the battle clock. -1 means no band is showing. Menus keep UITween time.
        float _bandTime = -1f, _bandExit = -1f;
        const float BandExitTime = .16f;

        /// <summary>Advances the cut-in band by <paramref name="dt"/> battle seconds (no-op when none is showing).</summary>
        public void AdvanceCutIn(float dt)
        {
            if (_bandTime < 0f) return;
            if (_ult == null || !_ult.gameObject.activeSelf) { StopCutIn(); return; }
            _bandTime += Mathf.Max(0f, dt);
            ApplyCutIn(_bandTime);
        }

        /// <summary>Starts the timed exit of a showing band; false when none is (the caller hides an ultimate / the boss call-out).</summary>
        bool HideBandCutIn()
        {
            if (_bandTime < 0f) return false;
            if (_bandExit < 0f) _bandExit = _bandTime;
            return true;
        }

        /// <summary>Clears the band state and hides the band (action cancelled, new battle or battle teardown): never leaves a frozen cut-in.</summary>
        public void StopCutIn()
        {
            _bandTime = -1f; _bandExit = -1f;
            if (_ult != null && _ult.gameObject.activeSelf) _ult.gameObject.SetActive(false);
        }

        void ApplyCutIn(float t)
        {
            float E(UIEase ease, float start, float duration) => UITween.Evaluate(ease, Mathf.Clamp01((t - start) / duration));
            float width = _root.rect.width > 0f ? _root.rect.width : 2000f;
            float faceX = Compact ? 250f : 330f, faceIn = -_ultFace.sizeDelta.x * .5f;
            // Band snaps open from a line with a white-hot flash; edges draw outward.
            _ultBand.localScale = new Vector3(1f, E(UIEase.OutCubic, 0f, .14f), 1f);
            float edge = E(UIEase.OutCubic, 0f, .22f);
            _ultEdgeTop.rectTransform.localScale = _ultEdgeBottom.rectTransform.localScale = new Vector3(edge, 1f, 1f);
            _ultFlash.color = new Color(1f, 1f, 1f, .45f * (1f - E(UIEase.OutQuad, 0f, .3f)));
            // Portrait slides in, then keeps drifting so the shot never freezes.
            float face = t < .28f ? Mathf.Lerp(faceIn, faceX, E(UIEase.OutCubic, .04f, .24f)) : faceX + 40f * Mathf.Clamp01((t - .28f) / 1.2f);
            _ultFace.anchoredPosition = new Vector2(face, -50f);
            // Name lines punch in from the right.
            float slide = E(UIEase.OutCubic, .1f, .22f);
            _ultText.anchoredPosition = new Vector2(500f * (1f - slide), 0f);
            _ultActor.alpha = slide;
            float punch = E(UIEase.OutBack, .16f, .26f);
            _ultSkill.transform.localScale = Vector3.one * Mathf.LerpUnclamped(1.35f, 1f, punch);
            _ultSkill.alpha = Mathf.Clamp01((t - .16f) / .26f);
            for (int i = 0; i < _ultLines.Count; i++)
            {
                var line = _ultLines[i];
                float span = width * .5f + line.sizeDelta.x;
                float u = Mathf.Clamp01((t - (i % 8) * .07f) / (.32f + (i % 4) * .06f));
                line.anchoredPosition = new Vector2(Mathf.Lerp(span, -span, u), line.anchoredPosition.y);
            }
            float alpha = 1f;
            if (_bandExit >= 0f)
            {
                float u = Mathf.Clamp01((t - _bandExit) / BandExitTime);
                alpha = 1f - UITween.Evaluate(UIEase.InQuad, u);
                if (u >= 1f) { _ult.gameObject.SetActive(false); StopCutIn(); }
            }
            _ultGroup.alpha = alpha;
        }
    }
}
