"""Render authored production geometry only; writes exclusively inside Store/.
Run via generate.py, or Blender --background --factory-startup --python this_file.
"""
import json
import math
import sys
from pathlib import Path

import bpy
from mathutils import Euler, Matrix, Vector

ROOT = Path(__file__).resolve().parents[2]
ART = ROOT / 'Assets/_Game/Resources/Art'
OUT = ROOT / 'Store/source'
OUT.mkdir(parents=True, exist_ok=True)
SOURCES = []


def material(slot):
    name = 'Store_' + slot.split('.')[0]
    found = bpy.data.materials.get(name)
    if found:
        return found
    mat = bpy.data.materials.new(name)
    mat.use_nodes = True
    tree = mat.node_tree
    bsdf = tree.nodes.get('Principled BSDF')
    vertex = tree.nodes.new('ShaderNodeVertexColor')
    vertex.layer_name = 'Col'
    tree.links.new(vertex.outputs['Color'], bsdf.inputs['Base Color'])
    bsdf.inputs['Roughness'].default_value = .64
    if slot.startswith('M_Emit'):
        tree.links.new(vertex.outputs['Color'], bsdf.inputs['Emission Color'])
        bsdf.inputs['Emission Strength'].default_value = 2.4
    if slot.startswith('M_Clear'):
        # Editorial still uses a solid jeweled surface to retain a clean silhouette.
        bsdf.inputs['Roughness'].default_value = .3
        bsdf.inputs['Metallic'].default_value = .18
    return mat


def load(source, label):
    path = ART / source
    before = set(bpy.context.scene.objects)
    bpy.ops.import_scene.fbx(filepath=str(path), use_anim=False)
    objects = list(set(bpy.context.scene.objects) - before)
    parent = bpy.data.objects.new(label, None)
    bpy.context.scene.collection.objects.link(parent)
    for obj in objects:
        if obj.name.startswith('Col_'):
            obj.hide_render = True
        obj.name = label + '_' + obj.name
        if obj.parent not in objects:
            obj.parent = parent
        if obj.type == 'MESH':
            if 'Col' not in obj.data.color_attributes:
                raise ValueError('Missing original Col colors: ' + str(path))
            for slot in obj.material_slots:
                slot.material = material(slot.material.name)
    bpy.context.view_layer.update()
    SOURCES.append({'id': label, 'source': path.relative_to(ROOT).as_posix(),
                    'mesh_objects': sum(o.type == 'MESH' for o in objects)})
    return parent, objects


def pose(rig, values):
    rig.animation_data_clear()
    rig.data.pose_position = 'POSE'
    for name, degrees in values.items():
        pb = rig.pose.bones.get(name)
        if pb is None:
            raise ValueError('Production pose bone missing: ' + name)
        basis = pb.bone.matrix_local.to_quaternion()
        pb.rotation_mode = 'QUATERNION'
        pb.rotation_quaternion = basis.inverted() @ Euler(tuple(math.radians(x) for x in degrees), 'XYZ').to_quaternion() @ basis
    bpy.context.view_layer.update()


def weapon(rig, source, bone):
    root, _ = load('Weapons/' + source + '.fbx', source)
    socket = rig.pose.bones[bone]
    root.parent = rig
    root.matrix_parent_inverse = Matrix.Identity(4)
    # Production weapon +Z extends along socket head -> tail (bone-local +Y).
    root.matrix_basis = socket.matrix @ Euler((-math.pi / 2, 0, 0)).to_matrix().to_4x4()
    # Bake the still attachment into a static transform, preserving editable meshes.
    return root


def light(name, location, energy, color, size, target):
    data = bpy.data.lights.new(name, 'AREA')
    data.energy, data.color, data.shape, data.size = energy, color, 'DISK', size
    obj = bpy.data.objects.new(name, data)
    bpy.context.scene.collection.objects.link(obj)
    obj.location = location
    obj.rotation_euler = (Vector(target) - obj.location).to_track_quat('-Z', 'Y').to_euler()


def setup(name, width, height):
    scene = bpy.data.scenes.new(name)
    bpy.context.window.scene = scene
    scene.render.engine = 'CYCLES'
    scene.cycles.samples = 32
    scene.cycles.use_denoising = True
    scene.render.resolution_x, scene.render.resolution_y = width, height
    scene.render.resolution_percentage = 100
    scene.render.image_settings.file_format = 'PNG'
    scene.render.image_settings.color_mode = 'RGBA'
    scene.render.film_transparent = True
    scene.world = bpy.data.worlds.new(name + '_World')
    scene.world.use_nodes = True
    background = scene.world.node_tree.nodes.get('Background')
    background.inputs['Color'].default_value = (.08, .15, .20, 1)
    background.inputs['Strength'].default_value = .45
    scene.view_settings.view_transform = 'AgX'
    scene.view_settings.look = 'AgX - Medium High Contrast'
    scene.render.filepath = str(OUT / (name + '.png'))
    return scene


def camera(target, location, scale=None):
    data = bpy.data.cameras.new('EditorialCamera')
    obj = bpy.data.objects.new('EditorialCamera', data)
    bpy.context.scene.collection.objects.link(obj)
    obj.location = location
    obj.rotation_euler = (Vector(target) - obj.location).to_track_quat('-Z', 'Y').to_euler()
    if scale:
        data.type, data.ortho_scale = 'ORTHO', scale
    else:
        data.lens = 35
    data.clip_end = 2000
    bpy.context.scene.camera = obj
    return obj


def frame_model(objects, direction, margin=1.14):
    points = []
    deps = bpy.context.evaluated_depsgraph_get()
    for obj in objects:
        if obj.type != 'MESH':
            continue
        evaluated = obj.evaluated_get(deps)
        mesh = evaluated.to_mesh()
        points.extend(evaluated.matrix_world @ vertex.co for vertex in mesh.vertices)
        evaluated.to_mesh_clear()
    lo = Vector(tuple(min(p[a] for p in points) for a in range(3)))
    hi = Vector(tuple(max(p[a] for p in points) for a in range(3)))
    center = (lo + hi) * .5
    direction = Vector(direction).normalized()
    cam = camera(center, center + direction * 15, 5)
    inverse = cam.rotation_euler.to_matrix().transposed()
    projected = [inverse @ (point - center) for point in points]
    xlo, xhi = min(p.x for p in projected), max(p.x for p in projected)
    ylo, yhi = min(p.y for p in projected), max(p.y for p in projected)
    cam.location += cam.rotation_euler.to_matrix() @ Vector(((xlo + xhi) / 2, (ylo + yhi) / 2, 0))
    scene = bpy.context.scene
    aspect = scene.render.resolution_x / scene.render.resolution_y
    cam.data.ortho_scale = max(yhi - ylo, (xhi - xlo) / aspect) * margin
    light('Dawn_Key', (-3, -6, 7), 1050, (1, .83, .57), 5, center)
    light('Teal_Rim', (4, 3, 5), 1450, (.15, .9, 1), 4, center)
    light('Portrait_Fill', (2, -5, 3), 450, (.75, .85, 1), 4, center)
    return center


def main():
    selected_heroes = tuple(arg.split('=', 1)[1] for arg in sys.argv if arg.startswith('--hero='))
    heroes_only = '--heroes-only' in sys.argv or bool(selected_heroes)
    selected_heroes = selected_heroes or ('warrior', 'mage', 'archer', 'cleric')
    if heroes_only:
        bpy.ops.wm.open_mainfile(filepath=str(OUT / 'abyss-key-art.blend'))
        SOURCES.extend(json.loads((OUT / 'asset-sources.json').read_text(encoding='utf-8')))
        weapons = {'warrior': 'sword_bronze', 'mage': 'staff_crystal', 'archer': 'bow_hunter', 'cleric': 'mace_silver'}
        replacing = set(selected_heroes) | {weapons[ident] for ident in selected_heroes}
        SOURCES[:] = [row for row in SOURCES if row['id'] not in replacing]
        bpy.context.window.scene = bpy.data.scenes['crypt-world']
        for ident in selected_heroes:
            bpy.data.scenes.remove(bpy.data.scenes[ident])
    else:
        bpy.ops.wm.read_factory_settings(use_empty=True)
    bpy.context.preferences.filepaths.save_version = 0
    poses = {
        'warrior': {'upper_arm.R': (-42, 4, -40), 'forearm.R': (-12, 0, 5),
                    'upper_arm.L': (-39, -7, 0), 'chest': (3, 0, -8), 'head': (-3, 0, 6)},
        'mage': {'upper_arm.R': (-46, 8, -20), 'forearm.R': (-12, 0, 0),
                 'upper_arm.L': (-42, -20, 0), 'forearm.L': (-31, 0, 0), 'head': (-4, 0, 0)},
        'archer': {'upper_arm.L': (-57, -12, -8), 'forearm.L': (-12, 0, 0),
                   'upper_arm.R': (-35, 28, 8), 'forearm.R': (-65, 0, -20), 'head': (0, 0, 3)},
        'cleric': {'upper_arm.R': (-48, 4, -18), 'forearm.R': (-12, 0, 0),
                   'upper_arm.L': (-30, -15, 0), 'forearm.L': (-25, 0, 0), 'head': (-4, 0, -4)},
    }
    equipped = {'warrior': ('sword_bronze', 'weapon.R'), 'mage': ('staff_crystal', 'weapon.R'),
                'archer': ('bow_hunter', 'weapon.L'), 'cleric': ('mace_silver', 'weapon.R')}
    for ident, values in poses.items():
        if heroes_only and ident not in selected_heroes:
            continue
        setup(ident, 1500, 1900)
        root, objects = load(f'Characters/{ident}/{ident}.fbx', ident)
        rig = next(obj for obj in objects if obj.type == 'ARMATURE')
        pose(rig, values)
        weapon(rig, *equipped[ident])
        bpy.context.view_layer.update()
        meshes = [obj for obj in bpy.context.scene.objects if obj.type == 'MESH']
        frame_model(meshes, (.13 if ident in ('mage', 'cleric') else -.17, -1, .06), 1.11)
        bpy.ops.render.render(write_still=True)
        print('STORE_PLATE ' + ident, flush=True)
    if not heroes_only:
        setup('abyss-antagonist', 2000, 2500)
        root, objects = load('Enemies/boss/boss.fbx', 'abyss_sorcerer')
        rig = next(obj for obj in objects if obj.type == 'ARMATURE')
        pose(rig, {'spine': (-4, 0, -4), 'head': (-3, 0, 4), 'upperarm.R': (-28, 0, 18),
                   'forearm.R': (-30, 0, 0), 'upperarm.L': (-12, 0, -8)})
        frame_model(objects, (-.08, -1, .035), 1.08)
        bpy.ops.render.render(write_still=True)
        print('STORE_PLATE abyss-antagonist', flush=True)
        scene = setup('crypt-world', 3840, 2160)
        load('Environment/haunted_crypt/arena.fbx', 'haunted_crypt_arena')
        gate, _ = load('Environment/haunted_crypt/boss_gate.fbx', 'haunted_crypt_gate')
        gate.location = (0, 5, 0)
        camera((0, 2, 2), (10, -19, 9))
        light('World_Dawn', (-6, -4, 12), 3200, (1, .66, .3), 8, (0, 2, 0))
        light('World_Teal', (3, 7, 11), 5000, (.12, .78, 1), 7, (0, 0, 1))
        bpy.ops.render.render(write_still=True)
        print('STORE_PLATE crypt-world', flush=True)
    bpy.context.window.scene = bpy.data.scenes['warrior']
    for scene in bpy.data.scenes:
        scene['purpose'] = 'Original authored 3D promotional illustration plate; not a gameplay screenshot'
    bpy.ops.wm.save_as_mainfile(filepath=str(OUT / 'abyss-key-art.blend'))
    (OUT / 'asset-sources.json').write_text(json.dumps(SOURCES, indent=2) + '\n', encoding='utf-8')
    print('STORE_NATIVE_SOURCE_COMPLETE', flush=True)


if __name__ == '__main__':
    main()
