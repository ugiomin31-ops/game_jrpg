"""Read-only Cast FBX inspection; outputs only cast/processed.

Run in Blender --background --threads 4 --python this_file -- analyze|render.
Imports a byte-identical staging copy, never the retained raw source. No motion
is authored, retimed, trimmed, or exported. Renders evaluate the imported take.
"""
import argparse
import hashlib
import importlib.util
import json
import math
from pathlib import Path
import sys
import zipfile

import bpy
import numpy as np

ROOT = Path(__file__).resolve().parents[1]
BASE = ROOT / 'ArtSource/enemies/elite_mushroom/enrichment_20261015/individual-motion-exports/cast'
OUT = BASE / 'processed'
SOURCE = OUT / 'source-input/tripo_convert_5a303303-ca4a-4913-b018-a1250767306b.fbx'
spec = importlib.util.spec_from_file_location('mushroom_inspection', Path(__file__).with_name('inspect_elite_mushroom_motions.py'))
shared = importlib.util.module_from_spec(spec)
spec.loader.exec_module(shared)
shared.BASE, shared.OUT, shared.SOURCE = BASE, OUT, SOURCE


def write(name, value):
    (OUT / name).write_text(json.dumps(value, ensure_ascii=False, indent=2, allow_nan=False) + '\n', encoding='utf-8')


def hashes():
    manifest = json.loads((OUT / 'raw-hashes-before.json').read_text(encoding='utf-8-sig'))
    result = []
    for item in manifest:
        path = BASE / item['path']
        digest = hashlib.sha256(path.read_bytes()).hexdigest()
        matches = digest == item['sha256'] and path.stat().st_size == item['bytes']
        result.append(dict(**item, matches=matches))
        if not matches:
            raise RuntimeError('Raw source changed: ' + str(path))
    return result


shared.hashes = hashes


def native_fbx(fps):
    from io_scene_fbx import parse_fbx
    tree, version = parse_fbx.parse(str(SOURCE))
    objects = next(e for e in tree.elems if e.id == b'Objects')
    ticks = 46186158000

    def scalar(value):
        if isinstance(value, bytes):
            return value.decode('utf-8', errors='replace').replace('\x00\x01', ' / ')
        if hasattr(value, 'tolist'):
            return value.tolist()
        return value

    def properties(element):
        props = next((e for e in element.elems if e.id == b'Properties70'), None)
        return {scalar(e.props[0]): [scalar(p) for p in e.props[4:]] for e in props.elems} if props else {}

    stacks, curves = [], []
    for elem in objects.elems:
        if elem.id == b'AnimationStack':
            stacks.append(dict(name=scalar(elem.props[1]), properties=properties(elem)))
        if elem.id != b'AnimationCurve':
            continue
        times = next((e.props[0] for e in elem.elems if e.id == b'KeyTime'), [])
        values = next((e.props[0] for e in elem.elems if e.id == b'KeyValueFloat'), [])
        if not len(times):
            continue
        t = np.asarray(times, dtype=np.float64) / ticks * fps
        v = np.asarray(values, dtype=np.float64)
        changed = np.flatnonzero(np.abs(np.diff(v)) > 1e-6) + 1
        curves.append(dict(id=int(elem.props[0]), key_count=len(t), start=float(t.min()), end=float(t.max()),
                           min_value=float(v.min()), max_value=float(v.max()),
                           changing_key_frames=t[changed].tolist()))
    take_node = next((e for e in tree.elems if e.id == b'Takes'), None)

    def node(element):
        return dict(id=scalar(element.id), props=[scalar(v) for v in element.props],
                    children=[node(e) for e in element.elems])

    global_node = next((e for e in tree.elems if e.id == b'GlobalSettings'), None)
    write('raw-animation-curves.json', curves)
    changing = [f for c in curves for f in c['changing_key_frames']]
    return dict(version=version, ticks_per_second=ticks, frame_rate=fps,
                stacks=stacks, takes=node(take_node) if take_node else None,
                global_settings=properties(global_node) if global_node else {},
                key_frame_range=[min(c['start'] for c in curves), max(c['end'] for c in curves)],
                nonconstant_curves=sum(bool(c['changing_key_frames']) for c in curves),
                changing_key_frame_range=[min(changing), max(changing)] if changing else None,
                curves_changing_after_native_52=sum(any(f > 52.0001 for f in c['changing_key_frames']) for c in curves))


def analyze():
    before = hashes()
    raw_fbx = next(x for x in before if x['path'].endswith('.fbx'))
    if hashlib.sha256(SOURCE.read_bytes()).hexdigest() != raw_fbx['sha256']:
        raise RuntimeError('Staged FBX is not byte-identical to raw')
    with zipfile.ZipFile(BASE / 'elite_mushroom_cast_only.zip') as archive:
        members = []
        for entry in archive.infolist():
            if entry.is_dir():
                continue
            digest = hashlib.sha256(archive.read(entry)).hexdigest()
            raw = BASE / 'raw' / entry.filename
            members.append(dict(path=entry.filename, bytes=entry.file_size, sha256=digest,
                                matches_extracted_raw=raw.is_file() and hashlib.sha256(raw.read_bytes()).hexdigest() == digest))
        if not all(x['matches_extracted_raw'] for x in members):
            raise RuntimeError('Archive member does not match raw extraction')
        write('archive-verification.json', members)
    rig, mesh, action = shared.load_source()
    frames = list(range(round(action.frame_range[0]), round(action.frame_range[1]) + 1))
    fps = bpy.context.scene.render.fps / bpy.context.scene.render.fps_base
    bpy.context.scene.frame_set(frames[0])
    reference = shared.vertices(mesh)
    height = float(np.ptp(reference[:, 2]))
    foot_regions, soles = [], []
    for side in ('Left', 'Right'):
        groups = {g.index for g in mesh.vertex_groups if side in g.name and ('Foot' in g.name or 'Toe' in g.name)}
        ids = [v.index for v in mesh.data.vertices if sum(g.weight for g in v.groups if g.group in groups) > 0.5]
        if not ids:
            raise RuntimeError('No foot region for ' + side)
        foot_regions.append(ids)
        low = np.percentile(reference[ids, 2], 20)
        soles.append([i for i in ids if reference[i, 2] <= low])
    names = [bone.name for bone in rig.pose.bones]
    positions, rotations, feet, foot_z, bounds, root_matrices = [], [], [], [], [], []
    surface_step, surface_from_start = [], []
    previous = reference
    for frame in frames:
        bpy.context.scene.frame_set(frame)
        bpy.context.view_layer.update()
        positions.append([tuple(rig.matrix_world @ b.head) for b in rig.pose.bones])
        rotations.append([tuple(b.matrix_basis.to_quaternion()) for b in rig.pose.bones])
        coords = shared.vertices(mesh)
        feet.append([coords[ids].mean(axis=0) for ids in soles])
        foot_z.append([float(coords[ids, 2].min()) for ids in foot_regions])
        bounds.append([coords.min(axis=0), coords.max(axis=0)])
        root_matrices.append([list(row) for row in rig.matrix_world])
        surface_step.append(float(np.linalg.norm(coords - previous, axis=1).max()))
        surface_from_start.append(float(np.linalg.norm(coords - reference, axis=1).max()))
        previous = coords
        if frame % 48 == 0:
            print('ANALYZE_FRAME', frame, flush=True)
    p, q, s, fz, bb = map(np.asarray, (positions, rotations, feet, foot_z, bounds))
    q /= np.linalg.norm(q, axis=2, keepdims=True)
    angles = np.rad2deg(2 * np.arccos(np.clip(np.abs(np.sum(q[1:] * q[:-1], axis=2)), 0, 1)))
    dp = np.linalg.norm(np.diff(p, axis=0), axis=2)
    moving = np.flatnonzero((angles.max(axis=1) > 0.01) | (dp.max(axis=1) > 1e-6)) + 1
    floor = float(fz[0].min())
    grounded = fz <= floor + 0.02 * height
    speed = np.linalg.norm(np.diff(s[:, :, :2], axis=0), axis=2) * fps
    major = [i for i,n in enumerate(names) if not any(t in n.lower() for t in ('finger','thumb','index','middle','ring','pinky','toe'))]
    rms = np.sqrt(np.mean(angles[:, major] ** 2, axis=1))
    metrics = []
    for i, frame in enumerate(frames):
        metrics.append(dict(frame=frame, take_elapsed_seconds=(frame-frames[0])/fps,
                            max_local_step_degrees=0 if i == 0 else float(angles[i-1].max()),
                            major_step_rms_degrees=0 if i == 0 else float(rms[i-1]),
                            max_bone_step=0 if i == 0 else float(dp[i-1].max()),
                            max_surface_step=surface_step[i], max_surface_from_start=surface_from_start[i],
                            foot_min_z=fz[i].tolist(), sole_centroids=s[i].tolist(), bounds=bb[i].tolist()))
    blocks = []
    for start, end in [(0, len(frames)-1), (min(53,len(frames)-1), len(frames)-1)]:
        blocks.append(dict(frames=[frames[start],frames[end]],
                           max_bone_displacement_from_interval_start=float(np.linalg.norm(p[start:end+1]-p[start],axis=2).max()),
                           moving_transitions=int(((angles[start:end].max(axis=1) > .01) | (dp[start:end].max(axis=1) > 1e-6)).sum()),
                           total_transitions=end-start))
    contact = []
    for i,side in enumerate(('Left','Right')):
        near = grounded[:-1,i] & grounded[1:,i]
        low = near & (speed[:,i] <= 0.05 * height)
        fastest = int(np.argmax(np.where(near, speed[:,i], -1)))
        contact.append(dict(side=side, weighted_vertices=len(foot_regions[i]), sole_marker_vertices=len(soles[i]),
                            foot_z_range=[float(fz[:,i].min()),float(fz[:,i].max())],
                            max_below_reference_floor=float(max(0,floor-fz[:,i].min())),
                            max_above_reference_floor=float(max(0,fz[:,i].max()-floor)),
                            near_floor_frames=int(grounded[:,i].sum()),
                            low_speed_near_floor_transitions=int(low.sum()),
                            near_floor_transitions=int(near.sum()),
                            near_floor_max_sole_speed=float(speed[near,i].max()) if near.any() else None,
                            near_floor_fastest_frames=[frames[fastest],frames[fastest+1]] if near.any() else None,
                            near_floor_xy_path_length=float((speed[near,i]/fps).sum()),
                            sole_xy_span=np.ptp(s[:,:,:2][:,i],axis=0).tolist(),
                            sole_endpoint_distance=float(np.linalg.norm(s[-1,i]-s[0,i]))))
    endpoint_angles = np.rad2deg(2*np.arccos(np.clip(np.abs(np.sum(q[0]*q[-1],axis=1)),0,1)))
    native = native_fbx(fps)
    summary = dict(source=str((BASE / raw_fbx['path']).relative_to(ROOT)), sha256=raw_fbx['sha256'],
                   blender=bpy.app.version_string, threads=4, fps=fps, action=action.name,
                   all_actions=[a.name for a in bpy.data.actions], frame_range=frames[::len(frames)-1], frame_count=len(frames),
                   duration_seconds=(frames[-1]-frames[0])/fps,
                   fcurves=len(list(shared.curves(action))), bones=names, mesh_vertices=len(mesh.data.vertices),
                   triangles=sum(len(poly.vertices)-2 for poly in mesh.data.polygons),
                   materials=[m.name if m else None for m in mesh.data.materials],
                   image_sizes=[dict(name=i.name,size=list(i.size)) for i in bpy.data.images],
                   reference_height_world=height, world_up='Z', native_fbx=native,
                   native_to_blender_frame_offset=frames[0]-native['key_frame_range'][0],
                   motion_envelope=[frames[moving[0]-1],frames[moving[-1]]] if len(moving) else None,
                   moving_transitions=int(len(moving)), total_transitions=len(frames)-1,
                   movement_thresholds=dict(local_rotation_degrees=.01,bone_head_distance=1e-6),
                   static_transition_end_frames=[frames[i] for i in range(1,len(frames)) if i not in moving],
                   surface_step_range=[min(surface_step[1:]),max(surface_step[1:])],
                   max_surface_from_start=max(surface_from_start),
                   full_motion_bounds=[bb[:,0].min(axis=0).tolist(),bb[:,1].max(axis=0).tolist()],
                   armature_object_matrix_max_delta=float(np.abs(np.asarray(root_matrices)-root_matrices[0]).max()),
                   floor_reference_z=floor,
                   contact_definition=dict(floor='Minimum foot surface in first imported frame; estimated, not an authored ground plane.',
                                           near_floor_height=height*.02,low_speed_per_second=height*.05,
                                           limitation='Fixed sole marker XY travel is sliding evidence only when foot is planted; pivots and intentional steps also move these markers.'),
                   feet=contact, interval_metrics=blocks,
                   endpoint_pose=dict(max_local_bone_angle_degrees=float(endpoint_angles.max()),
                                      rms_local_bone_angle_degrees=float(np.sqrt(np.mean(endpoint_angles**2))),
                                      worst_bone=names[int(endpoint_angles.argmax())],
                                      max_bone_head_distance=float(np.linalg.norm(p[-1]-p[0],axis=1).max()),
                                      max_surface_distance=surface_from_start[-1]))
    np.savez_compressed(OUT/'motion-samples.npz',frames=frames,positions=p,rotations=q,soles=s,foot_min_z=fz,
                        bounds=bb,names=names,height=height,fps=fps)
    write('frame-metrics.json',metrics)
    write('motion-analysis.json',summary)
    write('raw-hashes-after-analysis.json',hashes())
    print(json.dumps({k:summary[k] for k in ('fps','action','frame_range','duration_seconds','motion_envelope','moving_transitions','interval_metrics','feet','endpoint_pose')},indent=2),flush=True)


def evidence():
    data=np.load(OUT/'motion-samples.npz')
    info=json.loads((OUT/'motion-analysis.json').read_text(encoding='utf-8'))
    p,q,s,fz=[data[k] for k in ('positions','rotations','soles','foot_min_z')]
    names=list(data['names'])
    frames=data['frames']
    fps=float(data['fps'])
    indices={name:names.index('mixamorig:'+name) for name in ('Hips','Head','LeftHand','RightHand','LeftArm','RightArm','LeftFoot','RightFoot')}
    traces=[]
    for i,frame in enumerate(frames):
        traces.append(dict(blender_frame=int(frame),native_frame=int(frame)-1,elapsed_seconds=float((frame-frames[0])/fps),
                           world_bone_heads={name:p[i,index].tolist() for name,index in indices.items()},
                           hand_distance_from_shoulders={side:float(np.linalg.norm(p[i,indices[side+'Hand']]-p[i,indices[side+'Arm']])) for side in ('Left','Right')}))
    write('pose-landmarks.json',traces)
    contact=[]
    for side_index,side in enumerate(('Left','Right')):
        speed=np.linalg.norm(np.diff(s[:,side_index,:2],axis=0),axis=1)*fps
        near=fz[:,side_index] <= info['floor_reference_z'] + info['reference_height_world']*.02
        fast=near[:-1] & near[1:] & (speed > info['reference_height_world']*.05)
        runs=[]
        start=None
        for i,value in enumerate(np.r_[fast,False]):
            if value and start is None:
                start=i
            if not value and start is not None:
                runs.append(dict(blender_frames=[int(frames[start]),int(frames[i])],
                                 near_floor_xy_path=float(speed[start:i].sum()/fps),
                                 xy_net_displacement=float(np.linalg.norm(s[i,side_index,:2]-s[start,side_index,:2])),
                                 max_xy_speed=float(speed[start:i].max())))
                start=None
        contact.append(dict(side=side,fast_near_floor_runs=runs))
    hips=p[:,indices['Hips']]
    write('contact-detail.json',dict(
        note='Potential sliding runs: near-floor sole-marker speed >5% reference height/sec. Rotations, stepping and skin deformation contribute; no authored foot contacts exist.',
        feet=contact,hips_world_bounds=[hips.min(axis=0).tolist(),hips.max(axis=0).tolist()],
        hips_endpoint_distance=float(np.linalg.norm(hips[-1]-hips[0])),
        armature_object_constant=info['armature_object_matrix_max_delta']==0))
    write('raw-hashes-after-evidence.json',hashes())
    print('EVIDENCE_DONE',flush=True)


def render(frames, view, tag):
    hashes()
    rig, mesh, action = shared.load_source()
    raw_range = list(map(float,action.frame_range))
    start,end = map(round,raw_range)
    if any(abs(actual-rounded) > 1e-4 for actual,rounded in zip(raw_range,(start,end))):
        raise ValueError('Expected integer-frame source boundaries: ' + str(raw_range))
    if not frames or any(frame < start or frame > end for frame in frames):
        raise ValueError('Render frames must lie inside the imported action')
    scene = shared.setup_render(mesh,frames,view)
    if view == 'opposite-quarter':
        bounds=np.load(OUT/'motion-samples.npz')['bounds']
        low,high=bounds[:,0].min(axis=0),bounds[:,1].max(axis=0)
        center=(low+high)/2
        scene.camera.location=shared.Vector(center)+shared.Vector((.85,-1,.10)).normalized()*float(max(high-low))*4
        shared.point_camera(scene.camera,center)
    # Keep the shadow plane identical to the numeric contact reference.
    info = json.loads((OUT/'motion-analysis.json').read_text(encoding='utf-8'))
    bpy.data.objects['Plane'].location.z = info['floor_reference_z'] - .002
    write(f'render-configuration-{tag}-{view}.json',dict(imported_action_float_range=raw_range,
          sampled_integer_range=[start,end],fps=info['fps'],engine=scene.render.engine,
          device=scene.cycles.device,threads=scene.render.threads,samples=scene.cycles.samples,
          image_size=[scene.render.resolution_x,scene.render.resolution_y],
          floor_plane_z=bpy.data.objects['Plane'].location.z,
          camera_view={'front':'+Y with elevated angle','three-quarter':'+X/+Y three-quarter','opposite-quarter':'+X/-Y three-quarter'}[view],
          material='Temporary inspection basecolor material, original texture, roughness 0.72; not exported.'))
    directory = OUT/'renders'/tag
    directory.mkdir(parents=True,exist_ok=True)
    paths,index = [],[]
    for frame in frames:
        scene.frame_set(frame)
        elapsed = (frame-start)/info['fps']
        bpy.data.objects['FrameLabel'].data.body = f'B{frame} | {elapsed:.3f}s | {view}'
        path = directory/f'{view}-{frame:04d}.png'
        if not path.exists():
            scene.render.filepath = str(path)
            bpy.ops.render.render(write_still=True)
        paths.append(path)
        index.append(dict(blender_frame=frame,native_fbx_frame=frame-info['native_to_blender_frame_offset'],
                          take_elapsed_seconds=elapsed,path=str(path.relative_to(ROOT))))
        print('RENDER_DONE',frame,flush=True)
    shared.contact_sheet(paths,OUT/f'contact-sheet-{tag}-{view}.png')
    write(f'render-index-{tag}-{view}.json',index)
    write('raw-hashes-after-render.json',hashes())


if __name__ == '__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('mode',choices=['analyze','evidence','render'])
    parser.add_argument('--frames',default='')
    parser.add_argument('--view',choices=['front','three-quarter','opposite-quarter'],default='front')
    parser.add_argument('--tag',default='cast')
    args=parser.parse_args(sys.argv[sys.argv.index('--')+1:])
    if args.mode == 'analyze':
        analyze()
    elif args.mode == 'evidence':
        evidence()
    else:
        evidence()
        render([int(f) for f in args.frames.split(',') if f],args.view,args.tag)
