"""
Blender Render Script - Render frames or animations from .blend files.

This script is executed inside Blender via:
    $BLENDER_EXE -b scene.blend --python render.py -- [options]

Arguments (after --):
    --output PATH       Output path (file or directory)
    --frame N           Render single frame N
    --start N           Start frame for animation
    --end N             End frame for animation
    --engine ENGINE     Render engine: CYCLES, BLENDER_EEVEE, BLENDER_EEVEE_NEXT, BLENDER_WORKBENCH
    --samples N         Number of render samples (Cycles/Eevee)
    --format FORMAT     Output format: PNG, JPEG, OPEN_EXR, TIFF, BMP, etc.
    --resolution X Y    Output resolution (width height)
    --percent N         Resolution percentage (1-100)
"""

import argparse
import sys

import bpy


def configure_render(
    engine: str = None,
    samples: int = None,
    output_format: str = None,
    resolution: tuple = None,
    percent: int = None,
):
    """Configure render settings."""
    scene = bpy.context.scene
    render = scene.render

    if engine:
        scene.render.engine = engine

    if samples:
        if scene.render.engine == "CYCLES":
            scene.cycles.samples = samples
        elif scene.render.engine in ("BLENDER_EEVEE", "BLENDER_EEVEE_NEXT"):
            scene.eevee.taa_render_samples = samples

    if output_format:
        render.image_settings.file_format = output_format

    if resolution:
        render.resolution_x, render.resolution_y = resolution

    if percent:
        render.resolution_percentage = percent


def render_frame(output_path: str, frame: int = None):
    """Render a single frame."""
    scene = bpy.context.scene

    if frame is not None:
        scene.frame_set(frame)

    scene.render.filepath = output_path
    bpy.ops.render.render(write_still=True)
    print(f"Rendered frame {scene.frame_current} to {output_path}")


def render_animation(output_path: str, start: int = None, end: int = None):
    """Render an animation sequence."""
    scene = bpy.context.scene

    if start is not None:
        scene.frame_start = start
    if end is not None:
        scene.frame_end = end

    scene.render.filepath = output_path
    bpy.ops.render.render(animation=True)
    print(f"Rendered animation frames {scene.frame_start}-{scene.frame_end} to {output_path}")


def main():
    # Parse arguments after --
    argv = sys.argv
    if "--" in argv:
        argv = argv[argv.index("--") + 1:]
    else:
        argv = []

    parser = argparse.ArgumentParser(description="Render frames or animations")
    parser.add_argument("--output", "-o", required=True, help="Output path")
    parser.add_argument("--frame", "-f", type=int, help="Single frame to render")
    parser.add_argument("--start", "-s", type=int, help="Animation start frame")
    parser.add_argument("--end", "-e", type=int, help="Animation end frame")
    parser.add_argument(
        "--engine",
        choices=["CYCLES", "BLENDER_EEVEE", "BLENDER_EEVEE_NEXT", "BLENDER_WORKBENCH"],
        help="Render engine",
    )
    parser.add_argument("--samples", type=int, help="Number of samples")
    parser.add_argument(
        "--format",
        dest="output_format",
        choices=["PNG", "JPEG", "OPEN_EXR", "OPEN_EXR_MULTILAYER", "TIFF", "BMP", "FFMPEG"],
        help="Output format",
    )
    parser.add_argument("--resolution", type=int, nargs=2, metavar=("X", "Y"), help="Resolution")
    parser.add_argument("--percent", type=int, help="Resolution percentage (1-100)")

    args = parser.parse_args(argv)

    # Configure render settings
    configure_render(
        engine=args.engine,
        samples=args.samples,
        output_format=args.output_format,
        resolution=tuple(args.resolution) if args.resolution else None,
        percent=args.percent,
    )

    # Render
    if args.frame is not None:
        render_frame(args.output, args.frame)
    elif args.start is not None or args.end is not None:
        render_animation(args.output, args.start, args.end)
    else:
        # Default: render current frame
        render_frame(args.output)


if __name__ == "__main__":
    main()
