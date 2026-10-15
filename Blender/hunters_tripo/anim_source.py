"""Hunter clips -> Unity Humanoid animation source for a Tripo hunter (no new animation authoring).

    blender -b --factory-startup --python-exit-code 1 -P Blender/hunters_tripo/anim_source.py -- <hero_id>
        [--src FBX]       default Assets/_Game/Resources/Art/Characters/<id>/<id>.fbx (the current Blender hero)
        [--out-dir DIR]   default ArtSource/hunters/<hero_id>/staging

Reads the hero's existing Blender FBX (game 22-bone rig, takes Rig|Idle ...) and writes DIR/<id>_anim.fbx:
  * skeleton only (no mesh, no materials): it only feeds clips to Unity's Humanoid retargeting;
  * bones renamed to Mixamo names (common.GAME_TO_MIXAMO) so Unity maps it like the Tripo rig;
  * rest pose rebased to the shared T-pose (common.pose_tpose), every take re-keyed so each bone keeps its exact
    world motion (verified per frame, before export and again after an FBX re-import);
  * same take names (Rig|Idle -> Unity clip Idle), same frame counts, 30 fps.
Report: DIR/<id>_anim_report.json.
"""
import math
import os
import sys

import bpy
from mathutils import Matrix

sys.path.append(os.path.dirname(os.path.abspath(__file__)))
import common as C  # noqa: E402


def parse(argv):
    a = C.args_after_dashes(argv)
    if not a:
        raise SystemExit(__doc__)
    o = {"id": a[0], "src": None, "out": None}
    i = 1
    while i < len(a):
        if a[i] == "--src":
            o["src"] = os.path.abspath(a[i + 1]); i += 2
        elif a[i] == "--out-dir":
            o["out"] = os.path.abspath(a[i + 1]); i += 2
        else:
            raise SystemExit("unknown option " + a[i])
    o["src"] = o["src"] or os.path.join(C.ART, "Characters", o["id"], o["id"] + ".fbx")
    o["out"] = o["out"] or os.path.join(C.REPO, "ArtSource", "hunters", o["id"], "staging")
    return o


def clip_name(action):
    return action.name.split("|")[-1]


def assign(rig, act):
    rig.animation_data_create()
    rig.animation_data.action = act
    if act is not None and getattr(act, "slots", None) and len(act.slots):
        rig.animation_data.action_slot = act.slots[0]


def frames_of(act):
    s, e = act.frame_range
    return list(range(int(round(s)), int(round(e)) + 1))


def sample(rig, act):
    """Armature-space matrix of every bone at every integer frame of `act`."""
    assign(rig, act)
    out = []
    for f in frames_of(act):
        bpy.context.scene.frame_set(f)
        out.append({pb.name: pb.matrix.copy() for pb in rig.pose.bones})
    return out


def ordered(rig):
    """Pose bones parents first."""
    res, seen = [], set()

    def visit(b):
        res.append(rig.pose.bones[b.name]); seen.add(b.name)
        for c in b.children:
            visit(c)
    for b in rig.data.bones:
        if b.parent is None:
            visit(b)
    return res


def rekey(rig, clip, samples, rename):
    """New action `clip` on the rebased rig reproducing the sampled armature-space matrices exactly."""
    act = bpy.data.actions.new(clip)
    act.use_fake_user = True
    assign(rig, act)
    bones = ordered(rig)
    prev = {}
    for i, frame in enumerate(samples):
        want = {rename.get(k, k): m for k, m in frame.items()}
        for pb in bones:
            rest = pb.bone.matrix_local
            m = want[pb.name]
            if pb.parent is None:
                basis = rest.inverted() @ m
            else:
                basis = rest.inverted() @ pb.parent.bone.matrix_local @ want[pb.parent.name].inverted() @ m
            loc, rot, scl = basis.decompose()
            if pb.name in prev and prev[pb.name].dot(rot) < 0:
                rot.negate()
            prev[pb.name] = rot.copy()
            pb.rotation_mode = "QUATERNION"
            pb.location, pb.rotation_quaternion, pb.scale = loc, rot, scl
            for path in ("location", "rotation_quaternion", "scale"):
                pb.keyframe_insert(path, frame=i, group=pb.name)
    act.use_frame_range = True
    act.frame_start, act.frame_end = 0, len(samples) - 1
    return act


def compare(rig, act, samples, rename, offset=None):
    """Max head-position (m) and rotation (deg) error of the rebased take against the original samples."""
    assign(rig, act)
    fr = frames_of(act)
    if len(fr) != len(samples):
        return {"frames": [len(fr), len(samples)], "pos_err_m": None, "rot_err_deg": None}
    perr = rerr = 0.0
    for f, frame in zip(fr, samples):
        bpy.context.scene.frame_set(f)
        for old, m in frame.items():
            pb = rig.pose.bones.get(rename.get(old, old))
            if pb is None:
                continue
            got = rig.matrix_world @ pb.matrix
            perr = max(perr, (got.translation - m.translation).length)
            q = got.to_quaternion().rotation_difference(m.to_quaternion())
            rerr = max(rerr, math.degrees(min(q.angle, 2 * math.pi - q.angle)))
    return {"frames": len(fr), "pos_err_m": round(perr, 6), "rot_err_deg": round(rerr, 4)}


def socket_motion(samples):
    """How far weapon.R / weapon.L move relative to their hand inside a take (0 = rigid socket)."""
    worst = 0.0
    for hand, sock in (("hand.R", "weapon.R"), ("hand.L", "weapon.L")):
        if not samples or hand not in samples[0]:
            continue
        ref = samples[0][hand].inverted() @ samples[0][sock]
        for fr in samples:
            rel = fr[hand].inverted() @ fr[sock]
            q = rel.to_quaternion().rotation_difference(ref.to_quaternion())
            worst = max(worst, math.degrees(min(q.angle, 2 * math.pi - q.angle)),
                        (rel.translation - ref.translation).length * 100)
    return round(worst, 4)


def build(o):
    hid, out = o["id"], o["out"]
    C.reset()
    objs = C.import_fbx(o["src"])
    rig = C.only(objs, "ARMATURE")
    if set(C.GAME_TO_MIXAMO) - set(rig.data.bones.keys()):
        raise RuntimeError("source is not the game 22-bone rig: missing " +
                           str(sorted(set(C.GAME_TO_MIXAMO) - set(rig.data.bones.keys()))))
    src_actions = sorted(bpy.data.actions, key=clip_name)
    samples, socket = {}, {}
    for act in src_actions:
        samples[clip_name(act)] = sample(rig, act)
        socket[clip_name(act)] = socket_motion(samples[clip_name(act)])
    missing = [c for c in C.CLIPS_REQUIRED if c not in samples]
    if missing:
        raise RuntimeError("source lacks clips " + str(missing))

    # Skeleton only.
    for ob in objs:
        if ob is not rig:
            bpy.data.objects.remove(ob)
    assign(rig, None)
    for act in src_actions:
        bpy.data.actions.remove(act)
    C.clear_pose(rig)

    # Shared T-pose rest, then Mixamo names.
    short = {v[len(C.MIX):]: k for k, v in C.GAME_TO_MIXAMO.items()}
    swing = C.pose_tpose(rig, short)
    C.apply_pose_as_rest(rig, [])
    for old, new in C.GAME_TO_MIXAMO.items():
        rig.data.bones[old].name = new
    rig.name = rig.data.name = "Rig"
    C.clear_pose(rig)

    rename = dict(C.GAME_TO_MIXAMO)
    new_actions = {clip: rekey(rig, clip, s, rename) for clip, s in samples.items()}
    pre = {clip: compare(rig, act, samples[clip], rename) for clip, act in new_actions.items()}
    assign(rig, None)
    C.clear_pose(rig)

    path = C.export_fbx(os.path.join(out, hid + "_anim.fbx"), [rig], animated=True, force=True)
    bpy.ops.wm.save_as_mainfile(filepath=os.path.join(out, hid + "_anim.blend"), compress=True)
    return path, samples, rename, {"tpose_swing_deg": swing, "pre_export_error": pre,
                                   "weapon_socket_motion_vs_hand(deg_or_cm)": socket}


def verify(o, path, samples, rename, info):
    hid, out = o["id"], o["out"]
    C.reset()
    objs = C.import_fbx(path)
    rig = C.only(objs, "ARMATURE")
    acts = {clip_name(a): a for a in bpy.data.actions}
    post = {clip: compare(rig, acts[clip], s, rename) if clip in acts else None for clip, s in samples.items()}
    C.clear_pose(rig)
    bones = rig.data.bones
    arm = {}
    for side in ("Left", "Right"):
        d = bones[C.MIX + side + "ForeArm"].head_local - bones[C.MIX + side + "Arm"].head_local
        arm[side] = round(math.degrees(math.asin(max(-1, min(1, d.normalized().z)))), 2)
    report = dict(info)
    report.update({
        "id": hid, "fbx": os.path.relpath(path, C.REPO).replace("\\", "/"),
        "source": os.path.relpath(o["src"], C.REPO).replace("\\", "/"),
        "objects": sorted(ob.name for ob in objs), "bones": sorted(b.name for b in bones),
        "takes": sorted(a.name for a in bpy.data.actions), "clips": sorted(acts),
        "upper_arm_elevation_deg": arm, "humanoid": C.humanoid_check(rig), "post_reimport_error": post,
    })
    def err(key, missing):
        return max((missing if not v or v[key] is None else v[key]) for v in post.values())
    worst, worst_rot = err("pos_err_m", 9.0), err("rot_err_deg", 999.0)
    report["ok"] = (all(post.values()) and worst < 1e-3 and worst_rot < 0.5
                    and not report["humanoid"]["missing_required"] and report["humanoid"]["hips_is_ancestor"]
                    and report["objects"] == ["Rig"])
    C.write_json(os.path.join(out, hid + "_anim_report.json"), report)
    print("REPORT", report)
    if not report["ok"]:
        raise SystemExit("verification failed: see " + os.path.join(out, hid + "_anim_report.json"))


if __name__ == "__main__":
    opts = parse(sys.argv)
    p, smp, ren, inf = build(opts)
    verify(opts, p, smp, ren, inf)
