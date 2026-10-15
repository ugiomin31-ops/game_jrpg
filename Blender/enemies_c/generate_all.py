"""Produce the v2 monster roster (enemies_c) with the same per-id evidence as enemies_a/generate_all.py.

Each id is built in its own process through `enemies_a/generate_all.py --asset ID` (generator -> FBX, .blend,
5 previews -> reopen the .blend and re-import the FBX, check Rig/Body/Col/weights/materials/7 clips), then the
v2 results are aggregated into Blender/blend/enemy_v2_production_all.json (budget: normal <= 10k, elite <= 14k tris).

  blender -b --factory-startup --python-exit-code 1 -P Blender/enemies_c/generate_all.py [-- --only ID ...]
  python Blender/enemies_c/generate_all.py [-- --only ID ...]        (bpy as a Python module)
"""
import argparse
import json
from pathlib import Path
import subprocess
import sys

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
REPORTS = ROOT / 'Blender' / 'blend'
sys.path.insert(0, str(HERE))
from roster import ROSTER  # noqa: E402

BUDGET = {'normal': 10000, 'elite': 14000}


def command(eid):
    script = str(ROOT / 'Blender' / 'enemies_a' / 'generate_all.py')
    try:
        import bpy
        binary = bpy.app.binary_path
    except ImportError:
        binary = ''
    if binary:
        return [binary, '-b', '--factory-startup', '--python-exit-code', '1', '-P', script, '--', '--asset', eid]
    return [sys.executable, script, '--', '--asset', eid]


def main():
    args = sys.argv[sys.argv.index('--') + 1:] if '--' in sys.argv else []
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--only', nargs='+', choices=sorted(ROSTER))
    parser.add_argument('--report-only', action='store_true')
    opts = parser.parse_args(args)
    selected = [] if opts.report_only else (opts.only or list(ROSTER))
    failures = []
    for eid in selected:
        log = REPORTS / f'enemy_production_{eid}.log'
        print(f'PRODUCING {eid}', flush=True)
        with log.open('w', encoding='utf-8') as stream:
            code = subprocess.run(command(eid), cwd=str(ROOT), stdout=stream, stderr=subprocess.STDOUT).returncode
        if code:
            failures.append({'id': eid, 'exit_code': code, 'log': str(log)})
            print(f'PRODUCTION_FAILED {eid} exit={code} log={log}', flush=True)
    rows, over = [], []
    for eid, (module, name, biome, floors, role) in ROSTER.items():
        path = REPORTS / f'enemy_production_{eid}.json'
        if not path.is_file():
            failures.append({'id': eid, 'missing_report': str(path)})
            continue
        rep = json.loads(path.read_text(encoding='utf-8'))
        tris = rep['reimported_fbx']['triangles']
        kind = 'elite' if eid.startswith('elite_') else 'normal'
        if tris > BUDGET[kind]:
            over.append({'id': eid, 'triangles': tris, 'budget': BUDGET[kind]})
        rows.append({'id': eid, 'name_ko': name, 'biome': biome, 'floors': floors, 'role': role, 'generator': f'enemies_c/{module}.py',
                     'triangles': tris, 'bones': rep['reimported_fbx']['bones'], 'materials': rep['reimported_fbx']['materials'],
                     'clips': rep['reimported_fbx']['clips'], 'fbx': rep['files']['fbx']})
    summary = {'roster': list(ROSTER), 'produced': [r['id'] for r in rows], 'failures': failures,
               'budget': BUDGET, 'over_budget': over, 'reports': rows}
    (REPORTS / 'enemy_v2_production_all.json').write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding='utf-8')
    for r in rows:
        print(f"V2 {r['id']:<20} {r['triangles']:>6} tris  {r['bones']:>2} bones  {r['name_ko']} ({r['biome']} {r['floors']})", flush=True)
    print('ENEMY_V2_PRODUCTION ' + json.dumps({'produced': len(rows), 'failures': failures, 'over_budget': over}, ensure_ascii=False), flush=True)
    if failures:
        raise SystemExit(1)


if __name__ == '__main__':
    main()
