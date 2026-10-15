"""Monster v3 (sculpted kit) roster: ids rebuilt with enemies_d generators override older sources."""
SOURCES = {}
for _module, _ids in {
    'beasts': ('ice_wolf', 'elite_ice_wolf', 'hellhound', 'elite_hellhound'),
    'flyers': ('bat', 'elite_bat', 'grave_bat', 'phoenix', 'fire_drake', 'elite_fire_drake', 'killer_bee', 'harpy'),
    'critters': ('horned_rabbit', 'yeti', 'elite_yeti', 'penguin_mage', 'lizardman'),
    'bugs': ('frost_spider', 'rhino_beetle', 'elite_rhino_beetle', 'sand_scorpion', 'coral_crab', 'elite_coral_crab',
             'jellyfish'),
    'spirits': ('ghost', 'flame_elemental'),
    'plants': ('slime', 'magma_slime', 'mushroom', 'elite_mushroom', 'sprout', 'mandragora'),
}.items():
    for _id in _ids:
        SOURCES[_id] = f'enemies_d/{_module}.py'
