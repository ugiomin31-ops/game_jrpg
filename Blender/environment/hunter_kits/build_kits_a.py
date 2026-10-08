"""Build the hunter-theme dungeon kits (subway, factory, cave): 26 pieces + arena each, with previews.

  blender -b --factory-startup --python-exit-code 1 -P Blender/environment/hunter_kits/build_kits_a.py -- --kit subway
  (--kit subway | factory | cave | all; --preview-dir DIR)

Exports Assets/_Game/Resources/Art/Environment/<tileset>/<piece>.fbx (abyss_bpy.export_fbx, same settings as the
other kits). Previews land in the shared preview folder as <tileset>_sheet.png, <tileset>_corridor.png and
<tileset>_arena_*.png, and are copied to Blender/preview/hunter_a/. No .blend files are written into the repo.
"""
import glob
import os
import shutil
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import common_a  # noqa: E402  (also puts Blender/environment and Blender/lib on sys.path)
import abyss_bpy as A  # noqa: E402

REPO_PREVIEW = os.path.normpath(os.path.join(HERE, "..", "..", "preview", "hunter_a"))
DEFAULT_PREVIEW = "/mnt/project-files/art-upgrade/hunter_v1/env_a"
KITS = ("subway", "factory", "cave")


def kit_class(name):
    if name == "subway":
        from subway import SubwayKit
        return SubwayKit
    if name == "factory":
        from factory import FactoryKit
        return FactoryKit
    if name == "cave":
        from cave import CaveKit
        return CaveKit
    raise SystemExit(f"unknown kit: {name}")


def arg(args, key, default):
    return args[args.index(key) + 1] if key in args else default


def publish_previews(ts, preview_dir):
    """Rename env_<ts>_*.png to <ts>_*.png (the names the kit previews are asked for) and copy to the repo."""
    os.makedirs(REPO_PREVIEW, exist_ok=True)
    for src in glob.glob(os.path.join(preview_dir, f"env_{ts}_*.png")):
        dst = os.path.join(preview_dir, os.path.basename(src).replace(f"env_{ts}_", f"{ts}_", 1))
        os.replace(src, dst)
        shutil.copy2(dst, os.path.join(REPO_PREVIEW, os.path.basename(dst)))
        print("[preview]", dst, flush=True)


def main():
    args = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
    choice = arg(args, "--kit", "subway")
    preview_dir = arg(args, "--preview-dir", DEFAULT_PREVIEW)
    names = KITS if choice == "all" else (choice,)
    A.PREVIEW_DIR = preview_dir
    A.save_blend = lambda name: None  # blend files are not written into the repo
    os.makedirs(preview_dir, exist_ok=True)
    for name in names:
        kit = kit_class(name)()
        kit.run_all()
        publish_previews(kit.TS, preview_dir)
        print(f"[hunter_kits] {name}: 26 pieces + arena exported", flush=True)


if __name__ == "__main__":
    main()
