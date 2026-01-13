"""
Blender Batch Process Script - Process multiple .blend files with a custom script.

This script is a wrapper that runs Blender on multiple files.
Run with uv, not inside Blender:
    uv run batch_process.py --pattern "*.blend" --script process.py

Arguments:
    --pattern GLOB      Glob pattern for input files
    --input DIR         Input directory (default: current)
    --script PATH       Python script to run on each file
    --output DIR        Output directory for results
    --parallel N        Number of parallel processes (default: 1)
"""

import argparse
import os
import subprocess
import sys
from concurrent.futures import ProcessPoolExecutor, as_completed
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
    """Find Blender executable."""
    import shutil

    blender_exe = os.environ.get("BLENDER_EXE")
    if blender_exe and Path(blender_exe).exists():
        return blender_exe

    common_paths = [
        "/Applications/Blender.app/Contents/MacOS/Blender",
        "/usr/bin/blender",
        "/usr/local/bin/blender",
    ]

    for path in common_paths:
        if Path(path).exists():
            return path

    return shutil.which("blender")


def process_file(blender_exe: str, blend_file: Path, script: str, output_dir: Path, extra_args: list):
    """Process a single .blend file."""
    cmd = [blender_exe, "-b", str(blend_file), "--python", script]

    if extra_args:
        cmd.append("--")
        cmd.extend(extra_args)

        # Replace {output} placeholder with actual output path
        if output_dir:
            output_file = output_dir / blend_file.name
            cmd = [arg.replace("{output}", str(output_file)) for arg in cmd]
            cmd = [arg.replace("{stem}", blend_file.stem) for arg in cmd]

    result = subprocess.run(cmd, capture_output=True, text=True)

    return {
        "file": str(blend_file),
        "returncode": result.returncode,
        "stdout": result.stdout,
        "stderr": result.stderr,
    }


def main():
    parser = argparse.ArgumentParser(description="Batch process .blend files")
    parser.add_argument("--pattern", "-p", default="*.blend", help="Glob pattern")
    parser.add_argument("--input", "-i", type=Path, default=Path.cwd(), help="Input directory")
    parser.add_argument("--script", "-s", required=True, help="Python script to run")
    parser.add_argument("--output", "-o", type=Path, help="Output directory")
    parser.add_argument("--parallel", "-j", type=int, default=1, help="Parallel processes")
    parser.add_argument("--blender", help="Path to Blender executable")
    parser.add_argument("args", nargs="*", help="Extra arguments for script (after --)")

    args, unknown = parser.parse_known_args()

    # Collect extra args
    extra_args = args.args + unknown if args.args or unknown else []

    load_env()

    blender_exe = args.blender or find_blender()
    if not blender_exe:
        print("Error: Could not find Blender. Set BLENDER_EXE in .env", file=sys.stderr)
        sys.exit(1)

    # Find files
    files = list(args.input.glob(args.pattern))
    if not files:
        print(f"No files found matching {args.pattern} in {args.input}", file=sys.stderr)
        sys.exit(1)

    print(f"Found {len(files)} files to process")

    # Create output directory
    if args.output:
        args.output.mkdir(parents=True, exist_ok=True)

    # Process files
    results = []
    if args.parallel > 1:
        with ProcessPoolExecutor(max_workers=args.parallel) as executor:
            futures = {
                executor.submit(process_file, blender_exe, f, args.script, args.output, extra_args): f
                for f in files
            }
            for future in as_completed(futures):
                result = future.result()
                results.append(result)
                status = "OK" if result["returncode"] == 0 else "FAILED"
                print(f"[{status}] {result['file']}")
    else:
        for f in files:
            result = process_file(blender_exe, f, args.script, args.output, extra_args)
            results.append(result)
            status = "OK" if result["returncode"] == 0 else "FAILED"
            print(f"[{status}] {result['file']}")

    # Summary
    success = sum(1 for r in results if r["returncode"] == 0)
    failed = len(results) - success
    print(f"\nProcessed: {len(results)} files, {success} success, {failed} failed")

    if failed > 0:
        sys.exit(1)


if __name__ == "__main__":
    main()
