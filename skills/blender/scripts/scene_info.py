"""
Blender Scene Info Script - Extract scene information from .blend files.

This script is executed inside Blender via:
    $BLENDER_EXE -b scene.blend --python scene_info.py -- [options]

Arguments (after --):
    --output PATH       Output JSON file (optional, prints to stdout if not set)
    --objects           List objects
    --materials         List materials
    --textures          List textures/images
    --cameras           List cameras
    --lights            List lights
    --collections       List collections
    --animation         Show animation info (frame range, fps)
    --all               Show all information (default)
"""

import argparse
import json
import sys

import bpy


def get_objects_info():
    """Get information about all objects."""
    objects = []
    for obj in bpy.data.objects:
        obj_info = {
            "name": obj.name,
            "type": obj.type,
            "location": list(obj.location),
            "rotation": list(obj.rotation_euler),
            "scale": list(obj.scale),
            "parent": obj.parent.name if obj.parent else None,
            "visible": obj.visible_get(),
        }

        if obj.type == "MESH":
            mesh = obj.data
            obj_info["vertices"] = len(mesh.vertices)
            obj_info["faces"] = len(mesh.polygons)
            obj_info["edges"] = len(mesh.edges)
            obj_info["materials"] = [m.name if m else None for m in obj.data.materials]

        objects.append(obj_info)

    return objects


def get_materials_info():
    """Get information about all materials."""
    materials = []
    for mat in bpy.data.materials:
        mat_info = {
            "name": mat.name,
            "use_nodes": mat.use_nodes,
            "users": mat.users,
        }

        if mat.use_nodes and mat.node_tree:
            mat_info["nodes"] = [node.type for node in mat.node_tree.nodes]

        materials.append(mat_info)

    return materials


def get_textures_info():
    """Get information about all images/textures."""
    images = []
    for img in bpy.data.images:
        img_info = {
            "name": img.name,
            "filepath": img.filepath,
            "size": list(img.size),
            "channels": img.channels,
            "is_packed": img.packed_file is not None,
            "users": img.users,
        }
        images.append(img_info)

    return images


def get_cameras_info():
    """Get information about all cameras."""
    cameras = []
    for cam in bpy.data.cameras:
        cam_info = {
            "name": cam.name,
            "type": cam.type,
            "lens": cam.lens,
            "sensor_width": cam.sensor_width,
            "clip_start": cam.clip_start,
            "clip_end": cam.clip_end,
        }
        cameras.append(cam_info)

    return cameras


def get_lights_info():
    """Get information about all lights."""
    lights = []
    for light in bpy.data.lights:
        light_info = {
            "name": light.name,
            "type": light.type,
            "energy": light.energy,
            "color": list(light.color),
        }
        lights.append(light_info)

    return lights


def get_collections_info():
    """Get information about all collections."""
    collections = []
    for coll in bpy.data.collections:
        coll_info = {
            "name": coll.name,
            "objects": [obj.name for obj in coll.objects],
            "children": [c.name for c in coll.children],
        }
        collections.append(coll_info)

    return collections


def get_animation_info():
    """Get animation/timeline information."""
    scene = bpy.context.scene
    return {
        "fps": scene.render.fps,
        "fps_base": scene.render.fps_base,
        "frame_start": scene.frame_start,
        "frame_end": scene.frame_end,
        "frame_current": scene.frame_current,
        "duration_frames": scene.frame_end - scene.frame_start + 1,
        "duration_seconds": (scene.frame_end - scene.frame_start + 1) / (scene.render.fps / scene.render.fps_base),
    }


def get_render_info():
    """Get render settings information."""
    scene = bpy.context.scene
    render = scene.render
    return {
        "engine": render.engine,
        "resolution_x": render.resolution_x,
        "resolution_y": render.resolution_y,
        "resolution_percentage": render.resolution_percentage,
        "file_format": render.image_settings.file_format,
        "filepath": render.filepath,
    }


def main():
    # Parse arguments after --
    argv = sys.argv
    if "--" in argv:
        argv = argv[argv.index("--") + 1:]
    else:
        argv = []

    parser = argparse.ArgumentParser(description="Extract scene information")
    parser.add_argument("--output", "-o", help="Output JSON file")
    parser.add_argument("--objects", action="store_true", help="List objects")
    parser.add_argument("--materials", action="store_true", help="List materials")
    parser.add_argument("--textures", action="store_true", help="List textures")
    parser.add_argument("--cameras", action="store_true", help="List cameras")
    parser.add_argument("--lights", action="store_true", help="List lights")
    parser.add_argument("--collections", action="store_true", help="List collections")
    parser.add_argument("--animation", action="store_true", help="Show animation info")
    parser.add_argument("--render", action="store_true", help="Show render settings")
    parser.add_argument("--all", "-a", action="store_true", help="Show all info")

    args = parser.parse_args(argv)

    # Default to all if nothing specified
    show_all = args.all or not any([
        args.objects, args.materials, args.textures,
        args.cameras, args.lights, args.collections,
        args.animation, args.render
    ])

    info = {
        "file": bpy.data.filepath,
        "blender_version": ".".join(str(v) for v in bpy.app.version),
    }

    if show_all or args.objects:
        info["objects"] = get_objects_info()
    if show_all or args.materials:
        info["materials"] = get_materials_info()
    if show_all or args.textures:
        info["textures"] = get_textures_info()
    if show_all or args.cameras:
        info["cameras"] = get_cameras_info()
    if show_all or args.lights:
        info["lights"] = get_lights_info()
    if show_all or args.collections:
        info["collections"] = get_collections_info()
    if show_all or args.animation:
        info["animation"] = get_animation_info()
    if show_all or args.render:
        info["render"] = get_render_info()

    # Output
    output = json.dumps(info, indent=2)
    if args.output:
        with open(args.output, "w") as f:
            f.write(output)
        print(f"Scene info written to {args.output}")
    else:
        print(output)


if __name__ == "__main__":
    main()
