mergeInto(LibraryManager.library, {
  // Push Emscripten's in-memory copy of persistentDataPath to IndexedDB (see WebStorage.cs).
  AbyssSyncFileSystem: function () {
    if (typeof FS !== "undefined" && FS.syncfs) FS.syncfs(false, function (err) { if (err) console.warn("Abyss save sync failed", err); });
  }
});
