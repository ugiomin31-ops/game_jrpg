import sys
sys.path.append(r"C:\Users\User\Desktop\game\Blender\bosses")
from _common import *  # noqa

A.reset_scene()
rig = A.armature([("root", (0, 0, 0), (0, 0, 0.5), None), ("arm", (0, 0, 1), (1, 0, 1), "root")])
b1 = A.box("b", (0.5, 0.5, 1), loc=(0, 0, 0.5))
o, _ = sweep("t", [(0, 0, 1), (0.5, 0, 1.1), (1, 0, 1)], [0.1, 0.08, 0.02])
chain_weights(o, [("arm", (0, 0, 1), (1, 0, 1))])
body = skin2({"root": [b1]}, [o], rig)
for n in ACTIONS:
    bake(rig, n, 20, lambda P, f, t: P.r("arm", (0, 0, 90 * t)))
print("ACTION SLOTS", [(a.name, [s.identifier for s in a.slots]) for a in bpy.data.actions])
A.render_preview("_smoke", action="Idle", frame=20, size=200)
A.ASSETS = r"C:\Users\User\AppData\Local\Temp\boss_smoke"
p = A.export_fbx("_smoke.fbx", objects=[rig, body], animated=True)
print("OK", p)
