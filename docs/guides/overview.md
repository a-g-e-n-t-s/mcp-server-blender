# mcp-server-blender Tool Guide

## Available Tools (use these first — less error-prone than raw Python):
- blender_create_object: Create primitives (cube, sphere, cylinder, plane, cone, torus)
- blender_modify_object: Move, rotate, scale, add modifiers (subdivision, solidify, mirror, bevel)
- blender_set_material: PBR materials with color, roughness, metallic
- blender_render: Render scene to PNG (CYCLES CPU recommended)
- blender_export: Export to glTF/FBX/OBJ/STL
- blender_get_scene_info: List all objects, transforms, materials
- blender_execute_python: Escape hatch for anything not covered above

## Workflow:
1. Use blender_get_scene_info to understand current state
2. Use dedicated tools for common operations
3. Fall back to blender_execute_python for complex operations
4. Always set `result = <value>` in execute_python to return data
