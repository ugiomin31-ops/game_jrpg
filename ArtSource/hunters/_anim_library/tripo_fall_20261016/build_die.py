"""Build shared Humanoid Die.fbx from the Tripo `fall` preset (dohyun rig e6b794c1).
- Armature only, one action "Die", object scale applied (pose locations rescaled).
- Whole motion turned about Z so frame 0 faces -Y like every library take (source starts ~45 deg off).
- Hips horizontal travel scaled by TRAVEL (source slides back ~85 % of body height).
- Bone Model nodes written in REST pose (rest key at frame -10 is the current frame at export).
"""
import bpy, sys, math
from mathutils import Matrix, Vector
src, out = sys.argv[sys.argv.index('--')+1:][:2]
TRAVEL = float(sys.argv[sys.argv.index('--')+3]) if len(sys.argv) > sys.argv.index('--')+3 else .5
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.fbx(filepath=src)
for o in list(bpy.data.objects):
    if o.type != 'ARMATURE': bpy.data.objects.remove(o, do_unlink=True)
arm = bpy.data.objects[0]
act = arm.animation_data.action
f0, f1 = (int(round(v)) for v in act.frame_range)
sc = bpy.context.scene
pb = arm.pose.bones
H = 'mixamorig:Hips'
print('bones', len(arm.data.bones), 'frames', f0, f1, 'rotmode', pb[H].rotation_mode)

def fcurves(a):
    out = []
    for layer in a.layers:
        for strip in layer.strips:
            for bag in strip.channelbags: out.extend(bag.fcurves)
    return out

def P(n): return arm.matrix_world @ pb[n].head
# 1) record hips world matrices and the frame-0 facing (character faces -(up x lateral))
world = {}
for f in range(f0, f1 + 1):
    sc.frame_set(f)
    world[f] = arm.matrix_world @ pb[H].matrix
    if f == f0:
        lat = (P('mixamorig:LeftUpLeg') - P('mixamorig:RightUpLeg')).normalized()
        up = (P('mixamorig:Neck') - P('mixamorig:Hips')).normalized()
        face = -up.cross(lat); face.z = 0; face.normalize()
yaw = math.atan2(face.y, face.x)
turn = -math.pi / 2 - yaw
print('frame0 facing deg', round(math.degrees(yaw), 1), 'turn deg', round(math.degrees(turn), 1))
# 2) apply the 0.01 object scale; pose locations live in armature units, so rescale them
s = arm.scale.x
bpy.context.view_layer.objects.active = arm; arm.select_set(True)
bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
for fc in fcurves(act):
    if fc.data_path.endswith('.location') and H not in fc.data_path:
        for k in fc.keyframe_points:
            k.co.y *= s; k.handle_left.y *= s; k.handle_right.y *= s
# 3) re-key hips: turn about the frame-0 hips position, scale horizontal travel
p0 = world[f0].translation.copy()
R = Matrix.Translation(Vector((p0.x, p0.y, 0))) @ Matrix.Rotation(turn, 4, 'Z') @ Matrix.Translation(Vector((-p0.x, -p0.y, 0)))
for f in range(f0, f1 + 1):
    m = R @ world[f]
    t = m.translation
    t.x = p0.x + TRAVEL * (t.x - p0.x); t.y = p0.y + TRAVEL * (t.y - p0.y)
    m.translation = t
    sc.frame_set(f)
    pb[H].matrix = arm.matrix_world.inverted() @ m
    pb[H].keyframe_insert('location', frame=f)
    pb[H].keyframe_insert('rotation_quaternion' if pb[H].rotation_mode == 'QUATERNION' else 'rotation_euler', frame=f)
# 4) rest key before the range so the exporter writes rest-pose bone nodes
REST = f0 - 10
for b in pb:
    b.location = (0, 0, 0); b.rotation_quaternion = (1, 0, 0, 0); b.rotation_euler = (0, 0, 0); b.scale = (1, 1, 1)
    b.keyframe_insert('location', frame=REST); b.keyframe_insert('scale', frame=REST)
    b.keyframe_insert('rotation_quaternion' if b.rotation_mode == 'QUATERNION' else 'rotation_euler', frame=REST)
act.name = 'Die'
act.use_frame_range = True; act.frame_start = f0; act.frame_end = f1
sc.frame_start, sc.frame_end = f0, f1
sc.render.fps = 24
sc.frame_set(REST)
bpy.ops.object.select_all(action='DESELECT'); arm.select_set(True)
bpy.ops.export_scene.fbx(filepath=out, use_selection=True, object_types={'ARMATURE'}, apply_unit_scale=True,
    apply_scale_options='FBX_SCALE_ALL', axis_forward='-Z', axis_up='Y', add_leaf_bones=False, primary_bone_axis='Y',
    secondary_bone_axis='X', use_armature_deform_only=False, bake_space_transform=False, bake_anim=True,
    bake_anim_use_all_bones=True, bake_anim_use_nla_strips=False, bake_anim_use_all_actions=True,
    bake_anim_force_startend_keying=True, bake_anim_step=1.0, bake_anim_simplify_factor=0.0, path_mode='STRIP')
print('wrote', out)
