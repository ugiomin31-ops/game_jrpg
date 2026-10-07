using System;
using System.IO;
using System.Text;
using Abyss.Logic;
using Abyss.Logic.Game;

namespace Abyss.Runtime.Persistence
{
    public sealed class SaveRepository
    {
        readonly string directory;
        readonly GameDB database;
        public SaveRepository(string directory, GameDB database)
        {
            this.directory = directory;
            this.database = database;
        }
        string PathFor(int slot)
        {
            if (slot < -1 || slot > 2) throw new ArgumentOutOfRangeException(nameof(slot));
            return Path.Combine(directory, slot == -1 ? "autosave.json" : "slot_" + (slot + 1) + ".json");
        }
        public bool Exists(int slot) => File.Exists(PathFor(slot));
        public DateTime? SlotTime(int slot) => Exists(slot) ? File.GetLastWriteTime(PathFor(slot)) : (DateTime?)null;
        public GameState Read(int slot) => SaveCodec.Deserialize(File.ReadAllText(PathFor(slot), Encoding.UTF8), database);
        public SaveSummary Summary(int slot) => SaveCodec.Summarize(database, Read(slot));
        public void Write(int slot, GameState state)
        {
            Directory.CreateDirectory(directory);
            AtomicWrite(PathFor(slot), SaveCodec.Serialize(state));
        }
        internal static void AtomicWrite(string path, string text)
        {
            byte[] bytes = new UTF8Encoding(false).GetBytes(text);
#if UNITY_WEBGL && !UNITY_EDITOR
            // Browser builds keep files in an in-memory FS mirrored to IndexedDB; write in place and push it to storage.
            File.WriteAllBytes(path, bytes);
            WebStorage.Flush();
#else
            string temporary = path + ".tmp";
            using (var stream = new FileStream(temporary, FileMode.Create, FileAccess.Write, FileShare.None, 4096, FileOptions.WriteThrough))
            {
                stream.Write(bytes, 0, bytes.Length);
                stream.Flush(true);
            }
            if (File.Exists(path)) File.Replace(temporary, path, null);
            else File.Move(temporary, path);
#endif
        }
    }
}
