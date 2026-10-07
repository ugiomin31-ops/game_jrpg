"""Anatomical anime body from the MakeHuman base mesh (CC0, see Blender/third_party/makehuman/README.md).

Why: the swept-tube body read as a mannequin. MakeHuman's hm08 mesh is a real human with clean
quad topology, modelled hands and feet, and a tuned skin weight map, so shoulders, elbows,
knees and fingers deform like a person. This module:

1. shapes it with MakeHuman's own morph targets (sex, build, proportions, face) plus an
   anime pass (larger head and eyes, small nose and mouth, narrow chin, longer legs);
2. poses it with MakeHuman's 163-bone skeleton and weights into the game's rest pose
   (arms near the sides, relaxed curled fingers) and bakes that pose into the mesh;
3. folds the MakeHuman weights onto the game's 20-bone Humanoid skeleton, so every clip
   in lib_humanoid/motion.py plays unchanged.
"""
import json
import math
import os

import bmesh
import bpy
import numpy as np
from mathutils import Matrix, Quaternion, Vector

import anime_body as AB
from humanoid import V

HERE = os.path.dirname(os.path.abspath(__file__))
DATA = os.path.join(HERE, "..", "third_party", "makehuman", "mh_data.npz")

_cache = {}


def data():
    if "d" not in _cache:
        z = np.load(DATA)
        d = {k: z[k] for k in z.files}
        for k in ("joints", "bones", "weights"):
            d[k] = json.loads(bytes(d[k]).decode())
        _cache["d"] = d
    return _cache["d"]


def target(name):
    d = data()
    return d["t/" + name + ".index"], d["t/" + name + ".vector"].astype(np.float64) * 1e-3


# Game bone that each MakeHuman bone's weight is folded into (descendants inherit through the parent walk).
FOLD = {
    "root": "hips", "spine05": "hips", "spine04": "hips", "pelvis": "hips",
    "spine03": "spine", "spine02": "spine",
    "spine01": "chest", "breast": "chest",
    "clavicle": "shoulder", "shoulder01": "upper_arm", "upperarm01": "upper_arm", "upperarm02": "upper_arm",
    "lowerarm01": "forearm", "lowerarm02": "forearm", "wrist": "hand",
    "neck01": "neck", "neck02": "neck", "neck03": "neck", "head": "head",
    "upperleg01": "thigh", "upperleg02": "thigh", "lowerleg01": "shin", "lowerleg02": "shin", "foot": "foot",
}


def fold(bone, bones):
    b = bone
    while b is not None:
        base, _, side = b.partition(".")
        if base in FOLD:
            g = FOLD[base]
            return g + "." + side if side and g not in ("hips", "spine", "chest", "neck", "head") else g
        b = bones[b]["parent"]
    return "hips"


def to_blender(co):
    """MakeHuman decimetres, Y up, facing +Z  ->  metres, Z up, facing -Y."""
    return np.stack([co[:, 0], -co[:, 2], co[:, 1]], axis=1) * 0.1


# ---------------------------------------------------------------- recipe

MALE = dict(sex="male", ethnic=dict(asian=0.35, caucasian=0.6, african=0.05), muscle=0.1, weight=-0.5,
            proportions=1.0, height=0.25, extra={"measure/measure-shoulder-dist-decr": 0.35,
            "torso/torso-scale-depth-decr": 0.3, "hip/hip-scale-horiz-decr": 0.2})
FEMALE = dict(sex="female", ethnic=dict(asian=0.5, caucasian=0.4, african=0.1), muscle=0.0, weight=-0.55,
              proportions=1.0, height=0.0)

# Face and limb targets that turn the realistic head into an anime one (weights tuned by eye on toon renders).
ANIME_FACE = {
    "eyes/{s}-eye-scale-incr": 0.9,
    "eyes/{s}-eye-height2-incr": 0.8,
    "eyes/{s}-eye-height1-incr": 0.4,
    "eyes/{s}-eye-bag-decr": 1.0,
    "eyes/{s}-eye-trans-down": 0.25,
    "nose/nose-scale-horiz-decr": 0.8,
    "nose/nose-scale-vert-decr": 0.5,
    "nose/nose-scale-depth-decr": 0.6,
    "nose/nose-nostrils-width-decr": 0.6,
    "nose/nose-width1-decr": 0.5,
    "mouth/mouth-scale-horiz-decr": 0.55,
    "mouth/mouth-lowerlip-volume-decr": 0.6,
    "mouth/mouth-upperlip-volume-decr": 0.6,
    "chin/chin-width-decr": 0.8,
    "head/head-oval": 0.6,
    "cheek/{s}-cheek-volume-decr": 0.7,
    "cheek/{s}-cheek-inner-decr": 0.5,
    "mouth/mouth-scale-depth-decr": 0.7,
    "nose/nose-volume-decr": 0.6,
    "nose/nose-flaring-decr": 0.8,
    "chin/chin-prominent-decr": 0.4,
    "chin/chin-triangle": 0.5,
    "chin/chin-height-decr": 0.6,
    "mouth/mouth-trans-up": 0.4,
    "nose/nose-trans-up": 0.3,
    "nose/nose-point-up": 0.3,
    "head/head-fat-decr": 0.8,
    "cheek/{s}-cheek-bones-decr": 0.6,
    "eyebrows/eyebrows-trans-up": 0.3,
    "neck/neck-scale-horiz-decr": 0.6,
    "armslegs/upperlegs-height-incr": 0.5,
    "armslegs/lowerlegs-height-incr": 0.4,
    "armslegs/{s}-hand-scale-decr": 0.25,
    "armslegs/{s}-foot-scale-decr": 0.3,
}


def shaped_vertices(recipe, face=ANIME_FACE):
    d = data()
    V0 = d["base"].astype(np.float64).copy()
    names = set(d["targets"])

    def add(name, w):
        if w == 0:
            return
        if name not in names:
            print("[mh_base] missing target", name)
            return
        idx, vec = target(name)
        V0[idx] += vec * w

    sex = recipe["sex"]
    for eth, w in recipe["ethnic"].items():
        add(f"macrodetails/{eth}-{sex}-young", w)

    def axis(lo_name, hi_name, x):
        add(hi_name if x > 0 else lo_name, abs(x))
    m, w = recipe["muscle"], recipe["weight"]
    axis(f"macrodetails/universal-{sex}-young-minmuscle-averageweight",
         f"macrodetails/universal-{sex}-young-maxmuscle-averageweight", m)
    axis(f"macrodetails/universal-{sex}-young-averagemuscle-minweight",
         f"macrodetails/universal-{sex}-young-averagemuscle-maxweight", w)
    add(f"macrodetails/proportions/{sex}-young-averagemuscle-averageweight-idealproportions", recipe["proportions"])
    axis(f"macrodetails/height/{sex}-young-averagemuscle-averageweight-minheight",
         f"macrodetails/height/{sex}-young-averagemuscle-averageweight-maxheight", recipe["height"])
    for name, wt in face.items():
        if "{s}" in name:
            for s in ("l", "r"):
                add(name.format(s=s), wt)
        else:
            add(name, wt)
    for name, wt in recipe.get("extra", {}).items():
        add(name, wt)
    return V0


# ---------------------------------------------------------------- build

def _joint(Vb, joints, name):
    return Vector(Vb[joints[name]].mean(axis=0))


def build(H, recipe, head_scale=1.15, jaw_taper=0.16, height=1.60, arm_down=None, curl=1.0):
    """Returns the weighted body object (posed into H's rest pose) and writes H.j / bone layout from it."""
    d = data()
    Vmh = shaped_vertices(recipe)
    Vb = to_blender(Vmh)
    joints, bones, weights = d["joints"], d["bones"], d["weights"]

    def J(n):
        return _joint(Vb, joints, n)

    # Anime head: scale everything the head bones drive about the top of the neck, blended by weight.
    head_w = np.zeros(len(Vb))
    for bn, lst in weights.items():
        if fold(bn, bones) == "head":
            for vi, wt in lst:
                head_w[vi] += wt
    head_w = np.clip(head_w, 0, 1)
    pivot = np.array(J("neck03____head"))
    s = 1.0 + (head_scale - 1.0) * head_w[:, None]
    Vb = pivot + (Vb - pivot) * s
    # Anime jaw: taper the lower face toward a narrow chin (the head bones' weight keeps the neck seam smooth).
    ez = float(Vb[d["eye_l"]][:, 2].mean())
    t = np.clip((ez - Vb[:, 2]) / 0.11, 0, 1) ** 1.2 * head_w
    Vb[:, 0] *= 1 - jaw_taper * t
    Vb[:, 1] = pivot[1] + (Vb[:, 1] - pivot[1]) * (1 - 0.04 * t)
    # Lower body: lift the floor to z=0.
    Vb[:, 2] -= Vb[d["body_faces"].reshape(-1)][:, 2].min()
    Vb *= height / Vb[d["body_faces"].reshape(-1)][:, 2].max()

    # ---- MakeHuman armature at the shaped joints
    arm = bpy.data.armatures.new("MHRig")
    rig = bpy.data.objects.new("MHRig", arm)
    bpy.context.scene.collection.objects.link(rig)
    bpy.context.view_layer.objects.active = rig
    bpy.ops.object.mode_set(mode="EDIT")
    for bn, b in bones.items():
        eb = arm.edit_bones.new(bn)
        eb.head = J(b["head"])
        eb.tail = J(b["tail"])
        if (eb.tail - eb.head).length < 1e-4:
            eb.tail = eb.head + Vector((0, 0, 0.01))
    for bn, b in bones.items():
        if b["parent"]:
            arm.edit_bones[bn].parent = arm.edit_bones[b["parent"]]
    bpy.ops.object.mode_set(mode="OBJECT")

    # ---- mesh with every base vertex (indices shared with joints/weights); faces = skin only
    me = bpy.data.meshes.new("Body")
    faces = d["body_faces"].tolist()
    me.from_pydata([tuple(v) for v in Vb], [], faces)
    me.update()
    body = bpy.data.objects.new("Body", me)
    bpy.context.scene.collection.objects.link(body)
    for bn, lst in weights.items():
        g = body.vertex_groups.new(name=bn)
        for vi, wt in lst:
            g.add([vi], wt, "REPLACE")
    md = body.modifiers.new("Armature", "ARMATURE")
    md.object = rig

    # ---- pose into the game rest pose
    for pb in rig.pose.bones:
        pb.rotation_mode = "QUATERNION"

    def rotate_world(bn, axis, deg, pivot=None):
        pb = rig.pose.bones[bn]
        bpy.context.view_layer.update()
        M = pb.matrix.copy()
        piv = Vector(pivot) if pivot is not None else M.translation
        R = Matrix.Translation(piv) @ Quaternion(Vector(axis).normalized(), math.radians(deg)).to_matrix().to_4x4() @ Matrix.Translation(-piv)
        pb.matrix = R @ M
        bpy.context.view_layer.update()

    angle = H.P["arm_angle"] if arm_down is None else arm_down
    for S, sg in (("L", 1), ("R", -1)):
        sh = rig.pose.bones["upperarm01." + S].head
        el = rig.pose.bones["lowerarm01." + S].head
        cur = math.degrees(math.atan2(sg * (el.x - sh.x), sh.z - el.z))
        drop = cur - angle
        # Most of the drop at the shoulder joint, a little through the clavicle so the shoulder line settles.
        rotate_world("clavicle." + S, (0, 1, 0), sg * drop * 0.12)
        rotate_world("upperarm01." + S, (0, 1, 0), sg * drop * 0.88)
        # Forearm: MakeHuman's rest bends the elbow well forward; straighten it to a relaxed ~10 degree bend.
        sh_p = rig.pose.bones["upperarm01." + S].head
        el_p = rig.pose.bones["lowerarm01." + S].head
        fore = rig.pose.bones["wrist." + S].head - el_p
        want = ((el_p - sh_p).normalized() + Vector((sg * 0.03, -0.17, 0))).normalized()
        axis = fore.normalized().cross(want)
        if axis.length > 1e-6:
            rotate_world("lowerarm01." + S, axis, math.degrees(fore.normalized().angle(want)), pivot=el_p.copy())
        # MakeHuman's A-pose has the palms facing the floor; track that normal through the posing.
        def palm():
            bpy.context.view_layer.update()
            pb = rig.pose.bones["wrist." + S]
            rot = pb.matrix.to_3x3() @ pb.bone.matrix_local.to_3x3().inverted()
            return (rot @ Vector((0, 0, -1))).normalized()

        def signed(u, v, axis):
            u = (u - axis * u.dot(axis)).normalized()
            v = (v - axis * v.dot(axis)).normalized()
            return math.degrees(math.atan2(axis.dot(u.cross(v)), u.dot(v)))
        # Palms turn to face the thighs: the twist is shared along the forearm, as the radius and ulna do.
        el_p = rig.pose.bones["lowerarm01." + S].head.copy()
        fdir = (rig.pose.bones["wrist." + S].head - el_p).normalized()
        twist = signed(palm(), Vector((-sg, -0.35, 0)).normalized(), fdir)
        rotate_world("lowerarm01." + S, fdir, twist * 0.4, pivot=el_p)
        rotate_world("lowerarm02." + S, fdir, twist * 0.6, pivot=rig.pose.bones["lowerarm02." + S].head.copy())
        # Wrist: hand in line with the forearm (MakeHuman's rest hand is bent toward the little finger).
        bpy.context.view_layer.update()
        wr = rig.pose.bones["wrist." + S].head.copy()
        fdir = (wr - rig.pose.bones["lowerarm01." + S].head).normalized()
        hdir = (rig.pose.bones["finger3-1." + S].head - wr).normalized()
        ax = hdir.cross(fdir)
        if ax.length > 1e-6:
            rotate_world("wrist." + S, ax, math.degrees(hdir.angle(fdir)) * 0.85, pivot=wr)
        # Relaxed fingers: every segment curls toward the palm; the thumb folds in less.
        for f in range(1, 6):
            for k in (1, 2, 3):
                bn = f"finger{f}-{k}.{S}"
                pb = rig.pose.bones[bn]
                pn = palm()
                fd = (pb.tail - pb.head).normalized()
                axis = fd.cross(pn)
                if axis.length < 1e-6:
                    continue
                deg = (14, 18, 16)[k - 1] if f == 1 else (30 + 4 * f, 48, 34)[k - 1]
                rotate_world(bn, axis, deg * curl, pivot=pb.head.copy())
        if os.environ.get("MH_DEBUG"):
            kn = sum((rig.pose.bones[f"finger{f}-1.{S}"].head for f in (2, 3, 4, 5)), Vector()) / 4
            tp = sum((rig.pose.bones[f"finger{f}-3.{S}"].tail for f in (2, 3, 4, 5)), Vector()) / 4
            print("[mh] palm", S, tuple(round(c, 2) for c in palm()), "curl dir", tuple(round(c, 3) for c in (tp - kn)))
    # Legs: feet under the hips (MakeHuman stands with a wide stance).
    for S, sg in (("L", 1), ("R", -1)):
        hp = rig.pose.bones["upperleg01." + S].head
        an = rig.pose.bones["foot." + S].head
        cur = math.degrees(math.atan2(sg * (an.x - hp.x), hp.z - an.z))
        rotate_world("upperleg01." + S, (0, 1, 0), sg * (cur - 2.5))
        an = rig.pose.bones["foot." + S].head
        rotate_world("foot." + S, (0, 1, 0), -sg * (cur - 2.5))
    bpy.context.view_layer.update()

    # Record the posed joints the game skeleton needs.
    P = {bn: (pb.head.copy(), pb.tail.copy()) for bn, pb in rig.pose.bones.items()}
    P = {bn: (rig.matrix_world @ h, rig.matrix_world @ t) for bn, (h, t) in P.items()}

    # Bake the pose into the mesh.
    bpy.context.view_layer.objects.active = body
    body.select_set(True)
    bpy.ops.object.modifier_apply(modifier="Armature")

    # Eye helper centres (baked with the pose: they follow the head, which is unposed, so read from Vb).
    eyes = {}
    for S, key in (("L", "eye_l"), ("R", "eye_r")):
        pts = Vb[d[key]]
        c = pts.mean(axis=0)
        r = float(np.linalg.norm(pts - c, axis=1).mean())
        eyes[S] = (Vector(c), r)

    # Fold MakeHuman groups into the game skeleton's groups.
    names = {g.index: g.name for g in body.vertex_groups}
    acc = {}
    for v in body.data.vertices:
        for g in v.groups:
            tgt = fold(names[g.group], bones)
            acc.setdefault(tgt, {}).setdefault(v.index, 0.0)
            acc[tgt][v.index] += g.weight
    for g in list(body.vertex_groups):
        body.vertex_groups.remove(g)
    for tgt, vs in acc.items():
        g = body.vertex_groups.new(name=tgt)
        for vi, wt in vs.items():
            g.add([vi], wt, "REPLACE")
    # Drop the helper/joint vertices no face uses.
    bm = bmesh.new()
    bm.from_mesh(body.data)
    bmesh.ops.delete(bm, geom=[v for v in bm.verts if not v.link_faces], context="VERTS")
    bm.to_mesh(body.data)
    bm.free()
    for p in body.data.polygons:
        p.use_smooth = True
    bpy.data.objects.remove(rig)

    # ---- game skeleton layout from the posed joints
    j = H.j
    head_top = P["head"][1]
    j["hip"] = (P["upperleg01.L"][0] + P["upperleg01.R"][0]) / 2
    j["hip"].x = 0
    j["spine"] = P["spine03"][0]
    j["chest"] = P["spine01"][0]
    j["neck"] = P["neck01"][0]
    j["head"] = P["head"][0]
    hr = (head_top.z - j["head"].z) / 1.8
    j["head_c"] = j["head"] + Vector((0, 0, hr * 0.8))
    for S in ("L", "R"):
        wr = P["wrist." + S][0]
        tip = P[f"finger3-3.{S}"][1]
        knuckles = sum((P[f"finger{f}-1.{S}"][0] for f in (2, 3, 4, 5)), Vector()) / 4
        j["shoulder_in." + S] = P["clavicle." + S][0]
        j["shoulder." + S] = P["upperarm01." + S][0]
        j["elbow." + S] = P["lowerarm01." + S][0]
        j["wrist." + S] = wr
        j["hand_tip." + S] = tip
        # Grip: inside the curled fist, just below the knuckle line.
        curl_pt = sum((P[f"finger{f}-2.{S}"][1] for f in (2, 3, 4, 5)), Vector()) / 4
        j["grip." + S] = knuckles.lerp(curl_pt, 0.55)
        j["hipj." + S] = P["upperleg01." + S][0]
        j["knee." + S] = P["lowerleg01." + S][0]
        j["ankle." + S] = P["foot." + S][0]
        j["toe." + S] = P["toe3-1." + S][0]
    H.P["head_r"] = hr
    H.height_est = head_top.z
    H.eyes = eyes
    body.data.color_attributes.new("Col", "BYTE_COLOR", "CORNER")
    AB.A.paint(body, AB.SKIN)
    return body
