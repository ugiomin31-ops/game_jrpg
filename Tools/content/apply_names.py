"""Writes the re-themed names from world/names_ko.py into the data files, in place.

    python3 Tools/content/apply_names.py            # rewrite display_name / description of listed ids
    python3 Tools/content/apply_names.py --check    # report only (no writes)

Targets: Assets/_Game/Resources/Data/equipment.json, items.json, jobs.json, enemies.json. Only rows whose id is listed
in names_ko are touched, and only the fields the entry gives (and the row already has). Files keep the formatting of
build_world.py (json.dumps indent=1, ensure_ascii, CRLF line endings, trailing CRLF), so an unchanged file is not
rewritten. Idempotent: a second run writes nothing.

Run it after build_world.py: that script regenerates enemies.json from spec and base data, which resets enemy names.
"""
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.normpath(os.path.join(HERE, '..', '..'))
DATA = os.path.join(ROOT, 'Assets', '_Game', 'Resources', 'Data')
sys.path.insert(0, HERE)

from world import names_ko  # noqa: E402

TABLES = [
    ('equipment', names_ko.EQUIPMENT),
    ('items', names_ko.ITEMS),
    ('jobs', names_ko.JOBS),
    ('enemies', names_ko.ENEMIES),
]
FIELDS = ('display_name', 'description')


def dumps(rows):
    return (json.dumps(rows, ensure_ascii=False, indent=1).replace('\n', '\r\n') + '\r\n').encode('utf-8')


def apply_table(name, table, write):
    """Returns (rows changed, listed ids missing from the file)."""
    path = os.path.join(DATA, name + '.json')
    with open(path, 'rb') as f:
        raw = f.read()
    rows = json.loads(raw.decode('utf-8'))
    by_id = {r['id']: r for r in rows}
    changed = set()
    for rid, new in table.items():
        row = by_id.get(rid)
        if row is None:
            continue
        for field in FIELDS:
            if field in new and field in row and row[field] != new[field]:
                row[field] = new[field]
                changed.add(rid)
    missing = sorted(rid for rid in table if rid not in by_id)
    data = dumps(rows)
    if changed and write and data != raw:
        with open(path, 'wb') as f:
            f.write(data)
    return len(changed), missing


def main(argv):
    write = '--check' not in argv
    status = 0
    for name, table in TABLES:
        n, missing = apply_table(name, table, write)
        print('%-10s listed %3d  renamed %3d  not in file %3d%s' % (
            name, len(table), n, len(missing), (' (' + ', '.join(missing) + ')') if missing and name != 'enemies' else ''))
    return status


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
