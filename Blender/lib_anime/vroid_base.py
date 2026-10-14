"""Heroes built on VRoid's CC0 sample avatars (HairSample_Male / HairSample_Female, VRoid Studio beta).

Why: a realistic head with painted anime eyes reads as uncanny. VRoid's samples are made by pixiv's
artists as real anime game characters (textured face, eyes, brows, lashes, layered hair), released
under CC0 ("copyright is waived ... no particular limit when using them"; the VRM meta says
licenseName CC0, commercial use Allow). See Blender/third_party/vroid/README.md.

This module:
1. imports the .vrm (a glTF binary) and drops the expression shape keys the game does not use;
2. poses the VRoid skeleton from its T-pose into the game rest pose (arms near the sides, palms
   toward the thighs, relaxed fingers) and bakes that pose into the meshes;
3. folds VRoid's weights onto the game's 20-bone Humanoid skeleton and writes H.j from the posed
   joints, so lib_humanoid/motion.py clips play unchanged;
4. turns the model to face -Y, scales it to the hero height and joins it into one weighted body that
   keeps its textures (UVs + per-material images) plus a white "Col" layer for the toon shader;
5. offers texture recolouring (hair, eyes, clothes) so each hero gets its own palette.
"""
import math
import os

import bmesh
import bpy
import numpy as np
from mathutils import Matrix, Quaternion, Vector

HERE = os.path.dirname(os.path.abspath(__file__))
SOURCES = os.path.join(HERE, "..", "third_party", "vroid")

# VRoid bone (without the J_Bip_ prefix and side) -> game bone.
FOLD = {
    "C_Hips": "hips", "C_Spine": "spine", "C_Chest": "spine", "C_UpperChest": "chest",
    "C_Neck": "neck", "C_Head": "head",
    "Shoulder": "shoulder", "UpperArm": "upper_arm", "LowerArm": "forearm", "Hand": "hand",
    "UpperLeg": "thigh", "LowerLeg": "shin", "Foot": "foot",
}
CENTRE = {"hips", "spine", "chest", "neck", "head"}


def _fold(bone, bones):
    b = bones.get(bone)
    while b is not None:
        n = b.name
        if n.startswith("J_Bip_"):
            key = n[len("J_Bip_"):]
            if key.startswith(("L_", "R_")):
                side, part = key[0], key[2:]
                for k, g in FOLD.items():
                    if part == k:
                        return f"{g}.{side}"
            elif key in FOLD:
                return FOLD[key]
        b = b.parent
    return "hips"


def _import(path):
    before = set(bpy.context.scene.objects)
    bpy.ops.import_scene.gltf(filepath=path)
    new = [o for o in bpy.context.scene.objects if o not in before]
    for o in list(new):
        if o.type == "MESH" and (o.parent is None or not o.vertex_groups):
            bpy.data.objects.remove(o)  # VRoid ships a stray icosphere
    new = [o for o in bpy.context.scene.objects if o not in before]
    arm = next(o for o in new if o.type == "ARMATURE")
    meshes = [o for o in new if o.type == "MESH"]
    return arm, meshes


def _hair_root(rig, name):
    b = rig.data.bones.get(name)
    while b is not None and b.parent is not None and b.parent.name.startswith("HairJoint"):
        b = b.parent
    return b


def drop_hair(rig, meshes, drop):
    """Deletes the hair strands whose chain root satisfies drop(root_head) (native VRoid frame: +Y is the back,
    +X the character's right). Used to take off cat ears or twin tails."""
    for o in meshes:
        bm = bmesh.new()
        bm.from_mesh(o.data)
        dl = bm.verts.layers.deform.verify()
        names = {g.index: g.name for g in o.vertex_groups}
        cache, gone = {}, []
        for v in bm.verts:
            if not v[dl]:
                continue
            g = max(v[dl].items(), key=lambda kv: kv[1])[0]
            if g not in cache:
                root = _hair_root(rig, names[g])
                cache[g] = (root is not None and root.name.startswith("HairJoint")
                            and drop(rig.matrix_world @ root.head_local))
            if cache[g]:
                gone.append(v)
        if gone:
            bmesh.ops.delete(bm, geom=gone, context="VERTS")
            bm.to_mesh(o.data)
        bm.free()


def drop_islands(meshes, pred):
    """Deletes loose mesh parts for which pred(lo, hi, material_names) is true (bounds in the native frame)."""
    for o in meshes:
        bm = bmesh.new()
        bm.from_mesh(o.data)
        M = o.matrix_world
        seen, gone = set(), []
        for v in bm.verts:
            if v in seen:
                continue
            stack, comp = [v], []
            seen.add(v)
            while stack:
                a = stack.pop()
                comp.append(a)
                for e in a.link_edges:
                    b = e.other_vert(a)
                    if b not in seen:
                        seen.add(b)
                        stack.append(b)
            ps = np.array([tuple(M @ x.co) for x in comp])
            mats = {o.data.materials[f.material_index].name for x in comp for f in x.link_faces
                    if f.material_index < len(o.data.materials)}
            if pred(Vector(ps.min(axis=0)), Vector(ps.max(axis=0)), mats):
                gone += comp
        if gone:
            bmesh.ops.delete(bm, geom=gone, context="VERTS")
            bm.to_mesh(o.data)
        bm.free()


def female_ears(lo, hi, mats):
    """The cat ears of HairSample_Female: flat shells beside the crown (pink inner layer is HAIR_02)."""
    if any(m.endswith("HAIR_02") for m in mats):
        return True
    return (hi.z > 1.625 and lo.z > 1.51 and lo.y > -0.065 and hi.y < 0.036 and max(abs(lo.x), abs(hi.x)) > 0.12
            and min(abs(lo.x), abs(hi.x)) < 0.02)


def build(H, source, height=1.64, arm_down=None, curl=1.0, name="Body", hair_drop=None, island_drop=None):
    """Imports `source` (file name under third_party/vroid or a path) and returns the joined, weighted body.
    hair_drop(root_head) -> bool removes hair strands by their chain root (see drop_hair)."""
    path = source if os.path.isabs(source) else os.path.join(SOURCES, source)
    if path.endswith(".vrm"):
        # Blender's glTF importer keys on the extension; a VRM is a glTF binary.
        import shutil
        import tempfile
        tmp = os.path.join(tempfile.gettempdir(), os.path.basename(path)[:-4] + ".glb")
        shutil.copyfile(path, tmp)
        path = tmp
    rig, meshes = _import(path)
    for o in meshes:
        if o.data.shape_keys:
            o.shape_key_clear()
    if hair_drop is not None:
        drop_hair(rig, meshes, hair_drop)
    if island_drop is not None:
        drop_islands(meshes, island_drop)
    bones = {b.name: b for b in rig.data.bones}

    # ---- pose into the game rest pose (VRoid native frame: faces +Y, character left at -X)
    bpy.context.view_layer.objects.active = rig
    for pb in rig.pose.bones:
        pb.rotation_mode = "QUATERNION"
    front = Vector((0, 1, 0))

    def rotate_world(bn, axis, deg, pivot=None):
        pb = rig.pose.bones[bn]
        bpy.context.view_layer.update()
        M = rig.matrix_world @ pb.matrix
        piv = Vector(pivot) if pivot is not None else M.translation
        R = (Matrix.Translation(piv) @ Quaternion(Vector(axis).normalized(), math.radians(deg)).to_matrix().to_4x4()
             @ Matrix.Translation(-piv))
        pb.matrix = rig.matrix_world.inverted() @ R @ M
        bpy.context.view_layer.update()

    def head(bn):
        bpy.context.view_layer.update()
        return rig.matrix_world @ rig.pose.bones[bn].head

    def palm(S):
        bpy.context.view_layer.update()
        pb = rig.pose.bones[f"J_Bip_{S}_Hand"]
        rot = pb.matrix.to_3x3() @ pb.bone.matrix_local.to_3x3().inverted()
        return (rig.matrix_world.to_3x3() @ rot @ Vector((0, 0, -1))).normalized()  # T-pose palms face down

    def signed(u, v, axis):
        u = (u - axis * u.dot(axis)).normalized()
        v = (v - axis * v.dot(axis)).normalized()
        return math.degrees(math.atan2(axis.dot(u.cross(v)), u.dot(v)))

    angle = H.P["arm_angle"] if arm_down is None else arm_down
    for S, sg in (("L", -1), ("R", 1)):  # native: character left is -X
        b = lambda part: f"J_Bip_{S}_{part}"  # noqa: E731
        sh, el = head(b("UpperArm")), head(b("LowerArm"))
        cur = math.degrees(math.atan2(sg * (el.x - sh.x), sh.z - el.z))
        drop = cur - angle
        rotate_world(b("Shoulder"), (0, 1, 0), sg * drop * 0.10)
        rotate_world(b("UpperArm"), (0, 1, 0), sg * drop * 0.90)
        # Elbow: a relaxed bend forward.
        sh, el, wr = head(b("UpperArm")), head(b("LowerArm")), head(b("Hand"))
        want = ((el - sh).normalized() + Vector((-sg * 0.03, 0, 0)) + front * 0.17).normalized()
        fore = (wr - el).normalized()
        ax = fore.cross(want)
        if ax.length > 1e-6:
            rotate_world(b("LowerArm"), ax, math.degrees(fore.angle(want)), pivot=el)
        # Palms toward the thighs, a little forward.
        el, wr = head(b("LowerArm")), head(b("Hand"))
        fdir = (wr - el).normalized()
        twist = signed(palm(S), (Vector((-sg, 0, 0)) + front * 0.35).normalized(), fdir)
        rotate_world(b("LowerArm"), fdir, twist, pivot=el)
        # Relaxed fingers curl toward the palm; the thumb folds in less.
        for f in ("Thumb", "Index", "Middle", "Ring", "Little"):
            for k in (1, 2, 3):
                bn = b(f"{f}{k}")
                pb = rig.pose.bones[bn]
                bpy.context.view_layer.update()
                p0 = rig.matrix_world @ pb.head
                fd = (rig.matrix_world @ pb.tail - p0)
                # VRoid finger bones point up the bone's local Y (rest tails were re-aimed by the importer):
                # use the direction to the next joint instead.
                nxt = rig.pose.bones.get(b(f"{f}{k + 1}") if k < 3 else b(f"{f}3_end"))
                if nxt is not None:
                    fd = rig.matrix_world @ nxt.head - p0
                fd.normalize()
                axis = fd.cross(palm(S))
                if axis.length < 1e-6:
                    continue
                deg = (12, 16, 14)[k - 1] if f == "Thumb" else (28 + 6 * ("Index", "Middle", "Ring", "Little").index(f),
                                                                  44, 30)[k - 1]
                rotate_world(bn, axis, deg * curl, pivot=p0)
    bpy.context.view_layer.update()
    P = {bn: (rig.matrix_world @ pb.head).copy() for bn, pb in rig.pose.bones.items()}

    # ---- bake the pose, fold weights
    for o in meshes:
        bpy.context.view_layer.objects.active = o
        for md in list(o.modifiers):
            if md.type == "ARMATURE":
                bpy.ops.object.modifier_apply(modifier=md.name)
        names = {g.index: g.name for g in o.vertex_groups}
        acc = {}
        for v in o.data.vertices:
            for g in v.groups:
                tgt = _fold(names[g.group], bones)
                acc.setdefault(tgt, {}).setdefault(v.index, 0.0)
                acc[tgt][v.index] += g.weight
        for g in list(o.vertex_groups):
            o.vertex_groups.remove(g)
        for tgt, vs in acc.items():
            g = o.vertex_groups.new(name=tgt)
            for vi, wt in vs.items():
                g.add([vi], min(1.0, wt), "REPLACE")
        mw = o.matrix_world.copy()
        o.parent = None
        o.matrix_world = mw

    # ---- face -Y, stand on z = 0, scale to the hero height
    top = max((o.matrix_world @ v.co).z for o in meshes for v in o.data.vertices
              if (o.matrix_world @ v.co).z < P["J_Bip_C_Head"].z + 0.4)
    # The ahoge (single hair strand) is not the head: measure the skull top from the head bone instead.
    skull_top = P["J_Bip_C_Head"].z + (P["J_Bip_C_Head"].z - P["J_Bip_C_Neck"].z) * 2.15
    s = height / min(top, skull_top)
    M = Matrix.Scale(s, 4) @ Matrix.Rotation(math.pi, 4, "Z")
    for o in meshes:
        o.data.transform(M @ o.matrix_world)
        o.matrix_world = Matrix.Identity(4)
    P = {k: M @ v for k, v in P.items()}
    bpy.data.objects.remove(rig)

    for o in meshes:
        me = o.data
        if "Col" not in me.color_attributes:
            me.color_attributes.new("Col", "BYTE_COLOR", "CORNER")
        attr = me.color_attributes["Col"]
        cols = np.ones(len(attr.data) * 4, np.float32)
        attr.data.foreach_set("color", cols)
        for p in me.polygons:
            p.use_smooth = True
    bpy.ops.object.select_all(action="DESELECT")
    for o in meshes:
        o.select_set(True)
    bpy.context.view_layer.objects.active = meshes[0]
    bpy.ops.object.join()
    body = bpy.context.view_layer.objects.active
    body.name = name

    # ---- game skeleton layout from the posed joints
    j = H.j
    J = lambda n: P["J_Bip_" + n].copy()  # noqa: E731
    j["hip"] = (J("L_UpperLeg") + J("R_UpperLeg")) / 2
    j["hip"].x = 0
    j["spine"] = J("C_Spine")
    j["chest"] = J("C_UpperChest")
    j["neck"] = J("C_Neck")
    j["head"] = J("C_Head")
    hr = (height - j["head"].z) / 1.8
    j["head_c"] = j["head"] + Vector((0, 0, hr * 0.8))
    for S in ("L", "R"):
        knuckles = sum((J(f"{S}_{f}1") for f in ("Index", "Middle", "Ring", "Little")), Vector()) / 4
        curled = sum((J(f"{S}_{f}3") for f in ("Index", "Middle", "Ring", "Little")), Vector()) / 4
        j["shoulder_in." + S] = J(f"{S}_Shoulder")
        j["shoulder." + S] = J(f"{S}_UpperArm")
        j["elbow." + S] = J(f"{S}_LowerArm")
        j["wrist." + S] = J(f"{S}_Hand")
        j["hand_tip." + S] = J(f"{S}_Middle3_end")
        j["grip." + S] = knuckles.lerp(curled, 0.5)
        j["hipj." + S] = J(f"{S}_UpperLeg")
        j["knee." + S] = J(f"{S}_LowerLeg")
        j["ankle." + S] = J(f"{S}_Foot")
        j["toe." + S] = J(f"{S}_ToeBase")
    H.P["head_r"] = hr
    H.height_est = height
    H.eyes = {S: (P.get(f"J_Adj_{S}_FaceEye", j["head_c"]).copy(), 0.012) for S in ("L", "R")}
    # The '> <' expression layer only shows through blend shapes, which the game does not drive.
    drop_material(body, "EyeExtra")
    return body


# ---------------------------------------------------------------- textures

def image_of(mat):
    if not mat or not mat.node_tree:
        return None
    for n in mat.node_tree.nodes:
        if n.type == "TEX_IMAGE" and n.image is not None:
            return n.image
    return None


def materials(body, key):
    return [m for m in body.data.materials if m and key in m.name]


def _pixels(img):
    a = np.empty(img.size[0] * img.size[1] * 4, np.float32)
    img.pixels.foreach_get(a)
    return a.reshape(-1, 4)


def _store(img, a):
    img.pixels.foreach_set(a.reshape(-1).astype(np.float32))
    img.update()


def _srgb(c):
    c = c.lstrip("#")
    return np.array([int(c[i:i + 2], 16) / 255.0 for i in (0, 2, 4)], np.float32)


def gradient_map(body, key, stops, keep_bright=None, stretch=True):
    """Recolours every texture whose material name contains `key` by luminance through `stops`
    [(lum, '#rrggbb'), ...] (image pixels are display-referred sRGB values in Blender's float buffer).
    keep_bright: luminance above which pixels (specular glints, eye highlights) stay as authored."""
    done = set()
    for m in materials(body, key):
        img = image_of(m)
        if img is None or img.name in done:
            continue
        done.add(img.name)
        a = _pixels(img)
        rgb = a[:, :3]
        lum = rgb @ np.array([0.299, 0.587, 0.114], np.float32)
        mask = a[:, 3] > 0.02
        if stretch and mask.any():
            lo, hi = np.percentile(lum[mask], [2, 98])
            t = np.clip((lum - lo) / max(hi - lo, 1e-3), 0, 1)
        else:
            t = lum
        xs = np.array([s[0] for s in stops], np.float32)
        cols = np.stack([_srgb(s[1]) for s in stops])
        out = np.stack([np.interp(t, xs, cols[:, k]) for k in range(3)], axis=1)
        if keep_bright is not None:
            br = lum > keep_bright
            out[br] = rgb[br]
        a[:, :3] = out
        _store(img, a)


def tint(body, key, color, strength=1.0):
    """Multiplies the textures of matching materials by a colour (white cloth -> coloured cloth)."""
    done = set()
    c = _srgb(color)
    for m in materials(body, key):
        img = image_of(m)
        if img is None or img.name in done:
            continue
        done.add(img.name)
        a = _pixels(img)
        a[:, :3] = a[:, :3] * (1 - strength + strength * c)
        _store(img, a)


def drop_material(body, key):
    """Deletes the faces using matching materials (e.g. sneakers replaced by boots)."""
    idx = {i for i, m in enumerate(body.data.materials) if m and key in m.name}
    bm = bmesh.new()
    bm.from_mesh(body.data)
    bmesh.ops.delete(bm, geom=[f for f in bm.faces if f.material_index in idx], context="FACES")
    bmesh.ops.delete(bm, geom=[v for v in bm.verts if not v.link_faces], context="VERTS")
    bm.to_mesh(body.data)
    bm.free()
