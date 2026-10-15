"""Monster v4 roster (enemies_e): the 23 new models of chapters 5 (가라앉은 신전) and 6 (심연의 핵).

Same sculpted kit (enemies_d/sculpt_kit.py), bone names, seven clips and FBX checks as v3; the two bosses also
carry the `Roar` clip and the boss preview set. ids, Korean names and ranks match Tools/content/spec.py NEW_MODELS.
"""
SOURCES = {}
for _module, _ids in {
    'sea': ('puffer', 'merfolk_guard', 'angler', 'giant_clam', 'sea_urchin', 'temple_guardian', 'sea_serpent',
            'drowned_knight', 'naga_priestess', 'turtle_titan', 'siren', 'leviathan'),
    'abyss': ('void_eye', 'shadow_beast', 'chaos_spawn', 'gargoyle', 'nightmare', 'doppelganger', 'abyss_worm',
              'fallen_angel', 'void_reaper', 'crystal_horror', 'abyss_lord'),
}.items():
    for _id in _ids:
        SOURCES[_id] = f'enemies_e/{_module}.py'

BOSSES = ('leviathan', 'abyss_lord')
ELITES = ('drowned_knight', 'naga_priestess', 'turtle_titan', 'fallen_angel', 'void_reaper', 'crystal_horror')
