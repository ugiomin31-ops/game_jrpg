"""Inspect/clean the existing Tripo station in Blender; writes only its processed directory.

blender --background --factory-startup --threads 4 --python-exit-code 1
        --python Tools/prepare_guild_field_station.py -- --stage inspect
No authored geometry/textures are generated; render cameras and lights are evidence-only.
"""
import argparse
import hashlib
import json
import math
from pathlib import Path
import shutil
import sys
import zipfile

import bpy
from mathutils import Matrix, Vector

ROOT = Path(__file__).resolve().parents[1]
ASSET = ROOT / "ArtSource/Tripo/enrichment-20261015/guild_field_gear_station"
RAW = ASSET / "raw"
OUT = ASSET / "processed"
TEXTURE_FOLDER = "guild_field_gear_station_tex"
EXPECTED_RAW = {
    "guild_field_gear_station.zip": "fd89c9e1560263679fa9713a749ae54f721339be9226997d019998e1e307fe6e",
    "tripo_convert_3551cec0-36df-4f5c-89e6-92c921944d29.fbx": "7ab5a2bbfbace46bbf52549b181f23485625e1d2cf9bf0ee26d40f503b2bb040",
}


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def raw_hashes():
    result = {name: sha(RAW / name) for name in EXPECTED_RAW}
    if result != EXPECTED_RAW:
        raise ValueError("Raw inputs differ from the recorded baseline")
    return result


def write_json(name, data):
    (OUT / name).write_text(json.dumps(data, indent=2, allow_nan=False) + "\n", encoding="utf-8")


def working_source():
    folder = OUT / "source_input"
    folder.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(RAW / "guild_field_gear_station.zip") as archive:
        for entry in archive.infolist():
            target = (folder / entry.filename).resolve()
            if not target.is_relative_to(folder.resolve()):
                raise ValueError("Unsafe archive path")
            if entry.is_dir():
                target.mkdir(parents=True, exist_ok=True)
                continue
            target.parent.mkdir(parents=True, exist_ok=True)
            content = archive.read(entry)
            if not target.exists():
                target.write_bytes(content)
            elif target.read_bytes() != content:
                raise ValueError("Working source already contains different bytes: " + str(target))
    fbx = next(folder.glob("*.fbx"))
    if sha(fbx) != EXPECTED_RAW[fbx.name]:
        raise ValueError("ZIP FBX and loose raw FBX do not match")
    return fbx


def bounds(meshes):
    points = [obj.matrix_world @ v.co for obj in meshes for v in obj.data.vertices]
    if not points or any(not math.isfinite(c) for p in points for c in p):
        raise ValueError("Empty or nonfinite mesh")
    lo = Vector(tuple(min(p[i] for p in points) for i in range(3)))
    hi = Vector(tuple(max(p[i] for p in points) for i in range(3)))
    return {"min": list(lo), "max": list(hi), "dimensions": list(hi - lo)}


def inspection(meshes):
    report = {"bounds_blender_xyz": bounds(meshes), "meshes": [], "materials": [], "images": []}
    for obj in meshes:
        data = obj.data
        data.calc_loop_triangles()
        report["meshes"].append({
            "name": obj.name, "vertices": len(data.vertices), "polygons": len(data.polygons),
            "triangles": len(data.loop_triangles), "uv_layers": [uv.name for uv in data.uv_layers],
            "invalid_uv_values": sum(not math.isfinite(c) for uv in data.uv_layers for item in uv.data for c in item.uv),
            "zero_area_triangles": sum(t.area < 1e-12 for t in data.loop_triangles),
            "material_slots": [m.name if m else None for m in data.materials],
            "invalid_material_indices": sum(p.material_index >= len(data.materials) for p in data.polygons),
            "location": list(obj.location), "rotation": list(obj.rotation_euler), "scale": list(obj.scale),
            "local_dimensions": [max(v.co[i] for v in data.vertices) - min(v.co[i] for v in data.vertices) for i in range(3)],
        })
    report["triangles"] = sum(m["triangles"] for m in report["meshes"])
    materials = {m for obj in meshes for m in obj.data.materials if m}
    for mat in sorted(materials, key=lambda m: m.name):
        report["materials"].append({
            "name": mat.name, "use_nodes": mat.use_nodes,
            "links": [[l.from_node.name, l.from_socket.name, l.to_node.name, l.to_socket.name]
                      for l in mat.node_tree.links] if mat.use_nodes else [],
            "principled": [{"node": n.name, "inputs": {s.name: list(s.default_value) if hasattr(s.default_value, "__len__") else s.default_value
                            for s in n.inputs if hasattr(s, "default_value") and not s.is_linked}}
                           for n in mat.node_tree.nodes if n.type == "BSDF_PRINCIPLED"] if mat.use_nodes else [],
        })
    for img in bpy.data.images:
        if img.source == "FILE":
            report["images"].append({"name": img.name, "size": list(img.size), "path": img.filepath,
                                     "color_space": img.colorspace_settings.name, "loaded": img.has_data})
    report["armatures"] = sum(o.type == "ARMATURE" for o in bpy.context.scene.objects)
    return report


def bind_textures(meshes):
    """Preserve authored pixels; correct FBX's legacy specular mapping to metallic PBR."""
    texture_dir = OUT / TEXTURE_FOLDER
    texture_dir.mkdir(exist_ok=True)
    files = {}
    for channel in ("basecolor", "metallic", "roughness", "normal"):
        source = next((OUT / "source_input").rglob("*_" + channel + ".PNG"))
        target = texture_dir / source.name
        shutil.copyfile(source, target)
        files[channel] = target
    materials = {m for obj in meshes for m in obj.data.materials if m}
    for mat in materials:
        nodes, links = mat.node_tree.nodes, mat.node_tree.links
        shader = next(n for n in nodes if n.type == "BSDF_PRINCIPLED")
        for channel, socket in (("basecolor", "Base Color"), ("metallic", "Metallic"), ("roughness", "Roughness")):
            node = next((n for n in nodes if n.type == "TEX_IMAGE" and n.image
                         and Path(n.image.filepath).name == files[channel].name), None)
            if node is None:
                node = nodes.new("ShaderNodeTexImage")
                node.image = bpy.data.images.load(str(files[channel]), check_existing=True)
            node.image.filepath = str(files[channel])
            node.image.colorspace_settings.name = "sRGB" if channel == "basecolor" else "Non-Color"
            links.new(node.outputs["Color"], shader.inputs[socket])
        # Tripo FBX connects its metallic image to the legacy specular input on import.
        for link in list(shader.inputs["Specular IOR Level"].links):
            links.remove(link)
        shader.inputs["Specular IOR Level"].default_value = 0.5
        for node in nodes:
            if node.type == "TEX_IMAGE" and node.image:
                candidate = texture_dir / Path(node.image.filepath).name
                if candidate.exists():
                    node.image.filepath = str(candidate)
    return [{"channel": c, "file": p.relative_to(OUT).as_posix(), "sha256": sha(p)} for c, p in files.items()]


def normalize(meshes):
    box = bounds(meshes)
    size = box["dimensions"]
    scale = (1.4 / size[0], 1.4 / size[0], 1.05 / size[2])
    offset = Vector((-(box["min"][0] + box["max"][0]) / 2,
                     -(box["min"][1] + box["max"][1]) / 2, -box["min"][2]))
    transform = Matrix.Diagonal((*scale, 1.0)) @ Matrix.Translation(offset)
    bpy.ops.object.select_all(action="DESELECT")
    for obj in meshes:
        matrix = transform @ obj.matrix_world
        obj.parent = None
        obj.matrix_world = matrix
        obj.select_set(True)
    bpy.context.view_layer.objects.active = meshes[0]
    bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)
    bpy.context.view_layer.update()
    return {"scale_xyz": list(scale), "pre_scale_translation": list(offset),
            "origin": "bottom center, applied transforms", "dimensions": bounds(meshes)["dimensions"]}


def render_setup():
    scene = bpy.context.scene
    scene.unit_settings.system = "METRIC"
    scene.unit_settings.scale_length = 1.0
    scene.render.engine = "CYCLES"
    scene.cycles.device = "CPU"
    scene.cycles.samples = 24
    scene.cycles.use_denoising = True
    scene.cycles.seed = 19
    scene.render.threads_mode = "FIXED"
    scene.render.threads = 4
    scene.render.resolution_x = scene.render.resolution_y = 960
    scene.render.resolution_percentage = 100
    scene.render.image_settings.file_format = "PNG"
    scene.render.image_settings.color_mode = "RGBA"
    scene.render.film_transparent = False
    scene.world = bpy.data.worlds.new("Evidence_NeutralWorld")
    scene.world.use_nodes = True
    background = scene.world.node_tree.nodes.get("Background")
    background.inputs["Color"].default_value = (0.35, 0.35, 0.35, 1)
    background.inputs["Strength"].default_value = 0.6
    scene.view_settings.view_transform = "AgX"
    target = Vector((0, 0, 0.52))
    for name, position, power, size in (
        ("Key", (0, -3, 4), 650, 3), ("Fill", (3, 1, 2), 450, 3), ("Rim", (-3, 2, 3), 700, 2)):
        data = bpy.data.lights.new("Evidence_" + name, "AREA")
        data.energy, data.size = power, size
        obj = bpy.data.objects.new(data.name, data)
        scene.collection.objects.link(obj)
        obj.location = position
        obj.rotation_euler = (target - obj.location).to_track_quat("-Z", "Y").to_euler()
    cameras = []
    for name, position in (("front", (2.1, -3.2, 2.1)), ("rear", (-2.1, 3.2, 2.1))):
        data = bpy.data.cameras.new("Evidence_" + name)
        data.type, data.ortho_scale = "ORTHO", 1.95
        obj = bpy.data.objects.new(data.name, data)
        scene.collection.objects.link(obj)
        obj.location = position
        obj.rotation_euler = (target - obj.location).to_track_quat("-Z", "Y").to_euler()
        cameras.append((name, obj))
    return cameras


def render_views(prefix, cameras):
    evidence = OUT / "evidence"
    evidence.mkdir(exist_ok=True)
    for name, cam in cameras:
        scene = bpy.context.scene
        scene.camera = cam
        scene.render.filepath = str(evidence / (prefix + "-" + name + ".png"))
        print("RENDER_START " + scene.render.filepath, flush=True)
        bpy.ops.render.render(write_still=True)
        print("RENDER_DONE " + scene.render.filepath, flush=True)


def validate(report):
    if not report["meshes"] or report["armatures"]:
        raise ValueError("Expected a static mesh prop without armatures")
    for mesh in report["meshes"]:
        if (not mesh["uv_layers"] or mesh["invalid_uv_values"] or mesh["zero_area_triangles"]
                or mesh["invalid_material_indices"] or not all(mesh["material_slots"])):
            raise ValueError("Mesh/UV/material validation failed: " + mesh["name"])
    if any(not image["loaded"] for image in report["images"]):
        raise ValueError("Unloaded texture")


def process(meshes, report):
    validate(report["source"])
    if len(meshes) != 1 or report["source"]["triangles"] != 6387:
        raise ValueError("Source differs from the inspected one-mesh 6387-triangle asset")
    report["textures"] = bind_textures(meshes)
    report["material_cleanup"] = "Authored metallic map linked to Metallic instead of legacy Specular IOR; pixel bytes unchanged. Same PBR material in before/after renders."
    report["normalization"] = normalize(meshes)
    report["before_decimation"] = inspection(meshes)
    cameras = render_setup()
    render_views("before", cameras)
    obj = meshes[0]
    obj.name = "guild_field_gear_station"
    obj.data.name = "guild_field_gear_station_mesh"
    bpy.context.view_layer.objects.active = obj
    modifier = obj.modifiers.new("Gentle_6387_to_5990", "DECIMATE")
    modifier.decimate_type = "COLLAPSE"
    modifier.ratio = 5990 / 6387
    modifier.use_collapse_triangulate = True
    bpy.ops.object.modifier_apply(modifier=modifier.name)
    bpy.context.view_layer.update()
    report["decimation"] = {"method": "one collapse modifier", "requested_ratio": 5990 / 6387,
                             "pre_final_normalization_bounds": bounds(meshes)}
    # Remove any submillimetre extrema drift introduced by the limited collapse.
    report["final_normalization"] = normalize(meshes)
    report["after"] = inspection(meshes)
    validate(report["after"])
    if not 5900 <= report["after"]["triangles"] <= 6000:
        raise ValueError("Triangle budget not met by the single gentle pass")
    write_json("cleanup-validation.json", report)
    render_views("after", cameras)

    bpy.ops.object.select_all(action="DESELECT")
    for mesh in meshes:
        mesh.select_set(True)
    bpy.context.view_layer.objects.active = obj
    export = OUT / "guild_field_gear_station.fbx"
    bpy.ops.export_scene.fbx(filepath=str(export), use_selection=True, object_types={"MESH"},
                             global_scale=1.0, apply_unit_scale=True, apply_scale_options="FBX_SCALE_UNITS",
                             use_space_transform=True, bake_space_transform=True, axis_forward="-Z", axis_up="Y",
                             use_mesh_modifiers=True, mesh_smooth_type="OFF", use_tspace=True,
                             bake_anim=False, add_leaf_bones=False, path_mode="RELATIVE", embed_textures=False)
    for image in bpy.data.images:
        if image.source == "FILE":
            path = Path(bpy.path.abspath(image.filepath))
            if path.exists() and path.is_relative_to(OUT):
                image.filepath = "//" + path.relative_to(OUT).as_posix()
    bpy.context.scene.camera = cameras[0][1]
    bpy.ops.wm.save_as_mainfile(filepath=str(OUT / "guild_field_gear_station.blend"))
    report["export"] = {"file": export.name, "sha256": sha(export), "axes": "-Z forward / Y up",
                         "unit_scale": 1.0, "mesh_selection_only": True, "animation": False}

    # Reimport the processed export in place so its relative texture references remain valid.
    # This is inside the owned output directory even if the importer writes an FBM folder.
    bpy.ops.wm.read_factory_settings(use_empty=True)
    bpy.ops.import_scene.fbx(filepath=str(export), use_anim=False)
    loaded = [o for o in bpy.context.scene.objects if o.type == "MESH"]
    report["roundtrip"] = inspection(loaded)
    validate(report["roundtrip"])
    original, actual = report["after"], report["roundtrip"]
    if original["triangles"] != actual["triangles"]:
        raise ValueError("Export changed triangle count")
    for a, b in zip(original["bounds_blender_xyz"]["dimensions"], actual["bounds_blender_xyz"]["dimensions"]):
        if abs(a - b) > 1e-4:
            raise ValueError("FBX roundtrip changed dimensions")
    if abs(actual["bounds_blender_xyz"]["min"][2]) > 1e-4 or any(abs(c) > 1e-4 for obj in loaded for c in obj.location):
        raise ValueError("FBX grounding/origin changed")
    report["raw_after"] = raw_hashes()
    report["passed"] = True
    write_json("cleanup-validation.json", report)
    print("STATION_CLEANUP_PASS " + json.dumps({"triangles": actual["triangles"],
          "dimensions": actual["bounds_blender_xyz"]["dimensions"], "raw_unchanged": True}), flush=True)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--stage", choices=["inspect", "process", "verify-blend", "package"], default="inspect")
    args = parser.parse_args(sys.argv[sys.argv.index("--") + 1:])
    raw_before = raw_hashes()
    OUT.mkdir(parents=True, exist_ok=True)
    if args.stage == "package":
        # Packaging only: no geometry/material-parameter changes or rerendering.
        report = json.loads((OUT / "cleanup-validation.json").read_text(encoding="utf-8"))
        bpy.ops.wm.open_mainfile(filepath=str(OUT / "guild_field_gear_station.blend"))
        folder = OUT / TEXTURE_FOLDER
        folder.mkdir(exist_ok=True)
        for texture in report["textures"]:
            source = OUT / texture["file"]
            target = folder / source.name
            if source != target:
                shutil.copyfile(source, target)
            if sha(target) != texture["sha256"]:
                raise ValueError("Packaging changed texture bytes")
            texture["file"] = target.relative_to(OUT).as_posix()
        for image in bpy.data.images:
            if image.source == "FILE" and (folder / Path(image.filepath).name).is_file():
                image.filepath = str(folder / Path(image.filepath).name)
        meshes = [o for o in bpy.context.scene.objects if o.type == "MESH"]
        bpy.ops.object.select_all(action="DESELECT")
        for mesh in meshes:
            mesh.select_set(True)
        bpy.context.view_layer.objects.active = meshes[0]
        export = OUT / "guild_field_gear_station.fbx"
        bpy.ops.export_scene.fbx(filepath=str(export), use_selection=True, object_types={"MESH"},
                                 global_scale=1.0, apply_unit_scale=True, apply_scale_options="FBX_SCALE_UNITS",
                                 use_space_transform=True, bake_space_transform=True, axis_forward="-Z", axis_up="Y",
                                 use_mesh_modifiers=True, mesh_smooth_type="OFF", use_tspace=True,
                                 bake_anim=False, add_leaf_bones=False, path_mode="RELATIVE", embed_textures=False)
        for image in bpy.data.images:
            if image.source == "FILE":
                path = Path(bpy.path.abspath(image.filepath)).resolve()
                image.filepath = "//" + path.relative_to(OUT).as_posix()
        bpy.ops.wm.save_as_mainfile(filepath=str(OUT / "guild_field_gear_station.blend"), relative_remap=False)
        bpy.ops.wm.read_factory_settings(use_empty=True)
        bpy.ops.import_scene.fbx(filepath=str(export), use_anim=False)
        loaded = [o for o in bpy.context.scene.objects if o.type == "MESH"]
        report["roundtrip"] = inspection(loaded)
        validate(report["roundtrip"])
        if report["roundtrip"]["triangles"] != report["after"]["triangles"]:
            raise ValueError("Packaging changed triangle count")
        for a, b in zip(report["after"]["bounds_blender_xyz"]["dimensions"], report["roundtrip"]["bounds_blender_xyz"]["dimensions"]):
            if abs(a - b) > 1e-4:
                raise ValueError("Packaging changed dimensions")
        from bpy_extras.io_utils import axis_conversion
        forward = axis_conversion(to_forward="-Z", to_up="Y") @ Vector((0, -1, 0))
        if (forward - Vector((0, 0, 1))).length > 1e-6:
            raise ValueError("Reference-facing side does not export as +Z")
        report["export"].update({"sha256": sha(export), "texture_folder": TEXTURE_FOLDER,
                                  "source_visual_front_blender": [0, -1, 0], "visual_front_fbx": list(forward),
                                  "unity_resource_path": "Art/Props/GuildFieldStation/guild_field_gear_station"})
        report["raw_after"] = raw_hashes()
        write_json("cleanup-validation.json", report)
        print("STATION_PACKAGE_PASS " + json.dumps({"triangles": report["roundtrip"]["triangles"],
              "fbx_front": list(forward), "material": report["roundtrip"]["materials"][0]["name"],
              "fbx_local_dimensions_xyz": report["roundtrip"]["meshes"][0]["local_dimensions"]}), flush=True)
        return
    if args.stage == "verify-blend":
        bpy.ops.wm.open_mainfile(filepath=str(OUT / "guild_field_gear_station.blend"))
        meshes = [o for o in bpy.context.scene.objects if o.type == "MESH"]
        result = inspection(meshes)
        validate(result)
        paths = []
        for image in bpy.data.images:
            if image.source == "FILE":
                path = Path(bpy.path.abspath(image.filepath)).resolve()
                paths.append({"image": image.name, "saved_path": image.filepath, "resolved": str(path), "exists": path.is_file()})
                if not path.is_file() or not path.is_relative_to(OUT):
                    raise ValueError("Saved blend has a missing or external image: " + str(path))
        write_json("blend-validation.json", {"passed": True, "inspection": result, "image_paths": paths,
                                             "raw_before": raw_before, "raw_after": raw_hashes()})
        print("STATION_BLEND_PASS " + json.dumps({"triangles": result["triangles"], "all_images_local_and_loaded": True}), flush=True)
        return
    source = working_source()
    bpy.ops.wm.read_factory_settings(use_empty=True)
    bpy.ops.import_scene.fbx(filepath=str(source), use_anim=False)
    meshes = [o for o in bpy.context.scene.objects if o.type == "MESH"]
    bpy.context.view_layer.update()
    report = {"blender_version": bpy.app.version_string, "raw_before": raw_before, "source": inspection(meshes)}
    report["raw_after"] = raw_hashes()
    write_json("source-inspection.json", report)
    print("STATION_INSPECTION " + json.dumps({"triangles": report["source"]["triangles"],
          "bounds": report["source"]["bounds_blender_xyz"]}), flush=True)
    if args.stage == "process":
        process(meshes, report)


if __name__ == "__main__":
    main()
