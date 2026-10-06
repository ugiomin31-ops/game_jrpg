using TMPro;
using UnityEngine;
using UnityEngine.EventSystems;
using UnityEngine.UI;

namespace Abyss.UI
{
    /// <summary>
    /// Single shared tooltip (title, body, optional footer) positioned beside a RectTransform and clamped
    /// to the screen. Access via <see cref="UIRoot.Tooltip"/>; attach hover tooltips with <see cref="UITooltipTrigger.Attach"/>.
    /// </summary>
    public sealed class UITooltip : MonoBehaviour
    {
        const float Width = 440f;
        [SerializeField] UIPanel _panel;
        static readonly Vector3[] Corners = new Vector3[4];
        [SerializeField] TextMeshProUGUI _title, _body, _footer;
        [SerializeField] CanvasGroup _group;
        RectTransform _anchor;

        /// <summary>The tooltip target currently shown (null when hidden).</summary>
        public RectTransform Anchor => _anchor;

        internal void Build()
        {
            var rt = (RectTransform)transform;
            rt.Stretch();
            _group = gameObject.AddComponent<CanvasGroup>();
            _group.blocksRaycasts = false;
            _group.interactable = false;
            _panel = UIFactory.Panel(rt, UIPanelStyle.Tooltip, true, "Tip");
            _panel.Background.raycastTarget = false;
            _panel.Rect.anchorMin = _panel.Rect.anchorMax = new Vector2(0.5f, 0.5f);
            _panel.Rect.sizeDelta = new Vector2(Width, 100f);
            var v = _panel.gameObject.AddComponent<VerticalLayoutGroup>();
            v.padding = new RectOffset(22, 22, 16, 18);
            v.spacing = 6f;
            v.childControlWidth = v.childControlHeight = true;
            v.childForceExpandWidth = true;
            v.childForceExpandHeight = false;
            _panel.gameObject.AddComponent<ContentSizeFitter>().verticalFit = ContentSizeFitter.FitMode.PreferredSize;
            _title = UIFactory.Label(_panel.Rect, "", UITheme.SizeLabel - 2f, UIFont.Heavy, UITheme.GoldBright, TextAlignmentOptions.MidlineLeft, UITextFx.Shadow, "Title");
            _title.textWrappingMode = TextWrappingModes.Normal;
            _body = UIFactory.Paragraph(_panel.Rect, "", UITheme.SizeBody - 2f, UITheme.Text, "Body");
            _body.lineSpacing = 4f;
            _footer = UIFactory.Label(_panel.Rect, "", UITheme.SizeCaption, UIFont.Bold, UITheme.TextDim, TextAlignmentOptions.MidlineLeft, UITextFx.Shadow, "Footer");
            _footer.textWrappingMode = TextWrappingModes.Normal;
            _group.alpha = 0f;
            _panel.gameObject.SetActive(false);
        }

        /// <summary>Shows the tooltip beside <paramref name="anchor"/> (right side preferred, flips to fit).</summary>
        public void Show(string title, string body, RectTransform anchor, string footer = null)
        {
            _anchor = anchor;
            Fill(title, body, footer);
            if (anchor == null) return;
            anchor.GetWorldCorners(Corners);
            var self = (RectTransform)transform;
            Vector2 min = self.InverseTransformPoint(Corners[0]);
            Vector2 max = self.InverseTransformPoint(Corners[2]);
            Place(new Vector2(max.x + 14f, max.y), new Vector2(min.x - 14f, max.y));
        }

        /// <summary>Shows the tooltip at a canvas-local point of the overlay layer (pivot top-left).</summary>
        public void ShowAt(string title, string body, Vector2 localPoint, string footer = null)
        {
            _anchor = null;
            Fill(title, body, footer);
            Place(localPoint + new Vector2(18f, -18f), localPoint + new Vector2(-18f, -18f));
        }

        /// <summary>Hides the tooltip.</summary>
        public void Hide()
        {
            _anchor = null;
            UITween.Kill(_group);
            if (!Application.isPlaying) { _group.alpha = 0f; _panel.gameObject.SetActive(false); return; }
            UITween.Fade(_group, 0f, 0.1f).OnComplete(() => { if (_anchor == null && _panel != null) _panel.gameObject.SetActive(false); });
        }

        /// <summary>Hides only if currently anchored to <paramref name="anchor"/>.</summary>
        public void HideFor(RectTransform anchor)
        {
            if (_anchor == anchor) Hide();
        }

        void Fill(string title, string body, string footer)
        {
            _panel.gameObject.SetActive(true);
            _title.text = title ?? "";
            _title.gameObject.SetActive(!string.IsNullOrEmpty(title));
            _body.text = body ?? "";
            _body.gameObject.SetActive(!string.IsNullOrEmpty(body));
            _footer.text = footer ?? "";
            _footer.gameObject.SetActive(!string.IsNullOrEmpty(footer));
            LayoutRebuilder.ForceRebuildLayoutImmediate(_panel.Rect);
            UITween.Kill(_group);
            if (Application.isPlaying) UITween.Fade(_group, 1f, 0.12f);
            else _group.alpha = 1f;
        }

        /// <summary>Places the top-left corner at <paramref name="right"/>, or the top-right at <paramref name="left"/> when it would overflow.</summary>
        void Place(Vector2 right, Vector2 left)
        {
            var self = ((RectTransform)transform).rect;
            var size = _panel.Rect.rect.size;
            bool flip = right.x + size.x > self.xMax - 12f;
            _panel.Rect.pivot = flip ? new Vector2(1f, 1f) : new Vector2(0f, 1f);
            var p = flip ? left : right;
            float minX = flip ? self.xMin + 12f + size.x : self.xMin + 12f;
            float maxX = flip ? self.xMax - 12f : self.xMax - 12f - size.x;
            p.x = Mathf.Clamp(p.x, minX, Mathf.Max(minX, maxX));
            p.y = Mathf.Clamp(p.y, self.yMin + 12f + size.y, self.yMax - 12f);
            _panel.Rect.anchoredPosition = p;
        }
    }

    /// <summary>Shows the root tooltip while the pointer hovers this element.</summary>
    public sealed class UITooltipTrigger : MonoBehaviour, IPointerEnterHandler, IPointerExitHandler
    {
        /// <summary>Tooltip title.</summary>
        public string Title;
        /// <summary>Tooltip body.</summary>
        [TextArea] public string Body;
        /// <summary>Optional footer (cost, target…).</summary>
        public string Footer;

        /// <summary>Adds (or updates) a hover tooltip on <paramref name="target"/> (needs a raycast-target graphic).</summary>
        public static UITooltipTrigger Attach(Component target, string title, string body, string footer = null)
        {
            if (!target.TryGetComponent(out UITooltipTrigger t)) t = target.gameObject.AddComponent<UITooltipTrigger>();
            t.Title = title;
            t.Body = body;
            t.Footer = footer;
            return t;
        }

        /// <inheritdoc/>
        public void OnPointerEnter(PointerEventData e)
        {
            if (!UIInput.CanReceive(this)) return;
            var root = UIRoot.Instance;
            if (root != null) root.Tooltip.Show(Title, Body, (RectTransform)transform, Footer);
        }

        /// <inheritdoc/>
        public void OnPointerExit(PointerEventData e)
        {
            var root = UIRoot.Instance;
            if (root != null) root.Tooltip.HideFor((RectTransform)transform);
        }

        void OnDisable()
        {
            var root = UIRoot.Instance;
            if (root != null && root.Tooltip != null) root.Tooltip.HideFor((RectTransform)transform);
        }
    }
}
