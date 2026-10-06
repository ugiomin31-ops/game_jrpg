using System;
using System.Collections.Generic;
using UnityEngine;
using UnityEngine.UI;
using Object = UnityEngine.Object;

namespace Abyss.UI
{
    /// <summary>Easing curves for <see cref="UITween"/>.</summary>
    public enum UIEase { Linear, OutQuad, InQuad, OutCubic, InCubic, InOutCubic, OutQuint, OutBack, OutElastic, InBack }

    /// <summary>
    /// Minimal unscaled-time tween used by every UI widget (menus must animate while the game is paused).
    /// A tween is a yield instruction: <c>yield return UITween.Fade(group, 0, 0.3f);</c>.
    /// Outside Play mode tweens complete instantly, so edit-mode built layouts show their final state.
    /// </summary>
    public sealed class UITween : CustomYieldInstruction
    {
        readonly Object _owner;
        readonly bool _hasOwner;
        readonly Action<float> _step;
        readonly float _duration;
        readonly UIEase _ease;
        float _delay;
        float _elapsed;
        Action _onComplete;

        /// <summary>True once the tween finished or was killed.</summary>
        public bool IsDone { get; private set; }

        /// <inheritdoc/>
        public override bool keepWaiting => !IsDone;

        UITween(Object owner, float duration, Action<float> step, UIEase ease, float delay)
        {
            _owner = owner;
            _hasOwner = owner != null;
            _duration = Mathf.Max(0f, duration);
            _step = step;
            _ease = ease;
            _delay = Mathf.Max(0f, delay);
        }

        /// <summary>
        /// Starts a tween calling <paramref name="step"/> with an eased 0..1 progress every frame.
        /// The tween dies silently when <paramref name="owner"/> is destroyed; <see cref="Kill(Object, bool)"/> stops all tweens of an owner.
        /// </summary>
        public static UITween To(Object owner, float duration, Action<float> step, UIEase ease = UIEase.OutCubic, float delay = 0f)
        {
            var t = new UITween(owner, duration, step, ease, delay);
            if (!Application.isPlaying || (t._duration <= 0f && t._delay <= 0f))
            {
                t.Finish();
                return t;
            }
            UITweenRunner.Add(t);
            return t;
        }

        /// <summary>A pure delay (no step) that completes after <paramref name="seconds"/> of unscaled time.</summary>
        public static UITween Delay(Object owner, float seconds, Action then = null) =>
            To(owner, seconds, null, UIEase.Linear).OnComplete(then);

        /// <summary>Registers a callback for completion (invoked immediately when already done).</summary>
        public UITween OnComplete(Action action)
        {
            if (action == null) return this;
            if (IsDone) action();
            else _onComplete += action;
            return this;
        }

        /// <summary>Stops this tween. When <paramref name="complete"/> the final state is applied and callbacks run.</summary>
        public void Kill(bool complete = false)
        {
            if (IsDone) return;
            if (complete) Finish();
            else IsDone = true;
        }

        /// <summary>Kills every running tween owned by <paramref name="owner"/>.</summary>
        public static void Kill(Object owner, bool complete = false) => UITweenRunner.KillOwner(owner, complete);

        // ---- convenience ----------------------------------------------------------------------------

        /// <summary>Fades a CanvasGroup alpha.</summary>
        public static UITween Fade(CanvasGroup group, float to, float duration, UIEase ease = UIEase.OutCubic, float delay = 0f)
        {
            float from = group.alpha;
            return To(group, duration, p => group.alpha = Mathf.LerpUnclamped(from, to, p), ease, delay);
        }

        /// <summary>Fades a Graphic's alpha (colour RGB untouched).</summary>
        public static UITween Fade(Graphic graphic, float to, float duration, UIEase ease = UIEase.OutCubic, float delay = 0f)
        {
            float from = graphic.color.a;
            return To(graphic, duration, p =>
            {
                var c = graphic.color;
                c.a = Mathf.LerpUnclamped(from, to, p);
                graphic.color = c;
            }, ease, delay);
        }

        /// <summary>Tweens a Graphic colour.</summary>
        public static UITween Color(Graphic graphic, Color to, float duration, UIEase ease = UIEase.OutCubic, float delay = 0f)
        {
            var from = graphic.color;
            return To(graphic, duration, p => graphic.color = UnityEngine.Color.LerpUnclamped(from, to, p), ease, delay);
        }

        /// <summary>Tweens localScale uniformly.</summary>
        public static UITween Scale(Transform t, float to, float duration, UIEase ease = UIEase.OutCubic, float delay = 0f)
        {
            var from = t.localScale;
            var target = new Vector3(to, to, 1f);
            return To(t, duration, p => t.localScale = Vector3.LerpUnclamped(from, target, p), ease, delay);
        }

        /// <summary>Tweens anchoredPosition.</summary>
        public static UITween Move(RectTransform rt, Vector2 to, float duration, UIEase ease = UIEase.OutCubic, float delay = 0f)
        {
            var from = rt.anchoredPosition;
            return To(rt, duration, p => rt.anchoredPosition = Vector2.LerpUnclamped(from, to, p), ease, delay);
        }

        // ---- runner interface -----------------------------------------------------------------------

        internal Object Owner => _owner;

        /// <summary>Advances the tween; returns false when finished.</summary>
        internal bool Tick(float dt)
        {
            if (IsDone) return false;
            if (_hasOwner && _owner == null) { IsDone = true; return false; }
            if (_delay > 0f)
            {
                _delay -= dt;
                if (_delay > 0f) return true;
                dt = -_delay;
            }
            _elapsed += dt;
            if (_elapsed >= _duration) { Finish(); return false; }
            _step?.Invoke(Evaluate(_ease, _elapsed / _duration));
            return true;
        }

        void Finish()
        {
            if (IsDone) return;
            IsDone = true;
            if (!_hasOwner || _owner != null) _step?.Invoke(1f);
            var cb = _onComplete;
            _onComplete = null;
            cb?.Invoke();
        }

        /// <summary>Evaluates an easing curve at <paramref name="t"/> in 0..1.</summary>
        public static float Evaluate(UIEase ease, float t)
        {
            t = Mathf.Clamp01(t);
            switch (ease)
            {
                case UIEase.OutQuad: return 1f - (1f - t) * (1f - t);
                case UIEase.InQuad: return t * t;
                case UIEase.OutCubic: { float u = 1f - t; return 1f - u * u * u; }
                case UIEase.InCubic: return t * t * t;
                case UIEase.InOutCubic: return t < 0.5f ? 4f * t * t * t : 1f - Mathf.Pow(-2f * t + 2f, 3f) / 2f;
                case UIEase.OutQuint: { float u = 1f - t; return 1f - u * u * u * u * u; }
                case UIEase.OutBack: { const float c1 = 1.70158f, c3 = c1 + 1f; float u = t - 1f; return 1f + c3 * u * u * u + c1 * u * u; }
                case UIEase.InBack: { const float c1 = 1.70158f, c3 = c1 + 1f; return c3 * t * t * t - c1 * t * t; }
                case UIEase.OutElastic:
                    if (t <= 0f || t >= 1f) return t;
                    return Mathf.Pow(2f, -10f * t) * Mathf.Sin((t * 10f - 0.75f) * (2f * Mathf.PI / 3f)) + 1f;
                default: return t;
            }
        }
    }

    /// <summary>Hidden driver that ticks <see cref="UITween"/>s with unscaled time.</summary>
    [AddComponentMenu("")]
    internal sealed class UITweenRunner : MonoBehaviour
    {
        static UITweenRunner _instance;
        readonly List<UITween> _tweens = new List<UITween>(64);
        readonly List<UITween> _pending = new List<UITween>(16);

        internal static void Add(UITween t)
        {
            if (_instance == null)
            {
                var go = new GameObject("[UITweenRunner]") { hideFlags = HideFlags.HideAndDontSave };
                DontDestroyOnLoad(go);
                _instance = go.AddComponent<UITweenRunner>();
            }
            _instance._pending.Add(t);
        }

        internal static void KillOwner(Object owner, bool complete)
        {
            if (_instance == null) return;
            KillIn(_instance._tweens, owner, complete);
            KillIn(_instance._pending, owner, complete);
        }

        static void KillIn(List<UITween> list, Object owner, bool complete)
        {
            for (int i = 0; i < list.Count; i++)
                if (ReferenceEquals(list[i].Owner, owner)) list[i].Kill(complete);
        }

        void Update()
        {
            if (_pending.Count > 0)
            {
                _tweens.AddRange(_pending);
                _pending.Clear();
            }
            float dt = Time.unscaledDeltaTime;
            for (int i = _tweens.Count - 1; i >= 0; i--)
                if (!_tweens[i].Tick(dt)) _tweens.RemoveAt(i);
        }
    }
}
