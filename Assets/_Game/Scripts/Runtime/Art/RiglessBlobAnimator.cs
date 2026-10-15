using System;
using UnityEngine;

namespace Abyss.Runtime.Art
{
    /// <summary>
    /// Code-driven squash / bob / stretch animation for rigless blob creatures (slime, magma slime, giant clam,
    /// sea urchin, chaos spawn) that ship no authored takes. Selected explicitly by <see cref="ArtLibrary.IsRiglessBlob"/>.
    /// It only moves the Visual transform it sits on (scale, tilt, small local offset around the baseline captured at
    /// Init), so root placement done by battle code and the baseline scale of the model are untouched.
    /// Same follow-up / interrupt / speed semantics as <see cref="ClipAnimator"/>; poses blend from whatever is
    /// currently shown, so interrupted hits and multi-hit restarts never pop.
    /// </summary>
    public sealed class RiglessBlobAnimator : MonoBehaviour, IModelAnimator
    {
        // Pose in baseline-relative terms. Lift / Fwd are fractions of the model height, angles in degrees.
        struct Pose
        {
            public float Sx, Sy, Sz, Lift, Fwd, Pitch, Roll;

            public static Pose Of(float sx, float sy, float sz, float lift = 0f, float fwd = 0f, float pitch = 0f, float roll = 0f) =>
                new Pose { Sx = sx, Sy = sy, Sz = sz, Lift = lift, Fwd = fwd, Pitch = pitch, Roll = roll };

            public static Pose Rest => Of(1f, 1f, 1f);

            /// <summary>Volume-preserving squash: height factor sy, width (x and z) 1/sqrt(sy).</summary>
            public static Pose Squash(float sy, float lift = 0f, float pitch = 0f)
            {
                float w = 1f / Mathf.Sqrt(Mathf.Max(0.05f, sy));
                return Of(w, sy, w, lift, 0f, pitch);
            }

            public static Pose Lerp(in Pose a, in Pose b, float t) => new Pose
            {
                Sx = Mathf.Lerp(a.Sx, b.Sx, t), Sy = Mathf.Lerp(a.Sy, b.Sy, t), Sz = Mathf.Lerp(a.Sz, b.Sz, t),
                Lift = Mathf.Lerp(a.Lift, b.Lift, t), Fwd = Mathf.Lerp(a.Fwd, b.Fwd, t),
                Pitch = Mathf.Lerp(a.Pitch, b.Pitch, t), Roll = Mathf.Lerp(a.Roll, b.Roll, t),
            };
        }

        struct Key
        {
            public float U; public Pose P;
            public Key(float u, Pose p) { U = u; P = p; }
        }

        // One-shot takes as keyed poses (u = 0..1 of the take). Attack contact = 0.4, Cast release = 0.6
        // (BattleView.Contact), so the peak stretch / swell lands exactly there.
        static readonly Pose DieFinal = Pose.Of(1.45f, 0.14f, 1.45f);
        static readonly Key[] AttackKeys =
        {
            new Key(0.00f, Pose.Rest),
            new Key(0.20f, Pose.Of(1.18f, 0.72f, 1.18f, 0f, -0.04f, -6f)),     // anticipation squash, lean back
            new Key(0.40f, Pose.Of(0.86f, 0.92f, 1.50f, 0.06f, 0.30f, 8f)),    // lunge stretch peak = contact
            new Key(0.62f, Pose.Of(1.05f, 0.94f, 1.18f, 0.02f, 0.14f, 3f)),
            new Key(1.00f, Pose.Rest),
        };
        static readonly Key[] CastKeys =
        {
            new Key(0.00f, Pose.Rest),
            new Key(0.30f, Pose.Of(1.10f, 1.06f, 1.10f, 0.03f)),
            new Key(0.60f, Pose.Of(1.30f, 1.18f, 1.30f, 0.10f)),               // full swell = release point
            new Key(0.68f, Pose.Of(1.14f, 0.74f, 1.14f, 0f, 0f, 5f)),          // release snap
            new Key(0.84f, Pose.Of(0.97f, 1.07f, 0.97f)),
            new Key(1.00f, Pose.Rest),
        };
        static readonly Key[] HitKeys =
        {
            new Key(0.00f, Pose.Rest),
            new Key(0.20f, Pose.Of(1.16f, 0.76f, 1.16f, 0f, -0.08f, -4f, 12f)), // quick squash + tilt
            new Key(0.55f, Pose.Of(0.96f, 1.06f, 0.96f, 0f, -0.02f, 0f, -5f)),
            new Key(1.00f, Pose.Rest),
        };
        static readonly Key[] DieKeys =
        {
            new Key(0.00f, Pose.Rest),
            new Key(0.20f, Pose.Of(1.12f, 0.84f, 1.12f, 0f, -0.05f, -6f, 6f)),
            new Key(0.55f, Pose.Of(1.55f, 0.10f, 1.55f)),                       // flatten (slight overshoot)
            new Key(1.00f, DieFinal),                                           // held
        };
        static readonly Key[] ReviveKeys =
        {
            new Key(0.00f, DieFinal),                                           // matches the held Die pose
            new Key(0.45f, Pose.Of(0.88f, 1.18f, 0.88f, 0.06f)),
            new Key(0.75f, Pose.Of(1.06f, 0.92f, 1.06f)),
            new Key(1.00f, Pose.Rest),
        };

        public const string IdleTake = "Idle";

        Transform _visual;
        Vector3 _basePos, _baseScale;
        Quaternion _baseRot;
        float _height = 1f, _footOffset;
        Pose _pose = Pose.Rest, _from = Pose.Rest;
        string _name, _then;
        float _time, _length = 1f, _blend = 1f, _fadeTime;
        float _speed = 1f;
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
                case "Idle": return 2.0f;
                case "Walk": return 0.8f;
                case "Run": return 0.5f;
                case "Attack": return 0.7f;
                case "Cast": return 0.9f;
                case "Hit": return 0.35f;
                case "Die": return 0.7f;
                case "Revive": return 0.6f;
                default: return 0.8f;   // Victory, Guard, Talk and any other name: gentle bounce
            }
        }

        static bool Loops(string clip) =>
            clip != "Attack" && clip != "Cast" && clip != "Hit" && clip != "Die" && clip != "Revive";

        public bool HasClip(string clip) => Supports(clip);
        public float Length(string clip) => string.IsNullOrEmpty(clip) ? 0f : LengthOf(clip);

        /// <summary>Capture the baseline of the Visual transform this component sits on and start Idle.</summary>
        public void Init()
        {
            if (_ready) throw new InvalidOperationException("RiglessBlobAnimator already initialized: " + name);
            _visual = transform;
            _basePos = _visual.localPosition; _baseRot = _visual.localRotation; _baseScale = _visual.localScale;
            MeasureVisual();
            _ready = true;
            Begin(IdleTake, 0f, true, null, 0f);
        }

        // Height and ground contact of the visible mesh in parent-local units, so lifts scale with the creature and
        // a squash keeps its underside planted even when the Visual pivot is not at its feet.
        void MeasureVisual()
        {
            var parent = _visual.parent;
            float scale = parent != null ? Mathf.Max(1e-4f, Mathf.Abs(parent.lossyScale.y)) : 1f;
            float originY = parent != null ? parent.position.y : 0f;
            bool any = false; var bounds = new Bounds();
            foreach (var r in _visual.GetComponentsInChildren<Renderer>(false))
            {
                if (r == null || r is ParticleSystemRenderer || !r.enabled) continue;
                if (!any) { bounds = r.bounds; any = true; } else bounds.Encapsulate(r.bounds);
            }
            if (!any) { _height = 1f; _footOffset = 0f; return; }
            _height = Mathf.Clamp(bounds.size.y / scale, 0.2f, 5f);
            _footOffset = Mathf.Clamp((bounds.min.y - originY) / scale - _basePos.y, -_height, _height);
        }

        public void Play(string clip, float fade = 0.15f, bool restart = true, string then = null) => Begin(clip, fade, restart, then, 0f);

        public void PlayFrom(string clip, float normalizedStart, float fade = 0.05f, string then = "Idle") =>
            Begin(clip, fade, true, then, Mathf.Clamp01(normalizedStart));

        public void PlayOnce(string clip, string then = "Idle", float fade = 0.1f) => Play(clip, fade, true, then);

        public void SetSpeed(float speed) => _speed = Mathf.Max(0f, speed);

        void Begin(string clip, float fade, bool restart, string then, float start)
        {
            if (!_ready || string.IsNullOrEmpty(clip)) return;
            if (!restart && clip == _name) return;
            if (then == null && clip == "Revive") then = IdleTake;   // un-flatten, then breathe again
            _from = _pose;                      // blend from the pose actually on screen (interrupts never pop)
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
                if (!_loop && _time > _length) _time = _length;   // one-shots hold their end pose (Die stays flat)
                if (_blend < 1f) _blend = _fadeTime <= 0f ? 1f : Mathf.Min(1f, _blend + dt / _fadeTime);
            }
            Evaluate();
            if (_then != null && _time >= _length)
            {
                string next = _then;
                _then = null;
                Begin(next, 0.12f, false, null, 0f);
            }
        }

        void Evaluate()
        {
            var target = Sample(_name, _time);
            _pose = _blend >= 1f ? target : Pose.Lerp(_from, target, _blend);
            Apply(_pose);
        }

        void Apply(in Pose p)
        {
            _visual.localScale = new Vector3(_baseScale.x * p.Sx, _baseScale.y * p.Sy, _baseScale.z * p.Sz);
            _visual.localRotation = _baseRot * Quaternion.Euler(p.Pitch, 0f, p.Roll);
            float grounded = (1f - p.Sy) * _footOffset;
            _visual.localPosition = _basePos + new Vector3(0f, p.Lift * _height + grounded, p.Fwd * _height);
        }

        static Pose Sample(string clip, float time)
        {
            float length = LengthOf(clip);
            float u = Loops(clip) ? Mathf.Repeat(time / length, 1f) : Mathf.Clamp01(time / length);
            switch (clip)
            {
                case "Idle": return Pose.Squash(1f + 0.045f * Mathf.Sin(u * Mathf.PI * 2f));   // slow breathing
                case "Walk": return Hop(u, 0.12f, 0.12f, 3f);
                case "Run": return Hop(u, 0.20f, 0.16f, 7f);
                case "Attack": return Keyed(AttackKeys, u);
                case "Cast": return Keyed(CastKeys, u);
                case "Hit": return Keyed(HitKeys, u);
                case "Die": return Keyed(DieKeys, u);
                case "Revive": return Keyed(ReviveKeys, u);
                default: return Hop(u * 0.5f, 0.10f, 0.08f, 0f);   // Victory / Guard / Talk: one gentle bounce per take
            }
        }

        // Two hops per take: squashed on the ground, stretched at the top of the arc.
        static Pose Hop(float u, float height, float squash, float lean)
        {
            float p = Mathf.Repeat(u * 2f, 1f);
            var pose = Pose.Squash(1f - squash * Mathf.Cos(p * Mathf.PI * 2f), height * Mathf.Sin(p * Mathf.PI), lean);
            return pose;
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
