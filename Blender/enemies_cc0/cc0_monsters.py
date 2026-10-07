"""Turn rigged + animated CC0 monster models (glTF) into game enemies that follow the Blender/README.md contract.

One call, ``build(eid)``, does everything for one enemy id listed in ``specs.SPECS``:

1. import the source glTF from ``THIRD_PARTY`` (+ optional extra glTF parts such as KayKit weapons),
2. drop helper objects (bone-shape icospheres), bone-parented parts become rigidly skinned,
3. bake each source material into the ``Col`` colour attribute (texture sampled per face corner, sRGB),
4. join everything into ONE skinned mesh ``Body`` under the armature object ``Rig``,
5. recolour with the per-enemy rules (palette swaps, emissive cracks, translucent bodies) and assign
   ONLY the slots M_Toon / M_Emit / M_Clear,
6. resample the source clips onto the seven game actions (Idle, Run, Attack, Cast, Hit, Die, Victory) at 30 fps:
   loops repeat or stretch to the README frame ranges, Attack's impact lands at 40 %, Cast's release at 60 %,
   Die holds its last pose,
7. fit to the size of the procedural enemy it replaces (feet on z=0, flyers keep their hover height),
8. add elite dressing (crowns, horns, spikes) rigidly bound to a bone,
9. export with ``abyss_bpy.export_fbx`` (same axis / scale settings as every other enemy) and render a preview.

Run one enemy:   blender -b --factory-startup -P Blender/enemies_cc0/cc0_monsters.py -- <enemy_id>
Run them all:    blender -b --factory-startup -P Blender/enemies_cc0/generate_all.py
"""
import colorsys
import math
import os
import sys

import bpy
from mathutils import Euler, Matrix, Vector

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "lib"))
sys.path.insert(0, HERE)
import abyss_bpy as A  # noqa: E402

# Source packs live here (see Blender/third_party/<pack>/README.md). Override with the env var
# ABYSS_CC0_DIR to build from a full pack download elsewhere.
THIRD_PARTY = os.environ.get("ABYSS_CC0_DIR") or os.path.normpath(os.path.join(HERE, "..", "third_party"))
REQUIRED = ("Idle", "Run", "Attack", "Cast", "Hit", "Die", "Victory")
LOOPS = ("Idle", "Run")


# ---------------------------------------------------------------- small colour utils

def hex3(h):
    h = h.lstrip("#")
    return (int(h[0:2], 16) / 255, int(h[2:4], 16) / 255, int(h[4:6], 16) / 255)


def to_hex(c):
    return "#%02x%02x%02x" % tuple(max(0, min(255, round(v * 255))) for v in c[:3])


def lin2srgb(x):
    return 12.92 * x if x <= 0.0031308 else 1.055 * x ** (1 / 2.4) - 0.055


def lum(c):
    return 0.2126 * c[0] + 0.7152 * c[1] + 0.0722 * c[2]


def dist(a, b):
    return math.sqrt(sum((a[i] - b[i]) ** 2 for i in range(3)))


# ---------------------------------------------------------------- import + clean

def source_path(rel):
    return os.path.join(THIRD_PARTY, rel)


def import_gltf(rel):
    path = source_path(rel)
    if not os.path.isfile(path):
        raise FileNotFoundError(f"CC0 source missing: {path} (see Blender/third_party/*/README.md)")
    before = set(bpy.data.objects)
    bpy.ops.import_scene.gltf(filepath=path)
    new = [o for o in bpy.data.objects if o not in before]
    # The glTF importer adds an "Icosphere" mesh as the bone display shape: never part of the model.
    for o in list(new):
        if o.type == "MESH" and o.name.startswith("Icosphere") and o.parent is None and not o.modifiers:
            new.remove(o)
            bpy.data.objects.remove(o)
    return new


def _sample_image(img):
    """Return (w, h, flat float list RGBA) of an image in its stored (sRGB for colour images) encoding."""
    w, h = img.size
    px = [0.0] * (w * h * 4)
    img.pixels.foreach_get(px)
    return w, h, px


def _material_source(mat):
    """('image', image) | ('flat', srgb colour) and whether the material glows."""
    nt = mat.node_tree if mat and mat.use_nodes else None
    if nt is None:
        c = mat.diffuse_color if mat else (0.8, 0.8, 0.8, 1)
        return ("flat", tuple(lin2srgb(v) for v in c[:3])), False
    bsdf = next((n for n in nt.nodes if n.type == "BSDF_PRINCIPLED"), None)
    glow = False
    if bsdf is not None:
        es = bsdf.inputs["Emission Strength"].default_value
        ec = bsdf.inputs["Emission Color"].default_value
        glow = es > 0.0 and max(ec[:3]) > 0.0
        if glow and not bsdf.inputs["Emission Color"].is_linked:
            return ("flat", tuple(lin2srgb(v) for v in ec[:3])), True
        inp = bsdf.inputs["Base Color"]
        if inp.is_linked:
            stack = [inp.links[0].from_node]
            while stack:
                n = stack.pop()
                if n.type == "TEX_IMAGE" and n.image:
                    return ("image", n.image), glow
                for i in n.inputs:
                    if i.is_linked:
                        stack.append(i.links[0].from_node)
        return ("flat", tuple(lin2srgb(v) for v in inp.default_value[:3])), glow
    return ("flat", (0.8, 0.8, 0.8)), False


def bake_colours(obj, cache):
    """Source materials -> Col (sRGB, face corner) + an int face attribute 'srcglow' (1 = emissive source)."""
    me = obj.data
    col = me.color_attributes.get("Col") or me.color_attributes.new("Col", "BYTE_COLOR", "CORNER")
    glow_attr = me.attributes.get("srcglow") or me.attributes.new("srcglow", "INT", "FACE")
    uv = me.uv_layers.active.data if me.uv_layers.active else None
    srcs = []
    for m in me.materials:
        src, glow = _material_source(m)
        if src[0] == "image":
            img = src[1]
            if img.name not in cache:
                cache[img.name] = _sample_image(img)
            src = ("image", cache[img.name])
        srcs.append((src, glow))
    for p in me.polygons:
        (kind, data), glow = srcs[p.material_index] if srcs else (("flat", (0.8, 0.8, 0.8)), False)
        glow_attr.data[p.index].value = 1 if glow else 0
        for li in p.loop_indices:
            if kind == "image" and uv is not None:
                w, h, px = data
                u, v = uv[li].uv
                x = int(math.floor((u % 1.0) * w)) % w
                y = int(math.floor((v % 1.0) * h)) % h
                k = (y * w + x) * 4
                c = (px[k], px[k + 1], px[k + 2])
            else:
                c = data if kind == "flat" else (0.8, 0.8, 0.8)
            col.data[li].color_srgb = (c[0], c[1], c[2], 1.0)
    return obj


def rest_pose(rig, rest=True):
    rig.data.pose_position = "REST" if rest else "POSE"
    bpy.context.view_layer.update()


def rigid_bind_bone_children(rig, meshes):
    """Bone-parented meshes (helmets, weapons) become rigidly skinned to that bone, in rest-pose world space."""
    rest_pose(rig, True)
    for o in meshes:
        if o.parent == rig and o.parent_type == "BONE":
            bone = o.parent_bone
            mw = o.matrix_world.copy()
            o.parent = None
            o.matrix_world = mw
            A.apply_transform(o)
            o.vertex_groups.clear()
            A.bind(o, bone)
            md = o.modifiers.new("Armature", "ARMATURE")
            md.object = rig
            o.parent = rig
            o.matrix_parent_inverse = Matrix.Identity(4)
    rest_pose(rig, False)


def attach_part(rig, rel, bone, offset=(0, 0, 0), rot=(0, 0, 0), scale=1.0):
    """Import an extra static glTF part (e.g. a weapon) and bind it rigidly to `bone`, positioned in the bone's
    rest frame (offset in bone-local metres, rot in degrees). Returns the new mesh objects."""
    objs = [o for o in import_gltf(rel) if o.type == "MESH"]
    rest_pose(rig, True)
    pb = rig.pose.bones[bone]
    base = rig.matrix_world @ pb.matrix
    local = Matrix.Translation(offset) @ Euler([math.radians(a) for a in rot]).to_matrix().to_4x4() \
        @ Matrix.Scale(scale, 4)
    for o in objs:
        o.parent = None
        o.matrix_world = base @ local @ o.matrix_world
        A.apply_transform(o)
        o.vertex_groups.clear()
        A.bind(o, bone)
        md = o.modifiers.new("Armature", "ARMATURE")
        md.object = rig
        o.parent = rig
        o.matrix_parent_inverse = Matrix.Identity(4)
    rest_pose(rig, False)
    return objs


# ---------------------------------------------------------------- recolour

def _hsv(c):
    return colorsys.rgb_to_hsv(*c[:3])


def _matches(rule, c, info):
    if "near" in rule:
        refs = rule["near"] if isinstance(rule["near"], (list, tuple)) else [rule["near"]]
        if not any(dist(c, hex3(r)) <= rule.get("tol", 0.10) for r in refs):
            return False
    if "hue" in rule or "sat" in rule or "val" in rule:
        h, s, v = _hsv(c)
        h *= 360
        if "hue" in rule:
            h0, h1 = rule["hue"]
            if not (h0 <= h <= h1 if h0 <= h1 else (h >= h0 or h <= h1)):
                return False
        if "sat" in rule and not (rule["sat"][0] <= s <= rule["sat"][1]):
            return False
        if "val" in rule and not (rule["val"][0] <= v <= rule["val"][1]):
            return False
    if "where" in rule and not rule["where"](info):
        return False
    if "glow" in rule and bool(info["glow"]) != rule["glow"]:
        return False
    return True


def _apply_to(rule, c):
    to = rule.get("to")
    if to is None:
        out = c
    elif callable(to):
        out = to(c)
    else:
        t = hex3(to)
        if rule.get("shade", True) and "near" in rule:
            ref = hex3(rule["near"] if isinstance(rule["near"], str) else rule["near"][0])
            k = (lum(c) + 0.02) / (lum(ref) + 0.02)
            k = max(0.6, min(1.4, k))
            out = tuple(min(1.0, t[i] * k) for i in range(3))
        else:
            out = t
    if "hue_shift" in rule or "sat_mul" in rule or "val_mul" in rule:
        h, s, v = _hsv(out)
        h = (h + rule.get("hue_shift", 0) / 360.0) % 1.0
        s = max(0, min(1, s * rule.get("sat_mul", 1)))
        v = max(0, min(1, v * rule.get("val_mul", 1)))
        out = colorsys.hsv_to_rgb(h, s, v)
    return out


def recolour(body, rules, tint=None, tint_k=0.0):
    """Apply rules (first match wins per face corner) and assign material slots per face.
    rule keys: near/tol, hue/sat/val, where(info), glow -> to (hex | fn), shade, hue_shift/sat_mul/val_mul, mat.
    info = {'p': face centre normalised to the model bounds (x,y in -1..1, z 0..1), 'n': normal, 'glow': bool,
            'bones': set of vertex-group names of the face}."""
    me = body.data
    col = me.color_attributes["Col"]
    glow = me.attributes.get("srcglow")
    xs = [v.co.x for v in me.vertices]
    ys = [v.co.y for v in me.vertices]
    zs = [v.co.z for v in me.vertices]
    cx, cy = (max(xs) + min(xs)) / 2, (max(ys) + min(ys)) / 2
    hx, hy = max((max(xs) - min(xs)) / 2, 1e-6), max((max(ys) - min(ys)) / 2, 1e-6)
    z0, hz = min(zs), max(max(zs) - min(zs), 1e-6)
    gnames = {g.index: g.name for g in body.vertex_groups}
    mats = []
    face_mat = []
    for p in me.polygons:
        c3 = p.center
        info = {"p": ((c3.x - cx) / hx, (c3.y - cy) / hy, (c3.z - z0) / hz), "n": tuple(p.normal), "co": c3.copy(),
                "glow": bool(glow.data[p.index].value) if glow else False, "index": p.index}
        v0 = me.vertices[p.vertices[0]]
        info["bones"] = {gnames[g.group] for g in v0.groups if g.weight > 0.5 and g.group in gnames}
        fm = "M_Emit" if info["glow"] else "M_Toon"
        for k, li in enumerate(p.loop_indices):
            c = tuple(col.data[li].color_srgb[:3])
            for rule in rules:
                if _matches(rule, c, info):
                    c = _apply_to(rule, c)
                    if k == 0 and "mat" in rule:
                        fm = rule["mat"]
                    break
            if tint is not None and tint_k > 0:
                c = tuple(c[i] * (1 - tint_k + tint_k * tint[i]) for i in range(3))
            col.data[li].color_srgb = (c[0], c[1], c[2], 1.0)
        face_mat.append(fm)
    me.materials.clear()
    for name in ("M_Toon", "M_Emit", "M_Clear"):
        if name in face_mat:
            me.materials.append(A._material(name))
            mats.append(name)
    for p, fm in zip(me.polygons, face_mat):
        p.material_index = mats.index(fm)
    if glow:
        me.attributes.remove(glow)
    return body


def subdivide(body, near=None, tol=0.06, cuts=1):
    """Split faces (all, or those whose first corner colour is near `near`) so recolour patterns such as
    mushroom spots or lava veins get round instead of blocky. Weights and Col are interpolated by bmesh."""
    import bmesh
    me = body.data
    col = me.color_attributes["Col"]
    keep = set()
    for p in me.polygons:
        if near is None or dist(tuple(col.data[p.loop_start].color_srgb[:3]), hex3(near)) <= tol:
            keep.add(p.index)
    bm = bmesh.new()
    bm.from_mesh(me)
    bm.faces.ensure_lookup_table()
    edges = list({e for i in keep for e in bm.faces[i].edges})
    bmesh.ops.subdivide_edges(bm, edges=edges, cuts=cuts, use_grid_fill=True)
    bm.to_mesh(me)
    bm.free()
    me.update()
    return body


def palette(body, top=24):
    """Distinct Col colours with face-corner counts and mean position (debug aid for writing rules)."""
    me = body.data
    col = me.color_attributes["Col"]
    acc = {}
    for p in me.polygons:
        for li in p.loop_indices:
            hx = to_hex(col.data[li].color_srgb)
            a = acc.setdefault(hx, [0, Vector()])
            a[0] += 1
            a[1] += p.center
    rows = sorted(acc.items(), key=lambda kv: -kv[1][0])[:top]
    return [(h, n, tuple(round(x, 2) for x in (s / n))) for h, (n, s) in rows]


# ---------------------------------------------------------------- actions

def _action_fcurves(act):
    try:
        return list(act.fcurves)
    except AttributeError:
        out = []
        for layer in act.layers:
            for strip in layer.strips:
                for bag in strip.channelbags:
                    out.extend(bag.fcurves)
        return out


def assign_action(rig, act):
    rig.animation_data_create()
    rig.animation_data.action = act
    if act is not None and hasattr(act, "slots") and len(act.slots) and rig.animation_data.action_slot is None:
        rig.animation_data.action_slot = act.slots[0]


def _pose_at(rig, act, t):
    sc = bpy.context.scene
    assign_action(rig, act)
    f = math.floor(t)
    sc.frame_set(int(f), subframe=float(t - f))
    return {pb.name: (pb.location.copy(), pb.rotation_quaternion.copy() if pb.rotation_mode == "QUATERNION"
                      else pb.rotation_euler.to_quaternion(), pb.scale.copy()) for pb in rig.pose.bones}


def _reach(rig, bones):
    """Most forward (-Y) point of the given bones in the current pose (attack impact detector)."""
    best = -1e9
    for name in bones:
        pb = rig.pose.bones.get(name)
        if pb:
            for p in (pb.head, pb.tail):
                best = max(best, -(rig.matrix_world @ p).y)
    return best


def find_impact(rig, act, bones, lo=0.15, hi=0.85):
    """Source frame where `bones` reach furthest forward (between lo..hi of the clip)."""
    a, b = act.frame_range
    best, bt = -1e9, a + (b - a) * 0.4
    n = int(b - a)
    for i in range(n + 1):
        t = a + i
        if not (a + (b - a) * lo <= t <= a + (b - a) * hi):
            continue
        _pose_at(rig, act, t)
        r = _reach(rig, bones)
        if r > best:
            best, bt = r, t
    return bt


def _time_map(spec, src_len, L):
    """Return fn(target frame) -> source frame for one clip spec."""
    s0 = spec.get("start", 0.0)
    s1 = spec.get("end", src_len)
    span = s1 - s0
    if spec.get("loop") or spec.get("repeat", 1) > 1:
        rep = spec.get("repeat", 1)
        return lambda f: s0 + ((f / L) * rep * span) % span if f < L else s0 + 0.0
    key = spec.get("key")          # (source frame, target fraction) -> piecewise-linear remap
    if key is not None:
        ks, kt = key
        kt *= L
        play = spec.get("play")    # target length the source span plays over (rest = hold)
        end = play if play else L

        def fn(f):
            if f <= kt:
                return s0 + (ks - s0) * (f / kt if kt else 1)
            if f >= end:
                return s1
            return ks + (s1 - ks) * ((f - kt) / (end - kt))
        return fn
    play = spec.get("play", L)     # e.g. Die: play the source over `play` frames then hold
    return lambda f: s0 + span * min(1.0, f / play)


def resample(rig, name, src, L, spec):
    """Bake a new action `name` of length L (frames 0..L) by sampling the source action through the time map."""
    fn = _time_map(spec, src.frame_range[1] - src.frame_range[0], L)
    off = src.frame_range[0]
    frames = []
    for f in range(L + 1):
        frames.append(_pose_at(rig, src, off + fn(f)))
    if spec.get("loop") or spec.get("repeat", 1) > 1:
        frames[-1] = frames[0]
    extra = spec.get("extra")      # fn(bone, f, L) -> (dloc, dquat) additive tweaks (e.g. a flyer's death drop)
    act = bpy.data.actions.new(name)
    act.use_fake_user = True
    assign_action(rig, None)
    rig.animation_data.action = act
    for pb in rig.pose.bones:
        pb.rotation_mode = "QUATERNION"
        prev = None
        locs, rots, scls = [], [], []
        for f, pose in enumerate(frames):
            loc, q, s = pose[pb.name]
            q = q.copy()
            if extra:
                d = extra(pb.name, f, L)
                if d:
                    loc = loc + Vector(d[0])
                    q = Euler([math.radians(x) for x in d[1]]).to_quaternion() @ q
            if prev is not None and prev.dot(q) < 0:
                q.negate()
            prev = q
            locs.append(loc)
            rots.append(q)
            scls.append(s)
        for path, seq, n in (("location", locs, 3), ("rotation_quaternion", rots, 4), ("scale", scls, 3)):
            dp = f'pose.bones["{pb.name}"].{path}'
            for i in range(n):
                if hasattr(act, "fcurve_ensure_for_datablock"):
                    fc = act.fcurve_ensure_for_datablock(rig, dp, index=i, group_name=pb.name)
                else:
                    fc = act.fcurves.new(dp, index=i, action_group=pb.name)
                fc.keyframe_points.add(len(seq))
                co = []
                for f, v in enumerate(seq):
                    co += [float(f), float(v[i])]
                fc.keyframe_points.foreach_set("co", co)
                for kp in fc.keyframe_points:
                    kp.interpolation = "LINEAR"
                fc.update()
    act.frame_range = (0, L)
    act.use_frame_range = True
    assign_action(rig, None)
    return act


def build_actions(rig, clips, impact_bones):
    """clips: {target: dict(src=..., len=..., [loop, repeat, play, hit, cast, start, end, extra])}.
    'hit' (Attack) -> impact auto-detected on impact_bones lands at 40 %; 'cast' = source release fraction -> 60 %."""
    src_actions = {a.name: a for a in bpy.data.actions}
    out = {}
    for name in REQUIRED:
        spec = dict(clips[name])
        src = src_actions[spec["src"]]
        L = int(spec["len"])
        if name == "Attack" and "key" not in spec:
            ks = spec.get("hit_frame") or find_impact(rig, src, spec.get("reach", impact_bones))
            spec["key"] = (ks - src.frame_range[0], 0.40)
        if name == "Cast" and "key" not in spec:
            a, b = spec.get("start", 0.0), spec.get("end", src.frame_range[1] - src.frame_range[0])
            spec["key"] = (a + (b - a) * spec.get("release", 0.5), 0.60)
        if name in LOOPS:
            spec["loop"] = True
        out[name] = resample(rig, "__new_" + name, src, L, spec)
    for a in list(bpy.data.actions):
        if a not in out.values():
            bpy.data.actions.remove(a)
    for name, a in out.items():
        a.name = name
    return out


def scale_action_locations(actions, s):
    for act in actions:
        for fc in _action_fcurves(act):
            if fc.data_path.endswith(".location"):
                for kp in fc.keyframe_points:
                    kp.co.y *= s
                    kp.handle_left.y *= s
                    kp.handle_right.y *= s
                fc.update()


# ---------------------------------------------------------------- body / fit

def join_body(rig, meshes):
    meshes = [o for o in meshes if o.type == "MESH"]
    for o in meshes:
        if not any(m.type == "ARMATURE" for m in o.modifiers):
            # unskinned part parented to the armature object: give it to the root bone
            A.bind(o, rig.data.bones[0].name)
            md = o.modifiers.new("Armature", "ARMATURE")
            md.object = rig
    bpy.ops.object.select_all(action="DESELECT")
    for o in meshes:
        o.select_set(True)
    bpy.context.view_layer.objects.active = meshes[0]
    bpy.ops.object.join()
    body = bpy.context.active_object
    body.name = body.data.name = "Body"
    # one armature modifier, pointing at the rig
    mods = [m for m in body.modifiers if m.type == "ARMATURE"]
    for m in mods[1:]:
        body.modifiers.remove(m)
    mods[0].object = rig
    mods[0].name = "Armature"
    body.parent = rig
    body.matrix_parent_inverse = Matrix.Identity(4)
    for p in body.data.polygons:
        p.use_smooth = True
    return body


def mesh_bounds(body, rig=None, action=None, frame=0):
    if rig is not None and action is not None:
        assign_action(rig, action)
        bpy.context.scene.frame_set(frame)
    dg = bpy.context.evaluated_depsgraph_get()
    be = body.evaluated_get(dg)
    me = be.to_mesh()
    pts = [be.matrix_world @ v.co for v in me.vertices]
    be.to_mesh_clear()
    lo = Vector((min(p.x for p in pts), min(p.y for p in pts), min(p.z for p in pts)))
    hi = Vector((max(p.x for p in pts), max(p.y for p in pts), max(p.z for p in pts)))
    return lo, hi


def fit(rig, body, actions, target, mode="height"):
    """Uniformly scale + move so the Idle pose matches target=(height, bottom_z, width) of the old enemy
    (any entry may be None: that dimension is then not matched).
    mode: 'height' | 'width' | 'mean' (geometric mean of the two ratios, for wide-winged flyers)."""
    lo, hi = mesh_bounds(body, rig, actions["Idle"], 0)
    th, tz, tw = target
    sh = th / (hi.z - lo.z) if th else None
    sw = tw / (hi.x - lo.x) if tw else None
    if sh is None or sw is None:
        s = sh or sw
    else:
        s = {"height": sh, "width": sw, "mean": math.sqrt(sh * sw), "min": min(sh, sw)}[mode]
    assign_action(rig, None)
    rig.scale = (s, s, s)
    # keep the source's own pivot (feet / body under the origin); tz=None keeps the source's (scaled) hover height
    rig.location = (0.0, 0.0, 0.0 if tz is None else tz - lo.z * s)
    bpy.context.view_layer.update()
    mw = body.matrix_world.copy()
    body.parent = None
    body.matrix_world = mw
    A.apply_transform(body)
    A.apply_transform(rig)
    body.parent = rig
    body.matrix_parent_inverse = Matrix.Identity(4)
    scale_action_locations(actions.values(), s)
    return s


def drop_unused_deform(rig, body):
    """Bones that weigh no vertex (and have no weighted descendant) are flagged non-deform so the FBX
    exporter's deform-only option leaves out IK targets and controls."""
    weighted = set()
    idx = {g.index: g.name for g in body.vertex_groups}
    for v in body.data.vertices:
        for g in v.groups:
            if g.weight > 0:
                weighted.add(idx[g.group])

    def needed(b):
        return b.name in weighted or any(needed(c) for c in b.children)
    for b in rig.data.bones:
        b.use_deform = needed(b)


# ---------------------------------------------------------------- elite dressing

def bone_cap(body, bones, axis=2, top=True):
    """Centre + extreme point of the vertices weighted to `bones` (rest pose, world space)."""
    idx = {g.name: g.index for g in body.vertex_groups}
    ids = {idx[b] for b in bones if b in idx}
    pts = [body.matrix_world @ v.co for v in body.data.vertices if any(g.group in ids and g.weight > 0.5 for g in v.groups)]
    if not pts:
        pts = [body.matrix_world @ v.co for v in body.data.vertices]
    ext = max(p[axis] for p in pts) if top else min(p[axis] for p in pts)
    lo = Vector((min(p.x for p in pts), min(p.y for p in pts), min(p.z for p in pts)))
    hi = Vector((max(p.x for p in pts), max(p.y for p in pts), max(p.z for p in pts)))
    return (lo + hi) / 2, ext, lo, hi


def add_parts(rig, body, parts):
    """parts: list of (bone, object) built in final world space; joined into Body with rigid weights."""
    if not parts:
        return body
    objs = []
    for bone, o in parts:
        A.bind(o, bone)
        objs.append(o)
    for o in objs:
        A.apply_transform(o)
    mats_before = [m.name for m in body.data.materials]
    bpy.ops.object.select_all(action="DESELECT")
    for o in objs:
        o.select_set(True)
    body.select_set(True)
    bpy.context.view_layer.objects.active = body
    bpy.ops.object.join()
    body = bpy.context.active_object
    # join may duplicate slots: collapse by name
    me = body.data
    names = [m.name.split(".")[0] for m in me.materials]
    order = []
    for n in ("M_Toon", "M_Emit", "M_Clear"):
        if n in names:
            order.append(n)
    remap = {i: order.index(n) for i, n in enumerate(names)}
    for p in me.polygons:
        p.material_index = remap[p.material_index]
    me.materials.clear()
    for n in order:
        me.materials.append(A._material(n))
    del mats_before
    return body


def crown(at, r, color="#f2c14e", gem="#ff4f6a", points=5, h=None):
    """Small spiked crown centred at `at` (base) with radius r."""
    h = h or r * 0.9
    parts = [A.cyl("crown_band", r=r, depth=h * 0.45, loc=(at.x, at.y, at.z + h * 0.22), color=color, seg=24)]
    for i in range(points):
        a = 2 * math.pi * i / points + math.pi / 2
        p = (at.x + math.cos(a) * r * 0.92, at.y + math.sin(a) * r * 0.92, at.z + h * 0.42)
        parts.append(A.cone(f"crown_spike{i}", r=r * 0.28, depth=h * 0.75, loc=(p[0], p[1], p[2] + h * 0.3),
                            color=color, seg=8))
        parts.append(A.sphere(f"crown_gem{i}", r=r * 0.11, loc=(at.x + math.cos(a) * r * 1.0, at.y + math.sin(a) * r * 1.0,
                                                                 at.z + h * 0.22), color=gem, mat="M_Emit", seg=10, rings=6))
    return A.join(parts, "crown")


def horn(base, tip, r, color, mat="M_Toon", bend=(0, 0, 0)):
    mid = [(base[i] + tip[i]) / 2 + bend[i] for i in range(3)]
    return A.tube("horn", [base, mid, tip], radius=r, color=color, mat=mat, seg=10, taper_end=0.12)


def spikes_on(body, bones, n, length, r, color, mat="M_Toon", seed=1, up_only=True):
    """Cones sprouting from random upward-facing points of the given bones' surface."""
    import random
    rnd = random.Random(seed)
    idx = {g.name: g.index for g in body.vertex_groups}
    ids = {idx[b] for b in bones if b in idx}
    me = body.data
    cand = [p for p in me.polygons if (not up_only or p.normal.z > 0.35)
            and any(g.group in ids and g.weight > 0.5 for g in me.vertices[p.vertices[0]].groups)]
    out = []
    for i in range(min(n, len(cand))):
        p = cand[rnd.randrange(len(cand))]
        c = body.matrix_world @ p.center
        nrm = (body.matrix_world.to_3x3() @ p.normal).normalized()
        o = A.cone(f"spike{i}", r=r, depth=length, loc=(0, 0, 0), color=color, mat=mat, seg=8)
        o.rotation_mode = "QUATERNION"
        o.rotation_quaternion = nrm.to_track_quat("Z", "Y")
        o.location = c + nrm * length * 0.35
        out.append(o)
    return out


# ---------------------------------------------------------------- preview

def render_cell(path, rig, body, action=None, frame=0, size=512, angle=(72, 0, 32), engine="WORKBENCH", bounds=None):
    sc = bpy.context.scene
    if action:
        assign_action(rig, bpy.data.actions[action])
        sc.frame_set(frame)
    lo, hi = bounds or mesh_bounds(body)
    center = (lo + hi) / 2
    radius = max((hi - lo).length / 2, 0.2)
    cam = bpy.data.objects.get("PreviewCam")
    if cam is None:
        cam = bpy.data.objects.new("PreviewCam", bpy.data.cameras.new("PreviewCam"))
        sc.collection.objects.link(cam)
    cam.data.lens = 50
    e = Euler([math.radians(a) for a in angle])
    cam.location = center + (e.to_matrix() @ Vector((0, 0, 1))) * radius * 3.0
    cam.rotation_euler = e
    sc.camera = cam
    setup_look(sc, engine)
    sc.render.resolution_x = sc.render.resolution_y = size
    sc.render.filepath = path
    bpy.ops.render.render(write_still=True)
    return path


def setup_look(sc, engine="WORKBENCH"):
    sc.render.engine = "BLENDER_WORKBENCH"
    sh = sc.display.shading
    sh.light = "STUDIO"
    sh.color_type = "VERTEX"
    sh.show_cavity = False
    sh.show_object_outline = True
    sh.object_outline_color = (0.08, 0.06, 0.1)
    sh.show_shadows = False
    sh.show_specular_highlight = False
    sc.render.film_transparent = False
    if sc.world is None:
        sc.world = bpy.data.worlds.new("W")
    sc.world.color = (0.16, 0.16, 0.2)
    sc.display_settings.display_device = "sRGB"
    sc.view_settings.view_transform = "Standard"


# ---------------------------------------------------------------- driver

def build(eid, export=True, preview=True, save=True, verbose=True):
    import specs
    spec = specs.ALL[eid]
    A.reset_scene()
    sc = bpy.context.scene
    sc.render.fps = A.FPS
    objs = import_gltf(spec["source"])
    rig = next(o for o in objs if o.type == "ARMATURE")
    meshes = [o for o in objs if o.type == "MESH" and o.name.split(".")[0] not in spec.get("drop", ())]
    for o in objs:
        if o.type == "MESH" and o not in meshes:
            bpy.data.objects.remove(o)
    rig.name = "Rig"
    rig.data.name = "Rig"
    for pb in rig.pose.bones:
        pb.custom_shape = None
    rigid_bind_bone_children(rig, meshes)
    for part in spec.get("attach", ()):
        meshes += attach_part(rig, **part)
    cache = {}
    for o in meshes:
        bake_colours(o, cache)
    body = join_body(rig, meshes)
    if verbose:
        print("PALETTE", eid, palette(body), flush=True)
    actions = build_actions(rig, spec["clips"], spec.get("impact_bones", ()))
    tgt = specs.TARGETS[eid]
    s = fit(rig, body, actions, tgt, spec.get("fit", "height"))
    for sub in spec.get("subdivide", ()):
        subdivide(body, **sub)
    recolour(body, spec.get("rules", ()), spec.get("tint"), spec.get("tint_k", 0.0))
    if spec.get("dress"):
        body = add_parts(rig, body, spec["dress"](rig, body))
    drop_unused_deform(rig, body)
    # remove any leftover object that is not the rig or the body
    for o in list(sc.objects):
        if o not in (rig, body):
            bpy.data.objects.remove(o)
    assign_action(rig, None)
    for pb in rig.pose.bones:
        pb.location = (0, 0, 0)
        pb.rotation_quaternion = (1, 0, 0, 0)
        pb.scale = (1, 1, 1)
    result = {"id": eid, "source": spec["source"], "scale": s,
              "triangles": sum(len(p.vertices) - 2 for p in body.data.polygons),
              "bones": len(rig.data.bones), "materials": [m.name for m in body.data.materials]}
    if export:
        result["fbx"] = A.export_fbx(f"Enemies/{eid}/{eid}.fbx", objects=[rig, body], animated=True)
    if save:
        A.save_blend("enemy_cc0_" + eid)
    if preview:
        os.makedirs(A.PREVIEW_DIR, exist_ok=True)
        render_cell(os.path.join(A.PREVIEW_DIR, f"enemy_cc0_{eid}.png"), rig, body, "Idle", 0)
        assign_action(rig, None)
    print("CC0_BUILT", result, flush=True)
    return result


if __name__ == "__main__":
    argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
    for eid in argv:
        build(eid)
