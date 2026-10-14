using System;
using System.Collections.Generic;
using TMPro;
using UnityEngine;
using UnityEngine.UI;

namespace Abyss.UI.Battle
{
    /// <summary>Screen band a HUD element occludes in the 3D view.</summary>
    public enum HudRegion { Top, Bottom, Right }

    /// <summary>One occluded area of the HUD in normalized viewport coordinates (0..1, origin bottom left, safe-area insets included).</summary>
    public readonly struct HudOcclusion
    {
        public HudRegion Region { get; }
        public Rect Viewport { get; }
        public HudOcclusion(HudRegion region, Rect viewport) { Region = region; Viewport = viewport; }
    }

    public sealed partial class BattleHUD
    {
        const float StepX = 18f;
        // Metrics resolved by ComputeMetrics for the current layout key (canvas units).
        float _topH, _partyH, _partyW, _partyGap, _partyMargin, _partyRaise, _partyBand, _fanBottom, _rowH, _rowStep, _fanW, _navH, _headH, _footH, _rightMargin, _leftMargin;
        int _capNoNav = 6, _capNav = 5;
        bool _showNav;

        readonly List<HudOcclusion> _occlusion = new List<HudOcclusion>(3);
        readonly List<HudOcclusion> _scratch = new List<HudOcclusion>(3);
        Rect _free = new Rect(0f, 0f, 1f, 1f), _safeViewport = new Rect(0f, 0f, 1f, 1f);
        int _occlusionVersion;

        /// <summary>
        /// Normalized viewport rectangles the HUD covers right now: the top bar, the party plates (plus threat/estimate chips)
        /// and, while choosing or in auto battle, the right-hand command fan / auto notice. They include the device
        /// safe-area insets (a bar reaches the physical screen edge) and follow layout changes; read them after the HUD's
        /// LateUpdate (it runs after the camera) or subscribe to <see cref="OcclusionChanged"/>.
        /// </summary>
        public IReadOnlyList<HudOcclusion> Occlusion => _occlusion;
        /// <summary>Largest viewport rectangle (0..1) free of the occlusion bands and outside the device cut-outs.</summary>
        public Rect FreeViewport => _free;
        /// <summary>Device safe area as a normalized viewport rectangle.</summary>
        public Rect SafeAreaViewport => _safeViewport;
        /// <summary>Incremented whenever any occlusion rectangle changed.</summary>
        public int OcclusionVersion => _occlusionVersion;
        /// <summary>Raised from LateUpdate after the HUD published changed rectangles.</summary>
        public event Action OcclusionChanged;

        /// <summary>Occlusion rectangle of a region (zero-size when that region is not occupied).</summary>
        public Rect OcclusionOf(HudRegion region)
        {
            foreach (var o in _occlusion) if (o.Region == region) return o.Viewport;
            return Rect.zero;
        }

        void OnEnable()
        {
            UIRoot.LayoutChanged += HandleLayoutChanged;
            HandleLayoutChanged();
        }

        void OnDisable() => UIRoot.LayoutChanged -= HandleLayoutChanged;

        /// <summary>Relayouts only when the layout key changed; never per frame.</summary>
        void HandleLayoutChanged()
        {
            if (_root == null || _menu == null) return;
            float scale = UIRoot.Instance != null && UIRoot.Instance.Canvas != null ? UIRoot.Instance.Canvas.scaleFactor : 1f;
            if (_layoutReady && _layoutCompact == Compact && _layoutTouch == TouchUI && Mathf.Approximately(_layoutTouchTarget, UIRoot.TouchTargetHeight)
                && Mathf.Approximately(_layoutScale, scale) && (_layoutRoot - _root.rect.size).sqrMagnitude < 0.01f) return;
            ApplyLayout();
        }

        /// <summary>
        /// Lays out every mode-dependent widget for the current key. A compact/full switch rebuilds the unit cards from
        /// their display snapshots; an open menu keeps its absolute selection and armed target, with paging and focus
        /// clamped to the new capacity.
        /// </summary>
        void ApplyLayout()
        {
            bool modeChanged = _layoutReady && _layoutCompact != Compact;
            int selected = _page * _perPage + _focus;
            _layoutReady = true; _layoutCompact = Compact; _layoutTouch = TouchUI; _layoutTouchTarget = UIRoot.TouchTargetHeight;
            _layoutScale = UIRoot.Instance != null && UIRoot.Instance.Canvas != null ? UIRoot.Instance.Canvas.scaleFactor : 1f;
            _layoutRoot = _root.rect.size;
            ComputeMetrics();
            LayoutChrome();
            LayoutMenu();
            if (_fastToast != null) LayoutFastToast();
            if (modeChanged)
            {
                RebuildCards();
                if (_orderShown) RefreshOrder();
                if (_ult != null && !_ult.gameObject.activeSelf) DiscardUltimate();
            }
            else { LayoutParty(); foreach (var card in _cards.Values) card.Dirty = true; }
            RefreshPlateStates();
            if (_input && _reward == null && _menu.gameObject.activeSelf)
            {
                ClampSelection(selected);
                Render();
            }
            UpdateOcclusion();
        }

        void ComputeMetrics()
        {
            bool compact = Compact, touch = TouchUI;
            float touchTarget = UIRoot.TouchTargetHeight;
            _topH = compact ? 80f : 92f;
            _partyH = compact ? 96f : 120f;
            _partyW = compact ? 330f : 400f;
            _partyGap = compact ? 10f : 12f;
            _partyMargin = compact ? 10f : 14f;
            _partyRaise = compact ? 8f : 10f;
            _partyBand = _partyMargin + _partyH + _partyRaise;
            _rowH = touch ? touchTarget : 70f;
            _rowStep = _rowH;
            _fanW = compact ? 440f : 500f;
            _navH = touch ? touchTarget : 48f;
            _headH = compact ? 42f : 48f;
            _footH = compact ? 40f : 44f;
            _rightMargin = compact ? 26f : 38f;
            _leftMargin = compact ? 22f : 30f;
            _fanBottom = _partyBand + 26f;
        }

        void LayoutChrome()
        {
            bool compact = Compact, touch = TouchUI;
            float touchTarget = UIRoot.TouchTargetHeight;
            float stripH = compact ? 64f : 72f;
            _top.Place(UIAnchor.TopLeft, new Vector2(_leftMargin, -8f), new Vector2(compact ? 650f : 780f, stripH));
            _roundLabel.rectTransform.Place(UIAnchor.Left, Vector2.zero, new Vector2(124f, 54f));
            _roundLabel.fontSize = compact ? 34 : 36;
            _orderRow.Place(UIAnchor.Left, new Vector2(124f, 0f), new Vector2(compact ? 520f : 640f, stripH));
            // Auto / speed sit in the top-right corner; their painted plates are slim, the touch target keeps full height.
            float visual = compact ? 64f : 60f, extra = touch ? Mathf.Max(0f, touchTarget - visual) : 0f;
            float autoW = compact ? 232f : 260f, speedW = compact ? 150f : 170f;
            _autoButton.Resize(new Vector2(autoW, visual), extra);
            _autoButton.Rt().Place(UIAnchor.TopRight, new Vector2(-_rightMargin, -8f), _autoButton.Rt().sizeDelta);
            if (_speedButton != null)
            {
                _speedButton.Resize(new Vector2(speedW, visual), extra);
                _speedButton.Rt().Place(UIAnchor.TopRight, new Vector2(-_rightMargin - autoW - 14f, -8f), _speedButton.Rt().sizeDelta);
            }
            float leftEdge = _leftMargin + 124f + (compact ? 500f : 600f) + 24f;
            float rightEdge = _root.rect.width - _rightMargin - autoW - 14f - speedW - 24f;
            float centreWidth = Mathf.Clamp(rightEdge - leftEdge, 260f, compact ? 560f : 640f);
            float centreX = leftEdge + Mathf.Max(0f, (rightEdge - leftEdge - centreWidth) * 0.5f);
            _logPanel.Place(UIAnchor.TopLeft, new Vector2(centreX, -10f), new Vector2(centreWidth, _topH - 22f));
            _log.fontSize = compact ? 26 : 26;
            _enemyBanner.Place(UIAnchor.TopLeft, new Vector2(centreX - 20f, -6f), new Vector2(centreWidth + 20f, _topH - 14f));
            _enemyBannerHome = _enemyBanner.anchoredPosition;
            _chainPlate.Rect.Place(UIAnchor.BottomLeft, new Vector2(_leftMargin, _partyBand + 4f), new Vector2(compact ? 250f : 290f, 38f));
            _banner.Place(UIAnchor.Top, new Vector2(0f, -(_topH + 14f)), new Vector2(compact ? 640f : 760f, compact ? 70f : 78f));
            _bannerText.fontSize = compact ? 38 : 42;
        }

        /// <summary>
        /// Resolves the command fan's page capacity for the current metrics: the stack, header and description footer (plus
        /// the navigation row when a submenu or several pages need it) must fit between the party band and the top bar.
        /// </summary>
        void LayoutMenu()
        {
            float rootHeight = _root.rect.height > 1f ? _root.rect.height : Compact ? UIRoot.PhoneReference.y : UITheme.ReferenceResolution.y;
            float available = rootHeight - _topH - 4f - _fanBottom;
            float fixedHeight = _headH + _footH + 8f;
            _capNoNav = Mathf.Clamp(Mathf.FloorToInt((available - fixedHeight) / _rowStep), 1, 6);
            _capNav = Mathf.Clamp(Mathf.FloorToInt((available - fixedHeight - _navH) / _rowStep), 1, 6);
            ResolvePaging();
            float autoHeight = TouchUI ? UIRoot.TouchTargetHeight + 14f : 76f;
            _autoBanner.Place(UIAnchor.BottomRight, new Vector2(-_rightMargin, _fanBottom), new Vector2(_fanW, autoHeight));
            _autoBannerTitle.rectTransform.Stretch(26f, 0f, _fanW * 0.42f, 0f);
            _autoBannerTitle.fontSize = Compact ? 30 : 30;
            float button = TouchUI ? UIRoot.TouchTargetHeight : 56f;
            _manualButton.Resize(new Vector2(_fanW * 0.42f, Mathf.Min(button, autoHeight - 14f)), 0f);
            _manualButton.Rt().Place(UIAnchor.Right, new Vector2(-14f, 0f), _manualButton.Rt().sizeDelta);
            RefreshAutoBanner();
        }

        void ResolvePaging()
        {
            _showNav = _back != null || _choices.Count > _capNoNav;
            _perPage = Math.Max(1, _showNav ? _capNav : _capNoNav);
        }

        // ---- occlusion ------------------------------------------------------------------------------

        void UpdateOcclusion()
        {
            if (_world == null || !BuildScreenMap()) return;
            // The canvas and the camera share one pixel space (Screen.width can differ from it in the editor's Game view).
            Rect pixels = _camera != null ? _camera.pixelRect : new Rect(0f, 0f, Screen.width, Screen.height);
            float sw = Mathf.Max(1f, pixels.width), sh = Mathf.Max(1f, pixels.height);
            var safe = Screen.safeArea;
            float fw = Mathf.Max(1f, Screen.width), fh = Mathf.Max(1f, Screen.height);
            Rect safeView = new Rect(safe.xMin / fw, safe.yMin / fh, safe.width / fw, safe.height / fh);
            float width = _canvasRect.width, height = _canvasRect.height;
            _scratch.Clear();
            // Canvas units -> normalized viewport. Bars run to the physical screen edge, so the insets are covered.
            float TopY(float canvasY) => (_py0 + canvasY / _ky - pixels.yMin) / sh;
            float X(float canvasX) => (_px0 + canvasX / _kx - pixels.xMin) / sw;
            float topEdge = TopY(height - _topH);
            _scratch.Add(new HudOcclusion(HudRegion.Top, new Rect(0f, topEdge, 1f, 1f - topEdge)));
            float bottomEdge = TopY(_partyBand + (AnyBottomChip() ? ChipBand : 0f));
            _scratch.Add(new HudOcclusion(HudRegion.Bottom, new Rect(0f, 0f, 1f, bottomEdge)));
            Rect right = Rect.zero;
            if (_menu != null && _menu.gameObject.activeSelf) right = CanvasRect(_menu, width);
            else if (_autoBanner != null && _autoBanner.gameObject.activeSelf) right = CanvasRect(_autoBanner, width);
            float freeRight = safeView.xMax;
            if (right.width > 0f)
            {
                float x0 = X(right.xMin), y0 = TopY(right.yMin), y1 = TopY(right.yMax);
                _scratch.Add(new HudOcclusion(HudRegion.Right, new Rect(x0, y0, 1f - x0, y1 - y0)));
                freeRight = Mathf.Min(freeRight, x0);
            }
            float freeLeft = safeView.xMin;
            var free = Rect.MinMaxRect(freeLeft, Mathf.Max(bottomEdge, safeView.yMin), Mathf.Max(freeLeft, freeRight), Mathf.Min(topEdge, safeView.yMax));
            if (!SameOcclusion(_scratch, free, safeView))
            {
                _occlusion.Clear(); _occlusion.AddRange(_scratch);
                _free = free; _safeViewport = safeView; _occlusionVersion++;
                OcclusionChanged?.Invoke();
            }
        }

        bool SameOcclusion(List<HudOcclusion> next, Rect free, Rect safe)
        {
            if (next.Count != _occlusion.Count) return false;
            for (int i = 0; i < next.Count; i++)
                if (next[i].Region != _occlusion[i].Region || !Near(next[i].Viewport, _occlusion[i].Viewport)) return false;
            return Near(free, _free) && Near(safe, _safeViewport);
        }

        static bool Near(Rect a, Rect b) =>
            Mathf.Abs(a.xMin - b.xMin) < 0.0005f && Mathf.Abs(a.yMin - b.yMin) < 0.0005f && Mathf.Abs(a.xMax - b.xMax) < 0.0005f && Mathf.Abs(a.yMax - b.yMax) < 0.0005f;
    }
}
