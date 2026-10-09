"""Gear and item data for the 20-hour campaign (equipment.json, items.json).

Run: python3 Tools/content/gear_items.py          (rewrites both tables; idempotent)
     python3 Tools/content/gear_items.py --table   (also prints the hero-vs-weapon stat table)

Existing rows keep their values except the intended re-tunes below (tier, jobs, T8 legendary stats/recipes);
new rows use the ids fixed in Tools/content/spec.py.

Tier curve (CONTENT_20H_PLAN, CHAPTERS in spec.py). The level is the party level at which the tier is bought:
    T1 ch1 early (Lv1-6)   T2 ch1 late (Lv6-12)  T3 ch2 (Lv12-24)  T4 ch3 (Lv24-34)
    T5 ch4 (Lv34-44)       T6 ch5 (Lv44-54)      T7 ch6 (Lv54-64)  T8 postgame legendary (Lv64-70, craft only)
T1-T4 keep the authored numbers. T5..T8 are the line's T4 integer stats x 1.30 / 1.60 / 1.95 / 2.40, which keeps
the weapon at 40-50 % of the wielder's total attack/magic (see --table) so +10 enhancement (+100 % of the piece)
stays meaningful without making level growth irrelevant. Shop tier = guild market tier (TIER_SHOP): the market sells gear tier t
from the zone spec.TIER_UNLOCK_ZONE[t] on (C#: TownServices.ChapterOfFloor); T8 is never sold.
"""
import json
import math
import os
import sys

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
DATA = os.path.join(ROOT, 'Assets', '_Game', 'Resources', 'Data')
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import spec  # noqa: E402

INT_STATS = ('atk', 'mag', 'def', 'res', 'spd', 'hp', 'mp')
# shop_tier = guild market tier (C# TownServices.ChapterOfFloor: one tier per two zones, 7 = the red gate).
# T1-T2 sell from zone 1, T3 zone 3, T4 zone 5, T5 zone 7, T6 zone 9, T7 zone 11; T8 legendaries are never sold.
TIER_SHOP = {1: 1, 2: 1, 3: 2, 4: 3, 5: 4, 6: 5, 7: 6, 8: 0}
TIER_FACTOR = {5: 1.30, 6: 1.60, 7: 1.95, 8: 2.40}
TIER_PRICE = {5: 1.95, 6: 3.3, 7: 5.5}
TIER_LEVEL = {1: 4, 2: 9, 3: 18, 4: 29, 5: 39, 6: 49, 7: 59, 8: 67}

# chapter materials used in recipes (existing + spec NEW_ITEMS)
MAT = {
    4: ('old_bone', 'ghost_essence', 'cursed_straw'),
    5: ('pearl', 'scale_blue', 'temple_stone', 'siren_feather'),
    6: ('void_shard', 'shadow_pelt', 'gargoyle_horn', 'fallen_feather'),
}

LINE_CLASSES = {'sword': ['warrior'], 'staff': ['mage'], 'bow': ['archer'], 'mace': ['cleric'],
                'armor': ['warrior'], 'robe': ['mage', 'cleric'], 'garb': ['archer']}
LINE_SLOT = {'sword': 'weapon', 'staff': 'weapon', 'bow': 'weapon', 'mace': 'weapon', 'armor': 'armor', 'robe': 'armor', 'garb': 'armor'}

# ------------------------------------------------------------------ names (T5-T7 of every line)
NEW_LINE_TEXT = {
    'sword_runic': ('룬 브레이드', '묘소의 대장장이가 푸른 룬을 새겨 넣은 장검. 칼날이 망자의 기척에 반응한다.'),
    'sword_tidal': ('해류의 곡도', '가라앉은 신전의 조류를 닮은 곡도. 칼등에 파도 문양이 빛난다.'),
    'sword_void': ('공허의 검', '심연의 핵에서 벼린 검은 칼날. 갈라진 틈으로 보랏빛이 새어 나온다.'),
    'staff_bone': ('망자의 해골 지팡이', '뿔 달린 해골이 초록 영혼불을 품은 지팡이.'),
    'staff_coral': ('산호 지팡이', '진주를 품은 산호 가지가 바닷물의 마력을 모은다.'),
    'staff_void': ('공허의 지팡이', '두 고리 사이에 공허의 구슬이 떠 있는 검은 지팡이.'),
    'bow_wraith': ('망령의 활', '사슬에 묶인 뼈 활. 시위를 당기면 원혼이 울부짖는다.'),
    'bow_tide': ('조류의 활', '지느러미처럼 펼쳐진 활채가 물살을 가르듯 화살을 보낸다.'),
    'bow_void': ('공허의 활', '가시 돋친 검은 활. 보랏빛 맥동이 화살에 실린다.'),
    'mace_requiem': ('진혼의 종퇴', '해골 추가 달린 쇠종. 울릴 때마다 망자가 잠든다.'),
    'mace_pearl': ('진주 조개 메이스', '열린 가리비 속에 큰 진주가 빛나는 메이스.'),
    'mace_judgment': ('심판의 전쇠', '한쪽은 둔기, 한쪽은 송곳인 흑금 전쇠. 저울의 문장이 새겨져 있다.'),
    'armor_rune': ('룬 판금 갑옷', '룬으로 강화한 판금. 묘소의 저주를 튕겨 낸다.'),
    'armor_tidal': ('해류의 갑주', '신전 수호병의 비늘 갑주. 물결처럼 가볍게 움직인다.'),
    'armor_void': ('공허의 갑주', '심연의 결정으로 덧댄 갑주. 빛을 삼키는 듯 어둡다.'),
    'robe_spirit': ('영혼의 법의', '망자의 영혼을 달래는 주문이 수놓인 법의.'),
    'robe_pearl': ('진주빛 법의', '진주 가루로 물들인 비단 법의. 마력이 잔잔히 흐른다.'),
    'robe_void': ('공허의 법의', '공허의 실로 짠 법의. 입은 이의 마력을 깊게 끌어낸다.'),
    'garb_wraith': ('망령의 경갑', '안개처럼 흐릿한 가죽 경갑. 적의 눈을 속인다.'),
    'garb_tide': ('조류의 경갑', '물고기 비늘을 엮은 경갑. 물속에서도 몸이 가볍다.'),
    'garb_void': ('공허의 경갑', '그림자 짐승의 가죽으로 만든 경갑. 발소리가 사라진다.'),
}

# Tints for armour pieces that reuse an existing display model (icon only; armour has no runtime model).
ARMOR_MODEL = {
    'armor_rune': ('armor_plate', [0.72, 0.84, 1.0, 1.0]), 'armor_tidal': ('armor_dawn', [0.5, 0.95, 0.95, 1.0]),
    'armor_void': ('armor_dawn', [0.6, 0.45, 0.95, 1.0]),
    'robe_spirit': ('robe_sage', [0.7, 1.0, 0.85, 1.0]), 'robe_pearl': ('robe_dawn', [1.0, 0.86, 0.92, 1.0]),
    'robe_void': ('robe_sage', [0.62, 0.48, 0.95, 1.0]),
    'garb_wraith': ('garb_wind', [0.8, 0.85, 1.0, 1.0]), 'garb_tide': ('garb_wind', [0.5, 0.92, 0.98, 1.0]),
    'garb_void': ('garb_dawn', [0.66, 0.5, 1.0, 1.0]),
}

# Small per-tier float bonuses on top of the T4 piece (weapons: crit/hit; light armour: evade).
FLOAT_STEP = {
    'sword': {'crit': 0.01, 'hit': 0.01}, 'bow': {'crit': 0.01, 'hit': 0.01}, 'staff': {}, 'mace': {},
    'armor': {}, 'robe': {}, 'garb': {'evade': 0.01},
}

# Craft recipes for T5-T7 line pieces (cheaper than the shop when you farm the chapter).
LINE_RECIPE = {
    5: lambda i: {MAT[4][i % 3]: 4, MAT[4][(i + 1) % 3]: 2, 'abyss_crystal': 1},
    6: lambda i: {MAT[5][i % 4]: 4, MAT[5][(i + 1) % 4]: 3, 'leviathan_fin': 1},
    7: lambda i: {MAT[6][i % 4]: 4, MAT[6][(i + 1) % 4]: 3, 'lord_crown': 1},
}

# T8 legendary (existing *_dawn / *_star / *_starlight rows) -> postgame recipes.
LEGENDARY_RECIPE = {
    'sword_dawn': {'trial_emblem': 3, 'lord_crown': 1, 'void_shard': 5, 'ember_crystal': 1},
    'staff_starlight': {'trial_emblem': 3, 'lord_crown': 1, 'siren_feather': 5, 'frost_crystal': 1},
    'bow_star': {'trial_emblem': 3, 'lord_crown': 1, 'fallen_feather': 5, 'verdant_crystal': 1},
    'mace_dawn': {'trial_emblem': 3, 'lord_crown': 1, 'pearl': 5, 'abyss_crystal': 1},
    'armor_dawn': {'trial_emblem': 3, 'leviathan_fin': 2, 'gargoyle_horn': 5, 'abyss_crystal': 1},
    'robe_dawn': {'trial_emblem': 3, 'leviathan_fin': 2, 'siren_feather': 5, 'abyss_crystal': 1},
    'garb_dawn': {'trial_emblem': 3, 'leviathan_fin': 2, 'shadow_pelt': 5, 'abyss_crystal': 1},
}

# ------------------------------------------------------------------ job signature weapons
# id: (Korean name, description, line T-factor source tier factor, extra stats, recipe, gold)
ELEMENT = {'none': 0, 'slash': 1, 'blunt': 2, 'pierce': 3, 'fire': 4, 'ice': 5, 'thunder': 6, 'dark': 7, 'holy': 8}
JOB_TEXT = {
    'sword_aegis': ('수호의 검 이지스', '기사 전용. 방패 모양 가드가 달린 넓은 검. 방어력이 크게 오르고 기절하지 않는다.'),
    'sword_ravager': ('파괴의 대검', '광전사 전용. 톱니 등날의 거대한 식칼. 치명타율이 매우 높지만 방어가 허술해진다.'),
    'sword_holy_avenger': ('성검 홀리 어벤저', '성기사 전용. 천사의 날개 가드가 달린 성검. 평타가 성속성이 된다.'),
    'sword_conqueror': ('정복왕의 대검', '워로드 전용. 왕관 가드의 흑금 대검. 전투 시작부터 TP를 품는다.'),
    'staff_prism': ('프리즘 지팡이', '원소술사 전용. 네 원소 결정이 프리즘을 감싼다. 매 턴 MP가 회복된다.'),
    'staff_hex': ('저주의 지팡이', '흑마법사 전용. 저주받은 눈이 박힌 비틀린 지팡이. 평타가 암속성이 되고 침묵하지 않는다.'),
    'staff_arcanum': ('대마도의 지팡이 아르카눔', '대마도사 전용. 세 겹의 궤도 고리가 푸른 구슬을 감싼다. 마력과 MP 회복이 압도적이다.'),
    'staff_abyss_eye': ('심연의 눈', '심연술사 전용. 촉수가 거대한 눈을 감싼 지팡이. 평타가 암속성이 되고 TP를 품고 시작한다.'),
    'bow_longshot': ('장거리 저격궁', '저격수 전용. 조준경이 달린 긴 활. 명중률과 치명타율이 높다.'),
    'bow_thornvine': ('가시덩굴 활', '레인저 전용. 살아 있는 덩굴 활. 속도가 오르고 매 턴 HP가 조금씩 회복된다.'),
    'bow_heavens': ('천공의 활', '신궁 전용. 날개가 된 활채에서 빛의 화살이 쏟아진다. 평타가 성속성이 된다.'),
    'bow_nightfall': ('황혼의 활', '그림자 추적자 전용. 양끝에 칼날이 달린 검은 활. 평타가 암속성이 되고 회피율이 오른다.'),
    'mace_grace': ('은총의 백합 홀', '신관 전용. 금빛 백합이 피어난 홀. 매 턴 MP가 회복된다.'),
    'mace_purifier': ('정화의 철퇴', '퇴마사 전용. 부적을 감은 가시 철퇴. 평타가 성속성이 되고 능력 저하에 걸리지 않는다.'),
    'mace_seraph': ('세라핌의 홀', '성녀 전용. 여섯 날개와 두 겹의 후광. 매 턴 HP와 MP가 회복된다.'),
    'mace_verdict': ('판결의 망치', '심판관 전용. 쇠테를 두른 거대한 의사봉. 평타가 성속성이 되고 치명타율이 높다.'),
}
ADV_JOBS = {'knight', 'berserker', 'elementalist', 'warlock', 'sniper', 'ranger', 'priest', 'exorcist'}
JOB_BASE = {}
for base, kids in spec.JOB_TREE.items():
    for kid in kids:
        JOB_BASE[kid] = base
def root_class(job):
    while job in JOB_BASE:
        job = JOB_BASE[job]
    return job

# extra (on top of the line's scaled stats) and special fields per job weapon
JOB_SPECIAL = {
    'sword_aegis': dict(add={'def': 18, 'res': 10, 'hp': 80}, mul_atk=0.9, immun=['stun']),
    'sword_ravager': dict(add={'def': -12}, mul_atk=1.12, crit=0.15),
    'sword_holy_avenger': dict(add={'res': 14, 'mag': 10}, element='holy', crit=0.04),
    'sword_conqueror': dict(add={'def': 10, 'hp': 120}, crit=0.08, tp_start=25),
    'staff_prism': dict(add={'res': 10}, mp_regen=4, resists=[4, 5, 6]),
    'staff_hex': dict(add={'atk': 10}, element='dark', immun=['silence']),
    'staff_arcanum': dict(add={'mp': 40, 'res': 12}, mp_regen=8),
    'staff_abyss_eye': dict(add={'spd': 6}, element='dark', tp_start=20, resists=[7]),
    'bow_longshot': dict(add={}, hit=0.15, crit=0.12),
    'bow_thornvine': dict(add={'spd': 8}, hp_regen=0.03, immun=['poison', 'poison_strong']),
    'bow_heavens': dict(add={'res': 12}, element='holy', crit=0.1),
    'bow_nightfall': dict(add={'spd': 6}, element='dark', evade=0.08, crit=0.12),
    'mace_grace': dict(add={'res': 10}, mp_regen=4),
    'mace_purifier': dict(add={'atk': 12}, element='holy', immun=['attack_down', 'defense_down']),
    'mace_seraph': dict(add={'res': 16}, hp_regen=0.04, mp_regen=6),
    'mace_verdict': dict(add={'atk': 20}, element='holy', crit=0.1),
}
JOB_RECIPE_ADV = {
    'sword': {'old_bone': 5, 'magma_core': 3, 'ember_crystal': 1}, 'staff': {'ghost_essence': 5, 'jelly_core': 3, 'frost_crystal': 1},
    'bow': {'cursed_straw': 5, 'drake_scale': 3, 'verdant_crystal': 1}, 'mace': {'ghost_essence': 4, 'golem_sandstone': 3, 'ember_crystal': 1},
}
JOB_RECIPE_MASTER = {
    'sword': {'leviathan_fin': 1, 'void_shard': 5, 'gargoyle_horn': 3}, 'staff': {'leviathan_fin': 1, 'void_shard': 5, 'siren_feather': 3},
    'bow': {'leviathan_fin': 1, 'void_shard': 5, 'fallen_feather': 3}, 'mace': {'leviathan_fin': 1, 'void_shard': 5, 'pearl': 3},
}

# ------------------------------------------------------------------ accessories (spec.NEW_ACCESSORIES)
HARMFUL = ['attack_down', 'bleed', 'blind', 'burn', 'defense_down', 'freeze', 'poison', 'poison_strong', 'silence', 'sleep', 'slow', 'stun']
# id: name, description, tier, shop?, stats, extra fields, model, tint, recipe+gold
ACC = [
    ('acc_iron_bangle', '무쇠 팔찌', '두툼한 무쇠 팔찌. 몸을 단단하게 지켜 준다.', 2, True, dict(def_=6, hp=30), {}, 'acc_power_band', (0.78, 0.82, 0.92), None),
    ('acc_mind_ring', '정신의 반지', '마음을 맑게 하는 은반지. 마법 저항과 MP가 오른다.', 2, True, dict(res=8, mp=15), {}, 'acc_guardian_ring', (0.75, 0.82, 1.0), None),
    ('acc_swift_anklet', '바람의 발찌', '발목에 감으면 걸음이 가벼워진다.', 3, True, dict(spd=6, evade=0.02), {}, 'acc_wind_boots', (0.7, 1.0, 0.9), None),
    ('acc_life_pendant', '생명의 펜던트', '심장 소리처럼 고동치는 붉은 펜던트. 최대 HP가 크게 오른다.', 4, True, dict(hp=160), {}, 'acc_flame_amulet', (1.0, 0.62, 0.72), None),
    ('acc_spirit_pendant', '정령의 펜던트', '정령이 깃든 보석. 마력과 MP가 오른다.', 4, True, dict(mag=10, mp=40), {}, 'acc_sage_pendant', (0.82, 0.7, 1.0), None),
    ('acc_thunder_amulet', '뇌전 부적', '번개를 땅으로 흘려보내는 부적. 뇌속성 피해를 줄인다.', 3, True, dict(res=8), dict(element_resists=[6]), 'acc_frost_amulet', (1.0, 0.95, 0.45), ({'jelly_core': 3, 'coral_shard': 2}, 500)),
    ('acc_holy_amulet', '성광 부적', '성스러운 빛을 가두어 둔 부적. 성속성 피해를 줄인다.', 5, True, dict(res=14), dict(element_resists=[8]), 'acc_frost_amulet', (1.0, 0.92, 0.68), ({'ghost_essence': 3, 'old_bone': 3}, 1800)),
    ('acc_dark_amulet', '칠흑의 부적', '어둠을 삼키는 칠흑의 부적. 암속성 피해를 줄이고 마력을 높인다.', 6, True, dict(res=18, mag=10), dict(element_resists=[7]), 'acc_shadow_amulet', (0.72, 0.55, 0.92), ({'scale_blue': 3, 'temple_stone': 3}, 3500)),
    ('acc_earth_amulet', '대지의 부적', '단단한 대지의 힘이 깃든 부적. 타격 피해를 줄인다.', 4, True, dict(def_=10, hp=60), dict(element_resists=[2]), 'acc_flame_amulet', (0.86, 0.72, 0.46), ({'golem_sandstone': 3, 'magma_core': 2}, 1100)),
    ('acc_silence_ward', '침묵막이 귀걸이', '말문이 막히지 않게 지켜 주는 귀걸이.', 3, True, dict(mp=15), dict(status_immunities=['silence']), 'acc_clarity_earring', (0.82, 0.82, 1.0), None),
    ('acc_sleep_ward', '꿈막이 방울', '맑은 소리로 잠과 어둠을 쫓는 방울.', 5, True, dict(res=10, spd=3), dict(status_immunities=['sleep', 'blind']), 'acc_awake_bell', (0.75, 0.75, 1.0), None),
    ('acc_paralyze_ward', '마비막이 반지', '몸이 굳지 않게 지켜 주는 반지. 기절과 둔화를 막는다.', 4, True, dict(def_=6), dict(status_immunities=['stun', 'slow']), 'acc_antidote_ring', (1.0, 0.95, 0.5), None),
    ('acc_curse_ward', '저주막이 부적', '저주를 튕겨 내는 부적. 공격력·방어력 저하를 막는다.', 5, True, dict(res=8), dict(status_immunities=['attack_down', 'defense_down']), 'acc_lucky_charm', (0.8, 0.66, 1.0), None),
    ('acc_burn_ward', '화상막이 반지', '불길을 식혀 주는 반지. 화상을 막는다.', 4, True, dict(res=6), dict(status_immunities=['burn']), 'acc_antidote_ring', (1.0, 0.58, 0.42), ({'magma_core': 2, 'drake_scale': 1}, 700)),
    ('acc_freeze_ward', '빙결막이 반지', '몸을 데워 주는 반지. 빙결을 막는다.', 3, True, dict(res=5), dict(status_immunities=['freeze']), 'acc_antidote_ring', (0.55, 0.85, 1.0), ({'frost_fur': 2, 'jelly_core': 1}, 400)),
    ('acc_berserk_ring', '광전사의 반지', '피가 끓어오르는 붉은 반지. 공격력이 크게 오르지만 방어가 허술해진다.', 5, True, dict(atk=22, def_=-10), {}, 'acc_guardian_ring', (1.0, 0.42, 0.42), None),
    ('acc_sniper_scope', '저격 조준경', '먼 과녁도 또렷하게 보이는 조준경. 명중률과 치명타율이 오른다.', 5, True, dict(hit=0.08, crit=0.12), {}, 'acc_eagle_eye', (0.8, 0.9, 1.0), None),
    ('acc_mana_spring', '마나의 샘', '마르지 않는 샘물이 담긴 펜던트. 매 턴 MP가 6 회복된다.', 5, True, dict(mp=20), dict(mp_regen=6), 'acc_sage_pendant', (0.55, 0.75, 1.0), ({'ghost_essence': 3, 'jelly_core': 3}, 2000)),
    ('acc_regen_ring', '재생의 반지', '생명력이 샘솟는 녹색 반지. 매 턴 최대 HP의 5 %를 회복한다.', 6, True, dict(hp=40), dict(hp_regen=0.05), 'acc_guardian_ring', (0.55, 1.0, 0.6), ({'pearl': 3, 'siren_feather': 2}, 4000)),
    ('acc_counter_charm', '역습의 부적', '공격을 흘려 반격의 틈을 노리게 해 주는 부적. 회피율과 치명타율이 오른다.', 4, True, dict(atk=8, evade=0.05, crit=0.06), {}, 'acc_lucky_charm', (1.0, 0.6, 0.5), None),
    ('acc_tp_crest', '투지의 문장', '전투가 시작되자마자 투지가 차오르는 문장. 전투 시작 시 TP 30.', 6, True, dict(atk=6, mag=6), dict(tp_start=30), 'acc_hero_emblem', (1.0, 0.85, 0.5), ({'gargoyle_horn': 2, 'temple_stone': 3}, 3500)),
    ('acc_gold_charm', '황금 부적', '금화 냄새를 맡는 부적. 전투에서 얻는 골드가 25 % 늘어난다(파티 합산, 최대 +100 %).', 3, True, dict(), dict(gold_bonus=0.25), 'acc_lucky_charm', (1.0, 0.85, 0.35), None),
    ('acc_exp_charm', '성장의 부적', '경험을 두 배로 새기는 부적. 착용자가 얻는 경험치가 30 % 늘어난다.', 3, True, dict(), dict(exp_bonus=0.3), 'acc_lucky_charm', (0.55, 0.85, 1.0), None),
    ('acc_ribbon', '여신의 리본', '여신의 가호가 깃든 리본. 모든 해로운 상태 이상을 막는다.', 8, False, dict(res=12, evade=0.03), dict(status_immunities=HARMFUL), 'acc_awake_bell', (1.0, 0.72, 0.86), ({'trial_emblem': 2, 'siren_feather': 4, 'metal_gel': 1}, 20000)),
    ('acc_crystal_crown', '수정 왕관', '네 봉인의 결정과 군주의 왕관을 녹여 만든 왕관. 모든 능력치가 오른다.', 8, False, dict(atk=18, mag=18, def_=16, res=16, spd=6, hp=120, mp=40), {}, 'acc_hero_emblem', (0.75, 0.9, 1.0), ({'lord_crown': 1, 'verdant_crystal': 1, 'frost_crystal': 1, 'ember_crystal': 1, 'abyss_crystal': 1}, 25000)),
    ('acc_dragon_fang', '해룡의 송곳니', '레비아탄의 송곳니. 쥐면 공격 본능이 깨어나고 전투 시작 시 TP 15를 얻는다.', 6, False, dict(atk=32, crit=0.1), dict(tp_start=15), 'acc_flame_amulet', (1.0, 0.92, 0.78), None),
    ('acc_kraken_eye', '크라켄의 눈', '빙해의 여왕의 눈. 냉기를 막고 매 턴 MP가 3 회복된다.', 3, False, dict(mag=14, res=10), dict(element_resists=[5], mp_regen=3), 'acc_shadow_amulet', (0.5, 0.9, 1.0), None),
    ('acc_sphinx_riddle', '스핑크스의 수수께끼', '불꽃 스핑크스가 남긴 수수께끼 석판. 지혜와 민첩이 오르고 침묵·수면을 막는다.', 4, False, dict(mag=16, spd=6, hit=0.05), dict(status_immunities=['silence', 'sleep']), 'acc_hero_emblem', (1.0, 0.76, 0.46), None),
    ('acc_lich_phylactery', '리치의 성물함', '망령술사의 영혼이 잠든 성물함. 어둠을 막고 매 턴 MP가 5 회복된다.', 5, False, dict(mag=24, mp=40), dict(element_resists=[7], mp_regen=5), 'acc_clarity_earring', (0.6, 1.0, 0.75), None),
    ('acc_abyss_heart', '심연의 심장', '심연의 군주가 남긴 고동치는 심장. 모든 능력치가 오르고 매 턴 HP가 회복된다.', 8, False, dict(atk=20, mag=20, def_=20, res=20, spd=8, hp=150), dict(hp_regen=0.03, tp_start=20), 'acc_flame_amulet', (0.66, 0.36, 0.95), None),
]
ACC_PRICE = {2: 600, 3: 1500, 4: 3000, 5: 5200, 6: 8500, 7: 13000, 8: 0}
EXISTING_ACC_TIER = {'acc_antidote_ring': 1, 'acc_lucky_charm': 1, 'acc_awake_bell': 3, 'acc_power_band': 3, 'acc_sage_pendant': 3,
                     'acc_frost_amulet': 3, 'acc_eagle_eye': 4, 'acc_flame_amulet': 4, 'acc_wind_boots': 4, 'acc_guardian_ring': 4,
                     'acc_clarity_earring': 5, 'acc_shadow_amulet': 5, 'acc_hero_emblem': 5}

# ------------------------------------------------------------------ items (spec.NEW_ITEMS)
# id: (name, description, type, target, fields, price, shop tier, rarity, max stack)
HEALING, MP, CURE, REVIVE, ESCAPE, FLEE, DAMAGE, MATERIAL, BUFF, SEED, KEY = range(11)
ITEMS = [
    ('x_potion', '엑스 포션', '아군 한 명의 HP를 2000 회복합니다.', HEALING, 'single_ally', dict(heal_amount=2000, value=2000), 1100, 5, 1, 9),
    ('max_ether', '맥스 에테르', '아군 한 명의 MP를 모두 회복합니다.', MP, 'single_ally', dict(value=999), 1600, 5, 1, 9),
    ('megalixir', '메가엘릭서', '아군 전원의 HP와 MP를 모두 회복합니다.', HEALING, 'all_allies', dict(heal_amount=9999, value=9999, mp_amount=999), 12000, 7, 3, 9),
    ('panacea', '만병통치약', '아군 전원의 해로운 상태 이상을 모두 치료합니다.', CURE, 'all_allies', dict(), 700, 4, 1, 9),
    ('phoenix_plume', '불사조의 꼬리깃', '쓰러진 아군 한 명을 HP 100 %로 되살립니다.', REVIVE, 'single_ally', dict(power=1.0), 2000, 5, 2, 9),
    ('fire_bomb', '화염 폭탄', '적 전체에 400의 화속성 고정 피해를 줍니다.', DAMAGE, 'all_enemies', dict(value=400, element=4), 650, 3, 0, 9),
    ('ice_bomb', '빙결 폭탄', '적 전체에 400의 빙속성 고정 피해를 줍니다.', DAMAGE, 'all_enemies', dict(value=400, element=5), 650, 3, 0, 9),
    ('thunder_bomb', '뇌전 폭탄', '적 전체에 400의 뇌속성 고정 피해를 줍니다.', DAMAGE, 'all_enemies', dict(value=400, element=6), 650, 3, 0, 9),
    ('holy_water', '성수', '적 전체에 650의 성속성 고정 피해를 줍니다. 망자에게 특히 잘 듣습니다.', DAMAGE, 'all_enemies', dict(value=650, element=8), 900, 4, 1, 9),
    ('magic_tonic', '마력의 영약', '아군 전원의 마력을 3턴 동안 높입니다.', BUFF, 'all_allies', dict(status_id='magic_up'), 450, 3, 0, 9),
    ('speed_tonic', '신속의 영약', '아군 전원의 속도를 3턴 동안 높입니다.', BUFF, 'all_allies', dict(status_id='speed_up'), 450, 3, 0, 9),
    ('camp_tent', '야영 텐트', '전투 밖에서만 사용. 아군 전원의 HP와 MP를 모두 회복합니다(쓰러진 동료 제외).', HEALING, 'all_allies', dict(heal_amount=9999, value=9999, mp_amount=999, field_only=True), 1500, 3, 1, 9),
    ('seed_power', '힘의 씨앗', '먹은 동료의 공격력이 영구히 2 오릅니다.', SEED, 'single_ally', dict(stat='attack', value=2), 0, 0, 2, 99),
    ('seed_magic', '지혜의 씨앗', '먹은 동료의 마력이 영구히 2 오릅니다.', SEED, 'single_ally', dict(stat='magic', value=2), 0, 0, 2, 99),
    ('seed_guard', '수호의 씨앗', '먹은 동료의 방어력이 영구히 2 오릅니다.', SEED, 'single_ally', dict(stat='defense', value=2), 0, 0, 2, 99),
    ('seed_mind', '정신의 씨앗', '먹은 동료의 마법 저항이 영구히 2 오릅니다.', SEED, 'single_ally', dict(stat='resistance', value=2), 0, 0, 2, 99),
    ('seed_swift', '신속의 씨앗', '먹은 동료의 속도가 영구히 1 오릅니다.', SEED, 'single_ally', dict(stat='speed', value=1), 0, 0, 2, 99),
    ('seed_life', '생명의 씨앗', '먹은 동료의 최대 HP가 영구히 20 오릅니다.', SEED, 'single_ally', dict(stat='max_hp', value=20), 0, 0, 2, 99),
    ('job_medal', '전직의 증표', '길드가 인정한 모험가에게 주는 증표. 1차 전직에 필요합니다. 팔 수 없습니다.', KEY, 'none', dict(), 2500, 2, 2, 9),
    ('master_seal', '마스터의 인장', '한 길을 끝까지 걸은 자의 인장. 2차 전직에 필요합니다. 팔 수 없습니다.', KEY, 'none', dict(), 12000, 4, 3, 9),
    ('enhance_stone', '강화석', '대장간에서 장비를 강화하는 돌. T1-T3 장비에 씁니다.', MATERIAL, 'none', dict(), 80, 1, 0, 99),
    ('enhance_stone_hi', '상급 강화석', '마력이 깃든 강화석. T4-T5 장비에 씁니다.', MATERIAL, 'none', dict(), 450, 3, 1, 99),
    ('enhance_stone_abyss', '심연 강화석', '심연의 힘이 응축된 강화석. T6-T8 장비에 씁니다.', MATERIAL, 'none', dict(), 1600, 5, 2, 99),
    ('pearl', '심해 진주', '가라앉은 신전의 조개가 품은 진주.', MATERIAL, 'none', dict(), 0, 0, 0, 99),
    ('scale_blue', '푸른 비늘', '어인과 바다뱀의 단단한 푸른 비늘.', MATERIAL, 'none', dict(), 0, 0, 0, 99),
    ('temple_stone', '신전 석재', '물이끼 낀 신전의 석재. 희미한 문양이 빛난다.', MATERIAL, 'none', dict(), 0, 0, 0, 99),
    ('siren_feather', '세이렌의 깃털', '노랫소리가 깃든 푸른 깃털.', MATERIAL, 'none', dict(), 0, 0, 0, 99),
    ('leviathan_fin', '레비아탄의 지느러미', '바다의 왕이 남긴 빛나는 지느러미.', MATERIAL, 'none', dict(), 0, 0, 1, 99),
    ('void_shard', '공허의 파편', '심연의 핵에서 떨어져 나온 보랏빛 결정.', MATERIAL, 'none', dict(), 0, 0, 0, 99),
    ('shadow_pelt', '그림자 털가죽', '연기처럼 일렁이는 그림자 짐승의 가죽.', MATERIAL, 'none', dict(), 0, 0, 0, 99),
    ('gargoyle_horn', '가고일의 뿔', '돌처럼 단단한 가고일의 뿔.', MATERIAL, 'none', dict(), 0, 0, 0, 99),
    ('fallen_feather', '타락한 깃털', '타락 천사의 검은 깃털. 금빛 고리가 남아 있다.', MATERIAL, 'none', dict(), 0, 0, 1, 99),
    ('lord_crown', '군주의 왕관', '심연의 군주가 쓰던 뿔 왕관의 조각.', MATERIAL, 'none', dict(), 0, 0, 2, 99),
    ('trial_emblem', '시련의 문장', '시련의 회랑에서 진 보스를 쓰러뜨린 증거.', MATERIAL, 'none', dict(), 0, 0, 2, 99),
    ('metal_gel', '메탈 젤', '메탈 슬라임이 남긴 은빛 젤. 아주 귀하다.', MATERIAL, 'none', dict(), 0, 0, 1, 99),
]
SELL = {'pearl': 150, 'scale_blue': 160, 'temple_stone': 180, 'siren_feather': 220, 'leviathan_fin': 1500, 'void_shard': 250,
        'shadow_pelt': 260, 'gargoyle_horn': 280, 'fallen_feather': 400, 'lord_crown': 3000, 'trial_emblem': 800, 'metal_gel': 500,
        'seed_power': 500, 'seed_magic': 500, 'seed_guard': 500, 'seed_mind': 500, 'seed_swift': 500, 'seed_life': 500,
        'job_medal': 0, 'master_seal': 0}


def load(name):
    with open(os.path.join(DATA, name + '.json'), encoding='utf-8') as f:
        return json.load(f)


def save(name, rows):
    rows = sorted(rows, key=lambda r: r['id'])
    text = json.dumps(rows, ensure_ascii=False, indent=1).replace('\n', '\r\n') + '\r\n'
    with open(os.path.join(DATA, name + '.json'), 'wb') as f:
        f.write(text.encode('utf-8'))


def r2(x):
    return round(x + 1e-9, 2)


def equip_row(ident, name, desc, slot, classes, stats, price, shop, rarity, tier, recipe=None, craft_gold=0, sell=-1, extra=None):
    row = {'id': ident, 'display_name': name, 'description': desc, 'slot': slot, 'classes': classes}
    for k in INT_STATS:
        row[k] = int(stats.get(k, 0))
    for k in ('hit', 'evade', 'crit'):
        row[k] = float(r2(stats.get(k, 0.0)))
    row['element_resists'] = list(stats.get('element_resists', []))
    row['status_immunities'] = list(stats.get('status_immunities', []))
    row['price'] = price
    row['sell_price'] = sell
    row['shop_tier'] = shop
    row['craft_materials'] = dict(recipe or {})
    row['craft_gold'] = craft_gold
    row['_file'] = ident
    row['rarity'] = rarity
    row['tier'] = tier
    row['jobs'] = []
    for k, v in (extra or {}).items():
        row[k] = v
    return row


def build_equipment():
    rows = {r['id']: r for r in load('equipment')}
    # 1. existing rows: tier + jobs on every row; T8 legendaries re-tuned for the postgame.
    tier_of = {}
    for line, ids in spec.GEAR_LINES.items():
        for t, ident in enumerate(ids, 1):
            tier_of[ident] = t
    tier_of.update(EXISTING_ACC_TIER)
    for ident, row in rows.items():
        row.setdefault('tier', tier_of.get(ident, 0))
        row['tier'] = tier_of.get(ident, row['tier'])
        row.setdefault('jobs', [])
    for line, ids in spec.GEAR_LINES.items():
        t4 = rows[ids[3]]
        # T8 (existing legendary): scale integer stats from the line's T4 piece, keep its own float flavour.
        legend = rows[ids[7]]
        for k in INT_STATS:
            legend[k] = max(legend[k], int(round(t4[k] * TIER_FACTOR[8])))
        for k in ('hit', 'evade', 'crit'):
            legend[k] = float(r2(max(legend[k], t4[k] + 0.02 if t4[k] > 0 else legend[k])))
        legend['craft_materials'] = dict(LEGENDARY_RECIPE[ids[7]])
        legend['craft_gold'] = 30000 if LINE_SLOT[line] == 'weapon' else 26000
        legend['sell_price'] = 7500
        legend['tier'] = 8
        # T5-T7: new rows from the T4 piece.
        for t in (5, 6, 7):
            ident = ids[t - 1]
            name, desc = NEW_LINE_TEXT[ident]
            stats = {k: int(round(t4[k] * TIER_FACTOR[t])) for k in INT_STATS}
            for k in ('hit', 'evade', 'crit'):
                step = FLOAT_STEP[line].get(k, 0.0)
                stats[k] = t4[k] + step * (t - 4) if t4[k] > 0 or step > 0 else 0.0
            price = int(round(t4['price'] * TIER_PRICE[t] / 50.0)) * 50
            recipe = LINE_RECIPE[t](list(spec.GEAR_LINES).index(line))
            extra = {}
            if ident in ARMOR_MODEL:
                extra = {'model': ARMOR_MODEL[ident][0], 'tint': ARMOR_MODEL[ident][1]}
            rows[ident] = equip_row(ident, name, desc, LINE_SLOT[line], list(LINE_CLASSES[line]), stats, price, TIER_SHOP[t], 2, t,
                                    recipe, int(round(price * 0.45 / 50.0)) * 50, extra=extra)
    # 2. job signature weapons
    for job, ident in spec.JOB_WEAPONS.items():
        line = ident.split('_')[0]
        t4 = rows[spec.GEAR_LINES[line][3]]
        advanced = job in ADV_JOBS
        factor = TIER_FACTOR[5] * 1.08 if advanced else 2.3
        sp = JOB_SPECIAL[ident]
        stats = {k: int(round(t4[k] * factor)) for k in INT_STATS}
        main = 'mag' if line == 'staff' else ('atk' if line in ('sword', 'bow') else None)
        if main and 'mul_atk' in sp:
            stats[main] = int(round(stats[main] * sp['mul_atk']))
        for k, v in sp['add'].items():
            stats[k] = stats.get(k, 0) + (v if advanced else int(round(v * 1.6)))
        for k in ('hit', 'evade', 'crit'):
            stats[k] = t4[k] + sp.get(k, 0.0) * (1.0 if advanced else 1.3)
        stats['element_resists'] = sp.get('resists', [])
        stats['status_immunities'] = sp.get('immun', [])
        extra = {}
        if 'element' in sp:
            extra['element'] = ELEMENT[sp['element']]
        for k in ('hp_regen', 'mp_regen', 'tp_start'):
            if k in sp:
                v = sp[k] if advanced else (sp[k] * 1.5 if k != 'tp_start' else sp[k] + 10)
                extra[k] = float(r2(v)) if k == 'hp_regen' else int(round(v))
        recipe = (JOB_RECIPE_ADV if advanced else JOB_RECIPE_MASTER)[line]
        name, desc = JOB_TEXT[ident]
        row = equip_row(ident, name, desc, 'weapon', [root_class(job)], stats, 0, 0, 2 if advanced else 3, 5 if advanced else 8,
                        recipe, 6000 if advanced else 24000, sell=2500 if advanced else 6000, extra=extra)
        row['jobs'] = [job]
        rows[ident] = row
    # 3. accessories
    for (ident, name, desc, tier, sold, st, fields, model, tint, craft) in ACC:
        stats = {('def' if k == 'def_' else k): v for k, v in st.items()}
        stats['element_resists'] = fields.get('element_resists', [])
        stats['status_immunities'] = fields.get('status_immunities', [])
        extra = {k: v for k, v in fields.items() if k not in ('element_resists', 'status_immunities')}
        extra['model'] = model
        extra['tint'] = [tint[0], tint[1], tint[2], 1.0]
        boss = ident in ('acc_dragon_fang', 'acc_kraken_eye', 'acc_sphinx_riddle', 'acc_lich_phylactery', 'acc_abyss_heart')
        price = ACC_PRICE[tier] if sold else 0
        rarity = 3 if boss or tier == 8 else (2 if tier >= 4 else 1)
        rows[ident] = equip_row(ident, name, desc, 'accessory', [], stats, price, TIER_SHOP[min(tier, 7)] if sold else 0, rarity, tier,
                                craft[0] if craft else None, craft[1] if craft else 0, sell=-1 if sold else (2500 if not craft else 5000), extra=extra)
    return list(rows.values())


def build_items():
    rows = {r['id']: r for r in load('items')}
    for (ident, name, desc, kind, target, fields, price, shop, rarity, stack) in ITEMS:
        row = {'id': ident, 'display_name': name, 'description': desc, 'item_type': kind,
               'heal_amount': fields.get('heal_amount', 0), 'max_stack': stack, 'power': float(fields.get('power', 0.0)),
               'value': fields.get('value', 0), 'target': target, 'price': price,
               'sell_price': SELL.get(ident, price // 2), 'shop_tier': shop, 'status_id': fields.get('status_id', ''),
               'element': fields.get('element', 0), '_file': ident, 'rarity': rarity}
        for k in ('mp_amount', 'stat', 'field_only'):
            if k in fields:
                row[k] = fields[k]
        rows[ident] = row
    return list(rows.values())


def hero_table(equipment):
    heroes = load('heroes')
    by_id = {r['id']: r for r in equipment}
    main = {'warrior': ('attack', 'atk', 'sword'), 'archer': ('attack', 'atk', 'bow'), 'mage': ('magic', 'mag', 'staff'), 'cleric': ('magic', 'mag', 'mace')}
    growth = {'attack': 'atk_growth', 'magic': 'mag_growth'}
    print('tier level ' + ' '.join(f'{h["id"]:>22}' for h in heroes))
    for t in range(1, 9):
        level = TIER_LEVEL[t]
        cells = []
        for h in heroes:
            stat, key, line = main[h['id']]
            base = round(h[stat] + h[growth[stat]] * (level - 1))
            w = by_id[spec.GEAR_LINES[line][t - 1]][key]
            cells.append(f'{base:4d}+{w:3d} ({w * 100 // (base + w):2d}%) +10:{w * 2:3d}')
        print(f'T{t}  Lv{level:2d} ' + ' '.join(f'{c:>22}' for c in cells))


def main():
    equipment = build_equipment()
    items = build_items()
    save('equipment', equipment)
    save('items', items)
    print(f'equipment {len(equipment)}  items {len(items)}')
    if '--table' in sys.argv:
        hero_table(equipment)


if __name__ == '__main__':
    main()
