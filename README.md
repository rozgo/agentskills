# Agent Skills

A collection of skills for agents.

## Structure

- `skills/` - Skill implementations
- `spec/` - Agent skills specification (submodule)

## Available Skills

### blender

Automate Blender 3D tasks via headless Python scripting. Use when users want to:
- Process .blend files
- Render images/animations
- Convert between 3D formats (glTF, FBX, OBJ, USD, etc.)
- Extract scene information
- Batch process files
- Automate 3D workflows without a GUI

See [skills/blender/SKILL.md](skills/blender/SKILL.md) for full documentation.

### leptos

Guidance for building Rust web UIs with the Leptos crate (0.8.x). Covers:
- Components and signals
- Router configuration
- SSR/hydrate/CSR feature flags
- Server functions
- Common pitfalls

See [skills/leptos/SKILL.md](skills/leptos/SKILL.md) for full documentation.
