"""Generate the 20 playable hunters (Tools/content/spec.py HUNTERS, Blender/lib_anime/hunters_anime.py HUNTER_BUILDERS).
Same ids, rig and clips as the other textured heroes; writes Characters/<id>/<id>.fbx plus <id>_tex/<material>.png.
Run with the full Blender executable:  blender -b --factory-startup -P Blender/heroes/generate_hunters.py -- h_dohyun h_seoa
No arguments builds all 20 hunters.
"""
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path[:0] = [os.path.join(HERE, '..', d) for d in ('lib_anime', 'lib', 'lib_humanoid')]
from hunters_anime import HUNTER_BUILDERS  # noqa: E402
from produce import produce  # noqa: E402

if __name__ == '__main__':
    args = sys.argv[sys.argv.index('--') + 1:] if '--' in sys.argv else []
    for name in args or list(HUNTER_BUILDERS):
        produce(name, HUNTER_BUILDERS[name])
