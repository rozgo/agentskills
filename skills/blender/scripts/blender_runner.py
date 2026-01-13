"""
Blender Runner - Execute Blender headless with Python scripts.

Loads BLENDER_EXE from .env file or falls back to common installation paths.

Usage:
    uv run blender_runner.py script.py [--blend file.blend] [--args ...]
    uv run blender_runner.py --expr "import bpy; print(bpy.data.objects[:])"
    uv run blender_runner.py --version
"""

import argparse
import os
import subprocess
import sys
from pathlib import Path


def load_env():
    """Load environment variables from .env file."""
    env_paths = [
        Path.cwd() / ".env",
        Path.home() / ".env",
    ]

    for env_path in env_paths:
        if env_path.exists():
            with open(env_path) as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith("#") and "=" in line:
                        key, _, value = line.partition("=")
                        key = key.strip()
                        value = value.strip().strip('"').strip("'")
                        if key and value:
                            os.environ.setdefault(key, value)


def find_blender():
    """Find Blender executable from BLENDER_EXE env var or common paths."""
    # Check environment variable first
    blender_exe = os.environ.get("BLENDER_EXE")
    if blender_exe and Path(blender_exe).exists():
        return blender_exe

    # Common installation paths
    common_paths = [
        # macOS
        "/Applications/Blender.app/Contents/MacOS/Blender",
        Path.home() / "Applications/Blender.app/Contents/MacOS/Blender",
        # Linux
        "/usr/bin/blender",
        "/usr/local/bin/blender",
        "/snap/bin/blender",
        Path.home() / ".local/bin/blender",
        # Windows
        Path(os.environ.get("PROGRAMFILES", "")) / "Blender Foundation/Blender/blender.exe",
        Path(os.environ.get("PROGRAMFILES", "")) / "Blender Foundation/Blender 4.0/blender.exe",
        Path(os.environ.get("PROGRAMFILES", "")) / "Blender Foundation/Blender 5.0/blender.exe",
    ]

    for path in common_paths:
        path = Path(path)
        if path.exists():
            return str(path)

    # Try PATH
    import shutil
    blender_in_path = shutil.which("blender")
    if blender_in_path:
        return blender_in_path

    return None


def run_blender(
    blender_exe: str,
    script: str = None,
    blend_file: str = None,
    python_expr: str = None,
    script_args: list = None,
    extra_args: list = None,
) -> subprocess.CompletedProcess:
    """
    Run Blender headless with a Python script or expression.

    Args:
        blender_exe: Path to Blender executable
        script: Path to Python script to run
        blend_file: Path to .blend file to open
        python_expr: Python expression to execute
        script_args: Arguments to pass to the Python script (after --)
        extra_args: Additional Blender command line arguments

    Returns:
        CompletedProcess with stdout, stderr, and returncode
    """
    cmd = [blender_exe, "-b"]  # -b for background/headless

    if blend_file:
        cmd.append(blend_file)

    if extra_args:
        cmd.extend(extra_args)

    if python_expr:
        cmd.extend(["--python-expr", python_expr])
    elif script:
        cmd.extend(["--python", script])

    if script_args:
        cmd.append("--")
        cmd.extend(script_args)

    return subprocess.run(
        cmd,
        capture_output=True,
        text=True,
    )


def main():
    parser = argparse.ArgumentParser(
        description="Run Blender headless with Python scripts",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
    uv run %(prog)s script.py
    uv run %(prog)s script.py --blend scene.blend
    uv run %(prog)s --expr "import bpy; print(bpy.data.objects[:])"
    uv run %(prog)s script.py --blend scene.blend -- --my-arg value
    uv run %(prog)s --version
        """,
    )

    parser.add_argument("script", nargs="?", help="Python script to execute")
    parser.add_argument("--blend", "-b", help="Blend file to open")
    parser.add_argument("--expr", "-e", help="Python expression to execute")
    parser.add_argument("--version", "-v", action="store_true", help="Show Blender version")
    parser.add_argument("--blender", help="Path to Blender executable (overrides BLENDER_EXE)")
    parser.add_argument("args", nargs="*", help="Arguments to pass to the script (after --)")

    args, unknown = parser.parse_known_args()

    # Load .env file
    load_env()

    # Find Blender
    blender_exe = args.blender or find_blender()
    if not blender_exe:
        print("Error: Could not find Blender executable.", file=sys.stderr)
        print("Set BLENDER_EXE in your .env file:", file=sys.stderr)
        print("  BLENDER_EXE=/Applications/Blender.app/Contents/MacOS/Blender", file=sys.stderr)
        sys.exit(1)

    # Show version
    if args.version:
        result = run_blender(blender_exe, python_expr="import bpy; print(bpy.app.version_string)")
        print(f"Blender: {blender_exe}")
        if result.returncode == 0:
            # Extract version from output
            for line in result.stdout.strip().split("\n"):
                if line and not line.startswith("Blender"):
                    print(f"Version: {line}")
                    break
        sys.exit(result.returncode)

    # Validate arguments
    if not args.script and not args.expr:
        parser.error("Either a script or --expr is required")

    if args.script and args.expr:
        parser.error("Cannot specify both script and --expr")

    # Run Blender
    result = run_blender(
        blender_exe=blender_exe,
        script=args.script,
        blend_file=args.blend,
        python_expr=args.expr,
        script_args=args.args if args.args else None,
        extra_args=unknown if unknown else None,
    )

    # Output results
    if result.stdout:
        print(result.stdout)
    if result.stderr:
        print(result.stderr, file=sys.stderr)

    sys.exit(result.returncode)


if __name__ == "__main__":
    main()
