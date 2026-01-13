---
name: blender
description: Automate Blender 3D tasks via headless Python scripting. Use when users want to process .blend files, render images/animations, convert between 3D formats (glTF, FBX, OBJ, USD, etc.), extract scene information, batch process files, or automate 3D workflows without a GUI.
---

# Blender Headless Scripting

## Overview

This skill enables automation of Blender 3D tasks via headless (background) Python scripting. It provides utility scripts for common operations and a live API search tool for discovering Blender's Python API.

## Configuration

Set `BLENDER_EXE` in your `.env` file to point to the Blender executable:

```bash
# macOS
BLENDER_EXE=/Applications/Blender.app/Contents/MacOS/Blender

# Linux
BLENDER_EXE=/usr/bin/blender

# Windows
BLENDER_EXE=C:\Program Files\Blender Foundation\Blender\blender.exe
```

If not set, scripts will attempt to find Blender in common installation paths.

## Quick Start

### Run Blender Headless

```bash
# Using the runner script
uv run .claude/skills/blender/scripts/blender_runner.py --version

# Run a Python expression
uv run .claude/skills/blender/scripts/blender_runner.py --expr "import bpy; print(bpy.data.objects[:])"

# Run a script on a .blend file
uv run .claude/skills/blender/scripts/blender_runner.py script.py --blend scene.blend
```

### Direct Blender Commands

```bash
# Basic headless execution
$BLENDER_EXE -b file.blend --python script.py

# Render frame 1
$BLENDER_EXE -b file.blend -f 1

# Render animation
$BLENDER_EXE -b file.blend -a

# Run Python expression
$BLENDER_EXE -b --python-expr "import bpy; print(bpy.app.version_string)"
```

## Rendering

Use `scripts/render.py` to render frames or animations:

```bash
# Render single frame
$BLENDER_EXE -b scene.blend --python .claude/skills/blender/scripts/render.py -- \
    --output /path/to/output.png --frame 1

# Render animation
$BLENDER_EXE -b scene.blend --python .claude/skills/blender/scripts/render.py -- \
    --output /path/to/frames/ --start 1 --end 250

# Render with specific engine and samples
$BLENDER_EXE -b scene.blend --python .claude/skills/blender/scripts/render.py -- \
    --output /path/to/output.png --engine CYCLES --samples 128
```

**Options:**
- `--output PATH` - Output path (required)
- `--frame N` - Render single frame
- `--start N` / `--end N` - Animation range
- `--engine` - CYCLES, BLENDER_EEVEE, BLENDER_EEVEE_NEXT, BLENDER_WORKBENCH
- `--samples N` - Render samples
- `--format` - PNG, JPEG, OPEN_EXR, TIFF, BMP, FFMPEG
- `--resolution X Y` - Output resolution
- `--percent N` - Resolution percentage (1-100)

## Format Conversion

Use `scripts/convert.py` to convert between 3D formats:

```bash
# Convert .blend to glTF
$BLENDER_EXE -b model.blend --python .claude/skills/blender/scripts/convert.py -- \
    --output model.glb

# Convert FBX to glTF
$BLENDER_EXE -b --python .claude/skills/blender/scripts/convert.py -- \
    --input model.fbx --output model.glb

# Convert with modifiers applied
$BLENDER_EXE -b model.blend --python .claude/skills/blender/scripts/convert.py -- \
    --output model.fbx --apply-modifiers
```

**Supported Formats:**
- Import: .blend, .fbx, .obj, .gltf, .glb, .usd, .usda, .usdc, .abc, .stl, .ply, .dae
- Export: .fbx, .obj, .gltf, .glb, .usd, .usda, .usdc, .abc, .stl, .ply, .dae

**Options:**
- `--input PATH` - Input file (if not opened with -b)
- `--output PATH` - Output file (format from extension)
- `--selection-only` - Export selected objects only
- `--apply-modifiers` / `--no-apply-modifiers` - Apply modifiers before export
- `--clear` - Clear scene before import

## Scene Inspection

Use `scripts/scene_info.py` to extract scene information as JSON:

```bash
# Get all scene information
$BLENDER_EXE -b scene.blend --python .claude/skills/blender/scripts/scene_info.py

# Get specific information
$BLENDER_EXE -b scene.blend --python .claude/skills/blender/scripts/scene_info.py -- \
    --objects --materials

# Save to file
$BLENDER_EXE -b scene.blend --python .claude/skills/blender/scripts/scene_info.py -- \
    --output scene_info.json --all
```

**Options:**
- `--output PATH` - Save JSON to file
- `--objects` - List objects with transforms, vertex counts
- `--materials` - List materials and nodes
- `--textures` - List images/textures
- `--cameras` - List cameras with settings
- `--lights` - List lights with settings
- `--collections` - List collections hierarchy
- `--animation` - Frame range, FPS, duration
- `--render` - Render settings
- `--all` - All information (default)

## Scene Modification

Use `scripts/modify_scene.py` for common scene modifications:

```bash
# Scale scene by 0.01 (cm to m)
$BLENDER_EXE -b scene.blend --python .claude/skills/blender/scripts/modify_scene.py -- \
    --scale 0.01 --output scaled.blend

# Apply all transforms and clean up
$BLENDER_EXE -b scene.blend --python .claude/skills/blender/scripts/modify_scene.py -- \
    --apply-transforms --remove-unused --output clean.blend

# Triangulate and decimate for game export
$BLENDER_EXE -b scene.blend --python .claude/skills/blender/scripts/modify_scene.py -- \
    --triangulate --decimate 0.5 --output optimized.blend
```

**Options:**
- `--output PATH` - Save modified file
- `--scale FACTOR` - Scale all objects
- `--apply-transforms` - Apply location/rotation/scale
- `--apply-modifiers` - Apply all modifiers
- `--remove-unused` - Remove orphan data blocks
- `--center-origin` - Center origins to geometry
- `--set-origin MODE` - CENTER, BOTTOM, CURSOR
- `--triangulate` - Convert to triangles
- `--decimate RATIO` - Reduce polygon count (0.0-1.0)
- `--smooth-shading` / `--flat-shading` - Set shading mode

## Batch Processing

Use `scripts/batch_process.py` to process multiple files:

```bash
# Process all .blend files with a custom script
uv run .claude/skills/blender/scripts/batch_process.py \
    --pattern "*.blend" --input ./models --script process.py

# Parallel processing
uv run .claude/skills/blender/scripts/batch_process.py \
    --pattern "**/*.blend" --script convert_to_glb.py --parallel 4 \
    --output ./exported
```

**Options:**
- `--pattern GLOB` - File pattern (default: *.blend)
- `--input DIR` - Input directory
- `--script PATH` - Script to run on each file
- `--output DIR` - Output directory
- `--parallel N` - Number of parallel processes
- `--blender PATH` - Override Blender path

## Custom Scripts

Write custom Blender Python scripts for specialized tasks:

```python
"""Custom Blender script example."""
import bpy
import sys

# Parse arguments after --
argv = sys.argv
if "--" in argv:
    argv = argv[argv.index("--") + 1:]

# Access scene data
scene = bpy.context.scene
objects = bpy.data.objects

# Example: Print all mesh objects
for obj in objects:
    if obj.type == "MESH":
        print(f"{obj.name}: {len(obj.data.vertices)} verts")

# Example: Select all meshes
bpy.ops.object.select_all(action="DESELECT")
for obj in objects:
    if obj.type == "MESH":
        obj.select_set(True)

# Example: Export selected
bpy.ops.export_scene.gltf(filepath="output.glb", use_selection=True)
```

Run with:
```bash
$BLENDER_EXE -b scene.blend --python custom_script.py -- --arg1 value1
```

## API Discovery

Use the live API search tool to query Blender's Python API at runtime. This is always accurate for your installed Blender version.

```bash
# Show API summary
$BLENDER_EXE -b --python .claude/skills/blender/scripts/api_search.py

# Search operators by name
$BLENDER_EXE -b --python .claude/skills/blender/scripts/api_search.py -- \
    --search "export gltf"

# Search operators by description
$BLENDER_EXE -b --python .claude/skills/blender/scripts/api_search.py -- \
    --search "animation" --in-description

# Get full details for an operator (all parameters, defaults, enum options)
$BLENDER_EXE -b --python .claude/skills/blender/scripts/api_search.py -- \
    --operator bpy.ops.export_scene.gltf

# List all operators in a module
$BLENDER_EXE -b --python .claude/skills/blender/scripts/api_search.py -- \
    --module export_scene

# List all operator modules
$BLENDER_EXE -b --python .claude/skills/blender/scripts/api_search.py -- \
    --modules

# Get type details (e.g., Mesh, Camera, Material)
$BLENDER_EXE -b --python .claude/skills/blender/scripts/api_search.py -- \
    --type bpy.types.Camera

# Search types
$BLENDER_EXE -b --python .claude/skills/blender/scripts/api_search.py -- \
    --search "Mesh" --types

# List bpy.data collections
$BLENDER_EXE -b --python .claude/skills/blender/scripts/api_search.py -- \
    --data

# List bpy.context attributes
$BLENDER_EXE -b --python .claude/skills/blender/scripts/api_search.py -- \
    --context

# Output as JSON (for programmatic use)
$BLENDER_EXE -b --python .claude/skills/blender/scripts/api_search.py -- \
    --search "export" --json
```

## Common Patterns

### Load .env in Custom Scripts

```python
import os
from pathlib import Path

def load_env():
    env_path = Path.cwd() / ".env"
    if env_path.exists():
        with open(env_path) as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith("#") and "=" in line:
                    key, _, value = line.partition("=")
                    os.environ.setdefault(key.strip(), value.strip().strip('"'))
```

### Error Handling

```python
import sys

try:
    # Blender operations
    bpy.ops.export_scene.gltf(filepath="output.glb")
except Exception as e:
    print(f"Error: {e}", file=sys.stderr)
    sys.exit(1)
```

### Progress Reporting

```python
import bpy

def progress_callback(progress, text):
    print(f"[{progress:.0%}] {text}")

# Some operations support progress callbacks
bpy.ops.wm.usd_export(filepath="out.usd", progress_callback=progress_callback)
```
