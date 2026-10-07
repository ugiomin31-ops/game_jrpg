"""Produce every enemy data ID in isolated Blender processes, with saved-source and FBX reports.

Run from the repository root:
  C:/Users/User/Tools/Blender/blender.exe -b --factory-startup --python-exit-code 1 -P Blender/enemies_a/generate_all.py
Optional arguments after --: --only ID [ID ...], or --report-only to refresh aggregate
evidence from completed exports without rebuilding them. This is asset production, not a Unity test runner.
Logs and machine-readable production evidence are kept beside the generated .blend sources.
"""
import argparse
import json
from pathlib import Path
import runpy
import subprocess
import sys
import time

import bpy

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / 'Blender' / 'enemies_c'))
from roster import SOURCES as V2_SOURCES  # noqa: E402  (v2 roster: enemies_c generators)
BLENDER = ROOT / 'Blender'
REPORTS = BLENDER / 'blend'
REQUIRED = ('Idle', 'Run', 'Attack', 'Cast', 'Hit', 'Die', 'Victory')
SOURCES = {
    'slime': 'enemies_a/slime.py',
    'sprout': 'enemies_a/sprout.py',
    'coral_crab': 'enemies_a/coral_crab.py',
    'elite_coral_crab': 'enemies_a/coral_crab.py',
    'ice_wolf': 'enemies_a/ice_wolf.py',
    'elite_ice_wolf': 'enemies_a/ice_wolf.py',
    **{eid: 'enemies_a/forest_frost.py' for eid in (
        'bat', 'elite_bat', 'grave_bat', 'mushroom', 'elite_mushroom', 'jellyfish', 'penguin_mage')},
    'magma_slime': 'enemies_b/magma_slime.py',
    **{eid: 'enemies_b/ember_undead.py' for eid in (
        'fire_drake', 'elite_fire_drake', 'sand_golem', 'elite_sand_golem', 'phoenix',
        'skeleton', 'elite_skeleton', 'scarecrow', 'elite_scarecrow', 'wisp')},
    **{eid: f'bosses/{eid}.py' for eid in ('boss', 'forest_guardian', 'frost_kraken', 'flame_sphinx')},
    **V2_SOURCES,
}
sys.path.insert(0, str(ROOT / 'Blender' / 'enemies_d'))
import importlib.util  # noqa: E402
_v3 = importlib.util.spec_from_file_location('roster_v3', str(ROOT / 'Blender' / 'enemies_d' / 'roster.py'))
_v3m = importlib.util.module_from_spec(_v3)
_v3.loader.exec_module(_v3m)
SOURCES.update(_v3m.SOURCES)  # monster v3: sculpted bodies replace older generators


def data_roster():
    with (ROOT / 'Assets/_Game/Resources/Data/enemies.json').open(encoding='utf-8') as stream:
        rows = json.load(stream)
    roster = {row['id']: row for row in rows}
    if len(rows) != len(roster) or len(roster) != len(SOURCES):
        raise RuntimeError(f'Enemy data must contain exactly {len(SOURCES)} distinct IDs')
    if set(roster) != set(SOURCES):
        raise RuntimeError(f'Generator/data mismatch: missing={set(roster)-set(SOURCES)}, extra={set(SOURCES)-set(roster)}')
    if sum(row['is_boss'] for row in rows) != 4:
        raise RuntimeError('Enemy roster must contain exactly four bosses')
    return roster


def nonempty(path, started):
    if not path.is_file() or path.stat().st_size == 0 or path.stat().st_mtime < started - 2:
        raise RuntimeError(f'Missing, empty or stale production output: {path}')
    return {'path': str(path), 'bytes': path.stat().st_size}


def inspect_scene(required, imported=False):
    rig = bpy.data.objects.get('Rig')
    body = bpy.data.objects.get('Body')
    if rig is None or rig.type != 'ARMATURE' or body is None or body.type != 'MESH':
        raise RuntimeError('Expected articulated Rig armature and Body mesh')
    unexpected = [obj.name for obj in bpy.context.scene.objects if obj.type not in ('ARMATURE', 'MESH')]
    if unexpected:
        raise RuntimeError(f'Unexpected exported scene objects: {unexpected}')
    if not body.data.color_attributes.get('Col'):
        raise RuntimeError('Body is missing Col vertex colours')
    if not any(mod.type == 'ARMATURE' and mod.object == rig for mod in body.modifiers):
        raise RuntimeError('Body is not skinned to Rig')
    unweighted = sum(not any(group.weight > 0 for group in vertex.groups) for vertex in body.data.vertices)
    if unweighted:
        raise RuntimeError(f'{unweighted} Body vertices have no skin weights')
    mats = [mat.name for mat in body.data.materials]
    if any(mat.split('.')[0] not in ('M_Toon', 'M_Emit', 'M_Clear') for mat in mats):
        raise RuntimeError(f'Unexpected materials: {mats}')
    actions = {action.name.rsplit('|', 1)[-1] if imported else action.name: action for action in bpy.data.actions}
    missing = set(required) - set(actions)
    if missing:
        raise RuntimeError(f'Missing {"FBX takes" if imported else "source clips"}: {sorted(missing)}')
    clips = {name: [float(value) for value in actions[name].frame_range] for name in required}
    if any(last <= first for first, last in clips.values()):
        raise RuntimeError(f'Empty animation: {clips}')
    return {'objects': sorted(obj.name for obj in bpy.context.scene.objects),
            'triangles': sum(len(poly.vertices) - 2 for poly in body.data.polygons),
            'vertices': len(body.data.vertices), 'bones': len(rig.data.bones),
            'materials': mats, 'clips': clips, 'unweighted_vertices': unweighted}


def asset_command(eid):
    """Child process that produces one id: Blender binary, or the bpy-module Python when run as `python script.py`."""
    script = str(Path(__file__).resolve())
    if bpy.app.binary_path:
        return [bpy.app.binary_path, '-b', '--factory-startup', '--python-exit-code', '1', '-P', script, '--', '--asset', eid]
    return [sys.executable, script, '--', '--asset', eid]


def produce_one(eid, roster):
    started = time.time()
    source = BLENDER / SOURCES[eid]
    sys.path.insert(0, str(source.parent))
    sys.argv = [str(source), '--', eid]
    runpy.run_path(str(source), run_name='__main__')
    boss = roster[eid]['is_boss']
    prefix = ('boss_' if boss else 'enemy_') + eid
    fbx = ROOT / f'Assets/_Game/Resources/Art/Enemies/{eid}/{eid}.fbx'
    blend = REPORTS / f'{prefix}.blend'
    required = REQUIRED + (('Roar',) if boss else ())
    file_evidence = {'fbx': nonempty(fbx, started), 'blend': nonempty(blend, started)}
    suffixes = ('front', 'side', 'back', 'attack', 'cast', 'die') if boss else ('', 'side', 'attack', 'cast', 'die')
    if eid == 'forest_guardian':
        suffixes = ('front', 'side', 'back', 'attack_wind', 'attack_hit', 'cast', 'die', 'roar')
    previews = [BLENDER / 'preview' / f'{prefix}{"_"+suffix if suffix else ""}.png' for suffix in suffixes]
    file_evidence['previews'] = [nonempty(path, started) for path in previews]
    bpy.ops.wm.open_mainfile(filepath=str(blend))
    saved_scene = inspect_scene(required)
    bpy.ops.wm.read_factory_settings(use_empty=True)
    bpy.ops.import_scene.fbx(filepath=str(fbx))
    imported_scene = inspect_scene(required, imported=True)
    result = {'id': eid, 'is_boss': boss, 'generator': str(source),
              'blender_version': bpy.app.version_string,
              'produced_at_utc': time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime()),
              'files': file_evidence, 'saved_blend': saved_scene, 'reimported_fbx': imported_scene}
    with (REPORTS / f'enemy_production_{eid}.json').open('w', encoding='utf-8') as stream:
        json.dump(result, stream, ensure_ascii=False, indent=2)
    print('ENEMY_PRODUCTION ' + json.dumps(result), flush=True)


def main():
    args = sys.argv[sys.argv.index('--') + 1:] if '--' in sys.argv else []
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--asset', choices=SOURCES)
    parser.add_argument('--only', nargs='+', choices=SOURCES)
    parser.add_argument('--report-only', action='store_true')
    opts = parser.parse_args(args)
    roster = data_roster()
    REPORTS.mkdir(exist_ok=True)
    if opts.asset:
        produce_one(opts.asset, roster)
        return
    selected = [] if opts.report_only else (opts.only or list(roster))
    reports, failures = [], []
    for eid in selected:
        cmd = asset_command(eid)
        log_path = REPORTS / f'enemy_production_{eid}.log'
        print(f'PRODUCING {eid}: {" ".join(cmd)}', flush=True)
        with log_path.open('w', encoding='utf-8') as log:
            code = subprocess.run(cmd, cwd=str(ROOT), stdout=log, stderr=subprocess.STDOUT).returncode
        if code:
            failures.append({'id': eid, 'exit_code': code, 'log': str(log_path)})
            print(f'PRODUCTION_FAILED {eid} exit={code} log={log_path}', flush=True)
        else:
            with (REPORTS / f'enemy_production_{eid}.json').open(encoding='utf-8') as stream:
                reports.append(json.load(stream))
            print(f'PRODUCED {eid}', flush=True)
    # A targeted rebuild updates the roster report without discarding other completed exports.
    produced = {report['id']: report for report in reports}
    for eid in roster:
        report_path = REPORTS / f'enemy_production_{eid}.json'
        if eid in selected or not report_path.is_file():
            continue
        with report_path.open(encoding='utf-8') as stream:
            previous = json.load(stream)
        files = previous['files']
        evidence = [files['fbx'], files['blend'], *files['previews']]
        if previous['id'] == eid and all(
                Path(item['path']).is_file() and Path(item['path']).stat().st_size == item['bytes']
                for item in evidence):
            produced[eid] = previous
    reports = [produced[eid] for eid in roster if eid in produced]
    missing_ids = [eid for eid in roster if eid not in produced]
    budgets = {'normal_elite': [3000, 8000], 'boss': [10000, 25000]}
    deviations = []
    for report in reports:
        category = 'boss' if report['is_boss'] else 'normal_elite'
        lower, upper = budgets[category]
        triangles = report['saved_blend']['triangles']
        if not lower <= triangles <= upper:
            deviations.append({'id': report['id'], 'category': category,
                               'observed_triangles': triangles, 'documented_budget': [lower, upper],
                               'difference_from_nearest_limit': triangles-upper if triangles>upper else triangles-lower})
    summary = {'expected_ids': list(roster), 'rebuilt_ids': selected,
               'produced_ids': [report['id'] for report in reports],
               'missing_ids': missing_ids, 'coverage_complete': not missing_ids and not failures,
               'normal_elite_count': sum(not report['is_boss'] for report in reports),
               'boss_count': sum(report['is_boss'] for report in reports),
               'failures': failures, 'polygon_budgets_source': 'Blender/README.md',
               'polygon_budgets': budgets, 'budget_deviations': deviations, 'reports': reports}
    with (REPORTS / 'enemy_production_all.json').open('w', encoding='utf-8') as stream:
        json.dump(summary, stream, ensure_ascii=False, indent=2)
    print('ENEMY_PRODUCTION_ALL ' + json.dumps({key: value for key, value in summary.items() if key != 'reports'}), flush=True)
    if failures:
        raise RuntimeError(f'{len(failures)} enemy production failures; see exact logs above')


if __name__ == '__main__':
    main()
