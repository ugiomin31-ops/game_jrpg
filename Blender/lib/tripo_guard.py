"""Guard against generator scripts overwriting Tripo-installed FBXs with the old procedural models.

A Tripo-installed asset is marked by `<name>.tripo` next to `<name>.fbx`, or by a `TRIPO` file in the FBX's folder
(enemies / characters / NPCs). export_fbx() in Blender/lib/abyss_bpy.py and Blender/hunters_tripo/common.py call
should_skip() first; a marked target is left untouched.

Override (intentional rebuild or a Tripo install script that writes the marker first): pass force=True to export_fbx,
or set the environment variable ABYSS_OVERWRITE_TRIPO=1.
Pure Python (no bpy) so any script can import it.
"""
import os

ENV_OVERRIDE = "ABYSS_OVERWRITE_TRIPO"


def marker_for(path):
    """Return the Tripo marker file protecting `path` (an .fbx), or None."""
    stem = os.path.splitext(path)[0]
    for marker in (stem + ".tripo", os.path.join(os.path.dirname(path), "TRIPO")):
        if os.path.isfile(marker):
            return marker
    return None


def should_skip(path, force=False):
    """True (after printing a notice) when `path` is Tripo-installed and no override is active."""
    if force or os.environ.get(ENV_OVERRIDE) == "1":
        return False
    if marker_for(path) is None:
        return False
    print("SKIP (Tripo-installed): %s" % path, flush=True)
    return True
