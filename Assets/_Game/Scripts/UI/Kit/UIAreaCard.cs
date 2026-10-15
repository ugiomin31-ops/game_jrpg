using System;
using System.Collections.Generic;
using TMPro;
using UnityEngine;
using UnityEngine.UI;

namespace Abyss.UI
{
    /// <summary>What an <see cref="UIAreaCard"/> shows once the screen is covered (built after the world swap).</summary>
    public sealed class UIAreaCardInfo
    {
        /// <summary>Small cyan line above the title ("NOW ENTERING").</summary>
        public string Eyebrow = "NOW ENTERING";
        /// <summary>Numeric floor label drawn dark on the band ("1-3"); empty for none.</summary>
        public string Label = "";
        /// <summary>Area name, large and white on the band.</summary>
        public string Name = "";
        /// <summary>One or two lines of description under the band (optional).</summary>
        public string Line = "";
        /// <summary>Giant watermark behind everything (optional).</summary>
        public string Ghost = "";
        /// <summary>Town variant: cyan band with dark lettering instead of coral.</summary>
        public bool Town;
        /// <summary>Slanted info chips under the description: text + edge colour.</summary>
        public readonly List<KeyValuePair<string, Color>> Chips = new List<KeyValuePair<string, Color>>();

        /// <summary>Adds a chip (ignored when <paramref name="text"/> is empty).</summary>
        public UIAreaCardInfo Chip(string text, Color edge)
        {
            if (!string.IsNullOrEmpty(text)) Chips.Add(new KeyValuePair<string, Color>(text, edge));
            return this;
        }
    }

    /// <summary>
    /// Area / floor transition card: a slanted night plate with coral and cyan blades sweeps over the screen, the
    /// caller swaps the world while it is covered, the band shows "NOW ENTERING · 1-3 변전실", then everything sweeps
    /// off to the right. About 1.4 s; a tap / confirm skips the hold. Reduced motion: plain fade with the same text.
    /// Input (world and UI) is blocked only while the screen is covering or covered, never during the reveal.
    /// </summary>
    public sealed class UIAreaCard : MonoBehaviour
    {
        enum Phase { Idle, In, Hold, Out }

        /// <summary>Band centre above the screen centre (in 720-line units) and its tilt.</summary>
        const float BandRaise = 32f, BandTilt = 8f;
        const float InTime = 0.3f, HoldTime = 0.85f, OutTime = 0.32f, MinHold = 0.12f;
        const float ReducedIn = 0.16f, ReducedHold = 0.75f, ReducedOut = 0.2f;

        static UIAreaCard _instance;

        RectTransform _root, _cover, _band, _text;
        CanvasGroup _group, _textGroup;
        Image _blocker, _bandFill, _barFill;
        TextMeshProUGUI _ghost;
        Phase _phase;
        float _t, _coverWidth, _bandTravel;
        bool _reduced, _skip;
        Func<UIAreaCardInfo> _info;
        Action _covered, _finished;
        readonly List<Anim> _anims = new List<Anim>();
        readonly List<GameObject> _bandText = new List<GameObject>();

        struct Anim
        {
            public RectTransform Rect;
            public CanvasGroup Group;
            public Vector2 Home, From;
            public float Delay, Duration;
        }

        /// <summary>True while the card covers (or is covering) the screen: world input and the pause menu wait.</summary>
        public static bool Blocking => _instance != null && (_instance._phase == Phase.In || _instance._phase == Phase.Hold);

        /// <summary>True from the start of the sweep-in to the end of the sweep-out.</summary>
        public static bool Active => _instance != null && _instance._phase != Phase.Idle;

        /// <summary>
        /// Covers the screen, runs <paramref name="covered"/> (swap worlds / rebuild HUD there), shows the card built by
        /// <paramref name="info"/> (evaluated after <paramref name="covered"/>, so it reads the new state), then reveals.
        /// <paramref name="finished"/> runs when the reveal completes. Outside Play mode both run immediately.
        /// </summary>
        public static void Play(Func<UIAreaCardInfo> info, Action covered, Action finished = null)
        {
            var root = UIRoot.Instance;
            if (!Application.isPlaying || root == null)
            {
                covered?.Invoke();
                finished?.Invoke();
                return;
            }
            if (_instance == null) _instance = Create(root);
            _instance.Begin(info, covered, finished);
        }

        static UIAreaCard Create(UIRoot root)
        {
            var rt = UIFactory.Rect(root.transform, "Area Card");
            rt.Stretch();
            var card = rt.gameObject.AddComponent<UIAreaCard>();
            card._root = rt;
            card._group = rt.gameObject.AddComponent<CanvasGroup>();
            card._blocker = UIFactory.Fill(rt, Color.clear, "Input blocker", raycast: true);
            rt.gameObject.SetActive(false);
            return card;
        }

        void Begin(Func<UIAreaCardInfo> info, Action covered, Action finished)
        {
            if (_phase == Phase.Hold)
            {
                // Already covered (a transition chained inside another): swap right away and restart the hold.
                var previous = _finished;
                _finished = () => { previous?.Invoke(); finished?.Invoke(); };
                _info = info;
                RunCovered(covered);
                _t = 0f;
                return;
            }
            if (_phase == Phase.In)
            {
                // Still sweeping in: settle the pending swap first, then continue the sweep with both swaps queued.
                var pending = _covered;
                _covered = () => { pending?.Invoke(); covered?.Invoke(); };
                var previous = _finished;
                _finished = () => { previous?.Invoke(); finished?.Invoke(); };
                _info = info;
                return;
            }
            if (_phase == Phase.Out) EndNow();
            _info = info; _covered = covered; _finished = finished;
            _reduced = UIRoot.Instance != null && UIRoot.Instance.ReducedMotion;
            _skip = false;
            _root.SetAsLastSibling();
            // Keep the generic fader above the card.
            if (UIRoot.Instance != null && UIRoot.Instance.Fader != null) UIRoot.Instance.Fader.transform.SetAsLastSibling();
            _root.gameObject.SetActive(true);
            BuildFrame();
            _blocker.raycastTarget = true;
            UIInput.PushLayer(_root);
            UIRoot.Instance?.Tooltip.Hide();
            _phase = Phase.In; _t = 0f;
            _group.alpha = _reduced ? 0f : 1f;
            Apply();
        }

        // ---- construction -------------------------------------------------------------------------------

        float Unit => Mathf.Max(1f, _root.rect.height) / 720f;

        void BuildFrame()
        {
            for (int i = _root.childCount - 1; i >= 0; i--)
            {
                var child = _root.GetChild(i);
                if (child != _blocker.transform) Destroy(child.gameObject);
            }
            _anims.Clear(); _bandText.Clear();
            float u = Unit, w = _root.rect.width, h = _root.rect.height;
            float overshoot = h * 0.5f * UISkew.Slope + 80f * u;
            _coverWidth = w + overshoot * 2f;

            _cover = UIFactory.Rect(_root, "Cover");
            _cover.Place(UIAnchor.Center, Vector2.zero, new Vector2(_coverWidth, h + 40f));
            var fill = UIFactory.Image(_cover, UISprites.White, UISlant.Night, "Night");
            fill.rectTransform.Stretch();
            fill.gameObject.AddComponent<UISkew>();
            Blade(_cover, "Lead blade", true, 26f * u, 10f * u, UISlant.Coral);
            Blade(_cover, "Lead line", true, 7f * u, 46f * u, UISlant.Cyan);
            Blade(_cover, "Tail blade", false, 14f * u, 10f * u, UISlant.Cyan);
            _ghost = UIFactory.Label(_cover, "", 260f * u, UIFont.Heavy, UISlant.Band, TextAlignmentOptions.TopRight, UITextFx.Plain, "Ghost");
            _ghost.rectTransform.Place(UIAnchor.Center, new Vector2(1f, 1f), new Vector2(w * 0.5f - 40f * u, h * 0.5f - 30f * u), new Vector2(w, 300f * u));

            _band = UIFactory.Rect(_root, "Band");
            _band.Place(UIAnchor.Center, new Vector2(0f, BandRaise * u), new Vector2(w + 900f * u, 230f * u));
            _band.localEulerAngles = new Vector3(0f, 0f, BandTilt);
            _bandTravel = w + 900f * u;
            var top = UIFactory.Image(_band, UISprites.White, UISlant.Paper, "Top rule");
            top.rectTransform.Place(UIAnchor.Top, new Vector2(0f, 30f * u), new Vector2(0f, 6f * u));
            top.rectTransform.anchorMin = new Vector2(0f, 1f); top.rectTransform.anchorMax = new Vector2(1f, 1f);
            _bandFill = UIFactory.Image(_band, UISprites.White, UISlant.Coral, "Fill");
            _bandFill.rectTransform.Stretch();
            var low = UIFactory.Image(_band, UISprites.White, UISlant.Cyan, "Low rule");
            low.rectTransform.Place(UIAnchor.Bottom, new Vector2(0f, -20f * u), new Vector2(0f, 14f * u));
            low.rectTransform.anchorMin = Vector2.zero; low.rectTransform.anchorMax = new Vector2(1f, 0f);

            // Text that does not ride the band lives inside the safe area (notches, rounded corners).
            _text = UIFactory.Rect(_root, "Text");
            var safe = UIRoot.Instance != null ? UIRoot.Instance.SafeArea : null;
            if (safe != null) { _text.anchorMin = safe.anchorMin; _text.anchorMax = safe.anchorMax; _text.offsetMin = _text.offsetMax = Vector2.zero; }
            else _text.Stretch();
            _textGroup = _text.gameObject.AddComponent<CanvasGroup>();
            _textGroup.alpha = 0f;
        }

        /// <summary>A slanted stripe just outside the cover's leading (right) or trailing (left) edge.</summary>
        static void Blade(RectTransform cover, string name, bool lead, float width, float gap, Color color)
        {
            var img = UIFactory.Image(cover, UISprites.White, color, name);
            var r = img.rectTransform;
            float side = lead ? 1f : 0f;
            r.anchorMin = new Vector2(side, 0f); r.anchorMax = new Vector2(side, 1f);
            r.pivot = new Vector2(lead ? 0f : 1f, 0.5f);
            r.sizeDelta = new Vector2(width, 0f);
            r.anchoredPosition = new Vector2(lead ? gap : -gap, 0f);
            img.gameObject.AddComponent<UISkew>();
        }

        void BuildText(UIAreaCardInfo info)
        {
            float u = Unit, w = _text.rect.width > 1f ? _text.rect.width : _root.rect.width;
            float left = 96f * u, rootW = _root.rect.width;
            bool town = info.Town;
            _bandFill.color = town ? UISlant.Cyan : UISlant.Coral;
            _ghost.text = info.Ghost ?? "";

            var eyebrow = UISlant.Eyebrow(_text, info.Eyebrow ?? "", 22f * u, town ? UISlant.Paper : UISlant.Cyan, 40f, "Eyebrow");
            eyebrow.rectTransform.Place(UIAnchor.TopLeft, new Vector2(left, -150f * u), new Vector2(w - left * 2f, 34f * u));
            Track(eyebrow.rectTransform, new Vector2(-40f * u, 0f), 0f, 0.22f);

            // Label + name ride the band (rotated with it). The band's local x = 0 is the screen centre.
            float x = -rootW * 0.5f + left + SafeLeft() + 14f * u;
            if (!string.IsNullOrEmpty(info.Label))
            {
                var label = UIFactory.Label(_band, info.Label, 120f * u, UIFont.Heavy, UISlant.Night, TextAlignmentOptions.MidlineLeft, UITextFx.Plain, "Floor label");
                float lw = label.GetPreferredValues(info.Label).x;
                label.rectTransform.Place(UIAnchor.Center, new Vector2(0f, 0.5f), new Vector2(x, 4f * u), new Vector2(lw + 8f, 150f * u));
                Track(label.rectTransform, new Vector2(160f * u, 0f), 0.02f, 0.28f);
                _bandText.Add(label.gameObject);
                x += lw + 28f * u;
            }
            var areaName = UIFactory.Label(_band, info.Name ?? "", 108f * u, UIFont.Title, town ? UISlant.Night : Color.white, TextAlignmentOptions.MidlineLeft, UITextFx.Plain, "Area name");
            float maxW = (rootW * 0.5f - SafeRight() - 60f * u) - x;
            areaName.enableAutoSizing = true; areaName.fontSizeMax = 108f * u; areaName.fontSizeMin = 56f * u;
            areaName.overflowMode = TextOverflowModes.Ellipsis;
            areaName.rectTransform.Place(UIAnchor.Center, new Vector2(0f, 0.5f), new Vector2(x, 0f), new Vector2(Mathf.Max(200f, maxW), 150f * u));
            Track(areaName.rectTransform, new Vector2(220f * u, 0f), 0.06f, 0.3f);
            _bandText.Add(areaName.gameObject);

            // Below the band where it is lowest at the text's left edge (cyan rule included), so nothing overlaps.
            float bandBottom = _root.rect.height * 0.5f - BandRaise * u + 135f * u + (rootW * 0.5f - left - SafeLeft()) * Mathf.Tan(BandTilt * Mathf.Deg2Rad);
            float y = -(bandBottom - (_root.rect.height - _text.rect.height) * 0.5f + 20f * u);
            if (!string.IsNullOrEmpty(info.Line))
            {
                var line = UIFactory.Paragraph(_text, info.Line, 20f * u, UISlant.Paper, "Description");
                // Bold SDF (not FontStyles.Bold on Body SDF: Body has no bold typeface or fallbacks, so the Bold weight lookup cannot
                // reach U+2026 and TMP drops the Ellipsis overflow to Truncate with a console warning).
                UIFactory.Style(line, UIFont.Bold, UITextFx.Shadow);
                line.lineSpacing = 0f;
                line.maxVisibleLines = 2;
                line.overflowMode = TextOverflowModes.Ellipsis;
                float lineW = Mathf.Min(w - left * 2f, 900f * u);
                line.rectTransform.Place(UIAnchor.TopLeft, new Vector2(left, y), new Vector2(lineW, 64f * u));
                float used = Mathf.Min(64f * u, line.GetPreferredValues(info.Line, lineW, 0f).y);
                Track(line.rectTransform, new Vector2(0f, -12f * u), 0.12f, 0.22f);
                y -= used + 14f * u;
            }
            float cx = left;
            for (int i = 0; i < info.Chips.Count; i++)
            {
                var chip = UISlant.Chip(_text, "Chip " + i, info.Chips[i].Value, 14f * u, 32f * u, UISlant.Plate);
                float cw = UISlant.FitChip(chip, info.Chips[i].Key);
                var plate = (RectTransform)chip.transform.parent;
                plate.Place(UIAnchor.TopLeft, new Vector2(cx, y), plate.sizeDelta);
                Track(plate, new Vector2(-24f * u, 0f), 0.16f + i * 0.04f, 0.22f);
                cx += cw + 10f * u;
            }

            // Hold timer bar and skip hint, bottom right.
            var bar = UIFactory.Image(_text, UISprites.White, UISlant.Band, "Hold bar");
            bar.gameObject.AddComponent<UISkew>();
            bar.rectTransform.Place(UIAnchor.BottomRight, new Vector2(-80f * u, 56f * u), new Vector2(280f * u, 6f * u));
            _barFill = UIFactory.Image(bar.rectTransform, UISprites.White, UISlant.Cyan, "Fill");
            _barFill.gameObject.AddComponent<UISkew>();
            _barFill.rectTransform.anchorMin = Vector2.zero; _barFill.rectTransform.anchorMax = new Vector2(0f, 1f);
            _barFill.rectTransform.offsetMin = _barFill.rectTransform.offsetMax = Vector2.zero;
            string glyph = UIInput.Glyph(UIAction.Confirm);
            string hint = UIRoot.TouchFirst || string.IsNullOrEmpty(glyph) ? "탭하여 건너뛰기" : glyph + " · 클릭으로 건너뛰기";
            var skip = UIFactory.Label(_text, hint, 13f * u, UIFont.Bold, UISlant.Muted, TextAlignmentOptions.BottomRight, UITextFx.Plain, "Skip hint");
            skip.rectTransform.Place(UIAnchor.BottomRight, new Vector2(-80f * u, 70f * u), new Vector2(400f * u, 24f * u));
        }

        float SafeLeft()
        {
            var safe = UIRoot.Instance != null ? UIRoot.Instance.SafeArea : null;
            return safe == null ? 0f : safe.anchorMin.x * _root.rect.width;
        }

        float SafeRight()
        {
            var safe = UIRoot.Instance != null ? UIRoot.Instance.SafeArea : null;
            return safe == null ? 0f : (1f - safe.anchorMax.x) * _root.rect.width;
        }

        void Track(RectTransform rt, Vector2 from, float delay, float duration)
        {
            var group = rt.gameObject.AddComponent<CanvasGroup>();
            group.alpha = 0f;
            _anims.Add(new Anim { Rect = rt, Group = group, Home = rt.anchoredPosition, From = _reduced ? Vector2.zero : from, Delay = delay, Duration = duration });
            rt.anchoredPosition += _reduced ? Vector2.zero : from;
        }

        // ---- timeline -----------------------------------------------------------------------------------

        void Update()
        {
            if (_phase == Phase.Idle) return;
            // A world swap can take a long frame; clamp so the reveal still animates instead of jumping to the end.
            _t += Mathf.Min(Time.unscaledDeltaTime, 1f / 20f);
            switch (_phase)
            {
                case Phase.In:
                    if (_t >= (_reduced ? ReducedIn : InTime))
                    {
                        _phase = Phase.Hold; _t = 0f;
                        Apply();
                        RunCovered(_covered);
                        _covered = null;
                    }
                    break;
                case Phase.Hold:
                    // Screens pushed while covered (story, notices) must not take input from under the card.
                    if (UIInput.TopLayer != _root) UIInput.PushLayer(_root);
                    if (_t >= MinHold && UIInput.Advance) { UIInput.Consume(); _skip = true; }
                    if (_skip || _t >= (_reduced ? ReducedHold : HoldTime)) StartOut();
                    break;
                case Phase.Out:
                    if (_t >= (_reduced ? ReducedOut : OutTime)) { EndNow(); return; }
                    break;
            }
            Apply();
        }

        void RunCovered(Action covered)
        {
            try { covered?.Invoke(); }
            catch (Exception e) { Debug.LogException(e); }
            if (this == null || _phase != Phase.Hold) return;
            // The swap may have pushed screens (and their input layers) above the card: the card keeps the top
            // input layer until StartOut releases it, so Confirm cannot advance a story hidden underneath.
            UIInput.PushLayer(_root);
            UIAreaCardInfo info = null;
            try { info = _info?.Invoke(); }
            catch (Exception e) { Debug.LogException(e); }
            // Rebuild the text layer for the (possibly new) destination.
            if (_text != null)
                for (int i = _text.childCount - 1; i >= 0; i--) Destroy(_text.GetChild(i).gameObject);
            foreach (var go in _bandText) if (go != null) Destroy(go);
            _bandText.Clear();
            _anims.Clear();
            // Keep the overlay on top of anything the swap created (HUD, story screens).
            _root.SetAsLastSibling();
            if (UIRoot.Instance != null && UIRoot.Instance.Fader != null) UIRoot.Instance.Fader.transform.SetAsLastSibling();
            BuildText(info ?? new UIAreaCardInfo());
            _textGroup.alpha = 1f;
        }

        void StartOut()
        {
            _phase = Phase.Out; _t = 0f;
            // Release input as soon as the reveal starts: the new screen is usable while the card sweeps away.
            _blocker.raycastTarget = false;
            UIInput.PopLayer(_root);
        }

        void EndNow()
        {
            _phase = Phase.Idle;
            _blocker.raycastTarget = false;
            UIInput.PopLayer(_root);
            if (_root != null) _root.gameObject.SetActive(false);
            var done = _finished; _finished = null; _covered = null; _info = null;
            try { done?.Invoke(); }
            catch (Exception e) { Debug.LogException(e); }
        }

        void Apply()
        {
            if (_cover == null) return;
            switch (_phase)
            {
                case Phase.In:
                {
                    float p = Mathf.Clamp01(_t / (_reduced ? ReducedIn : InTime));
                    if (_reduced) { _group.alpha = p; Place(0f, 0f); }
                    else
                    {
                        _group.alpha = 1f;
                        float cover = UITween.Evaluate(UIEase.OutCubic, p);
                        float band = UITween.Evaluate(UIEase.OutCubic, Mathf.Clamp01((p - 0.15f) / 0.85f));
                        Place(-(1f - cover) * _coverWidth, -(1f - band) * _bandTravel);
                    }
                    _textGroup.alpha = 0f;
                    break;
                }
                case Phase.Hold:
                {
                    _group.alpha = 1f;
                    Place(0f, 0f);
                    float hold = _reduced ? ReducedHold : HoldTime;
                    if (_barFill != null) _barFill.rectTransform.anchorMax = new Vector2(Mathf.Clamp01(_t / hold), 1f);
                    foreach (var a in _anims)
                    {
                        if (a.Rect == null) continue;
                        float k = Mathf.Clamp01((_t - a.Delay) / a.Duration);
                        float e = UITween.Evaluate(UIEase.OutCubic, k);
                        a.Rect.anchoredPosition = a.Home + a.From * (1f - e);
                        a.Group.alpha = Mathf.Clamp01(k * 1.6f);
                    }
                    break;
                }
                case Phase.Out:
                {
                    float p = Mathf.Clamp01(_t / (_reduced ? ReducedOut : OutTime));
                    if (_reduced) { _group.alpha = 1f - p; break; }
                    float e = UITween.Evaluate(UIEase.InCubic, p);
                    float band = UITween.Evaluate(UIEase.InCubic, Mathf.Clamp01(p / 0.8f));
                    Place(e * _coverWidth, band * _bandTravel);
                    _textGroup.alpha = 1f - Mathf.Clamp01(p * 3f);
                    break;
                }
            }
        }

        void Place(float cover, float band)
        {
            float u = Unit;
            _cover.anchoredPosition = new Vector2(cover, 0f);
            _band.anchoredPosition = new Vector2(band, BandRaise * u);
        }

        void OnDisable()
        {
            if (_root != null) UIInput.PopLayer(_root);
        }

        void OnDestroy()
        {
            if (_instance == this) _instance = null;
        }
    }
}
