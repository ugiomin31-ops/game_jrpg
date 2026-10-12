using System;
using UnityEngine;

namespace Abyss.Runtime.Art
{
    /// <summary>
    /// Code-driven flight animation for the winged creatures whose Tripo skin failed the rig gate (bat, killer bee,
    /// elite bat) and therefore ship no skeleton and no authored takes. Selected explicitly by
    /// <see cref="ArtLibrary.IsRiglessFlyer"/> (resolved model id + enemy resource path), never inferred.
    /// APPROVED EXCEPTION to the Tripo-only animation rule (user, 2026-10-12: code-driven runtime animation for
    /// monsters whose Tripo rig fails).
    ///
    /// Hierarchy contract (validated strictly, a mismatch throws): the Visual this component sits on holds exactly
    /// three renderers as direct children, "Body", "Wing_L", "Wing_R". Each wing node sits on its shoulder hinge and
    /// owns a "Hinge*" child (Hinge_L / Hinge_R) whose local position is the hinge-line direction. The whole creature moves / tilts through
    /// the common Visual (so the wings stay attached); the wings only rotate locally around their hinge
    /// (sweep, about the hinge line) and a small tip raise (about the model's forward axis).
    /// Same follow-up / interrupt / speed semantics as <see cref="RiglessBlobAnimator"/>: a new take blends from the
    /// pose actually on screen, speed 0 (pause / hit-stop) freezes the pose.
    /// </summary>
    public sealed class RiglessFlyerAnimator : MonoBehaviour, IModelAnimator
    {
        public const string BodyName = "Body", LeftWingName = "Wing_L", RightWingName = "Wing_R", HingeName = "Hinge";
        public const string IdleTake = "Idle";

        // Lift / Fwd are fractions of the creature height, angles in degrees. WRoll > 0 raises the wing tips,
        // WSweep > 0 sweeps them backwards (a diving / folded wing). Pitch > 0 is nose down.
        struct Pose
        {
            public float Lift, Fwd, Pitch, Roll, WRoll, WSweep;

            public static Pose Of(float lift = 0f, float fwd = 0f, float pitch = 0f, float roll = 0f, float wRoll = 0f, float wSweep = 0f) =>
                new Pose { Lift = lift, Fwd = fwd, Pitch = pitch, Roll = roll, WRoll = wRoll, WSweep = wSweep };

            public static Pose Rest => default;

            public static Pose Lerp(in Pose a, in Pose b, float t) => new Pose
            {
                Lift = Mathf.Lerp(a.Lift, b.Lift, t), Fwd = Mathf.Lerp(a.Fwd, b.Fwd, t),
                Pitch = Mathf.Lerp(a.Pitch, b.Pitch, t), Roll = Mathf.Lerp(a.Roll, b.Roll, t),
                WRoll = Mathf.Lerp(a.WRoll, b.WRoll, t), WSweep = Mathf.Lerp(a.WSweep, b.WSweep, t),
            };
        }

        struct Key
        {
            public float U; public Pose P;
            public Key(float u, Pose p) { U = u; P = p; }
        }

        // Attack contact = 0.4 and Cast release = 0.6 (BattleView.Contact): the dive peak / spread peak land there.
        static readonly Key[] AttackKeys =
        {
            new Key(0.00f, Pose.Rest),
            new Key(0.20f, Pose.Of(0.10f, -0.05f, -12f, 0f, 30f, -12f)),     // rise and rear back, wings up and forward
            new Key(0.40f, Pose.Of(-0.06f, 0.30f, 28f, 0f, -8f, 40f)),       // dive-lunge peak = contact, wings swept back
            new Key(0.62f, Pose.Of(0f, 0.12f, 10f, 0f, 10f, 18f)),
            new Key(1.00f, Pose.Rest),
        };
        static readonly Key[] CastKeys =
        {
            new Key(0.00f, Pose.Rest),
            new Key(0.30f, Pose.Of(0.12f, 0f, 0f, 0f, 22f, -8f)),
            new Key(0.60f, Pose.Of(0.22f, 0f, -8f, 0f, 34f, -18f)),          // rise and spread wide = release point
            new Key(0.68f, Pose.Of(0.14f, 0f, 6f, 0f, -16f, 10f)),           // release snap
            new Key(0.84f, Pose.Of(0.04f, 0f, 0f, 0f, 6f, 0f)),
            new Key(1.00f, Pose.Rest),
        };
        static readonly Key[] HitKeys =
        {
            new Key(0.00f, Pose.Rest),
            new Key(0.20f, Pose.Of(0.02f, -0.12f, -22f, 10f, 18f, 30f)),     // recoil: knocked back, wings flinch
            new Key(0.55f, Pose.Of(0f, -0.03f, 5f, -4f, -6f, 8f)),
            new Key(1.00f, Pose.Rest),
        };
        static readonly Pose DieEnd = Pose.Of(0f, 0f, 70f, 25f, -35f, 70f);  // Lift is replaced by the measured ground drop
        Key[] _dieKeys, _reviveKeys;

        Transform _visual, _body, _wingL, _wingR;
        Vector3 _basePos, _baseScale;
        Quaternion _baseRot;
        float _height = 1f, _dieDrop;
        Vector3 _center;                                  // rest bounds centre in Visual-local space (rotation pivot of the whole creature)
        Vector3 _restMin, _restMax;                       // rest bounds in Visual-local space
        Quaternion _restL, _restR;
        Vector3 _hingeL, _hingeR;                         // hinge axes in Visual space
        float _rollSignL, _rollSignR, _sweepSignL, _sweepSignR;
        Pose _pose = Pose.Rest, _from = Pose.Rest;
        string _name, _then;
        float _time, _length = 1f, _blend = 1f, _fadeTime, _speed = 1f;
        bool _loop, _ready;

        public string CurrentClip => _name;
        public float NormalizedTime => _name == null ? 0f : _time / _length;

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
                case "Idle": return 1.0f;
                case "Walk": return 0.6f;
                case "Run": return 0.5f;
                case "Attack": return 0.7f;
                case "Cast": return 0.9f;
                case "Hit": return 0.35f;
                case "Die": return 0.8f;
                case "Revive": return 0.6f;
                default: return 0.8f;
            }
        }

        static bool Loops(string clip) =>
            clip != "Attack" && clip != "Cast" && clip != "Hit" && clip != "Die" && clip != "Revive";

        public bool HasClip(string clip) => Supports(clip);
        public float Length(string clip) => string.IsNullOrEmpty(clip) ? 0f : LengthOf(clip);

        /// <summary>Rest bounds of the three parts in world space, independent of the pose currently shown.</summary>
        public Bounds RestWorldBounds()
        {
            var parent = _visual.parent;
            Matrix4x4 rest = (parent != null ? parent.localToWorldMatrix : Matrix4x4.identity) * Matrix4x4.TRS(_basePos, _baseRot, _baseScale);
            var b = new Bounds(rest.MultiplyPoint3x4(_restMin), Vector3.zero);
            for (int i = 0; i < 8; i++)
                b.Encapsulate(rest.MultiplyPoint3x4(new Vector3((i & 1) == 0 ? _restMin.x : _restMax.x, (i & 2) == 0 ? _restMin.y : _restMax.y, (i & 4) == 0 ? _restMin.z : _restMax.z)));
            return b;
        }

        /// <summary>Validate the hierarchy, measure the rest pose BEFORE any hover / flap is applied, then start Idle.</summary>
        public void Init()
        {
            if (_ready) throw new InvalidOperationException("RiglessFlyerAnimator already initialized: " + name);
            _visual = transform;
            _body = RequirePart(BodyName);
            _wingL = RequirePart(LeftWingName);
            _wingR = RequirePart(RightWingName);
            foreach (Transform child in _visual)
                if (child != _body && child != _wingL && child != _wingR && child.GetComponentInChildren<Renderer>(true) != null)
                    throw new InvalidOperationException($"Flyer model {name} has an unexpected renderer node '{child.name}' (only Body / Wing_L / Wing_R allowed).");
            _basePos = _visual.localPosition; _baseRot = _visual.localRotation; _baseScale = _visual.localScale;
            _restL = _wingL.localRotation; _restR = _wingR.localRotation;
            MeasureRest();
            ReadWing(_wingL, _restL, out _hingeL, out _rollSignL, out _sweepSignL);
            ReadWing(_wingR, _restR, out _hingeR, out _rollSignR, out _sweepSignR);
            _dieDrop = MeasureDieDrop();
            _dieKeys = new[]
            {
                new Key(0.00f, Pose.Rest),
                new Key(0.20f, Pose.Of(0.05f, -0.05f, -15f, 6f, 30f, 15f)),
                new Key(0.60f, Pose.Of(-_dieDrop / _height, 0f, DieEnd.Pitch * 1.05f, DieEnd.Roll, DieEnd.WRoll, DieEnd.WSweep)),   // thump, slight overshoot
                new Key(1.00f, Pose.Of(-_dieDrop / _height, 0f, DieEnd.Pitch, DieEnd.Roll, DieEnd.WRoll, DieEnd.WSweep)),           // held
            };
            _reviveKeys = new[]
            {
                new Key(0.00f, _dieKeys[3].P),
                new Key(0.45f, Pose.Of(0.12f, 0f, -8f, 0f, 24f, -6f)),
                new Key(0.75f, Pose.Of(0.04f, 0f, 3f, 0f, 8f, 4f)),
                new Key(1.00f, Pose.Rest),
            };
            _ready = true;
            Begin(IdleTake, 0f, true, null, 0f);
        }

        Transform RequirePart(string partName)
        {
            Transform found = null;
            int count = 0;
            foreach (Transform child in _visual)
                if (child.name == partName) { found = child; count++; }
            if (count != 1)
                throw new InvalidOperationException($"Flyer model {name} needs exactly one direct child '{partName}' under its Visual (found {count}).");
            if (found.GetComponent<MeshRenderer>() == null || found.GetComponent<MeshFilter>() == null || found.GetComponent<MeshFilter>().sharedMesh == null)
                throw new InvalidOperationException($"Flyer part {name}/{partName} has no MeshFilter + MeshRenderer.");
            return found;
        }

        // Rest bounds from the meshes' local bounds (rotation correct, no dependency on the pose on screen).
        void MeasureRest()
        {
            Matrix4x4 toVisual = _visual.worldToLocalMatrix;
            bool first = true;
            _restMin = _restMax = Vector3.zero;
            foreach (var part in new[] { _body, _wingL, _wingR })
            {
                var mesh = part.GetComponent<MeshFilter>().sharedMesh;
                Matrix4x4 m = toVisual * part.localToWorldMatrix;
                Vector3 c = mesh.bounds.center, e = mesh.bounds.extents;
                for (int i = 0; i < 8; i++)
                {
                    var p = m.MultiplyPoint3x4(c + new Vector3((i & 1) == 0 ? -e.x : e.x, (i & 2) == 0 ? -e.y : e.y, (i & 4) == 0 ? -e.z : e.z));
                    if (first) { _restMin = _restMax = p; first = false; }
                    else { _restMin = Vector3.Min(_restMin, p); _restMax = Vector3.Max(_restMax, p); }
                }
            }
            _center = (_restMin + _restMax) * 0.5f;
            _height = Mathf.Clamp((_restMax.y - _restMin.y) * Mathf.Abs(_baseScale.y), 0.2f, 5f);
        }

        void ReadWing(Transform wing, Quaternion rest, out Vector3 hinge, out float rollSign, out float sweepSign)
        {
            Transform hingeNode = null;
            foreach (Transform child in wing)
                if (child.name.StartsWith(HingeName, StringComparison.Ordinal)) { hingeNode = child; break; }
            if (hingeNode == null || hingeNode.localPosition.sqrMagnitude < 1e-8f)
                throw new InvalidOperationException($"Flyer wing {name}/{wing.name} has no '{HingeName}' child (hinge direction).");
            hinge = (rest * hingeNode.localPosition).normalized;
            var mesh = wing.GetComponent<MeshFilter>().sharedMesh;
            Vector3 tip = rest * mesh.bounds.center;            // wing origin = shoulder hinge, so the bounds centre points at the wing
            if (tip.sqrMagnitude < 1e-8f)
                throw new InvalidOperationException($"Flyer wing {name}/{wing.name} mesh is centred on its hinge (pivot not set on the shoulder).");
            rollSign = Vector3.Cross(Vector3.forward, tip).y >= 0f ? 1f : -1f;    // + raises the wing tip
            sweepSign = Vector3.Cross(hinge, tip).z <= 0f ? 1f : -1f;             // + sweeps the wing tip backwards
        }

        // Ground drop of the held Die pose, so the fallen creature lies on the floor (parent-local units).
        float MeasureDieDrop()
        {
            var parent = _visual.parent;
            float scale = parent != null ? Mathf.Max(1e-4f, Mathf.Abs(parent.lossyScale.y)) : 1f;
            float groundY = parent != null ? parent.position.y : 0f;
            Apply(Pose.Of(0f, 0f, DieEnd.Pitch, DieEnd.Roll, DieEnd.WRoll, DieEnd.WSweep));
            float minY = float.MaxValue;
            foreach (var part in new[] { _body, _wingL, _wingR })
            {
                var mesh = part.GetComponent<MeshFilter>().sharedMesh;
                Matrix4x4 m = part.localToWorldMatrix;
                Vector3 c = mesh.bounds.center, e = mesh.bounds.extents;
                for (int i = 0; i < 8; i++)
                    minY = Mathf.Min(minY, m.MultiplyPoint3x4(c + new Vector3((i & 1) == 0 ? -e.x : e.x, (i & 2) == 0 ? -e.y : e.y, (i & 4) == 0 ? -e.z : e.z)).y);
            }
            Apply(Pose.Rest);
            return Mathf.Max(0f, (minY - groundY) / scale);
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
            if (then == null && clip == "Revive") then = IdleTake;
            _from = _pose;                       // blend from the pose actually on screen (interrupts never pop)
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
                if (!_loop && _time > _length) _time = _length;   // one-shots hold their end pose (Die stays down)
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
            // Whole creature through the common Visual: tilt about the rest centre (not the ground pivot), then offset.
            var tilt = Quaternion.Euler(p.Pitch, 0f, p.Roll);
            Vector3 pivotShift = _baseRot * Vector3.Scale(_baseScale, _center - tilt * _center);
            _visual.localRotation = _baseRot * tilt;
            _visual.localPosition = _basePos + pivotShift + new Vector3(0f, p.Lift * _height, p.Fwd * _height);
            // Wings only rotate locally around their hinge: sweep about the hinge line, tip raise about forward.
            _wingL.localRotation = Quaternion.AngleAxis(_rollSignL * p.WRoll, Vector3.forward) * Quaternion.AngleAxis(_sweepSignL * p.WSweep, _hingeL) * _restL;
            _wingR.localRotation = Quaternion.AngleAxis(_rollSignR * p.WRoll, Vector3.forward) * Quaternion.AngleAxis(_sweepSignR * p.WSweep, _hingeR) * _restR;
        }

        Pose Sample(string clip, float time)
        {
            float length = LengthOf(clip);
            float u = Loops(clip) ? Mathf.Repeat(time / length, 1f) : Mathf.Clamp01(time / length);
            const float Tau = Mathf.PI * 2f;
            switch (clip)
            {
                case "Idle":   // hover bob and a relaxed double flap per take (rest pose at u = 0)
                    return Pose.Of(0.035f * Mathf.Sin(u * Tau * 2f - 0.6f) + 0.035f * Mathf.Sin(0.6f), 0f, 0f, 0f, 16f * Mathf.Sin(u * Tau * 2f), 10f * Mathf.Sin(u * Tau * 2f - 0.9f));
                case "Walk":   // faster flap, slight forward lean
                    return Pose.Of(0.03f * Mathf.Sin(u * Tau * 3f), 0f, 6f, 0f, 22f * Mathf.Sin(u * Tau * 3f), 14f * Mathf.Sin(u * Tau * 3f - 0.9f));
                case "Run":
                    return Pose.Of(0.04f * Mathf.Sin(u * Tau * 4f), 0f, 14f, 0f, 26f * Mathf.Sin(u * Tau * 4f), 16f * Mathf.Sin(u * Tau * 4f - 0.9f) + 6f);
                case "Attack": return Keyed(AttackKeys, u);
                case "Cast": return Keyed(CastKeys, u);
                case "Hit": return Keyed(HitKeys, u);
                case "Die": return Keyed(_dieKeys, u);
                case "Revive": return Keyed(_reviveKeys, u);
                default:       // Victory / Guard / Talk: one lazy flap per take
                    return Pose.Of(0.03f * Mathf.Sin(u * Tau), 0f, 0f, 0f, 14f * Mathf.Sin(u * Tau), 8f * Mathf.Sin(u * Tau - 0.9f));
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
