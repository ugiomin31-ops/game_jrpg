# -*- coding: utf-8 -*-
"""Re-themed display names for the hunter setting. Applied to Assets/_Game/Resources/Data by Tools/content/apply_names.py.

EQUIPMENT, ITEMS and JOBS map id -> dict(display_name=..., description=...) for rows of equipment.json, items.json and
jobs.json. Only ids listed here change; a row's description is written only when the entry gives one.
ENEMIES maps id -> dict(display_name=...) for enemies.json. Enemy descriptions are not a field of enemies.json; they
are written from texts.ENEMY_DESC / ENEMY_DESC_UPDATE into text_ko (enemy_desc_<id>) by build_world.py.
Weapons and armour are hunter gear (T1 starter -> T8 newest); chapter materials are gate mana stones (마석) and gate
by-products; the guild's own colours and names carry 새벽 (dawn) instead of 여명 (dawn of the village)."""

# ------------------------------------------------------------------ equipment (gear lines T1..T8, job weapons, accessories)
EQUIPMENT = {
    # sword line (melee hunter weapons)
    'sword_bronze': dict(display_name='쇠파이프', description='길가에서 주운 쇠파이프. 헌터 첫날의 무기로는 충분하다. 든든하진 않아도 없는 것보단 낫다.'),
    'sword_iron': dict(display_name='삼단봉', description='휴대성이 좋은 삼단봉. 손목 스냅으로 빠르게 휘두를 수 있다.'),
    'sword_knight': dict(display_name='강철 사냥 단검', description='사냥 헌터들이 즐겨 쓰는 강철 단검. 날이 짧아 다루기 쉽다.'),
    'sword_flamberge': dict(display_name='웨이브 블레이드', description='물결치는 칼날이 적의 급소를 노리는 검입니다.'),
    'sword_runic': dict(display_name='마석 각인 블레이드', description='게이트 마석 가루로 각인한 장검. 칼날이 게이트의 기운에 반응한다.'),
    'sword_tidal': dict(display_name='심해 곡도', description='A급 신전의 물결을 닮은 곡도. 칼등에 파도 문양이 빛난다.'),
    'sword_void': dict(display_name='공허 절단검', description='심연의 핵에서 벼린 검은 칼날. 갈라진 틈으로 보랏빛이 새어 나온다.'),
    'sword_dawn': dict(display_name='새벽검', description='새벽 길드의 문장을 새긴 최상급 검. 어둠을 가르는 첫 빛처럼 날이 선다.'),
    # staff line (mage gear)
    'staff_oak': dict(display_name='연습용 마력 완드', description='원소 마법의 기초를 익히는 나무 완드. 헌터 교육원 지급품이다.'),
    'staff_crystal': dict(display_name='마석 완드', description='맑은 마석이 마력을 모아 주는 완드입니다.'),
    'staff_sage': dict(display_name='전술 마력 완드', description='마법의 흐름을 정리해 주는 전술용 완드입니다.'),
    'staff_ruby': dict(display_name='홍염 마력 완드', description='붉은 홍옥이 강한 마력을 이끌어 내는 완드입니다.'),
    'staff_bone': dict(display_name='뼈 장식 완드', description='뿔 달린 뼈 장식이 초록 불꽃을 품은 완드. 망자의 힘을 빌린다.'),
    'staff_coral': dict(display_name='산호 마력 완드', description='산호 가지가 바닷물의 마력을 모은다.'),
    'staff_void': dict(display_name='공허 마력 완드', description='두 고리 사이에 공허의 구슬이 떠 있는 검은 완드.'),
    'staff_starlight': dict(display_name='성광 마력 완드', description='별빛과 네 원소의 마석을 엮은 최상급 완드입니다.'),
    # bow line (archer gear)
    'bow_short': dict(display_name='양궁용 리커브 보우', description='가볍고 다루기 쉬운 입문용 리커브 보우입니다.'),
    'bow_hunter': dict(display_name='사냥꾼 컴파운드 보우', description='사냥꾼이 즐겨 쓰는 균형 잡힌 활입니다.'),
    'bow_composite': dict(display_name='합성 컴파운드 보우', description='여러 재료를 겹쳐 힘과 정확도를 높인 활입니다.'),
    'bow_gale': dict(display_name='질풍 리커브 보우', description='바람처럼 빠르게 시위를 당길 수 있는 활입니다.'),
    'bow_wraith': dict(display_name='사슬 장식 보우', description='사슬에 묶인 뼈 활. 시위를 당기면 원혼이 울부짖는다.'),
    'bow_tide': dict(display_name='심해 보우', description='지느러미처럼 펼쳐진 활채가 물살을 가르듯 화살을 보낸다.'),
    'bow_void': dict(display_name='공허 보우', description='가시 돋친 검은 활. 보랏빛 맥동이 화살에 실린다.'),
    'bow_star': dict(display_name='유성 보우', description='유성처럼 정확한 화살을 쏘는 게이트 마석 활입니다.'),
    # mace line (healer gear)
    'mace_wood': dict(display_name='구급 지팡이', description='초보 응급 구조원을 위한 소박한 나무 지팡이. 상처에 대는 것만으로도 든든하다.'),
    'mace_silver': dict(display_name='의료용 메이스', description='은빛 머리 장식이 달린 응급 구조용 메이스입니다.'),
    'mace_requiem': dict(display_name='진혼의 쇠추 망치', description='쇠추가 달린 망치. 휘두를 때마다 망령이 가라앉는다.'),
    'mace_dawn': dict(display_name='새벽의 홀', description='마지막 게이트를 밝히는 새벽의 홀입니다.'),
    # armour line
    'armor_chain': dict(display_name='방검 조끼', description='움직임을 크게 방해하지 않는 기본 방검 조끼입니다.'),
    'armor_scale': dict(display_name='경량 택티컬 아머', description='겹친 금속 판이 몸을 보호하는 경량 방어구입니다.'),
    'armor_plate': dict(display_name='택티컬 아머', description='두꺼운 판으로 전위를 지키는 방어구입니다.'),
    'armor_dragon': dict(display_name='드레이크 비늘 아머', description='드레이크의 단단한 비늘로 보강한 방어구입니다.'),
    'armor_rune': dict(display_name='마석 강화 아머', description='마석 각인으로 강화한 판금 방어구. 게이트의 저주를 튕겨 낸다.'),
    'armor_tidal': dict(display_name='심해 수호 아머', description='A급 신전 수호병의 비늘 방어구. 물결처럼 가볍게 움직인다.'),
    'armor_void': dict(display_name='공허 아머', description='심연의 결정으로 덧댄 방어구. 빛을 삼키는 듯 어둡다.'),
    'armor_dawn': dict(display_name='새벽 길드 아머', description='새벽 길드의 문장이 새겨진 최상급 방어구입니다. 게이트 마석으로 덧댔다.'),
    # robe line (mage armour)
    'robe_cloth': dict(display_name='입문용 마력 코트', description='마법사와 힐러가 함께 입는 소박한 마력 코트입니다.'),
    'robe_silk': dict(display_name='마력 코트', description='마력의 흐름을 돕는 부드러운 실크 마력 코트입니다.'),
    'robe_mystic': dict(display_name='전술 마력 코트', description='문양이 마법 방어를 높여 주는 마력 코트입니다.'),
    'robe_sage': dict(display_name='현자 마력 코트', description='현자의 지식으로 짜인 고급 마력 코트입니다.'),
    'robe_spirit': dict(display_name='정화 마력 코트', description='망자의 기운을 달래는 주문이 수놓인 마력 코트입니다.'),
    'robe_pearl': dict(display_name='진주빛 마력 코트', description='진주 가루로 물들인 비단 코트. 마력이 잔잔히 흐른다.'),
    'robe_void': dict(display_name='공허 마력 코트', description='공허의 실로 짠 마력 코트. 입은 이의 마력을 깊게 끌어낸다.'),
    'robe_dawn': dict(display_name='새벽 마력 코트', description='새벽 길드의 빛을 수놓은 최상급 마력 코트입니다. 마력이 새벽처럼 퍼진다.'),
    # garb line (archer armour: hunter jackets)
    'garb_leather': dict(display_name='헌터 재킷', description='헌터 입문 세트의 가죽 재킷. 움직임을 살리는 가벼운 재킷입니다.'),
    'garb_ranger': dict(display_name='레인저 재킷', description='탐색 헌터를 위한 질긴 가죽 조끼입니다.'),
    'garb_shadow': dict(display_name='그림자 가죽 재킷', description='그림자처럼 몸을 숨기기 좋은 유연한 가죽 재킷입니다.'),
    'garb_wind': dict(display_name='바람막이 재킷', description='바람처럼 가볍게 움직일 수 있는 재킷입니다.'),
    'garb_wraith': dict(display_name='안개 위장 재킷', description='안개처럼 흐릿한 가죽 재킷. 적의 눈을 속인다.'),
    'garb_tide': dict(display_name='심해 재킷', description='물고기 비늘을 엮은 재킷. 물속에서도 몸이 가볍다.'),
    'garb_void': dict(display_name='공허 재킷', description='그림자 짐승의 가죽으로 만든 재킷. 발소리가 사라진다.'),
    'garb_dawn': dict(display_name='새벽 재킷', description='새벽 길드 문장이 달린 최상급 재킷입니다. 회피와 기동성이 높다.'),
    # accessories that named the old seals and gold
    'acc_crystal_crown': dict(display_name='수정 왕관', description='게이트 마석과 심연 군주의 왕관 조각을 녹여 만든 왕관. 모든 능력치가 오른다.'),
    'acc_guardian_ring': dict(display_name='수호의 반지', description='길드 수호의 힘을 담은 반지.'),
    'acc_hero_emblem': dict(display_name='영웅의 문장', description='네 개의 게이트 마석을 모은 증표. 모든 능력치가 오른다.'),
    'acc_gold_charm': dict(display_name='황금 부적', description='금화 냄새를 맡는 부적. 전투에서 얻는 보상 금액이 25 % 늘어난다(파티 합산, 최대 +100 %).'),
}

# ------------------------------------------------------------------ items (consumables, gate materials, job items)
ITEMS = {
    # healing: 하급 / 중급 / 상급 / 특급
    'healing_potion': dict(display_name='회복 포션(하급)', description='아군 한 명의 HP를 60 회복합니다.'),
    'hi_potion': dict(display_name='회복 포션(중급)', description='아군 한 명의 HP를 250 회복합니다.'),
    'mega_potion': dict(display_name='회복 포션(상급)', description='아군 한 명의 HP를 600 회복합니다.'),
    'x_potion': dict(display_name='회복 포션(특급)', description='아군 한 명의 HP를 2000 회복합니다.'),
    # mana
    'ether': dict(display_name='마나 포션', description='아군 한 명의 MP를 30 회복합니다.'),
    'hi_ether': dict(display_name='마나 포션(중급)', description='아군 한 명의 MP를 90 회복합니다.'),
    'max_ether': dict(display_name='마나 포션(상급)', description='아군 한 명의 MP를 모두 회복합니다.'),
    # party healing and revive
    'elixir': dict(display_name='전원 회복 앰플', description='아군 전원의 HP를 모두 회복합니다.'),
    'megalixir': dict(display_name='전원 회복 키트', description='아군 전원의 HP와 MP를 모두 회복합니다.'),
    'phoenix_feather': dict(display_name='소생 앰플', description='쓰러진 아군을 HP 30%로 되살립니다.'),
    'phoenix_plume': dict(display_name='소생 앰플(상급)', description='쓰러진 아군 한 명을 HP 100 %로 되살립니다.'),
    'camp_tent': dict(display_name='구조 텐트', description='전투 밖에서만 사용. 아군 전원의 HP와 MP를 모두 회복합니다(쓰러진 동료 제외).'),
    # escape and boosts
    'return_stone': dict(display_name='게이트 탈출 비콘', description='전투 밖에서 사용하면 길드로 돌아갑니다.'),
    'guard_tonic': dict(display_name='방어 부스트 드링크', description='아군 전원의 방어력을 3턴 동안 높입니다.'),
    'magic_tonic': dict(display_name='마력 부스트 드링크', description='아군 전원의 마력을 3턴 동안 높입니다.'),
    'speed_tonic': dict(display_name='속도 부스트 드링크', description='아군 전원의 속도를 3턴 동안 높입니다.'),
    'power_tonic': dict(display_name='공격 부스트 드링크', description='아군 전원의 공격력을 3턴 동안 높입니다.'),
    # job items
    'job_medal': dict(display_name='각성의 증표', description='길드가 인정한 헌터에게 주는 증표. 1차 각성에 필요합니다. 팔 수 없습니다.'),
    'master_seal': dict(display_name='초월의 인장', description='한 길을 끝까지 걸은 헌터의 인장. 2차 각성에 필요합니다. 팔 수 없습니다.'),
    # gate mana stones (chapter materials of the first four gates)
    'verdant_crystal': dict(display_name='신록 마석', description='E급 숲 게이트의 마석. 생명력이 깃들어 있다.'),
    'frost_crystal': dict(display_name='빙결 마석', description='D급 얼음 동굴의 마석. 결코 녹지 않는다.'),
    'ember_crystal': dict(display_name='홍염 마석', description='C급 사막 게이트의 마석. 손에 쥐면 따뜻하다.'),
    'abyss_crystal': dict(display_name='심연 마석', description='마지막 게이트에서 새어 나온 검은 마석.'),
    # other gate by-products
    'trial_emblem': dict(display_name='붉은 게이트 문장', description='붉은 게이트에서 쓰러뜨린 보스의 메아리를 증명하는 문장.'),
    'old_bone': dict(display_name='오래된 유골', description='묘소 기사의 단단한 뼈. 정중히 안치해 주세요.'),
    'cursed_straw': dict(display_name='허수아비 짚', description='원한이 스민 허수아비의 짚.'),
    'golem_sandstone': dict(display_name='골렘 코어 파편', description='마력이 깃든 단단한 골렘 코어 조각.'),
}

# ------------------------------------------------------------------ jobs (awakening paths; spec.JOB_NAMES_KO)
JOBS = {
    'warrior': dict(display_name='전사', description='방패와 검으로 파티 앞에 서는 기본 직업입니다. 균형 잡힌 공격과 방어를 갖췄습니다.'),
    'knight': dict(display_name='가디언', description='동료를 지키는 방패 헌터입니다. 체력과 방어가 크게 오르고, 몬스터의 공격을 끌어모으는 기술을 익힙니다.'),
    'paladin': dict(display_name='철벽의 수호자', description='방패 가드를 완성한 수호자입니다. 가디언의 단단함에 신성한 공격과 파티 전체를 지키는 결계를 더합니다.'),
    'berserker': dict(display_name='광전사', description='방어를 버리고 공격에 모든 것을 거는 헌터입니다. 공격과 치명타가 오르고 방어는 떨어집니다.'),
    'warlord': dict(display_name='투신', description='전장을 지배하는 격투의 정점입니다. 압도적인 공격력으로 적 전체를 무너뜨리고 아군의 사기를 높입니다.'),
    'mage': dict(display_name='마법사', description='원소 마법을 다루는 기본 직업입니다.'),
    'elementalist': dict(display_name='원소술사', description='불, 얼음, 번개의 마석 마법을 다루는 술사입니다. 마력과 MP가 오르고 상태 이상을 거는 원소 마법을 익힙니다.'),
    'archmage': dict(display_name='대마법사', description='마법의 정점에 선 대마법사입니다. 마력이 크게 오르고 적 전체를 휩쓰는 대마법을 씁니다.'),
    'warlock': dict(display_name='저주술사', description='저주와 어둠을 다루는 마법사입니다. 적을 약하게 만들고 생명력을 빼앗는 주문을 익힙니다.'),
    'abyssal': dict(display_name='심연술사', description='심연의 힘을 빌린 술사입니다. 공허의 마법으로 적 전체를 잠식하고 저주를 퍼뜨립니다.'),
    'archer': dict(display_name='궁수', description='활과 화살로 싸우는 기본 직업입니다.'),
    'sniper': dict(display_name='저격수', description='한 발에 모든 것을 거는 저격수입니다. 명중과 치명타가 오르고 방어를 꿰뚫는 사격을 익힙니다.'),
    'divine_archer': dict(display_name='신궁', description='하늘의 화살을 쏘는 신궁입니다. 신성한 화살비로 적 전체를 꿰뚫습니다.'),
    'ranger': dict(display_name='암살자', description='그림자처럼 움직이는 헌터입니다. 속도와 회피가 오르고 여러 번 쏘는 연사 기술을 익힙니다.'),
    'shadow_stalker': dict(display_name='그림자 암살자', description='그림자에 숨어 표적을 쫓는 암살자입니다. 압도적인 속도로 어둠의 연격을 퍼붓습니다.'),
    'cleric': dict(display_name='힐러', description='치유와 응급 처치를 다루는 기본 직업입니다.'),
    'priest': dict(display_name='치유사', description='치유에 정통한 전문가입니다. MP와 마력이 오르고 회복과 보호 기술이 늘어납니다.'),
    'saint': dict(display_name='성녀', description='기적을 일으키는 성녀입니다. 쓰러진 동료를 한꺼번에 일으키고 파티 전체를 지킵니다.'),
    'exorcist': dict(display_name='퇴마사', description='부적과 주문으로 악령을 몰아내는 퇴마사입니다. 마력이 오르고 신성 속성 공격 주술을 익힙니다.'),
    'inquisitor': dict(display_name='심판관', description='악을 심판하는 심판관입니다. 강력한 신성 공격과 적을 무력하게 만드는 심문 기술을 씁니다.'),
}

# ------------------------------------------------------------------ enemies (display names only; see module docstring)
ENEMIES = {
    # clashing names of existing monsters
    'slime': dict(display_name='점액 슬라임'),
    'elite_sand_golem': dict(display_name='철광 거인'),
    # zone monsters (spec.ZONE_VARIANTS)
    'subway_bat_lord': dict(display_name='지하철 박쥐 군주'),
    # hunter monsters with their own models (spec.HUNTER_MONSTERS)
    'goblin': dict(display_name='고블린'),
    'goblin_shaman': dict(display_name='고블린 주술사'),
    'sewer_rat': dict(display_name='땅굴쥐'),
    'cave_mole': dict(display_name='굴착 두더지'),
    'orc': dict(display_name='오크 전사'),
    'high_orc': dict(display_name='하이 오크'),
    'sewer_slime': dict(display_name='하수구 슬라임'),
    'tunnel_bat': dict(display_name='터널 박쥐'),
    'scrap_colossus': dict(display_name='고철 거상'),
    'scrap_golem': dict(display_name='고철 로봇'),
    'oil_slime': dict(display_name='기름 슬라임'),
    'spark_wisp': dict(display_name='전기 도깨비불'),
    'iron_beetle': dict(display_name='강철 풍뎅이'),
    'crystal_cave_lord': dict(display_name='수정 동굴의 주인'),
    'crystal_slime': dict(display_name='수정 슬라임'),
    'cave_spider': dict(display_name='동굴 거미'),
    'festival_pumpkin_king': dict(display_name='축제의 호박왕'),
    'locker_mimic': dict(display_name='사물함 미믹'),
    'school_ghost': dict(display_name='방과 후 유령'),
    'plague_lich': dict(display_name='역병의 리치'),
    'pill_slime': dict(display_name='알약 슬라임'),
    'syringe_bee': dict(display_name='주사벌'),
    'bandage_ghost': dict(display_name='붕대 미라'),
    'abyss_herald': dict(display_name='심연의 사도'),
    'street_hound': dict(display_name='거리의 사냥개'),
}
