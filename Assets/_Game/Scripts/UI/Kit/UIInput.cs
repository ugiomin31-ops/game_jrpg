using System;
using System.Collections.Generic;
using UnityEngine;
using UnityEngine.InputSystem;

namespace Abyss.UI
{
    /// <summary>Device family that produced the latest input (drives key-hint glyphs).</summary>
    public enum UIInputDevice { KeyboardMouse, Gamepad, Touch }

    /// <summary>Logical UI actions (for key hints and custom bindings).</summary>
    public enum UIAction { Confirm, Cancel, TabPrev, TabNext, Menu, Info }

    /// <summary>
    /// Static Input System polling for menus. All queries are per-frame and side-effect free except
    /// <see cref="Consume"/>; navigation pulses include hold-to-repeat.
    /// <para>Keyboard: arrows/WASD navigate, Enter/Space/Z confirm, Esc/X/Backspace cancel, Q/E tabs, Tab/C menu, Shift/I info.
    /// Gamepad: d-pad/left stick, South confirm, East cancel, shoulders tabs, Start/North menu, West info. Mouse: right click cancels.
    /// Touch: taps advance dialog; the Android back button arrives as Escape and cancels.</para>
    /// <para>Input layers: modal UI pushes its root with <see cref="PushLayer"/>; widgets only react when
    /// <see cref="CanReceive"/> is true (they live under the top layer).</para>
    /// </summary>
    public static class UIInput
    {
        /// <summary>Seconds before a held direction starts repeating.</summary>
        public const float RepeatDelay = 0.36f;
        /// <summary>Seconds between repeats while held.</summary>
        public const float RepeatInterval = 0.075f;
        const float StickThreshold = 0.5f;

        static int _frame = -1;
        static int _consumedFrame = -1;
        static Vector2Int _heldDir, _pulse;
        static float _repeatAt;
        static UIInputDevice _device = Application.isMobilePlatform ? UIInputDevice.Touch : UIInputDevice.KeyboardMouse;
        static readonly List<Transform> Layers = new List<Transform>();

        /// <summary>Raised when the active device family changes.</summary>
        public static event Action<UIInputDevice> DeviceChanged;

        /// <summary>Device family of the latest input.</summary>
        public static UIInputDevice Device { get { Refresh(); return _device; } }

        // ---- buttons ----------------------------------------------------------------------------------

        /// <summary>Confirm pressed this frame (Enter/Space/Z, gamepad South).</summary>
        public static bool Confirm => Live && (Pressed(Kb?.enterKey) || Pressed(Kb?.numpadEnterKey) || Pressed(Kb?.spaceKey) || Pressed(Kb?.zKey) || Pressed(Pad?.buttonSouth));

        /// <summary>Cancel pressed this frame (Esc/X/Backspace, gamepad East, mouse right button).</summary>
        public static bool Cancel => Live && (Pressed(Kb?.escapeKey) || Pressed(Kb?.xKey) || Pressed(Kb?.backspaceKey) || Pressed(Pad?.buttonEast) || Pressed(Ms?.rightButton));

        /// <summary>Previous tab (Q, left shoulder).</summary>
        public static bool TabPrev => Live && (Pressed(Kb?.qKey) || Pressed(Pad?.leftShoulder));

        /// <summary>Next tab (E, right shoulder).</summary>
        public static bool TabNext => Live && (Pressed(Kb?.eKey) || Pressed(Pad?.rightShoulder));

        /// <summary>Open/close menu (Tab/C, gamepad Start/North).</summary>
        public static bool Menu => Live && (Pressed(Kb?.tabKey) || Pressed(Kb?.cKey) || Pressed(Pad?.startButton) || Pressed(Pad?.buttonNorth));

        /// <summary>Info / detail toggle (Shift/I, gamepad West).</summary>
        public static bool Info => Live && (Pressed(Kb?.leftShiftKey) || Pressed(Kb?.iKey) || Pressed(Pad?.buttonWest));

        /// <summary>Confirm, left click or a tap — advancing dialog text.</summary>
        public static bool Advance => Confirm || (Live && (Pressed(Ms?.leftButton) || Pressed(Ts?.primaryTouch.press)));

        /// <summary>True while confirm or a touch is held (fast-forward dialog).</summary>
        public static bool ConfirmHeld => (Kb != null && (Kb.enterKey.isPressed || Kb.spaceKey.isPressed || Kb.zKey.isPressed)) || (Pad != null && Pad.buttonSouth.isPressed)
            || (Ts != null && Ts.primaryTouch.press.isPressed);

        /// <summary>Any key / button / click this frame (title screens, skipping).</summary>
        public static bool AnyPressed => Live && ((Kb != null && Kb.anyKey.wasPressedThisFrame) || Pressed(Ms?.leftButton) || Pressed(Ts?.primaryTouch.press) || PadAnyPressed());

        /// <summary>True if the logical action was pressed this frame.</summary>
        public static bool Pressed(UIAction action)
        {
            switch (action)
            {
                case UIAction.Confirm: return Confirm;
                case UIAction.Cancel: return Cancel;
                case UIAction.TabPrev: return TabPrev;
                case UIAction.TabNext: return TabNext;
                case UIAction.Menu: return Menu;
                case UIAction.Info: return Info;
                default: return false;
            }
        }

        // ---- navigation ---------------------------------------------------------------------------------

        /// <summary>Direction pulse this frame with hold-repeat (x: -1 left / +1 right, y: +1 up / -1 down).</summary>
        public static Vector2Int Navigate { get { Refresh(); return Live ? _pulse : Vector2Int.zero; } }

        /// <summary>Vertical navigation pulse: -1 = move selection up the list, +1 = down.</summary>
        public static int NavigateRows => -Navigate.y;

        /// <summary>Raw held direction (no repeat).</summary>
        public static Vector2Int NavigateHeld { get { Refresh(); return _heldDir; } }

        /// <summary>Mouse wheel notches this frame (+ = scroll up).</summary>
        public static float Scroll => Ms == null ? 0f : Ms.scroll.ReadValue().y / 120f;

        /// <summary>Mouse pointer position in screen pixels.</summary>
        public static Vector2 PointerPosition => Ms == null ? Vector2.zero : Ms.position.ReadValue();

        // ---- consumption & layers -----------------------------------------------------------------------

        /// <summary>Marks all button/navigation input of this frame as handled so later readers see nothing.</summary>
        public static void Consume() => _consumedFrame = Time.frameCount;

        /// <summary>Pushes a modal input layer: only widgets under <paramref name="root"/> receive input until popped.</summary>
        public static void PushLayer(Transform root)
        {
            Layers.Remove(root);
            Layers.Add(root);
        }

        /// <summary>Removes a layer pushed with <see cref="PushLayer"/> (order independent).</summary>
        public static void PopLayer(Transform root) => Layers.Remove(root);

        /// <summary>The top input layer, or null when none.</summary>
        public static Transform TopLayer
        {
            get
            {
                for (int i = Layers.Count - 1; i >= 0; i--)
                {
                    if (Layers[i] != null) return Layers[i];
                    Layers.RemoveAt(i);
                }
                return null;
            }
        }

        /// <summary>True when <paramref name="widget"/> lies under the top input layer (or no layer is active).</summary>
        public static bool CanReceive(Component widget)
        {
            var top = TopLayer;
            return top == null || (widget != null && widget.transform.IsChildOf(top));
        }

        // ---- internals ----------------------------------------------------------------------------------

        static Keyboard Kb => Keyboard.current;
        static Gamepad Pad => Gamepad.current;
        static Mouse Ms => Mouse.current;
        static Touchscreen Ts => Touchscreen.current;
        static bool Live { get { Refresh(); return _consumedFrame != Time.frameCount && Application.isFocused; } }

        static bool PadAnyPressed()
        {
            var p = Pad;
            return p != null && (p.buttonSouth.wasPressedThisFrame || p.buttonEast.wasPressedThisFrame || p.buttonWest.wasPressedThisFrame
                || p.buttonNorth.wasPressedThisFrame || p.leftShoulder.wasPressedThisFrame || p.rightShoulder.wasPressedThisFrame
                || p.leftTrigger.wasPressedThisFrame || p.rightTrigger.wasPressedThisFrame || p.startButton.wasPressedThisFrame
                || p.selectButton.wasPressedThisFrame || p.dpad.up.wasPressedThisFrame || p.dpad.down.wasPressedThisFrame
                || p.dpad.left.wasPressedThisFrame || p.dpad.right.wasPressedThisFrame);
        }

        static bool Pressed(UnityEngine.InputSystem.Controls.ButtonControl b) => b != null && b.wasPressedThisFrame;

        static void Refresh()
        {
            int f = Time.frameCount;
            if (f == _frame) return;
            _frame = f;
            TrackDevice();

            var dir = ReadDirection();
            float now = Time.unscaledTime;
            _pulse = Vector2Int.zero;
            if (dir != _heldDir)
            {
                _heldDir = dir;
                if (dir != Vector2Int.zero)
                {
                    _pulse = dir;
                    _repeatAt = now + RepeatDelay;
                }
            }
            else if (dir != Vector2Int.zero && now >= _repeatAt)
            {
                _pulse = dir;
                _repeatAt = now + RepeatInterval;
            }
        }

        static Vector2Int ReadDirection()
        {
            int x = 0, y = 0;
            var kb = Kb;
            if (kb != null)
            {
                if (kb.upArrowKey.isPressed || kb.wKey.isPressed) y += 1;
                if (kb.downArrowKey.isPressed || kb.sKey.isPressed) y -= 1;
                if (kb.leftArrowKey.isPressed || kb.aKey.isPressed) x -= 1;
                if (kb.rightArrowKey.isPressed || kb.dKey.isPressed) x += 1;
            }
            var pad = Pad;
            if (pad != null && x == 0 && y == 0)
            {
                var d = pad.dpad.ReadValue();
                var s = pad.leftStick.ReadValue();
                var v = d.sqrMagnitude > 0.01f ? d : s;
                if (Mathf.Abs(v.x) > Mathf.Abs(v.y)) { if (Mathf.Abs(v.x) > StickThreshold) x = v.x > 0 ? 1 : -1; }
                else if (Mathf.Abs(v.y) > StickThreshold) y = v.y > 0 ? 1 : -1;
            }
            // Single axis only: vertical wins so diagonal keys never skip rows.
            if (y != 0) x = 0;
            return new Vector2Int(x, y);
        }

        static void TrackDevice()
        {
            var next = _device;
            var pad = Pad;
            if (pad != null && pad.wasUpdatedThisFrame && (pad.leftStick.ReadValue().sqrMagnitude > 0.25f || PadAnyPressed()))
                next = UIInputDevice.Gamepad;
            else if (Ts != null && Ts.primaryTouch.press.wasPressedThisFrame)
                next = UIInputDevice.Touch;
            else if ((Kb != null && Kb.anyKey.wasPressedThisFrame) || (Ms != null && (Ms.leftButton.wasPressedThisFrame || Ms.delta.ReadValue().sqrMagnitude > 4f)))
                next = UIInputDevice.KeyboardMouse;
            if (next == _device) return;
            _device = next;
            DeviceChanged?.Invoke(next);
        }

        /// <summary>Short glyph text for an action on the current device (rendered in a key cap); empty on touch, where hints show no key.</summary>
        public static string Glyph(UIAction action)
        {
            if (Device == UIInputDevice.Touch) return "";
            bool pad = Device == UIInputDevice.Gamepad;
            switch (action)
            {
                case UIAction.Confirm: return pad ? "A" : "Z";
                case UIAction.Cancel: return pad ? "B" : "X";
                case UIAction.TabPrev: return pad ? "LB" : "Q";
                case UIAction.TabNext: return pad ? "RB" : "E";
                case UIAction.Menu: return pad ? "Y" : "C";
                case UIAction.Info: return pad ? "X" : "Shift";
                default: return "?";
            }
        }
    }
}
