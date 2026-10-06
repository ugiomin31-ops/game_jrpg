"""Publish all 20 weapons and 28 equipment displays from authored builders."""
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.join(HERE, '..', 'props'))
import _common as W
import swords
import arcane
import bows
import equipment


def main():
    selected = sys.argv[sys.argv.index('--') + 1:] if '--' in sys.argv else []
    report = []
    for category, builders in [('Weapons', swords.BUILDERS + arcane.BUILDERS + bows.BUILDERS),
                                ('Props/Equipment', equipment.BUILDERS)]:
        for ident, builder in builders:
            if selected and ident not in selected:
                continue
            W.A.reset_scene()
            obj = builder()
            W.export_items([(ident, obj)], category)
            W.A.save_blend('equipment_' + ident)
            W.preview_items([(ident, obj)], 'equipment_', {'_front': (90, 0, 0), '_detail': (72, 0, 35)}, size=640)
            report.append({'id': ident, 'category': category, 'triangles': W.tri_count(obj),
                           'dimensions': list(obj.dimensions), 'materials': [m.name for m in obj.data.materials]})
            print('GEAR_PUBLISHED ' + ident, flush=True)
    with open(os.path.join(W.A.BLEND_DIR, 'equipment_manifest.json'), 'w', encoding='utf-8') as stream:
        json.dump(report, stream, indent=2)
    print('GEAR_COMPLETE ' + str(len(report)), flush=True)


if __name__ == '__main__':
    main()
