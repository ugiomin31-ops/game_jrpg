"""Regenerate all four complete dungeon kits and battle arenas.

Run with C:/Users/User/Tools/Blender/blender.exe -b --factory-startup
-P Blender/environment/regenerate_all.py. Every kit exports its 26 pieces,
contact sheets, placed-layout previews and editable blend; each arena exports
FBX, blend and battle/wide/top previews. -- --biome NAME selects one kit.
"""
import importlib.util
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.join(HERE, "..", "lib"))
from _arenas_a import build as build_arena

SCRIPTS = {
    "verdant_ruins": "verdant_ruins/build_verdant_ruins.py",
    "frost_grotto": "frost_grotto/kit.py",
    "ember_caverns": "ember_caverns/kit.py",
    "haunted_crypt": "haunted_crypt/kit.py",
}


def load(name, relative_path):
    spec = importlib.util.spec_from_file_location(name, os.path.join(HERE, relative_path))
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def main():
    args = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
    selected = args[args.index("--biome") + 1] if "--biome" in args else None
    if selected and selected not in SCRIPTS:
        raise ValueError("Unknown biome: " + selected)
    for ts, script in SCRIPTS.items():
        if selected and selected != ts:
            continue
        kit = load("environment_" + ts, script)
        kit.main()
        if ts == "ember_caverns":
            load("environment_ember_arena", "ember_caverns/arena.py").build()
        else:
            build_arena(ts, haunted=kit if ts == "haunted_crypt" else None)
        print("[environment] PUBLISHED", ts, "26 modular pieces + arena", flush=True)
    print("[environment] REGENERATION COMPLETE", flush=True)


if __name__ == "__main__":
    main()
