using System;
using System.Collections.Generic;
using UnityEngine;

namespace Abyss.UI
{
    /// <summary>
    /// Base class for full screens and windows managed by <see cref="UIScreenStack"/>.
    /// Override <see cref="Build"/> to create content with <see cref="UIFactory"/> (called once, after any setup
    /// callback passed to <see cref="UIScreenStack.Push{T}"/>). The screen root stretches over the screens layer.
    /// </summary>
    [RequireComponent(typeof(CanvasGroup))]
    public abstract class UIScreen : MonoBehaviour
    {
        bool _built;

        /// <summary>Owning stack (null when not pushed).</summary>
        public UIScreenStack Stack { get; internal set; }
        /// <summary>Root RectTransform (full-screen stretch).</summary>
        public RectTransform Rect => (RectTransform)transform;
        /// <summary>CanvasGroup used for fades and input blocking.</summary>
        public CanvasGroup Group { get; private set; }
        /// <summary>True when this is the top screen of its stack.</summary>
        public bool IsTop => Stack != null && Stack.Top == this;
        /// <summary>True between push and pop.</summary>
        public bool IsOpen { get; internal set; }

        /// <summary>Hide this screen while another is stacked on top (default: stay visible, non-interactive).</summary>
        public virtual bool HideWhenCovered => false;
        /// <summary>Cancel (Esc/X/B/right click) closes the screen by default.</summary>
        public virtual bool CloseOnCancel => true;
        /// <summary>Destroy the GameObject after it is popped (false = keep for reuse with <see cref="UIScreenStack.Push(UIScreen)"/>).</summary>
        public virtual bool DestroyOnClose => true;

        /// <summary>Creates the screen's content (called once).</summary>
        protected abstract void Build();
        /// <summary>Called right after the screen is pushed (before the in-animation).</summary>
        protected virtual void OnOpen() { }
        /// <summary>Called when the screen is popped (before the out-animation).</summary>
        protected virtual void OnClose() { }
        /// <summary>Called when the screen becomes the top of the stack (also after <see cref="OnOpen"/>).</summary>
        protected virtual void OnFocus() { }
        /// <summary>Called when another screen is pushed on top.</summary>
        protected virtual void OnBlur() { }

        /// <summary>Handles cancel input while top. Default closes when <see cref="CloseOnCancel"/>.</summary>
        protected virtual void OnCancel()
        {
            if (!CloseOnCancel) return;
            UISound.Play(UISoundId.Cancel);
            Close();
        }

        /// <summary>In-animation: fade + rise. Override for custom transitions.</summary>
        protected virtual UITween AnimateIn()
        {
            Group.alpha = 0f;
            Rect.anchoredPosition = UIRoot.Instance != null && UIRoot.Instance.ReducedMotion ? Vector2.zero : new Vector2(0f, -18f);
            UITween.Move(Rect, Vector2.zero, UIRoot.Instance != null && UIRoot.Instance.ReducedMotion ? 0f : 0.22f, UIEase.OutCubic);
            return UITween.Fade(Group, 1f, 0.22f, UIEase.OutQuad);
        }

        /// <summary>Out-animation: fade + sink.</summary>
        protected virtual UITween AnimateOut()
        {
            UITween.Move(Rect, UIRoot.Instance != null && UIRoot.Instance.ReducedMotion ? Vector2.zero : new Vector2(0f, -12f), 0.16f, UIEase.InCubic);
            return UITween.Fade(Group, 0f, 0.18f, UIEase.InQuad);
        }

        /// <summary>Pops this screen (and any above it) from its stack.</summary>
        public void Close() => Stack?.Pop(this);

        internal void EnsureBuilt()
        {
            if (Group == null) Group = GetComponent<CanvasGroup>();
            if (_built) return;
            _built = true;
            Rect.Stretch();
            Build();
        }

        internal void InternalOpen()
        {
            IsOpen = true;
            gameObject.SetActive(true);
            UITween.Kill(Group);
            UITween.Kill(Rect);
            Group.blocksRaycasts = true;
            Group.interactable = true;
            OnOpen();
            AnimateIn();
        }

        internal UITween InternalClose()
        {
            IsOpen = false;
            Group.blocksRaycasts = false;
            Group.interactable = false;
            OnClose();
            UITween.Kill(Group);
            UITween.Kill(Rect);
            return AnimateOut();
        }

        internal void InternalFocus()
        {
            Group.blocksRaycasts = true;
            Group.interactable = true;
            if (HideWhenCovered)
            {
                gameObject.SetActive(true);
                UITween.Kill(Group);
                UITween.Fade(Group, 1f, 0.18f);
            }
            OnFocus();
        }

        internal void InternalBlur()
        {
            Group.blocksRaycasts = false;
            Group.interactable = false;
            if (HideWhenCovered)
            {
                UITween.Kill(Group);
                UITween.Fade(Group, 0f, 0.15f).OnComplete(() => { if (!IsTop && IsOpen && this != null) gameObject.SetActive(false); });
            }
            OnBlur();
        }

        internal void InternalCancel() => OnCancel();
    }

    /// <summary>
    /// Push/pop navigation of <see cref="UIScreen"/>s with animated transitions, input layers and cancel routing.
    /// Get the root's stack from <see cref="UIRoot.Screens"/>.
    /// </summary>
    public sealed class UIScreenStack : MonoBehaviour
    {
        readonly List<UIScreen> _stack = new List<UIScreen>();

        /// <summary>Raised whenever the top screen changes (argument may be null when empty).</summary>
        public event Action<UIScreen> TopChanged;

        /// <summary>Top screen or null.</summary>
        public UIScreen Top => _stack.Count > 0 ? _stack[_stack.Count - 1] : null;
        /// <summary>Number of open screens.</summary>
        public int Count => _stack.Count;
        /// <summary>Open screens, bottom first.</summary>
        public IReadOnlyList<UIScreen> Screens => _stack;

        /// <summary>
        /// Creates a new screen of type <typeparamref name="T"/>, runs <paramref name="setup"/> (pass data here),
        /// builds and pushes it.
        /// </summary>
        public T Push<T>(Action<T> setup = null) where T : UIScreen
        {
            var rt = UIFactory.Rect(transform, typeof(T).Name);
            rt.gameObject.AddComponent<CanvasGroup>();
            var screen = rt.gameObject.AddComponent<T>();
            setup?.Invoke(screen);
            Push(screen);
            return screen;
        }

        /// <summary>Pushes an existing (possibly reused) screen instance.</summary>
        public UIScreen Push(UIScreen screen)
        {
            if (screen == null || _stack.Contains(screen)) return screen;
            if (screen.transform.parent != transform) screen.transform.SetParent(transform, false);
            screen.transform.SetAsLastSibling();
            screen.EnsureBuilt();
            var prev = Top;
            screen.Stack = this;
            UIInput.Consume();
            UIRoot.Instance?.Tooltip.Hide();
            _stack.Add(screen);
            UIInput.PushLayer(screen.transform);
            prev?.InternalBlur();
            UISound.Play(UISoundId.Open);
            screen.InternalOpen();
            screen.InternalFocus();
            TopChanged?.Invoke(screen);
            return screen;
        }

        /// <summary>Pops the top screen.</summary>
        public void Pop()
        {
            if (_stack.Count > 0) Pop(Top);
        }

        /// <summary>Pops <paramref name="screen"/> and every screen above it.</summary>
        public void Pop(UIScreen screen)
        {
            int i = _stack.IndexOf(screen);
            if (i < 0) return;
            UIInput.Consume();
            UIRoot.Instance?.Tooltip.Hide();
            for (int k = _stack.Count - 1; k >= i; k--) Remove(k);
            var top = Top;
            top?.InternalFocus();
            TopChanged?.Invoke(top);
        }

        /// <summary>Pops everything.</summary>
        public void Clear()
        {
            for (int k = _stack.Count - 1; k >= 0; k--) Remove(k);
            TopChanged?.Invoke(null);
        }

        void Remove(int k)
        {
            var s = _stack[k];
            _stack.RemoveAt(k);
            if (s == null) return;
            UIInput.PopLayer(s.transform);
            s.Stack = null;
            var anim = s.InternalClose();
            bool destroy = s.DestroyOnClose;
            anim.OnComplete(() =>
            {
                if (s == null || s.IsOpen) return;
                if (destroy)
                {
                    if (Application.isPlaying) Destroy(s.gameObject);
                    else DestroyImmediate(s.gameObject);
                }
                else s.gameObject.SetActive(false);
            });
        }

        void Update()
        {
            var top = Top;
            if (top == null || !top.IsOpen) return;
            if (UIInput.Cancel && UIInput.CanReceive(top))
            {
                UIInput.Consume();
                top.InternalCancel();
            }
        }

        void OnDestroy()
        {
            foreach (var s in _stack)
                if (s != null) UIInput.PopLayer(s.transform);
        }
    }
}
