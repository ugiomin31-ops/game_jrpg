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
    }
}
