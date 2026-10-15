using System;
using System.Collections.Generic;
using TMPro;
using UnityEngine;
using UnityEngine.UI;

namespace Abyss.UI
{
    /// <summary>Background treatments for <see cref="UIFactory.Panel"/>.</summary>
    public enum UIPanelStyle
    {
        /// <summary>Navy glass with thin gold line — default window.</summary>
        Glass,
        /// <summary>Glass with ornate gold corner filigree and gems — important windows, modals, dialog.</summary>
        Ornate,
        /// <summary>Dark compact tooltip frame.</summary>
        Tooltip,
        /// <summary>Recessed slot.</summary>
        Slot,
        /// <summary>Flat dark navy, no frame — sub-sections inside windows.</summary>
        Dark,
    }

    /// <summary>A panel: drop shadow + framed background; children go directly under <see cref="Rect"/>.</summary>
    [DisallowMultipleComponent]
    public sealed class UIPanel : MonoBehaviour
    {
        /// <summary>The panel root (add content here).</summary>
        public RectTransform Rect => (RectTransform)transform;
        /// <summary>Framed background image (stretched, ignores layout).</summary>
        [field: SerializeField] public Image Background { get; internal set; }
        /// <summary>Soft drop shadow behind the panel (null when created without shadow).</summary>
        [field: SerializeField] public Image Shadow { get; internal set; }

        /// <summary>Swaps the background treatment.</summary>
        public void SetStyle(UIPanelStyle style) => UIFactory.ApplyPanelStyle(Background, style);
    }

    /// <summary>
    /// Code-only construction of the Abyss UI (no prefabs). Every method parents the new object under
    /// <c>parent</c>, uses <see cref="UITheme"/> styling, and returns the main component.
    /// Layout is at the 1920×1080 reference resolution (see <see cref="UIRoot"/>).
    /// </summary>
    public static class UIFactory
    {
        // ---- primitives -----------------------------------------------------------------------------

        /// <summary>Creates an empty UI object with a RectTransform.</summary>
        public static RectTransform Rect(Transform parent, string name = "Rect")
        {
            var go = new GameObject(name, typeof(RectTransform));
            go.layer = 5; // UI
            var rt = (RectTransform)go.transform;
            rt.SetParent(parent, false);
            return rt;
        }

        /// <summary>Creates a UI child carrying component <typeparamref name="T"/>.</summary>
        public static T Add<T>(Transform parent, string name) where T : Component => Rect(parent, name).gameObject.AddComponent<T>();

        /// <summary>Creates an Image (sliced automatically when the sprite has borders).</summary>
        /// <param name="borderScale">Values &gt; 1 shrink 9-slice borders (sprite pixels per canvas unit).</param>
        public static Image Image(Transform parent, Sprite sprite, Color? color = null, string name = "Image", bool raycast = false, float borderScale = 1f)
        {
            var img = Add<Image>(parent, name);
            img.sprite = sprite;
            img.color = color ?? Color.white;
            img.raycastTarget = raycast;
            img.type = sprite != null && sprite.border != Vector4.zero ? UnityEngine.UI.Image.Type.Sliced : UnityEngine.UI.Image.Type.Simple;
            img.pixelsPerUnitMultiplier = borderScale;
            return img;
        }

        /// <summary>Creates a RawImage (portraits, render textures).</summary>
        public static RawImage RawImage(Transform parent, Texture texture = null, string name = "RawImage")
        {
            var img = Add<RawImage>(parent, name);
            img.texture = texture;
            img.raycastTarget = false;
            return img;
        }

        /// <summary>Full-stretch flat colour overlay (dimmers, flashes, raycast blockers).</summary>
        public static Image Fill(Transform parent, Color color, string name = "Fill", bool raycast = false)
        {
            var img = Image(parent, UISprites.White, color, name, raycast);
            img.rectTransform.Stretch();
            return img;
        }

        /// <summary>Square icon image.</summary>
        public static Image Icon(Transform parent, Sprite sprite, float size, string name = "Icon")
        {
            var img = Image(parent, sprite, Color.white, name);
            img.preserveAspect = true;
            img.rectTransform.sizeDelta = new Vector2(size, size);
            img.enabled = sprite != null;
            return img;
        }

        /// <summary>Framed window: shadow + background. Place it with <see cref="UIRect"/> helpers and add content as children.</summary>
        public static UIPanel Panel(Transform parent, UIPanelStyle style = UIPanelStyle.Glass, bool shadow = true, string name = "Panel")
        {
            var rt = Rect(parent, name);
            var panel = rt.gameObject.AddComponent<UIPanel>();
            if (shadow)
            {
                panel.Shadow = Image(rt, UISprites.PanelShadow, new Color(1f, 1f, 1f, 0.9f), "Shadow");
                panel.Shadow.rectTransform.Stretch(-26f, -22f, -26f, -34f);
                IgnoreLayout(panel.Shadow);
            }
            panel.Background = Image(rt, null, Color.white, "Background", raycast: true);
            panel.Background.rectTransform.Stretch();
            IgnoreLayout(panel.Background);
            ApplyPanelStyle(panel.Background, style);
            return panel;
        }

        internal static void ApplyPanelStyle(Image bg, UIPanelStyle style)
        {
            bg.type = UnityEngine.UI.Image.Type.Sliced;
            bg.pixelsPerUnitMultiplier = 1f;
            bg.color = Color.white;
            switch (style)
            {
                case UIPanelStyle.Glass: bg.sprite = UISprites.PanelGlass; break;
                case UIPanelStyle.Ornate: bg.sprite = UISprites.PanelOrnate; break;
                case UIPanelStyle.Tooltip: bg.sprite = UISprites.Tooltip; break;
                case UIPanelStyle.Slot: bg.sprite = UISprites.Slot; break;
                case UIPanelStyle.Dark:
                    bg.sprite = UISprites.PanelWhite;
                    bg.color = new Color(0.02f, 0.03f, 0.09f, 0.55f);
                    bg.pixelsPerUnitMultiplier = 1.6f;
                    break;
            }
        }

        /// <summary>Creates a TextMeshPro label styled from the theme (raycasts off).</summary>
        public static TextMeshProUGUI Label(Transform parent, string text, float size = UITheme.SizeLabel, UIFont font = UIFont.Bold,
            Color? color = null, TextAlignmentOptions align = TextAlignmentOptions.MidlineLeft, UITextFx fx = UITextFx.Shadow, string name = "Label")
        {
            var t = Add<TextMeshProUGUI>(parent, name);
            Style(t, font, fx);
            t.text = text;
            t.fontSize = size;
            t.color = color ?? UITheme.Text;
            t.alignment = align;
            t.raycastTarget = false;
            t.textWrappingMode = TextWrappingModes.NoWrap;
            t.overflowMode = TextOverflowModes.Overflow;
            t.richText = true;
            return t;
        }

        /// <summary>Wrapped paragraph label (descriptions, dialog).</summary>
        public static TextMeshProUGUI Paragraph(Transform parent, string text, float size = UITheme.SizeBody, Color? color = null, string name = "Paragraph")
        {
            var t = Label(parent, text, size, UIFont.Body, color, TextAlignmentOptions.TopLeft, UITextFx.Shadow, name);
            t.textWrappingMode = TextWrappingModes.Normal;
            t.lineSpacing = 6f;
            return t;
        }

        /// <summary>Applies a theme font + effect preset to any TMP text.</summary>
        public static void Style(TMP_Text text, UIFont font, UITextFx fx)
        {
            text.font = UITheme.Font(font);
            var mat = UITheme.TextMaterial(font, fx);
            if (mat != null) text.fontSharedMaterial = mat;
        }

        /// <summary>Gold flourish separator line, centred, <paramref name="width"/> wide.</summary>
        public static Image Separator(Transform parent, float width = 420f, string name = "Separator")
        {
            var img = Image(parent, UISprites.Separator, Color.white, name);
            img.rectTransform.sizeDelta = new Vector2(width, 24f);
            return img;
        }

        /// <summary>Full-screen vignette darkening the edges.</summary>
        public static Image Vignette(Transform parent, float alpha = 0.85f)
        {
            var img = Image(parent, UISprites.Vignette, new Color(1f, 1f, 1f, alpha), "Vignette");
            img.rectTransform.Stretch();
            return img;
        }

        // ---- widgets --------------------------------------------------------------------------------

        /// <summary>Framed text button (hover/press tweens, sounds). Default size 260×64.</summary>
        public static UIButton Button(Transform parent, string label, Action onClick = null, Sprite icon = null, string name = null)
        {
            var b = Add<UIButton>(parent, name ?? "Button " + label);
            b.Build(label, icon);
            if (onClick != null) b.Clicked += onClick;
            return b;
        }

        /// <summary>Row/column of buttons with keyboard/gamepad focus navigation.</summary>
        public static UIButtonGroup ButtonGroup(Transform parent, bool horizontal, float spacing = 18f, string name = "Buttons")
        {
            var g = Add<UIButtonGroup>(parent, name);
            g.Build(horizontal, spacing);
            return g;
        }

        /// <summary>Recessed icon slot with count badge (inventory/equipment grids).</summary>
        public static UIIconSlot IconSlot(Transform parent, float size = 88f, Sprite icon = null, string name = "Slot")
        {
            var s = Add<UIIconSlot>(parent, name);
            s.Build(size);
            s.SetIcon(icon);
            return s;
        }

        /// <summary>Smooth gauge (HP/MP/TP/custom) with delayed trail and numeric text. <paramref name="height"/> is the bar thickness.</summary>
        public static UIGauge Gauge(Transform parent, UIGaugeKind kind, float width, float height = 14f, UIGaugeText text = UIGaugeText.Above, string name = null)
        {
            var g = Add<UIGauge>(parent, name ?? kind + " Gauge");
            g.Build(kind, width, height, text);
            return g;
        }

        /// <summary>Row of shield / break pips.</summary>
        public static UIPips Pips(Transform parent, int max, float pipSize = 22f, string name = "Pips")
        {
            var p = Add<UIPips>(parent, name);
            p.Build(max, pipSize);
            return p;
        }

        /// <summary>Circular gold-framed portrait with masked RawImage/Image slot.</summary>
        public static UIPortrait Portrait(Transform parent, float size, string name = "Portrait")
        {
            var p = Add<UIPortrait>(parent, name);
            p.Build(size);
            return p;
        }

        /// <summary>
        /// Selectable vertical list (icons, labels, right-aligned costs, disabled reasons, scrolling).
        /// Its height is <paramref name="visibleRows"/> × <paramref name="rowHeight"/>; set width via the RectTransform.
        /// </summary>
        public static UIList List(Transform parent, int visibleRows, float rowHeight = UITheme.RowHeight, float costWidth = 120f, string name = "List")
        {
            var l = Add<UIList>(parent, name);
            l.Build(visibleRows, rowHeight, costWidth);
            return l;
        }

        /// <summary>Tab strip with Q/E (shoulder) hints.</summary>
        public static UITabs Tabs(Transform parent, IList<string> labels, float tabWidth = 170f, float height = 54f, string name = "Tabs")
        {
            var t = Add<UITabs>(parent, name);
            t.Build(tabWidth, height);
            t.SetTabs(labels);
            return t;
        }

        /// <summary>Key-cap input hint ("[Z] 결정") that follows the active device.</summary>
        public static UIKeyHint KeyHint(Transform parent, UIAction action, string label, string name = null)
        {
            var k = Add<UIKeyHint>(parent, name ?? "Hint " + action);
            k.Build(action, label);
            return k;
        }

        /// <summary>Bottom dialog window with name plate, portrait slot, typewriter text and advance arrow.</summary>
        public static UIDialogBox DialogBox(Transform parent, string name = "DialogBox")
        {
            var d = Add<UIDialogBox>(parent, name);
            d.Build();
            return d;
        }

        /// <summary>Vertical ScrollRect with a masked viewport; add rows to <paramref name="content"/> (it has a VerticalLayoutGroup + fitter).</summary>
        public static ScrollRect ScrollView(Transform parent, out RectTransform content, float spacing = 6f, string name = "Scroll")
        {
            var root = Rect(parent, name);
            var sr = root.gameObject.AddComponent<ScrollRect>();
            var viewport = Rect(root, "Viewport").Stretch(0f, 0f, 18f, 0f);
            viewport.gameObject.AddComponent<RectMask2D>();
            var hit = viewport.gameObject.AddComponent<Image>();
            hit.color = Color.clear;
            content = Rect(viewport, "Content");
            content.anchorMin = new Vector2(0f, 1f);
            content.anchorMax = new Vector2(1f, 1f);
            content.pivot = new Vector2(0.5f, 1f);
            content.sizeDelta = Vector2.zero;
            var v = content.gameObject.AddComponent<VerticalLayoutGroup>();
            v.spacing = spacing;
            v.childControlWidth = true;
            v.childControlHeight = true;
            v.childForceExpandWidth = true;
            v.childForceExpandHeight = false;
            content.gameObject.AddComponent<ContentSizeFitter>().verticalFit = ContentSizeFitter.FitMode.PreferredSize;

            var bar = Rect(root, "Scrollbar");
            bar.anchorMin = new Vector2(1f, 0f);
            bar.anchorMax = Vector2.one;
            bar.pivot = new Vector2(1f, 0.5f);
            bar.offsetMin = new Vector2(-8f, 4f);
            bar.offsetMax = new Vector2(0f, -4f);
            var track = bar.gameObject.AddComponent<Image>();
            track.sprite = UISprites.BarFlat;
            track.type = UnityEngine.UI.Image.Type.Sliced;
            track.color = new Color(0f, 0f, 0.05f, 0.6f);
            var handle = Image(bar, UISprites.BarFlat, UITheme.Gold.WithAlpha(0.85f), "Handle", raycast: true);
            handle.rectTransform.Stretch();
            var sb = bar.gameObject.AddComponent<Scrollbar>();
            sb.direction = Scrollbar.Direction.BottomToTop;
            sb.handleRect = handle.rectTransform;
            sb.targetGraphic = handle;

            sr.viewport = viewport;
            sr.content = content;
            sr.horizontal = false;
            sr.vertical = true;
            sr.movementType = ScrollRect.MovementType.Clamped;
            sr.scrollSensitivity = 40f;
            sr.verticalScrollbar = sb;
            sr.verticalScrollbarVisibility = ScrollRect.ScrollbarVisibility.AutoHideAndExpandViewport;
            sr.verticalScrollbarSpacing = 6f;
            return sr;
        }

        /// <summary>Fixed-column grid layout.</summary>
        public static GridLayoutGroup Grid(Transform parent, Vector2 cellSize, Vector2 spacing, int columns, string name = "Grid")
        {
            var g = Add<GridLayoutGroup>(parent, name);
            g.cellSize = cellSize;
            g.spacing = spacing;
            g.constraint = GridLayoutGroup.Constraint.FixedColumnCount;
            g.constraintCount = Mathf.Max(1, columns);
            g.childAlignment = TextAnchor.UpperLeft;
            return g;
        }

        /// <summary>Vertical stack layout (children control their own heights via LayoutElement/preferred size).</summary>
        public static VerticalLayoutGroup VStack(Transform parent, float spacing = 8f, RectOffset padding = null, TextAnchor align = TextAnchor.UpperLeft, string name = "VStack")
        {
            var v = Add<VerticalLayoutGroup>(parent, name);
            v.spacing = spacing;
            v.padding = padding ?? new RectOffset();
            v.childAlignment = align;
            v.childControlWidth = true;
            v.childControlHeight = true;
            v.childForceExpandWidth = true;
            v.childForceExpandHeight = false;
            return v;
        }

        /// <summary>Horizontal stack layout.</summary>
        public static HorizontalLayoutGroup HStack(Transform parent, float spacing = 8f, RectOffset padding = null, TextAnchor align = TextAnchor.MiddleLeft, string name = "HStack")
        {
            var h = Add<HorizontalLayoutGroup>(parent, name);
            h.spacing = spacing;
            h.padding = padding ?? new RectOffset();
            h.childAlignment = align;
            h.childControlWidth = true;
            h.childControlHeight = true;
            h.childForceExpandWidth = false;
            h.childForceExpandHeight = false;
            return h;
        }

        /// <summary>Adds/updates a LayoutElement (negative = unset).</summary>
        public static LayoutElement Layout(Component c, float preferredWidth = -1f, float preferredHeight = -1f, float flexibleWidth = -1f, float flexibleHeight = -1f)
        {
            if (!c.TryGetComponent(out LayoutElement le)) le = c.gameObject.AddComponent<LayoutElement>();
            le.preferredWidth = preferredWidth;
            le.preferredHeight = preferredHeight;
            le.flexibleWidth = flexibleWidth;
            le.flexibleHeight = flexibleHeight;
            return le;
        }

        /// <summary>Excludes an element from parent layout groups.</summary>
        public static void IgnoreLayout(Component c)
        {
            if (!c.TryGetComponent(out LayoutElement le)) le = c.gameObject.AddComponent<LayoutElement>();
            le.ignoreLayout = true;
        }
    }
}
