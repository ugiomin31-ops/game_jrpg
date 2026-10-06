"""Generate eight distinct named townspeople including all required motion clips."""
import os
import sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'lib_humanoid'))
from costumes import NPCS, npc
from produce import produce

if __name__ == '__main__':
    args = sys.argv[sys.argv.index('--') + 1:] if '--' in sys.argv else []
    for name in args or list(NPCS):
        produce(name, lambda name=name: npc(name), npc=True)
