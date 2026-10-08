# -*- coding: utf-8 -*-
"""Guild quests for the 35-floor campaign (~50). unlock_floor is the 0-based floor index the party must have
reached (GameState.DeepestFloor). The 12 original quest ids keep their ids (saves keep their progress) with
targets and unlock floors moved onto the new layout.

Job items: 4 job_medal = forest_guardian's guaranteed drop + three chapter 2 trials (all four heroes can take
their advanced job around Lv 15-18); 4 master_seal = the chapter 4 herald's drop + three chapter 5 trials
(master jobs right after the herald falls, Lv 40+)."""


def Q(id, title, desc, kind, target, count, gold, items, unlock):
    return dict(id=id, title=title, description=desc, kind=kind, target_id=target, count=count,
                reward_gold=gold, reward_items=dict(items), unlock_floor=unlock, _file=id)


QUESTS = [
    # ---- 제1장 이끼 낀 숲의 유적 (B1F-B5F)
    Q('q_slime_cull', '슬라임 소탕', '유적 입구의 슬라임이 늘고 있어요. 8마리만 정리해 주세요.', 'kill', 'slime', 8, 150, {'healing_potion': 3}, 0),
    Q('q_forest_fiber', '덩굴 섬유 납품', '대장간에서 질긴 덩굴 섬유 4개가 필요하대요.', 'collect', 'forest_fiber', 4, 250, {'remedy': 2}, 0),
    Q('q_toxic_king', '독왕 버섯 토벌', '덩굴 회랑을 떠도는 거대한 독버섯을 쓰러뜨려 주세요.', 'foe', 'elite_mushroom', 1, 600, {'acc_antidote_ring': 1}, 1),
    Q('q_bee_swarm', '벌집 정리', '살인벌이 유적 천장에 벌집을 지었어요. 10마리를 처치하면 마을 꿀단지가 무사할 거예요.', 'kill', 'killer_bee', 10, 500, {'ether': 2, 'enhance_stone': 1}, 1),
    Q('q_beetle_vault', '갑충왕의 보물고', '뿌리 내린 석실의 보물고를 지키는 투구 갑충을 몰아내 주세요. 보물고는 여러분 몫이에요.', 'foe', 'elite_rhino_beetle', 1, 900, {'enhance_stone': 2}, 2),
    Q('q_gold_slime', '금빛 소문', '금화처럼 반짝이는 슬라임을 봤다는 사람이 있어요! 한 마리만 잡아 주시면 사례할게요.', 'kill', 'gold_slime', 1, 300, {'acc_iron_bangle': 1}, 2),
    Q('q_guardian', '고목의 안식', '고목의 성소에서 검은 결정에 사로잡힌 수호자를 쉬게 해 주세요.', 'boss', 'forest_guardian', 1, 1500, {'hi_potion': 3, 'enhance_stone': 2}, 3),
    # ---- 제2장 얼어붙은 해식동굴 (B6F-B10F)
    Q('q_frost_survey', '빙결 수로 조사', 'B7F 빙결의 수로까지 내려가 길을 확인해 주세요.', 'explore', 'frost_2', 1, 800, {'ether': 3}, 5),
    Q('q_wolf_hunt', '서리 늑대 사냥', '서리 늑대 10마리를 사냥해 주세요. 털가죽은 가지셔도 돼요.', 'kill', 'ice_wolf', 10, 1200, {'hi_potion': 3}, 5),
    Q('q_job_medal_1', '전직 시험 · 사냥꾼의 길', '길드의 첫 번째 전직 시험이에요. 설원 뿔토끼 8마리를 잡아 오세요. 통과하면 전직의 증표를 드려요.', 'kill', 'snow_rabbit', 8, 600, {'job_medal': 1}, 5),
    Q('q_crab_king', '거대 집게 토벌', '수로를 막고 있는 거대 산호 집게를 치워 주세요.', 'foe', 'elite_coral_crab', 1, 1500, {'phoenix_feather': 2}, 6),
    Q('q_job_medal_2', '전직 시험 · 우두머리', '두 번째 시험은 실전이에요. 서리 늑대 무리의 우두머리를 쓰러뜨리세요. 전직의 증표가 걸려 있어요.', 'foe', 'elite_ice_wolf', 1, 900, {'job_medal': 1}, 6),
    Q('q_job_medal_3', '전직 시험 · 서리의 기억', '세 번째 시험은 인내예요. 서리 털가죽 6장을 모아 오세요. 증표를 만드는 데 쓰인대요.', 'collect', 'frost_fur', 6, 900, {'job_medal': 1}, 7),
    Q('q_yeti_tyrant', '설산의 폭군', '설원의 굴 보물고 앞에서 버티는 거대 설인을 쓰러뜨려 주세요.', 'foe', 'elite_yeti', 1, 2200, {'enhance_stone': 2, 'seed_guard': 1}, 7),
    Q('q_dawn_letter', '산호 속 편지', '산호 빙벽 어딘가에 아이가 쓴 편지가 끼워져 있대요. B9F까지 가서 찾아봐 주세요.', 'explore', 'frost_4', 1, 1500, {'acc_life_pendant': 1}, 7),
    Q('q_kraken', '여왕의 자장가', '빙해의 여왕이 다시 노래하도록, 그녀를 괴롭히는 속삭임을 끊어 주세요.', 'boss', 'frost_kraken', 1, 3000, {'hi_ether': 2, 'enhance_stone': 3}, 8),
    # ---- 제3장 작열하는 용암굴 (B11F-B15F)
    Q('q_drake_scales', '드레이크 비늘 납품', '내열 갑옷 연구에 드레이크 비늘 5장이 필요합니다.', 'collect', 'drake_scale', 5, 2500, {'mega_potion': 2}, 10),
    Q('q_ember_bees', '불티 사냥', '화염벌이 날아다니며 마을 창고에 불티를 옮겨요. 10마리를 처치해 주세요.', 'kill', 'ember_bee', 10, 2200, {'fire_bomb': 2, 'ice_bomb': 2}, 10),
    Q('q_hellhound', '쌍두견 퇴치', '용암 협곡을 배회하는 쌍두 사냥개를 처치해 주세요.', 'foe', 'elite_hellhound', 1, 3000, {'enhance_stone': 2}, 11),
    Q('q_golem_breaker', '사막의 거상 토벌', '사암 석굴의 보물고를 지키는 거상을 무너뜨려 주세요.', 'foe', 'elite_sand_golem', 1, 4000, {'ember_crystal': 1}, 12),
    Q('q_metal_slime', '은빛 도망자', '쇠처럼 단단한 은빛 슬라임이 나타났대요. 잡기만 하면 엄청난 경험이 된다나요? 행운을 빌어요!', 'kill', 'metal_slime', 1, 2000, {'seed_swift': 1}, 12),
    Q('q_drake_king', '홍염 비룡 사냥', '불사조의 둥지 근처를 나는 홍염 비룡을 떨어뜨려 주세요.', 'foe', 'elite_fire_drake', 1, 5000, {'enhance_stone_hi': 1, 'acc_burn_ward': 1}, 13),
    Q('q_sphinx', '태양의 수수께끼', '태양의 제단의 스핑크스를 진정시켜 주세요.', 'boss', 'flame_sphinx', 1, 6000, {'hi_ether': 3, 'enhance_stone_hi': 1}, 13),
    # ---- 제4장 망자의 묘소 (B16F-B20F)
    Q('q_bone_collector', '뼈 수집가', '묘소 기사들의 오래된 뼈 6개를 모아 주세요. 정중히 안치하겠습니다.', 'collect', 'old_bone', 6, 5000, {'elixir': 1}, 15),
    Q('q_general', '해골 장군 토벌', '묘소를 순찰하는 해골 장군을 쉬게 해 주세요.', 'foe', 'elite_skeleton', 1, 6000, {'abyss_crystal': 1}, 15),
    Q('q_lament', '통곡의 납골당 정화', '도깨비불 8개를 잠재워 납골당의 통곡을 멈춰 주세요.', 'kill', 'wisp', 8, 6000, {'abyss_crystal': 1, 'elixir': 1}, 16),
    Q('q_scarecrow_king', '허수아비 왕', '시든 호밀 밭의 허수아비 왕을 베어 주세요. 까마귀들이 마을까지 날아와요.', 'foe', 'elite_scarecrow', 1, 7000, {'enhance_stone_hi': 1, 'acc_sleep_ward': 1}, 16),
    Q('q_knight_commander', '칠흑의 기사단장', '허수아비 밭 보물고를 지키는 기사단장에게 마지막 명령을 내려 주세요. "이제 쉬어라."', 'foe', 'elite_dark_knight', 1, 8000, {'enhance_stone_hi': 2, 'seed_power': 1}, 17),
    Q('q_pandora', '판도라의 상자', '납골당 깊은 곳의 거대한 미믹을 처치해 주세요. 열지 말고 부수세요!', 'foe', 'elite_mimic', 1, 9000, {'acc_curse_ward': 1}, 18),
    Q('q_herald', '심연의 전령', '옥좌에 앉은 전령을 막아 주세요. 루멘 님의 제자였다는 소문이… 사실일까요?', 'boss', 'boss', 1, 12000, {'elixir': 2, 'enhance_stone_hi': 2}, 18),
    # ---- 제5장 가라앉은 신전 (B21F-B25F)
    Q('q_master_seal_1', '인장 시험 · 녹슨 맹세', '마스터의 인장을 원하나요? 첫 시험은 신전의 익사한 기사를 쉬게 하는 것이에요.', 'foe', 'drowned_knight', 1, 8000, {'master_seal': 1}, 20),
    Q('q_sunken_bell', '물속의 종소리', '종의 줄이 신전의 정원까지 이어져 있대요. B23F 거북의 정원까지 내려가 확인해 주세요.', 'explore', 'sunken_3', 1, 6000, {'x_potion': 3, 'acc_regen_ring': 1}, 20),
    Q('q_master_seal_2', '인장 시험 · 진주의 무게', '두 번째 시험이에요. 신전의 진주 8개를 모아 오세요. 인장의 재료가 된답니다.', 'collect', 'pearl', 8, 8000, {'master_seal': 1}, 21),
    Q('q_siren_song', '노래를 멈춰라', '세이렌의 노래에 잠든 탐험가가 셋이나 돼요. 세이렌 8마리를 처치해 주세요.', 'kill', 'siren', 8, 9000, {'panacea': 3, 'acc_sleep_ward': 1}, 21),
    Q('q_master_seal_3', '인장 시험 · 나가의 찬가', '마지막 시험이에요. 진주 왕관의 나가 사제를 쓰러뜨리세요.', 'foe', 'naga_priestess', 1, 10000, {'master_seal': 1}, 22),
    Q('q_turtle', '정원의 거북', '거북의 정원 보물고 앞에서 잠든 타이탄을 깨워 쓰러뜨려 주세요. 등의 사원에 보물이 있대요.', 'foe', 'turtle_titan', 1, 11000, {'enhance_stone_hi': 2, 'seed_life': 1}, 22),
    Q('q_golden_mimic', '황금 상자', '신전에 금빛 보물 상자가 돌아다닌대요. …돌아다닌다고요? 아무튼 잡아 주세요!', 'kill', 'golden_mimic', 1, 15000, {'seed_magic': 1}, 22),
    Q('q_leviathan', '바다의 뚜껑', '신전 가장 깊은 곳의 레비아탄이 길을 막고 있어요. 종의 줄은 그 너머로 이어져요.', 'boss', 'leviathan', 1, 20000, {'megalixir': 1, 'enhance_stone_abyss': 1}, 23),
    # ---- 제6장 심연의 핵 (B26F-B30F)
    Q('q_void_shards', '공허의 결정 회수', '대장간에서 공허의 파편 10개를 원해요. 브론 씨 말로는 "망치가 떨리는 재료"래요.', 'collect', 'void_shard', 10, 15000, {'enhance_stone_abyss': 2}, 25),
    Q('q_shadow_hunt', '그림자 사냥', '그림자 짐승 10마리를 처치해 주세요. 등불을 든 사람 앞에서는 길을 비킨대요.', 'kill', 'shadow_beast', 10, 15000, {'x_potion': 4, 'acc_tp_crest': 1}, 25),
    Q('q_lamp_oil', '등불 기름', '수정 협곡 아래에서 종소리가 들린대요. B28F까지 내려가 루멘 님의 흔적을 찾아 주세요.', 'explore', 'abyss_3', 1, 12000, {'max_ether': 3}, 25),
    Q('q_fallen_angel', '떨어진 날개', '그림자 숲의 타락 천사를 쉬게 해 주세요. 한때 군주를 막으러 내려왔던 이래요.', 'foe', 'fallen_angel', 1, 18000, {'enhance_stone_abyss': 2, 'acc_holy_amulet': 1}, 26),
    Q('q_crystal_horror', '소원의 괴수', '수정 협곡의 보물고를 지키는 수정 괴수를 부숴 주세요.', 'foe', 'crystal_horror', 1, 20000, {'seed_guard': 1, 'enhance_stone_abyss': 1}, 27),
    Q('q_reaper', '사신의 낫', '거울의 회랑을 떠도는 공허의 사신을 쓰러뜨려 주세요.', 'foe', 'void_reaper', 1, 20000, {'seed_mind': 1, 'acc_curse_ward': 1}, 27),
    Q('q_village_dawn', '마을 사람 모두의 의뢰', '의뢰인: 여명의 마을 사람 모두. 내용: 아침을 돌려주세요. 보상: 모두가 조금씩 모았어요.', 'boss', 'abyss_lord', 1, 50000, {'megalixir': 2}, 28),
    # ---- 시련의 회랑 (B31F-B35F, 클리어 후)
    Q('q_trial_emblems', '회랑의 문장', '시련의 문장 10개를 모아 오세요. 회랑을 걷는 자의 증표래요.', 'collect', 'trial_emblem', 10, 30000, {'megalixir': 2, 'enhance_stone_abyss': 3}, 30),
    Q('q_ex_forest', '현상 수배 · 금빛 고목', '시련의 회랑 제1문의 금빛 고목 수호자를 쓰러뜨려 주세요.', 'kill', 'forest_guardian_ex', 1, 40000, {'seed_life': 2}, 30),
    Q('q_ex_kraken', '현상 수배 · 진짜 바다의 노래', '제2문의 크라켄 여왕을 쓰러뜨려 주세요. 이번엔 자장가가 아니래요.', 'kill', 'frost_kraken_ex', 1, 45000, {'seed_mind': 2}, 31),
    Q('q_ex_sphinx', '현상 수배 · 마지막 일출', '제3문의 스핑크스를 쓰러뜨려 주세요. 태양을 떨어뜨린대요.', 'kill', 'flame_sphinx_ex', 1, 50000, {'seed_magic': 2}, 32),
    Q('q_ex_herald', '현상 수배 · 제자의 메아리', '제4문의 모르데인을 쓰러뜨려 주세요. 이번엔 자기 힘으로 싸운대요.', 'kill', 'boss_ex', 1, 55000, {'seed_guard': 2}, 33),
    Q('q_ex_leviathan', '현상 수배 · 풀려난 바다', '회랑 끝의 레비아탄을 쓰러뜨려 주세요.', 'kill', 'leviathan_ex', 1, 60000, {'seed_swift': 2}, 34),
    Q('q_ex_lord', '현상 수배 · 마지막 그림자', '회랑의 끝, 심연의 마지막 그림자를 쓰러뜨려 주세요. 길드 역사상 최고 현상금이에요.', 'boss', 'abyss_lord_ex', 1, 100000, {'seed_power': 2, 'megalixir': 3}, 34),
]
