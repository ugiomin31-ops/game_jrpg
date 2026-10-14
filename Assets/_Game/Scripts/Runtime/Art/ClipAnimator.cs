using System;
using System.Collections.Generic;
using UnityEngine;
using UnityEngine.Animations;
using UnityEngine.Playables;

namespace Abyss.Runtime.Art
{
    /// <summary>Named Generic-rig takes, with interruptible cross-fades and held one-shot end poses.</summary>
    [RequireComponent(typeof(Animator))]
    public sealed class ClipAnimator : MonoBehaviour, IModelAnimator
    {
        readonly Dictionary<string, AnimationClip> _clips = new Dictionary<string, AnimationClip>();
        readonly Dictionary<string, int> _slots = new Dictionary<string, int>();
        PlayableGraph _graph;
        AnimationMixerPlayable _mixer;
        AnimationClipPlayable[] _playables;
        AnimationClip[] _slotClips;
        float[] _weights, _fromWeights;
        int _current = -1;
        string _currentName, _queuedAfter, _pendingName, _pendingAfter;
        float _fade, _fadeTime, _pendingFade, _pendingStart;
        float _speed = 1f;
        bool _ready;

        readonly Dictionary<string, float> _clipRates = new Dictionary<string, float>();
        string _rest = "Idle";
        /// <summary>Crossfade out of a finished one-shot into its follow-up (Attack/Cast/Skill/Hit back to the standing loop).</summary>
        public const float ReturnFade = 0.22f;

        /// <summary>
        /// The standing loop that a request for "Idle" resolves to. Battle heroes use "BattleIdle" (a ready stance) so that
        /// Attack/Cast/Skill/Hit start and end close to it; the town and everything without that take keep "Idle".
        /// </summary>
        public string RestClip
        {
            get => _rest;
            set { if (HasClip(value)) _rest = value; }
        }

        string Resolve(string clip) => clip == "Idle" ? _rest : clip;

        /// <summary>Playback-rate multiplier of one take on top of <see cref="SetSpeed"/> (e.g. Run matched to ground speed).</summary>
        public void SetClipRate(string clip, float rate)
        {
            rate = Mathf.Max(0.05f, rate);
            if (_clipRates.TryGetValue(clip, out var old) && Mathf.Approximately(old, rate)) return;
            _clipRates[clip] = rate;
            if (!_ready) return;
            for (int i = 0; i < _playables.Length; i++) UpdateSpeed(i);
        }

        readonly Dictionary<string, float> _clipEnds = new Dictionary<string, float>();
        /// <summary>Plays only the first part (0..1) of a one-shot before returning to its follow-up, e.g. cutting a held recovery pose.</summary>
        public void SetClipEnd(string clip, float fraction) => _clipEnds[clip] = Mathf.Clamp(fraction, .1f, 1f);
        public float EndFraction(string clip) => clip != null && _clipEnds.TryGetValue(clip, out var f) ? f : 1f;

        float RateOf(int slot) => _clipRates.TryGetValue(_slotClips[slot].name, out var r) ? r : 1f;

        readonly Dictionary<string, float> _clipStarts = new Dictionary<string, float>();
        readonly Dictionary<string, float> _clipHolds = new Dictionary<string, float>();
        /// <summary>
        /// Plays a one-shot only from <paramref name="start"/> to <paramref name="hold"/> (fractions) and holds that pose: a long
        /// preset whose useful part sits in the middle (Tripo <c>defeat_02</c>: still for 15 %, slumps at 20-50 %, then stands up again).
        /// </summary>
        public void SetClipWindow(string clip, float start, float hold)
        {
            _clipStarts[clip] = Mathf.Clamp01(start);
            _clipHolds[clip] = Mathf.Clamp(hold, _clipStarts[clip] + .01f, 1f);
        }
        float HoldTime(int slot) => _slotClips[slot].length * (_clipHolds.TryGetValue(_slotClips[slot].name, out var h) ? h : 1f);

        readonly Dictionary<string, float> _loopBlends = new Dictionary<string, float>();
        /// <summary>
        /// Cross-fades a loop into a fresh copy of itself over <paramref name="seconds"/> before it wraps, for takes whose first
        /// and last poses do not match (the warrior BattleIdle wraps every 1.5 s with a visible hitch).
        /// </summary>
        public void SetLoopBlend(string clip, float seconds) { if (seconds > 0f) _loopBlends[clip] = seconds; else _loopBlends.Remove(clip); }

        /// <summary>
        /// Per-unit start phase (0..1) of the standing loops, so units spawned together do not breathe in lockstep. Derived
        /// from the object's instance id: stable for the unit's lifetime, different between units.
        /// </summary>
        float _phase;
        bool IsRestLoop(string clip) => (clip == _rest || clip == "Idle" || clip == "BattleIdle") && _clips.TryGetValue(clip, out var c) && c.isLooping;

        public string CurrentClip => _currentName;
        public IEnumerable<string> ClipNames => _clips.Keys;
        public float NormalizedTime => _current < 0 ? 0f :
            (float)(_playables[_current].GetTime() / _slotClips[_current].length);

        public void Init(IEnumerable<AnimationClip> clips)
        {
            if (_ready) throw new InvalidOperationException("ClipAnimator already initialized: " + name);
            foreach (var clip in clips)
            {
                if (clip == null || clip.name.StartsWith("__preview__", StringComparison.Ordinal)) continue;
                if (clip.length <= 0f) throw new InvalidOperationException("Empty animation take: " + name + "/" + clip.name);
                _clips.Add(clip.name, clip);
            }
            RequireClip("Idle");
            unchecked { uint h = (uint)GetInstanceID() * 2654435761u; _phase = (h >> 8) / 16777216f; }
            var animator = GetComponent<Animator>();
            animator.applyRootMotion = false;
            animator.cullingMode = AnimatorCullingMode.AlwaysAnimate;
            _graph = PlayableGraph.Create(name + ".Clips");
            _graph.SetTimeUpdateMode(DirectorUpdateMode.GameTime);
            // Two reusable lanes per take allow a restart to fade out its previous instance.
            // Interrupted transitions retain every contributing lane, not just the newest take.
            int count = _clips.Count * 2;
            _playables = new AnimationClipPlayable[count];
            _slotClips = new AnimationClip[count];
            _weights = new float[count]; _fromWeights = new float[count];
            _mixer = AnimationMixerPlayable.Create(_graph, count);
            int slot = 0;
            foreach (var pair in _clips)
            {
                _slots.Add(pair.Key, slot);
                for (int lane = 0; lane < 2; lane++, slot++)
                {
                    var playable = AnimationClipPlayable.Create(_graph, pair.Value);
                    playable.SetApplyFootIK(false);
                    playable.SetSpeed(0);
                    _playables[slot] = playable; _slotClips[slot] = pair.Value;
                    _graph.Connect(playable, 0, _mixer, slot);
                    _mixer.SetInputWeight(slot, 0);
                }
            }
            var output = AnimationPlayableOutput.Create(_graph, "Anim", animator);
            output.SetSourcePlayable(_mixer);
            _ready = true;
            Play("Idle", 0f);
            _graph.Play();
        }

        public bool HasClip(string clip) => clip != null && _clips.ContainsKey(clip);
        public float Length(string clip) => HasClip(clip) ? _clips[clip].length : 0f;

        void RequireClip(string clip)
        {
            if (!HasClip(clip)) throw new InvalidOperationException("Missing authored animation take: " + name + "/" + (clip ?? "<null>"));
        }

        /// <summary>Blend from the complete current pose. Missing named takes are content errors.</summary>
        public void Play(string clip, float fade = 0.15f, bool restart = true, string then = null) => Begin(clip, fade, restart, then, -1f);

        /// <summary>Restart a take part-way through (0..1), e.g. a follow-up strike that skips the wind-up.</summary>
        public void PlayFrom(string clip, float normalizedStart, float fade = 0.05f, string then = "Idle") =>
            Begin(clip, fade, true, then, Mathf.Clamp01(normalizedStart));

        /// <summary><paramref name="start"/> below 0 = the take's default start: its window start, a standing loop's unit phase, else 0.</summary>
        void Begin(string clip, float fade, bool restart, string then, float start)
        {
            if (!_ready) return;
            clip = Resolve(clip); then = then == null ? null : Resolve(then);
            RequireClip(clip);
            if (start < 0f) start = _clipStarts.TryGetValue(clip, out var windowStart) ? windowStart : IsRestLoop(clip) ? _phase : 0f;
            if (then != null) RequireClip(then);
            _pendingName = null;
            if (!restart && clip == _currentName) return;
            int slot = _slots[clip];
            if (_weights[slot] > 0f) slot++;
            if (_weights[slot] > 0f)
            {
                // An unusually fast third restart waits for a lane instead of deleting a visible pose.
                // Keep only the latest request; storage and the playable graph stay bounded.
                _pendingName = clip; _pendingAfter = then; _pendingFade = fade; _pendingStart = start;
                return;
            }
            Array.Copy(_weights, _fromWeights, _weights.Length);
            _current = slot; _currentName = clip; _queuedAfter = then;
            var playable = _playables[slot];
            playable.SetTime(start * _slotClips[slot].length); playable.SetDone(false); playable.SetSpeed(_speed * RateOf(slot));
            _fadeTime = Mathf.Max(0f, fade);
            float total = 0f;
            for (int i = 0; i < _fromWeights.Length; i++) total += _fromWeights[i];
            _fade = _fadeTime <= 0f || total <= 0f ? 1f : 0f;
            ApplyWeights();
        }

        /// <summary>Play one cycle (including a looping take), then return to the requested take.</summary>
        public void PlayOnce(string clip, string then = "Idle", float fade = 0.1f) => Play(clip, fade, true, then);

        public void SetSpeed(float speed)
        {
            speed = Mathf.Max(0f, speed);
            if (Mathf.Approximately(_speed, speed)) return;
            _speed = speed;
            if (!_ready) return;
            for (int i = 0; i < _playables.Length; i++) UpdateSpeed(i);
        }

        void UpdateSpeed(int slot)
        {
            bool ended = !_slotClips[slot].isLooping && _playables[slot].GetTime() >= HoldTime(slot);
            _playables[slot].SetSpeed((_weights[slot] > 0f || slot == _current) && !ended ? _speed * RateOf(slot) : 0f);
        }

        void ApplyWeights()
        {
            for (int i = 0; i < _weights.Length; i++)
            {
                _weights[i] = Mathf.Lerp(_fromWeights[i], i == _current ? 1f : 0f, _fade);
                _mixer.SetInputWeight(i, _weights[i]);
                UpdateSpeed(i);
            }
        }

        void Update()
        {
            if (!_ready) return;
            // Explicitly clamp nonloops: Die remains down until a real revive changes its take.
            for (int i = 0; i < _playables.Length; i++)
                if ((_weights[i] > 0f || i == _current) && !_slotClips[i].isLooping && _playables[i].GetTime() > HoldTime(i))
                { _playables[i].SetTime(HoldTime(i)); _playables[i].SetSpeed(0); }
            if (_fade < 1f)
            {
                _fade = Mathf.Min(1f, _fade + Time.deltaTime * _speed / _fadeTime);
                ApplyWeights();
            }
            if (_pendingName != null && _fade >= 1f)
            {
                string next = _pendingName, after = _pendingAfter;
                Begin(next, _pendingFade, true, after, _pendingStart);
            }
            else if (_queuedAfter != null && NormalizedTime >= EndFraction(_currentName))
            {
                string next = _queuedAfter;
                _queuedAfter = null;
                Play(next, ReturnFade, false);
            }
            else if (_queuedAfter == null && _fade >= 1f && _currentName != null && _loopBlends.TryGetValue(_currentName, out float blend))
            {
                // Seam cross-fade: start a fresh copy on the other lane so the old one wraps at (near) zero weight.
                float length = _slotClips[_current].length;
                float local = (float)(_playables[_current].GetTime() % length);
                if (local >= length - blend * RateOf(_current)) Begin(_currentName, blend, true, null, 0f);
            }
        }

        void OnDestroy()
        {
            if (_graph.IsValid()) _graph.Destroy();
        }
    }
}
