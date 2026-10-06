using UnityEngine;

namespace Abyss.UI
{
    /// <summary>Nine anchor presets for <see cref="UIRect.Place"/>.</summary>
    public enum UIAnchor { TopLeft, Top, TopRight, Left, Center, Right, BottomLeft, Bottom, BottomRight }

    /// <summary>Fluent RectTransform layout helpers (all return the same RectTransform).</summary>
    public static class UIRect
    {
        /// <summary>The component's RectTransform (UI objects only).</summary>
        public static RectTransform Rt(this Component c) => (RectTransform)c.transform;

        /// <summary>Stretches to fill the parent with the given insets (pixels at reference resolution).</summary>
        public static RectTransform Stretch(this RectTransform rt, float left = 0f, float top = 0f, float right = 0f, float bottom = 0f)
        {
            rt.anchorMin = Vector2.zero;
            rt.anchorMax = Vector2.one;
            rt.pivot = new Vector2(0.5f, 0.5f);
            rt.offsetMin = new Vector2(left, bottom);
            rt.offsetMax = new Vector2(-right, -top);
            return rt;
        }

        /// <summary>Stretches to fill the parent expanded by <paramref name="outset"/> on every side.</summary>
        public static RectTransform Outset(this RectTransform rt, float outset) => rt.Stretch(-outset, -outset, -outset, -outset);

        /// <summary>
        /// Anchors and pivots at a preset point of the parent, then offsets by <paramref name="pos"/>
        /// (+x right, +y up) with a fixed <paramref name="size"/>.
        /// </summary>
        public static RectTransform Place(this RectTransform rt, UIAnchor anchor, Vector2 pos, Vector2 size)
        {
            var a = AnchorPoint(anchor);
            rt.anchorMin = rt.anchorMax = a;
            rt.pivot = a;
            rt.sizeDelta = size;
            rt.anchoredPosition = pos;
            return rt;
        }

        /// <summary>Anchors to a preset point with a custom pivot.</summary>
        public static RectTransform Place(this RectTransform rt, UIAnchor anchor, Vector2 pivot, Vector2 pos, Vector2 size)
        {
            rt.anchorMin = rt.anchorMax = AnchorPoint(anchor);
            rt.pivot = pivot;
            rt.sizeDelta = size;
            rt.anchoredPosition = pos;
            return rt;
        }

        /// <summary>Spans the parent's width at the top (height fixed), inset horizontally.</summary>
        public static RectTransform TopStrip(this RectTransform rt, float height, float y = 0f, float left = 0f, float right = 0f)
        {
            rt.anchorMin = new Vector2(0f, 1f);
            rt.anchorMax = new Vector2(1f, 1f);
            rt.pivot = new Vector2(0.5f, 1f);
            rt.offsetMin = new Vector2(left, -y - height);
            rt.offsetMax = new Vector2(-right, -y);
            return rt;
        }

        /// <summary>Spans the parent's width at the bottom (height fixed), inset horizontally.</summary>
        public static RectTransform BottomStrip(this RectTransform rt, float height, float y = 0f, float left = 0f, float right = 0f)
        {
            rt.anchorMin = new Vector2(0f, 0f);
            rt.anchorMax = new Vector2(1f, 0f);
            rt.pivot = new Vector2(0.5f, 0f);
            rt.offsetMin = new Vector2(left, y);
            rt.offsetMax = new Vector2(-right, y + height);
            return rt;
        }

        /// <summary>Sets sizeDelta.</summary>
        public static RectTransform Size(this RectTransform rt, float width, float height)
        {
            rt.sizeDelta = new Vector2(width, height);
            return rt;
        }

        /// <summary>Normalised anchor of a preset.</summary>
        public static Vector2 AnchorPoint(UIAnchor anchor)
        {
            int i = (int)anchor;
            return new Vector2((i % 3) * 0.5f, 1f - (i / 3) * 0.5f);
        }
    }
}
