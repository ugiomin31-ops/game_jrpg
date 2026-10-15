"""Offline inspection of the existing elite mushroom FBX; writes only processed/.

Run with the installed Blender --background --python ... -- analyze|render.
No generated or synthesized motion. Rendering evaluates the original FBX action.
"""
import argparse
import hashlib
import json
import math
from pathlib import Path
import sys

import bpy
import numpy as np
from mathutils import Vector

ROOT = Path(__file__).resolve().parents[1]
BASE = ROOT / 'ArtSource/enemies/elite_mushroom/enrichment_20261015'
OUT = BASE / 'processed'
SOURCE = BASE / 'raw/tripo_convert_d949cdaa-e88a-49f9-895a-cfd278c89c81.fbx'


def write_json(name, value):
    OUT.mkdir(exist_ok=True)
    (OUT / name).write_text(json.dumps(value, ensure_ascii=False, indent=2, allow_nan=False) + '\n', encoding='utf-8')


def hashes():
    result = []
    for entry in json.loads((BASE / 'raw-hashes.json').read_text(encoding='utf-8-sig')):
        path = BASE / entry['path']
        with path.open('rb') as source_file:
            digest = hashlib.file_digest(source_file, 'sha256').hexdigest()
        result.append(dict(path=entry['path'], bytes=path.stat().st_size, sha256=digest,
                           expected_sha256=entry['sha256'], matches=digest == entry['sha256']))
    if not all(item['matches'] for item in result):
        raise RuntimeError('Raw hash differs from retained manifest')
    return result


def load_source():
    bpy.ops.wm.read_factory_settings(use_empty=True)
    bpy.ops.import_scene.fbx(filepath=str(SOURCE), use_anim=True)
    rig, = [o for o in bpy.context.scene.objects if o.type == 'ARMATURE']
    mesh, = [o for o in bpy.context.scene.objects if o.type == 'MESH']
    action = rig.animation_data.action
    return rig, mesh, action


def curves(action):
    for layer in action.layers:
        for strip in layer.strips:
            for bag in strip.channelbags:
                yield from bag.fcurves


def vertices(mesh):
    obj = mesh.evaluated_get(bpy.context.evaluated_depsgraph_get())
    data = obj.to_mesh()
    try:
        return np.array([tuple(obj.matrix_world @ v.co) for v in data.vertices], dtype=np.float64)
    finally:
        obj.to_mesh_clear()


def analyze():
    before = hashes()
    write_json('raw-hashes-before.json', before)
    rig, mesh, action = load_source()
    names = [b.name for b in rig.pose.bones]
    frames = list(range(round(action.frame_range[0]), round(action.frame_range[1]) + 1))
    bpy.context.scene.frame_set(frames[0])
    reference = vertices(mesh)
    height = float(np.ptp(reference[:, 2]))
    sole_indices = []
    foot_regions = []
    for side in ('Left', 'Right'):
        group_ids = {g.index for g in mesh.vertex_groups if side in g.name and ('Foot' in g.name or 'Toe' in g.name)}
        ids = [v.index for v in mesh.data.vertices if sum(g.weight for g in v.groups if g.group in group_ids) > 0.5]
        if not ids:
            raise RuntimeError('No weighted foot region: ' + side)
        foot_regions.append(ids)
        low = float(np.percentile(reference[ids, 2], 20))
        sole_indices.append([i for i in ids if reference[i, 2] <= low])
    positions, rotations, soles, foot_z, bounds = [], [], [], [], []
    for frame in frames:
        bpy.context.scene.frame_set(frame)
        bpy.context.view_layer.update()
        positions.append([tuple(rig.matrix_world @ b.head) for b in rig.pose.bones])
        rotations.append([tuple(b.matrix_basis.to_quaternion()) for b in rig.pose.bones])
        coords = vertices(mesh)
        soles.append([coords[ids].mean(axis=0) for ids in sole_indices])
        foot_z.append([float(coords[ids, 2].min()) for ids in foot_regions])
        bounds.append([coords.min(axis=0), coords.max(axis=0)])
        if frame % 48 == 0:
            print('ANALYZE_FRAME', frame, flush=True)
    p, q, s, fz, bb = map(np.asarray, (positions, rotations, soles, foot_z, bounds))
    q /= np.linalg.norm(q, axis=2, keepdims=True)
    angles = 2 * np.arccos(np.clip(np.abs(np.sum(q[1:] * q[:-1], axis=2)), 0, 1)) * 180 / math.pi
    major = [i for i, n in enumerate(names) if not any(part in n.lower() for part in ('finger', 'thumb', 'index', 'middle', 'ring', 'pinky', 'toe'))]
    rms = np.sqrt(np.mean(angles[:, major] ** 2, axis=1))
    top = sorted(range(len(rms)), key=lambda i: float(rms[i]), reverse=True)[:35]
    curve_list = list(curves(action))
    key_times = sorted(set(round(float(k.co[0]), 5) for c in curve_list for k in c.keyframe_points))
    inventory = dict(source=str(SOURCE.relative_to(ROOT)), sha256=before[-1]['sha256'], blender=bpy.app.version_string,
                     fps=bpy.context.scene.render.fps / bpy.context.scene.render.fps_base,
                     action=action.name, frame_range=list(map(float, action.frame_range)), frame_count=len(frames),
                     fcurves=len(curve_list), unique_key_times=key_times, bones=names,
                     mesh_vertices=len(mesh.data.vertices), triangles=sum(len(p.vertices)-2 for p in mesh.data.polygons),
                     frame0_height_world=height, world_up='Z', foot_regions=[len(x) for x in foot_regions],
                     sole_marker_vertices=sole_indices,
                     metric_notes='Local bone quaternion step angles; fixed lowest 20% of foot-weighted vertices at frame 0 tracked through evaluated skin. No added motion.',
                     largest_pose_steps=[dict(from_frame=frames[i], to_frame=frames[i+1], major_rms_degrees=float(rms[i]),
                         max_degrees=float(angles[i].max()), max_bone=names[int(angles[i].argmax())]) for i in top])
    write_json('motion-analysis.json', inventory)
    write_json('frame-metrics.json', [dict(frame=frame, major_step_rms_degrees=0.0 if j==0 else float(rms[j-1]),
                foot_min_z=fz[j].tolist(), sole_centroids=s[j].tolist(), bounds=bb[j].tolist()) for j, frame in enumerate(frames)])
    np.savez_compressed(OUT / 'motion-samples.npz', frames=frames, positions=p, rotations=q, soles=s, foot_min_z=fz,
                        bounds=bb, names=names, height=height, fps=inventory['fps'])
    write_json('raw-hashes-after-analysis.json', hashes())
    print(json.dumps({k:inventory[k] for k in ('fps','frame_range','fcurves','frame0_height_world','largest_pose_steps')}, indent=2), flush=True)


def point_camera(obj, target):
    obj.rotation_euler = (Vector(target) - obj.location).to_track_quat('-Z', 'Y').to_euler()


def evidence():
    """Summarize original sampled data and binary FBX structure without reimport."""
    data = np.load(OUT / 'motion-samples.npz')
    p, q, soles, foot_z = [data[key].copy() for key in ('positions','rotations','soles','foot_min_z')]
    q /= np.linalg.norm(q, axis=2, keepdims=True)
    fps, height = float(data['fps']), float(data['height'])
    angles = np.rad2deg(2*np.arccos(np.clip(np.abs(np.sum(q[1:]*q[:-1],axis=2)),0,1)))
    displacements = np.linalg.norm(p[1:]-p[:-1],axis=2)
    major = [i for i,n in enumerate(data['names']) if not any(part in str(n).lower() for part in ('finger','thumb','index','middle','ring','pinky','toe'))]
    rms = np.sqrt(np.mean(angles[:,major]**2,axis=1))
    analysis = json.loads((OUT/'motion-analysis.json').read_text(encoding='utf-8'))
    analysis['largest_pose_steps'] = [dict(from_frame=int(i),to_frame=int(i+1),major_rms_degrees=float(rms[i]),
        max_degrees=float(angles[i].max()),max_bone=str(data['names'][angles[i].argmax()]))
        for i in sorted(range(len(rms)),key=lambda i:float(rms[i]),reverse=True)[:35]]
    analysis['rotation_normalization'] = 'All quaternion measurements normalized before acos, including this refreshed summary.'
    write_json('motion-analysis.json',analysis)
    frame_metrics=json.loads((OUT/'frame-metrics.json').read_text(encoding='utf-8'))
    for i,row in enumerate(frame_metrics):
        row['major_step_rms_degrees']=0.0 if i==0 else float(rms[i-1])
    write_json('frame-metrics.json',frame_metrics)
    moving = np.flatnonzero((angles.max(axis=1)>0.01) | (displacements.max(axis=1)>1e-6)) + 1
    final = len(p)-1
    floor = float(foot_z[0].min())
    speed = np.linalg.norm(np.diff(soles[:,:,:2],axis=0),axis=2)*fps
    height_limit, speed_limit = 0.02*height, 0.05*height
    grounded = foot_z <= floor+height_limit
    blocks = []
    for start,end in [(0,final),(0,53),(53,final),(54,60),(60,final)]:
        blocks.append(dict(start=start,end=end,
            max_bone_head_displacement_from_start=float(np.linalg.norm(p[start:end+1]-p[start],axis=2).max()),
            max_local_rotation_from_start_degrees=float(np.rad2deg(2*np.arccos(np.clip(np.abs(np.sum(q[start:end+1]*q[start],axis=2)),0,1))).max()),
            feet=[dict(side=side, lowest_surface_z_min=float(foot_z[start:end+1,i].min()),
                       lowest_surface_z_max=float(foot_z[start:end+1,i].max()),
                       near_floor_frames=int(grounded[start:end+1,i].sum()),
                       max_below_reference_floor=float(max(0,floor-foot_z[start:end+1,i].min())),
                       max_above_reference_floor=float(max(0,foot_z[start:end+1,i].max()-floor)),
                       low_speed_near_floor_transitions=int((grounded[start:end,i] & grounded[start+1:end+1,i] & (speed[start:end,i]<=speed_limit)).sum()),
                       max_sole_xy_speed=float(speed[start:end,i].max()),
                       near_floor_max_sole_xy_speed=float(speed[start:end,i][grounded[start:end,i] & grounded[start+1:end+1,i]].max()) if (grounded[start:end,i] & grounded[start+1:end+1,i]).any() else None,
                       sole_endpoint_distance=float(np.linalg.norm(soles[end,i]-soles[start,i]))) for i,side in enumerate(('Left','Right'))]))
    seams = []
    for start,end in [(0,53),(0,59),(0,60),(0,final),(60,final)]:
        a = np.rad2deg(2*np.arccos(np.clip(np.abs(np.sum(q[start]*q[end],axis=1)),0,1)))
        seams.append(dict(start=start,end=end,max_local_bone_angle_degrees=float(a.max()),
                          worst_bone=str(data['names'][a.argmax()]),rms_local_bone_angle_degrees=float(np.sqrt(np.mean(a*a))),
                          max_bone_head_distance=float(np.linalg.norm(p[end]-p[start],axis=1).max()),
                          sole_endpoint_distances=np.linalg.norm(soles[end]-soles[start],axis=1).tolist(),
                          bone_head_endpoint_velocity_mismatch=float(np.linalg.norm((p[start+1]-p[start] - (p[end]-p[end-1]))*fps,axis=1).max()),
                          note='Endpoint pose distance only; not approval to loop or proof of a clip boundary.'))
    from io_scene_fbx import parse_fbx
    tree, version = parse_fbx.parse(str(SOURCE))
    objects = next(e for e in tree.elems if e.id == b'Objects')
    names = {}
    curve_stats = []
    for elem in objects.elems:
        if elem.id in (b'AnimationStack',b'AnimationLayer'):
            names.setdefault(elem.id.decode(),[]).append(str(elem.props[1]))
        if elem.id == b'AnimationCurve':
            times = next((e.props[0] for e in elem.elems if e.id == b'KeyTime'), [])
            values = next((e.props[0] for e in elem.elems if e.id == b'KeyValueFloat'), [])
            if len(times) and len(times)==len(values):
                times = np.asarray(times,dtype=np.float64)/46186158000*fps
                values = np.asarray(values,dtype=np.float64)
                changed=np.flatnonzero(np.abs(np.diff(values))>1e-6)+1
                curve_stats.append(dict(id=int(elem.props[0]),keys=len(values),start=float(times[0]),end=float(times[-1]),
                    min=float(values.min()),max=float(values.max()),last_change_frame=float(times[changed[-1]]) if len(changed) else None,
                    changes_after_frame_60=int((times[changed]>60.0001).sum())))
    result=dict(fps=fps,frame_range=[0,final],blender=bpy.app.version_string,
        source_hash_confirmation=hashes(), raw_fbx_version=version, raw_animation_objects=names,
        nonconstant_raw_curves=sum(c['last_change_frame'] is not None for c in curve_stats),
        raw_curves_with_changes_after_60=sum(c['changes_after_frame_60']>0 for c in curve_stats),
        raw_last_changing_key_frame=max(c['last_change_frame'] for c in curve_stats if c['last_change_frame'] is not None),
        first_observed_pose_change_frame=int(moving[0]) if len(moving) else None,
        last_observed_pose_change_frame=int(moving[-1]) if len(moving) else None,
        movement_thresholds=dict(rotation_degrees=0.01,bone_head_world_distance=1e-6),
        floor_estimate_z=floor,reference_height_world=height,
        foot_contact_definition=dict(floor='Lower foot surface at neutral frame 0; estimate, not authored ground. Height differences are reported rather than corrected.',
            near_floor_height=height_limit,low_speed_xy_per_second=speed_limit,
            limitation='No authored contact flags. Low-speed near-floor samples are contact candidates; no categorical planted-foot claim.'),
        interval_metrics=blocks,endpoint_seams=seams,
        per_frame_max_rotation_degrees=angles.max(axis=1).tolist(),
        per_frame_max_bone_head_distance=displacements.max(axis=1).tolist())
    write_json('motion-evidence.json',result)
    write_json('raw-animation-curves.json',curve_stats)
    print(json.dumps({k:result[k] for k in ('raw_animation_objects','nonconstant_raw_curves','raw_curves_with_changes_after_60','last_observed_pose_change_frame','interval_metrics','endpoint_seams')},indent=2),flush=True)


def setup_render(mesh, frames, view):
    scene = bpy.context.scene
    scene.render.engine = 'CYCLES'
    scene.cycles.device = 'CPU'
    scene.cycles.samples = 12
    scene.cycles.use_denoising = True
    scene.render.threads_mode = 'FIXED'
    scene.render.threads = 4
    scene.render.resolution_x = 320
    scene.render.resolution_y = 320
    scene.render.resolution_percentage = 100
    scene.render.image_settings.file_format = 'PNG'
    scene.render.film_transparent = False
    scene.view_settings.view_transform = 'Standard'
    if scene.world is None:
        scene.world = bpy.data.worlds.new('InspectionWorld')
    scene.world.use_nodes = True
    scene.world.node_tree.nodes.get('Background').inputs[0].default_value = (0.14, 0.17, 0.21, 1)
    scene.world.node_tree.nodes.get('Background').inputs[1].default_value = 0.5
    # Correct only the temporary inspection material, retaining the raw basecolor.
    tex = next(SOURCE.parent.rglob('*basecolor.PNG'))
    material = bpy.data.materials.new('Inspection_Basecolor')
    material.use_nodes = True
    shader = material.node_tree.nodes.get('Principled BSDF')
    shader.inputs['Roughness'].default_value = 0.72
    image_node = material.node_tree.nodes.new('ShaderNodeTexImage')
    image_node.image = bpy.data.images.load(str(tex))
    material.node_tree.links.new(image_node.outputs['Color'], shader.inputs['Base Color'])
    mesh.data.materials.clear()
    mesh.data.materials.append(material)
    sample_data = np.load(OUT / 'motion-samples.npz')
    bbox = sample_data['bounds']
    lo, hi = bbox[:,0].min(axis=0), bbox[:,1].max(axis=0)
    size = float(max(hi-lo))
    center = (lo+hi)/2
    camera_data = bpy.data.cameras.new('InspectionCamera')
    camera = bpy.data.objects.new('InspectionCamera', camera_data)
    scene.collection.objects.link(camera)
    # Fixed world-axis inspection cameras; view names are labels, not a rig-forward contract.
    direction = Vector((0, 1, 0.20) if view == 'front' else (0.85, 1, 0.10)).normalized()
    camera.location = Vector(center) + direction * size * 4
    point_camera(camera, center)
    camera_data.type = 'ORTHO'
    camera_data.ortho_scale = size * 1.22
    scene.camera = camera
    label_data = bpy.data.curves.new('FrameLabel', 'FONT')
    label_data.size = camera_data.ortho_scale * 0.045
    label = bpy.data.objects.new('FrameLabel', label_data)
    scene.collection.objects.link(label)
    label.parent = camera
    label.location = (-camera_data.ortho_scale * 0.46, camera_data.ortho_scale * 0.43, -size)
    ink = bpy.data.materials.new('LabelInk')
    ink.use_nodes = True
    ink.node_tree.nodes.clear()
    emission = ink.node_tree.nodes.new('ShaderNodeEmission')
    emission.inputs['Color'].default_value = (0.8,0.9,1.0,1)
    output = ink.node_tree.nodes.new('ShaderNodeOutputMaterial')
    ink.node_tree.links.new(emission.outputs[0], output.inputs[0])
    label.data.materials.append(ink)
    for name, vector, energy in [('Key',(-2,3,4),180),('Fill',(3,1,2),90)]:
        light_data = bpy.data.lights.new(name, 'AREA')
        light_data.energy = energy * size * size
        light_data.shape = 'DISK'
        light_data.size = size * 3
        light = bpy.data.objects.new(name, light_data)
        scene.collection.objects.link(light)
        light.location = Vector(center) + Vector(vector) * size
        point_camera(light, center)
    # A reference plane supplies visible grounded shadows; it is never exported.
    floor_z = float(np.percentile(sample_data['foot_min_z'], 5))
    bpy.ops.mesh.primitive_plane_add(size=size*200, location=(0,0,floor_z-0.002))
    plane = bpy.context.object
    ground = bpy.data.materials.new('InspectionFloor')
    ground.diffuse_color = (0.20,0.23,0.27,1)
    plane.data.materials.append(ground)
    return scene


def contact_sheet(paths, destination, columns=6):
    rows = math.ceil(len(paths) / columns)
    tile_size = 320
    canvas = np.zeros((rows*tile_size, columns*tile_size, 4), dtype=np.float32)
    canvas[:,:,3] = 1
    for i, path in enumerate(paths):
        tile = bpy.data.images.load(str(path), check_existing=False)
        values = np.empty(tile_size*tile_size*4, dtype=np.float32)
        tile.pixels.foreach_get(values)
        y = (rows-1-i//columns)*tile_size
        x = (i%columns)*tile_size
        canvas[y:y+tile_size, x:x+tile_size] = values.reshape(tile_size,tile_size,4)
        bpy.data.images.remove(tile)
    sheet = bpy.data.images.new('ContactSheet', width=columns*tile_size, height=rows*tile_size, alpha=True)
    sheet.pixels.foreach_set(canvas.reshape(-1))
    sheet.filepath_raw = str(destination)
    sheet.file_format = 'PNG'
    sheet.save()
    bpy.data.images.remove(sheet)


def render(frames, tag, view):
    hashes()
    rig, mesh, action = load_source()
    setup_render(mesh, frames, view)
    directory = OUT / 'renders' / tag
    directory.mkdir(parents=True, exist_ok=True)
    rendered = []
    for frame in frames:
        bpy.context.scene.frame_set(frame)
        bpy.data.objects['FrameLabel'].data.body = f'Frame {frame} | {view}'
        path = directory / f'{view}-{frame:04d}.png'
        if not path.exists():
            bpy.context.scene.render.filepath = str(path)
            bpy.ops.render.render(write_still=True)
        rendered.append(dict(frame=frame, path=str(path.relative_to(ROOT))))
        print('RENDER_DONE', frame, path, flush=True)
    contact_sheet([ROOT/item['path'] for item in rendered], OUT / f'contact-sheet-{tag}-{view}.png')
    write_json(f'render-index-{tag}-{view}.json', rendered)
    write_json('raw-hashes-after-render.json', hashes())


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('mode', choices=['analyze','render','evidence'])
    parser.add_argument('--frames', default='')
    parser.add_argument('--tag', default='overview')
    parser.add_argument('--view', choices=['front','three-quarter'], default='front')
    args = parser.parse_args(sys.argv[sys.argv.index('--')+1:])
    OUT.mkdir(exist_ok=True)
    if args.mode == 'analyze':
        analyze()
    elif args.mode == 'evidence':
        evidence()
    else:
        render([int(f) for f in args.frames.split(',')], args.tag, args.view)


if __name__ == '__main__':
    main()
