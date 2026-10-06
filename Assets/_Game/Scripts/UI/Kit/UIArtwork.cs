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

        public static Sprite Hero(string id) => Load("Heroes", id);
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
