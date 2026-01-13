"""
Blender Modify Scene Script - Common scene modifications.

This script is executed inside Blender via:
    $BLENDER_EXE -b scene.blend --python modify_scene.py -- [options]

Arguments (after --):
    --output PATH           Save modified .blend file to path
    --scale FACTOR          Scale all objects by factor
    --apply-transforms      Apply all object transforms
    --apply-modifiers       Apply all modifiers
    --remove-unused         Remove unused data blocks
    --center-origin         Center origins to geometry
    --set-origin MODE       Set origin: CENTER, BOTTOM, CURSOR
    --triangulate           Triangulate all meshes
    --decimate RATIO        Decimate meshes (0.0-1.0)
    --smooth-shading        Set smooth shading on all meshes
    --flat-shading          Set flat shading on all meshes
"""

import argparse
import sys
from pathlib import Path

import bpy


def scale_scene(factor: float):
    """Scale all objects by a factor."""
    for obj in bpy.data.objects:
        obj.scale *= factor
    print(f"Scaled all objects by {factor}")


def apply_transforms():
    """Apply transforms to all objects."""
    bpy.ops.object.select_all(action="SELECT")
    bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)
    bpy.ops.object.select_all(action="DESELECT")
    print("Applied transforms to all objects")


def apply_modifiers():
    """Apply all modifiers on mesh objects."""
    for obj in bpy.data.objects:
        if obj.type == "MESH":
            bpy.context.view_layer.objects.active = obj
            for modifier in obj.modifiers[:]:
                try:
                    bpy.ops.object.modifier_apply(modifier=modifier.name)
                except RuntimeError as e:
                    print(f"Warning: Could not apply {modifier.name} on {obj.name}: {e}")
    print("Applied modifiers")


def remove_unused():
    """Remove unused data blocks."""
    # Remove orphan data
    bpy.ops.outliner.orphans_purge(do_local_ids=True, do_linked_ids=True, do_recursive=True)
    print("Removed unused data blocks")


def center_origins():
    """Center origin to geometry for all objects."""
    bpy.ops.object.select_all(action="SELECT")
    bpy.ops.object.origin_set(type="ORIGIN_GEOMETRY", center="BOUNDS")
    bpy.ops.object.select_all(action="DESELECT")
    print("Centered origins to geometry")


def set_origin(mode: str):
    """Set origin for all objects."""
    origin_types = {
        "CENTER": "ORIGIN_GEOMETRY",
        "BOTTOM": "ORIGIN_CENTER_OF_VOLUME",
        "CURSOR": "ORIGIN_CURSOR",
    }

    if mode not in origin_types:
        print(f"Unknown origin mode: {mode}")
        return

    bpy.ops.object.select_all(action="SELECT")
    bpy.ops.object.origin_set(type=origin_types[mode])
    bpy.ops.object.select_all(action="DESELECT")
    print(f"Set origin to {mode}")


def triangulate_meshes():
    """Triangulate all meshes."""
    for obj in bpy.data.objects:
        if obj.type == "MESH":
            bpy.context.view_layer.objects.active = obj
            bpy.ops.object.mode_set(mode="EDIT")
            bpy.ops.mesh.select_all(action="SELECT")
            bpy.ops.mesh.quads_convert_to_tris()
            bpy.ops.object.mode_set(mode="OBJECT")
    print("Triangulated all meshes")


def decimate_meshes(ratio: float):
    """Decimate all meshes."""
    for obj in bpy.data.objects:
        if obj.type == "MESH":
            modifier = obj.modifiers.new(name="Decimate", type="DECIMATE")
            modifier.ratio = ratio
            bpy.context.view_layer.objects.active = obj
            bpy.ops.object.modifier_apply(modifier=modifier.name)
    print(f"Decimated meshes to {ratio * 100}%")


def set_shading(smooth: bool):
    """Set shading mode for all meshes."""
    for obj in bpy.data.objects:
        if obj.type == "MESH":
            bpy.context.view_layer.objects.active = obj
            bpy.ops.object.select_all(action="DESELECT")
            obj.select_set(True)
            if smooth:
                bpy.ops.object.shade_smooth()
            else:
                bpy.ops.object.shade_flat()
    print(f"Set {'smooth' if smooth else 'flat'} shading")


def main():
    # Parse arguments after --
    argv = sys.argv
    if "--" in argv:
        argv = argv[argv.index("--") + 1:]
    else:
        argv = []

    parser = argparse.ArgumentParser(description="Modify scene")
    parser.add_argument("--output", "-o", help="Save to file")
    parser.add_argument("--scale", type=float, help="Scale factor")
    parser.add_argument("--apply-transforms", action="store_true")
    parser.add_argument("--apply-modifiers", action="store_true")
    parser.add_argument("--remove-unused", action="store_true")
    parser.add_argument("--center-origin", action="store_true")
    parser.add_argument("--set-origin", choices=["CENTER", "BOTTOM", "CURSOR"])
    parser.add_argument("--triangulate", action="store_true")
    parser.add_argument("--decimate", type=float, help="Decimate ratio 0.0-1.0")
    parser.add_argument("--smooth-shading", action="store_true")
    parser.add_argument("--flat-shading", action="store_true")

    args = parser.parse_args(argv)

    # Apply modifications in order
    if args.scale:
        scale_scene(args.scale)

    if args.apply_transforms:
        apply_transforms()

    if args.center_origin:
        center_origins()

    if args.set_origin:
        set_origin(args.set_origin)

    if args.triangulate:
        triangulate_meshes()

    if args.decimate:
        decimate_meshes(args.decimate)

    if args.apply_modifiers:
        apply_modifiers()

    if args.smooth_shading:
        set_shading(smooth=True)
    elif args.flat_shading:
        set_shading(smooth=False)

    if args.remove_unused:
        remove_unused()

    # Save output
    if args.output:
        output_path = Path(args.output)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        bpy.ops.wm.save_as_mainfile(filepath=str(output_path))
        print(f"Saved to {args.output}")


if __name__ == "__main__":
    main()
