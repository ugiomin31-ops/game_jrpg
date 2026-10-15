using System.Runtime.InteropServices;

namespace Abyss.Runtime.Persistence
{
    /// <summary>
    /// Browser builds: Application.persistentDataPath lives in Emscripten's IDBFS, which only reaches IndexedDB when the
    /// file system is synced. Saves call Flush so closing the tab right after saving keeps the file.
    /// </summary>
    public static class WebStorage
    {
#if UNITY_WEBGL && !UNITY_EDITOR
        [DllImport("__Internal")] static extern void AbyssSyncFileSystem();
        public static void Flush() => AbyssSyncFileSystem();
#else
        public static void Flush() { }
#endif
    }
}
