"""Job (class change) data generator: writes Resources/Data/jobs.json and adds the job skills, their presentations,
the two class-change items and the job UI text. IDs and names come from Tools/content/spec.py.

Run from the repository root:  python3 Tools/content/jobs.py
Safe to re-run: rows it owns (jb_* / ult_jb_* skills, pr_jb_* presentations, job_* text) are replaced in place.

Rules (also documented in docs/CONTENT_20H_PLAN.md and PartyStats):
- Stats: the hero's level stats (base + growth) are multiplied per stat by the job's *_mult, then equipment is added.
  hit/evade/crit add flat to the hero's rates.
- Skills: a hero uses its own learnset plus the learnset of every job on its path (base -> advanced -> master) whose
  level is <= the hero level. Job changes only move forward on the tree, so nothing learned is ever lost, and a
  hero who changes job late learns every job skill up to its level at once. Learnset levels are hero levels.
"""
import json
import os
import sys

ROOT = os.path.normpath(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..'))
DATA = os.path.join(ROOT, 'Assets', '_Game', 'Resources', 'Data')
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from spec import JOB_TREE, JOB_NAMES_KO, JOB_WEAPONS  # noqa: E402

BASES = ('warrior', 'mage', 'archer', 'cleric')
PARENT = {child: parent for parent, children in JOB_TREE.items() for child in children}


def base_of(job):
    while job in PARENT:
        job = PARENT[job]
    return job


def tier_of(job):
    t = 1
    while job in PARENT:
        job = PARENT[job]
        t += 1
    return t


# ------------------------------------------------------------------ stats
# hp, mp, atk, mag, def, res, spd multipliers; hit, evade, crit flat bonuses.
STATS = {
    'knight':         (1.15, 1.00, 1.00, 1.00, 1.25, 1.10, 0.95, 0.00, 0.00, 0.00),
    'berserker':      (1.10, 0.90, 1.25, 0.90, 0.85, 0.90, 1.05, 0.00, 0.00, 0.05),
    'paladin':        (1.30, 1.10, 1.10, 1.10, 1.40, 1.25, 1.00, 0.00, 0.00, 0.00),
    'warlord':        (1.25, 1.00, 1.45, 0.95, 1.00, 1.00, 1.10, 0.00, 0.00, 0.08),
    'elementalist':   (1.00, 1.15, 1.00, 1.20, 1.00, 1.10, 1.00, 0.00, 0.00, 0.00),
    'warlock':        (1.05, 1.10, 1.00, 1.15, 1.00, 1.15, 1.05, 0.00, 0.00, 0.00),
    'archmage':       (1.10, 1.30, 1.00, 1.40, 1.05, 1.25, 1.05, 0.00, 0.00, 0.00),
    'abyssal':        (1.15, 1.20, 1.05, 1.35, 1.10, 1.30, 1.10, 0.00, 0.00, 0.00),
    'sniper':         (1.00, 1.00, 1.20, 1.00, 0.95, 1.00, 1.00, 0.03, 0.00, 0.10),
    'ranger':         (1.05, 1.00, 1.10, 1.00, 1.00, 1.00, 1.20, 0.00, 0.05, 0.00),
    'divine_archer':  (1.15, 1.10, 1.40, 1.10, 1.05, 1.10, 1.10, 0.03, 0.00, 0.15),
    'shadow_stalker': (1.15, 1.05, 1.30, 1.00, 1.05, 1.05, 1.35, 0.00, 0.08, 0.08),
    'priest':         (1.05, 1.20, 1.00, 1.15, 1.00, 1.15, 1.00, 0.00, 0.00, 0.00),
    'exorcist':       (1.05, 1.05, 1.10, 1.20, 1.05, 1.10, 1.00, 0.00, 0.00, 0.02),
    'saint':          (1.20, 1.40, 1.00, 1.35, 1.10, 1.35, 1.05, 0.00, 0.00, 0.00),
    'inquisitor':     (1.20, 1.15, 1.20, 1.40, 1.15, 1.20, 1.05, 0.00, 0.00, 0.05),
}

DESCRIPTIONS = {
    'warrior': '검과 방패로 앞에 서는 기본 직업입니다. 균형 잡힌 공격과 방어를 갖췄습니다.',
    'knight': '동료를 지키는 방패의 기사입니다. 체력과 방어가 크게 오르고, 적의 공격을 끌어모으는 기술을 익힙니다.',
    'paladin': '성스러운 검을 든 수호자입니다. 기사의 단단함에 신성한 공격과 아군 전체를 지키는 결계를 더합니다.',
    'berserker': '방어를 버리고 공격에 모든 것을 거는 전사입니다. 공격과 치명타가 오르고 방어는 떨어집니다.',
    'warlord': '전장을 지배하는 패왕입니다. 압도적인 공격력으로 적 전체를 무너뜨리고 아군의 사기를 높입니다.',
    'mage': '원소 마법을 다루는 기본 직업입니다.',
    'elementalist': '불, 얼음, 번개의 정령을 부리는 술사입니다. 마력과 MP가 오르고 상태 이상을 거는 원소 마법을 익힙니다.',
    'archmage': '모든 마법의 정점에 선 대마도사입니다. 마력이 크게 오르고 적 전체를 휩쓰는 대마법을 씁니다.',
    'warlock': '저주와 어둠을 다루는 마법사입니다. 적을 약하게 만들고 생명력을 빼앗는 주문을 익힙니다.',
    'abyssal': '심연의 힘을 빌린 술사입니다. 공허의 마법으로 적 전체를 잠식하고 저주를 퍼뜨립니다.',
    'archer': '활과 화살로 싸우는 기본 직업입니다.',
    'sniper': '한 발에 모든 것을 거는 저격수입니다. 명중과 치명타가 오르고 방어를 꿰뚫는 사격을 익힙니다.',
    'divine_archer': '하늘의 화살을 쏘는 신궁입니다. 신성한 화살비로 적 전체를 꿰뚫습니다.',
    'ranger': '숲을 누비는 날렵한 사냥꾼입니다. 속도와 회피가 오르고 여러 번 쏘는 연사 기술을 익힙니다.',
    'shadow_stalker': '그림자에 숨어 사냥하는 추적자입니다. 압도적인 속도로 어둠의 연격을 퍼붓습니다.',
    'cleric': '치유와 신성 마법을 다루는 기본 직업입니다.',
    'priest': '치유에 정통한 신관입니다. MP와 마력이 오르고 회복과 보호 기술이 늘어납니다.',
    'saint': '기적을 일으키는 성녀입니다. 쓰러진 동료를 한꺼번에 일으키고 파티 전체를 지킵니다.',
    'exorcist': '악을 몰아내는 퇴마사입니다. 마력이 오르고 신성 속성 공격 마법을 익힙니다.',
    'inquisitor': '악을 심판하는 심판관입니다. 강력한 신성 공격과 적을 무력하게 만드는 심문 기술을 씁니다.',
}

# ------------------------------------------------------------------ skills
# (level, id, name, description, kind, scaling, target, scope, element, power, hits, mp, crit, def_ignore, tier,
#  status, chance, extra_statuses, drain, bonus_vs_status, bonus_mult, presentation)
# kind 0 damage 1 heal 2 buff 3 debuff 4 revive 5 cleanse | scaling 0 atk 1 mag | target 0 enemy 1 ally 2 self
# scope 0 single 1 all 2 random | element 0 none 1 slash 2 blunt 3 pierce 4 fire 5 ice 6 thunder 7 dark 8 holy
# Ultimates (tp 100, mp 0) have ids ult_jb_<job> and use the pr_jb_<job> presentation with the job_<job> effect.
def S(level, sid, name, desc, kind, sc, tt, scope, el, power=0.0, hits=1, mp=0, crit=0.0, dign=0.0, tier=2,
      status=None, chance=0.0, extra=(), drain=0.0, bvs='', bvsm=1.0, pres=None):
    return dict(level=level, id=sid, name=name, desc=desc, kind=kind, sc=sc, tt=tt, scope=scope, el=el, power=power,
                hits=hits, mp=mp, crit=crit, dign=dign, tier=tier, status=status, chance=chance, extra=list(extra),
                drain=drain, bvs=bvs, bvsm=bvsm, pres=pres)


def ULT(level, job, name, desc, kind, sc, tt, scope, el, power, hits=1, crit=0.0, dign=0.0, status=None, chance=0.0,
        extra=(), drain=0.0, bvs='', bvsm=1.0):
    return S(level, 'ult_jb_' + job, '[오의] ' + name, desc, kind, sc, tt, scope, el, power, hits, 0, crit, dign, 3,
             status, chance, extra, drain, bvs, bvsm, 'pr_jb_' + job)


LEARNSETS = {
    'knight': [
        S(15, 'jb_kn_shield_bash', '실드 배시', '방패로 적 하나를 강타합니다. 확률로 기절시킵니다.', 0, 0, 0, 0, 2, 1.45, mp=6, status='stun', chance=0.35, pres='stunning_slam'),
        S(17, 'jb_kn_vow', '수호의 맹세', '적의 공격을 자신에게 끌어모으고 방어를 크게 높입니다.', 2, 0, 2, 0, 0, mp=8, status='provoke', chance=1.0, extra=['defense_up_l'], pres='pr_w_provoke'),
        S(20, 'jb_kn_guard_aura', '가드 오라', '기사의 기운으로 아군 전체의 방어를 높입니다.', 2, 1, 1, 1, 0, mp=14, status='defense_up', chance=1.0, pres='pr_c_protect_all'),
        S(23, 'jb_kn_lance_charge', '랜스 차지', '창처럼 돌진해 적 하나를 꿰뚫습니다. 방어를 30% 무시합니다.', 0, 0, 0, 0, 3, 2.0, mp=12, dign=0.3, pres='pr_jb_lance'),
        ULT(25, 'knight', '창천의 방패검', '푸른 방벽의 문장을 펼친 뒤 방패째 내리베어 적 하나에게 큰 피해를 주고 기절시킬 수 있습니다.', 0, 0, 0, 0, 1, 3.6, crit=0.2, dign=0.4, status='stun', chance=0.5),
        S(26, 'jb_kn_fortress', '불굴의 요새', '자신에게 보호막을 두르고 방어를 크게 높입니다.', 2, 0, 2, 0, 0, mp=16, status='barrier', chance=1.0, extra=['defense_up_l'], pres='pr_w_aegis'),
        S(29, 'jb_kn_rampart_crash', '성벽 붕괴', '방패로 땅을 내리쳐 적 전체에 피해를 주고 방어를 낮춥니다.', 0, 0, 0, 1, 2, 1.1, mp=20, status='defense_down', chance=0.45, pres='pr_blunt_all'),
    ],
    'paladin': [
        ULT(40, 'paladin', '성검 강림', '하늘에서 성검을 내려 적 전체를 두 번 베어 냅니다. 방어를 일부 무시합니다.', 0, 0, 0, 1, 8, 1.5, hits=2, crit=0.1, dign=0.3),
        S(44, 'jb_pa_holy_smite', '홀리 스마이트', '성스러운 빛을 실은 일격으로 적 하나를 벱니다.', 0, 0, 0, 0, 8, 2.4, mp=16, crit=0.1, tier=3, pres='pr_w_blade_holy'),
        S(48, 'jb_pa_sanctuary_guard', '수호의 성역', '성역을 펼쳐 아군 전체에 보호막을 두르고 방어를 높입니다.', 2, 1, 1, 1, 0, mp=26, status='barrier', chance=1.0, extra=['defense_up'], tier=3, pres='pr_c_sanctuary'),
        S(52, 'jb_pa_judgment_blade', '심판의 검', '빛의 칼날로 적 전체를 벱니다.', 0, 0, 0, 1, 8, 1.35, mp=28, tier=3, pres='pr_w_grand_cross'),
        S(56, 'jb_pa_divine_ward', '신성 결계', '아군 전체의 방어를 크게 높이고 재생을 부여합니다.', 2, 1, 1, 1, 0, mp=30, status='defense_up_l', chance=1.0, extra=['regen'], tier=3, pres='pr_w_aegis'),
    ],
    'berserker': [
        S(15, 'jb_be_reckless', '무모한 일격', '방어를 잊고 휘두르는 일격. 치명타가 잘 터집니다.', 0, 0, 0, 0, 1, 2.2, mp=8, crit=0.15, pres='strong_attack'),
        S(17, 'jb_be_frenzy', '광란', '피가 끓어올라 공격이 크게 오르고 빨라집니다.', 2, 0, 2, 0, 0, mp=10, status='attack_up_berserk', chance=1.0, extra=['speed_up'], pres='pr_w_berserk'),
        S(20, 'jb_be_rend', '찢어발기기', '적 하나를 세 번 베어 출혈시킵니다.', 0, 0, 0, 0, 1, 0.7, hits=3, mp=10, status='bleed', chance=0.5, pres='pr_w_combo'),
        S(23, 'jb_be_blood_thirst', '피의 갈증', '적을 베고 준 피해의 35%만큼 회복합니다.', 0, 0, 0, 0, 1, 1.6, mp=12, drain=0.35, pres='pr_slash_bleed'),
        ULT(25, 'berserker', '광혈난무', '붉은 광기에 몸을 맡겨 적 하나를 여섯 번 할퀴듯 벱니다. 출혈 중인 적에게 더 아픕니다.', 0, 0, 0, 0, 1, 0.9, hits=6, crit=0.2, bvs='bleed', bvsm=1.3),
        S(26, 'jb_be_rampage', '폭주', '무작위 적에게 네 번 달려듭니다.', 0, 0, 0, 2, 1, 0.8, hits=4, mp=16, pres='pr_w_whirlwind'),
        S(29, 'jb_be_skull_split', '두개골 쪼개기', '혼신의 내려찍기. 방어를 40% 무시하고 확률로 기절시킵니다.', 0, 0, 0, 0, 2, 2.6, mp=20, dign=0.4, status='stun', chance=0.25, pres='pr_w_armor_break'),
    ],
    'warlord': [
        ULT(40, 'warlord', '패왕진격', '전장을 가르는 두 번의 충격파로 적 전체를 짓밟고 방어를 낮춥니다.', 0, 0, 0, 1, 2, 1.8, hits=2, crit=0.1, dign=0.3, status='defense_down', chance=0.5),
        S(44, 'jb_wl_war_banner', '전군 돌격', '군기를 높이 들어 아군 전체의 공격과 속도를 높입니다.', 2, 0, 1, 1, 0, mp=24, status='attack_up', chance=1.0, extra=['speed_up'], tier=3, pres='pr_w_war_cry'),
        S(48, 'jb_wl_conquer', '정복의 일격', '적 하나를 무너뜨리는 일격. 방어를 30% 무시합니다.', 0, 0, 0, 0, 1, 3.0, mp=26, crit=0.2, dign=0.3, tier=3, pres='pr_w_crimson'),
        S(52, 'jb_wl_earthshaker', '대지 진동', '땅을 뒤흔들어 적 전체에 피해를 주고 기절시킬 수 있습니다.', 0, 0, 0, 1, 2, 1.5, mp=30, status='stun', chance=0.25, tier=3, pres='pr_w_cataclysm'),
        S(56, 'jb_wl_overlord', '패왕의 위압', '압도적인 기세로 적 전체의 공격과 방어를 낮춥니다.', 3, 0, 0, 1, 0, mp=28, status='attack_down', chance=0.7, extra=['defense_down'], tier=3, pres='pr_jb_overlord'),
    ],
    'elementalist': [
        S(15, 'jb_el_fire_spirit', '화염 정령', '불의 정령을 불러 적 하나를 태웁니다.', 0, 1, 0, 0, 4, 1.9, mp=10, status='burn', chance=0.4, pres='pr_m_blaze'),
        S(17, 'jb_el_frost_spirit', '냉기 정령', '얼음 정령이 적 하나를 얼어붙게 합니다.', 0, 1, 0, 0, 5, 1.9, mp=10, status='freeze', chance=0.3, pres='pr_m_glacier'),
        S(20, 'jb_el_storm_spirit', '뇌전 정령', '번개 정령이 적 하나를 꿰뚫고 기절시킬 수 있습니다.', 0, 1, 0, 0, 6, 1.9, mp=10, status='stun', chance=0.3, pres='pr_m_lightning'),
        S(23, 'jb_el_resonance', '원소 공명', '정령과 마음을 맞춰 마력과 속도를 높입니다.', 2, 1, 2, 0, 0, mp=8, status='magic_up', chance=1.0, extra=['speed_up'], pres='pr_m_focus'),
        ULT(25, 'elementalist', '원소 합일', '불과 얼음의 정령이 마법진 위에서 하나로 합쳐져 적 전체를 세 번 강타합니다.', 0, 1, 0, 1, 0, 1.25, hits=3, status='burn', chance=0.4, extra=['slow']),
        S(26, 'jb_el_tri_burst', '트라이 버스트', '세 원소의 빛줄기를 무작위 적에게 여섯 번 쏩니다.', 0, 1, 0, 2, 0, 0.7, hits=6, mp=20, pres='pr_m_prism'),
        S(29, 'jb_el_eruption', '이럽션', '땅속의 불길을 터뜨려 적 전체를 태웁니다.', 0, 1, 0, 1, 4, 1.3, mp=24, status='burn', chance=0.5, pres='pr_m_hellfire'),
    ],
    'archmage': [
        ULT(40, 'archmage', '그랜드 메테오', '세 겹의 마법진을 열고 거대한 운석을 떨어뜨려 적 전체를 세 번 강타합니다.', 0, 1, 0, 1, 4, 1.5, hits=3, dign=0.2, status='burn', chance=0.6),
        S(44, 'jb_am_mana_tide', '마나의 조류', '마나의 흐름을 열어 아군 전체의 마력을 높이고 재생을 부여합니다.', 2, 1, 1, 1, 0, mp=24, status='magic_up', chance=1.0, extra=['regen'], tier=3, pres='pr_m_focus'),
        S(48, 'jb_am_starfall', '별의 낙하', '별빛을 떨어뜨려 적 전체를 칩니다.', 0, 1, 0, 1, 0, 1.6, mp=34, tier=3, pres='pr_jb_starfall'),
        S(52, 'jb_am_time_stop', '시간 왜곡', '시간을 비틀어 적 전체를 느리게 하고 침묵시킵니다.', 3, 1, 0, 1, 0, mp=30, status='slow', chance=0.7, extra=['silence'], tier=3, pres='pr_m_silence'),
        S(56, 'jb_am_annihilate', '원소 대붕괴', '모든 원소를 한 점에 모아 적 하나를 소멸시킵니다. 방어를 30% 무시합니다.', 0, 1, 0, 0, 0, 3.4, mp=38, dign=0.3, tier=3, pres='pr_void_lance'),
    ],
    'warlock': [
        S(15, 'jb_wk_hex_bolt', '헥스 볼트', '저주가 깃든 어둠의 화살. 적의 공격을 낮출 수 있습니다.', 0, 1, 0, 0, 7, 1.6, mp=9, status='attack_down', chance=0.4, pres='pr_dark'),
        S(17, 'jb_wk_wither', '쇠약의 저주', '적 하나의 공격과 방어를 함께 낮춥니다.', 3, 1, 0, 0, 0, mp=8, status='defense_down', chance=0.8, extra=['attack_down'], pres='pr_debuff'),
        S(20, 'jb_wk_soul_drain', '영혼 흡수', '적의 영혼을 빨아들여 준 피해의 절반만큼 회복합니다.', 0, 1, 0, 0, 7, 1.7, mp=12, drain=0.5, pres='pr_m_drain'),
        S(23, 'jb_wk_plague', '역병', '독기를 퍼뜨려 적 전체를 맹독에 빠뜨립니다.', 0, 1, 0, 1, 0, 0.6, mp=14, status='poison_strong', chance=0.7, pres='pr_toxic_cloud'),
        ULT(25, 'warlock', '저주의 소용돌이', '보랏빛 저주의 소용돌이가 적 전체를 세 번 휘감고 공격과 방어를 낮춥니다.', 0, 1, 0, 1, 7, 1.3, hits=3, status='attack_down', chance=0.6, extra=['defense_down']),
        S(26, 'jb_wk_nightmare', '악몽', '적 전체를 깊은 잠에 빠뜨립니다.', 3, 1, 0, 1, 0, mp=16, status='sleep', chance=0.55, pres='pr_m_sleep'),
        S(29, 'jb_wk_doom', '둠', '파멸의 주문. 공격이 약해진 적에게 더 큰 피해를 줍니다.', 0, 1, 0, 0, 7, 2.6, mp=22, bvs='attack_down', bvsm=1.4, pres='pr_void_lance'),
    ],
    'abyssal': [
        ULT(40, 'abyssal', '심연 개문', '공허의 균열을 찢어 열어 적 전체를 세 번 삼킵니다. 준 피해의 일부를 흡수합니다.', 0, 1, 0, 1, 7, 1.6, hits=3, dign=0.3, drain=0.2),
        S(44, 'jb_ab_void_rift', '공허의 균열', '공허를 열어 적 전체에 피해를 주고 공격을 낮춥니다.', 0, 1, 0, 1, 7, 1.5, mp=30, status='attack_down', chance=0.5, tier=3, pres='pr_m_abyss_gate'),
        S(48, 'jb_ab_abyss_ward', '심연의 장벽', '심연의 막으로 아군 전체에 보호막을 두릅니다.', 2, 1, 1, 1, 0, mp=28, status='barrier', chance=1.0, extra=['magic_up'], tier=3, pres='pr_abyss_wall'),
        S(52, 'jb_ab_soul_harvest', '영혼 수확', '적 전체의 영혼을 거둬 준 피해의 30%만큼 회복합니다.', 0, 1, 0, 1, 7, 1.2, mp=34, drain=0.3, tier=3, pres='pr_soul_reap'),
        S(56, 'jb_ab_oblivion', '망각', '적 전체의 기억을 지워 침묵시키고 잠재웁니다.', 3, 1, 0, 1, 0, mp=30, status='silence', chance=0.6, extra=['sleep'], tier=3, pres='pr_m_silence'),
    ],
    'sniper': [
        S(15, 'jb_sn_aimed_shot', '조준 사격', '숨을 고르고 쏘는 한 발. 치명타가 잘 터집니다.', 0, 0, 0, 0, 3, 2.0, mp=8, crit=0.25, pres='pr_arrow_snipe'),
        S(17, 'jb_sn_steady_aim', '정신 집중', '호흡을 가다듬어 공격과 속도를 높입니다.', 2, 0, 2, 0, 0, mp=6, status='attack_up', chance=1.0, extra=['speed_up'], pres='pr_a_focus'),
        S(20, 'jb_sn_armor_pierce', '철갑 화살', '갑옷을 꿰뚫는 화살. 방어를 50% 무시합니다.', 0, 0, 0, 0, 3, 1.7, mp=12, dign=0.5, pres='pr_jb_armor_pierce'),
        S(23, 'jb_sn_headshot', '헤드샷', '급소를 노린 사격. 치명타가 매우 잘 터지고 기절시킬 수 있습니다.', 0, 0, 0, 0, 3, 2.4, mp=16, crit=0.4, status='stun', chance=0.3, pres='pr_a_deadeye'),
        ULT(25, 'sniper', '일격필살', '조준경이 한 점에 모이는 순간 빛의 화살로 적 하나를 꿰뚫습니다. 방어를 절반 무시합니다.', 0, 0, 0, 0, 3, 5.0, crit=0.5, dign=0.5),
        S(26, 'jb_sn_suppress', '제압 사격', '무작위 적에게 네 발을 쏘아 느리게 만듭니다.', 0, 0, 0, 2, 3, 0.8, hits=4, mp=18, status='slow', chance=0.4, pres='pr_a_gale'),
        S(29, 'jb_sn_disarm', '무력화 사격', '적의 무기를 노려 공격을 크게 떨어뜨립니다.', 0, 0, 0, 0, 3, 1.5, mp=14, status='attack_down', chance=0.7, pres='pr_a_flash'),
    ],
    'divine_archer': [
        ULT(40, 'divine_archer', '천상의 빛화살', '하늘에 황금 문장을 열어 적 전체에 신성한 화살을 네 번 쏟아붓습니다.', 0, 0, 0, 1, 8, 1.3, hits=4, crit=0.2),
        S(44, 'jb_da_sacred_arrow', '신성 관통시', '신성한 화살로 적 하나를 꿰뚫습니다. 방어를 30% 무시합니다.', 0, 0, 0, 0, 8, 2.8, mp=18, dign=0.3, tier=3, pres='pr_a_holy'),
        S(48, 'jb_da_blessing_wind', '축복의 바람', '축복의 바람이 아군 전체의 속도와 공격을 높입니다.', 2, 1, 1, 1, 0, mp=26, status='speed_up', chance=1.0, extra=['attack_up'], tier=3, pres='pr_c_hymn_swift'),
        S(52, 'jb_da_judgment_rain', '심판의 화살비', '빛의 화살비로 적 전체를 꿰뚫습니다.', 0, 0, 0, 1, 8, 1.5, mp=30, crit=0.1, tier=3, pres='pr_arrow_all'),
        S(56, 'jb_da_true_shot', '진실의 한 발', '하늘의 뜻을 담은 화살. 방어를 절반 무시합니다.', 0, 0, 0, 0, 3, 4.0, mp=34, crit=0.3, dign=0.5, tier=3, pres='pr_a_deadeye'),
    ],
    'ranger': [
        S(15, 'jb_ra_quick_draw', '속사', '눈 깜짝할 새 적 하나에게 세 발을 쏩니다.', 0, 0, 0, 0, 3, 0.6, hits=3, mp=7, pres='pr_a_triple'),
        S(17, 'jb_ra_snare', '올가미 덫', '덫으로 적 하나를 묶어 느리게 만듭니다.', 0, 0, 0, 0, 3, 1.2, mp=6, status='slow', chance=0.7, pres='pr_root'),
        S(20, 'jb_ra_wind_step', '바람 걸음', '바람을 타고 움직여 속도와 공격을 높입니다.', 2, 0, 2, 0, 0, mp=8, status='speed_up', chance=1.0, extra=['attack_up'], pres='pr_c_haste'),
        S(23, 'jb_ra_thorn_volley', '가시 화살비', '가시 화살을 무작위 적에게 여섯 번 쏘고 독을 퍼뜨립니다.', 0, 0, 0, 2, 3, 0.55, hits=6, mp=14, status='poison', chance=0.3, pres='pr_a_gale'),
        ULT(25, 'ranger', '질풍노도', '나뭇잎 폭풍을 두르고 무작위 적에게 화살 열 발을 몰아칩니다.', 0, 0, 0, 2, 3, 0.75, hits=10, crit=0.1),
        S(26, 'jb_ra_falcon', '매의 습격', '길들인 매가 무작위 적을 다섯 번 할퀴고 눈을 가립니다.', 0, 0, 0, 2, 3, 0.6, hits=5, mp=16, status='blind', chance=0.3, pres='pr_crow_swarm'),
        S(29, 'jb_ra_storm_arrows', '폭풍 화살', '돌풍에 실은 화살로 적 전체를 두 번 꿰뚫습니다.', 0, 0, 0, 1, 3, 0.6, hits=2, mp=20, pres='pr_a_piercing_gale'),
    ],
    'shadow_stalker': [
        ULT(40, 'shadow_stalker', '그림자 처형', '그림자 속으로 사라졌다가 적 하나를 일곱 번 베어 냅니다. 방어를 일부 무시합니다.', 0, 0, 0, 0, 7, 0.9, hits=7, crit=0.3, dign=0.3),
        S(44, 'jb_ss_shadow_veil', '그림자 장막', '그림자를 둘러 보호막을 만들고 빨라집니다.', 2, 0, 2, 0, 0, mp=18, status='speed_up', chance=1.0, extra=['barrier'], tier=3, pres='pr_jb_veil'),
        S(48, 'jb_ss_assassinate', '암살', '숨통을 노리는 일격. 잠든 적에게 훨씬 큰 피해를 줍니다.', 0, 0, 0, 0, 7, 3.2, mp=26, crit=0.4, bvs='sleep', bvsm=1.5, tier=3, pres='pr_a_shadow'),
        S(52, 'jb_ss_night_raid', '야습', '어둠 속에서 무작위 적을 일곱 번 습격합니다.', 0, 0, 0, 2, 7, 0.8, hits=7, mp=30, tier=3, pres='pr_a_phantom'),
        S(56, 'jb_ss_venom_fang', '독아 난무', '독 묻은 화살로 적 전체를 두 번 꿰뚫고 맹독에 빠뜨립니다.', 0, 0, 0, 1, 3, 1.0, hits=2, mp=30, status='poison_strong', chance=0.6, tier=3, pres='pr_a_venom'),
    ],
    'priest': [
        S(15, 'jb_pr_renew', '리뉴', '아군 하나를 회복하고 재생을 부여합니다.', 1, 1, 1, 0, 0, 1.6, mp=9, status='regen', chance=1.0, pres='pr_c_regen'),
        S(17, 'jb_pr_prayer', '기도', '아군 전체를 회복합니다.', 1, 1, 1, 1, 0, 1.0, mp=14, pres='pr_heal_all'),
        S(20, 'jb_pr_bless_all', '축복의 비', '아군 전체의 마력과 공격을 높입니다.', 2, 1, 1, 1, 0, mp=18, status='magic_up', chance=1.0, extra=['attack_up'], pres='pr_c_protect_all'),
        S(23, 'jb_pr_revive_light', '소생의 빛', '쓰러진 동료 하나를 체력의 60%로 일으킵니다.', 4, 1, 1, 0, 0, 0.6, mp=20, pres='pr_revive'),
        ULT(25, 'priest', '축복의 성광', '빛의 기둥과 꽃잎이 아군 전체를 크게 회복하고 재생과 방어 상승을 부여합니다.', 1, 1, 1, 1, 0, 2.4, status='regen', chance=1.0, extra=['defense_up']),
        S(26, 'jb_pr_holy_wall', '성벽의 기도', '아군 전체에 보호막을 두릅니다.', 2, 1, 1, 1, 0, mp=22, status='barrier', chance=1.0, pres='pr_c_barrier'),
        S(29, 'jb_pr_full_heal', '풀 힐', '아군 하나를 크게 회복합니다.', 1, 1, 1, 0, 0, 4.0, mp=22, pres='pr_greater_heal'),
    ],
    'saint': [
        ULT(40, 'saint', '성녀의 강림', '거대한 후광 아래 쓰러진 동료를 모두 일으키고 아군 전체를 감쌉니다.', 4, 1, 1, 1, 0, 1.0),
        S(44, 'jb_sa_grace', '은총', '아군 전체를 크게 회복하고 재생을 부여합니다.', 1, 1, 1, 1, 0, 1.8, mp=30, status='regen', chance=1.0, tier=3, pres='pr_c_benediction'),
        S(48, 'jb_sa_divine_shield', '신성 방벽', '아군 전체의 방어를 크게 높이고 보호막을 두릅니다.', 2, 1, 1, 1, 0, mp=32, status='defense_up_l', chance=1.0, extra=['barrier'], tier=3, pres='pr_c_sanctuary'),
        S(52, 'jb_sa_holy_nova', '홀리 노바', '성스러운 빛을 터뜨려 적 전체를 정화합니다.', 0, 1, 0, 1, 8, 1.5, mp=30, tier=3, pres='pr_holy_all'),
        S(56, 'jb_sa_angel_song', '천사의 노래', '아군 전체의 마력과 속도를 높이고 재생을 부여합니다.', 2, 1, 1, 1, 0, mp=36, status='magic_up', chance=1.0, extra=['speed_up', 'regen'], tier=3, pres='pr_c_hymn_swift'),
    ],
    'exorcist': [
        S(15, 'jb_ex_holy_seal', '성인', '신성한 인장을 새겨 적 하나를 치고 침묵시킬 수 있습니다.', 0, 1, 0, 0, 8, 1.9, mp=9, status='silence', chance=0.3, pres='pr_c_banish'),
        S(17, 'jb_ex_smite', '징벌', '빛의 창으로 적 하나를 꿰뚫습니다.', 0, 1, 0, 0, 8, 2.2, mp=12, pres='pr_c_holy_lance'),
        S(20, 'jb_ex_ward', '퇴마 결계', '결계를 둘러 보호막을 만들고 마력을 높입니다.', 2, 1, 2, 0, 0, mp=10, status='magic_up', chance=1.0, extra=['barrier'], pres='pr_c_barrier'),
        S(23, 'jb_ex_purge', '정화의 불꽃', '성화로 적 전체를 태웁니다.', 0, 1, 0, 1, 8, 1.1, mp=16, status='burn', chance=0.3, pres='pr_holy_all'),
        ULT(25, 'exorcist', '대퇴마진', '거대한 성인이 회전하며 열려 적 전체를 세 번 정화하고 침묵시킵니다.', 0, 1, 0, 1, 8, 1.4, hits=3, status='silence', chance=0.5),
        S(26, 'jb_ex_spirit_chain', '영혼 사슬', '빛의 사슬로 적 하나를 묶어 침묵시키고 느리게 합니다.', 3, 1, 0, 0, 0, mp=14, status='silence', chance=0.7, extra=['slow'], pres='pr_m_silence'),
        S(29, 'jb_ex_banishment', '대추방', '악을 쫓아내는 일격. 침묵한 적에게 더 큰 피해를 줍니다.', 0, 1, 0, 0, 8, 3.0, mp=22, bvs='silence', bvsm=1.3, pres='pr_c_exorcism'),
    ],
    'inquisitor': [
        ULT(40, 'inquisitor', '최후의 심판', '붉은 심판의 기둥과 거대한 십자가로 적 하나를 꿰뚫고 방어를 낮춥니다.', 0, 1, 0, 0, 8, 5.5, dign=0.4, status='defense_down', chance=0.8),
        S(44, 'jb_iq_verdict', '판결', '심판의 빛으로 적 전체를 치고 방어를 낮춥니다.', 0, 1, 0, 1, 8, 1.5, mp=30, status='defense_down', chance=0.5, tier=3, pres='pr_c_inquisitor'),
        S(48, 'jb_iq_interrogate', '심문', '적 하나를 침묵시키고 공격과 방어를 낮춥니다.', 3, 1, 0, 0, 0, mp=18, status='silence', chance=0.85, extra=['attack_down', 'defense_down'], tier=3, pres='pr_debuff'),
        S(52, 'jb_iq_crimson_cross', '진홍의 십자', '붉은 십자가로 적 하나를 치고 준 피해의 30%만큼 회복합니다.', 0, 1, 0, 0, 8, 3.5, mp=32, drain=0.3, tier=3, pres='pr_c_holy_lance'),
        S(56, 'jb_iq_absolution', '사면', '아군 전체를 회복하고 재생을 부여합니다.', 1, 1, 1, 1, 0, 2.0, mp=34, status='regen', chance=1.0, tier=3, pres='pr_heal_all'),
    ],
}

# ------------------------------------------------------------------ presentations
# Signature ultimates: one per job, playing the authored job_<id> area effect.
ULT_PRES = {
    #                 action,  approach,         impact,          wait, light
    'knight':         ('attack', 'dash_to_target', 'critical',       0.7, [0.6, 0.8, 1.0, 1.0]),
    'paladin':        ('attack', 'dash_to_target', 'holy',           0.8, [1.0, 0.95, 0.7, 1.0]),
    'berserker':      ('attack', 'dash_to_target', 'crimson_slash',  0.6, [1.0, 0.35, 0.3, 1.0]),
    'warlord':        ('attack', 'dash_to_target', 'critical',       0.8, [1.0, 0.4, 0.3, 1.0]),
    'elementalist':   ('cast',   'none',           'prism_hit',      0.8, [1.0, 0.8, 0.9, 1.0]),
    'archmage':       ('cast',   'none',           'flame',          1.0, [1.0, 0.55, 0.25, 1.0]),
    'warlock':        ('cast',   'none',           'dark',           0.7, [0.75, 0.45, 1.0, 1.0]),
    'abyssal':        ('cast',   'none',           'void_pierce',    0.9, [0.55, 0.8, 1.0, 1.0]),
    'sniper':         ('shoot',  'none',           'snipe_hit',      0.6, [0.9, 0.97, 1.0, 1.0]),
    'divine_archer':  ('shoot',  'none',           'holy_arrow_hit', 0.8, [1.0, 0.95, 0.7, 1.0]),
    'ranger':         ('shoot',  'none',           'pierce',         0.6, [0.55, 1.0, 0.6, 1.0]),
    'shadow_stalker': ('attack', 'dash_to_target', 'critical',       0.6, [0.7, 0.45, 1.0, 1.0]),
    'priest':         ('cast',   'none',           'heal',           0.6, [1.0, 0.95, 0.8, 1.0]),
    'saint':          ('cast',   'none',           'revive',         0.8, [1.0, 0.98, 0.88, 1.0]),
    'exorcist':       ('cast',   'none',           'holy',           0.6, [1.0, 0.97, 0.85, 1.0]),
    'inquisitor':     ('cast',   'none',           'judgment_cross', 0.8, [1.0, 0.45, 0.4, 1.0]),
}
CHARGE = {'attack': 'charge_grand', 'cast': 'charge_grand', 'shoot': 'charge_grand'}


def pres_row(pid, tier, action, approach, charge, travel, impact, interval, hit_stop, shake, flash, light, area, wait, sfx_cast=''):
    return {'tier': tier, 'actor_action': action, 'approach': approach, 'charge_vfx': charge, 'travel_vfx': travel,
            'impact_vfx': impact, 'hit_interval': interval, 'hit_stop': hit_stop, 'shake': shake, 'screen_flash': flash,
            'light_color': light, 'sfx_cast': sfx_cast, 'sfx_impact': '', 'id': pid, '_file': pid,
            'area_vfx': area, 'area_wait': wait, 'area_scale': 1.0}


def presentations():
    rows = []
    for job, (action, approach, impact, wait, light) in ULT_PRES.items():
        travel = 'arrow' if action == 'shoot' and job != 'divine_archer' else ''
        rows.append(pres_row('pr_jb_' + job, 3, action, approach, CHARGE[action], travel, impact, 0.1, 0.11, 0.55, True, light, 'job_' + job, wait))
    rows.append(pres_row('pr_jb_lance', 2, 'attack', 'dash_to_target', '', '', 'void_pierce', 0.09, 0.09, 0.4, False, [0.7, 0.85, 1.0, 1.0], '', 0.0))
    rows.append(pres_row('pr_jb_armor_pierce', 2, 'shoot', 'none', 'charge_bow', 'arrow', 'snipe_hit', 0.09, 0.08, 0.35, False, [0.9, 0.95, 1.0, 1.0], '', 0.0))
    rows.append(pres_row('pr_jb_starfall', 3, 'cast', 'none', 'magic_circle', '', 'arcane_hit', 0.1, 0.09, 0.5, True, [0.85, 0.85, 1.0, 1.0], 'prism_ray', 0.6))
    rows.append(pres_row('pr_jb_overlord', 3, 'cast', 'none', 'aura', '', 'debuff', 0.09, 0.05, 0.35, False, [1.0, 0.45, 0.35, 1.0], 'warcry', 0.35, 'sfx_dark'))
    rows.append(pres_row('pr_jb_veil', 2, 'cast', 'none', '', '', 'smoke', 0.09, 0.0, 0.0, False, [0.6, 0.45, 0.9, 1.0], '', 0.0, 'sfx_buff'))
    for r in rows:
        if not r['area_vfx']:
            del r['area_vfx'], r['area_wait'], r['area_scale']
    return rows


def skill_row(s):
    row = {'id': s['id'], 'display_name': s['name'], 'description': s['desc'], 'kind': s['kind'], 'scaling_stat': s['sc'],
           'target_type': s['tt'], 'scope': s['scope'], 'element': s['el'], 'power': float(s['power']), 'hit_count': s['hits'],
           'mp_cost': s['mp'], 'tp_cost': 100 if s['id'].startswith('ult_') else 0, 'crit_bonus': float(s['crit']),
           'defense_ignore': float(s['dign']), 'tier': s['tier'], 'status_chance': float(s['chance']),
           'bonus_vs_status': s['bvs'], 'bonus_vs_status_mult': float(s['bvsm'])}
    if s['drain']:
        row['drain'] = float(s['drain'])
    if s['status']:
        row['status_effect'] = s['status']
    if s['extra']:
        row['extra_statuses'] = s['extra']
    row['presentation'] = s['pres']
    row['_file'] = s['id']
    return row


def job_rows():
    order = []
    for base in BASES:
        order.append(base)
        for adv in JOB_TREE[base]:
            order.append(adv)
            order.extend(JOB_TREE.get(adv, ()))
    rows = []
    for job in order:
        tier = tier_of(job)
        m = STATS.get(job, (1, 1, 1, 1, 1, 1, 1, 0, 0, 0))
        row = {'id': job, 'display_name': JOB_NAMES_KO[job], 'hero': base_of(job), 'tier': tier, 'parent': PARENT.get(job, ''),
               'description': DESCRIPTIONS[job],
               'required_level': {1: 1, 2: 15, 3: 40}[tier],
               'required_item': {1: '', 2: 'job_medal', 3: 'master_seal'}[tier],
               'required_boss': {1: '', 2: 'forest_guardian', 3: 'boss'}[tier],
               'hp_mult': m[0], 'mp_mult': m[1], 'atk_mult': m[2], 'mag_mult': m[3], 'def_mult': m[4], 'res_mult': m[5], 'spd_mult': m[6],
               'hit': m[7], 'evade': m[8], 'crit': m[9],
               'signature_weapon': JOB_WEAPONS.get(job, ''),
               'learnset': [{'level': s['level'], 'skill': s['id']} for s in LEARNSETS.get(job, [])],
               '_file': job}
        for k in ('hp_mult', 'mp_mult', 'atk_mult', 'mag_mult', 'def_mult', 'res_mult', 'spd_mult', 'hit', 'evade', 'crit'):
            row[k] = float(row[k])
        rows.append(row)
    return rows


ITEMS = [
    {'id': 'job_medal', 'display_name': '전직의 증표', 'description': '전직의 자격을 증명하는 은빛 증표. 길드에서 1차 전직을 할 때 하나 사용합니다.',
     'item_type': 7, 'heal_amount': 0, 'max_stack': 99, 'power': 0.0, 'value': 0, 'target': 'none', 'price': 0, 'sell_price': 0,
     'shop_tier': 0, 'status_id': '', 'element': 0, '_file': 'job_medal', 'rarity': 2},
    {'id': 'master_seal', 'display_name': '마스터의 인장', 'description': '한 길을 끝까지 걸은 자에게 주어지는 금빛 인장. 길드에서 2차 전직을 할 때 하나 사용합니다.',
     'item_type': 7, 'heal_amount': 0, 'max_stack': 99, 'power': 0.0, 'value': 0, 'target': 'none', 'price': 0, 'sell_price': 0,
     'shop_tier': 0, 'status_id': '', 'element': 0, '_file': 'master_seal', 'rarity': 3},
]

TEXT = {
    'job_title': '전직',
    'job_greeting': '충분히 단련했다면 새로운 길을 열어 드리지요. 전직해도 익힌 기술은 그대로 남습니다.',
    'job_changed_msg': '전직 완료! %s의 새 직업은 %s입니다.',
    'job_label': '직업',
    'reason_job_unknown': '등록되지 않은 직업입니다.',
    'reason_job_not_next': '지금 직업에서 바로 이어지는 직업이 아닙니다.',
    'reason_job_level': '레벨이 부족합니다.',
    'reason_job_boss': '아직 전직의 자격을 얻지 못했습니다. 더 강한 수호자를 쓰러뜨려야 합니다.',
    'reason_job_item': '전직에 필요한 아이템이 없습니다.',
    'reason_job_battle': '탐험 중에는 전직할 수 없습니다.',
    'reason_job_mismatch': '지금 직업으로는 장착할 수 없습니다.',
    'cannot_equip_job': '다른 직업 전용 장비',
}


def load(name):
    path = os.path.join(DATA, name + '.json')
    raw = open(path, 'rb').read()
    return json.loads(raw.decode('utf-8')), raw.endswith(b'\r\n')


def dump(name, data, trailing):
    text = json.dumps(data, ensure_ascii=False, indent=1).replace('\n', '\r\n') + ('\r\n' if trailing else '')
    with open(os.path.join(DATA, name + '.json'), 'wb') as f:
        f.write(text.encode('utf-8'))


def main():
    effects = {e['key'] for e in json.load(open(os.path.join(ROOT, 'Assets/_Game/Resources/Vfx/effects.json'), encoding='utf-8'))['effects']}
    statuses = {s['id'] for s in load('statuses')[0]}

    pres, trail = load('presentation')
    new_pres = presentations()
    owned = {p['id'] for p in new_pres}
    pres = [p for p in pres if p['id'] not in owned] + new_pres
    pres_ids = {p['id'] for p in pres}
    for p in new_pres:
        for key in ('charge_vfx', 'travel_vfx', 'impact_vfx', 'area_vfx'):
            assert not p.get(key) or p[key] in effects, (p['id'], key, p[key])
    dump('presentation', pres, trail)

    skills, trail = load('skills')
    new_skills = [skill_row(s) for rows in LEARNSETS.values() for s in rows]
    owned = {s['id'] for s in new_skills}
    assert len(owned) == len(new_skills), 'duplicate job skill id'
    existing = {s['id'] for s in skills if s['id'] not in owned}
    assert not owned & existing
    for s in new_skills:
        assert s['presentation'] in pres_ids, (s['id'], s['presentation'])
        for st in [s.get('status_effect')] + s.get('extra_statuses', []):
            assert st is None or st in statuses, (s['id'], st)
    skills = sorted([s for s in skills if s['id'] not in owned] + new_skills, key=lambda s: s['id'])
    dump('skills', skills, trail)

    dump('jobs', job_rows(), True)

    items, trail = load('items')
    have = {i['id'] for i in items}
    for item in ITEMS:
        if item['id'] not in have:
            items.append(item)
    items.sort(key=lambda i: i['id'])
    dump('items', items, trail)

    text, trail = load('text_ko')
    text.update(TEXT)
    dump('text_ko', text, trail)
    print('jobs: %d rows, %d job skills, %d presentations' % (len(job_rows()), len(new_skills), len(new_pres)))


if __name__ == '__main__':
    main()
