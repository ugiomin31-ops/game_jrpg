"""Complete quaternion motion library, posed around character-space axes.
Attack contact is frame 10 / 25; spell release is frame 21 / 35.
"""
import math
import bpy
from mathutils import Euler, Vector, Quaternion

LENGTHS = dict(Idle=48, Walk=32, Run=20, Attack=25, Cast=35, Hit=12, Die=30, Victory=42, Talk=48,
               Guard=36, Revive=60)


def create_actions(H, npc=False):
    rig = H.rig
    rig.animation_data_create()
    basis = {b.name: b.matrix_local.to_quaternion() for b in rig.data.bones}
    actions = {}

    def action(name, frames, grounded=False):
        length = LENGTHS[name]
        act = bpy.data.actions.new(name)
        act.use_fake_user = True
        act.use_frame_range = True
        act.frame_range = (0, length)
        rig.animation_data.action = act
        # Hero contact motions are baked at every frame: quaternion interpolation
        # and evaluated skinned geometry determine the floor clearance, not a
        # guessed character height. NPC motion stays on its original contract.
        if grounded:
            samples = []
            for frame in range(length + 1):
                left, right = next((a, z) for a, z in zip(frames, frames[1:])
                                   if a[0] <= frame <= z[0])
                t = (frame - left[0]) / (right[0] - left[0])
                if t == 0 or t == 1:
                    pose = dict(left[1] if t == 0 else right[1])
                    samples.append((frame, pose, left[2] if t == 0 else right[2]))
                    continue
                pose = {}
                for bn in rig.pose.bones.keys():
                    qa = Euler(tuple(math.radians(x) for x in left[1].get(bn, (0, 0, 0))), 'XYZ').to_quaternion()
                    qb = Euler(tuple(math.radians(x) for x in right[1].get(bn, (0, 0, 0))), 'XYZ').to_quaternion()
                    pose[bn] = tuple(math.degrees(x) for x in qa.slerp(qb, t).to_euler('XYZ'))
                samples.append((frame, pose, left[2] * (1 - t) + right[2] * t))
            frames = samples
        root_keys = []
        for f, pose, root_z in frames:
            for pb in rig.pose.bones:
                deg = pose.get(pb.name, (0, 0, 0))
                q = Euler(tuple(math.radians(x) for x in deg), 'XYZ').to_quaternion()
                b = basis[pb.name]
                pb.rotation_mode = 'QUATERNION'
                pb.rotation_quaternion = b.inverted() @ q @ b
                pb.location = b.inverted() @ Vector((0, 0, root_z)) if pb.name == 'root' else (0, 0, 0)
                pb.scale = (1, 1, 1)
            if grounded:
                bpy.context.view_layer.update()
                evaluated = H.body.evaluated_get(bpy.context.evaluated_depsgraph_get())
                mesh = evaluated.to_mesh()
                floor = min((evaluated.matrix_world @ v.co).z for v in mesh.vertices)
                evaluated.to_mesh_clear()
                # Exact Idle endpoints retain their original transform. Other
                # keys touch the floor without penetrating it or floating.
                root_z -= floor if abs(floor) > 1e-6 else 0
                rig.pose.bones['root'].location = basis['root'].inverted() @ Vector((0, 0, root_z))
            root_keys.append((f, root_z))
            for pb in rig.pose.bones:
                pb.keyframe_insert('rotation_quaternion', frame=f, group=pb.name)
                pb.keyframe_insert('location', frame=f, group=pb.name)
                pb.keyframe_insert('scale', frame=f, group=pb.name)
        if grounded:
            for curve in act.layers[0].strips[0].channelbag(rig.animation_data.action_slot).fcurves:
                for key in curve.keyframe_points:
                    key.interpolation = 'LINEAR'
            act['root_height_keys'] = [value for _, value in root_keys]
        act['contact_normalized'] = .4 if name == 'Attack' else .6 if name == 'Cast' else -1.0
        act['loop'] = name in ('Idle', 'Walk', 'Run', 'Talk')
        act['authored_keyframes'] = [f for f, _, _ in frames]
        actions[name] = act

    def cloth(pose, phase, amount=1):
        for i, bn in enumerate(H.secondary):
            pose[bn] = (math.sin(phase + i * .8) * 5 * amount, math.sin(phase + i) * 3 * amount, 0)
        return pose

    frames = []
    for f in (0, 12, 24, 36, 48):
        p = f / 48 * math.tau
        pose = {'spine': (1.5 * math.sin(p), 0, 0), 'chest': (-1.1 * math.sin(p), 0, 0),
                'head': (.8 * math.sin(p), 1.7 * math.sin(p), 0),
                'upper_arm.L': (0, -3 - math.sin(p), 0), 'upper_arm.R': (0, 3 + math.sin(p), 0)}
        frames.append((f, cloth(pose, p, .4), .002 * (1 - math.cos(p))))
    idle_pose = dict(frames[0][1])
    action('Idle', frames)

    for name, length, stride, arm, bounce in (('Walk', 32, 22, 18, .011), ('Run', 20, 39, 37, .022)):
        frames = []
        for i in range(9):
            f = length * i / 8
            phase = i * math.tau / 8
            sn = math.sin(phase)
            pose = {'thigh.L': (-stride * sn, 0, 0), 'thigh.R': (stride * sn, 0, 0),
                    'shin.L': (max(0, sn) * stride * .65, 0, 0), 'shin.R': (max(0, -sn) * stride * .65, 0, 0),
                    'foot.L': (-max(0, sn) * stride * .15, 0, 0), 'foot.R': (-max(0, -sn) * stride * .15, 0, 0),
                    'upper_arm.L': (arm * sn, -4, 0), 'upper_arm.R': (-arm * sn, 4, 0),
                    'forearm.L': (-12 if name == 'Walk' else -33, 0, 0),
                    'forearm.R': (-12 if name == 'Walk' else -33, 0, 0),
                    'chest': (-5 if name == 'Run' else -1, 0, -3 * sn), 'head': (3 if name == 'Run' else 0, 0, sn)}
            frames.append((f, cloth(pose, phase + 1, 1.1), bounce * (1 - math.cos(phase * 2))))
        action(name, frames)

    # Deliberate anticipation, acceleration into exact 40%-contact, recoil, recovery.
    if H.name == 'archer':
        wind = {'chest': (0, 0, -10), 'upper_arm.L': (-81, -12, -8), 'forearm.L': (-12, 0, 0),
                'upper_arm.R': (-62, 28, 8), 'forearm.R': (-70, 0, -23), 'head': (0, 0, 8)}
        hit = dict(wind, **{'forearm.R': (-100, 0, -40), 'hand.R': (0, 0, 16), 'chest': (0, 0, -5)})
        follow = dict(wind, **{'upper_arm.R': (-45, 42, 12), 'forearm.R': (-63, 0, -30)})
    elif H.name == 'warrior':
        wind = {'upper_arm.R': (-134, 5, -18), 'forearm.R': (-29, 0, 5), 'upper_arm.L': (-47, -7, 0),
                'chest': (7, 0, -17), 'hips': (0, 0, -8), 'head': (-4, 0, 10)}
        hit = {'upper_arm.R': (-56, -18, 22), 'forearm.R': (-14, 0, 0), 'upper_arm.L': (-53, -10, 0),
               'chest': (-13, 0, 15), 'hips': (-7, 0, 9), 'head': (5, 0, -5), 'thigh.R': (-16, 0, 0)}
        follow = dict(hit, **{'upper_arm.R': (-24, -28, 25), 'chest': (-8, 0, 20)})
    else:
        wind = {'upper_arm.R': (-112, 16, 0), 'forearm.R': (-24, 0, 0), 'upper_arm.L': (-42, -20, 0),
                'chest': (4, 0, -12), 'head': (-5, 0, 5)}
        hit = {'upper_arm.R': (-61, -9, 0), 'forearm.R': (-18, 0, 0), 'upper_arm.L': (-65, -17, 0),
               'chest': (-8, 0, 9), 'head': (2, 0, -4)}
        follow = dict(hit, **{'upper_arm.R': (-38, -17, 0), 'chest': (-4, 0, 12)})
    action('Attack', [(0, {}, 0), (5, cloth(wind, 1, .7), .004), (10, cloth(hit, 2, 1.8), .008),
                      (14, cloth(follow, 3, 1.4), .007), (20, {'chest': (0, 0, 3)}, 0), (25, {}, 0)])

    gather = {'upper_arm.R': (-58, 15, 0), 'forearm.R': (-53, 0, 0), 'upper_arm.L': (-46, -23, 0),
              'forearm.L': (-31, 0, 0), 'head': (9, 0, 0), 'chest': (5, 0, 0)}
    release = {'upper_arm.R': (-143, 11, 0), 'forearm.R': (-12, 0, 0), 'upper_arm.L': (-93, -37, 0),
               'forearm.L': (-16, 0, 0), 'hand.L': (0, -13, 0), 'chest': (-7, 0, 0), 'head': (-12, 0, 0)}
    action('Cast', [(0, {}, 0), (8, cloth(gather, .4, .5), 0), (16, cloth(gather, 1, .7), .005),
                    (21, cloth(release, 2, 1.6), .012), (26, cloth(release, 3, 1.2), .006), (35, {}, 0)])
    action('Hit', [(0, {}, 0), (3, {'chest': (20, 0, -8), 'head': (13, 0, 7), 'upper_arm.L': (-21, -10, 0),
                                 'upper_arm.R': (-17, 13, 0), 'hips': (9, 0, 0)}, 0),
                   (7, {'chest': (-6, 0, 4), 'head': (-6, 0, 0)}, .003), (12, {}, 0)])
    collapse = {'root': (90, 0, -7), 'chest': (6, 0, 0), 'head': (-8, 0, 0),
                'upper_arm.L': (16, -22, 0), 'upper_arm.R': (12, 24, 0),
                'forearm.L': (-18, 0, 0), 'forearm.R': (-22, 0, 0), 'shin.L': (17, 0, 0)}
    death_frames = [(0, {}, 0), (7, {'hips': (-14, 0, 4), 'chest': (-21, 0, 0), 'head': (14, 0, 0),
                                    'shin.L': (32, 0, 0), 'shin.R': (24, 0, 0)}, 0),
                    (17, dict(collapse, root=(64, 0, -7)), .10), (24, collapse, .15), (30, collapse, .15)]
    action('Die', death_frames, grounded=not npc)
    if not npc:
        # Arms protect the torso, rather than using the spell release as guard.
        # Socket bones remain at identity relative to each existing hand.
        guard_arms = {
            'warrior': {'upper_arm.L': (-72, -17, -8), 'forearm.L': (57, 0, 5),
                        'upper_arm.R': (-29, 11, 8), 'forearm.R': (-41, 0, 0)},
            'mage': {'upper_arm.L': (-22, -16, -8), 'forearm.L': (-102, 0, 8),
                     'upper_arm.R': (-22, 9, 5), 'forearm.R': (-73, 0, 0)},
            'archer': {'upper_arm.L': (-41, -15, -9), 'forearm.L': (-40, 0, 4),
                       'upper_arm.R': (-18, 18, 8), 'forearm.R': (-105, 0, -5)},
            'cleric': {'upper_arm.L': (-24, -18, -7), 'forearm.L': (-94, 0, 8),
                       'upper_arm.R': (-26, 8, 5), 'forearm.R': (-68, 0, 0)},
        }[H.name]
        brace = dict(guard_arms, chest=(7, 0, -4), head=(-6, 0, 4),
                     **{'thigh.L': (-16, 0, 0), 'thigh.R': (-16, 0, 0),
                        'shin.L': (32, 0, 0), 'shin.R': (32, 0, 0),
                        'foot.L': (-16, 0, 0), 'foot.R': (-16, 0, 0)})
        guard_frames = []
        for f, weight, recoil in ((0, 0, 0), (3, .16, 0), (6, .5, 0), (9, .86, 0),
                                  (12, 1, 0), (15, 1, 2), (18, 1, 1), (21, 1, 0),
                                  (24, 1, 0), (27, .85, 0), (30, .5, 0),
                                  (33, .16, 0), (36, 0, 0)):
            pose = {bn: tuple(idle_pose.get(bn, (0, 0, 0))[i] * (1 - weight)
                              + brace.get(bn, (0, 0, 0))[i] * weight for i in range(3))
                    for bn in set(idle_pose) | set(brace)}
            pose['chest'] = (pose.get('chest', (0, 0, 0))[0] + recoil, 0, -4 * weight)
            guard_frames.append((f, pose, 0))
        action('Guard', guard_frames, grounded=True)
        actions['Guard']['hold_normalized'] = [1 / 3, 2 / 3]
        actions['Guard']['recovery_normalized'] = 2 / 3
        # Prone -> planted forearms -> knees under hips -> crouch -> standing.
        # No bind/rest reset is inserted between Die and Revive.
        plant = dict(collapse, head=(-19, 0, 0),
                     **{'upper_arm.L': (-31, -12, 0), 'upper_arm.R': (-35, 14, 0),
                        'forearm.L': (-56, 0, 0), 'forearm.R': (-53, 0, 0)})
        knees = dict(plant, root=(68, 0, -4), chest=(-12, 0, 0), head=(-27, 0, 0),
                     **{'thigh.L': (-86, 0, 0), 'thigh.R': (-81, 0, 0),
                        'shin.L': (99, 0, 0), 'shin.R': (94, 0, 0),
                        'foot.L': (-13, 0, 0), 'foot.R': (-13, 0, 0)})
        push = dict(knees, root=(40, 0, -2), chest=(-10, 0, 0), head=(-20, 0, 0),
                    **{'thigh.L': (-83, 0, 0), 'thigh.R': (-76, 0, 0),
                       'shin.L': (99, 0, 0), 'shin.R': (91, 0, 0),
                       'foot.L': (-56, 0, 0), 'foot.R': (-55, 0, 0),
                       'upper_arm.L': (-22, -14, 0), 'upper_arm.R': (-26, 15, 0),
                       'forearm.L': (-28, 0, 0), 'forearm.R': (-32, 0, 0)})
        crouch = dict(idle_pose, root=(9, 0, 0), chest=(-3, 0, 0), head=(-6, 0, 0),
                      **{'thigh.L': (-52, 0, 0), 'thigh.R': (-48, 0, 0),
                         'shin.L': (87, 0, 0), 'shin.R': (79, 0, 0),
                         'foot.L': (-44, 0, 0), 'foot.R': (-40, 0, 0),
                         'upper_arm.L': (-16, -9, 0), 'upper_arm.R': (-18, 10, 0)})
        rise = dict(idle_pose, chest=(3, 0, 0), head=(-3, 0, 0),
                    **{'thigh.L': (-15, 0, 0), 'thigh.R': (-15, 0, 0),
                       'shin.L': (30, 0, 0), 'shin.R': (30, 0, 0),
                       'foot.L': (-15, 0, 0), 'foot.R': (-15, 0, 0)})
        action('Revive', [(0, collapse, .15), (4, collapse, .15), (10, plant, .15),
                          (19, knees, 0), (29, push, 0), (39, crouch, 0),
                          (49, rise, 0), (55, idle_pose, 0), (60, idle_pose, 0)], grounded=True)
        actions['Revive']['start_pose'] = 'Die:30'
        actions['Revive']['end_pose'] = 'Idle:0'
        actions['Revive']['recovery_normalized'] = 55 / 60
    salute = {'upper_arm.R': (-154, 0, -6), 'forearm.R': (-15, 0, 0), 'upper_arm.L': (-66, -18, 0),
              'forearm.L': (-38, 0, 0), 'head': (-7, 0, 0), 'chest': (-5, 0, 0)}
    action('Victory', [(0, {}, 0), (7, {'thigh.L': (-9, 0, 0), 'thigh.R': (-9, 0, 0), 'shin.L': (18, 0, 0),
                                     'shin.R': (18, 0, 0), 'chest': (12, 0, 0)}, 0),
                       (13, cloth(salute, 1, 1.7), .045), (21, cloth(salute, 2, 1), .01),
                       (29, dict(salute, head=(-7, 0, -7)), .004),
                       (36, {'upper_arm.R': (-65, 0, 0), 'head': (0, 0, 3)}, 0), (42, {}, 0)])
    if npc:
        frames = []
        for f in (0, 12, 24, 36, 48):
            t = f / 48 * math.tau
            pose = {'head': (3 * math.sin(t), 0, 3 * math.sin(t)), 'chest': (math.sin(t), 0, 0),
                    'upper_arm.L': (-35 - 12 * math.sin(t), -13, 0), 'forearm.L': (-32, 0, 0),
                    'upper_arm.R': (-22 + 8 * math.sin(t), 10, 0), 'forearm.R': (-18, 0, 0)}
            frames.append((f, cloth(pose, t, .35), 0))
        action('Talk', frames)
    rig.animation_data.action = None
    for pb in rig.pose.bones:
        pb.rotation_quaternion = (1, 0, 0, 0)
        pb.location = (0, 0, 0)
        pb.scale = (1, 1, 1)
    return actions
