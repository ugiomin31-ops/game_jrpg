"""Builds the playable hunter roster into Assets/_Game/Resources/Data/heroes.json (+ signature skills in skills.json).

    python3 Tools/content/hunters.py          # write heroes.json and the sig_* rows of skills.json
    python3 Tools/content/hunters.py --check  # build and validate only

Source: Tools/content/spec.py HUNTERS (20 hunters, 5 per class) and the four class templates in
Tools/content/world/base_heroes.json (the original warrior / mage / archer / cleric rows). A hunter is its class
template with personal stat multipliers, every learnset entry up to Lv 3 moved to Lv 1 (three skills from the
start), and a signature skill: a stronger, renamed copy of one class skill (id sig_<hunter>) learned at Lv 1.
Hunters who join later start with the gear tier of their zone (spec.TIER_OF_ZONE). Run after build_world.py
(which rewrites skills.json) and before apply_names.py. Deterministic.
"""
import copy
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.normpath(os.path.join(HERE, '..', '..'))
DATA = os.path.join(ROOT, 'Assets', '_Game', 'Resources', 'Data')
sys.path.insert(0, HERE)
import spec  # noqa: E402

GROWTH = {'max_hp': 'hp_growth', 'max_mp': 'mp_growth', 'attack': 'atk_growth', 'magic': 'mag_growth',
          'defense': 'def_growth', 'resistance': 'res_growth', 'speed': 'spd_growth'}
WEAPON_LINE = {'warrior': 'sword', 'mage': 'staff', 'archer': 'bow', 'cleric': 'mace'}
ARMOR_LINE = {'warrior': 'armor', 'mage': 'robe', 'archer': 'garb', 'cleric': 'robe'}
SIG_POWER = 1.15


def load(name):
    with open(os.path.join(DATA, name + '.json'), encoding='utf-8') as f:
        return json.load(f)


def dumps(rows):
    return (json.dumps(rows, ensure_ascii=False, indent=1).replace('\n', '\r\n') + '\r\n').encode('utf-8')


def write(name, rows):
    path = os.path.join(DATA, name + '.json')
    data = dumps(rows)
    old = open(path, 'rb').read() if os.path.exists(path) else b''
    if old == data:
        return False
    with open(path, 'wb') as f:
        f.write(data)
    return True


def signature(skills, h):
    base_id, name = h['sig']
    base = skills[base_id]
    row = copy.deepcopy(base)
    row['id'] = row['_file'] = 'sig_' + h['id'][2:]
    row['display_name'] = '★ ' + name
    row['description'] = '%s의 고유 기술. %s' % (h['name'], base.get('description', ''))
    row['power'] = round(float(base.get('power', 1.0)) * SIG_POWER, 3)
    return row


def build():
    templates = {t['id']: t for t in json.load(open(os.path.join(HERE, 'world', 'base_heroes.json'), encoding='utf-8'))}
    skills_rows = load('skills')
    skills = {s['id']: s for s in skills_rows}
    jobs = {j['id']: j for j in load('jobs')}
    equipment = {e['id']: e for e in load('equipment')}
    heroes, sigs = [], []
    for h in spec.HUNTERS:
        cls = h['cls']
        t = templates[cls]
        row = {'id': h['id'], 'display_name': h['name']}
        for k, v in t.items():
            if k in ('id', 'display_name', '_file', 'learnset', 'skills', 'starter_equipment'):
                continue
            row[k] = copy.deepcopy(v)
        for stat, mult in h['stat'].items():
            row[stat] = max(1, int(round(row[stat] * mult)))
            row[GROWTH[stat]] = round(row[GROWTH[stat]] * mult, 3)
        sig = signature(skills, h)
        sigs.append(sig)
        learn = sorted(t['learnset'], key=lambda e: e['level'])
        learnset = [{'level': 1, 'skill': sig['id']}]
        for e in learn:
            if e['skill'] == h['sig'][0]:
                continue  # the signature replaces its base skill
            learnset.append({'level': 1 if e['level'] <= 3 else e['level'], 'skill': e['skill']})
        row['skills'] = ['basic_attack'] + [e['skill'] for e in learnset if e['level'] == 1]
        row['learnset'] = learnset
        if h['join'] == 'start':
            row['starter_equipment'] = dict(t['starter_equipment'])
            kind, zone, price = 'start', 1, 0
        else:
            kind, zone = h['join'][0], h['join'][1]
            price = h['join'][2] if kind == 'scout' else 0
            tier = spec.TIER_OF_ZONE[zone]
            row['starter_equipment'] = {
                'weapon': spec.GEAR_LINES[WEAPON_LINE[cls]][tier - 1],
                'armor': spec.GEAR_LINES[ARMOR_LINE[cls]][tier - 1],
                'accessory': '',
            }
        row.update({'class': cls, 'rank': h['rank'], 'gender': h['gender'], 'join_kind': kind, 'join_zone': zone,
                    'scout_price': price, 'start_job': h['start_job'] or '', 'line': h['line'], 'profile': h['look'],
                    '_file': h['id']})
        heroes.append(row)
    # validation
    problems = []
    for row in heroes:
        for e in row['learnset']:
            if e['skill'] not in skills and not e['skill'].startswith('sig_'):
                problems.append('%s learns unknown %s' % (row['id'], e['skill']))
        for slot, gid in row['starter_equipment'].items():
            if gid and (gid not in equipment or equipment[gid]['slot'] != slot or
                        (equipment[gid]['classes'] and row['class'] not in equipment[gid]['classes'])):
                problems.append('%s starter %s %s' % (row['id'], slot, gid))
        sj = row['start_job']
        if sj and (sj not in jobs or jobs[sj]['hero'] != row['class']):
            problems.append('%s start_job %s' % (row['id'], sj))
    if len(heroes) != len({r['id'] for r in heroes}):
        problems.append('duplicate hunter ids')
    out_skills = [s for s in skills_rows if not s['id'].startswith('sig_')] + sigs
    return heroes, out_skills, problems


def main(argv):
    heroes, skills_rows, problems = build()
    for p in problems:
        print('PROBLEM', p)
    if problems:
        return 1
    if '--check' in argv:
        print('ok: %d hunters, %d signature skills' % (len(heroes), sum(1 for s in skills_rows if s['id'].startswith('sig_'))))
        return 0
    changed = [n for n, rows in (('heroes', heroes), ('skills', skills_rows)) if write(n, rows)]
    print('written:', ', '.join(changed) or 'nothing changed')
    return 0


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
