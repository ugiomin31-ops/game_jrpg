using System;
using System.Collections.Generic;
using TMPro;
using UnityEngine;
using UnityEngine.EventSystems;
using UnityEngine.UI;

namespace Abyss.UI
{
    /// <summary>One row of a <see cref="UIList"/>.</summary>
    public sealed class UIListItem
    {
        /// <summary>Main text.</summary>
        public string Label;
        /// <summary>Right-aligned cost / value column ("MP 12", "×3", "120G"); null hides it.</summary>
        public string Cost;
        /// <summary>Cost colour override (defaults to gold-white).</summary>
        public Color? CostColor;
        /// <summary>Leading icon (optional).</summary>
        public Sprite Icon;
        /// <summary>Disabled rows can be highlighted but not submitted (buzzer).</summary>
        public bool Enabled = true;
        /// <summary>Why the row is disabled, shown beneath its label and in the owner's detail pane.</summary>
        public string DisabledReason;
        /// <summary>Long description for tooltips / help panes (not rendered by the list).</summary>
        public string Description;
        /// <summary>Label colour override.</summary>
        public Color? LabelColor;
        /// <summary>Free payload for the owner (skill id, item def…).</summary>
        public object Tag;

        /// <summary>Creates an item.</summary>
        public UIListItem(string label, string cost = null, bool enabled = true, string disabledReason = null, Sprite icon = null, object tag = null)
        {
            Label = label;
            Cost = cost;
            Enabled = enabled;
            DisabledReason = disabledReason;
            Icon = icon;
            Tag = tag;
        }
    }

    /// <summary>
    /// Vertical selectable list with a fixed number of visible rows, scrolling, wrap-around keyboard/gamepad
    /// navigation (hold to repeat), mouse hover/click/wheel, disabled rows with reasons, icon and cost columns.
    /// Input is polled only while <see cref="Focused"/> and under the top <see cref="UIInput"/> layer.
    /// Cancel is NOT handled here (screens own it). Create with <see cref="UIFactory.List"/>.
    /// </summary>
    public sealed class UIList : MonoBehaviour, IScrollHandler
    {
        sealed class Row
        {
            public RectTransform Rect;
            public Image Highlight, Icon;
            public TextMeshProUGUI Label, Reason, Cost;
            public UIListRowHandler Handler;
        }

        [SerializeField] float _rowHeight;
        [SerializeField] float _costWidth;
        [SerializeField] int _visibleRows;
        [SerializeField] RectTransform _rowsRoot, _cursor, _scrollTrack, _scrollThumb;
        [SerializeField] Image _arrowUp, _arrowDown;
        [SerializeField] TextMeshProUGUI _empty;
        readonly List<Row> _rows = new List<Row>();
        readonly List<UIListItem> _items = new List<UIListItem>();
        int _selected, _top;
        bool _focused = true;
        float _cursorY;

        /// <summary>Raised when the highlighted row changes (index, item).</summary>
        public event Action<int, UIListItem> SelectionChanged;
        /// <summary>Raised when an enabled row is confirmed (keyboard/gamepad confirm or click).</summary>
        public event Action<int, UIListItem> Submitted;
        /// <summary>Raised when a disabled row is confirmed (a buzzer already played).</summary>
        public event Action<int, UIListItem> Rejected;

        /// <summary>Current items (read-only view).</summary>
        public IReadOnlyList<UIListItem> Items => _items;
        /// <summary>Highlighted item or null when empty.</summary>
        public UIListItem Selected => _selected >= 0 && _selected < _items.Count ? _items[_selected] : null;
        /// <summary>Wrap from last to first row and vice versa.</summary>
        public bool Wrap { get; set; } = true;
        /// <summary>Text shown when the list has no items.</summary>
        public string EmptyText { get => _empty.text; set => _empty.text = value; }

        /// <summary>Whether this list reacts to keyboard/gamepad and shows its cursor.</summary>
        public bool Focused
        {
            get => _focused;
            set { _focused = value; Render(); }
        }

        /// <summary>Highlighted index (-1 when empty). Setting scrolls it into view (no sound / event).</summary>
        public int SelectedIndex
        {
            get => _items.Count == 0 ? -1 : _selected;
            set => Select(value, false, false);
        }

        internal void Build(int visibleRows, float rowHeight, float costWidth)
        {
            _visibleRows = Mathf.Max(1, visibleRows);
            _rowHeight = rowHeight;
            _costWidth = costWidth;
            var rt = (RectTransform)transform;
            rt.sizeDelta = new Vector2(560f, _visibleRows * rowHeight);
            var hit = gameObject.AddComponent<Image>();
            hit.color = Color.clear;

            _rowsRoot = UIFactory.Rect(rt, "Rows").Stretch(28f, 0f, 14f, 0f);
            for (int i = 0; i < _visibleRows; i++) _rows.Add(BuildRow(i));

            var cursorImg = UIFactory.Image(rt, UISprites.Cursor, Color.white, "Cursor");
            _cursor = cursorImg.rectTransform;
            _cursor.anchorMin = _cursor.anchorMax = new Vector2(0f, 1f);
            _cursor.pivot = new Vector2(0.5f, 0.5f);
            _cursor.sizeDelta = new Vector2(40f, 40f);

            _scrollTrack = UIFactory.Image(rt, UISprites.BarFlat, new Color(0f, 0f, 0.04f, 0.55f), "ScrollTrack").rectTransform;
            _scrollTrack.anchorMin = new Vector2(1f, 0f);
            _scrollTrack.anchorMax = new Vector2(1f, 1f);
            _scrollTrack.pivot = new Vector2(1f, 0.5f);
            _scrollTrack.offsetMin = new Vector2(-5f, 14f);
            _scrollTrack.offsetMax = new Vector2(0f, -14f);
            _scrollThumb = UIFactory.Image(_scrollTrack, UISprites.BarFlat, UITheme.Gold, "Thumb").rectTransform;
            _scrollThumb.anchorMin = new Vector2(0f, 0f);
            _scrollThumb.anchorMax = new Vector2(1f, 1f);
            _scrollThumb.offsetMin = _scrollThumb.offsetMax = Vector2.zero;

            _arrowUp = UIFactory.Image(rt, UISprites.ArrowDown, Color.white, "MoreAbove");
            _arrowUp.rectTransform.Place(UIAnchor.Top, new Vector2(0f, 14f), new Vector2(26f, 26f));
            _arrowUp.rectTransform.localEulerAngles = new Vector3(0f, 0f, 180f);
            _arrowDown = UIFactory.Image(rt, UISprites.ArrowDown, Color.white, "MoreBelow");
            _arrowDown.rectTransform.Place(UIAnchor.Bottom, new Vector2(0f, -14f), new Vector2(26f, 26f));

            _empty = UIFactory.Label(rt, "(없음)", UITheme.SizeBody, UIFont.Bold, UITheme.TextDisabled, TextAlignmentOptions.Center);
            _empty.rectTransform.TopStrip(rowHeight);
            Render();
        }

        Row BuildRow(int i)
        {
            var r = new Row();
            r.Rect = UIFactory.Rect(_rowsRoot, "Row " + i);
            r.Rect.TopStrip(_rowHeight - 4f, i * _rowHeight + 2f);
            var hit = r.Rect.gameObject.AddComponent<Image>();
            hit.color = Color.clear;
            r.Handler = r.Rect.gameObject.AddComponent<UIListRowHandler>();
            r.Handler.List = this;
            r.Handler.Slot = i;
            r.Highlight = UIFactory.Image(r.Rect, UISprites.RowHighlight, Color.white, "Highlight");
            r.Highlight.rectTransform.Stretch(-6f, 0f, 0f, 0f);
            float iconSize = Mathf.Min(40f, _rowHeight - 14f);
            r.Icon = UIFactory.Icon(r.Rect, null, iconSize);
            r.Icon.rectTransform.Place(UIAnchor.Left, new Vector2(10f, 0f), new Vector2(iconSize, iconSize));
            r.Label = UIFactory.Label(r.Rect, "", UITheme.SizeLabel, UIFont.Bold, UITheme.Text, TextAlignmentOptions.MidlineLeft, UITextFx.Shadow, "Label");
            r.Label.overflowMode = TextOverflowModes.Ellipsis;
            r.Reason = UIFactory.Label(r.Rect, "", UITheme.SizeCaption, UIFont.Bold, UITheme.Danger, TextAlignmentOptions.MidlineRight, UITextFx.Shadow, "Reason");
            r.Reason.alignment = TextAlignmentOptions.MidlineLeft;
            r.Reason.overflowMode = TextOverflowModes.Ellipsis;
            r.Cost = UIFactory.Label(r.Rect, "", UITheme.SizeLabel - 2f, UIFont.Heavy, UITheme.Text, TextAlignmentOptions.MidlineRight, UITextFx.Shadow, "Cost");
            r.Cost.overflowMode = TextOverflowModes.Ellipsis;
            r.Cost.rectTransform.anchorMin = new Vector2(1f, 0f);
            r.Cost.rectTransform.anchorMax = new Vector2(1f, 1f);
            r.Cost.rectTransform.pivot = new Vector2(1f, 0.5f);
            r.Cost.rectTransform.offsetMin = new Vector2(-_costWidth, 0f);
            r.Cost.rectTransform.offsetMax = new Vector2(-14f, 0f);
            return r;
        }

        /// <summary>Replaces all items and highlights <paramref name="select"/> (clamped).</summary>
        public void SetItems(IEnumerable<UIListItem> items, int select = 0)
        {
            _items.Clear();
            if (items != null) _items.AddRange(items);
            _top = 0;
            _selected = -1;
            Select(Mathf.Clamp(select, 0, Mathf.Max(0, _items.Count - 1)), false, true);
        }

        /// <summary>Re-renders rows after mutating items in place.</summary>
        public void Refresh() => Render();

        /// <summary>Highlights an index, scrolling it into view.</summary>
        public void Select(int index, bool playSound, bool raiseEvent = true)
        {
            if (_items.Count == 0) { _selected = 0; Render(); return; }
            index = Mathf.Clamp(index, 0, _items.Count - 1);
            bool changed = index != _selected;
            _selected = index;
            if (_selected < _top) _top = _selected;
            else if (_selected >= _top + _visibleRows) _top = _selected - _visibleRows + 1;
            _top = Mathf.Clamp(_top, 0, Mathf.Max(0, _items.Count - _visibleRows));
            if (changed && playSound) UISound.Play(UISoundId.Move);
            Render();
            if (changed && raiseEvent) SelectionChanged?.Invoke(_selected, _items[_selected]);
        }

        /// <summary>Confirms the highlighted row as if the player pressed confirm.</summary>
        public void Submit()
        {
            var item = Selected;
            if (item == null) return;
            UIInput.Consume();
            if (item.Enabled)
            {
                UISound.Play(UISoundId.Confirm);
                PunchRow();
                Submitted?.Invoke(_selected, item);
            }
            else
            {
                UISound.Play(UISoundId.Buzzer);
                ShakeCursor();
                Rejected?.Invoke(_selected, item);
            }
        }

        /// <summary>Scrolls the window by <paramref name="rows"/> keeping the selection visible.</summary>
        public void ScrollBy(int rows)
        {
            int max = Mathf.Max(0, _items.Count - _visibleRows);
            int top = Mathf.Clamp(_top + rows, 0, max);
            if (top == _top) return;
            _top = top;
            int sel = Mathf.Clamp(_selected, _top, _top + _visibleRows - 1);
            if (sel != _selected) Select(sel, true);
            else Render();
        }

        void Update()
        {
            if (_cursor == null) return;
            // Cursor glide + idle bob.
            bool reduced = UIRoot.Instance != null && UIRoot.Instance.ReducedMotion;
            float targetY = -(_selected - _top + 0.5f) * _rowHeight;
            _cursorY = reduced ? targetY : Mathf.Lerp(_cursorY, targetY, 1f - Mathf.Exp(-Time.unscaledDeltaTime * 22f));
            float bob = reduced ? 0f : Mathf.Sin(Time.unscaledTime * 6f) * 2f;
            _cursor.anchoredPosition = new Vector2(10f + bob, _cursorY);

            if (!_focused || _items.Count == 0 || !UIInput.CanReceive(this)) return;
            int step = UIInput.NavigateRows;
            if (step != 0)
            {
                int next = _selected + step;
                if (Wrap && _items.Count > 1)
                {
                    if (next < 0) next = _items.Count - 1;
                    else if (next >= _items.Count) next = 0;
                }
                Select(next, true);
            }
            if (UIInput.Confirm)
            {
                UIInput.Consume();
                Submit();
            }
        }

        void Render()
        {
            if (_rows.Count == 0) return;
            for (int i = 0; i < _rows.Count; i++)
            {
                var r = _rows[i];
                int idx = _top + i;
                bool has = idx < _items.Count;
                r.Rect.gameObject.SetActive(has);
                if (!has) continue;
                var it = _items[idx];
                bool sel = idx == _selected;
                r.Highlight.enabled = sel;
                r.Highlight.color = _focused ? Color.white : new Color(0.75f, 0.8f, 1f, 0.45f);
                bool icon = it.Icon != null;
                r.Icon.sprite = it.Icon;
                r.Icon.enabled = icon;
                r.Icon.color = it.Enabled ? Color.white : new Color(0.55f, 0.55f, 0.6f, 0.65f);

                r.Cost.text = it.Cost ?? "";
                r.Cost.color = !it.Enabled ? UITheme.TextDisabled : it.CostColor ?? UITheme.GoldBright;
                bool hasCost = !string.IsNullOrEmpty(it.Cost);
                float right = hasCost ? _costWidth + 6f : 14f;
                string reason = it.Enabled ? "" : it.DisabledReason ?? "";
                r.Reason.text = reason;
                float left = icon ? 10f + r.Icon.rectTransform.sizeDelta.x + 12f : 16f;
                if (reason.Length > 0)
                {
                    r.Label.rectTransform.TopStrip((_rowHeight - 4f) * 0.57f, 0f, left, right + 6f);
                    r.Reason.rectTransform.BottomStrip((_rowHeight - 4f) * 0.43f, 0f, left, right + 6f);
                }
                else
                {
                    r.Label.rectTransform.Stretch(left, 0f, right + 6f, 0f);
                    r.Reason.rectTransform.BottomStrip(0f);
                }
                r.Label.text = it.Label;
                r.Label.color = !it.Enabled ? UITheme.TextDisabled : sel && _focused ? UITheme.DawnBright : it.LabelColor ?? UITheme.Text;
            }
            _empty.gameObject.SetActive(_items.Count == 0);
            _cursor.gameObject.SetActive(_focused && _items.Count > 0);
            if (!Application.isPlaying || _cursorY == 0f)
            {
                _cursorY = -(_selected - _top + 0.5f) * _rowHeight;
                _cursor.anchoredPosition = new Vector2(10f, _cursorY);
            }

            bool scrolls = _items.Count > _visibleRows;
            _scrollTrack.gameObject.SetActive(scrolls);
            _arrowUp.enabled = scrolls && _top > 0;
            _arrowDown.enabled = scrolls && _top + _visibleRows < _items.Count;
            if (scrolls)
            {
                float size = (float)_visibleRows / _items.Count;
                float pos = (float)_top / (_items.Count - _visibleRows);
                _scrollThumb.anchorMin = new Vector2(0f, (1f - size) * (1f - pos));
                _scrollThumb.anchorMax = new Vector2(1f, (1f - size) * (1f - pos) + size);
            }
        }

        void PunchRow()
        {
            if (!Application.isPlaying || (UIRoot.Instance != null && UIRoot.Instance.ReducedMotion)) return;
            var row = _rows[_selected - _top].Rect;
            UITween.Kill(row);
            row.localScale = new Vector3(1.035f, 1.035f, 1f);
            UITween.Scale(row, 1f, 0.22f, UIEase.OutBack);
        }

        void ShakeCursor()
        {
            if (!Application.isPlaying || (UIRoot.Instance != null && UIRoot.Instance.ReducedMotion)) return;
            var label = _rows[_selected - _top].Label.rectTransform;
            var basePos = label.anchoredPosition;
            UITween.Kill(label);
            UITween.To(label, 0.28f, p => label.anchoredPosition = basePos + new Vector2(Mathf.Sin(p * Mathf.PI * 6f) * 7f * (1f - p), 0f), UIEase.Linear);
        }

        internal void OnRowHover(int slot)
        {
            int idx = _top + slot;
            if (idx < _items.Count && idx != _selected && UIInput.CanReceive(this)) Select(idx, true);
        }

        internal void OnRowClick(int slot)
        {
            int idx = _top + slot;
            if (idx >= _items.Count || !UIInput.CanReceive(this)) return;
            Select(idx, false);
            Submit();
        }

        /// <inheritdoc/>
        public void OnScroll(PointerEventData e)
        {
            if (!UIInput.CanReceive(this)) return;
            if (e.scrollDelta.y > 0f) ScrollBy(-1);
            else if (e.scrollDelta.y < 0f) ScrollBy(1);
        }
    }

    /// <summary>Pointer relay for a <see cref="UIList"/> row (internal plumbing).</summary>
    [AddComponentMenu("")]
    public sealed class UIListRowHandler : MonoBehaviour, IPointerEnterHandler, IPointerClickHandler
    {
        internal UIList List;
        internal int Slot;

        /// <inheritdoc/>
        public void OnPointerEnter(PointerEventData e) => List.OnRowHover(Slot);

        /// <inheritdoc/>
        public void OnPointerClick(PointerEventData e)
        {
            if (e.button == PointerEventData.InputButton.Left) List.OnRowClick(Slot);
        }
    }
}
