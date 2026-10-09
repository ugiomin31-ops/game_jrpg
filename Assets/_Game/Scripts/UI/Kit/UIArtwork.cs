using System;
using System.Collections.Generic;
using Abyss.Logic;
using UnityEngine;

namespace Abyss.UI
{
    /// <summary>Production 3D-rendered sprites. Missing art is an asset error, never substitute art.</summary>
    public static class UIArtwork
    {
        static readonly Dictionary<string, Sprite> cache = new Dictionary<string, Sprite>(StringComparer.Ordinal);

        static Sprite Load(string family, string id)
        {
            if (string.IsNullOrEmpty(id) || id.IndexOf('/') >= 0 || id.IndexOf('\\') >= 0)
                throw new ArgumentException("A production artwork ID is required.", nameof(id));
            string key = family + "/" + id;
            if (cache.TryGetValue(key, out var sprite)) return sprite;
            sprite = Resources.Load<Sprite>("Icons/" + key);
            if (sprite == null) throw new InvalidOperationException("Missing production UI sprite: Icons/" + key);
            cache.Add(key, sprite);
            return sprite;
        }

        static readonly HashSet<string> missing = new HashSet<string>(StringComparer.Ordinal);

        /// <summary>Returns the sprite or null when it does not exist (job portraits only; everything else must exist).</summary>
        static Sprite TryLoad(string family, string id)
        {
            string key = family + "/" + id;
            if (cache.TryGetValue(key, out var sprite)) return sprite;
            if (missing.Contains(key)) return null;
            sprite = Resources.Load<Sprite>("Icons/" + key);
            if (sprite == null) { missing.Add(key); return null; }
            cache.Add(key, sprite);
            return sprite;
        }

        /// <summary>
        /// Hero id -> current job id, set by the game UI. <see cref="Hero"/> shows the job portrait
        /// (Icons/Heroes/&lt;job&gt;) when one exists and falls back to the hero's own portrait.
        /// </summary>
        public static Func<string, string> HeroJob;

        /// <summary>A hunter's own portrait; a hunter without one shows its job's, then its class's portrait.</summary>
        public static Sprite Hero(string id)
        {
            if (string.IsNullOrEmpty(id)) return Load("Heroes", id);
            var own = TryLoad("Heroes", id);
            if (own != null) return own;
            string job = HeroJob?.Invoke(id);
            if (!string.IsNullOrEmpty(job) && job.IndexOf('/') < 0 && job.IndexOf('\\') < 0)
            {
                var sprite = TryLoad("Heroes", job);
                if (sprite != null) return sprite;
            }
            return Load("Heroes", Abyss.Logic.GameDB.Instance?.ClassOf(id) ?? id);
        }

        /// <summary>Portrait of a job (falls back to the hero's portrait when the job has none).</summary>
        public static Sprite Job(string jobId, string heroId) => (string.IsNullOrEmpty(jobId) ? null : TryLoad("Heroes", jobId)) ?? Load("Heroes", heroId);
        public static Sprite NPC(string id) => Load("NPCs", id);
        public static Sprite Enemy(string id) => Load("Enemies", id);
        public static Sprite Gear(string id) => Load("Gear", id);
        public static Sprite Item(string id) => Load("Items", id);
        public static Sprite Status(string id) => Load("Status", id);
        public static Sprite Element(string id) => Load("Elements", id);
        public static Sprite Command(string id) => Load("UI", id);

        public static Sprite Element(Abyss.Logic.Element element)
        {
            switch (element)
            {
                case Abyss.Logic.Element.Slash: return Element("slash");
                case Abyss.Logic.Element.Blunt: return Element("blunt");
                case Abyss.Logic.Element.Pierce: return Element("pierce");
                case Abyss.Logic.Element.Fire: return Element("fire");
                case Abyss.Logic.Element.Ice: return Element("ice");
                case Abyss.Logic.Element.Thunder: return Element("thunder");
                case Abyss.Logic.Element.Dark: return Element("dark");
                case Abyss.Logic.Element.Holy: return Element("holy");
                default: return null; // Neutral damage has no authored element emblem.
            }
        }
    }
}
