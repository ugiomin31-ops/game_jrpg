"""v2 monster roster (enemies_c): generator module, Korean name, biome and design role per enemy id.
Pure data (no bpy) so production scripts and review-sheet tools can share it.
"""

ROSTER = {
    # id: (module, 한국어 이름, biome, floors, role)
    'horned_rabbit': ('verdant', '뿔토끼', 'verdant_ruins', 'B1-B2', 'fast swarm'),
    'killer_bee': ('verdant', '킬러비', 'verdant_ruins', 'B2-B3', 'swarm / poison'),
    'mandragora': ('verdant', '만드라고라', 'verdant_ruins', 'B2-B3', 'debuffer (sleep, slow)'),
    'rhino_beetle': ('verdant', '장수풍뎅이', 'verdant_ruins', 'B2-B3', 'tank'),
    'elite_rhino_beetle': ('verdant', '강철 투구왕', 'verdant_ruins', 'B3 FOE', 'elite tank'),
    'pixie': ('verdant', '숲의 요정', 'verdant_ruins', 'B3', 'healer'),
    'frost_spider': ('frost', '서리 거미', 'frost_grotto', 'B4-B5', 'debuffer (slow)'),
    'snow_fairy': ('frost', '눈꽃 요정', 'frost_grotto', 'B4-B6', 'healer / ice caster'),
    'yeti': ('frost', '꼬마 설인', 'frost_grotto', 'B5-B6', 'bruiser (stun, enrage)'),
    'elite_yeti': ('frost', '설산의 폭군', 'frost_grotto', 'B6 FOE', 'elite bruiser'),
    'ice_golem': ('frost', '얼음 골렘', 'frost_grotto', 'B6', 'tank'),
    'hellhound': ('ember', '헬하운드', 'ember_caverns', 'B7-B8', 'fast pack hunter'),
    'elite_hellhound': ('ember', '오르트로스', 'ember_caverns', 'B8 FOE', 'elite twin-headed hunter'),
    'flame_elemental': ('ember', '불꽃 정령', 'ember_caverns', 'B7-B9', 'fire caster'),
    'sand_scorpion': ('ember', '모래 전갈', 'ember_caverns', 'B7-B9', 'poison tank'),
    'lizardman': ('ember', '리자드맨', 'ember_caverns', 'B8-B9', 'warrior (bleed)'),
    'harpy': ('ember', '하피', 'ember_caverns', 'B8-B9', 'evasive flyer (AoE, blind)'),
    'ghost': ('crypt', '원령', 'haunted_crypt', 'B10-B12', 'evasive dark caster (sleep)'),
    'mimic': ('crypt', '미믹', 'haunted_crypt', 'B10-B12', 'rare treasure ambusher'),
    'elite_mimic': ('crypt', '판도라 상자', 'haunted_crypt', 'B12 FOE', 'elite ambusher'),
    'dark_knight': ('crypt', '암흑 기사', 'haunted_crypt', 'B11-B12', 'heavy attacker'),
    'elite_dark_knight': ('crypt', '칠흑의 기사단장', 'haunted_crypt', 'B11 FOE', 'elite heavy attacker'),
    'lich': ('crypt', '꼬마 리치', 'haunted_crypt', 'B11-B12', 'summoner / dark caster'),
}

SOURCES = {eid: f'enemies_c/{row[0]}.py' for eid, row in ROSTER.items()}
