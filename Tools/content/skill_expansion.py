"""Skill expansion (2026-10-14): new hunter skills with the execute / shield-crusher / self-buff mechanics, signature
monster moves, their presentations, the class learnset entries and the extra monster moves.

    python3 Tools/content/skill_expansion.py            # upsert into the data files, then run hunters.py
    python3 Tools/content/skill_expansion.py --check    # validate only

Idempotent: rows are upserted by id (skills before the sig_* rows that hunters.py rewrites, presentations at the end),
learnset entries and monster moves are added once. It edits the current data files directly because build_world.py no
longer reproduces them (later hand-authored floor events would be lost); run it after any build_world.py run.

New mechanics (SkillDef, BattleEngine): execute_below / execute_mult (bonus on low-HP targets), break_power (shield points
removed by every landed hit, weakness or not) and self_status (a status the attacker gains once the action lands).
"""
import json
import os
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.normpath(os.path.join(HERE, '..', '..'))
DATA = os.path.join(ROOT, 'Assets', '_Game', 'Resources', 'Data')
BASE_HEROES = os.path.join(HERE, 'world', 'base_heroes.json')
EFFECTS = os.path.join(ROOT, 'Assets', '_Game', 'Resources', 'Vfx', 'effects.json')

# kind: 0 damage 1 heal 2 buff 3 debuff | scaling: 0 atk 1 mag | target: 0 enemy 1 ally 2 self | scope: 0 single 1 all 2 random
# element: 0 none 1 slash 2 blunt 3 pierce 4 fire 5 ice 6 thunder 7 dark 8 holy


def S(id, name, desc, kind, scaling, target, scope, element, power, pres, hits=1, mp=0, status=None, chance=0.0, extra=None,
      crit=0.0, ignore=0.0, execute=(0.0, 1.0), breaks=0, self_status='', tier=2):
    row = {
        'id': id, 'display_name': name, 'description': desc, 'kind': kind, 'scaling_stat': scaling,
        'target_type': target, 'scope': scope, 'element': element, 'power': power, 'hit_count': hits,
        'mp_cost': mp, 'tp_cost': 0, 'crit_bonus': crit, 'defense_ignore': ignore, 'tier': tier,
        'status_chance': chance, 'bonus_vs_status': '', 'bonus_vs_status_mult': 1.0,
    }
    if status:
        row['status_effect'] = status
    if extra:
        row['extra_statuses'] = extra
    if execute[0] > 0:
        row['execute_below'], row['execute_mult'] = execute
    if breaks:
        row['break_power'] = breaks
    if self_status:
        row['self_status'] = self_status
    row['presentation'] = pres
    row['_file'] = id
    return row


HERO_SKILLS = [
    # warrior
    S('sk_w_shield_crush', '실드 크러시', '방패째 내려찍어 약점과 상관없이 적의 실드를 1 더 깎습니다.', 0, 0, 0, 0, 2, 0.9, 'pr_w_crush',
      mp=8, breaks=1),
    S('sk_w_execution', '처형의 일격', '뛰어올라 내려벱니다. 체력이 30% 이하인 적에게는 1.6배 피해를 줍니다.', 0, 0, 0, 0, 1, 1.2, 'pr_w_execution',
      mp=9, crit=0.05, execute=(0.3, 1.6)),
    S('sk_w_battle_flow', '기세 연참', '두 번 베어 낸 뒤 그 기세로 자신의 공격력을 올립니다.', 0, 0, 0, 0, 1, 0.72, 'pr_w_combo',
      hits=2, mp=8, self_status='attack_up'),
    # mage
    S('sk_m_shatter', '결정 파쇄', '얼음 창으로 꿰뚫어 약점과 상관없이 적의 실드를 1 더 깎습니다.', 0, 1, 0, 0, 5, 1.05, 'pr_m_shatter',
      mp=9, breaks=1),
    S('sk_m_soul_burn', '영혼 소각', '어둠의 불꽃으로 태웁니다. 체력이 30% 이하인 적에게는 1.6배 피해를 줍니다.', 0, 1, 0, 0, 7, 1.15, 'pr_m_soulburn',
      mp=8, execute=(0.3, 1.6)),
    S('sk_m_mana_surge', '마력 폭주', '번개를 네 번 무작위로 떨어뜨린 뒤 넘치는 마력으로 자신의 마력을 올립니다.', 0, 1, 0, 2, 6, 0.5, 'pr_chain_spark',
      hits=4, mp=12, self_status='magic_up'),
    # archer
    S('sk_a_breaker_bolt', '실드 브레이커', '갑옷 틈을 노린 화살로 약점과 상관없이 적의 실드를 1 더 깎습니다.', 0, 0, 0, 0, 3, 0.9, 'pr_a_breaker',
      mp=7, breaks=1),
    S('sk_a_finisher', '마무리 사격', '급소를 노립니다. 체력이 30% 이하인 적에게는 1.6배 피해를 줍니다.', 0, 0, 0, 0, 3, 1.15, 'pr_arrow_snipe',
      mp=7, crit=0.1, execute=(0.3, 1.6)),
    S('sk_a_volley_step', '질풍 연사', '뒤로 뛰며 세 발을 쏘고, 그 걸음으로 자신의 속도를 올립니다.', 0, 0, 0, 0, 3, 0.62, 'pr_a_triple',
      hits=3, mp=9, self_status='speed_up'),
    # cleric
    S('sk_c_judgment_hammer', '심판의 망치', '빛의 망치로 내려쳐 약점과 상관없이 적의 실드를 1 더 깎습니다.', 0, 1, 0, 0, 8, 1.0, 'pr_c_hammer',
      mp=8, breaks=1),
    S('sk_c_final_rite', '종언의 의식', '빛의 십자가를 내립니다. 체력이 30% 이하인 적에게는 1.6배 피해를 줍니다.', 0, 1, 0, 0, 8, 1.3, 'pr_c_final',
      mp=10, execute=(0.3, 1.6)),
    S('sk_c_guardian_light', '수호의 빛', '성스러운 빛을 쏜 뒤 자신을 보호막으로 감쌉니다.', 0, 1, 0, 0, 8, 1.1, 'holy_light',
      mp=8, self_status='barrier'),
]

MONSTER_MOVES = [
    S('sk_e_dive_bomb', '급강하', '높이 솟구쳤다가 내리꽂힙니다.', 0, 0, 0, 0, 0, 1.3, 'pr_e_dive'),
    S('sk_e_pounce', '덮치기', '몸을 낮췄다가 덮쳐 와 쓰러뜨립니다.', 0, 0, 0, 0, 1, 1.3, 'pr_e_pounce', status='stun', chance=0.1),
    S('sk_e_body_slam', '몸통 박치기', '뛰어올라 온몸으로 짓누릅니다.', 0, 0, 0, 0, 2, 1.35, 'pr_e_slam', status='stun', chance=0.15),
    S('sk_e_horn_charge', '뿔 돌진', '머리를 낮추고 돌진해 들이받습니다.', 0, 0, 0, 0, 3, 1.4, 'pr_e_charge'),
    S('sk_e_throat_bite', '목덜미 물기', '약해진 상대의 목덜미를 노립니다. 체력이 30% 이하이면 피해가 1.5배입니다.', 0, 0, 0, 0, 1, 1.15, 'pr_e_pounce',
      execute=(0.3, 1.5)),
    S('sk_e_bone_rush', '뼈 돌격', '부서진 뼈를 덜그럭거리며 돌격해 벱니다.', 0, 0, 0, 0, 1, 1.3, 'pr_e_charge', status='bleed', chance=0.2),
    S('sk_e_web_shot', '거미줄', '끈적한 거미줄을 뿜어 한 명의 발을 묶습니다.', 3, 1, 0, 0, 0, 0.0, 'pr_e_web', status='slow', chance=0.8),
    S('sk_e_slime_press', '짓누르기', '통통 튀어 와 몸으로 짓눌러 움직임을 둔하게 합니다.', 0, 0, 0, 0, 2, 1.25, 'pr_e_slam', status='slow', chance=0.2),
    S('sk_e_spore_burst', '포자 폭발', '포자를 터뜨려 전체를 중독시킵니다.', 0, 1, 0, 1, 0, 0.45, 'pr_e_spores', status='poison', chance=0.2),
    S('sk_e_execution', '처단', '쓰러져 가는 상대를 노려 벱니다. 체력이 30% 이하이면 피해가 1.6배입니다.', 0, 0, 0, 0, 1, 1.2, 'pr_e_execute',
      execute=(0.3, 1.6)),
]


def P(id, action, approach, impact, tier=2, charge='', travel='', area=None, area_scale=1.0, area_wait=0.0, shake=0.35,
      hit_stop=0.07, flash=False, light=(1.0, 1.0, 1.0), sfx_cast='', sfx_impact='', interval=0.1):
    row = {'tier': tier, 'actor_action': action, 'approach': approach, 'charge_vfx': charge, 'travel_vfx': travel,
           'impact_vfx': impact, 'hit_interval': interval, 'hit_stop': hit_stop, 'shake': shake, 'screen_flash': flash,
           'light_color': [light[0], light[1], light[2], 1.0], 'sfx_cast': sfx_cast, 'sfx_impact': sfx_impact,
           'id': id, '_file': id}
    if area:
        row.update({'area_vfx': area, 'area_wait': area_wait, 'area_scale': area_scale})
    return row


PRESENTATIONS = [
    P('pr_w_crush', 'attack', 'dash_to_target', 'armor_break', area='area_quake', area_scale=0.7, area_wait=0.05, shake=0.55,
      hit_stop=0.1, light=(1.0, 0.7, 0.35), sfx_impact='sfx_shock'),
    P('pr_w_execution', 'attack', 'dash_to_target', 'crimson_slash', charge='enchant', shake=0.6, hit_stop=0.11, flash=True,
      light=(1.0, 0.35, 0.3), sfx_cast='sfx_sword'),
    P('pr_m_shatter', 'cast', 'none', 'prism_hit', charge='charge_ice', travel='lance_ice', shake=0.5, hit_stop=0.09,
      light=(0.55, 0.85, 1.0)),
    P('pr_m_soulburn', 'cast', 'none', 'dark', charge='charge_dark', travel='bolt_dark', area='soul_reap', area_scale=0.6,
      area_wait=0.1, shake=0.45, hit_stop=0.08, light=(0.75, 0.4, 1.0)),
    P('pr_a_breaker', 'shoot', 'none', 'armor_break', charge='charge_bow', travel='arrow', shake=0.45, hit_stop=0.09,
      light=(1.0, 0.85, 0.5), sfx_impact='sfx_shock'),
    P('pr_c_hammer', 'attack', 'dash_to_target', 'stun_slam', charge='charge_holy', area='area_quake', area_scale=0.6,
      area_wait=0.05, shake=0.5, hit_stop=0.09, light=(1.0, 0.92, 0.6), sfx_impact='sfx_light'),
    P('pr_c_final', 'cast', 'none', 'light_hit', charge='charge_holy', area='judgment_cross', area_scale=0.7, area_wait=0.25,
      shake=0.55, hit_stop=0.1, flash=True, light=(1.0, 0.95, 0.7)),
    # monster moves
    P('pr_e_dive', 'attack', 'dash_to_target', 'impact', shake=0.4, hit_stop=0.08, light=(0.85, 0.85, 1.0), sfx_cast='sfx_wind'),
    P('pr_e_pounce', 'attack', 'dash_to_target', 'twin_bite', shake=0.38, hit_stop=0.07, light=(1.0, 0.5, 0.4)),
    P('pr_e_slam', 'attack', 'dash_to_target', 'stun_slam', area='area_quake', area_scale=0.55, area_wait=0.0, shake=0.55,
      hit_stop=0.1, light=(1.0, 0.78, 0.45), sfx_impact='sfx_earth'),
    P('pr_e_charge', 'attack', 'dash_to_target', 'pierce', shake=0.45, hit_stop=0.08, light=(1.0, 0.85, 0.65), sfx_impact='sfx_spear'),
    P('pr_e_web', 'cast', 'none', 'root_bind', light=(0.9, 0.92, 1.0), shake=0.15, hit_stop=0.04),
    P('pr_e_spores', 'cast', 'none', 'poison_hit', area='spore_burst', area_scale=0.8, area_wait=0.15, shake=0.2, hit_stop=0.03,
      light=(0.7, 0.9, 0.4)),
    P('pr_e_execute', 'attack', 'dash_to_target', 'crimson_slash', shake=0.5, hit_stop=0.1, light=(1.0, 0.4, 0.4)),
    # Monster skills that all shared pr_heavy_enemy (one tentacle-crush impact for a halberd, an anchor, a dive...).
    P('pr_e_clamp', 'attack', 'dash_to_target', 'twin_bite', shake=0.45, hit_stop=0.09, light=(0.7, 0.88, 1.0), sfx_impact='sfx_shock'),
    P('pr_e_halberd', 'attack', 'dash_to_target', 'bleed_slash', shake=0.5, hit_stop=0.09, light=(0.85, 0.9, 1.0), sfx_impact='sfx_axe'),
    P('pr_e_anchor', 'attack', 'dash_to_target', 'stun_slam', area='area_quake', area_scale=0.6, shake=0.6, hit_stop=0.1,
      light=(0.6, 0.8, 0.95), sfx_impact='sfx_water'),
    P('pr_e_stone_dive', 'attack', 'dash_to_target', 'blunt', area='area_quake', area_scale=0.55, shake=0.6, hit_stop=0.1,
      light=(0.85, 0.8, 0.75), sfx_cast='sfx_wind', sfx_impact='sfx_earth'),
    P('pr_e_burrow', 'attack', 'dash_to_target', 'stun_slam', area='area_quake', area_scale=0.7, shake=0.6, hit_stop=0.1,
      light=(0.9, 0.75, 0.55), sfx_impact='sfx_earth'),
    P('pr_e_tail', 'attack', 'dash_to_target', 'blunt', area='area_quake', area_scale=0.5, shake=0.55, hit_stop=0.09,
      light=(0.55, 0.8, 1.0), sfx_impact='sfx_water'),
]

# Existing monster skills moved off the shared pr_heavy_enemy (sk_tentacle_crush keeps it: the tentacle impact is its own).
PRESENTATION_OF = {
    'sk_e_clamp': 'pr_e_clamp', 'sk_e_halberd': 'pr_e_halberd', 'sk_e_anchor_smash': 'pr_e_anchor',
    'sk_e_stone_dive': 'pr_e_stone_dive', 'sk_e_burrow_strike': 'pr_e_burrow', 'sk_lev_tail_crush': 'pr_e_tail',
}

# Class learnsets (world/base_heroes.json; hunters.py copies them to every hunter of the class).
LEARN = {
    'warrior': [(9, 'sk_w_shield_crush'), (14, 'sk_w_execution'), (19, 'sk_w_battle_flow')],
    'mage': [(10, 'sk_m_shatter'), (13, 'sk_m_soul_burn'), (18, 'sk_m_mana_surge')],
    'archer': [(5, 'sk_a_breaker_bolt'), (9, 'sk_a_finisher'), (15, 'sk_a_volley_step')],
    'cleric': [(7, 'sk_c_judgment_hammer'), (15, 'sk_c_final_rite'), (17, 'sk_c_guardian_light')],
}

# A third move for the regular monsters that only had a basic attack and one skill (weight 1: an occasional surprise).
# jellyfish stays as it is: the frost kraken summons it, and the boss band is tuned on its lullaby rate.
MONSTER_EXTRA = {
    'bat': 'sk_e_dive_bomb', 'grave_bat': 'sk_e_dive_bomb', 'killer_bee': 'sk_e_dive_bomb', 'phoenix': 'sk_e_dive_bomb',
    'fire_drake': 'sk_e_pounce', 'horned_rabbit': 'sk_e_pounce', 'ice_wolf': 'sk_e_throat_bite', 'lizardman': 'sk_e_venom_fang',
    'coral_crab': 'sk_e_clamp', 'ice_golem': 'sk_e_body_slam', 'sand_golem': 'sk_e_body_slam', 'yeti': 'sk_war_cry',
    'rhino_beetle': 'sk_e_horn_charge', 'sand_scorpion': 'sk_e_venom_fang', 'frost_spider': 'sk_e_web_shot',
    'magma_slime': 'sk_e_slime_press', 'slime': 'sk_e_slime_press', 'metal_slime': 'sk_e_slime_press',
    'gold_slime': 'sk_e_slime_press', 'ice_slime': 'sk_e_slime_press', 'mushroom': 'sk_e_spore_burst', 'sprout': 'sk_e_spore_burst',
    'skeleton': 'sk_e_bone_rush', 'dark_knight': 'sk_e_execution', 'scarecrow': 'sk_harvest_reap',
}


def load(path):
    with open(path, encoding='utf-8') as f:
        return json.load(f)


def dump(path, rows, trailing):
    text = json.dumps(rows, ensure_ascii=False, indent=1).replace('\n', '\r\n') + ('\r\n' if trailing else '')
    data = text.encode('utf-8')
    old = open(path, 'rb').read()
    if old == data:
        return False
    with open(path, 'wb') as f:
        f.write(data)
    return True


def upsert(rows, new_rows, before=None):
    """Replace rows with the same id in place; insert the others before the first row matching `before` (else append)."""
    index = {r['id']: i for i, r in enumerate(rows)}
    pending = []
    for r in new_rows:
        if r['id'] in index:
            rows[index[r['id']]] = r
        else:
            pending.append(r)
    at = next((i for i, r in enumerate(rows) if before and before(r)), len(rows))
    rows[at:at] = pending
    return rows


def build():
    skills = load(os.path.join(DATA, 'skills.json'))
    skills = upsert(skills, HERO_SKILLS + MONSTER_MOVES, before=lambda r: r['id'].startswith('sig_'))
    for row in skills:
        if row['id'] in PRESENTATION_OF:
            row['presentation'] = PRESENTATION_OF[row['id']]
    presentations = upsert(load(os.path.join(DATA, 'presentation.json')), PRESENTATIONS)
    heroes = load(BASE_HEROES)
    for t in heroes:
        have = {e['skill'] for e in t['learnset']}
        for level, skill in LEARN.get(t['id'], []):
            if skill not in have:
                t['learnset'].append({'level': level, 'skill': skill})
    enemies = load(os.path.join(DATA, 'enemies.json'))
    for e in enemies:
        move = MONSTER_EXTRA.get(e['id'])
        if move and move not in e['skills']:
            e['skills'].append(move)
            e['skill_weights'].append(1)
    # validation
    problems = []
    ids = {s['id'] for s in skills}
    pres = {p['id'] for p in presentations}
    statuses = {s['id'] for s in load(os.path.join(DATA, 'statuses.json'))}
    effects = {e['key'] for e in load(EFFECTS)['effects']}
    for s in HERO_SKILLS + MONSTER_MOVES:
        if s['presentation'] not in pres:
            problems.append('%s presentation %s' % (s['id'], s['presentation']))
        for st in [s.get('status_effect'), s.get('self_status')] + s.get('extra_statuses', []):
            if st and st not in statuses:
                problems.append('%s status %s' % (s['id'], st))
    for p in PRESENTATIONS:
        for k in ('charge_vfx', 'travel_vfx', 'impact_vfx', 'area_vfx'):
            if p.get(k) and p[k] not in effects:
                problems.append('%s %s %s' % (p['id'], k, p[k]))
    for skill, pid in PRESENTATION_OF.items():
        if skill not in ids or pid not in pres:
            problems.append('presentation override %s -> %s' % (skill, pid))
    for cls, entries in LEARN.items():
        for _, skill in entries:
            if skill not in ids:
                problems.append('%s learns unknown %s' % (cls, skill))
    for enemy, move in MONSTER_EXTRA.items():
        if move not in ids:
            problems.append('%s move %s' % (enemy, move))
        if not any(e['id'] == enemy for e in enemies):
            problems.append('unknown monster %s' % enemy)
    return skills, presentations, heroes, enemies, problems


def main(argv):
    skills, presentations, heroes, enemies, problems = build()
    for p in problems:
        print('PROBLEM', p)
    if problems:
        return 1
    if '--check' in argv:
        print('ok: %d hero skills, %d monster moves, %d presentations' % (len(HERO_SKILLS), len(MONSTER_MOVES), len(PRESENTATIONS)))
        return 0
    changed = [name for name, path, rows, trailing in (
        ('skills', os.path.join(DATA, 'skills.json'), skills, True),
        ('presentation', os.path.join(DATA, 'presentation.json'), presentations, False),
        ('base_heroes', BASE_HEROES, heroes, False),
        ('enemies', os.path.join(DATA, 'enemies.json'), enemies, True)) if dump(path, rows, trailing)]
    print('written:', ', '.join(changed) or 'nothing changed')
    # Hunters copy the class learnsets (and keep the sig_* rows last in skills.json).
    return subprocess.run([sys.executable, os.path.join(HERE, 'hunters.py')]).returncode


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
