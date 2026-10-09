"""Build the hunter-theme dungeon kits (subway, factory, cave): 26 pieces + arena each, with previews.

  blender -b --factory-startup --python-exit-code 1 -P Blender/environment/hunter_kits/build_kits_a.py -- --kit subway
  (--kit subway | factory | cave | all; --preview-dir DIR)

Exports Assets/_Game/Resources/Art/Environment/<tileset>/<piece>.fbx (abyss_bpy.export_fbx, same settings as the
other kits). Previews go to the shared folder as <tileset>_corridor.png, <tileset>_arena_wide.png,
<tileset>_arena_battle.png, <tileset>_props.png (plus the layout and contact sheets). No preview images or .blend
files are written into the repo.
"""
import glob
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import common_a  # noqa: E402  (also puts Blender/environment and Blender/lib on sys.path)
import abyss_bpy as A  # noqa: E402

DEFAULT_PREVIEW = "/mnt/project-files/art-upgrade/hunter_v2/kits"
VIEW_NAMES = {"sheet_props": "props", "arena_battlecam": "arena_battle"}
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
    """Rename env_<ts>_<view>.png to <ts>_<view>.png (view names per VIEW_NAMES)."""
    for src in glob.glob(os.path.join(preview_dir, f"env_{ts}_*.png")):
        view = os.path.basename(src)[len(f"env_{ts}_"):-len(".png")]
        dst = os.path.join(preview_dir, f"{ts}_{VIEW_NAMES.get(view, view)}.png")
        os.replace(src, dst)
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
