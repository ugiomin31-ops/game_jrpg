# Complete local-folder transfer

Original folder: `C:\Users\User\Desktop\game`

All **46,476 files**, totaling **4,778,372,383 bytes**, and **2,600 directories** are preserved in the full snapshot attached to the [full-folder-snapshot-20261006 release](https://github.com/ugiomin31-ops/game_jrpg/releases/tag/full-folder-snapshot-20261006).

The repository tree contains **2,833 editable project files**. The full snapshot additionally includes every file in `Library/`, `Build/`, `Temp/`, and the original `.git/` directory (including its existing history and index). `.gitignore` does not exclude any file from the backup. Logs, user settings, source assets, Blender sources, packages, project settings, documentation, store artwork and tools are preserved as well.

The original local folder was retained. The original `.git` metadata is inside the snapshot, rather than nested in the new repository's Git metadata.

## Restore the exact folder contents

1. Download **all** `game-full-snapshot.zip.partNNN` assets plus `snapshot-summary.json` and `full-file-manifest.json` from the release into one empty directory.
2. Verify each downloaded part's SHA-256 against `snapshot-summary.json`.
3. Concatenate the parts in numeric order to reconstruct the ZIP. With Python installed, run this in that directory:

```python
from pathlib import Path
import shutil
with open('game-full-snapshot.zip', 'wb') as destination:
    for part in sorted(Path('.').glob('game-full-snapshot.zip.part[0-9][0-9][0-9]')):
        with part.open('rb') as source:
            shutil.copyfileobj(source, destination)
```

4. Extract the ZIP into a **new empty folder** using a ZIP64-capable archiver. It includes hidden `.git` metadata, so do not extract over an unrelated checkout.
5. Verify each extracted file against the path, byte count and SHA-256 in `full-file-manifest.json`. The manifest records all directories, including empty directories.

The snapshot was independently decompressed and every archived file's SHA-256 was checked before uploading. The editable project copy was checked against the same manifest before committing.
