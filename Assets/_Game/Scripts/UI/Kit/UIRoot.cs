using UnityEngine;
using UnityEngine.EventSystems;
using UnityEngine.InputSystem.UI;
using UnityEngine.UI;

namespace Abyss.UI
{
    /// <summary>Layered 1920x1080 Korean UI canvas. Create once before constructing screens.</summary>
    [DisallowMultipleComponent, RequireComponent(typeof(Canvas), typeof(CanvasScaler), typeof(GraphicRaycaster))]
    public sealed class UIRoot : MonoBehaviour
    {
        public static UIRoot Instance { get; private set; }
        public Canvas Canvas { get; private set; }
        public RectTransform Hud { get; private set; }
        public RectTransform SafeArea { get; private set; }
        public UIScreenStack Screens { get; private set; }
        public UIScreenStack Modals { get; private set; }
        public UIDialogBox Dialog { get; private set; }
        public UITooltip Tooltip { get; private set; }
        public UIToast Toast { get; private set; }
        public UINumberPopup Numbers { get; private set; }
        public UIFader Fader { get; private set; }
        internal bool ReducedMotion { get; set; }
        Rect _safe;
        int _width, _height;
        CanvasScaler _scaler;
        RectTransform _stickBase, _stickKnob;
        int _stickFrame = -1;

        public static UIRoot Create(Transform parent = null, bool persistent = true)
        {
            if (Instance != null) return Instance;
            var go = new GameObject("Abyss UI", typeof(RectTransform));
            go.layer = 5;
            if (parent != null) go.transform.SetParent(parent, false);
            var root = go.AddComponent<UIRoot>();
            if (persistent && parent == null) DontDestroyOnLoad(go);
            return root;
        }

        void Awake()
        {
            if (Instance != null && Instance != this) { Destroy(gameObject); return; }
            Instance = this;
            Canvas = GetComponent<Canvas>();
            Canvas.renderMode = RenderMode.ScreenSpaceOverlay;
            Canvas.sortingOrder = 100;
            _scaler = GetComponent<CanvasScaler>();
            _scaler.uiScaleMode = CanvasScaler.ScaleMode.ScaleWithScreenSize;
            _scaler.referenceResolution = UITheme.ReferenceResolution;
            _scaler.screenMatchMode = CanvasScaler.ScreenMatchMode.MatchWidthOrHeight;
            EnsureEventSystem();
            SafeArea = UIFactory.Rect(transform, "Safe Area").Stretch();
            Hud = UIFactory.Rect(SafeArea, "HUD").Stretch();
            Numbers = UIFactory.Add<UINumberPopup>(transform, "World Numbers"); Numbers.Build();
            Screens = UIFactory.Add<UIScreenStack>(SafeArea, "Screens"); Screens.Rt().Stretch();
            Dialog = UIFactory.DialogBox(SafeArea);
            Modals = UIFactory.Add<UIScreenStack>(SafeArea, "Modals"); Modals.Rt().Stretch();
            Tooltip = UIFactory.Add<UITooltip>(SafeArea, "Tooltips"); Tooltip.Build();
            Toast = UIFactory.Add<UIToast>(SafeArea, "Notifications"); Toast.Build();
            Fader = UIFactory.Add<UIFader>(transform, "Transitions"); Fader.Build();
            BuildTouchStick();
            // SafeArea precedes full-canvas layers by construction; bring it above world numbers.
            SafeArea.SetAsLastSibling();
            Fader.transform.SetAsLastSibling();
            UpdateSafeArea();
        }

        static void EnsureEventSystem()
        {
            var system = FindFirstObjectByType<EventSystem>();
            if (system == null)
            {
                var go = new GameObject("UI Event System", typeof(EventSystem));
                system = go.GetComponent<EventSystem>();
                DontDestroyOnLoad(go);
            }
            var module = system.GetComponent<InputSystemUIInputModule>();
            if (module == null)
            {
                foreach (var old in system.GetComponents<BaseInputModule>()) { old.enabled = false; Destroy(old); }
                module = system.gameObject.AddComponent<InputSystemUIInputModule>();
                module.AssignDefaultActions();
            }
            // Toolkit navigation is polled by UIInput; event module owns pointer routing only.
            module.move = null;
            module.submit = null;
            module.cancel = null;
            system.sendNavigationEvents = false;
        }

        /// <summary>Shows the floating movement stick under the player's thumb this frame (call every frame while movement is allowed).</summary>
        public void RequestTouchStick() => _stickFrame = Time.frameCount;

        void Update() => UITouch.Tick();

        void LateUpdate()
        {
            if (_safe != Screen.safeArea || _width != Screen.width || _height != Screen.height || Compact != ComputeCompact(Screen.width, Screen.height)) UpdateSafeArea();
            UpdateTouchStick();
        }

        void BuildTouchStick()
        {
            _stickBase = UIFactory.Image(transform, UISprites.Circle, Color.white.WithAlpha(0.14f), "Touch Stick").rectTransform;
            _stickBase.Place(UIAnchor.BottomLeft, new Vector2(0.5f, 0.5f), Vector2.zero, new Vector2(220f, 220f));
            _stickKnob = UIFactory.Image(_stickBase, UISprites.Circle, UITheme.GoldBright.WithAlpha(0.55f), "Knob").rectTransform;
            _stickKnob.Place(UIAnchor.Center, Vector2.zero, new Vector2(96f, 96f));
            _stickBase.gameObject.SetActive(false);
        }

        void UpdateTouchStick()
        {
            if (_stickBase == null) return;
            var stick = UITouch.Stick;
            bool show = _stickFrame == Time.frameCount && UITouch.Holding && stick != Vector2.zero;
            if (_stickBase.gameObject.activeSelf != show) _stickBase.gameObject.SetActive(show);
            if (!show) return;
            _stickBase.SetAsLastSibling();
            var canvas = (RectTransform)transform;
            RectTransformUtility.ScreenPointToLocalPointInRectangle(canvas, UITouch.StickOrigin, null, out var origin);
            _stickBase.anchoredPosition = origin + canvas.rect.size * 0.5f;
            _stickKnob.anchoredPosition = stick * (_stickBase.sizeDelta.x * 0.5f);
        }

        /// <summary>
        /// Landscape phone layout: touch-first and wide (≥1.85:1). The canvas then uses <see cref="PhoneReference"/>
        /// (900 units tall instead of 1080), which draws every text and button 20 % larger, and screens switch to
        /// their thumb-sized layouts. Tablets and desktops keep 1920x1080.
        /// </summary>
        public static bool Compact { get; private set; }
        /// <summary>Phones and tablets (or any device with a touchscreen): keyboard/gamepad hints are hidden.</summary>
        public static bool TouchFirst => Application.isMobilePlatform || UITouch.Supported;
        public static readonly Vector2 PhoneReference = new Vector2(1600f, 900f);

        static bool ComputeCompact(int width, int height) =>
            (Application.isMobilePlatform || UITouch.Supported) && height > 0 && (float)width / height >= 1.85f;

        void UpdateSafeArea()
        {
            _safe = Screen.safeArea; _width = Screen.width; _height = Screen.height;
            if (_width <= 0 || _height <= 0) return;
            Compact = ComputeCompact(_width, _height);
            _scaler.referenceResolution = Compact ? PhoneReference : UITheme.ReferenceResolution;
            // Layouts are authored for 16:9: wider screens (most phones) keep the full height and gain width,
            // narrower ones (tablets) keep the full width and gain height, so nothing is pushed off-screen.
            float reference = _scaler.referenceResolution.x / _scaler.referenceResolution.y;
            _scaler.matchWidthOrHeight = (float)_width / _height >= reference ? 1f : 0f;
            SafeArea.anchorMin = new Vector2(_safe.xMin / _width, _safe.yMin / _height);
            SafeArea.anchorMax = new Vector2(_safe.xMax / _width, _safe.yMax / _height);
            SafeArea.offsetMin = SafeArea.offsetMax = Vector2.zero;
        }

        void OnDestroy() { if (Instance == this) Instance = null; }
    }
}
