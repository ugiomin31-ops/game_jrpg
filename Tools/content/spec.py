"""Content plan for the 20-hour campaign: the single source of truth for new IDs.

Every worker that adds data, code or art for the expansion uses the IDs below, so monsters, drops, gear,
floors and models line up without waiting on each other. Stats, skills, drop chances, map layouts and
descriptions are left to the data generators; only names, chapters, roles and models are fixed here.
See docs/CONTENT_20H_PLAN.md for the design rationale.
"""

# ------------------------------------------------------------------ chapters (30 main floors + 5 postgame)
# Each chapter is 5 floors. Floor 3 holds the mid-boss FOE, floor 5 the chapter boss. Levels are the party
# level the chapter is tuned for (enter -> leave). Tilesets reuse the four existing kits; Ch5/Ch6/postgame
# get their own fog, light and overlay so they read as new places.
CHAPTERS = [
    dict(n=1, id='verdant', name='이끼 낀 숲의 유적', tileset='verdant_ruins', levels=(1, 12), boss='forest_guardian'),
    dict(n=2, id='frost', name='얼어붙은 해식동굴', tileset='frost_grotto', levels=(12, 24), boss='frost_kraken'),
    dict(n=3, id='ember', name='작열하는 용암굴', tileset='ember_caverns', levels=(24, 34), boss='flame_sphinx'),
    dict(n=4, id='crypt', name='망자의 묘소', tileset='haunted_crypt', levels=(34, 44), boss='boss'),
    dict(n=5, id='sunken', name='가라앉은 신전', tileset='frost_grotto', levels=(44, 54), boss='leviathan'),
    dict(n=6, id='abyss', name='심연의 핵', tileset='haunted_crypt', levels=(54, 64), boss='abyss_lord'),
    dict(n=7, id='trial', name='시련의 회랑 (클리어 후)', tileset='ember_caverns', levels=(64, 70), boss='abyss_lord_ex'),
]
LEVEL_CAP = 70

# ------------------------------------------------------------------ jobs
# Advanced job: Lv 15 and the Ch1 boss defeated, pay a 전직의 증표 (job_medal). Master job: Lv 40, the Ch4
# boss defeated, pay a 마스터의 인장 (master_seal). A job keeps the hero (face, hair, learned skills); the
# outfit model changes to Art/Characters/<job>/<job>.fbx (already authored in Blender/lib_anime/jobs_anime.py).
JOB_TREE = {
    'warrior': ('knight', 'berserker'), 'knight': ('paladin',), 'berserker': ('warlord',),
    'mage': ('elementalist', 'warlock'), 'elementalist': ('archmage',), 'warlock': ('abyssal',),
    'archer': ('sniper', 'ranger'), 'sniper': ('divine_archer',), 'ranger': ('shadow_stalker',),
    'cleric': ('priest', 'exorcist'), 'priest': ('saint',), 'exorcist': ('inquisitor',),
}
JOB_NAMES_KO = {
    'warrior': '전사', 'knight': '기사', 'paladin': '성기사', 'berserker': '광전사', 'warlord': '워로드',
    'mage': '마법사', 'elementalist': '원소술사', 'archmage': '대마도사', 'warlock': '흑마법사', 'abyssal': '심연술사',
    'archer': '궁수', 'sniper': '저격수', 'divine_archer': '신궁', 'ranger': '레인저', 'shadow_stalker': '그림자 추적자',
    'cleric': '사제', 'priest': '신관', 'saint': '성녀', 'exorcist': '퇴마사', 'inquisitor': '심판관',
}

# ------------------------------------------------------------------ monsters
# Existing 51 enemies stay (re-levelled into chapters 1-4 by the world data). New enemies are either
# palette variants of an existing model (data field "model" = base enemy id, "tint" = RGBA multiplier) or
# brand-new models built in Blender (model = own id). archetype must be one of body_only / flyer / blob.
VARIANTS = [
    # id, Korean name, base model, tint (r, g, b), chapter, role
    ('metal_slime', '메탈 슬라임', 'slime', (0.78, 0.82, 0.92), 0, 'rare: tiny HP, huge defence, flees, big EXP'),
    ('gold_slime', '황금 슬라임', 'slime', (1.0, 0.82, 0.32), 0, 'rare: flees, drops lots of gold'),
    ('poison_mushroom', '독버섯', 'mushroom', (0.72, 0.45, 0.95), 1, 'poison'),
    ('snow_rabbit', '설원 뿔토끼', 'horned_rabbit', (0.92, 0.96, 1.0), 2, 'fast'),
    ('ice_slime', '얼음 슬라임', 'slime', (0.55, 0.85, 1.0), 2, 'ice'),
    ('frost_bee', '서리벌', 'killer_bee', (0.6, 0.85, 1.0), 2, 'freeze sting'),
    ('ember_bee', '화염벌', 'killer_bee', (1.0, 0.45, 0.25), 3, 'burn sting'),
    ('lava_beetle', '용암 장수풍뎅이', 'rhino_beetle', (1.0, 0.42, 0.22), 3, 'tank'),
    ('flame_wisp', '불꽃 도깨비불', 'wisp', (1.0, 0.55, 0.2), 3, 'fire caster'),
    ('crimson_scorpion', '진홍 전갈', 'sand_scorpion', (1.0, 0.3, 0.3), 3, 'poison crit'),
    ('skeleton_mage', '해골 마법사', 'skeleton', (0.75, 0.6, 1.0), 4, 'dark caster'),
    ('dark_pixie', '어둠 요정', 'pixie', (0.6, 0.4, 0.9), 4, 'debuffer'),
    ('ghost_mushroom', '유령 버섯', 'mushroom', (0.7, 0.9, 0.95), 4, 'sleep spores'),
    ('crypt_hound', '묘소 사냥개', 'hellhound', (0.55, 0.6, 0.75), 4, 'pack'),
    ('deep_jelly', '심해 해파리', 'jellyfish', (0.55, 0.45, 1.0), 5, 'thunder'),
    ('swamp_lizardman', '늪 리자드맨', 'lizardman', (0.45, 0.8, 0.5), 5, 'poison spear'),
    ('storm_harpy', '폭풍 하피', 'harpy', (0.7, 0.55, 1.0), 5, 'thunder'),
    ('coral_golem', '산호 골렘', 'ice_golem', (1.0, 0.55, 0.6), 5, 'tank'),
    ('tide_drake', '조류 드레이크', 'fire_drake', (0.35, 0.8, 0.85), 5, 'water breath (ice)'),
    ('golden_mimic', '황금 미믹', 'mimic', (1.0, 0.8, 0.3), 5, 'rare: drops rare gear'),
    ('void_wisp', '공허의 도깨비불', 'wisp', (0.55, 0.35, 0.95), 6, 'dark caster'),
    ('void_knight', '공허 기사', 'dark_knight', (0.55, 0.4, 0.95), 6, 'heavy'),
    ('shadow_hound', '그림자 사냥개', 'hellhound', (0.35, 0.3, 0.5), 6, 'pack'),
    ('phantom', '망령', 'ghost', (0.5, 0.6, 1.0), 6, 'drain'),
    ('abyss_crab', '심연 게', 'coral_crab', (0.5, 0.35, 0.8), 6, 'tank'),
    ('elder_lich', '고대 리치', 'lich', (1.0, 0.85, 0.45), 7, 'caster'),
    ('chaos_yeti', '혼돈의 설인', 'yeti', (0.6, 0.35, 0.8), 7, 'heavy'),
    ('inferno_phoenix', '업화의 불사조', 'phoenix', (0.75, 0.35, 1.0), 7, 'revives'),
    # postgame rematch bosses (gold-tinted, stronger phases)
    ('forest_guardian_ex', '고목 수호자 · 진', 'forest_guardian', (1.0, 0.85, 0.5), 7, 'superboss'),
    ('frost_kraken_ex', '빙해의 크라켄 여왕 · 진', 'frost_kraken', (1.0, 0.85, 0.5), 7, 'superboss'),
    ('flame_sphinx_ex', '불꽃 스핑크스 · 진', 'flame_sphinx', (1.0, 0.85, 0.5), 7, 'superboss'),
    ('boss_ex', '심연의 망령술사 · 진', 'boss', (1.0, 0.85, 0.5), 7, 'superboss'),
    ('leviathan_ex', '레비아탄 · 진', 'leviathan', (1.0, 0.85, 0.5), 7, 'superboss'),
    ('abyss_lord_ex', '심연의 군주 · 진', 'abyss_lord', (1.0, 0.85, 0.5), 7, 'final superboss'),
]

NEW_MODELS = [
    # id, Korean name, chapter, archetype, rank (0 normal, 1 elite FOE, 2 boss), look
    ('puffer', '복어 풍선', 5, 'flyer', 0, 'round spiky pufferfish floating in the air, big eyes, small fins'),
    ('merfolk_guard', '어인 수비병', 5, 'body_only', 0, 'fish-headed humanoid soldier with a coral spear and shell shield'),
    ('angler', '초롱아귀', 5, 'flyer', 0, 'floating deep-sea anglerfish with a glowing lure on a stalk'),
    ('giant_clam', '거대 조개', 5, 'body_only', 0, 'huge clam with a pearl and a tongue, snapping shell'),
    ('sea_urchin', '성게', 5, 'blob', 0, 'spiky round urchin on tiny feet'),
    ('temple_guardian', '신전 수호상', 5, 'body_only', 0, 'barnacled stone statue warrior, moss and shells, halberd'),
    ('sea_serpent', '바다뱀', 5, 'body_only', 0, 'coiled sea serpent rising from the floor, fin crest'),
    ('drowned_knight', '익사한 기사', 5, 'body_only', 1, 'elite: rusted armoured knight dripping seaweed, anchor weapon'),
    ('naga_priestess', '나가 사제', 5, 'body_only', 1, 'elite: snake-tailed priestess with a trident staff and pearl crown'),
    ('turtle_titan', '거북 타이탄', 5, 'body_only', 1, 'elite: giant turtle with a temple on its shell'),
    ('siren', '세이렌', 5, 'flyer', 0, 'feathered bird-woman singer with a shell harp'),
    ('leviathan', '레비아탄', 5, 'body_only', 2, 'chapter 5 boss: colossal sea dragon, bioluminescent stripes, fin crown'),
    ('void_eye', '공허의 눈', 6, 'flyer', 0, 'floating eyeball with tentacles and a ring of small eyes'),
    ('shadow_beast', '그림자 짐승', 6, 'body_only', 0, 'big wolf-like beast of smoke with a glowing maw'),
    ('chaos_spawn', '혼돈의 촉수', 6, 'blob', 0, 'tentacle mass with a gaping maw'),
    ('gargoyle', '가고일', 6, 'flyer', 0, 'stone gargoyle with bat wings and horns'),
    ('nightmare', '나이트메어', 6, 'body_only', 0, 'black horse with a flaming violet mane'),
    ('doppelganger', '도플갱어', 6, 'body_only', 0, 'faceless mirror humanoid, cracked glass skin'),
    ('abyss_worm', '심연 벌레', 6, 'body_only', 0, 'huge segmented worm rising from the floor, ring of teeth'),
    ('fallen_angel', '타락 천사', 6, 'flyer', 1, 'elite: angel with torn black wings and a broken halo, greatsword'),
    ('void_reaper', '공허의 사신', 6, 'flyer', 1, 'elite: hooded reaper with a void scythe'),
    ('crystal_horror', '수정 괴수', 6, 'body_only', 1, 'elite: beast grown from violet abyss crystals'),
    ('abyss_lord', '심연의 군주', 6, 'body_only', 2, 'final boss: towering armoured demon king, crown of horns, '
                                                        'cape of void, two-handed blade'),
]

# ------------------------------------------------------------------ equipment
# Tier T1..T8 tracks chapters 1-7 (T8 = postgame / legendary). Existing pieces keep their ids and land in the
# tier listed; new ids are the ones not already in equipment.json. Every line is a base-class weapon/armour.
GEAR_LINES = {
    'sword': ['sword_bronze', 'sword_iron', 'sword_knight', 'sword_flamberge', 'sword_runic', 'sword_tidal', 'sword_void', 'sword_dawn'],
    'staff': ['staff_oak', 'staff_crystal', 'staff_sage', 'staff_ruby', 'staff_bone', 'staff_coral', 'staff_void', 'staff_starlight'],
    'bow': ['bow_short', 'bow_hunter', 'bow_composite', 'bow_gale', 'bow_wraith', 'bow_tide', 'bow_void', 'bow_star'],
    'mace': ['mace_wood', 'mace_silver', 'mace_blessed', 'mace_saint', 'mace_requiem', 'mace_pearl', 'mace_judgment', 'mace_dawn'],
    'armor': ['armor_chain', 'armor_scale', 'armor_plate', 'armor_dragon', 'armor_rune', 'armor_tidal', 'armor_void', 'armor_dawn'],
    'robe': ['robe_cloth', 'robe_silk', 'robe_mystic', 'robe_sage', 'robe_spirit', 'robe_pearl', 'robe_void', 'robe_dawn'],
    'garb': ['garb_leather', 'garb_ranger', 'garb_shadow', 'garb_wind', 'garb_wraith', 'garb_tide', 'garb_void', 'garb_dawn'],
}
# Job signature weapons: equipment field "jobs" lists who may equip (empty list = any job of the class).
JOB_WEAPONS = {
    'knight': 'sword_aegis', 'berserker': 'sword_ravager', 'paladin': 'sword_holy_avenger', 'warlord': 'sword_conqueror',
    'elementalist': 'staff_prism', 'warlock': 'staff_hex', 'archmage': 'staff_arcanum', 'abyssal': 'staff_abyss_eye',
    'sniper': 'bow_longshot', 'ranger': 'bow_thornvine', 'divine_archer': 'bow_heavens', 'shadow_stalker': 'bow_nightfall',
    'priest': 'mace_grace', 'exorcist': 'mace_purifier', 'saint': 'mace_seraph', 'inquisitor': 'mace_verdict',
}
NEW_ACCESSORIES = [
    'acc_iron_bangle', 'acc_mind_ring', 'acc_swift_anklet', 'acc_life_pendant', 'acc_spirit_pendant', 'acc_thunder_amulet',
    'acc_holy_amulet', 'acc_dark_amulet', 'acc_earth_amulet', 'acc_silence_ward', 'acc_sleep_ward', 'acc_paralyze_ward',
    'acc_curse_ward', 'acc_burn_ward', 'acc_freeze_ward', 'acc_berserk_ring', 'acc_sniper_scope', 'acc_mana_spring',
    'acc_regen_ring', 'acc_counter_charm', 'acc_tp_crest', 'acc_gold_charm', 'acc_exp_charm', 'acc_ribbon',
    'acc_crystal_crown', 'acc_dragon_fang', 'acc_kraken_eye', 'acc_sphinx_riddle', 'acc_lich_phylactery', 'acc_abyss_heart',
]

# ------------------------------------------------------------------ items
NEW_ITEMS = {
    # consumables
    'x_potion': 'heal', 'max_ether': 'mp', 'megalixir': 'heal_all', 'panacea': 'cure', 'phoenix_plume': 'revive',
    'fire_bomb': 'bomb', 'ice_bomb': 'bomb', 'thunder_bomb': 'bomb', 'holy_water': 'bomb', 'magic_tonic': 'buff',
    'speed_tonic': 'buff', 'camp_tent': 'heal_all',
    # permanent stat seeds
    'seed_power': 'seed', 'seed_magic': 'seed', 'seed_guard': 'seed', 'seed_mind': 'seed', 'seed_swift': 'seed', 'seed_life': 'seed',
    # progression
    'job_medal': 'key', 'master_seal': 'key', 'enhance_stone': 'material', 'enhance_stone_hi': 'material', 'enhance_stone_abyss': 'material',
    # chapter 5-7 materials
    'pearl': 'material', 'scale_blue': 'material', 'temple_stone': 'material', 'siren_feather': 'material', 'leviathan_fin': 'material',
    'void_shard': 'material', 'shadow_pelt': 'material', 'gargoyle_horn': 'material', 'fallen_feather': 'material', 'lord_crown': 'material',
    'trial_emblem': 'material', 'metal_gel': 'material',
}
