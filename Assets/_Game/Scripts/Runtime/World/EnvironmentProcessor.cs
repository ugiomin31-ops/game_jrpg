using System.Collections.Generic;
using UnityEngine;

namespace Abyss.Runtime.World
{
    /// <summary>
    /// Applies the Blender naming conventions to an instantiated static environment model:
    /// <c>Col_*</c> meshes carry invisible import-time colliders, <c>Spot_*</c> objects are indexed as named points,
    /// <c>LightAnchor*</c> objects get a warm point light. Returns the spot index.
    /// </summary>
    public static class EnvironmentProcessor
    {
        /// <summary>
        /// Optional per-anchor override for a <c>LightAnchor*</c> object. Return false to skip its light; lower
        /// <paramref name="intensity"/> or <paramref name="range"/> to dim it. Null (the default) keeps every anchor as authored.
        /// </summary>
        public delegate bool LightAnchorPolicy(string anchorName, ref float intensity, ref float range);

        public sealed class Result
        {
            public readonly Dictionary<string, Transform> Spots = new Dictionary<string, Transform>();
            public readonly List<Light> Lights = new List<Light>();
            public readonly List<Collider> Colliders = new List<Collider>();
        }

        public static Result Process(GameObject root, Color lightColor, float lightIntensity = 2.2f, float lightRange = 7f, bool lights = true,
            LightAnchorPolicy anchorPolicy = null)
        {
            var res = new Result();
            var all = root.GetComponentsInChildren<Transform>(true);
            foreach (var t in all)
            {
                string n = t.name;
                if (n.StartsWith("Col_"))
                {
                    var collider = t.GetComponent<Collider>();
                    var r = t.GetComponent<MeshRenderer>();
                    if (collider != null) res.Colliders.Add(collider);
                    if (r != null) Object.Destroy(r);
                }
                else if (n.StartsWith("Spot_"))
                {
                    res.Spots[n.Substring(5)] = t;
                }
                else if (lights && n.StartsWith("LightAnchor"))
                {
                    float intensity = lightIntensity, range = lightRange;
                    if (anchorPolicy != null && !anchorPolicy(n, ref intensity, ref range)) continue;
                    var l = t.gameObject.AddComponent<Light>();
                    l.type = LightType.Point;
                    l.color = lightColor;
                    l.intensity = intensity;
                    l.range = range;
                    l.shadows = LightShadows.None;
                    res.Lights.Add(l);
                }
            }
            return res;
        }

        /// <summary>Finds a direct-or-nested child by exact name (e.g. "Lid", "Door", "Spikes").</summary>
        public static Transform Find(Transform root, string name)
        {
            if (root.name == name) return root;
            for (int i = 0; i < root.childCount; i++)
            {
                var r = Find(root.GetChild(i), name);
                if (r != null) return r;
            }
            return null;
        }
    }
}
