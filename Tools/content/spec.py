"""Content plan for the 20-hour campaign: the single source of truth for new IDs.

Every worker that adds data, code or art for the expansion uses the IDs below, so monsters, drops, gear,
floors and models line up without waiting on each other. Stats, skills, drop chances, map layouts and
descriptions are left to the data generators; only names, chapters, roles and models are fixed here.
See docs/CONTENT_20H_PLAN.md for the design rationale.
"""

# ------------------------------------------------------------------ zones (hunter theme: 12 zones x 3 floors + postgame)
# The campaign is 12 zones of 3 floors (36 main floors) plus the 3-floor postgame "붉은 게이트". Floor 3 of a zone
# holds the zone boss; floor 2 holds the mid-boss FOE. Odd zones are modern places a gate broke into; even zones
# are graded gates (E..S). "levels" is the party level range the zone is tuned for (enter -> leave); the boss sits
# about one level above the exit. "style" picks the map layout family in world/maps.py; "overlay" is the floor
# mood overlay (Atmosphere.ForFloor) for gates that reuse an older tileset. Floor ids are '<zone id>_<k>',
# floor labels '<n>-<k>' ('R-<k>' in the postgame). The key 'chapter' in older code means this zone number.
FLOORS_PER_ZONE = 3
CHAPTERS = [
    dict(n=1, id='subway', name='지하철 역', grade='', tileset='subway', overlay='', style='tunnels', size=17,
         levels=(1, 6), boss='subway_bat_lord', midboss='elite_bat'),
    dict(n=2, id='gate_e', name='E급 게이트 · 초록 숲', grade='E', tileset='verdant_ruins', overlay='', style='maze',
         size=19, levels=(6, 11), boss='forest_guardian', midboss='elite_rhino_beetle'),
    dict(n=3, id='factory', name='폐공장', grade='', tileset='factory', overlay='', style='aisles', size=21,
         levels=(11, 17), boss='scrap_colossus', midboss='elite_sand_golem'),
    dict(n=4, id='gate_d', name='D급 게이트 · 얼음 동굴', grade='D', tileset='frost_grotto', overlay='', style='maze',
         size=21, levels=(17, 22), boss='frost_kraken', midboss='elite_yeti'),
    dict(n=5, id='cave', name='지하동굴', grade='', tileset='cave', overlay='', style='cave', size=23,
         levels=(22, 28), boss='crystal_cave_lord', midboss='elite_hellhound'),
    dict(n=6, id='gate_c', name='C급 게이트 · 화염 사막', grade='C', tileset='ember_caverns', overlay='', style='maze',
         size=23, levels=(28, 33), boss='flame_sphinx', midboss='elite_fire_drake'),
    dict(n=7, id='school', name='학교', grade='', tileset='school', overlay='', style='halls', size=23,
         levels=(33, 39), boss='festival_pumpkin_king', midboss='elite_mimic'),
    dict(n=8, id='gate_b', name='B급 게이트 · 망자의 묘소', grade='B', tileset='haunted_crypt', overlay='',
         style='maze', size=25, levels=(39, 44), boss='boss', midboss='elite_dark_knight'),
    dict(n=9, id='hospital', name='병원', grade='', tileset='hospital', overlay='', style='halls', size=25,
         levels=(44, 50), boss='plague_lich', midboss='elite_skeleton'),
    dict(n=10, id='gate_a', name='A급 게이트 · 가라앉은 신전', grade='A', tileset='frost_grotto', overlay='tidewater',
         style='maze', size=25, levels=(50, 55), boss='leviathan', midboss='turtle_titan'),
    dict(n=11, id='guild_street', name='습격당한 길드 거리', grade='', tileset='guild_street', overlay='', style='streets',
         size=27, levels=(55, 60), boss='abyss_herald', midboss='crystal_horror'),
    dict(n=12, id='gate_s', name='S급 게이트 · 심연', grade='S', tileset='haunted_crypt', overlay='voidglow', style='maze',
         size=27, levels=(60, 66), boss='abyss_lord', midboss='void_reaper'),
    dict(n=13, id='red_gate', name='붉은 게이트 (클리어 후)', grade='SS', tileset='ember_caverns', overlay='trialfire',
         style='maze', size=27, levels=(66, 70), boss='abyss_lord_ex', midboss='void_reaper', postgame=True),
]
MAIN_ZONES = 12
LEVEL_CAP = 70

# New tilesets (Blender/environment kits, same 28-piece contract as verdant_ruins: wall_a-c, floor_a-c, door,
# door_locked, stairs_up/down, chest, trap, spring, warp, lore_stone, torch, foe_marker, boss_gate, arena,
# decor_1-6, overlay_1-2). Look notes for the kit builders.
NEW_TILESETS = {
    'subway': 'Seoul metro station after a gate break: tiled platform floors with yellow safety line, rails and '
              'sleepers in tunnel corridors, tiled walls with line-colour stripe, fluorescent ceiling strips, '
              'turnstiles, benches, vending machine, route map signs, cracked concrete with violet gate glow.',
    'factory': 'abandoned factory: stained concrete floor with hazard stripes, corrugated metal walls, steel '
               'beams, conveyor belts, crates, oil drums, pipes and valves, hanging chains, rusty orange light.',
    'cave': 'natural limestone cave under the city: uneven rock floor, stalagmites, glowing blue/violet crystal '
            'clusters, underground stream, mushrooms, old mining props (lantern, cart rail).',
    'school': 'Korean high school at night (festival): linoleum corridor floor, lockers, classroom doors with '
              'windows, notice boards, festival paper garlands and lanterns, desks, chalkboard, window frames.',
    'hospital': 'abandoned hospital (kept cute, not horror): pale green tiles, white walls with handrails, ward '
                'curtains, beds, IV stands, medicine carts, red-cross signs, flickering but warm lights.',
    'guild_street': 'downtown street around the hunter guild overrun by monsters: asphalt road with lane marks, '
                    'sidewalk tiles, shop fronts with Korean signboards, guild banners, barricades, cracked '
                    'pavement with gate rifts, street lamps, overturned cars kept simple.',
}

# Zone palette variants (same mechanism as VARIANTS below: data field "model" = base enemy id, "tint" = RGBA
# multiplier). Zone bosses for the modern zones and themed normal monsters. Columns: id, Korean name, base model,
# tint (r, g, b), zone, rank (0 normal, 1 elite, 2 boss), role. When a new Blender model in HUNTER_MONSTERS is
# accepted, its id becomes the "model" of the rows that name it in 'replace_model'.
ZONE_VARIANTS = [
    ('subway_bat_lord', '지하철 박쥐 군주', 'elite_bat', (0.8, 0.75, 1.0), 1, 2, 'zone 1 boss: summons bats'),
    ('sewer_slime', '하수구 슬라임', 'slime', (0.62, 0.78, 0.5), 1, 0, 'poison spit'),
    ('tunnel_bat', '터널 박쥐', 'bat', (0.75, 0.75, 0.85), 1, 0, 'fast, blind'),
    ('scrap_colossus', '고철 거상', 'elite_sand_golem', (0.78, 0.62, 0.52), 3, 2, 'zone 3 boss: tank, thunder weak'),
    ('scrap_golem', '고철 골렘', 'sand_golem', (0.72, 0.66, 0.6), 3, 0, 'tank'),
    ('oil_slime', '기름 슬라임', 'magma_slime', (0.42, 0.36, 0.5), 3, 0, 'fire weak, blind spit'),
    ('spark_wisp', '전기 도깨비불', 'wisp', (1.0, 0.95, 0.45), 3, 0, 'thunder caster'),
    ('iron_beetle', '강철 풍뎅이', 'rhino_beetle', (0.72, 0.78, 0.86), 3, 0, 'defence'),
    ('crystal_cave_lord', '수정 동굴의 주인', 'crystal_horror', (0.6, 0.85, 1.0), 5, 2, 'zone 5 boss: reflects magic'),
    ('crystal_slime', '수정 슬라임', 'slime', (0.7, 0.6, 1.0), 5, 0, 'magic resist'),
    ('cave_spider', '동굴 거미', 'frost_spider', (0.8, 0.62, 0.45), 5, 0, 'poison web'),
    ('festival_pumpkin_king', '축제의 호박왕', 'elite_scarecrow', (1.0, 0.85, 0.6), 7, 2, 'zone 7 boss: summons scarecrows'),
    ('locker_mimic', '사물함 미믹', 'mimic', (0.6, 0.72, 0.9), 7, 0, 'surprise bite'),
    ('school_ghost', '방과 후 유령', 'ghost', (0.85, 0.9, 1.0), 7, 0, 'sleep'),
    ('plague_lich', '역병의 리치', 'lich', (0.7, 1.0, 0.65), 9, 2, 'zone 9 boss: poison, summons skeletons'),
    ('pill_slime', '알약 슬라임', 'slime', (1.0, 0.7, 0.8), 9, 0, 'heals allies'),
    ('syringe_bee', '주사벌', 'killer_bee', (0.75, 0.95, 1.0), 9, 0, 'sleep sting'),
    ('bandage_ghost', '붕대 유령', 'ghost', (1.0, 0.95, 0.85), 9, 0, 'curse'),
    ('abyss_herald', '심연의 사도', 'fallen_angel', (0.8, 0.6, 1.0), 11, 2, 'zone 11 boss: dark, summons'),
    ('street_hound', '거리의 사냥개', 'hellhound', (0.6, 0.6, 0.7), 11, 0, 'pack'),
]

# Monster pools per zone (existing ids + ZONE_VARIANTS). The world builder re-levels every monster into its zone's
# level range (normal = rank 0 random encounters, elite = FOE / mid-boss). A monster appears in one zone only,
# except the postgame (13), which mixes the strongest of every gate.
ZONE_POOLS = {
    1: dict(normal=['sewer_slime', 'slime', 'sewer_rat', 'horned_rabbit', 'tunnel_bat', 'bat', 'killer_bee'],
            elite=['elite_bat', 'elite_mushroom']),
    2: dict(normal=['goblin', 'goblin_shaman', 'sprout', 'mushroom', 'mandragora', 'rhino_beetle', 'pixie', 'poison_mushroom'],
            elite=['elite_rhino_beetle', 'elite_mushroom']),
    3: dict(normal=['scrap_golem', 'oil_slime', 'spark_wisp', 'iron_beetle', 'magma_slime', 'sand_scorpion'],
            elite=['elite_sand_golem']),
    4: dict(normal=['jellyfish', 'frost_spider', 'coral_crab', 'snow_fairy', 'penguin_mage', 'ice_wolf', 'yeti',
                    'ice_golem', 'ice_slime', 'snow_rabbit', 'frost_bee'],
            elite=['elite_ice_wolf', 'elite_yeti', 'elite_coral_crab']),
    5: dict(normal=['crystal_slime', 'cave_spider', 'cave_mole', 'sand_golem', 'lizardman', 'grave_bat', 'flame_elemental'],
            elite=['elite_hellhound', 'elite_sand_golem']),
    6: dict(normal=['hellhound', 'phoenix', 'harpy', 'fire_drake', 'ember_bee', 'lava_beetle', 'flame_wisp',
                    'crimson_scorpion'],
            elite=['elite_fire_drake', 'elite_hellhound']),
    7: dict(normal=['school_ghost', 'locker_mimic', 'dark_pixie', 'scarecrow', 'wisp', 'ghost_mushroom', 'mimic'],
            elite=['elite_mimic', 'elite_scarecrow']),
    8: dict(normal=['skeleton', 'skeleton_mage', 'ghost', 'dark_knight', 'lich', 'crypt_hound'],
            elite=['elite_skeleton', 'elite_dark_knight']),
    9: dict(normal=['pill_slime', 'syringe_bee', 'bandage_ghost', 'phantom', 'storm_harpy', 'swamp_lizardman'],
            elite=['elite_skeleton', 'drowned_knight']),
    10: dict(normal=['puffer', 'sea_urchin', 'deep_jelly', 'merfolk_guard', 'angler', 'giant_clam', 'siren',
                     'sea_serpent', 'coral_golem', 'temple_guardian', 'tide_drake'],
             elite=['turtle_titan', 'naga_priestess', 'drowned_knight']),
    11: dict(normal=['street_hound', 'orc', 'shadow_beast', 'gargoyle', 'nightmare', 'doppelganger', 'void_eye'],
             elite=['high_orc', 'crystal_horror', 'fallen_angel']),
    12: dict(normal=['void_wisp', 'chaos_spawn', 'shadow_hound', 'abyss_crab', 'void_knight', 'abyss_worm',
                     'elder_lich'],
             elite=['void_reaper', 'fallen_angel']),
    13: dict(normal=['chaos_yeti', 'inferno_phoenix', 'elder_lich', 'void_knight', 'abyss_worm'],
             elite=['void_reaper', 'crystal_horror', 'fallen_angel']),
}
RARE_BY_ZONE = {'gold_slime': [2, 3], 'metal_slime': [4, 5, 6], 'golden_mimic': [9, 10, 11]}
# Equipment tier (GEAR_LINES index + 1) found per zone. The guild market sells tier t from zone TIER_UNLOCK_ZONE[t]
# (C#: TownServices.ChapterOfFloor, one market tier per two zones; gear_items.py TIER_SHOP); T8 is never sold.
TIER_OF_ZONE = {1: 1, 2: 1, 3: 2, 4: 2, 5: 3, 6: 3, 7: 4, 8: 4, 9: 5, 10: 5, 11: 6, 12: 7, 13: 8}
TIER_UNLOCK_ZONE = {1: 1, 2: 1, 3: 3, 4: 5, 5: 7, 6: 9, 7: 11}

# New cute hunter-genre monsters built in Blender (enemies_h/). Look notes keep the user's direction: cute and
# charming (big eyes, round shapes, chibi), never gross or creepy. 'replace_model' lists ZONE_VARIANTS / existing ids
# whose "model" switches to this new model once the preview is approved.
HUNTER_MONSTERS = [
    ('goblin', '고블린', 2, 'body_only', 0, 'small green goblin, big pointy ears, oversized leather cap, wooden club, '
     'toothy grin but cute', []),
    ('goblin_shaman', '고블린 주술사', 2, 'body_only', 0, 'goblin with a feather headdress, bone staff with a glowing '
     'orb, poncho', []),
    ('sewer_rat', '땅굴쥐', 1, 'body_only', 0, 'chubby grey rat standing on hind legs, big round ears, buck teeth, '
     'pink tail, tiny miner helmet lamp', []),
    ('scrap_bot', '고철 로봇', 3, 'body_only', 0, 'round rusty robot made of scrap, one big lamp eye, antenna, '
     'wrench hand', ['scrap_golem']),
    ('cave_mole', '굴착 두더지', 5, 'body_only', 0, 'plump mole with huge digging claws, pink nose, goggles', []),
    ('mummy_pup', '붕대 미라', 9, 'body_only', 0, 'small round mummy wrapped in bandages, one big eye peeking out, '
     'stubby arms, cute not scary', ['bandage_ghost']),
    ('orc', '오크 전사', 11, 'body_only', 0, 'chibi green orc with tusks, horned helmet, big axe, belly', []),
    ('high_orc', '하이 오크', 11, 'body_only', 1, 'elite: armoured orc chief with a red cape, scarred, two-handed '
     'cleaver, still chibi', []),
]
# Battle data template of each hunter monster with its own row (stats shape, row, size): the variant builder copies
# the base row, re-levels it into the monster's zone and sets 'model' to the hunter monster's own id. Monsters with a
# non-empty replace list have no row of their own: they only become the model of those rows.
HUNTER_MONSTER_BASE = {'goblin': 'horned_rabbit', 'goblin_shaman': 'pixie', 'sewer_rat': 'horned_rabbit',
                       'cave_mole': 'lizardman', 'orc': 'dark_knight', 'high_orc': 'elite_dark_knight'}
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
    'warrior': '전사', 'knight': '가디언', 'paladin': '철벽의 수호자', 'berserker': '광전사', 'warlord': '투신',
    'mage': '마법사', 'elementalist': '원소술사', 'archmage': '대마법사', 'warlock': '저주술사', 'abyssal': '심연술사',
    'archer': '궁수', 'sniper': '저격수', 'divine_archer': '신궁', 'ranger': '암살자', 'shadow_stalker': '그림자 암살자',
    'cleric': '힐러', 'priest': '치유사', 'saint': '성녀', 'exorcist': '퇴마사', 'inquisitor': '심판관',
}
# First awakening (advanced job): Lv 12 and the zone 2 boss (forest_guardian) beaten, pay a job_medal (also sold
# at the guild market from zone 3). Second awakening (master job): Lv 36 and the zone 7 boss
# (festival_pumpkin_king) beaten, pay a master_seal (sold from zone 8). Recruits that join already awakened
# (HUNTERS start_job) skip the cost.
JOB_ADVANCED_LEVEL, JOB_ADVANCED_BOSS = 12, 'forest_guardian'
JOB_MASTER_LEVEL, JOB_MASTER_BOSS = 36, 'festival_pumpkin_king'

# ------------------------------------------------------------------ hunters (playable roster)
# 20 hunters, 5 per class. A hunter is a hero row in heroes.json: id = hunter id, "class" = base class (warrior,
# mage, archer, cleric; the job tree and equipment rules follow the class). The active party is 4 hunters chosen
# at the guild; benched hunters get 50 % of battle EXP. join: 'start' (in the party from the prologue),
# ('boss', zone) joins when that zone's boss falls, ('scout', zone, price) can be hired at the guild reception
# from that zone on. start_job: job the hunter already holds when joining (None = the class). stat: multipliers
# on the class's base stats and growth. sig: (signature skill base id to clone, Korean name) learned at Lv 1.
# gender picks the VRoid base (M = HairSample_Male, F = HairSample_Female). look: outfit notes for Blender
# (Blender/lib_anime/hunters_anime.py); rank: licence grade shown on the profile.
HUNTERS = [
    # ---- starting party (newly awakened E-rank hunters)
    dict(id='h_dohyun', name='강도현', cls='warrior', gender='M', rank='E', join='start', start_job=None,
         stat=dict(max_hp=1.05, attack=1.05), sig=('sk_w_twin_slash', '각성 이연참'), hair=['#16161c', '#2c2c38', '#4a4a5c'],
         eyes='#c0392b', look='protagonist: black hoodie under an olive tactical vest, dark cargo pants, sneakers, '
         'fingerless gloves, red scarf', line='나는 아직 E급이야. 그래도 여기서 도망치진 않아.'),
    dict(id='h_seoa', name='한서아', cls='mage', gender='F', rank='E', join='start', start_job=None,
         stat=dict(magic=1.05, max_mp=1.1), sig=('sk_m_spark', '정전기 폭발'), hair=['#3a2a20', '#7a5238', '#c8946a'],
         eyes='#4a8ad4', look='university student: beige trench coat over a white knit, pleated skirt, black tights, '
         'ankle boots, round glasses, small spellbook on a belt chain', line='수업 빠지면 F인데… 게이트가 먼저야.'),
    dict(id='h_jiho', name='윤지호', cls='archer', gender='M', rank='E', join='start', start_job=None,
         stat=dict(speed=1.08, attack=1.03), sig=('double_shot', '국대 더블 샷'), hair=['#2a1a10', '#5a3a22', '#8a6040'],
         eyes='#3a8a4a', look='ex national archery athlete: navy track jacket with white stripes, snapback cap, '
         'arm guard, quiver as a sports bag strap, joggers', line='과녁보다 크네. 안 빗나가.'),
    dict(id='h_yuna', name='백유나', cls='cleric', gender='F', rank='E', join='start', start_job=None,
         stat=dict(resistance=1.08, max_mp=1.05), sig=('heal', '응급 처치'), hair=['#5a2a3a', '#b0607a', '#f0a8bc'],
         eyes='#c86346', look='nursing student: white cardigan over a light blue scrub top, red-cross armband, '
         'white sneakers, hair in a low ponytail, first-aid pouch', line='다친 사람 있으면 저부터 불러 주세요!'),
    # ---- story joins: one when each zone boss falls
    dict(id='h_minjun', name='최민준', cls='warrior', gender='M', rank='D', join=('boss', 1), start_job=None,
         stat=dict(max_hp=1.15, defense=1.12, speed=0.92), sig=('sk_provoke', '구조대의 함성'),
         hair=['#1a1008', '#3a2414', '#6a4428'], eyes='#8a5a20',
         look='ex firefighter tank: orange-and-navy turnout coat with reflective stripes, helmet with visor up, '
         'heavy gloves, big round shield made from a manhole cover', line='시민 대피 끝! 이제 내가 막는다.'),
    dict(id='h_sora', name='이소라', cls='archer', gender='F', rank='D', join=('boss', 2), start_job='ranger',
         stat=dict(speed=1.12, attack=1.05, max_hp=0.92), sig=('sk_a_shadow_stitch', '그림자 바느질'),
         hair=['#101018', '#22223a', '#3a3a5a'], eyes='#8a3ad4',
         look='assassin: short black bomber jacket, face mask, hood, fitted dark pants, thigh straps with knives, '
         'violet accents', line='…말 걸지 마. 표적이 도망가.'),
    dict(id='h_taeyang', name='오태양', cls='mage', gender='M', rank='C', join=('boss', 3), start_job='elementalist',
         stat=dict(magic=1.08, defense=1.05), sig=('sk_flame_wave', '용광로 파도'),
         hair=['#5a1a08', '#b0401a', '#ff8a3a'], eyes='#ff8a2a',
         look='factory engineer fire mage: orange work coveralls with sleeves tied at the waist, black tank top, '
         'welding goggles on forehead, tool belt, burn-proof gloves', line='공장 불 끄던 놈이 불을 쓰게 될 줄이야.'),
    dict(id='h_eunbi', name='정은비', cls='cleric', gender='F', rank='C', join=('boss', 4), start_job='exorcist',
         stat=dict(magic=1.06, resistance=1.08), sig=('sk_c_banish', '부적 퇴마'),
         hair=['#0a0a14', '#1a1a2a', '#2e2e46'], eyes='#c83a3a',
         look='Korean shaman exorcist: white jeogori-style short jacket with red goreum ribbon, dark hanbok-like '
         'long skirt, talismans on a cord, bell bracelet, long straight black hair', line='귀신보다 무서운 건 야근이에요.'),
    dict(id='h_gunwoo', name='서건우', cls='warrior', gender='M', rank='C', join=('boss', 5), start_job='berserker',
         stat=dict(attack=1.12, max_hp=1.05, defense=0.92), sig=('sk_w_berserk', '링 위의 광기'),
         hair=['#0a0a0a', '#202020', '#3a3a3a'], eyes='#d43a2a',
         look='MMA fighter berserker: sleeveless black compression top, red boxing shorts over leggings, hand wraps '
         'and bandaged forearms, buzz cut, chain necklace', line='맞으면서 배우는 거지. 덤벼!'),
    dict(id='h_hana', name='김하나', cls='mage', gender='F', rank='B', join=('boss', 6), start_job='elementalist',
         stat=dict(magic=1.1, speed=1.05, max_hp=0.92), sig=('sk_frost_nova', '아이돌 프로스트'),
         hair=['#6a7aa8', '#a8c0f0', '#e8f2ff'], eyes='#5ab0f0',
         look='idol hunter ice mage: white-and-ice-blue stage jacket with silver trim, short pleated skirt, '
         'star hairpin, knee boots, headset mic', line='팬 여러분, 오늘도 얼려 드릴게요!'),
    dict(id='h_siwoo', name='류시우', cls='archer', gender='M', rank='B', join=('boss', 7), start_job='sniper',
         stat=dict(attack=1.1, speed=1.02, max_hp=0.95), sig=('sk_a_deadeye', '방과 후 데드아이'),
         hair=['#1a1410', '#3a2e24', '#5a4a3a'], eyes='#3a6ad4',
         look='genius high-school sniper: navy school blazer with emblem, loosened tie, white shirt, grey slacks, '
         'headphones around the neck, long rifle-like bow', line='교실에서 보는 것보다 과녁이 크네요.'),
    dict(id='h_mirae', name='송미래', cls='cleric', gender='F', rank='B', join=('boss', 8), start_job='inquisitor',
         stat=dict(attack=1.08, magic=1.05), sig=('sk_c_judgment_cross', '정오의 심판'),
         hair=['#c8a050', '#f0d080', '#fff4c8'], eyes='#d4a020',
         look='inquisitor: long white military-style coat with gold buttons and a cross emblem, black gloves, '
         'peaked cap, knee boots, golden blonde braid', line='죄는 미워하되, 몬스터는 더 미워하세요.'),
    dict(id='h_jaehyun', name='남재현', cls='cleric', gender='M', rank='A', join=('boss', 9), start_job='priest',
         stat=dict(magic=1.1, max_mp=1.15, attack=0.9), sig=('sk_greater_heal', '긴급 수술'),
         hair=['#1a1a20', '#36364a', '#5a5a74'], eyes='#3a8aa0',
         look='doctor healer: white doctor coat over teal scrubs, stethoscope, ID badge, rimless glasses, neat '
         'short hair', line='환자는 제가 맡죠. 여러분은 싸우기만 하세요.'),
    dict(id='h_dana', name='문다나', cls='warrior', gender='F', rank='A', join=('boss', 10), start_job='knight',
         stat=dict(defense=1.12, max_hp=1.08, magic=0.9), sig=('sk_w_aegis', '해병의 방벽'),
         hair=['#2a1a10', '#5a3a20', '#8a5a34'], eyes='#5a7a3a',
         look='ex-marine guardian: digital camo jacket with rolled sleeves, tactical plate carrier, knee pads, '
         'combat boots, short ponytail, red beret', line='한 걸음도 물러서지 않는다. 그게 해병이다.'),
    dict(id='h_iseul', name='차이슬', cls='archer', gender='F', rank='A', join=('boss', 11), start_job='sniper',
         stat=dict(speed=1.1, attack=1.06), sig=('sk_piercing_gale', '정찰대 관통 질풍'),
         hair=['#2a3a2a', '#4a6a4a', '#7a9a6a'], eyes='#6ab06a',
         look='guild scout captain: green field poncho over a utility vest, cargo pants, binoculars, '
         'bandana, fingerless gloves', line='길드 거리는 내 앞마당이야. 따라와.'),
    dict(id='h_haneul', name='강하늘', cls='mage', gender='M', rank='S', join=('boss', 12), start_job='warlock',
         stat=dict(magic=1.14, max_mp=1.1, defense=0.9), sig=('sk_m_abyss_gate', '하늘 균열'),
         hair=['#e8e8f0', '#c0c0d4', '#9090a8'], eyes='#a04ae0',
         look='S-rank dark mage: long black coat with violet lining and high collar, black gloves, silver hair, '
         'floating violet runes, dress shoes', line='S급이라고 다 친절한 건 아냐. 난 예외지만.'),
    # ---- guild scouts (hire at the reception desk)
    dict(id='h_bora', name='표보라', cls='warrior', gender='F', rank='C', join=('scout', 3, 3000), start_job='berserker',
         stat=dict(attack=1.1, speed=1.05), sig=('sk_w_whirlwind', '경호원 회전베기'),
         hair=['#4a0a1a', '#8a1a3a', '#c83a5a'], eyes='#c8325a',
         look='bodyguard warrior: black suit with the jacket open, red tie, sunglasses on the head, earpiece, '
         'leather gloves, bob-cut wine-red hair', line='의뢰비만 확실하면, 끝까지 지켜 드리죠.'),
    dict(id='h_youngsu', name='장영수', cls='cleric', gender='M', rank='C', join=('scout', 6, 8000), start_job='exorcist',
         stat=dict(max_hp=1.1, defense=1.08, speed=0.95), sig=('sk_c_exorcism', '목탁 퇴마'),
         hair=['#1a1a1a', '#2a2a2a', '#3a3a3a'], eyes='#6a5a3a',
         look='temple monk exorcist: grey monk robe with a brown kasa sash, prayer beads, straw sandals over socks, '
         'shaved head, wooden moktak hanging from the belt', line='나무아미타불… 그리고 한 대 더.'),
    dict(id='h_rina', name='유리나', cls='mage', gender='F', rank='B', join=('scout', 8, 15000), start_job='elementalist',
         stat=dict(magic=1.08, speed=1.08), sig=('sk_m_prism', '마법소녀 프리즘'),
         hair=['#c84a8a', '#f08ac0', '#ffd0ea'], eyes='#f05aa0',
         look='magical-girl mage: pink-and-white frilled jacket with ribbon, star wand, twin tails with ribbons, '
         'striped stockings, small cape', line='사랑과 마력으로, 게이트를 닫겠어요!'),
    dict(id='h_jun', name='진준', cls='archer', gender='M', rank='A', join=('scout', 10, 30000), start_job='ranger',
         stat=dict(speed=1.12, attack=1.05, defense=0.92), sig=('sk_a_phantom_raid', '라이더 환영 난무'),
         hair=['#3a3a40', '#6a6a74', '#a0a0ac'], eyes='#f0c03a',
         look='courier rider assassin: black hooded windbreaker with neon yellow stripes, motorcycle gloves, '
         'helmet clipped to the belt, crossbow on the back, delivery bag', line='배송 완료. 표적도 완료.'),
]
STARTING_PARTY = ['h_dohyun', 'h_seoa', 'h_jiho', 'h_yuna']
# Old saves: the four original heroes become the starting hunters (level, EXP, job, gear, skills, seeds kept).
LEGACY_HERO_MAP = {'warrior': 'h_dohyun', 'mage': 'h_seoa', 'archer': 'h_jiho', 'cleric': 'h_yuna'}

# Guild staff (replace the town NPC looks; ids stay so markers and code keep working).
GUILD_NPCS = {
    'innkeeper': ('윤 간호사', '의무실', 'guild medic: light pink scrubs, nurse cap, clipboard'),
    'shopkeeper': ('박 사장', '헌터 마켓', 'market owner: apron over a hawaiian shirt, cap backwards, calculator'),
    'smith': ('곽 장인', '장비 공방', 'workshop master: dark work apron, welding mask pushed up, big wrench, beard'),
    'guild_clerk': ('서 주임', '접수처', 'receptionist: navy guild uniform blazer, scarf tie, ID lanyard, tablet'),
    'elder': ('백 길드장', '길드장실', 'guild master: grey-haired man in a black three-piece suit with a cane'),
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
