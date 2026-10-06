using System.Collections;
using System.Collections.Generic;
using UnityEngine;

namespace Abyss.Runtime.Art
{
    /// <summary>
    /// Runtime wrapper around an instantiated character FBX (hero, NPC or enemy): animation, weapon sockets,
    /// hit flash / dissolve (Abyss/Toon properties via MaterialPropertyBlock) and handy anchor points.
    /// </summary>
    public sealed class CharacterModel : MonoBehaviour
    {
        static readonly int FlashId = Shader.PropertyToID("_FlashColor");
        static readonly int DissolveId = Shader.PropertyToID("_Dissolve");
        static readonly int BaseColorId = Shader.PropertyToID("_BaseColor");

        public string ModelId { get; private set; }
        public ClipAnimator Anim { get; private set; }
        public Transform Visual { get; private set; }
        public float Height { get; private set; } = 1.2f;
        public float Radius { get; private set; } = 0.4f;

        readonly List<Renderer> _renderers = new List<Renderer>();
        readonly Dictionary<string, GameObject> _attachments = new Dictionary<string, GameObject>();
        MaterialPropertyBlock _mpb;
        Color _flash = new Color(1, 1, 1, 0);
        float _dissolve;
        Color _tint = Color.white;
        Coroutine _flashRoutine;
        Animator _humanoid;

        internal void Setup(string id, Transform visual, IEnumerable<AnimationClip> clips)
        {
            ModelId = id;
            Visual = visual;
            _mpb = new MaterialPropertyBlock();
            _renderers.AddRange(GetComponentsInChildren<Renderer>(true));
            var animator = visual.GetComponent<Animator>();
            if (animator == null)
                throw new System.InvalidOperationException("Missing Generic-rig or Humanoid Animator: " + id);
            _humanoid = animator.isHuman ? animator : null;
            Anim = visual.gameObject.AddComponent<ClipAnimator>();
            Anim.Init(clips);
            RecomputeBounds();
        }

        /// <summary>Measures the bind-pose bounds (call after scale changes).</summary>
        public void RecomputeBounds()
        {
            var b = new Bounds(transform.position, Vector3.zero);
            bool any = false;
            foreach (var r in _renderers)
            {
                if (r == null || r is ParticleSystemRenderer) continue;
                if (!any) { b = r.bounds; any = true; } else b.Encapsulate(r.bounds);
            }
            if (!any) return;
            Height = Mathf.Max(0.3f, b.max.y - transform.position.y);
            Radius = Mathf.Max(0.25f, Mathf.Max(b.extents.x, b.extents.z));
        }

        /// <summary>World point at the top of the model (damage numbers, status icons).</summary>
        public Vector3 HeadPoint => transform.position + Vector3.up * (Height + 0.15f);
        /// <summary>World point at the visual centre (impacts).</summary>
        public Vector3 CenterPoint => transform.position + Vector3.up * (Height * 0.55f);

        /// <summary>
        /// Finds a bone by name. Humanoid models (VRM, store, Mixamo) have no Blender "weapon.R"/"weapon.L" sockets,
        /// so those map to the avatar's hands; grip offsets for such models are tuned per model.
        /// </summary>
        public Transform FindBone(string boneName)
        {
            var bone = FindDeep(transform, boneName);
            if (bone != null || _humanoid == null) return bone;
            if (boneName == "weapon.R") return _humanoid.GetBoneTransform(HumanBodyBones.RightHand);
            if (boneName == "weapon.L") return _humanoid.GetBoneTransform(HumanBodyBones.LeftHand);
            return null;
        }

        static Transform FindDeep(Transform t, string n)
        {
            if (t.name == n) return t;
            for (int i = 0; i < t.childCount; i++)
            {
                var r = FindDeep(t.GetChild(i), n);
                if (r != null) return r;
            }
            return null;
        }

        /// <summary>Attach a static model (e.g. weapon FBX) to a bone socket; replaces any previous one on that socket.</summary>
        public GameObject Attach(string socket, GameObject prefab)
        {
            if (_attachments.TryGetValue(socket, out var old) && old != null)
            {
                for (int i = _renderers.Count - 1; i >= 0; i--)
                    if (_renderers[i] == null || _renderers[i].transform.IsChildOf(old.transform)) _renderers.RemoveAt(i);
                old.SetActive(false);
                Destroy(old);
            }
            _attachments.Remove(socket);
            if (prefab == null) return null;
            var bone = FindBone(socket);
            if (bone == null) return null;
            var go = Instantiate(prefab, bone, false);
            go.transform.localPosition = Vector3.zero;
            go.transform.localRotation = Quaternion.identity;
            // Undo the bone's accumulated scale so weapons keep their authored size.
            var s = bone.lossyScale;
            go.transform.localScale = new Vector3(1f / Mathf.Max(1e-4f, s.x), 1f / Mathf.Max(1e-4f, s.y), 1f / Mathf.Max(1e-4f, s.z)) * transform.lossyScale.x;
            foreach (var r in go.GetComponentsInChildren<Renderer>(true)) _renderers.Add(r);
            _attachments[socket] = go;
            ApplyBlock();
            return go;
        }

        public void SetTint(Color c) { _tint = c; ApplyBlock(); }

        public void SetDissolve(float amount) { _dissolve = Mathf.Clamp01(amount); ApplyBlock(); }

        /// <summary>Brief white (or coloured) flash on hit.</summary>
        public void Flash(Color color, float duration = 0.12f)
        {
            if (_flashRoutine != null) StopCoroutine(_flashRoutine);
            _flashRoutine = StartCoroutine(FlashRoutine(color, duration));
        }

        IEnumerator FlashRoutine(Color color, float duration)
        {
            float t = 0f;
            while (t < duration)
            {
                t += Time.deltaTime;
                _flash = new Color(color.r, color.g, color.b, Mathf.Lerp(0.85f, 0f, t / duration));
                ApplyBlock();
                yield return null;
            }
            _flash.a = 0f;
            ApplyBlock();
        }

        public IEnumerator DissolveOut(float duration) => DissolveTo(1f, duration);
        public IEnumerator DissolveIn(float duration) => DissolveTo(0f, duration);

        IEnumerator DissolveTo(float target, float duration)
        {
            float from = _dissolve, t = 0f;
            while (t < duration)
            {
                t += Time.deltaTime;
                SetDissolve(Mathf.Lerp(from, target, t / duration));
                yield return null;
            }
            SetDissolve(target);
        }

        void ApplyBlock()
        {
            foreach (var r in _renderers)
            {
                if (r == null || r is ParticleSystemRenderer) continue;
                r.GetPropertyBlock(_mpb);
                _mpb.SetColor(FlashId, _flash);
                _mpb.SetFloat(DissolveId, _dissolve);
                _mpb.SetColor(BaseColorId, _tint);
                r.SetPropertyBlock(_mpb);
            }
        }

        // Locomotion callers repeat this each frame; do not restart their stride or Idle breathing.
        public void Play(string clip, float fade = 0.15f) => Anim?.Play(clip, fade, false);
        public void PlayOnce(string clip, string then = "Idle") => Anim?.PlayOnce(clip, then);
    }
}
