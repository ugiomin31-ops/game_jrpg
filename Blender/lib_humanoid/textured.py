"""Textured heroes (VRoid-based builders in lib_anime/heroes_anime.py): texture export and FBX material setup.

Contract with Unity (Assets/_Game/Scripts/Editor/AbyssArtImporter.cs, TexturedMaterials):
- <dir>/<id>.fbx keeps the material names of the body. Untextured parts still use M_Toon / M_Emit / M_Clear,
  which Unity remaps to the shared Abyss/Toon materials as before.
- Every textured material <name> gets its image written to <dir>/<id>_tex/<name>.png (straight alpha, sRGB,
  downscaled to at most MAX_SIZE px for mobile). The file name IS the material name: Unity pairs them by name
  and builds one persistent Abyss/Toon material per texture in <dir>/<id>_mat/<name>.mat.
- Material-name suffixes from VRoid decide the Unity setup: _FACE / _EYE (alpha cutout, no outline, no shadow),
  _HAIR (cutout, double-sided), _CLOTH (double-sided), _SKIN and others (opaque).
"""
import contextlib
import os
import re

import bpy
import numpy as np

import abyss_bpy as A

MAX_SIZE = 1024
_UNSAFE = re.compile(r"[^A-Za-z0-9_\-]")


def image_of(mat):
    """First colour image of a material (VRoid materials hold exactly one), None for vertex-colour materials."""
    if mat is None or mat.name in A.MATERIALS or not mat.node_tree:
        return None
    for n in mat.node_tree.nodes:
        if n.type == "TEX_IMAGE" and n.image is not None and n.image.colorspace_settings.name != "Non-Color":
            return n.image
    return None


def is_textured(body):
    return any(image_of(m) for m in body.data.materials)


def remove_unused_slots(body):
    """Drops material slots no face uses (e.g. VRoid's expression-only eye layer, replaced shoes):
    they would otherwise reach Unity as empty materials and ship their textures."""
    me = body.data
    used = {p.material_index for p in me.polygons}
    names = [m.name if m else None for m in me.materials]
    before = {}
    for p in me.polygons:
        before[names[p.material_index]] = before.get(names[p.material_index], 0) + 1
    removed = []
    for i in reversed(range(len(me.materials))):
        if i not in used:
            removed.append(names[i])
            me.materials.pop(index=i)
    after = {}
    for p in me.polygons:
        n = me.materials[p.material_index].name if me.materials[p.material_index] else None
        after[n] = after.get(n, 0) + 1
    assert after == before, ("material indices shifted while removing slots", before, after)
    return removed


def _image_rgba(img):
    """Current (possibly recoloured in memory) pixels as an (h, w, 4) sRGB float array with straight alpha."""
    w, h = img.size
    a = np.empty(w * h * 4, np.float32)
    img.pixels.foreach_get(a)
    a = a.reshape(h, w, 4)
    if img.is_float and img.colorspace_settings.name not in ("sRGB", "Non-Color"):
        rgb = np.clip(a[..., :3], 0, 1)
        a[..., :3] = np.where(rgb <= 0.0031308, rgb * 12.92, 1.055 * np.power(rgb, 1 / 2.4) - 0.055)
    return a


def _downscale(a, max_size):
    """Integer box filter weighted by alpha, so the colour of transparent texels does not bleed into
    cut-out edges (lashes, brows, iris). Non-integer ratios fall back to a nearest-texel resample."""
    h, w = a.shape[:2]
    f = 1
    while max(w, h) / f > max_size:
        f *= 2
    if f == 1:
        return a
    if h % f or w % f:
        ys = (np.arange(h // f) * f + f // 2).clip(0, h - 1)
        xs = (np.arange(w // f) * f + f // 2).clip(0, w - 1)
        return a[ys][:, xs]
    blocks = a.reshape(h // f, f, w // f, f, 4)
    alpha = blocks[..., 3:4]
    wsum = alpha.sum(axis=(1, 3))
    rgb_w = (blocks[..., :3] * alpha).sum(axis=(1, 3))
    rgb_plain = blocks[..., :3].mean(axis=(1, 3))
    rgb = np.where(wsum > 1e-6, rgb_w / np.maximum(wsum, 1e-6), rgb_plain)
    return np.concatenate([rgb, wsum / (f * f)], axis=-1).astype(np.float32)


def _write_png(a, path):
    h, w = a.shape[:2]
    out = bpy.data.images.new("_abyss_tex_export", w, h, alpha=True)
    out.colorspace_settings.name = "sRGB"
    out.alpha_mode = "STRAIGHT"
    out.pixels.foreach_set(np.clip(a, 0, 1).reshape(-1))
    out.filepath_raw = path
    out.file_format = "PNG"
    out.save()
    bpy.data.images.remove(out)


def export_textures(body, tex_dir, max_size=MAX_SIZE):
    """Writes one PNG per textured material slot. Returns {slot index: info}. PNGs left over from an older
    export are deleted (with their Unity .meta); rewritten files keep their .meta so GUIDs stay stable."""
    os.makedirs(tex_dir, exist_ok=True)
    out, taken = {}, set()
    for i, m in enumerate(body.data.materials):
        img = image_of(m)
        if img is None:
            continue
        name = _UNSAFE.sub("_", m.name)
        base, k = name, 1
        while name.lower() in taken:
            k += 1
            name = f"{base}_{k}"
        taken.add(name.lower())
        a = _image_rgba(img)
        small = _downscale(a, max_size)
        path = os.path.join(tex_dir, name + ".png")
        _write_png(small, path)
        out[i] = dict(material=name, source_material=m.name, image=img.name, path=path,
                      source_size=list(img.size), size=[small.shape[1], small.shape[0]],
                      cutout_texels=round(float(np.mean(small[..., 3] < 0.5)), 4),
                      bytes=os.path.getsize(path))
    keep = {info["material"] + ".png" for info in out.values()}
    for f in os.listdir(tex_dir):
        if f.lower().endswith(".png") and f not in keep:
            os.remove(os.path.join(tex_dir, f))
            if os.path.exists(os.path.join(tex_dir, f + ".meta")):
                os.remove(os.path.join(tex_dir, f + ".meta"))
    return out


@contextlib.contextmanager
def fbx_materials(body, textures):
    """Temporarily swaps each textured slot for a plain Principled material of the same (safe) name whose
    Base Color / Alpha come from the exported PNG, so the FBX carries the material name plus a relative
    texture reference. The VRoid node trees and packed images are restored afterwards (the .blend keeps them)."""
    me = body.data
    swapped = []
    try:
        for i, info in textures.items():
            src = me.materials[i]
            original = src.name
            img = bpy.data.images.load(info["path"], check_existing=False)
            img.colorspace_settings.name = "sRGB"
            src.name = original + "__abyss_src"
            m = bpy.data.materials.new(info["material"])
            swapped.append((i, src, original, m, img))
            assert m.name == info["material"], (m.name, info["material"])
            m.use_nodes = True
            nt = m.node_tree
            bsdf = next(n for n in nt.nodes if n.type == "BSDF_PRINCIPLED")
            tex = nt.nodes.new("ShaderNodeTexImage")
            tex.image = img
            nt.links.new(tex.outputs["Color"], bsdf.inputs["Base Color"])
            nt.links.new(tex.outputs["Alpha"], bsdf.inputs["Alpha"])
            bsdf.inputs["Roughness"].default_value = 0.8
            m.use_backface_culling = src.use_backface_culling
            me.materials[i] = m
        yield
    finally:
        for i, src, original, m, img in reversed(swapped):
            me.materials[i] = src
            bpy.data.materials.remove(m)
            bpy.data.images.remove(img)
            src.name = original


def export_textured_fbx(rel_path, body, rig, max_size=MAX_SIZE):
    """FBX (rig + all clips, same settings as the vertex-colour heroes) plus <id>_tex/*.png next to it."""
    path = os.path.join(A.ASSETS, rel_path)
    stem = os.path.splitext(os.path.basename(path))[0]
    tex_dir = os.path.join(os.path.dirname(path), stem + "_tex")
    textures = export_textures(body, tex_dir, max_size)
    with fbx_materials(body, textures):
        A.export_fbx(rel_path, [body, rig], animated=True, path_mode="RELATIVE")
    return path, tex_dir, list(textures.values())
