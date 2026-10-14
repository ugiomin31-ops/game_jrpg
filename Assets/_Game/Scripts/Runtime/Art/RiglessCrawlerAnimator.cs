using System;
using UnityEngine;

namespace Abyss.Runtime.Art
{
    /// <summary>
    /// Code-driven animation for rigid, static creature meshes (armoured beetles) whose Tripo model ships no skeleton
    /// and no takes. Selected explicitly by <see cref="ArtLibrary.IsRiglessCrawler"/>. Unlike <see cref="RiglessBlobAnimator"/>
    /// the shell never squashes: the body only breathes (≤2 % scale), bobs, pitches and slides as one rigid piece —
    /// a low scuttle for Run, a short leg-less hop and head-down lunge for Attack (contact 0.4), a rear-up for Cast
    /// (release 0.6), a recoil for Hit, and for Die a tip-over onto its side that settles and sinks a little (held).
    /// It only moves the Visual transform it sits on (around the baseline captured at Init); root placement by battle
    /// code is untouched. Same follow-up / interrupt / speed semantics as <see cref="ClipAnimator"/>.
    /// </summary>
    public sealed class RiglessCrawlerAnimator : MonoBehaviour, IModelAnimator
    {
        // Rigid pose relative to the baseline: uniform scale, lift / forward (fractions of the body height), angles in degrees.
        struct Pose
        {
            public float Scale, Lift, Fwd, Pitch, Roll, Yaw;
            public static Pose Of(float lift = 0f, float fwd = 0f, float pitch = 0f, float roll = 0f, float scale = 1f, float yaw = 0f) =>
                new Pose { Scale = scale, Lift = lift, Fwd = fwd, Pitch = pitch, Roll = roll, Yaw = yaw };
            public static Pose Rest => Of();
            public static Pose Lerp(in Pose a, in Pose b, float t) => new Pose
            {
                Scale = Mathf.Lerp(a.Scale, b.Scale, t), Lift = Mathf.Lerp(a.Lift, b.Lift, t), Fwd = Mathf.Lerp(a.Fwd, b.Fwd, t),
                Pitch = Mathf.Lerp(a.Pitch, b.Pitch, t), Roll = Mathf.Lerp(a.Roll, b.Roll, t), Yaw = Mathf.Lerp(a.Yaw, b.Yaw, t),
            };
        }

        struct Key
        {
            public float U; public Pose P;
            public Key(float u, Pose p) { U = u; P = p; }
        }

        // Pitch: negative = nose up (Unity +X pitches the +Z nose down). Attack contact 0.4, Cast release 0.6 (BattleView.Contact).
        static readonly Pose DieFinal = Pose.Of(-0.12f, -0.05f, 6f, 82f);
        static readonly Key[] AttackKeys =
        {
            new Key(0.00f, Pose.Rest),
            new Key(0.22f, Pose.Of(0.00f, -0.10f, -10f)),                 // rock back, nose up (wind-up)
            new Key(0.32f, Pose.Of(0.14f, 0.05f, -4f)),                   // leg-less hop off the ground
            new Key(0.40f, Pose.Of(0.03f, 0.32f, 14f)),                   // head-down ram = contact
            new Key(0.60f, Pose.Of(0.00f, 0.16f, 5f)),
            new Key(1.00f, Pose.Rest),
        };
        static readonly Key[] CastKeys =
        {
            new Key(0.00f, Pose.Rest),
            new Key(0.35f, Pose.Of(0.04f, -0.06f, -12f, 0f, 1.01f)),      // rear up
            new Key(0.60f, Pose.Of(0.08f, -0.04f, -20f, 0f, 1.02f)),      // full rear = release
            new Key(0.70f, Pose.Of(0.00f, 0.04f, 6f)),                    // stamp down
            new Key(1.00f, Pose.Rest),
        };
        static readonly Key[] HitKeys =
        {
            new Key(0.00f, Pose.Rest),
            new Key(0.18f, Pose.Of(0.05f, -0.14f, -9f, 7f)),              // recoil back, nose up, list
            new Key(0.55f, Pose.Of(0.00f, -0.04f, 2f, -3f)),
            new Key(1.00f, Pose.Rest),
        };
        static readonly Key[] DieKeys =
        {
            new Key(0.00f, Pose.Rest),
            new Key(0.18f, Pose.Of(0.10f, -0.10f, -14f, 10f)),            // jolt up
            new Key(0.55f, Pose.Of(0.04f, -0.06f, 8f, 95f)),              // tip over (slight overshoot)
            new Key(0.75f, Pose.Of(-0.08f, -0.05f, 4f, 78f)),             // settle
            new Key(1.00f, DieFinal),                                     // held, partly sunk
        };
        static readonly Key[] ReviveKeys =
        {
            new Key(0.00f, DieFinal),
            new Key(0.50f, Pose.Of(0.12f, 0f, -6f, -12f)),
            new Key(1.00f, Pose.Rest),
        };

        public const string IdleTake = "Idle";

        Transform _visual;
        Vector3 _basePos, _baseScale;
        Quaternion _baseRot;
        float _height = 1f;
        Pose _pose = Pose.Rest, _from = Pose.Rest;
        string _name, _then;
        float _time, _length = 1f, _blend = 1f, _fadeTime, _speed = 1f;
        bool _loop, _ready;

        public string CurrentClip => _name;
        public float NormalizedTime => _name == null ? 0f : _time / _length;

        /// <summary>Takes the battle code can rely on (Skill / Ultimate / Roar are absent so callers fall back to Attack / Cast).</summary>
        public static bool Supports(string clip)
        {
            switch (clip)
            {
                case "Idle": case "Walk": case "Run": case "Attack": case "Cast": case "Hit":
                case "Die": case "Revive": case "Victory": case "Guard": case "Talk":
                    return true;
                default: return false;
            }
        }

        static float LengthOf(string clip)
        {
            switch (clip)
            {
                case "Idle": return 2.4f;
                case "Walk": return 0.8f;
                case "Run": return 0.42f;
                case "Attack": return 0.75f;
                case "Cast": return 0.9f;
                case "Hit": return 0.4f;
                case "Die": return 0.9f;
                case "Revive": return 0.7f;
                default: return 1.0f;
            }
        }

        static bool Loops(string clip) => clip != "Attack" && clip != "Cast" && clip != "Hit" && clip != "Die" && clip != "Revive";

        public bool HasClip(string clip) => Supports(clip);
        public float Length(string clip) => string.IsNullOrEmpty(clip) ? 0f : LengthOf(clip);

        /// <summary>Capture the baseline of the Visual transform this component sits on and start Idle.</summary>
        public void Init()
        {
            if (_ready) throw new InvalidOperationException("RiglessCrawlerAnimator already initialized: " + name);
            _visual = transform;
            _basePos = _visual.localPosition; _baseRot = _visual.localRotation; _baseScale = _visual.localScale;
            var parent = _visual.parent;
            float scale = parent != null ? Mathf.Max(1e-4f, Mathf.Abs(parent.lossyScale.y)) : 1f;
            bool any = false; var bounds = new Bounds();
            foreach (var r in _visual.GetComponentsInChildren<Renderer>(false))
            {
                if (r == null || r is ParticleSystemRenderer || !r.enabled) continue;
                if (!any) { bounds = r.bounds; any = true; } else bounds.Encapsulate(r.bounds);
            }
            _height = any ? Mathf.Clamp(bounds.size.y / scale, 0.2f, 5f) : 1f;
            _ready = true;
            Begin(IdleTake, 0f, true, null, 0f);
        }

        public void Play(string clip, float fade = 0.15f, bool restart = true, string then = null) => Begin(clip, fade, restart, then, 0f);
        public void PlayFrom(string clip, float normalizedStart, float fade = 0.05f, string then = "Idle") => Begin(clip, fade, true, then, Mathf.Clamp01(normalizedStart));
        public void PlayOnce(string clip, string then = "Idle", float fade = 0.1f) => Play(clip, fade, true, then);
        public void SetSpeed(float speed) => _speed = Mathf.Max(0f, speed);

        void Begin(string clip, float fade, bool restart, string then, float start)
        {
            if (!_ready || string.IsNullOrEmpty(clip)) return;
            if (!restart && clip == _name) return;
            if (then == null && clip == "Revive") then = IdleTake;
            _from = _pose;                      // blend from the pose on screen (interrupts never pop)
            _name = clip; _then = then;
            _length = LengthOf(clip); _loop = Loops(clip);
            _time = start * _length;
            _fadeTime = Mathf.Max(0f, fade);
            _blend = _fadeTime <= 0f ? 1f : 0f;
            Evaluate();
        }

        void LateUpdate()
        {
            if (!_ready) return;
            float dt = Time.deltaTime * _speed;   // speed 0 (pause / hit-stop) freezes time and blend
            if (dt > 0f)
            {
                _time += dt;
                if (!_loop && _time > _length) _time = _length;   // one-shots hold their end pose (Die stays tipped)
                if (_blend < 1f) _blend = _fadeTime <= 0f ? 1f : Mathf.Min(1f, _blend + dt / _fadeTime);
            }
            Evaluate();
            if (_then != null && _time >= _length)
            {
                string next = _then; _then = null;
                Begin(next, 0.12f, false, null, 0f);
            }
        }

        void Evaluate()
        {
            var target = Sample(_name, _time);
            _pose = _blend >= 1f ? target : Pose.Lerp(_from, target, _blend);
            _visual.localScale = _baseScale * _pose.Scale;
            _visual.localRotation = _baseRot * Quaternion.Euler(_pose.Pitch, _pose.Yaw, _pose.Roll);
            _visual.localPosition = _basePos + new Vector3(0f, _pose.Lift * _height, _pose.Fwd * _height);
        }

        static Pose Sample(string clip, float time)
        {
            float length = LengthOf(clip);
            float u = Loops(clip) ? Mathf.Repeat(time / length, 1f) : Mathf.Clamp01(time / length);
            float w = u * Mathf.PI * 2f;
            switch (clip)
            {
                // Breathing shell: ≤2 % uniform scale, a hair of lift and a slow nose sway; never a squash.
                case "Idle": return Pose.Of(0.006f * (1f - Mathf.Cos(w)), 0f, -0.8f * Mathf.Sin(w), 0f, 1f + 0.012f * Mathf.Sin(w), 1.5f * Mathf.Sin(w * 0.5f));
                // Scuttle: fast low chatter (two lifts per cycle) with a side-to-side waddle; Walk is the same, slower.
                case "Run": return Pose.Of(0.035f * Mathf.Abs(Mathf.Sin(w)), 0f, 3f, 3f * Mathf.Sin(w), 1f, 2f * Mathf.Sin(w));
                case "Walk": return Pose.Of(0.02f * Mathf.Abs(Mathf.Sin(w)), 0f, 1f, 2f * Mathf.Sin(w), 1f, 1.5f * Mathf.Sin(w));
                case "Attack": return Keyed(AttackKeys, u);
                case "Cast": return Keyed(CastKeys, u);
                case "Hit": return Keyed(HitKeys, u);
                case "Die": return Keyed(DieKeys, u);
                case "Revive": return Keyed(ReviveKeys, u);
                default: return Pose.Of(0.08f * Mathf.Max(0f, Mathf.Sin(w)), 0f, -6f * Mathf.Max(0f, Mathf.Sin(w)));   // Victory / Guard / Talk: a proud rear
            }
        }

        static Pose Keyed(Key[] keys, float u)
        {
            if (u <= keys[0].U) return keys[0].P;
            for (int i = 1; i < keys.Length; i++)
            {
                if (u > keys[i].U) continue;
                float t = Mathf.InverseLerp(keys[i - 1].U, keys[i].U, u);
                return Pose.Lerp(keys[i - 1].P, keys[i].P, t * t * (3f - 2f * t));
            }
            return keys[keys.Length - 1].P;
        }
    }
}
