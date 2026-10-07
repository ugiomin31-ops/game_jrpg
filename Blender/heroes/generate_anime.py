"""Generate the textured anime heroes (VRoid-based, Blender/lib_anime/heroes_anime.py HERO_BUILDERS).
Same ids, rig and clips as the chibi heroes; writes Characters/<id>/<id>.fbx plus <id>_tex/<material>.png.
Run with full Blender executable:  blender -b --factory-startup -P Blender/heroes/generate_anime.py -- archer
Promoted job outfits (Blender/lib_anime/jobs_anime.py JOB_BUILDERS, e.g. knight, archmage) are produced the same way
by id; `-- jobs` produces all 16 of them, no argument produces the four base heroes.
"""
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path[:0] = [os.path.join(HERE, '..', d) for d in ('lib_anime', 'lib', 'lib_humanoid')]
from heroes_anime import HERO_BUILDERS  # noqa: E402
from jobs_anime import JOB_BUILDERS  # noqa: E402
from produce import produce  # noqa: E402

BUILDERS = {**HERO_BUILDERS, **JOB_BUILDERS}

if __name__ == '__main__':
    args = sys.argv[sys.argv.index('--') + 1:] if '--' in sys.argv else []
    if args == ['jobs']:
        args = list(JOB_BUILDERS)
    for name in args or list(HERO_BUILDERS):
        produce(name, BUILDERS[name])
