"""Render production FBX geometry to transparent Unity sprites (no surrogate art).
Run: C:/Users/User/Tools/Blender/blender.exe -b --factory-startup -P Blender/ui/render_icons.py
Optional: -- Heroes/warrior Gear/sword_bronze (only render selected entries).
"""
import json
import math
from pathlib import Path
import sys

import bpy
from mathutils import Quaternion, Vector

ROOT = Path(__file__).resolve().parents[2]
ART = ROOT / 'Assets/_Game/Resources/Art'
OUTPUT = ROOT / 'Assets/_Game/Resources/Icons'
sys.path.insert(0, str(ROOT / 'Tools/ui'))
from asset_import import texture_meta

ELEMENTS = ('slash', 'blunt', 'pierce', 'fire', 'ice', 'thunder', 'dark', 'holy')
COMMANDS = ('attack', 'skill', 'ultimate', 'item', 'guard', 'flee', 'auto', 'gold', 'key', 'map', 'party', 'camp')
NPCS = ('innkeeper', 'shopkeeper', 'smith', 'guild_clerk', 'elder', 'villager_a', 'villager_b', 'villager_c')


def data_ids(name):
    return [row['id'] for row in json.loads((ROOT / 'Assets/_Game/Resources/Data' / (name + '.json')).read_text(encoding='utf-8'))]


def catalog():
    rows = []
    def add(family, ids, source):
        for ident in ids:
            rows.append((family, ident, ART / source(ident)))
    add('Heroes', data_ids('heroes'), lambda i: f'Characters/{i}/{i}.fbx')
    add('NPCs', NPCS, lambda i: f'NPCs/{i}/{i}.fbx')
    add('Enemies', data_ids('enemies'), lambda i: f'Enemies/{i}/{i}.fbx')
    add('Gear', data_ids('equipment'), lambda i: f'Weapons/{i}.fbx' if i.startswith(('sword_', 'staff_', 'bow_', 'mace_')) else f'Props/Equipment/{i}.fbx')
    add('Items', data_ids('items'), lambda i: f'Props/Items/{i}.fbx')
    add('Status', data_ids('statuses'), lambda i: f'Props/Status/{i}.fbx')
    add('Elements', ELEMENTS, lambda i: f'Props/Elements/{i}.fbx')
    add('UI', COMMANDS, lambda i: f'Props/UI/{i}.fbx')
    return rows


def render(family, ident, source):
    if not source.is_file():
        raise FileNotFoundError(source)
    # Reset all scene and data blocks per asset; animation takes are not loaded.
    bpy.ops.wm.read_factory_settings(use_empty=True)
    bpy.ops.import_scene.fbx(filepath=str(source), use_anim=False, use_custom_normals=True)
    scene = bpy.context.scene
    scene.frame_set(0)
    for obj in scene.objects:
        if obj.type == 'ARMATURE':
            obj.data.pose_position = 'REST'
    bpy.context.view_layer.update()
    meshes = [obj for obj in scene.objects if obj.type == 'MESH' and not obj.hide_render]
    if not meshes or any('Col' not in obj.data.color_attributes for obj in meshes):
        raise ValueError(f'{source}: missing production mesh or Col colors')
    deps = bpy.context.evaluated_depsgraph_get()
    points = []
    for obj in meshes:
        evaluated = obj.evaluated_get(deps)
        mesh = evaluated.to_mesh()
        points.extend(evaluated.matrix_world @ vertex.co for vertex in mesh.vertices)
        evaluated.to_mesh_clear()
    lo = Vector(tuple(min(p[a] for p in points) for a in range(3)))
    hi = Vector(tuple(max(p[a] for p in points) for a in range(3)))
    portrait = family in ('Heroes', 'NPCs')
    # Portrait includes the complete head/hair/hat and shoulder neckline, viewed front-on
    # so bangs, hat brims, and held props cannot hide either eye.
    if portrait:
        cutoff = lo.z + (hi.z - lo.z) * .48
        framed = [p for p in points if p.z >= cutoff]
    else:
        framed = points
    center = (lo + hi) / 2
    if portrait:
        head_lo = Vector(tuple(min(p[a] for p in framed) for a in range(3)))
        head_hi = Vector(tuple(max(p[a] for p in framed) for a in range(3)))
        center = (head_lo + head_hi) / 2
    direction = Vector((0, -1, 0)) if portrait or family in ('Status', 'Elements', 'UI') else Vector((.32, -1, .20)).normalized()
    flat_weapon = family == 'Gear' and ident.startswith(('sword_', 'bow_'))
    if flat_weapon:
        # Authored sword flats and bow curves lie in YZ: -Y is the edge, not the display face.
        direction = Vector((1, -.18, .08)).normalized()
    camera_data = bpy.data.cameras.new('ArtworkCamera')
    camera_data.type = 'ORTHO'
    camera = bpy.data.objects.new('ArtworkCamera', camera_data)
    scene.collection.objects.link(camera)
    camera.location = center + direction * max((hi - lo).length * 3, 4)
    camera.rotation_euler = (-direction).to_track_quat('-Z', 'Y').to_euler()
    if flat_weapon:
        camera.rotation_euler = (camera.rotation_euler.to_quaternion() @
            Quaternion((0, 0, 1), math.radians(-38))).to_euler()
    inverse = camera.rotation_euler.to_matrix().transposed()
    projected = [inverse @ (point - center) for point in framed]
    xlo, xhi = min(p.x for p in projected), max(p.x for p in projected)
    ylo, yhi = min(p.y for p in projected), max(p.y for p in projected)
    # Recenter using actual projected vertices, not approximate 3D sphere bounds.
    offset = camera.rotation_euler.to_matrix() @ Vector(((xlo + xhi) / 2, (ylo + yhi) / 2, 0))
    camera.location += offset
    camera_data.ortho_scale = max(xhi - xlo, yhi - ylo) * (1.12 if portrait else 1.16)
    camera_data.clip_end = 1000
    scene.camera = camera
    scene.render.engine = 'BLENDER_WORKBENCH'
    shading = scene.display.shading
    shading.light = 'STUDIO'
    shading.studiolight_rotate_z = math.radians(20)
    shading.color_type = 'VERTEX'
    shading.show_shadows = True
    shading.show_cavity = True
    shading.cavity_type = 'BOTH'
    shading.curvature_ridge_factor = 1.3
    shading.curvature_valley_factor = 1.05
    shading.show_object_outline = True
    shading.object_outline_color = (.055, .045, .08)
    shading.show_specular_highlight = True
    scene.display.render_aa = '32'
    scene.view_settings.view_transform = 'Standard'
    scene.view_settings.look = 'None'
    scene.render.film_transparent = True
    scene.render.resolution_x = scene.render.resolution_y = 512
    scene.render.resolution_percentage = 100
    scene.render.image_settings.file_format = 'PNG'
    scene.render.image_settings.color_mode = 'RGBA'
    scene.render.image_settings.color_depth = '8'
    output = OUTPUT / family / (ident + '.png')
    output.parent.mkdir(parents=True, exist_ok=True)
    scene.render.filepath = str(output)
    bpy.ops.render.render(write_still=True)
    texture_meta(output, sprite=True)
    record = dict(id=ident, family=family, source=source.relative_to(ROOT).as_posix(), output=output.relative_to(ROOT).as_posix(), framing='front head and shoulders' if portrait else 'complete silhouette', vertex_colors='Col', dimensions=[512, 512], transparent=True, camera=dict(type='ORTHO', position=list(camera.location), rotation=list(camera.rotation_euler), ortho_scale=camera_data.ortho_scale))
    print('ARTWORK_RENDERED ' + family + '/' + ident, flush=True)
    return record


def main():
    selection = set(sys.argv[sys.argv.index('--') + 1:]) if '--' in sys.argv else set()
    rows = catalog()
    expected = {'Heroes': 4, 'NPCs': 8, 'Enemies': 51, 'Gear': 48, 'Items': 30, 'Status': 22, 'Elements': 8, 'UI': 12}
    actual = {family: sum(row[0] == family for row in rows) for family in expected}
    if actual != expected:
        raise ValueError(f'Production data coverage changed: {actual}')
    manifest_path = OUTPUT / 'manifest.json'
    prior = json.loads(manifest_path.read_text(encoding='utf-8'))['assets'] if selection and manifest_path.exists() else []
    records = {(row['family'], row['id']): row for row in prior}
    for family, ident, source in rows:
        if selection and family + '/' + ident not in selection:
            continue
        records[family, ident] = render(family, ident, source)
        manifest = dict(generator='Blender/ui/render_icons.py', command='C:/Users/User/Tools/Blender/blender.exe -b --factory-startup -P Blender/ui/render_icons.py', coverage={f: sum(r['family'] == f for r in records.values()) for f in expected}, assets=list(records.values()))
        manifest_path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    print('ARTWORK_COMPLETE ' + str(len(records)), flush=True)


if __name__ == '__main__':
    main()
