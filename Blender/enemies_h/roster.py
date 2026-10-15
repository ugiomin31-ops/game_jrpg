"""Monster v5 roster (enemies_h): the eight hunter-theme monsters of Tools/content/spec.py HUNTER_MONSTERS.

Same sculpted kit (enemies_d/sculpt_kit.py), bone names, seven clips and FBX checks as v3/v4. The ids are not yet
rows of Assets/_Game/Resources/Data/enemies.json; generate_all.py registers them from this file.
"""
SOURCES = {}
for _id in ('goblin', 'goblin_shaman', 'sewer_rat', 'scrap_bot', 'cave_mole', 'mummy_pup', 'orc', 'high_orc'):
    SOURCES[_id] = 'enemies_h/hunter.py'

BOSSES = ()
ELITES = ('high_orc',)
