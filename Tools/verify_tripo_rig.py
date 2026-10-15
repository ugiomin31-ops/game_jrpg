"""Read-only FBX skin check inside Blender; no packages, exports, or saved scenes.

Usage: blender --background --python Tools/verify_tripo_rig.py -- input.fbx output.json
Exit: 0 = verified, 1 = rejected/error, 2 = invalid arguments.
Each selected limb must move at least one bound mesh vertex. Unknown bone naming
falls back to all weighted deform bones. This checks skinning, not animation quality.
"""

import argparse
import json
import math
from pathlib import Path
import re
import sys

import bpy
from mathutils import Euler


LIMB = re.compile(r"upperarm|lowerarm|forearm|arm|upleg|upperleg|lowerleg|thigh|calf|shin|leg|hand|foot")
SMALL = re.compile(r"finger|thumb|index|middle|ring|pinky|toe|twist")


def snapshot(mesh):
    evaluated = mesh.evaluated_get(bpy.context.evaluated_depsgraph_get())
    data = evaluated.to_mesh()
    try:
        points = [tuple(evaluated.matrix_world @ vertex.co) for vertex in data.vertices]
        if not points or any(not math.isfinite(c) for point in points for c in point):
            raise ValueError(f"Empty or nonfinite evaluated mesh: {mesh.name}")
        return points
    finally:
        evaluated.to_mesh_clear()


def weight_report(mesh, armature):
    deform = {bone.name for bone in armature.data.bones if bone.use_deform}
    groups = {group.index: group.name for group in mesh.vertex_groups if group.name in deform}
    counts = {}
    weighted = 0
    invalid = 0
    minimum = None
    maximum = 0.0
    for vertex in mesh.data.vertices:
        total = 0.0
        for entry in vertex.groups:
            if not math.isfinite(entry.weight) or entry.weight < 0:
                invalid += 1
                continue
            name = groups.get(entry.group)
            if name is not None and entry.weight > 0:
                total += entry.weight
                counts[name] = counts.get(name, 0) + 1
        if total > 0:
            weighted += 1
            minimum = total if minimum is None else min(minimum, total)
            maximum = max(maximum, total)
    return {
        "mesh": mesh.name, "armature": armature.name,
        "vertices": len(mesh.data.vertices), "weighted_vertices": weighted,
        "unweighted_vertices": len(mesh.data.vertices) - weighted,
        "invalid_weights": invalid, "minimum_positive_weight_sum": minimum,
        "maximum_weight_sum": maximum, "bone_vertex_counts": counts,
    }


def suspend_animation(obj):
    """Detach active actions, mute NLA/drivers, preserving Blender 4.4+ slots."""
    data = obj.animation_data
    if data is None:
        return lambda: None
    action = data.action
    slot = getattr(data, "action_slot", None)
    muted = [(item, item.mute) for item in list(data.nla_tracks) + list(data.drivers)]
    data.action = None
    for item, _ in muted:
        item.mute = True

    def restore():
        data.action = action
        if action is not None and slot is not None:
            data.action_slot = slot
        for item, mute in muted:
            item.mute = mute

    return restore


def verify(report):
    bpy.ops.wm.read_factory_settings(use_empty=True)
    result = bpy.ops.import_scene.fbx(filepath=report["input"], use_anim=False)
    if "FINISHED" not in result:
        raise ValueError("FBX importer did not finish")
    meshes = [obj for obj in bpy.context.scene.objects if obj.type == "MESH"]
    armatures = [obj for obj in bpy.context.scene.objects if obj.type == "ARMATURE"]
    failures = report["failures"]
    if not meshes or not armatures:
        failures.append("Imported source requires both meshes and an armature")
        return
    bindings = {}
    for mesh in meshes:
        # Check source coordinates as well as evaluated coordinates.
        if any(not math.isfinite(c) for v in mesh.data.vertices for c in v.co):
            failures.append(f"Nonfinite source coordinates: {mesh.name}")
        modifiers = [m for m in mesh.modifiers if m.type == "ARMATURE" and
                     m.show_viewport and m.object in armatures and m.use_vertex_groups]
        if not modifiers:
            failures.append(f"No enabled vertex-group armature binding: {mesh.name}")
        for modifier in modifiers:
            armature = modifier.object
            bound = bindings.setdefault(armature, [])
            if mesh in bound:
                continue
            bound.append(mesh)
            weights = weight_report(mesh, armature)
            report["weights"].append(weights)
            if not weights["weighted_vertices"] or weights["invalid_weights"]:
                failures.append(f"Missing or invalid deform weights: {mesh.name}/{armature.name}")

    for armature in armatures:
        bound = bindings.get(armature, [])
        if not bound:
            failures.append(f"Armature has no bound mesh: {armature.name}")
            continue
        weighted = set()
        for weights in report["weights"]:
            if weights["armature"] == armature.name:
                weighted.update(weights["bone_vertex_counts"])
        # Include unweighted limb parents if their descendants carry skin weights.
        eligible = [bone for bone in armature.pose.bones if bone.name in weighted or
                    any(child.name in weighted for child in bone.children_recursive)]
        major = [bone for bone in eligible if LIMB.search(bone.name.lower()) and
                 not SMALL.search(bone.name.lower())]
        candidates = major or [bone for bone in eligible if bone.name in weighted]
        report["selection"].append({
            "armature": armature.name,
            "method": "major_limb_names" if major else "all_weighted_deform_bones_fallback",
            "bones": [bone.name for bone in candidates],
        })
        if not candidates:
            failures.append(f"No probeable deform bones: {armature.name}")
            continue
        saved = [(bone, bone.matrix_basis.copy()) for bone in armature.pose.bones]
        restore_animation = suspend_animation(armature)
        pose_position = armature.data.pose_position
        try:
            armature.data.pose_position = "POSE"
            bpy.context.view_layer.update()
            baseline = {mesh: snapshot(mesh) for mesh in bound}
            deformed_meshes = set()
            for bone in candidates:
                original = bone.matrix_basis.copy()
                try:
                    rotation = Euler(tuple(math.radians(a) for a in (23, 17, 11)), "XYZ")
                    bone.matrix_basis = original @ rotation.to_matrix().to_4x4()
                    bpy.context.view_layer.update()
                    probe = {"armature": armature.name, "bone": bone.name, "meshes": []}
                    for mesh, before in baseline.items():
                        after = snapshot(mesh)
                        if len(before) != len(after):
                            raise ValueError(f"Evaluated topology changed: {mesh.name}/{bone.name}")
                        diagonal = math.sqrt(sum((max(p[i] for p in before) -
                                                  min(p[i] for p in before)) ** 2 for i in range(3)))
                        tolerance = max(1e-8, diagonal * 1e-6)
                        distances = [math.dist(a, b) for a, b in zip(before, after)]
                        if not all(math.isfinite(d) for d in distances) or not math.isfinite(tolerance):
                            raise ValueError(f"Nonfinite deformation: {mesh.name}/{bone.name}")
                        probe["meshes"].append({
                            "mesh": mesh.name, "evaluated_vertices": len(before),
                            "tolerance_world_units": tolerance,
                            "moved_vertices": sum(d > tolerance for d in distances),
                            "maximum_delta": max(distances),
                            "mean_delta": sum(d / len(distances) for d in distances),
                        })
                        if probe["meshes"][-1]["moved_vertices"]:
                            deformed_meshes.add(mesh)
                    probe["passed"] = any(item["moved_vertices"] for item in probe["meshes"])
                    report["probes"].append(probe)
                    if not probe["passed"]:
                        failures.append(f"Zero deformation: {armature.name}/{bone.name}")
                finally:
                    bone.matrix_basis = original
                    bpy.context.view_layer.update()
            for mesh in bound:
                if mesh not in deformed_meshes:
                    failures.append(f"Mesh never deformed: {mesh.name}/{armature.name}")
        finally:
            for bone, matrix in saved:
                bone.matrix_basis = matrix
            armature.data.pose_position = pose_position
            restore_animation()
            bpy.context.view_layer.update()
    if not report["probes"]:
        failures.append("No deformation probes completed")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("input", type=Path)
    parser.add_argument("output", type=Path)
    args = parser.parse_args(sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else [])
    source, destination = args.input.resolve(), args.output.resolve()
    if (source == destination or destination.suffix.lower() != ".json" or
            (destination.exists() and source.exists() and source.samefile(destination))):
        parser.error("Output must be a separate .json file")
    report = {
        "schema_version": 1, "input": str(source), "blender_version": bpy.app.version_string,
        "passed": False, "weights": [], "selection": [], "probes": [], "failures": [],
        "probe_rotation_degrees_xyz": [23, 17, 11],
        "limits": "Static skin deformation only; partial unweighted vertices are reported, not rejected.",
    }
    try:
        if not source.is_file() or source.suffix.lower() != ".fbx":
            raise ValueError("Input must be an existing .fbx file")
        verify(report)
        report["passed"] = bool(report["probes"]) and not report["failures"]
    except Exception as error:
        report["failures"].append(f"{type(error).__name__}: {error}")
    try:
        destination.write_text(json.dumps(report, ensure_ascii=False, indent=2, allow_nan=False) + "\n",
                               encoding="utf-8")
    except (OSError, ValueError) as error:
        print(f"Unable to write rig report: {error}", file=sys.stderr)
        return 1
    print(f"Rig verification {'PASS' if report['passed'] else 'FAIL'}: {destination}")
    return 0 if report["passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
