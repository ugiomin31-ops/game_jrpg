// Save (de)serialisation of GameState. JSON text only; the Unity layer owns file IO (3 slots + autosave,
// atomic temp-file swap as in save_store.gd).
using System;
using System.Collections.Generic;
using Abyss.Logic.Dungeon;
using Newtonsoft.Json;
using Newtonsoft.Json.Converters;
using Newtonsoft.Json.Linq;
using Newtonsoft.Json.Serialization;

namespace Abyss.Logic.Game
{
    /// <summary>Thrown for unreadable saves (corrupt JSON, or a version newer than this build).</summary>
    public sealed class SaveFormatException : Exception
    {
        public SaveFormatException(string message, Exception inner = null) : base(message, inner) { }
    }

    /// <summary>Lightweight description of a save slot for the load menu.</summary>
    public sealed class SaveSummary
    {
        public Difficulty Difficulty;
        public GameLocation Location;
        public string FloorLabel;
        public string DeepestFloorLabel;
        public int Gold;
        public double PlayTimeSeconds;
        /// <summary>Hero id -> level, in formation order.</summary>
        public List<KeyValuePair<string, int>> Levels = new List<KeyValuePair<string, int>>();
        public bool Cleared;
    }

    /// <summary>Versioned JSON codec for <see cref="GameState"/>.</summary>
    public static class SaveCodec
    {
        /// <summary>Format version written by this build.</summary>
        public const int CurrentVersion = 1;

        /// <summary>
        /// Forward migrations: key = version the document is in, action rewrites the raw JSON in place to
        /// version key + 1. Add an entry here (and bump <see cref="CurrentVersion"/>) whenever the format changes.
        /// </summary>
        static readonly Dictionary<int, Action<JObject>> Migrations = new Dictionary<int, Action<JObject>>();

        static readonly JsonSerializer Serializer = JsonSerializer.Create(new JsonSerializerSettings
        {
            ContractResolver = new DefaultContractResolver { NamingStrategy = new SnakeCaseNamingStrategy() },
            MissingMemberHandling = MissingMemberHandling.Ignore,
            NullValueHandling = NullValueHandling.Ignore,
            Converters = { new StringEnumConverter(new SnakeCaseNamingStrategy()), new GridPosConverter() },
            Formatting = Formatting.None,
        });

        /// <summary>Serialises campaign state including per-floor progress and any unsettled encounter.</summary>
        public static string Serialize(GameState state)
        {
            var root = JObject.FromObject(state, Serializer);
            root.AddFirst(new JProperty("version", CurrentVersion));
            return root.ToString(Formatting.None);
        }

        /// <summary>
        /// Parses a save, applying forward migrations from older versions. When <paramref name="db"/> is given the
        /// result is also repaired against the database (missing heroes/slots, learned skills, vitals, quests).
        /// Throws <see cref="SaveFormatException"/> for corrupt or newer-version saves.
        /// </summary>
        public static GameState Deserialize(string json, GameDB db = null)
        {
            JObject root;
            if (string.IsNullOrWhiteSpace(json)) throw new SaveFormatException("Save is empty");
            try { root = JObject.Parse(json); }
            catch (JsonException e) { throw new SaveFormatException("Save is not valid JSON", e); }
            int version;
            try { version = root.Value<int?>("version") ?? 0; }
            catch (Exception e) when (e is FormatException || e is InvalidCastException || e is OverflowException)
            { throw new SaveFormatException("Save version is invalid", e); }
            if (version < 0) throw new SaveFormatException("Save version is negative");
            if (version > CurrentVersion) throw new SaveFormatException($"Save version {version} is newer than supported {CurrentVersion}");
            for (int v = version; v < CurrentVersion; v++)
                if (Migrations.TryGetValue(v, out var migrate)) migrate(root);
            root.Remove("version");
            GameState state;
            try
            {
                state = root.ToObject<GameState>(Serializer);
                if (state == null) throw new SaveFormatException("Save has no campaign state");
                if (db != null) state.Repair(db);
            }
            catch (Exception e) when (e is JsonException || e is FormatException || e is InvalidCastException || e is OverflowException)
            { throw new SaveFormatException("Save content is invalid", e); }
            return state;
        }

        /// <summary>Load-menu summary of a state.</summary>
        public static SaveSummary Summarize(GameDB db, GameState state)
        {
            var summary = new SaveSummary
            {
                Difficulty = state.Difficulty,
                Location = state.Location,
                FloorLabel = db.Floors[Math.Max(0, Math.Min(db.Floors.Count - 1, state.FloorIndex))].FloorLabel,
                DeepestFloorLabel = db.Floors[Math.Max(0, Math.Min(db.Floors.Count - 1, state.DeepestFloor))].FloorLabel,
                Gold = state.Gold,
                PlayTimeSeconds = state.PlayTimeSeconds,
                Cleared = state.Flags.Contains(GameFlow.FlagCleared),
            };
            foreach (var hero in state.Party) summary.Levels.Add(new KeyValuePair<string, int>(hero.Id, hero.Level));
            return summary;
        }

        /// <summary>GridPos as a compact [x, y] array.</summary>
        sealed class GridPosConverter : JsonConverter<GridPos>
        {
            public override void WriteJson(JsonWriter writer, GridPos value, JsonSerializer serializer)
            {
                writer.WriteStartArray();
                writer.WriteValue(value.X);
                writer.WriteValue(value.Y);
                writer.WriteEndArray();
            }

            public override GridPos ReadJson(JsonReader reader, Type objectType, GridPos existingValue, bool hasExistingValue, JsonSerializer serializer)
            {
                var token = JToken.Load(reader);
                if (token is JArray a && a.Count >= 2) return new GridPos((int)a[0], (int)a[1]);
                if (token is JObject o) return new GridPos(o.Value<int>("x"), o.Value<int>("y"));
                throw new JsonSerializationException("Bad grid position " + token);
            }
        }
    }
}
