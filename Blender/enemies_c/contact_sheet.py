"""Render review cells for the v2 roster straight from the exported FBX files (what Unity imports).

  python Blender/enemies_c/contact_sheet.py -- OUT_DIR [--ids ID ...] [--pose Idle:0.0] [--size 512]

Writes OUT_DIR/<id>.png (transparent, Workbench, vertex colours, cavity + outline, front 3/4 view).
Compose the labelled sheet with Blender/enemies_c/compose_sheet.py (PIL, Korean labels).
"""
import argparse
import math
import os
import sys

import bpy
from mathutils import Euler, Vector

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from roster import ROSTER  # noqa: E402

ART = os.path.normpath(os.path.join(HERE, '..', '..', 'Assets', '_Game', 'Resources', 'Art', 'Enemies'))


def shoot(eid, out, pose, frac, size):
    bpy.ops.wm.read_factory_settings(use_empty=True)
    sc = bpy.context.scene
    sc.render.fps = 30
    bpy.ops.import_scene.fbx(filepath=os.path.join(ART, eid, eid + '.fbx'))
    rig = next(o for o in sc.objects if o.type == 'ARMATURE')
    meshes = [o for o in sc.objects if o.type == 'MESH']
    act = next(a for a in bpy.data.actions if a.name.split('|')[-1] == pose)
    rig.animation_data_create()
    rig.animation_data.action = act
    try:
        if len(act.slots):
            rig.animation_data.action_slot = act.slots[0]
    except AttributeError:
        pass
    f0, f1 = act.frame_range
    sc.frame_set(int(round(f0 + (f1 - f0) * frac)))
    dg = bpy.context.evaluated_depsgraph_get()
    pts = []
    for o in meshes:
        oe = o.evaluated_get(dg)
        me = oe.to_mesh()
        pts += [oe.matrix_world @ v.co for v in me.vertices]
        oe.to_mesh_clear()
    lo = Vector([min(p[i] for p in pts) for i in range(3)])
    hi = Vector([max(p[i] for p in pts) for i in range(3)])
    cam = bpy.data.objects.new('Cam', bpy.data.cameras.new('Cam'))
    sc.collection.objects.link(cam)
    cam.data.type = 'ORTHO'
    e = Euler([math.radians(a) for a in (78, 0, 24)])
    cam.rotation_euler = e
    inv = e.to_matrix().transposed()
    center = (lo + hi) / 2
    proj = [inv @ (p - center) for p in pts]
    xl, xh = min(p.x for p in proj), max(p.x for p in proj)
    yl, yh = min(p.y for p in proj), max(p.y for p in proj)
    center = center + e.to_matrix() @ Vector(((xl + xh) / 2, (yl + yh) / 2, 0))
    cam.location = center + e.to_matrix() @ Vector((0, 0, 1)) * 10
    cam.data.ortho_scale = max(xh - xl, yh - yl) * 1.12
    cam.data.clip_end = 100
    sc.camera = cam
    sc.render.engine = 'BLENDER_WORKBENCH'
    sh = sc.display.shading
    sh.light = 'STUDIO'
    sh.studiolight_rotate_z = math.radians(20)
    sh.color_type = 'VERTEX'
    sh.show_shadows = True
    sh.show_cavity = True
    sh.cavity_type = 'BOTH'
    sh.curvature_ridge_factor = 1.3
    sh.curvature_valley_factor = 1.05
    sh.show_object_outline = True
    sh.object_outline_color = (.055, .045, .08)
    sh.show_specular_highlight = True
    sc.display.render_aa = '16'
    sc.view_settings.view_transform = 'Standard'
    sc.render.film_transparent = True
    sc.render.resolution_x = sc.render.resolution_y = size
    sc.render.image_settings.file_format = 'PNG'
    sc.render.image_settings.color_mode = 'RGBA'
    sc.render.filepath = out
    bpy.ops.render.render(write_still=True)
    return hi.z - lo.z


def main():
    args = sys.argv[sys.argv.index('--') + 1:]
    ap = argparse.ArgumentParser()
    ap.add_argument('out_dir')
    ap.add_argument('--ids', nargs='+', default=list(ROSTER))
    ap.add_argument('--pose', default='Idle:0.0')
    ap.add_argument('--size', type=int, default=512)
    o = ap.parse_args(args)
    os.makedirs(o.out_dir, exist_ok=True)
    pose, frac = o.pose.split(':')
    for eid in o.ids:
        suffix = '' if pose == 'Idle' else '_' + pose.lower()
        h = shoot(eid, os.path.join(o.out_dir, eid + suffix + '.png'), pose, float(frac), o.size)
        print(f'SHEET_CELL {eid} {pose} height={h:.3f}', flush=True)


if __name__ == '__main__':
    main()
