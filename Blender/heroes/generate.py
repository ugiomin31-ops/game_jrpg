"""Generate all four weapon-free chibi heroes (warrior shield is body-owned).
Reference: abyss_ref/art/characters/<id>/full.png. Run with full Blender executable.
"""
import os
import sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'lib_humanoid'))
from costumes import HERO_BUILDERS
from produce import produce

if __name__ == '__main__':
    args = sys.argv[sys.argv.index('--') + 1:] if '--' in sys.argv else []
    for name in args or list(HERO_BUILDERS):
        produce(name, HERO_BUILDERS[name])
