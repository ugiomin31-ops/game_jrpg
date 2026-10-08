"""Render production FBX geometry to transparent Unity sprites (no surrogate art).
Run: C:/Users/User/Tools/Blender/blender.exe -b --factory-startup -P Blender/ui/render_icons.py
Optional: -- Heroes/warrior Gear/sword_bronze (only render selected entries).
"""
import json
import math
from pathlib import Path
import sys

import bpy
import numpy as np
from mathutils import Quaternion, Vector

ROOT = Path(__file__).resolve().parents[2]
ART = ROOT / 'Assets/_Game/Resources/Art'
OUTPUT = ROOT / 'Assets/_Game/Resources/Icons'
sys.path.insert(0, str(ROOT / 'Tools/ui'))
from asset_import import texture_meta

ELEMENTS = ('slash', 'blunt', 'pierce', 'fire', 'ice', 'thunder', 'dark', 'holy')
PORTRAIT_EXPOSURE = .55
COMMANDS = ('attack', 'skill', 'ultimate', 'item', 'guard', 'flee', 'auto', 'gold', 'key', 'map', 'party', 'camp')
NPCS = ('innkeeper', 'shopkeeper', 'smith', 'guild_clerk', 'elder', 'villager_a', 'villager_b', 'villager_c')


def data_ids(name):
    return [row['id'] for row in json.loads((ROOT / 'Assets/_Game/Resources/Data' / (name + '.json')).read_text(encoding='utf-8'))]


def catalog():
    rows = []
    def add(family, ids, source):
        for ident in ids:
            rows.append((family, ident, ART / source(ident)))
    heroes = data_ids('heroes')
    # Promoted job outfits (jobs.json rows that are not a base hero) get portraits framed like the heroes.
    add('Heroes', heroes + [j for j in data_ids('jobs') if j not in heroes], lambda i: f'Characters/{i}/{i}.fbx')
    add('NPCs', NPCS, lambda i: f'NPCs/{i}/{i}.fbx')
    add('Enemies', data_ids('enemies'), lambda i: f'Enemies/{i}/{i}.fbx')
    add('Gear', data_ids('equipment'), lambda i: f'Weapons/{i}.fbx' if i.startswith(('sword_', 'staff_', 'bow_', 'mace_')) else f'Props/Equipment/{i}.fbx')
    add('Items', data_ids('items'), lambda i: f'Props/Items/{i}.fbx')
    add('Status', data_ids('statuses'), lambda i: f'Props/Status/{i}.fbx')
    add('Elements', ELEMENTS, lambda i: f'Props/Elements/{i}.fbx')
    add('UI', COMMANDS, lambda i: f'Props/UI/{i}.fbx')
    return rows


def textured_shading(meshes):
    """Textured anime heroes (lib_humanoid/textured.py): image materials show their PNG; the procedural parts
    (M_Toon/M_Emit/M_Clear, coloured by Col) get their average Col as the flat material colour Workbench uses
    for materials without an image. Returns False for ordinary vertex-colour models."""
    def has_image(mat):
        return mat is not None and mat.use_nodes and any(n.type == 'TEX_IMAGE' and n.image for n in mat.node_tree.nodes)
    if not any(has_image(slot.material) for obj in meshes for slot in obj.material_slots):
        return False
    sums = {}
    for obj in meshes:
        col = obj.data.color_attributes['Col']
        for poly in obj.data.polygons:
            mat = obj.material_slots[poly.material_index].material if poly.material_index < len(obj.material_slots) else None
            if mat is None or has_image(mat):
                continue
            acc = sums.setdefault(mat.name, [0.0, 0.0, 0.0, 0])
            for li in poly.loop_indices:
                c = col.data[li].color if col.domain == 'CORNER' else col.data[obj.data.loops[li].vertex_index].color
                acc[0] += c[0]; acc[1] += c[1]; acc[2] += c[2]; acc[3] += 1
    for name, (r, g, b, n) in sums.items():
        if n:
            bpy.data.materials[name].diffuse_color = (r / n, g / n, b / n, 1.0)
    return True


def _pixels(path):
    image = bpy.data.images.load(str(path), check_existing=False)
    data = np.empty(len(image.pixels), dtype=np.float32)
    image.pixels.foreach_get(data)
    bpy.data.images.remove(image)
    return data.reshape(-1, 4)


def cel_portrait(scene, output):
    """Anime hero portraits: painted textures (face, hair, clothes) come from a flat-lit pass so skin keeps its
    colour, while untextured armour and props keep the studio-lit pass so they still read as solid shapes.
    A third pass masks which pixels are textured."""
    shading = scene.display.shading
    lit = _pixels(output)
    shading.light = 'FLAT'
    exposure = scene.view_settings.exposure
    scene.view_settings.exposure = 0
    bpy.ops.render.render(write_still=True)
    flat = _pixels(output)
    saved = {}
    for mat in bpy.data.materials:
        textured = mat.use_nodes and any(n.type == 'TEX_IMAGE' and n.image for n in mat.node_tree.nodes)
        saved[mat.name] = tuple(mat.diffuse_color)
        mat.diffuse_color = (1, 1, 1, 1) if textured else (0, 0, 0, 1)
    shading.color_type = 'MATERIAL'
    shading.show_object_outline = False
    render_aa = scene.display.render_aa
    bpy.ops.render.render(write_still=True)
    mask = _pixels(output)[:, :1]
    for mat in bpy.data.materials:
        mat.diffuse_color = saved[mat.name]
    shading.color_type = 'TEXTURE'
    shading.show_object_outline = True
    shading.light = 'STUDIO'
    scene.view_settings.exposure = exposure
    scene.display.render_aa = render_aa
    out = lit.copy()
    out[:, :3] = flat[:, :3] * mask + lit[:, :3] * (1 - mask)
    out[:, 3] = np.maximum(lit[:, 3], flat[:, 3])
    image = bpy.data.images.new('CelPortrait', scene.render.resolution_x, scene.render.resolution_y, alpha=True)
    image.pixels.foreach_set(out.ravel())
    image.filepath_raw = str(output)
    image.file_format = 'PNG'
    image.save()
    bpy.data.images.remove(image)


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
        # Full-height (anime) figures: keep head and shoulders only, or the face shrinks to a dot on the cards.
        cutoff = lo.z + (hi.z - lo.z) * (.76 if hi.z - lo.z > 1.45 else .48)
        framed = [p for p in points if p.z >= cutoff]
        if hi.z - lo.z > 1.45:
            # Wings, rune rings and long horns would widen the frame until the face is a dot: frame the
            # head-and-shoulders column only and let the rest crop at the edges.
            framed = [p for p in framed if abs(p.x) <= .30] or framed
    else:
        framed = points
    center = (lo + hi) / 2
    if portrait:
        head_lo = Vector(tuple(min(p[a] for p in framed) for a in range(3)))
        head_hi = Vector(tuple(max(p[a] for p in framed) for a in range(3)))
        center = (head_lo + head_hi) / 2
    direction = Vector((.18, -1, .03)).normalized() if portrait and hi.z - lo.z > 1.45 else Vector((0, -1, 0)) if portrait or family in ('Status', 'Elements', 'UI') else Vector((.32, -1, .20)).normalized()
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
    textured = textured_shading(meshes)
    shading.color_type = 'TEXTURE' if textured else 'VERTEX'
    # Anime heroes carry painted shading in their textures: studio light + cavity turned the skin grey,
    # so their portraits render the texture colours flat with the ink outline, like a cel illustration.
    cel = portrait and textured
    shading.show_shadows = not cel
    shading.show_cavity = not cel
    shading.cavity_type = 'BOTH'
    shading.curvature_ridge_factor = 1.3
    shading.curvature_valley_factor = 1.05
    shading.show_object_outline = True
    shading.object_outline_color = (.055, .045, .08)
    shading.show_specular_highlight = True
    scene.display.render_aa = '32'
    scene.view_settings.view_transform = 'Standard'
    if cel:
        scene.view_settings.exposure = PORTRAIT_EXPOSURE
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
    if cel:
        cel_portrait(scene, output)
    texture_meta(output, sprite=True)
    record = dict(id=ident, family=family, source=source.relative_to(ROOT).as_posix(), output=output.relative_to(ROOT).as_posix(), framing='front head and shoulders' if portrait else 'complete silhouette', vertex_colors='Col', dimensions=[512, 512], transparent=True, camera=dict(type='ORTHO', position=list(camera.location), rotation=list(camera.rotation_euler), ortho_scale=camera_data.ortho_scale))
    print('ARTWORK_RENDERED ' + family + '/' + ident, flush=True)
    return record


def main():
    selection = set(sys.argv[sys.argv.index('--') + 1:]) if '--' in sys.argv else set()
    rows = catalog()
    expected = {'Heroes': 20, 'NPCs': 8, 'Enemies': 51, 'Gear': 48, 'Items': 30, 'Status': 22, 'Elements': 8, 'UI': 12}
    # A selective render (-- Heroes/knight ...) only requires the coverage of the families it touches.
    families = [f for f in expected if not selection or any(item.startswith(f + '/') for item in selection)]
    actual = {family: sum(row[0] == family for row in rows) for family in families}
    if actual != {family: expected[family] for family in families}:
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
