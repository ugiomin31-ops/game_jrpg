using System;
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
        // Optional camera pad (the town): touches that begin on the right half rotate / pinch the camera.
        static int _zoneFrame = -10;
        static readonly CamTouch[] Cams = { CamTouch.None, CamTouch.None };
        static Vector2 _lookDelta;
        static float _pinch;
        static Vector2 _start, _current;
        static float _startTime;
        static bool _dragged, _tap;
        static Vector2Int _swipe;
        struct CamTouch
        {
            public int Finger;
            public Vector2 Start, Last;
            public float StartTime;
            public bool Dragged, Paired;
            public static readonly CamTouch None = new CamTouch { Finger = -1 };
        }
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

        /// <summary>
        /// Asks for the right half of the screen to act as a camera pad this frame (call every frame from the world that
        /// wants it): touches that begin there rotate / pinch the camera, the left half keeps the floating stick, and a
        /// short still touch anywhere is still a tap.
        /// </summary>
        public static void RequestCameraZone() => _zoneFrame = Time.frameCount;

        static bool CameraZone => Time.frameCount - _zoneFrame <= 1;

        /// <summary>Screen pixels the camera-pad finger moved this frame (zero unless a single camera finger is down).</summary>
        public static Vector2 LookDelta { get { Refresh(); return _lookDelta; } }

        /// <summary>Change in distance (pixels) between two camera-pad fingers this frame; positive when spreading.</summary>
        public static float Pinch { get { Refresh(); return _pinch; } }

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
            _lookDelta = Vector2.zero;
            _pinch = 0f;
            if (!Supported) { _finger = -1; Cams[0] = Cams[1] = CamTouch.None; return; }
            if (!EnhancedTouchSupport.enabled) EnhancedTouchSupport.Enable();

            bool seen = false;
            bool zone = CameraZone;
            float halfWidth = Screen.width * 0.5f;
            bool hadPair = Cams[0].Finger >= 0 && Cams[1].Finger >= 0;
            float previousSeparation = hadPair ? (Cams[0].Last - Cams[1].Last).magnitude : 0f;
            Span<bool> camSeen = stackalloc bool[2];
            foreach (var t in ETouch.activeTouches)
            {
                var phase = t.phase;
                int slot = CamSlot(t.finger.index);
                if (slot < 0 && zone && phase == ETouchPhase.Began && t.finger.index != _finger && t.screenPosition.x >= halfWidth && !OverUI(t.screenPosition))
                {
                    slot = Cams[0].Finger < 0 ? 0 : Cams[1].Finger < 0 ? 1 : -1;
                    if (slot >= 0)
                    {
                        Cams[slot] = new CamTouch { Finger = t.finger.index, Start = t.screenPosition, Last = t.screenPosition, StartTime = Time.unscaledTime };
                        int other = 1 - slot;
                        if (Cams[other].Finger >= 0) { Cams[other].Paired = true; Cams[slot].Paired = true; }
                    }
                }
                if (slot >= 0)
                {
                    camSeen[slot] = true;
                    var cam = Cams[slot];
                    Vector2 step = t.screenPosition - cam.Last;
                    cam.Last = t.screenPosition;
                    if ((cam.Last - cam.Start).sqrMagnitude > Sq(Inches(TapSlopInches))) cam.Dragged = true;
                    if (cam.Dragged && Cams[1 - slot].Finger < 0) _lookDelta += step;
                    bool ended = phase == ETouchPhase.Ended || phase == ETouchPhase.Canceled;
                    if (ended)
                    {
                        if (phase == ETouchPhase.Ended && !cam.Dragged && !cam.Paired && Time.unscaledTime - cam.StartTime <= TapMaxSeconds) _tap = true;
                        cam = CamTouch.None;
                    }
                    Cams[slot] = cam;
                    continue;
                }
                if (_finger < 0 && phase == ETouchPhase.Began && !OverUI(t.screenPosition) && !(zone && t.screenPosition.x >= halfWidth))
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
            // A camera finger vanished without an end phase (focus loss, missed frame): drop it silently.
            for (int i = 0; i < 2; i++) if (!camSeen[i]) Cams[i] = CamTouch.None;
            if (hadPair && Cams[0].Finger >= 0 && Cams[1].Finger >= 0)
                _pinch = (Cams[0].Last - Cams[1].Last).magnitude - previousSeparation;
            // The tracked finger vanished without an end phase (focus loss, missed frame): drop it silently.
            if (!seen) _finger = -1;
        }

        static int CamSlot(int finger) => finger < 0 ? -1 : Cams[0].Finger == finger ? 0 : Cams[1].Finger == finger ? 1 : -1;

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
