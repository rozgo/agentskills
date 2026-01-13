"""
Search Blender's Python API at runtime.

This script provides live introspection of Blender's API, eliminating the need
for static reference files. It queries the actual running Blender instance.

Usage:
    # Search operators by name
    $BLENDER_EXE -b --python api_search.py -- --search "export gltf"

    # Search operators by description
    $BLENDER_EXE -b --python api_search.py -- --search "animation" --in-description

    # Get full details for an operator
    $BLENDER_EXE -b --python api_search.py -- --operator bpy.ops.export_scene.gltf

    # List all operators in a module
    $BLENDER_EXE -b --python api_search.py -- --module export_scene

    # Search types
    $BLENDER_EXE -b --python api_search.py -- --search "Mesh" --types

    # Get type details
    $BLENDER_EXE -b --python api_search.py -- --type bpy.types.Mesh

    # List bpy.data collections
    $BLENDER_EXE -b --python api_search.py -- --data

    # List bpy.context attributes
    $BLENDER_EXE -b --python api_search.py -- --context

    # Output as JSON
    $BLENDER_EXE -b --python api_search.py -- --search "export" --json
"""

import sys
import json
import argparse


def get_operator_info(op_path):
    """Get detailed info for an operator."""
    import bpy

    parts = op_path.replace("bpy.ops.", "").split(".")
    if len(parts) != 2:
        return {"error": f"Invalid operator path: {op_path}"}

    module_name, op_name = parts
    try:
        module = getattr(bpy.ops, module_name)
        op = getattr(module, op_name)
        rna = op.get_rna_type()
    except AttributeError:
        return {"error": f"Operator not found: {op_path}"}

    info = {
        "path": op_path,
        "name": rna.name,
        "description": rna.description,
        "parameters": []
    }

    for prop in rna.properties:
        if prop.identifier == "rna_type":
            continue

        param = {
            "name": prop.identifier,
            "type": prop.type,
            "description": prop.description,
        }

        if hasattr(prop, "default"):
            param["default"] = prop.default
        elif hasattr(prop, "default_array"):
            param["default"] = list(prop.default_array)

        if prop.type == "ENUM" and hasattr(prop, "enum_items"):
            param["options"] = [
                {"id": item.identifier, "name": item.name, "description": item.description}
                for item in prop.enum_items
            ]

        if prop.type in ("INT", "FLOAT"):
            if hasattr(prop, "hard_min"):
                param["min"] = prop.hard_min
            if hasattr(prop, "hard_max"):
                param["max"] = prop.hard_max

        info["parameters"].append(param)

    return info


def search_operators(query, in_description=False):
    """Search operators by name or description."""
    import bpy

    results = []
    query_lower = query.lower()
    query_parts = query_lower.split()

    for module_name in dir(bpy.ops):
        if module_name.startswith("_"):
            continue

        module = getattr(bpy.ops, module_name)
        for op_name in dir(module):
            if op_name.startswith("_"):
                continue

            op_path = f"bpy.ops.{module_name}.{op_name}"

            try:
                op = getattr(module, op_name)
                rna = op.get_rna_type()

                # Check if all query parts match
                search_text = f"{module_name} {op_name}"
                if in_description:
                    search_text += f" {rna.description}"
                search_text = search_text.lower()

                if all(part in search_text for part in query_parts):
                    results.append({
                        "path": op_path,
                        "name": rna.name,
                        "description": rna.description[:100] + "..." if len(rna.description) > 100 else rna.description
                    })
            except:
                pass

    return results


def list_module_operators(module_name):
    """List all operators in a module."""
    import bpy

    try:
        module = getattr(bpy.ops, module_name)
    except AttributeError:
        return {"error": f"Module not found: bpy.ops.{module_name}"}

    operators = []
    for op_name in sorted(dir(module)):
        if op_name.startswith("_"):
            continue
        try:
            op = getattr(module, op_name)
            rna = op.get_rna_type()
            operators.append({
                "path": f"bpy.ops.{module_name}.{op_name}",
                "name": rna.name,
                "description": rna.description[:80] + "..." if len(rna.description) > 80 else rna.description
            })
        except:
            pass

    return {"module": f"bpy.ops.{module_name}", "count": len(operators), "operators": operators}


def get_type_info(type_path):
    """Get detailed info for a type."""
    import bpy

    type_name = type_path.replace("bpy.types.", "")
    try:
        type_obj = getattr(bpy.types, type_name)
    except AttributeError:
        return {"error": f"Type not found: {type_path}"}

    info = {
        "path": type_path,
        "name": type_name,
        "doc": type_obj.__doc__[:500] if type_obj.__doc__ else None,
        "properties": []
    }

    if hasattr(type_obj, "bl_rna"):
        for prop in type_obj.bl_rna.properties:
            if prop.identifier == "rna_type":
                continue
            info["properties"].append({
                "name": prop.identifier,
                "type": prop.type,
                "description": prop.description[:80] if prop.description else ""
            })

    return info


def search_types(query):
    """Search types by name."""
    import bpy

    results = []
    query_lower = query.lower()

    for type_name in dir(bpy.types):
        if type_name.startswith("_"):
            continue
        if query_lower in type_name.lower():
            type_obj = getattr(bpy.types, type_name)
            results.append({
                "path": f"bpy.types.{type_name}",
                "name": type_name,
                "doc": (type_obj.__doc__[:80] + "...") if type_obj.__doc__ and len(type_obj.__doc__) > 80 else type_obj.__doc__
            })

    return results


def list_data_collections():
    """List all bpy.data collections."""
    import bpy

    collections = []
    for name in sorted(dir(bpy.data)):
        if name.startswith("_"):
            continue
        attr = getattr(bpy.data, name)
        if hasattr(attr, "__iter__") and hasattr(attr, "new"):
            collections.append({
                "path": f"bpy.data.{name}",
                "name": name,
                "count": len(attr)
            })

    return collections


def list_context_attributes():
    """List all bpy.context attributes."""
    import bpy

    attributes = []
    for name in sorted(dir(bpy.context)):
        if name.startswith("_"):
            continue
        try:
            attr = getattr(bpy.context, name)
            attr_type = type(attr).__name__
            attributes.append({
                "path": f"bpy.context.{name}",
                "name": name,
                "type": attr_type
            })
        except:
            attributes.append({
                "path": f"bpy.context.{name}",
                "name": name,
                "type": "unavailable"
            })

    return attributes


def list_all_modules():
    """List all operator modules with counts."""
    import bpy

    modules = []
    for module_name in sorted(dir(bpy.ops)):
        if module_name.startswith("_"):
            continue
        module = getattr(bpy.ops, module_name)
        count = len([x for x in dir(module) if not x.startswith("_")])
        if count > 0:
            modules.append({
                "module": f"bpy.ops.{module_name}",
                "count": count
            })

    return modules


def format_operator_text(info):
    """Format operator info as readable text."""
    lines = []
    lines.append(f"\n{info['path']}")
    lines.append(f"  Name: {info['name']}")
    lines.append(f"  Description: {info['description']}")

    if info.get("parameters"):
        lines.append(f"  Parameters ({len(info['parameters'])}):")
        for param in info["parameters"]:
            default = f" = {param.get('default')}" if param.get("default") is not None else ""
            lines.append(f"    - {param['name']}: {param['type']}{default}")
            if param.get("description"):
                lines.append(f"        {param['description'][:70]}")
            if param.get("options"):
                opts = ", ".join(o["id"] for o in param["options"][:5])
                if len(param["options"]) > 5:
                    opts += f", ... (+{len(param['options'])-5} more)"
                lines.append(f"        Options: {opts}")

    return "\n".join(lines)


def main():
    import bpy

    parser = argparse.ArgumentParser(description="Search Blender's Python API")
    parser.add_argument("--search", "-s", help="Search query")
    parser.add_argument("--in-description", "-d", action="store_true", help="Also search in descriptions")
    parser.add_argument("--operator", "-o", help="Get details for specific operator (e.g., bpy.ops.export_scene.gltf)")
    parser.add_argument("--module", "-m", help="List operators in a module (e.g., export_scene)")
    parser.add_argument("--modules", action="store_true", help="List all operator modules")
    parser.add_argument("--type", "-t", help="Get details for specific type (e.g., bpy.types.Mesh)")
    parser.add_argument("--types", action="store_true", help="Search types instead of operators")
    parser.add_argument("--data", action="store_true", help="List bpy.data collections")
    parser.add_argument("--context", action="store_true", help="List bpy.context attributes")
    parser.add_argument("--json", "-j", action="store_true", help="Output as JSON")
    parser.add_argument("--limit", "-l", type=int, default=50, help="Max results (default: 50)")

    # Parse args after --
    argv = sys.argv
    if "--" in argv:
        argv = argv[argv.index("--") + 1:]
    else:
        argv = []

    args = parser.parse_args(argv)

    # Print version info
    if not args.json:
        print(f"Blender {bpy.app.version_string} API Search\n")

    result = None

    if args.operator:
        result = get_operator_info(args.operator)
        if not args.json:
            if result.get("error"):
                print(f"Error: {result['error']}")
            else:
                print(format_operator_text(result))

    elif args.module:
        result = list_module_operators(args.module)
        if not args.json:
            if result.get("error"):
                print(f"Error: {result['error']}")
            else:
                print(f"{result['module']} ({result['count']} operators)\n")
                for op in result["operators"]:
                    print(f"  {op['path']}")
                    print(f"    {op['description']}")

    elif args.modules:
        result = list_all_modules()
        if not args.json:
            print(f"Operator Modules ({len(result)} modules)\n")
            total = sum(m["count"] for m in result)
            for m in result:
                print(f"  {m['module']}: {m['count']} operators")
            print(f"\nTotal: {total} operators")

    elif args.type:
        result = get_type_info(args.type)
        if not args.json:
            if result.get("error"):
                print(f"Error: {result['error']}")
            else:
                print(f"\n{result['path']}")
                if result.get("doc"):
                    print(f"  Doc: {result['doc']}")
                print(f"  Properties ({len(result['properties'])}):")
                for prop in result["properties"][:30]:
                    print(f"    - {prop['name']}: {prop['type']}")
                if len(result["properties"]) > 30:
                    print(f"    ... and {len(result['properties'])-30} more")

    elif args.search and args.types:
        result = search_types(args.search)[:args.limit]
        if not args.json:
            print(f"Types matching '{args.search}': {len(result)}\n")
            for t in result:
                print(f"  {t['path']}")

    elif args.search:
        result = search_operators(args.search, args.in_description)[:args.limit]
        if not args.json:
            print(f"Operators matching '{args.search}': {len(result)}\n")
            for op in result:
                print(f"  {op['path']}")
                print(f"    {op['description']}")

    elif args.data:
        result = list_data_collections()
        if not args.json:
            print(f"bpy.data Collections ({len(result)})\n")
            for c in result:
                print(f"  {c['path']} ({c['count']} items)")

    elif args.context:
        result = list_context_attributes()
        if not args.json:
            print(f"bpy.context Attributes ({len(result)})\n")
            for a in result:
                print(f"  {a['path']}: {a['type']}")

    else:
        # Default: show summary
        modules = list_all_modules()
        total_ops = sum(m["count"] for m in modules)
        types_count = len([t for t in dir(bpy.types) if not t.startswith("_")])
        data_count = len(list_data_collections())
        ctx_count = len(list_context_attributes())

        result = {
            "version": bpy.app.version_string,
            "operator_modules": len(modules),
            "total_operators": total_ops,
            "types": types_count,
            "data_collections": data_count,
            "context_attributes": ctx_count
        }

        if not args.json:
            print("API Summary:")
            print(f"  Operator modules: {len(modules)}")
            print(f"  Total operators: {total_ops}")
            print(f"  Types: {types_count}")
            print(f"  Data collections: {data_count}")
            print(f"  Context attributes: {ctx_count}")
            print("\nUsage:")
            print("  --search <query>       Search operators by name")
            print("  --search <q> -d        Search operators by description")
            print("  --operator <path>      Get operator details")
            print("  --module <name>        List module operators")
            print("  --modules              List all modules")
            print("  --type <path>          Get type details")
            print("  --search <q> --types   Search types")
            print("  --data                 List bpy.data collections")
            print("  --context              List bpy.context attributes")
            print("  --json                 Output as JSON")

    if args.json and result:
        print(json.dumps(result, indent=2, default=str))


if __name__ == "__main__":
    main()
