using UnityEngine;
using UnityEngine.UI;

namespace Abyss.UI
{
    /// <summary>
    /// Flat convex polygon drawn from normalised points (0..1 of the rect, y up): arrow keys, compass pointers, blade
    /// tips. No sprite or material; pointer hits follow the outline when <see cref="Graphic.raycastTarget"/> is on.
    /// </summary>
    [AddComponentMenu(""), RequireComponent(typeof(CanvasRenderer))]
    public sealed class UIPolygon : MaskableGraphic, ICanvasRaycastFilter
    {
        Vector2[] _points = { new Vector2(0f, 0f), new Vector2(0.5f, 1f), new Vector2(1f, 0f) };

        /// <summary>Upward pentagon (arrow key): apex at the top, shoulders at <paramref name="shoulder"/> of the height.</summary>
        public static Vector2[] Pentagon(float shoulder = 0.66f) =>
            new[] { new Vector2(0.5f, 1f), new Vector2(1f, shoulder), new Vector2(1f, 0f), new Vector2(0f, 0f), new Vector2(0f, shoulder) };

        /// <summary>Downward triangle (pointer under a strip).</summary>
        public static Vector2[] Down => new[] { new Vector2(0f, 1f), new Vector2(1f, 1f), new Vector2(0.5f, 0f) };

        /// <summary>Upward chevron outline is not convex, so arrows use two polygons; this is a filled up triangle.</summary>
        public static Vector2[] Up => new[] { new Vector2(0f, 0f), new Vector2(0.5f, 1f), new Vector2(1f, 0f) };

        /// <summary>Creates a polygon under <paramref name="parent"/>.</summary>
        public static UIPolygon Create(Transform parent, string name, Vector2[] points, Color color, bool raycast = false)
        {
            var p = UIFactory.Add<UIPolygon>(parent, name);
            p.color = color;
            p.raycastTarget = raycast;
            p.SetPoints(points);
            return p;
        }

        /// <summary>Replaces the outline (convex, any winding).</summary>
        public void SetPoints(Vector2[] points)
        {
            if (points == null || points.Length < 3) return;
            _points = (Vector2[])points.Clone();
            SetVerticesDirty();
        }

        /// <inheritdoc/>
        protected override void OnPopulateMesh(VertexHelper vh)
        {
            vh.Clear();
            Rect r = rectTransform.rect;
            Color32 c = color;
            for (int i = 0; i < _points.Length; i++)
                vh.AddVert(new Vector3(r.xMin + _points[i].x * r.width, r.yMin + _points[i].y * r.height), c, Vector2.zero);
            for (int i = 1; i < _points.Length - 1; i++) vh.AddTriangle(0, i, i + 1);
        }

        /// <inheritdoc/>
        public bool IsRaycastLocationValid(Vector2 screenPoint, Camera eventCamera)
        {
            if (!RectTransformUtility.ScreenPointToLocalPointInRectangle(rectTransform, screenPoint, eventCamera, out var local)) return false;
            Rect r = rectTransform.rect;
            if (r.width <= 0f || r.height <= 0f) return false;
            var p = new Vector2((local.x - r.xMin) / r.width, (local.y - r.yMin) / r.height);
            // Inside a convex polygon: the point is on the same side of every edge.
            float sign = 0f;
            for (int i = 0; i < _points.Length; i++)
            {
                Vector2 a = _points[i], b = _points[(i + 1) % _points.Length];
                float cross = (b.x - a.x) * (p.y - a.y) - (b.y - a.y) * (p.x - a.x);
                if (Mathf.Abs(cross) < 1e-6f) continue;
                if (sign == 0f) sign = Mathf.Sign(cross);
                else if (Mathf.Sign(cross) != sign) return false;
            }
            return true;
        }
    }
}
