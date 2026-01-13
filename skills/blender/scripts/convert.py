"""
Blender Convert Script - Convert between 3D file formats.

This script is executed inside Blender via:
    $BLENDER_EXE -b --python convert.py -- [options]
    $BLENDER_EXE -b input.blend --python convert.py -- --output out.glb

Arguments (after --):
    --input PATH        Input file (if not opened with -b)
    --output PATH       Output file path (format determined by extension)
    --selection-only    Export only selected objects
    --apply-modifiers   Apply modifiers before export

Supported formats (by extension):
    Import: .blend, .fbx, .obj, .gltf, .glb, .usd, .usda, .usdc, .abc, .stl, .ply, .dae
    Export: .fbx, .obj, .gltf, .glb, .usd, .usda, .usdc, .abc, .stl, .ply, .dae
"""

import argparse
import sys
from pathlib import Path

import bpy


def clear_scene():
    """Clear all objects from the scene."""
    bpy.ops.object.select_all(action="SELECT")
    bpy.ops.object.delete()


def import_file(filepath: str):
    """Import a file based on its extension."""
    path = Path(filepath)
    ext = path.suffix.lower()

    if ext == ".blend":
        bpy.ops.wm.open_mainfile(filepath=filepath)
    elif ext == ".fbx":
        bpy.ops.import_scene.fbx(filepath=filepath)
    elif ext == ".obj":
        bpy.ops.wm.obj_import(filepath=filepath)
    elif ext in (".gltf", ".glb"):
        bpy.ops.import_scene.gltf(filepath=filepath)
    elif ext in (".usd", ".usda", ".usdc", ".usdz"):
        bpy.ops.wm.usd_import(filepath=filepath)
    elif ext == ".abc":
        bpy.ops.wm.alembic_import(filepath=filepath)
    elif ext == ".stl":
        bpy.ops.wm.stl_import(filepath=filepath)
    elif ext == ".ply":
        bpy.ops.wm.ply_import(filepath=filepath)
    elif ext == ".dae":
        bpy.ops.wm.collada_import(filepath=filepath)
    else:
        raise ValueError(f"Unsupported import format: {ext}")

    print(f"Imported: {filepath}")


def export_file(filepath: str, selection_only: bool = False, apply_modifiers: bool = True):
    """Export to a file based on its extension."""
    path = Path(filepath)
    ext = path.suffix.lower()

    # Ensure output directory exists
    path.parent.mkdir(parents=True, exist_ok=True)

    # Common export kwargs
    use_selection = selection_only

    if ext == ".fbx":
        bpy.ops.export_scene.fbx(
            filepath=filepath,
            use_selection=use_selection,
            apply_scale_options="FBX_SCALE_ALL",
            use_mesh_modifiers=apply_modifiers,
        )
    elif ext == ".obj":
        bpy.ops.wm.obj_export(
            filepath=filepath,
            export_selected_objects=use_selection,
            apply_modifiers=apply_modifiers,
        )
    elif ext in (".gltf", ".glb"):
        export_format = "GLB" if ext == ".glb" else "GLTF_SEPARATE"
        bpy.ops.export_scene.gltf(
            filepath=filepath,
            export_format=export_format,
            use_selection=use_selection,
            export_apply=apply_modifiers,
        )
    elif ext in (".usd", ".usda", ".usdc", ".usdz"):
        bpy.ops.wm.usd_export(
            filepath=filepath,
            selected_objects_only=use_selection,
        )
    elif ext == ".abc":
        bpy.ops.wm.alembic_export(
            filepath=filepath,
            selected=use_selection,
        )
    elif ext == ".stl":
        bpy.ops.wm.stl_export(
            filepath=filepath,
            export_selected_objects=use_selection,
            apply_modifiers=apply_modifiers,
        )
    elif ext == ".ply":
        bpy.ops.wm.ply_export(
            filepath=filepath,
            export_selected_objects=use_selection,
            apply_modifiers=apply_modifiers,
        )
    elif ext == ".dae":
        bpy.ops.wm.collada_export(
            filepath=filepath,
            selected=use_selection,
        )
    else:
        raise ValueError(f"Unsupported export format: {ext}")

    print(f"Exported: {filepath}")


def main():
    # Parse arguments after --
    argv = sys.argv
    if "--" in argv:
        argv = argv[argv.index("--") + 1:]
    else:
        argv = []

    parser = argparse.ArgumentParser(description="Convert between 3D formats")
    parser.add_argument("--input", "-i", help="Input file to import")
    parser.add_argument("--output", "-o", required=True, help="Output file path")
    parser.add_argument("--selection-only", action="store_true", help="Export selection only")
    parser.add_argument("--apply-modifiers", action="store_true", default=True, help="Apply modifiers")
    parser.add_argument("--no-apply-modifiers", action="store_false", dest="apply_modifiers")
    parser.add_argument("--clear", action="store_true", help="Clear scene before import")

    args = parser.parse_args(argv)

    # Clear scene if requested
    if args.clear:
        clear_scene()

    # Import if input file specified
    if args.input:
        import_file(args.input)

    # Export
    export_file(
        args.output,
        selection_only=args.selection_only,
        apply_modifiers=args.apply_modifiers,
    )


if __name__ == "__main__":
    main()
