# -*- coding: utf-8 -*-
"""Guild quests (헌터 협회 · 새벽 길드 의뢰) for the 13-zone hunter campaign: 51 quests, 3-5 per zone.

unlock_floor is the 0-based floor index the party must have reached (GameState.DeepestFloor); zone n floor k is
(n-1)*3 + (k-1). The 12 original quest ids keep their ids (saves keep their progress) with targets and unlock floors
moved onto the new zones.

Job medals: job_medal (각성의 증표) is the reward of three quests in zones 2-4 (the first awakening is Lv 12 after the
zone 2 gate boss). master_seal (초월의 인장) is the reward of three quests in zones 7-9 (second awakening, Lv 36 after
the zone 7 boss)."""


def Q(id, title, desc, kind, target, count, gold, items, unlock):
    return dict(id=id, title=title, description=desc, kind=kind, target_id=target, count=count,
                reward_gold=gold, reward_items=dict(items), unlock_floor=unlock, _file=id)


QUESTS = [
    # ---- 1구역 지하철 역 (floors 1-3, index 0-2)
    Q('q_slime_cull', '선로 슬라임 정리', '지하철 선로에 슬라임이 늘고 있어요. 8마리만 정리해 주세요.', 'kill', 'slime', 8, 150, {'healing_potion': 3}, 0),
    Q('q_missing_shoe', '잃어버린 신발 한 짝', '분실물 보관함에 아이 신발 한 짝이 남아 있대요. 선로 터널 2층까지 가서 찾아봐 주세요.', 'explore', 'subway_2', 1, 200, {'healing_potion': 2}, 0),
    Q('q_bat_lord', '지하철 박쥐 군주 토벌', '변전실의 박쥐 군주가 전력을 빨아먹고 있어요. 쓰러뜨려 주세요.', 'boss', 'subway_bat_lord', 1, 400, {'enhance_stone': 1, 'ether': 2}, 2),
    # ---- 2구역 E급 게이트 · 초록 숲 (index 3-5)
    Q('q_forest_fiber', '덩굴 섬유 납품', '장비 공방에서 질긴 덩굴 섬유 4개가 필요하대요.', 'collect', 'forest_fiber', 4, 250, {'remedy': 2}, 3),
    Q('q_job_medal_1', '각성 시험 · 숲의 사냥꾼', '길드의 첫 번째 각성 시험이에요. 숲에서 만드라고라 8마리를 잡아 오세요. 통과하면 각성의 증표를 드려요.', 'kill', 'mandragora', 8, 600, {'job_medal': 1}, 3),
    Q('q_toxic_king', '독왕 버섯 토벌', '덩굴 회랑을 떠도는 거대한 독버섯을 쓰러뜨려 주세요.', 'foe', 'elite_mushroom', 1, 600, {'acc_antidote_ring': 1}, 4),
    Q('q_guardian', '고목의 안식', '고목의 성소에서 검은 결정에 사로잡힌 수호자를 쉬게 해 주세요.', 'boss', 'forest_guardian', 1, 1500, {'hi_potion': 3, 'enhance_stone': 2}, 5),
    # ---- 3구역 폐공장 (index 6-8)
    Q('q_job_medal_2', '각성 시험 · 고철 사냥', '두 번째 시험은 실전이에요. 폐공장의 고철 골렘 6마리를 쓰러뜨리세요. 각성의 증표가 걸려 있어요.', 'kill', 'scrap_golem', 6, 900, {'job_medal': 1}, 6),
    Q('q_smuggler_ledger', '밀수 장부를 찾아라', '마석 창고 어딘가에 밀수 장부가 숨겨져 있대요. 창고 2층까지 가서 찾아봐 주세요.', 'explore', 'factory_2', 1, 800, {'enhance_stone': 2}, 6),
    Q('q_golem_breaker', '철광 거인 토벌', '폐공장 라인을 막고 있는 철광 거인을 무너뜨려 주세요.', 'foe', 'elite_sand_golem', 1, 4000, {'ember_crystal': 1}, 7),
    Q('q_scrap_boss', '고철 거상 토벌', '공장 한가운데의 고철 거상을 쓰러뜨려 주세요. 기계 몇 대가 그 몸에 깔려 있어요.', 'boss', 'scrap_colossus', 1, 2500, {'enhance_stone': 3, 'seed_guard': 1}, 8),
    # ---- 4구역 D급 게이트 · 얼음 동굴 (index 9-11)
    Q('q_frost_survey', '빙결 수로 조사', '얼음 창고 2층까지 내려가 길을 확인해 주세요.', 'explore', 'gate_d_2', 1, 800, {'ether': 3}, 9),
    Q('q_wolf_hunt', '서리 늑대 사냥', '서리 늑대 10마리를 사냥해 주세요. 털가죽은 가지셔도 돼요.', 'kill', 'ice_wolf', 10, 1200, {'hi_potion': 3}, 9),
    Q('q_crab_king', '거대 집게 토벌', '통로를 막고 있는 거대 산호 집게를 치워 주세요.', 'foe', 'elite_coral_crab', 1, 1500, {'phoenix_feather': 2}, 9),
    Q('q_job_medal_3', '각성 시험 · 서리의 기억', '세 번째 시험은 인내예요. 서리 털가죽 6장을 모아 오세요. 각성의 증표를 만드는 데 쓰인대요.', 'collect', 'frost_fur', 6, 900, {'job_medal': 1}, 10),
    Q('q_kraken', '여왕의 자장가', '빙해의 여왕이 다시 노래하도록, 그녀를 재우는 자장가를 끊어 주세요.', 'boss', 'frost_kraken', 1, 3000, {'hi_ether': 2, 'enhance_stone': 3}, 11),
    # ---- 5구역 지하동굴 (index 12-14)
    Q('q_crystal_slime', '수정 슬라임 정화', '맥 주변에서 수정 가루를 먹고 자란 슬라임이 늘고 있어요. 10마리를 정리해 주세요.', 'kill', 'crystal_slime', 10, 2000, {'ether': 3}, 12),
    Q('q_vein_letter', '수정 속 편지', '맥 통로 2층의 수정 속에 아이가 쓴 편지가 갇혀 있대요. 찾아서 가져다주세요.', 'explore', 'cave_2', 1, 1500, {'acc_life_pendant': 1}, 12),
    Q('q_hellhound', '오르트로스 퇴치', '맥 통로를 배회하는 쌍두 사냥개 오르트로스를 처치해 주세요.', 'foe', 'elite_hellhound', 1, 3000, {'enhance_stone': 2}, 13),
    Q('q_crystal_lord', '수정 동굴의 주인 토벌', '게이트 맥의 중심을 붙잡고 있는 수정 동굴의 주인을 쓰러뜨려 주세요.', 'boss', 'crystal_cave_lord', 1, 4000, {'enhance_stone_hi': 1, 'seed_magic': 1}, 14),
    # ---- 6구역 C급 게이트 · 화염 사막 (index 15-17)
    Q('q_drake_scales', '드레이크 비늘 납품', '내열 장비 연구에 드레이크 비늘 5장이 필요합니다.', 'collect', 'drake_scale', 5, 2500, {'mega_potion': 2}, 15),
    Q('q_ember_bees', '불티 사냥', '화염벌이 사막 캠프의 장비에 불티를 옮기고 있어요. 10마리를 처치해 주세요.', 'kill', 'ember_bee', 10, 2200, {'fire_bomb': 2, 'ice_bomb': 2}, 15),
    Q('q_drake_king', '홍염 비룡 사냥', '용암 협곡을 나는 홍염 비룡을 떨어뜨려 주세요.', 'foe', 'elite_fire_drake', 1, 5000, {'enhance_stone_hi': 1, 'acc_burn_ward': 1}, 16),
    Q('q_sphinx', '태양의 수수께끼', '불꽃 신전 제단의 스핑크스를 진정시켜 주세요.', 'boss', 'flame_sphinx', 1, 6000, {'hi_ether': 3, 'enhance_stone_hi': 1}, 17),
    # ---- 7구역 학교 (index 18-20)
    Q('q_lament', '교실 도깨비불 정화', '교실 복도를 떠다니는 도깨비불 8개를 잠재워 주세요. 밤마다 음악실 피아노 소리가 난대요.', 'kill', 'wisp', 8, 6000, {'abyss_crystal': 1, 'elixir': 1}, 18),
    Q('q_locker_mimic', '사물함 미믹 소탕', '사물함으로 위장한 미믹이 학생들을 놀라게 하고 있어요. 8마리를 처치해 주세요. 열지 말고 부수세요!', 'kill', 'locker_mimic', 8, 5000, {'acc_sleep_ward': 1}, 18),
    Q('q_master_seal_1', '초월 시험 · 축제 허수아비', '초월의 인장을 원하나요? 첫 시험은 교정의 허수아비 대장을 쓰러뜨리는 거예요.', 'foe', 'elite_scarecrow', 1, 7000, {'master_seal': 1}, 19),
    Q('q_pumpkin_king', '호박 왕 토벌', '축제 무대의 호박 왕을 쓰러뜨려 주세요. 교문 밖에서 학생들이 기다리고 있어요.', 'boss', 'festival_pumpkin_king', 1, 8000, {'enhance_stone_hi': 2, 'seed_power': 1}, 20),
    # ---- 8구역 B급 게이트 · 망자의 묘소 (index 21-23)
    Q('q_bone_collector', '묘소 유품 수집', '묘소 기사들의 오래된 유골 6개를 모아 주세요. 정중히 안치하겠습니다.', 'collect', 'old_bone', 6, 5000, {'elixir': 1}, 21),
    Q('q_general', '해골 장군 토벌', '묘소를 순찰하는 해골 장군을 쉬게 해 주세요.', 'foe', 'elite_skeleton', 1, 6000, {'abyss_crystal': 1}, 22),
    Q('q_master_seal_2', '초월 시험 · 망자의 정수', '두 번째 시험이에요. 묘소의 망령에게서 정수를 6개 모아 오세요. 인장의 재료가 된답니다.', 'collect', 'ghost_essence', 6, 8000, {'master_seal': 1}, 22),
    Q('q_herald', '심연의 전령 모르데인', '묘소 심부의 전령을 막아 주세요. 한때 S급이었던 헌터라고 해요. 그의 이름을 되찾아 주세요.', 'boss', 'boss', 1, 12000, {'elixir': 2, 'enhance_stone_hi': 2}, 23),
    # ---- 9구역 병원 (index 24-26)
    Q('q_pill_slime', '알약 슬라임 정리', '병동 약 상자에서 알약 슬라임이 쏟아져 나와요. 10마리를 정리해 주세요.', 'kill', 'pill_slime', 10, 6000, {'panacea': 1}, 24),
    Q('q_master_seal_3', '초월 시험 · 해골의 행진', '마지막 시험이에요. 병원 복도의 해골 장군을 쓰러뜨리세요.', 'foe', 'elite_skeleton', 1, 9000, {'master_seal': 1}, 25),
    Q('q_plague_lich', '역병의 리치 토벌', '격리 병동의 역병 리치를 쓰러뜨려 주세요. 환자들이 기다리고 있어요.', 'boss', 'plague_lich', 1, 10000, {'megalixir': 1, 'enhance_stone_hi': 2}, 26),
    # ---- 10구역 A급 게이트 · 가라앉은 신전 (index 27-29)
    Q('q_siren_song', '노래를 멈춰라', '세이렌의 노래에 잠든 구조대원이 셋이나 돼요. 세이렌 8마리를 처치해 주세요.', 'kill', 'siren', 8, 9000, {'panacea': 3, 'acc_sleep_ward': 1}, 27),
    Q('q_pearl_collect', '진주 회수', '잠긴 참배로의 진주 8개를 모아 오세요. 장비 공방에서 쓸 재료래요.', 'collect', 'pearl', 8, 8000, {'enhance_stone_hi': 1, 'acc_regen_ring': 1}, 27),
    Q('q_turtle', '정원의 거북', '거북 타이탄을 깨워 쓰러뜨려 주세요. 등의 사원에 보물이 있대요.', 'foe', 'turtle_titan', 1, 11000, {'enhance_stone_hi': 2, 'seed_life': 1}, 28),
    Q('q_leviathan', '바다의 수문', '신전 가장 깊은 곳의 레비아탄이 수문을 막고 있어요. 쓰러뜨려 주세요.', 'boss', 'leviathan', 1, 20000, {'megalixir': 1, 'enhance_stone_abyss': 1}, 29),
    # ---- 11구역 습격당한 길드 거리 (index 30-32)
    Q('q_street_hounds', '거리의 사냥개 퇴치', '길드 거리를 떠도는 사냥개 무리를 10마리 처치해 주세요. 구조견 콩이를 닮은 녀석도 있어요.', 'kill', 'street_hound', 10, 12000, {'x_potion': 2}, 30),
    Q('q_street_scout', '차이슬의 정찰', '상가 골목 2층까지 들어가 몬스터의 이동 경로를 확인해 주세요.', 'explore', 'guild_street_2', 1, 12000, {'x_potion': 3, 'acc_eagle_eye': 1}, 30),
    Q('q_gargoyle_horn', '가고일의 뿔', '가고일 뿔 5개를 모아 오세요. 방어구를 강화하는 데 쓰인대요.', 'collect', 'gargoyle_horn', 5, 14000, {'enhance_stone_hi': 2}, 31),
    Q('q_abyss_herald', '심연의 사도 토벌', '길드 본부 앞 광장을 짓밟은 심연의 사도를 쓰러뜨려 주세요. 간판을 되찾읍시다.', 'boss', 'abyss_herald', 1, 16000, {'megalixir': 1, 'enhance_stone_abyss': 1}, 32),
    # ---- 12구역 S급 게이트 · 심연 (index 33-35)
    Q('q_void_shards', '공허의 결정 회수', '장비 공방에서 공허의 파편 10개를 원해요. 곽 장인 말로는 "망치가 떨리는 재료"래요.', 'collect', 'void_shard', 10, 15000, {'enhance_stone_abyss': 2}, 33),
    Q('q_void_wisps', '공허의 도깨비불 소탕', '공허의 도깨비불 10마리를 처치해 주세요. 시선만으로 마법을 봉한대요. 눈을 피하세요!', 'kill', 'void_wisp', 10, 15000, {'x_potion': 4}, 33),
    Q('q_reaper', '사신의 낫', '공허의 회랑을 떠도는 공허의 사신을 쓰러뜨려 주세요.', 'foe', 'void_reaper', 1, 20000, {'seed_mind': 1, 'acc_curse_ward': 1}, 34),
    Q('q_last_dawn', '새벽을 돌려주세요', '의뢰인: 새벽 길드 전원. 내용: 아침을 돌려주세요. 보상은 모두가 조금씩 모았어요.', 'boss', 'abyss_lord', 1, 50000, {'megalixir': 2}, 35),
    # ---- 붉은 게이트 (postgame, index 36-38)
    Q('q_trial_emblems', '붉은 문장 수집', '붉은 게이트에서 되살아난 보스들의 문장 10개를 모아 오세요. 헌터의 증거래요.', 'collect', 'trial_emblem', 10, 30000, {'megalixir': 2, 'enhance_stone_abyss': 3}, 36),
    Q('q_ex_forest', '현상 수배 · 금빛 고목', '붉은 게이트 제1문의 금빛 고목 수호자를 쓰러뜨려 주세요.', 'kill', 'forest_guardian_ex', 1, 40000, {'seed_life': 2}, 36),
    Q('q_ex_herald', '현상 수배 · 제자의 메아리', '제2문 너머의 모르데인 메아리를 쓰러뜨려 주세요. 이번엔 자기 힘으로 싸운대요.', 'kill', 'boss_ex', 1, 55000, {'seed_guard': 2}, 37),
    Q('q_ex_lord', '현상 수배 · 마지막 그림자', '붉은 옥좌의 심연의 군주 · 진을 쓰러뜨려 주세요. 길드 역사상 최고 현상금이에요.', 'boss', 'abyss_lord_ex', 1, 100000, {'seed_power': 2, 'megalixir': 3}, 38),
]
