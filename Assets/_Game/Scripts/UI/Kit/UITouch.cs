using System.Collections.Generic;
using UnityEngine;
using UnityEngine.EventSystems;
using UnityEngine.InputSystem.EnhancedTouch;
using ETouch = UnityEngine.InputSystem.EnhancedTouch.Touch;
using ETouchPhase = UnityEngine.InputSystem.TouchPhase;

namespace Abyss.UI
{
    /// <summary>
    /// World-space touch gestures for phones and tablets: a floating virtual stick, taps and swipes.
    /// Only touches that begin outside UI widgets are tracked, so HUD buttons keep working through the event system.
    /// <para>Polled lazily like <see cref="UIInput"/>; <see cref="UIRoot"/> also ticks it every frame so no
    /// began/ended phase is missed. <see cref="Tapped"/> and <see cref="Swipe"/> are true for one frame only.</para>
    /// </summary>
    public static class UITouch
    {
        /// <summary>Movement (inches) before a touch stops counting as a tap.</summary>
        const float TapSlopInches = 0.12f;
        /// <summary>Longest press (seconds) that still counts as a tap.</summary>
        const float TapMaxSeconds = 0.35f;
        /// <summary>Minimum travel (inches) for a swipe.</summary>
        const float SwipeMinInches = 0.3f;
        /// <summary>Longest gesture (seconds) that still counts as a swipe rather than a stick drag.</summary>
        const float SwipeMaxSeconds = 0.6f;
        /// <summary>Stick deflection (inches) that reads as full speed.</summary>
        const float StickRadiusInches = 0.45f;

        static int _frame = -1;
        static int _finger = -1;
        static Vector2 _start, _current;
        static float _startTime;
        static bool _dragged, _tap;
        static Vector2Int _swipe;
        static readonly List<RaycastResult> Hits = new List<RaycastResult>();
        static PointerEventData _probe;
        static EventSystem _probeSystem;

        /// <summary>True on touch devices (phones, tablets, touch laptops).</summary>
        public static bool Supported => UnityEngine.InputSystem.Touchscreen.current != null;

        /// <summary>True while a world touch is held.</summary>
        public static bool Holding { get { Refresh(); return _finger >= 0; } }

        /// <summary>Screen position where the held world touch began.</summary>
        public static Vector2 StickOrigin { get { Refresh(); return _start; } }

        /// <summary>Screen position of the held world touch.</summary>
        public static Vector2 StickPosition { get { Refresh(); return _current; } }

        /// <summary>Floating stick deflection, magnitude 0..1 (zero until the touch moves past the tap slop).</summary>
        public static Vector2 Stick
        {
            get
            {
                Refresh();
                if (_finger < 0 || !_dragged) return Vector2.zero;
                return Vector2.ClampMagnitude((_current - _start) / Inches(StickRadiusInches), 1f);
            }
        }

        /// <summary>True on the frame a short, still world touch was released.</summary>
        public static bool Tapped { get { Refresh(); return _tap; } }

        /// <summary>Dominant direction of a quick flick released this frame (x: -1 left / +1 right, y: +1 up / -1 down).</summary>
        public static Vector2Int Swipe { get { Refresh(); return _swipe; } }

        /// <summary>Converts physical inches to screen pixels (falls back to a phone-like density when DPI is unknown).</summary>
        public static float Inches(float inches) => inches * (Screen.dpi > 1f ? Screen.dpi : 320f);

        /// <summary>Forces this frame's update; called by <see cref="UIRoot"/> so short touches are never missed.</summary>
        internal static void Tick() => Refresh();

        static void Refresh()
        {
            int f = Time.frameCount;
            if (f == _frame) return;
            _frame = f;
            _tap = false;
            _swipe = Vector2Int.zero;
            if (!Supported) { _finger = -1; return; }
            if (!EnhancedTouchSupport.enabled) EnhancedTouchSupport.Enable();

            bool seen = false;
            foreach (var t in ETouch.activeTouches)
            {
                var phase = t.phase;
                if (_finger < 0 && phase == ETouchPhase.Began && !OverUI(t.screenPosition))
                {
                    _finger = t.finger.index;
                    _start = _current = t.screenPosition;
                    _startTime = Time.unscaledTime;
                    _dragged = false;
                }
                if (t.finger.index != _finger) continue;
                seen = true;
                _current = t.screenPosition;
                if ((_current - _start).sqrMagnitude > Sq(Inches(TapSlopInches))) _dragged = true;
                if (phase == ETouchPhase.Ended || phase == ETouchPhase.Canceled)
                {
                    if (phase == ETouchPhase.Ended) Classify();
                    _finger = -1;
                }
            }
            // The tracked finger vanished without an end phase (focus loss, missed frame): drop it silently.
            if (!seen) _finger = -1;
        }

        static void Classify()
        {
            float held = Time.unscaledTime - _startTime;
            Vector2 delta = _current - _start;
            if (!_dragged && held <= TapMaxSeconds) { _tap = true; return; }
            if (held > SwipeMaxSeconds || delta.sqrMagnitude < Sq(Inches(SwipeMinInches))) return;
            _swipe = Mathf.Abs(delta.x) > Mathf.Abs(delta.y)
                ? new Vector2Int(delta.x > 0f ? 1 : -1, 0)
                : new Vector2Int(0, delta.y > 0f ? 1 : -1);
        }

        static bool OverUI(Vector2 screen)
        {
            var system = EventSystem.current;
            if (system == null) return false;
            if (_probe == null || _probeSystem != system) { _probe = new PointerEventData(system); _probeSystem = system; }
            _probe.position = screen;
            Hits.Clear();
            system.RaycastAll(_probe, Hits);
            return Hits.Count > 0;
        }

        static float Sq(float v) => v * v;
    }
}
