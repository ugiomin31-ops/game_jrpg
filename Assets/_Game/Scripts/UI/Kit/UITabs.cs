using System;
using System.Collections.Generic;
using TMPro;
using UnityEngine;
using UnityEngine.EventSystems;
using UnityEngine.UI;

namespace Abyss.UI
{
    /// <summary>
    /// Horizontal tab strip flanked by Q/E (LB/RB) key hints. Tab switching wraps; mouse clicks select.
    /// Create with <see cref="UIFactory.Tabs"/>.
    /// </summary>
    public sealed class UITabs : MonoBehaviour
    {
        [SerializeField] float _tabWidth, _height;
        [SerializeField] RectTransform _strip;
        readonly List<(Image bg, TextMeshProUGUI label)> _tabs = new List<(Image, TextMeshProUGUI)>();
        int _index;

        /// <summary>Raised when the active tab changes (by input or <see cref="Select"/> with notify).</summary>
        public event Action<int> Changed;

        /// <summary>Active tab index.</summary>
        public int Index => _index;
        /// <summary>Number of tabs.</summary>
        public int Count => _tabs.Count;
        /// <summary>When false, Q/E and shoulders are ignored.</summary>
        public bool InputEnabled { get; set; } = true;

        internal void Build(float tabWidth, float height)
        {
            _tabWidth = tabWidth;
            _height = height;
            var rt = (RectTransform)transform;
            var h = gameObject.AddComponent<HorizontalLayoutGroup>();
            h.spacing = 12f;
            h.childAlignment = TextAnchor.MiddleCenter;
            h.childControlWidth = h.childControlHeight = false;
            h.childForceExpandWidth = h.childForceExpandHeight = false;
            UIFactory.KeyHint(rt, UIAction.TabPrev, "", "PrevHint");
            _strip = UIFactory.Rect(rt, "Strip");
            var sh = _strip.gameObject.AddComponent<HorizontalLayoutGroup>();
            sh.spacing = 4f;
            sh.childAlignment = TextAnchor.LowerCenter;
            sh.childControlWidth = sh.childControlHeight = false;
            sh.childForceExpandWidth = sh.childForceExpandHeight = false;
            UIFactory.KeyHint(rt, UIAction.TabNext, "", "NextHint");
        }

        /// <summary>Replaces the tab labels (keeps the index when still valid).</summary>
        public void SetTabs(IList<string> labels)
        {
            for (int i = _strip.childCount - 1; i >= 0; i--)
            {
                var c = _strip.GetChild(i).gameObject;
                if (Application.isPlaying) Destroy(c); else DestroyImmediate(c);
            }
            _tabs.Clear();
            int n = labels?.Count ?? 0;
            for (int i = 0; i < n; i++)
            {
                var bg = UIFactory.Image(_strip, UISprites.TabInactive, Color.white, "Tab " + labels[i], raycast: true);
                bg.rectTransform.sizeDelta = new Vector2(_tabWidth, _height);
                var label = UIFactory.Label(bg.transform, labels[i], UITheme.SizeLabel - 2f, UIFont.Bold, UITheme.TextDim, TextAlignmentOptions.Center);
                label.rectTransform.Stretch(8f, 2f, 8f, 4f);
                label.enableAutoSizing = true;
                label.fontSizeMin = 19f;
                label.fontSizeMax = UITheme.SizeLabel - 2f;
                label.overflowMode = TextOverflowModes.Ellipsis;
                var click = bg.gameObject.AddComponent<UITabClick>();
                click.Tabs = this;
                click.TabIndex = i;
                _tabs.Add((bg, label));
            }
            float stripW = n * _tabWidth + Mathf.Max(0, n - 1) * 4f;
            _strip.sizeDelta = new Vector2(stripW, _height);
            ((RectTransform)transform).sizeDelta = new Vector2(stripW + 2f * (36f + 12f), _height);
            _index = Mathf.Clamp(_index, 0, Mathf.Max(0, n - 1));
            Render(true);
        }

        /// <summary>Activates a tab (wraps). <paramref name="notify"/> raises <see cref="Changed"/> and plays the tab sound.</summary>
        public void Select(int index, bool notify = true)
        {
            if (_tabs.Count == 0) return;
            index = (index % _tabs.Count + _tabs.Count) % _tabs.Count;
            if (index == _index) return;
            _index = index;
            Render(false);
            if (!notify) return;
            UISound.Play(UISoundId.Tab);
            Changed?.Invoke(_index);
        }

        void Update()
        {
            if (!InputEnabled || _tabs.Count < 2 || !UIInput.CanReceive(this)) return;
            if (UIInput.TabPrev) { Select(_index - 1); UIInput.Consume(); }
            else if (UIInput.TabNext) { Select(_index + 1); UIInput.Consume(); }
        }

        void Render(bool instant)
        {
            for (int i = 0; i < _tabs.Count; i++)
            {
                var (bg, label) = _tabs[i];
                bool on = i == _index;
                bg.sprite = on ? UISprites.TabActive : UISprites.TabInactive;
                label.color = on ? UITheme.GoldBright : UITheme.TextDim;
                float h = on ? _height + 6f : _height;
                UITween.Kill(bg.rectTransform);
                if (instant || !Application.isPlaying || (UIRoot.Instance != null && UIRoot.Instance.ReducedMotion)) bg.rectTransform.sizeDelta = new Vector2(_tabWidth, h);
                else
                {
                    var rt = bg.rectTransform;
                    float from = rt.sizeDelta.y;
                    UITween.To(rt, 0.16f, p => rt.sizeDelta = new Vector2(_tabWidth, Mathf.LerpUnclamped(from, h, p)), UIEase.OutBack);
                }
            }
        }

        internal void OnTabClicked(int i)
        {
            if (UIInput.CanReceive(this)) Select(i);
        }
    }

    /// <summary>Pointer relay for a tab (internal plumbing).</summary>
    [AddComponentMenu("")]
    public sealed class UITabClick : MonoBehaviour, IPointerClickHandler
    {
        internal UITabs Tabs;
        internal int TabIndex;

        /// <inheritdoc/>
        public void OnPointerClick(PointerEventData e)
        {
            if (e.button == PointerEventData.InputButton.Left) Tabs.OnTabClicked(TabIndex);
        }
    }
}
