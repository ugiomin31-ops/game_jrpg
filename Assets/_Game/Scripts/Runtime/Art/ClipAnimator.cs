using System;
using System.Collections.Generic;
using UnityEngine;
using UnityEngine.Animations;
using UnityEngine.Playables;

namespace Abyss.Runtime.Art
{
    /// <summary>Named Generic-rig takes, with interruptible cross-fades and held one-shot end poses.</summary>
    [RequireComponent(typeof(Animator))]
    public sealed class ClipAnimator : MonoBehaviour
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
        float _fade, _fadeTime, _pendingFade;
        float _speed = 1f;
        bool _ready;

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
        public void Play(string clip, float fade = 0.15f, bool restart = true, string then = null)
        {
            if (!_ready) return;
            RequireClip(clip);
            if (then != null) RequireClip(then);
            _pendingName = null;
            if (!restart && clip == _currentName) return;
            int slot = _slots[clip];
            if (_weights[slot] > 0f) slot++;
            if (_weights[slot] > 0f)
            {
                // An unusually fast third restart waits for a lane instead of deleting a visible pose.
                // Keep only the latest request; storage and the playable graph stay bounded.
                _pendingName = clip; _pendingAfter = then; _pendingFade = fade;
                return;
            }
            Array.Copy(_weights, _fromWeights, _weights.Length);
            _current = slot; _currentName = clip; _queuedAfter = then;
            var playable = _playables[slot];
            playable.SetTime(0); playable.SetDone(false); playable.SetSpeed(_speed);
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
            bool ended = !_slotClips[slot].isLooping && _playables[slot].GetTime() >= _slotClips[slot].length;
            _playables[slot].SetSpeed((_weights[slot] > 0f || slot == _current) && !ended ? _speed : 0f);
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
                if ((_weights[i] > 0f || i == _current) && !_slotClips[i].isLooping && _playables[i].GetTime() > _slotClips[i].length)
                { _playables[i].SetTime(_slotClips[i].length); _playables[i].SetSpeed(0); }
            if (_fade < 1f)
            {
                _fade = Mathf.Min(1f, _fade + Time.deltaTime * _speed / _fadeTime);
                ApplyWeights();
            }
            if (_pendingName != null && _fade >= 1f)
            {
                string next = _pendingName, after = _pendingAfter;
                Play(next, _pendingFade, true, after);
            }
            else if (_queuedAfter != null && NormalizedTime >= 1f)
            {
                string next = _queuedAfter;
                _queuedAfter = null;
                Play(next, 0.12f, false);
            }
        }

        void OnDestroy()
        {
            if (_graph.IsValid()) _graph.Destroy();
        }
    }
}
