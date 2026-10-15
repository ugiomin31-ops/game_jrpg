using System;
using Abyss.Runtime.Art;
using UnityEngine;

namespace Abyss.Runtime.World
{
    /// <summary>Apply after spawning town, before EnvironmentProcessor.Process and TownCamera.Collect.</summary>
    public static class TownEnrichment
    {
        const string StationPath = "Art/Props/GuildFieldStation/guild_field_gear_station";
        const string StationName = "Guild_Field_Gear_Station";
        const string StationColliderName = "Col_Guild_Field_Gear_Station";

        public static void Apply(GameObject town)
        {
            if (town == null) throw new ArgumentNullException(nameof(town));

            // The shipped FBX keeps this one trunk proxy at its pre-Tripo position.
            // Use transforms before physics has synchronized; preserve world Y, size and rotation.
            var tree = EnvironmentProcessor.Find(town.transform, "Tree_plaza_5");
            var proxy = EnvironmentProcessor.Find(town.transform, "Col_Tree_plaza_-140_10");
            if (tree != null && proxy != null)
                proxy.position = new Vector3(tree.position.x, proxy.position.y, tree.position.z);

            // Keep repeated initialization from adding another station or collider.
            var station = town.transform.Find(StationName);
            if (station == null)
            {
                // Required art: SpawnStatic reports the exact Resources path if it is missing.
                var model = ArtLibrary.SpawnStatic(StationPath, town.transform);
                model.name = StationName;
                station = model.transform;
            }
            station.localPosition = new Vector3(17.3f, 0.03f, -4.9f);
            station.localRotation = Quaternion.Euler(0f, -90f, 0f);

            // Only this empty child uses Col_: Process must never strip the model renderer.
            var collision = station.Find(StationColliderName);
            if (collision == null)
            {
                collision = new GameObject(StationColliderName).transform;
                collision.SetParent(station, false);
            }
            var box = collision.GetComponent<BoxCollider>();
            if (box == null) box = collision.gameObject.AddComponent<BoxCollider>();
            box.center = new Vector3(0f, 0.525f, 0f);
            box.size = new Vector3(1.4f, 1.05f, 0.665f);
            box.isTrigger = false;
        }
    }
}
