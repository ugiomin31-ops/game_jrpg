using System.Collections.Generic;
using TMPro;
using UnityEngine;

namespace Abyss.UI
{
    /// <summary>Damage-number presentation.</summary>
    public enum UINumberStyle
    {
        /// <summary>White, 44px, hop + bounce.</summary>
        Damage,
        /// <summary>Red, 60px, 0→1.5→1 scale pop, "CRITICAL" tag, after-images.</summary>
        Critical,
        /// <summary>Green, slow rise.</summary>
        Heal,
        /// <summary>Blue MP restore, slow rise.</summary>
        Mp,
        /// <summary>Grey "MISS", slides sideways.</summary>
        Miss,
    }

    /// <summary>
    /// Pooled screen-space popups that track world positions through a <see cref="Camera"/>
    /// (damage, crits, weak/resist tags, heals, MP, misses, multi-hit totals). Lives on the numbers layer
    /// of <see cref="UIRoot"/> (<see cref="UIRoot.Numbers"/>); set <see cref="Camera"/> to the battle camera.
    /// </summary>
    public sealed class UINumberPopup : MonoBehaviour
    {
        const string Mono = "<mspace=0.56em>";
        const float EditPreviewAge = 0.45f;

        sealed class Popup
        {
            public RectTransform Rect;
            public CanvasGroup Group;
            public TextMeshProUGUI Number, Tag, GhostA, GhostB;
            public Vector3 World;
            public Vector2 Offset;
            public float Age, Life;
            public UINumberStyle Style;
            public bool Weak, Text, Active;
        }

        readonly List<Popup> _pool = new List<Popup>(24);
        RectTransform _rt;

        /// <summary>Camera used to project world positions (falls back to <see cref="UnityEngine.Camera.main"/>).</summary>
        public Camera Camera { get; set; }

        internal void Build()
        {
            _rt = (RectTransform)transform;
            _rt.Stretch();
        }

        /// <summary>Spawns a number. <paramref name="weak"/> adds a yellow "WEAK!" tag + shake; <paramref name="resist"/> greys it with "RESIST".</summary>
        public void Spawn(Vector3 world, int amount, UINumberStyle style = UINumberStyle.Damage, bool weak = false, bool resist = false)
        {
            var p = Take();
            p.Style = style;
            p.Weak = weak && style != UINumberStyle.Heal && style != UINumberStyle.Mp;
            p.Text = false;
            string value = Mathf.Abs(amount).ToString("N0");
            float size;
            Color color;
            string tag = "";
            switch (style)
            {
                case UINumberStyle.Critical:
                    size = 60f; color = UITheme.NumCrit;
                    tag = UITheme.Tag(UITheme.NumCrit) + "CRITICAL</color>";
                    break;
                case UINumberStyle.Heal:
                    size = 44f; color = UITheme.NumHeal; value = "+" + value;
                    break;
                case UINumberStyle.Mp:
                    size = 38f; color = UITheme.NumMp; value = "+" + value + "<size=60%> MP</size>";
                    break;
                case UINumberStyle.Miss:
                    size = 36f; color = UITheme.NumResist; value = "MISS";
                    break;
                default:
                    size = 44f; color = Color.white;
                    break;
            }
            if (p.Weak)
            {
                if (style == UINumberStyle.Damage) { size = 50f; color = UITheme.NumWeak; }
                tag = (tag.Length > 0 ? tag + "  " : "") + UITheme.Tag(UITheme.NumWeak) + "<size=125%>WEAK!</size></color>";
            }
            if (resist && style != UINumberStyle.Heal && style != UINumberStyle.Mp)
            {
                size *= 0.85f;
                color = UITheme.NumResist;
                tag = (tag.Length > 0 ? tag + "  " : "") + UITheme.Tag(UITheme.NumResist) + "RESIST</color>";
            }
            Setup(p, world, Mono + value + "</mspace>", color, size, tag);
            p.Tag.fontSize = p.Weak ? 26f : 22f;
            p.Life = style == UINumberStyle.Heal || style == UINumberStyle.Mp ? 1.35f : style == UINumberStyle.Miss ? 0.9f : style == UINumberStyle.Critical ? 1.45f : 1.25f;
            Begin(p);
        }

        /// <summary>Free text popup that rises (status names, "GUARD", "BREAK!").</summary>
        public void SpawnText(Vector3 world, string text, Color color, float size = 34f)
        {
            var p = Take();
            p.Style = UINumberStyle.Heal;
            p.Weak = false;
            p.Text = true;
            Setup(p, world, text, color, size, "");
            p.Life = 1.3f;
            Begin(p);
        }

        /// <summary>Multi-hit total ("3 HITS 1,240") shown after the last hit.</summary>
        public void SpawnHits(Vector3 world, int hits, int total)
        {
            var p = Take();
            p.Style = UINumberStyle.Damage;
            p.Weak = false;
            p.Text = true;
            Setup(p, world, $"<size=70%><color=#ffd27a>{hits} HITS</color></size> {Mono}{total:N0}</mspace>", Color.white, 42f, "");
            p.Offset.y += 64f;
            p.Life = 1.6f;
            Begin(p);
        }

        /// <summary>Removes every active popup.</summary>
        public void Clear()
        {
            foreach (var p in _pool)
            {
                p.Active = false;
                p.Rect.gameObject.SetActive(false);
            }
        }

        Popup Take()
        {
            foreach (var p in _pool)
                if (!p.Active) return p;
            var n = new Popup();
            n.Rect = UIFactory.Rect(transform, "Popup");
            n.Rect.sizeDelta = new Vector2(560f, 96f);
            n.Group = n.Rect.gameObject.AddComponent<CanvasGroup>();
            n.Group.blocksRaycasts = false;
            n.GhostA = MakeText(n.Rect, "GhostA");
            n.GhostB = MakeText(n.Rect, "GhostB");
            n.Number = MakeText(n.Rect, "Number");
            n.Tag = UIFactory.Label(n.Rect, "", 22f, UIFont.Heavy, Color.white, TextAlignmentOptions.Bottom, UITextFx.Heavy, "Tag");
            n.Tag.rectTransform.Place(UIAnchor.Center, new Vector2(0.5f, 0f), new Vector2(0f, 24f), new Vector2(560f, 40f));
            n.Tag.characterSpacing = 4f;
            _pool.Add(n);
            return n;
        }

        static TextMeshProUGUI MakeText(RectTransform parent, string name)
        {
            var t = UIFactory.Label(parent, "", 44f, UIFont.Title, Color.white, TextAlignmentOptions.Center, UITextFx.Heavy, name);
            t.rectTransform.Place(UIAnchor.Center, Vector2.zero, new Vector2(560f, 96f));
            return t;
        }

        void Setup(Popup p, Vector3 world, string text, Color color, float size, string tag)
        {
            p.World = world;
            p.Age = 0f;
            p.Active = true;
            p.Number.text = p.GhostA.text = p.GhostB.text = text;
            p.Number.fontSize = p.GhostA.fontSize = p.GhostB.fontSize = size;
            p.Number.color = color;
            p.GhostA.color = p.GhostB.color = color.WithAlpha(0f);
            p.Tag.text = tag;
            p.Tag.fontSize = 22f;
            p.Tag.rectTransform.anchoredPosition = new Vector2(0f, size * 0.55f);
            // Stagger popups that land on the same spot at the same time.
            int stacked = 0;
            foreach (var o in _pool)
                if (o != p && o.Active && o.Age < 0.35f && (o.World - world).sqrMagnitude < 0.05f) stacked++;
            p.Offset = new Vector2(Random.Range(-16f, 16f), stacked * 48f);
            p.Rect.gameObject.SetActive(true);
            p.Rect.SetAsLastSibling();
        }

        void Begin(Popup p)
        {
            if (!Application.isPlaying) p.Age = EditPreviewAge;
            Evaluate(p);
        }

        void LateUpdate()
        {
            float dt = Time.unscaledDeltaTime;
            for (int i = 0; i < _pool.Count; i++)
            {
                var p = _pool[i];
                if (!p.Active) continue;
                p.Age += dt;
                if (p.Age >= p.Life)
                {
                    p.Active = false;
                    p.Rect.gameObject.SetActive(false);
                    continue;
                }
                Evaluate(p);
            }
        }

        void Evaluate(Popup p)
        {
            var cam = Camera != null ? Camera : Camera.main;
            if (cam == null || _rt == null) { p.Group.alpha = 0f; return; }
            Vector3 sp = cam.WorldToScreenPoint(p.World);
            if (sp.z < 0f) { p.Group.alpha = 0f; return; }
            RectTransformUtility.ScreenPointToLocalPointInRectangle(_rt, sp, null, out var local);

            float a = p.Age, x = 0f, y, scale = 1f, alpha = 1f, ghost = 0f;
            float fadeStart = p.Life - 0.42f;
            switch (p.Style)
            {
                case UINumberStyle.Heal:
                case UINumberStyle.Mp:
                    y = 42f * UITween.Evaluate(UIEase.OutCubic, a / p.Life);
                    if (a < 0.15f) scale = Mathf.Lerp(0.6f, 1f, UITween.Evaluate(UIEase.OutBack, a / 0.15f));
                    alpha = a > fadeStart ? 1f - (a - fadeStart) / 0.42f : Mathf.Clamp01(a / 0.08f);
                    break;
                case UINumberStyle.Miss:
                    x = 44f * UITween.Evaluate(UIEase.OutCubic, a / 0.6f);
                    y = 10f;
                    alpha = a > 0.5f ? 1f - (a - 0.5f) / (p.Life - 0.5f) : 1f;
                    break;
                default:
                    y = Hop(a, p.Text ? 0.45f : 1f);
                    if (p.Style == UINumberStyle.Critical)
                    {
                        scale = a < 0.09f ? Mathf.Lerp(0f, 1.5f, a / 0.09f)
                            : a < 0.24f ? Mathf.Lerp(1.5f, 1f, UITween.Evaluate(UIEase.OutQuad, (a - 0.09f) / 0.15f)) : 1f;
                        if (a > fadeStart) ghost = (a - fadeStart) / 0.42f;
                    }
                    else if (a < 0.12f) scale = Mathf.Lerp(1.3f, 1f, a / 0.12f);
                    if (p.Weak && a > 0.12f && a < 0.36f) x = Mathf.Sin((a - 0.12f) / 0.24f * Mathf.PI * 4f) * 7f;
                    if (a > fadeStart)
                    {
                        float t = (a - fadeStart) / 0.42f;
                        y += 30f * t;
                        alpha = 1f - t;
                    }
                    break;
            }
            p.Rect.anchoredPosition = local + p.Offset + new Vector2(x, y);
            p.Number.rectTransform.localScale = new Vector3(scale, scale, 1f);
            p.Tag.rectTransform.localScale = Vector3.one * Mathf.Min(1f, scale);
            p.Group.alpha = Mathf.Clamp01(alpha);
            if (ghost > 0f)
            {
                SetGhost(p.GhostA, p.Number.color, 1f + ghost * 0.35f, (1f - ghost) * 0.55f, new Vector2(-8f * ghost, 6f * ghost));
                SetGhost(p.GhostB, p.Number.color, 1f + ghost * 0.7f, (1f - ghost) * 0.35f, new Vector2(8f * ghost, 12f * ghost));
            }
            else
            {
                p.GhostA.color = p.GhostA.color.WithAlpha(0f);
                p.GhostB.color = p.GhostB.color.WithAlpha(0f);
            }
        }

        static void SetGhost(TextMeshProUGUI g, Color c, float scale, float alpha, Vector2 offset)
        {
            g.color = c.WithAlpha(alpha);
            g.rectTransform.localScale = new Vector3(scale, scale, 1f);
            g.rectTransform.anchoredPosition = offset;
        }

        /// <summary>Hop curve: rise 26px (back ease, 120ms), settle to 18px, hold.</summary>
        static float Hop(float a, float height)
        {
            if (a < 0.12f) return 26f * height * UITween.Evaluate(UIEase.OutBack, a / 0.12f);
            if (a < 0.3f) return Mathf.Lerp(26f, 18f, UITween.Evaluate(UIEase.OutQuad, (a - 0.12f) / 0.18f)) * height;
            return 18f * height;
        }
    }
}
