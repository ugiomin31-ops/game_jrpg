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
            var scaler = GetComponent<CanvasScaler>();
            scaler.uiScaleMode = CanvasScaler.ScaleMode.ScaleWithScreenSize;
            scaler.referenceResolution = UITheme.ReferenceResolution;
            scaler.screenMatchMode = CanvasScaler.ScreenMatchMode.MatchWidthOrHeight;
            scaler.matchWidthOrHeight = 0.5f;
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

        void LateUpdate()
        {
            if (_safe != Screen.safeArea || _width != Screen.width || _height != Screen.height) UpdateSafeArea();
        }

        void UpdateSafeArea()
        {
            _safe = Screen.safeArea; _width = Screen.width; _height = Screen.height;
            if (_width <= 0 || _height <= 0) return;
            SafeArea.anchorMin = new Vector2(_safe.xMin / _width, _safe.yMin / _height);
            SafeArea.anchorMax = new Vector2(_safe.xMax / _width, _safe.yMax / _height);
            SafeArea.offsetMin = SafeArea.offsetMax = Vector2.zero;
        }

        void OnDestroy() { if (Instance == this) Instance = null; }
    }
}
