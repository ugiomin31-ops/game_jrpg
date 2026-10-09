"""Entry point for the hunter-theme kits B.

Run: blender -b --factory-startup --python-exit-code 1 -P Blender/environment/hunter_kits_b/build_kits_b.py -- --kit school
Without --kit, every tileset in this folder is built (school, hospital, guild_street).
Each kit exports 26 pieces + arena to Assets/_Game/Resources/Art/Environment/<tileset>/ and writes previews to
/mnt/project-files/art-upgrade/hunter_v1/env_b/ (copies of the key ones go to Blender/preview/).
"""
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import school  # noqa: E402

KITS = {"school": school}
for _name in ("hospital", "guild_street"):
    try:
        KITS[_name] = __import__(_name)
    except ImportError:
        pass


def main():
    args = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
    names = args[args.index("--kit") + 1].split(",") if "--kit" in args else list(KITS)
    for name in names:
        KITS[name].main()
    print("[hunter_b] DONE", names, flush=True)


if __name__ == "__main__":
    main()
