"""Production export and render entry shared by hero/NPC generators.
The JSON report is generated from the actual authored scene, not hand-entered counts.
"""
import json
import math
import os
import bpy
from mathutils import Euler, Vector
from humanoid import A, V
from motion import create_actions
import textured as TX


def bounds(obj):
    deps = bpy.context.evaluated_depsgraph_get()
    evaluated = obj.evaluated_get(deps)
    mesh = evaluated.to_mesh()
    pts = [evaluated.matrix_world @ v.co for v in mesh.vertices]
    lo = [min(p[i] for p in pts) for i in range(3)]
    hi = [max(p[i] for p in pts) for i in range(3)]
    evaluated.to_mesh_clear()
    return dict(min=[round(x, 5) for x in lo], max=[round(x, 5) for x in hi],
                size=[round(hi[i] - lo[i], 5) for i in range(3)])


def motion_proof(H, actions, prefix, color_type="VERTEX"):
    """Render actual skinned takes at fixed scale/camera above a z=0 floor."""
    import numpy as np
    sc = bpy.context.scene
    size = 384
    frames_by_clip = dict(Guard=(0, 3, 6, 9, 12, 15, 18, 21, 24, 28, 32, 36),
                          Revive=(0, 4, 10, 15, 19, 24, 29, 34, 39, 49, 55, 60))
    evidence = {}
    # Record the actual evaluated poses before adding any proof-only geometry.
    def snapshot(clip, frame):
        H.rig.animation_data.action = actions[clip]
        sc.frame_set(frame)
        bpy.context.view_layer.update()
        return {b.name: tuple(b.location) + tuple(b.rotation_quaternion) + tuple(b.scale)
                for b in H.rig.pose.bones}

    transitions = {}
    for label, source, target in (('Die_to_Revive', ('Die', 30), ('Revive', 0)),
                                  ('Revive_to_Idle', ('Revive', 60), ('Idle', 0)),
                                  ('Idle_to_Guard', ('Idle', 0), ('Guard', 0)),
                                  ('Guard_to_Idle', ('Guard', 36), ('Idle', 0))):
        a, z = snapshot(*source), snapshot(*target)
        transitions[label] = max(abs(x - y) for bn in a for x, y in zip(a[bn], z[bn]))
    death = snapshot('Die', 30)
    evidence['transitions_max_local_component_delta'] = transitions
    evidence['die_final_root_location'] = list(death['root'][:3])
    evidence['clips'] = {}
    for clip in ('Die', 'Guard', 'Revive'):
        samples = []
        length = int(actions[clip].frame_range[1])
        for frame in range(length + 1):
            snapshot(clip, frame)
            samples.append(bounds(H.body)['min'][2])
        evidence['clips'][clip] = dict(sampled_frames=list(range(length + 1)),
                                       minimum_mesh_z=min(samples), maximum_mesh_min_z=max(samples))
    bpy.ops.mesh.primitive_plane_add(size=8, location=(0, -.3, -.001))
    floor = bpy.context.object
    floor.name = 'MotionProofFloor'
    colors = floor.data.color_attributes.new(name='Col', type='BYTE_COLOR', domain='CORNER')
    for color in colors.data:
        color.color_srgb = (.22, .25, .29, 1)
    camera_data = bpy.data.cameras.new('MotionProofCamera')
    camera_data.type = 'ORTHO'
    camera_data.ortho_scale = 2.2
    camera = bpy.data.objects.new('MotionProofCamera', camera_data)
    sc.collection.objects.link(camera)
    sc.camera = camera
    sc.render.engine = 'BLENDER_WORKBENCH'
    shading = sc.display.shading
    shading.light = 'STUDIO'
    shading.color_type = color_type
    shading.show_shadows = True
    shading.show_cavity = True
    shading.show_object_outline = True
    sc.render.resolution_x = size
    sc.render.resolution_y = size
    sc.render.resolution_percentage = 100
    sc.render.film_transparent = False
    digits = ('111101101101111', '010110010010111', '111001111100111',
              '111001111001111', '101101111001001', '111100111001111',
              '111100111101111', '111001001001001', '111101111101111',
              '111101111001111')
    evidence['sheets'] = []
    for clip, frames in frames_by_clip.items():
        for view, angle in (('threequarter', (75, 0, 22)), ('side', (85, 0, 90))):
            rotation = Euler(tuple(math.radians(a) for a in angle))
            camera.rotation_euler = rotation
            camera.location = Vector((0, -.45, .65)) + rotation.to_matrix() @ Vector((0, 0, 4))
            sheet = np.zeros((size * 3, size * 4, 4), dtype=np.float32)
            sheet[:, :, 3] = 1
            paths = []
            for index, frame in enumerate(frames):
                snapshot(clip, frame)
                path = os.path.join(A.PREVIEW_DIR, f'{prefix}_{clip.lower()}_{view}_f{frame:02}.png')
                sc.render.filepath = path
                bpy.ops.render.render(write_still=True)
                image = bpy.data.images.load(path, check_existing=False)
                pixels = np.empty(size * size * 4, dtype=np.float32)
                image.pixels.foreach_get(pixels)
                tile = pixels.reshape(size, size, 4)
                # Small raster frame numbers identify the real timeline keys.
                tile[size - 24:size - 2, 2:40] = (.035, .035, .035, 1)
                for digit_index, digit in enumerate(str(frame)):
                    for pixel_index, bit in enumerate(digits[int(digit)]):
                        if bit == '1':
                            row, col = divmod(pixel_index, 3)
                            y = size - 6 - row * 3
                            x = 6 + digit_index * 12 + col * 3
                            tile[y - 2:y + 1, x:x + 3] = (1, 1, 1, 1)
                row, col = divmod(index, 4)
                sheet[(2 - row) * size:(3 - row) * size, col * size:(col + 1) * size] = tile
                bpy.data.images.remove(image)
                paths.append(path)
            path = os.path.join(A.PREVIEW_DIR, f'{prefix}_{clip.lower()}_{view}_sheet.png')
            image = bpy.data.images.new('MotionProofSheet', width=size * 4, height=size * 3, alpha=True)
            image.pixels.foreach_set(sheet.ravel())
            image.filepath_raw = path
            image.file_format = 'PNG'
            image.save()
            bpy.data.images.remove(image)
            evidence['sheets'].append(dict(clip=clip, view=view, frames=list(frames), file=path, renders=paths))
    bpy.data.objects.remove(camera, do_unlink=True)
    bpy.data.cameras.remove(camera_data)
    bpy.data.objects.remove(floor, do_unlink=True)
    return evidence


def produce(name, builder, npc=False):
    """Builds, animates and exports one hero/NPC. Works for the vertex-colour chibi builders (costumes.py) and the
    textured anime builders (lib_anime/heroes_anime.py, which build their rig themselves): a body with image
    textures also writes <id>_tex/<material>.png next to the FBX (see textured.py)."""
    A.reset_scene()
    H = builder()
    if getattr(H, "rig", None) is None:
        H.build_rig()
    H.skin()
    textured = TX.is_textured(H.body)
    if textured:
        TX.remove_unused_slots(H.body)
    color_type = "TEXTURE" if textured else "VERTEX"
    actions = create_actions(H, npc)
    sc = bpy.context.scene
    sc.frame_set(0)
    bpy.context.view_layer.update()
    report = dict(id=name, category='NPCs' if npc else 'Characters', triangles=H.tris(),
                  bounds=bounds(H.body), bones=[b.name for b in H.rig.data.bones],
                  clips={n: dict(frames=list(a.frame_range), fps=30) for n, a in actions.items()},
                  contact=dict(Attack=.4, Cast=.6), sockets={})
    for s in ('R', 'L'):
        b = H.rig.data.bones['weapon.' + s]
        report['sockets']['weapon.' + s] = dict(head=list(b.head_local), tail=list(b.tail_local), parent=b.parent.name)
    prefix = ('npc_' if npc else 'hero_') + name
    rel = f"{report['category']}/{name}/{name}.fbx"
    if textured:
        report['fbx'], report['texture_dir'], report['textures'] = TX.export_textured_fbx(rel, H.body, H.rig)
    else:
        report['fbx'] = A.export_fbx(rel, [H.body, H.rig], animated=True)
    report['materials'] = [m.name for m in H.body.data.materials]
    report['previews'] = []
    for suffix, action, frame, angle in (('', 'Idle', 0, (78, 0, 22)), ('_front', 'Idle', 0, (90, 0, 0)),
                                        ('_attack', 'Attack', 10, (75, 0, 22)), ('_cast', 'Cast', 21, (75, 0, 22)),
                                        ('_die', 'Die', 30, (55, 0, 22)), ('_victory', 'Victory', 21, (78, 0, 22))):
        report['previews'].append(A.render_preview(prefix + suffix, [H.body], action=action, frame=frame, angle=angle,
                                                   size=768, color_type=color_type))
        H.rig.animation_data.action = actions[action]
        sc.frame_set(frame)
        bpy.context.view_layer.update()
        report.setdefault('pose_bounds', {})[action] = bounds(H.body)
    if not npc:
        for n, act in actions.items():
            clip = report['clips'][n]
            clip.update(take='Rig|' + n, seconds=(act.frame_range[1] - act.frame_range[0]) / 30,
                        loop=bool(act['loop']), authored_keyframes=list(act['authored_keyframes']))
            for prop in ('hold_normalized', 'recovery_normalized', 'start_pose', 'end_pose'):
                if prop in act:
                    value = act[prop]
                    clip[prop] = list(value) if prop == 'hold_normalized' else value
        report['motion_proof'] = motion_proof(H, actions, prefix, color_type)
    H.rig.animation_data.action = actions['Idle']
    sc.frame_set(0)
    bpy.context.view_layer.update()
    if textured:
        # Recoloured textures (gradient_map/tint) live only in memory: repack them so the .blend shows the hero.
        for img in {TX.image_of(m) for m in H.body.data.materials} - {None}:
            if img.is_dirty:
                img.pack()
    A.save_blend(prefix)
    report['blend'] = os.path.join(A.BLEND_DIR, prefix + '.blend')
    path = os.path.join(A.BLEND_DIR, prefix + '.json')
    with open(path, 'w', encoding='utf-8') as f:
        json.dump(report, f, indent=2)
    print('HUMANOID_PRODUCTION ' + json.dumps(report), flush=True)
    return report
