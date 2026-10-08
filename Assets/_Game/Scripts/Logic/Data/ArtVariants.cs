// Palette variants: a data row may reuse another row's art model ("model") with an RGBA multiplier ("tint").
// Pure lookups so the Unity layer (ArtLibrary, GearDisplay), the editor validator and tests agree on the rule.
using System;

namespace Abyss.Logic
{
    public static class ArtVariants
    {
        /// <summary>Art model id of an enemy: its "model" field, else its own id.</summary>
        public static string EnemyModel(EnemyDef def) => def == null ? "" : string.IsNullOrEmpty(def.Model) ? def.Id : def.Model;

        /// <summary>Art model id for an enemy id; unknown ids (or no database) resolve to themselves.</summary>
        public static string EnemyModel(GameDB db, string enemyId) =>
            db != null && enemyId != null && db.Enemies.TryGetValue(enemyId, out var def) ? EnemyModel(def) : enemyId ?? "";

        /// <summary>
        /// Runtime colour multiplier of an enemy, or null for none. Only palette variants (model differs from the id) are
        /// tinted: rows with their own model already carry their colours (the legacy elite "tint" is baked into their FBX).
        /// </summary>
        public static float[] EnemyTint(EnemyDef def)
        {
            if (def == null || string.IsNullOrEmpty(def.Model) || def.Model == def.Id) return null;
            return IsIdentity(def.Tint) ? null : Normalise(def.Tint);
        }

        public static float[] EnemyTint(GameDB db, string enemyId) =>
            db != null && enemyId != null && db.Enemies.TryGetValue(enemyId, out var def) ? EnemyTint(def) : null;

        /// <summary>Art model id of a gear piece: its "model" field, else its own id.</summary>
        public static string GearModel(EquipmentDef piece) => piece == null ? "" : string.IsNullOrEmpty(piece.Model) ? piece.Id : piece.Model;

        public static string GearModel(GameDB db, string equipmentId) =>
            db != null && equipmentId != null && db.Equipment.TryGetValue(equipmentId, out var piece) ? GearModel(piece) : equipmentId ?? "";

        /// <summary>Colour multiplier of a gear piece, or null when it keeps the model's authored colours.</summary>
        public static float[] GearTint(EquipmentDef piece) => piece == null || IsIdentity(piece.Tint) ? null : Normalise(piece.Tint);

        public static float[] GearTint(GameDB db, string equipmentId) =>
            db != null && equipmentId != null && db.Equipment.TryGetValue(equipmentId, out var piece) ? GearTint(piece) : null;

        /// <summary>Art model id of an item: its "model" field, else its own id.</summary>
        public static string ItemModel(ItemDef item) => item == null ? "" : string.IsNullOrEmpty(item.Model) ? item.Id : item.Model;

        /// <summary>RGBA (missing alpha = 1, missing channels = 1, negatives clamp to 0).</summary>
        public static float[] Normalise(float[] tint)
        {
            var output = new float[] { 1, 1, 1, 1 };
            if (tint == null) return output;
            for (int i = 0; i < Math.Min(4, tint.Length); i++) output[i] = Math.Max(0f, tint[i]);
            return output;
        }

        static bool IsIdentity(float[] tint)
        {
            if (tint == null || tint.Length == 0) return true;
            for (int i = 0; i < Math.Min(4, tint.Length); i++) if (Math.Abs(tint[i] - 1f) > 1e-4f) return false;
            return true;
        }
    }
}
